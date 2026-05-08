#!/bin/bash
# =============================================================================
# scripts/cluster/finishup_lpj_work.sh — post-run aggregation + cleanup
# =============================================================================
#
#SBATCH --output=append_guess_x.o%j
#SBATCH --error=append_guess_x.e%j
#SBATCH --time=2-00:00:00
#SBATCH --job-name=append_guess
#
# Adapted from: /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/
#               owl_hpc_cluster_scripts/scripts/finishup_lpj_work_owl.sh
# (the IMK-IFU 172-line post-processor; verified working on the owl partition).
#
# Adaptations from the IMK-IFU original:
#   1. Removed cluster-arch-specific prefix matching (was `finishup_lpj_work_owl.sh`
#      and `finishup_lpj_work_keal.sh`; now generic)
#   2. Cross-references to F-10/F-12 caveats inline (so future operators see
#      the architectural context)
#   3. Generic destpath naming (output-YYYY-MM-DD; not arch-prefixed)
#
# What this script does:
#   1. Concatenate per-rank `runNN/*.out` files into the work dir
#      via append_files.sh (xargs -P parallelism)
#   2. Concatenate per-rank `runNN/guess.log` into `guess_runs.log`
#   3. Run scenario-local `postproc.sh` if present
#   4. md5sum + gzip the outputs
#   5. Copy results to `<output_dir>/output-YYYY-MM-DD/`
#
# USAGE
# -----
#     sbatch finishup_lpj_work.sh <work_basedir> <output_basedir>
#   OR (called via setup_run.sh's startguess.sh dependency chain):
#     sbatch -p <append_partition> --ntasks=N --time=1-00:00:00 \
#       --dependency=afterok:<JOBID> finishup_lpj_work.sh <work_dir> <output_dir>
#
# REFERENCES
# ----------
# - IMK-IFU original: /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/
#                     owl_hpc_cluster_scripts/scripts/finishup_lpj_work_owl.sh
# - scripts/cluster/setup_run.sh (the staging-side counterpart)
# - scripts/cluster/append_files.sh (the per-file aggregator helper)
# =============================================================================

if [[ "$#" -ne 2 ]]; then
  echo "usage: $(basename "$0") <work_basedir> <output_basedir>"
  exit 1
fi

WORK_DIR=$1
OUTPUT_DIR=$2

if [[ ! -d "${WORK_DIR}" ]]; then
  echo "ERROR: work dir does not exist: ${WORK_DIR}"
  exit 1
fi

cd "${WORK_DIR}"

nruns=$(ls -d run* 2>/dev/null | wc -l)
echo "WORK_DIR    : ${PWD}"
echo "OUTPUT_DIR  : ${OUTPUT_DIR}"
echo "nruns       : ${nruns}"
echo "SLURM job   : ${SLURM_JOBID:-<unset; manual invocation>}"

NPROC="${SLURM_NTASKS:-4}"

# Resolve append_files.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPEND_FILES="${SCRIPT_DIR}/append_files.sh"
if [[ ! -x "${APPEND_FILES}" ]]; then
  echo "ERROR: append_files.sh not found or not executable at ${APPEND_FILES}"
  exit 1
fi

nouts=$(find run1 -name '*.out' 2>/dev/null | wc -l)
if [[ ${nouts} -eq 0 ]]; then
  echo "ERROR: no outputs found in ${PWD}/run1; terminating!"
  exit 1
fi

# -----------------------------------------------------------------------------
# Concatenate per-rank .out files via append_files.sh (parallel via xargs)
# -----------------------------------------------------------------------------
find run1 -name '*.out' | sed 's,run1/,,g' \
  | xargs -n "${NPROC}" -P "${NPROC}" "${APPEND_FILES}" "${nruns}"

# -----------------------------------------------------------------------------
# Concatenate per-rank guess.log files
# -----------------------------------------------------------------------------
[[ -e "guess_runs.log" ]] && rm guess_runs.log
[[ -e "state_runs.log" ]] && rm state_runs.log

