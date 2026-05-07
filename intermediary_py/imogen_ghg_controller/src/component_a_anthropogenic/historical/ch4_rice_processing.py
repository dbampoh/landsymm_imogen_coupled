
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
# CH4 EMISSIONS FROM RICE CULTIVATION — IPCC 2019 REFINEMENT TIER 1
# =============================================================================
#
# PURPOSE
# -------
# Implements the 2019 Refinement to the 2006 IPCC Guidelines for National GHG
# Inventories, Volume 4, Chapter 5, Section 5.5 (Tier 1) for methane (CH4)
# emissions from flooded rice cultivation. Applied at country level using
# FAO Production/Crops and Livestock activity data, 1970–2020.
#
# GOVERNING EQUATIONS
# -------------------
# Equation 5.1 — Total annual CH4 from rice cultivation:
#
#   CH4_Rice = Σ_{i,j,k} [ EF_{i,j,k} × t_{i,j,k} × A_{i,j,k} × 10^-6 ]
#
# Equation 5.2 (Tier 1) — Adjusted daily emission factor:
#
#   EF_i = EFc × SFw × SFp × SFo
#
# Equation 5.3 — Organic amendment scaling factor:
#
#   SFo = 1 + Σ_i [ (ROA_i × CFOA_i)^0.59 ]
#
# Where:
#   CH4_Rice  = annual emissions, Gg CH4 yr-1
#   EF_{i,j,k} = adjusted daily EF, kg CH4 ha-1 day-1
#   t_{i,j,k}  = cultivation period, days
#   A_{i,j,k}  = harvested area under conditions i,j,k, ha yr-1
#   EFc       = baseline daily EF, continuously flooded, no amendments
#               [Table 5.11 — region-specific, kg CH4 ha-1 day-1]
#   SFw       = water-regime scaling factor during cultivation [Table 5.12]
#   SFp       = pre-season water-regime scaling factor [Table 5.13]
#   SFo       = organic amendment scaling factor [Eq. 5.3 + Table 5.14]
#
# TIER 1 SIMPLIFICATIONS APPLIED
# --------------------------------
# 1. WATER REGIME: With no country-level water-regime split data in FAO,
#    we apply the AGGREGATED CASE SFw from Table 5.12 to produce three
#    emission-class sub-areas per country using the GCB/FAO-derived global
#    rice water regime fractions (Yan et al. 2005, updated in 2019 Annex 5A.2):
#      Irrigated:  65% of area (SFw = 0.60, aggregated irrigated case)
#      Rainfed:    30% of area (SFw = 0.45, aggregated rainfed/deep water)
#      Upland:      5% of area (SFw = 0.00, no significant flooding)
#
# 2. PRE-SEASON WATER REGIME: Without country-level data, we use SFp = 1.00
#    (Table 5.13 disaggregated case: "Non-flooded pre-season <180 days"),
#    which is the standard baseline condition for continuously-cultivated
#    irrigated rice and the IPCC default when no pre-season data exist.
#
# 3. ORGANIC AMENDMENTS: At Tier 1 without sub-national amendment data we
#    apply SFo = 1.00 for rainfed and upland; for irrigated rice we apply
#    a global-average straw incorporation rate of 2 t/ha (Yan et al. 2005,
#    as used in the worked example in Table 5.14b), giving:
#      SFo = 1 + (2 × 1.00)^0.59 = 1 + 2^0.59 = 1 + 1.508 = 2.508
#    NOTE: This makes irrigated rice emissions ~2.5× higher than no-amendment
#    baseline. This is appropriate for irrigated paddy systems where straw
#    incorporation is standard practice in Asia. For upland and rainfed
#    where straw is typically burned or removed, SFo = 1.00.
#
# 4. BASELINE EF: Table 5.11 provides REGION-SPECIFIC values (seven regions).
#    Countries are mapped to the seven rice sub-regions defined in the table.
#
# 5. CULTIVATION PERIOD: Table 5.11A provides REGION-SPECIFIC default periods.
#
# COMPARISON WITH FAO
# -------------------
# FAO's GLE methodology (post-2014) uses these same equations but applies
# country-specific irrigation/rainfed fractions from IRRI FAO datasets and
# applies SFo based on reported straw management practices. Our Tier 1
# uses global defaults where sub-national data are unavailable.
#
# WHAT IS NOT INCLUDED
# --------------------
#   • Deep-water rice (< 1% of global area) — excluded for simplicity;
#     its SFw = 0.06 makes its contribution negligible
#   • Pre-season CH4 from winter flooding — separate calculation per footnote b
#     in Table 5.13; excluded (FAO also excludes this from the rice item)
#   • Soil type and cultivar effects (SFs, SFr) — Tier 2 only
#
# INPUTS
# ------
#   Production_Crops_Livestock_E_All_Data.csv — FAO area harvested for rice
#     (item='Rice', element='Area harvested', unit='ha')
#
# OUTPUTS
# -------
#   ch4_rice_global.csv   — Global annual totals + FAO published + ratio
#   ch4_rice_country.csv  — Country × year results (Gg CH4)
#   ch4_rice_regional.csv — Regional annual totals (7 rice regions)
#   ch4_rice_waterclass.csv — Global split by water class (irrigated/rainfed/upland)
#
# REFERENCES
# ----------
#   IPCC (2019). 2019 Refinement, Vol. 4, Ch. 5, Section 5.5.
#     Equations 5.1, 5.2, 5.3; Tables 5.11, 5.11A, 5.12, 5.13, 5.14.
#   Yan et al. (2005). Global Biogeochemical Cycles 19:GB2010.
#   FAO (2023). FAOSTAT Emissions — Agriculture (GLE domain),
#     Rice Cultivation, Emissions (CH4).
# =============================================================================

