# `scripts/` — workstation and cluster launchers

Top-level orchestration scripts that build, prepare inputs, and run
the coupled model end-to-end.

## Planned scripts (per `EXECUTION_PLAN.md` Part V)

| Script | Step | Role |
|---|---|---|
| `build_all.sh` | 14 | Builds LPJ-GUESS (`./guess`) and Fortran IMOGEN, sets up the Python Intermediary venv. Honours **Anaconda3 NetCDF preference** (Decision #8) by detecting `$CONDA_PREFIX` and pointing CMake at the conda libnetcdf rather than the native Ubuntu `libnetcdf-dev`. |
| `run_coupled.sh` | 14 | Workstation Linux launcher. Self-contained. Usage: `./run_coupled.sh <SCENARIO> [<GRIDLIST>]`. Honours `coupling_mode = tight` by default; supports `prescribed` and `loose`. Prints the units-integrity startup banner (per §I.D.5). See Appendix A.4 for sketch. |
| `run_coupled.sbatch` | 16 | Cluster SLURM template. Wraps the existing owl-cluster scripts (imported from `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/`) with the coupled-mode invocation. |
| `cluster/setup_run_owl_with_scratch_lpj_work.sh` | 16 | Imported as-is from the owl scripts toolkit. 174-line 12-arg run-setup; splits gridlist across MPI ranks; generates `submit.sh` and `startguess.sh` per-run. |
| `cluster/mpi_run_guess_on_tmp.sh` | 16 | Imported. Per-rank scratch I/O wrapper; rsyncs ins+gridlist to `/scratch/${SLURM_JOBID}/output/runN/`, runs `./guess -parallel -input <module> <ins>`, rsyncs back. |
| `cluster/finishup_lpj_work_owl.sh` | 16 | Imported. Post-run cleanup as a separate sbatch with `afterok:<guess_jobid>` dependency. |
| `cluster/append_runfiles.sh`, `cluster/append_files.sh` | 16 | Imported. Concatenate per-rank outputs into single global outputs after the parallel run. |
| `cluster/make_guess.sh` | 16 | Imported. Cluster-side LPJ-GUESS build helper. |
| `smoke_test.sh` | 14 | 4-cell × 3-year coupled run that completes in <1 minute. Used in CI. |
| `parallel_smoke.sh` | 16 | 4-rank MPI workstation parallel test on `gridlist_test480.txt`; mimics the cluster setup so the owl-script logic can be validated before submitting to the actual cluster. |

## The single-codebase principle (Decision #7)

Per the Decisions Settled table item #7, the **same codebase** runs
on both workstation and cluster. The choice is made at run time by
which launcher is invoked:

- **Workstation:** `./scripts/run_coupled.sh SSP1-2.6` — runs the
  binary in single-process mode (no `-parallel`).
- **Cluster:** `sbatch ./scripts/run_coupled.sbatch SSP1-2.6` —
  runs the binary in MPI mode (`-parallel`) under SLURM.

No separate "cluster build" or "cluster fork". The same `./guess`
binary, the same Python venv, the same ins-files, the same data
paths (or symlinks to cluster-shared storage).

## Coupled-mode adaptations to the owl scripts

The owl scripts toolkit was designed for non-coupled `cfx`-style
runs. The coupled-mode adaptations at step 16 are:

1. Change `INPUTMETHOD=cfx` to `INPUTMETHOD=imogencfx` in the
   `setup_run.sh` wrapper.
2. Ensure `<DIR_COMMON>` (the IMOGEN engine handshake directory)
   is on **shared filesystem** rather than per-rank scratch — so
   the in-process IMOGEN engine handshake (per-rank `done` files)
   works correctly across ranks. Each rank has its own per-rank
   `<DIR_COMMON>/run<N>/...` namespace (via the per-rank `runN/`
   working directory pattern that `setup_run_owl_with_scratch_lpj_work.sh`
   already establishes), so cross-rank race conditions don't arise
   because each rank's IMOGEN engine is independent.
3. Document the cluster `module load` lines (gcc, cmake,
   netcdf-c, netcdf-fortran, openmpi — exact versions to be
   confirmed via terminal back-and-forth at step 16).
