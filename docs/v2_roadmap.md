# v2.0 roadmap — what comes after v1.0

**Version:** v0.15.0 (created at step 15 of the unified-codebase rebuild,
2026-05-08).

**Purpose:** Document the planned post-v1.0 development trajectory:
v1.1 (Phase 2A two-process tight coupling), v1.2 (validation), and v2.0
(in-process restructure + PLUM embedding). This is the canonical reference
for what the project's stretch goals are and how they sequence after Phase 1
ships.

**Companions:**
- [`docs/scientific_framework.md`](scientific_framework.md) — Stage I → Stage II
  protocol; F-10 caveat; Decision #10 save_state/restart pattern
- `notes/FOLLOWUPS.md` — F-1 through F-13 dashboard with timing per item
- `EXECUTION_PLAN.md` Part V — operational rebuild plan (steps 0–19 = v1.0;
  20+ = post-v1.0)

---

## 1. Phase 1 vs Phase 2 trajectory

```
Phase 1  (= v1.0; steps 0-19; v1.0.0 release)
   │
   ├─ steps 0-14  ✅ DONE (v0.1-skeleton → v0.14.0-step14-launcher)
   ├─ step 15      ⏳ documentation preservation + PLUM verify (THIS step)
   ├─ step 16      ⏳ cluster launcher (KIT IMK-IFU `owl`)
   ├─ step 17      ⏳ end-to-end validation (LOOSE-coupling fallback for v1.0)
   ├─ step 18      ⏳ documentation completion
   ├─ step 19      ⏳ CI/CD + Zenodo DOI + GMD paper submission
   │
   ▼
Phase 2A (= v1.1; F-12 Option B)
   │
   ├─ Two-process tight coupling (split imogen_lpjg engine into a separate
   │  concurrent Fortran process; existing file-based handshake provides the
   │  rendezvous layer)
   ├─ Estimated 2-3 days work
   ├─ Unblocks: real closed-loop NEE feedback; step 8's writer fires;
   │  bug C35 testable; first scientifically-rigorous tight-coupling run
   │
   ▼
Phase 2B (= v1.2; validation against working paper §2.5 thresholds)
   │
   ├─ Tight vs loose comparison for SSP1-2.6, SSP2-4.5
   ├─ Compare per-gridcell-rolling handshake bias vs proper synchronization
   ├─ Estimated 1 week
   │
   ▼
Phase 3   (= v2.0; F-12 Option C + PLUM embedding)
   │
   ├─ Additive `framework_loop_mode = "year_outer"` ins parameter
   ├─ Per-year-outer / per-gridcell-inner loop alongside the existing
   │  per-gridcell-outer / per-day-inner-across-all-years loop
   ├─ Globally-synchronized NEE feedback (proper closed-loop)
   ├─ PLUM embedding (Stage I re-coupled into the unified codebase)
   ├─ Estimated 1-2 weeks (Option C) + 2-3 weeks (PLUM embedding)
```

---

## 2. PLUM embedding (Stage I in v2.0)

### 2.1 What v1.0 did NOT do (per Decision #9)

v1.0 reuses the existing PLUM-harm `forLPJG` outputs at
`/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/<scenario>/...`
(per [`data/DATA.md`](../data/DATA.md) §1) as Stage II input. Stage I and
PLUM are **not run** as part of the v1.0 framework.

### 2.2 What v2.0 will do

Re-embed Stage I and PLUM into the unified codebase orchestration. Concrete
trajectory:

1. **Stage I LPJG run (`do_potyield 1`)** invoked from the launcher
   `scripts/run_coupled.sh` with prescribed ISIMIP3b climate (MRI-ESM2-0
   GCM per the working paper §2.4.3); outputs yield surfaces to
   `runs/<scenario>/stage1_yields/`.

2. **PLUM v2 invocation** as a launcher-orchestrated step. Two
   sub-options:
   - **2a (recommended)**: PLUM is wrapped as a Python module the launcher
     calls; inputs are Stage I yields + scenario demand; output is harmonised
     LU at 0.5° × 0.5° × 1850–2100. Requires PLUM team coordination + Python
     wrapping work.
   - **2b (lighter)**: PLUM is invoked as an external CLI tool the launcher
     wraps via subprocess; inputs/outputs same as 2a but PLUM remains a
     standalone codebase. Easier to land but less integrated.

3. **landsymm_py post-processing**: convert PLUM outputs to LPJG-readable
   `forLPJG` format (5 files: `landcover.txt`, `cropfractions.txt`,
   `irrig.txt`, `nfert.txt`, `landcover_peatland.txt`) per the existing
   schema (see [`scientific_framework.md`](scientific_framework.md) §3.2).
   The user's `landsymm_py` codebase already does this; v2.0 either embeds
   it or invokes it as a subprocess.

