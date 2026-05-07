"""
hybrid_comparator_processing.py
=================================
Component C, Step 6: builds a HYBRID full-trajectory external comparator
covering 1900-2100 by stitching together two independent observation-constrained
sources of "integrated total atmospheric source" (anthropogenic + natural):

    Historical (overlap with budget reports, 1980-2020 typically):
      -- Independent observation-constrained TOTAL from atmospheric inversions
         and global budget partitions (GMB 2025 / GNB 2024 / GCB 2025).
         These directly measure or constrain the global atmospheric source.

    Outside that overlap (pre-1980, pre-budget-reporting-period; AND 2021-2100):
      -- "Conventional" integrated reference: RCMIP_total (anthropogenic from
         the IAM/CEDS pipeline used by climate models) + FAIR-ERF natural
         baseline (held constant after 2005).
      -- This is the de facto reference framing for climate emulators and is
         INDEPENDENT of our pipeline (no LPJ-GUESS, no FAO Tier-1 substitution).

The hybrid trajectory therefore represents "the best independent integrated
total atmospheric source we can construct from publicly available datasets
that already exist on disk in this environment".

WHY THIS IS THE RIGHT COMPARATOR FOR OUR SCOPE
----------------------------------------------
Our integrated total = anthropogenic (RCMIP-substituted CH4/N2O or RCMIP EFOS
for CO2) + natural (LPJ-GUESS DGVM). Because LPJ-GUESS NEE includes BOTH
natural land response AND anthropogenic land-use components (LU_ch + Harvest +
Slow_h), our integrated CO2 total is conceptually equivalent to GCB's
"net atmospheric source" = EFOS + ELUC − SLAND. That's why we picked GCB's
partition for CO2.

For CH4/N2O, atmospheric inversions (top-down) measure the total global emission
that the atmosphere actually receives, regardless of partition between
anthropogenic and natural. That's the same quantity as our integrated total.

CAVEAT EXPLICITLY DOCUMENTED IN OUTPUT
--------------------------------------
For 2021-2100, the comparator's natural component is held CONSTANT (FAIR-ERF
2005 value, ~191 Tg CH4/yr and ~14.12 Tg N2O/yr). Real natural emissions will
respond to climate, CO2, and land-use change over the next century — that is
PRECISELY what our LPJ-GUESS pipeline projects. So divergence between our
integrated total and the hybrid comparator in 2021-2100 captures the natural-
emission climate-feedback signal that climate emulators conventionally ignore.
This divergence is informative, not error.

INPUT FILES
-----------
    external_comparators_ch4.csv  /  _n2o.csv  /  _co2.csv
        — observation-constrained period values (GMB/GNB/GCB)
    integrated_emissions_ch4.csv  /  _n2o.csv  /  _co2.csv
        — has RCMIP_total_Mt and FAIR_natural_Mt columns covering 1900-2100

OUTPUT
------
    hybrid_comparator_ch4.csv
    hybrid_comparator_n2o.csv
    hybrid_comparator_co2.csv

    Columns per gas:
        Year, Scenario,
        Comparator_Mt        — the hybrid trajectory (best, blended)
        Comparator_lo_Mt     — lower uncertainty bound (where defined)
        Comparator_hi_Mt     — upper uncertainty bound (where defined)
        Source_segment       — 'RCMIP+FAIR' / 'budget_TD' / 'transition'

    1005 rows per gas (5 scenarios × 201 years). Note that the budget-anchored
    historical segment is technically scenario-independent (same in all 5
    scenarios), but we replicate it across scenarios so the schema matches the
    integrated_emissions_*.csv files exactly for joinable plotting.

ANCHORING METHODOLOGY
---------------------
1. RCMIP+FAIR baseline at every year for every scenario: this gives a complete
   1900-2100 backbone trajectory (Default_total_Mt is already in the integrated
   CSVs).

2. Budget-anchor periods: for each (Period, gas) we have a Best_Mt and [Lo_Mt,
   Hi_Mt] range from external_comparators_*.csv. We assign the period midpoint
   year as the anchor year:
     CH4: 2005, 2015, 2020   (GMB 2000-2009, 2010-2019, 2020)
     N2O: 1997, 2015, 2020   (GNB 1997, 2010-2019, 2020)
     CO2: 1965, 1975, 1985, 1995, 2005, 2018  (GCB 1960s..2014-2023)

3. For years coinciding with anchor years: comparator = budget Best_Mt;
   bounds = budget [Lo_Mt, Hi_Mt].

4. For years between anchor years: linear interpolation between anchors.

5. For years before the first anchor or after the last anchor: comparator =
   RCMIP+FAIR baseline. To avoid a step at the boundary, we apply a 5-year
   blend region where the comparator = α × budget + (1-α) × RCMIP+FAIR with
   α going from 0 to 1 over the 5-year transition.

6. Bounds outside the budget-anchored region: we propagate the budget last/first
   anchor's Lo/Hi as a constant offset relative to the comparator best line.
   (This is a defensible expedient: it preserves the magnitude of uncertainty
   from the most recent or earliest anchor, but the user is alerted via the
   Source_segment column that the bounds are extrapolated.)
"""


