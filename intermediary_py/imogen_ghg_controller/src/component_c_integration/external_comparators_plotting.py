"""
external_comparators_plotting.py
==================================
Component C, Step 5: visualizes our integrated GHG emission trajectories
(anthropogenic + natural, 1900-2100, 5 SSPs) alongside independent external
comparators built from atmospheric inversions and observation-constrained
global budgets. This is the "does the sum land in the right place?"
sanity check.

PHILOSOPHY
----------
Our integrated total is the global total atmospheric GHG source — what the
atmosphere sees, regardless of whether the source is anthropogenic or natural,
geological or biogenic. The right comparator is therefore the same quantity
measured from atmospheric observations (top-down inversions), not from
anthropogenic-only inventories.

LAYOUT (3 panels, one per gas; 1×3 grid)
----------------------------------------
For each gas:
    - Per-scenario integrated total (10-yr running mean)
    - GMB 2025 / GNB 2024 / GCB 2025 top-down reference as a step-band
      (filled range + dashed best line) over reported decades
    - 1970 (Tier 1 inventory start) and 2020 (historical→scenario splice)
      vertical reference lines

Below the main panel: a residual sub-panel showing
    Our_integrated_period_mean − Reference_best
for each comparator period and each scenario, as a small grouped bar chart.
This makes the magnitude of agreement immediately legible.

INPUT FILES
-----------
    integrated_emissions_ch4.csv / _n2o.csv / _co2.csv
    external_comparators_ch4.csv / _n2o.csv / _co2.csv

OUTPUT
------
    external_comparators_comparison.png  (4800×3300, aspect 1.45)
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
    OUT_C_DATA, OUT_C_FIGS,
)

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', str(OUT_C_DATA))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_C_FIGS))
os.makedirs(OUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# DATA
# -----------------------------------------------------------------------------
df_int = {
    'CH4': pd.read_csv(os.path.join(DATA_DIR, 'integrated_emissions_ch4.csv')),
    'N2O': pd.read_csv(os.path.join(DATA_DIR, 'integrated_emissions_n2o.csv')),
    'CO2': pd.read_csv(os.path.join(DATA_DIR, 'integrated_emissions_co2.csv')),
}
df_cmp = {
    'CH4': pd.read_csv(os.path.join(DATA_DIR, 'external_comparators_ch4.csv')),
    'N2O': pd.read_csv(os.path.join(DATA_DIR, 'external_comparators_n2o.csv')),
    'CO2': pd.read_csv(os.path.join(DATA_DIR, 'external_comparators_co2.csv')),
}

SCENARIOS = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP4-6.0', 'SSP5-8.5']
SCEN_COLORS = {
    'SSP1-2.6': '#1a9850', 'SSP2-4.5': '#2c7bb6', 'SSP3-7.0': '#d7191c',
    'SSP4-6.0': '#fdae61', 'SSP5-8.5': '#762a83',
}
HIST_COLOR = '#1a1a1a'         # black for the pre-divergence historical period
HIST_END = 2014                # last year before RCMIP scenarios diverge
CMP_COLOR = '#08519c'       # darker blue for the external comparator (TD inversions)

# Source label for each gas (for legend)
SOURCE_SHORT = {
    'CH4': 'GMB 2025 top-down inversions',
    'N2O': 'GNB 2024 top-down inversions',
    'CO2': 'GCB 2025 (EFOS+ELUC−SLAND)',
}
UNIT = {
    'CH4': 'Mt CH4 yr$^{-1}$',
    'N2O': 'Mt N2O yr$^{-1}$',
    'CO2': 'Mt CO2 yr$^{-1}$',
}

# -----------------------------------------------------------------------------
# STYLE
# -----------------------------------------------------------------------------
SC = '#cccccc'
GK = dict(color='#cccccc', lw=0.5, ls='--', alpha=0.7)
TK = dict(fontsize=11, fontweight='bold', color='#1a1a1a', pad=6)
LK = dict(fontsize=9, color='#444444')
PK = dict(labelsize=8.5, colors='#666666')

def sax(ax, xlim=(1900, 2105)):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(*xlim)
    for sp in ['top']: ax.spines[sp].set_visible(False)
    for sp in ['left', 'bottom', 'right']:
        ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

def rmean(arr, w=10):
    return pd.Series(arr).rolling(w, center=True, min_periods=1).mean().values

def rmean_segmented(years, vals, hist_end=HIST_END):
    yrs = np.asarray(years); vs = np.asarray(vals)
    out = np.full_like(vs, np.nan, dtype=float)
    mh = yrs <= hist_end; ms = yrs > hist_end
    if mh.any(): out[mh] = rmean(vs[mh])
    if ms.any(): out[ms] = rmean(vs[ms])
    return out


def split_by_period(years, vals, hist_end=HIST_END):
    """Return (hist_years, hist_vals, scen_years, scen_vals) split at hist_end.
    hist_end is in BOTH segments for visual connection."""
    years = np.asarray(years); vals = np.asarray(vals)
    mh = years <= hist_end
    ms = years >= hist_end
    return years[mh], vals[mh], years[ms], vals[ms]


def step_band(ax, df_cmp_gas, color=CMP_COLOR, alpha=0.18, label_band=None,
              label_best=None):
    """Render the comparator as horizontal step-bands over each reported period."""
    first = True
    for _, row in df_cmp_gas.iterrows():
        x0, x1 = row.Year_start - 0.5, row.Year_end + 0.5
        ax.fill_between([x0, x1], [row.Lo_Mt, row.Lo_Mt],
                        [row.Hi_Mt, row.Hi_Mt],
                        color=color, alpha=alpha, edgecolor='none',
                        label=label_band if first else None)
        ax.plot([x0, x1], [row.Best_Mt, row.Best_Mt], color=color, lw=2.0,
                ls='--', label=label_best if first else None,
                solid_capstyle='butt')
        first = False


# =============================================================================
# FIGURE
# =============================================================================
print("Generating external-comparators plot ...", flush=True)
fig, axes = plt.subplots(2, 3, figsize=(20, 11),
                          gridspec_kw={'height_ratios': [2.4, 1]})
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')

fig.suptitle(
    'Integrated GHG Emission Trajectories vs Independent External Comparators | 1900-2100 | Five SSP-RCP Scenarios\n'
    'Our integrated total = anthropogenic (RCMIP-substituted CH4/N2O or RCMIP EFOS for CO2) + natural (LPJ-GUESS DGVM)\n'
    'External comparator = atmospheric-inversion top-down totals (GMB 2025 / GNB 2024) or budget partition (GCB 2025)',
    fontsize=11, fontweight='bold', color='#1a1a1a', y=0.995)


# -----------------------------------------------------------------------------
# Top row: trajectories
# -----------------------------------------------------------------------------
def panel_traj(ax, gas, ylim=None):
    df = df_int[gas]; cmp = df_cmp[gas]

    # Comparator (top-down) first so it's behind the lines
    step_band(ax, cmp, label_band=f'{SOURCE_SHORT[gas]} range',
              label_best=f'{SOURCE_SHORT[gas]} best')

    # Historical period — drawn once in black (identical across scenarios pre-HIST_END)
    sub_h = df[df.Scenario == SCENARIOS[0]].sort_values('Year')
    yrs_full = sub_h['Year'].values
    total_full = rmean_segmented(yrs_full, sub_h['Total_Mt'].values)
    h_yrs, h_total, _, _ = split_by_period(yrs_full, total_full)
    ax.plot(h_yrs, h_total, color=HIST_COLOR, lw=2.4, alpha=0.95,
            zorder=5, label=f'Historical (1900-{HIST_END})')

    # Scenario period — per-scenario lines
    for scen in SCENARIOS:
        sub = df[df.Scenario == scen].sort_values('Year')
        years = sub['Year'].values
        total = rmean_segmented(years, sub['Total_Mt'].values)
        _, _, s_yrs, s_total = split_by_period(years, total)
        ax.plot(s_yrs, s_total, color=SCEN_COLORS[scen], lw=2.4, alpha=0.95,
                zorder=5, label=scen)

    ax.axhline(0, color='#888888', lw=0.7, alpha=0.45)
    ax.axvline(1970, color='#888888', lw=0.6, ls=':', alpha=0.55)
    ax.axvline(HIST_END + 0.5, color='#888888', lw=0.7, ls=':', alpha=0.65)
    if ylim is not None: ax.set_ylim(*ylim)
    ax.set_title(f'{gas} — Integrated Total vs Top-Down', **TK)
    ax.set_ylabel(f'{gas} ({UNIT[gas]})', **LK)
    ax.set_xlabel('Year', **LK)
    sax(ax)


panel_traj(axes[0, 0], 'CH4', ylim=(0, 1300))
panel_traj(axes[0, 1], 'N2O', ylim=(0, 50))
panel_traj(axes[0, 2], 'CO2', ylim=(-30000, 140000))


# -----------------------------------------------------------------------------
# Bottom row: per-period residuals  (Our − Comparator best, per scenario)
# -----------------------------------------------------------------------------
def panel_residuals(ax, gas):
    df = df_int[gas]; cmp = df_cmp[gas]

    n_periods = len(cmp)
    n_scen = len(SCENARIOS)
    width = 0.78 / n_scen
    x_periods = np.arange(n_periods)

    # For each scenario, compute period-mean integrated total minus comparator best
    for i, scen in enumerate(SCENARIOS):
        residuals = []
        for _, row in cmp.iterrows():
            sub = df[(df.Scenario == scen)
                      & (df.Year >= row.Year_start)
                      & (df.Year <= row.Year_end)]
            our = sub['Total_Mt'].mean()
            residuals.append(our - row.Best_Mt)
        # Bar position offset for this scenario
        offsets = x_periods + (i - (n_scen - 1) / 2) * width
        ax.bar(offsets, residuals, width=width * 0.9,
               color=SCEN_COLORS[scen], alpha=0.85,
               edgecolor='white', linewidth=0.4, label=scen)

    # Shade the comparator uncertainty range as a horizontal band per period
    for j, (_, row) in enumerate(cmp.iterrows()):
        lo = row.Lo_Mt - row.Best_Mt   # negative
        hi = row.Hi_Mt - row.Best_Mt   # positive
        ax.fill_between([j - 0.5, j + 0.5], [lo, lo], [hi, hi],
                         color=CMP_COLOR, alpha=0.10, edgecolor='none')

    ax.axhline(0, color='#888888', lw=0.7, alpha=0.5)
    ax.set_xticks(x_periods)
    ax.set_xticklabels(cmp['Period_label'].values, fontsize=8)
    ax.set_title(f'{gas} residual: Our integrated − comparator best',
                 fontsize=10, fontweight='bold', color='#1a1a1a', pad=4)
    ax.set_ylabel(f'Δ ({UNIT[gas]})', **LK)
    ax.set_xlabel('Reference period', **LK)
    ax.tick_params(**PK); ax.grid(**GK, axis='y')
    for sp in ['top']: ax.spines[sp].set_visible(False)
    for sp in ['left', 'bottom', 'right']:
        ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)


panel_residuals(axes[1, 0], 'CH4')
panel_residuals(axes[1, 1], 'N2O')
panel_residuals(axes[1, 2], 'CO2')


# -----------------------------------------------------------------------------
# Comprehensive legends: every panel self-contained
# -----------------------------------------------------------------------------
scen_handles = [Line2D([], [], color=SCEN_COLORS[s], lw=2.4, ls='-', label=s)
                for s in SCENARIOS]
hist_handle  = Line2D([], [], color=HIST_COLOR, lw=2.4, ls='-',
                       label=f'Historical (1900-{HIST_END})')

# Top row: historical + scenarios + comparator best/range
for col, gas in enumerate(['CH4', 'N2O', 'CO2']):
    cmp_handles = [
        Line2D([], [], color=CMP_COLOR, lw=2.0, ls='--',
               label=f'{SOURCE_SHORT[gas]} best'),
        Patch(facecolor=CMP_COLOR, alpha=0.18, edgecolor='none',
              label=f'{SOURCE_SHORT[gas]} range'),
    ]
    handles = [hist_handle] + scen_handles + cmp_handles
    axes[0, col].legend(handles=handles, fontsize=7.6, loc='upper left',
                         framealpha=0.93, edgecolor=SC, fancybox=False,
                         ncol=1, handlelength=2.0, handletextpad=0.5,
                         labelspacing=0.4, title='Period + Scenarios + Comparator',
                         title_fontsize=7.8)

# Bottom row: scenarios + comparator-uncertainty band
for col, gas in enumerate(['CH4', 'N2O', 'CO2']):
    cmp_band = [Patch(facecolor=CMP_COLOR, alpha=0.10, edgecolor='none',
                       label='Comparator uncertainty range')]
    handles = scen_handles + cmp_band
    axes[1, col].legend(handles=handles, fontsize=7.0, loc='upper left',
                         framealpha=0.93, edgecolor=SC, fancybox=False,
                         ncol=1, handlelength=1.8, handletextpad=0.4,
                         labelspacing=0.3)


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
fig.text(
    0.5, 0.005,
    'Our integrated total = anthropogenic (RCMIP-substituted New_total for CH4/N2O; RCMIP EFOS-only for CO2) + natural (LPJ-GUESS DGVM: '
    'wetland + GMB IFW − GMB DCC for CH4; soil + fire for N2O; NEE for CO2). '
    'External comparators are atmospheric-inversion top-down totals (GMB 2025 wraparound figure 1; GNB 2024 figures 11, S6) and '
    'GCB 2025 Table 7 partition EFOS+ELUC-SLAND (= net atmospheric source). Scope = global total atmospheric source '
    '(land + geological systems combined). Comparators are historical-period only since atmospheric inversions cannot be projected.',
    ha='center', fontsize=6.6, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
              edgecolor='#cccccc', alpha=0.9), wrap=True)

plt.tight_layout(rect=[0, 0.04, 1, 0.96])
out = os.path.join(OUT_DIR, 'external_comparators_comparison.png')
plt.savefig(out, dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f'Saved: {out}', flush=True)
