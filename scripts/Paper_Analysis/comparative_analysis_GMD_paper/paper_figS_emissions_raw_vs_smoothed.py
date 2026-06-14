"""
paper_figS_emissions_raw_vs_smoothed.py
=======================================
Supplement figure (Almut review comment): the integrated GHG emission time
series handed to IMOGEN, shown BOTH raw (annual) and smoothed (10-year centred
running mean), 1900-2100, for the five SSP-RCP scenarios. Makes transparent (i)
the year-to-year variability and the methodological step discontinuities at the
1970 (Tier-1 inventory start) and 2020 (FAO -> PLUM activity-data hand-off)
transitions that are retained in the forcing, and (ii) the running mean that is
applied only to the figures and the reference series (Sect. 2.3.2, 2.3.4), never
to the driving emissions.

Reads component-C integrated_emissions_{ch4,n2o,co2}.csv. Writes
paper/_media/supplement/figS_emissions_raw_vs_smoothed.png.
"""
import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve()
while _ROOT.name and not (_ROOT / 'intermediary_py' / 'imogen_ghg_controller' / 'src').is_dir():
    if _ROOT.parent == _ROOT:
        break
    _ROOT = _ROOT.parent
_IGC = _ROOT / 'intermediary_py' / 'imogen_ghg_controller'
if str(_IGC) not in _sys.path:
    _sys.path.insert(0, str(_IGC))
from src.shared.paths import OUT_C_DATA

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

DATA = _Path(str(OUT_C_DATA))
OUT = _ROOT / 'paper' / '_media' / 'supplement' / 'figS_emissions_raw_vs_smoothed.png'

SCENARIOS = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP4-6.0', 'SSP5-8.5']
SCEN_COLORS = {'SSP1-2.6': '#1a9850', 'SSP2-4.5': '#2c7bb6', 'SSP3-7.0': '#d7191c',
               'SSP4-6.0': '#fdae61', 'SSP5-8.5': '#762a83'}
HIST_COLOR = '#1a1a1a'
HIST_END = 2014                      # scenarios diverge from 2015
GASES = [('ch4', 'CH$_4$', 'Mt CH$_4$ yr$^{-1}$', 1.0),
         ('n2o', 'N$_2$O', 'Mt N$_2$O yr$^{-1}$', 1.0),
         ('co2', 'CO$_2$', 'Gt CO$_2$ yr$^{-1}$', 1e-3)]   # CO2 Mt -> Gt


def rmean(a, w=10):
    return pd.Series(a).rolling(w, center=True, min_periods=1).mean().values


def seg_smooth(years, vals):
    """10-yr running mean on the historical (<=HIST_END) and scenario (>HIST_END)
    segments separately, so the 2015 divergence is not smoothed across."""
    years = np.asarray(years); vals = np.asarray(vals, dtype=float)
    out = np.full_like(vals, np.nan)
    mh = years <= HIST_END; ms = years > HIST_END
    if mh.any():
        out[mh] = rmean(vals[mh])
    if ms.any():
        out[ms] = rmean(vals[ms])
    return out


fig, axes = plt.subplots(1, 3, figsize=(16, 4.2), squeeze=False)
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat:
    ax.set_facecolor('#fafaf8')

for j, (gas, lab, unit, scale) in enumerate(GASES):
    ax = axes[0][j]
    df = pd.read_csv(DATA / f'integrated_emissions_{gas}.csv')
    # shared historical (<= HIST_END), drawn once in black: raw thin + smoothed thick
    h = df[df.Scenario == SCENARIOS[0]].sort_values('Year')
    hy = h['Year'].values; hv = h['Total_Mt'].values * scale
    mh = hy <= HIST_END
    sm_h = seg_smooth(hy, hv)
    ax.plot(hy[mh], hv[mh], color=HIST_COLOR, lw=0.6, alpha=0.55, zorder=2)
    ax.plot(hy[mh], sm_h[mh], color=HIST_COLOR, lw=1.8, zorder=5)
    # scenario period (>= 2015) per scenario: raw thin + smoothed thick
    for s in SCENARIOS:
        d = df[df.Scenario == s].sort_values('Year')
        y = d['Year'].values; v = d['Total_Mt'].values * scale
        ms = y >= HIST_END + 1
        sm = seg_smooth(y, v)
        c = SCEN_COLORS[s]
        ax.plot(y[ms], v[ms], color=c, lw=0.6, alpha=0.55, zorder=2)
        ax.plot(y[ms], sm[ms], color=c, lw=1.7, zorder=4)
    ax.axvline(1970, color='#888888', lw=0.7, ls=':', alpha=0.7)
    ax.axvline(2020, color='#888888', lw=0.7, ls=':', alpha=0.7)
    ax.text(1970, ax.get_ylim()[1], ' 1970', fontsize=7, color='#666666', va='top', ha='left')
    ax.text(2020, ax.get_ylim()[1], ' 2020', fontsize=7, color='#666666', va='top', ha='left')
    ax.set_title(f'{lab}', fontsize=12, fontweight='bold', color='#1a1a1a')
    ax.set_xlabel('Year', fontsize=9)
    ax.set_ylabel(f'integrated emissions ({unit})', fontsize=9)
    ax.set_xlim(1900, 2100)
    ax.grid(color='#cccccc', lw=0.4, ls='--', alpha=0.6)
    ax.tick_params(labelsize=8)
    for sp in ['top', 'right']:
        ax.spines[sp].set_visible(False)

handles = [
    Line2D([], [], color='0.4', lw=0.8, alpha=0.6, label='raw annual'),
    Line2D([], [], color='0.4', lw=1.8, label='10-year running mean'),
    Line2D([], [], color=HIST_COLOR, lw=1.8, label='shared historical (1900-2014)'),
] + [Line2D([], [], color=SCEN_COLORS[s], lw=1.8, label=s) for s in SCENARIOS]
fig.legend(handles=handles, loc='lower center', ncol=8, fontsize=8,
           frameon=False, bbox_to_anchor=(0.5, -0.06))
fig.suptitle('Integrated GHG emissions handed to IMOGEN: raw annual vs 10-year running mean, 1900-2100',
             fontsize=12)
fig.tight_layout(rect=(0, 0.04, 1, 0.96))
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(str(OUT), dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print('Saved:', OUT)
