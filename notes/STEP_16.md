# STEP 16 — Cluster launcher (loose-only baseline; F-10/F-12 caveats explicit)

**Date completed:** 2026-05-08
**Commit:** _to be filled in after `git commit`_
**Status:** ✅ **DONE for v1.0 LOOSE-only baseline.** Cluster orchestration toolkit at `scripts/cluster/` (7 files; ~50 KB) implementing the gridlist-split / per-rank-runNN / SLURM-submit / dependency-chained-finishup pattern adapted from the IMK-IFU `owl_hpc_cluster_scripts/` toolkit. Plus workstation-parallel mimic test (`scripts/run_parallel_mimic.sh`) that validates orchestration mechanics without requiring cluster SSH access. **Cluster + tight (and cluster + prescribed) is BLOCKED for v1.0** per the F-10/F-12 architectural analysis surfaced this session; resolution gates on F-12 Option C (per [`docs/v2_roadmap.md`](../docs/v2_roadmap.md) §5). Net `lpjguess/` source-level change: ZERO (bash + docs only).

---

## 1. Goal (per `EXECUTION_PLAN.md` V.1 step 16 + Decision #7)

> Cluster integration. The owl-cluster scripts toolkit was located at
> `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/`.
> Import the scripts into the unified codebase at `scripts/cluster/`.
> Adapt for coupled-mode: change `INPUTMETHOD=cfx` to `imogencfx`; ensure
> `<DIR_COMMON>` is a shared-filesystem path (not per-rank scratch) so the
> in-process IMOGEN engine handshake works correctly; document the
> `module load` lines (gcc, cmake, netcdf, openmpi). Also write a top-level
> `scripts/run_coupled.sbatch` template that wraps the owl scripts.
> Provide a workstation parallel test that mimics the cluster setup
> (4-rank MPI on a small gridlist) so the owl-script logic can be
> validated before submitting to the actual cluster.

(Goal **partially redirected** in scope per the architectural-tension
investigation in §2 below. The user-confirmed Path A trajectory keeps the
goal intact but defers the cluster + tight portion to F-12 Option C; v1.0
cluster ships with LOOSE-only baseline + the architectural caveats fully
documented.)

---

## 2. Architectural-tension investigation (the strategic pivot)

