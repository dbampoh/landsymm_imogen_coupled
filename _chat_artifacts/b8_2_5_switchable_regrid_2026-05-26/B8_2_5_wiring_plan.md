# Block 8.2.5 — Switchable-regrid-strategy wiring: δ-B Fortran-engine + δ-B-variant trunk-cpp-engine pipelines + 4-cell smoke side-by-side acceptance

**Date authored**: 2026-05-26 (session 11 day 2 afternoon ~15:35 CEST; post-block-8.2.4 close commit `efe5ee7` + tag `v0.23.0-trunk-engine-forwardport-complete` 3-remote-converged)

**Authoring agent**: Claude Opus 4.7 (session 11 day 2; same agent throughout session 11)

**Status**: ⏳ PHASE A INSPECTION COMPLETE; awaiting user approval before Phase B-H execution

**Scope**: Build BOTH pipelines for v1.0 paper Track 2 — (1) **δ-B (Fortran engine)**: `imogen/code/imogen_lpjg.f` @ NGPOINTS=3698 with REGRID=.TRUE. → FastRegrid IDW 3698→62892 → trunk-T_seq LPJG @ 62892; (2) **δ-B-variant (trunk-cpp-engine post-block-8.2.4)**: `forks/trunk_r13078/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` @ 1631 native → chained FastRegrid NN 1631→3698 + IDW 3698→62892 → trunk-T_seq LPJG @ 62892. Then 4-cell smoke side-by-side acceptance comparison + user picks ONE for v1.0 paper main Track 2 cluster production runs (the other stays in repo as v1+ post-paper switchable alternative per B57 + B59).

---

## §0 Scope decisions (architectural; key Rule #7 + #11 + #13 calls)

### §0.1 In-scope at block 8.2.5

