# STEP 6 — Import remaining reference data → `data/` (+ `imogen/emiss/` restructure)

**Date completed:** 2026-05-06
**Commit:** _to be filled in after `git commit`_
**Status:** ✅ All four V.1 step-6 sub-deliverables landed:

1. ✅ Tier 1 small reference data committed to git (`data/{soil,gridlist,concentrations}/`, ~14 MB)
2. ✅ Tier 2 medium-large data tarballed + manifested + fetch-script-ready (Ndep + emiss reference)
3. ✅ Tier 3 acquisition recipes written (`data/DATA.md`)
4. ✅ Standalone IMOGEN regression smoke run still produces years 1871, 1872 after the path restructure

Closes follow-up **F-5** (stage emission scenarios into 5th tarball).

---

## 1. Goal

Per `EXECUTION_PLAN.md` V.1 step 6 + `[CMI §5]`'s data inventory, populate
`data/` with the small reference inputs the coupled model needs at
runtime, tarball the medium-large reference inputs (Ndep, emiss
references), and document the very-large Tier-3 datasets (PLUM
scenario LU at `/media/bampoh-d/lpjg_input/...` (86 GB), legacy concatenated
LU (7.3 GB), legacy `Data/Intermediary/` tree (2.2 GB), public
RCMIP/FAIR/EDGAR/etc.) without committing them.

---

## 2. Investigation: data classification

### 2.1 The investigation docs were authoritative

`COUPLED_MODEL_INVESTIGATION.md` §5 already had a definitive table
(line 2482-2491) of `Data/` subdirs with sizes and roles, and a
"should NOT be in git" list (line 2516-2534) totalling ~17 GB of the
18 GB tree. `EXECUTION_PLAN.md` V.1 step 6 had a precise spec: which
files to import, which to exclude, which to document. Step 6's
investigation reduced to **ground-truthing** the docs against the
filesystem.

### 2.2 Filesystem ground-truth (matches `[CMI §5]` exactly)

| `Data/` subdir | Spec size | Actual | Action |
|---|---:|---:|---|
| `soil/` | 3.5 MB | 3.5 MB (1 file) | Commit |
| `Gridlist/` | 3.4 MB | 3.4 MB (7 files) | Commit |
| `Concentrations/` | 9.5 MB | 9.5 MB (XLSX/ZIP excluded → 7.5 MB usable) | Commit (small files only) |
| `Imogen/emiss/` | ~5 MB | 5.2 MB (CMIP5/, CMIP6/, DKB_dataset_totals/, etc.) | **Tarball** (closes F-5) |
| `Ndep/ndep_cruncep/` | 501 MB | 501 MB (5 .bin files) | **Tarball** |
| `Intermediary/` | 2.2 GB | 2.2 GB | **Skip** (production shifts to `intermediary_py` step 10) |
| `LU/SSP1_RCP26_concatenated/` | 7.3 GB | 7.3 GB (7 files) | **Skip** (superseded by PLUM-LU §3) |

`Data/Emissions/` (916 KB) is not separately staged — its content overlaps
with `Data/Imogen/emiss/`. The IMOGEN-side tarball covers the relevant
part.

### 2.3 The PLUM-LU media path is mounted

```bash
$ ls -ld /media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/
drwxrwxrwx 1 root root 4096 Mar 31 15:57 /media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/
```

86 GB total: 5 SSP×RCP scenario dirs + 2 hilda_remap output dirs +
1 R post-processing script. Confirms the user's earlier note that
this is the canonical LU reference for v1.0 (per Decision #10's
`save_state`/`restart` strategy).

### 2.4 The active `imogen_intermediary.ins` references the deeper emiss subdirs

The user's reference SSP1-RCP2.6 run config at
`landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/imogen_intermediary.ins`
references:

```text
FILE_SCEN_EMITS  .../Data/Imogen/emiss/CMIP6/Co2/co2_pg_emissions_anthropogenic_historical_ssp126_1850_2100.txt
FILE_NON_CO2_VALS .../Data/Imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp126.txt
FILE_CH4_N2O_EMITS .../Data/Imogen/emiss/CMIP6/CH4-N2O/ch4_n2o_annual_historical_anthropogenic_ssp126_1850_2100.txt
FILE_LPJG_FLUX .../Data/Imogen/emiss/CMIP6/Co2/co2_pg_emissions_natural_historical_ssp126_1850_2100.txt
FILE_LPJG_CH4_N2O_FLUX .../Data/Imogen/emiss/CMIP6/CH4-N2O/ch4_n2o_annual_historical_natural_ssp126_1850_2100.txt
```

