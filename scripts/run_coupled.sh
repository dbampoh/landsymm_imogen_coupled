#!/bin/bash
# =============================================================================
# scripts/run_coupled.sh — workstation-Linux LandSyMM-IMOGEN coupled launcher
# =============================================================================
#
# One-shot launcher that walks through the v1.0 coupled-run pipeline:
#
#     [1] Build LPJ-GUESS (skip if up-to-date)         — Anaconda3 NetCDF preferred per Decision #8
#     [2] Run intermediary_py (skip if up-to-date)     — RCMIP-substituted emissions; ~9 min
#     [3] Run the Python -> LPJG-format adapter         — produces 4 ASCII files in runs/<SSP>/inputs/
#     [4] Bootstrap LPJG_main/IMOGEN/ handshake dir     — per step 9 finding, F-10 deadlock workaround
#     [5] Print units banner (per EXECUTION_PLAN.md sec I.D.5)
#     [6] Launch ./guess -input imogencfx main.ins      — the coupled run
#     [7] Collect summary + log path
#
# This is the WORKSTATION variant. The cluster SLURM wrapper is
# scripts/run_coupled.sbatch (lands at step 16; thin wrapper around
# this script via srun).
#
# USAGE
# -----
#     scripts/run_coupled.sh [--scenario <SSP>] [--coupling-mode <mode>]
#                            [--backbone <which>] [--smoke|--production]
#                            [--no-build] [--no-intermediary] [--no-adapter]
#                            [--anaconda3-prefix <path>] [-h]
#
# OPTIONS
#   --scenario SSP        Scenario directory under runs/ (default: SSP1-2.6).
#                         Other supported (when their runs/ dirs are populated):
#                         SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5
#   --coupling-mode MODE  tight | prescribed | loose (default: prescribed).
#                         NB: tight deadlocks in v1.0 single-process mode
#                         (F-10); use only post-F-12 multi-pass design.
#                         prescribed is the v1.0-functional default.
#   --backbone WHICH      static-iiasa (default; predecessor's reference) |
#                         intermediary-py (the RCMIP-substituted backbone)
#                         Both are F-10-deadlock-compatible in prescribed mode.
#                         Switching backbone toggles which Option-A vs
#                         Option-B block is active in imogen_intermediary.ins.
#   --smoke               Smoke-test mode: 4-cell gridlist_test2.txt, 2 years
#                         (1871-1872), nyear_spinup=100, 1 patch. Default for
#                         development. Already configured in main.ins as v1.0.
#   --production          Production mode: 62892-cell production gridlist,
#                         full 1900-2100 horizon, nyear_spinup=500, 25 patches.
#                         REQUIRES F-10/F-12 work to actually complete; v1.0
#                         attempts will engine-output then deadlock at the
#                         per-year handshake (see step 9 empirical findings).
#                         Will print a warning if invoked in v1.0.
#   --no-build            Skip step 1 (use whatever ./guess exists).
#   --no-intermediary     Skip step 2 (assume intermediary_py outputs already
#                         exist at intermediary_py/imogen_ghg_controller/
#                         outputs/imogen_inputs/imogen_inputs_<SSP>.csv).
#   --no-adapter          Skip step 3 (assume runs/<SSP>/inputs/ already populated).
#   --anaconda3-prefix P  Override conda env detection. If set, use
#                         <P>/include and <P>/lib for NETCDF_INCLUDE_DIR /
#                         NETCDF_C_LIBRARY. Default: auto-detect via
#                         $CONDA_PREFIX, $ANACONDA_PREFIX, or fallback to
#                         /home/$USER/anaconda3 if it exists.
#   -h, --help            Show this message and exit.
#
# EXAMPLES
#   scripts/run_coupled.sh                                # smoke; prescribed; static-iiasa; default scenario SSP1-2.6
#   scripts/run_coupled.sh --backbone intermediary-py     # smoke; prescribed; intermediary_py-driven
#   scripts/run_coupled.sh --scenario SSP2-4.5 --no-build # SSP2-4.5; reuse build
#
# DECISIONS
# ---------
# - Build env: Anaconda3 NetCDF preferred per Decision #8 (avoids the
#   libhdf5_serial.so.310 / libcurl.so.4 ABI mismatch on the user's
#   workstation that breaks native-Ubuntu netcdf-dev linking).
# - Coupling mode: prescribed default for v1.0 per F-10 empirical findings
#   (tight deadlocks in single-process mode; resolution at F-12).
# - Backbone: static-iiasa default for v1.0 (matches predecessor + minimizes
#   moving parts); intermediary-py available via flag for paper-stage
#   comparison work (per F-13).
#
# REFERENCES
# ----------
# - EXECUTION_PLAN.md V.1 step 14 + Appendix A.4 + Decision #8
# - notes/STEP_9.md (F-10 deadlock empirical findings)
# - notes/STEP_11.md (intermediary_py end-to-end run details)
# - notes/STEP_13.md (the Python -> LPJG-format adapter)
# - notes/FOLLOWUPS.md F-10 (architectural deadlock; tight mode caveat)
# - notes/FOLLOWUPS.md F-12 (multi-pass tight-mode resolution)
# - docs/build.md (Anaconda3 NetCDF preference docs)
#
# AUTHOR
# ------
# Daniel Bampoh, 2026-05-07 (step 14 of unified-codebase rebuild)
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Color / message helpers
# -----------------------------------------------------------------------------
_red()    { printf '\033[31m%s\033[0m' "$*"; }
_green()  { printf '\033[32m%s\033[0m' "$*"; }
_yellow() { printf '\033[33m%s\033[0m' "$*"; }
_blue()   { printf '\033[34m%s\033[0m' "$*"; }
_bold()   { printf '\033[1m%s\033[0m' "$*"; }

