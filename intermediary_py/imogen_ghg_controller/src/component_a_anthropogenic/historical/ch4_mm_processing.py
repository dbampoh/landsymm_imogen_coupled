
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
    EDGAR_CH4_NEW, FAO_DIR, FAO_PRODUCTION_CSV, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
)

# =============================================================================
# CH4 EMISSIONS FROM MANURE MANAGEMENT — IPCC 2019 REFINEMENT TIER 1
# =============================================================================
#
# PURPOSE
# -------
# Implements the 2019 Refinement to the 2006 IPCC Guidelines for National GHG
# Inventories, Volume 4, Chapter 10 (Tier 1) for methane (CH4) emissions from
# livestock manure management systems (MMS). Applied at country level using
# FAO Production/Crops and Livestock activity data, 1970–2020.
#
# GOVERNING EQUATION (IPCC 2019 Refinement, Equation 10.23)
# ----------------------------------------------------------
# EF(T) = VS(T) × 365 × B0(T) × 0.67 × Σ_S,k [MCF(S,k)/100 × AWMS(T,S,k)]
#
# Where:
#   EF(T)     = annual CH4 emission factor, kg CH4 / head / year
#   VS(T)     = daily volatile solids excreted, kg VS / (1000 kg animal mass) / day
#               converted to per-head using TAM: VS_head = VS(T) × TAM(T) / 1000
#   365       = days per year
#   B0(T)     = maximum methane producing capacity, m3 CH4 / kg VS  [Table 10.16A]
#   0.67      = density of CH4, converting m3 to kg (kg CH4 / m3 CH4)
#   MCF(S,k)  = methane conversion factor for system S, climate zone k (%) [Table 10.17]
#   AWMS(T,S,k) = fraction of manure N in MMS S for species T in climate k [Tables 10A.6-10A.9]
#
# Total emissions (Gg CH4/yr) = Σ_T [N(T) × EF(T)] / 1e6
#
# KEY METHODOLOGICAL NOTES
# -------------------------
# 1. VS VALUES: From 2019 Table 10.13A. Units are kg VS per 1000 kg animal mass
#    per day. Per-head VS = VS_rate × TAM / 1000.
# 2. B0 VALUES: From 2019 Table 10.16A. For "Other Regions" (Latin America,
#    Africa, Middle East, Asia, Indian Subcontinent), Tier 1 uses the low
#    productivity default (Table 10.16A footnote 1).
# 3. MCF VALUES: From 2019 Table 10.17. Liquid/slurry systems use 6-month
#    retention time MCFs as the Table 10.17 footnote 1 default. Each IPCC
#    sub-region is assigned a dominant climate zone.
# 4. AWMS FRACTIONS: Same as used in the N2O calculation, from 2006 Tables
#    10A-4 to 10A-9. The 2019 Refinement provides updated AWMS (Tables 10A.6-
#    10A.9) but many cells are "no data" — retained 2006 values as documented.
# 5. PRP: Pasture/Range/Paddock manure is included but uses a special MCF of
#    0.47% with B0=0.19 (Table 10.17 footnote 2 + Table 10.16A). This B0 is
#    fixed regardless of species for PRP.
# 6. TAM: From 2019 Table 10A.5 (same as used in N2O calculation).
# 7. SPECIES SPLIT: Cattle are split into dairy and non-dairy using FAO milk
#    animals data. Chickens are split into layers and broilers using FAO laying
#    data. Swine use a blended Tier 1 value (90% finishing + 10% breeding per
#    VS weighted average from Table 10.13A).
#
# WHAT IS NOT INCLUDED
# ----------------------
# • Anaerobic digester CH4: Requires detailed reporting on digester type and
#   leakage rates (Table 10A.11). Excluded as country-level data unavailable.
# • Co-digestate CH4: Reported under separate source category (3.A2(k)).
# • Burning-for-fuel: Reported under Energy/Waste sector, not Agriculture.
#
# INPUTS
# ------
#   Production_Crops_Livestock_E_All_Data.csv — FAO livestock stocks
#   (Also uses dairy/milk-animals and laying-hen sub-category data)
#
# OUTPUTS
# -------
#   ch4_mm_global.csv  — Global annual totals with FAO published comparison
#   ch4_mm_country.csv — Country × year results
#   ch4_mm_regional.csv — Regional annual totals
#   ch4_mm_species.csv  — Global species contributions (2020)
#
# REFERENCES
# ----------
#   IPCC (2019). 2019 Refinement to the 2006 Guidelines, Vol. 4, Ch. 10.
#     Equations 10.22, 10.23; Tables 10.13A, 10.16A, 10.17, 10A.5-10A.9.
#   IPCC (2006). Guidelines for National GHG Inventories, Vol. 4, Ch. 10.
#     Tables 10A-4 to 10A-9 (AWMS fractions, retained where 2019 shows no data)
#   FAO (2023). FAOSTAT Emissions - Agriculture (GLE domain).
# =============================================================================

import pandas as pd
import numpy as np

YEAR_START = 1970
YEAR_END   = 2020
YEAR_COLS  = [f'Y{y}' for y in range(YEAR_START, YEAR_END + 1)]
KG_TO_GG   = 1.0e-6   # kg CH4 → Gg CH4 (= kt CH4)

print("=" * 70)
print("CH4 FROM MANURE MANAGEMENT — IPCC 2019 REFINEMENT TIER 1")
print(f"Period: {YEAR_START}–{YEAR_END}   Countries: all FAO member states")
print("=" * 70)

# =============================================================================
# SECTION 1: LOAD FAO ACTIVITY DATA
# =============================================================================
print("\n[1] Loading FAO activity data...")
df_raw = pd.read_csv(
    str(FAO_PRODUCTION_CSV),
    low_memory=False
)
df_raw[YEAR_COLS] = df_raw[YEAR_COLS].fillna(0)
df_c = df_raw[df_raw['Area Code'] < 5000].copy()

def extract_stocks(item_name, element_name='Stocks'):
    mask = (df_c['Item'] == item_name) & (df_c['Element'] == element_name)
    s = df_c[mask][['Area Code', 'Area'] + YEAR_COLS].copy()
    return s.set_index('Area Code')

