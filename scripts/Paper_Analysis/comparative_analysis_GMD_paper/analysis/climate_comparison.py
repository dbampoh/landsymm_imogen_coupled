#!/usr/bin/env python3
"""
Systematic comparison: IMOGEN REGRIDDED climate (ASCII) vs ISIMIP3b MRI-ESM2-0 (NetCDF4).

Cascade link (3): IMOGEN-coupled climate vs the ISIMIP-3b MRI-ESM2-0 reference climate.

Comparable variable pairs (IMOGEN file -> ISIMIP variable), after unit alignment:
  HEADLINE (main text):
    - tas    : T_anom.dat   <-> tas    (K)
    - pr     : P_anom.dat   <-> pr      (kg m-2 s-1 -> mm day-1 via *86400)
    - rsds   : SW_anom.dat  <-> rsds    (W m-2)
  SUPPLEMENTARY (SI):
    - tasmax : Tmax_anom.dat <-> tasmax (K)
    - tasmin : Tmin_anom.dat <-> tasmin (K)
    - dtr    : DTEMP_anom.dat <-> (tasmax - tasmin) derived (K)

Not paired (present in IMOGEN but not comparable to this ISIMIP set - see comprehensive
report): W_anom (wind; IMOGEN magnitudes inconsistent with ISIMIP sfcwind m/s),
Rh_anom (humidity; IMOGEN magnitudes inconsistent with ISIMIP hurs %), WET (baseline
climatological wet-day count; no direct ISIMIP counterpart), CO2/dtemp_o/fa_ocean (scalar).

Spatial alignment: IMOGEN land-centric points are matched to the nearest 0.5 deg ISIMIP
grid cell. Temporal: ISIMIP daily -> calendar-monthly means.

This driver loops over five SSP scenarios x three ~20-year analysis windows and, for each
scenario x window x comparable variable, computes:
  - summary stats (bias = IMOGEN-ISIMIP, RMSE, MAE, Pearson r [pooled], NRMSE);
  - spatial Taylor-diagram inputs (spatial pattern r, std ratio, centred RMSD);
  - global annual-mean trend overlays; zonal-mean profile overlays; spatial bias maps.

Outputs per (scenario, window): outputs_<ssp>_climate_<window>/ with CSVs/NPZ and PNG
figures tagged headline_* vs SI_*; master tables + per-variable Taylor diagrams in the
analysis dir.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date
from scipy import stats

# ---------------------------------------------------------------------------
# Defaults (override with env or CLI)
# ---------------------------------------------------------------------------
ANALYSIS_DIR = Path(__file__).resolve().parent

DEFAULT_IMOGEN_BASE = Path(
    os.environ.get(
        "IMOGEN_BASE",
        "/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/"
        "lpj-guess_imogen_landsymm/forks/trunk_r13078_runs",
    )
)
IMOGEN_SUBPATH = os.environ.get(
    "IMOGEN_SUBPATH", "Common-directory/IMOGEN/output_62892_cppengine"
)

DEFAULT_ISIMIP_BASE = Path(
    os.environ.get(
        "ISIMIP_BASE",
        "/media/bampoh-d/ISIMIP/inputs/climate_land_only_v2/climate3b",
    )
)

# Hyphenated IMOGEN scenario dir -> ISIMIP ssp code used in NetCDF filenames
SCENARIOS: Dict[str, str] = {
    "SSP1-2.6": "ssp126",
    "SSP2-4.5": "ssp245",
    "SSP3-7.0": "ssp370",
    "SSP4-6.0": "ssp460",
    "SSP5-8.5": "ssp585",
}

# Analysis windows: (label, requested_start, requested_end, actual_start, actual_end, note)
WINDOWS: List[Tuple[str, int, int, int, int, str]] = [
    (
        "2000_2020",
        2000,
        2020,
        2015,
        2020,
        "ISIMIP-3b scenario coverage begins 2015; requested 2000-2020 truncated to 2015-2020.",
    ),
    ("2040_2060", 2040, 2060, 2040, 2060, ""),
    ("2080_2100", 2080, 2100, 2080, 2100, ""),
]

SECONDS_PER_DAY = 86400.0

# Underlying ISIMIP-3b daily source variables (and unit scale to the analysis unit)
ISIMIP_SOURCE_VARS = ["tas", "pr", "rsds", "tasmax", "tasmin"]
ISIMIP_SCALE = {"tas": 1.0, "pr": SECONDS_PER_DAY, "rsds": 1.0, "tasmax": 1.0, "tasmin": 1.0}


def isimip_var_files(scenario: str) -> Dict[str, str]:
    return {
        v: f"mri-esm2-0_r1i1p1f1_w5e5_{scenario}_{v}_global_daily_2015_2100.nc4"
        for v in ISIMIP_SOURCE_VARS
    }


# Comparable variables. isimip = ("single", <source var>) or ("derived_dtr", None).
COMPARISONS: Dict[str, dict] = {
    "tas": {
        "imogen_file": "T_anom.dat",
        "isimip": ("single", "tas"),
        "label": "Near-surface air temperature",
        "unit": "K",
        "tier": "headline",
    },
    "pr": {
        "imogen_file": "P_anom.dat",
        "isimip": ("single", "pr"),
        "label": "Precipitation",
        "unit": "mm day-1",
        "tier": "headline",
    },
    "rsds": {
        "imogen_file": "SW_anom.dat",
        "isimip": ("single", "rsds"),
        "label": "Surface downwelling shortwave",
        "unit": "W m-2",
        "tier": "headline",
    },
    "tasmax": {
        "imogen_file": "Tmax_anom.dat",
        "isimip": ("single", "tasmax"),
        "label": "Daily maximum temperature",
        "unit": "K",
        "tier": "supplementary",
    },
    "tasmin": {
        "imogen_file": "Tmin_anom.dat",
        "isimip": ("single", "tasmin"),
        "label": "Daily minimum temperature",
        "unit": "K",
        "tier": "supplementary",
    },
    "dtr": {
        "imogen_file": "DTEMP_anom.dat",
        "isimip": ("derived_dtr", None),
        "label": "Diurnal temperature range (Tmax-Tmin)",
        "unit": "K",
        "tier": "supplementary",
    },
}

HEADLINE_VARS = [k for k, v in COMPARISONS.items() if v["tier"] == "headline"]
SI_VARS = [k for k, v in COMPARISONS.items() if v["tier"] == "supplementary"]


def sources_needed(comparisons: Iterable[str]) -> List[str]:
    need: set = set()
    for cv in comparisons:
        kind, arg = COMPARISONS[cv]["isimip"]
        if kind == "single":
            need.add(arg)
        elif kind == "derived_dtr":
            need.update(["tasmax", "tasmin"])
    return [v for v in ISIMIP_SOURCE_VARS if v in need]


@dataclass
class OnlineMoments:
    """Online weighted stats for paired (a, b) and difference d = a - b.
    All statistics are cos-latitude (gridcell-area) weighted: each (cell, month)
    sample carries the weight of its grid cell, so the reported global-mean bias,
    RMSE and pattern statistics are true area means over the 0.5 deg lat-lon land
    field rather than equal-per-cell averages (update with w=None reproduces the
    former unweighted behaviour)."""

    n: int = 0          # unweighted sample count (for n_samples reporting)
    sw: float = 0.0     # sum of weights
    swa: float = 0.0
    swb: float = 0.0
    swd: float = 0.0
    swd2: float = 0.0
    swabs: float = 0.0
    swa2: float = 0.0
    swb2: float = 0.0
    swab: float = 0.0

    def update(self, a: np.ndarray, b: np.ndarray, w: np.ndarray = None) -> None:
        a = np.asarray(a, dtype=float).ravel()
        b = np.asarray(b, dtype=float).ravel()
        if a.size == 0:
            return
        if w is None:
            w = np.ones_like(a)
        else:
            w = np.asarray(w, dtype=float).ravel()
        self.n += a.size
        self.sw += float(w.sum())
        self.swa += float((w * a).sum())
        self.swb += float((w * b).sum())
        d = a - b
        self.swd += float((w * d).sum())
        self.swd2 += float((w * d * d).sum())
        self.swabs += float((w * np.abs(d)).sum())
        self.swa2 += float((w * a * a).sum())
        self.swb2 += float((w * b * b).sum())
        self.swab += float((w * a * b).sum())

    def pearson_r(self) -> float:
        if self.sw <= 0:
            return float("nan")
        num = self.sw * self.swab - self.swa * self.swb
        den_a = self.sw * self.swa2 - self.swa**2
        den_b = self.sw * self.swb2 - self.swb**2
        if den_a <= 0 or den_b <= 0:
            return float("nan")
        return num / np.sqrt(den_a * den_b)

    def bias(self) -> float:
        return self.swd / self.sw if self.sw else float("nan")

    def rmse(self) -> float:
        return np.sqrt(self.swd2 / self.sw) if self.sw else float("nan")

    def mae(self) -> float:
        return self.swabs / self.sw if self.sw else float("nan")

    def mean_a(self) -> float:
        return self.swa / self.sw if self.sw else float("nan")

    def mean_b(self) -> float:
        return self.swb / self.sw if self.sw else float("nan")

    def std_a(self) -> float:
        if self.sw <= 0:
            return float("nan")
        m = self.mean_a()
        return float(np.sqrt(max(self.swa2 / self.sw - m * m, 0.0)))

    def std_b(self) -> float:
        if self.sw <= 0:
            return float("nan")
        m = self.mean_b()
        return float(np.sqrt(max(self.swb2 / self.sw - m * m, 0.0)))


def build_isimip_indices(lon: np.ndarray, lat: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Map IMOGEN (lon, lat) to ISIMIP 0.5 deg grid indices (lat: 0=N pole, lon: 0=-179.75)."""
    ilat = np.clip(np.round((89.75 - lat) / 0.5).astype(np.int32), 0, 359)
    ilon = np.clip(np.round((lon + 179.75) / 0.5).astype(np.int32), 0, 719)
    return ilat, ilon


