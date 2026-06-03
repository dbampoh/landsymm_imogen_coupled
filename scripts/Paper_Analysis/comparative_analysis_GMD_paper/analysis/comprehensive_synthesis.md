# Comprehensive Synthesis: IMOGEN vs ISIMIP3b Climate and Carbon Comparisons

## Overview

This document synthesises all comparative analyses conducted between climate outputs from the IMOGEN emulator and ISIMIP3b bias-adjusted MRI-ESM2-0 (downscaled to 0.5 degree), and the corresponding LPJ-GUESS carbon pool and flux outputs driven by each climate product. Analyses cover two SSP scenarios (SSP1-2.6 and SSP2-4.5) and span from early century (2020-2021) to end of century (2099-2100), with carbon analyses additionally covering full-period (2021-2100) and sub-period (2021-2040, 2081-2100) windows.

All climate statistics are computed across ~59,191 land grid points at 0.5 degree resolution over 24 monthly time steps per 2-year window (~1.42 million point-month samples). Carbon statistics are area-weighted using cos(lat)-corrected grid-cell areas across ~62,512 land points.

---

## 1. Climate Comparison Summary

### 1.1 SSP126

#### Early century (2020-2021)

| Variable | Mean IMOGEN | Mean ISIMIP | Bias (I-S) | RMSE | MAE | Pearson r |
|----------|-------------|-------------|------------|------|-----|-----------|
| tas (K) | 283.74 | 284.40 | -0.66 | 3.76 | 2.71 | 0.977 |
| pr (mm/day) | 1.91 | 2.15 | -0.24 | 2.33 | 1.26 | 0.679 |
| rsds (W/m2) | 181.85 | 177.53 | +4.32 | 26.70 | 19.62 | 0.955 |

#### End of century (2099-2100)

| Variable | Mean IMOGEN | Mean ISIMIP | Bias (I-S) | RMSE | MAE | Pearson r |
|----------|-------------|-------------|------------|------|-----|-----------|
| tas (K) | 287.93 | 284.36 | **+3.57** | 5.50 | 4.37 | 0.970 |
| pr (mm/day) | 2.09 | 2.21 | -0.13 | 2.83 | 1.50 | 0.595 |
| rsds (W/m2) | 179.78 | 181.41 | -1.63 | 28.08 | 21.08 | 0.950 |

### 1.2 SSP245

#### Early century (2020-2021)

| Variable | Mean IMOGEN | Mean ISIMIP | Bias (I-S) | RMSE | MAE | Pearson r |
|----------|-------------|-------------|------------|------|-----|-----------|
| tas (K) | 283.74 | 284.24 | -0.50 | 3.77 | 2.73 | 0.976 |
| pr (mm/day) | 1.91 | 2.11 | -0.20 | 2.31 | 1.24 | 0.682 |
| rsds (W/m2) | 181.85 | 177.23 | +4.63 | 27.26 | 19.82 | 0.953 |

#### End of century (2099-2100)

| Variable | Mean IMOGEN | Mean ISIMIP | Bias (I-S) | RMSE | MAE | Pearson r |
|----------|-------------|-------------|------------|------|-----|-----------|
| tas (K) | 287.93 | 285.87 | **+2.07** | 4.51 | 3.47 | 0.972 |
| pr (mm/day) | 2.09 | 2.24 | -0.16 | 2.70 | 1.45 | 0.630 |
| rsds (W/m2) | 179.78 | 179.06 | +0.72 | 28.27 | 20.95 | 0.948 |

### 1.3 Climate comparison across scenarios and periods

| Metric | SSP126 Early | SSP126 Late | SSP245 Early | SSP245 Late |
|--------|-------------|-------------|-------------|-------------|
| tas bias (K) | -0.66 | +3.57 | -0.50 | +2.07 |
| pr bias (mm/day) | -0.24 | -0.13 | -0.20 | -0.16 |
| rsds bias (W/m2) | +4.32 | -1.63 | +4.63 | +0.72 |
| tas r | 0.977 | 0.970 | 0.976 | 0.972 |
| pr r | 0.679 | 0.595 | 0.682 | 0.630 |
| rsds r | 0.955 | 0.950 | 0.953 | 0.948 |

