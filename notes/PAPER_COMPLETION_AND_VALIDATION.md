# Paper completion + validation triad — comprehensive working document

**Version**: v0.1 (initial draft; session 7 evening close 2026-05-19; iteratively updated through validation triad execution + paper writing)
**Status**: 🔧 LIVING DOCUMENT — populated incrementally as the validation triad scripts are ported + enhanced, results are analyzed, paper figures are produced, and the manuscript is drafted toward GMD submission.
**Last updated**: 2026-05-19 evening (session 7 close); first authoring + initial framing.

**Audience**: anyone (current + future maintainers + future chat agents) needing to:
- Understand the validation-triad structure for the v1.0 GMD paper
- Find + assess + port + enhance the existing intermediary_py plotting scripts (21 scripts) for paper-grade figures
- Find + port + enhance the predecessor-framework comparison scripts (~1010 LOC across 3 scripts) for the IMOGEN-vs-ISIMIP climate comparison + Track-1-vs-Track-2 LPJG ecosystem comparison
- Plan + execute the paper revisions (methods + results + discussion + conclusion + references)
- Find the right canonical docs for any specific paper-stage question

**Companions**:
- `paper/README.md` — the canonical paper-stage doc (manuscript contents plan + comparative-analysis framework + 9-item paper-revisions checklist; F-13 cross-reference)
- `notes/PRODUCTION_RUN_CONFIG.md` §5.3 — validation triad table (4 axes; Track 1 already-exists vs Track 2 NEW)
- `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` — sibling document covering the runs that produce the outputs analyzed in this document
- `notes/FOLLOWUPS.md` F-13 — post-v1.0 paper-stage comparative-analysis framework (the central tracking record for this work; full detail at FOLLOWUPS lines ~720+)
- `intermediary_py/imogen_ghg_controller/src/component_{a,b,c}_*/...plotting.py` — 21 existing plotting scripts (some directly paper-grade, some methodology figures)
- Predecessor comparison scripts (3 scripts, ~1010 LOC): `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/version_{A,B}/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Python-scripts/comparative_analysis/analysis/{climate_comparison,carbon_comparison,preprocess_isimip_cache}.py`
- Working manuscript draft: `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/version_A/.../References/IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` (currently: intro + methods only, with supervisor comments + edits applied)
- `notes/B40.md` §4 — the N2O sector-ownership-rule paragraph drafted for paper methods inclusion
- `docs/scientific_framework.md` — coupled-model scientific architecture (paper methods section foundation)

---

## 1. Validation triad — the 4 axes for the GMD paper results section

Per `paper/README.md` §"Comparative-analysis framework" + `notes/PRODUCTION_RUN_CONFIG.md` §5.3, the v1.0 paper's results section is structured around 4 comparison axes:

### 1.1 Axis 1 — Anthropogenic emissions plots

**Purpose**: document the integrated anthropogenic emissions modelling for each SSPx_RCPyy scenario (CO2, CH4, N2O); show RCMIP-substituted vs RCMIP-raw difference where applicable; justify the IPCC-Tier-1 refinement chosen.

**Tools**: existing intermediary_py plotting scripts (per §2 inventory below).

**Status**: ✅ READY — produced by intermediary_py itself; existing scripts likely paper-grade or close to it; readiness assessment is a real-time review at paper-figure-generation time.

**Estimated effort to paper-figure-ready**: ~0.5-1 day (review existing plots + tune styling/captioning).

### 1.2 Axis 2 — IMOGEN-derived atmospheric GHG concentrations vs literature

**Purpose**: document that IMOGEN-engine-derived atmospheric concentrations (CO2, CH4, N2O) match the historical record + are physically plausible across all 5 SSPs through 2100.

**Tools**: 
- `scripts/b19_phase4_literature_validate.py` (currently smoke-window 1900-1903 only; PASSED at B19 Phase 4 with STRICT_PASS post-B39 init-seed correction)
- Extension to full 1900-2100 horizon for paper (post-Track-2-runs deliverable)
- Reference data: MacFarling Meure 2006 (Law Dome ice core; pre-1957 CO2/CH4/N2O); Etheridge 1996 (Law Dome; supporting); Meinshausen 2017 (RCMIP / IPCC AR6); modern instrumental record (Mauna Loa, NOAA flask network)

**Status**: 🔄 PARTIALLY READY — smoke validation passed; production-horizon extension awaits Track 2 production runs (per `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` phase 2-3).

