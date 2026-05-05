# `archive/` — frozen legacy code preserved for reference

Code preserved for reference but not part of the active v1.0
codebase. Each subdirectory contains a snapshot of an earlier or
parallel implementation, kept so:

- Future maintainers can see the design history.
- Numerical-parity tests can compare against legacy outputs.
- The v2.0 work has a starting point that doesn't require
  re-investigating the predecessor framework.

**Status:** populated incrementally as the rebuild progresses. Each
import into `archive/` is a single git commit with a descriptive
message naming the subdirectory's provenance and the v1.0 code that
supersedes it.

## Planned contents (post-rebuild)

| Subdirectory | Contains | Imported at | Successor in v1.0 |
|---|---|---|---|
| `imogen_cxx/` | The user's earlier C++ IMOGEN refactor (`IMOGENCXX/ImogenCXX/src/Main.cpp`, single 2 631-LOC file, 25 catalogued bugs, never run end-to-end). Preserved as the starting point for Phase-2 numerical-parity work (`EXECUTION_PLAN.md` §II.2 Phase 2). | step 20+ post-v1.0 | `imogen/` (Fortran-with-`ALLOCATABLE`) — and eventually the C++ refactor brought to parity in Phase 2 lives here too. |
| `imogen_controller/` | The standalone C++ controller from the predecessor framework (`Imogen-controller/Imogen-controller-cross.cpp` etc.). Vestigial design from the legacy 2-process coupling architecture. | step 0 | The single-binary in-process design (LPJ-GUESS links the IMOGEN engine via `RUN_IMOGEN_ENGINE()`). |
| `intermediary_cpp/` | The legacy C++ Intermediary (`Intermediary/Code/`), 4 052-5 891 LOC across 12-13 source files, builds clean on Linux but `Adder` step commented out. Preserved as a parity baseline for the Python pipeline outputs. | post-v1.0 | `intermediary_py/` (the Python `imogen_ghg_controller v0.1.0`). |
| `matlab_plot_scripts/` | The 3 Matlab plot scripts from the predecessor's `Matlab-scripts/` (IIASA-CMIP6 comparison). Out-of-repo data dependency made them unrunnable as-shipped. | step 0 | The Python `intermediary_py/src/component_*/...plotting.py` modules. |
| `colab_notebook/` | The Python plot notebook from the predecessor's `Python-scripts/`. Hardcoded Colab Drive paths. | step 0 | Same — superseded by Python pipeline plotting. |
| `references_outdated/` | The OUTDATED documentation from the predecessor's `References/`: `Imogen_paper_GMD.docx` (older paper draft superseded by the working paper); `Adding NBP…docx` (incorrect formula superseded by `NEE-NBP Changes Report.docx`); `Brief Documentation of N2O Disaggregation.docx` (static methodology superseded by working paper §2.3.2 dynamic Tian 2024 method); `Reassessment of maps.docx` (early draft superseded by `IPCC_Maps_Reassessment_Validation.docx`); `Addressing Cross-Compiler…` (Linux-only project). Per `[CMI §7.2]`. | step 18 | The unified `docs/technical_manual.md` and `paper/manuscript_draft.docx`. |

## Discipline

Anything in `archive/` is **read-only reference**. It does NOT build
in the v1.0 CI pipeline. It does NOT run in the v1.0 launcher. Its
presence is purely informational.

When a v2.0 effort revives an archived component (e.g. brings the
C++ IMOGEN refactor to numerical parity), the work is done in the
active part of the tree (e.g. `imogen/cxx/` parallel to
`imogen/code/` for Fortran), not by mutating `archive/`.
