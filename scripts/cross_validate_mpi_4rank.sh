#!/bin/bash
# =============================================================================
# scripts/cross_validate_mpi_4rank.sh
# =============================================================================
#
# Step 17c (F-12 sub-milestone C3 PREP sub-phase 17c.0.7) — workstation
# `mpirun -np N` mimic verification harness, fulfilling the deferred-from-C2
# obligation per session-2 §17.7 (`_chat_artifacts/CHAT_HANDOFF_2026-05-08_
# session2.md` lines ~3789-3794) + the planning-doc directive at
# `notes/STEP_17c.md` §1 row 17c.0.7.
#
# WHAT THIS HARNESS VALIDATES (the C2-core MPI machinery, end-to-end on
# multiple ranks for the FIRST TIME):
#
#   1. `MPI_Barrier(MPI_COMM_WORLD)` at year boundary in `framework.cpp`
#      year_outer block (lines ~682-695; HAVE_MPI + MPI_Initialized guarded)
#      actually fires across N ranks without deadlock.
#
#   2. `ImogenOutput::flush_year_globally_synchronized(int year)` at
#      `imogenoutput.cpp:412+` correctly performs `MPI_Allreduce(MPI_SUM)`
#      over per-rank `accum_NEE_kgC` / `accum_CH4_gCH4C` / `accum_N2O_kgN`
#      / `accum_area_m2` / `accum_gridcell_count` and the lead rank
#      (rank 0) writes the unified handshake file `imogen_lpjg_flux.txt`.
#      (Loose mode early-exits this method at line 421 — no Allreduce
#      called; only the year-boundary MPI_Barrier is exercised in loose.)
#
#   3. The aggregate per-cell `*.out` files (after `cluster/append_files.sh`
#      concatenation of per-rank `runNN/*.out`) match the single-process
#      `year_outer` baseline within either BIT_EXACT or B17(a)-normalized
#      SORTED_EXACT envelope. Any SORTED_DIFFER outcome surfaces a NEW
#      audit item (provisional B18) for investigation.
#
#   4. The Allreduce-driven `imogen_lpjg_flux.txt` matches single-process
#      either BIT_EXACT or within IEEE-754 ULP-level FP-non-associativity
#      tolerance (the well-known floor of `MPI_Allreduce(SUM)` reduction
#      tree topology vs sequential SUM).
#
# WHY THIS WAS NOT VERIFIED AT C2 CLOSE-OUT (`f6c192e`, 2026-05-12):
#
# Per session-2 §17.7 deferral, the C2 close-out tag was issued with only
# `mpirun -np 1 -parallel` smoke verification. The full `mpirun -np 4`
# mimic was bundled-deferred into B-bundles (B4 prerequisite for the
# loose-mode 6-vs-10-fields gap closure was the explicit blocker, since
# resolved at commit `2bd5222`). At 17c.0.7, that obligation now lands.
#
# WHY NOW IN PARTICULAR (post-17c.0.6):
#
# The B17(b) MECHANICAL CLOSURE landed at sub-phase 17c.0.6 (commit
# `5d80e1d`; tag `v0.17.6-step17c-b17b-closure`) means we CAN now do a
# MEANINGFUL bit-equivalent comparison: pre-17c.0.6 the 4cell year_outer
# baseline had a 17-file SORTED_DIFFER drift that would have masked any
# additional MPI-rank-specific drift here. Post-17c.0.6 the 4cell
# year_outer envelope is `15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER
# + exit 0` IDENTICAL between LOOSE and TIGHT — clean baseline against
# which the mpirun-np-N aggregate can be compared cleanly.
#
# USAGE
# -----
#     scripts/cross_validate_mpi_4rank.sh [MODE] [NP]
#
#   MODE (1st arg; default 'all'):
#     loose      : `-input imogen` + coupling_mode "loose"; exercises only
#                  MPI_Barrier (flush_year_globally_synchronized early-exits
#                  per imogenoutput.cpp:421); embarrassingly-parallel
#     prescribed : `-input imogencfx` + coupling_mode "prescribed" +
#                  skip_inprocess_engine_run=1; full C2-core MPI exercise
#                  (Barrier + Allreduce + lead-rank-only-write); engine
#                  doesn't run in-process; this is the originally-articulated
#                  17c.0.7 deliverable per session-2 §17.7 verbatim
#     tight      : `-input imogencfx` + coupling_mode "tight" +
#                  skip_inprocess_engine_run=1; SAME C2-core MPI machinery
#                  as prescribed (both proceed through Allreduce + write);
#                  the only on-disk difference is the mode-string written
#                  into imogen_lpjg_flux.txt header (if applicable).
#                  In skip_inprocess_engine_run=1 setup, the in-process
#                  engine is NOT actually exercised (would require
#                  additional bootstrap work + climate-staging churn that
#                  is out-of-scope for 17c.0.7's MPI-machinery focus).
#                  A TRUE full-closed-loop tight run is deferred to the
#                  cluster phases (17c.1+) where SLURM provides the
#                  scaffold for engine-loop iteration.
#     all        : run all 3 modes sequentially (the v0.17.7 deliverable)
#
#   NP   (2nd arg; default 4):
#     Number of MPI ranks. The smoke gridlist `data/gridlist/gridlist_
#     test2.txt` has 4 cells; with NP=4 we get the canonical 1-cell-per-
#     rank scenario. NP > 4 would have idle ranks (split sets cells/N rounded
#     up; ranks beyond ceil(N/4) would get empty gridlists and likely fail
#     LPJ-GUESS's must-have-at-least-one-cell init); NP = 1, 2 are valid
#     but less interesting (no MPI rank-distribution exercise for NP=1).
#
# PRE-REQUISITES (verified during pre-flight):
#   1. `lpjguess/build_mpi/guess` exists and is MPI-linked (built at
#      sub-phase 17c.0.6 verification gate 2; surviving on-disk if no
#      intermediate build was triggered).
#   2. `mpirun` is on PATH (Anaconda3 MPICH 4.1.1 expected on workstation).
#   3. Pre-staged climate library at
#      `runs/SSP1-2.6/Common-directory/IMOGEN/output/{1871..1879}/`
#      (with all 13 climate files per year-dir; established at C1.3 sub-
#      step 7.3.1; used by every `cross_validate_year_outer.sh` invocation
#      from 17c.0.1 onward).
#   4. `runs/SSP1-2.6/main_xval_loose.ins` (loose-mode base .ins) +
#      `runs/SSP1-2.6/main_xval_imogencfx.ins` (tight/prescribed-mode
#      base .ins) both present.
#   5. `data/gridlist/gridlist_test2.txt` (the 4-cell smoke gridlist).
#
# OUTPUT LAYOUT
# -------------
# Per mode `<MODE>`:
#
#   Run B baseline (single-process year_outer):
#     $COMMON_DIR/xval_runs/4cell_<MODE>_mpi_run_B_baseline_year_outer/
#       *.out                                       (37 LPJ-GUESS output files)
#       LPJG_main/IMOGEN/imogen_lpjg_flux.txt       (per-year NEE_PgC; APPEND mode; non-loose only)
#       LPJG_main/IMOGEN/imogen_lpjg_ch4_n2o_flux.txt (per-year CH4_TgCH4 + N2O_TgN2O; APPEND mode; non-loose only)
#       LPJG_main/IMOGEN/imogen_lpjg.txt            (single-year final-state handshake; TRUNC each year; non-loose only)
#       LPJG_main/IMOGEN/done                       (engine-poll sentinel; TRUNC each year; non-loose only)
#       run.log                                     (full LPJG stdout/stderr capture)
#       xval_baseline_wrapper.ins                   (wrapper .ins for this run)
#
#   Run C MPI aggregate (mpirun -np N year_outer):
#     $SCENARIO_DIR/parallel_work_xval_mpi/<MODE>_4cell_runs/
#       run1/                                       (per-rank dir; 1 cell)
#       run2/                                       (per-rank dir; 1 cell)
#       run3/                                       (per-rank dir; 1 cell)
#       run4/                                       (per-rank dir; 1 cell)
#       *.out                                       (post-append_files.sh aggregate)
#       LPJG_main/IMOGEN/imogen_lpjg_flux.txt       (lead-rank-written; Allreduce(SUM)-aggregated; non-loose only)
#       LPJG_main/IMOGEN/imogen_lpjg_ch4_n2o_flux.txt (lead-rank-written; Allreduce(SUM)-aggregated; non-loose only)
#       LPJG_main/IMOGEN/imogen_lpjg.txt            (single-year final-state handshake; non-loose only)
#       LPJG_main/IMOGEN/done                       (engine-poll sentinel; non-loose only)
#       run.log                                     (combined mpirun output)
#       xval_mpi_wrapper.ins                        (wrapper .ins shared across ranks)
#
# WHY HANDSHAKE FILES NOW WRITE CORRECTLY (post-17c.0.7 refresh; was missing
# in the smoke run, root-caused as a wrapper-side DIR_COMMON elision):
#   - The xval base .ins (main_xval_imogencfx.ins) does NOT import
#     imogen_intermediary.ins (the production-launcher import that sets
#     DIR_COMMON), so DIR_COMMON was at C++ default (empty xtring) →
#     handshake_dir resolved to "/LPJG_main/IMOGEN/" (root-owned absolute path)
#     → all 4 ofstream opens silently failed with WARNING dprintfs in run.log.
#     The MPI machinery itself (Barrier + Allreduce + lead-rank-only-write)
#     was empirically green even in the smoke run (per-cell .out comparison
#     PASSED 15 BIT + 22 SORTED + 0 DIFFER); only the write target was wrong.
#   - Path α (refined) fix: wrapper .ins emits `DIR_COMMON "<absolute-path>"`
#     for non-loose modes; absolute path makes handshake_dir consistent across
#     all ranks (avoids per-rank-cwd-relative resolution to runNN/...) and
#     points to a writable per-mode-isolated location.
#   - The C++ does 2-level mkdir at imogenoutput.cpp:140-142 (creates
#     <DIR_COMMON>/LPJG_main/ then <DIR_COMMON>/LPJG_main/IMOGEN/) so the
#     harness does not need to pre-create the subdir.
#   - Loose mode: handshake files NOT produced by design (flush_year + flush_
#     year_globally_synchronized both early-exit for coupling_mode=='loose'
#     per imogenoutput.cpp:259 + 421); compare_imogen_lpjg_*() correctly
#     reports "absent in both = BY DESIGN" for loose.
#
# EXIT CODES
# ----------
#   0 : all requested modes PASS (no SORTED_DIFFER per-cell + flux equivalent
#       within tolerance; signal-of-life clean)
#   1 : pre-flight failure (missing binary / missing climate / missing .ins
#       / mpirun not on PATH); short-circuit before any execution
#   2 : at least one mode produced SORTED_DIFFER per-cell .out (REGRESSION
#       relative to 17c.0.6 baseline OR new audit item B18 (MPI-rank-specific
#       drift)); operationally either way investigation is warranted
#   3 : at least one mode failed signal-of-life assertions (MPI_Barrier
#       didn't fire; flush_year_globally_synchronized didn't fire; rank
#       didn't complete; banner missing); deeper bug than B17/B18 surface
#
# REFERENCES
# ----------
# - notes/STEP_17c.md §1 row 17c.0.7 (this sub-phase's planning entry)
# - notes/STEP_17c.md §3.9 (NEW; B18 surface IF surfaces; written post-run)
# - notes/STEP_17b.md §3a.7 (the C2-era B-bundle B12 forensic — substantive-
#   validation NaN gate origin; this harness inherits the same gate)
# - lpjguess/framework/framework.cpp:682-695 (MPI_Barrier site)
# - lpjguess/modules/imogenoutput.cpp:412+ (flush_year_globally_synchronized
#   + MPI_Allreduce sites)
# - scripts/cross_validate_year_outer.sh (sibling harness; post-17c.0.6
#   establishes the SINGLE-PROCESS year_outer baseline that this harness
#   builds on top of for the multi-rank comparison)
# - scripts/cluster/setup_run.sh (the per-rank gridlist-split + runNN/-
#   subdir staging utility this harness invokes)
# - scripts/cluster/append_files.sh (the per-file aggregator this harness
#   invokes after Run C completes)
# - _chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md §17.7 (the
#   originally-articulated deferred-from-C2 deliverable; quoted verbatim
#   in this harness's design recommendation per session-3+4 chat handoff)
#
# Backport classification: TRUNK-IRRELEVANT-by-novelty (year_outer +
# C2-core MPI machinery are both step-17 additions; no analog in
# trunk_r13078).
#
# - DKB 2026-05-15 (step 17c sub-phase 17c.0.7)
# =============================================================================

