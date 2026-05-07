
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
    EDGAR_N2O_NEW, FAO_EMISSIONS_CSV, FAO_FERTILIZERS_CSV, FAO_PRODUCTION_CSV, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
)


# =============================================================================
# N2O EMISSIONS FROM MANAGED SOILS — IPCC TIER 1  |  STANDALONE PROCESSING
# =============================================================================
# Produces: n2o_ms_global.csv, n2o_ms_country.csv,
#           n2o_ms_regional.csv, n2o_ms_components.csv
#
# SECTOR SCOPE (IPCC 2006/2019 Refinement Vol.4 Ch.11)
# ------------------------------------------------------
# Five N-input pathways contributing to agricultural soil N2O:
#   FSN  — Synthetic N fertilizers (from fertilizer nutrient data)
#   FON  — Organic N from managed manure applied to soils (from livestock data)
#   FPRP — N from Pasture, Range & Paddock excreta (from livestock data)
#   FCR  — N from Crop Residues returned to field (from crop production data)
#   FSOM — N from Drained Organic Soils (taken directly from FAO published data)
#
# TWO HEADLINE VARIANTS (both 2006 and 2019 parameters):
#   Without PRP : FSN + FON + FCR + FSOM
#   With PRP    : FSN + FON + FCR + FSOM + FPRP  (= FAO "Agricultural Soils")
#
# GOVERNING EQUATIONS (Ch.11 Eqs. 11.1, 11.9, 11.10)
# -----------------------------------------------------
# Direct:
#   N2O_dir-N = (FSN + FON + FCR + FSOM + FPRP) × EF1
#   N2O_dir   = N2O_dir-N × (44/28)
# Indirect — volatilisation:
#   N2O_vol-N = (FSN×FracGASF + FON×FracGASOM + FPRP×FracGASPRP) × EF4
#   N2O_vol   = N2O_vol-N × (44/28)
# Indirect — leaching [wet regions only]:
#   N2O_leach-N = (FSN + FON + FCR + FPRP) × FracLEACH × EF5
#   N2O_leach   = N2O_leach-N × (44/28)
#
# KEY PARAMETERS (IPCC 2019 Refinement Table 11.1 and 11.3)
# -----------------------------------------------------------
#   EF1        = 0.010  kg N2O-N kg-1 N  (unchanged 2006→2019, aggregated Tier 1)
#   FracGASF   = 0.11 (2019) / 0.10 (2006)  — synthetic N volatilisation
#   FracGASOM  = 0.21 (2019) / 0.20 (2006)  — organic N volatilisation
#   FracGASPRP = 0.21 (2019) / 0.20 (2006)  — PRP N volatilisation
#   EF4        = 0.010  kg N2O-N kg-1 N volatilised
#   FracLEACH  = 0.24 (2019) / 0.30 (2006)  [dry regions: 0]
#   EF5        = 0.011 (2019) / 0.0075 (2006)
#
# NOTES ON FSOM
# -------------
# Country-level drained organic soil N2O is read directly from FAO published
# emissions (FAO TIER 1, Item "Drained organic soils (N2O)") rather than
# computed from area data. This is because (a) area data for drained histosols
# is not in the standard FAO production files and (b) this component is only
# ~5% of total managed soils N2O. Pre-1990 values are held at the 1990 level.
#
# EDGAR BENCHMARK
# ---------------
#   3.C.4 — Direct N2O from managed soils   (EDGAR_N2O_1970_2024.xlsx)
#   3.C.5 — Indirect N2O from managed soils
# =============================================================================

import pandas as pd
import numpy as np

# =============================================================================
# SECTION 0: CONFIGURATION
# =============================================================================
PROD_CSV  = str(FAO_PRODUCTION_CSV)
FERT_CSV  = str(FAO_FERTILIZERS_CSV)
EMISS_CSV = str(FAO_EMISSIONS_CSV)
EDGAR_N2O = str(EDGAR_N2O_NEW)
OUT_DIR   = (str(OUT_A_DATA) + '/n2o_ms/')

YEAR_START = 1970;  YEAR_END = 2020
YEARS      = list(range(YEAR_START, YEAR_END + 1))
YEAR_COLS  = [f'Y{y}' for y in YEARS]
KG_TO_GG   = 1.0e-6;  T_TO_KG = 1.0e3;  MW_N2O = 44./28.

# =============================================================================
# SECTION 1: EMISSION FACTOR PARAMETERS
# =============================================================================
EF1 = 0.010  # direct, both guidelines

FRAC_GASF_06 = 0.10; FRAC_GASOM_06 = 0.20; FRAC_GASPRP_06 = 0.20
EF4_06 = 0.010; FRAC_LEACH_06 = 0.30; EF5_06 = 0.0075

FRAC_GASF_19 = 0.11; FRAC_GASOM_19 = 0.21; FRAC_GASPRP_19 = 0.21
EF4_19 = 0.010; FRAC_LEACH_19 = 0.24; EF5_19 = 0.011

# =============================================================================
# SECTION 2: REGION MAPPING
# =============================================================================
R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']
DRY_REGIONS = {'Middle East'}

