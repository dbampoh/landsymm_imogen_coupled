# STEP 15 — Stage I documentation preservation + Stage II PLUM-output reuse verification

**Date completed:** 2026-05-08
**Commit:** _to be filled in after `git commit`_
**Status:** ✅ **DONE.** Documentation-only step per Decision #9; verified existing PLUM-harm `forLPJG` outputs at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/` are accessible and inventoried; Stage I + Stage II + Decision #10 save_state/restart pattern fully documented in two new `docs/` files; all 5 anchoring documents updated; bundled BACKPORT_LEDGER §3 errata cleanup (15 verified commit hashes replacing 5 stale + 9 TBD entries). Net `lpjguess/` source-level change: ZERO.

---

## 1. Goal (per `EXECUTION_PLAN.md` V.1 step 15)

> **Stage I documentation preservation (NOT execution).** Per Decision #9,
> Stage I yield-generation is deferred for v1.0 (we use the already-produced
> PLUM outputs from the user's prior work). `do_potyield` is confirmed
> present in `trunk_r13078`; no merge from integrated LTS needed. This step
> reduces to: (a) document Stage I in `docs/scientific_framework.md` per
> working paper §2.4.3 framing; (b) verify that the existing PLUM outputs
> are usable as-is for the v1.0 Stage II coupled run; (c) preserve the v2.0
> plan in `docs/v2_roadmap.md` for the eventual PLUM embedding.

(Plus a small bundled errata cleanup of `notes/TRUNK_R13078_BACKPORT_LEDGER.md`
§3 per the prior chat handoff Part 11 §82.3's flagged "30-minute
documentation-only fix" maintenance follow-up.)

---

## 2. Investigation findings

### 2.1 PLUM-harm `forLPJG` outputs are accessible (item 15.b verification)

External mount points referenced in [`data/DATA.md`](../data/DATA.md) §1
verified live during this step:

```
/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/    ← canonical path
├── SSP1_RCP26/    17 GB
├── SSP2_RCP45/
├── SSP3_RCP70/
├── SSP4_RCP60/
└── SSP5_RCP85/

/media/bampoh-d/ISIMIP/inputs/landuse/plum_harm_lu/  ← redundant copy on different drive
└── (same 5-SSP layout)
```

Each scenario directory contains 4 sub-directories. The one consumed by LPJG is
`s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/` (~3.5 GB
per scenario). Verbatim contents for SSP1_RCP26:

```text
1 044 694 499 bytes  cropfractions.txt
1 044 694 499 bytes  irrig.txt
  275 238 969 bytes  landcover.txt
  315 471 734 bytes  landcover_peatland.txt
1 044 694 499 bytes  nfert.txt
```

### 2.2 Format of PLUM-harm vs predecessor concatenated LU (the schema delta)

**PLUM-harm forLPJG outputs (the v1.1+ canonical Option B / Option D source)**:

```
$ head -2 .../SSP1_RCP26/.../forLPJG/landcover.txt
Lon   Lat   Year  PASTURE CROPLAND NATURAL BARREN
-179.75 65.75 2021 0.111353 0.000001 0.411637 0.477010

$ head -2 .../SSP1_RCP26/.../forLPJG/cropfractions.txt
Lon  Lat  Year  CerealsC3i CerealsC4i Ricei OilNfixi OilOtheri Pulsesi StarchyRootsi FruitAndVegi Sugari Miscanthusi CerealsC3 CerealsC4 Rice OilNfix OilOther Pulses StarchyRoots FruitAndVeg Sugar ExtraCrop Miscanthus
-179.75 65.75 2021 0.090909 0.090909 0.090909 0.090909 0.090909 ... 0.090909 0.000000 0.000000 ... 0.000000 0.090909 0.000000
```

- Year coverage: **2021–2100 only** (scenario phase; historic phase implied
  by HILDA+ v2 prefix from same directory)
- Land-cover columns: `PASTURE CROPLAND NATURAL BARREN`
- Crop columns: 21 (10 irrigated `*i` + 10 rainfed + `ExtraCrop`)
  - Includes `OilNfix` / `OilOther` split (vs predecessor's merged `Oilcrops`)

**Predecessor's concatenated 1901-2100 LU (the v1.0 simplification source;
Option C)**:

```
$ head -2 version_A/.../Data/LU/SSP1_RCP26_concatenated/LU_SSP1_RCP26_1901_2100_final.txt
Lon Lat Year NATURAL CROPLAND PASTURE BARREN
-179.75 65.75 1901 0.427431 0.000000 0.132850 0.439719

$ head -2 version_A/.../Data/LU/SSP1_RCP26_concatenated/cropfracs_SSP1_RCP26_1901_2100_final.txt
Lon Lat Year CerealsC3 CerealsC4 Rice Oilcrops Pulses StarchyRoots FruitAndVeg Sugar CerealsC3i CerealsC4i Ricei Oilcropsi Pulsesi StarchyRootsi FruitAndVegi Sugari ExtraCrop Miscanthus Miscanthusi
-179.75 65.75 1901 0.005192 0.001543 0.000239 0.002068 0.000873 0.000372 0.635759 0.000089 0.000302 0.002053 0.000268 0.000031 0.000033 0.021767 0.103444 0.000133 0.225833 0.000000 0.000000
```

- Year coverage: **1901–2100 (concatenated)**
- Land-cover columns: `NATURAL CROPLAND PASTURE BARREN`
- Crop columns: 19 (8 rainfed + 8 irrigated + `ExtraCrop`/`Miscanthus`/`Miscanthusi`)
  - Single `Oilcrops`/`Oilcropsi` (merged)

**Implication**: PLUM-harm forLPJG and predecessor concatenated LU are **NOT
drop-in interchangeable**. Switching from Option C (current v1.0) to Option B
(PLUM-harm) requires:
1. Either a format-conversion step (column reorder + crop column merge/split)
2. Or, more architecturally cleanly, the `save_state`/`restart` pattern
   (Decision #10 Option D) where historic and scenario phases are separate
   LPJG runs joined by a state checkpoint at year 2020. The PLUM-harm
   outputs being scenario-only (2021+) makes this the natural choice.

### 2.3 `lpjguess/` already has all required save_state/restart parameters

Per `lpjg_landsymm_integration/landsymm_runtime_parameters.md §2.1-§2.3`:

| Parameter | LandSyMM alias | Where | Purpose |
|---|---|---|---|
| `state_year` | `save_year`, `restart_year`, `save_years` (first year) | `main.ins` | Year at which state is saved/restarted |
| `restart` | — | `main.ins` | 0 = fresh; 1 = start from saved state |
| `save_state` | — | `main.ins` | 0 = no save; 1 = save at `state_year` |
| `state_path` | — | `main.ins` | Directory for state files |

These are already wired in our `lpjguess/` (= LandSyMM_LPJ-GUESS = "integrated
LTS"; per Decision #3). **Decision #10 Option D therefore requires NO
source-level work**; only `.ins` files + launcher updates (deferred to v1.1
per [`docs/v2_roadmap.md`](../docs/v2_roadmap.md) §3).

### 2.4 Decision #9's Stage I parameters also already wired

Per `landsymm_runtime_parameters.md §6.1-§6.3`:

| Parameter | Value | Location | Behaviour |
|---|---|---|---|
| `do_potyield` | `0` (production) / `1` (factorial Stage I) | `landcover.ins` | Currently `0` in `runs/SSP1-2.6/landcover.ins:20` ✓ matches Decision #9 |
| `isforpotyield` | bool per stand-type | `crop_n_stlist*.ins` | Marks Stage I participating stands |
| `N_appfert_mt` | kg N/m² per stand-type | `crop_n_stlist*.ins` | Per-treatment N rate (priority chain: file > stand > PFT) |

**Conclusion**: Stage I infrastructure is **fully present in v1.0 source code**
even though Stage I is **deferred for v1.0 execution**. v2.0 PLUM-embedding
only needs orchestration work (PLUM team coordination + landsymm_py
integration), not LPJG source changes.

### 2.5 Stage I + Decision #10 example .ins files exist

User's `owl_hpc_cluster_scripts/` toolkit (per the prior chat handoff
Part 12 §85.4) contains two canonical example `.ins` files demonstrating the
save_state/restart pattern:

- `historic_run_with_saving_state_example.ins`:
  ```
  restart 0
  save_state 1
  state_path "/bg/data/lpj/bampoh-d/forest_productivity_runs/.../historical/BD_10"
  state_year 1365
  ```
- `scenario_restart_from_saved_state_example.ins`:
  ```
  restart 1
  save_state 0
  state_path "/bg/data/lpj/bampoh-d/forest_productivity_runs/.../historical/BD_10"
  state_year 1365
  lasthistyear 2100
  ```

These are `cfx`-mode forest-productivity examples; the same parameter pattern
works for `imogencfx`-mode coupled runs. Wiring up `imogen_intermediary.ins`
variants for a PLUM-harm forLPJG run is mechanical .ins editing (deferred to
v1.1 per [`docs/v2_roadmap.md`](../docs/v2_roadmap.md) §3.2).

### 2.6 BACKPORT_LEDGER §3 commit-hash errata (the bundled cleanup)

Per the prior chat handoff Part 11 §69.1 + §82.3, the BACKPORT_LEDGER §3
section had **stale step-1-5 hashes** and **`_TBD_` placeholders for steps
9-14**. Verified live via `git rev-list -n 1 <tag>`:

| Step | Stale hash in ledger | Verified hash | Tag |
|---|---|---|---|
| 1 | `dc91efb` | **`662f288`** | (bundled into `v0.2.0-imports`) |
| 2 | `9e51a23` | **`a93c3ec`** | `v0.2.0-imports` |
| 3 | `5f86bb1` | **`fb626c4`** | `v0.3.0-fortran-allocatable` |
| 4 | `f3bb471` | **`e80317b`** | `v0.4.0-imogen-data-fetch-script` |
| 5 | `2d36c8e` | **`514f089`** | `v0.5.0-cmip6-converter` |
| 6 | `3ef66de` | `3ef66de` ✓ | `v0.6.0-data-import` |
| 7 | `71c171d` | `71c171d` ✓ | `v0.7.0-coupling-fixes` |
| 8 | `a543e9d` | `a543e9d` ✓ | `v0.8.0-imogenoutput` |
| 8.1 | (n/a; docs) | `1cfb280` | `v0.8.1-backport-ledger` |
| 9 | `_TBD_` | **`d6f4853`** | `v0.9.0-step9-smoke` |
| 9.5 | `_TBD_` | **`f00033c`** | `v0.10.0-step9.5-consumer-wiring` |
| 10 | `_TBD_` | **`a90e9be`** | `v0.11.0-step10-intermediary-py-import` |
| 11 | `_TBD_` | **`e89af1e`** | `v0.12.0-step11-intermediary-py-validated` |
| 13 | `_TBD_` | **`aa802e0`** | `v0.13.0-step13-adapter` |
| 14 | `_TBD_` | **`ced4b1d`** | `v0.14.0-step14-launcher` |

All 14 ledger entries' commit-hash fields are updated in this step.

---

## 3. What was implemented

### 3.1 `docs/scientific_framework.md` (NEW; ~13 KB)

The canonical scientific-architecture reference for the framework. 7
sections:

1. The four components (LPJ-GUESS, PLUM, Intermediary Controller, IMOGEN)
2. The two-stage simulation protocol (Stage I + Stage II per working paper §2.4.3)
3. Stage II land-use forcing options (Option A, B, C with format details)
4. Decision #10 — save_state/restart strategy with verbatim examples
5. The F-10 architectural caveat + v1.0 limitation
6. Units integrity (Decision #6) summary
7. References (10 peer-reviewed citations including Alexander 2018, Rabin 2020,
   Smith 2014, Huntingford 2010, Smith 2018, Nicholls 2020, IPCC 2019,
   Winkler 2021, Lindeskog 2013, Olin 2015)

### 3.2 `docs/v2_roadmap.md` (NEW; ~13 KB)

The post-v1.0 development trajectory. 7 sections:

1. Phase 1 vs Phase 2 trajectory (v1.0 → v1.1 → v1.2 → v2.0 sequence)
2. PLUM embedding (Stage I in v2.0; the Decision #9 v2.0 flip)
3. v1.1 — wire save_state/restart with PLUM-harm forLPJG outputs (the
   ~0.5-1 day deliverable that follows v1.0 release)
4. F-12 Option B (v1.1 Phase 2A) — two-process tight coupling
5. F-12 Option C (v2.0 Phase 3) — in-process restructure with
   `framework_loop_mode` (the user's preferred long-term approach)
6. Other post-v1.0 stretch items (F-1, F-3, F-9, F-11, F-13)
7. v2.0 release criteria

### 3.3 `notes/TRUNK_R13078_BACKPORT_LEDGER.md` errata cleanup

§3 entries' "Commit:" fields updated:
- Step 1: `dc91efb` → `662f288`
- Step 2: `9e51a23` → `a93c3ec`
- Step 3: `5f86bb1` → `fb626c4`
- Step 4: `f3bb471` → `e80317b`
- Step 5: `2d36c8e` → `514f089`
- Step 6: unchanged (`3ef66de` ✓)
- Step 7: unchanged (`71c171d` ✓)
- Step 8: unchanged (`a543e9d` ✓)
- Step 9: `_TBD_` → `d6f4853`
- Step 9.5: `_TBD_` → `f00033c`
- Step 10: `_TBD_` → `a90e9be`
- Step 11: `_TBD_` → `e89af1e`
- Step 13: `_TBD_` → `aa802e0`
- Step 14: `_TBD_` → `ced4b1d`

Plus a NEW step-15 row in §3 (annotation only; documentation-only step;
zero `lpjguess/` source change; backport-irrelevant).

### 3.4 `notes/STEP_15.md` (NEW; this file)

Per-step verification record per the standard discipline.

### 3.5 `CHANGELOG.md` updated

New `[v0.15.0-step15-stage1-deferral]` entry following the Keep-a-Changelog
format established at steps 0–14.

### 3.6 `EXECUTION_PLAN.md` V.1 step 15 row marked DONE

Following the same DONE-row pattern as steps 0–14.

### 3.7 `notes/FOLLOWUPS.md` status dashboard refreshed

"Last updated" date bumped to 2026-05-08; F-1 to F-13 statuses unchanged
(no follow-ups raised or closed at step 15; pure documentation step).

---

## 4. Verification

### 4.1 No source-level change

Step 15 deliberately introduces ZERO `lpjguess/` C++ changes, ZERO
`imogen/code/` Fortran changes, ZERO `intermediary_py/` Python changes,
ZERO `tools/` script changes, ZERO `runs/SSP1-2.6/` changes.

Build state unchanged from step 14:
- `lpjguess/build/guess`: 2 939 136 bytes (May 7; unchanged)
- `lpjguess/build/runtests`: 3 523 216 bytes (May 7; unchanged); 162/162
  assertions pass
- `imogen/code/imogen_lpjg`: 129 600 bytes (May 6; unchanged)

Re-running `runtests` is unnecessary at step 15 (no source-level change to
test); the build state from step 14's empirical-capture exercise (per the
prior chat handoff Part 13 §90.2) remains valid.

### 4.2 Documentation cross-reference integrity

- [`docs/scientific_framework.md`](../docs/scientific_framework.md) cross-references
  - `docs/build.md` ✓
  - `docs/v2_roadmap.md` ✓
  - `EXECUTION_PLAN.md` ✓
  - `paper/README.md` ✓
  - `data/DATA.md` ✓
- [`docs/v2_roadmap.md`](../docs/v2_roadmap.md) cross-references
  - `docs/scientific_framework.md` ✓
  - `notes/FOLLOWUPS.md` ✓
  - `EXECUTION_PLAN.md` ✓
  - `data/DATA.md` ✓
- `notes/STEP_15.md` (this file) cross-references
  - `data/DATA.md` ✓
  - `docs/scientific_framework.md` ✓
  - `docs/v2_roadmap.md` ✓

### 4.3 PLUM-harm forLPJG inventory verified live

7 distinct paths verified accessible (5 SSP scenarios × 2 mount points,
plus 2 forLPJG sub-trees per scenario; total ~85 GB on `/media/bampoh-d/`):

```
/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/
  SSP1_RCP26/   17 GB  ✓ (verified contents per §2.1)
  SSP2_RCP45/         ✓
  SSP3_RCP70/         ✓
  SSP4_RCP60/         ✓
  SSP5_RCP85/         ✓

/media/bampoh-d/ISIMIP/inputs/landuse/plum_harm_lu/
  (5 SSPs; redundant copy on second drive)         ✓
```

The format delta vs predecessor's concatenated 1901-2100 LU is documented in
[`docs/scientific_framework.md`](../docs/scientific_framework.md) §3 and
this STEP note §2.2. Wiring Option B end-to-end is a v1.1 deliverable per
[`docs/v2_roadmap.md`](../docs/v2_roadmap.md) §3.

---

## 5. Backport Sprint relevance (F-11)

**Net source-level change in `lpjguess/`: ZERO** — backport-irrelevant.

The two new docs (`docs/scientific_framework.md`, `docs/v2_roadmap.md`) +
this STEP_15.md + the BACKPORT_LEDGER errata cleanup live entirely OUTSIDE
`lpjguess/`. The Backport Sprint does NOT need to replicate any step-15
deliverable in `trunk_r13078` — these are framework-wide documentation
artefacts.

---

## 6. Cross-reference for follow-ups

### Triggers (none)
None. Step 15 was pure documentation + verification; nothing surfaced that
opens a new follow-up.

### Closed by step 15
- **Part 11 §82.3 maintenance follow-up** (BACKPORT_LEDGER stale hashes).
  All 14 hashes verified + corrected.

### Anticipated by step 15 docs (already-tracked follow-ups)
- F-10 (architectural deadlock; documented in
  [`docs/scientific_framework.md`](../docs/scientific_framework.md) §5;
  resolution in [`docs/v2_roadmap.md`](../docs/v2_roadmap.md) §4)
- F-11 (Backport Sprint; not affected by step 15 since net source change is
  zero)
- F-12 (multi-pass / two-process; v1.1 path documented in
  [`docs/v2_roadmap.md`](../docs/v2_roadmap.md) §4)
- v1.1 PLUM-harm save_state wiring (NEW DEFERRAL DOCUMENTED at
  [`docs/v2_roadmap.md`](../docs/v2_roadmap.md) §3; not a new F-N because
  it sequences after F-12 as part of the v1.1 milestone)

---

## 7. Effort

- Investigation phase: ~1.5 hours (read 14-part chat handoff in full; verify
  external mounts; read 9 inputs in parallel; verify commit hashes)
- Documentation phase: ~2 hours (write 3 NEW files: scientific_framework.md
  + v2_roadmap.md + STEP_15.md; update 4 existing: BACKPORT_LEDGER, CHANGELOG,
  EXECUTION_PLAN, FOLLOWUPS)
- Cross-reference + verification phase: ~30 min
- Commit/push command preparation: ~15 min
- **Total: ~4-4.5 hours** (vs ~5 h estimate; under budget)

---

**Step 15 complete.** Tag target: `v0.15.0-step15-stage1-deferral`. Next:
step 16 (cluster launcher per Decision #7) per the rebuild plan, or pivot
to F-12 Phase 2A if user prefers (per
[`docs/v2_roadmap.md`](../docs/v2_roadmap.md) §4).
