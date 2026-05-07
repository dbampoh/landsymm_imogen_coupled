
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
    EDGAR_N2O_NEW, FAO_DIR, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES, RCMIP_CSV as RCMIP_CSV_PATH,
)

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np
_BASE=((str(FAO_DIR) + '/'))
EDGAR_N2O=str(EDGAR_N2O_NEW)
RCMIP_CSV=str(RCMIP_CSV_PATH)
OUT_DIR   = (str(OUT_A_DATA) + '/n2o_synfert/')
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
dg=pd.read_csv(OUT_DIR+'n2o_synfert_global.csv'); dr=pd.read_csv(OUT_DIR+'n2o_synfert_regional.csv')
yr=dg['Year'].values; t06=dg['Total_2006_GgN2O'].values/1000; t19c=dg['Total_2019clim_GgN2O'].values/1000
ftot=dg['FAO_Total_GgN2O'].values/1000; edgar=dg['EDGAR_GgN2O'].values/1000
direct=dg['Direct_GgN2O'].values/1000; iv06=dg['IndVol_2006_GgN2O'].values/1000; il06=dg['IndLeach_2006_GgN2O'].values/1000
R9=['North America','Western Europe','Eastern Europe','Oceania','Latin America','Africa','Middle East','Asia','Indian Subcontinent']
RC={'North America':'#1f77b4','Western Europe':'#aec7e8','Eastern Europe':'#ffbb78','Oceania':'#2ca02c','Latin America':'#98df8a','Africa':'#d62728','Middle East':'#ff9896','Asia':'#9467bd','Indian Subcontinent':'#c5b0d5'}
rd={r:dr[dr['Region']==r].sort_values('Year')['Total_2019clim_GgN2O'].values/1000 if len(dr[dr['Region']==r])==51 else np.zeros(51) for r in R9}
df_r=pd.read_csv(RCMIP_CSV,low_memory=False); rcmip=splice('Emissions|N2O',df_r)/1000  # kt->Mt
de=pd.ExcelFile(EDGAR_N2O).parse('IPCC 2006',header=9)
et=de[YC_E].apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
rcmip_sf=edgar/np.where(et/1000>0,et/1000,1)*rcmip
CF='#2166ac'; CO='#e07b39'; C19='#9056b3'; CE='#4dac26'; CR='#d6604d'; SC='#cccccc'
GK=dict(color='#cccccc',linewidth=0.5,linestyle='--',alpha=0.7); TK=dict(fontsize=11,fontweight='bold',color='#1a1a1a',pad=8)
LK=dict(fontsize=9,color='#444444'); PK=dict(labelsize=8,colors='#666666'); RL=(0,(3,1,1,1))
def sax(ax,ylim=None):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(1970,2020)
    if ylim: ax.set_ylim(*ylim)
    for s in ['top','right']: ax.spines[s].set_visible(False)
    for s in ['left','bottom']: ax.spines[s].set_color(SC); ax.spines[s].set_linewidth(0.8)
