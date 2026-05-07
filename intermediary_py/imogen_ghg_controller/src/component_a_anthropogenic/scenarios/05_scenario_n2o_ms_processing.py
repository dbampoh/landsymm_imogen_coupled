"""
scenario_n2o_ms_processing.py
===============================
N2O from Managed Soils — scenario 2020-2100.

Five N input components (IPCC Ch.11 Eq. 11.1):
  FSN  — synthetic N fertilizer (from PLUM FertAmount, Mt N)
  FON  — organic N from managed manure applied to soils (from anchored livestock)
  FCR  — N from crop residues returned to field (from PLUM Production, Mt DM)
  FSOM — N from drained organic soils (held at FAO 2020; no future scenario data)
  FPRP — N from pasture/range/paddock excreta (from anchored livestock)

All emission equations identical to the historical n2o_ms_processing.py script.

DATA INPUTS
-----------
  /tmp/plum_crop_s1.csv               — PLUM crop scenario data
  scenario_pipeline/anchored_livestock_2020_2100.csv  — livestock scenarios
  scenario_n2o_synfert_regional.csv   — pre-computed FSN N2O by region
  historical n2o_ms_global.csv        — for FSOM 2020 values

FSN
---
  PLUM FertAmount (Mt N/yr) summed by region, excluding pasture and setaside.
  Identical to scenario_n2o_synfert computation.

FON + FPRP
----------
  Computed from anchored livestock head counts using 2019 Refinement Nex rates
  (Nrate × TAM / 1000 × 365) and AWMS fractions.
  FON  = N from managed (non-PRP, non-burned) manure applied to soils
         = Σ species [ heads × Nex × AWMS_managed_fraction ]
         AWMS_managed = Σ all AWMS columns EXCEPT PRP (index 4) and Burned (index 7)
  FPRP = N deposited on pasture by grazing animals
         = Σ species [ heads × Nex × AWMS_PRP_fraction ]

FCR
---
  PLUM Production (Mt DM) × crop-specific FCR N factor (dimensionless: t N / t DM)
  × calibration scale = 0.4694 (ratio of historical 2020 FCR to raw PLUM 2020 FCR)
  The scale factor corrects for PLUM's broader fruitveg/energycrop categories
  which overestimate residue N relative to historical crop-specific estimates.
  FCR factor formula (from IPCC 2019 Table 11.2):
    N = RAGP × (1 - Frac_remove) × NC_AGR + RBGP × NC_BGR   [t N / t DM grain]

FSOM
----
  Taken from FAO published values (historical n2o_ms script) at 2020 by region.
  Held constant at 2020 level for all scenario years and SSPs.
  Rationale: Tier 1 has no future scenario for drained organic soils; FSOM
  is ~6% of total managed soils N2O (348 Gg out of 6122 Gg in 2020).

EMISSION EQUATIONS (2019 Refinement, same as historical)
---------------------------------------------------------
  Direct:   N2O_dir  = (FSN + FON + FCR + FSOM_kg + FPRP) × EF1 × MW
  Indirect: N2O_vol  = (FSN × FracGASF + FON × FracGASOM + FPRP × FracGASPRP) × EF4 × MW
            N2O_lea  = (FSN + FON + FCR + FPRP) × FracLEACH × EF5 × MW
                       [FracLEACH = 0 for dry climates: Middle East]
  Total     = N2O_dir + N2O_vol + N2O_lea + FSOM_n2o

PARAMETERS (2019 Refinement Table 11.3)
-----------------------------------------
  EF1       = 0.010  kg N2O-N / kg N
  FracGASF  = 0.11   FracGASOM = 0.21  FracGASPRP = 0.21
  EF4       = 0.010  FracLEACH = 0.24 (wet) / 0.00 (dry)  EF5 = 0.011
  MW_N2O    = 44/28
"""


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
    OUT_A_DATA, PLUM_CROP_CSV,
)

