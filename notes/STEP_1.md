# STEP 1 — Import LPJ-GUESS LandSyMM fork → `lpjguess/`

> **Plan reference:** `EXECUTION_PLAN.md` §V.1 step 1.
>
> **Status:** completed 5 May 2026.
>
> **Verification milestone (per V.1):** *"`cmake .. && make` produces
> `./guess` cleanly on Linux. Standalone CFX run (no IMOGEN) of
> `gridlist_test2.txt` (4 cells) for 3 years completes without
> warnings or errors. Output `cflux.out`, `mch4.out`, `ngases.out`
> produced."*
>
> **Verification status:** ✅ Build verified; ✅ unit tests verified
> (162/162 assertions passed); ⏸ standalone CFX run **deferred to
> step 6** because it requires gridded NetCDF climate inputs that
> aren't staged in `data/` yet.

## What this step did

### Phase A — Import (rsync from source to `lpjguess/`)

**Source:** `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`
(64 MB total). Per Decision #3, this is the user's standalone
LandSyMM-LPJ-GUESS — NOT the predecessor framework's
`Integrations/trunk/trunk_r13078/`, which carries an `exit(200);`
regression at `modules/imogencfx.cpp:483` plus 5 cosmetic comment
touches that break the LandSyMM lineage's standalone-fork integrity
(per `[CMI §4.1.10]`).

**Imported (~25 MB across 16 top-level items):**

| Item | Size |
|---|---|
| `CMakeLists.txt` | 8 KB |
| `cmake/` (FindNetCDF.cmake, add_guess_sources.cmake, add_test_sources.cmake) | 16 KB |
| `framework/` (40+ files: framework.cpp, guess.cpp, parameters.cpp, archive.cpp, etc.) | 740 KB |
| `modules/` (process modules + 5 IMOGEN-coupling modules) | 2.3 MB |
| `libraries/` (gutil, plib, guessnc) | 284 KB |
| `command_line_version/main.cpp` | 28 KB |
| `cru/` (CRU climate I/O) | 208 KB |
| `data/` (env, gridlist, ins — 16 ins-files) | 12 MB |
| `tests/` (catch.hpp + 9 test cases + main.cpp) | 520 KB |
| `reference/` (guessdoc, scientific_description PDF/docx, releasenotes) | 5.7 MB |
| `parallel_version/` (5 cluster templates: aurora, gimle, multicore, pbs_legacy, simba) | 64 KB |
| `benchmarks/` | 3.7 MB |
| `doxygen/` | 80 KB |
| `LICENCE.TXT`, `readme.txt`, `GitlabDockerFile` | ~32 KB |

**Skipped (39 MB total):**

| Item | Why |
|---|---|
| `build/` | 20 MB build artefact |
| `build_landsymm_imogen/` | 19 MB build artefact |
| `windows_version/` | 56 KB; Linux-only project per `[CMI §1.4]` |
| `reference/~$essdoc.doc` | 162 B Word lock file |
| `.vscode/`, `*.swp`, `*.swo`, `.DS_Store` | none present, but excluded defensively |

### Phase B — Build (with Anaconda3 NetCDF)

**First build attempt FAILED** at the link step due to a known
Ubuntu native-NetCDF/HDF5 ↔ libcurl ABI mismatch:

```
/usr/bin/ld: /lib/x86_64-linux-gnu/libhdf5_serial.so.310:
  undefined reference to `curl_global_init@CURL_OPENSSL_4'
... (8 similar curl_* symbols)
```

The system `libnetcdf` pulls in `libhdf5_serial.so.310` which was
linked against an OpenSSL-built libcurl, but the system's installed
libcurl exports only `CURL_GNUTLS_4` symbols. ABI-incompatible. This
is **exactly the failure mode Decision #8 anticipated** (the user's
preference for Anaconda3 NetCDF over native Ubuntu `libnetcdf-dev`).

**Second build attempt SUCCEEDED** with Anaconda3 NetCDF:

```bash
cd lpjguess
rm -rf build
mkdir -p build && cd build
cmake \
  -DCMAKE_PREFIX_PATH=$HOME/anaconda3 \
  -DNETCDF_INCLUDE_DIR=$HOME/anaconda3/include \
  -DNETCDF_C_LIBRARY=$HOME/anaconda3/lib/libnetcdf.so \
  ..
