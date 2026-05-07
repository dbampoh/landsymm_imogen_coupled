"""
scenario_ch4_rice_plotting.py
===============================
Self-contained plotting script for CH4 Rice Cultivation scenario
emissions (2020-2100, PLUMv2 s1 central realisations).

Reads:
  scenario_ch4_rice_global.csv    — global totals by scenario and year
  scenario_ch4_rice_regional.csv  — by IPCC region, scenario, year
  ../ch4_rice_cultivation/ch4_rice_global.csv   — historical Tier 1
  ../ch4_rice_cultivation/ch4_rice_regional.csv — historical by region
  rcmip-emissions-annual-means-v5-1-0.csv        — RCMIP (historical context)
  EDGAR CH4 2025                                  — EDGAR proportions

Produces:
  scenario_ch4_rice_trends.png  (4-panel, 300 dpi)

Panels
------
1  Global totals 1970-2100 — historical Tier 1 (grey), FAO (blue dot),
   RCMIP×EDGAR 3.C.7 hist. splice (red-orange dash-dot, 1970-2020 only),
   5 PLUMv2 SSP solid scenario lines (2020-2100) + uncertainty band.
   Single combined legend.
2  Regional stacked area — SSP2-4.5 (2020-2100)
3  Scenario divergence relative to SSP2-4.5 (2020-2100)
4  Irrigated vs rainfed component bars at key years (all SSPs, SSP2-4.5 shown)

Note on RCMIP attribution:
  EDGAR 2025 code 3.C.7 = CH4 from rice cultivation.
  Used as sector proportion of total CH4: EDGAR_3C7 / EDGAR_total × RCMIP_CH4.
  Shown only for historical period (1970-2020); not extended into scenario period.

Note on 2020 offset:
  PLUM scenario 2020 ≈ 20,500-21,100 Gg CH4 vs historical 26,898 Gg CH4.
  The ~22% gap is entirely explained by PLUM's smaller rice area coverage
  (~120 Mha) relative to FAO harvested area (~195 Mha). The scenario trajectory
  captures the relative change in rice emissions from 2020 onward correctly.
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
    EDGAR_CH4_NEW, OUT_A_DATA, OUT_A_FIGS, RCMIP_CSV as RCMIP_CSV_PATH,
)

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np
import os

# =============================================================================
# PATHS
# =============================================================================
HERE      = os.path.dirname(os.path.abspath(__file__))
HIST_DIR = os.path.join(str(OUT_A_DATA), 'ch4_rice')
EDGAR_CH4 = str(EDGAR_CH4_NEW)
RCMIP_CSV = str(RCMIP_CSV_PATH)

# =============================================================================
# CONSTANTS
# =============================================================================
SCENARIOS = ['SSP1_RCP26_s1','SSP2_RCP45_s1','SSP3_RCP70_s1',
             'SSP4_RCP60_s1','SSP5_RCP85_s1']
LABELS = {'SSP1_RCP26_s1':'SSP1-2.6','SSP2_RCP45_s1':'SSP2-4.5',
          'SSP3_RCP70_s1':'SSP3-7.0','SSP4_RCP60_s1':'SSP4-6.0',
          'SSP5_RCP85_s1':'SSP5-8.5'}
COLORS = {'SSP1_RCP26_s1':'#1a9641','SSP2_RCP45_s1':'#2b83ba',
          'SSP3_RCP70_s1':'#d7191c','SSP4_RCP60_s1':'#fdae61',
          'SSP5_RCP85_s1':'#7b2d8b'}
R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']
RC9 = {'North America':'#1f77b4','Western Europe':'#aec7e8',
       'Eastern Europe':'#ffbb78','Oceania':'#2ca02c',
       'Latin America':'#98df8a','Africa':'#d62728',
       'Middle East':'#ff9896','Asia':'#9467bd',
       'Indian Subcontinent':'#c5b0d5'}
SC='#cccccc'; GK=dict(color='#cccccc',lw=0.5,ls='--',alpha=0.7)
TK=dict(fontsize=10,fontweight='bold',color='#1a1a1a',pad=6)
LK=dict(fontsize=8.5,color='#444444'); PK=dict(labelsize=8,colors='#666666')
C_HIST='#666666'; C_FAO='#2166ac'; C_RCMIP='#d6604d'
SCALE = 1/1000   # Gg CH4 → Mt CH4

# =============================================================================
# RCMIP HISTORICAL SECTOR LINE (1970-2020)
# EDGAR 3.C.7 = CH4 rice cultivation
# =============================================================================
def build_rcmip_hist_rice():
    YEARS  = list(range(1970, 2021))
    YR_STR = [str(y) for y in YEARS]
    YC_E   = [f'Y_{y}' for y in YEARS]

    de = pd.ExcelFile(EDGAR_CH4).parse('IPCC 2006', header=9)
    col = 'ipcc_code_2006_for_standard_report'
    et  = de[YC_E].apply(pd.to_numeric, errors='coerce').fillna(0).sum().values
    es  = de[de[col] == '3.C.7'][YC_E]\
            .apply(pd.to_numeric, errors='coerce').fillna(0).sum().values
    prop = np.where(et > 0, es / et, 0.)

    df_r = pd.read_csv(RCMIP_CSV, low_memory=False)
    h = df_r[(df_r['Region']=='World') & (df_r['Scenario']=='historical') &
             (df_r['Variable']=='Emissions|CH4')][YR_STR].values[0].astype(float)
    s = df_r[(df_r['Region']=='World') & (df_r['Scenario']=='ssp245') &
             (df_r['Variable']=='Emissions|CH4')][YR_STR].values[0].astype(float)

    i15 = YEARS.index(2015); i20 = YEARS.index(2020)
    rcmip = np.zeros(51)
    for i, y in enumerate(YEARS):
        if   y <= 2014:        rcmip[i] = h[i]
        elif y == 2015:        rcmip[i] = s[i15]
        elif 2016 <= y <= 2019:rcmip[i] = s[i15] + (y-2015)/5.*(s[i20]-s[i15])
        else:                  rcmip[i] = s[i20]
    # RCMIP CH4 already in Mt; prop is dimensionless → Mt
    return np.arange(1970, 2021), prop * rcmip

print("Building RCMIP historical reference (EDGAR 3.C.7 proportion) ...")
rcmip_yrs, rcmip_vals = build_rcmip_hist_rice()
print(f"  RCMIP × EDGAR 3.C.7 at 2020: {rcmip_vals[-1]:.2f} Mt CH4")

# =============================================================================
# LOAD DATA
# =============================================================================
print("Loading emissions data ...")
sg = pd.read_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_ch4_rice_global.csv'))
sr = pd.read_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_ch4_rice_regional.csv'))
hg = pd.read_csv(os.path.join(HIST_DIR, 'ch4_rice_global.csv'))
hr = pd.read_csv(os.path.join(HIST_DIR, 'ch4_rice_regional.csv'))

# Historical columns
h_tot_col = [c for c in hg.columns if 'Total' in c and 'GgCH4' in c][0]
h_fao_col = [c for c in hg.columns if 'FAO' in c][0]
h_reg_col = [c for c in hr.columns if 'Total' in c and 'GgCH4' in c][0]

h_yrs  = hg['Year'].values
h_vals = hg[h_tot_col].values * SCALE
h_fao  = hg[h_fao_col].values * SCALE

scen_data = {}
for s in SCENARIOS:
    sub = sg[sg['Scenario'] == s].sort_values('Year')
    scen_data[s] = {'yrs':  sub['Year'].values,
                    'vals': sub['CH4_GgCH4'].values * SCALE,
                    'irr':  sub['CH4_irr_GgCH4'].values * SCALE,
                    'rain': sub['CH4_rain_GgCH4'].values * SCALE}

ssp2_reg  = {}
ssp2_yrs  = sr[sr['Scenario'] == 'SSP2_RCP45_s1'].sort_values('Year')['Year'].unique()
for r in R9:
    sub = sr[(sr['Scenario'] == 'SSP2_RCP45_s1') & (sr['Region'] == r)]\
            .sort_values('Year')
    if len(sub):
        ssp2_reg[r] = sub['CH4_GgCH4'].values * SCALE

# =============================================================================
# STYLE HELPER
# =============================================================================
def style_ax(ax, xlim=(1970,2100), ylim=None):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    ax.axvline(2020, color='#888888', lw=1.0, ls=':', alpha=0.6)
    for sp in ['top','right']: ax.spines[sp].set_visible(False)
    for sp in ['left','bottom']:
        ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

# =============================================================================
# PLOT
# =============================================================================
print("Generating plot ...")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')
fig.suptitle(
    'CH4 \u2014 Rice Cultivation\n'
    'Scenario projections 2020\u20132100  |  '
    'PLUMv2 s1 (IrrigAmount split: irrigated SFw=0.60 / rainfed SFw=0.45, '
    'IPCC 2019 Refinement)',
    fontsize=9.5, fontweight='bold', color='#1a1a1a', y=0.99)

# ── Panel 1: Global totals — single combined legend ──────────────────────────
ax = axes[0, 0]
ax.plot(h_yrs, h_vals, color=C_HIST, lw=2.0, zorder=10)
ax.plot(h_yrs, h_fao,  color=C_FAO,  lw=1.8, ls=':', zorder=9)
ax.plot(rcmip_yrs, rcmip_vals, color=C_RCMIP, lw=1.5,
        ls=(0,(4,1,1,1)), alpha=0.75, zorder=8)

lo = np.min([scen_data[s]['vals'] for s in SCENARIOS], axis=0)
hi = np.max([scen_data[s]['vals'] for s in SCENARIOS], axis=0)
ax.fill_between(scen_data[SCENARIOS[0]]['yrs'], lo, hi,
                alpha=0.10, color='#888888', zorder=5)
for s in SCENARIOS:
    d = scen_data[s]
    ax.plot(d['yrs'], d['vals'], color=COLORS[s], lw=2.0, zorder=12)

# Annotation explaining the 2020 offset
ax.annotate('PLUM covers ~120 Mha\nvs FAO 195 Mha\n(gap explains offset)',
            xy=(2020, scen_data['SSP2_RCP45_s1']['vals'][0]),
            xytext=(2030, scen_data['SSP2_RCP45_s1']['vals'][0] * 1.18),
            fontsize=6.5, color='#555555',
            arrowprops=dict(arrowstyle='->', color='#888888', lw=0.8))

handles = [
    Line2D([0],[0], color=C_HIST,  lw=2,
           label='Our IPCC Tier 1 (2019 Ref., FAO area)'),
    Line2D([0],[0], color=C_FAO,   lw=1.8, ls=':', label='FAO TIER 1'),
    Line2D([0],[0], color=C_RCMIP, lw=1.5,
           ls=(0,(4,1,1,1)), alpha=0.75,
           label='RCMIP \u00d7 EDGAR 3.C.7 prop. (hist. only)'),
] + [Line2D([0],[0], color=COLORS[s], lw=2, label=LABELS[s])
     for s in SCENARIOS]
ax.legend(handles=handles, fontsize=7.5, loc='upper left',
          framealpha=0.92, edgecolor=SC, fancybox=False)
ax.set_title('Global Totals', **TK)
ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax)

# ── Panel 2: Regional stacked — SSP2-4.5 ────────────────────────────────────
ax = axes[0, 1]
ro = ['Indian Subcontinent','Asia','Latin America','Africa',
      'North America','Eastern Europe','Western Europe','Middle East','Oceania']
stacks = [ssp2_reg.get(r, np.zeros(len(ssp2_yrs))) for r in ro]
ax.stackplot(ssp2_yrs, stacks, labels=ro,
             colors=[RC9[r] for r in ro], alpha=0.82)
ax.plot(scen_data['SSP2_RCP45_s1']['yrs'],
        scen_data['SSP2_RCP45_s1']['vals'],
        color='black', lw=1.8, ls='--', zorder=10, label='SSP2-4.5 total')
ax.set_title('Regional Breakdown \u2014 SSP2-4.5 (PLUMv2)', **TK)
ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax, xlim=(2020, 2100))
ax.legend(fontsize=7, loc='upper left', framealpha=0.92,
          edgecolor=SC, fancybox=False)

# ── Panel 3: Scenario divergence relative to SSP2-4.5 ───────────────────────
ax = axes[1, 0]
ssp2_base = np.array(scen_data['SSP2_RCP45_s1']['vals'])
for s in SCENARIOS:
    d = scen_data[s]
    ratio = np.where(ssp2_base > 0, np.array(d['vals']) / ssp2_base, 1.)
    ax.plot(d['yrs'], ratio, color=COLORS[s], lw=1.8, label=LABELS[s])
ax.axhline(1.0, color='#888888', lw=1.2)
ax.text(2022, 1.015, 'SSP2-4.5 reference',
        fontsize=7, color='#666666', va='bottom')
ax.set_title('Scenario Divergence Relative to SSP2-4.5', **TK)
ax.set_ylabel('Ratio (Scenario / SSP2-4.5)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax, xlim=(2020, 2100))
ax.legend(fontsize=8, loc='upper left', framealpha=0.92,
          edgecolor=SC, fancybox=False)

# ── Panel 4: Irrigated vs rainfed component bars at key years (all SSPs) ────
ax = axes[1, 1]
key_yrs  = [2020, 2040, 2060, 2080, 2100]
n_yrs    = len(key_yrs)
n_ssp    = len(SCENARIOS)
group_w  = 0.80
bar_w    = group_w / n_ssp
spacing  = 1.2
x_centres = [i * spacing for i in range(n_yrs)]

C_IRR  = '#2b83ba'   # irrigated: blue
C_RAIN = '#74c476'   # rainfed: green

for si, s in enumerate(SCENARIOS):
    d    = scen_data[s]
    yr_s = d['yrs']
    offset = (si - n_ssp/2 + 0.5) * bar_w + np.array(x_centres)
    irr_vals  = [float(pd.Series(d['irr'],  index=yr_s).reindex([y]).fillna(0).iloc[0])
                 for y in key_yrs]
    rain_vals = [float(pd.Series(d['rain'], index=yr_s).reindex([y]).fillna(0).iloc[0])
                 for y in key_yrs]
    irr_arr  = np.array(irr_vals)
    rain_arr = np.array(rain_vals)
    ax.bar(offset, irr_arr,  bar_w * 0.92,
           color=C_IRR,  alpha=0.85, edgecolor='white', lw=0.4,
           label='Irrigated' if si == 0 else '_')
    ax.bar(offset, rain_arr, bar_w * 0.92, bottom=irr_arr,
           color=C_RAIN, alpha=0.85, edgecolor='white', lw=0.4,
           label='Rainfed' if si == 0 else '_')
    # SSP label below bars
    for xi, xc in enumerate(x_centres):
        ax.text(offset[xi], -0.025, LABELS[s][3:7],
                ha='center', va='top', fontsize=4.8,
                color=COLORS[s], rotation=90,
                transform=ax.get_xaxis_transform())

ax.set_xticks(x_centres)
ax.set_xticklabels([str(y) for y in key_yrs], fontsize=8)
ax.set_title('Irrigated vs Rainfed CH4 — All SSPs at Key Years\n'
             '(each cluster = one year; bars L\u2192R = SSP1\u2192SSP5)', **TK)
ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)', **LK)
ax.legend(fontsize=8, loc='upper left', framealpha=0.92,
          edgecolor=SC, fancybox=False)
ax.tick_params(**PK); ax.grid(axis='y', **GK)
for sp in ['top','right']: ax.spines[sp].set_visible(False)
for sp in ['left','bottom']:
    ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

# ── Footer ───────────────────────────────────────────────────────────────────
v20  = scen_data['SSP2_RCP45_s1']['vals'][0]
v100 = {LABELS[s]: f"{scen_data[s]['vals'][-1]:.2f}" for s in SCENARIOS}
fig.text(
    0.5, 0.003,
    f"SSP2 2020: {v20:.2f} Mt  |  "
    f"2100: " + "  ".join(f"{k}={v}" for k,v in v100.items()) + " Mt  |  "
    f"Method: PLUMv2 IrrigAmount>0 \u2192 irrigated (SFw=0.60, SFo=2.508), "
    f"IrrigAmount=0 \u2192 rainfed (SFw=0.45, SFo=1.0)  |  "
    f"IPCC 2019 Ref. EFc, T, SFw, SFp, SFo (Tables 5.11-5.14)",
    ha='center', fontsize=6.2, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
              edgecolor='#cccccc', alpha=0.9))

plt.tight_layout(rect=[0, 0.04, 1, 0.97])
outpath = os.path.join(str(OUT_A_FIGS), 'scenario_ch4_rice_trends.png')
plt.savefig(outpath, dpi=300, bbox_inches='tight',
            facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {outpath}")
