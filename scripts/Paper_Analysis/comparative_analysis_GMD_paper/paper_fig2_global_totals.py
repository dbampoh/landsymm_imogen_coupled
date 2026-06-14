"""
paper_fig2_global_totals.py
===========================
Main-text Figure 2 for the GMD paper: the global agricultural-emission totals
(1970-2020) for the five Tier-1 source categories, each compared against
FAOSTAT, EDGAR 2025, and the RCMIP (CMIP6) backbone. This is the enlarged,
single-panel-per-category version requested in supervisor review; the detailed
species / regional / ratio breakdowns remain in the per-category figures
(now Supplement).

Panels (2 rows x 3 cols; 6th cell holds the shared legend):
  (a) Enteric fermentation       CH4
  (b) Manure management          CH4
  (c) Rice cultivation           CH4
  (d) Manure management          N2O
  (e) Managed (agricultural) soils  N2O

Series per panel: LandSyMM Tier-1 estimate, FAOSTAT, EDGAR 2025,
RCMIP-derived (EDGAR-proportioned). The LandSyMM N2O estimates use the basis
reported in Sect. 3.1 (manure management on the 2006-Guidelines basis;
managed soils on the 2019-Refinement with-PRP basis).

Reads the same component-A global CSVs and EDGAR/RCMIP inputs as the
per-category scripts. Writes paper_fig2_global_totals.png.
"""

import sys as _sys
from pathlib import Path as _Path
_PROJ_ROOT = _Path(__file__).resolve()
while _PROJ_ROOT.name and not (_PROJ_ROOT / 'intermediary_py' / 'imogen_ghg_controller' / 'src').is_dir():
    if _PROJ_ROOT.parent == _PROJ_ROOT:
        break
    _PROJ_ROOT = _PROJ_ROOT.parent
_IGC = _PROJ_ROOT / 'intermediary_py' / 'imogen_ghg_controller'
if str(_IGC) not in _sys.path:
    _sys.path.insert(0, str(_IGC))
from src.shared.paths import (
    EDGAR_CH4_NEW, EDGAR_N2O_NEW, OUT_A_DATA, OUT_A_FIGS, RCMIP_CSV as RCMIP_CSV_PATH,
)

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

OUT_DATA = str(OUT_A_DATA)
FIG_DIR = str(OUT_A_FIGS) + '/'
os.makedirs(FIG_DIR, exist_ok=True)

YEARS = list(range(1970, 2021))
YR_STR = [str(y) for y in YEARS]
YC_E = [f'Y_{y}' for y in YEARS]


def rcmip_splice(variable, df_r):
    """RCMIP World series: CMIP6 historical to 2014 + SSP2-4.5 for 2015/2020,
    with 2016-2019 linearly interpolated."""
    hist = df_r[(df_r['Region'] == 'World') & (df_r['Scenario'] == 'historical') & (df_r['Variable'] == variable)]
    ssp = df_r[(df_r['Region'] == 'World') & (df_r['Scenario'] == 'ssp245') & (df_r['Variable'] == variable)]
    h = hist[YR_STR].values[0].astype(float) if len(hist) else np.zeros(51)
    s = ssp[YR_STR].values[0].astype(float) if len(ssp) else np.zeros(51)
    out = np.zeros(51)
    i15 = YEARS.index(2015); i20 = YEARS.index(2020)
    for i, y in enumerate(YEARS):
        if y <= 2014:
            out[i] = h[i]
        elif y == 2015:
            out[i] = s[i15]
        elif 2016 <= y <= 2019:
            out[i] = s[i15] + (y - 2015) / 5. * (s[i20] - s[i15])
        else:
            out[i] = s[i20]
    return out


# --- RCMIP backbone (Mt) ---
df_r = pd.read_csv(str(RCMIP_CSV_PATH), low_memory=False)
rcmip_ch4 = rcmip_splice('Emissions|CH4', df_r)            # Mt CH4
rcmip_n2o = rcmip_splice('Emissions|N2O', df_r) / 1000.    # kt -> Mt N2O

# --- EDGAR sector proportions ---
de_ch4 = pd.ExcelFile(str(EDGAR_CH4_NEW)).parse('IPCC 2006', header=9)
et_ch4 = de_ch4[YC_E].apply(pd.to_numeric, errors='coerce').fillna(0).sum().values


def edgar_code_ch4(code):
    return de_ch4[de_ch4['ipcc_code_2006_for_standard_report'] == code][YC_E].apply(
        pd.to_numeric, errors='coerce').fillna(0).sum().values


de_n2o = pd.ExcelFile(str(EDGAR_N2O_NEW)).parse('IPCC 2006', header=9)
et_n2o = de_n2o[YC_E].apply(pd.to_numeric, errors='coerce').fillna(0).sum().values


def edgar_code_n2o(code):
    return de_n2o[de_n2o['ipcc_code_2006_for_standard_report'] == code][YC_E].apply(
        pd.to_numeric, errors='coerce').fillna(0).sum().values


def rcmip_derived(gas, codes):
    if gas == 'CH4':
        em = sum(edgar_code_ch4(c) for c in codes)
        return em / np.where(et_ch4 > 0, et_ch4, 1) * rcmip_ch4
    else:
        em = sum(edgar_code_n2o(c) for c in codes)
        return em / np.where(et_n2o > 0, et_n2o, 1) * rcmip_n2o


