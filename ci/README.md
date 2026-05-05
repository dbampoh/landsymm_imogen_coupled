# `ci/` — Continuous Integration / Continuous Delivery

Workflow definitions for the GitHub Actions / GitLab CI pipelines
that build, test, and validate the codebase on every commit.

**Status:** to be populated at **step 19** of the rebuild plan
(`EXECUTION_PLAN.md` §V.1, after the workstation and cluster
launchers are complete).

## Planned workflows

| File | Triggered by | Action |
|---|---|---|
| `.github/workflows/ci.yml` | every push, every PR | builds LPJ-GUESS (cmake + g++ + libnetcdf), builds Fortran IMOGEN (gfortran), builds Python venv (`pip install -r intermediary_py/requirements.txt`); runs the 3 pytest tests in `intermediary_py/tests/`; runs the units-integrity tests added in step 19 (per `EXECUTION_PLAN.md` §I.D.4); runs the smoke coupled-run test (`scripts/smoke_test.sh`); confirms reference outputs match expected (md5 or pandas tolerance). |
| `.gitlab-ci.yml` | every push to KIT and Helmholtz mirrors | identical scope to the GitHub workflow, written in GitLab CI YAML. |

The CI runs on Ubuntu 22.04 + 24.04 (the framework's target Linux
versions). Cluster-only steps (the MPI parallel tests, the full
SSP1-2.6 production run on owl) are NOT in CI — they run manually
via the cluster SLURM scripts and the user's terminal back-and-forth.

## Discipline

Per `EXECUTION_PLAN.md` §I.D:

- **§I.D.4 cross-component validation tests:** CI verifies that the
  units math at component boundaries is self-consistent. The Python
  Intermediary's existing `test_unit_conversions.py` is the
  template; new tests for the LPJG → handshake → IMOGEN data path
  are added at step 19.
- **§I.D.6 unit drift detection:** CI compares the run log's
  startup banner (printed by `scripts/run_coupled.sh`, per §I.D.5)
  against a checked-in reference banner. Any drift fails the build.
- **§I.D.7 reciprocal producer/consumer checks:** every
  cross-component data path has at least one CI test fixture:
  producer writes a known-value file; consumer reads it; assertion
  that the consumer's parsed value matches the producer's intended
  value (modulo unit conversion).

When adding new functionality, add a corresponding test fixture.
When fixing a bug, add a regression test that fails before the fix
and passes after. See `CONTRIBUTING.md` for the full discipline.
