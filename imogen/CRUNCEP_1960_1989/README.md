# `imogen/CRUNCEP_1960_1989/` — base climatology for IMOGEN's pattern-scaling

This directory holds the 30-year CRUNCEP climatology (1960-1989)
that IMOGEN uses as the baseline against which GCM-pattern-derived
anomalies are added. **The data is NOT in git** — it is large
reference data (~60 MB raw, 11 MB compressed) acquired via the fetch
script.

## What is here when fully populated (360 entries, ~60 MB)

360 ASCII files at the top level, no subdirectories, named
`<month><year_offset>` where:

- `<month>` is a 3-letter abbreviation: `jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec`
- `<year_offset>` is an integer 1-30 corresponding to calendar years 1960-1989

So e.g. `apr1` = April 1960, `dec30` = December 1989.

Each file is ~170 KB ASCII, one row per cell on the IMOGEN HadCM3
native land grid (`GPOINTS=1631`), with columns for the climatology
variables (T, precip, RH, wind, pressure, shortwave, longwave, etc.).

## How to acquire

```bash
tools/fetch_imogen_data.sh --base <DATA_LOCATION> --component cruncep
```

(or omit `--component` to fetch the patterns + climatology together;
see `imogen/patterns/README.md` for the full menu.)

After a successful fetch, the `imogen_lpjg` binary's default
`DIR_CLIM=../CRUNCEP_1960_1989/` setting in
`imogen/code/imogen_settings.txt` resolves correctly.

## Why these 30 years?

The 1960-1989 window is the standard IMOGEN base-period (Huntingford &
Cox 2000; Zelazowski 2018) — chosen as 30 years of relatively quiescent
forcing pre-dating the strongest CO2-induced warming, providing a clean
baseline from which the GCM patterns are added. Replacing it with a
later window (e.g. 1990-2019) requires regenerating the pattern files,
which is out of scope for v1.0 of this codebase.

## Provenance

Generated at step 4 of the unified-codebase rebuild (DKB 2026-05-05)
from `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/CRUNCEP_1960_1989/`.
The original CRUNCEP-v7 climatology source was reduced to this 30-year
×12-month×1631-cell ASCII subset by the predecessor framework; the
exact pre-processing pipeline is documented in
`paper/IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` §2.2.
