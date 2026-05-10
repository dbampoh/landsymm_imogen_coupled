#!/bin/bash
# =============================================================================
# scripts/cross_validate_year_outer.sh
# =============================================================================
#
# F-12 sub-milestone C1 cross-validation harness.
#
# Runs LPJ-GUESS twice (Run A: gridcell_outer; Run B: year_outer) with
# byte-identical inputs (same .ins / gridlist / pre-staged climate /
# random seeds), then diffs the .out files for bit-exact comparison.
#
# GO/NO-GO gate for F-12 sub-milestone C1: bit-exact cross-validation
# of all outputs (per notes/STEP_17a.md §7.2 + §7.3 + §7.3.2; see also
# notes/FOLLOWUPS.md F-12).
#
# Usage: scripts/cross_validate_year_outer.sh [1cell|4cell] [imogen|imogencfx]
#   gridlist variant (1st arg; default 1cell):
#     1cell : single-cell smoke (gridlist_test1.txt; 1 cell) —
#             bypasses spinup_year_idx cell-ordering complexity. RUN FIRST.
#     4cell : multi-cell smoke (gridlist_test2.txt; 4 cells) —
#             tests spinup_year_idx state-machine reproduction formula.
#   input module (2nd arg; default imogen):
#     imogen    : LOOSE-coupling input module (ImogenInput; C1.1+C1.2 path).
#                 Uses runs/SSP1-2.6/main_xval_loose.ins as base .ins.
#     imogencfx : TIGHT-coupling input module (IMOGENCFXInput; C1.3 sub-step
#                 7.3.2 path). Uses runs/SSP1-2.6/main_xval_imogencfx.ins
#                 as base .ins. Requires skip_inprocess_engine_run=1 (set
#                 in main_xval_imogencfx.ins) to bypass F-10 deadlock at
#                 IMOGENCFXInput::init()'s RUN_IMOGEN_ENGINE() call.
#
# Pre-requisites:
#   1. Pre-staged engine climate at runs/SSP1-2.6/Common-directory/
#      IMOGEN/output/{1871..1902}/ (32 year-dirs; ALL with 13 files each
#      post-C1.3 sub-step 7.3.1 climate writer fix at commit 7be595a).
#      If absent, run:
#         timeout --foreground 300 ./scripts/run_coupled.sh --no-build &
#         (then `pkill -9 -x guess` after ~3-5 min when launcher
#          deadlocks at year ~33 per F-10)
#   2. lpjguess/build/guess binary built (per scripts/run_coupled.sh).
#   3. data/gridlist/gridlist_test{1,2}.txt exist.
#   4. For imogencfx variant: runs/SSP1-2.6/main_xval_imogencfx.ins exists
#      (created at C1.3 sub-step 7.3.2 setup; sets skip_inprocess_engine_run=1).
#
# - Daniel Bampoh, 2026-05-10 (step 17a C1 of unified-codebase rebuild;
#   imogencfx 2nd-arg variant added at C1.3 sub-step 7.3.2)
# =============================================================================

set -u
# (intentionally NOT set -e + NOT set -o pipefail: we WANT to keep going
#  past non-zero per-run exit codes + tolerate SIGPIPE from `head` etc.
#  so we can report comparison outcomes cleanly.)

GRIDLIST_VARIANT="${1:-1cell}"  # 1cell or 4cell
INPUT_MODULE="${2:-imogen}"     # imogen or imogencfx

case "$GRIDLIST_VARIANT" in
  1cell) GRIDLIST_NAME="gridlist_test1.txt" ;;
  4cell) GRIDLIST_NAME="gridlist_test2.txt" ;;
  *)
    echo "Usage: $0 [1cell|4cell] [imogen|imogencfx]" >&2
    echo "  Got unrecognized 1st argument: $GRIDLIST_VARIANT" >&2
    exit 1
    ;;
esac

