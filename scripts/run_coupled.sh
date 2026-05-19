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
#                         (1900-1901; was 1871-1872 pre-B34(β) addendum 2026-05-18),
#                         nyear_spinup=100, 1 patch. Default for development.
#                         Already configured in main.ins + imogen_intermediary.ins
#                         as v1.0. The 1900-1901 window is in-range for both
#                         --backbone static-iiasa (1850-2100 CMIP6 ref files) and
#                         --backbone intermediary-py (1900-2100 adapter outputs).
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
#   --engine-only-mode    Productisation of the path-iv launcher-side `done`-marker
#                         sidecar mechanism empirically confirmed at B37 DR1
#                         (2026-05-19 evening session 7; per notes/B37.md sec 5 +
#                         notes/B44.md). When set, spawns a background bash
#                         sidecar that touches <HSHAKE_DIR>/done every 1 second
#                         BEFORE invoking ./guess, so the IMOGEN engine's
#                         per-iter polling loop (climatemodel.cpp:347-401) sees
#                         the `done` marker on every cycle and progresses through
#                         all years without waiting for an LPJG `done` write that
#                         the F-10 case-α deadlock prevents (LPJG main loop never
#                         runs because imogencfx::init() inline-calls
#                         RUN_IMOGEN_ENGINE which never returns until engine
#                         exits). The sidecar PID is captured + cleaned up via
#                         trap-on-EXIT on any exit path (normal/error/signal/
#                         timeout). Engine produces ~200-202 year-dirs for a
#                         YEAR1=1900/IYEND=2100 production-IMOGEN run (DR1
#                         empirically demonstrated 202 year-dirs 1900-2101 in
#                         12 min 48 sec wall on smoke 4-cell; ~3.78 sec/year
#                         scaling; ~63 min total local for all 5 SSP-RCPs);
#                         engine exits 99 on the YEAR1=2100 over-shoot (per the
#                         brittle YEAR1==2100 hardcoded KEEPRUNNING=false +
#                         YEAR1_LPJG=1871 hardcoded reset at
#                         climatemodel.cpp:1189-1197; B45 NEW filed for v1.1+
#                         source-edit cleanup). REQUIRES --coupling-mode
#                         prescribed (the only mode where this mechanism makes
#                         sense; loose bypasses LPJG handshake at the input
#                         module not the engine; tight remains F-10-deadlocked).
#                         When set, the launcher's exit-99 messaging context-
#                         switches to "engine-only-mode terminal" instead of
#                         "F-10 deadlock workaround". Per notes/B44.md +
#                         notes/B37.md sec 5 (B44 NEW filed at B37 close).
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
ENGINE_ONLY_MODE=0
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
    --engine-only-mode) ENGINE_ONLY_MODE=1; shift ;;
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

# [B44 NEW 2026-05-19 evening session 7 continuation: --engine-only-mode flag
#  validation. The flag productises the path-iv launcher-side `done`-marker
#  sidecar mechanism empirically confirmed at B37 DR1 (per notes/B37.md sec 5).
#  Required combination is `--coupling-mode prescribed`: (a) `loose` bypasses
#  LPJG handshake at the input-module layer (imogenoutput.cpp:269-274 + 473-478
#  early-return when mode=='loose'), not at the engine layer — so the sidecar
#  is unnecessary; (b) `tight` is the F-10-deadlocked mode the sidecar is
#  designed to work around, but in v1.0 tight-mode-with-sidecar produces
#  identical behavior to prescribed-mode-with-sidecar because LPJG main loop
#  never runs in either case (per imogencfx::init inline RUN_IMOGEN_ENGINE
#  call). prescribed is the canonical v1.0 production-IMOGEN mode per the
#  v1.0 paper-publication architecture decision (B43; F-12 deferred to v1.1+).
#  Reject other combinations with explicit error.]
if [ "${ENGINE_ONLY_MODE}" = "1" ]; then
  case "$COUPLING_MODE" in
    prescribed) ;;
    *) _err "--engine-only-mode requires --coupling-mode prescribed; got '$COUPLING_MODE'."
       _err "  Rationale: --engine-only-mode productises the path-iv launcher-side done-marker sidecar"
       _err "  per B37 DR1. It only makes sense with prescribed mode (the v1.0 paper-publication"
       _err "  default). loose bypasses LPJG handshake at input-module not engine; tight is the"
       _err "  F-10-deadlocked mode the sidecar works around (but tight = prescribed in v1.0 since"
       _err "  LPJG main loop never runs either way). See notes/B44.md + notes/B37.md sec 5."
       exit 2 ;;
  esac
