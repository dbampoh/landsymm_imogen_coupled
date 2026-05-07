"""
hybrid_comparator_plotting.py
==============================
Component C, Step 7: visualizes our integrated GHG emission trajectories
against the HYBRID full-trajectory external comparator built by
hybrid_comparator_processing.py.

WHAT'S DIFFERENT FROM external_comparators_plotting.py
-------------------------------------------------------
The earlier external-comparators plot showed budget references as historical
step-bands only (no scenario-period reference at all). This plot extends the
comparator across the full 1900-2100 window using the hybrid construction
described in hybrid_comparator_processing.py:
  - 1900-1979: RCMIP+FAIR baseline (or RCMIP-SLAND+FAIR for CO2)
  - 1980-2020: budget-anchored top-down values (GMB/GNB/GCB)
  - 2021-2100: RCMIP+FAIR baseline again (or RCMIP-SLAND+FAIR for CO2)
  - 5-year transition blends at the boundaries

LAYOUT (3 rows × 3 cols)
-------------------------
Row 1: full-trajectory comparison per gas (one panel each)
   - Per-scenario integrated total (10-yr running mean)
   - Hybrid comparator best line (per-scenario, since RCMIP_total varies)
   - Hybrid comparator uncertainty band per-scenario (shaded)
   - Source-segment shading at the bottom of the panel as a thin strip

Row 2: zoomed-in view of the historical period (1900-2020) — same content
   but x-limited so the budget-anchored agreement is legible. (We omit
   this — better to use a single full-range panel and let the legend
   document.)

We'll instead use 2 rows: top = trajectories, bottom = residuals over time.

INPUT FILES
-----------
   integrated_emissions_ch4.csv  /  _n2o.csv  /  _co2.csv
   hybrid_comparator_ch4.csv     /  _n2o.csv  /  _co2.csv

OUTPUT
------
   hybrid_comparator_comparison.png  (4800×3300, aspect 1.45)
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
                                # (RCMIP scenario records begin at 2015)
CMP_COLOR = '#08519c'

UNIT = {
    'CH4': 'Mt CH4 yr$^{-1}$',
    'N2O': 'Mt N2O yr$^{-1}$',
    'CO2': 'Mt CO2 yr$^{-1}$',
}

# Load
df_int = {gas: pd.read_csv(os.path.join(DATA_DIR, f'integrated_emissions_{gas.lower()}.csv'))
          for gas in ['CH4', 'N2O', 'CO2']}
df_hyb = {gas: pd.read_csv(os.path.join(DATA_DIR, f'hybrid_comparator_{gas.lower()}.csv'))
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
    """10-yr running mean computed separately on the historical (≤ HIST_END)
    and scenario (> HIST_END) segments to avoid stitching across the boundary."""
    yrs = np.asarray(years); vs = np.asarray(vals)
    out = np.full_like(vs, np.nan, dtype=float)
    mh = yrs <= hist_end; ms = yrs > hist_end
    if mh.any(): out[mh] = rmean(vs[mh])
    if ms.any(): out[ms] = rmean(vs[ms])
    return out


def split_by_period(years, vals, hist_end=HIST_END):
    """Return (hist_years, hist_vals, scen_years, scen_vals) split at hist_end.
    The historical-end point is included as the FIRST scenario point too,
    so the scenario line visually connects to the historical line."""
    years = np.asarray(years); vals = np.asarray(vals)
    mh = years <= hist_end
    ms = years >= hist_end       # include hist_end so connection is drawn
    return years[mh], vals[mh], years[ms], vals[ms]


# =============================================================================
# FIGURE
# =============================================================================
print("Generating hybrid-comparator plot ...", flush=True)
fig, axes = plt.subplots(2, 3, figsize=(20, 11),
                          gridspec_kw={'height_ratios': [2.4, 1]})
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')

fig.suptitle(
    'Integrated GHG Emission Trajectories vs Hybrid Full-Trajectory Comparator | 1900-2100 | Five SSP-RCP Scenarios\n'
    'Comparator: 1900-1979 = RCMIP+FAIR-ERF (or RCMIP-SLAND+FAIR for CO2); '
    '1980-2020 = budget top-down (GMB/GNB/GCB); 2021-2100 = RCMIP+FAIR continued',
    fontsize=11, fontweight='bold', color='#1a1a1a', y=0.995)


def panel_traj(ax, gas, ylim=None):
    df = df_int[gas]; hyb = df_hyb[gas]

    # ---------------- historical period (≤ HIST_END) drawn as a single line ----
    # All scenarios share identical pre-HIST_END values for both integrated total
    # and comparator. We draw them once in black to avoid the visual confusion
    # of stacking 5 identical lines on top of each other.
    sub_int_h = df[df.Scenario == SCENARIOS[0]].sort_values('Year')
    sub_hyb_h = hyb[hyb.Scenario == SCENARIOS[0]].sort_values('Year')
    yrs_full = sub_int_h['Year'].values

    h_yrs, h_int_vals, _, _ = split_by_period(yrs_full, sub_int_h['Total_Mt'].values)
    h_yrs, h_hyb_vals, _, _ = split_by_period(yrs_full, sub_hyb_h['Comparator_Mt'].values)
    h_yrs, h_hyb_lo, _, _   = split_by_period(yrs_full, sub_hyb_h['Comparator_lo_Mt'].values)
    h_yrs, h_hyb_hi, _, _   = split_by_period(yrs_full, sub_hyb_h['Comparator_hi_Mt'].values)

    # Smooth historical integrated total
    h_int_smooth = rmean(h_int_vals)

    # Comparator uncertainty band (historical)
    ax.fill_between(h_yrs, h_hyb_lo, h_hyb_hi,
                    color=HIST_COLOR, alpha=0.05, edgecolor='none', zorder=2)
    # Comparator best (historical)
    ax.plot(h_yrs, h_hyb_vals, color=HIST_COLOR, lw=1.4, ls='--',
            alpha=0.5, zorder=4)
    # Integrated total (historical)
    ax.plot(h_yrs, h_int_smooth, color=HIST_COLOR, lw=2.6, ls='-',
            alpha=0.95, zorder=6, label='Historical (1900-2014)')

    # ---------------- scenario period (> HIST_END) per-scenario in colour ----
    for scen in SCENARIOS:
        c = SCEN_COLORS[scen]
        sub_int = df[df.Scenario == scen].sort_values('Year')
        sub_hyb = hyb[hyb.Scenario == scen].sort_values('Year')
        years = sub_int['Year'].values

        # Compute smoothed integrated total over full series (so the scenario
        # segment running mean uses adjacent scenario points), then split off
        # the post-HIST_END portion (with HIST_END included for visual connection).
        total_smooth = rmean_segmented(years, sub_int['Total_Mt'].values)
        _, _, s_yrs, s_int_smooth = split_by_period(years, total_smooth)

        # Comparator best and bounds for the scenario period
        _, _, s_yrs, s_hyb_best = split_by_period(years, sub_hyb['Comparator_Mt'].values)
        _, _, s_yrs, s_hyb_lo   = split_by_period(years, sub_hyb['Comparator_lo_Mt'].values)
        _, _, s_yrs, s_hyb_hi   = split_by_period(years, sub_hyb['Comparator_hi_Mt'].values)

        ax.fill_between(s_yrs, s_hyb_lo, s_hyb_hi,
                        color=c, alpha=0.07, edgecolor='none', zorder=2)
        ax.plot(s_yrs, s_hyb_best, color=c, lw=1.4, ls='--',
                alpha=0.6, zorder=4)
        ax.plot(s_yrs, s_int_smooth, color=c, lw=2.6, ls='-',
                alpha=0.95, zorder=6, label=scen)

    # Shade the budget-anchored region for visual cue
    sub_seg = hyb[hyb.Scenario == SCENARIOS[0]]
    bud_years = sub_seg[sub_seg['Source_segment'] == 'budget_TD']['Year'].values
    if len(bud_years):
        ax.axvspan(bud_years.min() - 0.5, bud_years.max() + 0.5,
                   facecolor='#f5e8d0', alpha=0.30, zorder=1)
        if ylim is not None:
            txt_y = ylim[1] * 0.96
        else:
            txt_y = ax.get_ylim()[1] * 0.96
        ax.text((bud_years.min() + bud_years.max()) / 2, txt_y,
                'Budget-anchored\n(top-down inversions)', ha='center', va='top',
                fontsize=7.5, color='#8a6d2f', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fcf6e6',
                          edgecolor='#d4b984', alpha=0.85), zorder=3)

    ax.axhline(0, color='#888888', lw=0.7, alpha=0.45)
    ax.axvline(1970, color='#888888', lw=0.6, ls=':', alpha=0.55)
    ax.axvline(HIST_END + 0.5, color='#888888', lw=0.7, ls=':', alpha=0.65)
    if ylim is not None: ax.set_ylim(*ylim)
    ax.set_title(f'{gas} — Integrated vs Hybrid Comparator', **TK)
    ax.set_ylabel(f'{gas} ({UNIT[gas]})', **LK)
    ax.set_xlabel('Year', **LK)
    sax(ax)


panel_traj(axes[0, 0], 'CH4', ylim=(0, 1300))
panel_traj(axes[0, 1], 'N2O', ylim=(0, 50))
panel_traj(axes[0, 2], 'CO2', ylim=(-30000, 140000))


def panel_residual(ax, gas, ylim=None):
    """Residual = our integrated total − hybrid comparator (smoothed).
    Historical period drawn in black (identical across scenarios pre-HIST_END);
    scenario period drawn per-scenario in colour."""
    df = df_int[gas]; hyb = df_hyb[gas]

    ax.axhline(0, color='#888888', lw=0.7, alpha=0.5)

    # ----- historical residual (≤ HIST_END) drawn once in black -----
    sub_int_h = df[df.Scenario == SCENARIOS[0]].sort_values('Year')
    sub_hyb_h = hyb[hyb.Scenario == SCENARIOS[0]].sort_values('Year')
    yrs_full = sub_int_h['Year'].values
    res_full_raw = sub_int_h['Total_Mt'].values - sub_hyb_h['Comparator_Mt'].values

    # Smooth on the historical segment only
    h_yrs, h_res_raw, _, _ = split_by_period(yrs_full, res_full_raw)
    h_res_smooth = rmean(h_res_raw)
    ax.plot(h_yrs, h_res_smooth, color=HIST_COLOR, lw=1.8,
            label='Historical (1900-2014)', zorder=4)

    # ----- scenario residual (> HIST_END) per-scenario in colour -----
    for scen in SCENARIOS:
        c = SCEN_COLORS[scen]
        sub_int = df[df.Scenario == scen].sort_values('Year')
        sub_hyb = hyb[hyb.Scenario == scen].sort_values('Year')
        years = sub_int['Year'].values
        residual_raw = sub_int['Total_Mt'].values - sub_hyb['Comparator_Mt'].values
        residual_smooth = rmean_segmented(years, residual_raw)
        _, _, s_yrs, s_res = split_by_period(years, residual_smooth)
        ax.plot(s_yrs, s_res, color=c, lw=1.6, label=scen, zorder=3)

        # Gas-aware label at 2100:
        #   CH4 / N2O: percent of comparator denominator (stable, strongly positive)
        #   CO2: absolute Pg C/yr (denominator can be small or negative —
        #        e.g. SSP1-2.6 hybrid 2100 ≈ -17 Gt due to RCMIP DAC; percent
        #        ratio sign-flip would mislead).
        idx_2100 = np.where(years == 2100)[0]
        if len(idx_2100):
            v_2100 = residual_smooth[idx_2100[0]]
            if gas == 'CO2':
                v_PgC = v_2100 / 3666.67   # Mt CO2/yr → Pg C/yr
                ax.annotate(f'{v_PgC:+.2f} PgC/yr',
                            xy=(2100, v_2100),
                            xytext=(2102, v_2100), color=c, fontsize=7.5,
                            fontweight='bold', va='center')
            else:
                cmp_2100 = sub_hyb[sub_hyb.Year == 2100].iloc[0]['Comparator_Mt']
                if cmp_2100 != 0:
                    pct = 100.0 * v_2100 / cmp_2100
                    ax.annotate(f'{pct:+.0f}%',
                                xy=(2100, v_2100),
                                xytext=(2102, v_2100), color=c, fontsize=8,
                                fontweight='bold', va='center')

    # Shade comparator uncertainty as a horizontal band: ±max bound offset
    sub_hyb_any = hyb[hyb.Scenario == SCENARIOS[0]].sort_values('Year')
    yrs = sub_hyb_any['Year'].values
    lo = sub_hyb_any['Comparator_lo_Mt'].values - sub_hyb_any['Comparator_Mt'].values
    hi = sub_hyb_any['Comparator_hi_Mt'].values - sub_hyb_any['Comparator_Mt'].values
    ax.fill_between(yrs, lo, hi, color=CMP_COLOR, alpha=0.08, edgecolor='none')

    ax.axvline(1970, color='#888888', lw=0.6, ls=':', alpha=0.5)
    ax.axvline(HIST_END + 0.5, color='#888888', lw=0.7, ls=':', alpha=0.65)
    if ylim is not None: ax.set_ylim(*ylim)
    ax.set_title(f'Δ {gas}: Our integrated − hybrid comparator (10-yr running mean)',
                 fontsize=10, fontweight='bold', color='#1a1a1a', pad=4)
    ax.set_ylabel(f'Δ ({UNIT[gas]})', **LK)
    ax.set_xlabel('Year', **LK)
    sax(ax)


# Compute reasonable y-limits for residual panels
def auto_ylim_residual(gas):
    df = df_int[gas]; hyb = df_hyb[gas]
    all_residuals = []
    for scen in SCENARIOS:
        sub_int = df[df.Scenario == scen].sort_values('Year')
        sub_hyb = hyb[hyb.Scenario == scen].sort_values('Year')
        years = sub_int['Year'].values
        residual = sub_int['Total_Mt'].values - sub_hyb['Comparator_Mt'].values
        residual_smooth = rmean_segmented(years, residual)
        all_residuals.extend(residual_smooth.tolist())
    arr = np.array(all_residuals)
    rng = arr.max() - arr.min()
    return (arr.min() - 0.08 * rng, arr.max() + 0.08 * rng)


panel_residual(axes[1, 0], 'CH4', ylim=auto_ylim_residual('CH4'))
panel_residual(axes[1, 1], 'N2O', ylim=auto_ylim_residual('N2O'))
panel_residual(axes[1, 2], 'CO2', ylim=auto_ylim_residual('CO2'))


# Comprehensive legends
scen_handles = [Line2D([], [], color=SCEN_COLORS[s], lw=2.6, ls='-', label=s)
                for s in SCENARIOS]
hist_handle = Line2D([], [], color=HIST_COLOR, lw=2.6, ls='-',
                     label=f'Historical (1900-{HIST_END})')

for col, gas in enumerate(['CH4', 'N2O', 'CO2']):
    cmp_handles = [
        Line2D([], [], color='#666666', lw=1.4, ls='--',
               label='Hybrid comparator best'),
        Patch(facecolor='#cccccc', alpha=0.30, edgecolor='none',
              label='Comparator uncertainty band'),
        Patch(facecolor='#f5e8d0', alpha=0.45, edgecolor='#d4b984',
              label='Budget-anchored region'),
    ]
    handles = [hist_handle] + scen_handles + cmp_handles
    axes[0, col].legend(handles=handles, fontsize=7.4, loc='upper left',
                        framealpha=0.93, edgecolor=SC, fancybox=False,
                        ncol=1, handlelength=2.0, handletextpad=0.5,
                        labelspacing=0.4,
                        title='Period + Scenarios + Comparator',
                        title_fontsize=7.6)

for col, gas in enumerate(['CH4', 'N2O', 'CO2']):
    cmp_band = [Patch(facecolor=CMP_COLOR, alpha=0.08, edgecolor='none',
                       label='Comparator ±1σ band')]
    handles = [hist_handle] + scen_handles + cmp_band
    axes[1, col].legend(handles=handles, fontsize=7.0, loc='upper left',
                        framealpha=0.93, edgecolor=SC, fancybox=False,
                        ncol=1, handlelength=1.8, handletextpad=0.4,
                        labelspacing=0.3)


# Footer
fig.text(
    0.5, 0.005,
    'Hybrid comparator construction: 1900-1979 = RCMIP_total + FAIR-ERF natural baseline (CO2 also subtracts a SLAND-equivalent estimate from GCB, '
    'so the comparator always represents "atmospheric source = what the atmosphere actually receives", semantically consistent with our integrated total). '
    '1980-2020 = budget top-down values (CH4: GMB 2025; N2O: GNB 2024; CO2: GCB 2025 partition EFOS+ELUC-SLAND), linearly interpolated at the period midpoints '
    '(2005, 2015, 2020 for CH4; 1997, 2015, 2020 for N2O; 1965, 1975, 1985, 1995, 2005, 2018 for CO2). 2021-2100 = RCMIP+FAIR-ERF (CO2 with SLAND held at 2014-2023 value). '
    '5-year linear blends at the segment boundaries. Caveat: scenario-period comparator natural component is held constant — divergence between our integrated total and the comparator '
    'in 2021-2100 captures the natural-emission climate-feedback signal that climate emulators conventionally ignore.',
    ha='center', fontsize=6.4, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
              edgecolor='#cccccc', alpha=0.9), wrap=True)

plt.tight_layout(rect=[0, 0.05, 1, 0.96])
out = os.path.join(OUT_DIR, 'hybrid_comparator_comparison.png')
plt.savefig(out, dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f'Saved: {out}', flush=True)
