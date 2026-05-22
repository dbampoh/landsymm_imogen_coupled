# `forks/trunk_r13078_runs/` — trunk-Track-2 T_seq production-run configurations

**Status**: ACTIVE — populated incrementally as Track 2 production runs per SSP are configured at block 8.0.2 onwards.

**Purpose**: house the trunk-Track-2 T_seq `.ins` files + run-directory structure for v1.0 paper-publication Track 2 production runs per `notes/B47.md` §4. Sibling to `forks/trunk_r13078/` (the source tree imported at block 8.0.1 + minimally source-edited at block 8.0.2). This dual-sibling structure preserves the rebuild's primary fork (`lpjguess/` + `runs/`) untouched while keeping the trunk backport fork's source AND its run configurations clearly co-located + version-controlled.

> **✅ SWITCHABLE-REGRID-STRATEGY NOTE (post-block-8.1.5; 2026-05-22)**: per `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §1 POST-BLOCK-8.1.5 ordering + `forks/README.md` "Switchable-regrid-strategy" section, v1.0 paper Track 2 production runs use one of two **switchable engine+regrid pipelines** (chosen at block 8.2.5 close based on side-by-side 4-cell smoke comparison; the other stays in repo as v1+ post-paper alternative):
> - **δ-B (Fortran engine)**: `imogen/code/imogen_lpjg.f` @ 3698 → FastRegrid IDW → 62,892 → trunk-T_seq LPJG; **predecessor-architecture-matching**. Run directories: `integrated_tseq_<scenario>_wpeat_fortranengine/`.
> - **δ-B-variant (C++ engine)**: `lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` @ 1631 native → FastRegrid IDW → 62,892 → trunk-T_seq LPJG; **rebuild-native engine validation**. Run directories: `integrated_tseq_<scenario>_wpeat_cppengine/`.
>
> Block 8.4 will populate these `_fortranengine/` and `_cppengine/` run directories per SSP (hist + 5 SSPs × 2 engine pipelines = 12 total run dirs). Block 8.2.5 acceptance test runs both at 4-cell smoke + user picks one for paper cluster production. Per **NEW B59** filing in `notes/FOLLOWUPS.md`.

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
