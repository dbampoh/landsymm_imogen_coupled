# Contributing to LandSyMM-IMOGEN

Thank you for your interest in contributing to the LandSyMM-IMOGEN
coupled model framework. This document covers the development workflow,
the per-step verification protocol that the rebuild plan enforces, and
the units / data-exchange integrity discipline that prevents the
class of bugs the audit surfaced in the legacy `version_A` and
`version_B` framework trees.

> **Status:** The repository is currently in active rebuild per
> `EXECUTION_PLAN.md` Part V. Most of the v1.0 code does not yet
> exist. Until v1.0 is tagged, contributions are by invitation
> only — please coordinate with the maintainer.

---

## Project structure

See top-level `README.md` for the directory layout. In brief:

- `lpjguess/`, `imogen/`, `intermediary_py/` — the three model
  components.
- `tools/` — cross-component utilities (adapters, converters).
- `runs/` — per-scenario run setups.
- `data/` — small reference data (large data documented in
  `data/DATA.md` for separate acquisition).
- `scripts/` — workstation and cluster launchers.
- `docs/` — unified technical manual + scientific framework.
- `notes/` — per-step development notes (`notes/STEP_<n>.md`).
- `archive/` — frozen legacy code preserved for reference.

The repository's two governing documents are:

- **`COUPLED_MODEL_INVESTIGATION.md`** — the master investigation
  document (state-of-the-system, bug catalogue, roadmap). Every
  significant claim in the codebase traces to evidence in this
  document or to the underlying subagent reports in
  `_phase2_findings/`.
- **`EXECUTION_PLAN.md`** — the operational checklist (settled
  decisions, gap inventory, formal Part V step-by-step rebuild plan
  with verification milestones).

---

## Development workflow

The rebuild follows the **incremental verified-step** discipline of
`EXECUTION_PLAN.md` §V.0:

1. **Each step starts with a clean, verifiable predecessor state**
   and ends with a clean, verifiable successor state.
2. **If a step's verification fails**, the prior state is restored
   (`git checkout HEAD~1` or `git revert`) and the step is
   re-investigated before proceeding.
3. **Each step ends with a single git commit** with a descriptive
   message naming the verification milestone passed:

   ```
   git commit -m "Step <n>: <one-line summary>

   <2-5 lines of context: what was imported / changed, what was verified>

   Verification: <the verification milestone from EXECUTION_PLAN.md V.1>"
   ```

4. **Per-step documentation.** Each step's verification protocol is
   recorded in `notes/STEP_<n>.md` so any reader (or successor) can
   reproduce the verification.
5. **Tags at meaningful milestones.** `v0.1-skeleton`,
   `v0.2-lpjg-builds`, `v0.3-coupling-fixed`, ..., `v1.0`. See
   `EXECUTION_PLAN.md` Part V for the full milestone schedule.

---

## Branch strategy

- **`main`** is the always-verifiable trunk. Each commit on `main`
  passes its V.1 verification milestone.
- **Feature branches** (`step-<n>-<description>`, or
  `feat/<description>`) are used only for substantively risky work
  (e.g. the C++ IMOGEN parity port in step 20+).
- **For routine import / wiring steps**, direct commits to `main`
  are acceptable since each step is small and bounded.
- **Merging feature branches**: use `--no-ff` to preserve the step
  boundary in `git log`.

---

## Three-remote push pattern

The repository mirrors to three Git hosts:

- **GitHub:** `https://github.com/<user>/lpj-guess_imogen_landsymm` (origin)
- **KIT GitLab:** `https://gitlab.imk-ifu.kit.edu/<user>/lpj-guess_imogen_landsymm` (kit)
- **Helmholtz GitLab:** `https://<helmholtz-gitlab-url>/<user>/lpj-guess_imogen_landsymm` (helmholtz)

After cloning, set up all three remotes:

```bash
git remote add origin     <github-url>
git remote add kit        <kit-gitlab-url>
git remote add helmholtz  <helmholtz-gitlab-url>

# Verify
git remote -v
```

Push to all three after each commit (or end of day):

```bash
git push origin main && git push kit main && git push helmholtz main
```

