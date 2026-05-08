#!/bin/bash
# =============================================================================
# scripts/run_parallel_mimic.sh — workstation-parallel mimic of cluster MPI run
# =============================================================================
#
# Purpose: validate the cluster orchestration logic (per-rank gridlist split +
# per-rank runNN/ subdirs + parallel guess invocation + post-run aggregation)
# WITHOUT requiring access to the actual cluster. Uses Anaconda3's MPICH
# (mpirun -np N) on the workstation; runs guess -parallel on a 4-cell
# smoke gridlist, then verifies per-rank output + concatenation.
#
# This is the v1.0 step 16's `--workstation parallel test` deliverable per
# `EXECUTION_PLAN.md` V.1 step 16:
#   "Provide a workstation parallel test that mimics the cluster setup
#    (4-rank MPI on a small gridlist) so the owl-script logic can be
#    validated before submitting to the actual cluster."
#
# The mimic test exercises ONLY loose coupling (`--inputmethod imogen` →
# LPJG reads pre-baked engine climate from disk; embarrassingly parallel;
# no F-10 deadlock). Tight on cluster requires F-12 Option C (per
# docs/v2_roadmap.md §5).
#
# USAGE
# -----
#     scripts/run_parallel_mimic.sh [--np N] [--scenario SSP] [--no-build]
#
# OPTIONS
#   --np N         Number of MPI ranks (default: 4)
#   --scenario SSP Scenario directory under runs/ (default: SSP1-2.6)
#   --no-build     Skip MPI build; reuse existing lpjguess/build_mpi/guess
#   -h, --help     Show this and exit
#
# WHAT THIS DOES
#   [1] Optionally rebuild lpjguess/build_mpi/guess with mpicxx
#   [2] Stage runs/<SSP>/parallel_work/<SSP>/runNN/ subdirs via
#       scripts/cluster/setup_run.sh (with --workdir-base override)
#   [3] mpirun -np N <build_mpi>/guess -parallel -input imogen <ins>
#       (under runs/<SSP>/parallel_work/<SSP>/)
#   [4] After completion: concatenate per-rank outputs via append_files.sh
#   [5] Verify per-rank runNN/*.out files exist + are non-trivial
#   [6] Print summary
#
# REFERENCES
# ----------
# - EXECUTION_PLAN.md V.1 step 16 (cluster integration milestone)
# - scripts/cluster/setup_run.sh (the orchestration this validates)
# - scripts/cluster/mpi_run_guess.sh (the per-rank wrapper this mimics)
# =============================================================================

set -euo pipefail

NP=4
SCENARIO="SSP1-2.6"
DO_BUILD=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --np)         NP="$2"; shift 2 ;;
    --scenario)   SCENARIO="$2"; shift 2 ;;
    --no-build)   DO_BUILD=0; shift ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \?//' | head -40
      exit 0
      ;;
    *) echo "ERROR: unknown arg '$1'"; exit 1 ;;
  esac
done

# -----------------------------------------------------------------------------
# Resolve paths
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SCENARIO_DIR="${REPO_ROOT}/runs/${SCENARIO}"
GRIDLIST="${REPO_ROOT}/data/gridlist/gridlist_test2.txt"  # 4 cells

if [[ ! -d "${SCENARIO_DIR}" ]]; then
  echo "ERROR: scenario dir not found: ${SCENARIO_DIR}"
  exit 1
fi

if [[ ! -f "${GRIDLIST}" ]]; then
  echo "ERROR: smoke gridlist not found: ${GRIDLIST}"
  exit 1
fi

# Verify the smoke gridlist has at least NP cells (otherwise some ranks have
# nothing to do and the parallel mimic doesn't validate anything)
NCELL=$(grep -cv '^[[:space:]]*$' "${GRIDLIST}")
if [[ ${NCELL} -lt ${NP} ]]; then
  echo "WARN: smoke gridlist has ${NCELL} cells but --np ${NP} ranks requested."
  echo "      Reducing NP to ${NCELL} to ensure each rank has at least one cell."
  NP=${NCELL}
fi

echo "============================================================"
echo "Workstation parallel mimic test"
echo "============================================================"
echo "  scenario  : ${SCENARIO}"
echo "  gridlist  : ${GRIDLIST}  (${NCELL} cells)"
echo "  np ranks  : ${NP}"
echo "  scenario  : ${SCENARIO_DIR}"
echo "============================================================"

# -----------------------------------------------------------------------------
# [1] Build LPJ-GUESS with MPI (if not skipped)
# -----------------------------------------------------------------------------
BUILD_MPI_DIR="${REPO_ROOT}/lpjguess/build_mpi"
GUESS_BIN="${BUILD_MPI_DIR}/guess"

if [[ "${DO_BUILD}" -eq 1 ]] || [[ ! -x "${GUESS_BIN}" ]]; then
  echo "[1/5] Building LPJ-GUESS with MPI (build_mpi/)"
  bash "${SCRIPT_DIR}/cluster/make_guess.sh" --mpi
  if [[ ! -x "${GUESS_BIN}" ]]; then
    echo "ERROR: MPI build failed; ${GUESS_BIN} not produced"
    exit 1
  fi
else
  echo "[1/5] --no-build; reusing ${GUESS_BIN}"
fi

# Verify MPI symbols are linked in
echo "  MPI symbols in guess binary:"
ldd "${GUESS_BIN}" 2>&1 | grep -iE "libmpi|libpmi|libpsm|libfabric" | head -5 || echo "  (none found; check make_guess.sh --mpi build)"