import pandas as pd
import numpy as np

YEAR_START = 1970
YEAR_END   = 2020
YEAR_COLS  = [f'Y{y}' for y in range(YEAR_START, YEAR_END + 1)]
KG_TO_GG   = 1.0e-6   # 1 Gg = 10^6 kg

print("=" * 70)
print("CH4 FROM RICE CULTIVATION — IPCC 2019 REFINEMENT TIER 1")
print(f"Period: {YEAR_START}–{YEAR_END}   Countries: all FAO member states")
print("=" * 70)

# =============================================================================
# SECTION 1: LOAD FAO RICE AREA DATA
# =============================================================================
print("\n[1] Loading FAO rice area data...")
df_raw = pd.read_csv(
    str(FAO_PRODUCTION_CSV),
    low_memory=False
)
df_raw[YEAR_COLS] = df_raw[YEAR_COLS].fillna(0)
df_c = df_raw[df_raw['Area Code'] < 5000].copy()

# Rice harvested area (ha) — units confirmed from FAOSTAT documentation
rice_area_df = df_c[
    (df_c['Item'] == 'Rice') &
    (df_c['Element'] == 'Area harvested')
][['Area Code', 'Area'] + YEAR_COLS].copy().set_index('Area Code')

area_names = df_c.drop_duplicates('Area Code').set_index('Area Code')['Area'].to_dict()
area_codes = list(set(rice_area_df.index.tolist()))
print(f"    {len(area_codes)} countries with rice area data")
print(f"    Global 2020 rice area: {rice_area_df['Y2020'].sum()/1e6:.1f} million ha")

# =============================================================================
# SECTION 2: COUNTRY → RICE SUB-REGION MAPPING
# =============================================================================
# Table 5.11 defines SEVEN rice sub-regions for region-specific EFc and
# cultivation period. These differ from the livestock 9-region system.
# Countries not producing rice are omitted (their area is zero).
#
# RICE SUB-REGIONS (Table 5.11):
#   East Asia:     China, Japan, Korea (DPR & Rep.), Mongolia, Taiwan
#   Southeast Asia: ASEAN countries + Timor-Leste
#   South Asia:    India, Pakistan, Bangladesh, Nepal, Sri Lanka, Bhutan, Afghanistan
#   Europe:        All European countries (including Turkey, Russia)
#   North America: USA, Canada, Mexico (and Caribbean)
#   South America: All South American + Central American countries
#   Africa:        All African + Middle Eastern countries (Table 5.11 footnote 1:
#                  "For Africa, the global estimate is used due to lack of data")
# Countries not in any sub-region → Africa (global estimate as fallback)

EAST_ASIA = {
    'China','China, mainland','China, Hong Kong SAR','China, Macao SAR',
    'China, Taiwan Province of','Japan',
    "Democratic People's Republic of Korea",'North Korea',
    'Korea, Republic of','South Korea','Republic of Korea','Mongolia'
}

