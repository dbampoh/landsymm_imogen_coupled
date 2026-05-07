
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
    EDGAR_CH4_NEW, FAO_DIR, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES, RCMIP_CSV as RCMIP_CSV_PATH,
)

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np
_BASE=((str(FAO_DIR) + '/'))
EDGAR_CH4=str(EDGAR_CH4_NEW)
RCMIP_CSV=str(RCMIP_CSV_PATH)
OUT_DIR   = (str(OUT_A_DATA) + '/ch4_mm/')
FIG_DIR   = (str(OUT_A_FIGS) + '/')
import os as _os; _os.makedirs(FIG_DIR, exist_ok=True)
YEARS=list(range(1970,2021)); YR_STR=[str(y) for y in YEARS]; YC_E=[f'Y_{y}' for y in YEARS]
def splice(var,df_r):
    h=df_r[(df_r['Region']=='World')&(df_r['Scenario']=='historical')&(df_r['Variable']==var)][YR_STR].values[0].astype(float)
    s=df_r[(df_r['Region']=='World')&(df_r['Scenario']=='ssp245')&(df_r['Variable']==var)][YR_STR].values[0].astype(float)
    out=np.zeros(51); i15=YEARS.index(2015); i20=YEARS.index(2020)
    for i,y in enumerate(YEARS):
        if y<=2014: out[i]=h[i]
        elif y==2015: out[i]=s[i15]
        elif 2016<=y<=2019: out[i]=s[i15]+(y-2015)/5.*(s[i20]-s[i15])
        else: out[i]=s[i20]
    return out
def emp_band(fao,*series):
    ratios=np.array([np.where(fao>0,s/fao,np.nan) for s in series])
    return np.nanmin(ratios,axis=0),np.nanmax(ratios,axis=0)
dg=pd.read_csv(OUT_DIR+'ch4_mm_global.csv'); dr=pd.read_csv(OUT_DIR+'ch4_mm_regional.csv')
yr=dg['Year'].values; our=dg['Total_GgCH4'].values/1000; fao=dg['FAO_published_GgCH4'].values/1000; edgar=dg['EDGAR_GgCH4'].values/1000
dg=dg.rename(columns={'Dairy_Cattle_GgCH4':'Dairy_GgCH4','Other_Cattle_GgCH4':'OtherCattle_GgCH4'})
dg['Poultry_GgCH4']=dg[['Layers_GgCH4','Broilers_GgCH4','Turkeys_GgCH4','Ducks_GgCH4']].fillna(0).sum(axis=1)
dg['SmallRum_GgCH4']=dg[['Sheep_GgCH4','Goats_GgCH4']].fillna(0).sum(axis=1)
SP=['Dairy_GgCH4','OtherCattle_GgCH4','Buffalo_GgCH4','Swine_GgCH4','Poultry_GgCH4','SmallRum_GgCH4','Horses_GgCH4']
SPL=['Dairy cattle','Other cattle','Buffalo','Swine','All poultry','Small ruminants','Horses']
for c in SP:
    if c not in dg.columns: dg[c]=0.
sp=[dg[c].values/1000 for c in SP]
R9=['North America','Western Europe','Eastern Europe','Oceania','Latin America','Africa','Middle East','Asia','Indian Subcontinent']
RC={'North America':'#1f77b4','Western Europe':'#aec7e8','Eastern Europe':'#ffbb78','Oceania':'#2ca02c','Latin America':'#98df8a','Africa':'#d62728','Middle East':'#ff9896','Asia':'#9467bd','Indian Subcontinent':'#c5b0d5'}
rd={r:dr[dr['Region']==r].sort_values('Year')['Total_GgCH4'].values/1000 if len(dr[dr['Region']==r])==51 else np.zeros(51) for r in R9}
df_r=pd.read_csv(RCMIP_CSV,low_memory=False); rcmip=splice('Emissions|CH4',df_r)
de=pd.ExcelFile(EDGAR_CH4).parse('IPCC 2006',header=9)
et=de[YC_E].apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
em=de[de['ipcc_code_2006_for_standard_report']=='3.A.2'][YC_E].apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
rcmip_mm=em/np.where(et>0,et,1)*rcmip
CF='#2166ac'; CO='#e07b39'; CE='#4dac26'; CR='#d6604d'; SC='#cccccc'
GK=dict(color='#cccccc',linewidth=0.5,linestyle='--',alpha=0.7); TK=dict(fontsize=11,fontweight='bold',color='#1a1a1a',pad=8)
LK=dict(fontsize=9,color='#444444'); PK=dict(labelsize=8,colors='#666666'); RL=(0,(3,1,1,1))
SC2=['#1f77b4','#aec7e8','#ff7f0e','#d62728','#2ca02c','#9467bd','#8c564b']
def sax(ax,ylim=None):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(1970,2020)
    if ylim: ax.set_ylim(*ylim)
    for s in ['top','right']: ax.spines[s].set_visible(False)
    for s in ['left','bottom']: ax.spines[s].set_color(SC); ax.spines[s].set_linewidth(0.8)