fi

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
# [B31 sub-item (b) 2026-05-16: explicit NATURAL flux source banner so launcher
#  output unambiguously reports the active LPJ-GUESS<->IMOGEN handshake config.
#  The source is determined deterministically from (COUPLING_MODE, BACKBONE) and
#  the auto-rewrite at step 4.5 below makes the .ins file consistent with this.
#  See notes/B19.md §3.4.2.4 + COUPLED_MODEL_INVESTIGATION.md §2.3+§3.7. -DKB]
case "${COUPLING_MODE}-${BACKBONE}" in
  prescribed-static-iiasa)   NATURAL_LABEL="static CMIP6 natural reference (Option A; v1.0 default)" ;;
  prescribed-intermediary-py)NATURAL_LABEL="intermediary_py-derived (Option B; adapter outputs from runs/${SCENARIO}/inputs/)" ;;
  tight-static-iiasa)        NATURAL_LABEL="LIVE LPJG handshake (Option C; F-10 deadlock applies in v1.0 single-process)" ;;
  tight-intermediary-py)     NATURAL_LABEL="LIVE LPJG handshake (Option C; F-10 deadlock applies in v1.0 single-process)" ;;
  loose-*)                   NATURAL_LABEL="loose-mode static climate library (handshake bypassed entirely)" ;;
  *)                         NATURAL_LABEL="(unrecognized; check --coupling-mode + --backbone)" ;;
esac
echo "  NATURAL flux source: ${NATURAL_LABEL}"
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
  if [ "$BACKBONE" = "intermediary-py" ]; then
    _info "[2/7] backbone=intermediary-py + --no-intermediary; skipping intermediary_py end-to-end run (assuming ${PY_OUT_CSV} already exists)."
  else
    _info "[2/7] backbone=${BACKBONE} (predecessor's reference files); skipping intermediary_py."
  fi
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
  if [ "$BACKBONE" = "intermediary-py" ]; then
    _info "[3/7] backbone=intermediary-py + --no-adapter; skipping adapter (assuming ${RUN_DIR}/inputs/{co2,ch4_n2o}_*.txt already populated)."
  else
    _info "[3/7] backbone=${BACKBONE}; skipping adapter (predecessor's static files used directly via Option A)."
  fi
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
#
# [B19 Phase 2 / B31 sub-item (c) 2026-05-16: bootstrap now ALWAYS-OVERWRITES
#  (was: only-if-absent), and SPINUP is computed dynamically to match the
#  climatemodel.cpp:1181-1199 state-machine semantics that the d9c90d5 Phase 0
#  fix wired into the per-iteration writer at imogenoutput.cpp:399-401.
#  Before this fix the bootstrap hardcoded SPINUP=FALSE, which (a) disagreed
#  with the d9c90d5 dynamic semantics for any YEAR1<1901, and (b) could never
#  be auto-corrected on re-run because of the if-not-exist guard. Now: bootstrap
#  is always re-written; SPINUP follows the state machine. For smoke v1.0
#  configs (YEAR1=1900 post-B34(β) addendum 2026-05-18; was 1871) this means
#  SPINUP=TRUE on first iteration (1900<1901 still triggers the spinup branch).
#  v1.1 audit: make YEAR1_BOOT / IYEND_BOOT parameterizable from .ins
#  (today they are kept synchronized manually with imogen_intermediary.ins
#  YEAR1/IYEND). -DKB]
_info "[4/7] Bootstrapping LPJG_main/IMOGEN/ handshake dir..."
HSHAKE_DIR="${RUN_DIR}/Common-directory/LPJG_main/IMOGEN"
mkdir -p "${HSHAKE_DIR}"

