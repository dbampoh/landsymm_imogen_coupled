"""
lpjg_historical_scenario_plotting.py
=======================================
Extends the historical 4-panel comparison plot through 2100 with PLUMv2
scenario-driven LPJ-GUESS projections, while keeping the published
historical-period budget benchmarks (GMB 2025, GNB 2024, GCB 2025) and
FAIR-ERF v1.3 natural baseline anchored as in the historical figure.

Forcing:
  Historical (1901-2020): HILDA+v2 land use
  Scenarios   (2021-2100): PLUMv2 SSP-RCP land use, harmonized with
                           HILDA+v2 via the LUH2 protocol

A small flux discontinuity is expected at the 2020/2021 boundary because
each scenario is an independent simulation with its own spin-up state
(LUH2 protocol harmonizes land use, not fluxes). A vertical line at
year 2020 marks the boundary.

INPUT FILES (in DATA_DIR)
-------------------------
  Historical (existing):
    lpjg_co2_annual.csv, lpjg_ch4_annual.csv, lpjg_ch4_combined_annual.csv,
    lpjg_n2o_annual.csv, fair_erf_natural_baseline.csv
  Scenario long-format (one row per Scenario × Year):
    lpjg_co2_annual_scenarios.csv, lpjg_ch4_annual_scenarios.csv,
    lpjg_ch4_combined_annual_scenarios.csv, lpjg_n2o_annual_scenarios.csv

OUTPUT (in OUT_DIR)
-------------------
  lpjg_historical_scenario_comparison.png

PANELS (axis conventions identical to historical plot)
------------------------------------------------------
  Panel 1 (CH4) : LEFT Tg C/yr ; RIGHT Tg CH4/yr
  Panel 2 (N2O) : LEFT Tg N2O/yr ; RIGHT Tg N/yr
                  Main trend = LPJ-GUESS N2O_soil + N2O_fire (combined
                  natural N2O); thin dotted auxiliary line shows N2O_fire
                  alone for breakdown context.
  Panel 3 (CO2) : LEFT Pg CO2/yr ; RIGHT Pg C/yr
  Panel 4       : NEE by scenario (Pg C/yr; secondary Pg CO2/yr).

10-year running means use rolling(10, center=True, min_periods=1) so
the curves extend across the full 1901-2100 range without endpoint
clipping. The running mean is computed independently for the historical
period and for each scenario (no stitching across the 2020-2021 boundary
during the running-mean computation itself).

Each scenario line is drawn natively from year 2021 onwards (in the
scenario's own colour). A separate connector segment is drawn from
the historical 2020 endpoint to the scenario 2021 first point IN THE
HISTORICAL COLOUR, so the visual identity of the bridge across the
boundary belongs to the historical record, not the scenario. This keeps
the plot reading "historical (orange/red) → bridge (orange/red) → each
scenario (its own colour)".

SCENARIO STYLING (IPCC convention)
----------------------------------
  ssp1rcp26 — green   (sustainability)
  ssp2rcp45 — blue    (middle of the road)
  ssp3rcp70 — red     (regional rivalry)
  ssp4rcp60 — orange  (inequality)
  ssp5rcp85 — purple  (fossil-fueled)           [future delivery]
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
    OUT_B_DATA, OUT_B_FIGS,
)

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', str(OUT_B_DATA))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_B_FIGS))
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------
co2_h     = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_co2_annual.csv'))
ch4_h     = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_ch4_annual.csv'))
ch4_cmb_h = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_ch4_combined_annual.csv'))
n2o_h     = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_n2o_annual.csv'))
fair      = pd.read_csv(os.path.join(DATA_DIR, 'fair_erf_natural_baseline.csv'))

co2_s     = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_co2_annual_scenarios.csv'))
ch4_s     = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_ch4_annual_scenarios.csv'))
ch4_cmb_s = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_ch4_combined_annual_scenarios.csv'))
n2o_s     = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_n2o_annual_scenarios.csv'))

years_h = co2_h['Year'].values
SCENARIOS = sorted(co2_s['Scenario'].unique())

# ---------------------------------------------------------------------------
# UNIT CONVERSIONS
# ---------------------------------------------------------------------------
MW_CH4_C = 12.0 / 16.0
MW_N2O_N = 28.0 / 44.0
MW_N_N2O = 44.0 / 28.0
MW_C_CO2 = 44.0 / 12.0

# ---------------------------------------------------------------------------
# BUDGET REFERENCE VALUES (historical-period only)
# ---------------------------------------------------------------------------
GMB_PERIODS = [
    (2000, 2009, '2000-2009', 159, 119, 203),
    (2010, 2019, '2010-2019', 153, 116, 189),
    (2020, 2020, '2020',      161, 131, 198),
]
GNB_PERIODS_N = [
    (1980, 1989, '1980-1989', 6.4, 3.9, 8.5, -0.4, -1.1, 0.7),
    (1990, 1999, '1990-1999', 6.4, 3.8, 8.6, -0.5, -1.4, 0.6),
    (2000, 2009, '2000-2009', 6.4, 3.9, 8.5, -0.6, -1.9, 0.8),
    (2010, 2019, '2010-2019', 6.4, 3.9, 8.6, -0.6, -2.1, 1.2),
    (2020, 2020, '2020',      6.4, 3.8, 8.7, -0.6, -2.2, 1.8),
]
def gnb_combined(p):
    _, _, _, b, blo, bhi, p_, plo, phi = p
    return (b + p_, blo + plo, bhi + phi)

GCB_PERIODS = [
    (1960, 1969, '1960s',     1.2, 0.5, 1.6, 0.7),
    (1970, 1979, '1970s',     2.0, 0.8, 1.4, 0.7),
    (1980, 1989, '1980s',     1.8, 0.8, 1.4, 0.7),
    (1990, 1999, '1990s',     2.5, 0.6, 1.6, 0.7),
    (2000, 2009, '2000s',     2.8, 0.7, 1.4, 0.7),
    (2014, 2023, '2014-2023', 3.2, 0.9, 1.1, 0.7),
]
def gcb_nee(s, sigs, e, sige):
    return -(s - e), np.sqrt(sigs**2 + sige**2)

# ---------------------------------------------------------------------------
# STYLE
# ---------------------------------------------------------------------------
SC = '#cccccc'
GK = dict(color='#cccccc', lw=0.5, ls='--', alpha=0.7)
TK = dict(fontsize=10, fontweight='bold', color='#1a1a1a', pad=6)
LK = dict(fontsize=8.5, color='#444444')
PK = dict(labelsize=8, colors='#666666')

C_LPJG    = '#e07b39'   # historical annual
C_LPJG_R  = '#a04018'   # historical 10-yr mean
C_BUDG    = '#2166ac'   # budget benchmark
C_FW      = '#7b3294'   # CH4 combined (purple)
C_FAIR    = '#1a9641'   # FAIR-ERF (green)
C_FIRE    = '#b35f5f'   # N2O fire

# IPCC scenario palette
SCEN_STYLES = {
    'ssp1rcp26': dict(color='#1a9850', label='SSP1-2.6'),
    'ssp2rcp45': dict(color='#2c7bb6', label='SSP2-4.5'),
    'ssp3rcp70': dict(color='#d7191c', label='SSP3-7.0'),
    'ssp4rcp60': dict(color='#fdae61', label='SSP4-6.0'),
    'ssp5rcp85': dict(color='#762a83', label='SSP5-8.5'),
}

def sax(ax, xlim=(1900, 2105)):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(*xlim)
    for sp in ['top']: ax.spines[sp].set_visible(False)
    for sp in ['left','bottom','right']:
        ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

def step_band_arr(ax, x_pairs, lo_arr, hi_arr, color, alpha=0.20, label=None):
    first = True
    for (x0, x1), lo, hi in zip(x_pairs, lo_arr, hi_arr):
        ax.fill_between([x0 - 0.5, x1 + 0.5], [lo, lo], [hi, hi],
                        color=color, alpha=alpha,
                        label=label if first else None,
                        edgecolor='none')
        first = False

def step_line_arr(ax, x_pairs, vals, color, lw=2.0, ls='-', label=None):
    first = True
    for (x0, x1), v in zip(x_pairs, vals):
        ax.plot([x0 - 0.5, x1 + 0.5], [v, v], color=color, lw=lw, ls=ls,
                label=label if first else None,
                solid_capstyle='butt')
        first = False

def rmean(arr, w=10):
    return pd.Series(arr).rolling(w, center=True, min_periods=1).mean().values

def boundary_line(ax):
    """Mark the historical-scenario boundary at year 2020.5."""
    ax.axvline(2020.5, color='#888888', lw=0.7, ls=':', alpha=0.7)

def connector(ax, hist_y_last, scen_y_first, color, lw=2.0, ls='-', alpha=1.0,
              hist_year_last=2020, scen_year_first=2021):
    """Draw a single connector line segment from the historical endpoint
    to the first scenario point. The segment is drawn in `color` (typically
    the historical color C_LPJG_R) so the visual identity of the bridge
    matches the historical line, not the scenario line.
    """
    ax.plot([hist_year_last, scen_year_first],
            [hist_y_last, scen_y_first],
            color=color, lw=lw, ls=ls, alpha=alpha,
            solid_capstyle='butt')

# ---------------------------------------------------------------------------
# FIGURE
# ---------------------------------------------------------------------------
print("Generating extended (historical+scenario) plot ...", flush=True)
fig, axes = plt.subplots(2, 2, figsize=(16, 11))
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')

scen_label_str = ' & '.join(SCEN_STYLES[s]['label'] for s in SCENARIOS)
fig.suptitle(
    'LPJ-GUESS Natural Emission Global Annual Totals - Historical + Scenarios\n'
    f'1901-2100  |  HILDA+v2 historical (1900-2020) + PLUMv2 scenarios (2021-2100): {scen_label_str}',
    fontsize=11, fontweight='bold', color='#1a1a1a', y=0.998)

# =========================================================================
# PANEL 1: CH4
# =========================================================================
ax = axes[0, 0]

# Historical
ch4_h_C = ch4_h['CH4_TgCH4'].values * MW_CH4_C
ch4_h_cmb_C   = ch4_cmb_h['CombinedDCC_TgCH4_best'].values * MW_CH4_C
ch4_h_cmb_lo  = ch4_cmb_h['CombinedDCC_TgCH4_lo'].values   * MW_CH4_C
ch4_h_cmb_hi  = ch4_cmb_h['CombinedDCC_TgCH4_hi'].values   * MW_CH4_C

# GMB historical band
gmb_pairs   = [(p[0], p[1]) for p in GMB_PERIODS]
gmb_lo_C    = [p[4] * MW_CH4_C for p in GMB_PERIODS]
gmb_hi_C    = [p[5] * MW_CH4_C for p in GMB_PERIODS]
gmb_best_C  = [p[3] * MW_CH4_C for p in GMB_PERIODS]
step_band_arr(ax, gmb_pairs, gmb_lo_C, gmb_hi_C, C_BUDG, alpha=0.22,
              label='GMB 2025 wetlands range [BU, historical]')
step_line_arr(ax, gmb_pairs, gmb_best_C, C_BUDG, lw=2.2, ls='--',
              label='GMB 2025 wetlands best [BU, historical]')

# Historical wetland + IFW + DCC range band (across full 1900-2020)
ax.fill_between(years_h, ch4_h_cmb_lo, ch4_h_cmb_hi, color=C_FW, alpha=0.10,
                label='LPJ wet + GMB IFW + DCC range (historical)')

# Historical lines (annual + running mean)
ax.plot(years_h, ch4_h_C, color=C_LPJG, lw=1.0, alpha=0.55,
        label='LPJ-GUESS wetland CH4 (annual, historical)')
ax.plot(years_h, rmean(ch4_h_C), color=C_LPJG_R, lw=2.0,
        label='LPJ-GUESS wetland CH4 (10-yr mean, historical)')
ax.plot(years_h, ch4_h_cmb_C, color=C_FW, lw=1.6, alpha=0.7,
        label='LPJ wet + IFW − DCC best (historical, +89 net)')

# Compute the historical endpoint values once for the connectors
hist_ch4_C_last     = ch4_h_C[-1]
hist_ch4_rm_C_last  = rmean(ch4_h_C)[-1]
hist_ch4_cmb_C_last = ch4_h_cmb_C[-1]

# Scenarios — drawn natively from 2021, with separate connectors back to historical
for scen in SCENARIOS:
    style = SCEN_STYLES[scen]
    sub = ch4_s[ch4_s.Scenario == scen].sort_values('Year')
    sub_c = ch4_cmb_s[ch4_cmb_s.Scenario == scen].sort_values('Year')
    yrs = sub['Year'].values
    wet_C = sub['CH4_TgCH4'].values * MW_CH4_C
    cmb_C = sub_c['CombinedDCC_TgCH4_best'].values * MW_CH4_C
    wet_rm = rmean(wet_C)

    # Connectors from historical (2020) to scenario (2021), drawn in HISTORICAL color
    connector(ax, hist_ch4_C_last,    wet_C[0],  C_LPJG,   lw=1.0, alpha=0.5)
    connector(ax, hist_ch4_rm_C_last, wet_rm[0], C_LPJG_R, lw=2.0)
    connector(ax, hist_ch4_cmb_C_last, cmb_C[0], C_FW,     lw=1.6, ls=':')

    # Scenario lines from 2021 onwards, in scenario color
    ax.plot(yrs, wet_C, color=style['color'], lw=1.0, alpha=0.5)
    ax.plot(yrs, wet_rm, color=style['color'], lw=2.0,
            label=f'{style["label"]} wetland (10-yr mean)')
    ax.plot(yrs, cmb_C, color=style['color'], lw=1.6, ls=':',
            label=f'{style["label"]} wet + IFW − DCC')

# FAIR-ERF
fair_C = fair['CH4_TgCH4'].values * MW_CH4_C
fair_yrs = fair['Year'].values
ax.plot(fair_yrs, fair_C, color=C_FAIR, lw=1.7, ls='-.',
        label='FAIR-ERF v1.3 natural CH4 (Smith+ 2018)')
# Extend FAIR through 2100 (constant since 2005)
last_fair = fair_C[-1]
ax.plot([fair_yrs[-1], 2100], [last_fair, last_fair], color=C_FAIR, lw=1.7, ls='-.')

boundary_line(ax)
ax.set_title('CH4 - Wetland Natural Emissions (Historical + Scenarios)', **TK)
ax.set_ylabel('CH4-C flux (Tg C yr$^{-1}$)', **LK)
ax.set_xlabel('Year', **LK)
sax(ax)
ax.set_ylim(0, 300 * MW_CH4_C)
ax.legend(fontsize=6.6, loc='upper left', framealpha=0.92,
          edgecolor=SC, fancybox=False, ncol=1)

ax2 = ax.twinx()
ax2.set_ylim(np.array(ax.get_ylim()) / MW_CH4_C)
ax2.set_ylabel('CH4 (Tg CH4 yr$^{-1}$)', fontsize=8.5, color='#444444')
ax2.tick_params(labelsize=7.5, colors='#666666')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_color(SC); ax2.spines['right'].set_linewidth(0.8)

# =========================================================================
# PANEL 2: N2O
# =========================================================================
ax = axes[0, 1]

# GNB historical band
gnb_pairs    = [(p[0], p[1]) for p in GNB_PERIODS_N]
gnb_best_N   = [gnb_combined(p)[0] for p in GNB_PERIODS_N]
gnb_lo_N     = [gnb_combined(p)[1] for p in GNB_PERIODS_N]
gnb_hi_N     = [gnb_combined(p)[2] for p in GNB_PERIODS_N]
gnb_best_N2O = [v * MW_N_N2O for v in gnb_best_N]
gnb_lo_N2O   = [v * MW_N_N2O for v in gnb_lo_N]
gnb_hi_N2O   = [v * MW_N_N2O for v in gnb_hi_N]
step_band_arr(ax, gnb_pairs, gnb_lo_N2O, gnb_hi_N2O, C_BUDG, alpha=0.20,
              label='GNB 2024 nat soil + perturbed range [historical]')
step_line_arr(ax, gnb_pairs, gnb_best_N2O, C_BUDG, lw=2.2, ls='--',
              label='GNB 2024 nat soil + perturbed best [historical]')

# Historical: total natural N2O = soil + fire (annual + 10-yr running mean)
n2o_total_h = n2o_h['N2O_soil_TgN2O'].values + n2o_h['N2O_fire_TgN2O'].values
n2o_fire_h  = n2o_h['N2O_fire_TgN2O'].values
ax.plot(years_h, n2o_total_h, color=C_LPJG, lw=1.0, alpha=0.55,
        label='LPJ N2O_soil + N2O_fire (annual, historical)')
ax.plot(years_h, rmean(n2o_total_h), color=C_LPJG_R, lw=2.0,
        label='LPJ N2O_soil + N2O_fire (10-yr mean, historical)')
# Keep a thin auxiliary line for fire alone, for breakdown context
ax.plot(years_h, n2o_fire_h, color=C_FIRE, lw=0.9, ls=':',
        label='LPJ N2O_fire alone (annual, historical)')

# Compute historical endpoints for connectors
hist_n2o_tot_last    = n2o_total_h[-1]
hist_n2o_tot_rm_last = rmean(n2o_total_h)[-1]
hist_n2o_fire_last   = n2o_fire_h[-1]

# Scenarios — drawn natively from 2021, with separate connectors in historical color
for scen in SCENARIOS:
    style = SCEN_STYLES[scen]
    sub = n2o_s[n2o_s.Scenario == scen].sort_values('Year')
    yrs = sub['Year'].values
    soil = sub['N2O_soil_TgN2O'].values
    fire = sub['N2O_fire_TgN2O'].values
    total = soil + fire                            # natural soil + fire
    total_rm = rmean(total)

    # Connectors in historical colors
    connector(ax, hist_n2o_tot_last,    total[0],    C_LPJG,   lw=1.0, alpha=0.55)
    connector(ax, hist_n2o_tot_rm_last, total_rm[0], C_LPJG_R, lw=2.0)
    connector(ax, hist_n2o_fire_last,   fire[0],     C_FIRE,   lw=0.9, ls=':')

    # Scenario lines from 2021 onwards
    ax.plot(yrs, total, color=style['color'], lw=1.0, alpha=0.5)
    ax.plot(yrs, total_rm, color=style['color'], lw=2.0,
            label=f'{style["label"]} N2O_soil + N2O_fire (10-yr mean)')
    ax.plot(yrs, fire, color=style['color'], lw=0.9, ls=':', alpha=0.7)

# FAIR-ERF
fair_N2O = fair['N2O_TgN2O'].values
ax.plot(fair_yrs, fair_N2O, color=C_FAIR, lw=1.7, ls='-.',
        label='FAIR-ERF v1.3 natural N2O')
ax.plot([fair_yrs[-1], 2100], [fair_N2O[-1], fair_N2O[-1]],
        color=C_FAIR, lw=1.7, ls='-.')

boundary_line(ax)
ax.set_title('N2O - Natural Soil + Fire Emissions (Historical + Scenarios)', **TK)
ax.set_ylabel('N2O (Tg N2O yr$^{-1}$)', **LK)
ax.set_xlabel('Year', **LK)
sax(ax)
ax.set_ylim(0, 20)
ax.legend(fontsize=6.6, loc='upper left', framealpha=0.92,
          edgecolor=SC, fancybox=False, ncol=1)

ax2 = ax.twinx()
ax2.set_ylim(np.array(ax.get_ylim()) * MW_N2O_N)
ax2.set_ylabel('N flux (Tg N yr$^{-1}$)', fontsize=8.5, color='#444444')
ax2.tick_params(labelsize=7.5, colors='#666666')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_color(SC); ax2.spines['right'].set_linewidth(0.8)

# =========================================================================
# PANEL 3: CO2 NEE
# =========================================================================
ax = axes[1, 0]

# GCB historical bands
gcb_pairs    = [(p[0], p[1]) for p in GCB_PERIODS]
gcb_best_CO2 = []; gcb_lo_CO2 = []; gcb_hi_CO2 = []
for (y0, y1, lab, s, sigs, e, sige) in GCB_PERIODS:
    n_C, sig_C = gcb_nee(s, sigs, e, sige)
    n_CO2 = n_C * MW_C_CO2; sig_CO2 = sig_C * MW_C_CO2
    gcb_best_CO2.append(n_CO2)
    gcb_lo_CO2.append(n_CO2 - sig_CO2)
    gcb_hi_CO2.append(n_CO2 + sig_CO2)
step_band_arr(ax, gcb_pairs, gcb_lo_CO2, gcb_hi_CO2, C_BUDG, alpha=0.18,
              label='GCB 2025 net land flux ±1$\\sigma$ [historical]')
step_line_arr(ax, gcb_pairs, gcb_best_CO2, C_BUDG, lw=2.2, ls='--',
              label='GCB 2025 net land flux best [historical]')

# Historical NEE
nee_h_C   = co2_h['NEE_PgC'].values
nee_h_CO2 = nee_h_C * MW_C_CO2
ax.plot(years_h, nee_h_CO2, color=C_LPJG, lw=0.8, alpha=0.45,
        label='LPJ-GUESS NEE (annual, historical)')
ax.plot(years_h, rmean(nee_h_CO2), color=C_LPJG_R, lw=2.0,
        label='LPJ-GUESS NEE (10-yr mean, historical)')

# Historical endpoints
hist_nee_CO2_last    = nee_h_CO2[-1]
hist_nee_CO2_rm_last = rmean(nee_h_CO2)[-1]

# Scenarios — drawn natively from 2021, with separate connectors in historical color
for scen in SCENARIOS:
    style = SCEN_STYLES[scen]
    sub = co2_s[co2_s.Scenario == scen].sort_values('Year')
    yrs = sub['Year'].values
    nee_CO2 = sub['NEE_PgC'].values * MW_C_CO2
    nee_rm = rmean(nee_CO2)

    connector(ax, hist_nee_CO2_last,    nee_CO2[0], C_LPJG,   lw=0.8, alpha=0.45)
    connector(ax, hist_nee_CO2_rm_last, nee_rm[0],  C_LPJG_R, lw=2.0)

    ax.plot(yrs, nee_CO2, color=style['color'], lw=0.8, alpha=0.45)
    ax.plot(yrs, nee_rm, color=style['color'], lw=2.0,
            label=f'{style["label"]} NEE (10-yr mean)')

ax.axhline(0, color='#888888', lw=0.8, alpha=0.5)
ax.text(1902, 0.7, 'Source (emission)', fontsize=7.5, color='#888888')
ax.text(1902, -0.7, 'Sink (uptake)',    fontsize=7.5, color='#888888', va='top')

boundary_line(ax)
ax.set_title('CO2 - Net Ecosystem Exchange (Historical + Scenarios)', **TK)
ax.set_ylabel('CO2 flux (Pg CO2 yr$^{-1}$; negative = uptake)', **LK)
ax.set_xlabel('Year', **LK)
sax(ax)
ax.set_ylim(-20, 12)   # ensure 2010 NEE spike (+8.5 Pg CO2) is visible
ax.legend(fontsize=6.6, loc='lower left', framealpha=0.92,
          edgecolor=SC, fancybox=False, ncol=1)

ax2 = ax.twinx()
ax2.set_ylim(np.array(ax.get_ylim()) / MW_C_CO2)
ax2.set_ylabel('CO2-C flux (Pg C yr$^{-1}$; negative = uptake)', fontsize=8.5, color='#444444')
ax2.tick_params(labelsize=7.5, colors='#666666')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_color(SC); ax2.spines['right'].set_linewidth(0.8)

# =========================================================================
# PANEL 4: NEE by scenario (yearly + running mean), Pg C convention
# =========================================================================
# This panel highlights the scenario divergence in NEE specifically, since
# the historical CO2 component breakdown does not naturally extend (each
# scenario has its own component decomposition). We instead show NEE only,
# with all scenarios + historical on a single axis for clear comparison.
ax = axes[1, 1]

# Historical NEE (annual + running mean), Pg C
ax.plot(years_h, nee_h_C, color=C_LPJG, lw=0.7, alpha=0.4)
ax.plot(years_h, rmean(nee_h_C), color=C_LPJG_R, lw=2.0,
        label='Historical (HILDA+v2)')

# Historical endpoints (Pg C)
hist_nee_C_last    = nee_h_C[-1]
hist_nee_C_rm_last = rmean(nee_h_C)[-1]

# Scenarios — drawn natively from 2021, with separate connectors in historical color
for scen in SCENARIOS:
    style = SCEN_STYLES[scen]
    sub = co2_s[co2_s.Scenario == scen].sort_values('Year')
    yrs = sub['Year'].values
    nee_C = sub['NEE_PgC'].values
    nee_rm = rmean(nee_C)

    connector(ax, hist_nee_C_last,    nee_C[0],  C_LPJG,   lw=0.7, alpha=0.4)
    connector(ax, hist_nee_C_rm_last, nee_rm[0], C_LPJG_R, lw=2.0)

    ax.plot(yrs, nee_C, color=style['color'], lw=0.7, alpha=0.4)
    ax.plot(yrs, nee_rm, color=style['color'], lw=2.0,
            label=style['label'])

ax.axhline(0, color='#888888', lw=0.8, alpha=0.5)
boundary_line(ax)
ax.set_title('CO2 - NEE by Scenario (yearly + 10-yr running mean)', **TK)
ax.set_ylabel('NEE (Pg C yr$^{-1}$)', **LK)
ax.set_xlabel('Year', **LK)
sax(ax)
ax.set_ylim(-5.5, 3.5)   # accommodate 2010 spike (+2.32 Pg C)
ax.legend(fontsize=7.6, loc='lower left', framealpha=0.92,
          edgecolor=SC, fancybox=False, ncol=1)

ax2 = ax.twinx()
ax2.set_ylim(np.array(ax.get_ylim()) * MW_C_CO2)
ax2.set_ylabel('NEE (Pg CO2 yr$^{-1}$)', fontsize=8.5, color='#444444')
ax2.tick_params(labelsize=7.5, colors='#666666')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_color(SC); ax2.spines['right'].set_linewidth(0.8)

# Footer
fig.text(
    0.5, 0.003,
    'LPJ-GUESS forced by HILDA+v2 historical (1900-2020) + PLUMv2 scenarios (2021-2100, '
    'harmonized via LUH2 protocol).  Vertical dotted line = historical/scenario boundary.  '
    'A small flux discontinuity at the boundary is expected (each scenario has its own spin-up).\n'
    'GMB IFW (112 Tg/yr) and DCC (-23 Tg/yr) applied uniformly to scenario period.  '
    'Budget references: Saunois et al. 2025 (GMB) | Tian et al. 2024 (GNB) | '
    'Friedlingstein et al. 2025 (GCB) | Smith et al. 2018 (FAIR-ERF v1.3).',
    ha='center', fontsize=6.5, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
              edgecolor='#cccccc', alpha=0.9))

plt.tight_layout(rect=[0, 0.05, 1, 0.998])
out = os.path.join(OUT_DIR, 'lpjg_historical_scenario_comparison.png')
plt.savefig(out, dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f'Saved: {out}', flush=True)