SOUTHEAST_ASIA = {
    'Brunei Darussalam','Cambodia','Indonesia',"Lao People's Democratic Republic",
    'Laos','Malaysia','Myanmar','Myanmar/Burma','Philippines','Singapore',
    'Thailand','Timor-Leste','Viet Nam','Vietnam'
}

SOUTH_ASIA = {
    'Afghanistan','Bangladesh','Bhutan','India','Maldives','Nepal','Pakistan','Sri Lanka'
}

EUROPE = {
    'Albania','Andorra','Austria','Belarus','Belgium','Belgium-Luxembourg',
    'Bosnia and Herzegovina','Bulgaria','Croatia','Cyprus','Czechia','Czech Republic',
    'Denmark','Estonia','Finland','France','France and Monaco','Georgia','Germany',
    'Greece','Hungary','Iceland','Ireland','Israel','Italy','Italy, San Marino and the Holy See',
    'Kazakhstan','Kyrgyzstan','Latvia','Lithuania','Luxembourg','Malta','Moldova',
    'Montenegro','Netherlands','North Macedonia','Norway','Poland','Portugal',
    'Romania','Russia','Serbia','Serbia and Montenegro','Slovakia','Slovenia',
    'Spain','Spain and Andorra','Sweden','Switzerland','Switzerland and Liechtenstein',
    'Tajikistan','Türkiye','Turkey','Turkmenistan','Ukraine','United Kingdom','Uzbekistan',
    'Armenia','Azerbaijan','Kosovo','Yugoslavia','Georgia','Lithuania'
}

NORTH_AMERICA = {
    'United States of America','Canada','Mexico','Guatemala','Belize',
    'Honduras','El Salvador','Nicaragua','Costa Rica','Panama',
    'Cuba','Dominican Republic','Haiti','Jamaica','Puerto Rico',
    'Antigua and Barbuda','Barbados','Dominica','Grenada',
    'Saint Kitts and Nevis','Saint Lucia','Saint Vincent and the Grenadines',
    'Trinidad and Tobago','Bahamas','Bermuda','Greenland',
    'Saint Pierre and Miquelon','Aruba','Netherlands Antilles','Cayman Islands'
}

SOUTH_AMERICA = {
    'Argentina','Bolivia','Bolivia (Plurinational State of)','Brazil','Chile',
    'Colombia','Ecuador','Guyana','Paraguay','Peru','Suriname','Uruguay',
    'Venezuela','Venezuela (Bolivarian Republic of)','French Guiana'
}

def get_rice_region(country):
    """Map a country to one of the seven rice sub-regions in Table 5.11."""
    if country in EAST_ASIA:       return 'East Asia'
    if country in SOUTHEAST_ASIA:  return 'Southeast Asia'
    if country in SOUTH_ASIA:      return 'South Asia'
    if country in EUROPE:          return 'Europe'
    if country in NORTH_AMERICA:   return 'North America'
    if country in SOUTH_AMERICA:   return 'South America'
    return 'Africa'   # all remaining: sub-Saharan Africa, Middle East, Oceania,
                      # Central Asia → use global estimate per Table 5.11 footnote 1

area_region = {ac: get_rice_region(area_names.get(ac,'')) for ac in area_codes}
print(f"\n[2] Rice sub-region mapping complete ({len(set(area_region.values()))} regions)")

# =============================================================================
# SECTION 3: EMISSION FACTORS AND PARAMETERS — ALL FROM PDF TABLES
# =============================================================================

# ---------------------------------------------------------------------------
# 3A. BASELINE EMISSION FACTOR (EFc) — Table 5.11 (2019 Updated)
# ---------------------------------------------------------------------------
# Units: kg CH4 ha-1 day-1
# Definition: continuously flooded fields, no pre-season flooding >180 days,
#             no organic amendments
# World-average: 1.19 kg CH4 ha-1 day-1 (used for Africa = global estimate)
#
# IMPORTANT CHANGE from 2006: the 2019 Refinement substantially revised
# these EFc values using a new, larger database (updated Yan et al. 2005 dataset
# extended through June 2017) and a new statistical model with random effects.
# Key changes: North America decreased from 0.99 to 0.65; East Asia increased
# from 0.98 to 1.32; South Asia decreased from 1.24 to 0.85.

