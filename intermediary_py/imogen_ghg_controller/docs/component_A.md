# Component A — Anthropogenic Agricultural Inventory

**Location**: `src/component_a_anthropogenic/`

## Purpose

Construct an independent IPCC 2019 Refinement Tier-1 agricultural emission inventory at country level for six sectors, then extend into SSP-RCP scenario projections, then substitute these into the published RCMIP/CMIP6 anthropogenic emission trajectory to produce our own anthropogenic trajectories for CH₄ and N₂O.

## Sub-pipelines

### `historical/` — six sector pipelines, 1970–2020

| Sector | Gas | Activity data | Tier 1 source |
|---|---|---|---|
| `ch4_ef_*` | CH₄ | FAO livestock | IPCC 2019 V4 Ch10 |
| `ch4_mm_*` | CH₄ | FAO livestock | IPCC 2019 V4 Ch10 |
| `ch4_rice_*` | CH₄ | FAO rice harvested area | IPCC 2019 V4 Ch5 |
| `n2o_mm_*` | N₂O | FAO livestock | IPCC 2019 V4 Ch10 |
| `n2o_ms_*` | N₂O | FAO livestock + crop residues | IPCC 2019 V4 Ch11 |
| `n2o_synfert_*` | N₂O | FAO fertilizer inputs | IPCC 2019 V4 Ch11 |

Each sector has a `*_processing.py` script that produces global / country / regional / sub-category CSVs in `outputs/component_a/data/<sector>/`, and a `*_plotting.py` script that produces a publication-quality 4-panel trend plot.

### `scenarios/` — five sector pipelines + livestock anchor, 2020–2100

The livestock anchor (`00_scenario_livestock_anchor.py`) must run first. It uses PLUMv2 SSP-RCP relative-change projections to anchor 2020 livestock counts forward to 2100. Other scripts then use these anchored counts with the same Tier-1 equations as historical.

Numbered processing scripts (`01_…05_`) run in order. CH₄ rice cultivation scenario was pending in prior session handoffs; not yet implemented.

### `rcmip_substitution/` — Tier-1 substitution into RCMIP trajectory

`rcmip_substitution_processing.py` produces `rcmip_substitution_ch4.csv` and `rcmip_substitution_n2o.csv`: per-scenario annual trajectories where the CEDS/CMIP6 agricultural sectors have been replaced with our Tier-1 estimates. Two comparison plots show the agricultural-sector-only and full-totals comparisons.

## Key outputs

- `outputs/component_a/data/rcmip_substitution_ch4.csv` and `_n2o.csv` — these are the integrated anthropogenic trajectories consumed by Component C.
- Per-sector global / country / regional / scenario CSVs for diagnostic and reporting purposes.

## Caveats from prior session handoffs

See `HANDOFF.md` §2.5. Brief summary:
- Tier 1 starts at 1970 (not 1900); pre-1970 anthropogenic in our trajectories uses RCMIP unchanged.
- CH₄ rice cultivation scenario projection is pending (only historical exists).
- Some sectors have known systematic differences from FAO's own EDGAR-based estimates; these are documented.
