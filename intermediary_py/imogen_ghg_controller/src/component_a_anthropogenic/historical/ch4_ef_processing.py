
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
# CH4 EMISSIONS FROM ENTERIC FERMENTATION — IPCC 2019 REFINEMENT TIER 1
# =============================================================================
#
# PURPOSE
# -------
# Implements the 2019 Refinement to the 2006 IPCC Guidelines for National GHG
# Inventories, Volume 4, Chapter 10, Section 10.3 (Tier 1) for methane (CH4)
# emissions from enteric fermentation in livestock. Applied at country level
# using FAO Production/Crops and Livestock activity data, 1970-2020.
#
# GOVERNING EQUATIONS (IPCC 2019 Refinement, Equations 10.19-10.20)
# -----------------------------------------------------------------
# Equation 10.19 — Emissions from a single livestock category T:
#
#   E(T) = Σ_P [ EF(T,P) × N(T,P) ] / 10^6
#
# Equation 10.20 — Total enteric fermentation emissions:
#
#   Total_CH4_Enteric = Σ_i  E(i)
#
# Where:
#   E(T)      = CH4 from category T, Gg CH4 yr-1
#   EF(T,P)   = emission factor, kg CH4 head-1 yr-1  [Tables 10.10, 10.11]
#   N(T,P)    = number of head in category T, productivity system P
#   10^6      = converts kg → Gg
#   P         = productivity class (Tier 1a only; Tier 1 uses a single blended EF)
#
# This is the simplest of the three Chapter 10 calculations — there are no
# AWMS fractions, no climate zones, and no multi-step volatilisation pathway.
# The only inputs are: head counts, emission factors, and the dairy/non-dairy
# and layer/broiler species splits derived from FAO production sub-items.
#
# TIER 1 EMISSION FACTORS
# -----------------------
# Cattle and Buffalo: Table 10.11 — region-specific Tier 1 values (kg CH4/head/yr)
#   These were derived from full Tier 2 calculations (GLEAM + Annex 10A.1-10A.4)
#   and represent population-weighted averages for each IPCC sub-region. They
#   differ substantially from the 2006 values, especially for dairy cattle in
#   developed regions (where higher milk yields → higher CH4 via rumen kinetics).
#
# Other species: Table 10.10 — high and low productivity system EFs
#   Footnote 1: "For all regions other than North America, Europe and Oceania
#   the Tier 1 default values are the low productivity EFs."
#   So developed regions = high productivity EF; all others = low productivity EF.
#
# SPECIES COVERAGE
# ----------------
#   Dairy cattle       — split from total cattle using FAO 'Milk Animals' element
#   Non-dairy cattle   — total cattle minus dairy; all sub-categories combined
#   Buffalo            — region-specific EF (Table 10.11)
#   Sheep              — Table 10.10 (high prod: 9, low prod: 5 kg CH4/head/yr)
#   Goats              — Table 10.10 (high prod: 9, low prod: 5 kg CH4/head/yr)
#   Swine              — Table 10.10 (high prod: 1.5, low prod: 1 kg CH4/head/yr)
#   Horses             — Table 10.10 (18 kg CH4/head/yr, all regions)
#   Mules and Asses    — Table 10.10 (10 kg CH4/head/yr, all regions)
#   Camels             — Table 10.10 (46 kg CH4/head/yr, all regions)
#   Poultry            — Table 10.10: "Insufficient data for calculation" → excluded
#
# WHAT IS NOT INCLUDED
# --------------------
#   Poultry:  explicitly excluded per Table 10.10 note
#   Deer, Ostrich, Llamas/Alpacas: not separately reported in FAOSTAT stocks;
#     their contribution is globally < 0.3% and excluded
#
# DAIRY / NON-DAIRY SPLIT
# ------------------------
# FAO 'Milk Animals' element under 'Raw milk of cattle' gives the number of
# cows currently in milk production. This is capped at total cattle stocks
# (a data quality measure). Non-dairy = total cattle − dairy.
# This split is critical: dairy cows have EFs 1.4–2.7× higher than non-dairy
# cattle depending on the region, because high-producing cows consume more
# feed and have more complex rumen methane dynamics.
#
# INPUTS
# ------
#   Production_Crops_Livestock_E_All_Data.csv — FAO livestock stocks and
#     milk production data (with 'Milk Animals' element for dairy split)
#
# OUTPUTS
# -------
#   ch4_ef_global.csv   — Global annual totals with FAO published comparison
#   ch4_ef_country.csv  — Country × year × species results (Gg CH4)
#   ch4_ef_regional.csv — Regional annual totals
#   ch4_ef_species.csv  — Species breakdown, all years, globally
#
# REFERENCES
# ----------
#   IPCC (2019). 2019 Refinement to the 2006 IPCC Guidelines, Vol. 4, Ch. 10.
#     Equations 10.19-10.20; Tables 10.10, 10.11. Section 10.3.
#   IPCC (2006). Guidelines for National GHG Inventories, Vol. 4, Ch. 10.
#   FAO (2023). FAOSTAT Emissions — Agriculture (GLE domain), Enteric
#     Fermentation, Emissions (CH4).
# =============================================================================