EFC = {
    'East Asia':     1.32,   # [0.89–1.96]
    'Southeast Asia':1.22,   # [0.83–1.81]
    'South Asia':    0.85,   # [0.58–1.26]
    'Europe':        1.56,   # [1.06–2.31]
    'North America': 0.65,   # [0.44–0.96]
    'South America': 1.27,   # [0.86–1.88]
    'Africa':        1.19,   # [0.80–1.76] — global estimate (Table 5.11 footnote 1)
}

# ---------------------------------------------------------------------------
# 3B. CULTIVATION PERIOD — Table 5.11A (NEW in 2019)
# ---------------------------------------------------------------------------
# Units: days
# Default cultivation period for each region. Previously (2006 Guidelines)
# a global default of 120 days was used; the 2019 Refinement now provides
# region-specific values derived from the updated measurement database.

T_DAYS = {
    'East Asia':     112,   # [73–147]
    'Southeast Asia':102,   # [78–150]
    'South Asia':    112,   # [90–140]
    'Europe':        123,   # [111–153]
    'North America': 139,   # [110–165]
    'South America': 124,   # [110–146]
    'Africa':        113,   # [74–152] — global estimate (Table 5.11A footnote 1)
}

# ---------------------------------------------------------------------------
# 3C. WATER REGIME SCALING FACTORS (SFw) — Table 5.12 (2019 Updated)
# ---------------------------------------------------------------------------
# Aggregated case SFw — applied when only rice ecosystem type (irrigated/
# rainfed/upland) is known, not detailed flooding pattern.
#
# Irrigated (aggregated case):   0.60  [0.44–0.78]
#   Represents a blend of continuously flooded and single-drainage systems.
#   Under the aggregated case, all irrigated rice uses this single SFw.
# Rainfed + deep water (agg.):   0.45  [0.32–0.62]
#   Represents regular rainfed + some deep water contribution.
# Upland:                        0.00  (never flooded — no CH4 production)
#
# NOTE: The continuously flooded disaggregated SFw = 1.00 by definition
# (it IS the reference condition for EFc).

SFW_IRRIGATED = 0.60   # aggregated case, Table 5.12
SFW_RAINFED   = 0.45   # aggregated case, Table 5.12
SFW_UPLAND    = 0.00   # Table 5.12 — zero emissions (never flooded)

# ---------------------------------------------------------------------------
# 3D. PRE-SEASON WATER REGIME (SFp) — Table 5.13 (2019 Updated)
# ---------------------------------------------------------------------------
# Without country-level data on pre-season water status, we use the
# disaggregated case value for "Non-flooded pre-season <180 days" = 1.00.
# This is the standard baseline condition:
#   • Irrigated double-cropped: typically <180 days non-flooded between seasons
#   • It equals 1.0 in the disaggregated column, meaning EFc is not adjusted
# The aggregated case for flooded pre-season (1.22) would only apply if
# we knew the pre-season was flooded, which we don't at Tier 1 globally.

SFP_DEFAULT = 1.00   # disaggregated: non-flooded pre-season <180 days

# ---------------------------------------------------------------------------
# 3E. ORGANIC AMENDMENT SCALING FACTOR (SFo) — Eq. 5.3 + Table 5.14
# ---------------------------------------------------------------------------
# SFo = 1 + Σ_i [ (ROA_i × CFOA_i)^0.59 ]
#
# For irrigated rice fields, straw incorporation is the dominant organic
# amendment globally. Yan et al. (2005) report a global median of ~2 t/ha
# dry straw incorporated before planting (consistent with the worked example
# in Tables 5.14a-5.14c in the 2019 Refinement).
#
# CFOA for straw incorporated shortly before cultivation = 1.00 (Table 5.14)
# ROA = 2.0 t/ha (dry weight)
# SFo = 1 + (2.0 × 1.00)^0.59 = 1 + 2^0.59 = 1 + 1.508 = 2.508

ROA_STRAW     = 2.0    # tonne ha-1 (dry weight), global median from Yan et al.
CFOA_STRAW    = 1.00   # straw incorporated <30 days before cultivation, Table 5.14
EXP_SFO       = 0.59   # exponent in Equation 5.3

