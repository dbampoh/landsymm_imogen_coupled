# STEP 0 — Initialise the unified repo

> **Plan reference:** `EXECUTION_PLAN.md` §V.1 step 0.
>
> **Status:** completed 5 May 2026.
>
> **Verification:** `git init`; `git status` clean after first commit.
> Top-level `tree -L 2` shows clean structure.

## What this step did

Initialised the unified codebase at
`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm/`
with the following structure:

### Top-level files

- `README.md` — top-level navigation, project overview, build/run
  placeholder, roadmap, citation pointers, license info.
- `LICENSE` — MIT, with reference to upstream component licences.
- `CITATION.cff` — machine-readable citation metadata; placeholder
  for the GMD paper currently in preparation; references the
  upstream peer-reviewed components (Huntingford 2010, Alexander
  2018, Rabin 2020, Zelazowski 2018, Mathison 2025 PRIME, Nicholls
  2020 RCMIP, Smith 2018 FAIR).
- `CONTRIBUTING.md` — development workflow, per-step verification
  protocol (per §V.0), three-remote push pattern (GitHub + KIT
  GitLab + Helmholtz GitLab), units-integrity discipline (§I.D
  six rules + §I.D.7 reciprocal producer/consumer checks).
- `CHANGELOG.md` — `Keep a Changelog` format. Documents the
  v0.0-investigation predecessor (the investigation phase outputs)
  and the v0.1-skeleton that this step produces.
- `.gitignore` — comprehensive coverage of build artefacts (CMake,
  make, MSBuild leftovers, *.o/.so/.exe), Python venv (.venv,
  __pycache__), run output (runs/*/output/, IMOGEN year-dir output,
  Intermediary outputs), large input data (LU, Lamarque archives,
  CMIP6 NetCDF), editor noise (*.swp, .vscode, .idea), and
  Word/OS junk (*.swp, ~$*.docx, .DS_Store). Allow-list overrides
  preserve per-subdir READMEs.

### Top-level directories (12 dirs, each with placeholder README.md)

- `lpjguess/` — for LPJ-GUESS LandSyMM fork (`trunk_r13078` baseline
  in v1.0; integrated LTS as Phase-2 backend).
- `imogen/` — for Fortran IMOGEN with `ALLOCATABLE`-array refactor
  (Phase 1); C++ refactor brought to parity in Phase 2.
- `intermediary_py/` — for Python `imogen_ghg_controller v0.1.0`
  (IPCC Tier-1 + RCMIP substitution + LPJG natural-flux aggregation).
- `tools/` — for cross-component utilities (`imogen_inputs_to_lpjg_format.py`
  adapter; `cmip6_nc_to_cmip5_ascii.py` converter; cleaned-up regrid).
- `runs/` — for per-scenario run setups (`runs/historic/`,
  `runs/SSP1-2.6/`, etc.).
- `data/` — for small reference data; large data documented in
  `data/DATA.md`.
- `scripts/` — for `run_coupled.sh` (workstation), `run_coupled.sbatch`
  (cluster), `cluster/` (owl helpers).
- `ci/` — for GitHub Actions / GitLab CI workflows.
- `docs/` — for unified technical manual + scientific framework +
  build instructions + troubleshooting + glossary.
- `paper/` — for manuscript draft + figures + cited PDFs.
- `notes/` — for per-step development notes.
- `archive/` — for frozen legacy code preserved for reference.

### Investigation evidence base (preserved at top level, immutable)

- `COUPLED_MODEL_INVESTIGATION.md` — 240 KB / 3 968 lines.
- `EXECUTION_PLAN.md` — 142 KB / 2 595 lines.
- `_phase2_findings/` — 8 reports, 424 KB / 6 507 lines total.

## Commands used

```bash
cd /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm

# 1. Initialise git
git init -b main

# 2. Create scaffolding directories
mkdir -p lpjguess imogen intermediary_py tools runs data scripts ci archive docs paper notes

# 3. Write top-level files
# (.gitignore, README.md, LICENSE, CITATION.cff, CONTRIBUTING.md, CHANGELOG.md
#  written via Cursor Write tool; see git history for content)

# 4. Write per-subdir placeholder README.md
# (one each in lpjguess/, imogen/, intermediary_py/, tools/, runs/, data/,
#  scripts/, ci/, docs/, paper/, notes/, archive/)

# 5. First commit + tag
git add .
git commit -m "Step 0: initialise unified codebase scaffolding (v0.1-skeleton)

- Top-level files: README.md, LICENSE, CITATION.cff, CONTRIBUTING.md,
  CHANGELOG.md, .gitignore.
- 12 top-level directory scaffolding (lpjguess, imogen, intermediary_py,
  tools, runs, data, scripts, ci, archive, docs, paper, notes), each with
  a placeholder README.md describing the planned contents per
  EXECUTION_PLAN.md Part V.
- Investigation evidence base preserved at top level (immutable):
  COUPLED_MODEL_INVESTIGATION.md (240 KB), EXECUTION_PLAN.md (142 KB),
  _phase2_findings/ (424 KB across 8 reports).

Verification: 'git status' clean after this commit; 'tree -L 2' shows
clean structure with all planned scaffolding in place.

Per EXECUTION_PLAN.md V.1 step 0 verification milestone."

git tag -a v0.1-skeleton -m "v0.1-skeleton: scaffolding initialised; rebuild begins"
```

## Verification

- ✅ `git init` succeeded (`Initialized empty Git repository in
  /.../lpj-guess_imogen_landsymm/.git/`).
- ✅ All 12 directories created.
- ✅ All 6 top-level files created
  (README.md / LICENSE / CITATION.cff / CONTRIBUTING.md /
  CHANGELOG.md / .gitignore).
- ✅ All 12 per-subdir READMEs created.
- ✅ Investigation docs and `_phase2_findings/` preserved at top level
  (not moved into `docs/` or `archive/`).
- ✅ `git status` clean after first commit.
- ✅ Tag `v0.1-skeleton` applied to first commit.

## What's NOT in this step

- No model code yet. `lpjguess/`, `imogen/`, `intermediary_py/`,
  `tools/` are empty placeholders.
- No data yet. `data/` is empty (just a README); `data/DATA.md` is
  not yet written (will be created in step 6 with full acquisition
  table).
- No CI configuration. `ci/` is empty (created in step 19).
- No docs beyond the per-subdir READMEs and the investigation
  evidence base. The `docs/technical_manual.md` etc. will be built
  in step 18.

These are all in the V.1 plan and will be filled in by subsequent
steps.

## Next: step 1

Import LPJ-GUESS LandSyMM fork → `lpjguess/`. Source from
`lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/` (NOT the predecessor
framework's `Integrations/trunk/trunk_r13078/`, to avoid the
`exit(200)` regression). Verify by building with `cmake .. && make`
and running a 4-cell × 3-year standalone CFX test.

See `EXECUTION_PLAN.md` §V.1 step 1 for the full specification.
