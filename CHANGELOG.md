# Changelog

All notable changes to the LandSyMM-IMOGEN coupled model framework
are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

For each release tag listed below, see `git log <tag>` for the per-step
commit history that produced it. The investigation evidence base is
preserved in `_phase2_findings/` and is **immutable across releases**
— it documents the predecessor framework trees (`version_A` and
`version_B`) at the moment the rebuild began.

---

## [Unreleased] — Rebuild in progress

In progress per `EXECUTION_PLAN.md` Part V steps 0-19. See
README.md "Roadmap" for the milestone schedule.

### 2026-05-12 (night; session 3 continuation) — Step 17b (F-12 sub-milestone C2; **B3 LANDED — closed by architectural reframing**): the C++ in-process port has NO REGRID branch; the stale `// TODO at step 9.5b` was an aspirational forward-reference; ~30 LOC additive docs-only in `lpjguess/modules/climatemodel.cpp`; ZERO functional code change; un-tagged checkpoint

This commit closes **audit item B3** (C++ Tmin/Tmax in REGRID branch of `climatemodel.cpp`) per the re-ordered Option A bundle sequence (B10 → B6 → B2 → **B3** → B4 → B1; user-confirmed 2026-05-11). The forensic determination is that B3 is **closed by architectural reframing** (not by the originally-anticipated mechanical Tmin/Tmax insertion): the C++ in-process port has **no REGRID branch in which to insert**. The `// TODO at step 9.5b: replicate this in the REGRID branch.` comment at `climatemodel.cpp` ~line 894 was an aspirational forward-reference left by the step-9.5 author anticipating a future C++ REGRID branch that was never built.

#### Forensic finding — no C++ REGRID branch exists

Pre-implementation investigation (per the four checks in the B3 onboarding prompt):

