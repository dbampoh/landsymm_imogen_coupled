# Phase-2 Finding 07 — GCM patterns & the three regrid utilities

Subagent 7 / Phase 2.
Scope: catalog the GCM-pattern directories under `Common-directory/IMOGEN-codebase/patterns/`, map the three C++ regrid utilities (`Regrid`, `FastRegrid`, `RegridLPJG`), and sketch the path to using the (currently unused) CMIP6 NetCDF patterns.
**Read-only.** No files outside this report were modified. IMOGEN's internal pattern-reading code, LPJ-GUESS, and the Intermediary are explicitly out of scope (other subagents).

All paths are relative to:
`landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/`
(abbreviated below as `FRAMEWORK/`).

---

## 1. GCM patterns inventory

### 1.1 Directory enumeration

There are **36 directories** under `FRAMEWORK/Common-directory/IMOGEN-codebase/patterns/` plus one `readme.log`. (The task brief says "38" — the actual on-disk count is 36. The ≈22-GCM Zelazowski-style CMIP3 set was later extended in CMIP5 to 34 GCMs; the two extras here are the legacy HadCM3 dir and the CMIP6 collection dir.)

`readme.log` contents:

```
#imogen CMIP5 patterns
see also /pd/data/lpj/input_data/IMOGEN_patterns/CMIP5/patterns/
and copy needed patterns folder here
```

So the tree was deliberately populated by copying CMIP5 pattern sub-trees from `/pd/data/lpj/input_data/IMOGEN_patterns/CMIP5/patterns/`; the 34 `CEN_*_MOD_*` directories are **CMIP5**. The `ukmo_hadcm3_rel` dir is the legacy **CMIP3 / HadCM3 relative-to-baseline** pattern kept for historical compatibility. The `CMIP6_IMOGEN_EBM_values_and_patterns` dir is a **CMIP6 NetCDF** deliverable (5 GCMs). Size-wise, every CMIP5 dir is 2.4 MB of ASCII, `ukmo_hadcm3_rel` is 2.0 MB, and the CMIP6 dir is 20 MB (≈4.0 MB per NetCDF).

### 1.2 Naming convention

`CEN_<institute>_MOD_<model>` — `CEN`/`MOD` are literal tokens separating CMIP5 **CENtre (institute_id)** and **MODel (model_id)** from the official CMIP5 DRS vocabulary. Examples:

