# `inputs/` — Raw input data

This directory is **gitignored** because the raw data is large (~1.5 GB total, dominated by LPJ-GUESS .gz files). Before running the pipeline, populate this directory as documented below.

The pipeline expects the following layout:

```
inputs/
├── fao/                 ← FAOSTAT bulk-download CSVs
│   ├── Production_Crops_Livestock_E_All_Data.csv
│   ├── Emissions_Totals_E_All_Data.csv
│   └── Inputs_FertilizersNutrient_E_All_Data.csv
│
├── plum/                ← PLUMv2 land-use scenario outputs
│   ├── plum_crop_s1.csv
│   ├── Livestock_counts.txt        ← extracted from Livestock_counts.zip (~1 GB)
│   ├── rice_cult_plum_scen_using_plum_irrig_optA.zip
│   └── rice_cult_plum_scen_using_plum_irrig_optB.zip
│
├── lpjg/                ← LPJ-GUESS DGVM outputs (~1.5 GB)
│   ├── historical/
│   │   ├── lpjg_cflux.out_historical.gz
│   │   ├── lpjg_mch4.out_historical.gz
│   │   └── lpjg_ngases.out_historical.gz
│   └── scenarios/
│       ├── ssp1_rcp26/{cflux,mch4,ngases}.out_ssp1rcp26.gz
│       ├── ssp2_rcp45/...
│       ├── ssp3_rcp70/...
│       ├── ssp4_rcp60/...
│       └── ssp5_rcp85/...
│
├── rcmip/               ← RCMIP Phase 2 emissions
│   └── rcmip-emissions-annual-means-v5-1-0.csv
│
├── fair_erf/            ← FAIR-ERF natural baseline
│   └── natural.csv
│
├── edgar/               ← EDGAR sector emission inventories (benchmark + RCMIP proportioning)
│   ├── EDGAR_CH4_1970_2024.xlsx       ← NEW: benchmark/proportioning, 16 of 17 EDGAR-using scripts
│   ├── EDGAR_N2O_1970_2024.xlsx       ← NEW: benchmark/proportioning, 16 of 17 EDGAR-using scripts
│   ├── essd_ghg_data_emiss.xlsx       ← OLD: required by n2o_synfert_processing.py only
│   └── IEA_EDGAR_CO2_1970_2024.xlsx   ← optional: not currently used by any pipeline script
│
└── reference_pdfs/      ← optional, for reader convenience
    ├── 19R_V4_Ch05_Cropland.pdf
    ├── 19R_V4_Ch10_Livestock.pdf
    ├── 19R_V4_Ch11_Soils_N2O_CO2.pdf
    ├── V4_10_Ch10_Livestock.pdf
    ├── essd-17-1873-2025_GMB.pdf
    ├── essd-16-2543-2024_GNB.pdf
    └── essd-17-965-2025_GCB.pdf
```

## Acquisition

### Public data sources

