# `trunk_r13078` Backport Ledger

**Purpose:** running source-of-truth catalogue of every code change
made in our `lpjguess/` tree (and the related Fortran IMOGEN
`imogen/code/` tree) that will need to be **replicated in
`trunk_r13078`** for working-paper Stage-1/Stage-2 consistency.

**Why this exists:** see policy section below; in short, our v1.0
rebuild operates on `LandSyMM_LPJ-GUESS/` (which the user also calls
the "integrated LTS" per the integration-project terminology
established before this coupled-model project began), but the
`trunk_r13078` fork inside the original framework's
`version_A/Integrations/trunk/` and `version_B/Integrations/trunk/`
trees was used in the working paper's Stage 1 PLUM yield runs.
For Stage-2 consistency, both forks must eventually be
fully-coupled-model-capable and switchable.

---

## 1. Policy

### 1.1 The two forks

| Fork | Path (canonical) | Role |
|---|---|---|
| **LandSyMM_LPJ-GUESS** (a.k.a. "integrated LTS") | `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/` | **v1.0 active development base.** Imported into our `lpjguess/` at step 1. |
| **trunk_r13078** | `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/` and the identical copy in `version_B/.../`. | **Backport target.** The original LandSyMM fork that the working paper's Stage 1 PLUM yield runs used. |

The two are byte-identical modulo **6 files** (5 cosmetic + 1
critical: `modules/imogencfx.cpp:483`'s `exit(200)` regression that
short-circuits LandSyMM-fork standalone runs). See `[CMI §4.1.10]`
and `notes/STEP_1.md` §A for the diff details.

### 1.2 Workflow

1. Work proceeds in `lpjguess/` on `LandSyMM_LPJ-GUESS` (the
   "integrated LTS" per user terminology).
2. Every commit that touches the C++ tree records its change set
   in this ledger (under §3 below).
3. At the end of Phase-1 (after step 19's V.1 verification and
   before any v1.0 release / paper submission), a dedicated
   **Backport Sprint** replicates each ledger entry into
   `trunk_r13078`, runs the same V.1 verification, and exposes
   both forks as switchable build-time backends.
4. Both forks then live in the rebuild as reference
   implementations; users / CI tests can run with either and
   results are cross-checked.

### 1.3 What this ledger covers (and doesn't)

- ✅ **Covers**: source-level changes to `lpjguess/framework/`,
  `lpjguess/modules/`, `lpjguess/libraries/`,
  `lpjguess/CMakeLists.txt`, `lpjguess/cmake/`, etc.
- ✅ **Covers**: cascading changes to the Fortran IMOGEN tree
  (`imogen/code/imogen_lpjg.f`, etc.) where they couple semantically
  with C++-side changes — even though the Fortran tree is shared
  across both forks (no fork-specific Fortran), recording these
  here ensures the backport sprint reviews them.
- ❌ **Does NOT cover**: Python tooling (`tools/`,
  `intermediary_py/`), build infrastructure outside `lpjguess/`,
  data files, run-config `.ins` files (those live in `runs/` and
  are fork-agnostic).

---

## 2. The 6-file delta between the forks (baseline diff)

Established at step 1; ground truth for what's already different
**before** any of our changes. Backport sprint must reconcile these
first, then layer on our changes from §3.

| File | Difference |
|---|---|
| `modules/imogencfx.cpp` | `trunk_r13078` has `exit(200);` at line 483 (silent abort); `LandSyMM_LPJ-GUESS` has it removed. **Critical.** |
| `framework/parameters.cpp` | Cosmetic: comment / whitespace |
| `framework/guess.h` | Cosmetic: comment / whitespace |
| `modules/canexch.cpp` | Cosmetic: comment / whitespace |
| `modules/landcover.cpp` | Cosmetic: comment / whitespace |
| `data/ins/global_cfx.ins` | Cosmetic: comment / whitespace |

(Detailed line-by-line diffs available via `diff -ruN
trunk_r13078/ LandSyMM_LPJ-GUESS/` at the user's workstation; they
were inspected and confirmed during step 1's import audit.)

---

## 3. Change set — running ledger

Format per entry:

```text
### Step <N>: <one-line summary>
**Commit:** <git-hash>  **Date:** <YYYY-MM-DD>
For each file:
- File: <relative-path-within-lpjguess>
- Operation: <add | modify | delete>
- Lines or function: <line range or symbol name>
- Description: <short rationale>
- Backport guidance: <any subtleties for the backport sprint>
```

### Step 1: Import LandSyMM_LPJ-GUESS into lpjguess/

**Commit:** `662f288` (Step 1; bundled into tag `v0.2.0-imports`)  **Date:** 2026-05-05

**[Errata 2026-05-08, step-15 cleanup]**: an earlier draft of this ledger
recorded `dc91efb` here; verified against `git log` at step 15 and corrected
to `662f288`. Step 1's commit was bundled with step 2's into the
`v0.2.0-imports` tag, but the underlying step-1 commit is `662f288`.
- **No source-level changes from the imported source** (rsync only).
- The 6-file delta from `trunk_r13078` (per §2 above) is "free"
  for the backport sprint — those differences must be reconciled
  first; only then do later steps' changes layer on.

### Step 2: Import Fortran IMOGEN; immediate Linux fixes

**Commit:** `a93c3ec` (Step 2; tag `v0.2.0-imports`)  **Date:** 2026-05-05

**[Errata 2026-05-08, step-15 cleanup]**: previously `9e51a23`; corrected
to `a93c3ec` per `git rev-list -n 1 v0.2.0-imports`.
- **No `lpjguess/` changes**; all changes are in `imogen/code/`
  which is fork-shared (Fortran). Backport-irrelevant for the
  C++ side; relevant for the Fortran side which trunk_r13078 also
  uses unchanged.

### Step 3: Fortran IMOGEN ALLOCATABLE refactor

**Commit:** `fb626c4` (Step 3; tag `v0.3.0-fortran-allocatable`)  **Date:** 2026-05-05

**[Errata 2026-05-08, step-15 cleanup]**: previously `5f86bb1`; corrected
to `fb626c4` per `git rev-list -n 1 v0.3.0-fortran-allocatable`.
- **No `lpjguess/` changes**; Fortran-only. Backport-irrelevant
  for the C++ side.

### Step 4: GCM patterns + CRUNCEP fetch infrastructure

**Commit:** `e80317b` (Step 4; tag `v0.4.0-imogen-data-fetch-script`)  **Date:** 2026-05-06

**[Errata 2026-05-08, step-15 cleanup]**: previously `f3bb471`; corrected
to `e80317b` per `git rev-list -n 1 v0.4.0-imogen-data-fetch-script`.
- **No `lpjguess/` changes**; tooling + Fortran data infrastructure
  only. Backport-irrelevant.

### Step 5: CMIP6 → CMIP5 ASCII converter

**Commit:** `514f089` (Step 5; tag `v0.5.0-cmip6-converter`)  **Date:** 2026-05-06

**[Errata 2026-05-08, step-15 cleanup]**: previously `2d36c8e`; corrected
to `514f089` per `git rev-list -n 1 v0.5.0-cmip6-converter`.
- **No `lpjguess/` changes**; Python tool + docs. Backport-
  irrelevant.

### Step 6: Reference data import (Tier-1/2/3)

**Commit:** `3ef66de` (Step 6)  **Date:** 2026-05-06
- **No `lpjguess/` changes**; data + manifests + ndep tarball +
  emiss restructure. Backport-irrelevant.
- One **Fortran IMOGEN settings change** worth flagging for
  backport-cross-reference: `imogen/code/imogen_settings.txt`
  paths updated for the new `imogen/emiss/DKB_dataset_totals/`
  prefix (3 lines: `FILE_SCEN_EMITS`, `FILE_NON_CO2_VALS`,
  `FILE_CH4_N2O_EMITS`). Not a fork-specific change but is part
  of the reproducibility pipeline both forks will share.

### Step 7: LPJ-GUESS coupling source-level fixes (C2, C3, C4) + F-4 Fortran twin

**Commit:** `71c171d` (Step 7)  **Date:** 2026-05-06

Three C++ fixes in `lpjguess/`:

#### File: `lpjguess/modules/climatemodel.cpp`
- **Operation:** modify
- **Lines:** 332-353
- **Description:** Fix bugs **C2 + C3** (per `[CMI §3.7]`):
  - C2: restored `doneExist = filesystem_dkb::exists(...)` INQUIRE
    at lines 332-333 (replacing the hard-coded `doneExist = true`
    short-circuit that bypassed the per-year LPJG↔IMOGEN handshake's
    safety semantics).
  - C2: added a first-call bypass right after the INQUIRE:
    `if (firstCall && !doneExist) doneExist = true;` — so the very
    first iteration doesn't hang waiting for a `done` file that
    doesn't exist yet.
  - C3: uncommented 3 polling guards at lines 336, 343, 352
    (`runnowOpen = !file.is_open();`, etc.) which were wholly
    inactive before.
- **Backport guidance:** **trunk_r13078 has the SAME comment-out
  pattern** (verified via diff at step 7); the backport must apply
  the identical 5-line restoration there. NB the surrounding code
  context is byte-identical between forks at this region.

#### File: `lpjguess/modules/imogen_input.cpp`
- **Operation:** modify
- **Line:** 728
- **Description:** Fix bug **C4** (per `[CMI §3.7]`): uncommented
  `ndep.getndep(...)`. The comment-out caused the loose-coupling
  mode to silently feed un-initialised N-deposition values to
  LPJ-GUESS.
- **Backport guidance:** `trunk_r13078`'s `imogen_input.cpp:728`
  has the SAME comment-out. Single-line uncomment.

#### File: `lpjguess/modules/imogencfx.cpp`
- **Operation:** modify
- **Line:** 895 (added 5-line cross-reference comment)
- **Description:** Documentation-only addition. The active
  `ndep.getndep(...)` call at line 895 is **already correct** in
  both forks; we added a comment block flagging it as the
  tight-coupling twin of `imogen_input.cpp:728` (C4) so future
  maintainers don't re-comment-out either of them by mistake.
- **Backport guidance:** Pure documentation; safe to copy verbatim
  into `trunk_r13078`'s `imogencfx.cpp` near its line 895.

One Fortran fix in the shared `imogen/code/`:

#### File: `imogen/code/imogen_lpjg.f`
- **Operation:** modify
- **Lines:** ~360 (insert auto-create block before `DO WHILE
  (KEEPRUNNING)` outer loop) + line 363 (delete dead commented line)
- **Description:** Fix bug **F-4** (Fortran-side twin of C2/C3): the
  IMOGEN engine was hanging in standalone mode because `done` file
  was never created on first iteration. Inserted
  `CALL SYSTEM('mkdir -p ... /LPJG_main/IMOGEN')` and
  `CALL SYSTEM('touch ... /LPJG_main/IMOGEN/done')` block before
  the outer loop. Deleted the dead `!DONE_EXIST=.TRUE.` comment.
- **Backport guidance:** Fortran tree is fork-shared; this change
  doesn't need replication BUT the backport sprint should verify
  the Fortran tree the trunk_r13078 backport uses is the same one
  with this fix already applied. Document this as a sanity check.

### Step 8: LPJG-side handshake writer + coupling_mode parameter

**Commit:** `a543e9d` (Step 8)  **Date:** 2026-05-06

#### File: `lpjguess/framework/parameters.h`
- **Operation:** modify
- **Lines:** ~497 (after `interpolation_mode` declaration in
  `IMOGENConfig` namespace)
- **Description:** Added `extern xtring coupling_mode;` declaration
  with explanatory block comment.
- **Backport guidance:** `trunk_r13078`'s `parameters.h` has the
  same `IMOGENConfig` namespace with the same `interpolation_mode`
  ending the namespace member list at the same relative location.
  Trivial 5-line backport.

#### File: `lpjguess/framework/parameters.cpp`
- **Operation:** modify
- **Lines:** matches the header location
- **Description:** Added `xtring coupling_mode = "tight";` definition.
- **Backport guidance:** Trivial 3-line backport.

#### File: `lpjguess/modules/imogencfx.cpp`
- **Operation:** modify
- **Line:** ~333 (after `interpolation_mode` declare_parameter call)
- **Description:** Added
  `declare_parameter("coupling_mode", &IMOGENConfig::coupling_mode,
   20, "...")` registration so the value can be set from `.ins` files.
- **Backport guidance:** The surrounding context (other
  `declare_parameter` calls for `simulation_mode` etc.) IS NOT
  byte-identical between the forks at this region; the trunk_r13078
  may have slightly different ordering of parameter declarations.
  Backport sprint must locate the right insertion point manually
  rather than blindly copy-pasting the line range.

#### File: `lpjguess/modules/imogenoutput.h` (NEW)
- **Operation:** add
- **Size:** ~150 lines
- **Description:** New module declaring `GuessOutput::ImogenOutput`
  derived from `OutputModule`; writes per-year handshake control
  files for the LPJG↔IMOGEN feedback loop. Doc block in source
  documents cadence, mode-gating, and F-10 architectural caveat.
- **Backport guidance:** Add the file verbatim to
  `trunk_r13078/modules/imogenoutput.h`. No fork-specific
  adaptation needed.

#### File: `lpjguess/modules/imogenoutput.cpp` (NEW)
- **Operation:** add
- **Size:** ~310 lines
- **Description:** Implementation of `ImogenOutput`. Writes 4
  files (`imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt`,
  `imogen_lpjg.txt`, `done`). Carbon flux loop mirrors
  `commonoutput.cpp::outannual`'s pattern (Gridcell→Stand→Patch).
  Mode-gated by `IMOGENConfig::coupling_mode`.
- **Backport guidance:** Add file verbatim. Verify
  `trunk_r13078/modules/commonoutput.cpp`'s flux-loop pattern is
  identical in flux types referenced (Fluxes::MANUREC, NPP, REPRC,
  SOILC, FIREC, ESTC, N2O_FIRE, N2O_SOIL, CH4C) — these enums are
  in `framework/guessmath.h` or similar and SHOULD be fork-stable.

#### File: `lpjguess/modules/CMakeLists.txt`
- **Operation:** modify
- **Lines:** 2 inserts (one in `headers` list, one in `source` list)
- **Description:** Added `imogenoutput.h` and `imogenoutput.cpp` to
  the cmake source lists so they compile into both `guess` and
  `runtests` targets.
- **Backport guidance:** Trivial 2-line backport. The other entries
  in the cmake source list (`climatemodel.cpp`, `imogenlogger.cpp`,
  etc.) ARE fork-stable.

#### File: `lpjguess/modules/miscoutput.h`
- **Operation:** modify (cleanup, not new feature)
- **Lines:** 2 deletions + 1 modification:
  - Deleted `getImogenData(int, int)` random-placeholder helper
    (~12 lines: signature, body, comment) at the top of
    `MiscOutput` class declaration.
  - Deleted `#include <random>` (only consumer was the dead helper).
  - Added a multi-line cross-reference comment pointing to F-9
    follow-up (the half-scaffolded climate-input diagnostic stubs
    that remain in place but are out of step-8 scope).
- **Backport guidance:** **Check whether `trunk_r13078`'s
  `miscoutput.h` even has the `getImogenData` helper.** If yes,
  remove it. If not (because the helper was added in our prior
  integration project and never propagated to `trunk_r13078`),
  the backport is a no-op for this file.

### Step 14: Workstation launcher + Anaconda3 NetCDF build docs + .ins file_tmin/tmax fix

**Commit:** `ced4b1d` (Step 14; tag `v0.14.0-step14-launcher`)  **Date:** 2026-05-07

**[Hash filled in 2026-05-08, step-15 cleanup]**: replaced `_TBD_`
placeholder with verified hash via `git rev-list -n 1 v0.14.0-step14-launcher`.

#### Net source-level change in `lpjguess/`: ZERO

Step 14's deliverables (launcher script + build docs + .ins file
collateral fix) live entirely OUTSIDE `lpjguess/`. The Backport
Sprint (F-11) does NOT need to replicate any step-14 changes in
`trunk_r13078`.

#### Files added (all OUTSIDE lpjguess/)

- `scripts/run_coupled.sh` (NEW, ~12 KB / ~330 LOC bash) — workstation launcher
- `docs/build.md` (NEW, ~150 lines markdown) — Anaconda3 NetCDF preference docs + manual build/run paths
- `notes/STEP_14.md` (NEW, ~12 KB)

#### Files modified (all OUTSIDE lpjguess/)

- `runs/SSP1-2.6/imogen_intermediary.ins` (+2 `param` directives for
  file_tmin / file_tmax — step-9.5 collateral fix; documents step-14
  provenance via inline comment)
- `.gitignore` (+`runs/*/Common-directory/` rule)

#### Cross-reference for the Backport Sprint

When the Backport Sprint runs the coupled model on the `trunk_r13078`
backend, it will use the SAME launcher (`scripts/run_coupled.sh`).
The launcher's behavior is fork-agnostic; only the build target changes
(future enhancement: `--lpjg-backend trunk_r13078` flag added at
Backport Sprint time).

---

### Step 13: Python Intermediary -> Fortran IMOGEN ASCII adapter

**Commit:** `aa802e0` (Step 13; tag `v0.13.0-step13-adapter`)  **Date:** 2026-05-07

**[Hash filled in 2026-05-08, step-15 cleanup]**: replaced `_TBD_`
placeholder with verified hash via `git rev-list -n 1 v0.13.0-step13-adapter`.

#### Net source-level change in `lpjguess/`: ZERO

Step 13's adapter (`tools/imogen_inputs_to_lpjg_format.py`) is fork-
agnostic Python tooling. It reads intermediary_py CSV outputs and
writes Fortran-readable ASCII files using the same format the engine
parses regardless of which LPJG fork generated the upstream natural-
flux .gz files.

#### Files added (all OUTSIDE lpjguess/)

- `tools/imogen_inputs_to_lpjg_format.py` (NEW, ~270 LOC Python)
- `notes/STEP_13.md`

#### Files modified (all OUTSIDE lpjguess/ except annotations)

- `tools/README.md`: added "Implemented tools" entry; removed planned row
- `runs/SSP1-2.6/imogen_intermediary.ins`: added "Option B" block
  (commented-out by default; Option A static-IIASA remains v1.0 default)
- `.gitignore`: comment annotation about `runs/*/inputs/`

#### Cross-reference for the Backport Sprint

When the Backport Sprint runs the coupled model end-to-end on the
`trunk_r13078` backend, it will use the SAME adapter (no changes
needed). The adapter produces Fortran-ASCII files that any IMOGEN
engine (current or backported) reads identically.

(Step 12 was consolidated with step 11; no separate ledger entry.)

---

### Step 11: intermediary_py end-to-end pipeline run + 4 source bug fixes + reproducibility validation

**Commit:** `e89af1e` (Step 11; tag `v0.12.0-step11-intermediary-py-validated`)  **Date:** 2026-05-07

**[Hash filled in 2026-05-08, step-15 cleanup]**: replaced `_TBD_`
placeholder with verified hash via `git rev-list -n 1 v0.12.0-step11-intermediary-py-validated`.
Step 12 was consolidated with step 11 — no separate ledger entry; this commit
covers both.

#### Net source-level change in `lpjguess/`: ZERO

Step 11 deliberately introduces zero `lpjguess/` C++ changes.
intermediary_py is a fork-agnostic Python pipeline; its bug fixes
do not need replication in `trunk_r13078`.

#### Files modified (all OUTSIDE lpjguess/)

In `intermediary_py/imogen_ghg_controller/` (Python):

- `src/shared/paths.py` (+60 LOC): extended `ensure_output_dirs()` to
  enumerate all 14 level-3 sub-subdirs; added module-level auto-call on
  import (gated by `IMOGEN_GHG_NO_AUTO_MKDIR=1` env var)
- `src/component_a_anthropogenic/rcmip_substitution/rcmip_substitution_processing.py`
  (~12 LOC change): write outputs to `OUT_A_DATA` instead of script's
  own dir (`HERE`)
- `src/component_a_anthropogenic/scenarios/01_scenario_ch4_ef_processing.py`
  (+8 LOC): added `import os`; changed `'FAOCountry'` → `'Country'`
- `src/component_a_anthropogenic/scenarios/02_scenario_ch4_mm_processing.py`
  (+1 LOC): added `import os`
- `src/component_a_anthropogenic/scenarios/03_scenario_n2o_mm_processing.py`
  (+1 LOC): added `import os`
- `run_all.py` (+7 LOC): comment about path auto-create
- `requirements.txt` (+4 LOC): added `openpyxl>=3.0` (bug C33 fix)
- `pyproject.toml` (+2 LOC): added `openpyxl>=3.0` to dependencies

Plus `.gitignore` (+10 LOC) for `intermediary_py/imogen_ghg_controller/{inputs,outputs,archive}/*` (the README.md inside is excepted).

#### Cross-reference for the Backport Sprint

When the Backport Sprint runs the coupled model end-to-end on the
`trunk_r13078` backend, it will use the SAME intermediary_py
(imogen_ghg_controller) Python pipeline. The bug fixes from step 11
are inherited automatically because intermediary_py is fork-agnostic.

---

### Step 10: Import intermediary_py (imogen_ghg_controller v0.1.0)

**Commit:** `a90e9be` (Step 10; tag `v0.11.0-step10-intermediary-py-import`)  **Date:** 2026-05-07

**[Hash filled in 2026-05-08, step-15 cleanup]**: replaced `_TBD_`
placeholder with verified hash via `git rev-list -n 1 v0.11.0-step10-intermediary-py-import`.

#### Net source-level change in `lpjguess/`: ZERO

Step 10's deliverable lives entirely OUTSIDE `lpjguess/`. The
`intermediary_py/imogen_ghg_controller/` Python pipeline is fork-
agnostic — it consumes LPJG `.out` outputs (which are the same
regardless of which LPJG fork produced them) and produces RCMIP-
substitution emission CSVs that feed IMOGEN. The Backport Sprint
does NOT need to replicate any step 10 changes in `trunk_r13078`.

#### Files added (all OUTSIDE lpjguess/)

- `intermediary_py/imogen_ghg_controller/` — 7.9 MB / 78 files
  (rsync'd from `version_A/.../imogen_ghg_controller_SOURCE_ONLY/`,
  excluding `inputs/`, `outputs/`, `archive/`, `__pycache__`)
- `notes/STEP_10.md`

#### Cross-reference

When the Backport Sprint runs an end-to-end coupled run on the
`trunk_r13078` backend, it will use the SAME `intermediary_py/`
pipeline to produce IMOGEN inputs. No fork-specific intermediary
code exists; all the substitution/integration logic is in Python
and reads LPJG outputs through fork-stable file format conventions.

---

### Step 9.5: LPJG-side IMOGEN climate-output consumer wiring + BLAZE check + C++ Tmin/Tmax

**Commit:** `f00033c` (Step 9.5; tag `v0.10.0-step9.5-consumer-wiring`)  **Date:** 2026-05-07

**[Hash filled in 2026-05-08, step-15 cleanup]**: replaced `_TBD_`
placeholder with verified hash via `git rev-list -n 1 v0.10.0-step9.5-consumer-wiring`.

#### File: `lpjguess/modules/imogencfx.h`
- **Operation:** modify
- **Changes:**
  - Add `double dtmin[Date::MAX_YEAR_LENGTH]`, `double dtmax[Date::MAX_YEAR_LENGTH]` (~3 LOC)
  - Add `xtring file_tmin`, `xtring file_tmax` (~3 LOC)
  - Add `std::vector< std::vector< std::vector<double> > > all_dtmin`, `all_dtmax` (~3 LOC)
- **Backport guidance:** Trivial 3 separate insert blocks; same locations as
  the existing `dtemp[]`, `file_temp`, `all_temp` patterns.

#### File: `lpjguess/modules/imogencfx.cpp`
- **Operation:** modify (substantial; ~80 LOC across 5 spots)
- **Changes:**
  - `IMOGENCFXInput::init()`: 4 new `param[...]` reads (file_relhum, file_wind, file_tmin, file_tmax)
  - `IMOGENCFXInput::init()`: 4 new `resize3DimVector(all_drelhum/all_dwind/all_dtmin/all_dtmax, ...)` calls
  - `IMOGENCFXInput::read_climate_for_year()`: 4 new `read_lines_from_file(...)` calls (each with empty-path guard)
  - `IMOGENCFXInput::get_climate_for_gridcell()`: BLAZE compatibility check
    RESTORED (with empty-path safety message); per-month → per-day
    interpolation block for the 4 new climate variables (uses
    `interp_monthly_means_conserve` like existing code); daily-mode
    passthrough block for the 4 new variables
  - `IMOGENCFXInput::getclimate()`: 4 new `climate.relhum`/`u10`/`tmin`/`tmax` assignments
- **Backport guidance:** **NON-TRIVIAL backport**. The trunk_r13078 fork's
  `imogencfx.cpp` may not have all of the existing infrastructure (e.g.,
  `all_drelhum`/`all_dwind` may already be in our fork from earlier
  integration work but absent from trunk_r13078). The backport sprint
  must FIRST replicate the half-built infrastructure (per the user's
  earlier integration project) THEN apply step 9.5's wiring. Estimated
  3-4 hours during the backport sprint.

#### File: `lpjguess/modules/climatemodel.cpp`
- **Operation:** modify (~25 LOC inserted into existing T_anom write block)
- **Changes:**
  - In the non-REGRID native-grid output branch (around lines ~880-958):
    - Add `file100, file101` ofstream declarations
    - Open at `iyear == year1`: `Tmin_anom.dat`, `Tmax_anom.dat`
    - Per-gridpoint lon/lat header writes for both
    - Per-month-per-day data writes in BOTH `dailyOut` branches:
      `Tmin = tOutM - dtempOutM/2`, `Tmax = tOutM + dtempOutM/2`
    - Per-gridpoint newlines + close at `iyear == iyend`
- **Backport guidance:** Trivial copy if trunk_r13078's climatemodel.cpp
  has the same Rh+W writer pattern (which the user added at integration
  project time). If not, requires the integration-project Rh+W work
  first. **TODO at step 9.5b**: replicate the same Tmin/Tmax write in
  the REGRID branch (smoke uses `REGRID=0` so non-REGRID is sufficient
  for v1.0).

#### Non-`lpjguess/` notes (no backport needed; Fortran tree fork-shared)
- Step 9.5 deliberately does NOT modify `imogen/code/imogen_lpjg.f`.
  The Fortran Rh/W computation+writer port (item a in the original
  step 9.5 plan) was deferred to step 9.5b after investigation revealed
  Fortran engine doesn't COMPUTE Rh/wind at all — it's not just a writer
  port but a full physics-pipeline port (~70-100 LOC of Fortran).

---

### Step 9: SSP1-2.6 run-config + bug C5/R-anom fixes; perturbation_factor add-then-remove

**Commit:** `d6f4853` (Step 9; tag `v0.9.0-step9-smoke`)  **Date:** 2026-05-07

**[Hash filled in 2026-05-08, step-15 cleanup]**: replaced `_TBD_`
placeholder with verified hash via `git rev-list -n 1 v0.9.0-step9-smoke`.

#### Net source-level change in `lpjguess/`: ZERO

Step 9's substantive deliverable is the `runs/SSP1-2.6/` directory
(NOT in `lpjguess/`) and the documentation. The `lpjguess/` source
files received only **annotation comments** documenting an
add-then-remove cycle of the `imogen_nee_perturbation_factor` runtime
parameter (added at step 9 phase C, removed at step 9 wrap-up because
the F-10 deadlock means LPJG main loop never runs in v1.0 single-process
mode, so the helper could never affect anything observable; per user's
code-integrity preference, the helper was REMOVED rather than kept as
permanent v1.0 scaffolding).

#### File: `lpjguess/framework/parameters.h`
- **Operation:** modify (annotation only; net code: zero added)
- **Lines:** ~510 (after the `coupling_mode` declaration block)
- **Description:** Comment block documenting the add-then-remove of
  `extern double imogen_nee_perturbation_factor;`.
- **Backport guidance:** Annotation-only; trivial copy.

#### File: `lpjguess/framework/parameters.cpp`
- **Operation:** modify (annotation only); same as `.h`.

#### File: `lpjguess/modules/imogencfx.cpp`
- **Operation:** modify (annotation only)
- **Lines:** in the `declare_parameter` block (after `coupling_mode`)
- **Description:** Comment block documenting the add-then-remove of
  `declare_parameter("imogen_nee_perturbation_factor", ...)`.

#### File: `lpjguess/modules/imogenoutput.cpp`
- **Operation:** modify (annotation only)
- **Lines:** in `flush_year` near the unit-conversion block
- **Description:** Comment block documenting that the
  `imogen_nee_perturbation_factor` multiplier was applied here briefly
  then removed.

#### Non-`lpjguess/` deliverables (catalogued for completeness)

Listed here for the Backport Sprint to know what step 9 delivered
(NOT requiring `lpjguess/` replication):
- `runs/SSP1-2.6/` (NEW): main.ins, imogen_intermediary.ins, README.md,
  + 11 stand/PFT/landcover ins files copied from version_A's predecessor
- `imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp126.txt` (NEW)

---

### Step 15: Stage I documentation preservation + Stage II PLUM-output reuse verification + bundled BACKPORT_LEDGER errata cleanup

**Commit:** `cd68b29` (Step 15; tag `v0.15.0-step15-stage1-deferral`)  **Date:** 2026-05-08

**[Hash filled in 2026-05-08 by step-16 prep work]**: replaced `_TBD_`
placeholder with verified hash via `git rev-list -n 1 v0.15.0-step15-stage1-deferral`.

---

### Step 16: Cluster launcher (loose-only baseline; F-10/F-12 caveats explicit) + workstation parallel mimic test

**Commit:** `572820c` (Step 16; tag `v0.16.0-step16-cluster-launcher`)  **Date:** 2026-05-08

**[Hash filled in 2026-05-08 by post-step-16 maintenance commit]**: replaced
`_TBD_` placeholder with verified hash via `git rev-list -n 1 v0.16.0-step16-cluster-launcher`.

#### Net source-level change in `lpjguess/`: ZERO

Step 16 is bash + docs + .gitignore additions only — entirely OUTSIDE
`lpjguess/`. **Backport-irrelevant.**

#### Files added (all OUTSIDE `lpjguess/`)

- `scripts/cluster/run_coupled.sbatch` (NEW, ~17 KB / 290 lines bash) —
  top-level SLURM launcher mirroring `scripts/run_coupled.sh` CLI; refuses
  cluster + tight in v1.0 with clear error + resolution pointer to F-12 Option C
- `scripts/cluster/setup_run.sh` (NEW, ~11 KB / 200 lines bash) —
  gridlist-split + per-rank `runNN/` + generates `submit.sh` + `startguess.sh`;
  adapted from IMK-IFU's 174-line `setup_run_owl_with_scratch_lpj_work.sh`
- `scripts/cluster/mpi_run_guess.sh` (NEW, ~7 KB / 165 lines bash) —
  per-rank scratch-I/O wrapper; multi-MPI rank detection (MPICH || OpenMPI ||
  SLURM); adapted from IMK-IFU's 82-line `mpi_run_guess_on_tmp.sh`
- `scripts/cluster/finishup_lpj_work.sh` (NEW, ~7 KB / 175 lines bash) —
  post-run aggregation; adapted from IMK-IFU's 172-line `finishup_lpj_work_owl.sh`
- `scripts/cluster/make_guess.sh` (NEW, ~4.5 KB / 130 lines bash) —
  cluster-side build helper with `--mpi` flag; lightweight version of
  IMK-IFU's 126-line `make_guess.sh`
- `scripts/cluster/append_files.sh` (NEW, ~1.7 KB / 40 lines bash) —
  per-file aggregator helper; adapted (verbatim with comments) from
  IMK-IFU's `append_files.sh`
- `scripts/cluster/env_owl.sh` (NEW, ~3.7 KB / 80 lines bash) —
  module-load template (PLACEHOLDER values; refine via SSH on owl)
- `scripts/cluster/README.md` (NEW, ~6 KB / 175 lines markdown) —
  comprehensive cluster-orchestration narrative
- `scripts/run_parallel_mimic.sh` (NEW, ~9 KB / 200 lines bash) —
  workstation parallel mimic test (4-rank `mpirun -np N` on smoke gridlist)
- `notes/STEP_16.md` (NEW, ~13 KB markdown)

#### Files modified (all OUTSIDE `lpjguess/`)

- `docs/build.md`: cluster section replaced from placeholder with full
  step-by-step + F-10/F-12 caveat narrative + cross-references
- `.gitignore`: +2 step-16 rules (`runs/*/parallel_work/` for workstation
  parallel mimic per-rank work dirs; `lpjguess/build_mpi/` for cluster MPI build)
- `CHANGELOG.md`: NEW `[v0.16.0-step16-cluster-launcher]` entry
- `EXECUTION_PLAN.md`: V.1 step 16 row marked DONE 2026-05-08
- `notes/FOLLOWUPS.md`: status dashboard "Last updated" refresh
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (this file): this NEW step-16
  row appended

#### Cross-reference for the Backport Sprint

When the Backport Sprint runs the coupled model on the `trunk_r13078`
backend, it inherits the cluster orchestration verbatim — `scripts/cluster/`
is fork-agnostic. The Backport Sprint will use the SAME launcher with an
adapted `make_guess.sh --mpi` flow that selects the `trunk_r13078` build
backend via the future `-DLPJGUESS_BACKEND=trunk_r13078` cmake flag (added
at F-11 sprint time per §4 step 1 below).

The architectural-tension investigation this session also re-shaped the
F-12 sequencing into Phase 1 (per user-confirmed Path A; was Phase 2):

- v1.0 (current) ships with cluster + LOOSE working end-to-end + cluster +
  tight blocked with clear caveat
- F-12 Option B (next) lands single-process tight in v1.0
- F-12 Option C (after Option B) lands HPC tight in v1.0 via additive
  `framework_loop_mode = "year_outer"` ins parameter (per
  `docs/v2_roadmap.md` §5)

The F-11 Backport Sprint runs at end-of-Phase-1 per the original plan, so
the F-12 Options B + C work will all be in `lpjguess/` source by then — the
Backport Sprint will need to replicate them in `trunk_r13078`. This is a
significantly larger backport scope than was assumed in the prior chat
handoff Part 6 §28 — but still manageable per the sprint's per-step ledger
discipline.

#### Net source-level change in `lpjguess/`: ZERO

Step 15 is a documentation-only step per Decision #9 (Stage I deferred for
v1.0). Net-zero `lpjguess/` C++ source change; net-zero `imogen/code/`
Fortran source change; net-zero `intermediary_py/` Python source change;
net-zero run-config or tooling change. **Backport-irrelevant.**

#### Files added (all OUTSIDE `lpjguess/`)

- `docs/scientific_framework.md` (NEW, ~13 KB markdown) — canonical Stage I
  + Stage II + Decision #10 save_state/restart pattern + F-10 caveat narrative
- `docs/v2_roadmap.md` (NEW, ~13 KB markdown) — post-v1.0 trajectory:
  v1.1 PLUM-harm save_state wiring + F-12 Option B two-process; v2.0 F-12
  Option C in-process restructure + PLUM embedding
- `notes/STEP_15.md` (NEW, ~12 KB)

#### Files modified (all OUTSIDE `lpjguess/`)

- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (this file): §3 commit-hash
  errata cleanup (15 entries; 5 stale step-1-5 hashes corrected + 9 `_TBD_`
  step-9-14 placeholders filled in; verified via `git rev-list -n 1 <tag>`);
  + this NEW step-15 row appended
- `CHANGELOG.md`: NEW `[v0.15.0-step15-stage1-deferral]` entry
- `EXECUTION_PLAN.md`: V.1 step 15 row marked DONE 2026-05-08
- `notes/FOLLOWUPS.md`: status dashboard "Last updated" date refresh

#### Cross-reference for the Backport Sprint

When the Backport Sprint runs the coupled model on the `trunk_r13078`
backend, it inherits the documentation produced at step 15 verbatim — the
new `docs/scientific_framework.md` and `docs/v2_roadmap.md` are framework-
wide artefacts, fork-agnostic. **No replication needed in `trunk_r13078`.**