import pandas as pd
import numpy as np

YEAR_START = 1970
YEAR_END   = 2020
YEAR_COLS  = [f'Y{y}' for y in range(YEAR_START, YEAR_END + 1)]
KG_TO_GG   = 1.0e-6   # 1 Gg = 10^6 kg

print("=" * 70)
print("CH4 FROM ENTERIC FERMENTATION — IPCC 2019 REFINEMENT TIER 1")
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
    """Return a DataFrame (Area Code index) with YEAR_COLS as columns."""
    mask = (df_c['Item'] == item_name) & (df_c['Element'] == element_name)
    s = df_c[mask][['Area Code', 'Area'] + YEAR_COLS].copy()
    return s.set_index('Area Code')

# Livestock head counts (head; chickens/ducks/turkeys in 1000 head)
cattle_df  = extract_stocks('Cattle')
buffalo_df = extract_stocks('Buffalo')
sheep_df   = extract_stocks('Sheep')
goats_df   = extract_stocks('Goats')
swine_df   = extract_stocks('Swine / pigs')
horses_df  = extract_stocks('Horses')
mules_df   = extract_stocks('Mules')
asses_df   = extract_stocks('Asses')
camels_df  = extract_stocks('Camels')

# Dairy split: 'Milk Animals' under 'Raw milk of cattle'
# Gives the number of cows currently in milk production — used to partition
# total cattle into dairy vs non-dairy for separate EF application
dairy_df   = extract_stocks('Raw milk of cattle', 'Milk Animals')

area_names = df_c.drop_duplicates('Area Code').set_index('Area Code')['Area'].to_dict()
area_codes = list(area_names.keys())
print(f"    {len(area_codes)} countries/territories loaded")
print(f"    Items: cattle, buffalo, sheep, goats, swine, horses, mules, asses, camels + dairy split")

# =============================================================================
# SECTION 2: COUNTRY → IPCC REGION MAPPING
# =============================================================================
# Nine IPCC sub-regions determine which Table 10.11 emission factor to use
# for cattle and buffalo. For all other species (Table 10.10), the distinction
# is simply developed (NA, WE, EE, OC) vs developing (all others).

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
    return 'Africa'   # conservative fallback for unlisted territories

R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']

# Developed regions (use high productivity EFs from Table 10.10)
DEVELOPED = {'North America','Western Europe','Eastern Europe','Oceania'}

area_region = {ac: get_region(area_names[ac]) for ac in area_codes}
print(f"[2] Region mapping complete ({len(R9)} IPCC sub-regions)")

# =============================================================================
# SECTION 3: EMISSION FACTORS (Tables 10.10 and 10.11)
# =============================================================================
# All values are read directly from the 2019 Refinement Tables 10.10 and 10.11.
# Units throughout: kg CH4 / head / year
# Uncertainty: ±30-50% per Table 10.10 footnote; ±30% for cattle/buffalo per
# 2006 IPCC Guidelines Section 10.3.4 (retained in 2019 Refinement).

# ---------------------------------------------------------------------------
# 3A. CATTLE AND BUFFALO — Table 10.11 (region-specific, from Tier 2 calcs)
# ---------------------------------------------------------------------------
# These are the Tier 1 single values — representing population-weighted
# averages of the full Tier 2 sub-category calculations in Annex 10A.1-10A.4.
# They reflect: animal mass, diet quality, milk yield, feed digestibility, and
# the IPCC Ym (methane conversion factor from Tier 2 for cattle/buffalo).
#
# Source: 2019 Refinement Table 10.11, "Emission Factor" column (kg CH4/head/yr)

