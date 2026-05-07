# STEP 10 — Import `intermediary_py` (`imogen_ghg_controller v0.1.0`)

**Date completed:** 2026-05-07
**Commit:** _to be filled in after `git commit`_
**Status:** ✅ Source imported clean; package structure verified; pipeline
dry-run shows all 43 steps registered cleanly. End-to-end pipeline
execution + integration into `runs/SSP1-2.6/` gated on step 11
(Tier-3 input-data acquisition: ~1.8 GB across RCMIP / FAIR ERF /
EDGAR / PLUM / LPJ-GUESS reference outputs).

---

## 1. Goal (per `EXECUTION_PLAN.md` V.1 step 10)

> Import + adapt `intermediary_py` from
> `version_A/Intermediary_py/imogen_ghg_controller_SOURCE_ONLY/`. This
> replaces the predecessor's legacy C++ `Intermediary/Code/` (272 KB,
> ~half-built) with the user's modern Python pipeline that performs the
> IPCC 2019-Refinement Tier-1 emissions estimation, RCMIP substitution,
> and IMOGEN-input file production.

---

## 2. Investigation findings

### 2.1 Locating the source

Two candidate variants in `version_A/Intermediary_py/`:

| Variant | Size | Contents | Verdict |
|---|---|---|---|
| `imogen_ghg_controller_SOURCE_ONLY/` | 7.9 MB | 78 files: 59 Python source + 3 tests + 16 docs/config | **Import this** |
| `imogen_ghg_controller_FULL/` | 5.2 GB | SOURCE_ONLY + populated `inputs/` (RCMIP, FAIR, EDGAR, PLUM, LPJG outputs) + complete `outputs/` (per-step + final IMOGEN inputs) + figures | Tier-3; document acquisition; do NOT commit |

### 2.2 A vs B equivalence

`diff -rq` between version_A and version_B's SOURCE_ONLY trees (excluding
`figures_gallery/`, `inputs/`, `outputs/`, `archive/`, `__pycache__`)
returns **zero differences**. The two predecessor frameworks have
identical intermediary_py source. Imported version_A's copy.

### 2.3 Pipeline architecture (from `Quick_Start.md` + `run_all.py`)

43 steps × 4 components, dry-run verified:

| Component | Role | Steps | Approx runtime |
|---|---|---|---|
| **A** Anthropogenic | IPCC Tier-1 emissions for 6 sectors (CH4 EF, MM, rice cult; N2O MM, MS, syn-fert) × FAO/EDGAR/PLUM activity data; substitute into RCMIP totals | 28 | ~10-15 min (livestock anchor is RAM-heavy: 6-8 GB) |
| **B** Natural | LPJ-GUESS reference outputs streamed (`.gz` files), GMB IFW/DCC corrections | 5 | ~10-15 min (3-5 min per .gz) |
| **C** Integration | Sums A + B; 3 independent comparators (conventional/hybrid/external) | 9 | ~1 min |
| **D** IMOGEN export | Reshape to per-scenario wide + combined long format CSVs | 1 | ~2 sec |

**Final 6 IMOGEN-input deliverables** at `outputs/imogen_inputs/`:
- 5 per-scenario wide CSVs (SSP1-1.9 / SSP1-2.6 / SSP2-4.5 / SSP3-7.0 / SSP5-8.5)
- 1 combined long-format CSV
- Format: 201 rows × 10 columns; **units: Mt-of-gas/yr**

### 2.4 Anthropogenic substitution backbone (Decision #1)

Per `EXECUTION_PLAN.md` Decision #1, the substitution algebra is:

```
New_total = RCMIP_total − RCMIP_agri + Our_agri
```

where `Our_agri` is the IPCC Tier-1 estimate from FAO/PLUM activity data.
The code already implements this via
`src/component_a_anthropogenic/rcmip_substitution/`. **Pre-validated**:
38/38 reference data files byte-identical to canonical scripts (per
`Quick_Start.md` provenance check).

### 2.5 Test suite

3 pytest tests at `tests/`:
- `test_unit_conversions.py` — Pg C ↔ Mt CO2, Tg N ↔ Tg N2O
- `test_co2_option_a_validation.py` — SSP2-4.5 2014-2020 mean within
  ±1σ of GCB 2025 carbon budget partition
- `test_imogen_export_schema.py` — final output shape + column order

Tests require populated `outputs/` (Tier-3 data); run them at step 11
after input acquisition.

---

## 3. What was implemented

### 3.1 Import

