"""
lpjg_historical_plotting.py
==============================
Plots LPJ-GUESS natural-emission global annual totals (1901-2020) against
the latest published global budget estimates (GMB 2025, GNB 2024, GCB 2025)
and the FAIR-ERF v1.3 natural emissions baseline (Smith et al. 2018).

Forcing of LPJ-GUESS in this run: HILDA+v2 historical land use (1900-2020)
                                  (PLUMv2 SSP-RCP scenarios 2020-2100 are
                                   plotted separately, in a future script.)

INPUT FILES (in DATA_DIR)
-------------------------
  lpjg_co2_annual.csv             — 11 CO2 component fluxes (Pg C/yr)
  lpjg_ch4_annual.csv             — wetland CH4 (Tg CH4/yr)
  lpjg_ch4_combined_annual.csv    — wetland + GMB IFW + DCC (Tg CH4/yr)
  lpjg_n2o_annual.csv             — N gas species (Tg N/yr; Tg N2O/yr for N2O)
  fair_erf_natural_baseline.csv   — FAIR-ERF v1.3 natural baseline (1900-2020)

OUTPUT (in OUT_DIR)
-------------------
  lpjg_historical_comparison.png  — 4-panel comparison plot

PANELS AND AXIS CONVENTIONS
---------------------------
Each gas panel uses dual y-axes; the PRIMARY (left) axis matches the
publication convention of the comparison budget paper, with the SECONDARY
(right) axis showing the alternative unit:

  Panel 1 (top-left)     CH4: PRIMARY = Tg C/yr (CH4-as-carbon)
                              SECONDARY = Tg CH4/yr  (full molecular)
                              Conversion: Tg CH4 × 12/16 = Tg C

  Panel 2 (top-right)    N2O: PRIMARY = Tg N2O/yr   (full molecular)
                              SECONDARY = Tg N/yr   (nitrogen content)
                              Conversion: Tg N × 44/28 = Tg N2O

  Panel 3 (bottom-left)  CO2: PRIMARY = Pg CO2/yr   (full molecular)
                              SECONDARY = Pg C/yr   (carbon convention)
                              Conversion: Pg C × 44/12 = Pg CO2

  Panel 4 (bottom-right) CO2 component breakdown — PRIMARY = Pg C/yr only.
                                                   No smoothing applied.

PANEL CONTENTS
--------------
Panel 1 (CH4):
  - LPJ-GUESS wetland CH4 (annual, thin orange + 10-yr running mean, dark)
  - LPJ-GUESS wetland + GMB IFW − GMB DCC (purple solid + range band)
        = LPJ-GUESS wetland + 112 − 23 = +89 Tg CH4/yr net IFW contribution
  - GMB 2025 wetlands-alone band + best (decadal, 2000+; from Table 3)
  - FAIR-ERF v1.3 natural CH4 (green dash-dot, 1900-2020)

Panel 2 (N2O):
  - LPJ-GUESS N2O_soil (annual, thin orange + 10-yr running mean, dark)
  - LPJ-GUESS N2O_fire (annual, thin red dotted)
  - GNB 2024 natural soil baseline + perturbed-fluxes subtotal (decadal
    step band; bounds widen over time as perturbed uncertainty grows)
  - FAIR-ERF v1.3 natural N2O (green dash-dot, 1900-2020)

Panel 3 (CO2):
  - LPJ-GUESS NEE (annual, thin orange + 10-yr running mean, dark)
  - GCB 2025 net land flux (decadal step band ±1σ; from Table 7)
        NetLand = SLAND − ELUC; sign-flipped to NEE convention
        (negative = land sink). σ via quadrature: √(σ²_SL + σ²_EL).

Panel 4 (CO2 components):
  - 7 yearly area-weighted sums on a single Pg C axis (no smoothing):
    Veg (NPP), Soil (Rh), Harvest, Fire, LU change, Slow pool, NEE (sum).
  - 2010 LU_ch = +2.84 Pg C/yr is visible directly in the LU change line.

10-YEAR RUNNING MEAN
--------------------
  pd.Series(arr).rolling(10, center=True, min_periods=1).mean().values
  → curve extends across the full 1901-2020 window. At edges, the mean
    is computed from 5-9 available years rather than being clipped.

BUDGET PAPER REFERENCES & SPECIFIC TABLE VALUES
-----------------------------------------------
GMB 2025 — Saunois et al. (2025), ESSD 17, 1873-1958.
            doi.org/10.5194/essd-17-1873-2025
  Table 3, "Wetlands BU"          (CH4 panel: blue band & dashed best)
    2000-2009: 159 [119, 203] Tg CH4/yr
    2010-2019: 153 [116, 189] Tg CH4/yr
    2020:      161 [131, 198] Tg CH4/yr
  Table 3, "Inland freshwaters"   (constant 112 [49, 202] Tg CH4/yr)
  Table 3, "Double-counting correction"  (-23 [-9, -36] Tg CH4/yr,
    applied to LPJ-GUESS + IFW combined estimate)

GNB 2024 — Tian et al. (2024), ESSD 16, 2543-2604.
            doi.org/10.5194/essd-16-2543-2024
  Table 3, "Natural soil baseline"  (~6.4 Tg N/yr, ≈constant by GNB design)
  Table 3, "Subtotal" (perturbed fluxes from climate, CO2, LUC):
    1980-1989:  -0.4 [-1.1, 0.7] Tg N/yr
    1990-1999:  -0.5 [-1.4, 0.6]
    2000-2009:  -0.6 [-1.9, 0.8]
    2010-2019:  -0.6 [-2.1, 1.2]
    2020:       -0.6 [-2.2, 1.8]
  Combined (baseline + perturbed) plotted as decadal step band.

GCB 2025 — Friedlingstein et al. (2025), ESSD 17, 965-1039.
            doi.org/10.5194/essd-17-965-2025
  Table 7, "Terrestrial sink (SLAND)" GtC/yr (= Pg C/yr):
    1960s 1.2±0.5  1970s 2.0±0.8  1980s 1.8±0.8
    1990s 2.5±0.6  2000s 2.8±0.7  2014-2023 3.2±0.9
  Table 7, "Land-use change emissions (ELUC)" GtC/yr:
    1960s 1.6±0.7  1970s 1.4±0.7  1980s 1.4±0.7
    1990s 1.6±0.7  2000s 1.4±0.7  2014-2023 1.1±0.7
  Plotted: NEE = -(SLAND - ELUC), σ = √(σ²_SL + σ²_EL), then × 44/12 → Pg CO2.

FAIR-ERF v1.3 — Smith et al. (2018), GMD 11, 2273-2297.
            doi.org/10.5194/gmd-11-2273-2018
  Natural emissions backed out from RCP scenarios assuming steady-state at
  1765 and constant atmospheric lifetimes (CH4 = 9.3 yr, N2O = 121 yr).
  Values from 2005 onward held constant by FAIR construction.
  Source file convention: CH4 in Tg CH4/yr; N2O in Tg N (nitrogen content)
  → multiply by 44/28 to obtain Tg N2O/yr.

FIGURE GEOMETRY
---------------
  figsize=(16, 11) at dpi=300 → 4800×3300 pixel output (aspect 1.45),
  matching the project's standard plot aspect convention.
  bbox_inches='tight' is intentionally NOT used in savefig, to preserve
  the fixed aspect ratio (its expansion behavior on legend overflow
  produces oversized canvases that scale poorly in chat viewports).
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

# =============================================================================
# DATA
# =============================================================================
co2     = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_co2_annual.csv'))
ch4     = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_ch4_annual.csv'))
ch4_cmb = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_ch4_combined_annual.csv'))
n2o     = pd.read_csv(os.path.join(DATA_DIR, 'lpjg_n2o_annual.csv'))
fair    = pd.read_csv(os.path.join(DATA_DIR, 'fair_erf_natural_baseline.csv'))
years   = co2['Year'].values

# =============================================================================
# UNIT CONVERSIONS
# =============================================================================
MW_CH4_C  = 12.0 / 16.0    # CH4 -> CH4-C (mass of carbon per unit mass of CH4)
MW_N2O_N  = 28.0 / 44.0    # N2O -> N (nitrogen content)
MW_N_N2O  = 44.0 / 28.0    # N   -> N2O
MW_C_CO2  = 44.0 / 12.0    # C   -> CO2

# =============================================================================
# BUDGET REFERENCE VALUES (latest published)
# =============================================================================
# -- GMB 2025 wetland-alone CH4 (BU), Tg CH4/yr ---------------------------
GMB_PERIODS = [
    # (yr_start, yr_end, label,  best, lo, hi)
    (2000, 2009, '2000-2009', 159, 119, 203),
    (2010, 2019, '2010-2019', 153, 116, 189),
    (2020, 2020, '2020',      161, 131, 198),
]
GMB_IFW = (112.0, 49.0, 202.0)   # constant Tg CH4/yr (best, lo, hi)

# -- GNB 2024 natural soil + perturbed-fluxes subtotal, Tg N/yr -----------
# Combined best = baseline + perturbed; bounds added (consistent with GNB
# Table 3 reporting min/max range).
GNB_PERIODS_N = [
    # (yr_start, yr_end, label, baseline_best, base_lo, base_hi,
    #                            perturb_best, pert_lo, pert_hi)
    (1980, 1989, '1980-1989', 6.4, 3.9, 8.5, -0.4, -1.1, 0.7),
    (1990, 1999, '1990-1999', 6.4, 3.8, 8.6, -0.5, -1.4, 0.6),
    (2000, 2009, '2000-2009', 6.4, 3.9, 8.5, -0.6, -1.9, 0.8),
    (2010, 2019, '2010-2019', 6.4, 3.9, 8.6, -0.6, -2.1, 1.2),
    (2020, 2020, '2020',      6.4, 3.8, 8.7, -0.6, -2.2, 1.8),
]

def gnb_combined(p):
    """Return (best, lo, hi) of natural-soil+perturbed in Tg N/yr."""
    _, _, _, b, blo, bhi, p_, plo, phi = p
    return (b + p_, blo + plo, bhi + phi)

# -- GCB 2025 Net Land flux (NEE convention), Pg C/yr ---------------------
# NetLand = SLAND - ELUC. We sign-flip so that negative means uptake
# (matching LPJ-GUESS NEE convention). Combined sigma via quadrature.
GCB_PERIODS = [
    # (start, end, label, SLAND, sigSL, ELUC, sigEL)
    (1960, 1969, '1960s',     1.2, 0.5, 1.6, 0.7),
    (1970, 1979, '1970s',     2.0, 0.8, 1.4, 0.7),
    (1980, 1989, '1980s',     1.8, 0.8, 1.4, 0.7),
    (1990, 1999, '1990s',     2.5, 0.6, 1.6, 0.7),
    (2000, 2009, '2000s',     2.8, 0.7, 1.4, 0.7),
    (2014, 2023, '2014-2023', 3.2, 0.9, 1.1, 0.7),
]
def gcb_nee(s, sigs, e, sige):
    """Return (NEE_best, sigma) in Pg C/yr (NEE convention; negative = uptake)."""
    return -(s - e), np.sqrt(sigs**2 + sige**2)

# =============================================================================
# STYLE
# =============================================================================
SC = '#cccccc'
GK = dict(color='#cccccc', lw=0.5, ls='--', alpha=0.7)
TK = dict(fontsize=10, fontweight='bold', color='#1a1a1a', pad=6)
LK = dict(fontsize=8.5, color='#444444')
PK = dict(labelsize=8, colors='#666666')

C_LPJG    = '#e07b39'
C_LPJG_R  = '#a04018'
C_BUDG    = '#2166ac'
C_BUDG_LT = '#9bbcde'
C_FW      = '#7b3294'
C_FAIR    = '#1a9641'
C_FIRE    = '#b35f5f'

def sax(ax, xlim=(1900, 2025)):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(*xlim)
    for sp in ['top']: ax.spines[sp].set_visible(False)
    for sp in ['left','bottom','right']:
        ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

def step_band_arr(ax, x_pairs, lo_arr, hi_arr, color, alpha=0.20, label=None):
    """Draw decadal step band from arrays of (x_pairs, lows, highs)."""
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
    """Centered running mean with min_periods=1 so curve spans the full range."""
    return pd.Series(arr).rolling(w, center=True, min_periods=1).mean().values

# =============================================================================
# FIGURE
# =============================================================================
print("Generating comparison plot ...", flush=True)
fig, axes = plt.subplots(2, 2, figsize=(16, 11))
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')

fig.suptitle(
    'LPJ-GUESS Natural Emission Global Annual Totals vs Latest Global Budget Estimates\n'
    '1901-2020  |  LPJ-GUESS driven by HILDA+v2 historical land use',
    fontsize=11, fontweight='bold', color='#1a1a1a', y=0.998)

# =========================================================================
# PANEL 1: CH4
# =========================================================================
ax = axes[0, 0]

ch4_tgC      = ch4['CH4_TgCH4'].values            * MW_CH4_C
# DCC-corrected combined: LPJ wetland + GMB IFW best + GMB DCC best
ch4_cmb_tgC  = ch4_cmb['CombinedDCC_TgCH4_best'].values * MW_CH4_C
ch4_cmb_lo_C = ch4_cmb['CombinedDCC_TgCH4_lo'].values   * MW_CH4_C
ch4_cmb_hi_C = ch4_cmb['CombinedDCC_TgCH4_hi'].values   * MW_CH4_C

gmb_pairs    = [(p[0], p[1]) for p in GMB_PERIODS]
gmb_best_C   = [p[3] * MW_CH4_C for p in GMB_PERIODS]
gmb_lo_C     = [p[4] * MW_CH4_C for p in GMB_PERIODS]
gmb_hi_C     = [p[5] * MW_CH4_C for p in GMB_PERIODS]

step_band_arr(ax, gmb_pairs, gmb_lo_C, gmb_hi_C, C_BUDG, alpha=0.22,
              label='GMB 2025 wetlands range [BU]')
step_line_arr(ax, gmb_pairs, gmb_best_C, C_BUDG, lw=2.2, ls='--',
              label='GMB 2025 wetlands best [BU]')

ax.plot(years, ch4_tgC, color=C_LPJG, lw=1.4, alpha=0.85,
        label='LPJ-GUESS wetland CH4 (annual)')
ax.plot(years, rmean(ch4_tgC), color=C_LPJG_R, lw=2.2,
        label='LPJ-GUESS wetland CH4 (10-yr running mean)')

ax.fill_between(years, ch4_cmb_lo_C, ch4_cmb_hi_C, color=C_FW, alpha=0.10,
                label='LPJ-GUESS wetland + GMB IFW + DCC range')
ax.plot(years, ch4_cmb_tgC, color=C_FW, lw=2.0, ls='-',
        label='LPJ-GUESS wetland + GMB IFW + DCC best\n(+112 Tg IFW − 23 Tg DCC = +89 Tg net)')

fair_yrs   = fair['Year'].values
fair_ch4_C = fair['CH4_TgCH4'].values * MW_CH4_C
ax.plot(fair_yrs, fair_ch4_C, color=C_FAIR, lw=1.7, ls='-.',
        label='FAIR-ERF v1.3 natural CH4 (Smith+ 2018)')

ax.set_title('CH4 - Wetland Natural Emissions', **TK)
ax.set_ylabel('CH4-C flux (Tg C yr$^{-1}$)', **LK)
ax.set_xlabel('Year', **LK)
sax(ax)
ax.set_ylim(0, 300 * MW_CH4_C)
ax.legend(fontsize=7.0, loc='upper left', framealpha=0.92,
          edgecolor=SC, fancybox=False)

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

n2o_soil_N2O = n2o['N2O_soil_TgN2O'].values
n2o_fire_N2O = n2o['N2O_fire_TgN2O'].values

gnb_pairs    = [(p[0], p[1]) for p in GNB_PERIODS_N]
gnb_best_N   = [gnb_combined(p)[0] for p in GNB_PERIODS_N]
gnb_lo_N     = [gnb_combined(p)[1] for p in GNB_PERIODS_N]
gnb_hi_N     = [gnb_combined(p)[2] for p in GNB_PERIODS_N]
gnb_best_N2O = [v * MW_N_N2O for v in gnb_best_N]
gnb_lo_N2O   = [v * MW_N_N2O for v in gnb_lo_N]
gnb_hi_N2O   = [v * MW_N_N2O for v in gnb_hi_N]

step_band_arr(ax, gnb_pairs, gnb_lo_N2O, gnb_hi_N2O, C_BUDG, alpha=0.20,
              label='GNB 2024 natural soil + perturbed range (decadal)')
step_line_arr(ax, gnb_pairs, gnb_best_N2O, C_BUDG, lw=2.2, ls='--',
              label='GNB 2024 natural soil + perturbed best (decadal)')

ax.plot(years, n2o_soil_N2O, color=C_LPJG, lw=1.4, alpha=0.85,
        label='LPJ-GUESS N2O_soil (annual)')
ax.plot(years, rmean(n2o_soil_N2O), color=C_LPJG_R, lw=2.2,
        label='LPJ-GUESS N2O_soil (10-yr running mean)')

ax.plot(years, n2o_fire_N2O, color=C_FIRE, lw=1.0, ls=':',
        label='LPJ-GUESS N2O_fire (annual)')

ax.plot(fair_yrs, fair['N2O_TgN2O'].values, color=C_FAIR, lw=1.7, ls='-.',
        label='FAIR-ERF v1.3 natural N2O (Smith+ 2018)')

ax.set_title('N2O - Natural Soil + Fire Emissions', **TK)
ax.set_ylabel('N2O (Tg N2O yr$^{-1}$)', **LK)
ax.set_xlabel('Year', **LK)
sax(ax)
ax.set_ylim(0, 20)
ax.legend(fontsize=7.0, loc='upper left', framealpha=0.92,
          edgecolor=SC, fancybox=False)

ax2 = ax.twinx()
ax2.set_ylim(np.array(ax.get_ylim()) * MW_N2O_N)
ax2.set_ylabel('N flux (Tg N yr$^{-1}$)', fontsize=8.5, color='#444444')
ax2.tick_params(labelsize=7.5, colors='#666666')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_color(SC); ax2.spines['right'].set_linewidth(0.8)

# =========================================================================
# PANEL 3: CO2 NEE
#   Primary axis: Pg CO2/yr (full molecular)
#   Secondary axis: Pg C/yr (carbon convention)
# =========================================================================
ax = axes[1, 0]

# Convert LPJ-GUESS NEE (Pg C) to Pg CO2
nee_C   = co2['NEE_PgC'].values
nee_CO2 = nee_C * MW_C_CO2

# Convert GCB decadal benchmarks to Pg CO2 by × 44/12
gcb_pairs    = [(p[0], p[1]) for p in GCB_PERIODS]
gcb_best_CO2 = []; gcb_lo_CO2 = []; gcb_hi_CO2 = []
for (y0, y1, lab, s, sigs, e, sige) in GCB_PERIODS:
    n_C, sig_C = gcb_nee(s, sigs, e, sige)
    n_CO2   = n_C   * MW_C_CO2
    sig_CO2 = sig_C * MW_C_CO2
    gcb_best_CO2.append(n_CO2)
    gcb_lo_CO2.append(n_CO2 - sig_CO2)
    gcb_hi_CO2.append(n_CO2 + sig_CO2)

step_band_arr(ax, gcb_pairs, gcb_lo_CO2, gcb_hi_CO2, C_BUDG, alpha=0.18,
              label='GCB 2025 net land flux ±1$\\sigma$\n(SLAND - ELUC, sign-flipped to NEE convention)')
step_line_arr(ax, gcb_pairs, gcb_best_CO2, C_BUDG, lw=2.2, ls='--',
              label='GCB 2025 net land flux (decadal best)')

ax.plot(years, nee_CO2, color=C_LPJG, lw=1.0, alpha=0.55,
        label='LPJ-GUESS NEE (annual)')
ax.plot(years, rmean(nee_CO2), color=C_LPJG_R, lw=2.2,
        label='LPJ-GUESS NEE (10-yr running mean)')

ax.axhline(0, color='#888888', lw=0.8, alpha=0.5)
ax.text(1902, 0.7, 'Source (emission)', fontsize=7.5, color='#888888')
ax.text(1902, -0.7, 'Sink (uptake)',    fontsize=7.5, color='#888888', va='top')

ax.set_title('CO2 - Net Ecosystem Exchange vs GCB Net Land Flux', **TK)
ax.set_ylabel('CO2 flux (Pg CO2 yr$^{-1}$; negative = uptake)', **LK)
ax.set_xlabel('Year', **LK)
sax(ax)
ax.legend(fontsize=7.0, loc='lower left', framealpha=0.92,
          edgecolor=SC, fancybox=False)

# Right axis: Pg C/yr (× 12/44 from primary)
ax2 = ax.twinx()
ax2.set_ylim(np.array(ax.get_ylim()) / MW_C_CO2)
ax2.set_ylabel('CO2-C flux (Pg C yr$^{-1}$; negative = uptake)', fontsize=8.5, color='#444444')
ax2.tick_params(labelsize=7.5, colors='#666666')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_color(SC); ax2.spines['right'].set_linewidth(0.8)

# =========================================================================
# PANEL 4: CO2 components (yearly area-weighted sums)
# =========================================================================
ax = axes[1, 1]

COMP = [
    ('Veg_PgC',     'Veg (NPP)',   '#2b83ba', 1.4),
    ('Soil_PgC',    'Soil (Rh)',   '#d7191c', 1.4),
    ('Harvest_PgC', 'Harvest',     '#7b2d8b', 1.2),
    ('Fire_PgC',    'Fire',        '#fdae61', 1.1),
    ('LU_ch_PgC',   'LU change',   '#1a9641', 1.1),
    ('Slow_h_PgC',  'Slow pool',   '#999999', 1.0),
    ('NEE_PgC',     'NEE (sum)',   '#000000', 2.2),
]
for col, lbl, c, lw in COMP:
    ax.plot(years, co2[col], color=c, lw=lw, alpha=0.9, label=lbl)

ax.axhline(0, color='#888888', lw=0.8, alpha=0.5)

ax.set_title('CO2 Component Breakdown (yearly area-weighted sums)', **TK)
ax.set_ylabel('CO2-C flux (Pg C yr$^{-1}$)', **LK)
ax.set_xlabel('Year', **LK)
sax(ax)
ax.legend(fontsize=7.0, loc='upper left', framealpha=0.92, edgecolor=SC,
          fancybox=False, ncol=2)

# Footer
fig.text(
    0.5, 0.003,
    'LPJ-GUESS run forced by HILDA+v2 historical land use (1900-2020).  '
    'CH4 input units: g CH4 m$^{-2}$ month$^{-1}$ -> Tg CH4/yr (×12/16 -> Tg C).  '
    'N2O input units: kg N ha$^{-1}$ yr$^{-1}$ -> Tg N/yr (×44/28 -> Tg N2O).  '
    'CO2 input units: kg C m$^{-2}$ yr$^{-1}$ -> Pg C/yr (×44/12 -> Pg CO2).\n'
    'Inland freshwater CH4 = 112 Tg/yr (GMB 2025 BU best; constant).  '
    'Budget references: Saunois et al. 2025 (GMB) | Tian et al. 2024 (GNB) | '
    'Friedlingstein et al. 2025 (GCB) | Smith et al. 2018 (FAIR-ERF v1.3).',
    ha='center', fontsize=6.5, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
              edgecolor='#cccccc', alpha=0.9))

plt.tight_layout(rect=[0, 0.05, 1, 0.998])
out = os.path.join(OUT_DIR, 'lpjg_historical_comparison.png')
plt.savefig(out, dpi=300, facecolor=fig.get_facecolor())
plt.close()
print(f'Saved: {out}', flush=True)
