"""
conventional_comparator_plotting.py
=====================================
Component C, Step 9 (Option A): visualizes our integrated GHG emission
trajectories against the CONVENTIONAL CLIMATE-EMULATOR full-trajectory
comparator built by conventional_comparator_processing.py.

WHAT THIS PLOT SHOWS
--------------------
For each gas, side-by-side:
  - Our integrated total (anthropogenic [Tier-1-substituted] + natural
    [LPJ-GUESS DGVM]).
  - The "conventional" comparator (RCMIP_total + FAIR-ERF natural baseline)
    that a typical climate emulator would ingest as forcing.

The gap between them is informative:
  - For CH4 / N2O: it's the difference between (a) our Tier-1-substituted
    anthropogenic + LPJ-GUESS natural and (b) raw RCMIP anthropogenic +
    FAIR-ERF natural baseline. Captures BOTH the substitution effect
    (anthropogenic side) AND the LPJ-GUESS climate feedback (natural side).
  - For CO2: it's effectively the LPJ-GUESS-simulated NEE, since both sides
    use the same EFOS for anthropogenic (no Tier-1 substitution exists for
    CO2) and FAIR_natural=0 in our schema. So the gap = LPJ-GUESS NEE itself.
    See the methodological note in conventional_comparator_processing.py.

CONTRAST WITH OPTION B (HYBRID COMPARATOR)
------------------------------------------
The hybrid comparator (built earlier) overlays observation-constrained budget
top-down values for the historical 1980-2020 segment. The conventional
comparator here uses RCMIP+FAIR throughout, including historical, so it's a
purer "what would conventional emulators assume?" reference. The two plots are
complementary — Option B shows agreement with observations during the budget-
anchored historical window; Option A shows the cumulative effect of replacing
the conventional framing with our pipeline.

LAYOUT (3 cols × 2 rows)
------------------------
Row 1: per-gas full-trajectory comparison (one panel each)
   - Historical period (≤ 2014) drawn in BLACK (single shared line per layer).
   - Per-scenario integrated total (10-yr running mean) from 2015.
   - Per-scenario conventional comparator (RCMIP + FAIR) as dashed lines.
   - Vertical reference lines at 1970 (Tier 1 inventory start), 2014.5
     (RCMIP scenario divergence boundary), and a horizontal at zero.

Row 2: residual = Our_integrated − Conventional, smoothed (running mean), one
   line per scenario. Historical residual (≤ 2014) drawn in BLACK; per-scenario
   residuals (≥ 2015) in their respective scenario colours.

INPUT FILES
-----------
   integrated_emissions_ch4.csv  /  _n2o.csv  /  _co2.csv
   conventional_comparator_ch4.csv  /  _n2o.csv  /  _co2.csv

OUTPUT
------
   conventional_comparator_comparison.png  (4800×3300, aspect 1.45)
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

SCENARIOS = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP4-6.0', 'SSP5-8.5']
SCEN_COLORS = {
    'SSP1-2.6': '#1a9850', 'SSP2-4.5': '#2c7bb6', 'SSP3-7.0': '#d7191c',
    'SSP4-6.0': '#fdae61', 'SSP5-8.5': '#762a83',
}
HIST_COLOR = '#1a1a1a'         # black for the pre-divergence historical period
HIST_END = 2014                # last year before RCMIP scenarios diverge

UNIT = {
    'CH4': 'Mt CH4 yr$^{-1}$',
    'N2O': 'Mt N2O yr$^{-1}$',
    'CO2': 'Mt CO2 yr$^{-1}$',
}

# Load data
df_int = {gas: pd.read_csv(os.path.join(DATA_DIR, f'integrated_emissions_{gas.lower()}.csv'))
          for gas in ['CH4', 'N2O', 'CO2']}
df_cmp = {gas: pd.read_csv(os.path.join(DATA_DIR, f'conventional_comparator_{gas.lower()}.csv'))
          for gas in ['CH4', 'N2O', 'CO2']}

# Style
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
    years = np.asarray(years); vals = np.asarray(vals)
    mh = years <= hist_end
    ms = years >= hist_end
    return years[mh], vals[mh], years[ms], vals[ms]


# =============================================================================
# FIGURE
# =============================================================================
print("Generating conventional-comparator plot ...", flush=True)
fig, axes = plt.subplots(2, 3, figsize=(20, 11),
                          gridspec_kw={'height_ratios': [2.4, 1]})
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')

fig.suptitle(
    'Integrated GHG Emission Trajectories vs Conventional Climate-Emulator Comparator | 1900-2100 | Five SSP-RCP Scenarios\n'
    'Conventional comparator = RCMIP_total (anthropogenic) + FAIR-ERF natural baseline (constant after 2005, =0 for CO2)\n'
    'i.e. what a typical climate emulator (FAIR/MAGICC/etc.) would ingest as forcing — no observation anchoring',
    fontsize=11, fontweight='bold', color='#1a1a1a', y=0.995)


# ---- Top row: trajectory comparison ----
def panel_traj(ax, gas, ylim=None):
    df = df_int[gas]; cmp = df_cmp[gas]

    # ----- historical period (≤ HIST_END) drawn ONCE in black -----
    sub_int_h = df[df.Scenario == SCENARIOS[0]].sort_values('Year')
    sub_cmp_h = cmp[cmp.Scenario == SCENARIOS[0]].sort_values('Year')
    yrs_full = sub_int_h['Year'].values

    # Historical integrated total (smoothed)
    h_yrs, h_int_vals, _, _ = split_by_period(yrs_full,
                                               sub_int_h['Total_Mt'].values)
    h_int_smooth = rmean(h_int_vals)
    # Historical conventional comparator (raw — already smooth as it's RCMIP+FAIR)
    h_yrs, h_cmp_vals, _, _ = split_by_period(yrs_full,
                                               sub_cmp_h['Comparator_Mt'].values)

    ax.plot(h_yrs, h_cmp_vals, color=HIST_COLOR, lw=1.4, ls='--',
            alpha=0.55, zorder=4)
    ax.plot(h_yrs, h_int_smooth, color=HIST_COLOR, lw=2.6, ls='-',
            alpha=0.95, zorder=6, label=f'Historical (1900-{HIST_END})')

    # ----- scenario period (> HIST_END) per-scenario in colour -----
    for scen in SCENARIOS:
        c = SCEN_COLORS[scen]
        sub_int = df[df.Scenario == scen].sort_values('Year')
        sub_cmp = cmp[cmp.Scenario == scen].sort_values('Year')
        years = sub_int['Year'].values

        # Smoothed integrated total over full series, then split off post-HIST_END
        total_smooth = rmean_segmented(years, sub_int['Total_Mt'].values)
        _, _, s_yrs, s_int_smooth = split_by_period(years, total_smooth)

        # Conventional comparator — already smooth (RCMIP + constant FAIR)
        _, _, s_yrs, s_cmp = split_by_period(years, sub_cmp['Comparator_Mt'].values)

        ax.plot(s_yrs, s_cmp, color=c, lw=1.4, ls='--', alpha=0.6, zorder=4)
        ax.plot(s_yrs, s_int_smooth, color=c, lw=2.6, ls='-', alpha=0.95,
                zorder=6, label=scen)

    ax.axhline(0, color='#888888', lw=0.7, alpha=0.45)
    ax.axvline(1970, color='#888888', lw=0.6, ls=':', alpha=0.55)
    ax.axvline(HIST_END + 0.5, color='#888888', lw=0.7, ls=':', alpha=0.65)
    if ylim is not None: ax.set_ylim(*ylim)
    ax.set_title(f'{gas} — Integrated vs Conventional Comparator', **TK)
    ax.set_ylabel(f'{gas} ({UNIT[gas]})', **LK)
    ax.set_xlabel('Year', **LK)
    sax(ax)


panel_traj(axes[0, 0], 'CH4', ylim=(0, 1300))
panel_traj(axes[0, 1], 'N2O', ylim=(0, 50))
panel_traj(axes[0, 2], 'CO2', ylim=(-30000, 140000))


# ---- Bottom row: residual = our integrated − conventional comparator ----
def panel_residual(ax, gas, ylim=None):
    df = df_int[gas]; cmp = df_cmp[gas]
    ax.axhline(0, color='#888888', lw=0.7, alpha=0.5)

    # Historical residual drawn once in black
    sub_int_h = df[df.Scenario == SCENARIOS[0]].sort_values('Year')
    sub_cmp_h = cmp[cmp.Scenario == SCENARIOS[0]].sort_values('Year')
    yrs_full = sub_int_h['Year'].values
    res_full_raw = sub_int_h['Total_Mt'].values - sub_cmp_h['Comparator_Mt'].values
    h_yrs, h_res_raw, _, _ = split_by_period(yrs_full, res_full_raw)
    h_res_smooth = rmean(h_res_raw)
    ax.fill_between(h_yrs, 0, h_res_smooth, color=HIST_COLOR, alpha=0.10,
                    edgecolor='none')
    ax.plot(h_yrs, h_res_smooth, color=HIST_COLOR, lw=1.8,
            label=f'Historical (1900-{HIST_END})', zorder=4)

    # Per-scenario residual (≥ HIST_END) in colour
    for scen in SCENARIOS:
        c = SCEN_COLORS[scen]
        sub_int = df[df.Scenario == scen].sort_values('Year')
        sub_cmp = cmp[cmp.Scenario == scen].sort_values('Year')
        years = sub_int['Year'].values
        residual_raw = sub_int['Total_Mt'].values - sub_cmp['Comparator_Mt'].values
        residual_smooth = rmean_segmented(years, residual_raw)
        _, _, s_yrs, s_res = split_by_period(years, residual_smooth)
        ax.fill_between(s_yrs, 0, s_res, color=c, alpha=0.18, edgecolor='none')
        ax.plot(s_yrs, s_res, color=c, lw=1.6, label=scen, zorder=3)

        # Label at 2100 — gas-aware:
        #   For CH4 and N2O the comparator denominator is strongly positive
        #   throughout 2100 in all scenarios, so percent is meaningful.
        #   For CO2 the conventional comparator can be small or net-negative at
        #   2100 (e.g. SSP1-2.6 ≈ -5.7 Gt CO2/yr from RCMIP DAC), making the
        #   percent ratio sign-flip and become misleading. Use absolute Pg C/yr
        #   instead, which is the natural diagnostic for CO2 (it equals the
        #   LPJ-GUESS NEE under the FAIR-natural-CO2=0 convention).
        idx_2100 = np.where(years == 2100)[0]
        if len(idx_2100):
            v_2100 = residual_smooth[idx_2100[0]]
            if gas == 'CO2':
                # Convert Mt CO2/yr to Pg C/yr by dividing by 44/12*1000 = 3666.67
                v_PgC = v_2100 / 3666.67
                ax.annotate(f'{v_PgC:+.2f} PgC/yr',
                            xy=(2100, v_2100),
                            xytext=(2102, v_2100), color=c, fontsize=7.5,
                            fontweight='bold', va='center')
            else:
                d_2100 = sub_cmp[sub_cmp.Year == 2100].iloc[0]
                denom = d_2100['Comparator_Mt']
                if denom != 0:
                    pct = 100.0 * v_2100 / denom
                    ax.annotate(f'{pct:+.0f}%', xy=(2100, v_2100),
                                xytext=(2102, v_2100), color=c, fontsize=8,
                                fontweight='bold', va='center')

    ax.axvline(1970, color='#888888', lw=0.6, ls=':', alpha=0.5)
    ax.axvline(HIST_END + 0.5, color='#888888', lw=0.7, ls=':', alpha=0.65)
    if ylim is not None: ax.set_ylim(*ylim)
    ax.set_title(f'Δ {gas}: Our integrated − conventional comparator (10-yr running mean)',
                 fontsize=10, fontweight='bold', color='#1a1a1a', pad=4)
    ax.set_ylabel(f'Δ ({UNIT[gas]})', **LK)
    ax.set_xlabel('Year', **LK)
    sax(ax, xlim=(1900, 2110))


# Compute reasonable y-limits for residual panels by data range
def auto_ylim_residual(gas):
    df = df_int[gas]; cmp = df_cmp[gas]
    all_residuals = []
    for scen in SCENARIOS:
        sub_int = df[df.Scenario == scen].sort_values('Year')
        sub_cmp = cmp[cmp.Scenario == scen].sort_values('Year')
        years = sub_int['Year'].values
        residual = sub_int['Total_Mt'].values - sub_cmp['Comparator_Mt'].values
        residual_smooth = rmean_segmented(years, residual)
        all_residuals.extend(residual_smooth.tolist())
    arr = np.array(all_residuals)
    rng = arr.max() - arr.min()
    return (arr.min() - 0.10 * rng, arr.max() + 0.10 * rng)


panel_residual(axes[1, 0], 'CH4', ylim=auto_ylim_residual('CH4'))
panel_residual(axes[1, 1], 'N2O', ylim=auto_ylim_residual('N2O'))
panel_residual(axes[1, 2], 'CO2', ylim=auto_ylim_residual('CO2'))


# ---- Comprehensive legends per panel ----
scen_handles = [Line2D([], [], color=SCEN_COLORS[s], lw=2.6, ls='-', label=s)
                for s in SCENARIOS]
hist_handle = Line2D([], [], color=HIST_COLOR, lw=2.6, ls='-',
                      label=f'Historical (1900-{HIST_END})')

for col, gas in enumerate(['CH4', 'N2O', 'CO2']):
    cmp_handle = [Line2D([], [], color='#666666', lw=1.4, ls='--',
                          label='Conventional comparator (RCMIP + FAIR)')]
    handles = [hist_handle] + scen_handles + cmp_handle
    axes[0, col].legend(handles=handles, fontsize=7.4, loc='upper left',
                        framealpha=0.93, edgecolor=SC, fancybox=False,
                        ncol=1, handlelength=2.0, handletextpad=0.5,
                        labelspacing=0.4,
                        title='Period + Scenarios + Comparator',
                        title_fontsize=7.6)

for col, gas in enumerate(['CH4', 'N2O', 'CO2']):
    handles = [hist_handle] + scen_handles
    axes[1, col].legend(handles=handles, fontsize=7.0, loc='upper left',
                        framealpha=0.93, edgecolor=SC, fancybox=False,
                        ncol=1, handlelength=1.8, handletextpad=0.4,
                        labelspacing=0.3,
                        title='Period', title_fontsize=7.2)


# ---- Footer ----
fig.text(
    0.5, 0.005,
    'Conventional comparator = RCMIP_total (anthropogenic from CEDS/CMIP6 SSPs, INDEPENDENT of our Tier-1 substitution) + FAIR-ERF natural '
    'baseline (constant after 2005, =0 for CO2 by FAIR-ERF convention). This is the conventional climate-emulator framing — '
    'INDEPENDENT of our pipeline. Pre-2015 trajectory shared across scenarios and rendered in BLACK; per-scenario coloured lines begin at 2015. '
    'Note for CO2: the gap between our integrated total (= EFOS + LPJ-GUESS NEE, "atmospheric source after the LPJ-GUESS land sink") and the '
    'conventional comparator (= RCMIP_total + 0, "anthropogenic forcing before the climate-emulator carbon cycle removes any sink") is '
    'precisely the LPJ-GUESS-simulated land sink itself. For CH4/N2O the conceptual asymmetry is much smaller. The Δ panels' + ' percentage labels '
    'at 2100 are relative to the conventional comparator.',
    ha='center', fontsize=6.4, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
              edgecolor='#cccccc', alpha=0.9), wrap=True)

plt.tight_layout(rect=[0, 0.05, 1, 0.96])
out = os.path.join(OUT_DIR, 'conventional_comparator_comparison.png')
plt.savefig(out, dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f'Saved: {out}', flush=True)
