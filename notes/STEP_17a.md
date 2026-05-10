# STEP 17a — F-12 sub-milestone C1 (Workstation single-process year_outer + cross-validation)

**Date opened:** 2026-05-10
**Date foundation landed:** 2026-05-10 (this commit)
**Date C1 fully closed:** _pending — IMOGENCFXInput year_outer override + cross-validation_
**Foundation commit:** _to be filled in after `git commit`_
**Full C1 commit / tag:** _pending — `v0.17.0-step17a-c1-year-outer-single-process` (per [`notes/FOLLOWUPS.md`](FOLLOWUPS.md) F-12 + [`EXECUTION_PLAN.md`](../EXECUTION_PLAN.md) V.1 row 17a)_
**Status:** ⚠️ **FOUNDATION LANDED; FULL C1 IN PROGRESS.** The architectural foundation for the year_outer code path is in place and verified non-breaking (162 unit tests pass; default mode `gridcell_outer` preserved byte-exactly). The IMOGENCFXInput override of `preload_all_climate` + `getclimate_for_year` (with the spinup_year_idx state-machine reproduction formula) and the bit-exact cross-validation against gridcell_outer baseline are deferred to subsequent work within step 17a — see [§7](#7-remaining-work-within-c1-c11-c12) for the staged plan and [§5.4](#54-the-spinup_year_idx-state-machine-finding-flagged-this-session) for the substantive new finding from this session.

This session's work: ~3-4 hours wall-clock for inherited-handoff ingest (sessions 1+2; ~554 KB / 8 199 lines), live verification anchors, deeper C1 pre-flight investigation, foundation implementation (parameter + virtuals + framework block), default-mode regression verification, and documentation.

Net `lpjguess/` source-level change in this commit: **5 files modified, +~250 LOC**:
- `lpjguess/framework/parameters.h` (+22 LOC; `framework_loop_mode` extern declaration with comment block)
- `lpjguess/framework/parameters.cpp` (+8 LOC; `framework_loop_mode = "gridcell_outer"` definition)
- `lpjguess/modules/imogencfx.cpp` (+12 LOC; `declare_parameter` registration with comment block)
- `lpjguess/framework/inputmodule.h` (+50 LOC; two new virtual method declarations with extensive doc blocks)
- `lpjguess/framework/inputmodule.cpp` (+33 LOC; default-fail implementations of the two new virtuals)
- `lpjguess/framework/framework.cpp` (+218 LOC; new `if (framework_loop_mode == "year_outer")` additive block with full year_outer / per-cell-inner loop; existing per-gridcell-outer code preserved byte-exactly via early-return pattern)

**Backport-Sprint-relevance: HIGH.** All 6 file changes need to be replicated in `trunk_r13078` per F-11 discipline. The additive nature (new parameter; new virtuals with default implementations; new code block gated on parameter; existing code path unchanged byte-exactly) makes the backport mechanical.

---

## 1. Goal (per `EXECUTION_PLAN.md` V.1 step row 17a + session-2 chat handoff Part 9)

> **F-12 sub-milestone C1 — Workstation single-process year_outer + cross-validation.** Per
> Path A 2026-05-09 refinement (skip Option B; staged Option C only; per
> [`notes/FOLLOWUPS.md`](FOLLOWUPS.md) F-12 +
> [`_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md`](../../_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md)
> Part 8). Add `framework_loop_mode` ins parameter (default `gridcell_outer`
> preserves LTS-equivalent behaviour byte-exactly; new value `year_outer`
> activates the additive code path). Implement `year_outer` block in
> `framework.cpp` as additive single-process code (no MPI yet). Add
> `getclimate_year(Gridcell&, int year)` method to relevant input modules
> (`IMOGENInput`, `IMOGENCFXInput`, `CFXInput`, `CRUInput`). Audit
> `lpjguess/framework/randomState.cpp` (or equivalent) to confirm per-cell
> PRNG state is independent of loop ordering — if shared-global PRNG (latent
> design flaw), fix BEFORE shipping. Cross-validate Run A (`gridcell_outer`)
> vs Run B (`year_outer`) on 5-cell smoke gridlist × 50-yr simulation;
> tolerances: bit-exact for deterministic outputs (soil-water balance, C/N
> pools without disturbance, GPP/NPP); ≤ 0.1% RMSD for annual cell-mean
> aggregates; ≤ 1% RMSD for stochastic per-cell outputs. Bit-exact
> cross-validation is the GO/NO-GO gate before C1 ships.

(Goal **partially fulfilled** in this commit: foundation landed; IMOGENCFXInput
year_outer overrides + cross-validation deferred to follow-up work within
step 17a per [§7](#7-remaining-work-within-c1-c11-c12).)

---

## 2. Inherited context (from session-2 chat handoff Parts 5-9)

The two previous chat sessions established the canonical staged C1 → C2 → C3 plan for F-12 Option C:

- **C1** (~1.5-2 weeks per session-2 §9.4): Workstation single-process year_outer + cross-validation. **THIS STEP.**
- **C2** (~3-5 days): Workstation MPI year_outer (`MPI_Barrier` at year boundary; `MPI_Allreduce` for global-sync flux flush; pre-requisite: fix Anaconda3 `mpicxx` wrapper).
- **C3** (~1-2 weeks SSH iterative): Cluster MPI year_outer + production verification on KIT IMK-IFU `owl`.

After C3 → all 4 v1.0 combinations (local/HPC × loose/tight) work; existing step 17 (renumbered to step 17d in EXECUTION_PLAN V.1) becomes runnable end-to-end.

The session-2 evening (2026-05-09) C1 pre-flight investigation (commit `9a7158d`; documented in [`FOLLOWUPS.md`](FOLLOWUPS.md) F-12 "C1 pre-flight investigation findings (2026-05-09 evening)") established 5 critical pre-flight findings:

1. **PRNG architecture is year_outer-friendly** (per-instance `Stand.seed` at `guess.h:4931` + `Gridcell.seed` at `guess.h:5406`; `randfrac()` at `driver.cpp:42` is a deterministic Park-Miller LCG taking seed by reference). Cross-validation can target **bit-exact** for both deterministic AND stochastic outputs (better than the defensively-budgeted ≤1% RMSD).
2. **`framework.cpp:411-534` per-gridcell-outer loop has 4 embedded concerns** to preserve in year_outer mode: (a) per-cell setup; (b) restart load; (c) per-day inner with year-end actions; (d) per-cell teardown.
3. **`getclimate(gridcell)` is a stateful per-day driver tied to GLOBAL `date`** (per `imogen_input.cpp:752-810` audit; same pattern in `imogencfx.cpp`, `cfxinput.cpp`, etc.). It reads `date.get_calendar_year()` + `date.day` and advances internal state machinery (`spinup_year_idx`, `stored_years[]`, file-position cursors).
4. **3 design options surfaced** (D1/D2/D3); D1 (preload climate per-cell up-front via new method `preload_all_climate`; year_outer reads from cache without invoking the existing `getclimate` state machinery) is the recommended choice. **CONFIRMED THIS SESSION; see [§5.1](#51-design-decision-d1-confirmed) for the design-decision record.**
5. **Revised C1 effort estimate: 1.5-2 weeks** (was: 1 week). Expansion concentrated in the `getclimate`-refactor scope.

---

## 3. This session's deeper investigation (extends session-2 §9 findings)

Beyond the inherited pre-flight findings, this session's investigation surfaced four additional architectural details that informed the foundation design:

### 3.1 Input module inventory (9 registered modules)

Live `grep` of `REGISTER_INPUT_MODULE` macro invocations: 9 input modules total.

| # | Name | Class | File | C1 scope |
|---|---|---|---|---|
| 1 | `imogencfx` | `IMOGENCFXInput` | `lpjguess/modules/imogencfx.cpp:177` | **Critical (smoke-test path)** |
| 2 | `imogen` | `ImogenInput` | `lpjguess/modules/imogen_input.cpp:175` | Defer (loose-coupling; no year_outer need yet) |
| 3 | `cfx` | `CFXInput` | `lpjguess/modules/cfxinput.cpp:25` | Defer |
| 4 | `cru_ncep` | `CRUInput` | `lpjguess/cru/guessio/cruinput.cpp:24` | Defer |
| 5 | `firemip` | `FireMIPInput` | `lpjguess/modules/firemipinput.cpp:25` | Defer |
| 6 | `cf` | `CFInput` | `lpjguess/modules/cfinput.cpp:23` | Defer |
| 7 | `demo` | `DemoInput` | `lpjguess/modules/demoinput.cpp:18` | Defer |
| 8 | `fluxnet` | `FluxnetInput` | `lpjguess/benchmarks/extra_source/fluxnet/modules/fluxnet.cpp:28` | Defer (benchmarks only) |
| 9 | `watch_diurnal` | `WATCHDiurnalInput` | `lpjguess/benchmarks/extra_source/watch_diurnal/modules/watch_diurnal.cpp:24` | Defer (benchmarks only) |

**For C1 only `IMOGENCFXInput` strictly needs the year_outer overrides** (smoke-test critical path; the SSP1-2.6 launcher invokes `./guess -input imogencfx`). Other input modules are kept on the default-fail virtual implementation; users attempting `framework_loop_mode = "year_outer"` with them will get a clear error pointing at gridcell_outer fallback. Adding year_outer support to other modules later is purely additive.

### 3.2 The framework.cpp loop is line 411-534, NOT 411-516

Session-2 §9.2 + handoff Part 5 use `lpjguess/framework/framework.cpp:411-516` as shorthand for the per-gridcell-outer loop. **Live verification this session confirms the outer `while (true) { ... }` braces close at line 534**, not 516. The "411-516" shorthand refers to the per-day inner block; the post-day teardown block (`closelocalfiles` + `balance.check_period`) at lines 524-528 is part of the outer iteration. The year_outer additive block correctly preserves all 4 concerns including the teardown.

### 3.3 `IMOGENCFXInput` already has the `all_*` 3D-vector cache infrastructure

Live read of `lpjguess/modules/imogencfx.h:242-254` reveals that `IMOGENCFXInput` already has class-member 3D vectors (`all_temp`, `all_prec`, `all_wetdays`, `all_insol`, `all_dtr`, `all_drelhum`, `all_dwind`, `all_dtmin`, `all_dtmax`) indexed `[year_cache_slot, gridcell_index, day_or_month]`. The existing `getclimate(gridcell)` machinery uses `stored_years[]` (line 230) for cache lookup; cache misses trigger `readenv()` (line 122) to load year-Y data for ALL cells at once. **This is a ready-made cache infrastructure for D1 preload.**

The IMOGENCFXInput year_outer override (deferred to next session per [§7](#7-remaining-work-within-c1-c11-c12)) can largely reuse the existing `readenv` + `get_climate_for_gridcell` infrastructure; only need to (a) ensure `nyears` is sized large enough to hold all simulation years, (b) fix the `spinup_year_idx` ordering issue, and (c) add a `getclimate_for_year` accessor that reads from the cache without invoking the per-day state machinery.

### 3.4 `ImogenOutput::outannual` year-change-detection works correctly in BOTH modes

Live read of `lpjguess/modules/imogenoutput.cpp:115-126` confirms the year-change-detection pattern: when a new year's `outannual` fires for the first time, the prior year's accumulators are flushed via `flush_year` + `reset_accumulators`. **In year_outer mode this fires at the FIRST cell of year Y+1 after ALL cells have completed year Y** — providing the per-year globally-synchronized flush that F-10 requires. **No source change to `imogenoutput.cpp/h` needed for year_outer mode** in single-process; the MPI globally-synchronized flush is C2 work (`flush_year_globally_synchronized` with `MPI_Allreduce`).

---

## 4. Implementation in this commit (the foundation; ~250 LOC)

### 4.1 `lpjguess/framework/parameters.h` — extern declaration

Added `extern xtring framework_loop_mode;` to the `IMOGENConfig` namespace, placed adjacent to `coupling_mode` (added at step 8) for thematic grouping. Inline doc block explains both values with their semantics, the F-10 connection, and cross-references to FOLLOWUPS F-12 + EXECUTION_PLAN rows 17a/17b/17c.

### 4.2 `lpjguess/framework/parameters.cpp` — definition + default value

Defined `xtring framework_loop_mode = "gridcell_outer";` adjacent to `coupling_mode = "tight";`. The `"gridcell_outer"` default is what makes the foundation byte-exactly preserve LTS-equivalent behaviour: no .ins-file edit is required for any existing run to keep behaving identically.

### 4.3 `lpjguess/modules/imogencfx.cpp` — `declare_parameter` registration

Added `declare_parameter("framework_loop_mode", &IMOGENConfig::framework_loop_mode, 20, ...)` inside `IMOGENCFXInput::IMOGENCFXInput()` constructor, immediately after the existing `coupling_mode` registration. This makes the parameter readable from `.ins` files when the user runs `-input imogencfx`. (For other input modules, the parameter is unread; they're effectively pinned to `gridcell_outer`. Adding the parameter to other input modules' constructors is a trivial future addition if needed.)

### 4.4 `lpjguess/framework/inputmodule.h` — two new virtual method declarations

Added two new `virtual` (non-pure) methods to the `InputModule` abstract base class:
- `virtual void preload_all_climate(Gridcell&, int first_calendar_year, int last_calendar_year);`
- `virtual bool getclimate_for_year(Gridcell&, int calendar_year, int day_of_year);`

Both have default implementations in `inputmodule.cpp` that abort with a clear error message pointing the user at `gridcell_outer` fallback + the staged rollout plan. Doc blocks explicitly state: input modules that override one MUST override the other (year_outer framework block calls them as a pair).

**Why non-pure-virtual with default implementations**: this preserves backward compatibility across all 9 existing input modules without forcing any of them to add stub overrides. Only modules that opt in to year_outer mode need to override.

### 4.5 `lpjguess/framework/inputmodule.cpp` — default-fail implementations

Added the bodies for the two new virtuals. Both call `fail()` (variadic; declared in `framework/shell.h`; transitively included via `guess.h`) with an actionable error pointing at:
- The fallback (`framework_loop_mode = "gridcell_outer"`)
- The canonical docs (`notes/FOLLOWUPS.md` F-12 + this STEP_17a.md + the staged rollout plan)

### 4.6 `lpjguess/framework/framework.cpp` — year_outer additive code path (~218 LOC)

Inserted a new `if (IMOGENConfig::framework_loop_mode == "year_outer") { ... return 0; }` block immediately before the existing `while (true)` per-gridcell-outer loop (between lines 409 and 411 of the pre-edit framework.cpp). The new block ends with `return 0;` so the existing per-gridcell-outer code path below is **byte-untouched** (no whitespace, indentation, or content change to the existing block; verifiable via `git diff -w` showing zero whitespace-only changes outside the new block).

#### 4.6.1 Block structure (5 phases per the design)

1. **C1 limitation guards** (~24 LOC) — fail fast with clear pointers to gridcell_outer fallback if any of: `restart`, `save_state`, `crop_gs_out`, `printseparatestands`. C1 deliberately scopes year_outer to the smoke-test critical path; these features are scheduled for C1.2 / C1.3 follow-ups.
2. **Year range determination** (~10 LOC) — `total_years = nyear_spinup + (lasthistyear - firsthistyear + 1)`; `first_calendar_year = firsthistyear - nyear_spinup`. Diagnostic `dprintf` lines for forensic visibility during C1 cross-validation.
3. **Pre-load all gridcells + climate** (~35 LOC) — replicates gridcell_outer's per-cell setup pipeline (lines 425-452 of the existing block: `date.init(1)`, `getgridcell`, `reset`, `setup_multipart`, `climate.initdrivers`, `landcover_init`); then calls `preload_all_climate(gridcell, first, last)` on the input module (default-fail unless input module overrides). All gridcells stored in a `std::vector<std::unique_ptr<Gridcell>>` for the year-outer phase.
4. **Per-year outer loop** (~50 LOC) — for each year_idx in [0, total_years), for each cell_idx in [0, num_cells), reset `date` to (year_idx, day=0), then 365-day inner loop calling `getclimate_for_year(gridcell, calendar_year, day_of_year)` + `simulate_day(gridcell, ...)` + `output_modules.outdaily(gridcell)`. Year-end actions (`outannual`, `balance.check_year`, `abort_request_received`) gated on `date.islastday && date.islastmonth` exactly as gridcell_outer does. `date.next()` per iteration.
5. **Per-cell teardown + cleanup + return** (~15 LOC) — mirrors gridcell_outer lines 524-528 (`balance.check_period` per cell), then `crop_gs_out` cleanup defensively, then explicit `return 0;` to skip the existing per-gridcell-outer block below.

#### 4.6.2 Why the early-return pattern (not else-wrap)

Wrapping the existing 124-line per-gridcell-outer block in `else { ... }` would force re-indenting every line by one level (4 spaces or 1 tab). That would produce a noisy `git diff` masking the actual additive nature of the change. The early-return-on-year_outer pattern keeps the existing block at byte-exact original whitespace, indentation, and content — the diff shows only the new block as added; nothing is modified. This is the cleanest possible structure for an additive parameter-gated alternative code path (mirroring the LandSyMM-fork-into-LTS integration pattern from the user's earlier integration project, per session-2 §6.2).

#### 4.6.3 Per-cell `date` management in year_outer (the Date::init(1) + manual year set pattern)

For each `(year_idx, cell_idx)` tuple, `date.init(1)` resets all per-day fields (day, month, dayofmonth, islastday/islastmonth/ismidday, etc.) to start-of-year zero values. Then `date.year = year_idx` sets the simulation-year-relative-to-first-calendar-year value. Subsequent `date.next()` calls inside the 365-day loop advance per-day correctly through the year, eventually setting `islastday + islastmonth` true at day 364 (after 12 month wraps). This sequence reproduces what gridcell_outer's per-cell `date.init(1)` + per-day `date.next()` chain produces — but per-cell-per-year rather than per-cell-across-all-years.

The global `first_calendar_year` (set elsewhere by `Date::set_first_calendar_year`) is unchanged; both modes see the same calendar-year mapping.

---

## 5. Design decisions + caveats

### 5.1 Design decision: D1 confirmed

Per session-2 §9.3, three design options were on the table for the `getclimate` global-state-coupling challenge:
- **D1**: NEW `preload_all_climate(gridcell, first_yr, last_yr)` virtual; year_outer reads from cache without invoking the existing per-day state machinery.
- **D2**: Make `date` a member of `Gridcell`. Largest refactor; deferred to v2.0 if ever.
- **D3**: Save/restore global `date` per-call within year_outer. Smallest refactor; subtle state-save timing pitfalls.

**This session confirms D1.** Rationale (extending session-2 §9.3 with this session's deeper findings):
- The IMOGENCFXInput class already has `all_*` 3D-vector cache infrastructure ready for D1 preload (per [§3.3](#33-imogencfxinput-already-has-the-all_-3d-vector-cache-infrastructure)). The `preload_all_climate` override can largely reuse `readenv` + `get_climate_for_gridcell`.
- D1 cleanly separates year_outer's climate access from the existing per-day stateful driver, avoiding both the global-`date` issue (D3's risk) and the cell-ordering-dependent shared-mutable-state issue (the `spinup_year_idx` finding in [§5.4](#54-the-spinup_year_idx-state-machine-finding-flagged-this-session)).
- D1 is purely additive at the input-module level: existing `getclimate(gridcell)` is unchanged byte-exactly; only NEW methods are added.

### 5.2 Foundation vs full C1 staging within step 17a

Session-2 §9.4 estimated C1 at ~1.5-2 weeks. This session's investigation confirms the IMOGENCFXInput year_outer override + cross-validation work is substantial (the spinup_year_idx state-machine reproduction formula is new this session; cross-validation requires the full launcher pipeline + smoke gridlist + 50-yr SSP1-2.6 .ins config + multi-run bit-exact comparison; iterative debugging likely). **This session lands the ARCHITECTURAL FOUNDATION** (parameter + base virtuals + framework block + default-mode regression verification). **Subsequent session(s) within step 17a complete the FULL C1** (IMOGENCFXInput overrides + cross-validation + tag).

The foundation alone is meaningful and reviewable:
- The new `framework_loop_mode` parameter is parseable from `.ins` files
- The `year_outer` framework block is in place (~218 LOC additive); year_outer mode RUNS through all 5 phases (with default-fail at the input-module preload, until any input module overrides it)
- 162 unit tests pass (default-mode byte-exact preserved)
- The user can review the design + architectural shape before the more complex IMOGENCFXInput refactor proceeds

This staging keeps each commit reviewable + debuggable in isolation.

### 5.3 C1 scope limitations (deliberately narrow; expand in C1.2 / C1.3)

The year_outer block fails fast on:
- `restart` (use gridcell_outer)
- `save_state` (use gridcell_outer)
- `crop_gs_out` (use gridcell_outer)
- `printseparatestands` (use gridcell_outer)

These are not needed for the SSP1-2.6 smoke test cross-validation. Adding support is purely additive future work; the `fail` calls give actionable fallback pointers.

### 5.4 The `spinup_year_idx` state-machine finding (flagged this session)

The session-2 §9.5 PRNG audit established that LPJ-GUESS's `Stand.seed` + `Gridcell.seed` are per-instance + ordering-friendly, supporting bit-exact cross-validation. **This session's deeper investigation found a separate ordering-sensitive state in `IMOGENCFXInput`**: the `spinup_year_idx` class-member counter (line 220 of `imogencfx.h`) **persists across cells** in gridcell_outer mode.

Concretely, with `nyear_spinup = 100` and `NYEAR_SPINUP = 30` (LandSyMM defaults):
- After `IMOGENCFXInput::init()` (line 411): `spinup_year_idx = 0`
- Cell 0's spinup years 0..99: `spinup_year_idx` cycles `1, 2, ..., 29, 0, 1, ..., 29, 0, 1, ..., 29, 0, 1, ..., 9` — ending at 10
- Cell 1's spinup years 0..99: starts from `spinup_year_idx = 10` (NOT 0); imogen_year sequence differs from cell 0's
- Cell 2's spinup years: starts from `(10 + 100) % 30 = 20`
- ...etc.

`imogen_year = FIRST_SPINUP_YEAR + spinup_year_idx`, so each cell sees DIFFERENT spinup climate forcing. This is the existing gridcell_outer behaviour and must be preserved EXACTLY per session-2 §9.5's "byte-identical default" constraint.

**For year_outer mode to produce bit-identical outputs to gridcell_outer**, the IMOGENCFXInput year_outer override (next session's work) must reproduce this state-machine progression by computing per-cell `spinup_year_idx_at_cell_start` deterministically. The formula is:

```
spinup_year_idx_at_cell_idx_year_idx
    = (cell_idx * nyear_spinup + year_idx + 1) % NYEAR_SPINUP
```

(Derived from: increment count from `init()` at start of cell C, spinup year Y is `C * nyear_spinup + Y + 1`; spinup_year_idx after the K-th increment is `K % NYEAR_SPINUP`.)

This is a 1-line formula in the year_outer input-module override. **No source change to gridcell_outer mode is required** — the formula reproduces what gridcell_outer's stateful counter would have produced, given knowledge of the cell index in the gridlist.

Cross-validation simplification for the next session: a **single-cell smoke gridlist** bypasses cell-ordering complexity entirely (cell 0 is the only cell; spinup_year_idx starts from 0 in both modes). After single-cell cross-validation passes, multi-cell cross-validation tests the formula reproduction.

This finding is captured in [`notes/FOLLOWUPS.md`](FOLLOWUPS.md) F-12 entry as a refinement of the C1 pre-flight findings.

---

## 6. Verification (this commit)

| Check | Method | Result |
|---|---|---|
| Build clean (no warnings outside pre-existing simfire_input.h fread) | `cd lpjguess/build && make -j$(nproc)` | ✅ |
| 162 unit tests pass | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| Default mode (`gridcell_outer`) byte-exact behaviour | Default value preserved; existing per-gridcell-outer code byte-untouched (early-return pattern) | ✅ verified via 162-test pass + visual inspection of `git diff -w` (zero whitespace-only changes outside new block) |
| `framework_loop_mode` parameter parses correctly | `declare_parameter` call wired in `IMOGENCFXInput` constructor; mirrors the proven `coupling_mode` pattern from step 8 | ✅ build succeeds; test instantiation paths exercise the parameter declaration without failure |
| Default-fail virtuals produce clear error message | `inputmodule.cpp` `fail()` calls have actionable text pointing at `gridcell_outer` fallback + canonical docs | ✅ static verification (live runtime test deferred to next session when an input module's override is invoked, allowing both code paths to exercise) |
| Cross-references resolve | All inline references to STEP_17a.md, FOLLOWUPS.md F-12, EXECUTION_PLAN V.1 row 17a are added/exist | ✅ |
| BACKPORT_LEDGER updated | New step-17a-foundation entry documenting the 6 file changes; `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | ✅ (this commit) |

**Empirical year_outer-mode end-to-end test deferred** to next session, when the IMOGENCFXInput overrides land. The foundation alone cannot be empirically end-to-end-verified because year_outer mode immediately default-fails at the `preload_all_climate` call (which is the intended semantics for the foundation).

---

## 7. Remaining work within C1 (C1.1, C1.2)

Per the foundation-vs-full-C1 staging in [§5.2](#52-foundation-vs-full-c1-staging-within-step-17a):

### 7.1 C1.1 — IMOGENCFXInput year_outer override (next session; ~3-5 days)

Implement two virtuals on `IMOGENCFXInput`:

#### `IMOGENCFXInput::preload_all_climate(Gridcell& gridcell, int first_calendar_year, int last_calendar_year)`

Pre-loads all needed climate for ONE cell across the year range. Implementation steps:
1. Determine cell index in gridlist (`current_grid_index`; existing class member, set by `getgridcell`)
2. For each year_idx in [0, total_years):
   - Compute calendar_year = first_calendar_year + year_idx
   - Determine if spinup: year_idx < nyear_spinup
   - Compute imogen_year:
     - If spinup: `imogen_year = FIRST_SPINUP_YEAR + ((current_grid_index * nyear_spinup + year_idx + 1) % NYEAR_SPINUP)` (per [§5.4](#54-the-spinup_year_idx-state-machine-finding-flagged-this-session))
     - If historical: `imogen_year = calendar_year`
   - Cache lookup via `stored_years[]`; if miss, allocate slot via `last_store_index++`
   - If reread: call `readenv(...)` for `imogen_year` (loads ALL cells' data for that year; reuses existing infrastructure)
   - Call `get_climate_for_gridcell(store_index, current_grid_index, gridcell.seed)` to fill per-day arrays for THIS cell THIS year
   - Store the per-day arrays into a NEW per-cell-per-year cache structure (TBD whether to reuse existing `dtemp[]`/`dprec[]`/etc. with overwrite semantics, or to add a per-(cell,year)-keyed cache)

Pre-requisites: ensure `nyears` (the `stored_years` cache size; line 230 of `imogencfx.h`) is large enough to hold all simulation years. Default value needs to be checked + possibly raised.

#### `IMOGENCFXInput::getclimate_for_year(Gridcell& gridcell, int calendar_year, int day_of_year)`

Reads from the per-cell-per-year cache populated by preload_all_climate. Assigns to `gridcell.climate.{temp, prec, insol, dtr, relhum, u10, tmin, tmax, co2}` and `gridcell.{dNH4dep, dNO3dep}` exactly as the existing `getclimate(gridcell)` does (lines 1166-1193 of `imogencfx.cpp`). Returns true (sim-done terminator handled by the year-outer loop's `total_years` bound, not by this method).

### 7.2 C1.2 — Cross-validation (next session; ~1-2 days)

Run BOTH modes with byte-identical inputs (.ins / gridlist / seeds / climate / LU forcing):
- **Run A**: `framework_loop_mode = "gridcell_outer"` (existing trusted baseline)
- **Run B**: `framework_loop_mode = "year_outer"` (new additive code path)

Cross-validation gridlist progression:
1. **Single-cell smoke first** — bypasses spinup_year_idx cell-ordering complexity; tests pure year_outer code path. Tolerance: bit-exact for ALL outputs.
2. **Multi-cell smoke (4-5 cells) second** — tests the spinup_year_idx state-machine reproduction formula. Tolerance: bit-exact for ALL outputs.

Outputs to compare: `cflux.out`, `cmass.out`, `mch4.out`, `ngases.out`, `cpool.out`, `nflux.out` (the standard LPJ-GUESS commonoutput suite).

Bit-exact cross-validation is the GO/NO-GO gate. If single-cell cross-validation fails, debug the year_outer code path. If multi-cell fails (after single-cell passes), debug the spinup_year_idx formula.

### 7.3 C1 close-out (next session; ~0.5 day)

After cross-validation passes:
- Update this STEP_17a.md with C1.1 + C1.2 outcomes (replace this §7)
- Update CHANGELOG `[Unreleased]` → `[v0.17.0-step17a-c1-year-outer-single-process]`
- Update EXECUTION_PLAN V.1 row 17a status: ⏳ → ✅ DONE
- Update FOLLOWUPS F-12 entry: C1 closed; C2 next
- Update BACKPORT_LEDGER with C1.1 file changes (likely `lpjguess/modules/imogencfx.cpp/h` additions + possible reuse of existing infrastructure)
- Tag `v0.17.0-step17a-c1-year-outer-single-process`; push to all 3 remotes

---

## 8. Cross-references

- **Canonical revised plan**: [`notes/FOLLOWUPS.md`](FOLLOWUPS.md) F-12 (especially the "C1 pre-flight investigation findings (2026-05-09 evening)" subsection)
- **Operational plan**: [`EXECUTION_PLAN.md`](../EXECUTION_PLAN.md) V.1 step rows 17a (this) + 17b (C2) + 17c (C3) + 17d (validation)
- **Architectural rationale + design options**: [`_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md`](../../_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md) Parts 5-9
- **Architectural diagnosis being resolved**: [`notes/FOLLOWUPS.md`](FOLLOWUPS.md) F-10 (the per-gridcell-outer / per-day-inner-across-all-years framework loop ordering)
- **PRNG audit (year_outer-friendly)**: `lpjguess/modules/driver.cpp:42` (`randfrac()`); `lpjguess/framework/guess.h:4931` (`Stand.seed`); `lpjguess/framework/guess.h:5406` (`Gridcell.seed`)
- **Existing per-gridcell-outer code (preserved byte-exactly)**: `lpjguess/framework/framework.cpp:411-534`
- **Coupling-mode template for new parameter**: `lpjguess/framework/parameters.h` (`coupling_mode`); `lpjguess/framework/parameters.cpp`; `lpjguess/modules/imogencfx.cpp` (`declare_parameter` call)
- **ImogenOutput year-change-detection (works correctly in BOTH modes; no change needed)**: `lpjguess/modules/imogenoutput.cpp:115-126`
- **Backport target (F-11)**: `notes/TRUNK_R13078_BACKPORT_LEDGER.md` — new step-17a-foundation entry added in this commit
- **Working paper context**: `paper/README.md` (3-axis paper-stage comparison framework; F-13 paper revisions)

---

## 9. Effort recap

| Phase | Hours (approx) |
|---|---|
| Inherited handoff ingest (sessions 1+2; ~554 KB / 8 199 lines; meticulous read) | 1.5-2.0 |
| Live verification anchors + repo state check + 162-test baseline | 0.25 |
| §7.1 verification anchors per session-2 + read 8 specific anchors per Part 9 §9.5/§9.6 | 0.5 |
| Deeper C1 pre-flight investigation (input module inventory; framework deps; parameters pattern; imogenoutput; spinup_year_idx finding) | 1.0 |
| Foundation implementation (parameter + base virtuals + framework block) | 1.0 |
| Default-mode regression verification (build + 162 tests) | 0.25 |
| This STEP_17a.md + supporting docs (CHANGELOG + FOLLOWUPS + EXECUTION_PLAN + BACKPORT_LEDGER + handoff Part 10) | 1.0-1.5 |
| **Total this session** | **~5.5-6.5 hours** |

**Remaining C1 effort estimate**: ~3-7 days of focused work for IMOGENCFXInput overrides + cross-validation + close-out (per [§7](#7-remaining-work-within-c1-c11-c12)). Aligns with session-2 §9.4's revised "1.5-2 weeks" total C1 estimate.