# [B19 Phase 3 addendum 2026-05-18 B34(β): smoke years shifted 1871-1872 → 1900-1901
#  to support --backbone intermediary-py (whose adapter outputs cover 1900-2100 only).
#  These MUST stay in sync with runs/<SSP>/imogen_intermediary.ins YEAR1/IYEND and
#  runs/<SSP>/main.ins firsthistyear/lasthistyear.]
YEAR1_BOOT=1900
IYEND_BOOT=1901
if [ "${YEAR1_BOOT}" -lt 1901 ]; then SPINUP_BOOT="TRUE"; else SPINUP_BOOT="FALSE"; fi
if [ "${IYEND_BOOT}" -gt 1900 ]; then FIRSTCALL_BOOT="FALSE"; else FIRSTCALL_BOOT="TRUE"; fi
# Bootstrap == "this is the very first call from LPJG"; FIRSTCALL_BOOT is TRUE
# by definition regardless of IYEND-derived state-machine semantics that apply
# starting on iteration 2. Per imogen_lpjg.f:447-448, the Fortran engine reads
# FIRSTCALL on every iteration; the d9c90d5 writer sets the per-iteration value
# from IMOGENConfig::FIRSTCALL which is initialised TRUE and flipped FALSE at
# climatemodel.cpp:1193 after IYEND>1900. So the bootstrap FIRSTCALL=TRUE is
# correct seed for iteration 1; iteration 2+ gets per-iteration values from
# the LPJG-side step-8 writer.
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
_ok "[4/7] Bootstrap files written: ${HSHAKE_DIR}/{imogen_lpjg.txt, done} (SPINUP=${SPINUP_BOOT}, FIRSTCALL=${FIRSTCALL_BOOT}, KEEPRUNNING=TRUE)"

# =============================================================================
# Step 4.5: Auto-rewrite imogen_intermediary.ins per (COUPLING_MODE, BACKBONE)
# =============================================================================
# [B19 Phase 2 / B31 sub-items (a)+(b) + B33 sub-item (b) 2026-05-16:
#  surfaced by user-driven double-counting investigation at Phase 1 CLOSE
#  (notes/B19.md §3.4.2). The .ins file has 3 NATURAL-flux Option blocks
#  (A=static CMIP6 ref, B=intermediary_py-derived adapter outputs, C=relative
#  paths for LIVE LPJG handshake) + 2 ANTHRO-emission Option blocks (A=DKB
#  reference files, B=intermediary_py-derived adapter outputs). Pre-B31 the
#  launcher accepted --coupling-mode + --backbone flags but did NOT rewrite
#  the .ins to match -- user had to manually un-comment the correct block.
#  Silent mis-config risk: user could think they're running intermediary-py
#  but IMOGEN still reads Option-A CMIP6 reference.
#
#  Also wraps B33 sub-item (b) pre-flight: if coupling_mode "tight" is set
#  but FILE_LPJG_FLUX uses an absolute path, abort with explicit error.
#
#  Strategy: content-based sed toggles (NOT line-number-based). Each parameter
#  line is uniquely identifiable by its distinctive path content. Backup of
#  .ins written to logs/ for audit + manual revert. Idempotent: re-running
#  with same flags produces same .ins (no-op detected via diff vs current).
#
#  Cross-refs: notes/B19.md §3.4.2.4 (B31+B32+B33 audit-item descriptions),
#  COUPLED_MODEL_INVESTIGATION.md §2.3 + §3.7 (no-double-counting + POSIX
#  footgun), runs/SSP1-2.6/imogen_intermediary.ins lines 156-201. -DKB]

_info "[4.5] Auto-rewrite imogen_intermediary.ins per (coupling_mode=${COUPLING_MODE}, backbone=${BACKBONE})..."

INS_FILE="${RUN_DIR}/imogen_intermediary.ins"
if [ ! -f "${INS_FILE}" ]; then
  _err "Cannot auto-rewrite: ${INS_FILE} not found."
  exit 1
fi

INS_BAK="${LOG_DIR}/$(basename "${INS_FILE}").bak.$(date '+%Y%m%d_%H%M%S')"
cp "${INS_FILE}" "${INS_BAK}"

# Determine target Option codes for NATURAL flux + ANTHRO emissions per (mode,backbone).
# NATURAL_TARGET: A|B|C|SKIP   ANTHRO_TARGET: A|B|SKIP
case "${COUPLING_MODE}-${BACKBONE}" in
  prescribed-static-iiasa)    NATURAL_TARGET="A"; ANTHRO_TARGET="A" ;;
  prescribed-intermediary-py) NATURAL_TARGET="B"; ANTHRO_TARGET="B" ;;
  tight-static-iiasa)         NATURAL_TARGET="C"; ANTHRO_TARGET="A" ;;
  tight-intermediary-py)      NATURAL_TARGET="C"; ANTHRO_TARGET="B" ;;
  loose-*)                    NATURAL_TARGET="SKIP"; ANTHRO_TARGET="SKIP" ;;
  *)                          _err "Unrecognized (mode,backbone) tuple: (${COUPLING_MODE}, ${BACKBONE})"; exit 2 ;;
