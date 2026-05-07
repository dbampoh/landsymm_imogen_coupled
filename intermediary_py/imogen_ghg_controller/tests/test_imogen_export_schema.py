"""
test_imogen_export_schema.py — verifies Component D produces correctly-shaped
IMOGEN-input CSVs with the expected schema.

Tests:
1. All 5 per-scenario CSVs exist after Component D runs
2. Combined long-format CSV exists
3. Each per-scenario CSV has 201 rows (1900-2100) and 10 columns
4. Required columns present in expected order
5. No NaN values in data columns
6. Year column is monotonically increasing 1900 → 2100
"""
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Bootstrap
_ROOT = Path(__file__).resolve().parent
while _ROOT.name and not (_ROOT / 'src').is_dir():
    if _ROOT.parent == _ROOT:
        break
    _ROOT = _ROOT.parent
sys.path.insert(0, str(_ROOT))

from src.shared.paths import OUT_IMOGEN_INPUTS
from src.shared.constants import SCENARIOS


EXPECTED_COLS = [
    'Year',
    'CH4_anthro_Mt', 'CH4_natural_Mt', 'CH4_total_Mt',
    'N2O_anthro_Mt', 'N2O_natural_Mt', 'N2O_total_Mt',
    'CO2_EFOS_Mt',   'CO2_NEE_Mt',     'CO2_total_Mt',
]


def test_per_scenario_files_exist():
    for scen in SCENARIOS:
        path = OUT_IMOGEN_INPUTS / f'imogen_inputs_{scen}.csv'
        assert path.is_file(), f'Missing: {path}'

def test_combined_long_format_exists():
    path = OUT_IMOGEN_INPUTS / 'imogen_inputs_all_scenarios_long.csv'
    assert path.is_file(), f'Missing: {path}'

def test_per_scenario_schema():
    for scen in SCENARIOS:
        path = OUT_IMOGEN_INPUTS / f'imogen_inputs_{scen}.csv'
        df = pd.read_csv(path)
        assert df.shape == (201, 10), f'{scen}: expected (201, 10), got {df.shape}'
        assert list(df.columns) == EXPECTED_COLS, \
            f'{scen}: column order mismatch. Expected {EXPECTED_COLS}, got {list(df.columns)}'
        # No NaN values anywhere
        assert not df.isna().any().any(), f'{scen}: contains NaN values'
        # Years monotonically 1900-2100
        assert (df['Year'].values == np.arange(1900, 2101)).all(), \
            f'{scen}: Year column not 1900..2100'

def test_long_format_schema():
    path = OUT_IMOGEN_INPUTS / 'imogen_inputs_all_scenarios_long.csv'
    df = pd.read_csv(path)
    expected_long_cols = ['Year', 'Scenario', 'Gas', 'Anthro_Mt', 'Natural_Mt', 'Total_Mt', 'Unit']
    assert list(df.columns) == expected_long_cols, \
        f'Long-format column mismatch. Expected {expected_long_cols}, got {list(df.columns)}'
    # 5 scenarios × 3 gases × 201 years = 3015 rows
    assert len(df) == 5 * 3 * 201, f'Expected 3015 rows, got {len(df)}'
    # All scenarios present
    assert set(df.Scenario.unique()) == set(SCENARIOS)
    # All gases present
    assert set(df.Gas.unique()) == {'CH4', 'N2O', 'CO2'}


if __name__ == '__main__':
    test_per_scenario_files_exist()
    test_combined_long_format_exists()
    test_per_scenario_schema()
    test_long_format_schema()
    print('All IMOGEN export schema tests passed.')
