"""
N2O Managed Soils -- Standalone Plotting Script (Mt units, updated)
Changes vs first version:
  - All values converted to Mt yr-1
  - Regional panel: extended y-axis to 8.5 Mt; with-PRP total reference lines added
  - Component panel: note moved to top-right inside bounds
  - Empirical inter-method uncertainty band in ratio panel
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
    EDGAR_N2O_NEW, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES, RCMIP_CSV as RCMIP_CSV_PATH,
)

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def emp_band(fao, *series):
    """Empirical uncertainty: min/max envelope of all series/FAO ratios."""
    ratios = np.array([np.where(fao>0, s/fao, np.nan) for s in series])
    return np.nanmin(ratios, axis=0), np.nanmax(ratios, axis=0)

EDGAR_N2O = str(EDGAR_N2O_NEW)
RCMIP_CSV = str(RCMIP_CSV_PATH)
OUT_DIR   = (str(OUT_A_DATA) + '/n2o_ms/')
FIG_DIR   = (str(OUT_A_FIGS) + '/')
import os as _os; _os.makedirs(FIG_DIR, exist_ok=True)
YEARS  = list(range(1970, 2021)); YR_STR = [str(y) for y in YEARS]
YC_E   = [f"Y_{y}" for y in YEARS]

def rcmip_splice(variable, df_r):
    hist = df_r[(df_r["Region"]=="World")&(df_r["Scenario"]=="historical")&(df_r["Variable"]==variable)]
    ssp  = df_r[(df_r["Region"]=="World")&(df_r["Scenario"]=="ssp245")&(df_r["Variable"]==variable)]
    h = hist[YR_STR].values[0].astype(float) if len(hist) else np.zeros(51)
    s = ssp [YR_STR].values[0].astype(float) if len(ssp)  else np.zeros(51)
    out = np.zeros(51); i15 = YEARS.index(2015); i20 = YEARS.index(2020)
    for i, y in enumerate(YEARS):
        if y <= 2014:           out[i] = h[i]
        elif y == 2015:         out[i] = s[i15]
        elif 2016 <= y <= 2019: out[i] = s[i15] + (y-2015)/5.*(s[i20]-s[i15])
        else:                   out[i] = s[i20]
    return out

dg = pd.read_csv(OUT_DIR + "n2o_ms_global.csv")
dr = pd.read_csv(OUT_DIR + "n2o_ms_regional.csv")
dc = pd.read_csv(OUT_DIR + "n2o_ms_components.csv")
yr = dg["Year"].values

t_np19    = dg["Total_noPRP_2019_GgN2O"].values  / 1000
t_wp19    = dg["Total_withPRP_2019_GgN2O"].values / 1000
t_wp06    = dg["Total_withPRP_2006_GgN2O"].values / 1000
fao_np    = dg["FAO_noPRP_GgN2O"].values          / 1000
fao_wp    = dg["FAO_total_GgN2O"].values           / 1000
edgar_tot = dg["EDGAR_total_GgN2O"].values         / 1000
fsn_comp  = dc["FSN_dir_GgN2O"].values     / 1000
fon_comp  = dc["FON_2019_dir_GgN2O"].values / 1000
fprp_comp = dc["FPRP_2019_dir_GgN2O"].values / 1000
fcr_comp  = dc["FCR_dir_GgN2O"].values     / 1000
fsom_comp = dc["FSOM_GgN2O"].values        / 1000

R9 = ["North America","Western Europe","Eastern Europe","Oceania",
      "Latin America","Africa","Middle East","Asia","Indian Subcontinent"]
reg_np19 = {}; reg_wp19 = {}
for r in R9:
    sub = dr[dr["Region"]==r].sort_values("Year")
    if len(sub) == 51:
        reg_np19[r] = sub["Total_noPRP_2019_GgN2O"].values  / 1000
        reg_wp19[r] = sub["Total_withPRP_2019_GgN2O"].values / 1000
    else:
        reg_np19[r] = np.zeros(51); reg_wp19[r] = np.zeros(51)

df_r = pd.read_csv(RCMIP_CSV, low_memory=False)
rcmip_n2o = rcmip_splice("Emissions|N2O", df_r) / 1000
df_edgar = pd.ExcelFile(EDGAR_N2O).parse("IPCC 2006", header=9)
etot = df_edgar[YC_E].apply(pd.to_numeric,errors="coerce").fillna(0).sum().values
e34  = df_edgar[df_edgar["ipcc_code_2006_for_standard_report"]=="3.C.4"][YC_E].apply(pd.to_numeric,errors="coerce").fillna(0).sum().values
e35  = df_edgar[df_edgar["ipcc_code_2006_for_standard_report"]=="3.C.5"][YC_E].apply(pd.to_numeric,errors="coerce").fillna(0).sum().values
rcmip_ms = (e34+e35)/np.where(etot>0,etot,1) * rcmip_n2o

C_FAO="#2166ac"; C_NP19="#e07b39"; C_WP19="#d62728"; C_WP06="#f4a560"
C_EDG="#4dac26"; C_RCP="#d6604d"
COMP_COLS=["#3288bd","#66c2a5","#fc8d59","#fee08b","#d53e4f"]
COMP_LBL=["FSN (synthetic fertilizers)","FON (organic N, soil-applied)",
          "FPRP (pasture/range/paddock)","FCR (crop residues)","FSOM (drained organic soils)"]
RC_COLS={"North America":"#1f77b4","Western Europe":"#aec7e8","Eastern Europe":"#ffbb78",
         "Oceania":"#2ca02c","Latin America":"#98df8a","Africa":"#d62728",
         "Middle East":"#ff9896","Asia":"#9467bd","Indian Subcontinent":"#c5b0d5"}
ro=["Indian Subcontinent","Asia","Latin America","Africa","North America","Eastern Europe","Western Europe","Middle East","Oceania"]
SC="#cccccc"; GK=dict(color="#cccccc",linewidth=0.5,linestyle="--",alpha=0.7)
TK=dict(fontsize=11,fontweight="bold",color="#1a1a1a",pad=8)
LK=dict(fontsize=9,color="#444444"); PK=dict(labelsize=8,colors="#666666")
RLS=(0,(3,1,1,1))

def sax(ax, ylim=None):
    ax.tick_params(**PK); ax.grid(**GK); ax.set_xlim(1970,2020)
    if ylim: ax.set_ylim(*ylim)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
    for s in ["left","bottom"]: ax.spines[s].set_color(SC); ax.spines[s].set_linewidth(0.8)

fig, axes = plt.subplots(2,2,figsize=(14,10))
fig.patch.set_facecolor("#fafaf8")
for ax in axes.flat: ax.set_facecolor("#fafaf8")
fig.suptitle("N2O Managed Soils (Agricultural Soils)\n"
             "IPCC 2019 Tier 1 vs FAO GLE vs EDGAR (3.C.4+3.C.5) vs RCMIP CMIP6 | 1970-2020",
             fontsize=12, fontweight="bold", color="#1a1a1a", y=0.99)

# Panel 1: Global totals with and without PRP
ax = axes[0,0]
ax.fill_between(yr, t_np19, t_wp19, alpha=0.15, color=C_WP19)
ax.plot(yr, rcmip_ms, color=C_RCP, linewidth=2.0, linestyle=RLS,
        label="RCMIP CMIP6 (EDGAR 3.C.4+3.C.5 prop.)")
ax.plot(yr, edgar_tot, color=C_EDG, linewidth=1.8, linestyle="-.", label="EDGAR (3.C.4+3.C.5)")
ax.plot(yr, t_wp06, color=C_WP06, linewidth=1.4, linestyle=":", label="2006 params -- with PRP")
ax.plot(yr, t_np19, color=C_NP19, linewidth=2.0, linestyle="--", label="2019 params -- without PRP")
ax.plot(yr, t_wp19, color=C_WP19, linewidth=2.2, label="2019 params -- with PRP")
ax.plot(yr, fao_wp, color=C_FAO, linewidth=2.5, linestyle=":", label="FAO Agricultural Soils")
ax.plot(yr, fao_np, color=C_FAO, linewidth=1.5, linestyle="-.", label="FAO without PRP")
ax.set_title("Global N2O Totals -- With and Without PRP", **TK)
ax.set_ylabel("N2O (Mt yr\u207b\u00b9)", **LK); ax.set_xlabel("Year", **LK)
sax(ax, (1.0, 10.5))
ax.legend(fontsize=7, loc="upper left", framealpha=0.9, edgecolor=SC, fancybox=False)
# Annotation to the right of legend
ax.annotate("Shaded band\n= PRP contribution",
    xy=(2010,(t_np19[40]+t_wp19[40])/2), xytext=(2006,8.2),
    fontsize=7.5, color="#666666", ha="left",
    arrowprops=dict(arrowstyle="->", color="#aaaaaa", lw=0.8))

# Panel 2: Component stacked (direct pathway only)
ax = axes[0,1]
ax.stackplot(yr, [fsn_comp,fon_comp,fprp_comp,fcr_comp,fsom_comp],
    labels=COMP_LBL, colors=COMP_COLS, alpha=0.80)
ax.plot(yr, rcmip_ms, color=C_RCP, linewidth=2.0, linestyle=RLS, label="RCMIP total", zorder=11)
ax.plot(yr, edgar_tot, color=C_EDG, linewidth=1.8, linestyle="-.", label="EDGAR total", zorder=10)
ax.plot(yr, fao_wp, color=C_FAO, linewidth=2.5, linestyle=":", label="FAO total", zorder=12)
ax.set_title("Direct N2O by N-Input Pathway (2019 params)",
             fontsize=10, fontweight="bold", color="#1a1a1a", pad=8)
ax.set_ylabel("N2O (Mt yr\u207b\u00b9)", **LK); ax.set_xlabel("Year", **LK)
sax(ax, (0, 10.5))
ax.legend(fontsize=7, loc="upper left", framealpha=0.9, edgecolor=SC, fancybox=False)
# Note at top-right, anchored right edge, inside plot bounds
ax.text(2019, 10.2,
    "Stacked = EF1 x N-input per pathway (direct only).\n"
    "Indirect (volatilisation + leaching) not decomposed\n"
    "per pathway -- stack falls short of total ref. lines.",
    ha="right", va="top", fontsize=6.5, color="#555555",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#f9f9f4", edgecolor=SC, alpha=0.85))

# Panel 3: Ratio to FAO total with empirical uncertainty band
ax = axes[1,0]
ax.axhline(1.0, color="#888888", linewidth=1.2)
_lo, _hi = emp_band(fao_wp, t_wp19, edgar_tot, rcmip_ms)
ax.fill_between(yr, _lo, _hi, alpha=0.18, color="#888888", label="Inter-method spread")
ax.plot(yr, rcmip_ms/fao_wp,  color=C_RCP,  linewidth=2.0, linestyle=RLS,  label="RCMIP-derived / FAO")
ax.plot(yr, edgar_tot/fao_wp, color=C_EDG,  linewidth=1.8, linestyle="-.", label="EDGAR / FAO")
ax.plot(yr, t_np19/fao_wp,    color=C_NP19, linewidth=1.8, linestyle="--", label="2019 without PRP / FAO")
ax.plot(yr, t_wp19/fao_wp,    color=C_WP19, linewidth=2.2,                 label="2019 with PRP / FAO")
ax.set_title("Ratio to FAO Agricultural Soils Total", **TK)
ax.set_ylabel("Ratio (Series / FAO)", **LK); ax.set_xlabel("Year", **LK)
sax(ax, (0.60, 1.45))
ax.legend(fontsize=8, loc="lower left", framealpha=0.9, edgecolor=SC, fancybox=False)

# Panel 4: Regional stacked (noPRP) + with-PRP total reference lines
ax = axes[1,1]
ax.stackplot(yr, [reg_np19.get(r,np.zeros(51)) for r in ro], labels=ro,
             colors=[RC_COLS[r] for r in ro], alpha=0.80)
ax.plot(yr, t_wp19,   color=C_WP19, linewidth=2.0, linestyle="-",  label="Our total WITH PRP", zorder=13)
ax.plot(yr, fao_wp,   color=C_FAO,  linewidth=2.0, linestyle=":",   label="FAO total WITH PRP", zorder=12)
ax.plot(yr, fao_np,   color=C_FAO,  linewidth=1.5, linestyle="-.",  label="FAO total without PRP", zorder=12)
ax.plot(yr, rcmip_ms, color=C_RCP,  linewidth=2.0, linestyle=RLS,   label="RCMIP total", zorder=11)
ax.plot(yr, edgar_tot, color=C_EDG, linewidth=1.8, linestyle="-.",  label="EDGAR total", zorder=10)
ax.set_title("Regional Breakdown (2019 without PRP) + with-PRP totals", **TK)
ax.set_ylabel("N2O (Mt yr\u207b\u00b9)", **LK); ax.set_xlabel("Year", **LK)
sax(ax, (0, 8.5))
ax.legend(fontsize=7, loc="upper left", framealpha=0.9, edgecolor=SC, fancybox=False)

fig.text(0.5, 0.003,
    f"2020: NoPRP={t_np19[-1]:.3f}Mt | WithPRP={t_wp19[-1]:.3f}Mt | "
    f"FAO(noPRP)={fao_np[-1]:.3f}Mt | FAO(total)={fao_wp[-1]:.3f}Mt | "
    f"EDGAR={edgar_tot[-1]:.3f}Mt | RCMIP-derived={rcmip_ms[-1]:.3f}Mt  |  "
    f"FSOM from FAO published | RCMIP: hist+SSP2-4.5 (2016-2019 interpolated)",
    ha="center", fontsize=7, color="#555555", style="italic",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#f5f5f0", edgecolor="#cccccc", alpha=0.9))

plt.tight_layout(rect=[0,0.04,1,0.97])
plt.savefig(FIG_DIR + 'n2o_ms_trends.png', dpi=300, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.close()
print("Saved: n2o_ms_trends.png")
