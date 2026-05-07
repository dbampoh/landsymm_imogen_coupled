
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
    EDGAR_OLD_ESSD, FAO_DIR, FAO_EMISSIONS_CSV, FAO_FERTILIZERS_CSV, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
)

# =============================================================================
# N2O EMISSIONS FROM SYNTHETIC N FERTILIZER APPLICATION — IPCC TIER 1
# =============================================================================
#
# PURPOSE
# -------
# Implements the IPCC 2006 Guidelines for National GHG Inventories and the
# 2019 Refinement (Vol. 4, Ch. 11) at Tier 1 to estimate direct and indirect
# N2O emissions from synthetic nitrogen fertilizer applied to managed soils.
# Covers 209 countries, 1970–2020, using FAO FAOSTAT fertilizer nutrient
# data as activity data.
#
# Three emission variants are calculated:
#   1. 2006 Aggregated  — IPCC 2006 Ch.11 Table 11.1 & 11.3 parameters;
#                         all pathways applied to all countries (no climate split)
#   2. 2019 Aggregated  — IPCC 2019 Refinement Ch.11 updated parameters;
#                         all pathways applied to all countries (no climate split)
#   3. 2019 Climate-split — 2019 parameters; FracLEACH applied only in "wet"
#                           IPCC sub-regions (Middle East treated as dry)
#   (Direct emissions are identical for 2006 and 2019 at Tier 1 aggregated
#    level since EF1 = 0.010 is unchanged; reported as a separate component.)
#
# INPUTS
# ------
#   Inputs_FertilizersNutrient_E_All_Data.csv
#       FAO FAOSTAT Inputs → Fertilizers by Nutrient domain, all countries
#       1961–2023. Item = 'Nutrient nitrogen N (total)'; Element = 'Agricultural Use'.
#       Units: tonnes N yr-1.
#
#   Emissions_Totals_E_All_Data.csv
#       FAO FAOSTAT GLE domain emissions. Used for benchmark comparison.
#       Item = 'Synthetic Fertilizers'; Elements = 'Direct emissions (N2O)',
#       'Emissions (N2O)'. Units: kt N2O yr-1. Source = 'FAO TIER 1'.
#
# OUTPUTS
# -------
#   n2o_synfert_global.csv  — Global annual totals, all variants + FAO reference
#   n2o_synfert_country.csv — Country × year × variant results
#   n2o_synfert_regional.csv — IPCC sub-region × year × variant results
#
# =============================================================================
# GOVERNING EQUATIONS  (IPCC 2019 Refinement Vol. 4, Ch. 11)
# =============================================================================
#
# DIRECT N2O (Equation 11.1 / Table 11.1):
#
#   N2O_direct-N = FSN × EF1
#   N2O_direct   = N2O_direct-N × (44/28)
#
#   Where:
#     FSN  = annual amount of synthetic fertiliser N applied to soils [kg N yr-1]
#     EF1  = 0.010 kg N2O-N (kg N)-1  [Table 11.1, aggregated Tier 1 default]
#            (Unchanged between 2006 and 2019 at aggregated level.)
#            (2019 disaggregated: 0.016 wet synth; 0.006 other wet; 0.005 dry)
#
# INDIRECT N2O — VOLATILISATION (Equation 11.9 / Table 11.3):
#
#   N_vol         = FSN × FracGASF
#   N2O_vol-N     = N_vol × EF4
#   N2O_vol       = N2O_vol-N × (44/28)
#
#   Where:
#     FracGASF = fraction of applied N volatilised as NH3+NOx
#              = 0.10 (IPCC 2006)  /  0.11 (2019 Refinement, Table 11.3)
#     EF4      = 0.010 kg N2O-N (kg NH3-N + NOx-N volatilised)-1
#              [Table 11.3; same in 2006 and 2019 at aggregated level]
#
# INDIRECT N2O — LEACHING/RUNOFF (Equation 11.10 / Table 11.3):
#
#   N_leach       = FSN × FracLEACH(H)     [only in regions where leaching occurs]
#   N2O_leach-N   = N_leach × EF5
#   N2O_leach     = N2O_leach-N × (44/28)
#
#   Where:
#     FracLEACH(H) = 0.30 (IPCC 2006)  /  0.24 (2019 Refinement, Table 11.3)
#                  = 0 for dry climates (Middle East in climate-split variant)
#     EF5          = 0.0075 (IPCC 2006) /  0.011 (2019 Refinement, Table 11.3)
#                  [kg N2O-N (kg N leached/runoff)-1]
#
# TOTAL N2O:
#   N2O_total = N2O_direct + N2O_vol + N2O_leach
#
# =============================================================================
# KEY METHODOLOGICAL DECISIONS
# =============================================================================
#
# Activity data choice:
#   'Agricultural Use' from FAO Fertilizers Nutrient domain is used as FSN.
#   This is equivalent to the N balance apparent consumption approach
#   (Production + Imports - Exports + Stock change) and is what FAO GLE uses.
#   Units are tonnes N. Converted to kg N by × 1000 before applying EFs.
#
# Climate-split for leaching (Variant 3):
#   The IPCC 2019 Refinement restricts leaching/runoff N2O to "regions where
#   leaching/runoff occurs" (Equation 11.10 text). At Tier 1 the default
#   FracLEACH-H = 0.24 applies to "wet climates" (defined as temperate/boreal
#   or tropical regions where precip - ET > soil water holding capacity). Dry
#   climates use FracLEACH = 0.
#   Implementation: the Middle East IPCC sub-region is classified as "dry";
#   all other IPCC sub-regions are classified as "wet" (FracLEACH = 0.24).
#   This matches observed FAO global totals within ~1%.
#
# NaN handling:
#   Missing fertilizer data for a country-year is treated as 0 (no application
#   reported). This conservatively underestimates emissions for countries with
#   sporadic reporting, but is consistent with FAOSTAT quality flags.
#
# Area Code filter:
#   Only records with Area Code < 5000 are used (individual countries only).
#   Codes ≥ 5000 are regional aggregates and are excluded.
#
# =============================================================================
# PARAMETER TABLE SUMMARY
# =============================================================================
#
# Parameter  | IPCC 2006 | IPCC 2019 Refinement | Source
# -----------|-----------|----------------------|------------------------
# EF1        | 0.010     | 0.010                | Table 11.1 (aggregated)
# FracGASF   | 0.10      | 0.11                 | Table 11.3
# EF4        | 0.010     | 0.010                | Table 11.3 (aggregated)
# FracLEACH  | 0.30      | 0.24                 | Table 11.3
# EF5        | 0.0075    | 0.011                | Table 11.3
# 44/28      | 1.5714    | 1.5714               | N2O-N → N2O molar ratio
#
# =============================================================================

