#!/usr/bin/env bash
# =============================================================================
# setup_run_tseq.sh — Track 2 T_seq cluster launcher (per-cluster-dir wrapper)
# =============================================================================
#
# Block 8.4 pre-cluster prep (session 12 day 2 2026-05-27; per user's Track-1
# wpeat hist+ssp126_wpeat reference at
# /media/bampoh-d/landsymm_imogen_runs_cluster_mirror_2026-05-21/).
#
# This wrapper is COPY-cp'd into each of the 10 cluster run-dirs:
#   forks/trunk_r13078_runs/SSP{1-2.6, 2-4.5, 3-7.0, 4-6.0, 5-8.5}_cluster_{hist, scen}/
#
# The operator workflow (mirroring the user's established Track-1 pattern):
#
#   ┌─────────────────────────────────────────────────────────────────────┐
#   │ 1. cd forks/trunk_r13078_runs/<SSP>_cluster_<phase>/                │
#   │ 2. (HIST phase only; SCEN phase reads state from existing dir)      │
#   │    The state/ subdir already exists in <SSP>_cluster_hist/          │
#   │ 3. ./setup_run_tseq.sh                                              │
#   │    → invokes scripts/cluster/setup_run.sh with named-flag args     │
#   │    → splits gridlist into nnodes × cpu_per_node ranks               │
#   │    → cp .ins to per-rank dirs at $WORK_BASE                         │
#   │    → generates submit.sh + startguess.sh                            │
#   │ 4. cd $WORK_BASE/<dir-name>/                                        │
#   │ 5. bash startguess.sh                                               │
#   │    → sbatch submit.sh (256-rank parallel job)                       │
#   │    → afterok dependency: sbatch finishup_lpj_work.sh                │
#   │      (concat per-rank .out + md5sum + gzip + cp to dated output)    │
#   │ 6. After HIST completes: state files at:                            │
#   │    /bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm/forks/           │
#   │      trunk_r13078_runs/<SSP>_cluster_hist/state/                    │
#   │    SCEN phase reads from this state_path (configured in main.ins)   │
#   └─────────────────────────────────────────────────────────────────────┘
#
# Key Track-2 deltas vs your Track-1 wpeat reference:
#   - inputmethod: imogencfx (vs cfx for Track 1)
#   - binary: forks/trunk_r13078/build_owl/guess (trunk-T_seq LPJG; block 8.2.4
#     engine-side fork-parity)
#   - climate: pre-baked δ-B-variant 62892 library (cluster-side after rsync)
#   - state_path: absolute cluster path in main.ins (vs Track-1 local state/
#     subdir of run-dir)
#
# Allocation: 2 nodes × 128 CPUs = 256 ranks on owl genius/256 × 3-hour walltime
# (matches your established wpeat production allocation per block 8.1
# reconnaissance D2 + sacct evidence).
#
# Override env vars if needed:
#   NNODES, CPU_PER_NODE, PARTITION, WALLTIME, WORKDIR_BASE
#
# Cross-references:
#   - scripts/cluster/setup_run.sh    (the workhorse; named-flag CLI)
#   - scripts/cluster/run_coupled.sbatch  (alternative unified launcher)
#   - notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md §1 (block 8.4 pre-cluster prep)
#   - _chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_evaluation_2026-05-27.md
# =============================================================================

set -euo pipefail

# Repo root resolution (3 dirs up from this run-dir: forks/trunk_r13078_runs/<SSP>_cluster_<phase>/)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

# Per-cluster-dir auto-detection
RUNNAME="$(basename "$(pwd)")"
SCENARIO_DIR="$(pwd)"

# Allocation defaults (override via env)
NNODES="${NNODES:-2}"
CPU_PER_NODE="${CPU_PER_NODE:-128}"
PARTITION="${PARTITION:-genius}"
WALLTIME="${WALLTIME:-03:00:00}"
APPEND_PARTITION="${APPEND_PARTITION:-${PARTITION}}"
APPEND_NTASKS="${APPEND_NTASKS:-8}"

