# Production-run configuration reference

**Version**: v1.0 (initial draft)
**Last updated**: 2026-05-19 (session 6; B19+B20 close-out era; pre-local-v1-verification-window)
**Status**: 🔧 INITIAL DRAFT — to be iteratively refined as B36 + B37 + B39 + B40 (local v1 verification window) and 17c.1+ cluster phase 1 inform the v1.0 paper publication readiness checklist.

**Audience**: anyone (current + future maintainers) needing to:
- Run the v1.0 coupled model in production-style configuration on either local workstation OR HPC cluster
- Understand the gap between the smoke-test setup (`runs/SSP1-2.6/main.ins`) and the production-run setup
- Configure LU forcing for the v1.0 paper publication (the updated `_peatland` variant)
- Decide which `-input` module to use for each run-type
- Plan the v1.0 paper publication run sequence

**Companions**:
- `runs/SSP1-2.6/main.ins` — the canonical smoke-test main.ins (current rebuild)
- `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/main.ins` — example production-style main.ins (historical + SSP1-2.6)
- `notes/FOLLOWUPS.md` rows B41 + B42 + B43 — audit-item tracking
- `notes/B19.md` — closed-loop verification milestone (B19 + B20 = v1.0 magnitude validation)
- `docs/scientific_framework.md` — coupled-model scientific architecture; §5 F-10 caveat + §5.3 natural-flux mutual exclusion
- `EXECUTION_PLAN.md` row 17c — cluster-phase plan

---

## 1. Why this document exists

The v1.0 coupled-model rebuild has so far operated under a **stripped-down smoke-test configuration** in `runs/SSP1-2.6/main.ins` to enable rapid iteration during the rebuild. The smoke configuration is operationally distant from what the v1.0 paper publication needs:

- 4-cell `gridlist_test2.txt` (smoke) vs full 62892-cell `gridlist_in_62892_and_climate.txt` (production)
- 1-year `nyear_spinup` (smoke) vs 500-year (production)
- 1 patch (smoke) vs 25 patches (production)
- `firemodel "NOFIRE"` + empty `file_simfire` (smoke) vs `firemodel "BLAZE"` + actual SimFire binary (production)
- No popdens NetCDF + no wet/dry NHx+NOy ndep NetCDFs (smoke) vs all four production NetCDFs
- Legacy `version_A/.../SSP1_RCP26_concatenated/LU_*` LU forcing (smoke) vs updated `_peatland`-tagged LU forcing at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/` (production)
- 2-year window (smoke; 1900-1901) vs full 1900-2100 (production)

This document captures the full smoke→production migration delta, the updated LU forcing dataset paths, the cluster ↔ local path translation, the input-module evolution (`cf` → `cfx` → `imogencfx`), and the v1.0 paper publication run sequence. It exists to ensure that the architectural picture the user shared at session 5 (2026-05-18 evening) + session 6 (2026-05-19 morning) is preserved in the rebuild project's documentation rather than living only in the chat handoff.

---

## 2. Smoke→production parameter delta

### 2.1 main.ins

| Parameter | Smoke (current `runs/SSP1-2.6/main.ins`) | Production (target for v1.0 paper) | Source of production value |
|---|---|---|---|
| `firsthistyear` / `lasthistyear` | 1900 / 1901 | 1900 / 2020 (historical) → 2021 / 2100 (SSP scenario) | matches LU forcing year coverage |
| `firstoutyear` / `lastoutyear` | 1900 / 1901 | 1900 / 2020 → 2021 / 2100 | full publication time series |
| `file_gridlist` | `data/gridlist/gridlist_test2.txt` (4 cells) | `gridlist_in_62892_and_climate.txt` (62538 valid cells from 62892 nominal) | `integrated-4.1-ins2_landsymm_hist:35` |
| `file_gridlist_cf` | (matches gridlist) | (matches gridlist) | input-module specific |
| `file_soildata` | `soilmap_center_interpolated.remapv10_old_62892_gL.dat` | (same; production soilmap covers full 62892-cell production gridlist) | production soilmap is correct as-is |
| `nyear_spinup` | 1 (B19 ADDENDUM smoke) | **500** | `integrated-4.1-ins2_landsymm_hist:40` |
| `freenyears` | (smoke uses LPJG default) | **100** | `integrated-4.1-ins2_landsymm_hist:41` |
| `firemodel` | `"NOFIRE"` | **`"BLAZE"`** | production setup default |
| `npatch` | 1 | **25** | LPJG production default |
| `run_landcover` | 1 | 1 (already correct in smoke) | matches |
| `file_temp` etc. (climate) | empty (cf reader not used) | (cfx mode) ISIMIP3b NetCDFs OR (imogencfx mode) IMOGEN-engine ASCII per-year | depends on input module |
| `file_co2` | empty (cf reader not used) | (cfx mode) `co2_histssp126_annual_1850_2100.txt` OR (imogencfx mode) IMOGEN-engine `CO2.dat` per-year | depends on input module |
| `state_path` / `save_state` / `restart` | not used (smoke) | historical run saves at year 2020; SSP runs restart from the historical state | per integrated-4.1-ins2_landsymm_{hist,ssp126} |

### 2.2 landcover.ins + crop.ins

| Parameter | Smoke | Production (v1.0 paper) | Where to get the production file |
|---|---|---|---|
| `file_lu` | legacy `version_A/.../LU_SSP1_RCP26_1901_2100_final.txt` | **`LU.remapv10_old_62892_gL_peatland.txt`** (historical) + **`landcover_peatland.txt`** (SSP) | `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/output_hildaplus_remap_10b_3/remaps_v10_old_62892_gL/` (hist) + `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/<SSPx_RCPyy>/s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/` (SSP) |
| `file_lucrop` | legacy `cropfracs_SSP1_RCP26_1901_2100_final.txt` | `cropfracs.remapv10_old_62892_gL.txt` (historical) + `cropfractions.txt` (SSP) | same dirs as above |
| `file_Nfert` | legacy `nfert_SSP1_RCP26_1901_2100_final.txt` | `nfert.remapv10_old_62892_gL.txt` (historical) + `nfert.txt` (SSP) | same dirs as above |
| `file_irrigintens` | legacy `irrig_SSP1_RCP26_1901_2100_final.txt` | (historical: NO irrig file — use empty `""`) + `irrig.txt` (SSP) | same dirs as above |

### 2.3 Auxiliary input files (cfx + imogencfx production-only)

| Parameter | Smoke value | Production value | Where |
|---|---|---|---|
| `file_simfire` | `""` | `SimfireInput.bin` | `/media/bampoh-d/lpjg_input/input/fire/SimfireInput.bin` (local) ↔ `/bg/data/lpj/LPJ-GUESS/input/fire/SimfireInput.bin` (cluster) |
| `file_popdens` | (not set; firemodel=NOFIRE) | population NetCDF for SimFire ignition | `/media/bampoh-d/lpjg_input/input/pop_dens/...` (local) ↔ `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/pop/lpjg-popd/...` (cluster) |
| `file_mNHxdrydep` | (not set) | `ndep_drynhx_*.nc4` (per-SSP) | `/media/bampoh-d/lpjg_input/input/ndep/...` ↔ cluster equivalent |
| `file_mNHxwetdep` | (not set) | `ndep_wetnhx_*.nc4` | (same) |
| `file_mNOydrydep` | (not set) | `ndep_drynoy_*.nc4` | (same) |
| `file_mNOywetdep` | (not set) | `ndep_wetnoy_*.nc4` | (same) |

The smoke setup falls back to LPJG's pre-industrial-constant 2 kgN/ha/yr ndep when `file_ndep` is empty + the 4 wet/dry NetCDFs aren't supplied. This is **acceptable for smoke validation** (B19 + B20 PASS) but **insufficient for paper-grade publication runs** (modern N deposition is ~5-15× pre-industrial in many regions; impacts soil N cycling + N2O; IPCC AR6 standard N-deposition forcing is the 4-NetCDF wet/dry NHx + NOy product).

---

## 3. Updated LU forcing dataset map

### 3.1 Local mirror

```
/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/
├── output_hildaplus_remap_10b_3/
│   └── remaps_v10_old_62892_gL/                                    ← HISTORICAL 1900-2020
│       ├── LU.remapv10_old_62892_gL.txt                            (basic; 413 MB)
│       ├── LU.remapv10_old_62892_gL_peatland.txt                   ✓ USE THIS (664 MB; peatland-tagged)
│       ├── cropfracs.remapv10_old_62892_gL.txt                     (12.7 MB)
│       ├── nfert.remapv10_old_62892_gL.txt                         (12.7 MB)
│       └── soilmap_center_interpolated.remapv10_old_62892_gL.dat   (3.6 MB; matches production gridlist)
│       └── (NO irrig file for historical)
├── SSP1_RCP26/                                                     ← SSP1-RCP2.6 SCENARIO 2020-2100
│   └── s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/
│       ├── landcover.txt                                           (basic; 275 MB)
│       ├── landcover_peatland.txt                                  ✓ USE THIS (315 MB; peatland-tagged)
│       ├── cropfractions.txt                                       (1.05 GB)
│       ├── nfert.txt                                               (1.05 GB)
│       └── irrig.txt                                               (1.05 GB; SSP-period only)
├── SSP2_RCP45/                                                     ← (similar structure)
├── SSP3_RCP70/                                                     ← (similar structure)
├── SSP4_RCP60/                                                     ← (similar structure)
└── SSP5_RCP85/                                                     ← (similar structure)
```

### 3.2 Cluster path equivalence

| Local | Cluster |
|---|---|
| `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/` | `/bg/data/lpj/bampoh-d/landsymm_lu/` (per `integrated-4.1-ins2_landsymm_hist/landcover.ins:11`) |
| `/media/bampoh-d/lpjg_input/input/fire/SimfireInput.bin` | `/bg/data/lpj/LPJ-GUESS/input/fire/SimfireInput.bin` |
| `/media/bampoh-d/lpjg_input/input/pop_dens/...` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/pop/lpjg-popd/...` |
| `/media/bampoh-d/lpjg_input/input/ndep/...` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/n-deposition/...` |
| `/media/bampoh-d/lpjg_input/input/isimip/isimip3/climate_land_only_v2/climate3b/...` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/climate_land_only_v2/climate3b/...` |
| `/media/bampoh-d/lpjg_input/input/isimip/isimip3/co2/co2_histssp126_annual_1850_2100.txt` | `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/co2/co2_histssp126_annual_1850_2100.txt` |