```bash
rsync -a --info=stats1 \
  --exclude='inputs/*' --exclude='outputs/*' --exclude='archive/*' \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' \
  --include='inputs/README.md' --include='outputs/README.md' --include='archive/README.md' \
  ../version_A/.../imogen_ghg_controller_SOURCE_ONLY/imogen_ghg_controller/ \
  intermediary_py/imogen_ghg_controller/
```

Result: 7.9 MB at `intermediary_py/imogen_ghg_controller/` with the
following layout:

```
intermediary_py/imogen_ghg_controller/
├── HANDOFF.md              90 KB — verification protocol from author handoff
├── LICENSE                 1.1 KB — MIT
├── Quick_Start.md          7.7 KB — operational guide
├── README.md               25 KB — package overview
├── TECHNICAL_MANUAL.md     109 KB — methodology + reference tables
├── archive/README.md       (empty content kept for tracking)
├── docs/                   methodology, budget references, component_A-D specs
├── inputs/README.md        (acquisition placeholder; full data is Tier-3)
├── outputs/README.md       (output schema description)
├── pyproject.toml          1.1 KB — package metadata + deps + setuptools config
├── requirements.txt        54 B — pandas, numpy, matplotlib, pyarrow
├── run_all.py              11 KB — pipeline driver with --dry-run / --component flags
├── src/                    59 .py files
│   ├── shared/             paths, scenarios, unit conversions
│   ├── component_a_anthropogenic/    historical + rcmip_substitution + scenarios
│   ├── component_b_natural/          historical + scenarios + full_trajectory
│   ├── component_c_integration/      conventional + hybrid + external comparators
│   └── component_d_imogen_export/    final CSV reshape
└── tests/                  3 pytest files
```

### 3.2 Package metadata

- Python ≥ 3.10
- 4 dependencies: `pandas≥2.0`, `numpy≥1.24`, `matplotlib≥3.7`, `pyarrow≥14.0`
- Optional `[test]` extra: `pytest≥7.0`
- Setuptools-style packaging; `pip install -e .` should work

### 3.3 Verified

- `python3 run_all.py --dry-run` exits 0; reports all 43 steps cleanly
- No missing-imports errors at module-load time (system Python on workstation)
- File count + structure matches predecessor's SOURCE_ONLY tree

### 3.4 What was NOT done (gated on later steps)

| Item | Reason for deferral |
|---|---|
| Live pipeline run + IMOGEN-input file generation | Needs ~1.8 GB Tier-3 input data (RCMIP, FAIR ERF, EDGAR, PLUM, LPJG outputs); step 11 owns input acquisition |
| Integration into `runs/SSP1-2.6/imogen_intermediary.ins` (replace static-IIASA paths with intermediary_py outputs) | F-10 deadlock blocks end-to-end coupled run anyway; step 13's adapter (`tools/imogen_inputs_to_lpjg_format.py`) is the wiring point |
| Full pytest run | Tests need populated `outputs/`; run at step 11 |

---

## 4. Files modified / added

### Added

| Path | Bytes | Purpose |
|---|---|---|
| `intermediary_py/imogen_ghg_controller/` | 7.9 MB | full SOURCE_ONLY tree (78 files) |
| `notes/STEP_10.md` | this file | per-step verification record |

### Modified

| Path | Change |
|---|---|
| `intermediary_py/README.md` | Status updated: ✅ imported at step 10, dry-run verified, end-to-end gated on step 11 |
| `CHANGELOG.md` | `[v0.11.0-step10-intermediary-py-import]` entry |
| `EXECUTION_PLAN.md` | Step 10 row marked ✅ |
| `notes/FOLLOWUPS.md` | New "Deferred items dashboard" section at top (per user discipline request 2026-05-07) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | Step 10 entry: zero `lpjguess/` C++ changes (intermediary_py is non-fork code) |

---

## 5. Push commands (manual three-way push)

```bash
cd /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm

git add .
git commit -m "Step 10: import intermediary_py (imogen_ghg_controller v0.1.0); 43-step pipeline verified clean"
git push origin     main
git push kit        main
git push helmholtz  main

git tag -a v0.11.0-step10-intermediary-py-import -m "Step 10: imogen_ghg_controller imported (43 pipeline steps verified via dry-run); end-to-end gated on step 11 input acquisition"
git push origin     v0.11.0-step10-intermediary-py-import
git push kit        v0.11.0-step10-intermediary-py-import
git push helmholtz  v0.11.0-step10-intermediary-py-import
```
