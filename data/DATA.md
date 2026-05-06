# `data/` — Tier-3 large-data acquisition recipes

This document records **how to obtain** the large datasets the
unified codebase references but does NOT include in git. For the small
data committed directly to git, see `data/README.md` and the per-subdir
README files. For the medium data fetched via the manifest-driven fetch
script, see `tools/imogen_data_manifest.txt` and `tools/README.md`.

Created at step 6 of the rebuild plan (2026-05-06).

---

## Tier-3 inventory (post-step-6)

| Dataset | Size | Status | Acquisition path |
|---|---:|---|---|
| **PLUM scenario LU** (`landsymm_py`-harmonised) | ~86 GB | Project-internal; on user's external drive | §1 below |
| **Legacy LU** (`Data/LU/SSP1_RCP26_concatenated/`) | 7.3 GB | Superseded by PLUM LU; fallback only (Option C) | §2 below |
| **Legacy Intermediary working tree** (`Data/Intermediary/`) | 2.2 GB | Superseded by `intermediary_py` at step 10 | §3 below |
| **Predecessor's IMOGEN pre-baked outputs** (`Common-directory/IMOGEN_SSPx_RCPy_Clim/`) | ~2 GB each | Reproducible by re-running the unified codebase | §4 below |
| **HILDA+ v2** (historic LU) | ~3 GB raw | Public Zenodo dataset; pre-processed via `landsymm_py` | §5 below |
| **FAOSTAT, EDGAR 2025, RCMIP Phase 2 v5.1.0, FAIR ERF v1.3** | varies (KB to MB each) | Public datasets used by `intermediary_py` (step 10) | §6 below |
| **NOAA GMD + AGAGE** (CO2/CH4/N2O monthly observations) | small | Public; needed at step 17 (validation) | §7 below |

---

## §1 — PLUM scenario LU (`landsymm_py`-harmonised)

**Status**: project-internal, modeller-supplied.

**Path on user's workstation** (mounted external drive):
```text
/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/
├── SSP1_RCP26/                       Per-SSP+RCP land-use forcing
├── SSP2_RCP45/                       (each: 5 SSPs × 1 RCP each = 5 dirs;
├── SSP3_RCP70/                        ~17 GB per scenario; 86 GB total)
├── SSP4_RCP60/
├── SSP5_RCP85/
├── output_hildaplus_remap_10b/       (HILDA+ historic remapped output)
├── output_hildaplus_remap_10b_3/     (variant)
└── reformat_gridded_updated.R        (post-processing R script)
```

This is the harmonised HILDA+v2-historic + PLUMv2-scenario forcing
produced by the user's `landsymm_py` codebase. Per **Decision #10
(`save_state`/`restart` strategy)** it is consumed by LPJ-GUESS at
two distinct stages:

1. **Historic spin-up + 1850-2020 simulation** uses the historic
   portion (HILDA+v2 1850-2020).
2. **Scenario simulation 2021-2100** restarts from the 2020 saved
   state and uses the PLUM-scenario portion.

This avoids the need for the legacy concatenated
`SSP1_RCP26_concatenated/` (Option B) or the in-process Stage I
yield-loop (Option A; deferred to v2.0 per Decision #9).

**Alternative location** (also user-supplied):
```text
/media/bampoh-d/ISIMIP/inputs/landuse/plum_harm_lu/
```
(same content; redundant copy on a different external drive).

**To use in a coupled run**:

```bash
# In the run setup directory (e.g. runs/SSP1-2.6/):
ln -s /media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/SSP1_RCP26/s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/ inputs/lu_plum_harm
# Then the run-setup .ins file references inputs/lu_plum_harm/...
```

(Specific subdir naming varies per scenario; consult the directory
listing when staging.)

**Provenance**: the user's `landsymm_py` codebase (separate project
worked on earlier in the chat history that preceded this rebuild).
For acquisition by external collaborators: contact the user / provide
a Zenodo upload of the SSP×RCP scenarios (~17 GB each) when published.

---

## §2 — Legacy concatenated LU (`Data/LU/SSP1_RCP26_concatenated/`)

**Status**: superseded by §1; retained on disk as Option-C fallback.

**Path**:
```text
version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Data/LU/SSP1_RCP26_concatenated/
├── LU_SSP1_RCP26_1901_2100_final.txt              (NATURAL/CROPLAND/PASTURE/BARREN
│                                                    × 200 yr × 0.5° = ~2 GB)
├── LU_SSP1_RCP26_1901_2100_final.txt.map.bin      (binary index)
├── cropfracs_SSP1_RCP26_1901_2100_final.txt       (22 crop-PFT cols)
├── cropfracs_SSP1_RCP26_1901_2100_final.txt.map.bin
├── irrig_SSP1_RCP26_1901_2100_final.txt
├── nfert_SSP1_RCP26_1901_2100_final.txt
└── nfert_SSP1_RCP26_1901_2100_final.txt.map.bin
```

This was the predecessor framework's pre-concatenated 1901-2100 LU
forcing for SSP1-RCP2.6. The other 4 SSP×RCP scenarios were never
concatenated, which is part of why we switch to the
`save_state`/`restart` strategy (§1) for v1.0.

**Re-derive from upstream HILDA+ + PLUM**: use the user's
`landsymm_py` codebase if needed. Don't bring this into git or a
tarball — it's an intermediate build artefact.

---

## §3 — Legacy Intermediary working tree (`Data/Intermediary/`)

**Status**: production shifts to `intermediary_py` at **step 10** of
the rebuild plan; this 2.2 GB legacy tree is not needed for v1.0.

