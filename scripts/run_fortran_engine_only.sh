#!/usr/bin/env bash
# ============================================================================
# scripts/run_fortran_engine_only.sh — Fortran IMOGEN engine standalone-mode
#
# Authored at block 8.2.5 (2026-05-26 session 11 day 2) per the wiring plan at
# _chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_wiring_plan.md.
#
# Mirrors block 8.2.4's scripts/run_trunk_engine_only.sh wrapper pattern (which
# exercised trunk's forward-ported C++ engine; same bootstrap + sidecar
# mechanism); adapted for Fortran-specific I/O conventions:
#
# 1. PER-SSP RUNTIME DIR: cd into runs/<SSP>/Common-directory-fortranengine/
#    where the per-SSP imogen_settings.txt resides. Engine reads
#    imogen_settings.txt from CWD (imogen_lpjg.f:1712 OPEN(81,FILE='imogen_settings.txt')).
#
# 2. FILE_LPJG_FLUX + FILE_LPJG_CH4_N2O_FLUX path resolution: Fortran engine
#    PREPENDS ${DIR_COMMON}/LPJG_main/IMOGEN/ to these paths (imogen_lpjg.f:634
#    + :652). C++ engine omits prepend (climatemodel.cpp:559). Wrapper
#    accommodates by SYMLINKING the intermediary_py adapter outputs at
#    ../inputs/imogen_lpjg_{flux,ch4_n2o_flux}.txt INTO the handshake dir at
#    ./LPJG_main/IMOGEN/{imogen_lpjg_flux.txt, imogen_lpjg_ch4_n2o_flux.txt}.
#    FILE_LPJG_FLUX is then set to basename only in imogen_settings.txt.
#
# 3. BOOTSTRAP imogen_lpjg.txt: same as C++ engine; Fortran reads YEAR1/IYEND/
#    YEAR1_LPJG/SPINUP/KEEPRUNNING/FIRSTCALL from unit 82 = ${DIR_COMMON}/
#    LPJG_main/IMOGEN/imogen_lpjg.txt (imogen_lpjg.f:1905 OPEN(82,FILE=...)).
#
# 4. PATH-IV SIDECAR: touches ${HSHAKE_DIR}/done every 1s. Fortran engine reads
#    this at line ~426 INQUIRE for "done" existence to escape its inner polling
#    loop (analogous to C++ engine's polling at climatemodel.cpp:336 onwards).
#
# Usage:
#   FORTRAN_BIN=$(pwd)/imogen/code/imogen_lpjg scripts/run_fortran_engine_only.sh <SSP>
#     where <SSP> is one of SSP1-2.6 / SSP2-4.5 / SSP3-7.0 / SSP4-6.0 / SSP5-8.5
#
# Output:
#   runs/<SSP>/Common-directory-fortranengine/IMOGEN/output/<year>/*.dat
#     (3698-grid Fortran engine output for 10 climate vars + CO2.dat + ocean state)
#   1900-2100 = ~201 year-dirs (depending on Fortran engine YEAR1==2100 overshoot)
#   ~1 GB per SSP (3698-grid is 2.27x larger than 1631-grid C++ output's 443 MB)
#
# Cross-references:
#   - notes/B47.md §4 (T_seq design intent)
#   - notes/B37.md §5 (path-iv done-marker sidecar mechanism)
#   - notes/B44.md (lpjguess scripts/run_coupled.sh --engine-only-mode productisation)
#   - scripts/run_trunk_engine_only.sh (block 8.2.4 sibling wrapper for trunk's
#     C++ engine; same bootstrap + sidecar mechanism)
#   - _chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_wiring_plan.md
#
# - Daniel Bampoh, 2026-05-26 (session 11 day 2 block 8.2.5 Phase D)
# ============================================================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: scripts/run_fortran_engine_only.sh <SSP>"
    echo "  e.g. scripts/run_fortran_engine_only.sh SSP1-2.6"
    exit 1
fi

SSP="$1"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# [Block 8.2.5 (2026-05-26): FORTRAN_BIN env-overridable. Default is the rebuild
#  Fortran IMOGEN engine binary at imogen/code/imogen_lpjg (Step 3 ALLOCATABLE
#  + B10 alternating-year fix + B33(c) WARN_POSIX_CONCAT_COLLAPSE; binary built
#  May 17 2026; 142,112 bytes; md5 854a9f55316bbba06dd75898966dafc7). - DKB]
FORTRAN_BIN="${FORTRAN_BIN:-${ROOT}/imogen/code/imogen_lpjg}"
RUN_DIR="${ROOT}/runs/${SSP}/Common-directory-fortranengine"
INPUTS_DIR="${ROOT}/runs/${SSP}/inputs"
INS_FILE="${RUN_DIR}/imogen_settings.txt"
HSHAKE_DIR="${RUN_DIR}/LPJG_main/IMOGEN"
OUTPUT_DIR="${RUN_DIR}/IMOGEN/output"
LOG_DIR="${ROOT}/logs"
LOG_FILE="${LOG_DIR}/run_fortran_engine_only_${SSP}_$(date '+%Y%m%d_%H%M%S').log"

