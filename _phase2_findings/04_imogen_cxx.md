# Subagent 4 — IMOGEN C++ refactor (`IMOGENCXX/ImogenCXX/`)

> Scope: investigate the C++ refactor of the Fortran IMOGEN driver, map its
> structure, identify simplifications/bugs/missing features, and verify (or
> refute) the claim that it can run with larger gridlists than the Fortran
> version. Read‑only investigation; no source files were modified.

All paths in this report are relative to
`landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/`
unless otherwise noted. Fortran reference is
`Common-directory/IMOGEN-codebase/code/imogen_lpjg.f` (3 698 LOC) plus
`Common-directory/IMOGEN-codebase/code/nonco2.f` (175 LOC).

---

## 1. Top‑level structure of `IMOGENCXX`

```
IMOGENCXX/
└── ImogenCXX/
    ├── imogen_settings.txt        # 41 lines, Windows‑pathed
    └── src/
        └── Main.cpp               # 121 KB, 2 631 LOC, single translation unit
```

Observations:
* No header files, no module split, no build system (no CMakeLists, no Makefile,
  no `.vcxproj` other than an unused `.vscode` folder).  The whole IMOGEN port
  lives in a single 2 631‑line `Main.cpp`.
* No `nonco2.cpp` analogue file: `FAIR_NON_CO2_GHG`/`FAIR_NON_CO2_GHG_BUDGET`
  have been folded into `Main.cpp` (lines 76–153) instead of kept in a separate
  TU as in Fortran (`nonco2.f`).
* The Fortran tree provides `nonco2.f`, the IMOGEN `Makefile`, and seven
  pre‑built grid‑list / settings files; none of those have been carried over.
  Only the C++ source and a single `imogen_settings.txt` are present.
* No emitted artifacts (`.o`, executable) in either tree.
* Companion driver tree: `Imogen-controller/` (separate `main()` — see §7).

---

## 2. `Main.cpp` — class / function catalogue

There are **no classes**. Everything is C‑style free functions plus one big
`int main()`. The catalogue (in source order) is:

| # | Lines | Symbol | Purpose / notes |
|---|-------|--------|-----------------|
| 1 | 31–61 | global `const` block | `MM`, `MD`, `NSDMAX`, `NFARRAY=10000`, `OCEAN_AREA`, `N_OLEVS=254`, `CONV=0.471`, **`GPOINTS=1631`**, **`NGPOINTS=3698`**, `MDI=999.9`, FAIR molar masses, `EPSILON`, `T_LOW`/`T_HIGH`/`DELTA_T`, etc. All hard‑wired at compile time, exactly mirroring the Fortran `PARAMETER` constants. |
| 2 | 65–72 | `trim()` | Strip `!`‑comments and surrounding whitespace from a line. |
| 3 | 76–91 | `FAIR_NON_CO2_GHG` | Port of `FAIR_NON_CO2_GHG` from `nonco2.f`. Returns Q_CO2_FAIR, Q_CH4, Q_N2O. Numerically identical formula. |
| 4 | 93–153 | `FAIR_NON_CO2_GHG_BUDGET` | Port of `FAIR_NON_CO2_GHG_BUDGET` from `nonco2.f`. Updates CH4_PPBV, N2O_PPBV. |
| 5 | 155–159 | `RADF_CO2` | Port of Fortran `RADF_CO2`. |
| 6 | 161–219 | `RADF_NON_CO2` | Port of Fortran `RADF_NON_CO2`. |
| 7 | 221–306 | `INVERT` | Tridiagonal solver for ocean column. Allocates dense `N_OLEVS×N_OLEVS` matrices on every call (vs Fortran where `INVERT` worked on the same banded structure but took stack arrays). |
| 8 | 308–367 | `DELTA_TEMP` | Ocean temperature anomaly time stepper, calls `INVERT`. |
| 9 | 369–389 | `RESPONSE` | Ocean impulse response function. |
| 10 | 391–458 | `OCEAN_CO2` | Atmosphere‑ocean CO2 exchange. |
| 11 | 460–508 | `GCM_ANLG` | Reads pattern files (`/jan` … `/dec`), scales by ΔT_L. |
| 12 | 514–717 | **`SETTING`** | Reads `imogen_settings.txt`. **Hard‑coded Windows path** at line 525 — see §4 and §10. |
| 13 | 724–792 | **`SETTING_LPJG`** | Reads `imogen_lpjg.txt`. **Polarity inverted vs Fortran** — see §6 and §10. |
| 14 | 795–809 | `DATE_AND_TIME` | Replacement for Fortran intrinsic. **Uses Windows‑only `localtime_s`** (line 800). |
| 15 | 811–891 | `REGRID_CLIM` | Nearest‑neighbour regridding from native IMOGEN grid (`GPOINTS=1631`) to user gridlist (`NGPOINTS=3698`). |
| 16 | 893–916 | `RNDM` | Pseudo‑random generator (Wichmann‑Hill style). |
| 17 | 918–923 | `SOLPOS` | **STUB** — `SINDEC = sin(2π(d-81)/365)`, `SCS = 1367`. Comment: "Placeholder ... should be replaced". The Fortran `SOLPOS` is a 60‑line orbital‑elements routine; the C++ version returns a flat sinusoid and a constant solar constant. |
| 18 | 925–995 | `SOLANG` | Hour‑angle / cos(zenith) calculator. |
| 19 | 997–1060 | `SUNNY` | Sun fraction over a day. **Bug** at line 1021: `double TIME = (j-1)*TIMESTEP;` with `j` running `0…JDAY-1` produces `-TIMESTEP` for the first step (Fortran indexing was 1‑based so this expression was correct in Fortran). |
| 20 | 1062–1135 | `REDIS` | Precipitation redistribution within a day. |
| 21 | 1137–1162 | **`DAY_CALC`** | **EMPTY STUB.** The body is one block of commented‑out code followed by `};`. This is the function that should disaggregate daily values to sub‑daily (the Fortran `DAY_CALC` is ~462 lines and is the heart of the sub‑daily climate generation). See §9. |
| 22 | 1164–1297 | `CLIM_CALC` | Builds daily fields from monthly clim + anom; calls the empty `DAY_CALC`; never assigns `DTEMP_OUT` (line 1293 is commented out). |
| 23 | 1300–1613 | static `ES[]` | Saturation‑vapour‑pressure table copied verbatim from Fortran `BLOCK DATA`. Has a typo at the start: `0.966483E-02` is duplicated (lines 1301–1302), shifting the table by one entry vs the Fortran (which begins with that value at index 1). |
| 24 | 1615–1650 | `QSAT` | Saturation specific humidity from the table. **Calls `system("pause")`** (line 1648) — Windows‑only. |
| 25 | 1656–2631 | `int main()` | The Fortran `PROGRAM IMOGEN` body, inlined. |

