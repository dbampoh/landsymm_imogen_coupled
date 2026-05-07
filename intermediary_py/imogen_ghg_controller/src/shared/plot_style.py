"""
plot_style.py — shared plot style helpers
==========================================

Contains everything that was previously copy-pasted at the top of every
plotting script: scenario colour palette, axis-styling helpers, smoothing
functions, and step-band/step-line helpers.

All Component B and Component C plotting scripts now import from here.
"""

import numpy as np
import pandas as pd


# =============================================================================
# Scenario colour palette (IPCC AR6 standard)
# =============================================================================
SCEN_COLORS = {
    'SSP1-2.6': '#1a9850',   # green   — Sustainability
    'SSP2-4.5': '#2c7bb6',   # blue    — Middle-of-the-road
    'SSP3-7.0': '#d7191c',   # red     — Regional rivalry
    'SSP4-6.0': '#fdae61',   # orange  — Inequality
    'SSP5-8.5': '#762a83',   # purple  — Fossil-fuelled development
}

# Black for the historical period (drawn once, identical across scenarios pre-2015)
HIST_COLOR = '#1a1a1a'

# Comparator references (atmospheric inversions, budget partitions)
CMP_COLOR = '#08519c'


# =============================================================================
# Style dictionaries (passed to matplotlib via **)
# =============================================================================
SC = '#cccccc'                                                # spine colour
GK = dict(color='#cccccc', lw=0.5, ls='--', alpha=0.7)        # grid kwargs
TK = dict(fontsize=11, fontweight='bold',                     # title kwargs
          color='#1a1a1a', pad=6)
LK = dict(fontsize=9, color='#444444')                        # label kwargs
PK = dict(labelsize=8.5, colors='#666666')                    # tick (params) kwargs


# =============================================================================
# Axis-styling helper
# =============================================================================
def sax(ax, xlim=(1900, 2105)):
    """Apply consistent styling: tick params, grid, x-limit, hide top spine,
    soften remaining spines.

    Used at the end of every panel-drawing function.
    """
    ax.tick_params(**PK)
    ax.grid(**GK)
    ax.set_xlim(*xlim)
    ax.spines['top'].set_visible(False)
    for sp in ['left', 'bottom', 'right']:
        ax.spines[sp].set_color(SC)
        ax.spines[sp].set_linewidth(0.8)


# =============================================================================
# Smoothing helpers
# =============================================================================
def rmean(arr, w=10):
    """Centered rolling mean with window w. min_periods=1 ensures endpoints
    are still covered."""
    return pd.Series(arr).rolling(w, center=True, min_periods=1).mean().values


def rmean_segmented(years, vals, hist_end=2014):
    """Compute rolling mean separately on the historical (years <= hist_end)
    and scenario (years > hist_end) segments, then concatenate.

    Avoids stitching the running mean across the historical-scenario boundary
    where the underlying spin-up state may differ. hist_end defaults to 2014
    (the year before RCMIP scenarios begin diverging).
    """
    yrs = np.asarray(years)
    vs = np.asarray(vals)
    out = np.full_like(vs, np.nan, dtype=float)
    mask_h = yrs <= hist_end
    mask_s = yrs > hist_end
    if mask_h.any():
        out[mask_h] = rmean(vs[mask_h])
    if mask_s.any():
        out[mask_s] = rmean(vs[mask_s])
    return out


def split_by_period(years, vals, hist_end=2014):
    """Split a (years, values) series at hist_end into historical and scenario
    portions. hist_end is included in BOTH segments so plotted lines visually
    connect at the boundary.

    Returns: (h_yrs, h_vals, s_yrs, s_vals)
    """
    years = np.asarray(years)
    vals = np.asarray(vals)
    mh = years <= hist_end
    ms = years >= hist_end
    return years[mh], vals[mh], years[ms], vals[ms]


# =============================================================================
# Step-band and step-line helpers (for budget references over decades)
# =============================================================================
def step_band_horizontal(ax, x_pairs, lo_arr, hi_arr,
                         color=CMP_COLOR, alpha=0.16, label=None):
    """Draw filled rectangles spanning each (year_start, year_end) period at the
    given (lo, hi) values. Used for plotting GMB / GNB / GCB period ranges."""
    first = True
    for (x0, x1), lo, hi in zip(x_pairs, lo_arr, hi_arr):
        ax.fill_between(
            [x0 - 0.5, x1 + 0.5],
            [lo, lo], [hi, hi],
            color=color, alpha=alpha,
            label=label if first else None,
            edgecolor='none',
        )
        first = False


def step_line_horizontal(ax, x_pairs, vals, color=CMP_COLOR,
                         lw=2.0, ls='--', label=None):
    """Draw horizontal segments at the best-estimate value for each
    (year_start, year_end) period."""
    first = True
    for (x0, x1), v in zip(x_pairs, vals):
        ax.plot(
            [x0 - 0.5, x1 + 0.5], [v, v],
            color=color, lw=lw, ls=ls,
            label=label if first else None,
            solid_capstyle='butt',
        )
        first = False