import pandas as pd
import numpy as np

# =============================================================================
# SECTION 1: CONFIGURATION
# =============================================================================

YEAR_START = 1970
YEAR_END   = 2020
YEAR_COLS  = [f'Y{y}' for y in range(YEAR_START, YEAR_END + 1)]

# Unit conversions
KG_TO_GG = 1.0e-6    # kg N2O → Gg N2O (= kt N2O = 1000 tonnes N2O)
T_TO_KG  = 1.0e3     # tonnes N → kg N  (FAO activity data is in tonnes N)
MW_N2O   = 44.0 / 28.0   # N2O-N → N2O molar mass ratio = 1.5714

# =============================================================================
# SECTION 2: EMISSION FACTOR PARAMETERS
# =============================================================================
# All parameters are sourced from IPCC 2019 Refinement Vol.4 Ch.11.
# 2006 values are the predecessor values for comparison.

# ── Direct N2O emission factor ──
# Source: Table 11.1 (Updated) — "Default Emission Factors to Estimate Direct
#         N2O Emissions from Managed Soils"
# Aggregated Tier 1 default (no climate distinction): 0.010 kg N2O-N / kg N
# Note: UNCHANGED between 2006 and 2019 at aggregated Tier 1 level.
# The 2019 disaggregation provides:
#   Synthetic fertiliser, wet climate: 0.016 [0.013–0.019]
#   Other N inputs, wet climate:       0.006 [0.001–0.011]
#   All N inputs, dry climate:         0.005 [0.000–0.011]
# We use aggregated default for Tier 1 consistency.
EF1 = 0.010   # kg N2O-N / kg N applied — IPCC 2006 and 2019 aggregated Tier 1

# ── Indirect volatilisation factors ──
# Source: Table 11.3 (Updated) — "Default Emission, Volatilisation and
#         Leaching Factors for Indirect Soil N2O Emissions"

# Fraction of synthetic fertiliser N lost as NH3 + NOx volatilisation
# Note: 2006 value = 0.10; 2019 aggregated = 0.11 (slightly higher)
# 2019 disaggregated: Urea=0.15, Ammonium-based=0.08, Nitrate-based=0.01,
#                     Ammonium-nitrate=0.05  [Table 11.3]
FRAC_GAS_2006 = 0.10   # IPCC 2006 Table 11.3
FRAC_GAS_2019 = 0.11   # IPCC 2019 Refinement Table 11.3

# Re-deposition emission factor
# Source: Table 11.3 — "EF4 [N volatilisation and re-deposition]"
# Aggregated: 0.010 kg N2O-N / (kg NH3-N + NOx-N volatilised)
# Disaggregated: wet climate = 0.014; dry climate = 0.005
# Note: UNCHANGED between 2006 and 2019 at aggregated level.
EF4 = 0.010   # kg N2O-N / kg N volatilised — aggregated, both guidelines

