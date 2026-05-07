# IMOGEN GHG Controller — Technical Manual

**Version 1.0** · For codebase version 0.1.0 · 2026

---

## Preface

This is the comprehensive technical manual for the IMOGEN GHG Controller pipeline. It is intended for three audiences:

1. **Scientific users** who want to reproduce, extend, or adapt the pipeline for their own work
2. **Software maintainers** who need to debug, modify, or migrate the codebase
3. **Reviewers and collaborators** who need to understand methodological choices in depth

This manual is **complementary** to two other documents in the repository:

- **`README.md`** — quick-start oriented, written for first-time users who want to get running fast
- **`HANDOFF.md`** — chronological record of every methodological decision made across the project's three chat sessions, with bug fixes, validation results, and iteration history

The manual goes beyond both of these by (a) explaining the architectural choices, (b) documenting every script's interface and dependencies, (c) providing detailed troubleshooting recipes, and (d) identifying open issues and opportunities for further development.

If you are reading this for the first time, work through Sections 1–4 sequentially. After that, Sections 5–11 can be read out of order as reference material. Section 12 (issues and opportunities) is the most important part for anyone planning to extend the work.

---

## Table of Contents

1. [Project context and scientific goals](#1-project-context-and-scientific-goals)
2. [Architecture overview](#2-architecture-overview)
3. [Repository layout in detail](#3-repository-layout-in-detail)
4. [Installation and first run](#4-installation-and-first-run)
5. [The shared module — what's centralized and why](#5-the-shared-module--whats-centralized-and-why)
6. [Component A — anthropogenic agricultural inventory](#6-component-a--anthropogenic-agricultural-inventory)
7. [Component B — LPJ-GUESS natural emissions](#7-component-b--lpj-guess-natural-emissions)
8. [Component C — integration and validation](#8-component-c--integration-and-validation)
9. [Component D — IMOGEN export](#9-component-d--imogen-export)
10. [The pipeline driver: `run_all.py`](#10-the-pipeline-driver-run_allpy)
11. [Inputs catalogue and acquisition](#11-inputs-catalogue-and-acquisition)
12. [Outputs catalogue](#12-outputs-catalogue)
13. [Tests and reproducibility](#13-tests-and-reproducibility)
14. [Troubleshooting](#14-troubleshooting)
15. [Known issues and limitations](#15-known-issues-and-limitations)
16. [Opportunities for further development](#16-opportunities-for-further-development)
17. [Glossary](#17-glossary)
18. [Bibliography](#18-bibliography)

---

## 1. Project context and scientific goals

### 1.1 What this pipeline produces

The terminal output is a set of CSV files — one per SSP-RCP scenario, plus a combined long-format file — that contain annual greenhouse-gas emission trajectories from 1900 to 2100, decomposed into anthropogenic and natural components for CH₄, N₂O, and CO₂. These files are formatted for direct ingestion by the IMOGEN climate emulator (Huntingford & Cox 2000; Huntingford et al. 2010).

**Why this is non-trivial.** Climate emulators typically ingest emission scenarios from RCMIP (Reduced Complexity Model Intercomparison Project) or similar archives, which provide pre-built trajectories from Integrated Assessment Models (IAMs). Those trajectories carry IAM-internal assumptions about agricultural emissions and treat the natural carbon cycle as an internal computation rather than an external forcing. For studies that want to:

- impose specific natural-emission assumptions from a Dynamic Global Vegetation Model (DGVM) like LPJ-GUESS rather than using the emulator's internal carbon cycle;
- substitute their own agricultural emission inventory (e.g. an independent IPCC Tier-1 implementation) for the IAM-supplied agricultural sectors;
- explore how natural-emission climate feedbacks (e.g. CO₂-fertilization effects on the land sink, or wetland CH₄ response to warming) propagate into climate response;

the conventional pre-built emulator inputs are not directly suitable. This pipeline produces hand-crafted alternatives.

### 1.2 The three "components" and their independence

The pipeline is structured as four components, but they were originally conceived as three (A, B, C). Component D is a thin reformatting wrapper added at the end of the project to produce the IMOGEN-specific output schema.

- **Component A** — *Anthropogenic agricultural inventory*. Uses FAO production data and PLUMv2 land-use projections to build IPCC 2019 Refinement Tier-1 estimates for six agricultural sectors. Then performs a "Tier-1 substitution" into the published RCMIP CMIP6 anthropogenic emission trajectories: replace the CEDS-based agricultural sectors with our independent bottom-up estimates while leaving non-agricultural sectors untouched.

- **Component B** — *Natural emissions*. Streams raw LPJ-GUESS Dynamic Global Vegetation Model output files (text-format, gzip-compressed, ~1.5 GB total) and aggregates 62,538 grid cells × 120 years (historical) and × 80 years (each scenario) to global annual totals.

- **Component C** — *Integration and validation*. Combines anthropogenic + natural per gas to produce integrated trajectories. Builds three independent comparators: (i) external top-down references from the global budget papers; (ii) a hybrid full-trajectory comparator that anchors to budget values 1980-2020 and uses RCMIP+FAIR-ERF outside; (iii) a conventional comparator using RCMIP+FAIR-ERF throughout.

- **Component D** — *IMOGEN export*. Reformats Component C's integrated trajectories into the per-scenario wide-format CSVs that IMOGEN expects.

The components are **independently runnable**. You don't need Component A's outputs in the same session as Component B's. The pipeline driver `run_all.py` is a thin orchestrator over the components — each individual script underneath is a self-contained Python program with its own argparse-free interface.

### 1.3 The five SSP-RCP scenarios

Throughout the codebase, the canonical scenario list (defined in `src/shared/constants.py`) is:

```python
SCENARIOS = [
    'SSP1-2.6',   # Sustainability — green pathway
    'SSP2-4.5',   # Middle-of-the-road
    'SSP3-7.0',   # Regional rivalry
    'SSP4-6.0',   # Inequality
    'SSP5-8.5',   # Fossil-fuelled development
]
```

These are the same five scenarios used in the IPCC AR6 Working Group I report and CMIP6 ScenarioMIP. The scenarios diverge from a common historical period at year 2015 — see `HIST_END = 2014` in §5.

### 1.4 Time periods used throughout

Three boundary years matter:

| Year | Significance |
|---|---|
| 1900 | First year of the pipeline output (RCMIP historical extends back to 1750; we truncate at 1900) |
| 1970 | First year of the IPCC Tier-1 inventory (FAO data is reliable from 1961 but Tier-1 implementation was applied from 1970 for global coverage consistency) |
| 2014 | Last year before RCMIP scenarios begin diverging — the "historical-scenario boundary" |
| 2020 | First year of PLUMv2-driven scenario projections (Component A scenarios) |
| 2021 | First year of LPJ-GUESS scenario .gz files |
| 2100 | Terminal year |

So:
- 1900–1969 ("pre-inventory"): anthropogenic emissions come from RCMIP unchanged
- 1970–2014 ("historical"): our Tier-1 substitution applies; non-agri sectors still from RCMIP
- 2015–2100 ("scenario"): five separate trajectories per gas

### 1.5 What's deliberately NOT in the pipeline

For the avoidance of doubt:

- **No emulator runtime**. This pipeline produces input *forcing* trajectories. It does not run IMOGEN itself.
- **No grid-resolved outputs**. The pipeline outputs are global annual time series, not gridded. Component B aggregates LPJ-GUESS outputs from the gridded source to global totals.
- **No CO₂ Tier-1 inventory**. We do not have an independent CO₂ agricultural inventory; for CO₂, the anthropogenic side is the RCMIP `Emissions|CO2|MAGICC Fossil and Industrial` series (= EFOS) unchanged.
- **No CH₄ rice scenario projection**. The historical CH₄ rice cultivation Tier-1 estimate exists; the scenario projection was pending in prior session handoffs and is still pending. See §15 (Known Issues).
- **No uncertainty quantification beyond budget-paper σ**. We propagate GCB partition σ into the comparator uncertainty bands, but no Monte Carlo or parameter-sensitivity analyses are performed.
- **No interactive runtime / web UI**. The pipeline is batch-oriented: invoke a script, it produces files, done.

---

## 2. Architecture overview

### 2.1 The dependency graph

```
   ┌────────────┐
   │   inputs/  │  (FAO, PLUMv2, RCMIP, FAIR-ERF, LPJ-GUESS .gz)
   └─────┬──────┘
         │
   ┌─────┴───────────────────┬─────────────────┐
   │                         │                 │
   ▼                         ▼                 ▼
┌─────────────┐       ┌─────────────┐    ┌──────────┐
│ Component A │       │ Component B │    │ inputs   │
│ Tier-1 +    │       │ LPJ-GUESS   │    │ (RCMIP)  │
│ RCMIP sub   │       │ aggregation │    │          │
└──────┬──────┘       └──────┬──────┘    └────┬─────┘
       │                     │                │
       │ rcmip_substitution_ │ lpjg_*_annual_ │ rcmip_co2.csv
       │ {ch4,n2o}.csv       │ {scenarios}.csv│
       │                     │                │
       └──────────┬──────────┴────────────────┘
                  ▼
          ┌──────────────┐
          │ Component C  │  → integrated_emissions_{ch4,n2o,co2}.csv
          │ Integration  │  + comparators (3 types)
          └───────┬──────┘
                  │
                  ▼
          ┌──────────────┐
          │ Component D  │  → imogen_inputs_<SSP>.csv (×5)
          │ IMOGEN export│  + imogen_inputs_all_scenarios_long.csv
          └──────────────┘
```

### 2.2 Why components are decoupled via CSV files

Each component reads its inputs from CSV files on disk and writes its outputs to CSV files on disk. There is no in-memory pipeline runtime that orchestrates everything as Python objects. This is a deliberate design choice with several advantages:

1. **Inspectability**. Every intermediate step is a CSV that can be opened in a spreadsheet, diff'd against a previous run, or used as input to a different downstream tool.

2. **Granular re-runs**. If you change a single Component A sector script, you only need to re-run that script and downstream consumers — Components B and the unaffected parts of C don't need to re-run.

3. **No interpreter coupling**. Each script is a complete program. There's no application-level state to keep consistent.

4. **Reproducibility audit trail**. Every output file is a definite, dated artefact. Diffing the CSVs across two pipeline runs tells you exactly what changed.

The trade-off is that the CSV serialization step adds some I/O overhead and disk space usage. For this pipeline (~50 CSV files totalling ~10 MB excluding LPJ-GUESS streamed inputs), this is negligible compared to the compute time of streaming the 1.5 GB of raw LPJ-GUESS data.

### 2.3 The "shared" module — what's centralized

Five files in `src/shared/` contain everything that would otherwise be duplicated across multiple scripts:

| File | Purpose |
|---|---|
| `constants.py` | Canonical scenario list, time-period boundaries, unit-conversion factors, output CSV name dictionaries |
| `plot_style.py` | IPCC scenario colour palette, axis-styling helpers, smoothing functions, step-band/step-line drawing helpers |
| `budget_refs.py` | Numerical reference values from GMB 2025, GNB 2024, GCB 2025 + helper conversion functions |
| `paths.py` | Project-root auto-discovery + all input/output directory constants |
| `__init__.py` | Re-exports everything via `from src.shared import …` |

Without this module, the constants and helpers would be duplicated in ~50-line preludes at the top of every plotting script, leading to inevitable drift over time. With it, a single change to (say) the scenario palette or the GMB CH₄ reference values propagates uniformly across all consumers.

The bootstrap pattern at the top of each script ensures `from src.shared import …` works regardless of how the script is invoked or where the project lives on disk:

```python
import sys as _sys
from pathlib import Path as _Path
_PROJ_ROOT = _Path(__file__).resolve()
while _PROJ_ROOT.name and not (_PROJ_ROOT / 'src').is_dir():
    if _PROJ_ROOT.parent == _PROJ_ROOT:
        break
    _PROJ_ROOT = _PROJ_ROOT.parent
if str(_PROJ_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_PROJ_ROOT))
from src.shared.paths import (...)
```

This walks up from the script's own location until it finds a directory containing `src/`, then adds that to `sys.path`. The result: scripts run correctly whether invoked as `python src/.../foo.py` from the project root, as `python ../../foo.py` from a deeply nested directory, from an IDE, or from `run_all.py`.

### 2.4 Path resolution and relocation

The project is **fully relocatable**. You can place the `imogen_ghg_controller/` directory anywhere on disk:

```
~/Documents/Intermediary/imogen_ghg_controller/
~/code/research/imogen_ghg_controller/
/opt/projects/imogen_ghg_controller/
```

The bootstrap walk-up logic finds the project root regardless. All paths are computed relative to that. There is one optional override: setting the `IMOGEN_GHG_ROOT` environment variable explicitly bypasses auto-discovery. This is useful for testing scenarios where you want a specific project layout.

### 2.5 Determinism

The pipeline is fully deterministic. Specifically:

- No stochastic methods (no Monte Carlo, no bootstrap, no random sampling)
- No floating-point reductions whose order depends on dict iteration (Python 3.7+ dict-iteration order is itself deterministic, so this is automatic)
- LPJ-GUESS streaming reads files in a fixed order
- All `pandas.DataFrame` operations use deterministic implementations

Re-running with identical inputs produces bit-identical outputs. This was verified during the project's reproducibility round — see `archive/scratch_session_scripts/lpjg_*_annual_REPRO.csv` and the `repro/lpjg_repro.py` artefact (also archived).

---

## 3. Repository layout in detail

This section walks through every directory in the repository, top to bottom, explaining what's there and why.

### 3.1 Top-level files

```
imogen_ghg_controller/
├── README.md         (24 KB) — user-facing entry point with quick start
├── HANDOFF.md        (75 KB) — chronological technical record of all decisions
├── TECHNICAL_MANUAL.md       — this document
├── LICENSE                   — MIT License
├── .gitignore                — excludes inputs/, outputs/, archive/
├── requirements.txt          — pandas, numpy, matplotlib, pyarrow
├── pyproject.toml            — Python packaging metadata
└── run_all.py                — single-command pipeline driver
```

The three markdown documents serve different purposes and you should read them at different times:

- **README.md** is what you read first and what a new collaborator reads to get oriented. It's organized around tasks ("how do I install? how do I run? where do outputs go?").
- **HANDOFF.md** is what you read when you want to know *why* a particular decision was made. It's chronological and includes the iteration history with bug fixes documented inline.
- **TECHNICAL_MANUAL.md** (this document) is what you read when you want a complete reference. It's organized around the codebase structure and goes into detail on every script.

### 3.2 `src/` — all canonical pipeline source

This is the only directory that should be tracked in git. Everything else (`inputs/`, `outputs/`, `archive/`) is gitignored because it's either large, regeneratable, or non-canonical.

```
src/
├── __init__.py
├── shared/                            ~530 lines, 5 files
├── component_a_anthropogenic/        ~8800 lines, 30 files
│   ├── historical/                   12 files (6 sectors × {processing, plotting})
│   ├── scenarios/                    11 files (livestock anchor + 5 sectors × {processing, plotting})
│   └── rcmip_substitution/           3 files
├── component_b_natural/              ~1750 lines, 9 files
│   ├── historical/                   2 files
│   ├── scenarios/                    1 file
│   └── full_trajectory/              2 files
├── component_c_integration/          ~2700 lines, 9 files
└── component_d_imogen_export/        ~180 lines, 1 file
```

**Total**: 36 canonical Python scripts (excluding `__init__.py` files), ~14,000 lines of code.

### 3.3 `inputs/` — raw data (gitignored)

```
inputs/
├── README.md                         — describes acquisition for each sub-directory
├── fao/                              — FAOSTAT bulk-download CSVs
├── plum/                             — PLUMv2 land-use scenario outputs
├── lpjg/                             — LPJ-GUESS DGVM .gz output files
│   ├── historical/                   3 files
│   └── scenarios/<ssp>/              3 files × 5 SSPs = 15 files
├── rcmip/                            — RCMIP Phase 2 CSV
├── fair_erf/                         — FAIR-ERF natural baseline
└── reference_pdfs/                   — IPCC + budget paper PDFs (optional)
```

**Total size**: ~1.8 GB on disk after all inputs are populated.

The directory is gitignored because (a) FAOSTAT data is downloadable separately, (b) PLUMv2 and LPJ-GUESS data are project-internal and obtained from the modeller, (c) reference PDFs are large and easily re-obtained from publishers, (d) the resulting tracked-source repo would balloon to several GB if inputs were included.

The `inputs/README.md` file documents the acquisition path for every piece. See §11 of this manual for full details.

### 3.4 `outputs/` — generated outputs (gitignored)

```
outputs/
├── README.md
├── component_a/{data, figures, summaries}/
├── component_b/{data, figures, summaries}/
├── component_c/{data, figures, summaries}/
└── imogen_inputs/                    — TERMINAL OUTPUT
```

Each component has three sub-directories:
- `data/` — CSV files
- `figures/` — PNG plots
- `summaries/` — plain text summary files (no machine-readable schema)

**Total size**: ~10 MB on disk after a full pipeline run (figures are by far the largest contributors at ~1.5 MB each for the dense Component C plots).

The directory is gitignored because outputs are fully reproducible from `inputs/` + `src/`. Including them would (a) enable spurious git diffs from runtime variability in figure rendering, (b) bloat the tracked repo unnecessarily, (c) couple the canonical state to a specific run.

### 3.5 `docs/` — scientific documentation

```
docs/
├── methodology.md           — unified methodology summary
├── component_A.md           — anthropogenic component details
├── component_B.md           — natural component details
├── component_C.md           — integration component details
├── component_D.md           — IMOGEN export details
├── budget_references.md     — citation tables for GMB/GNB/GCB/FAIR-ERF
└── figures_gallery/         — symlinks to all PNGs for browsing
```

These are concise per-component summaries (~100-200 lines each), focused on the science. For the deeper engineering and code-level detail, see this manual.

The `figures_gallery/` directory contains symlinks to the PNGs in `outputs/component_*/figures/`. After a pipeline run, you can browse all 18 plots in one place.

### 3.6 `archive/` — superseded scripts and prior handoffs (gitignored)

```
archive/
├── README.md
├── superseded_lpjg_scripts/                          (8 files: older 264-line LPJ scripts)
├── superseded_anthropogenic_worldrow_aggregation/    (4 files: older 212-line variants)
├── scratch_session_scripts/                          (10 files: scratch n2o_*.py + lpjg_repro.py)
└── prior_session_handoffs/                           (4 files: SESSION_HANDOFF_*.md)
```

These are kept on disk for audit-trail and reference purposes but are not part of the active pipeline. The `archive/README.md` explains what's in each subdirectory and why it was archived. See §3.7 for the supersession history.

### 3.7 Supersession history

| What was superseded | By what | Why |
|---|---|---|
| `lpjg_historical_processing.py` v1 (264 lines) | `src/component_b_natural/historical/lpjg_historical_processing.py` (353 lines) | Better unit tracking, more comprehensive validation, better summary outputs |
| `lpjg_historical_plotting.py` v1 (280 lines) | `src/component_b_natural/historical/lpjg_historical_plotting.py` (455 lines) | Added IPCC scenario palette, segmented running-mean smoothing, GMB/GNB/GCB step-band overlays |
| `rcmip_comparison{1,2}_plotting.py` "World-row aggregation" (212 lines) | "Country-sum aggregation" version (274 lines) | Country-sum approach correctly handles country splits/merges over the FAO time series |
| Top-level scratch `n2o_*.py` and `lpjg_repro.py` | Canonical `lpjg_scenario_processing.py` | The canonical script handles all SSPs in one run; the scratch scripts processed them individually for debugging |

### 3.8 `tests/` — reproducibility tests

```
tests/
├── test_unit_conversions.py       — sanity check on PgC↔MtCO2, TgN↔TgN2O
├── test_co2_option_a_validation.py — verifies our CO2 atmospheric source matches GCB partition (key scientific test)
└── test_imogen_export_schema.py    — verifies Component D produces correctly-shaped CSVs
```

These are simple Python scripts with `def test_*()` functions. Run them with `pytest tests/` or invoke each directly with `python tests/test_*.py`. All three pass on the canonical state of the repository.


---

## 4. Installation and first run

### 4.1 System requirements

- **Python**: 3.10 or later (uses `from pathlib import Path` and other modern conveniences). 3.11+ recommended.
- **OS**: Linux, macOS, or Windows (the LPJ-GUESS streaming code uses `subprocess.Popen(['zcat', ...])` which requires `zcat` or `gunzip` to be on PATH; on Windows, install via WSL2 or Cygwin)
- **Disk**: ~2.5 GB free (1.8 GB for inputs, ~700 MB for working space and outputs)
- **RAM**: 4 GB minimum, 8 GB recommended (LPJ-GUESS streaming holds aggregation accumulators in memory; peak usage ~2 GB for the historical run)
- **CPU**: Single-threaded; no GPU. Total runtime ~25 min on a modern laptop, dominated by LPJ-GUESS streaming.

### 4.2 Installing dependencies

```bash
cd imogen_ghg_controller
pip install -r requirements.txt
```

Dependencies are minimal:

```
pandas>=2.0      # tabular data manipulation throughout
numpy>=1.24      # array operations, smoothing
matplotlib>=3.7  # all plotting
pyarrow>=14.0    # fast CSV reading (auto-used by pandas if installed)
```

Optionally install pytest for running tests:

```bash
pip install pytest
```

### 4.3 Verifying the install

After `pip install`, run:

```bash
python -c "import pandas, numpy, matplotlib; print('OK')"
```

Then verify the package itself imports correctly:

```bash
cd imogen_ghg_controller
python -c "from src.shared import SCENARIOS, PgC_to_MtCO2, SCEN_COLORS; \
           print('Scenarios:', SCENARIOS); print('PgC→MtCO2:', PgC_to_MtCO2)"
```

Expected output:
```
Scenarios: ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP4-6.0', 'SSP5-8.5']
PgC→MtCO2: 3666.6666666666665
```

### 4.4 Populating `inputs/`

Before running the pipeline, populate `inputs/` according to `inputs/README.md`. Briefly:

1. **FAO data** — download three CSVs from FAOSTAT and place in `inputs/fao/`
2. **PLUMv2 outputs** — obtain from project modeller; place in `inputs/plum/`
3. **LPJ-GUESS outputs** — obtain on request from project modeller; place in `inputs/lpjg/{historical,scenarios/<ssp>}/`
4. **RCMIP CSV** — download from rcmip.org and place in `inputs/rcmip/`
5. **FAIR-ERF natural.csv** — bundled with FAIR distribution; place in `inputs/fair_erf/`
6. **Reference PDFs** (optional) — IPCC + budget papers; place in `inputs/reference_pdfs/`

Verify with:

```bash
python -c "
from src.shared.paths import RCMIP_CSV, FAIR_ERF_CSV, LPJG_HIST_DIR, LPJG_SCEN_DIR
import os
print(f'RCMIP_CSV exists:    {os.path.isfile(RCMIP_CSV)}')
print(f'FAIR_ERF_CSV exists: {os.path.isfile(FAIR_ERF_CSV)}')
print(f'LPJG hist files:     {len(list(LPJG_HIST_DIR.glob(\"*.gz\")))}')
print(f'LPJG scen files:     {sum(len(list(d.glob(\"*.gz\"))) for d in LPJG_SCEN_DIR.iterdir())}')
"
```

Expected: all `True`, 3 LPJG hist files, 15 LPJG scen files.

### 4.5 First run

Recommended first run is the **dry-run** to verify all scripts are discoverable:

```bash
python run_all.py --dry-run
```

This prints all 41 steps of the pipeline without executing them. If you see "MISSING" warnings, your repository is incomplete.

Then a full run (only attempt this once `inputs/` is populated):

```bash
python run_all.py
```

This takes ~25 min on a modern laptop. Output goes to `outputs/` and progress is printed to stderr.

For incremental development, you'll usually run individual components:

```bash
python run_all.py --component D                 # just Component D (fast)
python run_all.py --component C D               # C then D
python run_all.py --component B C D --skip-plots  # skip plotting
python run_all.py --verbose                     # stream sub-process output
```

### 4.6 Running individual scripts

Every script under `src/` is independently runnable from the project root:

```bash
python src/component_d_imogen_export/imogen_inputs_export.py
python src/component_c_integration/hybrid_comparator_processing.py
python src/component_b_natural/historical/lpjg_historical_processing.py
```

Or from any subdirectory — the bootstrap walk-up logic finds the project root regardless:

```bash
cd src/component_c_integration
python integrated_emissions_processing.py
```

### 4.7 Setting up a fresh environment from scratch

If you're starting fresh on a new machine:

```bash
# Clone or extract the source tarball
tar -xzf imogen_ghg_controller_SOURCE_ONLY.tar.gz
cd imogen_ghg_controller

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate           # macOS/Linux
# or: .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize git (optional, but recommended for tracking changes)
git init
git add .
git commit -m "Initial commit"

# Populate inputs/ (follow inputs/README.md)
# ...

# Run pipeline
python run_all.py
```

---

## 5. The shared module — what's centralized and why

This is the most important module to understand because every script depends on it. Five files in `src/shared/`.

### 5.1 `src/shared/constants.py` — definitions

Contains four categories of constants:

#### Scenarios

```python
SCENARIOS = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP4-6.0', 'SSP5-8.5']

LPJG_TAG_MAP = {                # display label → LPJ-GUESS file tag
    'SSP1-2.6': 'ssp1rcp26',
    'SSP2-4.5': 'ssp2rcp45',
    'SSP3-7.0': 'ssp3rcp70',
    'SSP4-6.0': 'ssp4rcp60',
    'SSP5-8.5': 'ssp5rcp85',
}

SCEN_RCMIP_MAP = {              # display label → RCMIP scenario name
    'SSP1-2.6': 'ssp126',
    'SSP2-4.5': 'ssp245',
    'SSP3-7.0': 'ssp370',
    'SSP4-6.0': 'ssp460',
    'SSP5-8.5': 'ssp585',
}
```

The `LPJG_TAG_MAP` is needed because LPJ-GUESS output filenames use a different scenario tag format (`ssp1rcp26`, no separator) than our display labels (`SSP1-2.6`, dash separator).

#### Time-period boundaries

```python
HIST_END = 2014        # last year before RCMIP scenarios diverge
TIER1_START = 1970     # first year of IPCC Tier-1 inventory
SCENARIO_START = 2020  # first year of PLUMv2-driven scenarios
```

`HIST_END = 2014` is verified empirically against RCMIP data: scenario records share identical values up to 2014, then begin diverging at 2015 (verified during Round C6 of the project). This is used as the boundary for the "black historical / colored scenario" plot convention.

#### Unit-conversion factors

```python
PgC_to_MtCO2 = (44.0 / 12.0) * 1000.0         # = 3666.6667
TgN_to_TgN2O = 44.0 / 28.0                    # ≈ 1.5714
TgN2O_to_TgN = 28.0 / 44.0                    # ≈ 0.6364
```

These are derived from molar mass ratios: 44/12 for CO₂/C (carbon dioxide to carbon), 44/28 for N₂O/2N (nitrous oxide molecule contains 2 nitrogen atoms).

#### Output filename catalogues

```python
INTEGRATED_CSV_NAMES = {
    'CH4': 'integrated_emissions_ch4.csv',
    'N2O': 'integrated_emissions_n2o.csv',
    'CO2': 'integrated_emissions_co2.csv',
}
EXTERNAL_CSV_NAMES = {...}
HYBRID_CSV_NAMES = {...}
CONVENTIONAL_CSV_NAMES = {...}
```

These are referenced by the pipeline driver, the tests, and the comparator scripts to avoid typos in repeated filename strings.

### 5.2 `src/shared/plot_style.py` — visualization conventions

#### Scenario colours

```python
SCEN_COLORS = {
    'SSP1-2.6': '#1a9850',   # green  — sustainability
    'SSP2-4.5': '#2c7bb6',   # blue   — middle-of-the-road
    'SSP3-7.0': '#d7191c',   # red    — regional rivalry
    'SSP4-6.0': '#fdae61',   # orange — inequality
    'SSP5-8.5': '#762a83',   # purple — fossil-fuelled
}

HIST_COLOR = '#1a1a1a'        # black for historical period
CMP_COLOR = '#08519c'         # dark blue for comparator references
```

These match the IPCC AR6 Working Group I report's standard scenario palette.

#### Style dictionaries (passed to matplotlib via **kwargs)

```python
SC = '#cccccc'                                                 # spine colour
GK = dict(color='#cccccc', lw=0.5, ls='--', alpha=0.7)        # grid kwargs
TK = dict(fontsize=11, fontweight='bold',
          color='#1a1a1a', pad=6)                              # title kwargs
LK = dict(fontsize=9, color='#444444')                         # label kwargs
PK = dict(labelsize=8.5, colors='#666666')                     # tick params
```

Used at the top of every Component B and C plot:

```python
ax.set_title('CH4 — Historical', **TK)     # bold dark title
ax.set_xlabel('Year', **LK)                 # softer grey label
ax.tick_params(**PK)                        # consistent tick styling
```

#### Smoothing helpers

The most-used helper is `rmean_segmented`:

```python
def rmean_segmented(years, vals, hist_end=2014):
    """Compute rolling mean separately on the historical (years <= hist_end)
    and scenario (years > hist_end) segments, then concatenate."""
    yrs = np.asarray(years); vs = np.asarray(vals)
    out = np.full_like(vs, np.nan, dtype=float)
    mask_h = yrs <= hist_end
    mask_s = yrs > hist_end
    if mask_h.any():
        out[mask_h] = rmean(vs[mask_h])
    if mask_s.any():
        out[mask_s] = rmean(vs[mask_s])
    return out
```

The point: avoid stitching the running mean across the historical-scenario boundary. If you smooth across the boundary, the smoothed value at year 2014 contaminates years 2015-2018, which can hide or fabricate divergence behaviour at the splice point.

#### Step-band drawer

```python
def step_band_horizontal(ax, x_pairs, lo_arr, hi_arr,
                         color=CMP_COLOR, alpha=0.16, label=None):
    """Draw filled rectangles spanning each (year_start, year_end) period at
    the given (lo, hi) values."""
```

Used to overlay GMB / GNB / GCB period values (e.g. "2010-2019: 575 [553, 586] Mt CH4/yr") as horizontal bands on the time-series plots.

### 5.3 `src/shared/budget_refs.py` — observation-constrained references

Contains the canonical reference values from the three budget papers, verified by reading the source PDFs directly via `pdftotext -layout` during Round C4 of the project:

```python
# CH4 — GMB 2025 atmospheric inversions
GMB_CH4_PERIODS = [
    (2000, 2009, 543, 528, 578),   # year_start, year_end, best, lo, hi (Mt CH4/yr)
    (2010, 2019, 575, 553, 586),
    (2020, 2020, 608, 581, 627),
]

# N2O — GNB 2024 atmospheric inversions
GNB_N_PERIODS = [
    (1997, 1997, 15.4, 13.9, 16.7),    # in Tg N/yr
    (2010, 2019, 17.4, 15.8, 19.2),
    (2020, 2020, 17.0, 16.6, 17.4),
]

# CO2 — GCB 2025 Table 7 partition
GCB_PARTITION = [
    ('1960s',     1960, 1969, 3.0, 0.2, 1.6, 0.7, 1.2, 0.5),  # EFOS, σ, ELUC, σ, SLAND, σ
    ('1970s',     1970, 1979, 4.7, 0.2, 1.4, 0.7, 2.0, 0.8),
    # ...
    ('2014-2023', 2014, 2023, 9.7, 0.5, 1.1, 0.7, 3.2, 0.9),
]
```

Helper functions convert these into plot-ready Mt CH₄/yr or Mt N₂O/yr or Mt CO₂/yr units:

```python
def gmb_combined_ch4(period):
    """Return (best, lo, hi) in Mt CH4/yr."""
    _, _, best, lo, hi = period
    return best, lo, hi

def gnb_combined_n2o(period):
    """Return (best, lo, hi) in Mt N2O/yr (× 44/28 conversion)."""
    _, _, best_n, lo_n, hi_n = period
    return best_n * TgN_to_TgN2O, lo_n * TgN_to_TgN2O, hi_n * TgN_to_TgN2O

def gcb_atmospheric_source_co2(period):
    """Return (best, lo, hi) for atmospheric source = EFOS + ELUC - SLAND
    in Mt CO2/yr, with quadrature-summed uncertainty."""
    _, y0, y1, ef, sef, el, sel, sl, ssl = period
    src = ef + el - sl
    sig = (sef ** 2 + sel ** 2 + ssl ** 2) ** 0.5
    return src * PgC_to_MtCO2, (src - sig) * PgC_to_MtCO2, (src + sig) * PgC_to_MtCO2
```

The GCB CO₂ helper is the most important because it computes the "atmospheric source" quantity (EFOS + ELUC − SLAND) that our integrated trajectory should match. The 2014–2023 row gives 7.6 ± 1.24 Pg C/yr, which is the validation target for our Component C integration framing.

### 5.4 `src/shared/paths.py` — directory resolution

Auto-discovers the project root:

```python
def _find_project_root():
    env_root = os.environ.get('IMOGEN_GHG_ROOT')
    if env_root:
        return Path(env_root).resolve()
    # Walk up from this file location
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / 'src').is_dir() and (parent / 'README.md').is_file():
            return parent
    return Path(__file__).resolve().parents[2]

PROJECT_ROOT = _find_project_root()
```

Then defines all I/O paths relative to it:

```python
INPUTS_DIR  = PROJECT_ROOT / 'inputs'
OUTPUTS_DIR = PROJECT_ROOT / 'outputs'

FAO_DIR        = INPUTS_DIR / 'fao'
PLUM_DIR       = INPUTS_DIR / 'plum'
LPJG_HIST_DIR  = INPUTS_DIR / 'lpjg' / 'historical'
LPJG_SCEN_DIR  = INPUTS_DIR / 'lpjg' / 'scenarios'
RCMIP_DIR      = INPUTS_DIR / 'rcmip'
FAIR_ERF_DIR   = INPUTS_DIR / 'fair_erf'

OUT_A_DATA      = OUTPUTS_DIR / 'component_a' / 'data'
OUT_A_FIGS      = OUTPUTS_DIR / 'component_a' / 'figures'
OUT_A_SUMMARIES = OUTPUTS_DIR / 'component_a' / 'summaries'
# ... similar for B, C
OUT_IMOGEN_INPUTS = OUTPUTS_DIR / 'imogen_inputs'
```

And specific canonical file paths:

```python
RCMIP_CSV    = RCMIP_DIR    / 'rcmip-emissions-annual-means-v5-1-0.csv'
FAIR_ERF_CSV = FAIR_ERF_DIR / 'natural.csv'

FAO_PRODUCTION_CSV  = FAO_DIR / 'Production_Crops_Livestock_E_All_Data.csv'
FAO_EMISSIONS_CSV   = FAO_DIR / 'Emissions_Totals_E_All_Data.csv'
FAO_FERTILIZERS_CSV = FAO_DIR / 'Inputs_FertilizersNutrient_E_All_Data.csv'
PLUM_CROP_CSV       = PLUM_DIR / 'plum_crop_s1.csv'
```

Plus a utility:

```python
def ensure_output_dirs():
    """Create all output directories. Called at the start of any script that writes."""
    for d in (OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
              OUT_B_DATA, OUT_B_FIGS, OUT_B_SUMMARIES,
              OUT_C_DATA, OUT_C_FIGS, OUT_C_SUMMARIES,
              OUT_IMOGEN_INPUTS):
        d.mkdir(parents=True, exist_ok=True)
```

### 5.5 `src/shared/__init__.py` — re-exports

For convenience, importing from the package directly works:

```python
# Long form (always works):
from src.shared.paths import OUT_C_DATA, RCMIP_CSV
from src.shared.constants import SCENARIOS, HIST_END, PgC_to_MtCO2
from src.shared.plot_style import SCEN_COLORS, rmean_segmented, sax

# Short form (also works, equivalent):
from src.shared import (
    OUT_C_DATA, RCMIP_CSV,
    SCENARIOS, HIST_END, PgC_to_MtCO2,
    SCEN_COLORS, rmean_segmented, sax,
)
```

The current scripts use the long form for explicitness — you can always tell which sub-module a name comes from. Future scripts can use either.


---

## 6. Component A — anthropogenic agricultural inventory

This is the largest component (~8,800 lines, 30 files) because it implements six independent IPCC Tier-1 sectors.

### 6.1 Why six sectors

The 2019 Refinement to the 2006 IPCC Guidelines for National GHG Inventories defines Tier-1 methodologies for several agricultural sectors. We implement six:

| Gas | Sector | IPCC source | Activity data |
|---|---|---|---|
| CH₄ | Enteric fermentation (`ch4_ef`) | 2019 Refinement V4 Ch10 | FAO livestock |
| CH₄ | Manure management (`ch4_mm`) | 2019 Refinement V4 Ch10 | FAO livestock |
| CH₄ | Rice cultivation (`ch4_rice`) | 2019 Refinement V4 Ch5 | FAO rice harvested area |
| N₂O | Manure management (`n2o_mm`) | 2019 Refinement V4 Ch10 | FAO livestock |
| N₂O | Managed soils (`n2o_ms`) | 2019 Refinement V4 Ch11 | FAO livestock + crop residues |
| N₂O | Synthetic fertilizers (`n2o_synfert`) | 2019 Refinement V4 Ch11 | FAO fertilizer inputs |

Other sectors (e.g. CO₂ from forest management, CH₄/N₂O from biomass burning, N₂O from indirect emissions) are not covered. Some are minor; some require non-FAO data sources we don't have (e.g. for biomass burning we'd need GFED).

### 6.2 Sub-directory structure

```
src/component_a_anthropogenic/
├── historical/                      # 1970-2020
│   ├── ch4_ef_processing.py         (671 lines)
│   ├── ch4_ef_plotting.py           (340 lines)
│   ├── ch4_mm_processing.py         (787 lines)
│   ├── ch4_mm_plotting.py           (382 lines)
│   ├── ch4_rice_processing.py       (635 lines)
│   ├── ch4_rice_plotting.py         (343 lines)
│   ├── n2o_mm_processing.py         (612 lines)
│   ├── n2o_mm_plotting.py           (348 lines)
│   ├── n2o_ms_processing.py         (1119 lines)
│   ├── n2o_ms_plotting.py           (510 lines)
│   ├── n2o_synfert_processing.py    (518 lines)
│   └── n2o_synfert_plotting.py      (351 lines)
│
├── scenarios/                       # 2020-2100
│   ├── 00_scenario_livestock_anchor.py  (200 lines, runs first)
│   ├── 01_scenario_ch4_ef_processing.py
│   ├── 01_scenario_ch4_ef_plotting.py
│   ├── 02_scenario_ch4_mm_processing.py
│   ├── 02_scenario_ch4_mm_plotting.py
│   ├── 03_scenario_n2o_mm_processing.py
│   ├── 03_scenario_n2o_mm_plotting.py
│   ├── 04_scenario_n2o_synfert_processing.py
│   ├── 04_scenario_n2o_synfert_plotting.py
│   ├── 05_scenario_n2o_ms_processing.py
│   └── 05_scenario_n2o_ms_plotting.py
│
└── rcmip_substitution/
    ├── rcmip_substitution_processing.py   (substitutes Tier-1 into RCMIP)
    ├── rcmip_comparison1_plotting.py      (agri-sector-only comparison)
    └── rcmip_comparison2_plotting.py      (full-totals comparison)
```

The numeric prefixes `00_`, `01_`, ..., `05_` on scenario scripts encode execution order. `00_scenario_livestock_anchor.py` MUST run first because subsequent scripts read its output.

### 6.3 Sector-script anatomy (using `ch4_ef_processing.py` as exemplar)

Every Component A processing script follows the same template:

```python
"""[Sector name] — IPCC 2019 Refinement Tier 1
==================================================
[Detailed methodology comment with equations from the IPCC PDF]
"""

# 1. Bootstrap (~10 lines, identical across all scripts)
import sys as _sys
from pathlib import Path as _Path
_PROJ_ROOT = _Path(__file__).resolve()
while _PROJ_ROOT.name and not (_PROJ_ROOT / 'src').is_dir():
    if _PROJ_ROOT.parent == _PROJ_ROOT: break
    _PROJ_ROOT = _PROJ_ROOT.parent
if str(_PROJ_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_PROJ_ROOT))
from src.shared.paths import (
    FAO_DIR, FAO_PRODUCTION_CSV, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
)

# 2. Imports
import os
import pandas as pd
import numpy as np

# 3. Path setup
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_A_DATA))
os.makedirs(OUT_DIR, exist_ok=True)

# 4. IPCC parameter tables (from PDFs)
EMISSION_FACTORS = {           # Table 10.10, Ch10, IPCC 2019 V4
    'developed': { 'cattle_dairy': 117, 'cattle_other': 64, ... },
    'developing': { 'cattle_dairy': 71, 'cattle_other': 47, ... },
}

# 5. Country/region lookup tables
IPCC_REGIONS = { ... }  # 9 IPCC regions × 200+ FAO countries

# 6. Activity data loading and cleaning
df = pd.read_csv(FAO_PRODUCTION_CSV, low_memory=False)
df = df[df.Element == 'Stocks']
# ...

# 7. Tier-1 calculation
emissions = df['Value'] * df['EF']  # apply equation 10.19
# ...

# 8. Aggregation: country → region → global
global_df = grouped.sum()
# ...

# 9. CSV output
global_df.to_csv(os.path.join(OUT_DIR, 'ch4_ef_global.csv'), index=False)
country_df.to_csv(os.path.join(OUT_DIR, 'ch4_ef_country.csv'), index=False)
regional_df.to_csv(os.path.join(OUT_DIR, 'ch4_ef_regional.csv'), index=False)
species_df.to_csv(os.path.join(OUT_DIR, 'ch4_ef_species.csv'), index=False)
```

**Key thing to note**: each sector script uses Tier-1 emission factors hard-coded into the Python source from the IPCC PDF tables. This was a deliberate choice — keeping the parameter tables in the script makes the sector script a self-contained reference for what was implemented. It's verbose but unambiguous: there is one table per script, traceable to a specific IPCC table number.

### 6.4 Outputs per sector

Each historical sector produces 3-4 CSVs:

| Output | Description |
|---|---|
| `<sector>_global.csv` | Annual global total |
| `<sector>_country.csv` | Year × Country panel |
| `<sector>_regional.csv` | Year × IPCC region panel |
| `<sector>_species.csv` (or `_components.csv`, `_waterclass.csv`) | Sector-specific decomposition |

For example, `ch4_ef_species.csv` decomposes by livestock species (cattle dairy, cattle other, sheep, goats, etc.), while `ch4_rice_waterclass.csv` decomposes by rice water management class (continuous flooding, intermittent, etc.).

### 6.5 Scenario projections — the livestock anchor

`00_scenario_livestock_anchor.py` runs first because subsequent scenario scripts depend on it. It:

1. Reads the FAO 2020 country-level livestock counts
2. Reads PLUMv2 SSP-RCP **relative-change** projections for 5-year intervals 2025-2100
3. Linearly interpolates to annual
4. Multiplies the FAO 2020 anchor by the cumulative relative change to produce an annual livestock count time series 2020-2100, per country, per scenario

Output: `anchored_livestock_2020_2100.csv` in `outputs/component_a/data/`.

The anchor approach handles a crucial methodological subtlety: PLUMv2 outputs are RELATIVE changes (e.g. "5% increase by 2050 in Region X"), not absolute counts. Multiplying our reliable FAO 2020 counts by these relative changes preserves the country-level structure while applying the scenario-specific evolution.

Missing species handling: PLUMv2 doesn't project all the species FAO covers. Missing species (Horses, Mules, Asses, Camels) are held constant at FAO 2020 country values throughout the scenario period. This is documented inline in each scenario script's docstring.

### 6.6 Scenario sector scripts (`01_` through `05_`)

Each scenario script:
1. Reads `anchored_livestock_2020_2100.csv` (or fertilizer/cropland equivalent for syn-fert/MS)
2. Applies IPCC Tier-1 equations identical to the historical script
3. Produces global and regional CSVs (no country-level for the scenarios — too sparse for useful spreadsheets)

Outputs: `scenario_<sector>_global.csv`, `scenario_<sector>_regional.csv`.

There is **no `scenario_ch4_rice_processing.py`** — see §15 (Known Issues).

### 6.7 RCMIP substitution

`rcmip_substitution_processing.py` is the most important Component A script because its output feeds Component C. It performs:

```
For CH4:
    New_total(year, scen) = RCMIP_total(year, scen)
                          - RCMIP_agri_sectors(year, scen)
                          + Our_Tier1(year, scen)

For N2O:
    [same formula]
```

Where `RCMIP_agri_sectors` is the sum of CEDS sectors corresponding to enteric fermentation, manure management, rice cultivation (CH4 only), managed soils, and synthetic fertilizers. The substitution only affects 1970+ (Tier-1 starts at 1970); pre-1970 values are RCMIP unchanged.

Output: `rcmip_substitution_ch4.csv` and `rcmip_substitution_n2o.csv`. Each has columns: `Year, Scenario, Period, RCMIP_total, RCMIP_agri, Our_Tier1, New_total, Δ`.

### 6.8 Comparison plots

`rcmip_comparison1_plotting.py` produces a 6-panel figure showing CH₄ and N₂O agricultural sectors side-by-side, with our Tier-1 (solid line) vs RCMIP CEDS (dashed line) for each scenario.

`rcmip_comparison2_plotting.py` produces a 6-panel figure showing the FULL anthropogenic totals (= all sectors, agri + non-agri) per gas, with our substituted total vs RCMIP unchanged. This is the more important diagnostic because it shows the magnitude of the substitution effect on the overall trajectory.

Both plots use the IPCC scenario palette and the black-historical convention.

### 6.9 Caveats and limitations

- **Tier-1 only**. Tier-2 (region-specific factors with farming system disaggregation) and Tier-3 (process-based) are not implemented. The IPCC 2019 Refinement provides Tier-2 tables that could be a future extension.
- **No uncertainty propagation**. IPCC Tier-1 emission factors carry uncertainty ranges (typically ±30% for CH₄ EF, ±40% for soil N₂O); we use the central values without propagating the ranges.
- **Country splits/merges over time** are handled by the country-sum aggregation: at each year, we sum all FAO country rows that exist in that year. So when South Sudan splits from Sudan (2011), the sum is preserved. We verified this against FAOSTAT's own World-row aggregation and chose the country-sum approach because the World row has occasional inconsistencies for transitional years.
- **Species missing from PLUMv2** are held constant at 2020 values. For donkeys, horses, mules, camels this is a small effect (~2% of livestock CH₄). For other species it's negligible.

---

## 7. Component B — LPJ-GUESS natural emissions

### 7.1 Why streaming is necessary

The raw LPJ-GUESS output files are large because they cover 62,538 land grid cells × 120 years × multiple variables. Each file:

| File | Size (compressed) | Lines | Cell × year |
|---|---|---|---|
| `lpjg_cflux.out_historical.gz` | ~120 MB | ~7.5M | 62,538 × 120 |
| `lpjg_mch4.out_historical.gz` | ~64 MB | ~7.5M | 62,538 × 120 |
| `lpjg_ngases.out_historical.gz` | ~138 MB | ~7.5M | 62,538 × 120 |

Loading any of these fully into memory as a pandas DataFrame would require ~3-5 GB RAM. The files are stored in **cell-first ordering** (all 120 years for cell 1, then all 120 years for cell 2, ...), so we can stream them line-by-line and accumulate yearly totals in a dictionary.

### 7.2 The streaming pattern

The canonical streaming code (used in both `lpjg_historical_processing.py` and `lpjg_scenario_processing.py`) looks like:

```python
import subprocess
import numpy as np

R = 6.371e6   # Earth radius in metres
def A(lat):
    """Area of a 0.5° × 0.5° cell at latitude lat (in radians)."""
    return (0.5 * np.pi / 180)**2 * R * R * np.cos(np.radians(lat))

# Per-year accumulators
acc = {}                              # {year: {variable: total}}

# Stream the .gz file using zcat (faster than gzip.open for huge files)
p = subprocess.Popen(
    ['zcat', '/path/to/lpjg_cflux.out_historical.gz'],
    stdout=subprocess.PIPE, bufsize=65536,
)

# Header is the first line
hdr = p.stdout.readline().decode().split()
ix = {c: hdr.index(c) for c in ['Lon', 'Lat', 'Year'] + variables_of_interest}

# Stream remaining lines
for line in p.stdout:
    v = line.decode().split()
    if len(v) < len(hdr): continue
    lat = float(v[ix['Lat']])
    yr  = int(float(v[ix['Year']]))
    a   = A(lat)
    if yr not in acc:
        acc[yr] = {c: 0.0 for c in variables_of_interest}
    for c in variables_of_interest:
        acc[yr][c] += float(v[ix[c]]) * a
```

The key efficiency points:

1. **`subprocess.Popen` with `zcat`** avoids the overhead of Python-side gzip decompression, which is significantly slower than the C-implemented `zcat` on Linux/macOS.
2. **`bufsize=65536`** matches typical filesystem block sizes for efficient reading.
3. **Accumulation uses a dict-of-dicts**, indexed by year. Memory usage is O(years × variables), not O(rows). For 120 years × 8 variables, this is ~1 KB total.
4. **No pandas DataFrame in the inner loop** — DataFrame indexing is much slower than dict access.

Total streaming time on a modern laptop: ~3-5 minutes per `.gz` file. The historical run (3 files) takes ~10-15 min; each scenario run takes ~10 min for 3 files (so ~50 min total for the 5 scenarios).

### 7.3 Unit conversions

Each LPJ-GUESS output variable has its own unit, and getting these right was a significant project effort (verified against the budget papers during multiple iterations):

| Variable | Source unit | Conversion to per-year totals |
|---|---|---|
| `cflux` (CO₂) | kg C m⁻² yr⁻¹ | × A(lat) [m²] → kg C cell⁻¹ yr⁻¹; sum cells; ÷ 1e12 → Pg C yr⁻¹ |
| `mch4` (CH₄) | g CH₄ m⁻² month⁻¹ | × A(lat) × 12 [months/yr] → g CH₄ cell⁻¹ yr⁻¹; sum; ÷ 1e12 → Tg CH₄ yr⁻¹ |
| `ngases` (N₂O, NOx, NH₃, N₂) | kg N ha⁻¹ yr⁻¹ | × (A(lat) / 10000) [ha] → kg N cell⁻¹ yr⁻¹; sum; ÷ 1e9 → Tg N yr⁻¹ |

The CH₄ × 12 factor handles month-to-year conversion (we sum monthly fluxes implicitly because LPJ-GUESS reports monthly average × 12 = annual total — verified against budget papers).

The ngases ÷ 10000 handles ha-to-m² conversion (1 ha = 10,000 m²).

### 7.4 Component B sub-directory structure

```
src/component_b_natural/
├── historical/                       # 1901-2020 only
│   ├── lpjg_historical_processing.py (353 lines)
│   └── lpjg_historical_plotting.py   (455 lines)
│
├── scenarios/                        # 2021-2100 (per-SSP) only
│   └── lpjg_scenario_processing.py   (404 lines)
│
└── full_trajectory/                  # 1900-2100 combined helpers
    ├── lpjg_combined_and_fair_processing.py  (179 lines)
    └── lpjg_historical_scenario_plotting.py  (366 lines)
```

The historical/scenarios split exists because the LPJ-GUESS modeller produced separate `.gz` files for each (with different forcing: HILDA+v2 historical, PLUMv2 scenario). The full_trajectory subdirectory holds:

- `lpjg_combined_and_fair_processing.py` — produces `lpjg_ch4_combined_annual{,_scenarios}.csv` with the Global Methane Budget IFW (+112 Mt) and DCC (−23 Mt) corrections applied to LPJ wetland CH₄. Also extracts the FAIR-ERF natural baseline from `inputs/fair_erf/natural.csv`.
- `lpjg_historical_scenario_plotting.py` — the extended 1901-2100 plot showing all five scenarios after 2020.

### 7.5 The combined CH₄ correction (IFW + DCC)

LPJ-GUESS reports only **wetland CH₄** in the `mch4` variable. The Global Methane Budget atmospheric inversions tell us the natural CH₄ source totals ~150-200 Tg/yr globally, broken down into:

- Wetland: ~150-180 Tg/yr (what LPJ-GUESS reports)
- Inland Freshwater (lakes, rivers, reservoirs): ~110 Tg/yr (NOT in LPJ-GUESS)
- Geological seeps, termites, ocean: residual
- Subtract: Direct Carbon Capture (DCC) by other natural processes: ~23 Tg/yr

To produce a "natural CH₄ total" that's comparable with budget atmospheric source, we apply two corrections:

```python
CombinedDCC_TgCH4_best = LPJ_wetland_TgCH4_best + 112.0 - 23.0
```

The +112 represents the GMB IFW best-estimate (the "112 Tg/yr from inland-freshwater bodies" cited in Saunois et al. 2025). The −23 represents the GMB DCC best-estimate. These values are constants applied uniformly across all years and scenarios (a simplification; in reality both terms have temporal variation).

Output column name `CombinedDCC_TgCH4_best` carries the "DCC" tag to remind users that the DCC correction has been applied.

### 7.6 LPJ-GUESS validation against budget papers

`lpjg_historical_plotting.py` produces a 4-panel figure overlaying our historical totals against the GMB / GNB / GCB period values. Key validation points (from the project's `lpjg_budget_comparison.txt` summary):

| Quantity | Period | Our LPJ value | Budget reference | Within range? |
|---|---|---|---|---|
| CH₄ wetland | 2010-2019 | ~153 Tg/yr | GMB lower bound 116-189 | ✓ |
| N₂O soil | 2010-2019 | ~13.0 Tg N/yr | GNB natural 10.0 ± 0.6 | high but plausible |
| CO₂ NEE | 2010-2019 | ~-2.5 Pg C/yr | GCB SLAND 2.8 ± 0.7 | ✓ (sign flipped because NEE = -SLAND for sinks) |

The N₂O soil value is at the high end of the GNB natural range. This is a known LPJ-GUESS bias — the model includes some indirect N₂O emissions that the GNB classifies as anthropogenic. The integrated trajectory captures this correctly because anthropogenic N₂O comes from our Tier-1 inventory (which excludes the same indirect emissions).

### 7.7 Output files from Component B

| File | Rows | Columns |
|---|---|---|
| `lpjg_co2_annual.csv` | 120 | Year, Veg, Soil, LU_ch, Harvest, Slow_h, Fire, Est, NEE_PgC |
| `lpjg_co2_annual_scenarios.csv` | 80×5=400 | Year, Scenario, [same columns] |
| `lpjg_ch4_annual.csv` | 120 | Year, Wetland_TgCH4 |
| `lpjg_ch4_annual_scenarios.csv` | 80×5=400 | Year, Scenario, Wetland_TgCH4 |
| `lpjg_ch4_combined_annual.csv` | 121 (1900-2020) | Year, Wetland, Combined_naive, CombinedDCC_best, CombinedDCC_lo, CombinedDCC_hi |
| `lpjg_ch4_combined_annual_scenarios.csv` | 81×5=405 | Year, Scenario, [same combined columns] |
| `lpjg_n2o_annual.csv` | 120 | Year, NH3_*, NOx_*, N2O_soil, N2O_fire, N2_*, Total |
| `lpjg_n2o_annual_scenarios.csv` | 80×5=400 | Year, Scenario, [same columns] |
| `fair_erf_natural_baseline.csv` | 121 | Year, FAIR_CH4_TgCH4_yr, FAIR_N2O_TgN_yr, FAIR_N2O_TgN2O_yr |

Plus three text summaries in `outputs/component_b/summaries/`:
- `lpjg_budget_comparison.txt` — validation table
- `lpjg_grid_diagnostics.txt` — cell count, total area, missing data check
- `lpjg_scenario_summary.txt` — per-scenario period means


---

## 8. Component C — integration and validation

This is where the scientific synthesis happens. Component C scripts:

1. Combine anthropogenic + natural per gas to produce **integrated trajectories**
2. Build three independent **comparators** for validation
3. Produce four publication-quality plots showing the integrated trajectories alongside each comparator

### 8.1 Sub-directory structure

Component C is intentionally flat — there is no historical/scenario split because every script processes the entire 1900-2100 window:

```
src/component_c_integration/
├── rcmip_co2_processing.py             (203 lines)
├── integrated_emissions_processing.py  (245 lines)
├── integrated_emissions_plotting.py    (498 lines)
├── external_comparators_processing.py  (172 lines)
├── external_comparators_plotting.py    (247 lines)
├── hybrid_comparator_processing.py     (387 lines)
├── hybrid_comparator_plotting.py       (361 lines)
├── conventional_comparator_processing.py (295 lines)
└── conventional_comparator_plotting.py (321 lines)
```

### 8.2 Step 1 — `rcmip_co2_processing.py`

Extracts the anthropogenic CO₂ trajectory for all five SSP-RCP scenarios from RCMIP. Specifically uses `Emissions|CO2|MAGICC Fossil and Industrial` (= EFOS), NOT the full `Emissions|CO2`.

**Why EFOS-only**: LPJ-GUESS NEE already includes both natural land response (Veg + Soil + Fire) AND anthropogenic land-use-change components (LU_ch + Harvest + Slow_h). If we used the full RCMIP CO₂ (= Fossil + Industrial + AFOLU), we'd double-count the AFOLU/ELUC component. Using EFOS only:

```
Total atmospheric CO2 source = EFOS (RCMIP) + NEE (LPJ-GUESS)
                             = (fossil + industrial) + (natural + ELUC)
                             = fossil + industrial + AFOLU + natural-land
                             ≈ EFOS + ELUC - SLAND (the GCB partition)
```

This was empirically validated against GCB 2025 — see §13.

**Splice handling**: RCMIP historical (1750-2014) is annual. Scenario data (2015-2100) is reported every 5 years. The script linearly interpolates scenario data to dense annual coverage:

```python
# Read scenario rows, pivot to {Year: value}
scen_5yr = df_scen.set_index('Year')['EFOS_MtCO2'].to_dict()
years = sorted(scen_5yr.keys())  # [2015, 2020, 2025, ..., 2100]
years_dense = list(range(2015, 2101))
values_dense = np.interp(years_dense, years, [scen_5yr[y] for y in years])
```

The interpolation is exact at the 5-year nodes, so no splicing artefact occurs at year 2014→2015.

**Output**: `outputs/component_c/data/rcmip_co2.csv` — 1005 rows (5 scen × 201 yr) × 4 cols (Year, Scenario, EFOS_MtCO2, Period).

### 8.3 Step 2 — `integrated_emissions_processing.py`

Combines anthropogenic + natural per gas:

```python
# CH4
df_ch4['Anthro_Mt']  = df_ch4['rcmip_substitution_New_total']           # Component A
df_ch4['Natural_Mt'] = df_ch4['lpjg_ch4_combined_CombinedDCC_TgCH4_best']  # Component B
df_ch4['Total_Mt']   = df_ch4['Anthro_Mt'] + df_ch4['Natural_Mt']

# N2O
df_n2o['Anthro_Mt']  = df_n2o['rcmip_substitution_New_total']
df_n2o['Natural_Mt'] = (df_n2o['N2O_soil_TgN'] + df_n2o['N2O_fire_TgN']) * TgN_to_TgN2O
df_n2o['Total_Mt']   = df_n2o['Anthro_Mt'] + df_n2o['Natural_Mt']

# CO2
df_co2['Anthro_Mt']  = df_co2['rcmip_co2_EFOS_MtCO2']        # Component C step 1
df_co2['Natural_Mt'] = df_co2['lpjg_co2_NEE_PgC'] * PgC_to_MtCO2
df_co2['Total_Mt']   = df_co2['Anthro_Mt'] + df_co2['Natural_Mt']
```

Plus a "default total" column that represents what a conventional climate emulator would compute:

```python
df['Default_total_Mt'] = df['RCMIP_total_Mt'] + df['FAIR_natural_Mt']
```

Where `RCMIP_total` is the full RCMIP anthropogenic (NOT Tier-1 substituted) and `FAIR_natural` is the FAIR-ERF natural baseline (held constant after 2005 by FAIR convention).

The integrated trajectories are smoothed using `rmean_segmented(years, values, hist_end=2014)` — a 10-year centred rolling mean computed separately on the historical and scenario segments to avoid stitching across the boundary.

**Outputs**:
- `integrated_emissions_ch4.csv` (1005 rows × 9 cols)
- `integrated_emissions_n2o.csv` (1005 rows × 9 cols)
- `integrated_emissions_co2.csv` (1005 rows × 9 cols)
- `integrated_emissions_summary.txt`

The 9 columns are: `Year, Scenario, Period, Anthro_Mt, Natural_Mt, Total_Mt, RCMIP_total_Mt, FAIR_natural_Mt, Default_total_Mt`.

`integrated_emissions_plotting.py` produces a 6-panel figure showing top-row trajectories (with decomposition layers per scenario) and bottom-row Δ panels showing `Total − Default_total`.

### 8.4 Step 3 — `external_comparators_processing.py`

Builds the simplest comparator: top-down GMB / GNB / GCB period values, historical only. No scenario projection because atmospheric inversions can't be projected into the future.

This script just looks up values from `src/shared/budget_refs.py` and writes them as flat CSVs:

```python
# external_comparators_ch4.csv
# Year_start, Year_end, Best_Mt, Lo_Mt, Hi_Mt
# 2000, 2009, 543, 528, 578
# 2010, 2019, 575, 553, 586
# 2020, 2020, 608, 581, 627
```

`external_comparators_plotting.py` produces a 3-panel figure with one panel per gas, showing the integrated trajectory from Component C step 2 alongside the period-banded budget references.

### 8.5 Step 4 — `hybrid_comparator_processing.py` (Option B, primary)

This is the most methodologically substantial Component C script. It builds a **full-trajectory comparator** that's anchored to budget values where they exist (1980-2020) and extrapolated using RCMIP+FAIR-ERF outside.

The construction has three regions:

```
1900 ─────────── 1979 ──────── 2020 ─────────── 2100
    RCMIP+FAIR     budget anchors   RCMIP+FAIR
    (ramp-up)      (linear interp)  (continued)
```

For CH₄, anchors are at midpoints of GMB periods: 2005 (2000-2009), 2015 (2010-2019), 2020. Plus extrapolated upward from 1980 to 2005 using RCMIP+FAIR slope.

For N₂O, anchors are at midpoints of GNB periods: 1997, 2015 (2010-2019), 2020. Plus extrapolated.

For CO₂, anchors are at decade midpoints from GCB Table 7: 1965 (1960s), 1975, 1985, 1995, 2005, 2018 (2014-2023 mid). Plus a 5-year linear blend at segment boundaries to avoid step discontinuities.

**SLAND correction for CO₂**: For CO₂ specifically, a SLAND correction is applied to the RCMIP+FAIR baseline outside the budget-anchored region so the comparator stays semantically consistent throughout (always representing "atmospheric source" = EFOS + ELUC − SLAND). SLAND is interpolated annually from GCB Table 7 decadal values, ramped from 0 at 1900 to 1.2 GtC/yr at 1965 (pre-industrial natural land cycle in approximate balance), and held constant at 3.2 GtC/yr after 2018.

**Outputs**:
- `hybrid_comparator_ch4.csv` (1005 rows × 6 cols: Year, Scenario, Period, Comparator_Mt, Comparator_lo_Mt, Comparator_hi_Mt)
- `hybrid_comparator_n2o.csv`, `hybrid_comparator_co2.csv`
- `hybrid_comparator_summary.txt`

`hybrid_comparator_plotting.py` produces a 6-panel figure: top row shows trajectory + comparator + uncertainty bands, bottom row shows Δ panels (integrated total − comparator) with budget-anchored region highlighted.

### 8.6 Step 5 — `conventional_comparator_processing.py` (Option A, supplementary)

The simpler comparator: just RCMIP_total + FAIR-ERF natural baseline throughout 1900-2100 with NO observation anchoring. Represents what conventional climate emulators (FAIR/MAGICC/HECTOR) would assume.

For CO₂, the conventional comparator uses RCMIP_total directly (= MAGICC Fossil and Industrial + MAGICC AFOLU). FAIR convention is `FAIR_natural_CO2 = 0`.

The CO₂ Δ panel for this comparator has a special interpretation:
```
Δ = Our_integrated_total - Conventional_comparator
  = (EFOS + NEE) - (EFOS + AFOLU)
  = NEE - AFOLU
  ≈ -SLAND  (since NEE ≈ AFOLU - SLAND for natural land response)
```

So the CO₂ Δ panel for Option A directly reads off the LPJ-GUESS-modelled land sink magnitude per scenario. Values like `-5.36 PgC/yr` for SSP5-8.5 mean "LPJ-GUESS projects a 5.36 PgC/yr stronger land sink than the conventional climate-emulator framing."

**Outputs**:
- `conventional_comparator_ch4.csv` (1005 rows × 5 cols)
- `conventional_comparator_n2o.csv`, `conventional_comparator_co2.csv`
- `conventional_comparator_summary.txt`

`conventional_comparator_plotting.py` produces the analogous 6-panel figure.

### 8.7 Δ panel labeling — gas-aware approach

A subtle issue in the Δ panels: for CH₄ and N₂O, the comparator denominator is positive throughout 2100, so `Δ% = 100 × (integrated - comparator) / comparator` is meaningful. For CO₂ the comparator can be small or net-negative at 2100 (e.g. SSP1-2.6 RCMIP DAC scenario reaches −5.7 Gt CO₂/yr), making the percentage ratio sign-flip and mislead.

The fix (applied to all three plotting scripts during the recent session):

```python
if gas == 'CO2':
    v_PgC = v_2100 / 3666.67    # Mt CO2/yr → Pg C/yr
    ax.annotate(f'{v_PgC:+.2f} PgC/yr', ...)
else:
    pct = 100.0 * v_2100 / denom
    ax.annotate(f'{pct:+.0f}%', ...)
```

So CH₄ and N₂O Δ panels show `+57%`, `+72%`, etc. CO₂ Δ panels show `-2.56 PgC/yr`, `-4.23 PgC/yr`, etc. The latter has clean physical interpretation as the LPJ-GUESS land sink magnitude.

### 8.8 Why hybrid (Option B) is preferred

After building both Option A and Option B, the project adopted **Option B as the primary comparator**. Reasons:

1. **Historical period grounded in observations**. The hybrid comparator's 1980-2020 region is anchored to atmospheric-inversion budget values, not model assumptions. This makes the Δ panel semantically meaningful: "where our integrated trajectory differs from observed atmospheric source."

2. **Semantically consistent CO₂ framing**. The SLAND correction means the Option B CO₂ comparator represents atmospheric source throughout, matching what we computed for the integrated trajectory.

3. **Same scenario-period story**. For CH₄ and N₂O after 2020, both options use RCMIP+FAIR (no budget anchors exist for the future). So the scenario-period validation is identical between options.

Option A is retained as a supplementary diagnostic, particularly useful for the CO₂ Δ panel reading directly off the LPJ-GUESS land sink magnitude.

### 8.9 Headline scientific findings

From the project's validation rounds:

| Period | Gas | Our integrated | Budget reference | Within ±1σ? |
|---|---|---|---|---|
| 2000-2009 | CH₄ | 530 ± 11 Mt/yr | GMB 543 [528, 578] | ✓ |
| 2010-2019 | CH₄ | 590 ± 13 Mt/yr | GMB 575 [553, 586] | upper edge |
| 2020 | CH₄ | 575 Mt/yr | GMB 608 [581, 627] | just below |
| 2010-2019 | N₂O | 17.4 ± 0.4 Tg N/yr | GNB 17.4 [15.8, 19.2] | ✓ |
| 2014-2020 | CO₂ | 7.93 Pg C/yr | GCB 7.6 ± 1.24 | ✓ (gap +0.33) |

End-of-century divergence (2091-2100 mean integrated total, vs Option B hybrid):

| Scenario | ΔCH₄ (Mt/yr) | ΔN₂O (Mt/yr) | ΔCO₂ NEE (PgC/yr) |
|---|---|---|---|
| SSP1-2.6 | +71 | -1 | -1.25 |
| SSP2-4.5 | +350 | +9.7 | -2.68 |
| SSP3-7.0 | +192 | +6.6 | -3.41 |
| SSP4-6.0 | +102 | +0.3 | -2.81 |
| SSP5-8.5 | +378 | +7.6 | -5.06 |

These deltas are precisely the natural-emission climate-feedback signals that conventional climate-emulator framings cannot represent — the central scientific value-add of this pipeline.

---

## 9. Component D — IMOGEN export

### 9.1 Purpose

A thin reformatting layer: take the integrated trajectories from Component C and produce per-scenario wide-format CSVs in the schema IMOGEN expects.

### 9.2 Source

```
src/component_d_imogen_export/imogen_inputs_export.py   (~175 lines)
```

This is a single-file component because it just reshapes data — no new computation.

### 9.3 What Component D does step-by-step

```python
# 1. Read all three integrated CSVs
df_ch4 = pd.read_csv(OUT_C_DATA / 'integrated_emissions_ch4.csv')
df_n2o = pd.read_csv(OUT_C_DATA / 'integrated_emissions_n2o.csv')
df_co2 = pd.read_csv(OUT_C_DATA / 'integrated_emissions_co2.csv')

# 2. For each scenario, extract Year+Anthro+Natural+Total triples per gas
for scen in SCENARIOS:
    ch4 = df_ch4[df_ch4.Scenario == scen]
    n2o = df_n2o[df_n2o.Scenario == scen]
    co2 = df_co2[df_co2.Scenario == scen]

    # 3. Assemble wide-format dataframe
    out_df = pd.DataFrame({
        'Year':           ch4.Year.values,
        'CH4_anthro_Mt':  ch4.Anthro_Mt.values,
        'CH4_natural_Mt': ch4.Natural_Mt.values,
        'CH4_total_Mt':   ch4.Total_Mt.values,
        'N2O_anthro_Mt':  n2o.Anthro_Mt.values,
        # ...
        'CO2_total_Mt':   co2.Total_Mt.values,
    })

    # 4. Write per-scenario CSV
    out_df.to_csv(OUT_IMOGEN_INPUTS / f'imogen_inputs_{scen}.csv', index=False)

# 5. Build combined long-format CSV
all_long_rows = [...]
pd.DataFrame(all_long_rows).to_csv(OUT_IMOGEN_INPUTS / 'imogen_inputs_all_scenarios_long.csv',
                                    index=False)
```

### 9.4 Output schema (wide format, per-scenario files)

| Column | Unit | Description |
|---|---|---|
| `Year` | — | 1900–2100 (201 rows) |
| `CH4_anthro_Mt` | Mt CH₄/yr | Tier-1-substituted anthropogenic CH₄ |
| `CH4_natural_Mt` | Mt CH₄/yr | LPJ-GUESS natural CH₄ (wetland + IFW − DCC) |
| `CH4_total_Mt` | Mt CH₄/yr | sum |
| `N2O_anthro_Mt` | Mt N₂O/yr | Tier-1-substituted anthropogenic N₂O |
| `N2O_natural_Mt` | Mt N₂O/yr | LPJ-GUESS natural N₂O (soil + fire) |
| `N2O_total_Mt` | Mt N₂O/yr | sum |
| `CO2_EFOS_Mt` | Mt CO₂/yr | RCMIP fossil + industrial CO₂ |
| `CO2_NEE_Mt` | Mt CO₂/yr | LPJ-GUESS Net Ecosystem Exchange |
| `CO2_total_Mt` | Mt CO₂/yr | atmospheric source = EFOS + NEE |

### 9.5 Output schema (long format, combined file)

| Column | Description |
|---|---|
| `Year` | 1900-2100 |
| `Scenario` | SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5 |
| `Gas` | CH4, N2O, CO2 |
| `Anthro_Mt` | anthropogenic component |
| `Natural_Mt` | natural component |
| `Total_Mt` | sum |
| `Unit` | "Mt {Gas}/yr" |

Total rows: 5 scenarios × 3 gases × 201 years = 3,015 rows.

### 9.6 What Component D outputs at completion

When you run `python src/component_d_imogen_export/imogen_inputs_export.py`, Component D prints to stdout:

```
[Component D] reading integrated trajectories from /path/to/outputs/component_c/data
[Component D] writing IMOGEN inputs to /path/to/outputs/imogen_inputs
  ✓ All integrated trajectories have expected shape (201 rows × 5 scenarios × 3 gases)

[Component D] producing per-scenario IMOGEN-input CSVs ...
  ✓ SSP1-2.6: 201 rows × 10 cols → imogen_inputs_SSP1-2.6.csv
  ✓ SSP2-4.5: 201 rows × 10 cols → imogen_inputs_SSP2-4.5.csv
  ✓ SSP3-7.0: 201 rows × 10 cols → imogen_inputs_SSP3-7.0.csv
  ✓ SSP4-6.0: 201 rows × 10 cols → imogen_inputs_SSP4-6.0.csv
  ✓ SSP5-8.5: 201 rows × 10 cols → imogen_inputs_SSP5-8.5.csv

  ✓ Combined long-format: 3,015 rows × 7 cols → imogen_inputs_all_scenarios_long.csv

[Component D] sample values (SSP2-4.5):
  1900:  CH4 anthro=   87.6  natural=  176.0  total=  263.6
        N2O anthro=   1.36  natural=  11.10  total=  12.46
        CO2 EFOS=     1789  NEE=    -4144  total=    -2355
  1950:  CH4 anthro=  152.2  natural=  174.9  total=  327.1
        N2O anthro=   4.38  natural=  13.06  total=  17.44
        CO2 EFOS=     6214  NEE=     -245  total=     5969
  2000:  CH4 anthro=  342.7  natural=  177.7  total=  520.4
        N2O anthro=   9.25  natural=  13.22  total=  22.47
        CO2 EFOS=    25260  NEE=    -1777  total=    23483
  2014:  CH4 anthro=  415.4  natural=  178.2  total=  593.6
        N2O anthro=  10.70  natural=  13.92  total=  24.62
        CO2 EFOS=    35616  NEE=    -5434  total=    30182
  2020:  CH4 anthro=  393.3  natural=  179.4  total=  572.7
        N2O anthro=  12.34  natural=  13.84  total=  26.18
        CO2 EFOS=    37388  NEE=    -9361  total=    28027
  2050:  CH4 anthro=  460.9  natural=  185.8  total=  646.6
        N2O anthro=  17.70  natural=  10.13  total=  27.83
        CO2 EFOS=    42961  NEE=    -2913  total=    40048
  2100:  CH4 anthro=  645.7  natural=  192.4  total=  838.2
        N2O anthro=  22.79  natural=   9.52  total=  32.30
        CO2 EFOS=    14483  NEE=    -5339  total=     9144

[Component D] complete.
```

The terminal "complete" line confirms everything succeeded. After completion, the directory `outputs/imogen_inputs/` contains six new files:

```
outputs/imogen_inputs/
├── imogen_inputs_SSP1-2.6.csv              (~21 KB, 201 rows × 10 cols)
├── imogen_inputs_SSP2-4.5.csv              (~21 KB)
├── imogen_inputs_SSP3-7.0.csv              (~21 KB)
├── imogen_inputs_SSP4-6.0.csv              (~21 KB)
├── imogen_inputs_SSP5-8.5.csv              (~21 KB)
└── imogen_inputs_all_scenarios_long.csv    (~186 KB, 3015 rows × 7 cols)
```

These six files are the **final terminal deliverable of the entire pipeline**.

---

## 10. The pipeline driver: `run_all.py`

### 10.1 What the driver is and isn't

The driver is a thin orchestrator. It does NOT contain pipeline logic — it just executes the canonical scripts in dependency order.

What it does:
- Defines the 41-step pipeline as four ordered lists (one per component)
- Allows selecting a subset of components via `--component`
- Allows skipping plotting via `--skip-plots`
- Provides `--dry-run` to preview without executing
- Captures sub-process output for failure diagnosis (or streams it with `--verbose`)
- Times each step and prints elapsed time
- Aborts on first failure with stderr/stdout dump

What it does NOT do:
- It does not provide any logic that the individual scripts don't have.
- It does not enforce the dependency graph (you can run Component C alone, but Component C's scripts will fail loudly if Component A and B haven't been run yet)
- It does not parallelize anything.

### 10.2 The component step lists

```python
COMPONENT_A = [
    ('component_a_anthropogenic/historical/ch4_ef_processing.py',
     'processing', 'A historical: CH4 enteric fermentation'),
    ('component_a_anthropogenic/historical/ch4_ef_plotting.py',
     'plotting',   'A historical: CH4 EF plot'),
    # ... 24 more entries
]

COMPONENT_B = [
    ('component_b_natural/historical/lpjg_historical_processing.py',
     'processing', 'B historical: LPJ-GUESS streaming 1901-2020'),
    # ... 4 more entries
]

COMPONENT_C = [...]   # 9 entries
COMPONENT_D = [...]   # 1 entry
```

Each tuple is `(relative_script_path, kind, label)`. The `kind` is `'processing'` or `'plotting'`, used by `--skip-plots` filtering.

### 10.3 Invocation patterns

```bash
# Full pipeline (all 41 steps)
python run_all.py

# Single component
python run_all.py --component A
python run_all.py --component B
python run_all.py --component C
python run_all.py --component D

# Multiple components
python run_all.py --component C D
python run_all.py --component A B C D    # equivalent to --component all

# Skip plotting (faster; processing only)
python run_all.py --skip-plots

# Combine
python run_all.py --component B C --skip-plots

# Dry run (preview without executing)
python run_all.py --dry-run
python run_all.py --component A --dry-run

# Verbose (stream sub-process stdout/stderr)
python run_all.py --component D --verbose
```

### 10.4 Failure handling

If a script fails, the driver:

1. Captures the script's stderr/stdout (last 20 lines each)
2. Prints them to the driver's stderr
3. Prints the elapsed time
4. Aborts (exit code 1)

Subsequent components are NOT attempted. The partial pipeline state is left intact on disk so you can debug.

Example failure dump:
```
┌── Component A ── (26 steps)
  → A historical: CH4 enteric fermentation
    ✓ done in 4.2s
  → A historical: CH4 EF plot
    ✗ FAILED after 0.6s
    stderr:
      Traceback (most recent call last):
        File "...", line 42, in <module>
          ...
      KeyError: 'value'
│
└── pipeline aborted after failure in A
```

### 10.5 Adding a new step

To add a step (e.g. a new validation script) edit `run_all.py`:

```python
COMPONENT_C = [
    # ... existing steps ...
    ('component_c_integration/your_new_script.py',
     'processing',
     'C: your new validation step'),
]
```

The script must follow the bootstrap pattern (see §5.3) so it can find the project root. Then the driver runs it via `subprocess.run(['python3', script_path])` like any other step.

---

## 11. Inputs catalogue and acquisition

This section gives the canonical reference for every input file the pipeline expects.

### 11.1 FAO data (`inputs/fao/`)

**Source**: FAOSTAT bulk-download (https://www.fao.org/faostat/en/#data/)

| Filename | What | Used by |
|---|---|---|
| `Production_Crops_Livestock_E_All_Data.csv` | livestock counts and crop production stats, 1961-present | all Component A historical sectors |
| `Emissions_Totals_E_All_Data.csv` | FAO's own emission estimates (for benchmarking) | benchmark plots in Component A |
| `Inputs_FertilizersNutrient_E_All_Data.csv` | Fertilizer N inputs by country | `n2o_synfert_processing.py` |

These CSVs are wide-format with one row per `(Country × Item × Element × Unit)` tuple and columns `Y1961, Y1962, ..., Y2023`. Sizes ~50-150 MB each.

### 11.2 PLUMv2 outputs (`inputs/plum/`)

**Source**: project modeller (PLUMv2 group)

| Filename | What |
|---|---|
| `plum_crop_s1.csv` | Per-country crop area / livestock projections, 5-yearly 2025-2100, 5 SSP-RCP scenarios |
| `rice_cult_plum_scen_using_plum_irrig_optA.zip` | Rice cultivation scenarios (Option A irrigation) |
| `rice_cult_plum_scen_using_plum_irrig_optB.zip` | Rice cultivation scenarios (Option B irrigation) |

The `s1` in `plum_crop_s1.csv` refers to PLUMv2's "scenario set 1". The two rice options correspond to different assumptions about irrigation infrastructure expansion.

### 11.3 LPJ-GUESS outputs (`inputs/lpjg/`)

**Source**: project modeller (LPJ-GUESS group)

```
inputs/lpjg/
├── historical/
│   ├── lpjg_cflux.out_historical.gz       (~120 MB)
│   ├── lpjg_mch4.out_historical.gz        (~64 MB)
│   └── lpjg_ngases.out_historical.gz      (~138 MB)
└── scenarios/
    ├── ssp1_rcp26/
    │   ├── lpjg_cflux.out_ssp1rcp26.gz
    │   ├── lpjg_mch4.out_ssp1rcp26.gz
    │   └── lpjg_ngases.out_ssp1rcp26.gz
    ├── ssp2_rcp45/...
    ├── ssp3_rcp70/...
    ├── ssp4_rcp60/...
    └── ssp5_rcp85/...
```

File format: gzip-compressed text, whitespace-separated columns. First line is the column header. Subsequent lines are one per `(Lon × Lat × Year)` tuple. Cell-first ordering.

### 11.4 RCMIP (`inputs/rcmip/`)

**Source**: https://rcmip.org/ Phase 2 release

| Filename | What |
|---|---|
| `rcmip-emissions-annual-means-v5-1-0.csv` | RCMIP Phase 2 emissions, ~50 MB |

Schema: long-format with columns `Variable, Region, Scenario, Mip_Era, Activity_Id, Unit, ...year columns 1750..2500...`. Dense annual coverage for historical, 5-yearly for scenarios.

### 11.5 FAIR-ERF (`inputs/fair_erf/`)

**Source**: bundled with the FAIR climate emulator (https://github.com/OMS-NetZero/FAIR)

| Filename | What |
|---|---|
| `natural.csv` | FAIR's natural-emission baseline for CH₄ and N₂O |

Small file (~10 KB). Schema: `Year, FAIR_CH4_TgCH4_yr, FAIR_N2O_TgN_yr`.

### 11.6 EDGAR (`inputs/edgar/`)

**Source**: https://edgar.jrc.ec.europa.eu/ (Joint Research Centre, European Commission)

| Filename | What | Used by |
|---|---|---|
| `EDGAR_CH4_1970_2024.xlsx` | NEW EDGAR 2025 release, methane sectors 1970-2024 | 8 Component A scripts (CH₄ EF, MM, rice processing + plotting + scenario plots) |
| `EDGAR_N2O_1970_2024.xlsx` | NEW EDGAR 2025 release, nitrous oxide sectors 1970-2024 | 8 Component A scripts (N₂O MM, MS, synfert plotting + scenario plots) |
| `essd_ghg_data_emiss.xlsx` | OLD ESSD release (predecessor format) | `n2o_synfert_processing.py` ONLY |
| `IEA_EDGAR_CO2_1970_2024.xlsx` | IEA-EDGAR CO₂ release | NOT currently used |

**Why both NEW and OLD are needed**: The NEW EDGAR aggregates synthetic-fertilizer N₂O into IPCC code 3.C.4 + 3.C.5 (= all agricultural managed soils, ~64% of total N₂O). The OLD ESSD release has a dedicated 4D11 "Synthetic Fertilizers" sub-category that isolates the synfert-specific value. So `n2o_synfert_processing.py` reads the OLD file to add the `EDGAR_GgN2O` benchmark column to its global CSV. All 16 other EDGAR-touching scripts use the NEW release.

**How EDGAR is used in the pipeline**:
1. **Benchmark column**: each historical processing script adds an `EDGAR_GgCH4` or `EDGAR_GgN2O` column to its sector global CSV (allows direct comparison: our IPCC Tier-1 estimate vs FAO published vs EDGAR independent inventory).
2. **Sector/total proportioning** (in scenario plotting scripts only): builds a "RCMIP × EDGAR proportion" historical reference line by computing `EDGAR_sector(t) / EDGAR_total(t) × RCMIP_total(t)`. This shows what share of the full RCMIP CH₄/N₂O total is attributable to each specific sector under EDGAR's accounting.

**File format**: `xlsx` workbooks with sheet `IPCC 2006`, header row at row index 9 (10th row). Columns are `ipcc_code_2006_for_standard_report` plus year columns named `Y_1970, Y_1971, ..., Y_2024`. Rows are per-country emissions; sum across rows after filtering by IPCC code to get global sector totals.

The `IEA_EDGAR_CO2` file is staged but unused because the pipeline has no CO₂ Tier-1 inventory (the anthropogenic CO₂ side is the RCMIP `Emissions|CO2|MAGICC Fossil and Industrial` series unchanged). It's included for forward compatibility if a CO₂ benchmark plot is added in the future.

### 11.7 Reference PDFs (`inputs/reference_pdfs/`, optional)

These are not parsed at runtime — they're for reader/reviewer reference only. The pipeline does not require them to be present. But if you want to verify numerical reference values against the source PDFs, place them here.

| PDF | Citation |
|---|---|
| `19R_V4_Ch05_Cropland.pdf` | IPCC 2019 Refinement V4 Ch5 (Cropland) |
| `19R_V4_Ch10_Livestock.pdf` | IPCC 2019 Refinement V4 Ch10 (Livestock) |
| `19R_V4_Ch11_Soils_N2O_CO2.pdf` | IPCC 2019 Refinement V4 Ch11 (Soils) |
| `V4_10_Ch10_Livestock.pdf` | IPCC 2006 GL V4 Ch10 (Livestock) |
| `essd-17-1873-2025_GMB.pdf` | Saunois et al. 2025 GMB |
| `essd-16-2543-2024_GNB.pdf` | Tian et al. 2024 GNB |
| `essd-17-965-2025_GCB.pdf` | Friedlingstein et al. 2025 GCB |

---

## 12. Outputs catalogue

### 12.1 Component A (`outputs/component_a/`)

**`data/`** (37 files):

Historical (per sector, ~3-4 files):
- `ch4_ef_global.csv`, `ch4_ef_country.csv`, `ch4_ef_regional.csv`, `ch4_ef_species.csv`
- `ch4_mm_global.csv`, `ch4_mm_country.csv`, `ch4_mm_regional.csv`, `ch4_mm_species2020.csv`
- `ch4_rice_global.csv`, `ch4_rice_country.csv`, `ch4_rice_regional.csv`, `ch4_rice_waterclass.csv`
- `n2o_mm_global.csv`, `n2o_mm_country.csv`, `n2o_mm_regional.csv`, `n2o_mm_species2020.csv`
- `n2o_ms_global.csv`, `n2o_ms_country.csv`, `n2o_ms_regional.csv`, `n2o_ms_components.csv`
- `n2o_synfert_global.csv`, `n2o_synfert_country.csv`, `n2o_synfert_regional.csv`

Scenarios:
- `scenario_<sector>_global.csv` × 5 sectors
- `scenario_<sector>_regional.csv` × 5 sectors
- `anchored_livestock_2020_2100.csv` (livestock anchor output)
- `fao2020_missing_species.csv` (diagnostic for missing species)

RCMIP substitution:
- `rcmip_substitution_ch4.csv` ← used by Component C
- `rcmip_substitution_n2o.csv` ← used by Component C

**`figures/`** (13 files):
- 6 historical sector trends + 5 scenario sector trends + 2 RCMIP comparison plots

### 12.2 Component B (`outputs/component_b/`)

**`data/`** (10 files):
- `lpjg_co2_annual.csv`, `lpjg_co2_annual_scenarios.csv`
- `lpjg_ch4_annual.csv`, `lpjg_ch4_annual_scenarios.csv`
- `lpjg_ch4_combined_annual.csv`, `lpjg_ch4_combined_annual_scenarios.csv`
- `lpjg_n2o_annual.csv`, `lpjg_n2o_annual_scenarios.csv`
- `fair_erf_natural_baseline.csv`
- `lpjg_budget_value_sources.csv`

**`figures/`** (2 files):
- `lpjg_historical_comparison.png` — 4-panel historical
- `lpjg_historical_scenario_comparison.png` — 1901-2100 full trajectory

**`summaries/`** (3 files):
- `lpjg_budget_comparison.txt` — validation table
- `lpjg_grid_diagnostics.txt` — cell count, total area
- `lpjg_scenario_summary.txt` — per-scenario period means

### 12.3 Component C (`outputs/component_c/`)

**`data/`** (13 files):
- `rcmip_co2.csv`
- `integrated_emissions_ch4.csv`, `integrated_emissions_n2o.csv`, `integrated_emissions_co2.csv`
- `external_comparators_ch4.csv`, `external_comparators_n2o.csv`, `external_comparators_co2.csv`
- `hybrid_comparator_ch4.csv`, `hybrid_comparator_n2o.csv`, `hybrid_comparator_co2.csv`
- `conventional_comparator_ch4.csv`, `conventional_comparator_n2o.csv`, `conventional_comparator_co2.csv`

**`figures/`** (4 files):
- `integrated_emissions_comparison.png`
- `external_comparators_comparison.png`
- `hybrid_comparator_comparison.png` ← primary validation figure
- `conventional_comparator_comparison.png`

**`summaries/`** (4 files):
- `integrated_emissions_summary.txt`
- `external_comparators_summary.txt`
- `hybrid_comparator_summary.txt`
- `conventional_comparator_summary.txt`

### 12.4 IMOGEN inputs (`outputs/imogen_inputs/`)

**6 files, the terminal deliverable:**

| File | Rows × Cols | Size |
|---|---|---|
| `imogen_inputs_SSP1-2.6.csv` | 201 × 10 | ~21 KB |
| `imogen_inputs_SSP2-4.5.csv` | 201 × 10 | ~21 KB |
| `imogen_inputs_SSP3-7.0.csv` | 201 × 10 | ~21 KB |
| `imogen_inputs_SSP4-6.0.csv` | 201 × 10 | ~21 KB |
| `imogen_inputs_SSP5-8.5.csv` | 201 × 10 | ~22 KB |
| `imogen_inputs_all_scenarios_long.csv` | 3015 × 7 | ~186 KB |


---

## 13. Tests and reproducibility

### 13.1 Test suite

The `tests/` directory contains three test files. They follow the simple `def test_*()` convention so they're discoverable by `pytest tests/`, but each is also a standalone executable script.

#### `test_unit_conversions.py`

Sanity checks for the unit-conversion factors in `src/shared/constants.py`:

```python
def test_PgC_to_MtCO2():
    """Pg C → Mt CO2 should be 44/12 × 1000 = 3666.6667."""
    assert abs(PgC_to_MtCO2 - 3666.66667) < 0.01

def test_PgC_round_trip_to_PgC():
    """1 Pg C should convert to ~3667 Mt CO2 → back to 1 Pg C (±1e-9)."""
    one_PgC = 1.0
    as_MtCO2 = one_PgC * PgC_to_MtCO2
    back_to_PgC = as_MtCO2 / PgC_to_MtCO2
    assert abs(back_to_PgC - 1.0) < 1e-9
```

5 assertions total. Should run in <1 second.

#### `test_co2_option_a_validation.py`

The most scientifically meaningful test: verifies our integrated CO₂ atmospheric source for SSP2-4.5 mean 2014-2020 falls within ±1σ of the GCB 2025 partition.

```python
def test_integrated_co2_within_gcb_uncertainty():
    df = pd.read_csv(OUT_C_DATA / 'integrated_emissions_co2.csv')
    mask = (df.Scenario == 'SSP2-4.5') & (df.Year >= 2014) & (df.Year <= 2020)
    our_total_mean = df[mask]['Total_Mt'].mean()
    gap = abs(our_total_mean - GCB_BEST_MtCO2)
    assert gap < GCB_SIGMA_MtCO2
```

Expected output (numerical regression test):
```
Our integrated CO2 mean (2014-2020, SSP2-4.5): 29087 Mt CO2/yr (= 7.93 Pg C/yr)
GCB 2025 atmospheric source (2014-2023):       27867 ± 4547 Mt CO2/yr (= 7.60 ± 1.24 Pg C/yr)
Gap: 1220 Mt CO2/yr (= 0.33 Pg C/yr)
✓ within ±1σ of GCB partition
```

This test reproduces the project's headline scientific finding. If this test starts failing, something fundamental has broken in the CO₂ pipeline (Component A, B, or C).

#### `test_imogen_export_schema.py`

Verifies Component D produces correctly-shaped output files:

```python
def test_per_scenario_files_exist():
    for scen in SCENARIOS:
        assert (OUT_IMOGEN_INPUTS / f'imogen_inputs_{scen}.csv').is_file()

def test_per_scenario_schema():
    for scen in SCENARIOS:
        df = pd.read_csv(OUT_IMOGEN_INPUTS / f'imogen_inputs_{scen}.csv')
        assert df.shape == (201, 10)
        assert list(df.columns) == EXPECTED_COLS
        assert not df.isna().any().any()
        assert (df['Year'].values == np.arange(1900, 2101)).all()

def test_long_format_schema():
    df = pd.read_csv(OUT_IMOGEN_INPUTS / 'imogen_inputs_all_scenarios_long.csv')
    assert len(df) == 5 * 3 * 201   # 5 scenarios × 3 gases × 201 years = 3015 rows
    assert set(df.Scenario.unique()) == set(SCENARIOS)
    assert set(df.Gas.unique()) == {'CH4', 'N2O', 'CO2'}
```

Run all three:

```bash
# pytest mode (full discovery)
pytest tests/

# direct invocation (verbose output for each)
python tests/test_unit_conversions.py
python tests/test_co2_option_a_validation.py
python tests/test_imogen_export_schema.py
```

### 13.2 Reproducibility verification

The pipeline is fully deterministic. To verify:

```bash
# Run the pipeline once
python run_all.py

# Save md5 checksums
md5sum outputs/imogen_inputs/*.csv > /tmp/run1.md5

# Re-run
python run_all.py

# Compare
md5sum outputs/imogen_inputs/*.csv > /tmp/run2.md5
diff /tmp/run1.md5 /tmp/run2.md5      # should be empty (no diff)
```

Expected: zero differences. If you see differences, something has changed (input file, library version, or floating-point determinism issue) — investigate.

### 13.3 What's NOT tested

Honest gaps in the test suite:

- No test for Component A sector outputs (each sector has many possible failure modes that aren't checked)
- No test for Component B output shapes/values
- No test for the comparator construction (hybrid + conventional)
- No test for the plotting scripts (they produce PNGs that are visually reviewed, not numerically tested)

A plausible future improvement is adding numerical regression tests for each component's headline values (e.g. "global CH₄ enteric fermentation 2010 should be 105±2 Mt CH₄/yr"). See §16.

---

## 14. Troubleshooting

### 14.1 Import errors

**Symptom**: `ModuleNotFoundError: No module named 'src.shared'` or similar.

**Diagnosis**: The bootstrap walk-up failed to find the project root.

**Fix**:
1. Verify you have `src/` and `README.md` at the project root.
2. Check that the script you're running has the bootstrap block at top (not somewhere later).
3. Try setting `IMOGEN_GHG_ROOT` environment variable explicitly:
   ```bash
   IMOGEN_GHG_ROOT=/path/to/imogen_ghg_controller python src/.../some_script.py
   ```

### 14.2 Missing input file

**Symptom**: `FileNotFoundError: [Errno 2] No such file or directory: '/path/to/inputs/lpjg/historical/lpjg_cflux.out_historical.gz'`

**Diagnosis**: An input file isn't where the pipeline expects it.

**Fix**:
1. Run the input-verification command from §4.4 of this manual to identify which files are missing.
2. Consult `inputs/README.md` for acquisition instructions.
3. If the path is correct but the file is named slightly differently (e.g. `cflux_out.gz` instead of `lpjg_cflux.out_historical.gz`), rename or symlink it to match the expected name. The expected names are listed in `src/shared/paths.py`.

### 14.3 Out-of-memory error during LPJ-GUESS streaming

**Symptom**: Python process gets killed with no traceback during `lpjg_*_processing.py`.

**Diagnosis**: System ran out of RAM during accumulation.

**Fix**:
- Close other applications to free RAM (LPJ-GUESS streaming peaks at ~2 GB).
- If still failing, decrease `bufsize` in the `subprocess.Popen` call from 65536 to 4096 (slower but uses less memory).

### 14.4 Slow LPJ-GUESS streaming

**Symptom**: streaming takes >30 minutes per .gz file.

**Diagnosis**: Either disk I/O is slow (HDD vs SSD) or the system is using Python-side gzip decompression instead of `zcat`.

**Fix**:
- Verify `zcat` is on PATH: `which zcat`
- If not, install: `apt install gzip` (Debian/Ubuntu), `brew install gzip` (macOS), or use WSL2 on Windows.
- The script currently uses `subprocess.Popen(['zcat', ...])` — if `zcat` is missing, the call itself will fail rather than fall back to gzip.

### 14.5 Plotting script fails with matplotlib errors

**Symptom**: `RuntimeError: Invalid DISPLAY variable` or `cannot connect to X server`.

**Diagnosis**: matplotlib is trying to use an interactive backend on a headless system.

**Fix**: Set the matplotlib backend to a non-interactive one:

```bash
MPLBACKEND=Agg python src/.../some_plotting.py
```

Or persist this in your shell's rc file. Some Component C scripts set this internally; others don't. (TODO: standardize.)

### 14.6 Component C reads from wrong directory

**Symptom**: Component C's `integrated_emissions_processing.py` raises `FileNotFoundError` for `rcmip_substitution_ch4.csv` even though it exists in `outputs/component_a/data/`.

**Diagnosis**: Either Component A wasn't run, OR the `DATA_DIR_RCMIP` environment variable is set to something wrong.

**Fix**:
- Run `python run_all.py --component A` first.
- Or check `DATA_DIR_RCMIP`: should default to `outputs/component_a/data`.

### 14.7 CO₂ Δ panel shows "+58%" instead of negative Pg C/yr

**Symptom**: After re-running plotting scripts, CO₂ Δ panels look unusual.

**Diagnosis**: You may have an older version of the plotting script before the gas-aware label fix (applied in Round R0 of the most recent session).

**Fix**: Verify the plotting scripts contain the `if gas == 'CO2': v_PgC = v_2100 / 3666.67` block. If not, re-extract from the canonical tarball.

### 14.8 Pipeline runs but produces "expected 201 rows, got X" error in Component D

**Symptom**: Component D's assertion `assert len(df_ch4[scen]) == 201` fails.

**Diagnosis**: One of the integrated trajectory CSVs is malformed.

**Fix**:
1. Inspect the relevant CSV: `head outputs/component_c/data/integrated_emissions_ch4.csv`
2. Check that `Year` column spans 1900-2100 and `Scenario` column has all five SSPs.
3. Re-run Component C: `python run_all.py --component C`
4. If the issue persists, check Component A and B outputs for upstream issues.

### 14.9 Identical scripts producing different output between runs

**Symptom**: Re-running a script produces slightly different CSVs (verified via md5 diff).

**Diagnosis**: Possible non-determinism. Could be due to:
- Iteration order over a set or dict (Python 3.7+ should be deterministic but worth checking)
- Floating-point reductions whose order depends on data shape
- Library version differences between runs

**Fix**:
1. Pin library versions: `pip freeze > requirements-frozen.txt`
2. Inspect the diff: `diff outputs/component_X/data/file_run1.csv outputs/component_X/data/file_run2.csv`
3. If all diffs are in the last decimal places, it's likely floating-point reduction order — usually harmless but worth investigating.

### 14.10 Tests pass but scientific results look wrong

**Symptom**: `test_co2_option_a_validation.py` passes, but a colleague says one of the headline numbers seems off.

**Diagnosis**: Tests cover narrow numerical assertions; they don't catch broader scientific issues.

**Fix**:
1. Compare against the validation table in §8.9.
2. Generate the comparator plots (`hybrid_comparator_comparison.png`) and visually inspect.
3. If a specific scenario's late-century value looks wrong, check the corresponding LPJ-GUESS output via `lpjg_scenario_summary.txt`.
4. Consult `HANDOFF.md` for any prior session decisions related to that finding.

---

## 15. Known issues and limitations

### 15.1 RESOLVED: CH₄ rice cultivation scenario projection

*(Originally listed as pending in earlier project handoffs; resolved during the EDGAR fix round.)*

The CH₄ rice cultivation scenario projection (2020-2100) exists in the canonical pipeline as `06_scenario_ch4_rice_processing.py`, alongside `06_scenario_ch4_rice_plotting.py`. These were located inside `rice_cult_plum_scen_using_plum_irrig_optB.zip` from the original input distribution and were integrated into the canonical pipeline structure. Outputs go to `outputs/component_a/data/scenario_pipeline/scenario_ch4_rice_{global,regional}.csv`.

**Methodology used**: Option B — IrrigAmount split. The PLUMv2 `IrrigAmount` field is used to partition rice area into IPCC water-regime classes:
- `IrrigAmount > 0` → Irrigated rice (IPCC aggregated SFw = 0.60)
- `IrrigAmount = 0` → Rainfed lowland rice (IPCC aggregated SFw = 0.45)

Upland rice (SFw = 0.00) is not separately represented in PLUMv2; rows with `IrrigAmount = 0` are treated as rainfed lowland (slightly conservative — actual upland would produce zero CH₄).

**Note**: Option A (a different irrigation methodology) is also available as `rice_cult_plum_scen_using_plum_irrig_optA.zip` but not currently integrated into the pipeline. Option B was selected as the canonical approach.

### 15.2 Tier-1 only — no Tier-2 or Tier-3

The IPCC 2019 Refinement provides Tier-2 (region-specific factors with farming system disaggregation) and Tier-3 (process-based) methodologies. We implement Tier-1 only. This is acceptable for global-totals work but introduces ~30-40% uncertainty per sector relative to country-level inventories that use Tier-2.

**Fix path**: Tier-2 implementation would require region-specific emission factor tables and farming system data not present in FAOSTAT. Substantial effort; not currently planned.

### 15.3 No uncertainty propagation through the integrated trajectory

The pipeline produces deterministic central values. We do NOT propagate:
- IPCC Tier-1 emission factor uncertainty (typically ±30-40%)
- LPJ-GUESS structural uncertainty
- RCMIP scenario uncertainty
- FAIR-ERF natural baseline uncertainty

The comparator uncertainty bands shown in plots are the GMB/GNB/GCB observation uncertainty, not pipeline uncertainty.

**Fix path**: Adding Monte Carlo uncertainty propagation would require:
1. Treating each Tier-1 emission factor as a distribution rather than a point value
2. Running N=100-1000 pipeline ensembles
3. Aggregating to mean ± σ per year per scenario per gas

Substantial computational cost (~25 min × 1000 = ~17 days serial). Plausible with parallelization.

### 15.4 GMB IFW and DCC corrections are constants, not scenario-dependent

The combined CH₄ formula `CombinedDCC = LPJ_wetland + 112 - 23` uses constant values for IFW (+112) and DCC (-23) across all years and scenarios. In reality:
- Inland-freshwater CH₄ has a temperature dependence (warmer climate → more CH₄ from lakes/rivers)
- DCC processes scale with biomass

**Impact**: The CH₄ natural component has lower scenario-dependence than it should. End-of-century values may be conservative.

**Fix path**: Use a temperature-dependent IFW parameterization (e.g. from Yvon-Durocher et al. 2014) and scale by global mean surface temperature changes. Requires importing GMST trajectories.

### 15.5 N₂O integration may double-count indirect emissions

LPJ-GUESS N₂O soil includes some emissions that GNB classifies as "indirect" (downstream of N deposition). Our Tier-1 N₂O inventory excludes these (by IPCC convention). However, the integrated total may include them in both anthropogenic AND natural categories.

**Impact**: Modest (~1-2 Tg N₂O/yr). The end-of-century N₂O totals may be biased ~5-8% high.

**Fix path**: Explicitly subtract the indirect-emission component from LPJ-GUESS N₂O soil before integration. Requires a methodology decision about which fraction is "indirect."

### 15.6 Plot rendering is not standardized

Some plotting scripts set `MPLBACKEND=Agg` internally (for headless systems); others don't. This means some plot scripts may fail on a headless server while others succeed.

**Fix path**: Add `import matplotlib; matplotlib.use('Agg')` to a shared plotting helper, called at the top of every `*_plotting.py` script.

### 15.7 No `__main__` guards in some scripts

Some scripts execute computation at module level (no `if __name__ == '__main__':`), making them difficult to import as modules. This is intentional for the current invocation pattern but limits reusability.

**Fix path**: Wrap all top-level code in `def main(): ...` and add `if __name__ == '__main__': main()`. Allows `from src.component_b_natural.historical.lpjg_historical_processing import main; main()` style invocation.

### 15.8 Tests don't exercise Components A and B end-to-end

The current test suite only validates Component C → D outputs. Components A and B are not tested numerically.

**Fix path**: Add regression tests for headline values per Component A sector and per Component B variable. Example test target: "global CH₄ enteric fermentation 2010 should be 105±2 Mt CH₄/yr." Pin these against the canonical output state.

### 15.9 LPJ-GUESS scenario .gz files are gigabytes — CI/CD impractical

You can't run the full pipeline in standard CI/CD pipelines because the LPJ-GUESS data is too large to include in a tracked repo or download in a CI environment.

**Fix path**: Generate small "synthetic LPJ-GUESS" fixtures (e.g. 100 cells × 5 years) for CI, and add an environment variable like `IMOGEN_GHG_TEST_MODE=1` that points scripts to fixtures instead of real inputs. Significant work but enables continuous testing.

### 15.10 No formal data versioning

The pipeline doesn't record which version of each input file was used (e.g. "RCMIP v5.1.0" vs "v5.1.1"). If an input file is updated upstream, you can't tell from the outputs which version was used.

**Fix path**: Record SHA-256 checksums of all input files in a `inputs/manifest.json` file. Update this whenever inputs change.

---

## 16. Opportunities for further development

This section is the most important for anyone planning to extend the work. Listed roughly in order of effort/impact.

### 16.1 Easy wins (1-2 days each)

**Add Option A irrigation methodology for CH₄ rice scenarios as a methodological alternative**. The pipeline currently uses Option B (IrrigAmount split). Option A (using PLUMv2 irrigation infrastructure expansion projections) is staged in `inputs/plum/rice_cult_plum_scen_using_plum_irrig_optA.zip` but not integrated. Adding it would enable methodological comparison between irrigation accounting choices.

**Standardize matplotlib backend across plotting scripts**. See §15.6. One-line change × 18 scripts.

**Wrap top-level script code in `main()` functions**. See §15.7. Also enables better error handling and logging.

**Add `IMOGEN_GHG_TEST_MODE` for synthetic fixtures**. See §15.9. Generate small synthetic .gz files representing 100 cells × 5 years for fast CI testing.

**Add input-file version tracking**. See §15.10. Compute and record SHA-256s in `inputs/manifest.json`.

### 16.2 Medium-effort improvements (1-2 weeks each)

**Comprehensive numerical regression tests**. See §13.3 and §15.8. Pin headline values per component and per scenario to catch silent regressions.

**Parallelize Component A scenario runs**. The 5 scenario sector pipelines are independent and could run in parallel via `multiprocessing.Pool`. Could halve Component A runtime.

**Parallelize LPJ-GUESS scenario streaming**. Each of the 5 scenarios is independent. Could halve Component B scenario runtime.

**Add a Monte Carlo uncertainty mode**. See §15.3. Propagate Tier-1 emission factor uncertainty by running N=100 ensembles with sampled factors. Output as ensemble mean ± σ trajectories.

**Replace LPJ-GUESS .gz streaming with NetCDF**. If the modeller can provide NetCDF output instead of text-CSV-gzipped, streaming would be much faster (NetCDF supports random access).

**Add Tier-2 implementation for at least one sector**. Pick `ch4_ef` (most data-rich). Use IPCC 2019 V4 Ch10 Tier-2 tables. Would require farming-system disaggregation data.

### 16.3 Larger projects (1-3 months each)

**Per-region disaggregated outputs**. Currently outputs are global. Many users would want per-region (continental-scale) trajectories. Requires modifying Component C to keep regional decomposition through integration.

**Spatial outputs (gridded)**. Currently Component B aggregates the 0.5° LPJ-GUESS grid to global. For some uses, gridded outputs are needed. Would require keeping spatial dimensions through Components C and D.

**Coupling to actual IMOGEN runs**. The pipeline produces forcing trajectories but doesn't run IMOGEN. Adding an IMOGEN runtime wrapper would close the loop and enable end-to-end climate projections.

**Comparison ensemble with other DGVMs**. The natural-emission side currently uses LPJ-GUESS only. An ensemble using LPJ-GUESS + LPJmL + JULES + ORCHIDEE would quantify model-spread uncertainty. Requires NetCDF processing for each model's output format.

**Web-based visualization dashboard**. Currently outputs are static PNGs. A small Plotly Dash or Streamlit app could provide interactive scenario comparison, period selection, etc. Would help wider adoption.

### 16.4 Methodological extensions

**Add CH₄ wetland temperature feedback**. See §15.4. Make IFW parameterization temperature-dependent.

**Add N₂O indirect-emission accounting**. See §15.5. Properly partition indirect vs direct emissions to avoid double-counting.

**Add additional anthropogenic sectors**. Biomass burning (CH₄ + N₂O) could be added using GFED data. Industrial CH₄/N₂O fugitives are already in RCMIP.

**Compare against EDGAR**. The pipeline benchmarks against FAO and RCMIP. Adding EDGAR v8 (https://edgar.jrc.ec.europa.eu/) as a third reference would provide independent validation.

### 16.5 Software engineering improvements

**Migrate to pyproject.toml-based packaging**. Currently the repo has `pyproject.toml` but the `src/` layout doesn't follow standard Python packaging (would need `__init__.py` re-exports + `pip install -e .` for `from imogen_ghg_controller.shared import ...` style imports).

**Migrate from CSV to Parquet**. CSVs are human-readable but Parquet is ~10× smaller and ~5× faster to read. Could keep CSV outputs for inspection and Parquet for inter-component data flow.

**Add type hints**. Currently no type annotations. Adding them would catch errors earlier.

**Migrate from print() to logging**. Currently uses print() for status. logging module would enable log-level control and structured output.

**Add a CLI entry point**. `pip install -e . && imogen-ghg run-all` instead of `python run_all.py`. Standard Python packaging convention.

---

## 17. Glossary

**AFOLU** — Agriculture, Forestry, and Other Land Use. An IPCC reporting category that includes land-use-change CO₂.

**CEDS** — Community Emissions Data System. The harmonized historical anthropogenic emission inventory used by RCMIP / CMIP6.

**DGVM** — Dynamic Global Vegetation Model. A class of land-surface model that simulates vegetation dynamics, soil carbon, and biogeochemical cycles. LPJ-GUESS is one such model.

**EFOS** — Emissions FOSsil. Specifically the `Emissions|CO2|MAGICC Fossil and Industrial` series in RCMIP, representing fossil fuel combustion + industrial process CO₂ but EXCLUDING land-use change.

**ELUC** — Emissions Land-Use Change. The CO₂ emission/uptake from human-caused land-use change (deforestation, afforestation, agricultural expansion, etc.). Part of LPJ-GUESS NEE.

**FAIR-ERF** — Finite Amplitude Impulse Response model with Effective Radiative Forcing. A simple climate emulator. Provides natural-emission baseline values for CH₄ and N₂O.

**FAO** — Food and Agriculture Organization (of the United Nations). Maintains the FAOSTAT statistical database, source of livestock counts, crop production, and fertilizer inputs.

**GCB** — Global Carbon Budget. Annual community-effort assessment of the global CO₂ partition (EFOS, ELUC, atmospheric growth, ocean sink, land sink).

**GMB** — Global Methane Budget. Annual community-effort assessment of the global CH₄ partition.

**GMST** — Global Mean Surface Temperature.

**GNB** — Global Nitrogen Budget. Periodic community-effort assessment of the global N₂O budget.

**HILDA+v2** — Harmonized historical land-use product used as forcing for the LPJ-GUESS historical run.

**IMOGEN** — Integrated Model of Greenhouse Effect from Nitrogen. A climate emulator developed at UK CEH. The terminal user of this pipeline's outputs.

**IPCC Tier 1** — The simplest tier of methodology in IPCC GHG inventory guidelines. Uses globally-averaged emission factors applied to activity data.

**LPJ-GUESS** — Lund-Potsdam-Jena General Ecosystem Simulator. The DGVM whose outputs Component B aggregates.

**NEE** — Net Ecosystem Exchange. The net CO₂ flux between the land biosphere and the atmosphere. Negative = land sink. Equals the sum of all LPJ-GUESS CO₂ flux components (Veg + Soil + Fire + LU_ch + Harvest + Slow_h).

**PLUMv2** — A land-use model that produces SSP-RCP-specific projections of land use, livestock, and crop area for 2020-2100. Used as activity data for Component A scenarios.

**RCMIP** — Reduced Complexity Model Intercomparison Project. Maintains harmonized historical and CMIP6 SSP scenario emission trajectories. Source of our anthropogenic CO₂ EFOS data.

**SLAND** — Land Sink. The natural-land CO₂ uptake. In the GCB partition: SLAND = EFOS + ELUC − atmospheric_growth − ocean_sink.

**SSP-RCP** — Shared Socioeconomic Pathway × Representative Concentration Pathway. The scenario framework used in IPCC AR6 / CMIP6.

---

## 18. Bibliography

### Primary references

- **Friedlingstein, P., O'Sullivan, M., Jones, M. W., et al. (2025).** Global Carbon Budget 2025. *Earth System Science Data*, 17, 965-1039. — Source of GCB 2025 partition values used in `src/shared/budget_refs.py`.
- **IPCC (2019).** 2019 Refinement to the 2006 IPCC Guidelines for National Greenhouse Gas Inventories, Vol. 4 (Agriculture, Forestry and Other Land Use). — Source of all Tier-1 emission factors in Component A.
- **Saunois, M., Martinez, A., Poulter, B., et al. (2025).** Global Methane Budget 2000-2020. *Earth System Science Data*, 17, 1873-1958. — Source of GMB 2025 atmospheric inversion values.
- **Tian, H., Pan, N., Thompson, R. L., et al. (2024).** A comprehensive quantification of global nitrous oxide sources and sinks. *Earth System Science Data*, 16, 2543-2604. — Source of GNB 2024 atmospheric inversion values.

### Models and frameworks

- **Huntingford, C., & Cox, P. M. (2000).** An analogue model to derive additional climate change scenarios from existing GCM simulations. *Climate Dynamics*, 16, 575-586. — IMOGEN original description.
- **Huntingford, C., Booth, B. B. B., Sitch, S., et al. (2010).** IMOGEN: an intermediate complexity model for evaluating future regional risks of changing land carbon storage. *Geoscientific Model Development*, 3, 679-687.
- **Smith, B., Wårlind, D., Arneth, A., et al. (2014).** Implications of incorporating N cycling and N limitations on primary production in an individual-based dynamic vegetation model. *Biogeosciences*, 11, 2027-2054. — LPJ-GUESS reference.
- **Smith, C. J., Forster, P. M., Allen, M., et al. (2018).** FAIR v1.3: a simple emissions-based impulse response and carbon cycle model. *Geoscientific Model Development*, 11, 2273-2297. — Source of FAIR-ERF natural baseline.
- **Nicholls, Z. R. J., Meinshausen, M., Lewis, J., et al. (2020).** Reduced Complexity Model Intercomparison Project Phase 1: introduction and evaluation of global-mean temperature response. *Geoscientific Model Development*, 13, 5175-5190. — RCMIP reference.

### Data sources

- **FAO** (Food and Agriculture Organization). FAOSTAT statistical database, https://www.fao.org/faostat/en/#data (accessed 2026)
- **RCMIP**. https://rcmip.org/ Phase 2 release v5.1.0 (2024)

### Methodological extensions

- **Yvon-Durocher, G., Allen, A. P., Bastviken, D., et al. (2014).** Methane fluxes show consistent temperature dependence across microbial to ecosystem scales. *Nature*, 507, 488-491. — Reference for temperature-dependent IFW parameterization (see §15.4).

---

*End of Technical Manual.*
*For questions, corrections, or extensions, see the project README.md for contact information.*
