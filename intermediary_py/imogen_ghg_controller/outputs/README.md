# `outputs/` — Generated outputs

This directory is **gitignored** because the contents are fully reproducible from `inputs/` + `src/`. After running `python run_all.py`, this directory contains:

```
outputs/
├── component_a/
│   ├── data/        ~38 CSVs (per-sector global/country/regional totals + scenario projections + RCMIP-substituted)
│   ├── figures/     ~13 PNGs (per-sector trend plots + RCMIP comparison plots)
│   └── summaries/   text summaries
│
├── component_b/
│   ├── data/        ~10 CSVs (LPJ-GUESS historical + scenario + combined CH4 + FAIR-ERF baseline)
│   ├── figures/     2 PNGs (4-panel historical + 1901-2100 full trajectory)
│   └── summaries/   3 text files (budget comparison, scenario summary, grid diagnostics)
│
├── component_c/
│   ├── data/        13 CSVs (rcmip_co2 + integrated × 3 gases + 3 comparator types × 3 gases)
│   ├── figures/     4 PNGs (integrated + top-down + hybrid + conventional)
│   └── summaries/   4 text files (one per comparator)
│
└── imogen_inputs/   ← TERMINAL OUTPUT
    ├── imogen_inputs_SSP1-2.6.csv  (201 rows × 10 cols)
    ├── imogen_inputs_SSP2-4.5.csv
    ├── imogen_inputs_SSP3-7.0.csv
    ├── imogen_inputs_SSP4-6.0.csv
    ├── imogen_inputs_SSP5-8.5.csv
    └── imogen_inputs_all_scenarios_long.csv (3015 rows × 7 cols)
```

The terminal output is the IMOGEN-ready CSVs in `imogen_inputs/`. These are the actual deliverable — everything else is intermediate or validation output.
