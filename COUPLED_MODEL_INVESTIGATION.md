# LandSyMM-IMOGEN Coupled Model — Investigation, State-of-the-System Report, and Roadmap to a Unified Working Codebase

> **Document role**
> This is the master investigation document produced from a meticulous,
> systematic and comprehensive read-only audit of the two coupled-model
> codebases delivered by the user (`version_A` — workstation; `version_B` —
> cluster) and the supporting documentation, configuration, and data they
> ship.
>
> **Audience**
> Anyone — the original author, a successor maintainer, a peer reviewer, a
> downstream user — who needs to (a) understand how the LandSyMM-IMOGEN
> coupled framework is intended to work, (b) understand the precise state
> in which the codebases are today, (c) reproduce or extend the work, or
> (d) build the unified, version-controlled, fully-working codebase that
> succeeds these two trees.
>
> **Methodology**
> All findings are evidence-based: the underlying audit was performed by
> eight specialised read-only subagents, each focusing on one subsystem,
> writing a self-contained per-subsystem report. Their full reports are
> retained as primary evidence in `_phase2_findings/`:
>
> | # | Topic | File | Size |
> |---|---|---|---|
> | 1 | Documentation inventory | `_phase2_findings/01_documentation_inventory.md` | 86 KB |
> | 2 | LPJ-GUESS LandSyMM fork (`trunk_r13078`) | `_phase2_findings/02_lpjguess_trunk_r13078.md` | 58 KB |
> | 3 | IMOGEN Fortran | `_phase2_findings/03_imogen_fortran.md` | 47 KB |
> | 4 | IMOGEN C++ refactor (`IMOGENCXX`) | `_phase2_findings/04_imogen_cxx.md` | 41 KB |
> | 5 | C++ Intermediary | `_phase2_findings/05_intermediary_cpp.md` | 55 KB |
> | 6 | Python Intermediary (`Intermediary_py`) | `_phase2_findings/06_intermediary_py.md` | 56 KB |
> | 7 | GCM patterns + regrid utilities | `_phase2_findings/07_patterns_and_regrid.md` | 30 KB |
> | 8 | Run setups, orchestration, `Data/` | `_phase2_findings/08_orchestration_and_data.md` | 38 KB |
>
> This master document **synthesises** them: it cross-references findings,
> resolves apparent inconsistencies, surfaces cross-cutting issues that no
> single subagent had a complete view of, and converts the audit into a
> concrete plan. It does not replace the per-subsystem reports — when this
> document is necessarily compact, the corresponding subagent report is
> the canonical source of evidence and is cited in-line.
>
> Where citations to specific files / line numbers appear, they refer to
> the on-disk state at investigation time
> (date stamp inside the audit reports). Where this document records a
> follow-up verification beyond the original subagent reports, those
> verifications are flagged as "**verified additionally** (this document)".

---

## Table of contents

