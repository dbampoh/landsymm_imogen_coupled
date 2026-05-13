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
# GUESS_BIN env var overrides the default build/guess path. Useful for
# running xval against build_mpi/guess (step 17b C2 verification: confirm
# the MPI build still passes the 4 xval scenarios in single-process mode
# before MPI_Barrier + flush_year_globally_synchronized code lands).
# Default (unset): build/guess (the C1-baseline build). - DKB 2026-05-11
GUESS_BIN="${GUESS_BIN:-$ROOT/lpjguess/build/guess}"
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

! Overrides for this run.
!
! [B15 FIX 2026-05-12 (session 3): plib supports TWO disjoint param mechanisms:
!   (1) Native plib  "key value"  bare syntax  -> directly mutates a C++
!       variable bound at module init via declare_parameter("key", &var, ...).
!       This is what framework.cpp:464's gate
!         if (IMOGENConfig::framework_loop_mode == "year_outer")
!       reads. So framework_loop_mode MUST be set with bare syntax.
!
!   (2) Plib SET-block  param "key" (str "value")  -> appends/overrides an
!       entry in the global Paramlist dictionary 'param', read via
!       param["key"].str (e.g. parameters.cpp:991 + 1506-1514 + 1858-1862).
!       Some parameters (file_gridlist, file_gridlist_cf, firsthistyear etc.)
!       are read ONLY through this Paramlist dictionary and MUST therefore
!       be set with param-syntax.
!
! These mechanisms target DIFFERENT storage and do NOT cross-update.
! Pre-B15, the wrapper used  param "framework_loop_mode" (str "...")  which
! silently wrote only to Paramlist["framework_loop_mode"].str — an entry
! NOTHING in the codebase reads. IMOGENConfig::framework_loop_mode stayed
! at its declare-side default "gridcell_outer" (parameters.cpp:288), so the
! framework.cpp:464 gate evaluated false and the year_outer block NEVER
! executed in any C1/C2 cross-validation Run B. All "bit-exact" passes were
! gridcell_outer == gridcell_outer identity matches. See notes/STEP_17c.md
! §0 (audit item B15) for full forensic.]
param "file_gridlist"     (str "$GRIDLIST")
param "file_gridlist_cf"  (str "$GRIDLIST")
framework_loop_mode "$mode"

