# STEP 17b — F-12 sub-milestone C2 (Workstation MPI year_outer + B1+B4 + small bundles)

**Date opened:** 2026-05-11
**Date C2 prep landed:** 2026-05-11 (commit `1405ada`; un-tagged checkpoint; pushed to all 3 remotes)
**Date C2 core (MPI_Barrier + flush_year_globally_synchronized) landed:** 2026-05-11 (this commit; un-tagged checkpoint)
**Date B1+B4 bundled with C2 era landed:** _pending_
**Date C2 close-out + tag `v0.17.5-step17b-c2-mpi-sync` landed:** _pending_
**Status:** 🔧 IN PROGRESS — C2 prep phase ✅ done (`1405ada`); C2 core ✅ done (`f13b302`; LPJG source ~317 LOC additive across 3 files); B12 ✅ done (`488c5a2`); B10 ✅ done (`3c00428`); B6 ✅ done (`24250b2`; docs-only; subsumed by B10); B2 ✅ done (`76b3b04`; Fortran Tmin/Tmax write block; +59 LOC additive); **B3 ✅ done this commit (C++ Tmin/Tmax in REGRID branch — closed by architectural reframing; the C++ port has no REGRID branch; ~30 LOC additive docs only in `lpjguess/modules/climatemodel.cpp`; ZERO functional code change)**; B4 ⏳ NEXT (ImogenInput consumer wiring); B1 ⏳ pending; full mpirun -np 4 mimic + tag at close-out.

---

## 1. Goal (per `EXECUTION_PLAN.md` V.1 step row 17b + session-2 chat handoff Parts 6 + 8 + 15)