### Functions in the Fortran original that have **no** C++ counterpart

* `PROGRAM IMOGEN` is the Fortran top level; in C++ this is `main()`. (Equivalent.)
* All 16 Fortran subroutines listed at §3 below have a same‑named C++ function,
  but several of them are *named*‑only and not actually implemented (`DAY_CALC`,
  `SOLPOS`, `SUNNY` partially) — see §9.

### Functions that exist in C++ but **not** in Fortran

* `trim()` — utility only.
* `DATE_AND_TIME()` — a re‑implementation of the Fortran intrinsic.

There are no genuinely new physics routines: the C++ does not add anything;
it is purely a port (with omissions).

---

## 3. Cross‑check with Fortran subroutines

| Fortran subroutine (`imogen_lpjg.f` / `nonco2.f`)        | Line (Fortran) | C++ counterpart           | Line (C++) | Faithfulness |
|----------------------------------------------------------|---------------:|---------------------------|-----------:|--------------|
| `PROGRAM IMOGEN`                                         |   16           | `int main()`              | 1656       | mostly faithful, see §9 |
| `REGRID_CLIM`                                            | 1089           | `REGRID_CLIM`             |  811       | faithful     |
| `SETTIN`                                                 | 1207           | `SETTING`                 |  514       | **bug**: hard‑coded Windows settings path (line 525). Reads same key set. |
| `SETTIN_LPJG`                                            | 1439           | `SETTING_LPJG`            |  724       | **bug**: Fortran *deletes* `done` after read; C++ *creates* it (polarity inverted). |
| `DAY_CALC`                                               | 1511           | `DAY_CALC`                | 1137       | **STUB — body is empty.** |
| `REDIS`                                                  | 1973           | `REDIS`                   | 1062       | port present; not exercised because `DAY_CALC` (its only caller in Fortran) is a stub in C++. |
| `SUNNY`                                                  | 2120           | `SUNNY`                   |  997       | port present, off‑by‑one in `TIME = (j-1)*TIMESTEP` (line 1021). |
| `SOLPOS`                                                 | 2267           | `SOLPOS`                  |  918       | **STUB** — replaced by 1‑line sinusoid + constant 1367 W/m². |
| `SOLANG`                                                 | 2332           | `SOLANG`                  |  925       | faithful direct port. |
| `RNDM`                                                   | 2469           | `RNDM`                    |  893       | faithful. |
| `CLIM_CALC`                                              | 2502           | `CLIM_CALC`               | 1164       | partial: monthly→daily expansion present; sub‑daily call goes to empty `DAY_CALC`; `DTEMP_OUT` write is commented out (line 1293). |
| `DELTA_TEMP`                                             | 2752           | `DELTA_TEMP`              |  308       | faithful. |
| `INVERT`                                                 | 2927           | `INVERT`                  |  221       | faithful but allocates 3 dense `254×254` matrices per call. |
| `GCM_ANLG`                                               | 3103           | `GCM_ANLG`                |  460       | faithful. |
| `OCEAN_CO2`                                              | 3253           | `OCEAN_CO2`               |  391       | faithful. |
| `RESPONSE`                                               | 3422           | `RESPONSE`                |  369       | faithful. |
| `RADF_CO2`                                               | 3459           | `RADF_CO2`                |  155       | faithful (extra `cout`). |
| `RADF_NON_CO2`                                           | 3483           | `RADF_NON_CO2`            |  161       | faithful. |
| `QSAT`                                                   | 3618           | `QSAT`                    | 1615       | port plus debug spew + `system("pause")` (line 1648). |
| `FAIR_NON_CO2_GHG` (`nonco2.f` line 13)                  |   13           | `FAIR_NON_CO2_GHG`        |   76       | faithful. |
| `FAIR_NON_CO2_GHG_BUDGET` (`nonco2.f` line 50)           |   50           | `FAIR_NON_CO2_GHG_BUDGET` |   93       | faithful (but called with the wrong flag, see §10). |

**Fortran subroutines without a C++ counterpart:** none — all are named in C++.

**C++ symbols without a Fortran ancestor:** `trim()`, `DATE_AND_TIME` helper.
No physics added.

---

## 4. Settings file (`imogen_settings.txt`)

### Comparison

`IMOGENCXX/ImogenCXX/imogen_settings.txt` is **byte‑for‑byte the same key set**
as the Fortran reference `Common-directory/IMOGEN-codebase/code/imogen_settings.txt`
and the template `…/imogen_settings_tmpl.txt`. All 41 keys in the C++ file are
also present in the Fortran reference; none have been added or removed.

The differences are content‑only (paths and a few values) and they reveal the
Windows‑only nature of the C++ deployment:

```1:9:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/IMOGENCXX/ImogenCXX/imogen_settings.txt
DIR_COMMON C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Common-directory
DIR_PATT C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Common-directory\IMOGEN-codebase\patterns\CEN_IPSL_MOD_IPSL-CM5A-MR\
DIR_CLIM C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Common-directory\IMOGEN-codebase\CRUNCEP_1960_1989\
FILE_SCEN_EMITS C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Data\Imogen\emiss\DKB_dataset_totals\co2_emissions_annual_historical_rcp85_allsources.txt
FILE_NON_CO2_VALS C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Data\Imogen\emiss\DKB_dataset_totals\nonco2_ch4_n2o_RF_historical_rcp85.txt
FILE_CH4_N2O_EMITS C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\Data\Imogen\emiss\DKB_dataset_totals\ch4_n2o_annual_historical_rcp85_non_lpjg_simulated.txt
FILE_LPJG_FLUX extended_lpjg_only_cfluxrcp85.txt
FILE_GRIDLIST gridlist_hurtt_RNDM_midpoint_3698.txt
FILE_LPJG_CH4_N2O_FLUX ch4_n2o_annual_historical_ssp5rcp85_lpjg_simulated_real.txt
```

The template file uses placeholder variables (`$WORKPATH`, `$IMOGENPATH`, …)
and is meant to be expanded by a setup script — that workflow has not been
brought across to the C++ tree.

### What the C++ reads (`SETTING`, lines 547–710)

41 keys, exactly matching the Fortran `SETTIN`:

* Path/file keys: `DIR_PATT`, `DIR_CLIM`, `DIR_COMMON`, `FILE_SCEN_EMITS`,
  `FILE_NON_CO2_VALS`, `FILE_SCEN_CO2_PPMV`, `FILE_LPJG_FLUX`, `FILE_GRIDLIST`,
  `FILE_CH4_N2O_EMITS`, `FILE_LPJG_CH4_N2O_FLUX`.
* Integers: `STEP_DAY`, `NYR_NON_CO2`, `NYR_EMISS`, `NYR_EMISS_NONCO2`, `NYR_LPJG_FLUX`.
* Floats: `T_OCEAN_INIT`, `KAPPA_O`, `F_OCEAN`, `LAMBDA_L`, `LAMBDA_O`, `MU`,
  `Q2CO2`, `TAU_DECAY_CH4`, `TAU_DECAY_N2O`, `CO2_INIT_PPMV`, `CH4_INIT_PPBV`,
  `N2O_INIT_PPBV`.
* Booleans: `FILE_NON_CO2`, `NONCO2_EMISSIONS`, `NONCO2_EMISSIONS_LPJG`,
  `C_EMISSIONS`, `LPJG_CFLUX`, `INCLUDE_CO2`, `INCLUDE_NON_CO2`, `DAILYOUT`,
  `LAND_FEED`, `OCEAN_FEED`, `ANLG`, `ANOM`, `REGRID`, `CO2_RF_FAIR`.

### What the C++ silently ignores

Nothing — every label in the supplied settings file is matched by a `case`
in `SETTING`. Unknown labels print a "Skipping invalid label" warning to
stderr (line 712) and are dropped (same as Fortran).

### What is *new* relative to the Fortran read

Nothing: all keys read by the C++ are also read by `SETTIN` in the Fortran.

### Critical caveat (also in §10)

The settings file path is **hard‑coded** in the C++ source, so the
`imogen_settings.txt` shipped next to the binary is not used unless the user
matches the absolute Windows path:

```525:525:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/IMOGENCXX/ImogenCXX/src/Main.cpp
	std::ifstream settings_file("C:\\GitHub\\dbampoh\\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\\IMOGENCXX\\ImogenCXX\\imogen_settings.txt");
```

The Fortran original opens `imogen_settings.txt` relative to the working
directory:

> `OPEN(81,FILE='imogen_settings.txt')` — `imogen_lpjg.f` line 1280.

This single line breaks portability and reproducibility: a user must literally
edit and recompile `Main.cpp` to point at their settings file.

---

## 5. Gridlist handling — fixed vs dynamic

**Claim under test:** the C++ rewrite can run with larger gridlists than the
Fortran version because it uses dynamic allocation.

**Verdict:** essentially **false**. The C++ does use `std::vector` instead of
fixed‑size Fortran arrays, but the *sizes themselves* are still the same
hard‑coded compile‑time constants:

```39:40:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/IMOGENCXX/ImogenCXX/src/Main.cpp
const int GPOINTS = 1631;   // IN Number of points, not including Antarctica
const int NGPOINTS = 3698; // Number of grid points in new gridlist used for nearest-neighbour regridding - TP 06.08.15
```

These mirror the Fortran `PARAMETER`s:

> `PARAMETER(GPOINTS=1631)` — `imogen_lpjg.f` line 188.
> `PARAMETER(NGPOINTS=3698)` — `imogen_lpjg.f` line 290.

All the climate‑state arrays (`T_ANOM`, `T_CLIM`, `T_OUT_M`, `T_OUT_M_REGRID`,
`F_WET_CLIM_REGRID`, …) are sized at startup using `GPOINTS` / `NGPOINTS` (see
the long block of declarations at lines 1771–1868). Switching to `std::vector`
moves the storage from the BSS to the heap (good — sidesteps the Fortran
stack‑size segfault on large grids) but does **not** make the grid count
configurable. To run a different gridlist the user must (a) edit the two
`const int`s above, (b) edit the `imogen_settings.txt` `FILE_GRIDLIST`, and
(c) rebuild.

The gridlist file path itself **is** read at runtime (`FILE_GRIDLIST` in
settings, used by `REGRID_CLIM` at line 834), and the regridding loop iterates
over `NGPOINTS` rather than reading until EOF; so a gridlist of a different
length will silently misread or run off the end.

Concretely:

* `FA_OCEAN` is `std::vector<double> FA_OCEAN(NFARRAY)` (line 1694, NFARRAY=10000).
* `DTEMP_O` is `std::vector<double> DTEMP_O(N_OLEVS)` (line 1703, N_OLEVS=254).
* All clim/anom 2‑D arrays are `std::vector<std::vector<double>>(GPOINTS, …)`.
* Output 4‑D arrays are `std::vector<std::vector<std::vector<std::vector<double>>>>`
  with first dimension `GPOINTS` or `NGPOINTS` — see lines 1798–1815 and 1859–1862.

**Implication for "larger gridlists":**

* On Linux a Fortran build with `GPOINTS=1631` and `NGPOINTS=3698` typically
  works after `ulimit -s unlimited` because the static arrays sum to
  ~hundreds of MB. On Windows the Fortran tree was reported to segfault for
  some users. The C++ rewrite happens to work around that by heap allocation,
  which is the *only* practical advantage uncovered here.
* For the grid count itself to grow, **`GPOINTS` (and `NGPOINTS`) must still
  be edited and the program rebuilt**, exactly as in Fortran. The C++ does
  not, e.g., open the gridlist first, count the lines, and then size its
  arrays. There is no `vector::reserve(N)` pattern keyed off file length.

So the rewrite buys you "no segfault on large grids on Windows", not
"runtime‑configurable gridlist size".

---

## 6. Output format and `done` marker

### Output files

Per‑year directory: `${DIR_COMMON}/IMOGEN/output/${YYYY}/`. Files written:

| File              | Fortran (`imogen_lpjg.f`) | C++ (`Main.cpp`) | Identical? |
|-------------------|---------------------------|------------------|------------|
| `T_anom.dat`      | `WRITE(92,'(f8.3)',ADVANCE='NO') ...` (lines 925–1037) | `T_anom_file << std::fixed << std::setprecision(3) << ...` (lines 2501–2588) | **No** — same numeric values, but Fortran writes `f8.3`/`f10.3` fixed‑width fields with no separator; C++ writes `<<` with a leading space and only `setprecision(3)`, *no* width. Files are not byte‑identical. |
| `P_anom.dat`      | as above                  | as above         | not byte‑identical |
| `SW_anom.dat`     | as above                  | as above         | not byte‑identical |
| `WET.dat`         | `WRITE(95,'(i10)', …)`     | `<< std::fixed << std::setprecision(3) << F_WET_CLIM_REGRID[…]` | **No** — Fortran writes integer `i10`, C++ writes the same integer value through a float format pipeline (line 2523). |
| `DTEMP_anom.dat`  | values from `DTEMP_OUT_M` | same             | values exist in Fortran; in C++ `DTEMP_OUT` is never assigned (see §9, the commented‑out line 1293), so what gets written here is whatever default‑initialised the vector to (zero). |
| `CO2.dat`         | same column layout         | same column layout | values match; whitespace differs. |
| `CO2_all.dat`     | same                       | same             | whitespace differs. |
| `RF_all.dat`      | same                       | same             | whitespace differs. |
| `fa_ocean.dat`    | `WRITE(95,*) FA_OCEAN(IGP)` | `fa_ocean_file << FA_OCEAN[IGP]` | values match in principle, but in C++ the file is opened **only inside `if (IYEAR == YEAR1)`** and there is no `else` branch (lines 2607–2622), so for `IYEAR > YEAR1` the writes silently go to a default‑constructed (closed) `ofstream` and are dropped. |
| `dtemp_o.dat`     | same                       | same             | same bug as `fa_ocean.dat` (lines 2611–2617). |
| `error`           | written on each error path | written on each error path | similar layout; values match. |

Bottom line: **outputs are not byte‑for‑byte identical** with the Fortran
outputs. They are the same fields with the same values up to numerical noise,
but the formatting (column widths, separators, integer vs real for `WET.dat`)
differs. Anything that re‑reads these files with a width‑sensitive parser
will need adjusting.

### `done` marker — protocol comparison

The Fortran flow for the `done` file is:

1. Per‑year, after writing climate output, IMOGEN writes the *content* file
   `${DIR_COMMON}/IMOGEN/output/${YYYY}/done` with payload `"Climate files
   written"` (`imogen_lpjg.f` line 1050). LPJ‑GUESS polls for this file.
2. LPJ‑GUESS in turn writes `${DIR_COMMON}/LPJG_main/IMOGEN/done` to tell
   IMOGEN that next‑year inputs are ready.
3. On the next IMOGEN call, **`SETTIN_LPJG` opens that file with
   `STATUS='DELETE'`** and closes — i.e. it removes the file as a handshake
   acknowledgement (`imogen_lpjg.f` lines 1498–1500).
4. After reading C‑flux files, the body of the loop also opens and deletes
   `…/LPJG_main/IMOGEN/done` (`imogen_lpjg.f` lines 591–593) — defensively, in
   the case the SETTIN_LPJG path was bypassed.

The C++ flow:

* Step 1 (output `done`) is implemented faithfully:

  ```2602:2604:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/IMOGENCXX/ImogenCXX/src/Main.cpp
  					std::ofstream done_file(DIR_COMMON + "/IMOGEN/output/" + THISYEAR + "/done");
  					done_file << "Climate files written" << std::endl;
  					done_file.close();
  ```

* Step 3 (delete the LPJ‑GUESS `done`) is **inverted**: instead of
  deleting the file, the C++ creates an empty one:

  ```784:792:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/IMOGENCXX/ImogenCXX/src/Main.cpp
  	std::string done_file_path = dir_common + "/LPJG_main/IMOGEN/done";
  	std::ofstream done_file(done_file_path);
  	if (done_file) {
  		done_file.close();
  	}
  	else {
  		std::cerr << "Error creating/closing done file: " << done_file_path << std::endl;
  	}
  ```

  This is a logical bug: the Fortran semantics ("acknowledge by deleting") have
  been replaced by "(re‑)create empty". Combined with the fact that the main
  poll loop *also* requires `DONE_EXIST == true` to start a year (line 1940),
  the C++ effectively never clears the rendezvous, so without the external
  `Imogen-controller` (§7) cleaning up, IMOGEN would race / busy‑loop.

