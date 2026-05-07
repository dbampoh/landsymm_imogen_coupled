"""
00_scenario_livestock_anchor.py
================================
Produces relative-change-anchored livestock head counts for all 5 SSP-RCP
scenarios (s1 realisations) for 2020-2100, at PLUM country/region level.

METHOD: Relative-change anchoring
----------------------------------
  scenario_heads(c, item, y, scen) =
      FAO_2020_baseline(c, item) × [PLUM(c, item, y, scen) / PLUM(c, item, 2020, scen)]

The FAO 2020 baseline is derived by applying the same R-script mapping logic
as Bart's continuity plot, but using the CURRENT (newer) FAO data and summing
at country level (not World row). PLUM aggregate regions are handled by summing
their FAO constituent countries before computing the relative change.

OUTPUT
------
  anchored_livestock_2020_2100.csv
    Columns: Scenario, Year, PLUMCountry, FAOItem, Heads_M
    Rows: 5 scenarios × 81 years × 158 PLUM regions × 10 items = ~640,800 rows

This file feeds directly into the sector-specific scenario processing scripts.

NOTES
-----
- Horses, Mules, Asses, Camels: NOT in PLUM; held at FAO 2020 country values
  throughout all scenarios (separate file: fao2020_missing_species.csv)
- PLUM 'Meat Poultry' already includes Ducks + Turkeys + Geese in its
  Meat Poultry item (per the R-script: Broilers + Ducks + Geese + Turkeys)
  so these are covered by the Meat Poultry anchoring
- Countries in FAO but not in PLUM: not anchored here; handled separately
  in sector scripts by holding at FAO 2020 values
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
    FAO_PRODUCTION_CSV, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES, PLUM_LIVESTOCK_TXT,
)

import pandas as pd
import numpy as np
import os

# =============================================================================
# SECTION 0: PATHS
# =============================================================================
PROD_CSV  = str(FAO_PRODUCTION_CSV)
PLUM_CSV  = str(PLUM_LIVESTOCK_TXT)
OUT_DIR   = (str(OUT_A_DATA) + '/scenario_pipeline/')
os.makedirs(OUT_DIR, exist_ok=True)

SCENARIOS = ['SSP1_RCP26_s1','SSP2_RCP45_s1','SSP3_RCP70_s1',
             'SSP4_RCP60_s1','SSP5_RCP85_s1']

PLUM_ITEMS = [
    'Eggs Primary',        # → Laying hens
    'Meat Poultry',        # → Broilers + Ducks + Turkeys + Geese
    'Meat buffalo',        # → Non-dairy buffalo
    'Meat cattle',         # → Non-dairy (beef) cattle
    'Meat goat',           # → Non-dairy goats
    'Meat pig',            # → All swine
    'Meat sheep',          # → Non-dairy sheep
    'Milk whole fresh cow',   # → Dairy cows
    'Milk whole fresh goat',  # → Dairy goats
    'Milk whole fresh sheep', # → Dairy sheep
]

# =============================================================================
# SECTION 1: PLUM AGGREGATE REGION → FAO CONSTITUENT COUNTRIES MAPPING
# =============================================================================
# For PLUM regions that bundle multiple countries, we sum FAO country-level
# 2020 stocks and apply the aggregate relative change.
PLUM_TO_FAO = {
    # Exact matches (no aggregation needed) -- handled automatically
    # Only non-trivial aggregates listed here:
    'Bahrain & Qatar':  ['Bahrain','Qatar'],
    'Belgium & Luxembourg': ['Belgium','Luxembourg','Belgium-Luxembourg'],
    'Bolivia':          ['Bolivia (Plurinational State of)'],
    'Caribbean Other':  ['Antigua and Barbuda','Bahamas','Barbados','Cuba',
                         'Dominica','Dominican Republic','Grenada','Haiti',
                         'Jamaica','Saint Kitts and Nevis','Saint Lucia',
                         'Saint Vincent and the Grenadines','Trinidad and Tobago',
                         'Puerto Rico','Netherlands Antilles','Aruba',
                         'Bermuda','Cayman Islands','Montserrat',
                         'British Virgin Islands','Turks and Caicos Islands',
                         'Guadeloupe','Martinique'],
    "Cote dIvoire":     ["Côte d'Ivoire"],
    'DR Congo':         ['Democratic Republic of the Congo'],
    'Gabon & Sao Tome': ['Gabon','Sao Tome and Principe','São Tomé and Príncipe'],
    'Guatemala & Belize':['Guatemala','Belize'],
    'Iran':             ['Iran (Islamic Republic of)'],
    'Italy & Malta':    ['Italy','Malta','Italy, San Marino and the Holy See',
                         'San Marino'],
    'Laos':             ["Lao People's Democratic Republic"],
    'Madagascar & Indian Ocean': ['Madagascar','Comoros','Mauritius',
                                   'Réunion','Seychelles','Mayotte'],
    'Malaysia Singapore & Brunei': ['Malaysia','Singapore','Brunei Darussalam'],
    'Moldova':          ['Republic of Moldova','Moldova'],
    'Netherlands':      ['Netherlands','Netherlands (Kingdom of the)'],
    'North Korea':      ["Democratic People's Republic of Korea"],
    'Pacific Other':    ['Fiji','Kiribati','Papua New Guinea','Samoa',
                         'Solomon Islands','Tonga','Tuvalu','Vanuatu',
                         'French Polynesia','New Caledonia','Cook Islands',
                         'Marshall Islands','Nauru','Niue','Palau',
                         'Timor-Leste'],
    'Russia':           ['Russian Federation'],
    'Senegal Gambia & Cabo Verde': ['Senegal','Gambia','Cabo Verde','Cape Verde'],
    'South Korea':      ['Republic of Korea','Korea, Republic of'],
    'Sri Lanka & Maldives': ['Sri Lanka','Maldives'],
    'Syria':            ['Syrian Arab Republic'],
    'Taiwan':           ['China, Taiwan Province of'],
    'Tanzania':         ['United Republic of Tanzania'],
    'Turkiye':          ['Türkiye','Turkey'],
    'United Kingdom':   ['United Kingdom','United Kingdom of Great Britain '
                         'and Northern Ireland'],
    'Venezuela':        ['Venezuela (Bolivarian Republic of)'],
}

# =============================================================================
# SECTION 2: FAO 2020 BASELINE — PLUM ITEM MAPPING
# =============================================================================
# Derive PLUM-compatible species aggregates from FAO production data.
# Each FAOItem derived from FAO using the R-script methodology:
#   Meat cattle  = Total cattle stocks − Dairy cows (Milk Animals)
#   Meat pig     = Total swine stocks
#   Meat buffalo = Total buffalo stocks − Dairy buffalo (≈ total; dairy buffalo small)
#   Meat sheep   = Total sheep stocks − Dairy sheep (Milk Animals)
#   Meat goat    = Total goats stocks − Dairy goats (Milk Animals)
#   Eggs Primary = Laying hens (Hen eggs in shell, Laying element)
#   Meat Poultry = Total chickens stocks − Laying hens + Ducks + Turkeys + Geese
#   Milk whole fresh cow   = Dairy cows (Raw milk of cattle, Milk Animals)
#   Milk whole fresh goat  = Dairy goats (Raw milk of goats, Milk Animals)
#   Milk whole fresh sheep = Dairy sheep (Raw milk of sheep, Milk Animals)

print("Loading FAO 2020 data ...")
df_fao = pd.read_csv(PROD_CSV, low_memory=False)
df_fao = df_fao[df_fao['Area Code'] < 5000].copy()
df_fao['Y2020'] = pd.to_numeric(df_fao['Y2020'], errors='coerce').fillna(0.)

def fao_item(item, element, unit=None):
    """Return country-level Series: area -> value in MILLIONS of heads."""
    mask = (df_fao['Item'] == item) & (df_fao['Element'] == element)
    if unit: mask = mask & (df_fao['Unit'] == unit)
    rows = df_fao[mask][['Area','Y2020']].copy()
    rows = rows.groupby('Area')['Y2020'].sum()
    # Convert to millions
    if unit == '1000 An' or (unit is None and len(rows) and
       df_fao[mask]['Unit'].iloc[0] == '1000 An'):
        rows = rows / 1e3
    else:
        rows = rows / 1e6   # individual animals -> millions
    return rows

# Raw FAO country-level stocks (millions of heads)
total_cattle  = fao_item('Cattle',           'Stocks', 'An')
total_buffalo = fao_item('Buffalo',          'Stocks', 'An')
total_sheep   = fao_item('Sheep',            'Stocks', 'An')
total_goats   = fao_item('Goats',            'Stocks', 'An')
total_swine   = fao_item('Swine / pigs',     'Stocks', 'An')
total_chick   = fao_item('Chickens',         'Stocks', '1000 An')
total_ducks   = fao_item('Ducks',            'Stocks', '1000 An')
total_turkeys = fao_item('Turkeys',          'Stocks', '1000 An')
total_geese   = fao_item('Geese',            'Stocks', '1000 An')

dairy_cows   = fao_item('Raw milk of cattle', 'Milk Animals', 'An')
dairy_goats  = fao_item('Raw milk of goats',  'Milk Animals', 'An')
dairy_sheep  = fao_item('Raw milk of sheep',  'Milk Animals', 'An')
dairy_buf    = fao_item('Raw milk of buffalo','Milk Animals', 'An')
laying_hens  = fao_item('Hen eggs in shell, fresh', 'Laying', '1000 An')

# Ensure dairy doesn't exceed total stocks
def safe_sub(total, subtract):
    """Subtract with floor at zero; align indices."""
    aligned = total.reindex(total.index).fillna(0) - \
               subtract.reindex(total.index).fillna(0)
    return aligned.clip(lower=0)

meat_cattle   = safe_sub(total_cattle,  dairy_cows)
meat_buffalo  = safe_sub(total_buffalo, dairy_buf)
meat_sheep    = safe_sub(total_sheep,   dairy_sheep)
meat_goat     = safe_sub(total_goats,   dairy_goats)
meat_pig      = total_swine.copy()
eggs_primary  = laying_hens.copy()
meat_poultry  = (safe_sub(total_chick, laying_hens)
                 .add(total_ducks.reindex(total_chick.index).fillna(0))
                 .add(total_turkeys.reindex(total_chick.index).fillna(0))
                 .add(total_geese.reindex(total_chick.index).fillna(0)))

# Build FAO baseline: {FAOItem -> country Series (M heads)}
FAO_BASELINE = {
    'Meat cattle':           meat_cattle,
    'Milk whole fresh cow':  dairy_cows,
    'Meat buffalo':          meat_buffalo,
    'Meat sheep':            meat_sheep,
    'Milk whole fresh sheep':dairy_sheep,
    'Meat goat':             meat_goat,
    'Milk whole fresh goat': dairy_goats,
    'Meat pig':              meat_pig,
    'Eggs Primary':          eggs_primary,
    'Meat Poultry':          meat_poultry,
}

# For each PLUM aggregate region, sum the FAO constituent countries
def fao_region_baseline(plum_region, fao_item_name):
    """Get total FAO 2020 baseline (M heads) for a PLUM region."""
    series = FAO_BASELINE[fao_item_name]
    if plum_region in PLUM_TO_FAO:
        constituents = PLUM_TO_FAO[plum_region]
        return series.reindex(constituents).fillna(0.).sum()
    else:
        # Direct match (PLUM country name = FAO country name)
        return series.get(plum_region, 0.)

print("FAO 2020 baselines computed.")
print(f"  Global cattle (meat+milk): "
      f"{meat_cattle.sum():.0f} + {dairy_cows.sum():.0f} = "
      f"{meat_cattle.sum()+dairy_cows.sum():.0f} M")
print(f"  Global swine: {meat_pig.sum():.0f} M")
print(f"  Global chickens (broilers+layers): "
      f"{safe_sub(total_chick,laying_hens).sum():.0f} + "
      f"{eggs_primary.sum():.0f} = "
      f"{meat_poultry.sum():.0f}+{eggs_primary.sum():.0f} M")

# =============================================================================
# SECTION 3: ALSO SAVE MISSING SPECIES (held at FAO 2020 throughout scenarios)
# =============================================================================
# Horses, Mules, Asses, Camels not in PLUM -> constant at FAO 2020
horses = fao_item('Horses',          'Stocks', 'An')
mules  = fao_item('Mules and hinnies','Stocks', 'An')
asses  = fao_item('Asses',           'Stocks', 'An')
camels = fao_item('Camels',          'Stocks', 'An')

missing = pd.DataFrame({
    'Horses_M':  horses,
    'Mules_M':   mules,
    'Asses_M':   asses,
    'Camels_M':  camels,
}).reset_index().rename(columns={'Area':'Country'})
missing.to_csv(OUT_DIR + 'fao2020_missing_species.csv', index=False)
print(f"\nSaved fao2020_missing_species.csv ({len(missing)} countries)")

# =============================================================================
# SECTION 4: LOAD PLUM S1 DATA
# =============================================================================
print("\nLoading PLUM data (s1 scenarios only) ...")
plum_df = pd.read_csv(PLUM_CSV, low_memory=False)
plum_s1 = plum_df[plum_df['Scenario'].isin(SCENARIOS)].copy()
print(f"  {len(plum_s1):,} rows loaded.")

# Get PLUM 2020 baseline (anchor year) per scenario/country/item
plum_2020 = plum_s1[plum_s1['Year'] == 2020].set_index(
    ['Scenario','Country','FAOItem'])['Heads(M)']

# =============================================================================
# SECTION 5: COMPUTE ANCHORED HEAD COUNTS
# =============================================================================
print("\nComputing anchored livestock head counts ...")

records = []

# Process each scenario
for scen in SCENARIOS:
    scen_data = plum_s1[plum_s1['Scenario'] == scen]

    for item in PLUM_ITEMS:
        item_data = scen_data[scen_data['FAOItem'] == item]

        for _, row in item_data.iterrows():
            country = row['Country']
            year    = row['Year']
            plum_val = row['Heads(M)']

            # PLUM 2020 anchor for this scenario/country/item
            try:
                plum_2020_val = plum_2020.loc[(scen, country, item)]
            except KeyError:
                plum_2020_val = np.nan

            # FAO 2020 baseline for this PLUM region/item
            fao_base = fao_region_baseline(country, item)

            # Relative change
            if (pd.notna(plum_2020_val) and plum_2020_val > 0 and fao_base > 0):
                rel_change = plum_val / plum_2020_val
                anchored   = fao_base * rel_change
            elif fao_base == 0:
                anchored = 0.0   # no animals in 2020, can't grow
            else:
                # PLUM 2020 = 0 for this region/item; use PLUM absolute directly
                # (rare case; relative change undefined)
                anchored = plum_val

            records.append({
                'Scenario':   scen,
                'Year':       year,
                'PLUMCountry':country,
                'FAOItem':    item,
                'Heads_M':    round(anchored, 6),
                'PLUM_raw':   round(plum_val, 6),
            })

df_anchored = pd.DataFrame(records)
print(f"  {len(df_anchored):,} records computed.")

# Verify 2020 global totals match FAO 2020 country sums
print("\n--- Verification: anchored 2020 global totals vs FAO 2020 country sum ---")
anchored_2020_ssp2 = df_anchored[
    (df_anchored['Year']==2020) & (df_anchored['Scenario']=='SSP2_RCP45_s1')
].groupby('FAOItem')['Heads_M'].sum()
for item in PLUM_ITEMS:
    fao_g = sum(fao_region_baseline(c, item)
                for c in plum_s1['Country'].unique())
    anch  = anchored_2020_ssp2.get(item, 0.)
    print(f"  {item:<30} FAO={fao_g:>8.1f}M  Anchored={anch:>8.1f}M  "
          f"match={abs(anch-fao_g)<0.1}")

# =============================================================================
# SECTION 6: SAVE OUTPUT
# =============================================================================
out_path = OUT_DIR + 'anchored_livestock_2020_2100.csv'
df_anchored.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print(f"  Shape: {df_anchored.shape}")
print(f"  Scenarios: {df_anchored['Scenario'].unique()}")
print(f"  Years: {df_anchored['Year'].min()} - {df_anchored['Year'].max()}")
print("\nDone.")
