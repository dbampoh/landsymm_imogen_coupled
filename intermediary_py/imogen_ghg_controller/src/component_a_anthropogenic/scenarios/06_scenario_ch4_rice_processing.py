"""
scenario_ch4_rice_processing.py
=================================
CH4 from Rice Cultivation — scenario projections 2020-2100.
PLUMv2 s1 central realisations, 5 SSP-RCP storylines.

WATER-REGIME SPLIT METHOD: OPTION B — IrrigAmount split
---------------------------------------------------------
PLUM provides a field 'IrrigAmount' (volume of irrigation water applied) for
each country × crop × scenario × year row. This is used to partition total
rice area into two IPCC water-regime classes:

  IrrigAmount > 0  →  Irrigated rice (IPCC aggregated SFw = 0.60)
  IrrigAmount = 0  →  Rainfed lowland rice (IPCC aggregated SFw = 0.45)

Upland rice (SFw = 0.00) is not separately represented in PLUMv2; rows
with IrrigAmount = 0 receive the rainfed lowland SFw (conservative — upland
would produce zero CH4, so this may slightly overestimate rainfed contribution).

KNOWN CAVEATS OF OPTION B
--------------------------
1. All major Asian rice producers (China, India, Indonesia, Bangladesh) appear
   as 100% irrigated in PLUM. In reality India is ~51% irrigated (IRRI). This
   is a PLUM structural simplification — irrigation is routed to high-yield
   commercial systems and not to smallholder rainfed paddies.
2. Russia appears with 14.5 Mha rainfed rice (FAO actual: 0.2 Mha). This is a
   PLUM regional aggregation artifact — 'Russia' in PLUM likely accumulates
   area that does not correspond to rice-producing systems.
3. The irrigated fraction evolves dynamically across SSPs (from ~79% at 2020 to
   83-92% by 2100 depending on SSP), which is physically plausible and provides
   real scenario differentiation that Option C (all-irrigated) would miss.

Despite these caveats, Option B is preferred over Option C because:
  - It uses information actually present in the PLUM data
  - The irrigated/rainfed proportions and their SSP-differentiated trajectories
    are scientifically meaningful at the global scale
  - The ratio of irrigated to rainfed EF (~1.33×) means the split matters
    but is not the dominant source of uncertainty (area trend is larger)

IPCC EQUATIONS (Ch. 5, 2019 Refinement — same as historical rice script)
-------------------------------------------------------------------------
  EF_i = EFc × SFw × SFp × SFo          (Eq. 5.2)
  CH4_i = EF_i × t × Area_i × 10^-6     (Eq. 5.1; Area in ha, output in Gg CH4)

PARAMETERS (2019 Refinement, Tables 5.11, 5.11A, 5.12, 5.13, 5.14)
--------------------------------------------------------------------
  EFc: region-specific baseline daily EF (kg CH4 ha-1 day-1):
    East Asia=1.32, SE Asia=1.22, South Asia=0.85, Europe=1.56,
    N.America=0.65, S.America=1.27, Africa=1.19

  T: region-specific cultivation period (days):
    East Asia=112, SE Asia=102, South Asia=112, Europe=123,
    N.America=139, S.America=124, Africa=113

  SFw: aggregated water-regime scaling factors:
    Irrigated=0.60, Rainfed=0.45, Upland=0.00 (Table 5.12)

  SFp: pre-season scaling factor = 1.00 (non-flooded, <180 days; Table 5.13)

  SFo: organic amendment factor:
    Irrigated = 1 + (2.0 × 1.00)^0.59 = 2.508  [2t/ha straw, Table 5.14]
    Rainfed = 1.00 (straw burned/removed)

PLUM DATA INPUTS
----------------
  /tmp/plum_crop_s1.csv  (filtered from country_land_use.txt.gz)
    Columns used: Scenario, Year, Country, Type, Crop, Area [Mha], IrrigAmount
    Rows used: Crop == 'rice', both 'conventional' and 'restricted' land-use types

  Area units: Mha → convert to ha (× 1e6) for IPCC equation

2020 ANCHOR COMPARISON
-----------------------
  Historical Tier 1 (2019 params) 2020:    26,898 Gg CH4
  FAO 2020:                                24,684 Gg CH4
  EDGAR 2020:                              25,355 Gg CH4
  Scenario 2020 (SSP2, Option B):          ~23,000–25,000 Gg CH4 expected
    (lower than historical because PLUM covers ~120 Mha vs FAO 195 Mha;
     historical uses complete FAO harvested area data)

OUTPUT FILES
------------
  scenario_ch4_rice_global.csv    — 5 scenarios × 81 years, global totals
  scenario_ch4_rice_regional.csv  — 5 scenarios × 81 years × 9 IPCC regions
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
HERE      = os.path.dirname(os.path.abspath(__file__))
PLUM_CROP = str(PLUM_CROP_CSV)

SCENARIOS_CROP = ['SSP1_RCP26/s1','SSP2_RCP45/s1','SSP3_RCP70/s1',
                  'SSP4_RCP60/s1','SSP5_RCP85/s1']
SCEN_MAP = {
    'SSP1_RCP26/s1':'SSP1_RCP26_s1','SSP2_RCP45/s1':'SSP2_RCP45_s1',
    'SSP3_RCP70/s1':'SSP3_RCP70_s1','SSP4_RCP60/s1':'SSP4_RCP60_s1',
    'SSP5_RCP85/s1':'SSP5_RCP85_s1',
}
SCENARIOS = list(SCEN_MAP.values())

R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']

# =============================================================================
# SECTION 1: IPCC 2019 REFINEMENT PARAMETERS (Tables 5.11, 5.11A, 5.12-5.14)
# =============================================================================

# Baseline EF (kg CH4 ha-1 day-1) — Table 5.11 (2019 updated)
EFC = {
    'East Asia':      1.32,
    'Southeast Asia': 1.22,
    'South Asia':     0.85,
    'Europe':         1.56,
    'North America':  0.65,
    'South America':  1.27,
    'Africa':         1.19,   # global estimate (Table 5.11 footnote 1)
}

# Cultivation period (days) — Table 5.11A (new in 2019)
T_DAYS = {
    'East Asia':      112,
    'Southeast Asia': 102,
    'South Asia':     112,
    'Europe':         123,
    'North America':  139,
    'South America':  124,
    'Africa':         113,   # global estimate
}

# Water-regime scaling factors — aggregated case, Table 5.12 (2019 updated)
SFW_IRRIGATED = 0.60
SFW_RAINFED   = 0.45   # rainfed lowland + deepwater blend
SFW_UPLAND    = 0.00   # not represented separately in PLUM

# Pre-season water regime — Table 5.13: non-flooded < 180 days = 1.00
SFP = 1.00

# Organic amendment scaling — Table 5.14 (Eq. 5.3: 1 + (ROA×CFOA)^0.59)
# Irrigated: 2 t/ha dry straw incorporated (Yan et al. global median)
ROA_STRAW  = 2.0;  CFOA_STRAW = 1.00;  EXP_SFO = 0.59
SFO_IRRIGATED = 1.0 + (ROA_STRAW * CFOA_STRAW) ** EXP_SFO   # = 2.508
SFO_RAINFED   = 1.00   # straw burned/removed in rainfed systems

# Pre-compute adjusted daily EF per RICE REGION × water class
# (Table 5.11 uses seven rice sub-regions distinct from the 9 IPCC regions)
ADJ_EF = {}
for region in EFC:
    efc = EFC[region]
    ADJ_EF[region] = {
        'irrigated': efc * SFW_IRRIGATED * SFP * SFO_IRRIGATED,
        'rainfed':   efc * SFW_RAINFED   * SFP * SFO_RAINFED,
    }

print("IPCC 2019 adjusted daily EF by rice sub-region (kg CH4 ha-1 day-1):")
for r, d in ADJ_EF.items():
    print(f"  {r:15s}: irrigated={d['irrigated']:.4f}  rainfed={d['rainfed']:.4f}")

# =============================================================================
# SECTION 2: REGION MAPPING
# =============================================================================
# IPCC 9-region → IPCC rice sub-region (for EFc / T assignment)
REGION_TO_RICE_SUBREGION = {
    'North America':       'North America',
    'Western Europe':      'Europe',
    'Eastern Europe':      'Europe',
    'Oceania':             'Southeast Asia',   # Australia rice → SE Asia EFc
    'Latin America':       'South America',
    'Africa':              'Africa',
    'Middle East':         'Africa',           # minimal rice; use global estimate
    'Asia':                'East Asia',
    'Indian Subcontinent': 'South Asia',
}

# Country → IPCC R9 mapping
REGION_SETS = {
    'Indian Subcontinent': {'Afghanistan','Bangladesh','Bhutan','India','Maldives',
                            'Nepal','Pakistan','Sri Lanka'},
    'North America':       {'United States of America','Canada','Greenland'},
    'Western Europe':      {'Albania','Andorra','Austria','Belgium','Belgium-Luxembourg',
        'Cyprus','Denmark','Finland','France','France and Monaco','Germany','Greece',
        'Iceland','Ireland','Italy','Italy, San Marino and the Holy See','Luxembourg',
        'Malta','Netherlands','Norway','Portugal','Spain','Spain and Andorra','Sweden',
        'Switzerland','Switzerland and Liechtenstein','United Kingdom','Monaco',
        'San Marino','Liechtenstein'},
    'Eastern Europe':      {'Armenia','Azerbaijan','Belarus','Bosnia and Herzegovina',
        'Bulgaria','Croatia','Czechia','Czech Republic','Estonia','Georgia','Hungary',
        'Kazakhstan','Kyrgyzstan','Latvia','Lithuania','Moldova','Montenegro',
        'North Macedonia','Poland','Romania','Russia','Russian Federation','Serbia',
        'Serbia and Montenegro','Slovakia','Slovenia','Tajikistan','Türkiye','Turkey',
        'Turkmenistan','Ukraine','Uzbekistan','Republic of Moldova'},
    'Oceania':             {'Australia','Cook Islands','Fiji','Kiribati','Marshall Islands',
        'Nauru','New Caledonia','New Zealand','Niue','Palau','Papua New Guinea','Samoa',
        'Solomon Islands','Tonga','Tuvalu','Vanuatu','French Polynesia','Timor-Leste',
        'Pacific Other'},
    'Latin America':       {'Antigua and Barbuda','Argentina','Bahamas','Barbados',
        'Belize','Bolivia (Plurinational State of)','Bolivia','Brazil','Chile',
        'Colombia','Costa Rica','Cuba','Dominica','Dominican Republic','Ecuador',
        'El Salvador','Grenada','Guatemala','Guyana','Haiti','Honduras','Jamaica',
        'Mexico','Nicaragua','Panama','Paraguay','Peru','Saint Kitts and Nevis',
        'Saint Lucia','Saint Vincent and the Grenadines','Suriname',
        'Trinidad and Tobago','Uruguay','Venezuela (Bolivarian Republic of)',
        'Venezuela','Puerto Rico','Aruba','Netherlands Antilles','Guadeloupe',
        'Martinique','Guatemala & Belize','Caribbean Other'},
    'Middle East':         {'Bahrain','Egypt','Iran (Islamic Republic of)','Iran','Iraq',
        'Jordan','Kuwait','Lebanon','Libya','Morocco','Oman','Qatar','Saudi Arabia',
        'Syrian Arab Republic','Syria','Tunisia','United Arab Emirates','Yemen',
        'Algeria','Djibouti','Israel','Mauritania','Somalia','Sudan',
        'Bahrain & Qatar'},
    'Africa':              {'Angola','Benin','Botswana','Burkina Faso','Burundi',
        'Cabo Verde','Cameroon','Central African Republic','Chad','Comoros','Congo',
        "Côte d'Ivoire","Côte d`Ivoire",'Democratic Republic of the Congo',
        'Equatorial Guinea','Eritrea','Eswatini','Ethiopia','Ethiopia PDR','Gabon',
        'Gambia','Ghana','Guinea','Guinea-Bissau','Kenya','Lesotho','Liberia',
        'Madagascar','Malawi','Mali','Mauritius','Mozambique','Namibia','Niger',
        'Nigeria','Rwanda','São Tomé and Príncipe','Sao Tome and Principe','Senegal',
        'Seychelles','Sierra Leone','South Africa','South Sudan','Tanzania','Togo',
        'Uganda','United Republic of Tanzania','Zambia','Zimbabwe','Cape Verde',
        'Réunion','Mayotte','DR Congo','Gabon & Sao Tome',
        'Senegal Gambia & Cabo Verde','Madagascar & Indian Ocean','Cote dIvoire'},
    'Asia':                {'Brunei Darussalam','Cambodia','China','China, mainland',
        'China, Hong Kong SAR','China, Macao SAR','China, Taiwan Province of',
        'Indonesia','Japan',"Democratic People's Republic of Korea",'North Korea',
        'Korea, Republic of','South Korea','Republic of Korea',
        "Lao People's Democratic Republic",'Laos','Malaysia','Mongolia','Myanmar',
        'Philippines','Singapore','Thailand','Viet Nam','Vietnam','Hong Kong',
        'Macao','Taiwan','Malaysia Singapore & Brunei','North Korea','South Korea',
        'Taiwan'},
}

PLUM_REGION_OVERRIDE = {
    'Bolivia':'Latin America','Caribbean Other':'Latin America',
    'DR Congo':'Africa','Gabon & Sao Tome':'Africa',
    'Guatemala & Belize':'Latin America','Iran':'Middle East',
    'Italy & Malta':'Western Europe','Laos':'Asia',
    'Madagascar & Indian Ocean':'Africa','Malaysia Singapore & Brunei':'Asia',
    'Moldova':'Eastern Europe','Netherlands':'Western Europe',
    'North Korea':'Asia','Pacific Other':'Oceania','Russia':'Eastern Europe',
    'Senegal Gambia & Cabo Verde':'Africa','South Korea':'Asia',
    'Sri Lanka & Maldives':'Indian Subcontinent','Syria':'Middle East',
    'Taiwan':'Asia','Tanzania':'Africa','Turkiye':'Eastern Europe',
    'United Kingdom':'Western Europe','Venezuela':'Latin America',
    'Bahrain & Qatar':'Middle East','Belgium & Luxembourg':'Western Europe',
    'Cote dIvoire':'Africa',
}

def get_region(c):
    if c in PLUM_REGION_OVERRIDE:
        return PLUM_REGION_OVERRIDE[c]
    for r, s in REGION_SETS.items():
        if c in s:
            return r
    return 'Africa'   # fallback

# =============================================================================
# SECTION 3: LOAD AND PREPARE PLUM CROP DATA
# =============================================================================
print("\nLoading PLUMv2 crop data (rice rows only) ...")
df_all = pd.read_csv(PLUM_CROP, low_memory=False)
df_rice = df_all[df_all['Crop'] == 'rice'].copy()
df_rice['Region']   = df_rice['Country'].apply(get_region)
df_rice['Scen_std'] = df_rice['Scenario'].map(SCEN_MAP)

# Irrigated flag: IrrigAmount > 0
df_rice['is_irrigated'] = df_rice['IrrigAmount'] > 0

print(f"  Rice rows: {len(df_rice):,}")
print(f"  Scenarios: {sorted(df_rice['Scen_std'].dropna().unique())}")
print(f"  Years: {df_rice['Year'].min()}–{df_rice['Year'].max()}")
print(f"  Countries: {df_rice['Country'].nunique()}")

# 2020 SSP2 diagnostic
diag = df_rice[(df_rice['Scen_std']=='SSP2_RCP45_s1') & (df_rice['Year']==2020)]
irr  = diag[diag['is_irrigated']]['Area'].sum()
rai  = diag[~diag['is_irrigated']]['Area'].sum()
print(f"\n  SSP2 2020: irrigated={irr:.1f} Mha ({irr/(irr+rai)*100:.1f}%)  "
      f"rainfed={rai:.1f} Mha ({rai/(irr+rai)*100:.1f}%)")

# =============================================================================
# SECTION 4: COMPUTE CH4 EMISSIONS
# =============================================================================
print("\nComputing CH4 rice scenario emissions ...")

records = []

for scen_crop, scen_std in SCEN_MAP.items():
    scen_df = df_rice[df_rice['Scenario'] == scen_crop]

    for year in sorted(scen_df['Year'].unique()):
        yr_df = scen_df[scen_df['Year'] == year]

        for region in R9:
            rice_sub = REGION_TO_RICE_SUBREGION[region]
            ef_irr  = ADJ_EF[rice_sub]['irrigated']   # kg CH4 ha-1 day-1
            ef_rain = ADJ_EF[rice_sub]['rainfed']
            t       = T_DAYS[rice_sub]                  # days

            reg_df  = yr_df[yr_df['Region'] == region]

            # Area split (Mha → ha: × 1e6)
            area_irr_ha  = reg_df[reg_df['is_irrigated']]['Area'].sum()  * 1e6
            area_rain_ha = reg_df[~reg_df['is_irrigated']]['Area'].sum() * 1e6
            area_tot_ha  = area_irr_ha + area_rain_ha

            # CH4 (kg CH4) = EF_i (kg/ha/day) × t (day) × Area (ha)
            # → Gg CH4: × 1e-6
            ch4_irr  = ef_irr  * t * area_irr_ha  * 1e-6   # Gg CH4
            ch4_rain = ef_rain * t * area_rain_ha * 1e-6   # Gg CH4
            ch4_tot  = ch4_irr + ch4_rain

            records.append({
                'Scenario':      scen_std,
                'Year':          year,
                'Region':        region,
                'RiceSubregion': rice_sub,
                'Area_irr_Mha':  round(area_irr_ha / 1e6, 6),
                'Area_rain_Mha': round(area_rain_ha / 1e6, 6),
                'Area_tot_Mha':  round(area_tot_ha / 1e6, 6),
                'Frac_irrigated':round(area_irr_ha / max(area_tot_ha, 1e-9), 6),
                'CH4_irr_GgCH4': round(ch4_irr,  4),
                'CH4_rain_GgCH4':round(ch4_rain, 4),
                'CH4_GgCH4':     round(ch4_tot,  4),
            })

df_out = pd.DataFrame(records)
print(f"  {len(df_out):,} records computed")

# Regional CSV
df_out.to_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_ch4_rice_regional.csv'), index=False)
print("  Saved: scenario_ch4_rice_regional.csv")

# Global CSV — sum across regions
gcols = ['CH4_irr_GgCH4','CH4_rain_GgCH4','CH4_GgCH4',
         'Area_irr_Mha','Area_rain_Mha','Area_tot_Mha']
g = df_out.groupby(['Scenario','Year'])[gcols].sum().reset_index()
g['Frac_irrigated'] = g['Area_irr_Mha'] / g['Area_tot_Mha'].replace(0, np.nan)
g.to_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_ch4_rice_global.csv'), index=False)
print("  Saved: scenario_ch4_rice_global.csv")

# =============================================================================
# SECTION 5: VERIFICATION
# =============================================================================
print()
print("=== Verification: 2020 global totals (all scenarios) ===")
g2020 = g[g['Year'] == 2020].sort_values('Scenario')
for _, r in g2020.iterrows():
    print(f"  {r['Scenario']}: {r['CH4_GgCH4']:.0f} Gg CH4  "
          f"(irrig={r['CH4_irr_GgCH4']:.0f}  rain={r['CH4_rain_GgCH4']:.0f})  "
          f"area={r['Area_tot_Mha']:.1f} Mha  irrig_frac={r['Frac_irrigated']:.3f}")

print(f"\n  Historical Tier 1 2020:  26,898 Gg CH4 (FAO 195 Mha)")
print(f"  FAO 2020:                24,684 Gg CH4")
print(f"  EDGAR 2020:              25,355 Gg CH4")
print(f"  Note: PLUM covers ~120 Mha vs FAO 195 Mha → scenario lower than historical")
print(f"        (relative trajectory is the key use of scenario output)")

print()
print("=== Scenario trajectories — global CH4 total (Gg CH4) ===")
for yr in [2030, 2050, 2075, 2100]:
    row = g[g['Year'] == yr]
    vals = '  '.join(
        f"{r['Scenario'][:13]}={r['CH4_GgCH4']:.0f}"
        for _, r in row.iterrows()
    )
    print(f"  {yr}: {vals}")

print("\nDone.")