SFO_IRRIGATED = 1.0 + (ROA_STRAW * CFOA_STRAW) ** EXP_SFO
SFO_RAINFED   = 1.00   # rainfed/upland: straw typically burned or removed
SFO_UPLAND    = 1.00

print(f"\n[3] Parameters loaded from Tables 5.11, 5.11A, 5.12, 5.13, 5.14:")
print(f"    EFc range: {min(EFC.values())}–{max(EFC.values())} kg CH4/ha/day")
print(f"    T range:   {min(T_DAYS.values())}–{max(T_DAYS.values())} days")
print(f"    SFw:       irrigated={SFW_IRRIGATED}, rainfed={SFW_RAINFED}, upland={SFW_UPLAND}")
print(f"    SFp:       {SFP_DEFAULT} (non-flooded pre-season <180d baseline)")
print(f"    SFo:       irrigated={{SFO_IRRIGATED:.4f}} (2t/ha straw), rainfed={SFO_RAINFED}")

# ---------------------------------------------------------------------------
# 3F. WATER REGIME AREA FRACTIONS
# ---------------------------------------------------------------------------
# Global-average fractions of rice area by water regime, adapted from the
# IRRI World Rice Statistics and FAO 2014 GLEAM rice module:
#   Irrigated:  ~65% of global harvested area
#   Rainfed:    ~30% of global harvested area
#   Upland:     ~5%  of global harvested area
# Source: Laborte et al. (2012); Heffer (2013); Yan et al. (2005, Table 1)
# These fractions are applied uniformly because sub-national water regime
# breakdowns are not available in FAOSTAT Production data.
# Regional variation could be applied at Tier 2 with IRRI data.

FRAC_IRRIGATED = 0.65
FRAC_RAINFED   = 0.30
FRAC_UPLAND    = 0.05

# ---------------------------------------------------------------------------
# 3G. PRE-COMPUTE ADJUSTED DAILY EF PER REGION × WATER CLASS
# ---------------------------------------------------------------------------
# EF_i = EFc × SFw × SFp × SFo   (Equation 5.2)
# This gives three EF values per region.
# CH4_Rice = EF_i × t × A_sub × 10^-6   (Equation 5.1)

print("\n    Adjusted daily EFs by region and water class (kg CH4 ha-1 day-1):")
adj_ef = {}   # {region: {'irrigated': EFi, 'rainfed': EFi, 'upland': EFi}}
for region in EFC:
    efc = EFC[region]
    ef_irr  = efc * SFW_IRRIGATED * SFP_DEFAULT * SFO_IRRIGATED
    ef_rain = efc * SFW_RAINFED   * SFP_DEFAULT * SFO_RAINFED
    ef_up   = efc * SFW_UPLAND    * SFP_DEFAULT * SFO_UPLAND
    adj_ef[region] = {
        'irrigated': ef_irr,
        'rainfed':   ef_rain,
        'upland':    ef_up,
    }
    print(f"    {region:15s}: irrig={ef_irr:.4f}  rainfed={ef_rain:.4f}  upland={ef_up:.4f}")

# =============================================================================
# SECTION 4: UTILITY FUNCTION
# =============================================================================
def gv(df_s, ac, yr_col):
    """Safely retrieve a value for a given area code and year."""
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
# SECTION 5: MAIN COMPUTATION LOOP
# =============================================================================
# For each country × year:
#   1. Get total harvested rice area (ha)
#   2. Split into irrigated/rainfed/upland sub-areas
#   3. Apply Equation 5.1: CH4 = EF_i × t × A_sub × 10^-6
#   4. Sum across water classes

print(f"\n[4] Running computation...")
print(f"    {len(area_codes)} countries × {len(YEAR_COLS)} years")

records = []

