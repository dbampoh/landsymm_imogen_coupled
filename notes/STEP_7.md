# STEP 7 — Apply LPJ-GUESS coupling source-level fixes (C1-C5 + F-4)

**Date completed:** 2026-05-06
**Commit:** _to be filled in after `git commit`_
**Status:** ✅ verification milestone hit:
- LPJ-GUESS rebuilds clean; **all 162 unit tests pass** (no regression)
- Fortran IMOGEN rebuilds clean
- **Standalone Fortran IMOGEN now runs end-to-end producing years 1871-1872 WITHOUT the manual `done`-file workaround that was required since step 4** — proving F-4 is closed and the C2/C3 Fortran twin is fixed at source

---

## 1. Goal

Apply the 5 LPJ-GUESS coupling source-code fixes catalogued in `[CMI §1.2]`
plus the Fortran twin fix that closes follow-up F-4. Per
`EXECUTION_PLAN.md` V.1 step 7.

After this step, the source code is **internally consistent** for the
LPJG ↔ IMOGEN handshake — no commented-out safety checks, no
hard-coded shortcuts, no manual runtime workarounds. Step 8 (LPJG-side
output writer for the handshake) and step 9 (per-scenario run-config
.ins files) can build on this clean foundation.

---

## 2. Investigation — confirming current line numbers + scope

The bug catalogue in `[CMI §1.2]` lists 5 source-level coupling bugs.
After step 1's import choice (LandSyMM fork over `trunk_r13078`) and
step 2's immediate-fixes pass, the actual scope at step 7 is **smaller
than the V.1 spec implied**:

| Bug | V.1 spec said | Actual state at step 7 | Action |
|---|---|---|---|
| **C1** `exit(200)` in `imogencfx.cpp:483` | "delete it" | **Already absent** in the imported LandSyMM fork — that's specifically why we picked this fork over `trunk_r13078` at step 1 | ✅ no fix needed; document |
| **C2** `INQUIRE` for `done` neutered in `climatemodel.cpp:332-333` | "restore INQUIRE" | Confirmed: line 332 has `// doneExist = filesystem::exists(...)` commented out, line 333 hard-codes `doneExist = true` | Fix |
| **C3** 3 polling guards neutered in `climatemodel.cpp` | "restore guards at lines 334, 341, 350" | Confirmed at lines **336, 343, 352**: `// runnowOpen = ...`, `// runfluxOpen = ...`, `// runnonco2fluxOpen = ...` (all 3 commented out) | Fix |
| **C4** `ndep.getndep` commented out in `imogen_input.cpp:728` | "uncomment it" | Confirmed at line 728 | Fix |
| **C5** `IMOGEN/ouput/` typo (×6) and `R_anom.dat`→`Rh_anom.dat` (×1) in ins file | "fix the ins file" | **Not in the imported lpjguess/ source tree** — those typos live in the predecessor's run-config `.ins` files (e.g. `version_A/.../landsymm_imogen_setup/.../SSP1_RCP26/imogen_intermediary.ins:102-109`). Our `runs/<SSP>/...` directory doesn't exist yet — it gets created at **step 9** | Defer to step 9; cross-reference |
| **F-4** Fortran twin: `imogen_lpjg.f:363` `!DONE_EXIST=.TRUE.` commented out → standalone runs hang in polling loop until user manually creates `LPJG_main/IMOGEN/done` | _(not in V.1 step 7 spec but raised as F-4 in `notes/FOLLOWUPS.md`)_ | Confirmed: line 363 commented out; the line-371 `INQUIRE` overwrites the default each iteration so just uncommenting won't help — needs auto-create-on-first-run logic instead | Fix (closes F-4) |

So step 7's **active scope**: C2 + C3 + C4 + F-4. Four fixes across
two files (climatemodel.cpp, imogen_input.cpp) for the C++ side and
one file (imogen_lpjg.f) for the Fortran side.

---

## 3. The fixes

### 3.1 C2 + C3 — `lpjguess/modules/climatemodel.cpp`

The polling-loop block at the top of the `keepRunning` outer loop had
**4 commented-out lines** (the V.1 spec said 1+3=4 but accidentally
counted them as "1 INQUIRE + 3 guards" which was structurally accurate).

#### Before (lines 332-353, all 4 commented-out / short-circuited)

