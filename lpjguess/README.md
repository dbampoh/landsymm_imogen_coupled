# `lpjguess/` — LPJ-GUESS LandSyMM fork

The LPJ-GUESS dynamic global vegetation model with the LandSyMM-fork
modifications. Imported at **step 1** of the rebuild plan
(`EXECUTION_PLAN.md` §V.1; see `notes/STEP_1.md` for verification
record). The directory holds 26 MB of source across 16 top-level
items.

## Provenance

Imported from the user's `LandSyMM_LPJ-GUESS/` fork at
`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`.

> **Terminology note**: the user calls this fork the **"integrated
> LTS"** (per their integration-project terminology, which predates
> this coupled-model rebuild). The directory name and the user's
> spoken term refer to the **same artifact**. See `EXECUTION_PLAN.md`
> II.11.0 for the full terminology clarification.

The predecessor `version_A`/`version_B` framework's
`Integrations/trunk/trunk_r13078/` was **deliberately NOT used** for
v1.0 — it carries an `exit(200);` regression at
`modules/imogencfx.cpp:483` plus five cosmetic comment touches that
`LandSyMM_LPJ-GUESS/` does not have; see `[CMI §4.1.10]`. However,
**`trunk_r13078` IS the backport target** for the working paper's
Stage-1/Stage-2 consistency: at the end of Phase-1, the **Backport
Sprint** (follow-up F-11) brings it to functional parity with the
`LandSyMM_LPJ-GUESS/` base by replicating every source-level edit
recorded in `notes/TRUNK_R13078_BACKPORT_LEDGER.md`.

**Maintenance discipline**: every commit that modifies C++ source
under `lpjguess/{framework,modules,libraries,cmake}/` MUST add a
matching entry to `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3
(step-N / commit-hash / file / line range / description /
backport-guidance). Documentation-only edits to `*.md` files and
build artefacts under `build/` are exempt. This discipline keeps
the eventual sprint mechanical instead of archaeological.

**Import excluded:** `build/`, `build_landsymm_imogen/` (build
artefacts, ~39 MB combined); `windows_version/` (Linux-only project
per `[CMI §1.4]`); `reference/~$essdoc.doc` (Word lock file); any
`.vscode/`, `*.swp`, `*.swo`, `.DS_Store`.

**Verified at import:** `grep -n "exit(200)" modules/imogencfx.cpp`
returned no matches — confirming the standalone-fork lineage is the
clean one.

## Build instructions

The build uses **Anaconda3 NetCDF** per Decision #8 of
`EXECUTION_PLAN.md`. Native Ubuntu `libnetcdf-dev` causes a link-time
failure (`libhdf5_serial.so.310: undefined reference to
curl_global_init@CURL_OPENSSL_4`) because the Ubuntu chain ships an
`OpenSSL`-built libhdf5 paired with a `GnuTLS`-built libcurl —
ABI-incompatible. Anaconda's conda-forge stack (`libnetcdf.so.19`,
`libhdf5.so.200`, `libcurl.so.4`) is internally consistent and works
out of the box.

```bash
cd lpjguess
mkdir -p build && cd build
cmake \
  -DCMAKE_PREFIX_PATH=$HOME/anaconda3 \
  -DNETCDF_INCLUDE_DIR=$HOME/anaconda3/include \
  -DNETCDF_C_LIBRARY=$HOME/anaconda3/lib/libnetcdf.so \
  ..
