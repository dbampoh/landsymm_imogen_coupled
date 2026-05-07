"""
rcmip_co2_processing.py
=========================
Component C, Step 1: extracts the anthropogenic CO2 trajectory from RCMIP for
all five SSP-RCP scenarios, 1900-2100, using the FOSSIL AND INDUSTRIAL series
only (Option A framing — see PROJECT_HANDOFF.md §8.1).

WHY EFOS-ONLY (not the full RCMIP CO2 total)?
---------------------------------------------
LPJ-GUESS NEE (the natural-side trajectory we'll add to this) already includes
both natural land response (Veg + Soil + Fire) AND anthropogenic land-use-change
components (LU_ch + Harvest + Slow_h). So if we used RCMIP's full Emissions|CO2
(= Fossil and Industrial + AFOLU), we'd double-count the AFOLU/ELUC component.

By using EFOS only, the integrated CO2 trajectory becomes:
    Total atmospheric source = EFOS (RCMIP) + NEE (LPJ-GUESS)
                             = (fossil + industrial) + (natural + ELUC)
                             = fossil + industrial + AFOLU + natural-land
which is the cleanest accounting.

Note: this script does NOT perform a Tier-1 substitution like
rcmip_substitution_processing.py does for CH4 and N2O — there is no independent
agricultural CO2 inventory in this project. The Our_anthro for CO2 IS the RCMIP
EFOS series, unchanged.

INPUT
-----
    {RCMIP_CSV}

VARIABLE EXTRACTED
------------------
    'Emissions|CO2|MAGICC Fossil and Industrial' for Region='World'
    Scenarios: historical (1750-2014) + ssp126/245/370/460/585 (2015-2100)
    Unit: Mt CO2/yr (already in target unit; no conversion needed)

TEMPORAL TREATMENT
------------------
    Historical (1900-2014): single trajectory shared by all SSPs (RCMIP
                            historical is one common record).
    Scenario  (2015-2100):  five separate trajectories. RCMIP scenario data
                            is reported every 5 years (2015, 2020, 2025, ...,
                            2100), so we linearly interpolate to annual within
                            this window. Annual data from RCMIP historical is
                            used for 1900-2014, then we splice in interpolated
                            scenario series at 2015. Both endpoints (1750-2010
                            in scenarios; 2015 in historical) coincide with
                            historical values, so the splice is continuous.
    The historical→scenario splice is at 2015 (where RCMIP scenarios start).
    For year 2014, the historical value is used. For 2015, scenario values
    diverge.

OUTPUT
------
    rcmip_co2.csv with columns:
        Year, Scenario, EFOS_MtCO2, Period
    1005 rows (5 scenarios × 201 years 1900-2100), in Mt CO2/yr.

    Period values: 'pre-inventory' (1900-1969), 'historical' (1970-2014),
                   'scenario' (2015-2100). The pre-inventory label is kept for
                   parity with rcmip_substitution_*.csv structure even though
                   no Tier-1 substitution applies here.
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
    OUT_C_DATA, OUT_C_FIGS, OUT_C_SUMMARIES, RCMIP_CSV,
)

import os
import pandas as pd
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_C_DATA))
RCMIP_CSV = str(RCMIP_CSV)  # path object → string for legacy str-concat code
os.makedirs(OUT_DIR, exist_ok=True)

# Map our scenario keys to RCMIP scenario names and friendly labels.
SCEN_MAP = {
    'SSP1-2.6': 'ssp126',
    'SSP2-4.5': 'ssp245',
    'SSP3-7.0': 'ssp370',
    'SSP4-6.0': 'ssp460',
    'SSP5-8.5': 'ssp585',
}

VARIABLE = 'Emissions|CO2|MAGICC Fossil and Industrial'
TARGET_YEARS = list(range(1900, 2101))   # 201 annual values

print("Loading RCMIP CSV ...")
df_r = pd.read_csv(RCMIP_CSV, low_memory=False)
print(f"  shape: {df_r.shape}, regions: {df_r['Region'].nunique()}")

# Helper: extract a single annual series for a given scenario.
def get_efos_series(rcmip_scen):
    """Return dict {year: value_MtCO2} for a given RCMIP scenario name.
    Only years with reported (non-NaN) values are included."""
    sub = df_r[(df_r['Variable'] == VARIABLE)
               & (df_r['Region'] == 'World')
               & (df_r['Scenario'] == rcmip_scen)]
    if len(sub) == 0:
        raise ValueError(f'No data for scenario "{rcmip_scen}"')
    if len(sub) > 1:
        raise ValueError(f'Multiple rows for "{rcmip_scen}" — ambiguous')
    row = sub.iloc[0]
    year_cols = [c for c in sub.columns if c.isdigit()]
    out = {}
    for c in year_cols:
        val = row[c]
        if pd.notna(val):
            out[int(c)] = float(val)
    return out


def interpolate_to_annual(reported, year_lo, year_hi):
    """Linearly interpolate a {year: value} dict to dense annual coverage
    from year_lo to year_hi inclusive. Reported years bracketing year_lo and
    year_hi must exist in `reported` (i.e., we only interpolate within the
    convex hull of reported years).
    """
    yrs_in = sorted(reported)
    vals_in = [reported[y] for y in yrs_in]
    yrs_out = list(range(year_lo, year_hi + 1))
    vals_out = np.interp(yrs_out, yrs_in, vals_in)
    return dict(zip(yrs_out, vals_out))

# 1. Pull historical (1750-2014) — shared across scenarios
hist_series = get_efos_series('historical')
print(f"  historical: {len(hist_series)} years "
      f"({min(hist_series)}-{max(hist_series)})")

# 2. Pull each scenario (raw reported years span 1750-2500), interpolate to
#    annual 1900-2100 within the scenario record. Note that scenario records
#    contain the full historical range 1750-2014 (annual) plus 2015, 2020,
#    2025, ..., 2100 (every 5 years), so interpolation is no-op for 1900-2014
#    and linear between the 5-year scenario points.
scen_series = {}
for label, rcmip_name in SCEN_MAP.items():
    raw = get_efos_series(rcmip_name)
    interp = interpolate_to_annual(raw, 1900, 2100)
    scen_series[label] = interp
    n_raw_in_window = sum(1 for y in raw if 1900 <= y <= 2100)
    print(f"  {label:9s}: {n_raw_in_window} raw years → {len(interp)} interpolated annual "
          f"(1900-2100)")

# 3. Build the long-format output
rows = []
for label in SCEN_MAP:
    for year in TARGET_YEARS:
        # Decide which series to use at this year:
        #   1900-2014: historical; 2015-2100: scenario
        if year <= 2014:
            value = hist_series.get(year)
            period = 'pre-inventory' if year <= 1969 else 'historical'
        else:
            value = scen_series[label].get(year)
            period = 'scenario'
        # Defensive: if RCMIP doesn't have that year, NaN it (shouldn't happen)
        rows.append({'Year': year, 'Scenario': label,
                     'EFOS_MtCO2': value, 'Period': period})

df_out = pd.DataFrame(rows)
df_out = df_out.sort_values(['Scenario', 'Year']).reset_index(drop=True)

# Sanity check
assert len(df_out) == 5 * 201, f"Expected 1005 rows, got {len(df_out)}"
assert df_out['EFOS_MtCO2'].notna().all(), "Some EFOS values are NaN"

# Spot-check the 2020 anchor and 2100 endpoint per scenario
print("\nSpot checks (Mt CO2/yr):")
print(f"  {'Scenario':<10} {'2020':>10} {'2050':>10} {'2100':>10}")
for label in SCEN_MAP:
    sub = df_out[df_out.Scenario == label]
    v2020 = sub[sub.Year == 2020]['EFOS_MtCO2'].values[0]
    v2050 = sub[sub.Year == 2050]['EFOS_MtCO2'].values[0]
    v2100 = sub[sub.Year == 2100]['EFOS_MtCO2'].values[0]
    print(f"  {label:<10} {v2020:>10.0f} {v2050:>10.0f} {v2100:>10.0f}")

# Save
out_path = os.path.join(OUT_DIR, 'rcmip_co2.csv')
df_out.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"Shape: {df_out.shape}")
print(f"Columns: {list(df_out.columns)}")