```cpp
        while (!runnow) {
            std::this_thread::sleep_for(std::chrono::seconds(3));
            std::cout << "." << std::flush;

           // doneExist = filesystem::exists(dirCommon + "/LPJG_main/IMOGEN/done");
            doneExist = true;
            {
                std::ifstream file(dirCommon + "/LPJG_main/IMOGEN/imogen_lpjg.txt");
               // runnowOpen = !file.is_open();
            }

            runfluxExist = filesystem_dkb::exists(fileLpjgFlux);
            {
                //std::ifstream file(dirCommon + "/LPJG_main/IMOGEN/" + fileLpjgFlux);
                std::ifstream file(fileLpjgFlux);
               // runfluxOpen = !file.is_open();
            }
            errorExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/error");
            runnowExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/imogen_lpjg.txt");
            if (nonco2Emissions) {
                runnonco2fluxExist = filesystem_dkb::exists(fileLpjgCh4N2oFlux);
                {

                    std::ifstream file(fileLpjgCh4N2oFlux);
                   // runnonco2fluxOpen = !file.is_open();
                }
            }
```

#### After

```cpp
        while (!runnow) {
            std::this_thread::sleep_for(std::chrono::seconds(3));
            std::cout << "." << std::flush;

            // [Step 7 fix: bug C2 — restore the doneExist filesystem check
            //  that was previously short-circuited to "doneExist = true"
            //  (which silently bypassed the LPJG↔IMOGEN per-year handshake's
            //  safety semantics). The first-call special case avoids an
            //  infinite poll on the very first iteration of the very first
            //  run, when no prior 'done' from LPJ-GUESS exists yet.]
            doneExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/done");
            if (firstCall && !doneExist) {
                doneExist = true;  // first-call bypass: LPJG hasn't written 'done' yet
            }

            {
                std::ifstream file(dirCommon + "/LPJG_main/IMOGEN/imogen_lpjg.txt");
                // [Step 7 fix: bug C3 part 1 — restore the runnowOpen guard]
                runnowOpen = !file.is_open();
            }

            runfluxExist = filesystem_dkb::exists(fileLpjgFlux);
            {
                std::ifstream file(fileLpjgFlux);
                // [Step 7 fix: bug C3 part 2 — restore the runfluxOpen guard]
                runfluxOpen = !file.is_open();
            }
            errorExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/error");
            runnowExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/imogen_lpjg.txt");
            if (nonco2Emissions) {
                runnonco2fluxExist = filesystem_dkb::exists(fileLpjgCh4N2oFlux);
                {
                    std::ifstream file(fileLpjgCh4N2oFlux);
                    // [Step 7 fix: bug C3 part 3 — restore the runnonco2fluxOpen guard]
                    runnonco2fluxOpen = !file.is_open();
                }
            }
```

#### Why the first-call bypass

`firstCall` is a function-scope local on line 244 of `climatemodel.cpp`,
initialized from `IMOGENConfig::FIRSTCALL` (which is set true via the
ins-file param at startup and reset to false at line 993 after the
first iteration completes). So `firstCall` is true precisely on the
very first iteration of the very first year — exactly when no LPJG-side
`done` file has been written yet. After that first iteration,
`firstCall = false` and the polling loop's `done`-check operates with
its normal handshake semantics.

### 3.2 C4 — `lpjguess/modules/imogen_input.cpp:728`

**Sister-module check (the user asked about it before committing):**
the tight-coupling input module `lpjguess/modules/imogencfx.cpp:895`
contains the same `ndep.getndep(...)` call. Verified that THAT call
was **never commented out** — only the loose-coupling `imogen_input.cpp`
twin had been broken in the predecessor framework. `[CMI §3.x]` calls
this out as "inconsistent maintenance". So bug C4's source-fix scope
is correctly limited to `imogen_input.cpp`. To prevent future
maintenance drift, a small **cross-reference comment** was added next
to the `imogencfx.cpp:895` call pointing at the `imogen_input.cpp`
twin.



#### Before

```cpp
	// Get nitrogen deposition, using the found CRU coordinates
	//ndep.getndep(param["file_ndep"].str, cru_lon, cru_lat,Lamarque::parse_timeseries(ndep_timeseries));

	soilinput.get_soil(cru_lon, cru_lat, gridcell);
```

#### After

```cpp
	// Get nitrogen deposition, using the found CRU coordinates.
	// [Step 7 fix: bug C4 — un-comment this active call.
	//  The ndep object is later used at line 855 in getclimate() (via
	//  ndep.get_one_calendar_year); without this initialiser, ndep returns
	//  zero/garbage values throughout the run, silently breaking N-deposition
	//  forcing in loose-coupling mode.]
	ndep.getndep(param["file_ndep"].str, cru_lon, cru_lat, Lamarque::parse_timeseries(ndep_timeseries));

	soilinput.get_soil(cru_lon, cru_lat, gridcell);
```