make -j$(nproc)
```

Expected output:
- `build/guess` — the LPJ-GUESS CLI binary (~2.8 MB).
- `build/runtests` — Catch-based unit test binary (~3.4 MB).
- `build/submit.sh` — auto-generated SLURM template
  (Simba/Aurora-style by default).

Verify the linkage:

```bash
ldd build/guess | grep -E "netcdf|hdf5|mpi|curl"
# Should show all libraries from /home/bampoh-d/anaconda3/lib/
# NOT from /lib/x86_64-linux-gnu/
```

Run the unit tests:

```bash
./build/runtests
# Expected: "All tests passed (162 assertions in 25 test cases)"
```

The wrapper that automates this (with conda-env activation) lands at
`scripts/build_all.sh` in step 14.

## Layout

```
lpjguess/
├── CMakeLists.txt           Top-level build config (cmake ≥ 2.8.12.2)
├── cmake/                   Helper modules:
│   ├── FindNetCDF.cmake
│   ├── add_guess_sources.cmake
│   └── add_test_sources.cmake
├── framework/               Core C++ framework: framework.cpp/h,
│                             guess.cpp/h, parameters.cpp/h, archive.cpp/h,
│                             inputmodule.cpp/h, outputmodule.cpp/h,
│                             outputchannel.cpp/h, indata.cpp/h, parallel.cpp/h,
│                             commandlinearguments.cpp/h, etc. (740 KB).
├── modules/                 Process + I/O modules including:
│   ├── demoinput.cpp/h      `-input demo` reference implementation
│   ├── cfinput.cpp/h        `-input cf` standard CF-NetCDF
│   ├── cfxinput.cpp/h       `-input cfx` extended CF-NetCDF (LandSyMM workhorse)
│   ├── firemipinput.cpp/h   `-input firemip` FireMIP variant
│   ├── imogen_input.cpp/h   `-input imogen` loose-coupling
│   ├── imogencfx.cpp/h      `-input imogencfx` tight-coupling
│   ├── climatemodel.cpp/h   In-process IMOGEN engine (linked into ./guess)
│   ├── imogenlogger.cpp/h   IMOGEN logger
│   ├── imogenoutput.cpp/h   LPJG-side handshake writer (added at step 8)
│   ├── intermediary.cpp/h   IMOGENConfig namespace
│   └── (process modules: canexch, vegdynam, soilwater, ...)
├── libraries/               Bundled support: gutil/, plib/, guessnc/
├── command_line_version/
│   └── main.cpp             CLI entry point
├── cru/                     CRU climate I/O sub-module
├── data/
│   ├── env/                 Demo-mode climate ASCII (temp, prec, sun, soil)
│   ├── gridlist/            LPJ-GUESS upstream gridlists
│   └── ins/                 16 upstream ins-files: arctic, crop[c|n|n_luh2],
│                             europe[_cf|_cru|_demo], global[_cf|_cru|_demo|_soiln],
│                             landcover, wetlandpfts
├── tests/                   Catch-based unit test sources (catch.hpp + 9 *_test.cpp)
├── reference/               LPJ-GUESS upstream documentation:
│   ├── guessdoc.doc, guess_guidelines.doc
│   ├── scientific_description.docx, scientific_description.pdf
│   └── releasenotes.txt
├── parallel_version/        5 cluster SLURM/PBS templates: aurora, gimle,
│                             multicore, pbs_legacy, simba (UPSTREAM
│                             reference; the active KIT IMK-IFU `owl` cluster
│                             scripts will land in `../scripts/cluster/` at step 16)
├── benchmarks/              Upstream benchmark suite (3.7 MB)
├── doxygen/                 Doxygen config for code-doc generation
├── readme.txt               Upstream LPJ-GUESS readme
├── LICENCE.TXT              Lund University LPJ-GUESS licence
├── GitlabDockerFile         KIT GitLab CI Docker file
└── README.md                (this file)
```

## Coupling-relevant code

The IMOGEN integration with LPJ-GUESS is in **six** `modules/` files
that get **statically linked** into the same `./guess` binary (no
separate IMOGEN process; no IMOGEN/COUPLED CMake flag — the IMOGEN
sources are listed unconditionally in `modules/CMakeLists.txt`):

| File | Role |
|---|---|
| `imogen_input.cpp/h` | `-input imogen` loose-coupling: reads pre-generated IMOGEN ASCII climate from disk |
| `imogencfx.cpp/h` | `-input imogencfx` tight-coupling: invokes `RUN_IMOGEN_ENGINE()` in-process; consumes `param "file_temp"`, `file_prec`, `file_insol`, `file_wetdays`, `file_dtr`, `file_co2` from the ins file. Owns the `coupling_mode` ins parameter (added at step 8). |
| `climatemodel.cpp/h` | The in-process IMOGEN engine (C++ port of the Fortran's pattern-scaling, year loop, ocean-CO2 box model, FAIR ERF) |
| `imogenlogger.cpp/h` | Singleton text logger used by the engine |
| `imogenoutput.cpp/h` | **LPJG-side handshake writer (added at step 8)**. Registered as `OutputModule "imogenoutput"` via `REGISTER_OUTPUT_MODULE`. Writes per-year `imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt`, `imogen_lpjg.txt`, `done` to `<DIR_COMMON>/LPJG_main/IMOGEN/`. Mode-gated by `IMOGENConfig::coupling_mode`. **F-10 caveat applies for tight mode in v1.0** — see `notes/FOLLOWUPS.md`. |
| `intermediary.cpp/h` | `IMOGENConfig::*` namespace globals shared across the engine + LPJG |

Per `[CMI §3.7]` and the rebuild plan, these have been / will be modified at:

- **Step 7 ✅:** applied the LPJ-GUESS coupling source-level fixes
  (C2/C3 polling-loop guards in `climatemodel.cpp:330-353`; C4
  `ndep.getndep` uncomment at `imogen_input.cpp:728`; cross-reference
  comment in `imogencfx.cpp:895`).
- **Step 8 ✅:** added `imogenoutput.cpp/h` module for the LPJG-side
  handshake writer + `coupling_mode` ins parameter declared in
  `IMOGENConfig` and registered via `imogencfx.cpp` `declare_parameter`.
  **Architectural caveat F-10 documented**: the framework loop's
  per-gridcell-outer / per-day-inner ordering means the writer emits
  per-gridcell-rolling values (not globally-synchronized); v1.0 meets
  the V.1 milestone but the Phase-2 follow-up is to add a runtime
  `framework_loop_mode` parameter that gates an additive year-outer
  code path alongside the existing one (mirroring the LandSyMM-into-LTS
  integration pattern).
- **Step 9.5:** wire up the consumer side for `Rh_anom.dat`,
  `W_anom.dat`, `Tmin_anom.dat`, `Tmax_anom.dat` IMOGEN outputs
  (currently unconsumed by `imogencfx::get_climate_for_gridcell`
  even though `Rh_anom`/`W_anom` ARE produced by the C++ engine —
  see `[CMI §4.3.4a]`); restore the `firemodel == BLAZE`
  incompatibility check at `imogencfx.cpp:792-794`. Plus complete
  the half-scaffolded miscoutput climate-input diagnostic outputs
  (follow-up F-9, opened by step 8).

See the rebuild plan in `EXECUTION_PLAN.md` Part V for the
step-by-step sequence and verification milestones.

## Coupling scope (clarified at step 1)

`imogencfx` (and `imogen_input`) supply LPJ-GUESS with **only the
climate forcings + atmospheric CO2** from IMOGEN. **All other LPJG
inputs** (landcover/cropfracs, fertiliser, irrigation, N-deposition,
soil, popdens for SimFire/BLAZE, fire forcing, NOx/NHx reactive
nitrogen, etc.) flow through the standard LPJ-GUESS input
mechanisms — exactly as they would in a non-coupled `cfx` run.
Per `[CMI §4.1.5]` "Scope of `imogencfx`" subsection. LPJ-GUESS
handles the temporal-resolution mismatch natively (climate
interpolated daily; ndep distributed via `distribute_ndep`; LU/popdens
held constant within year; soil static).

## Cross-references

- `[CMI §4.1]` — full deep-dive on the imported codebase (all 22
  catalogued bug/gap entries against this LPJ-GUESS source).
- `[SA2]` — Subagent 2's 58-KB report at
  `_phase2_findings/02_lpjguess_trunk_r13078.md` is the canonical
  evidence base for the import's structure and the diff-vs-trunk
  analysis.
- `[EXEC §V.1 step 1, §II.11]` — the rebuild-plan step + the
  `trunk_r13078`-vs-integrated-LTS strategic decision.
