# `imogen/patterns/` — GCM patterns for IMOGEN's pattern-scaling

This directory holds the GCM-pattern data the Fortran IMOGEN binary
uses to scale the base CRUNCEP climatology to a chosen GCM's response
to a given radiative-forcing trajectory. **Most of this directory's
contents are NOT in git** — they are large reference data acquired via
the fetch script (see "How to acquire" below).

## What is here when fully populated (40 entries, ~101 MB)

| Subdirectory | Provenance | Format | Size | Purpose |
|---|---|---|---:|---|
| `CEN_*_MOD_*/` (× 34) | CMIP5 ensemble (Zelazowski 2018) | ASCII, 12 month files | ~2.4 MB each | the standard 34-GCM CMIP5 set used by the working paper |
| `ukmo_hadcm3_rel/` | UKMO CMIP3 / HadCM3 (Huntingford & Cox 2000) | ASCII, 12 month files | ~2.0 MB | legacy CMIP3 reference pattern |
| `CMIP6_IMOGEN_EBM_values_and_patterns/` | CMIP6 (5 GCMs: GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL) | NetCDF + JSON params | ~20 MB | newer CMIP6 patterns; consumed via the planned `tools/cmip6_nc_to_cmip5_ascii.py` converter at step 5 of the rebuild plan |
| `readme.log` | Original upstream readme | text | <1 KB | upstream provenance note (committed to git) |

`Common-directory/IMOGEN-codebase/patterns/readme.log` (the only
piece of `patterns/` actually committed to git) reads:

```text
#imogen CMIP5 patterns

see also /pd/data/lpj/input_data/IMOGEN_patterns/CMIP5/patterns/

and copy needed patterns folder here
```

That instruction is the predecessor framework's manual-acquisition
note. Step 4 of the unified-codebase rebuild replaces it with the
automated fetch script described next.

## How to acquire (run-time data fetch)

The pattern + climatology data live as 4 tarballs (~49 MB total
compressed, ~161 MB extracted) outside of git. Fetch via:

```bash
# From the repository root:
tools/fetch_imogen_data.sh --base <DATA_LOCATION>

# Where <DATA_LOCATION> is one of:
#   - a local directory containing the 4 tarballs
#     (e.g. ../lpj-guess_imogen_landsymm_data/ on the workstation)
#   - an https:// URL prefix where they're hosted
#     (TBD: a Zenodo record / GitHub Release / institutional bucket;
#      see notes/FOLLOWUPS.md item F-1)
```

> **NOTE (post-step-4)**: until item **F-1** in `notes/FOLLOWUPS.md` is
> closed (the tarballs are uploaded to a permanent public host), the
> fetch script only works against a **local directory** `--base`.
> Fresh clones therefore cannot acquire the data without first being
> pointed at a copy on the same machine or via `rsync` from another
> machine. This is a temporary state.

`tools/imogen_data_manifest.txt` is the authoritative manifest of
filenames, SHA256 checksums, and sizes. The fetch script verifies
both before extraction.

To fetch only what's needed for a smoke run (CMIP5 default
+ CRUNCEP only, ~30 MB compressed):

```bash
tools/fetch_imogen_data.sh --base ... --component patterns-cmip5 --component cruncep
```

After a successful fetch, the layout matches what
`imogen/code/imogen_settings.txt`'s default
`DIR_PATT=../patterns/CEN_IPSL_MOD_IPSL-CM5A-MR/` and
`DIR_CLIM=../CRUNCEP_1960_1989/` paths expect.

## Format conventions

### CMIP5 ASCII patterns (`CEN_*_MOD_*/`)

Each GCM directory contains exactly 12 files: `jan, feb, mar, apr,
may, jun, jul, jun, jul, aug, sep, oct, nov, dec`.

The **first line** is the global header:

```text
    LON_W   LAT_S    LON_E   LAT_N
```

(typically `0.00 -60.00 360.00 90.00` — i.e. the global land-only
domain that the IMOGEN HadCM3 native grid covers; 1631 cells south
of 60°N).

Each subsequent line is one cell at `(LON, LAT)` followed by ~13
pattern coefficients used by the energy-balance + pattern-scaling
calculation in `imogen_lpjg.f`. The exact column meanings are
described in Huntingford & Cox 2000 §2.

### CMIP3 legacy pattern (`ukmo_hadcm3_rel/`)