for ac in area_codes:
    country = area_names.get(ac, '')
    region  = area_region[ac]
    t_days  = T_DAYS[region]
    ef_i    = adj_ef[region]

    for yr in YEAR_COLS:
        year = int(yr[1:])

        # Total rice harvested area (ha)
        area_total = gv(rice_area_df, ac, yr)
        if area_total <= 0:
            records.append({
                'Year': year, 'Area Code': ac, 'Area': country,
                'Region': region, 'Rice_Region': region,
                'Total_GgCH4': 0.0, 'Irrigated_GgCH4': 0.0,
                'Rainfed_GgCH4': 0.0, 'Upland_GgCH4': 0.0
            })
            continue

        # Sub-area by water class (ha)
        a_irr  = area_total * FRAC_IRRIGATED
        a_rain = area_total * FRAC_RAINFED
        a_up   = area_total * FRAC_UPLAND

        # Equation 5.1 applied to each water class
        # CH4 = EF_i × t × A × 10^-6  [result in Gg CH4]
        ch4_irr  = ef_i['irrigated'] * t_days * a_irr  * KG_TO_GG
        ch4_rain = ef_i['rainfed']   * t_days * a_rain * KG_TO_GG
        ch4_up   = ef_i['upland']    * t_days * a_up   * KG_TO_GG   # = 0 (SFw=0)
        ch4_tot  = ch4_irr + ch4_rain + ch4_up

        records.append({
            'Year':            year,
            'Area Code':       ac,
            'Area':            country,
            'Region':          region,
            'Rice_Region':     region,
            'Area_ha':         area_total,
            'Total_GgCH4':     ch4_tot,
            'Irrigated_GgCH4': ch4_irr,
            'Rainfed_GgCH4':   ch4_rain,
            'Upland_GgCH4':    ch4_up,
        })

print(f"    {len(records):,} country-year records computed")

# =============================================================================
# SECTION 6: AGGREGATE AND COMPARE
# =============================================================================
print("\n[5] Aggregating results...")

df_out = pd.DataFrame(records)

# Global annual totals
gg_cols = ['Total_GgCH4','Irrigated_GgCH4','Rainfed_GgCH4','Upland_GgCH4']
df_global = df_out.groupby('Year')[gg_cols].sum().reset_index()

# FAO published reference (kt CH4 = Gg CH4)
# Source: FAOSTAT GLE domain, Rice Cultivation, Emissions (CH4), FAO TIER 1
FAO_RICE_CH4 = {
    1970:20026.8, 1971:20387.1, 1972:20046.7, 1973:20722.6, 1974:20864.4,
    1975:21473.9, 1976:21432.8, 1977:21650.0, 1978:21688.2, 1979:21359.5,
    1980:21779.7, 1981:21878.5, 1982:21374.9, 1983:21421.1, 1984:21718.9,
    1985:21666.1, 1986:21677.1, 1987:21258.4, 1988:21954.5, 1989:22386.0,
    1990:22173.4, 1991:22072.9, 1992:22240.0, 1993:22042.8, 1994:22263.2,
    1995:22668.4, 1996:22919.6, 1997:23052.6, 1998:22936.4, 1999:23835.0,
    2000:23324.3, 2001:23023.7, 2002:22518.6, 2003:22493.1, 2004:22974.7,
    2005:23478.4, 2006:23546.0, 2007:23528.4, 2008:24132.8, 2009:23956.8,
    2010:24418.4, 2011:24506.4, 2012:24416.5, 2013:24644.0, 2014:24497.9,
    2015:24186.1, 2016:24316.5, 2017:24400.1, 2018:24552.4, 2019:24070.9,
    2020:24683.6,
}
df_global['FAO_published_GgCH4'] = df_global['Year'].map(FAO_RICE_CH4)
df_global['Ratio_to_FAO'] = df_global['Total_GgCH4'] / df_global['FAO_published_GgCH4']

# Regional totals
df_regional = df_out.groupby(['Year','Rice_Region'])[gg_cols].sum().reset_index()

# Water class fractions as a separate summary
df_water = df_global[['Year','Irrigated_GgCH4','Rainfed_GgCH4','Upland_GgCH4',
                       'Total_GgCH4','FAO_published_GgCH4','Ratio_to_FAO']].copy()
df_water['Pct_Irrigated'] = df_water['Irrigated_GgCH4'] / df_water['Total_GgCH4'] * 100
df_water['Pct_Rainfed']   = df_water['Rainfed_GgCH4']   / df_water['Total_GgCH4'] * 100

# =============================================================================
# SECTION 7: SAVE OUTPUTS
# =============================================================================
df_global.to_csv((str(OUT_A_DATA) + '/ch4_rice/ch4_rice_global.csv'), index=False)
df_out[['Year','Area Code','Area','Rice_Region','Area_ha'] + gg_cols].to_csv(
    (str(OUT_A_DATA) + '/ch4_rice/ch4_rice_country.csv'), index=False)