Or define an alias once:

```bash
git config --global alias.push-all '!git push origin main && git push kit main && git push helmholtz main'
git push-all
```

For tag pushes:

```bash
git push origin --tags && git push kit --tags && git push helmholtz --tags
```

---

## Units and data-exchange integrity discipline

Per `EXECUTION_PLAN.md` §I.D, every cross-component data path
follows six disciplines:

1. **Per-file canonical units header.** Every numeric data file
   in `data/`, `runs/`, and `outputs/` carries a header comment
   line (or `<filename>.meta.yaml` sidecar for binary files)
   declaring column names, units, sign conventions, spatial and
   temporal resolution, year coverage.
2. **Unit-checked adapter functions.** Every cross-component
   adapter (the Python `imogen_inputs_to_lpjg_format.py`, the
   LPJG-side `imogenoutput.cpp` writer, the
   `cmip6_nc_to_cmip5_ascii.py` converter) carries explicit
   unit-checking assertions at its boundaries.
3. **Central unit-conversion module.**
   `intermediary_py/src/shared/units.py` and `lpjguess/include/units.h`
   declare the canonical conversion constants. No inline magic
   numbers.
4. **Cross-component validation tests.** CI tests verify that the
   units math at component boundaries is self-consistent.
5. **Sign-convention banner at run start.** `scripts/run_coupled.sh`
   prints a startup banner declaring the active sign conventions
   and units, visible in the run log.
6. **Unit drift detection in CI.** After every bug fix or refactor,
   CI compares the run log's banner against a checked-in reference;
   any drift fails the build.

7. **Reciprocal producer/consumer checks** (per §I.D.7). Each
   cross-component data path has a CI test fixture: producer
   writes a known-value file; consumer reads it; assertion that
   the consumer's parsed value matches the producer's intended
   value.

When adding a new data path or modifying an existing one,
**update the banner, the schema, and the tests in the same
commit**.

---

## Coding style

### LPJ-GUESS C++ (`lpjguess/`)

Follow the upstream LPJ-GUESS conventions (CamelCase classes,
lowerCamelCase methods, consistent spacing). New IMOGEN-coupling
code (e.g. `lpjguess/modules/imogenoutput.cpp`) should match the
style of the existing `imogencfx.cpp` for consistency.

### Fortran IMOGEN (`imogen/`)

Fixed-form Fortran 77 with `-ffixed-line-length-132`. Stay close
to the upstream IMOGEN style. The `ALLOCATABLE` refactor in step 3
should preserve the existing variable names and just change the
declarations.

### Python Intermediary (`intermediary_py/`)

PEP 8. Type hints encouraged on new code. Per-module imports from
`src.shared.units`, `src.shared.paths`, `src.shared.constants`.

### Documentation (Markdown)

GitHub-flavoured Markdown. 80-character line limits where
practical. Code blocks fenced with language tags. Tables for
structured data. Cross-references via `[CMI §x.y]` (master doc)
and `[SAn §x.y]` (subagent reports) and `[EXEC §x.y]` (execution
plan).

---

## Testing

Three layers:

1. **`intermediary_py/tests/`** — pytest tests for the Python
   pipeline. Currently 3 passing; expansion in step 19 of the
   rebuild.
2. **Smoke coupled-run test** (`scripts/smoke_test.sh`, added at
   step 14) — a 4-cell × 3-year coupled run that completes in
   <1 minute and produces canonical output files. Used in CI.
3. **CI/CD pipeline** (added at step 19) — GitHub Actions /
   GitLab CI builds LPJ-GUESS + Fortran IMOGEN, builds Python venv,
   runs all pytest tests + units-integrity tests + smoke run,
   confirms reference outputs match.

When adding new functionality, add a corresponding test fixture.
When fixing a bug, add a regression test that fails before the fix
and passes after.

---

## Reporting issues

(Pending v1.0 release. Issue tracker URLs to be added once the
three remotes are set up.)

---

## License

Contributions are licensed under MIT (see `LICENSE`).

---

*This file will evolve as the rebuild progresses through Part V.
Major changes will be recorded in `CHANGELOG.md`.*
