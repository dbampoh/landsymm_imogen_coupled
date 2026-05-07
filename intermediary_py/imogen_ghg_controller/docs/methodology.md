# Methodology

This document summarizes the methodological choices across the pipeline. For exhaustive technical detail (including all iteration history and decision rationales), see `HANDOFF.md` at the project root.

## 1. Project objective

Construct internally consistent annual greenhouse-gas emission trajectories covering 1900–2100 for five SSP-RCP scenarios (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5), in the format expected by the IMOGEN climate emulator. Each trajectory has anthropogenic + natural decomposition for CH₄, N₂O, and CO₂.

## 2. Pipeline architecture

Four components in dependency order:

- **A — Anthropogenic agricultural inventory.** IPCC 2019 Refinement Tier 1 applied to FAO production data (1970–2020 historical) and PLUMv2 land-use projections (2020–2100 scenarios). Six sectors: CH₄ enteric fermentation, CH₄ manure management, CH₄ rice cultivation, N₂O managed soils, N₂O manure management, N₂O synthetic fertilizers. Then RCMIP substitution: replace the corresponding sectors in the published RCMIP/CMIP6 anthropogenic trajectory with our independent bottom-up estimates.

- **B — Natural emissions.** LPJ-GUESS DGVM outputs (62,538 grid cells × 120 years historical, × 80 years per scenario) streamed and aggregated to global annual totals. Variables: NEE for CO₂; mch4 for CH₄ wetland; ngases.N2O_soil + N2O_fire for N₂O. CH₄ also corrected with GMB IFW (+112 Mt) and DCC (−23 Mt) terms to capture inland-freshwater and dam/canal contributions.

- **C — Integration & validation.** Anthropogenic + natural per gas, smoothed across the historical-scenario boundary. Three independent comparators built: (1) top-down GMB/GNB/GCB references (historical only), (2) hybrid full-trajectory comparator with budget anchors 1980–2020 (Option B, primary), (3) conventional climate-emulator comparator using RCMIP+FAIR-ERF throughout (Option A, supplementary).

- **D — IMOGEN export.** Reformat integrated trajectories into the per-scenario CSV format expected by IMOGEN.

## 3. Key methodological decisions

### 3.1 CO₂ integration framing

For CO₂ specifically: anthropogenic side = `Emissions|CO2|MAGICC Fossil and Industrial` from RCMIP (NOT the full RCMIP CO₂ which would include AFOLU). Natural side = LPJ-GUESS NEE (which already captures natural land response + ELUC components). The combined total is the atmospheric source = EFOS + NEE ≈ EFOS + ELUC − SLAND.

This was empirically validated against GCB 2025: our 2014–2020 SSP2-4.5 mean = 7.93 Pg C/yr vs GCB partition = 7.60 ± 1.24 Pg C/yr. Gap of +0.33 Pg C/yr is within ±1σ.

### 3.2 Boundary year HIST_END = 2014

The last year before RCMIP scenarios begin diverging. Used throughout plotting and smoothing as the historical/scenario boundary. Empirically verified: scenario spread is exactly 0 at 2014, then jumps to 12.93 Mt CH₄/yr at 2016, 38.8 at 2018, 51.7 at 2019, 65.3 at 2020.

### 3.3 Black historical convention

In all Component C plots, the historical period (1900–2014) is drawn in solid black as a single shared line per layer. Per-scenario coloured lines diverge from 2015. This avoids the visual clutter of five identical lines stacked on top of each other where the last-drawn (SSP5-8.5 purple) dominates.

### 3.4 Δ panel labeling for CO₂

CH₄ and N₂O Δ panels label end-of-century values as percentages of the comparator. CO₂ Δ panels label in absolute Pg C/yr instead, because the comparator denominator can become small or net-negative at 2100 (e.g. SSP1-2.6 RCMIP DAC scenario ≈ −5.7 Gt CO₂/yr) which causes percentage labels to sign-flip and mislead. Pg C/yr is also the natural diagnostic unit for the CO₂ residual since for Option A it equals LPJ-GUESS NEE directly.

### 3.5 Comparator choice — Option B preferred

After building both Option A (conventional, RCMIP+FAIR throughout) and Option B (hybrid with budget anchors), the project adopted **Option B as the primary comparator** because:
1. Historical period grounded in atmospheric-inversion observations rather than model assumptions
2. Semantically consistent CO₂ framing throughout (SLAND correction applied)
3. Same scenario-period story as Option A for CH₄ and N₂O

Option A is retained as a supplementary diagnostic, particularly for reading off the LPJ-GUESS NEE magnitude per scenario directly from the CO₂ Δ panel.

## 4. Validation summary

See `HANDOFF.md` §8.11 for the full cross-comparator headline-findings synthesis.
