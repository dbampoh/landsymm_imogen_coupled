# Block 8.2.4 — Forward-port plan: bring `forks/trunk_r13078/` C++ IMOGEN engine to feature-parity with `lpjguess/` for v1.0 paper Track 2

**Date authored**: 2026-05-24 (session 11 day 1; Claude Opus 4.7 session-11 agent)

**Status**: ⏳ PHASE A INSPECTION COMPLETE; awaiting user approval before Phase B-D source-edit execution

**Scope**: Forward-port the engine-side slice of LEDGER §1.2 Installment-2 (~1300 LOC substantive) into `forks/trunk_r13078/` so that trunk's `build/guess --engine-only-mode` produces functionally equivalent C++ IMOGEN engine output to rebuild's `lpjguess/build/guess --engine-only-mode`. Goal: trunk_r13078's own engine produces the v1.0 paper Track 2 climate library at `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/`, enabling the methodological story "trunk_r13078 throughout: engine + LPJG + natural-emission preprocessor" (vs the current state where rebuild's engine output is cp'd into trunk-runs/ at Phase E γ-physical separation per block 8.2's accepted-but-now-superseded plan).

**Motivation (per user direction 2026-05-24)**: trunk_r13078 is what was used to produce the pre-baked LPJG natural-emission outputs feeding intermediary_py Component B (per `notes/B51.md` provenance + `intermediary_py/imogen_ghg_controller/inputs/lpjg/` ~1.5 GB). For paper methodological consistency + reviewer defensibility, the IMOGEN engine producing the climate forcing should ALSO be on trunk_r13078's fork lineage, not rebuild's. The rebuild's lpjguess fork remains the active v1+ development surface; the full bidirectional Installment-2 fork-parity reconciliation (the year_outer + `imogen_input.cpp` + Fortran B33(c) residual) remains the post-paper Backport Sprint target.

---

## §0 Scope decisions (architectural; key Rule #7 + #11 + #13 calls)

### §0.1 What block 8.2.4 includes (in-scope; "engine-slice of Installment-2")

| Module | Source | Forward-port scope | Effort |
|---|---|---|---|
| `forks/trunk_r13078/modules/climatemodel.cpp` | lpjguess/modules/climatemodel.cpp | ~220 substantive LOC across 22 hunks; engine-side step-7/8/9.5/17a + B19/B37/B39/B44/B45 deltas; zero year_outer entanglement | ~0.5-1 d |
| `forks/trunk_r13078/modules/imogenoutput.cpp` (NEW) | lpjguess/modules/imogenoutput.cpp | 599 LOC NEW file; cp wholesale; minor adaptation if any `#include` paths differ | ~0.25-0.5 d |
| `forks/trunk_r13078/modules/imogenoutput.h` (NEW) | lpjguess/modules/imogenoutput.h | 222 LOC NEW file; cp wholesale | ~0.1 d |
| `forks/trunk_r13078/modules/imogencfx.cpp` | lpjguess/modules/imogencfx.cpp | ~150-200 substantive LOC across 12 of 13 hunks (excluding the last ~444-LOC hunk which is year_outer scaffolding implementation = DEFERRED); step-8 imogenoutput dispatch + step-9.5 8-field wiring + step-17a engine writer fix + B19/B37/B39/B44 deltas | ~1-1.5 d |
| `forks/trunk_r13078/modules/imogencfx.h` | lpjguess/modules/imogencfx.h | ~30 substantive LOC (excluding year_outer additions: preload_all_climate decl + getclimate_for_year decl + year_outer_*_cache maps + `<map>` + `<utility>` includes = DEFERRED); cosmetic comment cleanup + KEEP TRUNK'S `FIRST_SPINUP_YEAR = 1900` (block 8.0.3 B49 fix; DO NOT revert to lpjguess's 1871) | ~0.25 d |
| `forks/trunk_r13078/framework/parameters.h` | lpjguess/framework/parameters.h | ~15 substantive LOC: ADD `coupling_mode` (xtring; step-8); RELOCATE `skip_inprocess_engine_run` from Installment-1 position (line ~501) to canonical step-17a position (line ~511+) with refined documentation; DEFER `framework_loop_mode` declaration (year_outer-only) | ~0.25 d |
| `forks/trunk_r13078/framework/parameters.cpp` | lpjguess/framework/parameters.cpp | ~15 substantive LOC: ADD `xtring coupling_mode = "tight";`; RELOCATE `skip_inprocess_engine_run = false;` to canonical step-17a position with refined documentation; DEFER `xtring framework_loop_mode = "gridcell_outer";` declaration; ADD cosmetic `xtring` comment enhancements (harmless tidying) | ~0.25 d |
| `forks/trunk_r13078/modules/CMakeLists.txt` | lpjguess/modules/CMakeLists.txt | 2 LOC: add `imogenoutput.h` to header set + `imogenoutput.cpp` to source set | trivial |