| Dir basename | Institute (CEN) | GCM (MOD) | Country / notes |
|---|---|---|---|
| `CEN_BCC_MOD_bcc-csm1-1` | BCC (Beijing Climate Center) | bcc-csm1-1 | China |
| `CEN_BCC_MOD_bcc-csm1-1-m` | BCC | bcc-csm1-1-m | China (medium-res sibling) |
| `CEN_BNU_MOD_BNU-ESM` | BNU (Beijing Normal University) | BNU-ESM | China |
| `CEN_CCCma_MOD_CanESM2` | CCCma | CanESM2 | Canada |
| `CEN_CMCC_MOD_CMCC-CMS` | CMCC | CMCC-CMS | Italy |
| `CEN_CNRM-CERFACS_MOD_CNRM-CM5` | CNRM / CERFACS | CNRM-CM5 | France |
| `CEN_CSIRO-BOM_MOD_ACCESS1-0` | CSIRO-BOM | ACCESS1-0 | Australia |
| `CEN_CSIRO-BOM_MOD_ACCESS1-3` | CSIRO-BOM | ACCESS1-3 | Australia |
| `CEN_CSIRO-QCCCE_MOD_CSIRO-Mk3-6-0` | CSIRO-QCCCE | CSIRO-Mk3-6-0 | Australia |
| `CEN_INM_MOD_inmcm4` | INM | inmcm4 | Russia |
| `CEN_IPSL_MOD_IPSL-CM5A-LR` | IPSL | IPSL-CM5A-LR | France (low-res) |
| `CEN_IPSL_MOD_IPSL-CM5A-MR` | IPSL | IPSL-CM5A-MR | France (mid-res) |
| `CEN_IPSL_MOD_IPSL-CM5B-LR` | IPSL | IPSL-CM5B-LR | France |
| `CEN_MIROC_MOD_MIROC-ESM` | MIROC | MIROC-ESM | Japan (Earth-system) |
| `CEN_MIROC_MOD_MIROC-ESM-CHEM` | MIROC | MIROC-ESM-CHEM | Japan (+ atmos chem) |
| `CEN_MIROC_MOD_MIROC5` | MIROC | MIROC5 | Japan |
| `CEN_MOHC_MOD_HadGEM2-CC` | MOHC (Met Office Hadley) | HadGEM2-CC | UK (carbon-cycle version) |
| `CEN_MOHC_MOD_HadGEM2-ES` | MOHC | HadGEM2-ES | UK (Earth-system) |
| `CEN_MPI-M_MOD_MPI-ESM-LR` | MPI-M | MPI-ESM-LR | Germany (low-res) |
| `CEN_MPI-M_MOD_MPI-ESM-MR` | MPI-M | MPI-ESM-MR | Germany (mid-res) |
| `CEN_MRI_MOD_MRI-CGCM3` | MRI | MRI-CGCM3 | Japan |
| `CEN_NASA-GISS_MOD_GISS-E2-H` | NASA-GISS | GISS-E2-H | USA (HYCOM ocean) |
| `CEN_NASA-GISS_MOD_GISS-E2-H-CC` | NASA-GISS | GISS-E2-H-CC | USA (+ carbon-cycle) |
| `CEN_NASA-GISS_MOD_GISS-E2-R` | NASA-GISS | GISS-E2-R | USA (Russell ocean) |
| `CEN_NASA-GISS_MOD_GISS-E2-R-CC` | NASA-GISS | GISS-E2-R-CC | USA (+ CC) |
| `CEN_NCAR_MOD_CCSM4` | NCAR | CCSM4 | USA |
| `CEN_NCC_MOD_NorESM1-M` | NCC (Norwegian Climate Centre) | NorESM1-M | Norway |
| `CEN_NCC_MOD_NorESM1-ME` | NCC | NorESM1-ME | Norway (+ BGC) |
| `CEN_NOAA-GFDL_MOD_GFDL-CM3` | NOAA-GFDL | GFDL-CM3 | USA |
| `CEN_NOAA-GFDL_MOD_GFDL-ESM2G` | NOAA-GFDL | GFDL-ESM2G | USA (isopycnal ocean) |
| `CEN_NOAA-GFDL_MOD_GFDL-ESM2M` | NOAA-GFDL | GFDL-ESM2M | USA (MOM ocean) |
| `CEN_NSF-DOE-NCAR_MOD_CESM1-BGC` | NSF-DOE-NCAR | CESM1-BGC | USA |
| `CEN_NSF-DOE-NCAR_MOD_CESM1-CAM5` | NSF-DOE-NCAR | CESM1-CAM5 | USA |
| `CEN_NSF-DOE-NCAR_MOD_CESM1-WACCM` | NSF-DOE-NCAR | CESM1-WACCM | USA (whole-atmos chem) |
| `ukmo_hadcm3_rel` | UKMO (Met Office) | HadCM3 (relative) | **CMIP3 legacy** format; original Zelazowski/Huntingford IMOGEN pattern |
| `CMIP6_IMOGEN_EBM_values_and_patterns` | multi-institute | GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL | **CMIP6**, NetCDF + JSON format — **not currently consumed by the Fortran IMOGEN** |

Totals: **34 CMIP5 CEN_*_MOD_* dirs** (2.4 MB each, all ASCII) + **1 CMIP3 legacy** (`ukmo_hadcm3_rel`, 2.0 MB ASCII) + **1 CMIP6** (5 GCMs, 20 MB NetCDF+JSON) = 36 directories.

### 1.3 Are they all the same format?

**No.** Two distinct file formats coexist:

1. **ASCII** (all 35 CEN_*_MOD_* dirs **and** `ukmo_hadcm3_rel`): 12 plain-text files named after month abbreviations (`jan`, `feb`, `mar`, `apr`, `may`, `jun`, `jul`, `aug`, `sep`, `oct`, `nov`, `dec`). No file extensions. `file(1)` reports each as `ASCII text`. Sizes within a given directory are ≈ equal (≈ 200 KB for CEN_* dirs, ≈ 170 KB for `ukmo_hadcm3_rel`). Detected by `file`:
   `.../CEN_IPSL_MOD_IPSL-CM5A-MR/jan: ASCII text`
   `.../ukmo_hadcm3_rel/jan: ASCII text`

2. **NetCDF-4 / HDF5 + JSON** (only in `CMIP6_IMOGEN_EBM_values_and_patterns/`): five `<model>_patterns.nc` files (4.0 MB each) and five matching `<model>_params.json` files (< 1 KB each). Detected by `file`:
   `.../ipsl-cm6a-lr_patterns.nc: Hierarchical Data Format (version 5) data`
   `.../ipsl-cm6a-lr_params.json: JSON text data`

### 1.4 Representative dir A — `CEN_IPSL_MOD_IPSL-CM5A-MR/` (CMIP5 ASCII)