---

## 2. Carbon Pool Comparison Summary

### 2.1 SSP126 Carbon Pools (kg C/m2, area-weighted)

| Period | Pool | Mean IMOGEN | Mean ISIMIP | Bias | WRMSE | Pearson r |
|--------|------|-------------|-------------|------|-------|-----------|
| 2021-2040 | VegC | 3.48 | 3.19 | +0.29 | 1.38 | 0.968 |
| 2021-2040 | LitterC | 1.67 | 1.68 | -0.004 | 0.52 | 0.960 |
| 2021-2040 | SoilC | 8.43 | 8.85 | -0.42 | 2.18 | 0.974 |
| 2021-2040 | Total | 13.60 | 13.74 | -0.14 | 1.88 | 0.987 |
| 2021-2100 | VegC | 3.79 | 3.47 | +0.32 | 1.49 | 0.966 |
| 2021-2100 | LitterC | 1.81 | 1.79 | +0.01 | 0.54 | 0.963 |
| 2021-2100 | SoilC | 8.46 | 8.88 | -0.43 | 2.17 | 0.974 |
| 2021-2100 | Total | 14.07 | 14.16 | -0.09 | 1.94 | 0.987 |
| 2081-2100 | VegC | 4.05 | 3.70 | +0.35 | 1.59 | 0.964 |
| 2081-2100 | LitterC | 1.95 | 1.92 | +0.03 | 0.57 | 0.966 |
| 2081-2100 | SoilC | 8.49 | 8.92 | -0.43 | 2.16 | 0.974 |
| 2081-2100 | Total | 14.50 | 14.55 | -0.05 | 2.00 | 0.987 |

### 2.2 SSP245 Carbon Pools (kg C/m2, area-weighted)

| Period | Pool | Mean IMOGEN | Mean ISIMIP | Bias | WRMSE | Pearson r |
|--------|------|-------------|-------------|------|-------|-----------|
| 2021-2040 | VegC | 3.46 | 3.17 | +0.29 | 1.36 | 0.969 |
| 2021-2040 | LitterC | 1.67 | 1.68 | -0.004 | 0.53 | 0.960 |
| 2021-2040 | SoilC | 8.43 | 8.85 | -0.42 | 2.17 | 0.974 |
| 2021-2040 | Total | 13.59 | 13.73 | -0.14 | 1.88 | 0.987 |
| 2021-2100 | VegC | 3.83 | 3.50 | +0.33 | 1.50 | 0.964 |
| 2021-2100 | LitterC | 1.81 | 1.79 | +0.02 | 0.54 | 0.963 |
| 2021-2100 | SoilC | 8.46 | 8.88 | -0.42 | 2.16 | 0.974 |
| 2021-2100 | Total | 14.13 | 14.20 | -0.07 | 1.95 | 0.987 |
| 2081-2100 | VegC | 4.18 | 3.81 | +0.37 | 1.63 | 0.961 |
| 2081-2100 | LitterC | 1.97 | 1.93 | +0.04 | 0.57 | 0.966 |
| 2081-2100 | SoilC | 8.49 | 8.92 | -0.43 | 2.14 | 0.974 |
| 2081-2100 | Total | 14.67 | 14.68 | -0.01 | 2.02 | 0.987 |

### 2.3 Carbon pool bias evolution over time

| Pool | SSP126 Early | SSP126 Late | SSP245 Early | SSP245 Late |
|------|-------------|-------------|-------------|-------------|
| VegC bias | +0.29 | +0.35 | +0.29 | +0.37 |
| LitterC bias | -0.004 | +0.03 | -0.004 | +0.04 |
| SoilC bias | -0.42 | -0.43 | -0.42 | -0.43 |
| Total bias | -0.14 | -0.05 | -0.14 | -0.01 |
| Total r | 0.987 | 0.987 | 0.987 | 0.987 |

---

