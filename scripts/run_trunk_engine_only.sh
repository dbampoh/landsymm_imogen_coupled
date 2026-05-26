#!/bin/bash
# scripts/run_trunk_engine_only.sh
# -----------------------------------------------------------------------------
# Block 8.2 phase F (NEW; session 10 day 1 evening) — Trunk_r13078 binary's C++
# engine standalone-mode wrapper.
#
# Companion to scripts/run_coupled.sh --engine-only-mode (which exercises the
# REBUILD lpjguess/build/guess binary's engine from runs/<SCEN>/). This wrapper
# exercises the TRUNK_R13078 fork's binary at forks/trunk_r13078/build/guess
# from forks/trunk_r13078_runs/<SCEN>/ — producing a truly-independent engine
# library at forks/trunk_r13078_runs/<SCEN>/Common-directory/IMOGEN/output/
# (vs the cp'd library from runs/<SCEN>/ that was set up at block 8.2 phase E
# per the γ-physical-separation design decision).
#
# Why both binaries needed (per user direction "Option D both b+c"; block 8.2.f):
# climatemodel.cpp + climatemodel.h are BYTE-IDENTICAL between lpjguess/modules/
# and forks/trunk_r13078/modules/ (per block 8.1.5 §6); so the engine output is
# expected to be byte-identical between the two binaries. BUT separate invocations
# provide independent FILESYSTEM EVIDENCE that each fork's binary was actually
# exercised at v1.0 — strengthening paper Methods §2.2 narrative + setting up the
# v1+ trajectory where the two forks' climatemodel.cpp MIGHT diverge (post-paper
# Installment-2 backport per LEDGER §1.2; v1+ live-coupling REGRID port per B54+B56).
#
# Usage:
#   scripts/run_trunk_engine_only.sh <SSP>
# Example:
#   scripts/run_trunk_engine_only.sh SSP1-2.6
#
# Pre-requisites:
#   - forks/trunk_r13078/build/guess binary built
#   - forks/trunk_r13078_runs/<SSP>/main_engine_only.ins exists (scaffolded at
#     block 8.2 phase F; flips skip_inprocess_engine_run=0 + un-nulls FILE_*_EMITS /
#     FILE_LPJG_* via end-of-file overrides pointing at runs/<SSP>/inputs/ adapter
#     outputs; SSP-specific CMIP6 non-CO2 RF file)
#   - runs/<SSP>/inputs/ adapter outputs exist (produced by scripts/run_coupled.sh
#     either via prior engine-only-mode run on the rebuild side or a fresh adapter run)
#
# Workflow:
#   1. Setup trunk-runs/<SSP>/Common-directory/{IMOGEN/output,LPJG_main/IMOGEN}
#      structure (engine writes to IMOGEN/output/<year>/; sidecar writes 'done'
#      marker to LPJG_main/IMOGEN/done)
#   2. Clean prior engine output at trunk-runs/<SSP>/Common-directory/IMOGEN/output/
#      (might be cp'd from runs/<SSP>/Common-directory/ at block 8.2 phase E;
#      will be replaced with truly-independent trunk-engine output)
#   3. Spawn path-iv sidecar bash process: touches 'done' marker every 1s
#      (mimics scripts/run_coupled.sh --engine-only-mode mechanism per B37 + B44)
#   4. Run forks/trunk_r13078/build/guess -input imogencfx main_engine_only.ins
#      from forks/trunk_r13078_runs/<SSP>/
#   5. Engine exits 99 on YEAR1==2100 over-shoot (expected per B37/B44/B45);
#      sidecar cleanup via trap-on-EXIT
#   6. Verify output: 202 year-dirs (1900-2101); ~443 MB library
#
# See:
#   - notes/B37.md §5 (path-iv done-marker sidecar mechanism)
#   - notes/B44.md (--engine-only-mode productisation in scripts/run_coupled.sh)
#   - notes/B47.md §4 (T_seq Installment-1 design; sequential-standalone workflow)
#   - _chat_artifacts/b8_1_5_architectural_clarification_2026-05-22/ §6 (climatemodel.cpp
#     byte-identity between lpjguess/ + forks/trunk_r13078/ confirmed)
#   - _chat_artifacts/b8_2_engine_libraries_2026-05-22/ (block 8.2 audit-evidence bundle)
#
# - Daniel Bampoh, block 8.2 phase F (2026-05-22 evening session 10 day 1)
# -----------------------------------------------------------------------------

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <SSP>" >&2
  echo "Available SSPs: SSP1-2.6 SSP2-4.5 SSP3-7.0 SSP4-6.0 SSP5-8.5" >&2
  exit 1
