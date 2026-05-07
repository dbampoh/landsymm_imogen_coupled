"""
scenario_n2o_ms_plotting.py
==============================
Self-contained plotting script for N2O Managed Soils scenario emissions
(2020-2100, PLUMv2 s1 central realisations).

Reads:
  scenario_n2o_ms_global.csv
  scenario_n2o_ms_regional.csv
  ../n2o_managed_soils/n2o_ms_global.csv   — historical Tier 1
  ../n2o_managed_soils/n2o_ms_regional.csv
  rcmip-emissions-annual-means-v5-1-0.csv  — RCMIP splice (historical only)
  EDGAR N2O 2025                            — EDGAR proportions

Produces:
  scenario_n2o_ms_trends.png  (4-panel, 300 dpi)

Panel 4 shows a stacked bar of component contributions (FSN, FON, FCR,
FPRP, FSOM) at 2020, 2050, and 2100 for SSP2-4.5, replacing the plain
bar comparison, since the component breakdown is especially informative
for managed soils.
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
HIST_DIR = os.path.join(str(OUT_A_DATA), 'n2o_ms')
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

# N input component colours for stacked bar (Panel 4)
COMP_COLS = {'FSN':'#2b83ba','FON':'#d7191c','FCR':'#fdae61',
             'FPRP':'#1a9641','FSOM':'#7b2d8b'}

# =============================================================================
# RCMIP HISTORICAL LINE
# Uses EDGAR 3.C.4 + 3.C.5 (direct + indirect from crop/livestock soils)
# Note: EDGAR agricultural soils aggregation differs from our MS sector;
# shown for orientation only.
# =============================================================================
def build_rcmip_hist_n2o(codes):
    df_r = pd.read_csv(RCMIP_CSV, low_memory=False)
    de   = pd.ExcelFile(EDGAR_N2O).parse('IPCC 2006', header=9)
    yc20 = [f'Y_{y}' for y in range(1970,2021)]
    et   = de[yc20].apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
    es   = sum(de[de['ipcc_code_2006_for_standard_report']==c][yc20]
                 .apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
               for c in codes)
    prop = np.where(et>0, es/et, 0.)
    yrs_all=list(range(1970,2101)); yr_str=[str(y) for y in yrs_all]
    hist=df_r[(df_r['Region']=='World')&(df_r['Scenario']=='historical')
              &(df_r['Variable']=='Emissions|N2O')]
    ssp2=df_r[(df_r['Region']=='World')&(df_r['Scenario']=='ssp245')
              &(df_r['Variable']=='Emissions|N2O')]
    h=hist[yr_str].values[0].astype(float) if len(hist) else np.full(131,np.nan)
    s=ssp2[yr_str].values[0].astype(float) if len(ssp2) else np.full(131,np.nan)
    s_anchors={y:s[i] for i,y in enumerate(yrs_all) if not np.isnan(s[i])}
    s_interp=np.full(131,np.nan)
    sa=sorted(s_anchors)
    for k in range(len(sa)-1):
        y0,y1=sa[k],sa[k+1]; i0,i1=yrs_all.index(y0),yrs_all.index(y1)
        for i in range(i0,i1+1):
            s_interp[i]=s_anchors[y0]+(i-i0)/(i1-i0)*(s_anchors[y1]-s_anchors[y0])
    out=np.full(51,np.nan)
    h2014=h[yrs_all.index(2014)]; s2020=s_interp[yrs_all.index(2020)]
    for i,y in enumerate(range(1970,2021)):
        out[i]=h[yrs_all.index(y)] if y<=2014 else h2014+(y-2014)/6.*(s2020-h2014)
    return np.arange(1970,2021), out*prop/1000.

print("Building RCMIP historical reference ...")
rcmip_yrs, rcmip_vals = build_rcmip_hist_n2o(['3.C.4','3.C.5'])

# =============================================================================
# LOAD DATA
# =============================================================================
print("Loading emissions data ...")
sg = pd.read_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_n2o_ms_global.csv'))
sr = pd.read_csv(os.path.join(str(OUT_A_DATA), 'scenario_pipeline', 'scenario_n2o_ms_regional.csv'))
hist_g = pd.read_csv(os.path.join(HIST_DIR,'n2o_ms_global.csv'))
hist_r = pd.read_csv(os.path.join(HIST_DIR,'n2o_ms_regional.csv'))

# Historical primary line: 2019 params with PRP (most complete)
h_tot_col = ([c for c in hist_g.columns if '2019' in c and 'withPRP' in c and 'Total' in c]
             or [c for c in hist_g.columns if 'Total' in c])[0]
h_fao_col = ([c for c in hist_g.columns if 'FAO' in c and 'total' in c.lower()]
             or [None])[0]
h_reg_col = ([c for c in hist_r.columns if '2019' in c and 'withPRP' in c and 'Total' in c]
             or [c for c in hist_r.columns if 'Total' in c])[0]

h_yrs  = hist_g['Year'].values
h_vals = hist_g[h_tot_col].values * SCALE
h_fao  = hist_g[h_fao_col].values * SCALE if h_fao_col else np.zeros(len(h_yrs))

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

# Component data for Panel 4 (all scenarios, Mt N2O)
# Derive N2O contribution of each component using EF1 × MW × KG_TO_GG scaling
# Components stored as N mass (kgN or MtN); convert to N2O
EF1 = 0.010; MW = 44/28; KG_TO_GG = 1e-6

def n2o_from_kgN(kg):   return kg * EF1 * MW * KG_TO_GG / 1000  # → Mt N2O
def n2o_from_MtN(mt):   return mt * EF1 * MW * 1e9 * KG_TO_GG / 1000  # → Mt N2O

sg_comp = sg[['Scenario','Year','FSN_MtN','FON_kgN','FCR_MtN',
              'FPRP_kgN','FSOM_GgN2O']].copy()
sg_comp['FSN_Mt']  = sg_comp['FSN_MtN'].apply(lambda x: n2o_from_MtN(x))
sg_comp['FON_Mt']  = sg_comp['FON_kgN'].apply(lambda x: n2o_from_kgN(x))
sg_comp['FCR_Mt']  = sg_comp['FCR_MtN'].apply(lambda x: n2o_from_MtN(x))
sg_comp['FPRP_Mt'] = sg_comp['FPRP_kgN'].apply(lambda x: n2o_from_kgN(x))
sg_comp['FSOM_Mt'] = sg_comp['FSOM_GgN2O'] / 1000

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
fig.suptitle('N2O \u2014 Managed Soils\n'
             'Scenario projections 2020\u20132100  |  '
             'PLUMv2 s1 (FSN+FON+FCR+FPRP+FSOM, IPCC 2019 Refinement)',
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
    Line2D([0],[0],color=C_HIST,lw=2,   label='Our IPCC Tier 1 (2019, with PRP)'),
    Line2D([0],[0],color=C_FAO, lw=1.8,ls=':',label='FAO TIER 1'),
    Line2D([0],[0],color=C_RCMIP,lw=1.5,ls=(0,(4,1,1,1)),alpha=0.75,
           label='RCMIP \u00d7 EDGAR 3.C.4+5 (hist. only)'),
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

# Panel 4: Stacked N input component contributions for all SSPs at key years
ax=axes[1,1]
key_yrs=[2020,2050,2100]
comp_names=['FSN','FON','FCR','FPRP','FSOM']
comp_mt   =['FSN_Mt','FON_Mt','FCR_Mt','FPRP_Mt','FSOM_Mt']

n_ssp=len(SCENARIOS); n_yr=len(key_yrs)
group_w=0.80; bar_w=group_w/n_ssp; spacing=1.2
x_centres=[i*spacing for i in range(n_yr)]

for si,s in enumerate(SCENARIOS):
    sdf=sg_comp[sg_comp['Scenario']==s].set_index('Year')
    offsets=[xc - group_w/2 + si*bar_w + bar_w/2 for xc in x_centres]
    bottoms=np.zeros(n_yr)
    for comp,colkey in zip(comp_names,comp_mt):
        vals=np.array([sdf.loc[y,colkey] if y in sdf.index else np.nan
                       for y in key_yrs])
        ax.bar(offsets,vals,bar_w*0.92,bottom=bottoms,
               color=COMP_COLS[comp],alpha=0.85,edgecolor='white',lw=0.4,
               label=comp if si==0 else '_')
        bottoms=bottoms+np.nan_to_num(vals)

ax.set_xticks([xc for xc in x_centres])
ax.set_xticklabels([str(y) for y in key_yrs],fontsize=8)
# Secondary annotation: SSP labels on x-axis
for si,s in enumerate(SCENARIOS):
    for xi,xc in enumerate(x_centres):
        xpos=xc - group_w/2 + si*bar_w + bar_w/2
        ax.text(xpos,-0.018,LABELS[s][4:7],ha='center',va='top',
                fontsize=5,color=COLORS[s],rotation=90,
                transform=ax.get_xaxis_transform())

ax.set_title('N Input Components — All SSPs at Key Years\n'
             '(each cluster = one year; bars L→R = SSP1→SSP5)',**TK)
ax.set_ylabel('N2O (Mt yr\u207b\u00b9)',**LK)
ax.legend(fontsize=8,loc='upper left',framealpha=0.92,edgecolor=SC,fancybox=False,
          title='N input source',title_fontsize=7.5)
ax.tick_params(**PK); ax.grid(axis='y',**GK)
for sp in ['top','right']: ax.spines[sp].set_visible(False)
for sp in ['left','bottom']:
    ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

# Footer
v20=scen_data['SSP2_RCP45_s1']['vals'][0]
v100=scen_data['SSP2_RCP45_s1']['vals'][-1]
fig.text(0.5,0.003,
    f"SSP2 2020: {v20:.3f} Mt  |  SSP2 2100: {v100:.3f} Mt  |  "
    f"Components: FSN=synthetic N (PLUM FertAmount), FON=organic N (livestock), "
    f"FCR=crop residues (PLUM Production \u00d7 IPCC factors \u00d7 0.469 calib.), "
    f"FPRP=pasture excreta (livestock), FSOM=drained org. soils (held at FAO 2020)",
    ha='center',fontsize=6.2,color='#555555',style='italic',
    bbox=dict(boxstyle='round,pad=0.4',facecolor='#f5f5f0',
              edgecolor='#cccccc',alpha=0.9))

plt.tight_layout(rect=[0,0.04,1,0.97])
outpath=os.path.join(HERE,'scenario_n2o_ms_trends.png')
plt.savefig(outpath,dpi=300,bbox_inches='tight',facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {outpath}")
