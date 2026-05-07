"""
scenario_ch4_mm_plotting.py
============================
Self-contained plotting script for CH4 Manure Management scenario
emissions (2020-2100, PLUMv2 s1 central realisations).

Reads:
  scenario_ch4_mm_global.csv   — global total per scenario and year
  scenario_ch4_mm_regional.csv — by IPCC region, scenario, year
  ../ch4_enteric_fermentation/ch4_ef_global.csv   — historical Tier 1
  ../ch4_enteric_fermentation/ch4_ef_regional.csv — historical by region
  rcmip-emissions-annual-means-v5-1-0.csv          — RCMIP splice (historical)
  EDGAR CH4 2025                                    — EDGAR proportions (historical)

Produces:
  scenario_ch4_mm_trends.png  (4-panel, 300 dpi)

Panels
------
1  Global totals 1970-2100: historical Tier 1 (grey), FAO (blue dot),
   RCMIP×EDGAR historical splice (red-orange dash-dot, 1970-2020 only),
   5 PLUMv2 SSP scenario lines (2020-2100), inter-scenario uncertainty band.
   Single combined legend.
2  Regional stacked area — SSP2-4.5 (2020-2100)
3  Scenario divergence relative to SSP2-4.5 (2020-2100)
4  Bar comparison at key years (2020, 2040, 2060, 2080, 2100)

Historical RCMIP line: RCMIP 'historical' × EDGAR 3.A.1 / EDGAR total,
spliced to SSP2-4.5 at 2015-2019; plotted 1970-2020 only. Not extended
into scenario period (see session notes for methodological justification).
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
    EDGAR_CH4_NEW, OUT_A_DATA, RCMIP_CSV as RCMIP_CSV_PATH,
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
HERE     = os.path.dirname(os.path.abspath(__file__))
HIST_DIR = os.path.join(str(OUT_A_DATA), 'ch4_mm')
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
SC='#cccccc'
GK=dict(color='#cccccc',linewidth=0.5,linestyle='--',alpha=0.7)
TK=dict(fontsize=10,fontweight='bold',color='#1a1a1a',pad=6)
LK=dict(fontsize=8.5,color='#444444')
PK=dict(labelsize=8,colors='#666666')
C_HIST='#666666'; C_FAO='#2166ac'; C_RCMIP='#d6604d'
SCALE = 1/1000   # Gg CH4 → Mt CH4

# =============================================================================
# RCMIP HISTORICAL SECTOR LINE (1970-2020 only)
# =============================================================================
def build_rcmip_hist(variable, edgar_code, edgar_file):
    """Return (years 1970-2020, sector-attributed RCMIP values in Mt)."""
    df_r = pd.read_csv(RCMIP_CSV, low_memory=False)
    de   = pd.ExcelFile(edgar_file).parse('IPCC 2006', header=9)
    yc20 = [f'Y_{y}' for y in range(1970,2021)]
    et   = de[yc20].apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
    es   = de[de['ipcc_code_2006_for_standard_report']==edgar_code][yc20]\
             .apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
    prop = np.where(et>0, es/et, 0.)                # 51 values 1970-2020

    yrs_all = list(range(1970,2101))
    yr_str  = [str(y) for y in yrs_all]
    hist = df_r[(df_r['Region']=='World')&(df_r['Scenario']=='historical')
                &(df_r['Variable']==variable)]
    ssp2 = df_r[(df_r['Region']=='World')&(df_r['Scenario']=='ssp245')
                &(df_r['Variable']==variable)]
    h = hist[yr_str].values[0].astype(float) if len(hist) else np.full(131,np.nan)
    s = ssp2[yr_str].values[0].astype(float) if len(ssp2) else np.full(131,np.nan)
    # Interpolate SSP2-4.5 decadal to annual
    s_anchors = {y: s[i] for i,y in enumerate(yrs_all) if not np.isnan(s[i])}
    s_interp  = np.full(131,np.nan)
    sa = sorted(s_anchors)
    for k in range(len(sa)-1):
        y0,y1 = sa[k],sa[k+1]
        i0,i1 = yrs_all.index(y0),yrs_all.index(y1)
        for i in range(i0,i1+1):
            s_interp[i] = s_anchors[y0]+(i-i0)/(i1-i0)*(s_anchors[y1]-s_anchors[y0])
    # Splice hist→SSP2 2015-2019
    out = np.full(51,np.nan)
    h2014 = h[yrs_all.index(2014)]
    s2020 = s_interp[yrs_all.index(2020)]
    for i,y in enumerate(range(1970,2021)):
        if y<=2014: out[i] = h[yrs_all.index(y)]
        else:       out[i] = h2014 + (y-2014)/6.*(s2020-h2014)
    return np.arange(1970,2021), out * prop   # Mt (CH4 already in Mt in RCMIP)

print("Building RCMIP historical reference ...")
rcmip_yrs, rcmip_vals = build_rcmip_hist('Emissions|CH4','3.A.2',EDGAR_CH4)

# =============================================================================
# LOAD DATA
# =============================================================================
print("Loading emissions data ...")
sg = pd.read_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_ch4_mm_global.csv'))
sr = pd.read_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_ch4_mm_regional.csv'))
hg = pd.read_csv(os.path.join(HIST_DIR,'ch4_mm_global.csv'))
hr = pd.read_csv(os.path.join(HIST_DIR,'ch4_mm_regional.csv'))

h_yrs  = hg['Year'].values
h_vals = hg['Total_GgCH4'].values * SCALE
h_fao  = hg['FAO_published_GgCH4'].values * SCALE

scen_data = {}
for s in SCENARIOS:
    sub = sg[sg['Scenario']==s].sort_values('Year')
    scen_data[s] = {'yrs':sub['Year'].values,'vals':sub['CH4_GgCH4'].values*SCALE}

ssp2_reg = {}
ssp2_yrs = sr[sr['Scenario']=='SSP2_RCP45_s1'].sort_values('Year')['Year'].unique()
for r in R9:
    sub = sr[(sr['Scenario']=='SSP2_RCP45_s1')&(sr['Region']==r)].sort_values('Year')
    if len(sub): ssp2_reg[r] = sub['CH4_GgCH4'].values * SCALE

# =============================================================================
# PLOT
# =============================================================================
def style_ax(ax, xlim=(1970,2100), ylim=None):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    ax.axvline(2020,color='#888888',lw=1.0,ls=':',alpha=0.6)
    for sp in ['top','right']: ax.spines[sp].set_visible(False)
    for sp in ['left','bottom']:
        ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

print("Generating plot ...")
fig, axes = plt.subplots(2,2,figsize=(14,10))
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')
fig.suptitle('CH4 \u2014 Manure Management\n'
             'Scenario projections 2020\u20132100  |  '
             'PLUMv2 s1 (relative-change anchored to FAO 2020)',
             fontsize=10,fontweight='bold',color='#1a1a1a',y=0.99)

# ── Panel 1: Global totals (single combined legend) ───────────────────────────
ax = axes[0,0]
ax.plot(h_yrs,   h_vals,    color=C_HIST, lw=2.0, zorder=10)
ax.plot(h_yrs,   h_fao,     color=C_FAO,  lw=1.8, ls=':', zorder=9)
ax.plot(rcmip_yrs,rcmip_vals,color=C_RCMIP,lw=1.5,
        ls=(0,(4,1,1,1)),alpha=0.75,zorder=8)
lo = np.min([scen_data[s]['vals'] for s in SCENARIOS],axis=0)
hi = np.max([scen_data[s]['vals'] for s in SCENARIOS],axis=0)
ax.fill_between(scen_data[SCENARIOS[0]]['yrs'],lo,hi,alpha=0.10,color='#888888',zorder=5)
for s in SCENARIOS:
    d = scen_data[s]
    ax.plot(d['yrs'],d['vals'],color=COLORS[s],lw=2.0,zorder=12)

# Single combined legend
legend_handles = [
    Line2D([0],[0],color=C_HIST, lw=2,  label='Our IPCC Tier 1 (2019 Ref.)'),
    Line2D([0],[0],color=C_FAO,  lw=1.8,ls=':',label='FAO TIER 1'),
    Line2D([0],[0],color=C_RCMIP,lw=1.5,ls=(0,(4,1,1,1)),alpha=0.75,
           label='RCMIP \u00d7 EDGAR prop. (hist. only)'),
] + [
    Line2D([0],[0],color=COLORS[s],lw=2,label=LABELS[s]) for s in SCENARIOS
]
ax.legend(handles=legend_handles,fontsize=7.5,loc='upper left',
          framealpha=0.92,edgecolor=SC,fancybox=False)
ax.set_title('Global Totals',**TK)
ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)',**LK)
ax.set_xlabel('Year',**LK)
style_ax(ax)

# ── Panel 2: Regional stacked — SSP2-4.5 ─────────────────────────────────────
ax = axes[0,1]
ro = ['Indian Subcontinent','Asia','Latin America','Africa',
      'North America','Eastern Europe','Western Europe','Middle East','Oceania']
stacks = [ssp2_reg.get(r,np.zeros(len(ssp2_yrs))) for r in ro]
ax.stackplot(ssp2_yrs,stacks,labels=ro,colors=[RC9[r] for r in ro],alpha=0.82)
ax.plot(scen_data['SSP2_RCP45_s1']['yrs'],scen_data['SSP2_RCP45_s1']['vals'],
        color='black',lw=1.8,ls='--',zorder=10,label='SSP2-4.5 total')
ax.set_title('Regional Breakdown \u2014 SSP2-4.5 (PLUMv2)',**TK)
ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)',**LK); ax.set_xlabel('Year',**LK)
style_ax(ax,xlim=(2020,2100))
ax.legend(fontsize=7,loc='upper left',framealpha=0.92,edgecolor=SC,fancybox=False)

# ── Panel 3: Divergence relative to SSP2-4.5 ─────────────────────────────────
ax = axes[1,0]
ssp2_base = np.array(scen_data['SSP2_RCP45_s1']['vals'])
for s in SCENARIOS:
    d = scen_data[s]
    r = np.where(ssp2_base>0,np.array(d['vals'])/ssp2_base,1.)
    ax.plot(d['yrs'],r,color=COLORS[s],lw=1.8,label=LABELS[s])
ax.axhline(1.0,color='#888888',lw=1.2)
ax.text(2022,1.015,'SSP2-4.5 reference',fontsize=7,color='#666666',va='bottom')
ax.set_title('Scenario Divergence Relative to SSP2-4.5',**TK)
ax.set_ylabel('Ratio (Scenario / SSP2-4.5)',**LK); ax.set_xlabel('Year',**LK)
style_ax(ax,xlim=(2020,2100))
ax.legend(fontsize=8,loc='upper left',framealpha=0.92,edgecolor=SC,fancybox=False)

# ── Panel 4: Bar comparison at key years ─────────────────────────────────────
ax = axes[1,1]
key_yrs=[2020,2040,2060,2080,2100]
x=np.arange(len(key_yrs)); offsets=np.linspace(-0.30,0.30,5); bw=0.115
for j,s in enumerate(SCENARIOS):
    d = scen_data[s]
    yr_s = pd.Series(d['vals'],index=d['yrs'])
    ax.bar(x+offsets[j],[yr_s.get(y,np.nan) for y in key_yrs],bw,
           color=COLORS[s],label=LABELS[s],alpha=0.85,edgecolor='white',lw=0.5)
ax.set_xticks(x); ax.set_xticklabels([str(y) for y in key_yrs],fontsize=8)
ax.set_title('Scenario Comparison at Key Years',**TK)
ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)',**LK)
ax.legend(fontsize=7.5,loc='upper left',framealpha=0.92,edgecolor=SC,
          fancybox=False,ncol=2)
ax.tick_params(**PK); ax.grid(axis='y',**GK)
for sp in ['top','right']: ax.spines[sp].set_visible(False)
for sp in ['left','bottom']: ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

# ── Footer ────────────────────────────────────────────────────────────────────
v20  = scen_data['SSP2_RCP45_s1']['vals'][0]
v100 = {LABELS[s]:f"{scen_data[s]['vals'][-1]:.2f}" for s in SCENARIOS}
fig.text(0.5,0.003,
    f"2020 baseline (SSP2): {v20:.3f} Mt  |  "
    f"2100: "+"  ".join(f"{k}={v}" for k,v in v100.items())+" Mt  |  "
    f"PLUMv2 s1 relative-change anchored to FAO 2020 country sums  |  "
    f"IPCC 2019 Refinement Tier 1 VS/TAM/AWMS/MCF/B0 (Tables 10.13A, 10A.2, 10A.4-10A.9, 10.16A, 10.17)",
    ha='center',fontsize=6.5,color='#555555',style='italic',
    bbox=dict(boxstyle='round,pad=0.4',facecolor='#f5f5f0',
              edgecolor='#cccccc',alpha=0.9))

plt.tight_layout(rect=[0,0.04,1,0.97])
outpath = os.path.join(HERE,'scenario_ch4_mm_trends.png')
plt.savefig(outpath,dpi=300,bbox_inches='tight',facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {outpath}")