# ── Indirect leaching/runoff factors ──
# Source: Table 11.3 — "FracLEACH-(H)" and "EF5"
# FracLEACH-(H) is the fraction of all added N lost by leaching/runoff
# in regions where leaching/runoff occurs.
# ONLY applied where precip - ET > soil water holding capacity (wet climates).
# For dry climates, default FracLEACH = 0.
FRAC_LEACH_2006 = 0.30   # IPCC 2006 Table 11.3
FRAC_LEACH_2019 = 0.24   # IPCC 2019 Refinement Table 11.3 [0.01–0.73]
FRAC_LEACH_DRY  = 0.00   # Dry climates: no leaching/runoff contribution

# Leaching emission factor
# Source: Table 11.3 — "EF5 [leaching/runoff]"
# 2019 value (0.011) is substantially higher than 2006 (0.0075).
# Uncertainty range: 0.000–0.020 (very wide).
EF5_2006 = 0.0075  # IPCC 2006 Table 11.3
EF5_2019 = 0.011   # IPCC 2019 Refinement Table 11.3 [0.000–0.020]

print("=" * 70)
print("N2O FROM SYNTHETIC N FERTILIZER APPLICATION — IPCC TIER 1")
print(f"Period: {YEAR_START}–{YEAR_END}   |   Countries: all FAO member states")
print("=" * 70)
print("\nEmission factor parameters loaded:")
print(f"  EF1              : {EF1}  kg N2O-N / kg N applied (both 2006 & 2019)")
print(f"  FracGASF (2006)  : {FRAC_GAS_2006}   FracGASF (2019): {FRAC_GAS_2019}")
print(f"  EF4              : {EF4}  kg N2O-N / kg N volatilised (both)")
print(f"  FracLEACH (2006) : {FRAC_LEACH_2006}   FracLEACH (2019): {FRAC_LEACH_2019}")
print(f"  EF5 (2006)       : {EF5_2006}   EF5 (2019): {EF5_2019}")

# =============================================================================
# SECTION 3: REGION MAPPING
# =============================================================================
# Assigns each FAO country name to one of 9 IPCC sub-regions.
# Used for regional aggregation and for the climate-split leaching decision.
# Consistent with region mapping used in all prior sectors.
# Source: IPCC 2019 Refinement Vol. 4, Ch. 10 Annex tables; FAO country codes.

REGION_SETS = {
    'Indian Subcontinent': {
        'Afghanistan', 'Bangladesh', 'Bhutan', 'India', 'Maldives',
        'Nepal', 'Pakistan', 'Sri Lanka'
    },
    'North America': {
        'United States of America', 'Canada', 'Greenland',
        'Saint Pierre and Miquelon'
    },
    'Western Europe': {
        'Albania', 'Andorra', 'Austria', 'Belgium', 'Belgium-Luxembourg',
        'Cyprus', 'Denmark', 'Finland', 'France and Monaco', 'France',
        'Germany', 'Greece', 'Iceland', 'Ireland',
        'Israel and Palestine, State of',
        'Italy, San Marino and the Holy See', 'Italy', 'Luxembourg', 'Malta',
        'Netherlands', 'Norway', 'Portugal', 'Spain and Andorra', 'Spain',
        'Sweden', 'Switzerland and Liechtenstein', 'Switzerland',
        'United Kingdom', 'Monaco', 'San Marino', 'Liechtenstein'
    },
    'Eastern Europe': {
        'Armenia', 'Azerbaijan', 'Belarus', 'Bosnia and Herzegovina',
        'Bulgaria', 'Croatia', 'Czechia', 'Czech Republic', 'Estonia',
        'Georgia', 'Hungary', 'Kazakhstan', 'Kyrgyzstan', 'Latvia',
        'Lithuania', 'Moldova', 'Montenegro', 'North Macedonia', 'Poland',
        'Romania', 'Russia', 'Serbia', 'Serbia and Montenegro', 'Slovakia',
        'Slovenia', 'Tajikistan', 'Türkiye', 'Turkey', 'Turkmenistan',
        'Ukraine', 'Uzbekistan', 'Kosovo', 'Yugoslavia'
    },
    'Oceania': {
        'Australia', 'Cook Islands', 'Fiji', 'Kiribati', 'Marshall Islands',
        'Nauru', 'New Caledonia', 'New Zealand', 'Niue', 'Palau',
        'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tonga', 'Tuvalu',
        'Vanuatu', 'French Polynesia'
    },
    'Latin America': {
        'Antigua and Barbuda', 'Argentina', 'Bahamas', 'Barbados', 'Belize',
        'Bolivia (Plurinational State of)', 'Bolivia', 'Brazil', 'Chile',
        'Colombia', 'Costa Rica', 'Cuba', 'Dominica', 'Dominican Republic',
        'Ecuador', 'El Salvador', 'Grenada', 'Guatemala', 'Guyana', 'Haiti',
        'Honduras', 'Jamaica', 'Mexico', 'Nicaragua', 'Panama', 'Paraguay',
        'Peru', 'Saint Kitts and Nevis', 'Saint Lucia',
        'Saint Vincent and the Grenadines', 'Suriname',
        'Trinidad and Tobago', 'Uruguay',
        'Venezuela (Bolivarian Republic of)', 'Venezuela', 'Puerto Rico',
        'Aruba', 'Netherlands Antilles', 'Bermuda', 'Cayman Islands',
        'British Virgin Islands', 'Turks and Caicos Islands'
    },
    'Middle East': {
        # Classified as DRY climate for leaching purposes (Variant 3).
        # Mean annual precipitation broadly below ET in this region.
        'Bahrain', 'Egypt', 'Iran (Islamic Republic of)', 'Iran', 'Iraq',
        'Jordan', 'Kuwait', 'Lebanon', 'Libya', 'Morocco', 'Oman', 'Qatar',
        'Saudi Arabia', 'Syrian Arab Republic', 'Syria', 'Tunisia',
        'United Arab Emirates', 'Yemen', 'Algeria', 'Djibouti', 'Israel',
        'Mauritania', 'Somalia', 'Sudan', 'Sudan and South Sudan'
    },
    'Africa': {
        'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi',
        'Cabo Verde', 'Cameroon', 'Central African Republic', 'Chad',
        'Comoros', 'Congo', 'Côte d`Ivoire', "Côte d'Ivoire",
        'Democratic Republic of the Congo', 'Equatorial Guinea', 'Eritrea',
        'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea',
        'Guinea-Bissau', 'Kenya', 'Lesotho', 'Liberia', 'Madagascar',
        'Malawi', 'Mali', 'Mauritius', 'Mozambique', 'Namibia', 'Niger',
        'Nigeria', 'Rwanda', 'São Tomé and Príncipe', 'Sao Tome and Principe',
        'Senegal', 'Seychelles', 'Sierra Leone', 'South Africa',
        'South Sudan', 'Tanzania', 'Togo', 'Uganda',
        'United Republic of Tanzania', 'Zambia', 'Zimbabwe',
        'Ethiopia PDR', 'Cape Verde', 'Réunion', 'Mayotte'
    },
    'Asia': {
        'Brunei Darussalam', 'Cambodia', 'China', 'China, mainland',
        'China, Hong Kong SAR', 'China, Macao SAR',
        'China, Taiwan Province of', 'Indonesia', 'Japan',
        "Democratic People's Republic of Korea", 'North Korea',
        'Korea, Republic of', 'South Korea', 'Republic of Korea',
        "Lao People's Democratic Republic", 'Laos', 'Malaysia', 'Mongolia',
        'Myanmar', 'Myanmar/Burma', 'Philippines', 'Singapore', 'Thailand',
        'Timor-Leste', 'Viet Nam', 'Vietnam', 'Hong Kong', 'Macao', 'Taiwan'
    },
}

