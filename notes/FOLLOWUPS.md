# Pending follow-ups (non-blocking)

Action items that came out of the rebuild steps but aren't blocking
the next step. Tracked centrally here so nothing falls through the
cracks. Each item lists: the **trigger** (which step / decision raised
it), the **action** to take, and the **suggested timing** (when it
ought to be done).

When an item is closed, move it from the **OPEN** section to **DONE**
with the closing date. Do not delete; the audit trail is valuable.

---

## Status dashboard (at-a-glance; updated at end of every step)

**Last updated:** 2026-05-13 (afternoon; session 4; **17c.0.1 + 17c.0.2 B15 FIX + SIGNAL-OF-LIFE ASSERTION + FOUR-XVAL RE-VERIFICATION LANDED — Step 17c.0 PREP sub-phases 17c.0.1 + 17c.0.2 bundled per `notes/STEP_17c.md` §1's plan**) — F1+F2+F3+F4 (per-fork harness + ins; backport-IRRELEVANT) + F5 (C++ runtime diagnostic in `lpjguess/framework/framework.cpp:339-357`; backport-RELEVANT) per the §0.8 design approved verbatim in session 4 with user-authorised F5 inclusion. **B15 (class-mismatch defect; the C1+C2 false-positive harness root cause) is CLOSED**: F1+F2 land bare-keyword `framework_loop_mode "..."` syntax in the two `runs/SSP1-2.6/main_xval_*.ins` files; F3 lands the same in the harness wrapper-writer at `scripts/cross_validate_year_outer.sh:138`; F4 lands the rule-#8 signal-of-life banner-presence assertion in `compare_outputs()` (greps both run.logs for `\[year_outer\]` banner emitted at `framework.cpp:502`; pass requires `banner_a == 0` AND `banner_b >= 1`; failure exits with new exit code **4** non-overlapping with existing 0/1/2/3); F5 lands the consumer-side ~3-LOC `dprintf` echo of `IMOGENConfig::framework_loop_mode` immediately after `read_instruction_file()` returns, closing the §0.6(3) consumer-side observability gap. **Strategy**: hybrid stash cherry-pick of `stash@{0}` for F1-F4 (per `notes/STEP_17c.md` §0.12's "individual hunks" provision; the WIP narrative comments aligned precisely with §0.5's plib-parser walkthrough; saves ~1 h doc-writing time and preserves a non-trivial bash-`grep -c` defensive pattern); fresh authorship for F5 against §0.5 + §0.8(F5) canonical citations. Cosmetic anchor-text touch-up `§0.B15` → `§0 (audit item B15)` at 6 sites (the literal `§0.B15` was a non-existent anchor; preserves the B15 association while pointing to the actual section anchor). The two C++ B16 stash hunks (`lpjguess/modules/imogen_input.cpp` +35/-9 + `lpjguess/modules/imogencfx.cpp` +29/-11) **NOT applied** — remain in `stash@{0}` as starting material for sub-phase 17c.0.3. Net code diff: **+171 / −5** across 4 files. **Verification gates 1-4 (clean rebuilds + unit tests) ALL PASS**: `lpjguess/build/` rebuild ZERO warnings; `lpjguess/build_mpi/` rebuild ZERO warnings; 25 cases / 162 assertions PASS on both. **Verification gates 5-8 (four-xval re-verification — THE substantive 17c.0.2 evidence)**: 1cell scenarios PASS substantive + signal-of-life clean (gate 5 `1cell imogen` rc=0 / 37/37 bit-exact / 0 NaN / banner_a=0 / banner_b=5 / F5 echoes "gridcell_outer" + "year_outer"; gate 6 `1cell imogencfx` same metrics) — **the first time the year_outer code path has actually been exercised in any cross-validation since C1 close-out** (`v0.17.0-step17a-c1-year-outer-single-process` 2026-05-10); 4cell scenarios surface **B16 textbook-exactly per `notes/STEP_17c.md` §0.9** (gate 7 `4cell imogen` rc=99 with `"ImogenInput::preload_all_climate: stored_years cache already full (last_store_index=9 >= nyears=9) when preloading cell (-95.75,80.25)"`, banner_a=0/banner_b=3 — year_outer started + 3 setup banners then aborted at preload; gate 8 `4cell imogencfx` symmetric `IMOGENCFXInput::preload_all_climate` same fail at same cell; both modules; same numerics; same fault site `cell_idx=1`) — **positive empirical evidence** that B15 is genuinely fixed (year_outer reaches `preload_all_climate` for the first time across `cell_idx >= 1`) and that B16 surfaces exactly as predicted. This is the canonical input data point for sub-phase 17c.0.3 (B16 forensic + fix). **Backport classification**: F1-F4 IRRELEVANT (per-fork cluster config + harness; not in `trunk_r13078`); F5 RELEVANT (`framework.cpp` exists in `trunk_r13078`; `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17c-17c.0.1 entry captures the F5 backport directive). 6-file source-level cascade (F5 RELEVANT classification triggers full cascade): STEP_17c.md §1.1 NEW landing record + CHANGELOG.md NEW dated entry + EXECUTION_PLAN.md row 17c update + this status dashboard refresh + TRUNK_R13078_BACKPORT_LEDGER.md step-17c-17c.0.1 entry + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 2 NEW. **Step 17c.0 PREP status post-this-commit**: 17c.0.0 + 17c.0.1 + 17c.0.2 ✅ DONE; 17c.0.3 (B16 forensic + fix) NEXT (~0.5-1 d; empirically triggered by gates 7+8); 17c.0.4 (4-xval re-verify on B15+B16-fixed HEAD; ~0.5 d) → 17c.0.5 (C2 close-out tag annotation amendment per `notes/STEP_17c.md` §0.11; ~0.2 d) → 17c.0.6 (workstation `mpirun -np 4` mimic; deferred-from-C2 obligation; ~1 d) → 17c.0.7 (PREP close-out; ~0.2 d). Total remaining 17c.0 PREP: ~2.5-3.5 d. **Operational heuristics**: no new rules surface; rule #8 (added in 17c.0.0) is now operationally validated — F4 implements it verbatim and would have surfaced B15 immediately at C1 close-out had it existed then. v1.0 % done estimate held at ~62-65% (this commit closes the B15 false-positive but doesn't unblock substantive 4cell year_outer until 17c.0.3 closes B16; the year_outer-actually-exercised milestone for 1cell cases is the meaningful step-forward). Full forensic + landing chain in `notes/STEP_17c.md` §1.1 (NEW; ~190 LOC).

**Prior dashboard entry preserved for context (2026-05-12 afternoon-evening; session 3; 17c.0.0 B15+B16 FORENSIC RECORD LANDED — Step 17c.0 PREP first sub-phase; forensic-only; ZERO source change; NEW rule #8):** Comprehensive forensic write-up of two audit items surfaced during session-3 onboarding audit of the C2 close-out tag at `f6c192e`. **B15 (class-mismatch defect; xval harness false-positive)**: the `framework_loop_mode` parameter — declared via `declare_parameter("framework_loop_mode", &IMOGENConfig::framework_loop_mode, 20, ...)` at `lpjguess/modules/imogencfx.cpp:353` + `lpjguess/modules/imogen_input.cpp:214` (Class 1; bound to a C++ `xtring` variable; consumed via direct C++ variable read at `lpjguess/framework/framework.cpp:464`) — was being set in the xval harness wrapper-writer (`scripts/cross_validate_year_outer.sh:138`) and the imported xval base ins (`runs/SSP1-2.6/main_xval_imogencfx.ins:176`) using **Class-2 syntax** (`param "framework_loop_mode" (str "$mode")`), which writes only to the global `Paramlist param[...]` dictionary and **never touches** the C++ variable. Result: the gate at `framework.cpp:464` always evaluated false; **all four C1+C2 xval scenarios silently ran in `gridcell_outer` mode in BOTH Run A and Run B**; the "PASS substantive 37/37 bit-exact + 0/37 NaN" reports at C2 close-out were false positives. Three independent evidence streams converge on the class-mismatch root cause: (1) empirical reproduction on clean HEAD `f6c192e` after stashing all WIP (Run A and Run B `run.log` sha256-byte-identical at `43c278b0…`; combined `.out` sha256 identical at `ab23ea80…`; zero `[year_outer]` banners in Run B; both runs show 11 `[F-10 caveat: per-gridcell-rolling]` flushes — the gridcell_outer signature); (2) `plib` parser source-level forensic showing `param "key" (str "value")` → `CB_STRPARAM` → `param.addparam(...)` → `Paramlist param[...]` only; bare-keyword → `declareitem(name, &cppvar, ...)` → `Plibitem` of type `PLIB_XTRING` → C++ variable directly; storage paths mechanically disjoint with zero cross-update; (3) canonical pattern from `version_A/`+`version_B/` reference setups (strict two-class convention: Class 1 takes bare-keyword syntax; Class 2 takes param-block syntax). **B16 (latent eager cache-fullness check; downstream of B15)**: `ImogenInput::preload_all_climate` + `IMOGENCFXInput::preload_all_climate` contain `if (last_store_index >= nyears) fail("...: stored_years cache already full ...")` at function entry; mis-models the `stored_years` cache as per-cell when the actual design intent (per inner cache-miss-branch comments) is cumulative-across-cells. The check fires on entry to `cell_idx >= 1` even when the cell needs zero new slots. Latent since C1.3 sub-step 7.3.2 (commit `d7f6c74`, 2026-05-10); undetected because B15 silently prevented `year_outer` from ever executing. **Recommended B15 fix (deferred to subsequent commit; forensic-record-this-commit only)**: F1 (`runs/SSP1-2.6/main_xval_imogencfx.ins:176` Class-2→Class-1 syntax) + F2 (`runs/SSP1-2.6/main_xval_loose.ins:182` symmetric) + F3 (`scripts/cross_validate_year_outer.sh:138` wrapper-writer Class-2→Class-1) + F4 (signal-of-life banner-presence assertion in `compare_outputs()` per **rule #8**) + optional F5 (~3 LOC C++ runtime diagnostic). All forensic-only; ZERO `lpjguess/` or `imogen/code/` source change in this commit. **NEW persistent operational heuristic rule #8** added below: signal-of-life banner-presence assertion for every code-path-gated cross-validation. Step 17c.0 PREP revised 5→8 sub-phases: 17c.0.0 (this commit; forensic record) → 17c.0.1 (B15 fix; NEXT) → 17c.0.2 (4-xval re-verify on B15-fixed HEAD) → 17c.0.3 (B16 forensic + fix; gated on 17c.0.2 surfacing the failure on 4cell) → 17c.0.4 (4-xval re-verify on B15+B16-fixed HEAD) → 17c.0.5 (C2 close-out tag annotation amendment decision; option a/b/c per `notes/STEP_17c.md` §0.11) → 17c.0.6 (workstation `mpirun -np 4` mimic verification; deferred-from-C2 obligation) → 17c.0.7 (PREP phase close-out). Total revised PREP estimate: ~3.5-5 d (was ~0.5-1 d). C3-era estimate still ~1-2 weeks SSH-iterative cluster work. v1.0 % done estimate held at ~62-65% (this commit is doc-only; substantive progress comes in 17c.0.1+). Backport-IRRELEVANT (forensic record only). Forensic at `notes/STEP_17c.md` §0 (full B15 + B16 forensic + fix design + rule #8 + PREP plan).

**Prior dashboard entry preserved for context (2026-05-12 early morning session 3 continuation; B1 LANDED — LAST AUDIT ITEM; C2-era B-BUNDLE COMPLETE):** Fortran-engine Rh + Wind COMPUTATION + write-block port landed; closed by architectural reframing (the "physics port" framing was a misread; only mechanical-symmetric-writer work was needed — Wind is a direct passthrough from `windOut` at `climatemodel.cpp:865`; Rh is a 22-LOC inline Tetens-formula computation at `climatemodel.cpp:1228-1249`; Fortran-side `WIND_OUT/QHUM_OUT/PSTAR_OUT/T_OUT_M` already exist and are populated). 18 surgical sub-edits + 1 NEW `SUBROUTINE RH_FROM_QPT(Q, P_PA, T_K, RH)` (~40 LOC; byte-identical Tetens algebra to C++) in `imogen/code/imogen_lpjg.f`. Writes `Rh_anom.dat` (unit 96) + `W_anom.dat` (unit 97) to BOTH REGRID + non-REGRID branches; extends `REGRID_CLIM` by 3 new nearest-neighbor passthroughs. Net source change: +202 / -2 = +200 LOC additive (single file). Verification: clean Fortran build (binary 137832 B; zero new warnings with `-Wall`); clean `lpjguess/build/` + `build_mpi/` rebuilds (no-op regression check); 162 unit tests pass both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN — **NOTE: these are the same false-positive PASSes later root-caused as audit item B15 in 17c.0.0 forensic above**). **Cross-engine Rh/W gap CLOSED**; full climate-anomaly output parity between the two engines. **All 6 audit items in the re-ordered Option A sequence are DONE** (B10 → B6 → B2 → B3 → B4 → **B1**). C2-era source-level estimate revised down to ~0 d remaining; only C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` remains (zero source changes). Backport-RELEVANT. Forensic at `notes/STEP_17b.md` §3g.

**Prior dashboard entry preserved for context (2026-05-12 night session 3 continuation; B4 LANDED at commit `2bd5222`):** `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion landed (the loose-mode counterpart to the tight-mode step-9.5 wiring in `IMOGENCFXInput`). 8 surgical insertions across `lpjguess/modules/imogen_input.{cpp,h}` + 1 config-file update (`runs/SSP1-2.6/main_xval_loose.ins`). In the header (+60 LOC): 4 new per-day arrays `drelhum/dwind/dtmin/dtmax[Date::MAX_YEAR_LENGTH]`; doc block annotating pre-existing vestigial `file_relhum`/`file_wind` decls as now-wired-by-B4 + 2 new path decls `file_tmin`/`file_tmax`; 4 new per-year caches `all_drelhum/all_dwind/all_dtmin/all_dtmax`. In the cpp (+127 LOC): ~30-line canonical B4 doc block + 4 param reads in `init()`; 4 `resize3DimVector` calls; doc block + 4 guarded reads in `readenv()` using the `if ((char*)file_relhum != NULL && file_relhum != "")` pattern from IMOGENCFXInput at `imogencfx.cpp:866-888`; monthly+daily branch additions in `get_climate_for_gridcell()` (4 `m*[12]` + `have_*` booleans + `interp_monthly_means_conserve` calls in monthly branch; 4 guarded daily passthroughs in daily branch; NO K→°C at this layer per ImogenInput convention); 4 `climate.{relhum,u10,tmin,tmax}` assignments in BOTH `getclimate()` (gridcell_outer driver) AND `getclimate_for_year()` (C1.1 year_outer override) — with K→°C `- 273.15` on tmin/tmax mirroring the existing `climate.temp = dtemp - 273.15` pattern. In .ins (+15 LOC): 4 new param directives mirroring `main_xval_imogencfx.ins:96-99`. **Design decisions** (cited in doc blocks): (1) K→°C conversion site at consumer (mirror of existing `climate.temp` pattern), intentionally DIFFERS from IMOGENCFXInput's monthly-array-step convention — preserved with cross-references in both files to prevent future drift; (2) B1-pending fallback: `if (path != "")` guards forward-safe across the B1-pending transition (RH/Wind Fortran physics port still pending); (3) Repurpose pre-existing vestigial `file_relhum`/`file_wind` declarations rather than adding duplicates; (4) `preload_all_climate` unchanged (delegates to `readenv()`); (5) `runs/SSP1-2.6/main_xval_loose.ins` updated 1:1 with `main_xval_imogencfx.ins` so xval exercises the new wiring. Verification: clean rebuild on both `build/` and `build_mpi/` with zero new warnings (only pre-existing `gutil.h:1521` sprintf-overflow warning in `Timer::print`); 162 unit tests pass on both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN); 8 xval run.log files complete with "Finished" terminator without `read_lines_from_file` failures (proves all 4 new paths resolved + were read successfully — a missing file would trigger `fail()` at `imogen_input.cpp:550`). **Loose-mode consumer-wiring parity matrix post-B4** (in `notes/STEP_17b.md` §3f.6): both input modules now populate all 10 climate fields (temp/prec/insol/dtr/co2/dNH4dep+dNO3dep/relhum/u10/tmin/tmax). The loose-mode-vs-tight-mode 6-vs-10-fields gap is **CLOSED** for the LPJG-side input pipeline. Cross-engine state post-B4: B3 reframe + Fortran-side B2 close the Tmin/Tmax gap; B4 closes the LPJG-consumer-side gap; only Fortran-engine Rh + Wind **physics computation** gap (B1; ~3-5 d) remains for full loose-mode parity. C2-era estimate revised down to **~4-7 d remaining** (was ~5-8 d; B4 landed in ~0.5 d via direct mirror of the C1.1 IMOGENCFXInput pattern, saving ~0.5 d vs the budgeted 1 d). v1.0 % done estimate revised UP to **~58-62%; ~38-42% remaining**. Step 17b remaining: B1 (next; LAST in re-ordered sequence; ~3-5 d) → C2 close-out (~1-2 d). Full forensic record in `notes/STEP_17b.md` §3f. Backport-RELEVANT (C++ source change in `lpjguess/modules/`).