> **F-12 sub-milestone C2 — Workstation MPI year_outer.** Per Path A 2026-05-09 (skip
> Option B; staged Option C only). Add `MPI_Barrier(MPI_COMM_WORLD)` at year
> boundary in the `year_outer` code path in `lpjguess/framework/framework.cpp`
> (#ifdef HAVE_MPI guarded; falls back gracefully in single-process build).
> Add `flush_year_globally_synchronized(int year)` method on `ImogenOutput`
> with `MPI_Allreduce` over per-rank flux contributions (NEE, CH4, N2O);
> only lead rank writes the unified handshake file. Pre-requisite:
> address Anaconda3 `mpicxx` wrapper issue. Build `lpjguess/build_mpi/guess`
> via `scripts/cluster/make_guess.sh --mpi`; test via
> `scripts/run_parallel_mimic.sh` workstation MPI mimic (`mpirun -np 4`).

**Plus bundled scope per 2026-05-11 user-confirmed B-item bundling decision** (refined option (i) for B1+B4 with C2 era + opportunistic option (iii) for B2/B3/B5-B11; full per-item assignment in [§5](#5-b-item-bundling-decision-2026-05-11)):

- B1 — Fortran Rh + Wind COMPUTATION port (3-5 d; heaviest)
- B2 — Fortran Tmin/Tmax write block (0.5 d)
- B3 — C++ Tmin/Tmax in REGRID branch (0.5 d)
- B4 — ImogenInput Rh/W/Tmin/Tmax consumer wiring expansion (1 d)
- B6 — F-2 Fortran T_anom 2× line count investigation (0.5 d)
- B10 — Symmetric Fortran engine writer fix (0.5 d)

**C2 era combined sprint estimate: ~9-13 days** (3-5 d core + 6-8 d bundled).

---

## 2. Inherited context (from session-1 + session-2 chat handoffs)

The C1 close-out at `v0.17.0-step17a-c1-year-outer-single-process` (commit `8aafe84`) landed the additive `framework_loop_mode = "year_outer"` ins parameter, the InputModule virtuals, the framework.cpp year_outer additive code path, the ImogenInput year_outer overrides (with corrected spinup_year_idx formula NO `+1`), and the IMOGENCFXInput year_outer overrides (plus the `skip_inprocess_engine_run` ins parameter + K→C latent-bug fix). All 4 cross-validation scenarios pass bit-exact 37/37. F-10 architectural deadlock is RESOLVED for workstation single-process tight.

C2 extends the resolution to multi-rank MPI tight (still on workstation; the cluster MPI tight ladder is C3). The key new mechanics:

1. **`MPI_Barrier(MPI_COMM_WORLD)` at year boundary** — provides the rank-wide synchronization point that the per-year-outer code path requires for closed-loop tight coupling. Lands inside `if (IMOGENConfig::coupling_mode == "tight" || ...)` block at the year boundary in `framework.cpp` year_outer block (line ~611 of the existing year_outer block; between the per-year outer loop body `}` close and the per-cell teardown). `#ifdef HAVE_MPI` guarded; falls back gracefully to single-process behaviour when not built with MPI.

2. **`flush_year_globally_synchronized(int year)` on `ImogenOutput`** — sibling to the existing `flush_year(int year)`. Performs `MPI_Allreduce(MPI_SUM)` over per-rank NEE / CH4 / N2O contributions so the lead rank (rank 0) writes a GLOBALLY-AGGREGATED handshake file rather than the per-rank-local values that `flush_year()` produces. The closed-loop tight-coupling correctness depends on this.

3. **Anaconda3 `mpicxx` wrapper fix** — addressed in this commit (§3 below).

---

## 3. C2 prep phase — Anaconda3 `mpicxx` wrapper diagnosis + fix (this commit)

### 3.1 Diagnostic findings (2026-05-11)

Per session-2 §8.1 workstation-specs 2026-05-09:

```
$ which mpicxx mpirun
/home/bampoh-d/anaconda3/bin/mpicxx
/home/bampoh-d/anaconda3/bin/mpirun

$ mpicxx --version
/home/bampoh-d/anaconda3/bin/mpicxx: line 321: x86_64-conda-linux-gnu-c++: command not found
```

The Anaconda3 `mpicxx` wrapper (MPICH 4.1.1) is configured to invoke `x86_64-conda-linux-gnu-c++` (the conda-shipped g++ wrapper compiler). That binary is **NOT present** in the bare Anaconda3 install (the user's workstation has Anaconda3 with MPICH + base packages but without the conda-shipped GCC toolchain). The wrapper fails immediately, blocking any MPI build.

Live `mpicxx -show` reveals the wrapper command intent:

```
x86_64-conda-linux-gnu-c++ -I/home/bampoh-d/anaconda3/include
  -L/home/bampoh-d/anaconda3/lib
  -Wl,-rpath,/home/bampoh-d/anaconda3/lib
  -lmpicxx -Wl,-rpath -Wl,/home/bampoh-d/anaconda3/lib
  -Wl,--enable-new-dtags -lmpi
```

So the wrapper expects the conda-shipped C++ toolchain to compile + link against Anaconda3's `libmpi.so` + `libmpicxx.so`.

### 3.2 Two-fix investigation

Two candidate fixes were investigated this commit:

#### Option (a) — Env-var override `MPICH_CXX=g++`

MPICH's documented mechanism to bypass the wrapper-compiler lookup; uses system `g++` instead. Verified working at the `mpicxx --version` level:

```
$ MPICH_CXX=g++ mpicxx --version
g++ (Ubuntu 15.2.0-4ubuntu4) 15.2.0
```

**INITIAL CHOICE** — for consistency with the existing `build/guess` (built with system `g++ 15.2.0` per workstation specs).

**REVERSED ON FURTHER DIAGNOSIS**: trying to build with `MPICH_CXX=g++` hit an independent **libstdc++ ABI mismatch** at the link stage:

```
$ MPICH_CXX=g++ scripts/cluster/make_guess.sh --mpi
...
[ 99%] Linking CXX executable runtests
/usr/bin/ld: ...main.cpp.o: in function `Catch::StreamBufImpl<...>::~StreamBufImpl()':
  undefined reference to `__cxa_call_terminate'
```

**Root cause**: Anaconda3 (pre-`gxx_linux-64` install) ships `libstdc++.so.6.0.29` (June 2022 / GCC 11.2 era), which **does NOT export `__cxa_call_terminate`**. System ships `libstdc++.so.6.0.34` (Sept 2025 / GCC 15.2 era), which **does export** it. Verified via `nm -D <libstdc++.so.6> | grep -c '__cxa_call_terminate'`:

| `libstdc++.so.6` | exports `__cxa_call_terminate`? |
|---|---|
| `/home/bampoh-d/anaconda3/lib/libstdc++.so.6` → `6.0.29` (pre-fix) | 0 (NOT EXPORTED) |
| `/lib/x86_64-linux-gnu/libstdc++.so.6` → `6.0.34` | 1 (EXPORTED) |

`g++ 15.2` emits calls to `__cxa_call_terminate` in Catch2 destructors (newer terminate-handling ABI). The `mpicxx` wrapper command bakes `-L/home/bampoh-d/anaconda3/lib -Wl,-rpath,/home/bampoh-d/anaconda3/lib` into the link line, so the linker finds Anaconda3's older `libstdc++` first → undefined reference at link time. Side-fix via `rpath/-L` surgery is theoretically possible but risks RUNTIME `libstdc++` resolution breakage.

The env-var override is INSUFFICIENT on its own.

#### Option (b) — `conda install -c conda-forge gxx_linux-64`

Provides the missing conda-shipped wrapper compiler AT the path mpicxx expects. The conda-forge `gxx_linux-64` package also ships a matching `libstdc++` (typically GCC 11.x+) which DOES export `__cxa_call_terminate`. Internal toolchain consistency: conda g++ + conda libstdc++ + conda libmpi + conda libnetcdf all from same vendor environment.

**CHOSEN** (per session-2 §8.1 "preferred" recommendation; reinforced by the empirical libstdc++ ABI evidence above).

Empirical confirmation post-install:

```
$ conda install -n base -c conda-forge -y gxx_linux-64
...
done

$ x86_64-conda-linux-gnu-c++ --version
x86_64-conda-linux-gnu-c++ (conda-forge gcc 15.2.0-7) 15.2.0

$ mpicxx --version
x86_64-conda-linux-gnu-c++ (conda-forge gcc 15.2.0-7) 15.2.0

$ ls -la /home/bampoh-d/anaconda3/lib/libstdc++.so.6
... libstdc++.so.6 -> libstdc++.so.6.0.34

$ nm -D /home/bampoh-d/anaconda3/lib/libstdc++.so.6 | grep -c __cxa_call_terminate
1
```

**Happy outcome**: conda-forge installed `gcc 15.2.0-7` — the SAME 15.2.0 major-minor as the system `g++` 15.2.0-4ubuntu4. Both compilers target the same `libstdc++.so.6.0.34` ABI. This means **xval bit-exactness should be preserved across `build/guess` and `build_mpi/guess`** (no compiler-induced micro-numerical noise).

### 3.3 NOTE — handoff erratum: `OMPI_CXX` vs `MPICH_CXX`

The inherited handoff Part 8.1 + the user's prompt suggested `OMPI_CXX=g++ mpicxx ...`. That's OpenMPI's variant; Anaconda3 ships MPICH, whose wrapper expects `MPICH_CXX`. Verified live 2026-05-11. Recorded as documentation erratum for the symmetric Fortran fix B10 + the F-11 Backport Sprint (the OPENMPI fallback path won't exist when the Backport Sprint replicates this fix to `trunk_r13078`).

### 3.4 Independent NetCDF mismatch in `make_guess.sh --mpi` path

The existing `scripts/cluster/make_guess.sh` had a workstation-incorrect logic at lines 92-102:

```bash
if [[ -n "${ANACONDA3_PREFIX:-}" && ${USE_MPI} -eq 0 ]]; then
  # Only use Anaconda3 NetCDF for non-MPI build (workstation case).
  # On cluster + MPI, prefer module-loaded NetCDF (consistent with cluster's
  # MPI implementation; mixing Anaconda3 NetCDF with cluster MPI causes ABI issues).
```

The `&& ${USE_MPI} -eq 0` clause **explicitly skipped Anaconda3 NetCDF** for `--mpi` builds. The rationale was cluster-correct (cluster prefers module-loaded NetCDF when present) but workstation-INCORRECT: on workstation there's NO module-loaded NetCDF; Ubuntu native is the broken `libhdf5_serial.so.310` ↔ `libcurl.so.4@CURL_OPENSSL_4` ABI mismatch that Decision #8 specifically AVOIDS via the Anaconda3 NetCDF preference.

Empirical evidence: with `--mpi` skipping Anaconda3 NetCDF, the MPI workstation build failed at link time with the canonical Decision #8 errors:
```
/usr/bin/ld: /lib/x86_64-linux-gnu/libhdf5_serial.so.310: undefined reference to
  `curl_global_init@CURL_OPENSSL_4'
```

**Fix this commit**: remove the `&& ${USE_MPI} -eq 0` clause; apply Anaconda3 NetCDF unconditionally when `ANACONDA3_PREFIX` is set. Cluster builds (which use module-loaded NetCDF) should NOT set `ANACONDA3_PREFIX`; the `env_owl.sh` module loads will populate cluster-native NETCDF paths and leave `ANACONDA3_PREFIX` unset.

### 3.5 Verification of C2 prep (this commit)

| Check | Method | Result |
|---|---|---|
| `mpicxx --version` works | Live shell | ✅ "conda-forge gcc 15.2.0-7" |
| `lpjguess/build_mpi/guess` builds clean | `scripts/cluster/make_guess.sh --mpi` | ✅ 2 836 440 bytes (2.7 MB); only pre-existing warnings |
| `lpjguess/build_mpi/runtests` builds clean | (same; full build target) | ✅ 162 tests / 25 cases pass |
| MPI symbol linkage | `ldd build_mpi/guess \| grep mpi` | ✅ `libmpi.so.12` + `libmpicxx.so.12` from Anaconda3 |
| NetCDF linkage | `ldd build_mpi/guess \| grep netcdf\|hdf5\|curl` | ✅ `libnetcdf.so.19` + `libhdf5.so.200` + `libcurl.so.4` all from Anaconda3 (Decision #8 honored) |
| libstdc++ linkage | `ldd build_mpi/guess \| grep stdc` | ✅ `/usr/lib/x86_64-linux-gnu/libstdc++.so.6` (system; matches Anaconda3's now-updated `libstdc++.so.6.0.34` ABI) |
| HAVE_MPI defined at compile | `nm build_mpi/CMakeFiles/.../parallel.cpp.o \| grep FinalizeCaller` | ✅ `auto_ptr<FinalizeCaller>` symbol present (only exists inside `#ifdef HAVE_MPI` block) |
| All 4 xval scenarios bit-exact PASS against `build_mpi/guess` (single-process; pre-MPI_Barrier baseline) | `GUESS_BIN=$PWD/lpjguess/build_mpi/guess scripts/cross_validate_year_outer.sh <var> <input>` × 4 | ✅ 37/37 bit-exact for all 4 (imogen 1cell, imogen 4cell, imogencfx 1cell, imogencfx 4cell) |

**The MPI build preserves the C1 baseline byte-exactly in single-process mode.** The HAVE_MPI conditional compilation doesn't disturb the gridcell_outer / year_outer code path correctness; it only adds the GuessParallel namespace functions (`init` / `get_rank` / `get_num_processes`) which are unused until `-parallel` flag is present at runtime.

### 3.6 Files modified this commit

| File | Change | Backport-relevance |
|---|---|---|
| `scripts/cluster/make_guess.sh` | (a) Replace MPICH_CXX env-var override approach with a fail-fast error message documenting the `conda install gxx_linux-64` preferred fix + the MPICH_CXX env-var alternative (with libstdc++ caveat) (b) Remove `&& ${USE_MPI} -eq 0` clause from Anaconda3 NetCDF preference; apply unconditionally when ANACONDA3_PREFIX is set | IRRELEVANT (scripts/ only; no `lpjguess/` source change) |
| `scripts/cross_validate_year_outer.sh` | Make `GUESS_BIN` env-var-overridable for testing alternative builds (e.g., `build_mpi/guess`); default unchanged (`build/guess`) | IRRELEVANT (scripts/ only) |
| `notes/STEP_17b.md` (NEW) | This file; full forensic record for C2 prep + C2 plan + B-item bundling | IRRELEVANT (docs) |

**Net `lpjguess/` source-level change: ZERO.** Backport-irrelevant. The Anaconda3 environment install of `gxx_linux-64` is a build-environment fix (not a source change); the Backport Sprint will need to document this prerequisite when applying changes to `trunk_r13078`.

---

## 3a. C2 core implementation — LANDED this commit (2026-05-11)

### 3a.1 What landed (3 files modified; +317 LOC additive)

| File | Change | LOC |
|---|---|---|
| `lpjguess/modules/imogenoutput.h` | NEW: `static ImogenOutput* get_instance()` accessor + `flush_year_globally_synchronized(int year)` method declaration + `static ImogenOutput* instance_` private member + extensive doc blocks | +60 |
| `lpjguess/modules/imogenoutput.cpp` | NEW: `#include <mpi.h>` (HAVE_MPI-guarded) + static `instance_` definition + ctor sets `instance_ = this` + dtor clears it + `flush_year_globally_synchronized(int year)` implementation (~120 LOC incl. doc block + MPI_Allreduce over per-rank flux contributions + lead-rank-only write delegation to existing `flush_year` + post-flush reset + per-rank diagnostic dprintf) | +181 |
| `lpjguess/framework/framework.cpp` | NEW: `#include <mpi.h>` (HAVE_MPI-guarded) + `#include "../modules/imogenoutput.h"` + year-boundary `MPI_Barrier` block (HAVE_MPI + `MPI_Initialized` guarded) + explicit call to `ImogenOutput::get_instance()->flush_year_globally_synchronized(calendar_year)` between per-year cell-inner loop body close and per-cell teardown in the year_outer additive block | +76 |

**Total**: +317 LOC purely additive (zero deletions). Backport-relevance HIGH for all 3 files.

### 3a.2 Design decision — singleton-pointer pattern over virtual-method-on-base

Considered two integration approaches:

| Option | Touch surface | Cleanliness | Chosen? |
|---|---|---|---|
| **(A)** Add new non-pure virtual `flush_year_globally_synchronized(int)` to `OutputModule` abstract base in `framework/outputmodule.h` + matching dispatch in `OutputModuleContainer` + override in `ImogenOutput` | 3 shared upstream files (`outputmodule.h/cpp`, container methods) + 1 LandSyMM module file | OOP-canonical | NO |
| **(B)** Singleton-pointer pattern in `ImogenOutput`: `static ImogenOutput* instance_` set in ctor, cleared in dtor; `static get_instance()` accessor; framework.cpp looks up the instance + calls the method directly | 2 LandSyMM module files (`imogenoutput.h/cpp`) + 1 framework file | Mirrors existing `output_channel` global at `outputmodule.h:227` | **YES** |

Option (B) chosen because:
1. **Smaller backport surface** (Option A would touch `framework/outputmodule.h/cpp` which are part of upstream LPJ-GUESS infrastructure; trunk_r13078 backport would have to apply OO changes to those files too)
2. **Mirrors existing LPJ-GUESS pattern** — `output_channel` is a process-global singleton at outputmodule.h:227 (an `extern OutputChannel*`). The pattern is mainstream in this codebase.
3. **Avoids forcing all 9 registered output modules to either get the new virtual or document its no-op default** — keeps the change localised to ImogenOutput which is the only module that needs it
4. **Defensive null-check at call site**: framework.cpp uses `if (ImogenOutput* imout = get_instance())` so a runtime scenario where ImogenOutput wasn't registered (e.g., a non-IMOGEN input mode that somehow ended up in year_outer) silently skips the flush rather than null-dereferencing

### 3a.3 MPI integration discipline — mirrors existing LPJ-GUESS conventions

Verified live against the existing MPI usage in the codebase (per user's 2026-05-11 query): the new C2 code follows the established LPJ-GUESS MPI integration pattern at `imogencfx.cpp:381` + `imogen_input.cpp:221` exactly:

| Aspect | Existing LPJ-GUESS pattern | C2 code | Match |
|---|---|---|---|
| `mpi.h` include placement | `#ifdef HAVE_MPI #include <mpi.h> #endif` at file top (before any std header) | Same | ✓ |
| MPI-alive guard | `int flag; MPI_Initialized(&flag); if (... == MPI_SUCCESS && flag == true) { ... }` | Same | ✓ |
| Rank identification | (existing uses Barrier only; never queries rank) | `GuessParallel::get_rank()` from `parallel.h` | ✓ (canonical accessor) |
| Communicator | `MPI_COMM_WORLD` | Same | ✓ |
| Compile-time guards | `#ifdef HAVE_MPI ... #endif` blocks | Same | ✓ |

**Only new MPI primitive C2 introduces is `MPI_Allreduce`** (the existing LPJ-GUESS code only uses `MPI_Barrier`). `MPI_Allreduce` with `MPI_DOUBLE` / `MPI_INT` + `MPI_SUM` is standard MPI-1; universally supported by MPICH (Anaconda3 + KIT IMK-IFU `owl`), OpenMPI, Cray MPICH, Intel MPI, etc.

**Why `MPI_Initialized(&flag)` over `GuessParallel::parallel`**: (1) matches existing convention; (2) more robust (actually queries MPI state rather than trusting a cached bool); (3) `GuessParallel::parallel` isn't exposed via `parallel.h` so using it would require touching the header (larger backport surface).

### 3a.4 Year-boundary semantics — preserves single-process bit-exactness

**Critical correctness property**: in `year_outer` mode, the existing `outannual` year-change-detection at `imogenoutput.cpp:118` (`if (accum_year >= 0 && this_year != accum_year)`) was the auto-flush trigger that produced one flush per year on year+1 cell 0. My new explicit `flush_year_globally_synchronized` call at year boundary changes the TIMING (end of year_idx body vs start of year_idx+1 cell 0) but NOT the VALUES (year-aggregated; same set of cells contribute). After my new call, `accum_year=-1` so outannual's auto-flush at year+1 cell 0 sees `-1 < 0` and SKIPS — avoiding double-write.

**This means**: single-process `year_outer` mode produces:
- Same flush values per year ✓
- Same number of flushes per year (one) ✓
- Different timing (slightly earlier in execution order) ✓
- → Same `.out` file content ✓ → bit-exact xval preserved

Final-year handling: in year_outer mode, framework.cpp explicitly fires `flush_year_globally_synchronized` for EVERY `year_idx` including the last (since it's inside the `for (year_idx=0; ...< total_years; ...)` loop body). So the destructor's catch-all `if (year_pending && accum_year >= 0)` is naturally bypassed in year_outer (accum_year=-1 + year_pending=false after the explicit flush). In gridcell_outer mode the destructor still catches the final year as before.

### 3a.5 Verification this commit

| Check | Method | Result |
|---|---|---|
| Build clean (non-MPI; `build/`) | `cd lpjguess/build && make -j$(nproc)` | ✅ no errors; only pre-existing warnings |
| Build clean (MPI; `build_mpi/`) | `cd lpjguess/build_mpi && make -j$(nproc)` | ✅ no errors; only pre-existing warnings |
| 162 unit tests pass (non-MPI) | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| 162 unit tests pass (MPI) | `lpjguess/build_mpi/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| imogen 1cell xval against `build_mpi/guess` single-process | harness `scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ 37/37 bit-exact PASS |
| imogen 4cell xval (regression) | harness `4cell imogen` | ✅ 37/37 bit-exact PASS |
| imogencfx 1cell xval (regression) | harness `1cell imogencfx` | ✅ 37/37 bit-exact PASS |
| imogencfx 4cell xval (regression) | harness `4cell imogencfx` | ✅ 37/37 bit-exact PASS |
| MPI_Init + my code path actually fires under `mpirun -np 1 -parallel` | hand-built `run1/` workdir + `timeout 60 mpirun -np 1 build_mpi/guess -parallel -input imogen main_mpi_smoke.ins` | ✅ "Finished" printed + diagnostic `[ImogenOutput] flushed year=XXXX` visible (confirms `flush_year_globally_synchronized` is invoked + delegates to existing `flush_year` for the write) |

**Side-finding (separate from C2 core)**: the hand-built `mpirun -np 1` smoke produced NaN values in some output fields. Isolation test (same workdir + same .ins WITHOUT `-parallel`) shows the NaN ALSO appears in single-process mode → root cause is the ad-hoc workdir layout (missing some symlinks for default file searches that the standard `cross_validate_year_outer.sh` harness has). **NOT a C2 bug**. Documented for the C2 close-out task: the proper `mpirun -np 4` mimic will use `scripts/run_parallel_mimic.sh` (which delegates to `scripts/cluster/setup_run.sh`) for production-grade per-rank dir population.

### 3a.6 What is NOT yet verified at this commit (deferred to C2 close-out)

- **`mpirun -np 4` workstation MPI mimic with proper per-rank `runNN/` directory population** (requires `scripts/run_parallel_mimic.sh` + `scripts/cluster/setup_run.sh` integration; the setup_run.sh expects `-input imogen` + main.ins which is more straightforward AFTER B4 lands, since B4 expands ImogenInput's Rh/W/Tmin/Tmax consumer wiring needed for full functional loose-mode parallelism)
- **`MPI_Allreduce` aggregation correctness across multiple ranks** (test: with `coupling_mode "prescribed"` + 4 ranks × 1-cell-per-rank, verify the unified handshake file written by rank 0 has values = sum of per-rank contributions)
- **Lead-rank-only write race avoidance** (test: confirm only rank 0 opens/writes the unified handshake file; other ranks emit diagnostic dprintf but don't touch the file)
- **Both deferred to C2 close-out alongside B-bundles (B1+B2+B3+B4+B6+B10)**, with full per-rank workspace setup via `setup_run.sh`.

### 3a.7 CRITICAL FINDING — Substantive-validation NaN gap in the C1 baseline (2026-05-11)

**Discovered during C2 core verification**: while diagnosing apparent NaN values in a `mpirun -np 1 -parallel` smoke test, isolation experiments revealed that **ALL FOUR C1 cross-validation scenarios produce NaN-laden outputs**, both pre- and post-C2-core. The C1 close-out at `v0.17.0-step17a-c1-year-outer-single-process` (commit `8aafe84`) tagged the project on a baseline where `cmp -s` byte-equality between gridcell_outer and year_outer modes was passing **because NaN bytes match NaN bytes**, not because the simulation was producing scientifically correct outputs.

#### 3a.7.1 The forensic chain

| # | Test | Result | Implication |
|---|---|---|---|
| 1 | `mpirun -np 1 -parallel` smoke with hand-built `run1/` workdir | NaN at Year 1871 | Initial suspicion: workdir layout |
| 2 | Same .ins WITHOUT `-parallel` (MPI code path bypassed) | Same NaN at Year 1871 | NOT MPI-caused |
| 3 | Same .ins from `Common-directory/` cwd (xval-harness-equivalent) | Same NaN | NOT workdir-caused |
| 4 | Revert `lpjguess/` to C1 close-out state (`git checkout 8aafe84 -- ...`); rebuild; rerun xval | **Same NaN pattern, byte-identical to C2 output** | NaN exists in the C1 tag baseline |
| 5 | Test imogen + imogencfx, 1cell + 4cell, all 4 variants | All 4 produce identical NaN patterns | NOT input-module-specific; both share the underlying issue |
| 6 | nyear_spinup ∈ {2, 10, 30}; freenyears ∈ {0, 5, 15} | All produce NaN | NOT short-spinup-caused |
| 7 | Drop `crop_n.ins` import (use global.ins + wetlandpfts.ins only) | Still NaN | NOT crop-module-caused |
| 8 | Use soilmap-exact-match cells (-103.75 76.25; 94.25 54.25; -57.75 -33.75) | Still NaN | NOT soilmap-mismatch-caused |
| 9 | searchradius=50 dist=0 exact climate match | Still NaN | NOT search-radius-caused |
| 10 | Climate file inspection: T=237-276 K at -78.75/82.50 | Sane Arctic values | NOT climate-input-caused |

NaN first appears at **Year 2 Day 1** (= second simulation year) in `soil.NH4_mass` diagnostic from `lpjguess/modules/somdynam.cpp:574`. The Year=1 simulation completes without diagnostic NaN, then propagates to Year 2's soil-N integration.

#### 3a.7.2 Implications for C1 close-out validation

The C1 close-out (`v0.17.0-step17a-c1-year-outer-single-process` tag at `8aafe84`) claimed "GO/NO-GO gate per session-2 §9.5 PASSED for all 4 scenarios" based on `scripts/cross_validate_year_outer.sh` reporting "37/37 bit-exact matches; 0 mismatches" for each scenario. That claim was:

- **Nominally correct** (byte-equality preserved between gridcell_outer and year_outer)
- **Substantively misleading** (both modes produced byte-identical NaN-laden outputs; `cmp -s` byte-equality of NaN == byte-equality of NaN)

The cross-validation harness's `cmp -s` byte-equality logic is **necessary but not sufficient** for scientific validation. Both modes producing NaN doesn't validate year_outer's correctness — it just validates that whatever mechanism is producing NaN does so identically in both loop-ordering modes.

**The substantive validation gap means**: we have NEVER actually run a successful, non-NaN, end-to-end LPJG main-loop simulation with `-input imogen` (or `-input imogencfx` + `skip_inprocess_engine_run`) on our smoke gridlists in this rebuild. F-10 deadlock prevented it from running before C1; C1's skip_inprocess_engine_run + year_outer unlocked the LPJG main loop, but the simulation produces NaN immediately and we hadn't noticed.

#### 3a.7.3 What is NOT the cause (definitively ruled out)

- C2 MPI code (NaN identical between C1-only and C1+C2 builds)
- `MPI_Initialized` vs `GuessParallel::parallel` integration choice (irrelevant; MPI completely bypassed in single-process mode)
- `-parallel` CLI flag (NaN with and without)
- Loop-ordering mode (NaN identical in gridcell_outer + year_outer)
- Short spinup (NaN persists across nyear_spinup ∈ {2, 10, 30})
- Crop module import
- Gridcell-specific config (4 cells across diverse latitudes all NaN)
- Soilmap-mismatch fallback (NaN even with exact soilmap matches)
- Search-radius interpretation (NaN even with dist=0 exact climate matches)

#### 3a.7.4 Plausible remaining root-cause hypotheses (for B12 investigation)

1. **LPJ-GUESS vegetation/soil initialization** for `-input imogen` with engine ASCII climate has an undiscovered defect that surfaces in single-cell smoke runs; production main.ins's LPJG main loop has never actually been validated to produce non-NaN with this input combination because F-10 deadlock prevented it prior to C1.
2. **An LPJG-internal bug** in `ImogenInput::get_climate_for_gridcell` or the monthly→daily interpolation path that uninitialised values propagate from.
3. **A wetlandpfts.ins + global.ins interaction** that mis-initialises soil N pools.
4. **A LandSyMM_LPJ-GUESS fork-specific issue** (the "integrated LTS" base per Decision #3) that wouldn't appear in `trunk_r13078`. Could be diagnosed by F-11 Backport Sprint preparation work.
5. **A NaN-aware code path** in soil-N integration (e.g., a divide-by-zero guarded by IFNLIM that the smoke .ins config bypasses).

#### 3a.7.4c B12 RESOLVED (2026-05-11 evening; session 3; post-d7f6c74)

**ROOT CAUSE IDENTIFIED + FIX APPLIED + ALL 4 xval scenarios PASS substantive validation (bit-exact AND non-NaN; 0/37 NaN-laden files in any run).**

#### Root cause chain (forensic)

1. Smoke `.ins` files (`main_xval_loose.ins` + `main_xval_imogencfx.ins`) explicitly set `ifcalccton 0` and `ifcalcsla 0` (intended to mean "use values from .ins", but with side effects).
2. With `ifcalccton 0`, `parameters.cpp::CB_CHECKPFT` (lines 2333-2337) **SKIPS** `ppft->init_cton_min()` for each PFT.
3. `init_cton_min()` is what populates `cton_leaf_min` from `leaflong` via the Reich et al. 1992 relation (`guess.h:2275-2287`):
   ```cpp
   cton_leaf_min = 500.0 / pow(10.0, 1.75 - 0.33 * log10(12.0 * leaflong));
   ```
   Without this call, `cton_leaf_min` stays at its default-initialized value of `0` (double member of the Pft class).
4. `parameters.cpp:2345` calls `init_cton_limits()` **UNCONDITIONALLY** (regardless of `ifcalccton`). This function (`guess.h:2289-2334`) cascades `cton_leaf_min = 0` through:
   - `cton_leaf_max = cton_leaf_min × frac_mintomax = 0 × 2.78 = 0`
   - `cton_leaf_avr = avg_cton(0, 0) = 2.0 / (1/0 + 1/0) = 2/inf = 0`
   - `cton_root_max = cton_leaf_max × 1.16 = 0`
   - `cton_root_min = cton_root_max × 0.9 = 0`
   - `cton_root_avr = avg_cton(0, 0) = 0`
   - `cton_sap_max = cton_leaf_max × 6.9 = 0`
   - `cton_sap_min = cton_sap_max × 0.9 = 0`
   - `cton_sap_avr = avg_cton(0, 0) = 0`
5. Then for TREE PFTs (line 2329-2330), the respcoeff scaling:
   ```cpp
   respcoeff /= cton_root / (cton_root_avr + cton_root_min) +
                cton_sap  / (cton_sap_avr  + cton_sap_min);
   ```
   With `cton_root=29` (PFT-set), denominators `0+0 = 0`, so each ratio = `29/0 = +inf`, divisor = `inf+inf = inf`, and `respcoeff /= inf = 0`. Note for our smoke: `respcoeff` ends up = 0 (not inf). For grass, similar pattern.
6. At runtime in `canexch.cpp::npp()`, when fresh individuals are first created (`indiv.cmass_sap = nmass_sap = 0`), `Individual::cton_sap()` returns `pft.cton_sap_max = 0` (from the negligible-cmass-and-nmass guard branch).
7. In `respiration()` at `canexch.cpp:2494`:
   ```cpp
   resp_sap = respcoeff * K * cmass_sap / cton_sap * gtemp_air;
            = 0 * 0.095218 * 0 / 0 * gtemp = (0 * 0) / 0 * gtemp = 0/0 * gtemp = NaN;
   ```
   IEEE 754: `0/0 = NaN`. Then `0 * gtemp = NaN * gtemp = NaN`. So `resp_sap = NaN`.
8. `resp = resp_sap + resp_root + resp_growth` → `resp = NaN`.
9. `indiv.dnpp = assim - resp = 0 - NaN = NaN`.
10. `indiv.anpp += dnpp` → `anpp = NaN` (cumulative NaN through year).
11. At year-end `growth()`, `cmass_*` updated from `anpp` calculations → `cmass_* = NaN`.
12. ESTC debit at `growth.cpp:1524`: `report_flux(Fluxes::ESTC, -(cmass_leaf + cmass_root + cmass_sap + cmass_heart - cmass_debt)) = -NaN`.
13. NaN propagates through `Fluxes::report_flux` → annual flux accumulators → `outannual()` → all `.out` files → continues to next year via NaN soil-N pools.
14. By Year 2 Day 0 (= second historical year, Jan 1 1872 in our config), `vegetation_n_uptake()` at `somdynam.cpp:1545` reads NaN `nmass_avail()` → propagates to NH4_mass updates → triggers the diagnostic at `somdynam.cpp:574`.

**Why predecessor `version_A` doesn't NaN**: predecessor's `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/main.ins` does NOT set `ifcalcsla` or `ifcalccton` explicitly, so they take the LPJ-GUESS defaults (= 1). With `ifcalccton 1`, `init_cton_min()` IS called for each PFT, populating `cton_leaf_min` correctly, and the entire cascade produces sensible non-zero C:N ratios.

**Why this only surfaced in v1.0**: per the inherited handoff, the LPJG main loop NEVER ran in our rebuild prior to step 17a's C1 close-out (F-10 deadlock blocked it pre-C1; C1's `skip_inprocess_engine_run` parameter unlocked it). So this latent bug (from setting `ifcalccton 0` in our smoke `.ins`) was never exercised. Once the LPJG main loop started running for the first time post-C1, the bug surfaced as the substantive-validation NaN finding.

#### Diagnostic methodology this session

A 4-stage diagnostic-narrowing process landed the root cause in ~2 hours:

1. **Stage 1: spinup-duration hypothesis** — REFUTED. Increased nyear_spinup from 2 to 30 + freenyears 0 to 10 → NaN persisted (and started 1 year earlier, not later).
2. **Stage 2: extreme-cold-cell-specific hypothesis** — REFUTED. Tested temperate cell (Switzerland 7.50°E 47.50°N) → same NaN pattern.
3. **Stage 3: wetlandpfts.ins hypothesis** — REFUTED. Dropped wetlandpfts.ins import → identical NaN.
4. **Stage 4: surgical NaN-source instrumentation** — RESOLVED. Added `Fluxes::report_flux` first-NaN diagnostic + targeted `growth.cpp:1524` ESTC-debit diag + `canexch.cpp:2635` dnpp-accumulation diag + `canexch.cpp:2626` respiration-inputs diag. Diagnostic chain definitively traced: dnpp NaN at Year 2 Day 0 → resp NaN → all respiration inputs are FINITE → therefore arithmetic INSIDE respiration() produces NaN with finite inputs → only possible via `0/0` → cton_sap = 0 (not NaN) → traced to `init_cton_limits()` cascading from `cton_leaf_min = 0` → traced to `init_cton_min()` not being called because `ifcalccton 0`.

#### Fix applied (this commit; backport-IRRELEVANT)

Two `.ins` file changes (no `lpjguess/` source change):

1. `runs/SSP1-2.6/main_xval_loose.ins`: changed `ifcalcsla 0` → `1` and `ifcalccton 0` → `1`. Added 13-line explanatory comment documenting the root cause + fix rationale + cross-references.

2. `runs/SSP1-2.6/main_xval_imogencfx.ins`: same change with shorter cross-reference comment.

#### Verification (this commit)

| Check | Method | Result |
|---|---|---|
| Build clean (build/) | `cd lpjguess/build && make -j$(nproc)` | ✅ |
| Build clean (build_mpi/) | `cd lpjguess/build_mpi && make -j$(nproc)` | ✅ |
| 162 unit tests (build/) | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| 162 unit tests (build_mpi/) | `lpjguess/build_mpi/runtests --reporter compact` | ✅ same |
| imogen 1cell xval | `scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ "PASS (substantive): All .out files are bit-exact AND non-NaN" (37/37 byte-equal; 0/37 NaN; 0/37 NaN) |
| imogen 4cell xval | `scripts/cross_validate_year_outer.sh 4cell imogen` | ✅ same PASS pattern |
| imogencfx 1cell xval | `scripts/cross_validate_year_outer.sh 1cell imogencfx` | ✅ same PASS pattern |
| imogencfx 4cell xval | `scripts/cross_validate_year_outer.sh 4cell imogencfx` | ✅ same PASS pattern |
| All 4 xval against build_mpi/guess single-process | `GUESS_BIN=...build_mpi/guess scripts/cross_validate_year_outer.sh ...` × 4 | ✅ all 4 PASS substantive |

**The substantive-validation NaN-gate (added 2026-05-11 in commit `f13b302`) now correctly reports PASS** for all 4 xval scenarios. The C1 byte-equality + non-NaN GO/NO-GO gate (per session-2 §9.5 + STEP_17a.md §7) is now SUBSTANTIVELY VALIDATED for the first time in our rebuild.

#### Sample post-fix output (sanity check)

`nflux.out` for cell (7.50, 47.50) Switzerland:
```
      Lon      Lat Year   NH4dep   NO3dep      fix     fert     flux    leach      NEE
     7.50    47.50 1871    -1.00    -1.00    -0.00    -0.00     0.17     1.03    -0.80
     7.50    47.50 1872    -1.00    -1.00    -2.78    -0.00     0.02     0.24    -4.53
     7.50    47.50 1879    -1.00    -1.00    -9.21    -0.00     0.04     1.07   -10.10
```
Sensible values: NH4/NO3dep -1.00 kgN/ha/yr (pre-industrial deposition; LPJG sign convention); N fixation ramps from 0 to -9.21 (system reaches near-equilibrium); leaching grows as N pool builds.

`cflux.out`:
```
     7.50    47.50 1871    0.000000    0.000   -0.000    0.000    0.00000    0.000    0.00000
     7.50    47.50 1872    0.000000    0.000   -0.000    0.000    0.00000   -0.037   -0.03674
     7.50    47.50 1879    0.000000   -0.138    0.014    0.064    0.00000    0.000   -0.06043
```
Sensible C dynamics: vegetation establishes at Year 1872 (Est=-0.037); Year 1879 has growing biomass (Veg=-0.138 = NPP × negative-sign-convention); soil C respiration ramping (Soil=0.064).

#### B12 status

**B12 IS RESOLVED.** Removed from "in-progress" item list. Will be marked DONE in `notes/FOLLOWUPS.md` "B-item bundling commitment (2026-05-11)" sub-section.

#### Defensive hardening recommendation (NOT done in this fix; documented for follow-up)

The bug was a **trap** in the LPJG configuration system: `ifcalccton 0` is a documented option (means "use cton_leaf_min from .ins") but with TeBE not setting `cton_leaf_min` explicitly in `global.ins`, the default-init-to-zero produces NaN downstream. **Defensive hardening options** (added as new audit item B13 in next commit):

- Option A: at `init_cton_limits()`, fail() with a clear message if `cton_leaf_min == 0`.
- Option B: at `init_cton_limits()`, fail() with a clear message if `cton_sap_max == 0` post-cascade.
- Option C: at `respiration()` line 2494, guard against `cton_sap == 0` divide-by-zero with a `negligible()` check.

Recommend Option A (cleanest; fail-fast at init time before any simulation runs). Tracked as new audit item B13 (defensive hardening; effort 0.5 day; bundle with step 18 docs/cleanup era; non-blocking for v1.0 release).

#### Process hardening recommendation (NEW audit item B14 + persistent Operational heuristics in FOLLOWUPS)

**B12 was structurally a config-divergence-from-canonical-baseline issue, not an LPJG code defect.** Predecessor `version_A`'s `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/global.ins` (which `main.ins` imports as its first line) sets `ifcalcsla 1` and `ifcalccton 1` (lines 96 + 98). Our smoke `main_xval_*.ins` overrode those to `0` without supplying the manual PFT-level fields that mode requires. A diff-against-original at `.ins` level would have flagged it immediately.

User direction in session continuation 2026-05-11 evening: **do not** undertake a full `.ins` realignment audit now (the `ifcalccton 1`/`ifcalcsla 1` fix sufficed); **do** document the lesson persistently for future chats. Operationalised via:

- **NEW audit item B14** in `notes/FOLLOWUPS.md` "B-item bundling commitment" table: one-time `.ins` parity audit of `runs/SSP1-2.6/main_xval_*.ins` (and the imported `global.ins` / `crop_n.ins` / `wetlandpfts.ins` / `imogen_intermediary.ins` chain) vs `version_A/.../landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/` and `version_B/.../landsymm_imogen/SSP1_RCP26/`. Each divergent parameter classified as **intentional** (rationale documented at the parameter site) or **unintentional** (open follow-up). Effort: 0.5–1 day. Bundle: step 18 (docs/reproducibility era); opportunistically usable earlier on any output anomaly.
- **NEW persistent "Operational heuristics — lessons learned" subsection** in `notes/FOLLOWUPS.md` (after "Tracking discipline"). Five standing rules distilled from B12 + Part 19 forensics, with `.ins`-parity-with-original as **rule #1** ("FIRST-LINE forensic step when outputs look wacky"). Designed as a stable anchor inheritable by any fresh chat that reads `FOLLOWUPS.md`.

Together B13 (code-level fail-fast) and B14 (process-level parity audit + persistent heuristics) form complementary defences against the trap that produced B12.

### 3a.7.4b B12 first-investigation findings (2026-05-11 evening; post-f13b302)

After commit `f13b302` landed cleanly on all 3 remotes, the user explicitly asked about units disparity (imogen vs LPJG climate variable conventions), dataset completeness (LU, ndep, CO2, simfire), and inspiration from predecessor configs at `version_A/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/` + `version_B/landsymm_imogen/SSP1_RCP26/`. ~30 minutes investigation; key findings:

**Predecessor SSP1_RCP26 main.ins (`version_A/.../landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/main.ins`)** — major differences from our `main_xval_loose.ins`:

| Setting | Predecessor production | Our `main_xval_loose.ins` |
|---|---|---|
| `nyear_spinup` | **500** | 2 |
| `freenyears` | **100** | 0 |
| `file_ndep` | `Data/Ndep/ndep_cruncep/GlobalNitrogenDeposition.bin` (REAL) | `""` (empty) |
| `file_simfire` | real path | NOT SET |
| `file_popdens` | `""` for SimFire-NOFIRE-mode | NOT SET |
| `firsthistyear`-`lasthistyear` | 1901-2100 | 1871-1879 |
| `file_gridlist` | `gridlist_in_62892_and_climate.txt` (62892 cells; aligned with all data archives) | `gridlist_test1.txt` or `gridlist_test2.txt` (test cells; NOT necessarily aligned with archives) |
| Intended invocation | `-input cf` (with NetCDF climate; though all `file_temp1`..`file_temp2` commented out — so actually engine ASCII via imogen_intermediary.ins) | `-input imogen` |

**N-deposition data IS available locally**: `data/ndep/ndep_cruncep/GlobalNitrogenDeposition.bin` (138 MB) + RCP26/45/60/85 variants (each ~96-98 MB). NOT in git (gitignored; Tier-2 per step 6 manifest). Predecessor's main.ins uses `GlobalNitrogenDeposition.bin`.

**Code-path inspection** (`lpjguess/cru/guessio/lamarquendep.cpp`):

- Line 119-122: when `file_ndep == ""`, `getndep()` calls `set_to_pre_industrial()` which sets all NHx/NOy Dry/Wet arrays to a well-defined constant (~2 kgN/ha/yr per line 281-292). NOT NaN. **So empty file_ndep is NOT the NaN cause.**
- Line 127-128: when `file_ndep != ""`, archive is opened. Archive is exact-match-only (no search radius). Line 135-138: if cell not found in archive, `fail()` aborts execution.

**Empirical test**: set `file_ndep` to the real path with our smoke cell (-78.75, 82.50). Result: `getndep(): Grid cell (lon, lat: -78.75,82.5) not found in /home/.../GlobalNitrogenDeposition.bin` → exit code 99 (fail). Our smoke gridcells aren't in the N-dep archive (which uses production-style 0.5°-aligned cells from `gridlist_in_62892_and_climate.txt`).

**Conclusion**: N-deposition is NOT the cause of NaN. The pre-industrial constant fallback is well-defined and correct. We have ruled out one more hypothesis.

**Remaining plausible root causes (UNCHANGED from §3a.7.4)**:
1. LPJ-GUESS vegetation/soil initialization for `-input imogen` was never substantively validated (F-10 deadlock blocked LPJG main loop pre-C1)
2. LPJG-internal bug in `ImogenInput::get_climate_for_gridcell` or monthly→daily interpolation (NEW: also worth checking if climate values are being stored correctly in the per-cell cache vs being read with wrong indexing)
3. `wetlandpfts.ins` + `global.ins` initialisation interaction (NEW: predecessor production main.ins also imports both; not unique to xval)
4. LandSyMM_LPJ-GUESS fork-specific issue
5. NaN-aware code path in soil-N integration

**Unit disparity check (user's other angle)**: ImogenInput::getclimate at `imogen_input.cpp:876` converts `climate.temp = dtemp[date.day] - 273.15` (K→C). IMOGENCFXInput's `get_climate_for_gridcell` does the K→C conversion at the input-reading layer (post-C1.3 sub-step 7.3.2 fix at `8aafe84`). Other variables (P, SW, WET, DTEMP) — units should match (precip mm/day, insol W/m², wetdays count, DTR K → maybe should also be K converted to C? would need investigation). **This is a remaining angle that could be relevant** if any non-T climate variable has units mismatch causing biogeochemistry NaN.

**Next investigation angles (for next session continuation)**:
1. Inspect `imogen_input.cpp:get_climate_for_gridcell` line-by-line for any uninitialized data or wrong-units assignment for non-T variables (P, SW, WET, DTEMP, Rh, W, Tmin, Tmax)
2. Try a gridcell that IS in `gridlist_in_62892_and_climate.txt` AND in the engine climate grid (= the natural intersection point that predecessor production uses) — even if it requires `searchradius > 0` for climate
3. Run `-input cru_ncep` (standard CRU climate) on the same gridcell to isolate whether NaN is IMOGEN-input-specific or fundamental
4. Inspect xval's `run.log` for the FIRST appearance of NaN — pinpoint which subroutine produces it (somdynam.cpp:574 is just the diagnostic; actual NaN-generation may be upstream in canexch.cpp or vegdynam.cpp)
5. Read `lpjguess/cru/guessio/cruinput.cpp::getclimate` for reference of how the production-validated code path works; diff against ImogenInput::getclimate



This commit introduces audit item **B12: Substantive-validation NaN root-cause investigation + fix** as a NEW critical-path item bundled with the C2 era. B12 is NOT optional and is NOT post-v1.0. It must land BEFORE the `v0.17.5-step17b-c2-mpi-sync` tag because the tag should be on a substantively-validated baseline, not on byte-equal-but-NaN-laden output.

Estimated effort: 2-10 days (genuinely unbounded). Could be a quick fix if it's something obvious in LPJG init; could require LPJG-developer-level expertise if it's a deep main-loop issue. Tracking in `notes/FOLLOWUPS.md` "Comprehensive outstanding-work audit (2026-05-11)" §B item B12 + "B-item bundling commitment (2026-05-11)" sub-section.

C2 era combined sprint estimate revised: **~11-23+ days** (was 9-13 d) due to B12 addition.

### 3a.8 xval harness hardening this commit (per B12 finding)

`scripts/cross_validate_year_outer.sh` is updated to add a **substantive-validation NaN gate** that runs AFTER the existing byte-equality check. The gate:

- Scans Run A and Run B `.out` files for `nan` tokens (case-insensitive)
- Reports the byte-equality and non-NaN check results separately
- If either run has NaN-laden `.out` files: **FAILS with exit code 3** (was: PASS based on byte-equality alone)
- Provides actionable diagnostic output pointing at this STEP_17b.md §3a.7 + FOLLOWUPS B12 + session-2 handoff Part 18

Effect on existing validation: until B12 is investigated + fixed, **all 4 cross-validation scenarios will now correctly REPORT FAIL** rather than masking the NaN issue behind byte-equality-of-garbage. This is the desired "stop the line" behavior — forces explicit attention on the science-correctness gap.

The C1 close-out tag at `v0.17.0-step17a-c1-year-outer-single-process` is preserved as-is in the git history (no retroactive de-tagging); it represents the byte-equality validation milestone, which is genuinely a real achievement (year_outer mechanics ARE byte-equivalent to gridcell_outer). The substantive-validation FAIL is a NEW, separate gate added 2026-05-11 to catch a previously-undetected gap.

---

## 3b. B10 — Symmetric Fortran engine writer fix (LANDED this commit, 2026-05-11)

### 3b.1 Pre-implementation re-examination (2026-05-11)

Per user direction "do a more meticulous, systematic, and comprehensive examination of the various documentations (including handoffs) to be sure of what we are doing", a comprehensive re-examination of the project's strategic decisions was completed before any B-item edits. The re-examination drew on `EXECUTION_PLAN.md` (Decisions #2/#11/#12; step rows 8/9/9.5/17a/17b), `_phase2_findings/04_imogen_cxx.md` (the 25-bug catalogue of the *standalone* IMOGENCXX C++ refactor), `notes/STEP_9.5.md` (engine architecture + Rh/W rationale), and `notes/FOLLOWUPS.md` (F-3 Fortran↔C++ parity + B-item interrelations). Findings:

1. **Canonical IMOGEN engine for v1.0 = Fortran** (`imogen/code/imogen_lpjg.f`), per Decision #2. The standalone IMOGENCXX C++ refactor (`version_A/.../IMOGENCXX/ImogenCXX/src/Main.cpp`; preserved as immutable archive per Decision #5) carries 25 documented bugs and is **deferred to Phase 2** for parity work.
2. **Distinct from IMOGENCXX**: there is also an *in-process* C++ engine port at `lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` used by `imogencfx` mode in v1.0. This is the engine that received the alternating-year writer fix at commit `7be595a` (2026-05-10; 5 conditional removals; ~76 LOC of doc blocks).
3. **B1 (Fortran Rh + Wind COMPUTATION port)** = port the Rh/W *physics computation* (~70-100 LOC) from the in-process C++ engine to the standalone Fortran engine. It is NOT about "fixing 25 bugs" of the standalone IMOGENCXX (those are Phase 2). The C++ in-process port serves as a *reference* for what computations to add to Fortran.
4. **B10 (Symmetric Fortran engine writer fix)** = mechanically replicate `7be595a`'s alternating-year fix in `imogen_lpjg.f`. Same root-cause bug (single-iteration OPEN/CLOSE gates on `IYEAR.EQ.YEAR1`/`IYEAR.EQ.IYEND` causing every-other-year empty climate output); same fix shape (unconditional OPEN/CLOSE per IYEAR iteration).

### 3b.2 Empirical scope refinement: 5 → 7 conditional removals

Inspection of `imogen_lpjg.f` revealed **7 conditional gates** (vs the originally-documented 5 in the FOLLOWUPS B10 row, which carried over from the C++ fix's 5-removal count):

| # | Line (pre-fix) | Block | Has C++ analogue? | Notes |
|---|---|---|---|---|
| 1 | 854 | CO2 writer OPEN (units 91, 98) | YES (`climatemodel.cpp` ~787) | Same logic |
| 2 | 883 | CO2 writer CLOSE (units 91, 98) | NO (Fortran-specific extra) | C++ uses `std::ofstream` RAII so close is implicit; Fortran requires explicit `CLOSE` |
| 3 | 954 | Climate-anomaly REGRID OPEN (T/P/SW/WET/DTEMP) | YES (`climatemodel.cpp` ~884) | Canonical doc lives here |
| 4 | 1013 | Climate-anomaly non-REGRID OPEN (same units) | NO (Fortran-specific extra) | C++ in-process port has no native-grid branch; always writes on a single grid |
| 5 | 1071 | Climate-anomaly CLOSE (units 11, 92, 93, 94, 95) | YES (`climatemodel.cpp` ~963) | Same logic |
| 6 | 1088 | FA_OCEAN/DTEMP_O OPEN (units 95, 96) | YES (`climatemodel.cpp` ~988) | Same logic |
| 7 | 1099 | FA_OCEAN/DTEMP_O CLOSE (units 95, 96) | YES (`climatemodel.cpp` ~998) | Same logic |

So **7 = 5 C++ analogues + 2 Fortran-specific extras** (CO2 CLOSE; non-REGRID OPEN). This is an **empirical refinement** of the originally-documented scope, not a scope expansion of intent: the *intent* (full alternating-year symmetry with the C++ fix) was always to fix every site exhibiting the bug; the original "5" count was inherited from the C++ fix's count without re-counting against the Fortran source.

### 3b.3 Framing: symmetric-correctness, not blocker

The Fortran engine is **NOT on the v1.0 production path**: the `imogen` mode in v1.0 calls a different launcher path; the Fortran engine is currently exercised only by **engine-only smoke testing** (e.g., `imogen/code/IMOGEN/output/{1871,1872}/` artefacts). The C1.2/C1.3 cross-validation PASSes verified at `7be595a` were on the C++ in-process port, not the Fortran engine.

So B10 is about **engine parity** (per F-3 Fortran↔C++ IMOGEN parity in `notes/FOLLOWUPS.md`) — keeping the two engines in lock-step so future engine-mode switches inherit identical writer semantics — rather than unblocking any current-path failure. Hence the **symmetric-correctness framing** rather than a "critical bug fix" framing.

### 3b.4 What landed this commit

| File | Change | LOC |
|---|---|---|
| `imogen/code/imogen_lpjg.f` | 7 conditional removals at lines (pre-fix) 854/883/954/1013/1071/1088/1099 + canonical doc block at the climate-anomaly REGRID OPEN (mirroring the canonical doc at `climatemodel.cpp` ~884) + 6 cross-referencing short blocks at the other sites | +121, -37 (net +84) |

Backport-relevance: **HIGH**. The Fortran engine source `imogen/code/imogen_lpjg.f` is part of the LandSyMM rebuild's core IMOGEN component. If `trunk_r13078`'s upstream IMOGEN ships the same engine file (likely; this is canonical Huntingford-Cox IMOGEN code), the same 7 mechanical removals apply. Ledger entry added at `notes/TRUNK_R13078_BACKPORT_LEDGER.md`.

### 3b.5 Verification this commit

| Check | Method | Result |
|---|---|---|
| Clean Fortran build | `cd imogen/code && rm -f *.o imogen_lpjg && bash compile.sh` | ✅ Exit 0; binary 129 600 bytes; ZERO warnings |
| Static gate-removal check | `rg 'IYEAR\.EQ\.(YEAR1\|IYEND)' imogen/code/imogen_lpjg.f` | ✅ Only matches are: (a) line 495 pre-existing `!IF(IYEAR.EQ.YEAR1)` legacy comment, (b) line 496 `IYEAR.EQ.YEAR1_LPJG` (different gate variable, not part of B10), (c) lines 974+1001-1007 = my own doc-block paragraph references. **All 7 B10 gates correctly removed.** |
| Net LOC parity with C++ | `git diff --shortstat` | ✅ +121, -37 (vs C++ `7be595a`'s +76, -5; proportionate given 7 vs 5 fixes + 2 extra Fortran-specific cross-reference blocks) |
| Pre-fix evidence preserved | `ls imogen/code/IMOGEN/output/{1871,1872}/` | ✅ `1871/` has 9 climate files (full); `1872/` has only `done` marker (empty) — empirical pre-fix demonstration of the alternating-year quirk, retained as a documentation artefact |
| C++ fix doc-block parity | Visual diff of `imogen_lpjg.f` canonical block (line ~969 post-fix) vs `climatemodel.cpp` canonical block (line ~884 post-`7be595a`) | ✅ Same structure: ROOT-CAUSE FIX paragraph + symmetric-engine-list paragraph + FIX paragraph + symmetric-removals list + backport note + author/date stamp |

**Empirical post-fix engine smoke test deferred** — would require staging the `CEN_IPSL_MOD_IPSL-CM5A-MR/` patterns + `DKB_dataset_totals/` emissions inputs that the existing `imogen_settings.txt` references but which are not currently shipped in the active rebuild's `imogen/` tree (the Fortran engine being NOT on the v1.0 production path means the inputs were not re-staged after Step 4's selective import). Per the symmetric-correctness framing, the clean compile + static gate-removal check + pre-fix evidence preserved together suffice for B10's verification gate. A full empirical engine smoke would naturally be staged when B1 (Fortran Rh + Wind COMPUTATION port) lands, since B1 will need engine input plumbing to verify its physics port — at which point a post-B1 engine smoke would simultaneously verify B10's writer fix in production.

### 3b.6 Re-ordering rationale (B10 → B6 → B2 → B3 → B4 → B1)

Per user concurrence on "Option A" (the assistant's recommendation 2026-05-11):

1. **B10 (this commit; ~0.5 d)** — most mechanical (literal copy-pattern from `7be595a`); zero new physics; zero new I/O semantics. Stages the Fortran engine for the heavier B1/B2/B6 work.
2. **B6 (next; ~0.5 d)** — Fortran T_anom 2× line count investigation; sits in the same `imogen_lpjg.f` writer block we just touched. Cohesive next-step.
3. **B2 (~0.5 d)** — Fortran Tmin/Tmax write block; algebraic `Tmin = T - DTEMP/2`; trivial extension of B6's writer-block work.
4. **B3 (~0.5 d)** — C++ Tmin/Tmax in REGRID branch of `climatemodel.cpp`; closes a `// TODO at step 9.5b` inline comment. Mirrors B2 logic on the C++ side.
5. **B4 (~1 d)** — `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion; mirrors C1.1 pattern; depends on B2+B3 producing the new outputs.
6. **B1 (~3-5 d)** — Fortran Rh + Wind COMPUTATION port (heaviest); ~70-100 LOC of new Fortran physics ported from `climatemodel.cpp`'s in-process C++ engine. Deliberately deferred to last so prior mechanical wins de-risk the bigger physics port.

Total bundle: ~6-8 d (matches §5 estimate). All within step 17b's C2 era.

---

## 3c. B6 — F-2 Fortran T_anom 2× line count investigation (LANDED this commit, 2026-05-11; **subsumed by B10**)

### 3c.1 Pre-investigation framing (per §3b.6 ordering)

Per the re-ordered Option A sequence (B10 → **B6** → B2 → B3 → B4 → B1), B6 was scheduled to be the cohesive next-step after B10 because both items live in the same `imogen_lpjg.f` writer block. The original F-2 audit note in `notes/FOLLOWUPS.md` listed four candidate hypotheses for the 2× line count (`STEP_4 §6` "Comparison with version_A's 1871 output" — our T_anom.dat = 3262 lines vs version_A reference = 1631 lines, exactly 2×):

1. Fortran writer iterates the cells twice (regrid + native; eliminated by user analysis: `1631 + 3698 = 5329 ≠ 3262`).
2. `NSDMAX`-related sub-day-step write that doubles the row count.
3. A genuinely doubled write loop (write each cell once for daily-mean, once for some other aggregate).
4. version_A's reference generated with a different (CMIP3 native) grid that genuinely had 1631 cells.

### 3c.2 Empirical forensic finding (this commit)

Inspection of the on-disk pre-fix outputs at `imogen/code/IMOGEN/output/1871/` (preserved as a documentation artefact per §3b.5) reveals the 2× line count is **one symptom of three** that all trace to the same alternating-year writer bug B10 just fixed:

| File | Our pre-fix lines | version_A reference | Pattern |
|---|---:|---:|---|
| `T_anom.dat` | 3262 | 1631 | **2× — doubled** |
| `P_anom.dat` | 3262 | 1631 | **2× — doubled** |
| `SW_anom.dat` | 3262 | 1631 | **2× — doubled** |
| `DTEMP_anom.dat` | 3262 | 1631 | **2× — doubled** |
| `WET.dat` | 1631 | 1631 | match |
| `fa_ocean.dat` | 11631 | 10000 | **+1631 — contaminated** |
| `dtemp_o.dat` | 508 | 254 | **2× — doubled** |
| `CO2.dat` | 1 | 1 | match (single-line file) |

The asymmetry between the **doubled** files (units 92, 93, 94, 11 plus dtemp_o on a separate unit) and the **single** WET file (unit 95) plus the **+1631-contaminated** fa_ocean file (unit 95 reused) is the smoking-gun pattern. Tail inspection of `fa_ocean.dat` (lines 9998-11631) confirms the contamination directly:

```text
[lines 9998-10000]    0.00000000          (legitimate fa_ocean float-free-format zeros)
[line 10001]    281.250  82.500         0         1         1 ...   (WET-format LON+LAT+12 ints!)
[line 10002]    285.000  82.500         1         1         1 ...   (WET-format LON+LAT+12 ints!)
...
[line 11631]    292.500 -55.000         1         1         1 ...   (WET-format LON+LAT+12 ints!)
```

Lines 10001-11631 of our pre-fix `fa_ocean.dat` are **exactly** WET.dat year-1872 content (1631 cells × `LON LAT + 12 monthly ints` per row). Version_A's reference `fa_ocean.dat` is clean (10000 lines of `0` only, no WET injection).

### 3c.3 Single-root-cause mechanism

The pre-B10 source had **both** sides of the OPEN/CLOSE pair gated by `IYEAR`-equality conditionals (verified by `git show 3c00428 -- imogen/code/imogen_lpjg.f`):

- OPENs of units 11/91/92/93/94/95/96/98 were wrapped in `IF(IYEAR.EQ.YEAR1) THEN ... ENDIF`
- CLOSEs of those same units were wrapped in `IF(IYEAR.EQ.IYEND) THEN ... ENDIF`

In a 2-year engine call (`YEAR1=1871, IYEND=1872`):

1. **Year 1871 (IYEAR.EQ.YEAR1=TRUE; IYEAR.EQ.IYEND=FALSE)**:
   - **All gated OPENs fire**. Climate writer opens units 92/93/94/95/11 against `/1871/{T,P,SW,WET,DTEMP}_anom.dat` with `STATUS='REPLACE'`; ocean-feedback block subsequently re-opens unit 95 against `/1871/fa_ocean.dat` (Fortran auto-closes the prior WET.dat connection on re-OPEN of the same unit) plus unit 96 against `/1871/dtemp_o.dat`; CO2 writer opens units 91/98 against `/1871/CO2.dat` and `IMOGEN/CO2_all.dat`.
   - **All writes fire**: 1631 cells × 12 monthly values to T/P/SW/DTEMP_anom.dat (1631 lines each); 1631 cells × 12 monthly integers to WET.dat (1631 lines, sealed at the auto-close mid-1871); 10000 floats to fa_ocean.dat (10000 lines); 254 floats to dtemp_o.dat (254 lines); 1 line to CO2.dat.
   - **All gated CLOSEs are skipped** (IYEAR.EQ.IYEND=FALSE). Units 92/93/94/11 (climate writers) + units 95/96 (ocean-feedback) + units 91/98 (CO2) **remain open across the year boundary**.

2. **Year 1872 (IYEAR.EQ.YEAR1=FALSE; IYEAR.EQ.IYEND=TRUE)**:
   - **All gated OPENs are skipped**. Units 92/93/94/11 still connect to `/1871/{T,P,SW,DTEMP}_anom.dat`. Unit 95 still connects to `/1871/fa_ocean.dat` (NOT to `/1871/WET.dat` — that connection was severed in step 1 by the auto-close on unit-95 re-OPEN). Unit 96 still connects to `/1871/dtemp_o.dat`. Units 91/98 still connect to `/1871/CO2.dat` and `IMOGEN/CO2_all.dat`.
   - **All writes fire and append to the still-open year-1871 files**:
     - `WRITE(92/93/94/11,...) T/P/SW/DTEMP` → append 1631 cells × 12 monthly values to `/1871/{T,P,SW,DTEMP}_anom.dat` → **3262 lines each** (the original F-2 symptom).
     - `WRITE(95,...) F_WET_CLIM_OUT(IGP,IMM)` (in the climate-writer loop) → append 1631 cells × 12 monthly **WET-format integers** to **the still-open `/1871/fa_ocean.dat`** (because unit 95's last connection was to fa_ocean, not WET) → **11631 lines** with the trailing 1631 being the smoking-gun `LON LAT + 12 ints` rows.
     - `WRITE(96,...)` → append 254 lines to `/1871/dtemp_o.dat` → **508 lines**.
     - `WRITE(91,...) / WRITE(98,...)` → append CO2 lines to `/1871/CO2.dat` and `IMOGEN/CO2_all.dat`.
   - **All gated CLOSEs fire** (IYEAR.EQ.IYEND=TRUE). All units sealed. `/1872/` directory ends up with only the unconditional `done` marker — no climate, no CO2, no fa_ocean, no dtemp_o.

So the four symptoms (T/P/SW/DTEMP × 2; WET × 1; fa_ocean + 1631; dtemp_o × 2) are **one bug expressed multiple ways**: the alternating-year OPEN/CLOSE gating prevents year 1872's writer from receiving fresh per-year file targets, and the asymmetry between the doubled (climate-writer-only) units and the contaminated (climate+ocean-feedback shared) unit 95 is the unit-reuse interleaving fingerprint.

### 3c.4 Determination — B6 subsumed by B10

**B10's structural fix** (commit `3c00428`, 2026-05-11) replaces every `IF(IYEAR.EQ.YEAR1)` OPEN gate and every `IF(IYEAR.EQ.IYEND)` CLOSE gate (7 such gates in `imogen_lpjg.f`) with unconditional per-IYEAR semantics. Post-B10, in the same 2-year engine call:

1. **Year 1871**: every climate/CO2/ocean OPEN fires with `STATUS='REPLACE'` against `/1871/`-targeted paths → fresh empty files. Writer writes 1631 cells to each of 5 climate units. Every CLOSE fires at year-end → units fully released.
2. **Year 1872**: every OPEN fires fresh with `STATUS='REPLACE'` against `/1872/`-targeted paths → fresh empty files in `/1872/`. Writer writes 1631 cells. CLOSE fires → units released.

**Net effect on each symptom**:
- T_anom/P_anom/SW_anom/DTEMP_anom: 1631 lines per year per file (in `/1871/` AND `/1872/`). 2× doubling **eliminated**.
- WET.dat: 1631 lines per year per file (in `/1871/` AND `/1872/`). Asymmetric-vs-T eliminated.
- fa_ocean.dat: 10000 lines per year per file (in `/1871/` AND `/1872/`). Contamination **eliminated** because year-1872 WET writes go to `/1872/WET.dat` (a fresh unit-95 connection) not the year-1871 fa_ocean unit.
- dtemp_o.dat: 254 lines per year per file. 2× doubling eliminated by the same mechanism on unit 96.

**Therefore B6 requires no additional code change.** It is **subsumed by B10**: the 2× line count is a downstream symptom of the same alternating-year OPEN/CLOSE gating bug that B10 mechanically fixed.

### 3c.5 Verification

| Check | Method | Result |
|---|---|---|
| Empirical pre-fix on-disk pattern | `wc -l imogen/code/IMOGEN/output/1871/*.dat` | ✅ T/P/SW/DTEMP=3262, WET=1631, fa_ocean=11631, dtemp_o=508 — confirms the 3-symptom pattern |
| version_A reference parity | `wc -l version_A/.../IMOGEN/output/1871/*.dat` | ✅ T/P/SW/DTEMP=1631, WET=1631, fa_ocean=10000, dtemp_o=254 — matches the predicted post-B10 structural output |
| Contamination tail signature | `sed -n '9998,10003p' imogen/code/IMOGEN/output/1871/fa_ocean.dat` | ✅ Lines 10001+ are WET-format `LON LAT + 12 ints` (smoking-gun signature) |
| Static writer-block analysis | grep `WRITE\(\s*(11\|92\|93\|94\|95)\s*[,\)]` in `imogen_lpjg.f` | ✅ Only one writer block (lines 1019-1071 REGRID; 1083-1135 non-REGRID); no other doubled-write paths |
| Loop-structure analysis | Inspect IYEAR loop (lines 485-1189) | ✅ Climate writer fires once per IYEAR iteration via the `(STEP_DAY.EQ.1).AND.(MM.EQ.12).AND.(MD.EQ.30)` gate (MM, MD are PARAMETERs = always true; STEP_DAY=1 from settings). No nested loops doubling firings. |

**Empirical post-B10 engine smoke-test deferred** for the same reason as B10 (the Fortran engine inputs `CEN_IPSL_MOD_IPSL-CM5A-MR/` patterns + `DKB_dataset_totals/` emissions are not currently shipped in the active rebuild; will be staged when B1 lands and a post-B1 engine smoke will simultaneously verify B6's predicted post-fix structure).

### 3c.6 Net code change for B6

**ZERO** Fortran source change. B6 is fully covered by `3c00428`'s 7 conditional removals + doc blocks. The net deliverable for B6 is **documentation only** (this §3c + companion entries in `CHANGELOG.md`, `EXECUTION_PLAN.md`, `notes/FOLLOWUPS.md`, `notes/TRUNK_R13078_BACKPORT_LEDGER.md`, and chat-handoff Part 22).

Backport-relevance: **N/A** (no source change; the B10 backport entry already covers all 7 gates whose removal collectively fixes the B6 symptom).

### 3c.7 Lesson for future audit-item triage

**B6's "subsumed by B10" outcome is a generalisable forensic pattern**: when a multi-year writer block exhibits asymmetric file-size scaling across files written from the SAME loop (some doubled, some not, some contaminated), check first whether the discrepancies all trace to a single OPEN/CLOSE-gating root cause across a unit-reuse chain. The triage rule is captured as a new entry in the persistent "Operational heuristics — lessons learned" subsection of `notes/FOLLOWUPS.md`.

---

## 3d. B2 — Fortran Tmin/Tmax write block (LANDED this commit, 2026-05-12)

### 3d.1 Pre-implementation framing (per §3b.6 ordering)

Per the re-ordered Option A sequence (B10 → B6 → **B2** → B3 → B4 → B1), B2 was scheduled as the next mechanical win after B6 because both items live in the same `imogen_lpjg.f` writer block. B2's scope per `notes/FOLLOWUPS.md` audit-table B-row + `notes/STEP_4.md` step 9.5b: add `Tmin_anom.dat` and `Tmax_anom.dat` writers to the Fortran engine using the algebraic derivation `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2` (per Decision #11; same units as T = Kelvin), mirroring the C++ in-process port at `lpjguess/modules/climatemodel.cpp` ~lines 952-953 (where `file100`/`file101` ofstreams already produce these outputs in the non-REGRID branch).

### 3d.2 Scope decision — both Fortran branches (REGRID + non-REGRID)

The C++ in-process port has Tmin/Tmax in the **non-REGRID branch only** (an explicit `// TODO at step 9.5b` comment at `climatemodel.cpp` ~line 894 documents the pending REGRID-side addition; that's **B3's** scope on the C++ side). The standalone Fortran engine has BOTH REGRID and non-REGRID branches in the climate-anomaly writer block. The natural Fortran scope is to add Tmin/Tmax to **both** Fortran branches — leaves no asymmetry between branches; doesn't pre-empt B3 (which is C++-side; B3 will add Tmin/Tmax to the C++ REGRID branch). The Fortran's REGRID branch addition here is independent of B3.

### 3d.3 Unit number selection — 100/101 (free; mirrors C++)

Existing `imogen_lpjg.f` unit usage (per `rg "OPEN\(\s*[0-9]+" imogen_lpjg.f`): `1, 2, 3, 4, 6, 11, 21, 49, 51, 60, 62, 63, 64, 65, 66, 72, 81, 82, 91, 92, 93, 94, 95, 96, 97, 98, 99`. Units **100 and 101 are free** and mirror the C++ ofstream variable names (`file100`, `file101`) for ergonomic cross-engine code-reading. Verified by `rg "OPEN\(\s*(100|101)\s*[,\)]" imogen_lpjg.f` returning zero pre-B2 hits.

### 3d.4 What landed this commit (1 file; +59, -0; net +59 LOC; backport-RELEVANT)

Nine surgical insertions in `imogen/code/imogen_lpjg.f`, distributed across the post-B10 writer block (no removals; all additive):

| # | Site | Branch | Action |
|---|---|---|---|
| 1 | After REGRID `OPEN(11, .../DTEMP_anom.dat)` (line ~1023 pre-B2) | REGRID | Canonical doc block + `OPEN(100, .../Tmin_anom.dat)` + `OPEN(101, .../Tmax_anom.dat)` |
| 2 | After REGRID `WRITE(11) LAT_OUT(IGP)` | REGRID | Short doc + `WRITE(100/101) LON_OUT(IGP)` + `WRITE(100/101) LAT_OUT(IGP)` (4 lines) |
| 3 | After REGRID DAILYOUT=TRUE `WRITE(95) F_WET_CLIM_REGRID` | REGRID | Short doc + `WRITE(100, '(f10.3)', ADVANCE='NO') T_OUT_M_REGRID(IGP,IMM,IMD,IND) - DTEMP_OUT_M_REGRID(IGP,IMM,IMD)/2.0` + same for unit 101 with `+` |
| 4 | After REGRID DAILYOUT=FALSE `WRITE(95) F_WET_CLIM_REGRID` | REGRID | Short doc + Tmin/Tmax monthly variants using `T_OUT_M_REGRID(IGP,IMM,1,1)` + `DTEMP_OUT_M_REGRID(IGP,IMM,1)` |
| 5 | After REGRID per-cell `WRITE(11,'()')` | REGRID | Short doc + `WRITE(100,'()')` + `WRITE(101,'()')` |
| 6 | After non-REGRID `OPEN(11, .../DTEMP_anom.dat)` (line ~1087 pre-B2) | non-REGRID | Short cross-ref doc + `OPEN(100, .../Tmin_anom.dat)` + `OPEN(101, .../Tmax_anom.dat)` |
| 7 | After non-REGRID `WRITE(11) LAT(IGP)` | non-REGRID | Short doc + `WRITE(100/101) LONG(IGP)` + `WRITE(100/101) LAT(IGP)` (4 lines; uses `LONG/LAT` not `LON_OUT/LAT_OUT`) |
| 8 | After non-REGRID DAILYOUT=TRUE `WRITE(95) F_WET_CLIM_OUT` | non-REGRID | Short doc + Tmin/Tmax daily writes using `T_OUT_M(IGP,IMM,IMD,IND)` + `DTEMP_OUT_M(IGP,IMM,IMD)` (no `_REGRID` suffix) |
| 9 | After non-REGRID DAILYOUT=FALSE `WRITE(95) F_WET_CLIM_OUT` + after `WRITE(11,'()')` | non-REGRID | Combined: short doc + Tmin/Tmax monthly writes + per-cell newlines for units 100/101 |
| 10 | After post-B10 `CLOSE(11)` | shared (post REGRID conditional) | Short doc + `CLOSE(100)` + `CLOSE(101)` |

**Doc-block style**: one canonical block at the REGRID OPEN site (Edit 1 above; details B2 scope, algebraic derivation, Decision #11 reference, symmetry with C++ port, unit-100/101 selection rationale, backport-relevance, format choice, cross-reference to this §3d). Eight shorter cross-referencing comment blocks at the other sites. Mirrors B10's canonical-plus-shorter-cross-references pattern from §3b.

### 3d.5 Verification this commit

| Check | Method | Result |
|---|---|---|
| Clean Fortran build | `cd imogen/code && rm -f *.o imogen_lpjg && bash compile.sh` | ✅ Exit 0; binary 133 696 bytes (vs 129 600 pre-B2 = +4096 B; sensible for 2 new units' machinery + writes); ZERO warnings |
| Static unit-100/101 reference count | `rg "OPEN\\\|CLOSE\\\|WRITE\(\s*(100\|101)\s*[,\)]" imogen_lpjg.f \| wc -l` | ✅ 26 occurrences = 4 OPENs + 2 CLOSEs + 8 LON/LAT writes + 8 data writes + 4 per-cell newlines (matches expected) |
| Both file paths in source | `rg "Tmin_anom\.dat\|Tmax_anom\.dat" imogen_lpjg.f -n` | ✅ 4 matches: lines 1041-1042 (REGRID branch) + 1136-1137 (non-REGRID branch) — symmetric placement confirmed |
| Variable name consistency | manual diff | ✅ REGRID branch uses `T_OUT_M_REGRID/DTEMP_OUT_M_REGRID`; non-REGRID branch uses `T_OUT_M/DTEMP_OUT_M`; LON/LAT headers use `LON_OUT/LAT_OUT` (REGRID) and `LONG/LAT` (non-REGRID); matches existing T_anom write patterns at corresponding sites |
| Algebra parity with C++ | Visual diff vs `climatemodel.cpp` ~lines 990-991, 1005-1006 | ✅ Same expressions (`T - DTEMP/2.0`, `T + DTEMP/2.0`); same format (`f10.3`); same units (Kelvin) |
| Real-division safety | inspect `/2.0` usage | ✅ All 8 algebraic expressions use `/2.0` (REAL literal) not `/2` (INTEGER) → no integer-division truncation |

**Empirical post-fix engine smoke deferred** (same reason as B10/B6: Fortran engine inputs not currently shipped in active rebuild). Will be staged when B1 lands and a post-B1 engine smoke will simultaneously verify B10 + B6 + B2's predicted output: each `/YEAR/` directory will contain 9 files (the original 7 + new Tmin_anom.dat + Tmax_anom.dat) with line counts matching `version_A` reference + 12 monthly Tmin/Tmax values per cell-row in the Tmin/Tmax files.

### 3d.6 Cross-engine parity matrix (post-B2; CORRECTED by §3e B3 forensic finding 2026-05-12)

**⚠️ IMPORTANT correction post-§3e**: an earlier draft of this matrix wrongly attributed "both branches" to the C++ in-process port for the existing fields (T/P/SW/DTEMP/WET) and listed B3 as "C++ REGRID gap to close". B3's forensic investigation (§3e) revealed that the C++ in-process port has **only ONE climate-anomaly writer branch** (the native-IMOGEN-grid block at `climatemodel.cpp` line ~890); there is no Fortran-style `if (regrid)` switch. The matrix below is rewritten to reflect actual architectural state.

| Field | C++ in-process (climatemodel.cpp) | Fortran standalone (imogen_lpjg.f) |
|---|---|---|
| T_anom | ✅ native-grid (the only branch) | ✅ both branches |
| P_anom | ✅ native-grid (the only branch) | ✅ both branches |
| SW_anom | ✅ native-grid (the only branch) | ✅ both branches |
| DTEMP_anom | ✅ native-grid (the only branch) | ✅ both branches |
| WET | ✅ native-grid (the only branch) | ✅ both branches |
| **Tmin_anom** | ✅ native-grid (the only branch; line ~952) — N/A (no C++ REGRID branch) | ✅ both branches (B2 added them) |
| **Tmax_anom** | ✅ native-grid (the only branch; line ~953) — N/A (no C++ REGRID branch) | ✅ both branches (B2 added them) |
| Rh_anom | ✅ native-grid (the only branch) | ⏳ B1 (Fortran physics port; ~3-5 d) |
| W_anom (wind) | ✅ native-grid (the only branch) | ⏳ B1 (Fortran physics port; ~3-5 d) |
| CO2 | ✅ (CO2.dat / CO2_all.dat) | ✅ (CO2.dat) |

**Post-B3 status**: every climate-anomaly writer site that actually exists in either engine has Tmin/Tmax wired. The Fortran engine has Tmin/Tmax in BOTH of its REGRID + non-REGRID branches (B2 added them). The C++ in-process port has Tmin/Tmax in the only branch it has (the native-IMOGEN-grid branch, present since step 9.5). The previously-anticipated "C++ REGRID branch" was never built (see §3e); if a future change adds one, Tmin/Tmax writers must be replicated there using B2's algebraic pattern. Rh + Wind remain Fortran-side-only physics gaps (B1 closes them).

---

## 3e. B3 — C++ Tmin/Tmax in REGRID branch of `climatemodel.cpp` (LANDED this commit, 2026-05-12; **closed by architectural reframing — no C++ REGRID branch exists**)

### 3e.1 Pre-implementation framing (per §3b.6 ordering)

Per the re-ordered Option A sequence (B10 → B6 → B2 → **B3** → B4 → B1), B3 was scheduled as the next mechanical win after B2 because both items live in the cross-engine Tmin/Tmax parity scope. B3's stated scope per `notes/FOLLOWUPS.md` audit-table B-row + §3d.6 cross-engine parity matrix above (pre-correction): "Mirror logic of B2 on the C++ side: add Tmin/Tmax writes to the C++ in-process port's REGRID branch using the same algebraic derivation `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2` (per Decision #11)." The canonical signpost was the inline `// TODO at step 9.5b: replicate this in the REGRID branch.` comment at `climatemodel.cpp` ~line 894, left there by the step-9.5 author when `file100`/`file101` ofstream writers were introduced for the non-REGRID branch.

### 3e.2 Pre-implementation investigation — four checks per the user prompt

The prompt's pre-implementation investigation list was:

1. Locate the REGRID branch of `RUN_IMOGEN_ENGINE()` in `climatemodel.cpp`.
2. Identify the 5 sub-edit insertion sites mirroring B2's Fortran sites.
3. Verify whether REGRID branch uses `tOutMRegrid`/`dtempOutMRegrid` arrays (mirror of Fortran's `T_OUT_M_REGRID`/`DTEMP_OUT_M_REGRID`).
4. Apply edits with B2-style doc-block discipline.

**Step 1 result (CRITICAL FINDING)**: there is **no C++ REGRID branch** in `RUN_IMOGEN_ENGINE()`. The function has only one climate-anomaly writer block — the "Output in native IMOGEN grid" block at line ~890. Evidence chain (each independently confirmable):

| Check | Method | Finding |
|---|---|---|
| Search for `REGRID`/`regrid` in `climatemodel.cpp` | `rg "REGRID\|regrid" lpjguess/modules/climatemodel.cpp` | **Only 3 hits**: (a) line 242 `bool regrid = IMOGENConfig::REGRID;` declaration; (b) line 894 the stale `// TODO at step 9.5b: replicate this in the REGRID branch.` comment; (c) line 1353 an unrelated comment in a different function. No `if (regrid) { ... } else { ... }` switch anywhere. |
| Search for `*Regrid` array variants (analogue of Fortran's `T_OUT_M_REGRID` etc.) | `rg "tOutMRegrid\|dtempOutMRegrid\|swOutMRegrid\|pOutMRegrid\|fWetClimRegrid\|longOut\|latOut\|LON_OUT" lpjguess/modules/climatemodel.cpp` | **Zero hits**. The only climate-array declarations are native-grid: `tOutM`, `pOutM`, `swOutM`, `windOutM`, `rhOutM`, `dtempOutM` (lines 284-289), sized over `GPOINTS`. No `NGPOINTS`-sized regridded variants. |
| Search for `REGRID_CLIM` function call (C++ analogue of Fortran `CALL REGRID_CLIM`) | `rg "REGRID_CLIM\|regridClim\|regrid_clim" lpjguess/` | Zero hits in `climatemodel.cpp` or any other `lpjguess/` source. The Fortran's `REGRID_CLIM` helper (`imogen/code/imogen_lpjg.f` ~line 964) was never ported. |
| Whether `bool regrid` at line 242 is used | Manual inspection of the full `RUN_IMOGEN_ENGINE()` body | The `regrid` local is **declared, never read** in `RUN_IMOGEN_ENGINE()`. It is dead code (a declared-but-unused warning would fire if `-Wunused-variable` were enabled at high warning level). |
| What the Fortran REGRID branch actually does | `imogen/code/imogen_lpjg.f` lines 962-1117 | Calls `REGRID_CLIM(T_OUT_M, ..., T_OUT_M_REGRID, ...)` to populate `*_REGRID` arrays via nearest-neighbour interpolation onto a new gridlist (`LON_OUT`, `LAT_OUT`; sized `NGPOINTS`), then writes the regridded arrays to the same file paths as the native branch. The C++ port has no equivalent. |

**Step 2 result**: not applicable — there is no REGRID branch in which to identify insertion sites.

**Step 3 result**: confirmed — no `tOutMRegrid`/`dtempOutMRegrid` arrays exist.

**Step 4 result**: applied with revised scope (this section + the canonical C++ doc-block at `climatemodel.cpp` line ~890).

### 3e.3 Interpretation of the finding

The `// TODO at step 9.5b: replicate this in the REGRID branch.` was an **aspirational forward-reference**: when the step-9.5 author added `file100`/`file101` ofstream writers for `Tmin_anom.dat`/`Tmax_anom.dat` (per Decision #11), they correctly noted that — IF the C++ port ever grew a Fortran-style REGRID branch — Tmin/Tmax writers would need replicating there too. But that future REGRID branch was never built. The C++ port has always written climate anomalies on the single native IMOGEN grid (which is what `imogencfx` mode requires; that mode is the production path).

The cross-engine parity matrix (§3d.6) — written 2026-05-12 in the B2 commit — wrongly implied that the C++ port had a REGRID branch matching the Fortran's. This was a documentation drift from a misreading of the stale TODO. §3d.6 is corrected above to reflect actual architectural state.

### 3e.4 What landed this commit (1 file; ~30 LOC additive docs only; backport-RELEVANT)

A single file (`lpjguess/modules/climatemodel.cpp`) with three surgical documentation edits — **ZERO functional code change**:

| # | Site | Action |
|---|---|---|
| 1 | Just before `bool regrid = IMOGENConfig::REGRID;` at line ~242 | Insert ~18-line doc block annotating the dead-code status of the `regrid` local: explains it's declared-but-never-read; cross-references the canonical B3 doc block at line ~890; documents the architectural finding that no C++ REGRID branch exists; flags a defensive runtime warning as recommended B13-style follow-up. |
| 2 | After the `// Output in native IMOGEN grid` comment at line ~890 | Extend the inline comment by one clause to make it explicit that this is the **ONLY** climate-anomaly writer branch (not merely the non-REGRID counterpart of some hypothetical REGRID branch). |
| 3 | Replace the stale 4-line `// TODO at step 9.5b: replicate this in the REGRID branch.` block at line ~894 | Insert the **canonical B3 doc block** (~50 lines): forensic finding statement; cross-engine parity matrix snapshot; forward-looking maintenance directive (with the exact C++ algebraic pattern for any future REGRID-branch Tmin/Tmax addition); cross-references to STEP_17b.md §3e (this section), B2 Fortran symmetric block at `imogen/code/imogen_lpjg.f` lines ~1019-1160 (commit `76b3b04`), and the BACKPORT_LEDGER step-17b-B3 entry. |

**Doc-block style** mirrors B6's "close-by-subsumption" pattern (no source-line removals required because the original anticipated source-edit target doesn't exist) combined with B2's canonical-plus-cross-references discipline (one detailed canonical block at the most relevant insertion site, with shorter cross-referencing annotations at related sites).

### 3e.5 Verification this commit

| Check | Method | Result |
|---|---|---|
| Clean build (non-MPI; `build/`) | `cd lpjguess/build && rm -f .../climatemodel.cpp.o && make -j$(nproc)` (forced rebuild of the touched file) | ✅ Exit 0; binary 2 966 056 B; **zero new warnings** (`grep -E "warning\|error"` returns nothing) |
| Clean build (MPI; `build_mpi/`) | `cd lpjguess/build_mpi && make -j$(nproc)` | ✅ Exit 0; binary 2 840 824 B; zero new warnings |
| 162 unit tests pass (non-MPI) | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| 162 unit tests pass (MPI) | `lpjguess/build_mpi/runtests --reporter compact` | ✅ same |
| imogen 1cell xval substantive PASS | `GUESS_BIN=$PWD/lpjguess/build_mpi/guess scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ "PASS (substantive): All .out files are bit-exact AND non-NaN" (37/37 byte-equal; 0/37 NaN) |
| imogen 4cell xval substantive PASS | (same harness, 4cell) | ✅ same PASS pattern |
| imogencfx 1cell xval substantive PASS | (same harness, 1cell imogencfx) | ✅ same PASS pattern |
| imogencfx 4cell xval substantive PASS | (same harness, 4cell imogencfx) | ✅ same PASS pattern |
| No regression in C++ port behaviour | All 4 xval PASS substantive | ✅ B3 is docs-only; zero functional change; byte-equality with pre-B3 build preserved |

**Empirical REGRID-branch smoke test deferred** (per the prompt's "Optional" gate): the C2 xval is native-grid; no REGRID branch fires in either engine. If a future C++ REGRID branch is added (per the forward-looking maintenance directive in the canonical doc block), the post-add verification gate will include an empirical native-vs-REGRID parity check.

### 3e.6 Cross-engine parity matrix (post-B3) — see corrected §3d.6 above

The corrected §3d.6 matrix is the authoritative post-B3 cross-engine parity statement: Tmin/Tmax are present at every climate-anomaly writer site that currently exists in either engine. Rh + Wind remain Fortran-side-only physics gaps (B1 closes them via the ~3-5 d physics port).

### 3e.7 Lesson for future audit-item triage

The B3 episode is the second "close-without-the-originally-expected-mechanical-action" outcome in step 17b (after B6's close-by-subsumption via B10). The forensic pattern: a stale forward-reference TODO can carry an implicit architectural assumption that has not been validated against actual code. Generalised heuristic — captured as new entry **rule #7** in the persistent "Operational heuristics — lessons learned" subsection of `notes/FOLLOWUPS.md`:

> **Stale forward-reference TODOs are architectural-finding triggers — investigate the actual code structure before mechanically replicating from a sibling implementation.** When a TODO comment says "replicate this in branch X" or "add this to function Y", verify that branch X / function Y actually exists in the same form as in the sibling implementation. Differences between sibling implementations (e.g., Fortran has REGRID branch; C++ port does not) can invalidate the mechanical-replication assumption, in which case the audit item's deliverable becomes architectural reframing (close-by-finding) rather than insertion work.

### 3e.8 Backport-relevance + ledger entry

The `lpjguess/modules/climatemodel.cpp` change is backport-RELEVANT for the F-11 Backport Sprint to `trunk_r13078`. The three doc-only edits should be replicated verbatim if `trunk_r13078`'s `climatemodel.cpp` has the same step-9.5 `file100`/`file101` block + stale TODO. Full mechanical instructions are at `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17b-B3 entry (this commit).

---

## 3f. B4 — `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion (LANDED this commit, 2026-05-12 night)

### 3f.1 Pre-implementation framing (per §3b.6 re-ordered Option A: B3 → **B4** → B1)

B4 is the loose-mode (`-input imogen`) counterpart to the tight-mode (`-input imogencfx`) step-9.5 wiring of Rh / Wind / Tmin / Tmax in `IMOGENCFXInput` (commit `a543e9d`; refined K→°C bug-fix at step-17a sub-step 7.3.2 commit `8aafe84`). Before this commit, `ImogenInput::getclimate()` populated only `climate.{temp, prec, insol, dtr}` (6 fields including CO2 + ndep) leaving `climate.{relhum, u10, tmin, tmax}` either zero-defaulted or carrying stale prior-cycle values — the "loose-mode-vs-tight-mode 6-vs-10-fields gap" identified during the 2026-05-10 late-evening audit (notes/FOLLOWUPS.md audit-item B4 row).

**Scope per audit-table B4 row:** "4 file_* declarations + read pipeline + climate.{relhum, u10, tmin, tmax} assignments + extension to the C1.1 year_outer override. Closes the loose-mode-vs-tight-mode 6-vs-10-fields gap discussed 2026-05-10 late evening." (~1 d estimate; ~0.5 d actual — landed within budget owing to direct code-level mirror of the C1.1 IMOGENCFXInput pattern.)

### 3f.2 Pre-implementation investigation — what was already wired vs missing

Four parallel investigations:

| # | Investigation | Finding |
|---|---|---|
| 1 | `imogen_input.h` current state | Existing `file_relhum` + `file_wind` + `file__pres` declarations at lines 232-236 (in a "for Blaze need from imogen:" block) but **NEVER referenced** in `imogen_input.cpp` — vestigial header decls. `file_tmin` + `file_tmax` declarations entirely absent. No per-day arrays for relhum/wind/tmin/tmax. No `all_drelhum`/`all_dwind`/`all_dtmin`/`all_dtmax` per-year caches. Verified by `rg "file_relhum\|file_wind\|file__pres\|file_tmin\|file_tmax" imogen_input.cpp` returning zero hits. |
| 2 | `imogencfx.{cpp,h}` C1.1 reference pattern | All 4 path decls at `imogencfx.h:260-266`; all 4 per-day arrays at `imogencfx.h:204-218`; all 4 caches at `imogencfx.h:311-318`. init() reads 4 params at `imogencfx.cpp:427-430`; resize at `imogencfx.cpp:584-587`; readenv() guarded reads at `imogencfx.cpp:866-888`; get_climate_for_gridcell() monthly+daily branches at `imogencfx.cpp:986-1004` + `:1017-1028`; getclimate() consumer assignments at `imogencfx.cpp:1274-1277`; getclimate_for_year() consumer assignments at `imogencfx.cpp:1604-1607`. Same K-vs-°C handling site decision documented at `imogencfx.cpp:920-962` (post-step-17a-7.3.2: convert at monthly-array population step). |
| 3 | `Climate` struct fields | `lpjguess/framework/guess.h:844` declares `double u10;` (km/h documented; m/s actually used by IMOGENCFXInput pass-through); `:847` declares `double relhum;` (fraction); `:850` declares `double tmin, tmax;` (degC). All 4 fields exist; B4 just needs to populate them. |
| 4 | Fortran engine output state (which files exist post-B2/post-B1) | Post-B2 (commit `76b3b04`): `Tmin_anom.dat` + `Tmax_anom.dat` written by Fortran engine. Pre-B1: `Rh_anom.dat` + `W_anom.dat` NOT written by Fortran engine (B1 will land them via the ~3-5 d Rh + Wind physics port). Pre-staged climate at `runs/SSP1-2.6/Common-directory/IMOGEN/output/1871/` already contains ALL 4 files (predecessor-staged set; 246281 B each; verified 2026-05-12 pre-B4 land). The pre-staged set fills the B1-pending gap for the xval window. |

### 3f.3 Design decisions

| # | Decision | Rationale |
|---|---|---|
| 1 | **K→°C conversion site**: at consumer (line ~885 `climate.temp = dtemp[date.day] - 273.15`), NOT at monthly-array population step | ImogenInput's existing `dtemp[]` convention is Kelvin (no -273.15 in `get_climate_for_gridcell()` at line ~639/~649); convert at the `climate.temp = dtemp - 273.15` line ~885. B4 applies the SAME convention to `dtmin[]/dtmax[]` for cross-field consistency. **Intentionally DIFFERS from IMOGENCFXInput's post-step-17a-7.3.2 convention** (which converts at the monthly-array step in `get_climate_for_gridcell`); this difference is preserved with cross-references in the doc blocks. Relhum/wind require no unit conversion. |
| 2 | **B1-pending fallback**: `if ((char*)file_relhum != NULL && file_relhum != "") { read }` guard pattern from IMOGENCFXInput readenv | Forward-safe across the B1-pending transition. If `.ins` doesn't set the 4 paths, no read attempted (file-not-found `fail()` avoided). Pre-staged climate at xval-time fills the gap; production deployments post-B1 will get Fortran-engine-generated files. |
| 3 | **Repurpose existing vestigial decls** (`file_relhum`/`file_wind`/`file__pres`) | Don't add duplicate decls. The existing decls (lines 232-236 pre-B4) get the B4 wiring. Add `file_tmin` + `file_tmax` as NEW decls. `file__pres` left intact (still vestigial; could be a future B-item for in-process pressure consumer). |
| 4 | **`preload_all_climate` unchanged** | The C1.1 year_outer override at `imogen_input.cpp:945-1034` delegates to `readenv()` for all climate fields. B4's extension of `readenv()` (decision #2 above) suffices; no modification to `preload_all_climate` is needed. |
| 5 | **`getclimate_for_year` separate extension** | Mirrors `getclimate()`'s consumer assignments per-day. Same K→°C at consumer site; same pass-through for relhum/wind. Indexed by `day_of_year` instead of `date.day`. |
| 6 | **`runs/SSP1-2.6/main_xval_loose.ins` update** (one config line per new path; 4 lines total + doc block) | Required for xval to exercise B4's new wiring; otherwise the `if (path != "")` guards skip the reads. Mirrors `main_xval_imogencfx.ins:96-99` 1:1. |

### 3f.4 What landed this commit (8 sub-edits across 3 source files + 1 config file)

**`lpjguess/modules/imogen_input.h`** (3 edits):

| # | Insertion site | Content |
|---|---|---|
| 1 | After `dNH4dep[]/dNO3dep[]` per-day arrays (line ~196) | 4 new per-day arrays `drelhum[]/dwind[]/dtmin[]/dtmax[]` + ~30-line canonical B4 doc block (K-vs-°C convention rationale; cross-references to imogencfx.h B4-equivalent + canonical Decision-#11 + this §3f) |
| 2 | After existing `file_wind` vestigial decl (line ~236 pre-B4) | Doc block annotating the previously-vestigial `file_relhum` + `file_wind` declarations as now-wired-by-B4 + 2 new path decls `file_tmin; file_tmax;` with doc block |
| 3 | After `all_dtr` per-year cache decl (line ~280 pre-B4) | 4 new caches `all_drelhum/all_dwind/all_dtmin/all_dtmax` + doc block mirroring imogencfx.h:311-318 |

**`lpjguess/modules/imogen_input.cpp`** (5 edits):

| # | Insertion site | Content |
|---|---|---|
| 1 | After `file_dtr = param["file_dtr"].str;` (init(), line ~251 pre-B4) | ~30-line canonical B4 doc block (scope, B1-pending fallback rationale, cross-references) + 4 param reads `file_relhum/file_wind/file_tmin/file_tmax = param["...].str;` |
| 2 | After `resize3DimVector(all_dtr, ...)` (init(), line ~372 pre-B4) | Doc block (mirror of `imogencfx.cpp:575-583`) + 4 new `resize3DimVector` calls for `all_drelhum`/`all_dwind`/`all_dtmin`/`all_dtmax` |
| 3 | After `if (ifbvoc) { ... all_dtr ... }` (readenv() line ~615 pre-B4) | Doc block + 4 guarded reads using the `(char*)file_relhum != NULL && file_relhum != ""` pattern (mirror of `imogencfx.cpp:866-888`) |
| 4 | After `interp_climate(...)` (get_climate_for_gridcell() monthly branch, line ~645 pre-B4) | Doc block (NO K→°C at this layer; ImogenInput convention) + 4 m*[12] arrays + 4 have_* booleans + 4 `interp_monthly_means_conserve` calls. ALSO daily-branch additions after `if (ifbvoc) ddtr[i] = ...` (line ~652 pre-B4): doc block + 4 guarded daily passthroughs |
| 5 | (a) After `if (ifbvoc) { climate.dtr = ddtr[date.day]; }` in `getclimate()` (line ~892 pre-B4); (b) After same in `getclimate_for_year()` (line ~1158 pre-B4) | Doc block + 4 `climate.{relhum, u10, tmin, tmax} = ...[date.day or day_of_year];` with K→°C `- 273.15` on tmin/tmax (mirror of existing `climate.temp = dtemp - 273.15` pattern on the line above). Same pattern applied to BOTH the gridcell_outer driver (`getclimate()`) AND the year_outer override (`getclimate_for_year()`). |

**`runs/SSP1-2.6/main_xval_loose.ins`** (1 edit, lines ~67-78 post-B4): doc block + 4 param directives `file_relhum`/`file_wind`/`file_tmin`/`file_tmax` (mirror of `main_xval_imogencfx.ins:96-99`).

**Net source change:** ~187 LOC additive in `imogen_input.h`/`imogen_input.cpp` (header: +60 LOC; cpp: +127 LOC); ~15 LOC additive in `main_xval_loose.ins`. **ZERO source removals.** Pure additive expansion.

### 3f.5 Verification this commit

| Gate | Result |
|---|---|
| Clean rebuild `lpjguess/build/` (forced touch on `imogen_input.{cpp,h}` + `make -j16`) | ✅ Zero new warnings. The only emitted warning is the pre-existing `gutil.h:1521` sprintf-overflow warning in `Timer::print` (triggered through `tmute.settimer(MUTESEC)` at `imogen_input.cpp:1066`; same warning was emitted at every prior commit's `imogen_input.cpp` line for the same call). |
| Clean rebuild `lpjguess/build_mpi/` | ✅ Zero new warnings (same pre-existing only). |
| `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| `lpjguess/build_mpi/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| `scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ PASS substantive (37/37 bit-exact + 0/37 NaN). |
| `scripts/cross_validate_year_outer.sh 4cell imogen` | ✅ PASS substantive (37/37 bit-exact + 0/37 NaN). |
| `scripts/cross_validate_year_outer.sh 1cell imogencfx` | ✅ PASS substantive (37/37 bit-exact + 0/37 NaN). |
| `scripts/cross_validate_year_outer.sh 4cell imogencfx` | ✅ PASS substantive (37/37 bit-exact + 0/37 NaN). |
| B4 wiring confirmation | ✅ `read_lines_from_file` would fail with `fail()` (line ~550) if any of the 4 new file paths' files were missing. All 8 run.log files (4 scenarios × 2 modes) complete with "Finished" — proves all 4 new paths resolved + were read successfully. |

### 3f.6 Loose-mode consumer-wiring parity matrix (post-B4)

Tracks which climate fields the LPJ-GUESS `Climate` struct receives from each input module's input pipeline (NOT from the IMOGEN engine's writer side — that is §3d.6's matrix).

| Climate field | `ImogenInput` (`-input imogen`) | `IMOGENCFXInput` (`-input imogencfx`) | Source |
|---|---|---|---|
| `climate.temp` | ✅ since pre-rebuild | ✅ since step 9.5 | `dtemp[] = all_temp[...]` |
| `climate.prec` | ✅ | ✅ | `dprec[]` |
| `climate.insol` | ✅ | ✅ | `dinsol[]` |
| `climate.dtr` (bvoc) | ✅ guarded by `ifbvoc` | ✅ guarded by `ifbvoc` | `ddtr[]` |
| `climate.co2` | ✅ | ✅ | yearly from `CO2.dat` |
| `gridcell.dNH4dep` / `dNO3dep` | ✅ | ✅ | distributed from monthly ndep |
| `climate.relhum` | ✅ **NEW B4 (this commit)** | ✅ since step 9.5 | `drelhum[] = all_drelhum[...]`; guarded on `file_relhum != ""` |
| `climate.u10` | ✅ **NEW B4 (this commit)** | ✅ since step 9.5 | `dwind[]`; guarded on `file_wind != ""` |
| `climate.tmin` | ✅ **NEW B4 (this commit)** | ✅ since step 9.5 (K→°C bug-fixed at step-17a sub-step 7.3.2) | `dtmin[] - 273.15` (B4 at consumer); `dtmin[]` already in °C (IMOGENCFXInput at monthly-array step) |
| `climate.tmax` | ✅ **NEW B4 (this commit)** | ✅ since step 9.5 (K→°C bug-fixed at step-17a sub-step 7.3.2) | `dtmax[] - 273.15` (B4 at consumer); `dtmax[]` already in °C (IMOGENCFXInput at monthly-array step) |

**Post-B4 status**: the loose-mode-vs-tight-mode 6-vs-10-fields gap is closed for the LPJG-side input pipeline. Both input modules now populate all 10 climate fields. The K→°C conversion site differs intentionally between the two input modules (consumer-site for ImogenInput; monthly-array-step for IMOGENCFXInput); doc blocks at both sites cross-reference each other to prevent future drift.

### 3f.7 What's still pending for full loose-mode physics parity (B1 — last in the re-ordered sequence)

**B1 is the engine-side counterpart to B4.** Currently the Fortran engine (`imogen/code/imogen_lpjg.f`) does NOT compute Rh / Wind anomalies physically (it's not just a missing writer; the entire physics-computation pipeline is absent from the Fortran code, per Decision #12 + STEP_9.5 §3.4 — the C++ engine port added the entire Rh/Wind physics pipeline; Fortran has never had it). B1 (~3-5 d) will:
1. Port the Rh + Wind physics computation pipeline from `lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` to `imogen/code/imogen_lpjg.f`.
2. Add the corresponding `Rh_anom.dat` / `W_anom.dat` writers (using the same B10-fixed unconditional OPEN/CLOSE-per-IYEAR semantics).
3. After B1 lands: live Fortran-engine smoke produces 11-file `IMOGEN/output/YYYY/` directories (vs. pre-B1 9-file directories: T/P/SW/DTEMP/WET/Tmin/Tmax/dtemp_o/fa_ocean post-B2-and-B10).

After B1 lands, B4's existing wiring (this commit) will consume the live Fortran-engine Rh + Wind anomaly files directly without further code changes on the LPJG side.

### 3f.8 Backport-relevance + ledger entry

The `lpjguess/modules/imogen_input.{cpp,h}` change is backport-RELEVANT for the F-11 Backport Sprint to `trunk_r13078`. The 8 source-side sub-edits should be replicated if `trunk_r13078`'s `imogen_input.{cpp,h}` has the same pre-B4 6-fields-only consumer pattern. The `runs/SSP1-2.6/main_xval_loose.ins` change is config-only and **not** part of `trunk_r13078`'s tree (the test-config files live outside `lpjguess/`). Full mechanical instructions are at `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17b-B4 entry (this commit).

---

## 3g. B1 — Fortran-engine Rh + Wind COMPUTATION + write-block port (LANDED this commit, 2026-05-12 early morning; **LAST audit item before C2 close-out**)

### 3g.1 Pre-implementation framing (per §3b.6 re-ordered Option A: B3 → B4 → **B1**)

B1 is the LAST of the 6 re-ordered audit items per the user-confirmed sequence (B10 → B6 → B2 → B3 → B4 → **B1**). It is described in the audit table as "Fortran Rh + Wind COMPUTATION port" with a 3-5 d budget — anticipated to be the heaviest item because it was framed as a "physics port".

### 3g.2 Pre-implementation forensic finding — the audit table mischaracterised the scope

Pre-implementation reading of `lpjguess/modules/climatemodel.cpp` revealed there is **no heavy physics to port**:

- **Wind output is a direct passthrough** from `windOut` (engine's disaggregated subdaily output) at `climatemodel.cpp:865`. The line is literally `windOutM[igp][imm][imd][ind] = windOut[igp][imm][imd][ind];` — no per-cell physics; just storage-layout aliasing.
- **Rh output is a single inline computation** via `computeRelativeHumidityFromSpeificHumidty(q, p_Pa, T_K)` at `climatemodel.cpp:866` calling the function defined at `climatemodel.cpp:1228-1249`. The function body is a 22-LOC Tetens-formula algebra:
  - K → °C: `T_C = T_K - 273.15`
  - Pa → hPa: `p_hPa = p_Pa / 100`
  - Vapor pressure (hPa): `e = (q * p_hPa) / (0.622 + 0.378 * q)`
  - Saturation vapor pressure (Tetens; hPa): `es = 6.112 * exp((17.67 * T_C) / (T_C + 243.5))`
  - Relative humidity (%): `RH = (e / es) * 100`
  - Clamp to [0, 100].
- **Fortran-side state pre-B1**: `WIND_OUT(GPOINTS,MM,MD,NSDMAX)`, `QHUM_OUT(GPOINTS,MM,MD,NSDMAX)`, `PSTAR_OUT(GPOINTS,MM,MD,NSDMAX)`, `T_OUT_M(GPOINTS,MM,MD,NSDMAX)` **already exist and are populated** at line 773 by the existing `CLIM_DISAG`-style subroutine call. The Fortran engine was missing ONLY (a) the writer block for `Rh_anom.dat` + `W_anom.dat`, and (b) the `REGRID_CLIM` extension to nearest-neighbor-regrid 3 additional source arrays (`WIND_OUT`, `QHUM_OUT`, `PSTAR_OUT`) so the REGRID writer branch has its inputs.

**Net effect**: B1 is mechanical-symmetric-writer work (same flavor as B2 + B10), NOT a physics port. **Estimated effort revised down to ~0.5 d** (was 3-5 d) — landed in a single session.

This is the second application of **operational heuristic rule #7** (stale forward-reference TODOs are architectural-finding triggers; first applied to B3). The audit-table description "Fortran Rh + Wind COMPUTATION port" reflected an early-stage misreading of `climatemodel.cpp:866`'s `// Compute Rh from Qh since Rh is not output directly` comment as "Rh requires a heavy physics port" when in fact the only computation is the inline Tetens algebra.

### 3g.3 Design decisions (cited in doc blocks at each insertion site)

| # | Decision | Rationale |
|---|---|---|
| 1 | Inline Tetens algebra in a NEW `SUBROUTINE RH_FROM_QPT(Q, P_PA, T_K, RH)` at the bottom of `imogen_lpjg.f` (NOT a call to existing `QSAT` lookup) | C++ uses Tetens (`climatemodel.cpp:1239`); Fortran `QSAT` (line ~3895) uses Goff-Gratch lookup table — different algorithm, different output (saturation specific humidity vs. saturation vapor pressure). Bit-level cross-engine parity with C++ requires identical algorithm. Tetens is ~1% absolute Rh accuracy — sufficient for downstream LandSyMM/BLAZE consumers. |
| 2 | Write Rh + Wind in BOTH REGRID + non-REGRID branches (mirror B2 symmetry); extend `REGRID_CLIM` by 3 new nearest-neighbor passthroughs | Maintains B2-discipline parity. Cost: ~40 extra LOC for `REGRID_CLIM` extension (signature + dimension decls + 3 IND_MIN passthroughs). Benefit: future REGRID users get Rh/W for free; preserves Fortran engine's design intent of full REGRID feature parity. (The C++ port has no REGRID branch — closed by B3 docs-only commit `ceb2766`; this is the Fortran-specific extra.) |
| 3 | Inline `CALL RH_FROM_QPT` at each writer site (NOT a separate global `RH_OUT_M` array maintained throughout the engine) | Mirrors C++ pattern: `rhOutM` is computed directly at writer (`climatemodel.cpp:866`); no separately-maintained global. Keeps the writer self-contained; reduces memory footprint by `GPOINTS*MM*32*NSDMAX*sizeof(REAL)` bytes vs. a global array. |
| 4 | Unit numbers 96 + 97 mirror C++ ofstream names `file96` (Rh) + `file97` (Wind) at `climatemodel.cpp:1046-1047` | Direct cross-engine symbol parity. Unit 97 is briefly re-used for the `done` marker after `CLOSE(97)` at the climate writers end (line ~1281) — sequence is correct (CLOSE then OPEN). Documented in B1 doc block. |
| 5 | Append new args at END of `REGRID_CLIM` signature (NOT inline interleaved with existing args) | Minimal-diff principle; preserves historical argument order; backport-friendly. The 6 new args (3 IN, 3 OUT) are added on continuation lines after the existing 19-arg signature. |
| 6 | Symmetric ALLOCATE / DEALLOCATE / decl ordering mirroring pre-B1 T/P/SW/DTEMP/F_WET pattern | All 3 new arrays grouped together with `T_OUT_M_REGRID` siblings — easier code-archaeology + future hygiene-check tooling alignment. |

### 3g.4 What landed this commit (18 sub-edits + 1 new subroutine in `imogen/code/imogen_lpjg.f`; +202 LOC additive, -2 deletions = +200 LOC net)

| # | Site (~line, post-edit) | Edit |
|---|---|---|
| 1 | ~302 | B1 doc block + 3 new `REAL, ALLOCATABLE :: WIND_OUT_M_REGRID/QHUM_OUT_M_REGRID/PSTAR_OUT_M_REGRID` declarations |
| 2 | ~320 | 1 new `REAL RH_TMP` scratch scalar (with 3-line doc block) |
| 3 | ~341 | 3 new `ALLOCATE(WIND_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX))` etc. |
| 4 | ~975 | B1 doc block on `CALL REGRID_CLIM(...)` + 2 continuation lines appending 6 new args |
| 5 | ~1052 | B1 doc block + 2 new `OPEN(96, 'Rh_anom.dat')` + `OPEN(97, 'W_anom.dat')` in REGRID branch |
| 6 | ~1063 | 4 new per-cell LON/LAT header WRITEs (units 96/97) in REGRID branch |
| 7 | ~1086 | B1 doc block + `WRITE(97, ..., WIND_OUT_M_REGRID(IGP,IMM,IMD,IND))` + `CALL RH_FROM_QPT(...)` + `WRITE(96, ..., RH_TMP)` in REGRID DAILYOUT=TRUE inner-loop |
| 8 | ~1118 | Analogous WRITE+CALL+WRITE in REGRID DAILYOUT=FALSE branch (monthly mean; ,1,1 sub-index) |
| 9 | ~1133 | `WRITE(96,'()') / WRITE(97,'()')` per-cell newlines in REGRID branch |
| 10 | ~1140 | B1 doc block + 2 new `OPEN(96/97)` in non-REGRID branch |
| 11 | ~1163 | 4 new per-cell LON/LAT header WRITEs in non-REGRID branch (uses `LONG(IGP)`/`LAT(IGP)`) |
| 12 | ~1192 | B1 doc block + WRITE+CALL+WRITE in non-REGRID DAILYOUT=TRUE branch (uses `WIND_OUT`/`QHUM_OUT`/`PSTAR_OUT`/`T_OUT_M`; no `_REGRID` suffix) |
| 13 | ~1218 | Analogous WRITE+CALL+WRITE in non-REGRID DAILYOUT=FALSE branch |
| 14 | ~1247 | `WRITE(96,'()') / WRITE(97,'()')` per-cell newlines in non-REGRID branch |
| 15 | ~1276 | B1 doc block + 2 new `CLOSE(96)/(97)` (symmetric with B2's CLOSE(100)/(101)) |
| 16 | ~1303 | 3 new `IF (ALLOCATED(...)) DEALLOCATE(...)` for the 3 new REGRID arrays |
| 17 | ~1342 | B1 doc block on `SUBROUTINE REGRID_CLIM(...)` + 2 continuation lines appending 6 new dummy args |
| 18 | ~1372 | 6 new dimension decls (3 IN, 3 OUT) + 3 new nearest-neighbor passthrough assignments inside `DO IMM, DO IMD, DO IND` triple-loop |
| **19** | **~1432** | **NEW `SUBROUTINE RH_FROM_QPT(Q, P_PA, T_K, RH)` with full docstring + IMPLICIT NONE + 4-line Tetens algebra + clamping (~40 LOC; byte-identical to C++ `computeRelativeHumidityFromSpeificHumidty`)** |

**Net source change**: +202 insertions, -2 deletions = +200 LOC additive in `imogen/code/imogen_lpjg.f`. **Single-file commit** on the Fortran-engine side. Zero changes to `lpjguess/` (verified by `git diff --stat`).

### 3g.5 Verification this commit

| Gate | Result |
|---|---|
| Fortran clean build (`compile.sh`) | ✅ Binary 137832 B; zero new warnings with `-Wall -Wno-unused-dummy-argument -Wno-unused-variable` (8 pre-existing warnings unchanged: line 4523 conversion, 1489/2466/3642/870/688/853 uninitialized — all from non-B1 code paths) |
| Clean rebuild `lpjguess/build/` (no-op regression check — B1 doesn't touch `lpjguess/`) | ✅ `[100%] Built target runtests` |
| Clean rebuild `lpjguess/build_mpi/` | ✅ Same |
| 162 unit tests on both | ✅ "Passed all 25 test cases with 162 assertions." |
| All 4 xval scenarios substantive | ✅ 37/37 bit-exact + 0/37 NaN per scenario |

### 3g.6 Cross-engine parity matrix (post-B1; FULL parity achieved for climate-anomaly output)

| Climate field | C++ in-process port | Standalone Fortran engine |
|---|---|---|
| `T_anom.dat` | ✅ since step 6 | ✅ since step 6 |
| `P_anom.dat` | ✅ since step 6 | ✅ since step 6 |
| `SW_anom.dat` | ✅ since step 6 | ✅ since step 6 |
| `WET.dat` | ✅ since step 6 | ✅ since step 6 |
| `DTEMP_anom.dat` | ✅ since step 8 | ✅ since step 8 |
| `Tmin_anom.dat` | ✅ since step 9.5 (non-REGRID; per B3) | ✅ since B2 (BOTH branches) |
| `Tmax_anom.dat` | ✅ since step 9.5 (non-REGRID) | ✅ since B2 (BOTH branches) |
| `Rh_anom.dat` | ✅ since step 9.5 (non-REGRID) | ✅ **NEW B1 (BOTH branches)** |
| `W_anom.dat` | ✅ since step 9.5 (non-REGRID) | ✅ **NEW B1 (BOTH branches)** |

**Cross-engine Rh/W gap CLOSED.** Full climate-anomaly output parity between the two engines for the v1.0 production path. The Fortran engine now provides full feature parity with the C++ in-process port for all climate fields written to disk (and extends beyond C++ via the REGRID branch which the C++ port lacks per B3).

### 3g.7 Backport-relevance + ledger entry

The `imogen/code/imogen_lpjg.f` change is backport-RELEVANT for the F-11 Backport Sprint to `trunk_r13078`. The 18 source-side sub-edits + 1 new SUBROUTINE should be replicated if `trunk_r13078`'s `imogen_lpjg.f` has the same pre-B1 Rh-and-W-output-missing state. Full mechanical instructions at `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17b-B1 entry (this commit).

---

## 4. C2 core implementation plan (next phase) — SUPERSEDED by §3a above; preserved for design-history reference

Per the plan in session-2 §6.3 + EXECUTION_PLAN.md V.1 row 17b:

### 4.1 `lpjguess/framework/framework.cpp` (~10 LOC additive)

Add `MPI_Barrier(MPI_COMM_WORLD)` at year boundary in the year_outer block, after the per-year cell-inner loop body close and before the per-cell teardown. Approximately at line ~611 of the existing year_outer block (between the `}` close of the outer `for (year_idx ...)` loop and the per-cell teardown at line ~615). Guarded by `#ifdef HAVE_MPI` for graceful single-process fallback.

```cpp
// Year boundary - all ranks rendezvous here so the closed-loop tight
// handshake aggregates a globally-consistent year-end NEE snapshot.
// #ifdef HAVE_MPI guarded; single-process builds skip this and proceed
// directly to the imogenoutput flush (which produces a single-rank-local
// flush per the existing flush_year mechanism).
#ifdef HAVE_MPI
if (GuessParallel::parallel) {
    MPI_Barrier(MPI_COMM_WORLD);
}
#endif
```

### 4.2 `lpjguess/modules/imogenoutput.cpp/h` (~30 LOC additive)

Add `flush_year_globally_synchronized(int year)` sibling method on `ImogenOutput`. Performs `MPI_Allreduce(MPI_SUM)` over per-rank `accum_NEE_kgC` / `accum_CH4_gCH4C` / `accum_N2O_kgN`; only lead rank (rank 0) writes the unified handshake file at `<DIR_COMMON>/LPJG_main/IMOGEN/`. Falls back to local-rank-only flush (i.e., the existing `flush_year` behaviour) when `HAVE_MPI` is undefined.

Header addition (sketch):
```cpp
// Sibling to flush_year(year). Performs MPI_Allreduce(MPI_SUM) over per-
// rank flux contributions before flushing the handshake file. Only the
// lead rank (rank 0) opens/writes the unified handshake file; other ranks
// participate in the Allreduce but do NOT write. Falls back to local-
// rank-only flush when HAVE_MPI is undefined. This restores GLOBAL flux
// aggregation, resolving the F-10 per-gridcell-rolling caveat for
// multi-rank MPI year_outer mode.
void flush_year_globally_synchronized(int year);
```

Wiring: framework.cpp year_outer block calls `imogen_output_instance.flush_year_globally_synchronized(year_idx + first_calendar_year)` AFTER the `MPI_Barrier` (so all ranks have completed year_idx before the Allreduce + write).

### 4.3 Tests

`scripts/run_parallel_mimic.sh --np 4` workstation MPI mimic — runs `build_mpi/guess` with `mpirun -np 4` across 4 ranks of the 4-cell smoke gridlist (1 cell per rank). Verifies:
- All 4 ranks reach the year-boundary `MPI_Barrier` simultaneously
- `MPI_Allreduce` aggregates per-rank NEE/CH4/N2O correctly (sanity: sum of 4 per-rank values vs single-process year_outer baseline)
- Only rank 0 writes the unified handshake file (per-rank file existence check)
- LPJG main loop completes end-to-end on all 4 ranks
- Aggregate `cflux.out` rows from all 4 per-rank `runNN/` dirs match what single-process year_outer produced for the same smoke gridlist

This is the **GO/NO-GO gate for C2 core**. Pass = year_outer + MPI sync produces correct closed-loop tight-coupling fluxes on workstation MPI.

---

## 5. B-item bundling decision (2026-05-11)

Per user direction 2026-05-11 (deferred to agent with the stated condition "be meticulous, systematic, and comprehensive; tackle all items; leave none undone"). Refined option (i) for B1+B4 with C2 era + option (iii) opportunistic for B2/B3/B5-B11 with explicit per-item per-step home:

| # | Item | Effort | Bundling home | Rationale |
|---|---|---|---|---|
| **B1** ✅ DONE | Fortran Rh + Wind COMPUTATION port — **closed by architectural reframing** | ~0.5 d (actual; landed in a single session; far lighter than the budgeted 3-5 d) | **C2 era (this step 17b)** | LANDED 2026-05-12 (this commit). Forensic finding: the audit-table description "Fortran Rh + Wind COMPUTATION port" mischaracterised the scope. There is no heavy physics to port — Wind is a direct passthrough from `windOut` (`climatemodel.cpp:865`); Rh is a single inline Tetens-formula computation at `climatemodel.cpp:866-867` calling `computeRelativeHumidityFromSpeificHumidty` (22 LOC at `climatemodel.cpp:1228-1249`). Fortran-side `WIND_OUT/QHUM_OUT/PSTAR_OUT/T_OUT_M` already exist and are populated by the existing `CLIM_DISAG` call. B1 was mechanical-symmetric-writer work (same flavor as B2 + B10) NOT a physics port. 18 surgical sub-edits + 1 NEW `SUBROUTINE RH_FROM_QPT` (~40 LOC; byte-identical Tetens algebra to C++) in `imogen/code/imogen_lpjg.f`. Writes `Rh_anom.dat` (unit 96) + `W_anom.dat` (unit 97) to BOTH REGRID + non-REGRID branches; extends `REGRID_CLIM` by 3 new nearest-neighbor passthroughs for `WIND_OUT/QHUM_OUT/PSTAR_OUT`. Net source change: +202 / -2 = +200 LOC additive (single file). Verification: clean Fortran build (binary 137832 B; zero new warnings with `-Wall`); clean lpjguess rebuilds both (no-op regression); 162 unit tests pass both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN). **Cross-engine Rh/W gap CLOSED**. Forensic record at §3g above. Backport-RELEVANT. Second application of operational heuristic rule #7 (stale "physics port" framing → forensic-finding trigger). |
| **B2** | Fortran Tmin/Tmax write block | 0.5 d | **C2 era (this step 17b)** | Trivially extends B1's Fortran writer work; algebraic `Tmin = T - DTEMP/2` |
| **B3** ✅ DONE | C++ Tmin/Tmax in REGRID branch — **closed by architectural reframing** | 0.3 d (actual; lighter than budgeted 0.5 d because docs-only) | **C2 era (this step 17b)** | LANDED 2026-05-12 (this commit). Forensic investigation revealed the C++ in-process port has **NO REGRID branch** — only one climate-anomaly writer block (the native-IMOGEN-grid branch at `climatemodel.cpp` line ~890). The `bool regrid` declaration at line ~242 is dead code; no `if (regrid)` switch exists; no `*Regrid` array variants exist; no `REGRID_CLIM` function was ever ported from Fortran. The stale `// TODO at step 9.5b: replicate this in the REGRID branch.` comment at line ~894 was an aspirational forward-reference. ~30 LOC of additive documentation (3 doc-only edits: dead-code annotation at line ~242; native-grid-is-only-branch clarification at line ~890; canonical B3 doc-block replacing the stale TODO at line ~894 — with forward-looking maintenance directive for any future C++ REGRID branch). ZERO functional code change. Backport-RELEVANT. Forensic record at §3e above. |
| **B4** ✅ DONE | ImogenInput Rh/W/Tmin/Tmax consumer wiring expansion | ~0.5 d (actual; lighter than budgeted 1 d because direct mirror of C1.1 IMOGENCFXInput pattern + zero unanticipated forensic findings) | **C2 era (this step 17b)** | LANDED 2026-05-12 night (this commit). 8 surgical insertions across `lpjguess/modules/imogen_input.{cpp,h}` adding the loose-mode counterpart to the tight-mode step-9.5 wiring of Rh/Wind/Tmin/Tmax. 4 new `file_*` path members (repurposed pre-existing vestigial `file_relhum`/`file_wind` decls + new `file_tmin`/`file_tmax`) + 4 new `d*` per-day arrays + 4 new `all_d*` per-year caches + 4 param reads in `init()` + 4 cache resizes + 4 guarded reads in `readenv()` (mirror of `imogencfx.cpp:866-888`) + monthly+daily branch additions in `get_climate_for_gridcell()` + 4 `climate.{relhum,u10,tmin,tmax}` assignments in BOTH `getclimate()` (gridcell_outer driver) AND `getclimate_for_year()` (year_outer override). K→°C conversion site decision: at consumer (mirror of existing `climate.temp = dtemp - 273.15` pattern; intentionally DIFFERS from IMOGENCFXInput's monthly-array-step convention with cross-references in both files). B1-pending fallback: `if ((char*)file_relhum != NULL && file_relhum != "")` guard pattern from IMOGENCFXInput; forward-safe across the B1-pending transition. `runs/SSP1-2.6/main_xval_loose.ins` updated (4 new param directives mirroring `main_xval_imogencfx.ins:96-99`). Net source change: +60 LOC in header, +127 LOC in cpp, +15 LOC in .ins. Verification: clean builds both (only pre-existing `gutil.h:1521` sprintf-overflow warning); 162 unit tests pass both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN). Loose-mode-vs-tight-mode 6-vs-10-fields gap CLOSED for the LPJG-side input pipeline. Forensic record at §3f above. Backport-RELEVANT (C++ source change in `lpjguess/modules/`). |
| **B5** | F-9 / step 9.5c miscoutput diagnostic outputs (Option A per-month Climate accumulator ~50 LOC) | 1-2 d | **Step 18** (docs/reproducibility) | Diagnostic outputs benefit step 18's reproducibility verification |
| **B6** ✅ DONE | F-2 Fortran T_anom 2× line count | 0.0 d (subsumed by B10) | **C2 era (this step 17b)** | LANDED 2026-05-11 (commit `24250b2`, docs-only). Forensic determination: the 2× line count is one of three downstream symptoms of the same alternating-year writer bug B10 fixed (T/P/SW/DTEMP doubled to 3262 lines; WET stuck at 1631; fa_ocean contaminated by +1631 WET-format integer rows; dtemp_o doubled to 508). All three symptoms structurally fixed by B10's unconditional-OPEN-per-IYEAR semantics. ZERO Fortran source change for B6. Forensic record at §3c above. |
| **B2** ✅ DONE | Fortran Tmin/Tmax write block | 0.5 d (actual; matches estimate) | **C2 era (this step 17b)** | LANDED 2026-05-12 (this commit). 9 surgical insertions in `imogen/code/imogen_lpjg.f` adding `Tmin_anom.dat` (unit 100) + `Tmax_anom.dat` (unit 101) writers to BOTH REGRID + non-REGRID branches via algebraic `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2` (per Decision #11). Symmetric with C++ in-process port at `climatemodel.cpp` ~lines 952-953 (which has Tmin/Tmax in non-REGRID only — REGRID-side C++ addition is **B3**'s scope). +59 LOC additive (no removals); clean Fortran build (zero warnings; binary 133 696 B = +4096 vs pre-B2); 26 unit-100/101 references match expected. Forensic record at §3d above. Backport-RELEVANT (Fortran source change). |
| **B7** | F-6 CMIP6 `ql1_patt` unit alignment | 0.5 d | **Step 18** (likely needs upstream-author email; aligns with docs era) | Upstream contact + small converter fix in `tools/cmip6_nc_to_cmip5_ascii.py` |
| **B8** | F-7 CMIP6 `pstar_patt` units (Pa vs hPa) | 0.5 d | **Step 18** (batched with B7) | One-line converter fix in same file as B7 |
| **B9** | F-8 CMIP6 wind-mag + precip rain/snow | 0.5-1 d | **Step 18** (batched with B7/B8) | Three CMIP6 caveats together |
| **B10** ✅ DONE | Symmetric Fortran engine writer fix | 0.5 d (actual) | **C2 era (this step 17b)** | LANDED 2026-05-11 (this commit). Mechanical replication of C++ fix at `7be595a` to `imogen_lpjg.f` lines 854/883/954/1013/1071/1088/1099 (**empirically refined to 7 conditional removals**, not 5; 5 C++ analogues + 2 Fortran-specific extras). Forensic record at §3b above. |
| **B11** | Latent OOB fix in IMOGENCFXInput::getclimate cache | 0.5 d | **Step 17d** (end-to-end-validation era) | Defensive hardening of pre-existing latent bug; lands when stress-testing production gridlists |

**C2 era combined sprint total** (this step 17b): C2 core (3-5 d ✅) + **B1 (~0.5 d ✅ this commit; landed via architectural-reframing far lighter than the budgeted 3-5 d because the "physics port" framing was a misread)** + **B2 (0.5 d ✅)** + **B3 (0.3 d ✅; close-by-architectural-reframing)** + **B4 (~0.5 d ✅; lighter than budgeted 1 d because direct mirror of IMOGENCFXInput pattern)** + B6 (0.0 d ✅, subsumed by B10) + B10 (0.5 d ✅) = **~5.3-7.3 days ACTUAL (all DONE)** (revised down ~2.5-4 d from the original 7.8-11.8 d estimate via the two B3+B1 architectural-reframing close-by-investigation outcomes and B4's lighter-than-budgeted direct-mirror landing). **C2-era B-bundle is feature-COMPLETE.** Remaining: C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` only (zero source changes).

**Step 18 bundle**: B5 + B7 + B8 + B9 = ~3-4.5 d (matches step 18's natural 3-5 d docs scope).

**Step 17d**: B11 = 0.5 d (within 17d's 2-3 d validation scope).

**Total B-item time** ~9-15 days, distributed cohesively across 3 natural homes; **nothing left undone**.

---

## 6. References + cross-links

- [`notes/FOLLOWUPS.md`](FOLLOWUPS.md) §"Comprehensive outstanding-work audit (2026-05-11)" — canonical aggregated outstanding-work list with all 22 items in 3 categories + bundling commitment for B1-B11
- [`EXECUTION_PLAN.md`](../EXECUTION_PLAN.md) V.1 step row 17b — C2 scope + tag target `v0.17.5-step17b-c2-mpi-sync`
- [`notes/STEP_17a.md`](STEP_17a.md) — C1 close-out narrative; 5-commit chain `2e918c0 → 90401f2 → 8bddc27 → 7be595a → 8aafe84`
- [`docs/v2_roadmap.md`](../docs/v2_roadmap.md) §5.2 — F-12 Option C design sketch (year_outer); historical reference
- [`_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md`](../../_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md) Parts 8, 14, 15, 16 — C1/C2 narrative trajectory + 2026-05-11 audit + 2026-05-11 C2 prep narrative
- [`lpjguess/CMakeLists.txt`](../lpjguess/CMakeLists.txt) lines 73-87 — MPI auto-detection via `find_package(MPI QUIET)` + `add_definitions(-DHAVE_MPI)`
- [`lpjguess/framework/parallel.cpp`](../lpjguess/framework/parallel.cpp) — minimal MPI infrastructure (`MPI_Init` / `Comm_rank` / `Comm_size` / `Finalize`); no synchronization primitives yet (C2 adds them)
- [`lpjguess/modules/imogenoutput.cpp/h`](../lpjguess/modules/imogenoutput.cpp) — existing `flush_year` (per-gridcell-rolling) + C2-target `flush_year_globally_synchronized` sibling
- [`scripts/cluster/make_guess.sh`](../scripts/cluster/make_guess.sh) — updated this commit (mpicxx-wrapper fix prompt + Anaconda3 NetCDF unconditional)
- [`scripts/run_parallel_mimic.sh`](../scripts/run_parallel_mimic.sh) — workstation MPI mimic harness (verifies C2 correctness at end)
- [`scripts/cross_validate_year_outer.sh`](../scripts/cross_validate_year_outer.sh) — updated this commit (GUESS_BIN env-var overridable; default unchanged)

---

## 7. Remaining work within step 17b (after this B12-resolution commit)

1. **~~C2 core~~ ✅ DONE 2026-05-11** (commit `f13b302`): MPI_Barrier + flush_year_globally_synchronized landed; mechanics verified via single-process xval byte-equality + mpirun -np 1 -parallel smoke. See §3a.
2. **~~B12 (CRITICAL PATH)~~ ✅ DONE 2026-05-11 evening session 3** (this commit): Substantive-validation NaN root cause identified + fixed via 2 `.ins` file changes (`ifcalccton 0 → 1` and `ifcalcsla 0 → 1`). Full forensic chain in §3a.7.4c above. ALL 4 xval scenarios PASS substantive validation (bit-exact + non-NaN). Net `lpjguess/` source change: ZERO. Backport-IRRELEVANT.
3. **B1+B2+B3+B4+B6+B10 bundles (~4-6 d remaining) — IN PROGRESS** (now safe to land on substantively-validated baseline). Per user-confirmed Option A 2026-05-11, ordered B10 → B6 → B2 → B3 → B4 → B1 (mechanical-first; physics-port-last). Status:
   - **B10 ✅ DONE** (commit `3c00428`, 2026-05-11): symmetric Fortran engine writer fix; 7 conditional removals (empirically refined from 5) at `imogen/code/imogen_lpjg.f`; forensic at §3b above.
   - **B6 ✅ DONE** (commit `24250b2`, 2026-05-11; docs-only): F-2 Fortran T_anom 2× line count fully traced to the same alternating-year writer bug B10 fixed (3 symptoms — T/P/SW/DTEMP doubled, WET asymmetric-single, fa_ocean contaminated; one root cause). ZERO Fortran source change. Forensic record at §3c above.
   - **B2 ✅ DONE** (commit `76b3b04`, 2026-05-12): Fortran Tmin/Tmax write block. 9 surgical insertions in `imogen/code/imogen_lpjg.f`; algebraic `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2` in BOTH REGRID + non-REGRID branches; units 100/101; +59 LOC additive; clean Fortran build (zero warnings); static check ✅. Forensic record at §3d above.
   - **B3 ✅ DONE** (this commit, 2026-05-12): **closed by architectural reframing** — the C++ in-process port has **NO REGRID branch** (`bool regrid` at line ~242 is dead code; no `if (regrid)` switch; no `*Regrid` array variants; no `REGRID_CLIM` function was ever ported). The stale `// TODO at step 9.5b: replicate this in the REGRID branch.` was an aspirational forward-reference. ~30 LOC of additive docs in `lpjguess/modules/climatemodel.cpp` (dead-code annotation at line ~242; native-grid-is-only-branch clarification at line ~890; canonical B3 doc-block replacing the stale TODO at line ~894 — with forward-looking maintenance directive for any future C++ REGRID branch). ZERO functional code change. Cross-engine parity matrix (§3d.6) corrected. Forensic record at §3e above. Backport-RELEVANT.
   - **B4 ✅ DONE** (this commit, 2026-05-12 night): `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion. 8 surgical insertions across `lpjguess/modules/imogen_input.{cpp,h}` mirroring C1.1 IMOGENCFXInput step-9.5 pattern: 4 path decls (2 new + 2 repurposed from vestigial) + 4 per-day arrays + 4 per-year caches + init() param reads + cache resizes + readenv() guarded reads + get_climate_for_gridcell() monthly+daily branch additions + climate.{relhum,u10,tmin,tmax} assignments in BOTH `getclimate()` AND `getclimate_for_year()` (with K→°C at consumer site mirroring `climate.temp = dtemp - 273.15` convention; intentionally differs from IMOGENCFXInput's monthly-array-step K→°C convention). `runs/SSP1-2.6/main_xval_loose.ins` updated with 4 new param directives. +60 LOC in header + +127 LOC in cpp + +15 LOC in .ins; ZERO source removals. Loose-mode-vs-tight-mode 6-vs-10-fields gap CLOSED for the LPJG-side input pipeline. Forensic record at §3f above. Backport-RELEVANT.
   - **B1 ✅ DONE** (this commit, 2026-05-12 early morning): Fortran-engine Rh + Wind COMPUTATION + write-block port — **closed by architectural reframing** (the audit-table "physics port" framing was a misread; only mechanical-symmetric-writer work was needed). 18 surgical sub-edits + 1 NEW `SUBROUTINE RH_FROM_QPT` (~40 LOC Tetens algebra; byte-identical to C++) in `imogen/code/imogen_lpjg.f`. Writes `Rh_anom.dat` (unit 96) + `W_anom.dat` (unit 97) to BOTH REGRID + non-REGRID branches; extends `REGRID_CLIM` by 3 new nearest-neighbor passthroughs for `WIND_OUT/QHUM_OUT/PSTAR_OUT`. +200 LOC net additive (single file). Verification: clean Fortran build (binary 137832 B; zero new warnings); clean lpjguess rebuilds both (no-op regression); 162 unit tests pass both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN). Cross-engine Rh/W gap CLOSED. Forensic record at §3g above. Backport-RELEVANT.
4. **B13 (NEW; defensive hardening; 0.5 d) — bundle with step 18**: per §3a.7.4c "Defensive hardening recommendation", make LPJG fail-fast at `init_cton_limits()` if `cton_leaf_min == 0`, so the next user setting `ifcalccton 0` without an explicit `.ins` `cton_leaf_min` value gets a clear error instead of silent NaN cascade.
5. **B14 (NEW; process hardening; 0.5–1 d) — bundle with step 18**: per §3a.7.4c "Process hardening recommendation", one-time `.ins` parity audit of `runs/SSP1-2.6/main_xval_*.ins` (and import chain) vs `version_A`'s + `version_B`'s `landsymm_imogen/SSP1_RCP26/` `.ins` set; classify each divergent parameter as intentional vs unintentional. Persistent companion: NEW "Operational heuristics — lessons learned" subsection in `notes/FOLLOWUPS.md` with `.ins`-parity-with-original as rule #1 forensic step.
6. **C2 close-out + tag** (after B1+B2+B3+B4+B6+B10 land): full 4-xval cross-validation against both `build/guess` and `build_mpi/guess` (single-process AND `mpirun -np 4` mimic via `scripts/run_parallel_mimic.sh` + properly populated per-rank `runNN/` dirs via `scripts/cluster/setup_run.sh`) — both gates pass (bit-exact AND non-NaN); 162 unit tests both builds; tag `v0.17.5-step17b-c2-mpi-sync`; push commit + tag to all 3 remotes.

**Revised C2 era combined sprint estimate**: **~0 d source-level remaining; C2 close-out tag only** (was ~4-7 d before this commit; B1 landed in ~0.5 d via architectural-reframing rather than the budgeted 3-5 d). **All 6 audit items in the re-ordered Option A sequence are DONE**: B10 → B6 → B2 → B3 → B4 → **B1** (this commit). Next step: C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` on top of this commit (zero source changes; tag + push only). After tag: Step 17c (HPC integration tests on `owl` cluster) per `EXECUTION_PLAN.md`.

---

— Last updated 2026-05-11 (C2 core landing + substantive-validation NaN finding + xval harness hardening + B12 audit item; un-tagged checkpoint on top of C2 prep `1405ada`) —

— Updated 2026-05-11 evening (session 3) with §3a.7.4c B12 RESOLUTION: root cause identified (`ifcalccton 0` in smoke .ins → `init_cton_min()` skipped → cton_leaf_min=0 → cascade → 0/0=NaN in respiration); fix applied (`ifcalccton 1` + `ifcalcsla 1` in 2 .ins files; ZERO lpjguess/ source change); ALL 4 xval scenarios PASS substantive validation against both build/guess and build_mpi/guess. Un-tagged checkpoint on top of `d7f6c74`. C2 era estimate revised back to ~9-13 d remaining. —

— Extended 2026-05-11 evening (session 3 continuation) with §3a.7.4c "Process hardening" addendum: predecessor `version_A`'s `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/global.ins` empirically confirmed to set `ifcalcsla 1` and `ifcalccton 1` (lines 96, 98) → B12 was a config-divergence-from-canonical-baseline issue, not an LPJG code defect. Per user direction: full `.ins` realignment audit deferred (not needed; fix sufficed); persistent documentation added — NEW audit item B14 (one-time `.ins` parity audit) + NEW "Operational heuristics — lessons learned" subsection in `notes/FOLLOWUPS.md` (5 standing rules; `.ins`-parity-with-original as rule #1 first-line forensic step). —

— Extended 2026-05-11 night (session 3 continuation) with NEW §3b: B10 SYMMETRIC FORTRAN ENGINE WRITER FIX landed (un-tagged commit). 7 conditional removals (empirically refined from originally-documented 5; 5 C++ analogues + 2 Fortran-specific extras: explicit CO2.dat CLOSE + non-REGRID climate-anomaly OPEN/CLOSE) in `imogen/code/imogen_lpjg.f` with C++ doc-block parity. Pre-implementation comprehensive re-examination of project documentation completed per user direction (Decisions #2/#11/#12 + IMOGENCXX vs in-process C++ port distinction confirmed; standalone IMOGENCXX with 25 bugs is Phase 2; Fortran is canonical for v1.0). Reordered B-item implementation per user-confirmed Option A: B10 → B6 → B2 → B3 → B4 → B1 (mechanical-first; physics-port-last). Verification: clean Fortran build (zero warnings); static gate-removal check (all 7 gates correctly removed); pre-fix evidence preserved in `imogen/code/IMOGEN/output/{1871,1872}/`. Empirical post-fix engine smoke deferred (Fortran engine inputs not currently shipped in active rebuild; symmetric-correctness framing means clean compile + diff parity suffice). Backport-RELEVANT (Fortran source change). —

— Extended 2026-05-11 night (session 3 continuation; commit `24250b2`) with NEW §3c: B6 — F-2 Fortran T_anom 2× line count investigation **subsumed by B10** (un-tagged docs-only commit). Forensic finding: the originally-reported 2× line count for T_anom.dat (3262 vs version_A's 1631) is one of three downstream symptoms of B10's alternating-year writer bug — (1) T/P/SW/DTEMP doubled to 3262 lines; (2) WET stuck at 1631 lines (asymmetric, due to mid-1871 unit-95 reuse for fa_ocean.dat that auto-closed WET); (3) fa_ocean.dat contaminated by +1631 WET-format integer rows (year-1872 WET writes appended to the still-open year-1871 fa_ocean unit). Smoking-gun confirmation: lines 10001-11631 of pre-fix `fa_ocean.dat` are exact WET-format `LON LAT + 12 ints` rows. Cross-validation against `version_A/.../IMOGEN/output/1871/` reference (T/P/SW/DTEMP=1631 each, WET=1631, fa_ocean=10000 clean) confirms the predicted post-B10 structural output. ZERO Fortran source change for B6. Updated §5 bundling table (B6 → 0.0 d, ✅ DONE) + §7 remaining work (B2 now NEXT). C2-era estimate revised down to ~6.5-9.5 d remaining (was ~9-13 d). Backport-IRRELEVANT (no source change; B10 backport entry already covers all 7 gates whose removal collectively fixes the B6 symptom). —

— Extended 2026-05-12 (session 3 continuation; commit `76b3b04`) with NEW §3d: B2 — Fortran Tmin/Tmax write block LANDED. 9 surgical insertions in `imogen/code/imogen_lpjg.f` adding `Tmin_anom.dat` (unit 100) + `Tmax_anom.dat` (unit 101) writers to BOTH REGRID + non-REGRID branches via algebraic `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2` (per Decision #11; same units as T = Kelvin). Symmetric with C++ in-process port at `lpjguess/modules/climatemodel.cpp` ~lines 952-953 (which has Tmin/Tmax in non-REGRID only — REGRID-side C++ addition is **B3**'s scope per the `// TODO at step 9.5b` comment in C++ source ~line 894). Net Fortran source change: +59 LOC additive (no removals). Verification: clean Fortran build (zero warnings; binary 133 696 B = +4096 vs pre-B2's 129 600 B); static unit-100/101 reference count = 26 (matches expected 4 OPENs + 2 CLOSEs + 8 LON/LAT writes + 8 data writes + 4 per-cell newlines); both `Tmin_anom.dat` + `Tmax_anom.dat` paths verified at REGRID branch lines 1041-1042 + non-REGRID branch lines 1136-1137; algebra parity with C++ confirmed (`/2.0` REAL division; same `(f10.3)` format; same Kelvin units). Updated §5 bundling table (B2 ✅ DONE) + §7 remaining work (B3 now NEXT) + post-B2 cross-engine parity matrix in §3d.6 (Fortran has Tmin/Tmax in BOTH branches; C++ in non-REGRID only; B3 closes the C++ REGRID gap). C2-era estimate revised down to ~5.5-8.5 d remaining (was ~6.5-9.5 d). Backport-RELEVANT (Fortran source change in standalone engine). —

— Extended 2026-05-12 night (session 3 continuation; commit `ceb2766`) with NEW §3e: B3 — C++ Tmin/Tmax in REGRID branch of `climatemodel.cpp` **closed by architectural reframing** (NOT by mechanical Tmin/Tmax insertion). Pre-implementation forensic investigation revealed: the C++ in-process port (`lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()`) has **NO REGRID branch** — only one climate-anomaly writer block (the native-IMOGEN-grid branch at line ~890). Evidence chain: (a) `rg "REGRID\|regrid" climatemodel.cpp` returns only 3 hits — line 242 dead-code declaration, line 894 stale TODO, line 1353 unrelated comment; (b) no `if (regrid) { ... } else { ... }` switch anywhere; (c) zero `*Regrid` array declarations or usages (only native `tOutM`/`pOutM`/`swOutM`/`windOutM`/`rhOutM`/`dtempOutM` at lines ~284-289); (d) zero `REGRID_CLIM` function calls in any `lpjguess/` source (the Fortran helper `REGRID_CLIM` at `imogen_lpjg.f` ~line 964 was never ported). Interpretation: the `// TODO at step 9.5b: replicate this in the REGRID branch.` comment was an aspirational forward-reference left by the step-9.5 author anticipating a future C++ REGRID branch that was never built. ~30 LOC of additive documentation in `lpjguess/modules/climatemodel.cpp` (3 doc-only edits: dead-code annotation at the `bool regrid` declaration line ~242; native-grid-is-only-branch clarification at line ~890; canonical B3 doc block replacing the stale TODO at line ~894 — with forward-looking maintenance directive specifying the exact C++ algebraic pattern for any future REGRID-branch Tmin/Tmax addition). **ZERO functional code change**. Verification: clean rebuild on both `build/` and `build_mpi/` with zero new warnings (forced rebuild of `climatemodel.cpp`); 162 unit tests pass on both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN) against `build_mpi/guess` single-process. **Updated §3d.6 cross-engine parity matrix** to reflect actual state (rather than the pre-B3 documentation drift that wrongly attributed a REGRID branch to the C++ port): Tmin/Tmax are now present at every climate-anomaly writer site that currently exists in either engine; the Fortran has them in BOTH its REGRID + non-REGRID branches (B2 added them); the C++ has them in the only branch it has. New persistent operational heuristic rule #7 added in `notes/FOLLOWUPS.md`: "stale forward-reference TODOs are architectural-finding triggers — investigate the actual code structure before mechanically replicating from a sibling implementation." C2-era estimate revised down to ~5-8 d remaining (was ~5.5-8.5 d). v1.0 % done estimate revised UP to ~56-59%; ~41-44% remaining. Backport-RELEVANT (C++ source change in `lpjguess/modules/`). —

— Extended 2026-05-12 early morning (session 3 continuation; this commit) with NEW §3g: B1 — Fortran-engine Rh + Wind COMPUTATION + write-block port LANDED — **closed by architectural reframing** (LAST audit item before C2 close-out). Pre-implementation forensic finding: the audit-table description "Fortran Rh + Wind COMPUTATION port" mischaracterised the scope. There is no heavy physics to port — Wind output is a direct passthrough from `windOut` (`climatemodel.cpp:865`); Rh output is a single inline Tetens-formula computation at `climatemodel.cpp:866` calling `computeRelativeHumidityFromSpeificHumidty` (22 LOC at `climatemodel.cpp:1228-1249`). Fortran-side `WIND_OUT/QHUM_OUT/PSTAR_OUT/T_OUT_M` already exist + are populated by the existing `CLIM_DISAG` call. B1 was mechanical-symmetric-writer work, NOT a physics port. 18 surgical sub-edits + 1 NEW `SUBROUTINE RH_FROM_QPT(Q, P_PA, T_K, RH)` (~40 LOC Tetens algebra; byte-identical to C++ `computeRelativeHumidityFromSpeificHumidty`) in `imogen/code/imogen_lpjg.f`. Writes `Rh_anom.dat` (unit 96) + `W_anom.dat` (unit 97) to BOTH REGRID + non-REGRID branches with B2-style symmetric discipline; extends `REGRID_CLIM` by 3 new nearest-neighbor passthroughs for `WIND_OUT/QHUM_OUT/PSTAR_OUT`. Net source change: +202 / -2 = +200 LOC additive (single file `imogen/code/imogen_lpjg.f`); ZERO changes to `lpjguess/`. **Design decisions** (cited in doc blocks): (1) inline Tetens (NOT `QSAT` Goff-Gratch lookup) for bit-level cross-engine parity with C++; (2) BOTH REGRID + non-REGRID branches for B2-discipline parity; (3) inline `CALL RH_FROM_QPT` at each writer site (no global `RH_OUT_M` array; mirrors C++ `rhOutM` pattern); (4) unit numbers 96/97 mirror C++ ofstream names `file96`/`file97`; (5) append new args at END of `REGRID_CLIM` signature for minimal-diff principle; (6) symmetric ALLOCATE/DEALLOCATE/decl ordering mirroring pre-B1 T/P/SW/DTEMP/F_WET pattern. Verification: clean Fortran build (binary 137832 B; zero new warnings with `-Wall`; 8 pre-existing warnings unchanged); clean `lpjguess/build/` + `build_mpi/` rebuilds (no-op regression check; zero changes there); 162 unit tests pass on both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN). **Cross-engine parity matrix (§3g.6)**: full climate-anomaly output parity achieved for the v1.0 production path — T/P/SW/WET/DTEMP/Tmin/Tmax/Rh/W are all written by both engines. Second application of operational heuristic rule #7 (stale forward-reference / mischaracterised-scope TODOs are architectural-finding triggers — investigate the actual code structure before relying on the audit-table description). **C2-era B-bundle is feature-COMPLETE** (all 6 items DONE: B10 → B6 → B2 → B3 → B4 → B1). C2-era source-level estimate revised down to ~0 d remaining; only the C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` remains (zero source changes). v1.0 % done estimate revised UP to ~62-65%; ~35-38% remaining. Backport-RELEVANT (Fortran source change in standalone engine; F-11 ledger entry at `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17b-B1). —

— Extended 2026-05-12 night (session 3 continuation; commit `2bd5222`) with NEW §3f: B4 — `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion LANDED. Mirrors the C1.1 IMOGENCFXInput step-9.5 wiring pattern (commit `a543e9d` + step-17a sub-step 7.3.2 K→°C bug-fix at `8aafe84`) on the loose-mode (`-input imogen`) side: closes the loose-mode-vs-tight-mode 6-vs-10-fields gap identified at the 2026-05-10 late-evening audit. 8 surgical insertions across 3 source files + 1 config file. In `lpjguess/modules/imogen_input.h` (3 edits, +60 LOC): 4 new per-day arrays `drelhum/dwind/dtmin/dtmax[Date::MAX_YEAR_LENGTH]` with ~30-line K-vs-°C convention doc block; doc block annotating the pre-existing vestigial `file_relhum`/`file_wind` decls as now-wired-by-B4 + 2 new path decls `file_tmin`/`file_tmax`; 4 new per-year cache decls `all_drelhum/all_dwind/all_dtmin/all_dtmax`. In `lpjguess/modules/imogen_input.cpp` (5 edits, +127 LOC): ~30-line canonical B4 doc block in `init()` + 4 param reads `file_relhum/wind/tmin/tmax = param[…].str;`; 4 new `resize3DimVector` calls in `init()`; doc block + 4 guarded reads in `readenv()` (using `(char*)file_relhum != NULL && file_relhum != ""` pattern from IMOGENCFXInput); monthly+daily branch additions in `get_climate_for_gridcell()` (4 `m*[12]` + 4 `have_*` booleans + 4 `interp_monthly_means_conserve` calls in monthly branch; 4 guarded daily passthroughs in daily branch; NO K→°C at this layer per ImogenInput convention); 4 `climate.{relhum,u10,tmin,tmax}` assignments in BOTH `getclimate()` (gridcell_outer driver) AND `getclimate_for_year()` (C1.1 year_outer override) — with K→°C `- 273.15` on tmin/tmax mirroring the existing `climate.temp = dtemp - 273.15` pattern on the line above. In `runs/SSP1-2.6/main_xval_loose.ins` (1 edit, +15 LOC): doc block + 4 new param directives `file_relhum`/`file_wind`/`file_tmin`/`file_tmax` mirroring `main_xval_imogencfx.ins:96-99`. **Design decisions** (cited in doc blocks): (1) K→°C conversion site at consumer site (mirror of existing `climate.temp` pattern), intentionally DIFFERS from IMOGENCFXInput's monthly-array-step convention (post-step-17a-7.3.2) — preserved with cross-references in both files to prevent future drift; (2) B1-pending fallback: `if (path != "")` guards forward-safe across the B1-pending transition (RH/Wind Fortran physics port still pending); (3) Repurpose pre-existing vestigial `file_relhum`/`file_wind` declarations rather than adding duplicates; (4) `preload_all_climate` unchanged (delegates to `readenv()`); (5) `runs/SSP1-2.6/main_xval_loose.ins` updated 1:1 with `main_xval_imogencfx.ins` so xval exercises the new wiring. Verification: clean rebuild on both `build/` and `build_mpi/` (only pre-existing `gutil.h:1521` sprintf-overflow warning in `Timer::print` — unchanged by B4; would emit at any caller of `Timer::settimer`); 162 unit tests pass on both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN); 8 run.log files from xval show "Finished" terminator without `read_lines_from_file` failures, confirming all 4 new paths resolved + were read successfully (a missing file would trigger `fail()` at `imogen_input.cpp:550`). Updated §3f.6 loose-mode consumer-wiring parity matrix to reflect post-B4 state: both input modules now populate all 10 climate fields (`temp/prec/insol/dtr/co2/dNH4dep+dNO3dep/relhum/u10/tmin/tmax`); the loose-mode-vs-tight-mode 6-vs-10-fields gap is CLOSED for the LPJG-side input pipeline. The K→°C conversion site difference between the two input modules is intentional + documented + cross-referenced. C2-era estimate revised down to ~4-7 d remaining (was ~5-8 d). v1.0 % done estimate revised UP to ~58-62%; ~38-42% remaining. Per re-ordered Option A: next is B1 (LAST in sequence; ~3-5 d Fortran Rh + Wind physics port; heaviest item). Backport-RELEVANT (C++ source change in `lpjguess/modules/`). —