cattle_df   = extract_stocks('Cattle')
buffalo_df  = extract_stocks('Buffalo')
sheep_df    = extract_stocks('Sheep')
goats_df    = extract_stocks('Goats')
swine_df    = extract_stocks('Swine / pigs')
chicken_df  = extract_stocks('Chickens')   # 1000 head
ducks_df    = extract_stocks('Ducks')       # 1000 head
turkeys_df  = extract_stocks('Turkeys')    # 1000 head
horses_df   = extract_stocks('Horses')

# Dairy split: number of cows in milk production
dairy_df    = extract_stocks('Raw milk of cattle', 'Milk Animals')
# Layer split: number of hens currently laying
layers_df   = extract_stocks('Hen eggs in shell, fresh', 'Laying')

area_names  = df_c.drop_duplicates('Area Code').set_index('Area Code')['Area'].to_dict()
area_codes  = list(area_names.keys())
print(f"    {len(area_codes)} countries/territories loaded")

# =============================================================================
# SECTION 2: COUNTRY → IPCC REGION → CLIMATE ZONE MAPPING
# =============================================================================
# The 2019 Refinement's Table 10.17 MCFs are indexed by climate zone (10 zones).
# For Tier 1, we assign each IPCC sub-region a single dominant climate zone
# following the average temperatures reported in Table 10.17 footnote 8.
# This is the same simplification used in FAO's GLE methodology.

REGION_SETS = {
    'Indian Subcontinent': {
        'Afghanistan','Bangladesh','Bhutan','India','Maldives','Nepal','Pakistan','Sri Lanka'
    },
    'North America': {
        'United States of America','Canada','Greenland','Saint Pierre and Miquelon'
    },
    'Western Europe': {
        'Albania','Andorra','Austria','Belgium','Belgium-Luxembourg','Cyprus','Denmark',
        'Finland','France and Monaco','France','Germany','Greece','Iceland','Ireland',
        'Israel and Palestine, State of','Italy, San Marino and the Holy See','Italy',
        'Luxembourg','Malta','Netherlands','Norway','Portugal','Spain and Andorra','Spain',
        'Sweden','Switzerland and Liechtenstein','Switzerland','United Kingdom','Monaco',
        'San Marino','Liechtenstein'
    },
    'Eastern Europe': {
        'Armenia','Azerbaijan','Belarus','Bosnia and Herzegovina','Bulgaria','Croatia',
        'Czechia','Czech Republic','Estonia','Georgia','Hungary','Kazakhstan','Kyrgyzstan',
        'Latvia','Lithuania','Moldova','Montenegro','North Macedonia','Poland','Romania',
        'Russia','Serbia','Serbia and Montenegro','Slovakia','Slovenia','Tajikistan',
        'Türkiye','Turkey','Turkmenistan','Ukraine','Uzbekistan','Kosovo','Yugoslavia'
    },
    'Oceania': {
        'Australia','Cook Islands','Fiji','Kiribati','Marshall Islands','Nauru',
        'New Caledonia','New Zealand','Niue','Palau','Papua New Guinea','Samoa',
        'Solomon Islands','Tonga','Tuvalu','Vanuatu','French Polynesia'
    },
    'Latin America': {
        'Antigua and Barbuda','Argentina','Bahamas','Barbados','Belize',
        'Bolivia (Plurinational State of)','Bolivia','Brazil','Chile','Colombia',
        'Costa Rica','Cuba','Dominica','Dominican Republic','Ecuador','El Salvador',
        'Grenada','Guatemala','Guyana','Haiti','Honduras','Jamaica','Mexico','Nicaragua',
        'Panama','Paraguay','Peru','Saint Kitts and Nevis','Saint Lucia',
        'Saint Vincent and the Grenadines','Suriname','Trinidad and Tobago','Uruguay',
        'Venezuela (Bolivarian Republic of)','Venezuela','Puerto Rico','Aruba',
        'Netherlands Antilles','Bermuda','Cayman Islands','British Virgin Islands',
        'Turks and Caicos Islands'
    },
    'Middle East': {
        'Bahrain','Egypt','Iran (Islamic Republic of)','Iran','Iraq','Jordan','Kuwait',
        'Lebanon','Libya','Morocco','Oman','Qatar','Saudi Arabia','Syrian Arab Republic',
        'Syria','Tunisia','United Arab Emirates','Yemen','Algeria','Djibouti','Israel',
        'Mauritania','Somalia','Sudan','Sudan and South Sudan'
    },
    'Africa': {
        'Angola','Benin','Botswana','Burkina Faso','Burundi','Cabo Verde','Cameroon',
        'Central African Republic','Chad','Comoros','Congo','Côte d`Ivoire',
        "Côte d'Ivoire",'Democratic Republic of the Congo','Equatorial Guinea','Eritrea',
        'Eswatini','Ethiopia','Gabon','Gambia','Ghana','Guinea','Guinea-Bissau','Kenya',
        'Lesotho','Liberia','Madagascar','Malawi','Mali','Mauritius','Mozambique',
        'Namibia','Niger','Nigeria','Rwanda','São Tomé and Príncipe',
        'Sao Tome and Principe','Senegal','Seychelles','Sierra Leone','South Africa',
        'South Sudan','Tanzania','Togo','Uganda','United Republic of Tanzania',
        'Zambia','Zimbabwe','Ethiopia PDR','Cape Verde','Réunion','Mayotte'
    },
    'Asia': {
        'Brunei Darussalam','Cambodia','China','China, mainland','China, Hong Kong SAR',
        'China, Macao SAR','China, Taiwan Province of','Indonesia','Japan',
        "Democratic People's Republic of Korea",'North Korea','Korea, Republic of',
        'South Korea','Republic of Korea',"Lao People's Democratic Republic",'Laos',
        'Malaysia','Mongolia','Myanmar','Myanmar/Burma','Philippines','Singapore',
        'Thailand','Timor-Leste','Viet Nam','Vietnam','Hong Kong','Macao','Taiwan'
    },
}

def get_region(country):
    for region, s in REGION_SETS.items():
        if country in s:
            return region
    return 'Africa'

R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']

