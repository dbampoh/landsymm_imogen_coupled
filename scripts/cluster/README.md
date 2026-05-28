# `scripts/cluster/` — SLURM cluster orchestration for LandSyMM-IMOGEN

**Created at:** step 16 of the unified-codebase rebuild (2026-05-08).
**Status:** **v1.0 LOOSE-only.** Cluster + tight is BLOCKED until F-12 Option C
lands (per [`docs/v2_roadmap.md`](../../docs/v2_roadmap.md) §5).

This directory contains the SLURM cluster launcher for running the coupled
LandSyMM-IMOGEN model on the KIT IMK-IFU `owl` cluster (or any SLURM-managed
HPC cluster with similar configuration).

---

## Architecture overview

The cluster launcher follows the **gridlist-split embarrassingly-parallel
pattern** that the IMK-IFU `owl_hpc_cluster_scripts/` toolkit established for
LPJ-GUESS production runs. Adapted minimally for our v1.0 unified codebase:

```
                ┌──────────────────────────────────┐
                │ scripts/cluster/run_coupled.sbatch│   <-- top-level launcher (mirrors
                │     (top-level SLURM wrapper)    │       scripts/run_coupled.sh CLI)
                └──────────────┬───────────────────┘
                               │
                               ▼
       ┌──────────────────────────────────────────────────────┐
       │ scripts/cluster/setup_run.sh                         │
       │   - Splits gridlist into N=nodes×cpu-per-node chunks │
       │   - Creates per-rank runNN/ subdirs with .ins copies │
       │   - Generates per-scenario submit.sh + startguess.sh │
       └──────────────────────────────────────────────────────┘
                               │
                               │ (operator runs `bash startguess.sh` in scenario dir)
                               ▼
                        ┌──────────────────┐
                        │ sbatch submit.sh │
                        └────────┬─────────┘
                                 │
                                 ▼
                ┌──────────────────────────────────────┐
                │ srun mpi_run_guess.sh (N parallel)   │
                │   - Each rank rsync's runNN/ to     │
                │     /scratch/$JOBID/output/runNN/   │
                │   - Each rank: guess -parallel \    │
                │       -input <module> <ins>         │
                │   - rsync results back to work dir   │
                └────────┬─────────────────────────────┘
                         │
                         │ (afterok dependency)
                         ▼
       ┌────────────────────────────────────────────────────────┐
       │ sbatch finishup_lpj_work.sh                            │
       │   - Concatenates per-rank runNN/*.out                  │
       │   - Concatenates per-rank guess.log                    │
       │   - Optional postproc.sh                               │
       │   - md5sum + gzip; copies to output-YYYY-MM-DD/        │
       └────────────────────────────────────────────────────────┘
```

---

## Files

| File | Role |
|---|---|
| `run_coupled.sbatch` | Top-level launcher; mirrors `scripts/run_coupled.sh` CLI; refuses cluster + tight in v1.0 (F-12 Option C blocker) |
| `setup_run.sh` | Per-scenario staging: gridlist split + per-rank `runNN/` + generates `submit.sh` + `startguess.sh` |
| `mpi_run_guess.sh` | Per-rank scratch-I/O wrapper (invoked via `srun`); MPICH+OpenMPI+SLURM rank detection |
| `finishup_lpj_work.sh` | Post-run aggregation: concatenates per-rank `*.out`, gzips, copies to `output-YYYY-MM-DD/` |
| `make_guess.sh` | Cluster-side build helper (`--mpi` flag for MPI build via `mpicxx`) |
| `append_files.sh` | Per-file aggregator (concatenates `runNN/*.out` with awk-based header skip) |
| `env_owl.sh` | Module-load template for IMK-IFU `owl` partition (PLACEHOLDER VALUES; refine via SSH on actual cluster) |
| `README.md` | This file |

---

## v1.0 status — what works, what's blocked, what's deferred

### Works end-to-end (the v1.0 cluster deliverable)