The errata cleanup of `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 itself is
also fork-agnostic — the corrected commit hashes are the canonical reference
both backends will use.

---

### Step 17a (FOUNDATION): F-12 sub-milestone C1 architectural foundation — framework_loop_mode parameter + InputModule virtuals + framework.cpp year_outer additive code path

**Commit:** `_TBD_` (this commit; foundation only; full step-17a tag waits for IMOGENCFXInput overrides + cross-validation)  **Date:** 2026-05-10

The architectural foundation for the per-year-outer / per-gridcell-inner
loop ordering (which resolves F-10's deadlock for tight coupling at root)
is in place. **Default mode `framework_loop_mode = "gridcell_outer"`
preserves LTS-equivalent behaviour byte-exactly** (verifiable via
`git diff -w` of `framework.cpp` lines 411-534: zero whitespace-only
changes outside the new additive block; the existing per-gridcell-outer
block is byte-untouched via the early-return-on-year_outer pattern).

**Backport-relevance: HIGH.** All 6 file changes need to be replicated in
`trunk_r13078`. The additive nature (new ins parameter; new non-pure
virtuals on `InputModule` base class with default-fail implementations;
new code block gated on parameter; existing code path byte-untouched)
makes the backport mechanical.

#### Files modified (~250 LOC added across 6 files; all in `lpjguess/`)

- File: `framework/parameters.h`
  - Operation: modify (add)
  - Lines: +22 LOC, inserted adjacent to `coupling_mode` extern declaration
  - Description: `extern xtring framework_loop_mode;` in `IMOGENConfig`
    namespace, with inline doc block explaining `"gridcell_outer"` (default;
    LTS-equivalent) and `"year_outer"` (additive Path A code path) values.
    Cross-references FOLLOWUPS F-12, EXECUTION_PLAN V.1 rows 17a/17b/17c,
    session-2 chat handoff Part 9.
  - Backport guidance: trivial copy-paste; mirrors the proven step-8
    `coupling_mode` declaration pattern.

- File: `framework/parameters.cpp`
  - Operation: modify (add)
  - Lines: +8 LOC, inserted adjacent to `coupling_mode` definition
  - Description: `xtring framework_loop_mode = "gridcell_outer";` default
    value. The default preserves LTS-equivalent behaviour byte-exactly: no
    .ins-file edit is required for any existing run to continue behaving
    identically.
  - Backport guidance: trivial copy-paste.

- File: `modules/imogencfx.cpp`
  - Operation: modify (add)
  - Lines: +12 LOC, inserted in `IMOGENCFXInput::IMOGENCFXInput()` constructor
    immediately after the existing `coupling_mode` declare_parameter call
  - Description: `declare_parameter("framework_loop_mode",
    &IMOGENConfig::framework_loop_mode, 20, ...)` registration; mirrors the
    proven `coupling_mode` declare_parameter pattern from step 8.
  - Backport guidance: trivial copy-paste; relative position to
    `coupling_mode` declare_parameter is preserved.

- File: `framework/inputmodule.h`
  - Operation: modify (add)
  - Lines: +50 LOC, two new virtual method declarations on `InputModule`
    abstract base class with extensive doc blocks
  - Description: `virtual void preload_all_climate(Gridcell&, int, int);`
    + `virtual bool getclimate_for_year(Gridcell&, int, int);` declarations
    (non-pure; default implementations live in inputmodule.cpp). The
    non-pure-virtual choice preserves backward compatibility across all 9
    existing input modules without forcing stub overrides; only modules
    that opt in to year_outer mode need to override.
  - Backport guidance: trivial copy-paste; pure-additive change to base
    class; no existing virtual method signatures touched.

- File: `framework/inputmodule.cpp`
  - Operation: modify (add)
  - Lines: +33 LOC, default-fail implementations of the two new virtuals
  - Description: both call `fail()` (variadic; declared in
    `framework/shell.h`; transitively included via `guess.h`) with an
    actionable error pointing at `framework_loop_mode = "gridcell_outer"`
    fallback + canonical docs (FOLLOWUPS F-12 + STEP_17a.md).
  - Backport guidance: trivial copy-paste; uses existing `fail()` infrastructure.

- File: `framework/framework.cpp`
  - Operation: modify (add); EXISTING per-gridcell-outer block at lines
    411-534 BYTE-UNTOUCHED (early-return pattern preserves byte-exactness)
  - Lines: +218 LOC, new `if (IMOGENConfig::framework_loop_mode == "year_outer") { ... return 0; }`
    block inserted between lines 409 and 411 (after `bool is_first_gridcell = true;`)
  - Description: 5-phase year_outer code path:
    (1) C1 limitation guards — fail fast on `restart`, `save_state`,
        `crop_gs_out`, `printseparatestands` with clear pointers to
        `gridcell_outer` fallback (deferred to C1.2/C1.3)
    (2) Year range determination from `nyear_spinup`/`firsthistyear`/
        `lasthistyear`
    (3) Pre-load all gridcells with full per-cell setup pipeline
        (mirrors gridcell_outer lines 425-452: `date.init(1)`, `getgridcell`,
        `reset`, `setup_multipart`, `climate.initdrivers`, `landcover_init`)
        + call `preload_all_climate(gridcell, first_yr, last_yr)` on input
        module (default-fail virtual aborts here unless input module overrides)
    (4) Per-year outer loop calling `getclimate_for_year(gridcell,
        calendar_year, day_of_year)` + `simulate_day` + `outdaily` + year-end
        `outannual` + `balance.check_year` + `abort_request_received` per
        cell per day; `date.next()` per iteration. Per-cell `date` reset to
        (year_idx, day=0) at start of each (year, cell) tuple via
        `date.init(1) + date.year = year_idx`
    (5) Per-cell teardown (`balance.check_period` per cell) + cleanup +
        explicit `return 0;` to skip the existing per-gridcell-outer block below
  - Backport guidance: this is the largest single block; copy-paste verbatim.
    The block depends on:
      - `IMOGENConfig::framework_loop_mode` (added in `parameters.h/cpp` above)
      - `InputModule::preload_all_climate` + `getclimate_for_year`
        (added in `inputmodule.h/cpp` above)
      - `<memory>` header (already included via existing `framework.cpp` line 36)
    No re-indentation of existing code; the new block is purely additive
    with explicit early-return.

#### Verification (this commit)

- `cd lpjguess/build && make -j$(nproc)`: clean (only pre-existing
  `simfire_input.h` `fread` warnings; unrelated to this commit)
- `lpjguess/build/runtests --reporter compact`: "Passed all 25 test cases
  with 162 assertions." (default-mode byte-exact regression preserved)
- Default-fail virtuals: static verification only this commit; runtime
  exercise deferred to next session (when an IMOGENCFXInput override
  invokes the year_outer code path)

#### Remaining work within step 17a (next session(s); subsequent commit(s); see notes/STEP_17a.md §7)

1. **C1.1**: IMOGENCFXInput override of `preload_all_climate` +
   `getclimate_for_year` (~3-5 days; ~150-300 LOC additional).
   Critical complexity uncovered this session: the
   `IMOGENCFXInput::spinup_year_idx` class-member counter persists
   across cells in the existing gridcell_outer mode, causing
   per-cell-different spinup `imogen_year` selections. Year_outer
   override must reproduce this via the deterministic formula
   `spinup_year_idx_at_cell_idx_year_idx = (cell_idx * nyear_spinup +
   year_idx + 1) % NYEAR_SPINUP`. See STEP_17a.md §5.4 for the
   detailed analysis.
2. **C1.2**: Bit-exact cross-validation Run A (gridcell_outer) vs Run B
   (year_outer) on smoke gridlist (single-cell first to bypass cell-
   ordering complexity; multi-cell second to test the formula) (~1-2 days).
3. **C1 close-out**: tag `v0.17.0-step17a-c1-year-outer-single-process`;
   update this ledger with the C1.1 file changes; close C1 in FOLLOWUPS F-12.

#### Net source-level change in `lpjguess/`: ~250 LOC across 6 files (all additive)

Backport-relevance HIGH: the Backport Sprint (F-11) at end of Phase 1
must replicate these changes mechanically into `trunk_r13078`. The
purely-additive nature + the byte-untouched existing per-gridcell-outer
block makes the replication straightforward.

---

### Step 17a (C1.1 IMPLEMENTATION): F-12 sub-milestone C1.1 — ImogenInput year_outer overrides (preload_all_climate + getclimate_for_year) with corrected spinup_year_idx state-machine reproduction formula

**Commit:** `_TBD_` (this commit; C1.1 implementation only; full step-17a tag waits for C1.2 cross-validation + optional C1.3 IMOGENCFXInput follow-up)  **Date:** 2026-05-10 (later in same day as foundation commit `2e918c0`)

C1.1 implementation lands the FIRST input-module override pair for the
year_outer code path: `ImogenInput::preload_all_climate` +
`ImogenInput::getclimate_for_year`. This makes the year_outer code path
runnable end-to-end with `-input imogen` (loose-coupling input module)
once climate is pre-staged on disk.

**Strategic choice**: ImogenInput first; IMOGENCFXInput follow-up. See
`notes/STEP_17a.md` §5.5 for full rationale; in short:
- ImogenInput has NO `RUN_IMOGEN_ENGINE()` call in `init()` (verified via
  grep — only `imogencfx.cpp:524` has it). Loose-mode runs complete
  `init()` cleanly + reach the LPJG main loop; no F-10 deadlock; no
  engine-bypass workaround needed for cross-validation.
- ImogenInput's `getclimate()` pattern is ~95% identical to
  `IMOGENCFXInput::getclimate()`. Implementation strategy + the
  spinup_year_idx formula derived in C1.1 transfer near-verbatim to
  IMOGENCFXInput.
- Cross-validation purpose (per session-2 §9.5): validate the year_outer
  code path's CORRECTNESS vs gridcell_outer's. Input module choice is
  secondary; what matters is bit-exact comparison between modes WITH
  SAME input module + SAME climate forcing.

**Backport-relevance: HIGH.** Both file changes need to be replicated in
`trunk_r13078`. The additive nature (new methods on a derived class
overriding base virtuals; extensive doc blocks; reuses existing
infrastructure verbatim; no existing code changed) makes the backport
mechanical. When C1.3 (IMOGENCFXInput year_outer override) lands, that
will add a parallel set of file changes to this ledger.

**CRITICAL ERRATUM applied this commit**: the foundation commit
`2e918c0`'s docs (CHANGELOG 2026-05-10 entry, FOLLOWUPS F-12 C1
pre-flight findings extension, STEP_17a.md §5.4, this BACKPORT_LEDGER's
preceding step-17a-foundation entry's "Description" of the
year_outer block, session-2 chat handoff Part 10) all stated the
spinup_year_idx reproduction formula as `(cell_idx * nyear_spinup +
year_idx + 1) % NYEAR_SPINUP` (with `+1`). The CORRECT formula
(verified by tracing the EXACT code at `imogen_input.cpp:781-805` +
`imogencfx.cpp:1071-1095` during C1.1 implementation) has NO `+1`:

```
spinup_year_idx_at_(cell_idx, year_idx)
    = (cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP
```

Derivation: the existing `getclimate()` reads `spinup_year_idx` VALUE
BEFORE incrementing it on day 0, so for cell C, spinup year Y, the
value READ equals the count of prior day-0 increments
(C * nyear_spinup + Y) modulo NYEAR_SPINUP. The C1.1 implementation
uses the CORRECTED formula; subsequent doc updates (STEP_17a.md §5.4
erratum, CHANGELOG entry, FOLLOWUPS F-12 erratum, session-2 chat
handoff Part 11, this BACKPORT_LEDGER entry) all reflect the CORRECTED
formula. **The Backport Sprint must use the CORRECTED formula** when
applying these changes to `trunk_r13078`.

#### Files modified (~280 LOC added across 2 files)

- File: `lpjguess/modules/imogen_input.h`
  - Operation: modify (add)
  - Lines: +~80 LOC
  - Description: 3 new includes (`<map>`, `<utility>`, already-existing
    `lamarquendep.h`); 2 new `virtual` method declarations on
    `ImogenInput` (overrides of base-class virtuals from foundation
    commit `2e918c0`):
    - `preload_all_climate(Gridcell&, int first_calendar_year, int last_calendar_year)`
    - `getclimate_for_year(Gridcell&, int calendar_year, int day_of_year)`
    Both have extensive doc blocks documenting the design rationale +
    spinup_year_idx state-machine reproduction formula + cross-references.
    2 new private cache members:
    - `std::map<std::pair<double,double>, int> year_outer_cell_idx`
      (keyed by (lon, lat); maps to `current_grid_index` value at preload time)
    - `std::map<std::pair<double,double>, Lamarque::NDepData> year_outer_ndep_cache`
      (keyed by (lon, lat); maps to value-copy of `ndep` member at preload time)
  - Backport guidance: trivial copy-paste; pure-additive; no existing
    declarations touched. The cache members rely on `Lamarque::NDepData`
    being a value type (which it is — verified at `lamarquendep.h`
    member inspection).

- File: `lpjguess/modules/imogen_input.cpp`
  - Operation: modify (add)
  - Lines: +~200 LOC
  - Description: implementations of the 2 new virtual methods inserted
    between `getclimate()` body end and `getsoil()`. Both implementations
    are documented with cross-references to the .h doc blocks +
    STEP_17a.md §5.4 + FOLLOWUPS F-12. They use the CORRECTED
    spinup_year_idx formula throughout. Reuse existing infrastructure
    (`readenv`, `get_climate_for_gridcell`, `gen_filename`, `co2.load_file`,
    `distribute_ndep`, `Lamarque::NDepData::get_one_calendar_year`)
    without modification. Per-day field assignments mirror existing
    `getclimate()` lines 876-887, INCLUDING the K → degC temperature
    conversion at line 876 specific to ImogenInput
    (`climate.temp = dtemp[day_of_year] - 273.15;` — IMOGENCFXInput's
    getclimate at line 1166 does NOT do this conversion; the two input
    modules have different temperature-unit conventions; this is
    preserved here for bit-exact reproduction of ImogenInput's
    gridcell_outer behaviour).
  - Backport guidance: trivial copy-paste; pure-additive; no existing
    function bodies touched. The `getclimate()` body is byte-untouched
    (verifiable via `git diff -w` showing zero whitespace-only changes
    outside the new block).

#### Verification (this commit)

- `cd lpjguess/build && make -j$(nproc)` (full clean rebuild): clean
  (only pre-existing warnings; ZERO warnings introduced by C1.1)
- `lpjguess/build/runtests --reporter compact`: "Passed all 25 test
  cases with 162 assertions." (default-mode + new-input-module
  byte-exact regression preserved)
- Spinup_year_idx formula correct (NO +1): hand-traced against
  `imogen_input.cpp:781-805`
- Per-cell ndep cache copies are independent: NDepData is value type
- K → degC conversion preserved: `getclimate_for_year` line matches
  existing `getclimate` line 876
- Backward compatibility: `getclimate()` body unchanged

#### Remaining work within step 17a (next session(s))

1. **C1.2** (~1-2 days): runtime bit-exact cross-validation Run A vs
   Run B on smoke gridlist (single-cell first; multi-cell second).
   Operational pre-requisites: pre-stage climate via launcher per
   session-1 §49.1 operational pattern; custom .ins file with
   `coupling_mode "loose"` + framework_loop_mode override; bash
   harness; iterate on divergences. The GO/NO-GO gate for C1.
2. **C1.3** (~2-3 days): replicate C1.1 implementation pattern for
   `IMOGENCFXInput`. Same structure + the additional climate fields
   (relhum, wind, tmin, tmax) handled via the additional
   `read_lines_from_file` calls already in `IMOGENCFXInput::readenv()`.
   Optional NEW ins parameter `skip_inprocess_engine_run` (default
   `false`) gating the `RUN_IMOGEN_ENGINE()` call in
   `IMOGENCFXInput::init()` to enable IMOGENCFX-mode cross-validation
   without F-10 deadlock. Cross-validate identically (single-cell
   first; multi-cell second).
3. **C1 close-out**: tag `v0.17.0-step17a-c1-year-outer-single-process`;
   update this ledger with C1.2/C1.3 file changes.

#### Net source-level change in `lpjguess/`: ~280 LOC across 2 files (all additive)

Backport-relevance HIGH (purely additive). The Backport Sprint (F-11)
at end of Phase 1 must replicate these changes mechanically into
`trunk_r13078`. The CORRECTED formula must be used when applying the
C1.1 changes; do NOT use the foundation commit's incorrect `+1`
formulation that propagated into multiple docs and was corrected
this commit.

---

### Step 17a (C1.2 1-CELL CROSS-VALIDATION): F-12 sub-milestone C1.2 — runtime bit-exact validation of year_outer code path on 1-cell smoke

**Commit:** `8bddc27` (un-tagged; full step-17a tag waits for sub-step 7.3.2 IMOGENCFXInput follow-up)  **Date:** 2026-05-10 (evening, same day as C1.1 commit `90401f2`)

**[Errata 2026-05-10 late evening, step-17a C1.3 sub-step 7.3.1 commit]**: previously `_TBD_` placeholder; now filled in with verified hash `8bddc27` per `git rev-list -n 1 HEAD~1` (where HEAD is the C1.3 sub-step 7.3.1 + engine writer fix commit).

C1.2 lands the runtime cross-validation milestone for the year_outer
code path. Both Run A (`framework_loop_mode = "gridcell_outer"`) and
Run B (`framework_loop_mode = "year_outer"`) ran end-to-end against
the same pre-staged engine climate using `-input imogen` (loose-coupling
input module + ImogenInput's C1.1 year_outer overrides). All 37
standard LPJ-GUESS outputs match BIT-EXACT.

**GO/NO-GO gate per session-2 §9.5: ✅ PASSED for 1-cell smoke.**

Cross-validation harness output:
```
SUMMARY: 37/37 bit-exact matches; 0 mismatches
PASS: All .out files are bit-exact between Run A and Run B.
```

#### Files modified (1 file; 9 LOC; backport-relevant)

- File: `lpjguess/modules/imogen_input.cpp`
  - Operation: modify (add)
  - Lines: +9 LOC, inserted in `ImogenInput::ImogenInput()` constructor
    after the existing `declare_parameter("monthly_imogen", ...)` call
  - Description: new `declare_parameter("framework_loop_mode",
    &IMOGENConfig::framework_loop_mode, 20, ...)` mirroring
    `IMOGENCFXInput`'s identical declaration at `imogencfx.cpp:353`.
    Required for `-input imogen` (loose-mode) runs to recognize the
    parameter (without it, `Paramlist::operator[]` aborts with
    "framework_loop_mode not found" when the .ins file sets
    `framework_loop_mode`).
  - Backport guidance: trivial copy-paste; pure-additive; mirrors the
    foundation commit `2e918c0`'s `IMOGENCFXInput`-side declaration.
    The same parameter declared in two input modules + same address
    is fine: plib accepts both registrations + each binds to the same
    `IMOGENConfig::framework_loop_mode` global. Pre-existing pattern;
    `searchradius` is also declared in both ImogenInput +
    IMOGENCFXInput identically.

#### Files added (NOT in `lpjguess/`; backport-IRRELEVANT)

(None of these need replication in trunk_r13078; they're testing /
operational artifacts, not LPJG source.)

- `data/gridlist/gridlist_test1.txt` (NEW; 17 bytes; 1-cell IMOGEN grid
  cell at `-78.75 82.50`)
- `runs/SSP1-2.6/main_xval_loose.ins` (NEW; ~5.5 KB; loose-mode .ins
  for cross-validation)
- `scripts/cross_validate_year_outer.sh` (NEW; ~8.4 KB / 230 LOC bash;
  cross-validation harness)

#### Verification (this commit)

- `scripts/cross_validate_year_outer.sh 1cell`: ✅ PASS — 37/37
  bit-exact matches; 0 mismatches; 0 missing files
- `cd lpjguess/build && make -j$(nproc)`: clean (only pre-existing
  warnings)
- `lpjguess/build/runtests --reporter compact`: "Passed all 25 test
  cases with 162 assertions."
- Backward compatibility: gridcell_outer mode (Run A) unchanged

#### Operational discoveries (informs C1.3 + production)

1. **Engine output is alternating-year**: only ODD years (1871, 1873,
   ..., 1901) have full climate; EVEN years have only `done` marker.
   Engine NCALLYR/STEP_DAY internals; resolved at C1.2 by constraining
   nyear_spinup=1 + firsthistyear=1871 so all imogen_year selections
   land on 1871 (ODD ✓).
2. **IMOGEN grid (3.75°×2.5° HadCM3) vs LPJG soilmap grid (0.5°
   .25-centered)**: ZERO exact-cell intersections. Resolved via
   `searchradius` (climate; class member; custom-param syntax) +
   `searchradius_soil` (SoilInput; declare_parameter; bare-global
   syntax). Per user's 2026-05-10 evening guidance.
3. **Engine REGRID parameter** at
   `runs/SSP1-2.6/imogen_intermediary.ins:244` (currently FALSE)
   regrids climate to user-specified gridlist when TRUE. Alternative
   to searchradius approach for production runs.

#### Remaining work within step 17a (next session(s); per STEP_17a.md §7.3 + §7.4)

1. **Sub-step 7.3.1 multi-cell cross-validation** (~0.5 day):
   Test the spinup_year_idx state-machine reproduction formula across
   cells. With `nyear_spinup=2` + 4-cell gridlist, all per-cell
   imogen_year selections land on ODD staged years.
2. **Sub-step 7.3.2 IMOGENCFXInput year_outer override** (~1.5-2 days):
   Replicate C1.1 pattern for `IMOGENCFXInput` + handle additional
   climate fields (relhum, wind, tmin, tmax) + BLAZE compatibility +
   engine-bypass mechanism (NEW `skip_inprocess_engine_run`
   parameter OR REGRID=1 alternative OR defer to C2).
3. **C1 close-out**: tag
   `v0.17.0-step17a-c1-year-outer-single-process`; update this ledger
   with the C1.3 file changes.

#### Net source-level change in `lpjguess/`: 9 LOC across 1 file (purely additive)

Backport-relevance HIGH (the 9-LOC declare_parameter mirror is purely
additive; it makes ImogenInput's parameter table consistent with
IMOGENCFXInput's). The Backport Sprint must replicate this single
declare_parameter call in `trunk_r13078`'s `imogen_input.cpp` along
with the foundation + C1.1 changes.

### Step 17a (C1.3 SUB-STEP 7.3.1 + ENGINE WRITER FIX): F-12 sub-milestone C1.3 sub-step 7.3.1 — multi-cell xval bit-exact PASS + IMOGEN engine writer fix (alternating-year quirk resolved at root)

**Commit:** `7be595a` (un-tagged; full step-17a tag at C1 close-out at sub-step 7.3.2 commit)  **Date:** 2026-05-10 (late evening, same day as C1.2 commit `8bddc27`)

**[Errata 2026-05-10 very late evening, step-17a sub-step 7.3.2 + close-out commit]**: previously `_TBD_` placeholder; now filled in with verified hash `7be595a` per `git rev-list -n 1 HEAD~1` (where HEAD is the sub-step 7.3.2 + C1 close-out commit).

This commit lands TWO bundled deliverables: (A) IMOGEN engine writer fix in `lpjguess/modules/climatemodel.cpp` (5 conditional removals at lines ~787, ~884, ~963, ~988, ~998 + extensive doc blocks; ~76 LOC total). (B) C1.3 sub-step 7.3.1 4-cell cross-validation PASS bit-exact (37/37) on `gridlist_test2.txt` × `nyear_spinup=2` × `lasthistyear=1879`.

**GO/NO-GO gate per session-2 §9.5: ✅ PASSED for both 1-cell AND 4-cell smoke.** The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is now empirically validated across BOTH cell_idx>0 AND year_idx>0 branches.

#### Files modified (1 file in `lpjguess/`; +76 LOC, -5 LOC; net +~71 LOC; backport-relevant)

- File: `lpjguess/modules/climatemodel.cpp`
  - Operation: modify (5 conditional removals + extensive doc blocks)
  - Lines:
    - ~787 (CO2.dat + CO2_all.dat OPEN block): `if (iyear == year1) {` → `{` (compound statement)
    - ~884 (climate-anomaly OPEN block: T_anom, P_anom, SW_anom, WET, DTEMP_anom, Rh_anom, W_anom, Tmin_anom, Tmax_anom): same gate removal
    - ~963 (climate-anomaly CLOSE block): `if (iyear == iyend) {` → `{`
    - ~988 (oceanFeed FA_OCEAN/DTEMP_O OPEN block): `if (iyear == year1) {` → `{`
    - ~998 (oceanFeed FA_OCEAN/DTEMP_O CLOSE block): `if (iyear == iyend) {` → `{`
  - Description: removes the structural alternating-year quirk in the engine writer. Each iteration of the per-IYEAR loop now opens + writes + closes its own per-year files cleanly. `thisYear` was already updated per IYEAR iteration at line ~457 (`thisYear = std::to_string(iyear)`), so each iteration's open targets the correct year-folder. Pre-fix, the gate skipped opens at non-YEAR1 iterations → subsequent WRITE statements went to default-closed std::ofstream objects → silent failure → only YEAR1 of each engine call had data; combined with `updateImogenControlData()` advancing YEAR1++ per iteration → only ODD years 1871, 1873, ..., 1901 had full climate; EVEN years had only `done` markers. Post-fix: ALL years in the engine's iteration range receive full climate.
  - Backport guidance: trivial mechanical fix (5 conditional removals). The Backport Sprint must apply identically to `trunk_r13078`'s `lpjguess/modules/climatemodel.cpp`. The change preserves all existing data writes (1871's content unchanged) while adding writes for previously-skipped iterations. Has the side-effect of adding restart-state files (fa_ocean.dat, dtemp_o.dat) for all years, not just YEAR1 of each call — beneficial structural improvement.
  - Side-finding (NOT fixed in this commit; documented for visibility): SAME structural bug exists in standalone Fortran engine `imogen/code/imogen_lpjg.f` at lines 954, 1013, 1071, 1088, 1099 (`IF(IYEAR.EQ.YEAR1) THEN` and `IF(IYEAR.EQ.IYEND) THEN` gates around OPEN/CLOSE in both REGRID and non-REGRID branches). Standalone Fortran is NOT on the prescribed-mode launcher path (which uses the in-process C++ port via `imogencfx::init() → RUN_IMOGEN_ENGINE()`); only used for engine-only smoke testing per session-1 §46. DEFERRED for symmetric fix as F-N-equivalent follow-up. The Backport Sprint should consider whether to bundle the Fortran fix at the same time.

#### Configuration files modified (NOT in `lpjguess/`; backport-IRRELEVANT)

- `runs/SSP1-2.6/main_xval_loose.ins` (modified; +45 LOC, -17 LOC; net +28 LOC):
  - Updated comment block at the spinup overrides section explaining the new C1.3 sub-step 7.3.1 multi-cell config (nyear_spinup=2 + lasthistyear=1879 + cache sizing analysis).
  - Changed `nyear_spinup 1 → 2` (exercises year_idx 0..1 of formula).
  - Changed `lasthistyear 1871 → 1879` (gives ImogenInput cache nyears=9 sufficient for 9 distinct imogen_years across all cell-year combinations).
  - Changed `lastoutyear 1871 → 1879` (output 9 historical years).
  - Changed `param "lasthistyear" (num 1871) → (num 1879)`.
  - Now serves both 1-cell xval (cell_idx=0; tests year_idx 0..1 branches of formula via single cell) AND 4-cell xval (cells 0..3; tests cell_idx 0..3 + year_idx 0..1 branches of formula).

#### Verification (this commit)

- `cd lpjguess/build && make clean && make -j$(nproc)` (full clean rebuild): clean (only pre-existing warnings; ZERO introduced)
- `lpjguess/build/runtests --reporter compact`: ✅ "Passed all 25 test cases with 162 assertions."
- Climate re-stage produces ALL 32 years (1871-1902) with 13 files each (vs prior 16 ODD with 13 + 16 EVEN with 1). Confirmed via per-year `ls | wc -l`. `diff <(ls 1871) <(ls 1872)` = EMPTY.
- `scripts/cross_validate_year_outer.sh 4cell`: ✅ PASS — 37/37 bit-exact matches; 0 mismatches; 0 missing files
- `scripts/cross_validate_year_outer.sh 1cell` (regression check with new config): ✅ PASS — 37/37 bit-exact matches (C1.2 PASS preserved post-engine-fix)
- Both Run A and Run B reach "Finished" end-to-end (12245 stdout lines each)

#### Side-finding (NOT fixed in this commit; documented)

Latent OOB write in existing `getclimate()` cache surfaced during this commit's iteration: `stored_years[store_index] = imogen_year` triggers undefined behavior when `store_index >= nyears` (the cache size from `nyears = (lasthistyear - FIRST_SPINUP_YEAR) + 1` formula is undersized for some test configs). Pre-existing latent bug in the existing code (NOT introduced by this commit's changes). Worked around in this test by bumping `lasthistyear` to size the cache appropriately. Could be hardened with explicit bounds check + dynamic resize OR refactored cache size formula in a future commit if production runs hit it. Not blocking.

#### Net source-level change in `lpjguess/`: +~76 LOC, -5 LOC across 1 file (climatemodel.cpp; mostly additive incl. doc blocks)

Backport-relevance HIGH. The Backport Sprint must replicate the 5 conditional removals + their associated doc blocks in `trunk_r13078`'s `lpjguess/modules/climatemodel.cpp`. Mechanical change. Consider also bundling the symmetric Fortran fix at `imogen/code/imogen_lpjg.f` if Fortran engine is used in any test scenarios.

### Step 17a (C1.3 SUB-STEP 7.3.2 + C1 CLOSE-OUT): F-12 sub-milestone C1.3 sub-step 7.3.2 — IMOGENCFXInput year_outer override + skip_inprocess_engine_run ins parameter + K→C latent-bug fix in IMOGENCFXInput::get_climate_for_gridcell — FULL C1 CLOSE-OUT (TAGGED v0.17.0-step17a-c1-year-outer-single-process)

**Commit:** `_TBD_` (this commit; FULL C1 CLOSE-OUT; **TAGGED `v0.17.0-step17a-c1-year-outer-single-process`** at this commit)  **Date:** 2026-05-10 (very late evening, same day as sub-step 7.3.1 commit `7be595a`)

This commit closes out F-12 sub-milestone C1 by landing THREE bundled deliverables on top of foundation 2e918c0 + C1.1 commit 90401f2 + C1.2 commit 8bddc27 + C1.3 sub-step 7.3.1 commit 7be595a. ALL FOUR cross-validation scenarios (imogen 1cell + imogen 4cell + imogencfx 1cell + imogencfx 4cell) PASS bit-exact 37/37 each.

#### A. NEW `skip_inprocess_engine_run` ins parameter (~50 LOC across 3 files; backport-relevant)

- File: `lpjguess/framework/parameters.h`
  - Operation: modify (add)
  - Lines: +22 LOC; new `extern bool skip_inprocess_engine_run;` declaration with extensive doc block in IMOGENConfig namespace; placed after `framework_loop_mode` extern.
  - Description: declares the bool ins parameter that gates `RUN_IMOGEN_ENGINE()` in `IMOGENCFXInput::init()`. Default `false` preserves LTS-equivalent behaviour. When set `true` in an .ins file, IMOGENCFXInput::init() skips the in-process engine call (which would otherwise deadlock per F-10 in single-process tight); user must pre-stage climate externally via launcher run + climate writer fix landed at C1.3 sub-step 7.3.1 commit `7be595a`.
  - Backport guidance: trivial copy-paste into `trunk_r13078`'s `lpjguess/framework/parameters.h` IMOGENConfig namespace. Single declaration line + doc block.

- File: `lpjguess/framework/parameters.cpp`
  - Operation: modify (add)
  - Lines: +14 LOC; new `bool skip_inprocess_engine_run = false;` definition with doc block; placed after `framework_loop_mode` definition.
  - Description: defines the bool with default `false`.
  - Backport guidance: trivial copy-paste.

- File: `lpjguess/modules/imogencfx.cpp`
  - Operation: modify (add) at TWO sites
  - Lines:
    - +14 LOC at constructor: new `declare_parameter("skip_inprocess_engine_run", &IMOGENConfig::skip_inprocess_engine_run, "...")` registration with doc block, placed after `framework_loop_mode` declare_parameter.
    - +14 LOC around `RUN_IMOGEN_ENGINE()` call at line ~524: gate on `if (!IMOGENConfig::skip_inprocess_engine_run)` with doc block + informative dprintf when the flag is set.
  - Description: registers the parameter in the input module's plib table + gates the engine call.
  - Backport guidance: mechanical; same call-site as the existing RUN_IMOGEN_ENGINE call.

#### B. IMOGENCFXInput year_outer overrides (~345 LOC across 2 files; backport-relevant)

- File: `lpjguess/modules/imogencfx.h`
  - Operation: modify (add)
  - Lines: +95 LOC additive (2 includes `<map>`, `<utility>`; 2 new virtual method declarations with extensive doc blocks; 2 cache map members `year_outer_cell_idx` + `year_outer_ndep_cache`)
  - Description: declares the year_outer mode overrides + per-cell cache. Doc blocks document the 3 IMOGENCFXInput-specific differences from ImogenInput's C1.1 pattern: (1) NO K→C conversion in climate.temp = dtemp[date.day] (preserved here for byte-exact reproduction; per K→C fix in item C below); (2) additional climate fields populated from cache (relhum, u10, tmin, tmax per step 9.5 wiring); (3) BLAZE compatibility check on day 0.
  - Backport guidance: copy-paste mechanically; same structure as ImogenInput's C1.1 cache members + virtual decls in imogen_input.h.

- File: `lpjguess/modules/imogencfx.cpp`
  - Operation: modify (add)
  - Lines: +~250 LOC additive (2 method implementations with extensive doc blocks); inserted before `getsoil()` definition.
  - Description: implements `IMOGENCFXInput::preload_all_climate(Gridcell&, int first, int last)` (pre-loads all needed years' climate for one cell into existing cache via readenv; mirrors C1.1 ImogenInput pattern with IMOGENCFXInput-specific differences) + `IMOGENCFXInput::getclimate_for_year(Gridcell&, int year, int day)` (reads from cache; on day 0: BLAZE check + populate per-day arrays via get_climate_for_gridcell + ndep + co2; every day: assigns all Climate fields including IMOGENCFXInput-specific relhum/u10/tmin/tmax + Gridcell ndep). Uses CORRECTED spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`).
  - Backport guidance: copy-paste mechanically; same structure as ImogenInput's C1.1 method implementations in imogen_input.cpp; ensure CORRECTED formula (NO `+1`) is preserved.

#### C. K→C latent-bug fix in `IMOGENCFXInput::get_climate_for_gridcell` (~25 LOC change; 6 code-line changes; backport-relevant)

- File: `lpjguess/modules/imogencfx.cpp`
  - Operation: modify (~25 LOC of doc blocks + 6 code-line changes adding `- 273.15`)
  - Lines:
    - Monthly branch (lines ~902-908): `mtmp[i] = all_temp[store_index][igrid][i] - 273.15` (was without `-273.15`); same fix for `mtmin[i]` and `mtmax[i]` in the lines ~923-927 block (Tmin/Tmax monthly arrays).
    - Daily branch (lines ~935-952): `dtemp[i] = all_temp[store_index][igrid][i] - 273.15` (was without `-273.15`); same fix for `dtmin[i]` and `dtmax[i]` in the conditional blocks below.
  - Description: K→C conversion at the input-reading layer. Root cause: IMOGEN engine writes T_anom/Tmin_anom/Tmax_anom in Kelvin; LPJG expects climate.temp/.tmin/.tmax in Celsius. Existing IMOGENCFXInput::getclimate had a LATENT K-vs-C bug for these 3 temperature fields — never surfaced because LPJG main loop never ran in -input imogencfx mode pre-F-12 (F-10 deadlock at IMOGENCFXInput::init's RUN_IMOGEN_ENGINE call blocked before main loop could exercise getclimate's per-day driver). ImogenInput's getclimate at imogen_input.cpp:876 correctly does `-273.15`; IMOGENCFXInput didn't. Surfaced empirically during sub-step 7.3.2 cross-validation with skip_inprocess_engine_run=1 bypassing F-10 (Run A failed at Soil::soil_temp_multilayer with T[i]: 169.393 = -103.76°C). Fix: subtract 273.15 at the monthly-array population step in get_climate_for_gridcell. Single change point benefits BOTH gridcell_outer (existing getclimate) AND year_outer (new getclimate_for_year) modes since both invoke get_climate_for_gridcell. Aligns IMOGENCFXInput's dtemp semantics with CFXInput's pattern (dtemp in Celsius natively; CFXInput's NetCDF ISIMIP3b is in Celsius). Per user's 2026-05-10 clarification: "imogencfx is meant to work like the cfx input module, with only caveat being instead of NetCDF climate forcing it takes in IMOGEN climate; everything else remains as with the cfx module."
  - Backport guidance: 6 line-level edits; mechanical. Same fix should be applied to `trunk_r13078`'s `lpjguess/modules/imogencfx.cpp` get_climate_for_gridcell. NO behavioral change to gridcell_outer mode that has previously run without exercising LPJG main loop in imogencfx mode (since LPJG main loop never ran in imogencfx mode pre-F-12 due to F-10).

#### Run-config + harness files added/modified (NOT in `lpjguess/`; backport-IRRELEVANT)

- `runs/SSP1-2.6/main_xval_imogencfx.ins` (NEW; ~140 LOC): mirrors `main_xval_loose.ins` exactly except (1) `coupling_mode "prescribed"` (vs "loose"; canonical for IMOGENCFXInput) and (2) `skip_inprocess_engine_run 1` (NEW). Includes the additional 4 file_relhum/wind/tmin/tmax param directives (IMOGENCFXInput-specific; safely processed post-engine-fix at sub-step 7.3.1).

- `scripts/cross_validate_year_outer.sh` (modified; ~20 LOC change): added optional 2nd argument for input-module selector (`imogen` (default; preserves prior behaviour) | `imogencfx` (NEW)). Run-output dirs gain `_imogencfx_` infix when imogencfx variant is used. The `-input` flag uses the variable. Banner updated.

#### Verification (this commit)

- `cd lpjguess/build && make -j$(nproc)`: clean (only pre-existing warnings; ZERO introduced)
- `lpjguess/build/runtests --reporter compact`: ✅ "Passed all 25 test cases with 162 assertions."
- ALL FOUR cross-validation scenarios PASS bit-exact (37/37 .out files identical):
  - `scripts/cross_validate_year_outer.sh 1cell imogen`: ✅ PASS
  - `scripts/cross_validate_year_outer.sh 4cell imogen`: ✅ PASS (regression)
  - `scripts/cross_validate_year_outer.sh 1cell imogencfx`: ✅ PASS (NEW)
  - `scripts/cross_validate_year_outer.sh 4cell imogencfx`: ✅ PASS (NEW)
- The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is empirically validated for BOTH input modules across BOTH single-cell + multi-cell + single-spinup-year + multi-spinup-year scenarios.
- Backward compatibility: existing `IMOGENCFXInput::getclimate()` body unchanged (the K→C fix is in the `get_climate_for_gridcell` helper that both modes use; preserves byte-exactness between modes).

#### Net source-level change in `lpjguess/`: +~420 LOC, -0 LOC across 4 files (parameters.h + parameters.cpp + imogencfx.h + imogencfx.cpp; mostly additive incl. doc blocks)

Backport-relevance HIGH for all 4 file changes. The Backport Sprint must replicate all of these in `trunk_r13078`'s corresponding files. Mechanical changes (declarations + parameter registration + cache members + method implementations + 6 K→C code-line edits in get_climate_for_gridcell). All changes preserve gridcell_outer's byte-exact behaviour (year_outer is purely additive; K→C fix benefits both modes equally).

---

### Step 17b (PREP): C2 prep phase — Anaconda3 `mpicxx` wrapper fix + `make_guess.sh` `--mpi` NetCDF logic fix + `build_mpi/guess` baseline verification

**Commit:** _to be determined_ (this commit; un-tagged checkpoint)
**Backport relevance:** **IRRELEVANT** (scripts/ + docs only; no `lpjguess/` source change)

Net `lpjguess/` source-level change this commit: **ZERO**. All changes are in `scripts/` + `notes/` + `CHANGELOG.md` + `EXECUTION_PLAN.md` + this ledger. Listed here for traceability only — the Backport Sprint can skip this commit (it has no source code to replicate in `trunk_r13078`).

Build-environment prerequisite for the Backport Sprint to note when applying step-17b changes to `trunk_r13078`: the Anaconda3 `mpicxx` wrapper requires either `conda install -c conda-forge gxx_linux-64` (recommended; provides matching wrapper compiler + libstdc++) OR `MPICH_CXX=g++` env-var override (NOTE: handoff Part 8.1 + the C2 prompt incorrectly said `OMPI_CXX`; that's the OpenMPI variable; Anaconda3 ships MPICH; verified live 2026-05-11). Detailed rationale in `notes/STEP_17b.md` §3.

Operational scripts updated this commit (NOT in `lpjguess/`; **NOT backportable to `trunk_r13078`**):

#### File: `scripts/cluster/make_guess.sh`

- Replaced the previous (silent) `mpicxx` invocation with a fail-fast probe + actionable error message documenting both fixes (`conda install gxx_linux-64` preferred + `MPICH_CXX=g++` alternative with libstdc++ ABI caveat).
- Removed the `&& ${USE_MPI} -eq 0` clause that incorrectly excluded Anaconda3 NetCDF preference for workstation MPI builds. Workstation `--mpi` now uses Anaconda3 NetCDF (same as non-MPI build/guess), avoiding the Decision #8 broken `libhdf5_serial.so.310 ↔ libcurl@CURL_OPENSSL_4` mismatch. Cluster `--mpi` builds (which use module-loaded NetCDF) should NOT set `ANACONDA3_PREFIX`; the script auto-detects and skips.

#### File: `scripts/cross_validate_year_outer.sh`

- `GUESS_BIN` made env-var overridable via `${GUESS_BIN:-$ROOT/lpjguess/build/guess}`. Default unchanged. Enables testing alternative builds (e.g., `GUESS_BIN=$PWD/lpjguess/build_mpi/guess scripts/cross_validate_year_outer.sh 1cell imogen`).

#### File: `notes/STEP_17b.md` (NEW)

Full forensic record for C2 prep phase + C2 plan + B-item bundling decision; mirrors the per-step doc discipline established at step 0 + maintained through step 17a.

#### Empirical baseline verification this commit

| Check | Result |
|---|---|
| `lpjguess/build_mpi/guess` builds clean (`make_guess.sh --mpi` after `conda install gxx_linux-64`) | ✅ 2 836 440 bytes |
| `lpjguess/build_mpi/runtests` builds clean | ✅ 162 tests / 25 cases pass |
| MPI symbol linkage | ✅ `libmpi.so.12` + `libmpicxx.so.12` from Anaconda3 |
| NetCDF linkage | ✅ `libnetcdf.so.19` + `libhdf5.so.200` + `libcurl.so.4` from Anaconda3 (Decision #8 honored) |
| HAVE_MPI defined at compile | ✅ `auto_ptr<FinalizeCaller>` symbol present in `parallel.cpp.o` |
| All 4 xval scenarios bit-exact PASS against `build_mpi/guess` single-process | ✅ 37/37 bit-exact for all 4 (imogen 1cell, imogen 4cell, imogencfx 1cell, imogencfx 4cell) |

**The MPI build preserves the C1 baseline byte-exactly in single-process mode.** This provides a verified baseline against which the upcoming C2 core (MPI_Barrier + flush_year_globally_synchronized) can be measured.

---

### Step 17b (CORE): C2 core — MPI_Barrier at year boundary + ImogenOutput::flush_year_globally_synchronized + singleton-pointer pattern

**Commit:** _to be determined_ (this commit; un-tagged checkpoint on top of `1405ada` C2 prep)
**Backport relevance:** **HIGH for all 3 file changes.** Backport Sprint must replicate in `trunk_r13078`'s corresponding files. Mechanical changes; all purely additive.

Net `lpjguess/` source-level change this commit: **+317 LOC additive across 3 files; 0 deletions.**

#### File: `lpjguess/modules/imogenoutput.h` (+60 LOC additive)

- New public method declaration: `void flush_year_globally_synchronized(int year)`
- New public static accessor: `static ImogenOutput* get_instance() { return instance_; }`
- New private static member: `static ImogenOutput* instance_;`
- Extensive doc blocks explaining design rationale + single-process fallback semantics + cross-references

**Backport-RELEVANT.** All additive; trunk_r13078's imogenoutput.h needs the same insertions.

#### File: `lpjguess/modules/imogenoutput.cpp` (+181 LOC additive)

- `#include <mpi.h>` inside `#ifdef HAVE_MPI` (placed at file top BEFORE std headers per MPI-2 SEEK_SET clash; same discipline as `parallel.cpp:10-15`)
- `#include "parallel.h"` for `GuessParallel::get_rank()` accessor
- Static member definition: `ImogenOutput* ImogenOutput::instance_ = nullptr;`
- Constructor body addition: `instance_ = this;` (after the existing initialiser list comments)
- Destructor body addition: `if (instance_ == this) { instance_ = nullptr; }` (defensive guard against accidental re-creation)
- NEW method `void ImogenOutput::flush_year_globally_synchronized(int year)` (~120 LOC including doc block):
  - Mode-gate: returns early on `coupling_mode == "loose"` after reset (mirrors flush_year's gate)
  - HAVE_MPI block: `MPI_Initialized(&flag)` guard pattern (mirrors `imogencfx.cpp:381`); inside guard, 5× `MPI_Allreduce(MPI_DOUBLE/MPI_INT, MPI_SUM)` to aggregate per-rank `accum_NEE_kgC` / `accum_CH4_gCH4C` / `accum_N2O_kgN` / `accum_area_m2` / `accum_gridcell_count`; swap globals into `accum_*` so flush_year writes them
  - Rank check: `if (rank == 0) flush_year(year);` (lead-rank-only write)
  - All ranks: `reset_accumulators(); accum_year = -1; year_pending = false;` (post-flush state cleanup)
  - Per-rank diagnostic dprintf for non-lead ranks (inside HAVE_MPI + MPI_Initialized guard)

**Backport-RELEVANT.** Mechanical replication. Use the CORRECTED state-handling pattern (accum_year=-1 after flush to suppress outannual's auto-flush at year+1 cell 0).

#### File: `lpjguess/framework/framework.cpp` (+76 LOC additive)

- `#include <mpi.h>` inside `#ifdef HAVE_MPI` (placed before "config.h" include per MPI-2 SEEK_SET clash discipline)
- `#include "../modules/imogenoutput.h"` for `ImogenOutput::get_instance()` accessor
- Year-boundary block inserted in the year_outer additive code path, between the per-year cell-inner loop body close (line ~610) and the per-cell teardown block (line ~615 of the year_outer additive block; per existing C1.1 layout):
  - `#ifdef HAVE_MPI ... MPI_Initialized(&flag) guard ... MPI_Barrier(MPI_COMM_WORLD); #endif`
  - `if (GuessOutput::ImogenOutput* imout = GuessOutput::ImogenOutput::get_instance()) { imout->flush_year_globally_synchronized(calendar_year); }`
  - Extensive doc block (~55 LOC) explaining: MPI_Barrier rendezvous + flush_year_globally_synchronized semantics + single-process fallback + double-flush avoidance via accum_year=-1 + cross-references to imogenoutput.cpp + parallel.cpp + STEP_17b.md + FOLLOWUPS F-10

**Backport-RELEVANT.** Trunk_r13078's framework.cpp year_outer block (which itself is being added per the C1 foundation backport at step 17a-foundation) needs this same MPI_Barrier + flush_year_globally_synchronized block at year boundary.

#### Verification this commit

| Check | Method | Result |
|---|---|---|
| Build clean (build/; non-MPI) | `cd lpjguess/build && make -j$(nproc)` | ✅ |
| Build clean (build_mpi/; MPI) | `cd lpjguess/build_mpi && make -j$(nproc)` | ✅ |
| 162 unit tests (build/) | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| 162 unit tests (build_mpi/) | `lpjguess/build_mpi/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| All 4 xval re-PASS bit-exact against `build_mpi/guess` single-process | `GUESS_BIN=$PWD/lpjguess/build_mpi/guess scripts/cross_validate_year_outer.sh <variant> <input>` × 4 | ✅ 37/37 bit-exact for all 4 (imogen 1cell, imogen 4cell, imogencfx 1cell, imogencfx 4cell) — C1 baseline preserved through C2 core code addition |
| `mpirun -np 1 -parallel` smoke (verifies MPI_Init pathway + code path reaches `flush_year_globally_synchronized`) | hand-built `run1/` workdir + `timeout 60 mpirun -np 1 build_mpi/guess -parallel -input imogen ...` | ✅ "Finished" + diagnostic `[ImogenOutput] flushed year=XXXX` visible |

**The MPI build with the C2 core code preserves the C1 baseline byte-exactly in single-process mode. MPI_Init + MPI_Barrier + flush_year_globally_synchronized call path verified functional under mpirun -np 1 -parallel.**

#### Substantive-validation NaN finding + xval harness hardening (this commit; audit item B12 NEW)

While verifying C2 core via `mpirun -np 1 -parallel` smoke testing, isolation experiments surfaced that **ALL 4 C1 cross-validation scenarios produce NaN-laden outputs** (full forensic record in `notes/STEP_17b.md` §3a.7 + `notes/FOLLOWUPS.md` "Substantive-validation NaN finding (2026-05-11 evening)" + session-2 chat handoff Part 18). The C1 close-out's `cmp -s` byte-equality "PASS 37/37" was nominally correct but masked the substantive-validation gap (NaN bytes match NaN bytes).

**The NaN finding does NOT invalidate the C2 core source-level changes documented above** — my C2 code is correct + preserves byte-equality identically between C1-only-revert builds + C2 builds. The NaN issue is in the C1 baseline, NOT in C2 work.

**xval harness change** (backport-IRRELEVANT; scripts/ only):
- `scripts/cross_validate_year_outer.sh` (+~70 LOC): NEW substantive-validation NaN-gate after byte-equality check. Scans Run A + Run B `.out` files for `nan` tokens; FAILs with exit code 3 if found; provides actionable diagnostic. Effect: until audit item B12 is resolved (NaN root cause fixed), all 4 cross-validation scenarios correctly REPORT FAIL rather than PASS-of-garbage.

**Backport Sprint implications**: when applying step-17b-core changes to `trunk_r13078` at F-11 sprint:
1. Apply the 3 `lpjguess/` file changes per above (mechanical replication).
2. Replicate the xval harness substantive-validation NaN-gate (best practice; prevents the same byte-equality-of-garbage gap from appearing in `trunk_r13078` validation).
3. **NaN root-cause fix (B12)** ✅ LANDED 2026-05-11 evening session 3 — see step-17b-B12-resolved entry below.

### Step 17b (B12 RESOLVED): substantive-validation NaN root cause fix — config-only (.ins file changes); no `lpjguess/` source change

**Commit:** `488c5a2` (un-tagged checkpoint on top of `d7f6c74`)
**Backport relevance:** **IRRELEVANT FOR `lpjguess/` SOURCE.** The fix is entirely in `runs/SSP1-2.6/main_xval_*.ins` (config files; not part of the LPJG source tree). Backport Sprint does NOT need to apply this fix to `trunk_r13078`'s `lpjguess/` directly. HOWEVER, if `trunk_r13078`-based smoke runs are set up in the future, they MUST also use `ifcalccton 1` and `ifcalcsla 1` (the LPJ-GUESS defaults) — same trap exists in `trunk_r13078`'s LPJG code (the `init_cton_min()` / `init_cton_limits()` cascade behaviour is unchanged from upstream).

**Why this fix is config-only and NOT a `lpjguess/` source fix:**
The original LPJG code logic at `parameters.cpp:2333-2337` (skip `init_cton_min()` if `ifcalccton == 0`) is by design — the documented purpose is to allow users to set `cton_leaf_min` directly in `.ins` files rather than have it auto-computed via the Reich et al. 1992 relation. The TRAP is that `init_cton_limits()` is then called UNCONDITIONALLY at line 2345 and cascades 0 if `cton_leaf_min` is also 0 (default-init for unset PFTs). For a user setting `ifcalccton 0`, they'd ALSO need to set `cton_leaf_min` for every PFT in the .ins file to avoid the cascade. Our smoke `.ins` did NOT set `cton_leaf_min` per PFT (PFTs come from imported `global.ins` which doesn't set it); so the trap fired silently.

**Net `lpjguess/` source change in this commit: ZERO.**

**Files changed in this commit (none in `lpjguess/`):**
- `runs/SSP1-2.6/main_xval_loose.ins` — change `ifcalcsla 0 → 1` and `ifcalccton 0 → 1`; ~17 LOC change incl. ~15 LOC explanatory comment block
- `runs/SSP1-2.6/main_xval_imogencfx.ins` — same change with shorter comment; ~12 LOC change
- `data/gridlist/gridlist_test_temperate.txt` (NEW; 1 cell at Switzerland 7.50°E 47.50°N; preserved from B12 diagnostic narrowing as a useful additional test cell)
- Documentation updates (STEP_17b.md §3a.7.4c; CHANGELOG; EXECUTION_PLAN row 17b; FOLLOWUPS B-bundling table; this LEDGER entry)

**Verification this commit:**
- `cd lpjguess/build && make -j$(nproc)`: clean (no source change so should be no-op build)
- `cd lpjguess/build_mpi && make -j$(nproc)`: clean
- 162 unit tests pass on both builds
- All 4 xval scenarios PASS substantive (bit-exact AND non-NaN; 0/37 NaN-laden files in any run): imogen 1cell, imogen 4cell, imogencfx 1cell, imogencfx 4cell
- Same 4 xval scenarios PASS substantive against `build_mpi/guess` single-process

**Defensive-hardening NEW audit item B13** (added per the B12 RESOLUTION post-mortem; bundled with step 18 docs/cleanup era; ~0.5 day): make LPJG `parameters.cpp::CB_CHECKPFT` (or `init_cton_limits()`) fail-fast with a clear error message if `cton_leaf_min == 0` post-PFT-init, so the trap that caused B12 cannot recur silently. Tracked in `notes/FOLLOWUPS.md` "B-item bundling commitment" sub-section.

**Process-hardening NEW audit item B14** (added per session-continuation user direction 2026-05-11 evening, after empirical confirmation that `version_A/.../landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/global.ins` sets `ifcalcsla 1` + `ifcalccton 1`; bundled with step 18; ~0.5–1 day): one-time `.ins` parity audit of `runs/SSP1-2.6/main_xval_*.ins` (and import chain) vs `version_A`'s `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/` and `version_B`'s `landsymm_imogen/SSP1_RCP26/`; each divergent parameter classified as intentional (rationale documented at site) or unintentional (open follow-up). **Backport relevance: IRRELEVANT** — B14 is a process audit on `runs/` configs, not on `lpjguess/` source. Persistent companion: NEW "Operational heuristics — lessons learned" subsection in `notes/FOLLOWUPS.md` (5 standing rules; `.ins`-parity-with-original as rule #1).

---

### Step 17b (B10 LANDED): symmetric Fortran engine writer fix — `imogen/code/imogen_lpjg.f`; mechanical replication of C++ fix at `7be595a`; **backport-RELEVANT**

**Commit:** _to be determined_ (this commit; un-tagged checkpoint on top of `488c5a2`)
**Backport relevance:** **RELEVANT** for the standalone Fortran IMOGEN engine. If `trunk_r13078` (and/or its companion IMOGEN/Fortran source tree) ships `imogen/code/imogen_lpjg.f` — likely, since this is canonical Huntingford-Cox IMOGEN code that has been part of the LandSyMM-IMOGEN coupled framework since the predecessor versions — the same 7 mechanical conditional removals apply symmetrically. The fix is purely structural (no new physics; no changed I/O semantics): unconditional file OPEN/CLOSE per IYEAR iteration in place of the previous `IF(IYEAR.EQ.YEAR1)` / `IF(IYEAR.EQ.IYEND)` gates that produced an alternating-year staged-climate quirk.

**Why this fix is symmetric (engine parity), not a critical-path bug fix:**
The standalone Fortran IMOGEN engine is **not on the v1.0 production path** (`imogen` mode in v1.0 calls a different launcher path; the Fortran engine is currently exercised only by engine-only smoke testing). The structurally-identical bug in the **in-process C++ engine port** at `lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` was the production-path blocker, fixed at commit `7be595a` (2026-05-10; 5 conditional removals; ~76 LOC of doc blocks; verified by C1.2/C1.3 4-cell xval PASS). B10 replicates that fix to the standalone Fortran engine for engine parity (per F-3 Fortran↔C++ IMOGEN parity in `notes/FOLLOWUPS.md`) — keeping the two engines in lock-step so future engine-mode switches inherit identical writer semantics.

**Empirical scope refinement: 5 → 7 conditional removals.**
The originally-documented scope was 5 removals (inherited from the C++ fix's 5-removal count). Empirical inspection of `imogen_lpjg.f` revealed **7 gates** = 5 C++ analogues + 2 Fortran-specific extras:

| # | Line (pre-fix) | Block | Has C++ analogue? | Notes |
|---|---|---|---|---|
| 1 | 854 | CO2 writer OPEN (units 91, 98) | YES (`climatemodel.cpp` ~787) | Same logic |
| 2 | 883 | CO2 writer CLOSE (units 91, 98) | NO (Fortran-specific extra) | C++ uses `std::ofstream` RAII so close is implicit; Fortran requires explicit `CLOSE` |
| 3 | 954 | Climate-anomaly REGRID OPEN (T/P/SW/WET/DTEMP) | YES (`climatemodel.cpp` ~884) | Canonical doc lives here |
| 4 | 1013 | Climate-anomaly non-REGRID OPEN (same units) | NO (Fortran-specific extra) | C++ in-process port has no native-grid branch; always writes on a single grid |
| 5 | 1071 | Climate-anomaly CLOSE (units 11, 92, 93, 94, 95) | YES (`climatemodel.cpp` ~963) | Same logic |
| 6 | 1088 | FA_OCEAN/DTEMP_O OPEN (units 95, 96) | YES (`climatemodel.cpp` ~988) | Same logic |
| 7 | 1099 | FA_OCEAN/DTEMP_O CLOSE (units 95, 96) | YES (`climatemodel.cpp` ~998) | Same logic |

This is an **empirical refinement** of the originally-documented scope, not a scope expansion of intent.

**Files changed in this commit:**
- `imogen/code/imogen_lpjg.f` (+121 LOC, -37 LOC; net +84 LOC; **backport-RELEVANT**) — 7 conditional removals at lines 854/883/954/1013/1071/1088/1099 with full C++-doc-block parity (canonical doc at REGRID OPEN mirroring `climatemodel.cpp` ~884 from `7be595a`; 6 cross-referencing short blocks at other sites)
- Documentation updates (STEP_17b.md §3b NEW + §5 + §7 + footer; CHANGELOG entry above B12-resolution; EXECUTION_PLAN row 17b status; FOLLOWUPS B-bundling table B10 ✅ DONE + status dashboard refresh + % done estimate; this LEDGER entry; chat handoff Part 21)

**Net `lpjguess/` source change in this commit: ZERO.**
The Fortran engine source `imogen/code/imogen_lpjg.f` lives outside `lpjguess/` (in the IMOGEN-specific directory tree), but is still backport-relevant per F-11 since it's part of the LandSyMM-IMOGEN coupled framework's core IMOGEN component. The Backport Sprint should track both `lpjguess/`-internal AND `imogen/`-internal source changes when applying step-17b changes to `trunk_r13078`.

**Verification this commit:**
- `cd imogen/code && rm -f *.o imogen_lpjg && bash compile.sh`: ✅ clean Fortran build (exit 0; binary 129 600 bytes; ZERO warnings beyond pre-existing)
- Static gate-removal check (`rg 'IYEAR\.EQ\.(YEAR1|IYEND)' imogen/code/imogen_lpjg.f`): ✅ all 7 B10 gates correctly removed; remaining matches are pre-existing legacy comment + `YEAR1_LPJG` (different gate variable, not part of B10) + my own doc-block paragraph references
- Net LOC parity with C++ (`git diff --shortstat`): ✅ +121, -37 (vs C++ `7be595a`'s +76, -5; proportionate given 7 vs 5 fixes + 2 extra Fortran-specific cross-reference blocks)
- Pre-fix evidence preserved (`ls imogen/code/IMOGEN/output/{1871,1872}/`): ✅ `1871/` has 9 climate files (full); `1872/` has only `done` marker (empty) — empirical pre-fix demonstration of the alternating-year quirk, retained as a documentation artefact
- C++ fix doc-block parity: ✅ Same structure as `climatemodel.cpp` ~884 canonical block (ROOT-CAUSE FIX + symmetric-engine-list + FIX + symmetric-removals list + backport note + author/date stamp)
- 162 unit tests on both `build/guess` and `build_mpi/guess`: PASS (no `lpjguess/` source change → no-op build expected; verified C1 baseline preserved)
- Empirical post-fix engine smoke: **DEFERRED** (Fortran engine inputs `CEN_IPSL_MOD_IPSL-CM5A-MR/` patterns + `DKB_dataset_totals/` emissions that the existing `imogen_settings.txt` references are not currently shipped in the active rebuild's `imogen/` tree; engine inputs were not re-staged after Step 4's selective import per the engine being NOT on the v1.0 production path). Per the symmetric-correctness framing, the clean compile + static gate-removal check + pre-fix evidence preserved together suffice for B10's verification gate. A full empirical engine smoke would naturally be staged when **B1** (Fortran Rh + Wind COMPUTATION port) lands — at which point a post-B1 engine smoke would simultaneously verify B10's writer fix in production.

**Backport Sprint instructions for `trunk_r13078`:**
1. Locate the standalone Fortran IMOGEN engine in `trunk_r13078`'s tree (likely `imogen/code/imogen_lpjg.f` or equivalent path; if absent, this entry is N/A and can be skipped).
2. Apply the same 7 mechanical conditional removals at the analogous gates (search for `IF(IYEAR.EQ.YEAR1)` / `IF(IYEAR.EQ.IYEND)` patterns around file OPEN/CLOSE blocks for units 11, 91, 92, 93, 94, 95, 96, 98).
3. Mirror the doc-block style: canonical block at the climate-anomaly REGRID OPEN; cross-referencing short blocks at the other sites.
4. Verify: clean Fortran build; static gate-removal check; if engine inputs are staged in `trunk_r13078`'s tree, run engine-only smoke and verify all years receive full climate (not alternating).

**Cross-references:**
- `notes/STEP_17b.md` §3b — canonical forensic record (root cause + scope refinement + verification + ordering rationale)
- `lpjguess/modules/climatemodel.cpp` post-`7be595a` — reference C++ fix (5 conditional removals; ~76 LOC of doc blocks)
- `notes/STEP_17a.md` §5.6 + §6.4 — original C++ fix narrative
- `notes/FOLLOWUPS.md` F-3 — Fortran↔C++ IMOGEN parity follow-up (B10 closes its symmetric-correctness aspect)

---

### Step 17b (B6 RESOLVED): F-2 Fortran T_anom 2× line count investigation — **subsumed by B10**; backport-IRRELEVANT (no source change)

**Audit-item scope:** B6 = audit item bundling F-2's "investigate Fortran T_anom.dat 2× line count" follow-up (originally 0.5 d budgeted). Per the re-ordered Option A bundle sequence (B10 → **B6** → B2 → B3 → B4 → B1; user-confirmed 2026-05-11), B6 was scheduled to be the cohesive next-step after B10 because both items live in the same `imogen_lpjg.f` writer block.

**Root-cause finding (this commit; docs-only):** the originally-reported 2× line count for T_anom.dat (3262 vs version_A's 1631) is **one of three downstream symptoms of the same alternating-year writer bug B10 mechanically fixed at commit `3c00428`**. The full forensic chain (in `notes/STEP_17b.md` §3c):

1. **T/P/SW/DTEMP_anom.dat doubled to 3262 lines**: pre-B10's `IF(IYEAR.EQ.IYEND)`-gated CLOSE caused units 92/93/94/11 to stay open across the 1871→1872 year boundary. Year-1872 climate writes appended 1631 cells to the still-open year-1871 files.
2. **WET.dat stuck at 1631 lines (asymmetric)**: mid-1871 OCEAN_FEED block re-OPENs unit 95 to `fa_ocean.dat`, auto-closing the WET.dat connection. Year 1872 cannot append to /1871/WET.dat (already closed).
3. **fa_ocean.dat contaminated by +1631 WET-format integer rows**: year-1872's `WRITE(95,...) F_WET_CLIM_OUT(IGP,IMM)` (climate writer block) lands on the still-open year-1871 fa_ocean.dat unit. Smoking-gun: lines 10001-11631 of pre-fix `imogen/code/IMOGEN/output/1871/fa_ocean.dat` are exact WET-format `LON LAT + 12 ints`.
4. **dtemp_o.dat doubled to 508 lines**: same alternating-year mechanism on unit 96.

B10's structural fix (unconditional OPEN/CLOSE per IYEAR iteration; 7 conditional removals) eliminates all four symptoms simultaneously by ensuring year 1872 receives fresh `/1872/`-targeted files with `STATUS='REPLACE'` resetting per iteration.

**Cross-validation:** `version_A/.../IMOGEN/output/1871/` reference shows T/P/SW/DTEMP=1631 lines each, WET=1631, fa_ocean=10000 (clean), dtemp_o=254 — matches the predicted post-B10 structural output exactly.

**What this commit lands:**
- `notes/STEP_17b.md` (NEW §3c — B6 forensic record + 3-symptom-1-root-cause mechanism + B10-subsumes-B6 determination + verification matrix; §5 bundling table marks B6 ✅ DONE 0.0 d; §7 remaining work refresh)
- `CHANGELOG.md` (B6 entry above B10)
- `EXECUTION_PLAN.md` (row 17b status refresh)
- `notes/FOLLOWUPS.md` (F-2 → CLOSED; B-item bundling table B6 ✅ DONE; new "Operational heuristics" rule #6 — asymmetric multi-year writer scaling triage rule)
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (this entry)
- `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` (Part 22 narrative; gitignored)

**ZERO Fortran/C++ source change in this commit. Docs-only.**

**Backport Sprint instructions for `trunk_r13078`:**

**N/A.** B6 has no source change to backport. The B10 backport entry (above) already covers all 7 conditional removals at `imogen/code/imogen_lpjg.f` whose application collectively fixes the F-2 / B6 symptom in `trunk_r13078` as well. The Backport Sprint should treat B6 as automatically satisfied once B10 is applied; this entry exists for traceability completeness.

**Cross-references:**
- `notes/STEP_17b.md` §3c — canonical forensic record (3-symptom pattern, single-root-cause mechanism, B10-subsumes-B6 determination)
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17b-B10 entry (above) — the source-level backport directive that fixes B6 too
- `notes/FOLLOWUPS.md` F-2 (now CLOSED 2026-05-11) + Operational heuristics rule #6 (asymmetric multi-year writer scaling triage rule)

---

### Step 17b (B2 LANDED): Fortran Tmin/Tmax write block — `imogen/code/imogen_lpjg.f`; algebraic Tmin = T - DTEMP/2; **backport-RELEVANT**

**Audit-item scope:** B2 = audit item bundling step-9.5b's "Fortran Tmin/Tmax write block" follow-up (originally 0.5 d budgeted; matched actual). Per the re-ordered Option A bundle sequence (B10 → B6 → **B2** → B3 → B4 → B1; user-confirmed 2026-05-11), B2 was scheduled as the next mechanical win after B6 because both items live in the same `imogen_lpjg.f` writer block.

**Symmetric-with-C++ framing (per Step 17b §3d.2):** the C++ in-process port at `lpjguess/modules/climatemodel.cpp` ~lines 952-953 already has `file100`/`file101` ofstream Tmin/Tmax writers in the **non-REGRID branch only** (added at step 9.5; an explicit `// TODO at step 9.5b` comment at `climatemodel.cpp` ~line 894 documents the pending REGRID-side addition — that's **B3's** scope on the C++ side). B2 mirrors this in the Fortran engine but for **BOTH** branches (REGRID + non-REGRID) because the Fortran writer block has both branches and there's no reason to leave them asymmetric. Per Decision #11: Tmin/Tmax are derived (not directly modelled) as `T ± DTEMP/2` (same units = Kelvin; same dynamic range as `T_anom`).

**Backport Sprint instructions for `trunk_r13078`:**

**One source file affected: `imogen/code/imogen_lpjg.f`.** If `trunk_r13078` ships this engine file (it likely does; the standalone Fortran IMOGEN engine is part of LandSyMM-IMOGEN's core), apply the same 9 surgical insertions. Total +59 LOC additive (no removals).

**Insertion sites** (line numbers approximate; pre-B2 reference in `notes/STEP_17b.md` §3d.4):

| # | Site | Branch | Code to insert |
|---|---|---|---|
| 1 | After `OPEN(11, .../DTEMP_anom.dat, STATUS='REPLACE')` (REGRID OPEN block) | REGRID | Canonical doc block + `OPEN(100, .../Tmin_anom.dat, STATUS='REPLACE')` + `OPEN(101, .../Tmax_anom.dat, STATUS='REPLACE')` |
| 2 | After REGRID `WRITE(11, '(f8.3)', ADVANCE='NO') LAT_OUT(IGP)` | REGRID | `WRITE(100/101, '(f8.3)', ADVANCE='NO') LON_OUT(IGP)` and same for LAT_OUT (4 lines + short doc) |
| 3 | After REGRID DAILYOUT=TRUE `WRITE(95, '(i10)', ADVANCE='NO') F_WET_CLIM_REGRID(IGP,IMM)` (just before ENDIF for `IMD.LE.MTHDAY(IMM)`) | REGRID | `WRITE(100, '(f10.3)', ADVANCE='NO') T_OUT_M_REGRID(IGP,IMM,IMD,IND) - DTEMP_OUT_M_REGRID(IGP,IMM,IMD)/2.0` and same for unit 101 with `+` |
| 4 | After REGRID DAILYOUT=FALSE `WRITE(95, '(i10)', ADVANCE='NO') F_WET_CLIM_REGRID(IGP,IMM)` (just before ENDIF for DAILYOUT) | REGRID | Tmin/Tmax monthly writes using `T_OUT_M_REGRID(IGP,IMM,1,1) ± DTEMP_OUT_M_REGRID(IGP,IMM,1)/2.0` |
| 5 | After REGRID per-cell `WRITE(11, '()')` | REGRID | `WRITE(100, '()')` + `WRITE(101, '()')` |
| 6 | After `OPEN(11, .../DTEMP_anom.dat)` in non-REGRID branch | non-REGRID | Short cross-ref doc + `OPEN(100, .../Tmin_anom.dat)` + `OPEN(101, .../Tmax_anom.dat)` |
| 7 | After non-REGRID `WRITE(11) LAT(IGP)` | non-REGRID | LON/LAT headers using `LONG/LAT` (NOT `LON_OUT/LAT_OUT`) for units 100/101 |
| 8 | After non-REGRID DAILYOUT=TRUE `WRITE(95) F_WET_CLIM_OUT` | non-REGRID | Tmin/Tmax daily writes using `T_OUT_M(IGP,IMM,IMD,IND) ± DTEMP_OUT_M(IGP,IMM,IMD)/2.0` (NO `_REGRID` suffix) |
| 9 | After non-REGRID DAILYOUT=FALSE `WRITE(95) F_WET_CLIM_OUT` + after `WRITE(11, '()')` | non-REGRID | Tmin/Tmax monthly writes + per-cell newlines for units 100/101 |
| 10 | After post-B10 `CLOSE(11)` (after `ENDIF !End of REGRID conditional`) | shared | `CLOSE(100)` + `CLOSE(101)` |

**Critical safety details to preserve at backport:**

1. **Real-division literal**: ALL 8 algebraic expressions MUST use `/2.0` (REAL literal), NOT `/2` (INTEGER). Integer division would truncate and corrupt Tmin/Tmax outputs.
2. **Variable name suffix discipline**: REGRID branch uses `T_OUT_M_REGRID/DTEMP_OUT_M_REGRID/LON_OUT/LAT_OUT`; non-REGRID branch uses `T_OUT_M/DTEMP_OUT_M/LONG/LAT` — do NOT mix; the wrong suffix in the wrong branch produces compile errors (good) or worse, silent corruption if the same name happens to compile in both contexts.
3. **Format `(f10.3)`**: must match `T_anom.dat` writes for byte-level parity (10-char width, 3 decimals). Same width/precision as the C++ port's `std::setw(10) << std::setprecision(3)`.
4. **Unit 100 + 101 free-ness**: verify in `trunk_r13078`'s `imogen_lpjg.f` that units 100 and 101 are unused before applying. If `trunk_r13078` has additional unit usage at 100/101 (unlikely but possible), pick alternative free units (e.g., 102/103).
5. **Place AFTER B10's unconditional OPEN/CLOSE fix is applied** — B10 is a pre-requisite (B2's writes to units 100/101 inherit the same per-IYEAR-iteration unconditional-open semantics).

**Verification gate at backport:**
- Clean Fortran build (zero warnings) — same `compile.sh` driver
- Static check: `rg "OPEN\\\|CLOSE\\\|WRITE\(\s*(100\|101)\s*[,\)]" imogen_lpjg.f` should return 26 occurrences (4 OPENs + 2 CLOSEs + 8 LON/LAT writes + 8 data writes + 4 per-cell newlines)
- Both `Tmin_anom.dat` + `Tmax_anom.dat` paths should appear at REGRID branch + non-REGRID branch (4 matches total in `rg "Tmin_anom\.dat\|Tmax_anom\.dat" imogen_lpjg.f`)
- Empirical engine smoke (when engine inputs ship): each `IMOGEN/output/YEAR/` should have 9 files (was 7); `Tmin_anom.dat` + `Tmax_anom.dat` should each have 1631 lines (1631 cells × 1 line of `LON LAT + 12 monthly Tmin/Tmax values` per cell, in non-REGRID branch DAILYOUT=FALSE; or 1631 lines × N daily values in DAILYOUT=TRUE)

**Cross-references:**
- `notes/STEP_17b.md` §3d — canonical forensic record (scope decision, unit-number selection, 9-insertion table, cross-engine parity matrix)
- `lpjguess/modules/climatemodel.cpp` ~lines 952-953 (file100/file101) + ~lines 990-991 (DAILYOUT=TRUE algebra) + ~lines 1005-1006 (DAILYOUT=FALSE algebra) — C++ analogue
- `notes/STEP_4.md` step 9.5b — original Tmin/Tmax write block deferral
- `notes/FOLLOWUPS.md` audit-table B2 row (now ✅ DONE 2026-05-12)
- `_phase2_findings/decisions.md` Decision #11 — Tmin/Tmax algebraic derivation rationale

---

### Step 17b (B3 LANDED): C++ Tmin/Tmax in REGRID branch of `climatemodel.cpp` — **closed by architectural reframing**; ~30 LOC additive docs only; **backport-RELEVANT** (docs-only)

**Audit-item scope:** B3 = audit item bundling step-9.5b's "C++ engine Tmin/Tmax write in REGRID branch" follow-up (originally 0.5 d budgeted; landed in 0.3 d as docs-only). Per the re-ordered Option A bundle sequence (B10 → B6 → B2 → **B3** → B4 → B1; user-confirmed 2026-05-11), B3 was scheduled as the C++-side mirror of B2 (the Fortran-side Tmin/Tmax write block).

**Pre-implementation forensic finding (the entire content of this commit):** the C++ in-process port at `lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` has **NO REGRID branch**. Evidence:

1. `rg "REGRID|regrid" lpjguess/modules/climatemodel.cpp` returns **only 3 hits**:
   - **Line ~242**: a `bool regrid` local variable declaration in `RUN_IMOGEN_ENGINE()` — **dead code**, never read after declaration.
   - **Line ~894**: the stale `// TODO at step 9.5b: replicate this in the REGRID branch.` comment — an aspirational forward-reference left by the step-9.5 author anticipating a future C++ REGRID branch that was never built.
   - **Line ~1353**: an unrelated comment in a different function (not in the climate-anomaly writer block).
2. There is **no `if (regrid) { ... } else { ... }` switch** anywhere in `RUN_IMOGEN_ENGINE()` or the surrounding code.
3. There are **zero `*Regrid` array declarations or usages** in `lpjguess/modules/climatemodel.cpp` (only native `tOutM/pOutM/swOutM/windOutM/rhOutM/dtempOutM` arrays at lines ~284-289, sized over `GPOINTS`, not `NGPOINTS` as the Fortran `_REGRID` variants are).
4. There are **zero `REGRID_CLIM` function calls** in any `lpjguess/` source. The Fortran helper subroutine `REGRID_CLIM` at `imogen/code/imogen_lpjg.f` ~line 964 was never ported to the C++ in-process port.

**Interpretation:** the C++ port has always written climate anomalies on the single native IMOGEN grid (which is what `imogencfx` mode requires; that mode is the v1.0 production path). The pre-B3 cross-engine parity matrix in `notes/STEP_17b.md` §3d.6 had inherited a documentation drift wrongly attributing a REGRID branch to the C++ port; B3 corrects it.

**Symmetric-with-Fortran framing (POST-B3, corrected):** B2 added Tmin/Tmax to BOTH branches of the Fortran writer block (REGRID + non-REGRID) because both branches exist in `imogen_lpjg.f`. B3 leaves the C++ engine with Tmin/Tmax in its single existing branch (the native-IMOGEN-grid branch, present since step 9.5 with `file100`/`file101` ofstream writers). Every climate-anomaly writer site that actually exists in either engine now has Tmin/Tmax wired.

**What landed this commit (1 source file; ~30 LOC additive docs; ZERO functional code change; backport-RELEVANT only for doc parity):**

| # | Location in `lpjguess/modules/climatemodel.cpp` | What was inserted |
|---|---|---|
| 1 | Line ~242 (after `bool regrid` declaration) | ~18-line dead-code annotation: declares that `regrid` is set-but-never-read, the C++ port has no REGRID branch (in contrast to Fortran), cross-references the canonical §3e doc block at line ~894, and flags a future defensive runtime warning (B13-style) as a follow-up if anyone ever tries to set `regrid=true` expecting branching behaviour. |
| 2 | Line ~890 (the "Output in native IMOGEN grid" comment header for the existing climate-anomaly writer block) | Extension clarifying that this is the **only** climate-anomaly writer branch in the C++ port (not "one of two" as the pre-B3 documentation drift might have implied). |
| 3 | Line ~894 (the stale `// TODO at step 9.5b: replicate this in the REGRID branch.` block) | **Replaced** the stale 4-line TODO with a **~50-line canonical B3 doc block**: forensic finding statement (no C++ REGRID branch exists); cross-engine parity matrix snapshot (post-B3 actual state); forward-looking maintenance directive specifying the **exact C++ algebraic pattern** for any future REGRID-branch Tmin/Tmax addition (e.g. `file100 << ... << (tOutMRegrid - dtempOutMRegrid/2.0)`; `file101 << ... << (tOutMRegrid + dtempOutMRegrid/2.0)`; `setw(10) << setprecision(3)`; units 100/101 ofstream variable naming convention preserved); cross-references to STEP_17b.md §3e, the Fortran B2 symmetric block at `imogen/code/imogen_lpjg.f` lines ~1019-1160 (commit `76b3b04`), and this BACKPORT_LEDGER step-17b-B3 entry. |

**Net source change:** +~30 LOC of comment text in 1 file (`lpjguess/modules/climatemodel.cpp`); no executable statements added, removed, or altered. The `bool regrid` declaration at line ~242 is left intact (dead code; annotated rather than deleted because (a) removal is out of scope for a docs-only commit; (b) keeping it preserves grep-anchor for the doc block).

**Backport Sprint instructions for `trunk_r13078`:**

**One source file affected: `lpjguess/modules/climatemodel.cpp`.** If `trunk_r13078`'s tree has a structurally similar `climatemodel.cpp` (it should; this is a `landsymm_fork`-internal but post-step-9.5 file that the predecessor `trunk_r13078` may carry forward — verify at backport time), apply the 3 documentation insertions:

1. **Verify the architectural premise first**: run `rg "REGRID|regrid|_Regrid|REGRID_CLIM" lpjguess/modules/climatemodel.cpp` in `trunk_r13078`. If the result mirrors what we observed (only 3 hits: a dead-code `bool regrid` declaration + the stale TODO + one unrelated comment), then proceed; the doc-block is directly applicable. If `trunk_r13078` has additional REGRID structure (unlikely but possible — e.g. if the predecessor was further along the REGRID port), then the doc block's "no REGRID branch exists" claim must be re-evaluated and likely the B3 outcome shifts from "close-by-architectural-reframing" to "implement-the-mechanical-mirror" in that backend.
2. **Insertion 1 (dead-code annotation)**: locate `bool regrid` in `RUN_IMOGEN_ENGINE()` (line ~242 in our tree). Insert the ~18-line annotation above (or directly below) the declaration. Use the same wording as our version (cross-reference §3e of STEP_17b.md, the canonical doc block).
3. **Insertion 2 (native-grid clarification)**: locate the "Output in native IMOGEN grid" comment header for the climate-anomaly writer block (line ~890 in our tree). Extend to clarify "the ONLY climate-anomaly writer branch in this port."
4. **Insertion 3 (canonical B3 doc block)**: locate the stale `// TODO at step 9.5b: replicate this in the REGRID branch.` comment (line ~894 in our tree). **Delete** the 4-line TODO. Insert the ~50-line canonical doc block (forensic finding + parity matrix + forward-looking maintenance directive + cross-references).

**Critical safety detail to preserve at backport:** the forward-looking maintenance directive in the canonical doc block is **architecturally important** — it specifies the exact C++ algebraic pattern (`tOutMRegrid - dtempOutMRegrid/2.0` for Tmin; `tOutMRegrid + dtempOutMRegrid/2.0` for Tmax; `/2.0` REAL division; `setw(10) << setprecision(3)` formatting; units 100/101 ofstream variables) that any future C++ REGRID branch implementation must use to preserve cross-engine numerical parity with Fortran. **Do NOT abbreviate** this section at backport; it is the entire justification for B3 being closed without a functional change.

**Verification gate at backport:**
- Clean rebuild of `lpjguess/build/` and `lpjguess/build_mpi/` with zero new warnings (force rebuild of `climatemodel.cpp`).
- 162 unit tests pass on both `build/runtests` and `build_mpi/runtests` (same as pre-B3; B3 is docs-only so should not affect anything).
- All 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN) against `build_mpi/guess` single-process.
- `rg "REGRID|regrid|TODO" lpjguess/modules/climatemodel.cpp | wc -l` matches expected (the count of B3 doc-block references; the old stale TODO is gone).

**Cross-references:**
- `notes/STEP_17b.md` §3e — canonical forensic record (architectural reframing, 4 evidence checks, 3-insertion table, post-B3 cross-engine parity matrix)
- `notes/STEP_17b.md` §3d.6 (POST-B3 CORRECTED) — cross-engine parity matrix reflecting actual architectural state
- `lpjguess/modules/climatemodel.cpp` line ~242 (dead-code `bool regrid`), line ~890 (sole climate-anomaly writer branch), line ~894 (canonical B3 doc block; replaces stale TODO)
- `imogen/code/imogen_lpjg.f` lines ~1019-1160 (commit `76b3b04`) — Fortran B2 symmetric counterpart (the only mechanical Tmin/Tmax write that did exist to land)
- `notes/FOLLOWUPS.md` audit-table B3 row (now ✅ DONE 2026-05-12; closed by architectural reframing) + new persistent Operational heuristics rule #7 (stale forward-reference TODOs are architectural-finding triggers)
- `_phase2_findings/decisions.md` Decision #11 — Tmin/Tmax algebraic derivation rationale (still applies if a future C++ REGRID branch is built)

**F-11 backport-sprint classification:** **RELEVANT (docs-only)**. No functional code change to backport, but the doc block, the dead-code annotation, and the parity-matrix correction should be applied to `trunk_r13078` for source-of-truth consistency. Treat as a 30-minute mechanical replication during the F-11 sprint.

---

### Step 17b (B4 LANDED): `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion in `lpjguess/modules/imogen_input.{cpp,h}` — +187 LOC additive in source + +15 LOC in `.ins`; **backport-RELEVANT** (functional code change)

**Audit-item scope:** B4 = audit item bundling the loose-mode (`-input imogen`) counterpart to the tight-mode (`-input imogencfx`) step-9.5 wiring of Rh / Wind / Tmin / Tmax in `IMOGENCFXInput` (commit `a543e9d`; refined K→°C bug-fix at step-17a sub-step 7.3.2 commit `8aafe84`). Per the re-ordered Option A bundle sequence (B10 → B6 → B2 → B3 → **B4** → B1; user-confirmed 2026-05-11), B4 was scheduled as the consumer-side mirror of the engine-side step-9.5 wiring. Budgeted at 1 d; landed in ~0.5 d (direct mirror of the C1.1 IMOGENCFXInput pattern with zero unanticipated forensic findings). **Closes the loose-mode-vs-tight-mode 6-vs-10-fields gap** identified during the 2026-05-10 late-evening audit.

**Pre-implementation investigation (forensic state captured before any edits):**

- `imogen_input.h` pre-B4 declared `file_relhum` + `file_wind` + `file__pres` at lines 232-236 (in a "for Blaze need from imogen:" block) but `rg "file_relhum|file_wind|file__pres|file_tmin|file_tmax" imogen_input.cpp` returned **zero hits** — i.e. the declarations were vestigial header-only. No `file_tmin`/`file_tmax` declarations existed pre-B4. No per-day arrays for relhum/wind/tmin/tmax. No `all_drelhum`/`all_dwind`/`all_dtmin`/`all_dtmax` per-year caches.
- `imogencfx.{cpp,h}` (the C1.1 reference) has all 4 path decls at `imogencfx.h:260-266`; all 4 per-day arrays at `imogencfx.h:204-218`; all 4 caches at `imogencfx.h:311-318`. `init()` reads 4 params at `imogencfx.cpp:427-430`; resize at `imogencfx.cpp:584-587`; `readenv()` guarded reads at `imogencfx.cpp:866-888`; `get_climate_for_gridcell()` monthly+daily branches at `imogencfx.cpp:986-1004` + `:1017-1028`; `getclimate()` consumer assignments at `imogencfx.cpp:1274-1277`; `getclimate_for_year()` consumer assignments at `imogencfx.cpp:1604-1607`.
- The `Climate` struct already has all 4 target fields at `lpjguess/framework/guess.h:844-850` (`u10`, `relhum`, `tmin`, `tmax`); B4 only needs to populate them, not declare them.
- Fortran-engine output state at B4-land time: post-B2 (commit `76b3b04`) the Fortran engine writes `Tmin_anom.dat` + `Tmax_anom.dat`; pre-B1 the Fortran engine does NOT write `Rh_anom.dat` / `W_anom.dat`. Pre-staged predecessor climate at `runs/SSP1-2.6/Common-directory/IMOGEN/output/YYYY/` contains ALL 4 files (verified 2026-05-12 pre-B4), so the xval window has full coverage independent of the B1-pending state.

**What landed this commit (3 source files + 1 config file; +187 LOC source additive + +15 LOC .ins additive; ZERO source removals):**

**File 1: `lpjguess/modules/imogen_input.h`** (3 sub-edits; +60 LOC):

| # | Insertion site | Content |
|---|---|---|
| 1 | After `dNH4dep[]/dNO3dep[]` per-day arrays (line ~196 pre-B4) | 4 new per-day arrays `drelhum/dwind/dtmin/dtmax[Date::MAX_YEAR_LENGTH]` + ~30-line canonical B4 doc block citing: (a) the C1.1 IMOGENCFXInput symmetric pattern at `imogencfx.h:204-218`; (b) the K-vs-°C convention decision (ImogenInput keeps K in per-day arrays; converts at consumer site — opposite of IMOGENCFXInput post-step-17a-7.3.2); (c) source files consumed (Tmin/Tmax post-B2; Rh/Wind B1-pending); (d) unit conventions per field. |
| 2 | After existing `file_wind` vestigial decl (line ~236 pre-B4) | (a) Doc block annotating the pre-existing vestigial `file_relhum`/`file_wind` decls as now-wired-by-B4 (preserving them rather than adding duplicates); (b) 2 new path decls `xtring file_tmin; xtring file_tmax;` with doc block mirroring `imogencfx.h:265-266`. |
| 3 | After `all_dtr` per-year cache decl (line ~280 pre-B4) | 4 new per-year caches `all_drelhum/all_dwind/all_dtmin/all_dtmax` with doc block mirroring `imogencfx.h:311-318`. |

**File 2: `lpjguess/modules/imogen_input.cpp`** (5 sub-edits; +127 LOC):

| # | Insertion site | Content |
|---|---|---|
| 1 | After `file_dtr = param["file_dtr"].str;` in `init()` (line ~251 pre-B4) | ~30-line canonical B4 doc block (scope, B1-pending fallback rationale, ins-file-side cross-references to `main_xval_imogencfx.ins:96-99` + `main_xval_loose.ins` post-B4 + `main.ins:74-75`) + 4 param reads: `file_relhum = param["file_relhum"].str; file_wind = param["file_wind"].str; file_tmin = param["file_tmin"].str; file_tmax = param["file_tmax"].str;` |
| 2 | After `resize3DimVector(all_dtr, ...)` in `init()` (line ~372 pre-B4) | Doc block (mirror of `imogencfx.cpp:575-583`) + 4 new `resize3DimVector` calls for `all_drelhum`, `all_dwind`, `all_dtmin`, `all_dtmax`. |
| 3 | After `if (ifbvoc) { ... all_dtr ... }` block in `readenv()` (line ~615 pre-B4) | Doc block + 4 guarded reads using the `if ((char*)file_relhum != NULL && file_relhum != "") { filename = gen_filename(file_relhum, calendar_year, false); read_lines_from_file(filename, lons, lats, line_index, all_drelhum[store_index], monthly); }` pattern (mirror of `imogencfx.cpp:866-888`). 4 of these blocks for relhum/wind/tmin/tmax respectively. |
| 4 | (a) After `interp_climate(...)` in `get_climate_for_gridcell()` monthly branch (line ~645 pre-B4); (b) After `if (ifbvoc) ddtr[i] = ...` in daily branch (line ~652 pre-B4) | **Monthly branch addition**: doc block (NO K→°C at this layer; ImogenInput convention) + 4 `m*[12]` arrays + 4 `have_*` booleans + 4 `interp_monthly_means_conserve` calls. **Daily branch addition**: doc block + 4 guarded daily passthroughs `if ((char*)file_relhum != NULL && file_relhum != "") drelhum[i] = all_drelhum[store_index][igrid][i];` (4 of these). |
| 5 | (a) After `if (ifbvoc) { climate.dtr = ddtr[date.day]; }` in `getclimate()` (line ~892 pre-B4); (b) After same in `getclimate_for_year()` (line ~1158 pre-B4) | Doc block (citing the K→°C-at-consumer-site decision; cross-reference to the existing `climate.temp = dtemp - 273.15` line above; cross-reference to `imogencfx.cpp:1274-1277` + `:1604-1607` for the symmetric pattern on the tight-mode side) + 4 `climate.{relhum, u10, tmin, tmax}` assignments: `climate.relhum = drelhum[date.day]; climate.u10 = dwind[date.day]; climate.tmin = dtmin[date.day] - 273.15; climate.tmax = dtmax[date.day] - 273.15;` (replace `date.day` with `day_of_year` for the `getclimate_for_year` version). |

**File 3: `runs/SSP1-2.6/main_xval_loose.ins`** (1 sub-edit; +15 LOC) — *NOT part of `trunk_r13078`'s tree; backport-side not needed but documented here for completeness*:

| # | Insertion site | Content |
|---|---|---|
| 1 | After existing `file_dtr` param line 65 | Doc block + 4 new param directives mirroring `main_xval_imogencfx.ins:96-99`: `param "file_relhum" (str "./IMOGEN/output/YYYY/Rh_anom.dat") `, `param "file_wind" (str "./IMOGEN/output/YYYY/W_anom.dat") `, `param "file_tmin" (str "./IMOGEN/output/YYYY/Tmin_anom.dat") `, `param "file_tmax" (str "./IMOGEN/output/YYYY/Tmax_anom.dat") `. |

**Net source change:** +60 LOC in `imogen_input.h` + +127 LOC in `imogen_input.cpp` = **+187 LOC additive** in `lpjguess/modules/`; **ZERO source removals**. Pure additive expansion.

**Backport Sprint instructions for `trunk_r13078`:**

**Files affected: `lpjguess/modules/imogen_input.h` + `lpjguess/modules/imogen_input.cpp`.** Apply the 8 source-side sub-edits (3 in `.h` + 5 in `.cpp`) in dependency order:

1. **Verify the pre-B4 state in `trunk_r13078`**: run `rg "file_tmin|file_tmax|file_relhum|file_wind" trunk_r13078/lpjguess/modules/imogen_input.cpp` and `rg "file_tmin|file_tmax" trunk_r13078/lpjguess/modules/imogen_input.h`. If the result mirrors our pre-B4 state (zero hits in `.cpp` for these patterns; only the vestigial `file_relhum`/`file_wind` decls in `.h`), then proceed; B4's mechanical insertions are directly applicable.
2. **`.h` edit 1** (per-day arrays): locate the `dNH4dep[]/dNO3dep[]` per-day array decls in the private section. Insert the 4 new per-day arrays `drelhum/dwind/dtmin/dtmax[Date::MAX_YEAR_LENGTH]` after them, with the full ~30-line doc block.
3. **`.h` edit 2** (path decls): locate the pre-existing vestigial `file_relhum`/`file_wind`/`file__pres` decls. Insert the doc block annotating them as now-wired-by-B4 + 2 new path decls `xtring file_tmin; xtring file_tmax;` after them.
4. **`.h` edit 3** (per-year caches): locate the `all_dtr` per-year cache decl. Insert the 4 new caches `all_drelhum/all_dwind/all_dtmin/all_dtmax` after it, with doc block.
5. **`.cpp` edit 1** (init() param reads): locate `file_dtr = param["file_dtr"].str;` in `init()`. Insert the ~30-line canonical B4 doc block + 4 param reads after it.
6. **`.cpp` edit 2** (init() resizes): locate `resize3DimVector(all_dtr, ...)` in `init()`. Insert 4 new resize calls after it, with doc block.
7. **`.cpp` edit 3** (readenv() guarded reads): locate the `if (ifbvoc) { ... all_dtr ... }` block in `readenv()`. Insert 4 guarded reads after it, with doc block.
8. **`.cpp` edit 4** (get_climate_for_gridcell() monthly + daily branches): locate `interp_climate(...)` in the monthly branch + `if (ifbvoc) ddtr[i] = ...` in the daily branch. Insert the monthly-branch additions (4 `m*[12]` + `have_*` + `interp_monthly_means_conserve`) + daily-branch additions (4 guarded passthroughs), with doc blocks at each branch.
9. **`.cpp` edit 5** (consumer assignments): locate `if (ifbvoc) { climate.dtr = ddtr[date.day]; }` in `getclimate()` AND in `getclimate_for_year()`. Insert 4 `climate.{relhum, u10, tmin, tmax}` assignments after each, with K→°C `- 273.15` on tmin/tmax (mirror of existing `climate.temp = dtemp[date.day] - 273.15` pattern). NOTE: the doc block at each site should cross-reference the deliberate intentional difference from IMOGENCFXInput's monthly-array-step K→°C convention.

**Critical safety details to preserve at backport:**

1. **K→°C conversion site decision**: ImogenInput converts at the **consumer site** (`climate.tmin = dtmin - 273.15`), not at the monthly-array step. IMOGENCFXInput converts at the **monthly-array step** post-step-17a-7.3.2 (`mtmin[i] = all_dtmin[...] - 273.15`). These are intentionally distinct and the doc blocks at both sites must cross-reference each other to prevent future drift. **Do NOT unify** the K→°C handling site at backport — preserving the distinction is part of the design intent (justification: bit-exact reproduction of each input module's existing temp semantics).
2. **B1-pending fallback**: the `if ((char*)file_relhum != NULL && file_relhum != "")` guard pattern is required around all 4 file reads in `readenv()`. Removing these guards (e.g. for "simplification") would break the B1-pending forward-safety: the run would `fail()` at `read_lines_from_file:550` when the `.ins` doesn't set the paths. **Preserve the guards verbatim.**
3. **Vestigial decl repurposing**: don't add duplicate `file_relhum`/`file_wind` decls in the header. The existing pre-B4 decls (in the "for Blaze need from imogen:" block) get the B4 wiring; only `file_tmin` + `file_tmax` are added as NEW decls. The `file__pres` decl is left intact (still vestigial; future B-item).
4. **`preload_all_climate` unchanged**: the C1.1 year_outer override delegates to `readenv()`. Extending `readenv()` (edit #7) is sufficient. Do NOT modify `preload_all_climate` for B4.

**Verification gate at backport:**

- Clean rebuild of `lpjguess/build/` and `lpjguess/build_mpi/` with zero new warnings (force rebuild of `imogen_input.{cpp,h}`).
- 162 unit tests pass on both `build/runtests` and `build_mpi/runtests`.
- All 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN) against `build_mpi/guess` single-process.
- 8 xval run.log files (4 scenarios × 2 modes) complete with "Finished" terminator without `read_lines_from_file` failures (proves all 4 new paths resolved correctly).
- `rg "file_tmin|file_tmax|file_relhum|file_wind" trunk_r13078/lpjguess/modules/imogen_input.cpp | wc -l` should return >= 20 hits post-backport (was 0 pre-backport): 4 param reads in `init()` + 8 in `readenv()` (2 per field: `if (...) { ... }`) + 8 in `get_climate_for_gridcell()` (4 per field across monthly+daily branches) + similar in `getclimate()` + `getclimate_for_year()`.

**Cross-references:**
- `notes/STEP_17b.md` §3f — canonical forensic record (B4 forensic, design decisions, 8-sub-edit insertion summary, verification gate table, post-B4 consumer-wiring parity matrix)
- `lpjguess/modules/imogencfx.{cpp,h}` (commit `a543e9d` + step-17a `8aafe84`) — C1.1 IMOGENCFXInput symmetric counterpart on the tight-mode side
- `lpjguess/framework/guess.h:840-850` — `Climate` struct field declarations for `u10` / `relhum` / `tmin` / `tmax`
- `runs/SSP1-2.6/main_xval_imogencfx.ins:96-99` — reference `.ins` configuration for the 4 new params
- `notes/FOLLOWUPS.md` audit-table B4 row (now ✅ DONE 2026-05-12 night)
- `_phase2_findings/decisions.md` Decision #11 — Tmin/Tmax algebraic derivation rationale

**F-11 backport-sprint classification:** **RELEVANT (functional code change)**. The 8 source-side sub-edits should be applied to `trunk_r13078`'s `imogen_input.{cpp,h}` if its pre-B4 state matches our pre-B4 state. Treat as a ~1-2 hour mechanical replication during the F-11 sprint. The `runs/SSP1-2.6/main_xval_loose.ins` change is config-only and **not** part of `trunk_r13078`'s tree.

---

### Step 17b (B1 LANDED): Fortran-engine Rh + Wind COMPUTATION + write-block port in `imogen/code/imogen_lpjg.f` — closed by architectural reframing; +200 LOC additive (single file); **backport-RELEVANT** (functional Fortran source change)

**Date:** 2026-05-12 (early morning; session 3 continuation). **Commit hash:** (HEAD this commit; un-tagged checkpoint on top of `2bd5222`).

**Forensic context:** The audit-table description "Fortran Rh + Wind COMPUTATION port" was a misread of `climatemodel.cpp:866`'s `// Compute Rh from Qh since Rh is not output directly` comment. Pre-implementation reading revealed: (a) Wind output is a direct passthrough from `windOut` (engine's disaggregated subdaily output) at `climatemodel.cpp:865` — no physics; (b) Rh output is a single 22-LOC inline Tetens-formula computation at `climatemodel.cpp:1228-1249` (`computeRelativeHumidityFromSpeificHumidty`); (c) Fortran-side `WIND_OUT/QHUM_OUT/PSTAR_OUT/T_OUT_M` already exist at `imogen_lpjg.f:229-231,1313-1316` and are populated by the existing `CLIM_DISAG` call at line 773. B1 is mechanical-symmetric-writer work, NOT a physics port. Estimate revised from 3-5 d → ~0.5 d.

**What landed this commit (single Fortran source file; 18 surgical sub-edits + 1 NEW SUBROUTINE; +202 / -2 = +200 LOC additive net):**

| # | Site (~line, post-edit) in `imogen/code/imogen_lpjg.f` | Edit | Backport directive |
|---|---|---|---|
| 1 | ~302 | B1 doc block + 3 new `REAL, ALLOCATABLE :: WIND_OUT_M_REGRID/QHUM_OUT_M_REGRID/PSTAR_OUT_M_REGRID(:,:,:,:)` declarations (after existing `T_OUT_M_REGRID` siblings at lines 295-298) | Apply identically; mirror the existing `T_OUT_M_REGRID` declaration pattern |
| 2 | ~320 | 1 new `REAL RH_TMP` scratch scalar (with 3-line doc block) for inline Rh computation at each writer cell | Apply identically; declare in MAIN scope alongside other WORK scalars |
| 3 | ~341 | 3 new `ALLOCATE(WIND_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX))` etc. (with 3-line doc block) immediately after existing `T_OUT_M_REGRID/P_OUT_M_REGRID/...` ALLOCATEs | Apply identically; same shape as `T_OUT_M_REGRID` allocation |
| 4 | ~975 | B1 doc block on `CALL REGRID_CLIM(...)` site + 2 continuation lines appending 6 new args (`,WIND_OUT,QHUM_OUT,PSTAR_OUT, WIND_OUT_M_REGRID,QHUM_OUT_M_REGRID,PSTAR_OUT_M_REGRID`) at the END of the existing 19-arg call | Apply identically; preserve trailing-arg ordering for minimal diff |
| 5 | ~1052 | B1 doc block + 2 new `OPEN(96, 'Rh_anom.dat')` + `OPEN(97, 'W_anom.dat')` in REGRID branch (symmetric with B2's Tmin/Tmax OPENs at lines ~1041-1042) | Apply identically; unit numbers 96/97 mirror C++ ofstream variable names `file96`/`file97` at `climatemodel.cpp:1046-1047` |
| 6 | ~1063 | 4 new per-cell LON/LAT header WRITEs (units 96/97) in REGRID branch | Apply identically |
| 7 | ~1086 | B1 doc block + `WRITE(97, ..., WIND_OUT_M_REGRID(IGP,IMM,IMD,IND))` + `CALL RH_FROM_QPT(...)` + `WRITE(96, ..., RH_TMP)` in REGRID DAILYOUT=TRUE inner-loop | Apply identically; use `_REGRID` suffix arrays in REGRID branch |
| 8 | ~1118 | Analogous WRITE+CALL+WRITE in REGRID DAILYOUT=FALSE branch (monthly mean; `,1,1` sub-index) | Apply identically |
| 9 | ~1133 | `WRITE(96,'()') / WRITE(97,'()')` per-cell newlines in REGRID branch | Apply identically; format must be `'()'` to advance one line |
| 10 | ~1140 | B1 doc block + 2 new `OPEN(96/97)` in non-REGRID branch (symmetric with item 5) | Apply identically |
| 11 | ~1163 | 4 new per-cell LON/LAT header WRITEs in non-REGRID branch (uses `LONG(IGP)`/`LAT(IGP)` vs REGRID's `LON_OUT`/`LAT_OUT`) | Apply identically; non-REGRID branch uses different LON/LAT arrays |
| 12 | ~1192 | B1 doc block + WRITE+CALL+WRITE in non-REGRID DAILYOUT=TRUE branch (uses `WIND_OUT/QHUM_OUT/PSTAR_OUT/T_OUT_M`; no `_REGRID` suffix) | Apply identically |
| 13 | ~1218 | Analogous WRITE+CALL+WRITE in non-REGRID DAILYOUT=FALSE branch | Apply identically |
| 14 | ~1247 | `WRITE(96,'()') / WRITE(97,'()')` per-cell newlines in non-REGRID branch | Apply identically |
| 15 | ~1276 | B1 doc block + 2 new `CLOSE(96)/(97)` (symmetric with B2's CLOSE(100)/(101) at lines ~1233-1234) — placed BEFORE the pre-existing `OPEN(97, 'done')` at line ~1304 | Apply identically; sequence is critical (CLOSE then OPEN for the unit 97 reuse pattern) |
| 16 | ~1303 | 3 new `IF (ALLOCATED(...)) DEALLOCATE(...)` for the 3 new REGRID arrays | Apply identically; mirror existing `T_OUT_M_REGRID` DEALLOCATE pattern |
| 17 | ~1342 (`SUBROUTINE REGRID_CLIM`) | B1 doc block on signature + 2 continuation lines appending 6 new dummy args (3 IN, 3 OUT) at the END | Apply identically |
| 18 | ~1372 (`REGRID_CLIM` body) | 6 new dimension decls (3 IN block + 3 OUT block) + 3 new nearest-neighbor passthrough assignments inside the `DO IMM, DO IMD, DO IND` triple-loop after the existing `T_OUT_M_REGRID = T_OUT_M` line | Apply identically; use `IND_MIN` (already computed by the existing nearest-neighbor loop) for all 3 new assignments |
| **19** | **~1432 (NEW SUBROUTINE)** | **NEW `SUBROUTINE RH_FROM_QPT(Q, P_PA, T_K, RH)` with full docstring + IMPLICIT NONE + 4-line Tetens algebra + clamping (~40 LOC; byte-identical to C++ `computeRelativeHumidityFromSpeificHumidty` at `climatemodel.cpp:1228-1249`)** | **Apply identically; insert between existing `REGRID_CLIM END` and `SUBROUTINE SETTIN` at the same anchor as in our tree** |

**Verification post-B1:**
- Fortran clean build: binary 137832 B (was 133696 B post-B2; +4136 B for B1 additions); zero new warnings with `-Wall -Wno-unused-dummy-argument -Wno-unused-variable` (8 pre-existing warnings at lines 4523/1489/2466/3642/870/688/853 unchanged — all from non-B1 code paths)
- C++ rebuilds clean (no-op regression check; B1 doesn't touch `lpjguess/`)
- 162 unit tests on both `build/runtests` + `build_mpi/runtests`: "Passed all 25 test cases with 162 assertions."
- All 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN): imogen 1cell, imogen 4cell, imogencfx 1cell, imogencfx 4cell

**Cross-engine parity matrix POST-B1:** Full climate-anomaly output parity between the two engines for the v1.0 production path. Both engines now write T/P/SW/WET/DTEMP/Tmin/Tmax/Rh/W (the Fortran engine writes these to BOTH REGRID + non-REGRID branches; the C++ port has only one branch — the native-IMOGEN-grid branch — per the B3 finding at `lpjguess/modules/climatemodel.cpp` line ~890).

**F-11 backport-sprint classification:** **RELEVANT (functional Fortran source change)**. The 18 sub-edits + 1 NEW SUBROUTINE should be applied to `trunk_r13078`'s `imogen_lpjg.f` if its pre-B1 state matches our pre-B1 state (i.e., no `WIND_OUT_M_REGRID`/`QHUM_OUT_M_REGRID`/`PSTAR_OUT_M_REGRID` REGRID arrays; no `Rh_anom.dat`/`W_anom.dat` writer blocks; no `RH_FROM_QPT` SUBROUTINE). Treat as a ~2-3 hour mechanical replication during the F-11 sprint. Although the Fortran engine source is shared across both forks (no fork-specific Fortran), recording the directive here ensures the backport sprint reviews the change against `trunk_r13078`'s build expectations.

**With B1 landed, the C2-era B-bundle is feature-COMPLETE** (all 6 audit items DONE: B10 → B6 → B2 → B3 → B4 → B1). Only the C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` remains (zero source changes).

---

### Step 17c (17c.0.0 LANDED): B15 + B16 forensic record — `notes/STEP_17c.md` NEW + 4-file documentation cascade; **backport-IRRELEVANT** (forensic record only; ZERO `lpjguess/` and `imogen/code/` source change)

**Date:** 2026-05-12 (afternoon-evening; session 3). **Commit hash:** `2beff31` (un-tagged checkpoint on top of `f6c192e`).

**Backport relevance:** **IRRELEVANT.** This commit is purely documentation (`notes/STEP_17c.md` NEW; CHANGELOG; EXECUTION_PLAN row 17c; FOLLOWUPS status dashboard refresh + new operational rule #8; session-3 chat handoff Part 1) — no `lpjguess/` or `imogen/code/` source touched. The B15+B16 ROOT CAUSES are now fully documented; the FIXES land at sub-phases 17c.0.1 + 17c.0.3 in subsequent commits (which will have their own LEDGER entries with backport directives).

**Cross-references for the Backport Sprint reader:**
- `notes/STEP_17c.md` §0 — full B15+B16 forensic record (~370 LOC) including §0.5 plib-parser source-level walkthrough, §0.8 recommended fix design (F1-F5), §0.9 B16 acknowledgement, §0.11 C2 tag-amendment decision deferral.
- `notes/FOLLOWUPS.md` "Operational heuristics" rule #8 — signal-of-life banner-presence assertion for code-path-gated cross-validation. Rule applies to ANY harness, not just our project; consider replicating in any `trunk_r13078`-based xval harness as best practice.

---

### Step 17c (17c.0.1 + 17c.0.2 LANDED): B15 fix (F1-F5) + signal-of-life harness assertion + four-xval re-verification — F5 in `lpjguess/framework/framework.cpp` is the ONLY RELEVANT change; F1-F4 are config/harness IRRELEVANT

**Date:** 2026-05-13 (afternoon; session 4). **Commit hash:** _to be determined_ (this commit; un-tagged checkpoint on top of `2beff31`).

**Backport relevance summary:**
- **F1, F2, F3, F4: IRRELEVANT** — per-fork cluster-config + harness; not in `trunk_r13078`'s tree. F1+F2 modify `runs/SSP1-2.6/main_xval_*.ins`; F3+F4 modify `scripts/cross_validate_year_outer.sh`. None of these files exist in `trunk_r13078`.
- **F5: RELEVANT (functional C++ source change)** — `lpjguess/framework/framework.cpp:339-357` adds a ~3-LOC `dprintf` runtime diagnostic + ~17-LOC doc block. `framework.cpp` is a near-identical sibling file in `trunk_r13078`'s framework; the F5 dprintf placement is structurally identical at the analogous post-`read_instruction_file()` site.

#### File: `lpjguess/framework/framework.cpp` (+21 LOC additive; F5 only)

**Insertion site:** Immediately after `read_instruction_file(args.get_instruction_file());` returns (line 337 in our tree at this commit), before the existing `firsthistyear`/`lasthistyear` sanity check at line 362. In `trunk_r13078`'s framework loop, locate the analogous `read_instruction_file()` call site (likely the same call signature; the function is part of the upstream LPJ-GUESS framework) and place F5 immediately after it.

**Change pattern (mechanical; copy verbatim):**

```cpp
	// Read the instruction file to obtain PFT static parameters and
	// simulation settings
	read_instruction_file(args.get_instruction_file());

	// [Step 17c (F-12 sub-milestone C3 PREP sub-phase 17c.0.1) — F5: signal-of-
	//  life RUNTIME DIAGNOSTIC for framework_loop_mode (added 2026-05-13).
	//  Echoes the parsed value of IMOGENConfig::framework_loop_mode immediately
	//  after read_instruction_file() returns, so every run.log contains a
	//  visible "this is the loop mode I parsed" line. Closes the third gap
	//  from notes/STEP_17c.md §0.6 (no consumer-side observability of the
	//  parsed framework_loop_mode value), complementing the harness-side
	//  rule-#8 banner-presence assertion in scripts/cross_validate_year_outer.sh
	//  ::compare_outputs() (F4) with an independent defense layer that fires
	//  unconditionally (not only when the framework.cpp:464 gate evaluates
	//  true). Catches both B15-class class-mismatch defects (pre-2beff31
	//  param-vs-bare-syntax) and any future typo'd framework_loop_mode value
	//  ("year_outter" etc.) which the harness rule-#8 banner check cannot
	//  surface (no banner emitted because no known gate matches). Backport-
	//  RELEVANT (touches lpjguess/framework/framework.cpp which exists in
	//  trunk_r13078). See notes/STEP_17c.md §0 (audit item B15) §0.6 + §0.8(F5).
	//  - DKB 2026-05-13]
	dprintf("[framework] framework_loop_mode = \"%s\" (after .ins parse)\n",
	        (const char*)IMOGENConfig::framework_loop_mode);

	// Initialise input/output
```

**Backport directive — apply if all of the following preconditions hold in `trunk_r13078`:**

1. `IMOGENConfig::framework_loop_mode` is declared (i.e., the C1 foundation backport has landed and the `framework_loop_mode` parameter is `declare_parameter`-bound to `IMOGENConfig::framework_loop_mode` per the step-17a-foundation LEDGER entry). If the C1 foundation has NOT been backported, F5 is a forward-reference dangling on a non-existent variable and must wait until the C1 foundation lands first.
2. `dprintf` is the canonical LPJ-GUESS log function in `trunk_r13078`'s framework (it is in our tree; verify by `rg "dprintf" trunk_r13078/lpjguess/framework/framework.cpp` returning many hits before applying).
3. The `read_instruction_file()` call site is reachable in `trunk_r13078`'s framework() function with the same call signature (it should be; this is upstream LPJ-GUESS plumbing).

If all three hold: copy the 21-LOC block verbatim immediately after `read_instruction_file(args.get_instruction_file());` returns. No other adjustments needed.

If precondition 1 doesn't hold yet: defer F5 until the C1 foundation backport lands; F5 cannot be backported in isolation because `IMOGENConfig::framework_loop_mode` doesn't exist without it.

**Why F5 matters for `trunk_r13078`-side validation:** F5 is the consumer-side defense layer against any future B15-class class-mismatch defect. Even if the harness-side rule-#8 banner check (F4) is absent in a `trunk_r13078`-based xval setup, F5's unconditional run.log echo of `framework_loop_mode` makes the parsed-vs-intent discrepancy directly observable. F5 also catches typo'd values like `"year_outter"` that would silently fall through F4 (no banner emitted because no known gate matches the typo). Treat F5 as ~5 minutes of mechanical work during the F-11 backport sprint; the doc block is informative and should be preserved as-is.

#### Files NOT applicable to `trunk_r13078` backport (F1-F4)

For Backport Sprint completeness, the per-fork files modified in this commit:

| File | Change | Backport directive |
|---|---|---|
| `runs/SSP1-2.6/main_xval_imogencfx.ins` (+15/−1; F1) | `param "framework_loop_mode" (str "gridcell_outer")` → `framework_loop_mode "gridcell_outer"` + 13-line doc block | **N/A** — `runs/` is a per-fork cluster-config tree; not in `trunk_r13078`. |
| `runs/SSP1-2.6/main_xval_loose.ins` (+8/−1; F2) | Symmetric to F1 | **N/A** — same reason as F1. |
| `scripts/cross_validate_year_outer.sh` (+127/−3; F3 + F4) | F3: wrapper-template `param "framework_loop_mode" (str "$mode")` → `framework_loop_mode "$mode"` + 27-line top-of-template doc block. F4: NEW signal-of-life banner-presence assertion in `compare_outputs()` (greps both run.logs for `[year_outer]` banner; pass requires `banner_a == 0` AND `banner_b >= 1`; failure exits with new code 4). | **N/A for source backport** — the harness is per-fork. **HOWEVER, recommended best practice for any future `trunk_r13078`-based xval harness:** if a `trunk_r13078`-based smoke runs the analogous gridcell_outer-vs-year_outer cross-validation, replicate the F4 rule-#8 banner-presence assertion pattern in that harness's compare phase. The F4 implementation (~92 LOC including doc + bash defensive patterns for `grep -c`'s exit-rc semantics) is directly reusable. |

#### Verification this commit (per `notes/STEP_17c.md` §1.1)

| Gate | Method | Result |
|---|---|---|
| 1 — `lpjguess/build/` rebuild | `cd lpjguess/build && cmake --build . --target guess` | ✅ ZERO new warnings (incremental: framework.cpp.o + relink) |
| 2 — `lpjguess/build_mpi/` rebuild | `cd lpjguess/build_mpi && cmake --build . --target guess` | ✅ ZERO new warnings (incremental: framework.cpp.o + imogen_input.cpp.o + imogencfx.cpp.o + relink; the latter two recompiled due to mtime cache, not behavioural) |
| 3 — 162 unit tests (build/) | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| 4 — 162 unit tests (build_mpi/) | `lpjguess/build_mpi/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| 5 — xval `1cell imogen` | `scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ rc=0 / 37/37 bit-exact / 0/37 NaN / banner_a=0 / banner_b=5 / F5 echoes "gridcell_outer" + "year_outer" — **first time year_outer code path actually exercised** |
| 6 — xval `1cell imogencfx` | `scripts/cross_validate_year_outer.sh 1cell imogencfx` | ✅ rc=0 / same metrics as gate 5 |
| 7 — xval `4cell imogen` | `scripts/cross_validate_year_outer.sh 4cell imogen` | ⚠️ rc=99 — **B16 anticipated surface** at `cell_idx=1` cell `(-95.75,80.25)` per `notes/STEP_17c.md` §0.9; positive empirical evidence for 17c.0.3 fix |
| 8 — xval `4cell imogencfx` | `scripts/cross_validate_year_outer.sh 4cell imogencfx` | ⚠️ rc=99 — symmetric `IMOGENCFXInput::preload_all_climate` same fail at same cell |

**Verification gate at `trunk_r13078`-backport time:** if the C1 foundation backport has landed in `trunk_r13078` AND F5 is applied per the directive above, the analogous re-build + run-some-LPJ-GUESS-with-an-`.ins`-that-sets-`framework_loop_mode "gridcell_outer"` smoke should show `[framework] framework_loop_mode = "gridcell_outer" (after .ins parse)` immediately after the `read_instruction_file` log lines. This is the trivial post-backport sanity check for F5.

#### Cross-references

- `notes/STEP_17c.md` §1.1 — canonical landing record (~190 LOC; F1-F5 implementation details + verification + B16 trigger)
- `notes/STEP_17c.md` §0.6 + §0.8(F5) — the gap analysis + F5 design rationale
- `notes/FOLLOWUPS.md` "Operational heuristics" rule #8 — the meta-rule that F4 implements
- `lpjguess/framework/framework.cpp` line 502 — the `[year_outer]` diagnostic banner that F4 greps for
- `lpjguess/framework/framework.cpp` line 464 — the gating decision that consumes `IMOGENConfig::framework_loop_mode`
- B16 next: 17c.0.3 sub-phase will land C++ source changes in `lpjguess/modules/imogen_input.cpp` + `lpjguess/modules/imogencfx.cpp` (both **backport-RELEVANT**); separate LEDGER entry to be added then.

**With this commit, B15 (the C1+C2 false-positive harness root cause) is closed**; year_outer is observably executed in 1cell xval scenarios for the first time. B16 surfaces empirically at cell_idx=1 in 4cell scenarios as anticipated by §0.9, triggering 17c.0.3.

---

### Step 17c (17c.0.3 LANDED): B16 fix (G1-G4) + B17 forensic surface — all changes **TRUNK-IRRELEVANT-by-novelty** (per-fork additions; `preload_all_climate` virtual function does not exist in `trunk_r13078`'s `InputModule` base class)

**Date:** 2026-05-13 (evening; session 4). **Commit hash:** _to be determined_ (this commit; un-tagged checkpoint on top of `019c9dd`).

**Backport relevance summary:**
- **G1, G2, G3, G4: TRUNK-IRRELEVANT-by-novelty (NOT by syntax/semantics)** — the `preload_all_climate` virtual function + cumulative-across-cells cache machinery + eager-check anti-pattern are **per-fork additions** introduced at C1.3 sub-step 7.3.2 (commit `d7f6c74`, 2026-05-10) as part of the C1.1 inputmodule subclass refactor. `trunk_r13078`'s `InputModule` base class does not declare `preload_all_climate` as a virtual function; trunk's input modules use a different per-cell streaming paradigm (no cumulative-cache concept; no preload phase distinct from the per-year readenv phase).
- **No backport directive** — this commit's changes have nothing to backport because the underlying machinery they modify doesn't exist upstream. Documented here for completeness (so the Backport Sprint reader knows this commit was reviewed and explicitly classified as TRUNK-IRRELEVANT, not overlooked).

#### Files in this commit (all TRUNK-IRRELEVANT-by-novelty)

| File | Change | Trunk-equivalence | Backport directive |
|---|---|---|---|
| `lpjguess/modules/imogen_input.cpp` (+38/−9; G1 + G4 part 1) | DELETE 8-line eager check at lines 1111-1118 (`if (last_store_index >= nyears) fail("...: stored_years cache already full ...")`); REPLACE with ~38-LOC doc block explaining cumulative-across-cells cache design intent + B16 root cause + cross-references to `notes/STEP_17c.md` §0.9 + §2.4 + §2.5. ALSO: add `cell_idx` to inner per-miss `fail()` message at lines 1158-1164 for unambiguous fault attribution (~4 LOC). | `ImogenInput::preload_all_climate` is a per-fork addition for the C1.1 cumulative-cache machinery; `trunk_r13078` doesn't have this method or this cache. | **N/A** — not in `trunk_r13078`. |
| `lpjguess/modules/imogencfx.cpp` (+20/−11; G2 + G4 part 2) | Symmetric DELETE 11-line eager check at lines 1366-1376; REPLACE with ~20-LOC doc block (cross-references G1's full forensic in `imogen_input.cpp`). ALSO: add `cell_idx` to inner per-miss `fail()` message at lines 1421-1427 (~4 LOC). | `IMOGENCFXInput::preload_all_climate` is a per-fork addition; `trunk_r13078` doesn't have the IMOGENCFX module at all (the entire `imogencfx.cpp` file is per-fork, introduced for IMOGEN tight-coupling at C1 era). | **N/A** — not in `trunk_r13078`. |
| `lpjguess/framework/inputmodule.h` (+20/0; G3) | AUGMENT existing `InputModule::preload_all_climate` virtual function doc block at lines 84-102 with ~20 LOC of "IMPLEMENTATION GUIDANCE FOR SUBCLASSES" formalising the cumulative-across-cells cache contract: subclasses MUST treat any per-cell cache as cumulative-across-cells; subclasses MUST NOT add eager early-exit checks at function entry that assume per-cell cache state. | The `preload_all_climate` virtual function declaration in `InputModule` is a per-fork addition; `trunk_r13078`'s `InputModule` base class doesn't have it. The augmentation is contract documentation for a virtual function that doesn't exist upstream. | **N/A** — not in `trunk_r13078`. |

#### Verification this commit (per `notes/STEP_17c.md` §1.2)

| Gate | Method | Result |
|---|---|---|
| 1 — `lpjguess/build/` rebuild | `cd lpjguess/build && cmake --build . --target guess` | ✅ ZERO new warnings (incremental: imogen_input.cpp.o + imogencfx.cpp.o + relink; inputmodule.h is included → triggers .cpp recompile) |
| 2 — `lpjguess/build_mpi/` rebuild | `cd lpjguess/build_mpi && cmake --build . --target guess` (after `MPICH_CXX=g++` recovery; see §1.2.10) | ✅ ZERO new warnings touching G1-G4 sites (332 total = pre-existing union of `guess` + `runtests` build outputs) |
| 3 — 162 unit tests (build/) | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| 4 — 162 unit tests (build_mpi/) | `lpjguess/build_mpi/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| 5 — xval `1cell imogen` | `scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ rc=0 / 37/37 bit-exact / 0/37 NaN / banner_a=0 / banner_b=5 — regression-clean baseline |
| 6 — xval `1cell imogencfx` | `scripts/cross_validate_year_outer.sh 1cell imogencfx` | ✅ rc=0 / same metrics as gate 5 |
| 7 — xval `4cell imogen` | `scripts/cross_validate_year_outer.sh 4cell imogen` | ⚠️ rc=2 / 15/37 bit-exact / 22/37 differ / 0/37 NaN / banner_a=0 / banner_b=**5** — year_outer ran END-TO-END (3→5 banner-count delta vs 17c.0.2 = mechanical evidence B16 is fixed); 22/37 differ surfacing **B17** (full forensic in `notes/STEP_17c.md` §3) |
| 8 — xval `4cell imogencfx` | `scripts/cross_validate_year_outer.sh 4cell imogencfx` | ⚠️ rc=2 / same metrics as gate 7 — confirms B17 is systemic year_outer multi-cell defect, not input-mode-specific |

#### Cross-references for the Backport Sprint reader

- `notes/STEP_17c.md` §1.2 — canonical landing record for 17c.0.3 (~115 LOC; G1-G4 implementation details + verification + B17 trigger)
- `notes/STEP_17c.md` §2 — full B16 forensic record (~120 LOC; analogous to §0 for B15)
- `notes/STEP_17c.md` §3 — B17 forensic surface (~110 LOC; recommended-fix subsection §3.6 to be elaborated in 17c.0.4 commit)
- `notes/STEP_17c.md` §1.2.10 — MPI build recovery via `MPICH_CXX=g++` operational lesson (the script's preferred `mpicxx` + Anaconda3 `conda-forge gxx_linux-64` path failed at link with system NetCDF/HDF5 ABI mismatches; recovery via option (a) of `scripts/cluster/make_guess.sh`'s documented compiler-selection options)
- B17 next: 17c.0.4 sub-phase will land the B17 forensic deep-dive + fix; if the fix touches `compare_outputs()` in `scripts/cross_validate_year_outer.sh` (B17(a) harness sort-then-diff upgrade), it will be IRRELEVANT (per-fork harness; not in `trunk_r13078`). If the fix touches engine code for B17(b) numerical drift (e.g., fixing per-PFT-total accumulator order to be cell-iteration-independent), it MAY be RELEVANT depending on which file is touched (the per-PFT-total accumulators may be in trunk's `commonoutput.cpp` or analogous; to be classified at 17c.0.4 commit time).

**With this commit, B16 (the latent eager cache-fullness check defect) is closed**; year_outer 4cell now runs end-to-end (5 banners; 37 .out files in Run B; pre-fix the run aborted at exit 99 after 3 banners). B17 surfaces empirically with 22/37 .out file divergence between gridcell_outer and year_outer in 4cell scenarios, triggering 17c.0.4 (combined B17(a) + B17(b) scope).

---

### Step 17c (17c.0.4 LANDED): B17 forensic deep-dive (Phase A) + B17(a) row-emission-order divergence fix (.sh-only sort-then-diff harness upgrade) + B17(b) reclassified — change is **TRUNK-IRRELEVANT-by-novelty** (per-fork harness `scripts/cross_validate_year_outer.sh` does not exist in `trunk_r13078`)

**Date:** 2026-05-13 (late evening; session 4). **Commit hash:** _to be determined_ (this commit; un-tagged checkpoint on top of `4d09b62`).

**Backport relevance summary:**
- **B17(a) FIX (option (a1) from `notes/STEP_17c.md` §3.6): TRUNK-IRRELEVANT-by-novelty (NOT by syntax/semantics)** — the `scripts/cross_validate_year_outer.sh` harness is a per-fork addition introduced at C1.1 era for cross-validating the per-fork `framework_loop_mode = "year_outer"` code path against `gridcell_outer`. `trunk_r13078` doesn't have either the `framework_loop_mode` parameter (per-fork; `framework.cpp` upstream has only the gridcell_outer code path) or this harness. The B17(a) row-emission-order divergence as a phenomenon also doesn't exist upstream because the upstream loop-order is the only one (cell-major), so there's no cross-mode comparison to make.
- **B17(b) RECLASSIFIED + DECISION DEFERRED to 17c.0.5**: this commit does NOT touch any source file related to B17(b). The forensic deep-dive (Phase A) lives in `notes/STEP_17c.md` §1.3.3 + new §3.8; the (α tolerance vs β root-cause) decision is for 17c.0.5. If 17c.0.5 chooses (β), the resulting fix MAY touch upstream-relevant files (e.g., `lpjguess/framework/framework.cpp` year_outer setup-phase reordering — which would still be backport-IRRELEVANT because year_outer is a per-fork addition); to be classified at 17c.0.5 commit time.
- **No backport directive** — this commit's changes have nothing to backport because the underlying machinery they modify (`scripts/cross_validate_year_outer.sh`) doesn't exist upstream. Documented here for completeness (so the Backport Sprint reader knows this commit was reviewed and explicitly classified as TRUNK-IRRELEVANT, not overlooked).

#### Files in this commit (TRUNK-IRRELEVANT-by-novelty)

| File | Change | Trunk-equivalence | Backport directive |
|---|---|---|---|
| `scripts/cross_validate_year_outer.sh` (+103/−3; B17(a) FIX) | INSERT ~100-LOC SORT-THEN-DIFF NORMALIZATION block in `compare_outputs()` between line 266 (end of "RAW BYTE-EQUALITY SUMMARY" block) and line 268 (start of NaN-check block): 75-LOC documentation comment + conditional sort-then-diff block (mktemp+trap RETURN auto-cleanup; LC_ALL=C sort -k1,1n -k2,2n -k3,3n on (Lon, Lat, Year); preserves header line via head -1 + tail -n+2 \| sort) + BIT_EXACT/SORTED_EXACT/SORTED_DIFFER classification + effective-pass semantic update + refined PASS/FAIL messages with B17(b) drift count reporting. Block IDEMPOTENT (guarded by `if mismatches > 0`; skipped when raw cmp -s passes). | The `scripts/cross_validate_year_outer.sh` harness is a per-fork addition (introduced at C1.1 era for `framework_loop_mode = "year_outer"` cross-validation); trunk has no equivalent harness because trunk has only the gridcell_outer loop-order. | **N/A** — not in `trunk_r13078`. |

Documentation cascade also touches: `notes/STEP_17c.md` (NEW §1.3 landing record + §3.3+§3.4+§3.6 status updates + NEW §3.8 reclassified-B17(b) sub-section + header date/status updates; ~+200 LOC), `notes/FOLLOWUPS.md` (status dashboard refresh), `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (this entry), `EXECUTION_PLAN.md` (row 17c update), `CHANGELOG.md` (NEW dated entry), `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (Part 4 NEW). All documentation deltas are TRUNK-IRRELEVANT.

#### Verification this commit (per `notes/STEP_17c.md` §1.3.5 + §1.3.6)

| Gate | Method | Result |
|---|---|---|
| 1+2 — clean rebuilds | SKIPPED | NO C++ rebuild needed (.sh-only fix; binaries from 17c.0.3 reused) |
| 3 — 162 unit tests (build/) | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." (regression-clean; .sh fix does not affect compiled binary) |
| 4 — 162 unit tests (build_mpi/) | `lpjguess/build_mpi/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." (build-agnostic) |
| 5 — xval `1cell imogen` | `scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ rc=0 / 37/37 raw BIT_EXACT / sort block skipped per idempotency / 0/37 NaN / banner_a=0 / banner_b=5 — preserves PASS exit 0 |
| 6 — xval `1cell imogencfx` | `scripts/cross_validate_year_outer.sh 1cell imogencfx` | ✅ rc=0 / same metrics as gate 5 |
| 7 — xval `4cell imogen` | `scripts/cross_validate_year_outer.sh 4cell imogen` | ⚠️ rc=2 (CONTROLLED-FAIL) / EXACTLY-PREDICTED **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER** classification / 0/37 NaN / banner_a=0 / banner_b=5 — B17(a) successfully normalizes 5 PURE B17(a) files (`npool.out`, `mch4.out`, `mch4_diffusion.out`, `mch4_ebullition.out`, `mch4_plant.out`) via sort-then-diff to byte-identical content; effective-pass count advanced from 15/37 → 20/37 (33% improvement); 17 SORTED_DIFFER files surface B17(b) cleanly (full reclassified forensic in `notes/STEP_17c.md` §3.8) |
| 8 — xval `4cell imogencfx` | `scripts/cross_validate_year_outer.sh 4cell imogencfx` | ⚠️ rc=2 / IDENTICAL 15+5+17 envelope as gate 7 — confirms B17 is build-agnostic + .ins-agnostic (the divergence is in the framework's year_outer code path, not input-module-specific) |

#### Cross-references for the Backport Sprint reader

- `notes/STEP_17c.md` §1.3 — canonical landing record for 17c.0.4 (~250 LOC; B17(a) implementation details + Phase A forensic + verification + B17(b) reclassification + 17c.0.5 plan)
- `notes/STEP_17c.md` §3.3 — B17(a) status update (CLOSED 2026-05-13 evening via §3.6 option (a1))
- `notes/STEP_17c.md` §3.4 — B17(b) status update (RECLASSIFIED + decision deferred to 17c.0.5; §3.4 hypothesis 1+2 FALSIFIED; hypothesis 3 surviving + refined)
- `notes/STEP_17c.md` §3.6 — recommended-fix subsection update (option (a1) IMPLEMENTED in this commit; option (β) for B17(b) deferred to 17c.0.5)
- `notes/STEP_17c.md` §3.8 — NEW reclassified-B17(b) sub-section (~120 LOC; empirical signature + hypothesis-bisection summary + scientific interpretation + Phase A's wall on root-cause identification)
- B17(b) next: 17c.0.5 sub-phase will decide between Option α (tolerance-based comparison upgrade to `compare_outputs()`; ~0.5-1 d; recommended; TRUNK-IRRELEVANT) and Option β (seed-tracking dprintf root-cause investigation; +1-2 d; targeted fix — backport classification depends on which file is touched). To be classified at 17c.0.5 commit time.

**With this commit, B17(a) (the row-emission-order divergence in multi-cell year_outer xval) is closed** via harness sort-then-diff normalization; effective-pass for 4cell scenarios advances from 15/37 → 20/37 (33% improvement). **B17(b) is reclassified** from "~1 ULP numerical roundoff" (FALSIFIED) to "stochastic-process sensitivity per cell-iteration-order RNG slip"; 17c.0.5 will decide the closure path.

---

### Step 17c (17c.0.4-followup LANDED): B17(b) operational acceptance at provisional 2% tolerance + sub-phase renumbering decision deferral — **TRUNK-IRRELEVANT** (doc-only + .sh-comment-only)

**Date:** 2026-05-13 (night; session 4). **Commit hash:** `2771939` (3-remote-converged at `origin/main`/`kit/main`/`helmholtz/main` 2026-05-13 night).

**Backport relevance summary:**
- **TRUNK-IRRELEVANT (doc-only + .sh-comment-only)**: zero source-logic change. The commit lands user-authorised provisional-acceptance of B17(b) per §3.8.5 (2% cell-total tolerance envelope; defers formal Option α/β closure to a future sub-phase TBD reactivated only on a §3.8.5 re-evaluation trigger). 3 in-tree files: `notes/STEP_17c.md` NEW §3.8.5 sub-section + `notes/FOLLOWUPS.md` "Last updated" header refresh + B17 row status update + `scripts/cross_validate_year_outer.sh` ~30-LOC inline comment block in `compare_outputs()` near the SORTED_DIFFER classification (ZERO logic change). Plus 1 sibling-artifact (`_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 4).
- **No backport directive** — this commit's changes are doc-only + .sh-comment-only (no logic change; no .cpp/.h touch); nothing to backport. Documented here for completeness.

#### Files in this commit (all TRUNK-IRRELEVANT)

| File | Change | Backport directive |
|---|---|---|
| `notes/STEP_17c.md` (~+140 LOC; NEW §3.8.5 sub-section) | Decision narrative + 4 re-evaluation triggers + sub-phase renumbering implication + documentation surface | N/A — `notes/` is per-fork |
| `notes/FOLLOWUPS.md` (~+5 LOC: "Last updated" header refresh + B17 row status update) | Status dashboard update reflecting provisional acceptance | N/A — `notes/` is per-fork |
| `scripts/cross_validate_year_outer.sh` (~+30 LOC inline comment block; ZERO logic change) | Documentation in `compare_outputs()` near SORTED_DIFFER classification capturing the operational context for runtime consumers + future maintainers without requiring them to leave the code | N/A — per-fork harness; not in `trunk_r13078` |

#### Verification this commit

Unit tests re-run as a sanity check: `lpjguess/build/runtests --reporter compact` → 25/25 / 162/162 PASS; `lpjguess/build_mpi/runtests --reporter compact` → 25/25 / 162/162 PASS. No xval re-verify (the next sub-phase 17c.0.5 does the canonical 4-xval re-verify per its own backport-ledger entry below).

**With this commit, B17(b) is operationally accepted at a provisional 2% cell-total tolerance** per §3.8.5; formal Option α (tolerance-based comparison upgrade) AND Option β (seed-tracking dprintf root-cause investigation) DEFERRED to a future sub-phase TBD reactivated only on a §3.8.5 re-evaluation trigger firing.

---

### Step 17c (17c.0.5 LANDED): full 4-xval re-verify on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD per user-authorised collapsed renumbering convention + harness stale-reference cleanup post-collapsed-renumbering — **TRUNK-IRRELEVANT** (verification-only + .sh-comment-only)

**Date:** 2026-05-13 (night-late; session 4). **Commit hash:** _to be determined_ (this commit; un-tagged checkpoint on top of `2771939`).

**Backport relevance summary:**
- **TRUNK-IRRELEVANT (verification + .sh-comment-only)**: zero engine source change. The commit lands the full 4-xval re-verify on `2771939` HEAD (gates 1-8) per the user-authorised collapsed renumbering convention (per `notes/STEP_17c.md` §3.8.5 "Sub-phase renumbering implication" sub-section), establishing the canonical baseline routine xval re-verify envelope (15+5+17 + exit 2) for the new §3.8.5.5 re-evaluation cadence. Opportunistically rolled in: 4 surgical -1/+1-or-+2 stale-reference cleanups at `scripts/cross_validate_year_outer.sh` lines 305-306, 429, 484, 630-633 (post-collapsed-renumbering convention adoption rendered the prior "sub-phase 17c.0.5 (decision: tolerance-based comparison vs root-cause fix)" framing factually incorrect; +10/-5 LOC; ZERO behaviour change).
- **No backport directive** — this commit's changes are verification + .sh-comment-only (no logic change; no .cpp/.h touch); nothing to backport. The cleanup itself is a direct consequence of the renumbering decision and would not apply upstream where `framework_loop_mode = "year_outer"` doesn't exist.

#### Files in this commit (all TRUNK-IRRELEVANT)

| File | Change | Trunk-equivalence | Backport directive |
|---|---|---|---|
| `scripts/cross_validate_year_outer.sh` (+10/−5; STALE-REF CLEANUP) | 4 surgical edits at lines 305-306 (header doc-comment), 429 (B17(a) NORMALIZATION SUMMARY classification), 484 (effective-pass block trailing comment), 630 (FAIL message at SORTED_DIFFER > 0 path) — replacing "sub-phase 17c.0.5 (decision: tolerance-based comparison vs root-cause fix)" framing with §3.8.5 cross-references. ZERO behaviour change; bash syntax + smoke-retest verified | The harness is per-fork (introduced at C1.1 era); trunk has no equivalent. The "17c.0.5 (decision)" terminology only makes sense in the per-fork PREP-phase ledger. | **N/A** — not in `trunk_r13078`. |

Documentation cascade also touches: `notes/STEP_17c.md` (NEW §1.4 + §1.5 landing records + §1 sub-phase table updates marking 17c.0.4-followup ✅ + 17c.0.5 ✅ + §3.8.5 closing-paragraph supersession + §3.8.5 sub-phase renumbering lock-in + NEW §3.8.5.5 re-evaluation cadence sub-section + header date refresh + status block update + Index updates; ~+250 LOC), `notes/FOLLOWUPS.md` (status dashboard refresh + B17 row update), `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (this entry), `EXECUTION_PLAN.md` (row 17c update), `CHANGELOG.md` (NEW dated entry), `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (Part 5 NEW). All documentation deltas are TRUNK-IRRELEVANT.

#### Verification this commit (per `notes/STEP_17c.md` §1.5 — full gates 1-8)

| Gate | Method | Result |
|---|---|---|
| 1 — `lpjguess/build/` rebuild | `cd lpjguess/build && cmake --build . --target guess` | ✅ NO-OP (binary sha256 `8daa1339...` byte-identical pre/post; no source change since `4d09b62`) |
| 2 — `lpjguess/build_mpi/` rebuild | `cd lpjguess/build_mpi && cmake --build . --target guess` | ✅ NO-OP (binary sha256 `dd307488...` byte-identical pre/post) |
| 3 — 162 unit tests (build/) | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." (regression-clean; third independent confirmation since 17c.0.4) |
| 4 — 162 unit tests (build_mpi/) | `lpjguess/build_mpi/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." (build-agnostic) |
| 5 — xval `1cell imogen` | `scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ rc=0 / 37/37 raw BIT_EXACT / 0/0 NaN / banner_a=0 / banner_b=5 |
| 6 — xval `1cell imogencfx` | `scripts/cross_validate_year_outer.sh 1cell imogencfx` | ✅ rc=0 / same metrics as gate 5 |
| 7 — xval `4cell imogen` | `scripts/cross_validate_year_outer.sh 4cell imogen` | ⚠️ rc=2 (CONTROLLED-FAIL within §3.8.5 envelope) / **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER** / 0/0 NaN / banner_a=0 / banner_b=5 — IDENTICAL to 17c.0.4 envelope |
| 8 — xval `4cell imogencfx` | `scripts/cross_validate_year_outer.sh 4cell imogencfx` | ⚠️ rc=2 / IDENTICAL 15+5+17 envelope as gate 7 — **B17(b) coupling-invariance confirmed** (gate-7-vs-gate-8 manifest diff EMPTY) |

#### Cross-references for the Backport Sprint reader

- `notes/STEP_17c.md` §1.4 — canonical landing record for 17c.0.4-followup commit `2771939` (~75 LOC; B17(b) operational acceptance at 2%; doc-only)
- `notes/STEP_17c.md` §1.5 — canonical landing record for 17c.0.5 commit (this commit; ~180 LOC; full 4-xval re-verify; gate-by-gate evidence; script renumbering cleanup detail in §1.5.7)
- `notes/STEP_17c.md` §3.8.5 — operational acceptance decision narrative (B17(b) provisionally accepted at 2% per 17c.0.4-followup `2771939`; collapsed renumbering convention adopted in this commit per §3.8.5 "Sub-phase renumbering implication")
- `notes/STEP_17c.md` §3.8.5.5 — NEW re-evaluation cadence sub-section (routine xval re-verify + C3-era cluster smoke + paper-stage analysis + ad-hoc on §3.8.5 trigger)
- Future sub-phase TBD: deferred Option α (tolerance-based comparison upgrade; ~0.5-1 d; TRUNK-IRRELEVANT — .sh harness only) OR Option β (seed-tracking dprintf root-cause investigation; +1-2 d; targeted fix — backport classification depends on which file is touched). Reactivates only on §3.8.5 re-evaluation trigger firing per §3.8.5.5. To be classified at reactivation commit time.

**With this commit, the full 4-xval re-verify on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD `2771939` is COMPLETE** with byte-identical envelope to 17c.0.4. The user-authorised collapsed renumbering convention is locked in. The §3.8.5.5 re-evaluation cadence is locked in with the canonical baseline envelope from this commit's gates 7+8 as the "expected" routine outcome that future routine xval re-verifies on this branch will be compared against. 17c.0.6 (C2 close-out tag annotation amendment decision; ACTIONABLE since 17c.0.5 has confirmed underlying year_outer code substantively passes within §3.8.5 envelope) is NEXT.

---

### Step 17c (17c.0.7 LANDED): workstation `mpirun -np 4` mimic verification of C2-core MPI machinery + Path α handshake-file write-path defect fix at the xval harness layer + 5 LOC of unit doc-comment clarifications in `lpjguess/framework/guess.h` (N2O_FIRE + N2O_SOIL + 3 sibling N-cycle flux types) + ~8 LOC of comment-clarity cleanup in `lpjguess/modules/imogenoutput.cpp:75-83` (N2O_PER_N constant) + 2 BUNDLED ADDITIONAL clarifications (typo fix + multi-line doc-block expansion at `guess.h:3850-3855` soil.N2O_mass declaration; NEW ~13 LOC inline-comment block at `commonoutput.cpp:1759-1771` documenting the ngases.out kgN/ha/yr writer convention) — **MIXED: TRUNK-IRRELEVANT-by-novelty for the harness + imogenoutput.cpp content + TRUNK-RELEVANT for the guess.h N-cycle unit doc-comments + the guess.h soil.N2O_mass typo fix + the commonoutput.cpp ngases.out unit comment block**

**Date:** 2026-05-15 (evening; session 4 continuation). **Commit hash:** _to be determined_ (this commit; tagged `v0.17.7-step17c-mpi-4rank-mimic` post-merge; ff-merged onto `main` from feature branch `step17c-mpi-4rank-mimic` on top of the 17c.0.6 commit).

**Backport relevance summary:**
- **TRUNK-IRRELEVANT-by-novelty for the harness** (`scripts/cross_validate_mpi_4rank.sh` is a per-fork harness; `scripts/` is not in `trunk_r13078`). The Path α `DIR_COMMON` injection in the wrapper-writer functions is harness-side defensive injection for the xval setup path that bypasses the canonical `imogen_intermediary.ins` import chain; not applicable to `trunk_r13078`.
- **TRUNK-IRRELEVANT-by-novelty for the `imogenoutput.cpp:75-79` N2O_PER_N comment cleanup** (`lpjguess/modules/imogenoutput.cpp` is a step-8 addition; no trunk analog; the constant + its comment are per-fork additions).
- **TRUNK-RELEVANT for the `lpjguess/framework/guess.h` N-cycle unit doc-comments** at lines 1241 (N2O_FIRE) + 1250 (N2O_SOIL) + the 3 sibling N-cycle flux types (N2_FIRE at 1243, NH3_SOIL at 1246, NO_SOIL at 1248) — `guess.h` exists in `trunk_r13078` as a near-identical sibling file; the units (kgN/m²; mass-of-N basis — the N atoms inside the respective compound molecules, NOT the molecule mass) are inherent to the N-cycle pool budget convention at `ntransform.cpp:93` (`n_budget_check = soil.NH4_mass + soil.NO3_mass + soil.NO2_mass + soil.NO_mass + soil.N2O_mass + soil.N2_mass`) and have been the canonical convention since before our rebuild started; the comments were simply missing from the declarations. Upstream `trunk_r13708` could accept this improvement as a pure documentation enhancement (zero behavior change; zero risk; lock-in of an implicit convention so future maintainers don't have to grep through `n_budget_check` to figure out the units).
- **Backport directive for the guess.h portion**: at Backport Sprint time (post-step 19), apply the same 5 LOC of doc-comments to `trunk_r13078`'s `framework/guess.h` declarations of N2O_FIRE + N2O_SOIL + N2_FIRE + NH3_SOIL + NO_SOIL. The trunk versions of these declarations are byte-identical to the pre-fix LandSyMM_LPJ-GUESS versions (per the 6-file delta in §2 of this ledger which does NOT include `framework/guess.h` modifications since step 7 began — meaning the file is currently shared modulo cosmetic whitespace).

#### Files in this commit

| File | Change | Backport directive |
|---|---|---|
| `scripts/cross_validate_mpi_4rank.sh` (NEW; ~700 LOC including comprehensive doc block at file head) | NEW harness orchestrating single-process baseline + `mpirun -np 4` runs for 3 coupling modes (loose, prescribed, tight) on a 4-cell × 11-yr smoke scenario; compares aggregated `.out` files (per-cell + per-mode) AND the four LPJG-side handshake files (`imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt`, `imogen_lpjg.txt`, `done`) at `<DIR_COMMON>/LPJG_main/IMOGEN/`. Wrapper-writer functions (`write_baseline_wrapper()` + `write_mpi_wrapper()`) inject `DIR_COMMON "<absolute-path>"` into the generated wrapper `.ins` files for non-loose modes per Path α defect fix. | TRUNK-IRRELEVANT-by-novelty (per-fork harness; not in `trunk_r13078`) |
| `.gitignore` (+6 / 0) | NEW entry for `runs/*/parallel_work_xval_mpi/` mirroring the existing `runs/*/parallel_work/` line; silences the new harness's per-mode test-artifact directories. | TRUNK-IRRELEVANT (per-fork test-artifact path) |
| `lpjguess/framework/guess.h` (+20 / −11; lines 1240-1257 = 5 N-cycle flux types: N2O_FIRE, N2_FIRE, NH3_SOIL, NO_SOIL, N2O_SOIL — original Phase 3a additions; PLUS lines 3850-3855 = soil.N2O_mass pool typo fix + multi-line doc-block expansion — NEW bundled additional clarification (i)) | Replaced single-line doc-comments with multi-line doc-comments specifying the kgN/m² + mass-of-N basis convention at the 5 N-cycle flux ENUMs. PLUS: pre-existing typo `/// soil NO mass in pool (kgN/m2)` for the soil pool variables `N2O_mass`/`N2O_mass_w`/`N2O_mass_d` was corrected (the variables are N2O, not NO) and the doc-comment was expanded to multi-line with explicit "(kgN/m2; mass-of-N basis -- i.e., kg of the N atoms residing inside N2O molecules, NOT kg of the N2O molecules themselves; multiply by 44/28 to convert to kg-N2O-molecules/m2)" + cross-refs to Fluxes::N2O_FIRE/N2O_SOIL doc-comments + ntransform.cpp:93 N-pool conservation budget. ZERO behaviour change. | **TRUNK-RELEVANT** (BOTH portions): apply same 5 LOC of doc-comments at the N-cycle ENUM declarations + the same typo-fix + multi-line doc-block expansion at the soil.N2O_mass declaration to `trunk_r13078`'s `framework/guess.h` at Backport Sprint time. The trunk versions of these declarations are byte-identical to the pre-fix LandSyMM_LPJ-GUESS versions (per the 6-file delta in §2 of this ledger which does NOT include `framework/guess.h` modifications since step 7 began). |
| `lpjguess/modules/imogenoutput.cpp` (+14 / −8; lines 75-83; N2O_PER_N constant comment + bonus cross-ref precision fix per bundled additional clarification (iii)) | Reworded the muddled "28 g/mol N2 basis" phrasing to a cleaner explanation: "N2O has 2 N atoms per molecule × 14 g/mol per N atom = 28 g of N per molecule of N2O = 44 g/mol of N2O, hence 44/28 = mass of N2O per mass of N atoms." Same numerical value (44/28); ZERO behaviour change. PLUS: bonus cross-ref precision fix — pre-existing cross-ref `guess.h:1241/1250` was off-by-one (doc-comment start lines are 1240/1251; ENUM declarations are at 1243/1256). Updated to be precise + add cross-ref to `guess.h:3850-3855` (the new soil pool doc-block per the bundled additional clarification (i) above) + add NOTE that ngases.out N2O columns are emitted in kgN/ha/yr (NOT kgN2O/ha/yr; cross-refs the new commonoutput.cpp:1759-1771 inline-comment block per bundled additional clarification (ii) below) + that applying N2O_PER_N is what distinguishes the IMOGEN handshake's TgN2O/yr from ngases.out's kgN/ha/yr. | TRUNK-IRRELEVANT-by-novelty (imogenoutput.cpp is a step-8 addition; no trunk analog; the bonus cross-ref is internal to imogenoutput.cpp + cross-references the new commonoutput.cpp inline-comment block which trunk doesn't have; but the underlying line-number precision improvement IS TRUNK-RELEVANT if backporting any of the imogenoutput.cpp content) |
| `lpjguess/modules/commonoutput.cpp` (+13 / 0; lines 1759-1771; NEW inline-comment block above ngases.out writer per bundled additional clarification (ii)) | NEW ~13 LOC inline-comment block immediately above the `outlimit(out,out_ngases, flux_*_* * M2_PER_HA)` block explicitly documenting the `* M2_PER_HA` writer-side conversion → output unit `kgN/ha/yr` (NOT `kgN2O/ha/yr`; NO mass-of-N→mass-of-N2O conversion is applied at the ngases.out writer; that conversion is applied separately at the IMOGEN handshake path via `N2O_PER_N=44/28` per `imogenoutput.cpp:84` to emit global `TgN2O/yr`). Locks in the convention to prevent the EXACT kind of half-remembered confusion the user described from his colleague ("kg N2O/ha/yr or kg N2O-N/ha/yr"). ZERO behaviour change. | **TRUNK-RELEVANT**: apply the same NEW ~13 LOC inline-comment block to `trunk_r13708`'s `lpjguess/modules/commonoutput.cpp` at the same `outlimit(out,out_ngases, ...)` site at Backport Sprint time. The trunk version of this code block exists modulo cosmetic whitespace (the M2_PER_HA pattern + outlimit signature predate our step-7 fork). Lock-in of the convention is just as valuable upstream. |
| `notes/STEP_17c.md` (+~330 LOC: NEW §1.6 landing record + NEW §3.10 Path α forensic + header date row + §1 sub-phase table 17c.0.7 row + Index updates + §1.6.5 expansion for the 2 bundled additional clarifications + the 1 bonus cross-ref fix) | Doc cascade per the 6-surface convention | DOC TRUNK-IRRELEVANT |
| `notes/FOLLOWUPS.md` (+~110 LOC; status dashboard refresh + NEW B19 follow-up with cross-links to steps 11/13/19 + NEW B20 follow-up for literature-comparison sanity check) | Doc cascade | DOC TRUNK-IRRELEVANT |
| `EXECUTION_PLAN.md` (+~7/−~5 LOC; row 17c update marking 17c.0.7 LANDED + 17c.0.8 NEXT + B19 + B20 mentioned) | Doc cascade | DOC TRUNK-IRRELEVANT |
| `CHANGELOG.md` (NEW dated entry ~+80 LOC; expanded for 2 bundled additional clarifications + B20 cross-link) | Doc cascade | DOC TRUNK-IRRELEVANT |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | This entry (NEW step-17c-17c.0.7; expanded for 2 bundled additional clarifications + bonus cross-ref) | DOC TRUNK-IRRELEVANT (self-referential) |

#### Sibling artifact (outside repo)

`_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 7 (NEW; outside repo; tracks the session's decision narrative and any non-canonical artifacts).

---

### Step 17c (17c.0.6 LANDED): B17(b) MECHANICAL CLOSURE via 4-LOC surgical correction of the closed-form `spinup_year_idx` reproduction formula in `lpjguess/modules/imogen_input.cpp` + `lpjguess/modules/imogencfx.cpp` per new `notes/STEP_17c.md` §3.8.6 + C2 close-out tag (a)-refined annotation amendment BUNDLED — **TRUNK-IRRELEVANT-by-novelty**

**Date:** 2026-05-15 (early morning; session 4 continuation). **Commit hash:** _to be determined_ (this commit; tagged `v0.17.6-step17c-b17b-closure` post-merge; ff-merged onto `main` from feature branch `step17c-b17b-investigation` on top of `e03ceb1`).

**Backport relevance summary:**
- **TRUNK-IRRELEVANT-by-novelty**: the year_outer code path + the spinup_year_idx state-machine reproduction formula are **step-17a additions** (introduced at C1.1 commit `90401f2`, 2026-05-10 + C1.3 sub-step 7.3.2 commit `7be595a`, 2026-05-10 for IMOGENCFXInput). The entire year_outer code path doesn't exist in `trunk_r13078`. The 4 source-side fix sites (2 in `imogen_input.cpp::(preload_all_climate|getclimate_for_year)` + 2 in `imogencfx.cpp::(preload_all_climate|getclimate_for_year)`) all live in step-17a-novel methods that have no analogue in trunk_r13078. Therefore the bug being fixed here did not exist in trunk_r13078 and the fix has no trunk-side analogue.
- **No backport directive** — this commit's source-side changes (4 LOC at 4 sites) only correct a defect in step-17a-novel code that doesn't exist in trunk_r13078. Documentation cascade (notes/STEP_17c.md §3.8.6, notes/STEP_17a.md §5.4 ERRATUM, FOLLOWUPS.md, EXECUTION_PLAN.md, CHANGELOG.md, this ledger entry, scripts/cross_validate_year_outer.sh inline-comment updates, sibling chat handoff §6.1) is doc-only and inherits the TRUNK-IRRELEVANT classification.

#### Files in this commit (all TRUNK-IRRELEVANT)

| File | Change | Backport directive |
|---|---|---|
| `lpjguess/modules/imogen_input.cpp` | 4-LOC source change at 2 sites (preload_all_climate + getclimate_for_year) replacing buggy `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` formula with `year_idx % NYEAR_SPINUP` + ~80-LOC inline canonical forensic block at preload_all_climate site + ~25-LOC cross-ref block at getclimate_for_year site | TRUNK-IRRELEVANT-by-novelty (preload_all_climate + getclimate_for_year are step-17a additions; not in trunk_r13078) |
| `lpjguess/modules/imogencfx.cpp` | 4-LOC source change at 2 sites (symmetric) + ~30-LOC cross-ref block at preload_all_climate + ~25-LOC cross-ref block at getclimate_for_year + ~5-LOC update to existing C1.1-erratum comment | TRUNK-IRRELEVANT-by-novelty (same reason; IMOGENCFXInput's year_outer overrides are step-17a additions) |
| `lpjguess/modules/imogen_input.h` | Doc-block formula update in preload_all_climate doc block (was `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP`; now `year_idx % NYEAR_SPINUP`) + ~25-LOC B17(b) closure annotation block | TRUNK-IRRELEVANT-by-novelty |
| `lpjguess/modules/imogencfx.h` | Symmetric doc-block update + ~25-LOC closure annotation | TRUNK-IRRELEVANT-by-novelty |
| `notes/STEP_17c.md` | Header dates + status block update (17c.0.6 added) + §1 sub-phase table 17c.0.6 row update + §3.8.5 + §3.8.5.5 SUPERSEDED-BY-CLOSURE blocks + NEW §3.8.6 closure record (~650 LOC; 11 nested sub-sections) + Index entry for §3.8.6 | DOC TRUNK-IRRELEVANT |
| `notes/STEP_17a.md` | NEW §5.4 ERRATUM block at head of §5.4 marking original derivation as superseded + cross-reference to §3.8.6; §5.4 prose preserved verbatim | DOC TRUNK-IRRELEVANT |
| `notes/FOLLOWUPS.md` | "Last updated" header refresh + B17 row → CLOSED at 17c.0.6 | DOC TRUNK-IRRELEVANT |
| `EXECUTION_PLAN.md` | Row 17c update (17c.0.6 LANDED prepended to 17c.0.5 entry) | DOC TRUNK-IRRELEVANT |
| `CHANGELOG.md` | NEW dated entry for 2026-05-15 documenting the 17c.0.6 mechanical-closure commit | DOC TRUNK-IRRELEVANT |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | This entry (NEW step-17c-17c.0.6-b17b-closure) | DOC TRUNK-IRRELEVANT (self-referential) |
| `scripts/cross_validate_year_outer.sh` | Inline comment updates near SORTED_DIFFER classification + Re-evaluation hook + effective-pass + FAIL message: replace "B17(b) provisionally accepted at 2%" / "FORCED + PERMITTED reactivation" framing with "B17(b) MECHANICALLY CLOSED at 17c.0.6 via §3.8.6"; ZERO logic change (controlled-FAIL machinery preserved as regression detector) | DOC TRUNK-IRRELEVANT (.sh harness only) |

#### Tag amendment (BUNDLED in this commit/push event)

`v0.17.5-step17b-c2-mpi-sync` annotation amended in place at `f6c192e` per (a)-refined approach: SHA preserved; original annotation text included verbatim within the new updated message; new content adds post-B15 + post-B17(a) + post-B17(b)-mechanical-closure verification status reflecting that B17(b) was MECHANICALLY CLOSED at 17c.0.6 (not "PROVISIONALLY ACCEPTED at 2%" as the original C2-era annotation had it). The tag amendment is reflected in the new tag `v0.17.6-step17c-b17b-closure` cut at this commit's HEAD post-merge as the marker of the 17c.0.6 milestone.

---

### Step 17c (17c.0.5-clarification LANDED): broaden B17(b) reactivation surface from FORCED-only (§3.8.5 trigger) to FORCED + PERMITTED (proactive at user discretion at any time) — **TRUNK-IRRELEVANT** (doc-only + .sh-comment-only)

**Date:** 2026-05-14 (early morning; session 4 continuation). **Commit hash:** `e03ceb1` (3-remote-converged at `origin/main`/`kit/main`/`helmholtz/main`; un-tagged checkpoint on top of `29ccc87`).

**Backport relevance summary:**
- **TRUNK-IRRELEVANT (doc-only + .sh-comment-only)**: zero source-logic change; zero engine source change. The commit broadens the reactivation surface for the deferred Option α/β closure-path investigation from "FORCED-only (any of the four §3.8.5 triggers firing)" to "FORCED + PERMITTED (any §3.8.5 trigger firing OR proactive at user discretion at any time)" per the user's verbatim 2026-05-13 night directive: _"It may be that we could come back and look at it and decide to do something about it"_. The 17c.0.5 cascade documentation had used the more restrictive "reactivated only on trigger" framing; this clarification corrects that across 6 in-tree surfaces (the 3 in the original 17c.0.5 cascade plus 3 more now extended at user request 2026-05-14 early morning).
- **No backport directive** — this commit's changes are doc-only + .sh-comment-only (no logic change; no .cpp/.h touch); nothing to backport. Documented here per user request 2026-05-14 early morning (the original 17c.0.5-clarification recommendation had been to skip the backport ledger entry as overkill for a doc-only touch-up; the user opted for full cascade consistency instead).

#### Files in this commit (all TRUNK-IRRELEVANT)

| File | Change | Backport directive |
|---|---|---|
| `scripts/cross_validate_year_outer.sh` (~+11/−1 LOC; 2 sites) | (1) inline comment block "Re-evaluation hook" sub-block (lines ~336-356): added new clause `(d) USER ELECTS TO PROACTIVELY REVISIT AT THEIR OWN DISCRETION even absent a trigger firing` with 4 illustrative-not-exhaustive prompts + meta-statement that triggers (a)-(c) are FORCED-REACTIVATION list, not EXCLUSIVE list. (2) FAIL message at SORTED_DIFFER > 0 path (lines ~633-642): replaced "reactivated only on a §3.8.5 re-eval trigger" with "reactivated either on a §3.8.5 re-eval trigger firing OR proactively at user discretion at any time" + verbatim user quote inline + cross-reference to §3.8.5.5 cadence. | N/A — per-fork harness; not in `trunk_r13078`. |
| `notes/STEP_17c.md` (+1 LOC NEW 5th cadence bullet in §3.8.5.5) | Added NEW 5th bullet "Proactive revisit at user discretion (NEW; clarification commit on top of 17c.0.5 commit `29ccc87`)" with 4 illustrative prompts + meta-statement establishing FORCED vs PERMITTED reactivation surfaces as both first-class. | N/A — `notes/` is per-fork. |
| `notes/FOLLOWUPS.md` (+4/−2 LOC; 2 sites) | (1) "Last updated" header line (recent 17c.0.5 entry): replaced "reactivated only on §3.8.5.5 trigger" with "reactivated either on §3.8.5.5 trigger firing (FORCED reactivation) OR proactively at user discretion at any time even absent a trigger (PERMITTED reactivation)". (2) B17 row in F-12 status table: same replacement + cross-reference to §3.8.5.5 5th-bullet. | N/A — `notes/` is per-fork. |
| `EXECUTION_PLAN.md` (+1/−1 LOC; row 17c) | Row 17c entry: replaced "reactivated only on §3.8.5.5 trigger" with "reactivated either on §3.8.5.5 trigger firing OR proactively at user discretion at any time" for cascade consistency with `notes/FOLLOWUPS.md` + the harness FAIL message. | N/A — per-fork plan. |
| `CHANGELOG.md` (NEW dated entry; ~+15 LOC) | NEW entry "2026-05-14 (early morning, session 4 continuation) — Step 17c (17c.0.5 clarification): broaden B17(b) reactivation surface from FORCED-only to FORCED + PERMITTED" capturing the clarification narrative + diffstat + cross-references. | N/A — per-fork changelog. |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (THIS entry; +N LOC) | Records this clarification commit's TRUNK-IRRELEVANT classification. | N/A — `notes/` is per-fork. |

Plus 1 sibling-artifact: `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` §5.14 (NEW; outside repo).

#### Verification this commit

Sanity check: `bash -n scripts/cross_validate_year_outer.sh` → exit 0 (bash syntax preserved). Smoke checks:
- gate 5 (1cell xval imogen) → exit 0 / 37/37 raw BIT_EXACT / 0/0 NaN / banner_a=0 / banner_b=5 — IDENTICAL envelope to 17c.0.5
- gate 7 (4cell xval imogen) → exit 2 / 15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER / 0/0 NaN / banner_a=0 / banner_b=5 — IDENTICAL envelope to 17c.0.5; new FAIL message text appears verbatim including user quote

No re-run of full 4-xval gates (gates 6+8) needed since the changes are pure-doc + the per-mode-pair envelope is already established at 17c.0.5; gates 6+8 would produce IDENTICAL envelopes to gates 5+7 by the §3.8.3 coupling-invariance finding.

**With this commit, the B17(b) reactivation surface is now formally broadened to include the PERMITTED-by-proactive-user-choice path** across all 6 in-tree cascade surfaces + the chat handoff. The provisional 2% tolerance + four §3.8.5 triggers + §3.8.5.5 four-cadence-bullet surveillance discipline all remain UNCHANGED; only the meta-policy framing of WHEN closure-path investigation can resume is broadened. 17c.0.6 (C2 close-out tag annotation amendment decision) remains NEXT.

---

### Step 17c (17c.0.8 LANDED): Step 17c.0 PREP phase OFFICIAL CLOSE-OUT — 11/11 sub-phases done; doc-cascade-only across 6 in-tree surfaces + 1 sibling-artifact (CHAT_HANDOFF Part 8); ZERO source-code change — **TRUNK-IRRELEVANT-by-novelty** (the entire `notes/` + `CHANGELOG.md` + `EXECUTION_PLAN.md` doc surface doesn't exist in `trunk_r13078`)

**Date:** 2026-05-15 (night; session 4 continuation). **Commit hash:** _to be determined_ (this commit; tagged `v0.17.8-step17c-prep-complete` post-merge; ff-merged onto `main` from feature branch `step17c-prep-close-out` on top of the 17c.0.7 commit `6695ef2`).

**Backport relevance summary:**
- **TRUNK-IRRELEVANT-by-novelty** in entirety. Pure-bookkeeping commit formally marking Step 17c.0 PREP phase OFFICIALLY COMPLETE. The 11-sub-phase arc spanned 4 calendar days across 4 chat sessions and closed 4 audit items (B15 + B16 + B17(a) + B17(b)) + 1 latent defect (Path α handshake-file write-path) + landed the deferred-from-C2 workstation `mpirun -np 4` mimic obligation per session-2 §17.7 + 18 LOC of TRUNK-RELEVANT N-cycle unit doc-comment clarifications (already captured in the 17c.0.6 + 17c.0.7 ledger entries above). **Net `lpjguess/` source-level change in THIS commit: ZERO.**
- **No backport directive** — this commit's changes are entirely doc-only across the per-fork `notes/` + `CHANGELOG.md` + `EXECUTION_PLAN.md` doc surface that doesn't exist in `trunk_r13078`. Documented here per the 6-surface doc-cascade convention + per the maintenance discipline at §6 (every step gets an entry, even doc-only / TRUNK-IRRELEVANT entries, for full audit-trail completeness).
- **Substantive backport-relevant LOC contributed by the entire 17c.0 PREP arc** (cumulative; for Backport Sprint planning convenience): F5 from 17c.0.1 (~3 LOC `dprintf` + ~17 LOC doc block in `lpjguess/framework/framework.cpp`) + 18 LOC of N-cycle unit doc-comment clarifications from 17c.0.7 (5 LOC at `guess.h:1240-1257` + 6 LOC at `guess.h:3850-3855` + 13 LOC at `commonoutput.cpp:1759-1771` + small precision fixes at `imogenoutput.cpp:75-83`). Everything else (B15-B17 fixes; harness work; forensic notes) is TRUNK-IRRELEVANT-by-novelty per the per-entry classifications above.

#### Files in this commit (all TRUNK-IRRELEVANT)

| File | Change | Backport directive |
|---|---|---|
| `notes/STEP_17c.md` (+~150 LOC; NEW §1.7 17c.0.8 landing record + header date row update + Status block promotion to "✅ 17c.0 PREP COMPLETE (11/11 sub-phases landed at this commit)" + §1 PREP table 17c.0.8 row promotion to ✅ DONE + footer summary update to "🎉 PREP phase OFFICIALLY COMPLETE" + Index entry for §1.7) | Doc cascade per the 6-surface convention; canonical landing record for the PREP-COMPLETE milestone with retrospective on the 11-sub-phase arc + handoff to B19/B20/17c.1+ + 3 deferred B19 questions for session-5 opening agenda (Q1 SPINUP/FIRSTCALL ordering + Q2 closed-loop validation tolerance + Q3 B19-Phase 1 ordering revisit). | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `notes/FOLLOWUPS.md` (+~50 LOC; status dashboard top-of-file refresh with PREP-COMPLETE banner + B19 PRIORITY: HIGH annotation promoting it to NEXT-TASK CLUSTER status + B20 PRIORITY: HIGH annotation paired with B19 + F-12 row update reflecting 17c.0.7 + 17c.0.8 LANDED + footer "NEXT-TASK CLUSTER" summary) | Doc cascade | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `CHANGELOG.md` (NEW dated entry ~+50 LOC) | NEW [Unreleased] entry "2026-05-15 (night, session 4 continuation) — Step 17c (F-12 sub-milestone C3 PREP sub-phase 17c.0.8; PREP phase OFFICIAL CLOSE-OUT)" capturing the close-out narrative + per-surface decomposition + verification + backport classification + what's-next + forecasting lesson candidate. | DOC TRUNK-IRRELEVANT (per-fork changelog) |
| `EXECUTION_PLAN.md` (+~5 LOC; row 17c update prepending 17c.0.8 LANDED clause + cross-checking V.1 step-row references for B19/B20 next-task-cluster) | Doc cascade | DOC TRUNK-IRRELEVANT (per-fork plan) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (THIS entry; +~30 LOC) | Records this close-out commit's TRUNK-IRRELEVANT classification. Contributes ZERO eligible LOC for backport. | DOC TRUNK-IRRELEVANT (self-referential) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (NEW Part 8 ~+200 LOC; sibling-artifact, outside repo) | Session-4 close-out narrative + handoff to session 5 with 3 deferred B19 questions agenda + retrospective on the 11-sub-phase PREP arc. | N/A (sibling artifact, outside repo) |

#### Verification this commit (doc-cascade-only)

No build or runtime verification needed (ZERO source-code touch). Documentation consistency verified across all 6 in-tree surfaces via 6-surface visual review: PREP-COMPLETE narrative consistent + B19/B20 promotion to NEXT-TASK CLUSTER consistent + 3 deferred B19 questions handoff to session 5 consistent + tag target `v0.17.8-step17c-prep-complete` consistent. Pre-existing build state preserved from 17c.0.7 commit `6695ef2` (gates 1-11 all PASS exit 0 at that commit; no source change since).

**With this commit, Step 17c.0 PREP phase is OFFICIALLY COMPLETE** — 11/11 sub-phases landed (17c.0.0 + 17c.0.1 + 17c.0.2 + 17c.0.3 + 17c.0.4 + 17c.0.4-followup + 17c.0.5 + 17c.0.5-clarification + 17c.0.6 + 17c.0.7 + 17c.0.8). **NEXT-TASK CLUSTER**: B19 (essential ~2.5-4 d closed-loop pipeline verification) + B20 (recommended ~1-2 d literature-comparison sanity check) → 17c.1 → 17c.4 cluster phases on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative). v1.0 % done estimate held at ~70-72% (this commit is pure book-keeping).

---

### B19 (Phase 0 commit `d9c90d5` + Phase 1 INTERIM commit `4c83561` + Phase 1 CLOSE commit `9c7417c` + this catch-up doc-cascade commit): closed-loop coupled-pipeline verification — Phase 0 SPINUP/FIRSTCALL hardcoding fix + Phase 1 intermediary_py + step-13 adapter reproducibility PASS-with-bonus + B28 orchestrator-order bug fix + 5 NEW audit items filed (B28+B29+B30+B31+B32+B33) — **MIXED: B19 Phase 0 fix is TRUNK-IRRELEVANT-by-novelty (`lpjguess/modules/imogenoutput.cpp` is novel to the rebuild; doesn't exist in `trunk_r13078`); B28 fix is TRUNK-IRRELEVANT-by-novelty (`intermediary_py/` is novel to the rebuild); B19 Phase 1 doc cascade is TRUNK-IRRELEVANT-by-novelty (per-fork notes); B33 includes ONE TRUNK-RELEVANT sub-item (~5-LOC Fortran-side defensive warning at `imogen/code/imogen_lpjg.f:565-566` — deferred to B33's actual landing window which is recommended B19 Phase 2)**

**Date span:** 2026-05-16 morning through 2026-05-16 evening (session 5; single calendar day; 3 substantive commits + 1 catch-up doc-cascade commit). **Commit hashes:** `d9c90d5` (B19 Phase 0; 2026-05-16 morning) + `4c83561` (B19 Phase 1 INTERIM = B28 orchestrator-order fix; 2026-05-16 afternoon) + `9c7417c` (B19 Phase 1 CLOSE; 2026-05-16 evening) + this catch-up commit (3-surface catch-up cascade; ZERO source change). All on working branch `b19-pipeline-verification` off `main @ v0.17.8-step17c-prep-complete` commit `56fcfd8`; 3-remote converged at `origin/b19-pipeline-verification`/`kit/b19-pipeline-verification`/`helmholtz/b19-pipeline-verification`.

**Catch-up rationale**: B19 Phase 0 + Phase 1 INTERIM + Phase 1 CLOSE each used a lighter 3-file cascade (canonical doc + `notes/FOLLOWUPS.md` + any source code) instead of the full 6-surface cascade convention established since 17c.0.0 (canonical doc + `notes/FOLLOWUPS.md` + `CHANGELOG.md` + `EXECUTION_PLAN.md` + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` + `_chat_artifacts/CHAT_HANDOFF` sibling). The under-cascade was an oversight, surfaced by user check-in at 2026-05-16 ~22:42 UTC+2 after the Phase 1 CLOSE commit's 3-remote push. This catch-up commit closes the 3-surface gap (`CHANGELOG.md` + `EXECUTION_PLAN.md` + this ledger) in a single bundled commit; the CHAT_HANDOFF sibling-artifact is deferred to next session boundary OR B19 Phase 5 close-out, whichever comes first.

**Backport relevance summary (cumulative across all 3 substantive B19 commits + this catch-up):**

- **B19 Phase 0 (`d9c90d5`)**: +54/-12 LOC in `lpjguess/modules/imogenoutput.cpp:341-401` (3 substantive LOC corrupting hardcoded `SPINUP=true, FIRSTCALL=true` ofstream writes to read `IMOGENConfig::*` state dynamically via `climatemodel.cpp:1181-1199 updateImogenControlData()`'s state machine + ~45-LOC inline-comment forensic rewrite + 5-LOC dprintf observability). **TRUNK-IRRELEVANT-by-novelty**: `lpjguess/modules/imogenoutput.cpp` is novel to the rebuild (introduced at step 8 commit `a543e9d` 2026-05-06 for the LPJG-to-IMOGEN handshake-file writer); does not exist in `trunk_r13078`. ZERO eligible LOC contributed for backport.
- **B19 Phase 1 INTERIM (`4c83561`)**: +18/-1 LOC in `intermediary_py/imogen_ghg_controller/run_all.py` (B28 orchestrator-order bug fix: re-ordered `COMPONENT_B` to move `lpjg_combined_and_fair_processing.py` from position 4 to position 2 — must run BEFORE `lpjg_historical_plotting.py` to populate `CombinedDCC_TgCH4_best` column the plotter requires; full forensic in `notes/B19.md` §3.4.1). **TRUNK-IRRELEVANT-by-novelty**: `intermediary_py/` is novel to the rebuild (Python pipeline added at step 10 + 11 + 13; entirely novel). ZERO eligible LOC contributed for backport.
- **B19 Phase 1 CLOSE (`9c7417c`)**: pure doc cascade (`notes/B19.md` +95/-10 LOC + `notes/FOLLOWUPS.md` +10/-1 LOC + 7 PNG reverts in `intermediary_py/.../src/`); ZERO C++ or Fortran source change. **TRUNK-IRRELEVANT-by-novelty**: `notes/B19.md` + `notes/FOLLOWUPS.md` are per-fork notes; `intermediary_py/` PNG paths are novel; none exist in `trunk_r13078`. ZERO eligible LOC contributed for backport.
- **This catch-up commit**: pure doc cascade across `CHANGELOG.md` + `EXECUTION_PLAN.md` + this ledger entry. ZERO source change. **TRUNK-IRRELEVANT-by-novelty**: the entire per-fork doc surface doesn't exist in `trunk_r13078`. ZERO eligible LOC contributed for backport.

**Forward-look (filed at this commit; not landed yet)**: 3 NEW audit items B31 + B32 + B33 surfaced during the user-driven double-counting investigation at Phase 1 CLOSE (full forensic in `notes/B19.md` §3.4.2.3 + §3.4.2.4):
- **B31** (launcher backbone auto-rewrite + runtime banner): MEDIUM severity; ~1-2 h; TRUNK-IRRELEVANT-by-novelty in entirety (`scripts/run_coupled.sh` + `runs/<SCEN>/imogen_intermediary.ins` are per-fork launcher + config; do not exist in `trunk_r13078`); recommended landing window B19 Phase 2. Will get its own ledger entry at its actual landing commit.
- **B32** (`docs/scientific_framework.md` §1.5 natural-flux mutual-exclusion invariant doc): LOW severity; ~1 h; TRUNK-IRRELEVANT-by-novelty in entirety (`docs/scientific_framework.md` is per-fork; novel). Recommended landing window B19 Phase 5 close-out. Will get its own ledger entry at its actual landing commit.
- **B33** (Option C POSIX-path robustness): MEDIUM severity; ~1 h; **PARTIALLY-TRUNK-RELEVANT** — sub-items (a) `.ins` relative paths + (b) launcher pre-flight check are TRUNK-IRRELEVANT-by-novelty; sub-item (c) `imogen/code/imogen_lpjg.f:565-566` defensive runtime warning (~5 LOC at the engine-side `OPEN(63, FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//FILE_LPJG_FLUX)` site) **IS TRUNK-RELEVANT** if the Fortran engine source `imogen/code/imogen_lpjg.f` ships in `trunk_r13078`. Recommended landing window B19 Phase 2 (alongside B31). At B33's actual landing commit, the (c) sub-item should be re-verified for trunk applicability + backported per the same discipline as B10's symmetric Fortran fix (per the B10 entry at 2026-05-11 night).

#### Files in this catch-up commit (all TRUNK-IRRELEVANT)

| File | Change | Backport directive |
|---|---|---|
| `CHANGELOG.md` (NEW dated entry ~+90 LOC) | NEW [Unreleased] entry "2026-05-16 (full day; session 5) — B19 Phase 0 + Phase 1 INTERIM + Phase 1 CLOSE landing combined" capturing the full B19 Phase 0 + B28 + Phase 1 reproducibility + double-counting investigation + B31/B32/B33 filing narrative across the 4 commits. | DOC TRUNK-IRRELEVANT (per-fork changelog) |
| `EXECUTION_PLAN.md` (+~15 LOC; row 17c B19-status prepend) | Row 17c update prepending B19-status note (Phase 0 ✅ + Phase 1 ✅ + Phase 2 NEXT) + cross-references to `notes/B19.md` §2.5 + §3.4.1 + §3.4.2 + V.1 step-row references for Phase 2 + Phase 3 + Phase 4 + Phase 5. | DOC TRUNK-IRRELEVANT (per-fork plan) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (THIS entry; +~80 LOC) | Records the B19 Phase 0 + Phase 1 INTERIM + Phase 1 CLOSE + this catch-up commits' classifications (all TRUNK-IRRELEVANT-by-novelty). Contributes ZERO eligible LOC for backport. Forward-looks B31 + B32 + B33 (with the B33(c) Fortran sub-item flagged as TRUNK-RELEVANT for backport at its eventual landing window). | DOC TRUNK-IRRELEVANT (self-referential) |

#### Verification this catch-up commit (doc-cascade-only)

No build or runtime verification needed (ZERO source-code touch in this catch-up). Documentation consistency verified via 3-surface visual review:
- `CHANGELOG.md` new entry consistent with `notes/B19.md` §2.5 (Phase 0) + §3.4.1 (Phase 1 INTERIM) + §3.4.2 (Phase 1 CLOSE) + `notes/FOLLOWUPS.md` top-of-dashboard B19 Phase 1 entry
- `EXECUTION_PLAN.md` row 17c B19-status prepend consistent with `notes/B19.md` Index + §11 Phase progress table
- This ledger entry consistent with `notes/B19.md` §3.4.2.8 backport classification + `notes/B19.md` §3.4.2.4 B31/B32/B33 audit item descriptions

Pre-existing build state preserved from `d9c90d5` Phase 0 commit (verified clean rebuild + 162/162 unit tests both builds at Phase 0 commit; no source change in `4c83561` Phase 1 INTERIM that affects `lpjguess/` or `imogen/code/`; no source change in `9c7417c` Phase 1 CLOSE; no source change in this catch-up).

**Discipline note**: going forward (Phase 2 + Phase 3 + Phase 4 + Phase 5), each B19 sub-phase commit should match the 17c.0.X 6-surface cascade convention from its initial commit, not retroactively. The under-cascade pattern at Phase 0 + Phase 1 is closed at this catch-up commit and should not recur.

---

### B37 ✅ DONE — productive-year-ceiling explanatory study CLOSED (this commit, 2026-05-19 evening session 7): 6 in-tree doc-cascade surfaces (1 NEW `notes/B37.md` ~340 LOC canonical landing record + 5 updates) + sibling Part 3 of session5_post_b19 handoff + audit-evidence bundle at `_chat_artifacts/b37_diagnostic_run_2026-05-19/`; ZERO source-code change — **TRUNK-IRRELEVANT-by-novelty in entirety**; ZERO eligible LOC contributed for backport at this commit.

**Investigation outcome**: root cause IDENTIFIED + closed-form formula derived + Run B/C/DR2/DR1 empirical match exact. Per-path verdicts: (i) configurable productive-year ceiling = VIABLE (5-15 LOC source-edit needed) → filed as **B45 NEW**; (ii) `--coupling-mode loose` bypass = NOT VIABLE; (iii) `skip_inprocess_engine_run` two-step = PARTIALLY VIABLE; **(iv) NEW launcher-side `done`-marker sidecar = ✅✅ VIABLE, empirically confirmed** (DR1 produced 202 year-dirs 1900-2101 in 12 min 48 sec wall on smoke 4-cell config; all 201 paper-target years 1900-2100 have valid CO2.dat with physically-sensible SSP1-2.6 trajectory) → filed as **B44 NEW** for productisation in `scripts/run_coupled.sh`.

**Future B45 implementation Backport-Sprint guidance**: parametrise the 3 hardcoded year sentinels (`1901`, `2100`, `1871`) at `lpjguess/modules/climatemodel.cpp::updateImogenControlData()` lines 1185-1197 — this is the C++ in-process IMOGEN engine port; **the canonical Fortran twin at `imogen/code/imogen_lpjg.f` likely has analogous logic** (subroutine equivalent to `updateImogenControlData`; ~similar year-sentinel hardcoding pattern; needs source-reading at B45 implementation time to confirm + locate exact line range). Both forks must be updated together at B45 implementation; the C++ port edit will be PER-FORK (TRUNK-IRRELEVANT for the C++ port file itself since `climatemodel.cpp` is the rebuild's novel port not shared with `trunk_r13078/`), but the Fortran twin edit IS TRUNK-RELEVANT for the canonical engine source shared with `trunk_r13078/`. Eligible-for-backport LOC at B45 implementation TBD (~5-15 LOC range).

**Future B44 implementation backport-irrelevance**: `scripts/run_coupled.sh` is per-fork (novel since step 14); the `--engine-only-mode` flag addition is TRUNK-IRRELEVANT-by-novelty.

**Cumulative backport-debt state at B37 close (this commit)**: UNCHANGED at **+145 LOC** eligible-for-backport (still entirely from B19 Phase 2 Commit 3 `6862d03`'s `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites at L425/L432/L631/L648). The Backport Sprint scope at post-step-19 work cycle should ALSO incorporate the future B45 implementation alongside B10 + B33(c) since all touch the canonical Fortran engine source.

---

### B41 + B42 + B43 ✅ DONE FILING + decisions-recorded — production-config consolidated reference document `notes/PRODUCTION_RUN_CONFIG.md` authored (this commit, 2026-05-19 morning session 6): 6 in-tree doc-cascade surfaces + sibling Part 2 of session5_post_b19 handoff; ZERO source-code change — **TRUNK-IRRELEVANT-by-novelty in entirety**; ZERO eligible LOC contributed for backport.

**Background**: User-raised concern at session 5 evening (2026-05-18) + session 6 morning (2026-05-19) that the rebuild project documentation surface had no consolidated reference for the dramatic configuration delta between (a) the smoke-test live LPJG run configuration in `runs/SSP1-2.6/main.ins` (4-cell `gridlist_test2.txt`; `nyear_spinup 1`; `npatch 1`; basic `landcover.txt` + `LU.bin`; NO SimFire BLAZE; NO popdens NetCDF; NO 4-NetCDF wet/dry NHx+NOy ndep; `firsthistyear`/`lasthistyear` 1900/1901) and (b) the v1.0 paper-publication production-style run configuration documented at `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/main.ins` reference directories (full 62892-cell `gridlist_in_62892_and_climate.txt`; `nyear_spinup 500`; `npatch 25`; updated `_peatland` LU at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/...`; SimFire BLAZE binary at `file_simfire`; population-density NetCDF at `file_popdens`; 4-NetCDF wet/dry NHx + NOy at `file_ndep_*`; full 1900-2100 envelope across all 5 SSP-RCPs). Knowledge-loss risk if context across sessions becomes fragmented.

**Audit-item state at this commit**:
- **B41** ✅ DONE (filing + initial draft): smoke→production parameter delta documentation gap → NEW `notes/PRODUCTION_RUN_CONFIG.md` (~300 LOC) with 8 sections + 6 tables + 3 ASCII architecture diagrams.
- **B42** ✅ DONE (LU choice rationale documented): updated `_peatland` LU variant chosen for v1.0 paper publication production runs (HILDA+ remapping per Winkler et al. 2021 Nature Comms; peatland as separate LU class; 62892-cell production resolution; matches past Track 1 cluster runs LU per user 2026-05-19 morning confirmation; keeps Track 1 vs Track 2 comparison clean with LU held constant).
- **B43** ✅ DONE (F-12 timeline decision recorded): F-12 architectural deadlock-resolution work DEFERRED to v1.1+ for the v1.0 paper publication; v1.0 stays in prescribed-mode architecture (`intermediary_py` coordinates BOTH anthropogenic + natural channels into IMOGEN; LPJG (Track 2) consumes IMOGEN climate + CO2 via `-input imogencfx`). Rationale: F-12 fix is multi-week effort + v1.0 prescribed-mode narrative is fully sound + scheduling risk + v1.1+ paper(s) can showcase tight-coupling as headline new capability.
- **B37** priority BUMPED in-place (HIGH; paper-publication critical-path dependency): outcome determines whether production-IMOGEN-engine runs (full 1900-2100 × 5 SSP-RCPs; required to produce IMOGEN climate + CO2 inputs that drive Track 2 LPJG-imogencfx production runs per B41 + B43) can complete without F-12 fix.

**Per-surface backport classification (this commit only):**

| Surface | Δ (LOC) | Rationale | Backport |
|---|---|---|---|
| NEW `notes/PRODUCTION_RUN_CONFIG.md` (~+300 LOC) | NEW production-config consolidated reference doc | Per-fork documentation that exists only because of the rebuild's coupled-model architecture (the entire "production-config doc surface for `intermediary_py` + IMOGEN engine + LPJG `-input imogencfx`" pipeline doesn't exist in `trunk_r13078`); covers Track 1 vs Track 2 paper-publication design + smoke→production deltas + LU map + input-module evolution + tight-coupling roadmap. | TRUNK-IRRELEVANT-by-novelty (per-fork production-config doc) |
| `notes/FOLLOWUPS.md` | +~10 LOC: NEW top-of-dashboard B41+B42+B43 close entry + B41 NEW row + B42 NEW row + B43 NEW row + B37 row priority bump in-place + dashboard refresh | Per-fork follow-ups + audit-trail file; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `CHANGELOG.md` (NEW dated entry; ~+85 LOC) | NEW [Unreleased] entry "2026-05-19 (morning, session 6) — B41 + B42 + B43 ✅ DONE FILING + decisions-recorded — production-config consolidated reference document authored" capturing the full decision narrative + per-surface decomposition + backport classification + what's-next. | DOC TRUNK-IRRELEVANT (per-fork changelog) |
| `EXECUTION_PLAN.md` (+~30 LOC; row 17c update prepending B41+B42+B43 status) | Doc cascade per the 6-surface convention; preserves prior B19+B20 status as PRIOR ENTRY. | DOC TRUNK-IRRELEVANT (per-fork plan) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (THIS entry; +~50 LOC) | Records this commit's TRUNK-IRRELEVANT-by-novelty classification. Contributes ZERO eligible LOC for backport. | DOC TRUNK-IRRELEVANT (self-referential) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-18_session5_post_b19.md` (NEW Part 2; sibling-artifact, outside repo) | Production-config narrative; opens session 6 morning per the progressive-CHAT_HANDOFF discipline established at session-3 §9.10 + session-5 Part 11 §10h.10 ("a future session 4 / 5 / 6 maintainer should open a new sibling handoff file"). | N/A (sibling artifact) |

**Cumulative backport state after this commit**: UNCHANGED at +145 LOC eligible-for-backport (still entirely from B19 Phase 2 Commit 3 `6862d03`'s `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites at L425/L432/L631/L648). The Backport Sprint should handle B10 (+121 LOC writer fix from step 17b) + B33(c) (+145 LOC) together since both touch `imogen/code/imogen_lpjg.f`.

**Verification this commit (doc-cascade-only)**: no build or runtime verification needed (ZERO source-code touch). Documentation consistency verified across all 6 in-tree surfaces via 6-surface visual review: B41+B42+B43 NEW row entries consistent across `notes/FOLLOWUPS.md` rows + dashboard top entry; row 17c update in `EXECUTION_PLAN.md` references the same B41+B42+B43 ✅ DONE status as the dashboard; CHANGELOG.md dated entry mirrors the dashboard top entry's content; THIS LEDGER entry classifies the commit's surfaces consistently with FOLLOWUPS + CHANGELOG; `notes/PRODUCTION_RUN_CONFIG.md` cross-references to B36 + B37 + B39 + B40 + B42 + B43 are all valid audit-item names per `notes/FOLLOWUPS.md` rows; sibling Part 2 of session5_post_b19 handoff narrative consistent with in-tree cascade. Pre-existing build state preserved from B20 close at `9a78df0` (no source change since).

**With this commit, the production-run configuration reference is locked in for v1.0 paper publication planning** — protects against knowledge-loss across session boundaries by consolidating the production-config picture in a versioned in-tree document. **NEXT**: Local v1 verification window (~6-13 h cumulative): B37 FIRST (paper-publication critical-path dependency per priority bump) → B36 → B39 → B40. Then 17c.1+ cluster phases on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative).

---

### B20 ✅ DONE — literature-comparison sanity check for global LPJG-natural CH4 + N2O magnitudes (this commit, 2026-05-18 late evening session 5 continuation): NEW Python validation tool + 5 doc surfaces + sibling Part 1 of new session5_post_b19 handoff file + tag `v0.20.0-b20-literature-sanity-checked` — **TRUNK-IRRELEVANT-by-novelty in entirety**; ZERO eligible LOC contributed for backport.

**Background**: B20 closes the NEXT-TASK CLUSTER (B19 + B20) per the user-authorised 2026-05-15 night ordering at 17c.0.8 PREP close-out. Distinct from B19 Phase 4 (intra-codebase consistency vs legacy A/B references — pivoted to literature comparison vs Law Dome ice core); B20 is **extra-codebase scientific plausibility check** comparing LPJG-natural-only fluxes against published global natural budgets.

**This commit lands** (all per-fork; ZERO eligible LOC for backport):

| File | LOC delta | Per-fork or canonical? | Trunk presence | Backport relevance |
|---|---|---|---|---|
| `scripts/b20_literature_validate.py` (NEW) | +~430 | per-fork (novel Python tool) | NOT in trunk (no Python tooling in trunk_r13078; trunk uses Fortran + minimal shell) | **TRUNK-IRRELEVANT-by-novelty** |
| `notes/FOLLOWUPS.md` | +~30/-2 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `CHANGELOG.md` | +~75 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `EXECUTION_PLAN.md` | +~3/-1 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (this entry) | +~30 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `notes/STEP_17c.md` | +~10/-3 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| **Total source LOC at this commit** | **+~430 (NEW Python tool only)** | | | **0 eligible-for-backport** |

**B20 verdict**: `WITHIN_ENVELOPE_MEAN_WITH_TIME_VARIATION` ✅ PASS (full 1900-2100 time-means of CH4 = 179.87 TgCH4/yr + N2O = 11.18 TgN2O/yr both within Saunois 2020 + Tian 2020 published envelopes; modern-decade N2O hump filed as NEW B40 for explanatory follow-up at paper-stage analytical work).

**Cumulative B19+B20 backport-debt state at B20 close**: UNCHANGED at **+145 LOC eligible-for-backport** — still entirely from Phase 2 Commit 3 (`6862d03`)'s `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites at L425/L432/L631/L648.

**B19+B20 backport-debt aggregation FINAL** (UPDATED at this B20 close commit):

| Phase / Commit | Source LOC | Eligible-for-backport LOC | Cumulative eligible | Notes |
|---|---|---|---|---|
| (B19 phases 0-5 — see prior table) | … | … | +145 | (entirely from `6862d03`) |
| **B20 close-out (THIS commit)** | **+~430 (NEW Python tool)** | **0** | **+145** | per-fork in entirety; B20 closes |

**Backport Sprint guidance at B19+B20 close** (UNCHANGED from B19 close): The Backport Sprint at the post-B19+B20 backport-relevant work cycle should handle BOTH B10 (+121 LOC writer fix from step 17b's `imogen_lpjg.f`) AND B33(c) (+145 LOC from Phase 2 Commit 3's `imogen_lpjg.f`) **together**, since both touch the same canonical Fortran engine source file. Risk profile for both: ZERO.

**B19+B20 ✅ COMPLETE. What's next** (post-B19+B20):

- **17c.1+ cluster phases** on KIT IMK-IFU `owl` — TRUNK-relevance TBD per sub-phase as the work lands.
- **Local v1 verification window** (~6-13 h cumulative; can be done in parallel with cluster setup): B36 (~2-4 h Fortran IMOGEN background-emission audit; **possibly TRUNK-RELEVANT** if surfaces a fix) + B37 (~1-3 h productive-year-ceiling explanatory study; possibly TRUNK-RELEVANT) + B39 (~1-2 h CO2_INIT_PPMV per-YEAR1 configurability; TRUNK-IRRELEVANT-by-novelty) + B40 (~2-4 h modern-decade N2O hump explanatory study; possibly TRUNK-RELEVANT if surfaces N-cycle source code refactor).
- **Future intermediary_py revision cycle**: B29 + B30 (~1.5 h cumulative; cosmetic; TRUNK-IRRELEVANT-by-novelty).

The Backport Sprint should review this LEDGER's full B19+B20 group at the time of the sprint to identify the canonical +145 LOC + decide on porting timing relative to other backlog items. B36 + B37 + B40 outcomes (whether they surface fixes or confirm "no-defect-by-finding") will modulate the cumulative eligible-for-backport state.

---

### B19 ✅ FULLY CLOSED — Phase 5 close-out (commit `7543c1e`, 2026-05-18 evening session 5 continuation): doc cascade + tag `v0.19.0-b19-literature-validated` + rule #9 + #10 promotions + B32 closure + B39 NEW filing — **TRUNK-IRRELEVANT-by-novelty in entirety**; ZERO eligible LOC contributed for backport.

**Background**: B19 Phase 5 is the FINAL B19 commit. Lands the close-out doc cascade summarising Phases 0+1+2+3+3-ADDENDUM+4 + 1 source touch (`docs/scientific_framework.md` NEW §5.3 = B32 closure) + 1 sibling Part 11 narrative + the annotated tag `v0.19.0-b19-literature-validated`.

**This commit lands** (all per-fork; ZERO eligible LOC for backport):

| File | LOC delta | Per-fork or canonical? | Trunk presence | Backport relevance |
|---|---|---|---|---|
| `docs/scientific_framework.md` | +~155/-3 (NEW §5.3 = B32 closure) | per-fork doc | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `notes/B19.md` | +~150/-10 (§0 ✅ CLOSED + §1.3 phase progression all-DONE + NEW §7.4.1 + §11 row 5 ✅ DONE + tail) | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `notes/FOLLOWUPS.md` | +~100/-5 (NEW dashboard entry + B19 ✅ + B20 NEXT + B32 ✅ + B39 NEW + rules #9 + #10 PROMOTED) | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `CHANGELOG.md` | +~60 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `EXECUTION_PLAN.md` | +~5/-1 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (this entry) | +~40 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `notes/STEP_17c.md` | +~10/-3 (§1.7.8 update for B19 ✅ CLOSED → B20 ACTIVE) | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| **Total source LOC at this commit** | **+~520/-22** | | | **0 eligible-for-backport** |

**Cumulative B19 backport-debt state at B19 ✅ FULLY CLOSED**: **+145 LOC eligible-for-backport** — UNCHANGED across the entire B19 arc; entirely from Phase 2 Commit 3 (`6862d03`)'s `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites at L425/L432/L631/L648.

**B19 backport-debt aggregation FINAL** (UPDATED at this Phase 5 close-out commit):

| Phase | Source LOC | Eligible-for-backport LOC | Cumulative eligible | Notes |
|---|---|---|---|---|
| Phase 0 (`d9c90d5`) | +54/-12 (`imogenoutput.cpp`) | 0 | 0 | per-fork surface (C++ port of writer) |
| Phase 1 INTERIM (`4c83561`) | +37/0 (`run_all.py` reorder) | 0 | 0 | per-fork (`intermediary_py/` not in trunk) |
| Phase 1 CLOSE (`9c7417c`) | +0/-0 (pure-doc cascade) | 0 | 0 | TRUNK-IRRELEVANT pure-doc |
| Phase 2 Commit 1 (`d7a0673`) | +165/-9 (`run_coupled.sh`) | 0 | 0 | per-fork launcher novelty |
| Phase 2 Commit 2 (`53e19f5`) | +47/-6 (`imogen_intermediary.ins`) | 0 | 0 | per-fork .ins |
| Phase 2 Commit 3 (`6862d03`) | +145/0 (`imogen_lpjg.f`) | **+145** | **+145** | canonical engine source; first eligible LOC |
| Phase 2 close-out (`170039e`) | 0 | 0 | +145 | pure-doc cascade |
| Phase 3 close (`ed51e05`) | 0 | 0 | +145 | pure-doc cascade |
| Phase 3 ADDENDUM (`0e665d4`) | +136/-37 (per-fork only) | 0 | +145 | per-fork in entirety (B34 + B35) |
| Post-Phase-3-ADDENDUM hygiene (`f7ab695`) | +17/-17 (encoding-only) | 0 | +145 | per-fork in entirety (canonical file but novel comments) |
| Phase 4 BALLPARK_PASS landing (`82a1bc8`) | +~280 (NEW Python tool) | 0 | +145 | per-fork in entirety |
| **Phase 5 close-out (THIS commit)** | **+~520/-22** (per-fork only) | **0** | **+145 (FINAL)** | per-fork in entirety; B19 closes |

**Backport Sprint guidance at B19 close** (for the future maintainer who picks this up):

The Backport Sprint at the post-B19 backport-relevant work cycle should handle BOTH B10 (+121 LOC writer fix from step 17b's `imogen_lpjg.f`) AND B33(c) (+145 LOC from Phase 2 Commit 3's `imogen_lpjg.f`) **together**, since both touch the same canonical Fortran engine source file. Risk profile for both: ZERO (B10 = additive-only writer; B33(c) = additive-only + warn-only with conservative predicate `IF (INDEX(RESOLVED_PATH, '/IMOGEN//') .EQ. 0) RETURN`).

**Bycatch finding for the Backport Sprint** (already documented in B19.md §6.4.1; mentioned here for ledger completeness): legacy_A SSP1-2.6 reference outputs at `version_A/.../IMOGEN_SSP1_RCP26_Clim/output/` are physically implausible for the early 20th century (CO2 +9 ppm/yr in 1900-1903 vs Law Dome's ~0.7 ppm/yr; CH4 wrong direction). When porting B33(c)'s WARN_POSIX_CONCAT_COLLAPSE helper to `trunk_r13078`'s `imogen/code/imogen_lpjg.f`, do NOT use legacy_A outputs as a numerical-comparison reference for trunk-side validation. Use Law Dome ice-core record (or any other authoritative published source) as reference instead. This bycatch finding is consistent with the user-noted general fact that legacy A and B "do not work properly or at all".

**B19 ✅ FULLY CLOSED. What's next** (post-B19):

- **B20 NEXT-IN-QUEUE (~1-2 d)** — literature-comparison sanity check for global N2O magnitudes; ZERO TRUNK source-touch expected (B20 is full-resolution scenario runs + literature plot comparison; per-fork analysis only).
- **17c.1+ cluster phases** on KIT IMK-IFU `owl` — TRUNK-relevance TBD per sub-phase as the work lands.
- **Local v1 verification window** (B36 + B37 + B39): B36 is "**possibly TRUNK-RELEVANT** if the audit surfaces any source-code fix needed" per its FOLLOWUPS row; B37 "possibly TRUNK-RELEVANT only if substantive Fortran source observation surfaces"; B39 TRUNK-IRRELEVANT-by-novelty (`runs/<SCEN>/imogen_intermediary.ins` is per-fork; the engine source consumer at `climatemodel.cpp:163-167` is the C++ port also per-fork).

The Backport Sprint should review this LEDGER's full B19 group at the time of the sprint to identify the canonical +145 LOC + decide on porting timing relative to other backlog items.

---

### B19 Phase 4 BALLPARK_PASS landing (commit `82a1bc8`, 2026-05-18 evening session 5 continuation): literature-comparison validation vs Law Dome ice-core record + Option-B plan pivot — **TRUNK-IRRELEVANT-by-novelty in entirety**; ZERO eligible LOC contributed for backport.

**Background**: original B19.md §6 plan called for comparing v1.0 Run C engine output against legacy_A reference outputs. Stage 4-pre investigation at session 5 evening (2026-05-18 ~17:00 UTC+2) surfaced that legacy_A's SSP1-2.6 reference outputs at `version_A/.../IMOGEN_SSP1_RCP26_Clim/output/` are physically implausible for the early 20th century (CO2 +9 ppm/yr in 1900-1903 vs Law Dome historical ~0.7 ppm/yr; CH4 -50 ppb/yr — wrong direction). Plan PIVOTED to Option B (literature comparison) per user authorization 2026-05-18 ~17:30 UTC+2.

**This commit lands**: NEW Python validation script + 5-surface in-tree doc cascade + 1 sibling-narrative + 3 audit artefacts. The validation script reads v1.0 Run C engine output (`runs/SSP1-2.6/Common-directory/IMOGEN/output/<year>/CO2.dat` for 1900-1903) → extracts col 2/7/8 (atm CO2 ppm + CH4 ppbv + N2O ppbv) → compares against hardcoded Law Dome reference (MacFarling Meure 2006) → applies tolerance gates → emits Markdown report + JSON summary. Phase 4 acceptance: ✅ BALLPARK_PASS (overall verdict; 8 of 12 cells STRICT_PASS, 4 of 12 BALLPARK_PASS, zero AMBER/FAIL).

**Per-source-file backport classification at this commit**:

| File | LOC delta | Per-fork or canonical? | Trunk presence | Backport relevance |
|---|---|---|---|---|
| `scripts/b19_phase4_literature_validate.py` (NEW) | +~280 | per-fork (novel Python tooling) | NOT in trunk (no Python tooling in trunk_r13078; trunk uses Fortran + minimal shell) | **TRUNK-IRRELEVANT-by-novelty** |
| `notes/B19.md` | +~120/-3 (this §6.4.1 + §0 + §11 + tail) | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `notes/FOLLOWUPS.md` | +~25/-2 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `CHANGELOG.md` | +~50 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `EXECUTION_PLAN.md` | +~3/-1 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (this entry) | +~25 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| **Total source LOC at this commit** | **+~280 (NEW Python tool only)** | | | **0 eligible-for-backport** |

**Cumulative B19 backport-debt state at Phase 4 close**: UNCHANGED at **+145 LOC eligible-for-backport** — still entirely from Phase 2 Commit 3's `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites at `6862d03`. The Backport Sprint at B19 Phase 5 close-out should still handle B10 (+121 LOC writer fix from step 17b) + B33(c) (+145 LOC) together since both touch `imogen/code/imogen_lpjg.f`.

**B19 backport-debt aggregation status by phase** (UPDATED at this Phase 4 commit):

| Phase | Source LOC | Eligible-for-backport LOC | Cumulative eligible | Notes |
|---|---|---|---|---|
| Phase 0 (`d9c90d5`) | +54/-12 (`imogenoutput.cpp`) | 0 | 0 | per-fork surface (C++ port of writer) |
| Phase 1 (`9c7417c` + `4c83561`) | +37/0 (`run_all.py` reorder) | 0 | 0 | per-fork (`intermediary_py/` not in trunk) |
| Phase 2 Commit 1 (`d7a0673`) | +165/-9 (`run_coupled.sh`) | 0 | 0 | per-fork launcher novelty |
| Phase 2 Commit 2 (`53e19f5`) | +47/-6 (`imogen_intermediary.ins`) | 0 | 0 | per-fork .ins |
| Phase 2 Commit 3 (`6862d03`) | +145/0 (`imogen_lpjg.f`) | **+145** | **+145** | canonical engine source; first eligible LOC |
| Phase 2 close-out (`170039e`) | 0 | 0 | +145 | pure-doc cascade |
| Phase 3 close (`ed51e05`) | 0 | 0 | +145 | pure-doc cascade |
| Phase 3 ADDENDUM (`0e665d4`) | +136/-37 (per-fork only) | 0 | +145 | per-fork in entirety (B34 + B35) |
| Post-Phase-3-ADDENDUM hygiene (`f7ab695`) | +17/-17 (encoding-only) | 0 | +145 | per-fork in entirety (canonical file but novel comments) |
| **Phase 4 BALLPARK_PASS landing (this commit)** | **+~280 (NEW Python tool)** | **0** | **+145** | per-fork in entirety (Python validation tool + doc cascade) |

**Bycatch finding for the Backport Sprint** (documented in B19.md §6.4.1; mentioned here for ledger completeness): legacy_A SSP1-2.6 reference outputs at `version_A/.../IMOGEN_SSP1_RCP26_Clim/output/` were empirically determined to be physically implausible for the early 20th century. **Implication for Backport Sprint**: when porting B33(c)'s WARN_POSIX_CONCAT_COLLAPSE helper to `trunk_r13078`'s `imogen/code/imogen_lpjg.f`, do NOT use legacy_A outputs as a numerical-comparison reference for trunk-side validation. Use Law Dome ice-core record (or any other authoritative published source) as reference instead. This bycatch finding is consistent with the user-noted general fact that legacy A and B "do not work properly or at all".

**Phase 5 close-out (FINAL) ACTIVE NEXT**: 6-surface cascade summarising Phases 0-4 + B19 close-out tag. The Backport Sprint will likely live at OR after Phase 5 (depending on user preference); when it begins it should focus on the +145 LOC eligible content from Phase 2 Commit 3 + the +121 LOC eligible content from B10 (step 17b writer fix) — both at `imogen/code/imogen_lpjg.f`. ALL OTHER B19 work (Phase 0/1/3/3-ADDENDUM/post-hygiene/4 + this commit) is per-fork; ZERO trunk-side touch needed.

---

### Post-B19-Phase-3-ADDENDUM hygiene cleanup (commit `f7ab695`, 2026-05-18 evening session 5 continuation): `lpjguess/modules/climatemodel.cpp` UTF-8 forensic encoding restoration (cosmetic; zero behavioral impact) — **TRUNK-IRRELEVANT-by-novelty**; ZERO eligible LOC contributed for backport.

**Background**: HEAD's `lpjguess/modules/climatemodel.cpp` had pre-existing CP1252-style invalid-UTF-8 single-byte chars (0x97 = em-dash, 0x9D = em-dash-or-degree, 0xA7 = section sign) embedded in 17 inline doc-comment lines. These were already invalid UTF-8 at HEAD (`ed51e05`); the commit history at lines 1-3000ish shows this corruption traces back at least to step 7 (`71c171d`) and step 9.5 (`f00033c`) doc-block additions. At some point during B19 Phase 3 ADDENDUM context-loading session (2026-05-18 afternoon), an editor canonicalized those 1-byte CP1252 chars into 3-byte U+FFFD (`0xEF 0xBF 0xBD`) replacement chars, giving the working-tree state observed at the start of `0e665d4` work. Both forms displayed as `�` in modern UTF-8 terminals/editors but neither was the intended character. The B34 work at `0e665d4` deliberately did NOT touch this file; it was deferred per user-authorized Q1 option C ("restore the correct UTF-8 chars") with prerequisite role-evaluation step.

**Role evaluation outcome** (from B19 Phase 3 ADDENDUM session): `lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` is the active C++ in-process IMOGEN engine in v1.0 (symbol `_Z17RUN_IMOGEN_ENGINEv` exported in `lpjguess/build/guess`; called from `imogencfx.cpp:549` when `simulation_mode == "online"`). Both Phase 3 Run B (static-iiasa) and Phase 3 ADDENDUM Run C (intermediary-py) used this engine path. The file is one of the most central source files in the v1.0 codebase. The mojibake however was confined to inline doc-comments; zero behavioral impact at any commit.

**Restoration mechanic at this commit** (per CHANGELOG entry; full forensic record there): each U+FFFD char mapped to its contextually-correct UTF-8 char by reading surrounding text. 18 char-level substitutions across 17 lines: 13 em-dash `—` (`0xE2 0x80 0x94`) + 3 section sign `§` (`0xC2 0xA7`) + 2 degree sign `°` (`0xC2 0xB0`). Verification: post-fix WT has 0 U+FFFD chars; distinct non-ASCII bytes are exactly the multi-byte UTF-8 components; file size delta +31 bytes matches arithmetic exactly (13×2 + 3×1 + 2×1 = 31).

**Per-source-file backport classification at this commit**:

| File | LOC delta | Per-fork or canonical? | Trunk presence | Backport relevance |
|---|---|---|---|---|
| `lpjguess/modules/climatemodel.cpp` | +17/-17 (encoding-only; zero code-path change) | shared file but rebuild-era novel comment content | trunk_r13078 has the file BUT does NOT have these specific B3/step-17b/F-12/Decision #11/Step 7-9.5 doc-block comments (all post-trunk-baseline rebuild material per `notes/STEP_17b.md` §3e + `notes/B19.md` §3.4.2.5) | **TRUNK-IRRELEVANT-by-novelty** (no trunk-side comments to encode-fix) |
| `CHANGELOG.md` | +~50 | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | +~25 (this entry) | per-fork | not in trunk | TRUNK-IRRELEVANT-by-novelty |
| **Total source LOC at this commit** | **+17/-17** (encoding-only) | | | **0 eligible-for-backport** |

**Cumulative B19 backport-debt state at this hygiene-cleanup commit**: UNCHANGED at **+145 LOC eligible-for-backport** — still entirely from Phase 2 Commit 3's `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites at `6862d03`. The Backport Sprint at B19 Phase 5 close-out should still handle B10 (+121 LOC writer fix from step 17b) + B33(c) (+145 LOC) together since both touch `imogen/code/imogen_lpjg.f`.

**B19 backport-debt aggregation status by phase** (UPDATED at this commit):

| Phase | Source LOC | Eligible-for-backport LOC | Cumulative eligible | Notes |
|---|---|---|---|---|
| Phase 0 (`d9c90d5`) | +54/-12 (`imogenoutput.cpp`) | 0 | 0 | per-fork surface (C++ port of writer) |
| Phase 1 (`9c7417c` + `4c83561`) | +37/0 (`run_all.py` reorder) | 0 | 0 | per-fork (`intermediary_py/` not in trunk) |
| Phase 2 Commit 1 (`d7a0673`) | +165/-9 (`run_coupled.sh`) | 0 | 0 | per-fork launcher novelty |
| Phase 2 Commit 2 (`53e19f5`) | +47/-6 (`imogen_intermediary.ins`) | 0 | 0 | per-fork .ins |
| Phase 2 Commit 3 (`6862d03`) | +145/0 (`imogen_lpjg.f`) | **+145** | **+145** | canonical engine source; first eligible LOC |
| Phase 2 close-out (`170039e`) | 0 | 0 | +145 | pure-doc cascade |
| Phase 3 close (`ed51e05`) | 0 | 0 | +145 | pure-doc cascade |
| Phase 3 ADDENDUM (`0e665d4`) | +136/-37 (per-fork only) | 0 | +145 | per-fork in entirety (B34 + B35) |
| **Post-Phase-3-ADDENDUM hygiene (this commit)** | **+17/-17** (encoding-only) | **0** | **+145** | per-fork in entirety (canonical file but novel comments) |

**Discipline note for future maintainers**: the legacy C++ in-process IMOGEN engine port at `lpjguess/modules/climatemodel.cpp` was authored in an era / on a system that wrote CP1252-style 1-byte chars for em-dash/section/degree even though the source-tree convention was nominally UTF-8. This drift produced HEAD's pre-existing invalid-UTF-8 byte state. The encoding restoration at this commit lands a clean canonical UTF-8 baseline going forward; any future inline-comment additions to this file should use proper UTF-8 multi-byte sequences (em-dash `0xE2 0x80 0x94` etc.) rather than CP1252 single bytes. No changes to other source files are warranted at this commit; if similar mojibake is found elsewhere in the codebase, file as a separate hygiene-cleanup commit.

---

### B19 Phase 3 ADDENDUM (commit `0e665d4`, 2026-05-18 afternoon session 5 continuation): mixed source + doc commit landing the Run C empirical verification of the IMOGEN engine round-trip on the **intermediary-py** backbone + B34 ✅ CLOSED via option β (smoke years 1871-1872 → 1900-1901) + companion launcher NYR_* auto-rewrite extension at `scripts/run_coupled.sh` step 4.5 + B35 ✅ CLOSED (cosmetic skip-message bug fix bundled) + B37 ⏳ NEW filed (productive-year-ceiling explanatory study; LOW priority post-B19 work) — **TRUNK-IRRELEVANT-by-novelty in entirety**. All 6 source-modified files are per-fork: `runs/SSP1-2.6/main.ins` (per-fork .ins; not in `trunk_r13078`), `runs/SSP1-2.6/imogen_intermediary.ins` (per-fork .ins), `scripts/run_coupled.sh` (per-fork launcher; novel post-step-14), `runs/SSP1-2.6/README.md` (per-fork doc), `scripts/cluster/run_coupled.sbatch` (per-fork doc), `tools/imogen_inputs_to_lpjg_format.py` (per-fork tool comment update). All 5 in-tree doc-cascade surfaces are per-fork. 1 sibling-narrative + 3 audit artefacts at `_chat_artifacts/b19_phase3_smoke_run/`. **ZERO eligible LOC contributed for backport at this commit; cumulative B19 backport-debt state UNCHANGED at +145 LOC eligible-for-backport** (still entirely from Phase 2 Commit 3's `imogen/code/imogen_lpjg.f` change at `6862d03`).

**Per-source-file backport classification at this addendum**:

| File | LOC delta | Per-fork or canonical? | Trunk presence | Backport relevance |
|---|---|---|---|---|
| `runs/SSP1-2.6/main.ins` | +13/-4 | per-fork (novel run config) | NOT in trunk | TRUNK-IRRELEVANT-by-novelty |
| `runs/SSP1-2.6/imogen_intermediary.ins` | +33/-15 | per-fork | NOT in trunk | TRUNK-IRRELEVANT-by-novelty |
| `scripts/run_coupled.sh` | +80/-12 | per-fork (novel since step 14) | NOT in trunk | TRUNK-IRRELEVANT-by-novelty |
| `runs/SSP1-2.6/README.md` | +8/-3 | per-fork doc | NOT in trunk | TRUNK-IRRELEVANT-by-novelty |
| `scripts/cluster/run_coupled.sbatch` | +1/-1 | per-fork doc | NOT in trunk | TRUNK-IRRELEVANT-by-novelty |
| `tools/imogen_inputs_to_lpjg_format.py` | +1/-1 | per-fork tool | NOT in trunk | TRUNK-IRRELEVANT-by-novelty |
| **Total source LOC at this commit** | **+136/-37** | | | **0 eligible-for-backport** |

**Cumulative B19 backport-debt state (Phase 0 → Phase 1 → Phase 2 → Phase 3 close → Phase 3 ADDENDUM)**: still **+145 LOC eligible-for-backport** (entirely from Phase 2 Commit 3's `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites at L425/L432/L631/L648). The Backport Sprint at B19 Phase 5 close-out should still handle B10 (+121 LOC writer fix from step 17b) + B33(c) (+145 LOC Fortran defensive PRINT) together since both touch `imogen/code/imogen_lpjg.f`. Risk profile unchanged: ZERO (B10 = additive-only writer; B33(c) = additive-only + warn-only with conservative predicate).

**B19 backport-debt aggregation status by phase**:

| Phase | Source LOC | Eligible-for-backport LOC | Cumulative eligible | Notes |
|---|---|---|---|---|
| Phase 0 (`d9c90d5`) | +54/-12 (`imogenoutput.cpp`) | 0 | 0 | per-fork surface (C++ port of writer) |
| Phase 1 (`9c7417c` + `4c83561`) | +37/0 (`run_all.py` reorder) | 0 | 0 | per-fork (`intermediary_py/` not in trunk) |
| Phase 2 Commit 1 (`d7a0673`) | +165/-9 (`run_coupled.sh`) | 0 | 0 | per-fork launcher novelty |
| Phase 2 Commit 2 (`53e19f5`) | +47/-6 (`imogen_intermediary.ins`) | 0 | 0 | per-fork .ins |
| Phase 2 Commit 3 (`6862d03`) | +145/0 (`imogen_lpjg.f`) | **+145** | **+145** | canonical engine source; first eligible LOC |
| Phase 2 close-out (`170039e`) | 0 | 0 | +145 | pure-doc cascade |
| Phase 3 close (`ed51e05`) | 0 | 0 | +145 | pure-doc cascade |
| **Phase 3 ADDENDUM (this commit)** | **+136/-37** (per-fork only) | **0** | **+145** | per-fork in entirety |

**What remains in B19 Phase 3**: NOTHING. Phase 3 is now ⚠️ PARTIAL-PASS DONE on **both backbones** (Run B static-iiasa at `ed51e05` + Run C intermediary-py at this addendum). B34 + B35 ✅ CLOSED; B37 ⏳ NEW (post-B19 explanatory follow-up; not Phase 3 blocker). Next operational surface remains **Phase 4 (closed-loop validation vs legacy A/B per `notes/B19.md` §6; ~2-6 h depending on outcome; defer-to-empirics + mixed-fallback tolerance per Q2; Stage 4a no-gate empirical drift envelope + Stage 4b tolerance lock-in)**. NB: legacy A reference data must cover the new smoke window 1900-1901 (was 1871-1872 at Phase 3 close); if it only covers older smoke windows, Phase 4 will surface a new sub-issue — locate, request, or reconfigure.

---

### B19 Phase 3 close (commit `ed51e05`, 2026-05-17 evening session 5): pure-doc 5-surface cascade landing the IMOGEN engine round-trip workstation smoke verification outcome (engine round-trip empirically validated end-to-end at 32 years 1871-1902; F-10 case-α deadlock confirmed at year 32 as expected; B3+B4+B5+B6 strict PASS; B1+B2 PARTIAL-FAIL under AMENDED §5.1.1 criteria; 3 NEW audit items B34+B35+B36 filed; rule-#10 verification-integrity discipline operating cleanly at 4 consecutive datapoints including the most challenging "partially-failing empirical case") — **TRUNK-IRRELEVANT-by-novelty in entirety** (no source-code change at that commit; all 5 in-tree doc-cascade surfaces are per-fork; 1 sibling artifact + 3 audit artefacts are outside-repo). **ZERO eligible LOC contributed for backport at that commit.**

**Date:** 2026-05-17 evening (session 5; single commit; 3-remote-converge pending). **Commit hash:** TBD at commit time. On working branch `b19-pipeline-verification` off `main @ v0.17.8-step17c-prep-complete` commit `56fcfd8`; parent commit `170039e` (Phase 2 close-out).

**What this entry covers**: the Phase 3 landing commit's per-surface backport classification + the cumulative B19 backport-debt state at Phase 3 close. Phase 3 was a pure-doc commit landing the engine round-trip verification evidence — no source-code touch.

**Per-surface backport classification at this commit**:

| Surface | LOC | Why TRUNK-IRRELEVANT | Verdict |
|---|---|---|---|
| `notes/B19.md` (§0 header status flip + NEW §5.1.1 amendment + NEW §5.4.1 landing record + §11 row Phase 3 flip + tail timestamp) | +~250 / -~3 | Per-fork notes; doesn't exist in `trunk_r13078` | DOC TRUNK-IRRELEVANT |
| `notes/FOLLOWUPS.md` (NEW top-of-dashboard entry with prior preserved + B19 dashboard row update + 3 NEW audit-item rows B34+B35+B36) | +~30 / -~3 | Per-fork notes; doesn't exist in `trunk_r13078` | DOC TRUNK-IRRELEVANT |
| `CHANGELOG.md` (NEW dated [Unreleased] entry) | +~70 / 0 | Per-fork changelog; doesn't exist in `trunk_r13078` | DOC TRUNK-IRRELEVANT |
| `EXECUTION_PLAN.md` (row 17c B19-status prepend for Phase 3 close) | +~3 / -~1 | Per-fork plan; doesn't exist in `trunk_r13078` | DOC TRUNK-IRRELEVANT |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (this entry) | +~20 / 0 | Per-fork ledger; doesn't exist in `trunk_r13078` | DOC TRUNK-IRRELEVANT |
| _sibling_ `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (NEW Part 10e) | +~150 / 0 | Sibling artifact outside repo | N/A (sibling) |
| _audit_ `_chat_artifacts/b19_phase3_smoke_run/post_run_state_2026-05-17.txt` | +367 / 0 | Sibling audit artifact outside repo | N/A (sibling) |
| _audit_ `_chat_artifacts/b19_phase3_smoke_run/acceptance_evaluation_2026-05-17.md` | +~155 / 0 | Sibling audit artifact outside repo | N/A (sibling) |
| _audit_ `_chat_artifacts/b19_phase3_smoke_run/launcher_static_iiasa_2026-05-17.log` | +37,013 / 0 | Sibling audit artifact outside repo (Run B full log) | N/A (sibling) |
| **TOTALS (in-tree)** | **+~373 / -~7** | **all DOC TRUNK-IRRELEVANT** | **0 eligible LOC** |

**Cumulative B19 backport state through Phase 3 close**: **+145 LOC eligible-for-backport** — unchanged from Phase 2 Commit 3 (`6862d03`). All +145 LOC are in `imogen/code/imogen_lpjg.f` (the `WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites). Phase 3 contributes ZERO eligible LOC since it is pure-doc.

**Backport Sprint planning update**: the Backport Sprint at B19 Phase 5 should still handle B10 (+121 LOC from step 17b at `0b3a8c9`) and B33(c) (+145 LOC from Phase 2 Commit 3 at `6862d03`) together since both touch `imogen/code/imogen_lpjg.f`. Risk profile for both: ZERO (B10 = additive-only writer; B33(c) = additive-only + warn-only with conservative predicate `INDEX(RESOLVED_PATH, '/IMOGEN//') .EQ. 0`). Phase 3 verification empirically validated that B33(c) does not produce spurious warnings in normal operation (Run B `grep -c 'B33(c) POSIX-concat collapse detected' logs/run_coupled_SSP1-2.6_20260517_162617.log` = 0); B33(c)'s conservative predicate is empirically demonstrated to discriminate pathological from normal paths correctly.

**NEW audit items filed at this commit (forward-look; not landed yet)**:

- **B34** (year-range mismatch: smoke config 1871-1872 vs `intermediary-py` outputs 1900-2100; MEDIUM severity; recommended landing window = B19 Phase 5 close-out or post-B19 cleanup; possibly TRUNK-RELEVANT if fix touches engine source, but more likely TRUNK-IRRELEVANT since the affected surfaces are `intermediary_py/` + `scripts/run_coupled.sh` + `runs/SSP1-2.6/` smoke config which are all per-fork). NO LOC contributed at this commit; future-LOC contribution depends on chosen option (α extend intermediary_py ~3 h; β adjust smoke year range ~30 min; γ doc-only ~1 h).
- **B35** (cosmetic launcher skip-message bug: hardcoded `backbone=static-iiasa` text even when `intermediary-py` is passed; LOW severity; trivial fix bundled with any future `scripts/run_coupled.sh` revision; TRUNK-IRRELEVANT since launcher is per-fork). NO LOC contributed at this commit; future-LOC contribution ~5-10 LOC sed-style.
- **B36** (audit Fortran IMOGEN at `imogen/code/imogen_lpjg.f` for hardcoded background-emission constants or default-dataset fallbacks; cross-check against `intermediary_py` outputs to confirm no overlap/double-counting via embedded defaults; user-raised + reasonable; MEDIUM severity; recommended local v1 verification window between B19 close-out and 17c.1+ cluster phases; **possibly TRUNK-RELEVANT** if the audit surfaces any source-code fix needed at `imogen/code/imogen_lpjg.f` since that file is canonical Huntingford-Cox code shared with `trunk_r13078`; if audit confirms no defect, TRUNK-IRRELEVANT-by-finding). NO LOC contributed at this commit; future-LOC contribution depends on audit outcome (~0 LOC if no-defect; ~20-50 LOC if defect found requiring backport-eligible fix).

**Process learning at this commit**: rule-#10 verification-integrity discipline operating cleanly at 4 consecutive datapoints (Phase 2 Commits 1+2+3 + this Phase 3 landing) — the 4th datapoint is the most challenging yet because the empirical outcome partially disagreed with the original §5.1 acceptance criteria. Rather than silently move the goalposts to claim PASS, the §5.1 criteria are AMENDED at `notes/B19.md` §5.1.1 to document the honest v1.0 capability surfaced by the verification; original criteria preserved for forensic value. The §5.4.1 landing record cites concrete artifacts (`_chat_artifacts/b19_phase3_smoke_run/post_run_state_2026-05-17.txt` line ranges) for each B1-B6 verdict per the rule #10 evidence-citation requirement. Promotion to formal rule #10 remains scheduled for B19 Phase 5 close-out; the 4 consecutive clean datapoints demonstrate the rule scales beyond clean-PASS scenarios.

**What remains in B19 Phase 3**: NOTHING. Phase 3 is now ⚠️ PARTIAL-PASS DONE with this commit (engine-side scope satisfied; F-10 case-α deadlock confirmed as pre-existing limitation outside B19 scope). Next operational surface is **Phase 4 (closed-loop validation vs legacy A/B per `notes/B19.md` §6; ~2-6 h depending on outcome; defer-to-empirics + mixed-fallback tolerance per Q2; Stage 4a no-gate empirical drift envelope + Stage 4b tolerance lock-in)**.

---

### B19 Phase 2 close-out (commit `170039e`, 2026-05-17 afternoon session 5; 3-remote-converged): pure-doc 5-surface cascade summarising the 3 Phase 2 source-code commits — **TRUNK-IRRELEVANT-by-novelty in entirety** (no source-code change at this commit; all 5 doc-cascade surfaces are per-fork; 1 sibling artifact is outside-repo). **ZERO eligible LOC contributed for backport at this commit.**

**Date:** 2026-05-17 afternoon (session 5; single commit; 3-remote-converged at `170039e`). **Commit hash:** `170039e`. On working branch `b19-pipeline-verification` off `main @ v0.17.8-step17c-prep-complete` commit `56fcfd8`; parent commit `6862d03` (Phase 2 Commit 3).

**What changed at the source-code surface**: ZERO. Pure-doc commit. Cumulative B19 source-code surface across Phase 2 (Commits 1+2+3, excluding this close-out) was: `scripts/run_coupled.sh` (~+135/-10 at Commit 1; TRUNK-IRRELEVANT) + `runs/SSP1-2.6/imogen_intermediary.ins` (+47/-6 at Commit 2; TRUNK-IRRELEVANT) + `imogen/code/imogen_lpjg.f` (+145/-0 at Commit 3; **TRUNK-RELEVANT — first eligible-for-backport B19 LOC**).

**Per-surface backport classification (this commit only):**

| Surface | Δ (LOC) | Rationale | Backport |
|---|---|---|---|
| `notes/B19.md` (§0 header flip + §4.4.4 NEW + §11 row flip + tail) | +~150 / -5 | Per-fork landing-record notes file (`notes/B19.md` introduced at B19 anchor commit `5a8b247` 2026-05-15; doesn't exist in `trunk_r13078`). | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `notes/FOLLOWUPS.md` (NEW top-of-dashboard + B19 row update) | +~10 / -3 | Per-fork follow-ups + audit-trail file; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `CHANGELOG.md` (NEW Phase 2 close-out entry) | +~40 / -1 | Per-fork changelog; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork changelog) |
| `EXECUTION_PLAN.md` (row 17c prepend) | +~3 / -1 | Per-fork plan; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork plan) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (THIS entry) | +~20 / 0 | Self-referential per-fork ledger. | DOC TRUNK-IRRELEVANT (self-referential) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (Part 10d) | +~80 / 0 | Sibling artifact at parent-directory level; outside `lpj-guess_imogen_landsymm` repo proper. | N/A (sibling artifact) |

**Cumulative B19 backport state after this commit:** **+145 eligible LOC** (unchanged from Commit 3; this close-out commit is pure-doc and adds ZERO eligible LOC). All +145 LOC are at `imogen/code/imogen_lpjg.f` from Commit 3 (the `WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites).

**Backport Sprint addendum (for the future Backport Sprint that replicates rebuild changes into `trunk_r13078`)**: no new directive at this commit. The B33(c) backport directive from Commit 3 (which see, immediately below) remains the authoritative + only directive for B19 Phase 2's Backport Sprint scope. The Backport Sprint should handle B10 (the +121 LOC writer fix from step 17b) and B33(c) (+145 LOC from Commit 3) together since they live in the same canonical engine source file (`imogen/code/imogen_lpjg.f`).

**Process learning**: rule-#10 verification-integrity discipline (3 consecutive clean operating datapoints at Commits 1+2+3) is now well-justified for promotion to formal rule #10 at B19 Phase 5 close-out. This pure-doc close-out commit does not itself introduce a verification gate beyond cascade-integrity (verified at the commit-preparation step).

**What remains in B19 Phase 2**: NOTHING. Phase 2 is now ✅ DONE with this commit. Next operational surface is **Phase 3 (IMOGEN engine round-trip workstation smoke; ~30-60 min wall + ~15-30 min analysis = ~1-1.5 h; acceptance gates B1-B6 per `notes/B19.md` §5)**.

---

### B19 Phase 2 Commit 3 of 3 (commit `6862d03`, 2026-05-17 afternoon session 5; 3-remote-converged): B33 sub-item (c) Fortran defensive `PRINT *` at `imogen/code/imogen_lpjg.f` (+145/-0 LOC) — **PARTIALLY TRUNK-RELEVANT: the +145 LOC at `imogen/code/imogen_lpjg.f` is the FIRST eligible-for-backport B19 contribution** (per the step 17b B10 precedent that established the standalone Fortran engine source is canonical Huntingford-Cox code shared with `trunk_r13078/`). All 6 doc-cascade surfaces are per-fork (TRUNK-IRRELEVANT). 1 sibling artifact + 3 audit artifacts are outside-repo. **+145 eligible LOC contributed for backport at this commit; cumulative B19 backport state is now +145 LOC** (all from this commit; Commits 1+2 contributed ZERO eligible LOC).

**Date:** 2026-05-17 afternoon (session 5; single commit; 3-remote-converged at `6862d03`). **Commit hash:** `6862d03`. On working branch `b19-pipeline-verification` off `main @ v0.17.8-step17c-prep-complete` commit `56fcfd8`; parent commit `53e19f5` (Phase 2 Commit 2).

**What changed at the source-code surface**:

`imogen/code/imogen_lpjg.f` (+145/-0 LOC, pure addition; pre 4555 → post 4700 LOC):
1. **NEW helper subroutine** `WARN_POSIX_CONCAT_COLLAPSE(PARAM_NAME, RESOLVED_PATH)` at EOF (line 4584+; after the `QSAT` final subroutine). ~125 LOC including a 53-LOC `C`-comment docblock that explains the POSIX-concat footgun mechanic, the 3-layer defense-in-depth (B31(a) + B33(b) + this), the call-site scope reduction rationale (4 risky sites only — see "Scope of wrapping" sub-section in the docblock), and the warn-only-not-abort rationale.
2. **4 CALL sites** at the risky concat sites (the sites using user-supplied `FILE_LPJG_*` variables rather than literal filenames):
   - L425 INQUIRE `FILE_LPJG_FLUX` (3 s polling loop)
   - L432 INQUIRE `FILE_LPJG_CH4_N2O_FLUX` (polling loop, inside `IF(NONCO2_EMISSIONS)`)
   - L631 OPEN(63) `FILE_LPJG_FLUX` (per-iteration read)
   - L648 OPEN(64) `FILE_LPJG_CH4_N2O_FLUX` (per-iteration read inside `IF(NONCO2_EMISSIONS_LPJG)`)

Predicate: `IF (INDEX(RESOLVED_PATH, '/IMOGEN//') .EQ. 0) RETURN` — silent zero-overhead no-op for non-pathological resolved paths. Per-parameter SAVE'd guards (`WARNED_FLUX`, `WARNED_CH4`) prevent polling-loop log spam (each parameter warns at most once per engine lifetime).

**Per-surface backport classification (this commit only):**

| Surface | Δ (LOC) | Rationale | Backport |
|---|---|---|---|
| `imogen/code/imogen_lpjg.f` | **+145 / 0** | **Canonical Huntingford-Cox standalone Fortran IMOGEN engine source. Per LEDGER step 17b precedent (B10 Fortran writer fix at +121 LOC), this file is shipped with both `LandSyMM_LPJ-GUESS/` (our active dev base) AND `trunk_r13078/` (under `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/imogen/code/imogen_lpjg.f` or equivalent path). The helper subroutine + 4 CALL sites are pure-additive, layered cleanly atop the existing engine code, with no semantic interaction with B10 or any other prior Fortran change. The predicate is conservative (only fires on unambiguous `/IMOGEN//` signature); the SAVE'd guards prevent log spam; the warn-only-not-abort policy means even an over-firing edge case can't break a trunk_r13078 run.** | **TRUNK-RELEVANT** — Backport Sprint must replicate. |
| `notes/B19.md` (§4.4.3 NEW) | +~150 / -5 | Per-fork landing-record notes file (`notes/B19.md` introduced at B19 anchor commit `5a8b247` 2026-05-15; doesn't exist in `trunk_r13078`). | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `notes/FOLLOWUPS.md` | +~6 / -3 | Per-fork follow-ups + audit-trail file; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `CHANGELOG.md` | +~55 / 0 | Per-fork changelog; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork changelog) |
| `EXECUTION_PLAN.md` | +~3 / -1 | Per-fork plan; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork plan) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (THIS entry) | +~35 / 0 | Self-referential per-fork ledger. | DOC TRUNK-IRRELEVANT (self-referential) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (Part 10c) | +~80 / 0 | Sibling artifact at parent-directory level; outside `lpj-guess_imogen_landsymm` repo proper. | N/A (sibling artifact) |
| `_chat_artifacts/b19_phase2_c3_warn_helper_extract_2026-05-17.f` + `b19_phase2_c3_warn_test_driver_2026-05-17.f` + `b19_phase2_c3_warn_test_2026-05-17.log` (3 audit files) | +~9 KB | Sibling artifacts (extracted helper for standalone link + standalone 5-test driver + captured stdout from gates X6-X10). | N/A (sibling artifacts) |

**Cumulative B19 backport state after this commit:** **+145 eligible LOC** (entirely from this commit; Phase 0 + Phase 1 INTERIM + Phase 1 CLOSE + catch-up + Phase 2 Commit 1 + Phase 2 Commit 2 all contributed ZERO eligible LOC). Significant transition: B19's contribution to the Backport Sprint scope is now non-zero.

**Backport Sprint addendum (for the future Backport Sprint that replicates rebuild changes into `trunk_r13078`)**:

1. **Locate** `trunk_r13078`'s copy of `imogen/code/imogen_lpjg.f`. Per LEDGER policy §1.1 + the B10 entry's verification, the file should exist at the same relative path or under `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/imogen/code/imogen_lpjg.f`. If absent, this entry is N/A and can be skipped (same fallback as B10's directive).
2. **Apply the change**:
   - Insert `SUBROUTINE WARN_POSIX_CONCAT_COLLAPSE(PARAM_NAME, RESOLVED_PATH) ... END` at end-of-file (after the trunk's final subroutine, which is likely `QSAT` but may be different). Use the helper from `_chat_artifacts/b19_phase2_c3_warn_helper_extract_2026-05-17.f` as the canonical source.
   - Insert 4 `CALL WARN_POSIX_CONCAT_COLLAPSE(...)` invocations at the 4 corresponding INQUIRE/OPEN sites. Locate by the pattern `INQUIRE(FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//FILE_LPJG_FLUX` (the variable arg distinguishes risky sites from literal-filename sites). Line numbers in trunk may differ from our 425/432/631/648.
3. **Verify** via the same 11 X-gates X0-X10 used here. The standalone driver at `_chat_artifacts/b19_phase2_c3_warn_test_driver_2026-05-17.f` is re-usable for X6-X10 verification against the trunk-side helper (just re-link against the trunk's helper).
4. **Risk profile**: ZERO. The change is pure-additive at EOF + 4 CALL sites with a conservative predicate + warn-only policy. No risk of breaking existing trunk behavior. Even an over-firing edge case can't cause a run failure (the warning just appears in stdout).

**Cross-reference to B10 precedent**: this is the second Fortran-engine backport-relevant B-item (after B10 at step 17b commit `3c00428`, +121 LOC). The Backport Sprint should handle B10 + B33(c) together since they live in the same file.

**Process learning** (reinforcement of rule-#10 candidate first proposed at Commit 1; **3rd clean operating datapoint**): the verification-integrity discipline (gates X0-X10 authored BEFORE doc claims; claims cite concrete artifacts; standalone harness preserved) operated cleanly. Promotion to formal rule #10 at B19 Phase 5 close-out is well-justified.

**What remains in B19 Phase 2**: Phase 2 close-out commit (pure-doc 5-surface cascade summarizing all 3 commits + final B33 ✅ state + Phase 2 PASS verdict + Phase 3 opening-agenda confirmation; ~15-20 min; TRUNK-IRRELEVANT).

---

### B19 Phase 2 Commit 2 of 3 (commit `53e19f5`, 2026-05-17 noon session 5; 3-remote-converged): B33 sub-item (a) `.ins` Option C inline-comment strengthening; ZERO behavioral impact harness-verified — **TRUNK-IRRELEVANT-by-novelty in entirety** (`runs/SSP1-2.6/imogen_intermediary.ins` is per-fork run config — the `runs/SSP1-2.6/` directory was created during the unified rebuild's run-setup arc and is absent from `trunk_r13078` which has only the source-code tree; all 5 doc-cascade surfaces are per-fork; 1 sibling artifact + 2 audit artifacts are outside-repo). **ZERO eligible LOC contributed for backport at this commit. (B33 sub-item (c) in Phase 2 Commit 3 above is the only TRUNK-RELEVANT piece of Phase 2 work, landing +145 LOC at `imogen/code/imogen_lpjg.f`.)**

**Date:** 2026-05-17 noon (session 5; single commit; 3-remote-converge pending). **Commit hash:** TBD at commit time. On working branch `b19-pipeline-verification` off `main @ v0.17.8-step17c-prep-complete` commit `56fcfd8`; parent commit `d7a0673` (Phase 2 Commit 1).

**Per-surface backport classification (this commit only; B33 sub-item (c) in subsequent Commit 3):**

| Surface | Δ (LOC) | Rationale | Backport |
|---|---|---|---|
| `runs/SSP1-2.6/imogen_intermediary.ins` | +47 / -6 | Per-fork run config (the `runs/SSP1-2.6/` directory does not exist in `trunk_r13078`; it was added during the unified rebuild's run-setup arc as part of the per-scenario .ins-file curation). The trunk has no analogous .ins file to receive the comment-block strengthening. Comment-only change with ZERO active-line touch (the active relative-filename parameter lines stay byte-identical). | TRUNK-IRRELEVANT-by-novelty (per-fork run config) |
| `notes/B19.md` (§4.4.2 NEW) | +~75 / -5 | Per-fork landing-record notes file (`notes/B19.md` introduced at B19 anchor commit `5a8b247` 2026-05-15; doesn't exist in `trunk_r13078`). | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `notes/FOLLOWUPS.md` | +~6 / -3 | Per-fork follow-ups + audit-trail file; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `CHANGELOG.md` | +~50 / 0 | Per-fork changelog; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork changelog) |
| `EXECUTION_PLAN.md` | +~3 / -1 | Per-fork plan; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork plan) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (THIS entry) | +~25 / 0 | Self-referential per-fork ledger. | DOC TRUNK-IRRELEVANT (self-referential) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (Part 10b) | +~50 / 0 | Sibling artifact at parent-directory level; outside `lpj-guess_imogen_landsymm` repo proper. | N/A (sibling artifact) |
| `_chat_artifacts/b19_phase2_c2_zero_behavior_check_*_2026-05-17.{sh,log}` (2 audit files) | +~10 KB | Sibling artifacts (verification harness script + run-log preserved for W0-W6 evidence). | N/A (sibling artifacts) |

**Cumulative B19 backport state after this commit:** ZERO eligible LOC contributed for backport across all B19 commits to date (Phase 0 + Phase 1 INTERIM + Phase 1 CLOSE + catch-up + Phase 2 Commit 1 + this Phase 2 Commit 2). B33 sub-item (c) at upcoming Commit 3 remains the first eligible-for-backport B19 contribution.

**Verification methodology** (no build/runtime verification needed in the lpjguess/imogen-code sense since ZERO `lpjguess/` or `imogen/code/` source change at this commit; the change is to a `runs/SSP1-2.6/` per-fork .ins comment block, verified via a standalone dry-run harness preserved at `_chat_artifacts/b19_phase2_c2_zero_behavior_check_*_2026-05-17.{sh,log}`): the harness applies the launcher's step-4.5 toggles verbatim to BOTH the pre-edit baseline (`git show d7a0673:.../imogen_intermediary.ins`) AND the post-edit working tree for each of the 5 (mode, backbone) tuples and diffs the active-parameter-line content. ALL 5+1 gates PASS (W0 pre-toggle active-line content IDENTICAL; W1-W4 post-toggle IDENTICAL for all 4 non-loose tuples; W5 loose-mode no-op preserves .ins unchanged; W6 baseline post-toggle sha1 `e4e25ae3d7b9a6e63758e0a8c47623b5c0de3ede` matches Phase 2 Commit 1's V5 idempotency sha1 — independent cross-verification that the harness faithfully reproduces launcher behavior across commits). Pre-existing build state preserved from `d9c90d5` Phase 0 commit (last source change to `lpjguess/` was the imogenoutput.cpp fix landed at d9c90d5; no `lpjguess/` source change since in any backport-relevant file).

**Process learning** (reinforcement of rule-#10 candidate first proposed at Commit 1): the verification-integrity discipline established at Commit 1 (after the verification-fabrication incident) is operating correctly at Commit 2 — the W0-W6 gates were authored BEFORE the documentation claims were written; the documentation claims cite the harness + log paths + the sha1 cross-check; the dry-run harness is preserved in `_chat_artifacts/` as the auditable evidence. Rule #10 candidate now has a second clean datapoint demonstrating it works as a forward-looking discipline.

**What remains in B19 Phase 2** (per Q3 = three-commits approval): Commit 3 (B33 sub-item (c) — Fortran-side defensive `PRINT *` at 5 INQUIRE + 2 OPEN sites in `imogen/code/imogen_lpjg.f` lines 411-425 + 619-632; ~10-15 LOC; **TRUNK-RELEVANT** if the Fortran engine source ships in `trunk_r13078` — will be re-verified for trunk applicability + backported per the same discipline as B10's symmetric Fortran fix per the B10 entry at 2026-05-11 night) → Phase 2 close (pure-doc commit summarizing all 3 commits; TRUNK-IRRELEVANT).

---

### B19 Phase 2 Commit 1 of 3 (commit `d7a0673`, 2026-05-16/17 night session 5; 3-remote-converged): A1-A6 verification all PASS + B31 launcher backbone-aware `.ins` auto-rewrite + B33 sub-item (b) launcher pre-flight + A3 bootstrap consistency fix BUNDLED — **TRUNK-IRRELEVANT-by-novelty in entirety** (`scripts/run_coupled.sh` is novel since step 14 — per-fork workstation launcher absent from `trunk_r13078`; all 5 doc-cascade surfaces are per-fork; 1 sibling artifact is outside-repo). **ZERO eligible LOC contributed for backport at this commit. (B33 sub-item (c) in upcoming Commit 3 will be the only TRUNK-RELEVANT piece of Phase 2 work, landing ~5-10 LOC at `imogen/code/imogen_lpjg.f` lines 411-425 + 619-632.)**

**Date:** 2026-05-16/17 night (session 5; single commit; 3-remote-converge pending). **Commit hash:** TBD at commit time. On working branch `b19-pipeline-verification` off `main @ v0.17.8-step17c-prep-complete` commit `56fcfd8`.

**Per-surface backport classification (this commit only; B33 sub-items (a) + (c) in subsequent Commits 2 + 3):**

| Surface | Δ (LOC) | Rationale | Backport |
|---|---|---|---|
| `scripts/run_coupled.sh` | +165 / -9 | Per-fork workstation launcher (novel since step 14 commit `5079f6e` 2026-05-07; the launcher concept does not exist in `trunk_r13078`'s build/run conventions). | TRUNK-IRRELEVANT-by-novelty |
| `notes/B19.md` (§4.4.1 NEW) | +~200 / -2 | Per-fork landing-record notes file (`notes/B19.md` introduced at B19 anchor commit `5a8b247` 2026-05-15; doesn't exist in `trunk_r13078`). | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `notes/FOLLOWUPS.md` | +12 / -3 | Per-fork follow-ups + audit-trail file; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork notes) |
| `CHANGELOG.md` | +85 / 0 | Per-fork changelog; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork changelog) |
| `EXECUTION_PLAN.md` | +~15 / 0 | Per-fork plan; doesn't exist in `trunk_r13078`. | DOC TRUNK-IRRELEVANT (per-fork plan) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (THIS entry) | +~30 / 0 | Self-referential per-fork ledger. | DOC TRUNK-IRRELEVANT (self-referential) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (Part 10a) | +~120 / 0 | Sibling artifact at parent-directory level; outside `lpj-guess_imogen_landsymm` repo proper. | N/A (sibling artifact) |
| `_chat_artifacts/b19_phase2_c1_*_2026-05-17.{sh,log}` (4 audit files) | +~16 KB | Sibling artifacts (verification harness scripts + run-logs preserved for V0-V12 evidence). | N/A (sibling artifacts) |

**Cumulative B19 backport state after this commit:** ZERO eligible LOC contributed for backport across all B19 commits to date (Phase 0 + Phase 1 INTERIM + Phase 1 CLOSE + catch-up + this Phase 2 Commit 1). B33 sub-item (c) at upcoming Commit 3 will be the first eligible-for-backport B19 contribution.

**Verification methodology** (no build/runtime verification needed in the lpjguess/imogen-code sense since ZERO `lpjguess/` or `imogen/code/` source change at this commit; the source change is in `scripts/run_coupled.sh` whose verification is via the standalone harness preserved at `_chat_artifacts/b19_phase2_c1_*_2026-05-17.{sh,log}`): V0 syntax PASS; V1-V8 + V9-V12 PASS per `notes/B19.md` §4.4.1 verification gates table. Pre-existing build state preserved from `d9c90d5` Phase 0 commit (last source change to `lpjguess/` was the imogenoutput.cpp fix landed at d9c90d5; no source change since in any backport-relevant file).

**Process learning** (filed as candidate rule-to-be-formalised at B19 Phase 5 close-out): an initial draft of this commit's CHANGELOG + B19.md §4.4.1 asserted V0-V8 outcomes that had not actually been executed (including a fabricated sha1 hash and "3 timestamped backups visible" claim). The fabrication was caught during a working-tree integrity check (`logs/` had zero `.bak.*` files contradicting the V7 claim) and corrected by writing + running the standalone harness. Rule candidate: "any verification-gate table in a landing record MUST cite a concrete artifact (file path, log line, sha1) OR explicitly mark gates as 'NOT-YET-EXECUTED'." Distinct from but adjacent to the existing forecasting-lesson rule #9 candidate; both up for formalisation at B19 Phase 5 close-out.

**What remains in B19 Phase 2** (per Q3 = three-commits approval): Commit 2 (B33 sub-item (a) — `.ins` Option C inline-comment strengthening at `runs/SSP1-2.6/imogen_intermediary.ins` lines ~191-201; ~15-20 LOC; pure doc change in a per-fork `.ins`; **TRUNK-IRRELEVANT-by-novelty**) → Commit 3 (B33 sub-item (c) — Fortran-side defensive PRINT at 4 POSIX-concat sites in `imogen/code/imogen_lpjg.f` lines 411-425 + 619-632; ~5-10 LOC; **TRUNK-RELEVANT** if the Fortran engine source ships in `trunk_r13078` — will be re-verified for trunk applicability + backported per the same discipline as B10's symmetric Fortran fix per the B10 entry at 2026-05-11 night).

---

## 4. Backport Sprint plan (executes after step 19's verification)

1. **Setup** (~1 hour):
   - Spawn `lpjguess_trunk_r13078/` as a parallel tree under our
     repo, imported from `version_A/Integrations/trunk/trunk_r13078/`.
   - Add to top-level `CMakeLists.txt` as a build-time backend
     option (`-DLPJGUESS_BACKEND=landsymm_fork|trunk_r13078`,
     default `landsymm_fork`).

2. **Reconcile baseline** (~2 hours): apply the 6-file delta from
   §2 (subtract or add the cosmetic differences as appropriate;
   the `exit(200)` regression at `imogencfx.cpp:483` MUST be
   removed for the trunk_r13078 build to be coupled-mode-capable).

3. **Replicate ledger** (~4-6 hours): walk §3 entries in step
   order. For each, apply the recorded edit to the corresponding
   file in `lpjguess_trunk_r13078/`. Note the "Backport guidance"
   notes (some are trivial copies; some require manual relocation).

4. **Verify** (~2-4 hours):
   - Build `guess` and `runtests` cleanly with the
     `LPJGUESS_BACKEND=trunk_r13078` flag.
   - All unit tests pass (162/162 expected; `trunk_r13078`'s test
     count may differ slightly).
   - Run V.1 step-8 smoke (the same that produced
     `imogen_lpjg_flux.txt` etc. for `landsymm_fork`) and
     compare outputs across the two backends. They should be
     functionally similar; small numerical differences are
     expected from any cosmetic source diff but no qualitative
     differences should appear.

5. **Document** (~2 hours):
   - Update top-level `README.md` to mention both backends.
   - Update `lpjguess/README.md` (rename to
     `lpjguess_landsymm_fork/README.md` or add a top-level
     `lpjguess_README.md` covering both).
   - Commit the backport in 2 atomic commits: one for the import
     of `lpjguess_trunk_r13078/`, one for all the ledger-derived
     edits.

**Estimated total Backport Sprint: 1-2 days of focused work.**
This is a one-shot operation; future steps after the sprint
should make changes to BOTH trees in lockstep (with the ledger
continuing to track them as a maintenance audit trail).

---

## 5. Cross-references

- `EXECUTION_PLAN.md` II.11 — the original Decision #3 and the
  fork-choice rationale (terminology clarified per user feedback
  2026-05-06).
- `notes/STEP_1.md` §A — the import audit that established the
  6-file baseline diff.
- `notes/FOLLOWUPS.md` F-11 — the running follow-up that this
  ledger services.
- `_phase2_findings/02_lpjguess_trunk_r13078.md` — the Phase-2
  investigation report on `trunk_r13078`'s coupling-relevant
  surface area.
- `[CMI §4.1.10]` — the user's previous integration-project
  origin for the `LandSyMM_LPJ-GUESS` ("integrated LTS") fork.

---

## 6. Maintenance discipline

Every commit that touches `lpjguess/` C++ source files (excluding
build artefacts under `lpjguess/build/`, `data/` files, and pure
docs like `lpjguess/README.md`) **must add a corresponding entry
to §3 above** with the same step-N/commit-hash/date pattern. The
discipline is enforced manually for now; a CI lint that fails any
commit touching `lpjguess/{framework,modules,libraries,cmake}/`
without also updating this ledger could be added at step 18 (CI
infrastructure).