REGION_SETS = {
    'Indian Subcontinent':{'Afghanistan','Bangladesh','Bhutan','India','Maldives','Nepal','Pakistan','Sri Lanka'},
    'North America':{'United States of America','Canada','Greenland','Saint Pierre and Miquelon'},
    'Western Europe':{'Albania','Andorra','Austria','Belgium','Belgium-Luxembourg','Cyprus','Denmark',
        'Finland','France and Monaco','France','Germany','Greece','Iceland','Ireland',
        'Israel and Palestine, State of','Italy, San Marino and the Holy See','Italy',
        'Luxembourg','Malta','Netherlands','Norway','Portugal','Spain and Andorra','Spain',
        'Sweden','Switzerland and Liechtenstein','Switzerland','United Kingdom',
        'Monaco','San Marino','Liechtenstein'},
    'Eastern Europe':{'Armenia','Azerbaijan','Belarus','Bosnia and Herzegovina','Bulgaria','Croatia',
        'Czechia','Czech Republic','Estonia','Georgia','Hungary','Kazakhstan','Kyrgyzstan',
        'Latvia','Lithuania','Moldova','Montenegro','North Macedonia','Poland','Romania',
        'Russia','Serbia','Serbia and Montenegro','Slovakia','Slovenia','Tajikistan',
        'Türkiye','Turkey','Turkmenistan','Ukraine','Uzbekistan','Kosovo','Yugoslavia'},
    'Oceania':{'Australia','Cook Islands','Fiji','Kiribati','Marshall Islands','Nauru',
        'New Caledonia','New Zealand','Niue','Palau','Papua New Guinea','Samoa',
        'Solomon Islands','Tonga','Tuvalu','Vanuatu','French Polynesia'},
    'Latin America':{'Antigua and Barbuda','Argentina','Bahamas','Barbados','Belize',
        'Bolivia (Plurinational State of)','Bolivia','Brazil','Chile','Colombia',
        'Costa Rica','Cuba','Dominica','Dominican Republic','Ecuador','El Salvador',
        'Grenada','Guatemala','Guyana','Haiti','Honduras','Jamaica','Mexico',
        'Nicaragua','Panama','Paraguay','Peru','Saint Kitts and Nevis','Saint Lucia',
        'Saint Vincent and the Grenadines','Suriname','Trinidad and Tobago','Uruguay',
        'Venezuela (Bolivarian Republic of)','Venezuela','Puerto Rico','Aruba',
        'Netherlands Antilles','Bermuda','Cayman Islands','British Virgin Islands',
        'Turks and Caicos Islands'},
    'Middle East':{'Bahrain','Egypt','Iran (Islamic Republic of)','Iran','Iraq','Jordan','Kuwait',
        'Lebanon','Libya','Morocco','Oman','Qatar','Saudi Arabia','Syrian Arab Republic',
        'Syria','Tunisia','United Arab Emirates','Yemen','Algeria','Djibouti','Israel',
        'Mauritania','Somalia','Sudan','Sudan and South Sudan'},
    'Africa':{'Angola','Benin','Botswana','Burkina Faso','Burundi','Cabo Verde','Cameroon',
        'Central African Republic','Chad','Comoros','Congo','Côte d`Ivoire',"Côte d'Ivoire",
        'Democratic Republic of the Congo','Equatorial Guinea','Eritrea','Eswatini','Ethiopia',
        'Gabon','Gambia','Ghana','Guinea','Guinea-Bissau','Kenya','Lesotho','Liberia',
        'Madagascar','Malawi','Mali','Mauritius','Mozambique','Namibia','Niger','Nigeria',
        'Rwanda','São Tomé and Príncipe','Sao Tome and Principe','Senegal','Seychelles',
        'Sierra Leone','South Africa','South Sudan','Tanzania','Togo','Uganda',
        'United Republic of Tanzania','Zambia','Zimbabwe','Ethiopia PDR','Cape Verde',
        'Réunion','Mayotte'},
    'Asia':{'Brunei Darussalam','Cambodia','China','China, mainland','China, Hong Kong SAR',
        'China, Macao SAR','China, Taiwan Province of','Indonesia','Japan',
        "Democratic People's Republic of Korea",'North Korea','Korea, Republic of',
        'South Korea','Republic of Korea',"Lao People's Democratic Republic",'Laos',
        'Malaysia','Mongolia','Myanmar','Myanmar/Burma','Philippines','Singapore',
        'Thailand','Timor-Leste','Viet Nam','Vietnam','Hong Kong','Macao','Taiwan'},
}
def get_region(c):
    for r, s in REGION_SETS.items():
        if c in s: return r
    return 'Africa'

# =============================================================================
# SECTION 3: LIVESTOCK PARAMETERS (same as N2O Manure Management sector)
# Source: IPCC 2019 Refinement Vol.4 Ch.10, Tables 10.19, 10A.4–10A.9
# =============================================================================
def rd(v): return dict(zip(R9, v))

NRATE_D06  = rd([0.44,0.48,0.35,0.44,0.48,0.60,0.70,0.47,0.47])
NRATE_O06  = rd([0.31,0.33,0.35,0.50,0.36,0.63,0.79,0.34,0.34])
NRATE_B06  = {r: 0.32 for r in R9}
NRATE_MS06 = rd([0.42,0.51,0.55,0.53,1.57,1.57,1.57,0.42,0.42])
NRATE_BS06 = rd([0.24,0.42,0.46,0.46,0.55,0.55,0.55,0.24,0.24])
NRATE_L06  = {r: (0.96 if r == 'Western Europe' else 0.82) for r in R9}
NRATE_BR06 = {r: 1.10 for r in R9}
NRATE_DK   = {r: 0.83 for r in R9}
NRATE_TK   = {r: 0.74 for r in R9}

