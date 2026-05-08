#!/bin/bash
# =============================================================================
# scripts/cluster/run_coupled.sbatch — SLURM cluster wrapper for the LandSyMM-
# IMOGEN coupled launcher (HPC variant of scripts/run_coupled.sh).
# =============================================================================
#
# v1.0 SCOPE: LOOSE-coupling end-to-end on cluster. TIGHT (closed-loop) on
# cluster requires F-12 Option C (additive `framework_loop_mode = "year_outer"`
# + MPI_Barrier at year boundary; per `docs/v2_roadmap.md` §5 + `notes/
# FOLLOWUPS.md` F-10 phase-2 sketch). v1.0 cluster-tight runs are blocked;
# the script will print a hard warning and refuse to proceed for tight mode.
#
# This wrapper:
#   [1] Sources cluster module loads (default scripts/cluster/env_owl.sh)
#   [2] Optionally rebuilds LPJ-GUESS with MPI enabled (build_mpi/)
#   [3] Optionally runs intermediary_py + adapter on the head node
#   [4] Stages the run dir at $WORK_BASE via setup_run.sh (per-rank gridlist
#       split into runNN/ subdirs)
#   [5] Generates an SBATCH-compatible submit script + startguess.sh
#   [6] sbatch's the job + a follow-up dependency-chained finishup_lpj_work.sh
#       that aggregates per-rank outputs back to the original run dir.
#
# USAGE
# -----
#     sbatch scripts/cluster/run_coupled.sbatch [opts]
#   OR
#     scripts/cluster/run_coupled.sbatch [opts]   (calls sbatch internally)
#
# OPTIONS (mirrors scripts/run_coupled.sh)
#   --scenario SSP        Scenario directory under runs/ (default: SSP1-2.6)
#   --coupling-mode MODE  loose (v1.0 default & only mode that actually works
#                                end-to-end on cluster) |
#                         prescribed | tight (BLOCKED in v1.0; F-12 Option C
#                         needed; gives a hard error and refuses to proceed)
#   --backbone WHICH      static-iiasa | intermediary-py (default: static-iiasa)
#   --smoke               4-cell + 1871-1872 (default; ~minutes)
#   --production          62892-cell + 1900-2100 (~hours per scenario)
#   --no-build            Skip step 2 (use existing build_mpi/guess)
#   --no-intermediary     Skip step 3 (use existing intermediary_py outputs)
#   --no-adapter          Skip step 4 (use existing runs/<SSP>/inputs/)
#   --partition NAME      SLURM partition (default: $RUN_PARTITION env or auto)
#   --nodes N             Number of nodes (default: 2)
#   --cpu-per-node N      Cores per node (default: 16; small for smoke; bump
#                         to e.g. 80 for production)
#   --append-partition NAME    SLURM partition for append/finishup (default:
#                              same as --partition)
#   --append-ntasks N     Tasks for append job (default: 8)
#   --walltime HH:MM:SS   Max wall time (default: 03:00:00)
#   --module-env FILE     Path to module-load script (default:
#                         scripts/cluster/env_owl.sh)
#   -h, --help            Show this and exit
#
# EXAMPLES
#   sbatch scripts/cluster/run_coupled.sbatch                      # smoke; loose; static-iiasa; SSP1-2.6
#   sbatch scripts/cluster/run_coupled.sbatch --production --nodes 4 --cpu-per-node 80
#   scripts/cluster/run_coupled.sbatch --coupling-mode tight       # ERROR: blocked in v1.0
#
# DECISIONS (per EXECUTION_PLAN.md II)
# ------------------------------------
# - Decision #7: single codebase + binary serves both workstation and cluster.
#   Cluster build path: lpjguess/build_mpi/guess (MPI-enabled).
# - Decision #8: cluster's module-loaded NetCDF/HDF5/openmpi is preferred over
#   Anaconda3 (the workstation default) — cluster has IT-managed ABI-consistent
#   software stack. See scripts/cluster/env_owl.sh for the module-load specifics.
#
# F-10 / F-12 CAVEATS
# -------------------
# v1.0 cluster + tight is BLOCKED:
#   - The framework loop is per-gridcell-outer / per-day-inner-across-all-years
#     (framework.cpp:411-516). On cluster, gridlist is split across ranks via
#     setup_run.sh's `split -a 4 -l <cells/N>`. Each rank processes ALL years
#     for ITS subset of cells INDEPENDENTLY; there's no MPI_Barrier at year
#     boundaries (parallel.cpp implements only MPI_Init/Comm_rank/Comm_size).
#   - Step 8's ImogenOutput::flush_year writer fires per-rank-per-year as each
#     rank reaches its cells' year-end; the engine cannot consume N independent
#     flux streams at a synchronization point. Same deadlock pattern as
#     single-process F-10 (see notes/STEP_9.md §4.4 + notes/FOLLOWUPS.md F-10
#     for the empirical confirmation), now multiplied by N ranks.
#   - Resolution: F-12 Option C — additive `framework_loop_mode = "year_outer"`
#     ins parameter that adds a per-year-outer / per-gridcell-inner loop with
#     MPI_Barrier at year boundary, leveraging existing per-rank gridlist
#     subsetting. Estimated 1-2 weeks + cross-validation. See
#     `docs/v2_roadmap.md` §5 for the concrete sketch.
#
# REFERENCES
# ----------
# - EXECUTION_PLAN.md V.1 step 16
# - scripts/run_coupled.sh (the workstation analogue)
# - scripts/cluster/setup_run.sh (gridlist-split + per-rank runNN/ generation)
# - scripts/cluster/mpi_run_guess.sh (per-rank scratch I/O wrapper)
# - scripts/cluster/finishup_lpj_work.sh (post-run aggregation)
# - scripts/cluster/env_owl.sh (cluster module loads; placeholder values
#                               to be refined via SSH session)
# - notes/FOLLOWUPS.md F-10 (phase-2 sketch; cluster-MPI implications);
#                        F-12 (multi-pass / two-process design)
# - docs/v2_roadmap.md §4 (F-12 Option B, single-process tight) + §5 (F-12
#                          Option C, in-process restructure for cluster-tight)
#
# AUTHOR
# ------
# Daniel Bampoh, 2026-05-08 (step 16 of unified-codebase rebuild)
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Cluster-script SLURM directives (only honoured when invoked via `sbatch`;
# ignored when sourced directly). The runtime --partition / --nodes / etc.
# from CLI flags below override these.
# -----------------------------------------------------------------------------
#SBATCH --job-name=landsymm_imogen
#SBATCH --output=logs/landsymm_imogen_%j.out
#SBATCH --error=logs/landsymm_imogen_%j.err
#SBATCH --time=03:00:00
#SBATCH --nodes=2

# -----------------------------------------------------------------------------
# Color / message helpers (mirrors scripts/run_coupled.sh)
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

trap '_err "SLURM-cluster launcher aborted at line $LINENO (exit $?)."' ERR

# -----------------------------------------------------------------------------
# Parse args
# -----------------------------------------------------------------------------
SCENARIO="SSP1-2.6"
COUPLING_MODE="loose"
BACKBONE="static-iiasa"
RUN_MODE="smoke"
DO_BUILD=1
DO_INTERMEDIARY=1
DO_ADAPTER=1
RUN_PARTITION="${RUN_PARTITION:-}"  # default empty; user must specify or env-set
NNODES=2
CPU_PER_NODE=16
APPEND_PARTITION=""
APPEND_NTASKS=8
WALLTIME="03:00:00"
MODULE_ENV="scripts/cluster/env_owl.sh"

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
    --partition)        RUN_PARTITION="$2"; shift 2 ;;
    --nodes)            NNODES="$2"; shift 2 ;;
    --cpu-per-node)     CPU_PER_NODE="$2"; shift 2 ;;
    --append-partition) APPEND_PARTITION="$2"; shift 2 ;;
    --append-ntasks)    APPEND_NTASKS="$2"; shift 2 ;;
    --walltime)         WALLTIME="$2"; shift 2 ;;
    --module-env)       MODULE_ENV="$2"; shift 2 ;;
    -h|--help)
      awk '/^# =+$/{n++; if (n==2) exit} n>=1' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      _err "Unknown argument: $1"
      exit 1
      ;;
  esac
