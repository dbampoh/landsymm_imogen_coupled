#!/usr/bin/env python3
"""
Ecosystem-state comparison for the LandSyMM-IMOGEN v1.0 GMD paper (Results §3.4,
validation-triad Axis 4): LPJ-GUESS ecosystem outputs driven by the IMOGEN-coupled
feedback climate (Track 2) vs the prescribed ISIMIP-3b climate (Track 1).

Both tracks share the same .ins configuration, land-use, and natural-emission
inputs; the SOLE differential is the climate + CO2 driver. Any Track 2 - Track 1
difference therefore isolates the effect of the IMOGEN coupling (which carries
the emulator's mean-state cool/bright/dry offset documented in §3.3/§4.4) on the
simulated ecosystem state. This is a fit-for-purpose, traceable comparison, not a
validated feedback magnitude.

Tracks share the 0.5-degree land grid (annual, 2021-2100); the inner-merge on
(Lon, Lat, Year) intersects the two gridlists (Track 1 ~62,538 cells; Track 2
PLUM-mask 62,512) automatically. Area statistics use cos(lat)-weighted cell areas.

Generalises the predecessor `carbon_comparison.py` (cpool/cflux only) to the full
ecosystem suite via the VARS registry below (headline + SI tiers).

USAGE
-----
  python ecosystem_comparison.py --scenario SSP1-2.6 [--vars cpool cmass anpp yield]
                                 [--map-start 2080 --map-end 2100] [--output-dir DIR]
  # default --vars = all registry vars; default window 2080-2100; paths auto-resolved.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as _stats

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[4]   # -> lpj-guess_imogen_landsymm
TRACK1_ROOT = Path("/home/bampoh-d/Desktop/landsymm_imogen_stage2A_output")  # prescribed ISIMIP-3b (_wpeat)
TRACK2_ROOT = REPO_ROOT / "forks" / "trunk_r13078_runs"                      # IMOGEN-coupled (cluster)
ANALYSIS_DIR = Path(__file__).resolve().parent

# SSPx-y.z  <->  sspXYZ
SCEN_MAP = {
    "SSP1-2.6": "ssp126", "SSP2-4.5": "ssp245", "SSP3-7.0": "ssp370",
    "SSP4-6.0": "ssp460", "SSP5-8.5": "ssp585",
}

EARTH_RADIUS_M = 6.371e6
DLAT = DLON = 0.5
KG_TO_PG = 1e-12

# --------------------------------------------------------------------------
# Variable registry: per-variable columns to compare, unit, tier, aggregation.
#   agg "none"        -> use the listed columns as-is
#   agg "sum_months"  -> sum the 12 monthly columns into one annual column (mch4)
#   global "density"  -> also report cos-lat area-weighted global TOTAL (col x area)
# --------------------------------------------------------------------------
VARS: Dict[str, dict] = {
    # ---- headline (main text) ----
    "cpool":  {"cols": ["VegC", "LitterC", "SoilC", "Total"],
               "unit": "kg C m$^{-2}$", "gunit": "Pg C", "tier": "headline", "global": "density"},
    "cmass":  {"cols": ["Total", "Natural_sum", "Crop_sum", "Pasture_sum", "Peatland_sum"],
               "unit": "kg C m$^{-2}$", "gunit": "Pg C", "tier": "headline", "global": "density"},
    "anpp":   {"cols": ["Total", "Natural_sum", "Crop_sum", "Pasture_sum", "Peatland_sum"],
               "unit": "kg C m$^{-2}$ yr$^{-1}$", "gunit": "Pg C yr$^{-1}$", "tier": "headline", "global": "density"},
    "cflux":  {"cols": ["NEE", "Veg", "Soil", "Fire", "Harvest"],
               "unit": "kg C m$^{-2}$ yr$^{-1}$", "gunit": "Pg C yr$^{-1}$", "tier": "headline", "global": "density"},
    "yield":  {"cols": ["CerealsC3", "CerealsC4", "Rice", "OilNfix", "OilOther", "Pulses"],
               "unit": "kg C m$^{-2}$ yr$^{-1}$", "gunit": "", "tier": "headline", "global": "none"},
    # ---- supplementary ----
    "npool":  {"cols": ["VegN", "LitterN", "SoilN", "Total"],
               "unit": "kg N m$^{-2}$", "gunit": "Pg N", "tier": "SI", "global": "density"},
    "ngases": {"cols": ["N2O_soil", "N2O_fire", "Total"],
               "unit": "kg N ha$^{-1}$ yr$^{-1}$", "gunit": "", "tier": "SI", "global": "none"},
    "nflux":  {"cols": ["fix", "fert", "leach", "NEE"],
               "unit": "kg N ha$^{-1}$ yr$^{-1}$", "gunit": "", "tier": "SI", "global": "none"},
    "mch4":   {"cols": ["AnnualCH4"], "agg": "sum_months",
               "unit": "g CH$_4$ m$^{-2}$ yr$^{-1}$", "gunit": "Tg CH$_4$ yr$^{-1}$", "tier": "SI", "global": "density"},
    "lai":    {"cols": ["Total"], "unit": "m$^2$ m$^{-2}$", "gunit": "", "tier": "SI", "global": "none"},
    "tot_runoff": {"cols": ["Total", "Surf", "Drain", "Base"],
                   "unit": "mm yr$^{-1}$", "gunit": "", "tier": "SI", "global": "none"},
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def gridcell_area_m2(lat_deg: np.ndarray) -> np.ndarray:
    lat = np.deg2rad(lat_deg)
    dlat, dlon = np.deg2rad(DLAT), np.deg2rad(DLON)
    return (EARTH_RADIUS_M ** 2) * dlon * (np.sin(lat + dlat / 2) - np.sin(lat - dlat / 2))


def resolve_paths(scenario: str) -> Dict[str, Path]:
    ssp = SCEN_MAP[scenario]
    # Both tracks' output dirs are date-stamped (Track 1 varies per scenario, e.g.
    # ssp370 = output-2026-04-27 vs others 2026-03-15; Track 2 = output-2026-06-0X)
    # -> glob rather than hardcode the date.
    t1c = sorted((TRACK1_ROOT / f"{ssp}_wpeat").glob("output-*"))
    if not t1c:
        raise FileNotFoundError(f"No Track 1 output dir under {TRACK1_ROOT}/{ssp}_wpeat")
    t2c = sorted((TRACK2_ROOT / f"{scenario}_cluster_scen").glob("output-2026-06-0*"))
    if not t2c:
        raise FileNotFoundError(f"No Track 2 output dir for {scenario} under {TRACK2_ROOT}")
    return {"track1": t1c[-1], "track2": t2c[-1]}


def load_var(d: Path, var: str) -> pd.DataFrame:
    spec = VARS[var]
    path = d / f"{var}.out.gz"
    with gzip.open(str(path), "rt") as f:
        df = pd.read_csv(f, sep=r"\s+")
    if spec.get("agg") == "sum_months":
        df["AnnualCH4"] = df[MONTHS].sum(axis=1)
    keep = ["Lon", "Lat", "Year"] + spec["cols"]
    return df[keep]


def weighted_stats(name: str, var: str, unit: str, a: np.ndarray, b: np.ndarray, w: np.ndarray) -> dict:
    m = np.isfinite(a) & np.isfinite(b) & np.isfinite(w)
    a, b, w = a[m], b[m], w[m]
    wsum = w.sum()
    wmean_t2 = float((a * w).sum() / wsum)
    wmean_t1 = float((b * w).sum() / wsum)
    d = a - b
    wbias = float((d * w).sum() / wsum)
    wrmse = float(np.sqrt((w * d ** 2).sum() / wsum))
    wmae = float((w * np.abs(d)).sum() / wsum)
    r = float(_stats.pearsonr(a, b)[0]) if len(a) > 2 and a.std() > 0 and b.std() > 0 else np.nan
    return {"variable": name, "output": var, "unit": unit.replace("$", "").replace("^", "").replace("{", "").replace("}", ""),
            "n": int(len(a)), "wmean_track2": wmean_t2, "wmean_track1": wmean_t1,
            "wbias_t2_minus_t1": wbias, "wrmse": wrmse, "wmae": wmae, "pearson_r": r}


def annual_global(merged: pd.DataFrame, cols: List[str], global_mode: str) -> pd.DataFrame:
    """Per-year cos-lat area-weighted global MEAN (native unit) for each col,
    and (if density) the global TOTAL (col x area summed)."""
    rows = []
    w = merged["area_m2"].values
    for yr, g in merged.groupby("Year"):
        wy = g["area_m2"].values
        row = {"Year": int(yr)}
        for c in cols:
            for trk, suf in [("track2", "_t2"), ("track1", "_t1")]:
                v = g[f"{c}{suf}"].values
                ww = wy[np.isfinite(v)]
                vv = v[np.isfinite(v)]
                row[f"{c}_{trk}_wmean"] = float((vv * ww).sum() / ww.sum()) if ww.sum() else np.nan
                if global_mode == "density":
                    row[f"{c}_{trk}_global"] = float((vv * ww).sum())  # native_unit * m^2
        rows.append(row)
    return pd.DataFrame(rows).sort_values("Year").reset_index(drop=True)


def mean_bias_map(merged: pd.DataFrame, cols: List[str]) -> Dict[str, pd.DataFrame]:
    """Time-mean (Track2 - Track1) per grid cell, per column."""
    out = {}
    grp = merged.groupby(["Lon", "Lat"])
    for c in cols:
        bias = (grp[f"{c}_t2"].mean() - grp[f"{c}_t1"].mean()).reset_index(name="bias")
        out[c] = bias
    return out


def plot_bias_maps(maps: Dict[str, pd.DataFrame], var: str, unit: str, path: Path) -> None:
    cols = list(maps.keys())
    n = len(cols)
    fig, axes = plt.subplots(n, 1, figsize=(9, 2.6 * n), squeeze=False)
    for ax, c in zip(axes[:, 0], cols):
        m = maps[c]
        vmax = np.nanpercentile(np.abs(m["bias"].values), 98) or 1.0
        sc = ax.scatter(m["Lon"], m["Lat"], c=m["bias"], cmap="RdBu_r",
                        vmin=-vmax, vmax=vmax, s=1.2, marker="s", linewidths=0)
        ax.set_title(f"{var} {c}: Track 2 (IMOGEN-coupled) - Track 1 (prescribed), time-mean",
                     fontsize=9)
        ax.set_xlim(-180, 180); ax.set_ylim(-60, 85)
        ax.set_xlabel("Lon", fontsize=8); ax.set_ylabel("Lat", fontsize=8)
        ax.tick_params(labelsize=7)
        plt.colorbar(sc, ax=ax, label=f"bias ({unit})", shrink=0.85)
    fig.tight_layout()
    fig.savefig(str(path), dpi=150)
    plt.close(fig)


def plot_global_timeseries(annual: pd.DataFrame, cols: List[str], var: str, unit: str,
                           gunit: str, global_mode: str, path: Path) -> None:
    show = cols[:4]
    n = len(show)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 3.6), squeeze=False)
    for ax, c in zip(axes[0], show):
        ax.plot(annual["Year"], annual[f"{c}_track1_wmean"], color="#1d3557", lw=1.8,
                label="Track 1 (prescribed)")
        ax.plot(annual["Year"], annual[f"{c}_track2_wmean"], color="#e63946", lw=1.8,
                label="Track 2 (IMOGEN-coupled)")
        ax.set_title(f"{var} {c}", fontsize=9)
        ax.set_xlabel("Year", fontsize=8); ax.set_ylabel(f"area-wt mean ({unit})", fontsize=8)
        ax.grid(alpha=0.3); ax.tick_params(labelsize=7)
        ax.legend(fontsize=7)
    fig.suptitle(f"{var}: global area-weighted mean, Track 1 vs Track 2", fontsize=10)
    fig.tight_layout()
    fig.savefig(str(path), dpi=150)
    plt.close(fig)


def compare_one(var: str, paths: Dict[str, Path], out: Path,
                map_start: int, map_end: int) -> List[dict]:
    spec = VARS[var]
    print(f"  [{var}] loading both tracks ...", flush=True)
    t2 = load_var(paths["track2"], var).rename(
        columns={c: f"{c}_t2" for c in spec["cols"]})
    t1 = load_var(paths["track1"], var).rename(
        columns={c: f"{c}_t1" for c in spec["cols"]})
    merged_full = t2.merge(t1, on=["Lon", "Lat", "Year"])
    coords = merged_full[["Lon", "Lat"]].drop_duplicates()
    coords["area_m2"] = gridcell_area_m2(coords["Lat"].values)
    merged_full = merged_full.merge(coords, on=["Lon", "Lat"])
    # annual timeseries over the full overlap
    annual = annual_global(merged_full, spec["cols"], spec.get("global", "none"))
    annual.to_csv(out / f"annual_{var}.csv", index=False)
    # stats + maps over the analysis window
    win = merged_full.query("@map_start <= Year <= @map_end")
    rows = []
    for c in spec["cols"]:
        rows.append(weighted_stats(c, var, spec["unit"],
                                   win[f"{c}_t2"].values, win[f"{c}_t1"].values,
                                   win["area_m2"].values))
    maps = mean_bias_map(win, spec["cols"])
    plot_bias_maps(maps, var, spec["unit"], out / f"fig_biasmap_{var}.png")
    plot_global_timeseries(annual, spec["cols"], var, spec["unit"],
                           spec.get("gunit", ""), spec.get("global", "none"),
                           out / f"fig_timeseries_{var}.png")
    n_cells = merged_full[["Lon", "Lat"]].drop_duplicates().shape[0]
    print(f"  [{var}] {n_cells} cells; window {map_start}-{map_end}; "
          + "; ".join(f"{r['variable']} bias={r['wbias_t2_minus_t1']:+.3f}" for r in rows[:2]))
    del t1, t2, merged_full, win
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scenario", required=True, choices=list(SCEN_MAP))
    p.add_argument("--vars", nargs="*", default=list(VARS), choices=list(VARS))
    p.add_argument("--map-start", type=int, default=2080)
    p.add_argument("--map-end", type=int, default=2100)
    p.add_argument("--output-dir", type=Path, default=None)
    a = p.parse_args()
    out = a.output_dir or (ANALYSIS_DIR / f"outputs_ecosystem_{SCEN_MAP[a.scenario]}_{a.map_start}_{a.map_end}")
    out.mkdir(parents=True, exist_ok=True)
    paths = resolve_paths(a.scenario)
    print(f"Scenario {a.scenario}\n  Track 1: {paths['track1']}\n  Track 2: {paths['track2']}\n"
          f"  window {a.map_start}-{a.map_end}; vars: {', '.join(a.vars)}")
    all_rows = []
    for v in a.vars:
        all_rows.extend(compare_one(v, paths, out, a.map_start, a.map_end))
    summary = pd.DataFrame(all_rows)
    summary.insert(0, "scenario", a.scenario)
    summary.insert(1, "tier", summary["output"].map(lambda v: VARS[v]["tier"]))
    summary.to_csv(out / "summary_statistics.csv", index=False)
    (out / "run_metadata.json").write_text(json.dumps({
        "scenario": a.scenario, "track1": str(paths["track1"]), "track2": str(paths["track2"]),
        "window": [a.map_start, a.map_end], "vars": a.vars,
    }, indent=2))
    print(f"\nWrote {out}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