* Step 4 is implemented at line 2184 (`remove(marker_file_path.c_str())`),
  partially compensating for step 3.

So the `done` protocol is **not the same as Fortran**. The shipped runtime
relies on the external `Imogen-controller` executable to make the protocol
look correct.

---

## 7. `Imogen-controller/`

This is a **separate driver / launcher**, not part of `IMOGENCXX`. Its job is
to drive the year‑by‑year handshake by writing `imogen_lpjg.txt` and the
`done` file in lieu of (or alongside) LPJ‑GUESS, so that `imogen_lpjg.exe` /
the C++ rewrite can be exercised standalone or stepped through years.

```
Imogen-controller/
├── Imogen-controller.cpp        # Windows‑only original (uses windows.h, Sleep, rd /s)
├── Imogen-controller-cxx.cpp    # Windows‑only variant (essentially identical)
├── Imogen-controller-cross.cpp  # Cross‑platform via #ifdef _WIN32 / #else
├── Makefile                     # builds Imogen-controller-cxx.cpp with g++ -std=c++17
├── README.txt                   # describes the role of the tool
└── config.txt                   # placeholder ("Future implementation of a config file")
```

### What it does

Quoting the README and re‑confirmed by reading the source:

1. At start, ensure `${DIR_COMMON}/LPJG_main/IMOGEN/done` exists (creates if not).
2. Loop: every 5 s, if `done` is missing, sleep 3 s, write a fresh
   `imogen_lpjg.txt` containing `YEAR1`, `IYEND`, `YEAR1_LPJG`, `SPINUP`,
   `KEEPRUNNING`, `FIRSTCALL` for the next year, then re‑create the `done`
   file. The year sequence is hard‑coded: `1871` (spin‑up), then every year
   from `1872` to `2100`; the controller exits at `counter == 228`.
3. Command‑line modes:
   * `Imogen-controller reset` — write a 1871 spin‑up `imogen_lpjg.txt`,
     remove `RF_all.dat`, `CO2_all.dat`, recursively delete the `IMOGEN/output`
     folder. Uses `rd /s` (Windows) or `rm -rf` (Linux variant).
   * `Imogen-controller move <name>` — rename the output folder and move
     `RF_all.dat` / `CO2_all.dat` into it. Uses `ren` / `move` on Windows or
     `mv` on Linux.

### The three `.cpp` variants

* `Imogen-controller.cpp` — Windows only. Includes `<windows.h>`, `<direct.h>`;
  uses `Sleep()`; `commonDirectory = "C:\\dampoh\\GitHub\\…"`; uses `rd /s`,
  `ren`, `move`. Hard‑codes a stray Windows path
  `"C:\\GitHub\\LPJ_IMOGEN_coupling\\Common_Directory\\LPJG_main\\IMOGEN\\done"`
  on line 214 that overrides `commonDirectory` for one branch — bug.
* `Imogen-controller-cxx.cpp` — same Windows‑only code, the only differences
  are the value of `commonDirectory` (different root) and that boolean
  literals are written `TRUE` instead of `.TRUE.` (which **breaks the Fortran
  `READ` namelist parsing**, since Fortran requires `.TRUE.` / `.FALSE.`).
  Ironic for a controller intended to feed Fortran.
* `Imogen-controller-cross.cpp` — cross‑platform via `#ifdef _WIN32`.
  This is the variant compiled by the `Makefile` (note: the `Makefile` actually
  references `Imogen-controller-cxx.cpp`, not `-cross.cpp`, so the Linux
  build still picks the Windows‑only file — see §10).
  Includes `<unistd.h>`, `<sys/stat.h>` and uses `usleep`, `rm -rf`, `mv` in
  the Linux branch. Still constructs paths with backslashes
  (`commonDirectory + "LPJG_main\\IMOGEN\\done"`) which are interpreted as
  literal characters in Linux paths — broken.

The user’s instruction is to ignore the Windows cross‑compile aspect because
this build is Linux‑only. So:

* On Linux, `Imogen-controller-cross.cpp` is the only candidate, *but* the
  shipped `Makefile` builds the wrong file, and even the right file uses
  Windows path separators throughout.
* Treat all three variants as scaffolding to be discarded when the C++
  IMOGEN is integrated as a callable library / sub‑routine of LPJ‑GUESS
  (which appears to be the actual goal of the unification effort).

### `Makefile` and `config.txt`

```42:43:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Imogen-controller/Makefile
build: $(SRC)
	$(CC) $(CFLAGS) -o $(EXEC) $(SRC)
```

* `CC := g++`, `CFLAGS := -Wall -std=c++17`, `SRC := Imogen-controller-cxx.cpp`.
* OS detection picks `del /Q` vs `rm -f` for the `clean` target only.
* `config.txt` is a single‑line placeholder.

There is no Makefile for the IMOGEN C++ refactor itself (`IMOGENCXX/`).

---

## 8. Windows‑isms to remove for a unified Linux build

Locations and what to do at each:

| Location | What it is | Fix on Linux |
|---|---|---|
| `Main.cpp:525` | `std::ifstream settings_file("C:\\GitHub\\dbampoh\\…\\imogen_settings.txt")` | replace with a CLI arg or `getenv("IMOGEN_SETTINGS")` and default to `"./imogen_settings.txt"`. |
| `Main.cpp:800` | `localtime_s(&now_tm, &now_time)` | use `localtime_r(&now_time, &now_tm)`. |
| `Main.cpp:1648` | `system("pause")` inside `QSAT` | delete; debug artefact. |
| `Main.cpp:2231` | `FILE_CLIM = DIR_CLIM.substr(0, II_CLIM) + "\\" + DRIVE_MONTH[j] + VARYEAR_STR;` | replace `"\\"` with `"/"` (or `std::filesystem::path` arithmetic). |
| `Main.cpp:466` | `DRIVE_MONTH = { "/jan", … }` (note the `/` already) | OK — use these as in Fortran. The mismatch with the `\\` at line 2231 means clim and pattern paths are constructed with different separators on Windows already. |
| `imogen_settings.txt` (all path keys) | `C:\GitHub\…` | re‑write as POSIX paths. |
| `Imogen-controller.cpp` (all three) | `<windows.h>`, `Sleep`, `direct.h`, `rd /s`, `ren`, `move`, `\\` separators | use the `-cross.cpp` only and fix its remaining `\\` separators; or drop the controller entirely if IMOGEN becomes an in‑process callee of LPJ‑GUESS. |
| `Imogen-controller-cxx.cpp:80, 199, 240, 251` | writes `TRUE`/`FALSE` (no dots) into `imogen_lpjg.txt` | restore `.TRUE.`/`.FALSE.` for Fortran compatibility — or commit to the C++ port and drop Fortran‑literal compatibility. |
| `Imogen-controller/Makefile:26` | `SRC := Imogen-controller-cxx.cpp` | change to `Imogen-controller-cross.cpp`. |
| `IMOGENCXX/` | no build system | add a CMakeLists.txt or Makefile; current code requires `-std=c++17` because of `<filesystem>` (line 26). |

There are **no `#ifdef _WIN32` guards** in `Main.cpp` itself — the code is
unconditionally compiled with the Windows‑only `localtime_s` / `system("pause")`
calls. They must simply be edited out.

---

## 9. Faithfulness assessment — is the C++ a faithful port?

Short answer: **it is structurally a faithful translation but functionally
incomplete and contains several bugs.** Significant pieces are missing or
wrong, in particular the sub‑daily disaggregation that is the *entire reason*
for IMOGEN's per‑year output:

1. **`DAY_CALC` is an empty stub.** The body is one block of commented‑out
   code (`Main.cpp` lines 1149–1162). In the Fortran, `DAY_CALC` (462 lines,
   `imogen_lpjg.f` 1511–1972) drives all sub‑daily disaggregation: rainfall
   redistribution via `REDIS`, diurnal temperature, sunlit fractions via
   `SUNNY`, longwave/shortwave partitioning, humidity from `QSAT`, etc.  The
   C++ `CLIM_CALC` calls this empty stub at line 1260 and then writes whatever
   uninitialised values the local arrays hold (or zeros, since the local
   arrays are default‑constructed `std::vector<double>` filled with 0). For
   `STEP_DAY > 1` the per‑step output is therefore meaningless; for
   `STEP_DAY == 1` (the default) the daily means computed in `CLIM_CALC` itself
   are still produced, so a daily‑monthly pipeline can superficially run, but
   any genuine sub‑daily run is broken.

2. **`SOLPOS` is a placeholder** — it returns `sin(2π(d-81)/365)` and
   `SCS = 1367` regardless of `YEAR` (the Fortran routine implements
   declination from orbital elements). Through `SUNNY`/`SOLANG` this affects
   sub‑daily SW partitioning, which is dead code anyway because of (1).

3. **`DTEMP_OUT` is never assigned** — `Main.cpp:1293` is the assignment line,
   commented out:

   ```1292:1293:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/IMOGENCXX/ImogenCXX/src/Main.cpp
   				//Also want a DTEMP output for LPJ - GUESS - TP 03.02.16
   				//DTEMP_OUT[L][J][K] = DTEMP_DAILY[L][J][K];
   ```

   The Fortran assigns it (`imogen_lpjg.f` 2502–2750 inside `CLIM_CALC`).
   `DTEMP_anom.dat` will therefore contain only zeros / MDI from C++.

4. **The per‑year loop never exits.**

   ```2626:2626:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/IMOGENCXX/ImogenCXX/src/Main.cpp
   	} while (KEEPRUNNING = true);
   ```

   The condition is an *assignment* (`=`) not a comparison (`==`), so
   `KEEPRUNNING` is forced to `true` every iteration, producing an infinite
   loop regardless of what `SETTING_LPJG` reads.  This negates the whole
   `KEEPRUNNING` protocol.

5. **`SETTING_LPJG` writes the `done` file instead of deleting it** (lines
   784–792). Polarity inverted vs Fortran; documented in §6.

6. **Spin‑up vector growth bug.**  `FA_OCEAN` is constructed with size
   `NFARRAY=10000`. Then in spin‑up (`if ((IYEAR == YEAR1_LPJG) || SPINUP)`):

   ```2044:2058:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/IMOGENCXX/ImogenCXX/src/Main.cpp
   					if (ANLG) {
   						for (int i = 1; i < N_OLEVS; i++)
   						{
   							DTEMP_O.push_back(0.0);
   							if (INCLUDE_CO2 && OCEAN_FEED && C_EMISSIONS) {
   								for (int i = 1; i < NFARRAY; i++) {
   									FA_OCEAN.push_back(0.0);
   								}
   							}
   						}
   					}
   					SEED_RAIN.push_back(9465);
   					SEED_RAIN.push_back(1484);
   					SEED_RAIN.push_back(3358);
   					SEED_RAIN.push_back(8350);
   ```

   The intent (per Fortran `DO I=1,N_OLEVS; DTEMP_O(I)=0.0; ENDDO`) was to
   *zero* the existing entries, not to *append*.  Each spin‑up call grows
   `DTEMP_O` by `N_OLEVS-1` zeros, and inside the same loop grows `FA_OCEAN`
   by `(N_OLEVS-1) × (NFARRAY-1)` zeros — i.e. about 2.5 million extra zeros
   per spin‑up call. `SEED_RAIN` similarly gets four entries appended on top
   of the four it was constructed with. Indexing into `SEED_RAIN[0..3]` is now
   the constructor zeros, not the seeds 9465/1484/3358/8350 — so the random
   stream is wrong.

