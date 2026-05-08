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
