# 05 — C++ Intermediary (IPCC tier-1 emissions estimator)

> Investigation scope: original C++ "Intermediary" that estimates anthropogenic
> CH4/N2O/CO2 emissions using IPCC 2019 Refinement (V4) tier-1 methodologies,
> consumes PLUM/OWI/FAO/GLWD3 inputs, and is supposed to merge them with IIASA
> SSP/CMIP background emissions and with LPJ-GUESS natural fluxes before
> handing one combined emissions vector to IMOGEN. Read-only audit of
> `version_A` and `version_B` of the framework, plus a quick sanity build of
> both. The Python replacement (`Intermediary_py/`) is out of scope and is
> covered by Subagent 6.

The Intermediary's documented purpose (`References/Emissions Handling
Methodology.docx`, `README.md`):
- IIASA provides total, sector-disaggregated CO2/CH4 (and total-only N2O)
  emissions from CMIP5/CMIP6 SSP runs.
- LPJ-GUESS supplies natural land/wetland fluxes.
- The Intermediary fills the agricultural / non-natural anthropogenic gap
  using mechanistic IPCC tier-1 formulae applied to PLUM (scenario) and
  FAO/OWI (historic) activity data.
- Then it concatenates: `IIASA_non_lpjg + (LPJG natural + IPCC anthropogenic)`
  per year and writes a combined CH4/N2O/CO2 series for IMOGEN.

That last step (merging) is supposed to live in `Adder.cpp`, but as documented
in §4 and §9 below, **the Adder, Extractor and Wetlands paths are commented
out in `main()` for both A and B**. The current build only computes the
PLUM-IPCC anthropogenic CH4 and N2O streams and writes them to disk.

---

## 1. Top-level structure

`version_A/.../Intermediary/`

```
Intermediary/
├── .vscode/settings.json          # VS Code C++ file associations only (skim only)
└── Code/
    ├── Makefile                   # GNU make, cross-platform (Windows/Linux)
    ├── config.txt                 # runtime config; Windows-style paths
    ├── include/                   # 13 headers
    │   ├── Adder.h                # really declares MethaneEmissions class (see §3)
    │   ├── Calculator.h           # IPCC tier-1 formulae
    │   ├── DualStreamBuffer.h     # tee std::cout to log file
    │   ├── Extractor.h            # LPJ-GUESS .out file reader
    │   ├── FileManager.h          # generic 2-/3-column ASCII I/O
    │   ├── Maps.h                 # ~944 lines of hard-coded IPCC tables
    │   ├── MethaneEmissions.h     # really declares Adder class (see §3)
    │   ├── NitrogenEmissions.h
    │   ├── Parameters.h           # extern globals shared across TUs
    │   ├── PlumDataProcessor.h    # PLUM landuse/fertilizer extractor
    │   ├── Templates.h            # POD structs (dataHolder1/2, etc.)
    │   ├── UtilityHandler.h       # config parser, string utils
    │   └── Wetlands.h             # GLWD3 wetlands -> CH4
    └── src/                       # 12 .cpp files mirroring headers + Main.cpp
```

`version_B/.../Intermediary/Code/` is identical in layout but adds
`include/Logger.h` and `src/Logger.cpp` (see §10).

Line counts (`wc -l`):

| File              | A (lines) | B (lines) |
|-------------------|----------:|----------:|
| `src/Adder.cpp`        |  292 |  292 |
| `src/Calculator.cpp`   |  118 |  353 |
| `src/Extractor.cpp`    |  300 |  298 |
| `src/FileManager.cpp`  |  129 |  154 |
| `src/Logger.cpp`       |    – |  136 |
| `src/Main.cpp`         |  241 |  327 |
| `src/Maps.cpp`         |   81 |  367 |
| `src/MethaneEmissions.cpp`  |  290 |  434 |
| `src/NitrogenEmissions.cpp` |  270 |  451 |
| `src/Parameters.cpp`   |   87 |   87 |
| `src/PlumDataProcessor.cpp` |  197 |  209 |
| `src/UtilityHandler.cpp`    |  155 |  137 |
| `src/Wetlands.cpp`     |   72 |  133 |
| `include/Maps.h`       |  944 | 1493 |
| **Code total**         | **4 052** | **5 891** |

---

## 2. Build system

A single `Makefile`. No CMake, no CI, no tests.

```7:32:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/Makefile
else
    detected_OS := $(shell uname -s)
    RM := rm -f
    EXT := 
    MKDIR = mkdir -p $(1)
endif


# Define compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -MMD -MP -Iinclude

# Directories
SRCDIR = src
INCDIR = include
BUILDDIR = build
BINDIR = bin

