#!/usr/bin/env python3
"""
tools/crujra_to_imogen_baseline.py
==================================

Build the IMOGEN base climatology (the `imogen/CRUNCEP_1960_1989/<mon><off>`
ASCII library, 360 files = 30 years x 12 months on the 1631-cell HadCM3 land
grid) from a SINGLE consistent source: CRU-JRA v2.4 monthly-mean NetCDF.

WHY
---
The legacy CRUNCEP_1960_1989 ASCII (reduced by the predecessor framework from
the CRUNCEP-v7 *main* fast-archive) carries ZERO relative humidity (col 4),
zero U/V wind (cols 5/6), zero downward longwave (col 7) and zero surface
pressure (col 12) for every cell -- the misc archive holding RH/wind was never
read, and surface pressure was never in any CRUNCEP fast-archive. The IMOGEN
engine adds GCM pattern anomalies on top of this baseline, so RH and wind handed
to LPJ-GUESS (and consumed by the BLAZE fire model) were ~0. CRU-JRA v2.4 is the
direct successor to CRUNCEP-v7 (same producer/0.5-deg grid) and carries T, precip,
SW, tmax/tmin (-> diurnal range), specific humidity, wind speed, surface pressure
and wet-day counts -- a complete, internally-consistent single source.

OUTPUT COLUMN ORDER (must match imogen_lpjg.f::READ at lines 714-718 +
climatemodel.cpp:625-627):

    lon lat  T  RH15M  U-wind  V-wind  LW  SW  DTEMP  RAINFALL  SNOWFALL  PSTAR  fWet
    [1] [2] [3]  [4]    [5]     [6]    [7] [8]  [9]      [10]      [11]    [12]   [13]

MAPPING (CRU-JRA v2.4 monmean -> column):
    T      (K)            <- tmp                                  -> col 3
    RH15M  (%)           <- Tetens(spfh, tmp, pres), clip [0,100] -> col 4
    U-wind (m/s)          <- wind / sqrt(2)  (speed split; CAVEAT-B) -> col 5
    V-wind (m/s)          <- wind / sqrt(2)                        -> col 6
    LW     (W/m^2)        <- 0.0 (CRU-JRA v2.4 has no dlwrf; LW is engine-internal,
                                  NOT ingested by LPJ-GUESS; kept 0 as in legacy) -> col 7
    SW     (W/m^2)        <- dswrf                                 -> col 8
    DTEMP  (K)            <- tmax(daymax.monmean) - tmin(daymin.monmean), clip >=0 -> col 9
    RAIN   (mm/day)       <- pre (kg m-2 = mm/day, monthly-mean daily rate) -> col 10
    SNOW   (mm/day)       <- 0.0 (total precip carried in RAIN; engine sums them) -> col 11
    PSTAR  (hPa)          <- pres / 100                            -> col 12
    fWet   (fraction)     <- pre pd0.1 monsum (wet-day count) / days_in_month -> col 13

Cell ordering + lon/lat are taken VERBATIM from data/gridlist/patterns_gridlist.txt
(1631 cells, lon in 0..360), which is byte-order-identical to the legacy CRUNCEP
files and to the GCM pattern files, so engine index L pairing is preserved.

Regrid: each 0.5-deg source cell whose centre falls within +/-1.875 deg lon and
+/-1.25 deg lat of a HadCM3 cell centre (the 3.75x2.5 cell footprint) is
area-equally averaged over the VALID (land/unmasked) cells; if a HadCM3 cell has
no valid source cell in its footprint, the nearest valid source cell is used.

USAGE
    python tools/crujra_to_imogen_baseline.py \
        --crujra-dir /bg/data/lpj/LPJ-GUESS/input/crujra \
        --gridlist   data/gridlist/patterns_gridlist.txt \
        --output     imogen/CRUNCEP_1960_1989 \
        [--year0 1960 --year1 1989] [--version v2.4]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

try:
    import netCDF4 as nc
except ImportError:
    print("ERROR: netCDF4 not installed. Activate the conda env.", file=sys.stderr)
    sys.exit(1)

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # 365-day calendar

# HadCM3 cell half-footprint for the area average (3.75 lon x 2.5 lat)
HALF_LON = 1.875
HALF_LAT = 1.25

# Header bbox (matches the GCM pattern files + legacy CRUNCEP)
HEADER = "  0.00  -60.00  360.00   90.00"

# CRU-JRA v2.4 file templates (relative to --crujra-dir)
TPL = {
    "tmp":  "crujra.{v}.5d.tmp.1901-2022.365d.noc.monmean.chunked_rew.nc",
    "spfh": "crujra.{v}.5d.spfh.1901-2022.365d.noc.monmean.chunked_rew.nc",
    "pres": "crujra.{v}.5d.pres.1901-2022.365d.noc.monmean.chunked_rew.nc",
    "wind": "crujra.{v}.5d.wind.1901-2022.365d.noc.monmean.chunked_rew.nc",
    "dswrf": "crujra.{v}.5d.dswrf.1901-2022.365d.noc.monmean.chunked_rew.nc",
    "tmax": "crujra.{v}.5d.tmax.1901-2022.365d.noc.daymax.monmean.chunked_rew.nc",
    "tmin": "crujra.{v}.5d.tmin.1901-2022.365d.noc.daymin.monmean.chunked_rew.nc",
    "pre":  "crujra.{v}.5d.pre.1901-2022.365d.noc.monmean.chunked_rew.nc",
    "pd":   "crujra.{v}.5d.pre.1901-2022.365d.noc.pd0.1.monsum.chunked_rew.nc",
}
VARNAME = {  # the data variable inside each file
    "tmp": "tmp", "spfh": "spfh", "pres": "pres", "wind": "wind",
    "dswrf": "dswrf", "tmax": "tmax", "tmin": "tmin", "pre": "pre",
    "pd": "precipitation_days_index_per_time_period",
}
CRUJRA_T0_YEAR = 1901  # time = months since 1901-01


def read_gridlist(path):
    cells = []
    with open(path) as f:
        for line in f:
            p = line.split()
            if len(p) >= 2:
                cells.append((float(p[0]), float(p[1])))
    arr = np.asarray(cells)  # (N,2) lon(0..360), lat
    if len(arr) != 1631:
        print(f"WARN: gridlist has {len(arr)} cells (expected 1631).", file=sys.stderr)
    return arr


def tetens_rh(q, t_k, p_pa):
    """Relative humidity (%) from specific humidity, temperature, pressure."""
    e = q * p_pa / (0.622 + 0.378 * q)                       # vapour pressure (Pa)
    es = 611.2 * np.exp(17.67 * (t_k - 273.15) / (t_k - 29.65))  # sat. vp (Pa, Bolton)
    rh = 100.0 * e / es
    return np.clip(rh, 0.0, 100.0)


def build_cell_index(glon, glat, src_lat, src_lon):
    """For each gridlist cell, return flat indices of source cells in its footprint
    (and a nearest-cell fallback flat index). src_lon normalised to 0..360."""
    nlat, nlon = src_lat.size, src_lon.size
    # source cell-centre meshes (flattened)
    LON, LAT = np.meshgrid(src_lon, src_lat)  # (nlat,nlon)
    LONf = LON.ravel()
    LATf = LAT.ravel()
    box_idx = []
    near_idx = np.empty(len(glon), dtype=np.int64)
    for k in range(len(glon)):
        dlat = LATf - glat[k]
        dlon = LONf - glon[k]
        dlon = (dlon + 180.0) % 360.0 - 180.0  # wrap to [-180,180]
        inbox = (np.abs(dlat) <= HALF_LAT) & (np.abs(dlon) <= HALF_LON)
        box_idx.append(np.nonzero(inbox)[0])
        # nearest (angular) cell as fallback
        d2 = dlat * dlat + (dlon * np.cos(np.deg2rad(glat[k]))) ** 2
        near_idx[k] = int(np.argmin(d2))
    return box_idx, near_idx


def slice_at(ds, varname, tidx):
    """Return the (nlat*nlon,) flattened masked field at time tidx."""
    a = ds.variables[varname][tidx]            # (nlat,nlon) masked array
    a = np.ma.masked_invalid(a)
    return a.ravel()


def regrid_flat(flat_vals, box_idx, near_idx):
    """Area-equal mean over valid source cells in each footprint; nearest fallback."""
    out = np.empty(len(box_idx))
    valid = ~np.ma.getmaskarray(flat_vals)
    data = np.ma.getdata(flat_vals)
    for k, idx in enumerate(box_idx):
        if idx.size:
            v = valid[idx]
            if v.any():
                out[k] = data[idx][v].mean()
                continue
        # fallback: nearest valid cell, else expand-search not needed (rare)
        ni = near_idx[k]
        out[k] = data[ni] if valid[ni] else 0.0
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crujra-dir", type=Path, required=True)
    ap.add_argument("--gridlist", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--year0", type=int, default=1960)
    ap.add_argument("--year1", type=int, default=1989)
    ap.add_argument("--version", default="v2.4")
    ap.add_argument("--limit-months", type=int, default=0,
                    help="debug: only write the first N (month,year) slices")
    args = ap.parse_args(argv)

    grid = read_gridlist(args.gridlist)
    glon, glat = grid[:, 0], grid[:, 1]
    ncell = len(grid)
    args.output.mkdir(parents=True, exist_ok=True)

    # open all source datasets
    ds = {}
    for key, tpl in TPL.items():
        fp = args.crujra_dir / tpl.format(v=args.version)
        if not fp.is_file():
            print(f"FATAL: missing {fp}", file=sys.stderr); return 2
        ds[key] = nc.Dataset(fp)

    # source grid from tmp (all share the same 0.5-deg grid)
    src_lat = ds["tmp"].variables["lat"][:].astype(float)
    src_lon = ds["tmp"].variables["lon"][:].astype(float)
    src_lon = np.where(src_lon < 0, src_lon + 360.0, src_lon)  # -> 0..360

    print(f"[1] gridlist {ncell} cells; source grid {src_lat.size}x{src_lon.size}; "
          f"building footprint index ...", file=sys.stderr)
    box_idx, near_idx = build_cell_index(glon, glat, src_lat, src_lon)

    nslice = 0
    for off, year in enumerate(range(args.year0, args.year1 + 1), start=1):
        for m in range(12):
            tidx = (year - CRUJRA_T0_YEAR) * 12 + m
            tmp = regrid_flat(slice_at(ds["tmp"], VARNAME["tmp"], tidx), box_idx, near_idx)
            spfh = regrid_flat(slice_at(ds["spfh"], VARNAME["spfh"], tidx), box_idx, near_idx)
            pres = regrid_flat(slice_at(ds["pres"], VARNAME["pres"], tidx), box_idx, near_idx)
            wind = regrid_flat(slice_at(ds["wind"], VARNAME["wind"], tidx), box_idx, near_idx)
            dswrf = regrid_flat(slice_at(ds["dswrf"], VARNAME["dswrf"], tidx), box_idx, near_idx)
            tmax = regrid_flat(slice_at(ds["tmax"], VARNAME["tmax"], tidx), box_idx, near_idx)
            tmin = regrid_flat(slice_at(ds["tmin"], VARNAME["tmin"], tidx), box_idx, near_idx)
            pre = regrid_flat(slice_at(ds["pre"], VARNAME["pre"], tidx), box_idx, near_idx)
            pdays = regrid_flat(slice_at(ds["pd"], VARNAME["pd"], tidx), box_idx, near_idx)

            rh = tetens_rh(spfh, tmp, pres)
            uv = wind / np.sqrt(2.0)
            lw = np.zeros(ncell)
            dtemp = np.clip(tmax - tmin, 0.0, None)
            rain = np.clip(pre, 0.0, None)
            snow = np.zeros(ncell)
            pstar_hpa = pres / 100.0
            fwet = np.clip(pdays / DAYS_IN_MONTH[m], 0.0, 1.0)

            out_file = args.output / f"{MONTHS[m]}{off}"
            with open(out_file, "w") as fh:
                fh.write(HEADER + "\n")
                for k in range(ncell):
                    fh.write(
                        f"{glon[k]:8.2f}{glat[k]:8.2f}{tmp[k]:9.2f}{rh[k]:8.2f}"
                        f"{uv[k]:8.3f}{uv[k]:8.3f}{lw[k]:8.2f}{dswrf[k]:9.2f}"
                        f"{dtemp[k]:8.3f}{rain[k]:8.3f}{snow[k]:8.3f}"
                        f"{pstar_hpa[k]:9.2f}{fwet[k]:8.3f}\n"
                    )
            nslice += 1
            if nslice % 24 == 0:
                print(f"    wrote {nslice} files (.. {MONTHS[m]}{off})", file=sys.stderr)
            if args.limit_months and nslice >= args.limit_months:
                print(f"[debug] stopping after {nslice} slices", file=sys.stderr)
                for d in ds.values():
                    d.close()
                return 0

    for d in ds.values():
        d.close()
    print(f"[done] wrote {nslice} ASCII files into {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