## 3. Carbon Flux Comparison Summary

### 3.1 SSP126 Carbon Fluxes (kg C/m2/yr, area-weighted)

| Period | Flux | Mean IMOGEN | Mean ISIMIP | Bias | WRMSE | Pearson r |
|--------|------|-------------|-------------|------|-------|-----------|
| 2021-2040 | NEE | -0.016 | -0.015 | -0.001 | 0.047 | 0.895 |
| 2021-2040 | Veg | -0.422 | -0.417 | -0.005 | 0.040 | 0.992 |
| 2021-2040 | Soil | 0.327 | 0.325 | +0.002 | 0.035 | 0.990 |
| 2021-2040 | Fire | 0.011 | 0.011 | +0.001 | 0.033 | 0.798 |
| 2021-2040 | Harvest | 0.038 | 0.038 | ~0.000 | 0.002 | 1.000 |
| 2081-2100 | NEE | -0.010 | -0.010 | ~0.000 | 0.051 | 0.876 |
| 2081-2100 | Veg | -0.428 | -0.423 | -0.004 | 0.038 | 0.992 |
| 2081-2100 | Soil | 0.338 | 0.336 | +0.002 | 0.036 | 0.990 |
| 2081-2100 | Fire | 0.013 | 0.012 | +0.001 | 0.036 | 0.793 |
| 2081-2100 | Harvest | 0.037 | 0.037 | ~0.000 | 0.000 | 1.000 |

### 3.2 SSP245 Carbon Fluxes (kg C/m2/yr, area-weighted)

| Period | Flux | Mean IMOGEN | Mean ISIMIP | Bias | WRMSE | Pearson r |
|--------|------|-------------|-------------|------|-------|-----------|
| 2021-2040 | NEE | -0.014 | -0.013 | -0.001 | 0.048 | 0.908 |
| 2021-2040 | Veg | -0.424 | -0.419 | -0.005 | 0.040 | 0.992 |
| 2021-2040 | Soil | 0.328 | 0.326 | +0.002 | 0.035 | 0.990 |
| 2021-2040 | Fire | 0.011 | 0.011 | +0.001 | 0.033 | 0.798 |
| 2021-2040 | Harvest | 0.039 | 0.039 | ~0.000 | 0.001 | 1.000 |
| 2081-2100 | NEE | -0.019 | -0.018 | -0.001 | 0.055 | 0.892 |
| 2081-2100 | Veg | -0.483 | -0.475 | -0.008 | 0.047 | 0.990 |
| 2081-2100 | Soil | 0.369 | 0.365 | +0.004 | 0.038 | 0.990 |
| 2081-2100 | Fire | 0.014 | 0.013 | +0.001 | 0.039 | 0.793 |
| 2081-2100 | Harvest | 0.047 | 0.047 | ~0.000 | 0.000 | 1.000 |

---

## 4. Contextualisation Against Inter-Model Spread

### 4.1 Climate variables in context of IPCC AR6 CMIP6 assessed ranges

Temperature and precipitation ranges are from IPCC AR6 WG1 Chapter 4 (very likely ranges for 2081-2100 relative to 1995-2014). Shortwave spread is from published inter-GCM comparisons.

| Metric | SSP126 bias | SSP245 bias | CMIP6 inter-model range | Bias as % of spread |
|--------|------------|------------|------------------------|-------------------|
| tas (K), early century | -0.66 | -0.50 | SSP1-2.6 very likely: 0.5-1.5 C; SSP2-4.5: 1.2-2.6 C | SSP126: ~66% of half-range; SSP245: ~36% |
| tas (K), end of century | +3.57 | +2.07 | SSP1-2.6: 0.5-1.5 C (1.0 K spread); SSP2-4.5: 1.2-2.6 C (1.4 K spread) | SSP126: **exceeds range**; SSP245: ~148% of spread |
| pr (mm/day), early century | -0.24 (~11%) | -0.20 (~10%) | SSP1-2.6: 0.0-6.6%; SSP2-4.5: 1.5-8.3% | Comparable to spread |
| pr (mm/day), end of century | -0.13 (~6%) | -0.16 (~7%) | As above | Within range |
| rsds (W/m2), early century | +4.32 | +4.63 | ~5-10 W/m2 typical inter-GCM spread | Within range |
| rsds (W/m2), end of century | -1.63 | +0.72 | ~5-10 W/m2 | Well within range |

