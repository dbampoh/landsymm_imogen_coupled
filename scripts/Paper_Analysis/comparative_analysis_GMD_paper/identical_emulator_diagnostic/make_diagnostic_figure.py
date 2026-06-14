#!/usr/bin/env python3
"""Render the identical-emulator diagnostic figure (emission-pathway feedback on
global-land-mean temperature) from diagnostic_partition.csv."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
CSV = HERE / "diagnostic_partition.csv"
OUT = Path("/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm/paper/_media/supplement/figS_diagnostic_feedback.png")

WINDOWS = ["2015-2020", "2040-2060", "2080-2100"]
SCEN_COLOR = {"SSP1-2.6": "#1d3557", "SSP5-8.5": "#e63946"}

rows = list(csv.DictReader(open(CSV)))
def get(scen, comp):
    return [next(float(r[comp]) for r in rows if r["scenario"] == scen and r["variable"] == "T" and r["window"] == win) for win in WINDOWS]

fig, ax = plt.subplots(figsize=(7.2, 4.6))
x = range(len(WINDOWS))
ax.axhspan(-0.5, 0.5, color="0.85", zorder=0, label="$\\pm$0.5 K band")
ax.axhline(0, color="0.4", lw=0.8)
for scen in ["SSP1-2.6", "SSP5-8.5"]:
    c = SCEN_COLOR[scen]
    ax.plot(x, get(scen, "feedback_opt1"), "-o", color=c, lw=1.8, label=f"{scen}: full feedback (vs RCMIP+FaIR)")
    ax.plot(x, get(scen, "subst_opt2"), "--s", color=c, lw=1.4, mfc="white",
            label=f"{scen}: CH$_4$/N$_2$O substitution only")
ax.set_xticks(list(x)); ax.set_xticklabels(WINDOWS)
ax.set_ylabel("Emission-pathway feedback on global-land-mean\ntemperature, IMOGEN integrated minus RCMIP control (K)")
ax.set_xlabel("Analysis window")
ax.set_ylim(-1.0, 1.0)
ax.grid(alpha=0.3)
ax.text(0.02, 0.97, "Total coupled minus ISIMIP-3b difference: +1.3 to +4.6 K (Table 12)\nso the emission-pathway feedback is a small fraction of the total",
        transform=ax.transAxes, va="top", ha="left", fontsize=8, color="0.25")
ax.legend(fontsize=7.5, loc="lower left", ncol=1, framealpha=0.9)
ax.set_title("Identical-emulator diagnostic: emission-pathway feedback on temperature", fontsize=10)
fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(str(OUT), dpi=150, bbox_inches="tight")
print(f"wrote {OUT}")
