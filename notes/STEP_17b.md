# STEP 17b — F-12 sub-milestone C2 (Workstation MPI year_outer + B1+B4 + small bundles)

**Date opened:** 2026-05-11
**Date C2 prep landed:** 2026-05-11 (commit `1405ada`; un-tagged checkpoint; pushed to all 3 remotes)
**Date C2 core (MPI_Barrier + flush_year_globally_synchronized) landed:** 2026-05-11 (this commit; un-tagged checkpoint)
**Date B1+B4 bundled with C2 era landed:** _pending_
**Date C2 close-out + tag `v0.17.5-step17b-c2-mpi-sync` landed:** _pending_
**Status:** 🔧 IN PROGRESS — C2 prep phase ✅ done (`1405ada`); C2 core ✅ done (this commit; LPJG source ~317 LOC additive across 3 files); B1+B4+B2+B3+B6+B10 bundles ⏳ NEXT; full mpirun -np 4 mimic + tag at close-out.

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
| **B1** | Fortran Rh + Wind COMPUTATION port | 3-5 d | **C2 era (this step 17b)** | Cohesive with C2's engine + ImogenOutput-touching scope; produces full Fortran symmetry for v1.0 |
| **B2** | Fortran Tmin/Tmax write block | 0.5 d | **C2 era (this step 17b)** | Trivially extends B1's Fortran writer work; algebraic `Tmin = T - DTEMP/2` |
| **B3** | C++ Tmin/Tmax in REGRID branch | 0.5 d | **C2 era (this step 17b)** | Mirrors B2 logic in REGRID branch; closes `// TODO at step 9.5b` in climatemodel.cpp |
| **B4** | ImogenInput Rh/W/Tmin/Tmax consumer wiring expansion | 1 d | **C2 era (this step 17b)** | ImogenInput already has year_outer overrides from C1.1; expansion is natural follow-on |
| **B5** | F-9 / step 9.5c miscoutput diagnostic outputs (Option A per-month Climate accumulator ~50 LOC) | 1-2 d | **Step 18** (docs/reproducibility) | Diagnostic outputs benefit step 18's reproducibility verification |
| **B6** | F-2 Fortran T_anom 2× line count | 0.5 d | **C2 era (this step 17b)** | While in B1's Fortran writer code, look at the 2× line count |
| **B7** | F-6 CMIP6 `ql1_patt` unit alignment | 0.5 d | **Step 18** (likely needs upstream-author email; aligns with docs era) | Upstream contact + small converter fix in `tools/cmip6_nc_to_cmip5_ascii.py` |
| **B8** | F-7 CMIP6 `pstar_patt` units (Pa vs hPa) | 0.5 d | **Step 18** (batched with B7) | One-line converter fix in same file as B7 |
| **B9** | F-8 CMIP6 wind-mag + precip rain/snow | 0.5-1 d | **Step 18** (batched with B7/B8) | Three CMIP6 caveats together |
| **B10** | Symmetric Fortran engine writer fix | 0.5 d | **C2 era (this step 17b)** | Mechanical replication of C++ fix at `7be595a` to `imogen_lpjg.f` lines 954/1013/1071/1088/1099 |
| **B11** | Latent OOB fix in IMOGENCFXInput::getclimate cache | 0.5 d | **Step 17d** (end-to-end-validation era) | Defensive hardening of pre-existing latent bug; lands when stress-testing production gridlists |

**C2 era combined sprint total** (this step 17b): C2 core (3-5 d) + B1 (3-5 d) + B2 (0.5 d) + B3 (0.5 d) + B4 (1 d) + B6 (0.5 d) + B10 (0.5 d) = **~9-13 days**.

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
3. **B1+B2+B3+B4+B6+B10 bundles (~6-8 d) — NEXT** (now safe to land on substantively-validated baseline): Fortran Rh/Wind physics port (B1; ~70-100 LOC in `imogen/code/imogen_lpjg.f`) + Fortran Tmin/Tmax write (B2; 0.5 d) + C++ Tmin/Tmax REGRID branch (B3; 0.5 d) + ImogenInput Rh/W/Tmin/Tmax consumer wiring expansion (B4; 1 d) + Fortran T_anom 2× investigation (B6; 0.5 d) + symmetric Fortran engine writer fix (B10; 0.5 d).
4. **B13 (NEW; defensive hardening; 0.5 d) — bundle with step 18**: per §3a.7.4c "Defensive hardening recommendation", make LPJG fail-fast at `init_cton_limits()` if `cton_leaf_min == 0`, so the next user setting `ifcalccton 0` without an explicit `.ins` `cton_leaf_min` value gets a clear error instead of silent NaN cascade.
5. **B14 (NEW; process hardening; 0.5–1 d) — bundle with step 18**: per §3a.7.4c "Process hardening recommendation", one-time `.ins` parity audit of `runs/SSP1-2.6/main_xval_*.ins` (and import chain) vs `version_A`'s + `version_B`'s `landsymm_imogen/SSP1_RCP26/` `.ins` set; classify each divergent parameter as intentional vs unintentional. Persistent companion: NEW "Operational heuristics — lessons learned" subsection in `notes/FOLLOWUPS.md` with `.ins`-parity-with-original as rule #1 forensic step.
6. **C2 close-out + tag** (after B1+B2+B3+B4+B6+B10 land): full 4-xval cross-validation against both `build/guess` and `build_mpi/guess` (single-process AND `mpirun -np 4` mimic via `scripts/run_parallel_mimic.sh` + properly populated per-rank `runNN/` dirs via `scripts/cluster/setup_run.sh`) — both gates pass (bit-exact AND non-NaN); 162 unit tests both builds; tag `v0.17.5-step17b-c2-mpi-sync`; push commit + tag to all 3 remotes.

**Revised C2 era combined sprint estimate**: **~9-13+ days remaining** (was 11-23+; B12 closed in ~2 hours session 3 work, much faster than 2-10 d unbounded estimate). Remaining: B-bundles ~6-8 d + C2 close-out + mpirun -np 4 verification ~1-2 d.

---

— Last updated 2026-05-11 (C2 core landing + substantive-validation NaN finding + xval harness hardening + B12 audit item; un-tagged checkpoint on top of C2 prep `1405ada`) —

— Updated 2026-05-11 evening (session 3) with §3a.7.4c B12 RESOLUTION: root cause identified (`ifcalccton 0` in smoke .ins → `init_cton_min()` skipped → cton_leaf_min=0 → cascade → 0/0=NaN in respiration); fix applied (`ifcalccton 1` + `ifcalcsla 1` in 2 .ins files; ZERO lpjguess/ source change); ALL 4 xval scenarios PASS substantive validation against both build/guess and build_mpi/guess. Un-tagged checkpoint on top of `d7f6c74`. C2 era estimate revised back to ~9-13 d remaining. —

— Extended 2026-05-11 evening (session 3 continuation) with §3a.7.4c "Process hardening" addendum: predecessor `version_A`'s `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/global.ins` empirically confirmed to set `ifcalcsla 1` and `ifcalccton 1` (lines 96, 98) → B12 was a config-divergence-from-canonical-baseline issue, not an LPJG code defect. Per user direction: full `.ins` realignment audit deferred (not needed; fix sufficed); persistent documentation added — NEW audit item B14 (one-time `.ins` parity audit) + NEW "Operational heuristics — lessons learned" subsection in `notes/FOLLOWUPS.md` (5 standing rules; `.ins`-parity-with-original as rule #1 first-line forensic step). —