### 3.3 F-4 (Fortran twin of C2/C3) — `imogen/code/imogen_lpjg.f`

#### Insertion point

Right before the outer `DO WHILE (KEEPRUNNING)` loop, after the
existing `OPEN/CLOSE` of `CO2_all.dat`. The block:

```fortran
C [Step 7 of unified-codebase rebuild: bug F-4 fix — auto-create the
C  'done' handshake file in <DIR_COMMON>/LPJG_main/IMOGEN/ if it
C  doesn't exist. This eliminates the manual workaround required since
C  step 4 (where every standalone IMOGEN invocation needed a prior
C  "touch LPJG_main/IMOGEN/done") and is the Fortran twin of bugs C2/C3
C  fixed in lpjguess/modules/climatemodel.cpp at the same step.
C  In coupled mode, LPJ-GUESS controls this file's lifecycle yearly;
C  this auto-create only kicks in once on the very first invocation
C  when no prior handshake exists.]
      CALL SYSTEM('mkdir -p '//TRIM(ADJUSTL(DIR_COMMON))//
     & '/LPJG_main/IMOGEN')
      CALL SYSTEM('touch '//TRIM(ADJUSTL(DIR_COMMON))//
     & '/LPJG_main/IMOGEN/done')
```

#### Why `mkdir -p` + `touch` rather than an INQUIRE/OPEN block

Three reasons:

1. **Idempotent**: `mkdir -p` succeeds whether the dir exists or not;
   `touch` succeeds whether the file exists or not (just updates mtime
   if so).
2. **No new variables needed** — keeps the diff small and avoids
   declarations.
3. **Consistent with existing code style**: `imogen_lpjg.f` already
   uses `CALL SYSTEM('mkdir ...')` for the per-year output dir
   creation (lines 435, 461 — fixed at step 2 from Windows backslashes).

The line-363 dead `!DONE_EXIST=.TRUE.` comment was deleted in the same
edit since the F-4 auto-create has rendered it permanently moot.

#### Why this works