**Estimated effort to paper-figure-ready**: ~1-2 days (extend the validation script to full 1900-2100 + 5 SSPs; add panel-of-3 figure (CO2 + CH4 + N2O) with literature overlay).

### 1.3 Axis 3 — IMOGEN-derived climate vs ISIMIP3b climate

**Purpose**: document the climate-driver fidelity between two driver pipelines: IMOGEN's RCMIP-substituted-emissions-driven climate vs ISIMIP3b MRI-ESM2-0 climate (the climate used for Stage 1 PLUM-yield runs); difference maps + trend comparisons.

**Tools**: 
- Predecessor `climate_comparison.py` (~640 LOC at `version_{A,B}/.../comparative_analysis/analysis/`) — to be ported + enhanced
- Predecessor `preprocess_isimip_cache.py` (~250 LOC; preprocesses ISIMIP3b cache for the comparison consumer)

**Status**: ❌ NOT YET STARTED — predecessor scripts have not been ported to the rebuild repo; tracked as F-13. **Awaits Track 2 production runs + porting work** (per §3 below).

**Estimated effort to paper-figure-ready**: ~3-5 days (port + adapt to v1.0 paths + add comparative stats per `paper/README.md` lines 113-120 enhancement list + produce 6-variable panel figures (T, P, SW, Rh, wind, DTR) for difference maps + trend comparisons).

### 1.4 Axis 4 — LPJG ecosystem state outputs: Track 1 vs Track 2

**Purpose**: document the propagated effect of climate-driver pipeline choice (ISIMIP3b in Track 1 vs IMOGEN-engine-derived in Track 2) on LPJ-GUESS ecosystem outputs (cflux, cmass, anpp, mch4, ngases, etc.) with all other inputs (LU, popdens, ndep, SimFire, soilmap, gridlist) held identical between the two tracks. The science the paper is ultimately about.