esac

if [ "${NATURAL_TARGET}" = "SKIP" ]; then
  _info "  loose mode: skipping .ins auto-rewrite (loose bypasses LPJG handshake entirely)"
else
  # toggle_ins_line FILE REGEX active|commented
  # NB: patterns contain '/' (path separators), so we use '#' as the sed address
  # delimiter via the POSIX \Xpattern\X form. None of our patterns contain '#'.
  toggle_ins_line() {
    local f="$1" pat="$2" want="$3"
    if [ "${want}" = "active" ]; then
      sed -i -E "\\#${pat}# { s/^!+[[:space:]]*// }" "${f}"
    else
      sed -i -E "\\#${pat}# { /^[[:space:]]*!/!s/^/!/ }" "${f}"
    fi
  }

  # NATURAL Option A: CMIP6 static reference natural fluxes (distinctive content)
  toggle_ins_line "${INS_FILE}" 'FILE_LPJG_FLUX.*co2_pg_emissions_natural'         $( [ "${NATURAL_TARGET}" = "A" ] && echo active || echo commented )
  toggle_ins_line "${INS_FILE}" 'FILE_LPJG_CH4_N2O_FLUX.*ch4_n2o_annual_historical_natural' $( [ "${NATURAL_TARGET}" = "A" ] && echo active || echo commented )

  # NATURAL Option B: intermediary_py-derived adapter outputs (distinctive runs/<SSP>/inputs/imogen_lpjg_*.txt)
  toggle_ins_line "${INS_FILE}" 'FILE_LPJG_FLUX.*runs/[^/]+/inputs/imogen_lpjg_flux\.txt' $( [ "${NATURAL_TARGET}" = "B" ] && echo active || echo commented )
  toggle_ins_line "${INS_FILE}" 'FILE_LPJG_CH4_N2O_FLUX.*runs/[^/]+/inputs/imogen_lpjg_ch4_n2o_flux\.txt' $( [ "${NATURAL_TARGET}" = "B" ] && echo active || echo commented )

  # NATURAL Option C: relative paths -> LIVE LPJG handshake (short bare filename, no /)
  toggle_ins_line "${INS_FILE}" 'FILE_LPJG_FLUX[[:space:]]+"imogen_lpjg_flux\.txt"'         $( [ "${NATURAL_TARGET}" = "C" ] && echo active || echo commented )
  toggle_ins_line "${INS_FILE}" 'FILE_LPJG_CH4_N2O_FLUX[[:space:]]+"imogen_lpjg_ch4_n2o_flux\.txt"' $( [ "${NATURAL_TARGET}" = "C" ] && echo active || echo commented )

  # ANTHRO Option A: DKB_dataset_totals defaults (relative paths; NEVER abs-path footgun for anthro)
  toggle_ins_line "${INS_FILE}" 'FILE_SCEN_EMITS.*DKB_dataset_totals/co2_emissions_annual_historical' $( [ "${ANTHRO_TARGET}" = "A" ] && echo active || echo commented )
  toggle_ins_line "${INS_FILE}" 'FILE_CH4_N2O_EMITS.*DKB_dataset_totals/ch4_n2o_annual_historical'   $( [ "${ANTHRO_TARGET}" = "A" ] && echo active || echo commented )

  # ANTHRO Option B: intermediary_py-derived adapter outputs
  toggle_ins_line "${INS_FILE}" 'FILE_SCEN_EMITS.*runs/[^/]+/inputs/co2_anthro_emissions\.txt'        $( [ "${ANTHRO_TARGET}" = "B" ] && echo active || echo commented )
  toggle_ins_line "${INS_FILE}" 'FILE_CH4_N2O_EMITS.*runs/[^/]+/inputs/ch4_n2o_anthro_emissions\.txt' $( [ "${ANTHRO_TARGET}" = "B" ] && echo active || echo commented )

  # Also sync the engine-side coupling_mode line itself to match the launcher arg.
  sed -i -E "s/^coupling_mode[[:space:]]+\"[a-z]+\"/coupling_mode       \"${COUPLING_MODE}\"/" "${INS_FILE}"

  # ---------------------------------------------------------------------------
  # [B19 Phase 3 addendum 2026-05-18 / B34(β)]: BACKBONE-determined NYR_*
  # auto-rewrite (extension of the FILE_* auto-rewrite logic above).
  #
  # The Fortran/C++ engine's per-year emissTally validation at climatemodel.cpp
  # :741-756 (and imogen_lpjg.f:825-836) loops 0..NYR_EMISS-1 looking for a
  # year-column match against IYEAR. If NYR_EMISS exceeds the file's actual row
  # count, the read overflows past EOF; if NYR_EMISS is too small, IYEAR may
  # not be in range and emissTally=0 → "Emission dataset does not match run"
  # crash. Each backbone has a fixed dataset year-span and row count:
  #   - static-iiasa  : 1850-2100 = 251 rows for {NATURAL CO2, NATURAL CH4/N2O,
  #                     ANTHRO CH4/N2O}; ANTHRO CO2 is 252 rows incl. dup-tail
  #                     (engine reads first 251 — verified empirically Run B).
  #   - intermediary-py: 1900-2100 = 201 rows for all 4 adapter outputs.
  # NYR_NON_CO2 stays 251 always (FILE_NON_CO2_VALS = the 1850-2100 CMIP6 RF
  # file, regardless of backbone).
  #
  # Pre-B34(β) (i.e., the Phase 3 Run A 2026-05-17 attempt with
  # --backbone intermediary-py): the NYR_* values stayed at the 251 default
  # while the FILE_* paths flipped to Option B → engine read 251 rows from a
  # 201-row file → emissTally=0 for IYEAR=1871 → crash. B34(β) addresses both
  # axes (smoke window + NYR_*) at this commit.
  #
  # Cross-refs: notes/B19.md §5.4.2 (B34 closure record); notes/FOLLOWUPS.md
  # B34 entry; runs/<SSP>/imogen_intermediary.ins lines 167-189 (Option B
  # docblock); engine source at climatemodel.cpp:741-756. -DKB
  # ---------------------------------------------------------------------------
  case "${BACKBONE}" in
    static-iiasa)    NYR_EMISS_VAL=251; NYR_EMISS_NONCO2_VAL=251; NYR_LPJG_FLUX_VAL=251 ;;
    intermediary-py) NYR_EMISS_VAL=201; NYR_EMISS_NONCO2_VAL=201; NYR_LPJG_FLUX_VAL=201 ;;
    *)               _err "Unrecognized BACKBONE for NYR_* rewrite: '${BACKBONE}'"; exit 2 ;;
  esac

  # Use leading-anchor + at-least-one-space form so the existing column padding
  # in the .ins is preserved roughly; the trailing comment is also rewritten so
  # it keeps documenting the active backbone deterministically per-run.
  sed -i -E "s|^NYR_EMISS_NONCO2[[:space:]]+[0-9]+([[:space:]].*)?$|NYR_EMISS_NONCO2 ${NYR_EMISS_NONCO2_VAL}    ! Anthropogenic CH4+N2O emissions span; backbone=${BACKBONE} (auto-rewritten by run_coupled.sh step 4.5)|" "${INS_FILE}"
  sed -i -E "s|^NYR_EMISS[[:space:]]+[0-9]+([[:space:]].*)?$|NYR_EMISS       ${NYR_EMISS_VAL}     ! Anthropogenic CO2 emissions span; backbone=${BACKBONE} (auto-rewritten by run_coupled.sh step 4.5)|" "${INS_FILE}"
  sed -i -E "s|^NYR_LPJG_FLUX[[:space:]]+[0-9]+([[:space:]].*)?$|NYR_LPJG_FLUX   ${NYR_LPJG_FLUX_VAL}     ! LPJG flux file span; backbone=${BACKBONE} (auto-rewritten by run_coupled.sh step 4.5)|" "${INS_FILE}"
  # NYR_NON_CO2 deliberately NOT auto-rewritten — it's always 251 per the CMIP6 RF file.

  # Verify exactly 1 active NYR_EMISS + NYR_EMISS_NONCO2 + NYR_LPJG_FLUX line at the rewritten value
  for triple in "NYR_EMISS:${NYR_EMISS_VAL}" "NYR_EMISS_NONCO2:${NYR_EMISS_NONCO2_VAL}" "NYR_LPJG_FLUX:${NYR_LPJG_FLUX_VAL}"; do
    pname="${triple%:*}"; pval="${triple#*:}"
    n=$(grep -cE "^${pname}[[:space:]]+${pval}([[:space:]]|$)" "${INS_FILE}" || true)
    if [ "${n}" -ne 1 ]; then
      _err "B34(β) NYR_* post-rewrite verification FAILED: expected 1 active '${pname} ${pval}' line; got ${n}"
      _err "  Backup at ${INS_BAK}; revert via: cp '${INS_BAK}' '${INS_FILE}'"
      exit 1
    fi
  done

  # Verify exactly 1 active FILE_LPJG_FLUX + 1 active FILE_LPJG_CH4_N2O_FLUX + 1 active FILE_SCEN_EMITS + 1 active FILE_CH4_N2O_EMITS
  for p in FILE_LPJG_FLUX FILE_LPJG_CH4_N2O_FLUX FILE_SCEN_EMITS FILE_CH4_N2O_EMITS; do
    n=$(grep -cE "^${p}[[:space:]]+" "${INS_FILE}" || true)
    if [ "${n}" -ne 1 ]; then
      _err "Post-rewrite verification FAILED: expected 1 active ${p} line; got ${n}"
      _err "  Backup at ${INS_BAK}; revert via: cp '${INS_BAK}' '${INS_FILE}'"
      exit 1
    fi
  done

  # B33 sub-item (b) pre-flight: in tight mode, FILE_LPJG_FLUX must NOT be absolute
  # (the engine's path-concat at imogen_lpjg.f:619-620 collapses absolute paths
  # and bypasses the LPJG live handshake -- "loose-masquerading-as-tight" footgun
  # per COUPLED_MODEL_INVESTIGATION.md §3.7).
  if [ "${COUPLING_MODE}" = "tight" ]; then
    abs_flux=$(grep -E "^FILE_LPJG_FLUX[[:space:]]+\"/" "${INS_FILE}" || true)
    abs_ch4n2o=$(grep -E "^FILE_LPJG_CH4_N2O_FLUX[[:space:]]+\"/" "${INS_FILE}" || true)
    if [ -n "${abs_flux}" ] || [ -n "${abs_ch4n2o}" ]; then
      _err "B33 pre-flight FAILED: coupling_mode tight set but FILE_LPJG_FLUX/FILE_LPJG_CH4_N2O_FLUX use absolute path."
      _err "  Absolute paths collapse via POSIX path-concat (imogen_lpjg.f:619-620) and bypass the LPJG live handshake."
      _err "  Tight mode REQUIRES relative filenames (Option C: e.g. \"imogen_lpjg_flux.txt\")."
      _err "  See COUPLED_MODEL_INVESTIGATION.md §3.7 for the full footgun forensic."
      _err "  Backup at ${INS_BAK}; revert via: cp '${INS_BAK}' '${INS_FILE}'"
      exit 1
    fi
  fi

  _ok "  Rewrote ${INS_FILE} for NATURAL=Option-${NATURAL_TARGET} + ANTHRO=Option-${ANTHRO_TARGET}; coupling_mode synced to \"${COUPLING_MODE}\"; NYR_*={EMISS:${NYR_EMISS_VAL}, EMISS_NONCO2:${NYR_EMISS_NONCO2_VAL}, LPJG_FLUX:${NYR_LPJG_FLUX_VAL}} per backbone=${BACKBONE} (B34(β) launcher-managed)."
  _ok "  Backup at ${INS_BAK}; idempotent re-run safe."
