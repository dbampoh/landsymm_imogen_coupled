#!/usr/bin/env python3
"""
_replot_supp_taylor.py  (session 18 supplement fix)
===================================================
Regenerate the SUPPLEMENT Taylor diagrams (Figs S1 pr/rsds, S2 tasmin/tasmax/
dtr) from the already-computed corrected taylor_inputs.csv, with the window
legend RELABELLED from the internal nominal label "2000_2020" to the actual
sampled window "2015-2020" (ISIMIP-3b scenario coverage begins 2015), matching
the supplement text and Table S1. Pure re-plot: no climate is reprocessed.

The plotting logic mirrors climate_comparison._plot_taylor (same normalised
Taylor geometry, scenario colours, window markers, high-correlation zoom inset)
but keyed on the relabelled window strings.
"""
from pathlib import Path
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from climate_comparison import COMPARISONS, SCENARIOS

HERE = Path(__file__).resolve().parent
OUT = HERE / os.environ.get("SUPP_TAYLOR_OUTDIR", "_corrected_climate_out")
WIN_MAP = {"2000_2020": "2015-2020", "2040_2060": "2040-2060", "2080_2100": "2080-2100"}
WINDOW_MARKERS = {"2015-2020": "o", "2040-2060": "s", "2080-2100": "^"}


def plot_taylor(df: pd.DataFrame, variables, out_dir: Path):
    scen_list = list(SCENARIOS.keys())
    cmap = plt.get_cmap("tab10")
    scen_colors = {s: cmap(i % 10) for i, s in enumerate(scen_list)}
    paths = []
    for key in variables:
        sub = df[df["variable"] == key]
        if sub.empty:
            continue
        tier = COMPARISONS[key]["tier"]
        fig = plt.figure(figsize=(7.8, 7))
        ax = fig.add_subplot(111, projection="polar")
        ax.set_thetalim(0, np.pi / 2)
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(1)
        ratios = sub["std_ratio"].values
        rmax = max(1.6, float(np.nanmax(ratios)) * 1.1) if np.isfinite(np.nanmax(ratios)) else 1.6
        corr_ticks = np.array([0.0, 0.3, 0.6, 0.8, 0.9, 0.95, 0.99])
        ax.set_thetagrids(np.degrees(np.arccos(corr_ticks)), labels=[f"{c:g}" for c in corr_ticks])
        ax.set_rlim(0, rmax)
        ax.plot(0, 1.0, "k*", markersize=14, label="ISIMIP3b (ref)")
        for _, r in sub.iterrows():
            corr, ratio = r["spatial_pattern_r"], r["std_ratio"]
            if not (np.isfinite(corr) and np.isfinite(ratio)):
                continue
            theta = np.arccos(np.clip(corr, -1, 1))
            ax.plot(theta, ratio, marker=WINDOW_MARKERS.get(r["window"], "o"),
                    color=scen_colors.get(r["scenario"], "gray"), markersize=8, linestyle="none")
        ax.set_title(
            f"Taylor diagram (normalized): {COMPARISONS[key]['label']}\n"
            f"radius = std$_{{IMOGEN}}$/std$_{{ISIMIP}}$, angle = spatial pattern correlation", fontsize=10)
        scen_handles = [plt.Line2D([], [], color=scen_colors[s], marker="o", linestyle="none", label=s) for s in scen_list]
        win_handles = [plt.Line2D([], [], color="k", marker=WINDOW_MARKERS[w], linestyle="none", label=w) for w in WINDOW_MARKERS]
        leg1 = ax.legend(handles=scen_handles, loc="upper right", bbox_to_anchor=(1.34, 1.0), fontsize=8, title="Scenario")
        ax.add_artist(leg1)
        ax.legend(handles=win_handles, loc="lower right", bbox_to_anchor=(1.34, 0.0), fontsize=8, title="Window")

        zoom_corr_min, zoom_ratio_lo, zoom_ratio_hi = 0.95, 0.95, 1.10
        in_zoom = [
            (np.arccos(np.clip(rr["spatial_pattern_r"], -1, 1)), rr["std_ratio"], rr)
            for _, rr in sub.iterrows()
            if np.isfinite(rr["spatial_pattern_r"]) and np.isfinite(rr["std_ratio"])
            and rr["spatial_pattern_r"] >= zoom_corr_min and zoom_ratio_lo <= rr["std_ratio"] <= zoom_ratio_hi
        ]
        if in_zoom:
            axins = fig.add_axes([0.74, 0.34, 0.27, 0.31], projection="polar")
            axins.set_thetalim(0, np.arccos(zoom_corr_min))
            axins.set_theta_zero_location("E")
            axins.set_theta_direction(1)
            axins.set_rorigin(0)
            axins.set_rlim(zoom_ratio_lo, zoom_ratio_hi)
            ztk = np.array([0.95, 0.97, 0.98, 0.99, 1.0])
            axins.set_thetagrids(np.degrees(np.arccos(ztk)), labels=[f"{c:g}" for c in ztk], fontsize=7)
            axins.set_rgrids([0.95, 1.0, 1.1], fontsize=4)
            axins.set_rlabel_position(8)
            axins.tick_params(pad=1)
            axins.plot(0, 1.0, "k*", markersize=11)
            for theta, ratio, rr in in_zoom:
                axins.plot(theta, ratio, marker=WINDOW_MARKERS.get(rr["window"], "o"),
                           color=scen_colors.get(rr["scenario"], "gray"), markersize=7, linestyle="none")
            axins.set_title("zoom: corr 0.95-1.0", fontsize=8, pad=6)

        p = out_dir / f"fig_taylor_{tier}_{key}.png"
        fig.tight_layout()
        fig.savefig(p, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(p)
        print(f"  wrote {p.name}")
    return paths


def main():
    df = pd.read_csv(OUT / "taylor_inputs.csv")
    df["window"] = df["window"].map(lambda w: WIN_MAP.get(w, w))
    plot_taylor(df, ["pr", "rsds", "tasmin", "tasmax", "dtr"], OUT)


if __name__ == "__main__":
    main()
