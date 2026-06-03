#!/usr/bin/env python3
"""
One-time preprocessing: extract ISIMIP3b daily data at IMOGEN land points,
aggregate to monthly means, and save as a compact .npz cache.

Input:  ~33 GB NetCDF4 files (daily, global 0.5°)
Output: ~200 MB .npz file (monthly, ~59k land points only)

After this runs once, the analysis script reads from the cache and finishes
in seconds instead of hours.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, num2date

_IS_WIN = sys.platform.startswith("win")

DEFAULT_IMOGEN_ROOT = Path(
    os.environ.get(
        "IMOGEN_SSP126",
        r"E:\climate_comp_landsymm_imogen\REGRIDDED-SSP126\REGRIDDED\SSP126"
        if _IS_WIN
        else "/mnt/e/climate_comp_landsymm_imogen/REGRIDDED-SSP126/REGRIDDED/SSP126",
    )
)
DEFAULT_ISIMIP_DIR = Path(
    os.environ.get(
        "ISIMIP_SSP126",
        r"E:\climate_comp_landsymm_imogen\ssp126\MRI-ESM2-0-lpjg"
        if _IS_WIN
        else "/mnt/e/climate_comp_landsymm_imogen/ssp126/MRI-ESM2-0-lpjg",
    )
)
DEFAULT_CACHE = Path(
    os.environ.get(
        "ISIMIP_CACHE",
        r"E:\climate_comp_landsymm_imogen\analysis\isimip_monthly_cache.npz"
        if _IS_WIN
        else "/mnt/e/climate_comp_landsymm_imogen/analysis/isimip_monthly_cache.npz",
    )
)

ISIMIP_FILES = {
    "tas": "mri-esm2-0_r1i1p1f1_w5e5_ssp126_tas_global_daily_2015_2100.nc4",
    "pr": "mri-esm2-0_r1i1p1f1_w5e5_ssp126_pr_global_daily_2015_2100.nc4",
    "rsds": "mri-esm2-0_r1i1p1f1_w5e5_ssp126_rsds_global_daily_2015_2100.nc4",
}

SECONDS_PER_DAY = 86400.0
SCALE = {"tas": 1.0, "pr": SECONDS_PER_DAY, "rsds": 1.0}


def build_isimip_indices(lon: np.ndarray, lat: np.ndarray):
    ilat = np.clip(np.round((89.75 - lat) / 0.5).astype(np.int32), 0, 359)
    ilon = np.clip(np.round((lon + 179.75) / 0.5).astype(np.int32), 0, 719)
    return ilat, ilon


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--imogen-root", type=Path, default=DEFAULT_IMOGEN_ROOT)
    p.add_argument("--isimip-dir", type=Path, default=DEFAULT_ISIMIP_DIR)
    p.add_argument("--output", type=Path, default=DEFAULT_CACHE)
    args = p.parse_args()

    # Load IMOGEN grid coordinates from any year file
    ref = args.imogen_root / "2015" / "T_anom.dat"
    print(f"Loading IMOGEN grid from {ref} ...")
    arr = np.loadtxt(str(ref))
    lon, lat = arr[:, 0], arr[:, 1]
    ilat, ilon = build_isimip_indices(lon, lat)
    npts = lon.size
    print(f"  {npts} land points, lat [{lat.min():.2f}, {lat.max():.2f}], lon [{lon.min():.2f}, {lon.max():.2f}]")

    # Open time index from the tas file
    tas_path = args.isimip_dir / ISIMIP_FILES["tas"]
    print(f"Reading time index from {tas_path} ...")
    ds0 = Dataset(str(tas_path), "r")
    tvar = ds0.variables["time"]
    tvals = np.asarray(tvar[:])
    cal = getattr(tvar, "calendar", "standard")
    dates = num2date(tvals, units=tvar.units, calendar=cal)
    years_arr = np.array([int(d.year) for d in dates], dtype=np.int16)
    months_arr = np.array([int(d.month) for d in dates], dtype=np.int8)
    ds0.close()

    year_min, year_max = int(years_arr.min()), int(years_arr.max())
    n_years = year_max - year_min + 1
    n_months_total = n_years * 12
    print(f"  Time range: {year_min}–{year_max} ({len(tvals)} daily timesteps, {n_months_total} year-months)")

    # Open all 3 datasets
    datasets = {}
    for key, fname in ISIMIP_FILES.items():
        datasets[key] = Dataset(str(args.isimip_dir / fname), "r")

    # Allocate output: (n_months_total, n_points) per variable
    result = {k: np.zeros((n_months_total, npts), dtype=np.float32) for k in ISIMIP_FILES}
    result_years = np.zeros(n_months_total, dtype=np.int16)
    result_months = np.zeros(n_months_total, dtype=np.int8)

    # Fill year/month index
    for yi, y in enumerate(range(year_min, year_max + 1)):
        for mi in range(12):
            idx = yi * 12 + mi
            result_years[idx] = y
            result_months[idx] = mi + 1

    # Process year by year
    wall0 = time.time()
    for y in range(year_min, year_max + 1):
        t0 = time.time()
        mask_y = years_arr == y
        day_indices = np.where(mask_y)[0]
        if day_indices.size == 0:
            continue
        i0, i1 = int(day_indices[0]), int(day_indices[-1]) + 1
        sub_months = months_arr[i0:i1]
        yi = y - year_min

        for key in ISIMIP_FILES:
            var = datasets[key].variables[key]
            chunk = np.asarray(var[i0:i1, :, :], dtype=np.float32)
            daily_pts = chunk[:, ilat, ilon]  # (ndays, npts)

            for m in range(1, 13):
                day_mask = sub_months == m
                if not np.any(day_mask):
                    continue
                out_idx = yi * 12 + (m - 1)
                result[key][out_idx] = daily_pts[day_mask].mean(axis=0) * SCALE[key]

        elapsed = time.time() - t0
        total_elapsed = time.time() - wall0
        years_done = y - year_min + 1
        rate = total_elapsed / years_done
        eta = rate * (year_max - y)
        print(f"  {y}: {elapsed:.0f}s  (total {total_elapsed/60:.1f}min, ETA {eta/60:.0f}min)")

    # Close datasets
    for ds in datasets.values():
        ds.close()

    # Save cache
    print(f"Saving cache to {args.output} ...")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        str(args.output),
        lon=lon,
        lat=lat,
        ilat=ilat,
        ilon=ilon,
        years=result_years,
        months=result_months,
        tas=result["tas"],
        pr=result["pr"],
        rsds=result["rsds"],
    )
    size_mb = args.output.stat().st_size / 1e6
    print(f"Done. Cache size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