import pandas as pd
import numpy as np
import os

# =============================================================================
# SECTION 0: PATHS
# =============================================================================
HERE          = os.path.dirname(os.path.abspath(__file__))
SCEN_PIPE_DIR = os.path.join(str(OUT_A_DATA), 'scenario_pipeline')
HIST_MS_DIR   = os.path.join(str(OUT_A_DATA), 'n2o_ms')
PLUM_CROP     = str(PLUM_CROP_CSV)
PLUM_LIVESTOCK= os.path.join(SCEN_PIPE_DIR, 'anchored_livestock_2020_2100.csv')
os.makedirs(SCEN_PIPE_DIR, exist_ok=True)

SCENARIOS_CROP = ['SSP1_RCP26/s1','SSP2_RCP45/s1','SSP3_RCP70/s1',
                  'SSP4_RCP60/s1','SSP5_RCP85/s1']
SCEN_MAP = {
    'SSP1_RCP26/s1':'SSP1_RCP26_s1','SSP2_RCP45/s1':'SSP2_RCP45_s1',
    'SSP3_RCP70/s1':'SSP3_RCP70_s1','SSP4_RCP60/s1':'SSP4_RCP60_s1',
    'SSP5_RCP85/s1':'SSP5_RCP85_s1',
}
SCENARIOS = list(SCEN_MAP.values())

# =============================================================================
# SECTION 1: IPCC 2019 PARAMETERS
# =============================================================================
EF1         = 0.010
FRACGASF    = 0.11;  FRACGASOM   = 0.21;  FRACGASPRP  = 0.21
EF4         = 0.010
FRACLEACH   = 0.24;  EF5         = 0.011
MW          = 44.0 / 28.0
KG_TO_GG    = 1.0e-6
MT_TO_KG    = 1.0e9    # Mt N → kg N
DRY_REGIONS = {'Middle East'}

R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']

