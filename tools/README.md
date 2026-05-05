# `tools/` — cross-component utilities

Stand-alone scripts that bridge or transform data between the three
model components and the user-facing run setup.

## Planned tools (per `EXECUTION_PLAN.md` Part V)

| Tool | Step | Role |
|---|---|---|
| `imogen_inputs_to_lpjg_format.py` | 13 | Converts the Python Intermediary's wide-format `imogen_inputs_<SSP>.csv` (10 columns, Mt-of-gas/yr) into the four narrow files the Fortran IMOGEN reader expects: `co2_anthro_emissions.txt` (PgC/yr), `ch4_n2o_anthro_emissions.txt` (Tg/yr each), seed `imogen_lpjg_flux.txt` (PgC/yr) and `imogen_lpjg_ch4_n2o_flux.txt` (Tg/yr) for prescribed mode. Implements the unit-checked-adapter discipline of `EXECUTION_PLAN.md` §I.D.2. See Appendix A.2 for sketch. |
| `cmip6_nc_to_cmip5_ascii.py` | 5 | Converts the 5 CMIP6 NetCDF GCM patterns at `Common-directory/IMOGEN-codebase/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/` into CMIP5-style ASCII month files in `imogen/patterns/CEN_CMIP6_MOD_<gcm>/` so the Fortran IMOGEN reader consumes them transparently. Bilinearly interpolates 56×96 lat-lon grid → 1631-cell IMOGEN HadCM3 land grid. Converts `<gcm>_params.json` to Fortran namelist. See Appendix A.3 for sketch. |
| `regrid/` | 16+ | Cleaned-up successor to the framework's `Regrid/`, `FastRegrid/`, `RegridLPJG/` utilities. Likely just `FastRegrid` brought to a working Linux build (case-fix CMakeLists; restore actual OpenMP `#pragma`s). NetCDF input support added for CMIP6 patterns. |
| `ndep_archive/` | (post-v1.0) | Cleaned-up successor to the framework's `NdepFastArchive/` (read/repack the Lamarque-format `Data/Ndep/*.bin` archives). |

## Discipline

Every cross-component tool follows the units-integrity rules of
`EXECUTION_PLAN.md` §I.D — explicit unit assertions at function
boundaries, references to `intermediary_py/src/shared/units.py` and
`lpjguess/include/units.h` for canonical conversion constants, and
schema files for cross-component data paths.

See `CONTRIBUTING.md` for the units-integrity discipline summary.