_info()  { echo "[$(date '+%F %T')] $(_blue '[info ]') $*"; }
_warn()  { echo "[$(date '+%F %T')] $(_yellow '[warn ]') $*"; }
_err()   { echo "[$(date '+%F %T')] $(_red '[error]') $*" >&2; }
_ok()    { echo "[$(date '+%F %T')] $(_green '[ok   ]') $*"; }

trap '_err "Launcher aborted at line $LINENO (exit $?). See logs/run_coupled_error.log for details."' ERR

# -----------------------------------------------------------------------------
# Parse args
# -----------------------------------------------------------------------------
SCENARIO="SSP1-2.6"
COUPLING_MODE="prescribed"
BACKBONE="static-iiasa"
RUN_MODE="smoke"
DO_BUILD=1
DO_INTERMEDIARY=1
DO_ADAPTER=1
ANACONDA3_PREFIX_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario)         SCENARIO="$2"; shift 2 ;;
    --coupling-mode)    COUPLING_MODE="$2"; shift 2 ;;
    --backbone)         BACKBONE="$2"; shift 2 ;;
    --smoke)            RUN_MODE="smoke"; shift ;;
    --production)       RUN_MODE="production"; shift ;;
    --no-build)         DO_BUILD=0; shift ;;
    --no-intermediary)  DO_INTERMEDIARY=0; shift ;;
    --no-adapter)       DO_ADAPTER=0; shift ;;
    --anaconda3-prefix) ANACONDA3_PREFIX_OVERRIDE="$2"; shift 2 ;;
    -h|--help)
      # Extract the leading comment block (until the first non-#-prefixed
      # non-shebang line); strip the leading '# ' / '#'.
      awk '
        NR == 1 && /^#!/ { next }
        /^#/ { sub(/^#[ ]?/, ""); print; next }
        { exit }
      ' "$0"
      exit 0
      ;;
    *) _err "Unknown option: $1 (use -h for help)"; exit 2 ;;
  esac
done

# Validate enums
case "$COUPLING_MODE" in tight|prescribed|loose) ;;
  *) _err "--coupling-mode must be tight | prescribed | loose; got '$COUPLING_MODE'"; exit 2 ;; esac
case "$BACKBONE" in static-iiasa|intermediary-py) ;;
  *) _err "--backbone must be static-iiasa | intermediary-py; got '$BACKBONE'"; exit 2 ;; esac
case "$RUN_MODE" in smoke|production) ;;
  *) _err "--smoke/--production conflict; got '$RUN_MODE'"; exit 2 ;; esac

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${ROOT}/runs/${SCENARIO}"
LPJG_DIR="${ROOT}/lpjguess"
LPJG_BUILD="${LPJG_DIR}/build"
GUESS_BIN="${LPJG_BUILD}/guess"
PY_DIR="${ROOT}/intermediary_py/imogen_ghg_controller"
PY_OUT_CSV="${PY_DIR}/outputs/imogen_inputs/imogen_inputs_${SCENARIO}.csv"
ADAPTER="${ROOT}/tools/imogen_inputs_to_lpjg_format.py"
LOG_DIR="${ROOT}/logs"
LOG_FILE="${LOG_DIR}/run_coupled_${SCENARIO}_$(date '+%Y%m%d_%H%M%S').log"
mkdir -p "${LOG_DIR}"