# ---------------------------------------------------------------------------
# Project bootstrap: add project root to sys.path so we can import shared/
# ---------------------------------------------------------------------------
import sys as _sys
from pathlib import Path as _Path
_PROJ_ROOT = _Path(__file__).resolve()
while _PROJ_ROOT.name and not (_PROJ_ROOT / 'src').is_dir():
    if _PROJ_ROOT.parent == _PROJ_ROOT:
        break
    _PROJ_ROOT = _PROJ_ROOT.parent
if str(_PROJ_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_PROJ_ROOT))
from src.shared.paths import (
    OUT_C_DATA,
)

import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', str(OUT_C_DATA))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_C_DATA))
os.makedirs(OUT_DIR, exist_ok=True)

SCENARIOS = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP4-6.0', 'SSP5-8.5']
TARGET_YEARS = list(range(1900, 2101))


def load_inputs(gas):
    """Load the integrated_emissions_*.csv (for RCMIP+FAIR baseline per scenario)
    and the external_comparators_*.csv (for budget anchors)."""
    df_int = pd.read_csv(os.path.join(DATA_DIR, f'integrated_emissions_{gas.lower()}.csv'))
    df_cmp = pd.read_csv(os.path.join(DATA_DIR, f'external_comparators_{gas.lower()}.csv'))
    return df_int, df_cmp


def anchor_year(period_label, year_start, year_end):
    """Return the integer year used as the linear-interpolation anchor.
    Strategy: use the midpoint year for multi-year periods; for single-year
    periods (e.g. '2020'), use the year itself."""
    if year_start == year_end:
        return year_start
    return int(round((year_start + year_end) / 2.0))