**🔧 STRATEGIC CAVEAT raised at session 7 close (2026-05-19 12:53 AM)**: this Axis 4 framing tacitly assumes Track 2 uses the rebuild repo's LPJ-GUESS. **For paper-reviewer-defensibility, Track 1 vs Track 2 is much cleaner if LPJG version is held constant** — i.e., Track 2 also runs on `trunk_r13078` (the version that produced Track 1) with minimalist backport from the rebuild rather than the rebuild's later-4.1-base. The session 8.0 strategic decision per `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §0.2 (Option R vs Option T) materially affects this Axis 4 validation interpretation. **Preliminary recommendation: Option T** (trunk_r13078 minimally updated; ~150-300 LOC backport; Track 1 vs Track 2 isolates climate driver as the only variable; cleaner paper story); subject to session 8.0 C0-C5 verification.

**Tools**:
- Predecessor `carbon_comparison.py` (~370 LOC at `version_{A,B}/.../comparative_analysis/analysis/`) — to be ported + enhanced
- New scripting for non-carbon ecosystem variables (anpp; ngases for CH4/N2O; landcover; firert; nflux; etc.) — may need new scripts beyond the carbon-only predecessor scope

**Status**: ❌ NOT YET STARTED — predecessor `carbon_comparison.py` has not been ported; tracked as F-13. **Awaits Track 2 production runs + porting work** (per §3 below).

**Estimated effort to paper-figure-ready**: ~4-7 days (port + adapt to v1.0 paths + add comparative stats + extend beyond carbon-only to include the full LPJG output suite + produce multi-variable panel figures + difference maps).

### 1.5 Triad summary table

| Axis | Status at session 7 close | Effort to paper-grade |
|---|---|---|
| 1 — Anthro emissions | ✅ READY (existing intermediary_py scripts; review at paper-figure time) | ~0.5-1 day |
| 2 — IMOGEN atm conc vs literature | 🔄 PARTIAL (smoke validated; production-horizon extension awaits Track 2) | ~1-2 days |
| 3 — IMOGEN climate vs ISIMIP3b | ❌ NOT STARTED (predecessor `climate_comparison.py` to port + enhance) | ~3-5 days |
| 4 — Track 1 vs Track 2 LPJG ecosystem | ❌ NOT STARTED (predecessor `carbon_comparison.py` to port + enhance + extend) | ~4-7 days |
| **TOTAL** | — | **~8-15 days analyst-time** |

This is the post-Track-2-runs validation-triad workload. Compresses into ~1 calendar week if analyst-time is dedicated; more spread if interleaved with cluster + paper writing.

---

## 2. intermediary_py plotting scripts — inventory + paper relevance + readiness assessment

### 2.1 Full inventory (21 scripts)

| Component | Subdir | Scripts | Count | Paper section |
|---|---|---|---|---|
| Component A — anthropogenic | `historical/` | `ch4_ef`, `ch4_mm`, `ch4_rice`, `n2o_ms`, `n2o_mm`, `n2o_synfert` historical plotting | 6 | Methods (how each anthropogenic sector was modelled historically) |
| Component A — anthropogenic | `scenarios/` | `01_scenario_ch4_ef`, `02_scenario_ch4_mm`, `03_scenario_n2o_mm`, `04_scenario_n2o_synfert`, `05_scenario_n2o_ms`, `06_scenario_ch4_rice` plotting | 6 | Methods (how each anthropogenic sector was projected to 2100 per SSP) |
| Component A — anthropogenic | `rcmip_substitution/` | `rcmip_comparison1`, `rcmip_comparison2` plotting | 2 | Methods (shows that our RCMIP-substituted backbone differs from raw RCMIP; justifies the IPCC-Tier-1 refinement) |
| Component B — natural | `historical/` | `lpjg_historical` plotting | 1 | Methods (Component B historical natural-flux modelling) |
| Component B — natural | `full_trajectory/` | `lpjg_historical_scenario` plotting | 1 | Methods (Component B full 1900-2100 natural-flux trajectory) |
| Component C — integration | (root) | `integrated_emissions`, `conventional_comparator`, `external_comparators`, `hybrid_comparator` plotting | 4 | **Results (the integrated anthro + natural emissions plots feeding the IMOGEN engine; this is Axis 1's primary deliverable + a key novelty figure)** |
| Shared | `src/shared/` | `plot_style` | 1 | Styling utilities (Matplotlib defaults + paper-grade tweaks) |
| **TOTAL** | — | — | **21** | — |

### 2.2 Readiness-assessment plan (at paper-figure-generation time)

For each script in §2.1, the readiness review checks:

| Check | Pass criterion | Action if fail |
|---|---|---|
| Output figure size + DPI | ≥300 DPI, sized for GMD column-width (single 84mm or double 174mm) | Adjust `figsize` + `dpi` in `plot_style.py` or per-script overrides |
| Font sizes + weights | Readable at print scale (axis labels ~9pt; legend ~8pt; title ~10pt) | Adjust in `plot_style.py` |
| Color scheme | Colorblind-safe (e.g., viridis for sequential; ColorBrewer for categorical); GMD-conformant | Adjust palette in `plot_style.py` or per-script |
| Captions + annotations | Self-explanatory (no need to read body text to understand the figure) | Per-script enhancement |
| Citations on overlay | Reference values cited inline on the figure where applicable | Per-script enhancement |
| Time-series figures | Show uncertainty/envelope where applicable | Per-script enhancement; may require pulling envelope data |
| Map figures | Projection + coastlines + colorbar with units | Per-script enhancement |

**Expected outcome**: most scripts probably need minor styling tweaks; a few (especially the Component C integrated_emissions + comparators) may need substantive enhancement for paper-grade results-section figures.

**Real-time decision** (per user note: "we may be happy with what they do as-is, but we may also want to change some things to make sure they produce good publciation plots (but I doubt it)"): take the conservative path of running each script + assessing the output before deciding which need enhancement.

### 2.3 Audit-evidence bundle pattern

For each paper figure, bundle:
- The script invocation (full command line)
- The input data version (git SHA of intermediary_py / Track 2 outputs SHA)
- The output figure (PNG + PDF for vector reproducibility)
- A README in the figure dir documenting which paper section it lands in + caption draft + any enhancements applied

Suggested location: `paper/figures/<axis>_<figure_name>/`.

---

## 3. F-13 predecessor comparison scripts — porting + enhancement plan

### 3.1 Predecessor scripts inventory

Per `paper/README.md` lines 98-111 (user 2026-05-07 guidance) + my session-7-close reconnaissance:

| Predecessor script | Location (version_A; identical at version_B) | LOC | Paper axis | Status in rebuild |
|---|---|---|---|---|
| `carbon_comparison.py` | `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Python-scripts/comparative_analysis/analysis/carbon_comparison.py` | ~370 | Axis 4 (Track 1 vs Track 2 LPJG ecosystem) | NOT YET PORTED |
| `climate_comparison.py` | (same dir) | ~640 | Axis 3 (IMOGEN climate vs ISIMIP3b) | NOT YET PORTED |
| `preprocess_isimip_cache.py` | (same dir) | ~250 | Axis 3 supporting (preprocesses ISIMIP3b cache for climate_comparison consumer) | NOT YET PORTED |
| **TOTAL** | — | **~1260** | Axes 3 + 4 | F-13 deferred |

There are also (per `paper/README.md` lines 100-104) additional supporting materials in the predecessor: 12 example output dirs + 3 summary-table xlsx + a 23 MB PPTX context + a 15 KB synthesis markdown. These are reference materials for understanding the predecessor scripts' expected outputs + are worth reviewing at port time.

### 3.2 Porting strategy (proposed)

**Where to land in the rebuild repo**: probably `scripts/paper_validation/` (NEW subdir) or `intermediary_py/imogen_ghg_controller/src/paper_validation/` (if we want them under the existing python source tree).

Option proposal:
- **Option A — `scripts/paper_validation/`**: lives alongside `scripts/b19_phase4_literature_validate.py` (the existing validation script) + `scripts/run_coupled.sh` + `scripts/cluster/`. Keeps paper-stage code separate from the model-building intermediary_py. **My preliminary lean** for organizational clarity.
- **Option B — `intermediary_py/imogen_ghg_controller/src/paper_validation/`**: lives within the existing python tree, alongside the Component A/B/C subdirs. Reuses the existing intermediary_py module structure + import system. Useful if the comparison scripts depend on intermediary_py utilities.

Decision deferred to the porting session (post-Track-2-runs).

### 3.3 Minimum enhancements over predecessor (per `paper/README.md` lines 113-120)

The predecessor scripts have known gaps that should be filled during porting:

1. **Add comparative stats alongside the plots** (currently plots-only):
   - RMSE per grid cell + global mean
   - Bias (mean signed difference)
   - Mean + standard deviation per variable
   - Decadal-mean comparison tables
   - Interquartile range (IQR) for spread
   - Comparison vs published budgets where applicable (GCB 2025 / Saunois 2025 / Tian 2024 — i.e., the same literature the validation triad already references at Axis 2)
2. **Wire to v1.0's run-time outputs** (currently hard-coded to predecessor paths):
   - Path-flexibilify via CLI args + config file
   - Track 1 outputs path (cluster `/bg/data/lpj/.../Track1_outputs/`); Track 2 outputs path (cluster `/bg/data/lpj/.../Track2_outputs/`)
3. **Add v1.0-RCMIP-backbone vs IIASA-backbone comparison** (Axis 1 novel; not in template scripts):
   - The Axis 1 comparison is RCMIP-substituted vs RCMIP-raw; the predecessor was IIASA-backbone-only — needs new scripting for our novel backbone comparison
4. **Add the v1.0-paper-specific narrative annotations** to figures:
   - Cross-reference to validation outcomes (e.g., "WITHIN_ENVELOPE per Saunois 2020" badges)
   - Cite the canonical landing records (e.g., footnotes pointing to `notes/B19.md` + `notes/B20.md` for the validation evidence)
5. **Add reproducibility metadata** (git SHA; data version; environment) embedded in figure output

### 3.4 Porting effort estimate

| Script | Port-only effort (line-for-line adaptation) | Port + enhancement effort |
|---|---|---|
| `carbon_comparison.py` (~370 LOC → ~500-700 LOC enhanced) | ~1-2 days | ~3-5 days |
| `climate_comparison.py` (~640 LOC → ~800-1000 LOC enhanced) | ~2-3 days | ~4-7 days |
| `preprocess_isimip_cache.py` (~250 LOC → ~300-400 LOC enhanced) | ~0.5-1 day | ~1-2 days |
| New Axis 1 RCMIP-backbone comparison script | (new) | ~1-2 days |
| **TOTAL** | **~3.5-6 days port-only** | **~9-16 days port + enhancement** |

The enhancement work is substantial. Compresses to ~2 weeks calendar if analyst-time is dedicated.

---

## 4. Manuscript working draft — current state + revisions checklist

### 4.1 Current state

Per `paper/README.md` lines 14-20 + lines 122-149:

- **Location**: `version_A/.../References/IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`
- **Format**: Microsoft Word document (`.docx`)
- **Completeness**: **substantially incomplete** — only introduction + methods sections written; supervisor comments + edits applied to the methods section
- **Vintage**: pre-rebuild (predecessor IIASA-backbone framework era; before RCMIP backbone decision)

The intent (per `paper/README.md` lines 14-17) is to update the existing draft incrementally rather than rewriting from scratch. The methods + intro have a foundation; results + discussion + conclusion + complete references need to be authored.

### 4.2 Required revisions checklist (per `paper/README.md` lines 125-149)

For tracking + progress assessment:

| # | Section | Revision | Status | Owner | Effort |
|---|---|---|---|---|---|
| 1 | Methods | Replace "legacy IIASA-backbone via legacy intermediary" with "RCMIP/CMIP6 backbone via intermediary_py" (Decision #1) | NOT STARTED | post-Track-2 | ~1 day |
| 2 | Methods | Add two-IMOGEN-implementation strategy narrative (Fortran ALLOCATABLE base + C++ refactor switchable backend; Decision #2) | NOT STARTED | post-Track-2 | ~0.5 day |
| 3 | Methods | Add tight-coupling default narrative + F-10/F-12 architectural caveat honestly disclosed (Decision #4) | NOT STARTED | post-Track-2 | ~0.5 day |
| 4 | Methods | Add save_state/restart LU strategy narrative (Decision #10) | NOT STARTED | post-Track-2 | ~0.25 day |
| 5 | Methods | Add Tmin/Tmax IMOGEN computation narrative (Decision #11) | NOT STARTED | post-Track-2 | ~0.25 day |
| 6 | Methods | Add B40 §4 N2O sector-ownership-rule paragraph (clarifies that LPJG `N2O_SOIL` is N-deposition-influenced natural pathway aligned with Saikawa 2014 rather than Tian 2020 narrow; per `notes/B40.md` §4) | DRAFTED at B40 close; needs paper integration | post-Track-2 | ~0.25 day to integrate |
| 7 | Results | Add complete results section based on the 4-axis validation triad (per §1 above) | NOT STARTED | post-Track-2 + post-script-port | ~5-7 days |
| 8 | Discussion | Add discussion section including limitations (F-10 caveat; v1.0-vs-v2.0 scope split; PLUM embedding deferred per Decision #9; B45/B46 future cleanup) | NOT STARTED | post-results | ~2-3 days |
| 9 | Conclusion + References | Add conclusions section + complete references | NOT STARTED | post-discussion | ~1-2 days |
| 10 | Whole-paper | Final review + supervisor sign-off + GMD submission preparation | NOT STARTED | terminal | ~1 week |
| **TOTAL** | — | — | — | — | **~12-16 days post-Track-2** |

### 4.3 Draft revisions workflow (proposed)

| Phase | What | Mode | Coordination |
|---|---|---|---|
| Pre-Track-2 (parallel to cluster setup) | Items 1-6 (methods updates) — could start now since they're not data-dependent | Word `.docx` editing | User + supervisor review |
| During Track-2 runs (interleaved) | Items 1-6 finalised + reviewer-defensibility polish | Word `.docx` editing | User + supervisor review |
| Post-Track-2 + post-script-port | Item 7 (results section) | Word `.docx` + figure generation | User + supervisor review |
| Post-results | Item 8 (discussion) | Word `.docx` | User + supervisor review |
| Post-discussion | Item 9 (conclusion + references) | Word `.docx` | User + supervisor review |
| Pre-submission | Item 10 (final review + supervisor sign-off + GMD submission prep) | Word `.docx` + GMD submission template | User + supervisor + GMD editorial liaison |

### 4.4 Manuscript-to-rebuild-repo sync (post-step-18)

Per `paper/README.md` lines 12-25, the intended end state has:

```
paper/
├── manuscript_draft.docx                 (the working paper; updated to cite RCMIP/CMIP6 etc.)
├── figures/                              (figures produced for the paper; many = intermediary_py + Track 2 validation outputs)
├── references/                           (cited peer-reviewed PDFs)
├── methodology_revisions.md              (paper revisions made; rationale + dates)
└── supplementary/                        (supplementary tables, sensitivity analyses, validation plots)
```

The `paper/` subdir in the rebuild repo is currently empty (only `README.md`); populating it is part of paper-stage work + happens incrementally as the validation triad + figure generation + manuscript revisions proceed. Each addition gets its own commit + brief CHANGELOG entry.

---

## 5. Cross-references

- `paper/README.md` — canonical paper-stage doc (this document operationalises it)
- `notes/PRODUCTION_RUN_CONFIG.md` §5.3 — validation triad framing
- `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` — sibling document covering the runs that produce the outputs this document analyses
- `notes/FOLLOWUPS.md` F-13 — post-v1.0 paper-stage comparative-analysis framework (the central tracking record; full detail at FOLLOWUPS lines ~720+)
- `notes/B19.md` — closed-loop verification milestone (smoke-window Axis 2 validation; PASSED at Phase 4)
- `notes/B20.md` (via FOLLOWUPS) — LPJG-natural-flux literature validation (Saunois 2020 + Tian 2020 budgets WITHIN ENVELOPE)
- `notes/B40.md` §4 — N2O sector-ownership-rule paragraph drafted for paper methods inclusion (item #6 above)
- `intermediary_py/imogen_ghg_controller/src/component_{a,b,c}_*/...plotting.py` — 21 existing plotting scripts (Axis 1 + methods figures)
- `scripts/b19_phase4_literature_validate.py` — existing Axis 2 smoke-window validator (to be extended to full 1900-2100 for paper)
- `version_{A,B}/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Python-scripts/comparative_analysis/analysis/{climate_comparison,carbon_comparison,preprocess_isimip_cache}.py` — F-13 predecessor scripts (~1260 LOC; to port + enhance for Axes 3 + 4)
- Working manuscript draft: `version_A/.../References/IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`

---

## 6. Open items / questions for paper-stage work (append as they arise)

| # | Item | Surfaced | Owner | Resolution timing |
|---|---|---|---|---|
| 1 | Where to land the ported predecessor scripts: `scripts/paper_validation/` (Option A; preliminary lean) or `intermediary_py/.../src/paper_validation/` (Option B)? | session 7 close 2026-05-19 | porting session decision | post-Track-2 |
| 2 | Does the predecessor `climate_comparison.py` handle all 6+ climate variables the paper needs (T, P, SW, Rh, wind, DTR, possibly Tmin/Tmax), or is it carbon-related only? Need to read source at port time | session 7 close 2026-05-19 | porting session source-read | post-Track-2 |
| 3 | Does the predecessor `carbon_comparison.py` extend cleanly to non-carbon ecosystem variables (anpp, ngases, landcover, firert, nflux), or does it need substantial new code? Need to read source at port time | session 7 close 2026-05-19 | porting session source-read | post-Track-2 |
| 4 | B19 Phase 4 validation script extension: full 1900-2100 horizon + 5 SSPs + 3-species panel figures (CO2, CH4, N2O) — can be done with minor edits to existing `scripts/b19_phase4_literature_validate.py`, OR needs a new paper-stage script? | session 7 close 2026-05-19 | post-Track-2 decision | post-Track-2 |
| 5 | Post-B39 CO2 trajectory at 2050 ~472.872 ppm at upper end of SSP1-2.6 published peak range (~430-470 ppm per IPCC AR6) — flagged at B44 acceptance test; whether the SSP1-2.6 mid-/end-century trajectory shape is paper-defensible is a separate validation question that the Axis 2 production-horizon extension will surface clearly | session 7 close 2026-05-19 (B44 acceptance flag); user-flagged as Rule #9 honest disclosure | post-Track-2 Axis 2 paper figure | post-Track-2 |
| 6 | Manuscript revisions items 1-6 (methods updates) — could potentially START NOW pre-Track-2 since they're not data-dependent (Decision #1/#2/#4/#10/#11 narrative + B40 §4 paragraph integration). Is the user ready to do this work in parallel with cluster setup, or wait until post-Track-2? | session 7 close 2026-05-19 | session 8+ user decision | session 8+ |
| 7 | Working manuscript draft is a `.docx` file (Word); the rebuild repo would benefit from a plaintext / Markdown / LaTeX version for git tracking + diff-ability. Consider conversion to LaTeX at some point | session 7 close 2026-05-19 | optional; deferred to paper-completion late-stage | terminal phase |
| 8 | GMD submission requirements: latest GMD template; supplementary materials format; reproducibility checklist; data + code DOI requirements (Zenodo? Figshare?) | session 7 close 2026-05-19 | check at terminal phase | terminal phase |

(Append new items as discoveries surface.)

---

_End of `notes/PAPER_COMPLETION_AND_VALIDATION.md` v0.1 — initial draft 2026-05-19 evening session 7 close; iteratively updated through validation triad execution + paper writing work._
