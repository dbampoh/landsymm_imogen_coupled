"""
budget_refs.py — observation-constrained budget reference values
================================================================

Centralized canonical values from:
  - GMB 2025 (Saunois et al., ESSD 17, 1873-1958) — atmospheric CH4 inversions
  - GNB 2024 (Tian et al., ESSD 16, 2543-2604) — atmospheric N2O inversions
  - GCB 2025 (Friedlingstein et al., ESSD 17, 965-1039) — Table 7 partition

All values were verified against the source PDFs by reading the
executive-summary text directly during Round C4 of the project.

These reference values are used:
  1. As historical-period step-band references in plots
  2. As anchor points for the hybrid full-trajectory comparator
  3. As validation benchmarks for our integrated trajectories
"""

from .constants import TgN_to_TgN2O, PgC_to_MtCO2


# =============================================================================
# CH4 — GMB 2025 atmospheric-inversion top-down totals
# =============================================================================
# Each tuple: (year_start, year_end, best, lo, hi) in Tg CH4/yr (= Mt CH4/yr).
# Source: Saunois et al. 2025, executive summary text, paragraphs covering
# global total emission for 2000s, 2010s, and 2020.
GMB_CH4_PERIODS = [
    (2000, 2009, 543, 528, 578),
    (2010, 2019, 575, 553, 586),
    (2020, 2020, 608, 581, 627),
]


# =============================================================================
# N2O — GNB 2024 atmospheric-inversion top-down totals
# =============================================================================
# Each tuple: (year_start, year_end, best_TgN, lo_TgN, hi_TgN) in Tg N/yr.
# Source: Tian et al. 2024, executive summary, atmospheric inversions section.
# Convert to Tg N2O/yr in helper function below.
GNB_N_PERIODS = [
    (1997, 1997, 15.4, 13.9, 16.7),
    (2010, 2019, 17.4, 15.8, 19.2),
    (2020, 2020, 17.0, 16.6, 17.4),
]


# =============================================================================
# CO2 — GCB 2025 Table 7 partition
# =============================================================================
# Each tuple: (year_start, year_end, EFOS, sigEFOS, ELUC, sigELUC, SLAND, sigSLAND)
# All values in GtC/yr. Atmospheric source = EFOS + ELUC - SLAND.
# Source: Friedlingstein et al. 2025, Table 7.
GCB_PARTITION = [
    ('1960s',     1960, 1969, 3.0, 0.2, 1.6, 0.7, 1.2, 0.5),
    ('1970s',     1970, 1979, 4.7, 0.2, 1.4, 0.7, 2.0, 0.8),
    ('1980s',     1980, 1989, 5.5, 0.3, 1.4, 0.7, 1.8, 0.8),
    ('1990s',     1990, 1999, 6.4, 0.3, 1.6, 0.7, 2.5, 0.6),
    ('2000s',     2000, 2009, 7.8, 0.4, 1.4, 0.7, 2.8, 0.7),
    ('2014-2023', 2014, 2023, 9.7, 0.5, 1.1, 0.7, 3.2, 0.9),
]


# =============================================================================
# Helper functions returning combined values in Mt-of-gas units
# =============================================================================
def gmb_combined_ch4(period):
    """Return (best, lo, hi) in Mt CH4/yr for a GMB_CH4_PERIODS tuple.
    Pass-through (units already match)."""
    _, _, best, lo, hi = period
    return best, lo, hi


def gnb_combined_n2o(period):
    """Return (best, lo, hi) in Mt N2O/yr for a GNB_N_PERIODS tuple.
    Converts Tg N → Tg N2O via × 44/28.
    """
    _, _, best_n, lo_n, hi_n = period
    return best_n * TgN_to_TgN2O, lo_n * TgN_to_TgN2O, hi_n * TgN_to_TgN2O


def gcb_atmospheric_source_co2(period):
    """Return (best, lo, hi) in Mt CO2/yr for a GCB_PARTITION tuple.
    Computes EFOS + ELUC - SLAND in GtC/yr, then converts to Mt CO2/yr.
    Uncertainty propagated as quadrature sum of component sigmas.
    """
    _, y0, y1, ef, sef, el, sel, sl, ssl = period
    src = ef + el - sl
    sig = (sef ** 2 + sel ** 2 + ssl ** 2) ** 0.5
    return (
        src * PgC_to_MtCO2,
        (src - sig) * PgC_to_MtCO2,
        (src + sig) * PgC_to_MtCO2,
    )