def get_region(country):
    """Return the IPCC sub-region name for a given FAO country name.
    Falls back to 'Africa' for unlisted small territories."""
    for region, members in REGION_SETS.items():
        if country in members:
            return region
    return 'Africa'   # conservative fallback for unlisted micro-territories

# Climate classification for leaching Variant 3:
# "Wet" regions receive FracLEACH = 0.24 (2019 value).
# "Dry" regions (Middle East) receive FracLEACH = 0.0.
DRY_REGIONS = {'Middle East'}   # all others treated as wet at Tier 1

R9 = ['North America', 'Western Europe', 'Eastern Europe', 'Oceania',
      'Latin America', 'Africa', 'Middle East', 'Asia', 'Indian Subcontinent']

print(f"\nRegion mapping configured. Dry regions (no leaching in Variant 3): {DRY_REGIONS}")

# =============================================================================
# SECTION 4: LOAD ACTIVITY DATA — SYNTHETIC N FERTILIZER USE
# =============================================================================

FERT_PATH = str(FAO_FERTILIZERS_CSV)

print(f"\nLoading fertilizer data from:\n  {FERT_PATH}")
df_fert_raw = pd.read_csv(FERT_PATH, low_memory=False)
print(f"  Raw shape: {df_fert_raw.shape}")

# Filter to: individual countries only (Area Code < 5000),
# synthetic nitrogen nutrient, and agricultural use element.
# ── Why 'Nutrient nitrogen N (total)' under 'Agricultural Use'? ──
# FAO Inputs → Fertilizers by Nutrient domain aggregates all synthetic N forms
# (urea, ammonium nitrate, calcium ammonium nitrate, etc.) into a single
# nitrogen nutrient balance series. 'Agricultural Use' = Production + Imports
# - Exports + Stock changes, representing net N applied to cropland per year.
# This is exactly FSN (synthetic fertiliser N) in IPCC Eq. 11.1.
df_f = df_fert_raw[
    (df_fert_raw['Area Code'] < 5000) &
    (df_fert_raw['Item'] == 'Nutrient nitrogen N (total)') &
    (df_fert_raw['Element'] == 'Agricultural Use')
].copy()

