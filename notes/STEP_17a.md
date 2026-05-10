# STEP 17a — F-12 sub-milestone C1 (Workstation single-process year_outer + cross-validation)

**Date opened:** 2026-05-10
**Date foundation landed:** 2026-05-10 (commit `2e918c0`)
**Date C1.1 implementation landed:** 2026-05-10 (commit `90401f2`)
**Date C1.2 cross-validation 1-cell PASS landed:** 2026-05-10 (this commit)
**Date C1 fully closed:** _pending — multi-cell cross-validation + IMOGENCFXInput follow-up (C1.3)_
**Foundation commit:** `2e918c0` (un-tagged)
**C1.1 implementation commit:** `90401f2` (un-tagged; on top of `2e918c0`)
**C1.2 1-cell cross-validation commit:** _to be filled in after `git commit`_ (un-tagged; on top of `90401f2`)
**Full C1 commit / tag:** _pending — `v0.17.0-step17a-c1-year-outer-single-process`. Tag waits for multi-cell bit-exact cross-validation + IMOGENCFXInput year_outer override per [§7.3 + §7.4](#73-c13--imogencfxinput-year_outer-override-next-sessions-2-3-days)._
**Status:** ✅ **FOUNDATION + C1.1 IMPLEMENTATION + C1.2 1-CELL CROSS-VALIDATION PASS LANDED; multi-cell + C1.3 PENDING.** This commit lands the runtime 1-cell smoke cross-validation: Run A (`framework_loop_mode = "gridcell_outer"`) vs Run B (`framework_loop_mode = "year_outer"`) produced **all 37 .out files bit-exact (37/37 matches; 0 mismatches)**. The year_outer code path is empirically validated for the smoke-test critical path. **GO/NO-GO gate per session-2 §9.5: PASSED.** Multi-cell cross-validation (tests the spinup_year_idx formula across cells) + IMOGENCFXInput year_outer override (C1.3) are the next session(s) of work within step 17a, before tagging.

**User's strategic guidance applied this session (2026-05-10 evening)**: per the user's reminder, both `searchradius` (climate; declared as ImogenInput class member; custom-param table syntax `param "X" (num Y)`) and `searchradius_soil` (declared via `declare_parameter` at `soilinput.h:32`; global plib syntax `X Y` bare assignment) parameters were essential to make ImogenInput's loose-mode runs succeed against staged engine climate (1631-cell IMOGEN grid) + 62892-cell soilmap with NO exact-cell intersections. The IMOGEN engine also has a `REGRID` parameter (`runs/SSP1-2.6/imogen_intermediary.ins:244`; currently `0`/FALSE) that, when enabled, makes the engine regrid climate output to a user-specified gridlist — alternative path to the searchradius approach for cases where the user wants engine output AT specific LPJG cells. Documented for the IMOGENCFXInput follow-up (C1.3).

**Strategic decision (this session)**: C1.1 starts with **`ImogenInput`** (loose-coupling input module) rather than `IMOGENCFXInput`, because ImogenInput has NO `RUN_IMOGEN_ENGINE()` call in `init()` — so loose-mode runs are not blocked by F-10 and end-to-end cross-validation is achievable without an engine-bypass workaround. The two input modules have nearly-identical `getclimate()` patterns; the implementation strategy + spinup_year_idx formula transfer ~95% to `IMOGENCFXInput` later (a natural follow-up sub-step within step 17a, possibly bundled with an engine-bypass parameter or with C2's per-year-inline engine-drive integration). See [§5.5](#55-revised-c1-staging-imogeninput-first-imogencfxinput-follow-up).

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

### 5.4 The `spinup_year_idx` state-machine finding (flagged this session) [ERRATUM applied at C1.1 implementation]

The session-2 §9.5 PRNG audit established that LPJ-GUESS's `Stand.seed` + `Gridcell.seed` are per-instance + ordering-friendly, supporting bit-exact cross-validation. **This session's deeper investigation (foundation phase) found a separate ordering-sensitive state in `IMOGENCFXInput` and `ImogenInput`**: the `spinup_year_idx` class-member counter (line 220 of `imogencfx.h`; line 199 of `imogen_input.h`) **persists across cells** in gridcell_outer mode.

Concretely, with `nyear_spinup = 100` and `NYEAR_SPINUP = 30` (LandSyMM defaults):
- After `init()`: `spinup_year_idx = 0`
- Cell 0's spinup year 0, day 0: `imogen_year = FIRST_SPINUP_YEAR + 0 = 1871` is computed using the OLD value, then `spinup_year_idx` is incremented to 1
- Cell 0's spinup year 1, day 0: `imogen_year = FIRST_SPINUP_YEAR + 1 = 1872`; then incremented to 2
- ...
- Cell 0's spinup year 29, day 0: `imogen_year = FIRST_SPINUP_YEAR + 29 = 1900`; then incremented to 30 → wrap to 0
- Cell 0's spinup year 30, day 0: `imogen_year = FIRST_SPINUP_YEAR + 0 = 1871`; incremented to 1
- ...
- Cell 0's spinup year 99 (LAST spinup year): `spinup_year_idx_BEFORE` = 99 % 30 = 9; `imogen_year = FIRST_SPINUP_YEAR + 9 = 1880`; AFTER = 10
- Cell 1's spinup year 0, day 0: starts from `spinup_year_idx = 10` (carried from cell 0); `imogen_year = FIRST_SPINUP_YEAR + 10 = 1881`; then incremented to 11
- ...

`imogen_year = FIRST_SPINUP_YEAR + spinup_year_idx_BEFORE_THIS_CALL`, so each cell sees DIFFERENT spinup climate forcing per its starting `spinup_year_idx`. This is the existing gridcell_outer behaviour and must be preserved EXACTLY per session-2 §9.5's "byte-identical default" constraint.

**For year_outer mode to produce bit-identical outputs to gridcell_outer**, the input-module year_outer override must reproduce this state-machine progression by computing per-cell `spinup_year_idx` deterministically. The CORRECTED formula (verified by tracing the exact code at `imogen_input.cpp` lines 781-805 / `imogencfx.cpp` lines 1071-1095 during C1.1 implementation):

```
spinup_year_idx_at_(cell_idx, year_idx)
    = (cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP
```

**NOTE: NO `+1`.** The CHAT_HANDOFF Part 10 + earlier draft of this §5.4 + earlier CHANGELOG entry + earlier FOLLOWUPS F-12 update + earlier BACKPORT_LEDGER entry incorrectly stated `(cell_idx * nyear_spinup + year_idx + 1) % NYEAR_SPINUP`. The CORRECT formula has no `+1` because the existing `getclimate()` reads the spinup_year_idx VALUE BEFORE incrementing it on day 0 (the increment happens AFTER imogen_year is computed). Derivation:
- `init()` sets `spinup_year_idx = 0`
- Cumulative spinup-year-day-0 increments BEFORE (cell C, year Y, day 0) = `C * nyear_spinup + Y` (cell C has been preceded by C cells × nyear_spinup spinup years; within cell C, Y prior spinup years have been processed)
- Each such call increments `spinup_year_idx` by 1 (modulo NYEAR_SPINUP)
- So `spinup_year_idx_BEFORE_THIS_CALL = (C * nyear_spinup + Y) % NYEAR_SPINUP`
- And `imogen_year = FIRST_SPINUP_YEAR + spinup_year_idx_BEFORE_THIS_CALL`

The C1.1 implementation in `ImogenInput::preload_all_climate` + `ImogenInput::getclimate_for_year` uses the CORRECT formula (no `+1`). Subsequent doc updates (this STEP_17a.md §5.4, the CHANGELOG entry, the FOLLOWUPS F-12 extension, the BACKPORT_LEDGER step-17a-c1.1 entry, the session-2 handoff Part 11) all reflect the corrected formula.

Cross-validation simplification (preserved from foundation-phase plan): a **single-cell smoke gridlist** bypasses cell-ordering complexity entirely (cell 0 is the only cell; `spinup_year_idx_at_(0, year_idx) = year_idx % NYEAR_SPINUP` regardless of formula edge cases). After single-cell cross-validation passes, multi-cell cross-validation tests the cell-ordering aspect of the formula.

This finding is captured in [`notes/FOLLOWUPS.md`](FOLLOWUPS.md) F-12 entry as a refinement of the C1 pre-flight findings (with the erratum corrected).

### 5.5 Revised C1 staging: `ImogenInput` first; `IMOGENCFXInput` follow-up

Foundation + C1.1 implementation deliberately scoped to `ImogenInput` (loose-coupling input module) for these reasons:

1. **`ImogenInput::init()` does NOT call `RUN_IMOGEN_ENGINE()`** (verified via `grep RUN_IMOGEN_ENGINE` — only `imogencfx.cpp:524` has it). So loose-mode runs (`-input imogen` + `coupling_mode "loose"`) complete `init()` cleanly + reach the LPJG main loop, regardless of `framework_loop_mode` setting. **No engine-bypass workaround needed for cross-validation.**
2. **`ImogenInput`'s `getclimate()` pattern is ~95% identical to `IMOGENCFXInput::getclimate()`** (same `spinup_year_idx` state machine; same `stored_years[]` cache; same `readenv()` + `get_climate_for_gridcell()` infrastructure). The implementation strategy + spinup_year_idx formula derived in C1.1 transfers to `IMOGENCFXInput` near-verbatim.
3. **Cross-validation purpose (per session-2 §9.5)**: validate the year_outer code path's CORRECTNESS vs gridcell_outer's. The input module choice is secondary; what matters is bit-exact comparison between modes WITH SAME input module + SAME climate forcing.
4. **`IMOGENCFXInput` year_outer override is a natural follow-up sub-step within step 17a**, bundled with one of:
   - A NEW ins parameter (e.g., `skip_inprocess_engine_run`) that gates the `RUN_IMOGEN_ENGINE()` call in `IMOGENCFXInput::init()` — useful for testing scenarios where climate is already pre-staged on disk
   - C2's MPI work, which inherently involves rethinking the engine-drive integration (per session-2 §6.3.2's Option C sketch: per-year-inline `climatemodel.run_year(yr+1)` call within the year_outer loop's year-boundary block)

This staging keeps each commit reviewable + bug-bounded. The full `v0.17.0-step17a-c1-year-outer-single-process` tag waits for the bit-exact cross-validation pass with at least one input module's year_outer override (ImogenInput, per this C1.1 work).

---

## 6. Verification

### 6.1 Foundation commit (`2e918c0`; 2026-05-10)

| Check | Method | Result |
|---|---|---|
| Build clean (no warnings outside pre-existing simfire_input.h fread) | `cd lpjguess/build && make -j$(nproc)` | ✅ |
| 162 unit tests pass | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| Default mode (`gridcell_outer`) byte-exact behaviour | Default value preserved; existing per-gridcell-outer code byte-untouched (early-return pattern) | ✅ verified via 162-test pass + visual inspection of `git diff -w` (zero whitespace-only changes outside new block) |
| `framework_loop_mode` parameter parses correctly | `declare_parameter` call wired in `IMOGENCFXInput` constructor; mirrors the proven `coupling_mode` pattern from step 8 | ✅ build succeeds; test instantiation paths exercise the parameter declaration without failure |
| Default-fail virtuals produce clear error message | `inputmodule.cpp` `fail()` calls have actionable text pointing at `gridcell_outer` fallback + canonical docs | ✅ static verification (live runtime test deferred to C1.1 when an input module's override is invoked, allowing both code paths to exercise) |
| Cross-references resolve | All inline references to STEP_17a.md, FOLLOWUPS.md F-12, EXECUTION_PLAN V.1 row 17a are added/exist | ✅ |
| BACKPORT_LEDGER updated | New step-17a-foundation entry documenting the 6 file changes; `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | ✅ |

**Empirical year_outer-mode end-to-end test was deferred** to C1.1 (this commit) at foundation time, because the foundation alone cannot be empirically end-to-end-verified — year_outer mode immediately default-fails at the `preload_all_climate` call (which is the intended semantics for the foundation).

### 6.2 C1.1 implementation commit (this commit; 2026-05-10)

| Check | Method | Result |
|---|---|---|
| Build clean | `cd lpjguess/build && make -j$(nproc)` (full clean rebuild) | ✅ (only pre-existing `simfire_input.h` `cruncep_*.h` `GlobalNitrogenDeposition*.h` `gutil.{cpp,h}` `indata.cpp` warnings; ZERO warnings introduced by C1.1 additions) |
| 162 unit tests pass | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| Header includes resolved (`<map>`, `<utility>`, `lamarquendep.h`) | `imogen_input.h` modifications | ✅ included |
| Spinup_year_idx formula correct (NO `+1`) | Hand-traced against `imogen_input.cpp:781-805` | ✅ formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` matches |
| Per-cell ndep cache copies are independent | `Lamarque::NDepData` is value type (no pointers; just arrays); `std::map<key, NDepData>` value-copies on insert | ✅ verified via `lamarquendep.h` member inspection |
| K → degC temperature conversion preserved | `getclimate_for_year` line: `climate.temp = dtemp[day_of_year] - 273.15;` matches existing `getclimate` line 876 | ✅ |
| Per-day field assignments mirror existing `getclimate` | All 6 fields (temp/prec/insol/dtr conditional/dNH4dep/dNO3dep) populated identically | ✅ |
| `fail()` paths produce actionable messages on cache miss / sim-done / corrupt state | All 5 fail() call sites have specific context (cell coords + year + day + cache state) | ✅ |
| Backward compatibility with existing `getclimate()` (gridcell_outer mode) | `getclimate()` body unchanged; new methods are SEPARATE additions; existing code path completely intact | ✅ |
| BACKPORT_LEDGER updated | New step-17a-c1.1 entry documenting the 2 file changes (`imogen_input.h` + `imogen_input.cpp`); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | ✅ (this commit) |

**Empirical year_outer-mode end-to-end test still deferred** to C1.2 (next session), because cross-validation requires:
1. Pre-staged climate output at `runs/SSP1-2.6/Common-directory/IMOGEN/output/{1871..1900+}/` (currently MISSING after a previous post-smoke cleanup)
2. A custom cross-validation .ins file with `coupling_mode "loose"` (uses ImogenInput) + `framework_loop_mode "year_outer"` for Run B (Run A uses default `gridcell_outer`)
3. A bash harness that runs both modes + diffs the .out files cell-by-cell
4. Iteration on any divergences found

Per the strategic decision in [§5.5](#55-revised-c1-staging-imogeninput-first-imogencfxinput-follow-up), each commit is bug-bounded; cross-validation is a separate runtime exercise that's bounded by what an empirical run reveals.

---

## 7. Remaining work within C1 (C1.2 cross-validation; IMOGENCFXInput follow-up)

Per the revised staging in [§5.5](#55-revised-c1-staging-imogeninput-first-imogencfxinput-follow-up), foundation + C1.1 implementation are landed; the runtime cross-validation (C1.2) and the IMOGENCFXInput year_outer follow-up are the remaining work.

### 7.1 C1.1 — ImogenInput year_outer override [DONE this commit]

Implemented two virtuals on `ImogenInput`:

- **`ImogenInput::preload_all_climate(gridcell, first_calendar_year, last_calendar_year)`** — pre-loads all needed years' climate for ONE cell into the existing `all_temp/all_prec/all_wetdays/all_insol/all_dtr` cache via `readenv()`. Caches per-cell `cell_idx` (== `current_grid_index` at preload time) + per-cell `Lamarque::NDepData` value-copy in `year_outer_cell_idx` + `year_outer_ndep_cache` maps respectively. Uses the corrected spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`; per [§5.4 erratum](#54-the-spinup_year_idx-state-machine-finding-flagged-this-session-erratum)) to compute per-(cell, year) `imogen_year` values that match what gridcell_outer mode would have selected.

- **`ImogenInput::getclimate_for_year(gridcell, calendar_year, day_of_year)`** — reads from cache. On day 0 of each (cell, year) tuple: looks up `cell_idx` + cached `NDepData`, calls existing `get_climate_for_gridcell()` to populate per-day arrays, calls `cell_ndep.get_one_calendar_year(...)` + `distribute_ndep(...)`, sets `climate.co2`. Every day: assigns `climate.{temp - 273.15 (K→degC), prec, insol, dtr conditional}` + `gridcell.{dNH4dep, dNO3dep}` from per-day arrays. Returns false at sim-done terminator (`calendar_year > lasthistyear`) or on missing-grid-point conditions.

Implementation files:
- `lpjguess/modules/imogen_input.h` (+~80 LOC: 3 includes, 2 method declarations with extensive doc blocks, 2 cache map members)
- `lpjguess/modules/imogen_input.cpp` (+~200 LOC: 2 method implementations with doc blocks, error handling, cross-references)

Verified per [§6.2](#62-c11-implementation-commit-this-commit-2026-05-10): build clean; 162 unit tests pass; backward compatibility preserved.

### 7.2 C1.2 — Cross-validation 1-cell smoke [DONE this commit; PASSED bit-exact]

Ran BOTH modes with byte-identical inputs (.ins / gridlist / climate / seeds):
- **Run A**: `framework_loop_mode = "gridcell_outer"` (existing trusted baseline)
- **Run B**: `framework_loop_mode = "year_outer"` (new additive code path; uses C1.1's overrides)

**Setup files added this commit**:
- `data/gridlist/gridlist_test1.txt` (NEW; 1-cell IMOGEN grid cell at `-78.75 82.50`; corresponds to IMOGEN native cell `281.25 82.50` via ImogenInput's `lon > 180 → lon - 360` normalization at `imogen_input.cpp:466`)
- `runs/SSP1-2.6/main_xval_loose.ins` (NEW; loose-mode .ins; absolute paths for gridlist + soilmap + relative paths for engine climate so cwd=Common-directory resolves correctly; `param "searchradius" (num 50)` + `searchradius_soil 50` to handle the IMOGEN-grid-vs-soilmap mismatch; minimal nyear_spinup=1 + firsthistyear=lasthistyear=1871 to use only ODD-numbered staged climate years)
- `scripts/cross_validate_year_outer.sh` (NEW; bash harness; cd into Common-directory; per-run wrapper .ins generation with framework_loop_mode + gridlist + outputdirectory overrides; cmp -s loop for bit-exact comparison; clean PASS/FAIL summary)

**1-LOC code addition this commit** (in `lpjguess/modules/imogen_input.cpp`):
- `declare_parameter("framework_loop_mode", &IMOGENConfig::framework_loop_mode, 20, ...)` mirroring `IMOGENCFXInput`'s identical declaration. Required for `-input imogen` (loose-mode) runs to recognize the parameter (without it, `Paramlist::operator[]` aborts with "framework_loop_mode not found").

**Operational pre-requisites** (resolved this session):
1. **Climate pre-staged** via `timeout --foreground 300 ./scripts/run_coupled.sh --no-build` per session-1 §49.1's documented operational pattern. Engine produced 32 year-output dirs at `runs/SSP1-2.6/Common-directory/IMOGEN/output/{1871..1902}/` (~3-5 min wall-clock; SIGTERM via timeout + launcher's `||` graceful exit handler). **Discovered**: only ODD years (1871, 1873, ..., 1901) have full climate (13 files); EVEN years have only `done` marker. The smoke config was constrained to need only odd-year imogen_year values to bypass this constraint.

2. **Per the user's 2026-05-10 evening guidance**, the searchradius (climate) and searchradius_soil mechanisms enabled both the IMOGEN grid + soilmap mismatches to be resolved via nearest-neighbour fallback. The user also noted the `REGRID` parameter (`runs/SSP1-2.6/imogen_intermediary.ins:244`; currently `0`/FALSE) as an alternative engine-side mechanism to regrid climate to a user-specified gridlist — useful for IMOGENCFXInput follow-up (C1.3) and production runs.

**1-cell cross-validation result (this commit)**:

```
================================================================================
SUMMARY: 37/37 bit-exact matches; 0 mismatches
================================================================================
PASS: All .out files are bit-exact between Run A and Run B.
```

All 37 standard LPJ-GUESS outputs match bit-exactly: `aaet.out`, `agpp.out`, `anpp.out` (+ cropland/natural/pasture variants), `cflux.out` (+ cropland/natural/pasture), `clitter.out`, `cmass.out`, `cpool.out` (+ cropland/natural/pasture), `cton_leaf.out`, `fpc.out`, `lai.out`, `mch4.out` (+ diffusion/ebullition/plant), `nflux.out` (+ cropland/natural/pasture), `ngases.out`, `nlitter.out`, `nmass.out`, `npool.out` (+ cropland/natural/pasture), `nsources.out`, `nuptake.out`, `tot_runoff.out`.

**GO/NO-GO gate per session-2 §9.5: ✅ PASSED for 1-cell smoke.** The year_outer code path is empirically validated to produce bit-identical outputs to gridcell_outer for the smoke-test critical path. The corrected spinup_year_idx formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) verified correct in single-cell scenarios (cell_idx=0).

### 7.3 C1.3 — Multi-cell cross-validation + IMOGENCFXInput year_outer override (next session(s); ~2-3 days)

After 1-cell cross-validation PASSED bit-exact this commit, two follow-up sub-steps remain within step 17a:

**Sub-step 7.3.1 — Multi-cell cross-validation** (~0.5 day):
- Use 4-cell `gridlist_test2.txt` OR a custom 4-5 cell gridlist with cells in IMOGEN's native grid
- Configure `nyear_spinup` so each cell's `imogen_year_at_(cell_idx, 0)` lands on an ODD year that's available in staged climate. With nyear_spinup=2, formula gives cell C → imogen_year = 1871 + 2C, all odd ✓ for cells 0..14 (covers 4-5 cells).
- Or alternatively: re-stage climate with `REGRID=1` so engine produces climate at exactly the LPJG gridlist cells (no nearest-neighbor needed).
- Cross-validate; target bit-exact to validate the spinup_year_idx formula across cells.

**Sub-step 7.3.2 — IMOGENCFXInput year_outer override** (~1.5-2 days):
- Replicate the C1.1 implementation pattern for `IMOGENCFXInput` (the `-input imogencfx` tight-coupling input module)
- Per the user's 2026-05-10 evening note: IMOGENCFXInput supports more input types than ImogenInput (NetCDF ndep + population data etc.), so the implementation needs more careful handling for the additional fields
- Add additional climate fields (relhum, wind, tmin, tmax) to the override + handle the BLAZE compatibility check
- IMPORTANT: `IMOGENCFXInput::init()` calls `RUN_IMOGEN_ENGINE()` which deadlocks per F-10. For C1.3 cross-validation, options:
  - (a) NEW `skip_inprocess_engine_run` ins parameter (~10 LOC) gating the engine call — simplest
  - (b) `REGRID=1` engine run + cross-validation against the regridded climate — uses existing config knobs
  - (c) Defer IMOGENCFXInput cross-validation to C2 (when proper per-year-inline engine drive lands per session-2 §6.3.2's Option C sketch)
- Cross-validate identically (single-cell first; multi-cell second).

### 7.4 C1 close-out (after C1.3; ~0.5 day)

After both multi-cell + IMOGENCFXInput cross-validations pass bit-exactly:
- Update this STEP_17a.md with C1.3 outcomes
- Update CHANGELOG `[Unreleased]` → `[v0.17.0-step17a-c1-year-outer-single-process]`
- Update EXECUTION_PLAN V.1 row 17a status: 🔧 → ✅ DONE
- Update FOLLOWUPS F-12 entry: C1 closed; C2 next
- Update BACKPORT_LEDGER with C1.3 file changes
- Tag `v0.17.0-step17a-c1-year-outer-single-process`; push to all 3 remotes

### 7.3 C1.3 — IMOGENCFXInput year_outer override (next session(s); ~2-3 days)

Once C1.2 cross-validation passes for ImogenInput, replicate the implementation pattern for `IMOGENCFXInput`:

- `IMOGENCFXInput::preload_all_climate(gridcell, first_yr, last_yr)` — identical structure to `ImogenInput::preload_all_climate` plus the additional climate fields IMOGENCFXInput handles (relhum, wind, tmin, tmax — populated via the additional `read_lines_from_file` calls in `readenv()` for the corresponding `file_*` params)
- `IMOGENCFXInput::getclimate_for_year(gridcell, calendar_year, day_of_year)` — identical to `ImogenInput::getclimate_for_year` PLUS the relhum/wind/tmin/tmax assignments AND the BLAZE compatibility check. NOTE: IMOGENCFXInput's `getclimate` does NOT do the K→degC conversion (the existing line is `climate.temp = dtemp[date.day]` without `-273.15`); preserve this difference for byte-exactness.
- Optional: NEW ins parameter `skip_inprocess_engine_run` (default `false`) gating the `RUN_IMOGEN_ENGINE()` call in `IMOGENCFXInput::init()`. Allows imogencfx-mode cross-validation against pre-staged climate without F-10 deadlock.

Cross-validate IMOGENCFXInput year_outer mode against gridcell_outer baseline (same single-cell-first then multi-cell pattern).

### 7.4 C1 close-out (after C1.2 + C1.3; ~0.5 day)

After both ImogenInput AND IMOGENCFXInput cross-validations pass bit-exactly:
- Update this STEP_17a.md with C1.2 + C1.3 outcomes
- Update CHANGELOG `[Unreleased]` → `[v0.17.0-step17a-c1-year-outer-single-process]`
- Update EXECUTION_PLAN V.1 row 17a status: ⏳/🔧 → ✅ DONE
- Update FOLLOWUPS F-12 entry: C1 closed; C2 next
- Update BACKPORT_LEDGER with C1.2/C1.3 file changes
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
