# `forks/trunk_r13078_runs/` — trunk-Track-2 T_seq production-run configurations

**Status**: ACTIVE — populated incrementally as Track 2 production runs per SSP are configured at block 8.0.2 onwards.

**Purpose**: house the trunk-Track-2 T_seq `.ins` files + run-directory structure for v1.0 paper-publication Track 2 production runs per `notes/B47.md` §4. Sibling to `forks/trunk_r13078/` (the source tree imported at block 8.0.1 + minimally source-edited at block 8.0.2). This dual-sibling structure preserves the rebuild's primary fork (`lpjguess/` + `runs/`) untouched while keeping the trunk backport fork's source AND its run configurations clearly co-located + version-controlled.

> **✅ BLOCK 8.3 LANDED — Chosen δ-B-variant pipeline empirically validated on cluster; Track 2 production workflow operational (2026-05-28 session 13 day 1 close; tag `v0.25.0-cluster-trunk-tseq-smoke-complete`)**: Cluster end-to-end smoke validated end-to-end on KIT IMK-IFU owl, milan partition × 4 nodes × 64 CPUs/node = 256 ranks. Both HIST + SCEN smoke phases (1024-cell biome-stratified-anchored gridlist; 50 Phase F anchors + 974 random seed=42) ran cleanly: HIST main `601955` ExitCode 0:0 in 1h29m on milan[05-08] + SCEN main `602049` ExitCode 0:0 in 9m45s on milan[03-06] (~9× faster as expected; restart=1 + restart_year=2020 + state_path absolute as designed; G6.1 NEW gate ✅ SCEN restart from HIST state empirically validated). 8/9 acceptance gates ✅ PASS + 1/9 ⚠️ PARTIAL (benign Svalbard barren-cell SCEN edge case). Per-biome physical sensibility: 36/50 anchor cells within Phase F published Smith2014/Pugh2019/Hickler2012/Friedlingstein2025GCB literature ranges; matches Phase F's 7-8/10 standard. **2 Rule #9 datapoints surfaced + fixed across PREP + close commits**: #34 (cluster main.ins file_gridlist absolute-path latent defect; fix at PREP commit `8e4ee8e`: 10 main.ins file_gridlist + file_gridlist_cf → "gridlist.txt" placeholder per Track-1 wpeat convention; setup_run.sh sed-replaces with --gridlist basename per rank for proper gridlist-split-parallelism); #35 (finishup_lpj_work.sh SLURM script-cache portability bug; fix at this close commit: env-overridable FINISHUP_SCRIPT_DIR with BASH_SOURCE fallback + setup_run.sh's startguess.sh HEREDOC `--export=ALL,FINISHUP_SCRIPT_DIR=${SCRIPT_DIR}`). Both fixes empirically validated. Cluster path now operational for full 5-SSP × HIST + SCEN Track 2 production runs. Full evidence: `_chat_artifacts/b8_3_cluster_smoke_2026-05-28/B8_3_evaluation_2026-05-28.md` (~365 LOC; 12 sections).

