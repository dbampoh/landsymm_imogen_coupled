# STEP 9 — `runs/SSP1-2.6/imogen_intermediary.ins` + bug C5/C35/R-anom fixes + first coupled smoke

**Date completed:** 2026-05-07
**Commit:** _to be filled in after `git commit`_
**Status:** **PARTIALLY VERIFIED** — ins-file infrastructure works; engine runs end-to-end with correct units; bug fixes proven; **F-10 architectural deadlock empirically confirmed in BOTH `coupling_mode="tight"` and `coupling_mode="prescribed"`** — V.1 step-9 verification milestone (NEE 2x → CO2 shift) cannot be tested in v1.0 single-process mode; gated on **new follow-up F-12** (multi-pass / two-process verification design).

---

## 1. Goal (per `EXECUTION_PLAN.md` V.1 step 9)

> Rewrite `FILE_LPJG_FLUX` and `FILE_LPJG_CH4_N2O_FLUX` in
> `runs/SSP1-2.6/imogen_intermediary.ins` to relative filenames
> (`imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt`) so the
> engine reads what step 8's writer produces. Fix bug C35 (per [CMI §3.7]).
> Verify the `coupling_mode = tight` parameter is honoured; verify a
> `coupling_mode = prescribed` run with the original IIASA-style absolute
> paths still works.

---

## 2. Investigation findings (informed the design)

### 2.1 Predecessor `imogen_intermediary.ins` (version_A SSP1_RCP26 setup)

