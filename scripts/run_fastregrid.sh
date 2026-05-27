#!/usr/bin/env bash
# ============================================================================
# scripts/run_fastregrid.sh — δ-B + δ-B-variant FastRegrid wrapper
#
# Authored at block 8.2.5 (2026-05-26 session 11 day 2) per the wiring plan at
# _chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_wiring_plan.md.
#
# Handles both pipelines via the chained-FastRegrid pattern:
#
#   δ-B (Fortran engine pipeline):
#     - INPUT: runs/<SSP>/Common-directory-fortranengine/IMOGEN/output/<year>/*.dat
#              (3698-grid Fortran-engine output from scripts/run_fortran_engine_only.sh
#               Phase D; 1 GB per SSP)
#     - SINGLE-STEP IDW 3698 → 62892
#     - OUTPUT: runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892/<year>/*.dat
#               (~17 GB per SSP; chosen-pipeline target for paper Track 2 cluster
#                production if user picks δ-B at Phase G)
#
#   δ-B-variant (trunk C++ engine pipeline post-block-8.2.4):
#     - INPUT: forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/<year>/*.dat
#              (1631-grid trunk-C++-engine output from block 8.2.4 Phase E;
#               443 MB per SSP)
#     - CHAINED: STEP 1 = NN 1631 → 3698 (mimics Fortran engine's REGRID_CLIM NN
#       internal step); STEP 2 = IDW 3698 → 62892
#     - INTERMEDIATE: forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_3698_cppengine/<year>/*.dat
#     - OUTPUT: forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/<year>/*.dat
#               (~17 GB per SSP; chosen-pipeline target for paper Track 2 cluster
#                production if user picks δ-B-variant at Phase G)
#
# CO2.dat handling: per Rule #9 datapoint #23 surfaced at Phase C canary, CO2.dat
# is structurally a single-line atmospheric-concentration time-series (not per-cell
# field) and is NOT regriddable spatially. Wrapper cp's CO2.dat (+ done + dtemp_o
# + fa_ocean ocean-state files) from input → output as-is for each year.
#
# Usage:
#   scripts/run_fastregrid.sh <SSP> <pipeline>
#     where <SSP> = SSP1-2.6 / SSP2-4.5 / SSP3-7.0 / SSP4-6.0 / SSP5-8.5
#     and <pipeline> = delta_b / delta_b_variant
#
# Cross-references:
#   - notes/B57.md (switchable-regrid-strategy + δ-B-variant wiring)
#   - notes/B59.md (δ-B-variant decision; chained-FastRegrid for v1.0)
#   - tools/FastRegrid/ (the regrid binary; block 8.2.5 Phase C)
#   - _chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_wiring_plan.md
#
# - Daniel Bampoh, 2026-05-26 (session 11 day 2 block 8.2.5 Phase E)
# ============================================================================

set -euo pipefail

