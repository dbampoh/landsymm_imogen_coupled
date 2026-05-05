# `intermediary_py/` — Python Intermediary Controller

The IPCC 2019 Refinement Tier-1 emissions-estimator pipeline that
converts PLUM activity data + LPJ-GUESS natural fluxes into the
IMOGEN-bound annual emissions vector. Source: the user's
`imogen_ghg_controller v0.1.0` from the predecessor framework's
`Intermediary_py/imogen_ghg_controller_SOURCE_ONLY/`.

**Status:** to be imported at **step 10** of the rebuild plan
(`EXECUTION_PLAN.md` §V.1). Then exercised on staged inputs
(step 11), validated against earlier reference outputs (step 12),
and adapted to produce the four narrow IMOGEN-readable files
via `tools/imogen_inputs_to_lpjg_format.py` (step 13).

**Anthropogenic substitution backbone: RCMIP** (Decision #1 in
`EXECUTION_PLAN.md` §Decisions Settled). The substitution algebra is

```
New_total = RCMIP_total - RCMIP_agri + Our_agri
```

where `Our_agri` is the IPCC tier-1 estimate from FAO/PLUM activity
data and `RCMIP_agri` is `Emissions|<gas>|MAGICC AFOLU|Agriculture`
(for CH4) or `Emissions|<gas>|MAGICC AFOLU` (for N2O) from RCMIP
Phase 2 v5.1.0.

## Pipeline architecture

Four components in dependency order, driven by `run_all.py` (43
ordered steps):

| Component | Role | LOC |
|---|---|---|
| **A. Anthropogenic** | IPCC tier-1 emissions × FAO/EDGAR/PLUM activity data; substitution into RCMIP | 8 682 (28 .py) |
| **B. Natural** | LPJ-GUESS streaming aggregation (.gz files) + GMB IFW/DCC corrections | 1 791 (5 .py) |
| **C. Integration** | Sums anthro + natural; 3 independent comparators | 2 848 (9 .py) |
| **D. IMOGEN export** | Reshape to per-scenario wide + combined long format CSVs | 176 |

## Outputs

- `outputs/component_a/data/*.csv` — per-sector historical and
  scenario CH4/N2O.
- `outputs/component_b/data/*.csv` — LPJ-GUESS natural CO2/CH4/N2O.
- `outputs/component_c/data/*.csv` — integrated CH4/N2O/CO2 with
  comparators.
- **`outputs/imogen_inputs/imogen_inputs_<SSP>.csv`** — the
  framework-ready output: 5 wide-format scenario CSVs + 1 long-format
  combined. 201 rows × 10 columns each. Mt-of-gas/yr units.

## Prerequisites for v1.0

- Python ≥ 3.10
- pandas ≥ 2.0, numpy ≥ 1.24, matplotlib ≥ 3.7, pyarrow ≥ 14.0,
  **openpyxl ≥ 3.0** (added as part of step 10; missing in the
  predecessor's `requirements.txt`).
- `zcat` on PATH (LPJ-GUESS .gz streaming).
- ~2.5 GB free disk (1.8 GB inputs + ~700 MB working).
- 6-8 GB RAM (livestock anchor step).

See `inputs/README.md` (created at step 11) for input acquisition
details.

## Tests

3 pytest tests, all passing:
- `test_unit_conversions.py` — Pg C ↔ Mt CO2, Tg N ↔ Tg N2O.
- `test_co2_option_a_validation.py` — SSP2-4.5 mean 2014-2020
  integrated CO2 atmospheric source within ±1σ of GCB 2025 partition.
- `test_imogen_export_schema.py` — final output shape and column
  order.

Expanded with cross-component validation tests at step 19 of the
rebuild.