Production .ins files maintained on the cluster reference `/bg/data/lpj/...` paths; for local production-style validation runs (e.g., during local v1 verification window) these need to be substituted with `/media/bampoh-d/lpjg_input/input/...` equivalents.

---

## 4. Input-module evolution

The lpjguess source registers **5 input modules** (`grep REGISTER_INPUT_MODULE lpjguess/modules/*.cpp`):

| Module | Source file | What it reads | Used by |
|---|---|---|---|
| `cf` | `cfinput.cpp` | older CF-NetCDF reader (climate only) | (deprecated; not used in v1.0) |
| `cfx` | `cfxinput.cpp` | extended CF-NetCDF reader: ISIMIP3b climate (NetCDF) + atmospheric CO2 (txt) + popdens (NetCDF) + SimFire binary + 4-NetCDF wet/dry NHx+NOy ndep + LU forcing | **Track 1: past + future Track-1 cluster runs** that produced the LPJG natural-flux outputs feeding `intermediary_py` Component B |
| `imogen` | `imogen_input.cpp` | LPJG reads pre-baked IMOGEN climate from disk (loose mode; standalone) | F-10 deadlock-bypass mode for cross-validation |
| `imogencfx` | `imogencfx.cpp` | IMOGEN engine output (climate + CO2; in-process via RUN_IMOGEN_ENGINE) + cfx-style auxiliaries (popdens, SimFire, ndep, LU forcing) | **Track 2: v1.0 paper publication coupled-mode runs** (in-process IMOGEN engine drives LPJG climate + CO2; everything else flows like cfx) |
| `demo` | `demoinput.cpp` | demonstration / placeholder | (not used) |
| `firemip` | `firemipinput.cpp` | FireMIP-specific inputs | (not used in v1.0) |

**Key relationship**: `imogencfx` IS `cfx` + IMOGEN-engine-substitution-for-climate-and-CO2. Switching from `cfx` (Track 1) to `imogencfx` (Track 2) for the v1.0 paper publication keeps every other input pipeline (popdens, SimFire, ndep, LU, soil, gridlist) identical; only the climate + CO2 sources differ. **This is what makes the Track 1 vs Track 2 ecosystem comparison clean** for the paper.

