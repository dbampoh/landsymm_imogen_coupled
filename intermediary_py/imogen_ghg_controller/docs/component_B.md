# Component B — LPJ-GUESS Natural Emissions

**Location**: `src/component_b_natural/`

## Purpose

Stream the raw LPJ-GUESS DGVM output files (62,538 grid cells × 120 years historical, × 80 years per scenario) and aggregate to global annual totals for CH₄, N₂O, and CO₂ natural emissions.

## Sub-pipelines

### `historical/` — 1901–2020

`lpjg_historical_processing.py` streams the three historical .gz files (`lpjg_cflux.out_historical.gz`, `lpjg_mch4.out_historical.gz`, `lpjg_ngases.out_historical.gz`) using `subprocess.Popen(['zcat', ...], bufsize=65536)`. The files are too large to load fully into RAM and are stored in cell-first ordering (all 120 years per cell, then next cell), so a streaming approach is mandatory.

For each grid cell, area is computed from latitude using:
```
A(lat) = (0.5 × π/180)² × R² × cos(radians(lat))    where R = 6.371e6 m
```

Then values are converted from per-area units to per-cell totals:
- CO₂ cflux: kg C m⁻² yr⁻¹ × A(lat) → kg C cell⁻¹ yr⁻¹
- CH₄ mch4: g CH₄ m⁻² month⁻¹ × A(lat) × 12 → g CH₄ cell⁻¹ yr⁻¹
- N gases: kg N ha⁻¹ yr⁻¹ × (A(lat) / 10000) → kg N cell⁻¹ yr⁻¹

Then summed across all cells for each year, then converted to project-standard units (Pg C/yr for CO₂; Tg CH₄/yr; Tg N/yr).

`lpjg_historical_plotting.py` produces a 4-panel publication-quality figure showing historical trends with running means and budget references overlaid.

### `scenarios/` — 2021–2100, five SSP-RCP scenarios

`lpjg_scenario_processing.py` does the same streaming for each of the five scenario directories (`ssp1_rcp26`, `ssp2_rcp45`, etc.). Output is per-scenario rows in `lpjg_*_annual_scenarios.csv`.

### `full_trajectory/` — combined CH₄ helper + extended plot

`lpjg_combined_and_fair_processing.py` produces:
- `lpjg_ch4_combined_annual.csv` and `_scenarios.csv`: LPJ wetland CH₄ + GMB IFW correction (+112 Mt) − GMB DCC correction (−23 Mt). The combined natural CH₄ trajectory used downstream by Component C.
- `fair_erf_natural_baseline.csv`: extracted from `inputs/fair_erf/natural.csv`. Used as the "constant-natural" reference in Components C comparators.

`lpjg_historical_scenario_plotting.py` produces the 1901–2100 extended-trajectory plot showing all three gases with five scenarios after 2020.

## Key outputs (from Component B)

- `outputs/component_b/data/lpjg_co2_annual.csv` and `_scenarios.csv` — used by Component C
- `outputs/component_b/data/lpjg_ch4_combined_annual.csv` and `_scenarios.csv` — used by Component C
- `outputs/component_b/data/lpjg_n2o_annual.csv` and `_scenarios.csv` — used by Component C
- `outputs/component_b/data/fair_erf_natural_baseline.csv` — used by Component C comparators
- `outputs/component_b/figures/`: 2 publication-quality plots
- `outputs/component_b/summaries/`: budget comparison + scenario summary text files

## Validation against budget papers

The `lpjg_budget_comparison.txt` summary documents agreement with GMB 2025 for the 2010-2019 period:
- CH₄: LPJ wetland mean ≈ 153 Tg (within GMB lower bound of 116-189)
- N₂O soil mean ≈ 13.0 Tg N (within GNB range)
- CO₂ NEE mean ≈ -2.5 Pg C/yr (within GCB SLAND range of 2.8 ± 0.7)

The `lpjg_grid_diagnostics.txt` documents the cell count, total land area, and grid coverage for sanity-checking.
