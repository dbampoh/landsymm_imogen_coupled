# `lpjguess/` — LPJ-GUESS LandSyMM fork

The LPJ-GUESS dynamic global vegetation model with the LandSyMM-fork
modifications. Imported at **step 1** of the rebuild plan
(`EXECUTION_PLAN.md` §V.1; see `notes/STEP_1.md` for verification
record). The directory holds 26 MB of source across 16 top-level
items.

## Provenance

Imported from the user's standalone LandSyMM-LPJ-GUESS at
`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`
(the predecessor `version_A`/`version_B` framework's
`Integrations/trunk/trunk_r13078/` was deliberately NOT used — it
carries an `exit(200);` regression at `modules/imogencfx.cpp:483` plus
five cosmetic comment touches that the standalone LandSyMM-LPJ-GUESS
does not have; see `[CMI §4.1.10]`).

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

The IMOGEN integration with LPJ-GUESS is in five `modules/` files
that get **statically linked** into the same `./guess` binary (no
separate IMOGEN process; no IMOGEN/COUPLED CMake flag — the IMOGEN
sources are listed unconditionally in `modules/CMakeLists.txt:36-41,
76-81`):

| File | Role |
|---|---|
| `imogen_input.cpp/h` | `-input imogen` loose-coupling: reads pre-generated IMOGEN ASCII climate from disk |
| `imogencfx.cpp/h` | `-input imogencfx` tight-coupling: invokes `RUN_IMOGEN_ENGINE()` in-process; consumes `param "file_temp"`, `file_prec`, `file_insol`, `file_wetdays`, `file_dtr`, `file_co2` from the ins file |
| `climatemodel.cpp/h` | The in-process IMOGEN engine (C++ port of the Fortran's pattern-scaling, year loop, ocean-CO2 box model, FAIR ERF) |
| `imogenlogger.cpp/h` | Singleton text logger used by the engine |
| `intermediary.cpp/h` | `IMOGENConfig::*` namespace globals shared across the engine + LPJG |

Per `[CMI §3.7]` and the rebuild plan, these will be modified at:

- **Step 7:** apply the seven coupling break-point fixes
  (`exit(200);` removal — already absent in the imported source;
  `IMOGEN/ouput/` typo in the ins file; polling-loop guards in
  `climatemodel.cpp:330-350`; `ndep.getndep` uncomment at
  `imogen_input.cpp:728`; ...).
- **Step 8:** add a new module `imogenoutput.cpp/h` for the
  LPJG-side handshake writer (annual NEE + wetland CH4 + soil/fire
  N2O global aggregation; writes `imogen_lpjg_flux.txt`,
  `imogen_lpjg_ch4_n2o_flux.txt`, `imogen_lpjg.txt`, `done` files
  in `<DIR_COMMON>/LPJG_main/IMOGEN/`).
- **Step 9.5:** wire up the consumer side for `Rh_anom.dat`,
  `W_anom.dat`, `Tmin_anom.dat`, `Tmax_anom.dat` IMOGEN outputs
  (currently unconsumed by `imogencfx::get_climate_for_gridcell`
  even though `Rh_anom`/`W_anom` ARE produced by the C++ engine —
  see `[CMI §4.3.4a]`); restore the `firemodel == BLAZE`
  incompatibility check at `imogencfx.cpp:792-794`.

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
