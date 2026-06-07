#!/usr/bin/env python3
"""
make_fig5_taylor_multivar.py -- composite 4-panel Taylor diagram for Fig 5.

Reads climate_comparison's taylor_inputs.csv and draws one Taylor diagram per
variable (temperature `tas`, precipitation `pr`, shortwave `rsds`, diurnal
temperature range `dtr`) in a 2x2 figure. Each panel shows the 5 SSP scenarios
at 3 evaluation windows (colour = SSP, marker = window), versus the ISIMIP-3b
MRI-ESM2-0 reference (REF star at radius 1, correlation 1).

Taylor geometry: radius = spatial std ratio (sigma_IMOGEN / sigma_ISIMIP),
angle = arccos(spatial pattern correlation). The reference is the point (1, 0).

Usage:
  python make_fig5_taylor_multivar.py [--taylor-csv PATH] [--out PATH]
"""
from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ANALYSIS_DIR = Path(__file__).resolve().parent
PANELS = [("tas", "Temperature"), ("pr", "Precipitation"),
          ("rsds", "Shortwave radiation"), ("dtr", "Diurnal temperature range")]
SSP_COLORS = {
    "SSP1-2.6": "#1d3557", "SSP2-4.5": "#2a9d8f", "SSP3-7.0": "#e9c46a",
    "SSP4-6.0": "#f4a261", "SSP5-8.5": "#e63946",
}
WINDOW_MARKERS = {"2000_2020": ("o", "2015-2020"),
                  "2040_2060": ("^", "2040-2060"),
                  "2080_2100": ("s", "2080-2100")}
CORR_TICKS = [0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]


def _draw_taylor_axes(ax, rmax):
    """Draw the quarter-circle Taylor frame: std arcs + correlation rays."""
    th = np.linspace(0, np.pi / 2, 200)
    # std-ratio arcs
    for r in np.arange(0.5, rmax + 0.01, 0.5):
        ax.plot(r * np.cos(th), r * np.sin(th), color="0.7", lw=0.6, zorder=1)
    # reference std=1 arc (dashed)
    ax.plot(np.cos(th), np.sin(th), color="0.4", lw=0.9, ls="--", zorder=1)
    # correlation rays
    for c in CORR_TICKS:
        ang = np.arccos(c)
        ax.plot([0, rmax * np.cos(ang)], [0, rmax * np.sin(ang)],
                color="0.85", lw=0.5, zorder=1)
        ax.text((rmax + 0.04) * np.cos(ang), (rmax + 0.04) * np.sin(ang),
                f"{c:g}", fontsize=6, color="0.4",
                ha="center", va="center", rotation=0)
    ax.text((rmax + 0.16) * np.cos(np.pi / 4), (rmax + 0.16) * np.sin(np.pi / 4),
            "correlation", fontsize=7, color="0.4", ha="center", va="center",
            rotation=-45)
    # reference point (std_ratio=1, r=1)
    ax.plot(1.0, 0.0, marker="*", ms=13, color="k", zorder=5)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--taylor-csv", type=Path,
                   default=ANALYSIS_DIR / "_corrected_climate_out" / "taylor_inputs.csv")
    p.add_argument("--out", type=Path,
                   default=ANALYSIS_DIR / "_corrected_climate_out" / "fig5_taylor_multivar.png")
    args = p.parse_args(argv)

    df = pd.read_csv(args.taylor_csv)
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 10.5))
    for ax, (var, title) in zip(axes.ravel(), PANELS):
        sub = df[df["variable"] == var]
        rmax = max(1.25, float(np.nanmax(sub["std_ratio"])) * 1.08)
        _draw_taylor_axes(ax, rmax)
        for _, row in sub.iterrows():
            r = row["std_ratio"]; ang = np.arccos(np.clip(row["spatial_pattern_r"], -1, 1))
            mk = WINDOW_MARKERS.get(row["window"], ("o", row["window"]))[0]
            ax.plot(r * np.cos(ang), r * np.sin(ang), marker=mk, ms=7,
                    color=SSP_COLORS.get(row["scenario"], "0.5"),
                    mec="k", mew=0.4, ls="none", zorder=4)
        ax.set_xlim(0, rmax + 0.22); ax.set_ylim(0, rmax + 0.22)
        ax.set_aspect("equal")
        ax.set_xlabel("normalised standard deviation ($\\sigma_{\\mathrm{IMOGEN}}/\\sigma_{\\mathrm{ISIMIP}}$)",
                      fontsize=8)
        ax.set_title(f"({'abcd'[PANELS.index((var, title))]}) {title}", fontsize=11, loc="left")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(labelsize=7)

    # shared legend
    ssp_handles = [Line2D([0], [0], marker="o", ls="none", color=c, mec="k", mew=0.4, label=s)
                   for s, c in SSP_COLORS.items()]
    win_handles = [Line2D([0], [0], marker=m, ls="none", color="0.4", mec="k", mew=0.4, label=lab)
                   for (m, lab) in WINDOW_MARKERS.values()]
    ref_handle = [Line2D([0], [0], marker="*", ls="none", color="k", ms=12,
                         label="ISIMIP-3b reference")]
    fig.legend(handles=ssp_handles + win_handles + ref_handle, loc="lower center",
               ncol=5, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Taylor diagrams: IMOGEN-coupled vs ISIMIP-3b MRI-ESM2-0 (spatial pattern fidelity)",
                 fontsize=12, y=0.98)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160, bbox_inches="tight")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
