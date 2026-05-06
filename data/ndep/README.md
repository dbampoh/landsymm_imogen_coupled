# `data/ndep/` — N-deposition Lamarque archives

The 5 Lamarque-format binary fast-archive files used by LPJ-GUESS for
N-deposition forcing. **Not committed to git** — acquired via
`tools/fetch_imogen_data.sh --component ndep-lamarque`.

## What is here when fully populated (5 files, ~501 MB)

| File | Size | What it represents |
|---|---:|---|
| `ndep_cruncep/GlobalNitrogenDeposition.bin` | 132 MB | Historic 1850-2014 (Lamarque-format binary fast-archive) |
| `ndep_cruncep/GlobalNitrogenDepositionRCP26.bin` | 94 MB | RCP2.6 scenario forward extension |
| `ndep_cruncep/GlobalNitrogenDepositionRCP45.bin` | 92 MB | RCP4.5 scenario forward extension |
| `ndep_cruncep/GlobalNitrogenDepositionRCP60.bin` | 92 MB | RCP6.0 scenario forward extension |
| `ndep_cruncep/GlobalNitrogenDepositionRCP85.bin` | 92 MB | RCP8.5 scenario forward extension |

These are read by LPJ-GUESS's `Lamarque::ndep` module via the
`file_ndep` ins parameter, and consumed in:

- **`imogen_input.cpp`** (loose-coupling mode), at line 728
  (currently the `ndep.getndep(...)` call is commented out — bug **C4**;
  fixed at **step 7** of the rebuild plan).
- **`imogencfx.cpp`** (tight-coupling mode), at line 896.

## How to acquire

```bash
# From the repository root:
tools/fetch_imogen_data.sh --base <DATA_LOCATION> --component ndep-lamarque

# Where <DATA_LOCATION> is one of:
#   - a local directory containing the tarball
#     (e.g. ../lpj-guess_imogen_landsymm_data/ on the workstation)
#   - an https:// URL prefix where it's hosted
#     (TBD: see notes/FOLLOWUPS.md item F-1)
```

The `tools/imogen_data_manifest.txt` row for this component is the
authoritative SHA256 + size record:

```text
ndep-lamarque  imogen-ndep-lamarque-v1.0.tar.gz  a135d647...  481904459  data/
```

Compressed tarball ≈ 460 MB (binary; gzip yields modest 1.09× compression).

## Format

`Lamarque-format` binary fast-archive: a custom packed-binary layout
the predecessor framework's `NdepFastArchive/` C++ utility (in the
predecessor's repo, not imported into this rebuild) generated from
the upstream Lamarque et al. 2013 ACPD CMIP5-N-deposition NetCDF
files.

The unified codebase consumes these files as-is via the existing
`Lamarque::ndep` C++ class in `lpjguess/modules/`. Re-archiving from
upstream Lamarque NetCDF would require resurrecting the
`NdepFastArchive/` build (it's listed at `[CMI §4.8 Aux 1]` as not
having a Linux build); deferred to post-v1.0.

## Provenance

- Upstream science: Lamarque, J.-F. et al. 2013. "The Atmospheric
  Chemistry and Climate Model Intercomparison Project (ACCMIP):
  overview and description of models, simulations and climate
  diagnostics." *Geoscientific Model Development* 6, 179-206.
- Predecessor framework's archive: `version_A/.../Data/Ndep/ndep_cruncep/`
  (created Jun 2025 from upstream Lamarque NetCDF via predecessor's
  `NdepFastArchive`).
- Snapshot tarballed 2026-05-06 at step 6 of the unified-codebase
  rebuild.