mkdir -p "${LOG_DIR}"
[ -x "${FORTRAN_BIN}" ] || { echo "ERROR: FORTRAN_BIN not executable: ${FORTRAN_BIN}" | tee -a "${LOG_FILE}"; exit 1; }
[ -f "${INS_FILE}" ] || { echo "ERROR: per-SSP imogen_settings.txt not found at ${INS_FILE}" | tee -a "${LOG_FILE}"; exit 1; }
[ -d "${INPUTS_DIR}" ] || { echo "ERROR: intermediary_py adapter outputs dir not found at ${INPUTS_DIR}" | tee -a "${LOG_FILE}"; exit 1; }

echo "================================================================================" | tee "${LOG_FILE}"
echo "run_fortran_engine_only.sh — Fortran IMOGEN engine standalone-mode for ${SSP}" | tee -a "${LOG_FILE}"
echo "  SSP: ${SSP}" | tee -a "${LOG_FILE}"
echo "  Fortran binary: ${FORTRAN_BIN}" | tee -a "${LOG_FILE}"
echo "  Run dir: ${RUN_DIR}" | tee -a "${LOG_FILE}"
echo "  Inputs dir (adapter outputs): ${INPUTS_DIR}" | tee -a "${LOG_FILE}"
echo "  imogen_settings.txt: ${INS_FILE}" | tee -a "${LOG_FILE}"
echo "  Handshake dir: ${HSHAKE_DIR}" | tee -a "${LOG_FILE}"
echo "  Output dir: ${OUTPUT_DIR}" | tee -a "${LOG_FILE}"
echo "  Log file: ${LOG_FILE}" | tee -a "${LOG_FILE}"
echo "  Start: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${LOG_FILE}"
echo "================================================================================" | tee -a "${LOG_FILE}"

# Setup handshake dir
mkdir -p "${HSHAKE_DIR}"
echo "[setup] ${HSHAKE_DIR} ready" | tee -a "${LOG_FILE}"

# [Block 8.2.5 (2026-05-26): SYMLINK intermediary_py adapter outputs into the
#  handshake dir because Fortran engine PREPENDS ${DIR_COMMON}/LPJG_main/IMOGEN/
#  to FILE_LPJG_FLUX + FILE_LPJG_CH4_N2O_FLUX (imogen_lpjg.f:634 + :652). The
#  per-SSP imogen_settings.txt sets these to basename only; the symlinks here
#  make them resolve at runtime. - DKB block 8.2.5]
echo "[setup] Symlinking intermediary_py adapter outputs into ${HSHAKE_DIR}/" | tee -a "${LOG_FILE}"
for f in imogen_lpjg_flux.txt imogen_lpjg_ch4_n2o_flux.txt; do
    src="${INPUTS_DIR}/${f}"
    dst="${HSHAKE_DIR}/${f}"
    [ -f "${src}" ] || { echo "ERROR: adapter output not found at ${src}" | tee -a "${LOG_FILE}"; exit 1; }
    ln -sfn "${src}" "${dst}"
    echo "  ${dst} → ${src} ✅" | tee -a "${LOG_FILE}"
done

# Clean prior engine output if present
if [ -d "${OUTPUT_DIR}" ] && [ "$(ls -A "${OUTPUT_DIR}" 2>/dev/null | wc -l)" -gt 0 ]; then
    echo "[setup] Cleaning prior engine output at ${OUTPUT_DIR}/ (will be replaced)" | tee -a "${LOG_FILE}"
    rm -rf "${OUTPUT_DIR}"
fi
mkdir -p "${OUTPUT_DIR}"

