# `forks/` — sibling LPJ-GUESS fork(s) for two-fork dual-surface lifestyle

**Status**: ACTIVE — populated incrementally as backport fork(s) are brought into the rebuild repo for paper-publication runs + long-term parity work.

**✅ BLOCK 8.3 LANDED — CHOSEN δ-B-VARIANT PIPELINE OPERATIONAL ON CLUSTER (2026-05-28 session 13 day 1 close; tag `v0.25.0-cluster-trunk-tseq-smoke-complete`)**: Cluster end-to-end smoke validated end-to-end on KIT IMK-IFU owl, milan partition × 4 nodes × 64 CPUs/node = 256 ranks. Both HIST + SCEN smoke phases ran cleanly: HIST main `601955` ExitCode 0:0 in 1h29m + SCEN main `602049` ExitCode 0:0 in 9m45s (~9× faster as expected; restart from HIST state empirically validated). 8/9 acceptance gates ✅ PASS + 1/9 ⚠️ PARTIAL (benign Svalbard barren-cell SCEN edge case). Per-biome physical sensibility: 36/50 Phase F anchor cells within published Smith2014/Pugh2019/Hickler2012/Friedlingstein2025GCB literature ranges; matches Phase F's 7-8/10 standard. 2 Rule #9 datapoints surfaced + fixed across PREP + close commits (#34 cluster main.ins file_gridlist absolute-path latent defect; #35 finishup_lpj_work.sh SLURM script-cache portability bug); both empirically validated. Cluster path now operational for full 5-SSP × HIST + SCEN Track 2 production runs. Audit-evidence bundle at `_chat_artifacts/b8_3_cluster_smoke_2026-05-28/B8_3_evaluation_2026-05-28.md`.

**✅ BLOCK 8.2.5 FULL CLOSE — SWITCHABLE-REGRID-STRATEGY OPERATIONAL + δ-B-VARIANT CHOSEN FOR v1.0 PAPER (2026-05-27 session 12 day 2)**: Both switchable-regrid pipelines now built + paper-ready 62892-grid libraries available: (i) **δ-B (Fortran engine)** at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892/` (5 × 18 GB; Fortran imogen_lpjg.f native 3696 → FastRegrid IDW 62538); (ii) **δ-B-variant (trunk-C++ engine; CHOSEN for v1.0 paper Track 2)** at `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/` (5 × 18 GB; trunk-C++ climatemodel.cpp native 1631 → FastRegrid NN 3696 → IDW 62538). **Phase G user choice (~15:30 CEST 2026-05-27) = δ-B-variant** per methodological consistency with Methods §2.2 (trunk_r13078 throughout: engine + LPJG + natural-emission preprocessor); double-precision numerics (B62-clean); warm/wet biome NPP fidelity (Phase F 50-cell biome-stratified production-config smoke: 8/10 biomes in published Smith2014/Pugh2019/Hickler2012/Friedlingstein2025GCB NPP literature range @ 2000; TIE at 7/10 @ 2100). **δ-B Fortran-engine pipeline retained as v1+ switchable alternative** per B57/B59 v1+ trajectory; available for cross-engine validation studies, v1+ live-coupling trajectory exploration, or reviewer-requested supplementary materials. **B57 + B59 ✅ CLOSED**. **2 new Rule #9 datapoints (#32 + #33)** discovered + fixed at session 12 day 1 (wrapper IMOGEN-root self-cp + FastRegrid auto-detect-numeric-header). **1 new Rule #10 datapoint (#25)** self-correction on 2-axis pipeline differential (climate forcing + atmospheric CO2 both differ; CH4+N2O bit-identical as prescribed-input pass-through). Tag `v0.24.0-switchable-regrid-strategy-complete` reserved for block 8.2.5 close. Full evidence at `_chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_evaluation_2026-05-27.md` (~400 LOC).

**✅ ENGINE-SIDE FORK-PARITY REACHED AT BLOCK 8.2.4 (2026-05-26 session 11 day 2 close)**: `forks/trunk_r13078/`'s C++ IMOGEN engine has been forward-ported to **functional byte-identity** with `lpjguess/`'s engine for the engine-slice of LEDGER §1.2 Installment-2 (~1300 LOC source-edit + 2 NEW files `modules/imogenoutput.{h,cpp}`). Phase G byte-identity verification: 250/250 ✅ md5 matches (5 SSPs × 5 sentinel years × 10 climate variables). Trunk's freshly-built `build_b824/guess` binary produced 5-SSP engine libraries at `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/` (5 × ~443 MB = ~2.2 GB total). **B61 ✅ CLOSED** at this block. Paper Methods §2.2 framing locked in: "Both Track 1 and Track 2 use `trunk_r13078` for the LPJG ecosystem state simulations; the C++ IMOGEN engine producing Track 2 climate library is the port in `forks/trunk_r13078/modules/`, brought to functional byte-identity with rebuild's engine port at block 8.2.4." Residual ~1300 LOC for v1+ Installment-2 Backport Sprint (year_outer scaffolding ~500 LOC + imogen_input.{cpp,h} ~640 LOC + Fortran B33(c) ~145 LOC; not paper-blocking). Full evidence: `_chat_artifacts/b8_2_4_trunk_engine_forwardport_2026-05-24/B8_2_4_evaluation_2026-05-26.md`.

**Purpose**: house alternative LPJ-GUESS forks alongside the rebuild's primary `lpjguess/` so:
1. The rebuild's **primary fork** at `lpjguess/` continues as the **active development surface** for all v1.0+ scientific + architectural work (B45 hardcoded year sentinels; B46 N2O channel split; F-10/F-12 architectural deadlock resolution + v1.1+ tight coupling; v1.5+ ecosystem refinements; v2.0+ PLUM embedding) — uninterrupted by paper-publication runs targeting an alternative fork.
2. **Backport fork(s)** like `trunk_r13078/` (imported at session 8.0.1; 2026-05-20 afternoon) can run paper-publication runs in their own canonical state with bounded source-edit deltas vs the predecessor, while staying clearly distinct from the rebuild's primary fork.
3. Both forks are intended to live in the rebuild repo as **switchable reference implementations** (per `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §1.1's two-fork policy + the dual-fork long-term trajectory clarified at session 8.0 per `notes/B47.md` §0 + §5).