# Map IPCC sub-region → dominant 2019 climate zone (Table 10.17 column headers)
# These assignments reflect the dominant manure management temperature conditions
# for each region. Developed regions store manure primarily in cool/temperate climates.
REGION_TO_CLIMATE = {
    'North America':       'Cool Temperate Moist',
    'Western Europe':      'Cool Temperate Moist',
    'Eastern Europe':      'Cool Temperate Moist',
    'Oceania':             'Warm Temperate Moist',
    'Latin America':       'Tropical Moist',
    'Africa':              'Tropical Moist',
    'Middle East':         'Warm Temperate Dry',
    'Asia':                'Warm Temperate Moist',
    'Indian Subcontinent': 'Tropical Moist',
}

area_region  = {ac: get_region(area_names[ac]) for ac in area_codes}
area_climate = {ac: REGION_TO_CLIMATE[area_region[ac]] for ac in area_codes}
print(f"[2] Region and climate zone assignment complete")

# =============================================================================
# SECTION 3: PARAMETERS FROM IPCC 2019 REFINEMENT
# =============================================================================

# ---------------------------------------------------------------------------
# 3A. VS RATES (Table 10.13A) — kg VS per 1000 kg animal mass per day
# ---------------------------------------------------------------------------
# These are population-weighted Tier 1 values derived from GLEAM and
# the Tier 2 calculations in Annex 10A.1–10A.4.
# For "Other Regions" developing countries, Tier 1 default = mean value
# (no productivity split for Tier 1).
#
# Column mapping (9 IPCC sub-regions in R9 order):
# NA, WE, EE, OC, LA, AF, ME, AS, IS

# Dairy Cattle: Table 10.13A
_vs_dairy = [9.2, 8.4, 6.7, 6.0,  7.9, 18.2, 10.7, 9.0, 14.1]
VS_DAIRY = dict(zip(R9, _vs_dairy))

# Other (non-dairy) Cattle: Table 10.13A
_vs_other = [7.6, 5.7, 7.6, 8.7,  8.5, 12.1, 12.3, 9.8, 12.2]
VS_OTHER_CATTLE = dict(zip(R9, _vs_other))

# Buffalo: Table 10.13A (NA/OC = NA in table → use global average 11 as fallback)
_vs_buffalo = [11.0, 7.7, 6.2, 11.0,  11.2, 12.9, 13.5, 13.5, 15.2]
VS_BUFFALO = dict(zip(R9, _vs_buffalo))

# Swine: Table 10.13A — blended Tier 1 "Swine" row
_vs_swine = [3.3, 4.5, 4.0, 4.0,  5.0, 7.2, 5.8, 4.3, 7.7]
VS_SWINE = dict(zip(R9, _vs_swine))

# Chicken-Layers (Hens ≥1yr): Table 10.13A
_vs_layers = [9.4, 8.6, 9.4, 8.6,  10.1, 10.2, 9.0, 9.3, 13.2]
VS_LAYERS = dict(zip(R9, _vs_layers))

# Chicken-Broilers: Table 10.13A
_vs_broilers = [16.8, 16.1, 16.0, 18.3,  15.6, 15.9, 17.7, 15.7, 17.7]
VS_BROILERS = dict(zip(R9, _vs_broilers))

# Blended chicken VS for when no layer/broiler split is needed
# (not used in this calculation but documented for completeness)
_vs_chicken_blend = [14.5, 12.3, 12.6, 15.4,  13.5, 12.6, 14.2, 11.2, 14.9]
VS_CHICKEN_BLEND = dict(zip(R9, _vs_chicken_blend))

# Turkeys: Table 10.13A — single value 10.3 (all regions)
VS_TURKEYS = {r: 10.3 for r in R9}

# Ducks: Table 10.13A — single value 7.4 (all regions)
VS_DUCKS = {r: 7.4 for r in R9}

# Sheep: Table 10.13A — Developed: 8.2, Developing: 8.3 (effectively uniform)
VS_SHEEP = {r: (8.2 if r in {'North America','Western Europe','Eastern Europe','Oceania'} else 8.3) for r in R9}

# Goats: Table 10.13A — Developed: 9.0, Developing: 10.4
VS_GOATS = {r: (9.0 if r in {'North America','Western Europe','Eastern Europe','Oceania'} else 10.4) for r in R9}

# Horses: Table 10.13A — Developed: 5.65, Developing: 7.2
VS_HORSES = {r: (5.65 if r in {'North America','Western Europe','Eastern Europe','Oceania'} else 7.2) for r in R9}

# Mules and Asses: Table 10.13A — single value 7.2 (all regions)
VS_MULES = {r: 7.2 for r in R9}

# Camels: Table 10.13A — single value 11.5 (all regions)
VS_CAMELS = {r: 11.5 for r in R9}

# ---------------------------------------------------------------------------
# 3B. TAM (Table 10A.5) — Typical Animal Mass, kg/head
# ---------------------------------------------------------------------------
# Identical to values used in the N2O calculation.
# Used to convert VS per 1000 kg body mass → VS per head

DEVELOPED = {'North America','Western Europe','Eastern Europe','Oceania'}

_tam_dairy   = [650, 600, 550, 488,  508, 260, 349, 386, 285]
TAM_DAIRY    = dict(zip(R9, _tam_dairy))
_tam_other   = [407, 405, 389, 359,  303, 236, 275, 299, 226]
TAM_OTHER    = dict(zip(R9, _tam_other))
_tam_buf     = [380, 509, 467, 380,  315, 339, 381, 336, 321]
TAM_BUFFALO  = dict(zip(R9, _tam_buf))
_tam_sw      = [77,  76,  77,  61,   65,  49,  59,  58,  59]
TAM_SWINE    = dict(zip(R9, _tam_sw))
_tam_lay     = [1.5, 1.9, 1.9, 2.0,  1.4, 1.4, 1.2, 1.5, 1.3]
TAM_LAYERS   = dict(zip(R9, _tam_lay))
_tam_brl     = [1.4, 1.2, 1.1, 1.2,  0.9, 0.8, 0.7, 0.8, 0.8]
TAM_BROILERS = dict(zip(R9, _tam_brl))
TAM_TURKEYS  = {r: 6.8  for r in R9}
TAM_DUCKS    = {r: 2.7  for r in R9}
TAM_SHEEP    = {r: (40.0 if r in DEVELOPED else 31.0) for r in R9}
_tam_goats   = [41, 40, 36, 33, 24, 24, 24, 24, 24]
TAM_GOATS    = dict(zip(R9, _tam_goats))
TAM_HORSES   = {r: (377.0 if r in DEVELOPED else 238.0) for r in R9}
TAM_MULES    = {r: 130.0 for r in R9}