NRATE_D19  = rd([0.59,0.54,0.42,0.72,0.39,0.44,0.50,0.44,0.65])
NRATE_O19  = rd([0.40,0.42,0.47,0.46,0.31,0.45,0.56,0.38,0.44])
NRATE_B19  = rd([0.32,0.45,0.35,0.32,0.41,0.42,0.39,0.44,0.58])
NRATE_SW19 = rd([0.39,0.65,0.63,0.54,0.59,0.44,0.66,0.61,0.68])
NRATE_L19  = rd([1.13,0.87,0.81,1.04,1.17,1.20,1.11,1.00,1.65])
NRATE_BR19 = rd([1.59,1.14,1.12,1.59,1.23,1.40,1.43,1.35,1.58])
NRATE_SH19 = rd([0.35,0.36,0.36,0.43,0.32,0.32,0.32,0.32,0.32])
NRATE_GT19 = rd([0.46,0.46,0.44,0.42,0.34,0.34,0.34,0.34,0.34])
NRATE_HR   = {r: 0.55 for r in R9}  # horses/mules/asses (Ch.10 Table 10.19 approx.)

TAM_D06  = rd([604,600,550,500,400,275,275,350,275])
TAM_O06  = rd([389,420,391,330,305,173,173,319,110])
TAM_B06  = {r: 380 for r in R9}
TAM_MS06 = rd([46,50,50,45,28,28,28,28,28])
TAM_BS06 = rd([198,198,180,180,28,28,28,28,28])
TAM_L06  = {r: 1.8 for r in R9};  TAM_BR06 = {r: 0.9 for r in R9}
TAM_DK   = {r: 2.7 for r in R9};  TAM_TK   = {r: 6.8 for r in R9}
TAM_D19  = rd([650,600,550,488,508,260,349,386,285])
TAM_O19  = rd([407,405,389,359,303,236,275,299,226])
TAM_B19  = rd([380,509,467,380,315,339,381,336,321])
TAM_SW19 = rd([77,76,77,61,65,49,59,58,59])
TAM_L19  = rd([1.5,1.9,1.9,2.0,1.4,1.4,1.2,1.5,1.3])
TAM_BR19 = rd([1.4,1.2,1.1,1.2,0.9,0.8,0.7,0.8,0.8])
TAM_SH19 = {r: (40.0 if r in {'North America','Western Europe','Eastern Europe','Oceania'} else 31.0) for r in R9}
TAM_GT19 = rd([41,40,36,33,24,24,24,24,24])
TAM_HR   = {r: 350.0 for r in R9}  # average body mass, kg

def nex(nr, tm, r): return nr[r] * tm[r] / 1000.0 * 365.0

