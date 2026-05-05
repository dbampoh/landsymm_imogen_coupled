#!/usr/bin/env python3
"""
tools/cmip6_nc_to_cmip5_ascii.py
================================

Convert IMOGEN CMIP6 NetCDF patterns into CMIP5-style ASCII directories
that the Fortran IMOGEN binary's pattern reader (`GCM_ANLG` in
`imogen_lpjg.f`, the per-month per-cell `READ(51,*) ...` block at lines
3270-3274) consumes directly.

Authoritative column order (from `imogen_lpjg.f::GCM_ANLG`):

    LON  LAT  T  RH15M  U-wind  V-wind  LW  SW  DTEMP_DAY  RAINFALL  SNOWFALL  PSTAR
    [1]  [2]  [3]  [4]   [5]    [6]    [7] [8]  [9]        [10]      [11]     [12]

The `imogen_lpjg.f` reader uses Fortran free-format READ which stops
after consuming the requested 12 fields, so a 13th trailing field is
ignored (the existing CMIP5 reference files include such a trailing
zero column for unknown reasons; we omit it on output).

CMIP6 source variables (from `mri-esm2-0_patterns.nc` and friends; CF-1.7;
8 `_patt` vars on the `(imogen_drive=12, lat=56, lon=96)` grid):

    tl1_patt        (units "1")            -> CMIP5 col 3 (T)
    ql1_patt        (units "K-1")          -> CMIP5 col 4 (RH15M; see CAVEAT-A)
    wind_patt       (units "m.s-1.K-1")    -> split equally to col 5 (U) and col 6 (V) (see CAVEAT-B)
    lwdown_patt     (units "W m-2 K-1")    -> CMIP5 col 7 (LW)
    swdown_patt     (units "W m-2 K-1")    -> CMIP5 col 8 (SW)
    range_tl1_patt  (units "1")            -> CMIP5 col 9 (DTEMP_DAY)
    precip_patt     (units "m-2.kg.s-1.K-1") -> CMIP5 col 10 (RAINFALL); col 11 (SNOWFALL) = 0  (see CAVEAT-C)
    pstar_patt      (units "m-1.kg.s-2.K-1") -> CMIP5 col 12 (PSTAR)

CAVEATS (also recorded in `notes/STEP_5.md` and `notes/FOLLOWUPS.md`):

    A. RH15M conversion. The CMIP5 column 4 in the predecessor framework
       is consumed as a relative-humidity sensitivity (units %/K in the
       Fortran reader's downstream maths). The CMIP6 `ql1_patt` variable
       has units "K-1" which most plausibly means "delta(specific humidity)
       per K of land-mean warming". Whether this maps directly to a
       relative-humidity-sensitivity column in IMOGEN's pattern-scaling
       energy balance depends on the upstream convention chosen by the
       generator (likely PRIME / Mathison 2025). For step 5 we pass
       through `ql1_patt` directly into col 4 with no unit conversion
       and document the open question for confirmation.

    B. U/V wind split. The CMIP6 NetCDF stores only wind-speed magnitude
       (`wind_patt`), not the U/V vector components the CMIP5 ASCII
       format expects (cols 5 and 6). To preserve the wind-magnitude
       contribution to the energy balance, we split equally:
           U_pat = wind_patt / sqrt(2)
           V_pat = wind_patt / sqrt(2)
       This recovers the magnitude (sqrt(U^2+V^2) = wind_patt) but loses
       directional information. Acceptable because IMOGEN's pattern-scaling
       output is later combined into a `WIND_OUT` magnitude in
       `imogen_lpjg.f::DAY_CALC` anyway.

    C. Rainfall vs snowfall. The CMIP6 NetCDF stores only total
       `precip_patt`, not rain/snow split. We put the full pattern
       value into RAINFALL (col 10) and zero into SNOWFALL (col 11).
       The Fortran `GCM_ANLG` then computes
           PRECIP_ANOM = RAINFALL_ANOM + SNOWFALL_ANOM
       so the total precipitation anomaly is preserved. Downstream
       LPJ-GUESS receives the same total, but the rain-vs-snow split
       within IMOGEN's per-day ('DAY_CALC') decomposition will use only
       the temperature-based partition rule, not the upstream CMIP6
       diagnostic (which doesn't exist). Step 9.5 of the rebuild plan
       could revisit this if a finer split matters.

Output layout:

    <output_dir>/{jan,feb,...,dec}                ASCII pattern files
    <output_dir>/../<gcm>_ebm.nml                 Fortran namelist with EBM scalars

The header line of each ASCII file is the bounding box of the TARGET
gridlist (matching the predecessor's CMIP5 ASCII convention:
"  0.00  -60.00  360.00   90.00").

USAGE

  Single GCM:
    python tools/cmip6_nc_to_cmip5_ascii.py \
        --nc imogen/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/mri-esm2-0_patterns.nc \
        --json imogen/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/mri-esm2-0_params.json \
        --gridlist imogen/code/patterns_gridlist.txt \
        --output imogen/patterns/CEN_CMIP6_MOD_MRI-ESM2-0/

  Batch all 5 GCMs:
    python tools/cmip6_nc_to_cmip5_ascii.py \
        --input-dir imogen/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/ \
        --gridlist imogen/code/patterns_gridlist.txt \
        --output-base imogen/patterns/

    (auto-discovers all *_patterns.nc files; pairs each with the
     matching *_params.json by filename prefix; emits to
     <output-base>/CEN_CMIP6_MOD_<UPPERCASED-GCM>/jan,feb,...,dec
     plus <output-base>/<gcm>_ebm.nml)

EXIT CODES
    0  success (all GCMs processed)
    1  bad arguments / missing files
    2  shape / data validation failure (e.g. gridlist lon/lat outside
       source NetCDF lat/lon range)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

try:
    import xarray as xr
except ImportError:
    print("ERROR: xarray not installed. Activate the project conda env, or `pip install xarray netCDF4`.",
          file=sys.stderr)
    sys.exit(1)

try:
    from scipy.interpolate import RegularGridInterpolator
except ImportError:
    print("ERROR: scipy not installed. `pip install scipy` (or activate conda env).", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# Constants
# =============================================================================

MONTH_NAMES = ["jan", "feb", "mar", "apr", "may", "jun",
               "jul", "aug", "sep", "oct", "nov", "dec"]

# Authoritative column order: see module docstring + imogen_lpjg.f:3270-3274
# Each entry is (cmip5_col_index_1based, cmip6_var_name_or_None, transform).
# transform takes the (lat, lon)-shaped numpy array of values and returns
# the value to write into the ASCII column (same shape, scalar transform).
SQRT2 = math.sqrt(2.0)
_HALF_OVER_SQRT2 = 1.0 / SQRT2  # = 0.7071...


def _identity(x): return x
def _wind_split_half(x): return x * _HALF_OVER_SQRT2


# CMIP6 -> CMIP5 column mapping. Order matches output column order.
# A None source variable means write a literal 0.0 in that column.
COLUMN_SPEC = [
    ("T",        3,  "tl1_patt",      _identity),
    ("RH15M",    4,  "ql1_patt",      _identity),
    ("U-wind",   5,  "wind_patt",     _wind_split_half),
    ("V-wind",   6,  "wind_patt",     _wind_split_half),
    ("LW",       7,  "lwdown_patt",   _identity),
    ("SW",       8,  "swdown_patt",   _identity),
    ("DTEMP",    9,  "range_tl1_patt", _identity),
    ("RAIN",    10,  "precip_patt",   _identity),
    ("SNOW",    11,  None,            None),
    ("PSTAR",   12,  "pstar_patt",    _identity),
]

# Predecessor CMIP5 ASCII files use these as the global-bounding-box header
# (top of every <month> file). Verified against
# imogen/patterns/CEN_IPSL_MOD_IPSL-CM5A-MR/jan and others.
_HEADER_BBOX = (0.00, -60.00, 360.00, 90.00)


# =============================================================================
# Helpers
# =============================================================================

def read_gridlist(path: Path) -> np.ndarray:
    """Read patterns_gridlist.txt — 1631-cell IMOGEN HadCM3 land grid.

    Returns an (N, 2) array of [lon, lat] in degrees, with lon in 0..360.
    """
    cells = []
    with open(path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            lon, lat = float(parts[0]), float(parts[1])
            if lon < 0:
                lon += 360.0
            cells.append((lon, lat))
    arr = np.asarray(cells, dtype=np.float64)
    if len(arr) != 1631:
        print(f"WARN: gridlist has {len(arr)} cells; predecessor convention is 1631.",
              file=sys.stderr)
    return arr


def build_interpolator(arr2d: np.ndarray, src_lat: np.ndarray, src_lon: np.ndarray):
    """Return a callable f(target_pts) where target_pts is (N, 2) [lat, lon].

    Bilinear interpolation; out-of-range cells fill with 0.0.
    """
    # If lat is descending, RegularGridInterpolator wants ascending → flip.
    lat = src_lat
    arr = arr2d
    if lat[0] > lat[-1]:
        lat = lat[::-1]
        arr = arr[::-1, :]

    # If lon spans negatives, normalise to 0..360 (IMOGEN convention)
    lon = src_lon.copy()
    if lon.min() < 0.0:
        lon = np.where(lon < 0, lon + 360.0, lon)
        order = np.argsort(lon)
        lon = lon[order]
        arr = arr[:, order]

    return RegularGridInterpolator(
        (lat, lon), arr,
        method="linear", bounds_error=False, fill_value=0.0,
    )


def interpolate_to_grid(ds: "xr.Dataset", var: str, m_idx: int,
                        target_pts: np.ndarray) -> np.ndarray:
    """Bilinear-interpolate ds[var][m_idx, :, :] onto target_pts [(lon,lat)]."""
    arr = ds[var].isel(imogen_drive=m_idx).values  # shape (lat, lon)
    src_lat = ds.lat.values
    src_lon = ds.lon.values
    interp = build_interpolator(arr, src_lat, src_lon)
    pts_lat_lon = np.column_stack([target_pts[:, 1], target_pts[:, 0]])  # [(lat, lon)]
    return interp(pts_lat_lon)


def write_month_ascii(out_path: Path, target_cells: np.ndarray, columns: dict):
    """Write one CMIP5-style ASCII pattern file.

    columns: dict mapping cmip5_col_index -> 1D numpy array of length N (target cells).
    """
    n_cells = target_cells.shape[0]
    # Header: bounding box of the TARGET gridlist (matches predecessor convention)
    header = "{:8.2f}{:8.2f}{:8.2f}{:8.2f}".format(*_HEADER_BBOX)

    with open(out_path, "w") as fh:
        fh.write(header + "\n")
        for i in range(n_cells):
            lon, lat = target_cells[i, 0], target_cells[i, 1]
            fields = ["{:7.2f}".format(lon), "{:7.2f}".format(lat)]
            for col_idx in range(3, 13):  # cols 3..12 inclusive
                v = columns[col_idx][i]
                fields.append("{:9.5f}".format(v))
            fh.write("  ".join(fields) + "\n")


def write_namelist(out_nml: Path, model_name: str, params: dict):
    """Write Fortran namelist of EBM scalars."""
    p = params[model_name]
    with open(out_nml, "w") as fh:
        fh.write("&IMOGEN_EBM\n")
        fh.write(f"  MODEL    = '{model_name}'\n")
        fh.write(f"  KAPPA_O  = {p['kappa_o']:.6f}\n")
        fh.write(f"  LAMBDA_L = {p['lambda_l']:.6f}\n")
        fh.write(f"  LAMBDA_O = {p['lambda_o']:.6f}\n")
        fh.write(f"  MU       = {p['mu']:.6f}\n")
        fh.write(f"  F_OCEAN  = {p['f_ocean']:.6f}\n")
        fh.write("/\n")


# =============================================================================
# Main convert routine for one GCM
# =============================================================================

def convert_one(nc_path: Path, json_path: Path, gridlist_path: Path, out_dir: Path,
                nml_dir: Path | None = None, verbose: bool = True) -> None:
    """Convert one CMIP6 NetCDF + JSON pair to a CMIP5-style ASCII directory."""
    if verbose:
        print(f"--- {nc_path.name} -> {out_dir} ---")

    # 1. Open NetCDF + verify shape
    ds = xr.open_dataset(nc_path)
    expected_dims = {"imogen_drive": 12, "lat": 56, "lon": 96}
    actual_dims = {d: ds.sizes.get(d) for d in expected_dims}
    if actual_dims != expected_dims:
        print(f"WARN: {nc_path.name} dims {actual_dims} (expected {expected_dims}); proceeding.",
              file=sys.stderr)

    # 2. Read target gridlist
    target_cells = read_gridlist(gridlist_path)

    # 3. Read JSON params
    with open(json_path) as f:
        params = json.load(f)
    model_name = list(params.keys())[0]

    # 4. Per-month: interpolate each variable onto target grid; write ASCII
    out_dir.mkdir(parents=True, exist_ok=True)
    for m_idx, mname in enumerate(MONTH_NAMES):
        # Build the dict of {cmip5_col_index -> 1D array of N values}
        columns: dict = {}
        for label, cmip5_col, cmip6_var, transform in COLUMN_SPEC:
            if cmip6_var is None:
                columns[cmip5_col] = np.zeros(len(target_cells))
            else:
                vals = interpolate_to_grid(ds, cmip6_var, m_idx, target_cells)
                columns[cmip5_col] = transform(vals)

        out_file = out_dir / mname
        write_month_ascii(out_file, target_cells, columns)
        if verbose:
            print(f"  wrote {mname} ({len(target_cells)+1} lines)")

    # 5. Namelist with EBM scalars
    if nml_dir is None:
        nml_dir = out_dir.parent
    nml_dir.mkdir(parents=True, exist_ok=True)
    nml_path = nml_dir / f"{model_name}_ebm.nml"
    write_namelist(nml_path, model_name, params)
    if verbose:
        print(f"  wrote {nml_path}")


# =============================================================================
# CLI
# =============================================================================

def _gcm_dir_name(model: str) -> str:
    """Map the JSON model name (e.g. 'MRI-ESM2-0') to a CEN_CMIP6_MOD_<...> dir name."""
    return f"CEN_CMIP6_MOD_{model}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Convert IMOGEN CMIP6 NetCDF patterns to CMIP5-style ASCII",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Either provide --nc + --json + --output for single-GCM mode, OR\n"
            "                --input-dir + --output-base for batch mode (auto-finds all 5).\n"
            "--gridlist is required in both modes."
        ),
    )
    p.add_argument("--nc", type=Path, help="Path to one *_patterns.nc file (single-GCM mode)")
    p.add_argument("--json", type=Path, help="Path to matching *_params.json (single-GCM mode)")
    p.add_argument("--output", type=Path, help="Output dir for ASCII month files (single-GCM mode)")

    p.add_argument("--input-dir", type=Path,
                   help="Directory containing *_patterns.nc + matching *_params.json (batch mode)")
    p.add_argument("--output-base", type=Path,
                   help="Directory under which CEN_CMIP6_MOD_<gcm>/ output dirs are created (batch mode)")

    p.add_argument("--gridlist", type=Path, required=True,
                   help="Path to patterns_gridlist.txt (the 1631-cell IMOGEN HadCM3 land grid)")
    p.add_argument("-q", "--quiet", action="store_true", help="Less verbose output")

    args = p.parse_args(argv)
    verbose = not args.quiet

    # Decide between single and batch mode
    single = args.nc is not None or args.json is not None or args.output is not None
    batch = args.input_dir is not None or args.output_base is not None

    if single and batch:
        print("ERROR: cannot mix --nc/--json/--output with --input-dir/--output-base.", file=sys.stderr)
        return 1

    if not args.gridlist.exists():
        print(f"ERROR: gridlist not found: {args.gridlist}", file=sys.stderr)
        return 1

    if single:
        if not (args.nc and args.json and args.output):
            print("ERROR: single-GCM mode requires --nc, --json, AND --output.", file=sys.stderr)
            return 1
        if not args.nc.exists():
            print(f"ERROR: NetCDF not found: {args.nc}", file=sys.stderr); return 1
        if not args.json.exists():
            print(f"ERROR: JSON params not found: {args.json}", file=sys.stderr); return 1
        convert_one(args.nc, args.json, args.gridlist, args.output, verbose=verbose)
        return 0

    if batch:
        if not (args.input_dir and args.output_base):
            print("ERROR: batch mode requires --input-dir AND --output-base.", file=sys.stderr)
            return 1
        if not args.input_dir.is_dir():
            print(f"ERROR: input dir not found: {args.input_dir}", file=sys.stderr); return 1

        nc_files = sorted(args.input_dir.glob("*_patterns.nc"))
        if not nc_files:
            print(f"ERROR: no *_patterns.nc found in {args.input_dir}", file=sys.stderr)
            return 1

        if verbose:
            print(f"Batch mode: {len(nc_files)} GCMs in {args.input_dir}")

        n_done = 0
        for nc_path in nc_files:
            stem = nc_path.stem.replace("_patterns", "")
            json_path = args.input_dir / f"{stem}_params.json"
            if not json_path.exists():
                print(f"  SKIP: no matching {json_path.name} found.", file=sys.stderr)
                continue
            # Read JSON to discover the model name (preserves case as upstream wrote it)
            with open(json_path) as f:
                params = json.load(f)
            model_name = list(params.keys())[0]
            out_dir = args.output_base / _gcm_dir_name(model_name)
            convert_one(nc_path, json_path, args.gridlist, out_dir,
                        nml_dir=args.output_base, verbose=verbose)
            n_done += 1
        if verbose:
            print(f"Done. Converted {n_done} GCM(s) into {args.output_base}/")
        return 0

    print("ERROR: must specify either single-GCM (--nc/--json/--output) or batch (--input-dir/--output-base) mode.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