| Component | Description | Effort |
|---|---|---|
| `imogen/code/imogen_settings.txt` per-SSP alignment for Fortran engine | DIR_PATT → CMIP6 MRI-ESM2-0 + REGRID=.TRUE. + B39 init values + LPJG_CFLUX=.TRUE. + intermediary_py adapter input paths + per-SSP runtime dirs at `runs/<SSP>/Common-directory-fortranengine/imogen_settings.txt` | ~1-2h |
| `tools/FastRegrid/` clone from `../version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/FastRegrid/FastRegrid/` + Linux/Linux-friendly CMake adaptation + 10-var `file_types` extension + CLI-arg parameterization of main() (replace hardcoded Windows paths) | ~2-3h |
| Build `tools/FastRegrid/build/fastregrid_example` via cmake + make | binary ready for invocation | ~5 min |
| NEW `scripts/run_fortran_engine_only.sh` wrapper (mirrors `scripts/run_trunk_engine_only.sh` block-8.2.4 pattern; bootstraps `imogen_lpjg.txt` + spawns sidecar + invokes `imogen/code/imogen_lpjg` from `runs/<SSP>/Common-directory-fortranengine/`) | ~100-150 LOC | ~1-2h |
| NEW `scripts/run_fastregrid.sh` wrapper (per-SSP + per-pipeline parameterized; handles both single-step δ-B IDW 3698→62892 + chained δ-B-variant NN 1631→3698 + IDW 3698→62892) | ~150-200 LOC | ~1-2h |
| Per-SSP Fortran-engine standalone runs × 5 SSPs (~13-17 min wall serial; or ~17 min 5-way parallel) | 5 × ~1 GB libraries at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output/<year>/*.dat` (3698-grid) | ~17 min wall (parallel) |
| FastRegrid IDW 3698→62892 for δ-B (5 SSPs) | 5 × ~17 GB output libraries at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892/<year>/*.dat` | ~30-60 min wall (parallel) |
| Chained FastRegrid NN 1631→3698 + IDW 3698→62892 for δ-B-variant (5 SSPs) | 5 × ~17 GB output libraries at `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/<year>/*.dat` | ~30-60 min wall (parallel) |
| `forks/trunk_r13078_runs/<SSP>/main_b825_smoke_delta_b.ins` + `main_b825_smoke_delta_b_variant.ins` 4-cell smoke .ins variants pointing at chosen pipeline's 62892 library | ~150 LOC per file × 2 × 5 SSPs (but probably just 2 for SSP1-2.6 if smoke is single-SSP); per the 4-cell smoke acceptance pattern at block 8.0.3 | ~1-2h |
| 4-cell smoke side-by-side acceptance test (trunk-T_seq LPJG × both δ-B + δ-B-variant for SSP1-2.6 with `gridlist_test2.txt`) | compare ecosystem outputs cflux + cmass + anpp + mch4 + ngases between pipelines | ~30 min wall (smoke); +1h evidence-bundle analysis |
| Audit-evidence bundle + multi-surface doc cascade + commit + tag candidate `v0.24.0-switchable-regrid-strategy-complete` | per session-11-day-2-or-3 close | ~2-3h |

**Total scope**: ~1.5-2 d focused work (matches session 11 prompt §5 estimate; matches block 8.1.5 §17 expectation).

### §0.2 Out-of-scope / deferred at block 8.2.5

| Item | Reason for deferral |
|---|---|
| Production cluster Track 2 runs (5 SSPs × 62538 cells × 1900-2100) | Block 8.4+ work (cluster smoke at 8.3 first; production at sessions 9-11) |
| In-engine C++ REGRID port (Option A from session 10 day 1 Option C-hybrid decision per B59) | v1+ post-paper trajectory per `notes/B54.md` + `notes/B56.md`; chained external FastRegrid is the v1.0 path |
| Track 1 baseline cluster runs (block 8.6) | v1.0 paper validation triad work; sessions 11-12 |
| FastRegrid parallelization tuning (OpenMP threads, etc.) | Default OpenMP build OK for v1.0; tune at v1+ if scaling beyond 5 SSPs × 62892 cells |
| Cluster-side FastRegrid invocation tooling | Block 8.4 cluster production-config delta authoring |

### §0.3 Per-SSP runtime layout strategy (KEY decision)

Following block 8.2.4's pattern (per-SSP runtime dirs at `runs/<SSP>/Common-directory/` + `forks/trunk_r13078_runs/<SSP>/Common-directory/`), block 8.2.5 adopts:

- **δ-B Fortran-engine pipeline** runtime: `runs/<SSP>/Common-directory-fortranengine/` (NEW; sibling to `runs/<SSP>/Common-directory/` which has the C++ engine library). Per-SSP `imogen_settings.txt` lives here; engine cd's into this dir at runtime; output lands at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output/<year>/*.dat` (3698-grid; engine hardcodes `IMOGEN/output/<year>/` subpath relative to DIR_COMMON `./`); post-FastRegrid 62892-grid output goes to `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892/<year>/*.dat`.

- **δ-B-variant trunk-cpp-engine pipeline** runtime: REUSES the existing `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/` (1631-grid; produced at block 8.2.4 Phase E with trunk's freshly-forward-ported engine; ~443 MB × 5 = ~2.2 GB total). Post-chained-FastRegrid 62892-grid output goes to `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/<year>/*.dat`.

- **Final paper-stage chosen library cp/symlink at block 8.4**: depending on user's pick at Phase G, the chosen post-FastRegrid 62892-grid library moves into `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_chosen/<year>/*.dat` (or trunk's main.ins climate `file_temp` etc. paths point at the chosen pipeline's 62892 location).

### §0.4 4-cell smoke acceptance design

Per block 8.0.3 acceptance pattern + session 11 prompt §5.2.6:

- Use `data/gridlist/gridlist_test2.txt` (4 cells: Canadian Arctic + Russia + Argentina + Far north Canada; 3 of 4 in production gridlist `gridlist_in_62892_and_climate.txt`; 1 lacks 62892-coverage which is fine — LPJG just skips it)
- Single SSP for smoke (SSP1-2.6; matches block 8.0.3 baseline)
- Two run-dirs per pipeline (or two .ins variants in single run-dir):
  - `forks/trunk_r13078_runs/SSP1-2.6_b825_smoke_delta_b/` (climate paths point at `runs/SSP1-2.6/Common-directory-fortranengine/IMOGEN/output_62892/<year>/`)
  - `forks/trunk_r13078_runs/SSP1-2.6_b825_smoke_delta_b_variant/` (climate paths point at `forks/trunk_r13078_runs/SSP1-2.6/Common-directory/IMOGEN/output_62892_cppengine/<year>/`)
- Run trunk-T_seq LPJG (`forks/trunk_r13078/build_b824/guess -input imogencfx main.ins`) for each smoke run
- Compare ecosystem outputs (cflux + cmass + anpp + mch4 + ngases) side-by-side
- User picks ONE pipeline based on:
  - Quantitative criteria: ecosystem-output value matches between pipelines (sanity-check; should be similar but not identical because the input climate fields differ slightly between Fortran-3698 vs C++-1631-chained)
  - Operational preferences: ease of v1+ live-coupling trajectory (likely favors δ-B-variant trunk-cpp-engine since v1+ live coupling uses the C++ engine); paper-architecture-purity (likely favors δ-B Fortran since it matches predecessor architecture exactly)

---

## §1 Phase B-H execution order (commit-cascade plan)

### §1.1 Phase B — Fortran engine settings alignment + per-SSP runtime dirs (~0.5-1h)

**Sub-edits per SSP** (5 SSPs):
1. `mkdir -p runs/<SSP>/Common-directory-fortranengine/`
2. Author `runs/<SSP>/Common-directory-fortranengine/imogen_settings.txt` per-SSP variant from the template at `imogen/code/imogen_settings.txt` with:
   - `DIR_COMMON ./` (engine writes under cwd; cwd will be `runs/<SSP>/Common-directory-fortranengine/`)
   - `DIR_PATT ../../../imogen/patterns/CEN_CMIP6_MOD_MRI-ESM2-0/` (CMIP6 MRI-ESM2-0; matches C++ engine + per user direction)
   - `DIR_CLIM ../../../imogen/CRUNCEP_1960_1989/`
   - `FILE_SCEN_EMITS ../../../runs/<SSP>/inputs/co2_anthro_emissions.txt` (intermediary_py adapter output; SAME inputs as C++ engine consumed at block 8.2 Phase D)
   - `FILE_NON_CO2_VALS ../../../imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp<TAG>.txt` (per-SSP)
   - `FILE_CH4_N2O_EMITS ../../../runs/<SSP>/inputs/ch4_n2o_anthro_emissions.txt`
   - `FILE_LPJG_FLUX ../../../runs/<SSP>/inputs/imogen_lpjg_flux.txt`
   - `FILE_GRIDLIST ../../../data/gridlist/gridlist_hurtt_RNDM_midpoint_3698.txt` (3698-grid)
   - `FILE_LPJG_CH4_N2O_FLUX ../../../runs/<SSP>/inputs/imogen_lpjg_ch4_n2o_flux.txt`
   - `NGPOINTS 3698` (unchanged from template)
   - `CO2_INIT_PPMV 296.1` (B39 Law Dome 1900; was 286.085 in template)
   - `CH4_INIT_PPBV 875.6` (B39 Law Dome 1900; was 865.0)
   - `N2O_INIT_PPBV 277.4` (unchanged)
   - `NYR_EMISS 201` + `NYR_EMISS_NONCO2 201` + `NYR_LPJG_FLUX 201` (1900-2100 = 201 yrs; was 251)
   - `LPJG_CFLUX .TRUE.` (was .FALSE.; engine uses intermediary_py-provided LPJG natural fluxes)
   - `REGRID .TRUE.` (was .FALSE.; THE key change enabling 3698-grid output via REGRID_CLIM NN)
   - All other params unchanged from template
3. ALSO add bootstrap params not in current template (these may be needed depending on what the Fortran engine reads; defaults likely safe if missing):
   - `YEAR1 1900`, `IYEND 2100`, `YEAR1_LPJG 1900`, `SPINUP 0`, `KEEPRUNNING 1`, `FIRSTCALL 1` (these may need to come via the bootstrap `imogen_lpjg.txt` like the C++ engine; need to verify by reading the Fortran source's bootstrap-vs-settings handling)

**Phase B verification**: per-SSP imogen_settings.txt readable + path relativity correct (e.g., `ls runs/SSP1-2.6/Common-directory-fortranengine/../../../imogen/patterns/CEN_CMIP6_MOD_MRI-ESM2-0/jan` resolves cleanly)

### §1.2 Phase C — tools/FastRegrid/ clone + adaptation + build (~2-3h)

**Sub-edits**:
1. `cp -r ../version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/FastRegrid/FastRegrid/* tools/FastRegrid/` (4 source files: CMakeLists.txt + FastRegrid.cpp + Regrid.cpp + Regrid.h)
2. **EXTEND `tools/FastRegrid/FastRegrid.cpp` `file_types` vector** (line 66) from 3 vars (`T_anom.dat`, `SW_anom.dat`, `P_anom.dat`) to 10 vars (add `DTEMP_anom.dat`, `WET.dat`, `Tmin_anom.dat`, `Tmax_anom.dat`, `Rh_anom.dat`, `W_anom.dat`, `CO2.dat`). ~5 LOC change per block 8.1.5 §3.
3. **REPLACE `main()` hardcoded Windows paths with CLI arg parsing** (argc/argv based or env-var based; cleanest path: convert to a small `parse_args()` function that takes `--input`, `--output`, `--target-gridlist`, `--method (NN|IDW)`, `--first-year`, `--last-year`, `--data-layout (YEAR_BY_YEAR|GRID_BY_TIME)` flags). ~50 LOC adaptation.
4. **Build**: `cd tools/FastRegrid && mkdir -p build && cd build && cmake .. && make -j$(nproc)`. Expected: clean build of `fastregrid` shared library + `fastregrid_example` executable; OpenMP automatically picked up by Linux's gcc-15 + system libgomp.

**Phase C verification**: smoke run `tools/FastRegrid/build/fastregrid_example --help` (or no-args) — should emit Usage banner; do a small 4-cell regrid as canary (e.g., regrid runs/SSP1-2.6/Common-directory/IMOGEN/output/1900/T_anom.dat from 1631-grid to gridlist_test2.txt 4 cells; produces 4-cell output).

### §1.3 Phase D — Fortran engine 5-SSP standalone runs (~17 min wall 5-way parallel)

**Sub-edits**:
1. NEW `scripts/run_fortran_engine_only.sh` (~100-150 LOC; mirrors `scripts/run_trunk_engine_only.sh` block-8.2.4 pattern):
   - `TRUNK_BIN` env-overridable → `FORTRAN_BIN="${FORTRAN_BIN:-${ROOT}/imogen/code/imogen_lpjg}"`
   - Setup Common-directory-fortranengine structure (mkdir -p; setup handshake dir similar to C++ engine)
   - Bootstrap `imogen_lpjg.txt` + `done` markers at `${HSHAKE_DIR}/`
   - Spawn path-iv sidecar
   - `cd runs/<SSP>/Common-directory-fortranengine && ${FORTRAN_BIN}` (or however the Fortran engine is invoked)
   - Verify output (202 year-dirs at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output/<year>/`)
2. Run for 5 SSPs (5-way parallel like block 8.2.4 Phase E)
3. Per Rule #9: anticipate latent defects surfacing (Fortran-engine-specific; e.g., maybe Fortran engine doesn't have B37+B44 path-iv sidecar mechanism baked in OR uses a different polling mechanism — these are Fortran-side at `imogen_lpjg.f` lines 411-450 INQUIRE calls; need to verify the polling-escape semantics match what our sidecar provides)

**Phase D acceptance gates** (8-gate; same template as block 8.2.4 Phase D):
- G0: Fortran binary built + executable at `imogen/code/imogen_lpjg` + smoke-runs cleanly
- G1: bootstrap files written
- G2: engine escapes polling loop (if applicable; Fortran engine may not have same polling pattern as C++)
- G3: 202 year-dirs produced (or whatever the natural Fortran 1900-2100 range produces; possibly 201 vs 202 depending on YEAR1==2100 overshoot semantics)
- G4: library size ~1 GB per SSP (3698-grid output; ~4-5x larger than C++ 1631 native because 3698/1631 = 2.27x more cells; ~5x because file headers + dat blocks)
- G5: per-year directories contain 10 climate variable .dat files
- G6: CO2 trajectories physically sensible vs IPCC AR6 / Friedlingstein 2025 GCB (same values as block 8.2 Phase D C++ engine ± minor numerical differences; or for SSP-comparison: CO2 2100 ≈ 427/590/826/631/1092 ppm per SSP)
- G7: engine exit code 0 OR 99 (depending on Fortran convention; B37+B44 was a C++-engine pattern)

### §1.4 Phase E — FastRegrid runs (~30-60 min wall 5-way parallel; both pipelines)

**Sub-edits**:
1. NEW `scripts/run_fastregrid.sh` (~150-200 LOC):
   - Parameterized for per-SSP + per-pipeline
   - Single-step IDW mode (δ-B): `fastregrid_example --input runs/<SSP>/Common-directory-fortranengine/IMOGEN/output --output runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892 --target-gridlist data/gridlist/gridlist_in_62892_and_climate.txt --method IDW --first-year 1900 --last-year 2100`
   - Chained mode (δ-B-variant): two-step invocation — first NN 1631→3698 (intermediate library), then IDW 3698→62892 (final library)
   - Per-SSP loop; parallelize across SSPs if workstation has capacity
2. Run δ-B FastRegrid for 5 SSPs (5 × ~17 GB → 85 GB total for δ-B 62892-grid libraries; may need to be selective for local-disk; cluster has more space)
3. Run δ-B-variant chained FastRegrid for 5 SSPs (5 × ~17 GB → 85 GB for δ-B-variant 62892-grid libraries; same disk consideration)

**Disk-space consideration**: 5 × ~17 GB × 2 pipelines = ~170 GB total local-disk for 62892-grid libraries. This is substantial. Options:
- (a) Generate full 5-SSP 62892-grid libraries locally (~170 GB)
- (b) Generate only 1 SSP (SSP1-2.6) 62892-grid library locally for smoke; defer full 5-SSP to cluster at block 8.4-8.5
- (c) Generate post-FastRegrid libraries that subset to the 4-cell smoke gridlist only (~tiny KB; just for smoke acceptance); defer full 62892 to cluster

Option (c) is cleanest for block 8.2.5 (smoke acceptance only); full 5-SSP 62892 regrid happens at block 8.3+ on cluster where disk is ample. Per the plan.

**Phase E acceptance**: Verify the smoke-subset output libraries are correctly formatted + read by trunk-T_seq LPJG at Phase F.

### §1.5 Phase F — 4-cell smoke side-by-side acceptance (~30 min wall + ~1h analysis)

**Sub-edits**:
1. Author `forks/trunk_r13078_runs/SSP1-2.6_b825_smoke_delta_b/main.ins` + matching landcover/crop/global/etc.ins set (cp + sed from existing SSP1-2.6/main.ins template; adjust climate `file_temp`/`file_prec`/etc. paths to point at `runs/SSP1-2.6/Common-directory-fortranengine/IMOGEN/output_62892/<year>/*.dat`)
2. Author `forks/trunk_r13078_runs/SSP1-2.6_b825_smoke_delta_b_variant/main.ins` (analogous; climate paths point at `forks/trunk_r13078_runs/SSP1-2.6/Common-directory/IMOGEN/output_62892_cppengine/<year>/*.dat`)
3. Both .ins set use `gridlist_test2.txt` (4-cell smoke gridlist)
4. Run trunk-T_seq LPJG for each smoke run (`forks/trunk_r13078/build_b824/guess -input imogencfx main.ins` cd'd into each smoke run-dir)
5. Compare ecosystem outputs (cflux + cmass + anpp + mch4 + ngases) side-by-side

**Phase F acceptance gates**:
- F-G0: Both LPJG smoke runs complete (exit code 0)
- F-G1: Both produce non-NaN ecosystem outputs for 3-of-4 smoke cells (per block 8.0.3 acceptance pattern)
- F-G2: cflux + cmass + anpp + mch4 + ngases physically reasonable (vs published ranges; per block 8.0.3 substantive-validation gates)
- F-G3: Side-by-side comparison shows expected similarity (modulo 1631-vs-3698 source-grid resolution difference)

### §1.6 Phase G — User picks ONE pipeline for v1.0 paper Track 2

**Decision criterion**: per the Phase F comparison evidence + user's strategic preference. Likely lean:
- **δ-B Fortran**: predecessor-architecture-matching; paper-architecture-purity argument
- **δ-B-variant trunk-cpp-engine**: v1+ live-coupling-readiness; matches the paper Methods §2.2 "trunk_r13078 throughout" framing locked at block 8.2.4

The unchosen pipeline stays in repo as v1+ post-paper switchable alternative per B57 + B59.

### §1.7 Phase H — Audit-evidence bundle + multi-surface doc cascade + commit + tag (~2-3h)

**Audit-evidence bundle**: `_chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/`:
- `B8_2_5_wiring_plan.md` (this doc; Phase A inspection + plan; ~300 LOC)
- `B8_2_5_evaluation_2026-05-XX.md` (Phase H close evidence; ~250-300 LOC; 8-gate scorecard + Phase A-H summary + Rule #9/#10 datapoints + δ-B vs δ-B-variant side-by-side ecosystem comparison + user's chosen-pipeline rationale)
- Phase B/C/D/E/F per-phase logs
- Sample post-FastRegrid 4-cell-subset libraries (~tiny KB)
- 4-cell ecosystem outputs from both pipelines

**Doc cascade**: ~9 surfaces (same as block 8.2.4):
1. `notes/FOLLOWUPS.md` dashboard top + B57 closure (if user picks ONE pipeline, B57's "Document switchable-regrid-strategy + wire Option δ-B" is partly CLOSED; remaining is documentation of the chosen pipeline) + B59 closure (Stage 2 chained-FastRegrid wiring DONE)
2. `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 NEW "Block 8.2.5 LANDED" entry (TRUNK-IRRELEVANT-by-novelty since changes are at `tools/FastRegrid/` + `runs/<SSP>/Common-directory-fortranengine/` + scripts/ + smoke .ins; no source-edit in `forks/trunk_r13078/`)
3. `CHANGELOG.md` [Unreleased] block 8.2.5 entry
4. `EXECUTION_PLAN.md` row 17c block 8.2.5 LANDED update
5. `notes/STEP_17c.md` §1.7.8 NEW block 8.2.5 entry
6. `notes/PAPER_COMPLETION_AND_VALIDATION.md` §4.5.0 Methods §2.2 update (add chosen-pipeline disclosure)
7. `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §1 NEW POST-BLOCK-8.2.5 operational ordering (block 8.3 cluster smoke ACTIVE NEXT)
8. `tools/FastRegrid/README.md` (NEW; document fork-from-version_B + 10-var extension + CLI args + Linux build notes)
9. `scripts/run_fortran_engine_only.sh` + `scripts/run_fastregrid.sh` NEW operational scripts (referenced from cascade docs)

**Tag candidate**: `v0.24.0-switchable-regrid-strategy-complete` (annotated; switchable-regrid-strategy v1.0 expedited path operational; chosen pipeline locked).

---

## §2 Risk register + Rule #9 mitigations

| Risk | Mitigation |
|---|---|
| Fortran engine has different polling mechanism than C++ engine (B37+B44 sidecar might not apply directly) | Phase D harness will surface this (Rule #9 #19 pattern); fix is wrapper-side (mirror lpjguess scripts/run_coupled.sh logic but for Fortran-specific handshake conventions) |
| FastRegrid Windows-path hardcoding in main() + missing CLI args | Phase C source-edit replaces with argc/argv parsing; ~50 LOC adaptation |
| OpenMP not available on workstation gcc-15 | CMakeLists has `if(OpenMP_CXX_FOUND)` guard; will gracefully fall back to single-threaded if OpenMP missing |
| Disk-space pressure with 5 × 17 GB × 2 pipelines = ~170 GB locally | Use Phase E disk-space-conscious option (c): generate post-FastRegrid only for 4-cell smoke subset locally; defer full 62892 to cluster at block 8.3+ |
| Numerical precision differences between Fortran-engine-direct-3698 and chained-NN-1631→3698 | Expected; both should produce climate at 3698-grid that's physically equivalent ± small numerical differences (~1e-4 to 1e-2 fractional). Phase F smoke ecosystem outputs should show closely-matching cflux/cmass/anpp |
| Per-SSP relative-path depth issue (analogous to block 8.2.4 Rule #9 #22) | Phase B uses `../../../imogen/patterns/...` (depth 3 from runs/<SSP>/Common-directory-fortranengine/) — pre-verify with `ls` before launching engine |
| Fortran engine source-edit-needed for missing config params (e.g., per-SSP bootstrap?) | Per Phase A inspection of `imogen_lpjg.f` line 1712 OPEN(81), Fortran engine reads imogen_settings.txt + likely bootstraps imogen_lpjg.txt similarly to C++ port; verify by running canary; if source-edit needed, scope at v1+ (Fortran tree is fork-shared; backport-IRRELEVANT but rebuild-only-edit) |

---

## §3 What this plan does NOT do (out-of-scope; will not be touched at block 8.2.5)

- `forks/trunk_r13078/modules/climatemodel.cpp` or any other engine source (engine itself is byte-identical between forks post-block-8.2.4 ✅)
- `imogen/code/imogen_lpjg.f` Fortran engine source (already built + operational; binary at May 17 timestamp)
- The block 8.2 / 8.2.4 5-SSP engine libraries (`runs/<SSP>/Common-directory/IMOGEN/output/` + `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/`) — these REMAIN as the source for the δ-B-variant chained FastRegrid + reference for cross-validation
- Track 1 baseline runs or any ISIMIP3b-related infrastructure (block 8.6 work)
- Cluster paths (block 8.4 work; this block 8.2.5 is local-workstation-only)
- Pre-existing intermediary_py / FAIR / RCMIP infrastructure (all already in place from block 8.2)

---

_End of B8_2_5_wiring_plan.md_