So step 6 cannot ship the flat-3-files emiss layout from step 4 — it
needs the full `Data/Imogen/emiss/` tree. This drove the
`imogen/emiss/` **restructure** (and the corresponding
`imogen_settings.txt` path update for the standalone run case).

---

## 3. Data classification (Tier 1 / Tier 2 / Tier 3)

### Tier 1 — committed to git (~14 MB)

| Path → unified destination | Source size | Why git |
|---|---:|---|
| `data/soil/soilmap_center_interpolated.remapv10_old_62892_gL.dat` | 3.5 MB | Single canonical file for any LPJ-GUESS run; binary-stable; reproducible only via complex remap pipeline |
| `data/gridlist/*.txt` (7 files) | 3.4 MB | Source-of-truth for cell selection; tiny |
| `data/concentrations/{EPA,IIASA}/{CMIP5,CMIP6}/...` (TXT/CSV/DAT only; XLSX/ZIP excluded) | 7.5 MB | Reference CO2/CH4/N2O timeseries used by IMOGEN config and by `intermediary_py`'s validation tests |

Total: ~14 MB across 31 files in 6 subdirs. Empty parent directories
(`XLSX/`, `ZIP/`, `IAM Scenarios/`) cleaned up post-rsync.

### Tier 2 — fetch-script + tarball

| Tarball | Contents | Raw | Compressed |
|---|---|---:|---:|
| `imogen-emiss-reference-v1.0.tar.gz` | Full `Data/Imogen/emiss/` tree (CMIP5/ + CMIP6/ + DKB + new + rcp + 6 loose files) — closes F-5 | 5.2 MB | **311 KB** (17×) |
| `imogen-ndep-lamarque-v1.0.tar.gz` | `Data/Ndep/ndep_cruncep/*.bin` (5 files: historic + RCP26/45/60/85) | 501 MB | **460 MB** (1.09×; binary already compressed-like) |

Both saved at `/home/bampoh-d/Desktop/.../lpj-guess_imogen_landsymm_data/` (sibling to repo).
Both registered in `tools/imogen_data_manifest.txt`. The fetch script
needed **zero code changes** — just two new manifest rows.

### Tier 3 — `data/DATA.md` documents acquisition

| Dataset | Size | Status |
|---|---:|---|
| PLUM scenario LU (`landsymm_py`-harmonised) | 86 GB | User's external drive, mounted at `/media/bampoh-d/lpjg_input/...` |
| Legacy concatenated LU | 7.3 GB | Superseded; fallback only |
| Legacy `Data/Intermediary/` | 2.2 GB | Superseded by `intermediary_py` step 10 |
| Predecessor's IMOGEN pre-baked outputs | ~2 GB each | Reproducible by re-running unified codebase |
| HILDA+ v2 (raw) | ~3 GB | Public Zenodo; pre-processed via `landsymm_py` |
| FAOSTAT, EDGAR 2025, RCMIP Phase 2 v5.1.0, FAIR ERF v1.3, IIASA SSP db | varies | Public; URLs in DATA.md §6 |
| NOAA GMD + AGAGE concentration observations | small | Public; needed at step 17 |

---

## 4. The `imogen/emiss/` restructure

### What changed

Step 4 staged a **flat-3-files layout** at the top of `imogen/emiss/`:

```text
imogen/emiss/
├── README.md
├── co2_emissions_annual_historical_rcp85_allsources.txt    ← from DKB_dataset_totals/
├── nonco2_ch4_n2o_RF_historical_rcp85.txt                  ← from DKB_dataset_totals/
└── ch4_n2o_annual_historical_rcp85_non_lpjg_simulated.txt  ← from DKB_dataset_totals/
```

This was a step-4 stop-gap so the **standalone IMOGEN smoke run**
could reach years 1871 and 1872 quickly. It was incompatible with
what the **coupled-mode** run config needs: the deeper subdir layout
of `Data/Imogen/emiss/` with `CMIP5/`, `CMIP6/{Co2,CH4-N2O,Non-Co2-CH4-N2O-RF}/`,
`DKB_dataset_totals/`, `new_emission_data/`, and `rcp_database/`.

Step 6 replaced the flat-3-files layout with the full tree:

```text
imogen/emiss/
├── README.md                              (committed)
├── CMIP5/                                 (extracted from tarball)
├── CMIP6/Co2/, CH4-N2O/, Non-Co2-CH4-N2O-RF/   (extracted)
├── DKB_dataset_totals/                    (extracted)
├── new_emission_data/                     (extracted)
├── rcp_database/                          (extracted)
└── 6 loose files (RF_NONCO2_GHG_IS92A.dat, emiss_co2.dat, hist_rcp{2p6,4p5,6p0,8p5}_*.txt)
```