if [ ! -d "${RUN_DIR}" ]; then
  _err "Scenario directory not found: ${RUN_DIR}"
  _err "  Expected: runs/${SCENARIO}/main.ins + imogen_intermediary.ins + ..."
  _err "  At v1.0, only runs/SSP1-2.6/ is populated. To run other scenarios, populate the corresponding runs/<SSP>/."
  exit 1
fi

# -----------------------------------------------------------------------------
# Anaconda3 NetCDF prefix detection (per Decision #8)
# -----------------------------------------------------------------------------
detect_anaconda3_prefix() {
  if [ -n "${ANACONDA3_PREFIX_OVERRIDE}" ]; then
    echo "${ANACONDA3_PREFIX_OVERRIDE}"; return
  fi
  if [ -n "${CONDA_PREFIX:-}" ] && [ -f "${CONDA_PREFIX}/lib/libnetcdf.so" ]; then
    echo "${CONDA_PREFIX}"; return
  fi
  if [ -n "${ANACONDA_PREFIX:-}" ] && [ -f "${ANACONDA_PREFIX}/lib/libnetcdf.so" ]; then
    echo "${ANACONDA_PREFIX}"; return
  fi
  if [ -d "/home/${USER}/anaconda3" ] && [ -f "/home/${USER}/anaconda3/lib/libnetcdf.so" ]; then
    echo "/home/${USER}/anaconda3"; return
  fi
  echo ""
}
ANACONDA3_PREFIX="$(detect_anaconda3_prefix)"

# =============================================================================
# Step 0: Banner (units + active conventions per EXECUTION_PLAN.md sec I.D.5)
# =============================================================================
{
echo
echo "================================================================================"
_bold "LandSyMM-IMOGEN-LPJG coupled run launcher (workstation; step 14)"
echo
echo "  Scenario        : ${SCENARIO}"
echo "  Coupling mode   : ${COUPLING_MODE}  $( [ "$COUPLING_MODE" = "tight" ] && _yellow '(F-10 deadlock applies in v1.0)')"
echo "  Backbone        : ${BACKBONE}"
echo "  Run mode        : ${RUN_MODE}"
echo
echo "  Active conventions (per EXECUTION_PLAN.md sec I.D.5):"
echo "    NEE / NBP        : positive = source to atmosphere"
echo "    CO2 emissions    : Mt CO2/yr (Intermediary) -> PgC/yr (IMOGEN), via /3666.6667"
echo "    CH4 / N2O        : Tg-of-gas/yr; 1 Mt = 1 Tg by mass identity"
echo "    Year indexing    : LPJG year N flux drives IMOGEN year N+1 climate (IYEAR-1 lookup)"
echo "    Cell area        : Earth radius 6371 km; 0.5 deg x 0.5 deg grid; spherical"
echo
echo "  Paths:"
echo "    ROOT          : ${ROOT}"
echo "    Run dir       : ${RUN_DIR}"
echo "    LPJG bin      : ${GUESS_BIN}"
echo "    Anaconda3     : ${ANACONDA3_PREFIX:-(none detected; will use system NetCDF)}"
echo "    Log file      : ${LOG_FILE}"
echo "================================================================================"
echo
} | tee -a "${LOG_FILE}"

if [ "$COUPLING_MODE" = "tight" ]; then
  _warn "tight mode in v1.0 will deadlock at the LPJG <-> IMOGEN handshake (F-10)."
  _warn "  See notes/STEP_9.md sec 4.4 for the empirical confirmation."
  _warn "  v1.0-functional resolution: use --coupling-mode prescribed (default)."
  _warn "  Phase-2 resolution: F-12 multi-pass / two-process design."
fi
if [ "$RUN_MODE" = "production" ]; then
  _warn "production mode in v1.0 will engine-output then deadlock at year-N+1 handshake (F-10)."
  _warn "  v1.0-functional alternative: --smoke (4-cell, 2-year window)."