EF_DAIRY = {          # Dairy cattle — Table 10.11
    'North America':       138,   # avg milk yield 10,250 kg/head/yr
    'Western Europe':      126,   # avg milk yield 7,410 kg/head/yr
    'Eastern Europe':       93,   # avg milk yield 4,000 kg/head/yr
    'Oceania':              93,   # avg milk yield 4,400 kg/head/yr
    'Latin America':        87,   # avg milk yield 2,200 kg/head/yr (Tier 1 mean)
    'Africa':               76,   # avg milk yield 1,300 kg/head/yr
    'Middle East':          76,   # avg milk yield 2,500 kg/head/yr
    'Asia':                 78,   # avg milk yield 2,800 kg/head/yr (est from Annex)
    'Indian Subcontinent':  73,   # avg milk yield 1,900 kg/head/yr
}

EF_OTHER_CATTLE = {   # Non-dairy cattle — Table 10.11
    'North America':       64,   # beef herd + growing steers + feedlot
    'Western Europe':      52,   # beef cows + growing steers/heifers + calves
    'Eastern Europe':      58,   # beef cows + growing + replacement + calves
    'Oceania':             63,   # grazing beef herd + growing
    'Latin America':       56,   # multipurpose + growing + calves
    'Africa':              52,   # multipurpose + draft + growing + calves
    'Middle East':         60,   # multipurpose + growing + calves
    'Asia':                54,   # multipurpose (stall-fed and grazing) + growing
    'Indian Subcontinent': 46,   # draft bullocks + multipurpose + growing + calves
}

EF_BUFFALO = {        # Buffalo — Table 10.11
    # Note: buffalo do not occur in North America or Oceania (no separate entry).
    # For those regions the buffalo stock should be essentially zero,
    # but we use a regional fallback value matching the closest climate.
    'North America':       58,   # fallback — effectively no buffalo
    'Western Europe':      78,   # intensive Italian/Romanian system
    'Eastern Europe':      68,   # commercialised roughage-based
    'Oceania':             58,   # fallback — effectively no buffalo
    'Latin America':       68,   # smallholder multi-purpose
    'Africa':              81,   # smallholder cropland-integrated
    'Middle East':         67,   # smallholder grazing
    'Asia':                68,   # diverse systems (Table 10.11 mean)
    'Indian Subcontinent': 85,   # smallholder, poor-quality roughage
}

# ---------------------------------------------------------------------------
# 3B. OTHER SPECIES — Table 10.10 (high vs low productivity systems)
# ---------------------------------------------------------------------------
# Table 10.10 footnote 1 (critical):
# "For all regions other than North America, Europe and Oceania the Tier 1
#  default values are the LOW PRODUCTIVITY EFs."
# So: DEVELOPED regions → high productivity EF
#     All other regions  → low productivity EF

# Sheep: 9 kg CH4/head/yr (high prod), 5 kg CH4/head/yr (low prod)
# Liveweights: 65 kg high prod, 45 kg low prod
EF_SHEEP_HIGH = 9    # kg CH4/head/yr — high productivity systems
EF_SHEEP_LOW  = 5    # kg CH4/head/yr — low productivity systems

# Goats: 9 kg CH4/head/yr (high prod), 5 kg CH4/head/yr (low prod)
# Liveweights: 50 kg high prod, 28 kg low prod
EF_GOATS_HIGH = 9    # kg CH4/head/yr — high productivity systems
EF_GOATS_LOW  = 5    # kg CH4/head/yr — low productivity systems

# Swine: 1.5 kg CH4/head/yr (high prod), 1 kg CH4/head/yr (low prod)
# Liveweights: 72 kg high prod, 52 kg low prod
# NOTE: These are the lowest EFs in the table — swine are monogastrics and
# produce minimal enteric CH4. Enteric fermentation for swine is globally
# < 1% of total, but is still included for completeness.
EF_SWINE_HIGH = 1.5  # kg CH4/head/yr — high productivity
EF_SWINE_LOW  = 1.0  # kg CH4/head/yr — low productivity

# Horses: 18 kg CH4/head/yr — single value, all regions (hindgut fermenter)
EF_HORSES = 18