# =============================================================================
# SECTION 2: REGION MAPPING
# =============================================================================
REGION_SETS = {
    'Indian Subcontinent':{'Afghanistan','Bangladesh','Bhutan','India','Maldives',
                           'Nepal','Pakistan','Sri Lanka'},
    'North America':      {'United States of America','Canada','Greenland'},
    'Western Europe':     {'Albania','Andorra','Austria','Belgium','Belgium-Luxembourg',
        'Cyprus','Denmark','Finland','France','France and Monaco','Germany','Greece',
        'Iceland','Ireland','Italy','Italy, San Marino and the Holy See','Luxembourg',
        'Malta','Netherlands','Norway','Portugal','Spain','Spain and Andorra','Sweden',
        'Switzerland','Switzerland and Liechtenstein','United Kingdom','Monaco',
        'San Marino','Liechtenstein'},
    'Eastern Europe':     {'Armenia','Azerbaijan','Belarus','Bosnia and Herzegovina',
        'Bulgaria','Croatia','Czechia','Czech Republic','Estonia','Georgia','Hungary',
        'Kazakhstan','Kyrgyzstan','Latvia','Lithuania','Moldova','Montenegro',
        'North Macedonia','Poland','Romania','Russia','Russian Federation','Serbia',
        'Serbia and Montenegro','Slovakia','Slovenia','Tajikistan','Türkiye','Turkey',
        'Turkmenistan','Ukraine','Uzbekistan','Republic of Moldova'},
    'Oceania':            {'Australia','Cook Islands','Fiji','Kiribati','Marshall Islands',
        'Nauru','New Caledonia','New Zealand','Niue','Palau','Papua New Guinea','Samoa',
        'Solomon Islands','Tonga','Tuvalu','Vanuatu','French Polynesia','Timor-Leste'},
    'Latin America':      {'Antigua and Barbuda','Argentina','Bahamas','Barbados',
        'Belize','Bolivia (Plurinational State of)','Bolivia','Brazil','Chile',
        'Colombia','Costa Rica','Cuba','Dominica','Dominican Republic','Ecuador',
        'El Salvador','Grenada','Guatemala','Guyana','Haiti','Honduras','Jamaica',
        'Mexico','Nicaragua','Panama','Paraguay','Peru','Saint Kitts and Nevis',
        'Saint Lucia','Saint Vincent and the Grenadines','Suriname',
        'Trinidad and Tobago','Uruguay','Venezuela (Bolivarian Republic of)',
        'Venezuela','Puerto Rico','Aruba','Netherlands Antilles','Guadeloupe',
        'Martinique'},
    'Middle East':        {'Bahrain','Egypt','Iran (Islamic Republic of)','Iran','Iraq',
        'Jordan','Kuwait','Lebanon','Libya','Morocco','Oman','Qatar','Saudi Arabia',
        'Syrian Arab Republic','Syria','Tunisia','United Arab Emirates','Yemen',
        'Algeria','Djibouti','Israel','Mauritania','Somalia','Sudan'},
    'Africa':             {'Angola','Benin','Botswana','Burkina Faso','Burundi',
        'Cabo Verde','Cameroon','Central African Republic','Chad','Comoros','Congo',
        "Côte d'Ivoire","Côte d`Ivoire",'Democratic Republic of the Congo',
        'Equatorial Guinea','Eritrea','Eswatini','Ethiopia','Ethiopia PDR','Gabon',
        'Gambia','Ghana','Guinea','Guinea-Bissau','Kenya','Lesotho','Liberia',
        'Madagascar','Malawi','Mali','Mauritius','Mozambique','Namibia','Niger',
        'Nigeria','Rwanda','São Tomé and Príncipe','Sao Tome and Principe','Senegal',
        'Seychelles','Sierra Leone','South Africa','South Sudan','Tanzania','Togo',
        'Uganda','United Republic of Tanzania','Zambia','Zimbabwe','Cape Verde',
        'Réunion','Mayotte'},
    'Asia':               {'Brunei Darussalam','Cambodia','China','China, mainland',
        'China, Hong Kong SAR','China, Macao SAR','China, Taiwan Province of',
        'Indonesia','Japan',"Democratic People's Republic of Korea",'North Korea',
        'Korea, Republic of','South Korea','Republic of Korea',
        "Lao People's Democratic Republic",'Laos','Malaysia','Mongolia','Myanmar',
        'Philippines','Singapore','Thailand','Viet Nam','Vietnam','Hong Kong',
        'Macao','Taiwan'},
}
def get_region(c):
    for r, s in REGION_SETS.items():
        if c in s: return r
    return 'Africa'

PLUM_REGION = {
    'Bahrain & Qatar':'Middle East','Belgium & Luxembourg':'Western Europe',
    'Bolivia':'Latin America','Caribbean Other':'Latin America',
    "Cote dIvoire":'Africa','DR Congo':'Africa','Gabon & Sao Tome':'Africa',
    'Guatemala & Belize':'Latin America','Iran':'Middle East',
    'Italy & Malta':'Western Europe','Laos':'Asia',
    'Madagascar & Indian Ocean':'Africa','Malaysia Singapore & Brunei':'Asia',
    'Moldova':'Eastern Europe','Netherlands':'Western Europe',
    'North Korea':'Asia','Pacific Other':'Oceania','Russia':'Eastern Europe',
    'Senegal Gambia & Cabo Verde':'Africa','South Korea':'Asia',
    'Sri Lanka & Maldives':'Indian Subcontinent','Syria':'Middle East',
    'Taiwan':'Asia','Tanzania':'Africa','Turkiye':'Eastern Europe',
    'United Kingdom':'Western Europe','Venezuela':'Latin America',
}
def plum_region(c): return PLUM_REGION.get(c, get_region(c))