done

[[ -z "${APPEND_PARTITION}" ]] && APPEND_PARTITION="${RUN_PARTITION}"

# -----------------------------------------------------------------------------
# Validate args
# -----------------------------------------------------------------------------
case "${COUPLING_MODE}" in
  loose|prescribed|tight) : ;;
  *) _err "--coupling-mode must be one of: loose | prescribed | tight (got '${COUPLING_MODE}')"; exit 1 ;;
esac

case "${BACKBONE}" in
  static-iiasa|intermediary-py) : ;;
  *) _err "--backbone must be one of: static-iiasa | intermediary-py (got '${BACKBONE}')"; exit 1 ;;
esac

# -----------------------------------------------------------------------------
# F-10 / F-12 BLOCKING CHECK — refuse to proceed for cluster + tight in v1.0
# -----------------------------------------------------------------------------
if [[ "${COUPLING_MODE}" == "tight" ]]; then
  _err "Cluster + tight coupling is BLOCKED in v1.0."
  _err "  Reason: F-10 architectural deadlock (single-process) extends to MPI"
  _err "  multi-rank because the framework loop has no MPI_Barrier at year"
  _err "  boundaries (lpjguess/framework/parallel.cpp implements only"
  _err "  MPI_Init/Comm_rank/Comm_size; per-gridcell-outer / per-day-inner"
  _err "  loop in framework.cpp:411-516 is incompatible with synchronized"
  _err "  per-year handshake)."
  _err "  Resolution: F-12 Option C (additive framework_loop_mode = "
  _err '              "year_outer" + MPI_Barrier at year boundary). See'
  _err "              docs/v2_roadmap.md §5 for the concrete plan."
  _err "  Alternatives:"
  _err "    --coupling-mode loose      (v1.0 functional cluster default; LPJG"
  _err "                                reads pre-baked engine climate from disk)"
  _err "    --coupling-mode prescribed (engine reads static-IIASA emissions;"
  _err "                                32-year-then-deadlock pattern even on"
  _err "                                cluster; same F-10 issue, just"
  _err "                                multiplied by N ranks)"
  exit 1