fi

# =============================================================================
# Step 5: Clean stale per-year IMOGEN engine output (always; idempotent re-run)
# =============================================================================
_info "[5/7] Cleaning stale per-year IMOGEN engine output dirs..."
rm -rf "${RUN_DIR}/Common-directory/IMOGEN/output" 2>/dev/null || true
_ok "[5/7] Stale outputs cleared."

# =============================================================================
# Step 6: Launch LPJ-GUESS in coupled mode
# =============================================================================
# [B44 NEW 2026-05-19 evening session 7 continuation: --engine-only-mode flag
#  productises the path-iv launcher-side `done`-marker sidecar mechanism per
#  notes/B37.md sec 5 + notes/B44.md. When ENGINE_ONLY_MODE=1, spawn a
#  background bash sidecar that touches <HSHAKE>/done every 1 second BEFORE
#  invoking ./guess; trap-on-EXIT cleans up the sidecar PID on any exit path
#  (normal/error/signal/timeout). The engine's per-iter polling loop at
#  climatemodel.cpp:347-401 sees the `done` marker on every cycle (engine
#  sleeps 3s between polls; sidecar touches every 1s so the file mostly
#  exists; engine deletes done at line 578 after consuming flux files; sidecar
#  re-creates within 1s). Engine progresses through all years until
#  YEAR1==2100 hardcoded KEEPRUNNING=false at climatemodel.cpp:1189-1190, then
#  over-shoots by 1 iter (engine tries year 2101 outside NYR_EMISS=201; falls
#  back to ./IMOGEN/output/1871/T_anom.dat per the brittle YEAR1_LPJG=1871
#  hardcoded reset at climatemodel.cpp:1197; exits 99). For YEAR1=1900/IYEND=
#  2100 production-IMOGEN runs, this produces ~200-202 year-dirs (1900-2099/
#  2100/2101 with the over-shoot empty placeholder). Empirically validated
#  at B37 DR1 (2026-05-19; ~12.6 min wall on smoke 4-cell; ~3.78 sec/year
#  scaling; ~63 min total local for all 5 SSP-RCPs). B45 NEW filed for v1.1+
#  source-edit cleanup of the brittle year sentinels.]
SIDECAR_PID=""
cleanup_sidecar() {
  if [ -n "${SIDECAR_PID}" ]; then
    kill "${SIDECAR_PID}" 2>/dev/null || true
    wait "${SIDECAR_PID}" 2>/dev/null || true
    SIDECAR_PID=""
  fi
}
trap cleanup_sidecar EXIT