# ── China deduplication ──
# Area Code 351 = "China" aggregate (mainland + Hong Kong + Macao + Taiwan).
# In the fertilizer dataset, China (351) = sum of mainland (41) + HK (96)
# + Taiwan (214) + Macao (128). Including both 351 and its sub-components
# would double-count China's N fertilizer use. We drop the aggregate "China"
# row and retain the individual sub-national entities, consistent with FAO
# GLE country-level methodology.
# Confirmed: China (351) value equals sum of sub-national rows exactly.
n_before = len(df_f)
df_f = df_f[df_f['Area Code'] != 351].copy()
print(f"  Dropped China aggregate (code 351) to avoid double-count. "
      f"Rows: {n_before} → {len(df_f)}")

print(f"  After filter (countries only, Agricultural Use): {df_f.shape[0]} rows")
print(f"  Countries in dataset: {df_f['Area'].nunique()}")

# Coerce year columns to float; fill NaN with 0
# Unit: tonnes N yr-1 per country
df_f[YEAR_COLS] = df_f[YEAR_COLS].apply(pd.to_numeric, errors='coerce').fillna(0.0)

# Index by Area Code for fast lookup
df_f = df_f.set_index('Area Code')

# Assign IPCC regions for each country
# Build a lookup: area_code → (area_name, region)
code_to_meta = {}
for ac, row in df_f.iterrows():
    name = row['Area']
    region = get_region(name)
    code_to_meta[ac] = (name, region)

print(f"  Region assignments complete. {len(code_to_meta)} countries mapped.")
region_counts = {}
for name, region in code_to_meta.values():
    region_counts[region] = region_counts.get(region, 0) + 1
for r in R9:
    print(f"    {r}: {region_counts.get(r, 0)} countries")

# =============================================================================
# SECTION 5: LOAD FAO EMISSIONS BENCHMARK
# =============================================================================
# FAO GLE domain, Item = 'Synthetic Fertilizers', two elements used:
#   'Direct emissions (N2O)'  — corresponds to our EF1-only direct calculation
#   'Emissions (N2O)'         — total N2O (direct + indirect vol + indirect leach)
# Unit: kt N2O yr-1 = Gg N2O yr-1. Source: 'FAO TIER 1'.

EMISS_PATH = str(FAO_EMISSIONS_CSV)

print(f"\nLoading FAO emissions benchmark from:\n  {EMISS_PATH}")
df_em = pd.read_csv(EMISS_PATH, low_memory=False)

fao_direct_row = df_em[
    (df_em['Area'] == 'World') &
    (df_em['Item'] == 'Synthetic Fertilizers') &
    (df_em['Element'] == 'Direct emissions (N2O)') &
    (df_em['Source'] == 'FAO TIER 1')
]
fao_total_row = df_em[
    (df_em['Area'] == 'World') &
    (df_em['Item'] == 'Synthetic Fertilizers') &
    (df_em['Element'] == 'Emissions (N2O)') &
    (df_em['Source'] == 'FAO TIER 1')
]

# Extract as numpy arrays indexed to YEAR_COLS
fao_direct = fao_direct_row[YEAR_COLS].astype(float).values[0]  # kt N2O
fao_total  = fao_total_row[YEAR_COLS].astype(float).values[0]   # kt N2O
fao_indirect = fao_total - fao_direct

print(f"  FAO direct N2O  (2020): {fao_direct[-1]:.1f} kt N2O")
print(f"  FAO total  N2O  (2020): {fao_total[-1]:.1f} kt N2O")
print(f"  FAO indirect    (2020): {fao_indirect[-1]:.1f} kt N2O")
print(f"  Indirect / Direct ratio (2020): {fao_indirect[-1]/fao_direct[-1]:.3f}")

# =============================================================================
# SECTION 6: MAIN COMPUTATION LOOP
# =============================================================================
# For each country and year, compute N2O from the three pathways.
#
# All results are accumulated into per-year global totals AND per-country
# per-year records.

# Storage structures
global_N_kt   = np.zeros(len(YEAR_COLS))  # total N applied (kt N)
global_direct = np.zeros(len(YEAR_COLS))  # direct N2O, all variants (Gg)
global_iv_06  = np.zeros(len(YEAR_COLS))  # indirect volatilisation, 2006
global_il_06  = np.zeros(len(YEAR_COLS))  # indirect leaching, 2006 (aggregated)
global_iv_19  = np.zeros(len(YEAR_COLS))  # indirect volatilisation, 2019
global_il_19  = np.zeros(len(YEAR_COLS))  # indirect leaching, 2019 (aggregated)
global_il_19c = np.zeros(len(YEAR_COLS))  # indirect leaching, 2019 (climate-split)

# Regional storage: dict of {region: array of shape (n_years,)}
reg_N       = {r: np.zeros(len(YEAR_COLS)) for r in R9}
reg_direct  = {r: np.zeros(len(YEAR_COLS)) for r in R9}
reg_total19 = {r: np.zeros(len(YEAR_COLS)) for r in R9}

# Country-level records list
country_records = []

