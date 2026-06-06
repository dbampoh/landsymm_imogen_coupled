#!/usr/bin/env bash
# run_armB.sh -- Identical-emulator diagnostic (path A): run ONE isolated Arm-B
# IMOGEN engine-only control for <SSP> <variant> on the native 1631 pattern grid.
#
# FAITHFUL MIRROR of scripts/run_trunk_engine_only.sh (the harness that produced the
# paper's Arm-A climate), differing ONLY in:
#   * isolated sibling run dir forks/trunk_r13078_runs/<SSP>_armB_<variant>/  (never
#     touches the paper run dir forks/trunk_r13078_runs/<SSP>/ or its outputs);
#   * the 4 FILE_* emission inputs point at the Arm-B inputs (everything else byte-identical
#     to Arm A -> a true identical-emulator control).
# Uses the SAME binary (build_b824/guess; the one that declares `coupling_mode` and whose
# 2026-05-26 build produced Arm A's output/), the SAME entry (main_engine_only.ins,
# skip_inprocess_engine_run 0), and the SAME bootstrap-handshake + done-marker sidecar.
#
# Usage: run_armB.sh <SSP> <variant>     (variant: opt1 | opt2 | armArepro)
set -uo pipefail

SSP="${1:?usage: run_armB.sh <SSP> <variant>}"
VARIANT="${2:?usage: run_armB.sh <SSP> <variant>}"

ROOT="/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm"
TRUNK_BIN="${TRUNK_BIN:-${ROOT}/forks/trunk_r13078/build_b824/guess}"   # the build that declares coupling_mode + made Arm A
SRC="${ROOT}/forks/trunk_r13078_runs/${SSP}"
RUN="${ROOT}/forks/trunk_r13078_runs/${SSP}_armB_${VARIANT}"
INP="${ROOT}/scripts/Paper_Analysis/comparative_analysis_GMD_paper/identical_emulator_diagnostic/armB_inputs/${SSP}_${VARIANT}"
COMMON="${RUN}/Common-directory"
HSHAKE="${COMMON}/LPJG_main/IMOGEN"
OUTDIR="${COMMON}/IMOGEN/output"

[ -x "$TRUNK_BIN" ] || { echo "FATAL: binary missing: $TRUNK_BIN"; exit 2; }
[ -d "$SRC" ]       || { echo "FATAL: source run dir missing: $SRC"; exit 2; }
[ -d "$INP" ]       || { echo "FATAL: Arm-B inputs missing: $INP"; exit 2; }
[ -f "$SRC/main_engine_only.ins" ] || { echo "FATAL: main_engine_only.ins missing in $SRC"; exit 2; }
case "$RUN" in *_armB_*) : ;; *) echo "FATAL: refusing non-armB run dir: $RUN"; exit 2 ;; esac

echo "[1] Fresh isolated run dir: $RUN  (binary: $TRUNK_BIN)"
rm -rf "$RUN"
mkdir -p "$OUTDIR" "$HSHAKE"