# ---------------------------------------------------------------------------
# 3C. B0 VALUES (Table 10.16A) — m3 CH4 / kg VS
# ---------------------------------------------------------------------------
# For developed regions (NA, WE, EE, OC): region-specific values
# For other regions: Tier 1 default = low productivity (Table 10.16A footnote 1)
# Buffalo B0 = 0.10 globally (no regional variation in Table 10.16A)
# PRP uses special B0 = 0.19 regardless of species (Table 10.17 footnote 2)

def B0(species, region):
    """Return B0 (m3 CH4 / kg VS) for a species-region combination."""
    if species == 'Dairy':
        if region == 'North America':  return 0.24
        if region in ('Western Europe','Eastern Europe','Oceania'): return 0.24
        return 0.13   # low productivity default for all other regions
    if species == 'Other Cattle':
        if region == 'North America':  return 0.19
        if region == 'Western Europe': return 0.18
        if region == 'Eastern Europe': return 0.17
        if region == 'Oceania':        return 0.17
        return 0.13   # low productivity default
    if species == 'Buffalo':
        return 0.10   # uniform globally
    if species == 'Swine':
        if region == 'North America':  return 0.48
        if region in ('Western Europe','Eastern Europe','Oceania'): return 0.45
        return 0.29   # low productivity default
    if species == 'Layers':
        if region in DEVELOPED: return 0.39
        return 0.24   # low productivity default
    if species in ('Broilers','Turkeys','Ducks'):
        if region in DEVELOPED: return 0.36
        return 0.24   # low productivity default (all other poultry)
    if species == 'Sheep':
        if region in DEVELOPED: return 0.19
        return 0.13   # low productivity default
    if species == 'Goats':
        if region in DEVELOPED: return 0.18
        return 0.13   # low productivity default
    if species == 'Horses':
        if region in DEVELOPED: return 0.30
        return 0.26
    if species == 'Mules':
        if region in DEVELOPED: return 0.33
        return 0.26
    if species == 'Camels':
        if region in DEVELOPED: return 0.26
        return 0.21
    return 0.13  # fallback

# ---------------------------------------------------------------------------
# 3D. MCF VALUES (Table 10.17) — fraction (not percentage)
# ---------------------------------------------------------------------------
# Key: each MMS × climate zone combination has a specific MCF.
# For Tier 1, we use simplified MCFs corresponding to each climate zone.
#
# Liquid/Slurry systems: 6-month retention time MCFs (Table 10.17 default per footnote 1)
#   Cool Temperate Moist: 21%, Cool Temperate Dry: 26%
#   Warm Temperate Moist: 37%, Warm Temperate Dry: 41%
#   Tropical Montane: 59%, Tropical Wet: 76%, Tropical Moist: 73%, Tropical Dry: 74%
#
# Anaerobic Lagoon (Table 10.17):
#   Cool Temperate Moist: 60%, Warm Temperate Moist: 73%, Tropical Moist: 80%
#
# Solid storage: 2% cool, 4% temperate, 5% warm (Table 10.17, unchanged)
# Drylot: 1% cool, 1.5% temperate, 2% warm
# Daily spread: 0.1% cool, 0.5% temperate, 1.0% warm
# Poultry manure with/without litter: 1.5% all climates (Table 10.17)
# PRP: 0.47% all climates, paired with B0=0.19 (Table 10.17 footnote 2)
# Burned for fuel: 10% all climates (Table 10.17)

# Climate-indexed MCF tables: {climate_zone: MCF_fraction}
MCF_LAGOON = {
    'Cool Temperate Moist': 0.60, 'Cool Temperate Dry': 0.67,
    'Boreal Moist': 0.50,         'Boreal Dry': 0.49,
    'Warm Temperate Moist': 0.73, 'Warm Temperate Dry': 0.76,
    'Tropical Montane': 0.76,     'Tropical Wet': 0.80,
    'Tropical Moist': 0.80,       'Tropical Dry': 0.80,
}

MCF_LIQUID_6MO = {
    'Cool Temperate Moist': 0.21, 'Cool Temperate Dry': 0.26,
    'Boreal Moist': 0.14,         'Boreal Dry': 0.14,
    'Warm Temperate Moist': 0.37, 'Warm Temperate Dry': 0.41,
    'Tropical Montane': 0.59,     'Tropical Wet': 0.76,
    'Tropical Moist': 0.73,       'Tropical Dry': 0.74,
}

MCF_SOLID = {     # 2% cool, 4% temperate, 5% warm (Table 10.17)
    'Cool Temperate Moist': 0.020, 'Cool Temperate Dry': 0.020,
    'Boreal Moist': 0.020,         'Boreal Dry': 0.020,
    'Warm Temperate Moist': 0.040, 'Warm Temperate Dry': 0.040,
    'Tropical Montane': 0.050,     'Tropical Wet': 0.050,
    'Tropical Moist': 0.050,       'Tropical Dry': 0.050,
}

MCF_DRYLOT = {    # 1% cool, 1.5% temperate, 2% warm (Table 10.17)
    'Cool Temperate Moist': 0.010, 'Cool Temperate Dry': 0.010,
    'Boreal Moist': 0.010,         'Boreal Dry': 0.010,
    'Warm Temperate Moist': 0.015, 'Warm Temperate Dry': 0.015,
    'Tropical Montane': 0.020,     'Tropical Wet': 0.020,
    'Tropical Moist': 0.020,       'Tropical Dry': 0.020,
}

MCF_DAILY  = {    # 0.1% cool, 0.5% temperate, 1.0% warm (Table 10.17)
    'Cool Temperate Moist': 0.001, 'Cool Temperate Dry': 0.001,
    'Boreal Moist': 0.001,         'Boreal Dry': 0.001,
    'Warm Temperate Moist': 0.005, 'Warm Temperate Dry': 0.005,
    'Tropical Montane': 0.010,     'Tropical Wet': 0.010,
    'Tropical Moist': 0.010,       'Tropical Dry': 0.010,
}

