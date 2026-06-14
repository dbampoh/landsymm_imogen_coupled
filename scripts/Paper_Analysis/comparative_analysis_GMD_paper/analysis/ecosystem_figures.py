#!/usr/bin/env python3
"""Assemble the manuscript ecosystem-response figures (Sect. 3.4 + Supplement S3).

Mirrors the per-scenario, multi-panel composite style of the climate figures
(``climate_comparison.py`` -> Fig. 6): cos-lat window-mean (IMOGEN-coupled
- ISIMIP-3b prescribed) spatial-difference maps, RdBu_r, 150 dpi.

Reuses the data loaders / bias-map computation from ``ecosystem_comparison.py``
(no re-computation logic is duplicated). Global trajectory overlays are read from
the already-computed ``annual_*.csv`` files under the per-scenario output dirs.

Outputs (defaults; all under the gitignored ``paper/_media``):
  Main text:
    fig7_carbon_biasmap_<ssp>_eoc.png   (ssp126, ssp585) - VegC / SoilC / Total
    fig8_yield_biasmap_<ssp>_eoc.png    (ssp126, ssp585) - C4 / rice / C3 / OilNfix
  Supplement S3:
    figS_eco_carbon_biasmap_<ssp>_eoc.png  (ssp245, ssp370, ssp460)
    figS_eco_yield_biasmap_<ssp>_eoc.png   (ssp245, ssp370, ssp460)
    figS_eco_trends.png                    (global trajectories, all 5 scenarios)

Usage:
    python3 ecosystem_figures.py                 # all figures, default media dirs
    python3 ecosystem_figures.py --maps-only
    python3 ecosystem_figures.py --trends-only
"""
from __future__ import annotations

import argparse
import gzip
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["axes.unicode_minus"] = False   # plain hyphen-minus in tick/colourbar labels
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ecosystem_comparison import (  # noqa: E402
    SCEN_MAP, VARS, ANALYSIS_DIR, TRACK1_ROOT, TRACK2_ROOT, MONTHS,
    resolve_paths, load_var, gridcell_area_m2, mean_bias_map,
)

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[4]
MEDIA_RESULTS = REPO_ROOT / "paper" / "_media" / "results"
MEDIA_SUPP = REPO_ROOT / "paper" / "_media" / "supplement"

MAIN_SCENARIOS = ["SSP1-2.6", "SSP5-8.5"]                 # bracketing, main text
SI_SCENARIOS = ["SSP2-4.5", "SSP3-7.0", "SSP4-6.0"]       # intermediate, SI
ALL_SCENARIOS = ["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP4-6.0", "SSP5-8.5"]

WIN = (2080, 2100)

# Panels selected for each composite (var, column, human label)
CARBON_PANELS: List[Tuple[str, str, str]] = [
    ("cpool", "Total", "Total ecosystem carbon"),
    ("cpool", "SoilC", "Soil carbon"),
    ("cpool", "VegC", "Vegetation carbon"),
]
YIELD_PANELS: List[Tuple[str, str, str]] = [
    ("yield", "CerealsC4", "C4 cereals"),
    ("yield", "Rice", "Rice"),
    ("yield", "CerealsC3", "C3 cereals"),
    ("yield", "OilNfix", "N-fixing oil crops"),
]

SCEN_PRETTY = {
    "SSP1-2.6": "SSP1-2.6 (low forcing)",
    "SSP2-4.5": "SSP2-4.5",
    "SSP3-7.0": "SSP3-7.0",
    "SSP4-6.0": "SSP4-6.0",
    "SSP5-8.5": "SSP5-8.5 (high forcing)",
}


# --------------------------------------------------------------------------
# Bias-map composites
# --------------------------------------------------------------------------
def _load_window_bias(scenario: str, var: str) -> Dict[str, pd.DataFrame]:
    """Window-mean per-cell bias (IMOGEN-coupled - ISIMIP-3b) for every column of ``var``."""
    spec = VARS[var]
    paths = resolve_paths(scenario)
    t2 = load_var(paths["track2"], var).rename(columns={c: f"{c}_t2" for c in spec["cols"]})
    t1 = load_var(paths["track1"], var).rename(columns={c: f"{c}_t1" for c in spec["cols"]})
    merged = t2.merge(t1, on=["Lon", "Lat", "Year"])
    win = merged.query("@WIN[0] <= Year <= @WIN[1]")
    return mean_bias_map(win, spec["cols"])


