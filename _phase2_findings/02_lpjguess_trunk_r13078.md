# Phase 2 — Subagent 2 Report
# LPJ-GUESS source tree at `Integrations/trunk/trunk_r13078`

Investigated path:
`landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/`

Comparison reference (only used to confirm fork lineage):
`lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`

Read-only investigation; no source files were modified.

---

## 1. Top-level structure of `trunk_r13078`

The tree is the standard "LPJ-GUESS Version 4.1" layout from the Lund SVN trunk (r13078), forked into LandSyMM and then again into the coupled-model framework. Directory inventory at the top level (per `ls`):

| Directory / File | Purpose |
|---|---|
| `CMakeLists.txt` | Top-level CMake script (project = `guess`) |
| `cmake/` | CMake helpers: `FindNetCDF.cmake`, `add_guess_sources.cmake`, `add_test_sources.cmake` |
| `framework/` | Core C++ framework: `framework.cpp/.h`, `guess.cpp/.h`, `parameters.cpp/.h`, `inputmodule.cpp/.h`, `outputmodule.cpp/.h`, `outputchannel.cpp/.h`, `archive.cpp/.h`, `parallel.cpp/.h`, MPI hooks, command-line parsing, etc. |
| `modules/` | Process modules + I/O modules (see §3 for input modules, §6 for output modules). 41 source files. |
| `libraries/` | Bundled support libraries: `gutil`, `plib`, `guessnc` |
| `command_line_version/main.cpp` | Entry point for the CLI binary |
| `windows_version/` | DLL entry point for the LPJ-GUESS Windows Shell |
| `parallel_version/` | Job-submit templates: `aurora.tmpl`, `gimle.tmpl`, `multicore.tmpl`, `pbs_legacy.tmpl`, `simba.tmpl` |
| `cru/` | CRU-NCEP I/O sub-module (separate `guessio` dir) |
| `data/` | `env/`, `gridlist/`, `ins/` — sample inputs and ins-files (incl. `ins/integrated-4.1-ins/` containing the coupled IMOGEN-LPJG ins set) |
| `tests/` | Unit tests (CATCH framework, gated by `UNIT_TESTS` CMake var) |
| `benchmarks/` | Benchmark scripts (Linux-only) |
| `reference/` | `guessdoc.pdf` technical manual (no `scientific_description.pdf` here, unlike the LandSyMM fork) |
| `doxygen/` | Doxygen config |
| `LICENCE.TXT`, `readme.txt`, `GitlabDockerFile`, `.gitignore`, `.gitlab-ci.yml`, `.vscode/` | Misc admin / CI / tooling. The `.gitlab-ci.yml` and `.vscode/` exist only in this trunk, not in the standalone LandSyMM fork. |
| `build_imogen/` | A pre-existing build tree from a previous run on the original developer's machine (`/home/bampoh-d/Desktop/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/...` per the `CMakeCache.txt` header) — has stale `Makefile`, `cmake_install.cmake`, `guess.log`, etc. Useful only as evidence of the build configuration that was last used. |

The `readme.txt` is the unmodified LPJ-GUESS v4.1 demo readme. It does **not** mention IMOGEN coupling at all.

---

## 2. Build system and dependencies

### 2.1 CMakeLists files

Three CMake files configure the build:

- `trunk_r13078/CMakeLists.txt` (top-level, 184 lines)
- `trunk_r13078/framework/CMakeLists.txt` (40 lines, just lists framework sources)
- `trunk_r13078/modules/CMakeLists.txt` (84 lines, lists module sources)

Top-level `CMakeLists.txt` highlights:

```1:9:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/CMakeLists.txt
################################################################################
# CMake configuration file for building LPJ-GUESS
#
# To build LPJ-GUESS with this build system cmake needs to be installed.
# If it's not installed it can be downloaded for free from www.cmake.org.
#

cmake_minimum_required(VERSION 2.8.12.2...3.5.2)
project(guess)
```

The build is *unconditional* with respect to IMOGEN. There is **no `IMOGEN`/`COUPLED`/`HAVE_IMOGEN` CMake variable, define, or target**. The IMOGEN-coupling source files (`imogen_input.cpp`, `imogencfx.cpp`, `imogenlogger.cpp`, `climatemodel.cpp`, `intermediary.cpp`) are listed unconditionally in `modules/CMakeLists.txt`:

```36:41:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/CMakeLists.txt
  imogen_input.h
  imogencfx.h
  intermediary.h
  climatemodel.h
  imogenlogger.h
  )
```
```76:81:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/CMakeLists.txt
  imogen_input.cpp
  imogencfx.cpp
  intermediary.cpp
  climatemodel.cpp
  imogenlogger.cpp
  )
```

Conditional definitions that the top-level CMakeLists *does* set:

| Flag | Source | Notes |
|---|---|---|
| `-DHAVE_NETCDF` | `find_package(NetCDF QUIET)` succeeds | Required by `cfinput`, `cfxinput`, `firemipinput`. Not used by `imogen_input` or `imogencfx` (they parse FORTRAN-style ASCII, not NetCDF). |
| `-DHAVE_MPI` | `find_package(MPI QUIET)` succeeds | Used inside `imogen_input.cpp` / `imogencfx.cpp` for `MPI_Barrier`. |
| `-D_CRT_SECURE_NO_WARNINGS / _SCL_SECURE_NO_WARNINGS` | MSVC | Windows-only |
| `-Wno-deprecated-declarations` | non-MSVC | Linux/macOS |
| `CMAKE_CXX_STANDARD 11` | always | Note: `imogenlogger.cpp` re-implements a tiny subset of `std::filesystem` because the project targets C++11, not C++17. |

`build_imogen/CMakeCache.txt` records that the last build used:
- `CMAKE_CXX_COMPILER:FILEPATH=/usr/bin/c++` (gcc-14 wrappers for `ar`/`ranlib`)
- `CMAKE_BUILD_TYPE:STRING=Release` → `-O3 -DNDEBUG`
- No `CMAKE_CXX_FLAGS` overrides

### 2.2 Output binaries

```118:135:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/CMakeLists.txt
# Specify the executable to build, and which sources to build it from
add_executable(${guess_command_name} ${guess_sources} command_line_version/main.cpp)

# Rule for building the unit test binary
if(BENCHMARK)
  message("We are in benchmarks, not creating executable for tests.")
else()
  add_executable(runtests ${guess_sources} ${test_sources})
  target_link_libraries(runtests ${LIBS})
endif()
```

Outputs: `guess` (Unix CLI), `guesscmd` + `guess.dll` (Windows shell), `runtests`. The IMOGEN engine is **statically linked into the same `guess` binary** — there is no separate `imogen` executable; the coupling is in-process (see §5).

### 2.3 Input-module registration (selecting an input at runtime)

The build links *all* input modules into the binary. The user picks one with `-input <name>` on the CLI. The framework calls:

```317:319:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/framework/framework.cpp
const char* input_module_name = args.get_input_module();

auto_ptr<InputModule> input_module(InputModuleRegistry::get_instance().create_input_module(input_module_name));
```

Available registered input modules (from `REGISTER_INPUT_MODULE("name", Class)`):

| Name (CLI `-input X`) | Source file | Class |
|---|---|---|
| `demo` | `modules/demoinput.cpp:18` | `DemoInput` |
| `cf` | `modules/cfinput.cpp:23` | `CFInput` |
| `cfx` | `modules/cfxinput.cpp:25` | `CFXInput` |
| `firemip` | `modules/firemipinput.cpp:25` | `FireMIPInput` |
| `imogen` | `modules/imogen_input.cpp:175` | `ImogenInput` |
| `imogencfx` | `modules/imogencfx.cpp:177` | `IMOGENCFXInput` |

