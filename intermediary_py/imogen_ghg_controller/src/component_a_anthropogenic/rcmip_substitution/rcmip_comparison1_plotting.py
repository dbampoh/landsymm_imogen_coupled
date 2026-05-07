"""
rcmip_comparison1_plotting.py
===============================
Comparison 1: Agricultural sector emissions — RCMIP baseline vs our
IPCC Tier 1 / PLUMv2 modelled estimates, 1900–2100.

This plot answers: how much does our independent bottom-up estimate of
agricultural GHG emissions differ from what RCMIP's IAM-based scenarios
attribute to the agricultural sector — both historically and into the future?

PANELS
------
  Panel 1 (top-left):    CH4 agricultural sector comparison
  Panel 2 (top-right):   N2O agricultural sector comparison
  Panel 3 (bottom-left): CH4 absolute difference (Our_agri − RCMIP_agri)
  Panel 4 (bottom-right):N2O absolute difference (Our_agri − RCMIP_agri)

LINES SHOWN
-----------
  RCMIP baseline (before):
    1900–2014: single grey dashed line (historical — same for all SSPs)
    2015–2100: five scenario-coloured dashed lines (one per SSP)

  Our estimate (after):
    1900–1969: none shown separately (equals RCMIP by construction)
    1970–2020: single orange-grey solid line (historical Tier 1,
               summed across modelled sectors)
    2020–2100: five scenario-coloured solid lines (PLUMv2 s1)

  Vertical reference lines at 1970 (inventory start) and 2020 (splice).
  Grey shaded band 1900–1969 indicating pre-inventory period.
"""

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np
import os

# =============================================================================
# PATHS AND CONSTANTS
# =============================================================================
HERE = os.path.dirname(os.path.abspath(__file__))

df_ch4 = pd.read_csv(os.path.join(HERE,'rcmip_substitution_ch4.csv'))
df_n2o = pd.read_csv(os.path.join(HERE,'rcmip_substitution_n2o.csv'))

SCENARIOS = ['SSP1-2.6','SSP2-4.5','SSP3-7.0','SSP4-6.0','SSP5-8.5']
COLORS = {
    'SSP1-2.6':'#1a9641','SSP2-4.5':'#2b83ba','SSP3-7.0':'#d7191c',
    'SSP4-6.0':'#fdae61','SSP5-8.5':'#7b2d8b',
}
C_HIST_OUR  = '#e07b39'   # our historical Tier 1 — orange
C_RCMIP_PRE = '#666666'   # RCMIP pre-2015 — grey
SC   = '#cccccc'
GK   = dict(color='#cccccc', lw=0.5, ls='--', alpha=0.7)
TK   = dict(fontsize=10, fontweight='bold', color='#1a1a1a', pad=6)
LK   = dict(fontsize=8.5, color='#444444')
PK   = dict(labelsize=8, colors='#666666')

def style_ax(ax, xlim=(1900,2100), ylim=None):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    # Shade pre-inventory period
    ax.axvspan(1900, 1970, alpha=0.05, color='#888888', lw=0)
    ax.axvline(1970, color='#888888', lw=0.9, ls=':', alpha=0.7)
    ax.axvline(2020, color='#888888', lw=1.1, ls=':', alpha=0.9)
    for sp in ['top','right']: ax.spines[sp].set_visible(False)
    for sp in ['left','bottom']:
        ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

# =============================================================================
# EXTRACT DATA ARRAYS
# =============================================================================
def get_arrays(df, scenario):
    sub = df[df['Scenario']==scenario].sort_values('Year')
    return sub['Year'].values, sub

# For the RCMIP historical pre-2015 period, all SSPs share the same values
df_s2_ch4 = df_ch4[df_ch4['Scenario']=='SSP2-4.5'].sort_values('Year')
df_s2_n2o = df_n2o[df_n2o['Scenario']=='SSP2-4.5'].sort_values('Year')

# Historical Tier 1 (1970-2019, same for all SSPs)
hist_mask_ch4 = (df_s2_ch4['Period']=='historical')
hist_mask_n2o = (df_s2_n2o['Period']=='historical')
hist_yrs_ch4  = df_s2_ch4[hist_mask_ch4]['Year'].values
hist_our_ch4  = df_s2_ch4[hist_mask_ch4]['Our_agri'].values
hist_yrs_n2o  = df_s2_n2o[hist_mask_n2o]['Year'].values
hist_our_n2o  = df_s2_n2o[hist_mask_n2o]['Our_agri'].values

# RCMIP historical agriculture (1900-2014, identical for all SSPs in this period)
pre_mask = df_s2_ch4['Year'] <= 2014
rcmip_pre_yrs = df_s2_ch4[pre_mask]['Year'].values
rcmip_pre_ch4 = df_s2_ch4[pre_mask]['RCMIP_agri'].values
rcmip_pre_n2o = df_s2_n2o[pre_mask]['RCMIP_agri'].values