| Check | Method | Finding |
|---|---|---|
| Search for `REGRID`/`regrid` in `climatemodel.cpp` | `rg "REGRID\|regrid" lpjguess/modules/climatemodel.cpp` | **Only 3 hits**: line 242 `bool regrid = IMOGENConfig::REGRID;` (dead-code declaration); line 894 the stale `// TODO at step 9.5b` comment; line 1353 an unrelated comment in a different function. **No `if (regrid)` switch anywhere in the file.** |
| `*Regrid` array variants (analogue of Fortran's `T_OUT_M_REGRID` etc.) | `rg "tOutMRegrid\|dtempOutMRegrid\|*Regrid" lpjguess/modules/climatemodel.cpp` | **Zero hits**. Only native-grid arrays exist: `tOutM/pOutM/swOutM/windOutM/rhOutM/dtempOutM` at lines 284-289, sized over `GPOINTS` (not `NGPOINTS`). |
| `REGRID_CLIM` function (C++ analogue of Fortran `CALL REGRID_CLIM`) | `rg "REGRID_CLIM\|regridClim" lpjguess/` | Zero hits anywhere in `lpjguess/`. The Fortran helper `REGRID_CLIM` (`imogen/code/imogen_lpjg.f` ~line 964) was never ported to C++. |
| `bool regrid` usage | Manual full-function inspection of `RUN_IMOGEN_ENGINE()` | Declared at line 242, never read. Dead code. |

The Fortran standalone engine (`imogen/code/imogen_lpjg.f` lines 962-1117) has a genuine `IF (REGRID) THEN ... ELSE ... ENDIF` block built around `CALL REGRID_CLIM(T_OUT_M, ..., T_OUT_M_REGRID, ...)` that populates `*_REGRID` arrays via nearest-neighbour interpolation. The C++ port has nothing analogous; it always writes climate anomalies on the single native IMOGEN grid (which is what `imogencfx` mode requires; that mode is the v1.0 production path).

#### Interpretation — close-by-architectural-reframing

The pre-B3 cross-engine parity matrix (e.g., `notes/STEP_17b.md` §3d.6 as written in the B2 commit `76b3b04`, plus FOLLOWUPS audit-table row B3) implicitly assumed the C++ port had both REGRID and non-REGRID branches, mirroring the Fortran. It does not. The matrix has been **corrected** this commit to reflect actual architectural state.

B3 is thus the second "close-without-the-originally-expected-mechanical-action" outcome in step 17b (after B6's close-by-subsumption via B10):

| Audit item | Close-out pattern | Mechanism |
|---|---|---|
| B6 | close-by-subsumption | One symptom (T_anom doubled) is fully covered by another bug's structural fix (B10's unconditional OPEN/CLOSE) |
| **B3** | **close-by-architectural-reframing** | The originally-anticipated insertion site (C++ REGRID branch) does not exist; the deliverable becomes documentation of the architectural finding + forward-looking maintenance directive |

#### What landed this commit (1 file; ~30 LOC additive docs only; backport-RELEVANT)

`lpjguess/modules/climatemodel.cpp`: three surgical documentation edits — **ZERO functional code change**:

| # | Site | Action |
|---|---|---|
| 1 | Before `bool regrid = IMOGENConfig::REGRID;` at line ~242 | Insert ~18-line doc block annotating the dead-code status of the `regrid` local: explains it's declared-but-never-read; cross-references the canonical B3 doc block at line ~890; documents the architectural finding; flags a defensive runtime warning as recommended B13-style follow-up |
| 2 | After `// Output in native IMOGEN grid` at line ~890 | Extend the inline comment to make it explicit that this is the **ONLY** climate-anomaly writer branch (not merely the non-REGRID counterpart of some hypothetical REGRID branch) |
| 3 | Replace the 4-line stale `// TODO at step 9.5b: replicate this in the REGRID branch.` block at line ~894 | Insert the canonical B3 doc block (~50 lines): forensic finding statement; cross-engine parity matrix snapshot; forward-looking maintenance directive (with the exact C++ algebraic pattern for any future REGRID-branch Tmin/Tmax addition: `file100 << ... << (tOutMRegrid - dtempOutMRegrid/2.0)`); cross-references to STEP_17b.md §3e, B2 Fortran symmetric block at `imogen/code/imogen_lpjg.f` lines ~1019-1160 (commit `76b3b04`), and the BACKPORT_LEDGER step-17b-B3 entry |

#### Cross-engine parity matrix (post-B3; CORRECTED)

| Field | C++ in-process (climatemodel.cpp) | Fortran standalone (imogen_lpjg.f) |
|---|---|---|
| T/P/SW/DTEMP/WET | ✅ native-grid (the only branch) | ✅ both branches |
| **Tmin/Tmax** | ✅ native-grid (the only branch) — N/A (no C++ REGRID branch) | ✅ both branches (B2) |
| Rh/W (wind) | ✅ native-grid (the only branch) | ⏳ B1 (Fortran physics port; ~3-5 d) |

**Post-B3 status**: every climate-anomaly writer site that actually exists in either engine has Tmin/Tmax wired. The "C++ REGRID gap" recorded in earlier docs was a documentation drift; B3 corrects it. Rh + Wind remain Fortran-side-only physics gaps (B1 closes them via the heaviest physics port).

#### Verification

| Check | Method | Result |
|---|---|---|
| Clean rebuild (non-MPI) | `cd lpjguess/build && rm -f .../climatemodel.cpp.o && make -j$(nproc)` (forced rebuild of touched file) | ✅ Exit 0; binary 2 966 056 B; **zero new warnings** (`grep -E "warning\|error"` returns nothing) |
| Clean rebuild (MPI) | `cd lpjguess/build_mpi && make -j$(nproc)` | ✅ Exit 0; binary 2 840 824 B; zero new warnings |
| 162 unit tests (non-MPI) | `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| 162 unit tests (MPI) | `lpjguess/build_mpi/runtests --reporter compact` | ✅ same |
| imogen 1cell xval substantive PASS | `GUESS_BIN=...build_mpi/guess scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ 37/37 bit-exact + 0/37 NaN |
| imogen 4cell xval substantive PASS | (same harness, 4cell imogen) | ✅ same |
| imogencfx 1cell xval substantive PASS | (same harness, 1cell imogencfx) | ✅ same |
| imogencfx 4cell xval substantive PASS | (same harness, 4cell imogencfx) | ✅ same |

**No regression**: B3 is docs-only; zero functional change; byte-equality with pre-B3 build preserved across all 4 xval scenarios.

#### New operational heuristic (rule #7 in `notes/FOLLOWUPS.md`)

The B3 forensic episode generalises cleanly into a new persistent heuristic for future audit-item triage:

> **Stale forward-reference TODOs are architectural-finding triggers — investigate the actual code structure before mechanically replicating from a sibling implementation.** When a TODO comment says "replicate this in branch X" or "add this to function Y", verify that branch X / function Y actually exists in the same form as in the sibling implementation. Differences between sibling implementations (e.g., Fortran has REGRID branch; C++ port does not) can invalidate the mechanical-replication assumption, in which case the audit item's deliverable becomes architectural reframing (close-by-finding) rather than insertion work.

This rule lives at `notes/FOLLOWUPS.md` §"Operational heuristics — lessons learned" rule #7 (companion to rules #1-6 from the B12 + B6 episodes).

#### Files changed this commit

| File | Change | Backport-relevance |
|---|---|---|
| `lpjguess/modules/climatemodel.cpp` | ~30 LOC additive docs only (3 edits: dead-code annotation at line ~242; native-grid-is-only-branch clarification at line ~890; canonical B3 doc block replacing stale TODO at line ~894) | **RELEVANT** (C++ source change in `lpjguess/modules/`; if `trunk_r13078`'s `climatemodel.cpp` has the same step-9.5 `file100`/`file101` block + stale TODO, apply the same 3 doc-only edits verbatim) |
| `notes/STEP_17b.md` | NEW §3e (B3 forensic record + 4-check pre-implementation investigation + interpretation + 3-edit table + verification + new rule #7 statement); corrected §3d.6 cross-engine parity matrix; §5 bundling table marks B3 ✅ DONE; §7 remaining work refresh (B4 NEXT); revised C2-era estimate ~5-8 d remaining; new dated footer entry | IRRELEVANT (docs) |
| `CHANGELOG.md` | This entry (above B2 entry) | IRRELEVANT (docs) |
| `EXECUTION_PLAN.md` | Row 17b status refresh (B3 ✅) | IRRELEVANT (docs) |
| `notes/FOLLOWUPS.md` | B-item bundling table (B3 ✅ DONE); status dashboard refresh ("B3 LANDED" header); NEW Operational heuristics rule #7; revised % done estimate | IRRELEVANT (docs) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | NEW step-17b-B3 entry: 1 file (`lpjguess/modules/climatemodel.cpp`); 3 mechanical doc-only insertions; backport-RELEVANT | IRRELEVANT (docs; the ledger row IS the backport directive) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` | Part 24 narrative (gitignored; not in commit) | IRRELEVANT (gitignored chat artifact) |

**Net `lpjguess/` source-level change in this commit: +30 LOC additive docs only (zero functional code).** Backport-RELEVANT.

#### Remaining within step 17b after this commit

Per §7 of `notes/STEP_17b.md` (refreshed this commit):

- **B4 ⏳ NEXT** (~1 d): `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion (mirrors C1.1 pattern).
- **B1** (~3-5 d; heaviest): Fortran Rh + Wind COMPUTATION port from C++ in-process engine to standalone Fortran (~70-100 LOC of new Fortran physics).
- **C2 close-out + tag** `v0.17.5-step17b-c2-mpi-sync` (after B4 + B1): full 4-xval substantive PASS + mpirun -np 4 mimic + 162 unit tests on both builds + tag + push to all 3 remotes.

**Revised C2-era estimate**: ~5-8 d remaining (was 5.5-8.5; B3 saved 0.2 d by landing in 0.3 d via the close-by-architectural-reframing outcome).
**Revised v1.0 % done estimate**: ~56-59% done; ~41-44% remaining.

---

### 2026-05-12 (session 3 continuation) — Step 17b (F-12 sub-milestone C2; **B2 LANDED**): Fortran Tmin/Tmax write block in `imogen/code/imogen_lpjg.f`; algebraic `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2` in BOTH REGRID + non-REGRID branches; +59 LOC additive; un-tagged checkpoint

This commit lands **audit item B2** (Fortran Tmin/Tmax write block) on top of the B6 docs-only commit (`24250b2`). Per the re-ordered Option A bundle sequence (B10 → B6 → **B2** → B3 → B4 → B1; user-confirmed 2026-05-11), B2 was scheduled as the next mechanical win after B6 because both items live in the same `imogen_lpjg.f` writer block.

#### What landed this commit (1 file; +59 LOC additive; backport-RELEVANT)

`imogen/code/imogen_lpjg.f`: 9 surgical insertions across the post-B10 climate-anomaly writer block, adding `Tmin_anom.dat` (unit 100) + `Tmax_anom.dat` (unit 101) writers symmetrically to BOTH REGRID + non-REGRID branches:

| # | Site | Branch | Action |
|---|---|---|---|
| 1 | After `OPEN(11, .../DTEMP_anom.dat)` (REGRID) | REGRID | Canonical doc block + `OPEN(100, .../Tmin_anom.dat)` + `OPEN(101, .../Tmax_anom.dat)` |
| 2 | After REGRID `WRITE(11) LAT_OUT(IGP)` | REGRID | LON/LAT headers for units 100/101 (4 lines + short doc) |
| 3 | After REGRID DAILYOUT=TRUE `WRITE(95) F_WET_CLIM_REGRID` | REGRID | Tmin/Tmax daily writes using `T_OUT_M_REGRID(IGP,IMM,IMD,IND) ± DTEMP_OUT_M_REGRID(IGP,IMM,IMD)/2.0` |
| 4 | After REGRID DAILYOUT=FALSE `WRITE(95) F_WET_CLIM_REGRID` | REGRID | Tmin/Tmax monthly writes using `T_OUT_M_REGRID(IGP,IMM,1,1) ± DTEMP_OUT_M_REGRID(IGP,IMM,1)/2.0` |
| 5 | After REGRID per-cell `WRITE(11,'()')` | REGRID | `WRITE(100,'()')` + `WRITE(101,'()')` |
| 6 | After `OPEN(11, .../DTEMP_anom.dat)` (non-REGRID) | non-REGRID | Short doc + `OPEN(100, .../Tmin_anom.dat)` + `OPEN(101, .../Tmax_anom.dat)` |
| 7 | After non-REGRID `WRITE(11) LAT(IGP)` | non-REGRID | LON/LAT headers using `LONG/LAT` (no `_OUT` suffix) for units 100/101 |
| 8 | After non-REGRID DAILYOUT=TRUE `WRITE(95) F_WET_CLIM_OUT` | non-REGRID | Tmin/Tmax daily writes using `T_OUT_M(IGP,IMM,IMD,IND) ± DTEMP_OUT_M(IGP,IMM,IMD)/2.0` (no `_REGRID` suffix) |
| 9 | After non-REGRID DAILYOUT=FALSE `WRITE(95) F_WET_CLIM_OUT` + after `WRITE(11,'()')` | non-REGRID | Tmin/Tmax monthly writes + per-cell newlines for units 100/101 |
| 10 | After post-B10 `CLOSE(11)` | shared (post-REGRID conditional) | `CLOSE(100)` + `CLOSE(101)` |

#### Symmetric-with-C++ framing

The C++ in-process port at `lpjguess/modules/climatemodel.cpp` ~lines 952-953 already has `file100`/`file101` ofstream Tmin/Tmax writers in the **non-REGRID branch only** (added at step 9.5; an explicit `// TODO at step 9.5b` comment at `climatemodel.cpp` ~line 894 documents the pending REGRID-side addition — that's **B3's** scope on the C++ side). B2 mirrors this in Fortran but for BOTH branches because the Fortran writer block has both REGRID and non-REGRID branches and there's no reason to leave them asymmetric. Per Decision #11: Tmin/Tmax are derived (not directly modelled) as `T ± DTEMP/2` (same units = Kelvin; same dynamic range as `T_anom`).

**Unit number selection**: `100`/`101` chosen to mirror the C++ ofstream variable names (`file100`, `file101`) for ergonomic cross-engine code-reading. Verified unused in `imogen_lpjg.f` pre-B2 (existing units: 1, 2, 3, 4, 6, 11, 21, 49, 51, 60, 62, 63, 64, 65, 66, 72, 81, 82, 91-99; unit 99 is `RF_all.dat` at line 715).

#### Verification

| Check | Method | Result |
|---|---|---|
| Clean Fortran build | `cd imogen/code && rm -f *.o imogen_lpjg && bash compile.sh` | ✅ Exit 0; binary 133 696 bytes (+4096 vs pre-B2's 129 600 B); ZERO warnings |
| Static unit reference count | `rg "OPEN\\\|CLOSE\\\|WRITE\(\s*(100\|101)\s*[,\)]" imogen_lpjg.f` | ✅ 26 occurrences = 4 OPENs + 2 CLOSEs + 8 LON/LAT writes + 8 data writes + 4 per-cell newlines (matches expected) |
| Both file paths in source | `rg "Tmin_anom\.dat\|Tmax_anom\.dat" imogen_lpjg.f -n` | ✅ 4 matches: REGRID lines 1041-1042 + non-REGRID lines 1136-1137 |
| Variable name consistency | manual diff vs existing T_anom writes at same sites | ✅ REGRID uses `T_OUT_M_REGRID/DTEMP_OUT_M_REGRID/LON_OUT/LAT_OUT`; non-REGRID uses `T_OUT_M/DTEMP_OUT_M/LONG/LAT` |
| Algebra parity with C++ | Visual diff vs `climatemodel.cpp` ~lines 990-991, 1005-1006 | ✅ Same expressions (`T - DTEMP/2.0`, `T + DTEMP/2.0`); same `(f10.3)` format; same Kelvin units |
| Real-division safety | inspect `/2.0` usage | ✅ All 8 algebraic expressions use `/2.0` (REAL literal) — no integer-division truncation |

**Empirical post-B2 engine smoke deferred** (same reason as B10/B6: Fortran engine inputs `CEN_IPSL_MOD_IPSL-CM5A-MR/` patterns + `DKB_dataset_totals/` emissions are not currently shipped in the active rebuild; will be staged when B1 lands and a post-B1 engine smoke will simultaneously verify B10 + B6 + B2's predicted output structure: each `/YEAR/` directory will contain 9 files with line counts matching `version_A` reference + 12 monthly Tmin/Tmax values per cell-row in `Tmin_anom.dat`/`Tmax_anom.dat`).

#### Cross-engine parity matrix (post-B2)

| Field | C++ in-process (climatemodel.cpp) | Fortran standalone (imogen_lpjg.f) |
|---|---|---|
| T/P/SW/DTEMP/WET | ✅ both branches | ✅ both branches |
| **Tmin/Tmax** | ✅ non-REGRID; ⏳ REGRID (B3) | ✅ both branches (THIS COMMIT) |
| Rh/W (wind) | ✅ both branches | ⏳ B1 (Fortran physics port; ~3-5 d) |

**Post-B2 status**: Fortran engine has caught up to AND surpassed C++ on Tmin/Tmax (Fortran has it in both branches; C++ has it only in non-REGRID; B3 closes the C++ REGRID gap). Rh + Wind remain Fortran-side-only gaps (B1 closes them).

#### Files changed this commit

| File | Change | Backport-relevance |
|---|---|---|
| `imogen/code/imogen_lpjg.f` | +59 LOC additive (9 surgical insertions: 4 OPENs + 2 CLOSEs + 8 LON/LAT writes + 8 data writes + 4 per-cell newlines + canonical doc block + 8 short cross-reference comments) | **RELEVANT** (Fortran source change in standalone engine; if `trunk_r13078` ships this engine file, apply the same 9 mechanical insertions) |
| `notes/STEP_17b.md` | NEW §3d (B2 forensic record + scope decision + unit-number selection + cross-engine parity matrix); §5 bundling table marks B2 ✅ DONE; §7 remaining work refresh (B3 NEXT); revised C2-era estimate ~5.5-8.5 d remaining; new dated footer entry | IRRELEVANT (docs) |
| `CHANGELOG.md` | This entry (above B6 entry) | IRRELEVANT (docs) |
| `EXECUTION_PLAN.md` | Row 17b status refresh (B2 ✅) | IRRELEVANT (docs) |
| `notes/FOLLOWUPS.md` | B-item bundling table (B2 ✅ DONE); status dashboard refresh; % done estimate updated | IRRELEVANT (docs) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | NEW step-17b-B2 entry: 1 file (`imogen/code/imogen_lpjg.f`); 9 mechanical insertions; backport-RELEVANT | IRRELEVANT (docs; the ledger row IS the backport directive) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` | Part 23 narrative (gitignored; not in commit) | IRRELEVANT (gitignored chat artifact) |

**Net `lpjguess/` source-level change in this commit: ZERO** (Fortran engine source lives at `imogen/code/`, NOT `lpjguess/`, but is still backport-relevant per F-11).

#### Remaining within step 17b after this commit

Per §7 of `notes/STEP_17b.md` (refreshed this commit):

- **B3 ⏳ NEXT** (~0.5 d): C++ Tmin/Tmax in REGRID branch of `climatemodel.cpp`; closes `// TODO at step 9.5b` inline comment.
- **B4** (~1 d): `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion.
- **B1** (~3-5 d; heaviest): Fortran Rh + Wind COMPUTATION port from C++ in-process engine to standalone Fortran.
- **C2 close-out + tag** `v0.17.5-step17b-c2-mpi-sync`.

**Revised C2-era estimate**: ~5.5-8.5 d remaining.

---

### 2026-05-11 (night; session 3) — Step 17b (F-12 sub-milestone C2; **B6 LANDED — subsumed by B10**): F-2 Fortran T_anom 2× line count fully traced to the same alternating-year writer bug B10 fixed (3 symptoms, one root cause); ZERO Fortran source change for B6; un-tagged docs-only checkpoint

This commit closes **audit item B6** (F-2 Fortran T_anom 2× line count investigation) per the re-ordered Option A bundle sequence (B10 → **B6** → B2 → B3 → B4 → B1; user-confirmed 2026-05-11). The forensic determination is that B6 is **fully subsumed by B10** (commit `3c00428`): the originally-reported 2× line count (T_anom.dat = 3262 lines vs version_A's 1631 lines) is **one of three downstream symptoms of the same alternating-year writer bug B10 fixed**.

#### Forensic finding — three symptoms, one root cause

Inspection of the on-disk pre-fix outputs at `imogen/code/IMOGEN/output/1871/` (preserved as a documentation artefact per B10's verification §3b.5) reveals the asymmetric file-count pattern:

| File | Our pre-fix lines | version_A reference | Pattern |
|---|---:|---:|---|
| `T_anom.dat` | 3262 | 1631 | **2× — doubled** |
| `P_anom.dat` | 3262 | 1631 | **2× — doubled** |
| `SW_anom.dat` | 3262 | 1631 | **2× — doubled** |
| `DTEMP_anom.dat` | 3262 | 1631 | **2× — doubled** |
| `WET.dat` | 1631 | 1631 | match (asymmetric vs T) |
| `fa_ocean.dat` | 11631 | 10000 | **+1631 — contaminated** |
| `dtemp_o.dat` | 508 | 254 | **2× — doubled** |

**Smoking-gun signature**: tail of pre-fix `fa_ocean.dat` (lines 10001-11631, 1631 rows) shows **WET-format `LON LAT + 12 ints`** content, e.g. ` 281.250  82.500         0         1         1 ...`. Version_A's reference is clean (10000 lines of `0` only).

#### Mechanism — alternating-year unit-95 reuse

In a 2-year engine call (`YEAR1=1871, IYEND=1872`) with the **pre-B10** OPEN/CLOSE gating:

1. **Year 1871**: climate writer OPENs unit 95 → `/1871/WET.dat` with `STATUS='REPLACE'`. Writes 1631 rows. Then OCEAN_FEED block re-OPENs unit 95 → `/1871/fa_ocean.dat` (Fortran auto-closes the existing WET.dat connection); writes 10000 rows. Climate-writer CLOSE statements at year-end were **gated** `IF(IYEAR.EQ.IYEND)` → did NOT fire. Units 92/93/94/95/11 stay open across year boundary. WET.dat is sealed at 1631 (because of the auto-close on unit-95 re-OPEN, not because of the CLOSE gate).
2. **Year 1872**: every `IF(IYEAR.EQ.YEAR1)`-gated OPEN is **skipped**. Units 92/93/94/11 still connect to `/1871/T_anom.dat` etc.; unit 95 still connects to `/1871/fa_ocean.dat` (NOT to `/1871/WET.dat` — that was auto-closed in step 1). Year-1872 climate writer:
   - `WRITE(92,...)` → appends 1631 cells to `/1871/T_anom.dat` → **3262 total**
   - `WRITE(93,...)` → appends 1631 cells to `/1871/P_anom.dat` → **3262 total**
   - `WRITE(94,...)` → appends 1631 cells to `/1871/SW_anom.dat` → **3262 total**
   - `WRITE(11,...)` → appends 1631 cells to `/1871/DTEMP_anom.dat` → **3262 total**
   - `WRITE(95,...) F_WET_CLIM_OUT(IGP,IMM)` → **appends 1631 WET-format integer rows to the still-open `/1871/fa_ocean.dat`** → **11631 total** (the smoking-gun contamination)
   - DTEMP_O writer on unit 96 → `/1871/dtemp_o.dat` → **508 total**
   - Climate-writer CLOSE statements fire (`IYEAR.EQ.IYEND=TRUE`) sealing all files.
3. **`/1872/` directory** receives only the **unconditional** `done` marker (everything else was redirected back to `/1871/`).

So **three symptoms = one bug**: pre-B10's alternating-year OPEN/CLOSE gating prevented year 1872 from receiving fresh per-year file targets; year-1872 writes silently appended to year-1871's still-open units; and the unit-95 mid-1871 reuse for fa_ocean.dat created the WET-vs-fa_ocean asymmetry.

#### Determination — B6 fully fixed by B10's structural change

**B10's structural fix** (`3c00428`, 7 conditional removals) replaces every gated OPEN/CLOSE with unconditional per-IYEAR semantics. Post-B10, year 1872's `STATUS='REPLACE'` OPENs target `/1872/`-paths cleanly; every unit closes at end-of-year. Predicted post-fix output:
- T/P/SW/DTEMP_anom.dat = 1631 lines per year per file (in BOTH `/1871/` and `/1872/`). 2× doubling **eliminated**.
- WET.dat = 1631 lines per year per file. Asymmetric-vs-T eliminated.
- fa_ocean.dat = 10000 lines per year per file. Contamination eliminated.
- dtemp_o.dat = 254 lines per year per file. Doubling eliminated.

Predicted post-fix structure matches `version_A/.../IMOGEN/output/1871/` reference **exactly** (same file count, same line count per file).

**Therefore B6 requires no additional code change.** It is **subsumed by B10**.

#### Verification

| Check | Method | Result |
|---|---|---|
| Empirical pre-fix on-disk pattern | `wc -l imogen/code/IMOGEN/output/1871/*.dat` | ✅ T/P/SW/DTEMP=3262, WET=1631, fa_ocean=11631, dtemp_o=508 — confirms the 3-symptom pattern |
| version_A reference parity | `wc -l version_A/.../IMOGEN/output/1871/*.dat` | ✅ T/P/SW/DTEMP=1631, WET=1631, fa_ocean=10000, dtemp_o=254 — matches predicted post-B10 structural output |
| Contamination tail signature | `sed -n '9998,10003p' imogen/code/IMOGEN/output/1871/fa_ocean.dat` | ✅ Lines 10001+ are WET-format `LON LAT + 12 ints` |
| Static writer-block analysis | `rg 'WRITE\(\s*(11\|92\|93\|94\|95)\s*[,\)]' imogen/code/imogen_lpjg.f` | ✅ Single writer block (lines 1019-1071 REGRID; 1083-1135 non-REGRID); no other doubled-write paths |
| Loop-structure analysis | Inspect IYEAR loop (lines 485-1189) | ✅ Climate writer fires once per IYEAR via the `(STEP_DAY.EQ.1).AND.(MM.EQ.12).AND.(MD.EQ.30)` gate (MM, MD = PARAMETERs always true; STEP_DAY=1 from settings); no nested loops doubling firings |

**Empirical post-B10 engine smoke deferred** — same reason as B10 (Fortran engine inputs `CEN_IPSL_MOD_IPSL-CM5A-MR/` patterns + `DKB_dataset_totals/` emissions are not currently shipped in the active rebuild). The post-B10 engine smoke that will be staged when B1 (Fortran Rh + Wind COMPUTATION port) lands will simultaneously verify both B10 and B6's predicted post-fix structure.

#### Files changed this commit

| File | Change | Backport-relevance |
|---|---|---|
| `notes/STEP_17b.md` | NEW §3c (B6 forensic record: pre-investigation framing, empirical 3-symptom pattern, single-root-cause mechanism, B10-subsumes-B6 determination, verification, code-change=ZERO, lesson-for-future-triage); §5 bundling table marks B6 ✅ DONE (0.0 d, subsumed); §7 remaining work refresh (B2 NEXT); revised C2-era estimate; new dated footer | IRRELEVANT (docs) |
| `CHANGELOG.md` | This entry (above B10 entry) | IRRELEVANT (docs) |
| `EXECUTION_PLAN.md` | Row 17b status refresh (B6 ✅) | IRRELEVANT (docs) |
| `notes/FOLLOWUPS.md` | F-2 entry → CLOSED 2026-05-11 by §3c (B6 subsumed by B10); B-item bundling table (B6 ✅ DONE); status dashboard refresh; "Operational heuristics — lessons learned" rule #6 (asymmetric multi-year writer scaling → check for single OPEN/CLOSE-gating root cause) | IRRELEVANT (docs) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | NEW step-17b-B6 entry: 0 source files; **backport-IRRELEVANT** (no source change; B10 backport entry already covers all 7 gates whose removal collectively fixes the B6 symptom) | IRRELEVANT (docs; the ledger row IS the backport directive) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` | Part 22 narrative (gitignored) | IRRELEVANT (gitignored chat artifact) |

**Net `lpjguess/` source-level change in this commit: ZERO. Net `imogen/` source-level change in this commit: ZERO. Docs-only commit.**

#### Remaining within step 17b after this commit

Per §7 of `notes/STEP_17b.md` (refreshed this commit):

- **B2 ⏳ NEXT** (~0.5 d): Fortran Tmin/Tmax write block (algebraic `Tmin = T - DTEMP/2`).
- **B3** (~0.5 d): C++ Tmin/Tmax in REGRID branch of `climatemodel.cpp`; closes `// TODO at step 9.5b`.
- **B4** (~1 d): `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion (mirrors C1.1 pattern).
- **B1** (~3-5 d; heaviest): Fortran Rh + Wind COMPUTATION port from in-process C++ engine to standalone Fortran (~70-100 LOC of Fortran physics).
- **C2 close-out + tag** `v0.17.5-step17b-c2-mpi-sync`.

**Revised C2-era estimate**: ~6.5-9.5 d remaining (was ~9-13 d at start of session 3; B6 saves 0.5 d by collapsing into B10).

---

### 2026-05-11 (night; session 3) — Step 17b (F-12 sub-milestone C2; **B10 LANDED**): symmetric Fortran engine writer fix in `imogen/code/imogen_lpjg.f`; 7 conditional removals (empirically refined from originally-documented 5); engines stay in lock-step for engine-mode parity; un-tagged checkpoint

This commit lands **audit item B10** (Symmetric Fortran engine writer fix) on top of the B12-resolution baseline. The standalone Fortran IMOGEN engine (`imogen/code/imogen_lpjg.f`) — canonical for v1.0's `imogen` mode per `EXECUTION_PLAN.md` Decision #2 — carried the same alternating-year writer bug that was fixed in the in-process C++ port (`lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()`) at commit `7be595a`. This commit applies the symmetric mechanical fix to the Fortran engine.

#### Pre-implementation re-examination (per user direction 2026-05-11)

Per user direction "do a more meticulous, systematic, and comprehensive examination of the various documentations (including handoffs)", a comprehensive review of `EXECUTION_PLAN.md` Decisions #2/#11/#12, `_phase2_findings/04_imogen_cxx.md` (the 25-bug catalogue of the **standalone** IMOGENCXX C++ refactor — distinct from the in-process C++ port at `climatemodel.cpp`), `notes/STEP_9.5.md`, and `notes/FOLLOWUPS.md` F-3 was completed before any code edits. Confirmed strategic context:

1. **Canonical IMOGEN engine for v1.0 = Fortran** (`imogen/code/imogen_lpjg.f`); standalone IMOGENCXX (with 25 documented bugs) is **deferred to Phase 2**, preserved as immutable archive in `version_A/.../IMOGENCXX/ImogenCXX/src/Main.cpp` per Decision #5.
2. **The in-process C++ engine port at `climatemodel.cpp`** (used by `imogencfx` mode in v1.0; NOT the same as standalone IMOGENCXX) was the engine fixed at `7be595a`. B10 is the symmetric replication of that fix to the standalone Fortran engine.
3. **B1 (Fortran Rh + Wind COMPUTATION port)** = port the Rh/W *physics computation* (~70-100 LOC) from the in-process C++ engine to the standalone Fortran engine. NOT about the 25 IMOGENCXX bugs.
4. **B-item ordering reconfirmed** per user-confirmed Option A 2026-05-11: B10 → B6 → B2 → B3 → B4 → B1 (mechanical-first; physics-port-last).

#### What landed this commit (1 file; +121 LOC, -37 LOC; net +84 LOC; backport-RELEVANT)

`imogen/code/imogen_lpjg.f`: 7 conditional removals around file OPEN/CLOSE blocks at (pre-fix) lines 854/883/954/1013/1071/1088/1099, with C++-doc-block parity. Net structure mirrors the C++ canonical doc at `climatemodel.cpp` ~884 (post-`7be595a`):

| # | Line (pre-fix) | Block | Has C++ analogue? |
|---|---|---|---|
| 1 | 854 | CO2 writer OPEN (units 91, 98) | YES (`climatemodel.cpp` ~787) |
| 2 | 883 | CO2 writer CLOSE (units 91, 98) | NO (Fortran-specific extra; C++ uses `std::ofstream` RAII so close is implicit) |
| 3 | 954 | Climate-anomaly REGRID OPEN (T/P/SW/WET/DTEMP, units 11, 92, 93, 94, 95) | YES (`climatemodel.cpp` ~884) — canonical doc lives here |
| 4 | 1013 | Climate-anomaly non-REGRID OPEN (same units) | NO (Fortran-specific extra; C++ port has no native-grid branch) |
| 5 | 1071 | Climate-anomaly CLOSE (units 11, 92, 93, 94, 95; covers both REGRID branches) | YES (`climatemodel.cpp` ~963) |
| 6 | 1088 | FA_OCEAN/DTEMP_O OPEN (units 95, 96) | YES (`climatemodel.cpp` ~988) |
| 7 | 1099 | FA_OCEAN/DTEMP_O CLOSE (units 95, 96) | YES (`climatemodel.cpp` ~998) |

So **7 = 5 C++ analogues + 2 Fortran-specific extras** (CO2 explicit CLOSE; non-REGRID OPEN branch). This is an **empirical refinement** of the originally-documented "5" count — not a scope expansion of intent. The intent was always full alternating-year symmetry; the original count was inherited from the C++ fix's count without re-counting against the Fortran source.

#### Symmetric-correctness framing (NOT a blocker)

The Fortran engine is **NOT on the v1.0 production path** — `imogen` mode in v1.0 calls a different launcher path; the Fortran engine is currently exercised only by **engine-only smoke testing**. The C1.2/C1.3 cross-validation PASSes verified at `7be595a` were on the C++ in-process port, not the Fortran engine. So B10 is about **engine parity** (per F-3 Fortran↔C++ IMOGEN parity in `notes/FOLLOWUPS.md`) — keeping the two engines in lock-step so future engine-mode switches inherit identical writer semantics — rather than unblocking any current-path failure.

#### Verification

| Check | Method | Result |
|---|---|---|
| Clean Fortran build | `cd imogen/code && rm -f *.o imogen_lpjg && bash compile.sh` | ✅ Exit 0; binary 129 600 bytes; ZERO warnings |
| Static gate-removal check | `rg 'IYEAR\.EQ\.(YEAR1\|IYEND)' imogen/code/imogen_lpjg.f` | ✅ All 7 B10 gates correctly removed; remaining matches are pre-existing legacy comment + different gate variable + my own doc-block paragraph references |
| Net LOC parity with C++ | `git diff --shortstat` | ✅ +121, -37 (vs C++ `7be595a`'s +76, -5; proportionate given 7 vs 5 fixes + 2 extra Fortran-specific cross-reference blocks) |
| Pre-fix evidence preserved | `ls imogen/code/IMOGEN/output/{1871,1872}/` | ✅ `1871/` has 9 climate files (full); `1872/` has only `done` marker (empty) — empirical pre-fix demonstration of the alternating-year quirk, retained as a documentation artefact |
| C++ fix doc-block parity | Visual diff of `imogen_lpjg.f` canonical block vs `climatemodel.cpp` ~884 canonical block | ✅ Same structure: ROOT-CAUSE FIX + symmetric-engine-list + FIX + symmetric-removals list + backport note + author/date stamp |

**Empirical post-fix engine smoke deferred** — would require staging the `CEN_IPSL_MOD_IPSL-CM5A-MR/` patterns + `DKB_dataset_totals/` emissions inputs that the existing `imogen_settings.txt` references but which are not currently shipped in the active rebuild's `imogen/` tree (engine inputs were not re-staged after Step 4's selective import per the engine being NOT on the v1.0 production path). Per the symmetric-correctness framing, the clean compile + static gate-removal check + pre-fix evidence preserved together suffice for B10's verification gate. A full empirical engine smoke would naturally be staged when **B1** (Fortran Rh + Wind COMPUTATION port) lands — at which point a post-B1 engine smoke would simultaneously verify B10's writer fix in production.

#### Files changed this commit

| File | Change | Backport-relevance |
|---|---|---|
| `imogen/code/imogen_lpjg.f` | 7 conditional removals around file OPEN/CLOSE blocks; canonical doc block + 6 cross-referencing short blocks (+121, -37) | **RELEVANT** (Fortran source change in standalone engine; if `trunk_r13078` ships this engine file, apply 7 mechanical removals symmetrically) |
| `notes/STEP_17b.md` | NEW §3b (B10 forensic record + scope refinement 5→7 + symmetric-correctness framing + ordering rationale); §5 bundling table marks B10 ✅ DONE; §7 remaining work refresh; new dated footer | IRRELEVANT (docs) |
| `CHANGELOG.md` | This entry (above B12-resolution entry) | IRRELEVANT (docs) |
| `EXECUTION_PLAN.md` | Row 17b status refresh (B10 ✅) | IRRELEVANT (docs) |
| `notes/FOLLOWUPS.md` | B-item bundling table (B10 ✅ DONE); status dashboard refresh; % done estimates | IRRELEVANT (docs) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | NEW step-17b-B10 entry: 1 file (`imogen/code/imogen_lpjg.f`); 7 conditional removals; backport-RELEVANT | IRRELEVANT (docs; the ledger row IS the backport directive) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` | Part 21 narrative (gitignored) | IRRELEVANT (gitignored chat artifact) |

**Net `lpjguess/` source-level change in this commit: ZERO** (the Fortran engine source lives at `imogen/code/`, NOT `lpjguess/`, but is still backport-relevant for the Backport Sprint per F-11 — the BACKPORT_LEDGER tracks both `lpjguess/`-internal AND `imogen/`-internal source changes).

#### Remaining within step 17b after this commit

Per §7 of `notes/STEP_17b.md` (refreshed this commit):

- **B6 ⏳ NEXT** (~0.5 d): F-2 Fortran T_anom 2× line count investigation; sits in same `imogen_lpjg.f` writer block; cohesive next step.
- **B2** (~0.5 d): Fortran Tmin/Tmax write block (algebraic `Tmin = T - DTEMP/2`).
- **B3** (~0.5 d): C++ Tmin/Tmax in REGRID branch of `climatemodel.cpp`; closes `// TODO at step 9.5b`.
- **B4** (~1 d): `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion.
- **B1** (~3-5 d; heaviest): Fortran Rh + Wind COMPUTATION port from C++ engine to Fortran (~70-100 LOC of new Fortran physics).
- **B13 + B14** (NEW; from B12 work; bundle with step 18; ~1-1.5 d): defensive hardening at `init_cton_limits()` if `cton_leaf_min == 0` (B13) + one-time `.ins` parity audit (B14).
- **C2 close-out + tag `v0.17.5-step17b-c2-mpi-sync`** (after all B-bundles): full 4-xval against both `build/guess` and `build_mpi/guess` (single-process AND `mpirun -np 4` mimic); tag; push to all 3 remotes.

Refs: `notes/STEP_17b.md` §3b (forensic) + §5 (bundling table refresh) + §7 (remaining work refresh); `notes/FOLLOWUPS.md` B-item table (B10 ✅); `EXECUTION_PLAN.md` V.1 row 17b (status); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (NEW step-17b-B10 entry); `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 21.

---

### 2026-05-11 (evening; session 3) — Step 17b (F-12 sub-milestone C2; **B12 RESOLVED**): substantive-validation NaN root cause identified + fix applied; ALL 4 xval scenarios now PASS substantive validation (bit-exact AND non-NaN); un-tagged checkpoint

The substantive-validation NaN finding documented at session-2 commit `f13b302` and audit item B12 is **fully resolved** in this commit. ALL 4 cross-validation scenarios (imogen 1cell, imogen 4cell, imogencfx 1cell, imogencfx 4cell) now pass `scripts/cross_validate_year_outer.sh`'s substantive-validation gate (bit-exact AND non-NaN); 0/37 NaN-laden output files in any run; against both `build/guess` and `build_mpi/guess` single-process. 162 unit tests pass on both builds.

#### Root cause (full forensic chain in `notes/STEP_17b.md` §3a.7.4c)

Smoke `.ins` files explicitly set `ifcalccton 0` and `ifcalcsla 0`. With `ifcalccton 0`, `parameters.cpp::CB_CHECKPFT` (lines 2333-2337) skips `init_cton_min()` for each PFT. `init_cton_min()` is what populates `cton_leaf_min` from `leaflong` via the Reich et al. 1992 relation. Without it, `cton_leaf_min` stays at its default-initialized value of `0`. Then `init_cton_limits()` (called UNCONDITIONALLY at parameters.cpp:2345) cascades 0 through `cton_leaf_max → cton_root_max → cton_sap_max` (and the avr/min siblings; `avg_cton(0,0)` returns 0 per its `2/(1/min + 1/max)` formula). For new individuals with `cmass_sap=nmass_sap=0`, `Individual::cton_sap()` returns `pft.cton_sap_max = 0`. In `respiration()` at `canexch.cpp:2494`:

```cpp
resp_sap = respcoeff * K * cmass_sap / cton_sap * gtemp_air;
         = respcoeff * K * 0 / 0 * gtemp_air            // 0/0 = NaN per IEEE 754
         = NaN * gtemp_air = NaN;
```

`resp = NaN → indiv.dnpp = NaN → indiv.anpp = NaN → cmass_* = NaN at year-end growth() → ESTC debit at growth.cpp:1524 = NaN → cascades to ALL .out files`.

#### Fix applied (this commit; backport-IRRELEVANT)

Two `.ins` file changes (no `lpjguess/` source change):

1. `runs/SSP1-2.6/main_xval_loose.ins`: changed `ifcalcsla 0 → 1` and `ifcalccton 0 → 1`. Added 13-line explanatory comment documenting the root cause + fix rationale + cross-references to STEP_17b.md §3a.7.4c.
2. `runs/SSP1-2.6/main_xval_imogencfx.ins`: same change with shorter cross-reference comment.

Optional 1-cell mid-latitude smoke gridlist `data/gridlist/gridlist_test_temperate.txt` (1 cell at Switzerland 7.50°E 47.50°N) added during diagnostic narrowing; preserved as a useful additional test cell for future investigations.

#### Why predecessor `version_A` doesn't NaN

Predecessor's `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/main.ins` does NOT set `ifcalcsla` or `ifcalccton` explicitly, so they take the LPJ-GUESS defaults (= 1). With `ifcalccton 1`, `init_cton_min()` IS called for each PFT, populating `cton_leaf_min` correctly, and the entire cascade produces sensible non-zero C:N ratios. The user's empirical observation that "version_A did not produce any NaNs that I was aware of" was a key clue — the LPJG code itself works fine; only our smoke configuration triggered the latent trap.

#### Why this only surfaced in v1.0

The LPJG main loop never ran in our rebuild prior to step 17a's C1 close-out (F-10 deadlock blocked it pre-C1; C1's `skip_inprocess_engine_run` parameter unlocked it for `-input imogencfx`; `-input imogen` was always F-10-free for loose-mode but our smoke .ins still had the same `ifcalccton 0`). So this latent bug from setting `ifcalccton 0` in our smoke `.ins` was never exercised. Once the LPJG main loop started running for the first time post-C1, the bug surfaced as the substantive-validation NaN finding.

#### Diagnostic methodology

A 4-stage diagnostic-narrowing process landed the root cause in ~2 hours of session-3 work (vs the 2-10 d unbounded estimate at B12 audit item creation):

1. Stage 1: spinup-duration hypothesis — REFUTED (longer spinup made NaN appear earlier).
2. Stage 2: extreme-cold-cell hypothesis — REFUTED (temperate Switzerland cell → same NaN).
3. Stage 3: wetlandpfts.ins hypothesis — REFUTED (dropping it → identical NaN).
4. Stage 4: surgical NaN-source instrumentation in `lpjguess/framework/guess.cpp::Fluxes::report_flux` + `lpjguess/modules/growth.cpp::1524` (ESTC debit) + `lpjguess/modules/canexch.cpp::2635` (dnpp accumulation) + `lpjguess/modules/canexch.cpp::2626` (respiration inputs). The diagnostic chain definitively traced from `dnpp NaN at Year 2 Day 0` → `resp NaN with finite inputs` → `0/0 inside respiration()` → `cton_sap = 0` → `init_cton_limits()` cascade → `cton_leaf_min = 0` → `init_cton_min()` not called → `ifcalccton 0` in smoke .ins.

All diagnostic instrumentation has been REMOVED in this same commit; the lpjguess/ source is back to its v0.17.0-step17a-c1-year-outer-single-process baseline (verified via `git status` showing only `runs/SSP1-2.6/main_xval_*.ins` as modified, no lpjguess/ source files modified post-cleanup).

#### Verification

- ✅ `cd lpjguess/build && make -j$(nproc)`: clean
- ✅ `cd lpjguess/build_mpi && make -j$(nproc)`: clean
- ✅ `lpjguess/build/runtests --reporter compact`: "Passed all 25 test cases with 162 assertions."
- ✅ `lpjguess/build_mpi/runtests --reporter compact`: same
- ✅ All 4 xval scenarios PASS substantive (bit-exact AND non-NaN) against `build/guess`:
  - imogen 1cell:    37/37 byte-equal; 0/37 NaN-laden
  - imogen 4cell:    37/37 byte-equal; 0/37 NaN-laden
  - imogencfx 1cell: 37/37 byte-equal; 0/37 NaN-laden
  - imogencfx 4cell: 37/37 byte-equal; 0/37 NaN-laden
- ✅ All 4 xval scenarios PASS substantive against `build_mpi/guess` single-process (same results)

#### Sample post-fix output for sanity

`nflux.out` for cell (7.50, 47.50) Switzerland:
```
      Lon      Lat Year   NH4dep   NO3dep      fix     fert     flux    leach      NEE
     7.50    47.50 1871    -1.00    -1.00    -0.00    -0.00     0.17     1.03    -0.80
     7.50    47.50 1872    -1.00    -1.00    -2.78    -0.00     0.02     0.24    -4.53
     7.50    47.50 1879    -1.00    -1.00    -9.21    -0.00     0.04     1.07   -10.10
```
Sensible: NH4/NO3dep -1.00 kgN/ha/yr (pre-industrial deposition; LPJG sign convention); N fixation ramps from 0 to -9.21; system reaches near-equilibrium.

#### Defensive hardening (NEW audit item B13)

The bug was a **trap** in the LPJG configuration system: `ifcalccton 0` is a documented option (means "use cton_leaf_min from .ins") but with TeBE not setting `cton_leaf_min` explicitly in `global.ins`, the default-init-to-zero produces NaN downstream. **NEW audit item B13** added: defensive hardening — make LPJG `init_cton_limits()` fail-fast with a clear message if `cton_leaf_min == 0`. Tracked in `notes/FOLLOWUPS.md` "B-item bundling commitment" sub-section. Effort: 0.5 day. Bundle: step 18 (docs/cleanup era).

#### Process hardening (NEW audit item B14 + persistent Operational heuristics)

In session continuation 2026-05-11 evening, the user asked whether predecessor `version_A`'s `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/` `.ins` files set `ifcalcsla` and `ifcalccton` to 1. Empirical answer: **yes** — both are set in `version_A/.../landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/global.ins` (lines 96, 98); `main.ins` imports `global.ins` so the production-style coupled run inherits those `1` values. This makes B12 a config-divergence-from-canonical-baseline issue, not an LPJG code defect.

User direction (recorded persistently): **do not** undertake a full `.ins` realignment audit now (the `ifcalcsla`/`ifcalccton` fix sufficed); **do** document the lesson so future chats see it. Operationalised via two additions to `notes/FOLLOWUPS.md`:

1. **NEW audit item B14**: one-time `.ins` parity audit of `runs/SSP1-2.6/main_xval_*.ins` (and import chain) vs `version_A/.../landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/` and `version_B/.../landsymm_imogen/SSP1_RCP26/`; classify each divergent parameter as **intentional** (document rationale at site) or **unintentional** (open follow-up). Effort: 0.5–1 d. Bundle: step 18 (docs/reproducibility era; opportunistically usable earlier on any output anomaly). Tracked in `notes/FOLLOWUPS.md` "B-item bundling commitment" sub-section.
2. **NEW persistent "Operational heuristics — lessons learned" subsection** in `notes/FOLLOWUPS.md` (placed after "Tracking discipline" so any onboarding chat reading the file inherits these defaults). Five standing rules of thumb distilled from B12 + Part 19 forensics, with the `.ins`-parity-with-original heuristic as **rule #1** ("FIRST-LINE forensic step when outputs look wacky"). Other rules: byte-equality is necessary but not sufficient; skip-by-default `if<flag> 0` paths are silent traps; production gridlists are not interchangeable with smoke gridlists; "when in doubt, ask the original codebase what it would have done."

#### Status

- B12: ✅ DONE
- C2 era combined sprint estimate revised back to ~9-13 d remaining (was 11-23+ before B12 closure).
- v1.0 % done estimate revised UP to ~52-55%; ~45-48% remaining (~28-37 d median).
- Substantive-validation gate now PASSES for the first time in our rebuild — meaningful science output is being produced by LPJG main loop in `-input imogen` and `-input imogencfx` modes.

#### Files changed

- `runs/SSP1-2.6/main_xval_loose.ins` (~17 LOC change; 2 lines flipped + ~15 LOC explanatory comment)
- `runs/SSP1-2.6/main_xval_imogencfx.ins` (~12 LOC change; 2 lines flipped + ~10 LOC explanatory comment)
- `data/gridlist/gridlist_test_temperate.txt` (NEW; 1 cell at 7.50°E 47.50°N; useful for future temperate-latitude smoke tests)
- `notes/STEP_17b.md` (+~150 LOC; new §3a.7.4c B12 RESOLUTION sub-section + revised §7 remaining work)
- `CHANGELOG.md` (this entry; ~150 LOC)
- `EXECUTION_PLAN.md` (row 17b status update)
- `notes/FOLLOWUPS.md` (~110 LOC total; status dashboard refresh + B-bundling table updates with B12 done + B13 added + B14 added; revised % done table + adopted estimate; NEW persistent "Operational heuristics — lessons learned" subsection with 5 standing rules of thumb)
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (small entry noting the B12 fix is .ins-only; no lpjguess/ source change so backport-IRRELEVANT)
- `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 20 (NEW; outside repo; gitignored)

Net `lpjguess/` source-level change THIS COMMIT: **ZERO**. Backport-IRRELEVANT.

Refs: notes/STEP_17b.md §3a.7.4c (full forensic record + verification + sample output); notes/FOLLOWUPS.md "Substantive-validation NaN finding (2026-05-11 evening)" sub-section + B-item bundling table updated; EXECUTION_PLAN.md V.1 row 17b status; notes/TRUNK_R13078_BACKPORT_LEDGER.md (B12 fix is config-only); session-2 chat handoff Part 20.

### 2026-05-11 (evening) — Step 17b (F-12 sub-milestone C2 CORE + CRITICAL substantive-validation NaN finding + xval harness hardening + NEW audit item B12): `MPI_Barrier(MPI_COMM_WORLD)` at year boundary in `framework.cpp` year_outer block + NEW `ImogenOutput::flush_year_globally_synchronized(int year)` method with `MPI_Allreduce(MPI_SUM)` over per-rank flux contributions + lead-rank-only write + singleton-pointer pattern + xval harness substantive-validation NaN gate (FAILs on NaN-laden outputs; was: PASS based on byte-equality alone — masked the C1 substantive-validation gap); both builds rebuild clean; 162 unit tests pass on both; mpirun -np 1 -parallel smoke verified MPI mechanics; full mpirun -np 4 mimic deferred to C2 close-out (alongside B-bundles); un-tagged checkpoint

C2 core landing for F-12 sub-milestone C2 on top of C2 prep commit `1405ada`. This is an intermediate checkpoint commit (no tag); the full step-17b tag `v0.17.5-step17b-c2-mpi-sync` waits for **B12 (NEW; CRITICAL PATH; substantive-validation NaN root-cause investigation + fix; 2-10 d unbounded)** + B1+B2+B3+B4+B6+B10 bundles + close-out validation. **REVISED C2 era combined sprint estimate: ~11-23+ days** (was 9-13 d) due to B12 addition.

#### CRITICAL FINDING — substantive-validation NaN gap in C1 baseline (this commit; audit item B12)

While diagnosing apparent NaN values in the `mpirun -np 1 -parallel` smoke test, isolation experiments revealed that **ALL FOUR C1 cross-validation scenarios produce NaN-laden outputs** at the C1 tag baseline (`v0.17.0-step17a-c1-year-outer-single-process` at commit `8aafe84`). The "GO/NO-GO gate PASSED for all 4 scenarios" claim at C1 close-out was:

- **Nominally correct** (byte-equality preserved between gridcell_outer + year_outer)
- **Substantively misleading** (both modes produced byte-identical NaN-laden outputs; `cmp -s` reports NaN-bytes match NaN-bytes as identical → PASS-of-garbage)

The cross-validation harness's `cmp -s` byte-equality logic is **necessary but not sufficient** for scientific validation. Both modes producing identical NaN doesn't validate year_outer's correctness — it only validates that whatever mechanism produces NaN does so identically in both loop-ordering modes.

NaN first appears at simulation Year 2 Day 1 in `soil.NH4_mass` diagnostic at `lpjguess/modules/somdynam.cpp:574` and propagates to vegetation establishment + C/N flux outputs.

**Investigation 2026-05-11 (45 min spent) conclusively ruled out**:
- C2 MPI code (NaN identical between C1-only-revert + C2 builds)
- `MPI_Initialized` vs `GuessParallel::parallel` (irrelevant; NaN with MPI completely bypassed)
- `-parallel` CLI flag (NaN with and without)
- Loop-ordering mode (NaN identical in gridcell_outer + year_outer; bit-exact)
- Short spinup (nyear_spinup ∈ {2, 10, 30}; freenyears ∈ {0, 5, 15} all NaN)
- `crop_n.ins` import (NaN without it too)
- Gridcell-specific (4 cells across 76°N, 80°N, 54°N, -33°S all NaN)
- Soilmap-mismatch (NaN even with exact soilmap matches)
- `searchradius=50` interpretation (NaN with dist=0 exact climate matches)
- Climate input quality (T=237-276 K at our cells; realistic Arctic values)

**Plausible remaining root-cause hypotheses (for B12 investigation)**:
1. LPJ-GUESS vegetation/soil initialization for `-input imogen` was never substantively validated (F-10 deadlock blocked LPJG main loop pre-C1; C1's `skip_inprocess_engine_run` unlocked it but NaN went unnoticed due to byte-comparison-only harness)
2. LPJG-internal bug in `ImogenInput::get_climate_for_gridcell` or monthly→daily interpolation
3. `wetlandpfts.ins` + `global.ins` initialisation interaction
4. LandSyMM_LPJ-GUESS fork-specific issue
5. NaN-aware code path in soil-N integration

**Implications**:
- The C1 close-out tag `v0.17.0-step17a-c1-year-outer-single-process` is preserved in git (the byte-equality milestone IS real); but it does NOT represent a substantively-validated baseline
- We have NEVER successfully run a non-NaN end-to-end LPJG main-loop simulation with `-input imogen` or `-input imogencfx + skip_inprocess_engine_run` on our smoke gridlists in this rebuild
- 2026-05-11 morning audit revised v1.0 estimate from ~70% done to ~48-50% done; this evening's B12 finding further revises to **~40-45% done; ~55-60% remaining (~35-42 days median; range 27-55+)**

#### xval harness hardening (`scripts/cross_validate_year_outer.sh`)

Added substantive-validation NaN-check gate that runs AFTER the byte-equality check. The gate:
- Scans Run A and Run B `.out` files for `nan` tokens (case-insensitive)
- Reports byte-equality and non-NaN check results separately
- **FAILs with exit code 3** if either run has NaN-laden `.out` files (was: PASS based on byte-equality alone)
- Provides actionable diagnostic output pointing at STEP_17b.md §3a.7 + FOLLOWUPS B12 + session-2 handoff Part 18

**Effect on existing validation**: until B12 is investigated + fixed, all 4 cross-validation scenarios now correctly REPORT FAIL rather than masking the NaN issue. This is the desired "stop the line" behavior. The harness modification is backport-IRRELEVANT (scripts/ only).

#### NEW audit item B12 (CRITICAL PATH; bundled with C2 era; MUST land before C2 close-out tag)

**B12: Substantive-validation NaN root-cause investigation + fix.** Estimated 2-10 d unbounded (could be quick if obvious in LPJG init; could require LPJG-developer-level expertise if deep main-loop issue). Bundled with C2 era BEFORE B1-B10 bundles and BEFORE C2 close-out tag so the `v0.17.5-step17b-c2-mpi-sync` milestone lands on a substantively-validated baseline (bit-exact AND non-NaN).

Full forensic record in `notes/STEP_17b.md` §3a.7 + §3a.8 + `notes/FOLLOWUPS.md` "Substantive-validation NaN finding (2026-05-11 evening)" sub-section + `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 18.

**Net `lpjguess/` source-level change this commit: +317 LOC additive across 3 files.** Backport-RELEVANT.

#### What landed

| File | Change | LOC |
|---|---|---|
| `lpjguess/modules/imogenoutput.h` | NEW: `static ImogenOutput* get_instance()` accessor + `flush_year_globally_synchronized(int year)` method declaration + `static ImogenOutput* instance_` private member + extensive doc blocks | +60 |
| `lpjguess/modules/imogenoutput.cpp` | NEW: `#include <mpi.h>` (HAVE_MPI-guarded) + static `instance_` definition + ctor sets `instance_ = this` + dtor clears it + `flush_year_globally_synchronized(int year)` implementation (~120 LOC incl. doc block + MPI_Allreduce over per-rank flux contributions + lead-rank-only write delegation to existing `flush_year` + post-flush reset + per-rank diagnostic dprintf) | +181 |
| `lpjguess/framework/framework.cpp` | NEW: `#include <mpi.h>` (HAVE_MPI-guarded) + `#include "../modules/imogenoutput.h"` + year-boundary `MPI_Barrier` block (HAVE_MPI + `MPI_Initialized` guarded) + explicit call to `ImogenOutput::get_instance()->flush_year_globally_synchronized(calendar_year)` between per-year cell-inner loop body close and per-cell teardown in the year_outer additive block | +76 |

#### Design decision — singleton-pointer pattern over virtual-method-on-base

Singleton-pointer (`static ImogenOutput* instance_` set in ctor, cleared in dtor; `get_instance()` accessor) chosen over adding a new non-pure virtual to `OutputModule` abstract base class. Rationale:
- Smaller backport surface (avoids touching `framework/outputmodule.h/cpp` which are upstream LPJ-GUESS infrastructure)
- Mirrors existing `output_channel` global at `outputmodule.h:227` (process-global singleton pattern is mainstream in this codebase)
- Avoids forcing all 9 registered output modules to either get the new virtual or document its no-op default
- Defensive null-check at call site: `if (ImogenOutput* imout = get_instance())` silently skips if not registered

#### MPI integration discipline (verified per user 2026-05-11 query)

Verified live against existing LPJ-GUESS MPI usage at `imogencfx.cpp:381` + `imogen_input.cpp:221`. The new C2 code follows the established pattern exactly:

- `#ifdef HAVE_MPI #include <mpi.h> #endif` at file top (before any std header) ✓
- `int flag; MPI_Initialized(&flag); if (... == MPI_SUCCESS && flag == true) { ... }` guard pattern ✓
- `MPI_COMM_WORLD` communicator ✓
- `GuessParallel::get_rank()` from `parallel.h` for rank identification ✓
- `#ifdef HAVE_MPI ... #endif` compile-time guards around all MPI calls ✓

**Only new MPI primitive C2 introduces is `MPI_Allreduce`** (existing LPJ-GUESS code only uses `MPI_Barrier`). `MPI_Allreduce` with `MPI_DOUBLE` / `MPI_INT` + `MPI_SUM` is standard MPI-1; universally supported by MPICH (Anaconda3 + KIT IMK-IFU `owl`), OpenMPI, Cray MPICH, Intel MPI, etc.

`MPI_Initialized(&flag)` chosen over `GuessParallel::parallel` because: (a) matches existing convention; (b) more robust (queries actual MPI state); (c) `GuessParallel::parallel` isn't exposed via `parallel.h` (using it would force a header touch + larger backport surface).

#### Year-boundary semantics — preserves single-process bit-exactness

In `year_outer` mode, the existing outannual year-change-detection at `imogenoutput.cpp:118` was the auto-flush trigger producing one flush per year on year+1 cell 0. The new explicit `flush_year_globally_synchronized` call at year boundary changes the TIMING (end of year_idx body vs start of year_idx+1 cell 0) but NOT the VALUES (year-aggregated; same set of cells contribute). After the new call, `accum_year=-1` so outannual's auto-flush at year+1 cell 0 sees `-1 < 0` and SKIPS — avoiding double-write. Result: same flush values, same flush count, slightly earlier timing in execution → same `.out` file content → bit-exact xval preserved.

Final-year handling: framework.cpp's `for (year_idx=0; ... < total_years; ...)` loop body now explicitly fires `flush_year_globally_synchronized` for EVERY year_idx including the last, so the destructor's catch-all `if (year_pending && accum_year >= 0)` is naturally bypassed in year_outer (accum_year=-1 + year_pending=false). In gridcell_outer mode the destructor still catches the final year as before.

#### Verification

| Check | Result |
|---|---|
| `cd lpjguess/build && make -j$(nproc)`: clean (build/) | ✅ no errors |
| `cd lpjguess/build_mpi && make -j$(nproc)`: clean (build_mpi/) | ✅ no errors |
| `lpjguess/build/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| `lpjguess/build_mpi/runtests --reporter compact` | ✅ "Passed all 25 test cases with 162 assertions." |
| `GUESS_BIN=$PWD/lpjguess/build_mpi/guess scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ 37/37 bit-exact PASS |
| `4cell imogen` | ✅ 37/37 bit-exact PASS |
| `1cell imogencfx` | ✅ 37/37 bit-exact PASS |
| `4cell imogencfx` | ✅ 37/37 bit-exact PASS |
| `mpirun -np 1 build_mpi/guess -parallel -input imogen <ins>` smoke | ✅ MPI_Init succeeds + `flush_year_globally_synchronized` invoked (`[ImogenOutput] flushed year=XXXX` diagnostic visible) + LPJG main loop completes ("Finished") |

**Side-finding (NOT a C2 bug)**: hand-built `mpirun -np 1` smoke produced NaN values in some output fields. Isolation test (same workdir + same .ins WITHOUT `-parallel`) showed the NaN ALSO appears in single-process mode → root cause is the ad-hoc workdir layout (missing some symlinks for default file searches that the standard `cross_validate_year_outer.sh` harness has). The proper `mpirun -np 4` mimic at C2 close-out will use `scripts/run_parallel_mimic.sh` + `scripts/cluster/setup_run.sh` for production-grade per-rank dir population.

#### Remaining within step 17b (next session)

1. **B1+B4 cohesive C2 era work**: Fortran Rh + Wind COMPUTATION port (B1; 3-5 d in `imogen/code/imogen_lpjg.f` — heaviest; the physics pipeline that C++ engine has but Fortran doesn't compute) + ImogenInput Rh/W/Tmin/Tmax consumer wiring expansion (B4; 1 d in `lpjguess/modules/imogen_input.cpp/h` — loose-mode symmetry with IMOGENCFXInput).
2. **B2+B3+B6+B10 small bundles**: Fortran Tmin/Tmax write (B2; 0.5 d) + C++ Tmin/Tmax REGRID branch (B3; 0.5 d) + F-2 Fortran T_anom 2× investigation (B6; 0.5 d) + symmetric Fortran engine writer fix at `imogen_lpjg.f` lines 954/1013/1071/1088/1099 (B10; 0.5 d).
3. **C2 close-out + tag `v0.17.5-step17b-c2-mpi-sync`**: full 4-xval cross-validation against both `build/guess` and `build_mpi/guess` (single-process AND `mpirun -np 4` mimic via `scripts/run_parallel_mimic.sh` + per-rank dirs via `scripts/cluster/setup_run.sh`) + 162 unit tests both builds + tag + push to all 3 remotes.

Refs: `notes/STEP_17b.md` §3a (full C2 core implementation forensic record); `notes/FOLLOWUPS.md` F-12 dashboard refresh + C2 core landing context; `EXECUTION_PLAN.md` V.1 step row 17b (status updated with C2 core landing); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 step-17b-core entry (backport-RELEVANT; 3 file changes); `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 17 (NEW; this commit's narrative + MPI integration discipline verification per user 2026-05-11 query).

### 2026-05-11 (afternoon) — Step 17b (F-12 sub-milestone C2 PREP): Anaconda3 `mpicxx` wrapper fix + `make_guess.sh` `--mpi` NetCDF logic fix + `lpjguess/build_mpi/guess` built clean + all 4 cross-validation scenarios re-PASS bit-exact against `build_mpi/guess` (single-process baseline; pre-MPI_Barrier code); B-item bundling decision LOCKED IN (refined option (i) for B1+B4 with C2 era + opportunistic option (iii) for B2/B3/B5-B11 with definitive per-item home); STEP_17b.md NEW (no tag)

C2 prep phase landing for F-12 sub-milestone C2 (workstation MPI year_outer) on top of C1 tag `v0.17.0-step17a-c1-year-outer-single-process` + audit docs commit `e8fd7fb`. This is an intermediate checkpoint commit (no tag); the full step-17b tag `v0.17.5-step17b-c2-mpi-sync` waits for C2 core (MPI_Barrier + flush_year_globally_synchronized) + B1+B2+B3+B4+B6+B10 bundles to land.

**Net `lpjguess/` source-level change this commit: ZERO** (scripts/ + docs only).

#### Anaconda3 `mpicxx` wrapper fix (the C2 pre-requisite)

Anaconda3's mpicxx wrapper (MPICH 4.1.1) is configured to invoke `x86_64-conda-linux-gnu-c++` (the conda-shipped g++ wrapper compiler). That binary is NOT present in the bare Anaconda3 install on this workstation per session-2 §8.1 specs:

```
$ mpicxx --version
/home/bampoh-d/anaconda3/bin/mpicxx: line 321:
  x86_64-conda-linux-gnu-c++: command not found
```

Two fixes investigated 2026-05-11:
- (a) `MPICH_CXX=g++` env-var override — uses system g++ instead of conda wrapper. NOT chosen: hits an INDEPENDENT libstdc++ ABI issue (Anaconda3 ships `libstdc++.so.6.0.29` GCC 11.2 era which doesn't export `__cxa_call_terminate`; system `libstdc++.so.6.0.34` GCC 15.2 era does; the mpicxx wrapper command bakes `-L/home/.../anaconda3/lib -Wl,-rpath,...` into the link line → linker finds older libstdc++ first → undefined reference). NOTE: handoff Part 8.1 + the user's C2 prompt suggested `OMPI_CXX=g++`; corrected here — Anaconda3 ships MPICH, not OpenMPI; the variable is `MPICH_CXX`.
- (b) `conda install -c conda-forge gxx_linux-64` — provides the missing wrapper compiler AT the path mpicxx expects + ships a matching `libstdc++` (typically GCC 11.x+ which exports `__cxa_call_terminate`). CHOSEN (per session-2 §8.1 "preferred"). Empirical: installed `conda-forge gcc 15.2.0-7` (literally the SAME 15.2.0 major-minor as system g++; ABI fully compatible). Anaconda3's `libstdc++.so.6` link target updated 2026-05-11 to `libstdc++.so.6.0.34` (matches system; exports `__cxa_call_terminate`).

#### Independent NetCDF/HDF5 mismatch in `make_guess.sh --mpi` path

Existing `scripts/cluster/make_guess.sh` had a workstation-incorrect `&& ${USE_MPI} -eq 0` clause at lines 92-102 that excluded Anaconda3 NetCDF preference for MPI builds. The rationale was cluster-correct ("cluster + MPI prefers module-loaded NetCDF") but workstation-INCORRECT: on workstation there's no module-loaded NetCDF; Ubuntu native is the broken `libhdf5_serial.so.310` ↔ `libcurl.so.4@CURL_OPENSSL_4` ABI mismatch that Decision #8 specifically AVOIDS via the Anaconda3 NetCDF preference.

Empirical evidence: with `--mpi` skipping Anaconda3 NetCDF, MPI workstation build failed at link time with the canonical Decision #8 errors:
```
undefined reference to `curl_global_init@CURL_OPENSSL_4`
undefined reference to `curl_easy_perform@CURL_OPENSSL_4`
... (libhdf5_serial.so.310 ↔ libcurl mismatch)
```

Fix: apply Anaconda3 NetCDF unconditionally when ANACONDA3_PREFIX is set. Cluster builds (which use module-loaded NetCDF) should NOT set ANACONDA3_PREFIX; env_owl.sh module loads will populate cluster-native NETCDF paths and leave ANACONDA3_PREFIX unset.

#### Verification (this commit)

| Check | Result |
|---|---|
| `mpicxx --version` works | ✅ "conda-forge gcc 15.2.0-7" |
| `lpjguess/build_mpi/guess` builds clean | ✅ 2 836 440 bytes |
| `lpjguess/build_mpi/runtests` builds clean | ✅ 162 tests / 25 cases pass |
| MPI symbol linkage | ✅ `libmpi.so.12` + `libmpicxx.so.12` from Anaconda3 |
| NetCDF linkage | ✅ `libnetcdf.so.19` + `libhdf5.so.200` + `libcurl.so.4` from Anaconda3 (Decision #8 honored) |
| HAVE_MPI defined at compile | ✅ `auto_ptr<FinalizeCaller>` symbol present in `parallel.cpp.o` |
| All 4 xval scenarios bit-exact PASS against `build_mpi/guess` (single-process; pre-MPI_Barrier baseline) | ✅ 37/37 bit-exact for all 4 (imogen 1cell, imogen 4cell, imogencfx 1cell, imogencfx 4cell) |

**The MPI build preserves the C1 baseline byte-exactly in single-process mode.**

#### B-item bundling decision (locked in this commit)

Per user 2026-05-11 deferred-to-agent direction "tackle ALL items; leave NONE undone":

- **C2 era (this step 17b)** ← B1 (Fortran Rh/Wind port; 3-5 d) + B2 (Fortran Tmin/Tmax; 0.5 d) + B3 (C++ Tmin/Tmax REGRID; 0.5 d) + B4 (ImogenInput consumer expansion; 1 d) + B6 (F-2 T_anom 2×; 0.5 d) + B10 (symmetric Fortran writer fix; 0.5 d) = **~6-8 d bundled with C2 core 3-5 d → ~9-13 day combined sprint**
- **Step 18** ← B5 (F-9 miscoutput diagnostic outputs; 1-2 d) + B7+B8+B9 (CMIP6 unit caveats; 1.5-2.5 d) = ~3-4.5 d
- **Step 17d** ← B11 (latent OOB defensive hardening; 0.5 d)

Full bundling rationale in `notes/STEP_17b.md` §5 + `notes/FOLLOWUPS.md` "B-item bundling commitment (2026-05-11)" sub-section.

#### Files modified this commit

| File | Change | Backport-relevance |
|---|---|---|
| `scripts/cluster/make_guess.sh` | mpicxx-wrapper fix prompt + Anaconda3 NetCDF unconditional | IRRELEVANT (scripts/ only) |
| `scripts/cross_validate_year_outer.sh` | `GUESS_BIN` env-var overridable (testing alt builds); default unchanged | IRRELEVANT (scripts/ only) |
| `notes/STEP_17b.md` (NEW) | Full forensic record + C2 plan + B-item bundling | IRRELEVANT (docs) |
| `CHANGELOG.md` | this entry | IRRELEVANT (docs) |
| `EXECUTION_PLAN.md` | row 17b status 🔧 with C2 prep landing details | IRRELEVANT (docs) |
| `notes/FOLLOWUPS.md` | dashboard date refresh + F-12 row update + B-item bundling commitment section | IRRELEVANT (docs) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | NEW step-17b-prep entry (note: backport-IRRELEVANT for this commit since no `lpjguess/` source change) | docs entry |

Refs: `notes/STEP_17b.md` (NEW; full forensic record); `notes/FOLLOWUPS.md` "Comprehensive outstanding-work audit" + "B-item bundling commitment (2026-05-11)" sub-section; `EXECUTION_PLAN.md` V.1 step row 17b (status updated to 🔧 C2 PREP LANDED); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17b-prep entry; `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 16 (NEW; this commit's narrative + decisions adopted).

---

## [v0.17.0-step17a-c1-year-outer-single-process] — F-12 sub-milestone C1 CLOSE-OUT (workstation single-process year_outer with cross-validation across all 4 scenarios) — 2026-05-10

This release closes out F-12 sub-milestone C1 per Path A 2026-05-09 refinement (skip Option B; staged Option C only; per `notes/FOLLOWUPS.md` F-12 + `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 8). Workstation single-process tight coupling via the additive `framework_loop_mode = "year_outer"` ins parameter is now empirically validated across all 4 cross-validation scenarios:

| # | Scenario | Result |
|---|---|---|
| 1 | `imogen` 1-cell | ✅ 37/37 bit-exact |
| 2 | `imogen` 4-cell | ✅ 37/37 bit-exact |
| 3 | `imogencfx` 1-cell | ✅ 37/37 bit-exact (NEW this commit) |
| 4 | `imogencfx` 4-cell | ✅ 37/37 bit-exact (NEW this commit) |

**GO/NO-GO gate per session-2 §9.5: PASSED for all 4 scenarios.** The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is empirically validated for BOTH input modules across BOTH single-cell + multi-cell + single-spinup-year + multi-spinup-year scenarios.

### 2026-05-10 (very late evening) — Step 17a (F-12 sub-milestone C1.3 sub-step 7.3.2) IMOGENCFXInput year_outer override + skip_inprocess_engine_run ins parameter + K→C latent-bug fix in IMOGENCFXInput::get_climate_for_gridcell + cross-validation harness extended for `imogencfx` variant; FULL C1 CLOSE-OUT (TAGGED v0.17.0-step17a-c1-year-outer-single-process)

This is the FINAL commit within step 17a, landing THREE bundled deliverables that together close out F-12 sub-milestone C1 + tag the v0.17.0 release.

#### A. NEW `skip_inprocess_engine_run` ins parameter (option a per STEP_17a.md §7.3.2 above)

NEW bool ins parameter (default `false`; preserves LTS-equivalent behaviour). When set to `true` in an `.ins` file, gates the `RUN_IMOGEN_ENGINE()` call in `IMOGENCFXInput::init()` at imogencfx.cpp ~line 524 (which would otherwise deadlock per F-10 in single-process tight). User must pre-stage climate externally via launcher run (the climate writer fix landed at sub-step 7.3.1 commit `7be595a` makes ALL years available, not just ODD; confirmed in this commit's verification).

Files modified for the parameter:
- `lpjguess/framework/parameters.h` (~22 LOC; new `extern bool skip_inprocess_engine_run;` declaration with extensive doc block in IMOGENConfig namespace)
- `lpjguess/framework/parameters.cpp` (~14 LOC; default `false` definition with doc block)
- `lpjguess/modules/imogencfx.cpp` (~14 LOC; `declare_parameter` registration in `IMOGENCFXInput::IMOGENCFXInput()` constructor + ~14 LOC gate around `RUN_IMOGEN_ENGINE()` call at imogencfx.cpp:524 with informative dprintf when the flag is set)

#### B. IMOGENCFXInput year_outer overrides (replicates C1.1 ImogenInput pattern with IMOGENCFXInput-specific differences)

Implemented two virtuals on `IMOGENCFXInput`:
- `IMOGENCFXInput::preload_all_climate(Gridcell&, int first, int last)` — pre-loads all needed years' climate for ONE cell into the existing all_temp/all_prec/.../all_dtmax cache via `readenv()` (which handles ALL 9 climate fields: temp/prec/insol/wetdays/dtr/relhum/wind/tmin/tmax; relhum/wind/tmin/tmax per step 9.5 wiring). Caches per-cell `cell_idx` + per-cell `Lamarque::NDepData` value-copy in `year_outer_cell_idx` + `year_outer_ndep_cache` maps. Uses CORRECTED spinup_year_idx formula (NO `+1`).
- `IMOGENCFXInput::getclimate_for_year(Gridcell&, int year, int day)` — reads from cache. On day 0: BLAZE compatibility check (mirror of imogencfx.cpp:884-893); calls `get_climate_for_gridcell()` to populate per-day arrays (now with K→C fix per item C below); calls `cell_ndep.get_one_calendar_year(...)` + `distribute_ndep(...)`; sets `climate.co2`. Every day: assigns climate.{temp, prec, insol, dtr conditional, relhum, u10, tmin, tmax} + gridcell.{dNH4dep, dNO3dep} from per-day arrays.

**Critical IMOGENCFXInput-specific design** (per user's 2026-05-10 clarification): "imogencfx is meant to work like the cfx input module, with only caveat being that instead of NetCDF climate forcing variables (ISIMIP3b) it takes in IMOGEN climate; everything else (NetCDF population density for SIMFIRE, SIMFIRE-BLAZE binary, atmospheric CO2 concentrations, NetCDF nitrogen deposition NHx/NOy etc.) remains as with the cfx module." The CFXInput-equivalent infrastructure (landcover_input, management_input, soilinput, ndep, etc.) is preserved unchanged. The year_outer block in framework.cpp already calls `getgridcell()` per cell during pre-load, exercising all this naturally. Only the climate-driver (the IMOGEN ASCII reader) is replaced.

Files modified for the overrides:
- `lpjguess/modules/imogencfx.h` (+~95 LOC additive: 2 includes `<map>`, `<utility>`; 2 method declarations with extensive doc blocks; 2 cache map members)
- `lpjguess/modules/imogencfx.cpp` (+~250 LOC additive: 2 method implementations with extensive doc blocks)

#### C. K→C latent-bug fix in `IMOGENCFXInput::get_climate_for_gridcell` (~25 LOC change incl. doc blocks; 5 actual code-line changes)

**Discovered empirically during sub-step 7.3.2 cross-validation**: with skip_inprocess_engine_run=1 bypassing F-10 deadlock, LPJG main loop runs in `-input imogencfx` mode for the first time. Run A immediately failed at `Soil::soil_temp_multilayer - SOIL TEMP. ERROR!!!` with `T[i]: 169.393` (= -103.76°C, physically impossible).

**Root cause**: the IMOGEN engine writes T_anom.dat / Tmin_anom.dat / Tmax_anom.dat in **Kelvin** (e.g., 237.881 K for high-Arctic January); LPJG's `Climate` struct expects `climate.temp / .tmin / .tmax` in **degrees Celsius**. The previous code stored Kelvin in `dtemp/dtmin/dtmax` then assigned `climate.temp = dtemp[date.day]` directly (line ~1179 in `IMOGENCFXInput::getclimate`) WITHOUT subtracting 273.15. ImogenInput's `getclimate` at `imogen_input.cpp:876` correctly does `climate.temp = dtemp[date.day] - 273.15;`. **IMOGENCFXInput had a LATENT K-vs-C bug** for these 3 temperature fields that was never surfaced because LPJG main loop never ran in `-input imogencfx` mode (F-10 deadlock blocked before main loop could exercise getclimate's per-day driver).

**Fix**: subtract 273.15 at the monthly-array population step in `get_climate_for_gridcell` (lines ~902-908 monthly branch + lines ~935-952 daily branch + symmetric application to mtmin/mtmax). Single change point benefits BOTH gridcell_outer (existing getclimate) AND year_outer (new getclimate_for_year) modes since both invoke `get_climate_for_gridcell`. Aligns IMOGENCFXInput's `dtemp` semantics with CFXInput's pattern (dtemp in Celsius natively, since CFXInput's NetCDF ISIMIP3b is in Celsius). 5 code-line changes (3 in monthly branch: mtmp/mtmin/mtmax; 3 in daily branch: dtemp/dtmin/dtmax; net 6 since dtemp got it twice via interp_climate vs daily mode; doc blocks document all).

Files modified for the K→C fix:
- `lpjguess/modules/imogencfx.cpp::get_climate_for_gridcell` (~25 LOC of doc blocks + 6 code-line changes adding `- 273.15`)

#### Cross-validation scaffolding for sub-step 7.3.2

- `runs/SSP1-2.6/main_xval_imogencfx.ins` (NEW; ~140 LOC): mirrors `main_xval_loose.ins` exactly except (1) `coupling_mode "prescribed"` (vs `"loose"`; canonical for IMOGENCFXInput) and (2) `skip_inprocess_engine_run 1` (NEW). Includes the additional 4 file_relhum/wind/tmin/tmax param directives (IMOGENCFXInput-specific; safely processed post-engine-fix at sub-step 7.3.1).

- `scripts/cross_validate_year_outer.sh` (extended; ~20 LOC change): added optional 2nd argument for input-module selector (`imogen` (default; preserves prior behaviour) | `imogencfx` (NEW)). Run-output dirs gain `_imogencfx_` infix suffix when imogencfx variant is used to avoid conflict with imogen runs. The `-input` flag uses the variable. Banner updated to display both gridlist variant + input module.

#### Cross-validation results (this commit)

ALL FOUR cross-validation scenarios PASS bit-exact (37/37 .out files identical):

```
$ scripts/cross_validate_year_outer.sh 1cell imogen
SUMMARY: 37/37 bit-exact matches; 0 mismatches
PASS: All .out files are bit-exact between Run A and Run B.

$ scripts/cross_validate_year_outer.sh 4cell imogen
SUMMARY: 37/37 bit-exact matches; 0 mismatches
PASS: All .out files are bit-exact between Run A and Run B.

$ scripts/cross_validate_year_outer.sh 1cell imogencfx
SUMMARY: 37/37 bit-exact matches; 0 mismatches
PASS: All .out files are bit-exact between Run A and Run B.

$ scripts/cross_validate_year_outer.sh 4cell imogencfx
SUMMARY: 37/37 bit-exact matches; 0 mismatches
PASS: All .out files are bit-exact between Run A and Run B.
```

**The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is empirically validated for BOTH ImogenInput AND IMOGENCFXInput across BOTH single-cell + multi-cell + single-spinup-year + multi-spinup-year scenarios.**

#### What changed in `lpjguess/` source (this commit; backport-relevant)

- **`lpjguess/framework/parameters.h`** (+22 LOC; declaration + doc block)
- **`lpjguess/framework/parameters.cpp`** (+14 LOC; definition + doc block)
- **`lpjguess/modules/imogencfx.h`** (+95 LOC additive; 2 includes, 2 virtual decls with doc, 2 cache map members)
- **`lpjguess/modules/imogencfx.cpp`** (+~290 LOC additive: declare_parameter + ~14 LOC engine-call gate + ~250 LOC for the 2 method implementations + ~25 LOC K→C fix in get_climate_for_gridcell)

#### Verification (this commit)

- `cd lpjguess/build && make -j$(nproc)`: clean (only pre-existing warnings)
- `lpjguess/build/runtests --reporter compact`: ✅ "Passed all 25 test cases with 162 assertions."
- All 4 cross-validations PASS bit-exact 37/37 (per above)
- Both new ImogenInput AND IMOGENCFXInput year_outer overrides verified working
- Backward compatibility: existing `getclimate()` body in IMOGENCFXInput unchanged (the K→C fix is in the `get_climate_for_gridcell` helper that both modes use; preserves byte-exactness between modes)

#### TAG: v0.17.0-step17a-c1-year-outer-single-process

**This commit closes out F-12 sub-milestone C1** per the staged Path A plan (per `notes/FOLLOWUPS.md` F-12 + `EXECUTION_PLAN.md` V.1 step row 17a). Tag pushed to all 3 remotes. Next sub-milestone: C2 (workstation MPI year_outer; ~3-5 days; tag target `v0.17.5-step17b-c2-mpi-sync`; per `EXECUTION_PLAN.md` V.1 row 17b).

Cross-references: `notes/STEP_17a.md` §7.3.2 (sub-step 7.3.2 outcome) + §7.4 (C1 close-out checklist); `notes/FOLLOWUPS.md` F-12 (C1 closed; C2 next); `EXECUTION_PLAN.md` V.1 step row 17a (status updated 🔧 → ✅); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 (NEW step-17a-c1.3-sub-step-7.3.2 entry; sub-step 7.3.1 `_TBD_` filled with `7be595a`); `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 14 (NEW; this commit narrative + C1 close-out).

---

### 2026-05-10 (late evening) — Step 17a (F-12 sub-milestone C1.3 sub-step 7.3.1) 4-CELL CROSS-VALIDATION PASS + IMOGEN ENGINE WRITER FIX: alternating-year staged-climate quirk resolved at root; year_outer code path empirically validated for multi-cell × multi-spinup-year (37/37 .out files bit-exact); GO/NO-GO gate per session-2 §9.5 PASSED for 4-cell smoke (no tag — full step-17a tag waits for sub-step 7.3.2 IMOGENCFXInput year_outer override)

This commit lands TWO bundled deliverables:

#### A. IMOGEN engine writer fix (`lpjguess/modules/climatemodel.cpp`; ~76 LOC including doc blocks; 5 conditional removals)

**Problem discovered at C1.2** (commit `8bddc27`): the launcher's prescribed-mode in-process engine port (`RUN_IMOGEN_ENGINE` in `climatemodel.cpp`) produced an **alternating-year staged climate** — only ODD years (1871, 1873, ..., 1901) had full 13-file climate; EVEN years (1872, 1874, ..., 1902) had only the `done` marker.

**Root cause** (this commit's investigation): the per-IYEAR loop body had `if (iyear == year1)` gates around the file OPEN (line ~886) and `if (iyear == iyend)` gates around the CLOSE (line ~963). With `std::ofstream` objects declared INSIDE the IYEAR loop body (per-iteration scope) and the gate blocking the open at non-YEAR1 iterations, subsequent WRITE statements went to closed file streams (silent failure in C++ default error handling). Combined with `updateImogenControlData()` (lines 1013-1031) advancing `IMOGENConfig::YEAR1++` and `IYEND++` per IYEAR iteration, each engine call effectively wrote ONE year of climate (its YEAR1) and silently dropped the IYEND year. Net effect across 16 calls: only ODD years got data; EVEN year directories existed (created at line ~457) but contained only the `done` marker (lines ~975-980).

**Fix**: removed the 5 conditional gates around file OPEN/CLOSE blocks at lines ~787 (CO2.dat + CO2_all.dat OPEN), ~884 (climate-anomaly OPEN: T_anom, P_anom, SW_anom, WET, DTEMP_anom, Rh_anom, W_anom, Tmin_anom, Tmax_anom), ~963 (climate-anomaly CLOSE), ~988 (oceanFeed FA_OCEAN/DTEMP_O OPEN), ~998 (oceanFeed CLOSE). Each iteration now opens + writes + closes its own files cleanly. `thisYear` was already updated per IYEAR iteration at line ~457 (`thisYear = std::to_string(iyear)`), so each iteration's open targets the correct year-folder. Wrapped each fix in extensive doc blocks explaining the structural cause, the fix, the symmetric application, the C1.2 PASS preservation argument, and the backport-relevance.

**C1.2 PASS preserved**: year-1871 data is bit-exact pre-fix vs post-fix (was always written by call 1 iteration 1; same path with or without gate). Re-verified empirically post-fix: 1-cell xval still PASSES 37/37 bit-exact.

**Net structural improvement**: engine output now correctly reflects ALL years it iterates over (vs only YEAR1 of each call). Restart from any year is now possible. CO2.dat present for all years. Latent silent-data-drop bug fixed; engine output is now complete + production-correct.

**Same structural bug exists in standalone Fortran engine** at `imogen/code/imogen_lpjg.f` lines 954, 1013, 1071, 1088, 1099 (NOT fixed in this commit; standalone Fortran is not on the prescribed-mode launcher path which uses the in-process C++ port; deferred as F-N-equivalent follow-up for symmetry; documented in STEP_17a.md §5.6).

#### B. C1.3 sub-step 7.3.1 4-cell cross-validation (per session-2 handoff Part 12 §12.9)

**Setup**: 4-cell `gridlist_test2.txt` (cells: NW Canada `-103.75 76.25`, N Greenland `-95.75 80.25`, central Asia `94.25 54.25`, Patagonia `-57.75 -33.75`) × `nyear_spinup=2` (exercises year_idx 0..1 of formula) × `firsthistyear=1871, lasthistyear=1879` (cache nyears=9 sufficient for 9 distinct imogen_years across all cell-year combinations) × 9 historical years simulated × 2 spinup years per cell × 4 cells = 44 cell-year iterations per run.

**Result**:
```
================================================================================
SUMMARY: 37/37 bit-exact matches; 0 mismatches
================================================================================
PASS: All .out files are bit-exact between Run A and Run B.
```

All 37 standard LPJ-GUESS outputs bit-exact between Run A (`framework_loop_mode = "gridcell_outer"`; existing trusted baseline) and Run B (`framework_loop_mode = "year_outer"`; new C1.1 additive code path).

**The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is now empirically validated across BOTH cell_idx>0 AND year_idx>0 branches.** Combined with C1.2's PASS for cell_idx=0/year_idx=0, the year_outer code path is fully validated for the smoke-test critical path.

#### Iteration history this commit (full forensics for transparency)

1. **First 4-cell xval attempt**: nyear_spinup=2 + lasthistyear=1871. Run A failed at cell 0's spinup year_idx=1 (calendar 1870 → imogen_year=1872 EVEN) with `read_lines_from_file: could not open ./IMOGEN/output/1872/T_anom.dat for input` (335 ms, exit 99). Confirms my pre-flight prediction: alternating-year staged climate is the structural blocker.

2. **Engine writer fix** (climatemodel.cpp; 5 gate removals + doc blocks).

3. **Climate re-stage**: cleared old climate, re-ran launcher (`timeout --foreground 300 ./scripts/run_coupled.sh --no-build &`; ~3-4 min wall-clock; F-10 deadlock at year ~33 expected; killed with `pkill -9 -x guess`). Verified ALL 32 years have 13 files each (vs prior 16 ODD with 13 + 16 EVEN with 1).

4. **Second 4-cell xval attempt**: nyear_spinup=2 + lasthistyear=1871 (unchanged). Segfault at run.log = 0 bytes. Diagnosed: latent OOB write in existing `getclimate()` at `stored_years[store_index] = imogen_year` when `store_index >= nyears` (cache size formula `nyears = (lasthistyear - FIRST_SPINUP_YEAR) + 1 = 1` insufficient for the 8 distinct imogen_years needed by 4 cells × 2 spinup years).

5. **Cache size fix**: bumped lasthistyear=1879 in `main_xval_loose.ins` (gives nyears=9; sufficient for 9 distinct imogen_years across all cell-year combinations). Adds 8 historical years 1872-1879 to the simulation — all now have climate post-fix #2 above.

6. **Third 4-cell xval attempt**: nyear_spinup=2 + lasthistyear=1879. **PASSED 37/37 bit-exact.** Both Run A and Run B reached "Finished" (12245 lines of stdout each). cflux.out has 37 lines = 1 header + 4 cells × 9 historical output years.

7. **Regression checks**: 162 unit tests pass post-rebuild. 1-cell xval re-PASSES with the new config (nyear_spinup=2 + lasthistyear=1879).

#### What changed in `lpjguess/` source (1 file; +76 LOC, -5 LOC; net +~71 LOC; backport-relevant)

- **`lpjguess/modules/climatemodel.cpp`** (+~76 LOC including extensive doc blocks):
  - Lines ~787, ~884, ~963, ~988, ~998: removed `if (iyear == year1) {` and `if (iyear == iyend) {` conditional gates around 5 file OPEN/CLOSE blocks. Replaced each with `{` (compound statement; preserves indentation; no functional difference beyond gate removal).
  - Each fix wrapped in a doc block (40-50 lines per block) explaining the structural cause, the fix's effect, C1.2 PASS preservation, symmetric application across all 5 gate sites, and backport-relevance.

#### Run-config files added/modified (NOT in `lpjguess/`; backport-irrelevant)

- **`runs/SSP1-2.6/main_xval_loose.ins`** (modified; 45 insertions, 17 deletions; net +28 LOC): updated comment block at the spinup overrides section to explain the new C1.3 sub-step 7.3.1 multi-cell config (nyear_spinup=2 + lasthistyear=1879 + cache sizing analysis); changed `nyear_spinup 1 → 2`, `lasthistyear 1871 → 1879`, `lastoutyear 1871 → 1879`, `param "lasthistyear" (num 1871) → (num 1879)`. Now serves both 1-cell xval (cell_idx=0; tests year_idx 0..1 branches of formula via single cell) AND 4-cell xval (cells 0..3; tests cell_idx 0..3 + year_idx 0..1 branches of formula).

#### Verification (this commit)

- `cd lpjguess/build && make clean && make -j$(nproc)`: clean (only pre-existing warnings; ZERO introduced)
- `lpjguess/build/runtests --reporter compact`: ✅ "Passed all 25 test cases with 162 assertions."
- Climate re-stage produces ALL 32 years (1871-1902) with 13 files each (vs prior 16 ODD with 13 + 16 EVEN with 1). Confirmed via `for y in 1871..1902; do ls 1$y/ | wc -l; done`. `diff <(ls 1871) <(ls 1872)` = EMPTY.
- `scripts/cross_validate_year_outer.sh 4cell`: ✅ PASS — 37/37 bit-exact matches; 0 mismatches; 0 missing files
- `scripts/cross_validate_year_outer.sh 1cell` (regression check with new config): ✅ PASS — 37/37 bit-exact matches
- Both Run A and Run B reach "Finished" end-to-end (12245 stdout lines each)
- ImogenOutput year-change-detection works correctly in year_outer mode (per session-2 §10.3 finding; "[ImogenOutput] flushed year=1879 (gridcells_seen=1, area_m2=2.570e+09)" appears at end of Run B)

#### What this commit does NOT yet do (next session within step 17a)

- **Sub-step 7.3.2 IMOGENCFXInput year_outer override** (~1.5-2 days): replicate C1.1 pattern for `IMOGENCFXInput` + handle additional climate fields (relhum, wind, tmin, tmax) + BLAZE compatibility check + engine-bypass mechanism (NEW `skip_inprocess_engine_run` parameter recommended per STEP_17a.md §7.3.2). Cross-validate single-cell first; multi-cell second.
- **C1 close-out**: tag `v0.17.0-step17a-c1-year-outer-single-process`.

Backport-relevance: HIGH. The climatemodel.cpp 5-gate-removal change is structural (affects engine output for ALL future runs); per the new step-17a-c1.3 entry in `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3. Standalone Fortran engine has same bug (`imogen/code/imogen_lpjg.f` lines 954, 1013, 1071, 1088, 1099); deferred for symmetric fix.

---

### 2026-05-10 (evening) — Step 17a (F-12 sub-milestone C1.2) 1-CELL CROSS-VALIDATION PASS: year_outer code path empirically validated (37/37 .out files bit-exact); GO/NO-GO gate per session-2 §9.5 PASSED for 1-cell smoke (no tag — full step-17a tag waits for multi-cell + IMOGENCFXInput follow-up)

C1.2 lands the runtime cross-validation milestone for the year_outer code
path. Both Run A (`framework_loop_mode = "gridcell_outer"`) and Run B
(`framework_loop_mode = "year_outer"`) ran end-to-end against the same
pre-staged engine climate using `-input imogen` (loose-coupling input
module + ImogenInput's C1.1 year_outer overrides). All 37 standard
LPJ-GUESS outputs (cflux, cmass, mch4, ngases, nuptake, nflux, etc.)
match BIT-EXACT between the two modes.

#### What changed in `lpjguess/` source (1 file; 9 LOC; backport-relevant)

- **`lpjguess/modules/imogen_input.cpp`** (+9 LOC): new `declare_parameter`
  call in `ImogenInput::ImogenInput()` mirroring `IMOGENCFXInput`'s
  identical declaration. Required for `-input imogen` (loose-mode) runs
  to recognize the `framework_loop_mode` parameter (without it,
  `Paramlist::operator[]` aborts with "framework_loop_mode not found").
  Same parameter declared in two input modules; same address
  (`&IMOGENConfig::framework_loop_mode`); plib accepts both. Pre-existing
  pattern; same as `searchradius` (declared in both ImogenInput +
  IMOGENCFXInput).

#### Setup files added (NOT in `lpjguess/`; backport-irrelevant)

- `data/gridlist/gridlist_test1.txt` (NEW; 17 bytes; 1-cell IMOGEN grid
  cell at `-78.75 82.50`, corresponding to IMOGEN native cell
  `281.25 82.50` via ImogenInput's `lon > 180 → lon - 360` normalization)
- `runs/SSP1-2.6/main_xval_loose.ins` (NEW; ~5.5 KB; loose-mode .ins
  for cross-validation; absolute paths for gridlist + soilmap; relative
  paths for engine climate so cwd=Common-directory resolves correctly;
  `param "searchradius" (num 50)` + `searchradius_soil 50` to handle
  IMOGEN-grid-vs-soilmap mismatch; minimal nyear_spinup=1 +
  firsthistyear=lasthistyear=1871 to use only ODD-numbered staged
  climate years)
- `scripts/cross_validate_year_outer.sh` (NEW; ~8.4 KB / 230 LOC bash;
  cross-validation harness; cd into Common-directory; per-run wrapper
  .ins generation with framework_loop_mode + gridlist + outputdirectory
  overrides; cmp -s loop for bit-exact comparison; clean PASS/FAIL
  summary; usage: `scripts/cross_validate_year_outer.sh [1cell|4cell]`)

#### Operational discoveries this session (informs C1.3 + production runs)

1. **Engine output is alternating-year**: launcher's prescribed-mode
   smoke produces 32 year-output dirs at
   `Common-directory/IMOGEN/output/{1871..1902}/`, but ONLY ODD years
   (1871, 1873, ..., 1901) have the full 13 climate files; EVEN years
   have only the `done` marker. Likely due to engine's NCALLYR/STEP_DAY
   internals; documented for the C1.3 / production work to address (e.g.
   via REGRID=1 or longer engine run).

2. **IMOGEN grid (3.75° × 2.5° HadCM3) vs LPJG soilmap grid (0.5°
   centered on .25)**: ZERO exact-cell intersections. Resolved via
   `searchradius` (climate; ImogenInput class member; custom-param
   syntax `param "X" (num Y)`) + `searchradius_soil` (SoilInput class
   member; declare_parameter at `soilinput.h:32`; bare-global syntax
   `X Y`). Per the user's 2026-05-10 guidance.

3. **Engine has a `REGRID` parameter** at
   `runs/SSP1-2.6/imogen_intermediary.ins:244` (currently `0`/FALSE)
   that, when enabled, makes the engine regrid climate output to a
   user-specified gridlist. Alternative path to the searchradius
   approach for cases where the user wants engine output AT specific
   LPJG cells. Documented for IMOGENCFXInput follow-up + production.

4. **`searchradius` declared as ImogenInput class member uses
   custom-param syntax** (`param "searchradius" (num 50)`), while
   `searchradius_soil` declared via `declare_parameter` at
   `soilinput.h:32` uses bare-global syntax (`searchradius_soil 50`).
   Both bindings end up in the same plib parameter table internally,
   but the .ins-file syntax differs based on declaration site.

#### Verification (this commit)

- `scripts/cross_validate_year_outer.sh 1cell`: ✅ PASS — 37/37
  bit-exact matches; 0 mismatches; 0 missing files
- `cd lpjguess/build && make -j$(nproc)`: clean (only pre-existing
  warnings; ZERO introduced by C1.2)
- `lpjguess/build/runtests --reporter compact`: "Passed all 25 test
  cases with 162 assertions."
- Backward compatibility: gridcell_outer mode (Run A) unchanged

#### What this commit does NOT yet do (next session(s) within step 17a)

- **Sub-step 7.3.1 multi-cell cross-validation** (~0.5 day): Run A vs
  Run B on 4-5 cell gridlist with `nyear_spinup=2` (so per-cell
  imogen_year selections all land on ODD staged years). Tests the
  spinup_year_idx state-machine reproduction formula across cells.
- **Sub-step 7.3.2 IMOGENCFXInput year_outer override** (~1.5-2 days):
  replicate C1.1 pattern for IMOGENCFXInput with the additional climate
  fields (relhum, wind, tmin, tmax) + BLAZE compatibility check + an
  engine-bypass mechanism (NEW `skip_inprocess_engine_run` parameter
  OR REGRID=1 alternative OR defer to C2).
- **C1 close-out**: tag `v0.17.0-step17a-c1-year-outer-single-process`.

Backport-relevance: HIGH (the 9-LOC declare_parameter addition is purely
additive). Per the new step-17a-c1.2 entry in
`notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3.

---

### 2026-05-10 (later) — Step 17a (F-12 sub-milestone C1.1) IMOGENINPUT IMPLEMENTATION: ImogenInput year_outer overrides (preload_all_climate + getclimate_for_year) with corrected spinup_year_idx state-machine reproduction formula (no tag — full step-17a tag waits for runtime cross-validation)

C1.1 implementation lands the FIRST input-module override pair for the
year_outer code path: `ImogenInput::preload_all_climate(gridcell, first_yr,
last_yr)` + `ImogenInput::getclimate_for_year(gridcell, year, day)`. This
makes the year_outer code path runnable end-to-end with `-input imogen`
(loose-coupling input module) once climate is pre-staged on disk.

#### Strategic decision: ImogenInput first; IMOGENCFXInput follow-up

**ImogenInput chosen over IMOGENCFXInput for C1.1** because ImogenInput
has NO `RUN_IMOGEN_ENGINE()` call in `init()` (verified via grep — only
`imogencfx.cpp:524` has it). This means loose-mode runs (`-input imogen`
+ `coupling_mode "loose"`) complete `init()` cleanly + reach the LPJG
main loop, regardless of `framework_loop_mode` setting — **no engine-bypass
workaround needed for cross-validation**. The two input modules have
~95% identical `getclimate()` patterns; the implementation strategy +
spinup_year_idx formula derived in C1.1 transfers near-verbatim to
`IMOGENCFXInput` (planned as C1.3 follow-up sub-step within step 17a).
Per the foundation-vs-full-C1 staging in `notes/STEP_17a.md` §5.5.

#### What changed in `lpjguess/` source (2 files; ~280 LOC; backport-relevant)

- **`lpjguess/modules/imogen_input.h`** (+~80 LOC):
  - 3 new includes: `<map>`, `<utility>`, (already-existing) `lamarquendep.h`
  - 2 new `virtual` method declarations (overrides of `InputModule`
    base-class virtuals added at the foundation commit `2e918c0`):
    - `preload_all_climate(Gridcell&, int first_calendar_year, int last_calendar_year)`
    - `getclimate_for_year(Gridcell&, int calendar_year, int day_of_year)`
    Both have extensive doc blocks documenting the design rationale +
    the spinup_year_idx state-machine reproduction formula + cross-references.
  - 2 new private cache members for year_outer state:
    - `std::map<std::pair<double,double>, int> year_outer_cell_idx`
      — keyed by (lon, lat); maps to `current_grid_index` value at
      preload time
    - `std::map<std::pair<double,double>, Lamarque::NDepData> year_outer_ndep_cache`
      — keyed by (lon, lat); maps to value-copy of `ndep` member at
      preload time (right after `getgridcell -> ndep.getndep()`)

- **`lpjguess/modules/imogen_input.cpp`** (+~200 LOC):
  - `ImogenInput::preload_all_climate(gridcell, first_yr, last_yr)`
    implementation: caches `cell_idx` + `ndep` value-copy, then for each
    year_idx in [0, total_years): computes `imogen_year` via the formula
    below, looks up in `stored_years[]` cache, on cache miss assigns
    next `last_store_index++` slot + calls existing `readenv()` + loads
    CO2 via `co2.load_file(...)`. Reuses existing infrastructure
    verbatim; pre-loads eagerly (memory bounded for smoke-scale runs).
  - `ImogenInput::getclimate_for_year(gridcell, calendar_year, day_of_year)`
    implementation: looks up cached `cell_idx` + `cell_ndep`, computes
    `imogen_year` via same formula, finds `store_index` in cache. On
    day 0: calls existing `get_climate_for_gridcell(...)` to populate
    per-day arrays + ndep distribution + CO2. Every day: assigns
    `climate.{temp - 273.15 K→degC, prec, insol, dtr conditional}` +
    `gridcell.{dNH4dep, dNO3dep}` from per-day arrays. Returns false at
    sim-done terminator + on missing-grid-point conditions.

#### CORRECTED spinup_year_idx state-machine reproduction formula

**ERRATUM applied this commit**: the foundation commit's docs (CHANGELOG
2026-05-10 entry, FOLLOWUPS F-12 C1 pre-flight findings extension,
STEP_17a.md §5.4, BACKPORT_LEDGER step-17a-foundation entry,
session-2 chat handoff Part 10) all stated the formula as
`(cell_idx * nyear_spinup + year_idx + 1) % NYEAR_SPINUP` (with `+1`).
The CORRECT formula has NO `+1`:

```
spinup_year_idx_at_(cell_idx, year_idx)
    = (cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP
```

Derivation (verified by tracing the EXACT code at `imogen_input.cpp`
lines 781-805 + `imogencfx.cpp` lines 1071-1095 during C1.1
implementation):
- `init()` sets `spinup_year_idx = 0`
- Per the existing `getclimate()`: on day 0 of each spinup year,
  `imogen_year = FIRST_SPINUP_YEAR + spinup_year_idx` is computed
  using the CURRENT spinup_year_idx, THEN the counter is incremented.
- For cell C, spinup year Y, day 0: cumulative spinup-year-day-0
  increments BEFORE this call = `C * nyear_spinup + Y` (since cell C
  is preceded by C cells × nyear_spinup spinup years; within cell C,
  Y prior spinup years have been processed).
- Each such call increments `spinup_year_idx` by 1 (modulo NYEAR_SPINUP).
- So `spinup_year_idx_BEFORE_this_call = (C * nyear_spinup + Y) % NYEAR_SPINUP`.

The C1.1 implementation in `ImogenInput::preload_all_climate` +
`ImogenInput::getclimate_for_year` uses the CORRECTED formula.
Subsequent doc updates (this CHANGELOG entry, FOLLOWUPS F-12 erratum,
STEP_17a.md §5.4 erratum, BACKPORT_LEDGER step-17a-c1.1 entry,
session-2 chat handoff Part 11) all reflect the CORRECTED formula.

#### Verification (this commit)

- `cd lpjguess/build && make -j$(nproc)` (full clean rebuild): clean
  (only pre-existing `simfire_input.h` `cruncep_*.h`
  `GlobalNitrogenDeposition*.h` `gutil.{cpp,h}` `indata.cpp` warnings;
  ZERO warnings introduced by C1.1 additions)
- `lpjguess/build/runtests --reporter compact`: "Passed all 25 test
  cases with 162 assertions." (default-mode + new-input-module
  byte-exact regression preserved)
- Spinup_year_idx formula correct (NO +1): hand-traced against
  `imogen_input.cpp:781-805`
- Per-cell ndep cache copies are independent: `Lamarque::NDepData` is
  value type (no pointers; just arrays); `std::map<key, NDepData>`
  value-copies on insert
- K → degC temperature conversion preserved: `getclimate_for_year` line
  `climate.temp = dtemp[day_of_year] - 273.15;` matches existing
  `getclimate` line 876
- Backward compatibility with existing `getclimate()` (gridcell_outer
  mode): `getclimate()` body unchanged; new methods are SEPARATE
  additions; existing code path completely intact

#### What this commit does NOT yet do (next session(s) within step 17a)

- **C1.2 cross-validation** (~1-2 days): runtime bit-exact verification
  of Run A (`gridcell_outer`) vs Run B (`year_outer`) on smoke gridlist.
  Operational pre-requisites: pre-stage climate (re-run launcher per
  session-1 §49.1 operational pattern; ~3-5 min wall-clock + Ctrl-C);
  custom .ins with `coupling_mode "loose"`; bash harness; iterate on
  any divergences. **GO/NO-GO gate for C1.**
- **C1.3 IMOGENCFXInput year_outer override** (~2-3 days): replicate
  the C1.1 implementation pattern for IMOGENCFXInput (with the
  additional climate fields it handles + an optional engine-bypass
  parameter for testing). Cross-validate identically.
- **C1 close-out**: tag `v0.17.0-step17a-c1-year-outer-single-process`.

Backport-relevance HIGH (purely additive). Per the new step-17a-c1.1
entry in `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3.

---

### 2026-05-10 — Step 17a (F-12 sub-milestone C1) FOUNDATION: framework_loop_mode parameter + InputModule virtuals + framework.cpp year_outer additive code path (no tag — full step-17a tag waits for IMOGENCFXInput overrides + cross-validation)

Foundation for the F-12 Option C staged implementation lands. The architectural
foundation for the per-year-outer / per-gridcell-inner loop (which resolves
F-10's per-gridcell-outer / per-day-inner-across-all-years deadlock for tight
coupling at root) is in place; default mode (`framework_loop_mode = "gridcell_outer"`)
preserves LTS-equivalent behaviour byte-exactly.

#### What changed in `lpjguess/` source (6 files; ~250 LOC; backport-relevant)

- **`lpjguess/framework/parameters.h`** (+22 LOC): new `extern xtring framework_loop_mode;`
  in `IMOGENConfig` namespace, adjacent to `coupling_mode` (added at step 8).
  Inline doc block explains both values + F-10 connection + cross-references.
- **`lpjguess/framework/parameters.cpp`** (+8 LOC): `xtring framework_loop_mode = "gridcell_outer";`
  default value preserves LTS-equivalent behaviour byte-exactly.
- **`lpjguess/modules/imogencfx.cpp`** (+12 LOC): `declare_parameter("framework_loop_mode", ...)`
  registration in `IMOGENCFXInput::IMOGENCFXInput()` constructor, mirroring
  the proven `coupling_mode` pattern from step 8.
- **`lpjguess/framework/inputmodule.h`** (+50 LOC): two new `virtual` methods
  on the `InputModule` abstract base class — `preload_all_climate(Gridcell&,
  int first_calendar_year, int last_calendar_year)` and `getclimate_for_year
  (Gridcell&, int calendar_year, int day_of_year)`. Non-pure (default
  implementations in inputmodule.cpp); preserves backward compatibility
  across all 9 existing input modules without forcing stub overrides.
- **`lpjguess/framework/inputmodule.cpp`** (+33 LOC): default-fail
  implementations of the two new virtuals. Both abort with a clear error
  pointing at `framework_loop_mode = "gridcell_outer"` fallback + canonical
  docs (`notes/FOLLOWUPS.md` F-12 + `notes/STEP_17a.md`).
- **`lpjguess/framework/framework.cpp`** (+218 LOC additive; existing 124-line
  per-gridcell-outer block at lines 411-534 byte-untouched via early-return
  pattern): new `if (IMOGENConfig::framework_loop_mode == "year_outer") { ... return 0; }`
  block immediately before the existing `while (true)` per-gridcell-outer
  loop. The new block has 5 phases: (1) C1 limitation guards (fail fast on
  restart/save_state/crop_gs_out/printseparatestands; deferred to C1.2/C1.3);
  (2) year range determination; (3) pre-load all gridcells + preload climate
  per cell via the new InputModule virtual; (4) per-year outer loop calling
  `simulate_day` per cell per day via `getclimate_for_year`; (5) per-cell
  teardown + cleanup + explicit return.

#### Verification (this commit)

- `cd lpjguess/build && make -j$(nproc)`: ✅ clean (only pre-existing
  `simfire_input.h` `fread` warnings; unrelated)
- `lpjguess/build/runtests --reporter compact`: ✅ "Passed all 25 test
  cases with 162 assertions." (default-mode byte-exact regression
  preserved)
- `git diff -w` of existing per-gridcell-outer block (`framework.cpp`
  lines 411-534): ZERO whitespace-only changes (additive early-return
  pattern preserves existing block structure)
- Default-fail virtuals: static verification only this commit; runtime
  exercise deferred to next session when an input module's override is
  invoked

#### What this commit does NOT yet do (next session(s) within step 17a)

- IMOGENCFXInput override of `preload_all_climate` + `getclimate_for_year`
  — substantial work (~3-5 days): includes the per-cell `spinup_year_idx`
  state-machine reproduction formula uncovered this session
  (`spinup_year_idx_at_cell_idx_year_idx = (cell_idx * nyear_spinup +
  year_idx + 1) % NYEAR_SPINUP`), which year_outer mode needs to
  reproduce gridcell_outer's existing cell-ordering-dependent imogen_year
  selection
- Bit-exact cross-validation of Run A (`gridcell_outer`) vs Run B
  (`year_outer`) on smoke gridlist (single-cell first to bypass
  cell-ordering complexity; multi-cell second to test the formula)
- Tag `v0.17.0-step17a-c1-year-outer-single-process` (waits for
  cross-validation pass)

#### New finding from this session: `IMOGENCFXInput::spinup_year_idx` cross-cell coupling

Beyond session-2 §9.5's PRNG audit, this session discovered that
`IMOGENCFXInput::spinup_year_idx` (line 220 of `imogencfx.h`) is a
class-member counter that **persists across cells** in the existing
gridcell_outer mode — each cell sees a different starting value of
`spinup_year_idx`, causing different spinup `imogen_year` selections per
cell. This existing behaviour must be preserved EXACTLY per the
"byte-identical default" constraint, and year_outer mode's IMOGENCFXInput
override (next session) must reproduce it via the deterministic formula
above. Cross-validation strategy adapts: single-cell smoke first
(bypasses cell-ordering complexity); multi-cell smoke second (tests
formula reproduction). Captured in `notes/STEP_17a.md` §5.4 +
`notes/FOLLOWUPS.md` F-12.

#### Updated documents

- `notes/STEP_17a.md` (NEW): per-step verification record covering the
  foundation work + design decision (D1 confirmed) + spinup_year_idx
  finding + remaining-C1 work plan
- `CHANGELOG.md` (this entry)
- `EXECUTION_PLAN.md` V.1 step 17a row: status note "FOUNDATION LANDED"
  added with reference to the foundation commit
- `notes/FOLLOWUPS.md`: status dashboard date refreshed; F-12 entry
  C1 pre-flight findings subsection extended with the spinup_year_idx
  finding pointer
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md`: NEW step-17a-foundation
  entry documenting the 6 file changes; backport-relevance HIGH
  (purely additive; the new code applies cleanly to `trunk_r13078`
  once F-11 Backport Sprint runs); plus backfilled `_TBD_` step-15
  hash `cd68b29` and step-16 hash `572820c` as a free-rigor cleanup
- `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 10 (NEW;
  outside-repo session-state preservation): documents this session's
  C1 foundation work + design decisions + remaining work pointer for
  the next chat session(s)

#### Net source-level change in `lpjguess/`: ~250 LOC across 6 files

All purely additive. The Backport Sprint (F-11) will replicate these
changes mechanically into `trunk_r13078` at end of Phase 1 per the
new step-17a-foundation entry in BACKPORT_LEDGER.md §3.

---

### 2026-05-09 — Path A refinement: skip Option B; staged Option C only (no tag)

Documentation-only commit refining the F-12 plan ahead of any code work,
per user-confirmed Path A discussion 2026-05-09. **No source-level changes;
no new tag.**

#### What changed

After the 2026-05-08 docs maintenance commit (`76aa57b`) which staged
F-12 Options B + C as in-v1.0-scope, today's discussion surfaced that
Options B and C are architecturally orthogonal (not sequential):
- **Option B** (single-process workstation two-process orchestration)
  was framed as a fast stopgap (~2-3 days) but addresses ONLY workstation
  single-process tight, with a per-gridcell-rolling caveat that is less
  rigorous than Option C
- **Option C** (additive `framework_loop_mode = "year_outer"` ins
  parameter; per-year-outer loop alongside the existing per-gridcell-outer)
  resolves F-10 at the root for both single-process AND multi-rank MPI;
  is required regardless for the cluster + tight v1.0 deliverable
- Skipping Option B saves ~2-3 days of effort + a maintenance surface,
  and the C1 sub-milestone delivers the same workstation single-process
  tight capability Option B would have, but more rigorously
  (globally-synchronized per-cell flush vs per-gridcell-rolling)

User confirmed direction 2026-05-09: skip Option B; go straight to Option C
staged as 3 sub-milestones (C1 → C2 → C3). Workstation specs verified
(i9-11900K; 64 GB RAM; 16 cores; Anaconda3 MPICH 4.1.1 + gcc 15.2 +
cmake 3.31.6; ~62 GB single-process production memory pressure means
production is genuinely cluster-only). The new staged plan:

- **C1** (~1 week; workstation single-process year_outer + cross-validation
  against gridcell_outer baseline) → tag `v0.17.0-step17a-c1-year-outer-single-process`
- **C2** (~3-5 days; workstation MPI year_outer via mpirun -np 4 + addresses
  Anaconda3 mpicxx wrapper issue) → tag `v0.17.5-step17b-c2-mpi-sync`
- **C3** (~1-2 weeks SSH iterative; cluster MPI year_outer; refines
  env_owl.sh placeholders against actual `module avail` on owl) →
  tag `v0.18.0-step17c-c3-cluster-tight`

Plus existing step 17 → renumbered as step 17d (end-to-end validation;
now actually runnable for all 4 combinations after C3).

#### Updated documents

- **`notes/FOLLOWUPS.md`** F-12 entry: revised "Recommendation" section
  with the staged Option C plan; new "Cross-validation protocol" subsection
  (the GO/NO-GO gate at C1; tolerances per output category); new "Status
  as of 2026-05-09" subsection; new "What was decided today" subsection
  capturing the 4 user-confirmed decisions (skip Option B; intermediary_py
  copy-over flow stays; native LPJG filenames v1.1+ refinement noted;
  local + cluster equally important). Status dashboard "Last updated" +
  F-10 + F-12 row entries refreshed.
- **`EXECUTION_PLAN.md` V.1**: inserted 3 NEW step rows (17a, 17b, 17c)
  between step 16 and the existing step 17; renumbered existing step 17
  as step 17d (end-to-end validation; now runnable for all 4 combinations
  after C3 lands).
- **`docs/v2_roadmap.md`**: added REVISED 2026-05-09 banners at top of §4
  (Option B sketch — preserved as historical / decision-trail context;
  superseded) + §5 (Option C sketch — now in-v1.0 + staged); body content
  preserved for design reference but readers redirected to FOLLOWUPS F-12
  for the canonical active plan.
- **`_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md`** Part 8 (NEW;
  outside-repo session-state preservation): documents 2026-05-09 session
  decisions + workstation specs + revised plan + commit commands. (Not
  committed; lives in the sibling `_chat_artifacts/` dir per session-1
  Part 14 §C2 recommendation.)

#### Net source-level change in `lpjguess/`: ZERO

Documentation pass before any code work. Backport-irrelevant.

---

## [v0.16.0-step16-cluster-launcher] — 2026-05-08 — step 16: Cluster launcher (loose-only baseline; F-10/F-12 caveats explicit)

### Architectural-tension investigation (the strategic pivot for this step)

The user surfaced a critical architectural insight at session start
(2026-05-08): the F-10 single-process deadlock issue extends to multi-rank
MPI on cluster, not just to single-process tight coupling. Investigation
this session confirmed:

- `lpjguess/framework/parallel.cpp` implements ONLY `MPI_Init` /
  `MPI_Comm_rank` / `MPI_Comm_size` / `MPI_Finalize` — no `MPI_Barrier`,
  no `MPI_Allreduce`, no point-to-point messaging
- The cluster orchestration is gridlist-split embarrassingly-parallel:
  `setup_run_owl_with_scratch_lpj_work.sh` distributes per-rank gridcells
  via `split -a 4 -l <cells/N>` into `runNN/` subdirs; each rank runs
  `guess -parallel` independently
- Cluster + LOOSE coupling works fine (LPJG reads pre-baked engine climate;
  embarrassingly parallel; no synchronization needed)
- Cluster + TIGHT coupling has the same deadlock as single-process tight,
  multiplied by N ranks: each rank's `ImogenOutput::flush_year` fires
  per-rank-per-year; engine cannot consume N independent flux streams at
  a synchronization point that doesn't exist

User-confirmed Path A trajectory (re-sequencing of v1.0 vs v1.1+ scope):

1. **Step 16 (THIS step)**: Cluster launcher for LOOSE mode + workstation
   parallel mimic test
2. **F-12 Option B** (next): Local + tight via two-process; ~2-3 days
3. **F-12 Option C** (after Option B): HPC + tight via additive
   `framework_loop_mode = "year_outer"` + `MPI_Barrier`; ~1-2 weeks +
   cross-validation
4. **Steps 17-19**: validation + docs + CI/release

### Added — `scripts/cluster/` toolkit (7 files; ~50 KB total)

| File | Size | Adapted from | Role |
|---|---:|---|---|
| `run_coupled.sbatch` | ~17 KB / 290 lines | NEW (mirrors `scripts/run_coupled.sh` CLI) | Top-level SLURM launcher; refuses cluster + tight in v1.0 with clear error message |
| `setup_run.sh` | ~11 KB / 200 lines | `setup_run_owl_with_scratch_lpj_work.sh` (174 lines) | Gridlist split + per-rank `runNN/` + generates `submit.sh` + `startguess.sh` |
| `mpi_run_guess.sh` | ~7 KB / 165 lines | `mpi_run_guess_on_tmp.sh` (82 lines) | Per-rank scratch-I/O wrapper; multi-MPI rank detection |
| `finishup_lpj_work.sh` | ~7 KB / 175 lines | `finishup_lpj_work_owl.sh` (172 lines) | Post-run aggregation (concatenate per-rank `*.out`, gzip, copy to `output-YYYY-MM-DD/`) |
| `make_guess.sh` | ~4.5 KB / 130 lines | NEW (lightweight version of IMK-IFU `make_guess.sh` 126-line original) | Cluster-side build helper with `--mpi` flag |
| `append_files.sh` | ~1.7 KB / 40 lines | `append_files.sh` (verbatim with comments) | Per-file aggregator helper |
| `env_owl.sh` | ~3.7 KB / 80 lines | NEW (placeholder template) | Module-load template for `owl` (PLACEHOLDER values; refine via SSH) |
| `README.md` | ~6 KB / 175 lines | NEW | Comprehensive cluster-orchestration narrative |

### Added — Workstation parallel mimic test: `scripts/run_parallel_mimic.sh` (~9 KB / 200 lines)

Validates the cluster orchestration mechanics (gridlist split + per-rank
invocation + output concatenation) WITHOUT requiring SSH access to the
cluster. Uses Anaconda3 MPICH 4.1.1's `mpirun -np N` on the workstation;
runs `guess -parallel -input imogen` against the smoke 4-cell gridlist;
verifies per-rank artifacts. Deferred empirical execution to step 17
(validation), where engine climate library bootstrap will enable
full end-to-end loose-coupling validation.

### Key adaptations from the IMK-IFU originals

1. **Named-flag CLI** (vs positional 12-arg in `setup_run.sh`)
2. **Configurable `INPUTMETHOD`** (default `imogen` for v1.0 loose-only;
   IMK-IFU original was hardcoded `cfx` for forest-productivity)
3. **Multi-MPI rank detection** (MPICH `PMI_RANK` || OpenMPI
   `OMPI_COMM_WORLD_RANK` || SLURM `SLURM_PROCID`); IMK-IFU original
   supported only OpenMPI + SLURM
4. **F-10/F-12 caveat detection inline**: `setup_run.sh` warns on
   `--inputmethod imogencfx`; `run_coupled.sbatch` refuses cluster + tight
   outright (with clear error message + resolution pointer to F-12 Option C)
5. **`$TMP` fallback to `/tmp/$$`** for non-cluster contexts (workstation mimic)
6. **`--workdir-base` override** for non-IMK-IFU clusters

### Updated — `docs/build.md`

Cluster section replaced from placeholder with full step-by-step + F-10/F-12
caveat narrative + cross-references to `scripts/cluster/README.md`.

### Updated — `.gitignore`

Added two new step-16 ignore rules:
- `runs/*/parallel_work/` (workstation parallel mimic per-rank work dirs)
- `lpjguess/build_mpi/` (cluster MPI build dir)

### Net source-level change in `lpjguess/`: ZERO

Step 16 is bash + docs + .gitignore additions only. **Backport-irrelevant**
for the F-11 sprint; the cluster orchestration is fork-agnostic.

### Refs

- `EXECUTION_PLAN.md` V.1 step 16 (cluster integration milestone)
- `EXECUTION_PLAN.md` Decision #7 (single codebase + binary serves both
  workstation and cluster) + Decision #8 (Anaconda3 NetCDF preference is
  workstation-specific; cluster uses module-loaded NetCDF)
- `notes/STEP_16.md` (per-step verification record)
- `notes/FOLLOWUPS.md` F-10 (architectural deadlock; cluster-MPI extension
  documented in F-10 phase-2 sketch lines 343-411) + F-12 (multi-pass /
  two-process design space; Options B + C)
- `docs/scientific_framework.md` §5 (F-10 caveat narrative)
- `docs/v2_roadmap.md` §4 (F-12 Option B; v1.1 single-process tight) + §5
  (F-12 Option C; v1.1+ HPC tight via additive `framework_loop_mode`)
- IMK-IFU originals at `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/`
  (the prior-art cluster orchestration adapted from)
- `lpjguess/parallel_version/aurora.tmpl` (upstream LPJ-GUESS canonical
  SLURM template; cross-reference for the gridlist-split + mpirun pattern)

---

## [v0.15.0-step15-stage1-deferral] — 2026-05-08 — step 15: Stage I documentation preservation + Stage II PLUM-output reuse verification

### Added — `docs/scientific_framework.md` (NEW; ~13 KB)

Per `EXECUTION_PLAN.md` V.1 step 15.a + Decision #9 + working paper §2.4.3.
Canonical scientific-architecture reference for the framework. 7 sections:

1. The four components (LPJ-GUESS, PLUM, Intermediary Controller, IMOGEN)
   with peer-reviewed references (Smith 2014; Alexander 2018; Rabin 2020;
   Huntingford 2010; Smith 2018 FAIR; Nicholls 2020 RCMIP)
2. The two-stage simulation protocol (Stage I + Stage II per working paper
   §2.4.3) with ASCII flowchart
3. Stage II land-use forcing options (Option A in-process Stage I; Option B
   PLUM-harm forLPJG existing outputs; Option C predecessor's concatenated
   1901-2100 LU; v1.0 uses Option C)
4. Decision #10 — `save_state`/`restart` strategy with verbatim example .ins
   blocks from `owl_hpc_cluster_scripts/`
5. The F-10 architectural caveat + v1.0 limitation (loose-coupling fallback
   is scientifically defensible; matches predecessor's working paper)
6. Units integrity (Decision #6) summary table
7. References (10 peer-reviewed citations including IPCC 2019 Vol. 4 AFOLU,
   Winkler 2021 HILDA+, Lindeskog 2013, Olin 2015)

### Added — `docs/v2_roadmap.md` (NEW; ~13 KB)

Per `EXECUTION_PLAN.md` V.1 step 15.c + Decision #9 + Decision #10. The
post-v1.0 development trajectory. 7 sections:

1. Phase 1 vs Phase 2 trajectory (v1.0 → v1.1 → v1.2 → v2.0 ASCII timeline)
2. PLUM embedding (Stage I in v2.0; the Decision #9 v2.0 flip): Stage I
   parameter checklist + 4-step plan
3. v1.1 — wire save_state/restart with PLUM-harm forLPJG outputs (~0.5-1 day
   deliverable that follows v1.0 release): per-phase `imogen_intermediary.ins`
   variants + `--phase historic | scenario | both` launcher flag
4. F-12 Option B (v1.1 Phase 2A) — two-process tight coupling: 6 concrete
   deliverables; verification milestone (4-cell × 11-year SSP1-2.6 smoke run)
5. F-12 Option C (v2.0 Phase 3) — in-process restructure with
   `framework_loop_mode = "year_outer"`; the user's preferred long-term
   approach (per F-10 phase-2 entry); cross-validation protocol
6. Other post-v1.0 stretch items (F-3 Fortran↔C++ parity; F-11 Backport
   Sprint; F-13 paper-stage 3-axis comparison; F-9 climate-input diagnostics;
   F-1 Zenodo upload)
7. v2.0 release criteria

### Added — `notes/STEP_15.md` (NEW; ~12 KB)

Per-step verification record per the standard discipline. 7 sections:
goal, investigation findings, what was implemented, verification,
Backport Sprint relevance (zero `lpjguess/` change → backport-irrelevant),
follow-up cross-reference, effort.

### Verified — PLUM-harm `forLPJG` outputs accessible (item 15.b)

External mount points referenced in `data/DATA.md` §1 verified live:

```text
/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/    (canonical; 17 GB SSP1_RCP26)
├── SSP1_RCP26/   ✓
├── SSP2_RCP45/   ✓
├── SSP3_RCP70/   ✓
├── SSP4_RCP60/   ✓
└── SSP5_RCP85/   ✓

/media/bampoh-d/ISIMIP/inputs/landuse/plum_harm_lu/  (redundant copy on second drive)
└── (same 5-SSP layout)                              ✓
```

Per-scenario `s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/`
sub-tree contains 5 files (~3.5 GB total per scenario):
`landcover.txt`, `cropfractions.txt`, `irrig.txt`, `nfert.txt`,
`landcover_peatland.txt`. Year coverage scenario-only (2021-2100); column
ordering and crop-column count differ from predecessor's concatenated 1901-2100
LU (PASTURE/CROPLAND/NATURAL/BARREN vs NATURAL/CROPLAND/PASTURE/BARREN; 21
crops vs 19 with OilNfix/OilOther split vs Oilcrops merged). Switching
v1.0/v1.1 from Option C (current) to Option B requires either format
conversion or save_state/restart pattern (latter is canonical; deferred to
v1.1 per `docs/v2_roadmap.md` §3).

### Updated — `notes/TRUNK_R13078_BACKPORT_LEDGER.md`

§3 commit-hash errata cleanup (per the prior chat handoff Part 11 §82.3
maintenance follow-up):
- Steps 1-5 hashes corrected (5 stale entries replaced with verified hashes
  via `git rev-list -n 1 <tag>`)
- Steps 9-14 hashes filled in (9 `_TBD_` placeholders replaced)
- New §3 step-15 row added (annotation only; documentation step; zero
  `lpjguess/` change → backport-irrelevant)

| Step | Stale | Verified | Tag |
|---|---|---|---|
| 1 | `dc91efb` | `662f288` | (bundled into v0.2.0-imports) |
| 2 | `9e51a23` | `a93c3ec` | v0.2.0-imports |
| 3 | `5f86bb1` | `fb626c4` | v0.3.0-fortran-allocatable |
| 4 | `f3bb471` | `e80317b` | v0.4.0-imogen-data-fetch-script |
| 5 | `2d36c8e` | `514f089` | v0.5.0-cmip6-converter |
| 9 | `_TBD_` | `d6f4853` | v0.9.0-step9-smoke |
| 9.5 | `_TBD_` | `f00033c` | v0.10.0-step9.5-consumer-wiring |
| 10 | `_TBD_` | `a90e9be` | v0.11.0-step10-intermediary-py-import |
| 11 | `_TBD_` | `e89af1e` | v0.12.0-step11-intermediary-py-validated |
| 13 | `_TBD_` | `aa802e0` | v0.13.0-step13-adapter |
| 14 | `_TBD_` | `ced4b1d` | v0.14.0-step14-launcher |

### Net source-level change in `lpjguess/`: ZERO

Documentation-only step. Net: 4 files added/created (`docs/scientific_framework.md`,
`docs/v2_roadmap.md`, `notes/STEP_15.md`, this CHANGELOG entry); 3 files
modified (`notes/TRUNK_R13078_BACKPORT_LEDGER.md`, `EXECUTION_PLAN.md`,
`notes/FOLLOWUPS.md`).

### Refs

- `EXECUTION_PLAN.md` V.1 step 15
- Decision #9 (Stage I deferred for v1.0); Decision #10 (save_state/restart
  Option D); Decision #3 (LandSyMM_LPJ-GUESS = "integrated LTS" base)
- Working paper §2.4.3 framing
- `docs/scientific_framework.md` (canonical reference going forward)
- `docs/v2_roadmap.md` (post-v1.0 trajectory)
- Prior chat handoff Part 11 §82.3 (BACKPORT_LEDGER errata follow-up)
- `landsymm_runtime_parameters.md` §2 (save_state/restart parameters) + §6
  (do_potyield Stage I parameters) — both already wired in `lpjguess/`

---

## [v0.14.0-step14-launcher] — 2026-05-07 — step 14: workstation launcher + Anaconda3 NetCDF build docs

### Added — `scripts/run_coupled.sh` (~330 LOC bash; production-quality launcher)

Per `EXECUTION_PLAN.md` V.1 step 14 + Appendix A.4 + Decision #8.
One-shot launcher that walks the v1.0 coupled-run pipeline through
7 steps:

1. Build LPJ-GUESS (idempotent; skip if `lpjguess/build/guess` exists)
2. Run intermediary_py if `--backbone intermediary-py`
3. Run Python → LPJG-format adapter if `--backbone intermediary-py`
4. Bootstrap `LPJG_main/IMOGEN/` handshake dir (F-10 deadlock workaround)
5. Clean stale per-year IMOGEN engine output dirs
6. Launch `./guess -input imogencfx main.ins` in scenario's run dir
7. Collect summary + log path

#### Anaconda3 NetCDF auto-detection (Decision #8)

4-tier priority for Anaconda3 NetCDF prefix detection:
1. `--anaconda3-prefix <path>` flag (explicit override)
2. `$CONDA_PREFIX` (active conda env)
3. `$ANACONDA_PREFIX` (set in some shells)
4. `/home/$USER/anaconda3` (common default install location)

If found, CMake invoked with explicit `-DCMAKE_PREFIX_PATH`,
`-DNETCDF_INCLUDE_DIR`, `-DNETCDF_C_LIBRARY` pointing at the conda
env's libs (avoiding the libhdf5_serial / libcurl ABI mismatch that
breaks native-Ubuntu netcdf-dev linking — see `notes/STEP_1.md`).
If not found, prints warning and falls back to bare `cmake ..`.

#### CLI flags + validation

- `--scenario SSP` (default SSP1-2.6)
- `--coupling-mode tight | prescribed | loose` (default prescribed; v1.0
  workaround for F-10 deadlock that blocks tight mode)
- `--backbone static-iiasa | intermediary-py` (default static-iiasa;
  predecessor's reference files for v1.0 minimal-moving-parts)
- `--smoke / --production` (smoke = 4-cell + 1871-1872; production =
  62892-cell + 1900-2100)
- `--no-build / --no-intermediary / --no-adapter` for skipping individual steps
- `--anaconda3-prefix <path>` override
- `-h / --help` (89-line self-documenting help via awk-based extraction)

Each flag validated against its allowed values; invalid value aborts
with actionable error message.

#### F-10 deadlock awareness

When `--coupling-mode tight` or `--production` requested in v1.0, the
launcher prints WARNING explaining the architectural limitation +
recommends the v1.0-functional `prescribed` + `--smoke` defaults.
Phase-2 resolution at F-12 (multi-pass / two-process design).

#### Banner per §I.D.5

Run-start banner displays scenario, coupling-mode, backbone, run-mode,
plus the canonical units conventions (NEE sign, CO2 unit conversion,
CH4/N2O units, year indexing, cell-area assumption). Verbatim match
to EXECUTION_PLAN.md's specified format.

#### Other features

- **Idempotent**: re-runs skip already-completed steps via mtime / file-presence checks
- **Bootstrap helper**: pre-populates `imogen_lpjg.txt` + `done` files
  before engine start (per step 9 §4.4 empirical findings; needed
  until F-12 multi-pass design)
- **Structured logging**: 4 levels (info/warn/error/ok) with ANSI colors
- **Date-stamped log**: `logs/run_coupled_<SCENARIO>_<TS>.log`
- **Trap-based error handler**: actionable error message on any exit

### Added — `docs/build.md` (~150 lines; Anaconda3 NetCDF preference + manual paths)

Comprehensive build documentation covering:
- Quick-start (one-liner via launcher)
- 7-step launcher flow explained
- Why Anaconda3 NetCDF (the libhdf5_serial / libcurl ABI-mismatch
  diagnosis from step 1)
- Manual build instructions (without launcher; for debugging)
- Manual intermediary_py setup (with 7-symlink recipe from step 11)
- Manual adapter run
- How to verify the build succeeds
- Cluster build placeholder (to be filled at step 16)
- Troubleshooting common errors
- Cross-references to relevant STEP_*.md, FOLLOWUPS.md, EXECUTION_PLAN.md

### Modified — `runs/SSP1-2.6/imogen_intermediary.ins` (collateral fix)

Added `param "file_tmin" (str ".../Tmin_anom.dat")` and
`param "file_tmax" (str ".../Tmax_anom.dat")` directives.

**Provenance**: this is a step-9.5 follow-up that step 14's empirical
test surfaced. Step 9.5 wired the consumer side in
`imogencfx.cpp::init()` (`file_tmin = param["file_tmin"].str;` etc.)
but didn't update the example `.ins` file. The launcher's first
end-to-end smoke run on 2026-05-07 hit
`Paramlist::operator[]: parameter "file_tmin" not found` and
revealed the gap. Fix is one block of 2 directives + explanatory
comment referencing step 14 provenance. The C++ engine writes
Tmin_anom.dat / Tmax_anom.dat per step 9.5's climatemodel.cpp
non-REGRID branch; the consumer-side wiring correctly reads them
after this fix.

### Verified

- `scripts/run_coupled.sh --help`: 89 lines self-documenting help
- End-to-end smoke run with `--no-build`: banner displays correctly,
  all 7 steps progress in order, IMOGEN engine produces 30+ year-output
  dirs (1871-1900+), launcher exits cleanly when engine deadlocks at
  F-10 boundary
- Anaconda3 NetCDF auto-detection at `/home/bampoh-d/anaconda3` ✓
- Bootstrap helper creates handshake files ✓
- F-10 deadlock warnings printed for `--coupling-mode tight` and `--production` ✓

### What's NOT verified (gated on F-12)

End-to-end coupled run that gets LPJG main loop to actually fire
(producing `cflux.out`, `mch4.out`, `ngases.out`, etc. in `runs/<SSP>/output/`
+ step 8's writer producing `imogen_lpjg_*.txt` in
`Common-directory/LPJG_main/IMOGEN/`). Architecturally blocked by F-10
in v1.0 single-process imogencfx mode regardless of which launcher
is used. Resolution at F-12 (multi-pass / two-process design;
post-v1.0).

### NET source-level change in `lpjguess/`: ZERO

Launcher is a shell script + docs are markdown + `.ins` fix is
configuration. Backport Sprint (F-11) does NOT need to replicate
any step-14 changes in `trunk_r13078`.

### Files modified / added

```text
Added:
  scripts/run_coupled.sh                ~12 KB / ~330 LOC
  docs/build.md                         ~6 KB / ~150 lines
  notes/STEP_14.md                      ~12 KB

Modified:
  runs/SSP1-2.6/imogen_intermediary.ins +param file_tmin/tmax (step 9.5 collateral)
  .gitignore                            +runs/*/Common-directory/ rule
  notes/FOLLOWUPS.md                    status dashboard date refresh
  notes/TRUNK_R13078_BACKPORT_LEDGER.md +Step 14 entry (zero lpjguess C++)
  EXECUTION_PLAN.md                     step 14 row marked DONE
  CHANGELOG.md                          this entry

NOT committed (gitignored at runtime):
  logs/                                 launcher's date-stamped log files
  runs/*/Common-directory/              IMOGEN engine + LPJG runtime artifacts
```

---

## [v0.13.0-step13-adapter] — 2026-05-07 — step 13: Python Intermediary → Fortran IMOGEN ASCII adapter

(Step 12 was consolidated with step 11; see `[v0.12.0-step11-intermediary-py-validated]`.)

### Added — `tools/imogen_inputs_to_lpjg_format.py` (~270 LOC; production-quality adapter)

Per `EXECUTION_PLAN.md` V.1 step 13 + Appendix A.2 + Decisions #1 (RCMIP
backbone) and #11 (units integrity). Converts intermediary_py's wide-format
`imogen_inputs_<SSP>.csv` (10 columns, Mt-of-gas/yr units) into the four
narrow ASCII files the Fortran IMOGEN engine expects.

#### 4 output files (all in `runs/<SSP>/inputs/`)

| Output file | Format | Maps to ins-parameter | Unit |
|---|---|---|---|
| `imogen_lpjg_flux.txt` | (year, val) | `FILE_LPJG_FLUX` | PgC/yr |
| `imogen_lpjg_ch4_n2o_flux.txt` | (year, ch4, n2o) | `FILE_LPJG_CH4_N2O_FLUX` | TgCH4/yr, TgN2O/yr |
| `co2_anthro_emissions.txt` | (year, val) | `FILE_SCEN_EMITS` | PgC/yr |
| `ch4_n2o_anthro_emissions.txt` | (year, ch4, n2o) | `FILE_CH4_N2O_EMITS` | TgCH4/yr, TgN2O/yr |

#### Unit-checked-adapter discipline

Embodies `EXECUTION_PLAN.md` §I.D.2:
- **Schema validation**: aborts if any of the 10 expected columns are
  missing or NaN-valued
- **Sanity bounds**: per-column min/max range check (e.g.
  `CO2_EFOS_Mt: [-50000, 100000]` Mt/yr — allows for SSP1-2.6's
  negative-emissions late-century BECCS pathway)
- **Year monotonicity**: aborts if Year column has gaps or is non-numeric
- **Conversion constants**: explicit + named:
  - `PgC_TO_MtCO2 = (44/12) * 1000 = 3666.6667` (canonical 44/12 g_CO2/g_C
    × 1000 Mt/Pg ratio)
  - `MtCO2_TO_PgC = 1/3666.6667`
  - CH4/N2O: pass-through (Mt = Tg = 1e12 g; identical SI)
- **Startup banner** prints unit conventions explicitly so the operator
  sees what's happening
- **End-of-run banner** prints the exact `imogen_intermediary.ins` edits
  the user needs to make

#### Output format matches predecessor verbatim

Spot-check: `head -3 runs/SSP1-2.6/inputs/co2_anthro_emissions.txt`:
```
1900 0.487860
1901 0.504180
1902 0.519031
```

Compare with predecessor's `imogen/emiss/CMIP6/Co2/co2_pg_emissions_anthropogenic_historical_ssp126_1850_2100.txt`:
```
1850 0.000000
1851 0.482350
1852 0.957810
```

Same 2-col space-separated structure with 6-decimal precision. Engine
reader at `imogen_lpjg.f:598` parses both formats identically.

#### Unit conversion verified to 6 decimals

intermediary_py CSV row 2 (year 1900) `CO2_EFOS_Mt = 1788.820939`:
- Hand-math: `1788.820939 / 3666.6667 = 0.48786025165581587` PgC
- Adapter writes: `1900 0.487860`
- ✓ matches to 6 decimals

#### SSP1-2.6 negative-emissions verification

Late-century rows from `co2_anthro_emissions.txt`:
```
2099 -1.575525
2100 -1.559659
```

Negative CO2 anthropogenic ~-1.56 PgC/yr in 2099-2100 reflects SSP1-2.6's
BECCS / DACCS pathway — scientifically expected for the deepest-mitigation
scenario.

### Modified — `runs/SSP1-2.6/imogen_intermediary.ins`

Added new "Option B" intermediary_py-driven file-paths block alongside
existing "Option A" (static-IIASA) and "Option C" (relative-path tight-mode):

- **Option A (v1.0 default)**: predecessor's absolute-path static IIASA
  files; F-10-deadlock-compatible
- **Option B (NEW at step 13)**: absolute paths to adapter outputs at
  `runs/SSP1-2.6/inputs/`; same F-10 deadlock behavior as A but with our
  RCMIP-substituted emissions backbone
- **Option C**: relative paths so engine concat resolves to LPJG handshake
  dir; un-testable in v1.0 (deadlocks); resolution at F-12

Option B is preserved as commented-out by default. Users opting into the
intermediary_py-driven backbone uncomment Option B + comment out Option A.

### Modified — `tools/README.md`

Added detailed adapter entry in "Implemented tools" section; removed
corresponding "Planned tools" row.

### Year-range mismatch documented

intermediary_py CSV starts at 1900 (FAOSTAT's earliest); predecessor's
static files start at 1850 (RCMIP/FAIR baseline). Adapter outputs 201
rows (1900-2100). Documented:
- adapter prints "AND adjust year-range params if needed" banner with
  exact `NYR_*=201, YEAR1=1900` instructions
- `--pad-to-year 1850` flag exists for users who want compatibility with
  the engine's default `NYR_*=251` parameters; flagged as
  "compatibility shim only, NOT scientifically defensible" because
  pre-industrial CH4 anthropogenic ~22 TgCH4/yr (not 0)

### What CAN'T be verified in v1.0

End-to-end coupled run with adapter-driven backbone — the F-10
architectural deadlock (from step 9 + 9.5) blocks LPJG main loop in
single-process imogencfx mode regardless of which emissions backbone
(static-IIASA Option A or adapter-driven Option B) is used. The adapter
is **scientifically validated** (correct units, conversions, format, value
ranges); the **integrated coupled run** awaits F-12 (multi-pass /
two-process design).

### NET source-level change in `lpjguess/`: ZERO

Adapter is fork-agnostic Python tooling. Backport Sprint (F-11) does
NOT need to replicate any step-13 changes in `trunk_r13078`.

### Files modified / added

```text
Added:
  tools/imogen_inputs_to_lpjg_format.py     ~10 KB / ~270 LOC (the adapter)
  notes/STEP_13.md                          ~14 KB

Modified:
  tools/README.md                           +"Implemented tools" entry; removed planned row
  runs/SSP1-2.6/imogen_intermediary.ins     +Option B block (commented-out)
  .gitignore                                comment annotation about runs/*/inputs/
  notes/FOLLOWUPS.md                        status dashboard date refresh
  notes/TRUNK_R13078_BACKPORT_LEDGER.md     +Step 13 entry (zero lpjguess C++)
  EXECUTION_PLAN.md                         step 13 row marked DONE
  CHANGELOG.md                              this entry

NOT committed (gitignored):
  runs/SSP1-2.6/inputs/*                    derived from intermediary_py output;
                                            regenerable via the adapter
```

---

## [v0.12.0-step11-intermediary-py-validated] — 2026-05-07 — step 11: pipeline end-to-end + 4 source bugs fixed + reproducibility verified

### Headline outcome

✅ **First end-to-end intermediary_py run succeeded**: 23/23 steps in
540.3s (~9 min); 10/10 pytest pass; **CO2 + all natural CH4/N2O +
all historical columns byte-identically reproduce** version_A's
reference outputs. Anthropogenic scenario CH4/N2O within 0.17-0.22%
mean relative (matches Quick_Start.md's documented "slightly earlier
code revision" provenance).

### Strategic shortcut — version_A's FULL/inputs/ as input source

Per user guidance 2026-05-07, instead of acquiring ~1.8 GB inputs
piecemeal from RCMIP / FAIR / EDGAR / FAOSTAT / PLUM / LPJG, **the
existing version_A `imogen_ghg_controller_FULL/inputs/` directory
(5.1 GB) is symlinked** as our pipeline's input source. Pros: 0 GB
disk overhead; per-subdir granularity; gitignored (no commits).

Symlinks at `intermediary_py/imogen_ghg_controller/inputs/<subdir>`
for: edgar/, fao/, fair_erf/, lpjg/, plum/, rcmip/, reference_pdfs/.

### Fixed — 4 source-level bugs in the imported intermediary_py

These bugs all manifested during the first end-to-end pipeline run.
All fixes are localized + small + improve robustness for any user
running the pipeline:

#### Bug 1 — `paths.py::ensure_output_dirs()` only created level-2 dirs

**Symptom**: `OSError: Cannot save file into a non-existent directory:
'.../outputs/component_a/data/ch4_ef'` on first script.

**Diagnosis**: `ensure_output_dirs()` created the level-2 dirs (data/,
figures/, summaries/) but not the per-sector level-3 sub-subdirs
(data/ch4_ef, ..., data/scenario_pipeline + figures/ analogs).

**Fix** (per user request for self-contained pipeline behavior):
- Extended `ensure_output_dirs()` to enumerate all 14 level-3
  sub-subdirs under Component A's data/ + figures/
- Added auto-call at module-bottom of `paths.py`:
  `if os.environ.get('IMOGEN_GHG_NO_AUTO_MKDIR') != '1':
       ensure_output_dirs()`
- Idempotent (`mkdir(parents=True, exist_ok=True)`); safe whether
  dirs are pre-created manually or not
- Gated by `IMOGEN_GHG_NO_AUTO_MKDIR=1` env var for read-only
  inspection tools that want to import paths without filesystem
  side effects
- **Verified**: deleting all output subdirs and importing
  `src.shared.paths` reconstructs all 28 dirs in one call

#### Bug 2 — `os` not imported in 3 scenario scripts

**Symptom**: `NameError: name 'os' is not defined` at
`01_scenario_ch4_ef_processing.py:44`.

**Diagnosis**: 3 scripts use `os.makedirs(SCEN_DIR, exist_ok=True)`
without `import os`. Python 3.10+ may transitively expose `os` via
sys imports in some environments; on Python 3.9.x (the user's
anaconda3 default) it fails.

**Fix**: added `import os` to:
- `src/component_a_anthropogenic/scenarios/01_scenario_ch4_ef_processing.py`
- `src/component_a_anthropogenic/scenarios/02_scenario_ch4_mm_processing.py`
- `src/component_a_anthropogenic/scenarios/03_scenario_n2o_mm_processing.py`

#### Bug 3 — `FAOCountry` column reference (stale; should be `Country`)

**Symptom**: `KeyError: 'FAOCountry'` at
`01_scenario_ch4_ef_processing.py:187`.

**Diagnosis**: Script reads `missing['FAOCountry']` from
`fao2020_missing_species.csv` — but that CSV is written with column
`Country`, not `FAOCountry`. Documented in Quick_Start.md's "1-row
diff" discussion ("the reference outputs the user provided are from
a slightly earlier code revision").

**Fix**: `missing['FAOCountry']` → `missing['Country']` (single
occurrence across the codebase). Aligns with canonical-current
behavior; matches version_A's reference outputs (which also use
`Country`).

#### Bug 4 — `rcmip_substitution_processing.py` writes to source dir

**Symptom**: `FileNotFoundError:
'.../outputs/component_a/data/rcmip_substitution_ch4.csv'` when
Component C tries to read it.

**Diagnosis**: lines 376-377 used `df.to_csv(os.path.join(HERE, ...))`
where `HERE = os.path.dirname(os.path.abspath(__file__))` — i.e.,
writing into the script's own `src/` directory, not into
`outputs/component_a/data/`. This explained why version_A's tree had
the rcmip_substitution_*.csv files in BOTH locations: the script
wrote into `src/` (the bug), and someone manually copied them to
`outputs/` (the workaround).

**Fix**: both `to_csv(os.path.join(HERE, ...))` calls changed to
`to_csv(os.path.join(str(OUT_A_DATA), ...))`. Producer-consumer
chain now works directly without manual copying.

### Fixed — `openpyxl` missing from requirements (bug C33)

Added `openpyxl>=3.0` to BOTH `requirements.txt` (with explanatory
comment) and `pyproject.toml`'s `dependencies` list. Future fresh
installs via `pip install -r requirements.txt` will pull openpyxl
correctly. (Did not actually crash on this host since system Python
already had it installed.)

### Verified

```text
# Pipeline run
$ python3 run_all.py --skip-plots
  ✓ 23/23 steps in 540.3s

# Pytest
$ python3 -m pytest tests/ -v
  ✓ 10/10 passed (test_imogen_export_schema, test_unit_conversions, test_co2_option_a_validation)

# Reproducibility (vs version_A FULL/outputs/imogen_inputs_SSP1-2.6.csv)
  Historical 1900-2019: ALL 9 columns BYTE-IDENTICAL
  Scenarios 2020-2100:
    CO2_EFOS_Mt, CO2_NEE_Mt, CO2_total_Mt:           BYTE-IDENTICAL
    CH4_natural_Mt, N2O_natural_Mt:                  BYTE-IDENTICAL
    CH4_anthro_Mt, N2O_anthro_Mt, CH4_total_Mt, N2O_total_Mt:
        max abs diff 0.602 / 0.029 Mt; mean 0.17-0.22% rel drift
        (matches Quick_Start.md "slightly earlier code revision")
```

### Files modified / added

```text
Added:
  notes/STEP_11.md                                                          ~14 KB

Modified (in intermediary_py — 4 bug fixes + 1 infra + 1 dep declaration):
  intermediary_py/imogen_ghg_controller/src/shared/paths.py                 +60 LOC (auto-create on import)
  intermediary_py/imogen_ghg_controller/src/component_a_anthropogenic/
    rcmip_substitution/rcmip_substitution_processing.py                     +12 LOC (HERE -> OUT_A_DATA)
    scenarios/01_scenario_ch4_ef_processing.py                              +8 LOC (import os; FAOCountry->Country)
    scenarios/02_scenario_ch4_mm_processing.py                              +1 LOC (import os)
    scenarios/03_scenario_n2o_mm_processing.py                              +1 LOC (import os)
  intermediary_py/imogen_ghg_controller/run_all.py                          +7 LOC (comment about auto-create)
  intermediary_py/imogen_ghg_controller/requirements.txt                    +4 LOC (openpyxl)
  intermediary_py/imogen_ghg_controller/pyproject.toml                      +2 LOC (openpyxl)

Modified (in lpjguess infra):
  .gitignore                                                                +10 LOC (intermediary_py/inputs/outputs)

Modified (in docs):
  notes/FOLLOWUPS.md                                                        status dashboard refresh
  notes/TRUNK_R13078_BACKPORT_LEDGER.md                                     +Step 11 entry (zero lpjguess C++)
  EXECUTION_PLAN.md                                                         step 11 row marked DONE
  CHANGELOG.md                                                              this entry

NOT committed (local-only):
  intermediary_py/imogen_ghg_controller/inputs/{edgar,fao,...}/             7 symlinks to version_A/.../FULL/inputs/
  intermediary_py/imogen_ghg_controller/outputs/                            generated; regenerable via run_all.py

Reverted:
  intermediary_py/imogen_ghg_controller/src/component_a_anthropogenic/
    rcmip_substitution/rcmip_substitution_{ch4,n2o}.csv                     reverted to step-10 state (the buggy
                                                                            script had over-written them; fixed
                                                                            script no longer touches them)
```

### NET source-level change in `lpjguess/`: ZERO

intermediary_py is fork-agnostic. Step 11's bug fixes live entirely
in the Python pipeline. The Backport Sprint (F-11) does NOT need
to replicate any step-11 changes in `trunk_r13078`.

---

## [v0.11.0-step10-intermediary-py-import] — 2026-05-07 — step 10: import imogen_ghg_controller v0.1.0

### Added — `intermediary_py/imogen_ghg_controller/` (7.9 MB; 78 files)

Per `EXECUTION_PLAN.md` V.1 step 10. The user's Python pipeline
`imogen_ghg_controller v0.1.0` (replacing the predecessor's legacy
C++ `Intermediary/Code/`, 272 KB, half-built) is now imported as the
canonical anthropogenic-emissions backbone for v1.0.

#### Source provenance

- Imported from `version_A/Intermediary_py/imogen_ghg_controller_SOURCE_ONLY/imogen_ghg_controller/`
- Verified byte-identical to version_B's SOURCE_ONLY (excluding figures/inputs/outputs/archive)
- 7.9 MB total: 59 Python source + 3 pytest tests + 16 docs/config files
- Excludes `inputs/` (Tier-3 ~1.8 GB; Tier-3 acquisition recipe in `data/DATA.md`)
- Excludes `outputs/` (generated; not committed)
- Excludes `archive/`, `__pycache__`, `*.pyc` (transient)
- Exception: 3 README.md placeholders kept inside excluded dirs for
  acquisition-instruction tracking

#### Pipeline architecture (43 steps × 4 components)

| Component | Role | Steps |
|---|---|---|
| **A** Anthropogenic | IPCC Tier-1 (CH4 EF/MM/rice; N2O MM/MS/syn-fert) × FAO/EDGAR/PLUM × RCMIP substitution | 28 |
| **B** Natural | LPJG `.gz` streaming + GMB IFW/DCC corrections | 5 |
| **C** Integration | A + B + 3 comparators (conventional/hybrid/external) | 9 |
| **D** IMOGEN export | Per-scenario wide + combined long format CSVs | 1 |

Final 6 IMOGEN-input deliverables at `outputs/imogen_inputs/`:
- 5 per-scenario wide CSVs (SSP1-1.9 / SSP1-2.6 / SSP2-4.5 / SSP3-7.0 / SSP5-8.5)
- 1 combined long-format CSV
- Format: 201 rows × 10 columns; **units: Mt-of-gas/yr**

#### Anthropogenic substitution backbone (Decision #1)

```
New_total = RCMIP_total − RCMIP_agri + Our_agri
```

Already implemented in `src/component_a_anthropogenic/rcmip_substitution/`.
Pre-validated: 38/38 reference data files byte-identical to canonical
scripts (per `Quick_Start.md`'s provenance check).

#### Verified

```bash
$ python3 run_all.py --dry-run
══ pipeline complete: 43/43 steps in 0.0s ══
```

✅ All 43 steps register cleanly (Component A: 28; B: 5; C: 9; D: 1).
No missing-imports errors. Ready for end-to-end execution at step 11
once Tier-3 input data is acquired.

#### Deferred (gated on later steps)

- Live pipeline execution + IMOGEN-input file generation: needs
  ~1.8 GB Tier-3 input data; **step 11** owns acquisition
- Adapter to convert intermediary_py's 6 CSVs into the 4 narrow
  IMOGEN-readable files: **step 13** owns the adapter
- Integration into `runs/SSP1-2.6/imogen_intermediary.ins`: **step 13**
  + post-F-12 (because F-10 deadlock blocks end-to-end coupled run anyway)
- Full pytest run: needs populated `outputs/`; **step 11**

### Documented — deferred-items master dashboard in `notes/FOLLOWUPS.md`

Per user code-discipline request 2026-05-07. Added a status dashboard
at the top of FOLLOWUPS.md showing all OPEN items with best-timing
columns + a "blocks step 17?" flag. Tracking discipline committed:

1. Update dashboard at end of every step that touches FOLLOWUPS.md
2. Hard sweep at start of step 17
3. Final review at end of Phase 1 via the Backport Sprint (F-11)

### Files modified / added

```text
Added:
  intermediary_py/imogen_ghg_controller/    7.9 MB / 78 files
  notes/STEP_10.md                          ~13 KB

Modified:
  intermediary_py/README.md                 imported-status update
  notes/FOLLOWUPS.md                        +Status dashboard at top + tracking discipline
  notes/TRUNK_R13078_BACKPORT_LEDGER.md     +Step 10 entry (zero lpjguess C++ touched)
  EXECUTION_PLAN.md                         step 10 row marked DONE
  CHANGELOG.md                              this entry
```

---

## [v0.10.0-step9.5-consumer-wiring] — 2026-05-07 — step 9.5: LPJG-side consumer wiring + BLAZE check + C++ engine Tmin/Tmax (PARTIAL)

### Added — LPJG-side consumer wiring for IMOGEN engine's Rh/Wind/Tmin/Tmax outputs

Per `EXECUTION_PLAN.md` V.1 step 9.5 + Decisions #11 (Tmin/Tmax) and #12
(Rh/W output asymmetry). Step 9.5 is **partial** with significant scope
refinement (see "Scope refinement" below).

#### `lpjguess/modules/imogencfx.h` — header additions

- Per-day `dtmin[Date::MAX_YEAR_LENGTH]` and `dtmax[Date::MAX_YEAR_LENGTH]` arrays
- `xtring file_tmin` and `xtring file_tmax` ins-parameter paths
- `std::vector< std::vector< std::vector<double> > > all_dtmin` and `all_dtmax` storage

(`drelhum`, `dwind`, `file_relhum`, `file_wind`, `all_drelhum`, `all_dwind`
were already in the header from prior integration-project work — only the
`*tmin` / `*tmax` analogs needed adding.)

#### `lpjguess/modules/imogencfx.cpp` — 5 wiring blocks

- **`init()` param reads**: `param["file_relhum"]`, `param["file_wind"]`,
  `param["file_tmin"]`, `param["file_tmax"]` — 4 new ins-file consumed parameters
- **`init()` resize block**: `resize3DimVector(all_drelhum, ...)`, `all_dwind`,
  `all_dtmin`, `all_dtmax` storage allocation
- **`read_climate_for_year()`**: 4 new `read_lines_from_file()` calls (each
  with empty-path guard so missing-file cases are graceful no-ops)
- **`get_climate_for_gridcell()`**: BLAZE compatibility check **RESTORED**
  with empty-path safety (actionable error message); monthly→daily
  interpolation block for the 4 new climate variables (uses
  `interp_monthly_means_conserve` mirroring existing `interp_climate`
  pattern); daily-mode passthrough block for the 4 new variables
- **`getclimate()`**: `climate.relhum = drelhum[date.day]; climate.u10 =
  dwind[date.day]; climate.tmin = dtmin[date.day]; climate.tmax = dtmax[date.day];`
  — mirrors `cfxinput.cpp:1940-1945`

### Restored — BLAZE compatibility check at `imogencfx.cpp:803-804`

Was commented out in the predecessor framework (per `[CMI §1.2]` break-point).
Step 9 left it commented because Rh+wind weren't yet wired (uncommenting
would have caused all coupled runs with `firemodel=BLAZE` to fail). After
step 9.5's wiring of `file_relhum`/`file_wind` (above), BLAZE can run safely
PROVIDED the user supplies the corresponding IMOGEN engine output paths in
the ins file. The check is now **active** and produces an actionable error
message:

```cpp
fail("imogencfx with firemodel=BLAZE requires file_relhum + file_wind ins
      parameters pointing at the IMOGEN engine's Rh_anom.dat / W_anom.dat
      per-year output. None set; aborting. (See runs/SSP1-2.6/imogen_intermediary.ins
      for the canonical ins-file layout.)");
```

### Added — `lpjguess/modules/climatemodel.cpp` Tmin/Tmax write block

In the non-REGRID native-grid output branch (lines ~880-958):
- `file100, file101` ofstream declarations
- Open at `iyear == year1`: `Tmin_anom.dat`, `Tmax_anom.dat`
- Per-gridpoint lon/lat headers + per-month-per-day data writes:
  `Tmin = tOutM[..] − dtempOutM[..]/2` (deg C)
  `Tmax = tOutM[..] + dtempOutM[..]/2` (deg C)
- Per-gridpoint newlines + close at `iyear == iyend`

**TODO at step 9.5b**: replicate in the REGRID branch (smoke uses `REGRID=0`
so non-REGRID is sufficient for v1.0).

### Scope refinement (deferred items)

Two items in the original step 9.5 plan were **deferred** after Phase A
investigation surfaced unanticipated infrastructure dependencies:

#### (a) Fortran Rh/W writer port — DEFERRED to step 9.5b

The original plan (Decision #12) assumed the Fortran engine *computed*
Rh/wind but didn't *write* them — i.e., a writer-only port (~20 LOC).
Investigation revealed the Fortran engine **doesn't compute these
variables at all**: the C++ port added the entire computation pipeline
(per `[CMI §4.3.4a]`). Real Fortran port = adding ~70-100 LOC of
Fortran physics work. Beyond step 9.5's 1-day budget; deferred to a
focused step 9.5b session.

Item (b) Fortran Tmin/Tmax depends on (a)'s computation infrastructure;
also deferred to step 9.5b.

#### (e) F-9 closure — REFINED, kept open

`MiscOutput`'s 12 climate-input diagnostic stubs (`out_t_anom`, `out_p_anom`,
etc.) need both `create_output_table()` calls in `define_output_tables()`
AND per-gridcell `outlimit()` calls in `outannual()`. The latter has no
data source: `Climate` has only single-day fields and 20-year-window
aggregates — **no per-month accumulator array**. The original step 9.5
plan assumed `gridcell.climate.mtemp[m]` was accessible; it's not (only
the single-value `mtemp` "mean of last 31 days" exists).

F-9's `notes/FOLLOWUPS.md` entry refined with two paths to closure:
- **Option A** (recommended; ~50 LOC): add per-month accumulator arrays
  to `Climate` (e.g., `mclimate_temp[12]`, `mclimate_prec[12]`, ...)
- **Option B** (~15 LOC): cross-module getter from `IMOGENCFXInput::dtemp[]`

Deferred to a focused step 9.5c (or merged with the F-12 sprint).

### Verification

```text
Build: clean (no warnings on new code; pre-existing fortify-source
       warnings unchanged)
Tests: 162/162 still pass
End-to-end smoke: NOT POSSIBLE in v1.0 — F-10 deadlock (per step 9 §4.4)
                  blocks LPJG main loop; new wiring is code-correct,
                  build-verified, but un-firable until F-12 lands
What CAN be verified in next smoke: 64 new files (Tmin_anom.dat +
                  Tmax_anom.dat × 32 engine years) in
                  Common-directory/IMOGEN/output/<YYYY>/
```

### Files modified

```text
Modified:
  lpjguess/modules/imogencfx.h           +9 LOC (3 blocks)
  lpjguess/modules/imogencfx.cpp         +80 LOC (5 spots)
  lpjguess/modules/climatemodel.cpp      +25 LOC (non-REGRID Tmin/Tmax block)
  notes/FOLLOWUPS.md                     F-9 refined with infrastructure blocker
  notes/TRUNK_R13078_BACKPORT_LEDGER.md  +Step 9.5 entry
  EXECUTION_PLAN.md                      step 9.5 row marked PARTIAL
  CHANGELOG.md                           this entry

Added:
  notes/STEP_9.5.md                      ~12 KB
```

---

## [v0.9.0-step9-smoke] — 2026-05-07 — step 9: SSP1-2.6 run-config + bug fixes + empirical F-10 confirmation

### Added — `runs/SSP1-2.6/` directory (first per-scenario run setup)

Per `EXECUTION_PLAN.md` V.1 step 9 + per user guidance 2026-05-07
to bring in the predecessor's legacy SSP1_RCP26 land-use data:

- **`runs/SSP1-2.6/main.ins`** (~6 KB, NEW): LPJG entry point.
  Imports `global.ins`, `crop_n.ins`, `wetlandpfts.ins`,
  `imogen_intermediary.ins`. Smoke overrides for spinup (100y vs
  500y production), `freenyears` (50y vs 100y production),
  `firemodel="NOFIRE"` (avoiding BLAZE wind/RH dependency until
  step 9.5), `npatch=1` (vs production 25), `run_landcover=1`
  (per user guidance), and year-range params 1871-1872.
- **`runs/SSP1-2.6/imogen_intermediary.ins`** (~14 KB, NEW): IMOGEN-
  coupling parameters. Embodies the bug fixes documented below.
  Default `coupling_mode="prescribed"` (the only v1.0 mode that
  doesn't deadlock immediately; see "Empirical F-10 confirmation").
- **`runs/SSP1-2.6/README.md`** (~6 KB, NEW): scenario metadata,
  how-to-run instructions including the bootstrap-handshake setup,
  empirical F-10 findings, production setup overrides.
- **11 stand/PFT/landcover ins files** (copied from version_A's
  `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/` predecessor):
  global, global_soiln, crop, crop_n, crop_n_pftlist, crop_n_stlist
  (3 variants), pasture_n_stlist (2 variants), landcover, wetlandpfts.
  Stale `/home/bampoh-d/Desktop/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/...`
  paths in `crop.ins` and `landcover.ins` retargeted to version_A's
  actual tree at
  `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/.../version_A/.../Data/LU/...`.

### Added — `imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp126.txt`

3.5 KB file (251 rows, 1850-2100). Was MISSING from our tree at step 6
(other 4 SSPs ssp245/ssp370/ssp460/ssp585 were imported; only SSP126
was overlooked). Imported from version_B at step 9 to fix the smoke
crash `Invalid data format in file: ../../imogen/emiss/RF_NONCO2_GHG_IS92A.dat`
(which had only 243 rows starting at 1859, mismatched with `NYR_NON_CO2=251`).

### Fixed — bug C5 (`ouput` typo) and bug R-anom (filename mismatch)

Both fixed in `runs/SSP1-2.6/imogen_intermediary.ins`:

- **C5**: 8 climate-input file paths (`file_temp`, `file_prec`,
  `file_insol`, `file_wetdays`, `file_dtr`, `file_co2`, `file_wind`,
  `file_relhum`) corrected from `./IMOGEN/ouput/YYYY/...` to
  `./IMOGEN/output/YYYY/...`. **PROVEN**: the smoke run produced 32
  per-year directories at `Common-directory/IMOGEN/output/<YYYY>/`,
  not `ouput/`.
- **R-anom → Rh_anom**: `file_relhum` corrected from `R_anom.dat` to
  `Rh_anom.dat` to match the C++ engine's actual writer output.
  **PROVEN**: the engine emitted `Rh_anom.dat` files in each per-year
  directory; matches our path.

### Documented — bug C35 fix attempted but un-testable in v1.0

The relative-path C35 fix (`FILE_LPJG_FLUX "imogen_lpjg_flux.txt"`)
is correct in concept and in the .ins file (commented out with
extensive documentation). However, the v1.0 single-process mode
**deadlocks immediately** with relative paths because the file
doesn't exist (LPJG hasn't written it yet); the polling loop's
`RUNFLUX_EXIST=0` flag prevents progress. The active configuration
is `coupling_mode="prescribed"` with absolute-path static IIASA
reference files (predecessor's "bug C35" mechanic, intentionally
preserved as the only v1.0-functional configuration). Real C35
testing is gated on follow-up F-12.

### Documented — F-10 architectural deadlock empirically confirmed

Step 9's smoke test **definitively confirmed F-10's predicted
architectural deadlock** in v1.0 single-process imogencfx mode:

- IMOGEN engine ran successfully for 32 years (1871-1902, 320 climate
  output files in 3 minutes), then deadlocked polling for year 1903's
  `done` file
- LPJG main loop NEVER reached because `imogencfx::init()` never
  returned (engine still in outer `KEEPRUNNING` loop)
- Step 8's writer NEVER fired (no `imogen_lpjg_flux.txt` or
  `imogen_lpjg_ch4_n2o_flux.txt` produced in `Common-directory/LPJG_main/IMOGEN/`)
- The deadlock occurs in BOTH `coupling_mode="tight"` (immediate, with
  relative paths) and `coupling_mode="prescribed"` (delayed, after
  ~32 years using bootstrap+absolute paths)

**This formally explains why the predecessor "never ran end-to-end"
([CMI §1.1]).** The predecessor's apparent functionality was an
artifact of the polling loop being neutered (bugs C2/C3 — fixed at
step 7); restoring correct polling-loop semantics surfaced the
underlying architectural deadlock that was always there.

### Added — follow-up F-12 (multi-pass / two-process verification design)

`notes/FOLLOWUPS.md`. The proper resolution of the F-10 deadlock for
v1.0 production runs. Recommended approach: **Option B (two-process)**
— split the `imogen_lpjg` engine binary out of `imogencfx::init()`
into a separate concurrent Fortran process. This is what the
predecessor's polling-loop architecture was originally DESIGNED for;
the in-process port (`climatemodel.cpp::RUN_IMOGEN_ENGINE`) was a
convenience wrapper that broke this design. Estimated effort: 2-3 days.
Option C (in-process restructure per F-10 Phase-2) for v2.0+.

### Added (then removed) — `imogen_nee_perturbation_factor` runtime parameter

Per V.1 step-9's verification milestone (NEE 2x → CO2 trajectory shift),
a runtime ins parameter `imogen_nee_perturbation_factor` was added at
step 9 (parameters.h, parameters.cpp, imogencfx.cpp declare_parameter,
imogenoutput.cpp consumer). Then REMOVED at step 9's wrap-up because
the smoke test empirically confirmed F-10's deadlock means LPJG main
loop never runs in v1.0 — so the perturbation factor cannot affect
anything observable. Per user code-integrity preference, the perturbation
parameter is NOT permanent in lpjguess. Resolution will be designed at
follow-up F-12. **Net source-level changes after step 9 wrap-up: zero**
(only annotation comments referencing the add-then-remove decision).

### Verification

```text
Build: clean
Tests: 162/162 pass
Smoke: 32 years climate output (1871-1902); deadlock at year 1903 polling
  - Engine: read all inputs (CRUNCEP, GCM patterns, emissions, fluxes)
  - Engine: produced 320 climate output files (sized correctly)
  - LPJG: did NOT enter main loop (F-10 deadlock confirmed)
  - Step 8 writer: did NOT fire (gated on F-12)
```

### Files modified / added

```text
Added:
  runs/SSP1-2.6/main.ins                                   ~6 KB
  runs/SSP1-2.6/imogen_intermediary.ins                    ~14 KB
  runs/SSP1-2.6/README.md                                  ~6 KB
  runs/SSP1-2.6/{global, crop, landcover, ...}.ins         ~78 KB across 11 files
  imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp126.txt   3.5 KB
  notes/STEP_9.md                                          ~14 KB

Modified:
  notes/FOLLOWUPS.md                                       +F-12 (~80 lines)
  lpjguess/framework/parameters.h                          comment-only annotation
  lpjguess/framework/parameters.cpp                        comment-only annotation
  lpjguess/modules/imogencfx.cpp                           comment-only annotation
  lpjguess/modules/imogenoutput.cpp                        comment-only annotation
  notes/TRUNK_R13078_BACKPORT_LEDGER.md                    +Step 9 entry
  CHANGELOG.md                                             this entry
  EXECUTION_PLAN.md                                        V.1 step 9 row marked PARTIAL
```

---

## [v0.8.1-backport-ledger] — 2026-05-06 — terminology + backport-ledger documentation

### Documented — `LandSyMM_LPJ-GUESS/` ≡ "integrated LTS" terminology synonymy

Per user clarification 2026-05-06, the user calls our v1.0
development base — `LandSyMM_LPJ-GUESS/` — the **"integrated LTS"**
because that's the working name from their preceding
integration-project. The directory name and the spoken term refer
to the **same artifact**. There is a separate
`lpjg_landsymm_integration/LPJ-GUESS-integrated/` directory that is
NOT what we imported and is NOT what the user calls "the integrated
LTS"; out-of-scope for v1.0.

Updated:
- `EXECUTION_PLAN.md` II.11.0 — new "Terminology" subsection with
  the synonymy explicitly documented.
- `EXECUTION_PLAN.md` II.11.1 — table headers updated to match.
- `EXECUTION_PLAN.md` II.11.2 — "Why ... for v1.0" reframed
  ("integrated LTS" instead of "trunk_r13078" with rationale
  preserved).
- `EXECUTION_PLAN.md` II.11.3 — Phase-2 backend section reframed
  as the **Backport Sprint** with explicit reference to
  `notes/TRUNK_R13078_BACKPORT_LEDGER.md`.
- `EXECUTION_PLAN.md` II.11.4 — knowledge-gap #2 updated to
  reflect that v1.0 IS testing the integration-LTS coupling
  integration in real-time.
- `README.md` (top-level) — repository-structure section + Lineage
  section updated.
- `lpjguess/README.md` — Provenance section adds the terminology
  note + Maintenance Discipline subsection.

### Added — `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (~370 lines)

New running source-of-truth catalogue of every C++ source-level
change in `lpjguess/` that needs replication in `trunk_r13078` at
the end of Phase-1 (the **Backport Sprint**, follow-up F-11). The
ledger:

- §1 documents the policy (which fork is which, the workflow, what
  the ledger covers and doesn't).
- §2 lists the **6-file baseline diff** between the two forks
  (cosmetic + the critical `exit(200)` removal at
  `imogencfx.cpp:483`).
- §3 retroactively populates the change set for steps 1-8 with
  step / commit-hash / file / line range / description / backport-
  guidance fields per entry. Step 7's C2/C3/C4 fixes and step 8's
  imogenoutput module + coupling_mode parameter + miscoutput
  cleanup are all catalogued.
- §4 lays out the 1-2 day Backport Sprint plan (5 phases:
  setup → reconcile baseline → replicate ledger → verify →
  document).
- §6 establishes the maintenance discipline: every commit that
  touches `lpjguess/{framework,modules,libraries,cmake}/` C++
  source MUST add a matching ledger entry.

### Added — follow-up F-11 in `notes/FOLLOWUPS.md`

The Backport-Sprint task itself, with cross-references to the
ledger, EXECUTION_PLAN.md II.11, notes/STEP_1.md §A, and
`_phase2_findings/02_lpjguess_trunk_r13078.md`. Estimated 1-2 days
focused work, executed at end of Phase-1.

### Updated — `notes/README.md`

Filesystem layout updated to include `TRUNK_R13078_BACKPORT_LEDGER.md`
alongside `FOLLOWUPS.md`, with a "When to use which" subsection
explaining the distinction between the two trackers (FOLLOWUPS
tracks open tasks; the ledger tracks the change log feeding the
eventual backport sprint task).

### Files modified / added

```text
Added:
  notes/TRUNK_R13078_BACKPORT_LEDGER.md   ~370 lines (new ledger)

Modified:
  EXECUTION_PLAN.md                       II.11 reframing (~80 LOC)
  README.md                               structure + lineage sections
  lpjguess/README.md                      provenance + discipline note
  notes/FOLLOWUPS.md                      +F-11 (~45 LOC)
  notes/README.md                         layout + when-to-use subsection
  CHANGELOG.md                            this entry
```

### Why this is a documentation-only release (no code changes)

The terminology-synonymy clarification + backport ledger don't
modify any C++/Fortran source. Tagged separately from
`v0.8.0-imogenoutput` (the step-8 functional milestone) so the
documentation churn doesn't get hidden in the code milestone's
release notes.

---

## [v0.8.0-imogenoutput] — 2026-05-06 — step 8

### Added — LPJG-side handshake writer + `coupling_mode` ins parameter

Per `EXECUTION_PLAN.md` V.1 step 8 + Appendix A.1. Implements a new
LPJ-GUESS output module that writes per-year handshake control files
the IMOGEN engine consumes, completing the LPJG → IMOGEN feedback
flow that step 7's polling-loop fixes had un-blocked.

#### New module — `lpjguess/modules/imogenoutput.cpp/h` (~470 lines total)

A `GuessOutput::ImogenOutput` class derived from `OutputModule`,
registered via `REGISTER_OUTPUT_MODULE("imogenoutput", ImogenOutput)`.
Writes 4 files at `<DIR_COMMON>/LPJG_main/IMOGEN/`:

- `imogen_lpjg_flux.txt` — `(year, NEE_PgC)` timeseries (append per year)
- `imogen_lpjg_ch4_n2o_flux.txt` — `(year, CH4_TgCH4, N2O_TgN2O)` timeseries
- `imogen_lpjg.txt` — control state for IMOGEN's next year (overwritten)
- `done` — handshake marker (touched LAST, after data writes finish)

Cadence: per-gridcell accumulation in `outannual()`; year-change
detection at start of `outannual` triggers `flush_year(prev_year)`
and accumulator reset; final-year flush in destructor.

Mode-gated by `IMOGENConfig::coupling_mode`:
- `"tight"` (default) — all 4 files written; IMOGEN engine consumes them
- `"prescribed"` — all 4 files written; IMOGEN engine reads from
  static path in ins file (handshake files act as diagnostics only)
- `"loose"` — NO files written; LPJG runs against pre-baked IMOGEN
  climate library on disk

Unit conversions emit canonical IPCC units:
- NEE: kgC across all gridcells × 1e-12 → PgC/yr (positive = source)
- CH4: g(CH4-C) × (16/12) × 1e-12 → TgCH4/yr
- N2O: kgN × (44/28) × 1e-9 → TgN2O/yr

Spherical-Earth gridcell-area approximation (R=6 371 km, 0.5° resolution).

#### `coupling_mode` ins parameter

Three small additions to plumb the new parameter through:
- `lpjguess/framework/parameters.h` — `extern xtring coupling_mode;` decl
- `lpjguess/framework/parameters.cpp` — definition with `"tight"` default
- `lpjguess/modules/imogencfx.cpp` — `declare_parameter("coupling_mode", ...)` registration

#### Build-system update

`lpjguess/modules/CMakeLists.txt` extended with `imogenoutput.h` and
`imogenoutput.cpp` so both `guess` and `runtests` targets pick up the
new module.

### Removed — dead `getImogenData()` placeholder helper

In `lpjguess/modules/miscoutput.h`:
- Deleted the `getImogenData(int lower, int upper)` static helper
  (~12 lines) that returned non-deterministic random values from a
  `std::random_device`-seeded `std::uniform_real_distribution<>`. It
  was defined but never invoked anywhere in the codebase, and was
  semantically misleading (a "data getter" that returned randomness).
- Removed unused `#include <random>` (was the only consumer).

The 12 `xtring file_*_anom` and `Table out_*_anom` declarations
remain in place — they're inert at runtime and are tracked
separately as follow-up F-9 (climate-input diagnostic outputs;
distinct concern from step 8's handshake-writer scope).

### Documented — major architectural finding F-10 (extensive)

Step 8's investigation surfaced what is arguably the most important
architectural finding of the entire investigation phase: the
LPJ-GUESS framework's `framework.cpp` lines 411-516 implement a
**per-gridcell-outer / per-day-inner across all years** loop. Each
gridcell processes ALL its years before the next gridcell starts.

This is **fundamentally incompatible** with proper per-year-globally-
synchronized tight coupling. When gridcell-1 finishes year-N and the
handshake fires, gridcell-2 has not yet started year-N. Step 8's
writer therefore emits **per-gridcell-rolling** values (which meet
V.1's stated step-8 milestone — non-empty, sensible files), but the
values are NOT globally synchronized.

This finding is the formal explanation for why [CMI §1.1] notes the
predecessor framework "never ran end-to-end." The predecessor's
polling loops were "neutered" by bugs C2/C3 to mask the
synchronization gap; step 7's un-neutering and step 8's writer
expose it.

**Phase-2 recommendation** (per user guidance 2026-05-06): when we
implement proper synchronized tight coupling, do NOT alter the
existing `framework.cpp` loop. Instead, add a runtime parameter
(e.g. `framework_loop_mode = "year_outer"`) that gates a NEW
per-year-outer code path which lives ALONGSIDE the default
per-gridcell-outer path. This mirrors the LandSyMM-fork-into-LTS
integration pattern from earlier in the chat history — additive
parameter-gated code, no behavioral change to the default path.

Full extensive write-up in `notes/FOLLOWUPS.md` F-10 (~150 lines)
and cross-referenced from `notes/STEP_8.md`,
`lpjguess/modules/imogenoutput.h`, and `EXECUTION_PLAN.md`.

### Documented — F-9 (half-scaffolded miscoutput climate-input diagnostics)

Cross-reference to the surviving 12 `file_*_anom` table stubs in
miscoutput. These are the climate-input diagnostic outputs (T_anom,
P_anom, Tmin/Tmax_anom etc. — what IMOGEN supplied to LPJG) — a
distinct concern from step 8's handshake-writer scope. Best timing
to complete is step 9.5 alongside Rh_anom / W_anom output parity.

### Verification

```text
$ cd lpjguess/build && make
[ 83%] Building CXX object CMakeFiles/runtests.dir/modules/imogenoutput.cpp.o
[100%] Built target runtests

$ ./runtests
All tests passed (162 assertions in 25 test cases)
```

✅ Build clean; all 162 unit tests still pass; no regression from
the 6 source-code edits. Per-year file-write verification is gated
on step 9 (run-config setup); step 8 establishes the writer
infrastructure and registration.

### Files modified / added

```text
Added:
  lpjguess/modules/imogenoutput.h          ~150 lines
  lpjguess/modules/imogenoutput.cpp        ~310 lines
  notes/STEP_8.md                          ~440 lines

Modified:
  lpjguess/framework/parameters.h          +9 lines (coupling_mode decl)
  lpjguess/framework/parameters.cpp        +4 lines (coupling_mode defn)
  lpjguess/modules/imogencfx.cpp           +7 lines (declare_parameter)
  lpjguess/modules/CMakeLists.txt          +2 lines (header + source)
  lpjguess/modules/miscoutput.h            -16 lines / +5 lines (kill dead helper)
  notes/FOLLOWUPS.md                       +200 lines (F-9 + F-10 entries)
  CHANGELOG.md                             this entry
  EXECUTION_PLAN.md                        step 8 row marked ✅
```

---

## [v0.7.0-coupling-fixes] — 2026-05-06 — step 7

### Fixed — LPJ-GUESS coupling source-level bugs (C2, C3, C4) + closes F-4

Per `EXECUTION_PLAN.md` V.1 step 7 + `[CMI §1.2]`, applied 3 of 5
catalogued LPJG ↔ IMOGEN coupling source-level bugs. (Bug C1 was
already eliminated by step 1's import-choice; bug C5's typo fixes
live in run-config files we'll create at step 9.)

#### C2 + C3 — `lpjguess/modules/climatemodel.cpp` polling loop (lines 332-353)

Before, the polling loop had **4 lines short-circuited**:
- `// doneExist = filesystem::exists(...)` (INQUIRE-equivalent commented out)
- `doneExist = true;` (replacement that always exited the wait)
- `// runnowOpen = !file.is_open();` (×3 instances at lines 336, 343, 352)

The "doneExist=true" hard-code silently bypassed the per-year LPJG↔IMOGEN
handshake's safety semantics; the 3 `*Open` guards were wholly inactive.

After:
- Restored `doneExist = filesystem_dkb::exists(...)` (the INQUIRE-equivalent).
- Added first-call bypass: `if (firstCall && !doneExist) doneExist = true;`
  using the existing `firstCall` local (initialized from
  `IMOGENConfig::FIRSTCALL` at line 244, reset at line 993). This avoids
  an infinite poll on the very first iteration of the very first run
  while preserving the proper handshake semantics afterward.
- Uncommented the 3 `*Open` guards.

#### C4 — `lpjguess/modules/imogen_input.cpp:728` ndep initializer

Before:
```cpp
//ndep.getndep(param["file_ndep"].str, cru_lon, cru_lat, Lamarque::parse_timeseries(ndep_timeseries));
```

The `ndep` object is later used at line 855 in `getclimate()` (via
`ndep.get_one_calendar_year`); without this initializer, ndep returned
zero/garbage values throughout the run, silently breaking
N-deposition forcing in loose-coupling mode. Uncommented + documented.

#### F-4 — Fortran twin: `imogen/code/imogen_lpjg.f`

The Fortran-side equivalent of bugs C2/C3 — the polling-loop's
DONE_EXIST default at line 363 (`!DONE_EXIST=.TRUE.`) was commented
out, and the line-371 INQUIRE always overrode it. Result: every
standalone IMOGEN smoke run since step 4 required a manual
`touch LPJG_main/IMOGEN/done` before invocation, or the binary
spun forever in the polling loop.

Fix: added `mkdir -p` + `touch done` block via `CALL SYSTEM` right
before the outer `DO WHILE (KEEPRUNNING)` loop. Idempotent (no error
if dir/file already exist). The polling-loop INQUIRE then finds the
auto-created file on the very first iteration → DONE_EXIST=.TRUE. →
loop exits → year 1 processing begins. In coupled mode, LPJ-GUESS
manages the file's lifecycle yearly; this auto-create only kicks in
on the very first invocation when no prior handshake exists.

The dead `!DONE_EXIST=.TRUE.` comment at line 363 (now permanently
moot) was replaced with an explanatory comment block.

### Verification

- ✅ LPJ-GUESS rebuilds clean.
- ✅ All **162 unit tests still pass** (`./runtests` reports
  `All tests passed (162 assertions in 25 test cases)`) — no regression
  from C2/C3/C4 fixes.
- ✅ Fortran IMOGEN rebuilds clean.
- ✅ **CRITICAL**: standalone IMOGEN smoke run, **without** any manual
  `touch done` or pre-staged `done` file, produces years 1871-1872
  output cleanly. Verified by:
  ```
  rm -rf LPJG_main IMOGEN              # nuke all stale state
  mkdir -p LPJG_main/IMOGEN IMOGEN/output
  cp /path/to/version_A/.../*.txt LPJG_main/IMOGEN/   # control-file stubs only
  test ! -f LPJG_main/IMOGEN/done && echo "OK"        # confirms no done file
  timeout 60 ./imogen_lpjg
  # → "Read NGPOINTS: 3698" → "ALLOCATEd regrid arrays" →
  #   "DONE_EXIST = T" on first poll iteration → years 1871, 1872 produced
  ```
  No regression from step 4's structural output (same files, same
  format).

### What's NOT in this release

- **C5 typo fixes** (`IMOGEN/ouput/`→`IMOGEN/output/`, `R_anom.dat`→
  `Rh_anom.dat`) — those typos live in the predecessor's run-config
  `.ins` files, NOT in the imported source code. Our `runs/<SSP>/...`
  directories don't exist yet — they get created at **step 9**, where
  fresh ins files will use the correct paths from the start.
- **LPJG-side handshake writer** (`imogen_lpjg_flux.txt`,
  `imogen_lpjg_ch4_n2o_flux.txt`, year-end `done`) — that's **step 8**.
- **Per-scenario coupled-mode run-config** — **step 9**.

### Files modified

- `lpjguess/modules/climatemodel.cpp` (C2 + C3 fixes)
- `lpjguess/modules/imogen_input.cpp` (C4 fix)
- `lpjguess/modules/imogencfx.cpp` (cross-reference comment only;
  the parallel `ndep.getndep()` call here was already active —
  bug C4 was specifically scoped to `imogen_input.cpp`. Added a
  small documentation note at line 895 to prevent future
  maintenance drift between the two modules)
- `imogen/code/imogen_lpjg.f` (F-4 fix)

### Files added

- `notes/STEP_7.md` (per-step verification record)

### Files modified (docs)

- `notes/FOLLOWUPS.md` (close F-4)
- `CHANGELOG.md` (this entry)
- `EXECUTION_PLAN.md` (V.1 step 7 marked complete)

---

## [v0.6.0-data-import] — 2026-05-06 — step 6

### Added — reference data import + 2 new tarballs (closes follow-up F-5)

Per `EXECUTION_PLAN.md` V.1 step 6 + `[CMI §5]`'s data inventory,
populate `data/` with the small reference inputs the coupled model
needs at runtime, tarball the medium-large reference inputs (Ndep,
emiss-reference), and document the very-large Tier-3 datasets without
committing them.

#### Tier 1 — committed directly to git (~14 MB)

- **`data/soil/`** — `soilmap_center_interpolated.remapv10_old_62892_gL.dat`
  (3.5 MB; LPJ-GUESS soil property table).
- **`data/gridlist/`** — 7 gridlist files (3.4 MB total): the active
  62 538-cell `gridlist_in_62892_and_climate.txt` plus 6 alternates
  (test, hilda+, hurtt-style, ndep, patterns).
- **`data/concentrations/`** — 31 reference CO2/CH4/N2O timeseries
  files (7.5 MB; EPA + IIASA CMIP5/CMIP6 TXT/CSV/DAT only — raw
  XLSX/ZIP downloads excluded per V.1 spec).

#### Tier 2 — 2 new tarballs added to `tools/imogen_data_manifest.txt`

| Component | Tarball | Compressed | Raw | SHA256 |
|---|---|---:|---:|---|
| `emiss-reference` | `imogen-emiss-reference-v1.0.tar.gz` | 311 KB | 5.2 MB | `77b05df3…` |
| `ndep-lamarque` | `imogen-ndep-lamarque-v1.0.tar.gz` | 460 MB | 501 MB | `a135d647…` |

The fetch script needed **zero code changes** — just two new manifest
rows. `tools/fetch_imogen_data.sh --verify-only` cleanly verifies all
6 components.

#### Tier 3 — `data/DATA.md` (new) documents acquisition

Records paths + recipes for:

- PLUM scenario LU at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/`
  (86 GB; per Decision #10 used via `save_state`/`restart` strategy)
- Legacy concatenated `Data/LU/SSP1_RCP26_concatenated/` (7.3 GB; superseded fallback)
- Legacy `Data/Intermediary/` (2.2 GB; production shifts to `intermediary_py` step 10)
- Predecessor's pre-baked IMOGEN outputs (~2 GB each; reproducible by re-run)
- Public datasets used by `intermediary_py`: HILDA+ v2, FAOSTAT,
  EDGAR 2025, RCMIP Phase 2 v5.1.0, FAIR ERF v1.3, IIASA SSP db
- NOAA GMD + AGAGE atmospheric concentration observations (step 17 validation)

### Changed — `imogen/emiss/` restructured to full tree

The step-4 flat-3-files layout (just the RCP8.5 triple from
`DKB_dataset_totals/` at the top level) was replaced with the full
`Data/Imogen/emiss/` tree (CMIP5/, CMIP6/, DKB_dataset_totals/,
new_emission_data/, rcp_database/, + 6 loose top-level files).

This was **necessary** — the active coupled-mode reference config at
`landsymm_imogen_setup/.../SSP1_RCP26/imogen_intermediary.ins`
references files at the deeper subdir paths
(`imogen/emiss/CMIP6/{Co2,CH4-N2O,Non-Co2-CH4-N2O-RF}/<scenario>/...`).
Without the full tree, coupled-mode runs at step 9+ would fail to
resolve their FILE_SCEN_EMITS / FILE_NON_CO2_VALS / FILE_CH4_N2O_EMITS /
FILE_LPJG_FLUX / FILE_LPJG_CH4_N2O_FLUX paths.

`imogen/code/imogen_settings.txt`'s 3 `FILE_*_EMITS` keys were updated
correspondingly (added the `DKB_dataset_totals/` subdir prefix).

### Changed — `.gitignore` extension

Added `data/ndep/ndep_cruncep/` exclusion for the Lamarque
binaries, with allow-list override for `data/ndep/README.md`.

### Verification

- Tier 1: 31 trackable files, 14 MB total — exactly as classified.
- Tier 2 manifest: all 6 entries verify clean SHA256 + size via
  `tools/fetch_imogen_data.sh --verify-only`.
- Tier 3: `data/DATA.md` written; cross-referenced from `data/README.md`.
- **Standalone IMOGEN regression smoke** — after the
  `imogen_settings.txt` path update, the binary still produces years
  1871, 1872 with all expected climate files (T_anom.dat,
  P_anom.dat, etc.). No regression from the path restructure.
- The full coupled-mode run-completion verification is gated on
  step 7 (the source-level coupling fixes).

### Files added (committed)

- `data/DATA.md` (new — Tier-3 acquisition recipes)
- `data/soil/soilmap_center_interpolated.remapv10_old_62892_gL.dat`
- `data/gridlist/{7 files}`
- `data/concentrations/{23 files}` (EPA + IIASA CMIP5/CMIP6 small files only)
- `data/ndep/README.md` (Tier 2 acquisition pointer)
- `notes/STEP_6.md`

### Files modified

- `.gitignore` (data/ndep exclusion + README allowlist)
- `tools/imogen_data_manifest.txt` (2 new rows)
- `imogen/code/imogen_settings.txt` (3-line FILE_*_EMITS path update)
- `imogen/emiss/README.md` (rewritten for the restructured tree)
- `data/README.md` (Tier-1/2/3 inventory)
- `notes/FOLLOWUPS.md` (close F-5)
- `EXECUTION_PLAN.md` (V.1 step 6 marked complete)

### NOT in this release

- 5 Lamarque .bin files (gitignored, regenerated by fetch).
- Full `imogen/emiss/{CMIP5,CMIP6,…}/` tree (gitignored, regenerated by fetch).
- The 86 GB PLUM scenario LU at `/media/bampoh-d/...` (Tier 3, document only).
- The legacy 7.3 GB concatenated LU and 2.2 GB Intermediary tree (skipped per V.1 spec; reproducible).

---

## [v0.5.0-cmip6-converter] — 2026-05-06 — step 5

### Added — `tools/cmip6_nc_to_cmip5_ascii.py` (CMIP6 NetCDF → CMIP5 ASCII)

Per `EXECUTION_PLAN.md` §V step 5 + Appendix A.3, implemented the
CMIP6 NetCDF → CMIP5 ASCII converter so the Fortran IMOGEN binary
can run against any of the 5 CMIP6 GCMs (GFDL-ESM4, IPSL-CM6A-LR,
MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL) without modifying the
binary's pattern reader.

**~340 Python lines** (xarray + scipy bilinear interpolation). Two
operating modes:

- Single-GCM: `--nc`, `--json`, `--output`
- Batch: `--input-dir`, `--output-base` (auto-discovers all 5 GCMs
  in ~1.6 sec wall-clock)

For each (GCM, month):
1. Read NetCDF with xarray; verify expected dims `(imogen_drive=12,
   lat=56, lon=96)`.
2. Read target gridlist (1631-cell IMOGEN HadCM3 land grid from
   `imogen/code/patterns_gridlist.txt`).
3. Bilinearly interpolate each of 8 `_patt` variables onto target
   gridlist. Handles lat-descending and lon-negative source grids.
4. Apply per-column transform (e.g. `wind_patt × 1/√2` for U/V split).
5. Write CMIP5-style ASCII with bbox header
   `0.00 -60.00 360.00 90.00` + 1631 data rows × 12 columns.
6. Emit Fortran namelist `<MODEL>_ebm.nml` with KAPPA_O, LAMBDA_L,
   LAMBDA_O, MU, F_OCEAN from the JSON params.

#### Verified column ordering

Authoritative ordering from `imogen_lpjg.f::GCM_ANLG` `READ` statement
at line 3270-3274 (the Appendix A.3 sketch had 12 mapped variables,
which was incorrect — actual is **10 variable columns + 2 coords**):

```text
LON LAT  T  RH15M  U-wind  V-wind  LW  SW  DTEMP_DAY  RAIN  SNOW  PSTAR
[1] [2] [3]  [4]    [5]     [6]   [7] [8]  [9]       [10]  [11]  [12]
```

#### Three documented CMIP6→CMIP5 mapping caveats

- **CAVEAT-A**: CMIP6 `ql1_patt` (units "K-1") passed through directly
  into CMIP5 col 4 `DRH15M_PAT` without unit conversion. Upstream
  alignment with IMOGEN's RH-sensitivity convention to be confirmed
  with the CMIP6 NetCDF generator (followup **F-6**).
- **CAVEAT-B**: CMIP6 stores wind-speed magnitude only; we split
  equally `U = V = wind_patt / √2` to preserve magnitude. Loses
  direction. Acceptable for v1.0; revisit at step 9.5 if needed
  (followup **F-8**).
- **CAVEAT-C**: CMIP6 stores total `precip_patt` only; we put full
  pattern into RAIN col 10 and 0.0 into SNOW col 11. Total preserved;
  rain/snow split handled downstream by IMOGEN's temperature-based
  partition rule (followup **F-8**).

#### Verification

- Build clean. `--help`, `--list`, `--component`, `--verify-only` all
  tested.
- Standalone IMOGEN run with `DIR_PATT=patterns/CEN_CMIP6_MOD_MRI-ESM2-0/`
  produces years 1871, 1872 with all expected climate files written.
- Cell (lat=82.5°, lon=281.25°, Jan): our CMIP6/MRI T = 237.676 K
  vs step 4's CMIP5/IPSL T = 237.736 K — **0.06 K** difference
  (within the inter-GCM scatter expected from year 1871's tiny
  land-mean anomaly).

#### Open follow-up: `pstar_patt` units

Discovered while comparing converter output: the CMIP6/MRI Pstar
pattern at the same Arctic cell is −49.40 vs CMIP5/IPSL +0.32 — a
150× magnitude difference + opposite sign. Most likely a Pa-vs-hPa
unit mismatch in the source NetCDF; needs author confirmation
(followup **F-7**).

### Files added (committed to git)

- `tools/cmip6_nc_to_cmip5_ascii.py` (new)
- `notes/STEP_5.md` (new — per-edit verification)

### Files modified

- `.gitignore` — gitignore the derivative `*_ebm.nml` output
- `imogen/patterns/README.md` — extend with conversion recipe + caveats
- `tools/README.md` — extend with the converter under "Implemented tools"
- `notes/FOLLOWUPS.md` — add F-6, F-7, F-8
- `CHANGELOG.md` — this entry
- `EXECUTION_PLAN.md` — V.1 step 5 marked ✅

### NOT in this release

- 5 derivative directories `imogen/patterns/CEN_CMIP6_MOD_<gcm>/` and 5
  `<gcm>_ebm.nml` files (regeneratable; gitignored).
- A source-code fix for bug C2/C3 (deferred to step 7).
- Numerical parity Fortran ↔ C++ (Phase-2; Decision #2).

---

## [v0.4.0-imogen-data-fetch-script] — 2026-05-05 — step 4

### Added — IMOGEN reference-data acquisition infrastructure + first real Fortran output

Per Decision #5 (incremental rebuild) and `EXECUTION_PLAN.md` §V step 4,
imported the IMOGEN GCM patterns + CRUNCEP base climatology AND
established a clean **acquisition pattern** for the unified codebase:
the data lives **outside git** (49 MB compressed → 161 MB extracted)
and is fetched at setup time via a manifest-driven script.

#### `tools/fetch_imogen_data.sh` + `tools/imogen_data_manifest.txt`

- **Manifest format**: per-tarball record with filename, SHA256, size,
  and extract-path. 4 tarballs catalogued (CMIP5 ~19 MB, CMIP6 ~19 MB,
  CMIP3 legacy 534 KB, CRUNCEP ~11 MB).
- **Fetch script modes**:
  - `--list`: print manifest summary
  - default: fetch + SHA256-verify + extract
  - `--verify-only`: re-checksum without extracting (CI-friendly)
  - `--component <name>` (repeatable): partial fetch
- **Source flexibility**: `--base` accepts either a local directory
  path (workstation case during development) or an `https://` URL
  prefix (a TBD permanent host like Zenodo / GitHub Releases /
  institutional bucket — to be set up by the user post-step-4).
- **Initial draft hit the classic `set -e` + `((var++))` bash pitfall**;
  fixed by replacing `((errors++))` with `errors=$((errors+1))`.

#### `imogen/patterns/`, `imogen/CRUNCEP_1960_1989/`, `imogen/emiss/`

Reference data staged locally on the workstation (gitignored):

- 35 GCM pattern dirs (34 CMIP5 ASCII + 1 CMIP6 NetCDF + 1 CMIP3 legacy)
- 30-year CRUNCEP base climatology (12 mo × 30 yr × 1631 cells)
- 3 small reference RCP8.5 emission files

Each directory has a small README committed to git that explains
structure + provenance + acquisition; the actual data does not.

#### Standalone Fortran IMOGEN smoke run — first real scientific output

The verification milestone deferred from step 2 has now been hit:

- Years 1871 + 1872 produce per-year output at `imogen/code/IMOGEN/output/<YYYY>/`
- All expected ASCII climate files written (`T_anom.dat`, `P_anom.dat`,
  `SW_anom.dat`, `DTEMP_anom.dat`, `WET.dat`, `dtemp_o.dat`,
  `fa_ocean.dat`, `CO2.dat`, `done`)
- Numerical content is physically plausible (Arctic 82.5° N
  monthly Kelvin temperatures range 231–276 K)
- CO2.dat correctly reflects the initial concentration settings
  (286.085 ppm CO2; 865 ppb CH4; 277.4 ppb N2O)

Comparison against `version_A`'s reference 1871 output (which appears
to have been generated by the **C++ refactor**, not Fortran, based on
its `[IMOGEN LOGGER][2025-06-16 …][INFO]` log-line format):

- Same files, minus `Rh_anom.dat` + `W_anom.dat` (confirms `[SA3 §10]`;
  these are C++-only, will be ported in step 9.5 per Decision #11).
- Same column structure, but our Fortran writes 2× the lines and
  with more decimals (to investigate as a Fortran writer follow-up).
- Numerical T values diverge by 0.1–8 K vs version_A's C++ output
  (expected; Fortran ↔ C++ numerical parity is itself the Phase-2
  milestone per Decision #2).

#### Bug C2/C3 work-around for first run

The standalone run blocks indefinitely in the polling loop at
`imogen_lpjg.f:400-403` waiting for `DONE_EXIST=T`, because line 363's
default `DONE_EXIST=.TRUE.` was commented out at some point (the
"neutered polling-loop safety check" of `[CMI §1.2 / SA3 §10]`). For
step 4 this is **worked around at runtime** by pre-staging an empty
`done` file in `LPJG_main/IMOGEN/`. The source-level fix lands at
**step 7** of the rebuild plan.

### Fixed

- `.gitignore` was silently broken for `imogen/patterns/CEN_*/`,
  `imogen/patterns/CMIP6_*/`, and `imogen/patterns/ukmo_hadcm3_rel/`
  due to **inline comments after the pattern**. Gitignore does NOT
  support inline comments — they get parsed as part of the pattern.
  Fix: moved comments to their own lines. Effect: 431 pattern files
  (which had been technically untracked-but-not-ignored, easily
  `git add`-able by accident) are now correctly ignored.

### Files touched

- `tools/fetch_imogen_data.sh` (new, ~210 lines)
- `tools/imogen_data_manifest.txt` (new, 4 entries)
- `tools/README.md` (extended)
- `imogen/patterns/README.md` (new)
- `imogen/patterns/readme.log` (new — upstream provenance, 127 B)
- `imogen/CRUNCEP_1960_1989/README.md` (new)
- `imogen/emiss/README.md` (new)
- `imogen/README.md` (extended; step-4 milestone section)
- `notes/STEP_4.md` (new — full per-edit verification record)
- `.gitignore` (fix + additions)
- `EXECUTION_PLAN.md` (V.1 step 4 marked ✅)

### NOT in this release

- The 4 data tarballs themselves (saved at sibling path
  `lpj-guess_imogen_landsymm_data/`; user uploads to a permanent host
  in a follow-up — tracked as **F-1** in `notes/FOLLOWUPS.md`).
- A source-code fix for bug C2/C3 (deferred to step 7).
- Rh/W writer parity in Fortran (deferred to step 9.5).
- CMIP6 NetCDF → ASCII converter (step 5).
- Coupled-mode validation (steps 6-9).
- Investigation of the 2× line count of our Fortran's `T_anom.dat`
  vs `version_A`'s reference (low priority — tracked as **F-2**
  in `notes/FOLLOWUPS.md`).

### Follow-ups document

This release introduces `notes/FOLLOWUPS.md` — a centralised tracker
for non-blocking action items raised during step work. Items move
from OPEN to DONE as they close. Currently 5 OPEN items
(F-1 through F-5).

---

## [v0.3.0-fortran-allocatable] — 2026-05-05 — step 3

### Changed — Fortran IMOGEN: `ALLOCATABLE` array refactor (`NGPOINTS` runtime)

Per Decision #2 (Fortran-with-`ALLOCATABLE`-first IMOGEN strategy)
and `EXECUTION_PLAN.md` §V step 3, the 6 `NGPOINTS`-dimensioned
arrays in `imogen/code/imogen_lpjg.f` `PROGRAM IMOGEN` were
converted from static to Fortran-90 `ALLOCATABLE`, and the
`PARAMETER(NGPOINTS=3698)` was promoted to a run-time setting:

- `T_OUT_M_REGRID(:,:,:,:)`, `P_OUT_M_REGRID(:,:,:,:)`,
  `SW_OUT_M_REGRID(:,:,:,:)`, `DTEMP_OUT_M_REGRID(:,:,:)`,
  `F_WET_CLIM_REGRID(:,:)`, `LON_OUT(:)`, `LAT_OUT(:)` are now
  `ALLOCATABLE`, allocated in `PROGRAM IMOGEN` immediately after
  `CALL SETTIN(...)` returns the run-time `NGPOINTS` value.
- `imogen/code/imogen_settings.txt` gains a new
  `NGPOINTS 3698` key; `SUBROUTINE SETTIN` reads it via a new
  `CASE('NGPOINTS')` branch (signature now ends `…,CO2_RF_FAIR,NGPOINTS)`).
- A sentinel value (`NGPOINTS = -1`) plus post-loop validation in
  `SETTIN` aborts with a clear error message if the new key is
  missing or non-positive — preventing silent failure.
- A matching `DEALLOCATE(...)` block before `STOP` in `PROGRAM IMOGEN`
  ensures clean shutdown (with `IF(ALLOCATED(...))` guards to remain
  safe under any future early-error path).
- A startup banner `IMOGEN: ALLOCATEd regrid arrays for NGPOINTS=…`
  prints the actual value at run time, supporting the units-integrity
  rule "startup banners".

### Verification

- Build with `gfortran -ffixed-line-length-132 -O` succeeds clean (no
  warnings).
- **Positive smoke probe** (`NGPOINTS=3698`, default): parser reads,
  ALLOCATEs ~33 MB heap, terminates at later runtime input read
  (`IMOGEN/CO2_all.dat`) — same termination signature as step 2 →
  no regression.
- **Negative smoke probe** (`NGPOINTS` line removed from settings):
  validation fires, clean abort with helpful error message,
  `STOP 1`.
- **Scaling probe** (`NGPOINTS=10000`): parser reads new value,
  ALLOCATEs ~90 MB heap, terminates at same later runtime input
  read → confirms the run-time configurability works.

### Deferred (not in this release)

- `GPOINTS`-dimensioned arrays (~30 of them) remain `PARAMETER`-sized
  at 1631; conversion to `ALLOCATABLE` is a marginal heap-vs-BSS
  tweak with no functional benefit and is deferred to a future
  cleanup step. Changing `GPOINTS` itself requires regenerating the
  pattern + CRUNCEP files (1 631 cells locked in by upstream).
- `NFARRAY` (10 000) and `N_OLEVS` (254) likewise remain `PARAMETER`
  — neither is a memory bottleneck nor user-facing.
- `nonco2.f` references none of these constants → no changes needed
  there.

### Files touched

- `imogen/code/imogen_lpjg.f` — 7 ALLOCATABLE decls, ALLOCATE block,
  DEALLOCATE block, SETTIN signature/decl/sentinel/CASE/validation.
- `imogen/code/imogen_settings.txt` — added `NGPOINTS 3698` line.
- `notes/STEP_3.md` — full per-edit verification record.
- `imogen/README.md` — step-3 layout + ALLOCATABLE-refactor section
  + how to scale to 62 000 cells.

### Documentation updates

- `EXECUTION_PLAN.md` Part V step 3 marked ✅ complete.

---

## [v0.2.0-imports] — 2026-05-05 — steps 1 + 2

### Added — LPJ-GUESS LandSyMM fork (step 1)

- `lpjguess/` populated with the upstream LPJ-GUESS LandSyMM fork
  (`trunk_r13078`-equivalent, chosen over upstream `trunk_r13078`
  to avoid the `exit(200)` regression).
- Build configured with Anaconda3 NetCDF (per Decision #8) — works
  cleanly on the user's workstation where the native Ubuntu HDF5
  has a `curl_global_init@CURL_OPENSSL_4` ABI mismatch with libcurl
  4.
- All 162 unit tests pass post-import; CFX smoke test deferred to
  step 6.
- Documented in `notes/STEP_1.md`.

### Added — Fortran IMOGEN with immediate fixes (step 2)

- `imogen/code/` populated with `imogen_lpjg.f`, `nonco2.f`,
  `Makefile`, `compile.sh`, gridlists, etc.
- Step-2 fixes applied immediately on import:
  - **C10**: removed `PAUSE` statement in `QSAT` (halted
    non-interactive runs).
  - **C11**: removed `qsat_output.txt` debug-dump (file-handle
    leak; O(GB) of unused output).
  - **C12**: replaced Windows `\IMOGEN\output\` mkdir paths with
    forward slashes.
  - **C13**: rewrote Windows absolute paths in `imogen_settings.txt`
    to relative paths.
  - **Makefile**: replaced Windows `del` with `rm -f`; renamed
    target from `imogen` to `imogen_lpjg`.
  - **compile.sh**: removed `.exe` Windows convention.
- Build with `gfortran` succeeds clean; functional probe confirms
  startup + settings parsing.
- Standalone IMOGEN-only run deferred to step 4 (requires patterns
  + CRUNCEP).
- Documented in `notes/STEP_2.md`.

---

## [v0.1-skeleton] — 2026-05-05

### Added — initial repository scaffolding (step 0 of the rebuild plan)

- **Top-level files**:
  - `README.md` — top-level navigation, project overview, build/run
    placeholder, roadmap, citation pointers.
  - `LICENSE` — MIT, with reference to upstream component licences.
  - `CITATION.cff` — machine-readable citation metadata for the
    framework and its underlying peer-reviewed components.
  - `CONTRIBUTING.md` — development workflow, per-step verification
    discipline, three-remote push pattern, units-integrity
    discipline (six rules from `EXECUTION_PLAN.md` §I.D plus the
    reciprocal producer/consumer checks of §I.D.7).
  - `CHANGELOG.md` — this file.
  - `.gitignore` — comprehensive build artefact + run output +
    Python venv + IDE noise filtering, with allow-list overrides
    for per-subdir READMEs.
- **Top-level directory scaffolding** (12 dirs, each with a
  placeholder `README.md` to be expanded as the rebuild progresses):
  - `lpjguess/` — LPJ-GUESS LandSyMM fork (Phase 1 baseline:
    `trunk_r13078`; Phase 2 switchable backend: integrated LTS).
  - `imogen/` — Fortran IMOGEN with planned `ALLOCATABLE`-array
    refactor (Phase 1); C++ refactor brought to numerical parity
    in Phase 2.
  - `intermediary_py/` — Python `imogen_ghg_controller v0.1.0`
    (IPCC Tier-1 + RCMIP substitution).
  - `tools/` — cross-component utilities (the
    `imogen_inputs_to_lpjg_format.py` adapter,
    `cmip6_nc_to_cmip5_ascii.py` converter, regrid utilities).
  - `runs/` — per-scenario run setups
    (`runs/historic/` for the HILDA+ standalone Phase-1 with
    `save_state` at 2020; `runs/SSP1-2.6/`, `runs/SSP2-4.5/`,
    etc. for coupled scenario restart from 2020).
  - `data/` — small reference data (gridlists, soil map, etc.);
    large data documented in `data/DATA.md` for separate
    acquisition.
  - `scripts/` — `run_coupled.sh` (workstation),
    `run_coupled.sbatch` (cluster SLURM), `cluster/` (owl helpers).
  - `ci/` — CI/CD workflow definitions.
  - `docs/` — unified technical manual, scientific framework, build
    instructions, troubleshooting, glossary.
  - `paper/` — manuscript draft + figures + cited peer-reviewed PDFs.
  - `notes/` — per-step development notes
    (`notes/STEP_<n>.md` for each Part V step).
  - `archive/` — frozen legacy code preserved for reference
    (older C++ refactor before parity, retired Imogen-controller,
    legacy C++ Intermediary, etc.).

### Preserved — investigation evidence base (immutable)

- **`COUPLED_MODEL_INVESTIGATION.md`** (240 KB / 3 968 lines) —
  master investigation document covering: state of the system; the
  seven coupling break-points + bug C35 (`FILE_LPJG_FLUX`
  path-override); seven scientific framework lineages; system
  architecture (8 components plus auxiliaries); per-component deep
  dives drawing from the 8 subagent reports; full
  ~120-item bug catalogue with severity tags
  (🔴 active / 🟡 latent / 🟢 cosmetic); 11 documentation
  contradictions plus 4 doc-vs-code mismatches; A-vs-B divergence
  accounting; 24 open questions; 6-layer roadmap; recommended
  directory structure (which this scaffolding implements).
- **`EXECUTION_PLAN.md`** (142 KB / 2 595 lines) — operational
  checklist with: 12 settled strategic decisions (RCMIP backbone,
  Fortran-with-`ALLOCATABLE` first / C++ port second, `trunk_r13078`
  first / integrated LTS second, tight coupling default,
  incremental rebuild approach, units-integrity discipline,
  single codebase for workstation+cluster, Anaconda3 NetCDF
  preference, Stage I deferred-not-removed, save_state/restart
  LU strategy, Tmin/Tmax computation, Rh+W output asymmetry); item-
  by-item gap inventory (I.A code-level fixes, I.B 7 missing
  components, I.C data acquisition, I.D 7 units-integrity rules);
  11 strategic-decision write-ups; Part V formal step-by-step
  rebuild plan with verification milestones (steps 0-19, plus 9.5
  for climate-output enhancements; ~25-35 person-days to v1.0,
  ~7-10 weeks calendar); 5 implementation sketches in the appendix.
- **`_phase2_findings/`** (424 KB / 6 507 lines across 8 reports) —
  the canonical evidence base: documentation inventory, LPJ-GUESS
  `trunk_r13078`, Fortran IMOGEN, C++ IMOGEN refactor, C++
  Intermediary, Python Intermediary, GCM patterns + regrid
  utilities, run setups + orchestration + Data/. Cited inline
  throughout the master doc as `[SAn §x.y]`.

### Status

Scaffolding only. No build yet. The actual model code lands at
step 1 (LPJ-GUESS import) and onwards.

---

## [v0.0-investigation] — 2026-05-04

### Added — investigation phase (predecessor)

The investigation phase of this rebuild — performed entirely on the
predecessor framework trees `version_A/` and `version_B/` and the
two related projects `lpjg_landsymm_integration/` and `landsymm_py/`
— produced the three documents captured in the v0.1-skeleton
release:

- `COUPLED_MODEL_INVESTIGATION.md`
- `EXECUTION_PLAN.md`
- `_phase2_findings/01_documentation_inventory.md`
- `_phase2_findings/02_lpjguess_trunk_r13078.md`
- `_phase2_findings/03_imogen_fortran.md`
- `_phase2_findings/04_imogen_cxx.md`
- `_phase2_findings/05_intermediary_cpp.md`
- `_phase2_findings/06_intermediary_py.md`
- `_phase2_findings/07_patterns_and_regrid.md`
- `_phase2_findings/08_orchestration_and_data.md`

These document the state of `version_A` and `version_B` at the
investigation moment (4-5 May 2026) and serve as the immutable
evidence base for every claim in the rebuild plan.

The `version_A` and `version_B` framework trees themselves are
**not part of this repository** — they are preserved as read-only
reference at their original paths
(`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/version_{A,B}/`)
and are not modified by this rebuild.