def build_comparator_for_gas(gas):
    """Build the hybrid 1900-2100 comparator series for one gas.

    Returns a DataFrame with columns:
        Year, Scenario, Comparator_Mt, Comparator_lo_Mt,
        Comparator_hi_Mt, Source_segment

    SEMANTIC NOTE — CO2 framing correction
    ---------------------------------------
    For CO2 specifically, the budget anchor (GCB) reports the NET ATMOSPHERIC
    SOURCE = EFOS + ELUC − SLAND, while the RCMIP+FAIR baseline outside the
    budget-anchored region is RCMIP_total + 0 = EFOS + AFOLU (FULL anthropogenic
    BEFORE the climate-emulator carbon cycle removes any land sink). These two
    differ by ~3 Pg C/yr (the magnitude of SLAND).

    To keep the comparator semantically consistent throughout (always representing
    "what the atmosphere actually receives"), we apply a SLAND correction to the
    RCMIP+FAIR baseline for CO2 in the non-budget-anchored segments:

        CO2_baseline_corrected(y) = RCMIP_total(y) - SLAND_estimate(y)

    SLAND_estimate(y) is derived from GCB Table 7 by linear interpolation of the
    decadal SLAND values forward and backward, then held constant after 2020 at
    the most recent decadal value (3.2 GtC/yr = 11,734 Mt CO2/yr). This is a
    conservative assumption — most ESM ensembles project SLAND continuing to
    increase under high-CO2 scenarios, so the corrected baseline is likely an
    UPPER bound on the true atmospheric source for high-emission futures.

    For CH4 and N2O, atmospheric inversions and bottom-up totals are
    approximately equivalent (the gas-phase sinks scale linearly with atmospheric
    burden and are not dominated by a single removal process the way land
    carbon sink dominates CO2). So we don't apply a correction for CH4/N2O.
    """
    df_int, df_cmp = load_inputs(gas)

    # CO2-specific SLAND correction series (Mt CO2/yr per year)
    # Derived from GCB 2025 Table 7 SLAND column, in GtC/yr
    GCB_SLAND_DECADAL = {       # midpoint year → SLAND in GtC/yr
        1965: 1.2, 1975: 2.0, 1985: 1.8, 1995: 2.5, 2005: 2.8, 2018: 3.2,
    }
    # Convert to Mt CO2/yr and build interpolated annual series
    PgC_to_MtCO2 = (44.0 / 12.0) * 1000.0
    sland_years = sorted(GCB_SLAND_DECADAL)
    sland_vals_MtCO2 = [GCB_SLAND_DECADAL[y] * PgC_to_MtCO2 for y in sland_years]

    def sland_at_year(y):
        """Return SLAND-equivalent in Mt CO2/yr for the given year.

        SLAND is the climate-emulator land carbon sink driven by elevated
        atmospheric CO2 (CO2 fertilization). It's a PERTURBATION quantity:
        pre-industrial natural land carbon cycle is in approximate balance,
        so SLAND ≈ 0 before substantial anthropogenic CO2 buildup.

        Strategy:
          y ≤ 1960: SLAND linearly ramps from 0 (year 1900) to GCB 1960s
                    value (1.2 GtC = 4400 Mt CO2). This matches GCB Figure 4
                    showing SLAND emerging from near-zero in early 20th c.
          1960 < y < 2018: linear interpolation of GCB decadal values.
          y >= 2018: held constant at 2014-2023 value (3.2 GtC = 11734 Mt CO2).
                    This is conservative — SLAND likely continues to grow
                    in high-emissions futures, so our "atmospheric source"
                    comparator is likely an UPPER bound for those scenarios.
        """
        if y <= 1900:
            return 0.0
        if y < sland_years[0]:   # 1900 < y < 1965
            # ramp from 0 at 1900 to first decadal value at sland_years[0]
            alpha = (y - 1900) / (sland_years[0] - 1900)
            return alpha * sland_vals_MtCO2[0]
        if y >= sland_years[-1]:
            return sland_vals_MtCO2[-1]
        return float(np.interp(y, sland_years, sland_vals_MtCO2))

    # Build anchor table
    anchors = []
    for _, r in df_cmp.iterrows():
        ay = anchor_year(r.Period_label, r.Year_start, r.Year_end)
        anchors.append({
            'Anchor_year': ay,
            'Best_Mt':     r.Best_Mt,
            'Lo_Mt':       r.Lo_Mt,
            'Hi_Mt':       r.Hi_Mt,
            'Period':      r.Period_label,
        })
    anchors = sorted(anchors, key=lambda d: d['Anchor_year'])
    anchor_years = [a['Anchor_year'] for a in anchors]
    anchor_bests = [a['Best_Mt'] for a in anchors]
    anchor_los   = [a['Lo_Mt']   for a in anchors]
    anchor_his   = [a['Hi_Mt']   for a in anchors]

    # Precompute uncertainty offsets relative to best at first/last anchor
    # (used for years OUTSIDE the budget-anchored region)
    first_lo_offset = anchor_los[0]  - anchor_bests[0]
    first_hi_offset = anchor_his[0]  - anchor_bests[0]
    last_lo_offset  = anchor_los[-1] - anchor_bests[-1]
    last_hi_offset  = anchor_his[-1] - anchor_bests[-1]

    # Linear interpolation function for the "budget" segment
    def budget_at(year):
        if year < anchor_years[0] or year > anchor_years[-1]:
            return None
        return float(np.interp(year, anchor_years, anchor_bests))

    def budget_bounds_at(year):
        if year < anchor_years[0] or year > anchor_years[-1]:
            return None, None
        lo = float(np.interp(year, anchor_years, anchor_los))
        hi = float(np.interp(year, anchor_years, anchor_his))
        return lo, hi

    # Define transition windows (5-yr blends from baseline → budget at the
    # earliest anchor; budget → baseline at the latest anchor)
    blend_width = 5
    pre_budget_blend_start  = anchor_years[0]  - blend_width   # baseline from 1900..(start-1)
    pre_budget_blend_end    = anchor_years[0]                  # full budget at start
    post_budget_blend_start = anchor_years[-1]                 # full budget at end
    post_budget_blend_end   = anchor_years[-1] + blend_width   # baseline thereafter

    # Now build per-scenario rows
    rows = []
    for scen in SCENARIOS:
        sub = df_int[df_int.Scenario == scen].sort_values('Year').reset_index(drop=True)
        baseline_lookup = {int(r.Year): float(r.Default_total_Mt) for _, r in sub.iterrows()}

        for year in TARGET_YEARS:
            base = baseline_lookup.get(year)
            if base is None:
                continue

            # CO2 framing correction: subtract SLAND from baseline so the
            # comparator is semantically consistent (atmospheric-source framing)
            if gas == 'CO2':
                base_corrected = base - sland_at_year(year)
            else:
                base_corrected = base

            # Choose segment
            if year < pre_budget_blend_start:
                comp_best = base_corrected
                comp_lo = base_corrected + first_lo_offset
                comp_hi = base_corrected + first_hi_offset
                seg = 'RCMIP+FAIR' if gas != 'CO2' else 'RCMIP-SLAND+FAIR'
            elif year < anchor_years[0]:
                alpha = (year - pre_budget_blend_start) / blend_width
                bud = anchor_bests[0]
                comp_best = (1 - alpha) * base_corrected + alpha * bud
                comp_lo = comp_best + first_lo_offset
                comp_hi = comp_best + first_hi_offset
                seg = 'transition'
            elif year <= anchor_years[-1]:
                comp_best = budget_at(year)
                lo, hi = budget_bounds_at(year)
                comp_lo = lo; comp_hi = hi
                seg = 'budget_TD'
            elif year <= post_budget_blend_end:
                alpha = (year - post_budget_blend_start) / blend_width
                bud = anchor_bests[-1]
                comp_best = (1 - alpha) * bud + alpha * base_corrected
                comp_lo = comp_best + last_lo_offset
                comp_hi = comp_best + last_hi_offset
                seg = 'transition'
            else:
                comp_best = base_corrected
                comp_lo = base_corrected + last_lo_offset
                comp_hi = base_corrected + last_hi_offset
                seg = 'RCMIP+FAIR' if gas != 'CO2' else 'RCMIP-SLAND+FAIR'

            rows.append({
                'Year': year, 'Scenario': scen,
                'Comparator_Mt':    comp_best,
                'Comparator_lo_Mt': comp_lo,
                'Comparator_hi_Mt': comp_hi,
                'Source_segment':   seg,
            })

    df = pd.DataFrame(rows)
    df = df.sort_values(['Scenario', 'Year']).reset_index(drop=True)
    return df