The stale `! Make sure to start LPJ-GUESS with -input cf` comment in `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/main.ins` headers is a leftover from an earlier era; the actual production `setup_run.sh` invocation uses `cfx` (per `setup_run.sh` line 4 inputmethod arg). Worth correcting in the production .ins headers as a small future fix-it (TRUNK-IRRELEVANT-by-novelty since `lpjg_landsymm_integration/` lives outside the rebuild repo).

---

## 5. Two-track architecture for v1.0 paper publication

### 5.1 Track 1 — LPJG-cfx-ISIMIP3b (baseline; outputs already exist)

**Driver**: `-input cfx` + ISIMIP3b MRI-ESM2-0 climate (1850-2014 historical + 2015-2100 SSP scenario per scenario; 6 NetCDF files: tas, pr, rsds, sfcwind, hurs, tasmin, tasmax) + ISIMIP3b atmospheric CO2 (per-scenario txt: e.g. `co2_histssp126_annual_1850_2100.txt`)

**Auxiliaries** (same across both tracks for clean comparison): updated `_peatland` LU forcing, popdens NetCDF, SimFire BLAZE binary, 4 wet/dry NHx + NOy ndep NetCDFs, soilmap

**Outputs**: ecosystem state outputs (`*.out` files), LPJG-natural CH4 + N2O fluxes (`ngases.out` per-cell + global aggregations) — **the `imogen_lpjg_*_flux.txt`-style outputs from these runs were post-processed and stored in `intermediary_py/imogen_ghg_controller/INPUT_DATA/lpjg/` to feed Component B's natural-flux modeling per the user 2026-05-19 morning confirmation**.

**Status**: 5 cluster runs completed by user (SSP1-RCP2.6 + SSP2-RCP4.5 + SSP3-RCP7.0 + SSP4-RCP6.0 + SSP5-RCP8.5); outputs already in `intermediary_py` input data; B20 literature comparison validated the natural-flux magnitudes (full-envelope time-mean WITHIN Saunois 2020 + Tian 2020 envelopes).

### 5.2 Track 2 — LPJG-imogencfx-IMOGEN (NEW for v1.0 paper publication)

**Driver**: `-input imogencfx` + IMOGEN-engine climate (in-process via `RUN_IMOGEN_ENGINE()` at `lpjguess/modules/climatemodel.cpp:153`; emits per-year ASCII at `Common-directory/IMOGEN/output/<year>/{T_anom,P_anom,SW_anom,Rh_anom,W_anom,DTEMP_anom,Tmax_anom,Tmin_anom,WET}.dat`) + IMOGEN-engine atmospheric CO2 (in-process via the same engine; emits per-year ASCII at `Common-directory/IMOGEN/output/<year>/CO2.dat`)

**Engine inputs**: anthropogenic CO2/CH4/N2O emissions (from `intermediary_py` Component A: RCMIP/CMIP6 substitution) + natural CO2/CH4/N2O fluxes (from `intermediary_py` Component B: post-processed Track 1 LPJG-natural-flux data) — both flow through the prescribed-mode handshake at `runs/<SSP>/inputs/{co2,ch4_n2o}_anthro_emissions.txt` + `runs/<SSP>/inputs/imogen_lpjg_{flux,ch4_n2o_flux}.txt`

**Auxiliaries** (same as Track 1 for clean comparison): updated `_peatland` LU forcing, popdens NetCDF, SimFire BLAZE binary, 4 wet/dry NHx + NOy ndep NetCDFs, soilmap

**Outputs**: ecosystem state outputs (`*.out` files) — directly comparable to Track 1's `*.out` files (same gridlist, same LU, same auxiliaries; only climate + CO2 source differ)

**Status**: NOT YET RUN (this is the work for after local v1 verification window completes; cluster phase 17c.1+).

### 5.3 Validation triad for the paper's results section

