# Build instructions — LandSyMM-IMOGEN coupled model v1.0

This document covers the workstation Linux build. The cluster (KIT
IMK-IFU `owl`) build instructions land at step 16; they are largely
the same plus the SLURM module-load preamble.

## Quick start (workstation)

```bash
# Clone
git clone git@github.com:dbampoh/landsymm_imogen_coupled.git
cd landsymm_imogen_coupled

# One-liner: launches the full pipeline (build + intermediary + adapter + run)
scripts/run_coupled.sh                         # smoke; SSP1-2.6; prescribed mode
scripts/run_coupled.sh --backbone intermediary-py
```

The launcher is idempotent: re-run it any time and steps that are
already complete are skipped.

## What the launcher actually does

`scripts/run_coupled.sh` walks through 7 steps:

1. **Build LPJ-GUESS** if `lpjguess/build/guess` is missing.
   Uses Anaconda3 NetCDF if available (Decision #8); falls back to
   system NetCDF otherwise (likely fails on Ubuntu 22+; see
   "Why Anaconda3 NetCDF" below).
2. **Run the Python Intermediary** (`intermediary_py/imogen_ghg_controller`)
   if `--backbone intermediary-py`. Skipped for the static-iiasa default.
3. **Run the Python → LPJG-format adapter** if `--backbone intermediary-py`.
4. **Bootstrap LPJG-↔-IMOGEN handshake directory** with placeholder
   `imogen_lpjg.txt` + `done` files (F-10 deadlock workaround per step 9
   findings; until F-12 multi-pass design lands).
5. **Clean stale per-year IMOGEN engine output dirs**.
6. **Launch `./guess -input imogencfx main.ins`** in the scenario's run dir.
7. **Collect summary** of engine + LPJG outputs produced.

Every step prints to a date-stamped log at `logs/run_coupled_<SCENARIO>_<TS>.log`.

## Why Anaconda3 NetCDF (Decision #8)

The user's workstation (Ubuntu 22+) has a known ABI mismatch in the
native `libnetcdf-dev` chain: `libhdf5_serial.so.310` has an
undefined reference to `curl_global_init@CURL_OPENSSL_4` because the
Ubuntu chain ships an OpenSSL-built libhdf5 paired with a GnuTLS-built
libcurl. Linking LPJ-GUESS against this fails at the link stage.

Anaconda's conda-forge stack (`libnetcdf.so.19`, `libhdf5.so.310`,
`libcurl.so.4` — all OpenSSL-built or all GnuTLS-built) is
ABI-consistent and links cleanly.

Per Decision #8 in `EXECUTION_PLAN.md`, **Anaconda3 NetCDF is the
preferred build environment for the user's workstation.** The
launcher detects it via:

1. `--anaconda3-prefix <path>` flag (explicit override)
2. `$CONDA_PREFIX` (active conda env)
3. `$ANACONDA_PREFIX` (set in some shells)
4. `/home/$USER/anaconda3` (common default install)

If none found, the launcher prints a warning and falls back to system
NetCDF (which will probably fail at link).

## Manual build (without the launcher)

If you need to build LPJ-GUESS by hand (e.g., debugging the build
itself):

```bash
cd lpjguess/
mkdir -p build && cd build

# With Anaconda3 NetCDF:
ANACONDA3=/home/$USER/anaconda3   # or wherever your conda lives
cmake \
  -DCMAKE_PREFIX_PATH="$ANACONDA3" \
  -DNETCDF_INCLUDE_DIR="$ANACONDA3/include" \
  -DNETCDF_C_LIBRARY="$ANACONDA3/lib/libnetcdf.so" \
  ..

# Or, with system NetCDF (Ubuntu 22+ likely fails):
cmake ..

make -j$(nproc)
./runtests   # 162 unit tests; should all pass
```

After the build, `lpjguess/build/guess` is the LPJG-IMOGEN coupled-mode
binary, and `lpjguess/build/runtests` is the unit-test binary.

## Manual intermediary_py setup

