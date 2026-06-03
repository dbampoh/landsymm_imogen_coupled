#!/usr/bin/env python3
"""
Atmospheric GHG-concentration comparison for the LandSyMM GMD paper
(Results §3.2.2, cascade link 2): IMOGEN-derived CO2 / CH4 / N2O global
atmospheric concentrations vs

  (a) historical OBSERVED global annual means (EPA Climate-Indicators series,
      built on NOAA/GML + AGAGE + ice-core records), and
  (b) the SCENARIO prescribed concentrations (CMIP6-SSP / Meinshausen et al.
      2020, or an RCMIP *concentrations* file) -- OPTIONAL, supplied by the
      user via --ref-*-scenario; flagged as "not available locally" otherwise.

----------------------------------------------------------------------------
IMOGEN engine output: CO2.dat column decode (DEFINITIVE)
----------------------------------------------------------------------------
The in-process IMOGEN engine writes one CO2.dat per year at
  <scenario>/Common-directory/IMOGEN/output_62892_cppengine/<year>/CO2.dat
via the writer in forks/trunk_r13078/modules/climatemodel.cpp (lines ~824-826,
nonco2Emissions + full-coupling branch):

    file91 << iyear << " " << co2Ppmv << " " << CONV * cEmissLocal << " "
           << dLandAtmos << " " << dOceanAtmos << " " << co2ChangePpmv << " "
           << ch4Ppbv << " " << n2oPpbv << "\n";

and read back at climatemodel.cpp:521:

    co2File >> yrCo2File >> co2Ppmv >> dump >> dump >> dump
            >> co2ChangePpmv >> ch4Ppbv >> n2oPpbv;

So the 8 whitespace-separated columns are:
    col 1  iyear            : calendar year
    col 2  co2Ppmv          : atmospheric CO2 concentration            [ppm]
    col 3  CONV*cEmissLocal : anthropogenic carbon emissions (CONV=0.471) [Pg C/yr]
    col 4  dLandAtmos       : land -> atmosphere CO2 flux               [ppm/yr]
    col 5  dOceanAtmos      : ocean -> atmosphere CO2 flux              [ppm/yr]
    col 6  co2ChangePpmv    : annual change in CO2                      [ppm/yr]
    col 7  ch4Ppbv          : atmospheric CH4 concentration             [ppb]
    col 8  n2oPpbv          : atmospheric N2O concentration             [ppb]

=> N2O IS present, in COLUMN 8 (n2oPpbv), in ppb. It is seeded at the Law-Dome
   1900 value (IMOGENConfig::N2O_INIT_PPBV ~277 ppb) and evolves via the
   FaIR-style single-box budget fair_non_co2_ghg_budget().

(When the run is configured WITHOUT non-CO2 emissions, CO2.dat has only the
 first 6 columns; this script tolerates 6- or 8-column rows.)

----------------------------------------------------------------------------
N2O CONCENTRATION: forcing-consistent correction (default ON)
----------------------------------------------------------------------------
The raw CO2.dat N2O column (col 8) is the single-box budget by-product driven
by the LAND-ONLY natural N2O source (LPJ-GUESS soil + fire), which omits the
ocean and other non-land natural N2O and therefore runs ~30 ppb low vs the
observed record. The climate, however, was forced by the PRESCRIBED CMIP6
non-CO2 radiative forcing, whose implied N2O includes the full natural source.
The forcing-consistent N2O concentration is therefore the single-box budget
driven by Default_total_Mt (RCMIP anthropogenic + the FAIR-ERF full natural
baseline incl. ocean/non-land) from integrated_emissions_n2o.csv. By default
this script REPLACES the raw CO2.dat N2O column with that forcing-consistent
trajectory (use --no-correct-n2o to score the raw land-only by-product
instead). The CO2 and CH4 columns are always taken as written by the engine.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Paths / configuration
# --------------------------------------------------------------------------
# analysis/ -> comparative_analysis_GMD_paper/ -> Paper_Analysis/ -> scripts/
# -> <repo root> (lpj-guess_imogen_landsymm)
REPO_ROOT = Path(__file__).resolve().parents[4]

DEFAULT_RUNS_ROOT = REPO_ROOT / "forks" / "trunk_r13078_runs"
DEFAULT_REF_DIR = REPO_ROOT / "data" / "concentrations" / "EPA"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "outputs_concentration"

ENGINE_SUBPATH = Path("Common-directory") / "IMOGEN" / "output_62892_cppengine"

SCENARIOS = ["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP4-6.0", "SSP5-8.5"]

# CO2.dat column index (0-based) -> tidy field name
CO2DAT_COLS = {1: "co2_ppm", 6: "ch4_ppb", 7: "n2o_ppb"}

# Gas metadata: tidy key -> (label, unit, EPA ref filename, RMSD threshold)
GASES = {
    "co2_ppm": ("CO$_2$", "ppm", "ghg-concentrations_co2.csv", 10.0),
    "ch4_ppb": ("CH$_4$", "ppb", "ghg-concentrations_ch4.csv", 100.0),
    "n2o_ppb": ("N$_2$O", "ppb", "ghg-concentrations_n2o.csv", 15.0),
}

SCENARIO_COLORS = {
    "SSP1-2.6": "#1d3557",
    "SSP2-4.5": "#2a9d8f",
    "SSP3-7.0": "#e9c46a",
    "SSP4-6.0": "#f4a261",
    "SSP5-8.5": "#e63946",
}

# Year boundaries
HIST_END = 2021          # observed reference (EPA) extends to ~2021
SCENARIO_START = 2015    # CMIP6 SSP scenarios branch from historical in 2015
KEY_YEARS = [2020, 2100]

# --------------------------------------------------------------------------
# Forcing-consistent N2O correction (see module docstring)
# --------------------------------------------------------------------------
# Integrated-emissions table written by intermediary_py component C; the
# "Default_total_Mt" column = RCMIP anthropogenic + FAIR-ERF full natural
# baseline (incl. ocean/non-land), i.e. the natural source implied by the
# prescribed CMIP6 non-CO2 forcing that actually drove the climate.
N2O_EMISS_CSV = (REPO_ROOT / "intermediary_py" / "imogen_ghg_controller" /
                 "outputs" / "component_c" / "data" /
                 "integrated_emissions_n2o.csv")
N2O_EMISS_COL = "Default_total_Mt"

# Single-box N2O budget constants (match the engine's fair_non_co2_ghg_budget
# configuration and the Fig 4c rebuild).
MM_AIR = 28.9647         # g/mol, dry air
MM_N2O = 44.01           # g/mol, N2O
MM_N2 = 2 * 14.0067      # g/mol, N2 (the budget works in N-mass internally)
MA = 5.1352e18           # kg, mass of the atmosphere
N2O_TAU = 121.0          # yr, configured N2O lifetime
N2O_INIT_PPBV = 277.4    # ppb, Law-Dome ~1900 seed


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------
def read_co2dat(path: Path) -> Optional[Dict[str, float]]:
    """Parse a single CO2.dat line; return decoded fields or None."""
    try:
        text = path.read_text().strip()
    except OSError:
        return None
    if not text:
        return None
    parts = text.split()
    try:
        vals = [float(p) for p in parts]
    except ValueError:
        return None
    row: Dict[str, float] = {"year": int(round(vals[0]))}
    for idx, name in CO2DAT_COLS.items():
        row[name] = vals[idx] if idx < len(vals) else np.nan
    return row


def extract_scenario(runs_root: Path, scenario: str,
                     year_min: int, year_max: int) -> pd.DataFrame:
    eng_dir = runs_root / scenario / ENGINE_SUBPATH
    rows: List[Dict[str, float]] = []
    if not eng_dir.is_dir():
        print(f"  [WARN] missing engine dir for {scenario}: {eng_dir}",
              file=sys.stderr)
        return pd.DataFrame(rows)
    for ydir in sorted(p for p in eng_dir.iterdir() if p.is_dir()):
        if not ydir.name.isdigit():
            continue
        year = int(ydir.name)
        if not (year_min <= year <= year_max):
            continue
        rec = read_co2dat(ydir / "CO2.dat")
        if rec is None:
            continue
        rec["scenario"] = scenario
        rows.append(rec)
    df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    return df


def extract_all(runs_root: Path, year_min: int, year_max: int) -> pd.DataFrame:
    frames = []
    for sc in SCENARIOS:
        df = extract_scenario(runs_root, sc, year_min, year_max)
        if not df.empty:
            print(f"  {sc}: {len(df)} years "
                  f"({int(df['year'].min())}-{int(df['year'].max())})")
            frames.append(df)
    if not frames:
        raise RuntimeError("No IMOGEN CO2.dat data found for any scenario.")
    cols = ["scenario", "year", "co2_ppm", "ch4_ppb", "n2o_ppb"]
    return pd.concat(frames, ignore_index=True)[cols]


# --------------------------------------------------------------------------
# Forcing-consistent N2O budget (replaces the land-only CO2.dat by-product)
# --------------------------------------------------------------------------
def _n2o_budget(series: List[tuple]) -> Dict[int, float]:
    """Single-box N2O budget seeded at N2O_INIT_PPBV and stepped over an
    ordered [(year, emission_Mt_N2O), ...] series; returns {year: ppb}.
    Mirrors the engine's fair_non_co2_ghg_budget and the Fig 4c rebuild."""
    out: Dict[int, float] = {}
    c = N2O_INIT_PPBV * 1e-9
    decay = 1.0 - np.exp(-1.0 / N2O_TAU)
    for yr, e in series:
        e_kg_n2 = e * (MM_N2 / MM_N2O) * (1e12 / 1e3)
        c = c + e_kg_n2 / MA * MM_AIR / MM_N2 - c * decay
        out[yr] = c * 1e9
    return out


