"""
paths.py — central path configuration for the project
======================================================

Resolves paths for inputs, outputs, and reference data based on the project
root directory. Uses environment variables when set, falls back to a discovered
project root otherwise.

Usage in any script:
    from imogen_ghg_controller.shared.paths import (
        INPUTS_DIR, OUTPUTS_DIR,
        FAO_DIR, PLUM_DIR, LPJG_HIST_DIR, LPJG_SCEN_DIR,
        RCMIP_DIR, FAIR_ERF_DIR,
        OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
        OUT_B_DATA, OUT_B_FIGS, OUT_B_SUMMARIES,
        OUT_C_DATA, OUT_C_FIGS, OUT_C_SUMMARIES,
        OUT_IMOGEN_INPUTS,
    )

Override by setting IMOGEN_GHG_ROOT before invoking the scripts.
"""
import os
from pathlib import Path

# -----------------------------------------------------------------------------
# Determine project root.
# Priority: 1) IMOGEN_GHG_ROOT env var; 2) walk up from this file to find
# a directory that contains 'src/' AND 'inputs/' OR 'README.md' at top level.
# -----------------------------------------------------------------------------
def _find_project_root():
    env_root = os.environ.get('IMOGEN_GHG_ROOT')
    if env_root:
        return Path(env_root).resolve()

    # Walk up from this file location
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / 'src').is_dir() and (parent / 'README.md').is_file():
            return parent
    # Fallback: 3 levels up (src/shared/paths.py → project root)
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _find_project_root()


# -----------------------------------------------------------------------------
# Top-level directories
# -----------------------------------------------------------------------------
INPUTS_DIR  = PROJECT_ROOT / 'inputs'
OUTPUTS_DIR = PROJECT_ROOT / 'outputs'
DOCS_DIR    = PROJECT_ROOT / 'docs'
SRC_DIR     = PROJECT_ROOT / 'src'


# -----------------------------------------------------------------------------
# Input subdirectories
# -----------------------------------------------------------------------------
FAO_DIR         = INPUTS_DIR / 'fao'
PLUM_DIR        = INPUTS_DIR / 'plum'
LPJG_HIST_DIR   = INPUTS_DIR / 'lpjg' / 'historical'
LPJG_SCEN_DIR   = INPUTS_DIR / 'lpjg' / 'scenarios'
RCMIP_DIR       = INPUTS_DIR / 'rcmip'
FAIR_ERF_DIR    = INPUTS_DIR / 'fair_erf'
EDGAR_DIR       = INPUTS_DIR / 'edgar'
REF_PDFS_DIR    = INPUTS_DIR / 'reference_pdfs'


# -----------------------------------------------------------------------------
# Output subdirectories per component
# -----------------------------------------------------------------------------
OUT_A_DATA       = OUTPUTS_DIR / 'component_a' / 'data'
OUT_A_FIGS       = OUTPUTS_DIR / 'component_a' / 'figures'
OUT_A_SUMMARIES  = OUTPUTS_DIR / 'component_a' / 'summaries'

OUT_B_DATA       = OUTPUTS_DIR / 'component_b' / 'data'
OUT_B_FIGS       = OUTPUTS_DIR / 'component_b' / 'figures'
OUT_B_SUMMARIES  = OUTPUTS_DIR / 'component_b' / 'summaries'

OUT_C_DATA       = OUTPUTS_DIR / 'component_c' / 'data'
OUT_C_FIGS       = OUTPUTS_DIR / 'component_c' / 'figures'
OUT_C_SUMMARIES  = OUTPUTS_DIR / 'component_c' / 'summaries'

OUT_IMOGEN_INPUTS = OUTPUTS_DIR / 'imogen_inputs'


# -----------------------------------------------------------------------------
# Specific canonical input file paths (centralised so scripts don't hard-code)
# -----------------------------------------------------------------------------
RCMIP_CSV    = RCMIP_DIR    / 'rcmip-emissions-annual-means-v5-1-0.csv'
FAIR_ERF_CSV = FAIR_ERF_DIR / 'natural.csv'

FAO_PRODUCTION_CSV  = FAO_DIR / 'Production_Crops_Livestock_E_All_Data.csv'
FAO_EMISSIONS_CSV   = FAO_DIR / 'Emissions_Totals_E_All_Data.csv'
FAO_FERTILIZERS_CSV = FAO_DIR / 'Inputs_FertilizersNutrient_E_All_Data.csv'

PLUM_CROP_CSV       = PLUM_DIR / 'plum_crop_s1.csv'
PLUM_LIVESTOCK_TXT  = PLUM_DIR / 'Livestock_counts.txt'
PLUM_RICE_OPT_A_ZIP = PLUM_DIR / 'rice_cult_plum_scen_using_plum_irrig_optA.zip'
PLUM_RICE_OPT_B_ZIP = PLUM_DIR / 'rice_cult_plum_scen_using_plum_irrig_optB.zip'

# EDGAR datasets (used by Component A historical sector scripts as a
# benchmark inventory and for sector/total proportioning in scenario plots).
# - EDGAR_CH4_NEW and EDGAR_N2O_NEW: the EDGAR 2025 release covering 1970-2024.
#   Used in 16 of 17 EDGAR-touching scripts.
# - EDGAR_OLD_ESSD: the older ESSD release (essd_ghg_data_emiss.xlsx). Used
#   ONLY by n2o_synfert_processing.py because the old release has the 4D11
#   "Synthetic Fertilizers" sub-category that the new release aggregates into
#   3.C.4 + 3.C.5 (= all agricultural managed soils). Required for the
#   `EDGAR_GgN2O` benchmark column on n2o_synfert_global.csv.
# - EDGAR_IEA_CO2_NEW: the IEA-EDGAR CO2 release. Currently NOT used by any
#   pipeline script — included here for forward compatibility if a CO2
#   benchmark plot is ever added.
EDGAR_CH4_NEW    = EDGAR_DIR / 'EDGAR_CH4_1970_2024.xlsx'
EDGAR_N2O_NEW    = EDGAR_DIR / 'EDGAR_N2O_1970_2024.xlsx'
EDGAR_OLD_ESSD   = EDGAR_DIR / 'essd_ghg_data_emiss.xlsx'
EDGAR_IEA_CO2_NEW = EDGAR_DIR / 'IEA_EDGAR_CO2_1970_2024.xlsx'


def ensure_output_dirs():
    """Create all output directories. Called at the start of any script that writes."""
    for d in (OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
              OUT_B_DATA, OUT_B_FIGS, OUT_B_SUMMARIES,
              OUT_C_DATA, OUT_C_FIGS, OUT_C_SUMMARIES,
              OUT_IMOGEN_INPUTS):
        d.mkdir(parents=True, exist_ok=True)


if __name__ == '__main__':
    # Diagnostic: print all resolved paths
    print(f'PROJECT_ROOT: {PROJECT_ROOT}')
    print(f'INPUTS_DIR:   {INPUTS_DIR}')
    print(f'OUTPUTS_DIR:  {OUTPUTS_DIR}')
    print(f'  exists: PROJECT_ROOT={PROJECT_ROOT.exists()}, '
          f'INPUTS_DIR={INPUTS_DIR.exists()}, OUTPUTS_DIR={OUTPUTS_DIR.exists()}')
