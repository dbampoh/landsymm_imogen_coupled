#!/bin/bash
# =============================================================================
# scripts/cluster/mpi_run_guess.sh — per-rank scratch-I/O wrapper
# =============================================================================
#
# Adapted from: /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/
#               owl_hpc_cluster_scripts/scripts/mpi_run_guess_on_tmp.sh
# (the IMK-IFU per-rank scratch wrapper; verified working on the owl
# partition).
#
# Adaptations from the IMK-IFU original:
#   1. Multi-MPI-implementation rank detection (MPICH PMI_RANK || OpenMPI
#      OMPI_COMM_WORLD_RANK || SLURM_PROCID) — original supported only the
#      first two. We need PMI_RANK because Anaconda3's MPICH 4.1.1 sets that.
#   2. $TMP fallback to $TMPDIR or /tmp/$SLURM_JOBID for non-cluster contexts
#      (workstation parallel mimic test) when /scratch isn't available
#   3. F-10/F-12 caveat-aware: warn at runtime if `-input imogencfx` requested
#      (cluster + tight is gated on F-12 Option C per docs/v2_roadmap.md §5)
#
# What this script does (per rank):
#   1. Resolve world rank from MPI environment vars (MPICH || OpenMPI || SLURM)
#   2. Compute LOCAL_NRUN = rank+1 (LPJ-GUESS convention)
#   3. rsync the per-rank runNN/ subdir to fast scratch storage
#   4. Run guess -parallel -input <module> <ins>
#   5. rsync the per-rank outputs back to the shared work dir
#
# USAGE
# -----
# Invoked by SLURM srun (typically); not meant to be called directly:
#     srun mpi_run_guess.sh <abs-path-to-guess> -parallel -input <module> <ins>
#
# REFERENCES
# ----------
# - IMK-IFU original: /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/
#                     owl_hpc_cluster_scripts/scripts/mpi_run_guess_on_tmp.sh
# - lpjguess/framework/parallel.cpp (LPJ-GUESS's MPI rank/size queries; no
#                                     MPI_Barrier — see notes/FOLLOWUPS.md F-10
#                                     for the architectural implication)
# =============================================================================

# Don't `set -e` — the rsync flow uses partial failures gracefully