fi

SSP="$1"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# [Block 8.2.4 (2026-05-26) — TRUNK_BIN env-overridable so block 8.2.4 canary
#  run can target ${ROOT}/forks/trunk_r13078/build_b824/guess (the
#  block-8.2.4 forward-port-built binary) while preserving the legacy
#  ${ROOT}/forks/trunk_r13078/build/guess default for future use. - DKB]
TRUNK_BIN="${TRUNK_BIN:-${ROOT}/forks/trunk_r13078/build/guess}"
TRUNK_RUN_DIR="${ROOT}/forks/trunk_r13078_runs/${SSP}"
INS_FILE="${TRUNK_RUN_DIR}/main_engine_only.ins"
COMMON_DIR="${TRUNK_RUN_DIR}/Common-directory"
HSHAKE_DIR="${COMMON_DIR}/LPJG_main/IMOGEN"
OUTPUT_DIR="${COMMON_DIR}/IMOGEN/output"
LOG_DIR="${ROOT}/logs"
LOG_FILE="${LOG_DIR}/run_trunk_engine_only_${SSP}_$(date '+%Y%m%d_%H%M%S').log"

mkdir -p "${LOG_DIR}"

# Pre-flight checks
[ -x "${TRUNK_BIN}" ] || { echo "ERROR: trunk binary not found at ${TRUNK_BIN}" | tee -a "${LOG_FILE}"; exit 1; }
[ -d "${TRUNK_RUN_DIR}" ] || { echo "ERROR: trunk-runs dir not found: ${TRUNK_RUN_DIR}" | tee -a "${LOG_FILE}"; exit 1; }
[ -f "${INS_FILE}" ] || { echo "ERROR: main_engine_only.ins not found at ${INS_FILE}" | tee -a "${LOG_FILE}"; exit 1; }
[ -f "${ROOT}/runs/${SSP}/inputs/imogen_lpjg_flux.txt" ] || { echo "ERROR: adapter inputs not found at runs/${SSP}/inputs/imogen_lpjg_flux.txt; run scripts/run_coupled.sh first" | tee -a "${LOG_FILE}"; exit 1; }

echo "================================================================================" | tee -a "${LOG_FILE}"
echo "run_trunk_engine_only.sh — trunk_r13078 binary's C++ engine standalone-mode" | tee -a "${LOG_FILE}"
echo "  SSP: ${SSP}" | tee -a "${LOG_FILE}"
echo "  Trunk binary: ${TRUNK_BIN}" | tee -a "${LOG_FILE}"
echo "  Trunk-runs dir: ${TRUNK_RUN_DIR}" | tee -a "${LOG_FILE}"
echo "  main_engine_only.ins: ${INS_FILE}" | tee -a "${LOG_FILE}"
echo "  Output dir: ${OUTPUT_DIR}" | tee -a "${LOG_FILE}"
echo "  Log file: ${LOG_FILE}" | tee -a "${LOG_FILE}"
echo "  Start: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${LOG_FILE}"
echo "================================================================================" | tee -a "${LOG_FILE}"

# Setup Common-directory structure (engine writes here; sidecar touches done marker here)
mkdir -p "${HSHAKE_DIR}"
echo "[setup] ${HSHAKE_DIR} ready" | tee -a "${LOG_FILE}"

# Clean prior engine output (cp'd from runs/<SSP>/ at block 8.2 phase E will be replaced)
if [ -d "${OUTPUT_DIR}" ] && [ "$(ls -A "${OUTPUT_DIR}" 2>/dev/null | wc -l)" -gt 0 ]; then
  echo "[setup] Cleaning prior engine output at ${OUTPUT_DIR}/ (will be replaced with truly-independent trunk-engine output)" | tee -a "${LOG_FILE}"
  rm -rf "${OUTPUT_DIR}"
fi
mkdir -p "${OUTPUT_DIR}"