**Two-fork long-term trajectory** (user-clarified at session 8.0 mid-discussion 2026-05-20 afternoon):

- **`lpjguess/`** — the rebuild's LPJ-GUESS (imported from `LandSyMM_LPJ-GUESS` at step 1; iterated through steps 7/8/9.5/17a/17b/17c + B-series fixes through B19/B36/B37/B39/B40/B44). Active-development surface for v1.0+; all new scientific + architectural work lands here first.
- **`forks/trunk_r13078/`** — the `trunk_r13078` LPJG fork (the version the user used for Track 1 production runs via `-input cfx` + ISIMIP3b climate; produced the LPJG-natural-flux outputs feeding `intermediary_py` Component B). Brought into the rebuild repo at session 8.0.1 (structural import; ZERO source-edit at import; identical to source at `version_A/.../Integrations/trunk/trunk_r13078/` modulo the rsync exclusions for build artefacts).

  - **Installment 1** (T_seq pre-paper Track 2 enablement; blocks 8.0.2-8.0.3 of session 8): ~180-310 LOC C++ source-edit (skip_inprocess_engine_run flag + B4 8-field consumer wiring for Rh/W/Tmin/Tmax + per-year CO2.dat reader option-α + 1-line `exit(200)` regression removal at `modules/imogencfx.cpp:483`). Bare-minimum state to run Track 2 as standalone LPJG-only consumer of the rebuild engine's pre-baked per-year ASCII climate + atm-conc library.
  - **Installment 2** (post-paper Backport Sprint per ledger §1.2; sessions 15+): ~2900-3100 LOC remaining for full fork-parity (year_outer scaffolding + `imogenoutput.cpp` + `climatemodel.cpp` engine-side delta + framework.cpp year_outer + Fortran `imogen_lpjg.f` deltas including step-3 ALLOCATABLE + B10 alternating-year fix + B33(c) WARN_POSIX_CONCAT_COLLAPSE). Brings `forks/trunk_r13078/` to switchable-alternative parity with `lpjguess/`.

  **End state**: `forks/trunk_r13078/` and `lpjguess/` are switchable alternatives — same physics; same coupling capability; user/CI chooses which binary to build + run; outputs cross-checked between forks for paper publications.

