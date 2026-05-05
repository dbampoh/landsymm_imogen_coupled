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

### F-5 — Stage emission scenarios into a 5th tarball

- **Trigger**: `imogen/emiss/README.md` says step 6 will roll the small
  reference emission files (and other RCP/SSP scenarios at
  `version_A/.../emiss/{DKB_dataset_totals,new_emission_data,rcp_database}/`)
  into a 5th tarball: `imogen-emiss-historical-cmip5-v1.0.tar.gz`.
- **Action**: at step 6, when populating `data/`, also tar up the full
  set of historical + scenario emission ASCII files, hash them, and add
  a row to `tools/imogen_data_manifest.txt`.
- **Timing**: step 6 of the formal V.1 plan.

---

## DONE

_(Closed items go here in reverse-chronological order, with closing
date and short note. None yet.)_