case "$INPUT_MODULE" in
  imogen)    INS_BASENAME="main_xval_loose.ins" ;;
  imogencfx) INS_BASENAME="main_xval_imogencfx.ins" ;;
  *)
    echo "Usage: $0 [1cell|4cell] [imogen|imogencfx]" >&2
    echo "  Got unrecognized 2nd argument: $INPUT_MODULE" >&2
    exit 1
    ;;
esac

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_DIR="$ROOT/runs/SSP1-2.6"
COMMON_DIR="$RUN_DIR/Common-directory"
GUESS_BIN="$ROOT/lpjguess/build/guess"
GRIDLIST="$ROOT/data/gridlist/$GRIDLIST_NAME"
BASE_INS="$RUN_DIR/$INS_BASENAME"

# Per-run output dirs (under Common-directory so climate paths resolve);
# include input-module suffix for imogencfx variant (no conflict with imogen runs).
XVAL_BASE="$COMMON_DIR/xval_runs"
if [ "$INPUT_MODULE" = "imogen" ]; then
  RUN_A_DIR="$XVAL_BASE/${GRIDLIST_VARIANT}_run_A_gridcell_outer"
  RUN_B_DIR="$XVAL_BASE/${GRIDLIST_VARIANT}_run_B_year_outer"
else
  RUN_A_DIR="$XVAL_BASE/${GRIDLIST_VARIANT}_${INPUT_MODULE}_run_A_gridcell_outer"
  RUN_B_DIR="$XVAL_BASE/${GRIDLIST_VARIANT}_${INPUT_MODULE}_run_B_year_outer"
fi

# -----------------------------------------------------------------------------
# Sanity checks
# -----------------------------------------------------------------------------
[ -x "$GUESS_BIN" ] || { echo "ERROR: guess binary not found: $GUESS_BIN" >&2; exit 1; }
[ -f "$GRIDLIST" ]  || { echo "ERROR: gridlist not found: $GRIDLIST" >&2; exit 1; }
[ -f "$BASE_INS" ]  || { echo "ERROR: base .ins not found: $BASE_INS" >&2; exit 1; }
[ -d "$COMMON_DIR/IMOGEN/output/1871" ] || {
  echo "ERROR: pre-staged climate missing: $COMMON_DIR/IMOGEN/output/1871/" >&2
  echo "  Run: timeout --foreground 300 $ROOT/scripts/run_coupled.sh --no-build" >&2
  echo "  (then wait for ~3-5 min for the engine to produce 32 year-dirs)" >&2
  exit 1
}

# -----------------------------------------------------------------------------
# Function: write_wrapper_ins <output-dir> <framework_loop_mode>
# -----------------------------------------------------------------------------
write_wrapper_ins() {
  local out_dir="$1"
  local mode="$2"
  local wrapper="$out_dir/xval_wrapper.ins"

  mkdir -p "$out_dir"
  cat > "$wrapper" <<EOF
!///////////////////////////////////////////////////////////////////////////////////////
! Auto-generated wrapper .ins for cross-validation Run with
! framework_loop_mode = "${mode}" + gridlist = ${GRIDLIST_NAME}.
! Generated by scripts/cross_validate_year_outer.sh at \$(date).
!///////////////////////////////////////////////////////////////////////////////////////

! Import the base loose-mode .ins (sets all the standard params)
import "$BASE_INS"

! Overrides for this run
param "file_gridlist"     (str "$GRIDLIST")
param "file_gridlist_cf"  (str "$GRIDLIST")
param "framework_loop_mode" (str "$mode")

! Output directory: outputs go to this run dir
outputdirectory "$out_dir/"
EOF
  echo "$wrapper"
}

