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

### 2026-05-10 (later) — Step 17a (F-12 sub-milestone C1.1) IMOGENINPUT IMPLEMENTATION: ImogenInput year_outer overrides (preload_all_climate + getclimate_for_year) with corrected spinup_year_idx state-machine reproduction formula (no tag — full step-17a tag waits for runtime cross-validation)

C1.1 implementation lands the FIRST input-module override pair for the
year_outer code path: `ImogenInput::preload_all_climate(gridcell, first_yr,
last_yr)` + `ImogenInput::getclimate_for_year(gridcell, year, day)`. This
makes the year_outer code path runnable end-to-end with `-input imogen`
(loose-coupling input module) once climate is pre-staged on disk.

#### Strategic decision: ImogenInput first; IMOGENCFXInput follow-up

**ImogenInput chosen over IMOGENCFXInput for C1.1** because ImogenInput
has NO `RUN_IMOGEN_ENGINE()` call in `init()` (verified via grep — only
`imogencfx.cpp:524` has it). This means loose-mode runs (`-input imogen`
+ `coupling_mode "loose"`) complete `init()` cleanly + reach the LPJG
main loop, regardless of `framework_loop_mode` setting — **no engine-bypass
workaround needed for cross-validation**. The two input modules have
~95% identical `getclimate()` patterns; the implementation strategy +
spinup_year_idx formula derived in C1.1 transfers near-verbatim to
`IMOGENCFXInput` (planned as C1.3 follow-up sub-step within step 17a).
Per the foundation-vs-full-C1 staging in `notes/STEP_17a.md` §5.5.

#### What changed in `lpjguess/` source (2 files; ~280 LOC; backport-relevant)

- **`lpjguess/modules/imogen_input.h`** (+~80 LOC):
  - 3 new includes: `<map>`, `<utility>`, (already-existing) `lamarquendep.h`
  - 2 new `virtual` method declarations (overrides of `InputModule`
    base-class virtuals added at the foundation commit `2e918c0`):
    - `preload_all_climate(Gridcell&, int first_calendar_year, int last_calendar_year)`
    - `getclimate_for_year(Gridcell&, int calendar_year, int day_of_year)`
    Both have extensive doc blocks documenting the design rationale +
    the spinup_year_idx state-machine reproduction formula + cross-references.
  - 2 new private cache members for year_outer state:
    - `std::map<std::pair<double,double>, int> year_outer_cell_idx`
      — keyed by (lon, lat); maps to `current_grid_index` value at
      preload time
    - `std::map<std::pair<double,double>, Lamarque::NDepData> year_outer_ndep_cache`
      — keyed by (lon, lat); maps to value-copy of `ndep` member at
      preload time (right after `getgridcell -> ndep.getndep()`)

- **`lpjguess/modules/imogen_input.cpp`** (+~200 LOC):
  - `ImogenInput::preload_all_climate(gridcell, first_yr, last_yr)`
    implementation: caches `cell_idx` + `ndep` value-copy, then for each
    year_idx in [0, total_years): computes `imogen_year` via the formula
    below, looks up in `stored_years[]` cache, on cache miss assigns
    next `last_store_index++` slot + calls existing `readenv()` + loads
    CO2 via `co2.load_file(...)`. Reuses existing infrastructure
    verbatim; pre-loads eagerly (memory bounded for smoke-scale runs).
  - `ImogenInput::getclimate_for_year(gridcell, calendar_year, day_of_year)`
    implementation: looks up cached `cell_idx` + `cell_ndep`, computes
    `imogen_year` via same formula, finds `store_index` in cache. On
    day 0: calls existing `get_climate_for_gridcell(...)` to populate
    per-day arrays + ndep distribution + CO2. Every day: assigns
    `climate.{temp - 273.15 K→degC, prec, insol, dtr conditional}` +
    `gridcell.{dNH4dep, dNO3dep}` from per-day arrays. Returns false at
    sim-done terminator + on missing-grid-point conditions.

#### CORRECTED spinup_year_idx state-machine reproduction formula

**ERRATUM applied this commit**: the foundation commit's docs (CHANGELOG
2026-05-10 entry, FOLLOWUPS F-12 C1 pre-flight findings extension,
STEP_17a.md §5.4, BACKPORT_LEDGER step-17a-foundation entry,
session-2 chat handoff Part 10) all stated the formula as
`(cell_idx * nyear_spinup + year_idx + 1) % NYEAR_SPINUP` (with `+1`).
The CORRECT formula has NO `+1`:

```
spinup_year_idx_at_(cell_idx, year_idx)
    = (cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP
```

Derivation (verified by tracing the EXACT code at `imogen_input.cpp`
lines 781-805 + `imogencfx.cpp` lines 1071-1095 during C1.1
implementation):
- `init()` sets `spinup_year_idx = 0`
- Per the existing `getclimate()`: on day 0 of each spinup year,
  `imogen_year = FIRST_SPINUP_YEAR + spinup_year_idx` is computed
  using the CURRENT spinup_year_idx, THEN the counter is incremented.
- For cell C, spinup year Y, day 0: cumulative spinup-year-day-0
  increments BEFORE this call = `C * nyear_spinup + Y` (since cell C
  is preceded by C cells × nyear_spinup spinup years; within cell C,
  Y prior spinup years have been processed).
- Each such call increments `spinup_year_idx` by 1 (modulo NYEAR_SPINUP).
- So `spinup_year_idx_BEFORE_this_call = (C * nyear_spinup + Y) % NYEAR_SPINUP`.

The C1.1 implementation in `ImogenInput::preload_all_climate` +
`ImogenInput::getclimate_for_year` uses the CORRECTED formula.
Subsequent doc updates (this CHANGELOG entry, FOLLOWUPS F-12 erratum,
STEP_17a.md §5.4 erratum, BACKPORT_LEDGER step-17a-c1.1 entry,
session-2 chat handoff Part 11) all reflect the CORRECTED formula.

#### Verification (this commit)

- `cd lpjguess/build && make -j$(nproc)` (full clean rebuild): clean
  (only pre-existing `simfire_input.h` `cruncep_*.h`
  `GlobalNitrogenDeposition*.h` `gutil.{cpp,h}` `indata.cpp` warnings;
  ZERO warnings introduced by C1.1 additions)
- `lpjguess/build/runtests --reporter compact`: "Passed all 25 test
  cases with 162 assertions." (default-mode + new-input-module
  byte-exact regression preserved)
- Spinup_year_idx formula correct (NO +1): hand-traced against
  `imogen_input.cpp:781-805`
- Per-cell ndep cache copies are independent: `Lamarque::NDepData` is
  value type (no pointers; just arrays); `std::map<key, NDepData>`
  value-copies on insert
- K → degC temperature conversion preserved: `getclimate_for_year` line
  `climate.temp = dtemp[day_of_year] - 273.15;` matches existing
  `getclimate` line 876
- Backward compatibility with existing `getclimate()` (gridcell_outer
  mode): `getclimate()` body unchanged; new methods are SEPARATE
  additions; existing code path completely intact

#### What this commit does NOT yet do (next session(s) within step 17a)

- **C1.2 cross-validation** (~1-2 days): runtime bit-exact verification
  of Run A (`gridcell_outer`) vs Run B (`year_outer`) on smoke gridlist.
  Operational pre-requisites: pre-stage climate (re-run launcher per
  session-1 §49.1 operational pattern; ~3-5 min wall-clock + Ctrl-C);
  custom .ins with `coupling_mode "loose"`; bash harness; iterate on
  any divergences. **GO/NO-GO gate for C1.**
- **C1.3 IMOGENCFXInput year_outer override** (~2-3 days): replicate
  the C1.1 implementation pattern for IMOGENCFXInput (with the
  additional climate fields it handles + an optional engine-bypass
  parameter for testing). Cross-validate identically.
- **C1 close-out**: tag `v0.17.0-step17a-c1-year-outer-single-process`.

