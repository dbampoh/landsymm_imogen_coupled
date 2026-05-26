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

**✅ HYBRID-PRE-BAKED ARCHITECTURE CLARIFICATION + .INS-CONFIG-ALIGNMENT REFINEMENT (2026-05-20 session 8.0.3 follow-up exchange; ~6:25 PM Rule #10 self-correction + ~7:12 PM user-confirmed .ins-config-alignment specifics; post block 8.0.3 acceptance close)**: v1.0 paper coupling is NOT "purely prescribed" as my prior over-statement framed it (~6:10 PM in same exchange) — it is **hybrid pre-baked**: intermediary_py merges CMIP6/SSP-RCP/EDGAR/RCMIP/FAO anthropogenic emissions WITH **pre-baked offline trunk_r13078 LPJG-natural-emission outputs** (`inputs/lpjg/{historical,scenarios/ssp*}/lpjg_{cflux,mch4,ngases}.out_*.gz`; ~1.5 GB total; 62,538 cells × 120 years historical + 80 years × 5 SSP-RCPs; one-shot inputs from prior trunk_r13078 production runs) into IMOGEN-format emission inputs. **Per user-confirmed .ins-config-alignment refinement (2026-05-20 ~7:12 PM session 8.0.3 follow-up)**: the bedrock LPJG runs (STEP 1; that produced the `inputs/lpjg/*.gz` natural-emission inputs to intermediary_py) use **near-exact same .ins configuration as Track 2 LPJG production runs** (STEP 4; `forks/trunk_r13078/` post T_seq Installment-1 source-edit) — same gridlist (62,538 cells = `gridlist_in_62892_and_climate.txt`), same `_peatland` LU forcing (HILDA+ v2 + cropfracs + nfert + later irrigation in scenarios), same 4-NetCDF wet/dry NHx+NOy ndep, same popdens (population-density_3b_2015soc), same SimFire BLAZE fire model + ifcalccton/ifcalcsla N-cycle settings, same trunk_r13078 vintage. **The SOLE differential** between bedrock (STEP 1) and Track 2 (STEP 4) is the climate + CO2 driver: STEP 1 used ISIMIP3b MRI-ESM2-0 climate + ISIMIP3b prescribed CO2 (standard `-input cfx`); STEP 4 uses IMOGEN-derived climate + IMOGEN-derived per-year CO2 trajectory (`-input imogencfx` post T_seq). **This is a methodologically clean controlled experiment** — Track 1 vs Track 2 (where Track 1 ≡ STEP 1 bedrock LPJG runs in terms of .ins config + climate driver) genuinely isolates the IMOGEN-coupling effect on simulated ecosystem responses as the only experimental variable. **Implication for Axis 4 design strength**: BOTH Track 1 AND Track 2 trace back to **THE SAME pre-baked LPJG-natural-emission inputs** at intermediary_py's upstream — therefore any Track 1 vs Track 2 ecosystem-output difference is attributable purely to the IMOGEN-coupling (climate + CO2 trajectory) and NOT to differences in natural-emission inputs upstream of IMOGEN. **v1.0 → v1.1+ transition framing** is NOT "prescribed-mode → tight-coupling" but rather "offline pre-baked LPJG-natural ingestion → live per-year LPJG↔intermediary_py↔IMOGEN handshake" (F-12 v1.1+; trunk_r13078 stays at backport-fork-parity per `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §1.1; rebuild's `lpj-guess_imogen_landsymm/lpjguess/` becomes the live-handshake fork at v1.1+; intermediary_py keeps anthropogenic-emissions handling in v1.1+ — only natural-emissions handling moves out into the live LPJG↔IMOGEN loop). **Honest residual caveat (Rule #10; NON-blocking for v1.0 publication)**: Track 2 LPJG's internal natural-flux outputs (mch4.out + ngases.out + cflux.out from STEP 4) differ slightly from STEP 1 bedrock natural-flux outputs that fed intermediary_py — because Track 2 uses IMOGEN-derived climate while STEP 1 used ISIMIP3b MRI-ESM2-0 climate; this is a known limitation of offline pre-baked coupling, NOT a self-consistency claim in v1.0; v1.1+ resolves it by closing the loop. **See §4.5 below for the suggested Paper Methods §2.2 draft text** that frames this architecture for paper authoring; **see NEW B50 + B51 at `notes/FOLLOWUPS.md`** for companion doc-review work (scientific_framework.md §5+§6 review + Supplementary Materials provenance documentation). The original §1.4 text below remains correct in claiming LPJG-version-held-constant (T_seq design); the .ins-config-alignment refinement strengthens the experimental-design framing.

**✅ STRATEGIC CAVEAT RESOLVED at session 8.0 C5 (2026-05-20 afternoon) per `notes/B47.md`**: the strategic question raised at session 7 close — whether Track 2 should run on the rebuild's later-4.1-base (Option R) or `trunk_r13078` minimally updated (Option T) for paper-reviewer-defensibility — has been **resolved in favor of Option T_seq** (sequential-standalone with minimal trunk_r13078 backport in two installments). **Axis 4 validation now isolates climate driver as the only variable** between Track 1 (`trunk_r13078` + `-input cfx` + ISIMIP3b MRI-ESM2-0 climate) and Track 2 (`forks/trunk_r13078/` + T_seq Installment-1 source-edit + `-input imogencfx` + rebuild-IMOGEN-engine-derived climate); both tracks run on the same LPJG version with identical auxiliaries (LU, popdens, ndep, SimFire, soilmap). The Methods narrative for the paper §2.4.3 sector-ownership rule + the validation triad presentation in §3 should explicitly cite this LPJG-version-held-constant design choice as the methodologically clean variant of the comparison. **The original session-7-close preliminary "~150-300 LOC; few-hour to ~1-day" estimate was Rule-#10 over-optimistic when interpreted as in-process T1/T2 (actual ~1300-1600 LOC) but is just-right under T_seq sequential-standalone framing (~180-310 LOC Installment-1 source-edit); honest re-baselining preserved at `notes/B47.md` §2-§4 + `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §0.2 (resolution banner). The original preliminary text is preserved verbatim below for forensic continuity per Rule #10 amendment-vs-rewrite corollary.**

_Preserved preliminary caveat (session 7 close 2026-05-19 12:53 AM)_: this Axis 4 framing tacitly assumes Track 2 uses the rebuild repo's LPJ-GUESS. For paper-reviewer-defensibility, Track 1 vs Track 2 is much cleaner if LPJG version is held constant — i.e., Track 2 also runs on `trunk_r13078` (the version that produced Track 1) with minimalist backport from the rebuild rather than the rebuild's later-4.1-base. The session 8.0 strategic decision per `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §0.2 (Option R vs Option T) materially affects this Axis 4 validation interpretation. Preliminary recommendation: Option T (trunk_r13078 minimally updated; ~150-300 LOC backport; Track 1 vs Track 2 isolates climate driver as the only variable; cleaner paper story); subject to session 8.0 C0-C5 verification.

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

### 4.5.1 Block 8.1.5 addendum — engine identity + regrid-strategy clarification for Paper Methods §2.2 (2026-05-22 session 9 day 3)

> **✅ ENGINE IDENTITY + REGRID-STRATEGY ADDENDUM**: per block 8.1.5 findings (§1+§12+§13 of `_chat_artifacts/b8_1_5_architectural_clarification_2026-05-22/B8_1_5_architectural_clarification_findings_2026-05-22.md`), the v1.0 paper Methods §2.2 SHOULD explicitly note: (1) the IMOGEN engine implementation used is the C++ port embedded in LPJ-GUESS (`climatemodel.cpp::RUN_IMOGEN_ENGINE()`), which produces climate on IMOGEN's native 1631-point pattern grid; (2) for v1.0 production runs, the **Option δ-B switchable-regrid-strategy** uses the standalone Fortran IMOGEN with `REGRID=TRUE` + `NGPOINTS=3698` to produce 3698-grid climate, which is then regridded to the full 62892-cell LPJG gridlist via FastRegrid (inverse-distance-weighted interpolation) — matching the predecessor coupled-model architecture for apples-to-apples Axis 4 validation; (3) the v1.1+ trajectory includes porting the REGRID branch to the C++ port (and optionally switching to the IMOGENCXX C++ engine backport per B52) for a unified in-process architecture. **Also** add a sentence in the Discussion §5 v1.1+ outlook on the IMOGENCXX C++ backport (B52) + switchable-regrid-strategy (β/δ-A/δ-B) as future work extending the coupling framework.

### 4.5 Paper Methods §2.2 draft text — v1.0 prescribed-mode coupling architecture (drafted at session 8.0.3 follow-up; 2026-05-20 ~7:12 PM; **POST-BLOCK-8.2 honest-disclosure refinement 2026-05-23 session 10 day 1 close; POST-BLOCK-8.2.4 trunk-engine-throughout tightening 2026-05-26 session 11 day 2 close**)

#### 4.5.0 POST-BLOCK-8.2.4 trunk-engine-throughout framing (2026-05-26; LOCKED IN per block 8.2.4 byte-identity verification)

> **✅ TRUNK-ENGINE-THROUGHOUT FRAMING LOCKED IN** at block 8.2.4 close (2026-05-26 session 11 day 2). Block 8.2.4 forward-ported the engine-side slice of LEDGER §1.2 Installment-2 (~1300 LOC) into `forks/trunk_r13078/`, bringing trunk's C++ IMOGEN engine to **functional byte-identity** with rebuild's lpjguess engine. Trunk's freshly-built `build_b824/guess` binary produced all 5 SSP engine libraries at `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/` (5 × 443 MB = ~2.2 GB; 1900-2101). **Phase G byte-identity verification: 250/250 ✅ md5 matches** (5 SSPs × 5 sentinel years × 10 climate variables) between trunk's NEW engine output and rebuild's lpjguess-engine reference. CO2 trajectory values numerically match exactly (SSP1-2.6 2100 = 427.62 ppm peak-then-decline; SSP2-4.5 = 590.815; SSP3-7.0 = 826.34; SSP4-6.0 = 631.473; SSP5-8.5 = 1092.59; all within IPCC AR6 / Friedlingstein 2025 GCB ranges). **B61 ✅ CLOSED** at this block. Full evidence at `_chat_artifacts/b8_2_4_trunk_engine_forwardport_2026-05-24/B8_2_4_evaluation_2026-05-26.md`.

> **Methodological argument LOCKED IN**: "`trunk_r13078` throughout — engine + LPJG + natural-emission preprocessor — with rebuild's lpjguess as the active v1+ development surface." This satisfies paper-reviewer-defensibility concerns about fork-consistency between Track 1 (ISIMIP3b-forced trunk_r13078 LPJG) and Track 2 (IMOGEN-forced trunk_r13078 LPJG) without requiring full bidirectional fork-parity (which is the v1+ Installment-2 Backport Sprint target; ~1300 LOC residual: year_outer scaffolding + imogen_input.{cpp,h} + Fortran B33(c) — not paper-blocking).

> **Paper Methods §2.2 (CANONICAL; LOCKED IN at block 8.2.4 close)**:

```
## Methods §2.2 — Coupled-model architecture for v1.0 Track 2 production runs

Both Track 1 (ISIMIP3b-forced trunk_r13078 LPJG runs) and Track 2 (IMOGEN-forced
trunk_r13078 LPJG runs) use the **same LPJG ecosystem-model fork**
(`forks/trunk_r13078/`), ensuring a clean differential isolating climate-driver
source as the experimental variable.

The IMOGEN engine producing Track 2's climate library is the **C++ port located
in `forks/trunk_r13078/modules/`**, brought to functional byte-identity with
the rebuild's lpjguess engine port at block 8.2.4 (2026-05-26). The forward-port
brings the engine-side slice of the trunk-rebuild fork-parity reconciliation
(~1300 LOC: climatemodel.cpp + imogenoutput.{cpp,h} NEW + imogencfx.cpp
non-year_outer slice + parameters.{cpp,h} engine-side declarations + CMakeLists.txt
build wiring). Byte-identity of the trunk-engine vs rebuild-engine climate
libraries was verified across all 5 SSP-RCP scenarios × 5 sentinel years
(1900, 1950, 2000, 2050, 2100) × 10 climate variables (T_anom, P_anom, SW_anom,
DTEMP_anom, Rh_anom, W_anom, Tmin_anom, Tmax_anom, WET, CO2) = 250/250 md5
byte-identity matches per `_chat_artifacts/b8_2_4_trunk_engine_forwardport_
2026-05-24/B8_2_4_evaluation_2026-05-26.md` §1.6.

The natural-emission processing in intermediary_py uses pre-baked offline
`trunk_r13078` LPJG output (`intermediary_py/imogen_ghg_controller/inputs/lpjg/`
~1.5 GB; from prior trunk_r13078 production runs), ensuring engine + ecosystem
model + natural-emission preprocessor are all on the same fork lineage. The
rebuild fork (`lpj-guess_imogen_landsymm/lpjguess/`) serves as the active v1+
development surface; full bidirectional fork-parity reconciliation including
the `imogen_input.cpp` consumer-side delta + `year_outer` framework scaffolding
+ Fortran `imogen_lpjg.f` B33(c) deltas is the post-paper Installment-2
Backport Sprint target (~1300 LOC residual).

The IMOGEN engine consumes anthropogenic emissions (CO2, CH4, N2O) from the
intermediary_py pipeline (RCMIP-backboned; CMIP6-SSP-RCP scenarios), CMIP6
non-CO2 radiative forcing inputs (`imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/
nonco2_ch4_n2o_RF_historical_ssp<TAG>.txt` per SSP), and pre-baked offline
trunk_r13078 LPJG natural-emission outputs. The engine performs pattern-scaling
using **CMIP6 MRI-ESM2-0 GCM patterns** (`imogen/patterns/CEN_CMIP6_MOD_MRI-
ESM2-0/`; converted from `imogen/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/
mri-esm2-0_patterns.nc` per step 5 of the rebuild plan). Initial atmospheric
concentrations follow Law Dome 1900 ice-core record (MacFarling Meure 2006;
296.1 ppm CO2 / 875.6 ppb CH4 / 277.4 ppb N2O) per B39.

CO2 trajectories produced by the engine are physically sensible per IPCC AR6
/ Friedlingstein 2025 GCB published ranges across all 5 SSPs (Table M-§2.2-1):
SSP1-2.6 2100 = 427.62 ppm (peak-then-decline; ~430 ppm IPCC AR6 expected);
SSP2-4.5 = 590.815 ppm (~590 ppm); SSP3-7.0 = 826.34 ppm (~830 ppm); SSP4-6.0
= 631.473 ppm (~630 ppm); SSP5-8.5 = 1092.59 ppm (~1090 ppm).

For Track 2 production runs, the per-SSP climate library at
`forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/` (1900-2101;
202 year-dirs × ~443 MB) is regridded from IMOGEN's native 1631-point pattern
grid to the LPJG 62,892-cell production gridlist via chained FastRegrid
(nearest-neighbor 1631→3698 + inverse-distance-weighted 3698→62892); the
regridded library is then consumed by trunk_r13078's LPJG (`forks/trunk_r13078/
build_owl/guess -input imogencfx`) on the KIT IMK-IFU `owl` cluster
(2 nodes × 128 CPUs/node = 256 ranks on `genius` partition; ~5-15 hours total
wall across 5 SSP-RCPs × 62538 cells × 1900-2100).
```

#### 4.5.-1 PRIOR Methods §2.2 framing (block 8.2 honest-disclosure refinement 2026-05-23; SUPERSEDED by §4.5.0 above per Rule #10 amendment-vs-rewrite)

The Methods §2.2 framing below (drafted at block 8.2 close per session 10 day 1) was authored under the architectural state where rebuild's lpjguess engine produced the climate library at `runs/<SSP>/Common-directory/IMOGEN/output/` which was cp'd to `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/` at block 8.2 Phase E (γ-physical separation; same data; different filesystem location matching the LPJG consumer fork). Block 8.2.4 (2026-05-26) brought trunk's own engine to byte-identity with rebuild's, making the γ-physical-cp framing OBSOLETE: trunk's NEW engine now produces its own libraries at `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/`; rebuild's engine output at `runs/<SSP>/` remains as redundant cross-validation reference. The "honest disclosure" framing below is preserved per Rule #10 amendment-vs-rewrite for forensic continuity; the canonical Methods §2.2 is now §4.5.0 above.

(Original block 8.2 honest-disclosure refinement preserved verbatim below; superseded by §4.5.0)

### 4.5.-2 ORIGINAL Block 8.2 honest-disclosure refinement (2026-05-23 session 10 day 1 close; SUPERSEDED)

**Status**: ⏳ DRAFT — authored at session 8.0.3 follow-up exchange in conversation with user; deposited here for sessions 11-12 paper-writing phase to pick up + refine. Per Rule #10 amendment-vs-rewrite corollary, this draft text is the cumulative refinement post §1.4 HYBRID-PRE-BAKED ARCHITECTURE CLARIFICATION + .ins-config-alignment refinement (both 2026-05-20 same exchange) + **POST-BLOCK-8.2 honest-disclosure refinement** (2026-05-23 session 10 day 1 close — discloses that v1.0 Track 2 uses rebuild's improved C++ IMOGEN engine library cp'd to trunk-runs side rather than trunk's own engine, because of climatemodel.cpp non-byte-identity between forks per NEW B61).

> **POST-BLOCK-8.2 honest-disclosure addendum** (per **Rule #10 datapoint #23** + NEW B61 filing 2026-05-23 session 10 day 1 close):
>
> The Methods §2.2 draft text below was authored assuming that `forks/trunk_r13078/modules/climatemodel.cpp` (trunk-T_seq LPJG-consumer side) was byte-identical to `lpjguess/modules/climatemodel.cpp` (rebuild engine side), which would have meant trunk's binary's engine producing byte-identical engine output to rebuild's. That assumption is FALSE: the two `climatemodel.cpp` files differ (`md5sum` differs; ~263 LOC divergence per LEDGER §1.2 Installment-2 estimate per NEW B61). Rebuild's `lpjguess/modules/climatemodel.cpp` has step-7 polling guards + step-8 imogenoutput integration + step-9.5 Tmin/Tmax/Rh/W writers + step-17a engine writer fix + step-17a skip_inprocess_engine_run + B19/B37/B39/B44/B45 deltas; trunk's `forks/trunk_r13078/modules/climatemodel.cpp` is pre-rebuild-deltas baseline.
>
> **Implication for paper Methods §2.2 framing**: at v1.0 paper Track 2, the trunk-T_seq LPJG-consumer side reads pre-baked engine library produced by **rebuild's improved C++ engine** (not trunk's older engine; physically cp'd to trunk-runs/<SSP>/Common-directory/IMOGEN/ at block 8.2 phase E). This matches **T_seq design intent per `notes/B47.md` §4** ("Step A: rebuild engine standalone produces climate library; Step B: SCP/cp to trunk-runs side; Step C: trunk-T_seq LPJG consumes pre-baked library"). The trunk binary's own engine is not exercised at v1.0; would produce inferior output until v1+ Installment-2 backport reconciles climatemodel.cpp divergence (~2-4 d source-edit at v1+ Backport Sprint; resolves B61).
>
> **Honest framing for paper Methods §2.2**: "Track 2 of the validation framework uses the rebuild's C++ IMOGEN engine (lpjguess/modules/climatemodel.cpp; with step-7/8/9.5/17a + B19/B37/B39/B44/B45 path-iv done-marker mechanism + 8-field climate writers + B39 Law Dome 1900 init seeds + skip_inprocess_engine_run flag) to produce the per-SSP climate library at `runs/<SSP>/Common-directory/IMOGEN/output/`. The library is physically cp'd to `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/` (γ-physical separation; cluster-deployment-ready; one Common-directory per fork). The trunk-T_seq LPJG (forks/trunk_r13078/build/guess; with Installment-1 backport per `notes/B47.md` + LEDGER §1.1) then consumes this pre-baked library on cluster as a pure consumer (skip_inprocess_engine_run=1 in trunk-runs/<SSP>/main.ins; engine bypassed; LPJG main loop runs in T_seq sequential-standalone mode). This design choice — using rebuild's improved engine library across both Track 1 (rebuild) + Track 2 (trunk-T_seq LPJG consumer) — ensures (i) operational engine + emissions consistency between tracks (only differential is LPJG binary version: trunk's tested production code vs rebuild's evolving development code); (ii) LPJG fork-version consistency for Track 1 vs Track 2 ecosystem-output comparison; (iii) acceptable v1.0 paper scope vs the post-paper Installment-2 backport which will reconcile trunk's climatemodel.cpp to match rebuild's, enabling future v1.1+ runs where trunk's own engine produces independent climate libraries (deferred future work; see NEW B61 in `notes/FOLLOWUPS.md`)."

**Authoring rationale**: The user explicitly asked at session 8.0.3 follow-up whether the v1.0 prescribed-mode setup is scientifically justified for the paper, and confirmed the .ins-config-alignment specifics between bedrock LPJG runs (STEP 1) and Track 2 LPJG runs (STEP 4). Assistant confirmed YES with reference to standard ESM coupling practice (Burke et al. 2017 / Hartin et al. 2015 / Bondeau et al. 2007 / Smith et al. 2014 / Pongratz et al. 2018 / Stocker et al. 2013 / ScenarioMIP+CMIP6 emissions-driven runs). Resulting Methods draft text captured here for paper authoring at sessions 11-12 paper-writing phase.

**Drafted text (~paper §2.2 candidate; suitable for direct paste-and-refine into manuscript)**:

> **§2.2 Coupling architecture (v1.0 prescribed-mode + offline pre-baked LPJ-GUESS natural emissions)**
>
> The v1.0 LandSyMM-IMOGEN-LPJ-GUESS coupled model implements a **one-shot offline-driven approximation of tight coupling**. Anthropogenic emissions of CO₂, CH₄, and N₂O are derived from FAOSTAT historical bulk-download datasets (Crops, Livestock, Fertilizers; FAO 2024) for the 1900–2014 historical period and from PLUMv2 (Engström et al. 2017; Alexander et al. 2018) activity-data projections (livestock counts, crop area, irrigation amounts) for 2015–2100 across five Shared Socioeconomic Pathway / Representative Concentration Pathway (SSP-RCP) scenarios (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5). EDGAR sector inventories (v8.0; Crippa et al. 2024) provide benchmark cross-validation and within-period sector-total proportioning, and RCMIP Phase 2 emissions (Nicholls et al. 2020) supply the FAIR-ERF natural baseline (Smith et al. 2024). Natural greenhouse gas fluxes (net land-atmosphere carbon flux, wetland CH₄, soil N₂O) are derived from prior offline production runs of the trunk_r13078 revision of LPJ-GUESS (Smith et al. 2014; Lindeskog et al. 2013) covering 62,538 land grid cells × 120 years of historical (1900–2014) plus 80 years per SSP-RCP scenario (2015–2100), driven by ISIMIP3b MRI-ESM2-0 climate forcing (Frieler et al. 2017; Yukimoto et al. 2019) with prescribed CO₂ trajectories (Meinshausen et al. 2017). These anthropogenic and natural emission components are merged in the intermediary_py emissions pipeline — a Python orchestrator that performs Component A (anthropogenic-sector emissions estimation from activity data) and Component B (natural-flux ingestion from offline LPJ-GUESS) — and provided as inputs to the IMOGEN climate-emulator engine (implemented in this work's `lpjguess/modules/climatemodel.cpp` per the C++ port of the original Cox et al. 2013 / Huntingford et al. 2013 IMOGEN Fortran code; FAIR-based carbon cycle per Smith et al. 2018 and energy-balance climate emulation per Huntingford and Cox 2000). IMOGEN produces per-year atmospheric GHG concentrations (CO₂, CH₄, N₂O) and an eight-field climate library (monthly mean temperature, precipitation, shortwave radiation, diurnal temperature range, relative humidity, surface wind speed, daily minimum and maximum temperature, monthly wet-day fraction) for the 1900–2101 period at the 62,538-cell global half-degree grid resolution.
>
> This climate and CO₂ library then drives the Track 2 LPJ-GUESS production runs (`forks/trunk_r13078/` with T_seq Installment-1 minimal source-edit applied per the Code Availability section; specifically the `skip_inprocess_engine_run` flag enabling sequential-standalone consumption of the pre-baked IMOGEN climate library + the eight-field B4-wiring backport from this work's rebuild for Rh/Wind/Tmin/Tmax climate-field consumption + a Kelvin-to-Celsius conversion at the temperature-physics interface), using **identical .ins configuration to the bedrock natural-emission-source runs above**: same 62,538-cell gridlist (`gridlist_in_62892_and_climate.txt`), BLAZE fire model (Rabin et al. 2017) with population-density-driven ignition forcing (Klein Goldewijk et al. 2017), `_peatland` land-use forcing (HILDA+ v2 cropland/grassland/forest/urban + cropfracs + nfert; historical from Winkler et al. 2021, scenarios from PLUM-harmonized HILDA+ projections), four-NetCDF wet/dry NHx + NOy nitrogen deposition forcing (ISIMIP3b histsoc + ssp*soc protocol), ifcalccton and ifcalcsla N-cycle settings, and the LandSyMM crop-N stand-type list with N0/N60/N200/N1000 fertilization-treatment partitioning (Olin et al. 2015). The sole differential between bedrock (Track 1 / STEP 1) and Track 2 (STEP 4) is the climate + CO₂ driver — Track 1 uses ISIMIP3b MRI-ESM2-0 climate with prescribed CO₂; Track 2 uses IMOGEN-derived climate with IMOGEN-derived per-year CO₂ trajectory. This **methodologically clean controlled experimental design** isolates the IMOGEN-coupling effect on simulated ecosystem responses as the only experimental variable in the Track 1 vs Track 2 comparison (§3.4 Axis 4 validation).
>
> We emphasize that the v1.0 architecture is an **offline-driven approximation of tight coupling**: Track 2 LPJ-GUESS does not feed its computed natural fluxes back into the IMOGEN engine at runtime. Track 2's internal natural-flux outputs (mch4.out, ngases.out, cflux.out) therefore differ slightly from the bedrock natural fluxes that fed intermediary_py (because the climate driver differs between bedrock and Track 2 LPJG runs; see §5 Discussion for quantitative discussion of this offset). Full per-year LPJ-GUESS↔IMOGEN handshake closure (replacing the offline pre-baked natural-emission ingestion with live runtime coupling, with intermediary_py retaining its anthropogenic-emissions role while natural-emission ingestion moves into the live handshake) requires architectural refactoring tracked as planned future development items F-10 (in-process IMOGEN engine MPI deadlock resolution under tight-coupling case-α) and F-12 (LandSyMM-LPJ-GUESS↔IMOGEN tight-coupling protocol design and implementation). These tight-coupling enhancements are explicitly out of scope for v1.0 and constitute the primary v1.1+ development trajectory discussed in §5 Discussion. The v1.0 architecture validated here demonstrates that the coupling infrastructure functions end-to-end at production scale (62,538 cells × 200 years × five SSP-RCPs), and provides a clean experimental baseline against which v1.1+ live-coupling results can be assessed for self-consistency improvements.

**References cited (drafting placeholders; verify + complete at paper-writing phase)**:
- Alexander, P., et al. (2018). Adaptation of global land use and management intensity to changes in climate and atmospheric carbon dioxide. _Global Change Biology_, 24, 2791-2809.
- Bondeau, A., et al. (2007). Modelling the role of agriculture for the 20th century global terrestrial carbon balance. _Global Change Biology_, 13, 679-706.
- Burke, E. J., et al. (2017). Quantifying uncertainties of permafrost carbon-climate feedbacks. _Biogeosciences_, 14, 3051-3066.
- Cox, P. M., et al. (2013). Sensitivity of tropical carbon to climate change constrained by carbon dioxide variability. _Nature_, 494, 341-344.
- Crippa, M., et al. (2024). EDGAR v8.0 Global Greenhouse Gas Emissions. _Earth System Science Data_, 16, [v8.0 release].
- Engström, K., et al. (2017). Assessing uncertainties in global cropland futures using a conditional probabilistic modelling framework. _Earth System Dynamics_, 8, 357-376.
- FAO (2024). FAOSTAT statistical database. Food and Agriculture Organization of the United Nations.
- Frieler, K., et al. (2017). Assessing the impacts of 1.5°C global warming – simulation protocol of ISIMIP2b. _Geoscientific Model Development_, 10, 4321-4345.
- Hartin, C. A., et al. (2015). A simple object-oriented and open-source model for scientific and policy analyses of the global climate system – Hector v1.0. _Geoscientific Model Development_, 8, 939-955.
- Huntingford, C., and Cox, P. M. (2000). An analogue model to derive additional climate change scenarios from existing GCM simulations. _Climate Dynamics_, 16, 575-586.
- Huntingford, C., et al. (2013). Simulated resilience of tropical rainforests to CO₂-induced climate change. _Nature Geoscience_, 6, 268-273.
- Klein Goldewijk, K., et al. (2017). Anthropogenic land use estimates for the Holocene – HYDE 3.2. _Earth System Science Data_, 9, 927-953.
- Lindeskog, M., et al. (2013). Implications of accounting for land use in simulations of ecosystem carbon cycling in Africa. _Earth System Dynamics_, 4, 385-407.
- Meinshausen, M., et al. (2017). Historical greenhouse gas concentrations for climate modelling (CMIP6). _Geoscientific Model Development_, 10, 2057-2116.
- Nicholls, Z. R. J., et al. (2020). Reduced complexity model intercomparison project Phase 1: Introduction and evaluation of global-mean temperature response. _Geoscientific Model Development_, 13, 5175-5190.
- Olin, S., et al. (2015). Modelling the response of yields and tissue C:N to changes in atmospheric CO₂ and N management. _Biogeosciences_, 12, 7449-7474.
- Pongratz, J., et al. (2018). Models meet data: Challenges and opportunities in implementing land management in Earth system models. _Global Change Biology_, 24, 1470-1487.
- Rabin, S. S., et al. (2017). The Fire Modeling Intercomparison Project (FireMIP). _Geoscientific Model Development_, 10, 1175-1197.
- Smith, B., et al. (2014). Implications of incorporating N cycling and N limitations on primary production in an individual-based dynamic vegetation model. _Biogeosciences_, 11, 2027-2054.
- Smith, C. J., et al. (2018). FAIR v1.3: a simple emissions-based impulse response and carbon cycle model. _Geoscientific Model Development_, 11, 2273-2297.
- Smith, C. J., et al. (2024). FAIR v2 [version specifier]. [journal TBD].
- Stocker, B. D., et al. (2013). Multiple greenhouse-gas feedbacks from the land biosphere under future climate change scenarios. _Nature Climate Change_, 3, 666-672.
- Winkler, K., et al. (2021). Global land use changes are four times greater than previously estimated. _Nature Communications_, 12, 2501.
- Yukimoto, S., et al. (2019). The Meteorological Research Institute Earth System Model version 2.0, MRI-ESM2.0. _Journal of the Meteorological Society of Japan_, 97, 931-965.

**Cross-references for paper-writing phase**:
- `notes/B47.md` §clarification — Rule #10 self-correction context; T_seq design rationale
- `notes/FOLLOWUPS.md` B50 row — companion `docs/scientific_framework.md` §5+§6 review work
- `notes/FOLLOWUPS.md` B51 row — `inputs/lpjg/*.gz` provenance documentation (Supplementary Materials)
- `intermediary_py/imogen_ghg_controller/inputs/README.md` — concise current documentation of intermediary_py inputs structure
- `forks/trunk_r13078_runs/SSP1-2.6/main.ins` — canonical Track 2 .ins config (post-T_seq Installment-1)
- `forks/trunk_r13078_runs/SSP1-2.6/imogen_intermediary.ins` — IMOGEN engine + B39 Law Dome 1900 atm-conc seed values
- `notes/PRODUCTION_RUN_CONFIG.md` §2.1-§2.3 — production-knob inventory (BLAZE + LandSyMM crop + ndep + popdens + `_peatland` LU)
- `_chat_artifacts/b47_tseq_acceptance_4cell_2026-05-20/B47_tseq_acceptance_evaluation_2026-05-20.md` — block 8.0.3 acceptance test evidence + physical sensibility tables

**Items to verify at paper-writing phase**:
1. **PLUMv2 publication citation** — confirm Engström et al. 2017 + Alexander et al. 2018 are the canonical citations for the activity-data version used in `inputs/plum/plum_crop_s1.csv` + `Livestock_counts.txt`
2. **trunk_r13078 vintage citation** — establish whether the prior LPJ-GUESS runs that produced `inputs/lpjg/*.gz` cite Smith et al. 2014 only OR also Lindeskog et al. 2013 + Olin et al. 2015 (crop-N) — depends on which LandSyMM crop-treatment vintage was used; check with original modeler (relates to B51)
3. **EDGAR version specifier** — confirm v8.0 is correct; verify Crippa et al. 2024 publication date + journal
4. **IMOGEN engine citation chain** — Cox et al. 2013 (carbon sensitivity) + Huntingford et al. 2013 (resilience) are the typical paired cites; verify with IMOGEN repo + Chris Huntingford's preferred citation
5. **FAIR version specifier** — FAIR v2.x (Smith et al. 2024) vs FAIR v1.3 (Smith et al. 2018) — depends on which is wired into intermediary_py; check `intermediary_py/imogen_ghg_controller/` source
6. **ISIMIP3b protocol citation** — Frieler et al. 2017 is the ISIMIP2b paper; check whether ISIMIP3b has its own protocol paper (likely yes); verify
7. **MRI-ESM2-0 citation** — Yukimoto et al. 2019 is correct; verify version specifier (MRI-ESM2.0 vs MRI-ESM2-0)
8. **`_peatland` LU dataset citation** — depends on whether this is from HILDA+ v2 (Winkler 2021) + custom peat masking OR from another source; check with original modeler

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
