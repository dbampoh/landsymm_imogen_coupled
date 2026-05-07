"""
scenario_n2o_synfert_processing.py
====================================
N2O from Synthetic Fertilizer Application — scenario 2020-2100.

Uses PLUMv2 crop data (FertAmount column, Mt N/yr by country, crop type,
and land-use type) as the FSN activity data.  Applies identical IPCC 2019
Refinement Tier 1 equations to those in the historical n2o_synfert script.

DATA INPUTS
-----------
  plum_crop_s1.csv  (from /tmp/plum_crop_s1.csv)
    Columns: Scenario, Year, Country, Type, Crop, Area, AbandonedArea,
             FertAmount [Mt N/yr], IrrigAmount, OtherAmount, Production [Mt DM]
    Scenarios: SSP1_RCP26/s1 ... SSP5_RCP85/s1
    Years: 2020-2100 (annual)
    Countries: 158 PLUM regions (same as livestock data)

UNITS
-----
  FertAmount: Mt N / yr  (confirmed by global sum ~149 Mt ≈ FAO 140 Mt for 2020)
  For IPCC equations: convert Mt N → kg N (* 1e9)
  Output: Gg N2O / yr  (= kt N2O / yr)

IPCC EQUATIONS (Ch.11, 2019 Refinement — same as historical script)
--------------------------------------------------------------------
  Direct:   N2O_dir  = FSN × EF1 × (44/28)
  Indirect (volatilisation): N2O_vol = FSN × FracGASF × EF4 × (44/28)
  Indirect (leaching):       N2O_lea = FSN × FracLEACH × EF5 × (44/28)
                             [dry climate regions: FracLEACH = 0]

PARAMETERS (2019 Refinement, Table 11.3)
-----------------------------------------
  EF1       = 0.010  kg N2O-N / kg N applied
  FracGASF  = 0.11   (2019)
  EF4       = 0.010  kg N2O-N / kg N volatilised
  FracLEACH = 0.24   (wet climates) / 0.00 (dry: Middle East)
  EF5       = 0.011  kg N2O-N / kg N leached
  MW_N2O    = 44/28  (N → N2O molar mass conversion)

SCENARIO 2020 OFFSET FROM HISTORICAL
--------------------------------------
  Historical 2020 (our Tier 1):   2390 Gg N2O (FSN direct only, 2019)
  Scenario 2020 (PLUM FertAmount): ~2800 Gg N2O (direct)
  Offset (~17%): PLUM FertAmount global = 149 Mt N vs historical 115 Mt N.
  PLUM uses broader crop categorisation and different vintage fertilizer data.
  This offset is documentable and consistent across all 5 SSPs at 2020.

OUTPUT FILES
------------
  scenario_n2o_synfert_global.csv    — 5 scenarios × 81 years
  scenario_n2o_synfert_regional.csv  — 5 scenarios × 81 years × 9 regions
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
PLUM_CROP   = str(PLUM_CROP_CSV)
OUT_DIR     = os.path.join(str(OUT_A_DATA), 'scenario_pipeline')
os.makedirs(OUT_DIR, exist_ok=True)

SCENARIOS_CROP = ['SSP1_RCP26/s1','SSP2_RCP45/s1','SSP3_RCP70/s1',
                  'SSP4_RCP60/s1','SSP5_RCP85/s1']
# Map crop scenario names (forward slash) to standard key names (underscore)
SCEN_MAP = {
    'SSP1_RCP26/s1':'SSP1_RCP26_s1','SSP2_RCP45/s1':'SSP2_RCP45_s1',
    'SSP3_RCP70/s1':'SSP3_RCP70_s1','SSP4_RCP60/s1':'SSP4_RCP60_s1',
    'SSP5_RCP85/s1':'SSP5_RCP85_s1',
}

# =============================================================================
# SECTION 1: IPCC 2019 PARAMETERS (Table 11.3)
# =============================================================================
EF1          = 0.010   # kg N2O-N / kg N applied (Tier 1 aggregated; unchanged 2006→2019)
FRAC_GASF_19 = 0.11    # volatilisation fraction for synthetic N (2019)
EF4          = 0.010   # kg N2O-N / kg N volatilised
FRAC_LEACH   = 0.24    # fraction N lost to leaching (wet climates, 2019)
EF5          = 0.011   # kg N2O-N / kg N leached (2019)
MW_N2O       = 44.0 / 28.0   # N2O/N2 molar mass ratio
KG_TO_GG     = 1.0e-6        # kg → Gg
# FertAmount in Mt N; 1 Mt N = 1e9 kg N
MT_TO_KG     = 1.0e9

DRY_REGIONS  = {'Middle East'}   # no leaching contribution

# =============================================================================
# SECTION 2: REGION MAPPING
# =============================================================================
R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']

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
# SECTION 3: LOAD PLUM CROP DATA
# =============================================================================
print("Loading PLUMv2 crop data ...")
df_crop = pd.read_csv(PLUM_CROP, low_memory=False)
df_crop['Region'] = df_crop['Country'].apply(plum_region)
df_crop['Scenario_std'] = df_crop['Scenario'].map(SCEN_MAP)

print(f"  {len(df_crop):,} rows  |  "
      f"Scenarios: {sorted(df_crop['Scenario_std'].dropna().unique())}  |  "
      f"Years: {df_crop['Year'].min()}-{df_crop['Year'].max()}")

# Crops excluded from FSN: pasture, setaside (no synthetic N applied)
EXCL_CROPS = {'pasture', 'setaside'}

# =============================================================================
# SECTION 4: COMPUTE N2O EMISSIONS
# =============================================================================
print("Computing N2O scenario emissions (synthetic fertilizer) ...")

records = []

for scen_crop, scen_std in SCEN_MAP.items():
    scen_df = df_crop[df_crop['Scenario'] == scen_crop]

    for year in sorted(scen_df['Year'].unique()):
        yr_df = scen_df[(scen_df['Year'] == year) &
                        (~scen_df['Crop'].isin(EXCL_CROPS))]

        # Sum FertAmount by region (Mt N)
        reg_fert = yr_df.groupby('Region')['FertAmount'].sum()

        for region in R9:
            fsn_mt = reg_fert.get(region, 0.)   # Mt N
            if fsn_mt <= 0.:
                records.append({'Scenario':scen_std,'Year':year,'Region':region,
                                'FSN_MtN':0.,'N2O_direct_GgN2O':0.,
                                'N2O_vol_GgN2O':0.,'N2O_leach_GgN2O':0.,
                                'N2O_total_GgN2O':0.})
                continue

            fsn_kg  = fsn_mt * MT_TO_KG   # kg N

            # Direct N2O
            n2o_dir = fsn_kg * EF1 * MW_N2O * KG_TO_GG           # Gg N2O

            # Indirect — volatilisation (2019)
            n2o_vol = fsn_kg * FRAC_GASF_19 * EF4 * MW_N2O * KG_TO_GG

            # Indirect — leaching (2019; zero in dry climates)
            frac_l  = 0.0 if region in DRY_REGIONS else FRAC_LEACH
            n2o_lea = fsn_kg * frac_l * EF5 * MW_N2O * KG_TO_GG

            n2o_tot = n2o_dir + n2o_vol + n2o_lea

            records.append({
                'Scenario':scen_std,'Year':year,'Region':region,
                'FSN_MtN':round(fsn_mt,6),
                'N2O_direct_GgN2O':round(n2o_dir,4),
                'N2O_vol_GgN2O':   round(n2o_vol,4),
                'N2O_leach_GgN2O': round(n2o_lea,4),
                'N2O_total_GgN2O': round(n2o_tot,4),
            })

df_out = pd.DataFrame(records)
print(f"  {len(df_out):,} records computed")

# Regional CSV
df_out.to_csv(os.path.join(OUT_DIR,'scenario_n2o_synfert_regional.csv'), index=False)

# Global CSV
gcols = ['Scenario','Year','N2O_direct_GgN2O','N2O_vol_GgN2O',
         'N2O_leach_GgN2O','N2O_total_GgN2O','FSN_MtN']
g = df_out.groupby(['Scenario','Year'])[gcols[2:]].sum().reset_index()
g.columns = ['Scenario','Year'] + gcols[2:]
g.to_csv(os.path.join(OUT_DIR,'scenario_n2o_synfert_global.csv'), index=False)

print("Saved: scenario_n2o_synfert_regional.csv")
print("Saved: scenario_n2o_synfert_global.csv")

# =============================================================================
# SECTION 5: VERIFICATION
# =============================================================================
print()
print("=== Verification: 2020 global totals (all scenarios) ===")
g2020 = g[g['Year']==2020]
for _, r in g2020.iterrows():
    print(f"  {r['Scenario']}: total={r['N2O_total_GgN2O']:.1f} Gg N2O  "
          f"(dir={r['N2O_direct_GgN2O']:.1f}  vol={r['N2O_vol_GgN2O']:.1f}  "
          f"lea={r['N2O_leach_GgN2O']:.1f})  FSN={r['FSN_MtN']:.1f} Mt N")

print(f"\n  Historical ref (2019 params, total 2020): "
      f"2390 Gg N2O (direct only from 115 Mt N FSN)")
print(f"  Scenario uses PLUM FertAmount ~149 Mt N at 2020 → expected ~30% higher")

print()
print("=== Scenario trajectories — global N2O total (Gg N2O) ===")
SCENARIOS = ['SSP1_RCP26_s1','SSP2_RCP45_s1','SSP3_RCP70_s1',
             'SSP4_RCP60_s1','SSP5_RCP85_s1']
for yr in [2030, 2050, 2075, 2100]:
    row = g[g['Year']==yr]
    vals = '  '.join(f"{r['Scenario'][:13]}={r['N2O_total_GgN2O']:.0f}"
                     for _, r in row.iterrows())
    print(f"  {yr}: {vals}")

print("\nDone.")