def _draw_bias_panel(ax, m: pd.DataFrame, unit: str, title: str) -> None:
    vmax = float(np.nanpercentile(np.abs(m["bias"].values), 98)) or 1.0
    sc = ax.scatter(m["Lon"], m["Lat"], c=m["bias"], cmap="RdBu_r",
                    vmin=-vmax, vmax=vmax, s=1.2, marker="s", linewidths=0,
                    rasterized=True)
    ax.set_title(title, fontsize=10)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)
    ax.set_xlabel("Longitude", fontsize=8)
    ax.set_ylabel("Latitude", fontsize=8)
    ax.set_aspect("equal")
    ax.tick_params(labelsize=7)
    plt.colorbar(sc, ax=ax, label=unit, shrink=0.85)


def _composite_biasmap(scenario: str, panels: List[Tuple[str, str, str]],
                       suptitle: str, path: Path) -> None:
    # cache var-level bias once per var (cpool/yield loaded a single time)
    bias_by_var: Dict[str, Dict[str, pd.DataFrame]] = {}
    for var, _col, _lab in panels:
        if var not in bias_by_var:
            bias_by_var[var] = _load_window_bias(scenario, var)
    n = len(panels)
    fig, axes = plt.subplots(n, 1, figsize=(9, 2.7 * n), squeeze=False)
    for ax, (var, col, lab) in zip(axes[:, 0], panels):
        _draw_bias_panel(ax, bias_by_var[var][col], VARS[var]["unit"], lab)
    fig.suptitle(suptitle, fontsize=12, y=0.997)
    fig.tight_layout(rect=(0, 0, 1, 0.99))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path}")


def build_maps() -> None:
    for scen in MAIN_SCENARIOS:
        ssp = SCEN_MAP[scen]
        _composite_biasmap(
            scen, CARBON_PANELS,
            f"Ecosystem carbon response (IMOGEN-coupled - ISIMIP-3b), {SCEN_PRETTY[scen]}, "
            f"end of century ({WIN[0]}-{WIN[1]})",
            MEDIA_RESULTS / f"fig7_carbon_biasmap_{ssp}_eoc.png")
        _composite_biasmap(
            scen, YIELD_PANELS,
            f"Crop-yield response (IMOGEN-coupled - ISIMIP-3b), {SCEN_PRETTY[scen]}, "
            f"end of century ({WIN[0]}-{WIN[1]})",
            MEDIA_RESULTS / f"fig8_yield_biasmap_{ssp}_eoc.png")
    for scen in SI_SCENARIOS:
        ssp = SCEN_MAP[scen]
        _composite_biasmap(
            scen, CARBON_PANELS,
            f"Ecosystem carbon response (IMOGEN-coupled - ISIMIP-3b), {scen}, "
            f"end of century ({WIN[0]}-{WIN[1]})",
            MEDIA_SUPP / f"figS_eco_carbon_biasmap_{ssp}_eoc.png")
        _composite_biasmap(
            scen, YIELD_PANELS,
            f"Crop-yield response (IMOGEN-coupled - ISIMIP-3b), {scen}, "
            f"end of century ({WIN[0]}-{WIN[1]})",
            MEDIA_SUPP / f"figS_eco_yield_biasmap_{ssp}_eoc.png")


# --------------------------------------------------------------------------
# Global trajectory overlays (FULL PERIOD 1901-2100)
#   Historical (1901-2020): shared runs - IMOGEN-coupled = SSP2-4.5 cluster HIST
#   baseline; ISIMIP-3b = hist_wpeat. Scenario (2020-2100): per SSP.
#   For each column: cos-lat area-weighted MEAN (native unit) and the spatial
#   area-sum (sum value*area). A global TOTAL is meaningful only for GRIDCELL-
#   LEVEL quantities; per-land-cover (*_sum) and per-crop (yield) columns are
#   within-class densities (their totals would need land-use/crop-area fractions
#   not present in these outputs) and are therefore shown as MEAN.
# --------------------------------------------------------------------------
SCEN_COLORS = {
    "SSP1-2.6": "#1d3557", "SSP2-4.5": "#2a9d8f", "SSP3-7.0": "#e9c46a",
    "SSP4-6.0": "#f4a261", "SSP5-8.5": "#e63946",
}
HIST_T2_RUN = "SSP2-4.5_cluster_hist"   # shared IMOGEN-coupled historical baseline
HIST_T1_DIR = "hist_wpeat"               # shared ISIMIP-3b historical
TREND_CACHE = ANALYSIS_DIR / "_trend_cache"
SPLIT_YEAR = 2020                        # historical | scenario join

