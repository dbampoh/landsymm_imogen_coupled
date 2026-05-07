# IMOGEN GHG Controller

**A pipeline for constructing complete annual greenhouse-gas emission trajectories (1900–2100, five SSP-RCP scenarios) for use as forcing inputs to the IMOGEN climate emulator.**

This codebase combines an independent IPCC Tier-1 agricultural inventory (anthropogenic CH₄ and N₂O), the LPJ-GUESS dynamic global vegetation model output (natural CH₄, N₂O, and CO₂), and the published RCMIP/CEDS anthropogenic CO₂ trajectory, to produce internally consistent integrated emission trajectories validated against the published Global Methane Budget, Global Nitrogen Budget, and Global Carbon Budget.

---

## Table of Contents

1. [What this project produces](#1-what-this-project-produces)
2. [Pipeline overview](#2-pipeline-overview)
3. [Quick start](#3-quick-start)
4. [Repository structure](#4-repository-structure)
5. [Inputs — what to obtain and where to put it](#5-inputs--what-to-obtain-and-where-to-put-it)
6. [Outputs — what the pipeline produces](#6-outputs--what-the-pipeline-produces)
7. [Running individual components](#7-running-individual-components)
8. [Configuration via environment variables](#8-configuration-via-environment-variables)
9. [Reproducibility and tests](#9-reproducibility-and-tests)
10. [Scientific findings (headline results)](#10-scientific-findings-headline-results)
11. [License and citation](#11-license-and-citation)
12. [Further reading](#12-further-reading)

---

## 1. What this project produces

The terminal output of the pipeline is a set of CSV files at `outputs/imogen_inputs/`, one per SSP-RCP scenario, each containing 1900–2100 annual emission values for CH₄, N₂O, and CO₂ (decomposed into anthropogenic, natural, and total components) ready for ingestion by the IMOGEN climate emulator.

Each scenario file (e.g. `imogen_inputs_SSP2-4.5.csv`) has these columns:

| Column | Unit | Description |
|---|---|---|
| `Year` | — | 1900–2100 (201 rows) |
| `CH4_anthro_Mt` | Mt CH₄/yr | Tier-1-substituted anthropogenic CH₄ (CEDS/RCMIP non-agricultural sectors + our IPCC Tier-1 agricultural inventory) |
| `CH4_natural_Mt` | Mt CH₄/yr | LPJ-GUESS natural CH₄ (wetland + GMB IFW correction − GMB DCC correction) |
| `CH4_total_Mt` | Mt CH₄/yr | sum of the above |
| `N2O_anthro_Mt` | Mt N₂O/yr | Tier-1-substituted anthropogenic N₂O |
| `N2O_natural_Mt` | Mt N₂O/yr | LPJ-GUESS natural N₂O (soil + fire combined) |
| `N2O_total_Mt` | Mt N₂O/yr | sum |
| `CO2_EFOS_Mt` | Mt CO₂/yr | RCMIP "Emissions\|CO2\|MAGICC Fossil and Industrial" |
| `CO2_NEE_Mt` | Mt CO₂/yr | LPJ-GUESS Net Ecosystem Exchange (full anthropogenic LULC + natural land response) |
| `CO2_total_Mt` | Mt CO₂/yr | atmospheric source = EFOS + NEE |

Plus a long-format combined file `imogen_inputs_all_scenarios_long.csv` for users who prefer that representation.

---

## 2. Pipeline overview

The pipeline consists of four components executed in sequence:

```
┌──────────────────────────────────────────────────────────────────────┐
│  Component A — Anthropogenic Agricultural Inventory                  │
│    Historical (1970–2020): IPCC 2019 Refinement Tier 1 applied to    │
│    FAO production data, country level → 6 sectors                    │
│    Scenarios (2020–2100): same Tier 1 equations applied to PLUMv2    │
│    SSP-RCP land-use projections                                      │
│    RCMIP substitution: replace CEDS/CMIP6 agricultural sectors with  │
│    our independent bottom-up estimates                               │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Component B — LPJ-GUESS Natural Emissions                           │
│    Historical (1901–2020): stream raw LPJ-GUESS .gz files, aggregate │
│    62,538 grid cells × 120 years to global annual totals             │
│    Scenarios (2021–2100): same for each SSP-RCP variant              │
│    Combined CH₄ derivation (wetland ± GMB IFW/DCC corrections)       │
│    FAIR-ERF natural baseline extraction (for comparator)             │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Component C — Integration & Validation                              │
│    Integrated trajectories: anthro + natural per gas                 │
│    External comparators: GMB 2025 / GNB 2024 / GCB 2025 top-down     │
│    Hybrid full-trajectory comparator (Option B): budget anchors in   │
│    1980-2020, RCMIP+FAIR-ERF outside (PRIMARY VALIDATION)            │
│    Conventional comparator (Option A): RCMIP+FAIR-ERF throughout     │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Component D — IMOGEN Input Export                                   │
│    Final per-scenario IMOGEN-ready CSVs in wide format               │
│    Plus combined long-format CSV for convenience                     │
└──────────────────────────────────────────────────────────────────────┘
```

Each component is **independently runnable** — you do not need to re-run earlier components if their outputs are already on disk. The orchestrator `run_all.py` simply executes them in dependency order.

---

## 3. Quick start

### 3.1 Clone and install

```bash
git clone <your repo URL>
cd imogen_ghg_controller
pip install -r requirements.txt
```

The pipeline has minimal dependencies: `pandas`, `numpy`, `matplotlib`, and `pyarrow` (for fast CSV reading). All standard scientific Python packages.

### 3.2 Obtain inputs

The `inputs/` directory is gitignored because the raw data is large (~1.5 GB for LPJ-GUESS files). See [§5](#5-inputs--what-to-obtain-and-where-to-put-it) for full instructions on what to obtain and where to put it. In summary:

- FAO data → `inputs/fao/` (downloaded from FAOSTAT)
- PLUMv2 scenario outputs → `inputs/plum/` (from your modeller)
- LPJ-GUESS .gz files → `inputs/lpjg/historical/` and `inputs/lpjg/scenarios/<ssp>/` (from your modeller)
- RCMIP CSV → `inputs/rcmip/` (from rcmip.org)
- FAIR-ERF natural baseline → `inputs/fair_erf/natural.csv` (from FAIR repository)
- Reference PDFs → `inputs/reference_pdfs/` (IPCC + budget papers)

### 3.3 Run the full pipeline

```bash
python run_all.py
```

Outputs land in `outputs/component_a/`, `outputs/component_b/`, `outputs/component_c/`, and finally `outputs/imogen_inputs/`. Total runtime ~25 min on a modern laptop, dominated by the LPJ-GUESS streaming (~15 min for the historical pass and ~10 min for the five scenarios).

### 3.4 Run individual components

```bash
python run_all.py --component A         # just anthropogenic
python run_all.py --component B         # just natural
python run_all.py --component C         # just integration
python run_all.py --component D         # just IMOGEN export
python run_all.py --component A B       # A then B
python run_all.py --skip-plots          # processing only, no figures
python run_all.py --dry-run             # print steps without executing
```

Or invoke any individual script directly:

```bash
python src/component_b_natural/historical/lpjg_historical_processing.py
python src/component_c_integration/hybrid_comparator_processing.py
```

---

## 4. Repository structure

```
imogen_ghg_controller/
│
├── README.md                      ← you are here
├── HANDOFF.md                     ← consolidated technical handoff
├── LICENSE                        ← MIT
├── requirements.txt               ← Python dependencies
├── pyproject.toml                 ← pip install -e . metadata
├── .gitignore                     ← excludes inputs/, outputs/, archive/
│
├── run_all.py                     ← single-command pipeline driver
│
├── src/                           ← all canonical pipeline source
│   ├── shared/                    ← cross-component helpers
│   │   ├── __init__.py
│   │   ├── constants.py           ← scenarios, unit conversions, time-period boundaries
│   │   ├── plot_style.py          ← scenario palette, axis-styling, smoothing helpers
│   │   ├── budget_refs.py         ← GMB/GNB/GCB observation-constrained values
│   │   └── paths.py               ← path resolution (project root, inputs/, outputs/)
│   │
│   ├── component_a_anthropogenic/
│   │   ├── historical/            ← 6 sector pipelines (CH4_EF, CH4_MM, CH4_rice,
│   │   │                            N2O_MM, N2O_MS, N2O_synfert) × {processing, plotting}
│   │   ├── scenarios/             ← 5 sector scenario pipelines + livestock anchor
│   │   └── rcmip_substitution/    ← Tier-1 substitution + comparison plots
│   │
│   ├── component_b_natural/
│   │   ├── historical/            ← LPJ-GUESS streaming + plotting (1901-2020)
│   │   ├── scenarios/             ← LPJ-GUESS streaming for the 5 scenarios
│   │   └── full_trajectory/       ← Combined CH4 / FAIR helper + extended plot
│   │
│   ├── component_c_integration/   ← integration, comparators, validation (full-trajectory)
│   │
│   └── component_d_imogen_export/ ← terminal IMOGEN-input CSV exporter
│
├── inputs/                        ← raw inputs (gitignored; obtain separately)
│   ├── README.md                  ← detailed acquisition instructions
│   ├── fao/                       ← FAOSTAT data
│   ├── plum/                      ← PLUMv2 scenario outputs
│   ├── lpjg/                      ← LPJ-GUESS .gz files
│   │   ├── historical/
│   │   └── scenarios/
│   ├── rcmip/                     ← RCMIP CSV
│   ├── fair_erf/                  ← natural.csv
│   └── reference_pdfs/            ← IPCC + budget papers
│
├── outputs/                       ← all generated outputs (gitignored)
│   ├── component_a/{data,figures,summaries}/
│   ├── component_b/{data,figures,summaries}/
│   ├── component_c/{data,figures,summaries}/
│   └── imogen_inputs/             ← final IMOGEN-ready CSVs
│
├── docs/                          ← scientific documentation
│   ├── methodology.md
│   ├── component_A.md
│   ├── component_B.md
│   ├── component_C.md
│   ├── component_D.md
│   ├── budget_references.md
│   └── figures_gallery/
│
├── tests/                         ← reproducibility and validation tests
│   ├── test_unit_conversions.py
│   ├── test_co2_option_a_validation.py
│   └── test_imogen_export_schema.py
│
└── archive/                       ← superseded scripts and prior handoffs (gitignored)
    ├── README.md                  ← describes what's archived and why
    ├── superseded_lpjg_scripts/
    ├── superseded_anthropogenic_worldrow_aggregation/
    ├── scratch_session_scripts/
    └── prior_session_handoffs/
```

### 4.1 Why historical / scenarios / full-trajectory subdirectories in Components A and B

- **Component A** has methodologically distinct historical and scenario pipelines: historical uses FAO production data 1970–2020, scenarios use PLUMv2 land-use outputs 2020–2100. The Tier-1 equations are identical but the activity data, livestock anchoring, and missing-species handling differ.
- **Component B** has separate historical and scenario streamers because LPJ-GUESS produced separate `.gz` output files for the historical run (1901–2020, HILDA+v2 forcing) and each SSP-RCP scenario run (2021–2100, PLUMv2 forcing). The full-trajectory subdirectory holds the combined-CH₄/FAIR helper and the extended 1901–2100 plot.
- **Component C** is intrinsically full-trajectory — every script operates on the complete 1900–2100 window — so no subdirectory split is needed.

### 4.2 Naming conventions

- `*_processing.py`: produces CSV and TXT outputs into `outputs/component_X/data/` and `summaries/`.
- `*_plotting.py`: reads from data directory, produces PNG into `outputs/component_X/figures/`.
- Scenario pipeline scripts in Component A are numbered `00_` through `05_` to indicate execution order (livestock anchor must run first).

---

## 5. Inputs — what to obtain and where to put it

The `inputs/` directory is gitignored. Before running the pipeline, populate it as follows.

### 5.1 FAO sectoral inventory data → `inputs/fao/`

Download the following bulk-download CSVs from FAOSTAT (https://www.fao.org/faostat/en/#data) and place them in `inputs/fao/`:

- `Production_Crops_Livestock_E_All_Data.csv` — production statistics (used as IPCC Tier-1 activity data)
- `Emissions_Totals_E_All_Data.csv` — FAO's own emission estimates (used for benchmarking)
- `Inputs_FertilizersNutrient_E_All_Data.csv` — fertilizer input data (used for N₂O syn-fert sector)

These are publicly downloadable. The CSVs are wide-format with one row per (Country × Item × Element × Unit) and one column per year.

### 5.2 PLUMv2 scenario activity data → `inputs/plum/`

The PLUMv2 land-use model outputs for the five SSP-RCP scenarios are project-internal. Obtain `plum_crop_s1.csv` and the rice-cultivation scenario zips from the modeller. Place into `inputs/plum/`.

### 5.3 LPJ-GUESS dynamic global vegetation model outputs → `inputs/lpjg/`

The LPJ-GUESS run for this project produced 18 `.gz` files totalling ~1.5 GB.

```
inputs/lpjg/
├── historical/
│   ├── lpjg_cflux.out_historical.gz       (~120 MB)
│   ├── lpjg_mch4.out_historical.gz        (~64 MB)
│   └── lpjg_ngases.out_historical.gz      (~138 MB)
└── scenarios/
    ├── ssp1_rcp26/{cflux,mch4,ngases}.out_ssp1rcp26.gz
    ├── ssp2_rcp45/...
    ├── ssp3_rcp70/...
    ├── ssp4_rcp60/...
    └── ssp5_rcp85/...
```

These files are **available on request from the modeller**. They are too large to include in a public archive, so users who wish to reproduce the natural-emission pipeline must obtain them separately. The handoff document describes the file format and verifies the unit conventions.

### 5.4 RCMIP emission scenarios → `inputs/rcmip/`

Download `rcmip-emissions-annual-means-v5-1-0.csv` from https://rcmip.org/ (the Reduced Complexity Model Intercomparison Project) and place into `inputs/rcmip/`. This file contains historical and scenario emissions for all greenhouse gases under all CMIP6 SSPs.

### 5.5 FAIR-ERF natural baseline → `inputs/fair_erf/`

Place `natural.csv` (the FAIR-ERF v1.3 natural-emission baseline from Smith et al. 2018 GMD) into `inputs/fair_erf/`. This file is bundled with the FAIR climate emulator distribution.

### 5.6 EDGAR sector emission inventories → `inputs/edgar/`

EDGAR provides an independent global anthropogenic emission inventory used by 17 Component A scripts as a benchmark and for sector/total proportioning in scenario plots. Download from https://edgar.jrc.ec.europa.eu/ and place into `inputs/edgar/`:

- `EDGAR_CH4_1970_2024.xlsx` — NEW EDGAR 2025 release for methane sectors (used by 8 CH₄ scripts)
- `EDGAR_N2O_1970_2024.xlsx` — NEW EDGAR 2025 release for nitrous oxide sectors (used by 8 N₂O scripts)
- `essd_ghg_data_emiss.xlsx` — OLD ESSD release (used **only** by `n2o_synfert_processing.py` because the OLD release has a dedicated 4D11 "Synthetic Fertilizers" sub-category that the NEW release aggregates into 3.C.4 + 3.C.5)
- `IEA_EDGAR_CO2_1970_2024.xlsx` — IEA-EDGAR CO₂ release (currently NOT used; staged for forward compatibility)

EDGAR is used (a) as a benchmark column added to each historical sector global CSV, and (b) for sector/total proportioning in scenario plots that allocates RCMIP CMIP6 totals to specific sectors. The substitution itself does NOT use EDGAR — it uses RCMIP's own AFOLU sub-aggregation.

### 5.7 Reference PDFs → `inputs/reference_pdfs/`

Optional but recommended. Place the IPCC Tier-1 source PDFs and the global budget papers here for convenience. The pipeline does not parse PDFs at runtime — these are for reader/reviewer reference only.

- `19R_V4_Ch05_Cropland.pdf` — IPCC 2019 Refinement V4 Ch5 (Cropland)
- `19R_V4_Ch10_Livestock.pdf` — V4 Ch10 (Livestock)
- `19R_V4_Ch11_Soils_N2O_CO2.pdf` — V4 Ch11 (Soils)
- `V4_10_Ch10_Livestock.pdf` — IPCC 2006 GL V4 Ch10
- `essd-17-1873-2025_GMB.pdf` — Saunois et al. 2025 GMB
- `essd-16-2543-2024_GNB.pdf` — Tian et al. 2024 GNB
- `essd-17-965-2025_GCB.pdf` — Friedlingstein et al. 2025 GCB

---

## 6. Outputs — what the pipeline produces

The `outputs/` directory is gitignored because outputs are fully reproducible from inputs + source. After a successful run:

### 6.1 `outputs/component_a/`

- `data/` (~38 CSVs): per-sector global / country / regional totals (e.g. `ch4_ef_global.csv`, `n2o_synfert_country.csv`); scenario projections; `rcmip_substitution_ch4.csv` and `rcmip_substitution_n2o.csv` (the integrated anthropogenic trajectories used by Component C)
- `figures/` (~13 PNGs): per-sector trend plots, RCMIP comparison plots
- `summaries/`: brief text summaries

### 6.2 `outputs/component_b/`

- `data/`: `lpjg_{ch4,co2,n2o}_annual.csv` (historical); `_scenarios.csv` (per-SSP); `lpjg_ch4_combined_annual{,_scenarios}.csv` (with GMB IFW/DCC corrections); `fair_erf_natural_baseline.csv`
- `figures/`: `lpjg_historical_comparison.png` (4-panel historical), `lpjg_historical_scenario_comparison.png` (full 1901–2100)
- `summaries/`: budget comparison text, scenario summary

### 6.3 `outputs/component_c/`

- `data/`: `rcmip_co2.csv`; `integrated_emissions_{ch4,n2o,co2}.csv` (integrated trajectories); `external_comparators_{ch4,n2o,co2}.csv` (top-down budget references); `hybrid_comparator_{ch4,n2o,co2}.csv` (Option B); `conventional_comparator_{ch4,n2o,co2}.csv` (Option A)
- `figures/`: `integrated_emissions_comparison.png`; `external_comparators_comparison.png`; `hybrid_comparator_comparison.png`; `conventional_comparator_comparison.png`
- `summaries/`: per-comparator validation text files

### 6.4 `outputs/imogen_inputs/`

The final terminal output:

- `imogen_inputs_SSP1-2.6.csv`, `imogen_inputs_SSP2-4.5.csv`, `imogen_inputs_SSP3-7.0.csv`, `imogen_inputs_SSP4-6.0.csv`, `imogen_inputs_SSP5-8.5.csv` — wide-format per-scenario IMOGEN-ready CSVs (201 rows × 10 columns each)
- `imogen_inputs_all_scenarios_long.csv` — long-format combined file (3015 rows × 7 columns)

---

## 7. Running individual components

If you only want to refresh part of the pipeline, invoke any script directly. All scripts use `os.environ.get('OUT_DIR', <default>)` and similar patterns, so you can override paths if needed.

```bash
# Just rebuild the hybrid comparator and its plot
python src/component_c_integration/hybrid_comparator_processing.py
python src/component_c_integration/hybrid_comparator_plotting.py

# Just rebuild the IMOGEN inputs (Component D)
python src/component_d_imogen_export/imogen_inputs_export.py

# Just rebuild a single Component A sector
python src/component_a_anthropogenic/historical/ch4_ef_processing.py
python src/component_a_anthropogenic/historical/ch4_ef_plotting.py
```

---

## 8. Configuration via environment variables

For every script, the input and output directories can be overridden via environment variables:

| Environment variable | Default | Purpose |
|---|---|---|
| `IMOGEN_GHG_ROOT` | auto-discovered project root | Override project root entirely |
| `OUT_DIR` | component-specific data or figures dir | Override output directory for the script |
| `DATA_DIR` | component-specific data dir | Override input data directory (for plotting scripts) |
| `IN_DIR` | inputs/lpjg/historical | Component B historical streamer source |
| `DATA_DIR_LPJ` | outputs/component_b/data | Component C reading LPJ outputs |
| `DATA_DIR_RCMIP` | outputs/component_a/data | Component C reading anthropogenic outputs |

So for example you can run with custom paths:
```bash
OUT_DIR=/tmp/test_out python src/component_c_integration/integrated_emissions_processing.py
```

---

## 9. Reproducibility and tests

The pipeline is fully deterministic — no random seeds, no stochastic methods. Re-running with identical inputs produces bit-identical outputs.

```bash
pytest tests/                        # run all tests
pytest tests/test_unit_conversions.py
```

Tests cover:
- Unit-conversion correctness (e.g. PgC ↔ MtCO2, TgN ↔ TgN2O)
- Component C "Option A" validation against the GCB 2025 partition
- IMOGEN export schema check (correct columns, correct row counts, no NaNs in expected columns)

---

## 10. Scientific findings (headline results)

For full numerical detail see `HANDOFF.md` §8.11 and the per-comparator summary text files in `outputs/component_c/summaries/`. Brief headlines:

**Historical-period validation** (versus GMB 2025, GNB 2024, GCB 2025):
- CO₂: within ±1σ of GCB partition for all six decades 1960s through 2014–2023 (strongest external validation)
- CH₄: within range for 2000-2009; just above upper bound for 2010-2019; just below lower bound for 2020 (LPJ-GUESS wetland CH₄ underestimate)
- N₂O: within range for all reported periods (1997, 2010-2019, 2020), with a small ~1-2 Mt low bias

**End-of-century divergence** (the climate-feedback signal): Across all five scenarios, our LPJ-GUESS-coupled integrated trajectories diverge from the conventional climate-emulator framing (constant FAIR-ERF natural baseline). End-of-century deltas under SSP2-4.5: CH₄ +350 Mt, N₂O +9.7 Mt, CO₂ NEE −2.68 Pg C/yr. SSP5-8.5 reaches CH₄ +378 Mt, N₂O +7.6 Mt, CO₂ NEE −5.06 Pg C/yr (largest land sink under maximum CO₂ fertilization). These are precisely the natural-emission climate-feedback signals that conventional climate-emulator framings cannot represent — the central scientific value-add of this pipeline.

---

## 11. License and citation

Released under the **MIT License** (see `LICENSE`).

If you use this pipeline or its outputs in published work, please cite the contributing data sources:

- **IPCC 2019 Refinement** to the 2006 IPCC Guidelines for National Greenhouse Gas Inventories, Volume 4: Agriculture, Forestry and Other Land Use
- **Saunois et al. 2025**, "Global Methane Budget 2000–2020", *Earth System Science Data* 17, 1873–1958 (GMB)
- **Tian et al. 2024**, "Global Nitrogen Budget", *Earth System Science Data* 16, 2543–2604 (GNB)
- **Friedlingstein et al. 2025**, "Global Carbon Budget 2025", *Earth System Science Data* 17, 965–1039 (GCB)
- **Smith et al. 2018**, "FAIR v1.3 Natural Baseline", *Geoscientific Model Development* 11, 2273–2297
- **Nicholls et al. 2020**, RCMIP Phase 2, https://rcmip.org/
- The LPJ-GUESS DGVM (Smith et al., earlier publications) — citation to be added by the modeller

---

## 12. Further reading

- `HANDOFF.md` — comprehensive technical handoff covering every methodological decision made across the project's three chat sessions
- `docs/methodology.md` — unified methodology document (cross-references the HANDOFF)
- `docs/component_A.md` through `docs/component_D.md` — per-component deep dives
- `docs/budget_references.md` — citation tables and reference values for GMB / GNB / GCB / FAIR-ERF
- `archive/README.md` — what's archived and why

For questions, contact the project maintainer or open a GitHub issue.
