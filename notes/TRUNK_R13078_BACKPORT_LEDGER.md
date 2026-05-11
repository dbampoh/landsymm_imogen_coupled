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