**Prior dashboard entry preserved for context (2026-05-12 night session 3 continuation; B3 LANDED — closed by architectural reframing at commit `ceb2766`):** C++ Tmin/Tmax in REGRID branch of `lpjguess/modules/climatemodel.cpp` closed by forensic finding rather than by mechanical Tmin/Tmax insertion. Pre-implementation investigation per the four checks in the B3 prompt revealed that the C++ in-process port has **NO REGRID branch** — only one climate-anomaly writer block (the native-IMOGEN-grid branch at line ~890). Evidence chain: (a) `rg "REGRID|regrid" climatemodel.cpp` returns only 3 hits — line 242 dead-code declaration of `bool regrid`, line 894 the stale `// TODO at step 9.5b: replicate this in the REGRID branch.` comment, line 1353 an unrelated comment in a different function; (b) no `if (regrid) { ... } else { ... }` switch anywhere in `RUN_IMOGEN_ENGINE()`; (c) zero `*Regrid` array declarations or usages (only native `tOutM/pOutM/swOutM/windOutM/rhOutM/dtempOutM` at lines 284-289, sized over `GPOINTS`, not `NGPOINTS`); (d) zero `REGRID_CLIM` function calls in any `lpjguess/` source (the Fortran helper `REGRID_CLIM` at `imogen/code/imogen_lpjg.f` ~line 964 was never ported to C++). Interpretation: the `// TODO at step 9.5b: replicate this in the REGRID branch.` comment was an aspirational forward-reference left by the step-9.5 author anticipating a future C++ REGRID branch that was never built. The C++ port has always written climate anomalies on the single native IMOGEN grid (which is what `imogencfx` mode requires; that mode is the v1.0 production path). The pre-B3 cross-engine parity matrix in `notes/STEP_17b.md` §3d.6 had inherited a documentation drift wrongly attributing a REGRID branch to the C++ port; B3 corrects it. **~30 LOC of additive documentation in `lpjguess/modules/climatemodel.cpp` (3 doc-only edits)**: (1) dead-code annotation at line ~242 explaining `bool regrid` is declared-but-never-read; (2) native-grid-is-only-branch clarification at line ~890; (3) canonical B3 doc block (~50 lines) replacing the stale 4-line TODO at line ~894 — with forward-looking maintenance directive specifying the exact C++ algebraic pattern for any future REGRID-branch Tmin/Tmax addition (`file100 << ... << (tOutMRegrid - dtempOutMRegrid/2.0)`; `file101 << ... << (tOutMRegrid + dtempOutMRegrid/2.0)`; `setw(10) << setprecision(3)`; units 100/101 ofstream variable naming). **ZERO functional code change**. Verification: clean rebuild on both `build/` and `build_mpi/` with zero new warnings (forced rebuild of `climatemodel.cpp`); 162 unit tests pass on both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN). **Cross-engine parity matrix corrected**: every climate-anomaly writer site that actually exists in either engine has Tmin/Tmax wired (Fortran has them in BOTH its REGRID + non-REGRID branches per B2; C++ has them in the ONLY branch it has — the native-grid branch — since step 9.5). Rh + Wind remain Fortran-side-only physics gaps (B1 closes them). **NEW persistent operational heuristic rule #7** added (below): "stale forward-reference TODOs are architectural-finding triggers — investigate the actual code structure before mechanically replicating from a sibling implementation." C2-era estimate revised down to ~5-8 d remaining (was ~5.5-8.5 d; B3 saved 0.2 d by landing in 0.3 d). v1.0 % done estimate revised UP to ~56-59%; ~41-44% remaining. Step 17b remaining: B4 (next; ~1 d) → B1 (~3-5 d) → C2 close-out (~1-2 d). Full forensic record in `notes/STEP_17b.md` §3e. Backport-RELEVANT (C++ source change in `lpjguess/modules/`).

**Prior dashboard entry preserved for context (2026-05-12 session 3 continuation; B2 LANDED at commit `76b3b04`):** Fortran Tmin/Tmax write block in `imogen/code/imogen_lpjg.f`; 9 surgical insertions adding `Tmin_anom.dat` (unit 100) + `Tmax_anom.dat` (unit 101) writers symmetrically to BOTH REGRID + non-REGRID branches via algebraic `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2` (per Decision #11; same units = K); +59 LOC additive (no removals); canonical doc block at REGRID OPEN + 8 short cross-reference comments. Cross-engine parity matrix post-B2 (PRE-B3-CORRECTION; carried a documentation drift wrongly attributing a REGRID branch to the C++ port — corrected at B3): Fortran has Tmin/Tmax in BOTH branches; C++ has it only in non-REGRID; B3 closes the C++ REGRID gap. C2-era estimate revised down to ~5.5-8.5 d remaining. v1.0 % done estimate at B2 commit: ~55-58%. Full forensic record in `notes/STEP_17b.md` §3d.

**Prior dashboard entry preserved for context (2026-05-11 night session 3 continuation; B10 LANDED at commit `3c00428`):** Symmetric Fortran engine writer fix in `imogen/code/imogen_lpjg.f` — symmetric Fortran engine writer fix in `imogen/code/imogen_lpjg.f`; **7 conditional removals** (empirically refined from originally-documented 5; 5 C++ analogues + 2 Fortran-specific extras: explicit CO2.dat CLOSE absent in C++ which uses `std::ofstream` RAII; non-REGRID climate-anomaly OPEN/CLOSE branch absent in C++ port which writes on a single grid) at lines 854/883/954/1013/1071/1088/1099 with full C++-doc-block parity (canonical doc at REGRID OPEN mirroring `climatemodel.cpp` ~884 from `7be595a`; 6 cross-referencing short blocks at other sites); +121 LOC, -37 LOC; net +84 LOC. Pre-implementation comprehensive re-examination of project documentation (Decisions #2/#11/#12 + IMOGENCXX-vs-in-process-C++-port distinction confirmed; standalone IMOGENCXX with 25 bugs is Phase 2; Fortran is canonical for v1.0). Re-ordered remaining B-item implementation per user-confirmed Option A: **B10 → B6 → B2 → B3 → B4 → B1** (mechanical-first; physics-port-last). Verification: clean Fortran build (zero warnings; binary 129 600 bytes); static gate-removal check (all 7 gates correctly removed); pre-fix evidence preserved in `imogen/code/IMOGEN/output/{1871,1872}/`. Empirical post-fix engine smoke deferred (Fortran engine inputs not currently shipped in active rebuild; symmetric-correctness framing means clean compile + diff parity suffice). Backport-RELEVANT (Fortran source change in standalone engine). Step 17b remaining: B6 (next; ~0.5 d) → B2 (~0.5 d) → B3 (~0.5 d) → B4 (~1 d) → B1 (~3-5 d) → C2 close-out (~1-2 d). **Total step 17b remaining: ~6.5-11.5 days.** v1.0 % done estimate refreshed UP to ~53-56%; ~44-47% remaining. Full forensic record in `notes/STEP_17b.md` §3b.

**Prior dashboard entry preserved for context (2026-05-11 evening session 3; B12 RESOLVED at commit `488c5a2`):** root cause: smoke .ins files had `ifcalccton 0` and `ifcalcsla 0`, which skipped `init_cton_min()` for each PFT during init, leaving `cton_leaf_min=0`. `init_cton_limits()` (called unconditionally) then cascaded 0 through `cton_*_max/avr/min`, making `cton_sap()` return 0 for fresh individuals. In `respiration()` at canexch.cpp:2494, `cmass_sap (0) / cton_sap (0) = 0/0 = NaN`. NaN cascaded to dnpp → anpp → cmass_* at year-end growth() → ESTC debit → all .out files. Fix: changed `ifcalccton 0 → 1` and `ifcalcsla 0 → 1` in `runs/SSP1-2.6/main_xval_loose.ins` + `runs/SSP1-2.6/main_xval_imogencfx.ins`. Net `lpjguess/` source change: ZERO; backport-IRRELEVANT. ALL 4 xval scenarios now PASS substantive validation (bit-exact AND non-NaN; 0/37 NaN-laden files in any run) against both build/guess and build_mpi/guess. 162 unit tests pass on both builds. C2 era combined sprint estimate revised back to ~9-13 d remaining (B12 closed in ~2 hours work; much faster than 2-10 d unbounded estimate). v1.0 % done estimate revised UP to ~52-55%; ~45-48% remaining (~28-37 d median). Full forensic record in `notes/STEP_17b.md` §3a.7.4c.

**Prior dashboard entry preserved for context (2026-05-11 evening, pre-B12-resolution; F-12 sub-milestone C2 CORE landed + **CRITICAL substantive-validation NaN finding** surfaced during C2 core verification + xval harness hardened with non-NaN gate + NEW audit item **B12** added as critical-path follow-up). KEY DISCOVERY: the C1 close-out `v0.17.0-step17a-c1-year-outer-single-process` tag (commit `8aafe84`) reported "GO/NO-GO gate PASSED for all 4 cross-validation scenarios" based on the harness's `cmp -s` byte-equality check — but ALL 4 scenarios were producing **byte-identical NaN-laden outputs** (`cmp -s` reports NaN-bytes-match-NaN-bytes as identical → PASS, but the simulation is producing garbage). The substantive-validation gap was masked by the byte-comparison-only harness logic. **My C2 MPI code is NOT the cause** (NaN identical in C1-only revert + C2 builds; NaN identical with and without `-parallel`; NaN identical in gridcell_outer + year_outer). NaN appears at simulation Year 2 Day 1 in `soil.NH4_mass`; persists across nyear_spinup ∈ {2, 10, 30}, freenyears ∈ {0, 5, 15}, with/without crop_n.ins, across 4 cells at diverse latitudes (76°N, 80°N, 54°N, -33°S), with exact soilmap matches + with searchradius dist=0 exact climate matches. Plausible remaining root-cause hypotheses: LPJ-GUESS vegetation/soil initialization for `-input imogen` was never substantively-validated (F-10 deadlock blocked it pre-C1; C1's skip_inprocess_engine_run unlocked it but NaN issue went unnoticed); LPJG-internal bug in ImogenInput::get_climate_for_gridcell; wetlandpfts.ins + global.ins initialisation interaction; LandSyMM_LPJ-GUESS fork-specific issue. Path forward: NEW audit item **B12: Substantive-validation NaN root-cause investigation + fix** (CRITICAL PATH; bundled with C2 era BEFORE B1-B10 bundles + BEFORE C2 close-out tag; estimated 2-10 d unbounded). xval harness updated 2026-05-11 to FAIL on NaN-laden outputs (was: PASS based on byte-equality alone) — forces explicit attention on the science-correctness gap. Net `lpjguess/` source-level change this commit: +317 LOC additive (C2 core; correct + verified by mechanics; preserves byte-equality with C1 baseline). xval harness change: backport-IRRELEVANT (scripts/ only). C2 era combined sprint estimate revised: **~11-23+ days** (was 9-13 d).

**Prior dashboard entry preserved for context (2026-05-11 late afternoon; F-12 sub-milestone C2 CORE landed — `MPI_Barrier(MPI_COMM_WORLD)` at year boundary in `lpjguess/framework/framework.cpp` (HAVE_MPI + `MPI_Initialized` guarded; ~10 LOC additive at line ~611 of year_outer block) + `flush_year_globally_synchronized(int year)` method on `ImogenOutput` (~120 LOC additive in `lpjguess/modules/imogenoutput.cpp/h`) with `MPI_Allreduce(MPI_SUM)` over per-rank NEE/CH4/N2O/area/count contributions + lead-rank-only write delegation to existing `flush_year` + post-flush `accum_year=-1` reset (suppresses outannual auto-flush at year+1 cell 0 → avoids double-write) + singleton-pointer `ImogenOutput::get_instance()` pattern (mirrors existing `output_channel` global at `outputmodule.h:227`; minimises touch surface vs adding a new virtual to OutputModule base). MPI integration discipline VERIFIED to match existing LPJ-GUESS conventions exactly (`mpi.h` include placement + `MPI_Initialized(&flag)` guard pattern from `imogencfx.cpp:381` + `imogen_input.cpp:221` + `GuessParallel::get_rank()` from `parallel.h`). Both builds rebuild clean; 162 unit tests pass on BOTH `build/guess` and `build_mpi/guess`; ALL FOUR cross-validation scenarios re-PASS bit-exact 37/37 against `build_mpi/guess` single-process (C1 baseline preserved through C2 core code addition). `mpirun -np 1 -parallel` smoke test verified: MPI_Init succeeds + my code path is reachable (diagnostic `[ImogenOutput] flushed year=XXXX` visible in stdout) + LPJG main loop completes end-to-end. Full `mpirun -np 4` mimic with proper per-rank `runNN/` setup deferred to C2 close-out (alongside B-bundles, since B4 ImogenInput consumer wiring expansion is needed for full multi-rank loose-mode functionality). B1+B2+B3+B4+B6+B10 bundles are NEXT. Net `lpjguess/` source-level change this commit: +317 LOC additive across 3 files (backport-RELEVANT).

**Prior dashboard entry preserved for context (2026-05-11 afternoon; F-12 sub-milestone C2 PREP at commit `1405ada`):** Anaconda3 `mpicxx` wrapper fix via `conda install -c conda-forge gxx_linux-64` + `scripts/cluster/make_guess.sh --mpi` workstation-NetCDF logic fix + `lpjguess/build_mpi/guess` built clean + 162 unit tests pass + ALL FOUR cross-validation scenarios re-PASS bit-exact 37/37 against `build_mpi/guess` in single-process mode (pre-MPI_Barrier baseline). B1-B11 bundling decision locked in: refined option (i) for B1+B4 with C2 era + opportunistic option (iii) for B2/B3/B5-B11 with definitive per-item home (see "B-item bundling commitment (2026-05-11)" sub-section below).

**Prior dashboard entry preserved for context (2026-05-11 early morning; Comprehensive outstanding-work audit landed at commit `e8fd7fb`):** Triggered by user 2026-05-10 late-evening clarification + question about engine/input-module symmetry. Audit revealed: production path (`-input imogencfx` + C++ in-process engine port) IS fully wired post-C1 close-out at v0.17.0; non-production paths (standalone Fortran engine; `-input imogen` loose mode) have known asymmetries documented since step 9.5 (2026-05-07) that aggregate to ~9-15 days of additional in-v1.0-scope work previously omitted from chat-level "% remaining" estimates. Revised estimate: ~48-50% done; ~50-52% remaining (~33-37 days median); was ~70% / ~30% / ~20-32 days. See "Comprehensive outstanding-work audit" section below the dashboard table for full breakdown across in-v1.0-scope (A + B; ~25-45 days) + post-v1.0 (C; v1.1+/v2.0+/paper-stage). NO SOURCE-LEVEL CHANGE in that commit; docs-only.

**Prior dashboard entry preserved for context (2026-05-10 very late evening; F-12 SUB-MILESTONE C1 FULLY CLOSED OUT; TAGGED `v0.17.0-step17a-c1-year-outer-single-process`):** ALL FOUR cross-validation scenarios PASS bit-exact 37/37: imogen 1-cell ✅, imogen 4-cell ✅, imogencfx 1-cell ✅ (NEW), imogencfx 4-cell ✅ (NEW). The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) empirically validated for BOTH input modules across BOTH single-cell + multi-cell + single-spinup-year + multi-spinup-year scenarios. **GO/NO-GO gate per session-2 §9.5: PASSED for ALL FOUR scenarios.** Sub-step 7.3.2 commit lands: NEW `skip_inprocess_engine_run` ins parameter (option a per STEP_17a.md §7.3.2; default `false` preserves LTS-equivalent behaviour) + IMOGENCFXInput year_outer overrides (preload_all_climate + getclimate_for_year; ~250 LOC additive in imogencfx.cpp + ~95 LOC in imogencfx.h; mirrors C1.1 ImogenInput pattern with IMOGENCFXInput-specific differences) + K→C latent-bug fix in IMOGENCFXInput::get_climate_for_gridcell (~25 LOC; 6 code-line changes; surfaced empirically when -input imogencfx mode reached LPJG main loop for the first time post-skip_inprocess_engine_run; aligns with CFXInput's Celsius-native pattern per user's 2026-05-10 clarification "imogencfx is meant to work like the cfx input module, with only caveat being instead of NetCDF climate forcing it takes in IMOGEN climate"). Cross-validation harness extended for `imogencfx` 2nd-arg variant. 162 unit tests pass throughout. **Earlier 4-cell smoke + engine writer fix context preserved in prior dashboard entry (see git history for the full chain).** All 37 standard LPJG outputs match bit-exact between Run A (`gridcell_outer`) and Run B (`year_outer`) for 4-cell `gridlist_test2.txt` × `nyear_spinup=2` × `lasthistyear=1879` (44 cell-year iterations per run; 9 distinct imogen_years). The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is now empirically validated across BOTH cell_idx>0 AND year_idx>0 branches. Pre-requisite engine writer fix landed: `lpjguess/modules/climatemodel.cpp` 5-conditional-removals at lines ~787/~884/~963/~988/~998 (~76 LOC total incl. doc blocks) — fixes the alternating-year staged-climate quirk discovered at C1.2 (each engine call previously wrote climate ONLY for IYEAR == YEAR1; net effect: ODD years had full climate, EVEN years had only `done` marker). Post-fix: ALL 32 staged years (1871-1902) have full 13-file climate. Same bug exists in standalone Fortran engine (`imogen/code/imogen_lpjg.f` lines 954, 1013, 1071, 1088, 1099); deferred for symmetric fix as F-N follow-up. C1.2 PASS preserved (1-cell xval re-verified PASS post-fix). 162 unit tests still pass. **Remaining within step 17a (next session): sub-step 7.3.2 IMOGENCFXInput year_outer override (~1.5-2 days; with engine-bypass mechanism — NEW `skip_inprocess_engine_run` parameter recommended) + cross-validate single-cell first; multi-cell second + tag `v0.17.0-step17a-c1-year-outer-single-process` + close-out.**)