fi

if [[ "${COUPLING_MODE}" == "prescribed" ]]; then
  _warn "Cluster + prescribed runs into the same per-rank synchronization gap"
  _warn "as cluster + tight. Engine will produce ~32 years per rank then"
  _warn "deadlock. Recommended for v1.0 cluster runs: --coupling-mode loose"
fi

if [[ -z "${RUN_PARTITION}" ]]; then
  _err "No SLURM partition specified. Set --partition (or RUN_PARTITION env)."
  _err "  Example: --partition cclake (KIT IMK-IFU owl) or --partition <name>"
  exit 1
fi

# -----------------------------------------------------------------------------
# Resolve repository root + working directory
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCENARIO_DIR="${REPO_ROOT}/runs/${SCENARIO}"

if [[ ! -d "${SCENARIO_DIR}" ]]; then
  _err "Scenario directory does not exist: ${SCENARIO_DIR}"
  _err "  Available scenarios: $(ls "${REPO_ROOT}/runs/" 2>/dev/null | tr '\n' ' ')"
  exit 1
fi

# -----------------------------------------------------------------------------
# [1] Source cluster module-load environment
# -----------------------------------------------------------------------------
_info "[1/6] Sourcing cluster module-load environment from ${MODULE_ENV}"
if [[ -f "${REPO_ROOT}/${MODULE_ENV}" ]]; then
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/${MODULE_ENV}"
  _ok "Module loads sourced."
else
  _warn "Module-env file not found at ${MODULE_ENV}; proceeding with current shell environment."
  _warn "Refine ${MODULE_ENV} via cluster SSH session before production runs."
fi

# -----------------------------------------------------------------------------
# [2] Build LPJ-GUESS with MPI (cluster-side)
# -----------------------------------------------------------------------------
if [[ "${DO_BUILD}" -eq 1 ]]; then
  _info "[2/6] Building LPJ-GUESS with MPI enabled (build_mpi/)"
  bash "${SCRIPT_DIR}/make_guess.sh" --mpi
  _ok "LPJ-GUESS MPI build complete."
else
  _info "[2/6] --no-build; skipping LPJ-GUESS rebuild."
fi

# -----------------------------------------------------------------------------
# [3-4] Run intermediary_py + adapter on head node (if intermediary-py backbone)
# -----------------------------------------------------------------------------
if [[ "${BACKBONE}" == "intermediary-py" ]]; then
  if [[ "${DO_INTERMEDIARY}" -eq 1 ]]; then
    _info "[3/6] Running intermediary_py on head node"
    (cd "${REPO_ROOT}/intermediary_py/imogen_ghg_controller" && python3 run_all.py --skip-plots)
    _ok "intermediary_py complete."
  else
    _info "[3/6] --no-intermediary; skipping."
  fi
  if [[ "${DO_ADAPTER}" -eq 1 ]]; then
    _info "[4/6] Running Python -> LPJG-format adapter"
    python3 "${REPO_ROOT}/tools/imogen_inputs_to_lpjg_format.py" \
      --input  "${REPO_ROOT}/intermediary_py/imogen_ghg_controller/outputs/imogen_inputs/imogen_inputs_${SCENARIO}.csv" \
      --output "${SCENARIO_DIR}/inputs/"
    _ok "Adapter complete."
  else
    _info "[4/6] --no-adapter; skipping."
  fi
