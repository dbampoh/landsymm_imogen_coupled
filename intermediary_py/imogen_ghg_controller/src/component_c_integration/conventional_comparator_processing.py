"""
conventional_comparator_processing.py
=======================================
Component C, Step 8 (Option A): builds a "conventional climate-emulator"
full-trajectory external comparator covering 1900-2100.

WHAT THIS COMPARATOR REPRESENTS
-------------------------------
The conventional framing climate emulators (e.g. FAIR, MAGICC, OSCAR's IAM-driven
mode) use when ingesting emission inputs:

    Conventional_total = RCMIP_total + FAIR-ERF natural baseline

Where:
  RCMIP_total  = full anthropogenic emissions from RCMIP Phase 2
                 (CEDS-derived historical + CMIP6 SSP scenarios).
                 INDEPENDENT of our project's IPCC Tier-1 substitution.
  FAIR-ERF natural = natural-emission baseline from Smith et al. 2018 GMD,
                 used as the natural-source forcing in FAIR.
                 INDEPENDENT of our project's LPJ-GUESS DGVM.

This is the de facto reference framing for climate emulators worldwide. Both
inputs are independent of our pipeline AND independent of each other (RCMIP
comes from IAM/CEDS; FAIR-ERF comes from atmospheric-chemistry-model
inversions). So it's a valid "what would a conventional climate emulator
assume?" baseline against which our pipeline's integrated total can be compared
for the FULL 1900-2100 window.

DIFFERENCES VS THE HYBRID COMPARATOR (Option B)
-----------------------------------------------
The hybrid comparator built earlier (hybrid_comparator_processing.py) overlays
budget top-down values for the historical 1980-2020 segment, so it's
"observation-anchored where observations exist". The conventional comparator
here uses RCMIP+FAIR throughout, INCLUDING the historical period, so it's a
purer "what would a conventional emulator assume?" reference. Both have value:
  - Hybrid (Option B) tells us how close our pipeline lands to observations
    in the historical period.
  - Conventional (Option A) tells us how much our pipeline differs from the
    counterfactual where someone replaced our anthropogenic side with vanilla
    RCMIP and our natural side with the constant FAIR-ERF baseline.

CO2 FRAMING NOTE — IMPORTANT METHODOLOGICAL ASYMMETRY
-----------------------------------------------------
For CO2 specifically, the conventional comparator (RCMIP_total + FAIR-ERF=0)
represents "full anthropogenic emissions BEFORE any climate-emulator carbon
cycle removes a land sink". Our integrated total (RCMIP EFOS + LPJ-GUESS NEE)
represents "atmospheric source AFTER the LPJ-GUESS-simulated land sink is
applied". These are conceptually DIFFERENT quantities for CO2 — the comparator
is the climate-emulator's INPUT, our integrated total is the climate-emulator's
ENVELOPE-DERIVED ATMOSPHERIC SOURCE.

The gap between them is therefore not "error" but the LPJ-GUESS-simulated
land sink itself. This is explicitly documented in the script and the plot.

For CH4 and N2O, both quantities (forcing side and atmospheric source side) are
essentially equivalent because the gas-phase sinks are not dominated by one
specific removal process the way the land carbon sink dominates CO2.

INPUT FILES
-----------
    integrated_emissions_ch4.csv  /  _n2o.csv  /  _co2.csv
        — provides RCMIP_total_Mt and FAIR_natural_Mt columns covering 1900-2100
          (Default_total_Mt is already RCMIP_total + FAIR_natural, but we recompute
          here for transparency.)

OUTPUT
------
    conventional_comparator_ch4.csv
    conventional_comparator_n2o.csv
    conventional_comparator_co2.csv

    Columns per gas (1005 rows each = 5 scenarios × 201 years):
        Year, Scenario,
        RCMIP_total_Mt    — anthropogenic forcing component (Mt-of-gas)
        FAIR_natural_Mt   — natural baseline component (Mt-of-gas; CO2 = 0 by
                            convention because FAIR-ERF treats CO2 differently)
        Comparator_Mt     — Comparator = RCMIP_total + FAIR_natural

UNCERTAINTY ENVELOPE
--------------------
RCMIP and FAIR-ERF do not provide formal uncertainty bounds in the format we
need. We therefore omit explicit Lo/Hi columns. The plotting script renders a
single comparator line per scenario (no shaded uncertainty band).
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
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', str(OUT_C_DATA))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_C_DATA))
os.makedirs(OUT_DIR, exist_ok=True)

SCENARIOS = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP4-6.0', 'SSP5-8.5']


def banner(msg):
    print('\n' + '=' * 72 + f'\n{msg}\n' + '=' * 72, flush=True)


def build_for_gas(gas):
    """Build the conventional 1900-2100 comparator series for one gas.

    Returns a long-format DataFrame with one row per (year, scenario) and
    columns Year, Scenario, RCMIP_total_Mt, FAIR_natural_Mt, Comparator_Mt.
    """
    df_int = pd.read_csv(os.path.join(DATA_DIR,
                                       f'integrated_emissions_{gas.lower()}.csv'))

    rows = []
    for scen in SCENARIOS:
        sub = df_int[df_int.Scenario == scen].sort_values('Year')
        for _, r in sub.iterrows():
            rows.append({
                'Year':            int(r['Year']),
                'Scenario':        scen,
                'RCMIP_total_Mt':  float(r['RCMIP_total_Mt']),
                'FAIR_natural_Mt': float(r['FAIR_natural_Mt']),
                'Comparator_Mt':   float(r['RCMIP_total_Mt'])
                                 + float(r['FAIR_natural_Mt']),
            })

    return pd.DataFrame(rows).sort_values(
        ['Scenario', 'Year']).reset_index(drop=True)


# =============================================================================
# RUN PER GAS
# =============================================================================
banner("BUILDING CONVENTIONAL COMPARATORS (Option A)")

for gas in ['CH4', 'N2O', 'CO2']:
    df = build_for_gas(gas)
    out_path = os.path.join(OUT_DIR, f'conventional_comparator_{gas.lower()}.csv')
    df.to_csv(out_path, index=False)
    print(f'\n  {gas}: shape {df.shape}, saved to {out_path}')

    # Sanity print: first/last anchor points for SSP2-4.5
    sub2 = df[df.Scenario == 'SSP2-4.5']
    print(f"  Sample values (SSP2-4.5):")
    for yr in [1900, 1950, 2000, 2014, 2020, 2050, 2100]:
        rr = sub2[sub2.Year == yr]
        if len(rr):
            r = rr.iloc[0]
            print(f"    {yr}: RCMIP={r.RCMIP_total_Mt:>10.1f} + FAIR={r.FAIR_natural_Mt:>10.1f} "
                  f"= comp={r.Comparator_Mt:>10.1f}")


# =============================================================================
# VALIDATION CHECK: comparator vs integrated total at key years
# =============================================================================
banner("OUR_INTEGRATED vs CONVENTIONAL COMPARATOR (SSP2-4.5)")

for gas in ['CH4', 'N2O', 'CO2']:
    print(f'\n{gas}:')
    df_int = pd.read_csv(os.path.join(DATA_DIR,
                                       f'integrated_emissions_{gas.lower()}.csv'))
    df_cmp = pd.read_csv(os.path.join(OUT_DIR,
                                       f'conventional_comparator_{gas.lower()}.csv'))
    sub_int = df_int[df_int.Scenario == 'SSP2-4.5']
    sub_cmp = df_cmp[df_cmp.Scenario == 'SSP2-4.5']
    print(f"  {'Year':>6}{'Our int.':>14}{'Conventional':>16}{'Δ':>14}{'Δ %':>10}")
    for yr in [1900, 1950, 2000, 2014, 2020, 2050, 2100]:
        our = sub_int[sub_int.Year == yr]['Total_Mt'].values[0]
        cmp = sub_cmp[sub_cmp.Year == yr]['Comparator_Mt'].values[0]
        delta = our - cmp
        pct = 100.0 * delta / cmp if cmp != 0 else float('nan')
        print(f"  {yr:>6}{our:>14.2f}{cmp:>16.2f}{delta:>+14.2f}{pct:>+9.1f}%")

print('\nDone.')
