#!/usr/bin/env python3
"""
scripts/clamp_sw_anom_nonneg.py
===============================
Sixth v1.0 climate correction (2026-06-07): floor SHORTWAVE insolation at 0 in
the already-generated delta-B-variant climate library.

PROVENANCE (investigated 2026-06-07): the IMOGEN field reconstruction floors
precip, RH, diurnal range and wind to physical minima but NOT shortwave. This is
an ORIGINAL-Fortran characteristic (imogen_lpjg.f::CLIM_CALC, SW_DAILY line has
no MAX(...,0.0) while its siblings do) faithfully reproduced by the verbatim C++
port (climatemodel.cpp); it is NOT a regression from the oceanfix. It was latent
under the legacy CRUNCEP baseline (SW never went negative) and is exposed by the
corrected CRU-JRA baseline (near-zero polar-winter insolation) + a negative SW
pattern anomaly, yielding tiny negative absolute SW (min ~ -0.275 W/m^2, ~1% of
cell-months, Dec/Jan/Nov/Feb) that LPJ-GUESS's interp_monthly_means_conserve
hard-rejects. The engine source is now floored (both forks + Fortran); this clamp
brings the existing library into parity (numerically IDENTICAL to re-running with
the floor, since the per-month field is day-invariant: flooring output == flooring
reconstruction). Mean-rsds effect <= 0.0011 W/m^2 -> paper/ecosystem unaffected.

SCOPE: SW_anom.dat only (P/W/WET/T/Tmax/Tmin/DTEMP/Rh verified >= 0). Value
columns (>= index 2) only; lon/lat (cols 0-1, legitimately negative) untouched.
Surgical, format-preserving: each negative value token is replaced by zero of
identical character width, so every other byte (and all non-negative lines) is
preserved exactly, across both engine (3-dp) and FastRegrid (5-dp) file formats.

BACKUP (Rule #10): a gzipped manifest of every (file, row, col, original_value)
is written before edits -> fully reversible, and far lighter than copying 11.5 GB.

Usage:
    python scripts/clamp_sw_anom_nonneg.py            # dry-run (report only)
    python scripts/clamp_sw_anom_nonneg.py --apply    # write clamp + manifest
"""
import re, sys, glob, os, gzip, json, datetime
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERN = os.path.join(
    ROOT, "forks/trunk_r13078_runs/*_armB_armArepro/Common-directory/IMOGEN/output*/*/SW_anom.dat")
TOKEN = re.compile(r'(\s*)(\S+)')


def fix_line(line: str):
    """Replace negative value tokens (col index >= 2) with 0 of identical width."""
    nl = "\n" if line.endswith("\n") else ""
    parts = TOKEN.findall(line.rstrip("\n"))
    out, changed = [], []
    for i, (ws, tok) in enumerate(parts):
        if i >= 2:
            try:
                v = float(tok)
                if v < 0.0:
                    dec = len(tok.split(".")[1]) if "." in tok else 0
                    tok = format(0.0, f".{dec}f").rjust(len(tok))
                    changed.append((i, v))
            except ValueError:
                pass
        out.append(ws + tok)
    return "".join(out) + nl, changed


def main():
    apply = "--apply" in sys.argv
    files = sorted(glob.glob(PATTERN))
    print(f"matched {len(files)} SW_anom.dat files; mode={'APPLY' if apply else 'DRY-RUN'}", flush=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest = []
    tot_files = tot_neg = 0
    worst = 0.0
    for n, f in enumerate(files, 1):
        a = np.loadtxt(f)
        bad = np.where((a[:, 2:] < 0).any(axis=1))[0]
        if bad.size == 0:
            continue
        worst = min(worst, float(a[:, 2:].min()))
        with open(f) as fh:
            lines = fh.readlines()
        nfile = 0
        rel = os.path.relpath(f, ROOT)
        for r in bad:
            newln, ch = fix_line(lines[r])
            if ch:
                lines[r] = newln
                nfile += len(ch)
                for ci, ov in ch:
                    manifest.append([rel, int(r), int(ci), ov])
        if nfile:
            tot_files += 1
            tot_neg += nfile
            if apply:
                with open(f, "w") as fh:
                    fh.writelines(lines)
        if n % 250 == 0:
            print(f"  ...{n}/{len(files)} files scanned", flush=True)
    print(f"files with negative SW: {tot_files}; total negative value-tokens: {tot_neg}; "
          f"worst min = {worst:.4f} W/m^2", flush=True)
    if apply:
        bak = os.path.join(ROOT, f"forks/trunk_r13078_runs/SW_anom_clamp_manifest_{ts}.json.gz")
        with gzip.open(bak, "wt") as fh:
            json.dump({"note": "original negative SW values clamped to 0; reversible",
                       "ts": ts, "n": len(manifest), "entries": manifest}, fh)
        print(f"APPLIED. reversible manifest -> {bak}", flush=True)
    else:
        print("dry-run only; rerun with --apply to write.", flush=True)


if __name__ == "__main__":
    main()