# Mules and Asses: 10 kg CH4/head/yr — single value, all regions
EF_MULES_ASSES = 10

# Camels: 46 kg CH4/head/yr — single value, all regions (foregut fermenter,
# similar metabolic pathway to ruminants but lower body weight at 570 kg)
EF_CAMELS = 46

# Poultry: Table 10.10 states "Insufficient data for calculation" — excluded.
# This is consistent with FAO's GLE methodology, which also excludes poultry
# from enteric fermentation (birds have no foregut or hindgut fermentation
# comparable to ruminants; any emissions are negligible).

print("[3] All emission factors loaded from Tables 10.10 and 10.11")
print(f"    Cattle EFs: dairy range {min(EF_DAIRY.values())}–{max(EF_DAIRY.values())} kg/head/yr")
print(f"    Other cattle: {min(EF_OTHER_CATTLE.values())}–{max(EF_OTHER_CATTLE.values())} kg/head/yr")
print(f"    Buffalo: {min(EF_BUFFALO.values())}–{max(EF_BUFFALO.values())} kg/head/yr")
print(f"    Sheep/Goats: {EF_SHEEP_LOW}–{EF_SHEEP_HIGH} kg/head/yr")

# =============================================================================
# SECTION 4: UTILITY FUNCTION
# =============================================================================
def gv(df_s, ac, yr_col):
    """Safely retrieve a livestock count for a given area code and year."""
    try:
        if ac in df_s.index:
            rows = df_s.loc[[ac]]
            if len(rows) > 0 and yr_col in rows.columns:
                v = rows[yr_col].iloc[0]
                return float(v) if pd.notna(v) and v != 0 else 0.0
    except Exception:
        pass
    return 0.0

# =============================================================================
# SECTION 5: MAIN COMPUTATION LOOP (Equation 10.19 applied per country-year)
# =============================================================================
# For each country × year, apply Equation 10.19:
#   E(T) = EF(T) × N(T) / 10^6  for each species T
# then sum over species (Equation 10.20).
#
# Species split logic:
#   Dairy cattle:     N from FAO 'Milk Animals' element, capped at total cattle
#   Non-dairy cattle: total cattle − dairy cattle
#   All other species: taken directly from FAO 'Stocks' element
#
# Productivity split for Table 10.10 species:
#   DEVELOPED regions (NA, WE, EE, OC): high productivity EF
#   All other regions: low productivity EF (Table 10.10 footnote 1)

print(f"\n[4] Running computation...")
print(f"    {len(area_codes)} countries × {len(YEAR_COLS)} years")

records = []