def load_imogen_year(imogen_root: Path, year: int, comparisons: Iterable[str]) -> Dict[str, np.ndarray]:
    """Return monthly arrays (n_points, 12) per comparison variable."""
    ydir = imogen_root / str(year)
    out: Dict[str, np.ndarray] = {}
    for cv in comparisons:
        path = ydir / COMPARISONS[cv]["imogen_file"]
        if not path.is_file():
            raise FileNotFoundError(path)
        arr = np.loadtxt(path)
        if arr.shape[1] != 14:
            raise ValueError(f"{path}: expected 14 columns (lon,lat + 12 months)")
        out[cv] = arr[:, 2:14]
    return out


def load_imogen_coords(imogen_root: Path, year: int) -> Tuple[np.ndarray, np.ndarray]:
    path = imogen_root / str(year) / COMPARISONS["tas"]["imogen_file"]
    arr = np.loadtxt(path)
    return arr[:, 0], arr[:, 1]


FILL_THRESHOLD = 1e19  # ISIMIP land-only files use ~1e20 over ocean


class IsimipStack:
    """
    Efficient reader for ISIMIP-3b daily NetCDF4 whose chunking is [time, 1, 1]
    (the full time series of each grid cell is contiguous on disk). Reading a
    time-slice across all cells is pathological; instead we read each needed land
    cell's full time series once and bin it to per-year calendar-monthly means.

    The result is cached to disk per scenario (keyed by the set of needed years and
    source variables) so reruns are fast.
    """

    def __init__(self, isimip_dir: Path, ilat: np.ndarray, ilon: np.ndarray,
                 scenario: str, source_vars: List[str], needed_years: List[int],
                 cache_dir: Path | None = None) -> None:
        self.isimip_dir = isimip_dir
        self.ilat = np.asarray(ilat, dtype=np.int64)
        self.ilon = np.asarray(ilon, dtype=np.int64)
        self.source_vars = list(source_vars)
        self.scenario = scenario
        self.needed_years = sorted(set(int(y) for y in needed_years))
        self.npts = self.ilat.size
        self._files = isimip_var_files(scenario)

        # Bin layout: one column per (year, month) for needed years.
        self._year_list = self.needed_years
        self._year_to_col0 = {y: i * 12 for i, y in enumerate(self._year_list)}
        self.nbins = len(self._year_list) * 12

        # Unique cells + inverse map (points -> unique cell rows).
        key = self.ilat * 1000 + self.ilon
        _, uidx, self._inv = np.unique(key, return_index=True, return_inverse=True)
        self._ula = self.ilat[uidx]
        self._ulo = self.ilon[uidx]
        self._U = self._ula.size

        sig = f"{scenario}_y{self._year_list[0]}-{self._year_list[-1]}_n{len(self._year_list)}_v{'-'.join(self.source_vars)}_p{self.npts}"
        self._cache_path = (cache_dir / f"isimip_monthly_{sig}.npz") if cache_dir else None

        self._monthly_uc: Dict[str, np.ndarray] = {}
        if self._cache_path and self._cache_path.is_file():
            print(f"  loading ISIMIP monthly cache {self._cache_path.name}", flush=True)
            data = np.load(str(self._cache_path))
            for v in self.source_vars:
                self._monthly_uc[v] = data[v]
        else:
            self._build(isimip_dir)
            if self._cache_path:
                np.savez_compressed(str(self._cache_path), **self._monthly_uc)
                print(f"  saved ISIMIP monthly cache {self._cache_path.name}", flush=True)

    def _build(self, isimip_dir: Path) -> None:
        # Open first source for the time index.
        ds0 = Dataset(str(isimip_dir / self._files[self.source_vars[0]]), "r")
        tvar = ds0.variables["time"]
        tvals = np.asarray(tvar[:])
        cal = getattr(tvar, "calendar", "standard")
        dates = num2date(tvals, units=tvar.units, calendar=cal)
        yr = np.array([int(d.year) for d in dates], dtype=np.int32)
        mo = np.array([int(d.month) for d in dates], dtype=np.int32)
        ds0.close()

        # Day -> bin column (-1 if the day's year is not needed).
        day_bin = np.full(yr.size, -1, dtype=np.int64)
        for y in self._year_list:
            c0 = self._year_to_col0[y]
            sel = yr == y
            day_bin[sel] = c0 + (mo[sel] - 1)
        keep = day_bin >= 0
        day_bin_keep = day_bin[keep]

        for v in self.source_vars:
            print(f"  reading ISIMIP {v} ({self._U} cells) ...", flush=True)
            ds = Dataset(str(isimip_dir / self._files[v]), "r")
            var = ds.variables[v]
            scale = ISIMIP_SCALE[v]
            sums = np.zeros((self._U, self.nbins), dtype=np.float64)
            cnts = np.zeros((self._U, self.nbins), dtype=np.float64)
            for c in range(self._U):
                ts = np.ma.filled(np.asarray(var[:, self._ula[c], self._ulo[c]], dtype=np.float64), np.nan)
                ts = ts[keep]
                ok = np.isfinite(ts) & (np.abs(ts) < FILL_THRESHOLD)
                if not ok.all():
                    b = day_bin_keep[ok]
                    w = ts[ok]
                else:
                    b = day_bin_keep
                    w = ts
                sums[c] = np.bincount(b, weights=w, minlength=self.nbins)
                cnts[c] = np.bincount(b, minlength=self.nbins)
                if (c + 1) % 10000 == 0:
                    print(f"    {v}: {c + 1}/{self._U} cells", flush=True)
            ds.close()
            with np.errstate(invalid="ignore", divide="ignore"):
                mean_uc = np.where(cnts > 0, sums / cnts, np.nan) * scale
            self._monthly_uc[v] = mean_uc.astype(np.float32)

    def close(self) -> None:
        pass

    def yearly_monthly_sources(self, year: int) -> Dict[str, np.ndarray]:
        """Return monthly means at IMOGEN land points per source var: key -> (12, npts)."""
        if year not in self._year_to_col0:
            raise KeyError(f"Year {year} not in needed_years")
        c0 = self._year_to_col0[year]
        out: Dict[str, np.ndarray] = {}
        for v in self.source_vars:
            block_uc = self._monthly_uc[v][:, c0:c0 + 12]      # (U, 12)
            block_pts = block_uc[self._inv, :]                 # (npts, 12)
            out[v] = np.asarray(block_pts.T, dtype=np.float64)  # (12, npts)
        return out