(The README at the top of `lpj-guess_imogen_landsymm/` mentions five; the sixth, `firemip`, is a niche fire-MIP variant and not relevant to IMOGEN.)

---

## 3. Input modules — full anatomy

The five input modules relevant to this investigation are: `demo`, `cf`, `cfx`, `imogen`, `imogencfx`. The cfx variant is the upstream LandSyMM/SSR working horse for normal LPJ-GUESS runs, while `imogen` and `imogencfx` are the IMOGEN-coupling code paths. (Subagent 5 covers the `cfx` data side; here we describe its surface only.)

### 3.1 `demo` — `modules/demoinput.cpp` (361 lines), `demoinput.h`

Reference implementation provided by mainline LPJ-GUESS for the demo data set. Reads four ASCII files via the legacy `readfor()` formatted-read API:

```217:220:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/demoinput.cpp
file_temp=param["file_temp"].str;
file_prec=param["file_prec"].str;
file_sun=param["file_sun"].str;
file_soil=param["file_soil"].str;
```

- Climate: monthly mean temp / precip / sunshine, interpolated to daily values via `interp_climate()` + Gerten precipitation generator (`prdaily`).
- CO2: scalar from `param["co2"].num` (constant for whole run).
- N deposition: scalar from `param["ndep"].num`, distributed evenly across the year.
- Constraint at line 172: works only with `weathergenerator==INTERP` and `firemodel∈{GLOBFIRM,NOFIRE}`.
- No "done"-file polling, no IMOGEN coupling.

### 3.2 `cf` — `modules/cfinput.cpp` (1233 lines), `cfinput.h`

Standard CF-NetCDF input module. Wrapped in `#ifdef HAVE_NETCDF` (file body is a no-op without NetCDF). Reads daily/monthly CF-NetCDF for temp, prec, insolation, and optionally `wetdays`, `pres`, `specifichum`, `relhum`, `wind`, `min_temp`, `max_temp`. Uses `GuessNC::CF::GridcellOrderedVariable` from `libraries/guessnc`. Same `Lamarque::NDepData` N-dep path as cfx/imogen. Sample registration:

```23:23:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/cfinput.cpp
REGISTER_INPUT_MODULE("cf", CFInput)
```

### 3.3 `cfx` — `modules/cfxinput.cpp` (2118 lines), `cfxinput.h`

The "extended" CF-NetCDF input. Adds (beyond `cf`) multi-file climate streams (e.g. historical → SSP), per-CFT N-fertiliser, popdens (SimFire), GGCMI multi-part support (`setup_multipart`/`reset`), and the SSR/PLUM/LandSyMM features. Used for non-coupled LandSyMM runs.

```25:25:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/cfxinput.cpp
REGISTER_INPUT_MODULE("cfx", CFXInput)
```

This is the input used by the *standalone* LandSyMM fork. The IMOGEN-coupling fork extends `cfx` into `imogencfx` (§3.5).

### 3.4 `imogen` — `modules/imogen_input.cpp` (936 lines), `modules/imogen_input.h` (233 lines)

**Loose-coupling** input module. Reads pre-generated IMOGEN climate output that already exists on disk; LPJ-GUESS does **not** invoke any IMOGEN code at runtime in this mode.

#### 3.4.1 Format read (FORTRAN-ASCII text, NOT NetCDF)

From `imogen_input.cpp:567-579`:

```567:579:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogen_input.cpp
  // The temperature, precipitation and radiation files should be in FORTRAN ASCII text
  // format and contain one-line records for each coord.
  
  // The following is a sample record from the temperature file:
  //   " 281.250  82.500   236.450   236.450   ... 237.630   237.630   237.630"
  // corresponds to the following data:
  //   longitude 281.25 deg (0=greenwich, longitude goes from 0..360 )
  //   latitude 82.5 deg (+=N, latitude goes from -90 to 90)
  //   daily temperatures (K) 236.45 (1st-Jan), ..., 237.63 (31st-Dec)
  //
  // Precipitation is in (mm/day)  (convert for LPJ to kg m-2 s-1)  1m (m3/m2) * 1000 kg/m3 * 86400s/1day
  // Shortwave radiation is in (W/m^2)
```

Each calendar year's data lives in a file whose path embeds the year via the placeholder `Y` (replaced with the year number — **not** the standard `%Y` strftime form). Helper at `imogen_input.cpp:97-133`:

```115:128:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogen_input.cpp
    //long position = fname.find("%Y"); // find returns -1 if it doesn't find what it's looking for
	long position = fname.find("Y");
    if (position != -1) {

		//if it doesn't return -1, fname is a year(int) so we gotta convert to string. We do that by making use of the to_string template created above
      xtring syear = to_xtring(year);
      
      if (fmakedir) {
        xtring pathname = pathbase + fname.left(position) + syear;
        _mkdir((char*) pathname, 0775);
      }
      
      //fname = fname.left(position) + syear + fname.right(fname.len() - xtring("YYYY").len() - position); //generates file name
	  fname = fname.left(position) + syear + fname.right(fname.len() - xtring("YYYY").len() - position); //generates file name
    }
```

This is fragile — any literal `Y` in the path before the year placeholder will be replaced. The original LPJ-GUESS convention is `%Y` (commented out and replaced with bare `Y`).

#### 3.4.2 Climate ingestion flow

1. `init()` (line 233) reads `file_gridlist` line-by-line, fills `all_lon` / `all_lat` / `coord_line`, then maps each gridcell to a line index in the year-1871 spinup temperature file via `lon_lat_lines_in_file` (line 466) using either exact match or a `searchradius` (Euclidean lon/lat distance — see §10).
2. `getclimate()` (line 747): per gridcell per day. On `date.day==0`, if the year has not been read yet, calls `readenv()` (line 563) to slurp the entire year of *all* gridcells from `file_temp`, `file_prec`, `file_insol`, optionally `file_wetdays`, optionally `file_dtr` (for BVOC) into `all_temp[store_index][igrid][d]` etc.
3. `get_climate_for_gridcell` (line 617) extracts per-day values for the current gridcell. **Monthly data path** multiplies precipitation by 30 then runs `prdaily()` and `interp_monthly_means_conserve` to produce daily values. **Daily data path** copies through.
4. CO2 is read each year from `file_co2` (one file per year, path again year-templated): see line 832.
5. Temperature unit conversion: line 871 — `climate.temp = dtemp[date.day] - 273.15;` (IMOGEN files are in Kelvin).
6. N deposition: `ndep.get_one_calendar_year` + `distribute_ndep` produces daily NH4/NO3 values. **Note**: in `imogen_input.cpp` the call to `ndep.getndep(...)` is **commented out at line 728**, so `ndep` is uninitialised when `get_one_calendar_year` is invoked at line 855. This is a latent bug already present in the standalone LandSyMM fork; the `imogencfx` variant fixed it (see §3.5).

#### 3.4.3 No "done"-file polling here

`ImogenInput::getclimate` simply tries to open the file `file_temp` for the requested year and `fail()`s if absent. There is **no polling, no retry, no synchronisation barrier with an IMOGEN process**. This is the loose-coupling assumption: the climate is generated ahead of time and laid out on disk in the expected directory tree.

#### 3.4.4 Hard-coded year ranges

```192:198:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogen_input.h
  static const int FIRST_HIST_YEAR = 1901;
  //static const int FIRST_HIST_YEAR = 2012;
  static const int NYEAR_RUN = 200;

  static const int FIRST_SPINUP_YEAR = 1871;
  static const int NYEAR_SPINUP = 30;
```