# =============================================================================
# PLOT
# =============================================================================
print("Generating Comparison 1 plot ...")
fig, axes = plt.subplots(2, 2, figsize=(16, 11))
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')
fig.suptitle(
    'Comparison 1: Agricultural Sector GHG Emissions — RCMIP Baseline vs Our IPCC Tier 1 / PLUMv2 Estimates\n'
    '1900\u20132100  |  Five SSP-RCP scenarios  |  '
    'CH4: EF + MM + Rice  |  N2O: MM + Synthetic Fertilizers + Managed Soils',
    fontsize=10, fontweight='bold', color='#1a1a1a', y=0.995)

# ── Shared legend elements ────────────────────────────────────────────────────
legend_handles = [
    mpatches.Patch(facecolor='#cccccc', alpha=0.3,
                   label='Pre-inventory period (1900\u20131969)\nno independent estimate available'),
    Line2D([0],[0], color=C_RCMIP_PRE, lw=1.8, ls='--',
           label='RCMIP baseline (MAGICC AFOLU|Agriculture)\nhistorical 1900\u20132014, then SSP 2015\u20132100 [dashed]'),
    Line2D([0],[0], color=C_HIST_OUR, lw=2.2, ls='-',
           label='Our IPCC Tier 1 historical (1970\u20132020)\n[orange solid]'),
    Line2D([0],[0], color='#333333', lw=1.2, ls=':',
           label='Vertical lines: 1970 (inventory start) | 2020 (hist\u2192scenario splice)'),
]
for s in SCENARIOS:
    legend_handles.append(
        Line2D([0],[0], color=COLORS[s], lw=2,
               label=f'{s}  RCMIP=dashed  Our PLUMv2=solid')
    )

# ── Panel 1: CH4 agricultural sectors ────────────────────────────────────────
ax = axes[0,0]

# RCMIP historical (grey dashed, 1900-2014)
ax.plot(rcmip_pre_yrs, rcmip_pre_ch4,
        color=C_RCMIP_PRE, lw=1.8, ls='--', zorder=8, alpha=0.9)

# Our historical Tier 1 (orange solid, 1970-2020)
ax.plot(hist_yrs_ch4, hist_our_ch4,
        color=C_HIST_OUR, lw=2.5, ls='-', zorder=12)

# Scenario period (2020-2100): RCMIP dashed + Our solid, per SSP
for s in SCENARIOS:
    sub = df_ch4[(df_ch4['Scenario']==s) &
                 (df_ch4['Period']=='scenario')].sort_values('Year')
    yrs = sub['Year'].values
    ax.plot(yrs, sub['RCMIP_agri'].values,
            color=COLORS[s], lw=1.6, ls='--', alpha=0.75, zorder=9)
    ax.plot(yrs, sub['Our_agri'].values,
            color=COLORS[s], lw=2.0, ls='-', zorder=11)

# Annotate 2020 discontinuity
v_hist = hist_our_ch4[-1]
v_scen = df_ch4[(df_ch4['Scenario']=='SSP2-4.5')&(df_ch4['Year']==2020)]['Our_agri'].values[0]
ax.annotate(f'Discontinuity at 2020\nhist={v_hist:.0f} → scenario={v_scen:.0f} Mt\n'
            f'(FAO→PLUM activity data)',
            xy=(2020, v_scen), xytext=(2035, v_scen*0.75),
            fontsize=6.5, color='#555555',
            arrowprops=dict(arrowstyle='->', color='#888888', lw=0.8))

ax.set_title('CH4 \u2014 Agricultural Sectors\n'
             '(Enteric Fermentation + Manure Management + Rice)', **TK)
ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax)
ax.legend(handles=legend_handles, fontsize=6.5, loc='upper left',
          framealpha=0.92, edgecolor=SC, fancybox=False, ncol=1)

# ── Panel 2: N2O agricultural sectors ────────────────────────────────────────
ax = axes[0,1]

ax.plot(rcmip_pre_yrs, rcmip_pre_n2o,
        color=C_RCMIP_PRE, lw=1.8, ls='--', zorder=8, alpha=0.9)
ax.plot(hist_yrs_n2o, hist_our_n2o,
        color=C_HIST_OUR, lw=2.5, ls='-', zorder=12)

for s in SCENARIOS:
    sub = df_n2o[(df_n2o['Scenario']==s) &
                 (df_n2o['Period']=='scenario')].sort_values('Year')
    yrs = sub['Year'].values
    ax.plot(yrs, sub['RCMIP_agri'].values,
            color=COLORS[s], lw=1.6, ls='--', alpha=0.75, zorder=9)
    ax.plot(yrs, sub['Our_agri'].values,
            color=COLORS[s], lw=2.0, ls='-', zorder=11)

ax.set_title('N2O \u2014 Agricultural Sectors\n'
             '(Manure Management + Synthetic Fertilizers + Managed Soils)', **TK)