```
CEN_IPSL_MOD_IPSL-CM5A-MR/
├── jan   200 647 B, 1 632 lines   (1 header + 1 631 cells)
├── feb   200 647 B, 1 632 lines
├── mar   200 647 B, 1 632 lines
├── apr   200 647 B, 1 632 lines
├── may   200 647 B, 1 632 lines
├── jun   200 647 B, 1 632 lines
├── jul   200 647 B, 1 632 lines
├── aug   200 647 B, 1 632 lines
├── sep   200 647 B, 1 632 lines
├── oct   200 647 B, 1 632 lines
├── nov   200 647 B, 1 632 lines
└── dec   200 647 B, 1 632 lines
```

All 12 files have identical size and line count. The 1 631 data rows correspond to the IMOGEN native land-only grid at **3.75° lon × 2.5° lat** (the UKMO-HadCM3 grid, as Zelazowski et al. 2018 §2.1 specifies: *"we harmonised all types of WCRP CMIP3 grids into one, which is chosen to be the UKMO-HadCM3, although land points for Antarctica are excluded"*). A gridlist containing exactly these 1 631 points exists at `FRAMEWORK/Data/Gridlist/patterns_gridlist.txt` and `FRAMEWORK/Common-directory/IMOGEN-codebase/code/patterns_gridlist.txt`; both start with `281.25 82.50 / 285.00 82.50 / 288.75 82.50` and contain 1 631 lines.

### 1.5 Representative dir B — `CMIP6_IMOGEN_EBM_values_and_patterns/` (CMIP6 NetCDF)

```
CMIP6_IMOGEN_EBM_values_and_patterns/
├── gfdl-esm4_params.json     (245 B)     gfdl-esm4_patterns.nc     (4.0 MB)
├── ipsl-cm6a-lr_params.json  (245 B)     ipsl-cm6a-lr_patterns.nc  (4.0 MB)
├── mpi-esm1-2-hr_params.json (245 B)     mpi-esm1-2-hr_patterns.nc (4.0 MB)
├── mri-esm2-0_params.json    (245 B)     mri-esm2-0_patterns.nc    (4.0 MB)
└── ukesm1-0-ll_params.json   (245 B)     ukesm1-0-ll_patterns.nc   (4.0 MB)
```

Five GCMs: GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL. Each GCM has a pair `{name}_patterns.nc` (spatial monthly-climate patterns) + `{name}_params.json` (scalar EBM parameters). Details in §3.

---

## 2. Pattern file format — CMIP5 ASCII month files

Annotated `head -5` of `FRAMEWORK/Common-directory/IMOGEN-codebase/patterns/CEN_IPSL_MOD_IPSL-CM5A-MR/jan` (200 647 B, 1 632 lines):

```
    0.00  -60.00  360.00   90.00                         <- line 1: bbox header (lon_min lat_min lon_max lat_max)
281.25  82.50   1.4383  -0.2364  -0.0103   0.0000   5.0209   0.0000    0.00000    0.00793    0.00000    0.32460     0.0000
285.00  82.50   1.3262  -0.1372  -0.0145   0.0000   4.9234   0.0000    0.00000    0.01427    0.00000    0.44109     0.0000
288.75  82.50   1.3686  -0.0710   0.0427   0.0000   5.2753   0.0000    0.00000    0.05239    0.00000    0.21975     0.0000
292.50  82.50   1.4449  -0.0590   0.0660   0.0000   5.4313   0.0000    0.00000    0.05029    0.00000    0.06895     0.0000
```

Layout (whitespace-separated, no commas, fixed-width):

| Column | Width | Meaning |
|---|---|---|
| 1 | ~7 chars | longitude in **0–360 degrees east** (e.g., `281.25` = 78.75°W) |
| 2 | ~7 chars | latitude in **degrees north**, range −60 to +90 (Antarctica excluded, per Zelazowski et al. 2018) |
| 3–14 | ~10 chars each | **12 monthly pattern coefficients**, one per climate variable (the file is itself for one month, so each row holds the pattern values of all 12 forcing variables at that cell for that month) |

Confirmed by tail (last 3 rows): cells continue down through southern mid-latitudes (`288.75 -50.00 ... 292.50 -55.00`) to the Antarctic-exclusion limit at −60° lat consistent with the bbox header.

Row count = 1 + 1 631 = 1 632, matching the IMOGEN HadCM3 land gridlist `Data/Gridlist/patterns_gridlist.txt`.

The 12 data columns per row map (per IMOGEN convention) to 12 forcing/state variables, e.g. T_l (linear), T_l (quadratic / range), q_l, precip, wind, p_star, SW_down, LW_down, …. The exact column→variable map is set inside the Fortran IMOGEN reader (out of scope for this subagent — Subagent 3/4). The four variables visible at column 4 (`0.0000`) and columns 9, 11, 14 (`0.00000`/`0.0000`) being identically zero across all rows in the sample suggests several columns are reserved/unused or carry quadratic terms that are not populated for IPSL-CM5A-MR.

