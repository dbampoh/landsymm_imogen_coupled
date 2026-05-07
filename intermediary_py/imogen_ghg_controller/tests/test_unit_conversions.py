"""Tests for unit conversion factors in src.shared.constants."""

import sys
from pathlib import Path

# Bootstrap: add project root
_ROOT = Path(__file__).resolve().parent
while _ROOT.name and not (_ROOT / 'src').is_dir():
    if _ROOT.parent == _ROOT:
        break
    _ROOT = _ROOT.parent
sys.path.insert(0, str(_ROOT))

from src.shared.constants import PgC_to_MtCO2, TgN_to_TgN2O, TgN2O_to_TgN


def test_PgC_to_MtCO2():
    """Pg C → Mt CO2 should be 44/12 × 1000 = 3666.6667."""
    assert abs(PgC_to_MtCO2 - 3666.66667) < 0.01

def test_PgC_round_trip_to_PgC():
    """1 Pg C should convert to ~3667 Mt CO2 → back to 1 Pg C (±1e-3)."""
    one_PgC = 1.0
    as_MtCO2 = one_PgC * PgC_to_MtCO2
    back_to_PgC = as_MtCO2 / PgC_to_MtCO2
    assert abs(back_to_PgC - 1.0) < 1e-9

def test_TgN_to_TgN2O():
    """Tg N → Tg N2O = 44/28 (one N2O molecule has 2 N atoms)."""
    expected = 44.0 / 28.0
    assert abs(TgN_to_TgN2O - expected) < 1e-9

def test_TgN2O_TgN_round_trip():
    """N → N2O → N should round-trip exactly."""
    one_TgN = 1.0
    as_N2O = one_TgN * TgN_to_TgN2O
    back_to_N = as_N2O * TgN2O_to_TgN
    assert abs(back_to_N - 1.0) < 1e-9

def test_known_value_1PgC_is_about_3p67_GtCO2():
    """1 Pg C = 3.667 Gt CO2 — well-known value cited in IPCC AR6."""
    expected_GtCO2 = 3.667
    actual = 1.0 * PgC_to_MtCO2 / 1000.0   # convert Mt to Gt
    assert abs(actual - expected_GtCO2) < 1e-3


if __name__ == '__main__':
    test_PgC_to_MtCO2()
    test_PgC_round_trip_to_PgC()
    test_TgN_to_TgN2O()
    test_TgN2O_TgN_round_trip()
    test_known_value_1PgC_is_about_3p67_GtCO2()
    print('All unit conversion tests passed.')
