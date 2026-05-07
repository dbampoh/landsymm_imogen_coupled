# Archive — Superseded and Reference Material

This directory contains scripts, outputs, and documentation that are **not part
of the active pipeline** but are kept on disk for historical reference and
audit-trail purposes. The contents are gitignored by default (see project root
`.gitignore`).

## Contents

### `superseded_lpjg_scripts/`
Earlier versions of the LPJ-GUESS processing and plotting scripts that lived
in the original `work/` directory before the project's natural-emissions
pipeline was rebuilt as `lpjg_v2/`.

Specifically:
- `lpjg_historical_processing.py` (264 lines) — the v1 LPJ-GUESS streaming
  processor. Superseded by the canonical `src/component_b_natural/historical/`
  version (353 lines), which adds proper unit tracking, more comprehensive
  validation, and better summary outputs.
- `lpjg_historical_plotting.py` (280 lines) — v1 plotter. Superseded by the
  canonical version (455 lines) which adds the IPCC scenario palette, segmented
  running-mean smoothing, the GMB/GNB/GCB step-band overlays, and the budget
  comparison panels.
- `lpjg_historical_processing_v1_top_level_work.py` and the `_v1_top_level_work`
  plotting copy — the same v1 versions that were duplicated into the top level
  of `work/`.
- The accompanying CSV outputs (`lpjg_ch4_annual.csv`, `lpjg_co2_annual.csv`,
  `lpjg_n2o_annual.csv`) and PNG (`lpjg_historical_comparison.png`) produced
  by these earlier versions.

The current canonical LPJ-GUESS code lives at `src/component_b_natural/`.

### `superseded_anthropogenic_worldrow_aggregation/`
Earlier versions of the RCMIP comparison plotting scripts that aggregated
emissions using the **World-row** approach (i.e. extracting the FAO "World"
country-level row directly). This was superseded by the **country-sum**
approach, where global totals are computed by summing all individual country
rows. The country-sum approach is more rigorous because it correctly handles
country splits/merges over the FAO time series.

- `rcmip_comparison1_plotting.py` (212 lines) and `rcmip_comparison2_plotting.py`
  — the v1 versions using World-row aggregation.
- The two PNGs produced by these v1 versions.

The current canonical versions live at
`src/component_a_anthropogenic/rcmip_substitution/` (274 lines, country-sum
approach).

### `scratch_session_scripts/`
One-shot Python scripts I created during the most recent chat session for
debugging or processing individual SSPs in isolation. Their logic is fully
captured in the canonical `src/component_b_natural/scenarios/lpjg_scenario_processing.py`.

- `n2o_run.py` — initial N2O streaming experiment
- `n2o_ssp1.py`, `n2o_ssp2.py`, `n2o_ssp3.py`, `n2o_ssp4.py`, `n2o_ssp5.py` —
  per-SSP N2O processing (because the canonical script processes all SSPs
  but I wanted to run them one at a time)
- `lpjg_repro.py` and `lpjg_*_annual_REPRO.csv` — bit-for-bit reproducibility
  verification artefacts

These are kept as debugging references for future maintainers who want to
understand how individual scenarios were validated.

### `prior_session_handoffs/`
The four chat-session handoff markdown documents that preceded the current
session's `HANDOFF.md`:

- `SESSION_HANDOFF_INITIAL.md` (80 KB) — Session 1: IPCC Tier 1 setup and
  sector-by-sector implementation of the historical anthropogenic inventory.
- `SESSION_HANDOFF_FINAL.md` (26 KB) — Session 6: Component A complete.
- `SESSION_HANDOFF_FINAL_2.md` (42 KB) — Expanded version of Session 6.
- `SESSION_HANDOFF_COMPLETE.md` (62 KB) — Session ~7: Component A complete +
  initial Component B work.

The current `HANDOFF.md` at the project root descends from these and
consolidates the entire project history.

---

## Why we keep these

For three reasons:

1. **Audit trail.** A future reader who wants to understand why the
   canonical scripts look the way they do can compare against the v1
   versions to see what was changed and why.

2. **Reproducibility verification.** The `*_REPRO.csv` files document
   bit-for-bit reproducibility checks against an earlier state of the
   pipeline.

3. **Methodological history.** The `worldrow_aggregation` versus
   `countrysum_aggregation` choice was a meaningful methodological
   decision; keeping the older code makes that explicit.

If you are reviewing the active pipeline, **ignore everything in this
directory** — only files under `src/`, `outputs/`, `docs/`, and `tests/`
are part of the working codebase.