ax.set_ylabel('N2O (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax)
# Concise legend for N2O panel
n2o_handles = [
    Line2D([0],[0], color=C_RCMIP_PRE, lw=1.8, ls='--',
           label='RCMIP AFOLU baseline (dashed)'),
    Line2D([0],[0], color=C_HIST_OUR,  lw=2.2, ls='-',
           label='Our Tier 1 historical (solid orange)'),
] + [Line2D([0],[0], color=COLORS[s], lw=2,
            label=f'{s}  RCMIP=dashed / Ours=solid') for s in SCENARIOS]
ax.legend(handles=n2o_handles, fontsize=7, loc='upper left',
          framealpha=0.92, edgecolor=SC, fancybox=False)

# ── Panel 3: CH4 difference (Our_agri − RCMIP_agri) ─────────────────────────
ax = axes[1,0]

# Historical difference (1970-2020, single line)
hist_diff_ch4 = hist_our_ch4 - df_s2_ch4[hist_mask_ch4]['RCMIP_agri'].values
ax.plot(hist_yrs_ch4, hist_diff_ch4,
        color=C_HIST_OUR, lw=2.2, ls='-', zorder=12,
        label='Historical Tier 1 − RCMIP')

# Scenario difference per SSP (2020-2100)
for s in SCENARIOS:
    sub = df_ch4[(df_ch4['Scenario']==s) &
                 (df_ch4['Period']=='scenario')].sort_values('Year')
    diff = sub['Our_agri'].values - sub['RCMIP_agri'].values
    ax.plot(sub['Year'].values, diff,
            color=COLORS[s], lw=1.8, label=s, zorder=10)
    ax.fill_between(sub['Year'].values, 0, diff,
                    alpha=0.06, color=COLORS[s])

ax.axhline(0, color='#888888', lw=1.0, ls='-', alpha=0.5)
ax.text(1905, 2, 'Our estimate ABOVE RCMIP', fontsize=7.5,
        color='#444444', va='bottom')
ax.text(1905, -2, 'Our estimate BELOW RCMIP', fontsize=7.5,
        color='#444444', va='top')
ax.set_title('CH4 Difference: Our Estimate \u2212 RCMIP Baseline', **TK)
ax.set_ylabel('\u0394 CH4 (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax)
ax.legend(fontsize=7.5, loc='upper left',
          framealpha=0.92, edgecolor=SC, fancybox=False)

# ── Panel 4: N2O difference (Our_agri − RCMIP_agri) ─────────────────────────
ax = axes[1,1]

hist_diff_n2o = hist_our_n2o - df_s2_n2o[hist_mask_n2o]['RCMIP_agri'].values
ax.plot(hist_yrs_n2o, hist_diff_n2o,
        color=C_HIST_OUR, lw=2.2, ls='-', zorder=12,
        label='Historical Tier 1 − RCMIP')

for s in SCENARIOS:
    sub = df_n2o[(df_n2o['Scenario']==s) &
                 (df_n2o['Period']=='scenario')].sort_values('Year')
    diff = sub['Our_agri'].values - sub['RCMIP_agri'].values
    ax.plot(sub['Year'].values, diff,
            color=COLORS[s], lw=1.8, label=s, zorder=10)
    ax.fill_between(sub['Year'].values, 0, diff,
                    alpha=0.06, color=COLORS[s])

ax.axhline(0, color='#888888', lw=1.0, ls='-', alpha=0.5)
ax.set_title('N2O Difference: Our Estimate \u2212 RCMIP Baseline', **TK)
ax.set_ylabel('\u0394 N2O (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax)
ax.legend(fontsize=7.5, loc='upper left',
          framealpha=0.92, edgecolor=SC, fancybox=False)

# ── Footer ────────────────────────────────────────────────────────────────────
fig.text(
    0.5, 0.003,
    'RCMIP baseline: Emissions|CH4|MAGICC AFOLU|Agriculture  and  '
    'Emissions|N2O|MAGICC AFOLU  from RCMIP v5.1 (Nicholls et al. 2020).  '
    'Our CH4: IPCC 2019 Refinement Tier 1 (historical) / PLUMv2 s1 IPCC Tier 1 (scenario).  '
    'Our N2O: 2006-split MM + 2019clim Synfert + 2019 withPRP MS (historical) / PLUMv2 s1 (scenario).  '
    'SSP4-6.0 mapped to RCMIP ssp460.  '
    'Pre-1970 shaded region: no independent estimate; Our_agri = RCMIP_agri.',
    ha='center', fontsize=6.2, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
              edgecolor='#cccccc', alpha=0.9))

plt.tight_layout(rect=[0, 0.04, 1, 0.99])
outpath = os.path.join(HERE, 'rcmip_comparison1_agri_sectors.png')
plt.savefig(outpath, dpi=300, bbox_inches='tight',
            facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {outpath}")
