# `imogen/emiss/` — IMOGEN-side reference emission files

Small ASCII reference emission files (~20 KB total) consumed by the
Fortran IMOGEN binary at startup. **Not committed to git** —
acquired via the same fetch infrastructure as the patterns, OR
manually copied from the predecessor framework for development.

## Files (when fully populated)

| File | Size | What it is | Settings key |
|---|---:|---|---|
| `co2_emissions_annual_historical_rcp85_allsources.txt` | 3.8 KB | annual CO2 emissions 1850–2100 (RCP8.5) in PgC/yr | `FILE_SCEN_EMITS` |
| `nonco2_ch4_n2o_RF_historical_rcp85.txt` | 3.8 KB | annual non-CO2 (CH4+N2O) radiative forcing 1850-2100 in W/m² | `FILE_NON_CO2_VALS` |
| `ch4_n2o_annual_historical_rcp85_non_lpjg_simulated.txt` | 6.3 KB | annual CH4+N2O emissions 1850-2100 (non-LPJG-simulated portion) | `FILE_CH4_N2O_EMITS` |

These files were originally at
`version_A/.../IMOGEN-codebase/emiss/{DKB_dataset_totals,new_emission_data}/`
(predecessor framework). Step 4 of the unified-codebase rebuild
copies them into `imogen/emiss/` for the standalone smoke run.

## Acquisition

For step-4 development the files are simply copied from the
`version_A` source on the workstation:

```bash
SRC="/path/to/version_A/.../IMOGEN-codebase/emiss"
DST="$REPO/imogen/emiss"
mkdir -p "$DST"
cp "$SRC/DKB_dataset_totals/co2_emissions_annual_historical_rcp85_allsources.txt"   "$DST/"
cp "$SRC/DKB_dataset_totals/nonco2_ch4_n2o_RF_historical_rcp85.txt"                  "$DST/"
cp "$SRC/DKB_dataset_totals/ch4_n2o_annual_historical_rcp85_non_lpjg_simulated.txt"  "$DST/"
```

## Future plan

Step 6 of the rebuild plan will:

1. Roll these (and the other RCP/SSP scenarios at
   `emiss/{DKB_dataset_totals,new_emission_data,rcp_database}/`) into
   a 5th tarball: `imogen-emiss-historical-cmip5-v1.0.tar.gz`.
2. Add a corresponding row to `tools/imogen_data_manifest.txt`.
3. The fetch script will then handle them like the patterns + CRUNCEP.

For step 4, only the 3 RCP8.5 reference files needed for the standalone
smoke test are staged, manually.

## Format

Each file is a 2-column text file: `year value` (newline-separated).
Years run 1850-2100 (251 rows). The Fortran reader at
`imogen_lpjg.f:565-571` accepts this format directly.