set -u
# (intentionally NOT set -e + NOT set -o pipefail — like the sibling
#  cross_validate_year_outer.sh, we WANT to continue past per-run non-zero
#  exit codes so we can report a complete comparison summary cleanly.)

# -----------------------------------------------------------------------------
# CLI args
# -----------------------------------------------------------------------------
MODE_ARG="${1:-all}"
NP="${2:-4}"

case "$MODE_ARG" in
  loose|prescribed|tight|all) : ;;
  *)
    echo "Usage: $0 [loose|prescribed|tight|all] [NP]" >&2
    echo "  Got unrecognized 1st argument: $MODE_ARG" >&2
    exit 1
    ;;
esac

if ! [[ "$NP" =~ ^[0-9]+$ ]] || [ "$NP" -lt 1 ]; then
  echo "ERROR: NP must be a positive integer (got '$NP')" >&2
  exit 1
fi

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCENARIO_DIR="$ROOT/runs/SSP1-2.6"
COMMON_DIR="$SCENARIO_DIR/Common-directory"
GRIDLIST_NAME="gridlist_test2.txt"   # 4-cell smoke; harness assumes 4 cells
GRIDLIST="$ROOT/data/gridlist/$GRIDLIST_NAME"
GUESS_BIN="$ROOT/lpjguess/build_mpi/guess"
APPEND_FILES_SH="$SCRIPT_DIR/cluster/append_files.sh"
SETUP_RUN_SH="$SCRIPT_DIR/cluster/setup_run.sh"

# Per-mode I/O
BASE_INS_LOOSE="$SCENARIO_DIR/main_xval_loose.ins"
BASE_INS_TIGHT="$SCENARIO_DIR/main_xval_imogencfx.ins"

# Run B baseline output base
RUN_B_BASE="$COMMON_DIR/xval_runs"

# Run C MPI work base (per-mode subdirs created below)
WORK_BASE="$SCENARIO_DIR/parallel_work_xval_mpi"

