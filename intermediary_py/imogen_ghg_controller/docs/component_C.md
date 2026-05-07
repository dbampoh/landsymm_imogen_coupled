# Component C — Integration & Validation

**Location**: `src/component_c_integration/`

## Purpose

Assemble integrated trajectories (anthropogenic + natural) per gas and validate them against three independent comparator constructions.

## Scripts (in execution order)

### Step 1 — `rcmip_co2_processing.py`
Extracts `Emissions|CO2|MAGICC Fossil and Industrial` (= EFOS) for World region from RCMIP Phase 2. Splices historical (1750-2014, annual) with scenario (2015-2100, 5-yearly) and linearly interpolates to dense annual coverage. Writes `outputs/component_c/data/rcmip_co2.csv`.

EFOS-only is used (not full RCMIP CO₂) because LPJ-GUESS NEE already includes the AFOLU/ELUC component. Combining EFOS + NEE gives the "atmospheric source" quantity that matches GCB's `EFOS + ELUC − SLAND` partition.

### Step 2 — `integrated_emissions_processing.py`
Combines anthropogenic + natural per gas:
- CH₄: `rcmip_substitution_ch4.csv` "New_total" + `lpjg_ch4_combined_annual_scenarios.csv` "CombinedDCC_TgCH4_best"
- N₂O: `rcmip_substitution_n2o.csv` "New_total" + `lpjg_n2o_annual_scenarios.csv` "N2O_soil_TgN2O + N2O_fire_TgN2O"
- CO₂: `rcmip_co2.csv` "EFOS_MtCO2" + `lpjg_co2_annual_scenarios.csv` "NEE_PgC × 44/12 × 1000"

Writes `integrated_emissions_{ch4,n2o,co2}.csv` (1005 rows each, 9 cols including `Total_Mt`, `Default_total_Mt = RCMIP_total + FAIR_natural`).

`integrated_emissions_plotting.py` produces a 6-panel figure with top-row trajectories (decomposition layers per scenario) and bottom-row Δ panels showing `Total − Default_total`.

### Step 3 — `external_comparators_processing.py` and `_plotting.py`
The first comparator: top-down GMB 2025 / GNB 2024 / GCB 2025 atmospheric-inversion or partition values. Historical period only (atmospheric inversions cannot be projected). Period values verified by reading the budget paper PDFs directly via `pdftotext -layout`.

### Step 4 — `hybrid_comparator_processing.py` and `_plotting.py` (Option B, primary)
Stitches the three time periods:
- 1900–1979: RCMIP_total + FAIR-ERF (with SLAND correction for CO₂)
- 1980–2020: linear interpolation between budget anchor years (CH₄: 2005/2015/2020; N₂O: 1997/2015/2020; CO₂: 1965/1975/1985/1995/2005/2018)
- 2021–2100: RCMIP_total + FAIR-ERF continued

5-year linear blends at segment boundaries to avoid step discontinuities.

For CO₂ specifically, a SLAND correction is applied to the RCMIP+FAIR baseline outside the budget-anchored region so the comparator stays semantically consistent throughout (always representing "atmospheric source"). SLAND is interpolated annually from GCB Table 7 decadal values, ramped from 0 at 1900 to 1.2 GtC/yr at 1965 (pre-industrial natural land cycle in approximate balance), and held constant at 3.2 GtC/yr after 2018.

### Step 5 — `conventional_comparator_processing.py` and `_plotting.py` (Option A, supplementary)
The simpler comparator: RCMIP_total + FAIR-ERF natural baseline throughout the full 1900-2100 window with NO observation anchoring. Represents what conventional climate emulators (FAIR/MAGICC) would assume the integrated total to be.

For CO₂, this comparator's residual = LPJ-GUESS NEE itself (since EFOS = RCMIP_total for CO₂ and FAIR_natural=0 by FAIR-ERF convention for CO₂). So the CO₂ Δ panel directly reads off the LPJ-GUESS land sink magnitude per scenario.

## Plot conventions

All Component C plots use:
- Black historical (1900–2014) drawn once as a single line
- Per-scenario colours (IPCC AR6 standard) from 2015
- `HIST_END = 2014` boundary
- Δ panel labels at 2100: percent for CH₄/N₂O, absolute Pg C/yr for CO₂ (to avoid sign-flip from small denominators)

## Key outputs

- 13 CSVs in `outputs/component_c/data/`
- 4 figures in `outputs/component_c/figures/`
- 4 summary text files in `outputs/component_c/summaries/`

## Comparator choice — Option B preferred

After building both, **Option B (hybrid) is the project's primary comparator**. See `methodology.md` §3.5 and `HANDOFF.md` §8.10 for the full reasoning.