**Path**:
```text
version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Data/Intermediary/
├── Emissions/                  (output: per-SSP CO2/CH4/N2O/enteric/manure CSVs)
├── IPCC_OWI_FAO/, IPCC_PLUM/   (intermediate IPCC tier-1 stage outputs)
├── Input/                      (FAOSTAT.csv, livestock-counts.csv, n2ofertilizer.csv,
│                                arablelands.csv, countries.txt, plus Input/{CMIP5,CMIP6}/
│                                IIASA emission inputs)
└── PLUM_data/                  (animals_ssp{1..5}.txt, plum_land_use/, agg_land_use/)
```

`intermediary_py/inputs/` will receive a curated subset of these
inputs at step 11; the user's `landsymm_py` codebase already produced
the harmonised animal counts and land-use data the new pipeline
needs.

**Re-derive**: the `Input/{FAOSTAT.csv,livestock-counts.csv,n2ofertilizer.csv,arablelands.csv}`
files come from public databases (FAOSTAT, OWI-FAO, EDGAR). The
PLUM-modeller-supplied `PLUM_data/animals_ssp*.txt` come from the
PLUM team. `Emissions/*` are reproducible by re-running the
intermediary pipeline against fresh inputs.

---

## §4 — Predecessor's IMOGEN pre-baked outputs

**Status**: reproducible by re-running the unified Fortran IMOGEN.

**Paths**:
```text
version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/
├── IMOGEN/                            (~397 MB; standalone-IMOGEN run output 1871-2100
│                                       from 2025-06-16; appears C++-produced per its
│                                       [IMOGEN LOGGER][...][INFO] log format)
├── IMOGEN_SSP1_RCP26_Clim/            (~396 MB each; pre-baked per-scenario climate
├── IMOGEN_SSP2_RCP45_Clim/             archives, presumably from past coupled runs
├── IMOGEN_SSP3_RCP70_Clim/             of the predecessor framework)
├── IMOGEN_SSP4_RCP60_Clim/
└── IMOGEN_SSP5_RCP85_Clim/
```

Step 4 of this rebuild already verified that the unified Fortran
IMOGEN produces structurally-equivalent output (per-year T_anom.dat,
P_anom.dat, etc.); see `notes/STEP_4.md` §6 for the comparison
analysis.

For external reproducibility: don't ship these. The unified codebase
regenerates them in 2-5 minutes per simulated year on the user's
workstation.

---

## §5 — HILDA+ v2 (historic LU)

**Status**: public Zenodo dataset; pre-processed via `landsymm_py`.

**Source**: Winkler, K., Fuchs, R., Rounsevell, M. and Herold, M. 2021.
"Global land use changes are four times greater than previously
estimated." *Nature Communications* 12, 2501.
[doi:10.1038/s41467-021-22702-2](https://doi.org/10.1038/s41467-021-22702-2)

**Download**:
```text
https://doi.org/10.1594/PANGAEA.921846
```

The user's `landsymm_py` codebase has done the harmonisation /
remapping work; the resulting per-SSP+RCP harmonised LU forcing is at
the §1 path. **Don't fetch HILDA+ from Zenodo unless you specifically
need to redo the harmonisation** — for v1.0 of this rebuild we use
the §1 outputs directly.

---

## §6 — Public emission/concentration databases (used by `intermediary_py`)

These are public datasets that `intermediary_py` (step 10) consumes
for IPCC tier-1 anthropogenic emissions estimation.

| Dataset | Source | Use |
|---|---|---|
| **FAOSTAT** | https://www.fao.org/faostat/en/#data | Activity data: livestock, crop area, fertiliser; 1961-present |
| **EDGAR 2025** | https://edgar.jrc.ec.europa.eu/ | Sector-resolved historical emissions for cross-checking |
| **RCMIP Phase 2 v5.1.0** | https://www.rcmip.org/ | Anthropogenic-emission substitution backbone (per Decision #1) |
| **FAIR ERF v1.3** | https://github.com/OMS-NetZero/FAIR | Effective radiative forcing for non-CO2 species in IMOGEN |
| **IIASA SSP database v2.0** | https://tntcat.iiasa.ac.at/SspDb/dsd | Historical-basis substitution alternative (deferred per Decision #1) |
| **PLUM v2 outputs** | PLUM modelling team (project-internal) | Activity data for SSP scenarios |

`intermediary_py/inputs/README.md` (step 11) will provide concrete
download recipes + file paths for each. For step 6 we just record the
URLs here for reference.

---

## §7 — NOAA GMD + AGAGE atmospheric concentration observations

**Status**: needed at step 17 (validation) per V.1 step 17 spec.

| Dataset | Source | Use |
|---|---|---|
| **NOAA GMD** | https://gml.noaa.gov/ccgg/trends/ | CO2 RMSD ≤ 5 ppm threshold; CH4 RMSD ≤ 50 ppb |
| **AGAGE** | https://agage.mit.edu/ | CH4 (cross-validation against NOAA); N2O |

Will be fetched into `data/observations/` at step 17.

---

## How to refresh this document

When a new Tier-3 dataset enters scope (e.g. additional GCM patterns,
new validation observations), add a section here with:

1. **Status**: project-internal vs public; static or live.
2. **Path** on the user's workstation if pre-acquired.
3. **Source / DOI / URL** if public.
4. **Acquisition recipe** (download URL, citation, optional checksum).
5. **Usage** in this codebase (which step, which run config).

Cross-link from `data/README.md` and the relevant step note.