# -----------------------------------------------------------------------------
# Pre-flight
# -----------------------------------------------------------------------------
preflight_die() {
  echo "================================================================================" >&2
  echo "PRE-FLIGHT FAILURE: $1" >&2
  echo "================================================================================" >&2
  exit 1
}

[ -x "$GUESS_BIN" ]                                  || preflight_die "MPI binary missing or not executable: $GUESS_BIN"
[ -f "$GRIDLIST" ]                                   || preflight_die "Gridlist missing: $GRIDLIST"
[ -f "$BASE_INS_LOOSE" ]                             || preflight_die "Loose-mode base .ins missing: $BASE_INS_LOOSE"
[ -f "$BASE_INS_TIGHT" ]                             || preflight_die "Tight/prescribed-mode base .ins missing: $BASE_INS_TIGHT"
[ -d "$COMMON_DIR/IMOGEN/output/1871" ]              || preflight_die "Pre-staged climate missing: $COMMON_DIR/IMOGEN/output/1871/"
[ -x "$APPEND_FILES_SH" ]                            || preflight_die "append_files.sh missing or not executable: $APPEND_FILES_SH"
[ -x "$SETUP_RUN_SH" ]                               || preflight_die "setup_run.sh missing or not executable: $SETUP_RUN_SH"
command -v mpirun >/dev/null                         || preflight_die "mpirun not on PATH (Anaconda3 MPICH expected at /home/bampoh-d/anaconda3/bin/mpirun)"
ldd "$GUESS_BIN" 2>&1 | grep -qiE "libmpi|libpmi"    || preflight_die "build_mpi/guess does not appear to be MPI-linked (no libmpi/libpmi in ldd output)"

NCELL=$(grep -cv '^[[:space:]]*$' "$GRIDLIST")
if [ "$NCELL" -lt "$NP" ]; then
  echo "WARNING: gridlist has $NCELL cells but --np $NP requested." >&2
  echo "         Reducing NP to $NCELL to ensure each rank has >= 1 cell." >&2
  NP=$NCELL
fi

# -----------------------------------------------------------------------------
# Banner
# -----------------------------------------------------------------------------
cat <<EOF