**Total in-scope LOC**: ~1245-1305 substantive LOC + 2 NEW files.

### §0.2 What block 8.2.4 DEFERS to v1+ Installment-2 residual

| Item | Reason for deferral | Affects |
|---|---|---|
| `framework_loop_mode` parameter declaration + year_outer additive block in `framework/framework.cpp` | Paper Track 2 uses `gridcell_outer` (default); year_outer is the F-12 tight-coupling resolution mechanism, not paper-blocking | `framework/framework.cpp` ~400 LOC + parameter |
| `IMOGENCFXInput::preload_all_climate` + `IMOGENCFXInput::getclimate_for_year` virtual overrides in imogencfx.{cpp,h} | Same reason (year_outer-only entry points); InputModule base class virtuals will simply not be called when framework_loop_mode = gridcell_outer | imogencfx.cpp ~444 LOC + imogencfx.h ~50 LOC + `<map>` + `<utility>` |
| `year_outer_cell_idx` + `year_outer_ndep_cache` map members in imogencfx.h | Member layout; only accessed by deferred methods above | imogencfx.h ~10 LOC |
| `imogen_input.cpp` + `imogen_input.h` deltas (~642 LOC substantive) | Paper Track 2 uses `-input imogencfx`, not `-input imogen` | imogen_input.{cpp,h} entire delta |
| Fortran `imogen/code/imogen_lpjg.f` step-3 ALLOCATABLE + B10 + B33(c) deltas | Already in rebuild + shared across forks (Fortran tree is fork-shared per LEDGER §1.3); trunk inherits these automatically; no action needed at trunk side | none (already shared) |

**Note on year_outer deferral safety**: The `InputModule::preload_all_climate` + `InputModule::getclimate_for_year` base-class virtuals were added at the step-17a C1 foundation step in lpjguess. Trunk's `InputModule` does NOT yet have these virtuals declared. So trunk's `IMOGENCFXInput` doesn't need to override them — they don't exist. This means trunk's existing `IMOGENCFXInput::getclimate()` (gridcell_outer mode entry point) remains the sole climate-supply path, which is exactly what paper Track 2 uses. ZERO LOC change needed for this deferral; the absence of year_outer scaffolding in trunk is the natural state.

### §0.3 Honest Rule #10 disclosure on scope-vs-Installment-2

This block effectively executes **~80% of LEDGER §1.2 Installment-2's ~2900-3100 LOC scope**. The residual ~600-1000 LOC for v1+ Backport Sprint is:
- year_outer scaffolding in framework.cpp + imogencfx.{cpp,h} (~500 LOC; F-12 tight-coupling prerequisite)
- imogen_input.cpp + imogen_input.h deltas (~640 LOC; `-input imogen` mode; non-paper-blocking but completes consumer-side fork-parity)
- `miscoutput.h` delta (small; per LEDGER step 8 §366)
- Cleanup of any cosmetic ImogenLogger refactor differences not strictly needed for byte-identity

Per Rule #10 amendment-vs-rewrite: B61's original framing as "~263 LOC climatemodel.cpp engine-side delta" is now refined to "~1300 LOC engine + ImogenOutput + imogencfx step-8/9.5/17a slice = ~80% of Installment-2"; the LEDGER §1.2 + B61 entries will be updated in the doc cascade at Phase H close.

---

## §1 Phase B-D source-edit execution order (commit-cascade plan)

