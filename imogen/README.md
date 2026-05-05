# `imogen/` — IMOGEN climate emulator (Fortran, working IMOGEN)

The Fortran IMOGEN climate emulator with the LPJ-GUESS coupling
extensions. Imported and minimally fixed at **step 2**; refactored to
support run-time-configurable gridlist sizing at **step 3**; reference
data (GCM patterns + CRUNCEP base climatology) acquisition automated
at **step 4**, where the binary first produced real per-year output
(years 1871, 1872 of the standalone smoke run). See `EXECUTION_PLAN.md`
§V; `../notes/STEP_{2,3,4}.md` for per-step verification records.

The C++ refactor (`IMOGENCXX/`) gets brought to numerical parity
against this Fortran in **Phase 2** of the IMOGEN rebuild
(post-v1.0). Both backends will then be available as switchable
implementations per Decision #2.

## Provenance

Imported from the user's predecessor framework's
`Common-directory/IMOGEN-codebase/code/` (in `version_A`). Source
attribution: Huntingford & Cox 2000, Huntingford 2010 (the
foundational IMOGEN papers in `docs/`); Zelazowski 2018 for the
22-GCM pattern set; Hayman 2021 for CH4-mitigation extensions;
Mathison 2025 PRIME for the FaIR ERF integration approach the
working paper adopts.

## Layout (post-step-3)

```
imogen/
├── README.md                          (this file)
├── code/                              ← imported from
│   ├── imogen_lpjg.f                   Common-directory/IMOGEN-codebase/code/
│   ├── nonco2.f                        in step 2 (~470 KB);
│   │                                   step 3: NGPOINTS-arrays converted to ALLOCATABLE
│   ├── Makefile                       Build with: make
│   ├── compile.sh                     Alternative: bash compile.sh
│   ├── imogen_settings.txt            Linux-relative-path defaults (rewritten
│   │                                   from Windows C:\GitHub\... paths in step 2);
│   │                                   step 3: new NGPOINTS key for run-time grid sizing
│   ├── imogen_settings_tmpl.txt       Shell-variable template (upstream)
│   ├── gridlist_global.txt            13-cell tiny test grid
│   ├── gridlist_3deg.txt              2 371-cell 3° grid
│   ├── gridlist_hurtt_RNDM_midpoint_3698.txt    NGPOINTS=3698 default
│   ├── gridlist_hurtt_RNDM_midpoint_3711.txt    older variant
│   ├── gridlist_out.txt               (alias for 3deg?)
│   ├── patterns_gridlist.txt          1631-cell IMOGEN native (HadCM3 land)
│   ├── ch4_n2o_annual_historical_rcp85_allsources_1850_2100.txt
│   ├── .gitignore                     upstream Fortran .gitignore
│   └── (build/run output gitignored: imogen_lpjg, *.o, qsat_output.txt, IMOGEN/)
│
├── patterns/                          ← imported in step 4 (~169 MB)
│                                       36 GCM-pattern dirs:
│                                       • 34 CMIP5 ASCII (CEN_*_MOD_*)
│                                       • 1 CMIP3 legacy (ukmo_hadcm3_rel)
│                                       • 1 CMIP6 NetCDF (5 GCMs incl. MRI-ESM2-0)
│                                       Plus CMIP6 → CMIP5 ASCII converted
│                                       output in step 5 (CEN_CMIP6_MOD_*).
│
└── CRUNCEP_1960_1989/                 ← imported in step 4
                                        30-year base climatology, 12 months ×
                                        30 years × 1631 cells.
```

## Build instructions

The build uses `gfortran` with fixed-form Fortran 77 settings:

```bash
cd imogen/code
make                               # produces ./imogen_lpjg (Linux convention)
# OR
bash compile.sh                    # alternative; same output
```

Expected output: `imogen_lpjg` — a 119 KB ELF 64-bit Linux executable.

The build target was renamed from `imogen` (predecessor) to
`imogen_lpjg` for two reasons: (a) consistency with the source
filename `imogen_lpjg.f`, (b) matches the binary name expected by the
top-level `.gitignore`. The `.exe` suffix was removed from
`compile.sh` (Windows convention; superfluous on Linux).

## Step-2 immediate fixes applied on import