**Per-variable encoding inferred:** `column = a₀ + a₁·ΔT + a₂·ΔT²` style coefficients are not stored explicitly here — each file is *one month* and each column is *one variable's pattern coefficient*. Annual files are reconstructed by reading the 12 month files (`jan`…`dec`) in sequence.

---

## 3. CMIP6 NetCDF patterns

`ncdump -h FRAMEWORK/Common-directory/IMOGEN-codebase/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/ipsl-cm6a-lr_patterns.nc`:

```
netcdf ipsl-cm6a-lr_patterns {
dimensions:
    imogen_drive = 12 ;
    lat = 56 ;
    lon = 96 ;
    bnds = 2 ;
variables:
    double tl1_patt(imogen_drive, lat, lon) ;          tl1_patt:units = "1" ;
    int64  imogen_drive(imogen_drive) ;
    double lat(lat) ;          lat:axis = "Y" ; lat:bounds = "lat_bnds" ; lat:units = "degrees_north" ;
    double lat_bnds(lat, bnds) ;
    double lon(lon) ;          lon:axis = "X" ; lon:bounds = "lon_bnds" ; lon:units = "degrees_east" ;
    double lon_bnds(lon, bnds) ;
    double ql1_patt(imogen_drive, lat, lon) ;          ql1_patt:units      = "K-1" ;
    double precip_patt(imogen_drive, lat, lon) ;       precip_patt:units   = "m-2.kg.s-1.K-1" ;
    double wind_patt(imogen_drive, lat, lon) ;         wind_patt:units     = "m.s-1.K-1" ;
    double pstar_patt(imogen_drive, lat, lon) ;        pstar_patt:units    = "m-1.kg.s-2.K-1" ;
    double swdown_patt(imogen_drive, lat, lon) ;       swdown_patt:units   = "W m-2 K-1" ;
    double lwdown_patt(imogen_drive, lat, lon) ;       lwdown_patt:units   = "W m-2 K-1" ;
    double range_tl1_patt(imogen_drive, lat, lon) ;    range_tl1_patt:units = "1" ;
// global attributes:
    :Conventions = "CF-1.7" ;
}
```

**Salient properties:**

- **CF-1.7 compliant**, NetCDF-4/HDF5 underneath.
- **Grid:** regular `lat × lon = 56 × 96` ⇒ ~3.21° lat × 3.75° lon. NOT the IMOGEN HadCM3 land-only gridlist; this is a full lat×lon grid (5 376 cells incl. ocean) and **must be regridded** to the IMOGEN gridlist before consumption.
- **Time dimension:** `imogen_drive = 12`, integer index. Almost certainly month-of-year (Jan..Dec) — same cardinality as the 12 ASCII month files. No CF `time` units attribute, so this needs in-code documentation.
- **Pattern variables (8):**
  - `tl1_patt` (linear surface-temperature pattern, dimensionless)
  - `ql1_patt` (humidity, K⁻¹)
  - `precip_patt` (precipitation, kg m⁻² s⁻¹ K⁻¹)
  - `wind_patt` (wind speed, m s⁻¹ K⁻¹)
  - `pstar_patt` (surface pressure, kg m⁻¹ s⁻² K⁻¹ = Pa K⁻¹)
  - `swdown_patt` (shortwave down, W m⁻² K⁻¹)
  - `lwdown_patt` (longwave down, W m⁻² K⁻¹)
  - `range_tl1_patt` (diurnal range, dimensionless)

  All `_patt` variables are *per-Kelvin* sensitivities of the field to global-mean surface-temperature anomaly — i.e., classic Huntingford-Cox pattern-scaling coefficients. The CMIP5 ASCII files almost certainly encode the same 8 quantities but distributed across 12 columns (with 4 zero/reserved columns observed in the IPSL-CM5A-MR sample).

`cat ipsl-cm6a-lr_params.json` (single JSON object, 245 B):

```json
{"IPSL-CM6A-LR": {"model": "IPSL-CM6A-LR", "kappa_o": 320.0, "lambda_l": 1.2819275644225012, "lambda_o": 1.1299504358188983, "mu": 1.5467156266260915, "f_ocean": 0.712714582468359}}
```

**Scalar EBM (Energy Balance Model) parameters** that IMOGEN uses to drive global-mean ΔT from ΔCO₂ before applying the spatial patterns:

| Key | Meaning (IMOGEN convention) |
|---|---|
| `model` | GCM identifier |
| `kappa_o` | ocean vertical heat-diffusivity (W m⁻¹ K⁻¹ or similar) |
| `lambda_l` | land climate-feedback parameter (W m⁻² K⁻¹) |
| `lambda_o` | ocean climate-feedback parameter (W m⁻² K⁻¹) |
| `mu` | land-ocean warming contrast factor (dimensionless) |
| `f_ocean` | global ocean fraction |