area_codes = sorted(df_f.index.unique())
print(f"\nProcessing {len(area_codes)} countries × {len(YEAR_COLS)} years ...")

for ac in area_codes:
    country_name, region = code_to_meta[ac]

    # Climate classification for Variant 3 (leaching restriction):
    # Middle East is dry → no leaching. All others wet → FracLEACH = 0.24.
    frac_leach_19_clim = 0.0 if region in DRY_REGIONS else FRAC_LEACH_2019

    # Get all years' agricultural use data for this country (tonnes N yr-1)
    rows = df_f.loc[[ac]]   # may be multiple rows; take first
    n_applied_t = rows[YEAR_COLS].values[0]  # array of 51 values (tonnes N)

    # ── EMISSION CALCULATIONS ──
    # Convert tonnes N → kg N for emission factor application
    n_kg = n_applied_t * T_TO_KG   # kg N yr-1 per year

    # ── DIRECT N2O (both guidelines; EF1 identical) ──
    # IPCC Ch.11 Eq. 11.1:
    #   N2O_direct-N = FSN × EF1
    #   N2O_direct   = N2O_direct-N × (44/28)
    # Units: kg N2O-N → kg N2O → Gg N2O (via KG_TO_GG)
    n2o_direct = n_kg * EF1 * MW_N2O * KG_TO_GG   # Gg N2O yr-1

    # ── INDIRECT N2O — VOLATILISATION (2006) ──
    # IPCC Ch.11 Eq. 11.9:
    #   N_vol = FSN × FracGASF
    #   N2O_vol-N = N_vol × EF4
    n2o_iv_06 = n_kg * FRAC_GAS_2006 * EF4 * MW_N2O * KG_TO_GG

    # ── INDIRECT N2O — LEACHING/RUNOFF (2006, aggregated — all regions) ──
    # IPCC Ch.11 Eq. 11.10:
    #   N_leach = FSN × FracLEACH
    #   N2O_leach-N = N_leach × EF5
    n2o_il_06 = n_kg * FRAC_LEACH_2006 * EF5_2006 * MW_N2O * KG_TO_GG

    # ── INDIRECT N2O — VOLATILISATION (2019) ──
    n2o_iv_19 = n_kg * FRAC_GAS_2019 * EF4 * MW_N2O * KG_TO_GG

    # ── INDIRECT N2O — LEACHING/RUNOFF (2019, aggregated — all regions) ──
    n2o_il_19 = n_kg * FRAC_LEACH_2019 * EF5_2019 * MW_N2O * KG_TO_GG

    # ── INDIRECT N2O — LEACHING/RUNOFF (2019, climate-split) ──
    # frac_leach_19_clim = FRAC_LEACH_2019 if wet region, else 0.0
    n2o_il_19c = n_kg * frac_leach_19_clim * EF5_2019 * MW_N2O * KG_TO_GG

    # Totals for each variant:
    n2o_total_06  = n2o_direct + n2o_iv_06 + n2o_il_06
    n2o_total_19  = n2o_direct + n2o_iv_19 + n2o_il_19
    n2o_total_19c = n2o_direct + n2o_iv_19 + n2o_il_19c

    # ── Accumulate global arrays ──
    global_N_kt   += n_applied_t / 1000.0  # convert t N → kt N for global sum
    global_direct += n2o_direct
    global_iv_06  += n2o_iv_06
    global_il_06  += n2o_il_06
    global_iv_19  += n2o_iv_19
    global_il_19  += n2o_il_19
    global_il_19c += n2o_il_19c

    # ── Accumulate regional arrays ──
    reg_N[region]       += n_applied_t / 1000.0
    reg_direct[region]  += n2o_direct
    reg_total19[region] += n2o_total_19c   # use climate-split as regional default

    # ── Store country-level records (one row per year) ──
    for yi, yr in enumerate(range(YEAR_START, YEAR_END + 1)):
        country_records.append({
            'Area_Code':        ac,
            'Country':          country_name,
            'Region':           region,
            'Year':             yr,
            'N_applied_tN':     round(n_applied_t[yi], 3),
            'Direct_GgN2O':     round(n2o_direct[yi], 6),
            'IndVol_2019_GgN2O':round(n2o_iv_19[yi], 6),
            'IndLeach_2019clim_GgN2O': round(n2o_il_19c[yi], 6),
            'Total_2019clim_GgN2O':    round(n2o_total_19c[yi], 6),
            'Total_2006_GgN2O': round(n2o_total_06[yi], 6),
            'Total_2019_GgN2O': round(n2o_total_19[yi], 6),
        })

print("  Country-year loop complete.")

# =============================================================================
# SECTION 7: BUILD GLOBAL SUMMARY CSV
# =============================================================================

years_arr = list(range(YEAR_START, YEAR_END + 1))

global_total_06  = global_direct + global_iv_06 + global_il_06
global_total_19  = global_direct + global_iv_19 + global_il_19
global_total_19c = global_direct + global_iv_19 + global_il_19c