MCF_POULTRY = {cz: 0.015 for cz in MCF_SOLID}   # 1.5% all climates (Table 10.17)
MCF_PRP     = {cz: 0.0047 for cz in MCF_SOLID}  # 0.47% all climates (Table 10.17)
MCF_BURNED  = {cz: 0.10  for cz in MCF_SOLID}   # 10% all climates (Table 10.17)
MCF_DIGESTER= {cz: 0.0  for cz in MCF_SOLID}    # Excluded (see note above)
MCF_PIT_LT1 = {   # Pit < 1 month: 2.75% cool, 6.5% temperate, 18% warm (Table 10.17)
    'Cool Temperate Moist': 0.0275, 'Cool Temperate Dry': 0.0275,
    'Boreal Moist': 0.0275,         'Boreal Dry': 0.0275,
    'Warm Temperate Moist': 0.065,  'Warm Temperate Dry': 0.065,
    'Tropical Montane': 0.18,       'Tropical Wet': 0.18,
    'Tropical Moist': 0.18,         'Tropical Dry': 0.18,
}

# ---------------------------------------------------------------------------
# 3E. AWMS FRACTIONS
# ---------------------------------------------------------------------------
# From 2006 IPCC Tables 10A-4 to 10A-9, retained where 2019 shows "no data".
# Column order for cattle/buffalo: [Lagoon, Slurry, Solid, Drylot, PRP, Daily, Digester, Burned, Other]
# Column order for swine: [Lagoon, Slurry, Solid, Drylot, Pit<1mo, Pit>1mo, Daily, Digester, Other]

AWMS_DAIRY = {
    'North America':       [0.150, 0.270, 0.263, 0.000, 0.108, 0.184, 0.000, 0.000, 0.026],
    'Western Europe':      [0.000, 0.357, 0.368, 0.000, 0.200, 0.070, 0.000, 0.000, 0.005],
    'Eastern Europe':      [0.000, 0.175, 0.600, 0.000, 0.180, 0.025, 0.000, 0.000, 0.020],
    'Oceania':             [0.160, 0.010, 0.000, 0.000, 0.760, 0.080, 0.000, 0.000, 0.000],
    'Latin America':       [0.000, 0.010, 0.010, 0.000, 0.360, 0.620, 0.000, 0.000, 0.000],
    'Africa':              [0.000, 0.000, 0.010, 0.000, 0.830, 0.050, 0.000, 0.060, 0.040],
    'Middle East':         [0.000, 0.010, 0.020, 0.000, 0.800, 0.020, 0.000, 0.170, 0.000],
    'Asia':                [0.040, 0.380, 0.000, 0.000, 0.200, 0.290, 0.020, 0.070, 0.000],
    'Indian Subcontinent': [0.000, 0.010, 0.000, 0.000, 0.270, 0.190, 0.010, 0.510, 0.000],
}

AWMS_OTHER_CATTLE = {
    'North America':       [0.000, 0.002, 0.000, 0.184, 0.815, 0.000, 0.000, 0.000, 0.000],
    'Western Europe':      [0.000, 0.252, 0.390, 0.000, 0.320, 0.018, 0.000, 0.000, 0.020],
    'Eastern Europe':      [0.000, 0.225, 0.440, 0.000, 0.200, 0.000, 0.000, 0.000, 0.135],
    'Oceania':             [0.000, 0.000, 0.000, 0.090, 0.910, 0.000, 0.000, 0.000, 0.000],
    'Latin America':       [0.000, 0.000, 0.000, 0.000, 0.990, 0.000, 0.000, 0.000, 0.010],
    'Africa':              [0.000, 0.000, 0.000, 0.010, 0.950, 0.010, 0.000, 0.030, 0.000],
    'Middle East':         [0.000, 0.000, 0.000, 0.010, 0.790, 0.020, 0.000, 0.170, 0.020],
    'Asia':                [0.000, 0.000, 0.000, 0.460, 0.500, 0.020, 0.000, 0.020, 0.000],
    'Indian Subcontinent': [0.000, 0.010, 0.000, 0.040, 0.220, 0.200, 0.010, 0.530, 0.000],
}

AWMS_BUFFALO = {
    'North America':       [0.000, 0.000, 0.000, 0.000, 1.000, 0.000, 0.000, 0.000, 0.000],
    'Western Europe':      [0.000, 0.200, 0.000, 0.790, 0.000, 0.000, 0.000, 0.000, 0.000],
    'Eastern Europe':      [0.000, 0.240, 0.000, 0.000, 0.290, 0.000, 0.000, 0.000, 0.470],
    'Oceania':             [0.000, 0.000, 0.000, 0.000, 1.000, 0.000, 0.000, 0.000, 0.000],
    'Latin America':       [0.000, 0.000, 0.000, 0.000, 0.990, 0.000, 0.000, 0.000, 0.010],
    'Africa':              [0.000, 0.000, 0.000, 0.000, 1.000, 0.000, 0.000, 0.000, 0.000],
    'Middle East':         [0.000, 0.000, 0.000, 0.000, 0.200, 0.190, 0.000, 0.420, 0.190],
    'Asia':                [0.000, 0.000, 0.000, 0.410, 0.500, 0.040, 0.000, 0.050, 0.000],
    'Indian Subcontinent': [0.000, 0.000, 0.000, 0.040, 0.190, 0.210, 0.010, 0.550, 0.000],
}

# Swine AWMS: [Lagoon, Slurry, Solid, Drylot, Pit<1mo, Pit>1mo, Daily, Digester, Other]
AWMS_SWINE = {
    'North America':       [0.328, 0.185, 0.042, 0.040, 0.000, 0.406, 0.000, 0.000, 0.000],
    'Western Europe':      [0.087, 0.000, 0.137, 0.000, 0.028, 0.698, 0.020, 0.000, 0.030],
    'Eastern Europe':      [0.030, 0.000, 0.420, 0.000, 0.247, 0.247, 0.000, 0.000, 0.057],
    'Oceania':             [0.540, 0.000, 0.030, 0.150, 0.000, 0.000, 0.000, 0.000, 0.280],
    'Latin America':       [0.000, 0.080, 0.100, 0.410, 0.000, 0.000, 0.020, 0.000, 0.400],
    'Africa':              [0.000, 0.060, 0.060, 0.870, 0.010, 0.000, 0.000, 0.000, 0.000],
    'Middle East':         [0.000, 0.140, 0.000, 0.690, 0.000, 0.170, 0.000, 0.000, 0.000],
    'Asia':                [0.000, 0.400, 0.000, 0.540, 0.000, 0.000, 0.000, 0.060, 0.000],
    'Indian Subcontinent': [0.090, 0.220, 0.160, 0.300, 0.030, 0.000, 0.090, 0.080, 0.030],
}