## Switchable-regrid-strategy for v1.0 paper production runs (NEW post-block-8.1.5)

Per block 8.1.5 architectural clarification (2026-05-22; canonical findings .md at `_chat_artifacts/b8_1_5_architectural_clarification_2026-05-22/B8_1_5_architectural_clarification_findings_2026-05-22.md` §13), the v1.0 paper Track 2 production runs adopt a **switchable-regrid-strategy** with multiple interchangeable alternatives sharing common infrastructure (intermediary_py upstream + FastRegrid post-engine + LPJG `forks/trunk_r13078/` consumer). The active alternatives for v1.0 are:

| Option | Engine implementation | Engine native output grid | Regrid pathway | LPJG run | Status |
|---|---|---|---|---|---|
| **α** | C++ port `lpjguess/modules/climatemodel.cpp` | 1631 (native pattern grid; REGRID is dead code) | in-consumer NN-within-50°-Euclidean (in `imogencfx::lon_lat_lines_in_file()`) | @ 62,892 | ✅ SSP1-2.6 library complete; 4 remaining SSPs at block 8.2 |
| **β** | Fortran `imogen/code/imogen_lpjg.f` | 62,892 (REGRID=.TRUE.; NGPOINTS=62,892) | engine-side NN (in REGRID_CLIM helper) | @ 62,892 | Available; v1.1+ scope |
| **δ-A** | Fortran (same as β/δ-B) | 3698 (REGRID=.TRUE.; NGPOINTS=3698) | engine-side NN to 3698 + post-process FastRegrid IDW for figures only | @ 3698 (NOT 62,892) | Available; v1.1+ scope |
| **δ-B** ⭐ | Fortran (same as β/δ-A) | 3698 (REGRID=.TRUE.; NGPOINTS=3698) | engine-side NN to 3698 + external FastRegrid IDW to 62,892 | @ 62,892 | **v1.0 paper candidate (Fortran-engine pipeline; predecessor-architecture-matching)** |
| **δ-B-variant** ⭐ | C++ port `climatemodel.cpp` (same as α; faithful Fortran translation per climatemodel.cpp:2) | 1631 (no engine-side regrid; native) | external FastRegrid IDW 1631 → 62,892 (skip 3698 intermediate; engine uses its native output grid) | @ 62,892 | **v1.0 paper candidate (C++-engine pipeline; rebuild-native engine validation)** |

**v1.0 paper Track 2 production runs**: choose ONE of δ-B vs δ-B-variant at block 8.2.5 close (after side-by-side 4-cell smoke comparison). Both pipelines stay in repo as switchable infrastructure for v1.1+ post-paper development (e.g., live-coupling work uses C++ engine path; backport-fork-parity work uses Fortran engine path; either can serve as future paper sensitivity comparable). Per `notes/FOLLOWUPS.md` B57 (block 8.2.5 wiring) + NEW **B59** (δ-B-variant decision).

**Naming convention for δ-B / δ-B-variant run directories** (from block 8.4 onward):

| Pipeline | Trunk-T_seq run dir (cluster) | Engine-library subdir |
|---|---|---|
| δ-B (Fortran engine) | `forks/trunk_r13078_runs/integrated_tseq_<scenario>_wpeat_fortranengine/` | `Common-directory-fortranengine/IMOGEN/output_3698/<year>/` (raw) + `output_62892/<year>/` (post-FastRegrid) |
| δ-B-variant (C++ engine) | `forks/trunk_r13078_runs/integrated_tseq_<scenario>_wpeat_cppengine/` | `Common-directory/IMOGEN/output/<year>/` (existing 1631 native) + `Common-directory/IMOGEN/output_62892_cppengine/<year>/` (post-FastRegrid) |

This naming makes the engine implementation explicit in cluster file listings and `setup_run.sh` invocations.

## Layout

