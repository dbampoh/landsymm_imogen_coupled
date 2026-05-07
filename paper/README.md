# `paper/` — manuscript and citation material

The GMD paper currently in preparation, plus the cited peer-reviewed
PDFs.

**Status:** populated incrementally as the rebuild progresses; the
manuscript is updated in step 18 to reflect the settled strategic
decisions (RCMIP backbone, two-IMOGEN-implementation strategy,
save_state/restart LU strategy, etc.).

## Planned contents (post-step-18)

```
paper/
├── manuscript_draft.docx                 The working paper (currently
│                                          `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`
│                                          from the predecessor framework's
│                                          References/) — to be updated to
│                                          cite RCMIP Phase 2 (Nicholls 2020)
│                                          as the substitution backbone.
├── figures/                              Figures produced for the paper.
│                                          Many will be outputs of the
│                                          `intermediary_py/src/component_*/...
│                                          /plotting.py` modules and the v1.0
│                                          coupled-run validation outputs.
├── references/                           Cited peer-reviewed PDFs, deduplicated
│   ├── (Huntingford 2010 GMD)
│   ├── (Zelazowski 2018 GMD)
│   ├── (Mathison 2025 PRIME GMD)
│   ├── (Hayman 2021 ESD)
│   ├── (Smith 2018 FAIR v1.3 GMD)
│   ├── (Alexander 2018 GCB)
│   ├── (Rabin 2020 ESD)
│   ├── (Olin 2015 ESD)
│   ├── (Lindeskog 2013 ESD)
│   ├── (Smith 2014 BG)
│   ├── (IPCC 2019 Refinement V4 Ch5/10/11)
│   ├── (IPCC Wetlands Supplement)
│   ├── (Saunois 2025 GMB ESSD)
│   ├── (Tian 2024 GNB ESSD)
│   ├── (Friedlingstein 2025 GCB ESSD)
│   ├── (Nicholls 2020 RCMIP Phase 2)
│   └── (Winkler 2021 HILDA+ v2 ESSD)
├── methodology_revisions.md              The paper revisions made in step 18:
│                                          (1) cite RCMIP as the substitution
│                                          backbone (Decision #1); (2) the
│                                          two-IMOGEN-implementation strategy
│                                          (Decision #2); (3) the save_state
│                                          /restart LU strategy (Decision
│                                          #10); (4) the Tmin/Tmax inputs
│                                          (Decision #11); (5) the tight
│                                          coupling default mode (Decision #4).
└── supplementary/                        Supplementary tables, sensitivity
                                           analyses, validation plots.
```

## Comparative-analysis framework for the results section (post-v1.0)

Per user guidance 2026-05-07 (refined after step 13's adapter
implementation made RCMIP-substituted emissions fully addressable),
the GMD paper's results section will be built around three
comparison axes. **All three are deferred to post-v1.0** (post-step-19
release); the v1.0 work is focused on getting the coupled model to
run end-to-end first. See `notes/FOLLOWUPS.md` F-13 for the full plan
+ existing template scripts to leverage.

### Axis 1 — Atmospheric GHG concentrations (CO2, CH4, N2O)