These five parameters fully specify the IMOGEN EBM for that GCM. In the CMIP3/CMIP5 ASCII regime, equivalent values live inside hard-wired Fortran data statements / namelists (other-subagent territory), so the JSON is a clean, auditable replacement.

---

## 4. FastRegrid

`find FRAMEWORK/FastRegrid -maxdepth 4 -type f`:

```
FastRegrid/FastRegrid/CMakeLists.txt
FastRegrid/FastRegrid/Regrid.h          (105 lines — public API in namespace `regrid`)
FastRegrid/FastRegrid/Regrid.cpp        (356 lines — Regridder class implementation)
FastRegrid/FastRegrid/FastRegrid.cpp    (79 lines  — example/driver `main()`)
FastRegrid/FastRegrid/x64/Release/{FastRegrid.exe.recipe, .iobj, .ipdb}   <- Visual Studio MSBuild leftovers
```

**Purpose.** A re-engineered, library-shaped regridder written *after* `Regrid/Regrid.cpp`. Goals (visible in the API):
- separate **library** (`fastregrid` shared object) from **example** driver
- support both **YEAR_BY_YEAR** (IMOGEN) and **GRID_BY_TIME** (LPJ-GUESS) input layouts via a `DataLayout` enum
- **Haversine** distance metric (with EARTH_RADIUS_KM = 6371.0 km — see `Regrid.cpp:14`) as well as Euclidean
- **precompute** target↔source mappings once, reuse across all years/files
- structured, typed config via `regrid::RegridConfig`

**Build.** `CMakeLists.txt` (CMake ≥ 3.10, C++17):

```
add_library(fastregrid SHARED regrid.cpp)
add_executable(fastregrid_example fastregrid.cpp)
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    target_link_libraries(fastregrid PRIVATE OpenMP::OpenMP_CXX)
    target_link_libraries(fastregrid_example PRIVATE OpenMP::OpenMP_CXX)
endif()
install(TARGETS fastregrid DESTINATION lib)
install(FILES regrid.h DESTINATION include/fastregrid)
```

**I/O (driver `FastRegrid.cpp:main`).**
- *Inputs:* a target gridlist file (lon lat per line) and either (YEAR_BY_YEAR) a directory tree `<base>/<year>/{T_anom.dat,SW_anom.dat,P_anom.dat,…}` produced by IMOGEN, or (GRID_BY_TIME) a single LPJ-GUESS `.out` file with header + `lon lat year v1 v2 …` rows.
- *Outputs:* same layout under `<base>/REGRIDDED/…`, plus an optional `closest_mappings.txt` audit file.
- Defaults the driver actually runs with: `INVERSE_DISTANCE_WEIGHTED`, Haversine, `radius=100 km`, `power=2.0`, `max_points=5`, `precision=5`, `verbose=true`, `data_layout=GRID_BY_TIME`, target grid `gridlist_hurtt_RNDM_midpoint.txt`, processes `anpp.out` for years 1901–2100.

---

## 5. Regrid

`Regrid/` layout:

```
Regrid/Regrid.cpp        308 lines — single-file program
Regrid/Regrid/x64/Debug  Visual Studio build output dir (binaries — not read)
Regrid/x64/              MSBuild output root (binaries — not read)
```

No CMakeLists, no Makefile — this is a **Visual Studio 2019/2022 project** intended to be built on Windows only (the surviving `.exe.recipe` files in `x64/Release` confirm an MSBuild origin).

**Purpose.** Earliest of the three regridders. Single-file `main()` that walks IMOGEN's per-year output directories (`output-pure-iiasa-585/<year>/`) and regrids the five anomaly files (`T_anom.dat`, `SW_anom.dat`, `P_anom.dat`, `DTEMP_anom.dat`, `WET.dat`) from the IMOGEN HadCM3 grid (1 631 land cells) onto a finer target gridlist (`gridlist_hurtt_RNDM_midpoint_3698.txt` — note the `_3698` suffix, a different cell count from `gridlist_hurtt_RNDM_midpoint.txt` used by FastRegrid/RegridLPJG); four other per-year files (`CO2.dat`, `done`, `dtemp_o.dat`, `fa_ocean.dat`) are byte-copied unchanged.

**Algorithms.**
- `findClosestDataPoint` (NEAREST_NEIGHBOR): plain Euclidean in lon/lat space (degrees) with a 0–360 → −180–180 fix-up on source longitude (`Regrid.cpp:86`). **Latitude of the result is overwritten with the target latitude** but **longitude is not** (`Regrid.cpp:91-95`) — small asymmetric bug, see §7.
- `inverseDistanceWeightedInterpolation`: same Euclidean distance, fixed `radius` (default 5.0°) and `power` (default 2.0), early-return on distance < 1e-6, falls back to NN if no source points within radius.
- `regridDataUsingMapping` + `computeMapping`: caches NN target→source index map computed from the first year's input file and reuses for every subsequent year — clear precursor to FastRegrid's `precompute_mappings`.