for ((idx=1; idx <= nruns; idx++)); do
  echo "------ run${idx}/guess.log ------" >> guess_runs.log
  cat "run${idx}/guess.log" >> guess_runs.log
  if [[ -e "run${idx}/state.log" ]]; then
    cat "run${idx}/state.log" >> state_runs.log
  fi
done

ls -l ./*.out ./*.log ./*.txt ./*.ins 2>/dev/null

# -----------------------------------------------------------------------------
# Sanity checks (skipping / warnings / errors detection)
# -----------------------------------------------------------------------------
grep -B 1 -A 2 -H -i 'skip'    guess_runs.log > skipping.txt 2>/dev/null || true
grep -B 3 -A 2 -H -i 'warning' guess_runs.log > warnings.txt 2>/dev/null || true
grep -B 3 -A 2 -H -i 'error'   guess_runs.log > errors.txt   2>/dev/null || true

skipped=$(grep -i 'skip'    guess_runs.log 2>/dev/null | wc -l)
warned=$(grep  -i 'warning' guess_runs.log 2>/dev/null | wc -l)
errors=$(grep  -i 'error'   guess_runs.log 2>/dev/null | wc -l)
echo "Skipped   : ${skipped}"
echo "Warnings  : ${warned}"
echo "Errors    : ${errors}"

# -----------------------------------------------------------------------------
# Optional postproc
# -----------------------------------------------------------------------------
if [[ -e "postproc.sh" ]] || [[ -e "../postproc.sh" ]] || [[ -e "../../postproc.sh" ]]; then
  echo "Running postproc..."
  [[ -e "../../postproc.sh" ]] && cp ../../postproc.sh .
  [[ -e "../postproc.sh"    ]] && cp ../postproc.sh .
  bash postproc.sh
fi

# -----------------------------------------------------------------------------
# md5sum + gzip
# -----------------------------------------------------------------------------
echo "Compressing outputs..."
find . -name '*.out' ! -name 'Job*' | grep -v './run' | xargs -n "${NPROC}" -P "${NPROC}" md5sum > md5_out.txt 2>/dev/null
find . -name '*.out' ! -name 'Job*' | grep -v './run' | xargs -n "${NPROC}" -P "${NPROC}" gzip -f
gzip -f guess_runs.log &
wait
find . -name '*.gz' | xargs -n "${NPROC}" -P "${NPROC}" md5sum > md5_gz.txt 2>/dev/null

# -----------------------------------------------------------------------------
# Copy to output destination
# -----------------------------------------------------------------------------
destpath="${OUTPUT_DIR}/output-$(date +%F)"
echo "Copying to: ${destpath}"

if [[ -e "${destpath}" ]]; then
  echo "  previous ${destpath} → ${destpath}_BACKUP"
  mv "${destpath}" "${destpath}_BACKUP"
fi

mkdir -p "${destpath}"

if [[ -e "${destpath}" ]]; then
  ngz=$(find . -name '*.gz' 2>/dev/null | wc -l)
  if [[ ${ngz} -gt 0 ]]; then
    find . -name '*.gz' | grep -v './run' | xargs -I xx mv -v xx "${destpath}/" 2>/dev/null
  else
    find . -name '*.out' | grep -v './run' | xargs -I xx cp -v xx "${destpath}/"
  fi
  cp -v ./*.ins "${destpath}/" 2>/dev/null || true
  cp -v ./*.txt "${destpath}/" 2>/dev/null || true
  cp -v ./*.log "${destpath}/" 2>/dev/null || true
  cp -v ./guess "${destpath}/" 2>/dev/null || true

  echo "Verifying gz md5..."
  pushd "${destpath}" > /dev/null
  md5sum -c md5_gz.txt 2>/dev/null || true
  popd > /dev/null

  infostr="$(date) ${destpath} job ${SLURM_JOBID:-<manual>} appended Skipped ${skipped} Warnings ${warned} Errors ${errors}"
  echo "${infostr}"
  echo "${infostr}" >> ~/lpj-model-runs.txt
else
  echo "ERROR: failed to create destpath ${destpath}"
  exit 1
fi
