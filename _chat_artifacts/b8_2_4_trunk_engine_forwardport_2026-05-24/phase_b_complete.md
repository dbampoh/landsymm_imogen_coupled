# Phase B complete — Foundation source-edits + build verification

**Date**: 2026-05-26 ~12:15 PM CEST (session 11 day 2)
**Status**: ✅ COMPLETE

## Source-edits applied

| File | Operation | Description |
|---|---|---|
| `forks/trunk_r13078/framework/parameters.h` | modify | DELETE Installment-1's `skip_inprocess_engine_run` block (lines ~488-501); ADD `coupling_mode` declaration + RELOCATED `skip_inprocess_engine_run` at canonical step-17a position; ADD `imogen_nee_perturbation_factor` removed-comment block; ADD block 8.2.4 deferral note for `framework_loop_mode` |
| `forks/trunk_r13078/framework/parameters.cpp` | modify | DELETE Installment-1's `skip_inprocess_engine_run = false;` definition; ADD `xtring coupling_mode = "tight";` + RELOCATED `bool skip_inprocess_engine_run = false;` at canonical position; ADD documentary comments + block 8.2.4 deferral note |
| `forks/trunk_r13078/modules/imogenoutput.h` (NEW) | cp | wholesale cp from `lpjguess/modules/imogenoutput.h` (10849 bytes; md5 `9bdcb726fae8a8e90c2254fef1b8590a`) |
| `forks/trunk_r13078/modules/imogenoutput.cpp` (NEW) | cp | wholesale cp from `lpjguess/modules/imogenoutput.cpp` (28361 bytes; md5 `bf8b49019a9a475595c39777f4545551`) |
| `forks/trunk_r13078/modules/CMakeLists.txt` | modify | ADD `imogenoutput.h` to headers set; ADD `imogenoutput.cpp` to source set (2 LOC total) |

## Build verification gate

**Command**: `make -C forks/trunk_r13078/build_b824 -j$(nproc)`
**Walltime**: ~35 sec
**Result**: ✅ PASS

| Gate | Verdict | Evidence |
|---|---|---|
| G0 — cmake configures clean | ✅ PASS | `phase_b_cmake.log` shows "Configuring done", "Generating done", "Build files have been written to: .../build_b824" |
| G1 — make completes without errors | ✅ PASS | `grep -c "error:" phase_b_make.log` = 0; only pre-existing gutil.h sprintf-overflow warnings (332 warning lines; same as baseline trunk build) |
| G2 — imogenoutput.cpp compiled into BOTH targets | ✅ PASS | `phase_b_make.log` shows `[ 72%] Building CXX object CMakeFiles/guess.dir/modules/imogenoutput.cpp.o` + `[ 84%] Building CXX object CMakeFiles/runtests.dir/modules/imogenoutput.cpp.o` |
| G3 — guess binary linked successfully | ✅ PASS | `[ 99%] Linking CXX executable guess` + `[ 99%] Built target guess` |
| G4 — runtests binary linked successfully | ✅ PASS | `[100%] Linking CXX executable runtests` + `[100%] Built target runtests` |
| G5 — binary smoke-runs cleanly | ✅ PASS | `forks/trunk_r13078/build_b824/guess` (no args) emits standard `Usage: ... guess [-parallel] [-input ...]` banner |

## Build artifacts

- `forks/trunk_r13078/build_b824/guess`: 2,939,688 bytes; sha1 `140ccf7556749a66cb2ee05bdb3d299afd04c91b` (May 26 12:15)
- Compared to block 8.1 cluster build (block-8.1 sha1 `40d36db6...`; 2,594,392 bytes): **+345,296 bytes**; consistent with addition of ImogenOutput class (~821 LOC NEW + step-8 infrastructure) + relocated parameter declarations
- Compared to block 8.0.3 baseline (Installment-1 era; pre-block-8.2.4): same +imogenoutput growth

## Next phase

**Phase C — Engine surgery: climatemodel.cpp + imogencfx.{cpp,h}** per
`B8_2_4_forward_port_plan.md` §1.2 (~1.5-2 d).
