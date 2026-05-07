#!/usr/bin/env python3
"""
imogen_inputs_to_lpjg_format.py
================================

Convert the Python Intermediary's wide-format CSV (the canonical RCMIP-
substituted emissions trajectory produced by `intermediary_py/imogen_ghg_controller`)
into the four narrow-format ASCII files the Fortran IMOGEN engine expects:

  imogen_lpjg_flux.txt           (year, NEE_PgC)            -> FILE_LPJG_FLUX
  imogen_lpjg_ch4_n2o_flux.txt   (year, CH4_Tg, N2O_Tg)     -> FILE_LPJG_CH4_N2O_FLUX
  co2_anthro_emissions.txt       (year, CO2_anthro_PgC)     -> FILE_SCEN_EMITS
  ch4_n2o_anthro_emissions.txt   (year, CH4_Tg, N2O_Tg)     -> FILE_CH4_N2O_EMITS

UNIT-CHECKED ADAPTER DISCIPLINE
-------------------------------
Per `EXECUTION_PLAN.md` Decision #11 + section I.D.2, this adapter
embodies the project's units-integrity policy:

  - INPUT (intermediary_py CSV):  Mt-of-gas/yr for ALL 9 numeric columns
    (CH4_*_Mt, N2O_*_Mt, CO2_*_Mt). 1 Mt = 1e12 g (= 1 Tg, identical units).

  - OUTPUT (Fortran-readable ASCII):
    * CH4 / N2O files:  TgCH4/yr  / TgN2O/yr (= MtCH4/yr / MtN2O/yr; pass-through)
    * CO2 files:        PgC/yr (= GtC/yr; converted from MtCO2/yr by /3666.67)

  - CONVERSION CONSTANT for CO2:
        1 PgC = (44/12) PgCO2 = 3666.6667 MtCO2
        => MtCO2 / 3666.6667 = PgC
    Verified at `intermediary_py/imogen_ghg_controller/src/shared/constants.py`
    and matches the Fortran engine's `PARAMETER(CONV=0.471)` ppmv/GtC
    convention at `imogen/code/imogen_lpjg.f:114-116`.

  - SANITY ASSERTIONS at function boundaries (input shape, no NaNs, value
    ranges within scientific plausibility) — see `_validate_input` below.

  - STARTUP BANNER prints the unit-conversion summary so the operator
    sees what's happening.

USAGE
-----
    python tools/imogen_inputs_to_lpjg_format.py \\
        --input  intermediary_py/imogen_ghg_controller/outputs/imogen_inputs/imogen_inputs_SSP1-2.6.csv \\
        --output runs/SSP1-2.6/inputs/

The output directory is auto-created. The adapter writes 4 files
matching the predecessor's format conventions (verified at step 13 of
the unified-codebase rebuild against version_A's static IIASA reference
files in `imogen/emiss/CMIP6/`).

YEAR-RANGE NOTE
---------------
intermediary_py CSV starts at 1900 (the earliest year for which FAOSTAT
+ scenarios have coverage). The Fortran engine's predecessor reference
files at `imogen/emiss/CMIP6/Co2/co2_pg_emissions_*_1850_2100.txt`
start at 1850 (extending RCMIP back via FAIR baseline). To use this
adapter's outputs in `coupling_mode = prescribed` mode:

  1. Update `runs/<SSP>/imogen_intermediary.ins`:
        FILE_SCEN_EMITS      "<output_dir>/co2_anthro_emissions.txt"
        FILE_CH4_N2O_EMITS   "<output_dir>/ch4_n2o_anthro_emissions.txt"
        FILE_LPJG_FLUX       "<output_dir>/imogen_lpjg_flux.txt"
        FILE_LPJG_CH4_N2O_FLUX  "<output_dir>/imogen_lpjg_ch4_n2o_flux.txt"

  2. Update year-range parameters to match intermediary_py's coverage:
        NYR_EMISS             201      (was 251; 1900-2100 vs 1850-2100)
        NYR_LPJG_FLUX         201      (was 251)
        YEAR1                 1900     (was 1850 in predecessor; or 1871 in our smoke)

  3. Re-run the smoke test in coupling_mode = prescribed; verify the
     engine reads the new files cleanly without "data does not match
     run" errors.

The `--pad-to-year` option (default OFF) lets the adapter prepend
zero-valued rows for pre-1900 years if the user prefers to keep the
.ins file's year range unchanged. NOT scientifically recommended
(zero CH4 anthro for 1850 is wrong; pre-industrial CH4 anthro
~22 TgCH4/yr) but offered as a compatibility shim.

- Daniel Bampoh, 2026-05-07 (step 13 of unified-codebase rebuild)
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np


# =============================================================================
# UNIT CONVERSION CONSTANTS (per EXECUTION_PLAN.md section I.D.2)
# =============================================================================

#: 1 PgC = (44 g_CO2 / 12 g_C) * 1000 (Mt/Pg) = 3666.67 MtCO2 (gas mass)
PgC_TO_MtCO2 = (44.0 / 12.0) * 1000.0
MtCO2_TO_PgC = 1.0 / PgC_TO_MtCO2  # = 2.7273e-4

# Mt = Tg = 1e12 g (identical SI units; only naming differs)
# Both intermediary_py outputs (Mt-of-gas/yr) and Fortran engine inputs
# (TgCH4/yr, TgN2O/yr) are equivalent — pass-through, no conversion.

# =============================================================================
# COLUMN SCHEMA (the canonical intermediary_py output schema)
# =============================================================================

EXPECTED_COLS = (
    "Year",
    "CH4_anthro_Mt",   "CH4_natural_Mt", "CH4_total_Mt",
    "N2O_anthro_Mt",   "N2O_natural_Mt", "N2O_total_Mt",
    "CO2_EFOS_Mt",     "CO2_NEE_Mt",     "CO2_total_Mt",
)

# Sanity ranges (Mt-of-gas/yr) for empirical bounds-checking. Generous
# by design — these are sanity checks, not scientific bounds. Failure
# = adapter aborts with a clear message.
SANITY_RANGES = {
    "CH4_anthro_Mt":   (0.0,  1000.0),   # pre-industrial ~20; modern ~360
    "CH4_natural_Mt":  (0.0,  1000.0),   # pre-industrial ~150; modern ~250
    "CH4_total_Mt":    (0.0,  2000.0),
    "N2O_anthro_Mt":   (0.0,  100.0),    # pre-industrial ~0.5; modern ~6
    "N2O_natural_Mt":  (0.0,  100.0),    # pre-industrial ~10; modern ~10-12
    "N2O_total_Mt":    (0.0,  200.0),
    # CO2_EFOS_Mt can be NEGATIVE in deep-mitigation scenarios with
    # negative-emissions technologies (BECCS, DACCS) in late 21st century;
    # SSP1-2.6 in particular can dip to ~-6 GtCO2/yr by 2080-2100
    # per RCMIP. Allow generous range. - DKB step 13 of unified rebuild
    "CO2_EFOS_Mt":   (-50000.0,  100000.0), # pre-ind 0; modern ~37000; SSP1-2.6 future may be neg
    "CO2_NEE_Mt":    (-50000.0,  50000.0),  # NEE can be either sign
    "CO2_total_Mt":  (-50000.0, 100000.0),
}


# =============================================================================
# VALIDATION
# =============================================================================

def _validate_input(df: pd.DataFrame, *, input_path: Path) -> None:
    """Sanity-check the intermediary_py output CSV before conversion.

    Aborts with sys.exit on any failure. All checks are MANDATORY —
    we'd rather the adapter fail loudly than write bad data into the
    Fortran engine's input pipeline.
    """
    # 1. Schema
    missing = set(EXPECTED_COLS) - set(df.columns)
    if missing:
        sys.exit(
            f"[adapter] FAIL: input CSV {input_path} is missing columns: {missing}\n"
            f"[adapter]       expected schema: {EXPECTED_COLS}\n"
            f"[adapter]       got: {tuple(df.columns)}\n"
            f"[adapter]       (was the CSV generated by a different intermediary_py version?)"
        )

    # 2. No NaNs
    nan_counts = df[list(EXPECTED_COLS)].isna().sum()
    if nan_counts.any():
        sys.exit(
            f"[adapter] FAIL: input CSV {input_path} has NaN values:\n"
            f"{nan_counts[nan_counts > 0]}"
        )

    # 3. Year column is integer-valued, monotonically increasing
    if not pd.api.types.is_numeric_dtype(df["Year"]):
        sys.exit(f"[adapter] FAIL: 'Year' column not numeric in {input_path}")
    if not (df["Year"].diff().dropna() == 1).all():
        sys.exit(
            f"[adapter] FAIL: 'Year' column not monotonically increasing by 1 "
            f"in {input_path}; gaps detected"
        )

    # 4. Sanity-range checks (per-column min/max within plausible bounds)
    for col, (lo, hi) in SANITY_RANGES.items():
        cmin, cmax = df[col].min(), df[col].max()
        if cmin < lo or cmax > hi:
            sys.exit(
                f"[adapter] FAIL: column {col!r} value range [{cmin:.3g}, {cmax:.3g}] "
                f"outside sanity bounds [{lo}, {hi}].\n"
                f"[adapter]       (this is a sanity assertion, not a scientific bound; "
                f"if bounds need adjustment, edit SANITY_RANGES in this script)"
            )


# =============================================================================
# WRITERS — one per Fortran-readable file
# =============================================================================

def _write_2col(out_path: Path, year: pd.Series, value: pd.Series) -> None:
    """Write a 2-column ASCII (year, value) — matches predecessor format
    e.g. `co2_pg_emissions_anthropogenic_historical_ssp126_1850_2100.txt`."""
    with open(out_path, "w") as f:
        for y, v in zip(year, value):
            f.write(f"{int(y)} {v:.6f}\n")


def _write_3col(out_path: Path, year: pd.Series,
                col_a: pd.Series, col_b: pd.Series) -> None:
    """Write a 3-column ASCII (year, col_a, col_b) — matches predecessor format
    e.g. `ch4_n2o_annual_historical_anthropogenic_ssp126_1850_2100.txt`."""
    with open(out_path, "w") as f:
        for y, a, b in zip(year, col_a, col_b):
            f.write(f"{int(y)}\t{a:14.6f}\t{b:14.6f}\n")


# =============================================================================
# OPTIONAL: zero-pad pre-data years for YEAR1=1850 compatibility
# =============================================================================

def _zero_pad(df: pd.DataFrame, target_start: int) -> pd.DataFrame:
    """Prepend rows with year=target_start..first_year-1, all-zero values.

    Per EXECUTION_PLAN.md section I.D.2: this is a compatibility shim,
    NOT a scientifically defensible extension. Zero CH4 anthro for 1850
    is wrong (pre-industrial ~22 TgCH4/yr) but mathematically explicit;
    users opt into this knowing the limitation.
    """
    actual_start = int(df["Year"].iloc[0])
    if target_start >= actual_start:
        return df
    pad_years = list(range(target_start, actual_start))
    pad_data = {col: [0.0] * len(pad_years) for col in EXPECTED_COLS}
    pad_data["Year"] = pad_years
    pad_df = pd.DataFrame(pad_data, columns=list(EXPECTED_COLS))
    return pd.concat([pad_df, df], ignore_index=True)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description=__doc__.strip().split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i", required=True, type=Path,
        help="Path to intermediary_py output CSV "
             "(e.g. intermediary_py/imogen_ghg_controller/outputs/imogen_inputs/imogen_inputs_SSP1-2.6.csv)",
    )
    parser.add_argument(
        "--output", "-o", required=True, type=Path,
        help="Output directory (will be created if missing); 4 files written there",
    )
    parser.add_argument(
        "--pad-to-year", type=int, default=None, metavar="YYYY",
        help="If set, prepend zero-valued rows from YYYY to the CSV's first year. "
             "Use 1850 to match the predecessor's 1850-2100 file convention. "
             "NOT scientifically defensible (zero CH4 anthro for 1850 is wrong); "
             "compatibility shim only.",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        sys.exit(f"[adapter] FAIL: input CSV not found: {args.input}")

    # ---- Startup banner (units-integrity discipline §I.D.5) ----
    print("=" * 70)
    print("imogen_inputs_to_lpjg_format.py — RCMIP-substituted emissions")
    print("                                    intermediary_py -> Fortran IMOGEN")
    print("=" * 70)
    print(f"  INPUT  : {args.input}")
    print(f"  OUTPUT : {args.output}")
    print()
    print("  UNIT CONVENTIONS (per EXECUTION_PLAN.md section I.D.2):")
    print(f"    intermediary_py CSV cols are in Mt-of-gas/yr (= Tg-of-gas/yr; identical SI)")
    print(f"    CH4 / N2O  pass-through to engine (Mt = Tg)")
    print(f"    CO2 columns / {PgC_TO_MtCO2:.4f} -> PgC/yr  (= 44/12*1000 MtCO2 per PgC)")
    if args.pad_to_year is not None:
        print(f"  PAD-TO-YEAR : {args.pad_to_year} (zero-padding pre-CSV years; compatibility shim)")
    print("=" * 70)
    print()

    # ---- Load + validate ----
    df = pd.read_csv(args.input)
    _validate_input(df, input_path=args.input)
    if args.pad_to_year is not None:
        df = _zero_pad(df, target_start=args.pad_to_year)

    args.output.mkdir(parents=True, exist_ok=True)

    n = len(df)
    yr_min, yr_max = int(df["Year"].iloc[0]), int(df["Year"].iloc[-1])

    # =========================================================================
    # 1. FILE_LPJG_FLUX  -- (year, NEE_PgC)  -- LPJG natural CO2 flux
    # =========================================================================
    nee_pgc = df["CO2_NEE_Mt"] * MtCO2_TO_PgC
    out1 = args.output / "imogen_lpjg_flux.txt"
    _write_2col(out1, df["Year"], nee_pgc)
    print(f"  ✓ {out1.name:34s} {n:4d} rows  ({yr_min}-{yr_max})  PgC/yr")

    # =========================================================================
    # 2. FILE_LPJG_CH4_N2O_FLUX  -- (year, CH4_Tg, N2O_Tg)  -- LPJG natural
    # =========================================================================
    out2 = args.output / "imogen_lpjg_ch4_n2o_flux.txt"
    _write_3col(out2, df["Year"], df["CH4_natural_Mt"], df["N2O_natural_Mt"])
    print(f"  ✓ {out2.name:34s} {n:4d} rows  ({yr_min}-{yr_max})  Tg/yr (CH4, N2O)")

    # =========================================================================
    # 3. FILE_SCEN_EMITS  -- (year, CO2_anthro_PgC)  -- anthropogenic CO2
    # NB: uses CO2_EFOS_Mt (fossil CO2 only). Land-use anthro CO2 is
    # already inside CO2_NEE_Mt (handled by FILE_LPJG_FLUX above) so we
    # do NOT double-count it here.
    # =========================================================================
    efos_pgc = df["CO2_EFOS_Mt"] * MtCO2_TO_PgC
    out3 = args.output / "co2_anthro_emissions.txt"
    _write_2col(out3, df["Year"], efos_pgc)
    print(f"  ✓ {out3.name:34s} {n:4d} rows  ({yr_min}-{yr_max})  PgC/yr")

    # =========================================================================
    # 4. FILE_CH4_N2O_EMITS  -- (year, CH4_Tg, N2O_Tg)  -- anthropogenic
    # =========================================================================
    out4 = args.output / "ch4_n2o_anthro_emissions.txt"
    _write_3col(out4, df["Year"], df["CH4_anthro_Mt"], df["N2O_anthro_Mt"])
    print(f"  ✓ {out4.name:34s} {n:4d} rows  ({yr_min}-{yr_max})  Tg/yr (CH4, N2O)")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print()
    print("=" * 70)
    print(f"  4 IMOGEN-format files written to {args.output}")
    print(f"  Year range: {yr_min} - {yr_max} ({n} rows each)")
    print()
    print("  NEXT STEP — wire these into your imogen_intermediary.ins file:")
    print(f"    FILE_LPJG_FLUX         \"{out1}\"")
    print(f"    FILE_LPJG_CH4_N2O_FLUX \"{out2}\"")
    print(f"    FILE_SCEN_EMITS        \"{out3}\"")
    print(f"    FILE_CH4_N2O_EMITS     \"{out4}\"")
    print()
    print(f"  AND adjust year-range params if needed:")
    print(f"    NYR_EMISS              {n}")
    print(f"    NYR_LPJG_FLUX          {n}")
    print(f"    NYR_EMISS_NONCO2       {n}")
    print(f"    YEAR1                  {yr_min}")
    print("=" * 70)


if __name__ == "__main__":
    main()