else
  _info "[3/6] backbone=static-iiasa; skipping intermediary_py."
  _info "[4/6] backbone=static-iiasa; skipping adapter."
fi

# -----------------------------------------------------------------------------
# Banner per §I.D.5 (mirrors scripts/run_coupled.sh)
# -----------------------------------------------------------------------------
cat <<EOF

LandSyMM-IMOGEN-LPJG cluster run launcher (HPC; step 16)

  Scenario        : ${SCENARIO}
  Coupling mode   : ${COUPLING_MODE}    (v1.0: loose works end-to-end on cluster; prescribed/tight gated on F-12 Option C)
  Backbone        : ${BACKBONE}
  Run mode        : ${RUN_MODE}
  Partition       : ${RUN_PARTITION}
  Nodes           : ${NNODES}
  Cores per node  : ${CPU_PER_NODE}
  Total tasks     : $((NNODES * CPU_PER_NODE))
  Walltime        : ${WALLTIME}

  Active conventions (per EXECUTION_PLAN.md sec I.D.5):
    NEE / NBP        : positive = source to atmosphere
    CO2 emissions    : Mt CO2/yr (Intermediary) -> PgC/yr (IMOGEN), via /3666.6667
    CH4 / N2O        : Tg-of-gas/yr; 1 Mt = 1 Tg by mass identity
    Year indexing    : LPJG year N flux drives IMOGEN year N+1 climate (IYEAR-1 lookup)
    Cell area        : Earth radius 6371 km; 0.5 deg x 0.5 deg grid; spherical

EOF

# -----------------------------------------------------------------------------
# [5] Stage run dir + gridlist split via setup_run.sh
# -----------------------------------------------------------------------------
_info "[5/6] Staging run dir + gridlist split"

# Map --coupling-mode to LPJ-GUESS input module
case "${COUPLING_MODE}" in
  loose)      INPUT_MODULE="imogen" ;;
  prescribed) INPUT_MODULE="imogencfx" ;;
  tight)      INPUT_MODULE="imogencfx" ;;  # un-reachable; refused above
esac

NPROCESS=$((NNODES * CPU_PER_NODE))
GRIDLIST_FILE_REL="../../data/gridlist/gridlist_test2.txt"
[[ "${RUN_MODE}" == "production" ]] && GRIDLIST_FILE_REL="../../data/gridlist/gridlist_in_62892_and_climate.txt"

bash "${SCRIPT_DIR}/setup_run.sh" \
  --runname "$(basename "${SCENARIO_DIR}")" \
  --maininsfile "main.ins" \
  --extra-insfiles "imogen_intermediary.ins global.ins crop_n.ins landcover.ins wetlandpfts.ins" \
  --gridlist "${SCENARIO_DIR}/${GRIDLIST_FILE_REL}" \
  --inputmethod "${INPUT_MODULE}" \
  --nnodes "${NNODES}" \
  --cpu-per-node "${CPU_PER_NODE}" \
  --partition "${RUN_PARTITION}" \
  --append-partition "${APPEND_PARTITION}" \
  --append-ntasks "${APPEND_NTASKS}" \
  --walltime "${WALLTIME}" \
  --binary "${REPO_ROOT}/lpjguess/build_mpi/guess" \
  --scenario-dir "${SCENARIO_DIR}"

_ok "Run dir staged at scenario_dir; submit.sh + startguess.sh generated."

# -----------------------------------------------------------------------------
# [6] Submit job + dependency-chained finishup_lpj_work.sh
# -----------------------------------------------------------------------------
_info "[6/6] Submitting SLURM job + dependent finishup"

# Submit-side workflow expected by setup_run.sh:
#  - cd to scenario_dir
#  - run startguess.sh (which sbatches submit.sh + dependent finishup_lpj_work.sh)
cd "${SCENARIO_DIR}"
_info "Run startguess.sh manually:"
_info "  cd ${SCENARIO_DIR}"
_info "  bash startguess.sh"
_info ""
_info "Or invoke directly here (if --no-dry-run added in future):"
# bash "${SCENARIO_DIR}/startguess.sh"

_ok "Cluster launcher complete (job submission staged; not auto-submitted yet)."
_info "After submission, monitor via squeue -u \$USER + tail -f \${SCENARIO_DIR}/run1/guess.log"