# Sheep and Goats AWMS (2019 Table 10A.8 — now included in manure management)
# Format: [Lagoon, Slurry, Solid, Drylot, PRP, Daily, Digester, Burned, Other]
AWMS_SHEEP_GOATS = {
    'North America':       [0.000, 0.000, 0.200, 0.180, 0.620, 0.000, 0.000, 0.000, 0.000],
    'Western Europe':      [0.000, 0.000, 0.130, 0.000, 0.870, 0.000, 0.000, 0.000, 0.000],
    'Eastern Europe':      [0.000, 0.000, 0.150, 0.150, 0.700, 0.000, 0.000, 0.000, 0.000],
    'Oceania':             [0.000, 0.000, 0.200, 0.000, 0.800, 0.000, 0.000, 0.000, 0.000],
    'Latin America':       [0.000, 0.000, 0.100, 0.000, 0.900, 0.000, 0.000, 0.000, 0.000],
    'Africa':              [0.000, 0.000, 0.050, 0.000, 0.950, 0.000, 0.000, 0.000, 0.000],
    'Middle East':         [0.000, 0.000, 0.100, 0.200, 0.700, 0.000, 0.000, 0.000, 0.000],
    'Asia':                [0.000, 0.000, 0.050, 0.000, 0.950, 0.000, 0.000, 0.000, 0.000],
    'Indian Subcontinent': [0.000, 0.000, 0.050, 0.000, 0.950, 0.000, 0.000, 0.000, 0.000],
}

print("[3] All IPCC 2019 parameters loaded")
print(f"    VS: Table 10.13A | B0: Table 10.16A | MCF: Table 10.17 | AWMS: Tables 10A-4 to 10A.9")

# =============================================================================
# SECTION 4: EMISSION FACTOR COMPUTATION
# =============================================================================
# For each species × region × climate zone, pre-compute the annual CH4
# emission factor in kg CH4 per head per year using Equation 10.23:
#
#   EF = VS_head × 365 × B0 × 0.67 × Σ_S [MCF_S / 100 × AWMS_S]
#
# Where VS_head = VS_rate × TAM / 1000
#
# The MCF for each MMS system depends on climate zone.
# AWMS fractions and their associated MCFs:
#
# For cattle/buffalo AWMS column order: [Lagoon, Slurry, Solid, Drylot, PRP, Daily, Digester, Burned, Other]
# MCF lookup per index:
CATTLE_MCF_MAP = [
    MCF_LAGOON,    # 0 = Lagoon (anaerobic)
    MCF_LIQUID_6MO,# 1 = Slurry/liquid (6-month default)
    MCF_SOLID,     # 2 = Solid storage
    MCF_DRYLOT,    # 3 = Drylot
    MCF_PRP,       # 4 = PRP (special MCF; B0 also different)
    MCF_DAILY,     # 5 = Daily spread
    MCF_DIGESTER,  # 6 = Anaerobic digester (excluded — MCF=0)
    MCF_BURNED,    # 7 = Burned for fuel
    MCF_SOLID,     # 8 = Other (treated as solid storage)
]

# For swine AWMS column order: [Lagoon, Slurry, Solid, Drylot, Pit<1mo, Pit>1mo, Daily, Digester, Other]
SWINE_MCF_MAP = [
    MCF_LAGOON,    # 0 = Lagoon
    MCF_LIQUID_6MO,# 1 = Slurry
    MCF_SOLID,     # 2 = Solid storage
    MCF_DRYLOT,    # 3 = Drylot
    MCF_PIT_LT1,   # 4 = Pit < 1 month
    MCF_LIQUID_6MO,# 5 = Pit > 1 month (same as liquid 6mo per Table 10.17 footnote 10)
    MCF_DAILY,     # 6 = Daily spread
    MCF_DIGESTER,  # 7 = Digester (excluded)
    MCF_SOLID,     # 8 = Other
]

# Sheep/goats AWMS same column order as cattle
SHEEP_MCF_MAP = CATTLE_MCF_MAP.copy()

def compute_EF(vs_rate, tam, b0, awms_fracs, mcf_map, climate_zone, prp_index=4):
    """
    Compute the annual CH4 emission factor (kg CH4 / head / year).

    Parameters
    ----------
    vs_rate     : float — VS excretion, kg VS / 1000 kg / day  [Table 10.13A]
    tam         : float — Typical Animal Mass, kg/head          [Table 10A.5]
    b0          : float — max CH4 capacity, m3 CH4/kg VS       [Table 10.16A]
    awms_fracs  : list  — fraction of manure N in each MMS     [Tables 10A.x]
    mcf_map     : list  — MCF dicts keyed by climate zone       [Table 10.17]
    climate_zone: str   — climate zone label for MCF lookup
    prp_index   : int   — column index of PRP in awms_fracs

    Returns
    -------
    ef : float — kg CH4 / head / year
    """
    # VS per head per day
    vs_head = vs_rate * tam / 1000.0   # kg VS / head / day

    # Σ_S [ MCF_S × AWMS_S ] — weighted MCF
    # For PRP, the MCF must use B0 = 0.19 regardless of species B0
    # We handle PRP separately and add it back in.
    sigma = 0.0
    for i, frac in enumerate(awms_fracs):
        if frac <= 0.0:
            continue
        mcf = mcf_map[i][climate_zone]
        if i == prp_index:
            # PRP: B0 is fixed at 0.19 per Table 10.17 footnote 2
            # Compute PRP contribution separately and add to total
            sigma_prp = frac * mcf
            ef_prp = vs_head * 365 * 0.19 * 0.67 * sigma_prp
            # We'll accumulate non-PRP separately and add ef_prp at end
            continue
        sigma += frac * mcf

    # Non-PRP contribution
    ef_non_prp = vs_head * 365 * b0 * 0.67 * sigma

    # PRP contribution (if any PRP fraction exists)
    prp_frac = awms_fracs[prp_index] if prp_index < len(awms_fracs) else 0.0
    ef_prp = 0.0
    if prp_frac > 0:
        mcf_prp = mcf_map[prp_index][climate_zone]
        vs_head_prp = vs_rate * tam / 1000.0
        ef_prp = vs_head_prp * 365 * 0.19 * 0.67 * prp_frac * mcf_prp

    return ef_non_prp + ef_prp