! Output directory: outputs go to this run dir.
! [outputdirectory is declare_parameter-bound (outputmodule.cpp:38) so it
!  uses bare syntax — same mechanism class as framework_loop_mode above.]
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
  echo "RAW BYTE-EQUALITY SUMMARY: $matches/$total bit-exact matches; $mismatches mismatches"
  echo "================================================================================"

  # =============================================================================
  # [Step 17c (F-12 sub-milestone C3 PREP sub-phase 17c.0.4) — B17(a) FIX
  #  (landed 2026-05-13 evening, session 4): SORT-THEN-DIFF NORMALIZATION
  #  layer added.
  #
  # Added because B17(a) (row-emission-order divergence) is a STRUCTURAL
  # property of the year_outer loop, NOT a defect:
  #   - gridcell_outer emits .out rows in CELL-MAJOR order
  #     (cell 0 yr0..N, cell 1 yr0..N, ..., cell M yr0..N) because its
  #     loop is `for cell { for year { outannual } }`
  #     (framework.cpp::736-817).
  #   - year_outer    emits .out rows in YEAR-MAJOR order
  #     (yr0 cell0..M, yr1 cell0..M, ..., yrN cell0..M) because its
  #     loop is `for year { for cell { outannual } }`
  #     (framework.cpp::588-628).
  # Both modes call output_modules.outannual(gridcell) per (cell, year)
  # tuple at end-of-year; emission ORDER == loop ORDER. The two modes
  # produce IDENTICAL data rows but in different sequences. Raw cmp -s
  # therefore reports MISMATCH on EVERY multi-cell xval scenario even
  # when the underlying data is identical (which it is for the 5
  # "PURE B17(a)" files in our 4cell envelope: npool, mch4, mch4_
  # diffusion, mch4_ebullition, mch4_plant).
  #
  # The fix sorts each file's BODY (lines 2..N) by (Lon, Lat, Year) using
  # LC_ALL=C numeric sort -k1,1n -k2,2n -k3,3n. This matches the natural
  # ordering of both modes' output and is IDEMPOTENT on already-sorted
  # input. Per-LC summed files and 1cell scenarios already pass raw cmp -s
  # and skip the sort-then-diff entirely.
  #
  # File classification produced by this block (printed per-file +
  # summarized after the loop):
  #   BIT_EXACT     - raw cmp -s succeeded (identical bytes; no sort needed)
  #   SORTED_EXACT  - raw differs but sorted-cmp -s succeeds (PURE B17(a);
  #                   pure row-ordering divergence; counted toward effective
  #                   PASS for the substantive-validation gate)
  #   SORTED_DIFFER - raw differs AND sorted-cmp -s differs (B17(a) + B17(b);
  #                   confirmed numerical drift on top of row-ordering;
  #                   counted toward controlled-FAIL; B17(b) provisionally
  #                   accepted at 2% per notes/STEP_17c.md §3.8.5 + §3 + §3.6)
  #
  # PASS/FAIL semantics (updated): the substantive-validation gate now
  # passes when BIT_EXACT + SORTED_EXACT == total (zero SORTED_DIFFER).
  # FAIL exit 2 when SORTED_DIFFER > 0. This is a SEMANTIC interpretation
  # of Decision-12 byte-equality (equality of CONTENT, not of emission
  # order), which is the architecturally correct interpretation given
  # year_outer's loop-restructure mandate. The strict literal byte-
  # equality interpretation is structurally unachievable for any multi-
  # cell year_outer scenario without engine-level row-buffering (the
  # alternative architectural option (a2) per notes/STEP_17c.md §3.6;
  # NOT taken).
  #
  # ===========================================================================
  # B17(b) OPERATIONAL ACCEPTANCE (UPDATE 2026-05-13 night, session 4):
  #
  # Per the user-authorised provisional-acceptance decision documented in
  # _chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md §4.13 + notes/STEP_17c.md
  # §3.8.5, the SORTED_DIFFER classification surfaces B17(b) drift cleanly
  # but the formal Option α (tolerance-based comparison upgrade) is DEFERRED
  # — the harness continues to controlled-fail at exit 2 on B17(b) drift.
  # Operationally B17(b) is ACCEPTED at a provisional 2% cell-total tolerance
  # envelope, consistent with Phase A's empirical max cell-total drift bound
  # of 1.4% relative (per notes/STEP_17c.md §1.3.3 A.4 + §3.8.1) with ~40%
  # headroom. Per-PFT splits in low-biomass marginal-establishment PFTs
  # (TrIBE, TrBR, IBS) may exceed 2% individually (up to ~17-20% empirically)
  # but are accepted under the same provisional acceptance because they
  # reflect inherent stochastic-perturbation behaviour of the LPJ-GUESS
  # engine, NOT a structural year_outer code-path defect.
  #
  # Re-evaluation hook: the provisional acceptance reactivates the formal
  # Option α implementation OR the (β) seed-tracking dprintf root-cause
  # investigation per notes/STEP_17c.md §3.8.4 + §3.6 IF (a) cell-total
  # drifts exceed 2% on a real-world gridlist or NCELLS scaling beyond the
  # 4-cell test envelope; OR (b) per-PFT splits diverge in scientifically-
  # consequential PFT/cell combinations beyond the empirical envelope; OR
  # (c) C3-era cluster smoke runs reveal MPI-multi-rank-specific drift
  # not captured by 4cell xval. Until then, SORTED_DIFFER count is
  # informational AND a controlled-fail signal — operators should inspect
  # the count + per-file drift magnitudes against the §3.8.5 provisional
  # tolerance and proceed at their discretion.
  # ===========================================================================
  #
  # Sort-key invariant: ALL .out files in this codebase have (Lon, Lat,
  # Year) as columns 1, 2, 3. Verified empirically across all 37 files
  # in the 4cell xval envelope (per Phase A.2 forensic in 17c.0.4
  # investigation). If a future output file uses a different column
  # layout, this assumption must be revisited.
  #
  # Cleanup: temp dir created via mktemp; auto-cleaned via trap RETURN.
  # No side effects outside this function.
  #
  # Cross-references:
  #   - notes/STEP_17c.md §3 (B17 forensic surface)
  #   - notes/STEP_17c.md §3.3 (B17(a) characterization + emission-order
  #     mechanism; CLOSED 2026-05-13 evening via this implementation)
  #   - notes/STEP_17c.md §3.6 option (a1) (recommended-fix skeleton;
  #     this implementation realizes that recommendation)
  #   - notes/STEP_17c.md §1.3 (17c.0.4 landing record at commit `027d90d`)
  #   - notes/STEP_17c.md §3.8 (reclassified-B17(b) sub-section; full
  #     forensic + scientific interpretation + Phase A's wall on
  #     root-cause identification)
  #   - notes/STEP_17c.md §3.8.5 (B17(b) provisional 2% tolerance
  #     operational acceptance; canonical record of the §4.13 decision)
  #   - notes/FOLLOWUPS.md "Audit item B17" (status dashboard; B17(a)
  #     CLOSED + B17(b) PROVISIONALLY ACCEPTED at 2% tolerance)
  #   - _chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md §4.13
  #     (operational-acceptance decision narrative; user-authorised
  #     2026-05-13 night, session 4)
  #
  # Backport classification: TRUNK-IRRELEVANT (.sh harness only;
  # cross_validate_year_outer.sh is per-fork; trunk_r13078 has no
  # year_outer mode and no cross-validation harness).
  #
  # - DKB 2026-05-13
  # =============================================================================
  local sorted_exact=0
  local sorted_differ=0
  if [ "$mismatches" -gt 0 ]; then
    echo
    echo "================================================================================"
    echo "B17(a) SORT-THEN-DIFF NORMALIZATION (added 2026-05-13 per audit item B17)"
    echo "  Sort key: (Lon, Lat, Year) = columns 1,2,3 (LC_ALL=C numeric sort)"
    echo "  Header (line 1) preserved verbatim; only data rows (lines 2..N) sorted."
    echo "================================================================================"
    local sort_tmp
    sort_tmp=$(mktemp -d -t b17a_sort_XXXXXX)
    # Auto-cleanup of $sort_tmp on function return (success or failure path).
    trap 'rm -rf "$sort_tmp"' RETURN

    for fa in "$RUN_A_DIR"/*.out; do
      local base
      base=$(basename "$fa")
      local fb="$RUN_B_DIR/$base"
      # Skip files already passing raw byte-equality (no sort needed).
      if cmp -s "$fa" "$fb" 2>/dev/null; then
        continue
      fi
      # Skip files missing in Run B (already counted in $mismatches as MISSING).
      if [ ! -f "$fb" ]; then
        continue
      fi
      # Sort body of A and B by (Lon, Lat, Year) preserving header.
      local sa="$sort_tmp/${base}.A.sorted"
      local sb="$sort_tmp/${base}.B.sorted"
      ( head -1 "$fa"; tail -n+2 "$fa" | LC_ALL=C sort -k1,1n -k2,2n -k3,3n ) > "$sa"
      ( head -1 "$fb"; tail -n+2 "$fb" | LC_ALL=C sort -k1,1n -k2,2n -k3,3n ) > "$sb"
      if cmp -s "$sa" "$sb"; then
        echo "  $base : ✓ SORTED_EXACT (PURE B17(a) - pure row-ordering; data identical)"
        sorted_exact=$((sorted_exact + 1))
      else
        local sorted_diff_lines
        sorted_diff_lines=$(diff "$sa" "$sb" | wc -l)
        echo "  $base : ✗ SORTED_DIFFER ($sorted_diff_lines lines; B17(a) + B17(b) drift)"
        sorted_differ=$((sorted_differ + 1))
      fi
    done

    echo
    echo "B17(a) NORMALIZATION SUMMARY:"
    echo "  BIT_EXACT     (raw cmp -s passed)                              : $matches / $total"
    echo "  SORTED_EXACT  (raw differs, sorted cmp -s passes; PURE B17(a)) : $sorted_exact"
    echo "  SORTED_DIFFER (raw differs AND sorted cmp -s differs;          : $sorted_differ"
    echo "                 B17(a) + B17(b) drift; B17(b) accepted at 2% per §3.8.5)"
    echo "  Total accounted for                                            : $((matches + sorted_exact + sorted_differ)) / $total"
  fi

  # =============================================================================
  # [Step 17b (F-12 sub-milestone C2 core; 2026-05-11) — SUBSTANTIVE-VALIDATION
  #  GATE added after a critical audit finding.]
  #
  # The byte-equality check above is NECESSARY but NOT SUFFICIENT for
  # validating that the year_outer code path produces scientifically
  # correct output. If both Run A and Run B produce NaN-laden outputs
  # (e.g., from a config-level issue in the smoke .ins or an LPJG-internal
  # bug exposed by our -input imogen / -input imogencfx + skip_inprocess_
  # engine_run = 1 path), the byte-by-byte comparison still reports PASS
  # because NaN bytes match NaN bytes — but the underlying simulation is
  # producing garbage.
  #
  # This was discovered 2026-05-11 during C2 core mpirun smoke testing:
  # the C1 close-out at v0.17.0-step17a-c1-year-outer-single-process
  # passed byte-equality but ALL 4 cross-validation scenarios were producing
  # NaN-equal-to-NaN outputs. The substantive-validation gap was masked by
  # the byte-comparison-only harness logic.
  #
  # This block adds a substantive-validation gate that scans both runs'
  # .out files for "nan" tokens and FAILS the validation if any are found.
  # Until the underlying NaN root cause is fixed (audit item B12; full
  # context in notes/STEP_17b.md §3a.7 + notes/FOLLOWUPS.md
  # "Substantive-validation NaN finding (2026-05-11)" + session-2 chat
  # handoff Part 18), this harness will correctly REFUSE TO PASS — forcing
  # explicit attention on the science-correctness issue rather than masking
  # it behind byte-equality-of-garbage.
  #
  # NOTE: this gate is intentionally strict. After NaN root cause is
  # diagnosed + fixed in audit item B12, this gate becomes the GO/NO-GO
  # check for SUBSTANTIVE validation (both bit-exact AND non-NaN).
  #
  # - DKB 2026-05-11
  # =============================================================================
  local nan_in_a nan_in_b
  nan_in_a=$(grep -l -i 'nan' "$RUN_A_DIR"/*.out 2>/dev/null | wc -l)
  nan_in_b=$(grep -l -i 'nan' "$RUN_B_DIR"/*.out 2>/dev/null | wc -l)

  echo
  echo "================================================================================"
  echo "SUBSTANTIVE-VALIDATION (NaN-check) — added 2026-05-11 per audit item B12"
  echo "================================================================================"
  echo "Run A .out files containing NaN: $nan_in_a / $n_a"
  echo "Run B .out files containing NaN: $nan_in_b / $n_b"

  # [Step 17c (17c.0.4 B17(a) FIX, 2026-05-13): effective-pass semantics
  #  updated to count BIT_EXACT + SORTED_EXACT toward PASS. Pre-17c.0.4 this
  #  block computed bit_exact_ok = ($mismatches == 0). Post-17c.0.4, raw
  #  mismatches that NORMALIZE to bit-equality via the sort-then-diff layer
  #  above (PURE B17(a) cases) count as semantic-byte-equal (Decision-12
  #  equality of CONTENT, not emission order). SORTED_DIFFER files (B17(a)
  #  + B17(b) drift) remain controlled-FAIL per the B17(b) provisional
  #  acceptance at 2% cell-total tolerance (notes/STEP_17c.md §3.8.5);
  #  formal Option α/β closure deferred to a future sub-phase TBD that
  #  reactivates only on a §3.8.5 re-eval trigger. - DKB 2026-05-13/14]
  local effective_pass=$((matches + sorted_exact))
  local bit_exact_ok=0
  if [ "$effective_pass" -eq "$total" ] && [ "$total" -gt 0 ]; then
    bit_exact_ok=1
  fi

  if [ "$nan_in_a" -gt 0 ] || [ "$nan_in_b" -gt 0 ]; then
    echo
    echo "FAIL (substantive-validation): NaN values detected in one or both runs."
    echo "  Byte-equality check: $([ $bit_exact_ok -eq 1 ] && echo PASS || echo FAIL)"
    echo "  Non-NaN check      : FAIL ($nan_in_a + $nan_in_b NaN-laden .out files)"
    echo
    echo "BACKGROUND: bit-exact byte-equality is necessary but NOT sufficient"
    echo "for scientific validation. If both Run A and Run B produce NaN-laden"
    echo "outputs from a config-level or LPJG-internal issue, byte-equality"
    echo "still passes (NaN bytes match NaN bytes) but the simulation is"
    echo "producing garbage. This gate refuses to PASS under such conditions."
    echo
    echo "See:"
    echo "  - notes/STEP_17b.md §3a.7 (NaN-finding forensic record + path forward)"
    echo "  - notes/FOLLOWUPS.md \"Substantive-validation NaN finding (2026-05-11)\""
    echo "  - session-2 chat handoff Part 18 (full investigation narrative)"
    echo
    echo "AUDIT ITEM B12: NaN root-cause investigation + fix (in-v1.0-scope;"
    echo "bundled with C2 era; CRITICAL PATH for substantively-validated"
    echo "v0.17.5-step17b-c2-mpi-sync close-out)."
    echo "================================================================================"
    return 3
  fi

  # =============================================================================
  # [Step 17c (B15; 2026-05-12) — SIGNAL-OF-LIFE ASSERTION
  #  added after a critical audit finding.]
  #
  # After Run B completes, this gate asserts that the year_outer code path
  # actually executed by grepping for the dprintf banner emitted at
  # framework.cpp:502:
  #     "[year_outer] starting framework_loop_mode = \"year_outer\" ..."
  # If the banner is absent, the gate FAILS with exit code 4 — even if
  # bit-equality and the NaN gate both pass — because that combination
  # would only be possible if Run B silently degraded to gridcell_outer
  # mode (then matched Run A trivially: gridcell_outer == gridcell_outer).
  #
  # Symmetric defensive check: if the [year_outer] banner appears in
  # RUN A's log, the gate FAILS because that means our gridcell_outer
  # baseline was wrongly entering the year_outer block — invalidating the
  # baseline-vs-year_outer comparison semantics.
  #
  # BACKGROUND: This assertion exists because of B15 (the audit item that
  # exposed the silent xval-harness defect 2026-05-12). The pre-B15 wrapper
  # used  param "framework_loop_mode" (str "year_outer")  which writes
  # only to the Paramlist custom-parameter dictionary, NOT to the C++ xtring
  # IMOGENConfig::framework_loop_mode that framework.cpp:464 reads. Because
  # Paramlist["framework_loop_mode"] is never consumed by any code path,
  # the override was a silent no-op. Bit-equality and NaN gates therefore
  # rubber-stamped four C1/C2 close-out validations that never actually
  # exercised year_outer. The B15 wrapper-writer fix uses bare syntax
  # (framework_loop_mode "year_outer") which mutates the correct C++ xtring,
  # but a structural defense — this banner-presence assertion — is added
  # to prevent any future analogous false-positive class.
  #
  # This becomes operational heuristic rule #8 in notes/FOLLOWUPS.md:
  # "every code-path-gated cross-validation must have a signal-of-life
  # assertion in the harness (banner-presence grep on a dprintf inside
  # the gated branch). Bit-exact match alone is insufficient when both
  # branches reduce to the same code."
  #
  # - DKB 2026-05-12
  # =============================================================================
  # [Subtle bash gotcha: grep -c always prints 0 to stdout when there are no
  #  matches, but exits with rc=1, which would then cause `|| echo 0` to print
  #  a SECOND "0", yielding a "0\n0" multiline string that fails subsequent
  #  integer comparisons. Pattern below: feed the file via `< file` so missing
  #  files become an empty stdin -> grep prints "0" with rc=1; suppress rc with
  #  `|| true` and leave the single "0" stdout intact. - DKB 2026-05-12 (B15)]
  local banner_a banner_b
  if [ -f "$RUN_A_DIR/run.log" ]; then
    banner_a=$(grep -c '\[year_outer\]' "$RUN_A_DIR/run.log" || true)
  else
    banner_a=0
  fi
  if [ -f "$RUN_B_DIR/run.log" ]; then
    banner_b=$(grep -c '\[year_outer\]' "$RUN_B_DIR/run.log" || true)
  else
    banner_b=0
  fi

  echo
  echo "================================================================================"
  echo "SIGNAL-OF-LIFE (B15) — added 2026-05-12 per audit item B15"
  echo "================================================================================"
  echo "Run A (gridcell_outer baseline) [year_outer] banner count: $banner_a (expected: 0)"
  echo "Run B (year_outer)              [year_outer] banner count: $banner_b (expected: >=1)"

  if [ "$banner_a" -gt 0 ]; then
    echo
    echo "FAIL (signal-of-life A): Run A's run.log contains [year_outer] banners."
    echo "  This means the gridcell_outer baseline somehow entered the year_outer"
    echo "  code path, invalidating the baseline-vs-year_outer comparison."
    echo "  Investigate: is framework_loop_mode being mis-set in the wrapper?"
    echo "  See notes/STEP_17c.md §0 (audit item B15) for the plib parser-mechanism forensic."
    echo "================================================================================"
    return 4
  fi

  if [ "$banner_b" -eq 0 ]; then
    echo
    echo "FAIL (signal-of-life B): Run B's run.log contains ZERO [year_outer] banners."
    echo "  This means the year_outer code path did NOT execute even though Run B"
    echo "  was supposed to test it. The framework_loop_mode override is silently"
    echo "  failing. Pre-B15, the wrapper used  param \"framework_loop_mode\" (str ...)"
    echo "  which writes to plib's Paramlist dict (unread for this parameter) instead"
    echo "  of mutating IMOGENConfig::framework_loop_mode (which framework.cpp:464"
    echo "  reads). The B15 fix is to use bare syntax  framework_loop_mode \"year_outer\""
    echo "  in the wrapper. See notes/STEP_17c.md §0 (audit item B15) for the full forensic."
    echo "================================================================================"
    return 4
  fi

  if [ "$bit_exact_ok" -eq 1 ]; then
    echo
    echo "PASS (substantive + signal-of-life): All .out files are byte-exact (raw OR sorted-by-(Lon,Lat,Year)"
    echo "  per B17(a) normalization) AND non-NaN between Run A and Run B, AND the year_outer banner"
    echo "  appeared $banner_b time(s) in Run B's log (and 0 times in Run A's log) — confirming the year_outer"
    echo "  code path was actually executed in Run B and NOT in Run A."
    if [ "$sorted_exact" -gt 0 ]; then
      echo
      echo "  Note: $sorted_exact file(s) required B17(a) sort-normalization (raw differs but data is"
      echo "  identical after sort by (Lon, Lat, Year)). PURE B17(a) cases reflect the year_outer loop's"
      echo "  year-major emission order vs gridcell_outer's cell-major emission order; data content is"
      echo "  identical. See notes/STEP_17c.md §3.3."
    fi
    return 0
  else
    echo
    echo "FAIL: $sorted_differ file(s) have B17(b) drift (raw AND sorted both differ);"
    echo "  $matches BIT_EXACT + $sorted_exact SORTED_EXACT (PURE B17(a)) + $sorted_differ SORTED_DIFFER"
    echo "  + $((mismatches - sorted_exact - sorted_differ)) MISSING/other = $total total."
    echo
    echo "B17(b) is the small-magnitude (~0.5-2%) numerical drift in per-PFT-total +"
    echo "  tot_runoff files between gridcell_outer and year_outer multi-cell runs."
    echo "  Empirical signature: per-cell-isolated stochastic-process divergence (cell 0"
    echo "  bit-exact in BOTH modes; cells 1+ progressively diverge in low-biomass PFTs"
    echo "  while cell totals stay within ~1.4% relative). Closure plan in"
    echo "  notes/STEP_17c.md §3 (B17(b) forensic) + §3.6 (recommended-fix skeleton)"
    echo "  + §3.8.5 (B17(b) provisionally accepted at 2% per 2026-05-13 user directive;"
    echo "    formal Option α tolerance vs Option β root-cause closure deferred to a"
    echo "    future sub-phase TBD reactivated only on a §3.8.5 re-eval trigger)."
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