Same 12-file ASCII format as CMIP5; slightly older provenance and
slightly different size (~2 MB total instead of ~2.4 MB). Retained
as the historical baseline against which other GCMs are compared.

### CMIP6 NetCDF patterns (`CMIP6_IMOGEN_EBM_values_and_patterns/`)

Each of 5 CMIP6 GCMs has 2 files:

- `<gcm>_patterns.nc` (~4.1 MB NetCDF) — 8 pattern variables
  (`tl1_patt`, `ql1_patt`, `precip_patt`, `wind_patt`, `pstar_patt`,
  `swdown_patt`, `lwdown_patt`, `range_tl1_patt`) on a
  (`imogen_drive=12`, `lat=56`, `lon=96`) grid
- `<gcm>_params.json` (~180 bytes) — energy-balance model params
  (`kappa_o`, `lambda_l`, `lambda_o`, `mu`, `f_ocean`)

The Fortran IMOGEN binary in this repository **does not read NetCDF
directly**. **Step 5** of the rebuild added `tools/cmip6_nc_to_cmip5_ascii.py`
which converts these to the CMIP5 ASCII format the binary already
accepts:

```bash
# Batch-convert all 5 CMIP6 GCMs:
python tools/cmip6_nc_to_cmip5_ascii.py \
  --input-dir imogen/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/ \
  --gridlist imogen/code/patterns_gridlist.txt \
  --output-base imogen/patterns/

# Result:
#   imogen/patterns/CEN_CMIP6_MOD_GFDL-ESM4/{jan,feb,...,dec}
#   imogen/patterns/CEN_CMIP6_MOD_IPSL-CM6A-LR/{jan,feb,...,dec}
#   imogen/patterns/CEN_CMIP6_MOD_MPI-ESM1-2-HR/{jan,feb,...,dec}
#   imogen/patterns/CEN_CMIP6_MOD_MRI-ESM2-0/{jan,feb,...,dec}
#   imogen/patterns/CEN_CMIP6_MOD_UKESM1-0-LL/{jan,feb,...,dec}
#   imogen/patterns/<MODEL>_ebm.nml   (one per GCM; energy-balance scalars)
```

Outputs land at `imogen/patterns/CEN_CMIP6_MOD_<gcm>/`, are covered by
the same `CEN_*` gitignore rule, and the binary then consumes them
identically to a native CMIP5 directory by setting
`DIR_PATT=../patterns/CEN_CMIP6_MOD_<gcm>/` in `imogen_settings.txt`.

Three documented caveats in the conversion (see `tools/cmip6_nc_to_cmip5_ascii.py`
module docstring + `notes/STEP_5.md` for full discussion + `notes/FOLLOWUPS.md`
F-6, F-7, F-8 for follow-up confirmations needed):

- **CAVEAT-A**: `ql1_patt` (units "K-1") is passed through into CMIP5
  col 4 (`DRH15M_PAT`) without unit conversion. Open question: is the
  CMIP6 file already aligned to IMOGEN's RH-sensitivity convention?
- **CAVEAT-B**: CMIP6 stores only wind-speed magnitude `wind_patt`,
  not signed U/V components. We split equally
  (`U = V = wind_patt / √2`) to preserve magnitude.
- **CAVEAT-C**: CMIP6 stores only total `precip_patt`, not rain/snow
  split. We put the full pattern into rainfall, zero into snowfall.
  Total precip is preserved; the rain/snow partition is then handled
  downstream by IMOGEN's temperature-based partition rule.

## Selecting a GCM

The GCM is selected by setting `DIR_PATT` in `imogen/code/imogen_settings.txt`
(default: `../patterns/CEN_IPSL_MOD_IPSL-CM5A-MR/`). Any of the 35 ASCII
GCM directories is a valid choice once it has been acquired.

## Provenance — where the data originally came from

These tarballs were generated at step 4 of the unified-codebase
rebuild (DKB 2026-05-05) from
`version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/patterns/`.
The CMIP5 set originates from Zelazowski 2018 (the IMOGEN paper that
introduced the 22-GCM pattern collection, later extended to 34 GCMs);
the CMIP3 `ukmo_hadcm3_rel/` set is from Huntingford & Cox 2000;
the CMIP6 set was added by the predecessor framework in early 2025.
See `paper/` for the canonical scientific lineage.
