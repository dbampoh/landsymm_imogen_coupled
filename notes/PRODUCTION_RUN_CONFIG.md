# Production-run configuration reference

**Version**: v1.0 (initial draft)
**Last updated**: 2026-06-08 (session 18 cluster re-run — **🎉 TRACK 2 ECOSYSTEM RE-RUN ✅ COMPLETE on corrected climate**)

> **🎉 RE-RUN COMPLETE (2026-06-08, session 18) — supersedes the 2026-06-03 set.** All 6 runs re-ran clean on the corrected climate (incl. SW-floor) on **4 genius nodes / 509 ranks**: HIST (`SSP2-4.5_cluster_hist/output-2026-06-07/`, state 509/509) + 5 SCEN (`<SSP>_cluster_scen/output-2026-06-0[78]/`), 62,512 cells each, `COMPLETED` 0:0. Same validated config as 2026-06-03 — **only the input climate changed** (the 509-rank + per-rank-stdout mechanics below are unchanged); ran on genius rather than milan (weber-j freed genius). SW verified `min=0` (all 5 SSPs/years) pre-launch; re-run sailed past the year-1977 SW-failure point. Sensibility ✅: cmass gain SSP1-2.6 +0.51 < SSP3-7.0 +0.60 < SSP2-4.5 +0.61 < SSP4-6.0 +0.68 < SSP5-8.5 +0.71 kgC/m² (CO₂-fertilization-vs-warming tradeoff, now climate-responsive; 2020 ~3.41 identical; 0 NaN/neg). ⚠️ ~27 GB benign `warnings.txt` per output → exclude from rsync. Detail: CHANGELOG 2026-06-08.



> **⚠️ CLIMATE-FORCING CORRECTION (2026-06-06, session 18) — the v1.0 climate library is being regenerated; the 2026-06-03 ecosystem runs below used the pre-correction climate and must be re-run.** Five pre-existing defects fixed (detail: CHANGELOG 2026-06-06). **Engine**: `gcm_anlg` oceanfix (persistent `dtemp_o` + once-per-year `dtemp_l` to all 12 months) → +0.4 K → ~+15 K century warming; applied to trunk_r13078 + lpjguess; canonical fixed binary `forks/trunk_r13078/build_oceanfix/guess` (build/build_b824/lpjguess build+build_mpi also rebuilt; paper binary backed up). **Patterns**: `tools/cmip6_nc_to_cmip5_ascii.py` precip ×86400 fix; all 5 CMIP6 sets regenerated. **Baseline**: NEW `tools/crujra_to_imogen_baseline.py` rebuilt `imogen/CRUNCEP_1960_1989/` single-source from CRU-JRA v2.4 (RH/wind/pressure now physical — were zero lineage-wide; BLAZE consumes RH+wind; old baseline backed up). **EBM (per-GCM)**: use the calibrated scalars from `imogen/patterns/<GCM>_ebm.nml` (MRI-ESM2-0: `KAPPA_O 500 / LAMBDA_L 1.549 / LAMBDA_O 1.347 / MU 1.448 / F_OCEAN 0.708`) — NOT the generic HadCM3 defaults (0.4/1.9/1.78/280). **GCM switch**: `scripts/run_imogen_engine.sh <SSP> <GCM>` (NEW) auto-applies `DIR_PATT` + EBM per GCM (MRI for the paper; GFDL/IPSL/MPI/UKESM for sensitivity), then chains FastRegrid 1631→NN 3698→IDW 62892. Corrected δ-B-variant 62892 climate regenerated in `forks/trunk_r13078_runs/<SSP>_armB_armArepro/`; **NEXT**: rsync to cluster + re-run the 6 ecosystem runs below with this corrected climate. **⚠️ 6th correction (2026-06-07): SHORTWAVE non-negativity floor.** The cluster HIST re-run failed ~1977 (all ranks exit 99) on `interp_monthly_means_conserve` rejecting tiny negative SW (min ≈ −0.64 W m⁻²) in the corrected δ-B `SW_anom.dat`. Root cause: the field reconstruction floors precip/RH/DTEMP/wind but never shortwave — an original-Fortran trait (faithful in the C++ port; NOT the oceanfix), latent under CRUNCEP, exposed by the CRU-JRA near-zero-winter baseline. FIX: `MAX(...,0)`/`std::max(...,0.0)` added to all three engine sources + all 5 C++ binaries + the Fortran exe rebuilt; existing library brought to ≥0 by the equivalent post-hoc clamp `scripts/clamp_sw_anom_nonneg.py` (3015 files, reversible manifest). Negligible (mean-rsds shift ≤0.0011 W m⁻²) — paper/ecosystem unaffected. **Re-ship the clamped `SW_anom.dat` to the cluster (or the cluster applies the identical `<0→0` clamp) before re-running.** Detail: CHANGELOG 2026-06-06 entry (7).

> **🎉 PRODUCTION COMPLETE (2026-06-03, session 13 day 5)** *(used the PRE-CORRECTION climate; superseded by the 2026-06-06 correction above — re-run required)*: All 6 runs done + banked + physically verified on owl. **As-run config** (differs from the original strategy below in two operational ways discovered during launch): (1) **509 ranks, not 512** — the gridlist split `ceil(62512/512)=123` leaves ranks 509-511 empty, and empty-gridlist ranks fail `IMOGENCFXInput::init()` → `MPI_Finalize` → deadlock vs the working ranks' `framework()` `MPI_Barrier` (Rule #9 #37); launching at `--ntasks=509` (8 milan nodes; ranks 0-508 → run1-509) gives zero empty ranks + preserves the chunk-123 cell→rank→state map → restart-consistent. (2) **per-rank stdout redirect** in `mpi_run_guess.sh` (Rule #9 #36) — without it all ranks' verbose stdout funnels into one shared `guess_x.o` (hit 20 GB) → `pipe_write` throttle. With both fixes each run completed clean in ~1.5 h at full 8-node load. milan/8×64 used (genius/4×128 equivalent). Outputs: HIST 32 GB + 5 SCEN ~7.3-7.4 GB each (62512 cells, 2020-2100). All SCENs restart from shared SSP2-4.5 HIST 2020 state. See CHANGELOG 2026-06-03 + FOLLOWUPS #36/#37 for full detail.