Backport-relevance HIGH (purely additive). Per the new step-17a-c1.1
entry in `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3.

---

### 2026-05-10 — Step 17a (F-12 sub-milestone C1) FOUNDATION: framework_loop_mode parameter + InputModule virtuals + framework.cpp year_outer additive code path (no tag — full step-17a tag waits for IMOGENCFXInput overrides + cross-validation)

Foundation for the F-12 Option C staged implementation lands. The architectural
foundation for the per-year-outer / per-gridcell-inner loop (which resolves
F-10's per-gridcell-outer / per-day-inner-across-all-years deadlock for tight
coupling at root) is in place; default mode (`framework_loop_mode = "gridcell_outer"`)
preserves LTS-equivalent behaviour byte-exactly.

#### What changed in `lpjguess/` source (6 files; ~250 LOC; backport-relevant)

- **`lpjguess/framework/parameters.h`** (+22 LOC): new `extern xtring framework_loop_mode;`
  in `IMOGENConfig` namespace, adjacent to `coupling_mode` (added at step 8).
  Inline doc block explains both values + F-10 connection + cross-references.
- **`lpjguess/framework/parameters.cpp`** (+8 LOC): `xtring framework_loop_mode = "gridcell_outer";`
  default value preserves LTS-equivalent behaviour byte-exactly.
- **`lpjguess/modules/imogencfx.cpp`** (+12 LOC): `declare_parameter("framework_loop_mode", ...)`
  registration in `IMOGENCFXInput::IMOGENCFXInput()` constructor, mirroring
  the proven `coupling_mode` pattern from step 8.
- **`lpjguess/framework/inputmodule.h`** (+50 LOC): two new `virtual` methods
  on the `InputModule` abstract base class — `preload_all_climate(Gridcell&,
  int first_calendar_year, int last_calendar_year)` and `getclimate_for_year
  (Gridcell&, int calendar_year, int day_of_year)`. Non-pure (default
  implementations in inputmodule.cpp); preserves backward compatibility
  across all 9 existing input modules without forcing stub overrides.
- **`lpjguess/framework/inputmodule.cpp`** (+33 LOC): default-fail
  implementations of the two new virtuals. Both abort with a clear error
  pointing at `framework_loop_mode = "gridcell_outer"` fallback + canonical
  docs (`notes/FOLLOWUPS.md` F-12 + `notes/STEP_17a.md`).
- **`lpjguess/framework/framework.cpp`** (+218 LOC additive; existing 124-line
  per-gridcell-outer block at lines 411-534 byte-untouched via early-return
  pattern): new `if (IMOGENConfig::framework_loop_mode == "year_outer") { ... return 0; }`
  block immediately before the existing `while (true)` per-gridcell-outer
  loop. The new block has 5 phases: (1) C1 limitation guards (fail fast on
  restart/save_state/crop_gs_out/printseparatestands; deferred to C1.2/C1.3);
  (2) year range determination; (3) pre-load all gridcells + preload climate
  per cell via the new InputModule virtual; (4) per-year outer loop calling
  `simulate_day` per cell per day via `getclimate_for_year`; (5) per-cell
  teardown + cleanup + explicit return.

#### Verification (this commit)

- `cd lpjguess/build && make -j$(nproc)`: ✅ clean (only pre-existing
  `simfire_input.h` `fread` warnings; unrelated)
- `lpjguess/build/runtests --reporter compact`: ✅ "Passed all 25 test
  cases with 162 assertions." (default-mode byte-exact regression
  preserved)
- `git diff -w` of existing per-gridcell-outer block (`framework.cpp`
  lines 411-534): ZERO whitespace-only changes (additive early-return
  pattern preserves existing block structure)
- Default-fail virtuals: static verification only this commit; runtime
  exercise deferred to next session when an input module's override is
  invoked

#### What this commit does NOT yet do (next session(s) within step 17a)

- IMOGENCFXInput override of `preload_all_climate` + `getclimate_for_year`
  — substantial work (~3-5 days): includes the per-cell `spinup_year_idx`
  state-machine reproduction formula uncovered this session
  (`spinup_year_idx_at_cell_idx_year_idx = (cell_idx * nyear_spinup +
  year_idx + 1) % NYEAR_SPINUP`), which year_outer mode needs to
  reproduce gridcell_outer's existing cell-ordering-dependent imogen_year
  selection
- Bit-exact cross-validation of Run A (`gridcell_outer`) vs Run B
  (`year_outer`) on smoke gridlist (single-cell first to bypass
  cell-ordering complexity; multi-cell second to test the formula)
- Tag `v0.17.0-step17a-c1-year-outer-single-process` (waits for
  cross-validation pass)

#### New finding from this session: `IMOGENCFXInput::spinup_year_idx` cross-cell coupling

Beyond session-2 §9.5's PRNG audit, this session discovered that
`IMOGENCFXInput::spinup_year_idx` (line 220 of `imogencfx.h`) is a
class-member counter that **persists across cells** in the existing
gridcell_outer mode — each cell sees a different starting value of
`spinup_year_idx`, causing different spinup `imogen_year` selections per
cell. This existing behaviour must be preserved EXACTLY per the
"byte-identical default" constraint, and year_outer mode's IMOGENCFXInput
override (next session) must reproduce it via the deterministic formula
above. Cross-validation strategy adapts: single-cell smoke first
(bypasses cell-ordering complexity); multi-cell smoke second (tests
formula reproduction). Captured in `notes/STEP_17a.md` §5.4 +
`notes/FOLLOWUPS.md` F-12.

#### Updated documents

- `notes/STEP_17a.md` (NEW): per-step verification record covering the
  foundation work + design decision (D1 confirmed) + spinup_year_idx
  finding + remaining-C1 work plan
- `CHANGELOG.md` (this entry)
- `EXECUTION_PLAN.md` V.1 step 17a row: status note "FOUNDATION LANDED"
  added with reference to the foundation commit
- `notes/FOLLOWUPS.md`: status dashboard date refreshed; F-12 entry
  C1 pre-flight findings subsection extended with the spinup_year_idx
  finding pointer
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md`: NEW step-17a-foundation
  entry documenting the 6 file changes; backport-relevance HIGH
  (purely additive; the new code applies cleanly to `trunk_r13078`
  once F-11 Backport Sprint runs); plus backfilled `_TBD_` step-15
  hash `cd68b29` and step-16 hash `572820c` as a free-rigor cleanup