# Define source and object files
SRCS = $(wildcard $(SRCDIR)/*.cpp)
OBJS = $(patsubst $(SRCDIR)/%.cpp,$(BUILDDIR)/%.o,$(SRCS))
DEPS = $(OBJS:.o=.d)

# Define target executable
TARGET = $(BINDIR)/ipcc$(EXT)
```

Notes:
- C++17, header-only deps (only the standard library), single binary
  `bin/ipcc` (or `ipcc.exe` on Windows).
- No optimization flags, no `-Wall`, no warnings, no sanitizers.
- Compiles cleanly on Linux with `g++ 13` for **both** A and B (verified by
  copying `Code/` into `/tmp` and running `make`; both produced
  `bin/ipcc` without errors). The framework is therefore buildable, but
  whether it actually *runs* end-to-end is open (see §12).

`Main` reads `../config.txt`, i.e. it expects to be invoked from `bin/` with
`./ipcc` (relative parent). The `baseDirectory` key inside `config.txt` is
hard-coded to a Windows path (`C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\`)
in both A and B, which the user must edit before any real run.

Linux path-separator translation is done at runtime:

```83:88:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/src/Main.cpp
#ifdef __linux__
	for (auto &pair : config)
	{
		UtilityHandler::replaceAll(pair.second, "\\", "/");
	}
#endif
```

---

## 3. Source-file catalog

(One-line role, then a deeper note for the central files. All citations are
into `version_A` unless explicitly tagged "(B)".)

### Headers

- `Templates.h` — POD structs used as in-memory rows.
  - `dataHolder1{int year, double value}` — 2-col output.
  - `dataHolder2{int year, double value1, value2}` — 3-col output (CH4 + N2O).
  - `PLUMFileDataStruct` — one row of the PLUM `animals_sspN.txt` CSV
    (`year,country,item,nheads`).
  - `readcflux`, `readMethane`, `readNitrogen` — one-row scratch for the
    LPJG `cflux.out`, `mch4.out`, `ngases.out` files.
  - `readWetlands` — one-row scratch for the wetlands area CSV.
  - `readRiceMethane` — one-row scratch for the FAO `FAOSTAT.csv` rice file.
  - `readPLUMLandUSe` — full schema (74 columns) of an SSPx_s1_YYYY_LandUse.txt.
- `Parameters.h` / `Parameters.cpp` — declares the run-wide globals
  (config map, year window, every output filename, scenario `cmip5`/`cmip6`,
  ssp/rcp lists). Used as a poor man's singleton; mutated in `Main`.
- `UtilityHandler.h/.cpp` — `readConfig()` (key=value parser), `split`,
  `trim`, `replacePlaceholders` (substitutes `SSP`/`RCP`/`baseDirectory`
  in path templates), `replaceSubstring`/`replaceAll`.
- `FileManager.h/.cpp` — `openFile`, `closeFile`, `loadFile2/loadFile3`
  (read 2-/3-col whitespace-separated ASCII), `printToFile` overloads (5-decimal
  fixed format), `printToConsole` overloads. Calls `exit(100)` on any
  read failure.
- `DualStreamBuffer.h` — `std::streambuf` subclass that tees `std::cout`
  to a log file (path comes from `config["pathToLogFile"]`).
- `Maps.h` — **all hard-coded IPCC tables**. Pure declarations of
  `std::unordered_map`s with embedded comments naming the IPCC table
  number (10.10, 10.11, 10.13a, 10.19, 10.21, 10.22, 10A.5, 10A.9 …) and
  the wetlands `Tropical Wet`/`Cool`/etc. emission factors (Table 3A.2 in
  the 2006 Wetlands appendix).
- `Calculator.h/.cpp` — five tier-1 formulae; see §7.
- `MethaneEmissions.h/.cpp`, `NitrogenEmissions.h/.cpp` — workhorse classes
  for the PLUM scenario (2010-2100) and OWI/FAO historic (1961-2009)
  estimators; see §8/§9.
- `PlumDataProcessor.h/.cpp` — pre-processes raw PLUM `*_LandUse*` files
  into per-year fertilizer totals.
- `Wetlands.h/.cpp` — reads a per-country wetlands area CSV and applies
  Calculator's CH4 wetlands formula.
- `Extractor.h/.cpp` — reads LPJ-GUESS gridded `cflux.out`, `mch4.out`,
  `ngases.out` and aggregates them globally per year.
- `Adder.h/.cpp` — combines IIASA + LPJG + IPCC vectors into the final
  per-year output for IMOGEN.

### Source files

- `Main.cpp` — entry point; configuration loading, scenario validation,
  per-(ssp,rcp) loop. See §4.
- `Adder.cpp` — implementation of the merge logic. **Not currently called.**
  See §9.
- `Logger.cpp` (B only) — singleton text logger with timestamps and levels.

> **Header-naming bug**: `Adder.h` declares `class MethaneEmissions` and
> `MethaneEmissions.h` declares `class Adder`. The header guards/`#pragma
> once` work, but the file/class mismatch is misleading. Both A and B
> still ship this swap.
>
> ```11:14:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/include/Adder.h
> class MethaneEmissions
> {
> 
> private:
> ```
>
> ```8:14:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/include/MethaneEmissions.h
> class Adder
> {
> 
> private:
> 	// file manager to hamdle file management
> 	FileManager myFileManager;
> ```

---

## 4. Entry point and main flow

`src/Main.cpp::main()`. There is **no year loop in the executable** itself —
it's a one-shot batch over scenarios.

1. Read `../config.txt` via `UtilityHandler::readConfig`.
2. Pull `scenario`, `ssps`, `rcps`, `firstyear`, `lastyear`,
   `lpjg_start_year`, `lpjg_end_year`, `baseDirectory`, `pathToLogFile`
   into the globals declared in `Parameters.h`. Validate consistency:
   - `len(ssps) == len(rcps)`.
   - `scenario ∈ {cmip5, cmip6}`.
   - `firstyear ≥ 1850` (cmip5) or `≥ 1990` (cmip6).
   - `firstyear ≤ lastyear`.
3. On Linux only, replace `\` with `/` in every config value.
4. Install `DualStreamBuffer` so all `std::cout` is also written to
   `Data/Intermediary/Emissions/log.txt`.
5. **For each `i ∈ [0, ssps.size())`** (all version-A code paths
   commented out are kept here for fidelity):
   - Substitute `SSP` and `RCP` placeholders in every output/input
     path; if `scenario == "cmip6"`, also rewrite `CMIP5 → CMIP6` in two
     IIASA paths.
   - Construct `MethaneEmissions(myPLUMDataFilePath)`,
     call `setAuxFilePath(livestock_counts, fao_stats)`, then
     `startCalculations()` (does both 1961-2009 historic and 2010-2100
     scenario CH4), then write 3 files (enteric, manure-mgmt, total).
   - Construct `NitrogenEmissions(myPLUMDataFilePath, plumFertlizerPath)`,
     call `setAuxFilePath(livestock, n2ofert, arablelands)`, then
     `startCalculations()`, then write the total N2O file.

Active flow for **version_A**:

```183:197:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/src/Main.cpp
		// IPCC-PLUM Methane
		MethaneEmissions myMethaneEmissions(myPLUMDataFilePath);
		myMethaneEmissions.setAuxFilePath(livestock_counts_path, fao_stats_path);
		myMethaneEmissions.startCalculations();
		myMethaneEmissions.setMethaneEmissionsOutputFilePaths(entericFermentationMethaneOutputFilePath, manureManagementMethaneOutputFilePath, methaneEmissionOutputFilePath);
		myMethaneEmissions.printEntericFermentationMethaneEmissions();
		myMethaneEmissions.printManureManagementMethaneEmissions();
		myMethaneEmissions.printMethaneEmissions();

		// IPCC-PLUM Nitrogen
		NitrogenEmissions myNitrogenEmissions(myPLUMDataFilePath, plumFertlizerPath);
		myNitrogenEmissions.setAuxFilePath(livestock_counts_path, historic_nitrogen_fertiizer_file_path, arable_lands_nitrogen_fertilizer_path);
		myNitrogenEmissions.startCalculations();
		myNitrogenEmissions.setNitrogenEmissionsOutputFilePath(nitrogenEmissionOutputFilePath);
		myNitrogenEmissions.printNitrogenEmissions();
```

Lines 199-237 of `Main.cpp` (commented out): Extractor → Wetlands → vector
extraction → `Adder::startAddition(...)` → `printToFile`. **The merge step
that the README describes as the central job of the Intermediary is
disabled.**

In **version_B**, things degrade further: the entire `MethaneEmissions`
block is also commented out, leaving only the `NitrogenEmissions`
calculation (`src/Main.cpp` lines 243-277). Yet the line right after the
commented block still prints "Methane emissions results written
successfully" to the logger (line 259), which is misleading.

---

## 5. Inputs — file-by-file

All paths come from `Code/config.txt`. SSP/RCP placeholders are filled at
runtime via `UtilityHandler::replacePlaceholders`. `baseDirectory` is the
Windows `C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\` value.

The actual files exist under `Data/Intermediary/`:

```
Data/Intermediary/
├── Emissions/      (outputs; pre-existing reference outputs from a previous run)
├── IPCC_OWI_FAO/   (outputs; same)
├── IPCC_PLUM/      (outputs; same)
├── Input/
│   ├── CMIP5/      (IIASA non-LPJG and LPJG-component CH4/N2O/CO2)
│   ├── CMIP6/      (CMIP6 versions)
│   ├── FAOSTAT.csv      (rice harvested area + CH4 emissions)
│   ├── PLUM_Fertilizer_SSPx.txt   (5 files; pre-aggregated kg N/yr)
│   ├── arablelands.csv            (266 countries × years 1961–2018, ha)
│   ├── countries.txt              (only loaded by dead `loadCountries()` path)
│   ├── livestock-counts.csv       (OWI/FAO livestock heads)
│   └── n2ofertilizer.csv          (World-Bank fertilizer kg/ha)
└── PLUM_data/
    ├── animals_sspN.txt           (5 files; SSP scenario livestock 2010-2100)
    ├── plum_land_use/             (SSPx_s1_YYYY_LandUse.txt — 5 ssps × ~91 years)
    └── agg_land_use/              (SSPx_s1_LandUseAgg.csv — pre-aggregated)
```

| Input config key                          | Read by                                  | Format                                                                 | Source dataset                              |
|---                                        |---                                       |---                                                                     |---                                          |
| `myPLUMDataFilePath`                      | `MethaneEmissions::startCalculation_methane_scenario_2010_2100`, `NitrogenEmissions::startCalculation_nitrogen_scenario_2010_2100` | CSV: `year,country,item,nheads_in_millions`. e.g. `2010,Kenya,Meat pig,0.9337`. ~44 k lines per SSP. | PLUM model output                            |
| `livestock_counts_path`                   | `MethaneEmissions::startCalculation_methane_modelled_historic_1961_2009`, `NitrogenEmissions::startCalculations_historic_nitrogen_1961_2009` | CSV: `Entity,Code,Year,Asses,Buffalo,Cattle,Goats,Horses,Mules,Pigs,Sheep,Turkeys,Chickens` (HYDE & FAO 2017). | OWI / FAO                                    |
| `fao_stats_path`                          | `MethaneEmissions` (rice CH4)            | FAOSTAT CSV: `Domain Code,Domain,Area Code,Area,Element Code,Element,Item Code,Item,Year Code,Year,Unit,Value,Flag,Flag Description,CH4 emmision from rice cultivation`. Filtered to `Item=Rice paddy`, `Element=Area harvested`, `Area=World`, `1961 ≤ year < 2010` (A) / `< 2020` (B). | FAOSTAT                                     |
| `historic_nitrogen_fertiizer_file_path`   | `NitrogenEmissions` historic             | CSV: `Country Name,Country Code,Indicator Name,Indicator Code,1960..2021` — kg fertilizer per ha of arable land. | World Bank (`AG.CON.FERT.ZS`)               |
| `arable_lands_nitrogen_fertilizer_path`   | `NitrogenEmissions` historic             | CSV: same shape (266 rows × years 1961–2018), arable land area in ha. | World Bank                                  |
| `wetlandsAreaFilePath`                    | `Wetlands::startCalculation`             | CSV: `country,variable,year,measure,value` (A) — per-country wetland extent in km². B reorders columns. | GLWD3 (Lehner & Döll 2004); B switches to GLWD v2 + peat/openwater. |
| `basePathPLUMdata`                        | `PlumDataProcessor::extractDataFromPlumLandUseFiles` | Whitespace ASCII, 74 columns of fractional land-use per gridcell, one file per SSP×year (`SSPx_s1_YYYY_LandUse.txt`). | PLUM                                        |
| `basePathPLUMdata_v2`                     | `PlumDataProcessor::extractDataFromPlumLandUseFiles_v2` | CSV: `SSP,Year,PlumGroup,Crop,CropArea,CropFert,CropIrrig`. | PLUM                                        |
| `plumFertlizerPath`                       | `PlumDataProcessor::readFertilizerData` (called by `NitrogenEmissions::startCalculation_nitrogen_scenario_2010_2100`) | 2-col text: `year value` (kg N total). 91 lines (2010-2100). | PLUM-derived (output of one of the two extractor paths above) |
| `lpjgOutputDirectory` + `cflux.out`       | `Extractor::startLPJGDataExtraction`     | Whitespace ASCII gridded LPJG output: `lon lat year manure veg repr soil fire est seed harvest LU_ch Slow_h NEE`. | LPJ-GUESS                                  |
| `lpjgOutputDirectory` + `mch4.out`        | `Extractor`                              | Whitespace ASCII: `lon lat year jan…dec` monthly CH4. | LPJ-GUESS                                  |
| `lpjgOutputDirectory` + `ngases.out`      | `Extractor`                              | Whitespace ASCII: `lon lat year NH3_fire NH3_soil NOx_fire NOx_soil N2O_fire N2O_soil N2_fire N2_soil total`. | LPJ-GUESS                                  |
| `IIASA_non_lpjg_1850_2100`                | `Adder::read_IIASA_non_lpjg_1850_2010`   | 3-col text: `year CH4 N2O` (TgCH4/yr, TgN2O/yr). 251 lines (1850-2100) for cmip5. | IIASA SSP database — components LPJG/IPCC do **not** simulate. |
| `IIASA_lpjg_1850_2100`                    | `Adder::read_IIASA_lpjg_1850_2010`       | 3-col text: `year CH4 N2O`. | IIASA SSP database — components LPJG/IPCC **do** simulate (used for years before LPJG/IPCC kick in). |
| `IIASA_lpjg_co2_file_path`                | `Adder::read_IIASA_co2_lpjg_1850_2100`   | 2-col text: `year CO2`. Just CO2. | IIASA — used for the 1850-1960 spin-in of CO2 before LPJG cflux is available. |
| `historicEntericMethaneOutputFilePath` … `scenarioNitrogenFertilizerOutputFilePath` | (B only, see §10) | – | New per-stream diagnostic outputs in B. |

Notes on the historic (1961-2009) animal loop:
- Both A and B hard-code an array of 10 (A) or 13 (B) FAO item names that
  must match the column order in `livestock-counts.csv`. **In A only the
  first 10 array elements are used and they intentionally line up with the
  10 species columns.** B introduces a 13-element array but still loops
  `i < 10`, so the last 3 (`Camels`, `Ducks`, `Rabbits`) are *referenced*
  in the array literal but never iterated:
  ```47:48:landsymm_lpjg_imogen_coupled_model/version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/src/MethaneEmissions.cpp
  // string FAO_items[10] = {"Asses", "Meat buffalo", "Meat cattle", "Meat goat", "Horses", "Mules", "Meat pig", "Meat sheep", "Turkey", "Meat Poultry"};
  string FAO_items[13] = {"Asses", "Meat buffalo", "Camels", "Meat cattle", "Meat Poultry", "Ducks", "Meat goat", "Horses", "Mules", "Meat sheep", "Meat pig", "Turkey", "Rabbits"};
  ```
  The reordering (Camels at index 2, Meat Poultry at index 4 instead of
  Meat cattle) silently breaks A's intended PLUM↔column mapping; this is a
  latent bug.

---

## 6. Outputs — file-by-file

All outputs are 2- or 3-column whitespace text written by
`FileManager::printToFile`. Column 1 is always the integer `year`; values
are TgCH4/yr or TgN2O/yr or TgC/yr. SSP/RCP get baked into the filename
via `replacePlaceholders`.

| Output config key                                | Producer                                                | Format                                          | Downstream consumer                                                  |
|---                                               |---                                                      |---                                              |---                                                                   |
| `methaneEmissionOutputFilePath`                  | `MethaneEmissions::printMethaneEmissions`               | 2-col `year TotalCH4` (TgCH4/yr) for 2010-2100. | Adder (commented out) → would be passed to IMOGEN.                  |
| `entericFermentationMethaneOutputFilePath`       | `MethaneEmissions::printEntericFermentationMethaneEmissions` | 2-col, enteric-only stream.                | Diagnostic only.                                                     |
| `manureManagementMethaneOutputFilePath`          | `MethaneEmissions::printManureManagementMethaneEmissions`    | 2-col, manure-only stream.                 | Diagnostic only.                                                     |
| `historicEntericMethaneOutputFilePath` (B)       | `MethaneEmissions::printHistoricEntericFermentationMethaneEmissions`        | 2-col, 1961-2019.            | Diagnostic only.                                                     |
| `historicManureManagementMethaneOutputFilePath` (B) | (B)                                                  | 2-col.                                          | Diagnostic only.                                                     |
| `historicRiceCultivationMethaneOutputFilePath` (B) | (B)                                                   | 2-col, FAO rice-only.                           | Diagnostic only.                                                     |
| `nitrogenEmissionOutputFilePath`                 | `NitrogenEmissions::printNitrogenEmissions`             | 2-col `year TotalN2O`.                          | Adder (commented out) → IMOGEN.                                     |
| `historicNitrogenManureOutputFilePath` (B)       | (B)                                                     | 2-col.                                          | Diagnostic only.                                                     |
| `historicNitrogenFertilizerOutputFilePath` (B)   | (B)                                                     | 2-col.                                          | Diagnostic only.                                                     |
| `scenarioNitrogenManureOutputFilePath` (B)       | `NitrogenEmissions::printScenarioNitrogenManureEmissions`   | 2-col 2010-2100, manure-only.               | Diagnostic only.                                                     |
| `scenarioNitrogenFertilizerOutputFilePath` (B)   | `NitrogenEmissions::printScenarioNitrogenFertilizerEmissions` | 2-col 2010-2100, fertilizer-only.         | Diagnostic only.                                                     |
| `wetlandsMethaneEmissionsOutputPath`             | `Wetlands::printWetlandsMethaneData`                    | 2-col 1961-2100 (A) / 1961-2020 (B), constant value (see §8). | Adder (commented out).                                |
| `lpjgMethane`, `lpjgNitrogen`, `lpjgCflux`       | `Extractor::printLPJGEmissionsData`                     | 2-col globally aggregated annual TgCH4/TgN2O/TgC. | Adder (commented out).                                              |
| `methaneNitrogenTotalOutputFilePath`             | `Adder::PrintTotalMethaneNitrogenToFile`                | 3-col `year CH4 N2O`, full firstyear..lastyear range. | **IMOGEN** — this is the main combined product the framework was built to produce. |
| `file_LPJG_IPCC_Path`                            | `Adder::PrintTotalMethaneNitrogenToFile`                | 3-col, LPJG+IPCC-only (without IIASA non-LPJG component). | IMOGEN sensitivity analyses.                                  |
| `lpjgCflux_plus_IIASA_lpjg_co2`                  | `Adder::PrintTotalMethaneNitrogenToFile`                | 2-col, IIASA CO2 (1850-1960) + LPJG cflux (1961-2100). | IMOGEN.                                                       |
| `pathToLogFile`                                  | `DualStreamBuffer`                                      | Plain text mirror of `cout`.                    | Human-readable.                                                      |

For sanity, the included *sample* outputs from a previous successful end-to-end
run (`Data/Intermediary/Emissions/total_methane_nitrogen_rcp26ssp1.txt`,
`Data/Intermediary/Emissions/methane_ssp1.txt`, etc.) confirm the documented
column order and unit (TgCH4/yr, TgN2O/yr).

---

## 7. IPCC tier-1 formula coverage

All formulae live in **`src/Calculator.cpp`**. The Maps comments name
"Chapter 10", Table 10.10/10.11/10.13a/10.19/10.21/10.22/10A.5/10A.9
(Livestock) and Table 3A.2 (Wetlands), but no equation number is written
into the calculator code in A. B adds **one** explicit equation reference
(`EQUATION 3A.1` in `calcCH4Wetlands`). I therefore reconciled each formula
by hand against the 2019 Refinement V4 PDFs in `References/`.

| Calculator method | Formula in code | Maps to IPCC equation |
|---|---|---|
| `calcCH4EntericFermentation(country, animal, nHeads)` | `EF * nHeads / 1e6` (lines 39–47, A) | **V4 Ch10 Eq 10.19 (Updated)** "Enteric Fermentation Emissions From a Livestock Category (Tier 1)": `E_T = N_{T,P} · EF_{T,P} / 10^6` (Gg CH4/yr). EF table = Table 10.11 (cattle/buffalo) and Table 10.10 (other) — both stored as `MAP_ENTERIC_FERMENTATION_EMISSION_FACTORS_FOR_BUFFALO_CATTLE` and `MAP_ENTERIC_FERMENTATION_EMISSION_FACTORS_OTHERS`. |
| `calcCH4ManureManagement(country, animal, nHeads)` | `Σ_S nHeads · VS · AWMS_S · EF_S / 1000` (lines 49–66, A; lines 76–175, B) | **V4 Ch10 Eq 10.22 (Updated)** "CH4 Emissions From Manure Management (Tier 1)": `CH4_mm = Σ_{T,S,P} N · VS · AWMS · EF / 1000` (kg CH4/yr). VS table = Table 10.13a, AWMS = Tables 10A.6–10A.9, EF = Table 10.14 — present as `MAP_FOR_VOLATILE_SOLID_EXCRETION_RATE`, `AWMS`, and `MAP_EMISSION_FACTOR_FOR_METHANE_BY_MANURE_MANAGEMENT_SYSTEM`. |
| `calcVolalileSolidExcretion(rate, mass)` | `rate · mass · 365 / 1000` | **V4 Ch10 Eq 10.22a (Updated)** "Volatile Solid Excretion Rates" — annualised VS per animal. |
| `calcN20ManureManagement(nHeads, country, animal)` | `Σ_S (nHeads · Nex · AWMS_S + 0) · EF3_S · 44/28` (lines 78–101, A) | **V4 Ch10 Eq 10.25 (Updated)** "Direct N2O Emissions From Manure Management": `N2O_D(mm) = Σ_S [Σ_{T,P} (N · Nex · AWMS_{T,S,P}) + Ncdg_s] · EF3_S · 44/28`. The codigestate term `Ncdg` is hard-coded to 0 (`annual_nitrogen_input_via_codigestate = 0.0`). Nex from Table 10.19, EF3 from Table 10.21 — present as `MAP_NITROGEN_EXCRETION_RATE` and `MAP_EMISSION_FACTOR_FOR_N2O_FROM_MANURE_MANAGEMENT`. **Indirect N2O (Eq 10.26-10.29) is NOT implemented** — `MAP_FRACGAS` is loaded into Maps but `getFRACGAS` is never called. |
| `calcN2OManagedSoils(FSN_FON, EF1_avg=0.01, …)` | `FSN_FON · EF1_avg · 44/28 · 1e-9` (lines 103–112, A) | **V4 Ch11 Eq 11.1** "Direct N2O Emissions From Managed Soils (Tier 1)" — but **only the `N2O–N_{N inputs}` term**, and only its first sub-term `(F_SN+F_ON+F_CR+F_SOM) · EF1`. The default `EF1=0.01` matches the IPCC 2019 default. The flooded-rice (`EF1FR`), organic-soils (`F_OS · EF2`), and grazing (`F_PRP · EF3`) terms exist as function arguments but default to zero, and the code never passes non-zero values. |
| `calcNitrogenExcretion(rate, mass)` | A: `rate · mass · 1000/365` (line 75) — **wrong unit**; B: `(rate/1000) · mass · 365` (lines 182–187) — IPCC Eq 10.27/10.28 standard. | Aux function for Eq 10.25. The bug in A is documented in §11. |
| `calcCH4Wetlands(diff_EF, area, ice_free=250)` | `ice_free_period · E_diff · area · 1e-6 · 100 · 0.001` (lines 114–118, A; lines 348–353, B) | **V4 Appendix 3 ("CH4 Emissions from Flooded Land") Eq 3A.1**: `CH4_emiss_WW_flood = P · E(CH4)_diff · A_flood · 10^-6` (Gg CH4/yr). Comments in A say "1e-6 from IPCC, 100 ha→sqkm, 0.001 Gg→Tg". Note the comment is mis-stated: 100 actually converts km² **to** ha in the wetlands area input. EF defaults from Table 3A.2 (Polar Boreal Wet=0.086, Cold Temperate Moist=0.061, Warm Temperate Moist=0.150, Warm Temperate Dry=0.044, Tropical Wet=0.630, Tropical Dry=0.295). Only Tier 1, no bubble emissions, no DOC pathway. |

What is NOT covered in the C++ Intermediary:
- **No CO2 estimation in the C++ code.** The mechanism is not "estimate
  agricultural CO2 with IPCC tier-1" but "use LPJG cflux for natural CO2
  for 1961-2100, IIASA non-LPJG for 1850-1960, and the IIASA `non_lpjg`
  CO2 component for fossil/industrial throughout" — handled inside `Adder`
  (currently commented out).
- IPCC Ch5 Cropland (CO2 from biomass C-stock changes) — referenced PDF
  but no code path. LPJ-GUESS handles cropland C dynamics via NEE.
- Indirect N2O from manure (Ch10 Eq 10.26–10.29 leaching/volatilisation)
  — `MAP_FRACGAS` is populated in Maps.h but never queried.
- Indirect N2O from managed soils via `EF4`/`EF5` (Ch11) — not modelled.
- Wetlands CH4 bubble pathway (Eq 3A.2) — not modelled.

---

## 8. CH4 / N2O / CO2 estimation paths

### CH4 paths

1. **Enteric fermentation, scenario 2010-2100** —
   `MethaneEmissions::startCalculation_methane_scenario_2010_2100`
   reads `myPLUMDataFilePath` line by line, multiplies `nheads * 1e6`
   (PLUM stores millions of head), calls
   `Calculator::calcCH4EntericFermentation` → Tier 1, then converts
   Gg→Tg and accumulates per year.
2. **Manure-management CH4, scenario 2010-2100** — same loop, calls
   `Calculator::calcCH4ManureManagement` → Tier 1 with VS, AWMS, EF
   from Maps; converts Kg→Gg→Tg.
3. **Enteric + manure, historic 1961-2009** —
   `MethaneEmissions::startCalculation_methane_modelled_historic_1961_2009`
   reads `livestock-counts.csv`, applies the same two Tier 1 functions
   per (country, animal, year), excluding the `World` aggregate row.
4. **Rice cultivation CH4, historic** — reads the FAOSTAT file. Only
   summed in if the *boolean* `simulate_ipcc_fao_owi_rice_cultivation_methane_emissions`
   is `true`. **A defaults this to `false`** (with a banner warning printed)
   "because LPJG simulates rice cultivation"; **B defaults it to `true`**.
   Filter is `Item=Rice paddy`, `Element=Area harvested`, `Area=World`,
   year window 1961-2009 (A) or 1961-2019 (B). The "CH4 emission" column
   is taken directly from FAOSTAT's pre-computed value, not recomputed
   with EF × area. So this is technically a *passthrough*, not an IPCC
   formula application.
5. **Wetlands CH4** — `Wetlands::startCalculation` sums Eq 3A.1 over
   every per-country area row in the wetlands CSV, then **broadcasts that
   single global sum to every year 1961-2100** (A) or 1961-2020 (B):
   ```45:47:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/src/Wetlands.cpp
       for (int i = 1961; i <= 2100; i++) {
           wetlandsCH4.push_back({i,Ch4_wetlands_total});
       }
   ```
   So wetlands CH4 from this module is *time-invariant*; any temporal
   variation in wetland extent is ignored. (LPJ-GUESS supplies the
   time-varying wetland CH4, which is partly why the Adder ignores this
   module since 30/05/2023 — see Adder comments line 92, 96.)
6. **LPJG-modelled total CH4** — `Extractor` reads `mch4.out`, sums
   12 monthly grid columns, multiplies by gridcell area
   (`cdtarea(lat, lon, 1.25, 1.25)` — assumes a 1.25° × 1.25° grid in g
   then converts g → Tg).

### N2O paths

1. **Manure management direct N2O, scenario 2010-2100** —
   `NitrogenEmissions::startCalculation_nitrogen_scenario_2010_2100`
   reads PLUM, calls `Calculator::calcN20ManureManagement` (Eq 10.25,
   direct only), accumulates per year, converts Kg→Tg.
2. **Managed-soils N2O, scenario** — same function, then triggers
   `myPlumDataProcessor.readFertilizerData()` (which calls
   `FileManager::loadFile2(plumFertlizerPath)` → returns
   `(year, kg_N_total)`), applies `calcN2OManagedSoils(FSN_FON)` per year
   with default `EF1_avg=0.01`, then **adds** to `myN2OData` element-wise:
   ```105:108:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/src/NitrogenEmissions.cpp
   		for (int i = 0; i < myN2ODataManagedSoils.size(); i++)
   		{
   			myN2OData[i].value += myN2ODataManagedSoils[i].value;
   		}
   ```
3. **Manure direct N2O, historic 1961-2009** —
   `startCalculations_historic_nitrogen_1961_2009` reads
   `livestock-counts.csv` and applies `calcN20ManureManagement` per
   row, summed across the 10 species columns.
4. **Managed-soils N2O, historic** — reads `arablelands.csv` into
   `arable_land_areas[266][49]` (A) / `[266][58]` (B), then reads
   `n2ofertilizer.csv` (kg N per ha per year) row-aligned, multiplies
   element-wise, converts Kg→Tg, adds to the historic vector.
   **In version A, this loop has a clear bug** — `getline(ss, temp,
   ',')` is called instead of `getline(ss, fertvalue_kg_per_ha_arable_land,
   ',')`, so `fertvalue_kg_per_ha_arable_land` keeps its initial empty
   value and the contribution evaluates to `atof("") = 0`. B fixes this:
   ```289:291:landsymm_lpjg_imogen_coupled_model/version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/src/NitrogenEmissions.cpp
   					getline(ss, fertvalue_kg_per_ha_arable_land, ',');
   					double fert_value = atof(fertvalue_kg_per_ha_arable_land.c_str());
   					double arable_land = arable_land_areas[rows][i - 5];
   ```
5. **LPJG-modelled total N2O** — `Extractor` reads `ngases.out` and
   sums `N2O_soil + N2O_fire` per grid×year, multiplies by cell area,
   converts Kg→Tg with an extra `1e-4` for ha→m² (the column units in
   ngases.out are kg/m²).

### CO2 paths

The Intermediary itself **does not model CO2 mechanistically**. CO2 in
the IMOGEN-bound output comes purely from:
- IIASA `co2_emissions_annual_historical_rcpRCP_lpjg.txt` for 1850-1960
  (years where LPJG is not yet running).
- LPJ-GUESS `cflux.out` `NEE` column, area-weighted and converted to
  TgC/yr, for 1961-2100.
The merge happens in `Adder::startAddition` populating
`cflux_iiasa_co2_1850_1960_lpjg_2100`. Note: this means *fossil* CO2 is
not in this output stream — that comes from `IIASA_non_lpjg` (CMIP5 file
`co2_emissions_annual_historical_rcpRCP_non_lpjg.txt`) which is read but
whose values flow through a parallel pipeline outside `Adder` (probably
into IMOGEN's controller; this is Subagent 4/7's territory, not ours).

---

## 9. Double-counting prevention

The README explicitly identifies double-counting prevention as the
intermediary's central job:

> "It is imperative that a computationally effective intermediary
> preprocessor is set-up to extract the relevant data from LPJ-GUESS
> output, add appropriate non-natural emissions data and preprocess
> them for IMOGEN input during forwarded coupled runs."

The mechanism is encoded in the IIASA dataset split itself:
- IIASA values are pre-disaggregated into two files for each
  RCP/scenario:
  - `ch4_n2o_annual_historical_rcpRCP_lpjg_simulated.txt`
    — the **LPJG/IPCC-simulated** components of the IIASA total
    (natural fluxes, agriculture, wetlands, etc.). This is what gets
    *replaced* by LPJG+IPCC outputs going forward.
  - `ch4_n2o_annual_historical_rcpRCP_non_lpjg_simulated.txt`
    — fossil energy, transport, industry, waste, etc. This is **always
    retained** because LPJG/IPCC don't model these.

The merge logic is in `Adder::startAddition`. For each year `i ∈ [firstyear, lastyear]`:

```57:111:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/src/Adder.cpp
	if (scenario == "cmip5")
	{
		where_full_iiasa_covers_backwards = 1961;
		region_for_lpjg_ipcc_histroic_start = 1960;
		region_for_lpjg_ipcc_histroic_end = 2010;
		benchmark_to_zero_arrays_or_to_step_midway = 111;
	}

	// cmip6 dataset starts at 1991
	if (scenario == "cmip6")
	{
		where_full_iiasa_covers_backwards = 1990;
		region_for_lpjg_ipcc_histroic_start = 1989;
		region_for_lpjg_ipcc_histroic_end = 2010;
		benchmark_to_zero_arrays_or_to_step_midway = -29;
	}

	for (int i = firstyear; i <= lastyear; i++)
	{

		if (i < where_full_iiasa_covers_backwards)
		{

			myTotalMethaneData[i - firstyear].value = IIASA_non_lpjg_1850_2100[i - firstyear].value1 + IIASA_lpjg_1850_2100[i - firstyear].value1;
			...
		}

		// Region for LPJG historic + ipcc histroic (owi +fao)
		else if (i > region_for_lpjg_ipcc_histroic_start && i < region_for_lpjg_ipcc_histroic_end)
		{
			myTotalMethaneData[i - firstyear].value = IIASA_non_lpjg_1850_2100[i - firstyear].value1 + Historic_methane_1961_2009[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value + LPJGMethane[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
			...
		}
		else
		{

			myTotalMethaneData[i - firstyear].value = IIASA_non_lpjg_1850_2100[i - firstyear].value1 + IPCCMethane[i - firstyear - 160].value + LPJGMethane[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
			...
		}
	}
```

Three regimes:
1. **Pre-LPJG period (1850 ≤ y < 1961 cmip5; 1850 ≤ y < 1990 cmip6)**:
   `IIASA_non_lpjg + IIASA_lpjg` — uses both IIASA components, since
   neither LPJG nor IPCC has data there.
2. **Historic LPJG/IPCC region (1961 ≤ y < 2010)**:
   `IIASA_non_lpjg + Historic_(IPCC-OWI-FAO) + LPJG_natural`.
   IIASA's *lpjg-simulated* series is dropped for these years, and
   replaced by the OWI/FAO-driven IPCC tier-1 + LPJG natural.
   (Wetlands CH4 from the static `Wetlands` module **is intentionally
   removed** — see comments at lines 92 and 96 of `Adder.cpp`: "removed
   methane here since LPJG is producing it now | 30.05.2023".)
3. **Scenario region (2010 ≤ y ≤ 2100)**:
   `IIASA_non_lpjg + IPCCMethane (PLUM 2010-2100) + LPJG_natural`.

So: double-counting is avoided by *partitioning by year* (IIASA-simulated
LPJG component is used **only** before LPJG starts; otherwise
LPJG+OWI/FAO/PLUM-IPCC takes over) **and by source** (IIASA's `non_lpjg`
file always contributes; its `lpjg` file is masked out where LPJG/IPCC
have data). The CO2 path is analogous in `cflux_iiasa_co2_1850_1960_lpjg_2100`.

There is no smoothing across the IIASA→IPCC boundary in the current
code path (the smoothing block at `Adder.cpp` lines 114-164 is commented
out; `centeredMovingAverage` is defined but never invoked). The
"Emissions Handling Methodology.docx" describes a "spline harmonization"
strategy as the *intended* approach — that strategy is **not implemented
in the C++ Intermediary** and is described as part of the Python
replacement workflow (Step 6 in the docx).

The 160 magic number on lines 103, 105, 107, 109 corresponds to
`IPCCMethane`'s indexing offset: `IPCCMethane` spans 2010-2100 (91
elements, index 0 = 2010); `i - firstyear - 160` for `i = 2010`,
`firstyear = 1850` gives `index = 0`. This is hard-coded and only
correct when `firstyear == 1850`.

**The merge is currently disabled** in both A and B — `Main.cpp`'s
Adder/Extractor/Wetlands lines are commented out (see §4). So at present
the C++ Intermediary, when run, produces only the per-SSP IPCC-PLUM
methane and N2O scenario outputs and never builds the combined
IMOGEN-ready file. The pre-existing
`Data/Intermediary/Emissions/total_methane_nitrogen_rcp26ssp1.txt` (and
`...rcp85ssp5.txt`) demonstrate what those outputs *did* look like when
the Adder was run in a previous build.

---

## 10. A vs B diff

`diff -rq` shows: 12 modified files, 2 new files (`Logger.h`,
`Logger.cpp`), no removed files. Headline changes:

**Newly added in B:**
- `include/Logger.h` + `src/Logger.cpp` — singleton timestamped logger
  with `DEBUG`/`INFO`/`WARNING`/`ERROR` levels writing to `pathToLogFile`.
  Used pervasively by every other B class.
- New config keys for diagnostic outputs (rice, historic enteric,
  historic manure, historic fertilizer, scenario manure, scenario
  fertilizer):
  ```15:23:landsymm_lpjg_imogen_coupled_model/version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/config.txt
  historicEntericMethaneOutputFilePath=Data\Intermediary\Emissions\historic_enteric_methane_1961_2009.txt
  historicManureManagementMethaneOutputFilePath=Data\Intermediary\Emissions\historic_manure_management_methane_1961_2009.txt
  historicRiceCultivationMethaneOutputFilePath=Data\Intermediary\Emissions\historic_rice_cultivation_methane_1961_2009.txt
  historicNitrogenManureOutputFilePath=Data\Intermediary\Emissions\historic_nitrogen_manure_1961_2009.txt
  historicNitrogenFertilizerOutputFilePath=Data\Intermediary\Emissions\historic_nitrogen_fertilizer_1961_2009.txt
  ```

**Behavioural changes in B (mostly bugfixes + safety):**
- `Calculator.cpp` (118→353 lines): every function gains
  NaN/Inf/negative checks, error-logged early returns, and verbose debug
  logging.
  - `calcNitrogenExcretion` formula corrected (A had `rate*mass*1000/365`,
    which produces nonsense; B switches to the standard
    `(rate/1000) * mass * 365` for kg N/animal/yr).
  - `calcCH4ManureManagement` now goes via the new
    `Maps::getEmissionFactorForMethaneByManureManagementSystem` accessor
    (which trims keys and returns -1.0 on miss) instead of the unguarded
    nested `[][]` indexing in A (which silently inserts a zero default).
  - `calcCH4Wetlands` adds the `EQUATION 3A.1 V4_p_Ap3` reference.
- `MethaneEmissions.cpp` (290→434 lines): adds 3 new historic streams
  (`myHistoricEntericCH4Data_1961_2009`,
  `myHistoricManureManagementCH4Data_1961_2009`,
  `myHistoricRiceCultivationCH4Data_1961_2009`) and 3 corresponding
  setter/printer pairs. Year window for the historic loop expanded to
  `< 2020`. **The historic call is itself commented out
  (`startCalculations()` only invokes the future scenario in B), so all
  the new historic vectors are unused at runtime.** Rice cultivation
  toggle flipped to `true` by default. NaN/Inf guards added throughout.
- `NitrogenEmissions.cpp` (270→451 lines): symmetric refactor — adds
  manure-only and fertilizer-only output streams for both historic and
  scenario; expands historic window to `< 2020`; **fixes the
  `fertvalue_kg_per_ha_arable_land` reading bug** described in §8;
  changes the fertilizer-array dimension from `[266][49]` to `[266][58]`
  to cover 1961-2018; the historic call is also commented out in
  `startCalculations()`, but the diagnostic logging is kept.
- `Maps.cpp` (81→367 lines): every accessor rewritten to trim inputs,
  use `find()` instead of `[]`, return `""` / `-1.0` on miss instead of
  silently inserting zero, and log errors. New explicit accessor
  `getEmissionFactorForMethaneByManureManagementSystem`.
- `Maps.h` (944→1493 lines): a much larger
  `MAP_WETLANDS_COUNTRIES_CLIMATE` (covers more countries / spelling
  variants like `Eq. Guinea`, `Cabo Verde`, etc.); added `Table 10.14`
  comments; numeric values for the IPCC tables themselves are unchanged.
- `Wetlands.cpp` (72→133 lines): per-row CSV format **changed** — now
  `year,country,value,...` (3 leading columns) instead of A's
  `country,variable,year,measure,value`. Constant year-broadcast loop
  shortened to 1961-2020 (vs 1961-2100 in A). Adds NaN / zero
  diffusive-rate guards.
- `FileManager.cpp` (129→154 lines): adds Logger calls at every write.
- `UtilityHandler.h/.cpp`: `ltrim`/`rtrim`/`trim` moved from `.cpp` to
  inline definitions in `.h` so every TU sees them (B uses `trim`
  pervasively in Maps).
- `Main.cpp` (241→327 lines): copious Logger calls; CMIP6 scenario
  detection logs an info line; **methane block is now commented out**
  (only nitrogen runs); CMIP6 wetlandsAreaFilePath is corrected.
- A typo bug in A's `Main.cpp` line 128 (`config["wetlandsMethaneEmissionsOutputPathwetlandsAreaFilePath"]`,
  i.e. two keys concatenated) is fixed in B (`config["wetlandsMethaneEmissionsOutputPath"]`,
  line 186).
- B's `config.txt` adds `ssp=2,rcp=45` to the scenario list (now
  `1,2,5`/`26,45,85`); changes `wetlandsAreaFilePath` to
  `GLWD_v2_country_wetland_CH4_peat_openwater_km2.csv`; uses a different
  livestock-counts file (`FAOSTAT_data_en_1-6-2026-livestock-counts.csv`,
  dated **6 Jan 2026** — note this is "future" relative to B's
  source-file mtime of 21 Mar; the data file pre-dates the code rev).

**No-change**: `Adder.cpp` (still commented out in `Main.cpp`),
`Extractor.cpp` (only trivial whitespace), `Parameters.cpp`,
`PlumDataProcessor.cpp` (modulo whitespace), all `Templates.h`,
`DualStreamBuffer.h`.

### Net assessment of A vs B

B is a **safety-and-instrumentation pass** over A: bugfix
(`calcNitrogenExcretion`, fertilizer csv read), defensive map lookups,
universal logging, additional diagnostic outputs. Functionally the
**same active code path** (PLUM scenario CH4 + N2O), but B narrows it
further (methane block commented in B). **Neither version actually
runs the merge to IMOGEN-ready output.** B is the more current and
runnable code; A is what produced the reference outputs sitting in
`Data/Intermediary/Emissions/`.

---

## 11. Bugs, dead code, hardcoded paths, TODO/FIXME

### Outright bugs (real, would affect numerics)

1. **A: `calcNitrogenExcretion` (lines 73-76)** computes
   `rate * mass * 1000/365` — that is, kg N per animal per **(non-day,
   wrong-units)**. The IPCC expression is `(rate / 1000) * mass * 365`
   for an annual per-animal nitrogen excretion in kg N. B fixes it to
   the IPCC form. **Every N2O manure-management value computed by A is
   wrong by a factor of `(1000·365)² / 365² ≈ 10⁶ × … `** — actually it
   is off by a factor of `1000·365 / (365/1000) = 10⁶` per animal,
   which would yield N2O numbers ~10⁶× too large if it weren't for the
   `1e-9` Kg→Tg final convert which leaves the relative error baked in.
   The pre-existing reference outputs in `Data/.../nitrogen_ssp1.txt`
   were therefore computed with the buggy formula.
2. **A: `NitrogenEmissions::startCalculations_historic_nitrogen_1961_2009`**
   reads `n2ofertilizer.csv` but never assigns to
   `fertvalue_kg_per_ha_arable_land`; the variable is uninitialised,
   `atof("") = 0`, so the historic fertilizer N2O contribution is always
   zero. Fixed in B.
3. **A: `Adder::set_actual_lpjg_simulated_IIASA_1850_2009_lpjg_2010_2100`
   line 239** — `int vecSize = lastyear = firstyear + 1;` is an
   assignment-to-`lastyear` (mutates a global!) instead of a comparison
   or addition. This function is dead code, but the side effect on
   `lastyear` would be catastrophic if it ever ran.
4. **A and B: `MethaneEmissions::startCalculation_methane_modelled_historic_1961_2009`
   in A uses `myHistoricMethane_modelled_1961_2009.resize(49)` for
   1961-2009 = 49 elements (correct), but in B `resize(59)` and
   `< 2020` filter — i.e. covers 1961-2019 = 59 elements. The fact
   that the variable is still called `_1961_2009` in B is misleading.
5. **B: `MethaneEmissions::startCalculation_methane_modelled_historic`
   declares a 13-element FAO_items array but only iterates `i < 10`** —
   the species mapping in B is therefore reordered relative to A
   (e.g. `Camels` is at index 2 in B's array but never iterated;
   `Meat Poultry` is at index 4 instead of index 9; `Meat cattle` is at
   index 3 instead of index 2). This means even if the historic call
   were re-enabled, B's species labels would no longer line up with the
   `livestock-counts.csv` columns (which are still: Asses, Buffalo,
   Cattle, Goats, Horses, Mules, Pigs, Sheep, Turkeys, Chickens). Latent
   bug; currently masked by the call being commented out.
6. **A and B: livestock-counts.csv has 11 species columns
   (Asses, Buffalo, Cattle, Goats, Horses, Mules, Pigs, Sheep, Turkeys,
   Chickens) but the historic loops only consume 10**, and they treat
   the *first* column (Asses) as the value following two key columns
   (`Entity, Code`). In A the first `getline` after `country` reads the
   `Code`, so the species columns are correctly indexed from index 0;
   in B the `getline` for `code` is **commented out**:
   ```56:63:landsymm_lpjg_imogen_coupled_model/version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Intermediary/Code/src/MethaneEmissions.cpp
   		getline(ss, temp, ','); // country
   		myPLUMData.country = temp;

   		// getline(ss, temp, ','); // code || N/A

   		getline(ss, temp, ','); // year

   		myPLUMData.year = stoi(temp);
   ```
   So B reads the Country Code as the year and `stoi("AGO")` will throw
   `std::invalid_argument`. Together with bug #5 this is enough to make
   B's historic path crash if ever re-enabled. (It's currently dead.)

### Dead code

- `Calculator::loadCountries()` (called only in the commented constructor
  body) reads `C:\GitHub\LPJ_IMOGEN_coupling\IPCC\data\countries.txt`
  on a Windows path with `exit(200)` if missing.
- The entire `Adder`, `Extractor`, `Wetlands`, and `PlumDataProcessor`
  pipelines except for `PlumDataProcessor::readFertilizerData` (which
  loads a pre-computed PLUM_Fertilizer file). The
  `extractDataFromPlumLandUseFiles*` methods that would *produce* that
  file from raw PLUM `*_LandUse*` files are also never invoked from
  `Main`.
- B's `Wetlands::startCalculation` is rewired but `Main` does not call
  it.
- A's smoothing block in `Adder.cpp` lines 114-164.
- A's `Adder::set_actual_lpjg_simulated_IIASA_1850_2009_lpjg_2010_2100`
  (with the mutating-global bug noted above).
- All the **historic** (1961-2009) methane / nitrogen calculation paths
  in B (commented out at the call sites in
  `startCalculations`).

### Hardcoded paths / Windows assumptions

- `config.txt` ships with `baseDirectory=C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\`
  — every run requires editing this. (`Main` does Linux path-separator
  conversion at runtime, but cannot guess the user's actual root.)
- `Calculator.cpp` line 17 / 18:
  `const string fileName = "C:\\GitHub\\LPJ_IMOGEN_coupling\\IPCC\\data\\countries.txt";`
  in `loadCountries()`. Dead, but Windows-specific.
- `FileManager::deleteFile` shells out to `del` (Windows), not `rm`;
  unused.
- `Main.cpp` opens config via `"../config.txt"`, requiring the binary
  to be run from `bin/` exactly.
- The grid resolution in `Extractor::startLPJGDataExtraction` is
  hard-coded to `cdtarea(lat, lon, 1.25, 1.25)` — assumes a 1.25° × 1.25°
  LPJG output grid.
- Magic number `160` in `Adder::startAddition` (the IPCC offset for
  `firstyear=1850`); breaks if `firstyear != 1850`.
- Magic number `49`/`59` for the size of historic vectors instead of
  computing from year window.

### TODO / FIXME

- `include/Maps.h` line 328 (A) / 515 (B):
  `{"Pasture Range and Paddock", 0.004}, // TODO:` — annotation on the
  N2O EF for pasture range and paddock; no follow-up text.
- That is the **only** TODO in the entire C++ tree. No FIXME, XXX, HACK
  markers anywhere.

### Style / safety notes

- `exit(100)` / `exit(200)` calls litter the FileManager and Calculator
  on any error — no exception propagation, no stack unwinding.
- `printToFile(vector<dataHolder2>, …)` (lines 97-106 of
  `FileManager.cpp` A) **forgets to `closeFile`** the writer (the
  `dataHolder1` overload does close it). Probably benign because
  `fstream` destructor closes on scope exit, but inconsistent.
- Several constructors print to `cout` ("Calculator constructor invoked",
  "File Manager constructed!" …); B mostly silences these, but B's
  `FileManager` still prints ("File Manager constructed!", "File Manager
  destroyed!").

---

## 12. Open questions

1. **Does it actually run end-to-end?** Both A and B compile cleanly
   under `g++ -std=c++17` on Linux. Static analysis says: A's active
   code path (CH4 + N2O scenario) should run if the file paths in
   `config.txt` resolve — and indeed
   `Data/Intermediary/Emissions/methane_ssp1.txt`,
   `nitrogen_ssp1.txt`, `IPCC_OWI_FAO_methane_1961_2009_ssp1.txt`,
   `total_methane_nitrogen_rcp26ssp1.txt` etc. are present, suggesting
   that A *was* successfully run at least once (presumably with the
   Adder block uncommented). For B, the current `Main` runs only the
   N2O block; whether anyone has executed it in this state is unclear.
2. **Has the corrected `calcNitrogenExcretion` (B) ever been used to
   regenerate the reference `nitrogen_*.txt` outputs?** If not, every
   downstream artifact in `Data/Intermediary/Emissions/` is built on
   the buggy A formula.
3. **Is the missing Adder step the reason `Intermediary_py/` was
   created?** The `Emissions Handling Methodology.docx` describes a
   "Univariate Spline" smoothing harmonization — that is much easier in
   Python and matches what `imogen_ghg_controller_FULL` looks like
   (Subagent 6 confirms?). Strong inference: yes, the C++ merge is
   abandoned.
4. **Why is the year window mismatch in B (`< 2020` for "1961-2009"
   loops, vector size 59) and the corresponding bug in the
   FAO_items[13] ordering both present in B, even though the historic
   call is commented out?** Probably someone started a refactor and
   abandoned mid-stream. The state should be flagged before anyone
   re-enables the historic calls.
5. **What does PLUM currently provide for fertilizer N for 2010-2100?**
   The C++ Intermediary expects a pre-aggregated 2-col text file at
   `Data/Intermediary/Input/PLUM_Fertilizer_SSPx.txt`. The
   `PlumDataProcessor::extractDataFromPlumLandUseFiles*` paths that
   would *produce* this file from raw PLUM gridded data exist but are
   never called. Is there an out-of-tree script (Matlab? bash?) that
   does the pre-aggregation, or are those files manually produced? If
   PLUM ever changes its column schema, the extractor will silently
   produce wrong totals (it picks up "FQ" columns by integer index `13`
   and `20+7k`).
6. **Wetlands CH4 is constant in time in this module.** Is that a
   conscious decision (because LPJG provides time-varying wetland CH4)
   or an unfinished feature? B's smaller year-broadcast window
   (1961-2020 vs A's 1961-2100) suggests someone was rethinking it.
7. **Magic number 160 in `Adder::startAddition`** assumes `firstyear =
   1850`. If a user sets `firstyear = 1900` in `config.txt`, the
   IPCCMethane/IPCCNitrogen indexing into the merged output will
   silently shift. There is no guard.
8. **Indirect N2O (Eq 10.26-10.29 + Ch11 EF4/EF5)** is not modelled at
   all even though the `MAP_FRACGAS` table is loaded into Maps.h. Is
   this a deliberate Tier 1 simplification or pending implementation?
9. **What grid resolution does the LPJ-GUESS output the Intermediary
   was built against actually have?** `Extractor::cdtarea(lat, lon,
   1.25, 1.25)` hard-codes 1.25° × 1.25°, but the LPJG default is 0.5°.
   Either the run setup uses a 1.25° grid (e.g. for IMOGEN
   compatibility) or the area aggregation is wrong by a constant
   factor (~6.25× too large per cell).
10. **The `livestock_counts_path` in B's config.txt is
    `FAOSTAT_data_en_1-6-2026-livestock-counts.csv`** — file dated 6
    January 2026. Has this updated-format file been validated against
    the `Entity,Code,Year,…` column schema the code expects? With B's
    commented-out `getline(ss, temp, ',')` for the `Code` column, any
    change in column layout will silently corrupt year parsing.

> Cross-references for follow-up:
> - Subagent 4 (IMOGEN C++): does IMOGEN really expect the
>   `total_methane_nitrogen_rcpRCPsspSSP.txt` 3-col format?
> - Subagent 6 (Python intermediary): confirm it implements the
>   spline-harmonization in the .docx and supplies all three gases
>   (CO2, CH4, N2O) — including the merge step the C++ Adder is
>   missing.
> - Subagent 7 (controller / orchestration): is the C++ Intermediary
>   even invoked by the run setup, or is the Python replacement
>   wired in already?
