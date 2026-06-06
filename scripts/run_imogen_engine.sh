#!/bin/bash
# scripts/run_imogen_engine.sh
# =============================================================================
# General-purpose, GCM-parameterised IMOGEN cppengine run wrapper (delta_b
# variant). Produces a full 1900-2100 climate library for ONE <SSP> x <GCM>
# combination, then (optionally) FastRegrids it 1631 -> NN 3698 -> IDW 62892
# (the cluster-ingest grid). Generalises the identical-emulator-diagnostic
# harness (scripts/Paper_Analysis/.../identical_emulator_diagnostic/{run_armB,
# reproduce_corrected_climate}.sh) into a reusable production script that
# auto-applies the per-GCM EBM parameters (so you can run MRI for the paper or
# switch to GFDL/IPSL/MPI/UKESM for sensitivity/ensemble work with one arg).
#
# WHAT IT DOES (per run):
#   1. Resolve the GCM's pattern dir (imogen/patterns/CEN_CMIP6_MOD_<GCM>) and
#      its calibrated EBM scalars (imogen/patterns/<GCM>_ebm.nml).
#   2. Build the 4 IMOGEN emission/flux inputs from the intermediary_py
#      integrated-emissions CSV (tools/imogen_inputs_to_lpjg_format.py).
#   3. Set up an ISOLATED run dir (forks/trunk_r13078_runs/<SSP>_<GCM>_<TAG>/),
#      clone the .ins set from the paper run dir, then rewire:
#        - the 4 FILE_* emission/flux inputs -> the built inputs,
#        - DIR_PATT -> CEN_CMIP6_MOD_<GCM>,
#        - KAPPA_O / F_OCEAN / LAMBDA_L / LAMBDA_O / MU -> the GCM's EBM scalars.
#   4. Run the fixed engine (default build_oceanfix/guess; oceanfix = persistent
#      ocean heat + once-per-year dtemp_l applied to all 12 months) via the
#      main_engine_only.ins entry + bootstrap-handshake + done-marker sidecar.
#   5. (unless --no-regrid) chain scripts/run_fastregrid.sh <rundir> delta_b_variant
#      to produce output_3698_cppengine (NN) + output_62892_cppengine (IDW).
#
# The paper run dirs (forks/trunk_r13078_runs/<SSP>/) and their outputs are
# NEVER touched (read-only source for the cloned .ins + adapter CSV).
#
# Usage:
#   scripts/run_imogen_engine.sh <SSP> <GCM> [--tag TAG] [--no-regrid]
#                                            [--inputs-csv PATH] [--src-dir DIR]
# Examples:
#   scripts/run_imogen_engine.sh SSP1-2.6 MRI-ESM2-0            # paper config
#   scripts/run_imogen_engine.sh SSP5-8.5 IPSL-CM6A-LR --tag sens   # GCM swap
#   TRUNK_BIN=.../build_b824/guess scripts/run_imogen_engine.sh SSP2-4.5 GFDL-ESM4
#
# Env overrides: TRUNK_BIN (default forks/trunk_r13078/build_oceanfix/guess)
#
# SSPs: SSP1-2.6 SSP2-4.5 SSP3-7.0 SSP4-6.0 SSP5-8.5
# GCMs: MRI-ESM2-0 GFDL-ESM4 IPSL-CM6A-LR MPI-ESM1-2-HR UKESM1-0-LL
#       (each has imogen/patterns/CEN_CMIP6_MOD_<GCM>/ + <GCM>_ebm.nml; all on
#        the shared 1631 patterns_gridlist, so the regrid chain is GCM-agnostic)
#
# - Daniel Bampoh / session 18 (2026-06-06). See notes/PRODUCTION_RUN_CONFIG.md.
# =============================================================================
set -uo pipefail

usage() { echo "Usage: $0 <SSP> <GCM> [--tag TAG] [--no-regrid] [--inputs-csv PATH] [--src-dir DIR]" >&2; exit 1; }

[ $# -ge 2 ] || usage
SSP="$1"; GCM="$2"; shift 2
TAG="engine"; DO_REGRID=1; INPUTS_CSV=""; SRC_DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --tag) TAG="$2"; shift 2;;
    --no-regrid) DO_REGRID=0; shift;;
    --inputs-csv) INPUTS_CSV="$2"; shift 2;;
    --src-dir) SRC_DIR="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; usage;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRUNK_BIN="${TRUNK_BIN:-${ROOT}/forks/trunk_r13078/build_oceanfix/guess}"