# AWMS tables [9 MMS: 0=Lagoon,1=Slurry,2=Solid,3=Drylot,4=PRP,5=Daily,6=Digester,7=Burned,8=Other]
AWMS_D = {
    'North America':      [0.150,0.270,0.263,0.000,0.108,0.184,0.000,0.000,0.026],
    'Western Europe':     [0.000,0.357,0.368,0.000,0.200,0.070,0.000,0.000,0.005],
    'Eastern Europe':     [0.000,0.175,0.600,0.000,0.180,0.025,0.000,0.000,0.020],
    'Oceania':            [0.160,0.010,0.000,0.000,0.760,0.080,0.000,0.000,0.000],
    'Latin America':      [0.000,0.010,0.010,0.000,0.360,0.620,0.000,0.000,0.000],
    'Africa':             [0.000,0.000,0.010,0.000,0.830,0.050,0.000,0.060,0.040],
    'Middle East':        [0.000,0.010,0.020,0.000,0.800,0.020,0.000,0.170,0.000],
    'Asia':               [0.040,0.380,0.000,0.000,0.200,0.290,0.020,0.070,0.000],
    'Indian Subcontinent':[0.000,0.010,0.000,0.000,0.270,0.190,0.010,0.510,0.000],
}
AWMS_O = {
    'North America':      [0.000,0.002,0.000,0.184,0.815,0.000,0.000,0.000,0.000],
    'Western Europe':     [0.000,0.252,0.390,0.000,0.320,0.018,0.000,0.000,0.020],
    'Eastern Europe':     [0.000,0.225,0.440,0.000,0.200,0.000,0.000,0.000,0.135],
    'Oceania':            [0.000,0.000,0.000,0.090,0.910,0.000,0.000,0.000,0.000],
    'Latin America':      [0.000,0.000,0.000,0.000,0.990,0.000,0.000,0.000,0.010],
    'Africa':             [0.000,0.000,0.000,0.010,0.950,0.010,0.000,0.030,0.000],
    'Middle East':        [0.000,0.000,0.000,0.010,0.790,0.020,0.000,0.170,0.020],
    'Asia':               [0.000,0.000,0.000,0.460,0.500,0.020,0.000,0.020,0.000],
    'Indian Subcontinent':[0.000,0.010,0.000,0.040,0.220,0.200,0.010,0.530,0.000],
}
AWMS_B = {
    'North America':      [0.000,0.000,0.000,0.000,1.000,0.000,0.000,0.000,0.000],
    'Western Europe':     [0.000,0.200,0.000,0.790,0.000,0.000,0.000,0.000,0.000],
    'Eastern Europe':     [0.000,0.240,0.000,0.000,0.290,0.000,0.000,0.000,0.470],
    'Oceania':            [0.000,0.000,0.000,0.000,1.000,0.000,0.000,0.000,0.000],
    'Latin America':      [0.000,0.000,0.000,0.000,0.990,0.000,0.000,0.000,0.010],
    'Africa':             [0.000,0.000,0.000,0.000,1.000,0.000,0.000,0.000,0.000],
    'Middle East':        [0.000,0.000,0.000,0.000,0.200,0.190,0.000,0.420,0.190],
    'Asia':               [0.000,0.000,0.000,0.410,0.500,0.040,0.000,0.050,0.000],
    'Indian Subcontinent':[0.000,0.000,0.000,0.040,0.190,0.210,0.010,0.550,0.000],
}
AWMS_SW = {
    'North America':      [0.328,0.185,0.042,0.040,0.000,0.406,0.000,0.000,0.000],
    'Western Europe':     [0.087,0.000,0.137,0.000,0.028,0.698,0.020,0.000,0.030],
    'Eastern Europe':     [0.030,0.000,0.420,0.000,0.247,0.247,0.000,0.000,0.057],
    'Oceania':            [0.540,0.000,0.030,0.150,0.000,0.000,0.000,0.000,0.280],
    'Latin America':      [0.000,0.080,0.100,0.410,0.000,0.000,0.020,0.000,0.400],
    'Africa':             [0.000,0.060,0.060,0.870,0.010,0.000,0.000,0.000,0.000],
    'Middle East':        [0.000,0.140,0.000,0.690,0.000,0.170,0.000,0.000,0.000],
    'Asia':               [0.000,0.400,0.000,0.540,0.000,0.000,0.000,0.060,0.000],
    'Indian Subcontinent':[0.090,0.220,0.160,0.300,0.030,0.000,0.090,0.080,0.030],
}
AWMS_SG19 = {
    'North America':      [0.000,0.000,0.200,0.180,0.620,0.000,0.000,0.000,0.000],
    'Western Europe':     [0.000,0.000,0.130,0.000,0.870,0.000,0.000,0.000,0.000],
    'Eastern Europe':     [0.000,0.000,0.150,0.150,0.700,0.000,0.000,0.000,0.000],
    'Oceania':            [0.000,0.000,0.200,0.000,0.800,0.000,0.000,0.000,0.000],
    'Latin America':      [0.000,0.000,0.100,0.000,0.900,0.000,0.000,0.000,0.000],
    'Africa':             [0.000,0.000,0.050,0.000,0.950,0.000,0.000,0.000,0.000],
    'Middle East':        [0.000,0.000,0.100,0.200,0.700,0.000,0.000,0.000,0.000],
    'Asia':               [0.000,0.000,0.050,0.000,0.950,0.000,0.000,0.000,0.000],
    'Indian Subcontinent':[0.000,0.000,0.050,0.000,0.950,0.000,0.000,0.000,0.000],
}
# Horses/mules/asses: largely on pasture
AWMS_HR = {r: [0.000,0.050,0.150,0.100,0.650,0.000,0.000,0.000,0.050] for r in R9}
for r in ['North America','Western Europe','Eastern Europe']:
    AWMS_HR[r] = [0.000,0.100,0.200,0.150,0.500,0.000,0.000,0.000,0.050]
# Poultry: no PRP; mostly in solid/managed systems
AWMS_PL = {r: [0.000,0.000,0.900,0.000,0.000,0.100,0.000,0.000,0.000] for r in R9}

def _prp(awms, r):  return awms[r][4]
def _fon(awms, r):  return 1.0 - awms[r][0] - awms[r][4] - awms[r][7]

def contrib(head, Nex, awms, r, mode):
    """Return kg N for PRP or FON contribution."""
    f = _prp(awms, r) if mode == 'prp' else _fon(awms, r)
    return head * Nex * f

# =============================================================================
# SECTION 4: CROP RESIDUE PARAMETERS (IPCC 2019 Refinement Table 11.2)
# =============================================================================
# Each tuple: (R_AGP, Frac_Remove, NC_AGR, R_BGP, NC_BGR, DM_frac)
CROP_PARAMS = {
    'Wheat':        (1.20, 0.70, 0.006, 0.23, 0.009, 0.87),
    'Rice':         (1.757,0.70, 0.007, 0.16, 0.009, 0.87),
    'Maize':        (1.00, 0.70, 0.006, 0.22, 0.009, 0.87),
    'Barley':       (1.20, 0.70, 0.007, 0.22, 0.009, 0.87),
    'OtherCereals': (1.40, 0.70, 0.007, 0.22, 0.009, 0.87),
    'Roots':        (0.20, 0.00, 0.014, 0.20, 0.014, 0.20),
    'SugarCane':    (0.30, 0.50, 0.004, 0.40, 0.004, 0.26),
    'SugarBeet':    (0.20, 0.00, 0.006, 0.20, 0.006, 0.23),
    'Pulses':       (1.50, 0.50, 0.019, 0.19, 0.008, 0.87),
    'Soybean':      (1.50, 0.85, 0.008, 0.19, 0.008, 0.87),
    'OilSeeds':     (1.40, 0.85, 0.007, 0.22, 0.009, 0.87),
    'Vegetables':   (0.40, 0.10, 0.019, 0.10, 0.019, 0.10),
    'Fruits':       (0.00, 0.00, 0.012, 0.10, 0.012, 0.15),
    'Cotton':       (2.10, 0.85, 0.012, 0.23, 0.009, 0.87),
}
# N_residue (kg N) per tonne fresh harvested product
def fcr_n_per_t(ct):
    R, FR, NCA, RB, NCB, DM = CROP_PARAMS[ct]
    return DM * (R * (1 - FR) * NCA + RB * NCB)