### Settings file update (3-line change)

`imogen/code/imogen_settings.txt` lines 4-6 changed from:

```text
FILE_SCEN_EMITS ../emiss/co2_emissions_annual_historical_rcp85_allsources.txt
FILE_NON_CO2_VALS ../emiss/nonco2_ch4_n2o_RF_historical_rcp85.txt
FILE_CH4_N2O_EMITS ../emiss/ch4_n2o_annual_historical_rcp85_non_lpjg_simulated.txt
```

to:

```text
FILE_SCEN_EMITS ../emiss/DKB_dataset_totals/co2_emissions_annual_historical_rcp85_allsources.txt
FILE_NON_CO2_VALS ../emiss/DKB_dataset_totals/nonco2_ch4_n2o_RF_historical_rcp85.txt
FILE_CH4_N2O_EMITS ../emiss/DKB_dataset_totals/ch4_n2o_annual_historical_rcp85_non_lpjg_simulated.txt
```

(only the `DKB_dataset_totals/` prefix added).

### Why the restructure is the right call

Single canonical `imogen/emiss/` layout serves **both** standalone
IMOGEN runs (via `imogen_settings.txt` paths) and coupled-mode runs
(via `runs/<SSP>/imogen_intermediary.ins` paths). One source of truth;
no duplication.

---

## 5. The `.gitignore` extension

Added 2 new rules to filter the Tier-2 staged data:

```text
# Lamarque N-deposition binaries (~501 MB; staged at step 6 via tarball + fetch
# script). README.md preserved for git.
data/ndep/ndep_cruncep/
!data/ndep/README.md
```

The pre-existing `imogen/emiss/*` rule from step 4 already covers the
Tier-2 emiss restructuring (extracted CMIP5/, CMIP6/, etc. all
ignored; only `imogen/emiss/README.md` tracked).

The pre-existing `data/concentrations/IIASA/CMIP*/XLSX/` and
`data/concentrations/IIASA/CMIP*/ZIP/` rules from step 0 correctly
exclude the raw IIASA download dirs. (One side effect: a 5.4 MB CSV
that lives at `IIASA/CMIP6/XLSX/SSP_CMIP6_201811.csv` despite being a
CSV is also excluded — investigated and confirmed it's a
raw-IIASA-database download, not a runtime input; documented in
`data/DATA.md` §6 with re-acquisition recipe).

---

## 6. Verification

### 6.1 Tier 1 staging

```bash
$ git ls-files --others --exclude-standard data/ | wc -l
31  # 1 soil + 7 gridlists + 23 concentrations files
$ du -sh data/{soil,gridlist,concentrations}/
3.5M    data/soil/
3.4M    data/gridlist/
7.5M    data/concentrations/
```

Sanity: no XLSX/ZIP raw downloads leaked through.

### 6.2 Tier 2 tarball + manifest

```bash
$ tools/fetch_imogen_data.sh --base ../lpj-guess_imogen_landsymm_data --verify-only
…
SUCCESS: processed 6 component(s) cleanly.
```

All 6 manifest rows verify clean SHA256 + size. The 2 new tarballs:

| Tarball | SHA256 (truncated) | Bytes |
|---|---|---:|
| `imogen-emiss-reference-v1.0.tar.gz` | `77b05df3…` | 318 329 |
| `imogen-ndep-lamarque-v1.0.tar.gz` | `a135d647…` | 481 904 459 |

### 6.3 Standalone IMOGEN regression smoke run

After the `imogen_settings.txt` path update, with `done` file
restored at `imogen/code/LPJG_main/IMOGEN/` (bug-C2/C3 workaround;
fixed at step 7 / followup F-4):

```bash
$ cd imogen/code && rm -rf IMOGEN/output/* && timeout 60 ./imogen_lpjg
…
$ ls IMOGEN/output/
1871  1872
$ ls IMOGEN/output/1871/
CO2.dat  DTEMP_anom.dat  P_anom.dat  SW_anom.dat  T_anom.dat  WET.dat  done  dtemp_o.dat  fa_ocean.dat
```

✅ Years 1871, 1872 produced with all expected climate files. Output
matches step 4's verification — no regression from the path change.

### 6.4 Coupled-run path resolution (build-time check, no run)