```
forks/
├── README.md             this file
└── trunk_r13078/         the trunk_r13078 LPJG fork (imported at session 8.0.1 from
                          version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/
                          via rsync with build/dev exclusions; 23 MB / 346 files)
    ├── .gitignore        trunk's own internal .gitignore (preserved verbatim from upstream)
    ├── CMakeLists.txt    trunk's own CMake build system (used by `cd forks/trunk_r13078 && mkdir build && cd build && cmake .. && make`)
    ├── benchmarks/       trunk's benchmark test suite (~20 benchmarks; not exercised by rebuild CI initially)
    ├── cmake/            CMake toolchain helpers
    ├── command_line_version/  trunk's command_line_version main entry (used for the `guess` binary)
    ├── cru/              CRU input format support (legacy)
    ├── data/             trunk's reference data + `data/ins/integrated-4.1-ins/` predecessor .ins file set
    ├── doxygen/          doxygen config (cosmetic; not required for build)
    ├── framework/        trunk's framework/ tree (framework.cpp + parameters.cpp + etc.; LPJG core)
    ├── libraries/        trunk's libraries/ tree (plib + guessnc + gutil)
    ├── modules/          trunk's modules/ tree (canexch + landcover + cfxinput + imogencfx + climatemodel + etc.; the LPJG numerical kernels)
    ├── parallel_version/ trunk's parallel_version/ (cluster MPI entry point)
    ├── reference/        trunk's reference outputs + figures
    ├── tests/            trunk's unit tests
    ├── windows_version/  Windows build configuration (cosmetic; not exercised on Linux)
    └── ...               (LICENCE.TXT, readme.txt, GitlabDockerFile, .gitlab-ci.yml — all preserved as-is from upstream)
```

**Excluded by rsync at import** (recreated locally as needed; not committed):
- `build_*/` (build artefacts; ~24 MB at upstream)
- `.vscode/` (developer IDE config; ~few KB)
- `*.o`, `guess` (compiled artefacts; ~3 MB)
- `*.log`, `qsat_output.txt` (runtime debug dumps)
- `.git/` (none present in upstream; defensive exclude)

All of these match patterns in the rebuild's top-level `.gitignore` so they're auto-ignored at all paths (including under `forks/trunk_r13078/`). No `.gitignore` update was needed at session 8.0.1.

## Build instructions

**Primary fork** (`lpjguess/`; the rebuild):

```bash
cd lpjguess
mkdir -p build && cd build
cmake -DCMAKE_EXE_LINKER_FLAGS="-lcurl" ..
make -j$(nproc)
# produces ./guess binary
```

**Backport fork** (`forks/trunk_r13078/`; post-session-8.0.1):

```bash
cd forks/trunk_r13078
mkdir -p build && cd build
cmake -DCMAKE_EXE_LINKER_FLAGS="-lcurl" ..
make -j$(nproc)
# produces ./guess binary in this directory
# (a separate guess binary from lpjguess/build/guess; the two forks are
#  independent + can be built side-by-side without interference)
```

**Why the explicit `-DCMAKE_EXE_LINKER_FLAGS="-lcurl"`** (added at session 8.0.1 baseline build verification; tracked as NEW B48 per `notes/FOLLOWUPS.md`):

On Ubuntu 24.04+ with `libhdf5-310:amd64` >= 1.14.5+repack-3build1, HDF5's `libhdf5_serial.so.310` has a transitive runtime dependency on `libcurl@CURL_OPENSSL_4` symbols (e.g., `curl_global_init`, `curl_easy_perform`) that the linker doesn't auto-resolve via the existing `find_package(NetCDF)` / `find_package(HDF5)` chains in either fork's `CMakeLists.txt`. The workaround is the explicit `-lcurl` linker flag (libcurl is present on the system but not linked-against unless requested). The proper long-term fix (filed as **NEW B48** at session 8.0.1 close) is to add `find_package(CURL REQUIRED)` + `target_link_libraries(guess PRIVATE CURL::libcurl)` to both forks' `CMakeLists.txt`; ~5 LOC each; TRUNK-RELEVANT to both `lpjguess/` (rebuild) AND `forks/trunk_r13078/` (backport fork).