| ID | Status | Best timing | Blocks step 17 validation? |
|---|---|---|---|
| F-1 | OPEN | At v1.0 release time (~step 19) | No |
| F-2 | DONE 2026-05-11 (subsumed by B10 — 2× line count was one of three downstream symptoms of the alternating-year writer bug B10 fixed at `imogen/code/imogen_lpjg.f`; ZERO further code change needed for F-2; forensic at STEP_17b.md §3c) | — | — |
| F-3 | OPEN | F-12 era (when both engines testable) | No |
| F-4 | DONE 2026-05-06 | — | — |
| F-5 | DONE 2026-05-06 | — | — |
| F-6 | OPEN | Step 9.5b | No |
| F-7 | OPEN | Step 9.5b | No |
| F-8 | OPEN | Step 9.5b | No |
| F-9 | OPEN (refined at step 9.5) | Step 9.5c (or merge with F-12 sprint) | No |
| F-10 | PARTIALLY RESOLVED (workstation single-process tight: ✅ via F-12 C1 close-out; cluster MPI tight: ⏳ via C2+C3) | Resolved at C1+C2+C3 per Path A 2026-05-09 refinement (Option C only; Option B skipped) | C1 done (✅); C2+C3 still required for full v1.0 |
| F-11 | OPEN | End of Phase 1 (after step 19; scope expanded by F-12 in-v1.0) | No (paper consistency) |
| F-12 | **PARTIALLY DONE** — C1 byte-equality ✅ CLOSED (TAGGED `v0.17.0-step17a-c1-year-outer-single-process` 2026-05-10); C1 substantive-validation ✅ CLOSED (B12 RESOLVED 2026-05-11); **C2 prep ✅ done** (`1405ada`); **C2 core ✅ done** (`f13b302`); **B12 ✅ done** (`488c5a2`); **B10 ✅ done** (`3c00428`); **B6 ✅ done** (`24250b2`; F-2 subsumed; docs-only); **B2 ✅ done** (`76b3b04`); **B3 ✅ done** (`ceb2766`, closed by architectural reframing); **B4 ✅ done** (`2bd5222`); **B1 ✅ DONE** (this commit, 2026-05-12 early morning; closed by architectural reframing — the audit-table "physics port" framing was a misread; only mechanical-symmetric-writer work was needed; 18 surgical sub-edits + 1 NEW `SUBROUTINE RH_FROM_QPT` ~40 LOC in `imogen/code/imogen_lpjg.f`; +200 LOC additive). **C2-era B-bundle is feature-COMPLETE** (all 6 audit items DONE: B10 → B6 → B2 → B3 → B4 → B1). Only C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` remains (zero source changes). **Original B4 narrative**: `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion at `2bd5222`; 8 surgical insertions across `lpjguess/modules/imogen_input.{cpp,h}` + 1 .ins update; +187 LOC additive in source + +15 LOC in .ins; loose-mode-vs-tight-mode 6-vs-10-fields gap CLOSED for the LPJG-side input pipeline); **B1 ⏳ NEXT** (~3-5 d remaining; LAST in sequence per re-ordered Option A; heaviest item — Fortran Rh + Wind physics port from C++ in-process engine to standalone Fortran); full mpirun -np 4 mimic + close-out tag after B1; C3 ⏳ after C2 close-out. **[2026-05-12 audit refresh + 2026-05-13 17c.0.1+0.2 update]** Pre-cluster audit of `f6c192e`'s C2 close-out surfaced **B15** (class-mismatch defect; the `framework_loop_mode` Class-1 declare_parameter-bound C++ var was being set Class-2-syntax in the harness + ins; silent override → all C1+C2 xval scenarios false-positive in gridcell_outer == gridcell_outer mode) + **B16** (latent eager cache-fullness check in `(IMOGENCFX|Imogen)Input::preload_all_climate` mis-modelling cumulative-across-cells cache as per-cell). 17c.0.0 forensic record landed `2beff31` 2026-05-12 (doc-only; ZERO source change; rule #8 added). **17c.0.1 + 17c.0.2 LANDED 2026-05-13** (this commit; +171/−5 across 4 files): F1+F2+F3+F4+F5 per `notes/STEP_17c.md` §0.8; **B15 ✅ CLOSED**; 1cell xval scenarios PASS substantive + signal-of-life clean for the FIRST TIME (year_outer code path actually exercised in Run B; F5 echo + rule-#8 banner-presence assertion both observably effective); 4cell xval scenarios surface B16 textbook-exactly per §0.9 (positive empirical evidence; both modules; same `(-95.75,80.25)` cell; same `last_store_index=9 >= nyears=9` numerics). C2 close-out tag annotation amendment decision deferred to 17c.0.5; tag remains as-is at `f6c192e` un-amended through 17c.0.1+0.2. **B16 ⏳ NEXT** as sub-phase 17c.0.3 (~0.5-1 d). Then 17c.0.4 (re-verify on B15+B16-fixed HEAD; ~0.5 d) → 17c.0.5 (tag annotation decision; ~0.2 d) → 17c.0.6 (mpirun -np 4 mimic; ~1 d) → 17c.0.7 (PREP close-out; ~0.2 d). Total remaining 17c.0 PREP after this commit: ~2.5-3.5 d. C3-era cluster phases ~1-2 weeks SSH-iterative thereafter. | **B15 ✅ CLOSED 2026-05-13** (C1+C2 false-positive harness root cause); B16 ⏳ NEXT (17c.0.3); C2 close-out tag annotation amendment deferred to 17c.0.5; 17c.0.6 mpirun -np 4 mimic deferred-from-C2 obligation; C3 (~1-2 weeks cluster SSH iterative) after PREP close-out at 17c.0.7. **Tag target unchanged**: `v0.18.0-step17c-c3-cluster-tight` (after all 5 cluster phases pass + cluster smoke matches workstation MPI mimic baseline + production smoke completes within walltime + aggregate fluxes within working-paper §2.5 thresholds) | C2 close-out tag annotation + 17c.0.3 B16 fix + 17c.0.4-0.7 + C3 still **Yes** (cluster MPI tight gates on full PREP close-out + C3) |
| F-13 | OPEN (paper-stage comparative analysis) | Post-v1.0 (post-step-19) | No (paper-stage; not a v1.0-runnable item) |

### Step-row deferrals (in `EXECUTION_PLAN.md` rows; not in this file)

| Item | Where to track | Best timing |
|---|---|---|
| Step 9 V.1 verification milestone (NEE 2× → CO2 shift) | EXECUTION_PLAN.md V.1 step 9 row | Gated on F-12 (now: post-C1; testable in C2+ era) |
| Step 9.5b: Fortran Rh/W port + Fortran Tmin/Tmax + C++ Tmin/Tmax in REGRID branch | EXECUTION_PLAN.md V.1 step 9.5 row | Next time we touch engine output code (still OUTSTANDING per audit 2026-05-11; see §"Comprehensive outstanding-work audit" below) |
| Step 11 input-data acquisition (RCMIP, FAIR ERF, EDGAR, PLUM, LPJG outputs ~1.8 GB) | EXECUTION_PLAN.md V.1 step 11 row | Step 11 (DONE) |
| Step 13 adapter (intermediary_py outputs → 4 narrow IMOGEN-readable files) | EXECUTION_PLAN.md V.1 step 13 row | Step 13 (DONE) |

---

## Comprehensive outstanding-work audit (2026-05-11; full v1.0 scope sweep)

**Triggered by user 2026-05-10 late-evening clarification + question** about whether all IMOGEN climate variables (T, P, SW, WET, DTEMP, Rh, W, Tmin, Tmax, CO2 = 10 fields) are bidirectionally wired (engine writes + LPJG reads) for the v1.0 framework. Audit revealed: (a) **production path** (`-input imogencfx` + C++ in-process engine port) IS fully wired post-C1 close-out at v0.17.0; (b) **non-production paths** (standalone Fortran engine; `-input imogen` loose mode) have known asymmetries documented since step 9.5 (2026-05-07) but never aggregated into a single audit. This audit aggregates them and surfaces ~9-15 days of additional in-v1.0-scope work that was previously omitted from chat-level "% remaining" estimates.

### A. Production critical path (5 remaining V.1 steps; NEXT ladder)

| # | Item | Median effort | Status |
|---|---|---|---|
| A1 | Step 17b (F-12 C2; workstation MPI year_outer) | 3-5 days | ⏳ NEXT |
| A2 | Step 17c (F-12 C3; cluster MPI iterative SSH on KIT IMK-IFU `owl`) | 1-2 weeks (5-15 days) | ⏳ after A1 |
| A3 | Step 17d (end-to-end validation across 4 combinations: local/HPC × loose/tight) | 2-3 days | ⏳ after A2 |
| A4 | Step 18 (docs completion + reproducibility verification) | 3-5 days | ⏳ after A3 |
| A5 | Step 19 (CI/CD + Zenodo DOI + v1.0.0 release tag) | 2-3 days | ⏳ after A4 |

**Subtotal A**: ~16-30 days (median ~22-25 days)

### B. Deferred-from-earlier-steps follow-ups (in-v1.0-scope per audit; previously OMITTED from chat-level % estimates)

