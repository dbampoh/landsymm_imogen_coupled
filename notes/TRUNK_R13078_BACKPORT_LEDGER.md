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

**Commit:** `dc91efb` (Step 1)  **Date:** 2026-05-05
- **No source-level changes from the imported source** (rsync only).
- The 6-file delta from `trunk_r13078` (per §2 above) is "free"
  for the backport sprint — those differences must be reconciled
  first; only then do later steps' changes layer on.

### Step 2: Import Fortran IMOGEN; immediate Linux fixes

**Commit:** `9e51a23` (Step 2)  **Date:** 2026-05-05
- **No `lpjguess/` changes**; all changes are in `imogen/code/`
  which is fork-shared (Fortran). Backport-irrelevant for the
  C++ side; relevant for the Fortran side which trunk_r13078 also
  uses unchanged.

### Step 3: Fortran IMOGEN ALLOCATABLE refactor

**Commit:** `5f86bb1` (Step 3)  **Date:** 2026-05-05
- **No `lpjguess/` changes**; Fortran-only. Backport-irrelevant
  for the C++ side.

### Step 4: GCM patterns + CRUNCEP fetch infrastructure

**Commit:** `f3bb471` (Step 4)  **Date:** 2026-05-06
- **No `lpjguess/` changes**; tooling + Fortran data infrastructure
  only. Backport-irrelevant.

### Step 5: CMIP6 → CMIP5 ASCII converter

**Commit:** `2d36c8e` (Step 5)  **Date:** 2026-05-06
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

### Step 13: Python Intermediary -> Fortran IMOGEN ASCII adapter

**Commit:** _TBD_  **Date:** 2026-05-07

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

**Commit:** _TBD_  **Date:** 2026-05-07

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

**Commit:** _TBD_  **Date:** 2026-05-07

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

**Commit:** _TBD_  **Date:** 2026-05-07

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

**Commit:** _TBD (step 9)_  **Date:** 2026-05-07

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