if [[ $# -eq 0 ]]; then
  echo "usage: $(basename "$0") <abs-path-to-guess> -parallel -input <module> <ins-file>"
  exit 1
fi

GUESS=$1
shift
OPTIONS=$*

if [[ ! -e "${GUESS}" ]]; then
  echo "ERROR: guess binary not found at ${GUESS}"
  exit 1
fi

# -----------------------------------------------------------------------------
# Resolve world rank (MPICH || OpenMPI || SLURM)
# -----------------------------------------------------------------------------
NRANK=""
if [[ -n "${OMPI_COMM_WORLD_RANK:-}" ]]; then
  NRANK="${OMPI_COMM_WORLD_RANK}"  # OpenMPI
elif [[ -n "${PMI_RANK:-}" ]]; then
  NRANK="${PMI_RANK}"              # MPICH (incl. Anaconda3 MPICH 4.1.1)
elif [[ -n "${SLURM_PROCID:-}" ]]; then
  NRANK="${SLURM_PROCID}"          # SLURM srun without MPI library
else
  echo "ERROR: cannot determine MPI rank. None of these env vars are set:"
  echo "  OMPI_COMM_WORLD_RANK (OpenMPI), PMI_RANK (MPICH), SLURM_PROCID (SLURM)"
  exit 1
fi

# LPJ-GUESS uses 1-based rank ↦ runNN/ directory mapping
LOCAL_NRUN=$((NRANK + 1))

# -----------------------------------------------------------------------------
# Resolve per-rank scratch dir
# -----------------------------------------------------------------------------
if [[ -z "${TMP:-}" ]]; then
  if [[ -n "${SLURM_JOBID:-}" ]]; then
    TMP="/scratch/${SLURM_JOBID}"
  elif [[ -n "${TMPDIR:-}" ]]; then
    TMP="${TMPDIR}/lpjg-mpi-$$"
  else
    TMP="/tmp/lpjg-mpi-$$"
  fi
fi

SCRATCH_WORK_DIR="${TMP}/output"
SCRATCH_RUN_DIR="${SCRATCH_WORK_DIR}/run${LOCAL_NRUN}"

# Resolve work dir from SLURM submit dir (or PWD as fallback)
WORK_DIR="${SLURM_SUBMIT_DIR:-${PWD}}"
WORK_RUN_DIR="${WORK_DIR}/run${LOCAL_NRUN}"

echo "===== mpi_run_guess.sh rank ${NRANK} (run${LOCAL_NRUN}) ====="
echo "  hostname        : ${HOSTNAME}"
echo "  GUESS binary    : ${GUESS}"
echo "  GUESS options   : ${OPTIONS}"
echo "  WORK_DIR        : ${WORK_DIR}"
echo "  WORK_RUN_DIR    : ${WORK_RUN_DIR}"
echo "  SCRATCH_RUN_DIR : ${SCRATCH_RUN_DIR}"

# -----------------------------------------------------------------------------
# F-10/F-12 caveat detection
# -----------------------------------------------------------------------------
if [[ "${OPTIONS}" =~ -input[[:space:]]+imogencfx ]]; then
  echo
  echo "WARNING: -input imogencfx detected in cluster MPI context."
  echo "  v1.0 cluster + tight is BLOCKED (F-10 + lack of MPI_Barrier in"
  echo "  framework loop; per-rank handshake gap; see docs/v2_roadmap.md §5"
  echo "  for F-12 Option C resolution). This rank may complete its gridlist"
  echo "  subset in engine-only output then deadlock; recommended action is"
  echo "  to terminate the SLURM job once 32 engine year-output dirs exist"
  echo "  per rank (matching the single-process F-10 pattern)."
  echo
fi

# -----------------------------------------------------------------------------
# Set up scratch
# -----------------------------------------------------------------------------
mkdir -p "${SCRATCH_RUN_DIR}"

if [[ ! -d "${SCRATCH_RUN_DIR}" ]]; then
  echo "ERROR: could not create SCRATCH_RUN_DIR ${SCRATCH_RUN_DIR}"
  exit 1
fi

# Clean any stale outputs from a previous run
nout=$(find "${SCRATCH_RUN_DIR}" -name '*.out' 2>/dev/null | wc -l)
if [[ ${nout} -gt 0 ]]; then
  echo "  cleaning ${nout} stale .out files in ${SCRATCH_RUN_DIR}"
  rm -f "${SCRATCH_RUN_DIR}"/*.{out,ins,txt,log,dat} 2>/dev/null || true
  rm -f "${SCRATCH_RUN_DIR}"/core.* 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# rsync work runfiles → scratch (twice for reliability per IMK-IFU pattern)
# -----------------------------------------------------------------------------
rsync -az --partial "${WORK_RUN_DIR}/" "${SCRATCH_RUN_DIR}/"
rsync -az --partial "${WORK_RUN_DIR}/" "${SCRATCH_RUN_DIR}/"

# -----------------------------------------------------------------------------
# Run guess
# -----------------------------------------------------------------------------
cd "${SCRATCH_WORK_DIR}"  # only cd to scratch_work_dir; guess -parallel cd's into runNN
echo "  cmd: ${GUESS} ${OPTIONS}"
"${GUESS}" ${OPTIONS}
guess_exit=$?
wait

echo "  guess exit code : ${guess_exit}"

# -----------------------------------------------------------------------------
# rsync scratch → work (twice for reliability)
# -----------------------------------------------------------------------------
rsync -az --partial "${SCRATCH_RUN_DIR}/" "${WORK_RUN_DIR}/"
rsync -az --partial "${SCRATCH_RUN_DIR}/" "${WORK_RUN_DIR}/"

# -----------------------------------------------------------------------------
# Cleanup scratch
# -----------------------------------------------------------------------------
if [[ "${SCRATCH_RUN_DIR}" =~ /scratch ]] || [[ "${SCRATCH_RUN_DIR}" =~ /tmp/ ]]; then
  rm -f "${SCRATCH_RUN_DIR}"/* 2>/dev/null || true
  rmdir --ignore-fail-on-non-empty "${SCRATCH_RUN_DIR}" 2>/dev/null || true
fi

exit "${guess_exit}"
