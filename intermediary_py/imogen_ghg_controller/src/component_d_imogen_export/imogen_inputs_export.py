"""
imogen_inputs_export.py
=========================
Component D: produces the final IMOGEN-ready GHG emission trajectory CSVs.

This is the terminal output of the entire pipeline. It assembles per-scenario
CSVs in a wide-format ready for IMOGEN ingestion, drawing from the integrated
trajectories produced by Component C.

OUTPUT FORMAT
-------------
One CSV per SSP-RCP scenario (5 total):
  imogen_inputs_SSP1-2.6.csv
  imogen_inputs_SSP2-4.5.csv
  imogen_inputs_SSP3-7.0.csv
  imogen_inputs_SSP4-6.0.csv
  imogen_inputs_SSP5-8.5.csv

Each file has columns:
  Year                    — 1900 to 2100 (201 rows)
  CH4_anthro_Mt           — Tier-1-substituted anthropogenic CH4 emission (Mt CH4/yr)
  CH4_natural_Mt          — LPJ-GUESS natural CH4 (wetland + IFW − DCC) (Mt CH4/yr)
  CH4_total_Mt            — sum of anthropogenic and natural CH4 (Mt CH4/yr)
  N2O_anthro_Mt           — Tier-1-substituted anthropogenic N2O (Mt N2O/yr)
  N2O_natural_Mt          — LPJ-GUESS natural N2O (soil + fire) (Mt N2O/yr)
  N2O_total_Mt            — sum (Mt N2O/yr)
  CO2_EFOS_Mt             — RCMIP fossil and industrial CO2 (Mt CO2/yr)
  CO2_NEE_Mt              — LPJ-GUESS net ecosystem exchange (Mt CO2/yr)
  CO2_total_Mt            — atmospheric source = EFOS + NEE (Mt CO2/yr)

Plus a combined long-format CSV for users who prefer that:
  imogen_inputs_all_scenarios_long.csv  — Year × Scenario × Variable

UNITS
-----
All values in Mt-of-gas per year (10^9 kg per year). For CO2, this means Mt CO2,
NOT Mt C — multiply by 12/44 to convert to Mt C.

For Pg C/yr (the more common unit in carbon-cycle papers), divide CO2_total_Mt by
3666.67 (= 44/12 × 1000).
"""

# ---------------------------------------------------------------------------
# Project bootstrap
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
    OUT_C_DATA, OUT_IMOGEN_INPUTS, ensure_output_dirs,
)
from src.shared.constants import SCENARIOS

import os
import pandas as pd


# ---------------------------------------------------------------------------
# Load integrated trajectories
# ---------------------------------------------------------------------------
ensure_output_dirs()
DATA_DIR = os.environ.get('DATA_DIR', str(OUT_C_DATA))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_IMOGEN_INPUTS))
os.makedirs(OUT_DIR, exist_ok=True)

print(f'[Component D] reading integrated trajectories from {DATA_DIR}', flush=True)
print(f'[Component D] writing IMOGEN inputs to {OUT_DIR}', flush=True)


def _load_integrated(gas):
    """Load the integrated_emissions_<gas>.csv produced by Component C and
    return a per-scenario dictionary of DataFrames sorted by Year."""
    fp = os.path.join(DATA_DIR, f'integrated_emissions_{gas.lower()}.csv')
    df = pd.read_csv(fp)
    out = {}
    for scen in SCENARIOS:
        sub = df[df.Scenario == scen].sort_values('Year').reset_index(drop=True)
        out[scen] = sub
    return out


df_ch4 = _load_integrated('CH4')
df_n2o = _load_integrated('N2O')
df_co2 = _load_integrated('CO2')

# Verify each scenario has the expected 201 rows (1900-2100)
for scen in SCENARIOS:
    assert len(df_ch4[scen]) == 201, f'{scen} CH4: expected 201 rows, got {len(df_ch4[scen])}'
    assert len(df_n2o[scen]) == 201, f'{scen} N2O: expected 201 rows, got {len(df_n2o[scen])}'
    assert len(df_co2[scen]) == 201, f'{scen} CO2: expected 201 rows, got {len(df_co2[scen])}'
print('  ✓ All integrated trajectories have expected shape (201 rows × 5 scenarios × 3 gases)')