✅ **Cluster + LOOSE coupling**: LPJ-GUESS reads pre-baked engine climate
library from disk (the engine produces it standalone first; LPJG ranks then
each consume their gridlist subset's climate independently). This is the
default for `--coupling-mode loose` (which maps to `-input imogen` for
LPJ-GUESS internally). Embarrassingly parallel; the cluster's existing
gridlist-split pattern handles it natively.

### Blocked in v1.0 — gates on F-12 Option C

❌ **Cluster + TIGHT coupling**: per the prior chat handoff Part 7 + this
session's investigation, the LPJ-GUESS framework loop
(`framework.cpp:411-516`) is per-gridcell-outer / per-day-inner-across-all-years.
On cluster, ranks process their gridlist subsets independently — there's no
`MPI_Barrier` at year boundaries (per `lpjguess/framework/parallel.cpp`,
which implements only `MPI_Init`/`Comm_rank`/`Comm_size`). Step 8's
`ImogenOutput::flush_year` writer fires per-rank-per-year; the IMOGEN engine
cannot consume N independent flux streams at a synchronization point. Same
deadlock pattern as single-process F-10, multiplied by N ranks.

**Resolution**: F-12 Option C — add additive `framework_loop_mode = "year_outer"`
ins parameter that gates a per-year-outer / per-gridcell-inner loop alongside
the existing default. Year boundary becomes a natural `MPI_Barrier` rendezvous
point. Per-rank gridlist subsetting (existing pattern) inherits naturally.
See [`docs/v2_roadmap.md`](../../docs/v2_roadmap.md) §5 for the concrete
implementation sketch.

❌ **Cluster + PRESCRIBED coupling**: same architectural issue as cluster +
tight (engine reads static-IIASA flux files; per-rank synchronization gap
still applies; deadlocks same way after ~32 engine-years per rank). The
`run_coupled.sbatch` will print a warning if `--coupling-mode prescribed` is
requested and recommend `loose` instead.

### Deferred to step 17 (validation)

⏳ **End-to-end loose-coupling validation on workstation**: the
`scripts/run_parallel_mimic.sh` workstation-parallel test exercises the
orchestration mechanics (gridlist split + per-rank invocation + output
concatenation) but does NOT yet bootstrap the engine climate library — that
wiring is part of step 17's full-stack loose-coupling validation. The mimic
test as currently written validates the orchestration; full end-to-end
loose-coupling exercise comes at step 17.

### Deferred to step 16 follow-up — cluster module-load refinement

⏳ **`env_owl.sh` placeholder values**: the exact module names + versions
on the KIT IMK-IFU `owl` cluster need to be confirmed via SSH session with
the user on the actual cluster. The placeholders (`gcc/14`, `cmake/3.29`,
`netcdf-c/4.9`, `netcdf-fortran/4.6`, `openmpi/5.0`) come from the prior
chat handoff Part 4 §17 educated-guess; the user will SSH into `owl`,
run `module avail`, and we'll commit the refined values as a follow-up.

---

## Usage

### Production cluster run (when SSH-ready and module-loads refined)

```bash
# On the cluster login node:
cd /path/to/lpj-guess_imogen_landsymm/runs/SSP1-2.6
source ../../scripts/cluster/env_owl.sh    # refined module loads

# Build LPJ-GUESS with MPI
bash ../../scripts/cluster/make_guess.sh --mpi

# Stage + submit a loose-coupling run on owl partition
sbatch ../../scripts/cluster/run_coupled.sbatch \
    --scenario SSP1-2.6 \
    --coupling-mode loose \
    --partition cclake \
    --nodes 2 \
    --cpu-per-node 80 \
    --walltime 03:00:00

# Watch the queue
squeue -u $USER

# Tail per-rank logs
tail -f $WORK_DIR/SSP1-2.6/run1/guess.log
```

### Workstation parallel mimic test (no SSH; validates orchestration)

```bash
cd /path/to/lpj-guess_imogen_landsymm
bash scripts/run_parallel_mimic.sh --np 4 --scenario SSP1-2.6
```

This:
- Builds `lpjguess/build_mpi/guess` if not present
- Stages `runs/SSP1-2.6/parallel_work/SSP1-2.6/runNN/` with the smoke
  4-cell gridlist split into 4 per-rank chunks
- Invokes `mpirun -np 4 guess -parallel -input imogen main.ins`
- Verifies per-rank artifacts

The test is expected to exit non-zero in v1.0 because the engine climate
library isn't bootstrapped (deferred to step 17); the mimic validates the
orchestration mechanics regardless.

---

## Adapting for non-IMK-IFU clusters

The launcher is designed to be portable across SLURM-managed clusters with
minimal adaptation. To adapt:

1. **Module loads**: copy `env_owl.sh` → `env_<your-cluster>.sh`; refine
   module names/versions for your cluster (use `module avail`).
2. **Path translation**: `setup_run.sh` has cluster-path translation logic
   (lines ~80-100; matches `/pd/home`, `/pd/data/lpj`, `/bg/data/lpj`).
   Override via `--workdir-base <PATH>` flag for non-matching clusters,
   or extend the if-elif block for your cluster's filesystem layout.
3. **Partition names**: pass `--partition <YOUR_PARTITION>` to
   `run_coupled.sbatch`. Default is unset; the launcher refuses to proceed
   without it.

---

## References

- `EXECUTION_PLAN.md` V.1 step 16 — cluster integration milestone
- `EXECUTION_PLAN.md` Decision #7 — single codebase + binary serves both
  workstation and cluster
- `EXECUTION_PLAN.md` Decision #8 — Anaconda3 NetCDF preference (workstation);
  cluster uses module-loaded NetCDF/HDF5/openmpi
- `notes/STEP_16.md` — per-step verification record
- `notes/FOLLOWUPS.md` F-10 — architectural deadlock; per-gridcell-outer loop
  vs per-year-globally-synchronized handshake
- `notes/FOLLOWUPS.md` F-12 — multi-pass / two-process tight-mode design;
  Option B (single-process) and Option C (in-process restructure)
- `docs/scientific_framework.md` §5 — F-10 architectural caveat narrative
- `docs/v2_roadmap.md` §5 — F-12 Option C concrete sketch (the cluster + tight
  resolution path)
- IMK-IFU originals at `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/`
  — the prior-art cluster orchestration this directory adapts from
- `lpjguess/parallel_version/aurora.tmpl` — the upstream LPJ-GUESS canonical
  SLURM template (cross-reference for the gridlist-split + mpirun pattern)

— Generated at step 16 (2026-05-08) of the unified-codebase rebuild.

---

## Block 8.4 pre-cluster prep — Track 2 T_seq cluster launch (added at block 8.2.5 FULL close 2026-05-27 session 12 day 2)

At block 8.2.5 FULL close (Phase G user choice = δ-B-variant trunk-C++ engine throughout), 10 cluster production run-dirs were authored at `forks/trunk_r13078_runs/<SSP>_cluster_<phase>/` (5 SSPs × hist+scen) mirroring the user's established Track-1 wpeat hist+ssp{126,…}_wpeat pattern at `/media/bampoh-d/landsymm_imogen_runs_cluster_mirror_2026-05-21/`. Each cluster run-dir contains 14 .ins files + a `setup_run_tseq.sh` wrapper + (for `_hist` dirs) a `state/` subdir.

### Original Track 1 cluster workflow (user's established pattern; verified 2026-05-27)

```
1. cd <run-setup-dir>                                  (e.g., integrated-4.1-ins2_landsymm_ssp126_wpeat/)
2. mkdir state/                                        (manual creation before initiating)
3. ./setup_run.sh                                      (5-line run-dir-local wrapper)
4.   → setup_run_owl_with_scratch_lpj_work.sh \        (the IMK-IFU workhorse)
       <runname> main.ins "extra-ins-files" \
       gridlist_in_62892_and_climate.txt cfx ""        (cfx = Track 1 inputmethod)
       2 owl genius 8 genius 128                       (2 nodes × 128 CPUs = 256 ranks @ genius)
     - Creates per-rank dirs on /bg/scratch/...
     - cp .ins files to each rank dir
     - Splits gridlist into 256 chunks
     - Generates submit.sh + startguess.sh in work dir
5. cd <work-dir>                                       (scratch dir where rank dirs live)
6. ./startguess.sh                                     (calls sbatch submit.sh)
7. srun mpi_run_guess_on_tmp.sh × 256 ranks
     - Each: guess -parallel -input cfx main.ins        (on its gridlist chunk)
8. afterok: finishup_lpj_work_owl.sh                   (concat + compress + dated output dir
                                                         in <run-setup-dir>/)
9. state/ subdir in <run-setup-dir>/ contains saved state files (hist phase only)
```

### Revamped `scripts/cluster/` (v1.0 unified-codebase rebuild; this dir) — workflow comparison

| Component | Original (IMK-IFU `owl_hpc_cluster_scripts/`) | Revamped (this dir) | Notes |
|---|---|---|---|
| Top-level entry | User's per-run-dir 5-line `setup_run.sh` | `run_coupled.sbatch` (unified CLI with `--scenario`, `--coupling-mode`, `--production` etc.) | Revamped designed around rebuild's `runs/<SSP>/`; for Track 2 T_seq we use per-cluster-dir `setup_run_tseq.sh` wrapper |
| setup_run.sh interface | Positional 12-arg | Named flags | Same functional purpose |
| Default INPUT_MODULE | `cfx` (Track 1) | `imogen` (loose-coupling) | We override to `imogencfx` for Track 2 T_seq |
| Coupling mode | N/A (cfx = loose by design) | `loose` only (tight + cluster BLOCKED until F-12 Option C) | T_seq is conceptually loose (pre-baked climate) |
| Binary | `compiled/<archvariant>/guess` symlink | `lpjguess/build_mpi/guess` (rebuild) or `forks/trunk_r13078/build_owl/guess` (Track 2 T_seq) | We point at `forks/trunk_r13078/build_owl/guess` for Track 2 T_seq |
| mpi_run script | `mpi_run_guess_on_tmp.sh` (rsync-to-tmp) | `mpi_run_guess.sh` (rsync-to-scratch) | Functionally same |
| finishup | `finishup_lpj_work_owl.sh` | `finishup_lpj_work.sh` | Functionally same |
| State path | Implicit (manually-created state/ in run-dir) | **Explicit `state_path` in main.ins** (absolute cluster path) | Cleaner; our cluster .ins set state_path absolute per `forks/trunk_r13078_runs/<SSP>_cluster_hist/state/` |

### Track 2 T_seq cluster launch — two viable paths

**Path B — Per-cluster-dir `setup_run_tseq.sh` wrapper** (RECOMMENDED; mirrors your Track-1 mental model exactly):

```bash
# Sequence: hist FIRST then scen (scen restarts from hist saved state)

# 1. HIST phase (5 SSPs; can be parallel via 5 separate SBATCH jobs)
cd forks/trunk_r13078_runs/SSP1-2.6_cluster_hist
./setup_run_tseq.sh                  # invokes scripts/cluster/setup_run.sh with imogencfx + cluster paths
cd $WORK_BASE/SSP1-2.6_cluster_hist  # cluster work dir
bash startguess.sh                   # sbatch submit.sh + chain finishup
# (repeat for SSP2-4.5_cluster_hist, ..., SSP5-8.5_cluster_hist)

# 2. (Wait for all HIST runs to complete + state/ populated)

# 3. SCEN phase (5 SSPs; each restarts from corresponding <SSP>_cluster_hist/state/)
cd forks/trunk_r13078_runs/SSP1-2.6_cluster_scen
./setup_run_tseq.sh
cd $WORK_BASE/SSP1-2.6_cluster_scen
bash startguess.sh
# (repeat for SSP2-4.5_cluster_scen, ..., SSP5-8.5_cluster_scen)
```

The `setup_run_tseq.sh` wrapper auto-detects `$(pwd)` for runname + scenario-dir, hardcodes `--inputmethod imogencfx`, points `--binary` at `forks/trunk_r13078/build_owl/guess`, and invokes the workhorse `scripts/cluster/setup_run.sh` with all the right named-flag args. Override allocation via env: `NNODES=2 CPU_PER_NODE=128 PARTITION=genius WALLTIME=03:00:00 ./setup_run_tseq.sh`.

**GRIDLIST env-override** (added at block 8.3 cluster smoke prep 2026-05-28 per Rule #9 #34 fix; landed in setup_run_tseq_template.sh + cp'd to all 10 cluster `<SSP>_cluster_<phase>/setup_run_tseq.sh`): the production gridlist (`data/gridlist/gridlist_in_62892_and_climate.txt`; 62538 cells) is the default; override at invocation for smoke runs without editing any script:

```bash
# Block 8.3 smoke (1024-cell biome-stratified-anchored; 4 cells/rank for 256-rank MPI; 50 Phase F anchor cells preserved at lines 1-50)
GRIDLIST="$(realpath ../../../data/gridlist/gridlist_b830_cluster_smoke_1024cells_seed42.txt)" \
  NNODES=4 CPU_PER_NODE=64 PARTITION=milan WALLTIME=06:00:00 \
  ./setup_run_tseq.sh

# Production (default; just no GRIDLIST env)
NNODES=2 CPU_PER_NODE=128 PARTITION=genius WALLTIME=3-00:00:00 \
  ./setup_run_tseq.sh
```

The wrapper passes the override path to `setup_run.sh --gridlist <PATH>`, which (a) copies the gridlist to the work-dir, (b) sed-replaces `gridlist.txt` placeholder in all .ins with the override basename per rank for proper MPI gridlist-split-parallelism (cluster main.ins now uses `(str "gridlist.txt")` placeholder per Rule #9 #34 fix; Track-1 wpeat-compatible convention), and (c) splits the gridlist into 256 per-rank chunks at `runNN/<basename>`. **Cell-count discipline**: pick N such that `N % NPROCESS == 0` to ensure all ranks loaded (e.g., 256, 512, 768, 1024 cells for 256-rank); otherwise some ranks have no gridlist file → guess fails → finishup `--dependency=afterok` chain breaks. Verification: `lines_per_run = ceil(N/R); chunks = ceil(N/lines_per_run); idle_ranks = R - chunks; need idle_ranks == 0`. Production gridlist 62538/256 satisfies this with lines_per_run=245 → 256 chunks → 0 idle.

**Path A — Unified `run_coupled.sbatch` launcher** (alternative; uses rebuild's `--scenario` CLI pattern):

```bash
# Note: run_coupled.sbatch was designed around rebuild's runs/<SSP>/ paths; for Track 2 T_seq
# it requires --scenario-dir override to point at our forks/trunk_r13078_runs/<SSP>_cluster_<phase>/.
# This path may require minor adaptation; verify CLI surface before use.

scripts/cluster/run_coupled.sbatch \
  --scenario-dir forks/trunk_r13078_runs/SSP1-2.6_cluster_hist \
  --coupling-mode loose \
  --inputmethod imogencfx \
  --binary forks/trunk_r13078/build_owl/guess \
  --production \
  --nodes 2 --cpu-per-node 128 --partition genius --walltime 03:00:00
```

The Path B per-dir wrapper is the more familiar pattern + matches your established Track-1 workflow precisely. Path A is provided for unified-launcher consistency with rebuild's other operational scripts.

### Pre-cluster checklist (after `git pull` cluster to v0.24.0)

1. **Rebuild trunk binary on cluster**: `cd forks/trunk_r13078 && mkdir -p build_owl && cd build_owl && cmake -DCMAKE_BUILD_TYPE=Release .. && make -j$(nproc)` (per block 8.1 confirmation B48-immune on cluster)
2. **Rsync δ-B-variant 62892 library** workstation→cluster: 5 × 18 GB to `/bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm/forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/` (5-10 min over gigabit). Note: this 90 GB of binary data is gitignored — git won't track it, but it physically lives inside the cluster mirror dir tree. This mirrors the workstation layout exactly.
3. **(Optional, mirrors your Track-1 muscle memory) Create `./guess` symlinks** in each cluster run-dir: `for d in forks/trunk_r13078_runs/SSP*_cluster_*; do (cd $d && ln -s ../../trunk_r13078/build_owl/guess guess); done`. Not required because `setup_run_tseq.sh` passes `--binary` explicitly to `setup_run.sh`, but adding the symlink lets you `./guess --help` from within the run-dir for ad-hoc inspection (matches your Track-1 convention).
4. **Verify cluster LU + ndep + popdens + simfire + soilmap paths exist** (per your wpeat references in main.ins; should be there from your Track-1 runs)
5. **Block 8.3 cluster smoke test**: pick one SSP × hist phase + small smoke gridlist (e.g., gridlist_test2.txt) + verify end-to-end runs cleanly before full production launch
6. **Block 8.5 cluster MPI pre-flight**: verify chosen-pipeline trunk-T_seq scales correctly on genius/256 × 3-day walltime
7. **Track 2 production launches**: 5 SSPs × hist (~1-3 h cluster wall each) → 5 SSPs × scen (~0.5-1 h each); total ~5-15 h cluster wall per session 11 prompt §1B + B81 reconnaissance estimate.