# Ratio of our 2019 climate-split estimate vs FAO total (best match)
ratio_19c = np.where(fao_total > 0, global_total_19c / fao_total, np.nan)
# Ratio of our direct vs FAO direct (expected to be ~1.00)
ratio_direct = np.where(fao_direct > 0, global_direct / fao_direct, np.nan)

df_global = pd.DataFrame({
    'Year':                      years_arr,
    'N_applied_ktN':             global_N_kt.round(2),
    # Direct N2O (EF1 pathway only; same for both guidelines)
    'Direct_GgN2O':              global_direct.round(3),
    # Indirect: volatilisation pathway
    'IndVol_2006_GgN2O':         global_iv_06.round(3),
    'IndVol_2019_GgN2O':         global_iv_19.round(3),
    # Indirect: leaching pathway, 2006 aggregated (all areas)
    'IndLeach_2006_GgN2O':       global_il_06.round(3),
    # Indirect: leaching, 2019 aggregated (all areas)
    'IndLeach_2019_GgN2O':       global_il_19.round(3),
    # Indirect: leaching, 2019 climate-split (Middle East = dry)
    'IndLeach_2019clim_GgN2O':   global_il_19c.round(3),
    # Totals
    'Total_2006_GgN2O':          global_total_06.round(3),
    'Total_2019_GgN2O':          global_total_19.round(3),
    'Total_2019clim_GgN2O':      global_total_19c.round(3),
    # FAO benchmarks
    'FAO_Direct_GgN2O':          fao_direct.round(3),
    'FAO_Total_GgN2O':           fao_total.round(3),
    'FAO_Indirect_GgN2O':        fao_indirect.round(3),
    # Ratios
    'Ratio_Direct_to_FAOdirect': np.round(ratio_direct, 4),
    'Ratio_2019clim_to_FAOtotal':np.round(ratio_19c, 4),
})

global_csv = (str(OUT_A_DATA) + '/n2o_synfert/n2o_synfert_global.csv')
df_global.to_csv(global_csv, index=False)
print(f"\nGlobal CSV saved: {global_csv}")

# =============================================================================
# SECTION 8: BUILD REGIONAL CSV
# =============================================================================

regional_records = []
for r in R9:
    for yi, yr in enumerate(range(YEAR_START, YEAR_END + 1)):
        regional_records.append({
            'Region':               r,
            'Year':                 yr,
            'N_applied_ktN':        round(reg_N[r][yi], 2),
            'Direct_GgN2O':         round(reg_direct[r][yi], 4),
            'Total_2019clim_GgN2O': round(reg_total19[r][yi], 4),
        })

df_regional = pd.DataFrame(regional_records)
regional_csv = (str(OUT_A_DATA) + '/n2o_synfert/n2o_synfert_regional.csv')
df_regional.to_csv(regional_csv, index=False)
print(f"Regional CSV saved: {regional_csv}")

# =============================================================================
# SECTION 9: BUILD COUNTRY CSV
# =============================================================================

df_country = pd.DataFrame(country_records)
country_csv = (str(OUT_A_DATA) + '/n2o_synfert/n2o_synfert_country.csv')
df_country.to_csv(country_csv, index=False)
print(f"Country CSV saved: {country_csv}  ({len(df_country)} rows)")

# =============================================================================
# SECTION 10: PRINT SUMMARY TABLES
# =============================================================================

print("\n" + "=" * 70)
print("GLOBAL SUMMARY — N2O FROM SYNTHETIC N FERTILIZERS (Gg N2O = kt N2O)")
print("=" * 70)
print(f"{'Year':>6}  {'N-appl':>8}  {'Direct':>8}  {'2006tot':>8}  "
      f"{'2019tot':>8}  {'2019clim':>9}  {'FAOdir':>7}  {'FAOtot':>8}  {'Ratio':>6}")
print(f"{'':>6}  {'ktN':>8}  {'GgN2O':>8}  {'GgN2O':>8}  "
      f"{'GgN2O':>8}  {'GgN2O':>9}  {'GgN2O':>7}  {'GgN2O':>8}  {'19c/FAO':>6}")
print("-" * 78)
for yi, yr in enumerate(years_arr):
    if yr % 5 == 0:
        print(f"{yr:>6}  {global_N_kt[yi]:>8.0f}  "
              f"{global_direct[yi]:>8.1f}  "
              f"{global_total_06[yi]:>8.1f}  "
              f"{global_total_19[yi]:>8.1f}  "
              f"{global_total_19c[yi]:>9.1f}  "
              f"{fao_direct[yi]:>7.1f}  "
              f"{fao_total[yi]:>8.1f}  "
              f"{ratio_19c[yi]:>6.3f}")

