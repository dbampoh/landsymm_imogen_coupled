#!/bin/bash
# =============================================================================
# scripts/cluster/setup_run.sh — gridlist-split + per-rank runNN/ generation
# =============================================================================
#
# Adapted from: /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/
#               owl_hpc_cluster_scripts/scripts/setup_run_owl_with_scratch_lpj_work.sh
# (the IMK-IFU 174-line orchestrator at the user's existing cluster toolkit;
# verified working on the owl partition).
#
# Adaptations from the IMK-IFU original:
#   1. Named-flag CLI (vs positional 12-arg) for clarity + future-proofing
#   2. Configurable INPUT_MODULE (the IMK-IFU original was hardcoded `cfx`;
#      we default to `imogen` for v1.0 cluster + loose coupling)
#   3. Cluster path-translation logic preserved but configurable via env vars
#      ($WORK_BASE override) for portability across non-owl clusters
#   4. Cross-references to F-10/F-12 caveats inline in generated submit.sh
#      (so future operators see the architectural context at runtime)
#   5. Adapt for our `lpjguess/build_mpi/guess` binary location (vs the
#      IMK-IFU compiled/<archvariant>/guess symlink pattern)
#
# What this script does:
#   1. Reads the scenario's main + extra ins-files; copies them to a
#      cluster-shared work directory ($WORK_DIR/$RUN_DIR/)
#   2. Splits the gridlist into N approximately-equal chunks via
#      `split -a 4 -l <cells/N>` and distributes them to per-rank
#      `runNN/` subdirectories
#   3. Generates submit.sh (SLURM batch script invoked by the user)
#   4. Generates startguess.sh (the submit-and-chain-finishup wrapper)
#
# USAGE (named flags)
# -------------------
#     scripts/cluster/setup_run.sh --runname <NAME> \
#       --maininsfile <FILE> --extra-insfiles "<FILES>" --gridlist <PATH> \
#       --inputmethod <MODULE> --nnodes <N> --cpu-per-node <N> \
#       --partition <PARTITION> --walltime <HH:MM:SS> --binary <PATH> \
#       --scenario-dir <PATH> [--append-partition <NAME>] [--append-ntasks <N>] \
#       [--workdir-base <PATH>]
#
# REFERENCES
# ----------
# - IMK-IFU original: /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/
#                     owl_hpc_cluster_scripts/scripts/setup_run_owl_with_scratch_lpj_work.sh
# - lpjguess/parallel_version/aurora.tmpl (the canonical upstream LPJ-GUESS
#                                           parallel template for cross-reference)
# - F-10 (notes/FOLLOWUPS.md): per-rank gridlist subsetting works fine for
#                               loose; tight requires F-12 Option C
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Parse args
# -----------------------------------------------------------------------------
RUNNAME=""
INSFILE=""
EXTRA_INSFILES=""
GRIDLIST=""
INPUTMETHOD="imogen"      # v1.0 default = loose coupling (the only mode that
                          # works end-to-end on cluster per F-10/F-12 sequencing)
NNODES=2
CPU_PER_NODE=16
PARTITION=""
APPEND_PARTITION=""
APPEND_NTASKS=8
WALLTIME="03:00:00"
BINARY=""
SCENARIO_DIR=""
WORKDIR_BASE="${WORKDIR_BASE:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --runname)          RUNNAME="$2"; shift 2 ;;
    --maininsfile)      INSFILE="$2"; shift 2 ;;
    --extra-insfiles)   EXTRA_INSFILES="$2"; shift 2 ;;
    --gridlist)         GRIDLIST="$2"; shift 2 ;;
    --inputmethod)      INPUTMETHOD="$2"; shift 2 ;;
    --nnodes)           NNODES="$2"; shift 2 ;;
    --cpu-per-node)     CPU_PER_NODE="$2"; shift 2 ;;
    --partition)        PARTITION="$2"; shift 2 ;;
    --append-partition) APPEND_PARTITION="$2"; shift 2 ;;
    --append-ntasks)    APPEND_NTASKS="$2"; shift 2 ;;
    --walltime)         WALLTIME="$2"; shift 2 ;;
    --binary)           BINARY="$2"; shift 2 ;;
    --scenario-dir)     SCENARIO_DIR="$2"; shift 2 ;;
    --workdir-base)     WORKDIR_BASE="$2"; shift 2 ;;
    *) echo "ERROR: unknown arg '$1'"; exit 1 ;;
  esac
done