FAO_TO_IPCC = {
    'Wheat':                         'Wheat',
    'Rice':                          'Rice',
    'Maize (corn)':                  'Maize',
    'Barley':                        'Barley',
    'Sorghum':                       'OtherCereals',
    'Millet':                        'OtherCereals',
    'Oats':                          'OtherCereals',
    'Rye':                           'OtherCereals',
    'Roots and Tubers, Total':       'Roots',
    'Sugar cane':                    'SugarCane',
    'Sugar beet':                    'SugarBeet',
    'Pulses, Total':                 'Pulses',
    'Soya beans':                    'Soybean',
    'Sunflower seed':                'OilSeeds',
    'Rape or colza seed':            'OilSeeds',
    'Groundnuts, excluding shelled': 'OilSeeds',
    'Vegetables Primary':            'Vegetables',
    'Fruit Primary':                 'Fruits',
    'Cotton seed':                   'Cotton',
}
CROP_N_FACTOR = {item: fcr_n_per_t(itype) for item, itype in FAO_TO_IPCC.items()}

# =============================================================================
# SECTION 5: LOAD INPUT DATA
# =============================================================================
print("Loading input data …")
df_raw  = pd.read_csv(PROD_CSV, low_memory=False)
df_prod = df_raw[df_raw['Area Code'] < 5000].copy()
df_prod[YEAR_COLS] = df_prod[YEAR_COLS].apply(pd.to_numeric, errors='coerce').fillna(0.)

df_fert_raw = pd.read_csv(FERT_CSV, low_memory=False)
df_fert = df_fert_raw[
    (df_fert_raw['Area Code'] < 5000) &
    (df_fert_raw['Item'] == 'Nutrient nitrogen N (total)') &
    (df_fert_raw['Element'] == 'Agricultural Use') &
    (df_fert_raw['Area Code'] != 351)  # exclude China aggregate
].copy().set_index('Area Code')
df_fert[YEAR_COLS] = df_fert[YEAR_COLS].apply(pd.to_numeric, errors='coerce').fillna(0.)

df_em = pd.read_csv(EMISS_CSV, low_memory=False)
areas  = df_prod[['Area Code','Area']].drop_duplicates().dropna()
code_to_name   = dict(zip(areas['Area Code'], areas['Area']))
code_to_region = {ac: get_region(name) for ac, name in code_to_name.items()}
print(f"  {df_prod['Area Code'].nunique()} countries in production data")

# ── Livestock extracts ──────────────────────────────────────────────────────
def extr(item, el='Stocks'):
    m = (df_prod['Item'] == item) & (df_prod['Element'] == el)
    return df_prod[m][['Area Code','Area'] + YEAR_COLS].set_index('Area Code')

ct_df = extr('Cattle'); bu_df = extr('Buffalo')
sh_df = extr('Sheep');  gt_df = extr('Goats')
sw_df = extr('Swine / pigs')
ch_df = extr('Chickens'); dk_df = extr('Ducks'); tk_df = extr('Turkeys')
da_df = extr('Raw milk of cattle','Milk Animals')
la_df = extr('Hen eggs in shell, fresh','Laying')
ho_df = extr('Horses'); mu_df = extr('Mules'); as_df = extr('Asses')

def gv(ds, ac, yc):
    try:
        if ac in ds.index:
            v = ds.loc[ac, yc]
            if isinstance(v, pd.Series): v = v.iloc[0]
            return float(v) if pd.notna(v) else 0.
    except Exception:
        pass
    return 0.

# ── Crop production extracts ────────────────────────────────────────────────
crop_dfs = {}
for fao_item in FAO_TO_IPCC:
    m = (df_prod['Item'] == fao_item) & (df_prod['Element'] == 'Production')
    sub = df_prod[m][['Area Code','Area'] + YEAR_COLS].set_index('Area Code')
    if len(sub): crop_dfs[fao_item] = sub

# ── FSOM: FAO published drained organic soils N2O ─────────────────────────
fsom_em = df_em[
    (df_em['Item'] == 'Drained organic soils (N2O)') &
    (df_em['Element'] == 'Emissions (N2O)') &
    (df_em['Source'] == 'FAO TIER 1') &
    (df_em['Area Code'] < 5000)
].copy()
fsom_em[YEAR_COLS] = fsom_em[YEAR_COLS].apply(pd.to_numeric, errors='coerce')
idx_1990 = YEAR_COLS.index('Y1990')
for col in YEAR_COLS[:idx_1990]:
    fsom_em[col] = fsom_em['Y1990']  # pre-1990: hold 1990 constant
fsom_em = fsom_em.set_index('Area Code')

# ── FAO benchmark series ────────────────────────────────────────────────────
world_em = df_em[(df_em['Area'] == 'World') & (df_em['Source'] == 'FAO TIER 1')]

def fao_world_series(item, elem='Emissions (N2O)'):
    r = world_em[(world_em['Item'] == item) & (world_em['Element'] == elem)]
    if len(r) == 0: return np.zeros(len(YEARS))
    v = r[YEAR_COLS].astype(float).values[0]
    fv = next((x for x in v if not np.isnan(x)), 0.)
    return np.where(np.isnan(v), fv, v)