def banner(msg):
    print('\n' + '=' * 72 + f'\n{msg}\n' + '=' * 72, flush=True)


# =============================================================================
# RUN PER GAS
# =============================================================================
banner("BUILDING HYBRID COMPARATORS")

for gas in ['CH4', 'N2O', 'CO2']:
    df = build_comparator_for_gas(gas)
    out_path = os.path.join(OUT_DIR, f'hybrid_comparator_{gas.lower()}.csv')
    df.to_csv(out_path, index=False)
    print(f'\n  {gas}: shape {df.shape}, saved to {out_path}')

    # Sanity print: first/last anchor periods, transition regions, far-future
    print(f"  First anchor year segment values for SSP2-4.5:")
    sub2 = df[df.Scenario == 'SSP2-4.5']
    for _, r in sub2.iloc[:5].iterrows():
        print(f"    {int(r.Year)}: {r.Comparator_Mt:.2f} ({r.Source_segment})")
    print(f"  Around budget anchor period:")
    for yr in [1979, 1980, 1985, 1995, 2010, 2018, 2020, 2021, 2025, 2030]:
        rr = sub2[sub2.Year == yr]
        if len(rr):
            r = rr.iloc[0]
            print(f"    {yr}: {r.Comparator_Mt:.2f} ({r.Source_segment})")
    print(f"  End-of-century:")
    for yr in [2080, 2090, 2100]:
        rr = sub2[sub2.Year == yr]
        if len(rr):
            r = rr.iloc[0]
            print(f"    {yr}: {r.Comparator_Mt:.2f} ({r.Source_segment})")


# =============================================================================
# VALIDATION: compare integrated total to comparator at key years
# =============================================================================
banner("OUR_INTEGRATED vs HYBRID COMPARATOR (SSP2-4.5)")

for gas in ['CH4', 'N2O', 'CO2']:
    print(f'\n{gas}:')
    df_int = pd.read_csv(os.path.join(DATA_DIR,
                                       f'integrated_emissions_{gas.lower()}.csv'))
    df_cmp = pd.read_csv(os.path.join(OUT_DIR,
                                       f'hybrid_comparator_{gas.lower()}.csv'))
    sub_int = df_int[df_int.Scenario == 'SSP2-4.5']
    sub_cmp = df_cmp[df_cmp.Scenario == 'SSP2-4.5']
    for yr in [1950, 2000, 2020, 2050, 2100]:
        our = sub_int[sub_int.Year == yr]['Total_Mt'].values[0]
        cmp = sub_cmp[sub_cmp.Year == yr]['Comparator_Mt'].values[0]
        seg = sub_cmp[sub_cmp.Year == yr]['Source_segment'].values[0]
        print(f'  {yr}: our={our:>10.1f}  comparator={cmp:>10.1f}  '
              f'Δ={our-cmp:+.1f}  ({seg})')
