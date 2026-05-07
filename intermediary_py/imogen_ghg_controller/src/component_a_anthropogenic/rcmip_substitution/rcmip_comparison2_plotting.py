"""
rcmip_comparison2_plotting.py
===============================
Comparison 2: Full GHG emission totals — RCMIP published trajectories vs
post-substitution trajectories (agricultural sectors replaced with our
IPCC Tier 1 / PLUMv2 estimates), 1900–2100.

This plot answers: what is the net impact on the full GHG emission trajectory
(all sectors including fossil fuels, industry, land-use, etc.) of using our
independent bottom-up agricultural sector estimates instead of RCMIP's
IAM-based agriculture component?

PANELS
------
  Panel 1 (top-left):    CH4 full total — before and after substitution
  Panel 2 (top-right):   N2O full total — before and after substitution
  Panel 3 (bottom-left): CH4 absolute change from substitution (New − RCMIP)
  Panel 4 (bottom-right):N2O absolute change from substitution (New − RCMIP)

ALGEBRA (per year, per scenario)
---------------------------------
  New_total = RCMIP_total − RCMIP_agri + Our_agri
  Δ         = New_total − RCMIP_total
            = Our_agri − RCMIP_agri

  For 1900-1969: Δ = 0 by construction (Our_agri = RCMIP_agri).
  For 1970-2019: Δ = Our Tier 1 − RCMIP agri historical (single line).
  For 2020-2100: Δ = Our PLUMv2 − RCMIP agri per SSP (5 lines diverge).
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
SC  = '#cccccc'
GK  = dict(color='#cccccc', lw=0.5, ls='--', alpha=0.7)
TK  = dict(fontsize=10, fontweight='bold', color='#1a1a1a', pad=6)
LK  = dict(fontsize=8.5, color='#444444')
PK  = dict(labelsize=8, colors='#666666')
C_HIST_OUR = '#e07b39'

def style_ax(ax, xlim=(1900,2100), ylim=None):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    ax.axvspan(1900, 1970, alpha=0.05, color='#888888', lw=0)
    ax.axvline(1970, color='#888888', lw=0.9, ls=':', alpha=0.7)
    ax.axvline(2020, color='#888888', lw=1.1, ls=':', alpha=0.9)
    for sp in ['top','right']: ax.spines[sp].set_visible(False)
    for sp in ['left','bottom']:
        ax.spines[sp].set_color(SC); ax.spines[sp].set_linewidth(0.8)

# =============================================================================
# PLOT
# =============================================================================
print("Generating Comparison 2 plot ...")
fig, axes = plt.subplots(2, 2, figsize=(16, 11))
fig.patch.set_facecolor('#fafaf8')
for ax in axes.flat: ax.set_facecolor('#fafaf8')
fig.suptitle(
    'Comparison 2: Full GHG Emission Totals — RCMIP Published (before) vs '
    'Post-Substitution (after)\n'
    '1900\u20132100  |  New total = RCMIP total \u2212 RCMIP agri + Our IPCC Tier 1 / PLUMv2 agri',
    fontsize=10, fontweight='bold', color='#1a1a1a', y=0.995)

# Reference arrays: SSP2-4.5 historical segment (1970-2019) for single difference line
df_s2_ch4 = df_ch4[df_ch4['Scenario']=='SSP2-4.5'].sort_values('Year').set_index('Year')
df_s2_n2o = df_n2o[df_n2o['Scenario']=='SSP2-4.5'].sort_values('Year').set_index('Year')

# ── Panel 1: CH4 full totals ──────────────────────────────────────────────────
ax = axes[0,0]

for s in SCENARIOS:
    sub  = df_ch4[df_ch4['Scenario']==s].sort_values('Year')
    yrs  = sub['Year'].values

    # RCMIP total (before) — dashed
    ax.plot(yrs, sub['RCMIP_total'].values,
            color=COLORS[s], lw=1.6, ls='--', alpha=0.70, zorder=9)
    # New total (after) — solid, same colour
    ax.plot(yrs, sub['New_total'].values,
            color=COLORS[s], lw=2.0, ls='-', zorder=11)

# Fill between before and after for SSP2 to show the shift magnitude
sub_s2 = df_ch4[df_ch4['Scenario']=='SSP2-4.5'].sort_values('Year')
ax.fill_between(sub_s2['Year'].values,
                sub_s2['RCMIP_total'].values,
                sub_s2['New_total'].values,
                alpha=0.08, color=COLORS['SSP2-4.5'],
                label='_')

ax.set_title('CH4 \u2014 Full Global Total\n'
             '(all sectors: fossil fuels + AFOLU + industry + waste)', **TK)
ax.set_ylabel('CH4 (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax)

handles = [
    Line2D([0],[0], color='#888888', lw=1.6, ls='--',
           label='RCMIP published total (before substitution)'),
    Line2D([0],[0], color='#888888', lw=2.0, ls='-',
           label='Post-substitution total (after)'),
    mpatches.Patch(facecolor='#aaaaaa', alpha=0.15,
                   label='Shift band (SSP2-4.5 shown)'),
] + [Line2D([0],[0], color=COLORS[s], lw=2, label=s) for s in SCENARIOS]
ax.legend(handles=handles, fontsize=7, loc='upper right',
          framealpha=0.92, edgecolor=SC, fancybox=False)

# ── Panel 2: N2O full totals ──────────────────────────────────────────────────
ax = axes[0,1]

for s in SCENARIOS:
    sub  = df_n2o[df_n2o['Scenario']==s].sort_values('Year')
    yrs  = sub['Year'].values
    ax.plot(yrs, sub['RCMIP_total'].values,
            color=COLORS[s], lw=1.6, ls='--', alpha=0.70, zorder=9)
    ax.plot(yrs, sub['New_total'].values,
            color=COLORS[s], lw=2.0, ls='-', zorder=11)

sub_s2 = df_n2o[df_n2o['Scenario']=='SSP2-4.5'].sort_values('Year')
ax.fill_between(sub_s2['Year'].values,
                sub_s2['RCMIP_total'].values,
                sub_s2['New_total'].values,
                alpha=0.08, color=COLORS['SSP2-4.5'])

ax.set_title('N2O \u2014 Full Global Total\n'
             '(all sectors: fossil fuels + AFOLU + industry)', **TK)
ax.set_ylabel('N2O (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax)
n2o_handles = [
    Line2D([0],[0], color='#888888', lw=1.6, ls='--',
           label='RCMIP published total (before)'),
    Line2D([0],[0], color='#888888', lw=2.0, ls='-',
           label='Post-substitution total (after)'),
] + [Line2D([0],[0], color=COLORS[s], lw=2, label=s) for s in SCENARIOS]
ax.legend(handles=n2o_handles, fontsize=7, loc='upper left',
          framealpha=0.92, edgecolor=SC, fancybox=False)

# ── Panel 3: CH4 absolute change (New_total − RCMIP_total = Our − RCMIP_agri) ─
ax = axes[1,0]

# Historical period: single orange line (same for all SSPs)
hist_years = list(range(1970, 2020))
hist_delta  = [df_s2_ch4.loc[y,'New_total'] - df_s2_ch4.loc[y,'RCMIP_total']
               for y in hist_years]
ax.plot(hist_years, hist_delta, color=C_HIST_OUR, lw=2.2, ls='-',
        zorder=12, label='Historical (Tier 1 − RCMIP agri)')
ax.fill_between(hist_years, 0, hist_delta,
                alpha=0.12, color=C_HIST_OUR)

# Scenario period: 5 SSP lines
for s in SCENARIOS:
    sub = df_ch4[(df_ch4['Scenario']==s) &
                 (df_ch4['Period']=='scenario')].sort_values('Year')
    delta = sub['New_total'].values - sub['RCMIP_total'].values
    ax.plot(sub['Year'].values, delta,
            color=COLORS[s], lw=1.8, label=s, zorder=10)
    ax.fill_between(sub['Year'].values, 0, delta,
                    alpha=0.06, color=COLORS[s])

ax.axhline(0, color='#666666', lw=1.0, alpha=0.6)
ax.text(1905, 8, 'Post-substitution HIGHER than RCMIP', fontsize=7.5,
        color='#444444', va='bottom')
ax.text(1905, -3, 'Post-substitution LOWER than RCMIP', fontsize=7.5,
        color='#444444', va='top')
ax.set_title('CH4 Absolute Change from Substitution\n'
             '(New total \u2212 RCMIP total = Our agri \u2212 RCMIP agri)', **TK)
ax.set_ylabel('\u0394 CH4 (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax)
ax.legend(fontsize=7.5, loc='upper left',
          framealpha=0.92, edgecolor=SC, fancybox=False)

# ── Panel 4: N2O absolute change ──────────────────────────────────────────────
ax = axes[1,1]

hist_delta_n2o = [df_s2_n2o.loc[y,'New_total'] - df_s2_n2o.loc[y,'RCMIP_total']
                  for y in hist_years]
ax.plot(hist_years, hist_delta_n2o, color=C_HIST_OUR, lw=2.2, ls='-',
        zorder=12, label='Historical (Tier 1 − RCMIP agri)')
ax.fill_between(hist_years, 0, hist_delta_n2o,
                alpha=0.12, color=C_HIST_OUR)

for s in SCENARIOS:
    sub = df_n2o[(df_n2o['Scenario']==s) &
                 (df_n2o['Period']=='scenario')].sort_values('Year')
    delta = sub['New_total'].values - sub['RCMIP_total'].values
    ax.plot(sub['Year'].values, delta,
            color=COLORS[s], lw=1.8, label=s, zorder=10)
    ax.fill_between(sub['Year'].values, 0, delta,
                    alpha=0.06, color=COLORS[s])

ax.axhline(0, color='#666666', lw=1.0, alpha=0.6)
ax.set_title('N2O Absolute Change from Substitution\n'
             '(New total \u2212 RCMIP total = Our agri \u2212 RCMIP agri)', **TK)
ax.set_ylabel('\u0394 N2O (Mt yr\u207b\u00b9)', **LK)
ax.set_xlabel('Year', **LK)
style_ax(ax)
ax.legend(fontsize=7.5, loc='upper left',
          framealpha=0.92, edgecolor=SC, fancybox=False)

# ── Key findings annotation ───────────────────────────────────────────────────
# Add percentage change annotation for 2100
for gas, df_g, ax_idx in [('CH4', df_ch4, (1,0)), ('N2O', df_n2o, (1,1))]:
    ax = axes[ax_idx]
    for s in SCENARIOS:
        sub = df_g[(df_g['Scenario']==s) & (df_g['Year']==2100)]
        if len(sub):
            pct = ((sub['New_total'].values[0] - sub['RCMIP_total'].values[0])
                   / sub['RCMIP_total'].values[0] * 100)
            ax.annotate(f'{pct:+.0f}%',
                        xy=(2100, sub['New_total'].values[0] - sub['RCMIP_total'].values[0]),
                        fontsize=6.5, color=COLORS[s], ha='left',
                        fontweight='bold')

# ── Footer ────────────────────────────────────────────────────────────────────
fig.text(
    0.5, 0.003,
    'New total = RCMIP total \u2212 RCMIP_agri + Our_agri  where  '
    'RCMIP_agri = Emissions|CH4|MAGICC AFOLU|Agriculture  (CH4) or  '
    'Emissions|N2O|MAGICC AFOLU  (N2O).  '
    'Our_agri: IPCC Tier 1 2019 Refinement historical (1970\u20132020) + PLUMv2 s1 scenario (2020\u20132100).  '
    'CH4 sectors: EF + MM + Rice (Option B).  '
    'N2O sectors: MM + Synthetic Fertilizers + Managed Soils.  '
    'Pre-1970: Δ=0 (no independent estimate).  '
    'Discontinuity at 2020 reflects FAO→PLUM activity data change.',
    ha='center', fontsize=6.2, color='#555555', style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#f5f5f0',
              edgecolor='#cccccc', alpha=0.9))

plt.tight_layout(rect=[0, 0.04, 1, 0.99])
outpath = os.path.join(HERE, 'rcmip_comparison2_full_totals.png')
plt.savefig(outpath, dpi=300, bbox_inches='tight',
            facecolor=fig.get_facecolor())
plt.close()
print(f"Saved: {outpath}")
