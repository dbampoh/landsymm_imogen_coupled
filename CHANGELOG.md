# Changelog

All notable changes to the LandSyMM-IMOGEN coupled model framework
are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

For each release tag listed below, see `git log <tag>` for the per-step
commit history that produced it. The investigation evidence base is
preserved in `_phase2_findings/` and is **immutable across releases**
— it documents the predecessor framework trees (`version_A` and
`version_B`) at the moment the rebuild began.

---

## [Unreleased] — Rebuild in progress

In progress per `EXECUTION_PLAN.md` Part V steps 0-19. See
README.md "Roadmap" for the milestone schedule.

---

## [v0.8.1-backport-ledger] — 2026-05-06 — terminology + backport-ledger documentation

### Documented — `LandSyMM_LPJ-GUESS/` ≡ "integrated LTS" terminology synonymy

Per user clarification 2026-05-06, the user calls our v1.0
development base — `LandSyMM_LPJ-GUESS/` — the **"integrated LTS"**
because that's the working name from their preceding
integration-project. The directory name and the spoken term refer
to the **same artifact**. There is a separate
`lpjg_landsymm_integration/LPJ-GUESS-integrated/` directory that is
NOT what we imported and is NOT what the user calls "the integrated
LTS"; out-of-scope for v1.0.

Updated:
- `EXECUTION_PLAN.md` II.11.0 — new "Terminology" subsection with
  the synonymy explicitly documented.
- `EXECUTION_PLAN.md` II.11.1 — table headers updated to match.
- `EXECUTION_PLAN.md` II.11.2 — "Why ... for v1.0" reframed
  ("integrated LTS" instead of "trunk_r13078" with rationale
  preserved).
- `EXECUTION_PLAN.md` II.11.3 — Phase-2 backend section reframed
  as the **Backport Sprint** with explicit reference to
  `notes/TRUNK_R13078_BACKPORT_LEDGER.md`.
- `EXECUTION_PLAN.md` II.11.4 — knowledge-gap #2 updated to
  reflect that v1.0 IS testing the integration-LTS coupling
  integration in real-time.
- `README.md` (top-level) — repository-structure section + Lineage
  section updated.
- `lpjguess/README.md` — Provenance section adds the terminology
  note + Maintenance Discipline subsection.

### Added — `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (~370 lines)

New running source-of-truth catalogue of every C++ source-level
change in `lpjguess/` that needs replication in `trunk_r13078` at
the end of Phase-1 (the **Backport Sprint**, follow-up F-11). The
ledger:

- §1 documents the policy (which fork is which, the workflow, what
  the ledger covers and doesn't).
- §2 lists the **6-file baseline diff** between the two forks
  (cosmetic + the critical `exit(200)` removal at
  `imogencfx.cpp:483`).
- §3 retroactively populates the change set for steps 1-8 with
  step / commit-hash / file / line range / description / backport-
  guidance fields per entry. Step 7's C2/C3/C4 fixes and step 8's
  imogenoutput module + coupling_mode parameter + miscoutput
  cleanup are all catalogued.
- §4 lays out the 1-2 day Backport Sprint plan (5 phases:
  setup → reconcile baseline → replicate ledger → verify →
  document).
- §6 establishes the maintenance discipline: every commit that
  touches `lpjguess/{framework,modules,libraries,cmake}/` C++
  source MUST add a matching ledger entry.

### Added — follow-up F-11 in `notes/FOLLOWUPS.md`

The Backport-Sprint task itself, with cross-references to the
ledger, EXECUTION_PLAN.md II.11, notes/STEP_1.md §A, and
`_phase2_findings/02_lpjguess_trunk_r13078.md`. Estimated 1-2 days
focused work, executed at end of Phase-1.

### Updated — `notes/README.md`

Filesystem layout updated to include `TRUNK_R13078_BACKPORT_LEDGER.md`
alongside `FOLLOWUPS.md`, with a "When to use which" subsection
explaining the distinction between the two trackers (FOLLOWUPS
tracks open tasks; the ledger tracks the change log feeding the
eventual backport sprint task).

### Files modified / added

```text
Added:
  notes/TRUNK_R13078_BACKPORT_LEDGER.md   ~370 lines (new ledger)

Modified:
  EXECUTION_PLAN.md                       II.11 reframing (~80 LOC)
  README.md                               structure + lineage sections
  lpjguess/README.md                      provenance + discipline note
  notes/FOLLOWUPS.md                      +F-11 (~45 LOC)
  notes/README.md                         layout + when-to-use subsection
  CHANGELOG.md                            this entry
```

### Why this is a documentation-only release (no code changes)

The terminology-synonymy clarification + backport ledger don't
modify any C++/Fortran source. Tagged separately from
`v0.8.0-imogenoutput` (the step-8 functional milestone) so the
documentation churn doesn't get hidden in the code milestone's
release notes.

---

## [v0.8.0-imogenoutput] — 2026-05-06 — step 8

### Added — LPJG-side handshake writer + `coupling_mode` ins parameter

Per `EXECUTION_PLAN.md` V.1 step 8 + Appendix A.1. Implements a new
LPJ-GUESS output module that writes per-year handshake control files
the IMOGEN engine consumes, completing the LPJG → IMOGEN feedback
flow that step 7's polling-loop fixes had un-blocked.

#### New module — `lpjguess/modules/imogenoutput.cpp/h` (~470 lines total)

A `GuessOutput::ImogenOutput` class derived from `OutputModule`,
registered via `REGISTER_OUTPUT_MODULE("imogenoutput", ImogenOutput)`.
Writes 4 files at `<DIR_COMMON>/LPJG_main/IMOGEN/`:

- `imogen_lpjg_flux.txt` — `(year, NEE_PgC)` timeseries (append per year)
- `imogen_lpjg_ch4_n2o_flux.txt` — `(year, CH4_TgCH4, N2O_TgN2O)` timeseries
- `imogen_lpjg.txt` — control state for IMOGEN's next year (overwritten)
- `done` — handshake marker (touched LAST, after data writes finish)

Cadence: per-gridcell accumulation in `outannual()`; year-change
detection at start of `outannual` triggers `flush_year(prev_year)`
and accumulator reset; final-year flush in destructor.

Mode-gated by `IMOGENConfig::coupling_mode`:
- `"tight"` (default) — all 4 files written; IMOGEN engine consumes them
- `"prescribed"` — all 4 files written; IMOGEN engine reads from
  static path in ins file (handshake files act as diagnostics only)
- `"loose"` — NO files written; LPJG runs against pre-baked IMOGEN
  climate library on disk

Unit conversions emit canonical IPCC units:
- NEE: kgC across all gridcells × 1e-12 → PgC/yr (positive = source)
- CH4: g(CH4-C) × (16/12) × 1e-12 → TgCH4/yr
- N2O: kgN × (44/28) × 1e-9 → TgN2O/yr

Spherical-Earth gridcell-area approximation (R=6 371 km, 0.5° resolution).

#### `coupling_mode` ins parameter

Three small additions to plumb the new parameter through:
- `lpjguess/framework/parameters.h` — `extern xtring coupling_mode;` decl
- `lpjguess/framework/parameters.cpp` — definition with `"tight"` default
- `lpjguess/modules/imogencfx.cpp` — `declare_parameter("coupling_mode", ...)` registration

#### Build-system update

`lpjguess/modules/CMakeLists.txt` extended with `imogenoutput.h` and
`imogenoutput.cpp` so both `guess` and `runtests` targets pick up the
new module.

### Removed — dead `getImogenData()` placeholder helper

In `lpjguess/modules/miscoutput.h`:
- Deleted the `getImogenData(int lower, int upper)` static helper
  (~12 lines) that returned non-deterministic random values from a
  `std::random_device`-seeded `std::uniform_real_distribution<>`. It
  was defined but never invoked anywhere in the codebase, and was
  semantically misleading (a "data getter" that returned randomness).
- Removed unused `#include <random>` (was the only consumer).

The 12 `xtring file_*_anom` and `Table out_*_anom` declarations
remain in place — they're inert at runtime and are tracked
separately as follow-up F-9 (climate-input diagnostic outputs;
distinct concern from step 8's handshake-writer scope).

### Documented — major architectural finding F-10 (extensive)

Step 8's investigation surfaced what is arguably the most important
architectural finding of the entire investigation phase: the
LPJ-GUESS framework's `framework.cpp` lines 411-516 implement a
**per-gridcell-outer / per-day-inner across all years** loop. Each
gridcell processes ALL its years before the next gridcell starts.

This is **fundamentally incompatible** with proper per-year-globally-
synchronized tight coupling. When gridcell-1 finishes year-N and the
handshake fires, gridcell-2 has not yet started year-N. Step 8's
writer therefore emits **per-gridcell-rolling** values (which meet
V.1's stated step-8 milestone — non-empty, sensible files), but the
values are NOT globally synchronized.

This finding is the formal explanation for why [CMI §1.1] notes the
predecessor framework "never ran end-to-end." The predecessor's
polling loops were "neutered" by bugs C2/C3 to mask the
synchronization gap; step 7's un-neutering and step 8's writer
expose it.

**Phase-2 recommendation** (per user guidance 2026-05-06): when we
implement proper synchronized tight coupling, do NOT alter the
existing `framework.cpp` loop. Instead, add a runtime parameter
(e.g. `framework_loop_mode = "year_outer"`) that gates a NEW
per-year-outer code path which lives ALONGSIDE the default
per-gridcell-outer path. This mirrors the LandSyMM-fork-into-LTS
integration pattern from earlier in the chat history — additive
parameter-gated code, no behavioral change to the default path.

Full extensive write-up in `notes/FOLLOWUPS.md` F-10 (~150 lines)
and cross-referenced from `notes/STEP_8.md`,
`lpjguess/modules/imogenoutput.h`, and `EXECUTION_PLAN.md`.

### Documented — F-9 (half-scaffolded miscoutput climate-input diagnostics)

Cross-reference to the surviving 12 `file_*_anom` table stubs in
miscoutput. These are the climate-input diagnostic outputs (T_anom,
P_anom, Tmin/Tmax_anom etc. — what IMOGEN supplied to LPJG) — a
distinct concern from step 8's handshake-writer scope. Best timing
to complete is step 9.5 alongside Rh_anom / W_anom output parity.

### Verification

```text
$ cd lpjguess/build && make
[ 83%] Building CXX object CMakeFiles/runtests.dir/modules/imogenoutput.cpp.o
[100%] Built target runtests

$ ./runtests
All tests passed (162 assertions in 25 test cases)
```

✅ Build clean; all 162 unit tests still pass; no regression from
the 6 source-code edits. Per-year file-write verification is gated
on step 9 (run-config setup); step 8 establishes the writer
infrastructure and registration.

### Files modified / added

```text
Added:
  lpjguess/modules/imogenoutput.h          ~150 lines
  lpjguess/modules/imogenoutput.cpp        ~310 lines
  notes/STEP_8.md                          ~440 lines

Modified:
  lpjguess/framework/parameters.h          +9 lines (coupling_mode decl)
  lpjguess/framework/parameters.cpp        +4 lines (coupling_mode defn)
  lpjguess/modules/imogencfx.cpp           +7 lines (declare_parameter)
  lpjguess/modules/CMakeLists.txt          +2 lines (header + source)
  lpjguess/modules/miscoutput.h            -16 lines / +5 lines (kill dead helper)
  notes/FOLLOWUPS.md                       +200 lines (F-9 + F-10 entries)
  CHANGELOG.md                             this entry
  EXECUTION_PLAN.md                        step 8 row marked ✅
```

---

## [v0.7.0-coupling-fixes] — 2026-05-06 — step 7

### Fixed — LPJ-GUESS coupling source-level bugs (C2, C3, C4) + closes F-4

Per `EXECUTION_PLAN.md` V.1 step 7 + `[CMI §1.2]`, applied 3 of 5
catalogued LPJG ↔ IMOGEN coupling source-level bugs. (Bug C1 was
already eliminated by step 1's import-choice; bug C5's typo fixes
live in run-config files we'll create at step 9.)

#### C2 + C3 — `lpjguess/modules/climatemodel.cpp` polling loop (lines 332-353)

Before, the polling loop had **4 lines short-circuited**:
- `// doneExist = filesystem::exists(...)` (INQUIRE-equivalent commented out)
- `doneExist = true;` (replacement that always exited the wait)
- `// runnowOpen = !file.is_open();` (×3 instances at lines 336, 343, 352)

The "doneExist=true" hard-code silently bypassed the per-year LPJG↔IMOGEN
handshake's safety semantics; the 3 `*Open` guards were wholly inactive.

After:
- Restored `doneExist = filesystem_dkb::exists(...)` (the INQUIRE-equivalent).
- Added first-call bypass: `if (firstCall && !doneExist) doneExist = true;`
  using the existing `firstCall` local (initialized from
  `IMOGENConfig::FIRSTCALL` at line 244, reset at line 993). This avoids
  an infinite poll on the very first iteration of the very first run
  while preserving the proper handshake semantics afterward.
- Uncommented the 3 `*Open` guards.

#### C4 — `lpjguess/modules/imogen_input.cpp:728` ndep initializer

Before:
```cpp
//ndep.getndep(param["file_ndep"].str, cru_lon, cru_lat, Lamarque::parse_timeseries(ndep_timeseries));
```

The `ndep` object is later used at line 855 in `getclimate()` (via
`ndep.get_one_calendar_year`); without this initializer, ndep returned
zero/garbage values throughout the run, silently breaking
N-deposition forcing in loose-coupling mode. Uncommented + documented.

#### F-4 — Fortran twin: `imogen/code/imogen_lpjg.f`

The Fortran-side equivalent of bugs C2/C3 — the polling-loop's
DONE_EXIST default at line 363 (`!DONE_EXIST=.TRUE.`) was commented
out, and the line-371 INQUIRE always overrode it. Result: every
standalone IMOGEN smoke run since step 4 required a manual
`touch LPJG_main/IMOGEN/done` before invocation, or the binary
spun forever in the polling loop.

Fix: added `mkdir -p` + `touch done` block via `CALL SYSTEM` right
before the outer `DO WHILE (KEEPRUNNING)` loop. Idempotent (no error
if dir/file already exist). The polling-loop INQUIRE then finds the
auto-created file on the very first iteration → DONE_EXIST=.TRUE. →
loop exits → year 1 processing begins. In coupled mode, LPJ-GUESS
manages the file's lifecycle yearly; this auto-create only kicks in
on the very first invocation when no prior handshake exists.

The dead `!DONE_EXIST=.TRUE.` comment at line 363 (now permanently
moot) was replaced with an explanatory comment block.

### Verification

- ✅ LPJ-GUESS rebuilds clean.
- ✅ All **162 unit tests still pass** (`./runtests` reports
  `All tests passed (162 assertions in 25 test cases)`) — no regression
  from C2/C3/C4 fixes.
- ✅ Fortran IMOGEN rebuilds clean.
- ✅ **CRITICAL**: standalone IMOGEN smoke run, **without** any manual
  `touch done` or pre-staged `done` file, produces years 1871-1872
  output cleanly. Verified by:
  ```
  rm -rf LPJG_main IMOGEN              # nuke all stale state
  mkdir -p LPJG_main/IMOGEN IMOGEN/output
  cp /path/to/version_A/.../*.txt LPJG_main/IMOGEN/   # control-file stubs only
  test ! -f LPJG_main/IMOGEN/done && echo "OK"        # confirms no done file
  timeout 60 ./imogen_lpjg
  # → "Read NGPOINTS: 3698" → "ALLOCATEd regrid arrays" →
  #   "DONE_EXIST = T" on first poll iteration → years 1871, 1872 produced
  ```
  No regression from step 4's structural output (same files, same
  format).

### What's NOT in this release

- **C5 typo fixes** (`IMOGEN/ouput/`→`IMOGEN/output/`, `R_anom.dat`→
  `Rh_anom.dat`) — those typos live in the predecessor's run-config
  `.ins` files, NOT in the imported source code. Our `runs/<SSP>/...`
  directories don't exist yet — they get created at **step 9**, where
  fresh ins files will use the correct paths from the start.
- **LPJG-side handshake writer** (`imogen_lpjg_flux.txt`,
  `imogen_lpjg_ch4_n2o_flux.txt`, year-end `done`) — that's **step 8**.
- **Per-scenario coupled-mode run-config** — **step 9**.

### Files modified

- `lpjguess/modules/climatemodel.cpp` (C2 + C3 fixes)
- `lpjguess/modules/imogen_input.cpp` (C4 fix)
- `lpjguess/modules/imogencfx.cpp` (cross-reference comment only;
  the parallel `ndep.getndep()` call here was already active —
  bug C4 was specifically scoped to `imogen_input.cpp`. Added a
  small documentation note at line 895 to prevent future
  maintenance drift between the two modules)
- `imogen/code/imogen_lpjg.f` (F-4 fix)

### Files added

- `notes/STEP_7.md` (per-step verification record)

### Files modified (docs)

- `notes/FOLLOWUPS.md` (close F-4)
- `CHANGELOG.md` (this entry)
- `EXECUTION_PLAN.md` (V.1 step 7 marked complete)

---

## [v0.6.0-data-import] — 2026-05-06 — step 6

### Added — reference data import + 2 new tarballs (closes follow-up F-5)

Per `EXECUTION_PLAN.md` V.1 step 6 + `[CMI §5]`'s data inventory,
populate `data/` with the small reference inputs the coupled model
needs at runtime, tarball the medium-large reference inputs (Ndep,
emiss-reference), and document the very-large Tier-3 datasets without
committing them.

#### Tier 1 — committed directly to git (~14 MB)

- **`data/soil/`** — `soilmap_center_interpolated.remapv10_old_62892_gL.dat`
  (3.5 MB; LPJ-GUESS soil property table).
- **`data/gridlist/`** — 7 gridlist files (3.4 MB total): the active
  62 538-cell `gridlist_in_62892_and_climate.txt` plus 6 alternates
  (test, hilda+, hurtt-style, ndep, patterns).
- **`data/concentrations/`** — 31 reference CO2/CH4/N2O timeseries
  files (7.5 MB; EPA + IIASA CMIP5/CMIP6 TXT/CSV/DAT only — raw
  XLSX/ZIP downloads excluded per V.1 spec).

#### Tier 2 — 2 new tarballs added to `tools/imogen_data_manifest.txt`

| Component | Tarball | Compressed | Raw | SHA256 |
|---|---|---:|---:|---|
| `emiss-reference` | `imogen-emiss-reference-v1.0.tar.gz` | 311 KB | 5.2 MB | `77b05df3…` |
| `ndep-lamarque` | `imogen-ndep-lamarque-v1.0.tar.gz` | 460 MB | 501 MB | `a135d647…` |

The fetch script needed **zero code changes** — just two new manifest
rows. `tools/fetch_imogen_data.sh --verify-only` cleanly verifies all
6 components.

#### Tier 3 — `data/DATA.md` (new) documents acquisition

Records paths + recipes for:

- PLUM scenario LU at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/`
  (86 GB; per Decision #10 used via `save_state`/`restart` strategy)
- Legacy concatenated `Data/LU/SSP1_RCP26_concatenated/` (7.3 GB; superseded fallback)
- Legacy `Data/Intermediary/` (2.2 GB; production shifts to `intermediary_py` step 10)
- Predecessor's pre-baked IMOGEN outputs (~2 GB each; reproducible by re-run)
- Public datasets used by `intermediary_py`: HILDA+ v2, FAOSTAT,
  EDGAR 2025, RCMIP Phase 2 v5.1.0, FAIR ERF v1.3, IIASA SSP db
- NOAA GMD + AGAGE atmospheric concentration observations (step 17 validation)

### Changed — `imogen/emiss/` restructured to full tree

The step-4 flat-3-files layout (just the RCP8.5 triple from
`DKB_dataset_totals/` at the top level) was replaced with the full
`Data/Imogen/emiss/` tree (CMIP5/, CMIP6/, DKB_dataset_totals/,
new_emission_data/, rcp_database/, + 6 loose top-level files).

This was **necessary** — the active coupled-mode reference config at
`landsymm_imogen_setup/.../SSP1_RCP26/imogen_intermediary.ins`
references files at the deeper subdir paths
(`imogen/emiss/CMIP6/{Co2,CH4-N2O,Non-Co2-CH4-N2O-RF}/<scenario>/...`).
Without the full tree, coupled-mode runs at step 9+ would fail to
resolve their FILE_SCEN_EMITS / FILE_NON_CO2_VALS / FILE_CH4_N2O_EMITS /
FILE_LPJG_FLUX / FILE_LPJG_CH4_N2O_FLUX paths.

`imogen/code/imogen_settings.txt`'s 3 `FILE_*_EMITS` keys were updated
correspondingly (added the `DKB_dataset_totals/` subdir prefix).

### Changed — `.gitignore` extension

Added `data/ndep/ndep_cruncep/` exclusion for the Lamarque
binaries, with allow-list override for `data/ndep/README.md`.

### Verification

- Tier 1: 31 trackable files, 14 MB total — exactly as classified.
- Tier 2 manifest: all 6 entries verify clean SHA256 + size via
  `tools/fetch_imogen_data.sh --verify-only`.
- Tier 3: `data/DATA.md` written; cross-referenced from `data/README.md`.
- **Standalone IMOGEN regression smoke** — after the
  `imogen_settings.txt` path update, the binary still produces years
  1871, 1872 with all expected climate files (T_anom.dat,
  P_anom.dat, etc.). No regression from the path restructure.
- The full coupled-mode run-completion verification is gated on
  step 7 (the source-level coupling fixes).

### Files added (committed)

- `data/DATA.md` (new — Tier-3 acquisition recipes)
- `data/soil/soilmap_center_interpolated.remapv10_old_62892_gL.dat`
- `data/gridlist/{7 files}`
- `data/concentrations/{23 files}` (EPA + IIASA CMIP5/CMIP6 small files only)
- `data/ndep/README.md` (Tier 2 acquisition pointer)
- `notes/STEP_6.md`

### Files modified

- `.gitignore` (data/ndep exclusion + README allowlist)
- `tools/imogen_data_manifest.txt` (2 new rows)
- `imogen/code/imogen_settings.txt` (3-line FILE_*_EMITS path update)
- `imogen/emiss/README.md` (rewritten for the restructured tree)
- `data/README.md` (Tier-1/2/3 inventory)
- `notes/FOLLOWUPS.md` (close F-5)
- `EXECUTION_PLAN.md` (V.1 step 6 marked complete)

### NOT in this release

- 5 Lamarque .bin files (gitignored, regenerated by fetch).
- Full `imogen/emiss/{CMIP5,CMIP6,…}/` tree (gitignored, regenerated by fetch).
- The 86 GB PLUM scenario LU at `/media/bampoh-d/...` (Tier 3, document only).
- The legacy 7.3 GB concatenated LU and 2.2 GB Intermediary tree (skipped per V.1 spec; reproducible).

---

## [v0.5.0-cmip6-converter] — 2026-05-06 — step 5

### Added — `tools/cmip6_nc_to_cmip5_ascii.py` (CMIP6 NetCDF → CMIP5 ASCII)

Per `EXECUTION_PLAN.md` §V step 5 + Appendix A.3, implemented the
CMIP6 NetCDF → CMIP5 ASCII converter so the Fortran IMOGEN binary
can run against any of the 5 CMIP6 GCMs (GFDL-ESM4, IPSL-CM6A-LR,
MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL) without modifying the
binary's pattern reader.

**~340 Python lines** (xarray + scipy bilinear interpolation). Two
operating modes:

- Single-GCM: `--nc`, `--json`, `--output`
- Batch: `--input-dir`, `--output-base` (auto-discovers all 5 GCMs
  in ~1.6 sec wall-clock)

For each (GCM, month):
1. Read NetCDF with xarray; verify expected dims `(imogen_drive=12,
   lat=56, lon=96)`.
2. Read target gridlist (1631-cell IMOGEN HadCM3 land grid from
   `imogen/code/patterns_gridlist.txt`).
3. Bilinearly interpolate each of 8 `_patt` variables onto target
   gridlist. Handles lat-descending and lon-negative source grids.
4. Apply per-column transform (e.g. `wind_patt × 1/√2` for U/V split).
5. Write CMIP5-style ASCII with bbox header
   `0.00 -60.00 360.00 90.00` + 1631 data rows × 12 columns.
6. Emit Fortran namelist `<MODEL>_ebm.nml` with KAPPA_O, LAMBDA_L,
   LAMBDA_O, MU, F_OCEAN from the JSON params.

#### Verified column ordering

Authoritative ordering from `imogen_lpjg.f::GCM_ANLG` `READ` statement
at line 3270-3274 (the Appendix A.3 sketch had 12 mapped variables,
which was incorrect — actual is **10 variable columns + 2 coords**):

```text
LON LAT  T  RH15M  U-wind  V-wind  LW  SW  DTEMP_DAY  RAIN  SNOW  PSTAR
[1] [2] [3]  [4]    [5]     [6]   [7] [8]  [9]       [10]  [11]  [12]
```

#### Three documented CMIP6→CMIP5 mapping caveats

- **CAVEAT-A**: CMIP6 `ql1_patt` (units "K-1") passed through directly
  into CMIP5 col 4 `DRH15M_PAT` without unit conversion. Upstream
  alignment with IMOGEN's RH-sensitivity convention to be confirmed
  with the CMIP6 NetCDF generator (followup **F-6**).
- **CAVEAT-B**: CMIP6 stores wind-speed magnitude only; we split
  equally `U = V = wind_patt / √2` to preserve magnitude. Loses
  direction. Acceptable for v1.0; revisit at step 9.5 if needed
  (followup **F-8**).
- **CAVEAT-C**: CMIP6 stores total `precip_patt` only; we put full
  pattern into RAIN col 10 and 0.0 into SNOW col 11. Total preserved;
  rain/snow split handled downstream by IMOGEN's temperature-based
  partition rule (followup **F-8**).

#### Verification

- Build clean. `--help`, `--list`, `--component`, `--verify-only` all
  tested.
- Standalone IMOGEN run with `DIR_PATT=patterns/CEN_CMIP6_MOD_MRI-ESM2-0/`
  produces years 1871, 1872 with all expected climate files written.
- Cell (lat=82.5°, lon=281.25°, Jan): our CMIP6/MRI T = 237.676 K
  vs step 4's CMIP5/IPSL T = 237.736 K — **0.06 K** difference
  (within the inter-GCM scatter expected from year 1871's tiny
  land-mean anomaly).

#### Open follow-up: `pstar_patt` units

Discovered while comparing converter output: the CMIP6/MRI Pstar
pattern at the same Arctic cell is −49.40 vs CMIP5/IPSL +0.32 — a
150× magnitude difference + opposite sign. Most likely a Pa-vs-hPa
unit mismatch in the source NetCDF; needs author confirmation
(followup **F-7**).

### Files added (committed to git)

- `tools/cmip6_nc_to_cmip5_ascii.py` (new)
- `notes/STEP_5.md` (new — per-edit verification)

### Files modified

- `.gitignore` — gitignore the derivative `*_ebm.nml` output
- `imogen/patterns/README.md` — extend with conversion recipe + caveats
- `tools/README.md` — extend with the converter under "Implemented tools"
- `notes/FOLLOWUPS.md` — add F-6, F-7, F-8
- `CHANGELOG.md` — this entry
- `EXECUTION_PLAN.md` — V.1 step 5 marked ✅

### NOT in this release

- 5 derivative directories `imogen/patterns/CEN_CMIP6_MOD_<gcm>/` and 5
  `<gcm>_ebm.nml` files (regeneratable; gitignored).
- A source-code fix for bug C2/C3 (deferred to step 7).
- Numerical parity Fortran ↔ C++ (Phase-2; Decision #2).

---

## [v0.4.0-imogen-data-fetch-script] — 2026-05-05 — step 4

### Added — IMOGEN reference-data acquisition infrastructure + first real Fortran output

Per Decision #5 (incremental rebuild) and `EXECUTION_PLAN.md` §V step 4,
imported the IMOGEN GCM patterns + CRUNCEP base climatology AND
established a clean **acquisition pattern** for the unified codebase:
the data lives **outside git** (49 MB compressed → 161 MB extracted)
and is fetched at setup time via a manifest-driven script.

#### `tools/fetch_imogen_data.sh` + `tools/imogen_data_manifest.txt`

- **Manifest format**: per-tarball record with filename, SHA256, size,
  and extract-path. 4 tarballs catalogued (CMIP5 ~19 MB, CMIP6 ~19 MB,
  CMIP3 legacy 534 KB, CRUNCEP ~11 MB).
- **Fetch script modes**:
  - `--list`: print manifest summary
  - default: fetch + SHA256-verify + extract
  - `--verify-only`: re-checksum without extracting (CI-friendly)
  - `--component <name>` (repeatable): partial fetch
- **Source flexibility**: `--base` accepts either a local directory
  path (workstation case during development) or an `https://` URL
  prefix (a TBD permanent host like Zenodo / GitHub Releases /
  institutional bucket — to be set up by the user post-step-4).
- **Initial draft hit the classic `set -e` + `((var++))` bash pitfall**;
  fixed by replacing `((errors++))` with `errors=$((errors+1))`.

#### `imogen/patterns/`, `imogen/CRUNCEP_1960_1989/`, `imogen/emiss/`

Reference data staged locally on the workstation (gitignored):

- 35 GCM pattern dirs (34 CMIP5 ASCII + 1 CMIP6 NetCDF + 1 CMIP3 legacy)
- 30-year CRUNCEP base climatology (12 mo × 30 yr × 1631 cells)
- 3 small reference RCP8.5 emission files

Each directory has a small README committed to git that explains
structure + provenance + acquisition; the actual data does not.

#### Standalone Fortran IMOGEN smoke run — first real scientific output

The verification milestone deferred from step 2 has now been hit:

- Years 1871 + 1872 produce per-year output at `imogen/code/IMOGEN/output/<YYYY>/`
- All expected ASCII climate files written (`T_anom.dat`, `P_anom.dat`,
  `SW_anom.dat`, `DTEMP_anom.dat`, `WET.dat`, `dtemp_o.dat`,
  `fa_ocean.dat`, `CO2.dat`, `done`)
- Numerical content is physically plausible (Arctic 82.5° N
  monthly Kelvin temperatures range 231–276 K)
- CO2.dat correctly reflects the initial concentration settings
  (286.085 ppm CO2; 865 ppb CH4; 277.4 ppb N2O)

Comparison against `version_A`'s reference 1871 output (which appears
to have been generated by the **C++ refactor**, not Fortran, based on
its `[IMOGEN LOGGER][2025-06-16 …][INFO]` log-line format):

- Same files, minus `Rh_anom.dat` + `W_anom.dat` (confirms `[SA3 §10]`;
  these are C++-only, will be ported in step 9.5 per Decision #11).
- Same column structure, but our Fortran writes 2× the lines and
  with more decimals (to investigate as a Fortran writer follow-up).
- Numerical T values diverge by 0.1–8 K vs version_A's C++ output
  (expected; Fortran ↔ C++ numerical parity is itself the Phase-2
  milestone per Decision #2).

#### Bug C2/C3 work-around for first run

The standalone run blocks indefinitely in the polling loop at
`imogen_lpjg.f:400-403` waiting for `DONE_EXIST=T`, because line 363's
default `DONE_EXIST=.TRUE.` was commented out at some point (the
"neutered polling-loop safety check" of `[CMI §1.2 / SA3 §10]`). For
step 4 this is **worked around at runtime** by pre-staging an empty
`done` file in `LPJG_main/IMOGEN/`. The source-level fix lands at
**step 7** of the rebuild plan.

### Fixed

- `.gitignore` was silently broken for `imogen/patterns/CEN_*/`,
  `imogen/patterns/CMIP6_*/`, and `imogen/patterns/ukmo_hadcm3_rel/`
  due to **inline comments after the pattern**. Gitignore does NOT
  support inline comments — they get parsed as part of the pattern.
  Fix: moved comments to their own lines. Effect: 431 pattern files
  (which had been technically untracked-but-not-ignored, easily
  `git add`-able by accident) are now correctly ignored.

### Files touched

- `tools/fetch_imogen_data.sh` (new, ~210 lines)
- `tools/imogen_data_manifest.txt` (new, 4 entries)
- `tools/README.md` (extended)
- `imogen/patterns/README.md` (new)
- `imogen/patterns/readme.log` (new — upstream provenance, 127 B)
- `imogen/CRUNCEP_1960_1989/README.md` (new)
- `imogen/emiss/README.md` (new)
- `imogen/README.md` (extended; step-4 milestone section)
- `notes/STEP_4.md` (new — full per-edit verification record)
- `.gitignore` (fix + additions)
- `EXECUTION_PLAN.md` (V.1 step 4 marked ✅)

### NOT in this release

- The 4 data tarballs themselves (saved at sibling path
  `lpj-guess_imogen_landsymm_data/`; user uploads to a permanent host
  in a follow-up — tracked as **F-1** in `notes/FOLLOWUPS.md`).
- A source-code fix for bug C2/C3 (deferred to step 7).
- Rh/W writer parity in Fortran (deferred to step 9.5).
- CMIP6 NetCDF → ASCII converter (step 5).
- Coupled-mode validation (steps 6-9).
- Investigation of the 2× line count of our Fortran's `T_anom.dat`
  vs `version_A`'s reference (low priority — tracked as **F-2**
  in `notes/FOLLOWUPS.md`).

### Follow-ups document

This release introduces `notes/FOLLOWUPS.md` — a centralised tracker
for non-blocking action items raised during step work. Items move
from OPEN to DONE as they close. Currently 5 OPEN items
(F-1 through F-5).

---

## [v0.3.0-fortran-allocatable] — 2026-05-05 — step 3

### Changed — Fortran IMOGEN: `ALLOCATABLE` array refactor (`NGPOINTS` runtime)

Per Decision #2 (Fortran-with-`ALLOCATABLE`-first IMOGEN strategy)
and `EXECUTION_PLAN.md` §V step 3, the 6 `NGPOINTS`-dimensioned
arrays in `imogen/code/imogen_lpjg.f` `PROGRAM IMOGEN` were
converted from static to Fortran-90 `ALLOCATABLE`, and the
`PARAMETER(NGPOINTS=3698)` was promoted to a run-time setting:

- `T_OUT_M_REGRID(:,:,:,:)`, `P_OUT_M_REGRID(:,:,:,:)`,
  `SW_OUT_M_REGRID(:,:,:,:)`, `DTEMP_OUT_M_REGRID(:,:,:)`,
  `F_WET_CLIM_REGRID(:,:)`, `LON_OUT(:)`, `LAT_OUT(:)` are now
  `ALLOCATABLE`, allocated in `PROGRAM IMOGEN` immediately after
  `CALL SETTIN(...)` returns the run-time `NGPOINTS` value.
- `imogen/code/imogen_settings.txt` gains a new
  `NGPOINTS 3698` key; `SUBROUTINE SETTIN` reads it via a new
  `CASE('NGPOINTS')` branch (signature now ends `…,CO2_RF_FAIR,NGPOINTS)`).
- A sentinel value (`NGPOINTS = -1`) plus post-loop validation in
  `SETTIN` aborts with a clear error message if the new key is
  missing or non-positive — preventing silent failure.
- A matching `DEALLOCATE(...)` block before `STOP` in `PROGRAM IMOGEN`
  ensures clean shutdown (with `IF(ALLOCATED(...))` guards to remain
  safe under any future early-error path).
- A startup banner `IMOGEN: ALLOCATEd regrid arrays for NGPOINTS=…`
  prints the actual value at run time, supporting the units-integrity
  rule "startup banners".

### Verification

- Build with `gfortran -ffixed-line-length-132 -O` succeeds clean (no
  warnings).
- **Positive smoke probe** (`NGPOINTS=3698`, default): parser reads,
  ALLOCATEs ~33 MB heap, terminates at later runtime input read
  (`IMOGEN/CO2_all.dat`) — same termination signature as step 2 →
  no regression.
- **Negative smoke probe** (`NGPOINTS` line removed from settings):
  validation fires, clean abort with helpful error message,
  `STOP 1`.
- **Scaling probe** (`NGPOINTS=10000`): parser reads new value,
  ALLOCATEs ~90 MB heap, terminates at same later runtime input
  read → confirms the run-time configurability works.

### Deferred (not in this release)

- `GPOINTS`-dimensioned arrays (~30 of them) remain `PARAMETER`-sized
  at 1631; conversion to `ALLOCATABLE` is a marginal heap-vs-BSS
  tweak with no functional benefit and is deferred to a future
  cleanup step. Changing `GPOINTS` itself requires regenerating the
  pattern + CRUNCEP files (1 631 cells locked in by upstream).
- `NFARRAY` (10 000) and `N_OLEVS` (254) likewise remain `PARAMETER`
  — neither is a memory bottleneck nor user-facing.
- `nonco2.f` references none of these constants → no changes needed
  there.

### Files touched

- `imogen/code/imogen_lpjg.f` — 7 ALLOCATABLE decls, ALLOCATE block,
  DEALLOCATE block, SETTIN signature/decl/sentinel/CASE/validation.
- `imogen/code/imogen_settings.txt` — added `NGPOINTS 3698` line.
- `notes/STEP_3.md` — full per-edit verification record.
- `imogen/README.md` — step-3 layout + ALLOCATABLE-refactor section
  + how to scale to 62 000 cells.

### Documentation updates

- `EXECUTION_PLAN.md` Part V step 3 marked ✅ complete.

---

## [v0.2.0-imports] — 2026-05-05 — steps 1 + 2

### Added — LPJ-GUESS LandSyMM fork (step 1)

- `lpjguess/` populated with the upstream LPJ-GUESS LandSyMM fork
  (`trunk_r13078`-equivalent, chosen over upstream `trunk_r13078`
  to avoid the `exit(200)` regression).
- Build configured with Anaconda3 NetCDF (per Decision #8) — works
  cleanly on the user's workstation where the native Ubuntu HDF5
  has a `curl_global_init@CURL_OPENSSL_4` ABI mismatch with libcurl
  4.
- All 162 unit tests pass post-import; CFX smoke test deferred to
  step 6.
- Documented in `notes/STEP_1.md`.

### Added — Fortran IMOGEN with immediate fixes (step 2)

- `imogen/code/` populated with `imogen_lpjg.f`, `nonco2.f`,
  `Makefile`, `compile.sh`, gridlists, etc.
- Step-2 fixes applied immediately on import:
  - **C10**: removed `PAUSE` statement in `QSAT` (halted
    non-interactive runs).
  - **C11**: removed `qsat_output.txt` debug-dump (file-handle
    leak; O(GB) of unused output).
  - **C12**: replaced Windows `\IMOGEN\output\` mkdir paths with
    forward slashes.
  - **C13**: rewrote Windows absolute paths in `imogen_settings.txt`
    to relative paths.
  - **Makefile**: replaced Windows `del` with `rm -f`; renamed
    target from `imogen` to `imogen_lpjg`.
  - **compile.sh**: removed `.exe` Windows convention.
- Build with `gfortran` succeeds clean; functional probe confirms
  startup + settings parsing.
- Standalone IMOGEN-only run deferred to step 4 (requires patterns
  + CRUNCEP).
- Documented in `notes/STEP_2.md`.

---

## [v0.1-skeleton] — 2026-05-05

### Added — initial repository scaffolding (step 0 of the rebuild plan)

- **Top-level files**:
  - `README.md` — top-level navigation, project overview, build/run
    placeholder, roadmap, citation pointers.
  - `LICENSE` — MIT, with reference to upstream component licences.
  - `CITATION.cff` — machine-readable citation metadata for the
    framework and its underlying peer-reviewed components.
  - `CONTRIBUTING.md` — development workflow, per-step verification
    discipline, three-remote push pattern, units-integrity
    discipline (six rules from `EXECUTION_PLAN.md` §I.D plus the
    reciprocal producer/consumer checks of §I.D.7).
  - `CHANGELOG.md` — this file.
  - `.gitignore` — comprehensive build artefact + run output +
    Python venv + IDE noise filtering, with allow-list overrides
    for per-subdir READMEs.
- **Top-level directory scaffolding** (12 dirs, each with a
  placeholder `README.md` to be expanded as the rebuild progresses):
  - `lpjguess/` — LPJ-GUESS LandSyMM fork (Phase 1 baseline:
    `trunk_r13078`; Phase 2 switchable backend: integrated LTS).
  - `imogen/` — Fortran IMOGEN with planned `ALLOCATABLE`-array
    refactor (Phase 1); C++ refactor brought to numerical parity
    in Phase 2.
  - `intermediary_py/` — Python `imogen_ghg_controller v0.1.0`
    (IPCC Tier-1 + RCMIP substitution).
  - `tools/` — cross-component utilities (the
    `imogen_inputs_to_lpjg_format.py` adapter,
    `cmip6_nc_to_cmip5_ascii.py` converter, regrid utilities).
  - `runs/` — per-scenario run setups
    (`runs/historic/` for the HILDA+ standalone Phase-1 with
    `save_state` at 2020; `runs/SSP1-2.6/`, `runs/SSP2-4.5/`,
    etc. for coupled scenario restart from 2020).
  - `data/` — small reference data (gridlists, soil map, etc.);
    large data documented in `data/DATA.md` for separate
    acquisition.
  - `scripts/` — `run_coupled.sh` (workstation),
    `run_coupled.sbatch` (cluster SLURM), `cluster/` (owl helpers).
  - `ci/` — CI/CD workflow definitions.
  - `docs/` — unified technical manual, scientific framework, build
    instructions, troubleshooting, glossary.
  - `paper/` — manuscript draft + figures + cited peer-reviewed PDFs.
  - `notes/` — per-step development notes
    (`notes/STEP_<n>.md` for each Part V step).
  - `archive/` — frozen legacy code preserved for reference
    (older C++ refactor before parity, retired Imogen-controller,
    legacy C++ Intermediary, etc.).

### Preserved — investigation evidence base (immutable)

- **`COUPLED_MODEL_INVESTIGATION.md`** (240 KB / 3 968 lines) —
  master investigation document covering: state of the system; the
  seven coupling break-points + bug C35 (`FILE_LPJG_FLUX`
  path-override); seven scientific framework lineages; system
  architecture (8 components plus auxiliaries); per-component deep
  dives drawing from the 8 subagent reports; full
  ~120-item bug catalogue with severity tags
  (🔴 active / 🟡 latent / 🟢 cosmetic); 11 documentation
  contradictions plus 4 doc-vs-code mismatches; A-vs-B divergence
  accounting; 24 open questions; 6-layer roadmap; recommended
  directory structure (which this scaffolding implements).
- **`EXECUTION_PLAN.md`** (142 KB / 2 595 lines) — operational
  checklist with: 12 settled strategic decisions (RCMIP backbone,
  Fortran-with-`ALLOCATABLE` first / C++ port second, `trunk_r13078`
  first / integrated LTS second, tight coupling default,
  incremental rebuild approach, units-integrity discipline,
  single codebase for workstation+cluster, Anaconda3 NetCDF
  preference, Stage I deferred-not-removed, save_state/restart
  LU strategy, Tmin/Tmax computation, Rh+W output asymmetry); item-
  by-item gap inventory (I.A code-level fixes, I.B 7 missing
  components, I.C data acquisition, I.D 7 units-integrity rules);
  11 strategic-decision write-ups; Part V formal step-by-step
  rebuild plan with verification milestones (steps 0-19, plus 9.5
  for climate-output enhancements; ~25-35 person-days to v1.0,
  ~7-10 weeks calendar); 5 implementation sketches in the appendix.
- **`_phase2_findings/`** (424 KB / 6 507 lines across 8 reports) —
  the canonical evidence base: documentation inventory, LPJ-GUESS
  `trunk_r13078`, Fortran IMOGEN, C++ IMOGEN refactor, C++
  Intermediary, Python Intermediary, GCM patterns + regrid
  utilities, run setups + orchestration + Data/. Cited inline
  throughout the master doc as `[SAn §x.y]`.

### Status

Scaffolding only. No build yet. The actual model code lands at
step 1 (LPJ-GUESS import) and onwards.

---

## [v0.0-investigation] — 2026-05-04

### Added — investigation phase (predecessor)

The investigation phase of this rebuild — performed entirely on the
predecessor framework trees `version_A/` and `version_B/` and the
two related projects `lpjg_landsymm_integration/` and `landsymm_py/`
— produced the three documents captured in the v0.1-skeleton
release:

- `COUPLED_MODEL_INVESTIGATION.md`
- `EXECUTION_PLAN.md`
- `_phase2_findings/01_documentation_inventory.md`
- `_phase2_findings/02_lpjguess_trunk_r13078.md`
- `_phase2_findings/03_imogen_fortran.md`
- `_phase2_findings/04_imogen_cxx.md`
- `_phase2_findings/05_intermediary_cpp.md`
- `_phase2_findings/06_intermediary_py.md`
- `_phase2_findings/07_patterns_and_regrid.md`
- `_phase2_findings/08_orchestration_and_data.md`

These document the state of `version_A` and `version_B` at the
investigation moment (4-5 May 2026) and serve as the immutable
evidence base for every claim in the rebuild plan.

The `version_A` and `version_B` framework trees themselves are
**not part of this repository** — they are preserved as read-only
reference at their original paths
(`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/version_{A,B}/`)
and are not modified by this rebuild.