echo "[2] Cloning .ins files (small text only) from $SRC"
cp "$SRC"/*.ins "$RUN"/

echo "[3] Rewiring the 4 FILE_* emission inputs -> Arm-B inputs ($INP) in BOTH imogen_intermediary.ins and main_engine_only.ins"
for INS in "$RUN/imogen_intermediary.ins" "$RUN/main_engine_only.ins"; do
  sed -i -E "s#^FILE_SCEN_EMITS[[:space:]]+\".*#FILE_SCEN_EMITS         \"${INP}/co2_anthro_emissions.txt\"#"            "$INS"
  sed -i -E "s#^FILE_CH4_N2O_EMITS[[:space:]]+\".*#FILE_CH4_N2O_EMITS      \"${INP}/ch4_n2o_anthro_emissions.txt\"#"     "$INS"
  sed -i -E "s#^FILE_LPJG_FLUX[[:space:]]+\".*#FILE_LPJG_FLUX          \"${INP}/imogen_lpjg_flux.txt\"#"                 "$INS"
  sed -i -E "s#^FILE_LPJG_CH4_N2O_FLUX[[:space:]]+\".*#FILE_LPJG_CH4_N2O_FLUX  \"${INP}/imogen_lpjg_ch4_n2o_flux.txt\"#" "$INS"
done
echo "    Active FILE_* in main_engine_only.ins (end-of-file overrides win):"
grep -E "^FILE_(SCEN_EMITS|CH4_N2O_EMITS|LPJG_FLUX|LPJG_CH4_N2O_FLUX)" "$RUN/main_engine_only.ins" | sed 's/^/      /'

echo "[3b] Override EBM params -> MRI-ESM2-0-calibrated (mri-esm2-0_params.json). The paper .ins"
echo "     carried generic HadCM3-era defaults (LAMBDA_L 0.4 / LAMBDA_O 1.9 / MU 1.78 / KAPPA_O 280);"
echo "     all SSPs use the MRI-ESM2-0 pattern, so the EBM that scales it must be MRI-calibrated too."
for INS in "$RUN/imogen_intermediary.ins" "$RUN/main_engine_only.ins"; do
  sed -i -E "s#^KAPPA_O[[:space:]]+[0-9.]+.*#KAPPA_O         500.0   ! MRI-ESM2-0 calibrated (was 280.0 generic)#"          "$INS"
  sed -i -E "s#^F_OCEAN[[:space:]]+[0-9.]+.*#F_OCEAN         0.7077764 ! MRI-ESM2-0 calibrated (was 0.71)#"                  "$INS"
  sed -i -E "s#^LAMBDA_L[[:space:]]+[0-9.]+.*#LAMBDA_L        1.5485998 ! MRI-ESM2-0 calibrated (was 0.4 generic)#"          "$INS"
  sed -i -E "s#^LAMBDA_O[[:space:]]+[0-9.]+.*#LAMBDA_O        1.3468532 ! MRI-ESM2-0 calibrated (was 1.9 generic)#"          "$INS"
  sed -i -E "s#^MU[[:space:]]+[0-9.]+.*#MU              1.4476492 ! MRI-ESM2-0 calibrated (was 1.78 generic)#"               "$INS"
done
echo "    Active EBM params in imogen_intermediary.ins:"
grep -E "^(KAPPA_O|F_OCEAN|LAMBDA_L|LAMBDA_O|MU)[[:space:]]" "$RUN/imogen_intermediary.ins" | sed 's/^/      /'

echo "[4] Bootstrap handshake (imogen_lpjg.txt + done) -- verbatim from run_trunk_engine_only.sh"
# PRODUCTION-FAITHFUL: identical static bootstrap to run_trunk_engine_only.sh. The engine
# run length comes from main_engine_only.ins / the emission-input span (full 1900-2101,
# verified 202 year-dirs), NOT from IYEND_BOOT here (the handshake only seeds the first call).
# ENGINE BINARY: with the FIXED engine (build_oceanfix, passed via TRUNK_BIN) this harness
# produces proper transient warming -- SSP5-8.5 land-mean ~+10 K (2015->2100), reaching
# ~300 K, vs the buggy build_b824 Arm-A run which was flat at +0.2 K (the gcm_anlg
# Jan-only-dtemp_l + non-persistent dtemp_o defect, fixed 2026-06-05). The earlier
# "+0.4 K is the documented cool bias" note was written before that root-cause was found.
YEAR1_BOOT=1900; IYEND_BOOT=1901
if [ "$YEAR1_BOOT" -lt 1901 ]; then SPINUP_BOOT="TRUE"; else SPINUP_BOOT="FALSE"; fi
cat > "$HSHAKE/imogen_lpjg.txt" <<EOF
YEAR1 ${YEAR1_BOOT} !IN First year of the numerical experiment
IYEND ${IYEND_BOOT} !IN Stop year of the ENTIRE run
YEAR1_LPJG ${YEAR1_BOOT} !IN First year of the whole LPJ-GUESS simulation
SPINUP ${SPINUP_BOOT} !IN Are we in the spin-up phase of LPJ-GUESS?
KEEPRUNNING TRUE !IN control flag to keep imogen running
FIRSTCALL TRUE !IN Is this the very first call to IMOGEN from LPJ-GUESS
EOF
echo "bootstrap" > "$HSHAKE/done"

echo "[5] Engine-only run: $TRUNK_BIN -input imogencfx main_engine_only.ins"
( while true; do touch "$HSHAKE/done" 2>/dev/null; sleep 1; done ) &
SIDE=$!
trap 'kill $SIDE 2>/dev/null; wait $SIDE 2>/dev/null; rm -f "$HSHAKE/done" 2>/dev/null' EXIT
cd "$RUN"
"$TRUNK_BIN" -input imogencfx main_engine_only.ins > "$RUN/engine_run.log" 2>&1
EC=$?
kill $SIDE 2>/dev/null; wait $SIDE 2>/dev/null
echo "    guess exit code: $EC (99 expected at the YEAR1==2100 over-shoot)"

NY=$(ls -d "$OUTDIR"/[12]*/ 2>/dev/null | wc -l)
SZ=$(du -sh "$OUTDIR" 2>/dev/null | awk '{print $1}')
echo "[done] $SSP/$VARIANT -> output year-dirs: $NY (expect ~202), size: $SZ  (log: $RUN/engine_run.log)"
