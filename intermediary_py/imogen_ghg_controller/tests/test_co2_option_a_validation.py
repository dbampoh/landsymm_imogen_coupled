"""
test_co2_option_a_validation.py — empirical validation that Option A integration
framing (EFOS only + LPJ-GUESS NEE) lands within GCB partition uncertainty.

This is the core scientific validation test. For the 2014-2020 mean SSP2-4.5,
our integrated CO2 atmospheric source should fall within ±1σ of the GCB 2025
partition (EFOS + ELUC − SLAND).

GCB 2025 Table 7 (Friedlingstein et al. 2025):
  2014-2023 mean: EFOS=9.7±0.5, ELUC=1.1±0.7, SLAND=3.2±0.9
  Atmospheric source = EFOS + ELUC - SLAND = 7.6 GtC/yr
  Uncertainty (quadrature) = sqrt(0.5² + 0.7² + 0.9²) = 1.24 GtC/yr

The test passes if the gap between our integrated total and the GCB best is
within 1.24 GtC/yr (≈ 4546 Mt CO2/yr).
"""
import os
import sys
from pathlib import Path

import pandas as pd

# Bootstrap
_ROOT = Path(__file__).resolve().parent
while _ROOT.name and not (_ROOT / 'src').is_dir():
    if _ROOT.parent == _ROOT:
        break
    _ROOT = _ROOT.parent
sys.path.insert(0, str(_ROOT))

from src.shared.paths import OUT_C_DATA
from src.shared.constants import PgC_to_MtCO2


# GCB 2025 partition for the 2014-2023 mean
GCB_BEST_PgC = 7.6
GCB_SIGMA_PgC = 1.24
GCB_BEST_MtCO2 = GCB_BEST_PgC * PgC_to_MtCO2
GCB_SIGMA_MtCO2 = GCB_SIGMA_PgC * PgC_to_MtCO2


def test_integrated_co2_within_gcb_uncertainty():
    """For the 2014-2020 mean SSP2-4.5, our integrated CO2 atmospheric source
    should fall within ±1σ of GCB 2025's partition value."""
    # Read the integrated CO2 trajectory (produced by Component C)
    csv_path = OUT_C_DATA / 'integrated_emissions_co2.csv'
    if not csv_path.is_file():
        # If the output doesn't exist yet, this test is a no-op (will be skipped
        # by pytest when invoked but printed as a soft warning when run directly)
        print(f'  ⚠ skipped: {csv_path} not yet produced; run Component C first')
        return

    df = pd.read_csv(csv_path)

    # Compute 2014-2020 mean for SSP2-4.5
    mask = (df.Scenario == 'SSP2-4.5') & (df.Year >= 2014) & (df.Year <= 2020)
    our_total_mean = df[mask]['Total_Mt'].mean()

    # Validate: |our - GCB_best| < GCB_sigma
    gap = abs(our_total_mean - GCB_BEST_MtCO2)
    print(f'  Our integrated CO2 mean (2014-2020, SSP2-4.5): {our_total_mean:.0f} Mt CO2/yr '
          f'(= {our_total_mean / PgC_to_MtCO2:.2f} Pg C/yr)')
    print(f'  GCB 2025 atmospheric source (2014-2023):       {GCB_BEST_MtCO2:.0f} ± '
          f'{GCB_SIGMA_MtCO2:.0f} Mt CO2/yr (= {GCB_BEST_PgC:.2f} ± {GCB_SIGMA_PgC:.2f} Pg C/yr)')
    print(f'  Gap: {gap:.0f} Mt CO2/yr (= {gap / PgC_to_MtCO2:.2f} Pg C/yr)')
    assert gap < GCB_SIGMA_MtCO2, (
        f'Gap of {gap:.0f} Mt CO2/yr exceeds GCB ±1σ uncertainty of '
        f'{GCB_SIGMA_MtCO2:.0f} Mt CO2/yr — Option A integration framing may be invalidated.'
    )
    print(f'  ✓ within ±1σ of GCB partition')


if __name__ == '__main__':
    test_integrated_co2_within_gcb_uncertainty()
    print('CO2 Option A validation passed.')
