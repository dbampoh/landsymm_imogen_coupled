# `docs/` — unified user / developer documentation

The user- and developer-facing documentation for v1.0. To be built
at **step 18** of the rebuild plan (`EXECUTION_PLAN.md` §V.1, the
documentation-harmonisation phase).

**Status:** populated incrementally through the rebuild. The
existing top-level investigation documents (`COUPLED_MODEL_INVESTIGATION.md`,
`EXECUTION_PLAN.md`, `_phase2_findings/`) stay at the top level —
they document the rebuild itself; the `docs/` tree documents the
v1.0 product.

## Planned files (post-step-18)

| File | Audience | Role |
|---|---|---|
| `technical_manual.md` | maintainers, peer reviewers | The unified technical manual. Synthesised from `COUPLED_MODEL_INVESTIGATION.md` §1-§7, the working paper §1-§2, and the `Intermediary_py` HANDOFF/TECHNICAL_MANUAL. Build instructions, run instructions, output catalogue, validation procedure, troubleshooting, glossary. |
| `scientific_framework.md` | scientists, paper readers | The scientific framework, derived from the working paper §1-§2.4 and `[CMI §2]`. Lineage and citations, the two-stage protocol (Stage I yield generation as documented design intent, Stage II coupled run as v1.0 implementation), sector ownership and double-counting prevention, boundary harmonisation, validation thresholds, acknowledged biases. |
| `architecture.md` | developers | The system architecture. Distillation of `[CMI §3]`. Component inventory, single-binary process model, three coupling modes (tight / prescribed / loose), the `done`-file rendezvous protocol (§3.4), the `FILE_LPJG_FLUX` data-ownership table (§3.7), the data flows. |
| `build.md` | new users | Step-by-step build instructions for Ubuntu 22.04 / 24.04 workstations and the KIT IMK-IFU owl HPC cluster. **Honours the Anaconda3 NetCDF preference** (Decision #8). |
| `operating_manual.md` | new users | Run recipes: a 4-cell smoke test, a full SSP1-2.6 workstation run, a full SSP1-2.6 cluster run, a 5-SSP comparison run. |
| `data_inventory.md` | new users | Where to obtain every input dataset (HILDA+, PLUMv2, FAOSTAT, RCMIP, FAIR ERF, EDGAR 2025, CMIP6 patterns, CRUNCEP base climatology, NOAA GMD / AGAGE observations). |
| `troubleshooting.md` | users | Known issues and recipes for common failure modes. |
| `glossary.md` | everyone | Definitions of every variable, every file format, every acronym (LPJG, IMOGEN, PLUM, LandSyMM, NEE, NBP, NEP, RCMIP, FAIR, ERF, GCB, GMB, GNB, etc.). |
| `v2_roadmap.md` | future maintainers | The post-v1.0 stretch goals: PLUM embedding (Decision #9), C++ IMOGEN brought to parity (`§II.2.5`), integrated LTS as switchable backend (`§II.11.3`), native NetCDF in IMOGEN, Tier-2 emissions, formal uncertainty propagation, etc. |
| `components/` | developers | Per-component deep-dive sub-docs (lifted from `_phase2_findings/`): `lpjguess.md`, `imogen_fortran.md`, `intermediary_py.md`, `patterns_and_regrid.md`. |

## Cross-references

The `docs/` tree's documents cite back to the investigation evidence
base via `[CMI §x.y]` (master doc), `[SAn §x.y]` (subagent reports),
and `[EXEC §x.y]` (execution plan). This keeps the v1.0 user docs
short and operational while preserving the audit trail to the
~770 KB of evidence that supports each design decision.