- [0. Document conventions](#0-document-conventions)
- [1. Executive summary](#1-executive-summary)
  - [1.1 Verdict at a glance](#11-verdict-at-a-glance)
  - [1.2 The seven things that break coupling](#12-the-seven-things-that-break-coupling)
  - [1.3 What works, what does not, and what was never wired](#13-what-works-what-does-not-and-what-was-never-wired)
  - [1.4 What this document recommends](#14-what-this-document-recommends)
- [2. Scientific framework — what LandSyMM-IMOGEN is *supposed* to be](#2-scientific-framework--what-landsymm-imogen-is-supposed-to-be)
  - [2.1 Lineage and citations](#21-lineage-and-citations)
  - [2.2 The two-stage protocol](#22-the-two-stage-protocol)
  - [2.3 Sector ownership and double-counting prevention](#23-sector-ownership-and-double-counting-prevention)
  - [2.4 Boundary harmonisation](#24-boundary-harmonisation)
  - [2.5 Validation thresholds](#25-validation-thresholds)
  - [2.6 Acknowledged biases and limitations](#26-acknowledged-biases-and-limitations)
- [3. System architecture](#3-system-architecture)
  - [3.1 Component inventory](#31-component-inventory)
  - [3.2 Process model — single binary, not two processes](#32-process-model--single-binary-not-two-processes)
  - [3.3 Coupling modes — tight, loose, standalone](#33-coupling-modes--tight-loose-standalone)
  - [3.4 The `done`-file rendezvous protocol](#34-the-done-file-rendezvous-protocol)
  - [3.5 Data flows — intended vs actual](#35-data-flows--intended-vs-actual)
  - [3.6 Annotated process diagram](#36-annotated-process-diagram)
  - [3.7 The `FILE_LPJG_FLUX` path-override — "loose coupling masquerading as tight coupling"](#37-the-file_lpjg_flux-path-override--loose-coupling-masquerading-as-tight-coupling)
- [4. Per-component deep dives](#4-per-component-deep-dives)
  - [4.1 LPJ-GUESS LandSyMM fork (`trunk_r13078`)](#41-lpj-guess-landsymm-fork-trunk_r13078)
  - [4.2 IMOGEN Fortran (the working IMOGEN)](#42-imogen-fortran-the-working-imogen)
  - [4.3 IMOGEN C++ refactor (`IMOGENCXX`)](#43-imogen-c-refactor-imogencxx)
  - [4.4 Imogen-controller](#44-imogen-controller)
  - [4.5 C++ Intermediary (`Intermediary/Code`)](#45-c-intermediary-intermediarycode)
  - [4.6 Python Intermediary (`Intermediary_py`)](#46-python-intermediary-intermediary_py)
  - [4.7 GCM patterns and the three regrid utilities](#47-gcm-patterns-and-the-three-regrid-utilities)
  - [4.8 Auxiliary tooling — `NdepFastArchive`, `Matlab-scripts`, `Python-scripts`, `Plots`](#48-auxiliary-tooling--ndepfastarchive-matlab-scripts-python-scripts-plots)
- [5. Data inventory](#5-data-inventory)
- [6. Run setups — workstation A vs cluster B](#6-run-setups--workstation-a-vs-cluster-b)
- [7. Documentation map](#7-documentation-map)
- [8. Catalogue of bugs, gaps, and dead code](#8-catalogue-of-bugs-gaps-and-dead-code)
- [9. Documentation-vs-code contradictions](#9-documentation-vs-code-contradictions)
- [10. `version_A` vs `version_B` — full divergence accounting](#10-version_a-vs-version_b--full-divergence-accounting)
- [11. Open questions and uncertainties](#11-open-questions-and-uncertainties)
- [12. Roadmap to a unified working codebase](#12-roadmap-to-a-unified-working-codebase)
- [13. Recommended directory structure for the unified codebase](#13-recommended-directory-structure-for-the-unified-codebase)
- [14. Appendices](#14-appendices)

---

## 0. Document conventions

- **Path notation.** Paths are written relative to the workspace root
  `landsymm_lpjg_imogen_coupled_model/`. The two top-level investigated
  trees are abbreviated:
  - `A/` = `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/`
  - `B/` = `version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/`
- **Citations to source.** When a specific file/line is cited, it follows
  the form `filename:line` (e.g. `modules/imogencfx.cpp:483`). Citations
  to subagent reports use the form `[SA1 §3.2]` (Subagent 1, section 3.2).
- **Severity tags** in the bug catalogue (Section 8):
  - 🔴 **Active code defect** — known to fail or to corrupt results today
  - 🟡 **Latent defect** — masked by some other condition (commented-out
    code, unreachable branch, unused parameter); will activate on fix-up
  - 🟢 **Cosmetic** — comments, typos, dead declarations, build
    artefacts. No effect on correctness.
- **Component names.** "LandSyMM-IMOGEN" denotes the framework as named in
  the supervisor-reviewed working paper draft (the scientific
  source-of-truth, see §7). Earlier docs and the README sometimes refer
  to it as "LPJG-IMOGEN coupling setup"; this is OUTDATED nomenclature.
- **Implementation languages and shorthand.** "Fortran IMOGEN" =
  `Common-directory/IMOGEN-codebase/code/imogen_lpjg.f` (working). "C++
  IMOGEN" or "IMOGEN refactor" = `IMOGENCXX/ImogenCXX/src/Main.cpp`
  (broken). "C++ Intermediary" = `Intermediary/Code/` (legacy, partial).
  "Python Intermediary" = `Intermediary_py/imogen_ghg_controller_*/`
  (current, unwired).

---

## 1. Executive summary

### 1.1 Verdict at a glance

The LandSyMM-IMOGEN coupled framework as committed in `version_A` and
`version_B` is **structurally complete but functionally inoperative as a
coupled simulation**. Every component is on disk; several have been
exercised in isolation; reference outputs from earlier successful runs
are still present in `Data/Intermediary/Emissions/` and
`Common-directory/IMOGEN/output/`; but the *coupling itself* is broken
in at least seven distinct, independently-fixable places, and a single
top-level orchestration script that ties build → run → coupled-step →
analyse does not exist anywhere in either tree.

The on-disk evidence is unambiguous about this verdict because the
LPJ-GUESS↔IMOGEN handshake files
(`Common-directory/LPJG_main/IMOGEN/imogen_lpjg_flux.txt`,
`imogen_lpjg_ch4_n2o_flux.txt`) contain exactly one line each — a
manually-placed placeholder dated 2025-06-12 with the year hard-coded
to `2100` and a token flux value (`0.00` and `202\t9.1` respectively).
LPJ-GUESS never actually wrote those files in a real coupled run.
Likewise, the 230 year-directories under
`Common-directory/IMOGEN/output/<YYYY>/` were produced by an
**IMOGEN-only** standalone seeding run on 2025-06-16 — the per-year log
shows ~4–5 seconds per year of wall-clock time, far too short to
interleave a real LPJ-GUESS simulation step.

The audit also confirmed, however, that *every* component is close to
working. The fixes required are well-localised, and the underlying
science (working paper, IPCC tier-1 inventories, FaIR-driven IMOGEN per
the PRIME framework, HILDA+v2 land-use forcing, factorial yield
generation for PLUMv2) is internally consistent and well-documented.
The path from "two stuck codebases" to "one curated, public,
reproducible, scientifically-defensible codebase" is detailed in
Section 12 (Roadmap).

### 1.2 The seven things that break coupling

Listed in priority order: low-hanging fixes first, deeper refactors
later.

1. **`A/Integrations/trunk/trunk_r13078/modules/imogencfx.cpp:483`**
   contains a single line `exit(200);` immediately after
   `RUN_IMOGEN_ENGINE();`. This terminates LPJ-GUESS at the *end of
   `init()`*, before any gridcell is simulated. The line is **not
   present** in the standalone LandSyMM fork
   (`lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`) — it was added in
   the trunk on 2026-03-21 as a debug shortcut and never reverted.
   **Removing this single line is the single highest-impact change in
   the entire codebase**: it transforms the binary from "IMOGEN-only
   spin then halt" to "IMOGEN engine year ↔ LPJ-GUESS year, in
   process". [SA2 §3.5(3), §8.2]

2. **`modules/climatemodel.cpp:330–350`** has the polling-loop safety
   checks neutered. Specifically:
   - Line 330–331: `doneExist = true;` is hardcoded, with the actual
     `INQUIRE(FILE=...done)` check commented out.
   - Lines 334, 341, 350: the `runnowOpen`/`runfluxOpen`/
     `runnonco2fluxOpen` "is the writer still flushing?" guards are
     commented out.
   The polling loop will accept a partial flux file, and the `done`
   barrier file is bypassed entirely. [SA2 §5.2]

3. **`A/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/imogen_intermediary.ins`**
   (and the corresponding `B` file) line 102–109 contain
   `param "file_temp" (str "./IMOGEN/ouput/YYYY/T_anom.dat")` — six
   lines with a **`ouput` typo** for `output`, and one line claiming
   `R_anom.dat` instead of `Rh_anom.dat`. This audit verified
   additionally that `param "file_temp"` *is* consumed by
   `imogencfx.cpp:370`, so once the `exit(200)` of bug #1 is removed
   these typos cause `read_lines_from_file()` to fail silently.
   [verified additionally; SA8 §9, items 1–2]

4. **`A/Intermediary/Code/src/Main.cpp` lines 199–237 and the
   equivalent block in `B`** have the entire `Adder/Extractor/Wetlands`
   merge step commented out. The C++ Intermediary therefore produces
   only per-SSP CH4 and N2O scenario outputs — never the
   `total_methane_nitrogen_rcpRCPsspSSP.txt` 3-column combined product
   that IMOGEN actually consumes. The reference combined files in
   `Data/Intermediary/Emissions/` were produced by an earlier build
   with the merge step uncommented. [SA5 §4, §9]

5. **`IMOGENCXX/ImogenCXX/src/Main.cpp`** is structurally a faithful
   port of the Fortran but functionally incomplete: `DAY_CALC` is an
   empty stub (the Fortran's 462-line sub-daily disaggregation
   routine), `SOLPOS` is a one-line placeholder, `DTEMP_OUT` is never
   assigned, `} while (KEEPRUNNING = true);` at line 2626 is an
   assignment masquerading as a comparison (infinite loop),
   `SETTING_LPJG` *creates* the `done` file instead of *deleting* it
   (polarity inverted), the spin-up block uses `push_back()` where it
   meant to zero existing entries (corrupts `FA_OCEAN`, `DTEMP_O`,
   `SEED_RAIN`), and the settings-file path is hard-coded to a
   Windows-only absolute. The C++ refactor *cannot* complete a year of
   simulation in its current state. [SA4 §9]

6. **`A/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f:4131–4134`**
   ends `QSAT` with a `PAUSE` statement — a Fortran intrinsic that
   halts execution awaiting an interactive keystroke. `QSAT` is called
   inside `DAY_CALC` for every gridcell × every sub-day step × every
   day × every month. With the `PAUSE` enabled, any non-interactive
   (cluster, batch, automated) run will block at the first call.
   [SA3 §13]

7. **`A/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/setup_run.sh`**
   is the only run-launcher shipped in either repository. It is a
   one-line script that invokes `setup_run_owl_with_scratch_lpj_work.sh`
   — a helper that **was not in either coupled-model repo at audit
   time but has since been located** (5 May 2026) at
   `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/setup_run_owl_with_scratch_lpj_work.sh`,
   along with the full owl-cluster scripts toolkit (`mpi_run_guess_on_tmp.sh`,
   `finishup_lpj_work_owl.sh`, `submit.sh`, etc.). The unified codebase
   incorporates these at step 16 of the rebuild plan
   (see EXECUTION_PLAN.md Part V). The README's "planned bash script"
   was never written for the coupled-framework specifically, but the
   per-rank parallelism, gridlist-split, MPI invocation, and SLURM
   submission infrastructure all already exist in the owl scripts
   toolkit and need only minor coupled-framework adaptations
   (e.g. `INPUTMETHOD=imogencfx` rather than `cfx`; shared
   `<DIR_COMMON>` to coordinate the per-rank IMOGEN engine handshake).
   [SA8 §1.3, §3]

The first six are bugs in source files (≤ 50 lines of edits in total to
fix). The seventh is a missing artefact (one new shell script of ~50
lines).

### 1.3 What works, what does not, and what was never wired

| Status legend | |
|---|---|
| ✅ | Works in isolation. Has been run end-to-end at least once and produced reference outputs that are still on disk. |
| ⚙️ | Builds cleanly, runs partially, but does not complete its intended job in the current configuration. |
| ❌ | Cannot run end-to-end as committed. |
| 🔌 | Exists but is not wired into the framework. |

| # | Component | Path | Status | One-line current verdict |
|---:|---|---|:---:|---|
| 1 | LPJ-GUESS LandSyMM fork (standalone, `cf`/`cfx` modes) | `Integrations/trunk/trunk_r13078/` | ✅ | Builds and runs with `-input cfx`. Identical to standalone LandSyMM fork modulo five cosmetic and one critical (`exit(200)`) regression. |
| 2 | LPJ-GUESS in tight-coupling mode (`-input imogencfx`) | same | ❌ | Halts at `exit(200)` after `RUN_IMOGEN_ENGINE()`. Single-line fix restores function. |
| 3 | LPJ-GUESS in loose-coupling mode (`-input imogen`) | same | ⚙️ | Reads pre-generated IMOGEN climate from disk; latent N-deposition bug (`ndep.getndep` commented out at `imogen_input.cpp:728`); year-template logic uses bare `Y` instead of `%Y`. |
| 4 | Fortran IMOGEN (standalone) | `Common-directory/IMOGEN-codebase/code/imogen_lpjg.f` | ⚙️ | `gfortran` builds it; the working version produced 230 year-dirs in `Common-directory/IMOGEN/output/` on 2025-06-16. Cluster/batch runs blocked by `PAUSE` in `QSAT`; many Windows-style `mkdir \` paths; gridlist hard-capped at `NGPOINTS=3698`. |
| 5 | Fortran IMOGEN under tight coupling | same | ❌ | The polling protocol is fine; the failure mode is the LPJ-GUESS side per item #2. |
| 6 | C++ IMOGEN refactor (`IMOGENCXX`) | `IMOGENCXX/ImogenCXX/src/Main.cpp` | ❌ | Single-file 2 631-LOC port. `DAY_CALC` empty, `SOLPOS` placeholder, infinite year loop, hard-coded Windows path for settings, no build system at all. Has never run end-to-end. **Adds two output files Fortran lacks: `Rh_anom.dat` (relative humidity) and `W_anom.dat` (wind speed) — both with real engine data, both verified at `climatemodel.cpp:875-876, 903-904, 915-916` with `//DKB` annotations. Fortran's `imogen_lpjg.f` writes neither (zero matches in grep).** Phase 1 of the IMOGEN-rebuild strategy ports these two writers back into Fortran-with-`ALLOCATABLE` so the two backends produce parity output. |
| 7 | Imogen-controller (driver) | `Imogen-controller/` | 🔌 | Three `.cpp` variants; Makefile builds the wrong (Windows-only) one on Linux. Polling path uses Windows `\\` separator and points at `LPJG_main\\IMOGEN\\done` — but actual `done` files live at `IMOGEN/output/<YYYY>/done`. Never invoked from any shipped script. |
| 8 | C++ Intermediary (CH4/N2O scenarios only) | `Intermediary/Code/` | ⚙️ | **Verified additionally:** builds cleanly on Linux to `bin/ipcc` (882 KB, version A, `g++ -std=c++17`). `Main.cpp` Adder/Extractor/Wetlands merge block commented out. Reference outputs in `Data/Intermediary/Emissions/` were produced when this block was uncommented in an earlier build. Version A has bugs that B fixes (`calcNitrogenExcretion`, `n2ofertilizer.csv` read). |
| 9 | C++ Intermediary (full IMOGEN-bound merge) | same | ❌ | Adder is dead code. Magic year-offset 160 hardcodes `firstyear=1850`. Spline/taper harmonisation absent (working paper §2.3.4 prescribes it). |
| 10 | Python Intermediary (`imogen_ghg_controller v0.1.0`) | `Intermediary_py/` | ✅ 🔌 | Runs end-to-end (~25 min) via `python run_all.py`; 3 pytest tests pass; produces 5 wide + 1 long IMOGEN-input CSVs; reproducibility-tested against earlier runs (39/40 CSVs and 13/14 plots byte-identical). **Not wired into the framework**: no shared input format with framework's PLUM/LPJ-GUESS outputs; Quick_Start.md explicitly defers IMOGEN input-file spec. |
| 11 | GCM patterns — CMIP5 ASCII (34 GCMs) | `Common-directory/IMOGEN-codebase/patterns/CEN_*_MOD_*` | ✅ | Active forcing for current Fortran IMOGEN runs. Each dir is 12 month-files × 1631 cells (HadCM3 land grid). |
| 12 | GCM patterns — CMIP3 legacy HadCM3 | `…/patterns/ukmo_hadcm3_rel/` | ✅ | Same format as CMIP5. Used historically; can be retired once CMIP5/CMIP6 ensemble is validated. |
| 13 | GCM patterns — CMIP6 NetCDF (5 GCMs) | `…/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/` | 🔌 | 4-MB-each `<gcm>_patterns.nc` (CF-1.7) + 245-byte `<gcm>_params.json`. Not consumed by Fortran or C++ IMOGEN. |
| 14 | Regrid (CMIP/IMOGEN→user gridlist) | `Regrid/` | ❌ | Visual-Studio-only project. No CMakeLists, no Makefile. Hardcoded Windows paths. lat-overwrite/lon-no-overwrite asymmetric bug. |
| 15 | FastRegrid (re-engineered library + driver) | `FastRegrid/FastRegrid/` | ❌ | Has CMake, but references lowercase `regrid.cpp`/`fastregrid.cpp` while disk has PascalCase → fails on case-sensitive Linux. Links OpenMP but contains no `#pragma omp` anywhere — dead linkage. |
| 16 | RegridLPJG (LPJG `.out` → IMOGEN gridlist) | `RegridLPJG/RegridLPJG/` | ❌ | Visual-Studio-only. Was run once on Windows (committed `closest_points.txt`, 17 MB). lat/lon field-name swap (cancels at output but smelly). 14 of 15 file types disabled by comment. |
| 17 | NdepFastArchive (re-pack `Data/Ndep/*.bin`) | `NdepFastArchive/` | ❌ | No Makefile or CMakeLists. Windows-path hardcoded in `Main.cpp`. Header files for 5 scenarios (`GlobalNitrogenDeposition*RCP*.h`) auto-generated 2015. |
| 18 | Matlab plot scripts | `Matlab-scripts/` | 🔌 | Three `.m` files for IIASA-CMIP6 comparison plots. Hardcoded relative path `IIASA_DATABASE/...` not present anywhere in repo. |
| 19 | Python plot notebook | `Python-scripts/` | 🔌 | One Colab-exported `.py` + `.ipynb`. Hardcoded `/content/drive/MyDrive/...` paths. Reads files that exist in `Data/Intermediary/` but with a different relative root. |
| 20 | Plots/ (pre-rendered PNGs) | `Plots/` | ✅ | 9 static PNGs (`CMIP6_{CH4,CO2,N2O}_LPJG_IPCC_{NON_,}SIMULATED.png`, etc.). Outputs of items #18/#19. |

### 1.4 What this document recommends

Build a **single new repository** at
`landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm/` (the
empty directory the user already created) using the following rules of
thumb:

1. **Adopt the LPJ-GUESS LandSyMM fork at its standalone-canonical state.**
   Take the standalone fork (`lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`),
   *not* the trunk_r13078 inside the framework, since the latter has the
   `exit(200)` regression and a few other accidental edits. Replay the
   coupled-framework's `data/ins/integrated-4.1-ins*` and the runtime
   ins files from `landsymm_imogen{,_setup}/SSP1_RCP26/` into the new
   repo's `runs/` directory.
2. **Two IMOGEN implementations, phased delivery.** The Fortran
   IMOGEN works after small fixes plus a Fortran refactor that
   converts the ~30 statically-declared arrays to `ALLOCATABLE`,
   removing the practical gridlist cap (~3700 cells in the
   static-allocation regime; 62 000+ cells in the heap-allocated
   `ALLOCATABLE` regime — see §4.3.3). The C++ refactor remains
   broken (25 active bugs including an empty `DAY_CALC`) but is
   structurally faithful and brought to parity in Phase 4b of §12.4
   using the Fortran outputs as the numerical-parity reference. Both
   versions are then exposed as switchable IMOGEN backends. **The C++
   is not archived — it is preserved as a second implementation for
   cross-validation.**
3. **Adopt the Python Intermediary as the canonical Intermediary
   Controller.** The C++ Intermediary is in incomplete and bug-ridden
   even where it does run, the Python one is end-to-end-tested and
   reproducible. Build a thin adapter layer between the framework's
   PLUM/LPJG output paths and the Python pipeline's `inputs/` layout.
4. **Build the missing top-level orchestration.** Replace the
   `setup_run_owl_*` invocation with a self-contained `run_coupled.sh`
   (workstation) and a SLURM/batch template (cluster). See §12.5 for
   detailed proposal.
5. **Retire dead code aggressively.** Per §8 and §10, delete or archive:
   the C++ Intermediary's commented-out merge step, the `Intermediary_py`
   triplication, the four pre-baked `IMOGEN_SSP*_RCP*_Clim/` dirs in `A/`,
   the Visual Studio MSBuild leftovers in `Regrid/`, `RegridLPJG/`,
   `FastRegrid/`, the SVN remnants in `Integrations/hector/`, the older
   paper draft `Imogen_paper_GMD.docx`, the Word lock files, the
   double-extension `README.txt.txt` files, etc.
6. **Harmonise documentation to the working paper.** The paper draft
   `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` is the scientific
   source-of-truth. The C++ "coupling docs" docx is an outdated
   technical manual; the older `Imogen_paper_GMD.docx` is superseded;
   `Brief Documentation of N2O Disaggregation` is OUTDATED. Build a
   single, current technical manual in `docs/technical_manual.md` of
   the new repository, citing the working paper for the science and
   citing the implementation for the code.
7. **CI, tests, and reproducibility.** None of the components in either
   tree has CI or systematic regression tests (the Python Intermediary
   has 3 tests; the C++ has none; LPJ-GUESS has the upstream catch2
   suite that is not exercised). The unified codebase needs at minimum:
   GitHub Actions / GitLab CI to build the LPJ-GUESS binary on Linux,
   build the Fortran IMOGEN, build the Python Intermediary venv, and
   run the existing 3 pytest tests. Add a `make smoke` recipe that runs
   one year of one tiny gridlist coupled to a one-year IMOGEN call.

The full roadmap is in Section 12.

---

## 2. Scientific framework — what LandSyMM-IMOGEN is *supposed* to be

### 2.1 Lineage and citations

The framework is named **LandSyMM-IMOGEN** in the supervisor-reviewed
working paper draft `References/IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`
(2026-04-24, 12.6 MB). Its full title:
> *"A novel coupled model framework to explore the influence of bottom-up
> agricultural, land use, and management emissions on climate-ecosystem
> interactions."*

The framework brings together five lineages, each documented by a
peer-reviewed paper that is physically present in `References/` (see §7
for an exhaustive doc map):

| Lineage | Component | Reference (in `References/`) |
|---|---|---|
| Dynamic vegetation modelling with managed land + N | LPJ-GUESS | Smith 2014 (cited; not in `References/`); Lindeskog 2013 (`Lindeskog-al-Accounting_for_forest_management...pdf`); Olin 2015 (`esd-6-745-2015_Olin.pdf`); Wania 2010 LPJ-WHyMe (cited; not present); Smith 2001 framework paper (`Smith_2001_LPJ-GUESS – an ecosystem modelling framework...pdf`) |
| Land-use / management economic optimisation | PLUM v2 | Alexander 2018 (`Alexander et al 2017 Adaptation of global land use and management intensity...pdf`, B-only); Engström 2016 (cited) |
| LandSyMM ecosystem services | LandSyMM | Rabin 2020 (`Rabin et al 2020 Impacts of future agricultural change...pdf`, B-only) |
| Climate emulation via pattern-scaling | IMOGEN | Huntingford 2010 (`IMOGEN-gmd-3-679-2010.pdf`, also a duplicate at `IMOGEN-codebase/docs/huntingford_et_al_10.pdf`); Huntingford & Cox 2000 (`IMOGEN-codebase/docs/huntingford_and_cox_00.pdf`); Zelazowski 2018 22-GCM patterns (`Zelazowski_et_al_2018_Climate pattern-scaling set for an ensemble of 22 GCMs...pdf`, with a B-only duplicate at `gmd-11-541-2018.pdf`); Mathison 2025 PRIME / FaIR-IMOGEN (`gmd-18-1785-2025.pdf`, B-only); Hayman 2021 CH4 mitigation (`Hayman-esd-12-513-2021.pdf`); Smith 2018 FAIR v1.3 (`gmd-11-2273-2018.pdf` and a duplicate `…-1.pdf`); Martín Belda 2022 LPJ-GUESS/LSMv1 (`gmd-15-6709-2022.pdf`, B-only) |
| Tier-1 GHG inventories | IPCC | IPCC 2019 Refinement V4 Ch5 Cropland (`19R_V4_Ch05_Cropland.pdf`), Ch10 Livestock (`19R_V4_Ch10_Livestock.pdf`), Ch11 Soils (`19R_V4_Ch11_Soils_N2O_CO2.pdf`); Wetlands Supplement Ch7 / App3 / Entire (`V4_07_Ch7_Wetlands.pdf`, `V4_p_Ap3_WetlandsCH4.pdf`, `Wetlands_Supplement_Entire_Report.pdf`); IPCC 2006 V2 Ch1 (`V2_1_Ch1_Introduction.pdf`, B-only); IPCC AR5 WG1 Ch6 (`WG1AR5_Chapter06_FINAL.pdf`, B-only) |
| Reference budgets | Top-down checks | GMB 2025 Saunois (`essd-17-1873-2025_GMB.pdf`); GNB 2024 Tian (`essd-16-2543-2024_GNB.pdf`); GCB 2025 Friedlingstein (`essd-17-965-2025_GCB.pdf`); RCMIP Phase 2 (cited; not in `References/`) |

The framework is committed to **SSP1–RCP2.6 + SSP2–RCP4.5** as the
evaluation scenarios (the older draft `Imogen_paper_GMD.docx` used
SSP1+SSP5 — that draft is OUTDATED), to a **0.5° × 0.5° common grid**, to
a **1850–2100 horizon** with a **500-year soil/N spin-up at pre-industrial
CO₂ (~285 ppm)** under 1850–1900 climatology, and to **ISIMIP-3b
MRI-ESM2-0** as the GCM pattern (the older draft used IPSL-CM6-MR — also
OUTDATED). FaIR v1.3 is integrated upstream of IMOGEN's energy-balance
model, *"following the approach implemented in the PRIME framework
(Mathison et al., 2025)"* (working paper §2.1.3).

### 2.2 The two-stage protocol

The working paper §2.4.3 describes a two-stage closed-loop protocol:

**Stage I — Open-loop yield generation.**
LPJ-GUESS is driven with prescribed ISIMIP-3b MRI-ESM2-0 climate for the
entire 1850–2100 horizon to produce **factorial-management potential
yields** for PLUM. The factorials are 6 management treatments:
3 fertilisation levels × 2 irrigation regimes (rainfed vs irrigated).
This stage is uncoupled — no IMOGEN, no Intermediary. The output is
yield surfaces per CFT × treatment × year × grid cell that PLUM uses to
optimise land-use allocation per SSP–RCP scenario.

**Stage II — Closed-loop emissions/feedback.**
Per year (or per multi-year window), starting from the spun-up state at
1850:

1. **PLUM** consumes the yield surfaces and produces per-country / per-grid
   land-use change (LUC), crop fractions, fertiliser application, and
   irrigation for that year.
2. **LandSyMM-driven LPJ-GUESS** ingests the LUC + climate forcing and
   simulates ecosystem fluxes — producing the natural CH4 (LPJ-WHyMe
   wetlands >40°N), natural N2O (managed-soils + fire, with the
   double-counting caveat of §2.3 below), and net biome productivity
   NBP / NEE.
3. **The Intermediary Controller** (the working paper's §2.4.1 IC; in
   the codebase, either the C++ `Intermediary/` or the Python
   `Intermediary_py/`) takes the natural fluxes from LPJ-GUESS, computes
   anthropogenic IPCC tier-1 emissions from PLUM activity data (livestock
   counts, fertiliser application, rice paddy area, manure-management
   shares per region), substitutes these into the IIASA CMIP6
   trajectories, and produces a single annual all-source vector of
   CH4/N2O/CO2 emissions for that year.
4. **IMOGEN** reads that emissions vector + the GCM pattern coefficients
   for the chosen GCM and computes pattern-scaled monthly climate
   anomalies for the next year, plus updated atmospheric CO2/CH4/N2O
   concentrations and radiative forcing.
5. The cycle returns to step 2 with updated climate forcing, until 2100.

The "tight coupling" mode trades data year-by-year via files (`done` markers
plus per-year `*_anom.dat`/`CO2.dat` and per-year LPJG flux files); the
"loose coupling" mode runs one full IMOGEN climate trajectory ahead of
time and feeds it into LPJ-GUESS as if it were prescribed climate. Both
modes are nominally supported. See §3.3 for the LPJ-GUESS-side input
modules that select which mode is active at run time.

### 2.3 Sector ownership and double-counting prevention

The framework's central design decision is **how to combine LPJ-GUESS
natural fluxes, IPCC tier-1 anthropogenic estimates, and IIASA-prescribed
CMIP background emissions without double-counting**. The working paper
§2.4.4 states the rule explicitly:

> Each gas species is partitioned across "modelled" sectors (LPJ-GUESS +
> IPCC tier-1 / PLUM) and "non-modelled" sectors (IIASA-prescribed,
> typically energy/industry/transport/waste/land-use change), with the
> latter retained at face value and the former replaced by the bottom-up
> estimate where one is available.

In code:

- **Pre-LPJG period (1850 ≤ y < 1961 in CMIP5; 1850 ≤ y < 1990 in CMIP6).**
  No bottom-up estimate exists. Use IIASA totals unchanged, summing the
  `lpjg_simulated.txt` and `non_lpjg_simulated.txt` IIASA-component
  files that the working paper's documentation calls out as
  `IIASA_lpjg` and `IIASA_non_lpjg` respectively (see
  `imogen_intermediary.ins` keys `IIASA_lpjg_1850_2100` and
  `IIASA_non_lpjg_1850_2100`).

- **Historic LPJG/IPCC period (1961 ≤ y < 2010 in CMIP5; 1990 ≤ y <
  2010 in CMIP6).** LPJ-GUESS provides natural CH4/N2O. IPCC tier-1
  applied to **OWI/FAO** historic activity data provides the
  agricultural anthropogenic. IIASA's `lpjg_simulated.txt` is
  *replaced* by these two; IIASA's `non_lpjg_simulated.txt` is kept
  at face value because none of LPJG/IPCC simulate fossil/industrial.

- **Scenario period (2010 ≤ y ≤ 2100).** LPJ-GUESS still provides the
  natural CH4/N2O. IPCC tier-1 applied to **PLUM v2** scenario activity
  data provides the agricultural anthropogenic. IIASA remains as the
  non-modelled background. (CO2 case: LPJG NEE provides
  natural+land-use, plus EFOS from RCMIP / IIASA fossil-only — see
  §2.3.2 below for the Python pipeline's specific framing.)

The C++ Intermediary's `Adder::startAddition` encodes this regime
exactly (with a magic offset of 160 that hardcodes `firstyear=1850`); see
[SA5 §9] for the literal code. Three regime branches with explicit year
boundaries.

#### 2.3.1 LPJ-GUESS scope note on N2O

LPJ-GUESS soil N2O includes both natural and indirect (perturbed by N
deposition / fertilisation) emissions. The IPCC tier-1 estimator
(`Calculator::calcN2OManagedSoils`) computes only the **direct
managed-soils** N2O term `(F_SN+F_ON+F_CR+F_SOM)·EF1` of Eq 11.1 — it
does *not* compute indirect N2O (Eq 10.26-10.29 leaching/volatilisation
or Ch11 EF4/EF5). LPJ-GUESS's `N2O_soil` output may therefore include
some emissions that GNB classifies as anthropogenic. The Python pipeline
flags this in `TECHNICAL_MANUAL.md §15.5` as a residual ~5–8 % bias and
does not correct it. [SA6 §8.3]

#### 2.3.2 CO2 sector ownership — Option A (Python pipeline canonical)

The Python Intermediary (HANDOFF.md §8.1, TECHNICAL_MANUAL §1.5) names
the CO2 framing as **Option A**:

- Anthropogenic CO2 = RCMIP `Emissions|CO2|MAGICC Fossil and Industrial`
  (= EFOS) **only**. Land-use anthropogenic CO2 is NOT taken from RCMIP
  `MAGICC AFOLU` because LPJ-GUESS NEE already carries those components.
- Natural CO2 = LPJ-GUESS NEE (which equals the sum of
  Veg+Repr+Soil+Fire+Est+Seed+Harvest+LU_ch+Slow_h+Manure≡0 —
  i.e. *includes* anthropogenic LULC fluxes by construction).
- Combined `EFOS + NEE` matches GCB's "atmospheric source"
  (`EFOS + ELUC − SLAND`) up to ±1σ, validated empirically against
  Friedlingstein 2025 Table 7 (verified test:
  `tests/test_co2_option_a_validation.py`).

The C++ Intermediary's CO2 path is structurally similar
(`cflux_iiasa_co2_1850_1960_lpjg_2100`: IIASA CO2 1850-1960 + LPJG
cflux 1961-2100; the IIASA `non_lpjg` CO2 file enters separately)
[SA5 §8.3] but has not been recently exercised end-to-end.

The working paper does not name "Option A"; the Python doc-set adopted
that label after-the-fact. The working paper §2.4.4 prose is
consistent with Option A.

#### 2.3.3 Wetland CH4

The working paper §2.2.7 states:
- **>40°N** wetland CH4 from **LPJ-WHyMe** (Wania 2010), as
  implemented in LPJ-GUESS via the wetland PFTs declared in
  `wetlandpfts.ins`.
- **Tropical wetland CH4** retained as the IIASA residual (acknowledged
  bias).
- **Managed peatlands** disabled.

The Python Intermediary additionally applies two GMB 2025 (Saunois
Table 3) constants when assembling the natural CH4 baseline:
- **+112 Tg/yr** for IFW (inland fresh water).
- **−23 Tg/yr** for DCC (dam/canal correction).
- Result column `CombinedDCC_TgCH4_best = LPJ_wetland + 89 Tg/yr`,
  applied uniformly 1901–2100 [SA6 §7.1].

The C++ Intermediary's `Wetlands::startCalculation` instead applies a
Tier-1 EF (Eq 3A.1) to a static GLWD3 wetland-area CSV and broadcasts
the single global sum to every year. This is conceptually inconsistent
with both the working paper and the Python pipeline; the C++ Adder
acknowledges it ("removed methane here since LPJG is producing it now |
30.05.2023" comment at `Adder.cpp:92,96` — the C++ Intermediary's
Wetlands output was *already retired* in the active merge logic).

### 2.4 Boundary harmonisation

The working paper §2.3.1, §2.3.4 prescribe **Backward Tapered
Harmonisation (BTH)** (B = 10 yr for CO2, 30 yr for CH4/N2O) +
**Regression-Based Trend Matching** + **5-year Centred Moving Average**
to smooth the IIASA-pre-1961 → IPCC/LPJG-post-1961 boundary and the
historic→scenario 2010/2020 boundary.

**Both implementations are inconsistent with this prescription.**

- The C++ Intermediary's smoothing block (`Adder.cpp:114–164`) is
  commented out. `centeredMovingAverage` is defined but never
  invoked. [SA5 §9]
- The Python pipeline implements only **segmented running-mean
  smoothing** at the historical/scenario boundary; there is no BTH or
  spline harmonisation. [SA6 §1.2 (HANDOFF.md), §13.2 item 15.4]
- A separate B-only document `Emissions Handling Methodology.docx`
  describes a third option: **Univariate Spline ratio of modelled
  total to IIASA total**. This is also not implemented.

This is an explicit **documentation-vs-code mismatch** flagged in the
master findings table (§9, contradiction #4 of the documentation
investigation). Resolving it is a Roadmap §12 deliverable — either
(a) update the paper to describe what the code actually does, or (b)
implement BTH in the unified Intermediary.

### 2.5 Validation thresholds

The working paper §2.4.7 sets quantitative validation gates:

| Gate | Threshold |
|---|---|
| Sectoral inventory PBIAS (vs FAO/EDGAR) | ±15 % |
| CO2 atmospheric concentration RMSD vs observations | ≤ 5 ppm |
| CH4 atmospheric concentration RMSD vs observations | ≤ 50 ppb |
| N2O atmospheric concentration RMSD vs observations | ≤ 5 ppb |
| Validation period | 1850–2020 (or as far as observations allow) |

The Python Intermediary records achieved values per scenario and decade
in `HANDOFF.md §4`:

- **CO2:** SSP2-4.5 mean 2014–2020 atmospheric source = 7.93 PgC/yr vs
  GCB best 7.6 ± 1.24 PgC/yr → within ±1σ.
- **CH4:** within range for 2000–2009 decade.
- **N2O:** within range for all reported periods.

These are pipeline-level validations; concentration RMSD against atmospheric
observations would require running IMOGEN with the integrated emissions
and comparing with a CO2/CH4/N2O concentration record (e.g. NOAA GMD,
AGAGE) — that benchmark has not yet been run end-to-end in either tree.

### 2.6 Acknowledged biases and limitations

The working paper itself is candid about limitations (§2.2.3, §2.2.5,
§2.4.6) and the Python TECHNICAL_MANUAL §15 expands them:

- **Tier-1 EFs static 2020–2100** (Eq 2 = arithmetic mean across
  productivity systems). Acknowledged Tier-1 limitation.
- **Rice continuous-flooding bias** = +15 to +40 % high.
- **Managed-soil N2O** ≈ −20 to −30 % low (because EF3, EF4, EF5 are
  excluded).
- **Blended EF1 = 0.01** vs IPCC-2019 default 0.011 → ≈ −6 to −7 % low.
- **No Tier-2/Tier-3** in the Python implementation. ~30–40 % per-sector
  uncertainty relative to country Tier-2 inventories.
- **No formal uncertainty propagation.** Comparator bands are
  observation σ, not pipeline σ.
- **GMB IFW (+112) and DCC (−23) constants** with no temperature
  dependence — likely a conservative constraint at end-of-century.
- **Scenario boundary discontinuity at 2020/2021.** Each LPJ-GUESS
  scenario is an *independent* simulation with its own spin-up state,
  so N2O drops by ~3 Tg N2O between historical 2020 and scenario 2021.
  Real model behaviour, not a bug; documentation needs to address it
  (per HANDOFF §8.2).

---

## 3. System architecture

### 3.1 Component inventory

The framework is composed of eight functional components plus three
auxiliary tooling trees and one references / documentation tree. Their
on-disk locations and one-line roles:

| # | Component | Tree | Source language | Role |
|---:|---|---|---|---|
| 1 | **LPJ-GUESS LandSyMM fork** (`trunk_r13078`) | `Integrations/trunk/trunk_r13078/` | C++ (CMake, C++11) | Dynamic vegetation / DGVM. Hosts the 6 input modules including `imogen` (loose) and `imogencfx` (tight). The IMOGEN engine is **statically linked** into the same `guess` binary via `modules/climatemodel.cpp` + `IMOGENConfig` namespace globals. |
| 2 | **Fortran IMOGEN** | `Common-directory/IMOGEN-codebase/code/` | Fortran 77/90 (gfortran) | Standalone climate emulator. `imogen_lpjg.f` (4138 LOC, 17 subroutines) + `nonco2.f` (174 LOC, 2 subroutines). Reads `imogen_settings.txt` + per-call `imogen_lpjg.txt`. Emits per-year `*.dat` + a `done` marker. Working version of IMOGEN. |
| 3 | **C++ IMOGEN refactor** (`IMOGENCXX`) | `IMOGENCXX/ImogenCXX/src/Main.cpp` | C++ (no build system) | Single 2 631-LOC file. Structurally faithful port of the Fortran but functionally incomplete; never run end-to-end. Frozen for archive. |
| 4 | **Imogen-controller** | `Imogen-controller/` | C++ (Makefile) | Standalone driver intended to fake the LPJG↔IMOGEN year-by-year handshake when the two are run as separate processes. Three `.cpp` variants (Windows, Windows, cross-platform); Makefile builds the wrong one. Never invoked from any shipped script. |
| 5 | **C++ Intermediary** | `Intermediary/Code/` | C++17 (Makefile) | Legacy IPCC tier-1 emissions estimator. Builds on Linux. Active code path produces only CH4 + N2O scenario outputs (Adder/Extractor/Wetlands merge step is commented out). Reference combined outputs in `Data/Intermediary/Emissions/` are from an earlier build with the merge step active. Buggy in version A; B fixes some bugs, breaks others. |
| 6 | **Python Intermediary** (`imogen_ghg_controller v0.1.0`) | `Intermediary_py/` | Python ≥ 3.10 (pyproject.toml) | Current end-to-end IPCC tier-1 + integration pipeline. Four-component A/B/C/D layout. Produces 5 wide + 1 long IMOGEN-input CSVs. 3 pytest tests pass. Reproducibility-tested. **Not wired into the framework.** |
| 7 | **GCM patterns** | `Common-directory/IMOGEN-codebase/patterns/` | data | 34 CMIP5 ASCII GCM pattern dirs + 1 CMIP3 legacy + 1 CMIP6 NetCDF (5 GCMs). The CMIP6 NetCDF is on disk but unconsumed by either Fortran or C++ IMOGEN. |
| 8 | **Regrid utilities** | `Regrid/`, `FastRegrid/`, `RegridLPJG/` | C++ (Visual Studio + CMake) | Three independent regridding programs. None build cleanly on Linux as committed. Hard-coded Windows paths throughout. |
| Aux 1 | **NdepFastArchive** | `NdepFastArchive/` | C++ (no Makefile) | Re-pack utility for the Lamarque-format `Data/Ndep/*.bin` files. |
| Aux 2 | **Matlab-scripts** | `Matlab-scripts/` | MATLAB | Three IIASA-CMIP6 comparison plot scripts. Out-of-repo `IIASA_DATABASE/` paths. |
| Aux 3 | **Python-scripts** | `Python-scripts/` | Python (Colab notebook) | One auto-exported plot notebook with hardcoded Colab-Drive paths. |
| Aux 4 | **Plots** | `Plots/` | data | 9 pre-rendered PNG comparison plots — outputs of Aux 2/3. |
| Doc | **References** | `References/` | mixed (docx, pdf, txt) | ~70 documents. The supervisor-reviewed working paper draft is the science source-of-truth. Many older drafts are OUTDATED. See §7. |

### 3.2 Process model — single binary, not two processes

A common misconception (encouraged by the README's mention of a
"planned bash script that automates the simultaneous execution of both
models") is that LandSyMM-IMOGEN is a *two-process* system in which
LPJ-GUESS and IMOGEN run as independent OS processes communicating via
a filesystem rendezvous (`done` markers + flux files + climate files).

**This is not how the shipped code is wired.** As verified by Subagents 2
and 8:

- The IMOGEN sources (`modules/climatemodel.cpp`, plus the
  `IMOGENConfig` parameter namespace in `framework/parameters.cpp`,
  plus `modules/imogen_input.cpp` for loose mode and
  `modules/imogencfx.cpp` for tight mode) are **listed unconditionally
  in `modules/CMakeLists.txt`**, are **statically linked into the same
  `guess` binary**, and are **invoked synchronously from
  `IMOGENCFXInput::init()` via `RUN_IMOGEN_ENGINE()`**.
- There is **no `IMOGEN`/`COUPLED`/`HAVE_IMOGEN` CMake flag**. The
  IMOGEN code is always present in the binary. Whether the user invokes
  it is decided at runtime by the `-input <module>` CLI argument:
  - `-input cfx` → no IMOGEN involvement (standard LandSyMM CFX run).
  - `-input imogen` → loose coupling: LPJ-GUESS reads pre-existing
    IMOGEN ASCII month-files from disk, no engine invocation.
  - `-input imogencfx` → tight coupling: the engine runs *first* (as
    the last step of `init()`), produces all years' climate, then
    LPJ-GUESS would proceed (in principle) to consume them. The
    `exit(200)` after `RUN_IMOGEN_ENGINE()` currently halts the
    process at this point.
- The polling loop inside `climatemodel.cpp:300–394` is the IMOGEN
  engine's own loop, watching for LPJ-GUESS-side flux files and `done`
  markers it expects to be written *by the same process* later in its
  `iyear` loop. The variable names (`runnowExist`, `imogen_lpjg.txt`,
  `LPJG_main/IMOGEN/done`) reflect a legacy two-process design that was
  ported in-process, but the safety semantics (3-second polls,
  `is_open()` guards) were neutered in the port.

**The Imogen-controller binary** (`Imogen-controller/`) was built to
*drive* a separate-process design — it would write `imogen_lpjg.txt`
year-by-year and create a `done` file to nudge the IMOGEN side. **It is
never invoked from any shipped script.** Its `done`-poll path uses the
Windows separator (`LPJG_main\\IMOGEN\\done`) and points at the wrong
subdirectory anyway, so even if it were started it would never see the
real `done` files (which are at `IMOGEN/output/<YYYY>/done`).

**Implication for the unified codebase.** Either (a) commit to the
single-binary design and retire `Imogen-controller/`, or (b) re-engineer
the framework around a true two-process design — IMOGEN as a separate
binary or library, LPJ-GUESS as another, and a thin Python/Bash
orchestrator. The audit recommends **(a)** as the lower-risk path: the
single-binary design is closer to working, and the polling and
file-handshake infrastructure can be retained as a debug instrumentation
layer rather than a synchronisation primitive. See §12.

### 3.3 Coupling modes — tight, loose, standalone

Three coupling modes are nominally supported, selected by the
`-input <name>` CLI arg to `guess`:

| Mode | CLI flag | LPJ-GUESS class | IMOGEN run | Required ins-file additions | Use |
|---|---|---|---|---|---|
| Standalone (no IMOGEN) | `-input cfx` | `CFXInput` | not invoked | none | LandSyMM standard runs (Stage I yield generation, the existing factorial-management work) |
| Loose | `-input imogen` | `ImogenInput` | run ahead-of-time as standalone Fortran or C++ binary; output staged on disk | `searchradius`, `lon/lat_offset_to_midpoint`, `firsthistyear`/`lasthistyear`, `monthly_imogen`, `ndep_timeseries`, climate-file path templates with `Y` placeholder | Reproducibility studies, sensitivity to LPJG perturbations under fixed climate |
| Tight | `-input imogencfx` | `IMOGENCFXInput` | invoked in-process at end of `IMOGENCFXInput::init()` via `RUN_IMOGEN_ENGINE()` | All loose params PLUS ~80 `IMOGENConfig` engine params (`DIR_PATT`, `FILE_SCEN_EMITS`, `KAPPA_O`, ...) PLUS ~30 Intermediary params PLUS coupling-control flags `YEAR1`, `IYEND`, `YEAR1_LPJG`, `SPINUP`, `KEEPRUNNING`, `FIRSTCALL` | Closed-loop coupled simulations (the framework's core scientific use case) |

A fourth nominal mode in the README is `imogen_input` (= `imogen` at the
class level — they're synonyms; `REGISTER_INPUT_MODULE("imogen", ImogenInput)`
in `imogen_input.cpp:175`). The other 3 LPJ-GUESS input modules
(`demo`, `cf`, `firemip`) are upstream LPJ-GUESS or LandSyMM defaults
unrelated to IMOGEN coupling.

The loose-mode and tight-mode classes share substantial code; tight
extends loose and adds the engine kick-off plus ~110 additional
ins-parameters. See §4.1 for the full surface comparison.

### 3.4 The `done`-file rendezvous protocol

Two distinct `done` files exist; their roles must not be confused.

#### A. LPJG → IMOGEN handshake: `<DIR_COMMON>/LPJG_main/IMOGEN/done`

- **Written by:** LPJ-GUESS, *after* it finishes a year and emits the
  flux files (`<FILE_LPJG_FLUX>` plus optional `<FILE_LPJG_CH4_N2O_FLUX>`)
  and the per-call `imogen_lpjg.txt` settings file.
- **Read by:** the IMOGEN engine's polling loop in `climatemodel.cpp:300–394`
  and `imogen_lpjg.f:357–390`. The loop polls every 3 seconds via
  `INQUIRE`/`stat`; once `imogen_lpjg.txt`, `<FILE_LPJG_FLUX>`, and
  optionally `<FILE_LPJG_CH4_N2O_FLUX>` plus the `done` file are all
  present, the engine reads them and processes one year.
- **Deleted by:** the engine, in two places:
  1. `imogen_lpjg.f:1498–1500` inside `SETTIN_LPJG` after parsing the
     per-call settings.
  2. `imogen_lpjg.f:591–593` (defensive duplicate) and
     `climatemodel.cpp:544–546` after consuming the year's inputs.

In the **current LPJ-GUESS C++ build**, this handshake is *partly
neutered*. The `INQUIRE` was replaced by `doneExist = true;` (line
330–331) and three of the safety guards were commented out. The
existence of the `done` file is therefore not actually required for the
inner polling loop to advance.

#### B. IMOGEN → LPJG handshake: `<DIR_COMMON>/IMOGEN/output/<YYYY>/done`

- **Written by:** the IMOGEN engine, after the year's per-variable
  `*_anom.dat`, `WET.dat`, `CO2.dat`, `dtemp_o.dat`, and `fa_ocean.dat`
  files are flushed (`imogen_lpjg.f:1049–1052`,
  `climatemodel.cpp:938–945`). The payload is the literal string
  `Climate files written\n`, 22 bytes.
- **Read by:** the LPJ-GUESS-side `imogencfx::getclimate` for the next
  year's climate. This is the file LPJ-GUESS *should* poll for before
  reading climate, but as Subagent 2 found, the LPJ-GUESS framework
  side does **not** appear to do this polling — it assumes the engine
  has already produced *all* years' output ahead of time, since the
  `RUN_IMOGEN_ENGINE()` call at `imogencfx.cpp:482` runs the entire
  year-loop in one call.

This second `done` file is currently of operational interest only in
*loose-coupling* mode (where IMOGEN was run as a separate Fortran
binary via `Imogen-controller`/`compile.sh` and stages its output for
LPJ-GUESS to read offline).

#### C. The standalone Imogen-controller's role (legacy)

The Imogen-controller binary (`Imogen-controller/Imogen-controller-cross.cpp`)
implements an external 2-process protocol where:

1. The controller writes `imogen_lpjg.txt` for the next year (year N) into
   `<DIR_COMMON>/LPJG_main/IMOGEN/`.
2. The controller creates `<DIR_COMMON>/LPJG_main/IMOGEN/done` to signal
   to a **separate IMOGEN process** that input is ready.
3. The IMOGEN process reads `imogen_lpjg.txt`, deletes `done`, processes
   the year, writes `<DIR_COMMON>/IMOGEN/output/<N>/done`.
4. The controller polls every 5 seconds; when the IMOGEN-side `done`
   appears, advance to year N+1.

In the current code:
- The controller's `done`-poll path uses Windows `\\` separators —
  inoperable on Linux without rewriting (`Imogen-controller-cross.cpp:158`).
- The controller's `done`-poll path is `<DIR_COMMON>/LPJG_main/IMOGEN/done`,
  but the IMOGEN-side write goes to `<DIR_COMMON>/IMOGEN/output/<N>/done`
  — different directories. Even on Windows it would never see the file.
- The controller is never invoked from `setup_run.sh`, `main.ins`, or
  any Makefile target except its own `make run`.

**Bottom line:** the `done` rendezvous is a **vestigial design** in the
single-binary build. The unified codebase should either:
- (a) Retire `Imogen-controller/` entirely; rename the `done` files in
  the IMOGEN engine output as plain `imogen_year_complete.flag` and
  treat them as informational only; or
- (b) Preserve the rendezvous as a *debug instrumentation* primitive
  for tracing year-by-year flow, but document clearly that it is not
  used for synchronisation in the production build.

### 3.5 Data flows — intended vs actual

The intended data flow per the working paper is summarised here; the
actual on-disk evidence is then noted.

```
                            ┌────────────────────┐
                            │ HILDA+ v2 historic │
                            │ + LUH2 harmonised  │
   ┌─────────────────────┐  │ PLUMv2 SSP-RCP     │
   │ ISIMIP-3b MRI-ESM2-0│  └────────┬───────────┘
   │ climate forcing     │           │
   └──────────┬──────────┘           │
              │                      │
              v                      v
       ┌──────────────────────────────────────┐  ┌────────────────────────┐
       │ STAGE I: LPJ-GUESS open-loop         │  │ FAOSTAT, OWI, GLWD3,   │
       │ factorial-management runs            │  │ EDGAR, GMB/GNB/GCB     │
       │ (3 fert × 2 irrig = 6 treatments)    │  │ reference budgets      │
       │ → potential yield surfaces per CFT   │  └────────────┬───────────┘
       └──────────┬───────────────────────────┘               │
                  │                                            │
                  v                                            v
       ┌──────────────────────────────────────┐  ┌────────────────────────────┐
       │ PLUM v2 economic optimisation        │  │ Intermediary Controller    │
       │ → annual LU, fert, irrig, livestock  │←─│ (Python: A=anthropogenic   │
       │   per country/grid for SSP-RCP       │  │  IPCC tier-1; B=natural    │
       └──────────┬───────────────────────────┘  │  LPJG; C=integration;      │
                  │                              │  D=IMOGEN export)          │
                  │  (PLUMharm / scenario        │                            │
                  │   harmonisation 2010/2020)   │                            │
                  v                              │                            │
       ┌──────────────────────────────────────┐  │                            │
       │ STAGE II YEAR LOOP (1850 → 2100)     │  │                            │
       │                                      │  │                            │
       │  LPJ-GUESS year                      │  │                            │
       │   ↓ flux: NBP/NEE, CH4_wetland,      │──┘                            │
       │     N2O_soil+fire                    │                               │
       │                                      │                               │
       │  IC merge:                           │                               │
       │   anthropogenic (PLUM + IPCC)        │                               │
       │   + natural (LPJG)                   │                               │
       │   + non-modelled (IIASA, fossil/etc) │                               │
       │   → 3-col CH4/N2O/CO2 emissions year │                               │
       │                                      │                               │
       │  IMOGEN year                         │                               │
       │   ↑ in: emissions vector             │                               │
       │   pattern-scaled climate forcing     │                               │
       │   ↓ out: T,P,SW,LW,RH,wind,DTEMP     │                               │
       │     (12 monthly + sub-daily)         │                               │
       │   + atmospheric CO2/CH4/N2O          │                               │
       │     concentrations (Joos+FAIR)       │                               │
       │                                      │                               │
       │  → next year                         │                               │
       └──────────────────────────────────────┘                               │
                  │                                                            │
                  v                                                            │
       ┌──────────────────────────────────────┐                               │
       │ Final ecosystem-service indicators   │                               │
       │ (LandSyMM scope: C stocks, runoff,   │                               │
       │  biodiversity, N pollution)          │                               │
       └──────────────────────────────────────┘                               │
                                                                              │
       ┌──────────────────────────────────────────────────────────────────────┘
       │ All of the above happens with the FaIR v1.3 ERF module integrated
       │ upstream of IMOGEN's energy-balance model (Mathison 2025 PRIME).
       └──── (running in parallel as the climate forcing engine)
```

**Actual on-disk evidence**, comparing each arrow to current state:

| Arrow | Intended | On-disk evidence (A unless noted) | Status |
|---|---|---|---|
| HILDA+v2 + PLUMv2 → LPJG forcing | Land-use + crop fractions + fertiliser at 0.5° annual 1901–2100 | `Data/LU/SSP1_RCP26_concatenated/{LU,cropfracs,nfert,irrig}_SSP1_RCP26_1901_2100_final.txt` (7.3 GB total). Only SSP1_RCP26 realised; other 4 SSPs missing on disk. | ✅ for SSP1-2.6; ❌ for other SSPs |
| Stage I LPJ-GUESS factorial yields | 6 management treatments × CFT × year × grid | Not present on disk under `Data/`. The user's notes mention "`do_potyield`/`isforpotyield`" mode added to the integrated LTS in earlier project work; that capability lives in the LPJ-GUESS code but has not been exercised in this framework's `Data/` outputs. | ❌ |
| PLUM optimisation | annual fert/livestock/landuse 2010-2100 per SSP | `Data/Intermediary/PLUM_data/animals_ssp{1..5}.txt`, `plum_land_use/SSPx_s1_YYYY_LandUse.txt`, `agg_land_use/SSPx_s1_LandUseAgg.csv`. Present for all 5 SSPs. | ✅ |
| LPJ-GUESS year flux (Stage II) | per-year LPJG fluxes written to `<DIR_COMMON>/LPJG_main/IMOGEN/imogen_lpjg_flux.txt` etc. | `imogen_lpjg_flux.txt` = 10 bytes, contains literal `2100\t0.00\n`. `imogen_lpjg_ch4_n2o_flux.txt` = 13 bytes, contains literal `2100\t202\t9.1\n`. **Verified additionally:** these are stale placeholders from 2025-06-12 manually placed; LPJ-GUESS has not actually populated them. | ❌ |
| IC merge | per-year combined CH4/N2O/CO2 vector | `Data/Intermediary/Emissions/total_methane_nitrogen_rcp26ssp1.txt`, `…rcp85ssp5.txt` — pre-existing reference outputs from a previous run with the C++ Adder uncommented. The current C++ `Main` does not produce these. The Python pipeline produces equivalent files at `Intermediary_py/imogen_ghg_controller_FULL/outputs/imogen_inputs/imogen_inputs_SSP*.csv`. | ⚙️ (legacy refs exist; current code doesn't reproduce) |
| IMOGEN year out | per-year `*.dat` + `done` per gridcell | `Common-directory/IMOGEN/output/<YYYY>/{T_anom.dat, …, done}` for 1871-2100 (230 dirs). **Verified additionally:** logs show ~4-5 s wall-clock per year, ergo this was a **standalone IMOGEN-only seeding run on 2025-06-16**, not a coupled run. CO2 reaches 3 775 ppm by 2100, indicating an unconstrained-emissions test trajectory rather than a real RCP/SSP run. | ⚙️ (standalone OK; coupled never run) |
| Final indicators | ecosystem-service indicators per Rabin 2020 figure | Not present on disk. | ❌ |
| Coupled-run launcher | self-contained bash + cluster batch script | `setup_run_owl_with_scratch_lpj_work.sh` was missing at audit time but **located 5 May 2026 at `owl_hpc_cluster_scripts/scripts/`** alongside the full cluster toolkit; integrated at step 16 of the V.1 rebuild plan (workstation `run_coupled.sh` + cluster `submit.sh` template generated by the existing setup script). | ⚙️ (now feasible) |

The five `Common-directory/IMOGEN_SSP*_RCP*_Clim/` directories
(2.4 GB combined) are pre-archived per-scenario climate runs with the
same layout as `IMOGEN/output/`, evidently checkpointed in June 2025 so
subsequent LPJG-only experiments could read climate without re-running
IMOGEN. They are run *outputs*, not source, and should be moved out of
git. They are absent in version B.

### 3.6 Annotated process diagram

A more detailed view, showing the runtime processes, the in-process
IMOGEN-engine call, and the file rendezvous, for a tight-coupled run
(`-input imogencfx`, current single-binary design):

```
                        ┌─────────────────────────────────────────────────┐
                        │ guess BINARY (single OS process)                │
                        │                                                 │
                        │ main() in command_line_version/main.cpp         │
                        │  ↓                                              │
                        │ framework.cpp::run()                            │
                        │  ↓                                              │
                        │ create_input_module("imogencfx") → IMOGENCFXInput│
                        │  ↓                                              │
                        │ IMOGENCFXInput::init()  [imogencfx.cpp:341..]   │
                        │  ├ read all 110+ ins parameters                 │
                        │  ├ resize all_temp/all_prec/... vectors         │
                        │  ├ ndep.getndep(...)                            │
                        │  ├ read gridlist                                │
                        │  ├ for each gridcell: lon_lat_lines_in_file()   │
                        │  │   (Euclidean lon/lat NN match to IMOGEN grid)│
                        │  ├ RUN_IMOGEN_ENGINE();   [climatemodel.cpp:151]│
                        │  │   ├ create dir Common-directory/IMOGEN/      │
                        │  │   ├ ImogenLogger::initialize()               │
                        │  │   ├ read imogen_settings.txt                 │
                        │  │   ├ for iyear = YEAR1..IYEND:                │
                        │  │   │  ├ poll for LPJG flux files (3-s sleep)  │
                        │  │   │  ├ read flux files                       │
                        │  │   │  ├ delete LPJG_main/IMOGEN/done          │
                        │  │   │  ├ read climatology + patterns           │
                        │  │   │  ├ DELTA_TEMP, GCM_ANLG, CLIM_CALC       │
                        │  │   │  ├ apply emissions / Joos ocean          │
                        │  │   │  ├ write per-year *_anom.dat, CO2.dat... │
                        │  │   │  └ write IMOGEN/output/<YYYY>/done       │
                        │  │   └ end iyear loop                           │
                        │  └ exit(200);   ⊗ HALTS HERE — bug #1           │
                        │                                                 │
                        │ (rest of LPJ-GUESS init, the gridcell loop,     │
                        │  and getclimate per-year-per-cell are unreached)│
                        └─────────────────────────────────────────────────┘

                        ┌─────────────────────────────────────────────────┐
                        │ FILESYSTEM RENDEZVOUS (relative to DIR_COMMON)  │
                        │                                                 │
                        │ LPJG_main/IMOGEN/                               │
                        │  ├ imogen_lpjg.txt        (LPJG → IMOGEN: per-  │
                        │  │                         call settings)       │
                        │  ├ <FILE_LPJG_FLUX>       (LPJG → IMOGEN: C flux│
                        │  │                         table, currently     │
                        │  │                         "2100\t0.00")        │
                        │  ├ <FILE_LPJG_CH4_N2O_FLUX>                     │
                        │  ├ done                   (LPJG → IMOGEN:       │
                        │  │                         "I'm done with year  │
                        │  │                          N, your turn")      │
                        │  └ error                  (either side: abort)  │
                        │                                                 │
                        │ IMOGEN/                                         │
                        │  ├ CO2_all.dat            (cumulative)          │
                        │  ├ RF_all.dat             (cumulative)          │
                        │  ├ VARYEAR.dat            (climate-variability  │
                        │  │                         iterator 1..30)      │
                        │  └ output/<YYYY>/         (one dir per year)    │
                        │     ├ T_anom.dat                                │
                        │     ├ P_anom.dat                                │
                        │     ├ SW_anom.dat                               │
                        │     ├ WET.dat                                   │
                        │     ├ DTEMP_anom.dat                            │
                        │     ├ Rh_anom.dat                               │
                        │     ├ W_anom.dat                                │
                        │     ├ CO2.dat                                   │
                        │     ├ dtemp_o.dat                               │
                        │     ├ fa_ocean.dat                              │
                        │     └ done           ("Climate files written\n")│
                        └─────────────────────────────────────────────────┘
```

The legacy two-process design (with a separate `imogen_lpjg.exe`
process and the `Imogen-controller` driver) overlays this same
filesystem rendezvous but invokes IMOGEN as a child OS process from a
shell loop. That design is dead code.

### 3.7 The `FILE_LPJG_FLUX` path-override — "loose coupling masquerading as tight coupling"

A subtle but consequential additional finding (verified additionally
during the Phase-3 cross-reference): in the active run setups, the
**LPJG → IMOGEN flux channel is configured to read from a static
IIASA-derived reference file rather than from any LPJ-GUESS-produced
output**. This converts the nominal "tight coupling" into what is
effectively a one-way IMOGEN-driven run with prescribed
"LPJG-style" emissions.

#### 3.7.1 What the active ins file actually points at

`A/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/imogen_intermediary.ins:63`:

```
FILE_LPJG_FLUX "/home/bampoh-d/Desktop/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Data/Imogen/emiss/CMIP6/Co2/co2_pg_emissions_natural_historical_ssp126_1850_2100.txt"
```

`B/landsymm_imogen/SSP1_RCP26/imogen_intermediary.ins:63`:

```
FILE_LPJG_FLUX "/bg/data/lpj/bampoh-d/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Data/Imogen/emiss/CMIP5/Co2/co2_emissions_landuseonly_historical_rcp26.txt"
```

Both are absolute paths pointing to **pre-computed static "natural CO2"
reference files** for the chosen scenario. The filenames are explicit
about this: `co2_pg_emissions_natural_*` (A, CMIP6) and
`co2_emissions_landuseonly_*` (B, CMIP5). They are **time series of
LPJ-GUESS-style NEE / land-use CO2 fluxes that someone has pre-computed
once from a prior LPJ-GUESS-only run** (or from an equivalent
IIASA-style decomposition labelled as the "LPJG-modelled" component),
gzipped or text-stored, and staged here for IMOGEN to read as if they
were the live LPJG flux feedback. They are 251-line files (one row per
year 1850-2100) that do not change with any LPJG state — the data are
baked in, scenario-specific.

Sibling files in the same directory follow the same naming pattern for
both gases and both ownership classes:

```
co2_pg_emissions_anthropogenic_historical_ssp126_1850_2100.txt   ← FILE_SCEN_EMITS  (anthropogenic CO2)
co2_pg_emissions_natural_historical_ssp126_1850_2100.txt         ← FILE_LPJG_FLUX   (natural CO2 — pre-computed from LPJG)
ch4_n2o_annual_historical_anthropogenic_ssp126_1850_2100.txt     ← FILE_CH4_N2O_EMITS  (anthropogenic CH4+N2O)
ch4_n2o_annual_historical_natural_ssp126_1850_2100.txt           ← FILE_LPJG_CH4_N2O_FLUX (natural CH4+N2O — pre-computed from LPJG)
```

This naming makes explicit the **two-class data ownership** that the
audit eventually surfaced (§3.5 and §3.7.5):
- Anthropogenic CO2 / CH4 / N2O → owned by the **Intermediary**
  (Python or C++); pre-computed once.
- Natural CO2 / CH4 / N2O → owned by **LPJ-GUESS**; either pre-computed
  once (current setup) or written live per-year (the working paper's
  intent in tight-coupled mode).

#### 3.7.2 How the override is interpreted by the engine

The Fortran reader at `imogen_lpjg.f:565-566` (also the C++ port at
`climatemodel.cpp` polling loop):

```fortran
OPEN(63, FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//FILE_LPJG_FLUX)
```

When `FILE_LPJG_FLUX` is an absolute path starting with `/`, the
concatenation produces a string like
`<DIR_COMMON>/LPJG_main/IMOGEN//home/bampoh-d/.../co2_pg_emissions_natural...txt`,
which on POSIX collapses the leading `//` into `/` and resolves to the
absolute path because the absolute portion takes precedence over the
relative prefix. The engine therefore reads the IIASA static file,
**not** the LPJG-side placeholder
(`Common-directory/LPJG_main/IMOGEN/imogen_lpjg_flux.txt`).

This behaviour is reproducible and reliable across gfortran versions
on Linux. (On Windows, the same concat can produce a malformed path
with mixed separators — but that is academic for this Linux-only project.)

#### 3.7.3 What gets read in the current configuration

The static file `co2_pg_emissions_natural_historical_ssp126_1850_2100.txt`
is **a CMIP6 IIASA-derived natural CO2 emissions trajectory for SSP1-2.6**,
labelled "natural" because it represents the LPJG-modelled component
that is ordinarily simulated by the DGVM. It does not include
fossil/industrial emissions (those are in the sibling
`co2_pg_emissions_anthropogenic_*.txt` file referenced as
`FILE_SCEN_EMITS` at line 60 of the same ins file).

So when the engine polls and reads `FILE_LPJG_FLUX`, it gets exactly
the same 251-row natural-CO2 trajectory every year, regardless of any
LPJG state, and uses those values as the LPJG-feedback contribution to
the C-cycle update inside `imogen_lpjg.f:766-794` (the `LPJG_CFLUX`
branch). LPJ-GUESS itself, even if it had produced its own NEE/NBP
fluxes (which it currently does not because of `exit(200)`), would not
influence this trajectory.

#### 3.7.4 The on-disk placeholder files in `LPJG_main/IMOGEN/`

Three small files exist in the directory the engine polls:

```
imogen_lpjg.txt              369 B   6 lines   (handshake settings — YEAR1=1871, KEEPRUNNING=TRUE)
imogen_lpjg_flux.txt          10 B   1 line    "2100\t0.00\n"
imogen_lpjg_ch4_n2o_flux.txt  13 B   1 line    "2100\t202\t9.1\n"
```

These are **vestigial template stubs** placed manually on 12 June
2025 (per file mtime). They have the filenames the Fortran defaults
expect (the `imogen_settings_tmpl.txt` defaults are
`FILE_LPJG_FLUX imogen_lpjg_flux.txt`), but they cannot satisfy the
schema: with `NYR_LPJG_FLUX 251` set in the active ins file, the
Fortran read at `imogen_lpjg.f:566-571` would call `READ(63,*) YR_LPJG(N), C_LPJG(N)`
in a 251-iteration loop and hit EOF on iteration #2.

In the current configuration these files are **never read** because
the absolute-path override in the active ins file redirects the open
to the static IIASA file. They sit in the directory unconsumed.

#### 3.7.5 Implications

This finding amplifies finding §1.2 break-point #1 in two ways:

1. **The `exit(200)` fix alone is necessary but not sufficient for
   real two-way coupling.** Even after `exit(200)` is removed and
   LPJG's `init()` proceeds past the engine call, the engine has
   already finished its full year-loop using the static IIASA file as
   "LPJG fluxes". LPJ-GUESS subsequently consumes the engine's climate
   output, but its own NEE/NBP values never feed back to influence the
   IMOGEN climate trajectory. The system runs as a **one-way
   IMOGEN-prescribed-climate experiment**, not a closed-loop DGVM
   coupling.

2. **Restoring real two-way coupling requires three additional
   changes** beyond the §1.2 list:
   - **Rewrite `FILE_LPJG_FLUX` and `FILE_LPJG_CH4_N2O_FLUX`** to
     point at LPJG-produced files. The natural target is
     `imogen_lpjg_flux.txt` (the placeholder file currently in the
     same `LPJG_main/IMOGEN/` directory) — i.e. a relative filename
     not an absolute path, so the engine's concat resolves to the
     intended `<DIR_COMMON>/LPJG_main/IMOGEN/imogen_lpjg_flux.txt`.
   - **Implement the LPJG-side writer** for these files. Subagent 2's
     open question #3 (§11.1, item 3 of the master doc) flagged that
     no LPJG-side writer was located for `imogen_lpjg.txt`,
     `<FILE_LPJG_FLUX>`, or `<FILE_LPJG_CH4_N2O_FLUX>`. Either the
     writer exists in `gcpoutput.cpp` / `commonoutput.cpp` and the
     audit missed it (worth grepping for the literal filename), or it
     was never implemented and must be added. The writer's responsibility
     is, at the end of each LPJG year:
     - Write `imogen_lpjg.txt` with the next-year settings (`YEAR1`,
       `IYEND`, `YEAR1_LPJG`, `SPINUP`, `KEEPRUNNING`, `FIRSTCALL`).
     - Append the year's row `<year> <flux>` to
       `imogen_lpjg_flux.txt` (CO2 in TgC/yr or PgC/yr per the
       engine's expected unit).
     - Append the year's row `<year> <ch4> <n2o>` to
       `imogen_lpjg_ch4_n2o_flux.txt` (Tg/yr each).
     - Touch `<DIR_COMMON>/LPJG_main/IMOGEN/done` to signal the
       engine.
   - **Decide on the configuration's intent.** The current "static
     IIASA reference file as `FILE_LPJG_FLUX`" mode is useful as a
     **prescribed-emissions sensitivity experiment** (it lets one run
     IMOGEN with a fixed emissions trajectory while varying other
     parameters). The unified codebase should preserve this as an
     **explicit, documented mode** (e.g. `coupling_mode = prescribed`)
     distinct from the closed-loop mode (`coupling_mode = tight`).
     This avoids the silent-misconfiguration trap where a user thinks
     they are running coupled but is actually running prescribed.

#### 3.7.6 Diagnostic test for the unified codebase

Before any production tight-coupled run, the unified codebase should
include an automated check that:

- If `coupling_mode = tight`:
  - `FILE_LPJG_FLUX` and `FILE_LPJG_CH4_N2O_FLUX` are **relative
    filenames** (not absolute paths).
  - The corresponding files in `<DIR_COMMON>/LPJG_main/IMOGEN/` start
    with the spin-up year (or are empty if `FIRSTCALL=TRUE`).
  - The LPJG-side writer is reachable (e.g. by checking that
    `MiscOutput` or `gcpoutput` registers a callback for the path).
- If `coupling_mode = prescribed`:
  - The override paths exist and have the right number of rows
    (`NYR_LPJG_FLUX`).
  - A warning is printed at run start: *"Running in PRESCRIBED mode:
    LPJG fluxes are read from `<path>`; LPJ-GUESS-simulated fluxes will
    NOT influence the climate trajectory."*

---

## 4. Per-component deep dives

This section distils each subagent report into a self-contained
component overview (~2–4 pages each). The subagent reports remain the
canonical evidence and are cited inline as `[SAn §x]`. No new content
is introduced beyond what the subagents found, except where flagged
"verified additionally" — those are findings this consolidation pass
introduced through follow-up grep / read / build experiments.

### 4.1 LPJ-GUESS LandSyMM fork (`trunk_r13078`)

**Path:** `Integrations/trunk/trunk_r13078/`
**Detailed report:** `_phase2_findings/02_lpjguess_trunk_r13078.md` (58 KB)

#### 4.1.1 Provenance

The tree is the standard "LPJ-GUESS Version 4.1" Lund SVN-trunk-r13078
layout, forked into LandSyMM and then again into the coupled-model
framework. **Verified additionally**: this fork is byte-identical to
the standalone `lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/` that the
user previously committed to GitHub/KIT/Helmholtz, with **6 source
files differing** [SA2 §8.1] — only one of those 6 is a behavioural
regression (the `exit(200)` in `imogencfx.cpp`), the other five are
cosmetic comment changes.

#### 4.1.2 Build

- **Top-level:** `CMakeLists.txt` (project = `guess`, CMake 2.8.12.2…3.5.2,
  C++11). Optional `find_package(NetCDF)`, `find_package(MPI)` —
  both used.
- **Outputs:** `guess` (Unix CLI), `guesscmd` + `guess.dll` (Windows
  shell, not relevant), `runtests` (catch-based unit tests, gated by
  `UNIT_TESTS` CMake var, not exercised in this framework).
- **Pre-built tree:** `build_imogen/CMakeCache.txt` records last build
  with `c++=/usr/bin/c++` (gcc-14), Release, no flag overrides.
- **IMOGEN linkage is unconditional.** The 5 IMOGEN-related
  source files (`imogen_input.cpp`, `imogencfx.cpp`, `intermediary.cpp`,
  `climatemodel.cpp`, `imogenlogger.cpp`) are listed verbatim in
  `modules/CMakeLists.txt:36-41, 76-81`. There is no `IMOGEN`/`COUPLED`
  CMake flag.

#### 4.1.3 The 6 input modules

Selected at runtime by `-input <name>`:

| `-input` | Class | LOC | Role |
|---|---|---|---|
| `demo` | `DemoInput` (`modules/demoinput.cpp`) | 361 | Reference demo. ASCII monthly + scalar CO2/Ndep. |
| `cf` | `CFInput` | 1233 | CF-NetCDF, optional `HAVE_NETCDF`. Standard. |
| `cfx` | `CFXInput` | 2118 | Extended CF-NetCDF (multi-file, per-CFT N-fert, popdens, GGCMI multi-part, SSR/PLUM/LandSyMM). **The non-coupled LandSyMM working horse.** |
| `firemip` | `FireMIPInput` | n/a | FireMIP variant. Unrelated to coupling. |
| `imogen` | `ImogenInput` | 936 | **Loose coupling.** Reads pre-generated IMOGEN ASCII climate from disk. No engine invocation. |
| `imogencfx` | `IMOGENCFXInput` | 1105 | **Tight coupling.** Inherits from cfx-style ingestion plus the engine kick-off. |

[SA2 §3, §4]

#### 4.1.4 `imogen_input` (loose) anatomy

The loose-coupling class reads year-templated FORTRAN-ASCII text files
(`<dir>/<year>/T_anom.dat`, etc.) one full year at a time into
`all_temp[store_index][igrid][day]` arrays in `init()`+first
`getclimate` per year, then serves them per gridcell × per day in
`getclimate()`.

**Key parameters declared in the constructor:**
- `searchradius` (km) — for nearest-neighbour matching of LPJ-GUESS
  gridcells to IMOGEN gridlist.
- `lon_offset_to_midpoint`, `lat_offset_to_midpoint` (degrees) — if
  IMOGEN data are cell-corner rather than cell-midpoint.
- `firsthistyear`, `lasthistyear` — class members; class also has hard-coded
  fallbacks `FIRST_HIST_YEAR=1901`, `NYEAR_RUN=200`,
  `FIRST_SPINUP_YEAR=1871`, `NYEAR_SPINUP=30` in the header.
- `monthly_imogen` — selects monthly vs daily data path.
- `ndep_timeseries` — Lamarque-archive timeseries name (`historic`,
  `rcp26`, ...).

**Climate file path `param "file_temp"` etc.** are expected to contain
a literal `Y` somewhere in the path, which `gen_filename()` replaces
with the 4-character year string. The substitution mechanism uses
`fname.find("Y")` rather than `fname.find("%Y")` (line 117); any other
literal `Y` upstream in the path will be wrongly matched. [SA2 §3.4.1]

**Bugs in the loose path** (per [SA2 §3.4.5, §10]):
- Line 728: `ndep.getndep(...)` is **commented out**. The `ndep` object
  is then used at line 855 in `getclimate` (`ndep.get_one_calendar_year`)
  with no prior initialisation → undefined behaviour. 🔴 **active bug**
  for any loose-coupled run.
- Line 380-383: `extract_line_data()` only parses 12 monthly values; the
  daily branch (`for idx<MAX_YEAR_LENGTH`) is missing. 🟡 — daily files
  silently produce zero arrays.
- Line 494-495: distance metric uses raw `(file_lons - lons)²` without
  antimeridian wrap. 🟡 — gridcells near ±180° won't match.
- Line 116-129: `find("Y")` instead of `find("%Y")`. 🟡 — fragile.
- Line 39-94: `_mkdir` helper recurses without ever calling the OS
  syscall (commented out at line 88, 92). 🟡 — directory creation
  silently fails. Currently dormant (no callers pass `fmakedir=true`).

#### 4.1.5 `imogencfx` (tight) anatomy

`IMOGENCFXInput` is forked from `ImogenInput` and adds:
- ~80 `IMOGENConfig::*` parameters (engine config) declared in the
  constructor at lines 213–339, all written into the `IMOGENConfig`
  namespace globals defined in `framework/parameters.cpp`.
- ~30 Intermediary parameters (config keys for paths, scenario flags).
- 5 coupling-control flags (`YEAR1`, `IYEND`, `YEAR1_LPJG`, `SPINUP`,
  `KEEPRUNNING`, `FIRSTCALL`).
- 4 mode flags (`simulation_mode`, `feedback_mode`, `interpolation_mode`,
  `ssprcp`).
- Two extra climate variables: `drelhum`, `dwind` (relative humidity,
  wind speed), with member arrays declared in the header but **never
  consumed by `get_climate_for_gridcell`**. **Verified additionally:**
  `param "file_relhum"` and `param "file_wind"` from the ins file are
  declared in the ins but `imogencfx.cpp::init()` does NOT consume
  them — only `file_temp`, `file_prec`, `file_insol`, `file_wetdays`,
  `file_dtr`, `file_co2` are consumed (lines 370-376, 1000). The
  framework's BLAZE fire model would have used wind+relhum but is
  unwired.
- The IMOGEN engine kick-off:

  ```482:483:Integrations/trunk/trunk_r13078/modules/imogencfx.cpp
  	RUN_IMOGEN_ENGINE();
  	exit(200);
  ```

**Scope of `imogencfx` — what it owns vs what falls through to standard LPJG inputs.**
This is a frequently-asked design question that the audit clarified
fully. `imogencfx` is **literally `cfx` with the climate and CO2
inputs swapped for IMOGEN-derived equivalents**; everything else flows
through the standard LPJ-GUESS input mechanisms exactly as in a
non-coupled `cfx` run.

What `imogencfx` consumes from IMOGEN (the only IMOGEN-specific
input path):

| Ins-file param | Consumed at | Maps to LPJG `Climate` field |
|---|---|---|
| `param "file_temp"` | `imogencfx.cpp:370` | `climate.temp` (after K→°C; bug L1 above) |
| `param "file_prec"` | `imogencfx.cpp:372` | `climate.prec` |
| `param "file_insol"` | `imogencfx.cpp:375` | `climate.insol` |
| `param "file_wetdays"` | `imogencfx.cpp:374` (only if `monthly`) | (used by Gerten precipitation generator) |
| `param "file_dtr"` | `imogencfx.cpp:376` (only if `ifbvoc`) | (BVOC module input) |
| `param "file_co2"` | `imogencfx.cpp:1000` (read in `getclimate`) | `co2` global |

`param "file_relhum"` and `param "file_wind"` are declared in the
ins file but **never consumed** by `imogencfx::init` or `getclimate`
(the audit verified this with grep). The C++ engine `climatemodel.cpp`
**does** produce `Rh_anom.dat` and `W_anom.dat` files (so the inputs
exist), but the LPJG-side reader has not been wired up for them.
This is the BLAZE wind/humidity unwiring identified in `[CMI §4.1.6]`
bug L5. Wiring requires ~30 LOC in `imogencfx.cpp`.

What flows through standard LPJG input mechanisms (unchanged from
`cfx`):

| Input class | LPJG class / call site | Ins-file param(s) |
|---|---|---|
| **Land cover** (cropfracs) | `LandcoverInput::init()` and `loadlandcover(lon, lat)` at `imogencfx.cpp:841, 868` | `file_lu`, `file_cropfracs` |
| **Management** (fertiliser, irrigation) | `ManagementInput::init()` and `loadmanagement(lon, lat)` at `imogencfx.cpp:843, 870` | `file_nfert`, `file_irrig` |
| **N deposition** (Lamarque) | `Lamarque::ndep.getndep(...)` at `imogencfx.cpp:896` | `file_ndep` |
| **Soil** | `SoilInput::init()` at `imogencfx.cpp:???` (called from base class) | `file_soildata` |
| **Population density** (SimFire/BLAZE) | `PopDensInput::getpopdens()` per year (from base class) | `file_popdens` |
| **Fire forcing** (SimFire archive) | `FireMIPInput::getclimate_year()` (from base class) | `file_simfire_*` |
| **NOx/NOy/NHx/NHy reactive nitrogen** (if used) | Same Lamarque/CRU input mechanisms | various per the standard LPJG ins file |

**Temporal-resolution handling.** The mismatch between IMOGEN's
monthly-or-sub-daily climate and LPJG's other annual-or-static
inputs is real, but LPJ-GUESS handles it natively:

| Input | Native temporal resolution | How LPJG handles |
|---|---|---|
| Climate (from IMOGEN) | Monthly (or sub-daily if `STEP_DAY > 1`) | Interpolated to daily via `interp_climate()` (`imogencfx.cpp:165-171`); Gerten precipitation generator + `interp_monthly_means_conserve` for everything else |
| Ndep (Lamarque) | Annual scalars | Read once per year; spread evenly across 365 days within year via `distribute_ndep()` |
| Popdens (SimFire/BLAZE) | Annual | Read once per year; held constant within year |
| LU / cropfracs / nfert / irrig | Annual per cell | Read once per year per cell; held constant within year |
| Soil | Static | Read once at init |
| CO2 (from IMOGEN in tight mode) | Annual scalar | Read once per year; held constant within year (same value used for all 365 days) |

So a coupled-mode LPJ-GUESS run with `imogencfx` is structurally
identical to a `cfx` run with the climate + CO2 swap; no
temporal-resolution complications introduced beyond what `cfx`
already handles. This means the existing LPJ-GUESS `cfx` run
infrastructure (ins-file params, the standard LandSyMM `landcover.ins`,
`crop.ins`, `crop_n.ins`, `pasture_n_*.ins`, the standard
`gridlist_*.txt`, `Data/Ndep/*.bin`, `Data/soil/*.dat`, the SimFire
binary archives) is reusable verbatim in the coupled framework. Only
`imogen_intermediary.ins` adds the IMOGEN-specific config and
overrides the climate/CO2 paths.

**Bugs and issues in `imogencfx`** (per [SA2 §3.5, §10]):
- Line 483: `exit(200);` — bug #1, the showstopper. 🔴 active.
- Line 1039: `climate.temp = dtemp[date.day];` — missing `- 273.15`
  Kelvin→Celsius conversion that exists in `imogen_input.cpp:871`. 🟡
  — currently dead (unreachable due to #1) but will activate the
  moment `exit(200)` is removed.
- Line 792-794: BLAZE-incompatibility `fail()` is commented out but
  `drelhum`/`dwind` are not plumbed — running with BLAZE will silently
  use zero humidity/wind. 🟡
- Line 668-669: same antimeridian bug as `imogen_input`. 🟡
- Line 553-556: same daily-branch missing as `imogen_input`. 🟡
- `imogencfx.h` and `imogen_input.h` use the **same header guard**
  `LPJ_GUESS_IMOGEN_INPUT_H`. Including both files in the same TU
  silently excludes the second. 🟢
- `imogencfx.cpp:122-135`: 12 IMOGEN output-stub `declare_parameter`
  calls have **incorrect description strings** (10 of 12 read "Imogen
  Temperature Anomalies." regardless of what the file actually
  contains). 🟢

#### 4.1.6 `IMOGENConfig` namespace and parameter table

The `IMOGENConfig` namespace is declared in `framework/parameters.h:437-561`
and defined in `framework/parameters.cpp:215-389`. It carries 110+
typed globals (xtring path strings, integers, doubles, booleans). All
are bound to ins-file keys via `declare_parameter()` calls in
`imogencfx.cpp:213-336` — one per global. The 41 keys recognised by
the Fortran `SETTIN` (see §4.2) are a strict subset of these.

The naming convention in the namespace is the same as in the Fortran
settings file: `DIR_PATT`, `FILE_SCEN_EMITS`, `KAPPA_O`, `Q2CO2`,
`TAU_DECAY_CH4`, `CO2_INIT_PPMV`, etc. The full table is reproduced in
Appendix A.2.

#### 4.1.7 `MiscOutput` IMOGEN stubs (dead code)

`modules/miscoutput.cpp:121-136` declares 12 ins-file parameters for
IMOGEN climate-output files (`file_t_anom`, `file_wet`, `file_sw_anom`,
`file_p_anom`, `file_fa_ocean`, `file_dtemp_o`, `file_dtemp_anom`,
`file_co2`, `file_relhum_anom`, `file_tmin_anom`, `file_tmax_anom`,
`file_wind_anom`). 12 corresponding `Table` objects are declared in
`modules/miscoutput.h:172`. **None are ever wired** — no
`create_output_table` calls, no `outannual` writers reference them.
They are scaffolding for an IMOGEN-data-output module that was never
completed.

The file also declares `getImogenData(int lower, int upper)` at
`miscoutput.h:69-79` as a method that returns a literal random number
from a Mersenne Twister seeded with `random_device`. **No callers
exist** anywhere in the tree. Dead placeholder. 🟡 [SA2 §6]

#### 4.1.8 Polling loop in `climatemodel.cpp`

The polling loop is the IMOGEN engine's own loop (lines 300-394),
embedded in `RUN_IMOGEN_ENGINE()`. Per outer year:

1. Spin in `while (!runnow)` 3-s sleeps.
2. Each iteration `stat()` four paths:
   - `<DIR_COMMON>/LPJG_main/IMOGEN/imogen_lpjg.txt`
   - `<FILE_LPJG_FLUX>` (relative to `<DIR_COMMON>/LPJG_main/IMOGEN/`)
   - optionally `<FILE_LPJG_CH4_N2O_FLUX>` if `NONCO2_EMISSIONS`
   - `<DIR_COMMON>/LPJG_main/IMOGEN/error` (abort signal)
3. The real `done` file `stat()` is **commented out** — `doneExist`
   is hardcoded `true` (lines 330-331). 🔴
4. The `is_open()` "still being written" guards
   (`runnowOpen`/`runfluxOpen`/`runnonco2fluxOpen`) are commented out
   (lines 334, 341, 350). 🔴

After consuming inputs: write `done` to `<DIR_COMMON_OUT>/IMOGEN/output/<YYYY>/`
and delete `<DIR_COMMON>/LPJG_main/IMOGEN/done`.

#### 4.1.9 `imogenlogger`

A trivial singleton text logger writing both to stdout and to a
timestamped file in `<DIR_COMMON>/IMOGEN/imogen_<YYYYMMDD_HHMMSS>.log`.
Mutex member is commented out (`//std::mutex mutex_;`) — not thread-safe.
Directory creation block commented out at lines 82-85; relies on
`RUN_IMOGEN_ENGINE` having pre-created the directory. Comment typo
`<C++!7` at line 20 (should be `<C++17`). [SA2 §3.6]

#### 4.1.10 Diff vs the standalone LandSyMM fork

[SA2 §8] confirmed the trunk_r13078 fork is byte-identical to
`lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/` except for **6 source
files** and a few build/CI artifacts:

| File | Diff | Consequence |
|---|---|---|
| `modules/imogencfx.cpp` | trunk has `exit(200);` at line 483 (1 line); standalone does not | The single critical regression. |
| `modules/cfxinput.cpp` | line 339 comment style; line 1131 error vs warning policy on missing climate data | Cosmetic + minor behavioural; not coupling-related. |
| `framework/parameters.cpp` | comments stripped from `IMOGENConfig` member declarations | Cosmetic. |
| `modules/climatemodel.cpp` | `#define logger ImogenLogger::getInstance()` macro use difference, comment refinements | Cosmetic. |
| `modules/imogenlogger.cpp` | comment typo `<C++!7` introduced, two annotation comments removed | Cosmetic. |
| `modules/imogenlogger.h` | one annotation comment removed | Cosmetic. |

Reverting `exit(200);` is therefore the only behaviourally-significant
change between the standalone fork and the trunk_r13078 in this
framework. Plus the standalone fork lacks `data/ins/integrated-4.1-ins/`,
the CI infrastructure (`.gitlab-ci.yml`), and `.vscode/`.

#### 4.1.11 The 6 ins-file dirs in `Integrations/trunk_r13078_test/`

| Dir | Purpose | Recommendation |
|---|---|---|
| `integrated-4.1-ins` | Loose-coupling reference (Windows paths) | Keep as offline baseline |
| `integrated-4.1-ins2` | **Most recent** tight-coupling, Windows | Keep as tight-coupling reference |
| `integrated-4.1-ins2-wsl` | Linux/WSL twin of ins2 (partial) | Keep after path cleanup |
| `lpj-guess_git-svn_20190828` | Empty placeholder | **Retire** (empty) |
| `lsa_hist_base_ipsl` | Linux scenario, IPSL forcing | Keep as named-scenario |
| `ssr-ins-version` | SSR/pasture-fert test variant, oldest | **Archive then retire** (predates coupling) |

[SA2 §9]

### 4.2 IMOGEN Fortran (the working IMOGEN)

**Path:** `Common-directory/IMOGEN-codebase/code/`
**Detailed report:** `_phase2_findings/03_imogen_fortran.md` (47 KB)

#### 4.2.1 Files

- `imogen_lpjg.f` — 4 138 lines, 1 PROGRAM + 17 SUBROUTINEs.
- `nonco2.f` — 174 lines, 2 SUBROUTINEs (`FAIR_NON_CO2_GHG`,
  `FAIR_NON_CO2_GHG_BUDGET`).
- `Makefile`, `compile.sh` — both build targets, both gfortran.
- `imogen_settings.txt` — 41 lines, recognised parameters (Windows
  paths and a hardcoded RCP8.5 IPSL-CM5A-MR run as the active default).
- `imogen_settings_tmpl.txt` — same with `$VARS` placeholders for
  shell-substitution.
- 6 gridlist files (`gridlist_global.txt` 13 rows, `gridlist_3deg.txt`
  2371 rows, `gridlist_hurtt_RNDM_midpoint_3698.txt` 3698 rows,
  `gridlist_hurtt_RNDM_midpoint_3711.txt` 3711 rows, `gridlist_out.txt`
  2371 rows, `patterns_gridlist.txt` 1631 rows).
- `ch4_n2o_annual_historical_rcp85_allsources_1850_2100.txt`,
  `qsat_output.txt` (debug dump, see §4.2.6 below).
- `Original Imogen Modified for LPJG Coupling/imogen_lpjg.f` — backup
  of an earlier version.
- `R_wrappers/` — 4 R scripts for non-coupled standalone IMOGEN runs.
- `patch_add_ch4_n2o_conc.diff` — 16-line patch already applied to
  the current `imogen_lpjg.f`.
- `patterns/` — 36 GCM-pattern dirs + 1 `readme.log` (see §4.7).
- `CRUNCEP_1960_1989/` — 30-year climatology base (Jan1..Dec30,
  1631 cells per file).
- `emiss/` — anthropogenic emissions / non-CO2 RF time series + IIASA
  CMIP5 RCP database.
- `docs/` — only the two foundational IMOGEN papers (Huntingford &
  Cox 2000, Huntingford et al. 2010); no internal docs.

#### 4.2.2 Subroutine catalogue

[SA3 §3], summarised:

| Line | Symbol | Role |
|---:|---|---|
| 16 | `PROGRAM IMOGEN` | Main controller. Settings, polling, year loop, output. |
| 1089 | `REGRID_CLIM` | NN regridding from 1631-cell native grid to user gridlist. |
| 1207 | `SETTIN` | Reads `imogen_settings.txt`. |
| 1439 | `SETTIN_LPJG` | Reads `imogen_lpjg.txt` (per-call settings from LPJ-GUESS). |
| 1511 | `DAY_CALC` | Sub-daily disaggregation: SW/T/LW/precip/pressure/wind/humidity. **The 462-line core that the C++ port leaves empty.** |
| 1973 | `REDIS` | Stochastic rainfall redistribution within a day. |
| 2120 | `SUNNY` | Sunshine fraction / mean cos(zenith) per day. |
| 2267 | `SOLPOS` | Sun-Earth orbital declination. |
| 2332 | `SOLANG` | Solar zenith / hour angle. |
| 2469 | `RNDM` | Park-Miller PRNG. |
| 2502 | `CLIM_CALC` | Anomaly + climatology → daily fields; calls `DAY_CALC` per day. |
| 2752 | `DELTA_TEMP` | Two-box land/ocean energy-balance time-stepper, 20×/yr. |
| 2927 | `INVERT` | Tridiagonal solver for the implicit ocean diffusion. |
| 3103 | `GCM_ANLG` | Pattern-scaling. Reads `<DIR_PATT>/<month>` 12 files, multiplies by ΔT_L. |
| 3253 | `OCEAN_CO2` | Joos mixed-layer ocean carbon uptake. |
| 3422 | `RESPONSE` | Joos pulse-response function. |
| 3459 | `RADF_CO2` | `Q_CO2 = (Q2CO2/ln 2) × ln(CO2/CO2_REF)` IMOGEN-standard. |
| 3483 | `RADF_NON_CO2` | Reads `FILE_NON_CO2_VALS` (or hardcoded HadCM3 defaults), interpolates. |
| 3618 | `QSAT` | Goff-Gratch saturation specific humidity. **Has the `PAUSE` bug.** |
| nonco2.f:13 | `FAIR_NON_CO2_GHG` | FAIR (Smith 2018) RF for CO2/CH4/N2O. |
| nonco2.f:50 | `FAIR_NON_CO2_GHG_BUDGET` | Box-model concentration update for CH4/N2O. |

#### 4.2.3 Year loop

Outer `DO WHILE (KEEPRUNNING)` loop in `PROGRAM IMOGEN`. Per iteration:
1. Wait loop polls for LPJG-side flux files + `done` (3-s sleep, see §3.4).
2. `SETTIN_LPJG` reads `imogen_lpjg.txt` → updates YEAR1, IYEND, etc.
3. Update `VARYEAR` (1..30) → `VARYEAR.dat`.
4. Inner year loop `DO IYEAR = YEAR1, IYEND`:
   - mkdir `<DIR_COMMON_OUT>/IMOGEN/output/<YYYY>/` (Windows
     `\\` separator, broken on Linux — see bug list).
   - Read scenario emissions (CO2 from `FILE_SCEN_EMITS`,
     CH4/N2O from `FILE_CH4_N2O_EMITS` if `NONCO2_EMISSIONS=T`).
   - Read LPJG flux (`<FILE_LPJG_FLUX>` and optionally
     `<FILE_LPJG_CH4_N2O_FLUX>`).
   - Delete the LPJG-side `done` file.
   - Read climatology for VARYEAR: 12 month files in
     `<DIR_CLIM>/<month><VARYEAR>`.
   - If `(ANOM AND ANLG)`: compute Q_CO2, Q_NON_CO2, optionally Q_CH4/Q_N2O
     via FAIR; sum to total Q; append to `RF_all.dat`; call `GCM_ANLG`
     for pattern-scaled monthly anomalies.
   - `CLIM_CALC` → daily/sub-daily *_OUT arrays.
   - Carbon-cycle update: apply anthropogenic emissions; if
     `LPJG_CFLUX=T` apply LPJG natural flux as `D_LAND_ATMOS`; if
     `OCEAN_FEED=T` call `OCEAN_CO2` for ocean uptake; FAIR concentration
     update if `NONCO2_EMISSIONS=T`.
   - Write `CO2.dat`, append `CO2_all.dat` (8 columns if
     `NONCO2_EMISSIONS=T`, 6 otherwise).
   - Build 365-day arrays (`*_M`) by extending Feb 28 → 31; if `REGRID=T`
     call `REGRID_CLIM`.
   - Write `T_anom.dat`, `P_anom.dat`, `SW_anom.dat`, `WET.dat`,
     `DTEMP_anom.dat`, plus optionally `Rh_anom.dat`/`W_anom.dat` for
     rel-humidity/wind.
   - Write `done` file → tells LPJ-GUESS the year is ready.
   - If `OCEAN_FEED=T`: write `fa_ocean.dat`, `dtemp_o.dat` (restart state).
5. End year loop. Continue outer `KEEPRUNNING` loop until LPJG sets it
   false in `imogen_lpjg.txt`.

#### 4.2.4 Settings (41 keys)

Full table in [SA3 §5]. The 41 keys cover:
- Path/file (10 keys): `DIR_PATT`, `DIR_CLIM`, `DIR_COMMON`,
  `FILE_SCEN_EMITS`, `FILE_NON_CO2_VALS`, `FILE_CH4_N2O_EMITS`,
  `FILE_LPJG_FLUX`, `FILE_LPJG_CH4_N2O_FLUX`, `FILE_SCEN_CO2_PPMV`,
  `FILE_GRIDLIST`.
- Integer (5 keys): `STEP_DAY`, `NYR_NON_CO2`, `NYR_EMISS`,
  `NYR_EMISS_NONCO2`, `NYR_LPJG_FLUX`.
- Float (12 keys): `T_OCEAN_INIT`, `KAPPA_O`, `F_OCEAN`, `LAMBDA_L`,
  `LAMBDA_O`, `MU`, `Q2CO2`, `TAU_DECAY_CH4`, `TAU_DECAY_N2O`,
  `CO2_INIT_PPMV`, `CH4_INIT_PPBV`, `N2O_INIT_PPBV`.
- Boolean (14 keys): `FILE_NON_CO2`, `NONCO2_EMISSIONS`,
  `NONCO2_EMISSIONS_LPJG`, `C_EMISSIONS`, `LPJG_CFLUX`, `INCLUDE_CO2`,
  `INCLUDE_NON_CO2`, `DAILYOUT`, `LAND_FEED`, `OCEAN_FEED`, `ANLG`,
  `ANOM`, `REGRID`, `CO2_RF_FAIR`.

`SETTIN_LPJG` (line 1439) reads 6 per-call keys: `YEAR1`, `IYEND`,
`YEAR1_LPJG`, `SPINUP`, `KEEPRUNNING`, `FIRSTCALL`. Anything else is
silently skipped (line 1493 — note that the default-case echo of the
offending label was added to `SETTIN` by the patch but **not** to
`SETTIN_LPJG`).

#### 4.2.5 Pattern-scaling (`GCM_ANLG`)

The implementation is a verbatim Huntingford-Cox style pattern scaling:

1. Compute total RF `Q = Q_CO2 + Q_NON_CO2 [+ Q_CH4 + Q_N2O]`.
2. On the first month of the year, call `DELTA_TEMP` to step the two-box
   land/ocean EBM 20× per year and return ΔT_L.
3. For each month, open `<DIR_PATT>/<month>` and read header
   `LONGMIN/LATMIN/LONGMAX/LATMAX`. For each of the 1631 land cells
   read 12 per-K coefficients. Multiply each by ΔT_L:

   ```
   T_ANOM_AM(L,IM) = DT_C_PAT * DTEMP_L
   PRECIP_ANOM_AM(L,IM) = (DRAINFALL_PAT + DSNOWFALL_PAT) * DTEMP_L
   SW_ANOM_AM(L,IM) = DSW_C_PAT * DTEMP_L
   ... (all 8 forcing variables)
   ```

4. After `GCM_ANLG`, sanity-check that the pattern's bbox matches the
   climatology's bbox to within 1e-6; mismatch → write `error` and STOP.

GCM selection is by `DIR_PATT` in `imogen_settings.txt`. Switching GCM
= one-line settings edit. Active default is `CEN_IPSL_MOD_IPSL-CM5A-MR/`
(IPSL CMIP5; the working paper's MRI-ESM2-0 CMIP6 ensemble would
require either generating CMIP5-style ASCII for those GCMs or
extending the reader to NetCDF). [SA3 §6]

#### 4.2.6 Bugs / smells in the Fortran

[SA3 §13]:

| # | Loc | Sev | Issue |
|---:|---|:---:|---|
| 1 | `imogen_lpjg.f:4131-4134` | 🔴 | `PAUSE` left in `QSAT` — halts on first call awaiting interactive input. Must be removed for non-interactive runs. |
| 2 | `imogen_lpjg.f:4120-4128` | 🔴 | `qsat_output.txt` opened/written per QSAT call but never closed → file-handle leak. Wasteful I/O. |
| 3 | `imogen_lpjg.f:435,461` | 🔴 | `mkdir <DIR_COMMON_OUT>/IMOGEN/output/<YYYY>` uses **Windows backslashes** (`\IMOGEN\output\<YYYY>`). Linux `mkdir` reads `\IMOGEN\…` as one weird filename. |
| 4 | `imogen_settings.txt:1-10` | 🔴 | All paths are `C:\GitHub\dbampoh\…`. Cannot run on Linux without editing. |
| 5 | `code/.vscode/settings.json` | 🟢 | Hardcoded Windows AppData path for fortls. |
| 6 | `imogen_lpjg.f` | 🟡 | Mixed `\` and `/` separators inside the same file (lines 410/421 use `/`; 435/461 use `\`). |
| 7 | `imogen_lpjg.f:268` | 🟢 | Stray malformed declaration `LONGMIN_DAT,LON  GMAX_DAT` — fixed-form Fortran ignores the embedded space. Variables never used (dead code). |
| 8 | `imogen_lpjg.f:796-800` | 🟡 | Legacy `LAND_FEED && !LPJG_CFLUX` branch sets `D_LAND_ATMOS = -CONV*0.25*C_EMISS_LOCAL` with a `WARNING: Land C uptake defaulting to 25% of emissions` print. Hardcoded placeholder. |
| 9 | `imogen_lpjg.f:909-913` | 🟡 | `F_WET_CLIM_OUT` rounding patch silently bumps wet-day count to 1 when total monthly precip ≥ 0.5 µm. Harmless but undocumented. |
| 10 | `imogen_lpjg.f:332` | 🟡 | `OPEN(98,...,CO2_all.dat,ACCESS='APPEND',STATUS='REPLACE')` — gfortran prefers `STATUS='REPLACE'` so the file is truncated at every invocation. OK in single-run mode only. |
| 11 | `imogen_lpjg.f:1493` | 🟡 | `SETTIN_LPJG`'s `CASE DEFAULT` does not echo the offending label (only `SETTIN`'s does, after the patch). |
| 12 | `imogen_lpjg.f:1498-1500` and `:591-593` | 🟢 | Duplicate `done`-file deletion — one in `SETTIN_LPJG`, one in the year loop. |
| 13 | `gridlist_global.txt` (13 rows) | 🟡 | `REGRID_CLIM` would crash because `NGPOINTS=3698` but the file has only 13 lines; `IF(IOS.NE.0) CONTINUE` (1161) is a no-op so the read silently produces garbage in `LON_OUT(14..3698)`. |
| 14 | `imogen_lpjg.f:751,772; nonco2.f:107,127` | 🟡 | Multiple TODO comments `IYEAR vs IYEAR-1?` flagging year-indexing ambiguity for LPJG-flux year matching. Affects C-budget closure. |
| 15 | `imogen_lpjg.f:88` | 🟡 | `NFARRAY=10000` PARAMETER caps single-segment runs to ~500 yr at `NCALLYR=20`. Runtime check at line 3332 only `PRINT`s a warning, doesn't abort. |
| 16 | `imogen_lpjg.f:290` | 🟡 | `NGPOINTS=3698` PARAMETER hard-caps user-facing gridlist size. Recompile to change. Stack memory ~410 MB at this size. |

The `Original Imogen Modified for LPJG Coupling/imogen_lpjg.f` file
(2.6 MB, near-identical) is a **backup** that pre-dates the current
working version. Substantive differences [SA3 §11]:
- `NGPOINTS = 3711` (vs current 3698).
- `done` polling was disabled in the backup (`C` prefixed `INQUIRE` +
  forced `DONE_EXIST=.TRUE.`); current version restores it.
- `mkdir` was originally Windows + a commented Linux variant — now
  only Windows remains.
- `patch_add_ch4_n2o_conc.diff` is folded into current.
- Current version added the `qsat_output.txt` debug dump + the `PAUSE`.
- `INVERT` matrix-check `STOP` was originally commented out
  (`!STOP`); now re-enabled.

The patch should be **archived** once the current `imogen_lpjg.f` is
known-good.

### 4.3 IMOGEN C++ refactor (`IMOGENCXX`)

**Path:** `IMOGENCXX/ImogenCXX/`
**Detailed report:** `_phase2_findings/04_imogen_cxx.md` (41 KB)

#### 4.3.1 Surface

A single 2 631-LOC `Main.cpp` and a single 41-line `imogen_settings.txt`.
**No headers, no module split, no build system** (no CMakeLists, no
Makefile, no `.vcxproj` other than an unused `.vscode/`). All 19
Fortran subroutines plus the 2 from `nonco2.f` are folded as C-style
free functions in one TU. The settings file is byte-for-byte the same
key set as the Fortran reference — 41 keys, no additions, no removals.
[SA4 §1, §2, §4]

#### 4.3.2 Faithfulness assessment

Per [SA4 §3, §9]:

| Status | Functions |
|---|---|
| **Faithful** to Fortran | `RADF_CO2`, `RADF_NON_CO2`, `RESPONSE`, `INVERT`, `DELTA_TEMP`, `GCM_ANLG`, `RNDM`, `SOLANG`, `QSAT` (modulo `system("pause")`), `REGRID_CLIM`, `FAIR_NON_CO2_GHG`, `FAIR_NON_CO2_GHG_BUDGET`, settings keyset, output filenames |
| **Stub or wrong** | `DAY_CALC` (empty — Fortran's 462-line core), `SOLPOS` (1-line placeholder), `DTEMP_OUT` output (assignment commented), `done`-file polarity (creates instead of deletes), `KEEPRUNNING` loop (assignment, not comparison → infinite loop), spin-up vector init (`push_back` instead of zero), `OCEAN_CO2` indexing (off-by-one), `fa_ocean.dat`/`dtemp_o.dat` open only on `IYEAR==YEAR1`, output formatting widths differ from Fortran, `WET.dat` integer cast lost (printed as float), Windows-only system calls (`localtime_s`, `system("pause")`, `\\` in clim path) |

#### 4.3.3 The "larger gridlists" claim — clarified

**Earlier framing (in the master doc's first draft) said the
C++ refactor's gridlist benefit was "mostly false" because both
versions hardcode `NGPOINTS=3698` as a compile-time constant. That
framing was technically true but practically misleading; this
sub-section corrects it.**

The actual gridlist limitation has two components, internal and
external:

- **Internal IMOGEN climatology grid: `GPOINTS=1631`.** This is a hard
  cap in *both* Fortran and C++ that is tied to the underlying CMIP5
  ASCII pattern files and CRUNCEP base-climatology files (each sized
  for exactly 1631 HadCM3 land cells excl. Antarctica). Changing this
  requires regenerating those files, not just editing a constant. In
  practice no one needs to change it.

- **Output user-facing gridlist: `NGPOINTS=3698`.** This is the limit
  that matters for actual coupled runs and is the limit the user
  experienced in practice. The Fortran caps it via
  `PARAMETER NGPOINTS=3698` at `imogen_lpjg.f:290`; the C++ caps it via
  `const int NGPOINTS = 3698;` at `Main.cpp:39-40`.

The crucial difference is not in the constant but in the **memory
allocation strategy**:

- **Fortran:** `REAL T_OUT_M_REGRID(NGPOINTS, 12, 32, NSDMAX)` is a
  *statically declared array*. The compiler reserves space at link
  time in BSS (the uninitialised data segment) or, for arrays in
  inner subroutines, on the stack. At `NGPOINTS=3698`, NSDMAX=24,
  one `_REGRID` array is `3698 × 12 × 32 × 24 × 8 ≈ 273 MB`; four such
  arrays in `REGRID_CLIM` total `~1.1 GB`. At `NGPOINTS=62000`, those
  same four arrays would total `~14 GB` — which exceeds default Linux
  BSS reservations and can fail at link, at startup, or on first
  reference (segfault). Workarounds (`ulimit -s unlimited`,
  `-mcmodel=large`, hand-conversion of arrays to `ALLOCATABLE`) all
  require either user-environment changes that managed HPC clusters
  often disallow or refactoring the Fortran source.

- **C++:** `std::vector<std::vector<...>>` arrays are
  *heap-allocated at runtime*. At `NGPOINTS=62000`, the same 14 GB
  allocation succeeds on any 64-bit system with sufficient physical
  RAM (~32 GB workstation or larger cluster node). No link-time or
  startup-time blow-up.

So in the C++, **recompiling with `const int NGPOINTS = 62000;` and
running on a workstation with ≥32 GB RAM works**, while the Fortran
with the same recompile would die at startup. This is exactly the
practical difference the user observed.

#### 4.3.3a Implication for the unified codebase

The right fix is *not* to keep the C++ refactor (which has 25
unrelated bugs including an empty `DAY_CALC`). The right fix is to
**convert the Fortran's static arrays in `imogen_lpjg.f` and
`nonco2.f` to `ALLOCATABLE`** with `ALLOCATE` calls keyed off the
gridlist file length. Modern gfortran (≥4.6) supports this fully.
Effort: ~1-2 days of careful Fortran refactoring of the ~30
statically-declared array variables that scale with `NGPOINTS` and
`GPOINTS`. Outcome: the working Fortran physics (which the C++ is
missing pieces of) plus the heap-allocation scalability the C++ is
prized for. See §12.4 for the revised IMOGEN-implementation roadmap.

The C++ refactor remains valuable as an **eventual second
implementation** for cross-validation against the Fortran (the user's
suggestion: bring up the Fortran-with-ALLOCATABLE first, then later
fix the C++ using the Fortran outputs as a numerical-parity reference).
See §12.4 for the phased plan.

#### 4.3.4 25 catalogued bugs

[SA4 §10] catalogues 25 distinct bugs/oddities (B1-B25). The most
important:
- B1: Hardcoded settings path (`Main.cpp:525`) `C:\GitHub\dbampoh\…`
- B4: `DAY_CALC` body empty (`Main.cpp:1149-1162`)
- B5: `SOLPOS` placeholder
- B6: `DTEMP_OUT` assignment commented out (`Main.cpp:1293`)
- B7: `} while (KEEPRUNNING = true);` (`Main.cpp:2626`) — assignment
- B8: `SETTING_LPJG` creates `done` instead of deleting (lines 784-792)
- B9: spin-up `push_back` corrupts `FA_OCEAN`/`DTEMP_O`/`SEED_RAIN`
- B10: wrong flag passed to `FAIR_NON_CO2_GHG_BUDGET`
- B12: `ofstream` reopened only on `IYEAR == YEAR1` for per-year
  appends
- B14: `WET.dat` written through `<< fixed << setprecision(3)` (float
  format) instead of `i10`
- B16: duplicate first entry in `ES[]` saturation-vapour-pressure table
  → table off by one vs Fortran

The Imogen-controller `.cpp` variants ship companion bugs (B20-B22):
- B20: hardcoded `"C:\\GitHub\\LPJ_IMOGEN_coupling\\Common_Directory\\…"`
  override on one branch.
- B21: writes `TRUE`/`FALSE` (no dots) into `imogen_lpjg.txt` —
  breaks Fortran `READ` namelist parsing.
- B22: Makefile builds `Imogen-controller-cxx.cpp` (Windows-only)
  even when `detected_OS != Windows`.

#### 4.3.4a Climate output asymmetry between Fortran and C++ — Rh and W are C++-only

A new finding (5 May 2026): the C++ refactor produces **two output
files that the Fortran does not**, namely `Rh_anom.dat` (relative
humidity) and `W_anom.dat` (wind speed). Verified at:

```cpp
// climatemodel.cpp:875-876 — file open
file96.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/Rh_anom.dat");
file97.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/W_anom.dat");

// climatemodel.cpp:903-904 — sub-daily writes (when DAILYOUT=true)
file97 << ... windOutM[igp][imm][imd][ind] << " ";   //DKB Wind
file96 << ... rhOutM[igp][imm][imd][ind]   << " ";   //DKB Rh

// climatemodel.cpp:915-916 — monthly writes (when DAILYOUT=false)
file97 << ... windOutM[igp][imm][0][0] ...           //DKB
file96 << ... rhOutM[igp][imm][0][0]   ...           //DKB
```

The `//DKB` comment annotations confirm these are user-added in the
C++ refactor. A `grep "Rh_anom\|W_anom"` in `imogen_lpjg.f` returns
**zero matches** — the Fortran writer block at lines 925-1038 only
produces T_anom.dat, P_anom.dat, SW_anom.dat, WET.dat, DTEMP_anom.dat,
plus CO2.dat / fa_ocean.dat / dtemp_o.dat.

Updated full output comparison:

| File | Variable | Fortran | C++ |
|---|---|:---:|:---:|
| `T_anom.dat` | Mean 2 m temperature | ✓ | ✓ |
| `P_anom.dat` | Total precipitation | ✓ | ✓ |
| `SW_anom.dat` | Downward shortwave radiation | ✓ | ✓ |
| `WET.dat` | Wet-day count per month | ✓ | ✓ |
| `DTEMP_anom.dat` | Diurnal temperature range | ✓ | ✓ |
| `Rh_anom.dat` | Relative humidity | **✗** | **✓** |
| `W_anom.dat` | Wind speed | **✗** | **✓** |
| `Tmin_anom.dat` | Daily minimum temperature | ✗ | ✗ |
| `Tmax_anom.dat` | Daily maximum temperature | ✗ | ✗ |
| `CO2.dat` | Annual CO2/CH4/N2O concentrations | ✓ | ✓ |
| `fa_ocean.dat` | Cumulative ocean-atmosphere C flux history | ✓ | ✓ |
| `dtemp_o.dat` | Per-layer ocean temperature anomaly | ✓ | ✓ |
| `done` | Marker file | ✓ | ✓ |

Implications for the rebuild:

1. **The Phase-1 Fortran-with-`ALLOCATABLE` refactor (§II.2 of the
   execution plan) gains a small additional task**: port the C++
   `Rh_anom` + `W_anom` writers back into Fortran so the two
   backends produce parity output.
2. **`param "file_relhum"` and `param "file_wind"` in the ins file
   were not as dead as the audit initially suggested** — they were
   prepared for consumption from C++-produced Rh/W files. The
   producer side IS wired (in C++); the LPJG-side consumer (in
   `imogencfx::get_climate_for_gridcell`) is not. Wiring the
   consumer is ~30 LOC of `imogencfx.cpp` work (declare member
   arrays, read the params, populate the day arrays, set
   `climate.relhum` and `climate.u10`).
3. **Tmin/Tmax outputs** are achievable with ~3 hours of work
   (compute `Tmin = T - DTEMP/2` and `Tmax = T + DTEMP/2` in IMOGEN's
   writer block; add file_tmin/file_tmax ins-file params and reader
   in `imogencfx`; set `climate.tmin` / `climate.tmax`). Currently
   LPJ-GUESS computes these internally from DTEMP, so adding them
   as separate inputs is a diagnostic / verification enhancement
   rather than a new capability — but it would let the user verify
   Tmin/Tmax are numerically self-consistent. Captured as step 9.5
   of the V.1 rebuild plan.

**Critical units note:** if Rh/W writers are added to the Fortran,
the units must match the C++ outputs and what `cfxinput` expects
when consuming `param "file_relhum"`/`param "file_wind"` (the
non-IMOGEN reader at `cfxinput.cpp:1941-1942`). C++ `rhOutM` units
are not explicitly declared in the engine — likely % or fraction
(0..100 or 0..1); needs verification. Wind in m/s (`climate.u10` is
"10 m wind speed in m/s" by LPJ-GUESS convention). Per the I.D
units integrity discipline of the execution plan, every cross-
component data path needs a documented unit.

#### 4.3.5 Recommendation (revised)

The framework should adopt a **two-implementation strategy** with
phased delivery:

**Phase 1 (canonical, primary): Fortran-with-ALLOCATABLE.**
Bring the Fortran `imogen_lpjg.f` + `nonco2.f` into the unified
codebase with the small known fixes (PAUSE removal, mkdir slashes,
Windows path scrubbing) and one substantive enhancement: convert the
~30 statically-declared arrays that scale with `NGPOINTS` or
`GPOINTS` into `ALLOCATABLE` arrays with `ALLOCATE` calls keyed off
the gridlist file length. Modern gfortran (≥4.6) supports this fully.
Outcome: working Fortran IMOGEN that scales to 62k+ user gridlists
(the limit then becomes physical RAM, not the linker). Effort ~1-2
days refactoring + ~1 day validation.

**Phase 2 (secondary, follow-on): C++ refactor brought to parity.**
Fix the 25 catalogued bugs in `IMOGENCXX/ImogenCXX/src/Main.cpp`
(empty `DAY_CALC`, infinite year loop, polarity-inverted `done`,
hardcoded Windows settings path, `system("pause")`, ES table
off-by-one, etc.). Port `DAY_CALC` (462 lines) and `SOLPOS` (60
lines) from the Fortran. Numerical-parity test: per-gridcell,
per-year, C++ outputs must match the Fortran-with-ALLOCATABLE
outputs to within `EPSILON`. Effort ~1-3 weeks porting + parity
testing.

**Both implementations available, switchable.** Once both are
working, the unified codebase exposes them as alternative IMOGEN
backends (e.g. via a `imogen_backend "fortran"` or
`imogen_backend "cxx"` ins parameter, or two separate binaries that
LPJ-GUESS can invoke). Cross-validation between them serves as
ongoing QC.

This honours the user's stated preference: get the
Fortran-with-ALLOCATABLE working first (lower risk, working
physics), then bring the C++ to parity using the Fortran as the QC
reference. The C++ refactor is **not** archived as previously
suggested — it is preserved and brought to parity in Phase 2.

### 4.4 Imogen-controller

**Path:** `Imogen-controller/`
**Detailed report:** `_phase2_findings/04_imogen_cxx.md §7` (within SA4)

#### 4.4.1 Files

```
Imogen-controller/
├── Imogen-controller.cpp        # Windows-only original
├── Imogen-controller-cxx.cpp    # Windows-only variant
├── Imogen-controller-cross.cpp  # cross-platform via #ifdef _WIN32
├── Makefile                     # builds Imogen-controller-cxx.cpp (the wrong one)
├── README.txt                   # describes role
└── config.txt                   # placeholder ("Future implementation of a config file")
```

#### 4.4.2 Role

Per the README [SA1 §2.10]:
> *"`automate_imogen.exe` monitors/creates the `done` marker file at 2 s
> intervals; supports `automate_imogen.exe reset` (delete created folders,
> reset settings) and `automate_imogen.exe move RCP60` (move outputs into
> named folder)."*

The intended use case was a 2-process design where the controller
drives a separate IMOGEN binary by writing `imogen_lpjg.txt` and the
`done` file year-by-year while a separate IMOGEN process reads them.

#### 4.4.3 Currently dead

Per §3.2 and §3.4(C) above: not invoked from any shipped script;
polling path uses Windows separator and wrong subdirectory; LPJ-GUESS
in tight mode invokes IMOGEN in-process so the controller has no role.

**Recommendation:** retire entirely. The Makefile, the three .cpp
variants, the README, and the placeholder config.txt all go to
`archive/imogen_controller/`.

### 4.5 C++ Intermediary (`Intermediary/Code`)

**Path:** `Intermediary/Code/`
**Detailed report:** `_phase2_findings/05_intermediary_cpp.md` (55 KB)

#### 4.5.1 Surface

13 headers, 12 cpp files (A) / 13 cpp files (B; adds `Logger.h/.cpp`):

```
Intermediary/Code/
├── Makefile                    # GNU make, GCC/g++ -std=c++17, OS detection
├── config.txt                  # runtime config; Windows-style paths
├── include/                    # 13 headers
│   ├── Adder.h, Calculator.h, DualStreamBuffer.h, Extractor.h,
│   ├── FileManager.h, Logger.h (B), Maps.h (944/1493 lines!),
│   ├── MethaneEmissions.h, NitrogenEmissions.h, Parameters.h,
│   ├── PlumDataProcessor.h, Templates.h, UtilityHandler.h, Wetlands.h
└── src/                        # 12 / 13 cpp files
    └── (mirrors include/)
```

Total LOC: 4 052 (A) / 5 891 (B). [SA5 §1]

**Verified additionally:** version A builds cleanly on Linux to
`bin/ipcc` (882 KB). All 12 .cpp files compile with no warnings or
errors. [follow-up build experiment]

#### 4.5.2 Class roles

| Class | Header / Source | Purpose |
|---|---|---|
| `Templates` (POD structs) | `Templates.h` | dataHolder1/dataHolder2 (2-/3-col), readcflux, readMethane, readNitrogen, readWetlands, readRiceMethane, readPLUMLandUSe, PLUMFileDataStruct |
| `Parameters` (globals) | `Parameters.h/cpp` | config map, year window, output filenames, scenario, ssps[], rcps[] |
| `UtilityHandler` | `UtilityHandler.h/cpp` | `readConfig`, `split`, `trim`, `replacePlaceholders`, `replaceSubstring`, `replaceAll` |
| `FileManager` | `FileManager.h/cpp` | `openFile`, `closeFile`, `loadFile2/3` (2-/3-col read), `printToFile` (5-decimal fixed), `printToConsole` |
| `DualStreamBuffer` | `DualStreamBuffer.h` | streambuf subclass that tees stdout to logfile |
| `Maps` | `Maps.h/cpp` | **All hardcoded IPCC tables** (Tables 10.10/10.11/10.13a/10.19/10.21/10.22/10A.5/10A.9 livestock, 3A.2 wetlands; A: 944 lines; B: 1 493 lines with country expansion) |
| `Calculator` | `Calculator.h/cpp` | The 5 tier-1 formulae (see §4.5.3) |
| `MethaneEmissions` | `MethaneEmissions.h/cpp` | Workhorse: PLUM 2010-2100 scenario CH4 + OWI/FAO 1961-2009 historic |
| `NitrogenEmissions` | `NitrogenEmissions.h/cpp` | Same shape for N2O |
| `PlumDataProcessor` | `PlumDataProcessor.h/cpp` | Pre-processes PLUM `*_LandUse*` into per-year fertiliser totals |
| `Wetlands` | `Wetlands.h/cpp` | GLWD3 area + Tier 1 → CH4 (broadcast to constant time series) |
| `Extractor` | `Extractor.h/cpp` | Reads gridded LPJG cflux/mch4/ngases.out, aggregates global per year |
| `Adder` | `Adder.h/cpp` | **The merge step.** Combines IIASA + LPJG + IPCC into the per-year IMOGEN-bound product. **Currently called nowhere.** |

A header-naming bug: `Adder.h` declares `class MethaneEmissions` and
`MethaneEmissions.h` declares `class Adder` — both in A and B. 🟢

#### 4.5.3 IPCC Tier-1 formulae implemented

| Calculator method | IPCC equation | Status |
|---|---|---|
| `calcCH4EntericFermentation(country, animal, nHeads)` | V4 Ch10 Eq 10.19 | ✅ correct |
| `calcCH4ManureManagement(country, animal, nHeads)` | V4 Ch10 Eq 10.22 | ✅ correct |
| `calcVolalileSolidExcretion(rate, mass)` | V4 Ch10 Eq 10.22a | ✅ correct |
| `calcN20ManureManagement(nHeads, country, animal)` | V4 Ch10 Eq 10.25 (direct only) | ⚙️ partial — indirect (Eq 10.26-10.29) NOT modelled |
| `calcN2OManagedSoils(FSN_FON, EF1=0.01, …)` | V4 Ch11 Eq 11.1 (N-inputs first sub-term only) | ⚙️ partial — flooded-rice EF1FR, organic-soils F_OS·EF2, grazing F_PRP·EF3 NOT used |
| `calcNitrogenExcretion(rate, mass)` | aux for Eq 10.25 | A: **🔴 wrong** (`rate*mass*1000/365`); B: ✅ correct (`(rate/1000)*mass*365`) |
| `calcCH4Wetlands(diff_EF, area, ice_free=250)` | Wetlands Suppl. Ap3 Eq 3A.1 | ✅ correct (Tier 1 only, no bubble Eq 3A.2 or DOC pathway) |

**Not covered in C++:**
- No CO2 estimation. CO2 in IMOGEN-bound output comes from IIASA (1850-1960)
  + LPJG cflux NEE (1961-2100). LPJG handles cropland C dynamics.
- No indirect N2O (Eq 10.26-10.29). `MAP_FRACGAS` is loaded into
  Maps.h but `getFRACGAS` is never called.
- No EF4/EF5.

[SA5 §7]

#### 4.5.4 The merge step (`Adder::startAddition`)

[SA5 §9] reproduced essentially the algebra from §2.3 above. The merge
loop applies three regimes by year:
1. Pre-LPJG (1850 ≤ y < where_full_iiasa_covers_backwards):
   `IIASA_non_lpjg + IIASA_lpjg`.
2. Historic (1961 ≤ y < 2010 in CMIP5; 1990 ≤ y < 2010 in CMIP6):
   `IIASA_non_lpjg + Historic_(IPCC-OWI-FAO) + LPJG_natural`.
3. Scenario (2010 ≤ y ≤ 2100):
   `IIASA_non_lpjg + IPCCMethane(PLUM) + LPJG_natural`.

The smoothing block at lines 114-164 (centered moving average) is
commented out; `centeredMovingAverage` is defined but never invoked.

**The merge step is currently dead.** `src/Main.cpp` lines 199-237 in
A (where Extractor → Wetlands → vector extraction → `Adder::startAddition`
→ `printToFile` is invoked) are commented out. In B, the methane block
is *also* commented out, leaving only the N2O scenario calculation.

The pre-existing reference outputs in `Data/Intermediary/Emissions/`
(`total_methane_nitrogen_rcp26ssp1.txt`, `…rcp85ssp5.txt`) demonstrate
the Adder produced sensible results when uncommented in an earlier
build.

#### 4.5.5 Bugs

[SA5 §11]:

| # | Loc | Sev | Issue |
|---:|---|:---:|---|
| 1 | A `Calculator.cpp:73-76` | 🔴 | `calcNitrogenExcretion` formula wrong by factor of 10⁶ per animal (offset by `1e-9 Kg→Tg` final convert; relative error baked in). All A-produced N2O reference outputs are wrong. B fixes. |
| 2 | A `NitrogenEmissions.cpp` | 🔴 | `getline(ss, temp, ',')` instead of `getline(ss, fertvalue_kg_per_ha_arable_land, ',')` for `n2ofertilizer.csv` reading → `atof("")=0`, historic fertiliser N2O always 0. B fixes. |
| 3 | A `Adder.cpp:239` | 🔴 | `int vecSize = lastyear = firstyear + 1;` — assignment-to-global! Currently dead code. |
| 4 | A/B | 🟡 | `MethaneEmissions::startCalculation_methane_modelled_historic_1961_2009` resize/window is `49`/`<2010` in A, `59`/`<2020` in B but variable still called `_1961_2009`. |
| 5 | B `MethaneEmissions.cpp:47-48` | 🟡 | 13-element `FAO_items` array iterated only `i<10`; reordering breaks species mapping. Currently dead (call commented). |
| 6 | B `MethaneEmissions.cpp:56-63` | 🔴 | The `getline(ss, temp, ',')` for the `Code` column is **commented out**, so `stoi(country_code)` throws on the next line. Currently dead (call commented). |
| 7 | A/B | 🟡 | Magic offset `160` in `Adder::startAddition` lines 103/105/107/109 hardcodes `firstyear=1850`. |
| 8 | A/B | 🟡 | `Extractor::startLPJGDataExtraction` hardcodes `cdtarea(lat,lon,1.25,1.25)` but LPJG default is 0.5° → area off by ~6.25× per cell. |
| 9 | A/B `config.txt:1` | 🔴 | `baseDirectory=C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\` — every run requires editing. (Linux runtime path-separator translation handles backslash/slash but not the root.) |
| 10 | A `Calculator.cpp:17-18` | 🟢 | `loadCountries()` Windows path. Dead code. |
| 11 | A/B Adder/Wetlands/Extractor | 🟡 | All commented out in `Main.cpp` of both versions → merge step disabled. |

#### 4.5.6 A vs B differences

[SA5 §10]:
- **B-added:** `Logger.h/cpp` (singleton with timestamps and levels);
  6 new diagnostic CSV outputs (rice, historic enteric / manure /
  fertiliser, scenario manure, scenario fertiliser); rice cultivation
  toggle defaulted to `true` (vs `false` in A); CMIP6 wetlands path
  fixed.
- **B-fixed bugs:** `calcNitrogenExcretion`, fertiliser CSV read,
  `wetlandsMethaneEmissionsOutputPathwetlandsAreaFilePath` typo.
- **B-introduced bugs:** 13-element FAO_items reordering, `Code`-column
  getline commented out (both currently dead — call sites commented).
- **B-deviations:** Methane block also commented in `Main.cpp` (only
  N2O runs); historic windows expanded to `<2020` but variables still
  named `_1961_2009`; Wetlands CSV format reordered (`year,country,
  value` vs A's `country,variable,year,measure,value`); year-broadcast
  shortened to 1961-2020 (vs 1961-2100 in A).

**Net:** B is a *safety-and-instrumentation pass* with bugfix +
defensive map lookups + universal logging. Functionally the same active
code path as A (PLUM scenario CH4 + N2O), but B narrows it further.
Neither A nor B actually runs the merge to IMOGEN-ready output.

### 4.6 Python Intermediary (`Intermediary_py`)

**Path:** `Intermediary_py/`
**Detailed report:** `_phase2_findings/06_intermediary_py.md` (56 KB)

#### 4.6.1 Surface

5.3 GB total, dominated by populated `inputs/` (5.1 GB FAO+PLUM+RCMIP+
EDGAR+LPJG data) and `outputs/` (66 MB CSVs+plots). Source code is
much smaller — ~14 k LOC across `src/component_a_anthropogenic/`,
`src/component_b_natural/`, `src/component_c_integration/`,
`src/component_d_imogen_export/`, plus `src/shared/`. [SA6 §2]

```
Intermediary_py/
├── README.md (25 KB)           # user-facing entry
├── HANDOFF.md (92 KB)          # chronological technical record (R1..R16)
├── TECHNICAL_MANUAL.md (111 KB) # 18-section reference manual
├── Quick_Start.md (7.6 KB)     # Ubuntu workstation runbook
├── inputs_README.md (6.8 KB)   # input acquisition table
├── imogen_ghg_controller_FULL.tar.gz       (105 MB)
├── imogen_ghg_controller_SOURCE_ONLY.tar.gz (6.5 MB)
├── imogen_ghg_controller_FULL/imogen_ghg_controller/  (5.2 GB extracted)
└── imogen_ghg_controller_SOURCE_ONLY/imogen_ghg_controller/ (7.9 MB extracted)
```

The codebase is **physically triplicated** at three sibling paths
(top-level `Intermediary_py/`, `…_FULL/imogen_ghg_controller/`,
`…_SOURCE_ONLY/imogen_ghg_controller/`); all source content is
byte-identical. Only top-level should be retained in the unified codebase.

#### 4.6.2 Pipeline architecture (4 components A/B/C/D)

[SA6 §1.1, §3.1]:

| Component | Role | LOC | Outputs |
|---|---|---:|---|
| A. Anthropogenic | IPCC tier-1 emissions × FAO/EDGAR/PLUM activity data; substitution into RCMIP | 8 682 (28 .py) | `outputs/component_a/data/*.csv` (~37 CSVs); `rcmip_substitution_{ch4,n2o}.csv` are the integration-products |
| B. Natural | LPJ-GUESS streaming aggregation (.gz files) + GMB IFW/DCC corrections | 1 791 (5 .py) | `outputs/component_b/data/lpjg_{co2,ch4,n2o}_annual{,_scenarios}.csv` |
| C. Integration | Sums anthro + natural; 3 independent comparators | 2 848 (9 .py) | `integrated_emissions_{ch4,n2o,co2}.csv`; comparators |
| D. IMOGEN export | Reshape to per-scenario wide + combined long | 176 | 5 wide + 1 long CSV in `outputs/imogen_inputs/` |

The driver `run_all.py` is 211 lines, hardcoding 43 ordered steps as
`(script_path, kind, label)` tuples (28 + 5 + 9 + 1). Each step is
executed via `subprocess.run(['python3', str(script_path)])`. No
parallelism. Estimated runtimes: A 10-15 min, B 10-15 min (× 5
scenarios = 50 min for B step 3), C ~1 min, D ~2 s. **Livestock
anchor needs 6-8 GB RAM.**

#### 4.6.3 Final output schema (the IMOGEN-bound product)

5 per-scenario wide CSVs + 1 long combined, in `outputs/imogen_inputs/`.

Per-scenario wide schema (verified against on-disk SSP2-4.5):
```
Year, CH4_anthro_Mt, CH4_natural_Mt, CH4_total_Mt,
      N2O_anthro_Mt, N2O_natural_Mt, N2O_total_Mt,
      CO2_EFOS_Mt, CO2_NEE_Mt, CO2_total_Mt
1900,87.613300,175.952299,263.565599,1.356163,11.103581,12.459744,
     1788.820939,-4143.864232,-2355.043294
...
```

Long schema:
`Year, Scenario, Gas, Anthro_Mt, Natural_Mt, Total_Mt, Unit`
where `Unit ∈ {"Mt CH4/yr","Mt N2O/yr","Mt CO2/yr"}`.

**Units note:** all values in Mt-of-gas/yr (10⁹ kg). For CO2 this is
Mt CO2, **not** Mt C — multiply by 12/44 to convert to Mt C, or divide
`CO2_total_Mt` by 3666.67 for Pg C/yr.

201 rows per scenario CSV (1900-2100 inclusive). Asserted in
`imogen_inputs_export.py` lines 95-97; any future change to the time
axis requires a code edit.

#### 4.6.4 Tests

3 pytest files. All pass per HANDOFF §16:

- `test_unit_conversions.py` — 5 assertions on PgC↔MtCO2 and TgN↔TgN2O.
- `test_co2_option_a_validation.py` — verifies SSP2-4.5 mean 2014-2020
  integrated CO2 atmospheric source falls within ±1σ of GCB 2025
  partition (`|our − 7.6 PgC/yr| < 1.24 PgC/yr`). The headline
  scientific test.
- `test_imogen_export_schema.py` — verifies all 5 per-scenario CSVs +
  combined long-format exist, shapes (201, 10) and (3015, 7), expected
  column order, no NaNs, `Year=1900..2100`.

Reproducibility-tested: 39/40 reference CSVs and 13/14 reference plots
byte-identical against earlier runs (the diff CSV is a pandas
float-formatting cosmetic; the diff plot is a deliberate budget-refs
upgrade).

**Honest test-coverage gaps** (TECH §13.3, §15.8):
- No per-sector regression tests for Component A (28 scripts!).
- No shape/value tests for Component B (the LPJ-GUESS streaming
  aggregation).
- No comparator-construction tests.
- Plotting scripts not numerically tested.
- LPJ-GUESS .gz files are gigabytes → CI/CD impractical without
  synthetic fixtures (TECH §15.9 proposes `IMOGEN_GHG_TEST_MODE` env
  var; not implemented).

#### 4.6.5 Bugs / gaps

[SA6 §13]:

**Resolved per HANDOFF Round 15-16:**
- 89 scripts/files affected by hardcoded paths
  (`/mnt/user-data/uploads/`, `/tmp/...`,
  `/home/claude/Emissions_Modeling_Project_Directory/...`); all routed
  through `src/shared/paths.py`.
- 11 broken f-strings.
- 7 Component-C scripts missing `paths.py` import.
- Scenario directory inconsistency.

**Open per TECHNICAL_MANUAL §15:**
- 15.2: Tier-1 only (no Tier-2/3) → ~30-40 % per-sector uncertainty.
- 15.3: No uncertainty propagation through the integrated trajectory.
- 15.4: GMB IFW (+112) and DCC (−23) are **constants** with no
  temperature dependence.
- 15.5: Possible N2O double-counting between LPJ-GUESS soil and IPCC
  Tier-1 indirect (~5-8 %).
- 15.6: Inconsistent matplotlib backend handling.
- 15.7: Missing `if __name__ == '__main__'` guards in some scripts.
- 15.8: Tests don't exercise A and B end-to-end.
- 15.9: No CI fixtures for the gigabyte-scale LPJ-GUESS .gz inputs.
- 15.10: No formal data versioning (no `inputs/manifest.json`).

**Additional gaps surfaced by SA6:**
- **Missing `openpyxl` in requirements.** EDGAR scripts read xlsx via
  pandas, which silently requires openpyxl. Neither
  `pyproject.toml.dependencies` nor `requirements.txt` lists it.
  Fresh installs will fail at first EDGAR-using script with
  `ImportError: Missing optional dependency 'openpyxl'`. 🔴
- `from src.shared …` imports while pyproject declares `src` as a
  package literally named `src` — TECH §16.5 flags as future cleanup.
- Quick_Start lines 1-15 contain an out-of-place chat-conversation
  excerpt about reproducibility verification — should be deleted in
  the unified codebase.
- 5 SSP scenarios produced (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP4-6.0,
  SSP5-8.5) vs the working paper's 2-scenario evaluation focus
  (SSP1+SSP2). Capability vs evaluation — not a contradiction but
  worth documenting.

#### 4.6.6 Substitution roadmap (C++ Intermediary → Python Intermediary)

[SA6 §11]:

The Python pipeline is a **standalone** non-iterative single-shot batch.
It does not currently slot into the same loop position the C++ binary
occupies. Concrete integration steps:

1. **Establish IMOGEN's actual input-file spec.** *(BLOCKING.)*
   Quick_Start.md explicitly defers to a follow-up:
   *"please share the IMOGEN code so I can determine the input data
   form/structure/format requirements and figure out how the 6
   IMOGEN-input CSVs we produce should be transformed for ingestion
   into IMOGEN."*
   The current Python output schema (10-column wide CSV per scenario)
   is the author's plausible guess at what IMOGEN wants — not a
   verified contract. **Fortran IMOGEN actually consumes per-year
   `<DIR_COMMON>/LPJG_main/IMOGEN/<FILE_LPJG_FLUX>` as a 2-column
   `year value` text file** (§4.2 above). The 10-column wide CSV is
   *not* in the Fortran reader's recognised format. An adapter is
   required.

2. **Map each Component-D output column to an IMOGEN-controller input
   field.** The Fortran `imogen_lpjg.f` reads:
   - `FILE_LPJG_FLUX`: 2-col `year flux` for CO2 (TgC/yr).
   - `FILE_LPJG_CH4_N2O_FLUX`: 3-col `year ch4 n2o` (Tg/yr).
   - `FILE_SCEN_EMITS`: 2-col CO2 emissions time series.
   - `FILE_NON_CO2_VALS`: 2-col non-CO2 RF time series.
   - `FILE_CH4_N2O_EMITS`: 3-col `year ch4 n2o` anthropogenic
     emissions for FAIR.
   So Component D's wide CSV must be split / reshaped into these
   four file types. **A simple Python adapter script
   (`imogen_inputs_to_lpjg_format.py`) is the minimum-disruption path.**

3. **Decide the substitution mode.** The Python pipeline runs once
   up-front. The framework's intended use is per-iteration. Options:
   (a) drop-in CSV producer (run pipeline once, place outputs at
   IMOGEN's expected paths) — simpler, recommended; (b) per-iteration
   callable (refactor `imogen_inputs_export.py` into a function with
   in-memory args) — more work.

4. **Add a CLI entry point.** TECH §16.5 lists this as future work.
   Currently the only CLI is `python run_all.py --component …`.
   Wrap with `imogen-ghg run --output-dir ... --scenarios SSP2-4.5`.

5. **Reconcile the input-data sources.** The Python pipeline expects
   PLUMv2 outputs at `inputs/plum/plum_crop_s1.csv` and
   `inputs/plum/Livestock_counts.txt`. The framework's PLUM outputs
   live at `Data/Intermediary/PLUM_data/animals_ssp{1..5}.txt` and
   `Data/Intermediary/PLUM_data/{plum_land_use,agg_land_use}/`. The
   schemas differ (the Python pipeline expects extracted text from a
   270-MB ZIP). Either convert framework PLUM outputs into the layout
   the Python pipeline expects, or rewrite the Python pipeline's
   PLUM ingestion to read the framework's actual format.

6. **Resolve the LPJ-GUESS .gz file location.** Python pipeline expects
   `inputs/lpjg/historical/lpjg_<var>.out_historical.gz` and
   `inputs/lpjg/scenarios/<ssp>/lpjg_<var>.out_<tag>.gz`. Framework's
   LPJ-GUESS coupled outputs land elsewhere. Either symlink or rewire
   `paths.py` constants `LPJG_HIST_DIR` / `LPJG_SCEN_DIR`.

7. **Replace `run_all.py` with the framework's orchestrator.**
   Internal driver replaced with the framework's coupled-run launcher
   (the missing `run_coupled.sh`).

8. **Test parity** — run both C++ and Python end-to-end against
   identical inputs; compare. Known offsets (e.g. methodology-driven
   step at 2020 in CH4 EF and N2O MM, HANDOFF §2.5) need
   documentation, not "fixing".

### 4.7 GCM patterns and the three regrid utilities

**Path:** `Common-directory/IMOGEN-codebase/patterns/`, `Regrid/`,
`FastRegrid/`, `RegridLPJG/`
**Detailed report:** `_phase2_findings/07_patterns_and_regrid.md` (30 KB)

#### 4.7.1 GCM pattern inventory

**36 directories + 1 readme.log under `patterns/`**, three formats:

1. **34 CMIP5 ASCII** dirs `CEN_<institute>_MOD_<model>/` — each 12
   month files (`jan` … `dec`) of identical size (~200 KB each = 12
   forcing-variable columns × 1631 cells × 1 header line). Total per
   GCM: 2.4 MB. Land-only HadCM3 grid (1631 cells, 3.75°×2.5°,
   excluding Antarctica).
2. **1 CMIP3 legacy** `ukmo_hadcm3_rel/` — same ASCII format but
   relative-to-baseline, ~2.0 MB. The original Zelazowski/Huntingford
   HadCM3 pattern.
3. **1 CMIP6 NetCDF** `CMIP6_IMOGEN_EBM_values_and_patterns/` —
   contains 5 GCMs (GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR,
   MRI-ESM2-0, UKESM1-0-LL). Each GCM has `<gcm>_patterns.nc`
   (4.0 MB, CF-1.7 NetCDF-4, dims `imogen_drive=12, lat=56, lon=96`,
   8 named pattern vars: `tl1_patt`, `ql1_patt`, `precip_patt`,
   `wind_patt`, `pstar_patt`, `swdown_patt`, `lwdown_patt`,
   `range_tl1_patt`) + `<gcm>_params.json` (245 B, 5 EBM scalars
   `kappa_o, lambda_l, lambda_o, mu, f_ocean`).

The `readme.log` contains:
```
#imogen CMIP5 patterns
see also /pd/data/lpj/input_data/IMOGEN_patterns/CMIP5/patterns/
and copy needed patterns folder here
```

**The CMIP6 NetCDF set is on disk but not consumed by either Fortran or
C++ IMOGEN.** Both readers expect the CMIP5 ASCII format only. [SA7 §3]

The full enumeration of the 34 CMIP5 GCMs is reproduced in Appendix A.4.

#### 4.7.2 CMIP5 ASCII format details

Annotated `head` of `CEN_IPSL_MOD_IPSL-CM5A-MR/jan`:

```
    0.00  -60.00  360.00   90.00                                     ← bbox header
281.25  82.50   1.4383  -0.2364  -0.0103   0.0000   5.0209  ...      ← lon, lat, 12 cols
285.00  82.50   1.3262  -0.1372  -0.0145   0.0000   4.9234  ...
...
```

Per-row layout: `lon (0..360°E), lat (deg N, range −60..+90), 12
monthly pattern coefficients`. The "12 columns" almost certainly
encode 8 forcing variables (the same 8 as the CMIP6 NetCDF), padded
with 4 zero/reserved columns; this is observable in the IPSL-CM5A-MR
sample (columns 6, 11, 13 are identically zero across all rows).

The exact column→variable map lives in the Fortran IMOGEN reader
(`GCM_ANLG`'s `READ` statement at `imogen_lpjg.f:3226-3231`):

```
READ(51,*) LONG_AM(L), LAT_AM(L), DT_C_PAT, DRH15M_PAT,
&         DUWIND_PAT, DVWIND_PAT,
&         DLW_C_PAT, DSW_C_PAT,
&         DDTEMP_DAY_PAT, DRAINFALL_PAT,
&         DSNOWFALL_PAT, DPSTAR_C_PAT
```

So the 12 columns are: T, RH15M, U-wind, V-wind, LW, SW, DTEMP_day,
rainfall, snowfall, P*, plus 2 more (the IPSL sample shows only 11
non-zero data values; the trailing zero column may be reserved for
diurnal range or similar).

#### 4.7.3 CMIP6 NetCDF roadmap

[SA7 §8] proposes a **minimum-disruption migration path** (data side
only):

1. Write a small Python/MATLAB script that, for each `<gcm>_patterns.nc`:
   - Reads each of the 8 `_patt` variables on the 56×96 grid.
   - Bilinearly or NN samples them onto the 1 631-cell IMOGEN HadCM3
     land gridlist.
   - Composes 12 ASCII month files (`jan`…`dec`) in the CMIP5 layout
     documented above (header `lon_min lat_min lon_max lat_max`, then
     `lon lat v1 v2 … v12` per cell), padding zero columns to match
     what the Fortran expects.
   - Drops them into a new directory `CEN_CMIP6_MOD_<gcm>/` parallel
     to the existing CMIP5 dirs.
   - Converts the JSON params into the per-GCM Fortran data block / namelist.
2. The Fortran IMOGEN then needs **zero changes** — it just sees 5 more
   "CMIP5-style" GCMs.

The more invasive path: add NetCDF + JSON readers to IMOGEN
(which would also require regridding from 56×96 to 1631-cell at
runtime). Better long-term but Fortran work.

The working paper's chosen GCM is **MRI-ESM2-0** which IS in the CMIP6
NetCDF set. So adopting CMIP6 is required for the working paper's
canonical run.

#### 4.7.4 The three regrid utilities

[SA7 §4-6]:

| Util | Path | LOC | Build | Status |
|---|---|---:|---|---|
| `Regrid` | `Regrid/Regrid.cpp` | 308 | Visual Studio only — no CMakeLists, no Makefile | ❌ no Linux build |
| `FastRegrid` | `FastRegrid/FastRegrid/{Regrid.h,Regrid.cpp,FastRegrid.cpp}` | 540 (lib + driver) | `CMakeLists.txt` (CMake ≥ 3.10, C++17, OpenMP linked) | ⚙️ CMakeLists references lowercase `regrid.cpp`/`fastregrid.cpp` but disk has PascalCase → fails on case-sensitive Linux |
| `RegridLPJG` | `RegridLPJG/RegridLPJG/RegridLPJG.cpp` | 435 | Visual Studio only — no CMakeLists, no Makefile | ❌ no Linux build |

Plus the file `RegridLPJG/RegridLPJG/closest_points.txt` (355 148
lines, 17 MB) — a **committed run-output artefact** that should be in
.gitignore.

**Roles:**
- `Regrid` — earliest, walks IMOGEN's per-year output dirs and
  regrids the 5 anomaly files (`T_anom.dat, SW_anom.dat, P_anom.dat,
  DTEMP_anom.dat, WET.dat`) from IMOGEN's HadCM3 grid (1631 cells)
  onto a finer target gridlist. Other 4 per-year files (`CO2.dat,
  done, dtemp_o.dat, fa_ocean.dat`) byte-copied unchanged.
- `FastRegrid` — re-engineered library + example. Supports both
  IMOGEN YEAR_BY_YEAR layout and LPJ-GUESS GRID_BY_TIME layout.
  Haversine distance, precomputed mappings.
- `RegridLPJG` — regrids LPJ-GUESS GRID_BY_TIME `.out` files (header +
  `lon lat year v1 v2 …` rows for 1901-2100) from LPJ-GUESS's native
  gridlist onto the IMOGEN `gridlist_hurtt_RNDM_midpoint.txt`. IDW
  with hardcoded `power=2`, always uses 5 nearest neighbours
  (regardless of `radius` argument — the radius parameter is dead).

**Bugs / dead code** [SA7 §7]:
- All three utilities have hardcoded Windows paths
  (`C:\GitHub\…` or `C:/GitHub/…`).
- None take CLI args, env vars, or config files — must be edited and
  recompiled to retarget data.
- `Regrid::findClosestDataPoint` (line 86-95): latitude of closest
  source overwritten with target latitude, but longitude is left as
  the *adjusted source* longitude. Output coordinates won't match the
  requested gridlist exactly.
- `RegridLPJG.cpp:210-211`: `regridded.lat = target.first;
  regridded.lon = target.second;` — `target` was filled at line 252
  via `target_points.emplace_back(lon, lat)` so `target.first==lon`
  and `target.second==lat`. So `regridded.lat` is actually a longitude.
  Cancels at output (write order is also swapped) but the field-name
  swap is a smell that will bite future readers.
- `RegridLPJG.cpp:200-207` runs O(targets × years × sources × vars)
  triple loop where O((targets+years) × sources) would suffice.
- `RegridLPJG.cpp:104` always picks 5 nearest neighbours, ignoring
  `radius`.
- `RegridLPJG.cpp:375-380` has 14 of 15 file types disabled by
  comment; only `agpp.out` is processed.
- `FastRegrid/CMakeLists.txt:8,12` references lowercase `regrid.cpp`/
  `fastregrid.cpp`, disk has PascalCase → Linux build broken.
- `FastRegrid/CMakeLists.txt:16-20` finds and links `OpenMP::OpenMP_CXX`,
  but `Regrid.cpp` contains **no `#pragma omp` directives anywhere**
  → dead OpenMP link.

#### 4.7.5 Spec drift between utilities

[SA7 §7]:
- Three different gridlists referenced: `Regrid` uses
  `gridlist_hurtt_RNDM_midpoint_3698.txt`; `FastRegrid` and
  `RegridLPJG` use `gridlist_hurtt_RNDM_midpoint.txt`. Relationship
  between `_3698` and the unsuffixed file undocumented.
- IDW radii are 5.0° (Euclidean, Regrid), 100 km (Haversine,
  FastRegrid), 1500 km (notional only, RegridLPJG). Not directly
  comparable.

#### 4.7.6 Recommendation

Adopt **`FastRegrid`** as the canonical regridder (it has the cleanest
API, library/driver split, OpenMP intent, Haversine distance).
Required fixes: (a) lowercase the source filenames OR fix the
CMakeLists case; (b) actually add `#pragma omp parallel for` to the
hot loops; (c) make paths CLI-arg-driven; (d) extend with NetCDF
input support so it can also handle CMIP6 patterns and
`RegridLPJG`'s job. Retire `Regrid/` and `RegridLPJG/` to `archive/`.

### 4.8 Auxiliary tooling — `NdepFastArchive`, `Matlab-scripts`, `Python-scripts`, `Plots`

**Detailed report:** `_phase2_findings/08_orchestration_and_data.md §7`
(within SA8)

#### 4.8.1 `NdepFastArchive`

Standalone C++ tree to read/repack the `Data/Ndep/ndep_cruncep/
GlobalNitrogenDeposition*.bin` files. 5 auto-generated FastArchive
header files for the 5 RCP scenarios; `Main.cpp` opens
`GlobalNitrogenDeposition.bin`, iterates all records, and writes
lon/lat to `output_gridlist.txt`. Useful for matching N-dep archive
gridlists to runs. **No Makefile or CMakeLists.** Windows-path
hardcoded in `Main.cpp`. [SA8 §7.4]

#### 4.8.2 `Matlab-scripts/`

Three `.m` scripts: `new_iiasa_cmip6_{ch4,co2,n2o}_plots_*.m`. Each
reads from a hardcoded relative base `IIASA_DATABASE/Emissions/CMIP6/`
that **does not exist anywhere in the repo**. Produces aggregate SSP
scenario plots. Out-of-repo dependency.

#### 4.8.3 `Python-scripts/`

One Colab notebook + auto-export
(`LPJG_IMOGEN_COUPLED_MODEL_FRAMEWORK_PLOTS.{ipynb,py}`). Hardcodes
`/content/drive/MyDrive/LPJG_IMOGEN_DATABASE/...` paths — **Colab-only
as written**. Reads files like `IPCC_OWI_FAO_methane_1961_2009.txt`
relative to its working dir.

#### 4.8.4 `Plots/`

9 pre-rendered PNGs from the Matlab/Python scripts:
`CMIP6_{CH4,CO2,N2O}_LPJG_IPCC_{NON_,}SIMULATED.png` and
`CMIP6_{CH4,CO2,N2O}_TOTAL.png`.

**Recommendation:** all three auxiliary trees can be replaced by
plotting capabilities already in `Intermediary_py/src/`. Specifically,
`src/component_a_anthropogenic/rcmip_substitution/{rcmip_comparison1,
rcmip_comparison2}_plotting.py` produces equivalent agri-only and
full-totals comparisons; `src/component_c_integration/external_comparators_*`
produces equivalent IPCC-vs-IIASA comparisons. The Matlab and Python
notebook trees should be archived; the Plots/ PNGs replaced by
Intermediary_py outputs.

---

## 5. Data inventory

The unified Data/ tree at A/ measures **18 GB total** (B is **16 GB**;
the 2 GB difference is the pre-baked IMOGEN climate archives in A's
`Common-directory/`). Per top-level subdir of `Data/`:

| Subdir (A/Data/) | Size | Subdir purpose | Files of note |
|---|---:|---|---|
| `Concentrations/` | 9.5 MB | GHG concentration time series for IMOGEN forcing | `CO2_all.dat` (year, ppm, ...); `EPA/` CSVs; `IIASA/CMIP6/` and `IIASA/CMIP5/` IIASA-published RCP/SSP concentration files (XLSX + ZIP); MAGICC-format `.DAT` (`PICNTRL_MIDYR_CONC.DAT`, `PRE2005_MIDYR_CONC.DAT`, `RCP*_MIDYR_CONC.DAT`) and interpolated `rcp{26,45,60,85}_{ch4,co2,n2o}_interpolated.txt` |
| `Emissions/` | 916 KB | IIASA-only inventories (legacy/reference) | `IIASA/CMIP5/`, `IIASA/CMIP6/` |
| `Gridlist/` | 3.4 MB | LPJ-GUESS / IMOGEN gridlists | `gridlist_hilda+.txt` (62 864), `gridlist_hurtt_RNDM_midpoint.txt` (59 191), `gridlist_hurtt_RNDM_midpoint_3698.txt` (3 696), **`gridlist_in_62892_and_climate.txt`** (62 538 — the active gridlist for the SSP1_RCP26 setup), `gridlist_test2.txt` (4), `ndep_gridlist.txt` (59 191), `patterns_gridlist.txt` (1 631 — IMOGEN HadCM3 grid) |
| `Imogen/` | 5.2 MB | IMOGEN-specific climate placeholders + emission inputs | Empty `Climate/output/ssp{126,245,370,460,585}/`; `emiss/CMIP5/{Co2,CH4-N2O,Non-Co2-CH4-N2O-RF}/`; `emiss/CMIP6/{Co2,CH4-N2O,Non-Co2-CH4-N2O-RF}/`; loose files `RF_NONCO2_GHG_IS92A.dat`, `emiss_co2.dat`, `hist_rcp{2p6,4p5,6p0,8p5}_emiss_ch4_n2o_total_cmip5.txt` |
| `Intermediary/` | 2.2 GB | Intermediary working file system | `Emissions/{co2,methane,nitrogen,enteric_*,IPCC_OWI_FAO_*,total_methane_nitrogen_*}_ssp*.txt`; `IPCC_OWI_FAO/`; `IPCC_PLUM/`; `Input/{CMIP5,CMIP6}/`; `Input/{FAOSTAT.csv, PLUM_Fertilizer_SSP{1..5}.txt, arablelands.csv, countries.txt, livestock-counts.csv, n2ofertilizer.csv}`; `PLUM_data/{plum_land_use,agg_land_use,animals_ssp{1..5}.txt}` |
| `LU/` | 7.3 GB | Land-use forcing for LPJ-GUESS | `SSP1_RCP26_concatenated/` only realised; `LU_*_final.txt` (200 yr × 0.5° × 4 columns NATURAL/CROPLAND/PASTURE/BARREN), `cropfracs_*_final.txt` (22 cropPFT columns), `nfert_*_final.txt`, `irrig_*_final.txt`; each with `.map.bin` binary lookup index |
| `Ndep/` | 501 MB | Lamarque-format N-deposition binary archives | `ndep_cruncep/GlobalNitrogenDeposition{,RCP26,RCP45,RCP60,RCP85}.bin` |
| `soil/` | 3.5 MB | LPJ-GUESS soil-property table | `soilmap_center_interpolated.remapv10_old_62892_gL.dat` (header + 62 892 cells × 7 props: clay, silt, sand, orgC, CN, pH, cellfraction) |

`B/Data/` is the same except: **no `Data/soil/`**, **no
`Data/Concentrations/`**, **no `Data/Imogen/`** — B's ins files
compensate by pointing outside the repo to
`/bg/data/lpj/bampoh-d/...`.

The `A/Common-directory/` adds:
- `IMOGEN/` (397 MB): standalone IMOGEN run output 1871-2100 from
  2025-06-16. **Not coupled — see §1.3 verdict.**
- 5 × `IMOGEN_SSP{1..5}_RCP{26,45,70,60,85}_Clim/` (396 MB each =
  1.98 GB): pre-baked per-scenario climate archives.
- `IMOGEN-codebase/` (169 MB): the Fortran IMOGEN source + GCM patterns + climatology base.
- `LPJG_main/IMOGEN/`: the LPJ-GUESS↔IMOGEN handshake directory.
  Contains 9 files: `imogen_lpjg.txt` (368 B handshake settings),
  `imogen_lpjg_flux.txt` (10 B placeholder),
  `imogen_lpjg_ch4_n2o_flux.txt` (13 B placeholder), reference
  historical flux files (`extended_lpjg_only_cfluxrcp{26,85}.txt`,
  `lpjg_only_cfluxrcp26.txt`, `ch4_n2o_annual_historical_ssp{1rcp26,
  5rcp85}_lpjg_simulated_real.txt`), 0-byte `README.txt.txt`.

`B/Common-directory/` is 169 MB — only `IMOGEN-codebase/` plus the
`LPJG_main/IMOGEN/` handshake dir. No standalone IMOGEN run output, no
pre-baked climate archives.

**Disk usage that should NOT be in git** (must be archived externally):
- `A/Common-directory/IMOGEN/` (397 MB) — IMOGEN run output
- `A/Common-directory/IMOGEN_SSP*_RCP*_Clim/` (1.98 GB) — pre-baked
  climate archives
- `A/Data/LU/SSP1_RCP26_concatenated/` (7.3 GB) — preprocessed LU
  forcing (intermediate; reproducible)
- `A/Data/Ndep/ndep_cruncep/*.bin` (501 MB) — binary FastArchives
  (reproducible from upstream Lamarque)
- `A/Data/Intermediary/PLUM_data/plum_land_use/*.txt` (1+ GB) — raw
  PLUM outputs (project-internal, modeller-supplied)
- `A/Data/Intermediary/Input/*.csv` and `.txt` (~5 MB each, but
  reproducible from FAO/OWI/EDGAR public sources)
- `A/Intermediary_py/imogen_ghg_controller_FULL/inputs/` (5.1 GB)
  — full Intermediary_py inputs + outputs
- `A/Intermediary_py/imogen_ghg_controller_FULL.tar.gz` (105 MB)
- `B/Common-directory/IMOGEN/` is small (~12 MB) but `extended_lpjg_only_cfluxrcp*.txt`
  also reproducible

**Total disk that should NOT be in git**: ~17 GB of A's 18 GB; ~5 GB of B's 16 GB.

---

## 6. Run setups — workstation A vs cluster B

### 6.1 Top-level inventory

Both versions share the same 17-entry top-level layout, differing only
in one directory name:
- `A/landsymm_imogen_setup/` (workstation, the wrapper directory)
- `B/landsymm_imogen/` (cluster, no wrapper)

Inside each is exactly one realised scenario directory:
`SSP1_RCP26/`. The other four nominal scenarios
(`SSP2_RCP45`, `SSP3_RCP70`, `SSP4_RCP60`, `SSP5_RCP85`) are absent
from disk in both versions, despite being implied throughout
`Data/Imogen/emiss/CMIP{5,6}/...` and
`Data/Intermediary/Emissions/...co2_ssp{1..5}.txt`.

### 6.2 `SSP1_RCP26/` contents (33 files)

[SA8 §1.2]:

```
$ ls SSP1_RCP26/
crop.ins                         landcover.ins
crop_n.ins                       main.ins
crop_n_pftlist.simplePFT.remap10_g2p.ins   pasture_n_stlist.ins
crop_n_stlist.simplePFT.remap10_g2p.{N0-60-200-1000,agreed_treatments}.ins  pasture_n_stlist_agreed_treatments.ins
global.ins                       setup_run.sh
global_soiln.ins                 wetlandpfts.ins
imogen_intermediary.ins
guess (symlink to ../../../Integrations/trunk/trunk_r13078/build_imogen/guess)
gridlist_*.txt (12 files: test1, test2, test480, germany_HiRes/LoRes,
   hurtt_RNDM_midpoint{,_3698,_3698_10cells,_3711,_eu}, in_57{393,819,824}_
   plumharm2lpjg{,_rem,_random}, in_62892_and_climate)
guess.log (A only, residue from a partial in-place test)
qsat_output.txt (A only, residue from a debug dump)
```

### 6.3 A-vs-B differences in `SSP1_RCP26/`

[SA8 §1.2]:

| File | Differs? | Notes |
|---|---|---|
| `setup_run.sh` | identical | Calls missing `setup_run_owl_*` helper (see §6.4) |
| `global.ins`, `global_soiln.ins`, `wetlandpfts.ins`, `crop_n_*`, `pasture_n_*`, `crop_n.ins`, all `gridlist_*.txt` | identical | byte-for-byte |
| `main.ins` | **path prefix swap** | A: `/home/bampoh-d/Desktop/...`; B: `/bg/data/lpj/bampoh-d/...`; B uses bare `gridlist.txt` (split per-process by SLURM driver) |
| `crop.ins`, `landcover.ins` | **path prefix swap** | Same |
| `imogen_intermediary.ins` | **differs significantly** | A: `scenario "cmip6"` + CMIP6/SSP1-2.6 emiss files; B: `scenario "cmip5"` + CMIP5/RCP2.6 emiss files. A: `LPJG_CFLUX 1`; B: `LPJG_CFLUX 0`. A: `DIR_COMMON_OUT` absolute; B: `"./"` for parallel runs. **A and B run *different* scenarios under the same dir name.** |
| `guess` symlink | target differs | A → local `build_imogen/guess`; B → cluster `build_landsymm_imogen/guess` |

### 6.4 The missing launcher

`setup_run.sh` is identical in A and B:

```bash
#  args setup_run_owl_with_scratch_lpj_work.sh:
#  <runname>  <maininsfile> "all other ins files in quotes" <grid>  ...
setup_run_owl_with_scratch_lpj_work.sh $(basename $PWD) main.ins \
  "global.ins global_soiln.ins imogen_intermediary.ins landcover.ins crop.ins crop_n.ins crop_n_pftlist.simplePFT.remap10_g2p.ins crop_n_stlist.simplePFT.remap10_g2p.agreed_treatments.ins crop_n_stlist.simplePFT.remap10_g2p.N0-60-200-1000.ins pasture_n_stlist.ins pasture_n_stlist_agreed_treatments.ins wetlandpfts.ins" \
  gridlist_in_62892_and_climate.txt  imogencfx  "" 2 owl  haswell 8 haswell 40
```

`setup_run_owl_with_scratch_lpj_work.sh` **does not exist anywhere in
the workspace** (verified additionally with both `Glob "**/setup_run_owl*"`
and `Grep "setup_run_owl_with_scratch_lpj_work"`). It is a Lund LSA
cluster-side helper that must be installed system-wide on the cluster.
On a plain workstation, this script does nothing useful.

A workaround for workstation runs: invoke `./guess` directly with the
arguments the helper would have constructed:

```bash
./guess -input imogencfx main.ins
```

(All 12 ancillary ins files are imported transitively via `main.ins`.
The 13th file `imogen_intermediary.ins` is imported with the
`!import` directive in `main.ins`.)

### 6.5 Other inconsistencies

Inconsistency in the `setup_run.sh` comment block: the comment header
says `setup_run_keal_with_scratch_lpj_work.sh` while the call below
uses `setup_run_owl_with_scratch_lpj_work.sh` — owl/keal are two
different LSA clusters; the comment was not updated. Same drift in
`Integrations/trunk_r13078_test/{lsa_hist_base_ipsl,
integrated-4.1-ins2,integrated-4.1-ins2-wsl}/setup_run.sh`.

`A/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/main.ins`
hardcodes a path leading **outside** the actual checkout
(`/home/bampoh-d/Desktop/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/...`)
that may not exist. Fragile leftover.

### 6.6 What the user would actually run on a workstation

Per the audit's evidence:

```bash
# 1. Build LPJ-GUESS with the IMOGEN sources linked in
cd Integrations/trunk/trunk_r13078/build_imogen
cmake .. && make
# produces ./guess (the binary symlinked into SSP1_RCP26)

# 2. Build the C++ Intermediary if used (Python is recommended; see §12)
cd Intermediary/Code
make
# produces bin/ipcc

# 3. Build / install the Fortran IMOGEN if standalone is needed
cd Common-directory/IMOGEN-codebase/code
gfortran -ffixed-line-length-132 -O imogen_lpjg.f nonco2.f -o imogen_lpjg.exe

# 4. Run the coupled scenario (single-process, with the bug fixes from §8 applied)
cd landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26
./guess -input imogencfx main.ins
```

The `./guess` binary, with the fixes applied, will produce the
IMOGEN climate year by year inside `Common-directory/IMOGEN/output/<YYYY>/`
and consume them back via the `imogencfx::getclimate` path. The
`Imogen-controller` is not needed.

---

## 7. Documentation map

The framework's `References/` directory holds **~70 unique documents**
(some have A/B duplicates). Subagent 1 catalogued them by
authoritativeness. The full per-document index is in
`_phase2_findings/01_documentation_inventory.md` (86 KB). Here we
reproduce the **per-topic source-of-truth ranking** and the
**retirement plan**.

### 7.1 Per-topic source-of-truth (cite the top entry first)

| Topic | Source-of-truth | Subordinate sources |
|---|---|---|
| Framework name, scope, scientific design | `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` (working paper draft) | `Intermediary_py/{HANDOFF,TECHNICAL_MANUAL}.md` for the IC; `LPJG_IMOGEN coupling docs.docx` for input modules + IMOGEN settings + C++ Intermediary maps; top-level `README.md` (cautious — outdated for science); `Imogen_paper_GMD.docx` (do not cite — user-flagged ignore) |
| Coupling protocol (`done` files, year-by-year) | Working paper §2.4.2/§2.4.3 | `LPJG_IMOGEN coupling docs.docx`; top-level README; `Imogen-controller/README.txt` |
| IMOGEN config + Fortran subroutines | `Subroutines Defined in imogen.docx` | `LPJG_IMOGEN coupling docs.docx` (full settings); source code |
| IPCC Tier-1 EFs and intermediary maps | Working paper Appendix A (Tables A1-A14) | IPCC 2019 Refinement V4 PDFs (Ch5/10/11); `IPCC_Maps_Reassessment_Validation.docx`; `LPJG_IMOGEN coupling docs.docx` Maps section (outdated); `Reassessment of maps.docx` (outdated draft, do not cite) |
| Sector ownership / double-counting | Working paper §2.4.4 (Table 8) | `Intermediary_py/HANDOFF.md` §6 + `methodology.md` + `component_C.md`; `Emissions Handling Methodology.docx` (B-only) |
| Boundary harmonisation (1961, 2020) | Working paper §2.3.1, §2.3.4 | `Emissions Handling Methodology.docx` (B-only) — possibly contradictory; `Intermediary_py/HANDOFF.md` — incomplete |
| N2O sectoral disaggregation | Working paper §2.3.2 | `Emissions Handling Methodology.docx` (B-only) §5; `Brief Documentation of N2O Disaggregation Methodology.docx/.pdf` (OUTDATED, do not cite) |
| NEE/NBP definitions in `cflux.out` | `NEE-NBP Changes Report.docx/.pdf` (B-only) | Working paper §2.2.6; `Adding Net Biome Productivity…docx` (OUTDATED); `LPJG_IMOGEN coupling docs.docx` (OUTDATED — same incorrect formula) |
| Pasture fertilisation | `Pasture_Fert_Doc.docx`; source code (`management.cpp/.h`) | (none) |
| LPJ-GUESS data ingestion | `Intermediary_py/HANDOFF.md` §3 + `…/docs/component_B.md` | Source code |
| SSP-RCP scenarios | Working paper §2.2.9 (SSP1-2.6 + SSP2-4.5) | `Intermediary_py/README.md` (capability for all 5); `Plots-Details.txt`; `Imogen_paper_GMD.docx` (SSP1+SSP5 — OUTDATED); `Intermediary/Code/config.txt` (SSP1+SSP5 + CMIP5 — OUTDATED) |
| Validation thresholds | Working paper §2.4.7; `Intermediary_py/HANDOFF.md` §4 | (none) |

### 7.2 Retirement plan

[SA1 §5] proposes:

**DELETE (Junk / lock files / Word temp):**
- All `~$*.docx` Word lock files (`~$broutines Defined in imogen.docx` in
  both A/B; `~$issions Handling Methodology.docx` in B).
- `~WRL0536.tmp` in both A/B.
- `Common-directory/LPJG_main/IMOGEN/README.txt.txt` (empty 0-byte).
- `Imogen-controller/config.txt` ("Future implementation of a config
  file" placeholder).

**RETIRE (move to `archive/` or delete; superseded):**
- `Imogen_paper_GMD.docx` — superseded by working paper.
- `Adding Net Biome Productivity Calculations to Technical Branch of
  LPJG v4.docx` — superseded by `NEE-NBP Changes Report` (B-only).
- `Brief Documentation of N2O Disaggregation Methodology.{docx,pdf}` —
  superseded by working paper §2.3.2.
- `Reassessment of maps.docx` — superseded by `IPCC_Maps_Reassessment_Validation.docx`.
- `Intermediary/Code/config.txt` — Windows paths + CMIP5 settings.
- `LPJG Integration Work Overview and Updates[28-05-2024].docx` — older
  fork-integration notes (out of scope).
- `Ecosystems Modelling Project Update Report.pdf` — same.
- `Addressing Cross-Compiler Incompatibilities Between MSVC and GCC.{docx,pdf}` —
  Linux-only project per user instruction.

**DEDUPLICATE:**
- `gmd-11-2273-2018.pdf` and `gmd-11-2273-2018-1.pdf` — keep one.
- `Zelazowski_et_al_2018…pdf` and `gmd-11-541-2018.pdf` — same paper; keep one.
- `IMOGEN-gmd-3-679-2010.pdf` and `Common-directory/IMOGEN-codebase/docs/huntingford_et_al_10.pdf` — same paper; keep one.
- Triplicated `Intermediary_py/` (top-level, FULL, SOURCE_ONLY) — keep
  top-level only.

**CONSOLIDATE / NORMALISE:**
- All `README.txt.txt` → `README.md` (or `README.txt`).
- Top-level README → current-of-record version derived from working
  paper §1+§2.1, renamed to "LandSyMM-IMOGEN".
- `LPJG_IMOGEN coupling docs.docx` → drop empty stub sections (Troubleshooting,
  Case Studies, Future Developments, Glossary); drop Microsoft Visual
  Studio / MSVC / Windows-only sections; replace stale NBP formula with
  corrected one from `NEE-NBP Changes Report`; replace inline C++ Maps
  section with pointer to either C++ source (if retained) or Python
  pipeline (if C++ retired).
- Promote `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` to a
  top-level `paper/` directory.
- Consolidate B-only `Plots-Details.txt` and
  `Projets_Completion_Plan_Blueprint.txt` into a single `TODO.md` or
  `paper_assets.md`.
- Strip the top 15-line chat excerpt from `Intermediary_py/Quick_Start.md`.

**KEEP AS-IS (authoritative):**
- Working paper draft.
- `Intermediary_py/{README.md, HANDOFF.md, TECHNICAL_MANUAL.md,
  inputs_README.md}` and `…/docs/*.md`.
- `Subroutines Defined in imogen.docx`.
- `Pasture_Fert_Doc.docx`.
- `Emissions Handling Methodology.docx` (B-only).
- `NEE-NBP Changes Report.{docx,pdf}` (B-only).
- `IPCC_Maps_Reassessment_Validation.docx`.
- All peer-reviewed PDFs (ground truth).
- The 4 B-only PDFs cited by the working paper:
  `gmd-15-6709-2022.pdf` (Martín Belda 2022), `gmd-18-1785-2025.pdf`
  (Mathison PRIME — *cited by the working paper*),
  `Alexander et al 2017…pdf` (Alexander 2018 — *cited by the working
  paper*), `Rabin et al 2020…pdf` (Rabin 2020 — *cited by the working
  paper*).

The remaining B-only PDFs (`WG1AR5_Chapter06_FINAL.pdf`,
`V2_1_Ch1_Introduction.pdf`) are background references and can be
retained for context.

---

## 8. Catalogue of bugs, gaps, and dead code

The eight subagent reports together catalogue ~120 distinct issues
across the framework. This section consolidates them into a single
severity-ranked table, deduplicating overlaps and re-checking the
most important entries against the source.

### 8.1 Critical (🔴) — active code defects affecting correctness today

| # | Component | Location | Description | Fix |
|---:|---|---|---|---|
| C1 | LPJ-GUESS imogencfx | `Integrations/trunk/trunk_r13078/modules/imogencfx.cpp:483` | `exit(200);` immediately after `RUN_IMOGEN_ENGINE();` terminates LPJG before any gridcell is simulated; not in standalone fork | **Delete the line** |
| C2 | LPJ-GUESS climatemodel | `Integrations/trunk/trunk_r13078/modules/climatemodel.cpp:330–331` | `doneExist = true;` hardcoded; the actual `INQUIRE` for the LPJG-side `done` file is commented out | **Restore** the `INQUIRE`, delete the `doneExist=true` |
| C3 | LPJ-GUESS climatemodel | `Integrations/trunk/trunk_r13078/modules/climatemodel.cpp:334, 341, 350` | `runnowOpen`/`runfluxOpen`/`runnonco2fluxOpen` "is the writer still flushing?" guards are commented out | **Restore** the guards (or replace with an explicit barrier) |
| C4 | LPJ-GUESS imogen_input | `Integrations/trunk/trunk_r13078/modules/imogen_input.cpp:728` | `ndep.getndep(...)` is commented out; `ndep` is then used at line 855 in `getclimate` (`ndep.get_one_calendar_year`) without ever having been initialised → undefined behaviour | **Uncomment the call** (or move to `init()`) |
| C5 | Run setup ins file | `landsymm_imogen{,_setup}/SSP1_RCP26/imogen_intermediary.ins:102–109` | 6 `param "file_*"` paths use `IMOGEN/ouput/` (typo for `output`); 1 says `R_anom.dat` (file is `Rh_anom.dat`). Verified additionally: `param "file_temp"` IS consumed at `imogencfx.cpp:370`, so the typo IS a real bug — currently masked by C1's `exit(200)` | **Fix the typos**: `ouput` → `output` (×6); `R_anom.dat` → `Rh_anom.dat` (×1). Optional: drop unused `param "file_relhum"` and `param "file_wind"` (BLAZE not plumbed) |
| C6 | C++ Intermediary Main | `Intermediary/Code/src/Main.cpp` (A: 199–237; B: 243–277 + earlier) | Adder/Extractor/Wetlands merge step **commented out** in both A and B → C++ Intermediary produces only per-SSP CH4/N2O scenarios, never the IMOGEN-bound 3-col combined product | **Restore** the commented block (A) or **commit to Python pipeline** instead (recommended; see §12.3) |
| C7 | C++ Intermediary Calculator (A only) | `Intermediary/Code/src/Calculator.cpp:73–76` (A) | `calcNitrogenExcretion` formula is `rate*mass*1000/365` instead of `(rate/1000)*mass*365`; off by a factor of 10⁶ per animal. **Every N2O reference output in `Data/Intermediary/Emissions/` was computed with this buggy formula** | **B already fixed**. Adopt B's formula |
| C8 | C++ Intermediary NitrogenEmissions (A only) | `Intermediary/Code/src/NitrogenEmissions.cpp` (A `startCalculations_historic_nitrogen_1961_2009`) | `getline(ss, temp, ',')` reads into wrong variable for `n2ofertilizer.csv`; historic fertiliser N2O always 0 | **B already fixed**. Adopt B's read |
| C9 | C++ Intermediary Adder (A) | `Intermediary/Code/src/Adder.cpp:239` | `int vecSize = lastyear = firstyear + 1;` — assignment to **global** `lastyear`. Currently dead code, but would be catastrophic if revived | **Fix to comparison or addition** |
| C10 | IMOGEN Fortran QSAT | `Common-directory/IMOGEN-codebase/code/imogen_lpjg.f:4131–4134` | `PAUSE` left inside `QSAT` (called every gridcell × every sub-day step × every day × every month) — halts on first call awaiting interactive input | **Delete the `PAUSE`** and the surrounding `qsat_output.txt` debug dump |
| C11 | IMOGEN Fortran qsat | `Common-directory/IMOGEN-codebase/code/imogen_lpjg.f:4120–4128` | `qsat_output.txt` opened/written every `QSAT` call but never closed → file-handle leak; wasteful I/O | **Delete the dump** |
| C12 | IMOGEN Fortran mkdir | `Common-directory/IMOGEN-codebase/code/imogen_lpjg.f:435, 461` | `CALL SYSTEM('mkdir '//TRIM(...)//'\IMOGEN\output\'//THISYEAR)` uses Windows backslashes; Linux interprets `\IMOGEN\…` as one filename → mkdir fails silently | **Replace with forward slashes** (or use `EXECUTE_COMMAND_LINE` with `mkdir -p` on Linux) |
| C13 | IMOGEN Fortran settings | `Common-directory/IMOGEN-codebase/code/imogen_settings.txt:1–10` | All paths `C:\GitHub\dbampoh\…` — won't run on Linux without editing | **Replace with relative paths** or via `imogen_settings_tmpl.txt` shell substitution |
| C14 | C++ IMOGEN settings | `IMOGENCXX/ImogenCXX/src/Main.cpp:525` | `std::ifstream settings_file("C:\\GitHub\\dbampoh\\…\\imogen_settings.txt");` hardcoded | **Use a CLI arg or `getenv("IMOGEN_SETTINGS")`** with fallback `"./imogen_settings.txt"` |
| C15 | C++ IMOGEN system call | `IMOGENCXX/ImogenCXX/src/Main.cpp:1648` | `system("pause")` inside `QSAT` — Windows-only, halts execution | **Delete** |
| C16 | C++ IMOGEN DAY_CALC | `IMOGENCXX/ImogenCXX/src/Main.cpp:1149–1162` | Body is empty; the Fortran's 462-line sub-daily disaggregation is missing | **Port the Fortran's `DAY_CALC` body** OR adopt the Fortran build instead |
| C17 | C++ IMOGEN SOLPOS | `IMOGENCXX/ImogenCXX/src/Main.cpp:918–923` | One-line placeholder (`SINDEC = sin(2π(d-81)/365)`, `SCS = 1367`); the Fortran is a 60-line orbital-elements routine | **Port the Fortran's `SOLPOS` body** OR adopt Fortran build |
| C18 | C++ IMOGEN DTEMP_OUT | `IMOGENCXX/ImogenCXX/src/Main.cpp:1293` | Assignment `DTEMP_OUT[L][J][K] = DTEMP_DAILY[L][J][K]` is commented out; `DTEMP_anom.dat` will contain only zeros from C++ | **Uncomment** OR adopt Fortran |
| C19 | C++ IMOGEN year loop | `IMOGENCXX/ImogenCXX/src/Main.cpp:2626` | `} while (KEEPRUNNING = true);` — assignment, not comparison → infinite loop | **Change to `KEEPRUNNING == true` or just `KEEPRUNNING`** |
| C20 | C++ IMOGEN done polarity | `IMOGENCXX/ImogenCXX/src/Main.cpp:784–792` | `SETTING_LPJG` *creates* `LPJG_main/IMOGEN/done` instead of *deleting* it (Fortran semantics) | **Change to `remove(done_file_path)`** |
| C21 | C++ IMOGEN spin-up vectors | `IMOGENCXX/ImogenCXX/src/Main.cpp:2044–2058` | `push_back(0.0)` instead of zeroing existing entries → `FA_OCEAN`, `DTEMP_O`, `SEED_RAIN` get appended-to per spin-up, the original seeds 9465/1484/3358/8350 become unreachable | **Change to `std::fill(vec.begin(), vec.end(), 0.0)`** |
| C22 | C++ IMOGEN ofstream lifetime | `IMOGENCXX/ImogenCXX/src/Main.cpp:2499–2622` | `ofstream` for `fa_ocean.dat`, `dtemp_o.dat`, `T_anom.dat`, etc. opened only on `IYEAR == YEAR1`; for `IYEAR > YEAR1` writes go to a default-constructed (closed) stream and are silently dropped | **Open per-year** (move `open()` outside the `if`) |
| C23 | C++ IMOGEN OCEAN_CO2 | `IMOGENCXX/ImogenCXX/src/Main.cpp:391–458` | Off-by-one in the `RS[ISTEP - I]` indexing because Fortran was 1-based; drops one term and reads one out-of-range zero per outer step | **Fix indexing** |
| C24 | C++ IMOGEN flag | `IMOGENCXX/ImogenCXX/src/Main.cpp:2366` | Passes `NONCO2_EMISSIONS` to `FAIR_NON_CO2_GHG_BUDGET` where the function expects `NONCO2_EMISSIONS_LPJG` | **Pass `NONCO2_EMISSIONS_LPJG`** |
| C25 | C++ IMOGEN clim path | `IMOGENCXX/ImogenCXX/src/Main.cpp:2231` | `FILE_CLIM = DIR_CLIM.substr(0, II_CLIM) + "\\" + DRIVE_MONTH[j] + VARYEAR_STR;` uses `\\` separator | **Replace with `/`** |
| C26 | C++ IMOGEN ES table | `IMOGENCXX/ImogenCXX/src/Main.cpp:1300–1613` | Saturation-vapour-pressure table has duplicated first entry (lines 1301–1302), shifting the table by one vs Fortran | **Delete the duplicate** |
| C27 | C++ IMOGEN WET.dat fmt | `IMOGENCXX/ImogenCXX/src/Main.cpp:2523` | Written through `<< fixed << setprecision(3)` (float format) instead of `i10` integer | **Use `<< std::setw(10)` and integer cast** |
| C28 | Imogen-controller make | `Imogen-controller/Makefile:26` | Builds `Imogen-controller-cxx.cpp` (Windows-only) even when `detected_OS != Windows` | **Change to `Imogen-controller-cross.cpp`**; OR retire entirely (recommended; see §4.4) |
| C29 | Imogen-controller booleans | `Imogen-controller/Imogen-controller-cxx.cpp:80,199,240,251` | Writes `TRUE`/`FALSE` (no dots) into `imogen_lpjg.txt` — breaks Fortran namelist parsing | **Use `.TRUE.`/`.FALSE.`** or commit to non-Fortran consumer |
| C30 | Imogen-controller path | `Imogen-controller/Imogen-controller-cross.cpp:158` | `commonDirectory + "LPJG_main\\IMOGEN\\done"` — Windows separator on Linux + wrong subdir (`done` is at `IMOGEN/output/<YYYY>/done`) | **Fix the path** OR retire entirely |
| C31 | C++ Intermediary config | `Intermediary/Code/config.txt` | `baseDirectory=C:\GitHub\…` requires editing for every run | **Use relative path or env var** |
| C32 | C++ Intermediary grid | `Intermediary/Code/src/Extractor.cpp` | `cdtarea(lat, lon, 1.25, 1.25)` hardcodes 1.25° but LPJ-GUESS default is 0.5° → area off by ~6.25× per cell | **Read resolution from gridlist or as a parameter** |
| C33 | Intermediary_py deps | `Intermediary_py/imogen_ghg_controller/{requirements.txt, pyproject.toml}` | EDGAR scripts read xlsx via pandas (silently requires `openpyxl`); not in dependencies → fresh install fails on first EDGAR-using script | **Add `openpyxl>=3.0` to requirements** |
| C34 | Run launcher | `landsymm_imogen{,_setup}/SSP1_RCP26/setup_run.sh` | Calls `setup_run_owl_with_scratch_lpj_work.sh` which is not present anywhere in the repo | **Provide a self-contained workstation launcher + a SLURM batch template** (see §12.5) |
| C35 | Run-setup ins file (FILE_LPJG_FLUX path-override) | `landsymm_imogen{,_setup}/SSP1_RCP26/imogen_intermediary.ins:63, 65` | `FILE_LPJG_FLUX` and `FILE_LPJG_CH4_N2O_FLUX` are absolute paths to **static IIASA-derived reference files**; the engine reads the IIASA file regardless of LPJG state. The `LPJG_main/IMOGEN/imogen_lpjg_flux.txt` placeholder is bypassed entirely. Even with C1 (`exit(200)`) removed, this configuration produces **prescribed-emissions IMOGEN runs, not closed-loop coupling**. See §3.7. | **Rewrite to relative filenames** (e.g. `FILE_LPJG_FLUX "imogen_lpjg_flux.txt"`) AND **implement the LPJG-side writer** for those files, OR explicitly document the current mode as "prescribed" in a `coupling_mode` parameter |

### 8.2 Latent (🟡) — masked by other conditions; will activate on fix-up

| # | Component | Location | Description |
|---:|---|---|---|
| L1 | LPJ-GUESS imogencfx | `imogencfx.cpp:1039` | Missing `- 273.15` Kelvin→°C conversion in `climate.temp = dtemp[date.day];` (`imogen_input.cpp:871` has the conversion). Currently dead due to C1; will activate once exit(200) is removed |
| L2 | LPJ-GUESS imogen_input | `imogen_input.cpp:380–383, imogencfx.cpp:553–556` | `extract_line_data` only parses 12 monthly values; daily branch (`for idx<MAX_YEAR_LENGTH`) missing → daily files silently produce zero arrays |
| L3 | LPJ-GUESS imogen_input | `imogen_input.cpp:494–495, imogencfx.cpp:668–669` | Distance metric uses raw `(file_lons - lons)²` without antimeridian wrap → cells near ±180° won't match |
| L4 | LPJ-GUESS imogen_input | `imogen_input.cpp:116–129` | Year-substitution uses `find("Y")` instead of `find("%Y")`; any literal `Y` upstream in the path gets wrongly replaced |
| L5 | LPJ-GUESS imogencfx | `imogencfx.cpp:792–794` | BLAZE-incompatibility `fail()` is commented out; `drelhum`/`dwind` not plumbed → BLAZE runs would silently use zero humidity/wind |
| L6 | LPJ-GUESS imogencfx | `imogencfx.cpp` & `imogen_input.cpp` | `getNfert(Gridcell&)` declared but never defined; `void year_init(int rank, int calendar_year)` declared but never defined → compile-time linker errors waiting if `InputModule` virtual interface is changed |
| L7 | LPJ-GUESS misc-output stubs | `miscoutput.h:172, miscoutput.cpp:121–136` | 12 IMOGEN-output `Table` objects declared, 12 ins-file params declared with wrong description strings; never wired (no `create_output_table`, no writers) |
| L8 | LPJ-GUESS misc-output | `miscoutput.h:69–79` | `getImogenData(int lower, int upper)` returns a literal random number from a Mersenne Twister; no callers anywhere |
| L9 | LPJ-GUESS imogenlogger | `imogenlogger.cpp:75, 114, 131, 137` | `std::lock_guard<std::mutex>` lines all commented out → not thread-safe (would race under MPI/OpenMP) |
| L10 | LPJ-GUESS imogenlogger | `imogenlogger.cpp:82–85` | `create_directory(logDir)` commented out; logger silently fails (no log file) if dir doesn't exist and `RUN_IMOGEN_ENGINE` didn't pre-create it |
| L11 | LPJ-GUESS framework | `framework.cpp:30-41, 76-77, 99-164` | Large block of commented-out `#include "climatemodel.h"`, `gen_filename`, `_mkdir` helpers — refactor debris |
| L12 | LPJ-GUESS imogen_input | `imogen_input.cpp:39-94` | `_mkdir` helper recursively calls itself but the OS `mkdir` is commented out (lines 88, 92) → on Unix `_mkdir` recurses but never creates dirs. Dormant (no callers pass `fmakedir=true`) |
| L13 | LPJ-GUESS header guards | `imogen_input.h:10, imogencfx.h:10` | Both use the same identifier `LPJ_GUESS_IMOGEN_INPUT_H`. Including both files in the same TU silently excludes the second |
| L14 | IMOGEN Fortran TODOs | `imogen_lpjg.f:751,772; nonco2.f:107,127` | Multiple TODO comments asking `IYEAR vs IYEAR-1?` flagging year-indexing ambiguity for LPJG-flux year matching |
| L15 | IMOGEN Fortran NFARRAY | `imogen_lpjg.f:88` (`PARAMETER NFARRAY=10000`) | Caps single-segment runs to ~500 yr at `NCALLYR=20`. Runtime check at line 3332 only `PRINT`s a warning, doesn't abort |
| L16 | IMOGEN Fortran NGPOINTS | `imogen_lpjg.f:290` (`PARAMETER NGPOINTS=3698`) | Hard-caps user-facing gridlist size (recompile required to change). Stack memory ~410 MB at this size |
| L17 | IMOGEN Fortran GPOINTS | `imogen_lpjg.f:188` (`PARAMETER GPOINTS=1631`) | Hard-cap on internal IMOGEN climatology grid; cannot be raised without regenerating pattern + climatology files |
| L18 | IMOGEN Fortran F_WET_CLIM_OUT | `imogen_lpjg.f:909–913` | Silently bumps wet-day count to 1 when total monthly precip ≥ 0.5 µm. Harmless but undocumented |
| L19 | IMOGEN Fortran CO2_all.dat | `imogen_lpjg.f:332` | `OPEN(98, ..., 'CO2_all.dat', ACCESS='APPEND', STATUS='REPLACE')` — gfortran wins on REPLACE so file is truncated each invocation |
| L20 | IMOGEN Fortran SETTIN_LPJG | `imogen_lpjg.f:1493` | `CASE DEFAULT` doesn't echo offending label; only `SETTIN`'s does (after the patch) — easy source of silent typo bugs |
| L21 | IMOGEN Fortran tiny gridlist | `imogen_lpjg.f:1161` | `gridlist_global.txt` (13 rows) would crash `REGRID_CLIM` because `NGPOINTS=3698` but the file has only 13 lines; `IF(IOS.NE.0) CONTINUE` is no-op so reads silently produce garbage in `LON_OUT(14..3698)` |
| L22 | IMOGEN Fortran LAND_FEED stub | `imogen_lpjg.f:796–800` | If `LAND_FEED=T` AND `LPJG_CFLUX=F`, sets `D_LAND_ATMOS = -CONV*0.25*C_EMISS_LOCAL` with `WARNING: Land C uptake defaulting to 25% of emissions`. Hardcoded placeholder |
| L23 | C++ IMOGEN duplicate includes | `IMOGENCXX/ImogenCXX/src/Main.cpp:13–25` | `#include <iostream>` etc. appear three times — merge debris |
| L24 | C++ IMOGEN INVERT alloc | `IMOGENCXX/ImogenCXX/src/Main.cpp:221–306` | `INVERT` allocates 3 dense `N_OLEVS²×sizeof(double) ≈ 1.5 MB` matrices on every call inside `DELTA_TEMP`'s inner timestep loop — allocator load |
| L25 | C++ IMOGEN settings parser | `IMOGENCXX/ImogenCXX/src/Main.cpp:537, 545` | `value.erase(std::remove_if(..., ::isspace), value.end())` strips spaces from path values — fine for Windows paths without spaces, will silently break paths with spaces; `find` first ASCII space (`' '`), tab-separated keys won't parse |
| L26 | C++ Intermediary year window | `Intermediary/Code/src/MethaneEmissions.cpp` (B) | `myHistoricMethane_modelled_1961_2009.resize(59)` and `< 2020` filter — covers 1961-2019; variable still named `_1961_2009` |
| L27 | C++ Intermediary species map | `Intermediary/Code/src/MethaneEmissions.cpp:47-48` (B) | 13-element `FAO_items` array iterated `i<10`; reordering breaks species mapping. Currently dead (call commented) |
| L28 | C++ Intermediary code col | `Intermediary/Code/src/MethaneEmissions.cpp:56-63` (B) | `getline(ss, temp, ',')` for `Code` column commented out; `stoi(country_code)` would throw. Currently dead |
| L29 | C++ Intermediary magic 160 | `Intermediary/Code/src/Adder.cpp:103,105,107,109` | Magic offset `160` hardcodes `firstyear=1850`; if user sets `firstyear=1900`, IPCCMethane/IPCCNitrogen indexing into merged output silently shifts |
| L30 | Regrid asymmetric overwrite | `Regrid/Regrid.cpp:86–95` | `closestData.latitude = target.latitude` but `longitude` is left as adjusted source longitude → output coordinates won't match target gridlist exactly |
| L31 | RegridLPJG field swap | `RegridLPJG/RegridLPJG.cpp:210–211` | `regridded.lat = target.first; regridded.lon = target.second;` — `target.first==lon` so `regridded.lat` is actually a longitude. Cancels at output (write order is also swapped) but smelly |
| L32 | RegridLPJG O(N⁴) | `RegridLPJG/RegridLPJG.cpp:200–207` | Triple loop with per-(target × year) source filter inside; could be O((targets+years)·sources) with group-by-year |
| L33 | RegridLPJG dead radius | `RegridLPJG/RegridLPJG.cpp:104` | Always picks 5 nearest neighbours, ignoring `radius` argument (now only consulted in commented-out warning) |
| L34 | FastRegrid case mismatch | `FastRegrid/FastRegrid/CMakeLists.txt:8,12` | References lowercase `regrid.cpp`/`fastregrid.cpp` but disk has PascalCase → fails on case-sensitive Linux |
| L35 | FastRegrid dead OpenMP | `FastRegrid/FastRegrid/CMakeLists.txt:16-20` | Finds and links `OpenMP::OpenMP_CXX`, but `Regrid.cpp` contains no `#pragma omp` directives anywhere → dead linkage |
| L36 | NdepFastArchive Windows path | `NdepFastArchive/Main.cpp` | `C:\\GitHub\\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\\NdepFastArchive\\bin\\x64\\Debug\\GlobalNitrogenDeposition.bin` hardcoded |

### 8.3 Cosmetic (🟢) — comments, typos, dead declarations

| # | Component | Location | Description |
|---:|---|---|---|
| K1 | LPJ-GUESS imogenlogger | `imogenlogger.cpp:20` | Comment typo `<C++!7` (should be `<C++17`) — typo introduced in trunk relative to LandSyMM fork |
| K2 | LPJ-GUESS imogencfx | `imogencfx.cpp:122–135` | All 12 `declare_parameter` description strings for IMOGEN output files are wrong (10 of 12 read "Imogen Temperature Anomalies." regardless of content) |
| K3 | LPJ-GUESS framework | `framework.cpp:30-41, 76-77, 99-164` | Commented-out IMOGEN includes / helpers — refactor debris |
| K4 | LPJ-GUESS imogencfx | `imogencfx.cpp:834` | Comment `// Note that first_call is static, so this assignment is remembered` is incorrect (`first_call` is regular member, not static) |
| K5 | LPJ-GUESS imogen_input | `imogen_input.cpp` (top) | Filename comment claims `ImogenInput.cpp8` (typo) |
| K6 | IMOGEN Fortran Windows VS Code | `code/.vscode/settings.json` | Hardcoded Windows AppData path for fortls.path |
| K7 | IMOGEN Fortran mixed slashes | `imogen_lpjg.f:410, 421` (`/`); `:435, 461` (`\`) | Mixed conventions inside the same file |
| K8 | IMOGEN Fortran stray decl | `imogen_lpjg.f:268` | `LATMIN_DAT,LATMAX_DAT,LONGMIN_DAT,LON  GMAX_DAT` — embedded space ignored by fixed-form Fortran (parses as `LONGMAX_DAT`); never used |
| K9 | C++ Intermediary header swap | `Adder.h` declares `class MethaneEmissions`; `MethaneEmissions.h` declares `class Adder` |
| K10 | C++ Intermediary lone TODO | `Maps.h:328 (A) / 515 (B)` | `{"Pasture Range and Paddock", 0.004}, // TODO:` annotation; the only TODO/FIXME marker in the entire C++ Intermediary tree |
| K11 | C++ IMOGEN FIX ME | `IMOGENCXX/ImogenCXX/src/Main.cpp:1150, 2590` | `// FIX ME` and `// OPTIMIZATION IN PROGRESS` markers |
| K12 | Imogen-controller wrong dir override | `Imogen-controller.cpp:214` | Hardcoded `"C:\\GitHub\\LPJ_IMOGEN_coupling\\Common_Directory\\…"` overrides `commonDirectory` in one branch |
| K13 | Documentation lock files | `References/~$broutines Defined in imogen.docx`, `~$issions Handling Methodology.docx`, `~WRL0536.tmp` (A and B) | Word lock files to be deleted |
| K14 | Documentation dual ext | All `README.txt.txt` | Windows double-extension artefact; should normalise to `README.md` |
| K15 | Documentation empty file | `Common-directory/LPJG_main/IMOGEN/README.txt.txt` | 0 B placeholder |
| K16 | Documentation trivial config | `Imogen-controller/config.txt` | Single-line "Future implementation of a config file" placeholder |
| K17 | Build artefacts in git | `Regrid/Regrid/x64/`, `FastRegrid/FastRegrid/x64/Release/`, `RegridLPJG/RegridLPJG/x64/Release/` | MSBuild `.exe.recipe`/`.iobj`/`.ipdb` files committed |
| K18 | Run output in git | `RegridLPJG/RegridLPJG/closest_points.txt` (17 MB) | Committed run-output artefact |
| K19 | Pre-baked climate in git | `A/Common-directory/IMOGEN_SSP*_RCP*_Clim/` (1.98 GB total) | Run output, not source |
| K20 | Triplicated source | `Intermediary_py/{,_FULL/imogen_ghg_controller/,_SOURCE_ONLY/imogen_ghg_controller/}` | Same source three times; keep top-level only |
| K21 | Quick_Start chat excerpt | `Intermediary_py/Quick_Start.md:1-15` | AI-conversation excerpt about reproducibility verification — out-of-place |
| K22 | Stale Intermediary_py FULL stats | `Intermediary_py/.../docs/`-related symlinks | Some `figures_gallery/*.png` symlinks point at non-existent targets in both FULL and SOURCE_ONLY |

### 8.4 Bug-density observations

- **LPJ-GUESS imogen* sources** carry the bulk of the active defects
  (5 of 34 🔴 entries). All can be fixed with at most ~50 lines of
  source edits.
- **C++ IMOGEN refactor (`IMOGENCXX`)** carries a large fraction of
  🔴 entries (12 of 34) but they cluster into one decision: should
  the refactor be revived or archived? Per §1.4, archiving and
  keeping Fortran is recommended.
- **C++ Intermediary** has version-specific bugs (A's wrong N
  excretion formula was already fixed in B; B introduced two new
  latent bugs of its own). A unified codebase should adopt B's
  fixes plus disable the dead historic call sites.
- **Run setup** has 1 🔴 (the missing launcher) — the framework as
  shipped has no working coupled-run entry point.
- **Documentation** has many 🟢 cleanups (Word lock files, double
  extensions, OUTDATED references) but only one substantive issue:
  the doc-vs-code mismatch around boundary harmonisation (see §9).

---

## 9. Documentation-vs-code contradictions

The audit confirmed 11 documented contradictions between sources and 4
implicit doc-vs-code mismatches. Listed in priority for the unified
codebase.

### 9.1 Confirmed contradictions between docs

[SA1 §4.1, deduplicated]:

| # | Topic | Source A | Source B | Adjudication |
|---:|---|---|---|---|
| D1 | NBP formula in `cflux.out` | Older `Adding NBP…docx` and embedded copy in `LPJG_IMOGEN coupling docs.docx` give a formula that *subtracts* `flux_fire` | `NEE-NBP Changes Report.docx/.pdf` (B-only) gives a corrected formula that *adds* `flux_fire` and decomposes into `NEE + c_disturb` | **B is correct.** Older docs OUTDATED |
| D2 | N2O sectoral disaggregation | `Brief Documentation of N2O Disaggregation Methodology.docx/.pdf` uses static 59.81%/40.19% LPJG/non-LPJG split (Ciais 2013) | Working paper §2.3.2 + `Emissions Handling Methodology.docx` use a dynamic temporal-based proportion (Tian 2024 GNB) | **Working paper is correct** |
| D3 | SSP scenarios in scope | Older `Imogen_paper_GMD.docx`: SSP1+SSP5. `Intermediary/Code/config.txt`: SSP1+SSP5 | Working paper: SSP1+SSP2. `Intermediary_py/README.md`: all 5 (capability) | **Working paper is correct** for evaluation; Python pipeline retains capability for all 5 |
| D4 | GCM choice | Older `Imogen_paper_GMD.docx`: IPSL-CM6-MR | Working paper: ISIMIP-3b MRI-ESM2-0 | **Working paper is correct** |
| D5 | Historical land-use forcing | Older `Imogen_paper_GMD.docx`: LUH2 (Hurtt 2011) | Working paper §2.4.5 + `Intermediary_py/HANDOFF.md`: HILDA+v2 (Winkler 2021), with LUH2-style 5-year-window harmonisation as a *technique* (not data) | **Working paper is correct**; LUH2 is the harmonisation methodology, HILDA+v2 is the data |
| D6 | Climate forcing in LPJ-GUESS Stage I | Top-level README: "LPJG handles its own spinup and historical data via netCDF; IMOGEN provides scenario-year climate (2000-2100); pre-2000 is netCDF" | Working paper §2.4.3: Stage I uses **prescribed ISIMIP-3b MRI-ESM2-0 climate for the entire 1850-2100** to produce potential yields. Stage II uses IMOGEN climate for the realised run | **Working paper is correct** |
| D7 | Emission-time-series scope | Top-level README: "IMOGEN provides climate data for the scenario years (usually from 2000 to 2100)" | Working paper §2.3 + `Intermediary_py/HANDOFF.md`: emissions assembled 1850-2100 (paper) or 1900-2100 (Python pipeline) | **Working paper is correct** |
| D8 | Boundary harmonisation algorithm | Working paper §2.3.4: Backward Tapered Harmonisation + Regression-Based Trend Matching + 5-year Centred MA | `Emissions Handling Methodology.docx`: Univariate Spline ratio. `Intermediary_py/HANDOFF.md`: segmented running-mean smoothing only, no boundary harmonisation algebra | **Documentation-vs-code mismatch.** See §9.2 |
| D9 | Build environment | `LPJG_IMOGEN coupling docs.docx` and `Addressing Cross-Compiler Incompatibilities.docx`: Microsoft Visual Studio + MSVC + CMake | User instruction: Linux-only project | **User instruction takes precedence** |
| D10 | Wetland CH4 data source | Older `Imogen_paper_GMD.docx`: GSW DB max-water-extent (1984+2018 average), static | Working paper §2.2.7: LPJ-WHyMe (Wania 2010) >40°N only; tropical = IIASA residual. `Intermediary_py/HANDOFF.md`: LPJG `mch4.out` + GMB IFW (+112) − DCC (−23) | **Working paper is correct**; Python's IFW/DCC is an additional refinement |
| D11 | Source of the term "Intermediary" | `LPJG_IMOGEN coupling docs.docx` uses "Intermediary" for a C++ codebase with Extractor/Adder/Calculator/PLUM Preprocessor/Maps modules | Working paper §2.4.1 introduces the term "Intermediary Controller (IC)" — the Python codebase implements the IC | The C++ "Intermediary" is the legacy implementation; the Python "Intermediary Controller" is current. **Retire C++ Intermediary** |

### 9.2 Doc-vs-code mismatches — neither code matches the working paper

In addition to D8 (boundary harmonisation), three further
documentation-vs-code mismatches surfaced:

| # | Where doc says | Where code does | Resolution |
|---|---|---|---|
| E1 | Working paper §2.3.4: BTH + RBTM + 5-yr MA | C++ `Adder.cpp:114-164` smoothing block commented out; `centeredMovingAverage` defined but never invoked. Python pipeline does only segmented running mean | **Either** update the paper to describe the segmented-running-mean approach, **OR** implement BTH in the unified Intermediary |
| E2 | Working paper §2.4.5: HILDA+v2 + LUH2-style 5-yr-window harmonisation at 2020 | Python pipeline: scenario-side LU starts at 2021 with no smoothing across the 2020/2021 boundary; HANDOFF.md acknowledges the discontinuity but doesn't implement smoothing | **Implement** the LUH2-style 5-year-window smoothing in the unified pipeline, **OR** document the discontinuity as a known feature |
| E3 | Working paper §2.4.6: Tier-1 EFs static 2020-2100 | Python pipeline: scenario-side N2O MM uses 2019-Refinement parameters while historic uses 2006 Guidelines parameters (HANDOFF §2.5) — produces a small step at 2020 (633 Gg historical vs 750.6 Gg SSP2 scenario) | **Document the methodology choice** in the working paper or harmonise to one set |
| E4 | Working paper: `cflux.out` includes corrected NEE = `flux_veg − flux_repr + flux_soil + flux_fire` | LPJ-GUESS code: not yet verified by code-level audit beyond the `NEE-NBP Changes Report` author's own statement | **Code-level audit** — Subagent 2 confirms `commonoutput.cpp` exists and writes `cflux.out`; the NEE/NBP formula change is the change documented in NEE-NBP Changes Report |

---

## 10. `version_A` vs `version_B` — full divergence accounting

### 10.1 Disk usage

- **A:** 18 GB (bigger than B by 2 GB).
- **B:** 16 GB.
- **Difference:** A's `Common-directory/` (2.5 GB) vs B's (169 MB).
  All 2.4 GB of the difference is run output that should not be in
  git: `IMOGEN/output/<YYYY>/` (2025-06-16 standalone IMOGEN seeding
  run, 230 year-dirs) + 5 × `IMOGEN_SSP*_RCP*_Clim/` (pre-baked climate
  archives).

### 10.2 Top-level structure

Both share identical 17-entry top-level layouts except:
- A has `landsymm_imogen_setup/` (workstation, with the wrapper dir).
- B has `landsymm_imogen/` (cluster, no wrapper).

Otherwise identical: `Common-directory`, `Data`, `FastRegrid`,
`IMOGENCXX`, `Imogen-controller`, `Integrations`, `Intermediary`,
`Intermediary_py`, `Matlab-scripts`, `NdepFastArchive`, `Plots`,
`Python-scripts`, `README.md`, `References`, `Regrid`, `RegridLPJG`.

### 10.3 Git history

Both are independent checkouts of the same upstream
(`https://github.com/dbampoh/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK`,
branch `main`). Common ancestor commit: `59eeb64 Update`.
- **A** is 1 commit ahead with `454bff9 Merge remote-tracking branch
  'refs/remotes/origin/main'` (just a merge — no new content).
  Plus `dc26cd8 Update` and `f102c6a Update` on shared trunk.
- **B** is 2 commits ahead with `5e982a0 Updates` and `93f111d Updates`
  (substantive content additions).

So **B is the more recent codebase** by content. The A-only "merge"
commit is tooling-only.

### 10.4 Code differences (Intermediary)

[SA5 §10]:
- B adds Logger.h/Logger.cpp.
- B adds 6 new diagnostic output CSV paths in config.
- B fixes `calcNitrogenExcretion` (factor 10⁶ off).
- B fixes the `n2ofertilizer.csv` getline bug.
- B fixes the `wetlandsMethaneEmissionsOutputPathwetlandsAreaFilePath`
  typo in `Main.cpp`.
- B renames `wetlandsAreaFilePath` to use `GLWD_v2_country_wetland_CH4_peat_openwater_km2.csv`.
- B uses a different livestock-counts file (`FAOSTAT_data_en_1-6-2026-livestock-counts.csv`,
  dated 6 Jan 2026).
- B switches `simulate_ipcc_fao_owi_rice_cultivation_methane_emissions`
  default to `true` (A defaults `false`).
- B introduces 2 latent bugs of its own (13-element FAO_items reordering,
  Code-column getline commented).

### 10.5 Code differences (LPJ-GUESS)

Both versions ship the same trunk_r13078 fork, byte-identical except
for the same 6-file diffs documented in §4.1.10 (the `exit(200)` is
present in BOTH A and B's trunk_r13078). The fork itself is byte-identical.

### 10.6 Documentation differences

[SA1 §1]:
- A and B share most of `References/`. **B has 6 extra documents:**
  - `Emissions Handling Methodology.docx` (scientific authority for
    SSP integration workflow; supersedes older `Brief Documentation of
    N2O Disaggregation`).
  - `NEE-NBP Changes Report.docx` and `.pdf` (correct NBP formula).
  - `Plots-Details.txt` (paper figure list).
  - `Projets_Completion_Plan_Blueprint.txt` (TODO list; oil-palm PFT
    parameterisation embedded).
  - 4 PDFs cited by the working paper:
    - `gmd-15-6709-2022.pdf` (Martín Belda 2022)
    - `gmd-18-1785-2025.pdf` (Mathison PRIME — directly cited)
    - `Alexander et al 2017…pdf` (Alexander 2018 PLUM v2 — directly cited)
    - `Rabin et al 2020…pdf` (Rabin 2020 LandSyMM — directly cited)
  - 2 PDFs for background:
    - `WG1AR5_Chapter06_FINAL.pdf` (IPCC AR5 Ch6)
    - `V2_1_Ch1_Introduction.pdf` (IPCC 2006 Vol 2 Ch1)

### 10.7 Run setup differences (`SSP1_RCP26/`)

[SA8 §1.2, §1.4]: Same 33 files, but:
- 4 ins files differ in path prefix (A: `/home/...Desktop/...`, B:
  `/bg/data/lpj/bampoh-d/...`).
- `imogen_intermediary.ins` differs in **scenario semantics**:
  - A: `scenario "cmip6"` + CMIP6/SSP1-2.6 emission files +
    `LPJG_CFLUX 1` + `DIR_COMMON_OUT` absolute.
  - B: `scenario "cmip5"` + CMIP5/RCP2.6 emission files +
    `LPJG_CFLUX 0` + `DIR_COMMON_OUT "./"`.
- A and B's `SSP1_RCP26` directory **runs different scenarios** under
  the same name. This is a silent semantic divergence.

### 10.8 Data/ differences

- B has no `Data/soil/`, no `Data/Concentrations/`, no `Data/Imogen/`.
  Cluster setup expects these to live at `/bg/data/lpj/bampoh-d/...`
  outside the repo.
- All other Data/ subdirs are byte-identical (sample byte-counts in
  §5).

### 10.9 Net assessment

**B is the more current and runnable codebase by content.** A is the
working-snapshot with the 2 GB of pre-baked IMOGEN run output. Neither
is canonical for the unified codebase: the unified codebase should
take **B's ins file content** (for the cluster scenario semantics that
the working paper actually wants — though see below), **B's Intermediary
code** (with the latent bugs fixed), and **A's Data/ content where
present** (especially `Data/soil/`).

But there is a subtlety: A's `imogen_intermediary.ins` uses
`scenario "cmip6"` + CMIP6/SSP1-2.6 emission files, which is *closer*
to the working paper's commitment to CMIP6+SSP-RCP scenarios. B uses
`scenario "cmip5"` + CMIP5/RCP2.6 — which is older and not what the
working paper specifies. So:

- For **scenario configuration**, take A's CMIP6/SSP files. The
  working paper §2.2.9 specifies SSP1-2.6 and SSP2-4.5 with ISIMIP-3b
  MRI-ESM2-0 forcing.
- For **operational mechanics** (parallel-friendly `DIR_COMMON_OUT="./"`,
  no preprocessed soil/concentrations/imogen baked in), take B's
  approach; resolve the missing data via deployment-time symlinks or
  install steps rather than committing them.

---

## 11. Open questions and uncertainties

The investigation cannot resolve the following without further input
from the original developer or running experiments. Listed in priority
order.

### 11.1 Operational

1. **Why was `exit(200)` added to `imogencfx.cpp:483` on 2026-03-21?**
   The standalone LandSyMM fork doesn't have it. Was it (a) an
   accidental commit of a debug shortcut that was never reverted, or
   (b) an intentional disabling because some downstream component was
   broken? Hypothesis (a) is strongly supported by the file mtime
   matching unrelated unrelated documentation work (e.g. the
   `NEE-NBP Changes Report` mtime is also 2026-03-21). Confirming this
   with the developer would unblock the highest-impact fix.
2. **What was the original synchronisation contract between LPJG and
   IMOGEN?** The polling code in `climatemodel.cpp:300-394` has six
   file-existence checks of which three are bypassed (`doneExist=true`,
   `runnowOpen` and `runfluxOpen` both not assigned). Two
   interpretations:
   (a) the engine was originally a separate process that watched a
   directory shared with a parallel LPJG process, then was ported
   in-process and the file barriers were partially neutered;
   (b) the file barriers were always optional and the in-process design
   relies on year-by-year synchronicity baked into `RUN_IMOGEN_ENGINE`'s
   inner `for (iyear=year1; iyear<=iyend; ...)` loop.
   The variable name `LPJG_main` in the path strings hints at (a).
3. **Where does LPJG actually emit `imogen_lpjg.txt` and the flux file
   `<FILE_LPJG_FLUX>`?** Subagent 2 did not find any LPJG-side writer.
   They are *read* by the engine (`climatemodel.cpp:528, 538`); the
   LPJG side that should populate them must live somewhere — possibly
   in `gcpoutput.cpp`/`commonoutput.cpp` writes that flow into the
   same path. Worth grepping wider.
4. **Is the `imogen_input` (loose) path expected to be the long-term
   LandSyMM coupling, with `imogencfx` only used for development?**
   The fact that `imogen_input` has a real Kelvin→°C correction and
   N-dep deactivation (suggesting it gets N-dep from `file_ndep` ins
   directly elsewhere), while `imogencfx` does not subtract Kelvin and
   does call `ndep.getndep`, suggests inconsistent maintenance.
5. **Has the C++ IMOGEN refactor ever successfully run end-to-end?**
   The infinite loop, inverted `done` polarity, empty `DAY_CALC`, and
   hardcoded settings path together imply that the binary cannot
   complete a year without manual intervention. Confirming whether the
   rewrite has ever been validated against the Fortran would inform
   whether to revive it.
6. **Has the C++ Intermediary's corrected `calcNitrogenExcretion` (B)
   ever been used to regenerate the reference `nitrogen_*.txt`
   outputs?** If not, every downstream artifact in
   `Data/Intermediary/Emissions/` is built on the buggy A formula.
7. **What runs the IMOGEN binary in the seeded
   `Common-directory/IMOGEN/output/` tree?** The 230 year directories
   were produced 2025-06-16 by an "IMOGEN LOGGER" with 4-5 s per year
   wall-clock — clearly not LPJG-driven. Possibly a manually-triggered
   `IMOGEN-codebase/code/...` build with `compile.sh`. Worth
   confirming whether it can be invoked standalone or only via LPJG.
8. **Are the 5 `IMOGEN_SSP*_RCP*_Clim/` directories in `A/Common-directory/`
   intended as canonical climate archives consumed by all later runs?**
   They have the same layout as `IMOGEN/output/` and the timestamps
   suggest they were pre-baked one after another. If yes, the setup
   should symlink or set `DIR_COMMON_OUT` per-scenario; if no, they
   are stale and could be archived out of git.
9. **Is `setup_run_owl_with_scratch_lpj_work.sh` available anywhere
   in the user's environment?** ~~Worth grabbing a copy and adding to
   the unified `tools/` directory.~~ **RESOLVED 5 May 2026: located
   at `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/`
   along with the full owl-cluster scripts toolkit. Integrated at
   step 16 of the V.1 rebuild plan.**

### 11.2 Scientific

10. **Has the LPJG `cflux.out` actually been updated to match the
    corrected NEE/NBP formula?** The `NEE-NBP Changes Report.docx`
    says yes, but a code-level audit of `commonoutput.cpp` is
    required (Subagent 2 confirmed the file exists; the formula
    consistency was not verified line-by-line in the audit).
11. **What is the actual operational coupling at run time — is the
    documented `done`-marker design the canonical one, or has the
    in-process design replaced it?** The audit's evidence supports
    in-process; the README's documentation supports two-process. A
    decision document is needed.
12. **What is the actual harmonisation algorithm in the production
    code?** Working paper §2.3.4 describes BTH+RBTM+5-yr MA. Python
    pipeline implements only segmented running-mean. C++ Intermediary
    has commented-out `centeredMovingAverage`. `Emissions Handling
    Methodology.docx` describes Univariate Spline. **Three documents,
    three different algorithms, none implemented in code.** Before the
    paper can be submitted, this must be reconciled.
13. **The exact list of LPJ-GUESS PFTs/CFTs/standtypes used in the
    coupled runs is not documented.** The working paper §2.1.1 names
    PLUM commodity categories ("C3 cereals, C4 cereals, rice, oil
    crops, pulses, starchy roots, monogastrics, ruminants") and
    LPJ-GUESS Stage I CFTs ("winter and spring C3 cereals, C4
    cereals, pulses, rice"). The actual `.ins` instruction file
    content is not in any current document; the
    `crop_n_pftlist.simplePFT.remap10_g2p.ins` and stand-type files
    in `SSP1_RCP26/` are the implementation but their mapping to the
    working paper's commodity categories is not documented.
14. **The exact spin-up procedure** is described in two places with
    different detail. Working paper §2.4.3: 500 yr at 1850-1900
    climatology with pre-industrial CO2 (~285 ppm). The older docs
    describe a more elaborate procedure with potential-yield setup
    runs vs main runs. Inconsistency to flag.
15. **Output products from coupled runs** — exactly which `.out` files
    are produced and how they are post-processed. Working paper §2.4.6
    names categories; `NEE-NBP Changes Report` documents `cflux.out`
    columns; the Python intermediary documents `mch4.out`/`ngases.out`/
    `cflux.out`. But there is no central registry.
16. **Is the C++ Intermediary still in the production run path, or
    fully retired in favour of Python?** The Python pipeline's
    Quick_Start says "please share the IMOGEN code so I can determine
    the input data form/structure/format requirements" — i.e. the
    Python-to-IMOGEN integration was never finished. The C++ remains
    *technically* still present. Decision needed.
17. **Is the Python pipeline's "OPTION B" CH4 rice methodology
    compatible with the C++ Intermediary's choice?** Option A is
    staged but not integrated (TECH §16.1).
18. **Are the CH4/N2O scenario-period-boundary discontinuities
    (HANDOFF §2.5: 22 Mt CH4 at 2020, 117 Gg N2O at 2020) acceptable?**
    They are methodologically intentional but might break smooth-trajectory
    assumptions in IMOGEN driver code.

### 11.3 Build / runtime / environment

19. **Has any of {Regrid, FastRegrid, RegridLPJG, NdepFastArchive}
    ever been built on Linux/the cluster?** Only FastRegrid has a
    CMakeLists, and it has the case-sensitivity bug. The committed
    `closest_points.txt` proves RegridLPJG was at least executed
    once on Windows.
20. **Where do the `IMOGEN-codebase/patterns/` files come from on the
    user's local system?** `readme.log` points to
    `/pd/data/lpj/input_data/IMOGEN_patterns/CMIP5/patterns/`, a
    server-local store. For workstation deployment they must be
    copied. For the CMIP6 NetCDF set, provenance is also unclear.
21. **Pattern-file consistency across GCMs.** Each CMIP5 ASCII
    `patterns/<GCM>/<month>` file must be exactly 1 header + 1631
    cells on the *same* IMOGEN gridlist for `GCM_ANLG` to work. This
    was verified for IPSL-CM5A-MR/jan only. Other GCMs may diverge.
22. **CRUNCEP_1960_1989 cycling.** The `VARYEAR` mechanism cycles 1..30
    to pick `<month><n>` files. With 30 years from 1960-1989, we
    presume `jan1`=1960, `jan30`=1989. Not documented.
23. **R wrappers (`Common-directory/IMOGEN-codebase/R_wrappers/`)** —
    standalone-IMOGEN driver scripts that look like a GCP2015/RCP2.6
    workflow. Not opened in the audit. Confirm they are not part of
    the coupled flow.
24. **`emiss/rcp_database/` and `emiss/new_emission_data/`** —
    provenance of the emissions/RF time series consumed by
    `FILE_SCEN_EMITS`, `FILE_NON_CO2_VALS`, `FILE_CH4_N2O_EMITS`
    is undocumented. The `historical_all_rcp_*.xls` spreadsheets in
    `emiss/DKB_dataset_totals/` likely contain the raw provenance.

---

## 12. Roadmap to a unified working codebase

Goal: **a single, version-controlled, public-quality, scientifically
defensible codebase that runs LandSyMM-IMOGEN coupled simulations
end-to-end on both Linux workstations and HPC clusters, with extensive
documentation that allows anyone to use, troubleshoot, and extend the
system without further author support.**

The roadmap has six layers, each independently shippable. Earlier
layers are prerequisites for later ones. Effort estimates are rough and
assume one experienced engineer (the user or a successor).

### 12.1 Layer 1 — Clean up (low risk, high value)

**Effort:** 1–2 days. **Output:** a hygienic baseline.

1. **Initialise the new repo** at
   `lpj-guess_imogen_landsymm/` with a sensible `.gitignore` (build
   artefacts, run output, `inputs/` data, large binaries).
2. **Copy authoritative source code** from the right places:
   - LPJ-GUESS LandSyMM fork from `lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`
     (NOT from `Integrations/trunk/trunk_r13078/` — the latter has the
     accidental `exit(200)` regression and 5 cosmetic comment changes).
   - Fortran IMOGEN from `Common-directory/IMOGEN-codebase/code/`
     (with the working `imogen_lpjg.f`; archive
     `Original Imogen Modified for LPJG Coupling/`).
   - Python Intermediary from `Intermediary_py/imogen_ghg_controller_SOURCE_ONLY/`
     (the smallest complete copy — top-level `Intermediary_py/` is
     identical content but extracted).
   - GCM patterns from `Common-directory/IMOGEN-codebase/patterns/`
     (35 dirs after deduplicating CMIP5 + CMIP6 + CMIP3 legacy + readme.log).
   - CRUNCEP base climatology from `Common-directory/IMOGEN-codebase/CRUNCEP_1960_1989/`.
   - Run-setup ins files from `landsymm_imogen{,_setup}/SSP1_RCP26/`
     (taking A's CMIP6/SSP1-2.6 scenario configuration and B's
     `DIR_COMMON_OUT="./"` operational mechanics; see §10.9).
3. **Do not copy** (delete or archive externally):
   - The 2 GB of pre-baked IMOGEN run output in
     `A/Common-directory/IMOGEN_SSP*_RCP*_Clim/` and `IMOGEN/output/`.
   - The Visual Studio MSBuild leftovers (`x64/Release/`,
     `x64/Debug/` everywhere).
   - The triplicated Intermediary_py FULL/SOURCE_ONLY (keep top-level only).
   - 7 GB of Land-use forcing in `Data/LU/SSP1_RCP26_concatenated/`
     — these are reproducible from PLUM + HILDA+ via `landsymm_py`.
   - 5 GB of Intermediary_py inputs in `imogen_ghg_controller_FULL/inputs/`
     — these are reproducible from public sources.
   - Junk files (Word lock files, `~WRL0536.tmp`, `README.txt.txt`
     double extensions, empty placeholders).
4. **Apply the cosmetic cleanups** (Section 8 🟢 entries):
   - Fix the `<C++!7` comment typo.
   - Fix the 12 misnamed `declare_parameter` description strings.
   - Delete dead code (`getImogenData`, the 12 unused `MiscOutput`
     IMOGEN tables, the `_mkdir` recursion).
5. **Establish the new repo's structure** per §13 below.
6. **Commit baseline.** Push to a fresh GitHub remote (e.g.
   `landsymm/lpj-guess_imogen_landsymm`); mirror to KIT/Helmholtz GitLab.

### 12.2 Layer 2 — Fix the seven coupling break-points

**Effort:** 1–2 days. **Output:** a functional tight-coupled binary
that produces a year of LPJG-IMOGEN simulation end-to-end.

Apply the 🔴 fixes catalogued in §8.1, in the order:

1. **C1**: Delete `exit(200);` at `modules/imogencfx.cpp:483`. Single line.
2. **C5**: Fix `IMOGEN/ouput/` typo (×6) and `R_anom.dat`/`Rh_anom.dat`
   (×1) in `imogen_intermediary.ins`. Optional: drop unused
   `param "file_relhum"` and `param "file_wind"` lines (unconsumed by
   `imogencfx`).
3. **C2, C3**: Restore the `INQUIRE` for `done` and the 3
   `runnowOpen`/`runfluxOpen`/`runnonco2fluxOpen` guards in
   `climatemodel.cpp:330–350`. Or, alternatively, simplify the polling
   loop down to the 2 file-existence checks that are still active and
   document this as the synchronisation primitive.
4. **C4**: Uncomment `ndep.getndep(...)` at `imogen_input.cpp:728` (or
   move into `init()` for cleaner lifetime).
5. **C10, C11, C12**: Fortran IMOGEN cleanups — delete `PAUSE` and
   `qsat_output.txt` debug dump in `QSAT`; replace `\\` with `/` in the
   2 `mkdir` calls.
6. **C13**: Replace Windows paths in `imogen_settings.txt` with
   relative paths (and provide `imogen_settings_tmpl.txt` for shell
   substitution at deployment).
7. **C34**: Provide a self-contained workstation launcher
   `run_coupled.sh` (see §12.5).
8. **C35**: Decide on coupling intent. The active ins file currently
   configures **prescribed-emissions IMOGEN runs masquerading as tight
   coupling**: all four `FILE_*` settings point at pre-computed static
   files (anthropogenic CO2/CH4/N2O via Intermediary; "natural"
   CO2/CH4/N2O via prior LPJG-only run outputs labelled
   `co2_pg_emissions_natural_*` and `ch4_n2o_annual_historical_natural_*`).
   See §3.7 for the full ownership table. To restore real two-way
   coupling (working paper §2.4.3):
   1. Edit `imogen_intermediary.ins`:
      ```diff
      -FILE_LPJG_FLUX "/home/.../co2_pg_emissions_natural_historical_ssp126_1850_2100.txt"
      -FILE_LPJG_CH4_N2O_FLUX "/home/.../ch4_n2o_annual_historical_natural_ssp126_1850_2100.txt"
      +FILE_LPJG_FLUX "imogen_lpjg_flux.txt"
      +FILE_LPJG_CH4_N2O_FLUX "imogen_lpjg_ch4_n2o_flux.txt"
      ```
      so the engine reads files in `<DIR_COMMON>/LPJG_main/IMOGEN/`
      that LPJG itself populates.
   2. Locate or implement the LPJG-side writer for those files
      (Subagent 2 §11 open question 3 — likely needed in
      `gcpoutput.cpp` / `commonoutput.cpp`). The writer must:
      - Compute year-end NEE in TgC/yr (the engine's expected unit
        for `C_LPJG`) from the cflux components per the corrected
        `NEE-NBP Changes Report` formula
        (`NEE = flux_veg − flux_repr + flux_soil + flux_fire`).
      - Compute year-end CH4 from `mch4.out` (Tg CH4/yr global sum)
        and N2O from `ngases.out` `N2O_soil + N2O_fire`
        (Tg N2O/yr global sum).
      - Append the year's row to `imogen_lpjg_flux.txt` and
        `imogen_lpjg_ch4_n2o_flux.txt` (creating them empty on the
        first call).
      - Write `imogen_lpjg.txt` with the next-year settings.
      - Touch `<DIR_COMMON>/LPJG_main/IMOGEN/done`.
   3. Add a startup banner that prints the current coupling mode
      ("tight" with year-by-year LPJG feedback, "prescribed" with
      static reference flux file, or "loose" with pre-generated
      IMOGEN climate files).
   4. **For sensitivity experiments**, retain the path-override mode
      explicitly via a `coupling_mode` ins parameter — it is a
      genuine scientific use case (e.g. running IMOGEN with a fixed
      emissions trajectory while varying GCM patterns), it just must
      not be the default and must not be silent.

After these fixes, run the smoke test described in §12.5 to confirm
the binary produces one year of coupled output **with LPJ-GUESS's own
NEE/NBP feeding back into the IMOGEN climate trajectory** (verifiable
by checking that perturbing an LPJG parameter changes the resulting
`CO2.dat` time series in `Common-directory/IMOGEN/output/<YYYY>/`).

### 12.3 Layer 3 — Adopt Python Intermediary; retire C++ Intermediary

**Effort:** 1 week. **Output:** the unified Intermediary path produces
the IMOGEN-bound emissions vectors and the LPJG↔IMOGEN handshake works
through them.

1. **Validate the Python pipeline standalone** in the new repo. Ensure
   `python run_all.py` runs end-to-end on a fresh Ubuntu workstation;
   add `openpyxl` to requirements (C33); strip the 15-line chat
   excerpt from Quick_Start.md (K21).
2. **Write the adapter `imogen_inputs_to_lpjg_format.py`** that
   converts the Python pipeline's 10-column wide CSV
   (`outputs/imogen_inputs/imogen_inputs_<SSP>.csv`) into the four
   2/3-column files the Fortran IMOGEN expects:
   - `<FILE_LPJG_FLUX>` (2-col `year flux`, TgC/yr)
   - `<FILE_LPJG_CH4_N2O_FLUX>` (3-col `year ch4 n2o`, Tg/yr each)
   - `<FILE_SCEN_EMITS>` (2-col `year emiss`, Pg/yr CO2)
   - `<FILE_CH4_N2O_EMITS>` (3-col `year ch4 n2o` Tg/yr anthropogenic)
   plus the non-CO2 RF file `<FILE_NON_CO2_VALS>` (which is currently
   read from a static IIASA file; the Python pipeline does not
   currently produce this).
3. **Wire the adapter into `run_coupled.sh`**: invoke `run_all.py`
   first, then the adapter, then place outputs at the paths
   `imogen_intermediary.ins` expects.
4. **Adopt Python TECH §15 fixes** that affect production correctness:
   - 15.6: standardise `MPLBACKEND=Agg` across plotting scripts.
   - 15.7: add `if __name__ == '__main__'` guards in scripts that
     don't have them.
5. **Archive the C++ Intermediary** under `archive/intermediary_cpp/`.
   Keep the legacy `Data/Intermediary/Emissions/*.txt` reference
   outputs as a parity baseline for a one-off comparison test, then
   move them too.
6. **Commit**. Validate that the Python+adapter chain produces files
   byte-identical to the legacy C++ outputs (modulo the
   `calcNitrogenExcretion` bugfix; document the expected delta).

### 12.4 Layer 4 — CMIP6 NetCDF patterns and IMOGEN refactor decision

**Effort:** 1–2 weeks. **Output:** the framework can run with the
working paper's chosen GCM (MRI-ESM2-0, CMIP6) without code changes to
the IMOGEN reader.

1. **Convert CMIP6 NetCDF patterns to CMIP5 ASCII format** per
   [SA7 §8]:
   - For each `<gcm>_patterns.nc` (5 GCMs: GFDL-ESM4, IPSL-CM6A-LR,
     MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL):
     - Read the 8 `_patt` variables on the 56×96 grid.
     - Bilinearly sample onto the 1631-cell IMOGEN HadCM3 land grid.
     - Compose 12 ASCII month files in CMIP5 format
       (`lon_min lat_min lon_max lat_max` header + `lon lat v1..v12`
       per cell), padding zero columns to match the Fortran reader.
     - Drop into `patterns/CEN_CMIP6_MOD_<gcm>/`.
   - For each `<gcm>_params.json`, generate a Fortran-namelist data
     block (or a small extension to `SETTIN` to read JSON).
   Result: 5 new pseudo-CMIP5 GCM dirs that the existing Fortran reader
   handles transparently.
2. **IMOGEN implementation strategy (revised — two-phase delivery)**:

   **Phase 4a (Fortran-with-ALLOCATABLE — primary, immediate).**
   Convert `imogen_lpjg.f` and `nonco2.f` to use `ALLOCATABLE`
   arrays for all variables that scale with `NGPOINTS` or `GPOINTS`.
   The current static `PARAMETER` declarations cap the gridlist at
   ~3 698 cells because the static BSS allocation cannot accommodate
   the 14 GB of arrays that a 62 000-cell gridlist requires (this is
   the practical limit the user has historically hit with the
   Fortran). With `ALLOCATABLE`, the same arrays go on the heap and
   scale to whatever physical RAM allows. Effort: 1-2 days
   refactoring + 1 day validation against the existing 1631-cell
   native run. See §4.3.3 for the gridlist-scaling analysis.

   **Phase 4b (C++ refactor brought to parity — follow-on).**
   With Phase 4a's Fortran outputs as the numerical-parity
   reference, fix the 25 catalogued bugs in
   `IMOGENCXX/ImogenCXX/src/Main.cpp`:
   - Port the empty `DAY_CALC` body from Fortran (462 lines).
   - Port the placeholder `SOLPOS` from Fortran (60 lines).
   - Fix `DTEMP_OUT` assignment (line 1293).
   - Fix the `} while (KEEPRUNNING = true);` infinite loop (line 2626).
   - Fix `SETTING_LPJG` `done`-file polarity (lines 784-792).
   - Fix the spin-up `push_back` corruption of `FA_OCEAN`/`DTEMP_O`/`SEED_RAIN`.
   - Fix `OCEAN_CO2` indexing.
   - Replace `system("pause")` and `localtime_s` with portable
     equivalents.
   - Fix output-file lifetime and formatting bugs.
   - Add a CMakeLists or Makefile.
   Numerical-parity test: per-gridcell, per-year, C++ outputs must
   match Fortran outputs to within the same numerical tolerance the
   Fortran enforces internally. Cost: 1-3 weeks of careful porting +
   parity testing.

   **Phase 4c (both available, switchable).** Expose both backends
   via an `imogen_backend "fortran"` or `imogen_backend "cxx"` ins
   parameter (or as two binaries `imogen_lpjg_fortran` and
   `imogen_lpjg_cxx` that LPJ-GUESS picks between). Cross-validation
   between them serves as ongoing QC: any divergence > tolerance
   triggers a regression check.

   **Phase 4d (long-term, optional).** Rewrite IMOGEN as a callable
   library that LPJ-GUESS links into directly without the
   file-rendezvous layer. Cost: months. Stretch goal beyond v1.0.

3. **Retire `Imogen-controller/`** under `archive/imogen_controller/`.
4. **Commit**. Validate that the unified codebase can switch GCMs by
   editing one line in `imogen_settings.txt` (`DIR_PATT`), and switch
   IMOGEN backends by changing one parameter.

### 12.5 Layer 5 — Orchestration (the missing top-level launcher)

**Effort:** 3–5 days. **Output:** self-contained workstation and
cluster launchers; CI/CD running on every commit.

1. **Workstation launcher `run_coupled.sh`**:

   ```bash
   #!/bin/bash
   #
   # Self-contained LandSyMM-IMOGEN coupled run launcher (Linux workstation).
   # Usage:
   #   ./run_coupled.sh <scenario> <gridlist>
   # Example:
   #   ./run_coupled.sh SSP1-2.6 gridlist_in_62892_and_climate.txt
   set -euo pipefail
   SCENARIO=${1:-SSP1-2.6}
   GRIDLIST=${2:-gridlist_in_62892_and_climate.txt}
   ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   #
   # 1. Ensure the binary is built
   cd "$ROOT/lpjguess/build_imogen" && cmake .. && make -j8
   cd "$ROOT"
   #
   # 2. Run the Python Intermediary if outputs aren't already present
   if [ ! -f "$ROOT/outputs/imogen_inputs/imogen_inputs_${SCENARIO}.csv" ]; then
     cd "$ROOT/intermediary_py"
     python run_all.py 2>&1 | tee "$ROOT/logs/intermediary_${SCENARIO}.log"
     cd "$ROOT"
   fi
   #
   # 3. Run the adapter to convert wide CSV → IMOGEN file formats
   python tools/imogen_inputs_to_lpjg_format.py \
     --input outputs/imogen_inputs/imogen_inputs_${SCENARIO}.csv \
     --output runs/${SCENARIO}/inputs/
   #
   # 4. Run LPJ-GUESS in tight-coupled mode
   cd "$ROOT/runs/${SCENARIO}"
   ../../lpjguess/build_imogen/guess -input imogencfx main.ins \
     2>&1 | tee "$ROOT/logs/coupled_${SCENARIO}.log"
   ```
2. **Cluster batch template `run_coupled.sbatch`**:

   ```bash
   #!/bin/bash
   #SBATCH --job-name=landsymm-imogen-{{SCENARIO}}
   #SBATCH --partition={{PARTITION}}
   #SBATCH --nodes={{NODES}}
   #SBATCH --ntasks-per-node={{TASKS}}
   #SBATCH --time=72:00:00
   #SBATCH --output=logs/%x-%j.out
   module load gcc/14 cmake/3.29 netcdf-c/4.9 openmpi/5.0
   srun ./run_coupled.sh {{SCENARIO}} {{GRIDLIST}}
   ```
3. **Smoke test**: a 3-cell, 3-year coupled run (uses
   `gridlist_test2.txt` or similar) that completes in <1 minute and
   produces canonical output files. Used in CI.
4. **CI/CD pipeline** (`.github/workflows/ci.yml` or
   `.gitlab-ci.yml`):
   - **Build LPJ-GUESS** with CMake + g++ + NetCDF + MPI on Ubuntu
     latest.
   - **Build Fortran IMOGEN** with gfortran.
   - **Build C++ Intermediary** (kept as legacy reference).
   - **Build Python Intermediary** venv + `pip install -r requirements.txt`.
   - **Run** the 3 existing `Intermediary_py/tests/*.py` pytest tests.
   - **Run** the smoke coupled-run test.
   - **Confirm** all reference outputs match expected (md5 or per-row
     pandas comparison with tolerance).
5. **Commit**. Tag a release `v0.1` that's reproducible end-to-end.

### 12.6 Layer 6 — Documentation harmonisation and paper alignment

**Effort:** 1–2 weeks. **Output:** complete, internally-consistent docs
ready to accompany a peer-reviewed publication.

1. **Promote the working paper** `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`
   to `paper/manuscript_draft.docx` in the new repo. This is the
   scientific source-of-truth.
2. **Resolve the 11 documentation contradictions** of §9.1 by
   retiring or updating the OUTDATED docs (D1-D11). Specifically:
   - Update or delete `LPJG_IMOGEN coupling docs.docx` (replace stale
     NBP formula; drop empty stub sections; drop Windows-build
     content).
   - Move `Imogen_paper_GMD.docx`, `Adding NBP…docx`,
     `Brief Documentation of N2O…`, `Reassessment of maps.docx`,
     `Addressing Cross-Compiler…` to `archive/references/`.
3. **Resolve the 4 doc-vs-code mismatches** of §9.2 (E1-E4). For E1
   (boundary harmonisation) the choice is binary: either implement
   BTH+RBTM in the unified Intermediary, or revise the paper to
   describe the actual segmented-running-mean approach. Recommend the
   latter, since the segmented approach is empirically validated
   against GCB/GMB/GNB.
4. **Write the unified technical manual**
   `docs/technical_manual.md` covering:
   - Scientific framework (synthesised from working paper).
   - Build instructions (LPJ-GUESS + Fortran IMOGEN + Python
     Intermediary).
   - Run instructions (workstation + cluster, single scenario +
     all 5 scenarios).
   - Output catalogue (every `.out` and `.csv` file with column
     definitions and units).
   - Known issues and limitations (synthesised from §8 + Python
     TECH §15).
   - Validation procedure and thresholds.
   - Troubleshooting (the empty section in `LPJG_IMOGEN coupling
     docs.docx` finally filled).
5. **Citation and reference cleanup**:
   - Deduplicate the redundant PDFs (Zelazowski, Smith FAIR,
     Huntingford 2010).
   - Move all peer-reviewed PDFs to `paper/references/`.
   - Add author-readable BibTeX entries.
6. **Build a `CONTRIBUTING.md`** documenting how to:
   - Add a new GCM (CMIP5 ASCII or CMIP6 NetCDF, with the converter from §12.4).
   - Add a new SSP-RCP scenario.
   - Modify IPCC tier-1 EFs.
   - Run sensitivity studies (e.g. with/without GMB IFW correction).
7. **Tag a release** `v1.0` at the end of this layer.

### 12.7 Future layers (post-v1.0, stretch goals)

These are *not* required for a working public release but represent
worthwhile improvements suggested by the audit and by the Python
TECHNICAL_MANUAL §16:

- **Native CMIP6 NetCDF support** in the IMOGEN reader (replacing the
  CMIP5-ASCII conversion shim from §12.4). Requires Fortran NetCDF
  bindings.
- **Tier-2 Intermediary** for CH4/N2O agricultural emissions,
  reducing the ~30-40 % per-sector uncertainty.
- **Uncertainty propagation** through the integrated trajectory
  (Monte-Carlo IPCC EF perturbations).
- **Replace the file-rendezvous coupling with in-process API calls**
  — turning IMOGEN into a callable library, rather than a subprocess
  invoked via filesystem polling. Avoids the year directories and the
  4-5 s sleep overhead.
- **Parallelise the LPJ-GUESS gridcell loop within a year** under
  OpenMP. Currently the IMOGEN polling loop sleeps; gridcell-level
  parallelism is upstream-LPJG and is exercised on cluster runs only.
- **NetCDF-native I/O** for the IMOGEN per-year output (replacing
  the per-year ASCII `*_anom.dat` files with a single per-run NetCDF).
- **Webapp dashboard** of run results for stakeholder communication.

---

## 13. Recommended directory structure for the unified codebase

```
lpj-guess_imogen_landsymm/
├── README.md                       # Top-level navigation. Quick start.
├── CITATION.cff                    # How to cite this work.
├── LICENSE                         # MIT or equivalent.
├── CONTRIBUTING.md                 # Development workflow.
├── CHANGELOG.md                    # Versioned changes.
│
├── docs/
│   ├── technical_manual.md         # The unified technical manual.
│   ├── scientific_framework.md     # Synthesis of the working paper §1+§2.
│   ├── architecture.md             # System architecture (this doc's §3).
│   ├── data_inventory.md           # All input/output data files documented.
│   ├── operating_manual.md         # Workstation + cluster run recipes.
│   ├── troubleshooting.md          # Known issues, common errors, fixes.
│   ├── glossary.md                 # Variable names, file formats, etc.
│   └── components/                 # Per-component deep dives (lifted from _phase2_findings/).
│       ├── lpjguess.md
│       ├── imogen_fortran.md
│       ├── intermediary_py.md
│       ├── patterns_and_regrid.md
│       └── ...
│
├── paper/                          # The peer-reviewed publication.
│   ├── manuscript_draft.docx       # Working paper (the scientific source-of-truth).
│   ├── figures/                    # Plots produced for the paper.
│   └── references/                 # Cited peer-reviewed PDFs (deduplicated).
│
├── lpjguess/                       # LPJ-GUESS LandSyMM fork.
│   ├── CMakeLists.txt
│   ├── framework/                  # Core C++ framework.
│   ├── modules/                    # Includes imogen_input.cpp, imogencfx.cpp, climatemodel.cpp, intermediary.cpp, imogenlogger.cpp.
│   ├── libraries/                  # gutil, plib, guessnc.
│   ├── command_line_version/main.cpp
│   ├── data/
│   │   └── ins/integrated-4.1-ins/ # The reference ins files.
│   ├── tests/                      # CATCH unit tests (upstream).
│   └── reference/                  # guessdoc.pdf, scientific_description.pdf.
│
├── imogen/                         # Fortran IMOGEN.
│   ├── code/
│   │   ├── imogen_lpjg.f           # Fixed for Linux (no PAUSE, no Windows mkdir).
│   │   ├── nonco2.f
│   │   ├── Makefile
│   │   ├── imogen_settings.txt     # Relative-paths default.
│   │   └── imogen_settings_tmpl.txt
│   ├── patterns/                   # 35 GCM dirs (34 CMIP5 + 5 pseudo-CMIP5 from CMIP6 conversion).
│   │   ├── CEN_*_MOD_*/            # Original CMIP5 (34).
│   │   ├── CEN_CMIP6_MOD_*/        # Converted CMIP6 NetCDF → ASCII (5; output of §12.4 step 1).
│   │   └── CMIP6_IMOGEN_EBM_values_and_patterns/  # Original NetCDF + JSON, retained for native-NetCDF future.
│   ├── CRUNCEP_1960_1989/          # Base climatology (30 years × 12 months × 1631 cells).
│   ├── docs/
│   │   ├── huntingford_and_cox_00.pdf
│   │   └── huntingford_et_al_10.pdf
│   └── R_wrappers/                 # Standalone-IMOGEN driver scripts.
│
├── intermediary_py/                # Python Intermediary Controller.
│   ├── pyproject.toml
│   ├── requirements.txt            # With openpyxl added.
│   ├── run_all.py
│   ├── src/                        # Components A/B/C/D + shared.
│   ├── tests/                      # 3 pytest files (extended over time).
│   ├── docs/                       # Python-specific docs (synthesised, deduplicated).
│   ├── inputs/                     # README.md + acquisition instructions; data not committed.
│   └── outputs/                    # Gitignored; populated at runtime.
│
├── tools/                          # Cross-component tooling.
│   ├── imogen_inputs_to_lpjg_format.py   # Adapter (§12.3).
│   ├── cmip6_nc_to_cmip5_ascii.py        # CMIP6 NetCDF → CMIP5 ASCII (§12.4).
│   ├── fast_regrid/                # Cleaned-up regrid utility (CMake, OpenMP, Linux).
│   └── ndep_archive/               # Cleaned-up NdepFastArchive (CMake, Linux).
│
├── runs/                           # Run setups for each scenario.
│   ├── SSP1-2.6/
│   │   ├── main.ins
│   │   ├── imogen_intermediary.ins
│   │   ├── crop.ins, crop_n.ins, ...
│   │   ├── gridlist_in_62892_and_climate.txt
│   │   └── inputs/                 # Adapter outputs land here.
│   ├── SSP2-4.5/
│   ├── SSP3-7.0/
│   ├── SSP4-6.0/
│   └── SSP5-8.5/
│
├── data/                           # Reference data (small files only; see DATA.md for large data acquisition).
│   ├── DATA.md                     # Where to obtain the large data: HILDA+, PLUMv2, FAO, RCMIP, FAIR, EDGAR, IIASA.
│   ├── soil/
│   │   └── soilmap_center_interpolated.remapv10_old_62892_gL.dat
│   ├── gridlist/                   # All gridlists.
│   ├── concentrations/             # IPCC and IIASA concentration files.
│   ├── emissions/                  # IIASA reference emissions.
│   ├── ndep/                       # Lamarque archives.
│   └── lu/                         # Land-use forcing (gitignored if too big; see DATA.md).
│
├── scripts/                        # Top-level orchestration.
│   ├── run_coupled.sh              # Workstation launcher.
│   ├── run_coupled.sbatch          # Cluster SLURM template.
│   └── smoke_test.sh               # 3-cell × 3-year coupled run.
│
├── ci/                             # CI/CD configuration.
│   ├── .github/workflows/ci.yml    # GitHub Actions.
│   └── .gitlab-ci.yml              # GitLab CI mirror.
│
└── archive/                        # Frozen legacy code.
    ├── imogen_cxx/                 # IMOGENCXX kept for reference (Subagent 4 report).
    ├── imogen_controller/          # Imogen-controller kept for reference.
    ├── intermediary_cpp/           # C++ Intermediary kept for reference.
    ├── matlab_plot_scripts/        # Old IIASA-CMIP6 plotters.
    ├── colab_notebook/             # Python plot notebook.
    └── references/                 # OUTDATED docs (Imogen_paper_GMD.docx, etc.).
```

Each top-level dir would have its own `README.md` linking back to the
relevant `docs/components/*.md`. The total tree is much smaller than
the current 18 GB / 16 GB versions because the large run-output data
has been moved out of git into `DATA.md`-pointed external archives.

---

## 14. Appendices

### A.1 Subagent reports — full evidence base

The eight subagent reports are the canonical evidence for every claim
in this document. They live at:

| # | Report | Path | Size | Lines |
|---|---|---|---|---|
| 1 | Documentation inventory | `_phase2_findings/01_documentation_inventory.md` | 86 KB | 1 354 |
| 2 | LPJ-GUESS `trunk_r13078` | `_phase2_findings/02_lpjguess_trunk_r13078.md` | 58 KB | 777 |
| 3 | IMOGEN Fortran | `_phase2_findings/03_imogen_fortran.md` | 47 KB | 629 |
| 4 | IMOGEN C++ refactor | `_phase2_findings/04_imogen_cxx.md` | 41 KB | n/a |
| 5 | C++ Intermediary | `_phase2_findings/05_intermediary_cpp.md` | 55 KB | n/a |
| 6 | Python Intermediary | `_phase2_findings/06_intermediary_py.md` | 56 KB | 1 022 |
| 7 | GCM patterns + regrid | `_phase2_findings/07_patterns_and_regrid.md` | 30 KB | 391 |
| 8 | Run setups + Data/ | `_phase2_findings/08_orchestration_and_data.md` | 38 KB | 741 |
| **Total** |  |  | **414 KB** | **6 507** |

### A.2 The 41 IMOGEN settings keys (Fortran `SETTIN`)

| # | Label | Type | Default | Controls |
|---:|---|---|---|---|
| 1 | `DIR_PATT` | path | `$IMOGENPATH/patterns/$IMOGENPATTERN/` | GCM pattern dir |
| 2 | `DIR_CLIM` | path | `$IMOGENPATH/CRUNCEP_1960_1989` | Base-climatology dir |
| 3 | `DIR_COMMON` | path | `$WORKPATH` | Root for handshake & per-year output |
| 4 | `FILE_SCEN_EMITS` | path | `…/emiss/$IMOGENEMISSIONS` | Anthropogenic CO2 emissions time series |
| 5 | `FILE_NON_CO2_VALS` | path | `…/emiss/$IMOGENRFNONCO2` | Prescribed non-CO2 RF time series |
| 6 | `FILE_CH4_N2O_EMITS` | path | `…/emiss/$IMOGENEMISSCH4N2O` | Anthropogenic CH4/N2O emissions (FAIR) |
| 7 | `FILE_LPJG_FLUX` | path | `imogen_lpjg_flux.txt` | LPJG-supplied land C flux file |
| 8 | `FILE_LPJG_CH4_N2O_FLUX` | path | `imogen_lpjg_ch4_n2o_flux.txt` | LPJG-supplied CH4/N2O flux file |
| 9 | `FILE_SCEN_CO2_PPMV` | path | `$CO2CONCFILE` | Prescribed CO2 ppmv (only when `C_EMISSIONS=F`) |
| 10 | `FILE_GRIDLIST` | path | (active: `gridlist_hurtt_RNDM_midpoint_3698.txt`) | Output gridlist for `REGRID_CLIM` |
| 11 | `STEP_DAY` | INTEGER | 1 | Sub-daily timesteps (`NSDMAX` upper bound) |
| 12 | `T_OCEAN_INIT` | REAL | 289.28 | Initial ocean SST (K) |
| 13 | `KAPPA_O` | REAL | 280.0 | Ocean eddy diffusivity (W/m/K) |
| 14 | `F_OCEAN` | REAL | 0.71 | Fractional ocean coverage |
| 15 | `LAMBDA_L` | REAL | 0.4 | Inverse climate sensitivity over land (W/m²/K) |
| 16 | `LAMBDA_O` | REAL | 1.9 | Inverse climate sensitivity over ocean (W/m²/K) |
| 17 | `MU` | REAL | 1.78 | Land/ocean ΔT amplification ratio |
| 18 | `Q2CO2` | REAL | 3.74 | RF for CO2 doubling (W/m²) |
| 19 | `TAU_DECAY_CH4` | REAL | 9.3 | CH4 atmospheric lifetime (yr) |
| 20 | `TAU_DECAY_N2O` | REAL | 121 | N2O atmospheric lifetime (yr) |
| 21 | `FILE_NON_CO2` | LOGICAL | T | Read non-CO2 RF from file (vs hardcoded HadCM3) |
| 22 | `NYR_NON_CO2` | INTEGER | 251 | # years in `FILE_NON_CO2_VALS` (max 300) |
| 23 | `NONCO2_EMISSIONS` | LOGICAL | T | Use FAIR for CH4/N2O forcing |
| 24 | `NONCO2_EMISSIONS_LPJG` | LOGICAL | T | Add LPJG-supplied natural CH4/N2O fluxes |
| 25 | `CO2_INIT_PPMV` | REAL | 286.085 (active) | Initial CO2 (ppmv); FAIR/RADF_CO2 reference |
| 26 | `CH4_INIT_PPBV` | REAL | 865.0 | Initial CH4 (ppbv) |
| 27 | `N2O_INIT_PPBV` | REAL | 277.4 | Initial N2O (ppbv) |
| 28 | `NYR_EMISS_NONCO2` | INTEGER | 251 | # years in `FILE_CH4_N2O_EMITS` |
| 29 | `NYR_EMISS` | INTEGER | 251 | # years in `FILE_SCEN_EMITS` |
| 30 | `NYR_LPJG_FLUX` | INTEGER | 251 (active) | # years per call in LPJG flux file |
| 31 | `C_EMISSIONS` | LOGICAL | T | T → CO2 ppmv from emissions; F → from `FILE_SCEN_CO2_PPMV` |
| 32 | `LPJG_CFLUX` | LOGICAL | F (active) | Take land C flux from LPJG instead of internal |
| 33 | `INCLUDE_CO2` | LOGICAL | T | Allow CO2 to update RF |
| 34 | `INCLUDE_NON_CO2` | LOGICAL | T | Allow non-CO2 to update RF |
| 35 | `DAILYOUT` | LOGICAL | F | Write daily (vs monthly) climate output |
| 36 | `LAND_FEED` | LOGICAL | T | Apply land-CO2 feedback |
| 37 | `OCEAN_FEED` | LOGICAL | T | Apply Joos ocean uptake |
| 38 | `ANLG` | LOGICAL | T | Use the GCM analogue model |
| 39 | `ANOM` | LOGICAL | T | Apply anomalies (vs base climatology only) |
| 40 | `REGRID` | LOGICAL | T | Run NN regrid via `REGRID_CLIM` |
| 41 | `CO2_RF_FAIR` | LOGICAL | F | Use FAIR's CO2 RF formula (overwrites `Q_CO2`) |

`SETTIN_LPJG` (per-call settings from LPJ-GUESS) reads 6 keys:
`YEAR1`, `IYEND`, `YEAR1_LPJG`, `SPINUP`, `KEEPRUNNING`, `FIRSTCALL`.

### A.3 The IPCC Tier-1 emission factors implemented

| Implementation | Equation | Status |
|---|---|---|
| C++ Intermediary `Calculator::calcCH4EntericFermentation` | V4 Ch10 Eq 10.19 (Updated): `E_T = N_{T,P} · EF_{T,P} / 10⁶` (Gg CH4/yr) | ✅ |
| C++ Intermediary `calcCH4ManureManagement` | V4 Ch10 Eq 10.22 (Updated): `CH4_mm = Σ_{T,S,P} N · VS · AWMS · EF / 1000` | ✅ |
| C++ Intermediary `calcVolalileSolidExcretion` | V4 Ch10 Eq 10.22a (Updated): annual VS rate per animal | ✅ |
| C++ Intermediary `calcN20ManureManagement` | V4 Ch10 Eq 10.25 (Updated, direct only): `N2O_D(mm) = Σ_S [Σ_{T,P} (N · Nex · AWMS_{T,S,P}) + Ncdg_S] · EF3_S · 44/28`. **Indirect (Eq 10.26-10.29) NOT modelled.** | ⚙️ partial |
| C++ Intermediary `calcN2OManagedSoils(FSN_FON, EF1=0.01, …)` | V4 Ch11 Eq 11.1: only N-inputs first sub-term `(F_SN+F_ON+F_CR+F_SOM) · EF1`. Other terms (`EF1FR` flooded rice, `F_OS · EF2` organic soils, `F_PRP · EF3` grazing) NOT used. | ⚙️ partial |
| C++ Intermediary `calcCH4Wetlands` | Wetlands Suppl. Appendix 3 Eq 3A.1: `CH4_emiss_WW_flood = P · E(CH4)_diff · A_flood · 10⁻⁶` (Gg CH4/yr). Tier 1 only — bubble Eq 3A.2 NOT modelled, DOC pathway NOT modelled. | ✅ |
| Python Intermediary `historical/ch4_ef_processing.py` | Same V4 Ch10 Eq 10.19 | ✅ |
| Python Intermediary `historical/ch4_mm_processing.py` | Same V4 Ch10 Eq 10.22 | ✅ |
| Python Intermediary `historical/ch4_rice_processing.py` | V4 Ch5 (Cropland): rice CH4 from harvested area + scaling factors | ✅ |
| Python Intermediary `historical/n2o_mm_processing.py` | Same V4 Ch10 Eq 10.25 | ✅ |
| Python Intermediary `historical/n2o_ms_processing.py` | Same V4 Ch11 Eq 11.1 | ✅ |
| Python Intermediary `historical/n2o_synfert_processing.py` | V4 Ch11 (Soils): synthetic-fertiliser N2O via the EDGAR-OLD 4D11 sub-category | ✅ |

Not covered in either C++ or Python:
- AFOLU-CO2 Tier-1 inventory (LPJ-GUESS provides natural+LULC CO2;
  fossil/industrial from RCMIP/IIASA).
- Indirect N2O (Eq 10.26-10.29 leaching/volatilisation; Ch11 EF4/EF5).
- Biomass burning CH4/N2O (would need GFED).
- Industrial CH4/N2O fugitives (left to RCMIP non-agri).

### A.4 The 34 CMIP5 GCM pattern dirs

In `Common-directory/IMOGEN-codebase/patterns/`:

| Centre (CEN) | Model (MOD) | Country | Notes |
|---|---|---|---|
| BCC | bcc-csm1-1 | China | |
| BCC | bcc-csm1-1-m | China | medium-res sibling |
| BNU | BNU-ESM | China | |
| CCCma | CanESM2 | Canada | |
| CMCC | CMCC-CMS | Italy | |
| CNRM-CERFACS | CNRM-CM5 | France | |
| CSIRO-BOM | ACCESS1-0 | Australia | |
| CSIRO-BOM | ACCESS1-3 | Australia | |
| CSIRO-QCCCE | CSIRO-Mk3-6-0 | Australia | |
| INM | inmcm4 | Russia | |
| IPSL | IPSL-CM5A-LR | France | low-res |
| IPSL | IPSL-CM5A-MR | France | mid-res; **active default in `imogen_settings.txt`** |
| IPSL | IPSL-CM5B-LR | France | |
| MIROC | MIROC-ESM | Japan | Earth-system |
| MIROC | MIROC-ESM-CHEM | Japan | + atmos chem |
| MIROC | MIROC5 | Japan | |
| MOHC | HadGEM2-CC | UK | carbon-cycle version |
| MOHC | HadGEM2-ES | UK | Earth-system |
| MPI-M | MPI-ESM-LR | Germany | low-res |
| MPI-M | MPI-ESM-MR | Germany | mid-res |
| MRI | MRI-CGCM3 | Japan | |
| NASA-GISS | GISS-E2-H | USA | HYCOM ocean |
| NASA-GISS | GISS-E2-H-CC | USA | + carbon-cycle |
| NASA-GISS | GISS-E2-R | USA | Russell ocean |
| NASA-GISS | GISS-E2-R-CC | USA | + CC |
| NCAR | CCSM4 | USA | |
| NCC | NorESM1-M | Norway | |
| NCC | NorESM1-ME | Norway | + BGC |
| NOAA-GFDL | GFDL-CM3 | USA | |
| NOAA-GFDL | GFDL-ESM2G | USA | isopycnal ocean |
| NOAA-GFDL | GFDL-ESM2M | USA | MOM ocean |
| NSF-DOE-NCAR | CESM1-BGC | USA | |
| NSF-DOE-NCAR | CESM1-CAM5 | USA | |
| NSF-DOE-NCAR | CESM1-WACCM | USA | whole-atmos chem |
| (CMIP3 legacy) | HadCM3 | UK | `ukmo_hadcm3_rel/` — relative-to-baseline; original Zelazowski/Huntingford pattern |

CMIP6 NetCDF set in `CMIP6_IMOGEN_EBM_values_and_patterns/`:
GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL.
**MRI-ESM2-0 is the working paper's chosen GCM** — adopting CMIP6
(via the conversion of §12.4) is required for the canonical run.

### A.5 The 5 SSP-RCP scenarios

| SSP | RCP | Working paper inclusion | C++ Intermediary | Python Intermediary | Realised on disk |
|---|---|:---:|:---:|:---:|:---:|
| SSP1 | RCP2.6 | ✅ (primary) | ✅ | ✅ | ✅ (only) |
| SSP2 | RCP4.5 | ✅ (primary) | – (CMIP5 config has SSP1+5 only) | ✅ | – |
| SSP3 | RCP7.0 | – | – | ✅ | – |
| SSP4 | RCP6.0 | – | – | ✅ | – |
| SSP5 | RCP8.5 | – (was in the older paper) | ✅ (CMIP5) | ✅ | – |

The working paper's evaluation is on SSP1+SSP2 only, but the Python
pipeline retains capability for all 5 — useful for sensitivity studies.

### A.6 The on-disk evidence summary

The audit's strongest single piece of evidence for the
"system-not-yet-coupled-functional" verdict is the contents of three
small files in `A/Common-directory/LPJG_main/IMOGEN/`:

```
$ cat imogen_lpjg.txt
YEAR1 1871 !IN First year of the numerical experiment
IYEND 1871 !IN Stop year of the ENTIRE run
YEAR1_LPJG 1871 !IN First year of the whole LPJ-GUESS simulation
SPINUP TRUE	!IN Are we in the spin-up phase of LPJ-GUESS?
KEEPRUNNING TRUE	!IN control flag to keep imogen running
FIRSTCALL TRUE !IN Is this the very first call to IMOGEN from LPJ-GUESS (start of spin-up)?

$ cat imogen_lpjg_flux.txt
2100	0.00

$ cat imogen_lpjg_ch4_n2o_flux.txt
2100	202	9.1
```

The `imogen_lpjg.txt` is hand-set to spin-up state (year 1871). The
flux files contain *single-line placeholders* with year `2100` and
token values. **In a real coupled run, the flux files would carry one
line per simulated year (251 lines for 1850-2100 or fewer per call).**
Their current state proves no coupled LPJ-GUESS run has populated them.

### A.7 Verification checklist for the unified codebase

Before tagging `v1.0`, confirm:

| # | Check | Method |
|---:|---|---|
| 1 | LPJ-GUESS builds with default flags on Ubuntu 22.04 / 24.04 | `cmake .. && make` in CI |
| 2 | Fortran IMOGEN builds with gfortran | `make` in `imogen/code/` |
| 3 | Python Intermediary venv installs cleanly | `pip install -r requirements.txt` |
| 4 | All 3 pytest tests pass | `pytest intermediary_py/tests/` |
| 5 | Smoke coupled run completes | `./scripts/smoke_test.sh` |
| 6 | One full SSP1-2.6 scenario coupled run completes | `./scripts/run_coupled.sh SSP1-2.6` |
| 7 | Output `cflux.out`, `mch4.out`, `ngases.out` produced | check `runs/SSP1-2.6/output*` |
| 8 | Concentration trajectory in `CO2_all.dat` matches RCMIP within 5 ppm | post-run analysis |
| 9 | CMIP6 GCM (MRI-ESM2-0) selectable via single-line edit | edit `imogen_settings.txt` `DIR_PATT` |
| 10 | Cluster batch template runs on the user's HPC | submit `run_coupled.sbatch` |
| 11 | All 7 break-points of §1.2 demonstrably fixed | code-level review |
| 12 | CI passes on every commit | GitHub Actions / GitLab CI green |
| 13 | Documentation builds without dead links | `mdbook build docs/` or equivalent |
| 14 | Reference outputs reproducible (md5 or pandas tolerance) | `make verify` |

### A.8 References to all 8 subagent reports

The following sections are referenced in this document. For full
context, read the corresponding subagent report.

- **§1, §3, §4.1** ↔ Subagent 2 (`02_lpjguess_trunk_r13078.md`): all
  LPJ-GUESS / `trunk_r13078` content, including the `exit(200)` bug,
  the polling loop, the input modules, the IMOGENConfig namespace,
  the `MiscOutput` stubs, the diff vs the standalone LandSyMM fork.
- **§4.2** ↔ Subagent 3 (`03_imogen_fortran.md`): all Fortran IMOGEN
  content, including the 17-subroutine catalogue, the year-loop, the
  41 settings keys, the pattern-scaling, the `done`-file protocol,
  the gridlist limitations, the bug list including the `PAUSE`.
- **§4.3, §4.4** ↔ Subagent 4 (`04_imogen_cxx.md`): all C++ IMOGEN
  refactor + Imogen-controller content, including the 25 bugs, the
  empty-DAY_CALC stub, the gridlist non-claim, the polarity-inverted
  done file.
- **§4.5** ↔ Subagent 5 (`05_intermediary_cpp.md`): all C++
  Intermediary content, including the 7-formula IPCC tier-1 coverage,
  the dead Adder, the A vs B diff, the `calcNitrogenExcretion` bug.
- **§4.6** ↔ Subagent 6 (`06_intermediary_py.md`): all Python
  Intermediary content, including the 4-component pipeline, the
  43 ordered steps, the 3 pytest tests, the substitution roadmap, the
  `openpyxl` missing dep.
- **§4.7** ↔ Subagent 7 (`07_patterns_and_regrid.md`): all GCM
  pattern + regrid utility content, including the 36-dir inventory,
  the CMIP6 NetCDF format, the 3-utility comparison, the case-sensitivity
  Linux-build bug.
- **§5, §6, §10** ↔ Subagent 8 (`08_orchestration_and_data.md`): all
  Data/ + run-setup content, including the 33-file SSP1_RCP26 dir, the
  A/B `imogen_intermediary.ins` divergence, the missing
  `setup_run_owl_*` helper, the `ouput` typo, the `IMOGEN/output/` 230
  year dirs.
- **§2, §7, §9** ↔ Subagent 1 (`01_documentation_inventory.md`): all
  documentation-related content, including the source-of-truth
  ranking, the 11 contradictions, the retirement plan.

Two-letter cross-reference codes used in this document:
- `[SAn §x.y]` → Subagent n's section x.y.
- `[SAn §x.y, item z]` → Subagent n's section x.y, table/list item z.

---

*End of master investigation document.*

*Investigators: Subagents 1-8 of Phase 2 (read-only); synthesis and
re-investigation of loose ends by master agent of Phase 3.*

*Total evidence base: 414 KB / 6 507 lines across 8 subagent reports
plus this synthesis (`COUPLED_MODEL_INVESTIGATION.md`).*

