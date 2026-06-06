#!/usr/bin/env bash
# reproduce_corrected_climate.sh -- Identical-emulator cool-bias FIX rollout.
# For each SSP: build Arm-A (integrated) inputs -> run the FIXED C++ engine (build_oceanfix)
# at 1631 -> chained FastRegrid (NN 1631->3698, IDW 3698->62892), all in an ISOLATED dir
# (forks/trunk_r13078_runs/<SSP>_armB_armArepro/). The paper's <SSP>/ dirs are NEVER touched.
set -uo pipefail
ROOT="/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm"
DIAG="$ROOT/scripts/Paper_Analysis/comparative_analysis_GMD_paper/identical_emulator_diagnostic"
export TRUNK_BIN="$ROOT/forks/trunk_r13078/build_oceanfix/guess"   # the FIXED engine
[ -x "$TRUNK_BIN" ] || { echo "FATAL: fixed binary missing: $TRUNK_BIN"; exit 2; }

SSPS="${1:-SSP1-2.6 SSP2-4.5 SSP3-7.0 SSP4-6.0}"
for SSP in $SSPS; do
  echo "############################## $SSP : START $(date '+%H:%M:%S') ##############################"
  echo "#### [$SSP] 1/3 build Arm-A inputs (integrated emissions through adapter)"
  python "$ROOT/tools/imogen_inputs_to_lpjg_format.py" \
    --input "$ROOT/intermediary_py/imogen_ghg_controller/outputs/imogen_inputs/imogen_inputs_${SSP}.csv" \
    --output "$DIAG/armB_inputs/${SSP}_armArepro" > "$ROOT/logs/repro_${SSP}_adapter.log" 2>&1 \
    || { echo "FATAL adapter $SSP"; exit 3; }
  echo "#### [$SSP] 2/3 fixed-engine 1631 run (build_oceanfix)"
  bash "$DIAG/run_armB.sh" "$SSP" armArepro > "$ROOT/logs/repro_${SSP}_engine.log" 2>&1 \
    || echo "   (engine exit nonzero -- expected at 2100 over-shoot)"
  NY=$(ls -d "$ROOT/forks/trunk_r13078_runs/${SSP}_armB_armArepro/Common-directory/IMOGEN/output/"[12]*/ 2>/dev/null | wc -l)
  echo "   [$SSP] engine year-dirs: $NY (expect ~202)"
  echo "#### [$SSP] 3/3 FastRegrid delta_b_variant (NN 1631->3698, IDW 3698->62892)"
  bash "$ROOT/scripts/run_fastregrid.sh" "${SSP}_armB_armArepro" delta_b_variant \
    > "$ROOT/logs/repro_${SSP}_fastregrid.log" 2>&1 || { echo "FATAL fastregrid $SSP"; exit 4; }
  N6=$(ls -d "$ROOT/forks/trunk_r13078_runs/${SSP}_armB_armArepro/Common-directory/IMOGEN/output_62892_cppengine/"[12]*/ 2>/dev/null | wc -l)
  echo "############################## $SSP : DONE $(date '+%H:%M:%S')  (62892 year-dirs: $N6) ##############################"
done
echo "######## ALL CORRECTED CLIMATES COMPLETE ########"