# Columns plotted per output (SI = all; cflux extended with LU_ch land-use-change).
SI_COLS: Dict[str, List[str]] = {
    "cpool": ["VegC", "LitterC", "SoilC", "Total"],
    "cmass": ["Total", "Natural_sum", "Crop_sum", "Pasture_sum", "Peatland_sum"],
    "anpp": ["Total", "Natural_sum", "Crop_sum", "Pasture_sum", "Peatland_sum"],
    "cflux": ["NEE", "Veg", "Soil", "LU_ch", "Fire", "Harvest"],
    "yield": ["CerealsC3", "CerealsC4", "Rice", "OilNfix", "OilOther", "Pulses"],
    "npool": ["VegN", "LitterN", "SoilN", "Total"],
    "ngases": ["N2O_soil", "N2O_fire", "Total"],
    "nflux": ["fix", "leach", "NEE"],
    "mch4": ["AnnualCH4"],
    "lai": ["Total"],
    "tot_runoff": ["Total", "Surf", "Drain", "Base"],
}
# Global-total display unit + scale applied to sum(value * area_m2):
#   carbon/nitrogen per m2 (kg) -> Pg = 1e-12 (1 Pg = 1e12 kg);
#   N per ha (kg/ha) -> Tg = 1e-4*1e-9 = 1e-13; wetland CH4 (g/m2) -> Tg = 1e-12;
#   runoff mm*m2 -> km3 = 1e-3*1e-9 = 1e-12.
TOTAL_UNIT: Dict[str, Tuple[str, float]] = {
    "cpool": ("Pg C", 1e-12), "cmass": ("Pg C", 1e-12),
    "anpp": ("Pg C yr$^{-1}$", 1e-12), "cflux": ("Pg C yr$^{-1}$", 1e-12),
    "npool": ("Pg N", 1e-12), "ngases": ("Tg N yr$^{-1}$", 1e-13),
    "nflux": ("Tg N yr$^{-1}$", 1e-13), "mch4": ("Tg CH$_4$ yr$^{-1}$", 1e-12),
    "tot_runoff": ("km$^3$ yr$^{-1}$", 1e-12),
}
# Main-text panels: gridcell-level quantities only (continuous full period).
# NPP + yields are excluded from the main-text trends (within-stand/per-crop
# quantities discontinuous at the 2020 LU-dataset join; reported as mean stats
# in Tables 13/S2/S4/S5 and as scenario-period SI trends, Figs S10/S12).
MAIN_PANELS = [
    ("cpool", ["VegC", "SoilC", "Total"], "total"),
    ("cflux", ["NEE", "Veg", "Soil", "LU_ch"], "total"),
    ("npool", ["VegN", "SoilN", "Total"], "total"),
    ("nflux", ["NEE", "leach"], "total"),
]
MAIN_SCEN = ["SSP1-2.6", "SSP5-8.5"]
MAIN_FIGNUM = {"SSP1-2.6": 9, "SSP5-8.5": 10}
# Within-land-cover (per-stand) outputs carry a discontinuity at the 2020
# HILDA+->PLUM land-use-dataset join that land-cover-fraction weighting does not
# remove (the cropland fraction is continuous across the join; the join
# redistributes productivity among land covers + re-establishes crop stands in
# 2021). These are therefore shown over the internally consistent scenario
# period only. Gridcell-level outputs (cpool/cflux/npool/nflux/...) are unaffected.
CLIP_SCENARIO = {"anpp", "yield"}
CLIP_START = 2022
COL_PALETTE = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#a6761d"]
# cmass/anpp are recomputed from the raw .out.gz so their within-land-cover *_sum
# global totals can be land-cover-fraction-weighted (see load_lu); they are NOT
# read from the precomputed annual CSVs (whose *_global for *_sum would be the
# unweighted sum(density x cell_area), which is not a physical total).
CSV_OK = {"cpool", "npool", "mch4", "yield", "lai"}

