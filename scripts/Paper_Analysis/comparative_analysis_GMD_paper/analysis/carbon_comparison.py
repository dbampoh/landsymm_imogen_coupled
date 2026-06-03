#!/usr/bin/env python3
"""
Compare LPJ-GUESS carbon pool and flux outputs driven by IMOGEN vs ISIMIP3b
climate for SSP245.

Both datasets share the same 0.5° land grid (~62k points) and annual
time step (2021–2100), so no regridding is needed — just load, merge
on (Lon, Lat, Year), and diff.

All area-dependent statistics (spatial means, global totals) use
cos(lat)-weighted grid-cell areas on a regular 0.5° grid.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

_IS_WIN = sys.platform.startswith("win")

DEFAULT_ISIMIP_CPOOL = Path(
    r"E:\climate_comp_landsymm_imogen\ssp245\cpool.out.gz"
    if _IS_WIN
    else "/mnt/e/climate_comp_landsymm_imogen/ssp245/cpool.out.gz"
)
DEFAULT_ISIMIP_CFLUX = Path(
    r"E:\climate_comp_landsymm_imogen\ssp245\cflux.out.gz"
    if _IS_WIN
    else "/mnt/e/climate_comp_landsymm_imogen/ssp245/cflux.out.gz"
)
DEFAULT_IMOGEN_CPOOL = Path(
    r"E:\climate_comp_landsymm_imogen\REGRIDDED-SSP245\cpool.out.gz"
    if _IS_WIN
    else "/mnt/e/climate_comp_landsymm_imogen/REGRIDDED-SSP245/cpool.out.gz"
)
DEFAULT_IMOGEN_CFLUX = Path(
    r"E:\climate_comp_landsymm_imogen\REGRIDDED-SSP245\cflux.out.gz"
    if _IS_WIN
    else "/mnt/e/climate_comp_landsymm_imogen/REGRIDDED-SSP245/cflux.out.gz"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "outputs_carbon_ssp245"

EARTH_RADIUS_M = 6.371e6
DLAT = 0.5  # degrees
DLON = 0.5

CPOOL_VARS = ["VegC", "LitterC", "SoilC", "Total"]
CFLUX_VARS = ["NEE", "Veg", "Soil", "Fire", "Harvest"]

CPOOL_UNIT = "kg C m$^{-2}$"
CFLUX_UNIT = "kg C m$^{-2}$ yr$^{-1}$"
GLOBAL_POOL_UNIT = "Pg C"
GLOBAL_FLUX_UNIT = "Pg C yr$^{-1}$"

KG_TO_PG = 1e-12


def gridcell_area_m2(lat_deg: np.ndarray) -> np.ndarray:
    """Area of a DLAT x DLON grid cell at given latitude(s), in m²."""
    lat_rad = np.deg2rad(lat_deg)
    dlat_rad = np.deg2rad(DLAT)
    dlon_rad = np.deg2rad(DLON)
    return (EARTH_RADIUS_M ** 2) * dlon_rad * (
        np.sin(lat_rad + dlat_rad / 2) - np.sin(lat_rad - dlat_rad / 2)
    )


def load_gz(path: Path) -> pd.DataFrame:
    print(f"  loading {path.name} ...", flush=True)
    with gzip.open(str(path), "rt") as f:
        df = pd.read_csv(f, delim_whitespace=True)
    return df


def run(
    isimip_cpool_path: Path,
    isimip_cflux_path: Path,
    imogen_cpool_path: Path,
    imogen_cflux_path: Path,
    output_dir: Path,
    year_start: int,
    year_end: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    isimip_cpool = load_gz(isimip_cpool_path)
    imogen_cpool = load_gz(imogen_cpool_path)
    isimip_cflux = load_gz(isimip_cflux_path)
    imogen_cflux = load_gz(imogen_cflux_path)

    # Filter to requested year range
    for df in [isimip_cpool, imogen_cpool, isimip_cflux, imogen_cflux]:
        df.query("@year_start <= Year <= @year_end", inplace=True)

    # Build area weights from the grid
    coords = isimip_cpool[["Lon", "Lat"]].drop_duplicates().reset_index(drop=True)
    coords["area_m2"] = gridcell_area_m2(coords["Lat"].values)
    n_points = len(coords)
    total_area_m2 = coords["area_m2"].sum()
    years = sorted(isimip_cpool["Year"].unique())
    n_years = len(years)

    print(f"  {n_points} grid points, {n_years} years ({years[0]}–{years[-1]})")
    print(f"  total land area: {total_area_m2 / 1e12:.2f} x 10^12 m²", flush=True)

    meta = {
        "n_land_points": int(n_points),
        "year_range": [int(years[0]), int(years[-1])],
        "total_land_area_m2": float(total_area_m2),
        "isimip_cpool": str(isimip_cpool_path),
        "imogen_cpool": str(imogen_cpool_path),
        "isimip_cflux": str(isimip_cflux_path),
        "imogen_cflux": str(imogen_cflux_path),
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(meta, indent=2))

    # Merge IMOGEN and ISIMIP on (Lon, Lat, Year) for each output type
    merge_keys = ["Lon", "Lat", "Year"]

    pool_merged = imogen_cpool[merge_keys + CPOOL_VARS].merge(
        isimip_cpool[merge_keys + CPOOL_VARS],
        on=merge_keys,
        suffixes=("_imogen", "_isimip"),
    )
    pool_merged = pool_merged.merge(coords[["Lon", "Lat", "area_m2"]], on=["Lon", "Lat"])

    flux_merged = imogen_cflux[merge_keys + CFLUX_VARS].merge(
        isimip_cflux[merge_keys + CFLUX_VARS],
        on=merge_keys,
        suffixes=("_imogen", "_isimip"),
    )
    flux_merged = flux_merged.merge(coords[["Lon", "Lat", "area_m2"]], on=["Lon", "Lat"])

    # ---------- Summary statistics (area-weighted) ----------
    summary_rows = []
    for vname in CPOOL_VARS:
        a = pool_merged[f"{vname}_imogen"].values
        b = pool_merged[f"{vname}_isimip"].values
        w = pool_merged["area_m2"].values
        summary_rows.append(_weighted_stats(vname, "cpool", CPOOL_UNIT, a, b, w))
    for vname in CFLUX_VARS:
        a = flux_merged[f"{vname}_imogen"].values
        b = flux_merged[f"{vname}_isimip"].values
        w = flux_merged["area_m2"].values
        summary_rows.append(_weighted_stats(vname, "cflux", CFLUX_UNIT, a, b, w))

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(output_dir / "summary_statistics.csv", index=False)

    # ---------- Annual global totals (Pg C) ----------
    pool_annual = _annual_global(pool_merged, CPOOL_VARS)
    pool_annual.to_csv(output_dir / "annual_global_pools.csv", index=False)

    flux_annual = _annual_global(flux_merged, CFLUX_VARS)
    flux_annual.to_csv(output_dir / "annual_global_fluxes.csv", index=False)

    # ---------- Mean bias maps (time-averaged per grid cell) ----------
    pool_bias_maps = _mean_bias_per_point(pool_merged, CPOOL_VARS)
    flux_bias_maps = _mean_bias_per_point(flux_merged, CFLUX_VARS)

    # ---------- Figures ----------
    _plot_timeseries_pools(pool_annual, output_dir / "fig01_global_cpool_timeseries.png")
    _plot_timeseries_fluxes(flux_annual, output_dir / "fig02_global_cflux_timeseries.png")
    _plot_bias_maps(pool_bias_maps, CPOOL_VARS, CPOOL_UNIT, "Carbon Pool", output_dir / "fig03_cpool_bias_maps.png")
    _plot_bias_maps(flux_bias_maps, CFLUX_VARS, CFLUX_UNIT, "Carbon Flux", output_dir / "fig04_cflux_bias_maps.png")
    _plot_scatter(pool_merged, CPOOL_VARS, CPOOL_UNIT, "Carbon Pool", years[-1], output_dir / "fig05_cpool_scatter.png")
    _plot_scatter(flux_merged, CFLUX_VARS, CFLUX_UNIT, "Carbon Flux", years[-1], output_dir / "fig06_cflux_scatter.png")
    _plot_diff_timeseries_pools(pool_annual, output_dir / "fig07_global_cpool_diff_timeseries.png")
    _plot_diff_timeseries_fluxes(flux_annual, output_dir / "fig08_global_cflux_diff_timeseries.png")

    print(f"Wrote outputs to: {output_dir}")
    print(summary_df.to_string(index=False))


def _weighted_stats(vname, otype, unit, a, b, w):
    d = a - b
    wsum = w.sum()
    wmean_a = np.average(a, weights=w)
    wmean_b = np.average(b, weights=w)
    wbias = np.average(d, weights=w)
    wrmse = np.sqrt(np.average(d ** 2, weights=w))
    wmae = np.average(np.abs(d), weights=w)
    r = np.corrcoef(a, b)[0, 1] if len(a) > 1 else float("nan")
    return {
        "variable": vname,
        "type": otype,
        "unit": unit.replace("$", ""),
        "n_samples": len(a),
        "wmean_imogen": wmean_a,
        "wmean_isimip": wmean_b,
        "wbias_imogen_minus_isimip": wbias,
        "wrmse": wrmse,
        "wmae": wmae,
        "pearson_r": r,
    }


def _annual_global(merged: pd.DataFrame, varnames: list) -> pd.DataFrame:
    """Compute annual area-weighted global totals in Pg C (pools) or Pg C/yr (fluxes)."""
    rows = []
    for year, grp in merged.groupby("Year"):
        row = {"Year": int(year)}
        for v in varnames:
            a = grp[f"{v}_imogen"].values
            b = grp[f"{v}_isimip"].values
            w = grp["area_m2"].values
            row[f"{v}_imogen_PgC"] = (a * w).sum() * KG_TO_PG
            row[f"{v}_isimip_PgC"] = (b * w).sum() * KG_TO_PG
        rows.append(row)
    return pd.DataFrame(rows)


def _mean_bias_per_point(merged: pd.DataFrame, varnames: list) -> pd.DataFrame:
    """Time-averaged (IMOGEN − ISIMIP) per grid point."""
    diff_cols = {}
    for v in varnames:
        merged[f"_diff_{v}"] = merged[f"{v}_imogen"] - merged[f"{v}_isimip"]
        diff_cols[v] = f"_diff_{v}"
    agg = {dc: "mean" for dc in diff_cols.values()}
    agg["area_m2"] = "first"
    bias = merged.groupby(["Lon", "Lat"]).agg(agg).reset_index()
    bias.rename(columns={f"_diff_{v}": f"bias_{v}" for v in varnames}, inplace=True)
    return bias


# ====================== Plotting functions ======================

def _plot_timeseries_pools(annual: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(len(CPOOL_VARS), 1, figsize=(11, 3 * len(CPOOL_VARS)), sharex=True)
    if len(CPOOL_VARS) == 1:
        axes = [axes]
    for ax, v in zip(axes, CPOOL_VARS):
        ax.plot(annual["Year"], annual[f"{v}_imogen_PgC"], label="IMOGEN", linewidth=1.2)
        ax.plot(annual["Year"], annual[f"{v}_isimip_PgC"], label="ISIMIP3b", linewidth=1.2)
        ax.set_ylabel(f"{v}\n({GLOBAL_POOL_UNIT})")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Year")
    fig.suptitle("Global carbon pools (area-weighted totals)", fontsize=12)
    fig.tight_layout()
    fig.savefig(str(path), dpi=160)
    plt.close(fig)


def _plot_timeseries_fluxes(annual: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(len(CFLUX_VARS), 1, figsize=(11, 3 * len(CFLUX_VARS)), sharex=True)
    if len(CFLUX_VARS) == 1:
        axes = [axes]
    for ax, v in zip(axes, CFLUX_VARS):
        ax.plot(annual["Year"], annual[f"{v}_imogen_PgC"], label="IMOGEN", linewidth=1.2)
        ax.plot(annual["Year"], annual[f"{v}_isimip_PgC"], label="ISIMIP3b", linewidth=1.2)
        ax.set_ylabel(f"{v}\n({GLOBAL_FLUX_UNIT})")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Year")
    fig.suptitle("Global carbon fluxes (area-weighted totals)", fontsize=12)
    fig.tight_layout()
    fig.savefig(str(path), dpi=160)
    plt.close(fig)


def _plot_diff_timeseries_pools(annual: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(len(CPOOL_VARS), 1, figsize=(11, 3 * len(CPOOL_VARS)), sharex=True)
    if len(CPOOL_VARS) == 1:
        axes = [axes]
    for ax, v in zip(axes, CPOOL_VARS):
        diff = annual[f"{v}_imogen_PgC"] - annual[f"{v}_isimip_PgC"]
        ax.plot(annual["Year"], diff, color="k", linewidth=1.2)
        ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
        ax.set_ylabel(f"\u0394{v}\n({GLOBAL_POOL_UNIT})")
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Year")
    fig.suptitle("Difference in global carbon pools (IMOGEN \u2212 ISIMIP)", fontsize=12)
    fig.tight_layout()
    fig.savefig(str(path), dpi=160)
    plt.close(fig)


def _plot_diff_timeseries_fluxes(annual: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(len(CFLUX_VARS), 1, figsize=(11, 3 * len(CFLUX_VARS)), sharex=True)
    if len(CFLUX_VARS) == 1:
        axes = [axes]
    for ax, v in zip(axes, CFLUX_VARS):
        diff = annual[f"{v}_imogen_PgC"] - annual[f"{v}_isimip_PgC"]
        ax.plot(annual["Year"], diff, color="k", linewidth=1.2)
        ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
        ax.set_ylabel(f"\u0394{v}\n({GLOBAL_FLUX_UNIT})")
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Year")
    fig.suptitle("Difference in global carbon fluxes (IMOGEN \u2212 ISIMIP)", fontsize=12)
    fig.tight_layout()
    fig.savefig(str(path), dpi=160)
    plt.close(fig)


def _plot_bias_maps(bias: pd.DataFrame, varnames: list, unit: str, title_prefix: str, path: Path) -> None:
    n = len(varnames)
    fig, axes = plt.subplots(n, 1, figsize=(12, 3.5 * n))
    if n == 1:
        axes = [axes]
    for ax, v in zip(axes, varnames):
        col = f"bias_{v}"
        lon = bias["Lon"].values
        lat = bias["Lat"].values
        val = bias[col].values
        vmax = np.nanpercentile(np.abs(val), 98)
        vmax = max(vmax, 1e-10)
        sc = ax.scatter(lon, lat, c=val, s=1.5, cmap="RdBu_r", vmin=-vmax, vmax=vmax, rasterized=True)
        plt.colorbar(sc, ax=ax, label=f"Mean bias ({unit})")
        ax.set_title(f"{v}: IMOGEN \u2212 ISIMIP (time-mean)")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2)
    fig.suptitle(f"{title_prefix} mean bias maps", fontsize=12, y=1.01)
    fig.tight_layout()
    fig.savefig(str(path), dpi=170)
    plt.close(fig)


def _plot_scatter(merged: pd.DataFrame, varnames: list, unit: str, title_prefix: str,
                  snapshot_year: int, path: Path) -> None:
    sub = merged[merged["Year"] == snapshot_year]
    n = len(varnames)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 3.8))
    if n == 1:
        axes = [axes]
    for ax, v in zip(axes, varnames):
        a = sub[f"{v}_imogen"].values
        b = sub[f"{v}_isimip"].values
        hb = ax.hexbin(b, a, gridsize=70, cmap="viridis", mincnt=1)
        lim = [min(np.nanmin(a), np.nanmin(b)), max(np.nanmax(a), np.nanmax(b))]
        ax.plot(lim, lim, "r--", linewidth=1, alpha=0.85)
        ax.set_xlabel(f"ISIMIP ({unit})")
        ax.set_ylabel(f"IMOGEN ({unit})")
        ax.set_title(f"{v} — {snapshot_year}")
        plt.colorbar(hb, ax=ax, label="count")
    fig.suptitle(f"{title_prefix} scatter: IMOGEN vs ISIMIP ({snapshot_year})", fontsize=11)
    fig.tight_layout()
    fig.savefig(str(path), dpi=160)
    plt.close(fig)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--isimip-cpool", type=Path, default=DEFAULT_ISIMIP_CPOOL)
    p.add_argument("--isimip-cflux", type=Path, default=DEFAULT_ISIMIP_CFLUX)
    p.add_argument("--imogen-cpool", type=Path, default=DEFAULT_IMOGEN_CPOOL)
    p.add_argument("--imogen-cflux", type=Path, default=DEFAULT_IMOGEN_CFLUX)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--year-start", type=int, default=2021)
    p.add_argument("--year-end", type=int, default=2100)
    return p.parse_args()


def main():
    args = parse_args()
    run(
        isimip_cpool_path=args.isimip_cpool,
        isimip_cflux_path=args.isimip_cflux,
        imogen_cpool_path=args.imogen_cpool,
        imogen_cflux_path=args.imogen_cflux,
        output_dir=args.output_dir,
        year_start=args.year_start,
        year_end=args.year_end,
    )


if __name__ == "__main__":
    main()
