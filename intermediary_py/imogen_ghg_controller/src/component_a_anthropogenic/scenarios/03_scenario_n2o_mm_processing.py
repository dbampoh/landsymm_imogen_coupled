"""
03_scenario_n2o_mm.py  —  N2O Manure Management, scenario 2020-2100
=====================================================================
Applies identical IPCC 2019 Refinement Tier 1 parameters to the historical
n2o_mm_processing.py (supplement version). Uses climate-zone-indexed EF3
tables and species-specific AWMS/FG fractions.

IPCC equation (Ch.10 Eq.10.25):
  N2O_direct   = Σ_T Σ_S [N_T × AWMS_TS × EF3_S] × (44/28)
  N2O_indirect = Σ_T Σ_S [N_T × AWMS_TS × FG_S × EF4] × (44/28)
  Total        = N2O_direct + N2O_indirect

where:
  N_T  = annual N excreted by species T (kg N/yr) = heads × Nex_T
  Nex  = Nrate (kg N / 1000 kg TAM / day) × TAM / 1000 × 365
  EF3  = emission factor per MMS (kg N2O-N / kg N)
  FG   = fractional gas loss (volatilisation) per MMS
  EF4  = 0.010 kg N2O-N / kg N volatilised (all climates)

PLUM item → livestock mapping:
  'Milk whole fresh cow'   → dairy cattle
  'Meat cattle'            → other (non-dairy) cattle
  'Meat buffalo'           → buffalo
  'Meat pig'               → swine (2019 params)
  'Meat sheep' + milk      → sheep
  'Meat goat'  + milk      → goats
  'Eggs Primary'           → laying hens (2019 Nrate/TAM)
  'Meat Poultry'           → broilers + other poultry (2019 Nrate/TAM)

Missing species (horses/mules/asses): excluded — negligible N2O MM contribution.

OUTPUT
------
  scenario_n2o_mm_global.csv    — 5 scenarios × 81 years
  scenario_n2o_mm_regional.csv  — 5 scenarios × 81 years × 9 regions
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
    OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
)

import pandas as pd
import numpy as np

# =============================================================================
# SECTION 0: PATHS AND CONSTANTS
# =============================================================================
SCEN_DIR  = (str(OUT_A_DATA) + '/scenario_pipeline/')
os.makedirs(SCEN_DIR, exist_ok=True)
SCENARIOS = ['SSP1_RCP26_s1','SSP2_RCP45_s1','SSP3_RCP70_s1',
             'SSP4_RCP60_s1','SSP5_RCP85_s1']
KG_TO_GG  = 1e-6
MW_N2O    = 44. / 28.
EF4       = 0.010     # indirect (volatilisation) EF — all climates

R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']
DEVELOPED = {'North America','Western Europe','Eastern Europe','Oceania'}

# =============================================================================
# SECTION 1: EF3 TABLES (kg N2O-N / kg N in MMS)
# Table 10.21, IPCC 2019 Refinement — column order matches AWMS
# Cattle/buffalo: [Lagoon, Slurry, Solid, Drylot, PRP, Daily, Digester, Burned, Other]
# Swine same column order (PRP index unused — no swine PRP)
# =============================================================================
EF3_CAT19 = [0.000, 0.005, 0.010, 0.020, 0.000, 0.000, 0.0006, 0.000, 0.010]
EF3_SW19  = [0.000, 0.005, 0.010, 0.020, 0.002, 0.002, 0.000,  0.0006, 0.010]
EF3_SG19  = [0.000, 0.000, 0.010, 0.020, 0.000, 0.000, 0.000,  0.000,  0.010]
EF3_POUL  = 0.001     # poultry: single EF (kg N2O-N / kg N, all MMS)
FG_POUL   = 0.40      # poultry volatilisation fraction

# =============================================================================
# SECTION 2: FG (VOLATILISATION FRACTION) — Table 10.22 / 10A
# Same column order as AWMS.  FG_S = fraction of manure N volatilised in MMS S.
# =============================================================================
FG_D19  = [0.35, 0.39, 0.14, 0.20, 0.00, 0.07, 0.00, 0.00, 0.14]
FG_O19  = [0.35, 0.39, 0.17, 0.30, 0.00, 0.07, 0.00, 0.00, 0.17]
FG_B19  = FG_O19
FG_SW19 = [0.40, 0.48, 0.22, 0.20, 0.25, 0.25, 0.00, 0.00, 0.22]
FG_SG19 = [0.35, 0.35, 0.12, 0.12, 0.00, 0.07, 0.00, 0.00, 0.12]

# =============================================================================
# SECTION 3: AWMS FRACTIONS (Tables 10A.4–10A.9)
# =============================================================================
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

# =============================================================================
# SECTION 4: N EXCRETION RATES AND TAM (2019 REFINEMENT)
# Nrate: kg N / 1000 kg TAM / day  (Table 10.19)
# TAM:   kg / head                 (Table 10A.2)
# Nex (kg N / head / yr) = Nrate × TAM / 1000 × 365
# =============================================================================
def rd(v): return dict(zip(R9, v))

# 2019 Refinement values (used as primary for scenario projections)
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
TAM_SW19 = rd([77, 76, 77, 61, 65, 49, 59, 58, 59])
TAM_L19  = rd([1.5,1.9,1.9,2.0,1.4,1.4,1.2,1.5,1.3])
TAM_BR19 = rd([1.4,1.2,1.1,1.2,0.9,0.8,0.7,0.8,0.8])
TAM_SH19 = {r:(40.0 if r in DEVELOPED else 31.0) for r in R9}
TAM_GT19 = rd([41, 40, 36, 33, 24, 24, 24, 24, 24])

def nex(nrate, tam, r):
    """Annual N excretion: kg N / head / yr"""
    return nrate[r] * tam[r] / 1000. * 365.

# =============================================================================
# SECTION 5: CORE N2O COMPUTATION FUNCTION
# =============================================================================
def n2o_mm(heads_M, Nex_kgN_per_head, awms, ef3, fg):
    """
    N2O from manure management for one species-region combination.

    Parameters
    ----------
    heads_M : float — livestock head count in millions
    Nex_kgN_per_head : float — annual N excretion (kg N/head/yr)
    awms : list[float] — AWMS fractions (9 MMS systems)
    ef3  : list[float] — EF3 per MMS (kg N2O-N / kg N)
    fg   : list[float] — FG (volatilisation fraction) per MMS

    Returns
    -------
    (direct_GgN2O, indirect_GgN2O)
    """
    total_N = heads_M * 1e6 * Nex_kgN_per_head   # kg N / yr
    direct = indirect = 0.
    for i, frac in enumerate(awms):
        if frac <= 0.: continue
        manure_N_mms = total_N * frac              # kg N in this MMS
        direct   += manure_N_mms * ef3[i] * MW_N2O
        indirect += manure_N_mms * fg[i]  * EF4   * MW_N2O
    return direct * KG_TO_GG, indirect * KG_TO_GG

def n2o_poultry(heads_M, Nex_kgN_per_head):
    """Poultry N2O: single EF3 and FG (not MMS-indexed)."""
    total_N = heads_M * 1e6 * Nex_kgN_per_head
    direct   = total_N * EF3_POUL  * MW_N2O * KG_TO_GG
    indirect = total_N * FG_POUL   * EF4 * MW_N2O * KG_TO_GG
    return direct, indirect

# =============================================================================
# SECTION 6: REGION MAPPING
# =============================================================================
REGION_SETS = {
    'Indian Subcontinent':{'Afghanistan','Bangladesh','Bhutan','India','Maldives',
                           'Nepal','Pakistan','Sri Lanka'},
    'North America':      {'United States of America','Canada','Greenland',
                           'Saint Pierre and Miquelon'},
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
        'Turkmenistan','Ukraine','Uzbekistan','Kosovo','Republic of Moldova'},
    'Oceania':            {'Australia','Cook Islands','Fiji','Kiribati','Marshall Islands',
        'Nauru','New Caledonia','New Zealand','Niue','Palau','Papua New Guinea','Samoa',
        'Solomon Islands','Tonga','Tuvalu','Vanuatu','French Polynesia','Timor-Leste'},
    'Latin America':      {'Antigua and Barbuda','Argentina','Bahamas','Barbados',
        'Belize','Bolivia (Plurinational State of)','Bolivia','Brazil','Chile','Colombia',
        'Costa Rica','Cuba','Dominica','Dominican Republic','Ecuador','El Salvador',
        'Grenada','Guatemala','Guyana','Haiti','Honduras','Jamaica','Mexico',
        'Nicaragua','Panama','Paraguay','Peru','Saint Kitts and Nevis','Saint Lucia',
        'Saint Vincent and the Grenadines','Suriname','Trinidad and Tobago','Uruguay',
        'Venezuela (Bolivarian Republic of)','Venezuela','Puerto Rico','Aruba',
        'Netherlands Antilles','Guadeloupe','Martinique'},
    'Middle East':        {'Bahrain','Egypt','Iran (Islamic Republic of)','Iran','Iraq',
        'Jordan','Kuwait','Lebanon','Libya','Morocco','Oman','Qatar','Saudi Arabia',
        'Syrian Arab Republic','Syria','Tunisia','United Arab Emirates','Yemen','Algeria',
        'Djibouti','Israel','Mauritania','Somalia','Sudan','Sudan and South Sudan'},
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
        'Myanmar/Burma','Philippines','Singapore','Thailand','Viet Nam','Vietnam',
        'Hong Kong','Macao','Taiwan'},
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
# SECTION 7: PRE-COMPUTE PER-REGION EMISSION FACTORS
# (constant — IPCC parameters don't change with scenario year)
# =============================================================================
print("Pre-computing N2O MM emission factors (2019 params) ...")

# For each region: compute effective EF_total (kg N2O / kg N excreted)
# = Σ_S AWMS_S × (EF3_S × MW_N2O + FG_S × EF4 × MW_N2O)
# This allows quick emission = heads_M × 1e6 × Nex × EF_total × KG_TO_GG

def eff_ef(awms, ef3, fg):
    """Effective N2O emission factor: kg N2O per kg N excreted."""
    return sum(awms[i] * (ef3[i] * MW_N2O + fg[i] * EF4 * MW_N2O)
               for i in range(9) if awms[i] > 0)

EF_TABLE = {}
for r in R9:
    EF_TABLE[r] = {
        'dairy':   eff_ef(AWMS_D[r],  EF3_CAT19, FG_D19),
        'other':   eff_ef(AWMS_O[r],  EF3_CAT19, FG_O19),
        'buffalo': eff_ef(AWMS_B[r],  EF3_CAT19, FG_B19),
        'swine':   eff_ef(AWMS_SW[r], EF3_SW19,  FG_SW19),
        'sheep':   eff_ef(AWMS_SG[r], EF3_SG19,  FG_SG19),
        'goat':    eff_ef(AWMS_SG[r], EF3_SG19,  FG_SG19),
        # Poultry: single EF3 + FG (not MMS-indexed)
        'poultry': (EF3_POUL + FG_POUL * EF4) * MW_N2O,
    }

# Pre-compute annual Nex per region (kg N / head / yr)
NEX = {}
for r in R9:
    NEX[r] = {
        'dairy':  nex(NRATE_D19,  TAM_D19,  r),
        'other':  nex(NRATE_O19,  TAM_O19,  r),
        'buffalo':nex(NRATE_B19,  TAM_B19,  r),
        'swine':  nex(NRATE_SW19, TAM_SW19, r),
        'sheep':  nex(NRATE_SH19, TAM_SH19, r),
        'goat':   nex(NRATE_GT19, TAM_GT19, r),
        'layers': nex(NRATE_L19,  TAM_L19,  r),
        'broilers':nex(NRATE_BR19, TAM_BR19, r),
    }

# Spot-check
print(f"  Nex dairy NA: {NEX['North America']['dairy']:.2f} kg N/head/yr")
print(f"  Nex swine Asia: {NEX['Asia']['swine']:.2f} kg N/head/yr")
print(f"  EF dairy IndSub: {EF_TABLE['Indian Subcontinent']['dairy']:.5f} kg N2O/kg N")

# =============================================================================
# SECTION 8: LOAD DATA AND COMPUTE EMISSIONS
# =============================================================================
print("\nLoading anchored livestock data ...")
df = pd.read_csv(SCEN_DIR + 'anchored_livestock_2020_2100.csv')
df['Region'] = df['PLUMCountry'].apply(plum_region)

# Helper: column sum with missing-column safety
def cs(wide, col):
    return wide.get(col, pd.Series([0.]*len(wide))).sum()

def gg_species(heads_M, nex_val, ef_val):
    """N2O (Gg) = M heads × 1e6 × Nex (kg N/head/yr) × EF (kg N2O/kg N) × 1e-6"""
    return heads_M * nex_val * ef_val  # M heads × kg N/head/yr × kg N2O/kg N = M kg N2O/yr = Gg

print("Computing N2O MM scenario emissions ...")
records = []

for scen in SCENARIOS:
    sdf = df[df['Scenario'] == scen]
    for year in sorted(sdf['Year'].unique()):
        wide = sdf[sdf['Year'] == year].pivot_table(
            index=['PLUMCountry','Region'], columns='FAOItem',
            values='Heads_M', aggfunc='sum', fill_value=0.
        ).reset_index()

        for region in R9:
            reg  = wide[wide['Region'] == region]
            if not len(reg): continue
            ef   = EF_TABLE[region]
            nx   = NEX[region]

            da   = cs(reg, 'Milk whole fresh cow')
            oc   = cs(reg, 'Meat cattle')
            buf  = cs(reg, 'Meat buffalo')
            sw   = cs(reg, 'Meat pig')
            sh   = cs(reg, 'Meat sheep') + cs(reg, 'Milk whole fresh sheep')
            gt   = cs(reg, 'Meat goat')  + cs(reg, 'Milk whole fresh goat')
            la   = cs(reg, 'Eggs Primary')    # layer hens
            br   = cs(reg, 'Meat Poultry')    # broilers + other poultry

            n2o_gg = (gg_species(da,  nx['dairy'],   ef['dairy'])  +
                      gg_species(oc,  nx['other'],   ef['other'])  +
                      gg_species(buf, nx['buffalo'],  ef['buffalo'])+
                      gg_species(sw,  nx['swine'],   ef['swine'])  +
                      gg_species(sh,  nx['sheep'],   ef['sheep'])  +
                      gg_species(gt,  nx['goat'],    ef['goat'])   +
                      gg_species(la,  nx['layers'],  ef['poultry'])+
                      gg_species(br,  nx['broilers'],ef['poultry']))

            records.append({'Scenario': scen, 'Year': year, 'Region': region,
                            'N2O_GgN2O': round(n2o_gg, 6)})

df_out = pd.DataFrame(records)
df_out.to_csv(SCEN_DIR + 'scenario_n2o_mm_regional.csv', index=False)
g = df_out.groupby(['Scenario','Year'])['N2O_GgN2O'].sum().reset_index()
g.to_csv(SCEN_DIR + 'scenario_n2o_mm_global.csv', index=False)
print("Saved: scenario_n2o_mm_regional.csv  scenario_n2o_mm_global.csv")

# =============================================================================
# SECTION 9: VERIFICATION
# =============================================================================
print()
print("=== Verification: 2020 global totals ===")
for _, r in g[g['Year'] == 2020].iterrows():
    print(f"  {r['Scenario']}: {r['N2O_GgN2O']:.2f} Gg N2O")
print(f"  Historical ref: FAO=447 Gg  |  Our Tier1 (2006-split)=633 Gg")
print()
print("=== Scenario trajectories (global, Gg N2O) ===")
for yr in [2030, 2050, 2075, 2100]:
    row = g[g['Year'] == yr]
    vals = '  '.join(f"{r['Scenario'][:13]}={r['N2O_GgN2O']:.1f}"
                     for _, r in row.iterrows())
    print(f"  {yr}: {vals}")
print("\nDone.")