# [Block 8.2.4 (2026-05-26) — bootstrap handshake file imogen_lpjg.txt mirroring
#  lpjguess's scripts/run_coupled.sh --engine-only-mode pattern at Step [4/7]
#  (lines 414-446 of that script). Without this bootstrap, trunk's freshly-
#  forward-ported engine (now byte-identical with lpjguess's climatemodel.cpp at
#  the step-7 polling guard logic introduced at C2/C3 fix) gets stuck in the
#  polling loop because runnowExist=false (no imogen_lpjg.txt to read).
#  Engine reads actual config from IMOGENConfig (parsed from imogen_intermediary.ins)
#  after escaping the first poll; bootstrap values are only seeds for iteration 1's
#  polling escape. Surfaced as Rule #9 datapoint at Phase D canary. - DKB block 8.2.4]
echo "[setup] Bootstrap-writing imogen_lpjg.txt + done at ${HSHAKE_DIR}/" | tee -a "${LOG_FILE}"
YEAR1_BOOT=1900
IYEND_BOOT=1901
if [ "${YEAR1_BOOT}" -lt 1901 ]; then SPINUP_BOOT="TRUE"; else SPINUP_BOOT="FALSE"; fi
FIRSTCALL_BOOT="TRUE"
cat > "${HSHAKE_DIR}/imogen_lpjg.txt" <<EOF
YEAR1 ${YEAR1_BOOT} !IN First year of the numerical experiment
IYEND ${IYEND_BOOT} !IN Stop year of the ENTIRE run
YEAR1_LPJG ${YEAR1_BOOT} !IN First year of the whole LPJ-GUESS simulation
SPINUP ${SPINUP_BOOT} !IN Are we in the spin-up phase of LPJ-GUESS?
KEEPRUNNING TRUE !IN control flag to keep imogen running
FIRSTCALL ${FIRSTCALL_BOOT} !IN Is this the very first call to IMOGEN from LPJ-GUESS
EOF
if [ ! -f "${HSHAKE_DIR}/done" ]; then
  echo "bootstrap" > "${HSHAKE_DIR}/done"
fi
echo "[setup] Bootstrap files written: ${HSHAKE_DIR}/{imogen_lpjg.txt, done} (SPINUP=${SPINUP_BOOT}, FIRSTCALL=${FIRSTCALL_BOOT}, KEEPRUNNING=TRUE)" | tee -a "${LOG_FILE}"

# Spawn path-iv sidecar: touch done marker every 1s (mimics scripts/run_coupled.sh --engine-only-mode)
(while true; do touch "${HSHAKE_DIR}/done" 2>/dev/null; sleep 1; done) &
SIDECAR_PID=$!
echo "[setup] sidecar spawned: PID=${SIDECAR_PID}" | tee -a "${LOG_FILE}"

cleanup_sidecar() {
  if [ -n "${SIDECAR_PID:-}" ] && kill -0 "${SIDECAR_PID}" 2>/dev/null; then
    kill "${SIDECAR_PID}" 2>/dev/null || true
    wait "${SIDECAR_PID}" 2>/dev/null || true
    echo "[cleanup] sidecar PID=${SIDECAR_PID} cleaned up" | tee -a "${LOG_FILE}"
  fi
  rm -f "${HSHAKE_DIR}/done" 2>/dev/null || true
}
trap cleanup_sidecar EXIT

# Run trunk_r13078 binary's engine from trunk-runs/<SSP>/
echo "[run] cd ${TRUNK_RUN_DIR} && ${TRUNK_BIN} -input imogencfx main_engine_only.ins" | tee -a "${LOG_FILE}"
cd "${TRUNK_RUN_DIR}"

EXIT_CODE=0
"${TRUNK_BIN}" -input imogencfx main_engine_only.ins 2>&1 | tee -a "${LOG_FILE}" || EXIT_CODE=$?

# Engine exits 99 on YEAR1==2100 over-shoot (per climatemodel.cpp:1185-1199 brittle year sentinels; B45 v1+ source-edit cleanup)
echo "================================================================================" | tee -a "${LOG_FILE}"
if [ "${EXIT_CODE}" -eq 99 ]; then
  echo "[ok] trunk engine exited 99 (EXPECTED — YEAR1==2100 over-shoot; same as lpjguess engine behavior per B37+B44)" | tee -a "${LOG_FILE}"
elif [ "${EXIT_CODE}" -eq 0 ]; then
  echo "[ok] trunk engine exited 0 (clean exit)" | tee -a "${LOG_FILE}"
else
  echo "[error] trunk engine exited ${EXIT_CODE} (unexpected; see log)" | tee -a "${LOG_FILE}"
fi

# Verify output
YEAR_COUNT=$(ls "${OUTPUT_DIR}/" 2>/dev/null | wc -l)
LIB_SIZE=$(du -sh "${OUTPUT_DIR}/" 2>/dev/null | awk '{print $1}')
echo "[verify] Year-dirs produced: ${YEAR_COUNT} (expected: 202)" | tee -a "${LOG_FILE}"
echo "[verify] Library size: ${LIB_SIZE} (expected: ~443M)" | tee -a "${LOG_FILE}"
echo "  End: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${LOG_FILE}"
echo "================================================================================" | tee -a "${LOG_FILE}"

exit 0
