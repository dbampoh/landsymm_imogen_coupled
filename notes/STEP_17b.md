# STEP 17b — F-12 sub-milestone C2 (Workstation MPI year_outer + B1+B4 + small bundles)

**Date opened:** 2026-05-11
**Date C2 prep landed:** 2026-05-11 (this commit; un-tagged checkpoint)
**Date C2 core (MPI_Barrier + flush_year_globally_synchronized) landed:** _pending_
**Date B1+B4 bundled with C2 era landed:** _pending_
**Date C2 close-out + tag `v0.17.5-step17b-c2-mpi-sync` landed:** _pending_
**Status:** 🔧 IN PROGRESS — C2 prep phase ✅ done; C2 core ⏳ next; B1+B4 + small bundles ⏳ after core; tag at close-out.

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

## 4. C2 core implementation plan (next phase)

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

## 7. Remaining work within step 17b (after this prep commit)

1. **C2 core (~3-5 d)**: `MPI_Barrier(MPI_COMM_WORLD)` at year boundary in framework.cpp + `flush_year_globally_synchronized(int year)` in imogenoutput.cpp/h + workstation MPI mimic test via `scripts/run_parallel_mimic.sh --np 4`.
2. **B1+B2+B3+B4+B6+B10 bundles (~6-8 d)**: Fortran Rh/Wind physics port (B1; ~70-100 LOC in `imogen/code/imogen_lpjg.f`) + Fortran Tmin/Tmax write (B2; 0.5 d) + C++ Tmin/Tmax REGRID branch (B3; 0.5 d) + ImogenInput Rh/W/Tmin/Tmax consumer wiring expansion (B4; 1 d) + Fortran T_anom 2× investigation (B6; 0.5 d) + symmetric Fortran engine writer fix (B10; 0.5 d).
3. **C2 close-out + tag**: full 4-xval cross-validation against both `build/guess` and `build_mpi/guess` (single-process AND `mpirun -np 4` mimic); 162 unit tests both builds; tag `v0.17.5-step17b-c2-mpi-sync`; push commit + tag to all 3 remotes.

---

— End of STEP_17b.md prep-phase landing (2026-05-11) —