if [ "${ENGINE_ONLY_MODE}" = "1" ]; then
  _info "[6a/7] --engine-only-mode active: spawning path-iv done-marker sidecar (touches ${HSHAKE_DIR}/done every 1s)..."
  ( while true; do touch "${HSHAKE_DIR}/done" 2>/dev/null; sleep 1; done ) &
  SIDECAR_PID=$!
  _ok "[6a/7] Sidecar PID=${SIDECAR_PID} (cleaned up via trap-on-EXIT on any exit path)."
fi

_info "[6/7] Launching LPJ-GUESS coupled run (-input imogencfx)..."
cd "${RUN_DIR}"
"${GUESS_BIN}" -input imogencfx main.ins 2>&1 | tee -a "${LOG_FILE}" || {
  EC=$?
  if [ "${ENGINE_ONLY_MODE}" = "1" ]; then
    _warn "guess exit code: ${EC} (this is EXPECTED in --engine-only-mode v1.0 due to engine over-shoot at YEAR1==2100 hardcoded boundary)"
    _warn "  The engine ran through to the YEAR1==2100 KEEPRUNNING=false trigger at"
    _warn "  climatemodel.cpp:1189-1190, then over-shot by 1 iter trying year 2101"
    _warn "  (outside NYR_EMISS=201) and fell back to ./IMOGEN/output/1871/T_anom.dat"
    _warn "  per the brittle YEAR1_LPJG=1871 hardcoded reset at climatemodel.cpp:1197."
    _warn "  Engine outputs at Common-directory/IMOGEN/output/<YYYY>/ are produced for"
    _warn "  ALL years 1900-2100 + 1 over-shoot empty placeholder (2101; ignorable)."
    _warn "  See notes/B37.md sec 2 + notes/B44.md for the path-iv sidecar mechanism;"
    _warn "  B45 NEW filed for v1.1+ source-edit cleanup of the brittle year sentinels."
  else
    _warn "guess exit code: ${EC} (this is EXPECTED in v1.0 due to F-10 architectural deadlock)"
    _warn "  The engine reaches a polling loop on the year-N+1 handshake that LPJG can't supply."
    _warn "  Engine outputs at Common-directory/IMOGEN/output/<YYYY>/ are still produced"
    _warn "  for the productive-year-ceiling window per the closed-form formula at"
    _warn "  notes/B37.md sec 2.3 (4 years for YEAR1=1900; 32 years for YEAR1=1871; etc.)."
    _warn "  See notes/STEP_9.md sec 4.4 + notes/B37.md for full diagnosis."
    _warn "  TIP: pass --engine-only-mode to enable the path-iv sidecar that produces"
    _warn "  all ~200 years 1900-2100 for production-IMOGEN runs without F-12 fix."
  fi
}

# Clean up sidecar promptly (the trap-on-EXIT is the safety net; this call
# is the happy-path cleanup so the rest of the launcher's step 7 runs without
# the background process touching files).
cleanup_sidecar

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
