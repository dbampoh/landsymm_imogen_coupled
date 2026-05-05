# `data/` — reference data

Small reference data is committed to git. Large data (gridded LU,
gridded climate, gigabyte-scale Lamarque archives, etc.) is **not
committed** but is documented in `data/DATA.md` (created at step 6
of the rebuild plan) so any user / collaborator / successor knows
how to obtain it.

## Layout (post-step-6)

```
data/
├── DATA.md                               How to obtain large data
│                                          (HILDA+, PLUMv2, FAO,
│                                          RCMIP, FAIR, EDGAR, CMIP6,
│                                          NOAA GMD / AGAGE).
├── soil/
│   └── soilmap_center_interpolated.remapv10_old_62892_gL.dat
│                                          (3.5 MB; in-repo)
├── gridlist/
│   ├── gridlist_in_62892_and_climate.txt The active full 62 538-cell
│   │                                      gridlist for production runs.
│   ├── gridlist_test2.txt                4-cell smoke-test gridlist.
│   ├── gridlist_test480.txt              480-cell parallel-test gridlist.
│   ├── gridlist_hilda+.txt               62 864-cell HILDA+-style.
│   └── ...                                see EXECUTION_PLAN.md §V.1
│                                          step 6 for full inventory.
├── concentrations/                       Reference CO2/CH4/N2O.
│   ├── EPA/
│   │   ├── ghg-concentrations_co2.csv
│   │   ├── ghg-concentrations_ch4.csv
│   │   └── ghg-concentrations_n2o.csv
│   └── (large IIASA XLSX bundles documented in DATA.md)
├── emissions/
│   └── (small reference tables; large IIASA tables in DATA.md)
├── ndep/
│   └── (Lamarque .bin archives gitignored; see DATA.md)
├── lu/
│   ├── (legacy concatenated `Data/LU/SSP1_RCP26_concatenated/` —
│   │    fallback for Option C of LU strategy)
│   └── (new landsymm_py outputs at /media/bampoh-d/lpjg_input/...
│        documented in DATA.md and accessed via symlink at
│        runtime; not committed)
└── observations/                         For step-17 validation
    ├── noaa_gmd_co2_ch4_n2o_monthly.csv
    └── agage_ch4_n2o_monthly.csv
```

## Discipline

Per `EXECUTION_PLAN.md` §I.D.1, every numeric data file in `data/`
carries a units header (or `.meta.yaml` sidecar) declaring columns,
units, sign conventions, spatial and temporal resolution, year
coverage. When adding a new file, declare its schema. When reading
it, validate against the schema.

## Sources

The full source-of-truth table for every input dataset is in
`EXECUTION_PLAN.md` §I.C and the master doc `[CMI §5]`. Highlights:

- **HILDA+ v2** — Winkler et al. 2021 (ESSD) + the user's
  `landsymm_py` harmonisation pipeline.
- **PLUM v2** outputs — delivered by the PLUM modelling team based
  on the user's prior LPJ-GUESS Stage I yield surfaces.
- **FAOSTAT, RCMIP Phase 2 v5.1.0, FAIR ERF v1.3, EDGAR 2025** — public
  downloads (URLs in DATA.md).
- **GCM patterns** — the user's existing `Common-directory/IMOGEN-codebase/patterns/`
  set: 34 CMIP5 ASCII + 1 CMIP3 legacy + 5 CMIP6 NetCDF (converted
  via `tools/cmip6_nc_to_cmip5_ascii.py` to CMIP5 ASCII format the
  Fortran reader consumes; output in `imogen/patterns/CEN_CMIP6_MOD_<gcm>/`).
- **CRUNCEP base climatology** — Viovy 2018; in
  `imogen/CRUNCEP_1960_1989/`.

## Provenance

For reproducibility, `data/DATA.md` will record SHA-256 checksums
and download URLs for each public dataset, and modeller-of-record
for the project-internal datasets (PLUM team, the user's prior
landsymm_py runs, etc.).
