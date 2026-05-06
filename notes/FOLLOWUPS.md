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

### F-4 — Bug C2/C3 source fix (the polling-loop `DONE_EXIST` default)

- **Trigger**: step 4 confirmed the `imogen_lpjg.f:363` commented-out
  `!DONE_EXIST=.TRUE.` requires runtime workaround (pre-staging an
  empty `done` file). `[CMI §1.2]`, `[SA3 §10]`.
- **Action**: at step 7, either uncomment line 363 or add a
  `IF(FIRSTCALL) DONE_EXIST=.TRUE.` special case. Document why this
  default makes standalone runs work without the runtime stub.
- **Timing**: step 7 of the formal V.1 plan. NOT a separate follow-up;
  already on the formal step-7 task list.

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