fig,axes=plt.subplots(2,2,figsize=(14,10)); fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')
fig.suptitle('CH4 Emissions -- Manure Management\nIPCC 2019 Tier 1 vs FAO FAOSTAT GLE vs EDGAR (3.A.2) vs RCMIP CMIP6  |  1970-2020',fontsize=12,fontweight='bold',color='#1a1a1a',y=0.99)
ax=axes[0,0]; ax.fill_between(yr,fao,our,alpha=0.10,color=CO)
ax.plot(yr,rcmip_mm,color=CR,linewidth=2.0,linestyle=RL,label='RCMIP CMIP6 (EDGAR prop.)')
ax.plot(yr,edgar,color=CE,linewidth=1.8,linestyle='-.',label='EDGAR 2025 (3.A.2)')
ax.plot(yr,our,color=CO,linewidth=2.0,label='Our IPCC 2019 Tier 1')
ax.plot(yr,fao,color=CF,linewidth=2.5,linestyle=':',label='FAO TIER 1')
ax.set_title('Global CH4 Totals',**TK); ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)',**LK); ax.set_xlabel('Year',**LK); sax(ax,(5,18)); ax.legend(fontsize=8,loc='upper left',framealpha=0.9,edgecolor=SC,fancybox=False)
ax=axes[0,1]; ax.stackplot(yr,sp,labels=SPL,colors=SC2,alpha=0.80)
ax.plot(yr,rcmip_mm,color=CR,linewidth=2.0,linestyle=RL,label='RCMIP total',zorder=11)
ax.plot(yr,edgar,color=CE,linewidth=1.8,linestyle='-.',label='EDGAR total',zorder=10)
ax.plot(yr,fao,color=CF,linewidth=2.5,linestyle=':',label='FAO total',zorder=12)
ax.set_title('Species Breakdown (IPCC 2019 Tier 1)',**TK); ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)',**LK); ax.set_xlabel('Year',**LK); sax(ax,(0,18)); ax.legend(fontsize=7,loc='upper left',framealpha=0.9,edgecolor=SC,fancybox=False)
ax=axes[1,0]; ax.axhline(1.0,color='#888888',linewidth=1.2)
_lo,_hi=emp_band(fao,our,edgar,rcmip_mm)
ax.fill_between(yr,_lo,_hi,alpha=0.18,color='#888888',label='Inter-method spread')
ax.plot(yr,rcmip_mm/fao,color=CR,linewidth=2.0,linestyle=RL,label='RCMIP-derived / FAO')
ax.plot(yr,edgar/fao,color=CE,linewidth=1.8,linestyle='-.',label='EDGAR / FAO')
ax.plot(yr,our/fao,color=CO,linewidth=2.0,label='Our estimate / FAO')
ax.set_title('Ratio to FAO Published CH4',**TK); ax.set_ylabel('Ratio (Series / FAO)',**LK); ax.set_xlabel('Year',**LK); sax(ax,(0.85,1.65)); ax.legend(fontsize=8,loc='upper left',framealpha=0.9,edgecolor=SC,fancybox=False)
ax=axes[1,1]; ro=['Indian Subcontinent','Asia','Latin America','Africa','North America','Eastern Europe','Western Europe','Middle East','Oceania']
ax.stackplot(yr,[rd.get(r,np.zeros(51)) for r in ro],labels=ro,colors=[RC[r] for r in ro],alpha=0.80)
ax.plot(yr,rcmip_mm,color=CR,linewidth=2.0,linestyle=RL,label='RCMIP total',zorder=11)
ax.plot(yr,edgar,color=CE,linewidth=1.8,linestyle='-.',label='EDGAR total',zorder=10)
ax.plot(yr,fao,color=CF,linewidth=2.5,linestyle=':',label='FAO total',zorder=12)
ax.set_title('Regional Breakdown',**TK); ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)',**LK); ax.set_xlabel('Year',**LK); sax(ax,(0,18)); ax.legend(fontsize=7,loc='upper left',framealpha=0.9,edgecolor=SC,fancybox=False)
fig.text(0.5,0.003,f'2020: Our={our[-1]:.3f}Mt | FAO={fao[-1]:.3f}Mt | EDGAR={edgar[-1]:.3f}Mt | RCMIP-derived={rcmip_mm[-1]:.3f}Mt  |  RCMIP: CMIP6 hist+SSP2-4.5 (2016-19 interpolated); EDGAR 3.A.2 prop.',ha='center',fontsize=7,color='#555555',style='italic',bbox=dict(boxstyle='round,pad=0.4',facecolor='#f5f5f0',edgecolor='#cccccc',alpha=0.9))
plt.tight_layout(rect=[0,0.04,1,0.97]); plt.savefig(FIG_DIR + 'ch4_mm_trends.png',dpi=300,bbox_inches='tight',facecolor=fig.get_facecolor()); plt.close(); print("Saved: ch4_mm_trends.png")