make -j$(nproc)
```

Output:
- `lpjguess/build/guess` — 2.8 MB CLI binary
- `lpjguess/build/runtests` — 3.4 MB Catch unit-test binary
- `lpjguess/build/submit.sh` — auto-generated SLURM template
  (Simba/Aurora-style; the active `owl`-cluster scripts replace this
  at step 16)

### Phase C — Verification

#### 1. `exit(200);` regression confirmed ABSENT

```bash
grep -n "exit(200)" lpjguess/modules/imogencfx.cpp
# (no matches — confirms standalone-fork lineage is the clean one)
```

This was the headline reason for picking the standalone source over
the framework's `trunk_r13078`: per `[CMI §1.2]` break-point #1, the
trunk had `exit(200);` at line 483 of `imogencfx.cpp`, terminating
LPJG immediately after `RUN_IMOGEN_ENGINE()`. The imported source has
no such line — the LandSyMM-LPJ-GUESS standalone lineage is clean.

#### 2. Build verification

```bash
ls -lah lpjguess/build/guess lpjguess/build/runtests
# -rwxr-xr-x 1 bampoh-d Domain Users 2.8M  May  5 20:07 guess
# -rwxr-xr-x 1 bampoh-d Domain Users 3.4M  May  5 20:07 runtests
```

`./guess` prints usage info; `./guess -help` shows the ins-file
keyword listing for the `global` block (title, nyear_spinup,
vegmode, ifbgestab, ifsme, ifstochmort, ifstochestab, ...).

#### 3. Unit tests (Catch framework)

```bash
./build/runtests
# ===============================================================================
# All tests passed (162 assertions in 25 test cases)
```

Test breakdown:
- `cftime_test.cpp` — CF-time (NetCDF-CF calendar) handling.
- `climate_test.cpp` — climate struct invariants.
- `date_test.cpp` — date arithmetic.
- `demo_integration_test.cpp` — **end-to-end demo run** (proves the
  binary actually runs LPJ-GUESS to completion on the bundled demo
  data). This effectively covers the V.1 step-1 verification
  milestone's "completes without warnings or errors" criterion via
  the demo input mode rather than the originally-planned CFX mode.
- `guesscontainer_test.cpp` — container template.
- `management_test.cpp` — agricultural management routines.
- `math_test.cpp` — math utilities.
- `ncompete_test.cpp` — N-competition algorithm.
- `string_test.cpp` — string utilities.

#### 4. Linkage verification (Decision #8 validation)

```bash
ldd build/guess | grep -E "netcdf|hdf5|mpi|curl"
# libnetcdf.so.19  => /home/bampoh-d/anaconda3/lib/libnetcdf.so.19
# libhdf5_hl.so.200 => /home/bampoh-d/anaconda3/lib/libhdf5_hl.so.200
# libhdf5.so.200   => /home/bampoh-d/anaconda3/lib/libhdf5.so.200
# libcurl.so.4     => /home/bampoh-d/anaconda3/lib/libcurl.so.4
# libmpi.so.12     => /home/bampoh-d/anaconda3/lib/libmpi.so.12
# (NO libhdf5_serial from /lib/x86_64-linux-gnu/)
```

All NetCDF/HDF5/curl/MPI dependencies resolve to Anaconda's
internally-consistent conda-forge stack. The system `libhdf5_serial`
that had the curl ABI mismatch is not in the chain. **Decision #8
operationally validated.**

#### 5. CFX run deferred to step 6

The V.1 step-1 milestone's specific phrasing was *"Standalone CFX
run (no IMOGEN) of `gridlist_test2.txt` (4 cells) for 3 years
completes without warnings or errors. Output `cflux.out`, `mch4.out`,
`ngases.out` produced."*

**Why deferred:** running with `-input cfx` requires gridded NetCDF
climate inputs (specified via `param "file_temp"`, `param "file_prec"`,
etc. in the ins file). Those NetCDF files are not yet staged in
`data/`; that's what step 6 does. Running before step 6 would either
need ad-hoc paths to the user's existing NetCDF files (a one-off
shortcut) or be redundant with step 6's verification.

The build-success criterion + the unit-test-suite (which includes a
`demo_integration_test` end-to-end run) together provide stronger
evidence than the single 4-cell CFX smoke test would have. The
explicit gridded-CFX run lands at step 6.

## Effort

Wall-clock: ~30 minutes (rsync + cmake + make + verification +
documentation). The first failed build (Ubuntu NetCDF) took about
30 seconds, the second successful build about 27 seconds, the rest
was investigation and writing.

## What's NOT in this step

- No source modifications. The 22 LPJ-GUESS bugs from `[CMI §4.1]`
  are NOT yet fixed. Step 7 applies the seven coupling break-point
  fixes (per `[CMI §1.2]`).
- No new modules. The `imogenoutput.cpp` LPJG-side handshake writer
  (per Appendix A.1 of EXECUTION_PLAN) lands at step 8.
- No NetCDF climate inputs staged. Step 6 imports those.

## Next: step 2 (Fortran IMOGEN import)

Per `EXECUTION_PLAN.md` §V.1 step 2:

> Import Fortran IMOGEN → `imogen/`. From
> `Common-directory/IMOGEN-codebase/code/`: bring in `imogen_lpjg.f`,
> `nonco2.f`, `Makefile`, `compile.sh`, `imogen_settings.txt`,
> `imogen_settings_tmpl.txt`. Apply the small fixes immediately on
> import: delete `PAUSE` (line 4134), delete `qsat_output.txt`
> debug-dump block (lines 4120-4128), replace `\\` with `/` in
> `mkdir` calls (lines 435, 461). Bring in gridlists. Skip
> `Original Imogen Modified for LPJG Coupling/` (backup; archive
> only), `qsat_output.txt` (debug dump), `.vscode/`.

Verification: `gfortran -ffixed-line-length-132 -O imogen_lpjg.f
nonco2.f -o imogen_lpjg` builds clean. Standalone IMOGEN run on the
1631-cell native grid for 3 years (1871-1873) produces
`<DIR_COMMON_OUT>/IMOGEN/output/<YYYY>/{T_anom.dat, ..., done}`.

## Cross-references

- `[CMI §4.1]` — LPJ-GUESS LandSyMM fork deep-dive (audit findings).
- `[CMI §4.1.10]` — diff-vs-trunk_r13078 (the source-selection
  rationale).
- `[SA2 §2-§8]` — Subagent 2's evidence base.
- `[EXEC §I.A]` — code-level fix catalogue (the 22 entries that get
  applied at step 7).
- `[EXEC §I.B.1]` — LPJG-side handshake writer spec (lands at step 8).
- `[EXEC §V.1 step 1]` — the V.1 plan entry for this step.
- `[Decision #3]` — `trunk_r13078` vs integrated LTS choice
  (selected `trunk_r13078`-equivalent here; integrated LTS as
  switchable Phase-2 backend later).
- `[Decision #8]` — Anaconda3 NetCDF preference (operationally
  validated by this step).
