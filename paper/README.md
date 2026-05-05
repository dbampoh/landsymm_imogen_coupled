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