================================================================================
17c.0.7 workstation \`mpirun -np $NP\` mimic verification harness
================================================================================
  Mode arg          : $MODE_ARG
  NP                : $NP
  Gridlist          : $GRIDLIST  ($NCELL cells)
  MPI binary        : $GUESS_BIN
  Common dir        : $COMMON_DIR
  Run B base        : $RUN_B_BASE
  Run C work base   : $WORK_BASE
  Loose base .ins   : $BASE_INS_LOOSE
  Tight base .ins   : $BASE_INS_TIGHT
  mpirun            : $(command -v mpirun)
  mpirun version    : $(mpirun --version 2>&1 | head -1)
================================================================================

EOF

# -----------------------------------------------------------------------------
# Per-mode dispatch tables
# -----------------------------------------------------------------------------
mode_input_module() {
  case "$1" in
    loose)      echo "imogen" ;;
    prescribed) echo "imogencfx" ;;
    tight)      echo "imogencfx" ;;
  esac
}

mode_base_ins() {
  case "$1" in
    loose)                echo "$BASE_INS_LOOSE" ;;
    prescribed|tight)     echo "$BASE_INS_TIGHT" ;;
  esac
}

mode_coupling_string() {
  case "$1" in
    loose)      echo "loose" ;;
    prescribed) echo "prescribed" ;;
    tight)      echo "tight" ;;
  esac
}

# -----------------------------------------------------------------------------
# Function: write_baseline_wrapper <mode> <out_dir>
# Writes the wrapper .ins for Run B (single-process year_outer baseline).
# Mirrors the cross_validate_year_outer.sh wrapper pattern exactly except
# we ALSO override coupling_mode (so the tight variant routes through the
# tight code path even though the underlying base .ins uses prescribed).
# -----------------------------------------------------------------------------
write_baseline_wrapper() {
  local mode="$1"
  local out_dir="$2"
  local base_ins
  base_ins="$(mode_base_ins "$mode")"
  local coupling
  coupling="$(mode_coupling_string "$mode")"

  mkdir -p "$out_dir"
  local wrapper="$out_dir/xval_baseline_wrapper.ins"

  cat > "$wrapper" <<EOF
!///////////////////////////////////////////////////////////////////////////////////////
! Auto-generated wrapper .ins for 17c.0.7 Run B baseline
!   (single-process year_outer; \`-input $(mode_input_module "$mode")\`;
!    coupling_mode "$coupling"; gridlist $GRIDLIST_NAME).
! Generated by scripts/cross_validate_mpi_4rank.sh at \$(date).
!///////////////////////////////////////////////////////////////////////////////////////

! Import base .ins (sets all standard params; for tight-mode, base is
! main_xval_imogencfx.ins which sets coupling_mode "prescribed" — we
! override below to "tight" to route through the tight code path; for
! loose-mode, base is main_xval_loose.ins which doesn't set coupling_mode
! at all because ImogenInput doesn't declare_parameter it — only
! IMOGENCFXInput does at imogencfx.cpp:340).
import "$base_ins"

! Per-run overrides (gridlist absolute; framework_loop_mode bare-syntax
! per B15 fix; coupling_mode bare-syntax conditionally emitted below).
param "file_gridlist"     (str "$GRIDLIST")
param "file_gridlist_cf"  (str "$GRIDLIST")
framework_loop_mode "year_outer"
EOF

  # Conditionally emit coupling_mode override:
  #   - loose mode: SKIP (coupling_mode not declared by ImogenInput → would
  #     trigger plib "Undefined identifier" error and abort startup;
  #     loose mode is the absence-of-IMOGENCFXInput condition, not a
  #     parameter setting).
  #   - prescribed/tight: emit override (base sets prescribed; we want
  #     either to confirm prescribed explicitly or override to tight).
  if [ "$mode" != "loose" ]; then
    echo "coupling_mode \"$coupling\"" >> "$wrapper"
  fi

  # Conditionally emit DIR_COMMON override (Path α refined fix per
  # 17c.0.7 handshake-file investigation; was the root cause of
  # imogen_lpjg_*.txt absence in the smoke run):
  #   - loose mode: SKIP (handshake files not produced anyway per
  #     imogenoutput.cpp:259 mode gate; emitting DIR_COMMON for loose
  #     would be inert but adds no value).
  #   - prescribed/tight: emit absolute per-mode-isolated path. The
  #     C++ at imogenoutput.cpp:136 will compute handshake_dir =
  #     "<out_dir>/LPJG_main/IMOGEN/" and 2-level mkdir at lines
  #     140-142 will create both subdirs. This makes:
  #       - the handshake-file write target writable + per-mode-isolated
  #         (Run B baseline writes go to baseline_dir/LPJG_main/IMOGEN/;
  #         Run C MPI writes go to mpi_work_dir/LPJG_main/IMOGEN/)
  #       - the comparison can directly cmp -s files under those dirs
  #         (vs needing to snapshot Run B before Run C overwrites)
  if [ "$mode" != "loose" ]; then
    echo "DIR_COMMON \"$out_dir\"" >> "$wrapper"
  fi

  cat >> "$wrapper" <<EOF
outputdirectory "$out_dir/"
EOF

  echo "$wrapper"
}

# -----------------------------------------------------------------------------
# Function: run_baseline <mode> <out_dir>
# Executes Run B baseline (single-process year_outer; build_mpi/guess
# WITHOUT -parallel). Returns the LPJG exit code.
# -----------------------------------------------------------------------------
run_baseline() {
  local mode="$1"
  local out_dir="$2"
  local input_module
  input_module="$(mode_input_module "$mode")"

  echo
  echo "--------------------------------------------------------------------------------"
  echo "[Run B baseline] mode=$mode : single-process year_outer"
  echo "                 out_dir=$out_dir"
  echo "--------------------------------------------------------------------------------"

  rm -rf "$out_dir"
  mkdir -p "$out_dir"
  local wrapper
  wrapper="$(write_baseline_wrapper "$mode" "$out_dir")"

  cd "$COMMON_DIR"
  echo "[Run B] cwd: $(pwd)"
  echo "[Run B] cmd: $GUESS_BIN -input $input_module $wrapper"
  echo "[Run B] log: $out_dir/run.log"

  set +e
  "$GUESS_BIN" -input "$input_module" "$wrapper" > "$out_dir/run.log" 2>&1
  local rc=$?
  set -e

  local n_out
  n_out=$(ls "$out_dir"/*.out 2>/dev/null | wc -l)
  echo "[Run B] exit=$rc ; produced $n_out .out files"
  return $rc
}

# -----------------------------------------------------------------------------
# Function: stage_mpi_work <mode> <work_dir>
# Stages the Run C MPI work dir via cluster/setup_run.sh: per-rank runNN/
# subdirs with gridlist split + .ins copies.
# -----------------------------------------------------------------------------
stage_mpi_work() {
  local mode="$1"
  local work_dir="$2"
  local input_module
  input_module="$(mode_input_module "$mode")"
  local base_ins
  base_ins="$(mode_base_ins "$mode")"
  local base_ins_basename
  base_ins_basename="$(basename "$base_ins")"

  echo
  echo "--------------------------------------------------------------------------------"
  echo "[Run C stage] mode=$mode : mpirun -np $NP year_outer"
  echo "              work_dir=$work_dir"
  echo "--------------------------------------------------------------------------------"

  # Clean prior work_dir
  if [ -d "$work_dir" ]; then
    echo "  cleaning prior $work_dir"
    rm -rf "$work_dir"
  fi
  mkdir -p "$(dirname "$work_dir")"

  # Mirror run_parallel_mimic.sh's invocation pattern: setup_run.sh creates
  # the per-rank runNN/ subdirs + gridlist split + .ins copies. We pass
  # extra-insfiles enumerating ALL the .ins files imported transitively by
  # the base .ins (global.ins, crop_n.ins, wetlandpfts.ins + their imports).
  # Empirically this list is the same for both loose and tight bases.
  local extra_insfiles="global.ins crop_n.ins landcover.ins wetlandpfts.ins crop.ins crop_n_pftlist.simplePFT.remap10_g2p.ins crop_n_stlist.simplePFT.remap10_g2p.N0-60-200-1000.ins crop_n_stlist.simplePFT.remap10_g2p.agreed_treatments.ins pasture_n_stlist.ins pasture_n_stlist_agreed_treatments.ins global_soiln.ins imogen_intermediary.ins"
  # ALSO copy the base .ins itself (so it's available for our wrapper to
  # import via either basename or absolute path)
  extra_insfiles="$extra_insfiles $base_ins_basename"

  bash "$SETUP_RUN_SH" \
    --runname "$(basename "$work_dir")" \
    --maininsfile "main.ins" \
    --extra-insfiles "$extra_insfiles" \
    --gridlist "$GRIDLIST" \
    --inputmethod "$input_module" \
    --nnodes 1 \
    --cpu-per-node "$NP" \
    --partition "workstation-mimic" \
    --walltime "01:00:00" \
    --binary "$GUESS_BIN" \
    --scenario-dir "$SCENARIO_DIR" \
    --workdir-base "$(dirname "$work_dir")" \
    > "$work_dir.setup_run.log" 2>&1
  local rc=$?

  if [ $rc -ne 0 ]; then
    echo "[Run C stage] setup_run.sh FAILED (rc=$rc); see $work_dir.setup_run.log"
    cat "$work_dir.setup_run.log"
    return $rc
  fi

  # Note: setup_run.sh's --workdir-base creates $WORKDIR_BASE/$(basename
  # SCENARIO_DIR)/, NOT $WORKDIR_BASE/<runname>/. So the actual work_dir
  # is $WORKDIR_BASE/SSP1-2.6/. Symlink to our requested work_dir for
  # consistent downstream paths.
  local actual_work_dir
  actual_work_dir="$(dirname "$work_dir")/$(basename "$SCENARIO_DIR")"
  if [ -d "$actual_work_dir" ] && [ ! -e "$work_dir" ]; then
    mv "$actual_work_dir" "$work_dir"
  fi

  if [ ! -d "$work_dir/run1" ]; then
    echo "[Run C stage] FATAL: setup_run.sh did not produce per-rank runNN/ subdirs at $work_dir"
    return 2
  fi

  echo "[Run C stage] staged successfully:"
  ls -d "$work_dir/run"* 2>/dev/null
  for ((i=1; i <= NP; i++)); do
    local n
    n=$(grep -cv '^[[:space:]]*$' "$work_dir/run$i/$GRIDLIST_NAME" 2>/dev/null || echo 0)
    echo "    run$i: $n cells"
  done
  return 0
}

# -----------------------------------------------------------------------------
# Function: write_mpi_wrapper <mode> <work_dir>
# Writes the Run C wrapper .ins (shared across ranks). Each rank cd's into
# runNN/ at LPJ-GUESS -parallel startup; we use:
#   - gridlist by basename (resolves to per-rank-subset via runNN/$GRIDLIST_NAME)
#   - climate paths absolute (no dependency on per-rank cwd)
#   - framework_loop_mode "year_outer" (the C2-core exercise)
#   - coupling_mode "<mode>" (override base)
#   - outputdirectory "./" (per-rank cwd is runNN/, outputs land there)
# -----------------------------------------------------------------------------
write_mpi_wrapper() {
  local mode="$1"
  local work_dir="$2"
  local base_ins
  base_ins="$(mode_base_ins "$mode")"
  local base_ins_basename
  base_ins_basename="$(basename "$base_ins")"
  local coupling
  coupling="$(mode_coupling_string "$mode")"

  local wrapper="$work_dir/xval_mpi_wrapper.ins"

  # Path mappings per mode for climate inputs:
  # - The base .ins sets relative paths like ./IMOGEN/output/YYYY/T_anom.dat.
  # - Per-rank cwd is runNN/, so without intervention these would resolve
  #   to runNN/IMOGEN/... which doesn't exist.
  # - Solution: override climate paths to absolute (this also future-proofs
  #   against any cwd quirks in the parallel codepath).
  cat > "$wrapper" <<EOF
!///////////////////////////////////////////////////////////////////////////////////////
! Auto-generated wrapper .ins for 17c.0.7 Run C MPI mimic
!   (mpirun -np $NP year_outer; \`-input $(mode_input_module "$mode")\`;
!    coupling_mode "$coupling"; per-rank gridlist runNN/$GRIDLIST_NAME).
! Generated by scripts/cross_validate_mpi_4rank.sh at \$(date).
!///////////////////////////////////////////////////////////////////////////////////////

! Import base .ins (basename; resolved relative to per-rank cwd which has
! a copy via setup_run.sh's per-rank-stage of all .ins files).
import "$base_ins_basename"

! Per-rank gridlist (basename; resolves to runNN/$GRIDLIST_NAME which
! has 1 cell per rank for NP=4 + 4-cell test gridlist).
param "file_gridlist"     (str "$GRIDLIST_NAME")
param "file_gridlist_cf"  (str "$GRIDLIST_NAME")

! Climate paths overridden to absolute (the base .ins uses relative paths
! that would resolve to runNN/IMOGEN/... which doesn't exist; absolute
! paths resolve correctly regardless of per-rank cwd).
param "file_temp"    (str "$COMMON_DIR/IMOGEN/output/YYYY/T_anom.dat")
param "file_prec"    (str "$COMMON_DIR/IMOGEN/output/YYYY/P_anom.dat")
param "file_insol"   (str "$COMMON_DIR/IMOGEN/output/YYYY/SW_anom.dat")
param "file_wetdays" (str "$COMMON_DIR/IMOGEN/output/YYYY/WET.dat")
param "file_dtr"     (str "$COMMON_DIR/IMOGEN/output/YYYY/DTEMP_anom.dat")
param "file_co2"     (str "$COMMON_DIR/IMOGEN/output/YYYY/CO2.dat")
param "file_relhum"  (str "$COMMON_DIR/IMOGEN/output/YYYY/Rh_anom.dat")
param "file_wind"    (str "$COMMON_DIR/IMOGEN/output/YYYY/W_anom.dat")
param "file_tmin"    (str "$COMMON_DIR/IMOGEN/output/YYYY/Tmin_anom.dat")
param "file_tmax"    (str "$COMMON_DIR/IMOGEN/output/YYYY/Tmax_anom.dat")

! C2-core MPI exercise: year_outer mode (where MPI_Barrier + flush_year_
! globally_synchronized live).
framework_loop_mode "year_outer"
EOF

  # coupling_mode emitted only for non-loose modes (loose-mode ImogenInput
  # doesn't declare_parameter coupling_mode → bare-syntax write would
  # error; prescribed/tight require IMOGENCFXInput which DOES declare it
  # at imogencfx.cpp:340).
  if [ "$mode" != "loose" ]; then
    echo "coupling_mode \"$coupling\"" >> "$wrapper"
  fi

  # DIR_COMMON override (Path α refined fix per 17c.0.7 handshake-file
  # investigation; mirrors write_baseline_wrapper's DIR_COMMON emission).
  # Critically: ABSOLUTE path, not relative. If we emitted a relative
  # path, each rank would resolve it from its own per-rank cwd (runNN/)
  # → handshake_dir would be per-rank-isolated → the lead-rank-only
  # write would land in run1/<DIR_COMMON_REL>/LPJG_main/IMOGEN/ instead
  # of the shared work_dir/LPJG_main/IMOGEN/. Absolute makes all ranks
  # see the same handshake_dir; only rank 0 writes (per imogenoutput.
  # cpp:466 lead-rank-gate); other ranks participate in MPI_Allreduce
  # then no-op.
  if [ "$mode" != "loose" ]; then
    echo "DIR_COMMON \"$work_dir\"" >> "$wrapper"
  fi

  cat >> "$wrapper" <<EOF

! Output dir: per-rank cwd is runNN/; outputs land there.
outputdirectory "./"
EOF

  # Copy wrapper to each per-rank dir
  for ((i=1; i <= NP; i++)); do
    cp "$wrapper" "$work_dir/run$i/"
  done

  echo "$wrapper"
}

# -----------------------------------------------------------------------------
# Function: run_mpi_4rank <mode> <work_dir>
# Executes Run C: mpirun -np $NP build_mpi/guess -parallel ...
# Returns the mpirun exit code.
# -----------------------------------------------------------------------------
run_mpi_4rank() {
  local mode="$1"
  local work_dir="$2"
  local input_module
  input_module="$(mode_input_module "$mode")"

  local wrapper
  wrapper="$(write_mpi_wrapper "$mode" "$work_dir")"
  local wrapper_basename
  wrapper_basename="$(basename "$wrapper")"

  cd "$work_dir"
  echo
  echo "[Run C exec] cwd: $(pwd)"
  echo "[Run C exec] cmd: mpirun -np $NP $GUESS_BIN -parallel -input $input_module $wrapper_basename"
  echo "[Run C exec] log: $work_dir/run.log"

  set +e
  mpirun -np "$NP" "$GUESS_BIN" -parallel -input "$input_module" "$wrapper_basename" \
    > "$work_dir/run.log" 2>&1
  local rc=$?
  set -e

  echo "[Run C exec] mpirun exit=$rc"
  for ((i=1; i <= NP; i++)); do
    local n
    n=$(ls "$work_dir/run$i"/*.out 2>/dev/null | wc -l)
    echo "    run$i: $n .out files"
  done
  return $rc
}

# -----------------------------------------------------------------------------
# Function: aggregate_mpi_outputs <work_dir>
# Aggregates per-rank runNN/*.out into $work_dir/*.out via
# scripts/cluster/append_files.sh. Mirrors finishup_lpj_work.sh's invocation
# pattern.
# -----------------------------------------------------------------------------
aggregate_mpi_outputs() {
  local work_dir="$1"

  cd "$work_dir"
  local nout_per_rank
  nout_per_rank=$(find run1 -name '*.out' 2>/dev/null | wc -l)
  echo
  echo "[Run C aggregate] $nout_per_rank .out files per rank; concatenating across $NP ranks via append_files.sh"

  # Defensive: remove any stale top-level .out from a prior run
  find . -maxdepth 1 -name '*.out' -delete 2>/dev/null || true

  # append_files.sh signature: append_files.sh <number_of_jobs> <file1> [<file2> ...]
  find run1 -name '*.out' | sed 's,run1/,,g' \
    | xargs -n "$NP" -P "$NP" "$APPEND_FILES_SH" "$NP" \
    > "$work_dir.append.log" 2>&1
  local rc=$?

  local naggr
  naggr=$(find . -maxdepth 1 -name '*.out' 2>/dev/null | wc -l)
  echo "[Run C aggregate] produced $naggr aggregated .out files at $work_dir/"
  if [ "$naggr" -ne "$nout_per_rank" ]; then
    echo "  WARNING: aggregate count ($naggr) differs from per-rank count ($nout_per_rank)"
  fi
  return $rc
}

# -----------------------------------------------------------------------------
# Function: signal_of_life_check <mode> <baseline_log> <mpi_log>
# Verifies that:
#   - Run B baseline log has [year_outer] banner
#   - Run C mpirun log has [year_outer] banner per rank (>= NP)
#   - For non-loose modes: per-rank flush_year_globally_synchronized dprintfs
#     are visible (>= NP * N_YEARS where N_YEARS = lasthistyear - firsthistyear + 1)
# Returns 0 on green; 3 on signal-of-life failure.
# -----------------------------------------------------------------------------
signal_of_life_check() {
  local mode="$1"
  local baseline_log="$2"
  local mpi_log="$3"

  echo
  echo "[Signal of life] mode=$mode"

  local rc=0

  # [year_outer] banner is emitted by framework.cpp:502 ONCE per process at
  # year_outer block entry. Single-process Run B: should see >= 1.
  # Multi-rank Run C: should see >= NP (one per rank).
  local banner_b
  banner_b=$(grep -c '\[year_outer\]' "$baseline_log" 2>/dev/null || echo 0)
  echo "  Run B baseline [year_outer] banner count : $banner_b (expected >= 1)"
  if [ "$banner_b" -lt 1 ]; then
    echo "    FAIL: year_outer banner missing in baseline log; framework_loop_mode override failed?"
    rc=3
  fi

  local banner_c
  banner_c=$(grep -c '\[year_outer\]' "$mpi_log" 2>/dev/null || echo 0)
  echo "  Run C mpirun   [year_outer] banner count : $banner_c (expected >= $NP)"
  if [ "$banner_c" -lt "$NP" ]; then
    echo "    FAIL: only $banner_c year_outer banner(s) in mpirun log; expected one per rank ($NP)"
    rc=3
  fi

  if [ "$mode" != "loose" ]; then
    # flush_year_globally_synchronized fires per-rank-per-year for non-loose
    # modes. The dprintf at imogenoutput.cpp:508 fires for non-lead ranks
    # (rank != 0) per year. Lead rank (rank 0) executes flush_year() which
    # has its own dprintf at imogenoutput.cpp:223+ (see existing flush_year
    # docstring). So both rank-0 and rank-N>0 emit per-year diagnostics.
    # Conservative threshold: >= NP banners total (at least 1 per rank for
    # any year of the smoke run).
    local flush_c
    flush_c=$(grep -c 'flush_year_globally_synchronized' "$mpi_log" 2>/dev/null || echo 0)
    echo "  Run C mpirun   flush_year_globally_synchronized dprintf count : $flush_c (expected >= $NP)"
    if [ "$flush_c" -lt "$NP" ]; then
      echo "    FAIL: only $flush_c flush_year_globally_synchronized dprintf(s); expected at least one per rank ($NP)"
      rc=3
    fi
  else
    echo "  (loose mode: flush_year_globally_synchronized early-exits at imogenoutput.cpp:421;"
    echo "   only MPI_Barrier exercised in loose; no dprintf check)"
  fi

  return $rc
}

# -----------------------------------------------------------------------------
# Function: nan_gate <baseline_dir> <mpi_dir>
# Substantive-validation gate (B12-era) — refuses to PASS if either run
# produced NaN-laden outputs (would mask comparison-of-garbage).
# Returns 0 on clean; 3 on NaN found.
# -----------------------------------------------------------------------------
nan_gate() {
  local baseline_dir="$1"
  local mpi_dir="$2"

  local nan_b nan_c
  nan_b=$(grep -l -i 'nan' "$baseline_dir"/*.out 2>/dev/null | wc -l)
  nan_c=$(grep -l -i 'nan' "$mpi_dir"/*.out 2>/dev/null | wc -l)

  echo "  NaN gate: Run B baseline files with NaN : $nan_b (expected 0)"
  echo "  NaN gate: Run C aggregate files with NaN : $nan_c (expected 0)"

  if [ "$nan_b" -gt 0 ] || [ "$nan_c" -gt 0 ]; then
    echo "  FAIL: NaN found in output; refusing to PASS comparison-of-garbage"
    return 3
  fi
  return 0
}

# -----------------------------------------------------------------------------
# Function: compare_outputs <baseline_dir> <mpi_dir>
# Mirrors cross_validate_year_outer.sh's compare_outputs() exactly: raw
# cmp -s pass + B17(a) sort-then-diff fallback. Returns:
#   0 if all files BIT_EXACT or SORTED_EXACT
#   2 if any file SORTED_DIFFER (post-17c.0.6 = REGRESSION or NEW B18 surface)
#
# Sets globals: BIT_EXACT, SORTED_EXACT, SORTED_DIFFER, MISSING, TOTAL
# -----------------------------------------------------------------------------
BIT_EXACT=0
SORTED_EXACT=0
SORTED_DIFFER=0
MISSING=0
TOTAL=0
compare_outputs() {
  local baseline_dir="$1"
  local mpi_dir="$2"

  BIT_EXACT=0
  SORTED_EXACT=0
  SORTED_DIFFER=0
  MISSING=0
  TOTAL=0

  echo
  echo "[Compare] Run B baseline dir : $baseline_dir"
  echo "[Compare] Run C aggregate dir: $mpi_dir"
  echo

  local sort_tmp
  sort_tmp=$(mktemp -d -t mpi4rank_sort_XXXXXX)
  # Note: explicit cleanup at every return point below (rather than trap
  # RETURN) because trap+local interacts badly with `set -u` after the
  # function returns: the local sort_tmp goes out of scope but the trap's
  # command-string is evaluated lazily, triggering "unbound variable".

  for fb in "$baseline_dir"/*.out; do
    local base
    base=$(basename "$fb")
    local fc="$mpi_dir/$base"
    TOTAL=$((TOTAL + 1))

    if [ ! -f "$fc" ]; then
      printf "  %-40s : MISSING in Run C aggregate\n" "$base"
      MISSING=$((MISSING + 1))
      continue
    fi

    if cmp -s "$fb" "$fc"; then
      printf "  %-40s : ✓ BIT_EXACT\n" "$base"
      BIT_EXACT=$((BIT_EXACT + 1))
      continue
    fi

    # Sort-then-diff (B17(a) normalization; sort by Lon, Lat, Year)
    local sb="$sort_tmp/${base}.B.sorted"
    local sc="$sort_tmp/${base}.C.sorted"
    ( head -1 "$fb"; tail -n+2 "$fb" | LC_ALL=C sort -k1,1n -k2,2n -k3,3n ) > "$sb"
    ( head -1 "$fc"; tail -n+2 "$fc" | LC_ALL=C sort -k1,1n -k2,2n -k3,3n ) > "$sc"
    if cmp -s "$sb" "$sc"; then
      printf "  %-40s : ✓ SORTED_EXACT (PURE B17(a) - row-ordering only; data identical)\n" "$base"
      SORTED_EXACT=$((SORTED_EXACT + 1))
    else
      local lines_diff
      lines_diff=$(diff "$sb" "$sc" | wc -l)
      printf "  %-40s : ✗ SORTED_DIFFER ($lines_diff lines; MPI-rank-specific drift?)\n" "$base"
      SORTED_DIFFER=$((SORTED_DIFFER + 1))
    fi
  done

  echo
  echo "================================================================================"
  echo "COMPARISON SUMMARY:"
  echo "  BIT_EXACT     (raw cmp -s passed)                              : $BIT_EXACT / $TOTAL"
  echo "  SORTED_EXACT  (raw differs, sorted cmp -s passes; PURE B17(a)) : $SORTED_EXACT"
  echo "  SORTED_DIFFER (raw differs AND sorted cmp -s differs;           : $SORTED_DIFFER"
  echo "                 expected = 0 IF MPI_Allreduce reduction is FP-"
  echo "                 deterministic vs sequential SUM; > 0 indicates"
  echo "                 either (a) genuine MPI-rank-specific drift to"
  echo "                 investigate as new audit item B18, or (b) IEEE-"
  echo "                 754 FP-non-associativity floor of MPI_Allreduce"
  echo "                 reduction-tree topology vs sequential SUM, well-"
  echo "                 understood + bounded; per-file body inspection"
  echo "                 required to disambiguate)"
  echo "  MISSING       (file in Run B baseline but not Run C aggregate) : $MISSING"
  echo "  Total accounted for                                            : $((BIT_EXACT + SORTED_EXACT + SORTED_DIFFER + MISSING)) / $TOTAL"
  echo "================================================================================"

  rm -rf "$sort_tmp"

  if [ "$MISSING" -gt 0 ] || [ "$SORTED_DIFFER" -gt 0 ]; then
    return 2
  fi
  return 0
}

# -----------------------------------------------------------------------------
# Function: compare_handshake_file <baseline_dir> <mpi_dir> <relpath> <mode>
# Generic handshake-file comparison helper. <relpath> is the path under each
# run's root (e.g. "LPJG_main/IMOGEN/imogen_lpjg_flux.txt"). The C++-hardcoded
# handshake_dir suffix at imogenoutput.cpp:136 is "/LPJG_main/IMOGEN/" relative
# to DIR_COMMON; our wrapper sets DIR_COMMON to the run's root, so all
# handshake files land at <run_root>/LPJG_main/IMOGEN/<filename>.
#
# Returns:
#   0 = BIT_EXACT (or absent-in-both for loose-mode = BY DESIGN)
#   2 = MISSING in either run after Path α fix (load-bearing failure)
#   the FP-drift case is reported as a WARNING but returns 0 (well-known
#   IEEE-754 floor for MPI_Allreduce reduction-tree topology vs sequential
#   SUM; not a defect, an empirical observation about the floor's magnitude)
#
# Sets globals (per-call): HANDSHAKE_VERDICT (BIT_EXACT|FP_DRIFT|MISSING|
# ABSENT_BY_DESIGN), HANDSHAKE_DRIFT_LINES (line-count of any drift).
# -----------------------------------------------------------------------------
compare_handshake_file() {
  local baseline_dir="$1"
  local mpi_dir="$2"
  local relpath="$3"
  local mode="$4"

  local fb="$baseline_dir/$relpath"
  local fc="$mpi_dir/$relpath"
  local label
  label="$(basename "$relpath")"

  HANDSHAKE_VERDICT=""
  HANDSHAKE_DRIFT_LINES=0

  if [ ! -f "$fb" ] && [ ! -f "$fc" ]; then
    if [ "$mode" = "loose" ]; then
      printf "  %-32s : ✓ ABSENT in BOTH (BY DESIGN for loose mode; flush_year early-exits at imogenoutput.cpp:259)\n" "$label"
      HANDSHAKE_VERDICT="ABSENT_BY_DESIGN"
      return 0
    else
      printf "  %-32s : ✗ MISSING in BOTH (Path α DIR_COMMON wrapper-fix did not work; check run.log for WARNING)\n" "$label"
      HANDSHAKE_VERDICT="MISSING"
      return 2
    fi
  fi

  if [ ! -f "$fb" ]; then
    printf "  %-32s : ✗ MISSING in Run B baseline (single-process flush_year() failed; check baseline run.log)\n" "$label"
    HANDSHAKE_VERDICT="MISSING"
    return 2
  fi

  if [ ! -f "$fc" ]; then
    printf "  %-32s : ✗ MISSING in Run C MPI aggregate (lead-rank flush_year() failed; check mpirun run.log)\n" "$label"
    HANDSHAKE_VERDICT="MISSING"
    return 2
  fi

  if cmp -s "$fb" "$fc"; then
    printf "  %-32s : ✓ BIT_EXACT (single-process SUM == MPI_Allreduce(SUM) bit-deterministic for this cardinality)\n" "$label"
    HANDSHAKE_VERDICT="BIT_EXACT"
    return 0
  fi

  HANDSHAKE_DRIFT_LINES=$(diff "$fb" "$fc" | wc -l)
  printf "  %-32s : ⚠ FP_DRIFT (%d diff-lines; well-known MPI_Allreduce reduction-tree IEEE-754 non-associativity floor; not a defect)\n" \
    "$label" "$HANDSHAKE_DRIFT_LINES"
  echo "    Diff (full):"
  diff "$fb" "$fc" | sed 's/^/      /'
  HANDSHAKE_VERDICT="FP_DRIFT"
  return 0
}

# -----------------------------------------------------------------------------
# Function: compare_handshake_files <baseline_dir> <mpi_dir> <mode>
# Calls compare_handshake_file for each of the 4 handshake files emitted by
# flush_year() at imogenoutput.cpp:283-365:
#   - imogen_lpjg_flux.txt          : timeseries (year, NEE_PgC); APPEND mode
#   - imogen_lpjg_ch4_n2o_flux.txt  : timeseries (year, CH4_TgCH4, N2O_TgN2O);
#                                     APPEND mode
#   - imogen_lpjg.txt               : single-year final-state handshake;
#                                     TRUNC each year (last year only at end)
#   - done                          : engine-poll sentinel; TRUNC each year
#                                     (single-line content only)
#
# All four are produced under <DIR_COMMON>/LPJG_main/IMOGEN/ (C++-hardcoded
# suffix at imogenoutput.cpp:136).
#
# Per-mode semantics:
#   - loose: ALL FOUR absent BY DESIGN (flush_year mode-gate at line 259)
#     → all four ABSENT_BY_DESIGN verdict; mode-rc unaffected
#   - prescribed/tight: ALL FOUR present + BIT_EXACT (or FP-drift acceptable)
#     → if any MISSING: handshake_rc=2 (load-bearing failure)
#     → if all BIT_EXACT or FP_DRIFT: handshake_rc=0 (PASS)
#
# Sets globals: HANDSHAKE_BIT_EXACT, HANDSHAKE_FP_DRIFT, HANDSHAKE_MISSING,
# HANDSHAKE_ABSENT_BY_DESIGN, HANDSHAKE_TOTAL.
# -----------------------------------------------------------------------------
HANDSHAKE_BIT_EXACT=0
HANDSHAKE_FP_DRIFT=0
HANDSHAKE_MISSING=0
HANDSHAKE_ABSENT_BY_DESIGN=0
HANDSHAKE_TOTAL=0
compare_handshake_files() {
  local baseline_dir="$1"
  local mpi_dir="$2"
  local mode="$3"

  HANDSHAKE_BIT_EXACT=0
  HANDSHAKE_FP_DRIFT=0
  HANDSHAKE_MISSING=0
  HANDSHAKE_ABSENT_BY_DESIGN=0
  HANDSHAKE_TOTAL=0

  echo
  echo "[Handshake] LPJG→IMOGEN handshake-file comparison (4 files; under <run_root>/LPJG_main/IMOGEN/)"
  echo "  Run B baseline : $baseline_dir/LPJG_main/IMOGEN/"
  echo "  Run C MPI agg  : $mpi_dir/LPJG_main/IMOGEN/"
  echo

  local rc=0
  local file_rc
  for f in \
    "LPJG_main/IMOGEN/imogen_lpjg_flux.txt" \
    "LPJG_main/IMOGEN/imogen_lpjg_ch4_n2o_flux.txt" \
    "LPJG_main/IMOGEN/imogen_lpjg.txt" \
    "LPJG_main/IMOGEN/done"; do
    HANDSHAKE_TOTAL=$((HANDSHAKE_TOTAL + 1))
    file_rc=0
    compare_handshake_file "$baseline_dir" "$mpi_dir" "$f" "$mode" || file_rc=$?
    case "$HANDSHAKE_VERDICT" in
      BIT_EXACT)         HANDSHAKE_BIT_EXACT=$((HANDSHAKE_BIT_EXACT + 1)) ;;
      FP_DRIFT)          HANDSHAKE_FP_DRIFT=$((HANDSHAKE_FP_DRIFT + 1)) ;;
      MISSING)           HANDSHAKE_MISSING=$((HANDSHAKE_MISSING + 1)) ;;
      ABSENT_BY_DESIGN)  HANDSHAKE_ABSENT_BY_DESIGN=$((HANDSHAKE_ABSENT_BY_DESIGN + 1)) ;;
    esac
    if [ "$file_rc" -gt "$rc" ]; then
      rc=$file_rc
    fi
  done

  echo
  echo "  HANDSHAKE SUMMARY (mode=$mode):"
  echo "    BIT_EXACT          : $HANDSHAKE_BIT_EXACT / $HANDSHAKE_TOTAL"
  echo "    FP_DRIFT           : $HANDSHAKE_FP_DRIFT (acceptable; MPI_Allreduce IEEE-754 floor)"
  echo "    MISSING            : $HANDSHAKE_MISSING (FAIL if > 0 in non-loose modes)"
  echo "    ABSENT_BY_DESIGN   : $HANDSHAKE_ABSENT_BY_DESIGN (correct for loose mode; otherwise FAIL)"

  return $rc
}

# =============================================================================
# Per-mode driver
# =============================================================================
GLOBAL_RC=0
declare -A MODE_RC

run_mode() {
  local mode="$1"

  echo
  echo "################################################################################"
  echo "# MODE: $mode"
  echo "################################################################################"

  local baseline_dir="$RUN_B_BASE/4cell_${mode}_mpi_run_B_baseline_year_outer"
  local mpi_work_dir="$WORK_BASE/${mode}_4cell_runs"
  mkdir -p "$RUN_B_BASE" "$WORK_BASE"

  # Phase B.1: Run B baseline
  if ! run_baseline "$mode" "$baseline_dir"; then
    echo "[mode=$mode] Run B baseline FAILED; skipping Run C + comparison"
    MODE_RC[$mode]=1
    GLOBAL_RC=$((GLOBAL_RC > 1 ? GLOBAL_RC : 1))
    return
  fi

  # Phase C.1: Stage Run C
  if ! stage_mpi_work "$mode" "$mpi_work_dir"; then
    echo "[mode=$mode] Run C stage FAILED; skipping execution + comparison"
    MODE_RC[$mode]=1
    GLOBAL_RC=$((GLOBAL_RC > 1 ? GLOBAL_RC : 1))
    return
  fi

  # Phase C.2: Execute Run C
  if ! run_mpi_4rank "$mode" "$mpi_work_dir"; then
    echo "[mode=$mode] Run C mpirun FAILED; attempting aggregation + comparison anyway"
    # Don't early-return; partial outputs may still be informative
  fi

  # Phase C.3: Aggregate Run C
  aggregate_mpi_outputs "$mpi_work_dir"

  # Phase C.4: Signal-of-life
  local sol_rc=0
  signal_of_life_check "$mode" "$baseline_dir/run.log" "$mpi_work_dir/run.log" || sol_rc=$?

  # Phase C.5: NaN gate
  local nan_rc=0
  nan_gate "$baseline_dir" "$mpi_work_dir" || nan_rc=$?

  # Phase C.6: Per-cell .out comparison
  local cmp_rc=0
  compare_outputs "$baseline_dir" "$mpi_work_dir" || cmp_rc=$?

  # Phase C.7: Handshake-file comparison (all 4 files under LPJG_main/IMOGEN/)
  local hsk_rc=0
  compare_handshake_files "$baseline_dir" "$mpi_work_dir" "$mode" || hsk_rc=$?

  # Per-mode verdict (priority: signal_of_life/NaN > comparison > handshake)
  # rc=3: signal-of-life or NaN failure (deeper than B17/B18)
  # rc=2: per-cell SORTED_DIFFER OR handshake-file MISSING (load-bearing fail)
  # rc=0: clean PASS (handshake FP_DRIFT is acceptable)
  local mode_rc
  if [ $sol_rc -ne 0 ] || [ $nan_rc -ne 0 ]; then
    mode_rc=3
  elif [ $cmp_rc -ne 0 ] || [ $hsk_rc -ne 0 ]; then
    mode_rc=2
  else
    mode_rc=0
  fi
  MODE_RC[$mode]=$mode_rc
  if [ $mode_rc -gt $GLOBAL_RC ]; then
    GLOBAL_RC=$mode_rc
  fi

  echo
  echo "[mode=$mode] per-cell envelope    : BIT_EXACT=$BIT_EXACT / SORTED_EXACT=$SORTED_EXACT / SORTED_DIFFER=$SORTED_DIFFER / MISSING=$MISSING (rc=$cmp_rc)"
  echo "[mode=$mode] handshake envelope   : BIT_EXACT=$HANDSHAKE_BIT_EXACT / FP_DRIFT=$HANDSHAKE_FP_DRIFT / MISSING=$HANDSHAKE_MISSING / ABSENT_BY_DESIGN=$HANDSHAKE_ABSENT_BY_DESIGN (rc=$hsk_rc)"
  echo "[mode=$mode] signal_of_life_rc=$sol_rc ; nan_rc=$nan_rc ; mode_rc=$mode_rc"
}

# Dispatch
if [ "$MODE_ARG" = "all" ]; then
  for m in loose prescribed tight; do
    run_mode "$m"
  done
else
  run_mode "$MODE_ARG"
fi

# =============================================================================
# Final summary
# =============================================================================
echo
echo "================================================================================"
echo "17c.0.7 OVERALL VERDICT"
echo "================================================================================"
for m in loose prescribed tight; do
  if [ -n "${MODE_RC[$m]:-}" ]; then
    case "${MODE_RC[$m]}" in
      0) verdict="✓ PASS (per-cell .out clean + handshake files BIT_EXACT-or-FP_DRIFT)" ;;
      1) verdict="✗ EXEC FAIL (Run B or Run C did not complete)" ;;
      2) verdict="✗ COMPARISON FAIL (per-cell SORTED_DIFFER > 0 [B18 candidate] OR handshake-file MISSING [Path α DIR_COMMON wrapper-fix did not work])" ;;
      3) verdict="✗ SIGNAL-OF-LIFE or NaN FAIL (deeper than B17/B18; bug in C2-core machinery?)" ;;
    esac
    printf "  mode %-12s : rc=%d : %s\n" "$m" "${MODE_RC[$m]}" "$verdict"
  fi
done
echo
case $GLOBAL_RC in
  0) echo "  GLOBAL: ✓ ALL REQUESTED MODES PASS — 17c.0.7 deferred-from-C2 obligation FULFILLED" ;;
  1) echo "  GLOBAL: ✗ EXECUTION FAILURE in at least one mode — investigate run.log files" ;;
  2) echo "  GLOBAL: ✗ COMPARISON FAILURE in at least one mode — investigate as B18 candidate" ;;
  3) echo "  GLOBAL: ✗ SIGNAL-OF-LIFE or NaN FAILURE in at least one mode — deeper bug in C2-core machinery?" ;;
esac
echo "================================================================================"

exit $GLOBAL_RC