4. **Stage II coupled run (`do_potyield 0`)** consumes the PLUM-harm
   `forLPJG` outputs. By this point F-12 Option C is in place so the
   coupling is genuinely closed-loop.

### 2.3 v2.0 Stage I parameter checklist

The integrated LTS / LandSyMM_LPJ-GUESS fork (= our `lpjguess/`) already has
all required parameters in the source tree per
`landsymm_runtime_parameters.md §6`:

| Parameter | Where | Description |
|---|---|---|
| `do_potyield` | `landcover.ins` | 0 = production mode (Stage II); 1 = factorial mode (Stage I) |
| `isforpotyield` | `crop_n_stlist*.ins` | Mark stand types that participate in factorial Stage I |
| `N_appfert_mt` | `crop_n_stlist*.ins` | Per-stand-type N fertilisation rate (kg N/m²) |
| `hydrology` | `crop_n_stlist*.ins` or management blocks | `rainfed | irrigated | irrigated_wilt | irrigated_sat | inundated` |

**v2.0 Stage I `runs/<scenario>_stage1/` setup**:
- `main.ins`: enables `do_potyield 1` via import of a Stage I-specific
  `landcover.ins`
- `crop_n_stlist.simplePFT.remap10_g2p.<treatments>.ins`: define the 6
  management treatments via `isforpotyield 1` + per-stand `N_appfert_mt`
- prescribed climate via `-input cfx` and ISIMIP3b NetCDF inputs

### 2.4 Why this is post-v1.0

- **Coordination cost**: PLUM team coordination + landsymm_py orchestration
  setup is substantial (estimated 2-3 weeks)
- **Existing outputs are sufficient for v1.0 paper**: the user's prior
  landsymm_py + Stage I + PLUM runs produced PLUM-harm `forLPJG` outputs
  that v1.0 reuses for its 5 SSPs (see
  [`data/DATA.md`](../data/DATA.md) §1)
- **v1.0 paper deliverable does not require Stage I re-execution**: the
  scientific story (anthropogenic emissions inventory + climate-emulator
  closed-loop) is the v1.0 contribution; Stage I re-embedding is a
  follow-up paper / v2.0 deliverable

---

## 3. v1.1 — wire save_state/restart with PLUM-harm forLPJG outputs

### 3.1 Scope