**I/O.**
- Reads gridlist as `lon lat` per line, no header (`readGridList`).
- Reads climate-data files as `lon lat v1 v2 v3 …` per line, no header (`readClimateData`).
- Writes back in the same shape, fixed `setw(8)`, `setprecision(3)`.
- Hardcoded paths (Windows): see §7.

---

## 6. RegridLPJG

`find FRAMEWORK/RegridLPJG -maxdepth 4 -type f`:

```
RegridLPJG/RegridLPJG/RegridLPJG.cpp     435 lines — single-file program
RegridLPJG/RegridLPJG/closest_points.txt 355 148 lines — *committed output artefact* of a previous run
RegridLPJG/RegridLPJG/x64/Release/{.exe.recipe, .iobj, .ipdb}    Visual Studio MSBuild leftovers
```

No CMakeLists, no Makefile — Visual Studio project, Windows-only build path.

**Purpose.** Regrid LPJ-GUESS GRID_BY_TIME `.out` files (header line + `lon lat year v1 v2 …` rows for 1901–2100) from LPJ-GUESS's native gridlist onto IMOGEN-side gridlist `gridlist_hurtt_RNDM_midpoint.txt`. The user's hypothesis (NN or IDW interpolation onto a larger gridlist) is **half right**: it implements **only IDW** (with hardcoded `power = 2`, `radius = 1500.0` km used purely as a notification threshold; *all* sources within radius would be used, except the code instead always uses the **5 nearest points** regardless of radius — see `precompute_closest_points` line 104: `std::min(size_t(5), distances.size())`).

Distance metric is Haversine (km), same `EARTH_RADIUS_KM = 6371.0` constant as FastRegrid.

**Pipeline (`main`):**
1. `extract_source_gridlist(first_file, …)` — reads the first vegetation `.out` file, skips the header row, then builds the unique `(lon, lat)` set as the source grid.
2. `read_target_grid("gridlist_hurtt_RNDM_midpoint.txt")` — reads target.
3. `precompute_closest_points` — for each target cell, finds the 5 nearest source cells (Haversine), writes a 5-row block per target into `closest_points.txt` (the very file already committed in the repo, suggesting at some point it was actually executed and the output was checked in).
4. For each vegetation file (currently the array is reduced to `{ "agpp.out" }`; a fuller list with `cflux.out, cpool.out, lai.out, mch4.out, nflux.out, npool.out, nmass.out, …` is **commented out** — see lines 375–383):
   - Read all rows.
   - For each (target cell × year) compute IDW from the 5 cached neighbour indices.
   - Write `<target_lon> <target_lat> <year> <values…>` with `setw(12) setprecision(5)`.

**I/O paths** are hardcoded Windows-style (see §7).

---

## 7. Bugs / dead code / hardcoded paths spotted

### Hardcoded paths (all three utilities)

- `Regrid/Regrid.cpp:234` — `basePath = "C:\\GitHub\\dbampoh\\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\\Common-directory\\IMOGEN\\output-pure-iiasa-585\\"` (Windows backslashes; user-specific `dbampoh` GitHub root).
- `Regrid/Regrid.cpp:252` — `gridListFilename = "C:\\GitHub\\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\\Data\\Gridlist\\gridlist_hurtt_RNDM_midpoint_3698.txt"` (note: `_3698` suffix, distinct from FastRegrid/RegridLPJG variant).
- `FastRegrid/FastRegrid/FastRegrid.cpp:57,60,64,65,67,71,72` — six hardcoded `C:/GitHub/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/...` paths for mappings file, gridlist, IMOGEN base, LPJG `.out` input/output.
- `RegridLPJG/RegridLPJG/RegridLPJG.cpp:359,388` — `C:/GitHub/...` for input folder and target gridlist; line 386 even has `// FIX ME` next to the first-file derivation.

None of the three programs currently take CLI arguments, env vars, or a config file — they must be edited and recompiled to retarget data.

### Build-system gaps

- `FastRegrid` has a CMakeLists, but **`Regrid/` and `RegridLPJG/` do not**. They ship only Visual Studio `.exe.recipe`/`.iobj`/`.ipdb` artefacts under `x64/`. There is no Linux/cluster build path for them as-committed.
- `FastRegrid/FastRegrid/CMakeLists.txt:8,12` references **lowercase** `regrid.cpp` and `fastregrid.cpp`, but the on-disk files are PascalCase `Regrid.cpp` and `FastRegrid.cpp`. On Windows (case-insensitive NTFS) this builds; on a case-sensitive Linux ext4, CMake will fail to find the sources. **Linux build bug.**
- `FastRegrid/FastRegrid/CMakeLists.txt:16-20` finds and links `OpenMP::OpenMP_CXX`, but `FastRegrid/Regrid.cpp` contains **no `#pragma omp` directives anywhere** (`grep -n "pragma omp" Regrid.cpp` returns nothing). The OpenMP link is dead — no parallelization is actually happening despite the "Fast" name and the link flag.

