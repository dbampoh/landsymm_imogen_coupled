"""
CH4 Enteric Fermentation -- Standalone Plotting Script
Reads:  ch4_ef_global.csv, ch4_ef_regional.csv, ch4_ef_species.csv
        EDGAR_CH4_1970_2024.xlsx, rcmip-emissions-annual-means-v5-1-0.csv
Writes: ch4_ef_trends.png
RCMIP note: CMIP6 historical to 2014; SSP2-4.5 for 2015/2020;
            2016-2019 filled by linear interpolation.
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
    EDGAR_CH4_NEW, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES, RCMIP_CSV as RCMIP_CSV_PATH,
)

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import numpy as np

def emp_band(fao, *series):
    """Empirical uncertainty: min/max envelope of all series/FAO ratios."""
    ratios = np.array([np.where(fao>0, s/fao, np.nan) for s in series])
    return np.nanmin(ratios,axis=0), np.nanmax(ratios,axis=0)

# ── PATHS ─────────────────────────────────────────────────────────────────────
EDGAR_CH4 = str(EDGAR_CH4_NEW)
RCMIP_CSV = str(RCMIP_CSV_PATH)
OUT_DIR   = (str(OUT_A_DATA) + '/ch4_ef/')
FIG_DIR   = (str(OUT_A_FIGS) + '/')
import os as _os; _os.makedirs(FIG_DIR, exist_ok=True)

YEARS  = list(range(1970, 2021))
YR_STR = [str(y) for y in YEARS]
YC_E   = [f'Y_{y}' for y in YEARS]

# ── RCMIP SPLICE (historical to 2014 + SSP2-4.5 2015-2020, 2016-19 interpolated) ──
def rcmip_splice(variable, df_r):
    hist = df_r[(df_r['Region']=='World')&(df_r['Scenario']=='historical')&(df_r['Variable']==variable)]
    ssp  = df_r[(df_r['Region']=='World')&(df_r['Scenario']=='ssp245')&(df_r['Variable']==variable)]
    h = hist[YR_STR].values[0].astype(float) if len(hist) else np.zeros(51)
    s = ssp [YR_STR].values[0].astype(float) if len(ssp)  else np.zeros(51)
    out = np.zeros(51)
    i15 = YEARS.index(2015); i20 = YEARS.index(2020)
    for i, y in enumerate(YEARS):
        if y <= 2014:           out[i] = h[i]
        elif y == 2015:         out[i] = s[i15]
        elif 2016 <= y <= 2019: out[i] = s[i15] + (y-2015)/5.*(s[i20]-s[i15])
        else:                   out[i] = s[i20]
    return out

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
dg = pd.read_csv(OUT_DIR + 'ch4_ef_global.csv')
ds = pd.read_csv(OUT_DIR + 'ch4_ef_species.csv')
dr = pd.read_csv(OUT_DIR + 'ch4_ef_regional.csv')

yr      = dg['Year'].values
our_tot = dg['Total_GgCH4'].values / 1000  # Gg -> Mt
fao     = dg['FAO_published_GgCH4'].values / 1000
edgar   = dg['EDGAR_GgCH4'].values / 1000

# Combine horse species columns
for col in ['Horses_GgCH4', 'Mules_GgCH4', 'Asses_GgCH4']:
    if col not in ds.columns: ds[col] = 0.
ds['Horses_Asses_GgCH4'] = ds['Horses_GgCH4'] + ds['Mules_GgCH4'] + ds['Asses_GgCH4']

SPECIES = ['Other_Cattle_GgCH4','Dairy_Cattle_GgCH4','Buffalo_GgCH4',
           'Sheep_GgCH4','Goats_GgCH4','Camels_GgCH4','Horses_Asses_GgCH4','Swine_GgCH4']
SP_LBL  = ['Other cattle','Dairy cattle','Buffalo','Sheep','Goats','Camels','Horses & asses','Swine']
sp_data = [ds[c].values / 1000 for c in SPECIES]  # Gg -> Mt

R9 = ['North America','Western Europe','Eastern Europe','Oceania',
      'Latin America','Africa','Middle East','Asia','Indian Subcontinent']
reg_data = {}
for r in R9:
    sub = dr[dr['Region']==r].sort_values('Year')
    reg_data[r] = sub['Total_GgCH4'].values / 1000 if len(sub)==51 else np.zeros(51)

# ── RCMIP-DERIVED SECTOR LINE ─────────────────────────────────────────────────
df_r = pd.read_csv(RCMIP_CSV, low_memory=False)
rcmip_ch4_total = rcmip_splice('Emissions|CH4', df_r)         # already Mt
df_edgar = pd.ExcelFile(EDGAR_CH4).parse('IPCC 2006', header=9)
edgar_total_ch4 = df_edgar[YC_E].apply(pd.to_numeric, errors='coerce').fillna(0).sum().values
edgar_ef_ch4    = df_edgar[df_edgar['ipcc_code_2006_for_standard_report']=='3.A.1'][YC_E].apply(pd.to_numeric,errors='coerce').fillna(0).sum().values
# proportion is unitless; RCMIP already in Mt
prop_ef = edgar_ef_ch4 / np.where(edgar_total_ch4 > 0, edgar_total_ch4, 1)
rcmip_ef = prop_ef * rcmip_ch4_total

# ── STYLE ─────────────────────────────────────────────────────────────────────
C_FAO='#2166ac'; C_OUR='#e07b39'; C_EDG='#4dac26'; C_RCP='#d6604d'
SC='#cccccc'; GK=dict(color='#cccccc',linewidth=0.5,linestyle='--',alpha=0.7)
TK=dict(fontsize=11,fontweight='bold',color='#1a1a1a',pad=8)
LK=dict(fontsize=9,color='#444444'); PK=dict(labelsize=8,colors='#666666')
RLS=(0,(3,1,1,1))
SP_COLS=['#1f77b4','#aec7e8','#ff7f0e','#d62728','#2ca02c','#9467bd','#8c564b','#e377c2']
RC_COLS={'North America':'#1f77b4','Western Europe':'#aec7e8','Eastern Europe':'#ffbb78',
         'Oceania':'#2ca02c','Latin America':'#98df8a','Africa':'#d62728',
         'Middle East':'#ff9896','Asia':'#9467bd','Indian Subcontinent':'#c5b0d5'}

def sax(ax, ylim=None):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(1970,2020)
    if ylim: ax.set_ylim(*ylim)
    for s in ['top','right']: ax.spines[s].set_visible(False)
    for s in ['left','bottom']: ax.spines[s].set_color(SC); ax.spines[s].set_linewidth(0.8)


# ── FIGURE ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2,2,figsize=(14,10))
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')
fig.suptitle('CH4 Emissions -- Enteric Fermentation\n'
             'IPCC 2019 Tier 1 vs FAO FAOSTAT GLE vs EDGAR (3.A.1) vs RCMIP CMIP6  |  1970-2020',
             fontsize=12, fontweight='bold', color='#1a1a1a', y=0.99)

# Panel 1 -- Global totals
ax = axes[0,0]
ax.fill_between(yr, fao, our_tot, alpha=0.10, color=C_OUR)
ax.plot(yr, rcmip_ef,  color=C_RCP, linewidth=2.0, linestyle=RLS,  label='RCMIP CMIP6 (EDGAR prop.)')
ax.plot(yr, edgar,     color=C_EDG, linewidth=1.8, linestyle='-.', label='EDGAR 2025 (3.A.1)')
ax.plot(yr, our_tot,   color=C_OUR, linewidth=2.0,                 label='Our IPCC 2019 Tier 1')
ax.plot(yr, fao,       color=C_FAO, linewidth=2.5, linestyle=':',  label='FAO TIER 1')
ax.set_title('Global CH4 Totals', **TK)
ax.set_ylabel('CH4 (Mt yr⁻¹)', **LK); ax.set_xlabel('Year', **LK)
sax(ax, (50,160))
ax.legend(fontsize=8, loc='upper left', framealpha=0.9, edgecolor=SC, fancybox=False)

# Panel 2 -- Species stacked + reference lines
ax = axes[0,1]
ax.stackplot(yr, sp_data, labels=SP_LBL, colors=SP_COLS, alpha=0.80)
ax.plot(yr, rcmip_ef, color=C_RCP, linewidth=2.0, linestyle=RLS,  label='RCMIP total', zorder=11)
ax.plot(yr, edgar,    color=C_EDG, linewidth=1.8, linestyle='-.', label='EDGAR total', zorder=10)
ax.plot(yr, fao,      color=C_FAO, linewidth=2.5, linestyle=':',  label='FAO total',   zorder=12)
ax.set_title('Species Breakdown (IPCC 2019 Tier 1)', **TK)
ax.set_ylabel('CH4 (Mt yr⁻¹)', **LK); ax.set_xlabel('Year', **LK)
sax(ax, (0,160))
ax.legend(fontsize=7, loc='upper left', framealpha=0.9, edgecolor=SC, fancybox=False, ncol=2)

# Panel 3 -- Ratio to FAO
ax = axes[1,0]
ax.axhline(1.0, color='#888888', linewidth=1.2)
_lo,_hi=emp_band(fao,our_tot,edgar,rcmip_ef)
ax.fill_between(yr,_lo,_hi,alpha=0.18,color='#888888',label='Inter-method spread (Our/FAO, EDGAR/FAO, RCMIP/FAO)')
ax.plot(yr, rcmip_ef/fao, color=C_RCP, linewidth=2.0, linestyle=RLS,  label='RCMIP-derived / FAO')
ax.plot(yr, edgar/fao,    color=C_EDG, linewidth=1.8, linestyle='-.', label='EDGAR / FAO')
ax.plot(yr, our_tot/fao,  color=C_OUR, linewidth=2.0,                 label='Our estimate / FAO')
ax.set_title('Ratio to FAO Published CH4', **TK)
ax.set_ylabel('Ratio (Series / FAO)', **LK); ax.set_xlabel('Year', **LK)
sax(ax, (0.70,1.55))
ax.legend(fontsize=8, loc='upper right', framealpha=0.9, edgecolor=SC, fancybox=False)

# Panel 4 -- Regional stacked + reference lines
ax = axes[1,1]
ro = ['Indian Subcontinent','Asia','Latin America','Africa',
      'North America','Eastern Europe','Western Europe','Middle East','Oceania']
ax.stackplot(yr, [reg_data.get(r,np.zeros(51)) for r in ro], labels=ro,
             colors=[RC_COLS[r] for r in ro], alpha=0.80)
ax.plot(yr, rcmip_ef, color=C_RCP, linewidth=2.0, linestyle=RLS,  label='RCMIP total', zorder=11)
ax.plot(yr, edgar,    color=C_EDG, linewidth=1.8, linestyle='-.', label='EDGAR total', zorder=10)
ax.plot(yr, fao,      color=C_FAO, linewidth=2.5, linestyle=':',  label='FAO total',   zorder=12)
ax.set_title('Regional Breakdown (IPCC 2019 Tier 1)', **TK)
ax.set_ylabel('CH4 (Mt yr⁻¹)', **LK); ax.set_xlabel('Year', **LK)
sax(ax, (0,160))
ax.legend(fontsize=7, loc='upper left', framealpha=0.9, edgecolor=SC, fancybox=False)

fig.text(0.5, 0.003,
    f'2020: Our={our_tot[-1]:.3f}Mt | FAO={fao[-1]:.3f}Mt | '
    f'EDGAR={edgar[-1]:.3f}Mt | RCMIP-derived={rcmip_ef[-1]:.3f}Mt  |  '
    f'RCMIP: CMIP6 hist+SSP2-4.5; 2016-2019 linearly interpolated; EDGAR 3.A.1 proportion',
    ha='center', fontsize=7, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0', edgecolor='#cccccc', alpha=0.9))

plt.tight_layout(rect=[0,0.04,1,0.97])
plt.savefig(FIG_DIR + 'ch4_ef_trends.png', dpi=300, bbox_inches='tight',
            facecolor=fig.get_facecolor())
plt.close()
print("Saved: ch4_ef_trends.png")