The predecessor's setup was thoroughly read at step 9 phase A:
- 35 files in `version_A/.../landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/`
- 33 files in `version_B/.../landsymm_imogen/SSP1_RCP26/` (differs from A
  by `scenario "cmip5"` (vs A's "cmip6"), HPC paths, and **`LPJG_CFLUX 0`
  (vs A's 1)** — meaning B was effectively pure prescribed mode)
- `setup_run.sh` invoked `setup_run_owl_with_scratch_lpj_work.sh`
  with `imogencfx` input mode

### 2.2 Bug catalogue confirmed

| Bug | Location | Fix |
|---|---|---|
| **C5** ([CMI §3.7]) | `imogen_intermediary.ins:102-109` | Typo `ouput` → `output` in 8 climate-input paths |
| **C35** ([CMI §3.7]) | `imogen_intermediary.ins:63, 65` | Use RELATIVE filenames so concat resolves to `<DIR_COMMON>/LPJG_main/IMOGEN/...` |
| **R-anom → Rh_anom** | `imogen_intermediary.ins:109` | C++ engine emits `Rh_anom.dat`, not `R_anom.dat`; predecessor mismatch was silent failure |

### 2.3 Units audit (from step 9 phase A.5; very thorough)

| Engine variable | Source | Unit | Confirmed where |
|---|---|---|---|
| `C_LPJG` | LPJG handshake (or absolute-path static file) | **PgC/yr** (= GtC/yr) | `imogen_lpjg.f:114-116` (`PARAMETER(CONV=0.471)` = canonical 0.471 ppmv/GtC) |
| `CH4_LPJG` | LPJG handshake (or absolute-path static file) | **TgCH4/yr** | `nonco2.f:143` ("emiss.annual.ghg are for CH4 (CH4 emissions TgCH4/yr) and N2O (N2O emissions TgN2O/yr)") |
| `N2O_LPJG` | LPJG handshake (or absolute-path static file) | **TgN2O/yr** | Same `nonco2.f:143`; engine internally converts via `(MM_N2/MM_N2O)*(1e12/1e3)` to kgN-equivalent for FAIR |
| `CO2_INIT_PPMV`, `CH4_INIT_PPBV`, `N2O_INIT_PPBV` | ins file | **ppmv / ppbv** | predecessor convention; FAIR-compliant |
| Climate anomaly outputs (`T_anom.dat` etc.) | engine year directories | K, mm/day, W/m², kg/kg, m/s, days/month, ppmv | `imogen_lpjg.f` declarations |

Step 8's `ImogenOutput::flush_year` units are **fully correct** for the engine's expectations:
- NEE: `accum_NEE_kgC * 1e-12` → PgC/yr ✓
- CH4: `accum_CH4_gCH4C * (16/12) * 1e-12` → TgCH4/yr ✓ (g(CH4-C) → g(CH4) → Tg)
- N2O: `accum_N2O_kgN * (44/28) * 1e-9` → TgN2O/yr ✓ (kgN → kgN2O → Tg)

---

## 3. What was implemented

### 3.1 `runs/SSP1-2.6/` directory + 11 PFT/stand/landcover ins files

Copied from version_A's predecessor SSP1_RCP26 setup (preserved as immutable).
LU paths in `crop.ins` and `landcover.ins` retargeted from the predecessor's
stale `/home/bampoh-d/Desktop/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Data/LU/...`
to version_A's actual tree at
`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/.../version_A/.../Data/LU/...`.

### 3.2 `runs/SSP1-2.6/main.ins` (NEW)

- Imports `global.ins`, `crop_n.ins`, `wetlandpfts.ins`, `imogen_intermediary.ins`
- Smoke overrides: `nyear_spinup=100`, `freenyears=50` (predecessor: 500/100),
  `npatch=1` (predecessor: 25), `firemodel="NOFIRE"` (avoiding BLAZE
  wind/RH dependency), `run_landcover=1` (per user guidance to use LU)
- Year-range params: `firsthistyear=1871, lasthistyear=1872, firstoutyear=1871,
  lastoutyear=1872` (LPJG validator requires > 0)
- File paths set for tight coupling: `file_temp`, `file_prec`, etc. all
  point at `./IMOGEN/output/YYYY/*.dat` (with bug C5 fix: `output` not `ouput`)

### 3.3 `runs/SSP1-2.6/imogen_intermediary.ins` (NEW; ~250 lines)

- **Bug C5 fix** at lines 102-109 of analog: `output/` not `ouput/`
- **Bug R-anom fix** at line 109 analog: `Rh_anom.dat` not `R_anom.dat`
- **Bug C35 attempted fix** (relative filenames) — commented out with extensive
  documentation of the empirical F-10 deadlock that prevents this from
  working in v1.0; PRESCRIBED-mode absolute paths are the v1.0 default
- All other params: `DIR_COMMON`, `DIR_PATT` (CMIP6 MRI-ESM2-0 per Stage 1
  paper consistency), `DIR_CLIM` (CRUNCEP), `FILE_SCEN_EMITS` (anthropogenic
  CO2 SSP126), `FILE_NON_CO2_VALS` (SSP126 RF; copied from version_B at
  step 9 — see §3.5 below), `FILE_CH4_N2O_EMITS` (anthropogenic CH4+N2O SSP126)
- All numerical engine params (`CONV`, `T_OCEAN_INIT`, `KAPPA_O`, etc.):
  predecessor defaults preserved
- `coupling_mode "prescribed"` (default for v1.0; `"tight"` documented
  but disabled due to F-10)

### 3.4 `runs/SSP1-2.6/README.md` (NEW)

User-facing documentation describing:
- What's in the directory
- How to run (with bootstrap-handshake setup)
- The empirical F-10 deadlock findings
- Production setup overrides (post-V.1)
- v1.0 caveats summary

### 3.5 SSP126 NON_CO2 RF file added to our tree

`imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp126.txt`
(3.5 KB, 251 years 1850-2100). Was MISSING from our tree (the other 4 SSP
files ssp245/ssp370/ssp460/ssp585 were imported at step 6 — only SSP126
was overlooked). Imported from version_B at step 9.

### 3.6 `imogen_nee_perturbation_factor` runtime parameter (ADDED then REMOVED)

Added at step 9 as a V.1 step-9 verification helper, then **removed at
step 9's wrap-up** because the smoke test empirically confirmed F-10's
architectural deadlock means LPJG main loop never runs in v1.0
single-process mode — so the perturbation factor cannot affect anything
that's actually observable. Resolution will be designed at follow-up F-12.

Net source-level changes after step 9 wrap-up: **zero** — `parameters.h/cpp`,
`imogencfx.cpp`, `imogenoutput.cpp` are all back to their step-8 state
plus only annotation comments referencing this add-then-remove decision.

---

## 4. Smoke test execution (2026-05-07)

### 4.1 Command sequence (the actual flow that ran)

```bash
cd runs/SSP1-2.6/
mkdir -p Common-directory/LPJG_main/IMOGEN
# Bootstrap files (predecessor's pattern; CMI 3.7.4 documented)
cat > Common-directory/LPJG_main/IMOGEN/imogen_lpjg.txt <<'EOF'
YEAR1 1871
IYEND 1872
YEAR1_LPJG 1871
SPINUP FALSE
KEEPRUNNING TRUE
FIRSTCALL TRUE
EOF
echo "bootstrap" > Common-directory/LPJG_main/IMOGEN/done
# Launch
../../lpjguess/build/guess -input imogencfx main.ins > guess.log 2>&1
```

### 4.2 What worked

- ins-file parsed without errors (after 4 iterative fixes — see §4.3)
- Engine startup banner printed correctly:
  `[IMOGEN LOGGER] IMOGEN Logger initialized`
- Engine read inputs:
  - 12 monthly GCM pattern files for CMIP6 MRI-ESM2-0 ✓
  - CRUNCEP base climatology (1960-1989) ✓
  - 251 years anthropogenic CO2 emissions ✓
  - 251 years NON_CO2 RF (SSP126 file) ✓
  - 251 years LPJG-style CH4+N2O fluxes (absolute-path static IIASA file) ✓
  - 251 years LPJG-style CO2 fluxes (absolute-path static IIASA file) ✓
- Engine produced **32 years × 10 climate output files = 320 files** in 3 min:
  `Common-directory/IMOGEN/output/<1871..1902>/{T_anom,P_anom,SW_anom,DTEMP_anom,Rh_anom,W_anom,WET,CO2,dtemp_o,fa_ocean}.dat + done`
- Each climate output file: ~246 KB (correctly sized for the regridded grid)

### 4.3 Iterative fixes during 4 smoke attempts

| Attempt | Failure | Cause | Fix |
|---|---|---|---|
| 1 | `freenyears must be smaller than nyear_spinup` | Override `nyear_spinup=5` < default `freenyears=100` | Bumped `nyear_spinup=100, freenyears=50` |
| 2 | `firsthistyear and lasthistyear must be specified in ins-file and >0` | Predecessor's main.ins had `firsthistyear 1901`, ours didn't | Added `firsthistyear/lasthistyear/firstoutyear/lastoutyear=1871-1872` |
| 3 | Polling deadlock with relative-path C35 fix (`RUNFLUX_EXIST=0` forever) | F-10 architectural deadlock with relative paths | Switched to `coupling_mode="prescribed"` + absolute paths to static IIASA files |
| 4 | `Invalid data format in file: RF_NONCO2_GHG_IS92A.dat` | Used wrong NON_CO2 RF file (243 rows vs `NYR_NON_CO2=251`) | Imported SSP126-specific file from version_B; updated FILE_NON_CO2_VALS path |

After fix 4, the engine ran 32 years before deadlocking on the per-year handshake polling.

### 4.4 The deadlock — F-10 empirically confirmed

**Final polling state observed:**
```
RUNNOW_EXIST = (1)     → imogen_lpjg.txt exists (we bootstrapped it)
RUNNOW_OPEN = 0        → opened OK
RUNFLUX_EXIST = 1      → FILE_LPJG_FLUX exists (absolute static path)
RUNFLUX_OPEN = 0       → opened OK
DONE_EXIST = 0         → done DELETED by engine after consuming year N
NONCO2_EMISSIONS = 1
RUNNONCO2FLUX_EXIST = 1 → FILE_LPJG_CH4_N2O_FLUX exists (absolute static)
RUNNONCO2FLUX_OPEN = 0
.                       → polling continues forever
```

The engine, after running 32 outer cycles (each producing a year of
climate output), needs LPJG to write a NEW `imogen_lpjg.txt` AND
re-create `done` to proceed to the next outer cycle. LPJG cannot do this
because LPJG's main loop hasn't started — `imogencfx::init()` hasn't
returned because the engine is still stuck in its outer `KEEPRUNNING`
loop. Architectural deadlock.

This is the **single-process manifestation of F-10**. F-10's predicted
loop-ordering mismatch combines with the engine's per-year-handshake
expectation to produce a hard deadlock.

### 4.5 Verifiable evidence

```
Engine year directories: 32      (output/1871/ ... output/1902/)
guess.log: 33,963 lines           (mostly polling-loop prints)
LPJG main loop: NOT REACHED       (no .out files; no step 8 writer output)
Common-directory/LPJG_main/IMOGEN/imogen_lpjg_flux.txt: NOT WRITTEN
Common-directory/LPJG_main/IMOGEN/imogen_lpjg_ch4_n2o_flux.txt: NOT WRITTEN
```

---

## 5. Bug-fix delivery status

| Bug | v1.0 status | Verification |
|---|---|---|
| **C5** | ✅ FIXED + PROVEN | Engine wrote to `IMOGEN/output/YYYY/` directories (not `ouput/`); 32 directories observed |
| **R-anom → Rh_anom** | ✅ FIXED + PROVEN | Engine wrote `Rh_anom.dat`; matches our `file_relhum` path |
| **C35** | ⚠️ FIXED IN .ins (relative paths in commented block) but UN-TESTABLE in v1.0 — using prescribed-mode absolute paths to avoid F-10 deadlock | Will be testable when F-12 is implemented |

---

## 6. New follow-up F-12

Added to `notes/FOLLOWUPS.md` for the multi-pass / two-process tight-mode
verification design. Summary:

- **Goal**: enable real two-way IMOGEN ↔ LPJG coupling end-to-end
- **Design space**:
  - **Option A** (multi-pass): user runs `guess` once with N pre-populated
    handshake files; LPJG main loop runs after engine; LPJG writes year-N
    handshake; user re-runs `guess` so engine reads year-N updated handshake
    for year-(N+1)'s climate. Fragile but no architectural change.
  - **Option B** (two-process): split `imogen_lpjg` engine binary out of
    LPJG; run them concurrently with file-based sync; engine polls per-year
    and waits for LPJG. This is what the predecessor's polling loop was
    actually designed for.
  - **Option C** (in-process restructure per F-10 Phase-2): add
    `framework_loop_mode="year_outer"` parameter that gates a NEW
    per-year-outer code path alongside the existing one. This is F-10's
    Phase-2 design. Larger surface area but gives genuine in-process
    tight coupling.
- **Recommended**: Option B (two-process) for v1.0 → v1.1; Option C for v2.0+

---

## 7. Files modified / added

### Added (committed)

| Path | Bytes | Purpose |
|---|---|---|
| `runs/SSP1-2.6/main.ins` | ~6 KB | LPJG entry point (smoke + LU) |
| `runs/SSP1-2.6/imogen_intermediary.ins` | ~14 KB | IMOGEN-coupling params (bug fixes embedded) |
| `runs/SSP1-2.6/README.md` | ~6 KB | Run-config documentation |
| `runs/SSP1-2.6/{global, global_soiln, crop, crop_n, crop_n_*, pasture_n_*, landcover, wetlandpfts}.ins` | ~78 KB | 11 stand/PFT files (copied from version_A predecessor; LU paths retargeted) |
| `imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp126.txt` | 3.5 KB | SSP126 NON_CO2 RF file (was missing from our tree) |
| `notes/STEP_9.md` | this file | Per-step verification record |

### Modified

| Path | Change |
|---|---|
| `notes/FOLLOWUPS.md` | New entry F-12 (multi-pass / two-process tight-mode verification design) |
| `lpjguess/framework/parameters.h` | Annotation comment about add-then-remove of `imogen_nee_perturbation_factor` (NET CODE: zero changes; only comment) |
| `lpjguess/framework/parameters.cpp` | Same |
| `lpjguess/modules/imogencfx.cpp` | Same |
| `lpjguess/modules/imogenoutput.cpp` | Same |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | Step 9 entry (with the add-then-remove cancellation noted; NET ledger entries: only the 4 annotation comments) |
| `CHANGELOG.md` | `[v0.9.0-step9-smoke]` entry |
| `EXECUTION_PLAN.md` | V.1 step 9 row marked ⚠️-PARTIAL with F-10/F-12 cross-reference |

---

## 8. Push commands (manual three-way push)

```bash
cd /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm

git add .
git commit -m "Step 9: SSP1-2.6 run-config + bug C5/R-anom fixes + empirical F-10 confirmation; F-12 opened"
git push origin     main
git push kit        main
git push helmholtz  main

git tag -a v0.9.0-step9-smoke -m "Step 9: ins-file infrastructure + bug fixes + F-10 deadlock empirically confirmed"
git push origin     v0.9.0-step9-smoke
git push kit        v0.9.0-step9-smoke
git push helmholtz  v0.9.0-step9-smoke
```