- **FAOSTAT** (https://www.fao.org/faostat/en/#data) — download the three bulk-download CSVs listed above. They are wide-format with one row per (Country × Item × Element × Unit) and one column per year.
- **RCMIP** (https://rcmip.org/) — download `rcmip-emissions-annual-means-v5-1-0.csv` from the Phase 2 release. The SHA-256 should match the one bundled with the FAIR climate emulator distribution.
- **FAIR-ERF natural baseline** — `natural.csv` is bundled with the FAIR climate emulator (https://github.com/OMS-NetZero/FAIR). It contains FAIR's natural-emission baseline for CH₄ and N₂O.

### Project-internal data

- **PLUMv2 scenario activity data** — obtain from the project modeller. These are SSP-RCP-driven land-use projections used as activity data for the Component A scenario projections.
  - `plum_crop_s1.csv` — per-country crop area / livestock projections (5-yearly 2025-2100, all 5 SSP-RCP scenarios)
  - `Livestock_counts.txt` — used by `00_scenario_livestock_anchor.py`. Originally distributed inside `Livestock_counts.zip` (~270 MB compressed → ~1 GB uncompressed). Extract with `unzip Livestock_counts.zip` after placing the zip in `inputs/plum/`. NOTE: the livestock anchor script needs ~6-8 GB of free RAM to process this file; running on a memory-constrained system may fail.
  - `rice_cult_plum_scen_using_plum_irrig_optB.zip` — used by the CH4 rice scenario (Option B irrigation methodology). Contains per-country rice cultivation projections with IrrigAmount field used for water-regime classification.

- **LPJ-GUESS .gz files** — obtain on request from the modeller. These are the raw Dynamic Global Vegetation Model outputs covering 62,538 grid cells × 120 years (historical) and × 80 years (each scenario). File format is whitespace-separated text, gzip-compressed; one column per output variable, one row per (grid_cell × year).

- **EDGAR sector emission inventories** — used by 17 Component A scripts as a benchmark and for sector/total proportioning in scenario plots:
  - `EDGAR_CH4_1970_2024.xlsx` and `EDGAR_N2O_1970_2024.xlsx` — the EDGAR 2025 release covering 1970-2024. Use the `IPCC 2006` sheet with header at row 9. Used by 16 of 17 EDGAR-touching scripts. Available from https://edgar.jrc.ec.europa.eu/.
  - `essd_ghg_data_emiss.xlsx` — the older ESSD release. Used **only** by `n2o_synfert_processing.py` because it has the 4D11 "Synthetic Fertilizers" sub-category that the new release aggregates into 3.C.4 + 3.C.5 (= all agricultural managed soils, ~64% of total N2O). Required for the `EDGAR_GgN2O` benchmark column on `n2o_synfert_global.csv`. Use the `data_totals` sheet.
  - `IEA_EDGAR_CO2_1970_2024.xlsx` — currently NOT used by any pipeline script. Included for forward compatibility if a CO2 benchmark plot is ever added.

### Reference PDFs

These are not required at runtime — the pipeline does not parse them. They are kept here for reader / reviewer convenience. If you do not have them, the pipeline will still run.

## Disk space

| Source | Size |
|---|---|
| FAOSTAT CSVs | ~150 MB |
| PLUMv2 outputs (incl. extracted Livestock_counts.txt) | ~1 GB |
| LPJ-GUESS .gz files | ~1.5 GB |
| RCMIP CSV | ~50 MB |
| FAIR natural baseline | <1 MB |
| EDGAR xlsx files (4) | ~65 MB |
| Reference PDFs | ~50 MB |
| **Total** | **~2.8 GB** |

## Verification

After populating `inputs/`, confirm the layout with:

```bash
python -c "
from src.shared.paths import (
    RCMIP_CSV, FAIR_ERF_CSV, LPJG_HIST_DIR, LPJG_SCEN_DIR,
    EDGAR_CH4_NEW, EDGAR_N2O_NEW, EDGAR_OLD_ESSD,
    PLUM_LIVESTOCK_TXT,
)
import os
print(f'RCMIP_CSV:         exists={os.path.isfile(RCMIP_CSV)}')
print(f'FAIR_ERF_CSV:      exists={os.path.isfile(FAIR_ERF_CSV)}')
print(f'LPJG hist:         {len(list(LPJG_HIST_DIR.glob(\"*.gz\")))} .gz files')
print(f'LPJG scen:         {sum(len(list(d.glob(\"*.gz\"))) for d in LPJG_SCEN_DIR.iterdir())} .gz files')
print(f'EDGAR CH4 (new):   exists={os.path.isfile(EDGAR_CH4_NEW)}')
print(f'EDGAR N2O (new):   exists={os.path.isfile(EDGAR_N2O_NEW)}')
print(f'EDGAR ESSD (old):  exists={os.path.isfile(EDGAR_OLD_ESSD)}')
print(f'PLUM Livestock:    exists={os.path.isfile(PLUM_LIVESTOCK_TXT)}')
"
```

Expected output:
```
RCMIP_CSV:         exists=True
FAIR_ERF_CSV:      exists=True
LPJG hist:         3 .gz files
LPJG scen:         15 .gz files
EDGAR CH4 (new):   exists=True
EDGAR N2O (new):   exists=True
EDGAR ESSD (old):  exists=True
PLUM Livestock:    exists=True
```
