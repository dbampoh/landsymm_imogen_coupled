"""
02_scenario_ch4_mm.py  —  CH4 Manure Management, scenario 2020-2100
=====================================================================
Uses identical IPCC 2019 Tier 1 parameters to the historical script:
- Climate-zone-indexed MCF tables (Table 10.17)
- Species-specific AWMS fractions (Tables 10A.4-10A.9)
- VS rates and TAM per species and region (Tables 10.13A, 10A.2)
Activity data: anchored_livestock_2020_2100.csv
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
import os  # [Step 11 of unified-codebase rebuild: bug fix - os used without import. - DKB 2026-05-07]

SCEN_DIR  = (str(OUT_A_DATA) + '/scenario_pipeline/')
os.makedirs(SCEN_DIR, exist_ok=True)
SCENARIOS = ['SSP1_RCP26_s1','SSP2_RCP45_s1','SSP3_RCP70_s1',
             'SSP4_RCP60_s1','SSP5_RCP85_s1']
R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']

# ── Climate zone mapping (same as historical script) ────────────────────────
REGION_TO_CLIMATE = {
    'North America':'Cool Temperate Moist','Western Europe':'Cool Temperate Moist',
    'Eastern Europe':'Cool Temperate Moist','Oceania':'Warm Temperate Moist',
    'Latin America':'Tropical Moist','Africa':'Tropical Moist',
    'Middle East':'Warm Temperate Dry','Asia':'Warm Temperate Moist',
    'Indian Subcontinent':'Tropical Moist',
}

# ── MCF tables (Table 10.17) ─────────────────────────────────────────────────
MCF_LAGOON     = {'Cool Temperate Moist':0.60,'Cool Temperate Dry':0.67,
                  'Boreal Moist':0.50,'Boreal Dry':0.49,'Warm Temperate Moist':0.73,
                  'Warm Temperate Dry':0.76,'Tropical Montane':0.76,'Tropical Wet':0.80,
                  'Tropical Moist':0.80,'Tropical Dry':0.80}
MCF_LIQUID_6MO = {'Cool Temperate Moist':0.21,'Cool Temperate Dry':0.26,
                  'Boreal Moist':0.14,'Boreal Dry':0.14,'Warm Temperate Moist':0.37,
                  'Warm Temperate Dry':0.41,'Tropical Montane':0.59,'Tropical Wet':0.76,
                  'Tropical Moist':0.73,'Tropical Dry':0.74}
MCF_SOLID      = {'Cool Temperate Moist':0.020,'Cool Temperate Dry':0.020,
                  'Boreal Moist':0.020,'Boreal Dry':0.020,'Warm Temperate Moist':0.040,
                  'Warm Temperate Dry':0.040,'Tropical Montane':0.050,'Tropical Wet':0.050,
                  'Tropical Moist':0.050,'Tropical Dry':0.050}
MCF_DRYLOT     = {'Cool Temperate Moist':0.010,'Cool Temperate Dry':0.010,
                  'Boreal Moist':0.010,'Boreal Dry':0.010,'Warm Temperate Moist':0.015,
                  'Warm Temperate Dry':0.015,'Tropical Montane':0.020,'Tropical Wet':0.020,
                  'Tropical Moist':0.020,'Tropical Dry':0.020}
MCF_DAILY      = {'Cool Temperate Moist':0.001,'Cool Temperate Dry':0.001,
                  'Boreal Moist':0.001,'Boreal Dry':0.001,'Warm Temperate Moist':0.005,
                  'Warm Temperate Dry':0.005,'Tropical Montane':0.010,'Tropical Wet':0.010,
                  'Tropical Moist':0.010,'Tropical Dry':0.010}
MCF_PIT_LT1   = {'Cool Temperate Moist':0.0275,'Cool Temperate Dry':0.0275,
                  'Boreal Moist':0.0275,'Boreal Dry':0.0275,'Warm Temperate Moist':0.065,
                  'Warm Temperate Dry':0.065,'Tropical Montane':0.18,'Tropical Wet':0.18,
                  'Tropical Moist':0.18,'Tropical Dry':0.18}
MCF_POULTRY    = {cz:0.015 for cz in MCF_SOLID}
MCF_PRP        = {cz:0.0047 for cz in MCF_SOLID}
MCF_BURNED     = {cz:0.10  for cz in MCF_SOLID}
MCF_DIGESTER   = {cz:0.0   for cz in MCF_SOLID}

# MCF map lists (indexed by AWMS column position)
# Cattle/buffalo: [Lagoon, Slurry, Solid, Drylot, PRP, Daily, Digester, Burned, Other]
CATTLE_MCF = [MCF_LAGOON,MCF_LIQUID_6MO,MCF_SOLID,MCF_DRYLOT,
              MCF_PRP,MCF_DAILY,MCF_DIGESTER,MCF_BURNED,MCF_SOLID]
# Swine: [Lagoon, Slurry, Solid, Drylot, Pit<1mo, Pit>1mo, Daily, Digester, Other]
SWINE_MCF  = [MCF_LAGOON,MCF_LIQUID_6MO,MCF_SOLID,MCF_DRYLOT,
              MCF_PIT_LT1,MCF_LIQUID_6MO,MCF_DAILY,MCF_DIGESTER,MCF_SOLID]
SHEEP_MCF  = CATTLE_MCF[:]

# ── Species parameters (Tables 10.13A, 10A.2, 10.16A) ──────────────────────
def rd(v): return dict(zip(R9,v))

# VS rates (kg VS / 1000 kg TAM / day) — IPCC 2019 Refinement Table 10.13A
VS_D   = rd([9.2, 8.4, 6.7, 6.0, 7.9,18.2,10.7, 9.0,14.1])  # dairy cattle
VS_O   = rd([7.6, 5.7, 7.6, 8.7, 8.5,12.1,12.3, 9.8,12.2])  # other cattle
VS_B   = rd([11.0,7.7, 6.2,11.0,11.2,12.9,13.5,13.5,15.2])  # buffalo
VS_SW  = rd([3.3, 4.5, 4.0, 4.0, 5.0, 7.2, 5.8, 4.3, 7.7])  # swine
VS_SH  = {r:(8.2 if r in {'North America','Western Europe','Eastern Europe','Oceania'} else 8.3) for r in R9}
VS_GT  = {r:(9.0 if r in {'North America','Western Europe','Eastern Europe','Oceania'} else 10.4) for r in R9}
VS_L   = rd([9.4, 8.6, 9.4, 8.6,10.1,10.2, 9.0, 9.3,13.2])  # layers
VS_BR  = rd([16.8,16.1,16.0,18.3,15.6,15.9,17.7,15.7,17.7])  # broilers
VS_TK  = {r:10.3 for r in R9}   # turkeys (all regions)
VS_DK  = {r:7.4  for r in R9}   # ducks (all regions)

# TAM (kg/head) — IPCC 2019 Refinement Table 10A.2 / 10A.5
_dev = {'North America','Western Europe','Eastern Europe','Oceania'}
TAM_D  = rd([650,600,550,488,508,260,349,386,285])
TAM_O  = rd([407,405,389,359,303,236,275,299,226])
TAM_B  = rd([380,509,467,380,315,339,381,336,321])
TAM_SW = rd([77, 76, 77, 61, 65, 49, 59, 58, 59])
TAM_SH = {r:(40. if r in _dev else 31.) for r in R9}
TAM_GT = rd([41, 40, 36, 33, 24, 24, 24, 24, 24])
TAM_L  = rd([1.5,1.9,1.9,2.0,1.4,1.4,1.2,1.5,1.3])
TAM_BR = rd([1.4,1.2,1.1,1.2,0.9,0.8,0.7,0.8,0.8])
TAM_TK = {r:6.8 for r in R9}
TAM_DK = {r:2.7 for r in R9}

B0_D   = {r:0.24 for r in R9}
B0_O   = {r:0.24 for r in R9}
B0_B   = {r:0.10 for r in R9}
B0_SW  = rd([0.45,0.45,0.45,0.45,0.29,0.29,0.29,0.45,0.45])
B0_SG  = {r:0.19 for r in R9}
B0_PL  = {r:0.39 for r in R9}

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

# ── EF function (identical to historical) ────────────────────────────────────
def compute_EF(vs_rate, tam, b0, awms, mcf_map, cz, prp_idx=4):
    """kg CH4 / head / yr. PRP uses B0=0.19 (Table 10.17 footnote 2)."""
    vs_head = vs_rate * tam / 1000.0
    sigma = ef_prp = 0.0
    for i, frac in enumerate(awms):
        if frac <= 0.: continue
        mcf = mcf_map[i][cz]
        if i == prp_idx:
            ef_prp = vs_head * 365. * 0.19 * 0.67 * frac * mcf
        else:
            sigma += frac * mcf
    return vs_head * 365. * b0 * 0.67 * sigma + ef_prp

# ── Region mapping ────────────────────────────────────────────────────────────
REGION_SETS = {
    'Indian Subcontinent':{'Afghanistan','Bangladesh','Bhutan','India','Maldives','Nepal','Pakistan','Sri Lanka'},
    'North America':{'United States of America','Canada','Greenland','Saint Pierre and Miquelon'},
    'Western Europe':{'Albania','Andorra','Austria','Belgium','Belgium-Luxembourg','Cyprus','Denmark',
        'Finland','France','France and Monaco','Germany','Greece','Iceland','Ireland',
        'Italy','Italy, San Marino and the Holy See','Luxembourg','Malta','Netherlands',
        'Norway','Portugal','Spain','Spain and Andorra','Sweden','Switzerland',
        'Switzerland and Liechtenstein','United Kingdom','Monaco','San Marino','Liechtenstein'},
    'Eastern Europe':{'Armenia','Azerbaijan','Belarus','Bosnia and Herzegovina','Bulgaria','Croatia',
        'Czechia','Czech Republic','Estonia','Georgia','Hungary','Kazakhstan','Kyrgyzstan',
        'Latvia','Lithuania','Moldova','Montenegro','North Macedonia','Poland','Romania',
        'Russia','Russian Federation','Serbia','Serbia and Montenegro','Slovakia','Slovenia',
        'Tajikistan','Türkiye','Turkey','Turkmenistan','Ukraine','Uzbekistan','Republic of Moldova'},
    'Oceania':{'Australia','Cook Islands','Fiji','Kiribati','Marshall Islands','Nauru',
        'New Caledonia','New Zealand','Niue','Palau','Papua New Guinea','Samoa',
        'Solomon Islands','Tonga','Tuvalu','Vanuatu','French Polynesia','Timor-Leste'},
    'Latin America':{'Antigua and Barbuda','Argentina','Bahamas','Barbados','Belize',
        'Bolivia (Plurinational State of)','Bolivia','Brazil','Chile','Colombia','Costa Rica',
        'Cuba','Dominica','Dominican Republic','Ecuador','El Salvador','Grenada','Guatemala',
        'Guyana','Haiti','Honduras','Jamaica','Mexico','Nicaragua','Panama','Paraguay','Peru',
        'Saint Kitts and Nevis','Saint Lucia','Saint Vincent and the Grenadines','Suriname',
        'Trinidad and Tobago','Uruguay','Venezuela (Bolivarian Republic of)','Venezuela',
        'Puerto Rico','Aruba','Netherlands Antilles','Guadeloupe','Martinique'},
    'Middle East':{'Bahrain','Egypt','Iran (Islamic Republic of)','Iran','Iraq','Jordan','Kuwait',
        'Lebanon','Libya','Morocco','Oman','Qatar','Saudi Arabia','Syrian Arab Republic','Syria',
        'Tunisia','United Arab Emirates','Yemen','Algeria','Djibouti','Israel','Mauritania',
        'Somalia','Sudan','Sudan and South Sudan'},
    'Africa':{'Angola','Benin','Botswana','Burkina Faso','Burundi','Cabo Verde','Cameroon',
        'Central African Republic','Chad','Comoros','Congo',"Côte d'Ivoire","Côte d`Ivoire",
        'Democratic Republic of the Congo','Equatorial Guinea','Eritrea','Eswatini','Ethiopia',
        'Ethiopia PDR','Gabon','Gambia','Ghana','Guinea','Guinea-Bissau','Kenya','Lesotho',
        'Liberia','Madagascar','Malawi','Mali','Mauritius','Mozambique','Namibia','Niger',
        'Nigeria','Rwanda','São Tomé and Príncipe','Sao Tome and Principe','Senegal',
        'Seychelles','Sierra Leone','South Africa','South Sudan','Tanzania','Togo','Uganda',
        'United Republic of Tanzania','Zambia','Zimbabwe','Cape Verde','Réunion','Mayotte'},
    'Asia':{'Brunei Darussalam','Cambodia','China','China, mainland','China, Hong Kong SAR',
        'China, Macao SAR','China, Taiwan Province of','Indonesia','Japan',
        "Democratic People's Republic of Korea",'North Korea','Korea, Republic of',
        'South Korea','Republic of Korea',"Lao People's Democratic Republic",'Laos',
        'Malaysia','Mongolia','Myanmar','Myanmar/Burma','Philippines','Singapore',
        'Thailand','Timor-Leste','Viet Nam','Vietnam','Hong Kong','Macao','Taiwan'},
}
def get_region(c):
    for r,s in REGION_SETS.items():
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

# ── Pre-compute EF per region (constant — IPCC parameters don't change) ──────
print("Pre-computing emission factors ...")
EF = {}
for r in R9:
    cz = REGION_TO_CLIMATE[r]
    EF[r] = {
        'd':  compute_EF(VS_D[r], TAM_D[r],  B0_D[r],  AWMS_D[r],  CATTLE_MCF, cz),
        'o':  compute_EF(VS_O[r], TAM_O[r],  B0_O[r],  AWMS_O[r],  CATTLE_MCF, cz),
        'b':  compute_EF(VS_B[r], TAM_B[r],  B0_B[r],  AWMS_B[r],  CATTLE_MCF, cz),
        'sw': compute_EF(VS_SW[r],TAM_SW[r], B0_SW[r], AWMS_SW[r], SWINE_MCF,  cz, prp_idx=99),
        'sh': compute_EF(VS_SH[r],TAM_SH[r], B0_SG[r], AWMS_SG[r], SHEEP_MCF,  cz),
        'gt': compute_EF(VS_GT[r],TAM_GT[r], B0_SG[r], AWMS_SG[r], SHEEP_MCF,  cz),
        'la': (VS_L[r] *TAM_L[r] /1000.)*365.*B0_PL[r]*0.67*0.015,
        'br': (VS_BR[r]*TAM_BR[r]/1000.)*365.*B0_PL[r]*0.67*0.015,
        'tk': (VS_TK[r]*TAM_TK[r]/1000.)*365.*B0_PL[r]*0.67*0.015,
        'dk': (VS_DK[r]*TAM_DK[r]/1000.)*365.*B0_PL[r]*0.67*0.015,
    }

# Spot check
for r in ['North America','Indian Subcontinent','Asia']:
    print(f"  {r}: dairy={EF[r]['d']:.2f}  swine={EF[r]['sw']:.2f}  layer={EF[r]['la']:.4f}  kg CH4/head/yr")

# ── Load data ─────────────────────────────────────────────────────────────────
print("\nLoading anchored livestock ...")
df = pd.read_csv(SCEN_DIR+'anchored_livestock_2020_2100.csv')
df['Region'] = df['PLUMCountry'].apply(plum_region)

# Helper: column sum with missing-column safety
def cs(wide, col): return wide.get(col, pd.Series([0.]*len(wide))).sum()

# ── Compute emissions ─────────────────────────────────────────────────────────
print("Computing CH4 MM scenario emissions ...")
records = []
for scen in SCENARIOS:
    sdf = df[df['Scenario']==scen]
    for year in sorted(sdf['Year'].unique()):
        wide = sdf[sdf['Year']==year].pivot_table(
            index=['PLUMCountry','Region'], columns='FAOItem',
            values='Heads_M', aggfunc='sum', fill_value=0.).reset_index()
        for region in R9:
            reg = wide[wide['Region']==region]
            if not len(reg): continue
            ef = EF[region]
            # Heads (M): dairy/other cattle, buffalo, swine, sheep+goats, poultry
            da  = cs(reg,'Milk whole fresh cow')
            oc  = cs(reg,'Meat cattle')
            buf = cs(reg,'Meat buffalo')
            sw  = cs(reg,'Meat pig')
            sh  = cs(reg,'Meat sheep')  + cs(reg,'Milk whole fresh sheep')
            gt  = cs(reg,'Meat goat')   + cs(reg,'Milk whole fresh goat')
            la  = cs(reg,'Eggs Primary')    # layer hens
            br  = cs(reg,'Meat Poultry')    # broilers + ducks + turkeys + geese
            # CH4 (Gg) = M heads × EF (kg/head/yr)
            # 1 M heads × 1 kg/head/yr = 1e6 kg/yr = 1 Gg/yr  [direct conversion]
            ch4 = (da*ef['d'] + oc*ef['o'] + buf*ef['b'] + sw*ef['sw'] +
                   sh*ef['sh'] + gt*ef['gt'] + la*ef['la'] + br*ef['br'])
            records.append({'Scenario':scen,'Year':year,'Region':region,
                            'CH4_GgCH4':round(ch4,4)})

df_out = pd.DataFrame(records)
df_out.to_csv(SCEN_DIR+'scenario_ch4_mm_regional.csv', index=False)
g = df_out.groupby(['Scenario','Year'])['CH4_GgCH4'].sum().reset_index()
g.to_csv(SCEN_DIR+'scenario_ch4_mm_global.csv', index=False)
print("Saved: scenario_ch4_mm_regional.csv  scenario_ch4_mm_global.csv")

# ── Verification ──────────────────────────────────────────────────────────────
print()
print("=== Verification: 2020 global totals ===")
for _, r in g[g['Year']==2020].iterrows():
    print(f"  {r['Scenario']}: {r['CH4_GgCH4']:.0f} Gg CH4")
print(f"  Historical: FAO=9,888 Gg  |  Our Tier1=12,550 Gg")
print()
print("=== Scenario trajectories 2030/2050/2075/2100 (Gg CH4) ===")
for yr in [2030,2050,2075,2100]:
    row = g[g['Year']==yr]
    vals = '  '.join(f"{r['Scenario'][:13]}={r['CH4_GgCH4']:.0f}"
                     for _,r in row.iterrows())
    print(f"  {yr}: {vals}")
print("\nDone.")