# --------------------------------------------------------------------------
# Land-use area fractions (harmonised LU forcing that drove BOTH tracks).
# The main .out.gz *_sum columns (cmass/anpp) are within-land-cover densities
# (per m2 of that land cover). A physically meaningful global total is
#   sum_cells ( density x landcover_fraction x cell_area ),
# which reproduces the gridcell Total exactly (validated: ratio 1.0000).
# Files are the _peatland-tagged LU: cols Lon Lat Year NATURAL CROPLAND PASTURE
# PEATLAND BARREN.
# --------------------------------------------------------------------------
_LU_BASE = Path("/media/bampoh-d/ISIMIP/inputs/landuse/plum_harm_lu")
LU_HIST_FILE = (_LU_BASE / "output_hildaplus_remap_10b_3" /
                "remaps_v10_old_62892_gL" / "LU.remapv10_old_62892_gL_peatland.txt")
LU_SCEN_DIR = {
    "SSP1-2.6": "SSP1_RCP26", "SSP2-4.5": "SSP2_RCP45", "SSP3-7.0": "SSP3_RCP70",
    "SSP4-6.0": "SSP4_RCP60", "SSP5-8.5": "SSP5_RCP85",
}
LU_SCEN_SUB = Path("s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG") / "landcover_peatland.txt"
LU_COLS = ["NATURAL", "CROPLAND", "PASTURE", "PEATLAND"]
SUMCOL_TO_LU = {"Natural_sum": "NATURAL", "Crop_sum": "CROPLAND",
                "Pasture_sum": "PASTURE", "Peatland_sum": "PEATLAND"}
LU_WEIGHTED_VARS = {"cmass", "anpp"}
_LU_FRAME_CACHE: Dict[str, pd.DataFrame] = {}


def lu_file_for(scope: str) -> Path:
    return LU_HIST_FILE if scope == "hist" else (_LU_BASE / LU_SCEN_DIR[scope] / LU_SCEN_SUB)


def load_lu(scope: str) -> pd.DataFrame:
    """Per-cell, per-year land-cover area fractions for a scope (cached in memory)."""
    if scope not in _LU_FRAME_CACHE:
        df = pd.read_csv(lu_file_for(scope), sep=r"\s+")
        _LU_FRAME_CACHE[scope] = df[["Lon", "Lat", "Year"] + LU_COLS]
    return _LU_FRAME_CACHE[scope]


# crop_sum carries a within-stand density step at the 2020 HILDA+ -> PLUM join
# (crop stands re-established in 2021); smooth its trajectory for legibility.
SMOOTH_COLS = {("cmass", "Crop_sum")}
SMOOTH_WIN = 21
HIST_COLOR = "#1a1a1a"   # shared (scenario-identical) historical segment, drawn once in black


def _smooth(y: np.ndarray, win: int = SMOOTH_WIN) -> np.ndarray:
    return pd.Series(y).rolling(win, center=True, min_periods=1).mean().values


def total_ok(var: str, col: str) -> bool:
    """True if a global total is physically meaningful. Gridcell-level quantities
    always qualify; for cmass/anpp the within-land-cover *_sum densities qualify
    too because they are area-totalled with the land-cover fraction (load_lu)."""
    if var not in TOTAL_UNIT:
        return False
    if col.endswith("_sum"):
        return var in LU_WEIGHTED_VARS
    return True


def col_label(var: str, col: str) -> str:
    """Display label: the cflux net carbon flux is F_net (Sect. 2.2.6); the
    nflux net term is a nitrogen flux. Avoids the term NEE (per Methods)."""
    if var == "cflux" and col == "NEE":
        return "$F_{net}$"
    if var == "nflux" and col == "NEE":
        return "net N"
    return col


def _annual_dir(scenario: str) -> Path:
    ssp = SCEN_MAP[scenario]
    return ANALYSIS_DIR / f"outputs_ecosystem_{ssp}_{WIN[0]}_{WIN[1]}"


def _hist_dirs():
    t2 = sorted((TRACK2_ROOT / HIST_T2_RUN).glob("output-*"))
    t1 = sorted((TRACK1_ROOT / HIST_T1_DIR).glob("output-*"))
    return (t2[-1] if t2 else None), (t1[-1] if t1 else None)


