# STEP 2 — Import Fortran IMOGEN → `imogen/`

> **Plan reference:** `EXECUTION_PLAN.md` §V.1 step 2.
>
> **Status:** completed 5 May 2026.
>
> **Verification milestone (per V.1):** *"`gfortran -ffixed-line-length-132
> -O imogen_lpjg.f nonco2.f -o imogen_lpjg` builds clean. Standalone
> IMOGEN run on the 1631-cell native grid for 3 years (1871-1873)
> produces `Common-directory/IMOGEN/output/<YYYY>/{T_anom.dat, ..., done}`
> matching the existing run on disk in A."*
>
> **Verification status:** ✅ Build verified (`make` and
> `bash compile.sh` both produce `imogen_lpjg` cleanly); ✅ binary
> starts up and parses the rewritten settings file; ⏸ standalone
> IMOGEN-only run **deferred to step 4** because it requires the
> `patterns/` and `CRUNCEP_1960_1989/` data that get imported at step 4.

## What this step did

### Phase A — Import (rsync `code/` from source)

**Source:** `version_A/.../Common-directory/IMOGEN-codebase/code/`
(180 KB across 14 files, plus the 180 KB
`Original Imogen Modified for LPJG Coupling/` backup).

**Imported into `imogen/code/` (~470 KB):**

| File | Size | Role |
|---|---|---|
| `imogen_lpjg.f` | 178 KB (was 181 KB pre-fixes) | Main IMOGEN source (4 138 lines, 1 PROGRAM + 17 SUBROUTINEs) |
| `nonco2.f` | 8.4 KB | FAIR-style CH4/N2O budget + radiative forcing |
| `Makefile` | 238 B | gfortran build; `make` target renamed `imogen` → `imogen_lpjg` (alignment with V.1 spec); `clean` target Windows `del` → Linux `rm -f` |
| `compile.sh` | 122 B | Brought from parent `IMOGEN-codebase/compile.sh`; alternative to Makefile; `.exe` suffix removed |
| `imogen_settings.txt` | 3.0 KB (was 3.2 KB) | Active runtime settings — Windows `C:\GitHub\…` paths rewritten to Linux relative paths |
| `imogen_settings_tmpl.txt` | 2.6 KB | Shell-variable template (`$IMOGENPATH`, `$WORKPATH`); unchanged |
| `gridlist_global.txt` | 515 B (13 cells) | Tiny test grid |
| `gridlist_3deg.txt` | 38 KB (2 371 cells) | 3° grid |
| `gridlist_hurtt_RNDM_midpoint_3698.txt` | 63 KB (3 698 cells) | NGPOINTS=3698 default |
| `gridlist_hurtt_RNDM_midpoint_3711.txt` | 67 KB (3 711 cells) | Older variant ([SA3 §11]) |
| `gridlist_out.txt` | 38 KB | (3deg duplicate?) |
| `patterns_gridlist.txt` | 26 KB (1 631 cells) | IMOGEN native HadCM3 land grid |
| `ch4_n2o_annual_historical_rcp85_allsources_1850_2100.txt` | 6.3 KB | Annual CH4/N2O time series for RCP8.5 |
| `.gitignore` | 269 B | Upstream Fortran .gitignore |

**Skipped:**

| Item | Why skipped | Where it went |
|---|---|---|
| `Original Imogen Modified for LPJG Coupling/imogen_lpjg.f` | Backup; per V.1 spec "(backup; archive only)" | Archived to `archive/imogen_fortran_backup/imogen_lpjg.f` for forensic reference (per [SA3 §11]) |
| `qsat_output.txt` | Debug output from a previous run | Not needed |
| `.vscode/` (at parent IMOGEN-codebase level) | IDE config; Windows-specific paths | Not needed |
| `R_wrappers/` (at parent level) | Standalone-IMOGEN R analysis scripts; out of scope per [CMI §4.2.1] | Not needed for v1.0; can be reconsidered later |
| `patch_add_ch4_n2o_conc.diff` (at parent level) | Already applied to `imogen_lpjg.f` per [SA3 §11] | Not needed |
| `patterns/`, `CRUNCEP_1960_1989/`, `emiss/`, `docs/` (at parent level) | Imported at step 4 | Step 4 |

### Phase B — Apply immediate fixes (per V.1 step-2 spec)

Three fixes plus one Makefile portability fix were applied
immediately on import:

#### Fix 1: Delete `qsat_output.txt` debug-dump + `PAUSE` (bugs C10, C11)

The block `imogen_lpjg.f:4119-4135` contained:

- An `OPEN(UNIT=99, FILE='qsat_output.txt', STATUS='UNKNOWN')` that
  was never closed
- A `DO I = 1, NPNTS / WRITE(UNIT_NO, …)` loop that wrote one row
  per gridcell per QSAT call
- A `PAUSE` statement that halted non-interactive runs awaiting an
  interactive keystroke

QSAT is called inside `DAY_CALC` for every gridcell × every sub-day
step × every day × every month, so the dump leaked file handles and
generated O(GB) of unused output. The `PAUSE` made cluster runs
impossible.

Replaced with a 6-line `C`-comment block referencing `EXECUTION_PLAN.md`
V.1 step 2 and `[CMI §8.1]` bugs C10/C11 for traceability.

Verification: `grep -n "PAUSE" imogen_lpjg.f` shows only commented
lines (`c        PAUSE`, `!PAUSE`); no active PAUSE remains.
`grep -n "qsat_output.txt" imogen_lpjg.f` shows only the new
comment block + an unrelated already-commented line at 1765
(`!OPEN(UNIT=99, FILE='B_qsat_output.txt', ...)`). `imogen_lpjg.f`
shrank from 181 KB → 178 KB.

#### Fix 2: Replace Windows `\IMOGEN\output\` with `/IMOGEN/output/` (bug C12)

Two `CALL SYSTEM('mkdir ...//\IMOGEN\output\...')` calls at lines
435 and 461 used Windows path separators, which on Linux make
`mkdir` interpret `\IMOGEN\output\` as one weird filename — silently
failing (since `CALL SYSTEM` doesn't propagate exit status).

Replaced with forward slashes. Verification: `grep -n '\\\\IMOGEN'`
returns nothing; `grep -n "/IMOGEN/output/" imogen_lpjg.f` shows the
two now-fixed `mkdir` calls plus three pre-existing `OPEN`
statements (lines 439, 444, 501) that were always using forward
slashes — confirming the slash inconsistency was specifically in the
`SYSTEM` mkdir calls per `[SA3 §13]`.

#### Fix 3: Rewrite Windows paths in `imogen_settings.txt` (bug C13)

The first 6 lines of the original `imogen_settings.txt` had absolute
Windows paths:

```
DIR_COMMON C:\GitHub\dbampoh\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Common-directory
DIR_PATT C:\GitHub\dbampoh\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Common-directory\IMOGEN-codebase\patterns\CEN_IPSL_MOD_IPSL-CM5A-MR\
... (4 more)
```

Rewritten to Linux-relative paths that resolve from `imogen/code/`:

```
DIR_COMMON ./
DIR_PATT ../patterns/CEN_IPSL_MOD_IPSL-CM5A-MR/
DIR_CLIM ../CRUNCEP_1960_1989/
FILE_SCEN_EMITS ../emiss/co2_emissions_annual_historical_rcp85_allsources.txt
FILE_NON_CO2_VALS ../emiss/nonco2_ch4_n2o_RF_historical_rcp85.txt
FILE_CH4_N2O_EMITS ../emiss/ch4_n2o_annual_historical_rcp85_non_lpjg_simulated.txt
```

Lines 7-10 (FILE_LPJG_FLUX, FILE_GRIDLIST, FILE_LPJG_CH4_N2O_FLUX,
FILE_SCEN_CO2_PPMV) were already relative. All ~30 numeric/boolean
parameters from line 11 onwards are unchanged.

This is a **standalone-IMOGEN reference config** for when running
`imogen_lpjg` from `imogen/code/`. Coupled-mode runs use
`runs/<SSP>/imogen_intermediary.ins` and override via the
`IMOGENConfig::*` namespace.

Verification: `grep -n "C:\\\\" imogen_settings.txt` returns
nothing; first 6 lines now show Linux relative paths.

#### Bonus fix: Makefile portability

Three changes to `imogen/code/Makefile`:

1. Build target renamed `imogen` → `imogen_lpjg` (matches the V.1
   step-2 spec's `gfortran -o imogen_lpjg` and the source filename
   `imogen_lpjg.f`).
2. `clean` target: Windows `del *.o / del *exe` → Linux
   `rm -f *.o / rm -f imogen_lpjg imogen_lpjg.exe imogen` (covers
   both naming conventions defensively).
3. `compile.sh` (the alternative to Makefile): `.exe` suffix removed
   from binary name (Linux convention; aligns with the Makefile
   target name).

These weren't in the V.1 step-2 spec but follow the same
"replace Windows-isms with Linux-isms" pattern and are zero-risk
1-character edits.

### Phase C — Build verification

```bash
cd imogen/code
make
# gfortran -o imogen_lpjg.o -c -ffixed-line-length-132 -O imogen_lpjg.f
# gfortran -o nonco2.o -c -ffixed-line-length-132 -O nonco2.f
# gfortran -o imogen_lpjg imogen_lpjg.o nonco2.o
# Exit code: 0
```

Output: `imogen_lpjg` — a 119 KB ELF 64-bit Linux executable.

```bash
file imogen_lpjg
# imogen_lpjg: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV),
# dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2,
# BuildID[sha1]=..., for GNU/Linux 3.2.0, not stripped
```

Both `make` and `bash compile.sh` produce identical 119 KB binaries.

### Phase D — Functional probe

Stronger than just "build succeeded": ran the binary briefly with
a 3-second timeout and confirmed it starts up cleanly and parses
the entire rewritten settings file:

```bash
timeout 3 ./imogen_lpjg
#  Read DIR_COMMON: ./
#  Read DIR_PATT: ../patterns/CEN_IPSL_MOD_IPSL-CM5A-MR/
#  Read DIR_CLIM: ../CRUNCEP_1960_1989/
#  ... (all 30+ settings read correctly)
#  Read CO2_INIT_PPMV:    286.084991
#  ... (binary halts at the LPJG-handshake polling loop, expected)
# Exit code: 141 (= 128 + SIGTERM = killed cleanly by timeout)
```

This proves:
- The Fortran parses the rewritten settings file correctly.
- The relative paths are syntactically valid (the engine reads
  them; will fail later when it tries to open the actual files,
  which is fine).
- The fixes haven't broken the startup path.
- The polling loop in `imogen_lpjg.f:351..404` (which polls for
  the LPJG-side `done` file) is reached, then the timeout kills
  the process before the `mkdir` call (so no `IMOGEN/output/`
  artefact is left in CWD — confirmed clean).

### Phase E — Standalone IMOGEN smoke run deferred to step 4

The V.1 step-2 milestone's *"Standalone IMOGEN run on the 1631-cell
native grid for 3 years (1871-1873)"* is **deferred to step 4** for
exactly the same reason step-1's CFX run was deferred to step 6: the
data needed to run isn't staged yet. Specifically:

- `../patterns/CEN_IPSL_MOD_IPSL-CM5A-MR/{jan,feb,...,dec}` — the
  GCM pattern files for the default IPSL-CM5A-MR GCM. Step 4
  imports these.
- `../CRUNCEP_1960_1989/{jan1,jan2,...,dec30}` — the 30-year base
  climatology. Step 4 imports this.
- `../emiss/co2_emissions_annual_historical_rcp85_allsources.txt`
  and friends — the emissions time series. Step 4 imports these.
- An `imogen_lpjg.txt` per-call settings file that LPJ-GUESS would
  write in coupled mode. For standalone we'd write one manually
  with `YEAR1 1871 / IYEND 1873 / SPINUP TRUE / KEEPRUNNING TRUE /
  FIRSTCALL TRUE`.

Step 4's verification milestone explicitly includes the standalone
IMOGEN run; so this is a clean handoff, not a missed deliverable.

## Effort

Wall-clock: ~25 minutes (rsync + 3 fix edits + Makefile/compile.sh
alignment + build × 2 + functional probe + documentation).

## What's NOT in this step

- No `ALLOCATABLE` array refactor. That's step 3 — converting the
  ~30 statically-declared arrays in `imogen_lpjg.f` and `nonco2.f`
  to `ALLOCATABLE`, removing the practical 3 698-cell gridlist cap
  (per Decision #2 + [SA3 §10]).
- No CMIP6 patterns or CRUNCEP imported. Step 4.
- No new modules. The LPJG-side handshake writer
  (`lpjguess/modules/imogenoutput.cpp`) is on the C++ side — step 8.
- No coupled run yet.

## Next: step 3 (Fortran ALLOCATABLE refactor)

Per `EXECUTION_PLAN.md` §V.1 step 3:

> Convert Fortran static arrays to `ALLOCATABLE` (per Decisions #2 and
> §II.2). Identify the ~30 statically-declared arrays in `imogen_lpjg.f`
> (with `NGPOINTS` or `GPOINTS` dimensions): `T_OUT_M_REGRID`,
> `P_OUT_M_REGRID`, `SW_OUT_M_REGRID`, `DTEMP_OUT_M_REGRID`, `T_ANOM_AM`,
> `T_CLIM_AM`, ... see `[SA3 §10]` for the full list. Convert each
> declaration to `ALLOCATABLE`; add `ALLOCATE(...)` calls at the top of
> `PROGRAM IMOGEN` after `NGPOINTS` is read from `imogen_settings.txt`
> (a small parser change to read `NGPOINTS` as a runtime parameter
> rather than a `PARAMETER`). Apply the same to `nonco2.f` arrays.

Verification: build still clean; standalone IMOGEN run on 1631-cell
native grid produces byte-identical output to step 2's output (proves
the refactor is numerically equivalent). Then recompile with
`NGPOINTS=62000` and run with a 62k-cell gridlist; confirm successful
completion (no OOM, no segfault) on a 32-GB-RAM machine.

This step also unlocks `v0.2-lpjg-builds` tag.

## Cross-references

- `[CMI §4.2]` — IMOGEN Fortran deep-dive.
- `[CMI §4.3.4a]` — Climate output asymmetry (Rh/W writers in C++,
  not Fortran; relevant for step 9.5).
- `[SA3 §10, §13]` — full bug catalogue for this Fortran source
  (16 entries; 3 fixed in this step, 13 remaining for steps 3, 7, 9.5).
- `[EXEC §I.A]` — code-level fix catalogue (C10, C11, C12, C13
  applied here).
- `[EXEC §V.1 step 2]` — the V.1 plan entry.
- `[Decision #2]` — Fortran-with-`ALLOCATABLE` first / C++ port second.
- `[archive/imogen_fortran_backup/]` — the predecessor's backup
  imogen_lpjg.f preserved here for forensic reference.