The active SSP1-RCP2.6 reference config at
`landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/imogen_intermediary.ins`
references `imogen/emiss/CMIP6/Co2/co2_pg_emissions_anthropogenic_historical_ssp126_1850_2100.txt`
etc. These paths now resolve to actual files in the unified codebase.
The full coupled-mode run is gated on step 7 (apply the 7 LPJ-GUESS
coupling fixes) + step 8 (LPJG-side handshake writer).

---

## 7. Files added / modified

### Added (committed to git)

| Path | Bytes | Purpose |
|---|---:|---|
| `data/DATA.md` | new | Tier-3 acquisition recipes |
| `data/soil/soilmap_center_interpolated.remapv10_old_62892_gL.dat` | 3 564 133 | Tier 1 soil |
| `data/gridlist/{7 files}` | ~3.5 MB | Tier 1 gridlists |
| `data/concentrations/{23 files}` | ~7.5 MB | Tier 1 GHG concentrations (TXT/CSV/DAT) |
| `data/ndep/README.md` | ~3 KB | Tier 2 acquisition pointer |
| `notes/STEP_6.md` | this file | Per-step verification record |

### Modified

| Path | Change |
|---|---|
| `.gitignore` | Add `data/ndep/ndep_cruncep/` exclusion + README allowlist |
| `tools/imogen_data_manifest.txt` | Add 2 manifest rows: `emiss-reference` + `ndep-lamarque` |
| `imogen/code/imogen_settings.txt` | Update `FILE_*_EMITS` paths to point at `DKB_dataset_totals/` subdir (3-line change) |
| `imogen/emiss/README.md` | Rewrite to describe full restructured tree |
| `data/README.md` | Rewrite to describe Tier-1/2/3 layout with concrete file inventory |
| `notes/FOLLOWUPS.md` | Move F-5 from OPEN to DONE |
| `CHANGELOG.md` | `[v0.6.0-data-import]` entry |
| `EXECUTION_PLAN.md` | V.1 step 6 marked ✅ |

### Generated (NOT in git)

- `data/ndep/ndep_cruncep/{5 .bin files}` — 501 MB; gitignored;
  fetched via `--component ndep-lamarque`.
- `imogen/emiss/{CMIP5,CMIP6,DKB_dataset_totals,new_emission_data,rcp_database}/` plus loose files — 5.2 MB; gitignored; fetched via `--component emiss-reference`.
- 2 new tarballs at sibling path
  `lpj-guess_imogen_landsymm_data/{imogen-emiss-reference,imogen-ndep-lamarque}-v1.0.tar.gz`.

---

## 8. Recovery / re-fetch protocol

To reproduce step 6's setup from a fresh clone:

```bash
# 1. Clone the repo (Tier 1 included automatically)
git clone https://github.com/dbampoh/landsymm_imogen_coupled.git
cd landsymm_imogen_coupled

# 2. Fetch all 6 Tier-2 tarballs (patterns + cruncep + emiss + ndep) from a
#    permanent host — currently the user's local sibling dir; F-1 will
#    eventually point this at Zenodo / GitHub Releases:
tools/fetch_imogen_data.sh --base /path/to/lpj-guess_imogen_landsymm_data

# 3. (Optional) Acquire Tier-3 large data per data/DATA.md if you need it
#    for a specific step. Most users won't.

# 4. Build IMOGEN
cd imogen/code && make

# 5. Stage the LPJG-side stub files for bug-C2/C3 workaround (until step 7):
mkdir -p LPJG_main/IMOGEN
touch LPJG_main/IMOGEN/done
# (copy the 8 stub files from version_A or from step 4's notes; the
#  workaround goes away at step 7 when the source-fix lands)

# 6. Run
./imogen_lpjg
```

Per-step recovery: clean revert via `git revert <hash>` removes the
data-import infrastructure but leaves the data directories themselves
on disk (they're gitignored). The fetch script will re-extract.

---

## 9. Follow-ups closed by step 6

- **F-5 (CLOSED)** — Stage emission scenarios into a 5th tarball.
  Done as `imogen-emiss-reference-v1.0.tar.gz`; manifest row added;
  fetch-script verifies clean.

## Follow-ups raised by step 6

None new. Step 6 was a curation step rather than a discovery step.

---

## 10. Push commands (manual three-way push)

```bash
cd /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm

git push origin main
git push kit main
git push helmholtz main

# Optional tag:
git tag -a v0.6.0-data-import -m "Step 6: reference data import (Tier 1 in git, Tier 2 tarball + fetch, Tier 3 documented); imogen/emiss/ restructured to full tree; closes followup F-5"
git push origin v0.6.0-data-import
git push kit    v0.6.0-data-import
git push helmholtz v0.6.0-data-import
```