def corrected_n2o_series(emiss_csv: Path = N2O_EMISS_CSV) -> Dict[str, Dict[int, float]]:
    """Build the forcing-consistent N2O concentration per scenario from the
    Default_total_Mt emissions (RCMIP anthropogenic + full natural baseline)."""
    if not Path(emiss_csv).is_file():
        print(f"  [WARN] N2O emissions table not found, N2O correction "
              f"disabled: {emiss_csv}", file=sys.stderr)
        return {}
    df = pd.read_csv(emiss_csv)
    out: Dict[str, Dict[int, float]] = {}
    for sc in SCENARIOS:
        sub = df[df["Scenario"] == sc].sort_values("Year")
        if sub.empty:
            continue
        series = list(zip(sub["Year"].astype(int), sub[N2O_EMISS_COL].astype(float)))
        out[sc] = _n2o_budget(series)
    return out


def apply_n2o_correction(imogen: pd.DataFrame) -> pd.DataFrame:
    """Overwrite the raw (land-only) n2o_ppb column with the forcing-consistent
    budget. Rows whose year is absent from the budget keep their raw value."""
    corr = corrected_n2o_series()
    if not corr:
        return imogen
    df = imogen.copy()
    df["n2o_ppb"] = [
        corr.get(sc, {}).get(int(yr), raw)
        for sc, yr, raw in zip(df["scenario"], df["year"], df["n2o_ppb"])
    ]
    print("  N2O column replaced with forcing-consistent budget "
          f"(Default_total_Mt; {len(corr)} scenarios).")
    return df