Wire Decision #10's save_state/restart pattern (Option D = Option B over
save_state/restart) to enable v1.0/v1.1 runs against the PLUM-harm forLPJG
outputs at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/`.

### 3.2 Concrete deliverables (estimated 0.5–1 day)

1. **Per-phase `imogen_intermediary.ins` variants** at `runs/<scenario>/`:
   - `main_historic.ins` — `restart 0`, `save_state 1`, `state_year 2020`,
     `lasthistyear 2020`, `firstoutyear 1850`, `lastoutyear 2020`. References
     historic-only LU forcing (the HILDA+ v2 prefix at the same
     `/media/bampoh-d/...` directory).
   - `main_scenario.ins` — `restart 1`, `save_state 0`, `state_year 2020`,
     `lasthistyear 2100`, `firstoutyear 2021`, `lastoutyear 2100`. References
     PLUM-harm forLPJG scenario LU 2021–2100.

2. **Launcher flag `--phase historic | scenario | both`** in
   `scripts/run_coupled.sh`:
   - `historic`: invoke main_historic.ins
   - `scenario`: invoke main_scenario.ins (assumes historic state exists)
   - `both` (default): invoke historic, then scenario, in sequence

3. **Per-scenario state-files directory**: `runs/<scenario>/state/`
   (gitignored; created at historic phase end).

### 3.3 Why this is v1.1, not v1.0

- v1.0's smoke test uses the legacy concatenated 1901–2100 LU (Option C) for
  simplicity per user guidance 2026-05-07
- All 5 SSP scenarios need this if we want to expand beyond SSP1-2.6 (the
  other 4 SSPs were never pre-concatenated; see
  [`data/DATA.md`](../data/DATA.md) §2)
- v1.1's two-process F-12 work is the natural moment to also wire this up —
  both touch the run-config layer and the launcher

---

## 4. F-12 Option B (v1.1 Phase 2A) — two-process tight coupling

### 4.1 Why Option B is the v1.0 → v1.1 stopgap

Per the prior chat handoff Part 7 §35.2:

- The polling-loop architecture (now correct after step 7's bug-C2/C3 fixes)
  was originally **designed** for two-process operation
- The in-process `RUN_IMOGEN_ENGINE` wrapper at `climatemodel.cpp` was a
  convenience that broke this design
- File-based handshake (already implemented at step 8 of the rebuild) provides
  the rendezvous layer
- Per-gridcell-rolling year-change-detection in `imogenoutput.cpp::outannual`
  (step 8) writes year-(N) handshake when each gridcell's outannual fires —
  by the time the LAST gridcell flushes year-N, all cells have processed
  year-N. This is **scientifically defensible** for v1.1 (predecessor's
  working paper used loose coupling, which is even less synchronized)

### 4.2 Concrete deliverables (estimated 2-3 days)

1. **`lpjguess/modules/imogencfx.cpp`** (~5 LOC change):
   - Make `RUN_IMOGEN_ENGINE()` invocation conditional on
     `coupling_mode != "two_process"` (or new value `"tight"` reused with
     a launcher-side detection of separate process)
   - In two-process mode, just skip the in-process engine launch; the
     launcher invokes it separately

2. **`lpjguess/framework/parameters.h/cpp`** — add `"two_process"` value to
   `coupling_mode` enum or replace the in-process behaviour gating

3. **`scripts/run_coupled.sh`** (~30-50 LOC):
   - Add `--coupling-mode two_process` branch
   - Launch `imogen_lpjg` engine binary in background:
     `imogen/code/imogen_lpjg & PID_ENGINE=$!`
   - Launch `guess` in foreground (or backgrounded; capture PID)
   - Wait for both; trap SIGINT to kill both; collect exit codes;
     produce a unified log

4. **`scripts/cluster/run_coupled.sbatch`** (~20 LOC; lands at step 16):
   - Same pattern; SLURM-aware with `--ntasks=2` allocation
   - Per-rank scratch directory shared via the cluster's shared filesystem

5. **`runs/SSP1-2.6/imogen_intermediary.ins`** Option C (relative-path
   tight-mode block; currently un-testable in v1.0) becomes the default
   for `--coupling-mode two_process`. Option A (static IIASA) remains
   available as a sensitivity-study backbone

6. **`tests/integration/`** (NEW; ~100 LOC):
   - End-to-end test running engine + LPJG concurrently for 5 years
   - Assertions: `imogen_lpjg_flux.txt` contains 5 rows with monotonic Year +
     plausible NEE values; engine produces 5 year-output dirs

### 4.3 v1.1 verification milestone

A full SSP1-2.6 coupled run for 4-cell `gridlist_test2.txt` for years
1850–1860 (11 years) completes successfully on the user's workstation:

- Engine produces 11 year-output dirs at
  `Common-directory/IMOGEN/output/{1850..1860}/`
- LPJG produces 11 rows in `Common-directory/LPJG_main/IMOGEN/imogen_lpjg_flux.txt`
  with monotonic Year column and plausible NEE values (PgC/yr; mostly negative
  pre-industrial = land sink)
- Cross-check: engine's `CO2_all.dat` final value matches a 0–5 ppm tolerance
  against a control loose-coupling run (small differences expected due to
  per-gridcell-rolling handshake)
- LPJG outputs in `runs/SSP1-2.6/{cflux,mch4,ngases}.out` show non-zero data
  for all 11 simulated years

---

## 5. F-12 Option C (v2.0 Phase 3) — in-process restructure with `framework_loop_mode`

### 5.1 The user's preferred long-term approach (per F-10 phase-2 entry)

Per user guidance recorded in `notes/FOLLOWUPS.md` F-10 §"Phase-2 recommended
approach" (2026-05-06):

> "after we are done with phase 1 and addressed all follow ups in the follow
> up document at the end, and have a single working version 1 of the full,
> entire coupled model (that can be run loose and 'tight', local workstation
> or parallel) in place, and move on to phase 2 to do the proper tight
> coupling implementation where we might need to fundamentally alter the
> framework — it would be best if rather than alter the framework behavior,
> we establish a runtime parameter which when turned on in ins files, invokes
> some code we add to framework that takes things down the tightly coupled
> model run route, without altering the the original framework, or something
> like that (similar to how we added landsymm-related code and corresponding
> runtime parameters to produce landsymm fork behavior in the integrated lts
> without altering the lts behavior when we did the integration project much
> earlier in our chat and before the current coupled model project)."

This is the **additive parameter-gated code-path** pattern that mirrors the
LandSyMM-fork-into-LPJ-GUESS-LTS integration. It is the user's settled
long-term direction.

### 5.2 Concrete deliverables (estimated 1-2 weeks + 1 week cross-validation)

1. **NEW ins parameter `framework_loop_mode`** in `framework/parameters.h/.cpp`:
   - Default: `"gridcell_outer"` (preserves existing behaviour)
   - New: `"year_outer"` (alternative loop ordering; required for proper
     closed-loop tight coupling)

2. **`framework.cpp` modifications** (~50–100 LOC, additive):
   - At top of `framework()`, branch on `loop_mode`
   - If `"year_outer"`: pre-load all gridcells into memory (or per-rank
     chunks for MPI), then loop per-year (outer) × per-gridcell (inner) ×
     per-day (innermost). Globally-synchronized year-end synthesis point.
   - If `"gridcell_outer"`: existing code unchanged

3. **Cross-validation protocol** (essential before Option C ships):
   - Pick a test scenario (e.g. SSP1-2.6, 5-cell gridlist, 1900–2010)
   - Run both modes with identical seeds
   - Compare `cflux.out`, `cmass.out`, `mch4.out`, `ngases.out` cell-by-cell
   - Acceptable difference: bit-exact for deterministic outputs (e.g.
     soil-water budget); ≤ 1% for stochastic outputs (fire spread,
     vegetation establishment)
   - If divergence exceeds tolerance, investigate PRNG state-management

### 5.3 Memory considerations for Option C

For 62 538 cells × ~1 MB-each in-memory state at production scale:

| Configuration | Memory pressure |
|---|---|
| Workstation (single process) | ~62 GB. Comfortable on 96 GB+ workstations |
| HPC node (16 ranks of 4000 cells each) | ~4 GB/rank. Trivial |
| MPI (existing per-rank gridlist subsetting) | Already implemented in `lpjguess/parallel_version/` |

The predecessor's per-rank gridlist subsetting pattern (the
`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/`
toolkit's split-via-`split -a 4` orchestration) inherits naturally into the
Option C path; no new MPI infrastructure work.

---

## 6. Other post-v1.0 stretch items (Phase 2 / Phase 3 candidates)

### 6.1 F-3 — Numerical parity between Fortran and C++ IMOGEN engines

Per Decision #2: Phase 2 brings the C++ refactor (`IMOGENCXX/`; archived at
v1.0) to numerical parity with the Fortran engine; both backends become
runtime-switchable.

- 14 known bugs in C++ refactor (C14–C27 per the prior handoff Part 6 §24.4)
- Estimated 1–2 weeks
- Unlocks: faster engine execution; potentially MPI-friendly embedding

### 6.2 F-11 — Backport sprint to `trunk_r13078`

Per Decision #3: replicate every `lpjguess/` change in our LandSyMM_LPJ-GUESS
base into the `trunk_r13078` fork (the fork the working paper's Stage 1 PLUM
yield runs used) for paper-stage consistency.

- Per `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 ledger (running list of all
  source-level changes across steps 0–14)