# ---------------------------------------------------------------------------
# Build per-scenario IMOGEN-input CSVs (wide format)
# ---------------------------------------------------------------------------
print('\n[Component D] producing per-scenario IMOGEN-input CSVs ...', flush=True)
all_long_rows = []

for scen in SCENARIOS:
    ch4 = df_ch4[scen]
    n2o = df_n2o[scen]
    co2 = df_co2[scen]

    # Sanity check: years align across gases
    assert (ch4.Year.values == n2o.Year.values).all()
    assert (ch4.Year.values == co2.Year.values).all()

    # Build wide-format dataframe
    out_df = pd.DataFrame({
        'Year':           ch4.Year.values,
        'CH4_anthro_Mt':  ch4.Anthro_Mt.values,
        'CH4_natural_Mt': ch4.Natural_Mt.values,
        'CH4_total_Mt':   ch4.Total_Mt.values,
        'N2O_anthro_Mt':  n2o.Anthro_Mt.values,
        'N2O_natural_Mt': n2o.Natural_Mt.values,
        'N2O_total_Mt':   n2o.Total_Mt.values,
        'CO2_EFOS_Mt':    co2.Anthro_Mt.values,    # for CO2, Anthro_Mt = EFOS only
        'CO2_NEE_Mt':     co2.Natural_Mt.values,   # natural for CO2 = LPJ-GUESS NEE
        'CO2_total_Mt':   co2.Total_Mt.values,
    })

    # Write per-scenario CSV
    out_path = os.path.join(OUT_DIR, f'imogen_inputs_{scen}.csv')
    out_df.to_csv(out_path, index=False, float_format='%.6f')
    print(f'  ✓ {scen}: 201 rows × 10 cols → {os.path.basename(out_path)}')

    # Build long-format records for the combined CSV
    for _, row in out_df.iterrows():
        for gas, anthro_col, natural_col, total_col in [
            ('CH4', 'CH4_anthro_Mt', 'CH4_natural_Mt', 'CH4_total_Mt'),
            ('N2O', 'N2O_anthro_Mt', 'N2O_natural_Mt', 'N2O_total_Mt'),
            ('CO2', 'CO2_EFOS_Mt',   'CO2_NEE_Mt',     'CO2_total_Mt'),
        ]:
            all_long_rows.append({
                'Year':       int(row.Year),
                'Scenario':   scen,
                'Gas':        gas,
                'Anthro_Mt':  row[anthro_col],
                'Natural_Mt': row[natural_col],
                'Total_Mt':   row[total_col],
                'Unit':       f'Mt {gas}/yr',
            })


# ---------------------------------------------------------------------------
# Combined long-format CSV
# ---------------------------------------------------------------------------
long_df = pd.DataFrame(all_long_rows)
long_path = os.path.join(OUT_DIR, 'imogen_inputs_all_scenarios_long.csv')
long_df.to_csv(long_path, index=False, float_format='%.6f')
print(f'\n  ✓ Combined long-format: {len(long_df):,} rows × 7 cols → {os.path.basename(long_path)}')


# ---------------------------------------------------------------------------
# Validation print: sample values from the SSP2-4.5 file
# ---------------------------------------------------------------------------
print('\n[Component D] sample values (SSP2-4.5):', flush=True)
sample_path = os.path.join(OUT_DIR, 'imogen_inputs_SSP2-4.5.csv')
sample_df = pd.read_csv(sample_path)
for yr in [1900, 1950, 2000, 2014, 2020, 2050, 2100]:
    row = sample_df[sample_df.Year == yr]
    if len(row):
        r = row.iloc[0]
        print(f'  {yr}:  CH4 anthro={r.CH4_anthro_Mt:>7.1f}  natural={r.CH4_natural_Mt:>7.1f}  total={r.CH4_total_Mt:>7.1f}')
        print(f'        N2O anthro={r.N2O_anthro_Mt:>7.2f}  natural={r.N2O_natural_Mt:>7.2f}  total={r.N2O_total_Mt:>7.2f}')
        print(f'        CO2 EFOS={r.CO2_EFOS_Mt:>9.0f}  NEE={r.CO2_NEE_Mt:>9.0f}  total={r.CO2_total_Mt:>9.0f}')

print('\n[Component D] complete.', flush=True)