fi

# =============================================================================
# Step 1: Build LPJ-GUESS (idempotent; skipped if up-to-date)
# =============================================================================
if [ "$DO_BUILD" = "1" ]; then
  if [ -x "${GUESS_BIN}" ]; then
    _info "[1/7] LPJ-GUESS already built at ${GUESS_BIN}; skipping (use absent --no-build to force-skip)."
  else
    _info "[1/7] Building LPJ-GUESS..."
    mkdir -p "${LPJG_BUILD}"
    cd "${LPJG_BUILD}"
    if [ -n "${ANACONDA3_PREFIX}" ]; then
      _info "      Using Anaconda3 NetCDF at ${ANACONDA3_PREFIX} (Decision #8)"
      cmake \
        -DCMAKE_PREFIX_PATH="${ANACONDA3_PREFIX}" \
        -DNETCDF_INCLUDE_DIR="${ANACONDA3_PREFIX}/include" \
        -DNETCDF_C_LIBRARY="${ANACONDA3_PREFIX}/lib/libnetcdf.so" \
        .. 2>&1 | tee -a "${LOG_FILE}"
    else
      _warn "      No Anaconda3 NetCDF detected; using system default (may fail with libhdf5_serial / libcurl ABI mismatch on Ubuntu 22+)."
      cmake .. 2>&1 | tee -a "${LOG_FILE}"
    fi
    make -j"$(nproc)" 2>&1 | tee -a "${LOG_FILE}"
    _ok "[1/7] LPJ-GUESS build complete: ${GUESS_BIN}"
  fi
else
  _info "[1/7] --no-build; skipping LPJ-GUESS build."
fi

if [ ! -x "${GUESS_BIN}" ]; then
  _err "LPJ-GUESS binary not found at ${GUESS_BIN}; cannot proceed."
  exit 1
fi

# =============================================================================
# Step 2: Run intermediary_py if intermediary_py-driven backbone is selected
# =============================================================================
if [ "$BACKBONE" = "intermediary-py" ] && [ "$DO_INTERMEDIARY" = "1" ]; then
  if [ -f "${PY_OUT_CSV}" ]; then
    _info "[2/7] intermediary_py output already present: ${PY_OUT_CSV}; skipping (delete it to force re-run)."
  else
    _info "[2/7] Running intermediary_py end-to-end (~9 min on workstation)..."
    cd "${PY_DIR}"
    python3 run_all.py --skip-plots 2>&1 | tee -a "${LOG_FILE}"
    if [ ! -f "${PY_OUT_CSV}" ]; then
      _err "intermediary_py finished but expected output missing: ${PY_OUT_CSV}"
      exit 1
    fi
    _ok "[2/7] intermediary_py complete; output at ${PY_OUT_CSV}"
  fi
else
  _info "[2/7] backbone=static-iiasa (predecessor's reference files); skipping intermediary_py."
fi

# =============================================================================
# Step 3: Run the Python -> LPJG-format adapter (intermediary-py mode only)
# =============================================================================
if [ "$BACKBONE" = "intermediary-py" ] && [ "$DO_ADAPTER" = "1" ]; then
  _info "[3/7] Running adapter to produce 4 narrow ASCII files at ${RUN_DIR}/inputs/..."
  python3 "${ADAPTER}" \
    --input  "${PY_OUT_CSV}" \
    --output "${RUN_DIR}/inputs/" \
    2>&1 | tee -a "${LOG_FILE}"
  _ok "[3/7] Adapter complete; 4 files at ${RUN_DIR}/inputs/"
else
  _info "[3/7] backbone=static-iiasa; skipping adapter (predecessor's static files used directly via Option A)."
fi

# =============================================================================
# Step 4: Bootstrap LPJG_main/IMOGEN/ handshake dir (per step 9 finding)
# =============================================================================
# In v1.0 single-process mode, the IMOGEN engine's polling loop (step 7's
# restored bug C2/C3 fixes) requires imogen_lpjg.txt + done to exist before
# the engine's first iteration. LPJG can't supply them yet because LPJG's
# main loop hasn't started (init() hasn't returned). So we pre-populate
# these as bootstrap files. After F-12 multi-pass design, this becomes
# unnecessary (the orchestrator will manage handshake state).
_info "[4/7] Bootstrapping LPJG_main/IMOGEN/ handshake dir..."
HSHAKE_DIR="${RUN_DIR}/Common-directory/LPJG_main/IMOGEN"
mkdir -p "${HSHAKE_DIR}"
if [ ! -f "${HSHAKE_DIR}/imogen_lpjg.txt" ]; then
  cat > "${HSHAKE_DIR}/imogen_lpjg.txt" <<EOF
