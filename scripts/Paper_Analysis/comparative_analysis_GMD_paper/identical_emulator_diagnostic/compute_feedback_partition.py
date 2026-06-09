#!/usr/bin/env python3
"""
compute_feedback_partition.py -- identical-emulator diagnostic, corrected engine.

Computes the emission-pathway FEEDBACK on the IMOGEN climate as the difference
between the integrated-emission run (Arm A) and the unmodified-RCMIP control
(Arm B), both produced with the SAME corrected (oceanfix + SW-floor) C++ engine,
so the emulator structure cancels and the residual is the emission-pathway signal.

  Arm A (integrated)      = <SSP>_armB_armArepro  (engine-only on Arm A's OWN
                            integrated emissions; this IS the corrected paper
                            climate per notes/PRODUCTION_RUN_CONFIG.md)
  Arm B opt1 (headline)   = <SSP>_armB_opt1       (Default_total = RCMIP+FaIR
                            reference; reproduces Sect. 3.2.1 / Fig. 3)
  Arm B opt2 (sensitivity)= <SSP>_armB_opt2       (RCMIP anthro + LPJ-GUESS
                            natural; isolates the CH4/N2O Tier-1 substitution)

  feedback_opt1 = ArmA - opt1   (full emission-pathway feedback; headline)
  subst_opt2    = ArmA - opt2   (CH4/N2O Tier-1 substitution only)

Area-weighted (cos lat) global-land mean of the annual-mean field, by window.
NB the stored <SSP>/Common-directory/IMOGEN/output is the OBSOLETE buggy-engine
run and is deliberately NOT used here.

Output: diagnostic_partition.csv (scenario, variable, window, ArmA, opt1, opt2,
feedback_opt1, subst_opt2) + a printed summary.
"""
from pathlib import Path
import numpy as np
import csv

ROOT = Path("/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm")
GRIDLIST = ROOT / "data/gridlist/patterns_gridlist.txt"
RUNS = ROOT / "forks/trunk_r13078_runs"
HERE = Path(__file__).resolve().parent

SCENARIOS = ["SSP1-2.6", "SSP5-8.5"]
VARFILE = {"T": "T_anom.dat", "P": "P_anom.dat", "SW": "SW_anom.dat"}
VARUNIT = {"T": "K", "P": "(native)", "SW": "W m-2"}
WINDOWS = {"2015-2020": (2015, 2020), "2040-2060": (2040, 2060), "2080-2100": (2080, 2100)}


def load_weights():
    g = np.loadtxt(GRIDLIST)
    w = np.cos(np.deg2rad(g[:, 1]))
    return w / w.sum()


def annual_global_mean(path, w):
    a = np.loadtxt(path)
    return float(np.dot(w, a[:, 2:14].mean(axis=1)))


def series(output_dir, var, w):
    fn = VARFILE[var]
    out = {}
    for yd in sorted(output_dir.glob("[12]*")):
        if yd.is_dir() and (yd / fn).exists():
            try:
                out[int(yd.name)] = annual_global_mean(yd / fn, w)
            except Exception:
                pass
    return out


def wmean(s, lo, hi):
    vals = [s[y] for y in range(lo, hi + 1) if y in s]
    return float(np.mean(vals)) if vals else float("nan")


def main():
    w = load_weights()
    rows = []
    for ssp in SCENARIOS:
        dA = RUNS / f"{ssp}_armB_armArepro" / "Common-directory/IMOGEN/output"
        d1 = RUNS / f"{ssp}_armB_opt1" / "Common-directory/IMOGEN/output"
        d2 = RUNS / f"{ssp}_armB_opt2" / "Common-directory/IMOGEN/output"
        for var in VARFILE:
            sA, s1, s2 = series(dA, var, w), series(d1, var, w), series(d2, var, w)
            if not (sA and s1 and s2):
                print(f"[skip] {ssp} {var}: missing data (A={len(sA)} o1={len(s1)} o2={len(s2)})")
                continue
            for win, (lo, hi) in WINDOWS.items():
                a, o1, o2 = wmean(sA, lo, hi), wmean(s1, lo, hi), wmean(s2, lo, hi)
                rows.append(dict(scenario=ssp, variable=var, unit=VARUNIT[var], window=win,
                                 ArmA_integrated=round(a, 3), opt1_rcmip=round(o1, 3),
                                 opt2_rcmip_lpjgnat=round(o2, 3),
                                 feedback_opt1=round(a - o1, 3), subst_opt2=round(a - o2, 3)))
    out = HERE / "diagnostic_partition.csv"
    with open(out, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)
    print(f"wrote {out}  ({len(rows)} rows)\n")
    print(f"{'scen':9s} {'var':3s} {'window':10s} {'ArmA':>9s} {'opt1':>9s} {'opt2':>9s} {'fb_opt1':>9s} {'sub_opt2':>9s}")
    for r in rows:
        print(f"{r['scenario']:9s} {r['variable']:3s} {r['window']:10s} "
              f"{r['ArmA_integrated']:9.3f} {r['opt1_rcmip']:9.3f} {r['opt2_rcmip_lpjgnat']:9.3f} "
              f"{r['feedback_opt1']:9.3f} {r['subst_opt2']:9.3f}")


if __name__ == "__main__":
    main()
