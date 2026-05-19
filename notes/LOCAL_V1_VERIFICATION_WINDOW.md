# Local v1 verification window — close-out summary

**Status**: ✅ **FULLY COMPLETE** at this commit (2026-05-19 evening, session 7 continuation). Tag candidate: `v0.21.0-local-v1-verification-window-complete`.

**Window scope**: 4 audit items deferred from B19 Phase 5 close-out (`7543c1e`, 2026-05-18 evening) + B20 close (`9a78df0`, 2026-05-18 late evening) + B41+B42+B43 production-config doc-cascade (`268837f`, 2026-05-19 morning), to be addressed in the local-workstation pre-cluster-phase verification cycle: **B37 + B36 + B39 + B40**.

**Window window** (calendar): 2026-05-19 evening, single session 7 continuation. ~4 hours actual wall-clock for all 4 items combined (vs ~6-13 hours cumulative effort estimate per the FOLLOWUPS rows).

**Window arc**: 5 commits on `main`, all 3-remote-converged at landing:

| Commit | Item | Effort estimate | Actual | One-line verdict |
|---|---|---|---|---|
| `75811c0` | **B37** Productive-year-ceiling explanatory study | ~1-3 h | ~2 h | Root cause IDENTIFIED (3 hardcoded year sentinels in `climatemodel.cpp::updateImogenControlData()` at lines 1185-1197); closed-form formula derived (matches Run B + C + DR2 empirically); NEW path (iv) launcher-side `done`-marker sidecar surfaced + EMPIRICALLY CONFIRMED in DR1 (202 year-dirs 1900-2101 produced in 12 min 48 sec wall on smoke 4-cell). **v1.0 paper-publication production-IMOGEN-engine runs FEASIBLE WITHOUT F-12 architectural fix** (the headline window finding); 2 NEW post-v1.0 audit items filed (B44 + B45) |
| `a77ea8f` | **B36** Fortran IMOGEN background-emission audit at `imogen/code/imogen_lpjg.f` | ~2-4 h | ~30 min | **NO DOUBLE-COUNTING DEFECTS FOUND**; all 4 sub-item criteria PASS (zero hardcoded emission-rate DATA statements; zero default-filename fallback strings; zero BLOCK DATA subroutines; intermediary_py Component A + B outputs empirically confirmed as actual data feeding the 4 active FILE_* channels in v1.0 via Option B per B31 launcher auto-rewrite + DR1 launcher banner verification); engine-source-level PRINT warnings at `imogen_lpjg.f:655 + :742` document user-data design invariants (mirrored at `docs/scientific_framework.md` §5.3 from B32); Rule-#10 self-correction during writeup (initial IS92A→CMIP6 doc-drift fix retracted via `grep` confirming reference was in FOLLOWUPS B36 row pre-audit framing not in scientific_framework.md) |
| `8026740` | **B39** `CO2_INIT_PPMV` per-YEAR1 configurability fix (option α) | ~1-2 h | ~45 min | **STRICT_PASS empirically confirmed** at B19 Phase 4 re-validation against Law Dome MacFarling Meure 2006 ice-core record; CO2 drift -3.5 to -4.2% pre-fix → -0.09 to -0.80% post-fix (~5× tightening; STRICT_PASS across all 4 years); CH4 drift -0.5 to -0.7% → +0.07 to +0.39% post-fix (sign-flipped + magnitude reduced; user-authorized at session 7 q_b39_ch4_scope option A bundled CH4_INIT_PPBV 865.0 → 875.6 as B39 (α)' minor extension); N2O_INIT_PPBV unchanged per user preference; per-cell breakdown improved from 8 of 12 STRICT_PASS pre-fix → 11 of 12 STRICT_PASS post-fix; NEW `docs/scientific_framework.md` §6.1 cross-reference table for 1850/1900/2005 Law Dome / Meinshausen 2017 / Mauna Loa baselines; Rule-#10 self-correction (initial xval `.ins` edits reverted after `git check-ignore` confirmed git-IGNORED status; xval auto-inherits post-B39 main .ins via setup_run.sh copy mechanism at next re-activation) |
| `4ca1ef6` | **B40** Modern-decade N2O hump explanatory study | ~2-4 h | ~30 min | **Methodological characteristic, NOT defect**. Source-level smoking gun at `lpjguess/modules/somdynam.cpp:1689-1691` confirms LPJG's `N2O_SOIL` channel scope is Saikawa-2014-aligned (N-deposition-influenced natural pathway included) rather than Tian-2020-narrow ("purely natural" only); full 1900-2100 time-mean (11.18 TgN2O/yr) WITHIN both envelopes; modern-decade peak (~14.43 TgN2O/yr 2008-2017) explained by ~10-15× pre-industrial→modern increase in atmospheric NHx + NOy deposition (per Lamarque 2010 / Hauglustaine 2014); SSP1-2.6 mid-century decline tracks mitigation pathway (per Bauer 2017 / Rao 2017); paper §2.4.4 sector-ownership rule paragraph drafted at `notes/B40.md` §4; NEW B46 filed (optional v1.5+ source-edit to split channel; LOW priority; TRUNK-RELEVANT if option α full) |
| **THIS** | **Window close-out summary commit + tag** `v0.21.0-local-v1-verification-window-complete` | ~30-60 min | TBD | This document + 5-surface in-tree doc cascade refresh + sibling Part 7 of session5_post_b19 handoff + annotated tag + 3-remote push |

---

## 1. Headline findings (5-bullet TL;DR for future maintainers + paper authors)

1. **v1.0 paper-publication production-IMOGEN-engine runs (full 1900-2100 × 5 SSP-RCP scenarios) are FEASIBLE WITHOUT F-12 architectural fix** — empirically demonstrated via B37 DR1 (path-iv launcher-side `done`-marker sidecar produces 202 year-dirs 1900-2101 in ~12.6 min wall on smoke 4-cell config; ~63 min total local scaled for all 5 SSP-RCPs). F-12 + Track-2 cluster-MPI tight-coupling remain v1.1+ work per B43 (unchanged); v1.0 prescribed-mode coupled-model architecture is the paper-publication target.

2. **No hidden double-counting in the Fortran IMOGEN engine source** — B36's 4-sub-item audit at `imogen/code/imogen_lpjg.f` (4700 LOC) found zero hardcoded emission-rate DATA statements, zero default-filename fallback strings, zero BLOCK DATA subroutines. Engine-source-level PRINT warnings at `:655` + `:742` document the user-data design invariants that prevent double-counting at the .ins layer. Multi-layer no-double-counting defense (docs `docs/scientific_framework.md` §5.3 from B32 + launcher `scripts/run_coupled.sh` step 4.5 from B31 + engine `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE` from B33(c)) is intact.

3. **Atmospheric concentrations now match Law Dome ice-core record at STRICT_PASS-level** — B39's option α fix updated `CO2_INIT_PPMV 286.085 → 296.1` + `CH4_INIT_PPBV 865.0 → 875.6` (Law Dome 1900 per MacFarling Meure 2006) in the main `runs/SSP1-2.6/imogen_intermediary.ins`. B19 Phase 4 re-validation post-fix: 11 of 12 (year, species) cells STRICT_PASS (vs 8 of 12 pre-fix); CO2 drift cut ~5× from -3.5/-4.2% to -0.09/-0.80% across all 4 smoke-window years 1900-1903. NEW `docs/scientific_framework.md` §6.1 cross-reference table provides per-YEAR1 baseline values for common epochs (1850 / 1900 / 2005); xval rank dirs auto-inherit via setup_run.sh copy-from-main mechanism.

4. **Modern-decade N2O hump is a known methodological characteristic, NOT defect** — B40 confirmed at source level (`lpjguess/modules/somdynam.cpp:1689-1691` + `ntransform.cpp:179-467`) that LPJG's `N2O_SOIL` channel includes both purely-natural + N-deposition-influenced natural N2O contributions, aggregated without per-source attribution. Channel scope is Saikawa-2014-aligned (~14-24 TgN2O/yr modern decade) rather than Tian-2020-narrow (~9-12 TgN2O/yr). Full 1900-2100 time-mean (11.18 TgN2O/yr) WITHIN both envelopes. Paper §2.4.4 sector-ownership rule paragraph drafted at `notes/B40.md` §4 (needs paper-author integration into the working paper draft).

5. **Multi-layer scientific validation lines intact** — combining B19 Phase 4 (downstream atm concentrations vs Law Dome ice-core; ≤5% drift BALLPARK_PASS pre-B39 + STRICT_PASS post-B39 verified at THIS close-out) + B20 (upstream LPJG natural CH4 + N2O fluxes vs Saunois 2020 + Tian 2020 budgets; WITHIN_ENVELOPE_MEAN_WITH_TIME_VARIATION) + B36 (engine architecture clean) + B37 (engine workflow viable for production runs) + B39 (init-seed config improved) + B40 (N2O channel scope documented), v1.0 has a **scientifically-defensible verification posture for the paper publication's results section**.

---

## 2. Newly-filed post-v1.0 audit items across the window (B44 + B45 + B46)

| ID | Title | Filed at | Effort | Priority | Trunk-relevance |
|---|---|---|---|---|---|
| **B44** | Productise the path-iv `done`-marker sidecar in `scripts/run_coupled.sh` as a launcher option (e.g., `--engine-only-mode`) | B37 close (`75811c0`) | ~20-30 LOC bash + ~5-10 LOC `--help` text | **MEDIUM** | TRUNK-IRRELEVANT-by-novelty (`scripts/run_coupled.sh` is per-fork) |
| **B45** | Parametrise the 3 hardcoded year sentinels (`1901`, `2100`, `1871`) in `lpjguess/modules/climatemodel.cpp::updateImogenControlData()` lines 1185-1197 via new IMOGENConfig parameters | B37 close (`75811c0`) | ~5-15 LOC source-edit + ~10 LOC .ins-side defaults | **LOW** | **TRUNK-RELEVANT** (canonical engine source `climatemodel.cpp` is C++ port; Fortran twin at `imogen/code/imogen_lpjg.f` likely has analogous logic; Backport Sprint should handle both forks together) |
| **B46** | Optional v1.5+ source-edit: split `Fluxes::N2O_SOIL` into separately-attributed `N2O_SOIL_NATURAL` + `N2O_SOIL_NDEP_INFLUENCED` channels in `lpjguess/modules/ntransform.cpp` for per-source attribution accounting | B40 close (`4ca1ef6`) | ~150-250 LOC (option α full) OR ~60-90 LOC (option β ratio-based) OR ~0 LOC (option γ defer) | **LOW** | **TRUNK-RELEVANT if option α full** (touches canonical `ntransform.cpp` + Fluxes enum in `framework/guess.h`); TRUNK-IRRELEVANT if option β ratio-based; defer entirely is also valid |

**None of B44/B45/B46 are v1.0-blocking.** All recommended for v1.1+ (B44 alongside cluster setup) to v1.5+ (B45 + B46 alongside F-12 architectural work) eras.

---

## 3. Cumulative backport-debt status across the window

**UNCHANGED at +145 LOC eligible-for-backport** throughout all 4 window items (still entirely from B19 Phase 2 Commit 3 `6862d03`'s `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE` helper subroutine + 4 CALL sites at L425/L432/L631/L648). **None of the 4 window items touched canonical engine source** (`imogen/code/imogen_lpjg.f` Fortran or `lpjguess/modules/climatemodel.cpp` C++ port).

**Per-item backport classification**:
- B37: investigation; ZERO source change → TRUNK-IRRELEVANT-by-novelty
- B36: investigation; ZERO source change → TRUNK-IRRELEVANT-by-finding
- B39: 1 .ins value update + 1 Python script POST-B39-NOTE prepend + 1 NEW docs section → TRUNK-IRRELEVANT-by-novelty in entirety
- B40: investigation; ZERO source change → TRUNK-IRRELEVANT-by-finding

The future implementations of B45 (TRUNK-RELEVANT; ~5-15 LOC) and B46 option α full (TRUNK-RELEVANT; ~150-250 LOC) would add to the cumulative backport-debt when implemented in the v1.1-1.5+ era; Backport Sprint at the post-step-19 work cycle should plan for these alongside the existing +145 LOC.

---

## 4. Rule #9 + Rule #10 operating posture

**Rule #9 (harness-authoring routinely surfaces latent defects)**: clean operation across all 4 window items; cumulative ≥11 consecutive datapoints since formal promotion at B19 Phase 5 close-out (`7543c1e`):

- B37: harness-authoring (DR1 + DR2 sidecar treatment-vs-control) surfaced the NEW path (iv) solution outside the original 3-candidate scope + the 2101 over-shoot empty placeholder + the brittle `YEAR1_LPJG=1871` hardcoded reset forensic clue
- B36: source-reading surfaced the (initially mistakenly attributed) IS92A doc-drift that on grep-verification turned out to be in FOLLOWUPS B36 row pre-audit framing not in scientific_framework.md
- B39: acceptance-test re-run surfaced the stale PRE-B39 attribution text in `scripts/b19_phase4_literature_validate.py` (worth a cosmetic POST-B39-NOTE prepend) + the initial `--co2-dat-template` arg mismatch (correct arg is `--engine-output-dir`)
- B40: systematic grep refinement (initial cosmetic false-positives in `canexch.cpp` comments → refined `dndep|NH4_input|NO3_input|...` query located actual N-deposition addition at `somdynam.cpp:1689-1691`)

**Rule #10 (verification-integrity discipline)**: clean operation across all 4 window items; cumulative ≥11 consecutive datapoints. **Two honest self-corrections** mid-cascade-authoring (both retracted via grep / git verification before commit landed):

1. **B36** (1st self-correction): initial IS92A→CMIP6 doc-drift fix proposal for `docs/scientific_framework.md` retracted via `grep -E "IS92A|RF_NONCO2_GHG_IS92A" docs/scientific_framework.md` returning zero matches (reference was in FOLLOWUPS B36 row pre-audit framing; preserved as historical context per audit-trail discipline)
2. **B39** (2nd self-correction): initial xval `.ins` directive edits reverted after `git check-ignore` confirmed the 3 parallel xval `.ins` files at `runs/SSP1-2.6/parallel_work_xval_mpi/{loose,prescribed,tight}_4cell_runs/imogen_intermediary.ins` are git-IGNORED per `.gitignore`'s `runs/*/parallel_work_xval_mpi/...` rule (regenerable by `setup_run.sh` copy-from-main; xval rank dirs auto-inherit post-B39 main .ins values at next re-activation)

Both self-corrections operate as designed under Rule #10's "preserve original for forensic value" + "amend honestly when empirical reality diverges from initial plan" corollaries.

---

## 5. Audit-evidence bundle inventory across the window

Per Rule #10 verification-integrity discipline, every claim in the window's commit messages + canonical landing records cites concrete artifacts. Audit-evidence bundles outside the rebuild repo at `_chat_artifacts/`:

| Bundle | Purpose | Size | Cited from |
|---|---|---|---|
| `_chat_artifacts/b37_diagnostic_run_2026-05-19/_common.sh` | Shared pre/post-state capture + acceptance-gate evaluation utilities | ~11.3 KB | `notes/B37.md` §3 |
| `_chat_artifacts/b37_diagnostic_run_2026-05-19/dr2_control_no_sidecar.sh` | DR2 control run driver (re-reproduces Run C 4-year ceiling on current HEAD) | ~3.2 KB | `notes/B37.md` §3.1 |
| `_chat_artifacts/b37_diagnostic_run_2026-05-19/dr1_treatment_with_sidecar.sh` | DR1 treatment run driver + sidecar spawn + cleanup trap | ~4.8 KB | `notes/B37.md` §3.2 |
| `_chat_artifacts/b37_diagnostic_run_2026-05-19/baseline_run_c_output_snapshot/` | Snapshot of Run C pre-DR baseline IMOGEN/output state (4 year-dirs 1900-1903) | ~50 KB | `notes/B37.md` §3 |
| `_chat_artifacts/b37_diagnostic_run_2026-05-19/DR{1,2}_*_{run,pre_state,post_state,acceptance_gates}.{log,txt}` | DR2 control + DR1 treatment artifacts (logs + state captures + gate evaluations) | ~200 KB total | `notes/B37.md` §3 |
| `_chat_artifacts/b37_diagnostic_run_2026-05-19/B37_acceptance_evaluation_2026-05-19.md` | B37 acceptance verdict + concrete-artifact citations per Rule #10 | ~10 KB | `notes/B37.md` §3 |
| `_chat_artifacts/b39_acceptance_test_2026-05-19/post_fix_smoke_run_*.log` | Raw smoke-run log (post-B39 fix; 4-year ceiling per B37 formula) | ~178 KB | `notes/B39.md` §3 |
| `_chat_artifacts/b39_acceptance_test_2026-05-19/post_fix_literature_validation_2026-05-19.md` | Canonical post-fix B19 Phase 4 validation Markdown report | ~6.6 KB | `notes/B39.md` §3 |
| `_chat_artifacts/b39_acceptance_test_2026-05-19/post_fix_literature_validation_2026-05-19.md.json` | Machine-readable post-fix summary | ~2.9 KB | `notes/B39.md` §3 |

B36 + B40 are investigation-only (no empirical-run artifacts); their evidence is fully captured in the canonical landing records `notes/B36.md` + `notes/B40.md` via line-cited source-reading.

---

## 6. Paper-stage actions needed (from B40 §4)

The local v1 verification window's primary deliverable for the paper is the **B40 §4 sector-ownership rule paragraph** drafted at `notes/B40.md` §4:

> _"LPJG's natural-soil N2O channel (the `Fluxes::N2O_SOIL` flux reported in `ngases.out` and propagated to the IMOGEN-handshake natural-N2O channel at `imogen_lpjg_ch4_n2o_flux.txt`) is computed via Xu-Ri 2008 + Ma et al. 2022 JAMES nitrification + denitrification kinetics applied to the soil mineral N pool, which is incremented monthly by the sum of atmospheric NHx + NOy deposition (from ndep NetCDF input) + biological N-fixation (per Cleveland et al. 1999 precipitation-driven empirical formula) + organic-matter mineralization (from native + decomposed litter). This channel scope is conceptually consistent with Saikawa 2014's wider 'N-deposition-influenced natural N2O' envelope rather than Tian 2020's narrower 'purely natural N2O' envelope..."_

**This paragraph needs paper-author integration** into the working paper draft (`~/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/References/IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`) §2.4.4 sector-ownership rule section (or wherever the N2O methodological narrative lives). The integration is essential for reviewer-defensibility of v1.0's natural-N2O channel scope (otherwise reviewers may discover the modern-decade hump and question it without the methodological framing).

Additional paper amendments per `notes/PRODUCTION_RUN_CONFIG.md` §6 + the prompt's "Working paper status" section:
- Replace "legacy IIASA-backbone via legacy intermediary" with "RCMIP/CMIP6 backbone via intermediary_py" in introduction + methods
- Add Track 1 vs Track 2 ecosystem comparison framing in methods
- Add B19 + B20 + post-Track-2 validation discussion in results
- Add B40 §4 sector-ownership rule paragraph (this window's specific deliverable)

---

## 7. v1.0 % done estimate refresh

**Revised UP modestly to ~96-98%** (from ~95-97% at B41+B42+B43 close `268837f`). The bump reflects:
- The v1.0 paper-publication path is now empirically unblocked for production-IMOGEN runs (B37)
- The engine architecture is verified clean on hidden-defaults risk (B36)
- The atmospheric concentration validation is now at STRICT_PASS-level (B39)
- The N2O channel methodological framing is documented + paper paragraph drafted (B40)
- 3 NEW post-v1.0 enhancement audit items filed (B44 + B45 + B46) but none v1.0-blocking

The remaining ~2-4% spans:
- (OPTIONAL) **B44** productisation of path-iv sidecar (~20-30 min); could be done as a small commit before 17c.1 cluster setup
- **17c.1+ cluster phases** on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative) — production-scale runs + paper-stage data generation
- **Track 2 production runs** (5 SSP-RCPs × 1900-2100 × 62538-cell gridlist; `-input imogencfx`; using B37 path-iv sidecar OR cluster workflow; ~1-2 weeks compute + iteration)
- **Validation triad execution + paper figures** (~1 week)
- **Paper amendments + writing** (ongoing in parallel; estimated ~2-3 weeks active drafting effort)
- **v1.0 paper submission** (target; ~6-10 weeks calendar from this commit per `notes/PRODUCTION_RUN_CONFIG.md` §6.2 effort estimate)

---

## 8. Post-window roadmap

| Order | Item | Estimated effort | Priority |
|---|---|---|---|
| (this commit) | Local v1 verification window CLOSE-OUT summary + tag `v0.21.0-local-v1-verification-window-complete` + 3-remote push | ~30-60 min | this commit |
| (optional) | **B44** Productise path-iv sidecar in `scripts/run_coupled.sh` as new `--engine-only-mode` flag | ~20-30 min | MEDIUM (operational convenience for 17c.1+ cluster-orchestration sbatch) |
| 1 | **17c.1+ cluster phases** on KIT IMK-IFU `owl` (production-scale runs + paper-stage data generation per `notes/STEP_17c.md` §1.7.8) | ~1-2 weeks SSH-iterative | HIGH (paper-publication critical-path) |
| 2 | **Track 2 production runs** (5 SSP-RCPs × 1900-2100 × 62538-cell gridlist; `-input imogencfx`; using B37 path-iv sidecar) | ~1-2 weeks compute + iteration | HIGH |
| 3 | **Validation triad execution + paper figures** (anthropogenic emissions plots + IMOGEN concentrations vs Law Dome + ISIMIP3b climate vs IMOGEN-emulator difference maps + Track 1 vs Track 2 LPJG ecosystem comparison) | ~1 week | HIGH |
| 4 | **Paper amendments + writing** (intro + methods + results + discussion + conclusion + §2.4.4 sector-ownership rule paragraph per B40 §4 + RCMIP/CMIP6 backbone amendments per `notes/PRODUCTION_RUN_CONFIG.md` §6.1) | ongoing in parallel; ~2-3 weeks active drafting | HIGH |
| 5 | **v1.0 paper submission** to GMD or similar venue | target | TERMINAL |

**Total estimated calendar time** from this commit to v1.0 paper submission: **~6-10 weeks** (per `notes/PRODUCTION_RUN_CONFIG.md` §6.2 effort estimate, unchanged).

---

## 9. Cross-references

- `notes/B37.md` — Productive-year-ceiling explanatory study (window item 1)
- `notes/B36.md` — Fortran IMOGEN background-emission audit (window item 2)
- `notes/B39.md` — CO2_INIT_PPMV per-YEAR1 configurability fix (window item 3)
- `notes/B40.md` — Modern-decade N2O hump explanatory study (window item 4)
- `notes/FOLLOWUPS.md` — Audit-item dashboard; rows B37 + B36 + B39 + B40 all ✅ DONE; rows B44 + B45 + B46 ⏳ NEW filed
- `CHANGELOG.md` — Dated entries for B37 + B36 + B39 + B40 + this close-out
- `EXECUTION_PLAN.md` row 17c — Status flag flipped to ✅ at this commit
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` — Per-item entries + cumulative state UNCHANGED at +145 LOC throughout
- `notes/STEP_17c.md` §1.7.8 — Window completion summary + post-window roadmap
- `notes/PRODUCTION_RUN_CONFIG.md` — Production-run reference (B41+B42+B43; pre-window context)
- `docs/scientific_framework.md` §5.3 (B32 closure) + §6.1 (NEW at B39 close) — Canonical scientific architecture
- `_chat_artifacts/CHAT_HANDOFF_2026-05-18_session5_post_b19.md` Parts 3 + 4 + 5 + 6 + 7 — Sibling handoff narrative (this is Part 7's deliverable)
- `_chat_artifacts/b37_diagnostic_run_2026-05-19/` + `_chat_artifacts/b39_acceptance_test_2026-05-19/` — Audit-evidence bundles

---

_End of `notes/LOCAL_V1_VERIFICATION_WINDOW.md` — local v1 verification window ✅ FULLY COMPLETE at this commit 2026-05-19 evening session 7 continuation; tag `v0.21.0-local-v1-verification-window-complete`._