# =============================================================================
# SECTION 3: FCR PARAMETERS (IPCC 2019 Table 11.2)
# =============================================================================
CROP_PARAMS = {
    # (RAGP, Frac_remove, NC_AGR, RBGP, NC_BGR, DM_frac)
    'Wheat':        (1.20, 0.70, 0.006, 0.23, 0.009, 0.87),
    'Rice':         (1.757,0.70, 0.007, 0.16, 0.009, 0.87),
    'Maize':        (1.00, 0.70, 0.006, 0.22, 0.009, 0.87),
    'Roots':        (0.20, 0.00, 0.014, 0.20, 0.014, 0.20),
    'SugarCane':    (0.30, 0.50, 0.004, 0.40, 0.004, 0.26),
    'Pulses':       (1.50, 0.50, 0.019, 0.19, 0.008, 0.87),
    'Soybean':      (1.50, 0.85, 0.008, 0.19, 0.008, 0.87),
    'OilSeeds':     (1.40, 0.85, 0.007, 0.22, 0.009, 0.87),
    'Vegetables':   (0.40, 0.10, 0.019, 0.10, 0.019, 0.10),
    'OtherCereals': (1.40, 0.70, 0.007, 0.22, 0.009, 0.87),
}
# PLUM crop → IPCC crop type for FCR
PLUM_TO_FCR = {
    'wheat':'Wheat','rice':'Rice','maize':'Maize','starchyRoots':'Roots',
    'sugar':'SugarCane','pulses':'Pulses','oilcropsNFix':'Soybean',
    'oilcropsOther':'OilSeeds','fruitveg':'Vegetables','energycrops':'OtherCereals',
    'pasture':None,'setaside':None,
}

def fcr_factor(ipcc_crop):
    """t N residue per t DM grain (dimensionless; same ratio as kg/kg)."""
    R,FR,NCA,RB,NCB,DM = CROP_PARAMS[ipcc_crop]
    return R*(1-FR)*NCA + RB*NCB

FCR_FACTORS = {p: (fcr_factor(i) if i else 0.)
               for p, i in PLUM_TO_FCR.items()}

# Calibration scale: corrects PLUM raw FCR to match historical 2020 FCR
# PLUM 2020 FCR (raw) = 45.035 Mt N; Historical 2020 FCR = 21.139 Mt N
FCR_CALIB_SCALE = 21.139 / 45.035   # = 0.4694

# =============================================================================
# SECTION 4: N EXCRETION PARAMETERS (for FON and FPRP from livestock)
# =============================================================================
def rd(v): return dict(zip(R9,v))

# 2019 Refinement Nrate (kg N / 1000 kg TAM / day) and TAM (kg/head)
NRATE_D19  = rd([0.59,0.54,0.42,0.72,0.39,0.44,0.50,0.44,0.65])
NRATE_O19  = rd([0.40,0.42,0.47,0.46,0.31,0.45,0.56,0.38,0.44])
NRATE_B19  = rd([0.32,0.45,0.35,0.32,0.41,0.42,0.39,0.44,0.58])
NRATE_SW19 = rd([0.39,0.65,0.63,0.54,0.59,0.44,0.66,0.61,0.68])
NRATE_L19  = rd([1.13,0.87,0.81,1.04,1.17,1.20,1.11,1.00,1.65])
NRATE_BR19 = rd([1.59,1.14,1.12,1.59,1.23,1.40,1.43,1.35,1.58])
NRATE_SH19 = rd([0.35,0.36,0.36,0.43,0.32,0.32,0.32,0.32,0.32])
NRATE_GT19 = rd([0.46,0.46,0.44,0.42,0.34,0.34,0.34,0.34,0.34])

TAM_D19  = rd([650,600,550,488,508,260,349,386,285])
TAM_O19  = rd([407,405,389,359,303,236,275,299,226])
TAM_B19  = rd([380,509,467,380,315,339,381,336,321])
TAM_SW19 = rd([77,76,77,61,65,49,59,58,59])
TAM_L19  = rd([1.5,1.9,1.9,2.0,1.4,1.4,1.2,1.5,1.3])
TAM_BR19 = rd([1.4,1.2,1.1,1.2,0.9,0.8,0.7,0.8,0.8])
TAM_SH19 = {r:(40. if r in {'North America','Western Europe','Eastern Europe','Oceania'} else 31.) for r in R9}
TAM_GT19 = rd([41,40,36,33,24,24,24,24,24])