# --------------------------------------------------------------------------
# Reference data (historical observed)
# --------------------------------------------------------------------------
def load_epa_reference(ref_dir: Path, gas_key: str) -> Optional[pd.DataFrame]:
    """Load an EPA 2-column (year,value) historical-concentration series.

    Returns a frame with integer 'year' and 'obs' columns where duplicate
    years are averaged and the series is sorted; None if file is absent.
    """
    fname = GASES[gas_key][2]
    path = ref_dir / fname
    if not path.is_file():
        print(f"  [WARN] EPA reference not found: {path}", file=sys.stderr)
        return None
    raw = pd.read_csv(path, header=None, names=["year", "obs"])
    raw = raw.apply(pd.to_numeric, errors="coerce").dropna()
    raw = raw.groupby("year", as_index=False)["obs"].mean().sort_values("year")
    return raw.reset_index(drop=True)


def interp_reference(ref: pd.DataFrame, years: np.ndarray) -> np.ndarray:
    """Linearly interpolate sparse reference onto integer `years`.

    Values outside the reference coverage are returned as NaN (np.interp would
    otherwise clamp to the endpoints, which would bias the stats).
    """
    xp = ref["year"].values.astype(float)
    fp = ref["obs"].values.astype(float)
    out = np.interp(years.astype(float), xp, fp)
    out[(years < xp.min()) | (years > xp.max())] = np.nan
    return out


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------
def rmsd_bias(model: np.ndarray, ref: np.ndarray) -> Dict[str, float]:
    mask = np.isfinite(model) & np.isfinite(ref)
    n = int(mask.sum())
    if n == 0:
        return {"n": 0, "rmsd": np.nan, "bias": np.nan,
                "mae": np.nan, "max_abs_err": np.nan}
    d = model[mask] - ref[mask]
    return {
        "n": n,
        "rmsd": float(np.sqrt(np.mean(d ** 2))),
        "bias": float(np.mean(d)),
        "mae": float(np.mean(np.abs(d))),
        "max_abs_err": float(np.max(np.abs(d))),
    }