| Comparison | Tools | Purpose | Status |
|---|---|---|---|
| (1) **Anthropogenic emissions plots** | `intermediary_py` Component A plotting scripts (rcmip_substitution + scenarios subdirs) | document the integrated anthropogenic emissions modelling for each SSPx_RCPyy scenario | available; produced by `intermediary_py` itself |
| (2) **IMOGEN-derived atm GHG concentrations vs literature trends** | `scripts/b19_phase4_literature_validate.py` (currently smoke-only; extends to full 1900-2100 for paper) + literature reference values from MacFarling Meure 2006 / Etheridge 1996 / Meinshausen 2017 | document that IMOGEN-engine-derived atm concentrations match historical record + are physically plausible across all 5 SSPs | smoke validated (B19 Phase 4 BALLPARK_PASS); production extension awaits Track 2 runs |
| (3) **IMOGEN-derived climate vs ISIMIP3b climate** | NEW comparison script (post-Track-2-runs deliverable); ISIMIP3b NetCDFs as reference; difference maps + trend comparisons | document the climate-driver fidelity between two driver pipelines | NOT YET STARTED (awaits Track 2 runs) |
| (4) **Track 1 vs Track 2 LPJG ecosystem state output comparison** | NEW comparison script (post-Track-2-runs deliverable); per-output-file (cflux, ngases, ...) correlation + difference maps | document the ecosystem-output sensitivity to climate-driver pipeline (ISIMIP3b vs IMOGEN); all other inputs held constant | NOT YET STARTED (awaits Track 2 runs) |

---

## 6. v1.0 paper publication readiness checklist

### Status as of 2026-05-19 morning (B19+B20 close-out era)

- [x] B19 Phase 4 atmospheric concentrations verified against Law Dome ice core (smoke window 1900-1903; BALLPARK_PASS)
- [x] B20 LPJG-natural fluxes verified against Saunois 2020 + Tian 2020 budgets (full 1900-2100; WITHIN_ENVELOPE_MEAN_WITH_TIME_VARIATION = PASS)
- [x] B19 + B20 v1.0 magnitude validation PASS on smoke configuration
- [ ] Local v1 verification window: B36 (Fortran background-emission audit) + B37 (productive-year-ceiling study) + B39 (CO2_INIT_PPMV per-YEAR1) + B40 (modern-decade N2O hump explanatory study)
- [ ] Production-style configuration of `runs/<SSPx_RCPyy>/main.ins` with updated `_peatland` LU + production parameters (npatch=25, nyear_spinup=500, BLAZE+SimFire, popdens, 4-NetCDF wet/dry NHx+NOy ndep)
- [ ] Test run on local workstation with reduced gridlist (e.g., 100 cells; verify full pipeline works) before cluster scaling
- [ ] Cluster setup at KIT IMK-IFU `owl` (17c.1+ phase)
- [ ] Track 2 production runs (5 SSPx_RCPyy scenarios; 1900-2100; 62892-cell gridlist; `-input imogencfx`)
- [ ] Validation triad (1)+(2)+(3)+(4) execution + paper figures
- [ ] Paper amendments:
  - [ ] Replace "legacy IIASA-backbone via legacy intermediary" with "RCMIP/CMIP6 backbone via intermediary_py" in introduction + methods
  - [ ] Add Track 1 vs Track 2 ecosystem comparison framing in methods
  - [ ] Add B19 + B20 + post-Track-2 validation discussion in results

### Effort estimate (rough)

- Local v1 verification window: ~6-13 h (B36+B37+B39+B40)
- Production-config authoring (B41 follow-through): ~3-5 h
- Local 100-cell test run: ~1-2 h on workstation
- Cluster setup (17c.1): ~1-2 weeks SSH-iterative
- Track 2 production runs (5 scenarios; cluster): ~1-2 weeks compute + iteration
- Validation triad execution + paper figures: ~1 week
- Paper amendments + writing: ongoing in parallel
- **Total estimated calendar time to paper submission**: ~6-10 weeks from this commit

---

## 7. Tight-coupling roadmap (v1.1+; B43 record)

### Why deferred from v1.0 paper publication

Per user 2026-05-18 night + 2026-05-19 morning decision: F-12 architectural fix (resolving the F-10 case-α deadlock to enable LIVE-LPJG-handshake natural-flux flow direct to IMOGEN) is **deferred to v1.1+** for the following reasons:

1. F-12 architectural work is a substantial multi-week effort (per `notes/STEP_17c.md` + `notes/FOLLOWUPS.md` F-10 + F-12 entries)
2. The v1.0 paper publication scientific narrative is fully sound under prescribed mode (validation triad above is methodologically clean + reviewer-defensible)
3. F-12 fix would require additional verification cycles; risks v1.0 paper schedule slippage
4. v1.1+ paper(s) post-v1.0 can showcase tight-coupling as headline new capability + use prescribed-mode v1.0 baseline as methodological reference

### v1.0 architecture (prescribed mode; for paper)

```
intermediary_py
  ├─ Component A: anthropogenic CO2/CH4/N2O via RCMIP/CMIP6 substitution
  └─ Component B: natural CO2/CH4/N2O from post-processed Track 1 LPJG outputs
      │
      ▼ all 4 GHG channels (anthro + natural) flow through the .ins
      │ FILE_SCEN_EMITS / FILE_CH4_N2O_EMITS / FILE_LPJG_FLUX / FILE_LPJG_CH4_N2O_FLUX
      ▼
IMOGEN engine (climate emulator + GHG budget)
  produces: atm CO2/CH4/N2O concentrations + climate (1900-2100)
      │
      ▼ engine output read via the imogencfx input module
      ▼
LPJ-GUESS (-input imogencfx)
  + updated _peatland LU forcing
  + popdens NetCDF + SimFire BLAZE binary
  + 4-NetCDF wet/dry NHx+NOy N-deposition
  produces: ecosystem state outputs (Track 2 — for paper)
      │
      ▼ (LPJG natural-flux feedback to IMOGEN BLOCKED in v1.0 by F-10 case-α deadlock)
      ▼
   (LPJG main loop never relinquishes control; handshake never closes)
```

### v1.1+ architecture (tight-coupling; post-F-12)

```
intermediary_py
  └─ Component A: anthropogenic CO2/CH4/N2O via RCMIP/CMIP6 substitution
     (Component B no longer needed for the coupled run itself; remains a
      pre-condition data product for cross-validation)
      │
      ▼ anthro channels only
      ▼
IMOGEN engine
  ▲                                                  │
  │ LIVE LPJG natural fluxes via                     │
  │ FILE_LPJG_FLUX / FILE_LPJG_CH4_N2O_FLUX          │
  │ (Option C; F-12-fixed)                           │
  │                                                  ▼ atm conc + climate (year N)
  │                                                  │
  │                                                  ▼
  │                                              LPJ-GUESS (-input imogencfx)
  │                                                + updated _peatland LU
  │                                                + popdens + SimFire BLAZE
  │                                                + 4-NetCDF wet/dry NHx+NOy
  │                                                  │
  │                                                  ▼ ecosystem outputs +
  └──────────────────────────────────────────────────┘  LPJG natural fluxes
       (per-year handshake; closed feedback loop)      (year N → year N+1 IMOGEN)
```

### v1.1+ paper publications

Post-v1.0 papers can showcase:
- Tight-coupling vs prescribed-mode comparison (using v1.0 paper as methodological reference)
- Multi-decade closed-loop natural-flux feedback effects
- F-12 architectural fix as headline new capability

This is OUT OF SCOPE for v1.0 paper publication; CAPTURED here for forward continuity.

---

## 8. Cross-references

- `notes/B19.md` — closed-loop verification milestone (B19 Phases 0-5; smoke validation)
- `notes/FOLLOWUPS.md` — full audit-item dashboard (B36, B37, B39, B40, B41, B42, B43 + open Fs F-10, F-12)
- `docs/scientific_framework.md` — coupled-model scientific architecture
- `EXECUTION_PLAN.md` — step-by-step rebuild plan + cluster phase 17c roadmap
- `runs/SSP1-2.6/main.ins` — current smoke-test main.ins
- `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/` — example production-style main.ins (Track 1 cfx mode)
- `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_hist/setup_run.sh` — example production launcher (uses `cfx` inputmethod)
- `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Parts 10g + 10h + 11 — session 5 narrative (B19 Phase 3 ADDENDUM through B19 Phase 5 close-out)
- `_chat_artifacts/CHAT_HANDOFF_2026-05-18_session5_post_b19.md` Part 1 — B20 narrative

---

_End of `notes/PRODUCTION_RUN_CONFIG.md` — initial draft 2026-05-19 morning; iteratively refined as B36/B37/B39/B40 + 17c.1+ outcomes inform the readiness checklist._