- Estimated 1–2 days
- Add `--lpjg-backend trunk_r13078 | landsymm_fork` build-time flag

### 6.3 F-13 — Paper-stage comparative-analysis framework

Per the prior chat handoff Part 5 §13.1: 3-axis comparison framework
(GHG concentrations × climate trends × LPJG ecosystem outputs) with 9
specific paper revisions. Leverages existing `comparative_analysis/analysis/`
template scripts in `version_A/.../Python-scripts/`.

- Post-v1.0 release
- Drives the GMD paper's results section

### 6.4 F-9 — Climate-input diagnostic outputs in `miscoutput`

Per the prior chat handoff Part 6: 12 half-scaffolded `out_*_anom` Table
member declarations + 12 `file_*_anom` ins-file param declarations need
their `create_output_table()` + per-month accumulator wiring completed.

- Refined at step 9.5: blocked on `Climate` class needing per-month
  accumulator arrays (currently only single-day fields + 20-year-window
  aggregates)
- Estimated 0.5–1 day after the per-month accumulator infrastructure is added
- Best timing: alongside Phase 2A or 2B work on the climate output side

### 6.5 F-1 — Zenodo upload of IMOGEN data tarballs

Per `tools/imogen_data_manifest.txt`: 4 GCM-pattern + CRUNCEP tarballs (49 MB
total) currently sit at the user's workstation only. For external
reproducibility (paper code+data availability statement), upload to Zenodo
(or GitHub Releases) and update README references.

- Estimated 30 min
- Best timing: at v1.0 release time (~step 19)

---

## 7. v2.0 release criteria

By the time we tag `v2.0.0`:

| Criterion | Source |
|---|---|
| Stage I + PLUM embedded into the launcher orchestration | §2 above |
| Both `gridcell_outer` and `year_outer` framework loop modes runtime-switchable | §5 above |
| Cross-validation passes between the two loop modes | §5.2 above |
| C++ IMOGEN brought to numerical parity with Fortran (F-3) | §6.1 above |
| `trunk_r13078` backport sprint complete (F-11) | §6.2 above |
| All 13 of F-1 through F-13 closed | `notes/FOLLOWUPS.md` |
| Paper-stage 3-axis comparative analysis runnable (F-13) | §6.3 above |
| Documentation updated to v2.0 (this file gets superseded) | step-19-equivalent |
| Tag `v2.0.0` pushed to all 3 remotes; new Zenodo DOI | release ceremony |

— Generated at step 15 (2026-05-08) of the unified-codebase rebuild.