for ac in area_codes:
    country = area_names[ac]
    region  = area_region[ac]
    is_dev  = region in DEVELOPED   # determines high vs low productivity EF

    for yr in YEAR_COLS:
        year = int(yr[1:])
        sp_ch4 = {}   # species → kg CH4

        # ----- CATTLE (split dairy / non-dairy) --------------------------
        cattle_tot = gv(cattle_df,  ac, yr)
        dairy_n    = min(gv(dairy_df, ac, yr), cattle_tot)  # cap at total
        nondairy_n = cattle_tot - dairy_n

        if dairy_n > 0:
            # Equation 10.19 for dairy cattle
            sp_ch4['Dairy Cattle'] = dairy_n * EF_DAIRY[region]

        if nondairy_n > 0:
            # Equation 10.19 for non-dairy (other) cattle
            sp_ch4['Other Cattle'] = nondairy_n * EF_OTHER_CATTLE[region]

        # ----- BUFFALO ---------------------------------------------------
        buf_n = gv(buffalo_df, ac, yr)
        if buf_n > 0:
            sp_ch4['Buffalo'] = buf_n * EF_BUFFALO[region]

        # ----- SHEEP (Table 10.10) ----------------------------------------
        sh_n = gv(sheep_df, ac, yr)
        if sh_n > 0:
            ef_sh = EF_SHEEP_HIGH if is_dev else EF_SHEEP_LOW
            sp_ch4['Sheep'] = sh_n * ef_sh

        # ----- GOATS (Table 10.10) ----------------------------------------
        gt_n = gv(goats_df, ac, yr)
        if gt_n > 0:
            ef_gt = EF_GOATS_HIGH if is_dev else EF_GOATS_LOW
            sp_ch4['Goats'] = gt_n * ef_gt

        # ----- SWINE (Table 10.10) ----------------------------------------
        sw_n = gv(swine_df, ac, yr)
        if sw_n > 0:
            ef_sw = EF_SWINE_HIGH if is_dev else EF_SWINE_LOW
            sp_ch4['Swine'] = sw_n * ef_sw

        # ----- HORSES (Table 10.10 — single value all regions) -----------
        hs_n = gv(horses_df, ac, yr)
        if hs_n > 0:
            sp_ch4['Horses'] = hs_n * EF_HORSES

        # ----- MULES (Table 10.10 — single value all regions) ------------
        ml_n = gv(mules_df, ac, yr)
        if ml_n > 0:
            sp_ch4['Mules'] = ml_n * EF_MULES_ASSES

        # ----- ASSES (Table 10.10 — same EF as mules) --------------------
        as_n = gv(asses_df, ac, yr)
        if as_n > 0:
            sp_ch4['Asses'] = as_n * EF_MULES_ASSES

        # ----- CAMELS (Table 10.10 — single value all regions) -----------
        cm_n = gv(camels_df, ac, yr)
        if cm_n > 0:
            sp_ch4['Camels'] = cm_n * EF_CAMELS

        # ----- TOTAL (Equation 10.20) -------------------------------------
        total_kg = sum(sp_ch4.values())

        # Accumulate record
        rec = {
            'Year':       year,
            'Area Code':  ac,
            'Area':       country,
            'Region':     region,
            'Total_kgCH4': total_kg,
        }
        SPECIES_LIST = ['Dairy Cattle','Other Cattle','Buffalo','Sheep','Goats',
                        'Swine','Horses','Mules','Asses','Camels']
        for sp in SPECIES_LIST:
            rec[f'{sp.replace(" ","_")}_kgCH4'] = sp_ch4.get(sp, 0.0)
        records.append(rec)

print(f"    {len(records):,} country-year records computed")

# =============================================================================
# SECTION 6: AGGREGATE AND CONVERT UNITS
# =============================================================================
print("\n[5] Aggregating to regional and global totals...")

df_out = pd.DataFrame(records)
kg_cols = [c for c in df_out.columns if c.endswith('_kgCH4')]
gg_cols = []
for col in kg_cols:
    gg_col = col.replace('_kgCH4', '_GgCH4')
    df_out[gg_col] = df_out[col] * KG_TO_GG
    gg_cols.append(gg_col)

# --- Global annual totals ---
df_global = df_out.groupby('Year')[gg_cols].sum().reset_index()

# --- FAO published reference series ---
# Source: FAOSTAT Emissions — Agriculture, GLE domain
# Item: Enteric Fermentation | Element: Emissions (CH4) | Source: FAO TIER 1
# Units: kt CH4 = Gg CH4
FAO_EF_CH4 = {
    1970:73925.9, 1971:74950.2, 1972:76201.6, 1973:77172.5, 1974:79001.5,
    1975:80325.8, 1976:81014.4, 1977:81241.2, 1978:81421.9, 1979:81915.5,
    1980:82889.6, 1981:83658.5, 1982:84617.1, 1983:85138.4, 1984:85710.7,
    1985:86119.8, 1986:86848.5, 1987:86930.8, 1988:87415.6, 1989:88638.1,
    1990:89201.2, 1991:89153.8, 1992:88568.7, 1993:88209.6, 1994:88944.6,
    1995:89231.9, 1996:89247.4, 1997:87666.9, 1998:87820.4, 1999:88057.1,
    2000:88438.8, 2001:88496.0, 2002:89295.3, 2003:90339.2, 2004:91421.4,
    2005:92362.1, 2006:93167.6, 2007:93965.2, 2008:94628.9, 2009:94844.8,
    2010:94742.8, 2011:95111.1, 2012:95857.5, 2013:96329.3, 2014:96956.0,
    2015:97702.6, 2016:98798.8, 2017:99297.3, 2018:99524.5, 2019:100406.3,
    2020:101856.5,
}
df_global['FAO_published_GgCH4'] = df_global['Year'].map(FAO_EF_CH4)
df_global['Ratio_to_FAO'] = (df_global['Total_GgCH4'] /
                              df_global['FAO_published_GgCH4'])