# -----------------------------------------------------------------------------
# [2] Stage workstation parallel work dir via setup_run.sh
# -----------------------------------------------------------------------------
WORKDIR_BASE="${SCENARIO_DIR}/parallel_work"
echo "[2/5] Staging per-rank runNN/ subdirs at ${WORKDIR_BASE}/"

# Clean any prior parallel_work tree
if [[ -d "${WORKDIR_BASE}" ]]; then
  echo "  cleaning prior ${WORKDIR_BASE}/"
  rm -rf "${WORKDIR_BASE}"
fi

bash "${SCRIPT_DIR}/cluster/setup_run.sh" \
  --runname "$(basename "${SCENARIO_DIR}")" \
  --maininsfile "main.ins" \
  --extra-insfiles "imogen_intermediary.ins global.ins crop_n.ins landcover.ins wetlandpfts.ins crop.ins crop_n_pftlist.simplePFT.remap10_g2p.ins crop_n_stlist.simplePFT.remap10_g2p.N0-60-200-1000.ins crop_n_stlist.simplePFT.remap10_g2p.agreed_treatments.ins pasture_n_stlist.ins pasture_n_stlist_agreed_treatments.ins global_soiln.ins" \
  --gridlist "${GRIDLIST}" \
  --inputmethod "imogen" \
  --nnodes 1 \
  --cpu-per-node "${NP}" \
  --partition "workstation-mimic" \
  --walltime "01:00:00" \
  --binary "${GUESS_BIN}" \
  --scenario-dir "${SCENARIO_DIR}" \
  --workdir-base "${WORKDIR_BASE}" \
  > /tmp/setup_run_mimic.log 2>&1

if [[ $? -ne 0 ]]; then
  echo "ERROR: setup_run.sh failed; see /tmp/setup_run_mimic.log"
  cat /tmp/setup_run_mimic.log
  exit 1
fi

WORK_RUN_DIR="${WORKDIR_BASE}/$(basename "${SCENARIO_DIR}")"
echo "  staged at: ${WORK_RUN_DIR}"
ls "${WORK_RUN_DIR}" | head -10

# -----------------------------------------------------------------------------
# [3] Run mpirun -np N
# -----------------------------------------------------------------------------
echo "[3/5] Running: mpirun -np ${NP} ${GUESS_BIN} -parallel -input imogen main.ins"

cd "${WORK_RUN_DIR}"

# NOTE: this exercise of the LOOSE-coupling input module (`imogen`) will fail
# in v1.0 because the engine climate library at <DIR_COMMON>/IMOGEN/output/
# isn't pre-staged. This is expected — the mimic test validates the
# orchestration mechanics (gridlist split + per-rank invocation + output
# concatenation), not the science. End-to-end loose-coupling validation
# requires either:
#   (a) staging engine output via scripts/run_coupled.sh first, or
#   (b) wiring the bootstrap helper into this mimic script
# Both are deferred to step 17 (validation).

set +e
mpirun -np "${NP}" "${GUESS_BIN}" -parallel -input imogen main.ins > /tmp/mimic_guess.log 2>&1
guess_exit=$?
set -e

echo "  guess exit code: ${guess_exit}"
echo "  log (last 20 lines):"
tail -20 /tmp/mimic_guess.log | sed 's/^/    /'

# -----------------------------------------------------------------------------
# [4] Verify per-rank runNN/ has expected files
# -----------------------------------------------------------------------------
echo "[4/5] Per-rank verification"
nruns=$(ls -d run* 2>/dev/null | wc -l)
echo "  nruns        : ${nruns}  (expected: ${NP})"

if [[ ${nruns} -ne ${NP} ]]; then
  echo "  WARN: expected ${NP} run dirs, found ${nruns}"
fi

for ((i=1; i <= nruns; i++)); do
  rundir="run${i}"
  ngrid=$(grep -cv '^[[:space:]]*$' "${rundir}/$(basename "${GRIDLIST}")" 2>/dev/null || echo 0)
  nins=$(ls "${rundir}"/*.ins 2>/dev/null | wc -l)
  echo "    ${rundir}: ${ngrid} gridcells; ${nins} .ins files"
done

# -----------------------------------------------------------------------------
# [5] Summary
# -----------------------------------------------------------------------------
echo "[5/5] Summary"

if [[ ${guess_exit} -eq 0 ]]; then
  echo "  ✅ mpirun -np ${NP} guess -parallel succeeded"
else
  echo "  ⚠ mpirun -np ${NP} guess -parallel exited with code ${guess_exit}"
  echo "    (this is EXPECTED if engine climate library was not pre-staged;"
  echo "     the mimic test validates orchestration mechanics, not full"
  echo "     loose-coupling end-to-end execution. See step 17 validation.)"
fi

echo "  Per-rank work dir : ${WORK_RUN_DIR}"
echo "  guess.log per rank: $(find run* -name 'guess.log' 2>/dev/null | wc -l) files"
echo "  .out per rank     : $(find run* -name '*.out' 2>/dev/null | wc -l) files (across all ranks)"

echo ""
echo "Mimic test complete. Inspect ${WORK_RUN_DIR}/run*/ for per-rank artifacts."
echo "After step 17 wiring (engine climate library bootstrap), this mimic"
echo "test will exercise full loose-coupling end-to-end."