YEAR1 1871 !IN First year of the numerical experiment
IYEND 1872 !IN Stop year of the ENTIRE run
YEAR1_LPJG 1871 !IN First year of the whole LPJ-GUESS simulation
SPINUP FALSE !IN Are we in the spin-up phase of LPJ-GUESS?
KEEPRUNNING TRUE !IN control flag to keep imogen running
FIRSTCALL TRUE !IN Is this the very first call to IMOGEN from LPJ-GUESS
EOF
fi
if [ ! -f "${HSHAKE_DIR}/done" ]; then
  echo "bootstrap" > "${HSHAKE_DIR}/done"
fi
_ok "[4/7] Bootstrap files: ${HSHAKE_DIR}/{imogen_lpjg.txt, done}"

# =============================================================================
# Step 5: Clean stale per-year IMOGEN engine output (always; idempotent re-run)
# =============================================================================
_info "[5/7] Cleaning stale per-year IMOGEN engine output dirs..."
rm -rf "${RUN_DIR}/Common-directory/IMOGEN/output" 2>/dev/null || true
_ok "[5/7] Stale outputs cleared."

# =============================================================================
# Step 6: Launch LPJ-GUESS in coupled mode
# =============================================================================
_info "[6/7] Launching LPJ-GUESS coupled run (-input imogencfx)..."
cd "${RUN_DIR}"
"${GUESS_BIN}" -input imogencfx main.ins 2>&1 | tee -a "${LOG_FILE}" || {
  EC=$?
  _warn "guess exit code: ${EC} (this is EXPECTED in v1.0 due to F-10 architectural deadlock)"
  _warn "  The engine reaches a polling loop on the year-N+1 handshake that LPJG can't supply."
  _warn "  Engine outputs at Common-directory/IMOGEN/output/<YYYY>/ are still produced."
  _warn "  See notes/STEP_9.md sec 4.4 for full diagnosis."
}

# =============================================================================
# Step 7: Collect summary
# =============================================================================
_info "[7/7] Run summary:"
echo "  Engine year-output dirs produced:" | tee -a "${LOG_FILE}"
ls -d "${RUN_DIR}/Common-directory/IMOGEN/output"/*/ 2>/dev/null | wc -l | xargs -I{} echo "    count: {}" | tee -a "${LOG_FILE}"
ls "${RUN_DIR}/Common-directory/IMOGEN/output"/ 2>/dev/null | sort -n | head -5 | xargs -I{} echo "    first: {}" | tee -a "${LOG_FILE}"
ls "${RUN_DIR}/Common-directory/IMOGEN/output"/ 2>/dev/null | sort -n | tail -3 | xargs -I{} echo "    last:  {}" | tee -a "${LOG_FILE}"

echo "  LPJG handshake files (step 8 writer output; only if F-12 implemented):"  | tee -a "${LOG_FILE}"
for f in imogen_lpjg_flux.txt imogen_lpjg_ch4_n2o_flux.txt; do
  if [ -f "${HSHAKE_DIR}/${f}" ]; then
    LINES=$(wc -l < "${HSHAKE_DIR}/${f}")
    BYTES=$(wc -c < "${HSHAKE_DIR}/${f}")
    if [ "${LINES}" -gt 1 ]; then
      _ok "    ${f}: ${LINES} lines, ${BYTES} bytes (LPJG main loop fired!)" | tee -a "${LOG_FILE}"
    else
      echo "    ${f}: not yet written (F-10 deadlock; expected in v1.0)" | tee -a "${LOG_FILE}"
    fi
  fi
done

echo
echo "================================================================================"
_ok "Coupled run launcher finished."
echo "  Full log: ${LOG_FILE}"
echo "  Engine output: ${RUN_DIR}/Common-directory/IMOGEN/output/"
echo "  LPJG output:   ${RUN_DIR}/output/  (only populated when LPJG main loop runs; F-12-gated in v1.0)"
echo "================================================================================"