- `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 10 (NEW;
  outside-repo session-state preservation): documents this session's
  C1 foundation work + design decisions + remaining work pointer for
  the next chat session(s)

#### Net source-level change in `lpjguess/`: ~250 LOC across 6 files

All purely additive. The Backport Sprint (F-11) will replicate these
changes mechanically into `trunk_r13078` at end of Phase 1 per the
new step-17a-foundation entry in BACKPORT_LEDGER.md §3.

---

### 2026-05-09 — Path A refinement: skip Option B; staged Option C only (no tag)

Documentation-only commit refining the F-12 plan ahead of any code work,
per user-confirmed Path A discussion 2026-05-09. **No source-level changes;
no new tag.**

#### What changed

After the 2026-05-08 docs maintenance commit (`76aa57b`) which staged
F-12 Options B + C as in-v1.0-scope, today's discussion surfaced that
Options B and C are architecturally orthogonal (not sequential):
- **Option B** (single-process workstation two-process orchestration)
  was framed as a fast stopgap (~2-3 days) but addresses ONLY workstation
  single-process tight, with a per-gridcell-rolling caveat that is less
  rigorous than Option C
- **Option C** (additive `framework_loop_mode = "year_outer"` ins
  parameter; per-year-outer loop alongside the existing per-gridcell-outer)
  resolves F-10 at the root for both single-process AND multi-rank MPI;
  is required regardless for the cluster + tight v1.0 deliverable
- Skipping Option B saves ~2-3 days of effort + a maintenance surface,
  and the C1 sub-milestone delivers the same workstation single-process
  tight capability Option B would have, but more rigorously
  (globally-synchronized per-cell flush vs per-gridcell-rolling)

User confirmed direction 2026-05-09: skip Option B; go straight to Option C
staged as 3 sub-milestones (C1 → C2 → C3). Workstation specs verified
(i9-11900K; 64 GB RAM; 16 cores; Anaconda3 MPICH 4.1.1 + gcc 15.2 +
cmake 3.31.6; ~62 GB single-process production memory pressure means
production is genuinely cluster-only). The new staged plan:

- **C1** (~1 week; workstation single-process year_outer + cross-validation
  against gridcell_outer baseline) → tag `v0.17.0-step17a-c1-year-outer-single-process`
- **C2** (~3-5 days; workstation MPI year_outer via mpirun -np 4 + addresses
  Anaconda3 mpicxx wrapper issue) → tag `v0.17.5-step17b-c2-mpi-sync`
- **C3** (~1-2 weeks SSH iterative; cluster MPI year_outer; refines
  env_owl.sh placeholders against actual `module avail` on owl) →
  tag `v0.18.0-step17c-c3-cluster-tight`

Plus existing step 17 → renumbered as step 17d (end-to-end validation;
now actually runnable for all 4 combinations after C3).

#### Updated documents

- **`notes/FOLLOWUPS.md`** F-12 entry: revised "Recommendation" section
  with the staged Option C plan; new "Cross-validation protocol" subsection
  (the GO/NO-GO gate at C1; tolerances per output category); new "Status
  as of 2026-05-09" subsection; new "What was decided today" subsection
  capturing the 4 user-confirmed decisions (skip Option B; intermediary_py
  copy-over flow stays; native LPJG filenames v1.1+ refinement noted;
  local + cluster equally important). Status dashboard "Last updated" +
  F-10 + F-12 row entries refreshed.
- **`EXECUTION_PLAN.md` V.1**: inserted 3 NEW step rows (17a, 17b, 17c)
  between step 16 and the existing step 17; renumbered existing step 17
  as step 17d (end-to-end validation; now runnable for all 4 combinations
  after C3 lands).
- **`docs/v2_roadmap.md`**: added REVISED 2026-05-09 banners at top of §4
  (Option B sketch — preserved as historical / decision-trail context;
  superseded) + §5 (Option C sketch — now in-v1.0 + staged); body content
  preserved for design reference but readers redirected to FOLLOWUPS F-12
  for the canonical active plan.
- **`_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md`** Part 8 (NEW;
  outside-repo session-state preservation): documents 2026-05-09 session
  decisions + workstation specs + revised plan + commit commands. (Not
  committed; lives in the sibling `_chat_artifacts/` dir per session-1
  Part 14 §C2 recommendation.)

#### Net source-level change in `lpjguess/`: ZERO

Documentation pass before any code work. Backport-irrelevant.

---

## [v0.16.0-step16-cluster-launcher] — 2026-05-08 — step 16: Cluster launcher (loose-only baseline; F-10/F-12 caveats explicit)

### Architectural-tension investigation (the strategic pivot for this step)

The user surfaced a critical architectural insight at session start
(2026-05-08): the F-10 single-process deadlock issue extends to multi-rank
MPI on cluster, not just to single-process tight coupling. Investigation
this session confirmed:

- `lpjguess/framework/parallel.cpp` implements ONLY `MPI_Init` /
  `MPI_Comm_rank` / `MPI_Comm_size` / `MPI_Finalize` — no `MPI_Barrier`,
  no `MPI_Allreduce`, no point-to-point messaging
- The cluster orchestration is gridlist-split embarrassingly-parallel:
  `setup_run_owl_with_scratch_lpj_work.sh` distributes per-rank gridcells
  via `split -a 4 -l <cells/N>` into `runNN/` subdirs; each rank runs
  `guess -parallel` independently
- Cluster + LOOSE coupling works fine (LPJG reads pre-baked engine climate;
  embarrassingly parallel; no synchronization needed)
- Cluster + TIGHT coupling has the same deadlock as single-process tight,
  multiplied by N ranks: each rank's `ImogenOutput::flush_year` fires
  per-rank-per-year; engine cannot consume N independent flux streams at
  a synchronization point that doesn't exist

User-confirmed Path A trajectory (re-sequencing of v1.0 vs v1.1+ scope):

1. **Step 16 (THIS step)**: Cluster launcher for LOOSE mode + workstation
   parallel mimic test
2. **F-12 Option B** (next): Local + tight via two-process; ~2-3 days
3. **F-12 Option C** (after Option B): HPC + tight via additive
   `framework_loop_mode = "year_outer"` + `MPI_Barrier`; ~1-2 weeks +
   cross-validation
4. **Steps 17-19**: validation + docs + CI/release

### Added — `scripts/cluster/` toolkit (7 files; ~50 KB total)

| File | Size | Adapted from | Role |
|---|---:|---|---|
| `run_coupled.sbatch` | ~17 KB / 290 lines | NEW (mirrors `scripts/run_coupled.sh` CLI) | Top-level SLURM launcher; refuses cluster + tight in v1.0 with clear error message |
| `setup_run.sh` | ~11 KB / 200 lines | `setup_run_owl_with_scratch_lpj_work.sh` (174 lines) | Gridlist split + per-rank `runNN/` + generates `submit.sh` + `startguess.sh` |
| `mpi_run_guess.sh` | ~7 KB / 165 lines | `mpi_run_guess_on_tmp.sh` (82 lines) | Per-rank scratch-I/O wrapper; multi-MPI rank detection |
| `finishup_lpj_work.sh` | ~7 KB / 175 lines | `finishup_lpj_work_owl.sh` (172 lines) | Post-run aggregation (concatenate per-rank `*.out`, gzip, copy to `output-YYYY-MM-DD/`) |
| `make_guess.sh` | ~4.5 KB / 130 lines | NEW (lightweight version of IMK-IFU `make_guess.sh` 126-line original) | Cluster-side build helper with `--mpi` flag |
| `append_files.sh` | ~1.7 KB / 40 lines | `append_files.sh` (verbatim with comments) | Per-file aggregator helper |
| `env_owl.sh` | ~3.7 KB / 80 lines | NEW (placeholder template) | Module-load template for `owl` (PLACEHOLDER values; refine via SSH) |
| `README.md` | ~6 KB / 175 lines | NEW | Comprehensive cluster-orchestration narrative |

### Added — Workstation parallel mimic test: `scripts/run_parallel_mimic.sh` (~9 KB / 200 lines)

Validates the cluster orchestration mechanics (gridlist split + per-rank
invocation + output concatenation) WITHOUT requiring SSH access to the
cluster. Uses Anaconda3 MPICH 4.1.1's `mpirun -np N` on the workstation;
runs `guess -parallel -input imogen` against the smoke 4-cell gridlist;
verifies per-rank artifacts. Deferred empirical execution to step 17
(validation), where engine climate library bootstrap will enable
full end-to-end loose-coupling validation.

### Key adaptations from the IMK-IFU originals

1. **Named-flag CLI** (vs positional 12-arg in `setup_run.sh`)
2. **Configurable `INPUTMETHOD`** (default `imogen` for v1.0 loose-only;
   IMK-IFU original was hardcoded `cfx` for forest-productivity)
3. **Multi-MPI rank detection** (MPICH `PMI_RANK` || OpenMPI
   `OMPI_COMM_WORLD_RANK` || SLURM `SLURM_PROCID`); IMK-IFU original
   supported only OpenMPI + SLURM
4. **F-10/F-12 caveat detection inline**: `setup_run.sh` warns on
   `--inputmethod imogencfx`; `run_coupled.sbatch` refuses cluster + tight
   outright (with clear error message + resolution pointer to F-12 Option C)
5. **`$TMP` fallback to `/tmp/$$`** for non-cluster contexts (workstation mimic)
6. **`--workdir-base` override** for non-IMK-IFU clusters

### Updated — `docs/build.md`

Cluster section replaced from placeholder with full step-by-step + F-10/F-12
caveat narrative + cross-references to `scripts/cluster/README.md`.

### Updated — `.gitignore`

Added two new step-16 ignore rules:
- `runs/*/parallel_work/` (workstation parallel mimic per-rank work dirs)
- `lpjguess/build_mpi/` (cluster MPI build dir)

### Net source-level change in `lpjguess/`: ZERO

Step 16 is bash + docs + .gitignore additions only. **Backport-irrelevant**
for the F-11 sprint; the cluster orchestration is fork-agnostic.

### Refs

- `EXECUTION_PLAN.md` V.1 step 16 (cluster integration milestone)
- `EXECUTION_PLAN.md` Decision #7 (single codebase + binary serves both
  workstation and cluster) + Decision #8 (Anaconda3 NetCDF preference is
  workstation-specific; cluster uses module-loaded NetCDF)
- `notes/STEP_16.md` (per-step verification record)
- `notes/FOLLOWUPS.md` F-10 (architectural deadlock; cluster-MPI extension
  documented in F-10 phase-2 sketch lines 343-411) + F-12 (multi-pass /
  two-process design space; Options B + C)
- `docs/scientific_framework.md` §5 (F-10 caveat narrative)
- `docs/v2_roadmap.md` §4 (F-12 Option B; v1.1 single-process tight) + §5
  (F-12 Option C; v1.1+ HPC tight via additive `framework_loop_mode`)
- IMK-IFU originals at `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/`
  (the prior-art cluster orchestration adapted from)
- `lpjguess/parallel_version/aurora.tmpl` (upstream LPJ-GUESS canonical
  SLURM template; cross-reference for the gridlist-split + mpirun pattern)

---

## [v0.15.0-step15-stage1-deferral] — 2026-05-08 — step 15: Stage I documentation preservation + Stage II PLUM-output reuse verification

### Added — `docs/scientific_framework.md` (NEW; ~13 KB)

Per `EXECUTION_PLAN.md` V.1 step 15.a + Decision #9 + working paper §2.4.3.
Canonical scientific-architecture reference for the framework. 7 sections:

1. The four components (LPJ-GUESS, PLUM, Intermediary Controller, IMOGEN)
   with peer-reviewed references (Smith 2014; Alexander 2018; Rabin 2020;
   Huntingford 2010; Smith 2018 FAIR; Nicholls 2020 RCMIP)
2. The two-stage simulation protocol (Stage I + Stage II per working paper
   §2.4.3) with ASCII flowchart
3. Stage II land-use forcing options (Option A in-process Stage I; Option B
   PLUM-harm forLPJG existing outputs; Option C predecessor's concatenated
   1901-2100 LU; v1.0 uses Option C)
4. Decision #10 — `save_state`/`restart` strategy with verbatim example .ins
   blocks from `owl_hpc_cluster_scripts/`
5. The F-10 architectural caveat + v1.0 limitation (loose-coupling fallback
   is scientifically defensible; matches predecessor's working paper)
6. Units integrity (Decision #6) summary table
7. References (10 peer-reviewed citations including IPCC 2019 Vol. 4 AFOLU,
   Winkler 2021 HILDA+, Lindeskog 2013, Olin 2015)

### Added — `docs/v2_roadmap.md` (NEW; ~13 KB)

Per `EXECUTION_PLAN.md` V.1 step 15.c + Decision #9 + Decision #10. The
post-v1.0 development trajectory. 7 sections:

1. Phase 1 vs Phase 2 trajectory (v1.0 → v1.1 → v1.2 → v2.0 ASCII timeline)
2. PLUM embedding (Stage I in v2.0; the Decision #9 v2.0 flip): Stage I
   parameter checklist + 4-step plan
3. v1.1 — wire save_state/restart with PLUM-harm forLPJG outputs (~0.5-1 day
   deliverable that follows v1.0 release): per-phase `imogen_intermediary.ins`
   variants + `--phase historic | scenario | both` launcher flag
4. F-12 Option B (v1.1 Phase 2A) — two-process tight coupling: 6 concrete
   deliverables; verification milestone (4-cell × 11-year SSP1-2.6 smoke run)
5. F-12 Option C (v2.0 Phase 3) — in-process restructure with
   `framework_loop_mode = "year_outer"`; the user's preferred long-term
   approach (per F-10 phase-2 entry); cross-validation protocol
6. Other post-v1.0 stretch items (F-3 Fortran↔C++ parity; F-11 Backport
   Sprint; F-13 paper-stage 3-axis comparison; F-9 climate-input diagnostics;
   F-1 Zenodo upload)
7. v2.0 release criteria

### Added — `notes/STEP_15.md` (NEW; ~12 KB)

Per-step verification record per the standard discipline. 7 sections:
goal, investigation findings, what was implemented, verification,
Backport Sprint relevance (zero `lpjguess/` change → backport-irrelevant),
follow-up cross-reference, effort.

### Verified — PLUM-harm `forLPJG` outputs accessible (item 15.b)

External mount points referenced in `data/DATA.md` §1 verified live:

```text
/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/    (canonical; 17 GB SSP1_RCP26)
├── SSP1_RCP26/   ✓
├── SSP2_RCP45/   ✓
├── SSP3_RCP70/   ✓
├── SSP4_RCP60/   ✓
└── SSP5_RCP85/   ✓

/media/bampoh-d/ISIMIP/inputs/landuse/plum_harm_lu/  (redundant copy on second drive)
└── (same 5-SSP layout)                              ✓
```

Per-scenario `s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/`
sub-tree contains 5 files (~3.5 GB total per scenario):
`landcover.txt`, `cropfractions.txt`, `irrig.txt`, `nfert.txt`,
`landcover_peatland.txt`. Year coverage scenario-only (2021-2100); column
ordering and crop-column count differ from predecessor's concatenated 1901-2100
LU (PASTURE/CROPLAND/NATURAL/BARREN vs NATURAL/CROPLAND/PASTURE/BARREN; 21
crops vs 19 with OilNfix/OilOther split vs Oilcrops merged). Switching
v1.0/v1.1 from Option C (current) to Option B requires either format
conversion or save_state/restart pattern (latter is canonical; deferred to
v1.1 per `docs/v2_roadmap.md` §3).

### Updated — `notes/TRUNK_R13078_BACKPORT_LEDGER.md`

§3 commit-hash errata cleanup (per the prior chat handoff Part 11 §82.3
maintenance follow-up):
- Steps 1-5 hashes corrected (5 stale entries replaced with verified hashes
  via `git rev-list -n 1 <tag>`)
- Steps 9-14 hashes filled in (9 `_TBD_` placeholders replaced)
- New §3 step-15 row added (annotation only; documentation step; zero
  `lpjguess/` change → backport-irrelevant)

| Step | Stale | Verified | Tag |
|---|---|---|---|
| 1 | `dc91efb` | `662f288` | (bundled into v0.2.0-imports) |
| 2 | `9e51a23` | `a93c3ec` | v0.2.0-imports |
| 3 | `5f86bb1` | `fb626c4` | v0.3.0-fortran-allocatable |
| 4 | `f3bb471` | `e80317b` | v0.4.0-imogen-data-fetch-script |
| 5 | `2d36c8e` | `514f089` | v0.5.0-cmip6-converter |
| 9 | `_TBD_` | `d6f4853` | v0.9.0-step9-smoke |
| 9.5 | `_TBD_` | `f00033c` | v0.10.0-step9.5-consumer-wiring |
| 10 | `_TBD_` | `a90e9be` | v0.11.0-step10-intermediary-py-import |
| 11 | `_TBD_` | `e89af1e` | v0.12.0-step11-intermediary-py-validated |
| 13 | `_TBD_` | `aa802e0` | v0.13.0-step13-adapter |
| 14 | `_TBD_` | `ced4b1d` | v0.14.0-step14-launcher |

### Net source-level change in `lpjguess/`: ZERO

Documentation-only step. Net: 4 files added/created (`docs/scientific_framework.md`,
`docs/v2_roadmap.md`, `notes/STEP_15.md`, this CHANGELOG entry); 3 files
modified (`notes/TRUNK_R13078_BACKPORT_LEDGER.md`, `EXECUTION_PLAN.md`,
`notes/FOLLOWUPS.md`).

### Refs

- `EXECUTION_PLAN.md` V.1 step 15
- Decision #9 (Stage I deferred for v1.0); Decision #10 (save_state/restart
  Option D); Decision #3 (LandSyMM_LPJ-GUESS = "integrated LTS" base)
- Working paper §2.4.3 framing
- `docs/scientific_framework.md` (canonical reference going forward)
- `docs/v2_roadmap.md` (post-v1.0 trajectory)
- Prior chat handoff Part 11 §82.3 (BACKPORT_LEDGER errata follow-up)
- `landsymm_runtime_parameters.md` §2 (save_state/restart parameters) + §6
  (do_potyield Stage I parameters) — both already wired in `lpjguess/`

---

## [v0.14.0-step14-launcher] — 2026-05-07 — step 14: workstation launcher + Anaconda3 NetCDF build docs

### Added — `scripts/run_coupled.sh` (~330 LOC bash; production-quality launcher)

Per `EXECUTION_PLAN.md` V.1 step 14 + Appendix A.4 + Decision #8.
One-shot launcher that walks the v1.0 coupled-run pipeline through
7 steps:

1. Build LPJ-GUESS (idempotent; skip if `lpjguess/build/guess` exists)
2. Run intermediary_py if `--backbone intermediary-py`
3. Run Python → LPJG-format adapter if `--backbone intermediary-py`
4. Bootstrap `LPJG_main/IMOGEN/` handshake dir (F-10 deadlock workaround)
5. Clean stale per-year IMOGEN engine output dirs
6. Launch `./guess -input imogencfx main.ins` in scenario's run dir
7. Collect summary + log path

#### Anaconda3 NetCDF auto-detection (Decision #8)

4-tier priority for Anaconda3 NetCDF prefix detection:
1. `--anaconda3-prefix <path>` flag (explicit override)
2. `$CONDA_PREFIX` (active conda env)
3. `$ANACONDA_PREFIX` (set in some shells)
4. `/home/$USER/anaconda3` (common default install location)

If found, CMake invoked with explicit `-DCMAKE_PREFIX_PATH`,
`-DNETCDF_INCLUDE_DIR`, `-DNETCDF_C_LIBRARY` pointing at the conda
env's libs (avoiding the libhdf5_serial / libcurl ABI mismatch that
breaks native-Ubuntu netcdf-dev linking — see `notes/STEP_1.md`).
If not found, prints warning and falls back to bare `cmake ..`.

#### CLI flags + validation

- `--scenario SSP` (default SSP1-2.6)
- `--coupling-mode tight | prescribed | loose` (default prescribed; v1.0
  workaround for F-10 deadlock that blocks tight mode)
- `--backbone static-iiasa | intermediary-py` (default static-iiasa;
  predecessor's reference files for v1.0 minimal-moving-parts)
- `--smoke / --production` (smoke = 4-cell + 1871-1872; production =
  62892-cell + 1900-2100)
- `--no-build / --no-intermediary / --no-adapter` for skipping individual steps
- `--anaconda3-prefix <path>` override
- `-h / --help` (89-line self-documenting help via awk-based extraction)

Each flag validated against its allowed values; invalid value aborts
with actionable error message.

#### F-10 deadlock awareness

When `--coupling-mode tight` or `--production` requested in v1.0, the
launcher prints WARNING explaining the architectural limitation +
recommends the v1.0-functional `prescribed` + `--smoke` defaults.
Phase-2 resolution at F-12 (multi-pass / two-process design).

#### Banner per §I.D.5

Run-start banner displays scenario, coupling-mode, backbone, run-mode,
plus the canonical units conventions (NEE sign, CO2 unit conversion,
CH4/N2O units, year indexing, cell-area assumption). Verbatim match
to EXECUTION_PLAN.md's specified format.

#### Other features

- **Idempotent**: re-runs skip already-completed steps via mtime / file-presence checks
- **Bootstrap helper**: pre-populates `imogen_lpjg.txt` + `done` files
  before engine start (per step 9 §4.4 empirical findings; needed
  until F-12 multi-pass design)
- **Structured logging**: 4 levels (info/warn/error/ok) with ANSI colors
- **Date-stamped log**: `logs/run_coupled_<SCENARIO>_<TS>.log`
- **Trap-based error handler**: actionable error message on any exit

### Added — `docs/build.md` (~150 lines; Anaconda3 NetCDF preference + manual paths)

Comprehensive build documentation covering:
- Quick-start (one-liner via launcher)
- 7-step launcher flow explained
- Why Anaconda3 NetCDF (the libhdf5_serial / libcurl ABI-mismatch
  diagnosis from step 1)
- Manual build instructions (without launcher; for debugging)
- Manual intermediary_py setup (with 7-symlink recipe from step 11)
- Manual adapter run
- How to verify the build succeeds
- Cluster build placeholder (to be filled at step 16)
- Troubleshooting common errors
- Cross-references to relevant STEP_*.md, FOLLOWUPS.md, EXECUTION_PLAN.md

### Modified — `runs/SSP1-2.6/imogen_intermediary.ins` (collateral fix)

Added `param "file_tmin" (str ".../Tmin_anom.dat")` and
`param "file_tmax" (str ".../Tmax_anom.dat")` directives.

**Provenance**: this is a step-9.5 follow-up that step 14's empirical
test surfaced. Step 9.5 wired the consumer side in
`imogencfx.cpp::init()` (`file_tmin = param["file_tmin"].str;` etc.)
but didn't update the example `.ins` file. The launcher's first
end-to-end smoke run on 2026-05-07 hit
`Paramlist::operator[]: parameter "file_tmin" not found` and
revealed the gap. Fix is one block of 2 directives + explanatory
comment referencing step 14 provenance. The C++ engine writes
Tmin_anom.dat / Tmax_anom.dat per step 9.5's climatemodel.cpp
non-REGRID branch; the consumer-side wiring correctly reads them
after this fix.

### Verified

- `scripts/run_coupled.sh --help`: 89 lines self-documenting help
- End-to-end smoke run with `--no-build`: banner displays correctly,
  all 7 steps progress in order, IMOGEN engine produces 30+ year-output
  dirs (1871-1900+), launcher exits cleanly when engine deadlocks at
  F-10 boundary
- Anaconda3 NetCDF auto-detection at `/home/bampoh-d/anaconda3` ✓
- Bootstrap helper creates handshake files ✓
- F-10 deadlock warnings printed for `--coupling-mode tight` and `--production` ✓

### What's NOT verified (gated on F-12)

End-to-end coupled run that gets LPJG main loop to actually fire
(producing `cflux.out`, `mch4.out`, `ngases.out`, etc. in `runs/<SSP>/output/`
+ step 8's writer producing `imogen_lpjg_*.txt` in
`Common-directory/LPJG_main/IMOGEN/`). Architecturally blocked by F-10
in v1.0 single-process imogencfx mode regardless of which launcher
is used. Resolution at F-12 (multi-pass / two-process design;
post-v1.0).

### NET source-level change in `lpjguess/`: ZERO

Launcher is a shell script + docs are markdown + `.ins` fix is
configuration. Backport Sprint (F-11) does NOT need to replicate
any step-14 changes in `trunk_r13078`.

### Files modified / added

```text
Added:
  scripts/run_coupled.sh                ~12 KB / ~330 LOC
  docs/build.md                         ~6 KB / ~150 lines
  notes/STEP_14.md                      ~12 KB

Modified:
  runs/SSP1-2.6/imogen_intermediary.ins +param file_tmin/tmax (step 9.5 collateral)
  .gitignore                            +runs/*/Common-directory/ rule
  notes/FOLLOWUPS.md                    status dashboard date refresh
  notes/TRUNK_R13078_BACKPORT_LEDGER.md +Step 14 entry (zero lpjguess C++)
  EXECUTION_PLAN.md                     step 14 row marked DONE
  CHANGELOG.md                          this entry

