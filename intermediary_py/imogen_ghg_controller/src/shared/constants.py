"""
constants.py — physical constants, unit conversions, scenario lists, file naming
================================================================================

Centralizes values that were previously duplicated across multiple scripts.
All values traceable to peer-reviewed sources or canonical RCMIP/CMIP6 conventions.
"""

# =============================================================================
# Scenarios
# =============================================================================
# The five SSP-RCP scenario keys used throughout the project.
# Order matters for plotting and for the runner's iteration order.
SCENARIOS = [
    'SSP1-2.6',
    'SSP2-4.5',
    'SSP3-7.0',
    'SSP4-6.0',
    'SSP5-8.5',
]

# Mapping from our display labels to LPJ-GUESS file tags
LPJG_TAG_MAP = {
    'SSP1-2.6': 'ssp1rcp26',
    'SSP2-4.5': 'ssp2rcp45',
    'SSP3-7.0': 'ssp3rcp70',
    'SSP4-6.0': 'ssp4rcp60',
    'SSP5-8.5': 'ssp5rcp85',
}

# Mapping from our display labels to RCMIP scenario names
SCEN_RCMIP_MAP = {
    'SSP1-2.6': 'ssp126',
    'SSP2-4.5': 'ssp245',
    'SSP3-7.0': 'ssp370',
    'SSP4-6.0': 'ssp460',
    'SSP5-8.5': 'ssp585',
}


# =============================================================================
# Time-period constants
# =============================================================================
# HIST_END is the last year before RCMIP scenarios begin diverging.
# Empirically verified: RCMIP scenario records share identical values up to
# 2014 and begin diverging at 2015 (Round C6 finding).
# Used to draw the historical period as a single black line in plots.
HIST_END = 2014

# First year of our IPCC Tier 1 inventory (FAO data starts 1961, but Tier 1
# methodology applied from 1970 for consistent global coverage).
TIER1_START = 1970

# First year of scenario projections (PLUMv2 uses 2020 as anchor).
SCENARIO_START = 2020


# =============================================================================
# Unit-conversion factors
# =============================================================================
# Pg C → Mt CO2: multiply by (44/12) × 1000
# Where 44/12 = molar mass ratio CO2/C, and × 1000 converts Pg → Mt.
PgC_to_MtCO2 = (44.0 / 12.0) * 1000.0

# Tg N → Tg N2O: multiply by 44/28
# Where 44/28 = molar mass ratio N2O / 2N (one N2O molecule contains 2 N atoms).
TgN_to_TgN2O = 44.0 / 28.0
TgN2O_to_TgN = 28.0 / 44.0


# =============================================================================
# Canonical CSV filenames produced per gas
# =============================================================================
# These are referenced by the runner and tests; centralizing avoids typos.
INTEGRATED_CSV_NAMES = {
    'CH4': 'integrated_emissions_ch4.csv',
    'N2O': 'integrated_emissions_n2o.csv',
    'CO2': 'integrated_emissions_co2.csv',
}
EXTERNAL_CSV_NAMES = {
    'CH4': 'external_comparators_ch4.csv',
    'N2O': 'external_comparators_n2o.csv',
    'CO2': 'external_comparators_co2.csv',
}
HYBRID_CSV_NAMES = {
    'CH4': 'hybrid_comparator_ch4.csv',
    'N2O': 'hybrid_comparator_n2o.csv',
    'CO2': 'hybrid_comparator_co2.csv',
}
CONVENTIONAL_CSV_NAMES = {
    'CH4': 'conventional_comparator_ch4.csv',
    'N2O': 'conventional_comparator_n2o.csv',
    'CO2': 'conventional_comparator_co2.csv',
}