PATT_DIR="${ROOT}/imogen/patterns/CEN_CMIP6_MOD_${GCM}"
EBM_NML="${ROOT}/imogen/patterns/${GCM}_ebm.nml"
SRC_DIR="${SRC_DIR:-${ROOT}/forks/trunk_r13078_runs/${SSP}}"
INPUTS_CSV="${INPUTS_CSV:-${ROOT}/intermediary_py/imogen_ghg_controller/outputs/imogen_inputs/imogen_inputs_${SSP}.csv}"
ADAPTER="${ROOT}/tools/imogen_inputs_to_lpjg_format.py"
RUN="${ROOT}/forks/trunk_r13078_runs/${SSP}_${GCM}_${TAG}"
INP="${RUN}/imogen_inputs"
COMMON="${RUN}/Common-directory"
HSHAKE="${COMMON}/LPJG_main/IMOGEN"
OUTDIR="${COMMON}/IMOGEN/output"
LOG_DIR="${ROOT}/logs"; mkdir -p "${LOG_DIR}"
TS="$(date '+%Y%m%d_%H%M%S')"

# ---- pre-flight ----
[ -x "$TRUNK_BIN" ]                 || { echo "FATAL: engine binary missing: $TRUNK_BIN"; exit 2; }
[ -d "$PATT_DIR" ]                  || { echo "FATAL: pattern dir missing: $PATT_DIR (GCM=$GCM)"; exit 2; }
[ -f "$EBM_NML" ]                   || { echo "FATAL: EBM namelist missing: $EBM_NML"; exit 2; }
[ -d "$SRC_DIR" ]                   || { echo "FATAL: source run dir missing: $SRC_DIR"; exit 2; }
[ -f "$SRC_DIR/main_engine_only.ins" ] || { echo "FATAL: main_engine_only.ins missing in $SRC_DIR"; exit 2; }
[ -f "$INPUTS_CSV" ]                || { echo "FATAL: imogen_inputs CSV missing: $INPUTS_CSV"; exit 2; }
case "$RUN" in *_"${GCM}"_*) : ;; *) echo "FATAL: refusing run dir without GCM tag: $RUN"; exit 2;; esac

# ---- parse the GCM's EBM scalars from the namelist ----
nml_val() { grep -iE "^[[:space:]]*$1[[:space:]]*=" "$EBM_NML" | head -1 | sed -E 's/.*=[[:space:]]*//; s/[[:space:]].*//'; }
KAPPA_O="$(nml_val KAPPA_O)"; F_OCEAN="$(nml_val F_OCEAN)"
LAMBDA_L="$(nml_val LAMBDA_L)"; LAMBDA_O="$(nml_val LAMBDA_O)"; MU="$(nml_val MU)"
for v in KAPPA_O F_OCEAN LAMBDA_L LAMBDA_O MU; do
  [ -n "${!v}" ] || { echo "FATAL: could not parse $v from $EBM_NML"; exit 3; }
done

echo "================================================================================"
echo "run_imogen_engine.sh  SSP=$SSP  GCM=$GCM  tag=$TAG  $(date '+%H:%M:%S')"
echo "  binary : $TRUNK_BIN"
echo "  patterns: $PATT_DIR"
echo "  EBM    : KAPPA_O=$KAPPA_O F_OCEAN=$F_OCEAN LAMBDA_L=$LAMBDA_L LAMBDA_O=$LAMBDA_O MU=$MU"
echo "  run dir: $RUN  (paper dir $SRC_DIR is read-only)"
echo "================================================================================"

# ---- 1. build the 4 IMOGEN inputs from the integrated-emissions CSV ----
echo "[1] adapter: $INPUTS_CSV -> $INP"
rm -rf "$RUN"; mkdir -p "$INP" "$OUTDIR" "$HSHAKE"
python "$ADAPTER" --input "$INPUTS_CSV" --output "$INP" > "${LOG_DIR}/run_imogen_engine_${SSP}_${GCM}_${TAG}_adapter_${TS}.log" 2>&1 \
  || { echo "FATAL: adapter failed (see log)"; exit 4; }