fao_synfert = fao_world_series('Synthetic Fertilizers')
fao_manapp  = fao_world_series('Manure applied to Soils')
fao_prp     = fao_world_series('Manure left on Pasture')
fao_cropr   = fao_world_series('Crop Residues')
fao_fsom_w  = fao_world_series('Drained organic soils (N2O)')
fao_total_w = fao_world_series('Agricultural Soils')
fao_noprp_w = fao_synfert + fao_manapp + fao_cropr + fao_fsom_w

all_codes = sorted(
    set(ct_df.index) | set(bu_df.index) | set(sw_df.index) |
    set(ch_df.index) | set(sh_df.index) | set(gt_df.index) |
    set(df_fert.index)
)
print(f"  {len(all_codes)} unique country codes across all sources")

# =============================================================================
# SECTION 6: MAIN COMPUTATION LOOP
# =============================================================================
print(f"Computing N2O for {len(all_codes)} countries × {len(YEARS)} years …")
records = []

for ac in all_codes:
    country = code_to_name.get(ac, f'Code_{ac}')
    region  = get_region(country)
    wet     = region not in DRY_REGIONS

    # FSN array (kg N)
    fsn_row  = df_fert.loc[[ac]] if ac in df_fert.index else None
    fsn_vals = (fsn_row[YEAR_COLS].values[0] * T_TO_KG
                if fsn_row is not None and len(fsn_row) else np.zeros(len(YEARS)))

    # FSOM array (Gg N2O, already from FAO)
    fsom_row = fsom_em.loc[[ac]] if ac in fsom_em.index else None
    fsom_arr = (np.nan_to_num(fsom_row[YEAR_COLS].values[0].astype(float))
                if fsom_row is not None and len(fsom_row) else np.zeros(len(YEARS)))

    for yi, yc in enumerate(YEAR_COLS):
        year = YEARS[yi]

        # ── Activity data ────────────────────────────────────────────────
        ct   = gv(ct_df, ac, yc)
        da   = min(gv(da_df, ac, yc), ct);  oc = ct - da
        bu   = gv(bu_df, ac, yc)
        sh   = gv(sh_df, ac, yc);  gt = gv(gt_df, ac, yc)
        sw   = gv(sw_df, ac, yc)
        ch   = gv(ch_df, ac, yc) * 1000
        la   = min(gv(la_df, ac, yc) * 1000, ch);  br = ch - la
        dk   = gv(dk_df, ac, yc) * 1000
        tk   = gv(tk_df, ac, yc) * 1000
        ho   = (gv(ho_df, ac, yc) + gv(mu_df, ac, yc) + gv(as_df, ac, yc))
        fsn_kg   = fsn_vals[yi]
        fsom_gg  = fsom_arr[yi]

        # ── Nex rates ─────────────────────────────────────────────────────
        nx_d06  = nex(NRATE_D06,  TAM_D06,  region)
        nx_o06  = nex(NRATE_O06,  TAM_O06,  region)
        nx_b06  = nex(NRATE_B06,  TAM_B06,  region)
        nx_sw06 = 0.9 * nex(NRATE_MS06, TAM_MS06, region) + 0.1 * nex(NRATE_BS06, TAM_BS06, region)
        nx_l06  = nex(NRATE_L06,  TAM_L06,  region)
        nx_br06 = nex(NRATE_BR06, TAM_BR06, region)
        nx_dk   = nex(NRATE_DK,   TAM_DK,   region)
        nx_tk   = nex(NRATE_TK,   TAM_TK,   region)
        nx_d19  = nex(NRATE_D19,  TAM_D19,  region)
        nx_o19  = nex(NRATE_O19,  TAM_O19,  region)
        nx_b19  = nex(NRATE_B19,  TAM_B19,  region)
        nx_sw19 = nex(NRATE_SW19, TAM_SW19, region)
        nx_l19  = nex(NRATE_L19,  TAM_L19,  region)
        nx_br19 = nex(NRATE_BR19, TAM_BR19, region)
        nx_sh19 = nex(NRATE_SH19, TAM_SH19, region)
        nx_gt19 = nex(NRATE_GT19, TAM_GT19, region)
        nx_hr   = nex(NRATE_HR,   TAM_HR,   region)

        # ── FPRP (kg N yr-1) ─────────────────────────────────────────────
        def prp(head, Nex, awms): return contrib(head, Nex, awms, region, 'prp')
        fprp_06 = (prp(da,nx_d06,AWMS_D) + prp(oc,nx_o06,AWMS_O) + prp(bu,nx_b06,AWMS_B) +
                   prp(sw,nx_sw06,AWMS_SW) + prp(sh,nx_sh19,AWMS_SG19) +
                   prp(gt,nx_gt19,AWMS_SG19) + prp(ho,nx_hr,AWMS_HR))
        fprp_19 = (prp(da,nx_d19,AWMS_D) + prp(oc,nx_o19,AWMS_O) + prp(bu,nx_b19,AWMS_B) +
                   prp(sw,nx_sw19,AWMS_SW) + prp(sh,nx_sh19,AWMS_SG19) +
                   prp(gt,nx_gt19,AWMS_SG19) + prp(ho,nx_hr,AWMS_HR))

        # ── FON (kg N yr-1) ───────────────────────────────────────────────
        def fon_c(head, Nex, awms): return contrib(head, Nex, awms, region, 'fon')
        fon_06 = (fon_c(da,nx_d06,AWMS_D) + fon_c(oc,nx_o06,AWMS_O) + fon_c(bu,nx_b06,AWMS_B) +
                  fon_c(sw,nx_sw06,AWMS_SW) + fon_c(la,nx_l06,AWMS_PL) + fon_c(br,nx_br06,AWMS_PL) +
                  fon_c(dk,nx_dk,AWMS_PL) + fon_c(tk,nx_tk,AWMS_PL) +
                  fon_c(sh,nx_sh19,AWMS_SG19) + fon_c(gt,nx_gt19,AWMS_SG19) + fon_c(ho,nx_hr,AWMS_HR))
        fon_19 = (fon_c(da,nx_d19,AWMS_D) + fon_c(oc,nx_o19,AWMS_O) + fon_c(bu,nx_b19,AWMS_B) +
                  fon_c(sw,nx_sw19,AWMS_SW) + fon_c(la,nx_l19,AWMS_PL) + fon_c(br,nx_br19,AWMS_PL) +
                  fon_c(dk,nx_dk,AWMS_PL) + fon_c(tk,nx_tk,AWMS_PL) +
                  fon_c(sh,nx_sh19,AWMS_SG19) + fon_c(gt,nx_gt19,AWMS_SG19) + fon_c(ho,nx_hr,AWMS_HR))

        # ── FCR (kg N yr-1) ───────────────────────────────────────────────
        fcr_kg = 0.0
        for fao_item, ipcc_type in FAO_TO_IPCC.items():
            cdf = crop_dfs.get(fao_item)
            if cdf is None: continue
            prod_t = gv(cdf, ac, yc)
            if prod_t > 0:
                fcr_kg += prod_t * CROP_N_FACTOR[fao_item] * T_TO_KG

        # ── DIRECT N2O (Gg) ───────────────────────────────────────────────
        def dir_gg(fsn, fon, fcr, fprp, fsom):
            return (fsn + fon + fcr + fprp) * EF1 * MW_N2O * KG_TO_GG + fsom

        d_np06 = dir_gg(fsn_kg, fon_06, fcr_kg, 0.,     fsom_gg)
        d_wp06 = dir_gg(fsn_kg, fon_06, fcr_kg, fprp_06, fsom_gg)
        d_np19 = dir_gg(fsn_kg, fon_19, fcr_kg, 0.,     fsom_gg)
        d_wp19 = dir_gg(fsn_kg, fon_19, fcr_kg, fprp_19, fsom_gg)

        # ── INDIRECT — VOLATILISATION (Gg) ───────────────────────────────
        def vol_gg(fsn, fon, fprp, gf, gm, gp, ef4):
            return (fsn*gf + fon*gm + fprp*gp) * ef4 * MW_N2O * KG_TO_GG

        v_np06 = vol_gg(fsn_kg, fon_06, 0.,     FRAC_GASF_06, FRAC_GASOM_06, FRAC_GASPRP_06, EF4_06)
        v_wp06 = vol_gg(fsn_kg, fon_06, fprp_06, FRAC_GASF_06, FRAC_GASOM_06, FRAC_GASPRP_06, EF4_06)
        v_np19 = vol_gg(fsn_kg, fon_19, 0.,     FRAC_GASF_19, FRAC_GASOM_19, FRAC_GASPRP_19, EF4_19)
        v_wp19 = vol_gg(fsn_kg, fon_19, fprp_19, FRAC_GASF_19, FRAC_GASOM_19, FRAC_GASPRP_19, EF4_19)

        # ── INDIRECT — LEACHING (Gg, wet regions only) ───────────────────
        def leach_gg(fsn, fon, fcr, fprp, fl, ef5):
            return (fsn + fon + fcr + fprp) * fl * ef5 * MW_N2O * KG_TO_GG if wet else 0.

        l_np06 = leach_gg(fsn_kg, fon_06, fcr_kg, 0.,     FRAC_LEACH_06, EF5_06)
        l_wp06 = leach_gg(fsn_kg, fon_06, fcr_kg, fprp_06, FRAC_LEACH_06, EF5_06)
        l_np19 = leach_gg(fsn_kg, fon_19, fcr_kg, 0.,     FRAC_LEACH_19, EF5_19)
        l_wp19 = leach_gg(fsn_kg, fon_19, fcr_kg, fprp_19, FRAC_LEACH_19, EF5_19)

        records.append({
            'Year': year, 'Area_Code': ac, 'Country': country, 'Region': region,
            'FSN_kgN':        round(fsn_kg,  2),
            'FON_2006_kgN':   round(fon_06,  2),
            'FON_2019_kgN':   round(fon_19,  2),
            'FPRP_2006_kgN':  round(fprp_06, 2),
            'FPRP_2019_kgN':  round(fprp_19, 2),
            'FCR_kgN':        round(fcr_kg,  2),
            'FSOM_GgN2O':     round(fsom_gg, 6),
            'Direct_noPRP_2006_GgN2O':   round(d_np06, 6),
            'Direct_withPRP_2006_GgN2O': round(d_wp06, 6),
            'Indirect_noPRP_2006_GgN2O': round(v_np06 + l_np06, 6),
            'Indirect_withPRP_2006_GgN2O':round(v_wp06 + l_wp06, 6),
            'Total_noPRP_2006_GgN2O':    round(d_np06 + v_np06 + l_np06, 6),
            'Total_withPRP_2006_GgN2O':  round(d_wp06 + v_wp06 + l_wp06, 6),
            'Total_noPRP_2019_GgN2O':    round(d_np19 + v_np19 + l_np19, 6),
            'Total_withPRP_2019_GgN2O':  round(d_wp19 + v_wp19 + l_wp19, 6),
        })