def compute_stats(imogen: pd.DataFrame,
                  refs: Dict[str, Optional[pd.DataFrame]],
                  scenario_refs: Dict[str, Optional[pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for gas_key, (label, unit, _fname, thresh) in GASES.items():
        hist_ref = refs.get(gas_key)
        scen_ref = scenario_refs.get(gas_key)
        for sc in SCENARIOS:
            sub = imogen[imogen["scenario"] == sc].sort_values("year")
            if sub.empty:
                continue
            years = sub["year"].values
            model = sub[gas_key].values

            # --- (a) historical overlap vs observed ---
            for period, lo, hi, ref_df, ref_name in [
                ("historical", -np.inf, HIST_END, hist_ref, "EPA-observed"),
                ("scenario", SCENARIO_START, np.inf, scen_ref, "CMIP6/RCMIP-prescribed"),
            ]:
                pmask = (years >= lo) & (years <= hi)
                if ref_df is None:
                    rows.append({
                        "gas": label.replace("$", ""), "unit": unit,
                        "scenario": sc, "period": period,
                        "reference": ref_name + " (NOT AVAILABLE LOCALLY)",
                        "n": 0, "rmsd": np.nan, "bias": np.nan,
                        "mae": np.nan, "max_abs_err": np.nan,
                        "rmsd_threshold": thresh, "pass": "",
                    })
                    continue
                ry = years[pmask]
                rmodel = model[pmask]
                rref = interp_reference(ref_df, ry)
                st = rmsd_bias(rmodel, rref)
                passed = ("PASS" if (np.isfinite(st["rmsd"]) and st["rmsd"] <= thresh)
                          else ("FAIL" if np.isfinite(st["rmsd"]) else ""))
                rows.append({
                    "gas": label.replace("$", ""), "unit": unit,
                    "scenario": sc, "period": period,
                    "reference": ref_name, **st,
                    "rmsd_threshold": thresh, "pass": passed,
                })
    return pd.DataFrame(rows)


def headline_table(imogen: pd.DataFrame,
                   refs: Dict[str, Optional[pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for gas_key, (label, unit, _f, _t) in GASES.items():
        hist_ref = refs.get(gas_key)
        for sc in SCENARIOS:
            sub = imogen[imogen["scenario"] == sc]
            for yr in KEY_YEARS:
                cell = sub[sub["year"] == yr]
                if cell.empty:
                    continue
                mval = float(cell[gas_key].iloc[0])
                oval = np.nan
                if hist_ref is not None and yr <= HIST_END:
                    oval = float(interp_reference(hist_ref, np.array([yr]))[0])
                rows.append({
                    "gas": label.replace("$", ""), "unit": unit,
                    "scenario": sc, "year": yr,
                    "imogen": round(mval, 3),
                    "observed": (round(oval, 3) if np.isfinite(oval) else np.nan),
                    "bias": (round(mval - oval, 3) if np.isfinite(oval) else np.nan),
                })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Plotting
# --------------------------------------------------------------------------
def plot_trend_overlay(imogen: pd.DataFrame,
                       refs: Dict[str, Optional[pd.DataFrame]],
                       output_dir: Path) -> List[Path]:
    paths = []
    for i, (gas_key, (label, unit, _f, _t)) in enumerate(GASES.items(), start=1):
        fig, ax = plt.subplots(figsize=(10, 5))
        hist_done = False
        for sc in SCENARIOS:
            sub = imogen[imogen["scenario"] == sc].sort_values("year")
            if sub.empty:
                continue
            if not hist_done:
                h = sub[sub["year"] <= SCENARIO_START]
                ax.plot(h["year"], h[gas_key], color="0.25", linewidth=1.6,
                        label="IMOGEN (shared historical)")
                hist_done = True
            f = sub[sub["year"] >= SCENARIO_START]
            ax.plot(f["year"], f[gas_key], label=f"IMOGEN {sc}",
                    color=SCENARIO_COLORS[sc], linewidth=1.4)
        ref = refs.get(gas_key)
        if ref is not None:
            rmask = ref["year"] <= HIST_END
            ax.plot(ref.loc[rmask, "year"], ref.loc[rmask, "obs"],
                    "k.", markersize=4, label="Observed (EPA/NOAA)")
            ax.plot(ref.loc[rmask, "year"], ref.loc[rmask, "obs"],
                    "k-", linewidth=0.8, alpha=0.5)
        ax.axvline(SCENARIO_START, color="grey", linestyle=":", linewidth=0.8)
        ax.set_xlabel("Year")
        ax.set_ylabel(f"{label} ({unit})")
        ax.set_title(f"Atmospheric {label}: IMOGEN vs observed")
        ax.legend(fontsize=8, ncol=2)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        p = output_dir / f"fig0{i}_{gas_key}_trend_overlay.png"
        fig.savefig(str(p), dpi=160)
        plt.close(fig)
        paths.append(p)
    return paths


def plot_hist_bias(imogen: pd.DataFrame,
                   refs: Dict[str, Optional[pd.DataFrame]],
                   output_dir: Path) -> Optional[Path]:
    gas_keys = [g for g in GASES if refs.get(g) is not None]
    if not gas_keys:
        return None
    fig, axes = plt.subplots(len(gas_keys), 1,
                             figsize=(10, 3.2 * len(gas_keys)), sharex=True)
    if len(gas_keys) == 1:
        axes = [axes]
    for ax, gas_key in zip(axes, gas_keys):
        label, unit, _f, thresh = GASES[gas_key]
        ref = refs[gas_key]
        for sc in SCENARIOS:
            sub = imogen[(imogen["scenario"] == sc) &
                         (imogen["year"] <= HIST_END)].sort_values("year")
            if sub.empty:
                continue
            yrs = sub["year"].values
            bias = sub[gas_key].values - interp_reference(ref, yrs)
            ax.plot(yrs, bias, color=SCENARIO_COLORS[sc],
                    linewidth=1.2, label=sc)
        ax.axhline(0, color="k", linewidth=0.8)
        ax.axhspan(-thresh, thresh, color="green", alpha=0.10,
                   label=f"|bias| <= {thresh:g} {unit}")
        ax.set_ylabel(f"{label} bias\n({unit})")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, ncol=3)
    axes[-1].set_xlabel("Year")
    fig.suptitle("IMOGEN - observed concentration bias (historical overlap)",
                 fontsize=12)
    fig.tight_layout()
    p = output_dir / "fig04_historical_bias.png"
    fig.savefig(str(p), dpi=160)
    plt.close(fig)
    return p


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------
def run(runs_root: Path, ref_dir: Path, output_dir: Path,
        year_min: int, year_max: int,
        scenario_ref_paths: Dict[str, Optional[Path]],
        correct_n2o: bool = True) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Extracting IMOGEN concentrations from CO2.dat ...")
    imogen = extract_all(runs_root, year_min, year_max)
    if correct_n2o:
        print("Applying forcing-consistent N2O correction ...")
        imogen = apply_n2o_correction(imogen)
    imogen.to_csv(output_dir / "imogen_concentrations.csv", index=False)

    print("Loading historical (observed) reference series ...")
    refs = {g: load_epa_reference(ref_dir, g) for g in GASES}

    scenario_refs: Dict[str, Optional[pd.DataFrame]] = {g: None for g in GASES}
    for g, p in scenario_ref_paths.items():
        if p is not None and Path(p).is_file():
            df = pd.read_csv(p)
            scenario_refs[g] = df  # expected columns: year, obs (per-gas)

    stats = compute_stats(imogen, refs, scenario_refs)
    stats.to_csv(output_dir / "concentration_stats.csv", index=False)

    headline = headline_table(imogen, refs)
    headline.to_csv(output_dir / "headline_values.csv", index=False)

    fig_paths = plot_trend_overlay(imogen, refs, output_dir)
    bias_fig = plot_hist_bias(imogen, refs, output_dir)
    if bias_fig is not None:
        fig_paths.append(bias_fig)

    meta = {
        "repo_root": str(REPO_ROOT),
        "runs_root": str(runs_root),
        "scenarios": SCENARIOS,
        "year_range_requested": [year_min, year_max],
        "co2dat_column_decode": {
            "col1": "year",
            "col2": "co2Ppmv [ppm]",
            "col3": "CONV*cEmissLocal anthropogenic C emissions [PgC/yr] (CONV=0.471)",
            "col4": "dLandAtmos land->atm CO2 flux [ppm/yr]",
            "col5": "dOceanAtmos ocean->atm CO2 flux [ppm/yr]",
            "col6": "co2ChangePpmv annual CO2 change [ppm/yr]",
            "col7": "ch4Ppbv [ppb]",
            "col8": "n2oPpbv [ppb]",
        },
        "historical_reference": {
            g: (str(ref_dir / GASES[g][2]) if refs[g] is not None
                else "NOT AVAILABLE")
            for g in GASES
        },
        "scenario_reference": {
            g: (str(scenario_ref_paths[g]) if scenario_refs[g] is not None
                else "NOT AVAILABLE LOCALLY (supply CMIP6-SSP / RCMIP "
                     "concentrations via --ref-*-scenario)")
            for g in GASES
        },
        "thresholds": {g: GASES[g][3] for g in GASES},
        "notes": "RMSD/bias use observed series linearly interpolated onto "
                 "IMOGEN integer years within EPA coverage; values outside "
                 "coverage are excluded.",
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(meta, indent=2))

    print(f"\nWrote outputs to: {output_dir}")
    print("\n=== Headline values (key years) ===")
    print(headline.to_string(index=False))
    print("\n=== RMSD / bias vs reference ===")
    print(stats.to_string(index=False))


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    p.add_argument("--ref-dir", type=Path, default=DEFAULT_REF_DIR,
                   help="dir with EPA ghg-concentrations_{co2,ch4,n2o}.csv")
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--year-min", type=int, default=1900)
    p.add_argument("--year-max", type=int, default=2100)
    p.add_argument("--ref-co2-scenario", type=Path, default=None,
                   help="optional prescribed CO2 concentrations CSV (year,obs)")
    p.add_argument("--ref-ch4-scenario", type=Path, default=None)
    p.add_argument("--ref-n2o-scenario", type=Path, default=None)
    p.add_argument("--no-correct-n2o", dest="correct_n2o",
                   action="store_false",
                   help="score the raw land-only CO2.dat N2O by-product "
                        "instead of the forcing-consistent budget (default: "
                        "apply the correction)")
    p.set_defaults(correct_n2o=True)
    return p.parse_args()


def main():
    args = parse_args()
    run(
        runs_root=args.runs_root,
        ref_dir=args.ref_dir,
        output_dir=args.output_dir,
        year_min=args.year_min,
        year_max=args.year_max,
        scenario_ref_paths={
            "co2_ppm": args.ref_co2_scenario,
            "ch4_ppb": args.ref_ch4_scenario,
            "n2o_ppb": args.ref_n2o_scenario,
        },
        correct_n2o=args.correct_n2o,
    )


if __name__ == "__main__":
    main()