```bash
cd intermediary_py/imogen_ghg_controller

# Inputs: 7 symlinks to version_A's FULL/inputs/<subdir>
ln -sfn /path/to/version_A/.../FULL/inputs/edgar          inputs/edgar
ln -sfn /path/to/version_A/.../FULL/inputs/fao            inputs/fao
ln -sfn /path/to/version_A/.../FULL/inputs/fair_erf       inputs/fair_erf
ln -sfn /path/to/version_A/.../FULL/inputs/lpjg           inputs/lpjg
ln -sfn /path/to/version_A/.../FULL/inputs/plum           inputs/plum
ln -sfn /path/to/version_A/.../FULL/inputs/rcmip          inputs/rcmip
ln -sfn /path/to/version_A/.../FULL/inputs/reference_pdfs inputs/reference_pdfs

# Verify
python3 run_all.py --dry-run    # should report 43/43 steps registered

# Full run (takes ~9 min on workstation; ~25-40 min with plots)
python3 run_all.py --skip-plots
```

## Manual adapter

```bash
python3 tools/imogen_inputs_to_lpjg_format.py \
    --input  intermediary_py/imogen_ghg_controller/outputs/imogen_inputs/imogen_inputs_SSP1-2.6.csv \
    --output runs/SSP1-2.6/inputs/
```

This produces 4 narrow ASCII files at `runs/SSP1-2.6/inputs/` that
match the Fortran IMOGEN engine's format expectations.

## Verifying the build

After the build, the launcher's startup banner prints:
- Anaconda3 prefix detected (or "(none detected)")
- Active conventions (NEE, units, year indexing, cell area, coupling
  mode)
- Paths (ROOT, RUN_DIR, GUESS_BIN, ANACONDA3_PREFIX, LOG_FILE)

Verify by running with `--smoke` (the v1.0 default):

```bash
scripts/run_coupled.sh
```

Expected: completes step 1 (build) + steps 4-5 (bootstrap + cleanup),
launches LPJ-GUESS, IMOGEN engine produces ~32 per-year directories
at `runs/SSP1-2.6/Common-directory/IMOGEN/output/<YYYY>/` (T_anom,
P_anom, SW_anom, DTEMP_anom, Rh_anom, W_anom, WET, CO2, dtemp_o,
fa_ocean — 10 files per year), then deadlocks on the year-N+1 handshake
poll (F-10 architectural deadlock; expected in v1.0; resolution at F-12).

## Cluster build (placeholder)

To be filled in at step 16 with the KIT IMK-IFU `owl` cluster
specifics. Likely involves: `module load gcc/14 cmake/3.29
netcdf-c/4.9 netcdf-fortran/4.6 openmpi/5.0` then the same cmake
+ make. The Anaconda3 preference is workstation-specific; on the
cluster, the module-loaded NetCDF should be ABI-consistent.

## Troubleshooting

### `libhdf5_serial.so.310: undefined reference to curl_global_init@CURL_OPENSSL_4`

Ubuntu native `libnetcdf-dev` ABI mismatch. Use Anaconda3 NetCDF;
see "Why Anaconda3 NetCDF" above.

### `cmake: command not found`

Install via `apt install cmake` or `conda install cmake`.

### `gcc: command not found` or `Cannot link with gfortran`

Install via `apt install build-essential gfortran` or `conda install
gcc gfortran`.

### `ImportError: No module named pandas` (when running intermediary_py)

The launcher's step 2 doesn't strictly need a venv if the system
Python has the deps. Install with `pip install -r requirements.txt`
or use the `intermediary_py/imogen_ghg_controller/.venv/` setup that
the launcher creates if missing.

### Engine deadlocks at the polling loop

This is **expected in v1.0** (F-10 architectural mismatch). The
engine produces correct climate output; LPJG main loop never enters.
For a v1.0-functional alternative that IS end-to-end, use
`-input imogen` (loose mode) directly. End-to-end coupled-loop
verification is gated on F-12 (multi-pass / two-process design;
post-v1.0).

## References

- `EXECUTION_PLAN.md` Decision #8 (Anaconda3 NetCDF preference) and
  V.1 step 14 (this launcher)
- `notes/STEP_1.md` (initial Anaconda3 NetCDF link-failure
  reproduction)
- `notes/STEP_9.md` sec 4.4 (F-10 deadlock empirical findings)
- `notes/FOLLOWUPS.md` F-10 + F-12 (architectural caveats + Phase-2
  resolution)
- `scripts/run_coupled.sh -h` (full launcher help)