# -----------------------------------------------------------------------------
# Validate
# -----------------------------------------------------------------------------
[[ -z "${RUNNAME}" ]]          && { echo "ERROR: --runname required"; exit 1; }
[[ -z "${INSFILE}" ]]          && { echo "ERROR: --maininsfile required"; exit 1; }
[[ -z "${GRIDLIST}" ]]         && { echo "ERROR: --gridlist required"; exit 1; }
[[ -z "${PARTITION}" ]]        && { echo "ERROR: --partition required"; exit 1; }
[[ -z "${BINARY}" ]]           && { echo "ERROR: --binary required"; exit 1; }
[[ -z "${SCENARIO_DIR}" ]]     && { echo "ERROR: --scenario-dir required"; exit 1; }
[[ ! -f "${BINARY}" ]]         && { echo "ERROR: binary not found: ${BINARY}"; exit 1; }
[[ ! -f "${GRIDLIST}" ]]       && { echo "ERROR: gridlist not found: ${GRIDLIST}"; exit 1; }
[[ ! -d "${SCENARIO_DIR}" ]]   && { echo "ERROR: scenario dir not found: ${SCENARIO_DIR}"; exit 1; }
[[ -z "${APPEND_PARTITION}" ]] && APPEND_PARTITION="${PARTITION}"

# -----------------------------------------------------------------------------
# Cluster-path translation logic (per IMK-IFU owl pattern; configurable via
# WORKDIR_BASE env var). For non-owl clusters or workstation parallel mimic,
# pass --workdir-base explicitly.
# -----------------------------------------------------------------------------
LOCAL_DIR="${SCENARIO_DIR}"

if [[ -n "${WORKDIR_BASE}" ]]; then
  WORK_BASE="${WORKDIR_BASE}/$(basename "${LOCAL_DIR}")"
elif [[ "${LOCAL_DIR}" =~ /pd/home ]]; then
  WORK_BASE="${LOCAL_DIR/pd\/home/pd\/data\/lpj\/work}"
elif [[ "${LOCAL_DIR}" =~ /pd/data/lpj ]]; then
  WORK_BASE="${LOCAL_DIR/pd\/data\/lpj/pd\/data\/lpj\/work}"
elif [[ "${LOCAL_DIR}" =~ /bg/data/lpj ]]; then
  WORK_BASE="${LOCAL_DIR/bg\/data\/lpj/bg\/data\/lpj\/work}"
else
  # Workstation default: write into the scenario dir's `parallel_work/` subdir
  WORK_BASE="${LOCAL_DIR}/parallel_work"
fi

WORK_DIR="$(dirname "${WORK_BASE}")"
RUN_DIR="${RUNNAME}"
NPROCESS=$((NNODES * CPU_PER_NODE))

echo "user        : $(whoami)"
echo "local_dir   : ${LOCAL_DIR}"
echo "work_dir    : ${WORK_DIR}"
echo "run_dir     : ${RUN_DIR}"
echo "nprocess    : ${NPROCESS}"
echo "input_module: ${INPUTMETHOD}"
echo "binary      : ${BINARY}"
echo "gridlist    : ${GRIDLIST}"
echo "partition   : ${PARTITION}"
echo "walltime    : ${WALLTIME}"

# -----------------------------------------------------------------------------
# F-10/F-12 caveat
# -----------------------------------------------------------------------------
if [[ "${INPUTMETHOD}" == "imogencfx" ]]; then
  cat >&2 <<'WARN'

WARNING: --inputmethod imogencfx requested.

  This is the TIGHT-coupling input module. v1.0 cluster + tight is BLOCKED:
  the framework loop (framework.cpp:411-516) is per-gridcell-outer / per-day
  -inner-across-all-years, with no MPI_Barrier at year boundaries. Each rank
  processes its gridlist subset independently. Step 8's ImogenOutput::flush_year
  fires per-rank-per-year; engine cannot consume N independent flux streams.
  Resolution: F-12 Option C (additive framework_loop_mode = "year_outer" with
  MPI_Barrier at year boundary; per docs/v2_roadmap.md §5).

  Continuing anyway (the user knows what they're doing or is testing the
  v1.0 caveat empirically). If you wanted loose mode, re-run with
  --inputmethod imogen.

WARN
fi

# -----------------------------------------------------------------------------
# Stage work dir
# -----------------------------------------------------------------------------
mkdir -p "${WORK_DIR}/${RUN_DIR}/"

