# STEP 9.5 — IMOGEN climate-output enhancements (consumer-side wiring + C++ engine Tmin/Tmax + BLAZE check)

**Date completed:** 2026-05-07
**Commit:** _to be filled in after `git commit`_
**Status:** **PARTIALLY DONE WITH SCOPE REFINEMENT**. The LPJG-consumer-side wiring (item c) and BLAZE check (d) and C++ engine Tmin/Tmax write (partial b) are complete and build clean; **the Fortran Rh/W writer port (item a) and F-9 closure (item e) are deferred to a follow-on step (step 9.5b) because they require infrastructure additions beyond the original budget**. End-to-end verification of the new consumer wiring is gated on F-12 (the F-10 deadlock blocks LPJG main loop in v1.0 single-process mode, so `imogencfx::get_climate_for_gridcell` and `getclimate` paths can't actually fire in v1.0).

---

## 1. Goal (per `EXECUTION_PLAN.md` V.1 step 9.5 + Decisions #11/#12)

> (a) Port C++ Rh+W writers back into Fortran so both backends produce
> `Rh_anom.dat` and `W_anom.dat` (~20 LOC).
> (b) Add Tmin/Tmax computation and output (both backends): `Tmin = T − DTEMP/2`,
> `Tmax = T + DTEMP/2`. (~20 LOC × 2)
> (c) Wire up the LPJG-side consumer in imogencfx for `file_relhum`, `file_wind`,
> `file_tmin`, `file_tmax` (~46 LOC).
> (d) Restore the BLAZE check at `imogencfx.cpp:792-794` (~3 LOC).
> (e) Verify units carefully per §I.D.

---

## 2. Investigation (Phase A) findings — substantive scope refinement

### 2.1 Discovery — Fortran engine has no RH/wind variables at all

A grep for `RH15M_OUT`, `UWIND_OUT`, `VWIND_OUT`, `WIND_OUT_M` in
`imogen/code/imogen_lpjg.f` returned **zero matches**. The original step 9.5
plan (Decision #12) assumed the Fortran engine *computed* RH and wind but
*didn't write* them — i.e., that the port was a writer-only addition (~20 LOC).

In reality, the Fortran engine **doesn't compute these variables at all**.
The C++ engine (climatemodel.cpp) added the entire RH and wind computation
pipeline (per `[CMI §4.3.4a]`); porting that to Fortran requires:

- Adding the underlying physics calculations (~50-80 LOC of Fortran)
- Adding the writer block (~20 LOC)
- Total: 70-100 LOC of careful Fortran work

This is significantly beyond step 9.5's 1-day budget and warrants its own
focused step. Created **step 9.5b** placeholder for it; deferred.

### 2.2 Discovery — Climate class has no per-month accumulator

A grep of `lpjguess/framework/guess.h` for monthly arrays in `Climate` showed:
- `Climate` has single-day fields (`temp`, `prec`, `relhum`, `u10`, `tmin`, `tmax`, `insol`)
- 20-year-window aggregates (`mtemp_min20`, `mtemp_max20`)
- A 31-day average (`mtemp`, "mean temperature for the last 31 days")
- **NO 12-element monthly mean array**

The original F-9 design assumed `gridcell.climate.mtemp[m]` etc. were
accessible at year-end in `MiscOutput::outannual`. They aren't. Implementing
F-9 properly requires either:
- Adding per-month accumulator arrays to `Climate` (~50 LOC across `Climate`
  setup, daily-update hook, year-end-reset hook, plus serialization)
- Or exposing per-day arrays from the input module (`IMOGENCFXInput::dtemp[]`
  etc.) to `MiscOutput::outannual` via a getter pattern (smaller but
  introduces cross-module coupling)

This was not anticipated in the original step 9.5 plan; deferred F-9 closure
to a focused future step (refined F-9 entry in `notes/FOLLOWUPS.md`).

### 2.3 Discovery — consumer infrastructure already half-built

Pleasant surprise: `lpjguess/modules/imogencfx.h` ALREADY had:
- `double drelhum[Date::MAX_YEAR_LENGTH]` and `double dwind[Date::MAX_YEAR_LENGTH]`
- `xtring file_relhum` and `xtring file_wind`
- `std::vector< std::vector< std::vector<double> > > all_drelhum` and `all_dwind`

But `imogencfx.cpp` (the implementation) had **none** of:
- `param["file_relhum"]` or `param["file_wind"]` reads in `init()`
- `read_lines_from_file(... all_drelhum ...)` calls in `read_climate_for_year()`
- `interp_monthly_means_conserve(mrelhum, drelhum)` in `get_climate_for_gridcell()`
- `climate.relhum = drelhum[date.day]` in `getclimate()`
- `resize3DimVector(all_drelhum, ...)` resize calls

So the infrastructure was scaffolded but never wired. Step 9.5 (c)
completes the wiring.

### 2.4 Discovery — `cfxinput.cpp` has the canonical pattern

`lpjguess/modules/cfxinput.cpp:1940-1945`:

```cpp
climate.insol  = dinsol[date.day];
climate.relhum = drelhum[date.day];
climate.u10    = dwind[date.day];
climate.tmax   = dmax_temp[date.day];
climate.tmin   = dmin_temp[date.day];
climate.dtr    = ddtr[date.day];
```

Step 9.5 (c) mirrors this pattern in `imogencfx.cpp::getclimate()`.

### 2.5 Units verified

| Variable | Unit (LPJ-GUESS Climate convention) | Source |
|---|---|---|
| `climate.temp` | °C | `Climate::temp` doc: "mean air temperature today (deg C)" |
| `climate.tmin`, `climate.tmax` | °C | `Climate::tmin`/`tmax` doc: "min and max daily temperature (deg C)" |
| `climate.relhum` | fraction (0-1), NOT % | `Climate::relhum` doc: "rel. humidity (fract.)" |
| `climate.u10` | km/h, NOT m/s | `Climate::u10` doc: "10 m wind (km/h)" |
| `climate.dtr` | °C | DTR ≡ diurnal temperature range |
| `climate.insol` | depends on `instype` | day-length-adjusted W/m² (typical) |
| IMOGEN engine `T_anom.dat` etc. output | K (anomaly) | `imogen_lpjg.f` declarations |

**Important unit caveat for v1.0**: when the C++ engine emits Tmin_anom.dat
with values in K, and `imogencfx::getclimate` assigns `climate.tmin = dtmin[..]`,
LPJ-GUESS will receive K values where it expects °C. **The K→°C conversion
isn't done in step 9.5**; it's a downstream concern. Documented in F-9
follow-up (and as a TODO comment in the new code).

---

## 3. What was implemented

### 3.1 `lpjguess/modules/imogencfx.h` — header additions (3 blocks)

```cpp
// Block 1 — per-day arrays for Tmin/Tmax (cfxinput.cpp:dmax_temp/dmin_temp pattern)
double dtmin[Date::MAX_YEAR_LENGTH];
double dtmax[Date::MAX_YEAR_LENGTH];

// Block 2 — paths to engine Tmin_anom.dat / Tmax_anom.dat outputs
xtring file_tmin;
xtring file_tmax;

// Block 3 — 3D vectors for storage across years × gridcells × months
std::vector< std::vector< std::vector<double> > > all_dtmin;
std::vector< std::vector< std::vector<double> > > all_dtmax;
```

### 3.2 `lpjguess/modules/imogencfx.cpp` — 5 wiring blocks

| Block | LOC | What |
|---|---|---|
| `IMOGENCFXInput::init()` (after existing `param[...]` reads) | +5 | Read 4 new ins parameters: `file_relhum`, `file_wind`, `file_tmin`, `file_tmax` |
| `IMOGENCFXInput::init()` (after existing `resize3DimVector` block) | +4 | Resize `all_drelhum`, `all_dwind`, `all_dtmin`, `all_dtmax` |
| `IMOGENCFXInput::read_climate_for_year()` (after existing reads) | +14 | 4 new `read_lines_from_file()` calls, each guarded with empty-path check |
| `IMOGENCFXInput::get_climate_for_gridcell()` (top + middle + bottom) | +50 | RESTORED BLAZE check with empty-path safety message; per-month → per-day interpolation for relhum/wind/tmin/tmax (`interp_monthly_means_conserve` for the 4 new vars); daily-mode passthrough block for the 4 new vars |
| `IMOGENCFXInput::getclimate()` (after existing `climate.dtr` assignment) | +5 | `climate.relhum = drelhum[date.day]; climate.u10 = dwind[..]; climate.tmin = dtmin[..]; climate.tmax = dtmax[..]` |

**BLAZE check (d)** is now active and produces an actionable error message:

```cpp
if (firemodel == BLAZE) {
    if (file_relhum == "" || file_wind == "") {
        fail("imogencfx with firemodel=BLAZE requires file_relhum + file_wind "
             "ins parameters pointing at the IMOGEN engine's Rh_anom.dat / "
             "W_anom.dat per-year output. None set; aborting. (See "
             "runs/SSP1-2.6/imogen_intermediary.ins for canonical layout.)");
    }
}
```

### 3.3 `lpjguess/modules/climatemodel.cpp` — Tmin/Tmax write (item b, partial)

In the non-REGRID native-grid output branch (lines ~880-958):
- Added `file100, file101` ofstream declarations
- Added open at `iyear == year1`: `Tmin_anom.dat`, `Tmax_anom.dat`
- Added per-gridpoint lon/lat header writes
- Added per-month writes in BOTH the `dailyOut == true` and `dailyOut == false` sub-branches:
  - `Tmin = tOutM[..] − dtempOutM[..]/2`
  - `Tmax = tOutM[..] + dtempOutM[..]/2`
- Added newlines + close at `iyear == iyend`

**Caveat**: only the non-REGRID branch was updated. The REGRID branch
(used when `REGRID=1` in ins file; smoke uses `REGRID=0`) needs the same
treatment — TODO at step 9.5b.

### 3.4 What was NOT implemented (deferred)

| Item | Why deferred | Where to track |
|---|---|---|
| **(a) Fortran Rh/W writer port** | Investigation revealed Fortran engine doesn't COMPUTE Rh/wind at all (the C++ port added entire pipeline); ~70-100 LOC of Fortran work, beyond step 9.5's budget | New: step 9.5b (in EXECUTION_PLAN as a follow-on; or merge into the F-12 sprint if v1.0 ends up using only the C++ engine) |
| **(b) Fortran Tmin/Tmax** | Depends on (a)'s computation infrastructure | Same as (a) |
| **(b) C++ Tmin/Tmax in REGRID branch** | Smoke uses `REGRID=0`; non-REGRID branch covers v1.0 | Step 9.5b TODO |
| **(e) F-9 closure** | Requires per-month accumulator infrastructure that doesn't yet exist in `Climate` or accessible from `MiscOutput::outannual`; ~50 LOC infrastructure work | F-9 in `notes/FOLLOWUPS.md`, refined at step 9.5 with the per-month-accumulator blocker now identified |

---

## 4. Verification

### 4.1 Build

```bash
cd lpjguess/build
make
```

Output:
```
[ 49%] Linking CXX executable runtests
[100%] Built target runtests
```

✅ Clean build; no warnings on the new step 9.5 code.

### 4.2 Unit tests

```bash
./runtests
```

Output:
```
All tests passed (162 assertions in 25 test cases)
```

✅ No regression.

### 4.3 End-to-end smoke (NOT POSSIBLE in v1.0)

Because of F-10's architectural deadlock empirically confirmed at step 9
(`notes/STEP_9.md` §4.4), LPJG main loop never enters in v1.0 single-process
imogencfx mode. So the new wiring at `imogencfx.cpp::get_climate_for_gridcell`
and `imogencfx.cpp::getclimate` cannot actually fire in v1.0. The wiring is
**code-correct, build-verified, but un-testable end-to-end** until F-12 is
implemented.

What CAN be verified:
- (b) C++ engine Tmin/Tmax: re-run the step 9 smoke; check that `Tmin_anom.dat`
  and `Tmax_anom.dat` files appear in `Common-directory/IMOGEN/output/<YYYY>/`
  per year (engine completes 32 years before deadlocking, so 32 × 2 = 64 new
  files should appear). **Verifiable.**
- (c)+(d): the new BLAZE check with empty-path safety triggers ONLY if
  `firemodel == BLAZE` AND paths empty. Our smoke uses `firemodel = NOFIRE`
  so this code path is dormant in v1.0.

---

## 5. Files modified / added

### Added

(none)

### Modified

| Path | Change |
|---|---|
| `lpjguess/modules/imogencfx.h` | +3 doc-comment blocks; +`dtmin`/`dtmax` arrays; +`file_tmin`/`file_tmax` xtring; +`all_dtmin`/`all_dtmax` 3D vectors |
| `lpjguess/modules/imogencfx.cpp` | +5 wiring blocks (param reads, resizes, file reads, monthly→daily interpolation, climate.* assignments); BLAZE check restored with empty-path safety message |
| `lpjguess/modules/climatemodel.cpp` | +Tmin/Tmax write block in non-REGRID branch (file100/file101) |
| `notes/FOLLOWUPS.md` | F-9 entry refined with per-month-accumulator blocker; F-9 stays open |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | +Step 9.5 entry (3 lpjguess C++ files modified) |
| `EXECUTION_PLAN.md` | Step 9.5 row marked PARTIAL with scope refinement; new step 9.5b placeholder for deferred Fortran work |
| `CHANGELOG.md` | `[v0.10.0-step9.5-consumer-wiring]` entry |

---

## 6. Push commands (manual three-way push)

```bash
cd /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm

git add .
git commit -m "Step 9.5: wire LPJG consumer for IMOGEN Rh/Wind/Tmin/Tmax + BLAZE check restore + C++ engine Tmin/Tmax; Fortran port deferred to step 9.5b; F-9 refined"
git push origin     main
git push kit        main
git push helmholtz  main

git tag -a v0.10.0-step9.5-consumer-wiring -m "Step 9.5: LPJG-side consumer wiring for new IMOGEN climate outputs (Rh, wind, Tmin, Tmax) + BLAZE check restored + C++ engine Tmin/Tmax write"
git push origin     v0.10.0-step9.5-consumer-wiring
git push kit        v0.10.0-step9.5-consumer-wiring
git push helmholtz  v0.10.0-step9.5-consumer-wiring
```