Three fixes from `[CMI §8.1]` were applied immediately on import,
per the V.1 step-2 spec ("apply the small fixes immediately on
import"):

| Bug | Where | Fix |
|---|---|---|
| **C10** — `PAUSE` left inside `QSAT` | `imogen_lpjg.f:4134` (now removed) | Deleted the active `PAUSE` statement that halted non-interactive runs awaiting an interactive keystroke |
| **C11** — `qsat_output.txt` debug-dump | `imogen_lpjg.f:4119-4135` (now removed) | Deleted the `OPEN`/`WRITE` block that opened `qsat_output.txt` per QSAT call (per cell × per sub-day step × per day × per month) without closing — leaking file handles and generating O(GB) of unused output |
| **C12** — Windows `\IMOGEN\output\` mkdir paths | `imogen_lpjg.f:435, 461` (now `/IMOGEN/output/`) | Replaced backslash separators with forward slashes so `CALL SYSTEM('mkdir ...')` works on Linux |
| **C13** — Windows paths in settings file | `imogen_settings.txt` lines 1-6 | Rewrote `C:\GitHub\dbampoh\...` absolute paths to relative paths (`./`, `../patterns/...`, `../CRUNCEP_1960_1989/`, etc.) |

A small portability fix to the `Makefile` `clean` target was also
applied (Windows `del` → Linux `rm -f`); this aligns with the
`[CMI §1.4]` Linux-only declaration.

The standalone IMOGEN-only run (1631-cell native grid for 3 years
1871-1873, producing `Common-directory/IMOGEN/output/<YYYY>/{T_anom.dat,
P_anom.dat, ..., done}` matching the existing run on disk in
`version_A`) is **deferred to step 4** — it requires the patterns
and CRUNCEP base climatology that get imported at step 4. The
step-2 verification reduces to "build succeeds" + "binary starts up
and parses settings file" (both confirmed; see `notes/STEP_2.md`).

## Step-3 `ALLOCATABLE` refactor — what changed

Per Decision #2 and `EXECUTION_PLAN.md` §V step 3, the **6 `NGPOINTS`-dimensioned
arrays** in `PROGRAM IMOGEN` were converted from static to `ALLOCATABLE`,
and `NGPOINTS` was promoted from a `PARAMETER` to a run-time setting:

| Array | Old declaration | New declaration |
|---|---|---|
| `T_OUT_M_REGRID` | `REAL T_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)` (static) | `REAL, ALLOCATABLE :: T_OUT_M_REGRID(:,:,:,:)` |
| `P_OUT_M_REGRID` | static `(NGPOINTS,MM,32,NSDMAX)` | `ALLOCATABLE (:,:,:,:)` |
| `SW_OUT_M_REGRID` | static `(NGPOINTS,MM,32,NSDMAX)` | `ALLOCATABLE (:,:,:,:)` |
| `DTEMP_OUT_M_REGRID` | static `(NGPOINTS,MM,32)` | `ALLOCATABLE (:,:,:)` |
| `F_WET_CLIM_REGRID` | static INTEGER `(NGPOINTS,MM)` | `INTEGER, ALLOCATABLE (:,:)` |
| `LON_OUT`, `LAT_OUT` | static `(NGPOINTS)` | `ALLOCATABLE (:)` |

`NGPOINTS` itself moved from `PARAMETER(NGPOINTS=3698)` to a regular
`INTEGER` populated by `SETTIN` from a new `NGPOINTS 3698` line in
`imogen_settings.txt`. A sentinel value (`-1`) plus post-loop
validation in `SETTIN` aborts cleanly if the line is missing or
non-positive.

**To run with a 62 000-cell gridlist** (the original motivation, from
`COUPLED_MODEL_INVESTIGATION.md` §4.3.3):

1. Edit `imogen_settings.txt`: change `NGPOINTS 3698` to `NGPOINTS 62000`.
2. Edit `FILE_GRIDLIST` to point to your 62 000-line gridlist file.
3. Run `./imogen_lpjg`. **No recompile needed.**

The startup banner `IMOGEN: ALLOCATEd regrid arrays for NGPOINTS=…`
prints the actual value at runtime, supporting the units-integrity
discipline rule "startup banners" (`CONTRIBUTING.md`).

### What stayed `PARAMETER` (deferred)

| Constant | Value | Why kept static |
|---|---:|---|
| `GPOINTS` | 1631 | Hard-coupled to the pattern + CRUNCEP file structure (those files have exactly 1631 cells); changing requires regenerating upstream files. ~30 arrays affected; pure heap-vs-BSS tweak with no functional benefit at the current value. |
| `NFARRAY` | 10000 | Caps a single coupled-run segment to 500 yr at NCALLYR=20; sufficient for v1.0 251-yr scenarios. |
| `N_OLEVS` | 254 | Ocean column resolution; a science choice, not a memory bottleneck. |

`nonco2.f` references none of these constants — no changes there.

## Step-4 IMOGEN reference data + standalone smoke milestone

Step 4 added the GCM-pattern + CRUNCEP-base-climatology data acquisition
infrastructure. **The data lives outside git** (49 MB compressed → 161 MB
extracted); it's fetched at workstation/cluster setup time via:

```bash
tools/fetch_imogen_data.sh --base <DATA_LOCATION>
```

See `imogen/patterns/README.md` and `imogen/CRUNCEP_1960_1989/README.md`
for the full layout, and `tools/README.md` for fetch-script usage.

**Verification milestone hit at step 4**: with the data staged plus
the small workaround for bug C2/C3 (pre-staging an empty `done` file
in `imogen/code/LPJG_main/IMOGEN/`), the Fortran IMOGEN binary produced
sensible per-year output for 1871, 1872 (`T_anom.dat`, `P_anom.dat`,
`SW_anom.dat`, `DTEMP_anom.dat`, `WET.dat`, `dtemp_o.dat`, `fa_ocean.dat`,
`CO2.dat`, `done`). Sample T values are physically plausible
(231–276 K Arctic-summer-to-winter swing at lat=82.5°). See
`notes/STEP_4.md` for the comparison against `version_A`'s reference.

## What's NOT in this step

- **`Rh_anom.dat` and `W_anom.dat`** are still missing in the Fortran
  output (confirms `[SA3 §10]`; will be ported back from C++ at step 9.5
  per Decision #11).
- **Bug C2/C3** (the polling-loop `DONE_EXIST` check) is **worked around
  via runtime stub files** but not yet fixed in the source. The
  source-level fix lands at step 7 of the rebuild plan.
- **No live coupling with LPJ-GUESS** yet — the `imogen_lpjg` binary
  is run standalone here. Coupled-mode validation (LPJ-GUESS calling
  the in-process C++ IMOGEN engine via `imogencfx`) is steps 6-9 of
  the rebuild plan.
- **CMIP6 patterns are staged but not yet consumable by the binary**:
  it expects the CMIP5 ASCII format. The CMIP6 NetCDF → CMIP5 ASCII
  converter (`tools/cmip6_nc_to_cmip5_ascii.py`) is step 5.
- **Numerical parity between Fortran and C++ IMOGEN** has not been
  established — that's itself the Phase-2 milestone (Decision #2).
  Step 4's smoke run shows ours produces sensibly-shaped output but
  diverges from `version_A`'s C++-produced reference by 0.1–8 K on
  T_anom for some cells; the systematic Fortran-vs-C++ comparison is
  deferred to Phase 2.

## Settings file convention

`imogen_settings.txt` ships with sensible Linux-relative defaults
that resolve from `imogen/code/`:

```
DIR_COMMON ./
DIR_PATT ../patterns/CEN_IPSL_MOD_IPSL-CM5A-MR/
DIR_CLIM ../CRUNCEP_1960_1989/
FILE_SCEN_EMITS ../emiss/co2_emissions_annual_historical_rcp85_allsources.txt
FILE_NON_CO2_VALS ../emiss/nonco2_ch4_n2o_RF_historical_rcp85.txt
FILE_CH4_N2O_EMITS ../emiss/ch4_n2o_annual_historical_rcp85_non_lpjg_simulated.txt
NGPOINTS 3698        # NEW in step 3: number of grid points; must
                     # match line count of FILE_GRIDLIST.
