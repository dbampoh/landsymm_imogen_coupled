# Block 8.2.5 — Phases B + C complete

**Date**: 2026-05-26 ~16:00 CEST (session 11 day 2)
**Status**: ✅ Phase B + Phase C COMPLETE; ready for Phase D (Fortran engine 5-SSP runs)

## Phase B — Fortran engine settings alignment per-SSP ✅

| Action | Result |
|---|---|
| Created `runs/<SSP>/Common-directory-fortranengine/` dirs × 5 | ✅ |
| Authored `runs/SSP1-2.6/Common-directory-fortranengine/imogen_settings.txt` canonical (~9050 bytes; ~75 LOC config) | ✅ |
| Per-SSP sed-replicated to SSPs 2-5 (only diff: per-SSP path tags + ssp{245,370,460,585} non-CO2 RF variant) | ✅ |
| Path-relativity verified from `runs/SSP1-2.6/Common-directory-fortranengine/` (depth 3 from project root) | ✅ all 5 critical paths resolve |

**Key δ-B activation params** (changed from legacy template):
- `REGRID .TRUE.` (was `.FALSE.`) — THE δ-B pipeline activator; engine internally NN-regrids 1631-grid patterns → 3698-grid output via SUBROUTINE REGRID_CLIM
- `LPJG_CFLUX .TRUE.` (was `.FALSE.`) — use intermediary_py LPJG natural fluxes (RCMIP-backed; matches C++ engine config)
- `CO2_INIT_PPMV 296.1` (was `286.085`) — B39 Law Dome 1900
- `CH4_INIT_PPBV 875.6` (was `865.0`) — B39 Law Dome 1900
- `NYR_EMISS 201` (was `251`) — 1900-2100 = 201 yrs (matches intermediary_py adapter coverage)
- `DIR_PATT ../../../imogen/patterns/CEN_CMIP6_MOD_MRI-ESM2-0/` (was `CEN_IPSL_MOD_IPSL-CM5A-MR/`) — CMIP6 MRI-ESM2-0 matching C++ engine + per user direction
- `FILE_SCEN_EMITS` etc. → `runs/<SSP>/inputs/<adapter-output>` (intermediary_py; was legacy IIASA DKB_dataset_totals)
- `FILE_NON_CO2_VALS` → `imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp<TAG>.txt` (CMIP6 + per-SSP)

## Phase C — tools/FastRegrid/ clone + Linux adaptation + 10-var extension + CLI args + build ✅

| Action | Result |
|---|---|
| `cp -r ../version_B/.../FastRegrid/FastRegrid/* tools/FastRegrid/` | ✅ md5 byte-identical to source |
| Renamed files to lowercase (Linux case-sensitivity fix vs Windows-tolerant version_B) | `Regrid.h` → `regrid.h`; `Regrid.cpp` → `regrid.cpp`; `FastRegrid.cpp` → `fastregrid.cpp` |
| `tools/FastRegrid/CMakeLists.txt` keyword-signature fix (`PRIVATE fastregrid` link spec; all target_link_libraries use keyword syntax) | ✅ |
| `tools/FastRegrid/fastregrid.cpp` CLI-arg parsing replacing version_B's hardcoded Windows paths | ~80 LOC added: `parse_args()` + `print_usage()`; flags: `--mode imogen\|lpjg --input --output --target-gridlist --method NN\|IDW --first-year --last-year [--max-points --radius --power --verbose]` |
| `tools/FastRegrid/fastregrid.cpp` `file_types` extended from 3 vars (T_anom, P_anom, SW_anom) to 9 per-cell climate variables (T_anom, P_anom, SW_anom, DTEMP_anom, Rh_anom, W_anom, Tmin_anom, Tmax_anom, WET); CO2.dat excluded per Rule #9 datapoint #23 below | ✅ |
| Build: `cd tools/FastRegrid && mkdir -p build && cd build && cmake .. && make -j$(nproc)` | ✅ PASS; binary 93,592 bytes; lib 306,656 bytes |
| `--help` smoke + 4-cell NN canary regrid on SSP1-2.6 year 1900 1631-grid source → 4-cell target | ✅ PASS; all 9 per-cell vars regridded successfully; 4 target cells (Canadian Arctic + Far North Canada + Russia + Argentina) present in output T_anom.dat with proper LON LAT + 12 monthly anomalies |

### Rule #9 datapoints surfaced at Phase C canary

- **#23**: `CO2.dat` (engine output) is NOT a per-cell climate field — it's a single-line atmospheric concentration time-series `YEAR CO2_PPMV ...` (format established at block 8.2.4 Phase G verification). The version_B FastRegrid regrid loop assumed all `file_types` items are per-cell fields. Crashed with vector-out-of-bounds at `std::vector<_Tp, _Alloc>::operator[]` when processing CO2.dat. **Fix**: removed CO2.dat from `file_types` (now 9 vars only); `scripts/run_fastregrid.sh` wrapper at Phase E will `cp` CO2.dat (+ dtemp_o.dat + fa_ocean.dat ocean-state files) as-is from source to post-regrid output dir.

### Minor non-blocking observation at Phase C canary

Output files include the source-grid's first row preserved at top (e.g., 281.25/82.50 row before the 4 target cells). May be a known version_B FastRegrid behavior (perhaps interpreted as a header bbox). LPJG should gracefully ignore the phantom cell at (281.25, 82.50) since it's not in the consumer gridlist. Will verify at Phase F 4-cell smoke acceptance.

## Build artifacts ready for Phase D

- `imogen/code/imogen_lpjg` (Fortran IMOGEN engine binary; 142,112 bytes; May 17 2026; md5 `854a9f55316bbba06dd75898966dafc7`) — UNCHANGED; already operational from session 9
- `tools/FastRegrid/build/fastregrid_example` (FastRegrid CLI binary; 93,592 bytes; sha1 to be captured at Phase H) — NEW; block 8.2.5 Phase C
- `tools/FastRegrid/build/libfastregrid.so` (FastRegrid shared library; 306,656 bytes) — NEW; block 8.2.5 Phase C
- `forks/trunk_r13078/build_b824/guess` (trunk's freshly-forward-ported C++ IMOGEN engine binary; 2,943,808 bytes; sha1 `9ef4c4cfcef0d10d51a12c2e261147000cee7d6c`) — UNCHANGED from block 8.2.4 Phase C; already operational

## Next phase

**Phase D — Fortran engine 5-SSP standalone runs** per the wiring plan §1.3:
- NEW `scripts/run_fortran_engine_only.sh` wrapper (~150 LOC; mirrors block 8.2.4 `scripts/run_trunk_engine_only.sh` pattern; FORTRAN_BIN env-overridable; bootstrap `imogen_lpjg.txt` + sidecar)
- Run for 5 SSPs (5-way parallel; ~17 min total wall expected per block 8.2.4 Phase E timing reference)
- Anticipate Rule #9 datapoints around Fortran-specific polling/handshake conventions (the C++ engine + Fortran engine might have slightly different polling-escape semantics)
- Phase D acceptance gates: ~10-13 climate variable files per year-dir (engine writes T_anom, P_anom, SW_anom, DTEMP_anom, Rh_anom, W_anom, Tmin_anom, Tmax_anom, WET, CO2 + ocean state dtemp_o + fa_ocean); 201 year-dirs (1900-2100; Fortran engine may not have the YEAR1==2100 overshoot of C++ engine); library size ~1 GB per SSP (3698-grid; ~2.27x more cells than 1631-grid C++ engine output's 443 MB)
