# `tools/` — cross-component utilities

Stand-alone scripts that bridge or transform data between the three
model components and the user-facing run setup.

## Implemented tools (live; committed to git)

### `fetch_imogen_data.sh` — IMOGEN reference data acquisition (step 4)

Downloads (or copies from a local directory), SHA256-verifies, and
extracts the GCM-pattern + CRUNCEP base-climatology tarballs into
`imogen/patterns/` and `imogen/CRUNCEP_1960_1989/`. Reads the
authoritative manifest at `tools/imogen_data_manifest.txt`.

Quick recipes:

```bash
# Inspect available components
tools/fetch_imogen_data.sh --list

# Fetch everything from a local sibling directory (workstation case):
tools/fetch_imogen_data.sh --base /path/to/lpj-guess_imogen_landsymm_data

# Fetch only what's needed for a smoke run:
tools/fetch_imogen_data.sh --base ... --component patterns-cmip5 --component cruncep

# Verify a previous fetch:
tools/fetch_imogen_data.sh --base ... --verify-only
```

The data location can also be an `https://` URL prefix once the
tarballs are uploaded to a permanent host (Zenodo / GitHub Releases /
institutional bucket — see `notes/STEP_4.md` §3).

### `imogen_data_manifest.txt` — authoritative tarball manifest

Plain-text, hash-keyed list of the 4 IMOGEN tarballs with SHA256
checksums and exact byte sizes. Used by `fetch_imogen_data.sh` to
verify integrity before extraction. Generated 2026-05-05 from
`version_A/.../IMOGEN-codebase/`. Format:

```text
<component>  <filename>  <sha256>  <size_bytes>  <extract_to>
```

Adding a new GCM pattern requires:

1. `tar -czf …new….tar.gz -C imogen patterns/<NEW_DIR>`
2. `sha256sum …new….tar.gz` and `stat -c %s …new….tar.gz`
3. Append a row to this manifest.

### `cmip6_nc_to_cmip5_ascii.py` — CMIP6 NetCDF → CMIP5 ASCII converter (step 5)

Converts the 5 CMIP6 NetCDF patterns at
`imogen/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/` into CMIP5-style
ASCII directories that the Fortran IMOGEN binary's pattern reader
(`GCM_ANLG`, `imogen_lpjg.f:3270-3274`) consumes directly. Bilinearly
interpolates the source 56×96 lat-lon grid onto the 1631-cell IMOGEN
HadCM3 land grid (from `imogen/code/patterns_gridlist.txt`).

Two operating modes:

```bash
# Single GCM:
python tools/cmip6_nc_to_cmip5_ascii.py \
  --nc imogen/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/mri-esm2-0_patterns.nc \
  --json imogen/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/mri-esm2-0_params.json \
  --gridlist imogen/code/patterns_gridlist.txt \
  --output imogen/patterns/CEN_CMIP6_MOD_MRI-ESM2-0/

# Batch (all 5 GCMs in ~1.6 sec):
python tools/cmip6_nc_to_cmip5_ascii.py \
  --input-dir imogen/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/ \
  --gridlist imogen/code/patterns_gridlist.txt \
  --output-base imogen/patterns/
```

Output:

- `<output>/{jan,feb,...,dec}` — 12 ASCII month files, 1632 lines each
  (1 header + 1631 cells). Same column ordering as CMIP5 (12 columns:
  lon, lat, T, RH15M, U-wind, V-wind, LW, SW, DTEMP_DAY, RAIN, SNOW, PSTAR).
- `<output>/../<MODEL>_ebm.nml` — Fortran namelist with energy-balance
  scalars from the JSON params file.

Three documented mapping caveats (see module docstring +
`notes/STEP_5.md` + `notes/FOLLOWUPS.md` items F-6, F-7, F-8):

- CAVEAT-A: `ql1_patt` units alignment with IMOGEN RH-sensitivity
- CAVEAT-B: wind magnitude split into U/V equally
- CAVEAT-C: total precip lumped into RAIN; SNOW = 0

Dependencies: `xarray`, `scipy`, `numpy` (all in the project Anaconda3
env per Decision #8).

## Planned tools (per `EXECUTION_PLAN.md` Part V)

| Tool | Step | Role |
|---|---|---|
| `imogen_inputs_to_lpjg_format.py` | 13 | Converts the Python Intermediary's wide-format `imogen_inputs_<SSP>.csv` (10 columns, Mt-of-gas/yr) into the four narrow files the Fortran IMOGEN reader expects: `co2_anthro_emissions.txt` (PgC/yr), `ch4_n2o_anthro_emissions.txt` (Tg/yr each), seed `imogen_lpjg_flux.txt` (PgC/yr) and `imogen_lpjg_ch4_n2o_flux.txt` (Tg/yr) for prescribed mode. Implements the unit-checked-adapter discipline of `EXECUTION_PLAN.md` §I.D.2. See Appendix A.2 for sketch. |
| `regrid/` | 16+ | Cleaned-up successor to the framework's `Regrid/`, `FastRegrid/`, `RegridLPJG/` utilities. Likely just `FastRegrid` brought to a working Linux build (case-fix CMakeLists; restore actual OpenMP `#pragma`s). NetCDF input support added for CMIP6 patterns. |
| `ndep_archive/` | (post-v1.0) | Cleaned-up successor to the framework's `NdepFastArchive/` (read/repack the Lamarque-format `Data/Ndep/*.bin` archives). |

## Discipline

Every cross-component tool follows the units-integrity rules of
`EXECUTION_PLAN.md` §I.D — explicit unit assertions at function
boundaries, references to `intermediary_py/src/shared/units.py` and
`lpjguess/include/units.h` for canonical conversion constants, and
schema files for cross-component data paths.

See `CONTRIBUTING.md` for the units-integrity discipline summary.