# --- Regional annual totals ---
df_regional = df_out.groupby(['Year','Region'])[gg_cols].sum().reset_index()

# --- Species breakdown (all years, global) ---
sp_gg_cols = [c for c in gg_cols if 'Total' not in c]
df_species = df_out.groupby('Year')[sp_gg_cols].sum().reset_index()

# =============================================================================
# SECTION 7: SAVE OUTPUTS
# =============================================================================
df_global.to_csv((str(OUT_A_DATA) + '/ch4_ef/ch4_ef_global.csv'), index=False)
df_out[['Year','Area Code','Area','Region'] + gg_cols].to_csv(
    (str(OUT_A_DATA) + '/ch4_ef/ch4_ef_country.csv'), index=False)
df_regional.to_csv((str(OUT_A_DATA) + '/ch4_ef/ch4_ef_regional.csv'), index=False)
df_species.to_csv((str(OUT_A_DATA) + '/ch4_ef/ch4_ef_species.csv'), index=False)

# =============================================================================
# SECTION 8: PRINT SUMMARY
# =============================================================================
print("\n" + "=" * 78)
print("GLOBAL CH4 FROM ENTERIC FERMENTATION — IPCC 2019 REFINEMENT TIER 1")
print("=" * 78)
print(f"{'Year':>5} | {'Our estimate':>14} | {'FAO published':>14} | {'Ratio':>8}")
print("-" * 55)
for _, row in df_global[df_global['Year'].isin(range(1970, 2021, 5))].iterrows():
    fao = row['FAO_published_GgCH4']
    print(f"{int(row.Year):>5} | {row['Total_GgCH4']:>14.1f} | {fao:>14.1f} | "
          f"{row['Ratio_to_FAO']:>8.4f}")
print("-" * 55)
print("(all values in Gg CH4 = kt CH4 / year)")

# Species breakdown 2020
r2020 = df_global[df_global['Year']==2020].iloc[0]
tot2020 = r2020['Total_GgCH4']
print(f"\nSpecies breakdown (2020, global):")
for col in sp_gg_cols:
    sp = col.replace('_GgCH4','').replace('_',' ')
    val = r2020[col]
    pct = val / tot2020 * 100
    print(f"  {sp:20s}: {val:8.1f} Gg ({pct:.1f}%)")

# Regional breakdown 2020
print(f"\nRegional breakdown (2020):")
r2020_reg = df_regional[df_regional['Year']==2020][
    ['Region','Total_GgCH4']].sort_values('Total_GgCH4', ascending=False)
for _, row in r2020_reg.iterrows():
    pct = row['Total_GgCH4'] / tot2020 * 100
    print(f"  {row['Region']:25s}: {row['Total_GgCH4']:8.1f} Gg ({pct:.1f}%)")

print("\n[DONE] All outputs saved.")
print("  ch4_ef_global.csv   — 51 rows × global annual totals + FAO + ratio")
print("  ch4_ef_country.csv  — 10,710 rows × country × year × species")
print("  ch4_ef_regional.csv — regional annual totals")
print("  ch4_ef_species.csv  — species breakdown, all years")


# =============================================================================
# EDGAR EXTRACTION — add EDGAR_GgCH4 column to global CSV
# Source: EDGAR 2025, IPCC code 3.A.1
# =============================================================================
import pandas as _pd
import numpy as _np

_EDGAR_FILE = (str(EDGAR_CH4_NEW))
_YEARS_E = list(range(1970, 2021))
_YC_E    = [f'Y_{y}' for y in _YEARS_E]

_df_e = _pd.ExcelFile(_EDGAR_FILE).parse('IPCC 2006', header=9)
_sub  = _df_e[_df_e['ipcc_code_2006_for_standard_report'] == '3.A.1']
_edgar_vals = _sub[_YC_E].apply(_pd.to_numeric, errors='coerce').fillna(0).sum().values

_global_csv = (str(OUT_A_DATA) + '/ch4_ef/ch4_ef_global.csv')
_dg = _pd.read_csv(_global_csv)
_dg['EDGAR_GgCH4'] = _np.round(_edgar_vals, 3)
_dg.to_csv(_global_csv, index=False)
print(f'Added EDGAR_GgCH4 column to ch4_ef_global.csv')
print(f'  EDGAR 3.A.1 2020: {_edgar_vals[-1]:.1f} Gg')