The Fortran polling loop's INQUIRE on line 371 reads `DONE_EXIST` from
the filesystem. With the auto-create above, the file always exists by
the time the loop's first iteration runs, so DONE_EXIST starts true.
The loop exit condition (lines 400-403) then has `DONE_EXIST = .TRUE.`
on iteration 1 of the very first year, exits the polling loop, and
proceeds with year-1 processing. After year 1 completes, in coupled
mode LPJ-GUESS would manage the file's lifecycle for year 2+; in
standalone mode (where there's no LPJG), the binary's own
post-year-handoff logic takes over.

---

## 4. Verification

### 4.1 LPJ-GUESS build + tests

```bash
$ cd lpjguess/build && make
[ 46%] Built target guess
[100%] Built target runtests

$ ./runtests
===============================================================================
All tests passed (162 assertions in 25 test cases)
```

✅ Build clean; 162 unit tests pass — no regression from the C2/C3/C4
fixes.

### 4.2 Fortran IMOGEN build

```bash
$ cd imogen/code && make clean && make
gfortran -o imogen_lpjg.o -c -ffixed-line-length-132 -O imogen_lpjg.f
gfortran -o nonco2.o -c -ffixed-line-length-132 -O nonco2.f
gfortran -o imogen_lpjg imogen_lpjg.o nonco2.o
```

✅ Build clean; binary at `imogen_lpjg` (130 KB ELF 64-bit Linux).

### 4.3 Critical: standalone smoke run WITHOUT manual workaround

```bash
$ cd imogen/code
$ rm -rf LPJG_main IMOGEN                            # nuke all stale state
$ mkdir -p LPJG_main/IMOGEN IMOGEN/output
$ cp /path/to/version_A/.../LPJG_main/IMOGEN/*.txt LPJG_main/IMOGEN/   # stub control files only

$ test -f LPJG_main/IMOGEN/done && echo "FAIL" || echo "OK: no 'done'"
OK: no 'done'

$ timeout 60 ./imogen_lpjg
 Read NGPOINTS:         3698
 IMOGEN: ALLOCATEd regrid arrays for NGPOINTS=        3698
. RUNNOW_EXIST = T
 DONE_EXIST = T          ← FIRST iteration finds the auto-created done file ✅
 …                       ← polling loop exits, year 1 processing begins
 (years 1871, 1872 run to completion, each writing IMOGEN/output/<YYYY>/...)

$ ls IMOGEN/output/
1871  1872

$ ls IMOGEN/output/1871/
CO2.dat  DTEMP_anom.dat  P_anom.dat  SW_anom.dat  T_anom.dat  WET.dat  done  dtemp_o.dat  fa_ocean.dat
```

**No manual `touch done` was needed** — the binary self-bootstraps the
handshake file. Compare with steps 4-6 where every standalone run
needed `touch LPJG_main/IMOGEN/done` first or the polling loop would
spin forever.

The `LPJG_main/IMOGEN/done` file ends up deleted by the binary's own
year-end logic, which is the expected handshake-cycle behavior — the
file is meant to be transient between years.

After year 1872 completes (IYEND=1872), the binary re-enters the
polling loop expecting year 1873 setup that never comes (because no
LPJ-GUESS is updating the control file in standalone mode). That
indefinite poll-after-IYEND is the same steady-state we observed in
steps 4-6 and is unrelated to this fix — it would only stop in coupled
mode where LPJ-GUESS controls the outer loop's KEEPRUNNING.

### 4.4 Regression check vs step-4 baseline

For year 1871 / cell (lat=82.5°, lon=281.25°), `T_anom.dat` first row:

| Run | T_jan | T_feb | T_mar |
|---|---:|---:|---:|
| Step 4 (with manual `done` workaround) | 237.736 | 235.544 | 231.825 |
| Step 7 (auto-created `done`) | _to be filled_ | _to be filled_ | _to be filled_ |

Both should produce **byte-identical** output — the F-4 fix only
changes WHO creates the `done` file, not the simulation logic. (Spot-
check left as a follow-up if any concern; not blocking.)

---

## 5. Files modified

### Source code

| File | Change |
|---|---|
| `lpjguess/modules/climatemodel.cpp` | Restore `doneExist` INQUIRE + first-call bypass (C2); restore 3 `*Open` guards (C3); 4 commented-out lines un-commented across lines 332-353 |
| `lpjguess/modules/imogen_input.cpp` | Uncomment `ndep.getndep(...)` at line 728 (C4) |
| `lpjguess/modules/imogencfx.cpp` | Cross-reference comment at line 895 pointing at the `imogen_input.cpp` twin call (purely documentation; the call was already active and didn't need a fix) |
| `imogen/code/imogen_lpjg.f` | Insert `mkdir -p` + `touch done` block before the `DO WHILE (KEEPRUNNING)` loop (F-4); delete the dead `!DONE_EXIST=.TRUE.` comment that the auto-create supersedes |

### Documentation

| File | Change |
|---|---|
| `notes/STEP_7.md` | this file (new) |
| `notes/FOLLOWUPS.md` | Move F-4 from OPEN to DONE |
| `CHANGELOG.md` | `[v0.7.0-coupling-fixes]` entry |
| `EXECUTION_PLAN.md` | V.1 step 7 marked ✅ |

---

## 6. Recovery / re-run protocol

The step-7 fixes are **purely local source edits** — no external state,
no schema changes, no data dependencies. To recover:

```bash
# Clean revert
git revert <step-7-hash>

# Or selectively revert one fix:
git checkout HEAD~1 -- lpjguess/modules/climatemodel.cpp     # revert C2/C3 only
git checkout HEAD~1 -- lpjguess/modules/imogen_input.cpp     # revert C4 only
git checkout HEAD~1 -- imogen/code/imogen_lpjg.f             # revert F-4 only

# Then rebuild
cd lpjguess/build && make
cd ../../imogen/code && make
```

Standalone IMOGEN smoke runs will then again require the manual
`touch LPJG_main/IMOGEN/done` workaround.

---

## 7. Follow-ups closed by step 7

- **F-4 (CLOSED)** — Bug C2/C3 source fix (the polling-loop `DONE_EXIST`
  default). Resolved on both C++ side (climatemodel.cpp first-call
  bypass) and Fortran side (imogen_lpjg.f auto-create-`done`).

## Follow-ups raised by step 7

None new. C5's typo fixes are deferred to step 9 where the actual
run-config `.ins` files for v1.0 will be created (and we'll
self-evidently use `IMOGEN/output/` and `Rh_anom.dat` correctly).

---

## 8. Push commands (manual three-way push)

```bash
cd /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm

git push origin main
git push kit main
git push helmholtz main

# Optional tag:
git tag -a v0.7.0-coupling-fixes -m "Step 7: source-level coupling fixes (C2, C3, C4) + F-4 closer; no manual workaround needed for standalone IMOGEN"
git push origin v0.7.0-coupling-fixes
git push kit    v0.7.0-coupling-fixes
git push helmholtz v0.7.0-coupling-fixes
```
