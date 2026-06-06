#!/usr/bin/env python3
"""
analyze_partition.py -- Identical-emulator diagnostic (path A): compute the
feedback-vs-emulator-bias partition from the 1631-native IMOGEN engine output.

For each run we read the per-year *_anom.dat fields (1631 cells x 12 monthly values),
take the annual mean per cell, then the cos(lat) area-weighted global-land mean per year.
We then form window means (2015-2020, 2040-2060, 2080-2100) and the differences:

  A   = Arm A (existing coupled run): forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output
  B   = Arm B control:               forks/trunk_r13078_runs/<SSP>_armB_<variant>/.../output
  A-B = the emission-pathway FEEDBACK (identical emulator cancels)

Validation: armArepro (engine-only on Arm A's OWN inputs) must reproduce A (~0 diff).
The emulator-bias term = (A - ISIMIP3b, from Table 12) - (A - B).

Usage:
  analyze_partition.py <SSP> [--variants opt1,opt2,armArepro] [--vars T,P,SW]
"""
import argparse
import math
from pathlib import Path

import numpy as np

ROOT = Path("/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm")
GRIDLIST = ROOT / "data/gridlist/patterns_gridlist.txt"
RUNS = ROOT / "forks/trunk_r13078_runs"

VARFILE = {"T": "T_anom.dat", "P": "P_anom.dat", "SW": "SW_anom.dat"}
VARUNIT = {"T": "K", "P": "(native)", "SW": "W m-2"}
WINDOWS = {"2015-2020": (2015, 2020), "2040-2060": (2040, 2060), "2080-2100": (2080, 2100)}


def load_weights():
    g = np.loadtxt(GRIDLIST)  # cols: lon lat
    lat = g[:, 1]
    w = np.cos(np.deg2rad(lat))
    return w / w.sum()


def annual_global_mean(path: Path, w: np.ndarray) -> float:
    """area-weighted global-land mean of the annual-mean field in one *_anom.dat."""
    a = np.loadtxt(path)            # 1631 x (2 + 12)
    monthly = a[:, 2:14]            # 12 monthly values per cell
    cell_annual = monthly.mean(axis=1)
    return float(np.dot(w, cell_annual))


def series(output_dir: Path, var: str, w: np.ndarray) -> dict:
    fn = VARFILE[var]
    out = {}
    for yd in sorted(output_dir.glob("[12]*")):
        if not yd.is_dir():
            continue
        f = yd / fn
        if f.exists():
            try:
                out[int(yd.name)] = annual_global_mean(f, w)
            except Exception:
                pass
    return out


def window_mean(s: dict, lo: int, hi: int):
    vals = [s[y] for y in range(lo, hi + 1) if y in s]
    return float(np.mean(vals)) if vals else float("nan")


def out_dir(ssp, variant):
    if variant is None:  # Arm A
        return RUNS / ssp / "Common-directory/IMOGEN/output"
    return RUNS / f"{ssp}_armB_{variant}" / "Common-directory/IMOGEN/output"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ssp")
    ap.add_argument("--variants", default="opt1,opt2,armArepro")
    ap.add_argument("--vars", default="T,P,SW")
    args = ap.parse_args()
    w = load_weights()
    variants = args.variants.split(",")
    vars_ = args.vars.split(",")

    A_dir = out_dir(args.ssp, None)
    print(f"\n=== {args.ssp} | Arm A = {A_dir}")
    for var in vars_:
        sA = series(A_dir, var, w)
        if not sA:
            print(f"  [{var}] Arm A: no data yet"); continue
        print(f"\n  [{var}] ({VARUNIT[var]})  window-mean global-land means (n Arm A yrs={len(sA)})")
        header = "    window      " + "ArmA".rjust(10)
        rows = {win: {} for win in WINDOWS}
        for win, (lo, hi) in WINDOWS.items():
            rows[win]["ArmA"] = window_mean(sA, lo, hi)
        for v in variants:
            d = out_dir(args.ssp, v)
            sB = series(d, var, w)
            tag = v
            header += tag.rjust(12) + (f" (A-{tag})").rjust(12)
            for win, (lo, hi) in WINDOWS.items():
                bm = window_mean(sB, lo, hi)
                rows[win][tag] = bm
                rows[win][f"A-{tag}"] = rows[win]["ArmA"] - bm if not math.isnan(bm) else float("nan")
        print(header)
        for win in WINDOWS:
            line = f"    {win:11s} {rows[win]['ArmA']:10.3f}"
            for v in variants:
                line += f"{rows[win].get(v, float('nan')):12.3f}{rows[win].get('A-'+v, float('nan')):12.3f}"
            print(line)
    print("\n  NOTE: A-armArepro should be ~0 (validation). A-opt1 / A-opt2 are the feedback.")


if __name__ == "__main__":
    main()