# [Block 8.2.5 (2026-05-26): bootstrap imogen_lpjg.txt mirroring lpjguess's
#  scripts/run_coupled.sh --engine-only-mode Step [4/7] pattern (lines 414-446)
#  + block 8.2.4 scripts/run_trunk_engine_only.sh adaptation (Rule #9 #20 fix).
#  Fortran engine reads YEAR1/IYEND/YEAR1_LPJG/SPINUP/KEEPRUNNING/FIRSTCALL
#  from unit 82 = ${DIR_COMMON}/LPJG_main/IMOGEN/imogen_lpjg.txt
#  (imogen_lpjg.f:1905 OPEN(82,...)). Without bootstrap, engine polling loop
#  stuck because LPJG main loop hasn't written imogen_lpjg.txt yet
#  (the same Rule #9 pattern as block 8.2 Phase F that surfaced B61).
#
#  SPINUP="FALSE" (production-grade): matches C++ engine config at
#  runs/<SSP>/imogen_intermediary.ins SPINUP=0 (matches block 8.2 Phase D +
#  block 8.2.4 Phase E). Production-grade 1900-2100 run with LPJG natural
#  fluxes (LPJG_CFLUX=.TRUE.) — NOT the lpjguess smoke 1900-1901 window
#  which used SPINUP=TRUE. With SPINUP=TRUE, Fortran engine SKIPS per-year
#  CO2.dat write (imogen_lpjg.f:897 IF(SPINUP.EQV..FALSE.) THEN) which is
#  what trunk-T_seq LPJG needs per file_co2 path
#  (./Common-directory/IMOGEN/output/YYYY/CO2.dat). Rule #9 datapoint #25
#  surfaced at Phase D canary v2 (year 1925/1950/1975 missing CO2.dat).
#  - DKB block 8.2.5]
echo "[setup] Bootstrap-writing imogen_lpjg.txt + done at ${HSHAKE_DIR}/" | tee -a "${LOG_FILE}"
YEAR1_BOOT=1900
IYEND_BOOT=2100
SPINUP_BOOT="FALSE"
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
echo "[setup] Bootstrap files written (YEAR1=${YEAR1_BOOT}, IYEND=${IYEND_BOOT}, SPINUP=${SPINUP_BOOT}, FIRSTCALL=${FIRSTCALL_BOOT}, KEEPRUNNING=TRUE)" | tee -a "${LOG_FILE}"

# Spawn path-iv done-marker sidecar (mimics scripts/run_coupled.sh --engine-only-mode)
(while true; do touch "${HSHAKE_DIR}/done" 2>/dev/null; sleep 1; done) &
SIDECAR_PID=$!
echo "[setup] Sidecar spawned: PID=${SIDECAR_PID}" | tee -a "${LOG_FILE}"

cleanup_sidecar() {
    if [ -n "${SIDECAR_PID:-}" ] && kill -0 "${SIDECAR_PID}" 2>/dev/null; then
        kill "${SIDECAR_PID}" 2>/dev/null || true
        wait "${SIDECAR_PID}" 2>/dev/null || true
        echo "[cleanup] Sidecar PID=${SIDECAR_PID} cleaned up" | tee -a "${LOG_FILE}"
    fi
    rm -f "${HSHAKE_DIR}/done" 2>/dev/null || true
}
trap cleanup_sidecar EXIT

# Run Fortran engine from per-SSP runtime dir
echo "[run] cd ${RUN_DIR} && ${FORTRAN_BIN}" | tee -a "${LOG_FILE}"
cd "${RUN_DIR}"