> **✅ BLOCK 8.2.5 FULL CLOSE — δ-B-VARIANT PIPELINE CHOSEN FOR v1.0 GMD PAPER TRACK 2 (2026-05-27 session 12 day 2)**: After Phase F 50-cell biome-stratified production-config smoke side-by-side acceptance (both pipelines × hist+scen with save_state/restart per user's wpeat hist+ssp126 production pattern; ~23-24 min wall each in parallel), Phase G user choice (~15:30 CEST 2026-05-27) = **δ-B-variant** (trunk-C++ engine throughout: trunk's NEW engine writes 1631-cell native climate → FastRegrid NN 1631→3696 → IDW 3696→62538 = 5 × 18 GB at `<SSP>/Common-directory/IMOGEN/output_62892_cppengine/` below). Choice rationale: methodological consistency with Methods §2.2 framing (trunk_r13078 throughout); double-precision numerics (B62-clean; no ~15-31 ppm single-vs-double precision drift); cleaner CO2_all.dat output ergonomics; warm/wet biome NPP fidelity (8/10 biomes in Smith2014/Pugh2019/Hickler2012/Friedlingstein2025GCB NPP literature range @ 2000; TIE @ 7/10 @ 2100). **δ-B Fortran-engine pipeline retained at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892/` as v1+ switchable alternative** per B57/B59 v1+ trajectory. **B57 + B59 ✅ CLOSED**. **2 new Rule #9 datapoints (#32 + #33)** discovered at session 12 day 1 (wrapper IMOGEN-root self-cp under `set -e` + FastRegrid line-1-as-header bug) + fixed; both pipelines re-run cleanly post-fix (~39 min 10-way parallel; 7/7 verification gates PASS). Tag `v0.24.0-switchable-regrid-strategy-complete` reserved for block 8.2.5 close. Full evidence: `_chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_evaluation_2026-05-27.md` (~400 LOC).

> **POST-BLOCK-8.2.5 NEXT (cluster path per user direction)**: rsync 90 GB δ-B-variant 62892 library workstation→cluster (`/bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm/forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/`) + cluster trunk binary rebuild → block 8.3 cluster smoke → block 8.4 cluster production-config delta + two-track restructure (`<SSP>_local/` + `<SSP>_cluster/` per session-11 pivot #2; main_hist.ins + main_scen.ins per SSP × 5; setup_run.sh + run_coupled.sbatch T_seq retargeting) → block 8.5 cluster MPI pre-flight → Track 2 production runs (5 SSPs × 62538 cells × 1900-2100 × strict production npatch=25+spinup=500+save_state/restart on owl genius/256 × 3-day walltime; ~5-15 h cluster wall) → SCP outputs + validation triad + paper writing + v1.0 GMD submission.

> **✅ BLOCK 8.2.4 ENGINE-SIDE FORK-PARITY REACHED (2026-05-26 session 11 day 2 close)**: trunk's C++ IMOGEN engine has been forward-ported to functional byte-identity with rebuild's lpjguess engine (~1300 LOC source-edit + 2 NEW files `forks/trunk_r13078/modules/imogenoutput.{h,cpp}`). Trunk's freshly-built `forks/trunk_r13078/build_b824/guess` binary produced ALL 5 SSP engine libraries (5 × 202 year-dirs × 443 MB = ~2.2 GB total) at `Common-directory/IMOGEN/output/` in each SSP subdir below. Phase G byte-identity verification: 250/250 ✅ md5 matches (5 SSPs × 5 sentinel years × 10 climate variables) vs rebuild's lpjguess engine output. **B61 ✅ CLOSED**. Paper Methods §2.2 framing locked in: "Both Track 1 and Track 2 use `trunk_r13078` for the LPJG ecosystem state simulations; the C++ IMOGEN engine producing Track 2 climate library is the port in `forks/trunk_r13078/modules/`, brought to functional byte-identity with rebuild's engine port at block 8.2.4." Full evidence: `_chat_artifacts/b8_2_4_trunk_engine_forwardport_2026-05-24/B8_2_4_evaluation_2026-05-26.md`. The block 8.2 Phase E lpjguess-cp'd libraries are preserved as `Common-directory/IMOGEN/output_pre_block_8_2_4_lpjguess_cp_reference/` per SSP (gitignored; for byte-identity audit reference). Block 8.0.2 predecessor-era `imogen_intermediary.ins` files preserved as `imogen_intermediary.ins.pre_block_8_2_4_predecessor_baseline` per SSP (gitignored; forensic reference). Active `imogen_intermediary.ins` is now byte-identical to rebuild's `runs/<SSP>/imogen_intermediary.ins` (modulo 4 relative-path depth-adjustments `../../` → `../../../` for DIR_PATT + DIR_CLIM + FILE_NON_CO2_VALS + FILE_GRIDLIST because trunk-runs is 1 dir deeper in the project tree).

> **✅ SWITCHABLE-REGRID-STRATEGY NOTE (post-block-8.1.5; 2026-05-22; UPDATED post-block-8.2.4 2026-05-26)**: per `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §1 POST-BLOCK-8.2.4 ordering + `forks/README.md` "Switchable-regrid-strategy" section, v1.0 paper Track 2 production runs use one of two **switchable engine+regrid pipelines** (chosen at block 8.2.5 close based on side-by-side 4-cell smoke comparison; the other stays in repo as v1+ post-paper alternative):
> - **δ-B (Fortran engine)**: `imogen/code/imogen_lpjg.f` @ 3698 → FastRegrid IDW → 62,892 → trunk-T_seq LPJG; **predecessor-architecture-matching**. Run directories: `integrated_tseq_<scenario>_wpeat_fortranengine/`.
> - **δ-B-variant (TRUNK-CPP-ENGINE post-block-8.2.4)**: `forks/trunk_r13078/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` @ 1631 native → chained FastRegrid NN 1631→3698 + IDW 3698→62,892 → trunk-T_seq LPJG; **trunk-engine-throughout per paper Methods §2.2**. Run directories: `integrated_tseq_<scenario>_wpeat_cppengine/`. Block 8.2.4 forward-port (250/250 ✅ byte-identity with rebuild) confirms trunk's engine is functionally equivalent to rebuild's; libraries already produced at `Common-directory/IMOGEN/output/` per SSP below.
>
> Block 8.4 will populate two-track `_local/` + `_cluster/` variants of these `_fortranengine/` and `_cppengine/` run directories per SSP (per user's Q2=B selection at session 11 day 1; γ-physical-separation policy extended to host-track variants). Block 8.2.5 acceptance test runs both engine pipelines at 4-cell smoke + user picks one for paper cluster production.

## Layout

```
forks/
├── README.md                            forks/ substrate doc (two-fork policy)
├── trunk_r13078/                        the trunk_r13078 LPJG fork source
│   ├── modules/imogencfx.cpp            (T_seq surgical edits per block 8.0.2)
│   ├── modules/imogencfx.h              (T_seq additions: file_tmin/tmax + storage)
│   ├── framework/parameters.{cpp,h}     (T_seq addition: skip_inprocess_engine_run)
│   ├── CMakeLists.txt                   (trunk's own CMake; build with -lcurl per NEW B48)
│   └── ...                              (verbatim upstream content elsewhere)
└── trunk_r13078_runs/                   THIS dir — trunk-Track-2 .ins + run configs
    ├── README.md                        this file
    ├── SSP1-2.6/                        SSP1-2.6 scenario .ins set (block 8.0.2)
    │   ├── main.ins                     T_seq main entry-point (NEW; authored at block 8.0.2)
    │   ├── imogen_intermediary.ins      Engine-side config (T_seq-modified; skip_inprocess=1)
    │   ├── global.ins                   Standard LPJG global config (predecessor; B12-compliant)
    │   ├── landcover.ins                LU config (predecessor; overridden in main.ins for _peatland)
    │   ├── crop_n.ins                   LandSyMM N-cycle crop pipeline
    │   ├── crop.ins                     Crop PFT config
    │   ├── crop_n_pftlist.*.ins         Crop PFT list
    │   ├── crop_n_stlist.*.ins          Crop stand list (with N-fertilisation treatments)
    │   ├── pasture_n_stlist.ins         Pasture stand list
    │   ├── wetlandpfts.ins              Wetland PFTs (CH4 source)
    │   ├── global_soiln.ins             Soil N-cycle config
    │   ├── global_coupled_imogen_lpjg.ins  Legacy coupled config (predecessor; not actively used in T_seq)
    │   ├── gridlist_in_62892_and_climate.txt  Production gridlist (62538 cells)
    │   ├── gridlist_test480.txt         Mid-size testing gridlist
    │   ├── gridlist_test2.txt           Smoke gridlist (2 cells; for quick tests)
    │   └── setup_run.sh                 Predecessor setup script (reference; not actively used in T_seq)
    ├── SSP2-4.5/                        (planned; to be populated at session 10+)
    ├── SSP3-7.0/                        (planned)
    ├── SSP4-6.0/                        (planned)
    └── SSP5-8.5/                        (planned)

    [Block 8.4 cluster-naming restructure (NEW post-block-8.1.5; per CLUSTER_SETUP §1 + B57 + B59):]
    ├── integrated_tseq_hist_wpeat_fortranengine/        (δ-B Fortran-engine pipeline; hist)
    ├── integrated_tseq_ssp126_wpeat_fortranengine/       (δ-B; SSP1-2.6 scenario)
    ├── integrated_tseq_ssp245_wpeat_fortranengine/       (δ-B; SSP2-4.5)
    ├── integrated_tseq_ssp370_wpeat_fortranengine/       (δ-B; SSP3-7.0)
    ├── integrated_tseq_ssp460_wpeat_fortranengine/       (δ-B; SSP4-6.0)
    ├── integrated_tseq_ssp585_wpeat_fortranengine/       (δ-B; SSP5-8.5)
    ├── integrated_tseq_hist_wpeat_cppengine/             (δ-B-variant C++-engine pipeline; hist)
    ├── integrated_tseq_ssp126_wpeat_cppengine/           (δ-B-variant; SSP1-2.6)
    ├── integrated_tseq_ssp245_wpeat_cppengine/           (δ-B-variant; SSP2-4.5)
    ├── integrated_tseq_ssp370_wpeat_cppengine/           (δ-B-variant; SSP3-7.0)
    ├── integrated_tseq_ssp460_wpeat_cppengine/           (δ-B-variant; SSP4-6.0)
    └── integrated_tseq_ssp585_wpeat_cppengine/           (δ-B-variant; SSP5-8.5)
```

## T_seq workflow (per `notes/B47.md` §4)

### Step A — Rebuild engine standalone (LOCAL, one-time per SSP)

Run the rebuild's IMOGEN engine standalone via the B44 productised `--engine-only-mode`:

```bash
cd <repo>
scripts/run_coupled.sh --backbone intermediary-py --coupling-mode prescribed \
                       --scenario SSP1-2.6 --smoke \
                       --no-build --no-intermediary --no-adapter \
                       --engine-only-mode
# produces runs/SSP1-2.6/Common-directory/IMOGEN/output/<year>/*.dat
# ~12.5 min wall on smoke 4-cell config
# (replace --smoke with --production for full 1900-2100 × 5 SSPs)
```

### Step B — SCP engine library to cluster (one-time; only if running Step C on cluster)

```bash
# (run from local workstation)
cd <repo>
scp -r runs/SSP1-2.6/Common-directory/IMOGEN/output/ \
       <user>@<cluster>:<cluster-run-dir>/Common-directory/IMOGEN/
# ~500 MB per SSP × 5 SSPs ≈ 2.5 GB total
# Alternative: rsync -avz for resumable transfer
```

### Step C — Trunk-T_seq LPJG standalone (LOCAL or CLUSTER)

#### Pre-run setup (LOCAL)

The trunk-T_seq `main.ins` references the engine library via `./Common-directory/IMOGEN/output/YYYY/*.dat`. Make the library accessible via a symlink:

```bash
cd <repo>/forks/trunk_r13078_runs/SSP1-2.6/
ln -s ../../../runs/SSP1-2.6/Common-directory ./Common-directory
```

For CLUSTER deployment: the engine library was SCP'd to `<cluster-run-dir>/Common-directory/` in Step B, which trunk-T_seq main.ins reads via the same relative path.

#### Local invocation

```bash
cd <repo>/forks/trunk_r13078_runs/SSP1-2.6/
../../trunk_r13078/build/guess -input imogencfx main.ins
# produces Track-2 LPJG ecosystem outputs in the current directory:
# cflux.out, cmass.out, anpp.out, mch4.out, ngases.out, etc.
```

#### Cluster invocation (legacy launcher pattern per `owl_hpc_cluster_scripts/scripts/`)

```bash
# Adapt from setup_run_owl_with_scratch_lpj_work.sh:
#   INPUTMETHOD=imogencfx (was cfx for Track 1)
#   GRIDLIST=gridlist_in_62892_and_climate.txt
#   <... existing cluster pattern ...>
# Per session 8.7 cluster sbatch wrapper update per notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md §5
```

## LOCAL vs CLUSTER path overrides

The `main.ins` uses LOCAL-default paths (`/media/bampoh-d/lpjg_input/...`) for the auxiliary inputs (SimFire, popdens, ndep, LU, soilmap). For CLUSTER deployment, each LOCAL path has an inline `! CLUSTER OVERRIDE:` comment showing the corresponding cluster path per `notes/PRODUCTION_RUN_CONFIG.md` §3.2 cluster-path-equivalence table:

| Local | Cluster |
|---|---|
| `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/` | `/bg/data/lpj/bampoh-d/landsymm_lu/` |
| `/media/bampoh-d/lpjg_input/input/fire/SimfireInput.bin` | `/bg/data/lpj/LPJ-GUESS/input/fire/SimfireInput.bin` |
| `/media/bampoh-d/lpjg_input/input/pop_dens/...` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/pop/lpjg-popd/...` |
| `/media/bampoh-d/lpjg_input/input/ndep/...` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/n-deposition/...` |

For cluster, either (a) sed-replace the local prefix to the cluster prefix in `main.ins`, or (b) maintain a parallel `main_cluster.ins` with the cluster paths uncommented.

## Block 8.0.3 acceptance test (planned)

For local 4-cell smoke acceptance test:
- Override `file_gridlist` to `../../../data/gridlist/gridlist_test2.txt` (rebuild's 4-cell smoke gridlist; same cells as B44 acceptance test produced engine library for)
- Override `firsthistyear`/`lasthistyear`/`firstoutyear`/`lastoutyear` to a small window if iterating quickly
- 8 acceptance gates G0-G7 per `notes/B47.md` §4.3

## Cross-references

- `notes/B47.md` — Option T_seq strategic decision + design + dual-fork trajectory (canonical landing record)
- `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §0.2 ✅ STRATEGIC RESOLUTION (T_seq cluster integration story)
- `notes/PRODUCTION_RUN_CONFIG.md` — production-run reference (§2 smoke→production delta, §3.1 LU forcing dataset map, §3.2 cluster path equivalence)
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` ✅ STRATEGIC RESOLUTION + §3 "Block 8.0.1 LANDED" + future "Block 8.0.2 LANDED" entry
- `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1.4 ✅ STRATEGIC CAVEAT RESOLVED
- `forks/README.md` — two-fork policy + dual-fork trajectory + build instructions
- `lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/` — predecessor `.ins` source (Track 1 cfx-mode reference)

---

_End of `forks/trunk_r13078_runs/README.md` — initial authoring at session 8.0.2 (2026-05-20 afternoon); update incrementally as additional SSPs are configured or production knobs are tuned._