print(f"  {len(records):,} records computed.")
df_c = pd.DataFrame(records)

# =============================================================================
# SECTION 7: BUILD OUTPUT CSVs
# =============================================================================
df_c.to_csv(OUT_DIR + 'n2o_ms_country.csv', index=False)
print("Saved: n2o_ms_country.csv")

TCOLS = ['Total_noPRP_2006_GgN2O','Total_withPRP_2006_GgN2O',
         'Total_noPRP_2019_GgN2O','Total_withPRP_2019_GgN2O']
dr = df_c.groupby(['Region','Year'])[TCOLS].sum().reset_index()
dr['_o'] = dr['Region'].apply(lambda r: R9.index(r) if r in R9 else 99)
dr = dr.sort_values(['_o','Year']).drop(columns='_o')
dr.to_csv(OUT_DIR + 'n2o_ms_regional.csv', index=False)
print("Saved: n2o_ms_regional.csv")

# Global with all components
ALLCOLS = ['FSN_kgN','FON_2006_kgN','FON_2019_kgN','FPRP_2006_kgN','FPRP_2019_kgN',
           'FCR_kgN','FSOM_GgN2O'] + TCOLS + [
           'Direct_noPRP_2006_GgN2O','Direct_withPRP_2006_GgN2O',
           'Indirect_noPRP_2006_GgN2O','Indirect_withPRP_2006_GgN2O']