**Pre-session-8.0.1 fresh-build status**: the rebuild's pre-built binaries at `lpjguess/build/guess` (~2.97 MB; linked 2026-05-16) + `lpjguess/build_mpi/guess` (~2.90 MB; linked 2026-05-16) still WORK because they were linked before the system libcurl/HDF5 update. Any FRESH build from session 8.0.1 onward requires the `-lcurl` workaround until B48 patches the `CMakeLists.txt` permanently.

Both forks expect the same system dependencies (gcc/g++, cmake >= 3.10, NetCDF-C, NetCDF-Fortran, HDF5, libcurl, optionally OpenMPI for the parallel build). See `docs/build.md` for the canonical rebuild build instructions (which apply mutatis mutandis to the trunk fork).

## Operational invocations

**Rebuild engine standalone** (Step A of T_seq workflow per `notes/B47.md` §4.1; B44 productised at `scripts/run_coupled.sh`):

```bash
cd <repo-root>
scripts/run_coupled.sh --backbone intermediary-py --coupling-mode prescribed \
                       --scenario SSP1-2.6 --smoke \
                       --no-build --no-intermediary --no-adapter \
                       --engine-only-mode
# produces runs/SSP1-2.6/Common-directory/IMOGEN/output/<year>/*.dat
# 8-field climate + per-year CO2.dat (8-col) + WET.dat per year
# ~12.5 min wall on smoke 4-cell config; ~63 min wall × 5 SSPs at production
```

**Backport-fork LPJG against pre-baked engine library** (Step C of T_seq workflow per `notes/B47.md` §4.2; pending block 8.0.2 source-edit + 8.0.3 acceptance test):

```bash
cd <repo-root>
# (After block 8.0.2 has applied the ~180-310 LOC source-edit + authored .ins files)
forks/trunk_r13078/build/guess -input imogencfx forks/trunk_r13078_runs/SSP1-2.6/main.ins
# reads pre-baked climate from runs/SSP1-2.6/Common-directory/IMOGEN/output/<year>/
# via skip_inprocess_engine_run=1 + DIR_COMMON pointing at the engine library
# produces Track-2 LPJG ecosystem outputs in forks/trunk_r13078_runs/SSP1-2.6/output/
```

**Primary-fork LPJG (rebuild) coupled run** (the standard rebuild workflow; not affected by T_seq):

```bash
cd <repo-root>
scripts/run_coupled.sh --backbone intermediary-py --coupling-mode prescribed \
                       --scenario SSP1-2.6 --smoke
# uses lpjguess/build/guess; engine runs in-process via imogencfx::init's
# RUN_IMOGEN_ENGINE call; LPJG main loop runs against engine output
```

## Cross-references

- `notes/B47.md` — Option T_seq strategic decision + design + dual-fork long-term trajectory (canonical landing record for this `forks/` substrate)
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §1.1 (two-fork policy) + §1.2 (Backport Sprint workflow) + ✅ STRATEGIC RESOLUTION at top (refined two-installment trajectory under T_seq)
- `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §0.2 ✅ STRATEGIC RESOLUTION (T_seq cluster integration story)
- `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1.4 ✅ STRATEGIC CAVEAT RESOLVED (Axis 4 LPJG-version held constant under T_seq)
- `notes/FOLLOWUPS.md` B47 row
- `docs/build.md` (canonical build instructions for the rebuild; analogous for trunk fork)
- `docs/scientific_framework.md` §5.3 (mutual-exclusion invariant + no-double-counting; engine-side; the rebuild's engine is what runs in T_seq Step A)

## License + provenance

The `trunk_r13078/` source is the LPJ-GUESS trunk revision r13078 as imported into the predecessor framework at `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/`. Per `LICENCE.TXT` inside that subdir, terms apply unchanged. The rebuild's import at session 8.0.1 (2026-05-20 afternoon) is a verbatim copy of the upstream source modulo build/dev artefact exclusions; any modifications post-import are documented in `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 (running ledger of source-edits) + per-commit narrative in `CHANGELOG.md`.

---

_End of `forks/README.md` — initial authoring at session 8.0.1 (2026-05-20 afternoon); update incrementally as additional forks are imported or trunk_r13078 is brought toward Installment-2 full fork-parity._
