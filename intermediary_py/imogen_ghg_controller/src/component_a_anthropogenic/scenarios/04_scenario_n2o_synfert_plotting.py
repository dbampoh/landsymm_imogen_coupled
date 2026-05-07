"""
scenario_n2o_synfert_plotting.py
==================================
Self-contained plotting script for N2O Synthetic Fertilizer scenario
emissions (2020-2100, PLUMv2 s1 central realisations).

Reads:
  scenario_n2o_synfert_global.csv
  scenario_n2o_synfert_regional.csv
  ../n2o_synthetic_fertilizers/n2o_synfert_global.csv   — historical Tier 1
  ../n2o_synthetic_fertilizers/n2o_synfert_regional.csv
  rcmip-emissions-annual-means-v5-1-0.csv               — RCMIP splice (hist.)
  EDGAR N2O 2025                                         — EDGAR proportions

Produces:
  scenario_n2o_synfert_trends.png  (4-panel, 300 dpi)
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
    EDGAR_N2O_NEW, OUT_A_DATA, RCMIP_CSV as RCMIP_CSV_PATH,
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
HIST_DIR = os.path.join(str(OUT_A_DATA), 'n2o_synfert')
EDGAR_N2O = str(EDGAR_N2O_NEW)
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
SCALE = 1/1000   # Gg N2O → Mt N2O

# =============================================================================
# RCMIP HISTORICAL SECTOR LINE (1970-2020)
# Method: old EDGAR (4D11) synfert / new EDGAR N2O total × RCMIP N2O total
# This is identical to the historical n2o_synfert_plotting.py approach and
# ensures the RCMIP line matches at 2020 between the two plots.
#
# WHY NOT use new EDGAR codes 3.C.4+3.C.5:
#   Those codes cover ALL managed soils N2O (64% of total N2O), not just
#   synthetic fertilizer. Applying that proportion to RCMIP total gives ~7 Mt
#   at 2020, far above the synfert-specific value of ~2 Mt shown in the
#   historical plot. The old EDGAR 4D11 has a dedicated "Synthetic Fertilizers"
#   row (~17-18% of N2O total) which is the correct sector-specific denominator.
# =============================================================================
def build_rcmip_hist_synfert():
    """
    Replicate historical synfert plot RCMIP line exactly:
      rcmip_sf = edgar_old_synfert / edgar_new_total × rcmip_n2o_total
    Returns (years 1970-2020, values in Mt N2O).
    """
    YEARS  = list(range(1970, 2021))
    YR_STR = [str(y) for y in YEARS]
    YC_E   = [f'Y_{y}' for y in YEARS]

    # New EDGAR total N2O (denominator)
    de = pd.ExcelFile(EDGAR_N2O).parse('IPCC 2006', header=9)
    et = de[YC_E].apply(pd.to_numeric, errors='coerce').fillna(0).sum().values  # Gg

    # Old EDGAR synfert (numerator): read from historical sector CSV
    # (appended by n2o_synfert_processing.py as 'EDGAR_GgN2O')
    hist_csv = os.path.join(HIST_DIR, 'n2o_synfert_global.csv')
    hist_g   = pd.read_csv(hist_csv)
    edgar_sf = hist_g.sort_values('Year')['EDGAR_GgN2O'].values   # Gg, 51 values

    # RCMIP N2O total: historical → SSP2-4.5 splice
    df_r = pd.read_csv(RCMIP_CSV, low_memory=False)
    h = df_r[(df_r['Region']=='World') & (df_r['Scenario']=='historical') &
             (df_r['Variable']=='Emissions|N2O')][YR_STR].values[0].astype(float)
    s = df_r[(df_r['Region']=='World') & (df_r['Scenario']=='ssp245') &
             (df_r['Variable']=='Emissions|N2O')][YR_STR].values[0].astype(float)
    i15 = YEARS.index(2015); i20 = YEARS.index(2020)
    rcmip = np.zeros(51)
    for i, y in enumerate(YEARS):
        if   y <= 2014:       rcmip[i] = h[i]
        elif y == 2015:       rcmip[i] = s[i15]
        elif 2016 <= y <= 2019: rcmip[i] = s[i15] + (y-2015)/5.*(s[i20]-s[i15])
        else:                 rcmip[i] = s[i20]
    rcmip = rcmip / 1000.   # kt N2O → Mt N2O

    # Sector-attributed RCMIP (Mt N2O)
    rcmip_sf = edgar_sf / np.where(et > 0, et, 1) * rcmip   # Gg/Gg × Mt = Mt
    return np.arange(1970, 2021), rcmip_sf

print("Building RCMIP historical reference (old EDGAR synfert proportion) ...")
rcmip_yrs, rcmip_vals = build_rcmip_hist_synfert()

# =============================================================================
# LOAD DATA
# =============================================================================
print("Loading emissions data ...")
sg = pd.read_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_n2o_synfert_global.csv'))
sr = pd.read_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_n2o_synfert_regional.csv'))

# Determine historical column names
hist_g = pd.read_csv(os.path.join(HIST_DIR,'n2o_synfert_global.csv'))
hist_r = pd.read_csv(os.path.join(HIST_DIR,'n2o_synfert_regional.csv'))
# Use 2019 total (direct+indirect) as primary historical line
tot_col = [c for c in hist_g.columns if '2019' in c and 'total' in c.lower()]
tot_col = tot_col[0] if tot_col else [c for c in hist_g.columns if 'Total' in c or 'total' in c][0]
fao_col = [c for c in hist_g.columns if 'FAO' in c and 'total' in c.lower()]
fao_col = fao_col[0] if fao_col else None
reg_col_h = [c for c in hist_r.columns if '2019' in c and 'total' in c.lower()]
reg_col_h = reg_col_h[0] if reg_col_h else tot_col

h_yrs  = hist_g['Year'].values
h_vals = hist_g[tot_col].values * SCALE
h_fao  = hist_g[fao_col].values * SCALE if fao_col else np.zeros(len(h_yrs))

scen_data = {}
for s in SCENARIOS:
    sub = sg[sg['Scenario']==s].sort_values('Year')
    scen_data[s] = {'yrs':sub['Year'].values,
                    'vals':sub['N2O_total_GgN2O'].values*SCALE}

ssp2_reg={}
ssp2_yrs=sr[sr['Scenario']=='SSP2_RCP45_s1'].sort_values('Year')['Year'].unique()
for r in R9:
    sub=sr[(sr['Scenario']=='SSP2_RCP45_s1')&(sr['Region']==r)].sort_values('Year')
    if len(sub): ssp2_reg[r]=sub['N2O_total_GgN2O'].values*SCALE

# =============================================================================
# PLOT
# =============================================================================
def style_ax(ax,xlim=(1970,2100),ylim=None):
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
fig.suptitle('N2O \u2014 Synthetic Fertilizer Application\n'
             'Scenario projections 2020\u20132100  |  '
             'PLUMv2 s1 (PLUM FertAmount × IPCC 2019 EF1/FracGASF/FracLEACH)',
             fontsize=10,fontweight='bold',color='#1a1a1a',y=0.99)

# Panel 1: Global totals — single combined legend
ax=axes[0,0]
ax.plot(h_yrs,h_vals,color=C_HIST,lw=2.0,zorder=10)
ax.plot(h_yrs,h_fao, color=C_FAO, lw=1.8,ls=':',zorder=9)
ax.plot(rcmip_yrs,rcmip_vals,color=C_RCMIP,lw=1.5,
        ls=(0,(4,1,1,1)),alpha=0.75,zorder=8)
lo=np.min([scen_data[s]['vals'] for s in SCENARIOS],axis=0)
hi=np.max([scen_data[s]['vals'] for s in SCENARIOS],axis=0)
ax.fill_between(scen_data[SCENARIOS[0]]['yrs'],lo,hi,alpha=0.10,
                color='#888888',zorder=5)
for s in SCENARIOS:
    d=scen_data[s]
    ax.plot(d['yrs'],d['vals'],color=COLORS[s],lw=2.0,zorder=12)
handles=[
    Line2D([0],[0],color=C_HIST,lw=2,   label='Our IPCC Tier 1 (2019 Ref.)'),
    Line2D([0],[0],color=C_FAO, lw=1.8,ls=':',label='FAO TIER 1'),
    Line2D([0],[0],color=C_RCMIP,lw=1.5,ls=(0,(4,1,1,1)),alpha=0.75,
           label='RCMIP \u00d7 EDGAR (4D11 synfert prop., hist. only)'),
]+[Line2D([0],[0],color=COLORS[s],lw=2,label=LABELS[s]) for s in SCENARIOS]
ax.legend(handles=handles,fontsize=7.5,loc='upper left',
          framealpha=0.92,edgecolor=SC,fancybox=False)
ax.set_title('Global Totals',**TK)
ax.set_ylabel('N2O (Mt yr\u207b\u00b9)',**LK); ax.set_xlabel('Year',**LK)
style_ax(ax)

# Panel 2: Regional stacked SSP2-4.5
ax=axes[0,1]
ro=['Indian Subcontinent','Asia','Latin America','Africa','North America',
    'Eastern Europe','Western Europe','Middle East','Oceania']
stacks=[ssp2_reg.get(r,np.zeros(len(ssp2_yrs))) for r in ro]
ax.stackplot(ssp2_yrs,stacks,labels=ro,colors=[RC9[r] for r in ro],alpha=0.82)
ax.plot(scen_data['SSP2_RCP45_s1']['yrs'],scen_data['SSP2_RCP45_s1']['vals'],
        color='black',lw=1.8,ls='--',zorder=10,label='SSP2-4.5 total')
ax.set_title('Regional Breakdown \u2014 SSP2-4.5 (PLUMv2)',**TK)
ax.set_ylabel('N2O (Mt yr\u207b\u00b9)',**LK); ax.set_xlabel('Year',**LK)
style_ax(ax,xlim=(2020,2100))
ax.legend(fontsize=7,loc='upper left',framealpha=0.92,edgecolor=SC,fancybox=False)

# Panel 3: Divergence relative to SSP2-4.5
ax=axes[1,0]
ssp2_base=np.array(scen_data['SSP2_RCP45_s1']['vals'])
for s in SCENARIOS:
    d=scen_data[s]
    r=np.where(ssp2_base>0,np.array(d['vals'])/ssp2_base,1.)
    ax.plot(d['yrs'],r,color=COLORS[s],lw=1.8,label=LABELS[s])
ax.axhline(1.0,color='#888888',lw=1.2)
ax.text(2022,1.015,'SSP2-4.5 reference',fontsize=7,color='#666666',va='bottom')
ax.set_title('Scenario Divergence Relative to SSP2-4.5',**TK)
ax.set_ylabel('Ratio (Scenario / SSP2-4.5)',**LK); ax.set_xlabel('Year',**LK)
style_ax(ax,xlim=(2020,2100))
ax.legend(fontsize=8,loc='upper left',framealpha=0.92,edgecolor=SC,fancybox=False)

# Panel 4: Bar comparison at key years
ax=axes[1,1]
key_yrs=[2020,2040,2060,2080,2100]
x=np.arange(len(key_yrs)); offsets=np.linspace(-0.30,0.30,5); bw=0.115
for j,s in enumerate(SCENARIOS):
    d=scen_data[s]; yr_s=pd.Series(d['vals'],index=d['yrs'])
    ax.bar(x+offsets[j],[yr_s.get(y,np.nan) for y in key_yrs],bw,
           color=COLORS[s],label=LABELS[s],alpha=0.85,edgecolor='white',lw=0.5)
ax.set_xticks(x); ax.set_xticklabels([str(y) for y in key_yrs],fontsize=8)
ax.set_title('Scenario Comparison at Key Years',**TK)
ax.set_ylabel('N2O (Mt yr\u207b\u00b9)',**LK)
ax.legend(fontsize=7.5,loc='upper left',framealpha=0.92,edgecolor=SC,
          fancybox=False,ncol=2)
ax.tick_params(**PK); ax.grid(axis='y',**GK)
for sp in ['top','right']: ax.spines[sp].set_visible(False)
for sp in ['left','bottom']:
    ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

# Footer
v20={LABELS[s]:f"{scen_data[s]['vals'][0]:.3f}" for s in SCENARIOS}
v100={LABELS[s]:f"{scen_data[s]['vals'][-1]:.3f}" for s in SCENARIOS}
fig.text(0.5,0.003,
    f"2020: "+"  ".join(f"{k}={v}" for k,v in v20.items())+" Mt  |  "
    f"2100: "+"  ".join(f"{k}={v}" for k,v in v100.items())+" Mt  |  "
    f"FSN=PLUM FertAmount  |  IPCC 2019 Ref.: EF1=0.010  FracGASF=0.11  "
    f"FracLEACH=0.24(wet)/0(dry)  EF4=0.010  EF5=0.011",
    ha='center',fontsize=6.3,color='#555555',style='italic',
    bbox=dict(boxstyle='round,pad=0.4',facecolor='#f5f5f0',
              edgecolor='#cccccc',alpha=0.9))

plt.tight_layout(rect=[0,0.04,1,0.97])
outpath=os.path.join(HERE,'scenario_n2o_synfert_trends.png')
plt.savefig(outpath,dpi=300,bbox_inches='tight',facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {outpath}")
