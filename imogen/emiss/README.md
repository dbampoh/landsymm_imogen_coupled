# `imogen/emiss/` — IMOGEN reference emissions

Reference-emission files (~5 MB ASCII) consumed by:

- The **standalone Fortran IMOGEN** binary at startup, via the
  `FILE_SCEN_EMITS`, `FILE_NON_CO2_VALS`, `FILE_CH4_N2O_EMITS` keys
  in `imogen_settings.txt` (default points at `DKB_dataset_totals/`'s
  RCP8.5 reference triple).
- The **coupled-mode** scenario runs, via per-scenario paths in each
  `runs/<SSP>/imogen_intermediary.ins` (the canonical SSP1-RCP2.6
  config, for example, references
  `imogen/emiss/CMIP6/Co2/co2_pg_emissions_anthropogenic_historical_ssp126_1850_2100.txt`).

**Not committed to git** — acquired via
`tools/fetch_imogen_data.sh --component emiss-reference`.

## Layout (when fully populated, ~5 MB)

```text
imogen/emiss/
├── README.md                                       (committed; this file)
│
├── DKB_dataset_totals/                             (~2.7 MB; RCP8.5-focused
│   ├── co2_emissions_annual_historical_rcp85_allsources.txt
│   ├── nonco2_ch4_n2o_RF_historical_rcp85.txt
│   └── ch4_n2o_annual_historical_rcp85_non_lpjg_simulated.txt
│                                                    Used by the standalone
│                                                    IMOGEN smoke run; per
│                                                    imogen_settings.txt's
│                                                    FILE_SCEN_EMITS etc. keys)
│
├── CMIP5/                                          (~176 KB)
│   └── (per-RCP CMIP5-format emission timeseries)
│
├── CMIP6/                                          (~216 KB)
│   ├── Co2/                                          - co2_pg_emissions_{anthropogenic,natural}_historical_ssp{126,245,370,460,585}_1850_2100.txt
│   ├── CH4-N2O/                                      - ch4_n2o_annual_historical_{anthropogenic,natural}_ssp{126,245,370,460,585}_1850_2100.txt
│   └── Non-Co2-CH4-N2O-RF/                           - nonco2_ch4_n2o_RF_historical_ssp{126,245,370,460,585}.txt
│                                                     (referenced by coupled-mode
│                                                      runs/<SSP>/imogen_intermediary.ins;
│                                                      bug C35's FILE_LPJG_FLUX path
│                                                      override points at one of these
│                                                      natural-NEE timeseries)
│
├── new_emission_data/                              (~2.0 MB; auxiliary tables)
├── rcp_database/                                   (~56 KB; RCP-database extracts)
│
└── (loose files at top level, ~50 KB total:)
    ├── RF_NONCO2_GHG_IS92A.dat
    ├── emiss_co2.dat
    ├── hist_rcp2p6_emiss_ch4_n2o_total_cmip5.txt
    ├── hist_rcp4p5_emiss_ch4_n2o_total_cmip5.txt
    ├── hist_rcp6p0_emiss_ch4_n2o_total_cmip5.txt
    └── hist_rcp8p5_emiss_ch4_n2o_total_cmip5.txt
```

The structure mirrors the predecessor framework's
`Data/Imogen/emiss/`. It was tarballed at step 6 of the rebuild as
`imogen-emiss-reference-v1.0.tar.gz` (closes follow-up F-5).

## How to acquire

```bash
# From the repository root:
tools/fetch_imogen_data.sh --base <DATA_LOCATION> --component emiss-reference

# Or fetch all 6 components in one shot:
tools/fetch_imogen_data.sh --base <DATA_LOCATION>
```

The `tools/imogen_data_manifest.txt` row:

```text
emiss-reference  imogen-emiss-reference-v1.0.tar.gz  77b05df3...  318329  imogen/
```

Compressed tarball ≈ 311 KB (excellent compression — 17× — for the
ASCII content).

## What changed at step 6

Step 4 of the rebuild had staged a flat-3-files layout (just the
RCP8.5 triple from `DKB_dataset_totals/`) at the top level of
`imogen/emiss/`. **Step 6 replaced this with the full
`Data/Imogen/emiss/` tree** (CMIP5/, CMIP6/, DKB_dataset_totals/,
new_emission_data/, rcp_database/, plus the 6 loose files), because
the active coupled-mode `imogen_intermediary.ins` config references
the deeper paths under `CMIP6/{Co2,CH4-N2O,Non-Co2-CH4-N2O-RF}/`.

The standalone-IMOGEN `imogen/code/imogen_settings.txt` was updated
accordingly: its `FILE_SCEN_EMITS`, `FILE_NON_CO2_VALS`, and
`FILE_CH4_N2O_EMITS` keys now point at
`../emiss/DKB_dataset_totals/co2_…txt` etc. (one extra subdir level).

## Format

Each ASCII file is a **2-column text file**: `year value`
(newline-separated). Years run 1850-2100 (251 rows). The Fortran reader
at `imogen_lpjg.f:565-571` accepts this format directly.

For the per-cell pattern files (`patterns/CEN_*_MOD_*/{jan,…,dec}`)
see `imogen/patterns/README.md`. The `emiss/` files are global-mean
timeseries; the `patterns/` files are spatial patterns.

## Provenance

- Sourced from `version_A/.../Data/Imogen/emiss/` (the predecessor
  framework's curated tree) at step 6 of this rebuild (DKB 2026-05-06).
- The CMIP5 set ultimately derives from the IIASA RCP database.
- The CMIP6 set derives from the IIASA SSP CMIP6 database (Riahi et
  al. 2017) processed via the predecessor framework's earlier
  `landsymm_py` runs.
- The `DKB_dataset_totals/` files are project-internal post-processed
  totals.