# Copy binary + gridlist + ins files
cp "${BINARY}" "${WORK_DIR}/${RUN_DIR}/"
cp "${GRIDLIST}" "${WORK_DIR}/${RUN_DIR}/"

GRIDLIST_FILENAME="$(basename "${GRIDLIST}")"

# Process all .ins files (substitute gridlist placeholder)
for ins in ${INSFILE} ${EXTRA_INSFILES}; do
  ins_path="${LOCAL_DIR}/${ins}"
  if [[ ! -f "${ins_path}" ]]; then
    echo "WARN: ins file not found: ${ins_path}; skipping"
    continue
  fi
  sed -e "s,gridlist.txt,${GRIDLIST_FILENAME},g" \
      -e "s,\$GRIDLIST,${GRIDLIST_FILENAME},g" \
      "${ins_path}" > "${WORK_DIR}/${RUN_DIR}/${ins}"
done

# -----------------------------------------------------------------------------
# Create per-rank runNN/ subdirs
# -----------------------------------------------------------------------------
cd "${WORK_DIR}/${RUN_DIR}"
for ((b=1; b <= NPROCESS; b++)); do
  mkdir -p "run$b"
  cp ./*.ins "run$b/"
  rm -f "run$b/guess.log"
  rm -f "run$b/${GRIDLIST_FILENAME}"
done

# -----------------------------------------------------------------------------
# Split gridlist across ranks
# -----------------------------------------------------------------------------
lines_per_run=$(wc -l "${GRIDLIST_FILENAME}" | awk '{ x = $1/'"${NPROCESS}"'; d = (x == int(x)) ? x : int(x)+1; print d}')
split -a 4 -l "${lines_per_run}" "${GRIDLIST_FILENAME}" tmpSPLITGRID_

i=1
for file in tmpSPLITGRID_*; do
  mv "${file}" "run${i}/${GRIDLIST_FILENAME}"
  i=$((i+1))
done

# -----------------------------------------------------------------------------
# Generate submit.sh (SLURM batch script)
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat > submit.sh <<EOL
#!/bin/bash
#SBATCH --partition=${PARTITION}
#SBATCH --nodes=${NNODES}
#SBATCH --ntasks=${NPROCESS}
#SBATCH --output=guess_x.o%j
#SBATCH --error=guess_x.e%j
#SBATCH --time=${WALLTIME}
#SBATCH --job-name=${RUNNAME:0:12}_guess

# F-10/F-12 caveats applied: --inputmethod is "${INPUTMETHOD}".
# v1.0 cluster + loose works end-to-end; cluster + prescribed/tight gates on
# F-12 Option C (per docs/v2_roadmap.md §5).

cd ${WORK_DIR}/${RUN_DIR}
echo \$(date) \$(hostname) \$PWD job \$SLURM_JOBID ntasks \$SLURM_NTASKS started >> ~/lpj-model-runs.txt
srun ${SCRIPT_DIR}/mpi_run_guess.sh ${WORK_DIR}/${RUN_DIR}/$(basename "${BINARY}") -parallel -input ${INPUTMETHOD} ${INSFILE}
EOL
chmod +x submit.sh

# -----------------------------------------------------------------------------
# Generate startguess.sh (job submitter + dependency-chained finishup)
# -----------------------------------------------------------------------------
cat > startguess.sh <<EOL
#!/bin/bash
SLURM_JOBID=\$(sbatch submit.sh)
JOB_GUESS_ID=\$(echo \${SLURM_JOBID} | sed 's,Submitted batch job ,,g')
cp -v submit.sh \$(basename \$PWD)-submitted_\$(date +%F_%H-%M-%S).sh

sbatch -p ${APPEND_PARTITION} --ntasks=${APPEND_NTASKS} --time=1-00:00:00 \\
  --dependency=afterok:\${JOB_GUESS_ID} \\
  ${SCRIPT_DIR}/finishup_lpj_work.sh ${WORK_DIR}/${RUN_DIR} ${LOCAL_DIR}
EOL
chmod +x startguess.sh

echo
echo "Setup complete:"
echo "  Work dir : ${WORK_DIR}/${RUN_DIR}/"
echo "  $(ls "${WORK_DIR}/${RUN_DIR}" | wc -l) entries (run1..run${NPROCESS} + .ins files + binary + gridlist + submit.sh + startguess.sh)"
echo
echo "To submit the job:"
echo "  cd ${WORK_DIR}/${RUN_DIR}"
echo "  bash startguess.sh"