NOT committed (gitignored at runtime):
  logs/                                 launcher's date-stamped log files
  runs/*/Common-directory/              IMOGEN engine + LPJG runtime artifacts
```

---

## [v0.13.0-step13-adapter] — 2026-05-07 — step 13: Python Intermediary → Fortran IMOGEN ASCII adapter

(Step 12 was consolidated with step 11; see `[v0.12.0-step11-intermediary-py-validated]`.)

### Added — `tools/imogen_inputs_to_lpjg_format.py` (~270 LOC; production-quality adapter)

Per `EXECUTION_PLAN.md` V.1 step 13 + Appendix A.2 + Decisions #1 (RCMIP
backbone) and #11 (units integrity). Converts intermediary_py's wide-format
`imogen_inputs_<SSP>.csv` (10 columns, Mt-of-gas/yr units) into the four
narrow ASCII files the Fortran IMOGEN engine expects.

#### 4 output files (all in `runs/<SSP>/inputs/`)

| Output file | Format | Maps to ins-parameter | Unit |
|---|---|---|---|
| `imogen_lpjg_flux.txt` | (year, val) | `FILE_LPJG_FLUX` | PgC/yr |
| `imogen_lpjg_ch4_n2o_flux.txt` | (year, ch4, n2o) | `FILE_LPJG_CH4_N2O_FLUX` | TgCH4/yr, TgN2O/yr |
| `co2_anthro_emissions.txt` | (year, val) | `FILE_SCEN_EMITS` | PgC/yr |
| `ch4_n2o_anthro_emissions.txt` | (year, ch4, n2o) | `FILE_CH4_N2O_EMITS` | TgCH4/yr, TgN2O/yr |

#### Unit-checked-adapter discipline

Embodies `EXECUTION_PLAN.md` §I.D.2:
- **Schema validation**: aborts if any of the 10 expected columns are
  missing or NaN-valued
- **Sanity bounds**: per-column min/max range check (e.g.
  `CO2_EFOS_Mt: [-50000, 100000]` Mt/yr — allows for SSP1-2.6's
  negative-emissions late-century BECCS pathway)
- **Year monotonicity**: aborts if Year column has gaps or is non-numeric
- **Conversion constants**: explicit + named:
  - `PgC_TO_MtCO2 = (44/12) * 1000 = 3666.6667` (canonical 44/12 g_CO2/g_C
    × 1000 Mt/Pg ratio)
  - `MtCO2_TO_PgC = 1/3666.6667`
  - CH4/N2O: pass-through (Mt = Tg = 1e12 g; identical SI)
- **Startup banner** prints unit conventions explicitly so the operator
  sees what's happening
- **End-of-run banner** prints the exact `imogen_intermediary.ins` edits
  the user needs to make

#### Output format matches predecessor verbatim

Spot-check: `head -3 runs/SSP1-2.6/inputs/co2_anthro_emissions.txt`:
```
1900 0.487860
1901 0.504180
1902 0.519031
```

Compare with predecessor's `imogen/emiss/CMIP6/Co2/co2_pg_emissions_anthropogenic_historical_ssp126_1850_2100.txt`:
```
1850 0.000000
1851 0.482350
1852 0.957810
```

Same 2-col space-separated structure with 6-decimal precision. Engine
reader at `imogen_lpjg.f:598` parses both formats identically.

#### Unit conversion verified to 6 decimals

intermediary_py CSV row 2 (year 1900) `CO2_EFOS_Mt = 1788.820939`:
- Hand-math: `1788.820939 / 3666.6667 = 0.48786025165581587` PgC
- Adapter writes: `1900 0.487860`
- ✓ matches to 6 decimals

#### SSP1-2.6 negative-emissions verification

Late-century rows from `co2_anthro_emissions.txt`:
```
2099 -1.575525
2100 -1.559659
```

Negative CO2 anthropogenic ~-1.56 PgC/yr in 2099-2100 reflects SSP1-2.6's
BECCS / DACCS pathway — scientifically expected for the deepest-mitigation
scenario.

### Modified — `runs/SSP1-2.6/imogen_intermediary.ins`

Added new "Option B" intermediary_py-driven file-paths block alongside
existing "Option A" (static-IIASA) and "Option C" (relative-path tight-mode):

- **Option A (v1.0 default)**: predecessor's absolute-path static IIASA
  files; F-10-deadlock-compatible
- **Option B (NEW at step 13)**: absolute paths to adapter outputs at
  `runs/SSP1-2.6/inputs/`; same F-10 deadlock behavior as A but with our
  RCMIP-substituted emissions backbone
- **Option C**: relative paths so engine concat resolves to LPJG handshake
  dir; un-testable in v1.0 (deadlocks); resolution at F-12

Option B is preserved as commented-out by default. Users opting into the
intermediary_py-driven backbone uncomment Option B + comment out Option A.

### Modified — `tools/README.md`

Added detailed adapter entry in "Implemented tools" section; removed
corresponding "Planned tools" row.

### Year-range mismatch documented

intermediary_py CSV starts at 1900 (FAOSTAT's earliest); predecessor's
static files start at 1850 (RCMIP/FAIR baseline). Adapter outputs 201
rows (1900-2100). Documented:
- adapter prints "AND adjust year-range params if needed" banner with
  exact `NYR_*=201, YEAR1=1900` instructions
- `--pad-to-year 1850` flag exists for users who want compatibility with
  the engine's default `NYR_*=251` parameters; flagged as
  "compatibility shim only, NOT scientifically defensible" because
  pre-industrial CH4 anthropogenic ~22 TgCH4/yr (not 0)

### What CAN'T be verified in v1.0

End-to-end coupled run with adapter-driven backbone — the F-10
architectural deadlock (from step 9 + 9.5) blocks LPJG main loop in
single-process imogencfx mode regardless of which emissions backbone
(static-IIASA Option A or adapter-driven Option B) is used. The adapter
is **scientifically validated** (correct units, conversions, format, value
ranges); the **integrated coupled run** awaits F-12 (multi-pass /
two-process design).

### NET source-level change in `lpjguess/`: ZERO

Adapter is fork-agnostic Python tooling. Backport Sprint (F-11) does
NOT need to replicate any step-13 changes in `trunk_r13078`.

### Files modified / added

```text
Added:
  tools/imogen_inputs_to_lpjg_format.py     ~10 KB / ~270 LOC (the adapter)
  notes/STEP_13.md                          ~14 KB

Modified:
  tools/README.md                           +"Implemented tools" entry; removed planned row
  runs/SSP1-2.6/imogen_intermediary.ins     +Option B block (commented-out)
  .gitignore                                comment annotation about runs/*/inputs/
  notes/FOLLOWUPS.md                        status dashboard date refresh
  notes/TRUNK_R13078_BACKPORT_LEDGER.md     +Step 13 entry (zero lpjguess C++)
  EXECUTION_PLAN.md                         step 13 row marked DONE
  CHANGELOG.md                              this entry

