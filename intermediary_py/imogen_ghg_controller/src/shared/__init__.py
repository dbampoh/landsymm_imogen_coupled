"""
imogen_ghg_controller.shared
==============================
Shared constants, helpers, and reference values used across all components.

By centralizing these, we eliminate the ~50 lines of duplicated boilerplate
that previously lived at the top of every plotting script. Any change to
visualisation conventions, scenario palettes, unit conversions, or budget
reference values is now made in exactly one place.

Modules:
    constants    — physical constants, unit conversions, scenario list
    plot_style   — colour palette, axis-styling helpers, smoothing helpers
    budget_refs  — observation-constrained values from GMB / GNB / GCB / FAIR-ERF
"""

from .constants import (
    # Scenario keys (the canonical 5-SSP list used throughout)
    SCENARIOS,
    LPJG_TAG_MAP,
    SCEN_RCMIP_MAP,
    # Time-period constants
    HIST_END,
    TIER1_START,
    SCENARIO_START,
    # Unit-conversion factors
    PgC_to_MtCO2,
    TgN_to_TgN2O,
    TgN2O_to_TgN,
    # Common file names / paths
    INTEGRATED_CSV_NAMES,
    EXTERNAL_CSV_NAMES,
    HYBRID_CSV_NAMES,
    CONVENTIONAL_CSV_NAMES,
)

from .paths import (
    PROJECT_ROOT,
    INPUTS_DIR, OUTPUTS_DIR, DOCS_DIR, SRC_DIR,
    FAO_DIR, PLUM_DIR, LPJG_HIST_DIR, LPJG_SCEN_DIR,
    RCMIP_DIR, FAIR_ERF_DIR, EDGAR_DIR, REF_PDFS_DIR,
    OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
    OUT_B_DATA, OUT_B_FIGS, OUT_B_SUMMARIES,
    OUT_C_DATA, OUT_C_FIGS, OUT_C_SUMMARIES,
    OUT_IMOGEN_INPUTS,
    RCMIP_CSV, FAIR_ERF_CSV,
    FAO_PRODUCTION_CSV, FAO_EMISSIONS_CSV, FAO_FERTILIZERS_CSV,
    PLUM_CROP_CSV, PLUM_LIVESTOCK_TXT, PLUM_RICE_OPT_A_ZIP, PLUM_RICE_OPT_B_ZIP,
    EDGAR_CH4_NEW, EDGAR_N2O_NEW, EDGAR_OLD_ESSD, EDGAR_IEA_CO2_NEW,
    ensure_output_dirs,
)

from .plot_style import (
    # Colours
    SCEN_COLORS,
    HIST_COLOR,
    CMP_COLOR,
    # Style dicts
    SC, GK, TK, LK, PK,
    # Helpers
    sax,
    rmean,
    rmean_segmented,
    split_by_period,
    step_band_horizontal,
    step_line_horizontal,
)

from .budget_refs import (
    GMB_CH4_PERIODS,
    GNB_N_PERIODS,
    GCB_PARTITION,
    gmb_combined_ch4,
    gnb_combined_n2o,
    gcb_atmospheric_source_co2,
)

__all__ = [
    'SCENARIOS', 'LPJG_TAG_MAP', 'SCEN_RCMIP_MAP',
    'HIST_END', 'TIER1_START', 'SCENARIO_START',
    'PgC_to_MtCO2', 'TgN_to_TgN2O', 'TgN2O_to_TgN',
    'INTEGRATED_CSV_NAMES', 'EXTERNAL_CSV_NAMES',
    'HYBRID_CSV_NAMES', 'CONVENTIONAL_CSV_NAMES',
    'SCEN_COLORS', 'HIST_COLOR', 'CMP_COLOR',
    'SC', 'GK', 'TK', 'LK', 'PK',
    'sax', 'rmean', 'rmean_segmented', 'split_by_period',
    'step_band_horizontal', 'step_line_horizontal',
    'GMB_CH4_PERIODS', 'GNB_N_PERIODS', 'GCB_PARTITION',
    'gmb_combined_ch4', 'gnb_combined_n2o',
    'gcb_atmospheric_source_co2',
]