fig,axes=plt.subplots(2,2,figsize=(14,10)); fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')
fig.suptitle('N2O Emissions -- Synthetic N Fertilizer Application\nIPCC Tier 1 vs FAO FAOSTAT GLE vs EDGAR (4D11/old) vs RCMIP CMIP6  |  1970-2020',fontsize=12,fontweight='bold',color='#1a1a1a',y=0.99)
ax=axes[0,0]; ax.fill_between(yr,ftot,t06,alpha=0.08,color=CO)
ax.plot(yr,rcmip_sf,color=CR,linewidth=2.0,linestyle=RL,label='RCMIP CMIP6 (old EDGAR prop.)')
ax.plot(yr,t19c,color=C19,linewidth=1.5,linestyle='--',label='2019, arid-region leaching set to zero')
ax.plot(yr,edgar,color=CE,linewidth=1.8,linestyle='-.',label='EDGAR old (4D11; 2020=2019)')
ax.plot(yr,t06,color=CO,linewidth=2.0,label='2006 (= FAO total exactly)')
ax.plot(yr,ftot,color=CF,linewidth=2.5,linestyle=':',label='FAO TIER 1 -- Total')
ax.set_title('Global N2O Totals',**TK); ax.set_ylabel('N2O (Mt yr\u207b\u00b9)',**LK); ax.set_xlabel('Year',**LK); sax(ax,(0.3,3.2)); ax.legend(fontsize=7.5,loc='upper left',framealpha=0.9,edgecolor=SC,fancybox=False)
ax.annotate('** 2006 params reproduce\nFAO total exactly',xy=(1998,t06[28]),xytext=(1974,2.4),fontsize=7.5,color='#333333',arrowprops=dict(arrowstyle='->',color='#888888',lw=0.8),bbox=dict(boxstyle='round,pad=0.3',facecolor='#fffbe6',edgecolor='#cccc88',alpha=0.9))
ax=axes[0,1]; ax.stackplot(yr,[direct,iv06,il06],labels=['Direct N2O (EF1)','Indirect -- Volatilisation (2006)','Indirect -- Leaching (2006)'],colors=['#2c7bb6','#abd9e9','#ffffbf'],alpha=0.75)
ax.plot(yr,rcmip_sf,color=CR,linewidth=2.0,linestyle=RL,label='RCMIP total',zorder=11)
ax.plot(yr,edgar,color=CE,linewidth=1.8,linestyle='-.',label='EDGAR (4D11)',zorder=10)
ax.plot(yr,ftot,color=CF,linewidth=2.5,linestyle=':',label='FAO Total',zorder=12)
ax.set_title('Direct vs Indirect Decomposition (2006 params)',**TK); ax.set_ylabel('N2O (Mt yr\u207b\u00b9)',**LK); ax.set_xlabel('Year',**LK); sax(ax,(0,3.0)); ax.legend(fontsize=7.5,loc='upper left',framealpha=0.9,edgecolor=SC,fancybox=False)
ax=axes[1,0]; ax.axhline(1.0,color='#888888',linewidth=1.2)
_lo,_hi=emp_band(ftot,t06,edgar,rcmip_sf)
ax.fill_between(yr,_lo,_hi,alpha=0.18,color='#888888',label='Inter-method spread')
ax.plot(yr,rcmip_sf/ftot,color=CR,linewidth=2.0,linestyle=RL,label='RCMIP-derived / FAO Total')
ax.plot(yr,edgar/ftot,color=CE,linewidth=1.8,linestyle='-.',label='EDGAR (4D11) / FAO Total')
ax.plot(yr,t19c/ftot,color=C19,linewidth=1.5,linestyle='--',label='2019 aridity-split / FAO Total')
ax.plot(yr,t06/ftot,color=CO,linewidth=2.0,label='2006 / FAO Total (=1.000)')
ax.set_title('Ratio to FAO Published Total N2O',**TK); ax.set_ylabel('Ratio (Series / FAO)',**LK); ax.set_xlabel('Year',**LK); sax(ax,(0.55,1.20)); ax.legend(fontsize=7.5,loc='lower right',framealpha=0.9,edgecolor=SC,fancybox=False)
ax=axes[1,1]; ro=['Indian Subcontinent','Asia','Latin America','Africa','North America','Eastern Europe','Western Europe','Middle East','Oceania']
ax.stackplot(yr,[rd.get(r,np.zeros(51)) for r in ro],labels=ro,colors=[RC[r] for r in ro],alpha=0.80)
ax.plot(yr,rcmip_sf,color=CR,linewidth=2.0,linestyle=RL,label='RCMIP total',zorder=11)
ax.plot(yr,edgar,color=CE,linewidth=1.8,linestyle='-.',label='EDGAR (4D11)',zorder=10)
ax.plot(yr,ftot,color=CF,linewidth=2.5,linestyle=':',label='FAO total',zorder=12)
ax.axvline(2019.5,color='#aa4444',linewidth=0.8,linestyle=':',alpha=0.7); ax.text(2019.6,2.5,'2020=2019\n(EDGAR)',fontsize=6.5,color='#aa4444')
ax.set_title('Regional Breakdown -- 2019, aridity-split',**TK); ax.set_ylabel('N2O (Mt yr\u207b\u00b9)',**LK); ax.set_xlabel('Year',**LK); sax(ax,(0,3.0)); ax.legend(fontsize=7,loc='upper left',framealpha=0.9,edgecolor=SC,fancybox=False)
fig.text(0.5,0.003,f'2020: 2006={t06[-1]:.3f}Mt | FAO={ftot[-1]:.3f}Mt | EDGAR(4D11)={edgar[-1]:.3f}Mt | RCMIP-derived={rcmip_sf[-1]:.3f}Mt  |  RCMIP: CMIP6 hist+SSP2-4.5 (2016-19 interpolated); old EDGAR (4D11) proportion',ha='center',fontsize=7,color='#555555',style='italic',bbox=dict(boxstyle='round,pad=0.4',facecolor='#f5f5f0',edgecolor='#cccccc',alpha=0.9))
plt.tight_layout(rect=[0,0.04,1,0.97]); plt.savefig(FIG_DIR + 'n2o_synfert_trends.png',dpi=300,bbox_inches='tight',facecolor=fig.get_facecolor()); plt.close(); print("Saved: n2o_synfert_trends.png")
