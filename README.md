# LandSyMM-IMOGEN — Coupled Model Framework

> **Project:** A novel coupled model framework to explore the influence of
> bottom-up agricultural, land use, and management emissions on
> climate-ecosystem interactions.
>
> **Status:** v0.1 — scaffolding initialised; rebuild in progress per
> `EXECUTION_PLAN.md` Part V. See [Roadmap](#roadmap) below for current
> milestone.
>
> **Lineage:** This codebase rebuilds and unifies two predecessor
> framework trees (`version_A` workstation and `version_B` cluster — both
> archived elsewhere) into a single, public-quality, version-controlled
> codebase that runs end-to-end on Linux workstations and HPC clusters.

---

## What is this?

**LandSyMM-IMOGEN** is a closed-loop coupled model framework that
combines four components to project climate–ecosystem–emissions
interactions under SSP-RCP scenarios:

1. **LPJ-GUESS 4.1 (LandSyMM fork)** — a dynamic global vegetation
   model that simulates ecosystem fluxes (NEE, wetland CH4, soil/fire
   N2O) and provides "Stage I" potential yields to PLUM.
2. **PLUM v2** (external — not in this codebase) — economic land-use
   optimisation that converts yields + scenario demand into
   spatiotemporal land-use, crop fractions, fertiliser, irrigation,
   and per-country activity data.
3. **The Intermediary Controller (Python)** — applies IPCC 2019
   Refinement Tier-1 methodologies to PLUM activity data to estimate
   anthropogenic CH4 + N2O emissions from agriculture; substitutes
   them into the RCMIP Phase 2 background trajectory.
4. **IMOGEN** — a pattern-scaling climate emulator that takes
   integrated emissions and produces year-by-year monthly climate
   forcing back to LPJ-GUESS, closing the loop.

Two coupling modes are supported:

- **Tight (closed-loop, default):** LPJ-GUESS year N's NEE/CH4/N2O
  feed back into IMOGEN's year N+1 climate trajectory in real time.
- **Prescribed:** IMOGEN reads pre-computed static "natural" flux
  files; useful for sensitivity studies where LPJG perturbations
  should not influence climate.
- **Loose:** IMOGEN runs once standalone; LPJ-GUESS reads pre-baked
  climate. Legacy compatibility.

---

## Repository structure

```
lpj-guess_imogen_landsymm/
├── README.md                          (this file — top-level navigation)
├── COUPLED_MODEL_INVESTIGATION.md     Master investigation document (240 KB).
│                                       State-of-the-system + bug catalogue
│                                       + roadmap. Read this first.
├── EXECUTION_PLAN.md                  Operational checklist + strategic
│                                       decisions + rebuild plan (Part V).
│                                       Working instrument for development.
├── _phase2_findings/                  8 subagent reports, 414 KB total —
│                                       the canonical evidence base for
│                                       every claim in the master doc.
│
├── lpjguess/                          LPJ-GUESS LandSyMM fork
│                                       (`LandSyMM_LPJ-GUESS/`, also called
│                                       the "integrated LTS" per user
│                                       terminology). All v1.0 dev happens
│                                       here. `trunk_r13078` is the
│                                       backport target; ledger of every
│                                       source-level change is tracked at
│                                       `notes/TRUNK_R13078_BACKPORT_LEDGER.md`
│                                       for the end-of-Phase-1 sprint
│                                       (followup F-11) that brings
│                                       `trunk_r13078` to functional parity
│                                       and exposes both forks as
│                                       switchable backends.
├── imogen/                            Fortran IMOGEN with ALLOCATABLE-array
│                                       refactor (Phase 1); C++ refactor
│                                       brought to parity in Phase 2.
├── intermediary_py/                   Python imogen_ghg_controller v0.1.0:
│                                       IPCC Tier-1 + RCMIP substitution +
│                                       LPJG natural-flux aggregation.
│
├── tools/                             Cross-component utilities:
│                                       imogen_inputs_to_lpjg_format.py,
│                                       cmip6_nc_to_cmip5_ascii.py, regrid.
├── runs/                              Per-scenario run setups:
│                                       runs/historic/ (HILDA+ standalone
│                                       with save_state at 2020),
│                                       runs/SSP1-2.6/ (coupled scenario
│                                       restart from 2020), etc.
├── data/                              Reference small data; large data
│                                       documented in data/DATA.md
│                                       (acquired separately).
├── scripts/                           run_coupled.sh (workstation),
│                                       run_coupled.sbatch (cluster SLURM
│                                       template), cluster/ (owl helpers).
├── ci/                                CI/CD workflows.
├── docs/                              Unified technical manual,
│                                       scientific framework, build
│                                       instructions, troubleshooting.
├── paper/                             Manuscript draft + figures + cited
│                                       peer-reviewed PDFs.
├── notes/                             Per-step development notes
│                                       (notes/STEP_<n>.md) for the
│                                       rebuild plan in EXECUTION_PLAN.md.
└── archive/                           Frozen legacy code preserved for
                                        reference (older C++ refactor before
                                        parity, retired Imogen-controller,
                                        etc.).
```

---

## How to read this repo

Three documents serve different purposes:

1. **`COUPLED_MODEL_INVESTIGATION.md`** (the master doc) — start here.
   Comprehensive state-of-the-system report, scientific framework,
   per-component deep dives, ~120-item bug catalogue, doc-vs-code
   contradictions, A-vs-B divergence, open questions, roadmap, recommended
   directory structure. ~240 KB / ~3 970 lines.
2. **`EXECUTION_PLAN.md`** — operational checklist. Settled strategic
   decisions, gap inventory (necessities + missing components + data
   acquisition + units integrity), 11 strategic-decision write-ups,
   formal Part V step-by-step rebuild plan with verification milestones.
   ~142 KB / ~2 600 lines.
3. **`_phase2_findings/`** — 8 detailed subagent reports
   (~414 KB / ~6 500 lines) covering every subsystem at depth.
   Cited inline throughout the master doc. The canonical evidence
   base.

For **users / collaborators / reviewers** who want a quick orientation:
read `COUPLED_MODEL_INVESTIGATION.md` §1 (executive summary), §2
(scientific framework), §3 (system architecture), §13 (recommended
directory structure).

For **developers / maintainers**: read `EXECUTION_PLAN.md` Part V
(formal rebuild plan) for the per-step work plan.

---

## Build and run (post-v1.0)

(*Pending v1.0 release. Documentation in this section will fill in as
the rebuild progresses through Part V steps 14-19. For now, see*
`EXECUTION_PLAN.md` *Part V for the build sequence.*)

A v1.0 user will:

```bash
# 1. Clone the repo
git clone <one-of-three-remotes> lpj-guess_imogen_landsymm
cd lpj-guess_imogen_landsymm

# 2. Acquire the large input data (per data/DATA.md)
# 3. Build LPJ-GUESS, Fortran IMOGEN, Python Intermediary venv
./scripts/build_all.sh

# 4. Run a scenario (workstation)
./scripts/run_coupled.sh SSP1-2.6
# OR (cluster, SLURM)
sbatch ./scripts/run_coupled.sbatch SSP1-2.6
```

---

## Roadmap

Per `EXECUTION_PLAN.md` Part V. Headline tags expected during development:

| Tag | After step | Milestone |
|---|---|---|
| `v0.0-investigation` | (pre-step-0) | Investigation evidence base only |
| `v0.1-skeleton` | step 0 | This commit — scaffolding + investigation imported |
| `v0.2-lpjg-builds` | step 3 | LPJ-GUESS + Fortran-with-`ALLOCATABLE` IMOGEN both build cleanly |
| `v0.3-coupling-fixed` | step 9 | Basic coupled run works (the seven break-points + C35 fixed) |
| `v0.4-climate-parity` | step 9.5 | Fortran + C++ produce parity climate output; Tmin/Tmax wired |
| `v0.5-workstation-mvp` | step 14 | Full SSP1-2.6 coupled run completes on workstation |
| `v0.6-cluster-mvp` | step 16 | SSP1-2.6 completes on owl cluster |
| `v0.9-validated` | step 17 | NOAA/AGAGE concentration thresholds met |
| `v1.0` | step 19 | CI green; paper ready for GMD submission |

Total estimated effort to v1.0: ~25-35 person-days + ~3-4 days cluster
wall-clock. Calendar-time estimate: ~7-10 weeks.

---

## Citation

When publications result from this work, please cite the
LandSyMM-IMOGEN coupled framework as:

```
(citation pending — placeholder for the GMD paper currently in
preparation; see paper/manuscript_draft.docx)
```

Plus the underlying components per their own citation requirements:

- LPJ-GUESS / LandSyMM: Smith 2014 (BG); Lindeskog 2013 (ESD); Olin
  2015a/b (ESD/BG); Wania 2010 LPJ-WHyMe (GMD); Rabin 2020 (ESD).
- PLUM v2: Alexander 2018 (GCB); Engström 2016.
- IMOGEN: Huntingford 2010 (GMD); Zelazowski 2018 (GMD); Mathison
  2025 PRIME (GMD); Hayman 2021 (ESD).
- IPCC Tier-1 methodologies: IPCC 2019 Refinement Vol 4 Ch 5
  Cropland, Ch 10 Livestock, Ch 11 Soils, plus Wetlands Supplement.
- Reference budgets: GMB 2025 Saunois (ESSD); GNB 2024 Tian (ESSD);
  GCB 2025 Friedlingstein (ESSD).
- RCMIP Phase 2: Nicholls 2020.
- FaIR v1.3: Smith 2018 (GMD).

See `paper/references/` for the cited PDFs and `CITATION.cff` for
machine-readable citation metadata.

---

## License

MIT. See `LICENSE`.

---

## Contributing

See `CONTRIBUTING.md` for the development workflow, per-step
verification protocol, and units-integrity discipline.

---

## Project history

This codebase succeeds two earlier framework trees:

- **`version_A`** (workstation; user's local-development setup at
  `/home/bampoh-d/Desktop/...`) — archived elsewhere; not modified.
- **`version_B`** (cluster; user's KIT IMK-IFU owl cluster setup at
  `/bg/data/lpj/bampoh-d/...`) — archived elsewhere; not modified.

Both A and B are immutable read-only references during this rebuild.
Both are documented exhaustively in `COUPLED_MODEL_INVESTIGATION.md`
and `_phase2_findings/`.

This codebase also draws from two other completed predecessor projects:

- **`lpjg_landsymm_integration/`** — the user's prior integration
  project, which produced **`LandSyMM_LPJ-GUESS/`** (a.k.a. the
  "integrated LTS" per the integration-project terminology). That
  artifact IS our `lpjguess/` v1.0 development base. Backport
  target `trunk_r13078` (inside `version_A`/`version_B`) becomes
  a switchable build-time backend after the end-of-Phase-1
  Backport Sprint (followup F-11; ledger at
  `notes/TRUNK_R13078_BACKPORT_LEDGER.md`). See
  `EXECUTION_PLAN.md` II.11 for the full fork-choice decision and
  terminology synonymy.
- **`landsymm_py/`** — Python pipeline for HILDA+ historic + PLUM
  scenario LU harmonisation, the user's prior project. Provides the
  scenario LU at `/media/bampoh-d/.../plum_harm_lu/` consumed by
  this framework.

---

*Repository created 5 May 2026. Investigation phase complete; rebuild
phase in progress per EXECUTION_PLAN.md Part V.*
