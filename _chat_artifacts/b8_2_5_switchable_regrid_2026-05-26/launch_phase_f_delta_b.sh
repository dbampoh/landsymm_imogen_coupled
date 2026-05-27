#!/usr/bin/env bash
# Block 8.2.5 Phase F δ-B pipeline launcher (hist → scen sequential)
# Authored: session 12 day 2 2026-05-27
set -uo pipefail
ROOT="/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm"
LDIR="$ROOT/_chat_artifacts/b8_2_5_switchable_regrid_2026-05-26"
PIPELINE="delta_b"

# --- HIST phase ---
HIST_DIR="$ROOT/forks/trunk_r13078_runs/SSP1-2.6_b825_smoke_${PIPELINE}_hist"
HIST_LOG="$LDIR/phase_f_${PIPELINE}_hist.log"
{
  echo "================================================================================"
  echo "Phase F δ-B HIST phase"
  echo "Start: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "Dir: $HIST_DIR"
  echo "================================================================================"
} > "$HIST_LOG"
cd "$HIST_DIR" || { echo "[ERROR] cd to HIST dir failed" >> "$HIST_LOG"; exit 1; }
./guess -input imogencfx main.ins >> "$HIST_LOG" 2>&1
HIST_RC=$?
{
  echo "================================================================================"
  echo "HIST phase exit_code=$HIST_RC at $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "================================================================================"
} >> "$HIST_LOG"
if [ "$HIST_RC" != "0" ]; then
  echo "[ABORT] δ-B HIST failed (rc=$HIST_RC); skipping SCEN" >> "$HIST_LOG"
  exit "$HIST_RC"
fi

# --- SCEN phase (only if HIST succeeded) ---
SCEN_DIR="$ROOT/forks/trunk_r13078_runs/SSP1-2.6_b825_smoke_${PIPELINE}_scen"
SCEN_LOG="$LDIR/phase_f_${PIPELINE}_scen.log"
{
  echo "================================================================================"
  echo "Phase F δ-B SCEN phase (restart from HIST saved state)"
  echo "Start: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "Dir: $SCEN_DIR"
  echo "================================================================================"
} > "$SCEN_LOG"
cd "$SCEN_DIR" || { echo "[ERROR] cd to SCEN dir failed" >> "$SCEN_LOG"; exit 1; }
./guess -input imogencfx main.ins >> "$SCEN_LOG" 2>&1
SCEN_RC=$?
{
  echo "================================================================================"
  echo "SCEN phase exit_code=$SCEN_RC at $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "================================================================================"
} >> "$SCEN_LOG"
exit "$SCEN_RC"