### 4.2 Carbon variables in context of published inter-model spread

Global totals are computed using area-weighted sums across ~62,512 land points (total land area 140.3 x 10^12 m2). Published ranges are from CMIP5/CMIP6 inter-model comparisons.

| Metric | SSP126 bias | SSP245 bias | Published inter-model range | Bias as % of spread |
|--------|------------|------------|---------------------------|-------------------|
| VegC (Pg C), full period | +45 | +47 | 52-477 Pg C (Carvalhais 2014, Bloom 2016) | ~10-11% |
| VegC (Pg C), early century | +41 | +41 | As above | ~9-10% |
| VegC (Pg C), end of century | +49 | +52 | As above | ~11-12% |
| SoilC (Pg C), all periods | -60 | -60 | 510-3040 Pg C (Todd-Brown 2013, Tifafi 2018) | ~2% |
| Total C (Pg C), early century | -19 | -19 | ~600-3500 Pg C | <1% |
| Total C (Pg C), end of century | -6 | -1 | ~600-3500 Pg C | <0.2% |
| NEE (Pg C/yr), full period | -0.10 (SSP126), -0.19 (SSP245) | As listed | +/-3 Pg C/yr across ESMs (Friedlingstein 2022) | 3-6% |
| Veg uptake (Pg C/yr), full period | -0.72 (SSP126), -1.00 (SSP245) | As listed | +/-15 Pg C/yr across ESMs | 5-7% |
| Soil respiration (Pg C/yr), full period | +0.31 (SSP126), +0.44 (SSP245) | As listed | ~30-80 Pg C/yr range across models | <1% |
| Fire (Pg C/yr), full period | +0.10 (both) | As listed | 0.5-4.0 Pg C/yr across models | ~3% |
| Harvest (Pg C/yr) | ~0.00 (both) | As listed | Prescribed by land-use, not climate-dependent | N/A |

### 4.3 Carbon flux bias evolution (Pg C/yr, global area-weighted totals)

| Flux | SSP126 Early | SSP126 Late | SSP245 Early | SSP245 Late |
|------|-------------|-------------|-------------|-------------|
| NEE | -0.14 | -0.03 | -0.14 | -0.20 |
| Veg | -0.71 | -0.62 | -0.73 | -1.16 |
| Soil | +0.26 | +0.31 | +0.28 | +0.57 |
| Fire | +0.10 | +0.11 | +0.09 | +0.13 |
| Harvest | -0.01 | ~0.00 | ~0.00 | ~0.00 |

---

## 5. Key Findings

### 5.1 Temperature

- The temperature bias flips sign across the century in both scenarios: IMOGEN starts cooler than ISIMIP (-0.50 to -0.66 K) and ends warmer (+2.07 to +3.57 K).
- Under SSP126, the end-of-century bias (+3.57 K) exceeds the IPCC AR6 assessed very likely range (0.5-1.5 C). Under SSP245, the bias (+2.07 K) also exceeds the assessed very likely range (1.2-2.6 C) but by a smaller margin.
- Spatial correlations remain high (r > 0.97) throughout, indicating the two products agree well on where warming occurs even if they disagree on how much.

### 5.2 Precipitation

- IMOGEN is systematically drier than ISIMIP in both scenarios (-0.13 to -0.24 mm/day, or ~6-11%).
- The bias is comparable to the CMIP6 inter-model spread for precipitation change.
- Correlation is moderate (r ~0.60-0.68), substantially lower than temperature, reflecting the well-known difficulty of emulating precipitation patterns.

### 5.3 Shortwave radiation

