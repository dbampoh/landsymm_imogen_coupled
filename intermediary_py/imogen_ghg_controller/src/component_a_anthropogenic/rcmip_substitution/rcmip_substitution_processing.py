"""
rcmip_substitution_processing.py
==================================
Assembles the RCMIP pre/post-substitution trajectories for CH4 and N2O,
covering 1900–2100 for 5 SSP scenarios.

METHODOLOGY
-----------
Three time periods are handled differently:

  1900–1969  (pre-inventory):
    No independent agricultural estimate available.
    Our_agri(t) = RCMIP_agri(t)  [no change; New_total = RCMIP_total]

  1970–2020  (historical inventory period):
    Our_agri(t) = Our IPCC Tier 1 historical bottom-up estimate
                  (summed across all modelled sectors per gas)
    Source: historical global CSV files from standalone packages

  2020–2100  (scenario period):
    Our_agri(t, SSP) = PLUMv2 s1 scenario estimates
                       (summed across all modelled sectors per gas)
    Source: scenario global CSV files from standalone packages

SUBSTITUTION ALGEBRA
--------------------
    RCMIP_agri(t, SSP)     = Emissions|CH4|MAGICC AFOLU|Agriculture  [CH4]
                             = Emissions|N2O|MAGICC AFOLU              [N2O]
    RCMIP_nonagri(t, SSP)  = RCMIP_total(t, SSP) − RCMIP_agri(t, SSP)
    New_total(t, SSP)      = RCMIP_nonagri(t, SSP) + Our_agri(t, SSP)

CH4 SECTORS SUMMED (historical + scenario)
------------------------------------------
    CH4:  Enteric Fermentation + Manure Management + Rice Cultivation
          Historical:  Total_GgCH4 from each sector global CSV
          Scenario:    CH4_GgCH4 from each sector global CSV
          Rice:        Option B (IrrigAmount split) used

N2O SECTORS SUMMED (historical + scenario)
------------------------------------------
    N2O:  Manure Management + Synthetic Fertilizers + Managed Soils
          Historical:  Total_2006split_GgN2O (MM), Total_2019clim_GgN2O (Synfert),
                       Total_withPRP_2019_GgN2O (MS)
          Scenario:    N2O_GgN2O (MM), N2O_total_GgN2O (Synfert, MS)

    NOTE: Historical N2O MM uses 2006-split parameters (633 Gg at 2020) which
    gives the reference-case estimate shown in historical plots. The scenario
    N2O MM uses 2019 Refinement parameters (750.6 Gg at 2020, SSP2) which are
    methodologically more rigorous. A small discontinuity at 2020 is therefore
    expected and is documented. Similarly, historical CH4 uses FAO country-level
    activity data (wider coverage) while scenario uses PLUM 158-region coverage,
    producing offsets documented in the sector processing scripts.

RCMIP VARIABLES USED
---------------------
    CH4 agri:  'Emissions|CH4|MAGICC AFOLU|Agriculture'
    CH4 total: 'Emissions|CH4'
    N2O agri:  'Emissions|N2O|MAGICC AFOLU'
    N2O total: 'Emissions|N2O'
    Region:    'World'

UNITS
-----
    All output in Mt gas / yr (Mt CH4/yr, Mt N2O/yr)
    Input RCMIP CH4 in Mt CH4/yr (direct)
    Input RCMIP N2O in kt N2O/yr → divide by 1000 → Mt N2O/yr
    Input historical/scenario in Gg/yr → divide by 1000 → Mt/yr

RCMIP TEMPORAL STRUCTURE
-------------------------
    Historical: annual 1750–2014
    Scenarios:  annual 2010–2015, then 5-yearly 2015,2020,2030,...,2100
    This script:  interpolates linearly to annual 1900–2100 and splices
                  historical (1900–2014) + SSP (2015–2100)

SSP MAPPING
-----------
    SSP1_RCP26_s1 → ssp126
    SSP2_RCP45_s1 → ssp245
    SSP3_RCP70_s1 → ssp370
    SSP4_RCP60_s1 → ssp460
    SSP5_RCP85_s1 → ssp585

OUTPUT FILES
------------
    rcmip_substitution_ch4.csv
    rcmip_substitution_n2o.csv
    Each has columns: Year, Scenario, RCMIP_total, RCMIP_agri, RCMIP_nonagri,
                      Our_agri, New_total  [all in Mt gas/yr]
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
    OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES, RCMIP_CSV as RCMIP_CSV_PATH,
)

import pandas as pd
import numpy as np
import os

# =============================================================================
# SECTION 0: PATHS
# =============================================================================
HERE        = os.path.dirname(os.path.abspath(__file__))
HIST_DIR    = str(OUT_A_DATA)                                # historical sector outputs
SCEN_DIR    = os.path.join(str(OUT_A_DATA), 'scenario_pipeline')  # flat scenario CSVs
RCMIP_CSV   = str(RCMIP_CSV_PATH)

SCEN_MAP = {          # Our PLUMv2 key → RCMIP scenario name
    'SSP1_RCP26_s1': 'ssp126',
    'SSP2_RCP45_s1': 'ssp245',
    'SSP3_RCP70_s1': 'ssp370',
    'SSP4_RCP60_s1': 'ssp460',
    'SSP5_RCP85_s1': 'ssp585',
}
SCEN_LABELS = {
    'SSP1_RCP26_s1': 'SSP1-2.6',
    'SSP2_RCP45_s1': 'SSP2-4.5',
    'SSP3_RCP70_s1': 'SSP3-7.0',
    'SSP4_RCP60_s1': 'SSP4-6.0',
    'SSP5_RCP85_s1': 'SSP5-8.5',
}

PLOT_YEARS = list(range(1900, 2101))   # 201 annual values

# =============================================================================
# SECTION 1: LOAD AND INTERPOLATE RCMIP DATA
# =============================================================================
print("Loading RCMIP data ...")
df_r = pd.read_csv(RCMIP_CSV, low_memory=False)

ALL_YR_COLS = [c for c in df_r.columns if c.isdigit()]

def rcmip_annual(variable, scenario, unit_scale=1.0):
    """
    Extract and interpolate RCMIP series to annual 1900-2100.
    Splices: historical through 2014, SSP scenario from 2015 onward.
    unit_scale: 1.0 for CH4 (already Mt); 1/1000 for N2O (kt → Mt).
    Returns dict {year: value}.
    """
    # Historical series
    r_hist = df_r[(df_r['Variable'] == variable) &
                  (df_r['Region'] == 'World') &
                  (df_r['Scenario'] == 'historical')]
    # Scenario series
    r_ssp  = df_r[(df_r['Variable'] == variable) &
                  (df_r['Region'] == 'World') &
                  (df_r['Scenario'] == scenario)]

    if not len(r_hist) or not len(r_ssp):
        return {y: np.nan for y in PLOT_YEARS}

    # Build annual dict from non-NaN values (historical is already annual)
    hist_vals = {int(c): r_hist[c].values[0] * unit_scale
                 for c in ALL_YR_COLS
                 if c.isdigit() and 1900 <= int(c) <= 2014
                 and not pd.isna(r_hist[c].values[0])}

    ssp_vals  = {int(c): r_ssp[c].values[0] * unit_scale
                 for c in ALL_YR_COLS
                 if c.isdigit() and 2015 <= int(c) <= 2100
                 and not pd.isna(r_ssp[c].values[0])}

    # Linear interpolation within each set of anchor points
    def interp_dict(anchors, years):
        out = {}
        sorted_a = sorted(anchors)
        for k in range(len(sorted_a) - 1):
            y0, y1 = sorted_a[k], sorted_a[k+1]
            v0, v1 = anchors[y0], anchors[y1]
            for y in range(y0, y1 + 1):
                if y0 <= y <= y1:
                    out[y] = v0 + (y - y0) / (y1 - y0) * (v1 - v0)
        return out

    hist_interp = interp_dict(hist_vals, range(1900, 2015))
    ssp_interp  = interp_dict(ssp_vals,  range(2015, 2101))

    return {y: hist_interp.get(y, ssp_interp.get(y, np.nan))
            for y in PLOT_YEARS}

# Pre-load all required RCMIP series for all SSPs
print("  Interpolating RCMIP series to annual 1900-2100 ...")
rcmip = {}
for plum_s, rcmip_s in SCEN_MAP.items():
    rcmip[plum_s] = {
        'CH4_total':  rcmip_annual('Emissions|CH4',
                                    rcmip_s, unit_scale=1.0),
        'CH4_agri':   rcmip_annual('Emissions|CH4|MAGICC AFOLU|Agriculture',
                                    rcmip_s, unit_scale=1.0),
        'N2O_total':  rcmip_annual('Emissions|N2O',
                                    rcmip_s, unit_scale=1/1000),
        'N2O_agri':   rcmip_annual('Emissions|N2O|MAGICC AFOLU',
                                    rcmip_s, unit_scale=1/1000),
    }

# Spot-check
print(f"  CH4 total SSP2-4.5: 1970={rcmip['SSP2_RCP45_s1']['CH4_total'][1970]:.1f} "
      f"2020={rcmip['SSP2_RCP45_s1']['CH4_total'][2020]:.1f} "
      f"2100={rcmip['SSP2_RCP45_s1']['CH4_total'][2100]:.1f} Mt CH4")
print(f"  CH4 agri SSP2-4.5:  1970={rcmip['SSP2_RCP45_s1']['CH4_agri'][1970]:.1f} "
      f"2020={rcmip['SSP2_RCP45_s1']['CH4_agri'][2020]:.1f} "
      f"2100={rcmip['SSP2_RCP45_s1']['CH4_agri'][2100]:.1f} Mt CH4")
print(f"  N2O total SSP2-4.5: 1970={rcmip['SSP2_RCP45_s1']['N2O_total'][1970]:.3f} "
      f"2020={rcmip['SSP2_RCP45_s1']['N2O_total'][2020]:.3f} "
      f"2100={rcmip['SSP2_RCP45_s1']['N2O_total'][2100]:.3f} Mt N2O")

# =============================================================================
# SECTION 2: LOAD HISTORICAL TIER 1 SECTOR TOTALS (1970-2020)
# =============================================================================
print("\nLoading historical Tier 1 sector totals ...")

d_ef  = pd.read_csv(os.path.join(HIST_DIR,'ch4_ef','ch4_ef_global.csv'))
d_mm4 = pd.read_csv(os.path.join(HIST_DIR,'ch4_mm','ch4_mm_global.csv'))
d_rc4 = pd.read_csv(os.path.join(HIST_DIR,'ch4_rice','ch4_rice_global.csv'))
d_mm2 = pd.read_csv(os.path.join(HIST_DIR,'n2o_mm','n2o_mm_global.csv'))
d_sf2 = pd.read_csv(os.path.join(HIST_DIR,'n2o_synfert','n2o_synfert_global.csv'))
d_ms2 = pd.read_csv(os.path.join(HIST_DIR,'n2o_ms','n2o_ms_global.csv'))

# CH4 total: EF + MM + Rice (Gg → Mt)
# Use primary "Total_GgCH4" column (2019 params where available)
hist_ch4 = {}
for _, row in d_ef.iterrows():
    y = int(row['Year'])
    hist_ch4[y] = (row['Total_GgCH4']
                 + d_mm4[d_mm4['Year']==y]['Total_GgCH4'].values[0]
                 + d_rc4[d_rc4['Year']==y]['Total_GgCH4'].values[0]) / 1000.

# N2O total: MM + Synfert + MS (Gg → Mt)
# MM: Total_2006split_GgN2O (our reference case benchmarked against FAO)
# Synfert: Total_2019clim_GgN2O (2019 params with climate-zone leaching)
# MS: Total_withPRP_2019_GgN2O (2019 params, with PRP component)
hist_n2o = {}
for _, row in d_mm2.iterrows():
    y = int(row['Year'])
    hist_n2o[y] = (row['Total_2006split_GgN2O']
                 + d_sf2[d_sf2['Year']==y]['Total_2019clim_GgN2O'].values[0]
                 + d_ms2[d_ms2['Year']==y]['Total_withPRP_2019_GgN2O'].values[0]) / 1000.

print(f"  Historical CH4 (EF+MM+Rice): "
      f"1970={hist_ch4[1970]:.1f}  2020={hist_ch4[2020]:.1f} Mt")
print(f"  Historical N2O (MM+Syn+MS):  "
      f"1970={hist_n2o[1970]:.3f}  2020={hist_n2o[2020]:.3f} Mt")

# =============================================================================
# SECTION 3: LOAD SCENARIO SECTOR TOTALS (2020-2100)
# =============================================================================
print("\nLoading scenario sector totals ...")

ds_ef  = pd.read_csv(os.path.join(SCEN_DIR,'scenario_ch4_ef_global.csv'))
ds_mm4 = pd.read_csv(os.path.join(SCEN_DIR,'scenario_ch4_mm_global.csv'))
ds_rc4 = pd.read_csv(os.path.join(SCEN_DIR,'scenario_ch4_rice_global.csv'))
ds_mm2 = pd.read_csv(os.path.join(SCEN_DIR,'scenario_n2o_mm_global.csv'))
ds_sf2 = pd.read_csv(os.path.join(SCEN_DIR,'scenario_n2o_synfert_global.csv'))
ds_ms2 = pd.read_csv(os.path.join(SCEN_DIR,'scenario_n2o_ms_global.csv'))

# Build scenario dicts: {SSP_key: {year: value_Mt}}
scen_ch4 = {s: {} for s in SCEN_MAP}
scen_n2o = {s: {} for s in SCEN_MAP}

for s in SCEN_MAP:
    for y in range(2020, 2101):
        def gv(df, col):
            sub = df[(df['Scenario']==s) & (df['Year']==y)]
            return sub[col].values[0] if len(sub) else 0.

        scen_ch4[s][y] = (gv(ds_ef,  'CH4_GgCH4')
                        + gv(ds_mm4, 'CH4_GgCH4')
                        + gv(ds_rc4, 'CH4_GgCH4')) / 1000.

        scen_n2o[s][y] = (gv(ds_mm2, 'N2O_GgN2O')
                        + gv(ds_sf2, 'N2O_total_GgN2O')
                        + gv(ds_ms2, 'N2O_total_GgN2O')) / 1000.

# Spot-check
s2 = 'SSP2_RCP45_s1'
print(f"  Scenario CH4 SSP2: 2020={scen_ch4[s2][2020]:.1f}  "
      f"2050={scen_ch4[s2][2050]:.1f}  2100={scen_ch4[s2][2100]:.1f} Mt")
print(f"  Scenario N2O SSP2: 2020={scen_n2o[s2][2020]:.3f}  "
      f"2050={scen_n2o[s2][2050]:.3f}  2100={scen_n2o[s2][2100]:.3f} Mt")

# =============================================================================
# SECTION 4: ASSEMBLE COMBINED "OUR AGRI" SERIES PER SCENARIO
# =============================================================================
# For each SSP scenario and each year:
#   1900-1969: Our_agri = RCMIP_agri  (no substitution, pre-inventory)
#   1970-2019: Our_agri = hist_ch4 / hist_n2o  (historical Tier 1, interpolated annually)
#   2020-2100: Our_agri = scen_ch4 / scen_n2o  (PLUMv2 scenario, annual)
# Note: at 2020 we use the SCENARIO value (anchors to PLUMv2 at 2020)
# The 1970-2020 historical is already annual (one value per year)

def build_our_agri(gas, plum_scen, hist_dict, scen_dict, rcmip_agri_dict):
    """Build combined Our_agri series for one gas and one SSP."""
    out = {}
    for y in PLOT_YEARS:
        if y < 1970:
            out[y] = rcmip_agri_dict[y]   # RCMIP baseline pre-inventory
        elif y < 2020:
            out[y] = hist_dict.get(y, np.nan)
        else:
            out[y] = scen_dict.get(y, np.nan)
    return out

# =============================================================================
# SECTION 5: BUILD OUTPUT DATAFRAMES
# =============================================================================
print("\nAssembling substitution trajectories ...")

records_ch4 = []
records_n2o = []

for plum_s, rcmip_s in SCEN_MAP.items():
    label = SCEN_LABELS[plum_s]
    r_ch4 = rcmip[plum_s]
    r_n2o = rcmip[plum_s]

    our_ch4 = build_our_agri('CH4', plum_s, hist_ch4, scen_ch4[plum_s],
                              r_ch4['CH4_agri'])
    our_n2o = build_our_agri('N2O', plum_s, hist_n2o, scen_n2o[plum_s],
                              r_n2o['N2O_agri'])

    for y in PLOT_YEARS:
        rc_tot = r_ch4['CH4_total'][y]
        rc_ag  = r_ch4['CH4_agri'][y]
        rc_non = rc_tot - rc_ag if not np.isnan(rc_tot + rc_ag) else np.nan
        our_a  = our_ch4[y]
        new_t  = rc_non + our_a if not np.isnan(rc_non + our_a) else np.nan

        records_ch4.append({
            'Year':           y,
            'Scenario':       label,
            'RCMIP_total':    round(rc_tot,  4),
            'RCMIP_agri':     round(rc_ag,   4),
            'RCMIP_nonagri':  round(rc_non,  4),
            'Our_agri':       round(our_a,   4),
            'New_total':      round(new_t,   4),
            'Period':         ('pre-inventory' if y < 1970
                               else 'historical'  if y < 2020
                               else 'scenario'),
        })

        rn_tot = r_n2o['N2O_total'][y]
        rn_ag  = r_n2o['N2O_agri'][y]
        rn_non = rn_tot - rn_ag if not np.isnan(rn_tot + rn_ag) else np.nan
        our_a2 = our_n2o[y]
        new_t2 = rn_non + our_a2 if not np.isnan(rn_non + our_a2) else np.nan

        records_n2o.append({
            'Year':           y,
            'Scenario':       label,
            'RCMIP_total':    round(rn_tot,  6),
            'RCMIP_agri':     round(rn_ag,   6),
            'RCMIP_nonagri':  round(rn_non,  6),
            'Our_agri':       round(our_a2,  6),
            'New_total':      round(new_t2,  6),
            'Period':         ('pre-inventory' if y < 1970
                               else 'historical'  if y < 2020
                               else 'scenario'),
        })

df_ch4 = pd.DataFrame(records_ch4)
df_n2o = pd.DataFrame(records_n2o)

# [Step 11 of unified-codebase rebuild: bug fix - was writing to HERE
#  (= the script's own src/ directory) instead of OUT_A_DATA. Component C's
#  external_comparators_processing.py expects these files at
#  outputs/component_a/data/rcmip_substitution_*.csv. Predecessor's FULL
#  reference had them in BOTH locations (the src/ files were committed as
#  reference; outputs/ versions were produced by some out-of-band process).
#  Fixed to write directly to OUT_A_DATA so the producer-consumer chain
#  works end-to-end. - DKB 2026-05-07]
df_ch4.to_csv(os.path.join(str(OUT_A_DATA), 'rcmip_substitution_ch4.csv'), index=False)
df_n2o.to_csv(os.path.join(str(OUT_A_DATA), 'rcmip_substitution_n2o.csv'), index=False)
print(f"  Saved: rcmip_substitution_ch4.csv  ({len(df_ch4):,} rows)")
print(f"  Saved: rcmip_substitution_n2o.csv  ({len(df_n2o):,} rows)")

# =============================================================================
# SECTION 6: VERIFICATION
# =============================================================================
print()
print("=== Verification: SSP2-4.5 at key years ===")
s2_ch4 = df_ch4[df_ch4['Scenario']=='SSP2-4.5'].set_index('Year')
s2_n2o = df_n2o[df_n2o['Scenario']=='SSP2-4.5'].set_index('Year')

print(f"\nCH4 (Mt/yr):    {'Year':>6}  {'RCMIP_total':>12}  {'RCMIP_agri':>11}  "
      f"{'Our_agri':>10}  {'New_total':>10}  {'Delta':>8}")
for y in [1950, 1970, 1990, 2010, 2020, 2050, 2100]:
    row = s2_ch4.loc[y]
    delta = row['New_total'] - row['RCMIP_total']
    print(f"  {y:6d}  {row['RCMIP_total']:12.2f}  {row['RCMIP_agri']:11.2f}  "
          f"{row['Our_agri']:10.2f}  {row['New_total']:10.2f}  {delta:+8.2f}")

print(f"\nN2O (Mt/yr):    {'Year':>6}  {'RCMIP_total':>12}  {'RCMIP_agri':>11}  "
      f"{'Our_agri':>10}  {'New_total':>10}  {'Delta':>8}")
for y in [1950, 1970, 1990, 2010, 2020, 2050, 2100]:
    row = s2_n2o.loc[y]
    delta = row['New_total'] - row['RCMIP_total']
    print(f"  {y:6d}  {row['RCMIP_total']:12.4f}  {row['RCMIP_agri']:11.4f}  "
          f"{row['Our_agri']:10.4f}  {row['New_total']:10.4f}  {delta:+8.4f}")

print()
print("=== 2020 Discontinuity Summary ===")
print("  A discontinuity at 2020 separates historical Tier 1 from scenario:")
print("  CH4: historical 2019 → scenario 2020 (different activity data coverage)")
print("  N2O: historical 2019 → scenario 2020 (2006 params → 2019 params)")
print("  This is documented and expected; it reflects genuine differences in")
print("  methodology/coverage between the two periods.")
print()
print("Done.")