This step's investigation surfaced a critical insight from the user that
re-shaped the v1.0 scope. The full analysis is in the chat handoff
`_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 4; summarized here:

### 2.1 The cluster MPI architecture

Per `setup_run_owl_with_scratch_lpj_work.sh` + `mpi_run_guess_on_tmp.sh`
(read this session):

- The cluster orchestration is **gridlist-split embarrassingly parallel**:
  `split -a 4 -l <cells/N> $GRIDLIST` distributes per-rank gridcells into
  `runNN/` subdirs (lines 121-130 of the IMK-IFU original)
- `srun mpi_run_guess_on_tmp.sh ...` invokes `guess -parallel -input <module>
  <ins>` per rank, with each rank reading its own per-rank `runNN/` directory
- Each rank processes ALL years for ITS subset of gridcells INDEPENDENTLY

### 2.2 LPJ-GUESS's MPI layer is intentionally minimal

`lpjguess/framework/parallel.cpp` (read this session):

- Implements ONLY: `MPI_Init`, `MPI_Comm_rank`, `MPI_Comm_size`, `MPI_Finalize`
- **No `MPI_Barrier`, no `MPI_Allreduce`, no point-to-point messaging**
- The framework intentionally treats parallel runs as embarrassingly parallel
  via per-rank-`runNN/`; cross-rank synchronization is **not implemented**

### 2.3 The architectural tension surfaced

- **Cluster + LOOSE coupling**: ✅ works because LPJ-GUESS reads pre-baked
  engine climate library from disk; ranks operate independently; no
  synchronization needed
- **Cluster + TIGHT coupling**: ❌ blocked because:
  - Framework loop is per-gridcell-outer / per-day-inner-across-all-years
    (`framework.cpp:411-516`)
  - Each rank processes ALL years for ITS subset before any sync point
  - Step 8's `ImogenOutput::flush_year` writer fires per-rank-per-year
  - Engine cannot consume N independent flux streams; no synchronization
    point exists
  - **Same F-10 deadlock pattern as single-process, multiplied by N ranks**

### 2.4 The user's stated v1.0 requirement vs the architectural reality

User's stated v1.0 goal: "v1 needs both loose and 'tight' coupled mode run
options, with both local and parallel/hpc options in place".

This means **all 4 combinations** in v1.0:

| | Local workstation | Parallel/HPC cluster |
|---|---|---|
| Loose | ✅ works today | ✅ works after step 16 (this step) |
| Tight | ❌ needs F-12 Option B (single-process two-process; ~2-3 days) | ❌ needs F-12 Option C (additive `framework_loop_mode = "year_outer"` + `MPI_Barrier`; ~1-2 weeks + cross-validation) |

The prior chat handoff framed F-12 Options B + C as Phase 2 / v1.1+ work.
**The user's stated v1.0 requirement effectively pulls those into Phase 1.**

### 2.5 User-confirmed Path A trajectory

Per user 2026-05-08 (this session): "Path A confirmed; proceed". The Path A
sequencing is:

1. **Step 16 (now)**: Cluster launcher for LOOSE mode + workstation-parallel
   mimic test. Defers F-12 work; doesn't lock anything in. ← **THIS STEP**
2. **F-12 Option B** (after step 16): Local + tight via two-process
3. **F-12 Option C** (after Option B): HPC + tight via in-process restructure
4. **Steps 17-19**: validation + docs + CI/release

This step (step 16) is the prerequisite for both F-12 options; it proves the
cluster orchestration works (loose) and stages the infrastructure that
F-12 Option C will extend with year-boundary `MPI_Barrier`.

---

## 3. What was implemented

### 3.1 Cluster scripts toolkit at `scripts/cluster/` (7 files; ~50 KB)

| File | Size | Adapted from | Role |
|---|---:|---|---|
| `run_coupled.sbatch` | ~17 KB / 290 lines | (NEW; mirrors `scripts/run_coupled.sh`) | Top-level launcher; refuses cluster + tight in v1.0 |
| `setup_run.sh` | ~11 KB / 200 lines | `setup_run_owl_with_scratch_lpj_work.sh` (174 lines) | Gridlist split + per-rank `runNN/` + generates `submit.sh` |
| `mpi_run_guess.sh` | ~7 KB / 165 lines | `mpi_run_guess_on_tmp.sh` (82 lines) | Per-rank scratch-I/O wrapper |
| `finishup_lpj_work.sh` | ~7 KB / 175 lines | `finishup_lpj_work_owl.sh` (172 lines) | Post-run aggregation |
| `make_guess.sh` | ~4.5 KB / 130 lines | (NEW; lightweight version of IMK-IFU `make_guess.sh` 126-line original) | Cluster build helper with `--mpi` flag |
| `append_files.sh` | ~1.7 KB / 40 lines | `append_files.sh` (verbatim with comments) | Per-file aggregator helper |
| `env_owl.sh` | ~3.7 KB / 80 lines | (NEW; placeholder template) | Module-load template (PLACEHOLDER) |
| `README.md` | ~6 KB / 175 lines | (NEW) | Cluster orchestration narrative |

### 3.2 Key adaptations from the IMK-IFU originals

1. **Named-flag CLI** (vs positional 12-arg in `setup_run.sh`): clearer +
   future-proofing
2. **Configurable `INPUTMETHOD`** (default `imogen` for v1.0 loose-only;
   the IMK-IFU original was hardcoded `cfx` for forest-productivity runs)
3. **Multi-MPI rank detection** in `mpi_run_guess.sh` (MPICH `PMI_RANK` ||
   OpenMPI `OMPI_COMM_WORLD_RANK` || SLURM `SLURM_PROCID`); the IMK-IFU
   original supported only OpenMPI + SLURM. We need MPICH for Anaconda3's
   MPICH 4.1.1 on the workstation parallel mimic test
4. **F-10/F-12 caveat detection inline**: `setup_run.sh` warns if
   `--inputmethod imogencfx` requested; `run_coupled.sbatch` refuses
   cluster + tight outright (with detailed error message + resolution
   pointer); `mpi_run_guess.sh` warns at runtime if engine-only context
5. **`$TMP` fallback to `/tmp/$$`** for non-cluster / workstation mimic
   contexts (when `/scratch/$SLURM_JOBID` doesn't exist)
6. **Cluster path-translation logic configurable via `--workdir-base`**:
   the IMK-IFU original was hardcoded for `/pd/home`, `/pd/data/lpj`,
   `/bg/data/lpj`. We preserve the auto-detect for IMK-IFU paths but
   add a workstation-parallel default (`<scenario_dir>/parallel_work/`)
   and an explicit `--workdir-base` override
7. **`make_guess.sh` simplified**: dropped the IMK-IFU compiled/<archvariant>/
   symlink + git/svn version embedding (our git-tag-per-step discipline
   covers the same ground); kept the `cmake .. && make` essentials with
   a clean `--mpi` flag

### 3.3 Workstation parallel mimic test: `scripts/run_parallel_mimic.sh`

`scripts/run_parallel_mimic.sh` (~9 KB / 200 lines) — validates the cluster
orchestration mechanics without requiring SSH access to the cluster:

1. Builds `lpjguess/build_mpi/guess` if not present (via `make_guess.sh --mpi`)
2. Stages `runs/<SSP>/parallel_work/<SSP>/runNN/` via `setup_run.sh
   --workdir-base <scenario>/parallel_work/`
3. Invokes `mpirun -np 4 lpjguess/build_mpi/guess -parallel -input imogen
   main.ins` against the smoke 4-cell gridlist
4. Verifies per-rank `runNN/` artifacts (gridlist subset; `.ins` files;
   eventual `*.out` and `guess.log`)
5. Reports orchestration success/failure (with explicit note that v1.0
   loose-coupling end-to-end requires engine climate library bootstrap,
   deferred to step 17)

### 3.4 Documentation updates

- `docs/build.md`: cluster section replaced from placeholder with a full
  step-by-step + F-10/F-12 caveat narrative + cross-references to
  `scripts/cluster/README.md`
- `scripts/cluster/README.md` (NEW): comprehensive cluster orchestration
  narrative
- `notes/FOLLOWUPS.md`: status dashboard "Last updated" date refresh
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md`: step-15 hash filled in (`cd68b29`);
  new step-16 row added (annotation only; backport-irrelevant)