# Track-2 T_seq specifics
INPUTMETHOD="imogencfx"
BINARY="${REPO_ROOT}/forks/trunk_r13078/build_owl/guess"
# GRIDLIST defaults to production 62538-cell gridlist; override via env for smoke
# (e.g., `GRIDLIST=$REPO_ROOT/data/gridlist/gridlist_b830_cluster_smoke_1024cells_seed42.txt ./setup_run_tseq.sh`)
# Rule #9 #34 fix at block 8.3 cluster smoke prep 2026-05-28: env-overridable per Track-1
# muscle memory + cluster-citizenship smoke-vs-production decoupling.
GRIDLIST="${GRIDLIST:-${REPO_ROOT}/data/gridlist/gridlist_in_62892_and_climate.txt}"
EXTRA_INSFILES="crop.ins crop_n.ins global.ins global_soiln.ins landcover.ins crop_n_pftlist.simplePFT.remap10_g2p.ins crop_n_stlist.simplePFT.remap10_g2p.N0-60-200-1000.ins crop_n_stlist.simplePFT.remap10_g2p.agreed_treatments.ins wetlandpfts.ins imogen_intermediary.ins pasture_n_stlist.ins pasture_n_stlist_agreed_treatments.ins global_coupled_imogen_lpjg.ins"

# Pre-flight sanity
[ -f "${BINARY}" ]   || { echo "ERROR: trunk T_seq binary not found: ${BINARY}"; echo "  Build first: cd ${REPO_ROOT}/forks/trunk_r13078 && mkdir -p build_owl && cd build_owl && cmake -DCMAKE_BUILD_TYPE=Release .. && make -j\$(nproc)"; exit 1; }
[ -f "${GRIDLIST}" ] || { echo "ERROR: production gridlist not found: ${GRIDLIST}"; exit 1; }
[ -f main.ins ]      || { echo "ERROR: main.ins not in current dir; cd to a <SSP>_cluster_<phase>/ run-dir first"; exit 1; }

# state/ subdir sanity check (must exist for hist; must exist for scen too since restart reads from it)
case "${RUNNAME}" in
  *_hist) STATE_DIR="$(pwd)/state"; [ -d "${STATE_DIR}" ] || { echo "ERROR: state/ subdir missing in ${RUNNAME}; create with: mkdir -p state"; exit 1; } ;;
  *_scen) HIST_STATE_DIR="${REPO_ROOT}/forks/trunk_r13078_runs/${RUNNAME%_scen}_hist/state"; [ -d "${HIST_STATE_DIR}" ] || { echo "ERROR: hist state dir missing: ${HIST_STATE_DIR}; run hist phase first"; exit 1; } ;;
esac

echo "================================================================================"
echo "Block 8.4 Track 2 T_seq cluster launcher"
echo "  Run-dir:         ${SCENARIO_DIR}"
echo "  Runname:         ${RUNNAME}"
echo "  Inputmethod:     ${INPUTMETHOD}"
echo "  Binary:          ${BINARY}"
echo "  Gridlist:        ${GRIDLIST} ($(wc -l < ${GRIDLIST}) cells)"
echo "  Allocation:      ${NNODES} nodes × ${CPU_PER_NODE} CPUs = $((NNODES * CPU_PER_NODE)) ranks"
echo "  Partition:       ${PARTITION}"
echo "  Walltime:        ${WALLTIME}"
echo "  Workdir base:    ${WORKDIR_BASE:-<default per setup_run.sh>}"
echo "================================================================================"

exec "${REPO_ROOT}/scripts/cluster/setup_run.sh" \
  --runname "${RUNNAME}" \
  --maininsfile main.ins \
  --extra-insfiles "${EXTRA_INSFILES}" \
  --gridlist "${GRIDLIST}" \
  --inputmethod "${INPUTMETHOD}" \
  --nnodes "${NNODES}" \
  --cpu-per-node "${CPU_PER_NODE}" \
  --partition "${PARTITION}" \
  --walltime "${WALLTIME}" \
  --binary "${BINARY}" \
  --scenario-dir "${SCENARIO_DIR}" \
  --append-partition "${APPEND_PARTITION}" \
  --append-ntasks "${APPEND_NTASKS}" \
  ${WORKDIR_BASE:+--workdir-base "${WORKDIR_BASE}"}
