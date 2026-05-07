"""
01_scenario_ch4_ef.py
======================
CH4 Enteric Fermentation scenario emissions 2020-2100.
Uses relative-change-anchored livestock from anchored_livestock_2020_2100.csv.
Applies identical IPCC 2019 Tier 1 equations to those in the historical script.

MISSING SPECIES HANDLING
------------------------
- Horses, Mules, Asses, Camels: held constant at FAO 2020 country values
  (loaded from fao2020_missing_species.csv)
- Swine and Poultry: excluded (negligible enteric CH4, consistent with historical)

OUTPUT
------
  scenario_ch4_ef_global.csv   — global total by scenario and year
  scenario_ch4_ef_regional.csv — by IPCC region, scenario, year
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
    FAO_PRODUCTION_CSV, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
)

import pandas as pd
import numpy as np
import os  # [Step 11 of unified-codebase rebuild: bug fix - 'os' was used
            #  without import (line 44 below). Predecessor never failed
            #  here because os was imported transitively via _sys/_Path
            #  at module-load in some Python versions; on Python 3.9.x
            #  the transitive import doesn't expose os at module scope.
            #  - DKB 2026-05-07]

# =============================================================================
# SECTION 0: PATHS AND CONFIGURATION
# =============================================================================
PROD_CSV  = str(FAO_PRODUCTION_CSV)
SCEN_DIR  = (str(OUT_A_DATA) + '/scenario_pipeline/')
os.makedirs(SCEN_DIR, exist_ok=True)
OUT_DIR   = SCEN_DIR

SCENARIOS = ['SSP1_RCP26_s1','SSP2_RCP45_s1','SSP3_RCP70_s1',
             'SSP4_RCP60_s1','SSP5_RCP85_s1']

GG_PER_KG = 1e-6   # kg CH4 -> Gg CH4

# =============================================================================
# SECTION 1: IPCC ENTERIC FERMENTATION EF TABLE (same as historical script)
# IPCC 2019 Refinement Vol.4 Ch.10, Table 10.11
# Units: kg CH4 / head / year
# =============================================================================
R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']

def rd(v): return dict(zip(R9, v))

EF_DAIRY    = rd([128,128,100,117,100, 88, 88,100, 82])
EF_OTHER    = rd([ 53, 69, 69, 70, 58, 41, 43, 47, 30])
EF_BUFFALO  = rd([ 55, 55, 55, 55, 55, 55, 55, 55, 55])
EF_SHEEP    = rd([  8,  8,  8,  8,  5,  5,  5,  5,  5])
EF_GOATS    = rd([  5,  5,  5,  5,  5,  5,  5,  5,  5])
EF_CAMELS   = rd([ 46, 46, 46, 46, 46, 46, 46, 46, 46])
EF_HORSES   = rd([ 18, 18, 18, 18, 18, 18, 18, 18, 18])
EF_MULES    = rd([10,10,10,10,10,10,10,10,10])  # approx (Ch.10)
EF_ASSES    = rd([10,10,10,10,10,10,10,10,10])

# =============================================================================
# SECTION 2: REGION MAPPING (same as historical script)
# =============================================================================
REGION_SETS = {
    'Indian Subcontinent': {'Afghanistan','Bangladesh','Bhutan','India','Maldives',
                            'Nepal','Pakistan','Sri Lanka'},
    'North America':       {'United States of America','Canada','Greenland',
                            'Saint Pierre and Miquelon'},
    'Western Europe':      {'Albania','Andorra','Austria','Belgium','Belgium-Luxembourg',
        'Cyprus','Denmark','Finland','France and Monaco','France','Germany','Greece',
        'Iceland','Ireland','Israel and Palestine, State of',
        'Italy, San Marino and the Holy See','Italy','Luxembourg','Malta','Netherlands',
        'Norway','Portugal','Spain and Andorra','Spain','Sweden',
        'Switzerland and Liechtenstein','Switzerland','United Kingdom',
        'Monaco','San Marino','Liechtenstein'},
    'Eastern Europe':      {'Armenia','Azerbaijan','Belarus','Bosnia and Herzegovina',
        'Bulgaria','Croatia','Czechia','Czech Republic','Estonia','Georgia','Hungary',
        'Kazakhstan','Kyrgyzstan','Latvia','Lithuania','Moldova','Montenegro',
        'North Macedonia','Poland','Romania','Russia','Russian Federation','Serbia',
        'Serbia and Montenegro','Slovakia','Slovenia','Tajikistan','Türkiye','Turkey',
        'Turkmenistan','Ukraine','Uzbekistan','Kosovo','Yugoslavia','Republic of Moldova'},
    'Oceania':             {'Australia','Cook Islands','Fiji','Kiribati','Marshall Islands',
        'Nauru','New Caledonia','New Zealand','Niue','Palau','Papua New Guinea','Samoa',
        'Solomon Islands','Tonga','Tuvalu','Vanuatu','French Polynesia'},
    'Latin America':       {'Antigua and Barbuda','Argentina','Bahamas','Barbados',
        'Belize','Bolivia (Plurinational State of)','Bolivia','Brazil','Chile','Colombia',
        'Costa Rica','Cuba','Dominica','Dominican Republic','Ecuador','El Salvador',
        'Grenada','Guatemala','Guyana','Haiti','Honduras','Jamaica','Mexico',
        'Nicaragua','Panama','Paraguay','Peru','Saint Kitts and Nevis','Saint Lucia',
        'Saint Vincent and the Grenadines','Suriname','Trinidad and Tobago','Uruguay',
        'Venezuela (Bolivarian Republic of)','Venezuela','Puerto Rico','Aruba',
        'Netherlands Antilles','Bermuda','Cayman Islands','Montserrat',
        'British Virgin Islands','Turks and Caicos Islands','Guadeloupe','Martinique'},
    'Middle East':         {'Bahrain','Egypt','Iran (Islamic Republic of)','Iran','Iraq',
        'Jordan','Kuwait','Lebanon','Libya','Morocco','Oman','Qatar','Saudi Arabia',
        'Syrian Arab Republic','Syria','Tunisia','United Arab Emirates','Yemen','Algeria',
        'Djibouti','Israel','Mauritania','Somalia','Sudan','Sudan and South Sudan'},
    'Africa':              {'Angola','Benin','Botswana','Burkina Faso','Burundi',
        'Cabo Verde','Cameroon','Central African Republic','Chad','Comoros','Congo',
        "Côte d'Ivoire","Côte d`Ivoire",'Democratic Republic of the Congo',
        'Equatorial Guinea','Eritrea','Eswatini','Ethiopia','Gabon','Gambia','Ghana',
        'Guinea','Guinea-Bissau','Kenya','Lesotho','Liberia','Madagascar','Malawi','Mali',
        'Mauritius','Mozambique','Namibia','Niger','Nigeria','Rwanda',
        'São Tomé and Príncipe','Sao Tome and Principe','Senegal','Seychelles',
        'Sierra Leone','South Africa','South Sudan','Tanzania','Togo','Uganda',
        'United Republic of Tanzania','Zambia','Zimbabwe','Ethiopia PDR','Cape Verde',
        'Réunion','Mayotte'},
    'Asia':                {'Brunei Darussalam','Cambodia','China','China, mainland',
        'China, Hong Kong SAR','China, Macao SAR','China, Taiwan Province of',
        'Indonesia','Japan',"Democratic People's Republic of Korea",'North Korea',
        'Korea, Republic of','South Korea','Republic of Korea',
        "Lao People's Democratic Republic",'Laos','Malaysia','Mongolia','Myanmar',
        'Myanmar/Burma','Philippines','Singapore','Thailand','Timor-Leste',
        'Viet Nam','Vietnam','Hong Kong','Macao','Taiwan'},
}

def get_region(country):
    for r, s in REGION_SETS.items():
        if country in s: return r
    return 'Africa'

# =============================================================================
# SECTION 3: PLUM → FAO COUNTRY MAPPING (for region assignment)
# =============================================================================
# For PLUM aggregate regions, assign the region of the dominant country
PLUM_REGION = {
    'Bahrain & Qatar': 'Middle East',
    'Belgium & Luxembourg': 'Western Europe',
    'Bolivia': 'Latin America',
    'Caribbean Other': 'Latin America',
    "Cote dIvoire": 'Africa',
    'DR Congo': 'Africa',
    'Gabon & Sao Tome': 'Africa',
    'Guatemala & Belize': 'Latin America',
    'Iran': 'Middle East',
    'Italy & Malta': 'Western Europe',
    'Laos': 'Asia',
    'Madagascar & Indian Ocean': 'Africa',
    'Malaysia Singapore & Brunei': 'Asia',
    'Moldova': 'Eastern Europe',
    'Netherlands': 'Western Europe',
    'North Korea': 'Asia',
    'Pacific Other': 'Oceania',
    'Russia': 'Eastern Europe',
    'Senegal Gambia & Cabo Verde': 'Africa',
    'South Korea': 'Asia',
    'Sri Lanka & Maldives': 'Indian Subcontinent',
    'Syria': 'Middle East',
    'Taiwan': 'Asia',
    'Tanzania': 'Africa',
    'Turkiye': 'Eastern Europe',
    'United Kingdom': 'Western Europe',
    'Venezuela': 'Latin America',
}

def plum_country_region(c):
    if c in PLUM_REGION: return PLUM_REGION[c]
    return get_region(c)

# =============================================================================
# SECTION 4: LOAD ANCHORED LIVESTOCK AND MISSING SPECIES
# =============================================================================
print("Loading anchored livestock data ...")
df = pd.read_csv(SCEN_DIR + 'anchored_livestock_2020_2100.csv')
df['Region'] = df['PLUMCountry'].apply(plum_country_region)

# Missing species: horses, mules, asses, camels (constant at FAO 2020)
print("Loading missing species (horses, mules, asses, camels) ...")
missing = pd.read_csv(SCEN_DIR + 'fao2020_missing_species.csv')
missing['Region'] = missing['Country'].apply(get_region)  # [Step 11 of unified-codebase rebuild: was 'FAOCountry' (stale per Quick_Start.md provenance check); the historical livestock-anchor script writes 'Country'. Single-script source-of-truth fix; aligns with version_A reference outputs which also used 'Country'. - DKB 2026-05-07]

# Global regional totals for missing species (constant across all years/scenarios)
missing_regional = missing.groupby('Region')[['Horses_M','Mules_M','Asses_M','Camels_M']].sum()

# =============================================================================
# SECTION 5: COMPUTE CH4 ENTERIC FERMENTATION EMISSIONS
# =============================================================================
print("Computing CH4 EF scenario emissions ...")

records = []

for scen in SCENARIOS:
    scen_df = df[df['Scenario'] == scen].copy()

    for year in sorted(scen_df['Year'].unique()):
        yr_df = scen_df[scen_df['Year'] == year]

        # Livestock by PLUM country and item
        # Pivot to wide: PLUMCountry x FAOItem
        wide = yr_df.pivot_table(
            index=['PLUMCountry','Region'],
            columns='FAOItem',
            values='Heads_M',
            aggfunc='sum',
            fill_value=0.
        ).reset_index()

        total_ch4 = 0.
        for region in R9:
            reg = wide[wide['Region'] == region]
            if len(reg) == 0: continue

            # Livestock head counts (M)
            dairy = reg.get('Milk whole fresh cow', pd.Series([0.]*len(reg))).sum()
            other = reg.get('Meat cattle',          pd.Series([0.]*len(reg))).sum()
            buf   = reg.get('Meat buffalo',         pd.Series([0.]*len(reg))).sum()
            sh    = (reg.get('Meat sheep',          pd.Series([0.]*len(reg))).sum() +
                     reg.get('Milk whole fresh sheep',pd.Series([0.]*len(reg))).sum())
            gt    = (reg.get('Meat goat',           pd.Series([0.]*len(reg))).sum() +
                     reg.get('Milk whole fresh goat',pd.Series([0.]*len(reg))).sum())

            # Missing species: constant FAO 2020 regional totals
            miss_r = missing_regional.loc[region] if region in missing_regional.index \
                     else pd.Series({'Horses_M':0,'Mules_M':0,'Asses_M':0,'Camels_M':0})
            ho   = miss_r['Horses_M']
            mu   = miss_r['Mules_M']
            ass  = miss_r['Asses_M']
            cam  = miss_r['Camels_M']

            # CH4 (kg/yr) = head (M) × 1e6 × EF (kg/head/yr) -> Gg = × 1e6 × 1e-6
            # Simplification: M heads × EF (kg/head/yr) × 1e6 × 1e-6 = M heads × EF / 1e6 ... no
            # M heads × 1e6 heads × EF kg/head/yr = EF × 1e6 kg/yr = EF M kg/yr = EF / 1000 Gg/yr
            # More cleanly: 1 M heads × EF kg/head/yr = EF × 1e6 kg/yr = EF × 1e-3 Gg/yr
            def ch4(heads_M, ef): return heads_M * ef * 1e6 * GG_PER_KG

            reg_ch4 = (ch4(dairy,EF_DAIRY[region])   + ch4(other,EF_OTHER[region]) +
                       ch4(buf,  EF_BUFFALO[region])  + ch4(sh,   EF_SHEEP[region]) +
                       ch4(gt,   EF_GOATS[region])    + ch4(ho,   EF_HORSES[region]) +
                       ch4(mu,   EF_MULES[region])    + ch4(ass,  EF_ASSES[region]) +
                       ch4(cam,  EF_CAMELS[region]))

            records.append({
                'Scenario': scen, 'Year': year, 'Region': region,
                'Dairy_M': dairy, 'OtherCattle_M': other, 'Buffalo_M': buf,
                'Sheep_M': sh, 'Goats_M': gt, 'Horses_M': ho,
                'CH4_GgCH4': round(reg_ch4, 4)
            })
            total_ch4 += reg_ch4

print(f"  Computed {len(records):,} region-year-scenario records")

df_out = pd.DataFrame(records)

# Regional CSV
df_out[['Scenario','Year','Region','CH4_GgCH4']].to_csv(
    OUT_DIR + 'scenario_ch4_ef_regional.csv', index=False)
print(f"Saved: scenario_ch4_ef_regional.csv")

# Global CSV
global_df = df_out.groupby(['Scenario','Year'])['CH4_GgCH4'].sum().reset_index()
global_df.to_csv(OUT_DIR + 'scenario_ch4_ef_global.csv', index=False)
print(f"Saved: scenario_ch4_ef_global.csv")

# =============================================================================
# SECTION 6: VERIFICATION
# =============================================================================
print()
print("=== CH4 EF verification: 2020 anchoring ===")
v2020 = global_df[global_df['Year']==2020]
print(f"  2020 (all scenarios identical at FAO baseline):")
for _, r in v2020.iterrows():
    print(f"    {r['Scenario']}: {r['CH4_GgCH4']:.0f} Gg CH4")
fao_hist = 101857  # FAO 2020 published value (Gg)
our_hist = 133002  # Our IPCC 2019 Tier 1 historical (Gg)
print(f"  Historical reference: FAO={fao_hist} Gg, Our Tier 1={our_hist} Gg")
print()
print("=== CH4 EF scenario trajectories (global, Gg CH4) ===")
for yr in [2030, 2050, 2075, 2100]:
    print(f"  {yr}:")
    for _, r in global_df[global_df['Year']==yr].iterrows():
        print(f"    {r['Scenario']}: {r['CH4_GgCH4']:.0f} Gg CH4")

print("\nDone.")
