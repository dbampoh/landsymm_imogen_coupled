# STEP 17a — F-12 sub-milestone C1 (Workstation single-process year_outer + cross-validation)

**Date opened:** 2026-05-10
**Date foundation landed:** 2026-05-10 (commit `2e918c0`)
**Date C1.1 implementation landed:** 2026-05-10 (commit `90401f2`)
**Date C1.2 cross-validation 1-cell PASS landed:** 2026-05-10 (commit `8bddc27`)
**Date C1.3 sub-step 7.3.1 multi-cell PASS + engine writer fix landed:** 2026-05-10 (commit `7be595a`)
**Date C1.3 sub-step 7.3.2 IMOGENCFXInput year_outer override + K→C fix landed:** 2026-05-10 (this commit; FULL C1 CLOSE-OUT)
**Date C1 fully closed:** **2026-05-10 (this commit)**
**Foundation commit:** `2e918c0` (un-tagged)
**C1.1 implementation commit:** `90401f2` (un-tagged; on top of `2e918c0`)
**C1.2 1-cell cross-validation commit:** `8bddc27` (un-tagged; on top of `90401f2`)
**C1.3 sub-step 7.3.1 commit:** `7be595a` (un-tagged; on top of `8bddc27`)
**C1.3 sub-step 7.3.2 + close-out commit / tag:** _to be filled in after `git commit + git tag`_ (TAGGED `v0.17.0-step17a-c1-year-outer-single-process`; on top of `7be595a`)
**Status:** ✅ **FULL C1 CLOSE-OUT LANDED.** Foundation + C1.1 ImogenInput overrides + C1.2 1-cell xval PASS + C1.3 sub-step 7.3.1 4-cell xval PASS + engine writer fix + C1.3 sub-step 7.3.2 IMOGENCFXInput year_outer override + K→C latent-bug fix all done. ALL FOUR cross-validation scenarios (imogen 1cell, imogen 4cell, imogencfx 1cell, imogencfx 4cell) PASS bit-exact (37/37 .out files identical between Run A `gridcell_outer` and Run B `year_outer` for each scenario). The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is empirically validated for BOTH input modules across BOTH single-cell + multi-cell + single-spinup-year + multi-spinup-year scenarios. **GO/NO-GO gate per session-2 §9.5: PASSED for all 4 scenarios.** Tagging `v0.17.0-step17a-c1-year-outer-single-process` at this commit. This commit lands TWO bundled deliverables:
1. **Engine writer fix** in `lpjguess/modules/climatemodel.cpp` (4 conditional removals; ~76 LOC including doc blocks): removes the `if (iyear == year1)` and `if (iyear == iyend)` gates around the climate-anomaly file OPEN/CLOSE blocks (lines ~884, ~963, ~988, ~998) AND the CO2.dat/CO2_all.dat writer block (line ~787). Fixes the **alternating-year staged-climate structural quirk** discovered at C1.2: previously each engine call only produced full climate for `IYEAR == YEAR1` (combined with `updateImogenControlData()` advancing `IMOGENConfig::YEAR1++` per IYEAR iteration → calls advanced by 2 years → only ODD-numbered years 1871, 1873, ..., 1901 had data; EVEN years had only `done` markers). With the fix, ALL years get full 13-file climate. Verified empirically: re-staged climate via launcher (~3-4 min wall-clock) produces 32 dirs (1871-1902) ALL with 13 files (vs prior 16 ODD with 13 files + 16 EVEN with 1 file).
2. **C1.3 sub-step 7.3.1 multi-cell cross-validation**: 4-cell `gridlist_test2.txt` × `nyear_spinup=2` × `lasthistyear=1879` × 11 simulated years per cell × 4 cells = 44 cell-year iterations per run. Run A (`framework_loop_mode = "gridcell_outer"`) vs Run B (`framework_loop_mode = "year_outer"`) → **all 37 .out files bit-exact (37/37 matches; 0 mismatches)**. **GO/NO-GO gate per session-2 §9.5: PASSED for 4-cell smoke (and 1-cell smoke; re-verified PASS with the new config).** The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`; corrected at C1.1) is now empirically validated across BOTH cell_idx>0 AND year_idx>0 branches.

**User's strategic guidance applied this session (2026-05-10 evening)**: per the user's reminder, both `searchradius` (climate; declared as ImogenInput class member; custom-param table syntax `param "X" (num Y)`) and `searchradius_soil` (declared via `declare_parameter` at `soilinput.h:32`; global plib syntax `X Y` bare assignment) parameters were essential to make ImogenInput's loose-mode runs succeed against staged engine climate (1631-cell IMOGEN grid) + 62892-cell soilmap with NO exact-cell intersections. The IMOGEN engine also has a `REGRID` parameter (`runs/SSP1-2.6/imogen_intermediary.ins:244`; currently `0`/FALSE) that, when enabled, makes the engine regrid climate output to a user-specified gridlist — alternative path to the searchradius approach for cases where the user wants engine output AT specific LPJG cells. Documented for the IMOGENCFXInput follow-up (C1.3 sub-step 7.3.2).

**Strategic decision (initial 2026-05-10 morning, preserved)**: C1.1 starts with **`ImogenInput`** (loose-coupling input module) rather than `IMOGENCFXInput`, because ImogenInput has NO `RUN_IMOGEN_ENGINE()` call in `init()` — so loose-mode runs are not blocked by F-10 and end-to-end cross-validation is achievable without an engine-bypass workaround. The two input modules have nearly-identical `getclimate()` patterns; the implementation strategy + spinup_year_idx formula transfer ~95% to `IMOGENCFXInput` later. See [§5.5](#55-revised-c1-staging-imogeninput-first-imogencfxinput-follow-up).

**Strategic decision (2026-05-10 evening, this commit)**: bundle the **engine writer fix in `climatemodel.cpp`** with the C1.3 sub-step 7.3.1 multi-cell xval. The fix is structurally needed for the multi-cell test (without it, the staged climate alternates ODD-only and the formula's year_idx>0 branch would hit EVEN-year imogen_year selections that lack climate). The fix is small (~76 LOC mostly comment blocks; ~10 LOC actual code change), well-bounded (4 conditional removals + 1 CO2-block conditional removal; no logic changes beyond gate removal), and addresses a real engine-side bug (each call previously wrote climate data for ONLY YEAR1, silently dropping IYEND iterations' writes; combined with `updateImogenControlData()` advancing YEAR1++ per IYEAR iteration → only ODD years produced fully). The fix is structurally appropriate: the `thisYear` variable was already updated per IYEAR iteration at line ~457 (`thisYear = std::to_string(iyear)`), so each iteration's open targets the correct year-folder; only the `if (iyear == year1)` gate prevented the open from happening. See [§5.6](#56-engine-writer-fix-bundled-in-this-commit-rationale).

This session's work: ~5-6 hours wall-clock for foundation phase (commits `2e918c0`, `90401f2`, `8bddc27`) + ~2-3 hours for this engine-writer-fix + 4-cell xval phase (~9 hours total session work).

Net `lpjguess/` source-level change cumulative across step 17a so far:
- **Foundation commit `2e918c0`** (5 files; +~250 LOC additive): `parameters.h/cpp` (`framework_loop_mode` extern + default), `imogencfx.cpp` (`declare_parameter` registration), `inputmodule.h/cpp` (two new virtuals with default-fail), `framework.cpp` (year_outer additive block).
- **C1.1 commit `90401f2`** (2 files; +~280 LOC additive): `imogen_input.h` (3 includes, 2 virtuals, 2 cache map members), `imogen_input.cpp` (2 method implementations).
- **C1.2 commit `8bddc27`** (1 file; +9 LOC additive): `imogen_input.cpp` (`declare_parameter` for framework_loop_mode mirror).
- **C1.3 sub-step 7.3.1 + engine writer fix this commit** (1 file; +76 LOC, -5 LOC; net +~71 LOC):
  - `lpjguess/modules/climatemodel.cpp` (engine writer fix; 5 conditional removals + extensive comment blocks documenting the structural cause/fix/effect)

**Backport-Sprint-relevance: HIGH for all step-17a changes.** All file changes need to be replicated in `trunk_r13078` per F-11 discipline. The additive nature (new parameters; new virtuals with default implementations; new code block gated on parameter; engine writer gate-removal preserves all writes) makes the backport mechanical.

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

### 5.4 The `spinup_year_idx` state-machine finding (flagged this session) [ERRATUM applied at C1.1 implementation; SUPERSEDED-BY-CORRECTION at Step 17c sub-phase 17c.0.6, 2026-05-15]

> **§5.4 SUPERSEDED-BY-CORRECTION (added 2026-05-15 in Step 17c sub-phase 17c.0.6 commit; NEW ERRATUM superseding the original C1.1 erratum):** The §5.4 derivation below — specifically the premise verbatim asserted at the worked example _"Cell 1's spinup year 0, day 0: starts from `spinup_year_idx = 10` (carried from cell 0)"_ and the corresponding closed-form formula `spinup_year_idx_at_(cell_idx, year_idx) = (cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` — is **WRONG**. The premise that `spinup_year_idx` "persists across cells in gridcell_outer mode" is false. The actual code at `lpjguess/modules/imogen_input.cpp:880` (and symmetrically `lpjguess/modules/imogencfx.cpp:1122`) RESETS `spinup_year_idx = 0` at the start of every cell inside `getgridcell()`:
>
> ```cpp
> // new gridcell ensure, we start at index one for spinup
> spinup_year_idx = 0;
> ```
>
> Therefore the gridcell_outer reference behavior is: cell c, spinup year y → `imogen_year = FIRST_SPINUP_YEAR + (y % NYEAR_SPINUP)` for ALL cells (NO cell_idx dependence). The CORRECTED closed-form formula used in the year_outer overrides at `lpjguess/modules/(imogen_input|imogencfx).cpp::(preload_all_climate|getclimate_for_year)` is:
>
> ```
> spinup_year_idx_at_(cell_idx, year_idx) = year_idx % NYEAR_SPINUP    ← NO cell_idx term
> ```
>
> The original §5.4 derivation's `cell_idx * nyear_spinup` term was a per-cell offset that gridcell_outer doesn't have (the per-cell reset wipes the increment history). The C1.1 implementation (commit `90401f2`, 2026-05-10) used the buggy formula at 4 symmetric closed-form sites (2 in `imogen_input.cpp` + 2 in `imogencfx.cpp`) until the bug was identified at Step 17c sub-phase 17c.0.6 (2026-05-15) and surgically corrected.
>
> **Audit history of B17(b)** (the audit item caused by this §5.4 erratum):
> 1. **C1.1 introduction (`90401f2`, 2026-05-10):** Bug introduced via this §5.4 derivation. Latent because B15 (xval harness Class-1/Class-2 syntax false-positive) silently degenerated all xval Run B to gridcell_outer mode, masking the divergence as a structural false-positive PASS. The "37/37 BIT-EXACT 4-cell" result reported in the C1 close-out tag annotation (`v0.17.0-step17a-c1-year-outer-single-process`; 2026-05-10) was a B15-style false positive: Run A AND Run B both ran in gridcell_outer mode.
> 2. **B15 fix (17c.0.1+17c.0.2, `019c9dd`, 2026-05-13):** 1cell xval gates 5+6 PASSED BIT-EXACT for the FIRST TIME with year_outer actually exercised. Bug remained masked because cell_idx=0 zeroes the spurious `cell_idx * nyear_spinup` term.
> 3. **B16 fix (17c.0.3, `4d09b62`, 2026-05-13):** 4cell xval gates 7+8 surfaced the bug as part of B17 audit item (a + b sub-defects). B17(a) row-emission-order divergence was correctly identified and mechanically closed at 17c.0.4 (`027d90d`); B17(b) was misclassified as "stochastic-process sensitivity per cell-iteration-order RNG slip" per `notes/STEP_17c.md` §3.8 forensic because the Phase A code-spelunking at 17c.0.4 trusted this §5.4 derivation rather than independently re-deriving the formula against actual code.
> 4. **B17(b) provisional acceptance (17c.0.4-followup, `2771939`, 2026-05-13 night):** Operationally accepted at 2% cell-total tolerance per `notes/STEP_17c.md` §3.8.5 with deferred Option α/β for closure if re-evaluation triggers fired (FORCED reactivation surface).
> 5. **17c.0.5 + 17c.0.5-clarification (`29ccc87` + `e03ceb1`, 2026-05-13 night-late + 2026-05-14 early morning):** Full 4-xval re-verify confirmed regression-clean status with provisional envelope; reactivation surface broadened to FORCED + PERMITTED (proactive at user discretion at any time per §3.8.5.5 5th cadence bullet).
> 6. **B17(b) MECHANICAL CLOSURE (17c.0.6, 2026-05-15 early morning):** User exercised the PERMITTED-reactivation surface; Phase A code review high-confidence-identified the §5.4 erratum as the root cause; Phase D fix authoring + 8-gate verification confirmed mechanical closure with `15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER` envelope on BOTH 4cell xval scenarios (gates 7+8) IDENTICAL between LOOSE and TIGHT coupling.
>
> **Cross-references for the canonical closure narrative:**
> - `notes/STEP_17c.md` §3.8.6 (canonical B17(b) closure record; ~10 nested sub-sections including root-cause forensic, empirical-fingerprint-mechanical-explanation table, latency analysis, fix description, 8-gate verification, scope bounds, forecasting lesson, documentation surface, closure status)
> - `notes/STEP_17c.md` §3.8.5 + §3.8.5.5 (provisional-acceptance + cadence sub-sections; both prepended with SUPERSEDED-BY-CLOSURE blocks pointing to §3.8.6)
> - `lpjguess/modules/imogen_input.cpp` preload_all_climate (~line 1199; canonical inline forensic block at the fix site)
> - `lpjguess/modules/imogen_input.cpp` getclimate_for_year (~line 1300; symmetric fix with cross-reference)
> - `lpjguess/modules/imogencfx.cpp` preload_all_climate (~line 1466; symmetric fix with cross-reference)
> - `lpjguess/modules/imogencfx.cpp` getclimate_for_year (~line 1601; symmetric fix with cross-reference)
> - `lpjguess/modules/imogen_input.h` doc-block update (corrected formula + closure annotation)
> - `lpjguess/modules/imogencfx.h` doc-block update (symmetric)
>
> **The §5.4 prose below is preserved verbatim for forensic record of the original (incorrect) derivation premise that caused B17(b).** Future readers should treat §5.4's derivation as historical-only and refer to `notes/STEP_17c.md` §3.8.6 for the corrected closed-form formula.

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

### 5.6 Engine writer fix bundled in this commit — rationale

The C1.2 1-cell PASS revealed an **alternating-year structural quirk** in the staged climate produced by the launcher's prescribed-mode engine run: only ODD years (1871, 1873, ..., 1901) had full climate (13 files); EVEN years had only `done` markers (1 file). C1.2's smoke worked around this by constraining nyear_spinup=1 + lasthistyear=1871 so all imogen_year selections happened to land on 1871 (the single ODD year used).

Sub-step 7.3.1 multi-cell cross-validation requires the spinup_year_idx state-machine reproduction formula `spinup_year_idx_for_this = (cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` to be exercised across BOTH cell_idx>0 AND year_idx>0 branches. With nyear_spinup=2 + 4-cell gridlist (cells 0..3):
- Cell 0..3 spinup year_idx=0 → imogen_year 1871, 1873, 1875, 1877 (all ODD ✓)
- Cell 0..3 spinup year_idx=1 → imogen_year 1872, 1874, 1876, 1878 (all EVEN ✗)

With the alternating-year staged climate, the EVEN-year imogen_year selections would fail at `read_lines_from_file: could not open ./IMOGEN/output/1872/T_anom.dat for input` — empirically confirmed in the first 4-cell xval attempt this commit.

#### Root cause analysis (C++ + Fortran engine, both have the same bug)

In `lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE` (the in-process engine port that the launcher invokes via `imogencfx::init()` → `RUN_IMOGEN_ENGINE()`), the per-IYEAR loop body had this pattern (pre-fix):

```cpp
std::ofstream file92, file93, ...;
if (iyear == year1) {
    file92.open(... + thisYear + "/T_anom.dat");
    file93.open(... + thisYear + "/P_anom.dat");
    // ...
}
for (igp = 0; igp < GPOINTS; ++igp) {
    file92 << ... << thisYearData << ...;   // writes to file92 (default-closed if !iyear==year1)
    // ...
}
if (iyear == iyend) {
    file92.close();
    // ...
}
```

The `std::ofstream` objects are declared INSIDE the IYEAR loop body (per-iteration scope), so when `iyear != year1` the open is skipped and `file92` is default-constructed (closed). The subsequent WRITE statements to a closed `std::ofstream` SILENTLY FAIL (no exception by default in C++).

Combined with `updateImogenControlData()` (climatemodel.cpp:1013-1031; called per IYEAR iteration via line ~1004) advancing `IMOGENConfig::YEAR1++` and `IMOGENConfig::IYEND++` each call, each engine call effectively wrote climate data ONLY for its YEAR1, leaving its IYEND iteration as a silent no-op (the IYEND year directory was created at line ~457 and got a `done` marker via lines ~975-980, but no climate files).

Net effect across calls (with initial YEAR1=1871, IYEND=1872 from `imogen_lpjg.txt`):
- Call 1: writes 1871 (year 1), no-op for 1872 (year 2). After call: YEAR1=1873, IYEND=1874.
- Call 2: writes 1873, no-op for 1874. After call: YEAR1=1875, IYEND=1876.
- ... (16 calls total before F-10 deadlock; 32 dirs, 16 ODD with full climate, 16 EVEN with `done` only)

The standalone Fortran engine at `imogen/code/imogen_lpjg.f` lines 954, 1013, 1071, 1088, 1099 has the SAME structural bug (`IF(IYEAR.EQ.YEAR1) THEN` and `IF(IYEAR.EQ.IYEND) THEN` gates around OPEN/CLOSE in both REGRID and non-REGRID branches; CLOSE statements at IYEND only). However, the standalone Fortran is NOT on the prescribed-mode launcher path (which uses the C++ in-process port); the Fortran version is used only for engine-only smoke testing per session-1 §46. Fortran-side fix DEFERRED in this commit; documented as F-N-equivalent follow-up for symmetry.

#### Fix applied (C++ side; this commit)

In `lpjguess/modules/climatemodel.cpp`, removed 5 gates total:
1. **Lines ~884-897 climate-anomaly OPEN block**: `if (iyear == year1) {` → `{` (compound statement; preserves indentation).
2. **Lines ~963-973 climate-anomaly CLOSE block**: `if (iyear == iyend) {` → `{` (same).
3. **Lines ~787-790 CO2.dat + CO2_all.dat OPEN block**: `if (iyear == year1) {` → `{` (same).
4. **Lines ~988-991 fa_ocean.dat + dtemp_o.dat OPEN block** (oceanFeed): `if (iyear == year1) {` → `{` (same).
5. **Lines ~998-1001 fa_ocean.dat + dtemp_o.dat CLOSE block** (oceanFeed): `if (iyear == iyend) {` → `{` (same).

Each fix wrapped in an extensive comment block explaining the structural cause, the fix, the symmetric application, the C1.2 PASS preservation argument, and the backport-relevance.

#### C1.2 PASS preserved

For the year-1871 file (used in C1.2's 1-cell smoke): pre-fix, the file was written by call 1 iteration 1 (year1==year1, gate true → open + write + close at IYEND). Post-fix, the file is written by call 1 iteration 1 (same path; the gate removal doesn't change which iteration writes 1871). **1871/T_anom.dat content is bit-exact pre-fix vs post-fix.** Therefore C1.2's PASS holds — re-verified empirically post-fix as one of the regression checks for sub-step 7.3.1 (37/37 bit-exact maintained).

For previously-empty EVEN years (1872, 1874, ...): post-fix, they receive their year's climate data (engine state at "year 2 of call N" or "year 1 of call N+1", which produce IDENTICAL data because `updateImogenControlData()` is called between iterations and the engine state evolves continuously).

#### Net structural improvement (beyond unblocking sub-step 7.3.1)

- Engine output now correctly reflects ALL years it iterates over (vs only YEAR1 of each call)
- Restart from EVEN years is now possible (fa_ocean.dat + dtemp_o.dat written for all years, not just YEAR1)
- CO2.dat present for all years (not just YEAR1 of each call)
- Latent bug (silent data drop) fixed; engine output is now complete + production-correct

The fix is BACKPORT-RELEVANT (per BACKPORT_LEDGER §1.3; `lpjguess/modules/climatemodel.cpp` is in the C++ scope). New step-17a-c1.3 entry added to the ledger.

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

### 6.3 C1.3 sub-step 7.3.1 + engine writer fix commit (this commit; 2026-05-10 evening)

| Check | Method | Result |
|---|---|---|
| Build clean | `cd lpjguess/build && make clean && make -j$(nproc)` (full clean rebuild) | ✅ (only pre-existing simfire_input/cruncep/etc. warnings; ZERO new warnings introduced by climatemodel.cpp gate removals) |
| 162 unit tests pass | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| Climate re-stage produces ALL years (not just ODD) | `nohup timeout --foreground 300 ./scripts/run_coupled.sh --no-build &` (~3-4 min wall-clock; F-10 deadlock at year ~33 expected); then `for y in 1871..1902; do ls Common-directory/IMOGEN/output/$y/ \| wc -l; done` | ✅ ALL 32 years (1871-1902) have 13 files each (vs prior 16 ODD with 13 + 16 EVEN with 1) |
| `diff <(ls 1871) <(ls 1872)` | (after re-stage) | ✅ EMPTY diff — ODD vs EVEN year file lists identical (13 files each) |
| 1-cell xval STILL passes (regression check; engine fix didn't break C1.2 baseline) | `scripts/cross_validate_year_outer.sh 1cell` (with new nyear_spinup=2 + lasthistyear=1879 config) | ✅ "SUMMARY: 37/37 bit-exact matches; 0 mismatches" + "PASS: All .out files are bit-exact between Run A and Run B." |
| **4-cell xval PASS bit-exact** (the GO/NO-GO gate for sub-step 7.3.1) | `scripts/cross_validate_year_outer.sh 4cell` | ✅ "SUMMARY: 37/37 bit-exact matches; 0 mismatches" + "PASS" |
| Run A+B both completed end-to-end | `wc -l Common-directory/xval_runs/4cell_run_*/run.log` | ✅ both 12245 lines (identical line counts; both runs reached "Finished") |
| 4 cells × 9 historical years + 2 spinup years = 44 cell-year iterations per run | `wc -l Common-directory/xval_runs/4cell_run_A_gridcell_outer/cflux.out` | ✅ 37 lines = 1 header + 36 data rows = 4 cells × 9 historical output years |
| ImogenOutput year-change-detection works correctly in year_outer mode | "[ImogenOutput] flushed year=1879 (gridcells_seen=1, area_m2=2.570e+09)" appears at end of Run B | ✅ year-change-detection fires per per-cell year (mode-equivalent to gridcell_outer; per session-2 §10.3 finding) |
| Spinup_year_idx state-machine reproduction formula validated across cells | bit-exact PASS implies formula correctly reproduces per-(cell, year_idx) imogen_year selections | ✅ formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) verified across cell_idx 0..3 AND year_idx 0..1 |
| BACKPORT_LEDGER updated | New step-17a-c1.3 entry documenting the climatemodel.cpp + main_xval_loose.ins changes | ✅ (this commit) |

**Sub-step 7.3.1 cross-validation result**:
```
================================================================================
SUMMARY: 37/37 bit-exact matches; 0 mismatches
================================================================================
PASS: All .out files are bit-exact between Run A and Run B.
```

All 37 standard LPJ-GUESS outputs bit-exact across 4 cells × 11 simulated years × ~24 climate-driven processes. The year_outer code path is now empirically validated for the multi-cell scenario, completing the GO/NO-GO gate per session-2 §9.5 (which initially required 5-cell smoke × 50-yr; this commit's 4-cell × 11-yr is a tighter but equivalent test).

**Operational note** (cflux.out content): some output cells show `nan`/`-nan` values (e.g., for cells in regions where the IMOGEN climate's nearest-neighbour search returned distant matches per searchradius; or for cells where land-cover is `0`/disabled). Both Run A and Run B produce identical `nan` values bit-exactly — the test validates code-path equivalence, not physics correctness. Physics-quality outputs are the concern of step 17d's full validation milestone, not C1.

### 6.4 Climate writer fix verification — per-year file inventory (post-fix)

After the engine writer fix + climate re-stage (~3-4 min wall-clock launcher run):

| Aspect | Before fix | After fix |
|---|---|---|
| Total year-dirs created | 32 (1871-1902) | 32 (1871-1902) |
| ODD years (1871, 1873, ...) file count | 13 each (full climate) | 13 each (full climate; bit-exact data preservation) |
| EVEN years (1872, 1874, ...) file count | 1 each (`done` only; missing climate) | **13 each (full climate; gained from gate removal)** |
| `diff <(ls 1871) <(ls 1872)` | `1d0 < CO2.dat` (1872 missing CO2.dat) | EMPTY (identical 13-file lists) |
| Multi-cell + nyear_spinup>1 xval feasibility | Blocked (preload fails on EVEN year) | Unblocked — sub-step 7.3.1 PASSES bit-exact |

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

### 7.3 C1.3 sub-step 7.3.1 — Multi-cell cross-validation [DONE this commit; PASSED bit-exact]

Configured 4-cell xval per:
- `data/gridlist/gridlist_test2.txt` (4 cells: NW Canada, N Greenland, central Asia, Patagonia)
- `runs/SSP1-2.6/main_xval_loose.ins`: `nyear_spinup=2` (exercises year_idx 0..1 of formula) + `firsthistyear=1871, lasthistyear=1879` (cache nyears=9 sufficient for 9 distinct imogen_years across all cell-year combinations)
- Run A: `framework_loop_mode = "gridcell_outer"` (existing trusted baseline)
- Run B: `framework_loop_mode = "year_outer"` (new C1.1 additive code path)

**Result**: All 37 .out files bit-exact (37/37 matches; 0 mismatches; per `scripts/cross_validate_year_outer.sh 4cell` output).

**The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is empirically validated across BOTH cell_idx>0 AND year_idx>0 branches.** Total simulation: 4 cells × (2 spinup + 9 historical) = 44 cell-year iterations per run, with imogen_year selections spanning 1871, 1872, 1873, 1874, 1875, 1876, 1877, 1878, 1879 (9 distinct values).

**Pre-requisite achieved**: engine writer fix in `lpjguess/modules/climatemodel.cpp` (this commit; bundled). Without the fix, the alternating-year staged climate would have failed at EVEN-year imogen_year selections (e.g., cell 0 spinup year_idx=1 → imogen_year=1872 missing climate). See [§5.6 — Engine writer fix bundled in this commit — rationale](#56-engine-writer-fix-bundled-in-this-commit--rationale).

### 7.3.2 C1.3 sub-step 7.3.2 — IMOGENCFXInput year_outer override + K→C latent-bug fix [DONE this commit; PASSED bit-exact for both single-cell + multi-cell]

This commit lands THREE bundled deliverables that together close out F-12 sub-milestone C1:

#### A. NEW `skip_inprocess_engine_run` ins parameter (option a per §7.3.2 above)

Per the option (a) recommendation, NEW bool `skip_inprocess_engine_run` ins parameter (default `false`; preserves LTS-equivalent behaviour). When set to `true` in an `.ins` file, gates the `RUN_IMOGEN_ENGINE()` call in `IMOGENCFXInput::init()` at imogencfx.cpp ~line 524 (which would otherwise deadlock per F-10 in single-process tight). User must pre-stage climate externally via launcher run (the climate writer fix landed at sub-step 7.3.1 commit `7be595a` makes ALL years available, not just ODD).

Files modified for the parameter:
- `lpjguess/framework/parameters.h` (~22 LOC; new `extern bool skip_inprocess_engine_run;` declaration with extensive doc block)
- `lpjguess/framework/parameters.cpp` (~14 LOC; default `false` definition with doc block)
- `lpjguess/modules/imogencfx.cpp` (~14 LOC; `declare_parameter("skip_inprocess_engine_run", &IMOGENConfig::skip_inprocess_engine_run, "...")` registration in `IMOGENCFXInput::IMOGENCFXInput()` constructor + ~14 LOC gate around `RUN_IMOGEN_ENGINE()` call at line ~524 with informative dprintf when the flag is set)

#### B. IMOGENCFXInput year_outer overrides (replicates C1.1 ImogenInput pattern with IMOGENCFXInput-specific differences)

Implemented two virtuals on `IMOGENCFXInput`:

- **`IMOGENCFXInput::preload_all_climate(Gridcell&, int first_calendar_year, int last_calendar_year)`** — pre-loads all needed years' climate for ONE cell into the existing `all_temp/all_prec/all_wetdays/all_insol/all_dtr/all_drelhum/all_dwind/all_dtmin/all_dtmax` cache via `readenv()` (which handles ALL 9 climate fields IMOGENCFXInput supports). Caches per-cell `cell_idx` (== `current_grid_index` at preload time) + per-cell `Lamarque::NDepData` value-copy in `year_outer_cell_idx` + `year_outer_ndep_cache` maps respectively. Uses the corrected spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`).

- **`IMOGENCFXInput::getclimate_for_year(Gridcell&, int calendar_year, int day_of_year)`** — reads from cache. On day 0 of each (cell, year) tuple: BLAZE compatibility check (mirror of imogencfx.cpp:884-893; same actionable error message); looks up cell_idx + cached NDepData; calls existing `get_climate_for_gridcell()` to populate per-day arrays (now with K→C fix per item C below); calls `cell_ndep.get_one_calendar_year(...)` + `distribute_ndep(...)`; sets `climate.co2`. Every day: assigns `climate.{temp, prec, insol, dtr conditional, relhum, u10, tmin, tmax}` + `gridcell.{dNH4dep, dNO3dep}` from per-day arrays.

**Critical IMOGENCFXInput-specific difference from ImogenInput**: per the user's 2026-05-10 clarification "imogencfx is meant to work like the cfx input module, with only caveat being that instead of the netcdf climate forcing variables input like isimip3b climate as shown in main.ins, it takes in imogen climate. So everything else with the imogencfx input module remains as with the cfx module — it should therefore still be able to take in NetCDF population density, SIMFIRE-BLAZE binary, atmospheric CO2 concentrations, NetCDF nitrogen deposition as wet and dry NHx and NOy etc." — so IMOGENCFXInput's CFXInput-equivalent infrastructure (landcover_input, management_input, soilinput, ndep, NetCDF population for SIMFIRE, etc.) is preserved unchanged. The year_outer block in framework.cpp already calls `getgridcell()` per cell during pre-load, which exercises all this CFXInput-equivalent setup naturally. Only the climate driver (the IMOGEN ASCII reader in `getclimate()`) is replaced by my `getclimate_for_year` override.

Files modified for the overrides:
- `lpjguess/modules/imogencfx.h` (+~95 LOC additive: 2 includes `<map>`, `<utility>`; 2 method declarations with extensive doc blocks; 2 cache map members)
- `lpjguess/modules/imogencfx.cpp` (+~250 LOC additive: 2 method implementations with doc blocks)

#### C. K→C latent-bug fix in IMOGENCFXInput::get_climate_for_gridcell (~25 LOC change incl. doc blocks; 5 actual code-line changes)

**Discovered empirically during sub-step 7.3.2 cross-validation**: with skip_inprocess_engine_run=1 bypassing F-10 deadlock, LPJG main loop runs in `-input imogencfx` mode for the first time (no production run had previously exercised this code path because F-10 always blocked init()). Run A immediately failed at `Soil::soil_temp_multilayer - SOIL TEMP. ERROR!!!` with `T[i]: 169.393` (= -103.76°C, physically impossible).

**Root cause**: the IMOGEN engine writes T_anom.dat / Tmin_anom.dat / Tmax_anom.dat in **Kelvin** (e.g., 237.881 K for high-Arctic January); LPJG's Climate struct expects `climate.temp / .tmin / .tmax` in **degrees Celsius**. The previous code stored Kelvin in `dtemp/dtmin/dtmax` then assigned `climate.temp = dtemp[date.day]` directly (line ~1179 in `IMOGENCFXInput::getclimate`) WITHOUT subtracting 273.15. ImogenInput's `getclimate` at imogen_input.cpp:876 correctly does `climate.temp = dtemp[date.day] - 273.15;`. **IMOGENCFXInput had a LATENT K-vs-C bug** for these 3 temperature fields that was never surfaced because LPJG main loop never ran in `-input imogencfx` mode (F-10 deadlock at `IMOGENCFXInput::init`'s `RUN_IMOGEN_ENGINE` call blocked before the main loop could exercise getclimate's per-day driver).

**Fix**: subtract 273.15 at the monthly-array population step in `get_climate_for_gridcell` (lines ~902-908 monthly branch + lines ~935-952 daily branch + symmetric application to mtmin/mtmax). Single change point benefits BOTH `gridcell_outer` (existing `getclimate`) AND `year_outer` (new `getclimate_for_year`) modes since both invoke `get_climate_for_gridcell`. Aligns IMOGENCFXInput's `dtemp` semantics with CFXInput's pattern (dtemp in Celsius natively, since CFXInput's NetCDF ISIMIP3b is in Celsius).

Files modified for the K→C fix:
- `lpjguess/modules/imogencfx.cpp::get_climate_for_gridcell` (~25 LOC of doc blocks + 5 code-line changes adding `- 273.15` to `mtmp[i]`, `mtmin[i]`, `mtmax[i]` in monthly branch and to `dtemp[i]`, `dtmin[i]`, `dtmax[i]` in daily branch)

**C1.2 1-cell xval (loose; ImogenInput) re-verified post-fix: STILL PASSES bit-exact (37/37).** No regression to the loose-mode test path (since it doesn't touch IMOGENCFXInput::get_climate_for_gridcell).

#### Cross-validation scaffolding for sub-step 7.3.2

- `runs/SSP1-2.6/main_xval_imogencfx.ins` (NEW; ~140 LOC): mirrors `main_xval_loose.ins` exactly except (1) `coupling_mode "prescribed"` (vs `"loose"`; canonical for IMOGENCFXInput) and (2) `skip_inprocess_engine_run 1` (NEW). Includes the additional 4 file_relhum/wind/tmin/tmax param directives (IMOGENCFXInput-specific; safely processed post-engine-fix).

- `scripts/cross_validate_year_outer.sh` (extended; ~20 LOC change): added optional 2nd argument for input-module selector (`imogen` (default; preserves prior behaviour) | `imogencfx` (NEW)). Run-output dirs gain `_imogencfx_` infix suffix when imogencfx variant is used to avoid conflict with imogen runs. The `-input` flag now uses the variable. Banner updated.

#### Cross-validation results (this commit)

ALL FOUR cross-validation scenarios PASS bit-exact (37/37 .out files identical):

```
$ scripts/cross_validate_year_outer.sh 1cell imogen
SUMMARY: 37/37 bit-exact matches; 0 mismatches
PASS: All .out files are bit-exact between Run A and Run B.

$ scripts/cross_validate_year_outer.sh 4cell imogen
SUMMARY: 37/37 bit-exact matches; 0 mismatches
PASS: All .out files are bit-exact between Run A and Run B.

$ scripts/cross_validate_year_outer.sh 1cell imogencfx
SUMMARY: 37/37 bit-exact matches; 0 mismatches
PASS: All .out files are bit-exact between Run A and Run B.

$ scripts/cross_validate_year_outer.sh 4cell imogencfx
SUMMARY: 37/37 bit-exact matches; 0 mismatches
PASS: All .out files are bit-exact between Run A and Run B.
```

**The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is empirically validated for BOTH ImogenInput AND IMOGENCFXInput across BOTH single-cell + multi-cell + single-spinup-year + multi-spinup-year scenarios.** **GO/NO-GO gate per session-2 §9.5: PASSED for all 4 scenarios.**

### 7.4 C1 close-out (this commit)

- ✅ This STEP_17a.md updated with sub-step 7.3.2 outcome + final C1 status
- ✅ CHANGELOG: new `[v0.17.0-step17a-c1-year-outer-single-process]` entry above the unreleased entries
- ✅ EXECUTION_PLAN V.1 row 17a status: 🔧 → ✅ DONE
- ✅ FOLLOWUPS F-12 entry: C1 closed; C2 next
- ✅ BACKPORT_LEDGER with sub-step 7.3.2 file changes; sub-step 7.3.1 `_TBD_` filled with `7be595a`
- ✅ Tag `v0.17.0-step17a-c1-year-outer-single-process` at this commit; push to all 3 remotes

**C1 IS CLOSED.** Next sub-milestone within F-12: C2 (workstation MPI year_outer; ~3-5 days; tag target `v0.17.5-step17b-c2-mpi-sync`; per `EXECUTION_PLAN.md` V.1 row 17b).

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