> **POST-BLOCK-8.3-FULL-ADDENDUM (2026-05-29 session 13 day 1 close)** — *strategy as planned; superseded operationally by the 509-rank as-run config above*:

> **POST-BLOCK-8.3-FULL-ADDENDUM (2026-05-29 session 13 day 1 close)**:
>
> Track 2 production strategy LOCKED IN at Block 8.3 close FULL addendum. 6 refinements:
>
> | Component | State (post-addendum) |
> |---|---|
> | **Production gridlist** (canonical) | `data/gridlist/gridlist_in_62892_and_climate_and_PLUMmask.txt` (62,512 cells; production gridlist ∩ PLUM SSP scenario LU coverage; PLUM-mask-aligned for clean symmetric HIST + SCEN output). Old `gridlist_in_62892_and_climate.txt` (62,538 cells) preserved for backward compat per Rule #10 amendment-vs-rewrite. |
> | **HIST sharing strategy** (Track 1-style) | **1 shared HIST for SSP2-4.5** (middle-of-the-road business-as-usual) + **5 SCEN restart** from `SSP2-4.5_cluster_hist/state/`. 4 SCEN main.ins (SSP1-2.6, SSP3-7.0, SSP4-6.0, SSP5-8.5) state_path retargeted at addendum commit. SSP2-4.5 SCEN already correctly points at its own _cluster_hist/state/. Original lines preserved at `.preB83close_track1.bak`. Saves ~9 days cluster wall (~3-4 days total vs ~13 days for original 5 SSP-specific HIST plan). |
> | **Allocation defaults** | `setup_run_tseq.sh` defaults: `NNODES=8`, `CPU_PER_NODE=64`, `PARTITION=milan`, `WALLTIME=3-00:00:00` (3-day max for milan + genius). milan/8×64=512 ranks; **interchangeable** with genius/4×128=512 (also 512 ranks; state-restart-compatible across partition variants). Drop-in alternative: `NNODES=4 CPU_PER_NODE=128 PARTITION=genius ./setup_run_tseq.sh`. |
> | **Estimated production wall** | HIST ~52h on milan/8×64 / ~38h on genius/4×128 (within 3-day max); Phase 3a SCEN ~10h × 4 (parallel-ready: SSP1, SSP2, SSP3, SSP5); Phase 3b SCEN ~10h × 1 (SSP4-6.0 after workstation remediation). Total ~3-4 days cluster wall. |
> | **B64 NEW audit-item filed** | SSP4-6.0 IMOGEN HIST climate anomaly hypotheses investigation. **Hypothesis 2 (intermediary_py-vs-legacy-CMIP6 provenance) ✅ RESOLVED** at workstation-agent verification 2026-05-29 ~01:00 CEST (provenance chain clean; intermediary_py-derived anthro emissions; legacy IIASA paths INERT; FILE_NON_CO2_VALS prescribed-RF design intentional per Huntingford2010+Smith2018 GMD). **Hypothesis 1 (per-SSP nonco2 RF historical file divergence) ✅ CONFIRMED + REMEDIATION PLANNED** at workstation-agent diagnostic 2026-05-29 ~01:30 CEST: 5-SSP RF cross-comparison at year 2000 → ssp126/245/370/585 = 1.133761 W/m² (4-way byte-identical canonical CMIP6 historical) vs **ssp460 = 1.369924 W/m² (~21% higher; synthetic monotonic ~2%/yr exponential growth, NOT real CMIP6 historical with Pinatubo signal)**. Root cause: ssp460 file has corrupted historical (1850-2014) from Tier-2 SSP4-6.0 generation pathway gap; scenario period (2015-2100) is reasonable. Remediation (~30-45 min total wall on workstation): backup → splice shared 1850-2014 historical from ssp126 + ssp460 scenario 2015-2100 → re-run trunk-cpp-engine SSP4-6.0 → re-FastRegrid → re-rsync 18 GB SSP4-6.0 climate library to cluster. Hypothesis 3 (GCM pattern data quirk) MOOT since Hyp 1 explains anomaly fully. **Production launch implications**: Phase 1 + Phase 3a (4-of-5 SCEN: SSP1, SSP2, SSP3, SSP5) UNAFFECTED + can launch as planned; Phase 3b (SSP4-6.0 SCEN) DEFERRED until corrected SSP4-6.0 climate library is rsync'd post-remediation; workstation remediation overlaps cluster Phase 1 or 3a → 0 calendar-day delta on cluster side. See `notes/FOLLOWUPS.md` B64 row + `_chat_artifacts/b8_3_cluster_smoke_2026-05-28/B8_3_evaluation_2026-05-28.md` §13.8.6 for full detail. |
>
> **Track 2 launch sequence** (FINAL; revised post-Hypothesis-1-confirmation): Phase 1 (1× SSP2-4.5 HIST) → Phase 2 (wait for state/ populated) → Phase 3a (4-of-5 SCEN parallel: SSP1, SSP2, SSP3, SSP5) → Phase 3b (SSP4-6.0 SCEN after workstation remediation completes + corrected library rsync'd to cluster). See `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §1 POST-BLOCK-8.3 banner amendment + `_chat_artifacts/b8_3_cluster_smoke_2026-05-28/B8_3_evaluation_2026-05-28.md` §13 FULL addendum.
>
> ---
>
> **PRIOR POST-BLOCK-8.2.5-FULL + Block 8.4 pre-cluster prep addendum (2026-05-27 session 12 day 2; preserved for forensic value per Rule #10 amendment-vs-rewrite)**:
>
> Block 8.2.5 FULL CLOSE landed BOTH switchable-regrid pipelines (δ-B Fortran + δ-B-variant trunk-C++) + 50-cell biome-stratified production-config Phase F smoke side-by-side acceptance + **Phase G user choice = δ-B-variant (trunk-C++ engine throughout)** for v1.0 GMD paper Track 2 cluster production runs. Cluster production .ins authored at this commit:
>
> | Component | State |
> |---|---|
> | δ-B-variant 62892-grid library (5 × 18 GB; **CHOSEN for paper**) | `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/` (gitignored; rsync workstation→cluster pre-Track-2-production) |
> | δ-B Fortran 62892-grid library (5 × 18 GB; v1+ switchable alternative) | `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892/` (gitignored) |
> | 10 cluster production run-dirs (5 SSPs × hist+scen) | `forks/trunk_r13078_runs/<SSP>_cluster_<phase>/` (14 .ins files each + setup_run_tseq.sh + state/ subdir for _hist) — committed to git; production knobs nyear_spinup=500 / freenyears=100 / npatch=25 / gridlist=62538-cell / save_state=1+save_years="2020" hist → restart=1+restart_year=2020 scen per user's wpeat hist+ssp{126,…}_wpeat reference |
> | Cluster launch infrastructure | `scripts/cluster/setup_run_tseq.sh` (template; cp'd to each cluster run-dir) + revamped `scripts/cluster/setup_run.sh` (named-flag CLI) + `scripts/cluster/run_coupled.sbatch` (alternative unified launcher); both paths documented at `scripts/cluster/README.md` |
> | Cluster pre-flight checklist | git pull cluster mirror to v0.24.0 tag → cmake+make trunk binary at `forks/trunk_r13078/build_owl/guess` → rsync 90 GB δ-B-variant 62892 library workstation→cluster → optional `./guess` symlinks per Track-1 muscle memory → block 8.3 cluster smoke → block 8.5 MPI pre-flight → Track 2 production runs |
>
> Full evidence: `_chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_evaluation_2026-05-27.md` (~400 LOC; 8-gate scorecard for Phase D + E + F + Phase G chosen-pipeline disclosure + Rule #9 #23-#33 + Rule #10 #25 + §5 per-biome differential + §6 Methods §2.2 disclosure text). Tag `v0.24.0-switchable-regrid-strategy-complete` reserved for block 8.2.5 close (this commit).

> **POST-BLOCK-8.2 5-SSP CO2 trajectory addendum (2026-05-23 session 10 day 1 close)**:
>
> All 5 SSP-RCP scenarios now have C++ engine libraries produced at `runs/<SSP>/Common-directory/IMOGEN/output/` (202 year-dirs 1900-2101 each; ~443 MB each; ~2.2 GB total; γ-physically cp'd to forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/ per block 8.2 phase E). Per `--backbone intermediary-py` (Option B; Decision #1; RCMIP/CMIP6-backboned anthropogenic + pre-baked offline trunk_r13078 LPJG natural fluxes), all 5 SSPs use **intermediary_py adapter outputs** (NOT legacy IIASA). CO2 trajectory physical sensibility verified across all 5 SSPs vs IPCC AR6 / Friedlingstein 2025 GCB published ranges:
>
> | SSP | CO2 1900 (ppm; B39 Law Dome init) | CO2 2050 (ppm; mid-century) | CO2 2100 (ppm; endpoint) | IPCC AR6 / Friedlingstein 2025 reference (endpoint) | Acceptance |
> |---|---|---|---|---|---|
> | SSP1-2.6 | 295.844 | 472.872 | **427.62** (peak-then-decline ✅) | ~390-470 ppm (peak-then-decline) | ✅ PASS |
> | SSP2-4.5 | 295.844 | 512.143 | **590.815** | ~580-630 ppm | ✅ PASS |
> | SSP3-7.0 | 295.844 | 548.071 | **826.34** | ~830-900 ppm | ✅ PASS (low end; well within model uncertainty) |
> | SSP4-6.0 | 295.85 | 528.073 | **631.473** | ~660-720 ppm | ✅ PASS (low end; well within model uncertainty) |
> | SSP5-8.5 | 295.844 | 575.746 | **1092.59** | ~900-1100 ppm (peak) | ✅ PASS (peak range) |
>
> All 5 SSPs sit within or near-bound the IPCC AR6 / Friedlingstein 2025 GCB published ranges per Methods §2.2 narrative. SSP1-2.6 correctly shows the canonical peak-then-decline trajectory (peak ~2050 at ~472 ppm; decline to ~428 ppm by 2100 from negative emissions). SSP5-8.5 peak ~131 GtCO2/yr at ~2090 (per Friedlingstein 2025 GCB ~120-140 GtCO2/yr published range) drove **Rule #9 datapoint #18 fix** at `tools/imogen_inputs_to_lpjg_format.py:117-145`: CO2_EFOS_Mt + CO2_total_Mt SANITY_RANGES upper bounds bumped 100,000 → 200,000 Mt CO2/yr (200 GtCO2/yr; generous margin for SSP5-8.5 + future-scenario extensions while still flagging 1000x-error outliers). See `_chat_artifacts/b8_2_engine_libraries_2026-05-22/B8_2_engine_libraries_evaluation_2026-05-22.md` §1.5 + §3 for full Phase D + Rule #9 evidence.

**Earlier value**: 2026-05-19 (session 6; B19+B20 close-out era; pre-local-v1-verification-window)
**Status**: 🔧 INITIAL DRAFT — to be iteratively refined as B36 + B37 + B39 + B40 (local v1 verification window) and 17c.1+ cluster phase 1 inform the v1.0 paper publication readiness checklist.

**Audience**: anyone (current + future maintainers) needing to:
- Run the v1.0 coupled model in production-style configuration on either local workstation OR HPC cluster
- Understand the gap between the smoke-test setup (`runs/SSP1-2.6/main.ins`) and the production-run setup
- Configure LU forcing for the v1.0 paper publication (the updated `_peatland` variant)
- Decide which `-input` module to use for each run-type
- Plan the v1.0 paper publication run sequence

**Companions**:
- `runs/SSP1-2.6/main.ins` — the canonical smoke-test main.ins (current rebuild)
- `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/main.ins` — example production-style main.ins (historical + SSP1-2.6)
- `notes/FOLLOWUPS.md` rows B41 + B42 + B43 — audit-item tracking
- `notes/B19.md` — closed-loop verification milestone (B19 + B20 = v1.0 magnitude validation)
- `docs/scientific_framework.md` — coupled-model scientific architecture; §5 F-10 caveat + §5.3 natural-flux mutual exclusion
- `EXECUTION_PLAN.md` row 17c — cluster-phase plan

---

## 1. Why this document exists

The v1.0 coupled-model rebuild has so far operated under a **stripped-down smoke-test configuration** in `runs/SSP1-2.6/main.ins` to enable rapid iteration during the rebuild. The smoke configuration is operationally distant from what the v1.0 paper publication needs:

- 4-cell `gridlist_test2.txt` (smoke) vs full 62892-cell `gridlist_in_62892_and_climate.txt` (production)
- 1-year `nyear_spinup` (smoke) vs 500-year (production)
- 1 patch (smoke) vs 25 patches (production)
- `firemodel "NOFIRE"` + empty `file_simfire` (smoke) vs `firemodel "BLAZE"` + actual SimFire binary (production)
- No popdens NetCDF + no wet/dry NHx+NOy ndep NetCDFs (smoke) vs all four production NetCDFs
- Legacy `version_A/.../SSP1_RCP26_concatenated/LU_*` LU forcing (smoke) vs updated `_peatland`-tagged LU forcing at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/` (production)
- 2-year window (smoke; 1900-1901) vs full 1900-2100 (production)

This document captures the full smoke→production migration delta, the updated LU forcing dataset paths, the cluster ↔ local path translation, the input-module evolution (`cf` → `cfx` → `imogencfx`), and the v1.0 paper publication run sequence. It exists to ensure that the architectural picture the user shared at session 5 (2026-05-18 evening) + session 6 (2026-05-19 morning) is preserved in the rebuild project's documentation rather than living only in the chat handoff.

---

## 2. Smoke→production parameter delta

### 2.1 main.ins

| Parameter | Smoke (current `runs/SSP1-2.6/main.ins`) | Production (target for v1.0 paper) | Source of production value |
|---|---|---|---|
| `firsthistyear` / `lasthistyear` | 1900 / 1901 | 1900 / 2020 (historical) → 2021 / 2100 (SSP scenario) | matches LU forcing year coverage |
| `firstoutyear` / `lastoutyear` | 1900 / 1901 | 1900 / 2020 → 2021 / 2100 | full publication time series |
| `file_gridlist` | `data/gridlist/gridlist_test2.txt` (4 cells) | `gridlist_in_62892_and_climate.txt` (62538 valid cells from 62892 nominal) | `integrated-4.1-ins2_landsymm_hist:35` |
| `file_gridlist_cf` | (matches gridlist) | (matches gridlist) | input-module specific |
| `file_soildata` | `soilmap_center_interpolated.remapv10_old_62892_gL.dat` | (same; production soilmap covers full 62892-cell production gridlist) | production soilmap is correct as-is |
| `nyear_spinup` | 1 (B19 ADDENDUM smoke) | **500** | `integrated-4.1-ins2_landsymm_hist:40` |
| `freenyears` | (smoke uses LPJG default) | **100** | `integrated-4.1-ins2_landsymm_hist:41` |
| `firemodel` | `"NOFIRE"` | **`"BLAZE"`** | production setup default |
| `npatch` | 1 | **25** | LPJG production default |
| `run_landcover` | 1 | 1 (already correct in smoke) | matches |
| `file_temp` etc. (climate) | empty (cf reader not used) | (cfx mode) ISIMIP3b NetCDFs OR (imogencfx mode) IMOGEN-engine ASCII per-year | depends on input module |
| `file_co2` | empty (cf reader not used) | (cfx mode) `co2_histssp126_annual_1850_2100.txt` OR (imogencfx mode) IMOGEN-engine `CO2.dat` per-year | depends on input module |
| `state_path` / `save_state` / `restart` | not used (smoke) | historical run saves at year 2020; SSP runs restart from the historical state | per integrated-4.1-ins2_landsymm_{hist,ssp126} |
| **`CO2_INIT_PPMV` / `CH4_INIT_PPBV` / `N2O_INIT_PPBV`** (engine seed; in `imogen_intermediary.ins`) | 296.1 / 875.6 / 277.4 (B39 ✅ DONE 2026-05-19 evening session 7 continuation — set to Law Dome 1900 per MacFarling Meure 2006 + Meinshausen 2017; CO2 fix removes the -3.5 to -4.2% drift observed at B19 Phase 4) | **MUST match the production YEAR1 epoch** — for 1900-start production runs (the v1.0 paper-publication default), use 296.1 / 875.6 / 277.4 as in smoke; for 1850-start spinup runs, use 284.3 / 815 / 273.0 per `docs/scientific_framework.md` §6.1 cross-reference table; for 2005-start scenario runs, use 379.0 / 1774 / 319.0 per same table | **`docs/scientific_framework.md` §6.1 per-YEAR1 atmospheric-concentration seed table (NEW B39)** + `notes/B39.md` canonical landing record |

### 2.2 landcover.ins + crop.ins

| Parameter | Smoke | Production (v1.0 paper) | Where to get the production file |
|---|---|---|---|
| `file_lu` | legacy `version_A/.../LU_SSP1_RCP26_1901_2100_final.txt` | **`LU.remapv10_old_62892_gL_peatland.txt`** (historical) + **`landcover_peatland.txt`** (SSP) | `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/output_hildaplus_remap_10b_3/remaps_v10_old_62892_gL/` (hist) + `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/<SSPx_RCPyy>/s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/` (SSP) |
| `file_lucrop` | legacy `cropfracs_SSP1_RCP26_1901_2100_final.txt` | `cropfracs.remapv10_old_62892_gL.txt` (historical) + `cropfractions.txt` (SSP) | same dirs as above |
| `file_Nfert` | legacy `nfert_SSP1_RCP26_1901_2100_final.txt` | `nfert.remapv10_old_62892_gL.txt` (historical) + `nfert.txt` (SSP) | same dirs as above |
| `file_irrigintens` | legacy `irrig_SSP1_RCP26_1901_2100_final.txt` | (historical: NO irrig file — use empty `""`) + `irrig.txt` (SSP) | same dirs as above |

### 2.3 Auxiliary input files (cfx + imogencfx production-only)

| Parameter | Smoke value | Production value | Where |
|---|---|---|---|
| `file_simfire` | `""` | `SimfireInput.bin` | `/media/bampoh-d/lpjg_input/input/fire/SimfireInput.bin` (local) ↔ `/bg/data/lpj/LPJ-GUESS/input/fire/SimfireInput.bin` (cluster) |
| `file_popdens` | (not set; firemodel=NOFIRE) | population NetCDF for SimFire ignition | `/media/bampoh-d/ISIMIP/inputs/pop/lpjg-popd/...` (local; user-confirmed canonical at block 8.0.3 follow-up 2026-05-20) ↔ `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/pop/lpjg-popd/...` (cluster; verified at block 8.1 G4) |
| `file_mNHxdrydep` | (not set) | `ndep_drynhx_*.nc4` (per-SSP) | `/media/bampoh-d/ISIMIP/inputs/n-deposition/histsoc-ssp{126,370,585}soc-wetdry-lpjguess/` (local; user-confirmed canonical at block 8.0.3 follow-up; SSP-specific variants for SSP1-2.6, SSP3-7.0, SSP5-8.5) + `/media/bampoh-d/ISIMIP/inputs/n-deposition/histsoc-wetdry-lpjguess/` (1850-2015 historical fallback for SSP2-4.5 + SSP4-6.0 per user's canonical wpeat runs pattern verified at block 8.1 D5) ↔ cluster equivalents at `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/n-deposition/...` (verified at block 8.1 G4) |
| `file_mNHxwetdep` | (not set) | `ndep_wetnhx_*.nc4` | (same) |
| `file_mNOydrydep` | (not set) | `ndep_drynoy_*.nc4` | (same) |
| `file_mNOywetdep` | (not set) | `ndep_wetnoy_*.nc4` | (same) |

The smoke setup falls back to LPJG's pre-industrial-constant 2 kgN/ha/yr ndep when `file_ndep` is empty + the 4 wet/dry NetCDFs aren't supplied. This is **acceptable for smoke validation** (B19 + B20 PASS) but **insufficient for paper-grade publication runs** (modern N deposition is ~5-15× pre-industrial in many regions; impacts soil N cycling + N2O; IPCC AR6 standard N-deposition forcing is the 4-NetCDF wet/dry NHx + NOy product).

---

## 3. Updated LU forcing dataset map

### 3.1 Local mirror

```
/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/
├── output_hildaplus_remap_10b_3/
│   └── remaps_v10_old_62892_gL/                                    ← HISTORICAL 1900-2020
│       ├── LU.remapv10_old_62892_gL.txt                            (basic; 413 MB)
│       ├── LU.remapv10_old_62892_gL_peatland.txt                   ✓ USE THIS (664 MB; peatland-tagged)
│       ├── cropfracs.remapv10_old_62892_gL.txt                     (12.7 MB)
│       ├── nfert.remapv10_old_62892_gL.txt                         (12.7 MB)
│       └── soilmap_center_interpolated.remapv10_old_62892_gL.dat   (3.6 MB; matches production gridlist)
│       └── (NO irrig file for historical)
├── SSP1_RCP26/                                                     ← SSP1-RCP2.6 SCENARIO 2020-2100
│   └── s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/
│       ├── landcover.txt                                           (basic; 275 MB)
│       ├── landcover_peatland.txt                                  ✓ USE THIS (315 MB; peatland-tagged)
│       ├── cropfractions.txt                                       (1.05 GB)
│       ├── nfert.txt                                               (1.05 GB)
│       └── irrig.txt                                               (1.05 GB; SSP-period only)
├── SSP2_RCP45/                                                     ← (similar structure)
├── SSP3_RCP70/                                                     ← (similar structure)
├── SSP4_RCP60/                                                     ← (similar structure)
└── SSP5_RCP85/                                                     ← (similar structure)
```

### 3.2 Cluster path equivalence

| Local | Cluster |
|---|---|
| `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/` | `/bg/data/lpj/bampoh-d/landsymm_lu/` (per `integrated-4.1-ins2_landsymm_hist/landcover.ins:11`) |
| `/media/bampoh-d/lpjg_input/input/fire/SimfireInput.bin` | `/bg/data/lpj/LPJ-GUESS/input/fire/SimfireInput.bin` |
| `/media/bampoh-d/lpjg_input/input/pop_dens/...` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/pop/lpjg-popd/...` |
| `/media/bampoh-d/lpjg_input/input/ndep/...` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/n-deposition/...` |
| `/media/bampoh-d/lpjg_input/input/isimip/isimip3/climate_land_only_v2/climate3b/...` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/climate_land_only_v2/climate3b/...` |
| `/media/bampoh-d/lpjg_input/input/isimip/isimip3/co2/co2_histssp126_annual_1850_2100.txt` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/co2/co2_histssp126_annual_1850_2100.txt` |

Production .ins files maintained on the cluster reference `/bg/data/lpj/...` paths; for local production-style validation runs (e.g., during local v1 verification window) these need to be substituted with `/media/bampoh-d/lpjg_input/input/...` equivalents.

---

## 4. Input-module evolution

The lpjguess source registers **5 input modules** (`grep REGISTER_INPUT_MODULE lpjguess/modules/*.cpp`):

| Module | Source file | What it reads | Used by |
|---|---|---|---|
| `cf` | `cfinput.cpp` | older CF-NetCDF reader (climate only) | (deprecated; not used in v1.0) |
| `cfx` | `cfxinput.cpp` | extended CF-NetCDF reader: ISIMIP3b climate (NetCDF) + atmospheric CO2 (txt) + popdens (NetCDF) + SimFire binary + 4-NetCDF wet/dry NHx+NOy ndep + LU forcing | **Track 1: past + future Track-1 cluster runs** that produced the LPJG natural-flux outputs feeding `intermediary_py` Component B |
| `imogen` | `imogen_input.cpp` | LPJG reads pre-baked IMOGEN climate from disk (loose mode; standalone) | F-10 deadlock-bypass mode for cross-validation |
| `imogencfx` | `imogencfx.cpp` | IMOGEN engine output (climate + CO2; in-process via RUN_IMOGEN_ENGINE) + cfx-style auxiliaries (popdens, SimFire, ndep, LU forcing) | **Track 2: v1.0 paper publication coupled-mode runs** (in-process IMOGEN engine drives LPJG climate + CO2; everything else flows like cfx) |
| `demo` | `demoinput.cpp` | demonstration / placeholder | (not used) |
| `firemip` | `firemipinput.cpp` | FireMIP-specific inputs | (not used in v1.0) |

**Key relationship**: `imogencfx` IS `cfx` + IMOGEN-engine-substitution-for-climate-and-CO2. Switching from `cfx` (Track 1) to `imogencfx` (Track 2) for the v1.0 paper publication keeps every other input pipeline (popdens, SimFire, ndep, LU, soil, gridlist) identical; only the climate + CO2 sources differ. **This is what makes the Track 1 vs Track 2 ecosystem comparison clean** for the paper.

The stale `! Make sure to start LPJ-GUESS with -input cf` comment in `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/main.ins` headers is a leftover from an earlier era; the actual production `setup_run.sh` invocation uses `cfx` (per `setup_run.sh` line 4 inputmethod arg). Worth correcting in the production .ins headers as a small future fix-it (TRUNK-IRRELEVANT-by-novelty since `lpjg_landsymm_integration/` lives outside the rebuild repo).

---

## 5. Two-track architecture for v1.0 paper publication

### 5.1 Track 1 — LPJG-cfx-ISIMIP3b (baseline; outputs already exist)

**Driver**: `-input cfx` + ISIMIP3b MRI-ESM2-0 climate (1850-2014 historical + 2015-2100 SSP scenario per scenario; 6 NetCDF files: tas, pr, rsds, sfcwind, hurs, tasmin, tasmax) + ISIMIP3b atmospheric CO2 (per-scenario txt: e.g. `co2_histssp126_annual_1850_2100.txt`)

**Auxiliaries** (same across both tracks for clean comparison): updated `_peatland` LU forcing, popdens NetCDF, SimFire BLAZE binary, 4 wet/dry NHx + NOy ndep NetCDFs, soilmap

**Outputs**: ecosystem state outputs (`*.out` files), LPJG-natural CH4 + N2O fluxes (`ngases.out` per-cell + global aggregations) — **the `imogen_lpjg_*_flux.txt`-style outputs from these runs were post-processed and stored in `intermediary_py/imogen_ghg_controller/INPUT_DATA/lpjg/` to feed Component B's natural-flux modeling per the user 2026-05-19 morning confirmation**.

**Status**: 5 cluster runs completed by user (SSP1-RCP2.6 + SSP2-RCP4.5 + SSP3-RCP7.0 + SSP4-RCP6.0 + SSP5-RCP8.5); outputs already in `intermediary_py` input data; B20 literature comparison validated the natural-flux magnitudes (full-envelope time-mean WITHIN Saunois 2020 + Tian 2020 envelopes).

### 5.2 Track 2 — LPJG-imogencfx-IMOGEN (NEW for v1.0 paper publication)

**Driver**: `-input imogencfx` + IMOGEN-engine climate (in-process via `RUN_IMOGEN_ENGINE()` at `lpjguess/modules/climatemodel.cpp:153`; emits per-year ASCII at `Common-directory/IMOGEN/output/<year>/{T_anom,P_anom,SW_anom,Rh_anom,W_anom,DTEMP_anom,Tmax_anom,Tmin_anom,WET}.dat`) + IMOGEN-engine atmospheric CO2 (in-process via the same engine; emits per-year ASCII at `Common-directory/IMOGEN/output/<year>/CO2.dat`)

> **✅ ENGINE IDENTITY CLARIFICATION (block 8.1.5, 2026-05-22)**: the "IMOGEN engine" here is the **C++ port embedded in `lpjguess/modules/climatemodel.cpp`** — called inline from `imogencfx::init() → RUN_IMOGEN_ENGINE()`. This is NOT the standalone Fortran `imogen/code/imogen_lpjg.f`. The C++ port outputs on the native 1631-point IMOGEN pattern grid; pattern-scaling to LPJG's 62892 cells happens downstream in `imogencfx.cpp::lon_lat_lines_in_file()` via NN matching. For v1.0 production runs, **Option δ-B** (switchable-regrid-strategy per block 8.1.5 findings §13) uses the standalone Fortran engine with REGRID=TRUE → 3698-grid output → FastRegrid IDW → 62892-grid → LPJG, matching predecessor architecture for Axis 4 parity. Full evidence at `_chat_artifacts/b8_1_5_architectural_clarification_2026-05-22/B8_1_5_architectural_clarification_findings_2026-05-22.md`.

**Engine inputs**: anthropogenic CO2/CH4/N2O emissions (from `intermediary_py` Component A: RCMIP/CMIP6 substitution) + natural CO2/CH4/N2O fluxes (from `intermediary_py` Component B: post-processed Track 1 LPJG-natural-flux data) — both flow through the prescribed-mode handshake at `runs/<SSP>/inputs/{co2,ch4_n2o}_anthro_emissions.txt` + `runs/<SSP>/inputs/imogen_lpjg_{flux,ch4_n2o_flux}.txt`

**Auxiliaries** (same as Track 1 for clean comparison): updated `_peatland` LU forcing, popdens NetCDF, SimFire BLAZE binary, 4 wet/dry NHx + NOy ndep NetCDFs, soilmap

**Outputs**: ecosystem state outputs (`*.out` files) — directly comparable to Track 1's `*.out` files (same gridlist, same LU, same auxiliaries; only climate + CO2 source differ)

**Status**: NOT YET RUN (this is the work for after local v1 verification window completes; cluster phase 17c.1+).

### 5.3 Validation triad for the paper's results section

| Comparison | Tools | Purpose | Status |
|---|---|---|---|
| (1) **Anthropogenic emissions plots** | `intermediary_py` Component A plotting scripts (rcmip_substitution + scenarios subdirs) | document the integrated anthropogenic emissions modelling for each SSPx_RCPyy scenario | available; produced by `intermediary_py` itself |
| (2) **IMOGEN-derived atm GHG concentrations vs literature trends** | `scripts/b19_phase4_literature_validate.py` (currently smoke-only; extends to full 1900-2100 for paper) + literature reference values from MacFarling Meure 2006 / Etheridge 1996 / Meinshausen 2017 | document that IMOGEN-engine-derived atm concentrations match historical record + are physically plausible across all 5 SSPs | smoke validated (B19 Phase 4 BALLPARK_PASS); production extension awaits Track 2 runs |
| (3) **IMOGEN-derived climate vs ISIMIP3b climate** | NEW comparison script (post-Track-2-runs deliverable); ISIMIP3b NetCDFs as reference; difference maps + trend comparisons | document the climate-driver fidelity between two driver pipelines | NOT YET STARTED (awaits Track 2 runs) |
| (4) **Track 1 vs Track 2 LPJG ecosystem state output comparison** | NEW comparison script (post-Track-2-runs deliverable); per-output-file (cflux, ngases, ...) correlation + difference maps | document the ecosystem-output sensitivity to climate-driver pipeline (ISIMIP3b vs IMOGEN); all other inputs held constant | NOT YET STARTED (awaits Track 2 runs) |

---

## 6. v1.0 paper publication readiness checklist

### Status as of 2026-05-19 morning (B19+B20 close-out era)

- [x] B19 Phase 4 atmospheric concentrations verified against Law Dome ice core (smoke window 1900-1903; BALLPARK_PASS)
- [x] B20 LPJG-natural fluxes verified against Saunois 2020 + Tian 2020 budgets (full 1900-2100; WITHIN_ENVELOPE_MEAN_WITH_TIME_VARIATION = PASS)
- [x] B19 + B20 v1.0 magnitude validation PASS on smoke configuration
- [ ] Local v1 verification window: B36 (Fortran background-emission audit) + B37 (productive-year-ceiling study) + B39 (CO2_INIT_PPMV per-YEAR1) + B40 (modern-decade N2O hump explanatory study)
- [ ] Production-style configuration of `runs/<SSPx_RCPyy>/main.ins` with updated `_peatland` LU + production parameters (npatch=25, nyear_spinup=500, BLAZE+SimFire, popdens, 4-NetCDF wet/dry NHx+NOy ndep)
- [ ] Test run on local workstation with reduced gridlist (e.g., 100 cells; verify full pipeline works) before cluster scaling
- [ ] Cluster setup at KIT IMK-IFU `owl` (17c.1+ phase)
- [ ] Track 2 production runs (5 SSPx_RCPyy scenarios; 1900-2100; 62892-cell gridlist; `-input imogencfx`)
- [ ] Validation triad (1)+(2)+(3)+(4) execution + paper figures
- [ ] Paper amendments:
  - [ ] Replace "legacy IIASA-backbone via legacy intermediary" with "RCMIP/CMIP6 backbone via intermediary_py" in introduction + methods
  - [ ] Add Track 1 vs Track 2 ecosystem comparison framing in methods
  - [ ] Add B19 + B20 + post-Track-2 validation discussion in results

### Effort estimate (rough)

- Local v1 verification window: ~6-13 h (B36+B37+B39+B40)
- Production-config authoring (B41 follow-through): ~3-5 h
- Local 100-cell test run: ~1-2 h on workstation
- Cluster setup (17c.1): ~1-2 weeks SSH-iterative
- Track 2 production runs (5 scenarios; cluster): ~1-2 weeks compute + iteration
- Validation triad execution + paper figures: ~1 week
- Paper amendments + writing: ongoing in parallel
- **Total estimated calendar time to paper submission**: ~6-10 weeks from this commit

---

## 7. Tight-coupling roadmap (v1.1+; B43 record)

### Why deferred from v1.0 paper publication

Per user 2026-05-18 night + 2026-05-19 morning decision: F-12 architectural fix (resolving the F-10 case-α deadlock to enable LIVE-LPJG-handshake natural-flux flow direct to IMOGEN) is **deferred to v1.1+** for the following reasons:

1. F-12 architectural work is a substantial multi-week effort (per `notes/STEP_17c.md` + `notes/FOLLOWUPS.md` F-10 + F-12 entries)
2. The v1.0 paper publication scientific narrative is fully sound under prescribed mode (validation triad above is methodologically clean + reviewer-defensible)
3. F-12 fix would require additional verification cycles; risks v1.0 paper schedule slippage
4. v1.1+ paper(s) post-v1.0 can showcase tight-coupling as headline new capability + use prescribed-mode v1.0 baseline as methodological reference

### v1.0 architecture (prescribed mode; for paper)

```
intermediary_py
  ├─ Component A: anthropogenic CO2/CH4/N2O via RCMIP/CMIP6 substitution
  └─ Component B: natural CO2/CH4/N2O from post-processed Track 1 LPJG outputs
      │
      ▼ all 4 GHG channels (anthro + natural) flow through the .ins
      │ FILE_SCEN_EMITS / FILE_CH4_N2O_EMITS / FILE_LPJG_FLUX / FILE_LPJG_CH4_N2O_FLUX
      ▼
IMOGEN engine (climate emulator + GHG budget)
  produces: atm CO2/CH4/N2O concentrations + climate (1900-2100)
      │
      ▼ engine output read via the imogencfx input module
      ▼
LPJ-GUESS (-input imogencfx)
  + updated _peatland LU forcing
  + popdens NetCDF + SimFire BLAZE binary
  + 4-NetCDF wet/dry NHx+NOy N-deposition
  produces: ecosystem state outputs (Track 2 — for paper)
      │
      ▼ (LPJG natural-flux feedback to IMOGEN BLOCKED in v1.0 by F-10 case-α deadlock)
      ▼
   (LPJG main loop never relinquishes control; handshake never closes)
```

### v1.1+ architecture (tight-coupling; post-F-12)

```
intermediary_py
  └─ Component A: anthropogenic CO2/CH4/N2O via RCMIP/CMIP6 substitution
     (Component B no longer needed for the coupled run itself; remains a
      pre-condition data product for cross-validation)
      │
      ▼ anthro channels only
      ▼
IMOGEN engine
  ▲                                                  │
  │ LIVE LPJG natural fluxes via                     │
  │ FILE_LPJG_FLUX / FILE_LPJG_CH4_N2O_FLUX          │
  │ (Option C; F-12-fixed)                           │
  │                                                  ▼ atm conc + climate (year N)
  │                                                  │
  │                                                  ▼
  │                                              LPJ-GUESS (-input imogencfx)
  │                                                + updated _peatland LU
  │                                                + popdens + SimFire BLAZE
  │                                                + 4-NetCDF wet/dry NHx+NOy
  │                                                  │
  │                                                  ▼ ecosystem outputs +
  └──────────────────────────────────────────────────┘  LPJG natural fluxes
       (per-year handshake; closed feedback loop)      (year N → year N+1 IMOGEN)
```

### v1.1+ paper publications

Post-v1.0 papers can showcase:
- Tight-coupling vs prescribed-mode comparison (using v1.0 paper as methodological reference)
- Multi-decade closed-loop natural-flux feedback effects
- F-12 architectural fix as headline new capability

This is OUT OF SCOPE for v1.0 paper publication; CAPTURED here for forward continuity.

---

## 8. Cross-references

- `notes/B19.md` — closed-loop verification milestone (B19 Phases 0-5; smoke validation)
- `notes/FOLLOWUPS.md` — full audit-item dashboard (B36, B37, B39, B40, B41, B42, B43 + open Fs F-10, F-12)
- `docs/scientific_framework.md` — coupled-model scientific architecture
- `EXECUTION_PLAN.md` — step-by-step rebuild plan + cluster phase 17c roadmap
- `runs/SSP1-2.6/main.ins` — current smoke-test main.ins
- `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/` — example production-style main.ins (Track 1 cfx mode)
- `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_hist/setup_run.sh` — example production launcher (uses `cfx` inputmethod)
- `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Parts 10g + 10h + 11 — session 5 narrative (B19 Phase 3 ADDENDUM through B19 Phase 5 close-out)
- `_chat_artifacts/CHAT_HANDOFF_2026-05-18_session5_post_b19.md` Part 1 — B20 narrative

---

_End of `notes/PRODUCTION_RUN_CONFIG.md` — initial draft 2026-05-19 morning; iteratively refined as B36/B37/B39/B40 + 17c.1+ outcomes inform the readiness checklist._