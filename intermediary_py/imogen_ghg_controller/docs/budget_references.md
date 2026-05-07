# Budget References — Citation Tables

This document collects the canonical reference values used by the comparators in Component C, along with their source citations and the specific tables/sections they were extracted from.

All values were verified by reading the source PDFs directly via `pdftotext -layout` during Round C4 of the project.

## CH₄ — Global Methane Budget 2025

**Citation**: Saunois, M., et al. (2025). "Global Methane Budget 2000–2020." *Earth System Science Data*, 17, 1873–1958.

**Source location**: Executive summary text, paragraphs covering global total emission for the 2000s, 2010s, and 2020 (atmospheric inversions, top-down).

| Period | Best (Mt CH₄/yr) | Lo | Hi |
|---|---|---|---|
| 2000–2009 | 543 | 528 | 578 |
| 2010–2019 | 575 | 553 | 586 |
| 2020       | 608 | 581 | 627 |

Used in `src/shared/budget_refs.py` as `GMB_CH4_PERIODS`.

## N₂O — Global Nitrogen Budget 2024

**Citation**: Tian, H., et al. (2024). "A comprehensive quantification of global nitrous oxide sources and sinks." *Earth System Science Data*, 16, 2543–2604.

**Source location**: Executive summary, atmospheric inversions section.

| Period | Best (Tg N/yr) | Lo | Hi |
|---|---|---|---|
| 1997       | 15.4 | 13.9 | 16.7 |
| 2010–2019  | 17.4 | 15.8 | 19.2 |
| 2020       | 17.0 | 16.6 | 17.4 |

Convert to Tg N₂O/yr by × 44/28 (one N₂O molecule contains 2 N atoms).

Used in `src/shared/budget_refs.py` as `GNB_N_PERIODS`. Conversion via `gnb_combined_n2o()` helper.

## CO₂ — Global Carbon Budget 2025

**Citation**: Friedlingstein, P., et al. (2025). "Global Carbon Budget 2025." *Earth System Science Data*, 17, 965–1039.

**Source location**: Table 7 (decadal partition).

| Decade | EFOS | σEFOS | ELUC | σELUC | SLAND | σSLAND | Source = EFOS+ELUC−SLAND | σ |
|---|---|---|---|---|---|---|---|---|
| 1960s     | 3.0 | 0.2 | 1.6 | 0.7 | 1.2 | 0.5 | 3.4 | 0.88 |
| 1970s     | 4.7 | 0.2 | 1.4 | 0.7 | 2.0 | 0.8 | 4.1 | 1.08 |
| 1980s     | 5.5 | 0.3 | 1.4 | 0.7 | 1.8 | 0.8 | 5.1 | 1.10 |
| 1990s     | 6.4 | 0.3 | 1.6 | 0.7 | 2.5 | 0.6 | 5.5 | 0.94 |
| 2000s     | 7.8 | 0.4 | 1.4 | 0.7 | 2.8 | 0.7 | 6.4 | 1.06 |
| 2014–2023 | 9.7 | 0.5 | 1.1 | 0.7 | 3.2 | 0.9 | 7.6 | 1.24 |

All values in GtC/yr. Atmospheric-source uncertainty propagated as quadrature sum of component sigmas.

Convert to Mt CO₂/yr by × 44/12 × 1000 = 3666.67.

Used in `src/shared/budget_refs.py` as `GCB_PARTITION`. Conversion via `gcb_atmospheric_source_co2()` helper.

## FAIR-ERF natural baseline

**Citation**: Smith, C. J., et al. (2018). "FAIR v1.3: a simple emissions-based impulse response and carbon cycle model." *Geoscientific Model Development*, 11, 2273–2297.

**Source file**: `inputs/fair_erf/natural.csv` — bundled with the FAIR climate emulator distribution.

Provides the natural-emission baseline for CH₄ and N₂O used by FAIR. Held constant after 2005 (last calibration year). Used in Component C comparators as the "constant-natural" reference. For CO₂ specifically, FAIR_natural is set to 0 — FAIR's internal carbon cycle computes the land sink endogenously rather than ingesting it as forcing.

## RCMIP Phase 2 emissions

**Citation**: Nicholls, Z., et al. (2020). RCMIP Phase 2. https://rcmip.org/

**Source file**: `inputs/rcmip/rcmip-emissions-annual-means-v5-1-0.csv`

Used for:
- `Emissions|CH4` and `Emissions|N2O` (full anthropogenic) for the conventional/hybrid comparators
- `Emissions|CO2|MAGICC Fossil and Industrial` (EFOS-only) as the anthropogenic side of our integrated CO₂

Historical (1750-2014) is annual; scenario data (2015-2100) is reported every 5 years and linearly interpolated to dense annual coverage by `rcmip_co2_processing.py`.