def _load_cols(d: Path, var: str, cols: List[str]) -> pd.DataFrame:
    spec = VARS[var]
    with gzip.open(str(d / f"{var}.out.gz"), "rt") as f:
        df = pd.read_csv(f, sep=r"\s+")
    if spec.get("agg") == "sum_months":
        df["AnnualCH4"] = df[MONTHS].sum(axis=1)
    return df[["Lon", "Lat", "Year"] + cols]


def _agg_from_gz(d2: Path, d1: Path, var: str, cols: List[str], scope: str = None) -> pd.DataFrame:
    """Per-year area-weighted MEAN and area-SUM for each column, both configs.
    For cmass/anpp, the within-land-cover *_sum columns are area-totalled with
    the land-cover fraction (load_lu), so their global TOTAL is physical."""
    a = _load_cols(d2, var, cols)
    b = _load_cols(d1, var, cols)
    m = a.merge(b, on=["Lon", "Lat", "Year"], suffixes=("_track2", "_track1"))
    m["area"] = gridcell_area_m2(m["Lat"].values)
    use_lu = (var in LU_WEIGHTED_VARS and scope is not None
              and any(c in SUMCOL_TO_LU for c in cols))
    if use_lu:
        m = m.merge(load_lu(scope), on=["Lon", "Lat", "Year"], how="left")
    rows = []
    for yr, g in m.groupby("Year"):
        w = g["area"].values
        row = {"Year": int(yr)}
        for col in cols:
            lucol = SUMCOL_TO_LU.get(col) if use_lu else None
            for trk in ("track2", "track1"):
                v = g[f"{col}_{trk}"].values
                ok = np.isfinite(v)
                row[f"{col}_{trk}_wmean"] = (
                    float((v[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else float("nan"))
                if lucol is not None:
                    fr = g[lucol].values
                    fok = ok & np.isfinite(fr)
                    row[f"{col}_{trk}_gsum"] = float((v[fok] * fr[fok] * w[fok]).sum())
                else:
                    row[f"{col}_{trk}_gsum"] = float((v[ok] * w[ok]).sum())
        rows.append(row)
    return pd.DataFrame(rows).sort_values("Year").reset_index(drop=True)


def get_series(var: str, scope: str) -> pd.DataFrame:
    """Annual MEAN + area-SUM for SI_COLS[var]; scope = 'hist' or a scenario.
    Cached. Scenario 'easy' vars reuse the precomputed annual CSV; cflux/ngases/
    nflux/tot_runoff and all historical are computed from the raw .out.gz."""
    cols = SI_COLS[var]
    TREND_CACHE.mkdir(parents=True, exist_ok=True)
    cache = TREND_CACHE / f"trend_{var}_{scope}.csv"
    if cache.exists():
        return pd.read_csv(cache)
    if scope != "hist" and var in CSV_OK:
        src = pd.read_csv(_annual_dir(scope) / f"annual_{var}.csv")
        out = {"Year": src["Year"]}
        for col in cols:
            for trk in ("track2", "track1"):
                out[f"{col}_{trk}_wmean"] = src[f"{col}_{trk}_wmean"]
                g = f"{col}_{trk}_global"
                if g in src.columns:
                    out[f"{col}_{trk}_gsum"] = src[g]
        df = pd.DataFrame(out)
    else:
        if scope == "hist":
            d2, d1 = _hist_dirs()
        else:
            p = resolve_paths(scope)
            d2, d1 = p["track2"], p["track1"]
        if d2 is None or d1 is None or not (d2 / f"{var}.out.gz").exists():
            return pd.DataFrame()
        print(f"    [{scope}] {var} ...", flush=True)
        df = _agg_from_gz(d2, d1, var, cols, scope=scope)
    df.to_csv(cache, index=False)
    return df


def full_series(var: str, scenario: str) -> pd.DataFrame:
    """Historical (<2020) + scenario (>=2020) concatenated full-period series."""
    h = get_series(var, "hist")
    s = get_series(var, scenario)
    if h is None or h.empty:
        return s
    if s is None or s.empty:
        return h
    h = h[h["Year"] < int(s["Year"].min())]   # keep historical up to the scenario start
    return pd.concat([h, s], ignore_index=True).sort_values("Year").reset_index(drop=True)


def _config_handles():
    return [plt.Line2D([], [], color="0.3", lw=1.6, ls="-", label="ISIMIP-3b prescribed"),
            plt.Line2D([], [], color="0.3", lw=1.6, ls="--", label="IMOGEN-coupled")]


def _plot_trend_split(ax, fs_fn, col: str, kind: str, scale: float,
                      clipped: bool, smooth: bool, lw: float = 0.9) -> None:
    """Plot the shared (scenario-identical) historical segment once in black, and
    each scenario's post-2020 segment in its colour. kind in {'wmean','gsum'};
    scale multiplies the value. For clipped (scenario-only) vars no black
    historical is drawn and each scenario is plotted over its full range."""
    def yvals(df, trk):
        y = df[f"{col}_{trk}_{kind}"].values * scale
        return _smooth(y) if smooth else y
    if not clipped:
        dfh = fs_fn(ALL_SCENARIOS[0])
        yr = dfh["Year"].values
        mh = yr < SPLIT_YEAR
        for trk, ls in (("track1", "-"), ("track2", "--")):
            ax.plot(yr[mh], yvals(dfh, trk)[mh], color=HIST_COLOR, ls=ls, lw=lw, zorder=6)
    for scen in ALL_SCENARIOS:
        df = fs_fn(scen)
        yr = df["Year"].values
        m = (yr >= SPLIT_YEAR) if not clipped else np.ones(len(yr), dtype=bool)
        c = SCEN_COLORS[scen]
        for trk, ls in (("track1", "-"), ("track2", "--")):
            ax.plot(yr[m], yvals(df, trk)[m], color=c, ls=ls, lw=lw)


def _scenario_trendfig(scen: str, outpath: Path) -> None:
    """One per-scenario 4-panel ecosystem-trajectory composite (cpool / cflux /
    npool / nflux). Lines are coloured by output column (not scenario), so the
    shared historical period is shown per column rather than in black."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), squeeze=False)
    axes = axes.ravel()
    for ax, (var, cols, qty) in zip(axes, MAIN_PANELS):
        df = full_series(var, scen)
        clipped = var in CLIP_SCENARIO
        if clipped:
            df = df[df["Year"] >= CLIP_START]
        ylab = f"area-wt mean ({VARS[var]['unit']})"
        for k, col in enumerate(cols):
            cc = COL_PALETTE[k % len(COL_PALETTE)]
            if qty == "total" and total_ok(var, col):
                unit, sc = TOTAL_UNIT[var]
                y1, y2 = df[f"{col}_track1_gsum"] * sc, df[f"{col}_track2_gsum"] * sc
                ylab = f"global total ({unit})"
            else:
                y1, y2 = df[f"{col}_track1_wmean"], df[f"{col}_track2_wmean"]
            ax.plot(df["Year"], y1, color=cc, ls="-", lw=1.3)
            ax.plot(df["Year"], y2, color=cc, ls="--", lw=1.3)
        if not clipped:
            ax.axvline(SPLIT_YEAR, color="0.6", lw=0.8, ls=":")
        ax.set_title(var + (" (scenario period)" if clipped else ""), fontsize=11)
        ax.set_xlabel("Year", fontsize=9)
        ax.set_ylabel(ylab, fontsize=9)
        ax.grid(alpha=0.3); ax.tick_params(labelsize=8)
        col_h = [plt.Line2D([], [], color=COL_PALETTE[k % len(COL_PALETTE)], lw=1.4,
                            label=col_label(var, c)) for k, c in enumerate(cols)]
        ax.legend(handles=col_h, fontsize=6.5, ncol=2, loc="best")
    fig.legend(handles=_config_handles(), loc="lower center", ncol=2, fontsize=10,
               frameon=False, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle(f"Ecosystem-state trajectories 1901-2100, {scen}: "
                 f"ISIMIP-3b prescribed (solid) vs IMOGEN-coupled (dashed)", fontsize=13)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    outpath.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(outpath), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {outpath}")


def build_main_trends() -> None:
    """Per-scenario 4-panel composites: the bracketing scenarios as main-text
    Fig 9 (SSP1-2.6) and Fig 10 (SSP5-8.5); the three intermediate scenarios as
    the equivalent Supplement figures."""
    for scen in MAIN_SCEN:
        _scenario_trendfig(scen, MEDIA_RESULTS / f"fig{MAIN_FIGNUM[scen]}_eco_trends_{SCEN_MAP[scen]}.png")
    for scen in SI_SCENARIOS:
        _scenario_trendfig(scen, MEDIA_SUPP / f"figS_eco_trends_{SCEN_MAP[scen]}.png")


def build_si_trends() -> None:
    """One figure per output: per-column MEAN (top) and global TOTAL (bottom,
    where meaningful), all five scenarios, full period."""
    for var, cols in SI_COLS.items():
        has_total = any(total_ok(var, c) for c in cols)
        clipped = var in CLIP_SCENARIO
        def fs(scen, _v=var, _c=clipped):
            d = full_series(_v, scen)
            return d[d["Year"] >= CLIP_START] if _c else d
        nrow = 2 if has_total else 1
        fig, axes = plt.subplots(nrow, len(cols),
                                 figsize=(3.9 * len(cols), 3.3 * nrow), squeeze=False)
        for j, col in enumerate(cols):
            axm = axes[0][j]
            smooth = (var, col) in SMOOTH_COLS
            _plot_trend_split(axm, fs, col, "wmean", 1.0, clipped, smooth)
            if not clipped:
                axm.axvline(SPLIT_YEAR, color="0.6", lw=0.8, ls=":")
            axm.set_title(col_label(var, col), fontsize=9)
            axm.set_ylabel(f"mean ({VARS[var]['unit']})", fontsize=8)
            axm.grid(alpha=0.3); axm.tick_params(labelsize=7)
            if not has_total:
                axm.set_xlabel("Year", fontsize=8)
                continue
            axt = axes[1][j]
            if total_ok(var, col):
                unit, sc = TOTAL_UNIT[var]
                _plot_trend_split(axt, fs, col, "gsum", sc, clipped, smooth)
                axt.set_ylabel(f"global total ({unit})", fontsize=8)
                axt.grid(alpha=0.3)
            else:
                axt.text(0.5, 0.5, "global total not defined\n(within-land-cover density)",
                         ha="center", va="center", fontsize=7, color="0.45",
                         transform=axt.transAxes)
                axt.set_xticks([]); axt.set_yticks([])
            if not clipped:
                axt.axvline(SPLIT_YEAR, color="0.6", lw=0.8, ls=":")
            axt.set_xlabel("Year", fontsize=8); axt.tick_params(labelsize=7)
        hist_h = ([plt.Line2D([], [], color=HIST_COLOR, lw=1.6, label="Shared historical (1901-2019)")]
                  if not clipped else [])
        scen_h = [plt.Line2D([], [], color=SCEN_COLORS[s], lw=1.6, label=s) for s in ALL_SCENARIOS]
        fig.legend(handles=hist_h + scen_h + _config_handles(), loc="lower center",
                   ncol=8, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
        _yr = f"{CLIP_START}-2100 (scenario period)" if clipped else "1901-2100"
        fig.suptitle(f"{var}: global trajectories {_yr}, ISIMIP-3b prescribed "
                     f"(solid) vs IMOGEN-coupled (dashed)", fontsize=11)
        fig.tight_layout(rect=(0, 0.05, 1, 0.96))
        MEDIA_SUPP.mkdir(parents=True, exist_ok=True)
        p = MEDIA_SUPP / f"figS_trend_{var}.png"
        fig.savefig(str(p), dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  wrote {p}")


def build_lu_forcing() -> None:
    """SI figures documenting the harmonised land-use forcing used to drive BOTH
    tracks: (1) global land-cover area trajectories 1901-2100 (HILDA+ historical
    + PLUM scenarios); (2) end-of-century (2080-2100) mean land-cover-fraction
    maps for the bracketing scenarios."""
    LC_LABEL = {"NATURAL": "Natural", "CROPLAND": "Cropland",
                "PASTURE": "Pasture", "PEATLAND": "Peatland"}

    def global_area_by_year(df: pd.DataFrame) -> Dict[str, pd.Series]:
        a = gridcell_area_m2(df["Lat"].values)
        tmp = df[["Year"]].copy()
        out: Dict[str, pd.Series] = {}
        for lc in LU_COLS:
            tmp["_v"] = df[lc].values * a
            out[lc] = tmp.groupby("Year")["_v"].sum() * 1e-12   # m2 -> million km2
        return out

    hist = global_area_by_year(load_lu("hist"))
    scen = {s: global_area_by_year(load_lu(s)) for s in ALL_SCENARIOS}

    # (1) global land-cover area trajectories
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.7), squeeze=False)
    for j, lc in enumerate(LU_COLS):
        ax = axes[0][j]
        hs = hist[lc]; hy = hs.index.values; mh = hy < SPLIT_YEAR
        ax.plot(hy[mh], hs.values[mh], color=HIST_COLOR, lw=1.8, zorder=5)
        for s in ALL_SCENARIOS:
            ss = scen[s][lc]; sy = ss.index.values; ms = sy >= SPLIT_YEAR
            ax.plot(sy[ms], ss.values[ms], color=SCEN_COLORS[s], lw=1.2)
        ax.axvline(SPLIT_YEAR, color="0.6", lw=0.8, ls=":")
        ax.set_title(LC_LABEL[lc], fontsize=11)
        ax.set_xlabel("Year", fontsize=9)
        ax.set_ylabel("global area (million km$^2$)", fontsize=9)
        ax.set_xlim(1901, 2100); ax.grid(alpha=0.3); ax.tick_params(labelsize=8)
    handles = [plt.Line2D([], [], color=HIST_COLOR, lw=1.8, label="Shared historical (HILDA+)")]
    handles += [plt.Line2D([], [], color=SCEN_COLORS[s], lw=1.6, label=s) for s in ALL_SCENARIOS]
    fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=8,
               frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("Harmonised land-use forcing: global land-cover area, 1901-2100 "
                 "(HILDA+ historical, PLUM scenarios)", fontsize=12)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    p1 = MEDIA_SUPP / "figS_lu_forcing_trends.png"
    fig.savefig(str(p1), dpi=150, bbox_inches="tight"); plt.close(fig); print(f"  wrote {p1}")

    # (2) end-of-century mean land-cover-fraction maps (all scenarios)
    map_scens = ALL_SCENARIOS
    eoc = {}
    for s in map_scens:
        df = load_lu(s)
        sub = df[(df["Year"] >= WIN[0]) & (df["Year"] <= WIN[1])]
        eoc[s] = sub.groupby(["Lon", "Lat"], as_index=False)[LU_COLS].mean()
    fig, axes = plt.subplots(len(map_scens), len(LU_COLS),
                             figsize=(4.0 * len(LU_COLS), 2.4 * len(map_scens)), squeeze=False)
    scat = None
    for r, s in enumerate(map_scens):
        d = eoc[s]
        for cidx, lc in enumerate(LU_COLS):
            ax = axes[r][cidx]
            scat = ax.scatter(d["Lon"], d["Lat"], c=d[lc], cmap="YlGn", vmin=0, vmax=1,
                              s=0.8, marker="s", linewidths=0, rasterized=True)
            if r == 0:
                ax.set_title(LC_LABEL[lc], fontsize=10)
            if cidx == 0:
                ax.set_ylabel(f"{s}\nLatitude", fontsize=8)
            if r == len(map_scens) - 1:
                ax.set_xlabel("Longitude", fontsize=7)
            ax.set_xlim(-180, 180); ax.set_ylim(-60, 85); ax.set_aspect("equal")
            ax.tick_params(labelsize=5)
    fig.colorbar(scat, ax=axes.ravel().tolist(), shrink=0.5,
                 label="land-cover fraction", pad=0.01)
    fig.suptitle(f"Land-use forcing: end-of-century ({WIN[0]}-{WIN[1]}) mean land-cover fraction, "
                 f"all SSP-RCP scenarios", fontsize=12, y=1.0)
    p2 = MEDIA_SUPP / "figS_lu_forcing_eoc_maps.png"
    fig.savefig(str(p2), dpi=150, bbox_inches="tight"); plt.close(fig); print(f"  wrote {p2}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maps-only", action="store_true")
    ap.add_argument("--trends-only", action="store_true")
    ap.add_argument("--main-trends-only", action="store_true")
    ap.add_argument("--si-trends-only", action="store_true")
    ap.add_argument("--lu-only", action="store_true")
    a = ap.parse_args()
    if a.main_trends_only:
        build_main_trends(); print("Done."); return
    if a.si_trends_only:
        build_si_trends(); build_lu_forcing(); print("Done."); return
    if a.lu_only:
        build_lu_forcing(); print("Done."); return
    if not a.trends_only:
        print("Building bias-map composites ...")
        build_maps()
    if not a.maps_only:
        print("Building trend figures (main + SI, full period) ...")
        build_main_trends()
        build_si_trends()
        print("Building land-use forcing figures ...")
        build_lu_forcing()
    print("Done.")


if __name__ == "__main__":
    main()