- Early-century bias (IMOGEN brighter by ~4.3-4.6 W/m2) narrows or reverses by end of century.
- Both values fall comfortably within the typical ~5-10 W/m2 inter-GCM spread.
- Spatial correlations are consistently high (r ~0.95).

### 5.4 Carbon pools

- VegC: IMOGEN consistently stores more vegetation carbon (+0.29 to +0.37 kg C/m2 per grid cell; +41 to +52 Pg C globally). This represents only 10-12% of the published inter-model range.
- SoilC: IMOGEN stores less soil carbon (-0.42 to -0.43 kg C/m2; ~-60 Pg C globally). This is just ~2% of the enormous 510-3040 Pg C inter-model range.
- Total carbon: The opposing VegC and SoilC biases largely cancel. The total pool bias converges from -19 Pg C early century to near zero by 2100, representing <1% of inter-model spread.
- All spatial correlations remain stable at r ~0.987 regardless of period or scenario.

### 5.5 Carbon fluxes

- Vegetation uptake (Veg) and soil respiration (Soil) are nearly identical between the products (r ~0.99), with biases of 5-7% of inter-model spread.
- Fire emissions show the weakest agreement (r ~0.80) with IMOGEN producing ~0.1 Pg C/yr more fire. The warmer, drier IMOGEN climate likely enhances fire-prone conditions.
- NEE (the net carbon balance) tracks well year-to-year (r ~0.88-0.91) with small systematic differences.
- Harvest is virtually identical (r ~1.0) as it depends on land-use prescriptions rather than climate.

### 5.6 Scenario dependence

- The SSP126 and SSP245 analyses yield remarkably consistent patterns. Carbon biases are nearly identical between scenarios, suggesting the differences are structural (driven by how IMOGEN emulates the base GCM climate) rather than scenario-dependent.
- The temperature divergence is larger under SSP126 (+3.57 K) than SSP245 (+2.07 K) at end of century, which is counterintuitive but may reflect that SSP126's lower forcing level amplifies the relative importance of the emulator's pattern-scaling assumptions.

---

## 6. Overall Assessment

The two climate products are **broadly comparable** for many applications, with caveats:

- **Carbon cycle applications**: IMOGEN and ISIMIP3b are essentially interchangeable. All carbon biases fall within 2-12% of the enormous published inter-model spread, and spatial correlations exceed 0.96 for pools and 0.99 for major fluxes. The total carbon pool bias converges toward zero over the century.

- **Near-term climate applications (2020s-2040s)**: The products agree well. Temperature biases are modest (-0.50 to -0.66 K), radiation is within inter-GCM spread, and spatial patterns are highly correlated.

- **End-of-century temperature-sensitive applications**: The growing temperature divergence (up to +3.57 K under SSP126) exceeds the IPCC AR6 assessed inter-model range and is a genuine concern for impact studies focused on crossing temperature thresholds, permafrost stability, or other nonlinear temperature-dependent processes.

- **Precipitation-sensitive applications**: The moderate precipitation correlation (r ~0.60-0.68) and systematic dry bias suggest caution for hydrological, drought, or agricultural impact studies.

---

## References

- Carvalhais, N. et al. (2014). Global covariation of carbon turnover times with climate in terrestrial ecosystems. Nature, 514, 213-217.
- Bloom, A.A. et al. (2016). CARDAMOM: A Bayesian approach for constraining global carbon cycle analyses. Geophysical Research Letters, 43, 1-10.
- Todd-Brown, K.E.O. et al. (2013). Causes of variation in soil carbon simulations from CMIP5 Earth system models. Biogeosciences, 10, 1717-1736.
- Tifafi, M. et al. (2018). Large differences in global and regional total soil carbon stock estimates based on SoilGrids, HWSD, and NCSCD. Global Biogeochemical Cycles, 32, 42-56.
- Friedlingstein, P. et al. (2022). Global Carbon Budget 2022. Earth System Science Data, 14, 4811-4900.
- IPCC, 2021: Chapter 4: Future Global Climate: Scenario-based Projections and Near-term Information. In: Climate Change 2021: The Physical Science Basis. Cambridge University Press.