...
```

This is a **standalone-IMOGEN reference config**, used when running
`imogen_lpjg` directly from `imogen/code/`. Coupled-mode runs
(LPJ-GUESS in `imogencfx` mode invoking the in-process IMOGEN
engine) use a separate `runs/<SSP>/imogen_intermediary.ins` file
that overrides via the `IMOGENConfig::*` namespace. See
`runs/README.md` and Decision #4 for the three coupling modes.

For shell-variable templating (e.g. `$IMOGENPATH`, `$WORKPATH`,
`$IMOGENPATTERN`), see `imogen_settings_tmpl.txt` (upstream
template, unchanged).

## Backup preserved at `archive/`

The predecessor's `Original Imogen Modified for LPJG Coupling/imogen_lpjg.f`
(180 KB; described in `[SA3 §11]` as a backup of an earlier
`NGPOINTS=3711`/disabled-`done`-poll/no-PAUSE version) was archived
to `../archive/imogen_fortran_backup/imogen_lpjg.f` for forensic
reference rather than imported. This is per Decision #5
(rebuild-approach: A/B remain immutable archives; legacy artefacts
preserved in `archive/` rather than mutated).

## Cross-references

- `[CMI §4.2]` — full deep-dive on this Fortran source (17 subroutines
  catalogued; bug list).
- `[SA3]` — Subagent 3's 47-KB report at
  `../_phase2_findings/03_imogen_fortran.md` is the canonical
  evidence base.
- `[EXEC §V.1 step 2]` — the V.1 plan entry for this step.
- `[EXEC §II.2]` — the strategic decision for the
  Fortran-with-`ALLOCATABLE`-first / C++-port-second IMOGEN strategy.
- `[Decision #2]` — IMOGEN implementation strategy.
- `[Decision #8]` — Anaconda3 NetCDF preference (note: IMOGEN itself
  doesn't use NetCDF — pure Fortran 77 ASCII I/O — so this build
  doesn't depend on NetCDF at all; the only step that needs NetCDF
  is the CMIP6 → CMIP5 ASCII converter at step 5, written in Python).