# -----------------------------------------------------------------------------
# Function: run_one <output-dir> <framework_loop_mode> <run-name>
# -----------------------------------------------------------------------------
run_one() {
  local out_dir="$1"
  local mode="$2"
  local run_name="$3"

  echo "================================================================================"
  echo "Running $run_name : framework_loop_mode = \"$mode\" : gridlist = $GRIDLIST_NAME"
  echo "  Output dir: $out_dir"
  echo "================================================================================"

  # Clean prior outputs
  rm -rf "$out_dir"
  mkdir -p "$out_dir"

  # Write wrapper
  local wrapper
  wrapper="$(write_wrapper_ins "$out_dir" "$mode")"

  # Run from Common-directory so file_temp paths resolve to staged climate
  cd "$COMMON_DIR"
  echo "[run_one] cwd: $(pwd)"
  echo "[run_one] cmd: $GUESS_BIN -input $INPUT_MODULE $wrapper"
  echo "[run_one] log: $out_dir/run.log"
  echo

  # Run + capture output (don't fail on non-zero in case of partial failure)
  set +e
  "$GUESS_BIN" -input "$INPUT_MODULE" "$wrapper" > "$out_dir/run.log" 2>&1
  local rc=$?
  set -e

  echo "[run_one] $run_name exit code: $rc"
  local n_out
  n_out=$(ls "$out_dir"/*.out 2>/dev/null | wc -l)
  echo "[run_one] $run_name produced $n_out .out files"
  echo
  return $rc
}

# -----------------------------------------------------------------------------
# Function: compare_outputs
# -----------------------------------------------------------------------------
compare_outputs() {
  echo "================================================================================"
  echo "Comparing Run A (gridcell_outer) vs Run B (year_outer) outputs"
  echo "================================================================================"

  local n_a n_b
  n_a=$(ls "$RUN_A_DIR"/*.out 2>/dev/null | wc -l)
  n_b=$(ls "$RUN_B_DIR"/*.out 2>/dev/null | wc -l)
  echo "Run A: $n_a .out files"
  echo "Run B: $n_b .out files"

  if [ "$n_a" -eq 0 ] || [ "$n_b" -eq 0 ]; then
    echo "ERROR: One or both runs produced ZERO .out files. See run.log files."
    return 1
  fi

  if [ "$n_a" -ne "$n_b" ]; then
    echo "WARNING: file count mismatch ($n_a vs $n_b)"
  fi

  echo
  echo "Per-file diff results:"
  local total=0
  local matches=0
  local mismatches=0
  for fa in "$RUN_A_DIR"/*.out; do
    local base
    base=$(basename "$fa")
    local fb="$RUN_B_DIR/$base"
    total=$((total + 1))
    if [ ! -f "$fb" ]; then
      echo "  $base : MISSING in Run B"
      mismatches=$((mismatches + 1))
      continue
    fi
    if cmp -s "$fa" "$fb"; then
      echo "  $base : ✓ bit-exact"
      matches=$((matches + 1))
    else
      local lines_diff
      lines_diff=$(diff "$fa" "$fb" | wc -l)
      echo "  $base : ✗ DIFFERS ($lines_diff diff lines)"
      mismatches=$((mismatches + 1))
    fi
  done

  echo
  echo "================================================================================"
  echo "SUMMARY: $matches/$total bit-exact matches; $mismatches mismatches"
  echo "================================================================================"

  if [ "$mismatches" -eq 0 ] && [ "$total" -gt 0 ]; then
    echo "PASS: All .out files are bit-exact between Run A and Run B."
    return 0
  else
    echo "FAIL: $mismatches files differ. Investigate divergences."
    return 2
  fi
}

# -----------------------------------------------------------------------------
# Main flow
# -----------------------------------------------------------------------------
echo "================================================================================"
echo "F-12 sub-milestone C1 CROSS-VALIDATION"
echo "  Gridlist variant : $GRIDLIST_VARIANT (gridlist: $GRIDLIST_NAME)"
echo "  Input module     : $INPUT_MODULE (.ins: $INS_BASENAME)"
echo "================================================================================"
echo

# Run A: gridcell_outer (existing trusted baseline)
run_one "$RUN_A_DIR" "gridcell_outer" "Run A"

# Run B: year_outer (new additive code path; C1.1)
run_one "$RUN_B_DIR" "year_outer"     "Run B"

# Compare
compare_outputs
exit $?