7. **`OCEAN_CO2` indexing bug.** The Fortran call uses 1‑based indices
   throughout. The C++ `OCEAN_CO2` mixes 0‑based and 1‑based: `J` runs
   `1..NCALLYR*YEAR_CO2`, `ISTEP = (IYEAR - YEAR_CO2)*NCALLYR + J`, and the
   inner loop is `for (I = 1; I < ISTEP; ++I) DCO2_OCEAN_MOL += … FA_OCEAN[I] *
   RS[ISTEP - I] * …`.  In Fortran `RS` is allocated `RS(YEAR_RUN*NCALLYR)`
   with 1‑based indexing; in C++ it's `std::vector<double> RS(YEAR_RUN *
   NCALLYR)` (0‑based) but accessed as `RS[ISTEP - I]` with `ISTEP` 1‑based —
   off‑by‑one, dropping one term and reading one out‑of‑range zero per outer
   step. Subtle but wrong.

8. **Wrong flag passed to `FAIR_NON_CO2_GHG_BUDGET`.** Fortran passes
   `NONCO2_EMISSIONS_LPJG`; C++ passes `NONCO2_EMISSIONS` (line 2366).  Inside
   the function the flag controls whether to add LPJ‑GUESS CH4/N2O fluxes;
   the two booleans differ in semantic intent and can in principle be set
   independently.

9. **`!= comment` parser fragility.** `SETTING` finds the *first* space and
   takes everything after as the value. Lines like
   `STEP_DAY 1 		!IN Number of daily timesteps …` work because `trim()`
   strips at the `!` (line 66–71).  But `value.erase(std::remove_if(...,
   ::isspace), value.end())` (line 545) also strips spaces from path values
   — which is fine for Windows paths without spaces but will silently break
   user paths that contain spaces.

10. **`GCM_ANLG` glues paths with `+` and trims with `find_last_not_of(' ')`**
    (line 477). This is byte‑for‑byte the Fortran trim semantics, which is
    fine; but the same routine reads anomaly headers without checking
    `infile.fail()` after each `>>` — silent file corruption.

11. **The `.exe` semantics of the runtime are still assumed**: `system("pause")`,
    Windows path separators in clim file construction (line 2231), and
    `localtime_s`. All addressed in §8.

12. **Sub‑daily output is produced with `MDI` for `ISTEP >= STEP_DAY`** (lines
    1280–1290). With `STEP_DAY=1` (default) every sub‑daily slot beyond 0 is
    `MDI=999.9`. That is intentionally consistent with Fortran, so this isn’t
    a bug — but it means the same writers that read these files must handle
    `999.9` as missing.

### Summary judgement

* **Faithful** for: `RADF_CO2`, `RADF_NON_CO2`, `RESPONSE`, `INVERT`,
  `DELTA_TEMP`, `GCM_ANLG`, `RNDM`, `SOLANG`, `QSAT` (modulo the `system("pause")`),
  `REGRID_CLIM`, `FAIR_NON_CO2_GHG`, `FAIR_NON_CO2_GHG_BUDGET`, the FAIR
  formulas, the radiative balance arithmetic, the `imogen_settings.txt` keyset,
  `OCEAN_CO2` formulas (modulo §9.7), and the per‑year output filenames.
* **Missing or incorrect**: `DAY_CALC` (stub), `SOLPOS` (stub), `DTEMP_OUT`
  output, `done`‑file polarity, KEEPRUNNING loop exit, spin‑up vector
  initialisation, `OCEAN_CO2` indexing edge case, `fa_ocean.dat`/`dtemp_o.dat`
  re‑opening for `IYEAR > YEAR1`, output formatting widths, `WET.dat` integer
  formatting, and Windows‑only system calls.
* **Net assessment**: the rewrite is *not* production‑ready. As shipped it
  cannot reproduce the Fortran outputs even on Windows; on Linux it does not
  even open the settings file (hard‑coded path).

---

## 10. Bugs, dead code, hardcoded paths, TODO / FIXME

Bugs and oddities discovered (some already cited above for narrative reasons):

* **B1.** Hard‑coded settings path in `SETTING` — `Main.cpp:525`.
* **B2.** `localtime_s` (Windows‑only) — `Main.cpp:800`.
* **B3.** `system("pause")` left inside `QSAT` — `Main.cpp:1648`.
* **B4.** `DAY_CALC` body empty — `Main.cpp:1149–1162`.
* **B5.** `SOLPOS` is a placeholder — `Main.cpp:918–923`.
* **B6.** `DTEMP_OUT` assignment commented out — `Main.cpp:1293`.
* **B7.** `} while (KEEPRUNNING = true);` infinite loop — `Main.cpp:2626`.
* **B8.** `SETTING_LPJG` *creates* `done` instead of deleting — `Main.cpp:784–792`.
* **B9.** Spin‑up `push_back` instead of element zeroing — `Main.cpp:2044–2058`
  (corrupts `FA_OCEAN`, `DTEMP_O`, `SEED_RAIN`).
* **B10.** Wrong flag name passed to `FAIR_NON_CO2_GHG_BUDGET` —
  `Main.cpp:2366` (`NONCO2_EMISSIONS` vs `NONCO2_EMISSIONS_LPJG`).
* **B11.** `\\` path separator in clim‑file construction —
  `Main.cpp:2231`.
* **B12.** `ofstream` reopened only on `IYEAR == YEAR1` for the per‑year append
  files (`fa_ocean.dat`, `dtemp_o.dat`, `T_anom.dat`, etc.) — for
  `IYEAR > YEAR1` writes go to a default‑constructed (closed) stream and are
  silently dropped — `Main.cpp:2499–2622`.
* **B13.** Output file widths/separators differ from Fortran (§6).
* **B14.** `WET.dat` written through `<< std::fixed << setprecision(3)` rather
  than as integer — `Main.cpp:2523`.
* **B15.** `SUNNY` line 1021 has `(j-1)*TIMESTEP` for j starting at 0 — first
  step time is negative.
* **B16.** Duplicate first entry in `ES[]` table (lines 1301–1302) — table
  is shifted by one vs Fortran.
* **B17.** `TODO: Consider adding in the concentration reading for CH4 and
  N2O here` — left over from Fortran TODO at `Main.cpp:2220`.
* **B18.** Several `// FIX ME` and `//OPTIMIZATION IN PROGRESS` markers in the
  code (e.g. `Main.cpp:2590` "FIX ME"; `Main.cpp:1150` "OPTIMIZATION IN
  PROGRESS").
* **B19.** Triplicated `#include <iostream>` etc. at top of file (lines 13–25),
  harmless but suggestive of merge debris.
* **B20.** `Imogen-controller.cpp:214` hard‑codes
  `"C:\\GitHub\\LPJ_IMOGEN_coupling\\Common_Directory\\…"`, overriding
  `commonDirectory` in one branch.
* **B21.** `Imogen-controller-cxx.cpp` writes `TRUE`/`FALSE` (no dots) instead
  of `.TRUE.`/`.FALSE.`, breaking Fortran namelist parsing (lines 80–82,
  199–201, 240–242, 251–253).
* **B22.** `Imogen-controller/Makefile:26` builds `Imogen-controller-cxx.cpp`
  rather than `Imogen-controller-cross.cpp` even when `detected_OS != Windows`.
* **B23.** Three `//TODO: SHOULD THIS BE IYEAR-1 RATHER THAN IYEAR???` comments
  preserved in `Main.cpp` (lines 2326, 2346) — same TODOs are in Fortran.
* **B24.** `INVERT` allocates `3 × N_OLEVS² × sizeof(double)` ≈ 1.5 MB on every
  call; the Fortran version reuses stack/static arrays. Negligible for
  correctness, but called inside `DELTA_TEMP`'s inner timestep loop, so
  amounts to a noticeable allocator load.
* **B25.** Settings parser line 537 splits on the first ASCII space (`' '`),
  not whitespace; lines whose key/value separator is a tab will not parse.

Dead / commented code clusters: `Main.cpp:1149–1162`, `1923–1929`, `2188–2193`,
`2220`, `2590`. None of these are functionally relied on.

Hardcoded paths in C++ source (`grep` for `C:\\`):
`Main.cpp:525`, `Imogen-controller.cpp:13, 214`,
`Imogen-controller-cxx.cpp:13`, `Imogen-controller-cross.cpp:21`. All Windows.

---

## 11. Open questions

1. **Does the C++ truly handle larger gridlists?**
   Only in a limited sense: it heap‑allocates with `std::vector` (avoiding
   stack‑overflow that bites the Fortran build at `GPOINTS=3698` on Windows),
   but `GPOINTS=1631` and `NGPOINTS=3698` are still compile‑time
   `const int`s baked into `Main.cpp` lines 39–40. To run a different gridlist
   the user must (a) edit those constants, (b) edit `imogen_settings.txt`'s
   `FILE_GRIDLIST` value, and (c) recompile. There is no run‑time discovery
   of `N` from the gridlist file. The claim "can run with larger gridlists
   than the Fortran version" is therefore **mostly false**; what is true is
   "fits in memory at the same hard‑coded sizes as the Fortran without
   stack‑overflow on Windows".
2. **Has anyone successfully *run* the C++ binary?** The infinite loop in the
   year driver (B7), the inverted `done` polarity (B8), the empty `DAY_CALC`,
   and the hard‑coded settings path together imply that the binary cannot
   complete a year of simulation without manual intervention. Confirming
   whether the rewrite has ever been validated end‑to‑end against the Fortran
   would be valuable before committing further work to it.
3. **Should the unified Linux build keep the rewrite, port the Fortran, or
   call Fortran from C++?** Given that the C++ is incomplete (`DAY_CALC`,
   `SOLPOS`, `DTEMP_OUT`) and the Fortran is complete and tested, a third
   option is to keep the Fortran as the source of truth and only re‑implement
   the file‑system polling layer (`SETTIN_LPJG`, the `done` rendezvous, the
   `Imogen-controller` glue) in portable C++ / Bash.
4. **Is `Imogen-controller` still required at all?** Its job is to fake the
   year‑by‑year handshake. If LPJ‑GUESS itself becomes the orchestrator (the
   stated goal of the unification), the controller is dead weight and can
   be removed entirely.
5. **Output format compatibility.** The downstream readers of `T_anom.dat`,
   `P_anom.dat`, `SW_anom.dat`, `DTEMP_anom.dat`, `WET.dat` (presumably the
   Intermediary or LPJ‑GUESS itself) must be checked against the C++ writer’s
   formatting (§6) to see whether they already assume Fortran fixed widths;
   this is out of scope for Subagent 4 and is left to Subagents 2/5.
6. **Why are `gridlist_3deg.txt`, `gridlist_global.txt`, `gridlist_out.txt`
   etc. only present in `Common-directory/IMOGEN-codebase/code/`?** The C++
   refactor never references them; switching gridlists in the settings file
   without copying these alongside the working directory will fail.

---

End of report.