dg = df_c.groupby('Year')[ALLCOLS].sum().reset_index()

# Convert kgN to direct-emissions Gg for component display
for col, ipcc_t in [('FSN','FSN_kgN'),('FON_2006','FON_2006_kgN'),
                    ('FON_2019','FON_2019_kgN'),('FCR','FCR_kgN')]:
    dg[f'{col}_dir_GgN2O'] = dg[ipcc_t] * EF1 * MW_N2O * KG_TO_GG
dg['FPRP_2006_dir_GgN2O'] = dg['FPRP_2006_kgN'] * EF1 * MW_N2O * KG_TO_GG
dg['FPRP_2019_dir_GgN2O'] = dg['FPRP_2019_kgN'] * EF1 * MW_N2O * KG_TO_GG

# FAO benchmarks
dg['FAO_synfert_GgN2O'] = fao_synfert
dg['FAO_manapp_GgN2O']  = fao_manapp
dg['FAO_prp_GgN2O']     = fao_prp
dg['FAO_cropr_GgN2O']   = fao_cropr
dg['FAO_fsom_GgN2O']    = fao_fsom_w
dg['FAO_total_GgN2O']   = fao_total_w
dg['FAO_noPRP_GgN2O']   = fao_noprp_w

# EDGAR 3.C.4 + 3.C.5
df_edgar = pd.ExcelFile(EDGAR_N2O).parse('IPCC 2006', header=9)
YC_E = [f'Y_{y}' for y in YEARS]
edgar_34 = df_edgar[df_edgar['ipcc_code_2006_for_standard_report']=='3.C.4'][YC_E].apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
edgar_35 = df_edgar[df_edgar['ipcc_code_2006_for_standard_report']=='3.C.5'][YC_E].apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
dg['EDGAR_direct_GgN2O']   = edgar_34
dg['EDGAR_indirect_GgN2O'] = edgar_35
dg['EDGAR_total_GgN2O']    = edgar_34 + edgar_35
dg.to_csv(OUT_DIR + 'n2o_ms_global.csv', index=False)
print("Saved: n2o_ms_global.csv")

# Components CSV (direct-emission equivalent only, 2019 params)
comp = dg[['Year','FSN_dir_GgN2O','FON_2019_dir_GgN2O',
            'FPRP_2019_dir_GgN2O','FCR_dir_GgN2O','FSOM_GgN2O']].copy()
comp.to_csv(OUT_DIR + 'n2o_ms_components.csv', index=False)
print("Saved: n2o_ms_components.csv")

# =============================================================================
# SECTION 8: VERIFICATION
# =============================================================================
print()
print("=" * 70)
print("VERIFICATION — Our estimates vs FAO Agricultural Soils (Gg N2O)")
print(f"  {'Year':>5}  {'OurNoP_19':>10}  {'FAOnoP':>8}  "
      f"{'OurWiP_19':>10}  {'FAOwiP':>8}  {'Ratio_wiP':>9}")
for _, row in dg[dg['Year'].isin([1970,1980,1990,2000,2010,2020])].iterrows():
    y = int(row['Year'])
    rw = row['Total_withPRP_2019_GgN2O'] / row['FAO_total_GgN2O']
    print(f"  {y:>5}  {row['Total_noPRP_2019_GgN2O']:>10.1f}  "
          f"{row['FAO_noPRP_GgN2O']:>8.1f}  "
          f"{row['Total_withPRP_2019_GgN2O']:>10.1f}  "
          f"{row['FAO_total_GgN2O']:>8.1f}  {rw:>9.3f}")
print()
last = dg[dg['Year']==2020].iloc[0]
print(f"EDGAR 2020: direct={last['EDGAR_direct_GgN2O']:.0f}  "
      f"indirect={last['EDGAR_indirect_GgN2O']:.0f}  "
      f"total={last['EDGAR_total_GgN2O']:.0f}")
print("\nProcessing complete.")