def nex(nrate,tam,r):
    """Annual N excretion: kg N / head / yr."""
    return nrate[r]*tam[r]/1000.*365.

# AWMS fractions: PRP index = 4, Burned index = 7
# FON = manure N going to managed systems applied to soils
#     = Nex × (1 - AWMS_PRP - AWMS_Burned - AWMS_Digester)
# FPRP = Nex × AWMS_PRP

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
AWMS_SG = {
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

def fon_fprp_fracs(awms, has_prp=True, prp_idx=4, burned_idx=7, dig_idx=6):
    """Return (FON_fraction, FPRP_fraction) of total Nex."""
    fprp = awms[prp_idx] if has_prp else 0.
    excl = fprp + awms[burned_idx] + awms[dig_idx]
    fon  = max(0., 1.0 - excl)
    return fon, fprp

# Pre-compute FON/FPRP fractions per species per region
FON_FPRP = {}
for region in R9:
    FON_FPRP[region] = {
        'dairy':   fon_fprp_fracs(AWMS_D[region]),
        'other':   fon_fprp_fracs(AWMS_O[region]),
        'buffalo': fon_fprp_fracs(AWMS_B[region]),
        'swine':   fon_fprp_fracs(AWMS_SW[region], has_prp=False),  # no PRP for swine
        'sheep':   fon_fprp_fracs(AWMS_SG[region]),
        'goat':    fon_fprp_fracs(AWMS_SG[region]),
        'poultry': (1.0, 0.0),   # poultry: all managed, no PRP
    }

NEX = {}
for r in R9:
    NEX[r] = {
        'dairy':  nex(NRATE_D19, TAM_D19, r),
        'other':  nex(NRATE_O19, TAM_O19, r),
        'buffalo':nex(NRATE_B19, TAM_B19, r),
        'swine':  nex(NRATE_SW19,TAM_SW19,r),
        'sheep':  nex(NRATE_SH19,TAM_SH19,r),
        'goat':   nex(NRATE_GT19,TAM_GT19,r),
        'layers': nex(NRATE_L19, TAM_L19, r),
        'broilers':nex(NRATE_BR19,TAM_BR19,r),
    }

# =============================================================================
# SECTION 5: LOAD DATA
# =============================================================================
print("Loading PLUMv2 crop data ...")
df_crop = pd.read_csv(PLUM_CROP, low_memory=False)
df_crop['Region']   = df_crop['Country'].apply(plum_region)
df_crop['Scen_std'] = df_crop['Scenario'].map(SCEN_MAP)

print("Loading anchored livestock data ...")
df_ls = pd.read_csv(PLUM_LIVESTOCK, low_memory=False)
df_ls['Region'] = df_ls['PLUMCountry'].apply(plum_region)

print("Loading FSOM from historical managed soils ...")
hist_ms = pd.read_csv(os.path.join(HIST_MS_DIR,'n2o_ms_regional.csv'))
# Get FSOM 2020 by region from historical (Gg N2O, direct contribution)
# FSOM is stored as FSOM_GgN2O in the historical output
fsom_2020 = hist_ms[hist_ms['Year']==2020].set_index('Region')['FSOM_GgN2O'] \
            if 'FSOM_GgN2O' in hist_ms.columns else pd.Series(dtype=float)
if len(fsom_2020) == 0:
    # FSOM not in regional file; use the global total split equally
    hist_ms_g = pd.read_csv(os.path.join(HIST_MS_DIR,'n2o_ms_global.csv'))
    fsom_global_2020 = hist_ms_g[hist_ms_g['Year']==2020]['FSOM_GgN2O'].values[0]
    # Distribute proportionally using historical regional N2O totals
    reg_totals = hist_ms[hist_ms['Year']==2020].set_index('Region')['Total_withPRP_2019_GgN2O'] \
                 if 'Total_withPRP_2019_GgN2O' in hist_ms.columns else pd.Series({r:1/9 for r in R9})
    fsom_2020 = (reg_totals / reg_totals.sum() * fsom_global_2020)

print(f"  FSOM 2020 global: {fsom_2020.sum():.1f} Gg N2O (held constant in scenarios)")
EXCL_CROPS = {'pasture','setaside'}

# =============================================================================
# SECTION 6: COMPUTE EMISSIONS
# =============================================================================
print("Computing N2O managed soils scenario emissions ...")

records = []

for scen_crop, scen_std in SCEN_MAP.items():
    crop_scen = df_crop[df_crop['Scenario'] == scen_crop]
    ls_scen   = df_ls[df_ls['Scenario'] == scen_std]

    for year in sorted(crop_scen['Year'].unique()):
        crop_yr = crop_scen[crop_scen['Year'] == year]
        ls_yr   = ls_scen[ls_scen['Year'] == year]

        # FSN by region (Mt N)
        fsn_reg = crop_yr[~crop_yr['Crop'].isin(EXCL_CROPS)]\
                    .groupby('Region')['FertAmount'].sum()

        # FCR by region (Mt N, after calibration scaling)
        fcr_parts = []
        for plum_crop, factor in FCR_FACTORS.items():
            if factor == 0.: continue
            sub = crop_yr[crop_yr['Crop']==plum_crop]\
                    .groupby('Region')['Production'].sum() * factor
            fcr_parts.append(sub)
        fcr_reg = pd.concat(fcr_parts).groupby(level=0).sum() * FCR_CALIB_SCALE
        # Convert Mt N → kg N handled inside loop below

        # Livestock pivot: PLUMCountry × region × FAOItem
        ls_wide = ls_yr.pivot_table(
            index=['PLUMCountry','Region'], columns='FAOItem',
            values='Heads_M', aggfunc='sum', fill_value=0.).reset_index()

        for region in R9:
            reg_ls = ls_wide[ls_wide['Region']==region]
            nx  = NEX[region]
            ff  = FON_FPRP[region]

            def cs(col):
                return reg_ls.get(col, pd.Series([0.]*len(reg_ls))).sum()

            da   = cs('Milk whole fresh cow')
            oc   = cs('Meat cattle')
            buf  = cs('Meat buffalo')
            sw   = cs('Meat pig')
            sh   = cs('Meat sheep')   + cs('Milk whole fresh sheep')
            gt   = cs('Meat goat')    + cs('Milk whole fresh goat')
            la   = cs('Eggs Primary')
            br   = cs('Meat Poultry')

            # FON and FPRP (kg N / yr)
            # heads_M × 1e6 heads/M × Nex kg/head/yr × fraction
            def fon_fprp_sp(heads_M, sp):
                total_n = heads_M * 1e6 * nx[sp]
                fon_f, prp_f = ff[sp]
                return total_n * fon_f, total_n * prp_f

            fon_kg = fprp_kg = 0.
            for heads, sp in [(da,'dairy'),(oc,'other'),(buf,'buffalo'),
                               (sw,'swine'),(sh,'sheep'),(gt,'goat')]:
                f, p = fon_fprp_sp(heads, sp)
                fon_kg += f; fprp_kg += p
            # Poultry: all FON, no FPRP
            fon_kg += (la + br) * 1e6 * ((nx['layers']*la + nx['broilers']*br) /
                                          max(la+br, 1e-9))

            # FSN and FCR in kg N
            fsn_kg  = fsn_reg.get(region, 0.) * MT_TO_KG
            fcr_kg  = fcr_reg.get(region, 0.) * MT_TO_KG

            # FSOM (Gg N2O, constant at 2020)
            fsom_gg = fsom_2020.get(region, 0.)

            # FSOM as effective kg N (for direct eq.) — back-calculate
            # N2O_fsom = FSOM_kgN × EF1 × MW → FSOM_kgN = FSOM_GgN2O / (EF1 × MW × KG_TO_GG)
            fsom_kg = fsom_gg / (EF1 * MW * KG_TO_GG)

            wet = region not in DRY_REGIONS

            # Direct N2O (Gg)
            n2o_dir = (fsn_kg + fon_kg + fcr_kg + fsom_kg + fprp_kg) * EF1 * MW * KG_TO_GG

            # Indirect — volatilisation (Gg)
            n2o_vol = (fsn_kg*FRACGASF + fon_kg*FRACGASOM + fprp_kg*FRACGASPRP) * EF4 * MW * KG_TO_GG

            # Indirect — leaching (Gg; zero if dry)
            frac_l  = FRACLEACH if wet else 0.
            n2o_lea = (fsn_kg + fon_kg + fcr_kg + fprp_kg) * frac_l * EF5 * MW * KG_TO_GG

            n2o_tot = n2o_dir + n2o_vol + n2o_lea

            records.append({
                'Scenario':  scen_std,'Year':year,'Region':region,
                'FSN_MtN':   round(fsn_reg.get(region,0.),6),
                'FON_kgN':   round(fon_kg,2),
                'FCR_MtN':   round(fcr_reg.get(region,0.),6),
                'FPRP_kgN':  round(fprp_kg,2),
                'FSOM_GgN2O':round(fsom_gg,4),
                'N2O_direct_GgN2O':  round(n2o_dir,4),
                'N2O_vol_GgN2O':     round(n2o_vol,4),
                'N2O_leach_GgN2O':   round(n2o_lea,4),
                'N2O_total_GgN2O':   round(n2o_tot,4),
            })

df_out = pd.DataFrame(records)
print(f"  {len(df_out):,} records computed")

# Save
df_out.to_csv(os.path.join(SCEN_PIPE_DIR,'scenario_n2o_ms_regional.csv'), index=False)

gcols = ['N2O_direct_GgN2O','N2O_vol_GgN2O','N2O_leach_GgN2O','N2O_total_GgN2O',
         'FSN_MtN','FON_kgN','FCR_MtN','FPRP_kgN','FSOM_GgN2O']
g = df_out.groupby(['Scenario','Year'])[gcols].sum().reset_index()
g.to_csv(os.path.join(SCEN_PIPE_DIR,'scenario_n2o_ms_global.csv'), index=False)

print("Saved: scenario_n2o_ms_regional.csv")
print("Saved: scenario_n2o_ms_global.csv")

# =============================================================================
# SECTION 7: VERIFICATION
# =============================================================================
print()
print("=== Verification: 2020 global totals ===")
g2020 = g[g['Year']==2020]
for _, r in g2020.iterrows():
    print(f"  {r['Scenario']}: {r['N2O_total_GgN2O']:.1f} Gg N2O  "
          f"(dir={r['N2O_direct_GgN2O']:.1f} vol={r['N2O_vol_GgN2O']:.1f} "
          f"lea={r['N2O_leach_GgN2O']:.1f}  FSOM={r['FSOM_GgN2O']:.1f})")
print(f"\n  Historical 2020 ref (2019 params, with PRP): 6122 Gg N2O")
print(f"  FAO 2020: 6997 Gg N2O")

print()
print("=== Scenario trajectories — N2O total (Gg N2O) ===")
for yr in [2030, 2050, 2075, 2100]:
    row = g[g['Year']==yr]
    vals = '  '.join(f"{r['Scenario'][:13]}={r['N2O_total_GgN2O']:.0f}"
                     for _, r in row.iterrows())
    print(f"  {yr}: {vals}")
print("\nDone.")