The `firsthistyear`/`lasthistyear` ins-file overrides exist (declared at line 201-202 of the cpp), but `FIRST_SPINUP_YEAR` and `NYEAR_SPINUP` are baked-in.

#### 3.4.5 Other observations

- `extract_line_data` (line 366): the inner loop "if (monthly) { for (12 idx) iss>>data[idx] }" — there is no `else` branch; **daily** files would not actually be parsed despite a `bool monthly` option. Latent bug.
- Search-radius logic comparison uses `(file_lons[iline] - lons[igrid])*(file_lons[iline] - lons[igrid])` for the longitude squared term **without** wrapping at the 180° meridian (line 494) — also a latent bug for points near ±180°.

### 3.5 `imogencfx` — `modules/imogencfx.cpp` (1105 lines), `modules/imogencfx.h` (241 lines)

**Tight-coupling** input module: hosts the in-process IMOGEN engine via `RUN_IMOGEN_ENGINE()` from `climatemodel.cpp`. This is the file the user has been calling "the CF Extended one we've encountered before". File header attribution: `\author Peter Anthoni, Extended by DBampoh`.

Conceptually, `imogencfx` is forked from `imogen_input` and adds:

1. **Many ins-file parameters** for the IMOGEN engine (paths to pattern files, climatology files, scenario emissions, FAIR constants, SSP/RCP toggles, intermediary paths, etc.). Declared in the constructor `IMOGENCFXInput::IMOGENCFXInput()` at lines 179–339, all written to `IMOGENConfig::*` global namespace symbols (see §3.5.3).

2. **Extra climate variables** in the per-gridcell-per-year arrays: `drelhum`, `dwind` (in addition to temp/prec/insol/dtr/wetdays). Member declarations at `imogencfx.h:140-147`:

```140:147:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogencfx.h
	/// Relative humidty for current gridcell and current year
	double drelhum[Date::MAX_YEAR_LENGTH];

	/// Wind for current gridcell and current year
	double dwind[Date::MAX_YEAR_LENGTH];

	/// Daily N deposition for one year
	double dNH4dep[Date::MAX_YEAR_LENGTH], dNO3dep[Date::MAX_YEAR_LENGTH];
```

3. **The IMOGEN engine kick-off**: the very last action in `init()` is to call into the C++ port of IMOGEN and exit:

```481:484:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogencfx.cpp
	//In a coupled IMOGEN-LPJG Run, IMOGEN climate data has to be first generated 
	RUN_IMOGEN_ENGINE(); 
	exit(200);
```

⚠️ **Bug — `exit(200)` after `RUN_IMOGEN_ENGINE()`**: this terminates the LPJ-GUESS process at the *end* of `init()`, **before** any gridcell is simulated. With this line in place, `imogencfx` cannot complete a real LPJ-GUESS run. It is a debug-shortcut. It does **not** exist in the standalone LandSyMM fork (see §8 and §10). git/file mtime: `imogencfx.cpp` was last modified 2026-03-21 — likely the date this `exit(200)` was added. The body of `init()` after line 484 (vector resizing, gridlist sanity, lon/lat line lookup, `soilinput.init()`) is therefore unreachable.

4. **Validation guards** for `simulation_mode × interpolation_mode`:

```456:474:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogencfx.cpp
	// Online Mode Constraints

	if (IMOGENConfig::simulation_mode == "online" && IMOGENConfig::interpolation_mode == "NNC") {
		fail("Error! No support for nearest neighbour interpolation on climate for online runs\n");
	}

	if (IMOGENConfig::simulation_mode == "online" && IMOGENConfig::interpolation_mode == "IDWP") {
		fail("Error! No support for inverse distance weighted interpolation on patterns for online runs\n");
	}

	// Offline Mode Constraints

	if (IMOGENConfig::simulation_mode == "offline" && IMOGENConfig::interpolation_mode == "IDWP") {
		fail("\nError! No support for inverse distance weighted interpolation on patterns for offline runs\n");
	}

	if (IMOGENConfig::simulation_mode == "offline" && IMOGENConfig::interpolation_mode == "NNP") {
		fail("Error! No support for nearest neighbour interpolation on patterns for offline runs\n");
	}
```

Recognised values are `online`/`offline` × `NNC`/`NNP`/`IDWC`/`IDWP`. A typo (`!= NNC` etc.) would silently pass through.

5. **N deposition is actually called** here, unlike in `imogen_input`:

```895:896:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogencfx.cpp
	// Get nitrogen deposition, using the found CRU coordinates
	ndep.getndep(param["file_ndep"].str, cru_lon, cru_lat,Lamarque::parse_timeseries(ndep_timeseries));
```

6. **Unit conversion regression for temperature**: `imogencfx::getclimate` does **not** subtract 273.15:

```1039:1041:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogencfx.cpp
		climate.temp = dtemp[date.day];
		climate.prec = dprec[date.day];
		climate.insol = dinsol[date.day];
```

Compare `imogen_input.cpp:871` (`climate.temp = dtemp[date.day] - 273.15;`). The IMOGEN files are in Kelvin, so feeding them straight into `climate.temp` (which the rest of LPJ-GUESS treats as °C) would force-cap leaf-level fluxes at the K range. Either:
- `imogencfx` is meant to receive already-Celsius arrays from the engine via shared memory rather than the file path, OR
- this is a unit-conversion bug carried over from a refactor.

The body never executes anyway given §3.5(3), but if the `exit(200)` is removed, this line will be activated.

7. **Hard-coded BLAZE check disabled**: in `imogen_input.cpp:620-622` BLAZE is rejected; in `imogencfx.cpp:792-794` the check is **commented out**:

```792:794:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogencfx.cpp
		/*if (firemodel == BLAZE) {
			fail("%s: sorry, imogencfx input not setup for firemodel BLAZE, needs extra climate data and GWGEN", __FUNCTION__);
		}*/
```

The author intends BLAZE to work via the extra wind/relhum that `imogencfx` reads, but `firemodel==BLAZE` is not actually plumbed through `get_climate_for_gridcell` (it ignores `drelhum`/`dwind` even when monthly).

8. **Member shadowing**: `imogencfx.h:208-209` comments out the local `firsthistyear`/`lasthistyear` declarations:

```207:210:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogencfx.h
	// FIXME: move to parameters.cpp/h as in the PLUM code
	//int firsthistyear;  // the first year of this run
	//int lasthistyear;  // the last year of this run
	int nyears;
```

So `imogencfx` reads the **global** `firsthistyear`/`lasthistyear` declared in `framework/parameters.h:591-592` (and defined as `-1` in `parameters.cpp:123-124`, parsed from the ins-file via `declare_parameter` at `parameters.cpp:794-796`). Plus `firstoutyear`/`lastoutyear` (lines 595-596 / 798-800). Consistent with the rest of LandSyMM.

#### 3.5.1 Comparison summary `imogen` ↔ `imogencfx`

See §4.

### 3.6 `imogenlogger` — `modules/imogenlogger.cpp` (160 lines), `imogenlogger.h` (52 lines)

A simple singleton text logger that writes both to `stdout` and to a timestamped file under `<DIR_COMMON>/IMOGEN/`:

