# Pending follow-ups (non-blocking)

Action items that came out of the rebuild steps but aren't blocking
the next step. Tracked centrally here so nothing falls through the
cracks. Each item lists: the **trigger** (which step / decision raised
it), the **action** to take, and the **suggested timing** (when it
ought to be done).

When an item is closed, move it from the **OPEN** section to **DONE**
with the closing date. Do not delete; the audit trail is valuable.

---

## OPEN

### F-1 — Upload IMOGEN data tarballs to a permanent host

- **Trigger**: step 4 (`notes/STEP_4.md` §3 + §9). Decision #5 (incremental
  rebuild, single-codebase) plus the chosen Option C (external fetch
  script + checksum manifest) over Options A/B/D.
- **State**: 4 tarballs (49 MB total) sit at the sibling path
  `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm_data/`
  on the workstation. They are NOT on a public host yet, so a fresh
  clone of the repo cannot run `tools/fetch_imogen_data.sh` against
  an `https://` base — only against a local-directory base.
- **Action**: pick a host and upload. Two recommended options:
  | Host | Pros | Cons | Notes |
  |---|---|---|---|
  | **Zenodo** | DOI for citation; permanent archival; 50 GB/record; integrates with GitHub for release-triggered uploads | A bit more friction (per-version DOI, separate web UI for new versions) | Best fit for the GMD paper's "Code & data availability" statement |
  | **GitHub Releases** | Easier dev iteration; tied to git tags directly via `gh release`; `gh release create` from CLI | 2 GB per-asset cap (we're under 19 MB so fine); no DOI; vendor lock | Best fit for fast-cycle development |
  | (combo) | Use GitHub Releases during development; promote to Zenodo at v1.0 | | Recommended path |
- **After upload**:
  1. Edit `tools/README.md` to add the canonical `IMOGEN_DATA_BASE`
     URL example (e.g. `https://zenodo.org/record/<id>/files` or
     `https://github.com/dbampoh/landsymm_imogen_coupled/releases/download/v0.4.0-imogen-data/`).
  2. Edit `imogen/patterns/README.md` and
     `imogen/CRUNCEP_1960_1989/README.md` to replace the "TBD: a Zenodo
     record / GitHub Release / institutional bucket" wording with the
     real URL.
  3. Verify end-to-end on a fresh worktree:
     `IMOGEN_DATA_BASE=https://... tools/fetch_imogen_data.sh`
  4. Update `CHANGELOG.md` under `[Unreleased]` (or open a new
     `[v0.4.1-imogen-data-host-live]` patch entry) describing the
     change. Push to all three remotes.
- **Timing**: before the project becomes externally visible (paper
  submission, code release announcement). Not blocking step 5+.

### F-2 — Investigate Fortran writer 2× line count for `T_anom.dat`

- **Trigger**: step 4 (`notes/STEP_4.md` §6 "Comparison with version_A's
  1871 output"). Our Fortran's `T_anom.dat` has 3262 lines vs
  `version_A`'s 1631 lines — exactly 2× — at otherwise-similar formatting.
- **Hypotheses to check**:
  1. The Fortran writer iterates the cells twice (once for the 1631-cell
     native grid + once for the 3698-cell extended grid even though
     `REGRID=.FALSE.`); but 1631 × 2 = 3262, NOT 1631 + 3698 = 5329, so
     this is unlikely.
  2. A `NSDMAX`-related sub-day-step write that doubles the row count.
  3. A genuinely doubled write loop (e.g. write each cell once for
     the daily-mean and once for some other aggregate).
  4. version_A's reference was generated with a different (possibly
     CMIP3 native) grid that genuinely had 1631 cells, while ours is
     scaling to a different grid.
- **Where to look**: the per-year writer block in `imogen_lpjg.f` (search
  for `T_anom.dat` and `OPEN(...)` near the year-end output). Compare
  line counts against C++ `climatemodel.cpp`'s writer block.
- **Timing**: low priority. The output is structurally and numerically
  sane; this is a format/footprint discrepancy, not a physics bug.
  Schedule against step 9.5 (the parity work where Fortran ↔ C++
  output formats are reconciled).

### F-3 — Numerical parity: Fortran ↔ C++ IMOGEN

- **Trigger**: Decision #2 ("Phase 1 = Fortran with `ALLOCATABLE`
  arrays; Phase 2 = C++ refactor brought to numerical parity"). Step 4
  smoke-run revealed T values differ 0.1–8 K between our Fortran and
  `version_A`'s (probably-C++) reference for the same year, same GCM,
  same CRUNCEP base.
- **Action**: this is the **Phase-2 milestone** — not a tactical
  follow-up. Listed here only so it's not forgotten. Phase 2 plan is
  in `EXECUTION_PLAN.md` §II.2. Should run after v1.0 ships.
- **Timing**: post-v1.0.

### ~~F-4~~ — _CLOSED 2026-05-06 by step 7_

(Was: bug C2/C3 source fix — the polling-loop `DONE_EXIST` default;
see DONE section.)

### ~~F-5~~ — _CLOSED 2026-05-06 by step 6_

(Was: stage emission scenarios into a 5th tarball; see DONE section.)

### F-6 — Confirm CMIP6 `ql1_patt` unit alignment with IMOGEN's `DRH15M_PAT`

- **Trigger**: step 5 (`notes/STEP_5.md` §2 CAVEAT-A; §4.4). The CMIP6
  NetCDF stores `ql1_patt` with units "K-1", suggesting it represents
  delta(specific-humidity) per K of land-mean warming. The CMIP5
  ASCII column 4 (`DRH15M_PAT`) is a relative-humidity sensitivity per
  K. These are not the same physical quantity in general (they differ
  by a temperature-dependent saturation factor).
- **Symptom**: in our converted CMIP6/MRI-ESM2-0 output for cell
  (lat=82.5°, lon=281.25°, Jan), col 4 is +0.00014 — about 1500×
  smaller in magnitude than CMIP5/IPSL-CM5A-MR's -0.2364 at the same
  cell. Magnitude AND sign differ.
- **Action**: contact the upstream CMIP6 NetCDF author (likely PRIME /
  Mathison 2025) to confirm the convention. Either:
  1. The CMIP6 generator already aligned to IMOGEN's RH-sensitivity
     convention and the difference is just inter-GCM scatter (then no
     code change needed; document and close).
  2. The CMIP6 file is a specific-humidity sensitivity that needs a
     unit-conversion factor (e.g. multiply by `dRH/dq` evaluated at
     monthly mean T) before being written to col 4.
- **Workaround until closed**: we pass `ql1_patt` through directly.
  If a CMIP6-driven IMOGEN run produces hydrologically odd output
  (e.g. unphysical RH, broken precip-evap balance), revisit this.
- **Timing**: medium priority. Wait for the upstream author. If a
  CMIP6 GCM is selected for a published v1.0 run, this should be
  resolved before submission.

### F-7 — Verify CMIP6 `pstar_patt` units match CMIP5 `DPSTAR_C_PAT`

- **Trigger**: step 5 (`notes/STEP_5.md` §4.4). Our converted CMIP6/MRI
  Pstar pattern at cell (lat=82.5°, lon=281.25°, Jan) is **−49.40**;
  CMIP5/IPSL at the same cell is **+0.32**. That's a 150× magnitude
  difference plus opposite sign.
- **Possible explanations**:
  1. The CMIP6 NetCDF stores Pstar in **Pa/K** while the CMIP5 ASCII
     stores it in **hPa/K**. 100× factor would convert -49.40 Pa/K to
     -0.494 hPa/K — same order of magnitude as IPSL's +0.32, with
     reasonable inter-GCM scatter.
  2. The CMIP6 file genuinely has an opposite-sign response at this
     polar cell (different model physics).
  3. A bug in our interpolation or transform.
- **Action**: contact the upstream NetCDF author to confirm units;
  fix the converter's transform if needed. Likely a one-line fix
  (`* 0.01` to convert Pa/K → hPa/K).
- **Workaround until closed**: documented in `notes/STEP_5.md` §4.4.
- **Timing**: medium priority; same authoring contact as F-6 so can
  be batched with that.

### F-9 — Complete the half-scaffolded miscoutput IMOGEN climate-input diagnostic outputs

- **Trigger**: step 8 (`notes/STEP_8.md` §2.1, §3.5). While
  investigating where step 8's LPJG-side handshake writer should live,
  discovered that `lpjguess/modules/miscoutput.cpp/h` already contains
  **half-scaffolded IMOGEN diagnostic-output stubs**: 12 file-name
  parameters declared via `declare_parameter("file_t_anom",
  &file_t_anom, ...)` (and 11 other variables: file_p_anom,
  file_sw_anom, file_dtemp_anom, file_wet, file_fa_ocean,
  file_dtemp_o, file_co2, file_relhum_anom, file_tmin_anom,
  file_tmax_anom, file_wind_anom), 12 corresponding `Table out_*_anom`
  member declarations in the header — **but no `create_output_table()`
  calls in `define_output_tables()` and no `add_value()` calls in
  `outannual()`**. The whole pipeline is inert. A `// FIXME: DKB`
  marker at line 122 of miscoutput.cpp explicitly flags the
  work-in-progress state.
- **What scope F-9 covers**:
  - Add `create_output_table(out_t_anom, file_t_anom, ...)` calls
    in `MiscOutput::define_output_tables()` for the 12 diagnostic
    tables.
  - Add per-gridcell `outlimit(out, out_t_anom, ...)` calls in
    `MiscOutput::outannual(Gridcell&)` that write the actual IMOGEN
    climate values (T_anom, P_anom, etc. — the variables IMOGEN
    supplied to LPJ-GUESS for each year × each cell). The data source
    is `imogencfx`'s per-cell `dtemp[]`, `dprec[]`, `dinsol[]`,
    `ddtr[]`, `drelhum[]`, `dwind[]` arrays (see imogencfx.h:128-148).
- **Difference from step 8 (already implemented)**: step 8's
  `imogenoutput.cpp/h` writes the LPJG → IMOGEN handshake control
  files (`imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt`,
  `imogen_lpjg.txt`, `done`). F-9's miscoutput stubs would write the
  IMOGEN → LPJG climate-input diagnostics (`t_anom.out`, `p_anom.out`,
  etc.) as standard `.out` tabular files for users to inspect what
  climate IMOGEN supplied. **Different output channels for different
  purposes.**
- **Cleanup pre-completed**: step 8 already removed the dead
  `getImogenData(int, int)` random placeholder helper from
  `miscoutput.h` (it returned non-deterministic random values from
  `std::random_device`; was never invoked anywhere; misleading
  semantically). Plus removed the unused `#include <random>`. F-9
  starts from a slightly cleaner base.
- **Best timing**: step 9.5 of the formal V.1 plan, alongside the
  Rh_anom / W_anom / Tmin_anom / Tmax_anom output parity work
  (climate-output enhancements per Decisions #11 and #12). Both
  concern climate-output diagnostics; bundling them shares review
  effort.

### F-10 — Framework-loop ordering vs proper tight-coupling synchronization (significant)

- **Trigger**: step 8 (`notes/STEP_8.md` §2.4 + §4). While
  investigating where step 8's `imogenoutput.cpp` should hook into
  the LPJ-GUESS framework's per-year aggregation flow, discovered
  the canonical loop structure of `lpjguess/framework/framework.cpp`
  lines 411-516:

  ```cpp
  while (true) {                                           // outer: per-gridcell
      Gridcell gridcell;
      if (!input_module->getgridcell(gridcell)) break;
      // ... setup ...
      while (input_module->getclimate(gridcell)) {         // inner: per-day, ALL years
          simulate_day(gridcell, input_module.get());
          output_modules.outdaily(gridcell);
          if (date.islastday && date.islastmonth) {
              output_modules.outannual(gridcell);          // year-end, per gridcell
          }
          date.next();
      }
      // End of all-years loop for THIS gridcell
  }
  ```

  `getclimate()` returns false when ALL years have been simulated for
  the current gridcell. So **each gridcell processes ALL its years
  before moving to the next gridcell**. This is per-gridcell-outer /
  per-day-inner across all years.

- **The architectural problem**: Tight coupling (per-year-globally-
  synchronized handshake — IMOGEN's year-N+1 climate uses LPJ-GUESS's
  year-N globally-aggregated NEE feedback) **fundamentally cannot be
  cleanly implemented** with this loop ordering. When gridcell-1
  finishes year-1, gridcell-2 hasn't yet started year-1 (it's still
  on the next gridcell setup phase). When gridcell-1's `outannual`
  fires for year-1 and our handshake writer flushes, the flushed NEE
  represents only gridcell-1's contribution. Subsequent gridcells'
  year-1 contributions arrive at later wall-clock times, after the
  IMOGEN engine has already consumed the (incomplete) handshake.

- **Why this surfaced now and not earlier**: The predecessor framework
  already has this issue — but [CMI §1.1] specifically notes "the
  system has never run end-to-end." The predecessor's coupled mode
  was **scaffolded but never validated**; the polling loop in
  `imogen_lpjg.f` and `climatemodel.cpp` had been "neutered" (bugs
  C2/C3) to make standalone runs work, masking the synchronization
  problem from ever surfacing in practice. With step 7's fixes
  un-neutering those polling loops + step 8 actually writing the
  handshake files, the architectural gap is now exposed.

- **Implication for v1.0**:
  - `imogenoutput.cpp` (step 8) writes per-gridcell-rolling values:
    each `outannual` call adds this gridcell's contribution to the
    per-year accumulator, and the year-change-detection flushes
    whenever the year-N+1 first gridcell triggers it. The flushed
    values are non-empty, sensible per-gridcell-rolling, but NOT
    globally-synchronized.
  - V.1's stated step-8 verification milestone (*"non-empty handshake
    files; sensible NEE in PgC/yr"*) is met — the values look right
    in magnitude.
  - V.1's step-17 validation milestone (*"CO2 RMSD ≤ 5 ppm vs NOAA
    GMD"*) **may show systematic bias** from the non-synchronized
    feedback. We will discover empirically at step 17 whether the
    bias is significant. If yes → F-10 becomes blocking for v1.0
    publication-quality runs. If no → F-10 can stay deferred.

- **Phase-2 recommended approach (per user guidance 2026-05-06)**:

  Three principles, in order of importance:

  1. **DO NOT alter the existing framework.cpp loop**. The
     per-gridcell-outer ordering is correct and battle-tested for
     standalone, loose-coupling, prescribed-coupling, and parallel
     (HPC) runs. Restructuring it would risk breaking all of those.

  2. **DO add a runtime parameter** that gates a NEW per-year-outer /
     per-gridcell-inner code path which lives ALONGSIDE the existing
     code path. Example parameter:
     `framework_loop_mode = "year_outer" | "gridcell_outer"` (default
     `"gridcell_outer"` to preserve backward compatibility).

  3. **DO implement the new code path as an additive extension**,
     mirroring the **LandSyMM-fork-into-LPJ-GUESS-LTS integration
     pattern** from the predecessor project earlier in the chat
     history. In that integration: new fork-specific behavior was
     gated behind `do_potyield`, `landsymm_*`, etc. ins parameters
     that activated alternative code paths; the upstream LTS
     behavior was preserved as the default and untouched.

  Concrete implementation sketch (subject to refinement at Phase 2):

  ```cpp
  // framework.cpp -- new alternative loop, gated on framework_loop_mode
  if (loop_mode == "year_outer") {
      // Phase-2 path: per-year-outer / per-gridcell-inner
      load_all_gridcells_into_memory(gridlist);  // up-front
      for (int year = first_year; year <= last_year; ++year) {
          for (auto& gridcell : gridcells) {
              simulate_year(gridcell, year);
              output_modules.outannual(gridcell);
          }
          // ALL gridcells now done for year N; flush handshake here
          imogenoutput.flush_pending_year();
          // Trigger IMOGEN engine for year N+1's climate
          if (coupling_mode == "tight") {
              climatemodel.run_year(year + 1);
          }
      }
  } else {  // default gridcell_outer
      // Existing loop unchanged
      while (true) {
          Gridcell gridcell;
          if (!input_module->getgridcell(gridcell)) break;
          while (input_module->getclimate(gridcell)) { /* ... */ }
      }
  }
  ```

  Trade-offs for the year-outer path:
  - Memory: must hold all gridcells in memory simultaneously
    (vs streaming one at a time). For 62 538 cells × ~MB-each
    in-memory state → ~tens of GB. Workable on workstation, large
    on cluster nodes. Mitigation: per-rank gridlist subsetting
    in MPI mode (existing predecessor cluster pattern).
  - I/O: per-year `outannual` calls happen at very different wall-
    clock times in the existing path; bundled tightly in the new
    path. Disk I/O patterns shift; may need re-tuning.
  - Determinism: the new path is deterministically per-year; the old
    path is per-gridcell-with-eventual-aggregation. Outputs would
    differ in subtle ways; cross-validation is essential.

  Both paths sharing the same `imogenoutput.cpp::outannual` and
  `flush_pending_year` interfaces means the writer code itself
  doesn't need to change. Only the framework's call orchestration
  changes.

- **Action timing**:
  - **Now (v1.0)**: documented in this F-10 entry; cross-referenced
    from `notes/STEP_8.md`, `lpjguess/modules/imogenoutput.h` doc
    block, `EXECUTION_PLAN.md` step 8 row.
  - **Step 17** (validation): empirically test whether the
    per-gridcell-rolling handshake passes V.1's RMSD thresholds.
    Document outcomes.
  - **Phase 2 (post-v1.0)**: implement the parameter-gated
    additive year-outer code path. Estimated effort 1-2 weeks
    full-time including cross-validation.

- **Cross-references**:
  - `notes/STEP_8.md` §2.4 (the investigation finding), §4 (the
    detailed Phase-2 recommendation)
  - `lpjguess/modules/imogenoutput.h` doc block (mirrors this
    architectural caveat in the source code itself)
  - `EXECUTION_PLAN.md` V.1 step 8 row (marked ✅ with F-10 caveat)
  - `[CMI §1.1]` (the original "never ran end-to-end" note that
    F-10 formalizes the cause of)

### F-11 — Backport all `lpjguess/` changes to `trunk_r13078` for paper-stage consistency

- **Trigger**: user clarification 2026-05-06. Per Decision #3
  (`EXECUTION_PLAN.md` II.11), our v1.0 rebuild operates on the
  `LandSyMM_LPJ-GUESS/` fork (which the user calls the "integrated
  LTS" per terminology established in their integration project
  before this coupled-model project began — same artifact, two
  names). The **separate** `trunk_r13078` fork inside
  `version_A/Integrations/trunk/` and `version_B/Integrations/trunk/`
  was used in the working paper's **Stage 1 PLUM yield runs**, so for
  Stage-2 / paper consistency, both forks must eventually be
  fully-coupled-model-capable and runtime-switchable.
- **Action**: at the end of Phase-1 (after step 19's V.1
  verification), execute the **Backport Sprint** described in
  `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §4. In short:
  1. Import `version_A/Integrations/trunk/trunk_r13078/` as a
     parallel tree under our repo (e.g. `lpjguess_trunk_r13078/`).
  2. Reconcile the 6-file baseline diff (cosmetic + the critical
     `exit(200)` removal at `imogencfx.cpp:483`).
  3. Walk each ledger entry in `TRUNK_R13078_BACKPORT_LEDGER.md` §3
     in step order and replicate the recorded edit in
     `lpjguess_trunk_r13078/`.
  4. Add a build-time switch
     (`-DLPJGUESS_BACKEND=landsymm_fork|trunk_r13078`, default
     `landsymm_fork`) so users / CI tests can pick either backend.
  5. Run V.1's full verification (steps 1-19 milestones) against
     the `trunk_r13078` backend; cross-check outputs match within
     numerical tolerance.
- **Estimated effort**: 1-2 days of focused work.
- **Maintenance discipline (immediate, not deferred)**: every commit
  that touches `lpjguess/` C++ source files **must add a
  corresponding entry to `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3**
  with step-N / commit-hash / date / file / line range / description
  / backport-guidance fields. This is what makes the eventual sprint
  mechanical instead of archaeological.
- **Cross-references**:
  - `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (the running ledger;
    populated retroactively for steps 1-8 at creation time)
  - `EXECUTION_PLAN.md` II.11 (Decision #3 + the terminology
    clarification 2026-05-06)
  - `notes/STEP_1.md` §A (the import audit that established the
    6-file baseline diff)
  - `_phase2_findings/02_lpjguess_trunk_r13078.md` (Phase-2
    investigation of `trunk_r13078`'s coupling surface area)

### F-8 — Revisit CMIP6 wind-magnitude split + precip rain/snow partition at step 9.5

- **Trigger**: step 5 CAVEAT-B and CAVEAT-C. The CMIP6 NetCDF doesn't
  store separate U/V wind components or rain/snow split; we currently
  approximate via `U=V=wind_patt/√2` (preserves magnitude, loses
  direction) and `rain=precip, snow=0` (preserves total).
- **Action**: at step 9.5 (climate-output enhancements), if the
  approximations cause measurable downstream biases (e.g. in BLAZE
  fire model wind sensitivity, or LPJ-GUESS snow accumulation), implement
  finer splits — e.g. distribute wind direction climatologically; split
  precip by climate-zone rain/snow fraction.
- **Timing**: step 9.5 of the formal V.1 plan; only if biases manifest.

---

## DONE

### F-4 — Bug C2/C3 source fix (polling-loop `DONE_EXIST` default) — closed 2026-05-06

- **Trigger**: step 4 (`notes/STEP_4.md` §6 + `notes/FOLLOWUPS.md`
  original entry). Every standalone Fortran IMOGEN smoke run since
  step 4 needed a manual `touch LPJG_main/IMOGEN/done` because the
  polling loop's exit condition required `DONE_EXIST=.TRUE.` and the
  pre-loop default `!DONE_EXIST=.TRUE.` (line 363) was commented out.
  The C++ twin in `climatemodel.cpp:332-353` was similarly broken
  (4 lines commented out: `doneExist` INQUIRE + 3 `*Open` guards;
  a hard-coded `doneExist = true` short-circuited the safety check).
- **Resolution at step 7**:
  - **C++ side** (`lpjguess/modules/climatemodel.cpp`): restored the
    `doneExist = filesystem_dkb::exists(...)` INQUIRE + added a
    first-call bypass via the existing `firstCall` local
    (initialized from `IMOGENConfig::FIRSTCALL`); restored the 3
    `runnowOpen`, `runfluxOpen`, `runnonco2fluxOpen` guards. This
    re-engages the proper LPJG↔IMOGEN handshake safety semantics
    while still allowing first-call bootstrap.
  - **Fortran side** (`imogen/code/imogen_lpjg.f`): added a
    `CALL SYSTEM('mkdir -p ... /LPJG_main/IMOGEN')` +
    `CALL SYSTEM('touch ... /LPJG_main/IMOGEN/done')` block before
    the outer `DO WHILE (KEEPRUNNING)` loop. The auto-created file
    is then picked up by the polling loop's INQUIRE on the very
    first iteration. Idempotent (touch + mkdir -p both succeed
    whether the target exists or not).
- **Verification**: standalone IMOGEN smoke run now works
  end-to-end (years 1871, 1872 produced) **without** any pre-staged
  `done` file. Confirmed by removing all runtime state via
  `rm -rf LPJG_main IMOGEN`, re-staging only the control-file
  stubs (no `done` file), running `./imogen_lpjg`, and observing
  `DONE_EXIST = T` on the very first polling iteration.
- **Side benefit**: LPJ-GUESS's 162 unit tests still pass cleanly
  (no regression from the C2/C3/C4 fixes).
- **Documented in**: `notes/STEP_7.md` §3.1 (C2/C3), §3.3 (F-4).

### F-5 — Stage emission scenarios into a 5th tarball — closed 2026-05-06

- **Trigger**: `imogen/emiss/README.md` (step 4) flagged that step 6
  should roll the historical + scenario emission ASCII files into a
  5th tarball under the existing manifest+fetch architecture.
- **Resolution**: At step 6, the full `Data/Imogen/emiss/` tree
  (CMIP5/, CMIP6/, DKB_dataset_totals/, new_emission_data/,
  rcp_database/, plus 6 loose top-level files; ~5.2 MB raw) was
  rsynced into `imogen/emiss/`, tarballed as
  `imogen-emiss-reference-v1.0.tar.gz` (311 KB compressed; 17×
  compression on ASCII), SHA256-checksummed, and registered in
  `tools/imogen_data_manifest.txt` as the `emiss-reference`
  component. The fetch script needed zero code changes — just one
  new manifest row.
- **Side effect**: `imogen/emiss/` was restructured from the step-4
  flat-3-files stop-gap to the full predecessor framework tree, and
  `imogen/code/imogen_settings.txt`'s `FILE_*_EMITS` paths updated
  accordingly (3-line edit to add the `DKB_dataset_totals/` subdir
  prefix).
- **Verification**: `tools/fetch_imogen_data.sh --verify-only` reports
  all 6 components clean; standalone IMOGEN regression smoke run
  produces years 1871, 1872 unchanged from step-4 output.
- **Documented in**: `notes/STEP_6.md` §3, §4, §6.