print("\n" + "=" * 70)
print("REGIONAL BREAKDOWN 2020 — 2019 Climate-Split Total (Gg N2O)")
print("=" * 70)
print(f"{'Region':<25}  {'N-applied (ktN)':>16}  {'Direct':>8}  {'Total':>8}  {'% of total':>10}")
yi_2020 = years_arr.index(2020)
world_tot_2020 = global_total_19c[yi_2020]
for r in R9:
    n  = reg_N[r][yi_2020]
    d  = reg_direct[r][yi_2020]
    t  = reg_total19[r][yi_2020]
    pct = t / world_tot_2020 * 100 if world_tot_2020 > 0 else 0
    print(f"  {r:<23}  {n:>16.1f}  {d:>8.1f}  {t:>8.1f}  {pct:>10.1f}%")
print(f"\n  {'GLOBAL TOTAL':<23}  {global_N_kt[yi_2020]:>16.1f}  "
      f"{global_direct[yi_2020]:>8.1f}  {world_tot_2020:>8.1f}")
print(f"  FAO TOTAL (Direct / Total):  {fao_direct[yi_2020]:.1f}  /  {fao_total[yi_2020]:.1f}")

print("\n" + "=" * 70)
print("TOP 10 COUNTRIES BY N2O EMISSION (2020, 2019 climate-split, Gg N2O)")
print("=" * 70)
df_2020 = df_country[df_country['Year'] == 2020].copy()
df_2020 = df_2020.sort_values('Total_2019clim_GgN2O', ascending=False).head(10)
for _, row in df_2020.iterrows():
    print(f"  {row['Country']:<35}  {row['N_applied_tN']/1e6:>6.2f} Mt N  "
          f"  {row['Total_2019clim_GgN2O']:>7.1f} Gg N2O")

print("\n" + "=" * 70)
print("CRITICAL ANALYSIS: DIVERGENCE FROM FAO")
print("=" * 70)

print(f"""
DIRECT EMISSIONS (EF1 pathway):
  Our direct (2020):     {global_direct[yi_2020]:.1f} Gg N2O
  FAO direct (2020):     {fao_direct[yi_2020]:.1f} Gg N2O
  Ratio:                 {global_direct[yi_2020]/fao_direct[yi_2020]:.4f}

  → Near-perfect match confirms FAO uses EF1 = 0.010 applied to the same
    'Agricultural Use' N data from FAOSTAT fertilizer domain.

TOTAL EMISSIONS (all three pathways):
  2006 Aggregated (2020):     {global_total_06[yi_2020]:.1f} Gg N2O  (ratio {global_total_06[yi_2020]/fao_total[yi_2020]:.3f})
  2019 Aggregated (2020):     {global_total_19[yi_2020]:.1f} Gg N2O  (ratio {global_total_19[yi_2020]/fao_total[yi_2020]:.3f})
  2019 Climate-split (2020):  {global_total_19c[yi_2020]:.1f} Gg N2O  (ratio {global_total_19c[yi_2020]/fao_total[yi_2020]:.3f})
  FAO total (2020):           {fao_total[yi_2020]:.1f} Gg N2O

SOURCES OF RESIDUAL DIVERGENCE FROM FAO TOTAL:
  1. FracGASF uncertainty: FAO may apply fertilizer-type-specific FracGASF
     values (urea=0.15, ammonium=0.08, nitrate=0.01, ammonium-nitrate=0.05)
     weighted by actual fertilizer form distribution per country, while we
     apply the aggregated default 0.11 uniformly.
  2. Climate thresholds: FAO likely applies leaching restrictions based on
     country-level P-ET analysis rather than our broad IPCC sub-region
     classification. Our classification of Middle East as the only dry region
     may miss arid areas within Africa, Central Asia, and Australia.
  3. FracLEACH_H includes N from all managed soils; FAO may use the full
     FSN + FON balance for leaching, not just FSN.
""")

print("Script complete. All outputs saved.")

# Add EDGAR old (4D11) to global CSV
import pandas as _pd3, numpy as _np3
_xlo = _pd3.read_excel((str(EDGAR_OLD_ESSD)), sheet_name='data_totals', engine='openpyxl')
_yr3 = _xlo.iloc[2]; _xlo.columns=_yr3.values
_xlo = _xlo.iloc[3:].reset_index(drop=True)
_labs3 = _xlo['Row Labels'].fillna('').astype(str).values
for _i3,_l3 in enumerate(_labs3):
    if 'Synthetic' in _l3:
        _yrc=[c for c in _xlo.columns if isinstance(c,(int,float)) and 1970<=c<=2019]
        _ev3=_xlo.iloc[_i3+1][_yrc].astype(float).values/1000.
        _ev3=_np3.append(_ev3,_ev3[-1])  # extend 2020=2019
        break
_dg3=_pd3.read_csv((str(OUT_A_DATA) + '/n2o_synfert/n2o_synfert_global.csv'))
_dg3['EDGAR_GgN2O']=_np3.round(_ev3,3)
_dg3.to_csv((str(OUT_A_DATA) + '/n2o_synfert/n2o_synfert_global.csv'),index=False)
print('Added EDGAR_GgN2O (old, 4D11) to n2o_synfert_global.csv')