# --- Per-category series ----------------------------------------------------
def load_global(cat):
    return pd.read_csv(f'{OUT_DATA}/{cat}/{cat}_global.csv')

# (cat, gas, title, our_series_fn, fao_col, edgar_col, edgar_codes, ylim, note)
def panels():
    g = load_global('ch4_ef')
    yield dict(gas='CH4', title='(a) Enteric fermentation',
               our=g['Total_GgCH4'].values / 1000, fao=g['FAO_published_GgCH4'].values / 1000,
               edgar=g['EDGAR_GgCH4'].values / 1000, rcmip=rcmip_derived('CH4', ['3.A.1']),
               yr=g['Year'].values, ylim=(50, 160))

    g = load_global('ch4_mm')
    yield dict(gas='CH4', title='(b) Manure management',
               our=g['Total_GgCH4'].values / 1000, fao=g['FAO_published_GgCH4'].values / 1000,
               edgar=g['EDGAR_GgCH4'].values / 1000, rcmip=rcmip_derived('CH4', ['3.A.2']),
               yr=g['Year'].values, ylim=(4, 18))

    g = load_global('ch4_rice')
    yield dict(gas='CH4', title='(c) Rice cultivation',
               our=g['Total_GgCH4'].values / 1000, fao=g['FAO_published_GgCH4'].values / 1000,
               edgar=g['EDGAR_GgCH4'].values / 1000, rcmip=rcmip_derived('CH4', ['3.C.7']),
               yr=g['Year'].values, ylim=(15, 40))

    g = load_global('n2o_mm')
    yield dict(gas='N2O', title='(d) Manure management',
               our=g['Total_2006split_GgN2O'].values / 1000, fao=g['FAO_published_GgN2O'].values / 1000,
               edgar=g['EDGAR_GgN2O'].values / 1000, rcmip=rcmip_derived('N2O', ['3.A.2']),
               yr=g['Year'].values, ylim=(0.15, 1.05))

    g = load_global('n2o_ms')
    yield dict(gas='N2O', title='(e) Managed soils',
               our=g['Total_withPRP_2019_GgN2O'].values / 1000, fao=g['FAO_total_GgN2O'].values / 1000,
               edgar=g['EDGAR_total_GgN2O'].values / 1000, rcmip=rcmip_derived('N2O', ['3.C.4', '3.C.5']),
               yr=g['Year'].values, ylim=(1.0, 10.0))


# --- Style ------------------------------------------------------------------
C_OUR = '#e07b39'; C_FAO = '#2166ac'; C_EDG = '#4dac26'; C_RCP = '#d6604d'
SC = '#cccccc'
GK = dict(color='#cccccc', linewidth=0.5, linestyle='--', alpha=0.7)
RLS = (0, (3, 1, 1, 1))


def sax(ax, ylim=None):
    ax.tick_params(labelsize=10, colors='#666666')
    ax.grid(**GK)
    ax.set_xlim(1970, 2020)
    if ylim:
        ax.set_ylim(*ylim)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    for s in ['left', 'bottom']:
        ax.spines[s].set_color(SC); ax.spines[s].set_linewidth(0.8)


fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat:
    ax.set_facecolor('#fafaf8')

P = list(panels())
print('2020 totals (Tg yr-1): cat | LandSyMM | FAOSTAT | EDGAR | RCMIP-derived')
for ax, p in zip(axes.flat, P):
    yr = p['yr']
    ax.fill_between(yr, p['fao'], p['our'], alpha=0.10, color=C_OUR)
    ax.plot(yr, p['rcmip'], color=C_RCP, linewidth=1.8, linestyle=RLS)
    ax.plot(yr, p['edgar'], color=C_EDG, linewidth=1.8, linestyle='-.')
    ax.plot(yr, p['our'], color=C_OUR, linewidth=2.4)
    ax.plot(yr, p['fao'], color=C_FAO, linewidth=2.4, linestyle=':')
    unit = 'CH$_4$' if p['gas'] == 'CH4' else 'N$_2$O'
    ax.set_title(f"{p['title']} - {unit}", fontsize=13, fontweight='bold', color='#1a1a1a', pad=8)
    ax.set_ylabel(f'{unit} (Tg yr$^{{-1}}$)', fontsize=11, color='#444444')
    ax.set_xlabel('Year', fontsize=11, color='#444444')
    sax(ax, p['ylim'])
    print(f"  {p['title']:>28s} | {p['our'][-1]:7.2f} | {p['fao'][-1]:7.2f} | {p['edgar'][-1]:7.2f} | {p['rcmip'][-1]:7.2f}")

# 6th cell: shared legend
lax = axes[1, 2]
lax.axis('off')
handles = [
    Line2D([], [], color=C_OUR, lw=2.4, label='LandSyMM (IPCC Tier-1)'),
    Line2D([], [], color=C_FAO, lw=2.4, ls=':', label='FAOSTAT'),
    Line2D([], [], color=C_EDG, lw=1.8, ls='-.', label='EDGAR 2025'),
    Line2D([], [], color=C_RCP, lw=1.8, ls=RLS, label='RCMIP (CMIP6), EDGAR-proportioned'),
]
lax.legend(handles=handles, loc='center', fontsize=12, framealpha=0.95,
           edgecolor=SC, fancybox=False, title='Series', title_fontsize=12,
           handlelength=2.6, labelspacing=0.8)

plt.tight_layout()
out = FIG_DIR + 'paper_fig2_global_totals.png'
plt.savefig(out, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print('Saved:', out)