# [Block 8.2.5 (2026-05-26) Rule #9 datapoint #27: Fortran engine never exits
#  in standalone engine-only-mode because the outer DO WHILE (KEEPRUNNING)
#  loop at imogen_lpjg.f:391 expects LPJ-GUESS to flip KEEPRUNNING to FALSE
#  via re-writing imogen_lpjg.txt (KEEPRUNNING is documented at line 283 as
#  "Exit logical for while loop, provided by LPJ-GUESS"). In our standalone
#  engine-only-mode, LPJ-GUESS doesn't run, so KEEPRUNNING stays TRUE → the
#  outer loop endlessly re-cycles the inner year-loop 1900-2100 (engine
#  rewrites year-dir contents identically each cycle; CO2_all.dat append-mode
#  accumulates entries across cycles). To handle gracefully:
#    (1) After 201 year-dirs (i.e., year-loop completes its first cycle),
#        REWRITE imogen_lpjg.txt with KEEPRUNNING=FALSE. The engine's
#        SETTIN_LPJG call (imogen_lpjg.f:458, inside the per-year inner
#        loop) re-reads this file each year-iteration → on the next
#        iteration the engine picks up KEEPRUNNING=FALSE → outer loop
#        exits cleanly.
#    (2) Wait briefly for graceful exit.
#    (3) SIGTERM/SIGKILL as fallback if engine still doesn't exit
#        (e.g., the re-read might happen partway through cycle 2).
#  - DKB block 8.2.5]
(
    # [Block 8.2.5 (2026-05-26) Rule #9 datapoint #28: disable strict mode in
    #  watchdog subshell because the parent's `set -euo pipefail` (top of
    #  script) makes the `ls ... | grep ... | wc -l` pipeline die when
    #  OUTPUT_DIR is empty (grep returns 1 if no matches → pipefail kills
    #  the subshell). At Phase E 4-way parallel launch (block 8.2.5), this
    #  caused all 4 watchdogs to die SILENTLY at engine launch when
    #  OUTPUT_DIR was freshly mkdir'd + empty; engines then ran forever per
    #  Rule #9 #27 KEEPRUNNING-loop hang until manual SIGTERM. Fix:
    #  `set +eo pipefail` in the watchdog subshell. - DKB block 8.2.5]
    set +eo pipefail
    while true; do
        N=$(find "${OUTPUT_DIR}/" -maxdepth 1 -type d -name "[12][0-9][0-9][0-9]" 2>/dev/null | wc -l)
        if [ "${N:-0}" -ge 201 ]; then
            # Give engine ~30s to finish writing the last year-dir's contents
            sleep 30
            ENGINE_PIDS=$(pgrep -f "${FORTRAN_BIN}" | tr '\n' ' ')
            if [ -n "${ENGINE_PIDS}" ]; then
                # Step 1: GRACEFUL EXIT — rewrite imogen_lpjg.txt with KEEPRUNNING FALSE
                # (the canonical exit-signal mechanism per imogen_lpjg.f:283 + :1934)
                echo "[auto-exit] 201/201 year-dirs detected; rewriting imogen_lpjg.txt with KEEPRUNNING=FALSE for graceful exit (PIDs: ${ENGINE_PIDS}); per block-8.2.5 Rule #9 #27" | tee -a "${LOG_FILE}"
                cat > "${HSHAKE_DIR}/imogen_lpjg.txt" <<EOFEXIT
YEAR1 ${YEAR1_BOOT} !IN First year of the numerical experiment
IYEND ${IYEND_BOOT} !IN Stop year of the ENTIRE run
YEAR1_LPJG ${YEAR1_BOOT} !IN First year of the whole LPJ-GUESS simulation
SPINUP ${SPINUP_BOOT} !IN Are we in the spin-up phase of LPJ-GUESS?
KEEPRUNNING FALSE !IN Exit-signal: end the outer DO WHILE (KEEPRUNNING) loop per imogen_lpjg.f:391
FIRSTCALL FALSE !IN This is NOT the first call anymore
EOFEXIT
                # Step 2: give engine ~30s to re-read + exit gracefully
                sleep 30
                # Step 3: SIGTERM fallback if engine still running
                ENGINE_PIDS=$(pgrep -f "${FORTRAN_BIN}" | tr '\n' ' ')
                if [ -n "${ENGINE_PIDS}" ]; then
                    echo "[auto-exit] Engine did not exit gracefully within 30s; SIGTERM fallback (PIDs: ${ENGINE_PIDS})" | tee -a "${LOG_FILE}"
                    for pid in ${ENGINE_PIDS}; do kill -TERM "${pid}" 2>/dev/null || true; done
                    sleep 2
                    # Step 4: SIGKILL last resort
                    for pid in ${ENGINE_PIDS}; do
                        if kill -0 "${pid}" 2>/dev/null; then
                            kill -KILL "${pid}" 2>/dev/null || true
                        fi
                    done
                else
                    echo "[auto-exit] Engine exited gracefully after KEEPRUNNING=FALSE write ✅" | tee -a "${LOG_FILE}"
                fi
            fi
            break
        fi
        sleep 60
    done
) &
WATCHDOG_PID=$!

EXIT_CODE=0
"${FORTRAN_BIN}" 2>&1 | tee -a "${LOG_FILE}" || EXIT_CODE=$?

# Clean up watchdog if engine exited on its own
if kill -0 "${WATCHDOG_PID}" 2>/dev/null; then
    kill "${WATCHDOG_PID}" 2>/dev/null || true
fi

# Fortran engine may exit 0 (clean) or non-zero (Fortran STOP <code>)
echo "================================================================================" | tee -a "${LOG_FILE}"
if [ "${EXIT_CODE}" -eq 0 ]; then
    echo "[ok] Fortran engine exited 0 (clean exit)" | tee -a "${LOG_FILE}"
elif [ "${EXIT_CODE}" -eq 99 ]; then
    echo "[ok] Fortran engine exited 99 (analogous to C++ engine YEAR1==2100 overshoot per B37+B44; if reached this code path)" | tee -a "${LOG_FILE}"
else
    echo "[error] Fortran engine exited ${EXIT_CODE} (unexpected; see log)" | tee -a "${LOG_FILE}"
fi

# Verify output
YEAR_COUNT=$(ls "${OUTPUT_DIR}/" 2>/dev/null | wc -l)
LIB_SIZE=$(du -sh "${OUTPUT_DIR}/" 2>/dev/null | awk '{print $1}')
echo "[verify] Year-dirs produced: ${YEAR_COUNT} (expected: ~201 for 1900-2100; 202 if YEAR1==2100 overshoot)" | tee -a "${LOG_FILE}"
echo "[verify] Library size: ${LIB_SIZE} (expected: ~1 GB; 3698-grid is 2.27x larger than 1631-grid C++ output's 443 MB)" | tee -a "${LOG_FILE}"
echo "  End: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${LOG_FILE}"
echo "================================================================================" | tee -a "${LOG_FILE}"

exit "${EXIT_CODE}"
