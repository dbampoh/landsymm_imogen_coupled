# `lpjguess/` — LPJ-GUESS LandSyMM fork

Will hold the LPJ-GUESS dynamic global vegetation model with the LandSyMM
fork modifications. To be populated at **step 1** of the rebuild plan
(`EXECUTION_PLAN.md` §V.1).

**Source:** the standalone LandSyMM fork at
`lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/` (NOT
`Integrations/trunk/trunk_r13078/` from the predecessor framework, to
avoid the `exit(200)` regression and 5 cosmetic comment touches; see
`COUPLED_MODEL_INVESTIGATION.md` §4.1.10).

**Phase 2 follow-on:** integrated LTS as a switchable backend
(`lpjguess_lts/` parallel directory; see EXECUTION_PLAN §II.11).

**Step 7** applies the seven LPJ-GUESS coupling break-point fixes
(`exit(200)` removal; `imogen_intermediary.ins` `IMOGEN/ouput/` typo;
`climatemodel.cpp` polling-loop guards; `imogen_input.cpp:728`
`ndep.getndep` uncomment; etc.).

**Step 8** adds the LPJG-side handshake writer
(`modules/imogenoutput.cpp`) for the `imogen_lpjg_flux.txt`,
`imogen_lpjg_ch4_n2o_flux.txt`, `imogen_lpjg.txt`, and `done` files
that close the LPJG → IMOGEN feedback in tight-coupled mode.

**Step 9.5** wires the LPJG-side consumers for `Rh_anom.dat`,
`W_anom.dat`, `Tmin_anom.dat`, `Tmax_anom.dat` produced by the IMOGEN
engine.

See `EXECUTION_PLAN.md` Part V for the full rebuild sequence.