# ---- 2. clone .ins set + rewire FILE_* / DIR_PATT / EBM ----
echo "[2] clone .ins from $SRC_DIR + rewire FILE_* / DIR_PATT / EBM"
cp "$SRC_DIR"/*.ins "$RUN"/
REL_PATT="../../../imogen/patterns/CEN_CMIP6_MOD_${GCM}"
for INS in "$RUN/imogen_intermediary.ins" "$RUN/main_engine_only.ins"; do
  sed -i -E "s#^FILE_SCEN_EMITS[[:space:]]+\".*#FILE_SCEN_EMITS         \"${INP}/co2_anthro_emissions.txt\"#"            "$INS"
  sed -i -E "s#^FILE_CH4_N2O_EMITS[[:space:]]+\".*#FILE_CH4_N2O_EMITS      \"${INP}/ch4_n2o_anthro_emissions.txt\"#"     "$INS"
  sed -i -E "s#^FILE_LPJG_FLUX[[:space:]]+\".*#FILE_LPJG_FLUX          \"${INP}/imogen_lpjg_flux.txt\"#"                 "$INS"
  sed -i -E "s#^FILE_LPJG_CH4_N2O_FLUX[[:space:]]+\".*#FILE_LPJG_CH4_N2O_FLUX  \"${INP}/imogen_lpjg_ch4_n2o_flux.txt\"#" "$INS"
  sed -i -E "s#^DIR_PATT[[:space:]]+\".*#DIR_PATT        \"${REL_PATT}\"   ! ${GCM} (run_imogen_engine.sh)#"             "$INS"
  sed -i -E "s#^KAPPA_O[[:space:]]+[0-9.]+.*#KAPPA_O         ${KAPPA_O}   ! ${GCM}-calibrated (run_imogen_engine.sh)#"   "$INS"
  sed -i -E "s#^F_OCEAN[[:space:]]+[0-9.]+.*#F_OCEAN         ${F_OCEAN}   ! ${GCM}-calibrated#"                          "$INS"
  sed -i -E "s#^LAMBDA_L[[:space:]]+[0-9.]+.*#LAMBDA_L        ${LAMBDA_L}   ! ${GCM}-calibrated#"                        "$INS"
  sed -i -E "s#^LAMBDA_O[[:space:]]+[0-9.]+.*#LAMBDA_O        ${LAMBDA_O}   ! ${GCM}-calibrated#"                        "$INS"
  sed -i -E "s#^MU[[:space:]]+[0-9.]+.*#MU              ${MU}   ! ${GCM}-calibrated#"                                    "$INS"
done
echo "    DIR_PATT + EBM now in imogen_intermediary.ins:"
grep -E "^(DIR_PATT|KAPPA_O|F_OCEAN|LAMBDA_L|LAMBDA_O|MU)[[:space:]]" "$RUN/imogen_intermediary.ins" | sed 's/^/      /'

# ---- 3. bootstrap handshake (verbatim from run_trunk_engine_only.sh) ----
echo "[3] bootstrap handshake + done-marker sidecar"
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

# ---- 4. engine run ----
echo "[4] engine: $TRUNK_BIN -input imogencfx main_engine_only.ins"
( while true; do touch "$HSHAKE/done" 2>/dev/null; sleep 1; done ) &
SIDE=$!
trap 'kill $SIDE 2>/dev/null; wait $SIDE 2>/dev/null; rm -f "$HSHAKE/done" 2>/dev/null' EXIT
cd "$RUN"
"$TRUNK_BIN" -input imogencfx main_engine_only.ins > "$RUN/engine_run.log" 2>&1
EC=$?
kill $SIDE 2>/dev/null; wait $SIDE 2>/dev/null
NY=$(ls -d "$OUTDIR"/[12]*/ 2>/dev/null | wc -l)
echo "    engine exit=$EC (99/expected at YEAR1==2100 over-shoot); native year-dirs=$NY (expect ~202)"
[ "$NY" -ge 200 ] || { echo "FATAL: engine produced too few year-dirs ($NY); see $RUN/engine_run.log"; exit 5; }

# ---- 5. optional chained FastRegrid (NN 1631->3698, IDW 3698->62892) ----
if [ "$DO_REGRID" -eq 1 ]; then
  echo "[5] FastRegrid delta_b_variant (NN 1631->3698, IDW 3698->62892)"
  bash "$ROOT/scripts/run_fastregrid.sh" "${SSP}_${GCM}_${TAG}" delta_b_variant \
    > "${LOG_DIR}/run_imogen_engine_${SSP}_${GCM}_${TAG}_fastregrid_${TS}.log" 2>&1 \
    || { echo "FATAL: FastRegrid failed (see log)"; exit 6; }
  N6=$(ls -d "$COMMON/IMOGEN/output_62892_cppengine/"[12]*/ 2>/dev/null | wc -l)
  echo "    62892 year-dirs: $N6 (expect ~201)"
else
  echo "[5] --no-regrid: skipping FastRegrid (native 1631 library only)"
fi
echo "######## run_imogen_engine.sh DONE: $SSP / $GCM / $TAG  $(date '+%H:%M:%S') ########"