if [ $# -lt 2 ]; then
    echo "Usage: scripts/run_fastregrid.sh <SSP> <pipeline>"
    echo "  <SSP>      = SSP1-2.6 / SSP2-4.5 / SSP3-7.0 / SSP4-6.0 / SSP5-8.5"
    echo "  <pipeline> = delta_b (Fortran engine; IDW 3698→62892) | delta_b_variant (trunk C++ engine; chained NN 1631→3698 + IDW 3698→62892)"
    exit 1
fi

SSP="$1"
PIPELINE="$2"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FASTREGRID_BIN="${FASTREGRID_BIN:-${ROOT}/tools/FastRegrid/build/fastregrid_example}"
GRIDLIST_3698="${ROOT}/data/gridlist/gridlist_hurtt_RNDM_midpoint_3698.txt"
GRIDLIST_62892="${ROOT}/data/gridlist/gridlist_in_62892_and_climate.txt"
FIRST_YEAR=${FIRST_YEAR:-1900}
LAST_YEAR=${LAST_YEAR:-2100}
# [Block 8.2.5 Phase E (2026-05-26) Rule #9 datapoint #31: pass --radius 0
#  to disable the IDW within-radius source-filter (regrid.cpp:151) which
#  defaults to 100 km. For our sparse 3696-cell source (~5° spacing =
#  ~500 km between cells) regridding to dense 62538-cell target, MANY
#  target cells find ZERO sources within 100 km → empty idw_mapping_[i] →
#  std::vector::operator[] bounds violation on closest_indices[0] at
#  interpolate_idw line 341. Fix: --radius 0 disables filter; always
#  takes top-max_points=5 nearest regardless of distance. - DKB block 8.2.5]
RADIUS=${RADIUS:-0}

[ -x "${FASTREGRID_BIN}" ] || { echo "ERROR: FASTREGRID_BIN not executable: ${FASTREGRID_BIN}"; exit 1; }
[ -f "${GRIDLIST_3698}" ] || { echo "ERROR: 3698-grid gridlist missing: ${GRIDLIST_3698}"; exit 1; }
[ -f "${GRIDLIST_62892}" ] || { echo "ERROR: 62892-grid gridlist missing: ${GRIDLIST_62892}"; exit 1; }

LOG_DIR="${ROOT}/logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/run_fastregrid_${SSP}_${PIPELINE}_$(date '+%Y%m%d_%H%M%S').log"

# Helper: cp non-regriddable per-year files from input → output (CO2.dat + done + dtemp_o + fa_ocean)
cp_nonregrid_files() {
    local in_base="$1"
    local out_base="$2"
    for year in $(seq "${FIRST_YEAR}" "${LAST_YEAR}"); do
        local in_year_dir="${in_base}/${year}"
        local out_year_dir="${out_base}/${year}"
        [ -d "${in_year_dir}" ] || continue
        mkdir -p "${out_year_dir}"
        for f in CO2.dat done dtemp_o.dat fa_ocean.dat; do
            if [ -f "${in_year_dir}/${f}" ]; then
                cp "${in_year_dir}/${f}" "${out_year_dir}/${f}"
            fi
        done
    done
    # Top-level engine state files (one-shot) at IMOGEN/ root
    local in_root="$(dirname "${in_base}")"
    local out_root="$(dirname "${out_base}")"
    # [Block 8.2.5 Phase E δ-B-variant Rule #9 datapoint #32: when in_base + out_base
    #  are SIBLINGS under the same IMOGEN/ parent (always true for both pipelines
    #  since intermediate + final dirs live under IMOGEN/), dirname(in_base) ==
    #  dirname(out_base) and cp self-copies, which errors and (with set -e at top
    #  of script) terminates the script. Benign for single-step δ-B (triggers at
    #  end of script after success), but FATAL for chained δ-B-variant (kills
    #  STEP 2 IDW before it starts). Skip the cp when paths are the same — they
    #  ARE the same file in that case; no copy needed. - DKB block 8.2.5]
    if [ "${in_root}" != "${out_root}" ]; then
        for f in CO2_all.dat RF_all.dat VARYEAR.dat; do
            if [ -f "${in_root}/${f}" ]; then
                cp "${in_root}/${f}" "${out_root}/${f}"
            fi
        done
    fi
}

echo "================================================================================" | tee "${LOG_FILE}"
echo "run_fastregrid.sh — ${PIPELINE} pipeline for ${SSP}" | tee -a "${LOG_FILE}"
echo "  Pipeline: ${PIPELINE}" | tee -a "${LOG_FILE}"
echo "  SSP: ${SSP}" | tee -a "${LOG_FILE}"
echo "  Year range: ${FIRST_YEAR}-${LAST_YEAR}" | tee -a "${LOG_FILE}"
echo "  Start: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${LOG_FILE}"
echo "================================================================================" | tee -a "${LOG_FILE}"

case "${PIPELINE}" in
    delta_b)
        INPUT_BASE="${ROOT}/runs/${SSP}/Common-directory-fortranengine/IMOGEN/output"
        OUTPUT_BASE="${ROOT}/runs/${SSP}/Common-directory-fortranengine/IMOGEN/output_62892"
        [ -d "${INPUT_BASE}" ] || { echo "ERROR: δ-B input (Fortran engine 3698-grid output) missing: ${INPUT_BASE}"; exit 1; }
        echo "[run] δ-B IDW 3698→62892" | tee -a "${LOG_FILE}"
        echo "[run] Input:  ${INPUT_BASE}/" | tee -a "${LOG_FILE}"
        echo "[run] Output: ${OUTPUT_BASE}/" | tee -a "${LOG_FILE}"
        "${FASTREGRID_BIN}" --mode imogen --input "${INPUT_BASE}" --output "${OUTPUT_BASE}" --target-gridlist "${GRIDLIST_62892}" --method IDW --radius "${RADIUS}" --first-year "${FIRST_YEAR}" --last-year "${LAST_YEAR}" --verbose 2>&1 | tee -a "${LOG_FILE}"
        echo "[run] cp non-regriddable per-year files (CO2.dat + done + dtemp_o + fa_ocean) from input → output" | tee -a "${LOG_FILE}"
        cp_nonregrid_files "${INPUT_BASE}" "${OUTPUT_BASE}"
        ;;
    delta_b_variant)
        INPUT_BASE="${ROOT}/forks/trunk_r13078_runs/${SSP}/Common-directory/IMOGEN/output"
        INTERMEDIATE_BASE="${ROOT}/forks/trunk_r13078_runs/${SSP}/Common-directory/IMOGEN/output_3698_cppengine"
        OUTPUT_BASE="${ROOT}/forks/trunk_r13078_runs/${SSP}/Common-directory/IMOGEN/output_62892_cppengine"
        [ -d "${INPUT_BASE}" ] || { echo "ERROR: δ-B-variant input (trunk C++ engine 1631-grid output) missing: ${INPUT_BASE}"; exit 1; }
        echo "[run] δ-B-variant CHAINED: STEP 1 = NN 1631→3698" | tee -a "${LOG_FILE}"
        echo "[run]   Input:        ${INPUT_BASE}/" | tee -a "${LOG_FILE}"
        echo "[run]   Intermediate: ${INTERMEDIATE_BASE}/" | tee -a "${LOG_FILE}"
        "${FASTREGRID_BIN}" --mode imogen --input "${INPUT_BASE}" --output "${INTERMEDIATE_BASE}" --target-gridlist "${GRIDLIST_3698}" --method NN --radius "${RADIUS}" --first-year "${FIRST_YEAR}" --last-year "${LAST_YEAR}" --verbose 2>&1 | tee -a "${LOG_FILE}"
        echo "[run]   cp non-regriddable per-year files for STEP 1 intermediate" | tee -a "${LOG_FILE}"
        cp_nonregrid_files "${INPUT_BASE}" "${INTERMEDIATE_BASE}"
        echo "[run] δ-B-variant CHAINED: STEP 2 = IDW 3698→62892" | tee -a "${LOG_FILE}"
        echo "[run]   Input:  ${INTERMEDIATE_BASE}/" | tee -a "${LOG_FILE}"
        echo "[run]   Output: ${OUTPUT_BASE}/" | tee -a "${LOG_FILE}"
        "${FASTREGRID_BIN}" --mode imogen --input "${INTERMEDIATE_BASE}" --output "${OUTPUT_BASE}" --target-gridlist "${GRIDLIST_62892}" --method IDW --radius "${RADIUS}" --first-year "${FIRST_YEAR}" --last-year "${LAST_YEAR}" --verbose 2>&1 | tee -a "${LOG_FILE}"
        echo "[run]   cp non-regriddable per-year files for STEP 2 final" | tee -a "${LOG_FILE}"
        cp_nonregrid_files "${INTERMEDIATE_BASE}" "${OUTPUT_BASE}"
        ;;
    *)
        echo "ERROR: <pipeline> must be 'delta_b' or 'delta_b_variant'; got '${PIPELINE}'"
        exit 1
        ;;
esac

# Verify output
YEAR_COUNT=$(ls "${OUTPUT_BASE}/" 2>/dev/null | grep -E "^[0-9]{4}$" | wc -l)
LIB_SIZE=$(du -sh "${OUTPUT_BASE}/" 2>/dev/null | awk '{print $1}')
echo "================================================================================" | tee -a "${LOG_FILE}"
echo "[verify] Year-dirs produced: ${YEAR_COUNT}" | tee -a "${LOG_FILE}"
echo "[verify] Library size: ${LIB_SIZE} (expected ~17 GB at 62892-grid)" | tee -a "${LOG_FILE}"
echo "  End: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${LOG_FILE}"
echo "================================================================================" | tee -a "${LOG_FILE}"
