# Component D — IMOGEN Input Export

**Location**: `src/component_d_imogen_export/imogen_inputs_export.py`

## Purpose

Reformat the integrated trajectories from Component C into the per-scenario CSV format expected by the IMOGEN climate emulator.

## Outputs

Five per-scenario wide-format CSVs (201 rows × 10 columns each):
- `imogen_inputs_SSP1-2.6.csv`
- `imogen_inputs_SSP2-4.5.csv`
- `imogen_inputs_SSP3-7.0.csv`
- `imogen_inputs_SSP4-6.0.csv`
- `imogen_inputs_SSP5-8.5.csv`

Plus one combined long-format CSV (3,015 rows × 7 columns):
- `imogen_inputs_all_scenarios_long.csv`

All in `outputs/imogen_inputs/`.

## Wide-format schema

| Column | Unit | Description |
|---|---|---|
| `Year` | — | 1900–2100 (201 rows) |
| `CH4_anthro_Mt` | Mt CH₄/yr | Tier-1-substituted anthropogenic CH₄ |
| `CH4_natural_Mt` | Mt CH₄/yr | LPJ-GUESS combined natural CH₄ (wetland + IFW − DCC) |
| `CH4_total_Mt` | Mt CH₄/yr | sum |
| `N2O_anthro_Mt` | Mt N₂O/yr | Tier-1-substituted anthropogenic N₂O |
| `N2O_natural_Mt` | Mt N₂O/yr | LPJ-GUESS natural N₂O (soil + fire) |
| `N2O_total_Mt` | Mt N₂O/yr | sum |
| `CO2_EFOS_Mt` | Mt CO₂/yr | RCMIP fossil + industrial CO₂ |
| `CO2_NEE_Mt` | Mt CO₂/yr | LPJ-GUESS Net Ecosystem Exchange |
| `CO2_total_Mt` | Mt CO₂/yr | atmospheric source = EFOS + NEE |

## Long-format schema

| Column | Description |
|---|---|
| `Year` | 1900–2100 |
| `Scenario` | SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5 |
| `Gas` | CH4, N2O, CO2 |
| `Anthro_Mt` | anthropogenic component |
| `Natural_Mt` | natural component |
| `Total_Mt` | sum |
| `Unit` | "Mt {Gas}/yr" |

## Unit notes

- All values in Mt-of-gas per year (10⁹ kg per year).
- For CO₂, this means Mt CO₂, NOT Mt C — multiply by 12/44 to convert to Mt C.
- For Pg C/yr (the more common unit in carbon-cycle papers), divide CO2_total_Mt by 3666.67 (= 44/12 × 1000).

## Test

`tests/test_imogen_export_schema.py` verifies all six CSVs exist, have correct shape (201×10 wide; 3015×7 long), correct column order, no NaN values, and Year column monotonic 1900-2100.