```81:106:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogenlogger.cpp
    // Create logs directory using POSIX mkdir
    std::string logDir = baseDir + "/IMOGEN";
  /*  if (!::create_directory(logDir)) {
        std::cout << "[ERROR] Failed to create log directory: " << logDir << " (errno: " << errno << ")" << std::endl;
        return;
    }*/

    // Generate timestamped filename
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S");
    std::string timestamp = ss.str();
    std::string logFilePath = logDir + "/imogen_" + timestamp + ".log";

    // Open log file
    logFile_.open(logFilePath, std::ios::out | std::ios::app);
    if (!logFile_.is_open()) {
        std::cout << "[ERROR] Failed to open log file: " << logFilePath << std::endl;
        return;
    }
```

API:

| Method | What it does |
|---|---|
| `getInstance()` | Singleton. |
| `initialize(baseDir, minLevel)` | Opens `<baseDir>/IMOGEN/imogen_<YYYYMMDD_HHMMSS>.log`. |
| `debug/info/warn/error(msg)` | One log line: `[IMOGEN LOGGER][YYYY-MM-DD HH:MM:SS] [LEVEL] msg` |
| `setMinLevel`, `~ImogenLogger` | level mgmt + file close |

Notes / gotchas:
- The `std::mutex` member is commented out (`//std::mutex mutex_;` at line 48). All logging is thread-unsafe. With OpenMP/MPI it could interleave.
- The directory creation block is commented out (line 82-85). The logger relies on `RUN_IMOGEN_ENGINE` to have called `filesystem_dkb::create_directory` before initialising the logger (see `climatemodel.cpp:154-157`); otherwise `logFile_.open` will fail and the logger silently degrades to stdout-only.
- `enum class LogLevel { DEBUG, INFO, WARN, ERROR }` declared at line 14. Default minimum level is `INFO`.
- Default `baseDir` is `(char*)IMOGENConfig::DIR_COMMON` — meaning if you forget to override via `initialize(...)`, logs go under whatever `DIR_COMMON` is set to in the ins-file.
- `imogen_input.cpp` does **not** initialise the logger; only `RUN_IMOGEN_ENGINE` does. So in loose-coupled runs the logger is dormant.

---

## 4. `imogencfx` vs `imogen_input` — comparative table

| Aspect | `imogen` (`ImogenInput`, 936 LOC) | `imogencfx` (`IMOGENCFXInput`, 1105 LOC) |
|---|---|---|
| Coupling style | Loose: reads pre-generated IMOGEN climate files | Tight: invokes `RUN_IMOGEN_ENGINE()` in-process from `init()` |
| File format | FORTRAN-ASCII text per year, `lon lat v1 v2 ...` | Same on disk (engine writes the same ASCII format), plus engine state files (`fa_ocean.dat`, `dtemp_o.dat`, `CO2.dat`, `RF_all.dat`) |
| Climate variables | T, P, insol, wetdays, dtr (BVOC) | T, P, insol, wetdays, dtr, **rel-humidity, wind** (extra arrays present but un-used by `get_climate_for_gridcell`; daily-path copy disabled) |
| CO2 | Per-year file (one file per calendar year, name templated) | Same on the LPJG read side, but the engine also writes a separate `<DIR_COMMON_OUT>/IMOGEN/output/<year>/CO2.dat` |
| N deposition | `ndep.getndep` is **commented out** (line 728); subsequent `get_one_calendar_year` uses uninitialised `ndep` → bug | `ndep.getndep` is correctly called (line 896) |
| Temperature unit conversion | `climate.temp = dtemp[d] - 273.15;` | `climate.temp = dtemp[d];` (no Kelvin→°C conversion — bug, see §3.5(6)) |
| Land-cover / management init | `landcover_input.init()` and `management_input.init()` in `getgridcell` first-call (line 668-670) | Same (line 841-843) |
| BLAZE fire model | Explicit `fail()` at line 621 if `firemodel==BLAZE` | `fail()` is commented out at line 792-794 |
| ins-file parameters declared | searchradius, lon/lat_offset_to_midpoint, ndep_timeseries, firsthistyear, lasthistyear, monthly_imogen | All of the `imogen` set **plus** ~80 IMOGEN-engine parameters (DIR_COMMON, DIR_PATT, DIR_CLIM, FILE_SCEN_EMITS, FILE_NON_CO2_VALS, KAPPA_O, F_OCEAN, LAMBDA_L/O, MU, Q2CO2, TAU_DECAY_*, CO2/CH4/N2O_INIT_PPMV/PPBV, ANLG, ANOM, REGRID, NONCO2_EMISSIONS, LPJG_CFLUX, LAND_FEED, OCEAN_FEED, CO2_RF_FAIR, …) and ~30 Intermediary parameters (scenario, baseDirectory, methaneEmissionOutputFilePath, basePathPLUMdata, lpjgMethane, …) and ~5 coupling-control flags (YEAR1, IYEND, YEAR1_LPJG, SPINUP, KEEPRUNNING, FIRSTCALL) and ~4 mode flags (simulation_mode, feedback_mode, interpolation_mode, ssprcp). Full list at `imogencfx.cpp:213-336`. |
| `firsthistyear`/`lasthistyear` storage | Class members + ins-file params declared in ctor | Removed from class; uses globals from `framework/parameters.cpp` |
| `RUN_IMOGEN_ENGINE` call | Never | At `init()` line 482, then `exit(200)` |
| ImogenLogger initialisation | Never | Inside `RUN_IMOGEN_ENGINE` |
| MPI sync | `MPI_Barrier` in ctor / dtor under `HAVE_MPI` | Identical |
| Calling `getgridcell`/`getclimate` after init | Yes | Currently **unreachable** because of `exit(200)` |
| Search-radius lon-wrap fix | Latent bug, no wrap | Same latent bug (copy-paste of code path) |

### How they map to coupling modes (cross-reference with the README)

- **Loose coupling** (off-line): IMOGEN was run beforehand, climate data persisted to disk; LPJ-GUESS reads them with `-input imogen` using `global_coupled_imogen_lpjg.ins`.
- **Tight coupling** (in-process, currently labelled "online" in the source): the IMOGEN engine is compiled into LPJG; LPJG calls `RUN_IMOGEN_ENGINE` once at start of `init()`. The engine runs its own `KEEPRUNNING` loop that *itself* polls for an `imogen_lpjg.txt` flux file from a future LPJG year (see §5). LPJG is selected with `-input imogencfx` and the ins-file imports `imogen_intermediary.ins`.

---

## 5. "done"-file synchronisation protocol

The user's mental model — "LPJ-GUESS polls for a `done` file produced by IMOGEN" — is **inverted** by the current code. In the LandSyMM-style tight coupling implemented here, the **IMOGEN engine** (running inside the LPJG process) is the polling end. LPJG's role is to *produce* a flux file and a `done` file each year. Specifically:

### 5.1 Where polling lives

`modules/climatemodel.cpp` (3319 lines, lives in LPJ-GUESS modules dir but is the C++ port of the Fortran IMOGEN engine — Subagent 4 covers it in depth). Entry point:

```151:159:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/climatemodel.cpp
int RUN_IMOGEN_ENGINE() {

    //create output dir here
    filesystem_dkb::create_directory(std::string((char*)IMOGENConfig::DIR_COMMON_OUT) + "/IMOGEN/");

    //Initialize Imogen logger
    ImogenLogger::getInstance().initialize((char*)IMOGENConfig::DIR_COMMON_OUT, ImogenLogger::LogLevel::INFO);
```

The polling is the inner loop:

```300:394:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/climatemodel.cpp
    bool runnowExist, runnowOpen, runfluxExist, runfluxOpen;
    bool runnonco2fluxExist, runnonco2fluxOpen, doneExist, errorExist;
    bool runnow, keepRunning = IMOGENConfig::KEEPRUNNING;
    ...
    // Main KEEPRUNNING loop
    keepRunning = IMOGENConfig::KEEPRUNNING;
    while (keepRunning) {
        runnow = false;
        ...
        while (!runnow) {
            std::this_thread::sleep_for(std::chrono::seconds(3));
            std::cout << "." << std::flush;

           // doneExist = filesystem::exists(dirCommon + "/LPJG_main/IMOGEN/done");
            doneExist = true; 
            ...
            runfluxExist = filesystem_dkb::exists(fileLpjgFlux);
            ...
            errorExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/error");
            runnowExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/imogen_lpjg.txt");
            ...
            if (runnowExist && !runnowOpen && runfluxExist && !runfluxOpen && doneExist &&
                (!nonco2Emissions || (runnonco2fluxExist && !runnonco2fluxOpen))) {
                runnow = true;
                ...
            }

            if (errorExist) {
                std::cout << "Error in LPJ-GUESS\n";
                return 1;
            }
        }
```

### 5.2 Mechanism, decoded

Per outer iteration of `while (keepRunning)`:

1. Engine spins in `while (!runnow)`, sleeping 3 s between iterations and printing `.` to stdout.
2. Each iteration `stat()`s four paths (relative to `IMOGENConfig::DIR_COMMON`):
   - `<DIR_COMMON>/LPJG_main/IMOGEN/imogen_lpjg.txt` — flag file LPJG drops to say "I've finished a year, here are my fluxes"
   - `<FILE_LPJG_FLUX>` — the actual carbon flux table from LPJG
   - optionally `<FILE_LPJG_CH4_N2O_FLUX>` if `NONCO2_EMISSIONS` (i.e. CH4/N2O too)
   - `<DIR_COMMON>/LPJG_main/IMOGEN/error` — abort signal
3. The *real* `done` file check is **commented out**:

```330:331:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/climatemodel.cpp
           // doneExist = filesystem::exists(dirCommon + "/LPJG_main/IMOGEN/done");
            doneExist = true; 
```

   So `doneExist` is **hardcoded `true`** in this build. Any logic that depends on the LPJG-side `done` file *as an additional barrier* is bypassed.

4. The `runnowOpen`/`runfluxOpen` checks (a "is the file currently being written?" guard via `is_open()`) are also commented out — see lines 334, 341, 350. So the consistency check `runnowExist && !runnowOpen && ...` simplifies to "the files exist", with no anti-race protection beyond the 3 s sleep.

5. Timeout / retry: there is **no timeout**. The polling loop is unbounded. If LPJG never produces a flux file, IMOGEN polls forever. The only escape is dropping a literal file named `error` at `<DIR_COMMON>/LPJG_main/IMOGEN/error` (returns 1 from `RUN_IMOGEN_ENGINE`, then `exit(200)` per §3.5(3) terminates the LPJG process with status 200).

### 5.3 The `done` file the engine *writes*

After consuming LPJG fluxes for the year, the engine deletes the `done` file and creates a fresh one in two places:

```544:546:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/climatemodel.cpp
                std::ofstream doneFile(dirCommon + "/LPJG_main/IMOGEN/done", std::ios::out | std::ios::trunc);
                doneFile.close();
                filesystem_dkb::remove(dirCommon + "/LPJG_main/IMOGEN/done");
```
```938:945:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/climatemodel.cpp
                // Write done file for LPJ-GUESS
                ...
                    std::ofstream file97(dirCommonOut + "/IMOGEN/output/" + thisYear + "/done");
```

Two distinct done files exist: `<DIR_COMMON>/LPJG_main/IMOGEN/done` (consumed by the engine; LPJG would write it) and `<DIR_COMMON_OUT>/IMOGEN/output/<year>/done` (written by the engine to mark "year produced; safe for LPJG to advance"). The latter is the file whose existence subsequent LPJG simulation steps would poll for, but as noted in §3.5(3) the `exit(200)` short-circuits that.

### 5.4 Where in LPJ-GUESS does the polling happen?

**It does not happen in the LPJ-GUESS framework code at all.** All polling lives inside the IMOGEN engine module (`modules/climatemodel.cpp`) which is invoked synchronously from `IMOGENCFXInput::init()`. Subagents 3/4 will trace this in depth — I flag here that the file-presence checks LPJG's reads-done logic *should* care about (`<DIR_COMMON_OUT>/IMOGEN/output/<year>/done`) are not currently checked anywhere on the LPJG side that I can find. There is **no** `getclimate`-level retry loop that waits for the engine — which would actually be expected in tight coupling. Instead the design seems to be: the engine ran *all* years up-front in `init()`, then LPJG loops over the output. With `exit(200)` blocking that, LPJG never gets that far.

**Uncertainty flagged**: the original design intent of who-polls-whom is unclear from the trunk_r13078 source alone. The variable names (`runnowExist`, `imogen_lpjg.txt`) suggest a previous design where LPJG and IMOGEN ran as *separate* processes (true client-server), and the in-process port has retained the polling but neutered the synchronisation primitives (`doneExist=true`; closed-file checks commented out).

---

## 6. Output-module IMOGEN stubs

The user's hypothesis ("there are output files paralleling the standard `.out` files but for IMOGEN climate inputs that were stubbed/incomplete") is **confirmed**. Concrete evidence:

### 6.1 Declared output files in `modules/miscoutput.cpp`

```119:136:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/miscoutput.cpp
	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	//IMOGEN-RELATED FILES
	//std::cout << "print_imogen_output" << IMOGENConfig::print_imogen_output << std::endl;
	if (IMOGENConfig::print_imogen_output==true) { //use an input model based chek here: FIXME: DKB
		declare_parameter("file_t_anom", &file_t_anom, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_wet", &file_wet, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_sw_anom", &file_sw_anom, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_p_anom", &file_p_anom, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_fa_ocean", &file_fa_ocean, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_dtemp_o", &file_dtemp_o, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_dtemp_anom", &file_dtemp_anom, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_co2", &file_co2, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_relhum_anom", &file_relhum_anom, 300, "Imogen Relative Humidity Anomalies.");
		declare_parameter("file_tmin_anom", &file_tmin_anom, 300, "Imogen Minimum Temperature Anomalies.");
		declare_parameter("file_tmax_anom", &file_tmax_anom, 300, "Imogen Maximum Temperature Anomalies.");
		declare_parameter("file_wind_anom", &file_wind_anom, 300, "Imogen Wind Anomalies.");
	}
```

Twelve ins-file parameters are declared — but **all twelve description strings are wrong** (most read "Imogen Temperature Anomalies." even for prec, sw, ocean, wet days).

### 6.2 Output `Table` objects declared but never wired

`modules/miscoutput.h:172`:

```172:172:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/miscoutput.h
	Table out_t_anom, out_wet, out_sw_anom, out_p_anom, out_fa_ocean, out_dtemp_o, out_dtemp_anom, out_co2, out_relhum_anom, out_tmin_anom, out_tmax_anom, out_wind_anom;
```

A grep across the entire `trunk_r13078/` tree finds **zero** uses of `out_t_anom`, `out_sw_anom`, `out_p_anom`, `out_fa_ocean`, `out_dtemp_anom`, `out_relhum_anom`, `out_wind_anom`, `out_tmin_anom`, `out_tmax_anom`. They are defined and never assigned, never registered with `create_output_table`, and never written via `outannual`/`outdaily`.

### 6.3 `getImogenData` random-stub

`modules/miscoutput.h:69-79` — within `class MiscOutput`:

```69:79:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/miscoutput.h
	double getImogenData(int lower, int upper) {
		// Create a random device and seed the Mersenne Twister engine
		std::random_device rd;
		std::mt19937 gen(rd());

		// Define the range using uniform_real_distribution
		std::uniform_real_distribution<> distrib(static_cast<double>(lower), static_cast<double>(upper));

		double number = distrib(gen);
		return std::round(number * 1000.0) / 1000.0;
	}
```

A literally-random number generator labelled "getImogenData". Searches for callers of `getImogenData` find **only the definition** — it has no callers. This is a placeholder where, in the intended implementation, real IMOGEN data would have been pulled into `MiscOutput` for output. The plumbing was never finished.

### 6.4 What is *actually* output by `MiscOutput` for IMOGEN

Nothing. The stubs above are dead code. The IMOGEN engine itself (`climatemodel.cpp`) writes its own files to `<DIR_COMMON_OUT>/IMOGEN/output/<year>/` (e.g. `CO2.dat`, `fa_ocean.dat`, `dtemp_o.dat`, `done`, plus monthly climate output if `DAILYOUT==false`). Those are produced by the engine, not by an LPJG output module. There is no second IMOGEN output module elsewhere in `modules/`.

### 6.5 Conclusion

The intended integration (LPJ-GUESS's `MiscOutput` writing IMOGEN climate-input fields per gridcell per year, paralleling the standard `.out` tables) was scaffolded but never completed. Removing the dead `out_*` table declarations and the `getImogenData` random stub would be safe.

---

## 7. Tight vs loose coupling — `.ins` parameters and input modules

| Coupling style | CLI `-input` flag | Class | Required `.ins` files (per `data/ins/integrated-4.1-ins/`) | Distinguishing parameters |
|---|---|---|---|---|
| **Loose** ("offline") | `imogen` | `ImogenInput` | `main.ins` + `global.ins` (or `global_coupled_imogen_lpjg.ins` if you want the coupled-style spinup) + `crop_n.ins` + `wetlandpfts.ins` | `searchradius`, `lon_offset_to_midpoint`, `lat_offset_to_midpoint`, `ndep_timeseries`, `firsthistyear`, `lasthistyear`, `monthly_imogen` (~7 params total). Pre-existing per-year `T_anom.dat`/`P_anom.dat`/`SW_anom.dat`/`WET.dat`/`DTEMP_anom.dat`/`CO2_all.dat` on disk. |
| **Tight** ("online") | `imogencfx` | `IMOGENCFXInput` | `main.ins` + `global_coupled_imogen_lpjg.ins` + `imogen_intermediary.ins` (or equivalent imports) | All loose params + ~80 `IMOGENConfig` engine parameters + ~30 Intermediary parameters (see `imogencfx.cpp:213-339`). Critical control flags: `simulation_mode "online"`, `interpolation_mode "IDWC"`, `KEEPRUNNING`, `FIRSTCALL`, `YEAR1`, `IYEND`, `YEAR1_LPJG`. |

The README says there are 5 input modules (`demo`, `cf`, `cfx`, `imogen_input`, `imogen_cfx`); these correspond to the 5 `REGISTER_INPUT_MODULE` calls listed in §2.3 (firemip is a 6th but unrelated to coupling). The IMOGEN-coupling-relevant pair is `imogen` (loose) ↔ `imogencfx` (tight).

The `simulation_mode` ins parameter is recognised inside `imogencfx.cpp:331` and gated against `interpolation_mode` at 458-474. There is **no separate compile-time flag** distinguishing the modes — both classes are always linked, the choice is made at runtime by the `-input` argument.

The per-IMOGENConfig flag `KEEPRUNNING` (declared in `parameters.cpp:283`) is the on/off for the coupling polling loop in `RUN_IMOGEN_ENGINE`. `FIRSTCALL` controls one-time initialisation inside the engine. They both flow from ins → IMOGENConfig namespace globals; LPJG's framework does not change them.

---

## 8. Diff vs the standalone LandSyMM fork

Goal: confirm whether `trunk_r13078` is the same fork as `lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`.

### 8.1 Top-level `diff -rq`

Filtered to non-build-tree changes:

```
Only in trunk/trunk_r13078/data/ins:                  integrated-4.1-ins   (the coupled-LPJG ins set, see §9 cross-link)
Files .../framework/parameters.cpp                    differ
Only in trunk/trunk_r13078/:                          .gitignore
Only in trunk/trunk_r13078/:                          .gitlab-ci.yml
Files .../modules/cfxinput.cpp                        differ
Files .../modules/climatemodel.cpp                    differ
Files .../modules/imogencfx.cpp                       differ
Files .../modules/imogenlogger.cpp                    differ
Files .../modules/imogenlogger.h                      differ
Only in LandSyMM_LPJ-GUESS/reference:                 ~$essdoc.doc       (Word lock file leftover)
Only in LandSyMM_LPJ-GUESS/reference:                 scientific_description.pdf
Only in trunk/trunk_r13078/:                          .vscode
```

The `CMakeLists.txt` files are byte-identical. All other source files are byte-identical. Only six source files differ.

### 8.2 Per-file substantive deltas

- **`modules/imogencfx.cpp`** — exactly **one line of difference**:

  ```
  483d482
  < 	exit(200);
  ```

  trunk_r13078 has `exit(200);` immediately after `RUN_IMOGEN_ENGINE();` in `init()`; the LandSyMM fork does **not**. **This is the most impactful regression in the trunk version.** It was added 2026-03-21 (per file mtime). The function from line 484 onward is dead code in the trunk.

- **`modules/cfxinput.cpp`** — two cosmetic diffs:
  - Line 339: trivial comment-style change.
  - Line 1131: error vs warning policy when a gridcell is missing climate data — trunk says `Error` and continues with the per-year `fail`-style log; LandSyMM says `Warning: skipping to next gridcell, ...`. Behavioural impact, but irrelevant to IMOGEN coupling.

- **`framework/parameters.cpp`** — comments only. The `IMOGENConfig` member declarations have descriptive trailing comments in the LandSyMM fork (e.g. `xtring DIR_PATT; //For pattern scalers`); in the trunk those comments were stripped. No semantic change.

- **`modules/climatemodel.cpp`** — comment refinements and a `#define logger ImogenLogger::getInstance()` macro use difference. The LandSyMM fork uses `logger.debug(...)` consistently; the trunk explicitly writes `ImogenLogger::getInstance().debug(...)` in some early places and uses `logger.` further down. Functionally equivalent.

- **`modules/imogenlogger.h`** — removal of an annotation comment ("`//for IMOGEN`" stripped) and lacks the `//not necessary?` annotation on the commented-out mutex_ line. Cosmetic.

- **`modules/imogenlogger.cpp`** — three cosmetic diffs:
  - Line 20: typo fix in a comment (`<C++!7` → `<C++17`); the **trunk has the typo**, the LandSyMM fork is correct.
  - Line 114: comment annotation removed.
  - Line 120: comment annotation `//use dprintf later?` removed.

### 8.3 Conclusion

**`trunk_r13078` is the same fork** as the standalone `lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`. They share the same revision base. The trunk has:
- The integrated-4.1-ins data set (an extra ins-file dir in `data/ins/`)
- CI/IDE files (`.gitignore`, `.gitlab-ci.yml`, `.vscode/`)
- The `exit(200);` debug shortcut after `RUN_IMOGEN_ENGINE()`
- Some cosmetic comment regressions (a comment typo `<C++!7` was *introduced* into the trunk vs the cleaner LandSyMM)
- The error-vs-warning behavior change on missing gridcell data

Otherwise it is byte-identical. **There is no IMOGEN-specific code that exists in trunk_r13078 but not in the standalone LandSyMM fork** — the LandSyMM fork already carries all the imogen/imogencfx/imogenlogger/climatemodel/intermediary/IMOGENConfig machinery. The trunk_r13078 directory is essentially a snapshot of that fork plus the coupled-framework ins-file set, with one accidental debug regression.

---

## 9. The 6 ins-file dirs in `trunk_r13078_test/`

Inventory (with mtime of `main.ins`, structural classification):

| # | Dir | mtime of `main.ins` | Classification | Notes |
|---|---|---|---|---|
| 1 | `integrated-4.1-ins` | 2025-06-12 | **Loose-coupling reference** | `import "global.ins"`; no `imogen_intermediary.ins` import; `firsthistyear 1850 .. lasthistyear 2100`; uses Windows paths (`C:\GitHub\…`) for forcing data and the gridlist `gridlist_test2.txt`. The `global_coupled_imogen_lpjg.ins` lives here too but is not imported by `main.ins`. Looks like the working "non-IMOGEN baseline" for parity testing. |
| 2 | `integrated-4.1-ins2` | **2025-07-02** (most recent) | **Tight-coupling, Windows** | Identical layout to ins1 except imports `imogen_intermediary.ins` and `!imports global_coupled_imogen_lpjg.ins` (commented). Uses `gridlist_in_62892_and_climate.txt`. `firsthistyear 1901`. Includes 2 years of forcing files (1850-2014 + 2015-2100). Most recently modified. |
| 3 | `integrated-4.1-ins2-wsl` | 2025-06-12 | **Tight-coupling, WSL/Linux** sibling of ins2 | Same content as ins2 but Windows paths rewritten to `/mnt/c/...` for WSL. **Imports `imogen_intermediary.ins` (uncommented)** unlike ins2 where it is uncommented too. Most ins2 NetCDF inputs are commented out (lines 63–96 of main.ins). Looks like a partial/wip linux port. `state_path` still contains a Windows path (`C:/GitHub/...`) — inconsistency. Reduced gridlist (`gridlist_test2.txt`). |
| 4 | `lpj-guess_git-svn_20190828` | n/a | **Empty placeholder** | `ls` returns no files. Intended to hold a snapshot of an earlier revision. **Recommend retiring** — there's nothing here. |
| 5 | `lsa_hist_base_ipsl` | 2025-06-12 | **Linux scenario, IPSL forcing** | Linux cluster paths under `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/...`. `firsthistyear 1850`. Imports `global_coupled_imogen_lpjg.ins` and (commented) `imogen_intermediary.ins`. Setup oriented around historical-base IPSL run (the directory name hints at "Land-Sea-Atmosphere historical base IPSL"). Forcing-NetCDF set is from IPSL-CM6A-LR; no `gridlist_test*` so meant for the full-scale historical re-run. |
| 6 | `ssr-ins-version` | **2024-11-12** (oldest) | **SSR/pasture-fertilizer test variant** | Older reference using `pasture_fert_test_european_apps/gridlist_sites_test.txt` for the gridlist. `firsthistyear 1850`. Imports `global_coupled_imogen_lpjg.ins` and (commented) `imogen_intermediary.ins`. No `imogen_intermediary.ins`/`crop_n_stlist.simplePFT.remap10_g2p.N0-60-200-1000.ins` files in the dir — looks pre-coupled-framework. **Likely retire candidate** (predates IMOGEN-LPJG coupling work) but should be archived first as it's the only one tied to the `pasture_fert_test_european_apps` dataset. |

### Recommendations

| Action | Targets | Rationale |
|---|---|---|
| **Keep as current** | `integrated-4.1-ins2` | Most recent, Windows tight-coupling reference. |
| **Keep as Linux current** | `integrated-4.1-ins2-wsl` (after path cleanup) — fix the leftover `state_path "C:/..."` and fix the partially commented forcing-data block | Linux-ready twin of ins2. |
| **Keep as offline baseline** | `integrated-4.1-ins` | Loose-coupling parity test. |
| **Keep as named-scenario** | `lsa_hist_base_ipsl` | The only Linux-cluster IPSL setup. |
| **Retire** | `lpj-guess_git-svn_20190828` | Empty directory, presumably a half-done svn snapshot. |
| **Archive then retire** | `ssr-ins-version` | Pre-dates current coupling, ties to a no-longer-active dataset. |

---

## 10. Bugs, gaps, dead code, TODOs

Summary of issues discovered (file:line where applicable). **Severity: 🔴 active code, 🟡 latent, 🟢 cosmetic**.

| # | Severity | Location | Issue |
|---|---|---|---|
| 1 | 🔴 | `modules/imogencfx.cpp:483` | `exit(200);` after `RUN_IMOGEN_ENGINE();` terminates LPJG immediately; entire post-engine `init()` body and the rest of the simulation are dead code. Not present in LandSyMM fork. **Must be removed for tight-coupled runs to work.** |
| 2 | 🔴 | `modules/climatemodel.cpp:330-331` | `doneExist = true;` hardcoded; the actual file-stat for the `done` barrier file is commented out. Race-conditional: the polling loop will accept partial flux files. |
| 3 | 🔴 | `modules/climatemodel.cpp:334, 341, 350` | The three `runnowOpen`/`runfluxOpen`/`runnonco2fluxOpen` "is the writer still writing?" guards are commented out. The polling loop has no anti-race protection between `stat(file)` and `open(file)`. |
| 4 | 🔴 | `modules/imogen_input.cpp:728` | `ndep.getndep(...)` is commented out. `ndep` is then used in `getclimate` line 855 (`ndep.get_one_calendar_year`) without ever having been initialised → undefined behaviour for N deposition under loose coupling. |
| 5 | 🔴 | `modules/imogencfx.cpp:1039` | `climate.temp = dtemp[date.day];` — missing `- 273.15` Kelvin→°C conversion that exists in `imogen_input.cpp:871`. Currently unreachable due to bug #1, but will activate the moment `exit(200)` is removed. |
| 6 | 🟡 | `modules/imogen_input.cpp:380-383` & `imogencfx.cpp:553-556` | `extract_line_data` only parses 12 monthly values; the daily branch (`for idx<MAX_YEAR_LENGTH`) is missing — the `if (monthly)` guard short-circuits even when `monthly=false`, so daily IMOGEN files would silently produce zero-arrays. |
| 7 | 🟡 | `modules/imogen_input.cpp:494-495` & `imogencfx.cpp:668-669` | Distance metric uses raw `(file_lons[iline] - lons[igrid])` without antimeridian wrap. Gridcells near ±180° won't match. The first occurrence has a partial workaround (`file_lons[iline] > 180 ? file_lons[iline] - 360 : file_lons[iline]` on the first squared term only — but the second squared term still uses the unwrapped value). |
| 8 | 🟡 | `modules/imogen_input.cpp:116-129` | Year-substitution logic uses `find("Y")` instead of `find("%Y")` — any literal `Y` earlier in the path will be wrongly replaced. Only the `length-of-"YYYY"` constant (4) is correct, the placeholder is bare `Y`. Documented in code comments as intentional but fragile. |
| 9 | 🟡 | `modules/imogencfx.cpp:792-794` | BLAZE-incompatibility `fail()` is commented out; `imogencfx` does **not** plumb `drelhum`/`dwind` to the BLAZE driver in `get_climate_for_gridcell`. Running with BLAZE will silently use zero humidity/wind. |
| 10 | 🟡 | `modules/imogencfx.cpp` & `modules/imogen_input.cpp` | `getNfert(Gridcell&)` declared on the class but never defined. The framework never calls it (it's not in `InputModule` virtual interface). Dead method declaration — same in the LandSyMM fork. |
| 11 | 🟡 | `modules/imogencfx.h:65` & `modules/imogen_input.h:65` | `void year_init(int rank, int calendar_year);` declared but never defined and never invoked by the framework (no `year_init` in `InputModule` virtual interface either). Dead method declaration. |
| 12 | 🟡 | `modules/miscoutput.h:172` and `modules/miscoutput.cpp:122-135` | The 12 IMOGEN climate-output `Table` objects (`out_t_anom`, `out_sw_anom`, …) are declared and have ins-file params declared, but no `create_output_table` calls and no `outannual` writers reference them. Stub plumbing — see §6. |
| 13 | 🟡 | `modules/miscoutput.h:69-79` | `getImogenData(int lower, int upper)` returns a literal random number from a `std::mt19937` engine with `random_device` seed. Has no callers anywhere in the tree. Dead placeholder. |
| 14 | 🟡 | `modules/imogenlogger.cpp:75, 114, 131, 137` | `std::lock_guard<std::mutex>` lines all commented out. Logger is not thread-safe — would race under MPI/OpenMP. |
| 15 | 🟡 | `modules/imogenlogger.cpp:82-85` | The `create_directory(logDir)` call is commented out. Logger silently fails (no log file) if the directory does not yet exist and `RUN_IMOGEN_ENGINE` did not pre-create it. |
| 16 | 🟢 | `modules/imogencfx.cpp:122-135` | All 12 `declare_parameter` description strings for IMOGEN output files are wrong (10 of 12 read "Imogen Temperature Anomalies." regardless of what the file actually contains). |
| 17 | 🟢 | `modules/imogenlogger.cpp:20` | Comment typo `<C++!7` (should be `<C++17`) — typo introduced in trunk relative to LandSyMM fork. |
| 18 | 🟢 | `framework/framework.cpp:30-41, 76-77, 99-164` | Large block of `//#include "climatemodel.h"`, `//ImogenLogger::getInstance()…`, plus the (now deleted) `gen_filename` and `_mkdir` helpers — all commented out. Indicates an earlier refactor that pulled this code into `imogen_input.cpp`/`imogencfx.cpp`. Should be deleted. |
| 19 | 🟢 | `modules/imogencfx.cpp:834` | Comment `// Note that first_call is static, so this assignment is remembered` — incorrect, `first_call` is a regular member, not static. Inherited verbatim from `imogen_input.cpp:660`. |
| 20 | 🟢 | `modules/imogen_input.cpp` (top) | Filename comment claims `ImogenInput.cpp8` (typo — extraneous `8`). Cosmetic. |
| 21 | 🟢 | `modules/imogen_input.h:10` & `modules/imogencfx.h:10` | Both header guards use the **same identifier** `LPJ_GUESS_IMOGEN_INPUT_H`. Including both files in the same translation unit will silently exclude the second — by chance no current TU does this, but it's a guard collision waiting to happen. |
| 22 | 🟢 | `modules/imogen_input.cpp:39-94` | The `_mkdir` helper recursively calls itself `_mkdir(tmp, mode)` — and the only platform-specific `mkdir` it would dispatch to is shadowed by the same name. This is the classic "infinite recursion" pattern often present in copy-pasted recursive `_mkdir` code; the original `mkdir(2)` syscall is commented out (line 88, 92). On Unix this means `_mkdir` recurses but **never actually calls the OS `mkdir`** — directory creation silently fails. Used by `gen_filename(fmakedir=true)` only, currently no callers pass `fmakedir=true` in `imogen_input`/`imogencfx`. Dormant bug. |

---

## 11. Open questions for follow-up

1. **Is the `exit(200);` regression intentional or accidental?** The mtime (2026-03-21) and the absence of any matching change in the LandSyMM fork suggest accidental commit of a debug shortcut. **Action**: ask the developer who last touched `imogencfx.cpp`. If accidental, a one-line revert restores tight-coupling functionality.

2. **What was the original synchronisation contract between LPJG and IMOGEN?** The polling code in `climatemodel.cpp:300-394` has six file-existence checks of which three are bypassed (`doneExist=true`, `runnowOpen` not assigned, `runfluxOpen` not assigned). It is unclear whether:
   (a) the engine was originally a **separate process** that watched a directory shared with a parallel LPJG process, then was ported in-process and the file barriers were partially neutered; or
   (b) the file barriers were always optional and the in-process design relies on year-by-year synchronicity baked into `RUN_IMOGEN_ENGINE`'s `for (iyear=year1; iyear<=iyend; ...)` loop.
   The variable name `LPJG_main` in the path strings (`<DIR_COMMON>/LPJG_main/IMOGEN/done`) hints at design (a). Subagents 3/4 may know.

3. **Where does LPJG actually emit `imogen_lpjg.txt` and the flux file `<FILE_LPJG_FLUX>`?** I did not find any LPJG-side writer for these. They are *read* by the engine (line 528, 538) and the engine *deletes* the `done` barrier (line 546), but the LPJG side that populates them must live somewhere — possibly in `gcpoutput`/`commonoutput` writes that flow into the same path. Worth grepping for `imogen_lpjg.txt` in the wider tree (Subagents 5/6).

4. **Is the `imogen_input` (loose) path expected to be the long-term LandSyMM coupling, with `imogencfx` only used for development/testing?** The README differentiates them but does not state which is canonical. The fact that `imogen_input` has a real Kelvin→°C correction and N-dep deactivation (suggesting it gets N-dep from ins-file `file_ndep` directly elsewhere), while `imogencfx` does not subtract Kelvin and does call `ndep.getndep`, suggests the two were maintained inconsistently.

5. **Why is `printseparatestands` toggled by `LandcoverInput::init()` based on a 50-gridcell threshold (per the comment at miscoutput.h:21-23) when `imogen` and `imogencfx` use a different `landcover_input.init()` call path?** Possibly orthogonal but worth Subagent 6 confirmation when investigating run setups.

6. **The 6 ins-file dirs**: do `lsa_hist_base_ipsl` and `integrated-4.1-ins2-wsl` actually compile with the current trunk? `integrated-4.1-ins2-wsl` has an inconsistent `state_path "C:/..."` left over from Windows — would the WSL run fail on `state_path`? Subagent 6 / shell-experiment can verify.

7. **Output stubs in `MiscOutput`**: were these intended to be wired up but blocked by something concrete (e.g. `IMOGENConfig::print_imogen_output==true` triggering a code path that does not exist)? The `FIXME: DKB` comment at line 122 explicitly flags it as TODO.

---

## Appendix A — Quick file map

| Concern | Files |
|---|---|
| Coupling polling loop | `modules/climatemodel.cpp:300-394`, `:544-546`, `:938-945` |
| Engine entry | `modules/climatemodel.cpp:151`, `modules/climatemodel.h:253` |
| Engine kick-off from LPJG | `modules/imogencfx.cpp:481-484` |
| Loose-coupling input | `modules/imogen_input.cpp/.h` |
| Tight-coupling input | `modules/imogencfx.cpp/.h` |
| Logger | `modules/imogenlogger.cpp/.h` |
| IMOGENConfig namespace (declaration) | `framework/parameters.h:437-561` |
| IMOGENConfig namespace (definition) | `framework/parameters.cpp:215-389` |
| Output stubs | `modules/miscoutput.cpp:121-136`, `modules/miscoutput.h:122-123, 172` |
| Build glue | `CMakeLists.txt`, `modules/CMakeLists.txt:36-41, 76-81` |

---

*End of report.*