| # | Item | Median effort | Triggered by |
|---|---|---|---|
| B1 | **Step 9.5b (a)**: Fortran Rh + Wind COMPUTATION port from C++ engine to Fortran engine. Per Decision #12 + STEP_9.5 §3.4: the C++ port added the entire Rh/Wind physics pipeline; Fortran doesn't compute these at all. NOT a writer-only port (~70-100 LOC of Fortran physics work). | **3-5 days** (the heaviest piece) | Decision #12; STEP_9.5 §3.4 |
| B2 | **Step 9.5b (b)**: Fortran Tmin/Tmax write block (algebraic `Tmin = T − DTEMP/2`, `Tmax = T + DTEMP/2` per Decision #11; mirror climatemodel.cpp's non-REGRID branch addition). | 0.5 day | Decision #11; STEP_9.5 §3.3 |
| B3 | **Step 9.5b (c)**: C++ engine Tmin/Tmax write in REGRID branch (currently only non-REGRID branch; "TODO at step 9.5b" comment in code). | 0.5 day | STEP_9.5 §3.3 |
| B4 | **ImogenInput Rh/W/Tmin/Tmax consumer wiring expansion** — 4 file_* declarations + read pipeline + climate.{relhum, u10, tmin, tmax} assignments + extension to the C1.1 year_outer override. Closes the loose-mode-vs-tight-mode 6-vs-10-fields gap discussed 2026-05-10 late evening. | 1 day | User clarification 2026-05-10 late evening; tonight's audit |
| B5 | **F-9 / step 9.5c**: miscoutput diagnostic outputs (12 file_*_anom params already declared; needs Option A per FOLLOWUPS F-9 refinement: per-month Climate accumulator infrastructure ~50 LOC + create_output_table + outannual outlimit calls). | 1-2 days | STEP_8 §3.5 + STEP_9.5 §3.4 + FOLLOWUPS F-9 |
| ~~B6~~ ✅ DONE | ~~**F-2**: Fortran T_anom.dat 2× line count investigation + minor fix.~~ ✅ **CLOSED 2026-05-11 night (session 3 continuation)** — subsumed by B10. The 2× line count was one of three downstream symptoms of the alternating-year writer bug B10 mechanically fixed at `imogen/code/imogen_lpjg.f` (commit `3c00428`). ZERO source change for B6. Forensic record at STEP_17b.md §3c. | 0.0 d (subsumed) | STEP_17b.md §3c |
| B7 | **F-6**: CMIP6 `ql1_patt` unit alignment with IMOGEN's `DRH15M_PAT`. Magnitude differs 1500× at sample cell. Contact upstream (PRIME/Mathison 2025) author + possibly add unit-conversion factor. | 0.5 day | STEP_5 CAVEAT-A + FOLLOWUPS F-6 |
| B8 | **F-7**: CMIP6 `pstar_patt` units vs CMIP5 `DPSTAR_C_PAT`. 150× magnitude diff + opposite sign at sample cell; likely Pa-vs-hPa unit mismatch (one-line fix). | 0.5 day | STEP_5 CAVEAT-B + FOLLOWUPS F-7 |
| B9 | **F-8**: CMIP6 wind-magnitude split + precip rain/snow partition refinement (currently `U=V=wind/√2`, `rain=precip/snow=0`). | 0.5-1 day | STEP_5 CAVEAT-B/C + FOLLOWUPS F-8 |
| ~~B10~~ ✅ DONE | **Symmetric Fortran engine writer fix** (alternating-year bug at `imogen/code/imogen_lpjg.f`). ✅ **DONE 2026-05-11 night (session 3 continuation)** — empirically refined to **7 conditional removals** at lines 854/883/954/1013/1071/1088/1099 (5 C++ analogues + 2 Fortran-specific extras: explicit CO2.dat CLOSE absent in C++ which uses `std::ofstream` RAII; non-REGRID climate-anomaly OPEN/CLOSE branch absent in C++ port which writes on a single grid). Same root cause as the C++ fix landed at C1.3 sub-step 7.3.1 commit `7be595a`. Fortran engine is currently used only for engine-only smoke testing (NOT on prescribed-mode launcher path); fix landed under **symmetric-correctness framing** (engines stay in lock-step; engine-mode parity per F-3). +121 LOC, -37 LOC; clean Fortran build (zero warnings); static gate-removal check confirms all 7 gates correctly removed. Backport-RELEVANT (Fortran source change). | 0.5 day (actual) | STEP_17b.md §3b (canonical forensic) + STEP_17a §5.6 + sub-step 7.3.1 commit `7be595a` doc block |
| B11 | **Latent OOB fix in existing IMOGENCFXInput::getclimate cache** (`stored_years[i] = imogen_year` when `i >= nyears` due to undersized cache from formula `nyears = (lasthistyear - FIRST_SPINUP_YEAR) + 1`). Pre-existing latent bug surfaced at C1.3 sub-step 7.3.1 (worked around via lasthistyear bump in main_xval_loose.ins). Defensive hardening: add explicit bounds check + dynamic resize OR refactor the cache size formula. | 0.5 day | STEP_17a §6.3; surfaced at sub-step 7.3.1 |
| **B12** | **Substantive-validation NaN root-cause investigation + fix** (NEW 2026-05-11 evening; CRITICAL PATH). The C1 close-out at `v0.17.0-step17a-c1-year-outer-single-process` reported "bit-exact 37/37 PASS" but ALL 4 cross-validation scenarios were producing byte-identical NaN-laden outputs (`cmp -s` byte-equality of NaN == byte-equality of NaN → PASS-of-garbage). The byte-comparison-only harness logic masked the substantive-validation gap. NaN appears at simulation Year 2 Day 1 in `soil.NH4_mass` and propagates. Investigation 2026-05-11 ruled out: MPI code path; -parallel CLI flag; loop-ordering mode; short spinup (2/10/30); crop module; gridcell specificity (4 cells across 76°N → -33°S); soilmap mismatch; searchradius interpretation; climate input (sane Kelvin values). Plausible remaining causes: LPJ-GUESS vegetation/soil initialization for `-input imogen` never substantively-validated (F-10 deadlock blocked it pre-C1); LPJG-internal bug in ImogenInput::get_climate_for_gridcell; wetlandpfts.ins + global.ins initialisation interaction; LandSyMM_LPJ-GUESS fork-specific issue. **MUST land BEFORE C2 close-out tag** so the `v0.17.5-step17b-c2-mpi-sync` milestone is on a substantively-validated baseline. xval harness updated 2026-05-11 to FAIL on NaN-laden outputs (was: PASS based on byte-equality alone) — forces explicit attention until B12 is resolved. | **2-10 days unbounded** | STEP_17b §3a.7 (full forensic record + diagnostic chain); STEP_17b §3a.8 (xval harness hardening this commit); session-2 chat handoff Part 18 (full investigation narrative) |

**Subtotal B**: ~11-25+ days (median ~13-17 days; B12 unbounded) — was ~9-15 d before B12 addition

**TOTAL in-v1.0 remaining (A + B): ~27-55+ days (median ~35-42 days)** — was ~25-45 d before B12 addition

### C. Post-v1.0 (v1.1+ / v2.0+ / paper-stage; not blocking v1.0 release tag)

| # | Item | Median effort | Best timing |
|---|---|---|---|
| C1 | F-11 Backport Sprint to `trunk_r13078` (replicate all `lpjguess/` source changes from steps 7+8+9.5+17a-foundation+17a-C1.1+17a-C1.2+17a-C1.3-7.3.1+17a-C1.3-7.3.2+(any of B1-B11 that lands)). Scope expanded by F-12 in-v1.0 work (per FOLLOWUPS dashboard). | 3-5 days | End of Phase 1 (after step 19); paper-consistency required |
| C2 | F-1 Zenodo upload of data tarballs (49 MB across 4 patterns + CRUNCEP tarballs; 460 MB ndep tarball). Easy task; gives DOI for citation. | 30 min | At v1.0 release time (~step 19) |
| C3 | F-13 paper-stage comparative-analysis framework (3 axes per `paper/README.md`: GHG concentrations / climate trends / LPJG ecosystem outputs) + 9 paper revisions for GMD submission. | 1-2 weeks (paper work) | Post-v1.0 (post-step-19) |
| C4 | F-3 Fortran ↔ C++ IMOGEN numerical parity work (Decision #2 Phase-2 milestone). | 1-2 weeks | Phase 2 (v1.1+) |
| C5 | PLUM v2 embedding + Stage I re-coupling (per Decision #9; per `docs/v2_roadmap.md` §2). | 2-3 weeks | v2.0 (post-v1.0 release) |
| C6 | v1.1+ refinement: simplify `intermediary_py` cluster copy-over filenames from `lpjg_<output>_<scenario>.gz` to native LPJG names (since dir hierarchy already encodes scenario). | 0.5 day | v1.1+ |

### % done estimates (cross-method triangulation)

| Method | % done | % remaining | Days remaining |
|---|---|---|---|
| Original (production critical path only; previous chat-level estimate) | ~70% | ~30% | ~20-32 |
| Step-count weighted (17 of 21 sub-steps done) | ~80% | ~20% | n/a |
| 4-combination weighted (3 of 4 combinations done) | ~75% | ~25% | n/a |
| Risk-weighted (F-10 architectural mountain done; only mechanical work remains) | ~80% | ~20% | n/a |
| LOC-weighted (most lpjguess source changes are landed) | ~90% | ~10% | n/a |
| REVISED: full v1.0 with engine + input-module symmetry (per 2026-05-11 audit) | ~48-50% | ~50-52% | ~33-37 (median) |
| FURTHER REVISED (2026-05-11 evening, pre-B12 resolution) | ~40-45% | ~55-60% | ~35-42 (range 27-55+) |
| REVISED: full v1.0 post-B12 resolution (2026-05-11 evening session 3) | ~52-55% | ~45-48% | ~28-37 (median; range 22-43) |
| REVISED: full v1.0 post-B10 closure (2026-05-11 night session 3 continuation) | ~53-56% | ~44-47% | ~27-36 (median; range 21-42) |
| **REVISED: full v1.0 post-B6 closure (2026-05-11 night session 3 continuation)** | **~54-57%** | **~43-46%** | **~26.5-35.5 (median; range 21-42)** — B6 saved 0.5 d by collapsing into B10 |

**Adopted estimate going forward (2026-05-12 early morning session 3 continuation, post-B1 closure)**: **~62-65% done; ~35-38% remaining (~20-26 days median; range 16-32)**. B1 closed in ~0.5 d (far lighter than the 3-5 d budget; architectural-reframing close — the audit-table "physics port" framing was a misread; only mechanical-symmetric-writer work was needed). **All 6 audit items in the re-ordered Option A sequence are now DONE** (B10 → B6 → B2 → B3 → B4 → **B1**). The C2-era B-bundle is **feature-complete**; only C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` remains (zero source changes). After C2 close-out: Step 17c (HPC integration tests on `owl` cluster; iterative SSH session work; ~1-2 weeks). The C1 baseline produces non-NaN scientific output; both engines have the alternating-year writer fix applied symmetrically (C++ port at `climatemodel.cpp` from `7be595a` + standalone Fortran at `imogen_lpjg.f` from `3c00428`); B2 adds Fortran Tmin/Tmax writers; B3 corrects the documentation drift on the C++ side (no REGRID branch was ever built; ~30 LOC additive docs only); B4 closes the LPJG-consumer-side 6-vs-10-fields gap for both input modes. F-2's 2× line count symptom is mechanically eliminated by B10's structural fix.

**Prior estimate preserved (2026-05-12 night session 3 continuation, post-B3 closure)**: ~56-59% done; ~41-44% remaining (~25-32 days median; range 21-40). B3 closed in 0.3 d via close-by-architectural-reframing (lighter than budgeted 0.5 d).

### B-item bundling commitment (2026-05-11; locked in at C2 prep; REVISED 2026-05-11 evening to add B12 per substantive-validation NaN finding)

To honour the user's stated condition "tackle ALL items; leave NONE undone", every B-item has a **definitive home** before C2 implementation begins. Refined option (i) for B1+B4 with C2 era + opportunistic option (iii) for the smaller items B2/B3/B5-B11 with explicit per-item per-step assignment. **B12 added 2026-05-11 evening as NEW critical-path item per the substantive-validation NaN finding** (see "Substantive-validation NaN finding (2026-05-11)" sub-section below + STEP_17b.md §3a.7).

| # | Item | Effort | Bundling home | Status |
|---|---|---|---|---|
| **B12** | **~~Substantive-validation NaN root-cause investigation + fix~~** | **~~2-10 d~~ → ~2 hours** | ~~C2 era (step 17b)~~ | ✅ **DONE 2026-05-11 evening (session 3)** — root cause: `ifcalccton 0` in smoke .ins → `init_cton_min()` skipped → cton_leaf_min=0 → 0/0 in respiration → NaN; fix: `ifcalccton 1 + ifcalcsla 1` in 2 .ins files; net lpjguess/ source change ZERO; all 4 xval scenarios PASS substantive validation. See STEP_17b.md §3a.7.4c. |
| B1 | Fortran-engine Rh + Wind COMPUTATION + write-block port — **closed by architectural reframing** | 3-5 d (budgeted); **~0.5 d (actual)** | **C2 era (step 17b)** | ✅ **DONE** (this commit, 2026-05-12 early morning session 3 continuation; the audit-table "physics port" description was a misread — Wind is a direct passthrough; Rh is a 22-LOC inline Tetens computation; Fortran-side sources already exist and are populated; only mechanical-symmetric-writer work was needed; 18 surgical sub-edits + 1 NEW `SUBROUTINE RH_FROM_QPT` ~40 LOC in `imogen/code/imogen_lpjg.f`; +200 LOC additive; forensic at `notes/STEP_17b.md` §3g; **all 6 audit items in re-ordered Option A sequence DONE**) |
| **B2** ✅ DONE | Fortran Tmin/Tmax write block | 0.5 d (actual; matches estimate) | **C2 era (step 17b)** | ✅ **DONE 2026-05-12 (session 3 continuation; this commit)** — 9 surgical insertions in `imogen/code/imogen_lpjg.f` adding `Tmin_anom.dat` (unit 100) + `Tmax_anom.dat` (unit 101) writers symmetrically to BOTH REGRID + non-REGRID branches via algebraic `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2` (per Decision #11; same units = K). Symmetric with C++ in-process port at `climatemodel.cpp` ~lines 952-953 (which has Tmin/Tmax in non-REGRID only — **B3** closes C++ REGRID gap). +59 LOC additive (no removals); clean Fortran build (zero warnings; binary 133 696 B); 26 unit-100/101 references match expected. Backport-RELEVANT (Fortran source change). See STEP_17b.md §3d. |
| **B3** ✅ DONE | ~~C++ Tmin/Tmax in REGRID branch~~ → **closed by architectural reframing** | 0.3 d (actual; under 0.5 d estimate) | **C2 era (step 17b)** | ✅ **DONE 2026-05-12 night (session 3 continuation; this commit)** — pre-implementation forensic finding: the C++ in-process port has **NO REGRID branch**. Evidence: `rg "REGRID\|regrid" climatemodel.cpp` returns only 3 hits (line 242 dead-code `bool regrid` declaration; line 894 the stale TODO; line 1353 unrelated comment); no `if (regrid) { ... }` switch; zero `*Regrid` array variants; zero `REGRID_CLIM` calls. The `// TODO at step 9.5b: replicate this in the REGRID branch.` was an aspirational forward-reference left by the step-9.5 author anticipating a future C++ REGRID branch that was never built. ~30 LOC of additive documentation only in `lpjguess/modules/climatemodel.cpp` (3 doc-only edits): dead-code annotation at line ~242; native-grid-is-only-branch clarification at line ~890; canonical B3 doc block replacing stale TODO at line ~894 with forward-looking maintenance directive specifying the exact C++ algebraic pattern for any future REGRID-branch Tmin/Tmax addition. **ZERO functional code change**. Verification: clean rebuild on both `build/` and `build_mpi/` with zero new warnings; 162 unit tests pass on both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN). Updated §3d.6 cross-engine parity matrix in STEP_17b.md to reflect actual state (every climate-anomaly writer site that actually exists in either engine has Tmin/Tmax wired). New operational heuristic rule #7 added. Backport-RELEVANT (C++ source change in `lpjguess/modules/`). See STEP_17b.md §3e. |
| B4 | ImogenInput Rh/W/Tmin/Tmax consumer wiring expansion | 1 d (budgeted); **~0.5 d (actual)** | **C2 era (step 17b); B12+B10+B6+B2+B3+B4 ✅ done** | ✅ **DONE** (this commit, 2026-05-12 night session 3 continuation; 8 surgical insertions across `lpjguess/modules/imogen_input.{cpp,h}` + 1 config-file update; +187 LOC additive in source + +15 LOC in `.ins`; closes loose-mode-vs-tight-mode 6-vs-10-fields gap for LPJG-side input pipeline; forensic at `notes/STEP_17b.md` §3f) |
| B5 | F-9 / step 9.5c miscoutput diagnostic outputs | 1-2 d | **Step 18** (docs/reproducibility era) | ⏳ pending step 18 |
| **B6** ✅ DONE | ~~F-2 Fortran T_anom 2× line count~~ | 0.0 d (subsumed by B10) | **C2 era (step 17b)** | ✅ **DONE 2026-05-11 night (session 3 continuation; this commit; docs-only)** — forensic determination: the 2× line count is one of three downstream symptoms of the same alternating-year writer bug B10 fixed at `3c00428` (T/P/SW/DTEMP doubled to 3262 lines; WET stuck at 1631 lines due to mid-1871 unit-95 reuse for fa_ocean.dat that auto-closed WET; fa_ocean.dat contaminated by +1631 WET-format integer rows; dtemp_o.dat doubled to 508). Smoking-gun: lines 10001-11631 of pre-fix `fa_ocean.dat` are exact WET-format `LON LAT + 12 ints`. Cross-validation against `version_A/.../IMOGEN/output/1871/` reference (T/P/SW/DTEMP=1631 each, WET=1631, fa_ocean=10000 clean, dtemp_o=254) confirms the predicted post-B10 structural output. ZERO Fortran source change for B6. Backport-IRRELEVANT (no source change; B10 backport entry already covers all 7 gates). See STEP_17b.md §3c. |
| B7 | F-6 CMIP6 `ql1_patt` unit | 0.5 d | **Step 18** (batched with B8/B9) | ⏳ pending step 18 |
| B8 | F-7 CMIP6 `pstar_patt` units | 0.5 d | **Step 18** (batched with B7/B9) | ⏳ pending step 18 |
| B9 | F-8 CMIP6 wind-mag + precip rain/snow | 0.5-1 d | **Step 18** (batched with B7/B8) | ⏳ pending step 18 |
| **B10** ✅ DONE | ~~Symmetric Fortran engine writer fix~~ | 0.5 d (actual) | **C2 era (step 17b)** | ✅ **DONE 2026-05-11 night (session 3 continuation)** — 7 conditional removals (empirically refined from originally-documented 5; 5 C++ analogues + 2 Fortran-specific extras: explicit CO2.dat CLOSE + non-REGRID climate-anomaly OPEN/CLOSE branch absent in C++) at `imogen/code/imogen_lpjg.f` lines 854/883/954/1013/1071/1088/1099 with full C++-doc-block parity (canonical doc at REGRID OPEN mirroring `climatemodel.cpp` ~884 from `7be595a`; 6 cross-referencing short blocks at other sites); +121 LOC, -37 LOC; clean Fortran build (zero warnings); static gate-removal check confirms all 7 gates removed. Backport-RELEVANT (Fortran source change in standalone engine). See STEP_17b.md §3b. |
| B11 | Latent OOB fix in IMOGENCFXInput::getclimate cache | 0.5 d | **Step 17d** (end-to-end-validation era; defensive hardening) | ⏳ pending step 17d |
| **B13** | **Defensive hardening: fail-fast at `init_cton_limits()` if `cton_leaf_min == 0` (so the trap that caused B12 cannot recur silently)** | **0.5 d** (NEW 2026-05-11 session 3) | **Step 18** (docs/reproducibility era) | ⏳ pending step 18 |
| **B14** | **One-time `.ins` parity audit vs original codebase(s).** Diff `runs/SSP1-2.6/main_xval_*.ins` (and the imported `global.ins` / `crop_n.ins` / `wetlandpfts.ins` / `imogen_intermediary.ins` chain) against Version A's `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/` (and Version B's `landsymm_imogen/SSP1_RCP26/`) `.ins` set. For each parameter that differs: classify as (a) **intentional** (smoke-scale / xval-specific) and document rationale at the parameter site, or (b) **unintentional** (open follow-up). Driven by the B12 lesson: a single `ifcalccton 0` divergence from the inherited `global.ins` baseline produced silent NaNs. Low priority — fix arrived without a full audit — but the audit reduces residual unknown-unknown risk and is cheap to do once. | **0.5-1 d** (NEW 2026-05-11 session 3) | **Step 18** (docs/reproducibility era) — opportunistically usable earlier if any future output anomaly is suspected | ⏳ pending step 18 |

**C2 era combined sprint** (step 17b) — REVISED 2026-05-12 early morning session 3 continuation (**B1 ✅ DONE this commit — LAST AUDIT ITEM**): C2 core (3-5 d ✅ done) + B12 (~2 hours ✅ done) + B10 (~0.5 d ✅ done at `3c00428`) + B6 (0.0 d ✅ subsumed by B10 at `24250b2`) + B2 (0.5 d ✅ done at `76b3b04`) + B3 (0.3 d ✅ done at `ceb2766`; closed by architectural reframing) + B4 (~0.5 d ✅ done at `2bd5222`) + **B1 (~0.5 d ✅ done this commit; closed by architectural reframing — the audit-table "physics port" framing was a misread)** = **0 d remaining** for B-bundles (was 3-5 d budgeted for B1; closed in ~0.5 d). Plus C2 close-out (full 4-xval verification + tag): ~0-1 d (tag-only; xval already verified in this commit). **Total step 17b remaining: ~0-1 day (tag + push only).**
**Step 18 bundle**: B5 + B7 + B8 + B9 + B13 + B14 = **~4-6 days**.
**Step 17d bundle**: B11 = **0.5 day**.

Per `notes/STEP_17b.md` §5 + §3a.7 for the full bundling rationale + B12 forensic record.

### Substantive-validation NaN finding (2026-05-11 evening; CRITICAL; audit item B12)

**Discovered during C2 core verification 2026-05-11**: while diagnosing apparent NaN values in a `mpirun -np 1 -parallel` smoke test, isolation experiments revealed that **ALL FOUR C1 cross-validation scenarios produce NaN-laden outputs** at the C1 tag baseline (`v0.17.0-step17a-c1-year-outer-single-process` at commit `8aafe84`). The "GO/NO-GO gate PASSED for all 4 scenarios" claim at C1 close-out was nominally true (byte-equality preserved between gridcell_outer and year_outer) but substantively misleading: both modes produced byte-identical NaN-laden outputs.

**Forensic chain (full record in `notes/STEP_17b.md` §3a.7)**:

| Test ruled out | Method | Result |
|---|---|---|
| C2 MPI code | Revert to C1 (8aafe84) + rebuild + rerun xval | Identical NaN |
| `MPI_Initialized` vs `GuessParallel::parallel` | Test without `-parallel` flag | Identical NaN |
| Loop-ordering mode | Both gridcell_outer + year_outer | Identical NaN bytes |
| Short spinup | nyear_spinup ∈ {2, 10, 30}; freenyears ∈ {0, 5, 15} | All NaN |
| Crop module | Drop `crop_n.ins` import | Still NaN |
| Gridcell specificity | 4 cells across 76°N, 80°N, 54°N, -33°S | All NaN |
| Soilmap match | Cells WITH exact soilmap matches | Still NaN |
| Search-radius interpretation | dist=0 exact climate matches | Still NaN |
| Climate input quality | Inspected T_anom Kelvin values: 237-276 K (realistic Arctic) | Sane |

**What's confirmed**: NaN first appears at simulation Year 2 Day 1 in `soil.NH4_mass` diagnostic at `lpjguess/modules/somdynam.cpp:574`. Then propagates to vegetation establishment + C/N flux outputs.

**Plausible remaining root cause hypotheses (for B12 investigation)**:

1. LPJ-GUESS vegetation/soil initialization for `-input imogen` has an undiscovered defect that surfaces in smoke runs; production main.ins's LPJG main loop with engine ASCII climate has never been validated to produce non-NaN (F-10 deadlock blocked it pre-C1; C1's skip_inprocess_engine_run unlocked it but NaN issue went unnoticed)
2. LPJG-internal bug in `ImogenInput::get_climate_for_gridcell` or the monthly→daily interpolation path
3. `wetlandpfts.ins` + `global.ins` interaction that mis-initialises soil N pools
4. LandSyMM_LPJ-GUESS fork-specific issue (could be diagnosed by F-11 Backport Sprint preparation comparing against `trunk_r13078`)
5. A NaN-aware code path in soil-N integration (e.g., divide-by-zero guarded by IFNLIM that the smoke .ins config bypasses)

**Path forward**: NEW audit item **B12** added (above) as CRITICAL PATH bundled with C2 era. Must land BEFORE C2 close-out tag so `v0.17.5-step17b-c2-mpi-sync` is on substantively-validated baseline.

**xval harness hardening (this same commit)**: `scripts/cross_validate_year_outer.sh` updated to add substantive-validation NaN-check gate (FAILs with exit code 3 if NaN detected; was previously PASS based on byte-equality alone). All 4 cross-validation scenarios will now correctly REPORT FAIL until B12 is resolved — forces explicit attention. Documented in `notes/STEP_17b.md` §3a.8.

**The C1 close-out tag `v0.17.0-step17a-c1-year-outer-single-process` is preserved in git history** — it represents the byte-equality validation milestone which IS a real achievement (year_outer mechanics ARE byte-equivalent to gridcell_outer). The substantive-validation FAIL is a NEW, separate gate added 2026-05-11 to catch a previously-undetected gap.

### Tracking discipline (committed 2026-05-07)

1. **At end of every step** that touches FOLLOWUPS.md, refresh the
   "Last updated" date and review every OPEN entry for stale timing.
2. **At start of step 17** (validation milestone), do a hard sweep:
   convert F-10 + F-12 into in-progress sprint work; ensure no other
   open items have become blockers since being deferred.
3. **At end of Phase 1** (after step 19), the Backport Sprint (F-11)
   forces a final review of every `lpjguess/` source change, which
   will surface anything else still deferred.

### Operational heuristics — lessons learned (persistent; for current + future chats)

Standing rules of thumb extracted from forensic episodes in this rebuild. Inheritable: a fresh chat reading `FOLLOWUPS.md` should treat these as defaults.

1. **`.ins` parity-with-original is the FIRST-LINE forensic step when outputs look wacky.** _Origin: B12 (2026-05-11 session 3)._ A single `ifcalccton 0` divergence in `runs/SSP1-2.6/main_xval_*.ins` from the inherited `global.ins` baseline (Version A’s `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/global.ins` sets `ifcalcsla 1` and `ifcalccton 1`) silently produced NaN-laden outputs that read as “PASS” under byte-equality. Before deep code instrumentation, **diff our `.ins` set against the original codebases’**:
   - `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/`
   - `version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/landsymm_imogen/SSP1_RCP26/`
   - and the inherited `data/ins/global.ins` / `arctic.ins` / `europe.ins` from `LandSyMM_LPJ-GUESS` / `LPJ-GUESS-integrated`.

   Treat any divergence as suspect until classified as **intentional** (smoke-scale / xval-specific; document rationale inline at the parameter) or **unintentional** (open follow-up). A one-time formal version of this audit is tracked as **B14**.

2. **Byte-equality is necessary but not sufficient.** _Origin: same episode._ NaN-vs-NaN compares equal byte-for-byte. Substantive-validation gates (NaN-check; physical-bounds sanity) must run alongside `cmp`-style equality. The `scripts/cross_validate_year_outer.sh` NaN-gate (committed `f13b302`) is the canonical example.

3. **Skip-by-default code paths are silent traps.** _Origin: same episode._ When an `if<flag> 0` short-circuits an initialiser (`init_cton_min` skipped → `cton_leaf_min == 0` → 0/0 in respiration), the resulting state is _legal_ to the parser and _broken_ at runtime. Defensive fail-fast at the consumer site is the structural fix (B13). When auditing new code, ask: "what initialiser does my non-default flag suppress, and what enforces the manual replacement?"

4. **Production gridlists are not interchangeable with smoke gridlists.** _Origin: B12 N-deposition lap (Part 19)._ The N-dep archive is exact-match-only against `gridlist_in_62892_and_climate.txt`; arbitrary smoke cells fail with `getndep(): Grid cell not found`. Pick a smoke cell from the production gridlist when any input archive is exact-match-keyed.

5. **When in doubt, ask the original codebase what it would have done.** _Origin: B12 closure._ The Version A `.ins` set is the closest-to-canonical reference for the LPJG–IMOGEN coupled run; diff against it before hypothesising LPJ-GUESS internal bugs.

6. **Asymmetric file-size scaling across files written from the SAME loop ⇒ check single-OPEN/CLOSE-gating root cause across a unit-reuse chain.** _Origin: B6 (2026-05-11 session 3 continuation)._ The pre-B10 forensic on `imogen/code/IMOGEN/output/1871/` showed three apparently-unrelated symptoms — T/P/SW/DTEMP doubled to 3262 lines; WET stuck at 1631; fa_ocean contaminated by +1631 WET-format integer rows — that ALL traced to one bug: the alternating-year `IF(IYEAR.EQ.YEAR1)` OPEN gate plus mid-loop unit-95 reuse for `fa_ocean.dat`. Rule of thumb: when a multi-year writer block emits files with **different** scaling factors (some 1×, some 2×, some +δ), suspect a single OPEN/CLOSE gating bug + unit-reuse interleaving rather than chasing each file's discrepancy independently. Check whether `STATUS='REPLACE'` resets each file fresh per year-iteration, and whether mid-loop OPEN of one file on the same unit silently auto-closes the previous file. Before crafting separate fixes for each symptom, **verify whether one structural fix (unconditional per-iteration OPEN/CLOSE) cures all of them**.

7. **Stale forward-reference TODOs are architectural-finding triggers — investigate the actual code structure before mechanically replicating from a sibling implementation.** _Origin: B3 (2026-05-12 night, session 3 continuation)._ The `// TODO at step 9.5b: replicate this in the REGRID branch.` comment at `lpjguess/modules/climatemodel.cpp` ~line 894 had been on the work-tracker for ~2 weeks as "C++ Tmin/Tmax in REGRID branch (~0.5 d, mechanical mirror of B2)." The B3 prompt itself led with confident assumptions ("identify the 5 sub-edit insertion sites in the REGRID branch mirroring B2's Fortran sites… verify whether REGRID branch uses tOutMRegrid/dtempOutMRegrid arrays — grep to confirm"). One `rg "REGRID\|regrid" climatemodel.cpp` revealed only 3 hits — the dead-code `bool regrid` declaration, the TODO itself, and one unrelated comment — and **no REGRID branch existed**. The TODO was an aspirational forward-reference from the step-9.5 author anticipating a future REGRID branch that was never built; the documentation had drifted to imply parallel structure where none existed. Rule of thumb: when a sibling implementation has a structural feature (e.g. Fortran's `REGRID` branch) and a TODO claims the C++ port "should have one too", **the first pre-implementation step is always a forensic grep for the actual structural anchor** (`if (regrid)`, `*Regrid` arrays, `REGRID_CLIM` function calls). If the anchor is absent, the right outcome is **close-by-architectural-reframing** — convert the TODO into a forward-looking maintenance directive (so the algebra is documented for the day someone does build that branch), update the cross-engine parity matrix to reflect actual state (not aspirational state), and **do not invent the branch retroactively**. Documentation drift compounds: every cycle that says "C++ has Tmin/Tmax in non-REGRID; REGRID gap is B3's scope" makes the next reader believe a REGRID branch exists.

8. **Signal-of-life banner-presence assertion for every code-path-gated cross-validation.** _Origin: B15 (2026-05-12 afternoon-evening, session 3; 17c.0.0 forensic record)._ The C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` was issued with annotation language "all 4 xval scenarios PASS substantive against build/guess + build_mpi/guess single-process" — but session-3 onboarding audit revealed that **all four PASSes were false positives**: the `framework_loop_mode` parameter (Class 1; declare_parameter-bound C++ `xtring`; consumed via direct C++ variable read at `framework.cpp:464`) was being set in the xval harness using Class-2 syntax (`param "framework_loop_mode" (str "$mode")`), which writes only to the `Paramlist` dictionary and never touches the C++ variable. Both Run A (gridcell_outer) and Run B (year_outer-intended) silently ran the same code path; bit-equality of byte-identical outputs trivially passed; the `[year_outer]` diagnostic banner at `framework.cpp:502` was present zero times in Run B `run.log` for any of the four C1+C2 xval reports. Rule of thumb: when a cross-validation harness's Run A and Run B exercise different gated code paths in the same binary (`framework_loop_mode == "year_outer"` vs `"gridcell_outer"`; `coupling_mode "tight"` vs `"prescribed"` vs `"loose"`; `skip_inprocess_engine_run` variations; any future flag-gated variant), the harness MUST: (a) place a unique `dprintf` banner inside the gated branch; (b) grep both run.logs for the banner in the compare phase; (c) assert `banner_a == 0` AND `banner_b >= 1`; (d) exit non-zero (new dedicated exit code) on either invariant violation. Bit-equality + NaN-cleanliness are necessary but not sufficient — they pass trivially when both runs collapse to the same code path; a signal-of-life assertion converts that degenerate-pass class into a hard fail. **Operational corollary**: every newly-introduced gated code path needs a banner before its xval can be considered substantive. Without the banner, the xval is degenerate-pass-prone by construction. The B15-fix commit (Step 17c.0.1) lands the prototype implementation in `scripts/cross_validate_year_outer.sh::compare_outputs()` for the year_outer banner; subsequent gated-path xval extensions inherit the same pattern. Full forensic at `notes/STEP_17c.md` §0.5 (`plib` parser source-level walkthrough proving the two storage paths are mechanically disjoint) + §0.6 (why the defect wasn't caught earlier) + §0.10 (this rule's full statement).

---

## OPEN

### F-1 — Upload IMOGEN data tarballs to a permanent host

- **Trigger**: step 4 (`notes/STEP_4.md` §3 + §9). Decision #5 (incremental
  rebuild, single-codebase) plus the chosen Option C (external fetch
  script + checksum manifest) over Options A/B/D.
- **State**: 4 tarballs (49 MB total) sit at the sibling path
  `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm_data/`
  on the workstation. They are NOT on a public host yet, so a fresh
  clone of the repo cannot run `tools/fetch_imogen_data.sh` against
  an `https://` base — only against a local-directory base.
- **Action**: pick a host and upload. Two recommended options:
  | Host | Pros | Cons | Notes |
  |---|---|---|---|
  | **Zenodo** | DOI for citation; permanent archival; 50 GB/record; integrates with GitHub for release-triggered uploads | A bit more friction (per-version DOI, separate web UI for new versions) | Best fit for the GMD paper's "Code & data availability" statement |
  | **GitHub Releases** | Easier dev iteration; tied to git tags directly via `gh release`; `gh release create` from CLI | 2 GB per-asset cap (we're under 19 MB so fine); no DOI; vendor lock | Best fit for fast-cycle development |
  | (combo) | Use GitHub Releases during development; promote to Zenodo at v1.0 | | Recommended path |
- **After upload**:
  1. Edit `tools/README.md` to add the canonical `IMOGEN_DATA_BASE`
     URL example (e.g. `https://zenodo.org/record/<id>/files` or
     `https://github.com/dbampoh/landsymm_imogen_coupled/releases/download/v0.4.0-imogen-data/`).
  2. Edit `imogen/patterns/README.md` and
     `imogen/CRUNCEP_1960_1989/README.md` to replace the "TBD: a Zenodo
     record / GitHub Release / institutional bucket" wording with the
     real URL.
  3. Verify end-to-end on a fresh worktree:
     `IMOGEN_DATA_BASE=https://... tools/fetch_imogen_data.sh`
  4. Update `CHANGELOG.md` under `[Unreleased]` (or open a new
     `[v0.4.1-imogen-data-host-live]` patch entry) describing the
     change. Push to all three remotes.
- **Timing**: before the project becomes externally visible (paper
  submission, code release announcement). Not blocking step 5+.

### ~~F-2~~ — _CLOSED 2026-05-11 night session 3 by audit item B6 (subsumed by B10)_

- **Original trigger**: step 4 (`notes/STEP_4.md` §6 "Comparison with version_A's
  1871 output"). Our Fortran's `T_anom.dat` had 3262 lines vs
  `version_A`'s 1631 lines — exactly 2× — at otherwise-similar formatting.
- **Forensic determination (2026-05-11)**: the 2× line count is **one of three downstream symptoms of the same alternating-year writer bug B10 fixed at commit `3c00428`** (not a separate bug). The other two co-symptoms in the same `imogen/code/IMOGEN/output/1871/` directory:
  1. `WET.dat` stuck at 1631 lines (asymmetric vs T/P/SW/DTEMP) — explained by mid-1871 unit-95 reuse for `fa_ocean.dat` that auto-closes the WET.dat connection at line ~1088 (pre-fix).
  2. `fa_ocean.dat` at 11631 lines instead of 10000 (extra 1631 lines) — explained by year-1872 `WRITE(95,...) F_WET_CLIM_OUT(IGP,IMM)` appending WET-format integer rows to the still-open year-1871 fa_ocean.dat unit. Smoking-gun: `sed -n '9998,10003p' fa_ocean.dat` shows the float-to-WET-format transition exactly at line 10001.
- **Cross-validation**: `version_A/.../IMOGEN/output/1871/` reference shows T/P/SW/DTEMP=1631 lines each, WET=1631, fa_ocean=10000 (clean), dtemp_o=254 — matches the predicted post-B10 structural output exactly.
- **Mechanism**: pre-B10's `IF(IYEAR.EQ.YEAR1)`-gated OPEN + `IF(IYEAR.EQ.IYEND)`-gated CLOSE caused year 1872 of a 2-year engine call to reuse year-1871's still-open units rather than getting fresh `/1872/`-targeted files. B10's unconditional-OPEN-per-IYEAR semantics structurally fix all three symptoms simultaneously.
- **Resolution**: ZERO Fortran source change for B6. Forensic record at `notes/STEP_17b.md` §3c. Backport-IRRELEVANT (B10's backport entry already covers all 7 gates whose removal collectively fixes the B6 symptom).

### F-3 — Numerical parity: Fortran ↔ C++ IMOGEN

- **Trigger**: Decision #2 ("Phase 1 = Fortran with `ALLOCATABLE`
  arrays; Phase 2 = C++ refactor brought to numerical parity"). Step 4
  smoke-run revealed T values differ 0.1–8 K between our Fortran and
  `version_A`'s (probably-C++) reference for the same year, same GCM,
  same CRUNCEP base.
- **Action**: this is the **Phase-2 milestone** — not a tactical
  follow-up. Listed here only so it's not forgotten. Phase 2 plan is
  in `EXECUTION_PLAN.md` §II.2. Should run after v1.0 ships.
- **Timing**: post-v1.0.

### ~~F-4~~ — _CLOSED 2026-05-06 by step 7_

(Was: bug C2/C3 source fix — the polling-loop `DONE_EXIST` default;
see DONE section.)

### ~~F-5~~ — _CLOSED 2026-05-06 by step 6_

(Was: stage emission scenarios into a 5th tarball; see DONE section.)

### F-6 — Confirm CMIP6 `ql1_patt` unit alignment with IMOGEN's `DRH15M_PAT`

- **Trigger**: step 5 (`notes/STEP_5.md` §2 CAVEAT-A; §4.4). The CMIP6
  NetCDF stores `ql1_patt` with units "K-1", suggesting it represents
  delta(specific-humidity) per K of land-mean warming. The CMIP5
  ASCII column 4 (`DRH15M_PAT`) is a relative-humidity sensitivity per
  K. These are not the same physical quantity in general (they differ
  by a temperature-dependent saturation factor).
- **Symptom**: in our converted CMIP6/MRI-ESM2-0 output for cell
  (lat=82.5°, lon=281.25°, Jan), col 4 is +0.00014 — about 1500×
  smaller in magnitude than CMIP5/IPSL-CM5A-MR's -0.2364 at the same
  cell. Magnitude AND sign differ.
- **Action**: contact the upstream CMIP6 NetCDF author (likely PRIME /
  Mathison 2025) to confirm the convention. Either:
  1. The CMIP6 generator already aligned to IMOGEN's RH-sensitivity
     convention and the difference is just inter-GCM scatter (then no
     code change needed; document and close).
  2. The CMIP6 file is a specific-humidity sensitivity that needs a
     unit-conversion factor (e.g. multiply by `dRH/dq` evaluated at
     monthly mean T) before being written to col 4.
- **Workaround until closed**: we pass `ql1_patt` through directly.
  If a CMIP6-driven IMOGEN run produces hydrologically odd output
  (e.g. unphysical RH, broken precip-evap balance), revisit this.
- **Timing**: medium priority. Wait for the upstream author. If a
  CMIP6 GCM is selected for a published v1.0 run, this should be
  resolved before submission.

### F-7 — Verify CMIP6 `pstar_patt` units match CMIP5 `DPSTAR_C_PAT`

- **Trigger**: step 5 (`notes/STEP_5.md` §4.4). Our converted CMIP6/MRI
  Pstar pattern at cell (lat=82.5°, lon=281.25°, Jan) is **−49.40**;
  CMIP5/IPSL at the same cell is **+0.32**. That's a 150× magnitude
  difference plus opposite sign.
- **Possible explanations**:
  1. The CMIP6 NetCDF stores Pstar in **Pa/K** while the CMIP5 ASCII
     stores it in **hPa/K**. 100× factor would convert -49.40 Pa/K to
     -0.494 hPa/K — same order of magnitude as IPSL's +0.32, with
     reasonable inter-GCM scatter.
  2. The CMIP6 file genuinely has an opposite-sign response at this
     polar cell (different model physics).
  3. A bug in our interpolation or transform.
- **Action**: contact the upstream NetCDF author to confirm units;
  fix the converter's transform if needed. Likely a one-line fix
  (`* 0.01` to convert Pa/K → hPa/K).
- **Workaround until closed**: documented in `notes/STEP_5.md` §4.4.
- **Timing**: medium priority; same authoring contact as F-6 so can
  be batched with that.

### F-9 — Complete the half-scaffolded miscoutput IMOGEN climate-input diagnostic outputs (refined at step 9.5)

**Refinement 2026-05-07 (during step 9.5)**: investigation revealed an
unanticipated infrastructure dependency:

- The 12 `xtring file_*_anom` parameter declarations and `Table out_*_anom`
  member declarations in `miscoutput.h` ARE in place (gated on
  `IMOGENConfig::print_imogen_output==true`)
- BUT: a `create_output_table()` call in `define_output_tables()` AND a
  per-gridcell `outlimit()`/`add_value()` call in `outannual()` are missing
- **The missing per-gridcell `outlimit()` call has no obvious data source**:
  `Climate` has only single-day fields (`temp`, `prec`, `relhum`, `u10`,
  `tmin`, `tmax`, `insol`) and 20-year-window aggregates (`mtemp_min20`,
  `mtemp_max20`); **no per-month accumulator array is exposed**.
- The original step 9.5 plan assumed `gridcell.climate.mtemp[m]` was
  accessible — it isn't.

**Two paths to close F-9 properly**:

  - **Option A** (cleaner; ~50 LOC infrastructure addition): Add per-month
    accumulator arrays to `Climate`:
    ```cpp
    // In framework/guess.h Climate class:
    double mclimate_temp[12], mclimate_prec[12], mclimate_relhum[12],
           mclimate_u10[12], mclimate_tmin[12], mclimate_tmax[12], ...;
    ```
    Reset at year-start, accumulate daily values, divide by `mthday[m]` at
    month-end (or at year-end for outannual access). Then F-9's outannual
    can `outlimit_misc(out, out_t_anom, gridcell.climate.mclimate_temp[m])`
    inside a 12-month loop.
  - **Option B** (smaller; ~15 LOC cross-module getter): Expose
    `IMOGENCFXInput::dtemp[]` (per-day arrays, populated each year per
    gridcell) to `MiscOutput::outannual` via a getter or a globally-
    accessible reference. F-9's outannual aggregates per-day → per-month
    inline. Drawback: introduces cross-module coupling (output module
    reaching into input module state).

**Recommendation**: Option A. Cleaner; the per-month accumulator is generally
useful (e.g., for any other `m*` monthly diagnostic outputs) and keeps
miscoutput input-module-agnostic.

**Status**: deferred from step 9.5 to a focused step 9.5c (or merge with
the F-12 sprint if convenient — F-12's two-process design naturally
provides the per-month aggregation point in the engine-output side).

(Original entry continues below for reference.)

### F-9 — Complete the half-scaffolded miscoutput IMOGEN climate-input diagnostic outputs (original entry)

- **Trigger**: step 8 (`notes/STEP_8.md` §2.1, §3.5). While
  investigating where step 8's LPJG-side handshake writer should live,
  discovered that `lpjguess/modules/miscoutput.cpp/h` already contains
  **half-scaffolded IMOGEN diagnostic-output stubs**: 12 file-name
  parameters declared via `declare_parameter("file_t_anom",
  &file_t_anom, ...)` (and 11 other variables: file_p_anom,
  file_sw_anom, file_dtemp_anom, file_wet, file_fa_ocean,
  file_dtemp_o, file_co2, file_relhum_anom, file_tmin_anom,
  file_tmax_anom, file_wind_anom), 12 corresponding `Table out_*_anom`
  member declarations in the header — **but no `create_output_table()`
  calls in `define_output_tables()` and no `add_value()` calls in
  `outannual()`**. The whole pipeline is inert. A `// FIXME: DKB`
  marker at line 122 of miscoutput.cpp explicitly flags the
  work-in-progress state.
- **What scope F-9 covers**:
  - Add `create_output_table(out_t_anom, file_t_anom, ...)` calls
    in `MiscOutput::define_output_tables()` for the 12 diagnostic
    tables.
  - Add per-gridcell `outlimit(out, out_t_anom, ...)` calls in
    `MiscOutput::outannual(Gridcell&)` that write the actual IMOGEN
    climate values (T_anom, P_anom, etc. — the variables IMOGEN
    supplied to LPJ-GUESS for each year × each cell). The data source
    is `imogencfx`'s per-cell `dtemp[]`, `dprec[]`, `dinsol[]`,
    `ddtr[]`, `drelhum[]`, `dwind[]` arrays (see imogencfx.h:128-148).
- **Difference from step 8 (already implemented)**: step 8's
  `imogenoutput.cpp/h` writes the LPJG → IMOGEN handshake control
  files (`imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt`,
  `imogen_lpjg.txt`, `done`). F-9's miscoutput stubs would write the
  IMOGEN → LPJG climate-input diagnostics (`t_anom.out`, `p_anom.out`,
  etc.) as standard `.out` tabular files for users to inspect what
  climate IMOGEN supplied. **Different output channels for different
  purposes.**
- **Cleanup pre-completed**: step 8 already removed the dead
  `getImogenData(int, int)` random placeholder helper from
  `miscoutput.h` (it returned non-deterministic random values from
  `std::random_device`; was never invoked anywhere; misleading
  semantically). Plus removed the unused `#include <random>`. F-9
  starts from a slightly cleaner base.
- **Best timing**: step 9.5 of the formal V.1 plan, alongside the
  Rh_anom / W_anom / Tmin_anom / Tmax_anom output parity work
  (climate-output enhancements per Decisions #11 and #12). Both
  concern climate-output diagnostics; bundling them shares review
  effort.

### F-10 — Framework-loop ordering vs proper tight-coupling synchronization (significant)

- **Trigger**: step 8 (`notes/STEP_8.md` §2.4 + §4). While
  investigating where step 8's `imogenoutput.cpp` should hook into
  the LPJ-GUESS framework's per-year aggregation flow, discovered
  the canonical loop structure of `lpjguess/framework/framework.cpp`
  lines 411-516:

  ```cpp
  while (true) {                                           // outer: per-gridcell
      Gridcell gridcell;
      if (!input_module->getgridcell(gridcell)) break;
      // ... setup ...
      while (input_module->getclimate(gridcell)) {         // inner: per-day, ALL years
          simulate_day(gridcell, input_module.get());
          output_modules.outdaily(gridcell);
          if (date.islastday && date.islastmonth) {
              output_modules.outannual(gridcell);          // year-end, per gridcell
          }
          date.next();
      }
      // End of all-years loop for THIS gridcell
  }
  ```

  `getclimate()` returns false when ALL years have been simulated for
  the current gridcell. So **each gridcell processes ALL its years
  before moving to the next gridcell**. This is per-gridcell-outer /
  per-day-inner across all years.

- **The architectural problem**: Tight coupling (per-year-globally-
  synchronized handshake — IMOGEN's year-N+1 climate uses LPJ-GUESS's
  year-N globally-aggregated NEE feedback) **fundamentally cannot be
  cleanly implemented** with this loop ordering. When gridcell-1
  finishes year-1, gridcell-2 hasn't yet started year-1 (it's still
  on the next gridcell setup phase). When gridcell-1's `outannual`
  fires for year-1 and our handshake writer flushes, the flushed NEE
  represents only gridcell-1's contribution. Subsequent gridcells'
  year-1 contributions arrive at later wall-clock times, after the
  IMOGEN engine has already consumed the (incomplete) handshake.

- **Why this surfaced now and not earlier**: The predecessor framework
  already has this issue — but [CMI §1.1] specifically notes "the
  system has never run end-to-end." The predecessor's coupled mode
  was **scaffolded but never validated**; the polling loop in
  `imogen_lpjg.f` and `climatemodel.cpp` had been "neutered" (bugs
  C2/C3) to make standalone runs work, masking the synchronization
  problem from ever surfacing in practice. With step 7's fixes
  un-neutering those polling loops + step 8 actually writing the
  handshake files, the architectural gap is now exposed.

- **Implication for v1.0**:
  - `imogenoutput.cpp` (step 8) writes per-gridcell-rolling values:
    each `outannual` call adds this gridcell's contribution to the
    per-year accumulator, and the year-change-detection flushes
    whenever the year-N+1 first gridcell triggers it. The flushed
    values are non-empty, sensible per-gridcell-rolling, but NOT
    globally-synchronized.
  - V.1's stated step-8 verification milestone (*"non-empty handshake
    files; sensible NEE in PgC/yr"*) is met — the values look right
    in magnitude.
  - V.1's step-17 validation milestone (*"CO2 RMSD ≤ 5 ppm vs NOAA
    GMD"*) **may show systematic bias** from the non-synchronized
    feedback. We will discover empirically at step 17 whether the
    bias is significant. If yes → F-10 becomes blocking for v1.0
    publication-quality runs. If no → F-10 can stay deferred.

- **Phase-2 recommended approach (per user guidance 2026-05-06)**:

  Three principles, in order of importance:

  1. **DO NOT alter the existing framework.cpp loop**. The
     per-gridcell-outer ordering is correct and battle-tested for
     standalone, loose-coupling, prescribed-coupling, and parallel
     (HPC) runs. Restructuring it would risk breaking all of those.

  2. **DO add a runtime parameter** that gates a NEW per-year-outer /
     per-gridcell-inner code path which lives ALONGSIDE the existing
     code path. Example parameter:
     `framework_loop_mode = "year_outer" | "gridcell_outer"` (default
     `"gridcell_outer"` to preserve backward compatibility).

  3. **DO implement the new code path as an additive extension**,
     mirroring the **LandSyMM-fork-into-LPJ-GUESS-LTS integration
     pattern** from the predecessor project earlier in the chat
     history. In that integration: new fork-specific behavior was
     gated behind `do_potyield`, `landsymm_*`, etc. ins parameters
     that activated alternative code paths; the upstream LTS
     behavior was preserved as the default and untouched.

  Concrete implementation sketch (subject to refinement at Phase 2):

  ```cpp
  // framework.cpp -- new alternative loop, gated on framework_loop_mode
  if (loop_mode == "year_outer") {
      // Phase-2 path: per-year-outer / per-gridcell-inner
      load_all_gridcells_into_memory(gridlist);  // up-front
      for (int year = first_year; year <= last_year; ++year) {
          for (auto& gridcell : gridcells) {
              simulate_year(gridcell, year);
              output_modules.outannual(gridcell);
          }
          // ALL gridcells now done for year N; flush handshake here
          imogenoutput.flush_pending_year();
          // Trigger IMOGEN engine for year N+1's climate
          if (coupling_mode == "tight") {
              climatemodel.run_year(year + 1);
          }
      }
  } else {  // default gridcell_outer
      // Existing loop unchanged
      while (true) {
          Gridcell gridcell;
          if (!input_module->getgridcell(gridcell)) break;
          while (input_module->getclimate(gridcell)) { /* ... */ }
      }
  }
  ```

  Trade-offs for the year-outer path:
  - Memory: must hold all gridcells in memory simultaneously
    (vs streaming one at a time). For 62 538 cells × ~MB-each
    in-memory state → ~tens of GB. Workable on workstation, large
    on cluster nodes. Mitigation: per-rank gridlist subsetting
    in MPI mode (existing predecessor cluster pattern).
  - I/O: per-year `outannual` calls happen at very different wall-
    clock times in the existing path; bundled tightly in the new
    path. Disk I/O patterns shift; may need re-tuning.
  - Determinism: the new path is deterministically per-year; the old
    path is per-gridcell-with-eventual-aggregation. Outputs would
    differ in subtle ways; cross-validation is essential.

  Both paths sharing the same `imogenoutput.cpp::outannual` and
  `flush_pending_year` interfaces means the writer code itself
  doesn't need to change. Only the framework's call orchestration
  changes.

- **Action timing**:
  - **Now (v1.0)**: documented in this F-10 entry; cross-referenced
    from `notes/STEP_8.md`, `lpjguess/modules/imogenoutput.h` doc
    block, `EXECUTION_PLAN.md` step 8 row.
  - **Step 17** (validation): empirically test whether the
    per-gridcell-rolling handshake passes V.1's RMSD thresholds.
    Document outcomes.
  - **Phase 2 (post-v1.0)**: implement the parameter-gated
    additive year-outer code path. Estimated effort 1-2 weeks
    full-time including cross-validation.

- **Cross-references**:
  - `notes/STEP_8.md` §2.4 (the investigation finding), §4 (the
    detailed Phase-2 recommendation)
  - `lpjguess/modules/imogenoutput.h` doc block (mirrors this
    architectural caveat in the source code itself)
  - `EXECUTION_PLAN.md` V.1 step 8 row (marked ✅ with F-10 caveat)
  - `[CMI §1.1]` (the original "never ran end-to-end" note that
    F-10 formalizes the cause of)

### F-11 — Backport all `lpjguess/` changes to `trunk_r13078` for paper-stage consistency

- **Trigger**: user clarification 2026-05-06. Per Decision #3
  (`EXECUTION_PLAN.md` II.11), our v1.0 rebuild operates on the
  `LandSyMM_LPJ-GUESS/` fork (which the user calls the "integrated
  LTS" per terminology established in their integration project
  before this coupled-model project began — same artifact, two
  names). The **separate** `trunk_r13078` fork inside
  `version_A/Integrations/trunk/` and `version_B/Integrations/trunk/`
  was used in the working paper's **Stage 1 PLUM yield runs**, so for
  Stage-2 / paper consistency, both forks must eventually be
  fully-coupled-model-capable and runtime-switchable.
- **Action**: at the end of Phase-1 (after step 19's V.1
  verification), execute the **Backport Sprint** described in
  `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §4. In short:
  1. Import `version_A/Integrations/trunk/trunk_r13078/` as a
     parallel tree under our repo (e.g. `lpjguess_trunk_r13078/`).
  2. Reconcile the 6-file baseline diff (cosmetic + the critical
     `exit(200)` removal at `imogencfx.cpp:483`).
  3. Walk each ledger entry in `TRUNK_R13078_BACKPORT_LEDGER.md` §3
     in step order and replicate the recorded edit in
     `lpjguess_trunk_r13078/`.
  4. Add a build-time switch
     (`-DLPJGUESS_BACKEND=landsymm_fork|trunk_r13078`, default
     `landsymm_fork`) so users / CI tests can pick either backend.
  5. Run V.1's full verification (steps 1-19 milestones) against
     the `trunk_r13078` backend; cross-check outputs match within
     numerical tolerance.
- **Estimated effort**: 1-2 days of focused work.
- **Maintenance discipline (immediate, not deferred)**: every commit
  that touches `lpjguess/` C++ source files **must add a
  corresponding entry to `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3**
  with step-N / commit-hash / date / file / line range / description
  / backport-guidance fields. This is what makes the eventual sprint
  mechanical instead of archaeological.
- **Cross-references**:
  - `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (the running ledger;
    populated retroactively for steps 1-8 at creation time)
  - `EXECUTION_PLAN.md` II.11 (Decision #3 + the terminology
    clarification 2026-05-06)
  - `notes/STEP_1.md` §A (the import audit that established the
    6-file baseline diff)
  - `_phase2_findings/02_lpjguess_trunk_r13078.md` (Phase-2
    investigation of `trunk_r13078`'s coupling surface area)

### F-13 — Post-v1.0 paper-stage comparative-analysis framework

- **Trigger**: user guidance 2026-05-07 after step 13 commit. The user
  spelled out the comparison-plot framework needed for the GMD paper
  (working draft at
  `version_A/.../References/IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`,
  currently incomplete: intro + methods sections only, with supervisor
  comments + edits applied).
- **Three comparison axes for paper figures + stats**:

  **AXIS 1 — Atmospheric GHG concentration trends (CO2, CH4, N2O)**:
  IMOGEN engine runs forced by:
    - RCMIP-raw emissions (no substitution; reference baseline)
    - RCMIP-substituted emissions (our modelled anthro + LPJG natural)
  Compare resulting atmospheric concentration trajectories. **Both
  trajectories now producible** because intermediary_py's Component C
  outputs `RCMIP_total_Mt` (raw RCMIP) and `Total_Mt` (our substituted)
  side-by-side in `outputs/component_c/data/integrated_emissions_*.csv`.
  Adapter (step 13) can convert either column to engine-readable
  format; a small flag could be added to select RCMIP-raw mode for
  the comparison plots.

  **AXIS 2 — Climate trends and patterns (T, P, SW, RH, wind, DTR, Tmin/Tmax)**:
  Two sub-options for what to compare against:
    - **Sub-option 2A**: RCMIP-raw IMOGEN climate vs RCMIP-substituted
      IMOGEN climate (parallel to Axis 1; isolates the effect of OUR
      emissions modelling on downstream climate)
    - **Sub-option 2B**: RCMIP-substituted IMOGEN climate vs ISIMIP3b
      forcing climate (the climate used for Stage 1 PLUM-yield runs;
      validates IMOGEN's climate against an established reference)
  User notes Sub-option 2B is "the alternative" but **both could be
  valuable** in the paper.

  **AXIS 3 — LPJ-GUESS ecosystem outputs**:
  cflux, cmass, anpp, mch4, ngases, etc. under each of Axis 2's
  climate forcings. Quantifies the *propagated* effect of emissions
  modelling choices on ecosystem responses (the science the paper is
  ultimately about).

- **Existing template scripts to leverage** (per user 2026-05-07):
  `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Python-scripts/comparative_analysis/analysis/`
  (identical to version_B's same path; 73 MB total):
    - `carbon_comparison.py` (15 KB, ~370 LOC) — LPJG ecosystem-carbon
      output comparison (Axis 3)
    - `climate_comparison.py` (26 KB, ~640 LOC) — IMOGEN climate vs
      ISIMIP3b comparison (Axis 2 sub-option 2B)
    - `preprocess_isimip_cache.py` (6 KB, ~250 LOC) — preprocesses
      ISIMIP3b cache for the climate_comparison consumer
    - 12 reference output dirs (`outputs_carbon_ssp{126,245}_*` and
      `outputs_ssp{126,245}_climate_*`) showing example deliverables
    - `summary_tables*.xlsx` (3 files) — example stats tables
    - `comprehensive_synthesis.md` (15 KB) — narrative discussion
    - `IMOGEN_Prezi_final.pptx` (23 MB) — presentation context
  These scripts are **enhanceable starting points**; user explicitly
  flagged "perhaps you may have ideas even there as well" for how to
  improve them.

- **What intermediary_py already provides (per Component C)**:
    - `outputs/component_c/data/integrated_emissions_{ch4,co2,n2o}.csv`
      (Anthro, Natural, Total, RCMIP_total, FAIR_natural, Default_total
      side-by-side)
    - `outputs/component_c/data/conventional_comparator_{ch4,co2,n2o}.csv`
      (raw RCMIP comparator)
    - `outputs/component_c/data/hybrid_comparator_{ch4,co2,n2o}.csv`
      (hybrid; with explicit source segments)
    - `outputs/component_c/data/external_comparators_{ch4,co2,n2o}.csv`
      (published budget ranges, e.g. GCB 2025 Friedlingstein et al.
      ESSD 17, with [Lo, Best, Hi] decadal means for stats validation)
    - `outputs/component_c/figures/...` — comparator plots (with
      `python3 run_all.py` full mode; not `--skip-plots`)

  User notes: "intermediary_py already has plotting scripts that
  plot the various sector and total emissions trends in various
  comparative contexts (no comparative stats with the plots though)" —
  so adding **comparative stats alongside the plots** is a paper-stage
  enhancement opportunity (decadal means + IQR; bias + RMSE vs raw
  RCMIP; RMSE vs GCB external benchmark; etc.).

- **Action plan (post-v1.0; specifically post-step-19 release)**:

  1. **Bring up the comparative_analysis scripts into the rebuild**:
     copy + clean up + integrate into `tools/comparative_analysis/`
     (or a new top-level `analysis/` dir; decide at the time)
  2. **Run AXIS 1 comparison**: produce IMOGEN-engine atmospheric CO2/
     CH4/N2O trajectories for RCMIP-raw vs RCMIP-substituted; plot +
     stats. Single set of figures + tables for the paper's results section.
  3. **Run AXIS 2 sub-option 2A AND 2B comparisons**: produce IMOGEN
     climate + ISIMIP3b climate side-by-side over the v1.0 coupled
     run period. Spatial maps (key variables, decadal means) + temporal
     trends per cell + summary tables.
  4. **Run AXIS 3 comparisons**: produce LPJ-GUESS outputs under each
     climate forcing. Spatial + temporal + summary tables.
  5. **Add comparative stats** to all plots: RMSE, bias, mean, std,
     decadal-mean, IQR, comparison against published budgets.
  6. **Revise paper draft** at `paper/manuscript_draft.docx`:
     - Update intro + methods to reflect the RCMIP backbone (currently
       IIASA-based per user 2026-05-07)
     - Add results section using the AXIS 1/2/3 figures + stats
     - Add discussion of model intercomparisons and limitations
     - Add conclusions
     - Add complete references (the planned reference-PDF list in
       `paper/README.md` covers most; add new references uncovered
       during analysis)
     - Address the supervisor's comments + edits already in the draft
  7. **Submit to GMD** as planned.

- **Cross-references**:
  - `paper/README.md` (extended at step 13 to reference this F-13)
  - `intermediary_py/imogen_ghg_controller/outputs/component_c/data/`
    (the integrated_emissions / *_comparator outputs)
  - `version_A/.../Python-scripts/comparative_analysis/analysis/`
    (the existing template scripts)
  - `EXECUTION_PLAN.md` step 18 (paper revision step)
  - `EXECUTION_PLAN.md` Decision #1 (RCMIP substitution backbone)
- **Status**: deferred to post-v1.0 (post-step-19 release). The
  current v1.0 work is focused on getting the coupled model to RUN
  end-to-end; the paper-stage analysis framework comes after.

### F-12 — Multi-pass / two-process tight-mode verification design

- **Trigger**: step 9 (`notes/STEP_9.md` §4.4 + §6). The smoke test
  empirically confirmed F-10's architectural deadlock: in v1.0
  single-process `imogencfx` mode, the IMOGEN engine cannot terminate
  cleanly without LPJG-supplied per-year handshake updates, AND LPJG
  cannot run its main loop until `imogencfx::init()` returns (which
  it cannot until the engine terminates). **Hard deadlock, observed
  in BOTH `coupling_mode="tight"` and `coupling_mode="prescribed"`
  modes.**
- **What this means for v1.0**:
  - Step 8's `ImogenOutput::flush_year` writer mechanics are correct
    in code, units, and registration — but the function NEVER FIRES
    in v1.0 single-process mode because LPJG main loop never runs
  - Bug C35's relative-path fix is correct in concept but un-testable
    in v1.0 (deadlocks immediately because `RUNFLUX_EXIST=0`)
  - V.1 step-9 verification milestone (NEE 2x perturbation → CO2
    trajectory shift) cannot be tested in v1.0
  - The `coupling_mode = "prescribed"` workaround (with bootstrap
    handshake files + absolute-path static-IIASA `FILE_LPJG_FLUX`)
    runs the engine through climate output successfully but still
    deadlocks before LPJG main loop runs — see `notes/STEP_9.md` §4.4
- **F-12 design space** (three options; pick at Phase-2 kickoff):
  - **Option A — Multi-pass (one-binary, manual orchestration)**:
    User runs `guess` once with N pre-populated handshake files for
    year 1. Engine consumes them, runs year 1's climate to disk, then
    deadlocks polling for year-2 handshake. User kills `guess`, manually
    populates year-2 handshake files (or runs a tool that does so),
    relaunches `guess` with year 2's bootstrap. LPJG main loop never
    actually runs in this design — it's a pure engine-only mode.
    **Verdict: useless for actual coupling; just a workaround for
    engine-only verification. Reject.**
  - **Option B — Two-process (recommended for v1.0 → v1.1)**:
    Split the `imogen_lpjg` engine out of `imogencfx::init()` into a
    separate Fortran binary running concurrently with `guess`. The
    engine polls `<DIR_COMMON>/LPJG_main/IMOGEN/done` per year (already
    implemented in `imogen_lpjg.f`); LPJG (running concurrently in a
    separate `guess` process) writes the handshake files via step 8's
    writer per LPJG-year; engine sees the new handshake, advances to
    next year, etc. **This is what the predecessor's polling-loop
    architecture was originally DESIGNED for** — the predecessor's
    in-process port (climatemodel.cpp's `RUN_IMOGEN_ENGINE`) was a
    convenience wrapper that broke this design. Restoring two-process
    mode + step 8's writer should yield genuine year-by-year tight
    coupling. Estimated effort: 2-3 days (engine binary build setup
    via existing Fortran Makefile; orchestration script for concurrent
    launch; documentation).
  - **Option C — In-process restructure (F-10's Phase-2 design)**:
    Add `framework_loop_mode = "year_outer"` ins parameter that gates
    a NEW per-year-outer code path inside `framework.cpp`. Engine and
    LPJG would alternate per year inside the same process, sharing
    state via in-memory data structures (no file-based handshake
    needed for the in-process path). This is F-10's recommended
    Phase-2 design. Cleaner architecturally but larger surface area
    (~1-2 weeks). Gives BOTH single-binary AND parallel-HPC potential.
- **Recommendation (REVISED AGAIN 2026-05-09 per user-confirmed Path A
  refinement)**: **Skip Option B entirely**. Go straight to Option C,
  staged into 3 sub-milestones (C1 → C2 → C3) so the work is incrementally
  committable + verifiable. The 2026-05-08 plan had Option B + Option C
  sequenced; on closer architectural analysis (per session-2 chat handoff
  Part 8 and this F-12 entry's revised reasoning), Options B and C are
  **orthogonal**, not sequential — Option B addresses only single-process
  workstation tight (per-gridcell-rolling per-rank handshake; doesn't
  generalise to MPI), while Option C resolves the F-10 architectural
  deadlock at its root for both single-process AND multi-rank cluster
  contexts via the `framework_loop_mode = "year_outer"` additive code
  path. Since v1.0's stated 4-combination requirement REQUIRES Option C
  anyway (cluster + tight is gated on it), Option B becomes a redundant
  intermediate workstation-only deliverable. Skipping Option B saves
  ~2-3 days of effort + maintenance surface; the C1 sub-milestone (below)
  delivers the same workstation single-process tight capability Option B
  would have, BUT more rigorously (globally-synchronized per-cell flush
  rather than per-gridcell-rolling).
- **Staged sub-milestones for F-12 Option C**:
  - **C1 — Workstation single-process year_outer + cross-validation**
    (~1 week): add `framework_loop_mode` ins parameter (default
    `gridcell_outer`); implement `year_outer` code path in `framework.cpp`
    as additive single-process code (no MPI yet); add `getclimate_year()`
    method to relevant input modules; PRNG-state audit of
    `lpjguess/framework/randomState.cpp` (or equivalent); cross-validate
    year_outer single-process vs gridcell_outer baseline on 5-cell smoke
    × 50-yr simulation per the cross-validation protocol in the next
    bullet. Tag `v0.17.0-step17a-c1-year-outer-single-process`.
  - **C2 — Workstation MPI year_outer** (~3-5 days): add
    `MPI_Barrier(MPI_COMM_WORLD)` at year boundary (#ifdef HAVE_MPI);
    add `flush_year_globally_synchronized()` method on `ImogenOutput`
    with `MPI_Allreduce` over per-rank flux contributions; test via
    `scripts/run_parallel_mimic.sh` workstation MPI mimic
    (`mpirun -np 4` smoke); pre-requisite: address Anaconda3 mpicxx
    wrapper issue (`x86_64-conda-linux-gnu-c++` not found; install
    `gxx_linux-64` or override with `OMPI_CXX=g++`). Tag
    `v0.17.5-step17b-c2-mpi-sync`.
  - **C3 — Cluster MPI year_outer + production verification**
    (~1-2 weeks iterative SSH work): cluster deployment via
    `scripts/cluster/run_coupled.sbatch`; SSH session 1 = refine
    `env_owl.sh` placeholders against `module avail` on `owl`;
    SSH session 2 = cluster MPI build via `make_guess.sh --mpi`;
    SSH session 3 = small smoke run (4 ranks × 480-cell × 5-yr tight);
    SSH session 4+ = production-scale smoke + iteration. Tag
    `v0.18.0-step17c-c3-cluster-tight`.
- **Cross-validation protocol** (the GO/NO-GO gate at C1; ESSENTIAL):
  Run TWO simulations with byte-identical inputs (.ins / gridlist /
  seeds / climate / LU forcing):
  - Run A: `framework_loop_mode = "gridcell_outer"` (existing; trusted
    baseline)
  - Run B: `framework_loop_mode = "year_outer"` (new additive code path)
  Tolerances:
  - Soil-water balance, C/N pools without disturbance, GPP/NPP:
    **bit-exact** (these are deterministic; ANY divergence = code bug)
  - Annual cell-mean values (aggregated across whole gridlist):
    **≤ 0.1% RMSD**
  - Per-cell stochastic outputs (vegetation establishment, fire spread,
    background mortality): **≤ 1% RMSD**
  PRNG-state audit is the deepest risk surface — if LPJ-GUESS uses
  per-cell PRNG state (which a well-designed model should), outputs are
  bit-exact for deterministic processes and 1%-RMSD-level different for
  stochastic ones. If shared-global PRNG (latent design flaw), outputs
  diverge wildly → fix that BEFORE year_outer ships.
- **Status as of 2026-05-09 (after step 16 + post-step-16 docs maintenance
  + today's plan refinement)**: queued for next session(s); SHOULD fit
  comfortably in same chat as step 17a/C1 work. Workstation specs verified
  (i9-11900K; 64 GB RAM; 16 cores; Anaconda3 MPICH 4.1.1 + gcc 15.2 +
  cmake 3.31.6 available). C1 single-process workstation work fits;
  production gridlists (62k cells × ~MB ≈ 60+ GB) exceed workstation
  RAM and require cluster (=C3) for production runs anyway. NFS mount
  `owl01amd:/home → /bg/home` available on workstation (potential
  shortcut for some C3 cluster-state-inspection patterns).
- **C1 pre-flight investigation findings (2026-05-09 evening)** — all
  read-only audit; no source changes:
  1. **PRNG architecture is year_outer-friendly**: `randfrac(long& seed)`
     at `lpjguess/modules/driver.cpp:42` is a deterministic Park-Miller
     LCG taking seed by reference. Every stochastic call (`blaze.cpp`,
     `spitfire.cpp`, `vegdynam.cpp`, etc.) uses `patch.stand.seed` or
     `gridcell.seed` — per-instance. `Gridcell.seed` (`guess.h:5406`) +
     `Stand.seed` (`guess.h:4931`) are documented as designed for
     "comparing results when changing the order in which the simulation
     proceeds." Cross-validation should target **bit-exact** for both
     deterministic AND stochastic outputs (better than the ≤1% RMSD
     I had budgeted defensively).
  2. **`framework.cpp:411-516` per-gridcell-outer loop has 4 embedded
     concerns** to preserve in year_outer: (a) per-gridcell setup
     (`date.init(1)`, `getgridcell()`, `landcover_init()`, `initdrivers()`
     at lines 425-452); (b) restart load (`deserialize_gridcell()` at
     454-459); (c) per-day inner loop (`simulate_day` + `outdaily` +
     year-end `outannual` + save-year `serialize_gridcell` + `date.next()`
     at 465-522); (d) per-gridcell teardown (`balance.check_period()` at
     528+). Year_outer needs to service all 4 concerns per cell within
     the year-outer loop structure.
  3. **CRITICAL design challenge — `date` is GLOBAL state**, and
     `getclimate(gridcell)` is a STATEFUL per-day driver tied to it
     (per `imogen_input.cpp:752-810` audit; the same pattern in
     `imogencfx.cpp`, `cfxinput.cpp`, etc.). `getclimate()` reads
     `date.get_calendar_year()` + `date.day`, advances internal state
     machinery (`spinup_year_idx`, `stored_years[]`, file-position
     cursors) keyed off the GLOBAL date. Gridcell_outer mode resets
     `date` per-cell via `date.init(1)` at line 425. **For year_outer
     this presents 3 design options**:
     - **D1**: Pre-load climate per-cell up-front via NEW method
       `preload_all_climate(gridcell, first_yr, last_yr)`; year_outer
       inner loop reads from in-memory cache without calling `getclimate()`.
       Cleanest separation; doesn't touch gridcell_outer hot path. Memory
       overhead bounded (one cell's climate × all years ≈ few MB per cell
       briefly; can stream out after year_outer iteration). **CURRENTLY
       PREFERRED PER 2026-05-09 PRELIMINARY ANALYSIS**.
     - **D2**: Make `date` a member of `Gridcell` (vs global). Year_outer
       resets/advances per-cell-per-call; gridcell_outer code unchanged.
       Largest refactor (date is heavily globally-referenced); risk of
       incidental changes.
     - **D3**: Save/restore global `date` per-call within year_outer
       block. Smallest refactor; localized. Risk of subtle state-save
       timing pitfalls.
  4. **Revised C1 effort estimate**: 1.5-2 weeks (was: 1 week). The
     `getclimate`-refactor + design-D1-implementation work is more
     substantial than the additive-block sketch in the 2026-05-09 morning
     plan suggested. Cross-validation phase is unchanged (~few days);
     code-implementation phase is what expanded.
  5. **Recommendation for C1 fresh-chat resumption**: read this F-12
     entry's "C1 pre-flight findings" subsection (this list) FIRST as
     the canonical pre-flight context; then `_chat_artifacts/CHAT_HANDOFF
     _2026-05-08_session2.md` Part 9 (which captures the same findings
     with more detail + design rationale). Then design the D1 (or D2/D3)
     implementation in the fresh chat with full context budget for the
     code work.
- **C1 foundation landing + additional finding (2026-05-10 morning session)** —
  the C1 FOUNDATION landed in an un-tagged commit `2e918c0` on top of `09b40f0`:
  `framework_loop_mode` ins parameter (default `"gridcell_outer"` byte-
  exact LTS-equivalent) + `InputModule::preload_all_climate` +
  `getclimate_for_year` base-class virtuals (default-fail; backward-compat
  across all 9 input modules) + `framework.cpp` year_outer additive code
  path (~218 LOC; existing per-gridcell-outer block at lines 411-534
  byte-untouched via early-return pattern). 162 unit tests pass;
  default-mode regression preserved. **D1 design choice CONFIRMED** per
  the deeper investigation. **NEW FINDING from this session beyond the
  2026-05-09 evening pre-flight: `IMOGENCFXInput::spinup_year_idx`
  (line 220 of `imogencfx.h`) is a class-member counter that PERSISTS
  ACROSS CELLS in the existing gridcell_outer mode** — each cell sees a
  different starting value of `spinup_year_idx`, causing different spinup
  `imogen_year` selections per cell. This is existing behaviour that must
  be preserved EXACTLY per the byte-identical-default constraint, and
  year_outer mode's IMOGENCFXInput override (next session) must reproduce
  it via the deterministic formula
  `spinup_year_idx_at_cell_idx_year_idx = (cell_idx * nyear_spinup +
  year_idx + 1) % NYEAR_SPINUP`. Cross-validation strategy adapts:
  single-cell smoke first (bypasses cell-ordering complexity); multi-cell
  smoke second (tests formula reproduction). Captured in detail in
  `notes/STEP_17a.md` §5.4 + `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md`
  Part 10. Remaining within step 17a: IMOGENCFXInput overrides
  (~3-5 days) + cross-validation (~1-2 days) + tag
  `v0.17.0-step17a-c1-year-outer-single-process`.
- **C1.1 IMOGENINPUT IMPLEMENTATION + ERRATUM (2026-05-10 later session)** —
  the C1.1 IMOGENINPUT IMPLEMENTATION landed in an un-tagged commit on
  top of foundation commit `2e918c0`. **Strategic decision**: ImogenInput
  chosen over IMOGENCFXInput for C1.1 because ImogenInput has NO
  `RUN_IMOGEN_ENGINE()` call in `init()` (verified via grep — only
  `imogencfx.cpp:524` has it). Loose-mode runs (`-input imogen` +
  `coupling_mode "loose"`) complete `init()` cleanly + reach the LPJG
  main loop without F-10 deadlock — no engine-bypass workaround needed
  for cross-validation. The two input modules' `getclimate()` patterns
  are ~95% identical; the implementation strategy + spinup_year_idx
  formula transfers ~95% to IMOGENCFXInput later (planned as C1.3
  follow-up sub-step within step 17a). See `notes/STEP_17a.md` §5.5.
  C1.1 implementation: `ImogenInput::preload_all_climate(gridcell,
  first_yr, last_yr)` + `ImogenInput::getclimate_for_year(gridcell,
  year, day)` overrides. 2 files modified (`imogen_input.h` +~80 LOC,
  `imogen_input.cpp` +~200 LOC). 162 unit tests pass; backward compat
  with existing `getclimate()` preserved.
  **CRITICAL ERRATUM applied this commit**: the foundation commit's
  docs (foundation CHANGELOG entry, this F-12 entry's preceding bullet,
  STEP_17a.md §5.4, BACKPORT_LEDGER step-17a-foundation entry,
  session-2 chat handoff Part 10) all stated the spinup_year_idx
  reproduction formula as `(cell_idx * nyear_spinup + year_idx + 1) %
  NYEAR_SPINUP` (with `+1`). The CORRECT formula has NO `+1`:
  `spinup_year_idx_at_(cell_idx, year_idx) = (cell_idx * nyear_spinup
  + year_idx) % NYEAR_SPINUP`. Derivation (verified by tracing the
  EXACT code at `imogen_input.cpp:781-805` + `imogencfx.cpp:1071-1095`
  during C1.1 implementation): the existing `getclimate()` reads
  spinup_year_idx VALUE BEFORE incrementing it on day 0, so for cell C
  spinup year Y, the value READ equals the count of prior day-0
  increments `(C * nyear_spinup + Y)` modulo `NYEAR_SPINUP`. The C1.1
  implementation uses the CORRECTED formula; subsequent doc updates
  (STEP_17a.md §5.4 erratum, the CHANGELOG entry, this F-12 entry,
  BACKPORT_LEDGER step-17a-c1.1 entry, session-2 handoff Part 11) all
  reflect the CORRECTED formula. Remaining within step 17a:
  - C1.2 cross-validation (~1-2 days runtime; bit-exact Run A vs Run B
    on smoke gridlist; pre-stage climate via launcher per session-1
    §49.1 operational pattern; custom .ins; bash harness; iterate on
    divergences). The GO/NO-GO gate for C1.
  - C1.3 IMOGENCFXInput year_outer override (~2-3 days; replicates
    C1.1 pattern + handles relhum/wind/tmin/tmax fields + optional
    engine-bypass parameter for testing). Cross-validate identically.
  Then tag `v0.17.0-step17a-c1-year-outer-single-process`.
- **C1.2 1-CELL CROSS-VALIDATION PASS landed (2026-05-10 evening; commit
  `8bddc27`)** — first runtime end-to-end PASS of the year_outer code
  path. Bit-exact 37/37 .out files between Run A (`gridcell_outer`) and
  Run B (`year_outer`) on `gridlist_test1.txt` (1-cell IMOGEN-native cell
  at -78.75/82.50; nyear_spinup=1 + lasthistyear=1871). The corrected
  spinup_year_idx state-machine reproduction formula `(cell_idx *
  nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) verified for
  cell_idx=0/year_idx=0. Setup files added: NEW `gridlist_test1.txt`,
  NEW `runs/SSP1-2.6/main_xval_loose.ins`, NEW
  `scripts/cross_validate_year_outer.sh`. 1 LOC code change to
  `imogen_input.cpp` (declare_parameter for framework_loop_mode in
  ImogenInput's constructor; mirrors IMOGENCFXInput pattern). Per
  user's evening guidance: searchradius (climate; ImogenInput class
  member) + searchradius_soil (SoilInput; declare_parameter) resolved
  IMOGEN-grid-vs-soilmap mismatch. Operational discoveries: engine
  output is alternating-year (only ODD years 1871, 1873, ..., 1901
  have full climate; EVEN years have only `done` marker due to engine
  writer gate quirk; resolved at C1.3 sub-step 7.3.1 via engine writer
  fix per below). REGRID=1 alternative documented for production.
  Per session-2 chat handoff Part 12 + STEP_17a.md §6 + §7.2.
- **C1.3 SUB-STEP 7.3.1 4-CELL CROSS-VALIDATION PASS + IMOGEN ENGINE
  WRITER FIX landed (2026-05-10 late evening; this commit, un-tagged
  on top of `8bddc27`)** — multi-cell xval bit-exact PASS. Run A vs
  Run B 37/37 bit-exact for `gridlist_test2.txt` (4 cells: NW Canada,
  N Greenland, central Asia, Patagonia) × `nyear_spinup=2` ×
  `lasthistyear=1879` (44 cell-year iterations per run; spans 9
  distinct imogen_year values 1871..1879). The spinup_year_idx
  state-machine reproduction formula `(cell_idx * nyear_spinup +
  year_idx) % NYEAR_SPINUP` is now empirically validated across BOTH
  cell_idx>0 AND year_idx>0 branches. **PRE-REQUISITE: engine writer
  fix bundled in this commit** — `lpjguess/modules/climatemodel.cpp`
  5 conditional removals (~76 LOC incl. doc blocks) at lines ~787,
  ~884, ~963, ~988, ~998. Fixes the alternating-year staged-climate
  structural quirk: each engine call previously wrote climate ONLY
  for IYEAR == YEAR1 (combined with `updateImogenControlData()`
  advancing YEAR1++ per IYEAR iteration → only ODD years 1871, 1873,
  ..., 1901 had full climate; EVEN years had only `done` markers).
  With fix: ALL 32 staged years (1871-1902) have full 13-file climate.
  C1.2 PASS preserved (1-cell xval re-verified PASS post-fix). 162
  unit tests still pass. Same bug exists in standalone Fortran engine
  (`imogen/code/imogen_lpjg.f` lines 954, 1013, 1071, 1088, 1099);
  DEFERRED for symmetric fix as F-N-equivalent follow-up (Fortran
  engine is not on the prescribed-mode launcher path; only used for
  engine-only smoke testing per session-1 §46). Backport-relevant per
  BACKPORT_LEDGER §1.3 (climatemodel.cpp is in the C++ scope; new
  step-17a-c1.3 entry added). Also: latent OOB write surfaced in
  existing `getclimate()` cache (`stored_years[store_index] =
  imogen_year` when `store_index >= nyears` due to undersized cache
  formula `nyears = (lasthistyear - FIRST_SPINUP_YEAR) + 1`); resolved
  by bumping `lasthistyear` in `main_xval_loose.ins` (1871 → 1879;
  cache nyears=9 sufficient for 9 distinct imogen_years). The OOB write
  is a pre-existing latent bug in the existing `getclimate()` machinery
  — surfaced by this test config; not introduced by this commit; could
  be hardened in a future commit if production runs hit it. Iteration
  history (3 attempts; full forensics in CHANGELOG entry +
  `notes/STEP_17a.md` §6.3 + session-2 handoff Part 13). **Remaining
  within step 17a: sub-step 7.3.2 IMOGENCFXInput year_outer override
  (~1.5-2 days; per STEP_17a.md §7.3.2 + the 3-option engine-bypass
  recommendation — option (a) NEW `skip_inprocess_engine_run` parameter
  recommended) + cross-validate single-cell first; multi-cell second +
  tag `v0.17.0-step17a-c1-year-outer-single-process` + close-out.**
- **C1.3 SUB-STEP 7.3.2 IMOGENCFXInput YEAR_OUTER OVERRIDE + C1 FULL
  CLOSE-OUT landed (2026-05-10 very late evening; this commit; **TAGGED
  `v0.17.0-step17a-c1-year-outer-single-process`** on top of `7be595a`)**
  — F-12 sub-milestone C1 is now FULLY DONE. Lands THREE bundled
  deliverables:
  (A) NEW `skip_inprocess_engine_run` ins parameter (option a per
      STEP_17a.md §7.3.2; default `false` preserves LTS-equivalent
      behaviour). When set true, gates `RUN_IMOGEN_ENGINE()` call in
      `IMOGENCFXInput::init()` (which would otherwise deadlock per F-10).
      Files: `parameters.h` (~22 LOC) + `parameters.cpp` (~14 LOC) +
      `imogencfx.cpp` (~28 LOC for declare_parameter + gate).
  (B) IMOGENCFXInput year_outer overrides (preload_all_climate +
      getclimate_for_year). Replicates C1.1 ImogenInput pattern with
      IMOGENCFXInput-specific differences: handles additional climate
      fields (relhum, wind, tmin, tmax per step 9.5 wiring); BLAZE
      compatibility check on day 0 (mirror of imogencfx.cpp:884-893);
      preserves CFXInput-equivalent infrastructure unchanged (per user's
      2026-05-10 clarification: "imogencfx is meant to work like the cfx
      input module, with only caveat being instead of NetCDF climate
      forcing it takes in IMOGEN climate; everything else — NetCDF
      population density for SIMFIRE, SIMFIRE-BLAZE binary, atmospheric
      CO2 concentrations, NetCDF nitrogen deposition wet/dry NHx/NOy
      etc. — remains as with the cfx module"). Uses CORRECTED formula
      `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`).
      Files: `imogencfx.h` (+~95 LOC additive) + `imogencfx.cpp`
      (+~250 LOC additive).
  (C) K→C latent-bug fix in `IMOGENCFXInput::get_climate_for_gridcell`.
      Discovered empirically during sub-step 7.3.2 cross-validation:
      with skip_inprocess_engine_run=1 bypassing F-10, LPJG main loop
      runs in -input imogencfx mode for the FIRST TIME (no prior
      production run had exercised this path because F-10 always blocked
      init()). Run A immediately failed at `Soil::soil_temp_multilayer`
      with `T[i]: 169.393` (=-103.76°C, physically impossible). Root
      cause: IMOGEN engine writes T_anom/Tmin_anom/Tmax_anom in Kelvin;
      LPJG expects climate.temp/.tmin/.tmax in Celsius. Existing
      IMOGENCFXInput::getclimate had a LATENT K-vs-C bug for these 3
      temperature fields — never surfaced because LPJG main loop never
      ran in -input imogencfx mode pre-F-12-fix. ImogenInput's getclimate
      at imogen_input.cpp:876 correctly does `-273.15`; IMOGENCFXInput
      didn't. Fix: subtract 273.15 at the monthly-array population step
      in `get_climate_for_gridcell` (~25 LOC of doc blocks + 6 code-line
      changes). Single change point benefits BOTH gridcell_outer (existing
      getclimate) AND year_outer (new getclimate_for_year) modes since
      both invoke get_climate_for_gridcell. Aligns IMOGENCFXInput's
      dtemp semantics with CFXInput's pattern (dtemp in Celsius natively;
      CFXInput's NetCDF ISIMIP3b is in Celsius). Backport-relevant.
  
  Cross-validation harness extended: `scripts/cross_validate_year_outer.sh`
  takes optional 2nd arg for input-module selector (`imogen` (default;
  preserves prior behaviour) | `imogencfx` (NEW)). Run-output dirs gain
  `_imogencfx_` infix to avoid conflict with imogen runs. Banner
  updated. NEW `runs/SSP1-2.6/main_xval_imogencfx.ins` (~140 LOC; mirrors
  main_xval_loose.ins with `coupling_mode "prescribed"` and
  `skip_inprocess_engine_run 1`).
  
  Cross-validation results (this commit):
    - imogen 1cell:   ✅ 37/37 bit-exact
    - imogen 4cell:   ✅ 37/37 bit-exact
    - imogencfx 1cell: ✅ 37/37 bit-exact (NEW)
    - imogencfx 4cell: ✅ 37/37 bit-exact (NEW)
  
  **GO/NO-GO gate per session-2 §9.5: PASSED for ALL FOUR scenarios.**
  The spinup_year_idx state-machine reproduction formula
  `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is
  empirically validated for BOTH input modules across BOTH single-cell
  + multi-cell + single-spinup-year + multi-spinup-year scenarios. 162
  unit tests still pass.
  
  **C1 IS CLOSED. NEXT: C2 (workstation MPI year_outer; ~3-5 days; tag
  target `v0.17.5-step17b-c2-mpi-sync`; per EXECUTION_PLAN.md V.1 row
  17b).** Per the staged plan, after C2 → C3 (cluster MPI year_outer;
  ~1-2 weeks SSH iterative; tag target `v0.18.0-step17c-c3-cluster-tight`;
  per row 17c) → step 17d end-to-end validation across all 4
  combinations → step 18 docs → step 19 CI/release → v1.0.0.
- **What was decided today (2026-05-09; user confirmation)**:
  1. Skip Option B; go straight to staged Option C (C1 → C2 → C3)
  2. `intermediary_py` cluster integration: keep existing copy-over
     workflow (Choice 1) for v1.0; embed-into-launcher deferred to v1.1+
  3. Filename-naming refinement noted: existing copy-over uses
     `lpjg_<output>_<scenario>.gz` (redundant with directory hierarchy);
     could simplify to native LPJG names (`cflux.out.gz`, etc.) since
     dir structure encodes scenario. Defer to v1.1+ refinement.
  4. Both local AND cluster matter equally for v1.0; staged C1-C2-C3
     plan delivers both.
- **Cross-references**:
  - `notes/STEP_9.md` (the empirical findings that motivated F-12)
  - `notes/STEP_16.md` §2 (the architectural-tension investigation that
    re-shaped F-12 into v1.0 scope)
  - `notes/FOLLOWUPS.md` F-10 (the architectural diagnosis F-12 resolves)
  - `runs/SSP1-2.6/README.md` "Empirical findings" section
  - `docs/v2_roadmap.md` §4-§5 (concrete sprint plans for Options B + C)
  - `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Parts 5-7
    (fresh-chat onboarding playbook)
  - `[CMI §3.7.6]` (the diagnostic-test recommendation that should be
    implemented after F-12 lands)

### F-8 — Revisit CMIP6 wind-magnitude split + precip rain/snow partition at step 9.5

- **Trigger**: step 5 CAVEAT-B and CAVEAT-C. The CMIP6 NetCDF doesn't
  store separate U/V wind components or rain/snow split; we currently
  approximate via `U=V=wind_patt/√2` (preserves magnitude, loses
  direction) and `rain=precip, snow=0` (preserves total).
- **Action**: at step 9.5 (climate-output enhancements), if the
  approximations cause measurable downstream biases (e.g. in BLAZE
  fire model wind sensitivity, or LPJ-GUESS snow accumulation), implement
  finer splits — e.g. distribute wind direction climatologically; split
  precip by climate-zone rain/snow fraction.
- **Timing**: step 9.5 of the formal V.1 plan; only if biases manifest.

---

## DONE

### F-4 — Bug C2/C3 source fix (polling-loop `DONE_EXIST` default) — closed 2026-05-06

- **Trigger**: step 4 (`notes/STEP_4.md` §6 + `notes/FOLLOWUPS.md`
  original entry). Every standalone Fortran IMOGEN smoke run since
  step 4 needed a manual `touch LPJG_main/IMOGEN/done` because the
  polling loop's exit condition required `DONE_EXIST=.TRUE.` and the
  pre-loop default `!DONE_EXIST=.TRUE.` (line 363) was commented out.
  The C++ twin in `climatemodel.cpp:332-353` was similarly broken
  (4 lines commented out: `doneExist` INQUIRE + 3 `*Open` guards;
  a hard-coded `doneExist = true` short-circuited the safety check).
- **Resolution at step 7**:
  - **C++ side** (`lpjguess/modules/climatemodel.cpp`): restored the
    `doneExist = filesystem_dkb::exists(...)` INQUIRE + added a
    first-call bypass via the existing `firstCall` local
    (initialized from `IMOGENConfig::FIRSTCALL`); restored the 3
    `runnowOpen`, `runfluxOpen`, `runnonco2fluxOpen` guards. This
    re-engages the proper LPJG↔IMOGEN handshake safety semantics
    while still allowing first-call bootstrap.
  - **Fortran side** (`imogen/code/imogen_lpjg.f`): added a
    `CALL SYSTEM('mkdir -p ... /LPJG_main/IMOGEN')` +
    `CALL SYSTEM('touch ... /LPJG_main/IMOGEN/done')` block before
    the outer `DO WHILE (KEEPRUNNING)` loop. The auto-created file
    is then picked up by the polling loop's INQUIRE on the very
    first iteration. Idempotent (touch + mkdir -p both succeed
    whether the target exists or not).
- **Verification**: standalone IMOGEN smoke run now works
  end-to-end (years 1871, 1872 produced) **without** any pre-staged
  `done` file. Confirmed by removing all runtime state via
  `rm -rf LPJG_main IMOGEN`, re-staging only the control-file
  stubs (no `done` file), running `./imogen_lpjg`, and observing
  `DONE_EXIST = T` on the very first polling iteration.
- **Side benefit**: LPJ-GUESS's 162 unit tests still pass cleanly
  (no regression from the C2/C3/C4 fixes).
- **Documented in**: `notes/STEP_7.md` §3.1 (C2/C3), §3.3 (F-4).

### F-5 — Stage emission scenarios into a 5th tarball — closed 2026-05-06

- **Trigger**: `imogen/emiss/README.md` (step 4) flagged that step 6
  should roll the historical + scenario emission ASCII files into a
  5th tarball under the existing manifest+fetch architecture.
- **Resolution**: At step 6, the full `Data/Imogen/emiss/` tree
  (CMIP5/, CMIP6/, DKB_dataset_totals/, new_emission_data/,
  rcp_database/, plus 6 loose top-level files; ~5.2 MB raw) was
  rsynced into `imogen/emiss/`, tarballed as
  `imogen-emiss-reference-v1.0.tar.gz` (311 KB compressed; 17×
  compression on ASCII), SHA256-checksummed, and registered in
  `tools/imogen_data_manifest.txt` as the `emiss-reference`
  component. The fetch script needed zero code changes — just one
  new manifest row.
- **Side effect**: `imogen/emiss/` was restructured from the step-4
  flat-3-files stop-gap to the full predecessor framework tree, and
  `imogen/code/imogen_settings.txt`'s `FILE_*_EMITS` paths updated
  accordingly (3-line edit to add the `DKB_dataset_totals/` subdir
  prefix).
- **Verification**: `tools/fetch_imogen_data.sh --verify-only` reports
  all 6 components clean; standalone IMOGEN regression smoke run
  produces years 1871, 1872 unchanged from step-4 output.
- **Documented in**: `notes/STEP_6.md` §3, §4, §6.