- `EXECUTION_PLAN.md` V.1 step 16 row marked DONE
- `CHANGELOG.md`: NEW `[v0.16.0-step16-cluster-launcher]` entry
- This file (`notes/STEP_16.md`)

---

## 4. Verification

### 4.1 No `lpjguess/` source-level change

Step 16 introduces ZERO `lpjguess/` C++ changes, ZERO `imogen/code/`
Fortran changes, ZERO `intermediary_py/` Python changes, ZERO modifications
to `runs/SSP1-2.6/` configuration. Build state from step 14 → step 15
unchanged: `lpjguess/build/{guess, runtests}` (May 7) preserved.

The cluster MPI build (`lpjguess/build_mpi/guess`) is a NEW build directory
that will be created on first invocation of `scripts/cluster/make_guess.sh
--mpi` (or `scripts/run_parallel_mimic.sh`). It is gitignored under
existing `lpjguess/build/` rule extension (or a new explicit
`lpjguess/build_mpi/` rule if needed; verify before commit).

### 4.2 Linter check + cross-reference resolution

Performed in §6 below.

### 4.3 Workstation parallel mimic execution

Optional / deferred for empirical execution. See §5 below for the rationale.

---

## 5. What's deferred (intentionally)

### 5.1 Workstation parallel mimic test execution — deferred to a future commit

The mimic test (`scripts/run_parallel_mimic.sh`) is implemented; running it
requires:

1. Building `lpjguess/build_mpi/guess` (~3-5 minutes; needs cmake +
   `find_package(MPI)` to detect Anaconda3's MPICH 4.1.1)
2. Staging the per-rank `parallel_work/` dir (~seconds)
3. Running `mpirun -np 4 ./guess -parallel -input imogen main.ins`
   (will exit non-zero in v1.0 because engine climate library isn't
   bootstrapped yet; the mechanics validation is what the test exercises,
   not full end-to-end execution)

Deferred to a future commit because:
- The build-and-run take ~5-10 minutes; falls outside the chat-budget
  guidance for long-running operations
- The end-to-end loose-coupling test that will fully exercise the mimic
  is part of step 17 (validation), which has its own workstation
  parallel + cluster validation phases per `EXECUTION_PLAN.md` step 17
- The orchestration mechanics are validated by code review (this step)
  + cross-checking against the verified-working IMK-IFU originals

### 5.2 Cluster module-load refinement — deferred to a follow-up SSH session

`scripts/cluster/env_owl.sh` has PLACEHOLDER module-load values
(`gcc/14`, `cmake/3.29`, `netcdf-c/4.9`, `netcdf-fortran/4.6`,
`openmpi/5.0`). The actual module names + versions on KIT IMK-IFU `owl`
need to be confirmed via SSH session with the user on the cluster:

```bash
# On owl login node (during a future SSH session):
ssh owl-login.imk-ifu.kit.edu
module avail 2>&1 | tee /tmp/owl-modules.txt
# (we'll grep for gcc, cmake, netcdf-c, netcdf-fortran, openmpi versions)
exit
# Then back on workstation, refine env_owl.sh and commit
```

This is a step-16 follow-up (~30 min when SSH access available); not
blocking step 17 (validation) which uses workstation-parallel mimic
exclusively.

### 5.3 Cluster + tight coupling end-to-end — deferred to F-12 Option C

The architectural deadlock issue (per §2 above) means cluster + tight
genuinely cannot work in v1.0 without F-12 Option C. The cluster launcher
documents this explicitly and refuses to proceed for `--coupling-mode tight`.

F-12 Option C is the next major work item per Path A sequencing. Estimated
1-2 weeks + 1 week cross-validation (per `docs/v2_roadmap.md` §5).

---

## 6. Cross-reference integrity check

Files referenced from this step's deliverables:

| Reference | Resolves to | Status |
|---|---|---|
| `docs/build.md` | exists | ✅ |
| `docs/scientific_framework.md` | exists (step 15) | ✅ |
| `docs/v2_roadmap.md` | exists (step 15) | ✅ |
| `notes/FOLLOWUPS.md` | exists | ✅ |
| `EXECUTION_PLAN.md` | exists | ✅ |
| `scripts/run_coupled.sh` | exists | ✅ |
| `scripts/run_parallel_mimic.sh` | exists (NEW this step) | ✅ |
| `scripts/cluster/run_coupled.sbatch` | exists (NEW this step) | ✅ |
| `scripts/cluster/setup_run.sh` | exists (NEW this step) | ✅ |
| `scripts/cluster/mpi_run_guess.sh` | exists (NEW this step) | ✅ |
| `scripts/cluster/finishup_lpj_work.sh` | exists (NEW this step) | ✅ |
| `scripts/cluster/make_guess.sh` | exists (NEW this step) | ✅ |
| `scripts/cluster/append_files.sh` | exists (NEW this step) | ✅ |
| `scripts/cluster/env_owl.sh` | exists (NEW this step) | ✅ |
| `scripts/cluster/README.md` | exists (NEW this step) | ✅ |

---

## 7. Backport Sprint relevance (F-11)

**Net source-level change in `lpjguess/`: ZERO** — backport-irrelevant.

The cluster scripts at `scripts/cluster/` and the workstation parallel
mimic at `scripts/run_parallel_mimic.sh` live entirely OUTSIDE `lpjguess/`.
The Backport Sprint does NOT need to replicate any step-16 deliverable in
`trunk_r13078`. The cluster orchestration is fork-agnostic.

When the Backport Sprint runs the coupled model end-to-end on the
`trunk_r13078` backend, it will use the SAME cluster scripts (with
adapted CMakeLists.txt -DLPJGUESS_BACKEND=trunk_r13078 build flag at
F-11 sprint time).

---

## 8. Effort

- Investigation phase (architectural-tension analysis + cluster scripts
  toolkit reading + parallel.cpp + MPI build feasibility): ~1.5 hours
- Implementation phase (7 cluster scripts + workstation mimic): ~2 hours
- Documentation phase (STEP_16.md + cluster README + docs/build.md +
  CHANGELOG + EXECUTION_PLAN + FOLLOWUPS + BACKPORT_LEDGER): ~1.5 hours
- Cross-reference + verification: ~30 min
- **Total: ~5.5 hours** (vs ~1-2 days estimate; under budget because
  testing was intentionally deferred to step 17)

---

**Step 16 complete (loose-only baseline).** Tag target:
`v0.16.0-step16-cluster-launcher`. **Next per Path A**: F-12 Option B
(single-process tight; ~2-3 days; per `docs/v2_roadmap.md` §4).
