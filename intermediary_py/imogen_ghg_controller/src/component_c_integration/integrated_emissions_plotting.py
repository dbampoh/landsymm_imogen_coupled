"""
integrated_emissions_plotting.py
==================================
Component C, Step 3: visualizes the integrated emission trajectories built by
integrated_emissions_processing.py and contextualizes them against:

  (a) RCMIP published anthropogenic totals (the "what climate models use as
      anthropogenic" baseline before our substitution)
  (b) "Default total" = RCMIP_total + FAIR-ERF natural baseline (the
      conventional anthropogenic + natural framing for climate emulators)
  (c) Historical-period observation-constrained ranges from GMB 2025, GNB 2024,
      GCB 2025 (rendered as step bands in the historical period only)

LAYOUT  (6 panels, 2 rows × 3 columns)
--------------------------------------
  Row 1: Integrated trajectories per gas (CH4, N2O, CO2)
    Lines per scenario:
      - RCMIP_total            (dashed, scenario-colored, lw 1.0)  : pre-substitution
      - Our_anthro             (solid thin, scenario-colored, lw 1.4)
      - LPJ_natural            (dotted thick, scenario-colored, lw 2.0)
      - Our_integrated_total   (solid thick, scenario-colored, lw 2.6) : the headline
    Shared references (one per panel):
      - FAIR-ERF natural       (gray thin dashed, lw 1.2)
      - Default_total          (gray dotted thick, lw 1.4)
      - Historical budget step bands (GMB/GNB/GCB), light blue fill

  Row 2: ΔIntegrated panels (Our_integrated_total − Default_total)
    One filled band per scenario, with percentage-at-2100 annotation.
    Shows the net effect of replacing (RCMIP_anthro, FAIR_natural) with
    (Our_anthro_post_sub, LPJ_natural).

INPUT FILES
-----------
  integrated_emissions_ch4.csv
  integrated_emissions_n2o.csv
  integrated_emissions_co2.csv

OUTPUT
------
  integrated_emissions_comparison.png  (4800×3300, aspect 1.45)
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

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', str(OUT_C_DATA))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_C_FIGS))
os.makedirs(OUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# DATA
# -----------------------------------------------------------------------------
df_ch4 = pd.read_csv(os.path.join(DATA_DIR, 'integrated_emissions_ch4.csv'))
df_n2o = pd.read_csv(os.path.join(DATA_DIR, 'integrated_emissions_n2o.csv'))
df_co2 = pd.read_csv(os.path.join(DATA_DIR, 'integrated_emissions_co2.csv'))

SCENARIOS = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP4-6.0', 'SSP5-8.5']
SCEN_COLORS = {
    'SSP1-2.6': '#1a9850',   # green
    'SSP2-4.5': '#2c7bb6',   # blue
    'SSP3-7.0': '#d7191c',   # red
    'SSP4-6.0': '#fdae61',   # orange (saturated)
    'SSP5-8.5': '#762a83',   # purple
}
HIST_COLOR = '#1a1a1a'         # black for the pre-divergence historical period
HIST_END = 2014                # last year before RCMIP scenarios diverge
                                # (RCMIP scenario records begin at 2015)

# -----------------------------------------------------------------------------
# BUDGET REFERENCE VALUES (historical period only; documented in PROJECT_HANDOFF.md §6)
# -----------------------------------------------------------------------------
# GMB 2025 wetland + IFW − DCC, in Mt CH4/yr (combined natural CH4 best+range)
# Best: wetland_best + IFW_best (112) − DCC_best (-23). Same for low/hi.
GMB_PERIODS_CH4 = [   # (y0, y1, wet_best, wet_lo, wet_hi)
    (2000, 2009, 159, 119, 203),
    (2010, 2019, 153, 116, 189),
    (2020, 2020, 161, 131, 198),
]
def gmb_combined(p):
    _, _, b, lo, hi = p
    return b + 112 - 23, lo + 49 + (-36), hi + 202 + (-9)

# GNB 2024 natural soil baseline + perturbed subtotal, Tg N → Tg N2O
GNB_PERIODS_N = [    # (y0, y1, base_best, base_lo, base_hi, pert_best, pert_lo, pert_hi)
    (1980, 1989, 6.4, 3.9, 8.5, -0.4, -1.1, 0.7),
    (1990, 1999, 6.4, 3.8, 8.6, -0.5, -1.4, 0.6),
    (2000, 2009, 6.4, 3.9, 8.5, -0.6, -1.9, 0.8),
    (2010, 2019, 6.4, 3.9, 8.6, -0.6, -2.1, 1.2),
    (2020, 2020, 6.4, 3.8, 8.7, -0.6, -2.2, 1.8),
]
def gnb_combined(p):
    _, _, b, blo, bhi, pe, plo, phi = p
    # Tg N → Tg N2O via × 44/28
    f = 44.0/28.0
    return (b+pe)*f, (blo+plo)*f, (bhi+phi)*f

# GCB 2025 NEE, in Pg C/yr → Mt CO2/yr (× 44/12 × 1000)
GCB_PERIODS = [     # (y0, y1, sland, sigs, eluc, sige)
    (1960, 1969, 1.2, 0.5, 1.6, 0.7),
    (1970, 1979, 2.0, 0.8, 1.4, 0.7),
    (1980, 1989, 1.8, 0.8, 1.4, 0.7),
    (1990, 1999, 2.5, 0.6, 1.6, 0.7),
    (2000, 2009, 2.8, 0.7, 1.4, 0.7),
    (2014, 2023, 3.2, 0.9, 1.1, 0.7),
]
PgC_to_MtCO2 = (44.0/12.0) * 1000.0
def gcb_nee_MtCO2(p):
    _, _, s, sigs, e, sige = p
    nee = -(s - e); sig = (sigs**2 + sige**2)**0.5
    return nee * PgC_to_MtCO2, (nee - sig) * PgC_to_MtCO2, (nee + sig) * PgC_to_MtCO2

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
    """10-year centered running mean with min_periods=1 so endpoints stay covered."""
    return pd.Series(arr).rolling(w, center=True, min_periods=1).mean().values


def rmean_segmented(years, vals, hist_end_year=HIST_END):
    """Compute running mean separately for the historical segment (≤ hist_end_year)
    and the scenario segment (> hist_end_year), then concatenate. Avoids stitching
    the running mean across the historical-scenario boundary, where the underlying
    spin-up state differs."""
    yrs = np.asarray(years); vs = np.asarray(vals)
    mask_h = yrs <= hist_end_year
    mask_s = yrs > hist_end_year
    out = np.full_like(vs, np.nan, dtype=float)
    if mask_h.any(): out[mask_h] = rmean(vs[mask_h])
    if mask_s.any(): out[mask_s] = rmean(vs[mask_s])
    return out


def split_by_period(years, vals, hist_end=HIST_END):
    """Return (hist_years, hist_vals, scen_years, scen_vals) split at hist_end.
    hist_end is included in BOTH segments so the scenario lines visually
    connect to the historical line."""
    years = np.asarray(years); vals = np.asarray(vals)
    mh = years <= hist_end
    ms = years >= hist_end
    return years[mh], vals[mh], years[ms], vals[ms]

def step_band(ax, x_pairs, lo_arr, hi_arr, color='#2166ac', alpha=0.16,
              label=None):
    """Draw step-style filled band over historical decade ranges."""
    first = True
    for (x0, x1), lo, hi in zip(x_pairs, lo_arr, hi_arr):
        ax.fill_between([x0 - 0.5, x1 + 0.5], [lo, lo], [hi, hi],
                        color=color, alpha=alpha,
                        label=label if first else None,
                        edgecolor='none')
        first = False

def step_line(ax, x_pairs, vals, color='#2166ac', lw=2.0, ls='--',
              label=None):
    first = True
    for (x0, x1), v in zip(x_pairs, vals):
        ax.plot([x0 - 0.5, x1 + 0.5], [v, v], color=color, lw=lw, ls=ls,
                label=label if first else None, solid_capstyle='butt')
        first = False

# -----------------------------------------------------------------------------
# FIGURE
# -----------------------------------------------------------------------------
print("Generating integrated emissions plot ...", flush=True)
fig, axes = plt.subplots(2, 3, figsize=(20, 11),
                          gridspec_kw={'height_ratios': [2.4, 1]})
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')

fig.suptitle(
    'Integrated GHG Emission Trajectories (Anthropogenic + Natural) | 1900-2100 | Five SSP-RCP Scenarios\n'
    'Anthropogenic: RCMIP-substituted (CH4, N2O) or RCMIP EFOS (CO2)  ·  Natural: LPJ-GUESS DGVM',
    fontsize=12, fontweight='bold', color='#1a1a1a', y=0.995)


def panel_top(ax, df, gas_label, unit_label, ylim=None, draw_budget_band=None):
    """Draw the top-row integrated-trajectory panel for one gas.
       df contains columns: Year, Scenario, Anthro_Mt, Natural_Mt, Total_Mt,
       RCMIP_total_Mt, FAIR_natural_Mt, Default_total_Mt.
       Historical period (≤ HIST_END) is drawn ONCE in black; scenarios
       diverge from HIST_END+1 in their respective scenario colors."""

    # 1. Historical budget step band (shared across scenarios)
    if draw_budget_band is not None:
        draw_budget_band(ax)

    # 2. FAIR-ERF natural reference — single shared line in gray
    fair_default = df[df.Scenario == SCENARIOS[0]].sort_values('Year')
    ax.plot(fair_default['Year'], fair_default['FAIR_natural_Mt'],
            color='#666666', lw=1.2, ls='--', alpha=0.6, zorder=2,
            label='FAIR-ERF v1.3 natural (constant after 2005)' if gas_label != 'CO2' else None)

    # 3. Historical period — drawn once in black for all decomposition layers
    sub_h = df[df.Scenario == SCENARIOS[0]].sort_values('Year')
    yrs_full = sub_h['Year'].values

    # Split each component at HIST_END
    h_yrs, h_rcmip, _, _    = split_by_period(yrs_full, sub_h['RCMIP_total_Mt'].values)
    h_yrs, h_anthro, _, _   = split_by_period(yrs_full, sub_h['Anthro_Mt'].values)
    h_yrs, h_natural, _, _  = split_by_period(yrs_full, sub_h['Natural_Mt'].values)
    h_yrs, h_total, _, _    = split_by_period(yrs_full, sub_h['Total_Mt'].values)
    h_natural_smooth = rmean(h_natural)
    h_total_smooth   = rmean(h_total)

    # Historical layers (all in HIST_COLOR)
    ax.plot(h_yrs, h_rcmip,           color=HIST_COLOR, lw=1.0, ls='--',
            alpha=0.45, zorder=3)
    ax.plot(h_yrs, h_anthro,          color=HIST_COLOR, lw=1.4, ls='-',
            alpha=0.45, zorder=4)
    ax.plot(h_yrs, h_natural_smooth,  color=HIST_COLOR, lw=1.6, ls=':',
            alpha=0.7, zorder=5)
    ax.plot(h_yrs, h_total_smooth,    color=HIST_COLOR, lw=2.6, ls='-',
            alpha=0.95, zorder=7,
            label=f'Historical (1900-{HIST_END})')

    # 4. Scenario period — per-scenario lines
    for scen in SCENARIOS:
        sub = df[df.Scenario == scen].sort_values('Year')
        c = SCEN_COLORS[scen]
        years = sub['Year'].values
        natural_smooth = rmean_segmented(years, sub['Natural_Mt'].values)
        total_smooth   = rmean_segmented(years, sub['Total_Mt'].values)

        # Split each layer (HIST_END included for visual connection)
        _, _, s_yrs, s_rcmip   = split_by_period(years, sub['RCMIP_total_Mt'].values)
        _, _, s_yrs, s_anthro  = split_by_period(years, sub['Anthro_Mt'].values)
        _, _, s_yrs, s_natural = split_by_period(years, natural_smooth)
        _, _, s_yrs, s_total   = split_by_period(years, total_smooth)

        ax.plot(s_yrs, s_rcmip,    color=c, lw=1.0, ls='--', alpha=0.55, zorder=3)
        ax.plot(s_yrs, s_anthro,   color=c, lw=1.4, ls='-',  alpha=0.55, zorder=4)
        ax.plot(s_yrs, s_natural,  color=c, lw=1.6, ls=':',  alpha=0.7,  zorder=5)
        ax.plot(s_yrs, s_total,    color=c, lw=2.6, ls='-',  alpha=0.95, zorder=7,
                label=scen)

    # 5. Vertical reference lines
    ax.axvline(1970, color='#888888', lw=0.6, ls=':', alpha=0.55)
    ax.axvline(HIST_END + 0.5, color='#888888', lw=0.7, ls=':', alpha=0.65)
    ax.axhline(0, color='#888888', lw=0.7, alpha=0.45)

    if ylim is not None:
        ax.set_ylim(*ylim)

    ax.set_title(f'{gas_label} — Integrated Trajectory (anthropogenic + natural)', **TK)
    ax.set_ylabel(f'{gas_label} ({unit_label})', **LK)
    ax.set_xlabel('Year', **LK)
    sax(ax)


def panel_diff(ax, df, gas_label, unit_label, ylim=None):
    """Draw the bottom-row Δ panel: Our_total − Default_total.
       Historical period (≤ HIST_END) drawn once in black; scenarios diverge
       from HIST_END+1 in their respective colors. Smoothed with 10-yr running
       mean (separately on hist and scenario segments). Percentage labels
       at year 2100 per scenario."""
    ax.axhline(0, color='#888888', lw=0.8, alpha=0.5)

    # Historical Δ — drawn once in black
    sub_h = df[df.Scenario == SCENARIOS[0]].sort_values('Year')
    yrs_full = sub_h['Year'].values
    delta_full_raw = sub_h['Total_Mt'].values - sub_h['Default_total_Mt'].values
    h_yrs, h_delta_raw, _, _ = split_by_period(yrs_full, delta_full_raw)
    h_delta = rmean(h_delta_raw)
    ax.fill_between(h_yrs, 0, h_delta, color=HIST_COLOR, alpha=0.10, edgecolor='none')
    ax.plot(h_yrs, h_delta, color=HIST_COLOR, lw=1.8,
            label=f'Historical (1900-{HIST_END})', zorder=4)

    # Scenario Δ per scenario
    for scen in SCENARIOS:
        sub = df[df.Scenario == scen].sort_values('Year')
        c = SCEN_COLORS[scen]
        years = sub['Year'].values
        delta_raw = sub['Total_Mt'].values - sub['Default_total_Mt'].values
        delta = rmean_segmented(years, delta_raw)
        _, _, s_yrs, s_delta = split_by_period(years, delta)
        ax.fill_between(s_yrs, 0, s_delta, color=c, alpha=0.18, edgecolor='none')
        ax.plot(s_yrs, s_delta, color=c, lw=1.6, label=scen, zorder=3)

        # Label at 2100 — gas-aware (see conventional_comparator_plotting.py for rationale):
        #   CH4 and N2O denominators stay strongly positive at 2100 → use percent.
        #   CO2 Default_total can become small/negative at 2100 (e.g. SSP1-2.6
        #   has net-negative DAC, making percent ratio sign-flip and mislead).
        #   Use Pg C/yr for CO2 — natural diagnostic for sink magnitude.
        idx_2100 = np.where(years == 2100)[0]
        if len(idx_2100):
            v_2100 = delta[idx_2100[0]]
            if gas_label == 'CO2':
                # Mt CO2/yr → Pg C/yr by dividing by 44/12*1000 = 3666.67
                v_PgC = v_2100 / 3666.67
                ax.annotate(f'{v_PgC:+.2f} PgC/yr',
                            xy=(2100, v_2100),
                            xytext=(2102, v_2100), color=c, fontsize=7.5,
                            fontweight='bold', va='center')
            else:
                d_2100 = sub[sub['Year'] == 2100].iloc[0]
                denom = d_2100['Default_total_Mt']
                if denom != 0:
                    pct = 100.0 * v_2100 / denom
                    ax.annotate(f'{pct:+.0f}%', xy=(2100, v_2100),
                                xytext=(2102, v_2100), color=c, fontsize=8,
                                fontweight='bold', va='center')

    ax.axvline(1970, color='#888888', lw=0.6, ls=':', alpha=0.5)
    ax.axvline(HIST_END + 0.5, color='#888888', lw=0.7, ls=':', alpha=0.65)
    if ylim is not None: ax.set_ylim(*ylim)
    ax.set_title(f'Δ {gas_label}: Integrated − (RCMIP + FAIR), 10-yr running mean',
                 fontsize=10, fontweight='bold', color='#1a1a1a', pad=4)
    ax.set_ylabel(f'Δ ({unit_label})', **LK)
    ax.set_xlabel('Year', **LK)
    sax(ax, xlim=(1900, 2110))


# -----------------------------------------------------------------------------
# PANEL 1 (top-left): CH4
# -----------------------------------------------------------------------------
def draw_ch4_band(ax):
    pairs = [(p[0], p[1]) for p in GMB_PERIODS_CH4]
    bests = [gmb_combined(p)[0] for p in GMB_PERIODS_CH4]
    los   = [gmb_combined(p)[1] for p in GMB_PERIODS_CH4]
    his   = [gmb_combined(p)[2] for p in GMB_PERIODS_CH4]
    step_band(ax, pairs, los, his, alpha=0.14,
              label='GMB 2025 wet+IFW−DCC range')
    step_line(ax, pairs, bests, color='#2166ac', lw=1.6, ls='--',
              label='GMB 2025 wet+IFW−DCC best')

panel_top(axes[0, 0], df_ch4, 'CH4', 'Mt CH4 yr$^{-1}$',
          ylim=(0, 1300), draw_budget_band=draw_ch4_band)

# -----------------------------------------------------------------------------
# PANEL 2 (top-middle): N2O
# -----------------------------------------------------------------------------
def draw_n2o_band(ax):
    pairs = [(p[0], p[1]) for p in GNB_PERIODS_N]
    bests = [gnb_combined(p)[0] for p in GNB_PERIODS_N]
    los   = [gnb_combined(p)[1] for p in GNB_PERIODS_N]
    his   = [gnb_combined(p)[2] for p in GNB_PERIODS_N]
    step_band(ax, pairs, los, his, alpha=0.14,
              label='GNB 2024 nat+pert range (Mt N2O)')
    step_line(ax, pairs, bests, color='#2166ac', lw=1.6, ls='--',
              label='GNB 2024 nat+pert best')

panel_top(axes[0, 1], df_n2o, 'N2O', 'Mt N2O yr$^{-1}$',
          ylim=(0, 50), draw_budget_band=draw_n2o_band)

# -----------------------------------------------------------------------------
# PANEL 3 (top-right): CO2
# -----------------------------------------------------------------------------
def draw_co2_band(ax):
    pairs = [(p[0], p[1]) for p in GCB_PERIODS]
    bests = [gcb_nee_MtCO2(p)[0] for p in GCB_PERIODS]
    los   = [gcb_nee_MtCO2(p)[1] for p in GCB_PERIODS]
    his   = [gcb_nee_MtCO2(p)[2] for p in GCB_PERIODS]
    step_band(ax, pairs, los, his, alpha=0.14,
              label='GCB 2025 NEE ±1σ (Mt CO2)')
    step_line(ax, pairs, bests, color='#2166ac', lw=1.6, ls='--',
              label='GCB 2025 NEE best')

panel_top(axes[0, 2], df_co2, 'CO2', 'Mt CO2 yr$^{-1}$',
          ylim=(-30000, 140000), draw_budget_band=draw_co2_band)

# -----------------------------------------------------------------------------
# PANEL 4-6 (bottom row): Δ panels
# -----------------------------------------------------------------------------
panel_diff(axes[1, 0], df_ch4, 'CH4', 'Mt CH4 yr$^{-1}$',
           ylim=(-80, 450))
panel_diff(axes[1, 1], df_n2o, 'N2O', 'Mt N2O yr$^{-1}$',
           ylim=(-9, 14))
panel_diff(axes[1, 2], df_co2, 'CO2', 'Mt CO2 yr$^{-1}$',
           ylim=(-25000, 22000))

# -----------------------------------------------------------------------------
# COMPREHENSIVE LEGENDS (every panel self-contained)
# -----------------------------------------------------------------------------
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# Common building blocks
def linestyle_handles():
    return [
        Line2D([], [], color='#888888', lw=1.0, ls='--',
               label='RCMIP_total (anthro pre-sub)'),
        Line2D([], [], color='#888888', lw=1.4, ls='-',
               label='Our_anthro (post-sub)'),
        Line2D([], [], color='#888888', lw=1.6, ls=':',
               label='LPJ-GUESS natural (10-yr mean)'),
        Line2D([], [], color='#1a1a1a', lw=2.6, ls='-',
               label='Integrated total (10-yr mean)'),
        Line2D([], [], color='#666666', lw=1.2, ls='--',
               label='FAIR-ERF natural reference'),
    ]

def scenario_handles(thick=False):
    lw = 2.6 if thick else 1.8
    return [Line2D([], [], color=SCEN_COLORS[s], lw=lw, ls='-', label=s)
            for s in SCENARIOS]

def historical_handle(thick=True):
    lw = 2.6 if thick else 1.8
    return [Line2D([], [], color=HIST_COLOR, lw=lw, ls='-',
                   label=f'Historical (1900-{HIST_END})')]

def budget_handles(gas):
    """Per-gas observation-constrained references for historical-period."""
    if gas == 'CH4':
        return [
            Line2D([], [], color='#2166ac', lw=1.6, ls='--',
                   label='GMB 2025 wet+IFW−DCC best'),
            Patch(facecolor='#2166ac', alpha=0.18, edgecolor='none',
                  label='GMB 2025 range'),
        ]
    elif gas == 'N2O':
        return [
            Line2D([], [], color='#2166ac', lw=1.6, ls='--',
                   label='GNB 2024 nat+pert best'),
            Patch(facecolor='#2166ac', alpha=0.18, edgecolor='none',
                  label='GNB 2024 range'),
        ]
    elif gas == 'CO2':
        return [
            Line2D([], [], color='#2166ac', lw=1.6, ls='--',
                   label='GCB 2025 NEE best'),
            Patch(facecolor='#2166ac', alpha=0.18, edgecolor='none',
                  label='GCB 2025 NEE ±1σ'),
        ]
    return []

# Top row: each panel gets line-styles + historical + scenarios + gas-specific budget refs
# Combined into a single 2-column legend in upper-left
for col, gas in enumerate(['CH4', 'N2O', 'CO2']):
    handles = (linestyle_handles()
               + historical_handle(thick=True)
               + scenario_handles(thick=True)
               + budget_handles(gas))
    axes[0, col].legend(handles=handles, fontsize=6.8, loc='upper left',
                        framealpha=0.93, edgecolor=SC, fancybox=False,
                        ncol=2, columnspacing=0.8, handlelength=1.8,
                        handletextpad=0.4, labelspacing=0.3)

# Bottom row: historical + scenarios legend
for col, gas in enumerate(['CH4', 'N2O', 'CO2']):
    handles = historical_handle(thick=False) + scenario_handles(thick=False)
    axes[1, col].legend(handles=handles, fontsize=7.0, loc='upper left',
                        framealpha=0.93, edgecolor=SC, fancybox=False,
                        ncol=1, handlelength=1.8, handletextpad=0.4,
                        labelspacing=0.3,
                        title='Period', title_fontsize=7.2)

# Footer
fig.text(
    0.5, 0.005,
    'CH4 anthro: rcmip_substitution_ch4.csv New_total (RCMIP non-agri + our IPCC Tier 1 / PLUMv2 ag).  '
    'N2O anthro: rcmip_substitution_n2o.csv New_total (same).  '
    'CO2 anthro: rcmip_co2.csv EFOS only (Emissions|CO2|MAGICC Fossil and Industrial; no Tier 1 substitution exists for CO2). '
    'Natural: LPJ-GUESS combined CH4 = wetland + GMB IFW (+112) − GMB DCC (-23 best); soil + fire N2O; NEE for CO2 (× 44/12 × 1000).  '
    '"Default total" = RCMIP_total + FAIR-ERF natural baseline.  '
    'Vertical dotted lines at 1970 (Tier 1 inventory start) and 2014.5 (historical→scenario splice; RCMIP scenarios diverge from 2015). '
    'Pre-2015 trajectory is identical across scenarios and rendered in BLACK; per-scenario coloured lines begin at 2015.',
    ha='center', fontsize=6.4, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
              edgecolor='#cccccc', alpha=0.9), wrap=True)

plt.tight_layout(rect=[0, 0.04, 1, 0.97])
out = os.path.join(OUT_DIR, 'integrated_emissions_comparison.png')
plt.savefig(out, dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f'Saved: {out}', flush=True)
