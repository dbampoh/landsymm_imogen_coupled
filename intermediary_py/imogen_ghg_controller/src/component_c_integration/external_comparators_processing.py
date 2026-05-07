"""
external_comparators_processing.py
====================================
Component C, Step 4: builds an "external comparators" reference table for our
integrated GHG emission trajectories. These comparators are independent
estimates of the SAME integrated quantity we produce — i.e., the global total
atmospheric source from the land-system + geological systems together —
constructed from atmospheric inversions and observation-constrained budgets.

WHAT WE COMPARE TO (and why each is the right comparator)
---------------------------------------------------------
Our integrated total per gas is:
    Total = anthropogenic (incl. fossil/industrial)  +  natural land flux
This is what the atmosphere actually sees — the net global source.

For CH4: GMB 2025 atmospheric-inversion total emission (top-down, TD).
         Saunois et al. 2025 ESSD 17 1873-1958, executive summary text.
For N2O: GNB 2024 atmospheric-inversion total emission (top-down, TD).
         Tian et al. 2024 ESSD 16 2543-2604, executive summary text.
For CO2: GCB 2025 partition: EFOS + ELUC − SLAND = net atmospheric source.
         Friedlingstein et al. 2025 ESSD 17 965-1039, Table 7.
         Note: this equals our integrated quantity (EFOS + LPJ-NEE) by
         construction, because LPJ-NEE ≈ -(SLAND − ELUC) when the LPJ-GUESS
         configuration captures both natural and land-use CO2 fluxes (which
         it does — see PROJECT_HANDOFF.md §3.4).

These references EXIST ONLY FOR THE HISTORICAL PERIOD (typically 1980-2023).
Atmospheric inversions cannot be projected forward; they ARE measurements.
Hence comparators are plotted as historical-period step bands only.

EXTRACTED VALUES (from PDF executive summaries and tables)
----------------------------------------------------------

CH4 (GMB 2025), Tg CH4/yr top-down total source:
    2000-2009:  543 [528-578]   (= 575 - 32 from text; range is approximate)
    2010-2019:  575 [553-586]
    2020:       608 [581-627]

N2O (GNB 2024), Tg N/yr top-down total source:
    1997:       15.4 [13.9-16.7]
    2010-2019:  17.4 [15.8-19.2]
    2020:       17.0 [16.6-17.4]
    Convert to Tg N2O/yr: × 44/28

CO2 (GCB 2025 Table 7), GtC/yr atmospheric source (EFOS + ELUC − SLAND):
    1960s:    EFOS=3.0±0.2  ELUC=1.6±0.7  SLAND=1.2±0.5  →  3.4 ± 0.88
    1970s:    EFOS=4.7±0.2  ELUC=1.4±0.7  SLAND=2.0±0.8  →  4.1 ± 1.08
    1980s:    EFOS=5.5±0.3  ELUC=1.4±0.7  SLAND=1.8±0.8  →  5.1 ± 1.10
    1990s:    EFOS=6.4±0.3  ELUC=1.6±0.7  SLAND=2.5±0.6  →  5.5 ± 0.94
    2000s:    EFOS=7.8±0.4  ELUC=1.4±0.7  SLAND=2.8±0.7  →  6.4 ± 1.06
    2014-23:  EFOS=9.7±0.5  ELUC=1.1±0.7  SLAND=3.2±0.9  →  7.6 ± 1.24
    Convert to Mt CO2/yr: × 44/12 × 1000

OUTPUT FILES
------------
    external_comparators_ch4.csv
    external_comparators_n2o.csv
    external_comparators_co2.csv

    Columns (per gas):
        Period_label, Year_start, Year_end,
        Best_Mt, Lo_Mt, Hi_Mt, Source

    Each row is a multi-year period or single year with bounds. The plotting
    script renders these as horizontal step-bands across [year_start - 0.5,
    year_end + 0.5].
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
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_C_DATA))
os.makedirs(OUT_DIR, exist_ok=True)

# Conversion factors
TgN_to_TgN2O = 44.0 / 28.0
GtC_to_MtCO2 = (44.0 / 12.0) * 1000.0


# =============================================================================
# CH4 — GMB 2025 top-down total
# =============================================================================
ch4_rows = [
    {'Period_label': '2000-2009', 'Year_start': 2000, 'Year_end': 2009,
     'Best_Mt': 543, 'Lo_Mt': 528, 'Hi_Mt': 578,
     'Source': 'GMB 2025 (Saunois et al. ESSD 17), top-down inversions'},
    {'Period_label': '2010-2019', 'Year_start': 2010, 'Year_end': 2019,
     'Best_Mt': 575, 'Lo_Mt': 553, 'Hi_Mt': 586,
     'Source': 'GMB 2025 (Saunois et al. ESSD 17), top-down inversions'},
    {'Period_label': '2020',      'Year_start': 2020, 'Year_end': 2020,
     'Best_Mt': 608, 'Lo_Mt': 581, 'Hi_Mt': 627,
     'Source': 'GMB 2025 (Saunois et al. ESSD 17), top-down inversions'},
]
ch4_df = pd.DataFrame(ch4_rows)
ch4_df.to_csv(os.path.join(OUT_DIR, 'external_comparators_ch4.csv'), index=False)
print(f"Wrote external_comparators_ch4.csv ({len(ch4_df)} rows; Mt CH4/yr)")
print(ch4_df.to_string(index=False))


# =============================================================================
# N2O — GNB 2024 top-down total
# =============================================================================
n2o_rows = []
for label, y0, y1, best_n, lo_n, hi_n in [
    ('1997',      1997, 1997, 15.4, 13.9, 16.7),
    ('2010-2019', 2010, 2019, 17.4, 15.8, 19.2),
    ('2020',      2020, 2020, 17.0, 16.6, 17.4),
]:
    n2o_rows.append({
        'Period_label': label, 'Year_start': y0, 'Year_end': y1,
        'Best_Mt': best_n * TgN_to_TgN2O,
        'Lo_Mt':   lo_n   * TgN_to_TgN2O,
        'Hi_Mt':   hi_n   * TgN_to_TgN2O,
        'Source': 'GNB 2024 (Tian et al. ESSD 16), top-down inversions',
    })
n2o_df = pd.DataFrame(n2o_rows)
n2o_df.to_csv(os.path.join(OUT_DIR, 'external_comparators_n2o.csv'), index=False)
print(f"\nWrote external_comparators_n2o.csv ({len(n2o_df)} rows; Mt N2O/yr)")
print(n2o_df.to_string(index=False))


# =============================================================================
# CO2 — GCB 2025 Table 7 partition: EFOS + ELUC − SLAND = atmospheric source
# =============================================================================
gcb_table = [
    # (label, y0, y1, EFOS, sigEFOS, ELUC, sigELUC, SLAND, sigSLAND)
    ('1960s',     1960, 1969, 3.0, 0.2, 1.6, 0.7, 1.2, 0.5),
    ('1970s',     1970, 1979, 4.7, 0.2, 1.4, 0.7, 2.0, 0.8),
    ('1980s',     1980, 1989, 5.5, 0.3, 1.4, 0.7, 1.8, 0.8),
    ('1990s',     1990, 1999, 6.4, 0.3, 1.6, 0.7, 2.5, 0.6),
    ('2000s',     2000, 2009, 7.8, 0.4, 1.4, 0.7, 2.8, 0.7),
    ('2014-2023', 2014, 2023, 9.7, 0.5, 1.1, 0.7, 3.2, 0.9),
]
co2_rows = []
for label, y0, y1, ef, sef, el, sel, sl, ssl in gcb_table:
    src   = ef + el - sl     # atmospheric source (GtC/yr)
    sig   = (sef**2 + sel**2 + ssl**2) ** 0.5
    co2_rows.append({
        'Period_label': label, 'Year_start': y0, 'Year_end': y1,
        'Best_Mt': src * GtC_to_MtCO2,
        'Lo_Mt':   (src - sig) * GtC_to_MtCO2,
        'Hi_Mt':   (src + sig) * GtC_to_MtCO2,
        'Source': 'GCB 2025 (Friedlingstein et al. ESSD 17) Table 7: '
                  'EFOS+ELUC-SLAND = net atmospheric source',
    })
co2_df = pd.DataFrame(co2_rows)
co2_df.to_csv(os.path.join(OUT_DIR, 'external_comparators_co2.csv'), index=False)
print(f"\nWrote external_comparators_co2.csv ({len(co2_df)} rows; Mt CO2/yr)")
print(co2_df.to_string(index=False))


# =============================================================================
# DECADAL OVERLAP CHECK: print our integrated values for the same periods
# =============================================================================
print("\n" + "=" * 78)
print("OVERLAP CHECK: our integrated total vs external comparator")
print("=" * 78)

DATA = OUT_DIR
df_int_ch4 = pd.read_csv(os.path.join(DATA, 'integrated_emissions_ch4.csv'))
df_int_n2o = pd.read_csv(os.path.join(DATA, 'integrated_emissions_n2o.csv'))
df_int_co2 = pd.read_csv(os.path.join(DATA, 'integrated_emissions_co2.csv'))

def integrated_period_mean(df, scenario, y0, y1):
    sub = df[(df.Scenario == scenario) & (df.Year >= y0) & (df.Year <= y1)]
    return sub['Total_Mt'].mean()

# CH4 — period-by-period using SSP2-4.5 (representative)
print("\nCH4 (Mt CH4/yr) — historical period uses any SSP (all share historical):")
print(f"  {'Period':<14} {'Our int.':>10} {'GMB 2025 best':>14} {'Lo':>8} {'Hi':>8}")
for _, row in ch4_df.iterrows():
    our = integrated_period_mean(df_int_ch4, 'SSP2-4.5',
                                  row.Year_start, row.Year_end)
    print(f"  {row.Period_label:<14} {our:>10.1f} {row.Best_Mt:>14.1f} "
          f"{row.Lo_Mt:>8.1f} {row.Hi_Mt:>8.1f}")

print("\nN2O (Mt N2O/yr):")
print(f"  {'Period':<14} {'Our int.':>10} {'GNB 2024 best':>14} {'Lo':>8} {'Hi':>8}")
for _, row in n2o_df.iterrows():
    our = integrated_period_mean(df_int_n2o, 'SSP2-4.5',
                                  row.Year_start, row.Year_end)
    print(f"  {row.Period_label:<14} {our:>10.2f} {row.Best_Mt:>14.2f} "
          f"{row.Lo_Mt:>8.2f} {row.Hi_Mt:>8.2f}")

print("\nCO2 (Mt CO2/yr) — note conversion: 1 GtC = 3.667 Pg CO2 = 3667 Mt CO2:")
print(f"  {'Period':<14} {'Our int.':>10} {'GCB 2025 best':>14} {'Lo':>8} {'Hi':>8}")
for _, row in co2_df.iterrows():
    our = integrated_period_mean(df_int_co2, 'SSP2-4.5',
                                  row.Year_start, row.Year_end)
    print(f"  {row.Period_label:<14} {our:>10.0f} {row.Best_Mt:>14.0f} "
          f"{row.Lo_Mt:>8.0f} {row.Hi_Mt:>8.0f}")

print("\nDone.")
