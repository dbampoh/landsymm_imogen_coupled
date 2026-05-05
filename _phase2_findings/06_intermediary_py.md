# 06 — Intermediary_py (Python replacement for the C++ Intermediary)

> **Subagent 6 / 8** investigation, read-only. Source of truth: the bundled
> `README.md`, `HANDOFF.md`, `TECHNICAL_MANUAL.md`, `Quick_Start.md`,
> `inputs_README.md`, plus the two extracted source distributions
> (`imogen_ghg_controller_FULL/`, `imogen_ghg_controller_SOURCE_ONLY/`).

> **Path investigated:**
> `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary_py/`

> **Status of the package itself:** `imogen_ghg_controller v0.1.0`,
> MIT-licensed, declared "complete and reorganized into a single shareable
> codebase" (HANDOFF §1, "post-reorganization") and "runnable end-to-end via
> `python run_all.py`". Author calls it the **IMOGEN GHG Controller**.

> **Status w.r.t. the coupled framework:** the package exists as a
> *standalone* pipeline shipped next to the C++ `Intermediary/`. There is **no
> wiring to `Imogen-controller/`, `LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/`,
> `Regrid/`, or `landsymm_imogen_setup/`**. None of the docs mention IMOGEN's
> own input file naming/format spec or how the produced CSVs feed the C++
> emulator (Quick_Start.md line 166: *"please share the IMOGEN code so I can
> determine the input data form/structure/format requirements and figure out
> how the 6 IMOGEN-input CSVs we produce should be transformed for ingestion
> into IMOGEN"*). Substitution is therefore **not yet integration-ready** —
> see §11.

---

## 1. Documentation summary (per `.md` file)

Line counts:

| File | Lines | Size |
|---|---|---|
| `HANDOFF.md` | 1222 | 92 KB |
| `TECHNICAL_MANUAL.md` | 2272 | 111 KB |
| `README.md` | 432 | 25 KB |
| `Quick_Start.md` | 166 | 7.6 KB |
| `inputs_README.md` | 126 | 6.8 KB |

### 1.1 `README.md` (432 lines, ~25 KB)
User-facing entry point. Twelve numbered sections covering: (1) what the
project produces (a wide-format per-scenario IMOGEN-input CSV, schema given);
(2) the four-component pipeline overview (A anthropogenic / B natural / C
integration / D IMOGEN export) with an ASCII diagram; (3) Quick start (`pip
install -r requirements.txt` then `python run_all.py`); (4) repository tree;
(5) inputs to obtain (FAO, PLUMv2, LPJ-GUESS .gz, RCMIP, FAIR-ERF, EDGAR,
optional reference PDFs); (6) outputs catalogue; (7) running individual
components (env-var pattern shown); (8) configuration via env vars
(`IMOGEN_GHG_ROOT`, `OUT_DIR`, `DATA_DIR`, `IN_DIR`, `DATA_DIR_LPJ`,
`DATA_DIR_RCMIP`); (9) reproducibility / `pytest tests/`; (10) headline
scientific findings; (11) MIT licence + citations to GMB/GNB/GCB/IPCC/RCMIP/
FAIR; (12) further reading. Section 5.6 (added in Round 16) documents the
EDGAR files. Section 1's table is the canonical IMOGEN-input schema:
`Year, CH4_anthro_Mt, CH4_natural_Mt, CH4_total_Mt, N2O_anthro_Mt,
N2O_natural_Mt, N2O_total_Mt, CO2_EFOS_Mt, CO2_NEE_Mt, CO2_total_Mt`.

### 1.2 `HANDOFF.md` (1222 lines, ~92 KB)
Chronological technical record across the project's three chat sessions plus
two cleanup rounds. §§1–7 establish Components A/B; §1 declares the project
mission ("annual GHG emission trajectories from 1900 to 2100 for input to
the IMOGEN climate emulator"). §§2 documents the substitution algebra
(`New_total = RCMIP_total − RCMIP_agri + Our_agri`), §3 the LPJ-GUESS
streaming methodology (62 538 cells × 120 yrs, `subprocess.Popen(['zcat',
gz])`), §§5–6 plot conventions (IPCC palette, GMB/GNB/GCB references), §7
iteration history. §8 contains the substantial Component C work: rounds
C1–C8 build `rcmip_co2.csv`, the integrated trajectories, three independent
comparators (external top-down, hybrid Option B with SLAND correction,
conventional Option A), with §8.10 deciding Option B is the primary
comparator and §8.11 consolidating the headline findings. §10 documents
non-trivial computational-environment notes (zcat streaming, network
allowlist that blocked OSCAR / IIASA / ESGF access — §8.7). §14 documents
the codebase reorganization into `imogen_ghg_controller/` (R1 round, MIT
licence, `.gitignore`, four-component layout). §15 is the EDGAR fix round
(89 scripts/files affected: hardcoded paths, broken f-strings, missing
`paths.py` imports, scenario directory inconsistency). §16 is the
reproducibility verification (39/40 reference CSVs and 13/14 reference plots
byte-identical; the single CSV diff is a pandas float-formatting cosmetic
issue, the single plot diff is a deliberate plotting upgrade). HANDOFF.md
is candid about gaps: post-2020 natural baseline still constant in both
Option A and B comparators, multi-ESM / OSCAR comparators inaccessible,
Tier-1-only methodology, no formal uncertainty propagation.

### 1.3 `TECHNICAL_MANUAL.md` (2272 lines, ~111 KB)
The reference document. **Eighteen sections** (full ToC at lines 26–46):
1 Project context and scientific goals; 2 Architecture overview; 3
Repository layout in detail; 4 Installation and first run; 5 The shared
module — what's centralized and why; 6 Component A — anthropogenic
agricultural inventory; 7 Component B — LPJ-GUESS natural emissions; 8
Component C — integration and validation; 9 Component D — IMOGEN export;
10 The pipeline driver `run_all.py`; 11 Inputs catalogue and acquisition;
12 Outputs catalogue; 13 Tests and reproducibility; 14 Troubleshooting
(10 recipes); 15 Known issues and limitations (10 items); 16 Opportunities
for further development (4 categories: easy wins, medium, large,
methodological); 17 Glossary; 18 Bibliography. Documents: the
`HIST_END=2014` boundary; the `_find_project_root()` walk-up algorithm; the
`subprocess.Popen(['zcat',...], bufsize=65536)` streaming pattern; the unit
conversion table for cflux / mch4 / ngases; the GMB IFW (+112 Tg/yr) and
DCC (−23 Tg/yr) constant corrections; the GCB Table 7 SLAND-correction in
Option B; the gas-aware Δ-panel labelling (PgC/yr for CO₂, % for CH₄/N₂O).
§13 lists the three tests (`test_unit_conversions.py`,
`test_co2_option_a_validation.py`, `test_imogen_export_schema.py`) and the
`md5sum` reproducibility recipe. §15 enumerates known limitations (Tier-1
only, no uncertainty propagation, constant IFW/DCC corrections, possible
N₂O double-counting between LPJ soil and Tier-1 indirect, no
`MPLBACKEND=Agg` standardization, missing `__main__` guards in some
scripts). §16 lists concrete extension ideas including parallelization,
NetCDF migration, Tier-2, ensemble of DGVMs, web dashboard, CLI entry
point, Parquet migration, Monte-Carlo uncertainty.

### 1.4 `Quick_Start.md` (166 lines, ~7.6 KB)
Step-by-step Ubuntu workstation setup. Lines 1–16 are AI-generated narrative
about how outputs were verified (39 of 40 byte-identical) — note this
content is essentially commentary the author preserved from the assistant's
verification round. Lines 18–166 are the operational runbook: extract the
`SOURCE_ONLY` tarball, populate `inputs/` per `inputs/README.md` (FAO 3
CSVs, RCMIP, FAIR ERF, EDGAR 4 xlsx, PLUM 3 files including
`Livestock_counts.zip` extracted to .txt, LPJ-GUESS 18 .gz files), create
`.venv` and `pip install -r requirements.txt`, run a Python verification
snippet that reports input presence, then `python run_all.py --dry-run`
(43 steps) → `python run_all.py 2>&1 | tee run_all.log`. Estimated
runtimes: A 10-15 min, B 10-15 min, C ~1 min, D ~2 s. **Documents that
livestock anchor needs 6-8 GB RAM**. Lines 165-166 explicitly request the
IMOGEN code be shared so the author can determine how the 6 produced CSVs
"should be transformed for ingestion into IMOGEN".

### 1.5 `inputs_README.md` (126 lines, ~6.8 KB)
Reproduces the user-facing README inside `inputs/`. Same content as
`README.md` §5, with a per-source acquisition table (FAOSTAT
public-download URL, RCMIP via rcmip.org with SHA-256 expectation, FAIR
bundled with the FAIR climate emulator, PLUMv2 and LPJ-GUESS available
from project modeller). Lists disk-space costs (~2.8 GB total) and provides
a Python verification snippet that prints true/false and counts for each
canonical input path. **Reference PDFs are explicitly not parsed at
runtime** — they're for reviewer convenience.

---

## 2. Source tree map

### 2.1 Top-level common to FULL and SOURCE_ONLY

```
imogen_ghg_controller/
├── README.md             (432 lines)
├── HANDOFF.md            (1222 lines)
├── TECHNICAL_MANUAL.md   (2272 lines)
├── Quick_Start.md        (166 lines, also at parent path)
├── LICENSE               (MIT)
├── pyproject.toml        (setuptools build, src/* packages)
├── requirements.txt      (pandas>=2.0, numpy>=1.24, matplotlib>=3.7, pyarrow>=14.0)
├── run_all.py            (211 lines, four-component orchestrator)
├── src/                  (5366 lines source + 8682 lines Component A = ~14k LOC)
├── tests/                (3 pytest-discoverable files; ~17 KB)
├── docs/                 (6 .md files = 347 lines + figures_gallery/ symlinks)
├── inputs/               (only README.md in SOURCE_ONLY; populated in FULL)
├── outputs/              (only README.md in SOURCE_ONLY; populated in FULL)
└── archive/              (FULL only: 4.3 MB of superseded scripts + handoffs)
```

### 2.2 `src/` Python module map (verified `find` listing)

`src/shared/` (~530 lines) — 5 files, the cross-component "stdlib" of the
package:
- `paths.py` (135) — `_find_project_root()` walk-up, `INPUTS_DIR`,
  `OUTPUTS_DIR`, all per-component `OUT_X_DATA/FIGS/SUMMARIES`,
  `OUT_IMOGEN_INPUTS`, plus canonical filename constants (`RCMIP_CSV`,
  `FAIR_ERF_CSV`, `FAO_PRODUCTION_CSV`, `EDGAR_CH4_NEW`, …) and
  `ensure_output_dirs()`.
- `constants.py` (94) — `SCENARIOS` (5 SSP-RCP), `LPJG_TAG_MAP`,
  `SCEN_RCMIP_MAP`, `HIST_END=2014`, `TIER1_START=1970`,
  `SCENARIO_START=2020`, `PgC_to_MtCO2 = 44/12 × 1000`,
  `TgN_to_TgN2O = 44/28`, plus dicts of canonical CSV filenames per
  component output.
- `plot_style.py` (137) — `SCEN_COLORS` (IPCC palette), `HIST_COLOR='#1a1a1a'`
  (black for the unified historical line), `CMP_COLOR`, `rmean()`,
  `rmean_segmented()`, `step_band_horizontal()`, axis-styling kwarg dicts.
- `budget_refs.py` (94) — GMB 2025, GNB 2024, GCB 2025 Table 7 numerical
  values + helpers (`gmb_combined_ch4`, `gnb_combined_n2o`,
  `gcb_atmospheric_source_co2`).
- `__init__.py` (91) — re-exports for `from src.shared import …`.

`src/component_a_anthropogenic/` (~8682 lines, 28 .py files):
- `historical/` — six sectors × {processing, plotting}. Heaviest:
  `ch4_mm_processing.py` 850 lines, `n2o_synfert_processing.py` 711,
  `ch4_ef_processing.py` 589, `n2o_ms_processing.py` 624,
  `ch4_rice_processing.py` 565. Implements **IPCC 2019 Refinement V4 Ch5
  (Cropland), Ch10 (Livestock), Ch11 (Soils)** Tier-1 emission factors as
  hardcoded Python tables. Reads FAO 3 CSVs + EDGAR xlsx.
- `scenarios/` — `00_scenario_livestock_anchor.py` (339 lines, runs first;
  produces `anchored_livestock_2020_2100.csv` from FAO-2020 anchor ×
  PLUM-relative-change), then five sector pipelines numbered `01_ch4_ef`,
  `02_ch4_mm`, `03_n2o_mm`, `04_n2o_synfert`, `05_n2o_ms`, plus
  `06_scenario_ch4_rice_processing.py` and plotting (added in Round 15
  after rice scenario was found inside `rice_cult_plum_..._optB.zip`).
- `rcmip_substitution/` — `rcmip_substitution_processing.py` plus the two
  comparison plots (`rcmip_comparison1_plotting.py` agri-only,
  `rcmip_comparison2_plotting.py` full totals). Output:
  `rcmip_substitution_ch4.csv` and `rcmip_substitution_n2o.csv`
  (1005 rows = 5 SSPs × 201 yrs each).

`src/component_b_natural/` (~1791 lines, 5 .py files):
- `historical/lpjg_historical_processing.py` (370 lines) and
  `lpjg_historical_plotting.py` (472 lines) — stream the 3 historical .gz
  files, produce `lpjg_co2_annual.csv`, `lpjg_ch4_annual.csv`,
  `lpjg_n2o_annual.csv` plus a 4-panel comparison PNG.
- `scenarios/lpjg_scenario_processing.py` (290 lines) — accepts a scenario
  directory as argv[1] OR iterates all directories under `LPJG_SCEN_DIR`
  if invoked with no args (lines 279-289). `_upsert_scenario_rows()` makes
  per-scenario reruns safe (replaces, not appends). Produces
  `lpjg_*_annual_scenarios.csv` (long format with `Scenario` column).
- `full_trajectory/lpjg_combined_and_fair_processing.py` (133 lines) —
  builds the GMB-IFW (+112) + DCC (−23) corrected combined CH₄ CSVs and
  extracts the FAIR-ERF natural baseline.
- `full_trajectory/lpjg_historical_scenario_plotting.py` (526 lines) — the
  extended 1901–2100 plot.

`src/component_c_integration/` (~2848 lines, 9 .py files):
- `rcmip_co2_processing.py` (196) — extracts `Emissions|CO2|MAGICC Fossil
  and Industrial` (EFOS) for World × 5 SSPs, splices historical annual
  with 5-yearly scenario after linear interp; writes `rcmip_co2.csv`.
- `integrated_emissions_processing.py` (330) — assembles `Anthro_Mt +
  Natural_Mt = Total_Mt` per gas + `Default_total_Mt = RCMIP_total +
  FAIR_natural` reference. Outputs three `integrated_emissions_<gas>.csv`
  (1005 × 9 cols each).
- `integrated_emissions_plotting.py` (502).
- `external_comparators_*` (211 + 321) — top-down GMB/GNB/GCB period
  values; historical only.
- `hybrid_comparator_*` (381 + 377) — Option B full-trajectory comparator
  (budget anchors 1980–2020, RCMIP+FAIR outside, with SLAND correction
  for CO₂ to keep semantics consistent throughout).
- `conventional_comparator_*` (187 + 343) — Option A; pure RCMIP+FAIR
  throughout 1900–2100.

`src/component_d_imogen_export/imogen_inputs_export.py` (176) — the
**terminal stage**. Reads three integrated CSVs from `OUT_C_DATA`, asserts
each has 201 × 5 = 1005 rows per gas, and writes 5 wide-format
`imogen_inputs_<SSP>.csv` plus 1 long-format
`imogen_inputs_all_scenarios_long.csv` (3015 rows × 7 cols) into
`OUT_IMOGEN_INPUTS`.

`tests/` (3 files):
- `test_unit_conversions.py` — 5 assertions on PgC↔MtCO2 and TgN↔TgN2O.
- `test_co2_option_a_validation.py` — verifies SSP2-4.5 mean 2014–2020
  integrated CO₂ atmospheric source falls within ±1σ of GCB 2025
  partition (`|our − 7.6 PgC/yr| < 1.24 PgC/yr`). Skips with a soft
  warning if `integrated_emissions_co2.csv` doesn't exist.
- `test_imogen_export_schema.py` — verifies all 5 per-scenario CSVs +
  combined long-format exist, shape (201, 10) and (3015, 7) respectively,
  expected column order and no NaNs.

### 2.3 `imogen_ghg_controller_FULL/imogen_ghg_controller/`

Identical source tree to SOURCE_ONLY, plus:
- `inputs/` populated (5.1 GB total): `fao/` 107 MB, `plum/` 3.4 GB,
  `lpjg/` 1.5 GB (18 .gz files in the documented layout), `rcmip/` 46 MB,
  `fair_erf/` 28 KB, `edgar/` 63 MB, `reference_pdfs/` 48 MB.
- `outputs/` populated (66 MB total): `component_a/` 55 MB,
  `component_b/` 4.1 MB, `component_c/` 6.9 MB, `imogen_inputs/` 308 KB
  (the 6 terminal CSVs).
- `archive/` 4.3 MB of superseded scripts and prior session handoffs.
- `.gitignore` (Only-in-FULL marker per `diff -rq`).

### 2.4 FULL vs SOURCE_ONLY diff

`diff -rq imogen_ghg_controller_FULL/ imogen_ghg_controller_SOURCE_ONLY/`
produces the following classes of differences (full output captured):

| Class | Items | Notes |
|---|---|---|
| `archive/` subdirs | 4 dirs | `prior_session_handoffs/`, `scratch_session_scripts/`, `superseded_*/`. Only in FULL. The handoff explicitly gitignores these. |
| `inputs/<...>` subdirs | 7 dirs | All 7 input categories (`fao`, `plum`, `lpjg`, `rcmip`, `fair_erf`, `edgar`, `reference_pdfs`). Only in FULL. |
| `outputs/<...>` subdirs | 4 dirs | `component_a`, `component_b`, `component_c`, `imogen_inputs`. Only in FULL. |
| `docs/figures_gallery/*.png` | ~13 PNGs | Symlinks in both trees but the targets don't exist in either (broken symlinks → diff reports "No such file or directory"). |
| `.gitignore` | 1 file | Only in FULL. |

**Conclusion:** SOURCE_ONLY is exactly the canonical source subset
(excluding inputs/outputs/archive), as designed. `pyproject.toml`,
`requirements.txt`, every `src/**/*.py`, every `tests/*.py`, every `*.md`
top-level doc, and `run_all.py` are present in both. The size delta (5.2 GB
FULL vs 7.9 MB SOURCE_ONLY) is the embedded data: 5.1 GB inputs + 66 MB
outputs + 4.3 MB archive. The `.tar.gz` files corroborate (105 MB FULL vs
6.5 MB SOURCE_ONLY — only the FULL tarball is meaningfully large because
gzip already compressed the LPJ-GUESS .gz files inside).

---

## 3. Entry point and CLI

### 3.1 Primary driver — `run_all.py`

Argparse CLI (211 lines):

```bash
python run_all.py [--component {A,B,C,D,all}+] [--skip-plots]
                  [--dry-run|-n] [--verbose|-v]
```

The driver hardcodes 43 ordered steps as `(script_path, kind, label)`
tuples — `COMPONENT_A` 28 entries, `COMPONENT_B` 5 entries, `COMPONENT_C` 9
entries, `COMPONENT_D` 1 entry. `kind ∈ {'processing', 'plotting'}` for
`--skip-plots` filtering. Each step is executed via `subprocess.run(
['python3', str(script_path)], check=True)` from `PROJECT_ROOT` (i.e. the
parent of `src/`). On `CalledProcessError` it dumps the last 20 lines of
stdout/stderr and `sys.exit(1)`. There is **no parallelism**.

Component-B step 3 is the only step that processes all 5 scenarios in a
single subprocess call: `lpjg_scenario_processing.py` defaults to looping
over every directory in `LPJG_SCEN_DIR` when invoked with no args
(`if __name__ == '__main__': … for d in sorted(os.listdir(SCEN_ROOT)):
process_scenario(full)`). This is the longest single step (~10 min × 5
scenarios = ~50 min on a modern laptop per the manual).

### 3.2 Per-script invocation

Every `src/**/*.py` script is independently executable from any CWD via the
walk-up bootstrap (`while not (parent/'src').is_dir(): parent = parent.parent`).
Examples (from README §7 / Quick_Start.md):

```bash
python src/component_d_imogen_export/imogen_inputs_export.py
python src/component_b_natural/scenarios/lpjg_scenario_processing.py inputs/lpjg/scenarios/ssp2_rcp45
python src/component_c_integration/hybrid_comparator_processing.py
```

### 3.3 No external configuration file

There is **no `config.txt`, `config.yaml`, or `*_options.m`-style
configuration file**. All "configuration" is via:

1. **Hardcoded constants** in `src/shared/constants.py` (scenario list,
   period boundaries) and `src/shared/budget_refs.py` (GMB/GNB/GCB values).
2. **Environment variables** — runtime overrides of paths only:

| Env var | Default | Purpose |
|---|---|---|
| `IMOGEN_GHG_ROOT` | auto-discovered | bypass walk-up project-root finder |
| `OUT_DIR` | `OUT_<X>_DATA` or `..._FIGS` | per-script output override |
| `DATA_DIR` | `OUT_<X>_DATA` | input dir for plot scripts |
| `IN_DIR` | `inputs/lpjg/historical` | Component B historical streamer |
| `DATA_DIR_LPJ` | `outputs/component_b/data` | Component C reading B outputs |
| `DATA_DIR_RCMIP` | `outputs/component_a/data` | Component C reading A outputs |

3. **IPCC parameter tables** are hardcoded as Python dicts inside each
   sector script (`EMISSION_FACTORS`, `IPCC_REGIONS`, `WATER_REGIME_SF` …),
   making the script self-contained but requiring source edits to change
   parameters.

This is a **substantive interface difference** vs the C++ Intermediary, which
ships a `Code/config.txt` (see §12).

---

## 4. Inputs — file-by-file

Authoritative source: `src/shared/paths.py` (constants) and
`inputs/README.md` (acquisition). Numbers verified against the FULL tree.

| Path under `inputs/` | Source dataset | Format | Used by | Required size |
|---|---|---|---|---|
| `fao/Production_Crops_Livestock_E_All_Data.csv` | FAOSTAT bulk | wide CSV (Country×Item×Element×Unit × Y1961…Y2023) | every Component A historical sector | ~50 MB |
| `fao/Emissions_Totals_E_All_Data.csv` | FAOSTAT bulk | wide CSV | benchmark plots in Component A | ~70 MB |
| `fao/Inputs_FertilizersNutrient_E_All_Data.csv` | FAOSTAT bulk | wide CSV | `n2o_synfert_processing.py` only | ~15 MB |
| `plum/plum_crop_s1.csv` | PLUMv2 modeller | per-country crop area / livestock projections, 5-yearly 2025–2100, all 5 SSP-RCP | scenario sectors 01–05 | ~50 MB |
| `plum/Livestock_counts.txt` | PLUMv2 (extracted from `Livestock_counts.zip` ~270 MB) | text per-country livestock per scenario | `00_scenario_livestock_anchor.py` (needs 6–8 GB RAM) | ~1 GB uncompressed |
| `plum/rice_cult_plum_scen_using_plum_irrig_optA.zip` | PLUMv2 | Option-A irrigation methodology | NOT currently integrated (see §13.1) | small |
| `plum/rice_cult_plum_scen_using_plum_irrig_optB.zip` | PLUMv2 | Option-B (IrrigAmount split) — canonical | `06_scenario_ch4_rice_processing.py` | small |
| `lpjg/historical/lpjg_cflux.out_historical.gz` | LPJ-GUESS modeller, HILDA+v2 forcing | gzipped whitespace-text, cell-first ordering, 11 cflux cols, 0.5° × 0.5°, 62 538 cells × 120 yrs | `lpjg_historical_processing.py` | ~120 MB |
| `lpjg/historical/lpjg_mch4.out_historical.gz` | LPJ-GUESS modeller | 12 monthly CH₄ wetland cols, g CH₄ m⁻² month⁻¹ | same | ~64 MB |
| `lpjg/historical/lpjg_ngases.out_historical.gz` | LPJ-GUESS modeller | NH₃, NO_x, N₂O, N₂ × {fire, soil} + Total, kg N ha⁻¹ yr⁻¹ | same | ~138 MB |
| `lpjg/scenarios/ssp{1_rcp26,2_rcp45,3_rcp70,4_rcp60,5_rcp85}/lpjg_{cflux,mch4,ngases}.out_<tag>.gz` | LPJ-GUESS modeller, PLUMv2 + LUH2-harmonized forcing | same as historical, 80 yrs (2021–2100) | `lpjg_scenario_processing.py` | 15 files, ~1 GB combined |
| `rcmip/rcmip-emissions-annual-means-v5-1-0.csv` | rcmip.org Phase 2 | long CSV, `Variable, Region, Scenario, Mip_Era, Activity_Id, Unit, Y1750…Y2500` | `rcmip_co2_processing.py`, `rcmip_substitution_processing.py` | ~50 MB |
| `fair_erf/natural.csv` | FAIR climate emulator (github.com/OMS-NetZero/FAIR) | small CSV `Year, FAIR_CH4_TgCH4_yr, FAIR_N2O_TgN_yr` | `lpjg_combined_and_fair_processing.py`, comparators | <1 MB |
| `edgar/EDGAR_CH4_1970_2024.xlsx` | EDGAR JRC 2025 release | xlsx, sheet `IPCC 2006`, header at row 9 | 8 CH₄ scripts (benchmark column + scenario proportioning) | ~25 MB |
| `edgar/EDGAR_N2O_1970_2024.xlsx` | EDGAR JRC 2025 release | same | 8 N₂O scripts | ~25 MB |
| `edgar/essd_ghg_data_emiss.xlsx` | OLD ESSD release (predecessor format) | sheet `data_totals` | **only** `n2o_synfert_processing.py` (needs the 4D11 sub-category aggregated away in the 2025 release) | ~10 MB |
| `edgar/IEA_EDGAR_CO2_1970_2024.xlsx` | IEA-EDGAR CO₂ | xlsx | NOT currently used (staged for forward compatibility) | ~8 MB |
| `reference_pdfs/*.pdf` | IPCC 2019 Refinement V4 Ch5/10/11; IPCC 2006 V4 Ch10; GMB / GNB / GCB papers | PDF | NOT parsed at runtime | ~50 MB |

**Total disk after population: ~2.8 GB documented in `inputs_README.md`,
~5.1 GB measured in the FULL tree.** The discrepancy is mostly that the
FULL `plum/` directory is 3.4 GB (the modeller delivered additional files
beyond the documented minimum).

---

## 5. Outputs — file-by-file

Three intermediate component output trees plus the terminal IMOGEN-input
tree. All landings are under `outputs/`. Verified against the FULL tree.

### 5.1 `outputs/component_a/data/` (~37 CSVs)
Per-sector historical: `<sector>_global.csv`, `<sector>_country.csv`,
`<sector>_regional.csv`, plus sector-specific decompositions
(`ch4_ef_species.csv`, `ch4_rice_waterclass.csv`,
`n2o_ms_components.csv`, …). Per-sector scenario (under
`scenario_pipeline/`): `scenario_<sector>_global.csv`,
`scenario_<sector>_regional.csv`. Plus `anchored_livestock_2020_2100.csv`
and the diagnostic `fao2020_missing_species.csv`. **The two integration
products** that feed Component C live at the top of `data/`:
`rcmip_substitution_ch4.csv` (1005 × 8 cols: Year, Scenario, RCMIP_total,
RCMIP_agri, RCMIP_nonagri, Our_agri, New_total, Period) and
`rcmip_substitution_n2o.csv` (same schema). Verified head:
`1900,SSP1-2.6,87.6133,45.61,42.0033,45.61,87.6133,pre-inventory`.

### 5.2 `outputs/component_a/figures/` (13 PNGs)
6 historical sector trends + 5 scenario sector trends + 2 RCMIP comparison
plots (`rcmip_comparison1_agri_sectors.png`,
`rcmip_comparison2_full_totals.png`).

### 5.3 `outputs/component_b/data/` (~10 CSVs)
- `lpjg_co2_annual.csv` (120 rows, NEE in Pg C/yr, with all 11 component
  fluxes); `lpjg_co2_annual_scenarios.csv` (400 rows: 80 yrs × 5 scen +
  Scenario col).
- `lpjg_ch4_annual.csv` / `_scenarios.csv` — wetland CH₄ in Tg CH₄/yr.
- `lpjg_ch4_combined_annual.csv` (121 rows, 1900–2020 with backfilled
  1900) / `_scenarios.csv` — adds `IFW`, `DCC`, `Combined_*`,
  `CombinedDCC_*` columns (the **DCC-corrected** column is the one
  Component C uses).
- `lpjg_n2o_annual.csv` / `_scenarios.csv` — all 9 N gas species in Tg
  N/yr plus the N₂O species converted to Tg N₂O/yr.
- `fair_erf_natural_baseline.csv` (121 rows, 1900–2020).
- `lpjg_budget_value_sources.csv` — 27-row provenance table mapping each
  plotted benchmark to source paper / table / period.

### 5.4 `outputs/component_b/figures/`
2 PNGs: `lpjg_historical_comparison.png` (4-panel 1901–2020) and
`lpjg_historical_scenario_comparison.png` (1901–2100 full trajectory).

### 5.5 `outputs/component_c/data/` (13 CSVs)
- `rcmip_co2.csv` (1005 × 4 cols: Year, Scenario, EFOS_MtCO2, Period).
- `integrated_emissions_{ch4,n2o,co2}.csv` (1005 × 9 cols each: Year,
  Scenario, Period, Anthro_Mt, Natural_Mt, Total_Mt, RCMIP_total_Mt,
  FAIR_natural_Mt, Default_total_Mt). **Used by Component D and the test
  suite.**
- `external_comparators_{ch4,n2o,co2}.csv` (period-banded; small).
- `hybrid_comparator_{ch4,n2o,co2}.csv` (1005 × 6 cols: …,
  Comparator_Mt, Comparator_lo_Mt, Comparator_hi_Mt, Source_segment).
- `conventional_comparator_{ch4,n2o,co2}.csv` (1005 × 5 cols).

### 5.6 `outputs/component_c/figures/` (4 PNGs)
`integrated_emissions_comparison.png`, `external_comparators_comparison.png`,
`hybrid_comparator_comparison.png` (primary validation figure),
`conventional_comparator_comparison.png`.

### 5.7 `outputs/imogen_inputs/` — **the terminal deliverable** (6 files)

| File | Rows × Cols | Size in FULL |
|---|---|---|
| `imogen_inputs_SSP1-2.6.csv` | 201 × 10 | 21 274 B |
| `imogen_inputs_SSP2-4.5.csv` | 201 × 10 | 21 324 B |
| `imogen_inputs_SSP3-7.0.csv` | 201 × 10 | 21 397 B |
| `imogen_inputs_SSP4-6.0.csv` | 201 × 10 | 21 351 B |
| `imogen_inputs_SSP5-8.5.csv` | 201 × 10 | 21 504 B |
| `imogen_inputs_all_scenarios_long.csv` | 3015 × 7 | 185 673 B |

**Per-scenario wide schema** (verified head SSP2-4.5):
`Year, CH4_anthro_Mt, CH4_natural_Mt, CH4_total_Mt, N2O_anthro_Mt,
N2O_natural_Mt, N2O_total_Mt, CO2_EFOS_Mt, CO2_NEE_Mt, CO2_total_Mt`. All
numeric cells written `float_format='%.6f'`. Year 1900 row sample:
`1900,87.613300,175.952299,263.565599,1.356163,11.103581,12.459744,1788.820939,-4143.864232,-2355.043294`.

**Long schema** (verified head):
`Year, Scenario, Gas, Anthro_Mt, Natural_Mt, Total_Mt, Unit`, with
`Unit ∈ {"Mt CH4/yr","Mt N2O/yr","Mt CO2/yr"}`.

**Units note (from script docstring):** all values in Mt-of-gas per year
(10⁹ kg). For CO₂ this is Mt CO₂, **not** Mt C — multiply by 12/44 to
convert to Mt C, or divide `CO2_total_Mt` by 3666.67 for Pg C/yr.

---

## 6. IPCC formula coverage

The pipeline implements **IPCC 2019 Refinement to the 2006 Guidelines for
National GHG Inventories, Volume 4 (AFOLU), Tier 1 only**. From
TECHNICAL_MANUAL §6.1:

| Gas | Sector | IPCC chapter | Activity data | Script |
|---|---|---|---|---|
| CH₄ | Enteric fermentation | 2019 Refinement V4 Ch10 | FAO livestock counts | `historical/ch4_ef_processing.py` (589 lines) |
| CH₄ | Manure management | V4 Ch10 | FAO livestock | `historical/ch4_mm_processing.py` (850 lines) |
| CH₄ | Rice cultivation | V4 Ch5 | FAO rice harvested area; PLUMv2 IrrigAmount split for scenarios | `historical/ch4_rice_processing.py` (565); `06_scenario_ch4_rice_processing.py` (388) |
| N₂O | Manure management | V4 Ch10 | FAO livestock | `n2o_mm_processing.py` (324) |
| N₂O | Managed soils | V4 Ch11 | FAO livestock + crop residues | `n2o_ms_processing.py` (624) |
| N₂O | Synthetic fertilizers | V4 Ch11 | FAOSTAT `Inputs_FertilizersNutrient` | `n2o_synfert_processing.py` (711) |

**Not covered** (TECHNICAL_MANUAL §1.5 / §6.1 caveat):
- CO₂ AFOLU sectors (no independent CO₂ Tier-1 inventory; anthropogenic
  CO₂ is RCMIP `Emissions|CO2|MAGICC Fossil and Industrial` unchanged).
- Indirect N₂O emissions from N deposition (left to RCMIP non-agri
  residual; potential double-counting flagged in TECHNICAL_MANUAL §15.5).
- Biomass burning (CH₄, N₂O) — would require GFED, not currently used.
- Industrial CH₄/N₂O fugitives — left to RCMIP non-agri.

**Tier-2 / Tier-3 NOT implemented** (TECHNICAL_MANUAL §15.2). Author
notes ~30–40 % per-sector uncertainty relative to Tier-2 country
inventories.

**Improvements vs C++ Intermediary** (claimed by HANDOFF; not directly
verified against C++ source per scope constraint):
- Uses the **2019 Refinement** parameter set for scenarios (more recent
  than 2006 GLs). Documented as an **intentional discontinuity**:
  historical N₂O MM uses 2006-split parameters (633 Gg at 2020), scenario
  uses 2019 parameters (750.6 Gg at 2020 SSP2) — small step at 2020 by
  design (HANDOFF §2.5).
- Country-sum aggregation rather than reading FAO's "World" row directly
  (handles country splits/merges — superseded the older "World-row
  aggregation" approach, archived in `archive/superseded_anthropogenic_
  worldrow_aggregation/`).
- Explicit benchmark column per sector global CSV against EDGAR 2025 (16
  scripts) and EDGAR-OLD 4D11 (1 script, n2o_synfert).

---

## 7. CH₄ / N₂O / CO₂ paths

For each gas, three layers: anthropogenic, natural, integrated total.
Source-of-truth file paths cited where useful.

### 7.1 CH₄

**Anthropogenic** (Mt CH₄/yr):
1. `Component A historical` — six per-sector global CSVs: `ch4_ef_global.csv`,
   `ch4_mm_global.csv`, `ch4_rice_global.csv`. Tier-1 EF × FAO activity
   data for years 1970–2020 (HANDOFF §2.1, TECHNICAL_MANUAL §6.3).
2. `Component A scenarios` — `01_scenario_ch4_ef_processing.py`,
   `02_..._mm`, `06_..._rice` produce `scenario_<sector>_global.csv` for
   2020–2100 from `anchored_livestock_2020_2100.csv` + PLUMv2 rice areas.
3. `rcmip_substitution_processing.py` performs `New_total = RCMIP_total
   − RCMIP_agri + Our_agri` per (Year, Scenario) where `RCMIP_agri =
   Emissions|CH4|MAGICC AFOLU|Agriculture`. For 1900–1969 `Our_agri =
   RCMIP_agri` (identity). Output: `rcmip_substitution_ch4.csv`.
4. Component C reads column `New_total` as `Anthro_Mt`.

**Natural** (Tg CH₄/yr = Mt CH₄/yr):
1. LPJ-GUESS `lpjg_mch4.out_<run>.gz` streamed → wetland monthly fluxes ×
   12 × area / 1e12 → `lpjg_ch4_annual{,_scenarios}.csv`.
2. `lpjg_combined_and_fair_processing.py` adds the GMB IFW (+112) and
   DCC (−23) constants:
   `CombinedDCC_TgCH4_best = LPJ_wetland + 112 − 23 = LPJ_wetland + 89`
   (HANDOFF §5.3, TECHNICAL_MANUAL §7.5). Range bounds via
   `(IFW_lo + DCC_hi)` and `(IFW_hi + DCC_lo)`.
3. Component C reads `CombinedDCC_TgCH4_best` as `Natural_Mt`.

**Integrated:** `Total_Mt = Anthro_Mt + Natural_Mt`. Verified
SSP2-4.5 / 2020 ≈ 393 + 179 = 572 Mt CH₄/yr.

### 7.2 N₂O

**Anthropogenic** (Mt N₂O/yr):
1. Component A historical sectors `n2o_mm`, `n2o_ms`, `n2o_synfert`. The
   synfert sector uniquely uses the OLD ESSD EDGAR file (the 2025 release
   aggregates IPCC 4D11 into 3.C.4 + 3.C.5).
2. Scenario equivalents `03_..._mm`, `04_..._synfert`, `05_..._ms`.
3. `rcmip_substitution_processing.py` — same algebra as CH₄, with
   `RCMIP_agri = Emissions|N2O|MAGICC AFOLU` (no separate Agriculture
   sub-aggregation in RCMIP for N₂O). Output: `rcmip_substitution_n2o.csv`.
4. Component C reads `New_total` as `Anthro_Mt`.

Documented historical→scenario discontinuity: the **N₂O MM parameter
switch at 2020** (HANDOFF §2.5) — 633 Gg at 2020 historical vs 750.6 Gg
SSP2 scenario.

**Natural** (Tg N₂O/yr = Mt N₂O/yr):
1. LPJ-GUESS `lpjg_ngases.out_<run>.gz` → `N2O_soil` + `N2O_fire` columns,
   converted from kg N ha⁻¹ yr⁻¹ via `× area / 1e4 / 1e9 → Tg N/yr`,
   then `× 44/28 → Tg N₂O/yr`.
2. Component C: `Natural_Mt = (N2O_soil_TgN + N2O_fire_TgN) × 44/28` per
   `integrated_emissions_processing.py` docstring lines 27-31.

**Integrated:** `Total_Mt = Anthro_Mt + Natural_Mt`. Verified
SSP2-4.5 / 2020 ≈ 12.34 + 14.4 = 26.7 Mt N₂O/yr.

**Possible double-counting flag** (TECHNICAL_MANUAL §15.5): LPJ-GUESS
`N2O_soil` may include "indirect" emissions GNB classifies as
anthropogenic. ~1–2 Tg N₂O/yr / ~5–8 % bias estimated; not corrected.

### 7.3 CO₂

**Anthropogenic** (Mt CO₂/yr): **No Tier-1 inventory.** The script
`rcmip_co2_processing.py` extracts `Emissions|CO2|MAGICC Fossil and
Industrial` (= EFOS) for World × 5 SSPs from RCMIP, splices historical
annual 1750–2014 + scenario 5-yearly (linearly interpolated to annual
2015–2100). Output: `rcmip_co2.csv` (1005 × 4). EFOS pre-1970 is RCMIP
unchanged.

**Natural** (Mt CO₂/yr derived from Pg C/yr): LPJ-GUESS
`lpjg_cflux.out_<run>.gz` → 11 component fluxes (`Veg`, `Repr`, `Soil`,
`Fire`, `Est`, `Seed`, `Harvest`, `LU_ch`, `Slow_h`, `Manure`=0, `NEE`).
The streamer produces `lpjg_co2_annual{,_scenarios}.csv` with `NEE_PgC` =
sum of all components. Component C: `Natural_Mt = NEE_PgC × 44/12 ×
1000`.

**Crucially, NEE includes anthropogenic land-use fluxes**: `LU_ch +
Harvest + Slow_h` (HANDOFF §3.4). This is by design — it means the
combined `EFOS + NEE` matches GCB's "atmospheric source" (= EFOS + ELUC −
SLAND) and avoids ELUC double-counting. Validated against GCB 2025
Table 7: SSP2-4.5 / 2014–2020 mean = 7.93 Pg C/yr vs GCB best 7.6 ± 1.24
(within ±1 σ). This is the test target of
`tests/test_co2_option_a_validation.py`.

**Integrated:** `Total_Mt = EFOS_Mt + NEE_Mt`. Verified SSP2-4.5 / 2020 ≈
37 388 + (−7 300) = ~30 100 Mt CO₂/yr.

---

## 8. Double-counting prevention

The package has explicit double-counting safeguards documented across the
docs.

1. **CH₄ / N₂O anthropogenic side: substitution, not addition** (HANDOFF
   §2.2). The algebra is `New_total = RCMIP_total − RCMIP_agri + Our_agri`.
   The minus removes RCMIP's CEDS-derived agriculture before adding our
   independent Tier-1 estimate. For pre-1970 (no Tier-1 inventory)
   `Our_agri = RCMIP_agri` so `New_total = RCMIP_total` (identity).
2. **CO₂ Option-A integration framing** (HANDOFF §8.1, TECHNICAL_MANUAL
   §8.2). Anthropogenic CO₂ is **EFOS only** (`MAGICC Fossil and
   Industrial`), NOT the full `Emissions|CO2`. LPJ-GUESS NEE already
   carries the anthropogenic-LULC components (LU_ch, Harvest, Slow_h),
   so adding RCMIP's `MAGICC AFOLU` would double-count. Validated
   empirically against GCB 2025.
3. **N₂O LPJ scope note** (HANDOFF §3.5). LPJ-GUESS is run with
   `Manure = 0`, so `N2O_soil` ≈ natural soil + LUC-induced soil — not
   the same as the IPCC Tier-1 managed-soils sector that uses anthropogenic
   N inputs. Author flags this as **conceptually consistent** with GNB
   2024's "natural baseline + perturbed" framing but **acknowledges
   residual indirect-emission overlap** in TECHNICAL_MANUAL §15.5.

**Comparison vs the C++ Intermediary's approach:** subagent-5 territory.
This subagent confirms the Python pipeline implements substitution
explicitly via the `RCMIP_total − RCMIP_agri + Our_agri` algebra, codes
the choice into `rcmip_substitution_processing.py` (header §SUBSTITUTION
ALGEBRA), and asserts the choice is recorded as Option A (HANDOFF §8.1,
TECHNICAL_MANUAL §1.5).

---

## 9. Dependencies and packaging

`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "imogen_ghg_controller"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pandas>=2.0", "numpy>=1.24", "matplotlib>=3.7", "pyarrow>=14.0"]

[project.optional-dependencies]
test = ["pytest>=7.0"]

[tool.setuptools]
packages = ["src", "src.shared",
            "src.component_a_anthropogenic",
            "src.component_b_natural",
            "src.component_c_integration",
            "src.component_d_imogen_export"]
```

`requirements.txt`:

```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
pyarrow>=14.0
```

**No openpyxl / xlrd in requirements** — yet the EDGAR scripts read xlsx
(via pandas, which silently requires openpyxl). This is a **likely missing
dependency** — see §13.

Other runtime requirements (TECHNICAL_MANUAL §4.1):
- Python ≥ 3.10.
- `zcat` on PATH (LPJ-GUESS streaming uses `subprocess.Popen(['zcat',
  gz_path])`). On Windows requires WSL2 / Cygwin.
- ~2.5 GB free disk (1.8 GB inputs + ~700 MB working space + outputs).
- 4 GB minimum RAM, 8 GB recommended (livestock anchor needs 6–8 GB
  alone — HANDOFF / Quick_Start.md).

**Notably absent**: no xarray, no netCDF4 / h5py / cfgrib (the inputs are
gzipped text and CSVs / xlsx; nothing is NetCDF). No GDAL / rasterio (no
gridded outputs). No cartopy (Component B aggregates rather than mapping).
No pytest in `requirements.txt` — listed only as optional-dependency
`test`.

**Source layout vs. `pip install -e .`**: `pyproject.toml` lists `src` as
a package, but the package isn't actually importable as
`imogen_ghg_controller.shared.paths` — every script imports
`from src.shared.paths import …`. TECHNICAL_MANUAL §16.5 calls out
"Migrate to pyproject.toml-based packaging" as future work.

---

## 10. Tests

Three pytest-discoverable test files in `tests/` (~17 KB total). Each is
also a standalone executable (`if __name__ == '__main__': …`).

| File | Tests | What it verifies | Working? |
|---|---|---|---|
| `test_unit_conversions.py` | 5 functions | `PgC_to_MtCO2 ≈ 3666.67`, round-trip identity, `TgN_to_TgN2O = 44/28`, `1 Pg C ≈ 3.667 Gt CO₂` | Pure-arithmetic; passes without inputs/outputs |
| `test_co2_option_a_validation.py` | 1 function | SSP2-4.5 mean 2014–2020 integrated CO₂ atmospheric source within ±1 σ of GCB 2025 partition (`|our − 7.6 PgC/yr| < 1.24 PgC/yr`) | Runs only after Component C; soft-skips if `integrated_emissions_co2.csv` missing. **The headline scientific test.** |
| `test_imogen_export_schema.py` | 4 functions | All 5 per-scenario CSVs + long-format CSV exist, shapes (201, 10) and (3015, 7), expected column order, no NaNs, Year=1900..2100 | Runs only after Component D |

HANDOFF §16 reports "All 3 tests in `tests/` pass" after the canonical
end-to-end run. The pipeline is also reproducibility-tested by
md5-checksum: HANDOFF §16.2 reports **39 of 40 user-provided reference
data CSVs byte-identical** (the single CSV diff is cosmetic — `FAOCountry`
vs `Country` column name + pandas float-formatting precision) and **13 of
14 reference plots byte-identical** (the diff plot is an intentional
upgrade to GMB 2025 / GNB 2024 / GCB 2025 budget refs and IFW/DCC
correction overlay).

**Honest test-coverage gaps** flagged by author (TECHNICAL_MANUAL §13.3,
§15.8): no per-sector regression tests for Component A, no shape/value
tests for Component B, no comparator-construction tests, plotting scripts
not numerically tested.

---

## 11. Substitution roadmap (C++ Intermediary → Intermediary_py)

### 11.1 What "substitute the C++ Intermediary" means in the coupled framework

Per the parent framework's structure (see sibling
`Intermediary/Code/Makefile` + `config.txt` + `include/` + `src/`, content
not investigated in depth — subagent-5 territory), the C++ Intermediary is
a stage in the coupled `LPJG-IMOGEN` loop sandwiched between LPJ-GUESS /
PLUM regridding outputs and the IMOGEN climate emulator's expected forcing
inputs. The Python package, in contrast, is positioned as a **standalone,
non-iterative pipeline** that produces the IMOGEN-ready forcing CSVs in a
single end-to-end run from raw FAO/PLUM/RCMIP/LPJ-GUESS data. Conceptually
they overlap on the *output side* (both produce forcing inputs for IMOGEN)
but differ in scope on the input side (the Python pipeline is much wider
— it ingests FAO and RCMIP and rebuilds the anthropogenic inventory from
scratch). **The Python package does not currently slot into the same
loop position** the C++ binary occupies.

### 11.2 Concrete integration steps

A best-effort, evidence-based ordering. Items requiring confirmation from
other subagents are flagged.

1. **Establish IMOGEN's actual input-file spec.** *(BLOCKING.)*
   Quick_Start.md (lines 165–166) explicitly states: *"please share the
   IMOGEN code so I can determine the input data form/structure/format
   requirements and figure out how the 6 IMOGEN-input CSVs we produce
   should be transformed for ingestion into IMOGEN."* The 10-column
   wide-format CSV produced by Component D is **the author's plausible
   guess at what IMOGEN wants, not a verified contract**. Subagent
   investigating IMOGEN / `Imogen-controller/` should provide the
   authoritative file format(s) and naming conventions.

2. **Map each Component-D output column to an IMOGEN-controller input
   field.** Until step 1 lands this is speculative. The Python schema is
   `Year, CH4_anthro_Mt, CH4_natural_Mt, CH4_total_Mt, N2O_anthro_Mt,
   N2O_natural_Mt, N2O_total_Mt, CO2_EFOS_Mt, CO2_NEE_Mt, CO2_total_Mt`,
   units Mt-of-gas/yr, period 1900–2100, one CSV per of 5 SSP-RCP
   scenarios. The C++ Intermediary almost certainly produces something
   per-year, per-region; if IMOGEN needs region-resolved or grid-resolved
   inputs the Python pipeline is **insufficient as drop-in replacement**
   (TECHNICAL_MANUAL §15.6, §16.3 confirm the pipeline aggregates LPJ
   to global-only).

3. **Decide the substitution mode.** Two possibilities:
   - **(a) Drop-in CSV producer.** The Python pipeline runs once
     up-front; its 6 terminal CSVs are placed where IMOGEN-controller
     normally reads C++ Intermediary outputs; a thin wrapper shell
     script or symlink redirects file paths. Requires the input/output
     file formats to be compatible (column order, units, year coverage).
     If unit/format mismatch, an adapter script is needed (e.g.
     reshape-to-long, year subset, unit conversion).
   - **(b) Per-iteration callable.** The framework's `Imogen-controller`
     calls the Intermediary repeatedly during a coupled simulation,
     passing intermediate state. The Python pipeline is **not designed
     for this** — it streams FAO/PLUM/LPJ data from disk and writes
     final CSVs. It would require refactoring `imogen_inputs_export.py`
     into a function callable with in-memory arguments, with the
     anthropogenic and natural sides exposed as separate calls.

4. **Add a wrapper entry point.** Whether the framework calls the Python
   pipeline as a subprocess, a Python module, or via a shell script,
   create a stable entry point — e.g. a CLI like
   `imogen-ghg run --output-dir <path> --scenarios SSP2-4.5 SSP5-8.5`
   that the C++ orchestrator can invoke with `system()` /
   `subprocess.run`. TECHNICAL_MANUAL §16.5 lists "Add a CLI entry
   point" as future work; currently the only CLI is `python run_all.py
   --component …`.

5. **Reconcile the input-data sources.** The C++ Intermediary likely
   reads PLUM output through `RegridLPJG` / `Regrid` / `Common-directory`
   (sibling directories, content not investigated) using a different
   format than `inputs/plum/plum_crop_s1.csv` / `Livestock_counts.txt`.
   Either:
   - convert the framework's existing PLUM / regrid outputs into the
     CSV/zip layout the Python pipeline expects, or
   - rewrite the Python pipeline's `inputs/plum/` ingestion to read the
     framework's actual format directly. The first is lower-cost (one
     adapter script in the framework); the second couples the Python
     code to the framework.

6. **Resolve the LPJ-GUESS .gz file location.** In the framework, LPJ-GUESS
   outputs land somewhere under `RegridLPJG` or `landsymm_imogen_setup`
   per `cflux/mch4/ngases` naming. The Python pipeline expects them at
   `inputs/lpjg/historical/` and `inputs/lpjg/scenarios/<ssp>/` with
   exact filenames `lpjg_<var>.out_<tag>.gz`. Either symlink or rewire
   `paths.py` constants `LPJG_HIST_DIR` / `LPJG_SCEN_DIR`.

7. **Address the iteration/feedback question.** If the coupled framework
   iterates (e.g. IMOGEN feeds GMST back to drive PLUM, which
   re-emerges as new LPJ-GUESS forcing), the Python pipeline currently
   has **no mechanism** for accepting that feedback. It assumes
   PLUMv2 SSP-RCP outputs are fixed scenario inputs.

8. **Replace `run_all.py` with the framework's orchestrator.** `run_all.py`
   is internal to the Python package; the coupled framework's main loop
   would call individual scripts or the new CLI entry point per (3)/(4).

9. **Test parity.** Run both the C++ Intermediary and Intermediary_py
   end-to-end against an identical input set; compare the IMOGEN-fed
   outputs numerically. The Python pipeline's known offsets (e.g.
   methodology-driven step at 2020 in CH₄ EF and N₂O MM, HANDOFF §2.5)
   will manifest as differences from the C++ output and need
   documentation / sign-off, not "fixing".

10. **Decide the canonical version.** HANDOFF §1 calls the Python codebase
    "complete and reorganized into a single shareable codebase". TECHNICAL
    MANUAL §16.4 lists future methodological extensions. Whoever owns
    integration must decide whether (a) the Python output goes through
    the existing IMOGEN-controller, (b) the C++ Intermediary is retired
    in favour of the Python wrapper, or (c) both run in parallel for a
    transition period.

---

## 12. Compatibility / interface differences with the C++ Intermediary's I/O

This subagent did not deep-dive the C++ Intermediary (subagent-5 scope).
Surface-level comparison from `ls Intermediary/Code/`:

| Aspect | C++ Intermediary | Python Intermediary_py |
|---|---|---|
| Build system | `Makefile` (in `Intermediary/Code/`) | `pyproject.toml` + `pip install -r requirements.txt` |
| Configuration | `Code/config.txt` (text config file) | Hardcoded constants (`src/shared/constants.py`, `budget_refs.py`) + env vars (`IMOGEN_GHG_ROOT`, `OUT_DIR`, `DATA_DIR_*`) |
| Source layout | `Code/include/` + `Code/src/` (C++ headers + impl) | `src/<component>/` (Python packages) + `src/shared/` |
| Invocation | Compile → run binary | `python run_all.py [--component …]` |
| Inputs | Unknown to this subagent. Likely consumes `Common-directory/` and `RegridLPJG/` outputs in the framework | FAO 3 CSVs + RCMIP CSV + FAIR ERF CSV + EDGAR 4 xlsx + PLUM 3 files + LPJ-GUESS 18 .gz files. **Different acquisition surface — does not consume framework's regridded outputs directly.** |
| Output | Unknown to this subagent | 6 CSVs per run: 5 wide per-scenario + 1 long combined, in `outputs/imogen_inputs/` |
| Output format | Unknown | CSV, Mt-of-gas/yr units, decomposed into anthro / natural / total, fixed 1900–2100 annual |
| Iterability | Unknown — likely callable per coupling step | **Single-shot pipeline.** No state / no feedback; runs end-to-end in ~25 min |
| Spatial resolution | Unknown | **Global only** (LPJ-GUESS gridded inputs aggregated to global totals; no regional or per-cell outputs) |
| Scope of substitution | Unknown | CH₄ + N₂O agricultural sectors substituted into RCMIP CMIP6; CO₂ EFOS used unchanged; LPJ-GUESS NEE used as natural/biospheric CO₂ |

**Open compatibility questions** (require subagent 5 / IMOGEN-side input):
- Is the C++ Intermediary's output format CSV, NetCDF, or something else?
- What are the column names and units IMOGEN-controller actually reads?
- Does IMOGEN need region-resolved emissions, or are global trajectories
  acceptable?
- Is the time axis 1900–2100 annual, or does IMOGEN need a different
  span / resolution?
- Does the framework expect per-scenario files or a single combined
  file?

Until these are answered, **the Python pipeline cannot be wired in as a
drop-in replacement**.

---

## 13. Bugs, gaps, hardcoded paths, TODO/FIXME

### 13.1 RESOLVED (per the docs themselves)

HANDOFF Round 15 already fixed a large class of bugs: 89 scripts/files
affected by hardcoded `/mnt/user-data/uploads/`, `/tmp/...`,
`/home/claude/Emissions_Modeling_Project_Directory/...` paths; 11 broken
f-strings; 7 Component-C scripts missing `paths.py` import; missing EDGAR
staging; and the CH₄ rice scenario discovered inside
`rice_cult_plum_..._optB.zip`. HANDOFF Round 16 fixed scenario directory
inconsistency (4 scenario scripts writing to top-level vs
`scenario_pipeline/`) and historical plot scripts writing PNGs to data
subdirs. After R16 the pipeline is reported as bit-reproducible across
re-runs (md5-verified) and against user reference outputs (39/40 CSVs and
13/14 plots byte-identical).

### 13.2 Open gaps and limitations (per TECHNICAL_MANUAL §15)

| # | Item | Severity | Source |
|---|---|---|---|
| 15.2 | Tier-1 only — no Tier-2 / Tier-3 implementation. ~30–40 % per-sector uncertainty. | Methodological | TECH §15.2 |
| 15.3 | **No uncertainty propagation through the integrated trajectory.** Comparator bands shown are observation σ, not pipeline σ. | Methodological | TECH §15.3 |
| 15.4 | GMB IFW (+112) and DCC (−23) corrections are **constants** — no temperature dependence on inland-freshwater CH₄. End-of-century natural CH₄ may be conservative. | Methodological | TECH §15.4 |
| 15.5 | **Possible N₂O double-counting.** LPJ-GUESS soil N₂O may include indirect emissions GNB classifies as anthropogenic; ~5–8 % bias estimated. Not corrected. | Methodological / scientific | TECH §15.5 |
| 15.6 | **Inconsistent matplotlib backend handling.** Some plotting scripts set `MPLBACKEND=Agg` internally, others don't → some scripts may fail on a headless server. | Engineering | TECH §15.6 + lone TODO comment ("TODO: standardize.") at TECH §14.5 |
| 15.7 | **Missing `if __name__ == '__main__'` guards** in some scripts → top-level computation runs on import, so scripts can't be cleanly imported as modules. | Engineering | TECH §15.7 |
| 15.8 | **Tests don't exercise Components A and B end-to-end.** Only Component C → D outputs are tested numerically. | Test coverage | TECH §15.8 |
| 15.9 | LPJ-GUESS .gz files are gigabytes → CI/CD impractical without synthetic fixtures (`IMOGEN_GHG_TEST_MODE` env var idea proposed but not implemented). | Infrastructure | TECH §15.9 |
| 15.10 | **No formal data versioning.** No `inputs/manifest.json` SHA-256s; can't tell from outputs which input version was used. | Reproducibility | TECH §15.10 |

### 13.3 Items this subagent flags additionally (verified in code)

- **Missing xlsx library in `requirements.txt`.** EDGAR scripts read
  `.xlsx` via pandas (e.g.
  `pd.read_excel(EDGAR_CH4_NEW, sheet_name='IPCC 2006', header=9)`),
  which silently requires `openpyxl`. Neither
  `pyproject.toml.dependencies` nor `requirements.txt` lists it. Fresh
  installs will fail at first EDGAR-using script with `ImportError:
  Missing optional dependency 'openpyxl'`.
- **`run_all.py` defines 43 steps but TECHNICAL_MANUAL §10 / §4.5 say
  "all 41 steps".** Counting the source: COMPONENT_A 28 + COMPONENT_B 5
  + COMPONENT_C 9 + COMPONENT_D 1 = **43**. The doc is stale on this
  count (Quick_Start.md correctly says 43).
- **Component D shape assertion** at lines 95-97 hardcodes 201 rows; this
  is correct for the intended 1900–2100 span but means any future change
  to the time axis requires a code edit.
- **HIST_END=2014 is an empirically chosen constant** (`constants.py`
  line 48). HANDOFF Round C6 explicitly verifies it against RCMIP scenario
  divergence, which is good, but means a future RCMIP release with
  different splice could silently invalidate plots.
- **Scenario tag ambiguity for rice Option A.** Quick_Start.md and the
  `paths.py` define `PLUM_RICE_OPT_A_ZIP` and `PLUM_RICE_OPT_B_ZIP` but
  only Option B is integrated. Option A is **staged for forward
  compatibility** (TECH §16.1 lists it as an "easy win"). Possible
  confusion if a downstream integrator chooses Option A by mistake.
- **Codebase uses `from src.shared …` imports**, but `pyproject.toml`
  declares `src` as a package literally named `"src"`. After
  `pip install -e .`, both `import src.shared` and (potentially) other
  packages named `src` would clash. TECH §16.5 correctly identifies this
  as future packaging cleanup.
- **No `.gitignore` in SOURCE_ONLY tree** (only in FULL per `diff -rq`).
  This is a packaging slip — a fresh git init without the FULL
  `.gitignore` could accidentally commit `inputs/`, `outputs/`, and
  `archive/`.

### 13.4 Hardcoded paths

After Round 15, paths are routed through `src/shared/paths.py`. The
remaining "hardcoded" surface is the **filenames** within each input
directory (`rcmip-emissions-annual-means-v5-1-0.csv`, `natural.csv`,
`Production_Crops_Livestock_E_All_Data.csv`, `EDGAR_CH4_1970_2024.xlsx`,
`Livestock_counts.txt`, `plum_crop_s1.csv`, `lpjg_<var>.out_<tag>.gz`).
Changing input file names requires a `paths.py` edit. Given the framework
likely produces LPJ-GUESS outputs with different naming conventions, this
is a **friction point for integration**.

### 13.5 Literal TODO/FIXME in the codebase

Grep for `TODO|FIXME|XXX|HACK` across `src/` and `tests/`: **zero
matches**. The only TODO is in `TECHNICAL_MANUAL.md` line 1984
(matplotlib backend standardization; classified as §15.6 above).

---

## 14. Open questions

These are questions the docs do not answer, listed in approximate priority
for the coupled-framework integration:

1. **What is IMOGEN's actual input-file format?** Quick_Start.md
   explicitly defers this to a follow-up. Without it, the Python
   pipeline's terminal output schema is the author's guess at what
   IMOGEN wants. Authoritative answer should come from
   `Imogen-controller/` or `IMOGENCXX/` (different subagents).
2. **Does IMOGEN need spatially-resolved emissions?** The Python pipeline
   produces global annual scalars only. If IMOGEN consumes per-region or
   per-grid forcing, the pipeline is **insufficient as drop-in** (TECH
   §16.3).
3. **Is the C++ Intermediary called once per simulation or per-coupling
   iteration?** The Python pipeline is a single-shot batch; if the
   framework iterates, a refactor to expose per-step callable functions
   is needed (see §11 step 3b).
4. **Does the framework's PLUM output match `inputs/plum/plum_crop_s1.csv`
   format?** The Python pipeline expects PLUMv2 s1 output specifically;
   if `Imogen-controller/PLUM-driver` produces a different layout, an
   adapter is needed.
5. **Where do the LPJ-GUESS `.gz` files come from in the coupled
   framework?** Are they produced by `RegridLPJG/` or
   `landsymm_imogen_setup/`? File-naming conventions need cross-checking
   against the Python pipeline's expectations
   (`lpjg_<var>.out_<tag>.gz`).
6. **Is the Python pipeline's "OPTION B" CH₄ rice methodology compatible
   with the C++ Intermediary's choice?** Option A is staged but not
   integrated (TECH §16.1); the C++ might use a different convention.
7. **Are the CH₄/N₂O scenarios period boundary discontinuities (HANDOFF
   §2.5: 22 Mt CH₄ at 2020, 117 Gg N₂O at 2020) acceptable?** They are
   methodologically intentional but might break smooth-trajectory
   assumptions in IMOGEN driver code.
8. **What date span does IMOGEN need?** The Python pipeline produces
   1900–2100. If IMOGEN needs longer (1750–2300, RCMIP's full extent) the
   pipeline's coverage is insufficient.
9. **Are the 5 SSP-RCP scenarios the canonical scenario set for the
   coupled framework?** If the framework uses other scenarios (e.g. RCP-
   only, AR6 illustrative pathways), the Python pipeline's `SCENARIOS`
   constant is too narrow.
10. **Does the framework have a CO₂ Tier-1 inventory the Python pipeline
    should also consume?** The Python side currently uses RCMIP EFOS
    unchanged; if the framework provides bottom-up CO₂, the integration
    framing (Option A) might need to change.
11. **Should the Python pipeline be vendored into the framework or kept
    as a sibling package called via subprocess?** Affects packaging,
    licensing (MIT here), and operational ownership.
12. **Will the Python pipeline's `outputs/imogen_inputs/` placement
    survive integration?** The C++ Intermediary almost certainly writes
    to a different location; either the Python output path is rewired
    (env var `OUT_IMOGEN_INPUTS` override) or the framework's
    `Imogen-controller` is rewired to read from the Python location.
13. **What runtime environment does the framework run in?** The Python
    pipeline needs Python ≥ 3.10, pandas ≥ 2.0, and `zcat` on PATH
    (notably **not** plain Windows). If the framework is HPC-batch, this
    needs verification.

---

*Report written to:
`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm/_phase2_findings/06_intermediary_py.md`*