# =============================================================================
# SECTION 5: MAIN COMPUTATION LOOP
# =============================================================================
print("\n[4] Running computation...")
print(f"    {len(area_codes)} countries × {len(YEAR_COLS)} years")

def gv(df_s, ac, yr):
    try:
        if ac in df_s.index:
            rows = df_s.loc[[ac]]
            if len(rows) > 0 and yr in rows.columns:
                v = rows[yr].iloc[0]
                return float(v) if pd.notna(v) else 0.0
    except: pass
    return 0.0

records = []

for ac in area_codes:
    country = area_names[ac]
    region  = area_region[ac]
    climate = area_climate[ac]

    for yr in YEAR_COLS:
        year = int(yr[1:])
        result = {'Year': year, 'Area Code': ac, 'Area': country, 'Region': region}
        species_ch4 = {}

        # ----- CATTLE (split dairy / non-dairy) -----
        cattle_tot = gv(cattle_df,  ac, yr)
        dairy_n    = min(gv(dairy_df, ac, yr), cattle_tot)
        nondairy_n = cattle_tot - dairy_n

        if dairy_n > 0:
            ef = compute_EF(VS_DAIRY[region], TAM_DAIRY[region],
                            B0('Dairy', region),
                            AWMS_DAIRY[region], CATTLE_MCF_MAP, climate)
            species_ch4['Dairy Cattle'] = dairy_n * ef

        if nondairy_n > 0:
            ef = compute_EF(VS_OTHER_CATTLE[region], TAM_OTHER[region],
                            B0('Other Cattle', region),
                            AWMS_OTHER_CATTLE[region], CATTLE_MCF_MAP, climate)
            species_ch4['Other Cattle'] = nondairy_n * ef

        # ----- BUFFALO -----
        buf_n = gv(buffalo_df, ac, yr)
        if buf_n > 0:
            ef = compute_EF(VS_BUFFALO[region], TAM_BUFFALO[region],
                            B0('Buffalo', region),
                            AWMS_BUFFALO[region], CATTLE_MCF_MAP, climate)
            species_ch4['Buffalo'] = buf_n * ef

        # ----- SWINE -----
        sw_n = gv(swine_df, ac, yr)
        if sw_n > 0:
            ef = compute_EF(VS_SWINE[region], TAM_SWINE[region],
                            B0('Swine', region),
                            AWMS_SWINE[region], SWINE_MCF_MAP, climate,
                            prp_index=99)  # swine AWMS has no PRP column
            species_ch4['Swine'] = sw_n * ef

        # ----- CHICKENS (split layers / broilers) -----
        ch_tot  = gv(chicken_df,  ac, yr) * 1000
        lay_n   = min(gv(layers_df, ac, yr) * 1000, ch_tot)
        brl_n   = ch_tot - lay_n

        if lay_n > 0:
            # Layers: use poultry MCF (1.5%, all climates), B0 species-specific
            vs_head_lay = VS_LAYERS[region] * TAM_LAYERS[region] / 1000
            ef_lay = vs_head_lay * 365 * B0('Layers', region) * 0.67 * MCF_POULTRY[climate]
            species_ch4['Layers'] = lay_n * ef_lay

        if brl_n > 0:
            vs_head_brl = VS_BROILERS[region] * TAM_BROILERS[region] / 1000
            ef_brl = vs_head_brl * 365 * B0('Broilers', region) * 0.67 * MCF_POULTRY[climate]
            species_ch4['Broilers'] = brl_n * ef_brl

        # Turkeys (1000 head in FAO)
        tk_n = gv(turkeys_df, ac, yr) * 1000
        if tk_n > 0:
            vs_head_tk = VS_TURKEYS[region] * TAM_TURKEYS[region] / 1000
            ef_tk = vs_head_tk * 365 * B0('Turkeys', region) * 0.67 * MCF_POULTRY[climate]
            species_ch4['Turkeys'] = tk_n * ef_tk

        # Ducks (1000 head in FAO)
        dk_n = gv(ducks_df, ac, yr) * 1000
        if dk_n > 0:
            vs_head_dk = VS_DUCKS[region] * TAM_DUCKS[region] / 1000
            ef_dk = vs_head_dk * 365 * B0('Ducks', region) * 0.67 * MCF_POULTRY[climate]
            species_ch4['Ducks'] = dk_n * ef_dk

        # ----- SHEEP (now included: 2019 Table 10A.8 provides AWMS) -----
        sh_n = gv(sheep_df, ac, yr)
        if sh_n > 0:
            ef = compute_EF(VS_SHEEP[region], TAM_SHEEP[region],
                            B0('Sheep', region),
                            AWMS_SHEEP_GOATS[region], SHEEP_MCF_MAP, climate)
            species_ch4['Sheep'] = sh_n * ef

        # ----- GOATS (2019 Table 10A.8) -----
        gt_n = gv(goats_df, ac, yr)
        if gt_n > 0:
            ef = compute_EF(VS_GOATS[region], TAM_GOATS[region],
                            B0('Goats', region),
                            AWMS_SHEEP_GOATS[region], SHEEP_MCF_MAP, climate)
            species_ch4['Goats'] = gt_n * ef

        # ----- HORSES (Table 10.15 in 2019: all in dry systems) -----
        # Horses are managed almost entirely in solid/drylot/PRP per 2006 Table 10A-9.
        # We apply a simple EF using solid storage MCF.
        hs_n = gv(horses_df, ac, yr)
        if hs_n > 0:
            vs_head_hs = VS_HORSES[region] * TAM_HORSES[region] / 1000
            b0_hs = B0('Horses', region)
            # Assume horses: 50% PRP, 50% solid storage (dry systems per Table 10A-9)
            awms_hs = [0.0, 0.0, 0.50, 0.0, 0.50, 0.0, 0.0, 0.0, 0.0]
            ef = compute_EF(VS_HORSES[region], TAM_HORSES[region], b0_hs,
                            awms_hs, SHEEP_MCF_MAP, climate)
            species_ch4['Horses'] = hs_n * ef

        # Accumulate total
        total_kg_ch4 = sum(species_ch4.values())

        result['Total_kgCH4'] = total_kg_ch4
        for sp in ['Dairy Cattle','Other Cattle','Buffalo','Swine','Layers',
                   'Broilers','Turkeys','Ducks','Sheep','Goats','Horses']:
            result[f'{sp.replace(" ","_")}_kgCH4'] = species_ch4.get(sp, 0.0)
        records.append(result)

