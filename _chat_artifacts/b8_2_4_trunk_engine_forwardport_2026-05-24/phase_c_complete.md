# Phase C complete — Engine surgery: climatemodel.cpp + imogencfx.cpp

**Date**: 2026-05-26 ~12:23 PM CEST (session 11 day 2)
**Status**: ✅ COMPLETE

## Source-edits applied

### Phase C.1 — climatemodel.cpp wholesale forward-port

| File | Operation | Description |
|---|---|---|
| `forks/trunk_r13078/modules/climatemodel.cpp` | wholesale cp from lpjguess | Pre-cp md5 trunk `fcc7110a9246d057f540cdcc96f1b803`; Post-cp md5 `8dcced2834fa083a41ca84fd29bb4206` (byte-identical with lpjguess). 22 hunks of changes folded in via cp: step-7 polling guards (C2/C3/C4 fixes) + step-8 imogenoutput integration + step-9.5 8-field Tmin/Tmax/Rh/W writers + step-17a engine writer fix + B19/B37/B39/B44/B45 deltas. Zero year_outer entanglement so wholesale cp is safe. |

### Phase C.2 — imogencfx.h NO-OP

**Decision**: KEEP trunk's `imogencfx.h` AS-IS (preserved Installment-1 + B49 FIRST_SPINUP_YEAR=1900). All declarations needed for the non-year_outer slice of imogencfx.cpp (dtmin/dtmax arrays, file_tmin/file_tmax xtrings, etc.) are already in trunk's header. Cosmetic comment-text differences vs lpjguess's step-9.5-style framing are zero-functional-impact; not needed for engine byte-identity. Per Rule #11 no work without benefit.

### Phase C.3 — imogencfx.cpp surgical forward-port (head+tail composition)

| File | Operation | Description |
|---|---|---|
| `forks/trunk_r13078/modules/imogencfx.cpp` | reconstructed via head+tail | head -n 1307 lpjguess.cpp (everything up to + including `return true;` + closing `}` of getclimate at line 1306-1307) + deferral marker block (24 LOC documenting the deferred year_outer scaffolding scope + cross-references) + tail -n +1747 lpjguess.cpp (getsoil onward; 1747-end). Resulting trunk imogencfx.cpp = 1360 lines (vs lpjguess 1774; -414 from year_outer block excision + small delta from deferral marker added). |
| `forks/trunk_r13078/modules/imogencfx.cpp` | StrReplace | After head+tail composition, line 353 was found to have `declare_parameter("framework_loop_mode", &IMOGENConfig::framework_loop_mode, ...)` which references a symbol DEFERRED in parameters.{h,cpp} at Phase B (NEW Rule #9 datapoint surfaced by harness/verification). Removed via StrReplace; replaced with a block 8.2.4 deferral note. |

## Build verification gate (Phase C)

**Command**: `make -C forks/trunk_r13078/build_b824 -j$(nproc)`
**Walltime**: ~8 sec (incremental; only climatemodel.cpp + imogencfx.cpp recompiled + re-link)
**Result**: ✅ PASS

| Gate | Verdict | Evidence |
|---|---|---|
| G0 — climatemodel.cpp.o compiles | ✅ PASS | `phase_c_make.log` shows `[  2%] Building CXX object CMakeFiles/guess.dir/modules/climatemodel.cpp.o` + `[  3%] Building CXX object CMakeFiles/runtests.dir/modules/climatemodel.cpp.o` |
| G1 — imogencfx.cpp.o compiles | ✅ PASS | Same log: `[  2%] Building CXX object CMakeFiles/guess.dir/modules/imogencfx.cpp.o` + `[  4%] Building CXX object CMakeFiles/runtests.dir/modules/imogencfx.cpp.o` |
| G2 — guess binary links | ✅ PASS | `[  5%] Linking CXX executable guess` + `[ 49%] Built target guess` |
| G3 — runtests binary links | ✅ PASS | `[  6%] Linking CXX executable runtests` + `[100%] Built target runtests` |
| G4 — zero errors / undefined references / relocation issues | ✅ PASS | `grep -c "error:" + "undefined reference" + "relocation" = 0` |
| G5 — binary smoke runs cleanly | ✅ PASS | `forks/trunk_r13078/build_b824/guess` (no args) emits standard Usage banner |
| G6 — no live `framework_loop_mode` references in source | ✅ PASS | `grep -E "framework_loop_mode" forks/trunk_r13078/modules/imogencfx.cpp` returns only `//` comment lines (343, 347, 1316, 1326); zero `IMOGENConfig::framework_loop_mode` symbol references in live code |

## Build artifacts

- `forks/trunk_r13078/build_b824/guess`: 2,943,808 bytes (May 26 12:23)
- sha1: `9ef4c4cfcef0d10d51a12c2e261147000cee7d6c`
- Δ vs Phase B (2,939,688 bytes; sha1 `140ccf75...`): +4120 bytes growth from climatemodel.cpp + imogencfx.cpp engine logic additions

## Phase boundary summary post-Phase-C

| File | State |
|---|---|
| `forks/trunk_r13078/framework/parameters.h` | Modified at Phase B; +coupling_mode, relocated skip_inprocess_engine_run, framework_loop_mode DEFERRED |
| `forks/trunk_r13078/framework/parameters.cpp` | Modified at Phase B; matching .cpp deltas |
| `forks/trunk_r13078/modules/imogenoutput.h` (NEW) | Created at Phase B; byte-identical with lpjguess (md5 `9bdcb726...`) |
| `forks/trunk_r13078/modules/imogenoutput.cpp` (NEW) | Created at Phase B; byte-identical with lpjguess (md5 `bf8b4901...`) |
| `forks/trunk_r13078/modules/CMakeLists.txt` | Modified at Phase B; +2 LOC for imogenoutput.{h,cpp} |
| `forks/trunk_r13078/modules/climatemodel.cpp` | **Replaced wholesale at Phase C.1; byte-identical with lpjguess (md5 `8dcced28...`)** |
| `forks/trunk_r13078/modules/imogencfx.cpp` | **Surgically reconstructed at Phase C.3; year_outer scaffolding excised; framework_loop_mode declare_parameter excised; 1360 LOC vs lpjguess 1774 (-414)** |
| `forks/trunk_r13078/modules/imogencfx.h` | Unchanged (Phase C.2 NO-OP); KEEPS Installment-1 + B49 FIRST_SPINUP_YEAR=1900 |
| `forks/trunk_r13078/modules/climatemodel.h` | Unchanged (byte-identical between forks since baseline; md5 `d598d94...`) |

## Next phase

**Phase D — SSP1-2.6 canary engine run** per `B8_2_4_forward_port_plan.md` §1.3 (~0.5 d wall).
