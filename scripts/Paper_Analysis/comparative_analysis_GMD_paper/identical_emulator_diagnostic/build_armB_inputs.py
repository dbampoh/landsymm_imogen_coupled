#!/usr/bin/env python3
"""
build_armB_inputs.py  --  Identical-emulator diagnostic (path A), Arm B input builder.

Constructs the IMOGEN emission-input sets for the two Arm-B control variants, for the
bracketing scenarios, from the EXISTING comparator columns in
intermediary_py/.../component_c/data/integrated_emissions_{co2,ch4,n2o}.csv.

Arm A (existing coupled run) = integrated:  anthro = Anthro_Mt (Tier-1), natural = Natural_Mt (LPJG).
Arm B variants (NEW control runs):
  opt1 (Default_total comparator)  : anthro = RCMIP_total_Mt,  natural = FAIR_natural_Mt
  opt2 (RCMIP anthro + LPJG natural): anthro = RCMIP_total_Mt,  natural = Natural_Mt (LPJG)

For each (scenario, variant) we emit a CSV in the canonical imogen_inputs schema, then call
the validated adapter (tools/imogen_inputs_to_lpjg_format.py) to write the 4 Fortran-readable
input files into an ISOLATED directory. NOTHING in runs/<SSP>/ or forks/<...>/ is touched.
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
CDATA = ROOT / "intermediary_py/imogen_ghg_controller/outputs/component_c/data"
ADAPTER = ROOT / "tools/imogen_inputs_to_lpjg_format.py"
OUTROOT = Path(__file__).resolve().parent  # the diagnostic dir
CSV_DIR = OUTROOT / "armB_csv"
INPUTS_ROOT = OUTROOT / "armB_inputs"

SCENARIOS = ["SSP1-2.6", "SSP5-8.5"]
VARIANTS = {
    # variant -> (anthro_col, natural_col)
    "opt1": ("RCMIP_total_Mt", "FAIR_natural_Mt"),   # RCMIP anthro + FaIR natural (= Default_total comparator)
    "opt2": ("RCMIP_total_Mt", "Natural_Mt"),        # RCMIP anthro + LPJG natural
}


def load_gas(gas: str, scen: str) -> pd.DataFrame:
    df = pd.read_csv(CDATA / f"integrated_emissions_{gas}.csv")
    df = df[df["Scenario"] == scen].sort_values("Year").reset_index(drop=True)
    return df


def build_csv(scen: str, variant: str) -> Path:
    anthro_col, natural_col = VARIANTS[variant]
    co2 = load_gas("co2", scen)
    ch4 = load_gas("ch4", scen)
    n2o = load_gas("n2o", scen)

    yrs = co2["Year"].astype(int)
    assert (ch4["Year"].astype(int).values == yrs.values).all()
    assert (n2o["Year"].astype(int).values == yrs.values).all()

    out = pd.DataFrame({"Year": yrs})
    # CH4 / N2O: anthro + natural per the variant
    out["CH4_anthro_Mt"] = ch4[anthro_col].values
    out["CH4_natural_Mt"] = ch4[natural_col].values
    out["CH4_total_Mt"] = out["CH4_anthro_Mt"] + out["CH4_natural_Mt"]
    out["N2O_anthro_Mt"] = n2o[anthro_col].values
    out["N2O_natural_Mt"] = n2o[natural_col].values
    out["N2O_total_Mt"] = out["N2O_anthro_Mt"] + out["N2O_natural_Mt"]
    # CO2: EFOS-slot <- anthro col (RCMIP_total); NEE-slot <- natural col
    out["CO2_EFOS_Mt"] = co2[anthro_col].values
    out["CO2_NEE_Mt"] = co2[natural_col].values
    out["CO2_total_Mt"] = out["CO2_EFOS_Mt"] + out["CO2_NEE_Mt"]

    CSV_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = CSV_DIR / f"imogen_inputs_{scen}_{variant}.csv"
    out.to_csv(csv_path, index=False)
    return csv_path


def main() -> int:
    print(f"ROOT      = {ROOT}")
    print(f"comp-c    = {CDATA}")
    for scen in SCENARIOS:
        for variant in VARIANTS:
            csv_path = build_csv(scen, variant)
            out_dir = INPUTS_ROOT / f"{scen}_{variant}"
            print(f"\n=== {scen} / {variant} -> {out_dir} ===")
            rc = subprocess.run(
                [sys.executable, str(ADAPTER), "--input", str(csv_path), "--output", str(out_dir)],
                cwd=str(ROOT),
            ).returncode
            if rc != 0:
                print(f"ADAPTER FAILED for {scen}/{variant} (rc={rc})")
                return rc
    print("\nALL Arm-B input sets built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
