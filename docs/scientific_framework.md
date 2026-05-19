# Scientific framework — LandSyMM-IMOGEN coupled model

**Version:** v0.15.0 (created at step 15 of the unified-codebase rebuild,
2026-05-08).

**Purpose:** Document the scientific architecture of the LandSyMM-IMOGEN-LPJG
coupled model framework — what each component does, how they interact, and how
the v1.0 pipeline is structured (including Decision #9's Stage I deferral and
Decision #10's land-use strategy). This is the canonical reference for the
working paper's §2 methods narrative and for anyone seeking to understand the
science behind the codebase.

**Companions:**
- [`docs/build.md`](build.md) — how to build and run the system
- [`docs/v2_roadmap.md`](v2_roadmap.md) — what comes after v1.0 (PLUM embedding;
  proper closed-loop tight coupling)
- `EXECUTION_PLAN.md` Part V — operational rebuild plan
- `paper/README.md` — working paper structure + revision plan

---

## 1. The four components

The framework integrates four scientific components, each of which is itself a
peer-reviewed model in its own right:

| Component | What it computes | Reference | In v1.0 |
|---|---|---|---|
| **LPJ-GUESS 4.1** (LandSyMM fork) | Process-based DGVM: ecosystem C/N cycling, fire, hydrology, crop growth; outputs NEE, wetland CH4, soil/fire N2O; potential crop yields | Smith et al. 2014 *Biogeosciences*; Lindeskog et al. 2013 *ESD*; Olin et al. 2015 *ESD* | `lpjguess/`; native binary |
| **PLUM v2** | Economic land-use optimisation: takes LPJG potential yields + scenario demand → spatiotemporal LU + crop fractions + N-fertiliser + irrigation per country | Alexander et al. 2018 *ESD*; Rabin et al. 2020 *ESD* | **External** (Stage I deferred per Decision #9; existing PLUM-harm forLPJG outputs reused) |
| **The Intermediary Controller** (Python `imogen_ghg_controller`) | IPCC 2019-Refinement Tier-1 methodologies for AFOLU CH4 + N2O emissions from PLUM activity data; substitutes into RCMIP Phase 2 v5.1.0 anthropogenic backbone | IPCC (2019) Vol. 4 (AFOLU); Nicholls et al. 2020 *GMD* (RCMIP) | `intermediary_py/imogen_ghg_controller/`; 43-step pipeline |
| **IMOGEN** | Pattern-scaling climate emulator + Joos ocean uptake + FAIR non-CO2 budget; takes integrated emissions → year-by-year monthly climate forcing | Huntingford et al. 2010 *GMD*; Smith et al. 2018 *GMD* (FAIR) | Fortran `imogen/code/imogen_lpjg.f` (per Decision #2; ALLOCATABLE refactor at step 3) |

Two coupling modes are supported per Decision #4:

- **Tight (closed-loop, conceptual default)**: LPJ-GUESS year N's ecosystem
  fluxes feed back into IMOGEN's year N+1 climate trajectory in real time.
  In v1.0 this mode is **architecturally blocked by the F-10 deadlock** (see
  §5 below); it becomes runnable in v1.1 once F-12 (Option B, two-process
  design) lands. v1.0's functional-default is `prescribed`.
- **Prescribed (v1.0 functional default)**: IMOGEN reads pre-computed static
  natural-flux files (predecessor's IIASA-derived Option A, or step-13 adapter
  outputs as Option B); LPJG-side handshake-writer writes diagnostics but the
  engine does not consume them.
- **Loose**: IMOGEN runs once standalone; LPJG reads pre-baked engine climate
  via `-input imogen`. Legacy compatibility; predecessor's working paper used
  this. Functional end-to-end in v1.0.

---

## 2. The two-stage simulation protocol

Per the working paper §2.4.3 framing:

```
              ┌─────────────────────────────────┐
              │   STAGE I  (yield-generation)   │
              │   LPJG runs with do_potyield 1  │
              │   under prescribed climate;     │
              │   produces yield surfaces       │
              │   per crop × management         │
              └────────────────┬────────────────┘
                               ↓
                ┌──────────────────────────────┐
                │   PLUM v2 (external)         │
                │   takes yields + demand →    │
                │   harmonised LU + crop       │
                │   fractions + N + irrig      │
                └──────────────┬───────────────┘
                               ↓
              ┌─────────────────────────────────┐
              │  STAGE II (Stage-I-conditioned) │
              │  LPJG runs with do_potyield 0   │
              │  consuming PLUM-harm LU; coupled│
              │  to IMOGEN climate emulator;    │
              │  closed-loop NEE feedback       │
              └─────────────────────────────────┘
```

### 2.1 Stage I — potential-yield generation (deferred for v1.0 per Decision #9)

**Inputs to Stage I**:
- ISIMIP3b prescribed climate (1850–2100; MRI-ESM2-0 GCM per working paper
  §2.4.3 — same GCM the IMOGEN CMIP6 patterns target)
- HILDA+ v2 historic land-use 1850–2020 (Winkler et al. 2021)
- LUH2-style 5-year-window harmonisation across the 2020 historic↔scenario
  boundary
- 6 management treatments (rainfed/irrigated × multiple N-fertilisation rates)

**Stage I in code**: when `do_potyield 1` is set in `landcover.ins` (per
`landsymm_runtime_parameters.md §6`), LPJG runs in factorial mode:

- `file_lucrop` and `file_Nfert` are **ignored**
- Only stand types marked `isforpotyield 1` (in `crop_n_stlist*.ins`) participate
- Cropland area is **shared equally among participating stands**
- N rates come from `N_appfert_mt` per stand-type (kg N / m²)
- The `hydrology` enum (`rainfed | irrigated | irrigated_wilt | irrigated_sat |
  inundated`) selects the water-management regime

**Stage I outputs**: per-crop × per-management × per-year potential-yield
surfaces (`yield_st.out`, `gsirrigation_st.out`, etc.). These feed PLUM.

**v1.0 deferral rationale (Decision #9)**:
1. The 6 management treatments and the factorial-mode infrastructure (`do_potyield`,
   `isforpotyield`, `N_appfert_mt`, `hydrology` enum) are **all already present
   in `lpjguess/`** per the user's earlier integration project (see
   `landsymm_runtime_parameters.md §6`).
2. The user has already produced PLUM-harm `forLPJG` outputs at
   `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/` for all 5 SSPs from
   prior Stage-I-then-PLUM runs (see [`data/DATA.md`](../data/DATA.md) §1).
3. Re-running Stage I from scratch would require re-coordinating with the PLUM
   modelling team and re-orchestrating the user's `landsymm_py` post-processing
   pipeline — substantial extra setup not budgeted in v1.0.
4. v1.0 therefore reuses the existing PLUM-harm outputs as Stage II input.

**v2.0 plan**: re-embed Stage I into the unified codebase orchestration (PLUM
becomes a coupled component instead of an external dependency). See
[`v2_roadmap.md`](v2_roadmap.md) §2.

### 2.2 Stage II — Stage-I-conditioned coupled simulation (the v1.0 focus)

LPJG consumes the harmonised land-use forcing produced by Stage I + PLUM, runs
under either `imogencfx` (tight/prescribed; in-process IMOGEN) or `imogen`
(loose; pre-baked IMOGEN climate library) input modules, and produces:

- Standard LPJG outputs: `cflux.out`, `cmass.out`, `anpp.out`, `mch4.out`,
  `ngases.out`, `cpool.out`, `npool.out`, `nflux.out`
- LandSyMM-specific outputs: `cflux_cropland.out`, `anpp_cropland.out`,
  `nflux_cropland.out`, `cpool_cropland.out`, `npool_cropland.out` (and their
  pasture / natural / forest / peatland counterparts where stands are active)
- Per-stand-type variants (`*_st.out`)
- LPJG → IMOGEN handshake files (per step 8 of the rebuild):
  `imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt`, `imogen_lpjg.txt`,
  `done`, written at `<DIR_COMMON>/LPJG_main/IMOGEN/`

In tight mode, IMOGEN consumes those handshake files per year and produces
year-(N+1) monthly climate at `<DIR_COMMON>/IMOGEN/output/<YYYY>/` for LPJG to
read in the next year. **In v1.0 this loop deadlocks at the F-10 boundary**
(see §5).

---

## 3. Stage II land-use forcing for v1.0

Three options exist for sourcing the Stage II LU forcing; the choice is
documented per Decision #10.

### 3.1 Option A — In-process Stage I (the eventual goal; deferred to v2.0)

Run Stage I and PLUM as part of the framework's orchestration; produce
yield → LU dynamically. Requires PLUM embedding. **NOT in v1.0** per
Decision #9.

### 3.2 Option B — PLUM-harm forLPJG outputs (pre-existing; the architecturally cleanest v1.0 / v1.1 path)

Use the existing PLUM-harm `forLPJG` outputs at
`/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/<scenario>/s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/`
(see [`data/DATA.md`](../data/DATA.md) §1).

Each scenario directory (~3.5 GB) contains:

| File | Schema | Year coverage |
|---|---|---|
| `landcover.txt` | `Lon Lat Year PASTURE CROPLAND NATURAL BARREN` | 2021–2100 (scenario only) |
| `cropfractions.txt` | `Lon Lat Year` + 21 crop columns: 10 irrigated (`*i` suffix; `CerealsC3i CerealsC4i Ricei OilNfixi OilOtheri Pulsesi StarchyRootsi FruitAndVegi Sugari Miscanthusi`) + 10 rainfed + `ExtraCrop` | 2021–2100 |
| `irrig.txt` | per-cell-per-year irrigation intensity per crop | 2021–2100 |
| `nfert.txt` | per-cell-per-year N-fertilisation rate per crop | 2021–2100 |
| `landcover_peatland.txt` | per-cell-per-year peatland fraction | 2021–2100 |

**Format note (relative to predecessor's concatenated 1901–2100 files in §3.3
below)**:
- LU column ordering is `PASTURE CROPLAND NATURAL BARREN` (PLUM-harm) vs
  `NATURAL CROPLAND PASTURE BARREN` (predecessor concatenated)
- Crop column count is 21 (PLUM-harm; with OilNfix + OilOther split) vs 19
  (predecessor concatenated; with `Oilcrops` merged)
- Year range is 2021–2100 only (PLUM-harm; scenario phase) vs 1901–2100
  concatenated (predecessor)

**To use Option B end-to-end in v1.0**, the
[Decision #10](#41-decision-10-save_staterestart-for-historic-vs-scenario-lu)
`save_state`/`restart` pattern is the cleanest approach because Option B's LU
files are scenario-only (2021+):

1. **Historic phase**: standalone LPJG run 1850–2020 against HILDA+ v2 historic
   LU (the prefix for `s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/`,
   delivered by the user's `landsymm_py` codebase); save state at year 2020
   (`save_state 1`, `state_year 2020`).
2. **Scenario phase**: restart from 2020 saved state (`restart 1`); run
   2021–2100 against the PLUM-harm scenario LU forcing in coupled mode
   (`-input imogencfx`).

**v1.0 status**: Option B is **available and verified accessible** but **not
yet wired** end-to-end. The current `runs/SSP1-2.6/landcover.ins` uses
Option C (§3.3) for v1.0 simplicity. Wiring Option B is a v1.1 milestone (see
[`v2_roadmap.md`](v2_roadmap.md) §3).

### 3.3 Option C — Legacy concatenated 1901–2100 LU (v1.0 simplification)

Use the predecessor's pre-concatenated LU forcing at
`version_A/.../Data/LU/SSP1_RCP26_concatenated/`:

| File | Schema | Year coverage | Size |
|---|---|---|---|
| `LU_SSP1_RCP26_1901_2100_final.txt` | `Lon Lat Year NATURAL CROPLAND PASTURE BARREN` | 1901–2100 (concatenated) | 676 MB |
| `cropfracs_SSP1_RCP26_1901_2100_final.txt` | `Lon Lat Year` + 19 crop columns (`Oilcrops` merged) | 1901–2100 | 2.37 GB |
| `irrig_SSP1_RCP26_1901_2100_final.txt` | per-cell-per-year irrigation per crop | 1901–2100 | 2.37 GB |
| `nfert_SSP1_RCP26_1901_2100_final.txt` | per-cell-per-year N-fertilisation per crop | 1901–2100 | 2.37 GB |

**Why v1.0 uses Option C** (per user guidance 2026-05-07; recorded in
`notes/STEP_9.md`):
- The LU + crop fraction files are pre-concatenated 1901–2100, so a single
  LPJG run can consume them straight from `firsthistyear=1850` (or
  `firsthistyear=1901` for tighter scope) through `lastoutyear=2100` without
  any save_state/restart machinery.
- Only the SSP1-RCP2.6 scenario was concatenated; the other 4 SSPs were never
  pre-concatenated, which is part of why **save_state/restart (Option D
  through Option B's path) becomes the canonical approach for v1.1+**.
- Option C is fork-agnostic and depends only on `version_A`'s tree existing
  on the workstation (Tier-3; see [`data/DATA.md`](../data/DATA.md) §2).

**v1.0 wiring** in `runs/SSP1-2.6/landcover.ins:17-18` (LU + cropfracs) and
`runs/SSP1-2.6/crop.ins:23,33` (Nfert + irrigintens) — all four point at
`version_A/.../Data/LU/SSP1_RCP26_concatenated/`. The local-machine path is
documented inline; users on other machines must update accordingly.

---

## 4. Decision #10 — `save_state`/`restart` strategy (Option D = Option B over save_state/restart)

For Option B's PLUM-harm forLPJG outputs (which are scenario-only 2021+), the
canonical pattern is to split the simulation into two phases joined by a
state checkpoint at the historic↔scenario boundary year (2020). The integrated
LTS (= our `lpjguess/` base; per Decision #3) already has all required
parameters wired:

### 4.1 Parameters (per `landsymm_runtime_parameters.md §2.1-§2.3`)

| Parameter | Type | Where to set | Description |
|---|---|---|---|
| `restart` | bool | `main.ins` | 0 = fresh run; 1 = start from saved state |
| `save_state` | bool | `main.ins` | 0 = no save; 1 = save at `state_year` |
| `state_path` | str | `main.ins` | Directory for state files |
| `state_year` | int | `main.ins` | Year at which state is saved/restarted |
| `save_year` (alias) | int | `main.ins` | LandSyMM-style alias for `state_year` (save side) |
| `restart_year` (alias) | int | `main.ins` | LandSyMM-style alias for `state_year` (restart side) |
| `save_years` | str | `main.ins` | Space-separated list (currently first year used; multi-year a future enhancement) |

### 4.2 Canonical pattern (verbatim from `owl_hpc_cluster_scripts/`)

**Historic phase** (per `historic_run_with_saving_state_example.ins`):

```ins
restart    0                   ! fresh run
save_state 1                   ! save at state_year
state_path "/path/to/state/dir"
state_year 2020                ! save at year 2020
firsthistyear 1850
lasthistyear  2020
```

**Scenario phase** (per `scenario_restart_from_saved_state_example.ins`):

```ins
restart    1                   ! restart from saved state
save_state 0                   ! don't re-save
state_path "/path/to/state/dir"   ! same dir as historic phase
state_year 2020                ! restart from year 2020 state
firsthistyear 1850
lasthistyear  2100
```

The user's existing `owl_hpc_cluster_scripts/historic_run_with_saving_state_example.ins`
and `scenario_restart_from_saved_state_example.ins` exemplify the pattern for
the forest-productivity `cfx` use case; the same pattern works for our
`imogencfx` coupled mode with the PLUM-harm forLPJG scenario LU as the
2021–2100 forcing.

### 4.3 v1.0 status of save_state/restart

- The parameters and infrastructure exist in `lpjguess/` (no source-level work
  needed)
- The PLUM-harm forLPJG outputs exist on the workstation (no acquisition work
  needed)
- The `imogen_intermediary.ins` file would need a per-phase variant (one for
  historic save, one for scenario restart) — minor `.ins`-file edit
- The launcher `scripts/run_coupled.sh` would need a `--phase historic |
  scenario` flag — bash work
- **All deferred to v1.1**; not blocking v1.0 paper-stage runs (which use
  loose coupling per F-10 caveat — see §5)

---

## 5. The F-10 architectural caveat (v1.0 limitation)

**The most consequential finding of the rebuild project** (empirically
confirmed at step 9 of the rebuild plan; documented at length in
`notes/FOLLOWUPS.md` F-10 + the prior chat handoff Part 7):

`lpjguess/framework/framework.cpp:411-516` implements a **per-gridcell-outer /
per-day-inner-across-all-years loop**. Each gridcell processes ALL its years
before the next gridcell starts. This is **fundamentally incompatible** with
proper per-year-globally-synchronized tight coupling (which IMOGEN's
polling-loop architecture demands).

**In v1.0 single-process `imogencfx` mode, this manifests as a hard deadlock**:
- `imogencfx::init()` calls `RUN_IMOGEN_ENGINE()` inline (the C++ port wrapping
  the Fortran engine).
- Engine runs ~32 years using bootstrap files, then deadlocks polling for
  `LPJG_main/IMOGEN/done`.
- LPJG cannot write `done` because LPJG's main loop hasn't started — `init()`
  is still blocking.
- LPJG main loop NEVER reached; step 8's `ImogenOutput::flush_year` writer
  NEVER fires.

### 5.1 What this means for v1.0 paper-stage runs

The v1.0 deliverable's **scientifically defensible run mode is loose coupling**
(`-input imogen`), in which:
- IMOGEN runs once standalone end-to-end (years 1850–2100) and writes its
  per-year monthly climate library to `<DIR_COMMON>/IMOGEN/output/<YYYY>/`.
- LPJG then runs end-to-end in a separate invocation, reading the pre-baked
  climate from disk.
- This **is not a closed-loop run** in the strict sense — LPJG perturbations do
  not feed back into the IMOGEN climate trajectory — but it is the methodology
  the predecessor's working paper used and is an acceptable v1.0 baseline.

The three v1.0 sub-flows (engine-only, LPJG loose, intermediary_py +
adapter) are independently validated; their integration into a true
closed-loop tight run is a v1.1 milestone (F-12 Option B).

### 5.2 Phase-2 resolution path (per F-12)

- **v1.1 (Phase 2A; ~2-3 days work)**: F-12 Option B — split `imogen_lpjg`
  into a separate concurrent Fortran process; existing file-based handshake
  provides the rendezvous layer.
- **v2.0 (Phase 3; ~1-2 weeks work)**: F-12 Option C — additive runtime
  parameter `framework_loop_mode = "year_outer"` gating an alternative
  per-year-outer loop **alongside** the existing per-gridcell-outer one
  (mirroring the LandSyMM-fork-into-LTS integration pattern; the user's
  preferred long-term approach per F-10's Phase-2 design entry).

See [`v2_roadmap.md`](v2_roadmap.md) §4 + §5.

### 5.3 Natural-flux channel mutual exclusion + the no-double-counting invariant

_Origin: B32 (B19 Phase 5 close-out 2026-05-18 evening; condensed from
`COUPLED_MODEL_INVESTIGATION.md` §2.3 + §3.7; rediscovered as a key
architectural quirk during user-driven double-counting investigation at
B19 Phase 1 CLOSE 2026-05-16 evening per `notes/B19.md` §3.4.2)._

The IMOGEN engine integrates four anthropogenic + natural emission channels
into the atmospheric CO2 / CH4 / N2O budget, controlled by four
`<runs/<SCEN>/imogen_intermediary.ins>` parameters:

| Channel | `.ins` parameter | What it carries |
|---|---|---|
| Natural CO2 (LPJG-side) | `FILE_LPJG_FLUX` | LPJG-derived natural ecosystem CO2 flux (NEE; positive = source) |
| Natural CH4 + N2O (LPJG-side) | `FILE_LPJG_CH4_N2O_FLUX` | LPJG-derived natural CH4 (wetland + fire) + N2O (soil + fire) |
| Anthropogenic CO2 | `FILE_SCEN_EMITS` | Scenario fossil + LULUC CO2 emissions |
| Anthropogenic CH4 + N2O | `FILE_CH4_N2O_EMITS` | Scenario CH4 + N2O emissions (industry, agriculture, etc.) |

The two **natural** channels (`FILE_LPJG_FLUX` + `FILE_LPJG_CH4_N2O_FLUX`)
each have **three mutually-exclusive resolution options**:

- **Option A** — static CMIP6 reference (`imogen/emiss/CMIP6/Co2/co2_pg_emissions_natural_historical_ssp<XXX>_1850_2100.txt` etc.; the predecessor's pre-existing IIASA-derived files; v1.0 default).
- **Option B** — `intermediary_py`-derived adapter outputs (`runs/<SCEN>/inputs/imogen_lpjg_flux.txt` etc.; from the step-13 adapter applied to `intermediary_py`'s `imogen_inputs_<SCEN>.csv`; introduced at step 13 of the unified-codebase rebuild).
- **Option C** — relative bare-filename (`imogen_lpjg_flux.txt` etc.; the engine's POSIX path-concat resolves these to `<DIR_COMMON>/LPJG_main/IMOGEN/<filename>` where step-8's `ImogenOutput::flush_year` writes the per-year LIVE LPJG handshake; the F-10 deadlock applies here).

The two **anthropogenic** channels (`FILE_SCEN_EMITS` + `FILE_CH4_N2O_EMITS`)
each have **two mutually-exclusive options**:

- **Option A** — `imogen/emiss/DKB_dataset_totals/co2_emissions_annual_historical_<scen>_non_lpjg.txt` etc. (pre-existing scenario files).
- **Option B** — `runs/<SCEN>/inputs/co2_anthro_emissions.txt` etc. (`intermediary_py`-derived adapter outputs).

#### The mutual-exclusion invariant

For each natural channel, **exactly ONE of {A, B, C} must be active** in the
`.ins` file at any given time. For each anthropogenic channel, **exactly ONE
of {A, B} must be active**. Activating two options simultaneously would
result in **double-counting**: both options' fluxes would feed into the engine
budget, doubling (or worse) the natural / anthropogenic contribution to the
atmospheric budget for that year.

Since v0.18 (B31 launcher auto-rewrite at `scripts/run_coupled.sh` step 4.5;
landed at commit `d7a0673` 2026-05-16/17), the launcher enforces this
invariant deterministically per `(--coupling-mode, --backbone)` flag tuple
via content-keyed sed toggles + a post-rewrite verification loop that aborts
if any of the four `FILE_*` parameters has anything other than exactly 1
active line. The `(--coupling-mode, --backbone) → Options` mapping:

| `--coupling-mode` | `--backbone` | NATURAL Option | ANTHRO Option |
|---|---|---|---|
| prescribed | static-iiasa | A | A |
| prescribed | intermediary-py | B | B |
| tight | static-iiasa | C | A |
| tight | intermediary-py | C | B |
| loose | * | (skipped; loose mode bypasses LPJG handshake entirely) | (skipped) |

#### Why "Option A and Option B at once" is forbidden by science

Option A (CMIP6 static reference) and Option B (`intermediary_py` adapter)
each represent **the same physical quantity** (natural ecosystem CO2 / CH4 /
N2O flux for SSP1-2.6 etc.) computed from different upstream sources +
different methodologies. They are **alternatives**, not contributions. If
both flow into the engine, the natural CO2 sink would count twice (or, more
precisely, would sum two correlated-but-not-identical estimates); the
atmospheric CO2 trajectory would diverge from physical reality by ~5-10 ppm
per year of double-counted sink.

#### Why "Option B and Option C at once" is forbidden by architecture

Option C (LIVE LPJG handshake) and Option B (intermediary_py-derived static
reference) both describe LPJG-natural-flux contributions. Option C is the
**real-time-computed-by-LPJG-this-run** value; Option B is the
**pre-computed-from-an-earlier-LPJG-run-via-intermediary_py** value. In a
properly-functioning closed-loop run (post-F-12 v1.1+), these would reflect
the same simulation; activating both would double-count this run's LPJG
contribution.

#### `intermediary_py`'s anthropogenic-only invariant

A frequently-encountered side-question (raised by user at B19 Phase 1 CLOSE
investigation; resolved NEGATIVE per `notes/B19.md` §3.4.2.2): does
`intermediary_py` itself produce a "natural CH4 emissions" file that gets
used in our coupled run? **No.** `intermediary_py` produces TWO outputs that
feed IMOGEN:
- `runs/<SCEN>/inputs/{co2_anthro_emissions, ch4_n2o_anthro_emissions}.txt` →
  Anthropogenic Option B (intentional; this is the integrated anthropogenic
  channel `intermediary_py` was designed to produce per the IPCC 2019 Tier-1
  AFOLU-substituted-into-RCMIP-Phase-2 methodology).
- `runs/<SCEN>/inputs/{imogen_lpjg_flux, imogen_lpjg_ch4_n2o_flux}.txt` →
  Natural Option B (NOT a separate "natural CH4 from intermediary_py";
  these are derived from LPJ-GUESS reference outputs applied through the
  step-13 adapter, NOT from `intermediary_py`'s anthropogenic computation).

The architecture enforces no-double-counting at the `.ins` layer (mutual
exclusion above) AND no-naming-collision at the channel layer (anthro vs
natural file names are distinct + their `.ins` parameter names are distinct).

#### Forensic backstory + cross-references

The mutual-exclusion invariant was originally documented as a footnote in
the predecessor's design notes; lost during the rebuild's step 8 + step 9
.ins refactoring; rediscovered as a documentation gap during the B19 Phase
1 CLOSE user-driven double-counting investigation (2026-05-16 evening) +
filed as audit item B32. Lands here at B19 Phase 5 close-out per the
deferred-to-Phase-5 schedule.

The architectural footgun related to this invariant — the
"loose-masquerading-as-tight" POSIX path-concat collapse that silently
breaks Option C → Option A reduction when `FILE_LPJG_FLUX` starts with `/` —
is documented at `COUPLED_MODEL_INVESTIGATION.md` §3.7 + addressed in 3
defense-in-depth layers wired in at B19 Phase 2 (B33 audit item; commits
`d7a0673` / `53e19f5` / `6862d03`): launcher auto-rewrite + launcher
pre-flight abort + Fortran defensive `WARN_POSIX_CONCAT_COLLAPSE` runtime
print.

Cross-references:
- `notes/B19.md` §3.4.2 (B19 Phase 1 CLOSE side-investigation full record)
- `COUPLED_MODEL_INVESTIGATION.md` §2.3 (canonical mutual-exclusion forensic) + §3.7 (POSIX-concat collapse footgun forensic)
- `runs/SSP1-2.6/imogen_intermediary.ins` lines 156-242 (3-Option block + maintainer-critical inline comment harden by B33(a) at commit `53e19f5`)
- `scripts/run_coupled.sh` step 4.5 (the launcher auto-rewrite implementing the matrix above)

---

## 6. Units integrity (Decision #6)

Every emission, flux, and atmospheric concentration variable carries
documented canonical units. See `EXECUTION_PLAN.md` §I.D for the discipline;
key conversions reproduced here for reference:

| Conversion | Constant | Source |
|---|---|---|
| GtC → ppmv | 0.471 ppmv/GtC (= `CONV` in `imogen_lpjg.f:116`) | Atmospheric carbon sensitivity |
| MtCO2 → PgC | divide by 3666.6667 (= 44/12 × 1000) | Molar mass ratio CO2:C × Mt:Pg |
| Mt-of-gas ↔ Tg-of-gas | identity (Mt = Tg = 10¹² g) | SI definition |
| g(CH4-C) → g(CH4) | × 16/12 | Molar mass ratio MM_CH4 / MM_C |
| kgN → kgN2O | × 44/28 | Molar mass ratio MM_N2O / (2 × MM_N) |

NEE sign convention: **positive = source to atmosphere** (per
`commonoutput.cpp::outannual` lines ~1240-1270; mirrored in
`imogenoutput.cpp::flush_year`).

Year indexing: **LPJG year-N flux drives IMOGEN year-(N+1) climate**
(`imogen_lpjg.f:802`: `IF (YR_LPJG(N).EQ.IYEAR-1) THEN ...`).

### 6.1 Per-YEAR1 atmospheric-concentration seed table (B39 close-out 2026-05-19 session 7)

_Origin: B39 (CO2_INIT_PPMV per-YEAR1 configurability fix; option α). Empirical attribution at B19 Phase 4 BALLPARK_PASS commit `82a1bc8`: Run C 1900-1903 showed uniform CO2 negative bias of -3.47% (1900) → -4.18% (1903) vs Law Dome MacFarling Meure 2006 — fully attributable to `CO2_INIT_PPMV 286.085` being a 1850s/1860s-era value used as the engine's iteration-1 seed for the 1900-start sim. Same pattern at smaller magnitude for `CH4_INIT_PPBV 865.0` (~10 ppb below Law Dome 1900 875.6; explains -0.5 to -0.7% CH4 drift)._

The IMOGEN engine seeds its iteration-1 atmospheric concentrations from 3 `.ins` parameters declared in `runs/<SCEN>/imogen_intermediary.ins`:

- `CO2_INIT_PPMV` — atm CO2 in ppm at year YEAR1
- `CH4_INIT_PPBV` — atm CH4 in ppb at year YEAR1
- `N2O_INIT_PPBV` — atm N2O in ppb at year YEAR1

**These values MUST be set to historically-accurate concentrations for the specific YEAR1 of the run** (per option α; the engine source treats them as the iteration-1 seed and propagates forward via the FAIR non-CO2 + Joos ocean modules + the per-iter flux integrations). For any YEAR1 != the seed-table entries below, consult the cited Law Dome MacFarling Meure 2006 NOAA archive spline-fit data + Meinshausen 2017 CMIP6 historical concentration timeseries for the appropriate values.

#### Cross-reference table — common YEAR1 baseline values

| YEAR1 | `CO2_INIT_PPMV` | `CH4_INIT_PPBV` | `N2O_INIT_PPBV` | Source + notes |
|---|---|---|---|---|
| **1850** | **284.3** | **815** | **273.0** | Meinshausen 2017 CMIP6 historical pre-industrial baseline; also Law Dome MacFarling Meure 2006 spline-fit start-of-series |
| **1900** | **296.1** | **875.6** | **277.2** | Law Dome MacFarling Meure 2006 NOAA archive spline-fit; matches `scripts/b19_phase4_literature_validate.py:74` reference for year 1900; **this is the v1.0 paper-publication default (YEAR1=1900 per main `runs/SSP1-2.6/imogen_intermediary.ins`)** |
| **2005** | **379.0** | **1774** | **319.0** | Mauna Loa / NOAA GAGE observational era (mid-2000s baseline); useful for 2005-start scenario runs (e.g., SSP-RCP scenario phase starts) |

**Maintenance directive**: when configuring a new `imogen_intermediary.ins` for any YEAR1 not in the table above, EITHER (a) extend this table with the new YEAR1 epoch row + citation, OR (b) interpolate the 3 *_INIT_* values between the nearest tabulated epochs using the source data (Law Dome MacFarling Meure 2006 NOAA archive for pre-1958; Mauna Loa / NOAA observational record for 1958-present). The v1.0 production-IMOGEN-engine runs use YEAR1=1900 per `notes/PRODUCTION_RUN_CONFIG.md` §2.1 + the main `runs/SSP1-2.6/imogen_intermediary.ins`.

**Empirical validation acceptance**: post-B39 (this commit), re-running `scripts/b19_phase4_literature_validate.py` against the smoke window (1900-1903) is expected to show CO2 drift drop from -3.5 to -4.2% (B19 Phase 4 pre-fix) → near 0% (STRICT_PASS); CH4 drift drop from -0.5 to -0.7% → near 0%; N2O drift unchanged (N2O_INIT_PPBV unchanged at 277.4, within 0.07% of Law Dome 1900 277.2).

**Cross-references**:
- `notes/B39.md` (B39 canonical landing record; full source-reading + acceptance-test result)
- `notes/B19.md` §6.4.1 attribution #1 (original empirical observation of the CO2 negative bias)
- `runs/SSP1-2.6/imogen_intermediary.ins` lines 266-268 (the 3 `*_INIT_*` parameter site with inline maintenance directive)
- `notes/PRODUCTION_RUN_CONFIG.md` §2.1 (smoke→production parameter delta; references this §6.1 table)
- `_chat_artifacts/CHAT_HANDOFF_2026-05-18_session5_post_b19.md` Part 5 (B39 session-7 evening close-out narrative)

---

## 7. References

- Alexander, P., Rabin, S., Anthoni, P., Henry, R., Pugh, T.A.M., Rounsevell,
  M.D.A. & Arneth, A. (2018). Adaptation of global land-use scenarios for
  crop simulation: an agroeconomic protocol. *Earth System Dynamics* **9**,
  1349–1369.
  [doi:10.5194/esd-9-1349-2018](https://doi.org/10.5194/esd-9-1349-2018)
- Huntingford, C., Booth, B.B.B., Sitch, S., et al. (2010). IMOGEN: an
  intermediate complexity model to evaluate terrestrial impacts of a changing
  climate. *Geoscientific Model Development* **3**, 679–687.
  [doi:10.5194/gmd-3-679-2010](https://doi.org/10.5194/gmd-3-679-2010)
- IPCC (2019). 2019 Refinement to the 2006 IPCC Guidelines for National
  Greenhouse Gas Inventories, Volume 4 (AFOLU). Calvo Buendia, E. et al. (eds).
- Lindeskog, M., Arneth, A., Bondeau, A., et al. (2013). Implications of
  accounting for land use in simulations of ecosystem carbon cycling in
  Africa. *Earth System Dynamics* **4**, 385–407.
- Nicholls, Z.R.J., Meinshausen, M., Lewis, J., et al. (2020). Reduced
  Complexity Model Intercomparison Project Phase 1: Introduction and
  evaluation of global-mean temperature response. *Geoscientific Model
  Development* **13**, 5175–5190.
- Olin, S., Schurgers, G., Lindeskog, M., et al. (2015). Modelling the
  response of yields and tissue C:N to changes in atmospheric CO₂ and N
  management in the main wheat regions of western Europe. *Earth System
  Dynamics* **6**, 745–768.
- Rabin, S.S., Alexander, P., Henry, R., Anthoni, P., Pugh, T.A.M.,
  Rounsevell, M. & Arneth, A. (2020). Impacts of future agricultural change
  on ecosystem service indicators. *Earth System Dynamics* **11**, 357–376.
- Smith, B., Wårlind, D., Arneth, A., Hickler, T., Leadley, P., Siltberg, J.
  & Zaehle, S. (2014). Implications of incorporating N cycling and N
  limitations on primary production in an individual-based dynamic vegetation
  model. *Biogeosciences* **11**, 2027–2054.
- Smith, C.J., Forster, P.M., Allen, M., et al. (2018). FAIR v1.3: a simple
  emissions-based impulse response and carbon cycle model. *Geoscientific
  Model Development* **11**, 2273–2297.
- Winkler, K., Fuchs, R., Rounsevell, M. & Herold, M. (2021). Global land
  use changes are four times greater than previously estimated. *Nature
  Communications* **12**, 2501.
  [doi:10.1038/s41467-021-22702-2](https://doi.org/10.1038/s41467-021-22702-2)

— Generated at step 15 (2026-05-08) of the unified-codebase rebuild.