def assemble_isimip_comparisons(sources: Dict[str, np.ndarray], comparisons: Iterable[str]) -> Dict[str, np.ndarray]:
    out: Dict[str, np.ndarray] = {}
    for cv in comparisons:
        kind, arg = COMPARISONS[cv]["isimip"]
        if kind == "single":
            out[cv] = sources[arg]
        elif kind == "derived_dtr":
            out[cv] = sources["tasmax"] - sources["tasmin"]
        else:
            raise ValueError(f"Unknown isimip spec for {cv}: {kind}")
    return out


# ---------------------------------------------------------------------------
# Matrix driver: scenarios x windows x variables
# ---------------------------------------------------------------------------

def imogen_root_for(scen_hyphen: str, imogen_base: Path) -> Path:
    return imogen_base / scen_hyphen / IMOGEN_SUBPATH


def isimip_dir_for(ssp: str, isimip_base: Path) -> Path:
    return isimip_base / ssp / "MRI-ESM2-0-lpjg"


@dataclass
class WindowAccum:
    npts: int
    comparisons: List[str]
    moments: Dict[str, OnlineMoments] = field(default_factory=dict)
    sum_a_pt: Dict[str, np.ndarray] = field(default_factory=dict)
    sum_b_pt: Dict[str, np.ndarray] = field(default_factory=dict)
    cnt_pt: Dict[str, np.ndarray] = field(default_factory=dict)
    n_months: int = 0
    annual: List[Dict[str, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in self.comparisons:
            self.moments[k] = OnlineMoments()
            self.sum_a_pt[k] = np.zeros(self.npts, dtype=np.float64)
            self.sum_b_pt[k] = np.zeros(self.npts, dtype=np.float64)
            self.cnt_pt[k] = np.zeros(self.npts, dtype=np.float64)


def spatial_taylor_stats(a_bar: np.ndarray, b_bar: np.ndarray,
                         lat: np.ndarray = None) -> Dict[str, float]:
    """Taylor-diagram inputs from window-mean fields. Reference = ISIMIP (b).
    cos-latitude (gridcell-area) weighted when lat is provided, so the spatial
    means, standard deviations, pattern correlation and centred RMSD are
    area-weighted statistics of the 0.5 deg lat-lon field."""
    ok = np.isfinite(a_bar) & np.isfinite(b_bar)
    a_bar = np.asarray(a_bar)[ok]
    b_bar = np.asarray(b_bar)[ok]
    if a_bar.size < 2:
        return {k: float("nan") for k in ("std_imogen_spatial", "std_isimip_spatial",
                "std_ratio", "spatial_pattern_r", "centered_rmsd_spatial",
                "spatial_mean_imogen", "spatial_mean_isimip")}
    if lat is not None:
        w = np.cos(np.deg2rad(np.asarray(lat)[ok]))
    else:
        w = np.ones_like(a_bar)
    W = float(w.sum())
    am = float((w * a_bar).sum() / W)
    bm = float((w * b_bar).sum() / W)
    da = a_bar - am
    db = b_bar - bm
    sa = float(np.sqrt((w * da * da).sum() / W))
    sb = float(np.sqrt((w * db * db).sum() / W))
    denom = np.sqrt((w * da * da).sum() * (w * db * db).sum())
    corr = float((w * da * db).sum() / denom) if denom > 0 else float("nan")
    crmsd = float(np.sqrt((w * (da - db) ** 2).sum() / W))
    return {
        "std_imogen_spatial": sa,
        "std_isimip_spatial": sb,
        "std_ratio": (sa / sb) if sb > 0 else float("nan"),
        "spatial_pattern_r": corr,
        "centered_rmsd_spatial": crmsd,
        "spatial_mean_imogen": am,
        "spatial_mean_isimip": bm,
    }


def run_scenario(
    scen_hyphen: str,
    ssp: str,
    imogen_base: Path,
    isimip_base: Path,
    output_base: Path,
    windows: List[Tuple[str, int, int, int, int, str]],
    comparisons: List[str],
) -> List[Dict[str, float]]:
    imogen_root = imogen_root_for(scen_hyphen, imogen_base)
    isimip_dir = isimip_dir_for(ssp, isimip_base)
    print(f"\n=== Scenario {scen_hyphen} ({ssp}) ===", flush=True)
    print(f"  IMOGEN: {imogen_root}")
    print(f"  ISIMIP: {isimip_dir}")

    coord_year = min(w[3] for w in windows)
    lon, lat = load_imogen_coords(imogen_root, coord_year)
    cosw = np.cos(np.deg2rad(lat))   # cos-latitude gridcell-area weights
    ilat, ilon = build_isimip_indices(lon, lat)
    npts = lon.size
    print(f"  {npts} IMOGEN land points; comparisons={comparisons}")

    win_years = {w[0]: list(range(w[3], w[4] + 1)) for w in windows}
    accum: Dict[str, WindowAccum] = {lab: WindowAccum(npts, comparisons) for lab in win_years}
    all_years = sorted(set().union(*win_years.values()))
    src = sources_needed(comparisons)

    cache_dir = output_base / "_isimip_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    stack = IsimipStack(isimip_dir, ilat, ilon, ssp, src, all_years, cache_dir=cache_dir)
    try:
        for y in all_years:
            print(f"    year {y} ...", flush=True)
            imog = load_imogen_year(imogen_root, y, comparisons)
            isim = assemble_isimip_comparisons(stack.yearly_monthly_sources(y), comparisons)
            for lab, yrs in win_years.items():
                if y not in yrs:
                    continue
                acc = accum[lab]
                annual_means = {k: {"a": 0.0, "b": 0.0, "n": 0} for k in comparisons}
                for m in range(12):
                    for key in comparisons:
                        a = imog[key][:, m]
                        b = isim[key][m]
                        ok = np.isfinite(a) & np.isfinite(b)
                        a_ok = a[ok]
                        b_ok = b[ok]
                        w_ok = cosw[ok]
                        acc.moments[key].update(a_ok, b_ok, w_ok)
                        # per-point window-mean accumulation (NaN-safe; per-cell, time-mean)
                        acc.sum_a_pt[key][ok] += a[ok]
                        acc.sum_b_pt[key][ok] += b[ok]
                        acc.cnt_pt[key][ok] += 1.0
                        # cos-lat area-weighted annual spatial mean
                        annual_means[key]["a"] += float((w_ok * a_ok).sum())
                        annual_means[key]["b"] += float((w_ok * b_ok).sum())
                        annual_means[key]["n"] += float(w_ok.sum())
                acc.n_months += 12
                for key in comparisons:
                    n = max(annual_means[key]["n"], 1)
                    acc.annual.append(
                        {
                            "year": y,
                            "variable": key,
                            "spatial_mean_imogen": annual_means[key]["a"] / n,
                            "spatial_mean_isimip": annual_means[key]["b"] / n,
                        }
                    )
    finally:
        stack.close()

    rows: List[Dict[str, float]] = []
    for lab, req0, req1, act0, act1, note in windows:
        out_dir = output_base / f"outputs_{ssp}_climate_{lab}"
        rows.extend(
            _finalize_window(
                out_dir, scen_hyphen, ssp, lab, req0, req1, act0, act1, note,
                lon, lat, accum[lab], imogen_root, isimip_dir, comparisons,
            )
        )
    return rows


def _finalize_window(
    out_dir: Path, scen_hyphen: str, ssp: str, label: str,
    req0: int, req1: int, act0: int, act1: int, note: str,
    lon: np.ndarray, lat: np.ndarray, acc: WindowAccum,
    imogen_root: Path, isimip_dir: Path, comparisons: List[str],
) -> List[Dict[str, float]]:
    out_dir.mkdir(parents=True, exist_ok=True)

    with np.errstate(invalid="ignore", divide="ignore"):
        a_bar = {k: np.where(acc.cnt_pt[k] > 0, acc.sum_a_pt[k] / np.where(acc.cnt_pt[k] > 0, acc.cnt_pt[k], 1), np.nan) for k in comparisons}
        b_bar = {k: np.where(acc.cnt_pt[k] > 0, acc.sum_b_pt[k] / np.where(acc.cnt_pt[k] > 0, acc.cnt_pt[k], 1), np.nan) for k in comparisons}
    bias_maps = {k: a_bar[k] - b_bar[k] for k in comparisons}

    meta = {
        "scenario": scen_hyphen,
        "ssp": ssp,
        "window_label": label,
        "requested_years": [req0, req1],
        "actual_years": [act0, act1],
        "note": note,
        "imogen_root": str(imogen_root),
        "isimip_dir": str(isimip_dir),
        "n_land_points": int(lon.size),
        "n_months": int(acc.n_months),
        "comparisons": {
            k: {
                "imogen": COMPARISONS[k]["imogen_file"],
                "isimip": COMPARISONS[k]["isimip"],
                "unit": COMPARISONS[k]["unit"],
                "tier": COMPARISONS[k]["tier"],
            }
            for k in comparisons
        },
        "isimip_pr_note": "pr converted from kg m-2 s-1 to mm day-1 via *86400 after monthly mean of daily rates",
    }
    (out_dir / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))

    summary_rows: List[Dict[str, float]] = []
    for key in comparisons:
        om = acc.moments[key]
        tay = spatial_taylor_stats(a_bar[key], b_bar[key], lat)
        summary_rows.append(
            {
                "scenario": scen_hyphen,
                "ssp": ssp,
                "window": label,
                "year_start": act0,
                "year_end": act1,
                "variable": key,
                "tier": COMPARISONS[key]["tier"],
                "label": COMPARISONS[key]["label"],
                "unit": COMPARISONS[key]["unit"],
                "n_samples": om.n,
                "mean_imogen": om.mean_a(),
                "mean_isimip": om.mean_b(),
                "bias_imogen_minus_isimip": om.bias(),
                "rmse": om.rmse(),
                "mae": om.mae(),
                "pearson_r_pooled": om.pearson_r(),
                "nrmse_rmse_over_std_isimip": (om.rmse() / om.std_b()) if om.std_b() and om.std_b() > 0 else float("nan"),
                "spatial_pattern_r": tay["spatial_pattern_r"],
                "std_imogen_spatial": tay["std_imogen_spatial"],
                "std_isimip_spatial": tay["std_isimip_spatial"],
                "std_ratio": tay["std_ratio"],
                "centered_rmsd_spatial": tay["centered_rmsd_spatial"],
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(out_dir / "summary_statistics.csv", index=False)

    annual_df = pd.DataFrame(acc.annual)
    annual_df.to_csv(out_dir / "annual_spatial_means.csv", index=False)

    trend_rows = []
    for key in comparisons:
        sub = annual_df[annual_df["variable"] == key].sort_values("year")
        x = sub["year"].values.astype(float)
        ya = sub["spatial_mean_imogen"].values
        yb = sub["spatial_mean_isimip"].values
        if x.size >= 2:
            sa, _, ra, _, _ = stats.linregress(x, ya)
            sb, _, rb, _, _ = stats.linregress(x, yb)
        else:
            sa = sb = ra = rb = float("nan")
        trend_rows.append(
            {
                "variable": key,
                "tier": COMPARISONS[key]["tier"],
                "unit": COMPARISONS[key]["unit"],
                "trend_imogen_per_year": sa,
                "trend_isimip_per_year": sb,
                "r2_imogen": ra**2 if np.isfinite(ra) else float("nan"),
                "r2_isimip": rb**2 if np.isfinite(rb) else float("nan"),
            }
        )
    pd.DataFrame(trend_rows).to_csv(out_dir / "trends_annual_spatial_mean.csv", index=False)

    zonal_df = _compute_zonal_means(lat, a_bar, b_bar, comparisons)
    zonal_df.to_csv(out_dir / "zonal_means.csv", index=False)

    np.savez_compressed(
        out_dir / "mean_bias_per_point.npz",
        lon=lon, lat=lat,
        **{f"imogen_{k}": a_bar[k] for k in comparisons},
        **{f"isimip_{k}": b_bar[k] for k in comparisons},
        **{f"bias_{k}": bias_maps[k] for k in comparisons},
    )

    title = f"{scen_hyphen} ({ssp}) {act0}-{act1}"
    for tier, keys in (("headline", [k for k in comparisons if COMPARISONS[k]["tier"] == "headline"]),
                       ("SI", [k for k in comparisons if COMPARISONS[k]["tier"] == "supplementary"])):
        if not keys:
            continue
        _plot_annual_trends(annual_df, keys, out_dir / f"fig_{tier}_annual_trends.png", title)
        _plot_zonal(zonal_df, keys, out_dir / f"fig_{tier}_zonal_means.png", title)
        _plot_bias_maps(lon, lat, bias_maps, keys, out_dir / f"fig_{tier}_bias_maps.png", title)

    print(f"  [{label}] wrote {out_dir}")
    return summary_rows


def _compute_zonal_means(lat, a_bar, b_bar, comparisons) -> pd.DataFrame:
    edges = np.arange(-90, 92, 2.0)
    centers = 0.5 * (edges[:-1] + edges[1:])
    bin_idx = np.clip(np.digitize(lat, edges) - 1, 0, centers.size - 1)
    rows = []
    for key in comparisons:
        for bi, c in enumerate(centers):
            m = bin_idx == bi
            if not np.any(m):
                continue
            rows.append(
                {
                    "lat_center": c,
                    "variable": key,
                    "tier": COMPARISONS[key]["tier"],
                    "n_points": int(m.sum()),
                    "zonal_mean_imogen": float(np.nanmean(a_bar[key][m])),
                    "zonal_mean_isimip": float(np.nanmean(b_bar[key][m])),
                }
            )
    return pd.DataFrame(rows)


def _panel_grid(n: int) -> Tuple[int, int]:
    return n, 1


def _plot_annual_trends(annual_df, keys, path, title) -> None:
    nr, nc = _panel_grid(len(keys))
    fig, axes = plt.subplots(nr, nc, figsize=(10, 3 * nr), squeeze=False)
    axes = axes.ravel()
    for ax, key in zip(axes, keys):
        sub = annual_df[annual_df["variable"] == key].sort_values("year")
        x = sub["year"].values.astype(float)
        ya = sub["spatial_mean_imogen"].values
        yb = sub["spatial_mean_isimip"].values
        ax.plot(x, ya, label="IMOGEN", marker="o", markersize=3, linewidth=1)
        ax.plot(x, yb, label="ISIMIP3b", marker="s", markersize=3, linewidth=1)
        if x.size >= 2:
            sa, ia, _, _, _ = stats.linregress(x, ya)
            sb, ib, _, _, _ = stats.linregress(x, yb)
            ax.plot(x, ia + sa * x, "--", linewidth=1, alpha=0.8, label=f"IMOGEN OLS ({sa:.3g}/yr)")
            ax.plot(x, ib + sb * x, "--", linewidth=1, alpha=0.8, label=f"ISIMIP OLS ({sb:.3g}/yr)")
        ax.set_ylabel(f"{key}\n({COMPARISONS[key]['unit']})")
        ax.legend(fontsize=7, loc="best")
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Year")
    fig.suptitle(f"Annual global-mean (land) trend overlay - {title}", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_zonal(zonal_df, keys, path, title) -> None:
    fig, axes = plt.subplots(1, len(keys), figsize=(4.6 * len(keys), 5), squeeze=False)
    axes = axes.ravel()
    for ax, key in zip(axes, keys):
        sub = zonal_df[zonal_df["variable"] == key].sort_values("lat_center")
        ax.plot(sub["zonal_mean_imogen"], sub["lat_center"], label="IMOGEN", linewidth=1.2)
        ax.plot(sub["zonal_mean_isimip"], sub["lat_center"], label="ISIMIP3b", linewidth=1.2)
        ax.set_xlabel(f"{key} ({COMPARISONS[key]['unit']})")
        ax.set_ylabel("Latitude")
        ax.set_title(COMPARISONS[key]["label"], fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle(f"Zonal-mean profile (window mean) - {title}", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_bias_maps(lon, lat, bias, keys, path, title) -> None:
    nr = len(keys)
    fig, axes = plt.subplots(nr, 1, figsize=(12, 4 * nr), squeeze=False)
    axes = axes.ravel()
    for ax, key in zip(axes, keys):
        v = bias[key]
        vmax = max(float(np.nanpercentile(np.abs(v), 98)), 1e-6)
        sc = ax.scatter(lon, lat, c=v, s=1.5, cmap="RdBu_r", vmin=-vmax, vmax=vmax, rasterized=True)
        plt.colorbar(sc, ax=ax, label=f"Bias ({COMPARISONS[key]['unit']})")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(f"{COMPARISONS[key]['label']}: IMOGEN - ISIMIP (window mean)")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2)
    fig.suptitle(f"Spatial bias maps - {title}", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_taylor(master_df: pd.DataFrame, out_dir: Path) -> List[Path]:
    """One normalized Taylor diagram per variable; points = scenario x window."""
    paths: List[Path] = []
    window_markers = {"2000_2020": "o", "2040_2060": "s", "2080_2100": "^"}
    scen_list = list(SCENARIOS.keys())
    cmap = plt.get_cmap("tab10")
    scen_colors = {s: cmap(i % 10) for i, s in enumerate(scen_list)}

    for key in master_df["variable"].unique():
        sub = master_df[master_df["variable"] == key]
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
            corr = r["spatial_pattern_r"]
            ratio = r["std_ratio"]
            if not (np.isfinite(corr) and np.isfinite(ratio)):
                continue
            theta = np.arccos(np.clip(corr, -1, 1))
            ax.plot(theta, ratio, marker=window_markers.get(r["window"], "o"),
                    color=scen_colors.get(r["scenario"], "gray"), markersize=8, linestyle="none")
        ax.set_title(
            f"Taylor diagram (normalized): {COMPARISONS[key]['label']}\n"
            f"radius = std$_{{IMOGEN}}$/std$_{{ISIMIP}}$, angle = spatial pattern correlation", fontsize=10)
        scen_handles = [plt.Line2D([], [], color=scen_colors[s], marker="o", linestyle="none", label=s) for s in scen_list]
        win_handles = [plt.Line2D([], [], color="k", marker=window_markers[w], linestyle="none", label=w) for w in window_markers]
        leg1 = ax.legend(handles=scen_handles, loc="upper right", bbox_to_anchor=(1.34, 1.0), fontsize=8, title="Scenario")
        ax.add_artist(leg1)
        ax.legend(handles=win_handles, loc="lower right", bbox_to_anchor=(1.34, 0.0), fontsize=8, title="Window")

        # Zoomed polar inset of the tight high-correlation cluster, so the
        # scenario/window structure (otherwise overplotted near r~0.98) is legible.
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
                axins.plot(theta, ratio, marker=window_markers.get(rr["window"], "o"),
                           color=scen_colors.get(rr["scenario"], "gray"), markersize=7, linestyle="none")
            axins.set_title("zoom: corr 0.95-1.0", fontsize=8, pad=6)

        p = out_dir / f"fig_taylor_{tier}_{key}.png"
        fig.tight_layout()
        fig.savefig(p, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(p)
    return paths


def run_matrix(imogen_base, isimip_base, output_base, scenarios, windows, comparisons) -> None:
    output_base.mkdir(parents=True, exist_ok=True)
    all_rows: List[Dict[str, float]] = []
    for scen_hyphen, ssp in scenarios.items():
        all_rows.extend(run_scenario(scen_hyphen, ssp, imogen_base, isimip_base, output_base, windows, comparisons))

    master = pd.DataFrame(all_rows)
    master_path = output_base / "climate_comparison_stats_all.csv"
    master.to_csv(master_path, index=False)
    master[master["tier"] == "headline"].to_csv(output_base / "climate_comparison_stats_headline.csv", index=False)
    master[master["tier"] == "supplementary"].to_csv(output_base / "climate_comparison_stats_supplementary.csv", index=False)

    taylor_cols = ["scenario", "ssp", "window", "variable", "tier", "unit",
                   "spatial_pattern_r", "std_imogen_spatial", "std_isimip_spatial",
                   "std_ratio", "centered_rmsd_spatial", "pearson_r_pooled"]
    master[taylor_cols].to_csv(output_base / "taylor_inputs.csv", index=False)
    taylor_paths = _plot_taylor(master, output_base)

    print("\n==================== MASTER SUMMARY ====================")
    show = master[["scenario", "window", "variable", "tier", "bias_imogen_minus_isimip",
                   "rmse", "pearson_r_pooled", "nrmse_rmse_over_std_isimip", "spatial_pattern_r"]]
    with pd.option_context("display.max_rows", None, "display.width", 220):
        print(show.to_string(index=False))
    print(f"\nMaster stats: {master_path}")
    for p in taylor_paths:
        print(f"Taylor figure: {p}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--imogen-base", type=Path, default=DEFAULT_IMOGEN_BASE)
    p.add_argument("--isimip-base", type=Path, default=DEFAULT_ISIMIP_BASE)
    p.add_argument("--output-base", type=Path, default=ANALYSIS_DIR)
    p.add_argument("--scenario", type=str, default=None,
                   help="Restrict to one scenario (hyphenated, e.g. SSP1-2.6). Default: all five.")
    p.add_argument("--window", type=str, default=None,
                   help="Restrict to one window label (e.g. 2000_2020). Default: all three.")
    p.add_argument("--vars", type=str, default=None,
                   help="Comma-separated comparison vars (default: all). E.g. tas,pr,rsds")
    p.add_argument("--replot-from", type=Path, default=None,
                   help="Skip the climate recompute; re-draw Taylor diagrams from a cached "
                        "master stats CSV (e.g. climate_comparison_stats_all.csv).")
    return p.parse_args(list(argv))


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.replot_from is not None:
        master = pd.read_csv(args.replot_from)
        args.output_base.mkdir(parents=True, exist_ok=True)
        for p in _plot_taylor(master, args.output_base):
            print(f"Taylor figure (replot): {p}")
        return 0
    scenarios = SCENARIOS
    if args.scenario:
        if args.scenario not in SCENARIOS:
            raise SystemExit(f"Unknown scenario {args.scenario}; choose from {list(SCENARIOS)}")
        scenarios = {args.scenario: SCENARIOS[args.scenario]}
    windows = WINDOWS
    if args.window:
        windows = [w for w in WINDOWS if w[0] == args.window]
        if not windows:
            raise SystemExit(f"Unknown window {args.window}; choose from {[w[0] for w in WINDOWS]}")
    comparisons = list(COMPARISONS.keys())
    if args.vars:
        comparisons = [v.strip() for v in args.vars.split(",") if v.strip()]
        bad = [v for v in comparisons if v not in COMPARISONS]
        if bad:
            raise SystemExit(f"Unknown vars {bad}; choose from {list(COMPARISONS)}")
    run_matrix(args.imogen_base, args.isimip_base, args.output_base, scenarios, windows, comparisons)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