IMOGEN engine forced by:
- **RCMIP-raw** emissions (no substitution; reference baseline)
- **RCMIP-substituted** emissions (our IPCC Tier-1 + LPJG-natural;
  the v1.0 default per Decision #1)

intermediary_py's Component C produces both side-by-side
(`integrated_emissions_*.csv` columns `RCMIP_total_Mt` vs `Total_Mt`)
so this comparison is fully addressable now; just needs the
adapter (step 13) to convert `RCMIP_total_Mt` to engine-readable
form for a parallel comparison run.

### Axis 2 — Climate trends and patterns (T, P, SW, RH, wind, DTR, Tmin/Tmax)

Two sub-options (could do both for the paper):

- **Sub-option 2A**: RCMIP-raw IMOGEN climate vs RCMIP-substituted
  IMOGEN climate (parallel to Axis 1; isolates the effect of OUR
  emissions modelling on downstream climate)
- **Sub-option 2B**: RCMIP-substituted IMOGEN climate vs ISIMIP3b
  forcing climate (the climate used for Stage 1 PLUM-yield runs;
  validates IMOGEN's pattern-scaling against an established reference)

### Axis 3 — LPJ-GUESS ecosystem outputs

Standard LPJG outputs (cflux, cmass, anpp, mch4, ngases, ...) under
each of Axis 2's climate forcings. Quantifies the propagated effect
of emissions modelling choices on ecosystem responses (the science
the paper is ultimately about).

### Existing template scripts to leverage

Per user 2026-05-07, the predecessor framework's
`Python-scripts/comparative_analysis/analysis/` (identical in
version_A and version_B; ~73 MB total; ~1262 LOC across 3 .py files
+ 12 example output dirs + 3 summary-table xlsx + a 23 MB PPTX
context + a 15 KB synthesis markdown):

- `carbon_comparison.py` (~370 LOC) — LPJG ecosystem-carbon output
  comparison (Axis 3)
- `climate_comparison.py` (~640 LOC) — IMOGEN climate vs ISIMIP3b
  comparison (Axis 2 sub-option 2B)
- `preprocess_isimip_cache.py` (~250 LOC) — preprocesses ISIMIP3b
  cache for the climate_comparison consumer

These are **enhanceable starting points** — at minimum:
- Add **comparative stats alongside the plots** (currently plots only:
  RMSE, bias, mean, std, decadal-mean, IQR, comparison vs
  published budgets like GCB 2025 / Saunois 2025 / Tian 2024)
- Wire to v1.0's run-time outputs (currently hard-coded to
  predecessor paths)
- Add v1.0-RCMIP-backbone vs IIASA-backbone comparison (Axis 1
  novel; not in template scripts)

## Paper revisions needed (per user guidance 2026-05-07)

The current working draft is **substantially incomplete** — only
introduction + methods sections written, with supervisor comments +
edits applied. Post-v1.0 (specifically at step 18 when paper
revisions land), we will:

1. **Update the methodology section** to reflect Decision #1's RCMIP
   backbone (currently IIASA-based per the existing draft); cite
   Nicholls et al. (2020) RCMIP Phase 2 v5.1.0 + IPCC 2019
   Refinement Tier-1 + the new intermediary_py codebase as the
   substitution machinery
2. **Update the methodology section** to reflect Decision #2's
   two-IMOGEN-implementation strategy (Fortran ALLOCATABLE base + C++
   refactor switchable backend)
3. **Update the methodology section** to reflect Decision #4's
   tight-coupling default (and the F-10/F-12 architectural caveat,
   honestly disclosed)
4. **Update the methodology section** to reflect Decision #10's
   save_state/restart LU strategy
5. **Update the methodology section** to reflect Decision #11's
   Tmin/Tmax IMOGEN computation
6. **Add complete results section** based on the Axis 1/2/3
   comparisons above
7. **Add discussion section** including limitations (F-10 caveat;
   v1.0-vs-v2.0 scope split; PLUM embedding deferred per Decision #9)
8. **Add conclusions section** + complete references
9. **Submit to GMD** as planned

These revisions are the substantive paper-stage work that follows
the v1.0 release. They are tracked centrally as F-13 in
`notes/FOLLOWUPS.md`.

## Authoritativeness

The working paper draft is the **scientific source-of-truth** for
the framework (per `[CMI §7.1]`). Where the v1.0 codebase departs
from earlier paper-draft assumptions, the departure is documented
in `methodology_revisions.md` with the date settled and the new
canonical citation.

## License for paper material

The manuscript itself is © the authors (TBD). The cited PDFs in
`references/` are © their respective publishers and reproduced
here for fair-use citation only — the v1.0 release will use
DOI-resolvable links rather than embedded PDFs for the public
distribution.