df_regional.to_csv((str(OUT_A_DATA) + '/ch4_rice/ch4_rice_regional.csv'), index=False)
df_water.to_csv((str(OUT_A_DATA) + '/ch4_rice/ch4_rice_waterclass.csv'), index=False)

# =============================================================================
# SECTION 8: SUMMARY TABLE
# =============================================================================
print("\n" + "=" * 75)
print("GLOBAL CH4 FROM RICE CULTIVATION — IPCC 2019 REFINEMENT TIER 1")
print("=" * 75)
print(f"{'Year':>5} | {'Our estimate':>14} | {'FAO published':>14} | {'Ratio':>8}")
print("-" * 55)
for _, row in df_global[df_global['Year'].isin(range(1970, 2021, 5))].iterrows():
    fao = row['FAO_published_GgCH4']
    print(f"{int(row.Year):>5} | {row['Total_GgCH4']:>14.1f} | {fao:>14.1f} | "
          f"{row['Ratio_to_FAO']:>8.4f}")
print("-" * 55)
print("(Gg CH4 = kt CH4 / year)")

print("\nWater class split of our estimate (2020):")
r2020 = df_global[df_global['Year'] == 2020].iloc[0]
print(f"  Irrigated: {r2020['Irrigated_GgCH4']:,.1f} Gg  "
      f"({r2020['Irrigated_GgCH4']/r2020['Total_GgCH4']*100:.1f}%)")
print(f"  Rainfed:   {r2020['Rainfed_GgCH4']:,.1f} Gg  "
      f"({r2020['Rainfed_GgCH4']/r2020['Total_GgCH4']*100:.1f}%)")
print(f"  Upland:    {r2020['Upland_GgCH4']:,.1f} Gg  "
      f"({r2020['Upland_GgCH4']/r2020['Total_GgCH4']*100:.1f}%)")

print("\nTop rice CH4 countries, 2020 (from our estimate):")
country2020 = df_out[df_out['Year'] == 2020].sort_values('Total_GgCH4', ascending=False)
for _, row in country2020.head(12).iterrows():
    print(f"  {row['Area']:35s}: {row['Total_GgCH4']:6.0f} Gg CH4")

print("\nRegional breakdown (2020):")
r_2020 = df_regional[df_regional['Year'] == 2020].sort_values('Total_GgCH4', ascending=False)
tot_2020 = r2020['Total_GgCH4']
for _, row in r_2020.iterrows():
    pct = row['Total_GgCH4'] / tot_2020 * 100
    print(f"  {row['Rice_Region']:15s}: {row['Total_GgCH4']:7.1f} Gg ({pct:.1f}%)")

print("\n[DONE] All outputs saved.")
print("  ch4_rice_global.csv     — 51 rows × global annual totals + FAO + ratio")
print("  ch4_rice_country.csv    — country × year × water class breakdown")
print("  ch4_rice_regional.csv   — 7 rice sub-regions × year")
print("  ch4_rice_waterclass.csv — global water class contributions all years")


# =============================================================================
# EDGAR EXTRACTION — add EDGAR_GgCH4 column to global CSV
# Source: EDGAR 2025, IPCC code 3.C.7
# =============================================================================
import pandas as _pd
import numpy as _np

_EDGAR_FILE = (str(EDGAR_CH4_NEW))
_YEARS_E = list(range(1970, 2021))
_YC_E    = [f'Y_{y}' for y in _YEARS_E]

_df_e = _pd.ExcelFile(_EDGAR_FILE).parse('IPCC 2006', header=9)
_sub  = _df_e[_df_e['ipcc_code_2006_for_standard_report'] == '3.C.7']
_edgar_vals = _sub[_YC_E].apply(_pd.to_numeric, errors='coerce').fillna(0).sum().values

_global_csv = (str(OUT_A_DATA) + '/ch4_rice/ch4_rice_global.csv')
_dg = _pd.read_csv(_global_csv)
_dg['EDGAR_GgCH4'] = _np.round(_edgar_vals, 3)
_dg.to_csv(_global_csv, index=False)
print(f'Added EDGAR_GgCH4 column to ch4_rice_global.csv')
print(f'  EDGAR 3.C.7 2020: {_edgar_vals[-1]:.1f} Gg')