The work is decomposed into 4 commit-bundled phases with clear pass/fail gates between each. **Each phase ends with a build verification** (Rule #9 datapoint pattern: harness-authoring surfaces latent defects).

### §1.1 Phase B — Foundation: parameters + CMakeLists + imogenoutput NEW files (~0.5 d)

**Sub-edits**:
1. `forks/trunk_r13078/framework/parameters.h` — relocate `skip_inprocess_engine_run` + ADD `coupling_mode` declaration (see diff_parameters_h_trunk_to_lpjguess.diff; ~15 LOC substantive)
2. `forks/trunk_r13078/framework/parameters.cpp` — relocate `skip_inprocess_engine_run` + ADD `coupling_mode = "tight"` (see diff_parameters_cpp_trunk_to_lpjguess.diff; ~15 LOC substantive)
3. `cp lpjguess/modules/imogenoutput.h forks/trunk_r13078/modules/imogenoutput.h` (verify `#include` paths match trunk's `config.h` + `framework/guess.h` layout)
4. `cp lpjguess/modules/imogenoutput.cpp forks/trunk_r13078/modules/imogenoutput.cpp` (verify same `#include` paths)
5. `forks/trunk_r13078/modules/CMakeLists.txt` — add `imogenoutput.h` to headers + `imogenoutput.cpp` to sources (see diff_modules_CMakeLists.diff; 2 LOC)

**Phase B build verification gate**:
- `cd forks/trunk_r13078 && mkdir -p build_b824 && cd build_b824 && cmake .. -DCMAKE_EXE_LINKER_FLAGS="-lcurl" && make -j$(nproc)`
- Expect: clean build of imogenoutput.{cpp,h} + linker succeeds (no missing symbols)
- Stage-A artifact: `_chat_artifacts/b8_2_4_trunk_engine_forwardport_2026-05-24/phase_b_build.log`

### §1.2 Phase C — Engine surgery: climatemodel.cpp + imogencfx.{cpp,h} (~1.5-2 d)

**Sub-edits** (in this order; each sub-edit anchored to a specific diff hunk; non-year-outer slice only):
1. `forks/trunk_r13078/modules/climatemodel.cpp` — apply 22 hunks per diff_climatemodel_cpp_trunk_to_lpjguess.diff (~220 substantive LOC; engine logic; step-7 polling guards + step-8 imogenoutput integration + step-9.5 8-field writers + step-17a engine writer fix + B19/B37/B39/B44/B45 deltas)
2. `forks/trunk_r13078/modules/imogencfx.h` — apply non-year_outer hunks per diff_imogencfx_h_trunk_to_lpjguess.diff (~30 substantive LOC; cosmetic comment cleanup; KEEP TRUNK'S `FIRST_SPINUP_YEAR = 1900` per B49)
3. `forks/trunk_r13078/modules/imogencfx.cpp` — apply hunks 1-12 of 13 per diff_imogencfx_cpp_trunk_to_lpjguess.diff (~150-200 substantive LOC; SKIP the last `@@ -1259,6 +1306,444 @@` hunk = year_outer scaffolding implementation = DEFERRED)

**Phase C build verification gate**:
- Re-build trunk binary: `cd forks/trunk_r13078/build_b824 && make -j$(nproc)`
- Expect: clean build + linker succeeds
- Stage-A artifact: `phase_c_build.log`
- **Pre-flight sanity smoke**: invoke `forks/trunk_r13078/build_b824/guess` with no args (expect standard `Usage:` banner emission); confirms binary is operational

### §1.3 Phase D — Workstation engine canary test on SSP1-2.6 (~0.5 d wall on workstation)

**Setup**:
- Author `scripts/run_trunk_engine_only.sh` adaptation OR re-purpose existing `scripts/run_trunk_engine_only.sh` from block 8.2 phase F v1+ groundwork (which polls for done marker — should now work since trunk has step-7 polling guards + B37 done-marker sidecar mechanism via the path-iv sidecar)
- Backup current `forks/trunk_r13078_runs/SSP1-2.6/Common-directory/IMOGEN/output/` → rename to `Common-directory_pre_block_8_2_4_lpjguess_cp_reference/` (preserves Phase E cp'd reference for Phase G byte-identity verification)
- Use `forks/trunk_r13078_runs/SSP1-2.6/main_engine_only.ins` (already authored at block 8.2 phase F)
- Spawn path-iv done-marker sidecar (mimics scripts/run_coupled.sh --engine-only-mode pattern)
- Invoke: `forks/trunk_r13078/build_b824/guess -input imogencfx forks/trunk_r13078_runs/SSP1-2.6/main_engine_only.ins`

**Phase D acceptance gate**:
- Expect: 202 year-dirs (1900-2101) created at `forks/trunk_r13078_runs/SSP1-2.6/Common-directory/IMOGEN/output/`; 443 MB; ~12-15 min wall (matching rebuild's engine timing on same workstation)
- Stage-A artifact: `phase_d_ssp126_run.log`

### §1.4 Phase E — 5-SSP engine library production with trunk's binary (~1.5 h wall on workstation; 5x serial OR 5-way parallel)

For each of {SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5}:
- Backup existing Common-directory (Phase E cp'd from block 8.2) to `Common-directory_pre_block_8_2_4_lpjguess_cp_reference/`
- Invoke trunk engine via `scripts/run_trunk_engine_only.sh <SSP>` (adapted from block 8.2 phase F wrapper)
- Verify 202 year-dirs / 443 MB / physically sensible CO2 trajectory per IPCC AR6 / Friedlingstein 2025 GCB (same gates as block 8.2 Phase D acceptance)

**Phase E acceptance gate**:
- All 5 trunk-runs/<SSP>/Common-directory/IMOGEN/output/ are NOW PHYSICALLY trunk-engine-produced
- 8-gate acceptance scorecard mirroring block 8.2 §2.1 (G0-G7 + new G8 for byte-identity)
- Stage-A artifact: per-SSP run logs

---

## §2 Phase G — Byte-identity verification + paper-defensibility evidence

**Phase G.1 byte-identity canary** (SSP1-2.6 first; ~5 min):
- `md5sum forks/trunk_r13078_runs/SSP1-2.6/Common-directory/IMOGEN/output/<year>/*.dat` vs `runs/SSP1-2.6/Common-directory/IMOGEN/output/<year>/*.dat` for sentinel years {1900, 1950, 2000, 2050, 2100}
- **Expected**: BYTE-IDENTICAL across all sentinel-year files (T_anom.dat, P_anom.dat, SW_anom.dat, DTEMP_anom.dat, Rh_anom.dat, W_anom.dat, Tmin_anom.dat, Tmax_anom.dat, WET.dat, CO2.dat, done) since both forks now compile the same engine logic from the same source-of-truth (lpjguess) with the same intermediary_py adapter inputs
- If NOT byte-identical: investigate at Rule #9 datapoint (likely cause: missed delta, subtle init order, compiler optimisation differences)

**Phase G.2 physical-sensibility cross-check** (~10 min):
- Compare CO2 trajectories at YEAR 2050 + YEAR 2100 between forks for all 5 SSPs
- Expected: 100% match (since byte-identity already established at G.1)
- Stage-A artifact: `phase_g_byte_identity_table.md`

**Phase G.3 paper-defensibility evidence**:
- Document that block 8.2.4 brings the two forks' C++ IMOGEN engines to byte-identical functional parity (within the in-scope ~1300 LOC slice)
- Methods §2.2 (per `notes/PAPER_COMPLETION_AND_VALIDATION.md` §4.5) updated at Phase H doc cascade: "We built two C++ IMOGEN engine implementations of the same lineage in the rebuild's `lpjguess/` and trunk_r13078 forks; byte-identity of engine output across all 5 SSPs verified at block 8.2.4. Production climate libraries are generated by trunk_r13078's engine (per fork-consistency criterion); rebuild's engine output serves as redundant cross-validation reference. The rebuild fork remains the active v1+ development surface."

---

## §3 Phase H — Audit-evidence bundle + commit + tag candidate

**Audit-evidence bundle**: `_chat_artifacts/b8_2_4_trunk_engine_forwardport_2026-05-24/`:
- `B8_2_4_forward_port_plan.md` (THIS DOC; Phase A inspection + plan; ~300 LOC)
- `B8_2_4_evaluation_2026-05-XX.md` (Phase H close evidence; ~250 LOC; 8-gate acceptance scorecard + byte-identity table + Rule #9/#10 datapoints + scope-vs-Installment-2 honest disclosure)
- `diff_*.diff` × 7 (Phase A captured diffs)
- `phase_{b,c,d,e,g}_*.log` (per-phase verification logs)
- `phase_g_byte_identity_table.md` (canary table)

**Doc cascade (post-implementation per user direction; bundled in Phase H close commit)**:
1. `notes/FOLLOWUPS.md` dashboard top + B61 closure entry (move to CLOSED with concrete artifact citations)
2. `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 NEW "Block 8.2.4 LANDED" entry + §1.2 Installment-2 LOC accounting refinement
3. `CHANGELOG.md` [Unreleased] block 8.2.4 entry + 8-gate scorecard + Rule #9/#10 datapoints
4. `EXECUTION_PLAN.md` row 17c block 8.2.4 LANDED update
5. `notes/STEP_17c.md` §1.7.8 (latest entries) — NEW block 8.2.4 entry
6. `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1.4 + §4.5 Methods §2.2 update (trunk engine throughout framing)
7. `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §1 — block 8.2.4 LANDED + new POST-8.2.4 operational ordering (block 8.2.5 unblocked; δ-B-variant FastRegrid input source now `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/`)
8. `forks/README.md` + `forks/trunk_r13078_runs/README.md` — engine-side fork parity reached at block 8.2.4 (Installment-2 residual = year_outer + imogen_input + Fortran B33(c))

**Commit message draft** (assistant-drafted; user runs `git add` + `commit` + `push` + `tag` per Rule #3): tba at Phase H close.

**Tag candidate**: `v0.23.0-trunk-engine-forwardport-complete` (annotated; engine-side Installment-2 slice LANDED; ~1300 LOC forward-port).

---

## §4 Risk register + Rule #9 mitigations

| Risk | Mitigation |
|---|---|
| Hidden dependency on year_outer code (caller not present in trunk causes compile error) | Phase A confirmed: trunk's `InputModule` does NOT have year_outer virtuals; trunk's framework.cpp does NOT have year_outer additive block; defer scaffolding is structurally clean |
| `imogenoutput.{cpp,h}` `#include` paths might differ between forks (rebuild's `lpjguess/` vs trunk's `forks/trunk_r13078/`) | Phase B sub-edit 3-4 explicitly verifies; minor adjustment expected; harness-authoring will surface any mismatch (Rule #9 #19 pattern) |
| Reverting trunk's B49 `FIRST_SPINUP_YEAR=1900` to lpjguess's `1871` would break trunk's LPJG consumer at spinup (file-not-found for engine library 1871-1899) | Explicit DECISION: KEEP trunk's 1900; do NOT revert |
| Byte-identity might NOT hold across all 5 SSPs (e.g., compiler optimisation differences, ABI subtleties) | Phase G accepts physical-sensibility-match as fallback; if byte-identity fails on a single SSP, investigate; if all 5 SSPs show same physical CO2 trajectories within numerical tolerance (~1e-6 ppm), accept as functional parity |
| Forward-port surfaces a latent defect in lpjguess's engine code (Rule #9 #19 pattern) | Mitigation = Rule #11 meticulous execution; if defect surfaces, file as NEW B-row + decide whether to fix at block 8.2.4 or defer to v1+ |
| Workstation engine time for 5 SSPs is ~1.5 h wall serial; we could parallelize 5-way but might OOM | Block 8.2 phase D succeeded with 3-way parallel + 2 serial; same pattern works here |

---

## §5 What this plan does NOT do (out-of-scope; will not be touched at block 8.2.4)

- Anything in `imogen/code/imogen_lpjg.f` (Fortran tree; fork-shared per LEDGER §1.3; no fork-specific changes needed)
- Anything in `intermediary_py/` (Python pipeline; both forks share)
- Anything in `lpjguess/` (rebuild fork; unchanged; remains canonical active v1+ dev surface)
- Anything in `runs/<SSP>/` (rebuild engine output; unchanged; remains as redundant cross-validation reference for paper)
- Anything in `imogen_input.{cpp,h}` (paper uses `-input imogencfx`; v1+ Backport Sprint)
- Anything in `framework/framework.cpp` year_outer additive block (F-12 tight-coupling; v1+ Backport Sprint)
- Anything in `forks/trunk_r13078/`'s 5 cosmetic baseline-diff files (LEDGER §2; reserved for v1+ Backport Sprint reconciliation)

---

_End of B8_2_4_forward_port_plan.md_
