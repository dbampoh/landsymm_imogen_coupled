# Phase 2 — Subagent 3 report: original Fortran IMOGEN (LPJG-coupling version)

Investigation root:
`landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/`

All paths in this report are relative to that root unless prefixed `/`.
This report is read-only — no source files were modified.
Line numbers are taken from the **current** working copy of `code/imogen_lpjg.f` (4138 lines).

---

## 1. Codebase top-level structure

| Path | Contents | Purpose |
|---|---|---|
| `code/` | Fortran source, settings, gridlists, reference data | Active build directory |
| `code/imogen_lpjg.f` | 4138 lines, 1 PROGRAM + 17 SUBROUTINEs | Main IMOGEN extended for LPJG coupling |
| `code/nonco2.f` | 174 lines, 2 SUBROUTINEs | FAIR-style CH4/N2O budget + radiative forcing |
| `code/Makefile` | 11 lines | Builds `imogen` from the two `.f` files |
| `code/Original Imogen Modified for LPJG Coupling/` | One file: `imogen_lpjg.f` (179,976 bytes) | A near-identical *backup* of `imogen_lpjg.f` (see §11) |
| `code/imogen_settings.txt` | 41 lines | Active runtime settings (Windows paths, RCP8.5 IPSL-CM5A-MR) |
| `code/imogen_settings_tmpl.txt` | 41 lines | Template settings with shell-variable placeholders |
| `code/gridlist_global.txt` | 13 rows | Tiny test gridlist |
| `code/gridlist_3deg.txt` | 2371 rows | 3° gridlist |
| `code/gridlist_hurtt_RNDM_midpoint_3698.txt` | 3698 rows | Standard "Hurtt 3698-cell" gridlist (matches current `NGPOINTS=3698`) |
| `code/gridlist_hurtt_RNDM_midpoint_3711.txt` | 3710 rows | Older 3711-cell variant (matches the original backup's `NGPOINTS=3711`) |
| `code/gridlist_out.txt` | 2371 rows | Default `FILE_GRIDLIST` for `REGRID_CLIM` (3° size) |
| `code/patterns_gridlist.txt` | 1631 rows | The internal IMOGEN climatology gridlist (matches `GPOINTS=1631`) |
| `code/ch4_n2o_annual_historical_rcp85_allsources_1850_2100.txt` | annual time series | CH4/N2O totals (Tg/yr) — used outside the coupled run by R wrappers |
| `code/qsat_output.txt` | thousands of rows | Debug dump created by an instrumentation block in `QSAT` (see §13) |
| `code/.gitignore` | 32 lines | Standard Fortran object/exec ignores |
| `code/.vscode/settings.json` | 4 lines | A user's VS Code Fortran-LS path (Windows, hard-coded) |
| `patterns/` | 38 entries (37 GCM dirs + 1 `readme.log`) | GCM-analogue pattern files (one file per month: `jan` … `dec`). Each file is `1632` lines = 1 header + 1631 grid points |
| `CRUNCEP_1960_1989/` | Many files: `jan1`, `jan2`, …, `dec30` | Per-year-of-30 climatology base. Each file `1632` lines = 1 header + 1631 grid points. (Used by `VARYEAR` cycling in main loop, lines 407–425) |
| `emiss/` | `DKB_dataset_totals/`, `new_emission_data/`, `rcp_database/`, `RF_NONCO2_GHG_IS92A.dat`, `emiss_co2.dat`, `hist_rcpXpY_emiss_ch4_n2o_total_cmip5.txt` (4 RCPs) | Anthropogenic CO2 emissions, CH4/N2O emissions, non-CO2 RF time series |
| `docs/` | `huntingford_and_cox_00.pdf`, `huntingford_et_al_10.pdf` | The two foundational IMOGEN papers — *no other internal docs or READMEs* |
| `R_wrappers/` | `generate_GCP2015_climate.R`, `rcp2p6_climate.R`, `run_imogen.R`, `setup_imogen.R` | Standalone R scripts for non-coupled IMOGEN runs/analysis (skim only) |
| `compile.sh` | 3 lines | Bare gfortran compile/link command |
| `patch_add_ch4_n2o_conc.diff` | 16-line patch | Adds CH4/N2O fields to `CO2.dat` writes when `NONCO2_EMISSIONS=.TRUE.` (see §12) |

> **Uncertainty:** the `R_wrappers/` scripts were not opened. They are listed because the user requested a skim only, and the file names match standalone-IMOGEN/GCP analysis flow rather than coupled-run plumbing.

---

## 2. Build system

### `compile.sh`
```bash
#!/bin/bash
gfortran -c -ffixed-line-length-132 imogen_lpjg.f nonco2.f
gfortran -o imogen_lpjg.exe imogen_lpjg.o nonco2.o
```

### `code/Makefile`
```makefile
#make file to control the compilation process: DKB 08-06-2022
FC=gfortran
SRC=imogen_lpjg.f nonco2.f
OBJ = ${SRC:.f=.o}

%.o: %.f
	${FC} -o $@ -c -ffixed-line-length-132 -O $<

imogen:${OBJ}
	${FC} -o $@ ${OBJ}

clean:
	del *.o
	del *exe
```

Notes:
- Compiler is hardwired to **gfortran**; `-ffixed-line-length-132` is required because many lines (especially in `imogen_lpjg.f`) exceed the F77 default 72-column limit.
- The Makefile produces `imogen` while `compile.sh` produces `imogen_lpjg.exe`.
- `clean` uses `del` (a Windows command) — would fail under Linux/macOS shells. Indicates the project's primary author worked on Windows.
- No external libraries are linked. Pure Fortran, no NetCDF.

---

## 3. `imogen_lpjg.f` — subroutine catalogue

All from `imogen_lpjg.f` (line numbers are starting lines).

| Line | Symbol | Role |
|---:|---|---|
| 16 | `PROGRAM IMOGEN` | Main controller. Reads settings, polls for LPJG-handshake files, runs the year loop, dispatches climate calculation/output and CO2/RF book-keeping. |
| 1089 | `SUBROUTINE REGRID_CLIM` | Nearest-neighbour regridding from the IMOGEN native `GPOINTS=1631` grid to an arbitrary output gridlist of size `NGPOINTS`. Reads `FILE_GRIDLIST`. |
| 1207 | `SUBROUTINE SETTIN` | Reads `imogen_settings.txt` (key/value parser) into ~30 IMOGEN parameters/paths/flags. |
| 1439 | `SUBROUTINE SETTIN_LPJG` | Reads the per-call file `<DIR_COMMON>/LPJG_main/IMOGEN/imogen_lpjg.txt` written by LPJ-GUESS each year (`YEAR1`, `IYEND`, `SPINUP`, `YEAR1_LPJG`, `KEEPRUNNING`, `FIRSTCALL`). Then deletes the LPJG `done` marker file. |
| 1511 | `SUBROUTINE DAY_CALC` | Disaggregate daily climatology to sub-daily (`STEP_DAY`) values: SW/T/LW/precip/pressure/wind/humidity. Calls `SUNNY`, `REDIS`, `QSAT`. |
| 1973 | `SUBROUTINE REDIS` | Stochastic redistribution of monthly precipitation across days/sub-day intervals. Uses `RNDM`. |
| 2120 | `SUBROUTINE SUNNY` | Computes sunshine fraction / cosine of zenith for each grid point each day. Calls `SOLPOS`, `SOLANG`. |
| 2267 | `SUBROUTINE SOLPOS` | Returns sin(declination) and Sun–Earth correction for a given calendar day. |
| 2332 | `SUBROUTINE SOLANG` | Computes solar zenith / mean cos(zenith) over a sub-day window for a given lat/long. |
| 2469 | `SUBROUTINE RNDM` | Park-Miller-style PRNG used by `REDIS`. |
| 2502 | `SUBROUTINE CLIM_CALC` | Adds anomaly fields (T/SW/LW/RH/U/V/DTEMP/precip/pressure) to base climatology, then per-day calls `DAY_CALC` to produce sub-daily `*_OUT` arrays. |
| 2752 | `SUBROUTINE DELTA_TEMP` | Two-box (land/ocean) energy-balance model with vertical ocean diffusion. Updates `DTEMP_O(N_OLEVS=254)` and returns global-land `DTEMP_L`. Calls `INVERT`. |
| 2927 | `SUBROUTINE INVERT` | Tridiagonal-matrix inversion for the implicit ocean diffusion solver. |
| 3103 | `SUBROUTINE GCM_ANLG` | The pattern-scaling step. For each month opens `<DIR_PATT>/<month>` and multiplies each pattern variable by `DTEMP_L` to produce `*_ANOM_AM` fields. |
| 3253 | `SUBROUTINE OCEAN_CO2` | Joos-style mixed-layer ocean carbon uptake. Computes `D_OCEAN_ATMOS` (ppm change) using `FA_OCEAN(NFARRAY=10000)` history. |
| 3422 | `SUBROUTINE RESPONSE` | Returns Joos pulse-response function values used by `OCEAN_CO2`. |
| 3459 | `SUBROUTINE RADF_CO2` | `Q_CO2 = (Q2CO2/ln 2) * ln(CO2/CO2REF)` — IMOGEN-standard CO2 forcing. |
| 3483 | `SUBROUTINE RADF_NON_CO2` | Reads `FILE_NON_CO2_VALS` (or uses hard-coded HadCM3 defaults) and linearly interpolates non-CO2 RF for the current year. |
| 3618 | `SUBROUTINE QSAT` | Saturation specific humidity from a Goff-Gratch lookup table (1551 entries, 183.15–338.15 K). |

`nonco2.f` (see §next) contributes 2 more subroutines that are CALLed from the main program.

---

## 4. Data flow and year loop

### High-level outline

```
PROGRAM IMOGEN
├─ CALL SETTIN                                  [imogen_settings.txt]
├─ Open <DIR_COMMON>/IMOGEN/CO2_all.dat         (truncate, then close)
└─ DO WHILE (KEEPRUNNING)                       [outer 'forever' loop, line 339]
   ├─ DO WHILE (.NOT. RUNNOW)                   [poll loop, line 351]
   │   ├─ CALL SLEEP(3); INQUIRE(...) for:
   │   │     - <DIR_COMMON>/LPJG_main/IMOGEN/done
   │   │     - <DIR_COMMON>/LPJG_main/IMOGEN/error
   │   │     - <DIR_COMMON>/LPJG_main/IMOGEN/imogen_lpjg.txt
   │   │     - <DIR_COMMON>/LPJG_main/IMOGEN/<FILE_LPJG_FLUX>
   │   │     - (optional) <DIR_COMMON>/LPJG_main/IMOGEN/<FILE_LPJG_CH4_N2O_FLUX>
   │   ├─ If all present + closed + done present:
   │   │     CALL SETTIN_LPJG  → reads YEAR1, IYEND, SPINUP, YEAR1_LPJG, KEEPRUNNING, FIRSTCALL
   │   └─ If 'error' marker present: STOP
   │
   ├─ Update VARYEAR (1..30, climate-variability iterator) → write VARYEAR.dat   [407–425]
   │
   ├─ If SPINUP: write a stub <YYYY>/CO2.dat with CO2_INIT_PPMV, then …
   │
   └─ DO IYEAR=YEAR1,IYEND                      [main year loop, line 455]
      ├─ mkdir <DIR_COMMON>/IMOGEN/output/<YYYY>     (Windows-style backslashes)
      ├─ If first year of LPJG run / SPINUP: zero DTEMP_O, FA_OCEAN; init seeds
      ├─ If 1-year-mode AND IYEAR > YEAR1_LPJG: read fa_ocean.dat / dtemp_o.dat from <YYYY-1> and last CO2 from <YYYY-1>/CO2.dat
      ├─ Read scenario CO2 emissions (FILE_SCEN_EMITS); optionally CH4/N2O emissions (FILE_CH4_N2O_EMITS)
      ├─ Read LPJG land C flux (FILE_LPJG_FLUX); optionally LPJG CH4/N2O fluxes
      ├─ Delete <DIR_COMMON>/LPJG_main/IMOGEN/done                                [592–593]
      ├─ Read climatology for VARYEAR: 12 files <DIR_CLIM>/<month><VARYEAR>
      ├─ If (ANOM .AND. ANLG):
      │     ├─ CALL RADF_CO2 → Q_CO2
      │     ├─ CALL RADF_NON_CO2 → Q_NON_CO2
      │     ├─ If NONCO2_EMISSIONS: CALL FAIR_NON_CO2_GHG (in nonco2.f) → Q_CH4, Q_N2O
      │     ├─ Q = Q_CO2 + Q_NON_CO2 (+Q_CH4+Q_N2O if NONCO2_EMISSIONS)
      │     ├─ Append (IYEAR, Q, …) to <DIR_COMMON>/IMOGEN/RF_all.dat
      │     └─ CALL GCM_ANLG → *_ANOM(GPOINTS,12) pattern-scaled anomalies
      ├─ CALL CLIM_CALC → daily/sub-daily *_OUT arrays
      ├─ Carbon-cycle update (only if INCLUDE_CO2 .AND. C_EMISSIONS .AND. ANOM .AND. ANLG):
      │     ├─ Apply anthropogenic emissions (CONV*C_EMISS_LOCAL)
      │     ├─ If LPJG_CFLUX: D_LAND_ATMOS = CONV*C_LPJG_LOCAL  (LPJG land flux)
      │     │     If NONCO2_EMISSIONS: CALL FAIR_NON_CO2_GHG_BUDGET → updates CH4_PPBV, N2O_PPBV
      │     ├─ ELSEIF LAND_FEED: D_LAND_ATMOS = -CONV*0.25*C_EMISS_LOCAL  (legacy 25%-of-emissions stub)
      │     └─ If OCEAN_FEED: CALL OCEAN_CO2 → D_OCEAN_ATMOS
      ├─ Write CO2.dat / append CO2_all.dat                                     [822–851]
      ├─ Build 365-day arrays (`*_M`) by extending months 28/29/30 → 31         [866–916]
      ├─ If REGRID: CALL REGRID_CLIM → `*_M_REGRID` on NGPOINTS gridlist        [917]
      ├─ Write per-year output files (T_anom.dat, P_anom.dat, SW_anom.dat, WET.dat, DTEMP_anom.dat) [925–1038]
      ├─ Write the year's IMOGEN→LPJG `done` marker:
      │     OPEN(97,FILE=…/IMOGEN/output/<YYYY>/done,STATUS='REPLACE')
      │     WRITE(97,*) 'Climate files written'; CLOSE(97)                       [1050–1052]
      └─ If OCEAN_FEED: write fa_ocean.dat, dtemp_o.dat                          [1057–1072]
END KEEPRUNNING loop
STOP
```

In the typical coupled mode each call processes a single year (`IYEND-YEAR1==0`); LPJ-GUESS then writes a new `done` marker to ask for the next year, and the `DO WHILE (KEEPRUNNING)` loop iterates again.

---

## 5. Settings file format — full parameter table

`SETTIN` (line 1207) parses `imogen_settings.txt` line-by-line. Format is `LABEL <space> VALUE [! comment]`. Any unrecognised label is logged via `'Skipping invalid label "',LABEL,'" at line ',LINE` (line 1423) and silently ignored.

The complete recognised label set (from the `SELECT CASE` block, lines 1294–1424):

| # | Label | Type | Units / values | Default in `imogen_settings_tmpl.txt` | What it controls |
|---:|---|---|---|---|---|
| 1 | `DIR_PATT` | path | — | `$IMOGENPATH/patterns/$IMOGENPATTERN/` | GCM-analogue pattern dir (used by `GCM_ANLG`) |
| 2 | `DIR_CLIM` | path | — | `$IMOGENPATH/CRUNCEP_1960_1989` | Base-climatology dir (`/jan1`, `/feb2`, …) |
| 3 | `DIR_COMMON` | path | — | `$WORKPATH` | Root for the LPJG↔IMOGEN handshake & per-year output |
| 4 | `FILE_SCEN_EMITS` | path | — | `$IMOGENPATH/emiss/$IMOGENEMISSIONS` | Anthropogenic CO2 emissions time series |
| 5 | `FILE_NON_CO2_VALS` | path | — | `$IMOGENPATH/emiss/$IMOGENRFNONCO2` | Prescribed non-CO2 RF time series (year, W m⁻²) |
| 6 | `FILE_CH4_N2O_EMITS` | path | — | `$IMOGENPATH/emiss/$IMOGENEMISSCH4N2O` | Anthropogenic CH4/N2O emissions (used by FAIR) |
| 7 | `FILE_LPJG_FLUX` | path | — | `imogen_lpjg_flux.txt` | LPJG-supplied land C flux file (relative to `<DIR_COMMON>/LPJG_main/IMOGEN/`) |
| 8 | `FILE_LPJG_CH4_N2O_FLUX` | path | — | `imogen_lpjg_ch4_n2o_flux.txt` | LPJG-supplied CH4/N2O flux file |
| 9 | `FILE_SCEN_CO2_PPMV` | path | — | `$CO2CONCFILE` | Prescribed CO2 ppmv file (only used when `C_EMISSIONS=.FALSE.`) |
| 10 | `FILE_GRIDLIST` | path | — | (not in tmpl; in active settings.txt → `gridlist_hurtt_RNDM_midpoint_3698.txt`) | Output gridlist for `REGRID_CLIM` |
| 11 | `STEP_DAY` | INTEGER | sub-daily steps | 1 | `NSDMAX` upper bound for sub-day disaggregation |
| 12 | `T_OCEAN_INIT` | REAL | K | 289.28 | Initial ocean SST for `OCEAN_CO2` |
| 13 | `KAPPA_O` | REAL | W m⁻¹ K⁻¹ | 280.0 | Ocean eddy diffusivity (`DELTA_TEMP`) |
| 14 | `F_OCEAN` | REAL | fraction | 0.71 | Fractional ocean coverage |
| 15 | `LAMBDA_L` | REAL | W m⁻² K⁻¹ | 0.4 | Inverse climate sensitivity over land |
| 16 | `LAMBDA_O` | REAL | W m⁻² K⁻¹ | 1.9 | Inverse climate sensitivity over ocean |
| 17 | `MU` | REAL | — | 1.78 | Land/ocean ΔT amplification ratio |
| 18 | `Q2CO2` | REAL | W m⁻² | 3.74 | RF for CO2 doubling |
| 19 | `TAU_DECAY_CH4` | REAL | yr | 9.3 | CH4 atmospheric lifetime |
| 20 | `TAU_DECAY_N2O` | REAL | yr | 121 | N2O atmospheric lifetime |
| 21 | `FILE_NON_CO2` | LOGICAL | T/F | T | If T, read non-CO2 RF from `FILE_NON_CO2_VALS`; if F, use built-in HadCM3 array |
| 22 | `NYR_NON_CO2` | INTEGER | years | 251 | # years in `FILE_NON_CO2_VALS`. Hard cap 300 (`RADF_NON_CO2` line 3522). |
| 23 | `NONCO2_EMISSIONS` | LOGICAL | T/F | T | Use FAIR for CH4/N2O forcing |
| 24 | `NONCO2_EMISSIONS_LPJG` | LOGICAL | T/F | T | If T, add LPJG-supplied natural CH4/N2O fluxes |
| 25 | `CO2_INIT_PPMV` | REAL | ppmv | 296.57 | Initial CO2 (template) / 286.085 in active settings (CO2 reference for FAIR & RADF_CO2) |
| 26 | `CH4_INIT_PPBV` | REAL | ppbv | 865.0 | Initial CH4 |
| 27 | `N2O_INIT_PPBV` | REAL | ppbv | 277.4 | Initial N2O |
| 28 | `NYR_EMISS_NONCO2` | INTEGER | years | 251 | # years in `FILE_CH4_N2O_EMITS` |
| 29 | `NYR_EMISS` | INTEGER | years | 251 | # years in `FILE_SCEN_EMITS` |
| 30 | `NYR_LPJG_FLUX` | INTEGER | years | 1 (tmpl), 251 (active) | # years per call in the LPJG flux file (in coupled mode, normally 1 per year) |
| 31 | `C_EMISSIONS` | LOGICAL | T/F | T | T → CO2 ppmv computed from emissions; F → read from `FILE_SCEN_CO2_PPMV` |
| 32 | `LPJG_CFLUX` | LOGICAL | T/F | T (tmpl), F (active) | Take land C flux from LPJG instead of internal model |
| 33 | `INCLUDE_CO2` | LOGICAL | T/F | T | Allow CO2 to update RF |
| 34 | `INCLUDE_NON_CO2` | LOGICAL | T/F | T | Allow non-CO2 to update RF |
| 35 | `DAILYOUT` | LOGICAL | T/F | F | Write daily (vs. monthly) climate output |
| 36 | `LAND_FEED` | LOGICAL | T/F | T | Apply land-CO2 feedback |
| 37 | `OCEAN_FEED` | LOGICAL | T/F | T | Apply Joos ocean uptake |
| 38 | `ANLG` | LOGICAL | T/F | T | Use the GCM analogue model |
| 39 | `ANOM` | LOGICAL | T/F | T | Apply anomalies (vs. base climatology only) |
| 40 | `REGRID` | LOGICAL | T/F | T | Run nearest-neighbour regrid via `REGRID_CLIM` |
| 41 | `CO2_RF_FAIR` | LOGICAL | T/F | F | Use FAIR's CO2 RF formula (overwrites `Q_CO2` after `RADF_CO2`) |

`SETTIN_LPJG` (line 1439) reads `<DIR_COMMON>/LPJG_main/IMOGEN/imogen_lpjg.txt`; recognised labels are `YEAR1`, `IYEND`, `YEAR1_LPJG`, `SPINUP`, `KEEPRUNNING`, `FIRSTCALL`. Anything else is silently skipped (line 1493, no label echoed in the unpatched code — see §12).

> **Settings honored vs ignored:** every label in the table above is read AND used. The only currently-known *partial* honoring is `STEP_DAY`: the comment at line 1224 notes "Formerly set to 24, appeared to cause random unreproducible segmentation fault on change to 1". `MTHDAY` (28-day Feb) is hard-coded irrespective of any leap-year setting.

---

## 6. Pattern-scaling logic

The pattern-scaling implementation lives entirely in `GCM_ANLG` (`imogen_lpjg.f` lines 3103–3251).

### Call site
Inside the main year loop (single CALL):

```3103:3108:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
      SUBROUTINE GCM_ANLG(Q,LAND_PTS,T_ANOM_AM,PRECIP_ANOM_AM,
     &     RH15M_ANOM_AM,UWIND_ANOM_AM,VWIND_ANOM_AM,DTEMP_ANOM_AM,
     &     PSTAR_HA_ANOM_AM,SW_ANOM_AM,LW_ANOM_AM,
     &     N_OLEVS,DIR_PATT,F_OCEAN,KAPPA_O,LAMBDA_L,LAMBDA_O,MU,
     &     DTEMP_O,LONGMIN_AM,LATMIN_AM,
     &     LONGMAX_AM,LATMAX_AM,MM)
```

### Algorithm (per IYEAR)
1. Compute total RF `Q = Q_CO2 + Q_NON_CO2 [+ Q_CH4 + Q_N2O]` (lines 660–682 in main).
2. On the **first month** of the year, `GCM_ANLG` calls `DELTA_TEMP` (line 3203) which steps the two-box land/ocean model 20 times per year and returns the new global-land temperature anomaly `DTEMP_L`.
3. For **each month** (loop `IM=1..MM`):
   - Build `DRIVER_PATT = trim(DIR_PATT) // '/' // 'jan'|'feb'|…|'dec'` (line 3216).
   - `OPEN(51, FILE=DRIVER_PATT, STATUS='OLD')`.
   - Read header: `LONGMIN_AM, LATMIN_AM, LONGMAX_AM, LATMAX_AM` (line 3219).
   - For each of the 1631 land points read 12 per-K coefficients:
     ```3226:3231:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
              READ(51,*)LONG_AM(L),LAT_AM(L),DT_C_PAT,DRH15M_PAT
         &,       DUWIND_PAT,DVWIND_PAT
         &,       DLW_C_PAT,DSW_C_PAT
         &,       DDTEMP_DAY_PAT,DRAINFALL_PAT
         &,       DSNOWFALL_PAT,DPSTAR_C_PAT
     ```
   - Multiply each pattern coefficient by `DTEMP_L`:
     ```3232:3244:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
              T_ANOM_AM(L,IM) = DT_C_PAT * DTEMP_L
              RH15M_ANOM_AM(L,IM) = DRH15M_PAT * DTEMP_L
              UWIND_ANOM_AM(L,IM) = DUWIND_PAT * DTEMP_L
              VWIND_ANOM_AM(L,IM) = DVWIND_PAT * DTEMP_L
              RAINFALL_ANOM_AM(L,IM) = DRAINFALL_PAT * DTEMP_L
              SNOWFALL_ANOM_AM(L,IM) = DSNOWFALL_PAT * DTEMP_L
              DTEMP_ANOM_AM(L,IM) = DDTEMP_DAY_PAT * DTEMP_L
              LW_ANOM_AM(L,IM) = DLW_C_PAT * DTEMP_L
              SW_ANOM_AM(L,IM) = DSW_C_PAT * DTEMP_L
              PSTAR_HA_ANOM_AM(L,IM) = DPSTAR_C_PAT * DTEMP_L
     
              PRECIP_ANOM_AM(L,IM) = RAINFALL_ANOM_AM(L,IM) +
         &                           SNOWFALL_ANOM_AM(L,IM)
     ```

### GCM-pattern selection
`DIR_PATT` is set by a single `imogen_settings.txt` entry (no fallback). The active `code/imogen_settings.txt` selects:
```2:2:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_settings.txt
DIR_PATT C:\GitHub\dbampoh\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Common-directory\IMOGEN-codebase\patterns\CEN_IPSL_MOD_IPSL-CM5A-MR\
```
The 38 candidate pattern dirs are listed in §1. Switching GCM = changing one line in `imogen_settings.txt`.

After `GCM_ANLG` returns, `imogen_lpjg.f` sanity-checks that the pattern's bounding box matches the climatology's bounding box (`LONGMIN_CLIM` … `LATMAX_CLIM`) to within `1e-6` (lines 715–724). Mismatch → write `error` marker and `STOP`.

---

## 7. Per-year output files (the contract with LPJ-GUESS)

All written under `<DIR_COMMON>/IMOGEN/output/<YYYY>/`, where `<YYYY>` is the 4-digit string of `IYEAR`. Format is plain ASCII (Fortran list-directed `*` or explicit `f8.3 / f10.3 / i10` formats).

| File | Written at line | Format (per row) | Content |
|---|---:|---|---|
| `CO2.dat` | 825, 832–848 | If `NONCO2_EMISSIONS=T`: `IYEAR CO2_PPMV CONV*C_EMISS D_LAND_ATMOS D_OCEAN_ATMOS CO2_CHANGE_PPMV CH4_PPBV N2O_PPBV` (8 cols).<br>Else: same up to `CO2_CHANGE_PPMV` (6 cols). | Year's GHG state |
| `T_anom.dat` | 925/984 | `LON LAT  T(month=1) … T(month=12)` (or expanded sub-daily if `DAILYOUT=T`) | Monthly mean 2 m T anomaly (K) |
| `P_anom.dat` | 926/985 | same layout | Total precipitation (mm/day) |
| `SW_anom.dat` | 927/986 | same layout | Downward SW (W/m²) |
| `WET.dat` | 928/987 | `LON LAT W(1) … W(12)` (`i10`) | # wet days/month per cell |
| `DTEMP_anom.dat` | 929/988 | same as `T_anom.dat` | Diurnal temperature range (K) |
| `fa_ocean.dat` | 1059, 1063 | One value per line, `NFARRAY=10000` lines | Ocean–atmosphere C flux history (Joos restart state) |
| `dtemp_o.dat` | 1060, 1066 | One value per line, `N_OLEVS=254` lines | Per-layer ocean ΔT (K) (restart state) |
| `done` | 1050–1052 | Single line `'Climate files written'` | Tells LPJ-GUESS the year is ready |
| `error` | many sites | Single error message | Set on any internal failure; `STOP` follows |

Whether the spatial dimension is `GPOINTS=1631` (native, line 991) or `NGPOINTS=3698` (regridded, line 932) is controlled by the `REGRID` flag.

Auxiliary cumulative files at `<DIR_COMMON>/IMOGEN/`:
- `CO2_all.dat` — append-only mirror of `CO2.dat` rows for the full run (line 826/834/839/845/848).
- `RF_all.dat` — append-only `(IYEAR, Q, Q_CO2, Q_NON_CO2 [, Q_CH4, Q_N2O])` (line 685–693).
- `VARYEAR.dat` — single integer, climate-variability iterator (1..30) (lines 410, 421).

---

## 8. "done"-file marker — exact write location and timing

There are **two** `done` files in this protocol; do not confuse them:

### LPJG → IMOGEN  (`<DIR_COMMON>/LPJG_main/IMOGEN/done`)
Written by LPJ-GUESS after it has finished writing the year's flux files.
- IMOGEN polls for it inside the wait loop:
  ```357:358:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
          INQUIRE(FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
       &  'done',EXIST=DONE_EXIST)
  ```
- It is required (`DONE_EXIST` AND-ed) before the loop exits at line 386–390.
- IMOGEN deletes it once the year's inputs have been read:
  ```591:593:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
            !Remove the "done" marker file
            OPEN(65,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//'done')
            CLOSE(65,STATUS='DELETE')
  ```
- `SETTIN_LPJG` also tries to delete it at line 1498–1500.

### IMOGEN → LPJG  (`<DIR_COMMON>/IMOGEN/output/<YYYY>/done`)
Written **only** when the climate output for the year has been fully flushed:

```1049:1052:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
          !Write a temporary file to tell LPJ-GUESS that IMOGEN has completed writing the climate files - TP 29.07.15
          OPEN(97,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'done',STATUS='REPLACE')
          WRITE(97,*)'Climate files written'
          CLOSE(97)
```

This write is **conditional** on the surrounding block at lines 860–861:
```
IF(ANLG.AND.ANOM.AND.(STEP_DAY.EQ.1).AND.(MM.EQ.12).AND.(MD.EQ.30)) THEN
  ! … build *_M arrays, regrid (if REGRID), write *_anom.dat …
  ! … write done
ENDIF
```
That is: if any of `ANLG`, `ANOM`, `STEP_DAY=1`, `MM=12`, `MD=30` is not satisfied, **no `done` is written and LPJ-GUESS will deadlock**. `MM=12` and `MD=30` are PARAMETERs (lines 38–39) so always true; the practical gates are `ANLG=T`, `ANOM=T`, `STEP_DAY=1`.

---

## 9. Coupling-specific code paths

The "coupling" modifications are interleaved with the original IMOGEN flow. The important guarded blocks are:

### A. Settings + handshake plumbing
- `SETTIN_LPJG` (1439–1504): a second settings reader for per-call values supplied by LPJ-GUESS.
- The `DO WHILE (RUNNOW.EQV..FALSE.)` poll loop (351–404).
- The outer `DO WHILE (KEEPRUNNING)` (339–1077) — IMOGEN never returns to OS until LPJ-GUESS sets `KEEPRUNNING=.FALSE.`.

### B. `LPJG_CFLUX` path  (read LPJG land C flux instead of internal LAND_FEED)
Read site:
```562:594:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
C Get land emissions/uptake from LPJ-GUESS - TP 13.07.15
        IF(C_EMISSIONS.AND.INCLUDE_CO2.AND.ANOM.AND.ANLG.AND.
     &   LAND_FEED.AND.LPJG_CFLUX) THEN
          OPEN(63,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     &      FILE_LPJG_FLUX)
          DO N=1,NYR_LPJG_FLUX
            READ(63,*) YR_LPJG(N),C_LPJG(N)
            …
          ENDDO
          CLOSE(63)
```
Apply site (note the `IYEAR-1` lookup):
```766:794:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
C Include the land carbon cycle feedback - TP 13.07.15
          IF(LAND_FEED.AND.LPJG_CFLUX) THEN
            …
            DO N = 1,NYR_LPJG_FLUX !TODO, SHOULD THIS BE NYR_LPJG_FLUX??
              IF(YR_LPJG(N).EQ.IYEAR-1) THEN !TODO: SHOULD THIS BE IYEAR-1 RATHER THAN IYEAR??? - TP 30.07.15
                C_LPJG_LOCAL=C_LPJG(N)
                D_LAND_ATMOS=CONV*C_LPJG_LOCAL
                CO2_PPMV = CO2_PPMV + D_LAND_ATMOS
                EMISS_TALLY=EMISS_TALLY+1
              ENDIF
            ENDDO
            …
            !Update non-GHG concentrations if necessary
            IF(NONCO2_EMISSIONS) THEN
              CALL FAIR_NON_CO2_GHG_BUDGET(IYEAR,NONCO2_EMISSIONS_LPJG,…)
            ENDIF

          ELSEIF(LAND_FEED) THEN
C Here, temporarily made to be 25% of emissions for all times.
            PRINT *,'WARNING: Land C uptake defaulting to 25% of emissions'
            D_LAND_ATMOS=-CONV*0.25*C_EMISS_LOCAL
            CO2_PPMV = CO2_PPMV + D_LAND_ATMOS
          ENDIF
```
The `ELSEIF(LAND_FEED)` branch (lines 796–800) is the legacy "no-LPJG" stub: it sets land uptake to **−25 % of anthropogenic emissions**, an obvious placeholder.

### C. `NONCO2_EMISSIONS_LPJG` path
- Optional read of LPJG-supplied CH4/N2O fluxes (lines 575–589).
- `FAIR_NON_CO2_GHG_BUDGET` (in `nonco2.f`) adds these on top of the anthropogenic CH4/N2O when the flag is true (lines 122–141 of `nonco2.f`).

### D. `CO2_RF_FAIR` path
- After standard `RADF_CO2`, FAIR's CO2 RF (`Q_CO2_FAIR`) is computed inside `FAIR_NON_CO2_GHG`.
- If `CO2_RF_FAIR=T`, `Q_CO2_FAIR` overwrites `Q_CO2`:
  ```670:672:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
                  IF(CO2_RF_FAIR) THEN
                    Q_CO2=Q_CO2_FAIR
                  ENDIF
  ```

### E. `nonco2.f` — subroutine list

| Line | Symbol | Role |
|---:|---|---|
| 13 | `SUBROUTINE FAIR_NON_CO2_GHG` | Compute FAIR (Smith et al. 2018) RF expressions for CO2/CH4/N2O given current concentrations and pre-industrial reference (`*_INIT_*`). Returns `Q_CH4`, `Q_N2O`, `Q_CO2_FAIR` (W m⁻²). |
| 50 | `SUBROUTINE FAIR_NON_CO2_GHG_BUDGET` | Box-model update of `CH4_PPBV`, `N2O_PPBV` for the year. Sums anthropogenic emissions (from `CH4_EMISS`, `N2O_EMISS`) and, if `NONCO2_EMISSIONS_LPJG=T`, LPJG natural fluxes (from `CH4_LPJG`, `N2O_LPJG`); converts Tg/yr → kg/yr → mol-mixing-ratio increment, then applies `C[t] = C[t-1] + δC[t] - C[t-1]·(1 - exp(-1/τ))`. Writes an `error` file and `STOP`s on year-mismatch. |

### F. The `VARYEAR` mechanism
`<DIR_COMMON>/IMOGEN/VARYEAR.dat` carries an integer that cycles 1..30 between calls, used to pick which file in `CRUNCEP_1960_1989/` (`jan<VARYEAR>` etc.) to use. This is the climate-variability cycling baked into the coupling (lines 407–425).

---

## 10. Gridlist size limitation — root cause

The user reports that "large gridlists won't run". The Fortran code uses **fixed-size arrays declared via `PARAMETER`** for every spatial dimension. To change them you must recompile.

### Primary culprits

`GPOINTS = 1631` — **internal IMOGEN climatology grid size** (and thus the size of every per-month pattern file in `patterns/`):
```186:188:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
      INTEGER
     & GPOINTS           !IN Number of points, not including Antartica
      PARAMETER(GPOINTS=1631)
```
This is propagated into every climate array dimension `(GPOINTS,MM,MD,NSDMAX)` etc. for `T_OUT`, `SW_OUT`, … `LAT(GPOINTS)`, `LONG(GPOINTS)`. Because the climatology files (`CRUNCEP_1960_1989/jan1` etc.) and the pattern files (`patterns/<GCM>/jan` etc.) are all sized to 1631 cells, this number **cannot be raised at runtime** without (a) recompiling and (b) regenerating those climatology and pattern files.

`NGPOINTS = 3698` — **output gridlist size for `REGRID_CLIM`**:
```289:290:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
      INTEGER NGPOINTS !Number of grid points in new gridlist used for nearest-neighbour regridding - TP 06.08.15
      PARAMETER(NGPOINTS=3698) !NOTE: Needs to be hard-coded consistent with gridlist file - TP 06.08.15
```
This is the **direct hard limit on the user-facing gridlist size**. The original backup uses `3711` (see §11). `REGRID_CLIM` reads `FILE_GRIDLIST` row by row and stops with `'Gridlist file and NGPOINTS not compatible'` if it sees more than `NGPOINTS+1` rows:
```1164:1170:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
        IF (CC.GT.(NGPOINTS+1)) THEN
          PRINT *,'ERROR: Gridlist file and NGPOINTS not compatible'
          OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
          WRITE(98,*)'Gridlist file and NGPOINTS not compatible'
          CLOSE(98)
          STOP
        ENDIF
```
And the regridded output arrays are dimensioned `(NGPOINTS, 12, 32, NSDMAX)`:
```292:296:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
      REAL
     & T_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)    !OUT Regridded calculated temperature for 365 day year - TP 06.08.15
     &,P_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)    !OUT Regridded calculated total precipitation for 365 day year - TP 06.08.15
     &,SW_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)   !OUT Regridded calculated shortwave radiation for 365 day year - TP 06.08.15
     &,DTEMP_OUT_M_REGRID(NGPOINTS,MM,32)       !OUT Regridded calculated daily temperature range for 365 day year - TP 03.02.16
```
Memory cost grows linearly: at `NGPOINTS=3698`, `NSDMAX=24`, the four regrid arrays alone take ≈ `3698·12·32·24·4 B · 3 + 3698·12·32·4 B` ≈ 410 MB on the stack. Pushing `NGPOINTS` much higher quickly hits stack-size limits even after recompile.

### Secondary fixed-size arrays (also gridlist- or run-sensitive)

| Where | Constant | Practical limit |
|---|---|---|
| L 88 | `NFARRAY=10000` | Max `YEAR_RUN*NCALLYR(=20)` ⇒ ~500 yr per spin-up before `OCEAN_CO2` overflows |
| L 104 | `N_OLEVS=254` | Ocean diffusion levels |
| L 152–160 | `YR_EMISS(300)`, `C_EMISS(300)`, `YR_LPJG(300)`, `C_LPJG(300)`, `CH4_EMISS(300)`, `N2O_EMISS(300)`, `CH4_LPJG(300)`, `N2O_LPJG(300)`, `YR_LPJG_NONCO2(300)` | Hard cap of 300 entries per file (also enforced by `NYR_NON_CO2.GT.300` check in `RADF_NON_CO2`, line 3522). Note: the same `300` appears in `nonco2.f` arrays. |

> **Bottom line:** the gridlist limit is `NGPOINTS` (`code/imogen_lpjg.f:290`); raising it requires editing that line, recompiling, and checking the host has enough stack/heap for the regrid arrays. The internal climatology grid `GPOINTS=1631` is a deeper limit that requires regenerating the pattern + climatology files.

---

## 11. `Original Imogen Modified for LPJG Coupling/` vs current — diff summary

`code/Original Imogen Modified for LPJG Coupling/imogen_lpjg.f` is a single-file backup that pre-dates the current `code/imogen_lpjg.f`. A unified diff is 349 lines long (`diff -u` between the two). Substantive differences only (cosmetic and trailing-whitespace differences omitted):

| Theme | Original | Current | Notes |
|---|---|---|---|
| `NGPOINTS` PARAMETER | `3711` | `3698` | Indicates a different default Hurtt gridlist (see `gridlist_hurtt_RNDM_midpoint_3711.txt` vs `..._3698.txt`). |
| LPJG `done` polling | The `INQUIRE` on `done` was commented out (`C` prefixed) and `DONE_EXIST=.TRUE.` was forced | `INQUIRE(...) `done` ... ` re-enabled and `DONE_EXIST=.TRUE.` is now `! DONE_EXIST=.TRUE.` (line 349) | Restores year-by-year synchronisation. The original effectively skipped the handshake. |
| `SLEEP` argument | `CALL SLEEP(2)` | `CALL SLEEP(3)` | Tiny pacing tweak. |
| `mkdir` paths | A *commented* Linux variant (`mkdir -p ...` with forward slashes) was present alongside the active Windows one | The Linux comment lines were *removed* | Only the Windows backslash mkdir remains (still a portability problem; see §13). |
| Variability path | `OPEN(97,FILE=...//'\IMOGEN\VARYEAR.dat')` (backslash) | `OPEN(97,FILE=...//'/IMOGEN/VARYEAR.dat')` (forward slash) | Mixed slash conventions across the file remain. |
| Non-CO2 write of CO2.dat | Always `WRITE(91,*) IYEAR,CO2_PPMV,0.0,0.0,0.0,0.0` in the no-feedback branch | Branches on `NONCO2_EMISSIONS` and writes 8 vs 6 columns | This *is exactly the change in `patch_add_ch4_n2o_conc.diff`* — the patch has been applied to the current file. |
| Settings `Skipping invalid label` | `'Skipping invalid label at line ',LINE` | `'Skipping invalid label "',LABEL,'" at line ',LINE` | The other half of `patch_add_ch4_n2o_conc.diff`. |
| Year matching guard | `IF(YR_EMISS(N).EQ.IYEAR-1)THEN` (no space) and a duplicate commented copy below | One clean line | Refactor only. |
| `INVERT` matrix-check | `!STOP` (commented) | `STOP` re-enabled | Original would silently continue on tridiagonal-inverter mismatch. |
| `QSAT` debug instrumentation | none | Adds an `OPEN`/`WRITE` block that dumps every `QSAT` call to `qsat_output.txt` and a final `PAUSE` (lines 4116–4138) | Debug instrumentation **left in production** (see §13). |
| Diagnostic `PRINT *` block | none | Many extra `PRINT *,"RUNNOW_EXIST =", …` lines before the wait-loop exit (lines 373–384) | Purely diagnostic. |
| Misc. `PRINT *, 'CO2 CHANGE PPV = …'` | none | Added at line 815 | Debug. |
| Stray inserted text in declarations | `LONGMAX_DAT` clean | `LON  GMAX_DAT` (extra whitespace) at line 268, also a `FILE_NON_CO2 ... non-CO2 radiative forcings ar` truncation | Harmless in fixed-form Fortran (it's read as the same identifier and its trailing comment), but reflects sloppy editing. |

**Conclusion:** the `Original Imogen Modified for LPJG Coupling/imogen_lpjg.f` file is a **near-identical backup** kept in-tree. The current `code/imogen_lpjg.f` is the diverged active version, which (a) restores the LPJ-GUESS `done`-file handshake, (b) folds in `patch_add_ch4_n2o_conc.diff`, (c) switches `NGPOINTS` to 3698, (d) re-enables a `STOP` in `INVERT`, and (e) accumulates a layer of debugging instrumentation (`PAUSE`/`PRINT *`/the `qsat_output.txt` dump). It is **not a clean refactor**, just a working snapshot.

---

## 12. `patch_add_ch4_n2o_conc.diff` — what it does

The patch is 16 lines and applies to `code/imogen_lpjg.f`. Two hunks:

1. **Hunk 1 (around line 811–816 of the *pre-patch* code)**: in the `ELSE` branch where the run is *not* using all of `INCLUDE_CO2 + C_EMISSIONS + ANLG + ANOM + OCEAN_FEED + LAND_FEED`, the writes to units `91` (`CO2.dat`) and `98` (`CO2_all.dat`) previously always emitted 6 numeric columns. The patch makes them branch on `NONCO2_EMISSIONS`:
   - If `NONCO2_EMISSIONS=.TRUE.`: append `CH4_PPBV, N2O_PPBV` so every row becomes 8 numeric columns.
   - Else: keep the 6-column form.
   
   This is necessary because the *other* branches of the same `IF` block (the ones that *do* satisfy all the flags) already produced 8-column output when `NONCO2_EMISSIONS=T`, so without the patch the `CO2.dat` schema becomes inconsistent across years/branches and downstream readers break.

2. **Hunk 2 (around `RADF_CO2_FAIR` settings parser)**: in `SETTIN` the default-case `PRINT` becomes:
   `PRINT *,'Skipping invalid label "',LABEL,'" at line ',LINE`
   so the offending label name is logged, not just the line number — a diagnostic improvement only.

Both hunks are already reflected in the current `code/imogen_lpjg.f` (see §11), so the patch is a record of changes that have already landed.

---

## 13. Bugs, dead code, hardcoded paths, TODO/FIXME

### Production bugs / smells

1. **`PAUSE` left in `QSAT`** (`imogen_lpjg.f:4134`):
   ```4131:4134:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
         !DO I = 1, NPNTS
         ! PRINT *, 'QS(', I, ') = ', QS(I), ' T(', I, ') = ', T(I), ' P(', I, ') = ', P(I)
         !END DO
         PAUSE
   ```
   `QSAT` is called inside `DAY_CALC` for every grid point, every sub-day step, every day, every month. With `PAUSE` enabled the program halts at the first call awaiting an interactive keystroke. This is a debug remnant that **must be removed** for any non-interactive run.

2. **`qsat_output.txt` overwrite per call** (`imogen_lpjg.f:4120–4128`): every `QSAT` invocation `OPEN`s and `WRITE`s the same file with `STATUS='UNKNOWN'` and never `CLOSE`s before the next call. Wasteful I/O and a file-handle leak.

3. **Hard-coded Windows path separators** in `mkdir` calls (lines 435 and 461):
   ```
   CALL SYSTEM('mkdir '//TRIM(ADJUSTL(DIR_COMMON))//'\IMOGEN\output\'//THISYEAR)
   ```
   Will silently fail on Linux/macOS because `mkdir` interprets `\IMOGEN\…` as one weird filename. Note line 116 in `nonco2.f` uses forward slashes for the *same* directory:
   ```
   OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',…)
   ```
   so the slash convention is inconsistent throughout. (POSIX paths happen to work because most `OPEN`/`INQUIRE` rely on forward slashes, but the `mkdir` calls do not.)

4. **Hard-coded Windows-only paths in `imogen_settings.txt`**:
   ```1:6:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_settings.txt
   DIR_COMMON C:\GitHub\dbampoh\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Common-directory
   DIR_PATT C:\GitHub\dbampoh\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Common-directory\IMOGEN-codebase\patterns\CEN_IPSL_MOD_IPSL-CM5A-MR\
   …
   FILE_SCEN_EMITS C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Data\Imogen\emiss\DKB_dataset_totals\co2_emissions_annual_historical_rcp85_allsources.txt
   ```
   The template `imogen_settings_tmpl.txt` parameterises these via shell-style `$VARS`, but no in-tree script exists that turns the template into the active file (the MATLAB driver in this repo's parent presumably does it).

5. **Hard-coded Windows path in `code/.vscode/settings.json`** (the `fortls.path` to a specific user's AppData) — harmless to runs but commits a personal path.

6. **Mixed `\` and `/` inside the same Fortran file** (lines 410, 421 use `/`; lines 435, 461 use `\`).

7. **Stray malformed declaration**:
   ```268:268:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/code/imogen_lpjg.f
         REAL LATMIN_DAT,LATMAX_DAT,LONGMIN_DAT,LON  GMAX_DAT     !Anomaly pa
   ```
   In fixed-form Fortran the embedded space in `LON  GMAX_DAT` is silently ignored, so it parses as `LONGMAX_DAT`. Variables `LATMIN_DAT`, `LATMAX_DAT`, `LONGMIN_DAT`, `LONGMAX_DAT` are then never used anywhere else — **dead code** for the prescribed-anomaly path that the LPJG version never exercises.

8. **`LAND_FEED` legacy stub** (`imogen_lpjg.f:796–800`): if `LAND_FEED=T` AND `LPJG_CFLUX=F`, the model uses a hard-coded land uptake of −25 % of anthropogenic emissions (`D_LAND_ATMOS = -CONV*0.25*C_EMISS_LOCAL`) and prints `WARNING: Land C uptake defaulting to 25% of emissions`. Surely a placeholder.

9. **`F_WET_CLIM_OUT` rounding patch** (lines 909–913) silently bumps wet-day count to 1 when total monthly precip ≥ 0.5 µm; harmless but undocumented.

10. **`OPEN(98,..., 'CO2_all.dat', ACCESS='APPEND', STATUS='REPLACE')`** at line 332 — `STATUS='REPLACE'` plus `ACCESS='APPEND'` is contradictory. With gfortran `STATUS='REPLACE'` wins, truncating the file. So `CO2_all.dat` is reset at the start of *every* `imogen_lpjg.exe` invocation — only OK in single-run mode.

11. **`OPEN(82,…); CLOSE(82,STATUS='DELETE')`** in `SETTIN_LPJG` (lines 1498–1500) deletes `LPJG_main/IMOGEN/done` after parsing `imogen_lpjg.txt`. But `done` is *also* deleted at line 593 inside the year loop — duplicated logic.

12. **`SETTIN_LPJG` `CASE DEFAULT`** (line 1493) does **not** echo the offending label, only `'Skipping invalid label at line ',LINE` — easy source of silent settings-typo bugs. (`SETTIN`'s default branch was patched to echo the label; `SETTIN_LPJG`'s was not.)

13. **`patterns/readme.log`** is not present as a true README; it sits next to the GCM dirs but its content was not opened — its name is just `.log`, so any human-readable docs about the GCM patterns may live there. (Flagged as uncertainty.)

14. **`gridlist_global.txt` (13 rows)** would crash `REGRID_CLIM` because `NGPOINTS=3698` but the file has only 13 lines: `READ(21,…)` would race past EOF into uninitialised memory in `LON_OUT(14..3698)`. The IOSTAT loop exits cleanly only because `IF(IOS.NE.0) CONTINUE` (line 1161) is a no-op. So tiny gridlists silently produce garbage anomalies.

### Explicit `TODO`/`FIXME` markers in source (`grep "TODO|FIXME"`)

| Line | Comment |
|---:|---|
| 623 | `!TODO: CONSIDER ADDING IN THE CONCENTRATION READING FOR CH4 AND N2O HERE!!` |
| 751 | `!TODO: SHOULD THIS BE IYEAR-1 RATHER THAN IYEAR??? - TP 30.07.15` |
| 770 | `!DO N = 1,NYR_EMISS !TODO, SHOULD THIS BE NYR_LPJG_FLUX??` |
| 771 | `DO N = 1,NYR_LPJG_FLUX !TODO, SHOULD THIS BE NYR_LPJG_FLUX??` |
| 772 | `!TODO: SHOULD THIS BE IYEAR-1 RATHER THAN IYEAR??? - TP 30.07.15` |
| 1280 | `OPEN(81,FILE='imogen_settings.txt') !TODO: Update folder path appropriately - TP 03.08.15` |
| `nonco2.f:6` | `!TODO??:  2.1.3 Methane oxidation to CO2 ???? eq. 6` |
| `nonco2.f:107` | `!TODO: SHOULD THIS BE IYEAR-1 RATHER THAN IYEAR??? - TP 30.07.15` |
| `nonco2.f:127` | (same) |
| `nonco2.f:159` | `!CHECK: do we need to use mol weight of n2 or n2o here, since we converted to TgN2eq/yr above????` |

The repeated `IYEAR vs IYEAR-1` TODOs reveal lingering ambiguity in the year-indexing of the LPJG/Anthro flux read — relevant when checking C-cycle conservation between LPJG and IMOGEN.

### Dead/instrumentation code worth removing

- The `PAUSE` at `imogen_lpjg.f:4134` and the surrounding `qsat_output.txt` dump.
- The 12-line block of `PRINT *, "…"` between lines 373 and 384.
- The commented-out `!OPEN(UNIT=99, FILE='B_qsat_output.txt', …); !PAUSE` block at 1764–1770.
- Multiple `!PAUSE` comments at 384, 678, 713, 1770.
- `PRINT *,'YR_LPJG_NONCO2(N) ',YR_LPJG_NONCO2(N)` inside `nonco2.f` (line 126) — printed once per year inside an inner loop that runs `NYR_LPJG_FLUX` times.

---

## 14. Open questions

1. **Year-indexing convention** — Three TODO comments (`imogen_lpjg.f:751,772`, `nonco2.f:107,127`) flag uncertainty over whether emissions/fluxes for `IYEAR` should be read from row `IYEAR` or `IYEAR-1`. Does LPJ-GUESS write its flux file with the year header equal to the simulated year, or to "year just completed"? Confirming this against the LPJG side (Subagent 2) is essential before trusting any C-budget closure.

2. **`NGPOINTS` raise procedure** — What is the practical upper limit on the user-facing gridlist? Stack-size constraints (the regrid arrays alone are tens to hundreds of MB) imply that simply editing the PARAMETER may not be enough; a heap-allocated alternative may be required.

3. **Pattern-file consistency** — Each `patterns/<GCM>/<month>` file must be exactly 1 header + 1631 lines on the *same* IMOGEN gridlist. Is this guaranteed for *every* GCM in `patterns/`? (Only `CEN_IPSL_MOD_IPSL-CM5A-MR/jan` was verified here, at 1632 lines.) If not, `GCM_ANLG`'s sequential `READ` will silently misalign.

4. **`DIR_PATT` trailing slash** — `imogen_settings.txt` ends `DIR_PATT` with `\` and `GCM_ANLG` does `DRIVER_PATT = DIR_PATT(:II)//'/jan'`. That yields `…CM5A-MR\/jan` — works on Windows but on Linux the leading backslash inside the path is an opaque character that may break OS-level open. Worth confirming with a Linux dry-run.

5. **`CRUNCEP_1960_1989/`** — The `VARYEAR` mechanism cycles 1..30 to pick `<month><n>` files. With 30 years from 1960–1989, we presume `jan1`=1960, `jan30`=1989. There is no documentation of this mapping in the codebase; an authoritative readme is missing.

6. **`patterns/readme.log`** content — not opened in this report (file extension suggests a logfile, not docs). Worth confirming whether it documents GCM-pattern provenance.

7. **`R_wrappers/`** — assumed to be standalone-IMOGEN driver/analysis scripts (file names match a GCP2015/RCP2.6 setup workflow), but not opened. Confirm they are *not* part of the coupled flow.

8. **`emiss/rcp_database/` and `emiss/new_emission_data/`** — provenance of the emissions/RF time series consumed by `FILE_SCEN_EMITS`, `FILE_NON_CO2_VALS`, `FILE_CH4_N2O_EMITS` is not documented in-tree. The `historical_all_rcp_*.xls` spreadsheets in `emiss/DKB_dataset_totals/` likely contain the raw provenance.

9. **`NFARRAY=10000` overflow** — at `NCALLYR=20`, this caps single-segment runs to 500 yr. The runtime check `IF(YEAR_RUN*NCALLYR.GT.NFARRAY) PRINT 'Array size too small for FA_OCEAN'` (line 3332) only **prints** — it does not abort. Long runs would overflow `FA_OCEAN(I)` writes silently. Worth flagging to the C++ refactor (Subagent 4) if any consumer is rewriting the Joos solver.

10. **Restart correctness in multi-year mode** — the per-year `fa_ocean.dat` and `dtemp_o.dat` files contain `NFARRAY=10000` floats each. When `IYEND-YEAR1>0` (multi-year per call), the read at lines 498–514 happens only once at the start of the year-loop — does that cover all coupled use cases? Probably yes if each call is a single year, but worth verifying with the run scripts.