NOT committed (gitignored):
  runs/SSP1-2.6/inputs/*                    derived from intermediary_py output;
                                            regenerable via the adapter
```

---

## [v0.12.0-step11-intermediary-py-validated] — 2026-05-07 — step 11: pipeline end-to-end + 4 source bugs fixed + reproducibility verified

### Headline outcome

✅ **First end-to-end intermediary_py run succeeded**: 23/23 steps in
540.3s (~9 min); 10/10 pytest pass; **CO2 + all natural CH4/N2O +
all historical columns byte-identically reproduce** version_A's
reference outputs. Anthropogenic scenario CH4/N2O within 0.17-0.22%
mean relative (matches Quick_Start.md's documented "slightly earlier
code revision" provenance).

### Strategic shortcut — version_A's FULL/inputs/ as input source

Per user guidance 2026-05-07, instead of acquiring ~1.8 GB inputs
piecemeal from RCMIP / FAIR / EDGAR / FAOSTAT / PLUM / LPJG, **the
existing version_A `imogen_ghg_controller_FULL/inputs/` directory
(5.1 GB) is symlinked** as our pipeline's input source. Pros: 0 GB
disk overhead; per-subdir granularity; gitignored (no commits).

Symlinks at `intermediary_py/imogen_ghg_controller/inputs/<subdir>`
for: edgar/, fao/, fair_erf/, lpjg/, plum/, rcmip/, reference_pdfs/.

### Fixed — 4 source-level bugs in the imported intermediary_py

These bugs all manifested during the first end-to-end pipeline run.
All fixes are localized + small + improve robustness for any user
running the pipeline:

#### Bug 1 — `paths.py::ensure_output_dirs()` only created level-2 dirs

**Symptom**: `OSError: Cannot save file into a non-existent directory:
'.../outputs/component_a/data/ch4_ef'` on first script.

**Diagnosis**: `ensure_output_dirs()` created the level-2 dirs (data/,
figures/, summaries/) but not the per-sector level-3 sub-subdirs
(data/ch4_ef, ..., data/scenario_pipeline + figures/ analogs).

**Fix** (per user request for self-contained pipeline behavior):
- Extended `ensure_output_dirs()` to enumerate all 14 level-3
  sub-subdirs under Component A's data/ + figures/
- Added auto-call at module-bottom of `paths.py`:
  `if os.environ.get('IMOGEN_GHG_NO_AUTO_MKDIR') != '1':
       ensure_output_dirs()`
- Idempotent (`mkdir(parents=True, exist_ok=True)`); safe whether
  dirs are pre-created manually or not
- Gated by `IMOGEN_GHG_NO_AUTO_MKDIR=1` env var for read-only
  inspection tools that want to import paths without filesystem
  side effects
- **Verified**: deleting all output subdirs and importing
  `src.shared.paths` reconstructs all 28 dirs in one call

#### Bug 2 — `os` not imported in 3 scenario scripts

**Symptom**: `NameError: name 'os' is not defined` at
`01_scenario_ch4_ef_processing.py:44`.

**Diagnosis**: 3 scripts use `os.makedirs(SCEN_DIR, exist_ok=True)`
without `import os`. Python 3.10+ may transitively expose `os` via
sys imports in some environments; on Python 3.9.x (the user's
anaconda3 default) it fails.

**Fix**: added `import os` to:
- `src/component_a_anthropogenic/scenarios/01_scenario_ch4_ef_processing.py`
- `src/component_a_anthropogenic/scenarios/02_scenario_ch4_mm_processing.py`
- `src/component_a_anthropogenic/scenarios/03_scenario_n2o_mm_processing.py`

#### Bug 3 — `FAOCountry` column reference (stale; should be `Country`)

**Symptom**: `KeyError: 'FAOCountry'` at
`01_scenario_ch4_ef_processing.py:187`.

**Diagnosis**: Script reads `missing['FAOCountry']` from
`fao2020_missing_species.csv` — but that CSV is written with column
`Country`, not `FAOCountry`. Documented in Quick_Start.md's "1-row
diff" discussion ("the reference outputs the user provided are from
a slightly earlier code revision").

**Fix**: `missing['FAOCountry']` → `missing['Country']` (single
occurrence across the codebase). Aligns with canonical-current
behavior; matches version_A's reference outputs (which also use
`Country`).

#### Bug 4 — `rcmip_substitution_processing.py` writes to source dir

**Symptom**: `FileNotFoundError:
'.../outputs/component_a/data/rcmip_substitution_ch4.csv'` when
Component C tries to read it.

**Diagnosis**: lines 376-377 used `df.to_csv(os.path.join(HERE, ...))`
where `HERE = os.path.dirname(os.path.abspath(__file__))` — i.e.,
writing into the script's own `src/` directory, not into
`outputs/component_a/data/`. This explained why version_A's tree had
the rcmip_substitution_*.csv files in BOTH locations: the script
wrote into `src/` (the bug), and someone manually copied them to
`outputs/` (the workaround).

**Fix**: both `to_csv(os.path.join(HERE, ...))` calls changed to
`to_csv(os.path.join(str(OUT_A_DATA), ...))`. Producer-consumer
chain now works directly without manual copying.

### Fixed — `openpyxl` missing from requirements (bug C33)

Added `openpyxl>=3.0` to BOTH `requirements.txt` (with explanatory
comment) and `pyproject.toml`'s `dependencies` list. Future fresh
installs via `pip install -r requirements.txt` will pull openpyxl
correctly. (Did not actually crash on this host since system Python
already had it installed.)

### Verified

```text
# Pipeline run
$ python3 run_all.py --skip-plots
  ✓ 23/23 steps in 540.3s

# Pytest
$ python3 -m pytest tests/ -v
  ✓ 10/10 passed (test_imogen_export_schema, test_unit_conversions, test_co2_option_a_validation)

# Reproducibility (vs version_A FULL/outputs/imogen_inputs_SSP1-2.6.csv)
  Historical 1900-2019: ALL 9 columns BYTE-IDENTICAL
  Scenarios 2020-2100:
    CO2_EFOS_Mt, CO2_NEE_Mt, CO2_total_Mt:           BYTE-IDENTICAL
    CH4_natural_Mt, N2O_natural_Mt:                  BYTE-IDENTICAL
    CH4_anthro_Mt, N2O_anthro_Mt, CH4_total_Mt, N2O_total_Mt:
        max abs diff 0.602 / 0.029 Mt; mean 0.17-0.22% rel drift
        (matches Quick_Start.md "slightly earlier code revision")
```

### Files modified / added

```text
Added:
  notes/STEP_11.md                                                          ~14 KB

Modified (in intermediary_py — 4 bug fixes + 1 infra + 1 dep declaration):
  intermediary_py/imogen_ghg_controller/src/shared/paths.py                 +60 LOC (auto-create on import)
  intermediary_py/imogen_ghg_controller/src/component_a_anthropogenic/
    rcmip_substitution/rcmip_substitution_processing.py                     +12 LOC (HERE -> OUT_A_DATA)
    scenarios/01_scenario_ch4_ef_processing.py                              +8 LOC (import os; FAOCountry->Country)
    scenarios/02_scenario_ch4_mm_processing.py                              +1 LOC (import os)
    scenarios/03_scenario_n2o_mm_processing.py                              +1 LOC (import os)
  intermediary_py/imogen_ghg_controller/run_all.py                          +7 LOC (comment about auto-create)
  intermediary_py/imogen_ghg_controller/requirements.txt                    +4 LOC (openpyxl)
  intermediary_py/imogen_ghg_controller/pyproject.toml                      +2 LOC (openpyxl)

Modified (in lpjguess infra):
  .gitignore                                                                +10 LOC (intermediary_py/inputs/outputs)

Modified (in docs):
  notes/FOLLOWUPS.md                                                        status dashboard refresh
  notes/TRUNK_R13078_BACKPORT_LEDGER.md                                     +Step 11 entry (zero lpjguess C++)
  EXECUTION_PLAN.md                                                         step 11 row marked DONE
  CHANGELOG.md                                                              this entry

NOT committed (local-only):
  intermediary_py/imogen_ghg_controller/inputs/{edgar,fao,...}/             7 symlinks to version_A/.../FULL/inputs/
  intermediary_py/imogen_ghg_controller/outputs/                            generated; regenerable via run_all.py

Reverted:
  intermediary_py/imogen_ghg_controller/src/component_a_anthropogenic/
    rcmip_substitution/rcmip_substitution_{ch4,n2o}.csv                     reverted to step-10 state (the buggy
                                                                            script had over-written them; fixed
                                                                            script no longer touches them)
```

### NET source-level change in `lpjguess/`: ZERO

intermediary_py is fork-agnostic. Step 11's bug fixes live entirely
in the Python pipeline. The Backport Sprint (F-11) does NOT need
to replicate any step-11 changes in `trunk_r13078`.

---

## [v0.11.0-step10-intermediary-py-import] — 2026-05-07 — step 10: import imogen_ghg_controller v0.1.0

### Added — `intermediary_py/imogen_ghg_controller/` (7.9 MB; 78 files)

Per `EXECUTION_PLAN.md` V.1 step 10. The user's Python pipeline
`imogen_ghg_controller v0.1.0` (replacing the predecessor's legacy
C++ `Intermediary/Code/`, 272 KB, half-built) is now imported as the
canonical anthropogenic-emissions backbone for v1.0.

#### Source provenance

- Imported from `version_A/Intermediary_py/imogen_ghg_controller_SOURCE_ONLY/imogen_ghg_controller/`
- Verified byte-identical to version_B's SOURCE_ONLY (excluding figures/inputs/outputs/archive)
- 7.9 MB total: 59 Python source + 3 pytest tests + 16 docs/config files
- Excludes `inputs/` (Tier-3 ~1.8 GB; Tier-3 acquisition recipe in `data/DATA.md`)
- Excludes `outputs/` (generated; not committed)
- Excludes `archive/`, `__pycache__`, `*.pyc` (transient)
- Exception: 3 README.md placeholders kept inside excluded dirs for
  acquisition-instruction tracking

#### Pipeline architecture (43 steps × 4 components)

| Component | Role | Steps |
|---|---|---|
| **A** Anthropogenic | IPCC Tier-1 (CH4 EF/MM/rice; N2O MM/MS/syn-fert) × FAO/EDGAR/PLUM × RCMIP substitution | 28 |
| **B** Natural | LPJG `.gz` streaming + GMB IFW/DCC corrections | 5 |
| **C** Integration | A + B + 3 comparators (conventional/hybrid/external) | 9 |
| **D** IMOGEN export | Per-scenario wide + combined long format CSVs | 1 |

Final 6 IMOGEN-input deliverables at `outputs/imogen_inputs/`:
- 5 per-scenario wide CSVs (SSP1-1.9 / SSP1-2.6 / SSP2-4.5 / SSP3-7.0 / SSP5-8.5)
- 1 combined long-format CSV
- Format: 201 rows × 10 columns; **units: Mt-of-gas/yr**

#### Anthropogenic substitution backbone (Decision #1)

```
New_total = RCMIP_total − RCMIP_agri + Our_agri
```

Already implemented in `src/component_a_anthropogenic/rcmip_substitution/`.
Pre-validated: 38/38 reference data files byte-identical to canonical
scripts (per `Quick_Start.md`'s provenance check).

#### Verified

```bash
$ python3 run_all.py --dry-run
══ pipeline complete: 43/43 steps in 0.0s ══
```

✅ All 43 steps register cleanly (Component A: 28; B: 5; C: 9; D: 1).
No missing-imports errors. Ready for end-to-end execution at step 11
once Tier-3 input data is acquired.

#### Deferred (gated on later steps)

- Live pipeline execution + IMOGEN-input file generation: needs
  ~1.8 GB Tier-3 input data; **step 11** owns acquisition
- Adapter to convert intermediary_py's 6 CSVs into the 4 narrow
  IMOGEN-readable files: **step 13** owns the adapter
- Integration into `runs/SSP1-2.6/imogen_intermediary.ins`: **step 13**
  + post-F-12 (because F-10 deadlock blocks end-to-end coupled run anyway)
- Full pytest run: needs populated `outputs/`; **step 11**

### Documented — deferred-items master dashboard in `notes/FOLLOWUPS.md`

Per user code-discipline request 2026-05-07. Added a status dashboard
at the top of FOLLOWUPS.md showing all OPEN items with best-timing
columns + a "blocks step 17?" flag. Tracking discipline committed:

1. Update dashboard at end of every step that touches FOLLOWUPS.md
2. Hard sweep at start of step 17
3. Final review at end of Phase 1 via the Backport Sprint (F-11)

### Files modified / added

```text
Added:
  intermediary_py/imogen_ghg_controller/    7.9 MB / 78 files
  notes/STEP_10.md                          ~13 KB

Modified:
  intermediary_py/README.md                 imported-status update
  notes/FOLLOWUPS.md                        +Status dashboard at top + tracking discipline
  notes/TRUNK_R13078_BACKPORT_LEDGER.md     +Step 10 entry (zero lpjguess C++ touched)
  EXECUTION_PLAN.md                         step 10 row marked DONE
  CHANGELOG.md                              this entry
```

---

## [v0.10.0-step9.5-consumer-wiring] — 2026-05-07 — step 9.5: LPJG-side consumer wiring + BLAZE check + C++ engine Tmin/Tmax (PARTIAL)

### Added — LPJG-side consumer wiring for IMOGEN engine's Rh/Wind/Tmin/Tmax outputs

Per `EXECUTION_PLAN.md` V.1 step 9.5 + Decisions #11 (Tmin/Tmax) and #12
(Rh/W output asymmetry). Step 9.5 is **partial** with significant scope
refinement (see "Scope refinement" below).

#### `lpjguess/modules/imogencfx.h` — header additions

- Per-day `dtmin[Date::MAX_YEAR_LENGTH]` and `dtmax[Date::MAX_YEAR_LENGTH]` arrays
- `xtring file_tmin` and `xtring file_tmax` ins-parameter paths
- `std::vector< std::vector< std::vector<double> > > all_dtmin` and `all_dtmax` storage

(`drelhum`, `dwind`, `file_relhum`, `file_wind`, `all_drelhum`, `all_dwind`
were already in the header from prior integration-project work — only the
`*tmin` / `*tmax` analogs needed adding.)

#### `lpjguess/modules/imogencfx.cpp` — 5 wiring blocks

- **`init()` param reads**: `param["file_relhum"]`, `param["file_wind"]`,
  `param["file_tmin"]`, `param["file_tmax"]` — 4 new ins-file consumed parameters
- **`init()` resize block**: `resize3DimVector(all_drelhum, ...)`, `all_dwind`,
  `all_dtmin`, `all_dtmax` storage allocation
- **`read_climate_for_year()`**: 4 new `read_lines_from_file()` calls (each
  with empty-path guard so missing-file cases are graceful no-ops)
- **`get_climate_for_gridcell()`**: BLAZE compatibility check **RESTORED**
  with empty-path safety (actionable error message); monthly→daily
  interpolation block for the 4 new climate variables (uses
  `interp_monthly_means_conserve` mirroring existing `interp_climate`
  pattern); daily-mode passthrough block for the 4 new variables
- **`getclimate()`**: `climate.relhum = drelhum[date.day]; climate.u10 =
  dwind[date.day]; climate.tmin = dtmin[date.day]; climate.tmax = dtmax[date.day];`
  — mirrors `cfxinput.cpp:1940-1945`

### Restored — BLAZE compatibility check at `imogencfx.cpp:803-804`

Was commented out in the predecessor framework (per `[CMI §1.2]` break-point).
Step 9 left it commented because Rh+wind weren't yet wired (uncommenting
would have caused all coupled runs with `firemodel=BLAZE` to fail). After
step 9.5's wiring of `file_relhum`/`file_wind` (above), BLAZE can run safely
PROVIDED the user supplies the corresponding IMOGEN engine output paths in
the ins file. The check is now **active** and produces an actionable error
message:

```cpp
fail("imogencfx with firemodel=BLAZE requires file_relhum + file_wind ins
      parameters pointing at the IMOGEN engine's Rh_anom.dat / W_anom.dat
      per-year output. None set; aborting. (See runs/SSP1-2.6/imogen_intermediary.ins
      for the canonical ins-file layout.)");
```

### Added — `lpjguess/modules/climatemodel.cpp` Tmin/Tmax write block

In the non-REGRID native-grid output branch (lines ~880-958):
- `file100, file101` ofstream declarations
- Open at `iyear == year1`: `Tmin_anom.dat`, `Tmax_anom.dat`
- Per-gridpoint lon/lat headers + per-month-per-day data writes:
  `Tmin = tOutM[..] − dtempOutM[..]/2` (deg C)
  `Tmax = tOutM[..] + dtempOutM[..]/2` (deg C)
- Per-gridpoint newlines + close at `iyear == iyend`

**TODO at step 9.5b**: replicate in the REGRID branch (smoke uses `REGRID=0`
so non-REGRID is sufficient for v1.0).

### Scope refinement (deferred items)

Two items in the original step 9.5 plan were **deferred** after Phase A
investigation surfaced unanticipated infrastructure dependencies:

#### (a) Fortran Rh/W writer port — DEFERRED to step 9.5b

The original plan (Decision #12) assumed the Fortran engine *computed*
Rh/wind but didn't *write* them — i.e., a writer-only port (~20 LOC).
Investigation revealed the Fortran engine **doesn't compute these
variables at all**: the C++ port added the entire computation pipeline
(per `[CMI §4.3.4a]`). Real Fortran port = adding ~70-100 LOC of
Fortran physics work. Beyond step 9.5's 1-day budget; deferred to a
focused step 9.5b session.

Item (b) Fortran Tmin/Tmax depends on (a)'s computation infrastructure;
also deferred to step 9.5b.

#### (e) F-9 closure — REFINED, kept open

`MiscOutput`'s 12 climate-input diagnostic stubs (`out_t_anom`, `out_p_anom`,
etc.) need both `create_output_table()` calls in `define_output_tables()`
AND per-gridcell `outlimit()` calls in `outannual()`. The latter has no
data source: `Climate` has only single-day fields and 20-year-window
aggregates — **no per-month accumulator array**. The original step 9.5
plan assumed `gridcell.climate.mtemp[m]` was accessible; it's not (only
the single-value `mtemp` "mean of last 31 days" exists).

F-9's `notes/FOLLOWUPS.md` entry refined with two paths to closure:
- **Option A** (recommended; ~50 LOC): add per-month accumulator arrays
  to `Climate` (e.g., `mclimate_temp[12]`, `mclimate_prec[12]`, ...)
- **Option B** (~15 LOC): cross-module getter from `IMOGENCFXInput::dtemp[]`

Deferred to a focused step 9.5c (or merged with the F-12 sprint).

### Verification

```text
Build: clean (no warnings on new code; pre-existing fortify-source
       warnings unchanged)
Tests: 162/162 still pass
End-to-end smoke: NOT POSSIBLE in v1.0 — F-10 deadlock (per step 9 §4.4)
                  blocks LPJG main loop; new wiring is code-correct,
                  build-verified, but un-firable until F-12 lands
What CAN be verified in next smoke: 64 new files (Tmin_anom.dat +
                  Tmax_anom.dat × 32 engine years) in
                  Common-directory/IMOGEN/output/<YYYY>/
```

### Files modified

```text
Modified:
  lpjguess/modules/imogencfx.h           +9 LOC (3 blocks)
  lpjguess/modules/imogencfx.cpp         +80 LOC (5 spots)
  lpjguess/modules/climatemodel.cpp      +25 LOC (non-REGRID Tmin/Tmax block)
  notes/FOLLOWUPS.md                     F-9 refined with infrastructure blocker
  notes/TRUNK_R13078_BACKPORT_LEDGER.md  +Step 9.5 entry
  EXECUTION_PLAN.md                      step 9.5 row marked PARTIAL
  CHANGELOG.md                           this entry

Added:
  notes/STEP_9.5.md                      ~12 KB
```

---

## [v0.9.0-step9-smoke] — 2026-05-07 — step 9: SSP1-2.6 run-config + bug fixes + empirical F-10 confirmation

### Added — `runs/SSP1-2.6/` directory (first per-scenario run setup)

Per `EXECUTION_PLAN.md` V.1 step 9 + per user guidance 2026-05-07
to bring in the predecessor's legacy SSP1_RCP26 land-use data:

- **`runs/SSP1-2.6/main.ins`** (~6 KB, NEW): LPJG entry point.
  Imports `global.ins`, `crop_n.ins`, `wetlandpfts.ins`,
  `imogen_intermediary.ins`. Smoke overrides for spinup (100y vs
  500y production), `freenyears` (50y vs 100y production),
  `firemodel="NOFIRE"` (avoiding BLAZE wind/RH dependency until
  step 9.5), `npatch=1` (vs production 25), `run_landcover=1`
  (per user guidance), and year-range params 1871-1872.
- **`runs/SSP1-2.6/imogen_intermediary.ins`** (~14 KB, NEW): IMOGEN-
  coupling parameters. Embodies the bug fixes documented below.
  Default `coupling_mode="prescribed"` (the only v1.0 mode that
  doesn't deadlock immediately; see "Empirical F-10 confirmation").
- **`runs/SSP1-2.6/README.md`** (~6 KB, NEW): scenario metadata,
  how-to-run instructions including the bootstrap-handshake setup,
  empirical F-10 findings, production setup overrides.
- **11 stand/PFT/landcover ins files** (copied from version_A's
  `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/` predecessor):
  global, global_soiln, crop, crop_n, crop_n_pftlist, crop_n_stlist
  (3 variants), pasture_n_stlist (2 variants), landcover, wetlandpfts.
  Stale `/home/bampoh-d/Desktop/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/...`
  paths in `crop.ins` and `landcover.ins` retargeted to version_A's
  actual tree at
  `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/.../version_A/.../Data/LU/...`.

### Added — `imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp126.txt`

3.5 KB file (251 rows, 1850-2100). Was MISSING from our tree at step 6
(other 4 SSPs ssp245/ssp370/ssp460/ssp585 were imported; only SSP126
was overlooked). Imported from version_B at step 9 to fix the smoke
crash `Invalid data format in file: ../../imogen/emiss/RF_NONCO2_GHG_IS92A.dat`
(which had only 243 rows starting at 1859, mismatched with `NYR_NON_CO2=251`).

### Fixed — bug C5 (`ouput` typo) and bug R-anom (filename mismatch)

Both fixed in `runs/SSP1-2.6/imogen_intermediary.ins`:

- **C5**: 8 climate-input file paths (`file_temp`, `file_prec`,
  `file_insol`, `file_wetdays`, `file_dtr`, `file_co2`, `file_wind`,
  `file_relhum`) corrected from `./IMOGEN/ouput/YYYY/...` to
  `./IMOGEN/output/YYYY/...`. **PROVEN**: the smoke run produced 32
  per-year directories at `Common-directory/IMOGEN/output/<YYYY>/`,
  not `ouput/`.
- **R-anom → Rh_anom**: `file_relhum` corrected from `R_anom.dat` to
  `Rh_anom.dat` to match the C++ engine's actual writer output.
  **PROVEN**: the engine emitted `Rh_anom.dat` files in each per-year
  directory; matches our path.

### Documented — bug C35 fix attempted but un-testable in v1.0

The relative-path C35 fix (`FILE_LPJG_FLUX "imogen_lpjg_flux.txt"`)
is correct in concept and in the .ins file (commented out with
extensive documentation). However, the v1.0 single-process mode
**deadlocks immediately** with relative paths because the file
doesn't exist (LPJG hasn't written it yet); the polling loop's
`RUNFLUX_EXIST=0` flag prevents progress. The active configuration
is `coupling_mode="prescribed"` with absolute-path static IIASA
reference files (predecessor's "bug C35" mechanic, intentionally
preserved as the only v1.0-functional configuration). Real C35
testing is gated on follow-up F-12.

### Documented — F-10 architectural deadlock empirically confirmed

Step 9's smoke test **definitively confirmed F-10's predicted
architectural deadlock** in v1.0 single-process imogencfx mode:

- IMOGEN engine ran successfully for 32 years (1871-1902, 320 climate
  output files in 3 minutes), then deadlocked polling for year 1903's
  `done` file
- LPJG main loop NEVER reached because `imogencfx::init()` never
  returned (engine still in outer `KEEPRUNNING` loop)
- Step 8's writer NEVER fired (no `imogen_lpjg_flux.txt` or
  `imogen_lpjg_ch4_n2o_flux.txt` produced in `Common-directory/LPJG_main/IMOGEN/`)
- The deadlock occurs in BOTH `coupling_mode="tight"` (immediate, with
  relative paths) and `coupling_mode="prescribed"` (delayed, after
  ~32 years using bootstrap+absolute paths)

**This formally explains why the predecessor "never ran end-to-end"
([CMI §1.1]).** The predecessor's apparent functionality was an
artifact of the polling loop being neutered (bugs C2/C3 — fixed at
step 7); restoring correct polling-loop semantics surfaced the
underlying architectural deadlock that was always there.

### Added — follow-up F-12 (multi-pass / two-process verification design)

`notes/FOLLOWUPS.md`. The proper resolution of the F-10 deadlock for
v1.0 production runs. Recommended approach: **Option B (two-process)**
— split the `imogen_lpjg` engine binary out of `imogencfx::init()`
into a separate concurrent Fortran process. This is what the
predecessor's polling-loop architecture was originally DESIGNED for;
the in-process port (`climatemodel.cpp::RUN_IMOGEN_ENGINE`) was a
convenience wrapper that broke this design. Estimated effort: 2-3 days.
Option C (in-process restructure per F-10 Phase-2) for v2.0+.

### Added (then removed) — `imogen_nee_perturbation_factor` runtime parameter

Per V.1 step-9's verification milestone (NEE 2x → CO2 trajectory shift),
a runtime ins parameter `imogen_nee_perturbation_factor` was added at
step 9 (parameters.h, parameters.cpp, imogencfx.cpp declare_parameter,
imogenoutput.cpp consumer). Then REMOVED at step 9's wrap-up because
the smoke test empirically confirmed F-10's deadlock means LPJG main
loop never runs in v1.0 — so the perturbation factor cannot affect
anything observable. Per user code-integrity preference, the perturbation
parameter is NOT permanent in lpjguess. Resolution will be designed at
follow-up F-12. **Net source-level changes after step 9 wrap-up: zero**
(only annotation comments referencing the add-then-remove decision).

### Verification

```text
Build: clean
Tests: 162/162 pass
Smoke: 32 years climate output (1871-1902); deadlock at year 1903 polling
  - Engine: read all inputs (CRUNCEP, GCM patterns, emissions, fluxes)
  - Engine: produced 320 climate output files (sized correctly)
  - LPJG: did NOT enter main loop (F-10 deadlock confirmed)
  - Step 8 writer: did NOT fire (gated on F-12)
```

### Files modified / added

```text
Added:
  runs/SSP1-2.6/main.ins                                   ~6 KB
  runs/SSP1-2.6/imogen_intermediary.ins                    ~14 KB
  runs/SSP1-2.6/README.md                                  ~6 KB
  runs/SSP1-2.6/{global, crop, landcover, ...}.ins         ~78 KB across 11 files
  imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp126.txt   3.5 KB
  notes/STEP_9.md                                          ~14 KB

Modified:
  notes/FOLLOWUPS.md                                       +F-12 (~80 lines)
  lpjguess/framework/parameters.h                          comment-only annotation
  lpjguess/framework/parameters.cpp                        comment-only annotation
  lpjguess/modules/imogencfx.cpp                           comment-only annotation
  lpjguess/modules/imogenoutput.cpp                        comment-only annotation
  notes/TRUNK_R13078_BACKPORT_LEDGER.md                    +Step 9 entry
  CHANGELOG.md                                             this entry
  EXECUTION_PLAN.md                                        V.1 step 9 row marked PARTIAL
```

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