### Algorithmic / correctness issues

- `Regrid/Regrid.cpp:86–95` `findClosestDataPoint`: latitude of the closest source is overwritten with the target latitude (`closestData.latitude = target.latitude`) but longitude is left as the *adjusted source* longitude. Output coordinates therefore won't match the requested target gridlist exactly. The companion `regridDataUsingMapping` (lines 222–229) does the symmetric thing for both lon and lat — internal inconsistency.
- `RegridLPJG/RegridLPJG.cpp:210–211` writes `regridded.lat = target.first; regridded.lon = target.second;`, but `target` was filled at line 252 via `target_points.emplace_back(lon, lat)` — i.e. `target.first == lon` and `target.second == lat`. So `regridded.lat` is actually a longitude and `regridded.lon` is a latitude. The bug **happens to cancel** at output (the write at lines 216–217 does `regridded.lon` then `regridded.lat`, both swapped, so the columns end up `lon lat` again), but any future code that reads `regridded.lat` field-wise will be wrong. Smelly.
- `RegridLPJG/RegridLPJG.cpp:200–207` filters source data per `(target × year)` inside a triple loop ⇒ O(targets · years · sources · vars) work; the per-year filter could trivially be lifted out of the target loop (group-by year once), making it O((targets+years) · sources). On 200 years × ~3 700 targets × ~67 000 source rows this is the main reason it is slow.
- `RegridLPJG/RegridLPJG.cpp:104` always picks the **5 nearest neighbours** ignoring the `radius` argument (`radius` is then only consulted in a now-commented-out warning at lines 119–124). The function signature still advertises `radius` as significant — misleading dead parameter.

### Dead / commented code

- `RegridLPJG/RegridLPJG.cpp:375–380`: the full 14-variable file list is commented out, leaving only `agpp.out` to be processed. Anyone wanting to regrid all LPJG outputs must uncomment.
- `RegridLPJG/RegridLPJG.cpp:119–124`: radius-exceedance warning fully commented.
- `RegridLPJG/RegridLPJG.cpp:342–346`: per-line debug print + `system("pause")` (Windows-only) commented out — a strong signal the code has only ever been run interactively on Windows.
- `RegridLPJG/RegridLPJG/closest_points.txt` (355 148 lines, ~17 MB) is a **committed run-output artefact** — should be in `.gitignore`, not the repo.
- `Regrid/Regrid/x64/Debug/`, `Regrid/x64/`, `FastRegrid/FastRegrid/x64/Release/`, `RegridLPJG/RegridLPJG/x64/Release/` — all MSBuild build artefacts committed to git.

### Spec drift between utilities

- Three different gridlists are referenced across the three tools with no shared config: `gridlist_hurtt_RNDM_midpoint_3698.txt` (Regrid) vs `gridlist_hurtt_RNDM_midpoint.txt` (FastRegrid + RegridLPJG). The relationship between `_3698` and the unsuffixed file is undocumented.
- `Regrid` IDW uses `radius=5.0` in **degrees** (Euclidean lon/lat); `FastRegrid` IDW uses `radius=100.0` km (Haversine); `RegridLPJG` uses `radius=1500.0` km (notional). Not directly comparable.

---

## 8. Roadmap to CMIP6 NetCDF (data side only)

What the patterns side already provides versus what the consumers (Fortran IMOGEN) currently expect:

| Aspect | CMIP5 (currently consumed) | CMIP6 (already on disk, unused) | Gap to close |
|---|---|---|---|
| Container | 12 ASCII month files per GCM | 1 NetCDF-4 / HDF5 file per GCM (CF-1.7) | Add NetCDF reader on the consumer side (lib already linked by LPJ-GUESS, so available in the build) |
| Grid | IMOGEN HadCM3 land-only, 1 631 cells, 3.75°×2.5° | Regular `lat × lon = 56 × 96` (~3.21°×3.75°), 5 376 cells (incl. ocean) | **Regrid CMIP6 → IMOGEN gridlist** before consumption; either (a) batch-regrid offline using `Regrid` (extended to read NetCDF) producing month-files in CMIP5 ASCII format — minimum-change path; or (b) fold a NetCDF-aware regridder into the Fortran reader |
| Time/month axis | filename (`jan`..`dec`) | `imogen_drive(12)` int64 dim, no CF time units | Document Jan..Dec ordering convention (likely 1..12); add a small lookup |
| Variables | 12 columns per row, ordering set in Fortran | 8 named CF vars (`tl1_patt`, `ql1_patt`, `precip_patt`, `wind_patt`, `pstar_patt`, `swdown_patt`, `lwdown_patt`, `range_tl1_patt`) | Establish authoritative column→var map for CMIP5 ASCII; then write a thin shim that produces CMIP5-shaped ASCII from the 8 NetCDF vars (some columns will be zeros — matches existing CMIP5 pattern of reserved zero columns) |
| Units | implicit | explicit on every var (`K-1`, `m-2.kg.s-1.K-1`, `W m-2 K-1`, …) | Verify units match what Fortran assumes; convert if needed |
| EBM scalars | hardwired in Fortran data statements (per-GCM) | per-GCM JSON: `kappa_o, lambda_l, lambda_o, mu, f_ocean` | Generate a Fortran namelist from the JSON (trivial) or parse JSON in Fortran (less trivial) |
| GCMs | 34 CMIP5 + 1 CMIP3 legacy | only 5 CMIP6 so far (GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL) | Smaller ensemble — fine for testing, but the science user will likely want more (CMIP6 patterns generation pipeline is upstream / out of scope) |

**Minimum-disruption migration path (data side):**

1. Write a small Python/MATLAB script that, for each `<gcm>_patterns.nc`:
   - reads each of the 8 `_patt` variables on the 56×96 grid,
   - bilinearly or nearest-neighbour samples them onto the 1 631-cell IMOGEN HadCM3 land gridlist,
   - composes 12 ASCII month files (`jan`…`dec`) in exactly the CMIP5 layout documented in §2 (header `lon_min lat_min lon_max lat_max`, then `lon lat v1 v2 … v12` per cell), padding the four currently-zero columns with zeros so the column count matches what Fortran expects,
   - drops them into a new directory `CEN_CMIP6_MOD_<gcm>/` parallel to the existing CMIP5 dirs,
   - converts the JSON params into the per-GCM Fortran data block (or a namelist).
2. The Fortran IMOGEN then needs **zero changes** — it just sees 5 more "CMIP5-style" GCMs.

**More invasive but cleaner path:** add NetCDF + JSON readers to IMOGEN, drop the CMIP5 ASCII format, and use `Regrid`/`FastRegrid` (extended with NetCDF input support) to handle resolution conversion at runtime. Better long-term but requires Fortran work covered by Subagents 3/4.

---

## 9. Open questions

1. **CMIP5-ASCII column ordering.** What is the authoritative mapping from the 12 columns of each `CEN_*_MOD_*/<month>` file to the 8 (+ reserved) IMOGEN forcing variables? It must exist inside the Fortran IMOGEN reader (Subagent 3/4) — needed to validate the CMIP6→CMIP5-format converter in §8.
2. **`imogen_drive` semantics.** The CMIP6 NetCDF dimension is `imogen_drive=12` with no `units` or `calendar` attributes. Is the order strictly Jan..Dec? Is `int64` index 0-based or 1-based? Needs confirmation against the upstream pattern-generation code.
3. **`ukmo_hadcm3_rel`.** Is this the same 1 631-cell HadCM3 land grid as the CEN_* dirs (size suggests yes: 2.0 MB vs 2.4 MB)? If yes it could be retired once CMIP5/CMIP6 are validated.
4. **Two IMOGEN target gridlists.** Why `gridlist_hurtt_RNDM_midpoint_3698.txt` (used by `Regrid`) vs `gridlist_hurtt_RNDM_midpoint.txt` (used by `FastRegrid`/`RegridLPJG`)? Is the unsuffixed one a strict subset/superset, or a different RNG seed of the Hurtt midpoint sampling?
5. **Has any of {Regrid, FastRegrid, RegridLPJG} ever been built on Linux/the cluster?** Only FastRegrid has a CMakeLists, and it has the case-sensitivity bug (§7). The committed `closest_points.txt` proves RegridLPJG was at least executed once on Windows — but cluster runs would need fresh build infrastructure.
6. **CMIP6 patterns provenance.** Where does `CMIP6_IMOGEN_EBM_values_and_patterns/` come from — internal generation script or external collaborator deliverable? Are more GCMs expected? The pipeline that produces `<gcm>_patterns.nc` + `<gcm>_params.json` is not visible in this tree.
7. **Zero columns in CMIP5 ASCII.** Are columns 6, 11, and 13 (1-indexed) of `CEN_IPSL_MOD_IPSL-CM5A-MR/jan` legitimately always zero (reserved / quadratic-term placeholders), or just zero for IPSL-CM5A-MR? Sampling more GCMs would answer this but is outside the budget here.