print(f"    {len(records):,} records computed")

# =============================================================================
# SECTION 6: AGGREGATE AND OUTPUT
# =============================================================================
print("\n[5] Aggregating results...")
df_out = pd.DataFrame(records)

kg_cols = [c for c in df_out.columns if c.endswith('_kgCH4')]
for col in kg_cols:
    df_out[col.replace('_kgCH4','_GgCH4')] = df_out[col] * KG_TO_GG

gg_cols = [c for c in df_out.columns if c.endswith('_GgCH4')]

# Global annual
df_global = df_out.groupby('Year')[gg_cols].sum().reset_index()

# FAO published manure management CH4 (from Emissions_Totals_E_All_Data.csv)
FAO_MM_CH4 = {
    1970:7813.3,1971:8139.7,1972:8258.9,1973:8334.0,1974:8432.4,
    1975:8396.6,1976:8342.4,1977:8499.3,1978:8617.1,1979:8775.2,
    1980:8980.8,1981:8968.2,1982:8971.6,1983:8979.8,1984:9090.6,
    1985:9119.7,1986:9212.7,1987:9181.3,1988:9205.7,1989:9273.8,
    1990:9266.6,1991:9231.3,1992:9061.4,1993:8997.5,1994:9031.3,
    1995:9003.2,1996:8997.8,1997:8831.6,1998:8855.1,1999:8871.7,
    2000:8875.8,2001:8846.7,2002:8936.3,2003:9009.8,2004:9045.6,
    2005:9115.4,2006:9224.1,2007:9301.6,2008:9394.5,2009:9427.6,
    2010:9448.2,2011:9464.3,2012:9559.1,2013:9566.5,2014:9676.3,
    2015:9768.6,2016:9838.9,2017:9914.5,2018:9791.8,2019:9577.8,
    2020:9888.0,
}
df_global['FAO_published_GgCH4'] = df_global['Year'].map(FAO_MM_CH4)
df_global['Ratio_to_FAO'] = df_global['Total_GgCH4'] / df_global['FAO_published_GgCH4']

# Regional annual
df_regional = df_out.groupby(['Year','Region'])[gg_cols].sum().reset_index()

# Species breakdown (2020)
sp_cols = [c for c in gg_cols if 'Total' not in c]
df_species2020 = df_out[df_out['Year']==2020].groupby('Region')[sp_cols].sum()
df_species2020_global = df_out[df_out['Year']==2020][sp_cols].sum().to_frame('GgCH4_2020')

# Save
df_global.to_csv((str(OUT_A_DATA) + '/ch4_mm/ch4_mm_global.csv'), index=False)
df_out[['Year','Area Code','Area','Region'] + gg_cols].to_csv((str(OUT_A_DATA) + '/ch4_mm/ch4_mm_country.csv'), index=False)
df_regional.to_csv((str(OUT_A_DATA) + '/ch4_mm/ch4_mm_regional.csv'), index=False)
df_species2020.to_csv((str(OUT_A_DATA) + '/ch4_mm/ch4_mm_species2020.csv'))

print("\n" + "=" * 75)
print("GLOBAL CH4 FROM MANURE MANAGEMENT — IPCC 2019 REFINEMENT TIER 1")
print("=" * 75)
print(f"{'Year':>5} | {'Our estimate':>14} | {'FAO published':>14} | {'Ratio':>8}")
print("-" * 55)
for _, row in df_global[df_global['Year'].isin(range(1970,2021,5))].iterrows():
    fao = row['FAO_published_GgCH4']
    print(f"{int(row.Year):>5} | {row['Total_GgCH4']:>14.1f} | {fao:>14.1f} | {row['Ratio_to_FAO']:>8.4f}")
print("-" * 55)
print("(all values in Gg CH4 = kt CH4 / year)")

print("\nSpecies contributions to global total (2020):")
for sp_col in sp_cols:
    sp_name = sp_col.replace('_GgCH4','').replace('_',' ')
    val = df_species2020_global.loc[sp_col, 'GgCH4_2020'] if sp_col in df_species2020_global.index else 0
    pct = val / df_global[df_global['Year']==2020]['Total_GgCH4'].values[0] * 100
    print(f"  {sp_name:20s}: {val:8.1f} Gg CH4  ({pct:.1f}%)")

print("\nRegional contributions (2020):")
r2020 = df_regional[df_regional['Year']==2020][['Region','Total_GgCH4']].sort_values('Total_GgCH4',ascending=False)
for _, row in r2020.iterrows():
    pct = row['Total_GgCH4'] / df_global[df_global['Year']==2020]['Total_GgCH4'].values[0] * 100
    print(f"  {row['Region']:25s}: {row['Total_GgCH4']:8.1f} Gg CH4  ({pct:.1f}%)")


# =============================================================================
# EDGAR EXTRACTION — add EDGAR_GgCH4 column to global CSV
# Source: EDGAR 2025, IPCC code 3.A.2
# =============================================================================
import pandas as _pd
import numpy as _np

_EDGAR_FILE = (str(EDGAR_CH4_NEW))
_YEARS_E = list(range(1970, 2021))
_YC_E    = [f'Y_{y}' for y in _YEARS_E]

_df_e = _pd.ExcelFile(_EDGAR_FILE).parse('IPCC 2006', header=9)
_sub  = _df_e[_df_e['ipcc_code_2006_for_standard_report'] == '3.A.2']
_edgar_vals = _sub[_YC_E].apply(_pd.to_numeric, errors='coerce').fillna(0).sum().values

_global_csv = (str(OUT_A_DATA) + '/ch4_mm/ch4_mm_global.csv')
_dg = _pd.read_csv(_global_csv)
_dg['EDGAR_GgCH4'] = _np.round(_edgar_vals, 3)
_dg.to_csv(_global_csv, index=False)
print(f'Added EDGAR_GgCH4 column to ch4_mm_global.csv')
print(f'  EDGAR 3.A.2 2020: {_edgar_vals[-1]:.1f} Gg')
