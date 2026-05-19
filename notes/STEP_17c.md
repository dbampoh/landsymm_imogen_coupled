# STEP 17c — F-12 sub-milestone C3 (HPC cluster integration tests on KIT IMK-IFU `owl`)

**Date opened:** 2026-05-12 (session 3)

**Date 17c.0 PREP B15+B16 forensic record landed:** 2026-05-12 (commit `2beff31`; un-tagged checkpoint)

**Date 17c.0 PREP B15 fix + signal-of-life assertion landed (sub-phases 17c.0.1 + 17c.0.2):** 2026-05-13 (this commit; un-tagged checkpoint)

**Date 17c.0 PREP four-xval re-verification (year_outer actually exercised) landed:** 2026-05-13 (this commit; bundled with 17c.0.1 per §1; 1cell scenarios PASS substantive + signal-of-life clean; 4cell scenarios surface B16 as anticipated per §0.8 verification gate 4 + §0.9)

**Date 17c.0 PREP B16 forensic + fix landed (sub-phase 17c.0.3):** 2026-05-13 (this commit; un-tagged checkpoint)

**Date 17c.0 PREP B17 forensic surface from gates 7+8 controlled-fail recorded:** 2026-05-13 (this commit; B17 forensic landed as new §3; B17 fix deferred to NEXT sub-phase 17c.0.4)

**Date 17c.0 PREP B17 forensic deep-dive + B17(a) fix landed (sub-phase 17c.0.4):** 2026-05-13 evening (this commit; un-tagged checkpoint; B17(a) CLOSED via harness sort-then-diff in `scripts/cross_validate_year_outer.sh::compare_outputs()` per §3.6 option (a1); empirical Phase-A forensic deep-dive falsified §3.4 hypothesis 1 (FP-summation roundoff) and §3.4 hypothesis 2 (global RNG state) and reclassified B17(b) as **stochastic-process sensitivity per cell-iteration-order RNG slip** with new §3.8 forensic; B17(b) DECISION (α tolerance-based comparison vs β seed-tracking root-cause investigation) deferred to NEXT sub-phase 17c.0.5)

**Date 17c.0 PREP B17(b) operational acceptance at provisional 2% tolerance landed (sub-phase 17c.0.4 FOLLOW-UP, doc-only):** 2026-05-13 night (commit `2771939`; 3-remote-converged at `origin/main`/`kit/main`/`helmholtz/main`; SUPERSEDES the original 17c.0.5 (α/β decision) plan with a lighter-touch provisional-acceptance per new §3.8.5; formal Option α/β closure deferred to a future sub-phase TBD reactivated only on a §3.8.5 re-evaluation trigger per §3.8.5.5)

**Date 17c.0 PREP four-xval re-verification on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD landed (sub-phase 17c.0.5; collapsed-renumbering convention adopted per §3.8.5):** 2026-05-13 night-late (this commit; un-tagged checkpoint; full gates 1-8 re-verify on `2771939` HEAD all pass with byte-identical envelope to 17c.0.4 — gates 1+2 binary sha256 unchanged → no source change since `4d09b62`; gates 3+4 25/25 162/162 PASS both builds; gates 5+6 1cell xval PASS exit 0 with 37/37 raw BIT_EXACT; gates 7+8 4cell xval CONTROLLED-FAIL exit 2 with 15+5+17 envelope identical to 17c.0.4 + LOOSE-vs-TIGHT manifest BYTE-IDENTICAL confirming B17(b) is coupling-invariant; +10/-5 LOC `scripts/cross_validate_year_outer.sh` stale-reference cleanup post-collapsed-renumbering rolled in at 4 surgical sites — see §1.5)

**Date 17c.0 PREP workstation `mpirun -np 4` mimic verified (deferred-from-C2 obligation):** 2026-05-15 (sub-phase 17c.0.7; this commit; tagged `v0.17.7-step17c-mpi-4rank-mimic` post-merge; numbering preserved from 17c.0.4 era — renumbered from 17c.0.6 in 17c.0.3 commit to make room for B17-fix sub-phase; the post-17c.0.4-followup collapsed renumbering preserved 17c.0.7 since 17c.0.5 = verification took the originally-deferred slot; **verifies LPJG-side handshake-file write path (stage 1 of the 8-stage coupled pipeline) under workstation `mpirun -np 4` for all 3 coupling modes (loose, prescribed, tight); intermediary_py + IMOGEN engine round-trip stages 2-7 are scoped as B19 cluster-phase prerequisite cross-linked to already-planned steps 11/13/19**; sub-phase ALSO landed an unanticipated handshake-file write-path defect fix (Path α: `DIR_COMMON` must be set in the .ins file for the C++-side `LPJG_main/IMOGEN/` subdirectory creation in `imogenoutput.cpp:140-142` to land in a writable per-mode-isolated location — pre-fix the default empty `DIR_COMMON` caused `mkdir` to attempt `/LPJG_main/IMOGEN/` which fails permission-check at runtime; the xval harness `scripts/cross_validate_mpi_4rank.sh` was updated to inject `DIR_COMMON "<absolute-path>"` for non-loose modes via the wrapper-writer functions `write_baseline_wrapper()` + `write_mpi_wrapper()`; pre-existing `imogen_intermediary.ins` consumers were unaffected because that .ins sets `DIR_COMMON` already; the xval setup was the only consumer that bypassed it — this is a fix-by-defensive-injection at the harness layer rather than a fix at the C++ engine layer because making `DIR_COMMON` mandatory in the engine would break legacy A/B run setups; full Path α forensic in §3.10 of this file; **EMPIRICALLY CONFIRMS** that `MPI_Allreduce(MPI_SUM)` over 4 doubles produces bit-exact results between single-process and 4-rank runs for this specific MPICH implementation and cardinality — adds confidence to `flush_year_globally_synchronized` correctness beyond the unit-test surface); ALSO landed 5 LOC of unit doc-comment clarifications in `lpjguess/framework/guess.h` (N2O_FIRE, N2O_SOIL, N2_FIRE, NH3_SOIL, NO_SOIL — all sibling N-cycle flux types previously had no unit comments) + ~8 LOC of comment-clarity cleanup in `lpjguess/modules/imogenoutput.cpp:75-79` (N2O_PER_N constant; same numerical conversion 44/28; clearer wording removing the misleading "28 g/mol N2 basis" phrasing) — both surfaced through user Q&A on unit verification post-Path-α-handshake-file-content-inspection; these tiny clarifications are TRUNK-RELEVANT for the guess.h edits (the units are inherent to the N-cycle pool budget convention; the comment was simply missing) and TRUNK-IRRELEVANT-by-novelty for the imogenoutput.cpp edit (imogenoutput.cpp is a step-8 addition with no trunk analog))

**Date 17c.0 PREP B17(b) MECHANICAL CLOSURE landed via spinup_year_idx formula correction (sub-phase 17c.0.6; user-authorised PROACTIVE REVISIT per §3.8.5.5 5th cadence bullet PERMITTED-REACTIVATION surface, exercised 2026-05-14 night → 2026-05-15 early morning session 4 continuation; BUNDLED with C2 close-out tag annotation amendment in same commit/push event per user-authorised recommended-path 2026-05-15 ~01:44 UTC+2):** 2026-05-15 (this commit; un-tagged checkpoint above `e03ceb1`; tagged `v0.17.6-step17c-b17b-closure` post-merge; **B17(b) reclassified from "stochastic-process sensitivity per cell-iteration-order RNG slip" + "PROVISIONALLY ACCEPTED at 2% cell-total tolerance per §3.8.5" → "MECHANICALLY CLOSED at 17c.0.6 via 4-LOC surgical correction of the closed-form `spinup_year_idx` reproduction formula in `lpjguess/modules/imogen_input.cpp` + `lpjguess/modules/imogencfx.cpp` per new §3.8.6"**; root cause was an incorrect closed-form formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` derived in `notes/STEP_17a.md` §5.4 based on a false assumption that `spinup_year_idx` persists across cells in gridcell_outer mode — the actual code in both ImogenInput::getgridcell() at `imogen_input.cpp:880` AND IMOGENCFXInput::getgridcell() at `imogencfx.cpp:1122` RESETS `spinup_year_idx = 0` at the start of every cell, making the per-cell behavior depend ONLY on `year_idx % NYEAR_SPINUP`; the spurious `cell_idx * nyear_spinup` term introduced a per-cell offset that gridcell_outer doesn't have, causing cell c (c >= 1) in year_outer to use spinup imogen_years shifted by c*nyear_spinup positions; cell 0 was bit-exact pre-fix because cell_idx=0 zeroes the spurious term — also the reason 1cell xval false-positive-PASSED through the entire 17c.0.1+ era; full 8-gate verification CONFIRMS mechanical closure: gates 1+2 build/+build_mpi/ rebuild PASS exit 0 (incremental, both .cpp recompiled, both binaries re-linked); gates 3+4 unit tests 162/162 / 25 cases both builds PASS; gates 5+6 1cell xval 37/37 raw BIT_EXACT exit 0 (regression-clean — predicted from cell_idx=0 zeroes spurious term); **gates 7+8 4cell xval `15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER + 0 NaN + banner_a=0 + banner_b=5` exit 0 IDENTICAL between LOOSE (gate 7) and TIGHT (gate 8) coupling — the 17 previously-SORTED_DIFFER per-PFT-total + tot_runoff files are now ALL SORTED_EXACT (data identical between modes after row-order normalization); the residual difference is pure B17(a) row-emission-order which is the documented harness-side normalization, NOT model-state divergence**; the previously-attributed "stochastic-process sensitivity" hypothesis is mechanically falsified — B17(b) was a deterministic implementation defect, not stochastic noise; the §3.8.5 provisional acceptance is RETIRED; the §3.8.5.5 re-evaluation cadence (FORCED + PERMITTED reactivation surfaces) is RETIRED-with-honour-of-success-having-fired-once on the PERMITTED surface; the LOOSE-vs-TIGHT identical envelope mechanically confirms the §3.8.3 "coupling-invariance of B17(b)" finding because both input modules had the IDENTICAL bug pattern in 4 symmetric closed-form formula sites — see §3.8.6 for the canonical forensic narrative)

**Date 17c.0 PREP C2 close-out tag annotation amendment landed:** 2026-05-15 (this commit; (a)-refined approach: `v0.17.5-step17b-c2-mpi-sync` annotation amended in place at `f6c192e` to reflect post-B15 + post-B17(a) + post-B17(b)-mechanical-closure verification status, preserving original annotation text within the new updated message for forensic completeness; SHA `f6c192e` preserved per (a) approach choice; tag annotation message now reflects that B17(b) was MECHANICALLY CLOSED at 17c.0.6 via the spinup_year_idx formula correction rather than the previously-recorded "PROVISIONALLY ACCEPTED at 2%" status)

**Date deferred future sub-phase TBD landed (formal Option α tolerance-based comparison OR Option β seed-tracking root-cause for B17(b) closure):** _RETIRED-SUPERSEDED_ (the entire deferred-sub-phase mechanism was originally created to gate Option α/β against §3.8.5 re-evaluation triggers firing; B17(b) is now MECHANICALLY CLOSED at 17c.0.6 via §3.8.6 root-cause fix without needing either Option α or Option β; the deferred sub-phase TBD slot is therefore retired-with-honour-of-no-longer-being-needed; the FORCED-reactivation surface (4 §3.8.5 triggers) is RETIRED because the underlying drift no longer exists; the PERMITTED-reactivation surface (proactive revisit at user discretion per §3.8.5.5 5th cadence bullet) FIRED ONCE successfully — the 2026-05-14 night → 2026-05-15 early morning proactive revisit is the realisation of that surface and yielded the §3.8.6 mechanical closure; both surfaces are now RETIRED in the sense that the B17(b) audit item itself is CLOSED rather than the surfaces being abandoned mid-life)

**Date 17c.0 PREP close-out landed (sub-phase 17c.0.8; FINAL PREP sub-phase):** 2026-05-15 night (this commit; tagged `v0.17.8-step17c-prep-complete` post-merge; **Step 17c.0 PREP phase officially COMPLETE — 11/11 sub-phases (17c.0.0 through 17c.0.7 + 17c.0.8 itself) landed**; pure book-keeping doc cascade across 6 in-tree surfaces + 1 sibling-artifact (CHAT_HANDOFF Part 8); ZERO source-code change; backport-IRRELEVANT-by-novelty (pure book-keeping); explicit handoff to next-task cluster: **B19** (essential closed-loop pipeline verification; ~2.5-4 d revised down from 3-7 d after 2026-05-15 night code-reality check confirming steps 10/11/12/13/14 are all already DONE per `EXECUTION_PLAN.md` and the only essential B19 sub-items remaining are (c) IMOGEN engine round-trip + (e) closed-loop validation vs legacy A/B + recommended (i) SPINUP/FIRSTCALL hardcoding investigation) → **B20** (recommended literature-comparison sanity check; ~1-2 d) → 17c.1 → 17c.4 cluster phases on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative). Full landing record at §1.7 of this file. Three deferred B19 questions for session-5 opening agenda are documented in `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 8 §8.6.

**Date 17c.1 → 17c.4 cluster phases:** _pending — recommended AFTER B19 (essential) + B20 (recommended) per user-authorised 2026-05-15 ~19:30 UTC+2 ("hopefully before we get to the cluster work and tests"); see B19/B20 in `notes/FOLLOWUPS.md`._

**Date C3 close-out tag `v0.18.0-step17c-c3-cluster-tight`:** _pending_

**Status:** ✅ **17c.0 PREP COMPLETE** (11/11 sub-phases landed at this commit) / 🔧 **cluster phases 17c.1 → 17c.4 PENDING** (after B19 essential + B20 recommended) — Sub-phases 17c.0.0 (B15+B16 forensic record; commit `2beff31`, 2026-05-12), 17c.0.1 + 17c.0.2 (B15 fix + signal-of-life harness assertion + four-xval re-verification on B15-fixed HEAD; commit `019c9dd`, 2026-05-13), 17c.0.3 (B16 forensic + fix; commit `4d09b62`, 2026-05-13), 17c.0.4 (B17(a) harness sort-then-diff fix + B17 forensic deep-dive + reclassification of B17(b) as stochastic-process sensitivity; commit `027d90d`, 2026-05-13 evening), 17c.0.4-followup (B17(b) operational acceptance at provisional 2% cell-total tolerance per new §3.8.5; doc-only; commit `2771939`, 2026-05-13 night), 17c.0.5 (full 4-xval re-verify on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD per user-authorised collapsed renumbering convention + harness stale-reference cleanup; commit `29ccc87`, 2026-05-13 night-late), 17c.0.5-clarification (broaden B17(b) reactivation surface from FORCED-only to FORCED + PERMITTED via 6-surface in-tree cascade; doc-only; commit `e03ceb1`, 2026-05-14 early morning), and **17c.0.6 (B17(b) MECHANICAL CLOSURE via 4-LOC surgical correction of the closed-form `spinup_year_idx` reproduction formula in `lpjguess/modules/imogen_input.cpp` + `lpjguess/modules/imogencfx.cpp` per new §3.8.6, exercising the §3.8.5.5 5th cadence bullet PERMITTED-reactivation surface introduced at 17c.0.5-clarification; BUNDLED with C2 close-out tag (a)-refined annotation amendment in same commit/push event; this commit, 2026-05-15 early morning)** have landed. **B16 (latent eager-cache-fullness check defect) is closed**: G1+G2 remove the eager `if (last_store_index >= nyears) fail(...)` check at the start of `(Imogen|IMOGENCFX)Input::preload_all_climate` and replace it with extensive doc blocks (~38 LOC + ~20 LOC) explaining the cumulative-across-cells cache design intent and B16 forensic; G3 augments the base-class `InputModule::preload_all_climate` doc block in `inputmodule.h` with ~20 LOC of "IMPLEMENTATION GUIDANCE FOR SUBCLASSES" formalising the cumulative-cache contract; G4 tightens the inner per-miss `fail()` diagnostics in both modules with `cell_idx` for unambiguous fault attribution. **However, gates 7 + 8 controlled-fail at 17c.0.3 surfacing B17 (a new audit item with two sub-defects)** — same staged-discovery pattern as 17c.0.1 → 17c.0.3 (B15 fix unmasked B16; B16 fix unmasks B17): **B17(a)** = row-emission-order divergence between gridcell_outer (cell-major: per-cell-then-year) and year_outer (year-major: per-year-then-cell) makes Decision-12 byte-equality structurally unachievable for any multi-cell xval scenario (5/37 files differ purely on row order — sort-then-diff returns 0); **B17(b)** = small ~1 ULP numerical drift in 17 per-PFT-total / `tot_runoff` files (per-LC summed files unaffected) most prominently in southern-hemisphere cell `(-57.75, -33.75)` after sorting away B17(a). Both build-agnostic (serial AND single-process MPI exhibit identical fail pattern; binaries differ at byte 913+ proving distinct compilation). The 1cell xval scenarios (gates 5+6) PASS cleanly post-G1-G4 with year_outer fully executed (5 `[year_outer]` banners per Run B; identical envelope to 17c.0.1+17c.0.2 verification record). The 4cell xval scenarios (gates 7+8) **CONTROLLED-FAIL exit 2** (22/37 differ; 0 NaN; banner_a=0 banner_b=5) — proving B16 is mechanically fixed (year_outer reaches `preload_all_climate` for `cell_idx >= 1` AND completes preload AND completes the full 9-year run AND emits all 37 .out files; pre-B16 fix the run aborted at `preload_all_climate` with exit 99 after ≥3 banners). B17 was the next sub-phase trigger (analogous to how B16 surface in 17c.0.2 triggered 17c.0.3). **17c.0.4 (this commit, 2026-05-13 evening) lands the B17(a) fix + B17 forensic deep-dive.** Phase-A forensic deep-dive (per §1.3.3) materially revised the §3.4 hypothesis space: drift magnitudes are 0.67-17.7% relative (NOT ~1 ULP), falsifying §3.4 hypothesis 1 (FP-summation roundoff); per-cell-isolated `gridcell.seed` + `stand.seed` architecture rules out §3.4 hypothesis 2 (global RNG state); empirical localizer "cell 0 BIT-EXACT in ALL 17 drift files; cells 1, 2, 3 progressively diverge with drift first appearing at year 1873-1876 within each cell" reclassifies B17(b) as **stochastic-process sensitivity per cell-iteration-order RNG slip** (cell totals stay within ~1.4% relative; per-PFT splits up to ~20% in low-biomass marginal-establishment cases). **B17(a) (row-emission-order divergence) is mechanically CLOSED via a 100-line addition to `compare_outputs()` realising §3.6 option (a1) (harness sort-then-diff with `LC_ALL=C sort -k1,1n -k2,2n -k3,3n` on (Lon, Lat, Year) preserving header).** All 8 verification gates verified empirically: gates 3+4 162/162 unit tests both builds; gates 5+6 1cell xval PASS exit 0 (37/37 raw BIT_EXACT, regression-clean); gates 7+8 4cell xval CONTROLLED-FAIL exit 2 with NEW textbook 15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER classification on BOTH .ins variants — the 5 PURE B17(a) files (`mch4`, `mch4_diffusion`, `mch4_ebullition`, `mch4_plant`, `npool`) successfully normalize; the 17 B17(a)+(b) files retain B17(b) drift. **B17(b) DECISION (α tolerance-based comparison vs β seed-tracking dprintf root-cause investigation) deferred to 17c.0.5** because (1) B17(a) closure was the lower-risk + better-understood deliverable; (2) the empirically clarified picture (1.4% max cell-total drift in stochastic-process simulation) materially changes the (α) vs (β) calculus — Decision-12 acceptance criterion 2 ("PASS substantive within an explicit tolerance") is now empirically grounded as the (α) path, while (β) requires +1-2 d of seed-tracking instrumentation given that code-spelunking exhausted the easy hypotheses. **17c.0.4-followup (commit `2771939`, 2026-05-13 night) lands B17(b) operational acceptance at provisional 2% cell-total tolerance per new §3.8.5** (user-authorised lighter-touch reframing of the originally-planned 17c.0.5 (α/β decision) sub-phase: provisionally accept the B17(b) drift envelope WITHOUT writing any new harness code OR engine instrumentation; defer formal Option α/β closure to a future sub-phase TBD reactivated only on a §3.8.5 re-evaluation trigger per new §3.8.5.5 cadence). Doc-only commit (3 in-tree files: `notes/STEP_17c.md` + `notes/FOLLOWUPS.md` + `scripts/cross_validate_year_outer.sh` inline-comment block; ZERO logic change) + sibling-artifact handoff Part 4. **17c.0.5 (this commit, 2026-05-13 night-late) lands the full 4-xval re-verify on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD `2771939` (gates 1-8) per the user-authorised collapsed renumbering convention** — establishing the canonical baseline routine xval re-verify envelope for the §3.8.5.5 cadence. All 8 gates byte-identical to 17c.0.4 envelope: gates 1+2 binary sha256 unchanged (no source change since `4d09b62`; build/guess sha256 `8daa1339...`; build_mpi/guess sha256 `dd307488...`; both 2 974 248 B; both timestamped May 13 16:43/16:59); gates 3+4 25/25 / 162/162 PASS both builds; gates 5+6 1cell xval PASS exit 0 with 37/37 raw BIT_EXACT; gates 7+8 4cell xval CONTROLLED-FAIL exit 2 with **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER + 0 NaN + banner_a=0 + banner_b=5** envelope identical between LOOSE (gate 7) and TIGHT (gate 8) coupling — a stronger empirical confirmation than 17c.0.4 provided that B17(b) is **coupling-invariant** (engine-side per-cell-iteration-order RNG slip per §3.8.3, NOT input-module-specific). Opportunistically rolled into 17c.0.5: the 4-line surgical -1/+1-or-+2 stale-reference cleanup at `scripts/cross_validate_year_outer.sh` lines 305-306, 429, 484, 630-633 (post-collapsed-renumbering convention adoption rendered the prior "sub-phase 17c.0.5 (decision: tolerance-based comparison vs root-cause fix)" framing factually incorrect; +10/-5 LOC; ZERO behaviour change; bash syntax + smoke-retest verified). Remaining 17c.0 PREP sub-phases per §1 below: 17c.0.6 (C2 close-out tag annotation amendment decision — ACTIONABLE since 17c.0.5 has confirmed underlying year_outer code substantively passes within §3.8.5 envelope; ~0.2 d) → 17c.0.7 (workstation `mpirun -np 4` mimic; ~1 d) → 17c.0.8 (PREP phase close-out; ~0.2 d). The deferred Option α/β closure for B17(b) is now an EXTRA-PREP sub-phase (identifier TBD) that reactivates **either on §3.8.5 re-eval trigger firing (FORCED reactivation) OR proactively at user discretion at any time even absent a trigger (PERMITTED reactivation) per §3.8.5.5 5th cadence bullet** (clarification commit on top of 17c.0.5 commit `29ccc87`). Then 17c.1 → 17c.4 cluster phases on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative). The C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` annotation amendment (option a/b/c per §0.11) becomes ACTIONABLE in 17c.0.6 since the underlying year_outer code at `f6c192e` is now empirically confirmed substantively-correct within the §3.8.5 provisional-acceptance envelope.

**Post-17c.0.6 update (2026-05-15 evening + night):** Sub-phases **17c.0.7 (workstation `mpirun -np 4` mimic verification + Path α handshake-file write-path defect fix + 5 LOC TRUNK-RELEVANT N-cycle unit doc-comment clarifications + 13 LOC TRUNK-RELEVANT `commonoutput.cpp` ngases.out unit comment block + soil.N2O_mass typo fix at `guess.h:3850-3855` + bonus cross-ref precision fix at `imogenoutput.cpp:75-83`; commit `6695ef2`, 2026-05-15 evening; tagged `v0.17.7-step17c-mpi-4rank-mimic` post-merge; 3-remote-converged; full landing record at §1.6 of this file)** and **17c.0.8 (PREP phase close-out; this commit, 2026-05-15 night; tagged `v0.17.8-step17c-prep-complete` post-merge; doc-cascade-only across 6 in-tree surfaces + 1 sibling-artifact CHAT_HANDOFF Part 8; ZERO source-code change; backport-IRRELEVANT-by-novelty; full landing record at §1.7 of this file)** have ALSO landed. **Step 17c.0 PREP phase is now OFFICIALLY COMPLETE — 11/11 sub-phases (17c.0.0 + 17c.0.1 + 17c.0.2 + 17c.0.3 + 17c.0.4 + 17c.0.4-followup + 17c.0.5 + 17c.0.5-clarification + 17c.0.6 + 17c.0.7 + 17c.0.8) landed.** The C2 close-out tag annotation amendment was bundled into 17c.0.6 per (a)-refined approach; the deferred-from-C2 `mpirun -np 4` workstation mimic obligation per session-2 §17.7 was fulfilled at 17c.0.7. Next-task cluster (per user-authorised 2026-05-15 ~19:30 UTC+2 + ~22:30 UTC+2): **B19** (essential closed-loop pipeline verification of stages 2-7 of the 8-stage coupled pipeline; ~2.5-4 d revised down from the original 3-7 d estimate after 2026-05-15 night code-reality check confirmed steps 10/11/12/13/14 are all already DONE per `EXECUTION_PLAN.md` and only sub-items (c) IMOGEN engine round-trip + (e) closed-loop validation vs legacy A/B + recommended (i) SPINUP/FIRSTCALL hardcoding investigation are essential; the rest is optional polish) → **B20** (recommended literature-comparison sanity check for global N2O magnitudes against Tian et al. 2020 GCB / Saikawa et al. 2014 ACP / IPCC AR6 WG1 Ch. 5 published ranges; optionally CH4 against Saunois et al. 2020 ESSD; ~1-2 d) → **17c.1 → 17c.4 cluster phases** on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative). v1.0 % done estimate at 17c.0.8 close-out: **~70-72%** (held from 17c.0.7; 17c.0.8 is pure book-keeping with no fresh substantive milestone). Three deferred B19 questions for session-5 opening agenda are documented in `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 8 §8.6 (i-spinup-firstcall ordering relative to B19-Phase-4 closed-loop validation; B19-Phase-4 tolerance choice; B19-Phase-1 ↔ 17c.0.8 ordering revisit was resolved in favour of 17c.0.8-first as documented at this Status update).

---

## Index
- [§0. Pre-flight forensic — audit items B15 + B16 (this commit)](#0-pre-flight-forensic--audit-items-b15--b16-2026-05-12-session-3)
  - [0.1 Why this section exists](#01-why-this-section-exists-session-3-onboarding-audit-finding)
  - [0.2 Anchors at the start of the audit (the apparent “PASS” state)](#02-anchors-at-the-start-of-the-audit-the-apparent-pass-state)
  - [0.3 The smoking gun — empirical reproduction on clean HEAD](#03-the-smoking-gun--empirical-reproduction-on-clean-head-f6c192e)
  - [0.4 Canonical pattern from `version_A/` and `version_B/` reference setups](#04-canonical-pattern-from-version_a-and-version_b-reference-setups)
  - [0.5 `plib` parser mechanism (source-level walkthrough)](#05-plib-parser-mechanism-source-level-walkthrough)
  - [0.6 Why the defect wasn’t caught earlier (no signal-of-life assertion)](#06-why-the-defect-wasnt-caught-earlier-no-signal-of-life-assertion)
  - [0.7 Three independent evidence streams converge on the same root cause](#07-three-independent-evidence-streams-converge-on-the-same-root-cause)
  - [0.8 Recommended B15 fix design](#08-recommended-b15-fix-design)
  - [0.9 B16 acknowledgement (forensic + fix in subsequent commit)](#09-b16-acknowledgement-forensic--fix-in-subsequent-commit)
  - [0.10 New persistent operational heuristic — rule #8](#010-new-persistent-operational-heuristic--rule-8-signal-of-life-banner-presence-assertion-for-every-code-path-gated-cross-validation)
  - [0.11 C2 close-out tag (`v0.17.5-step17b-c2-mpi-sync`) annotation — decision deferred](#011-c2-close-out-tag-v0175-step17b-c2-mpi-sync-annotation--decision-deferred)
  - [0.12 Salvaged WIP — what we stashed and why](#012-salvaged-wip--what-we-stashed-and-why)
- [§1. 17c.0 PREP phase plan (revised post-B15 + post-B16 + post-B17 forensic)](#1-17c0-prep-phase-plan-revised-post-b15--post-b16--post-b17-forensic)
  - [§1.1 17c.0.1 + 17c.0.2 landing record — B15 fix + signal-of-life assertion + four-xval re-verification (commit `019c9dd`, 2026-05-13)](#11-17c01--17c02-landing-record--b15-fix--signal-of-life-assertion--four-xval-re-verification-commit-019c9dd-2026-05-13)
  - [§1.2 17c.0.3 landing record — B16 forensic + fix + four-xval re-verification surfacing B17 (commit `4d09b62`, 2026-05-13)](#12-17c03-landing-record--b16-forensic--fix--four-xval-re-verification-surfacing-b17-this-commit-2026-05-13)
  - [§1.3 17c.0.4 landing record — B17 forensic deep-dive (Phase A) + B17(a) harness sort-then-diff fix + reclassification of B17(b) (commit `027d90d`, 2026-05-13 evening)](#13-17c04-landing-record--b17-forensic-deep-dive-phase-a--b17a-harness-sort-then-diff-fix--reclassification-of-b17b-this-commit-2026-05-13-evening)
  - [§1.4 17c.0.4-followup landing record — B17(b) operational acceptance at provisional 2% tolerance + sub-phase renumbering decision deferral (commit `2771939`, 2026-05-13 night)](#14-17c04-followup-landing-record--b17b-operational-acceptance-at-provisional-2-tolerance--sub-phase-renumbering-decision-deferral-commit-2771939-2026-05-13-night)
  - [§1.5 17c.0.5 landing record — full 4-xval re-verify on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD (this commit, 2026-05-13 night-late)](#15-17c05-landing-record--full-4-xval-re-verify-on-b15b16b17ab17b-provisionally-accepted-head-this-commit-2026-05-13-night-late)
  - [§1.6 17c.0.7 landing record — workstation `mpirun -np 4` mimic verified + Path α handshake-file write-path defect fix + tiny unit doc-comment clarifications (this commit, 2026-05-15)](#16-17c07-landing-record--workstation-mpirun--np-4-mimic-verified--path-α-handshake-file-write-path-defect-fix--tiny-unit-doc-comment-clarifications-this-commit-2026-05-15)
  - [§1.7 17c.0.8 landing record — PREP phase close-out (this commit, 2026-05-15 night; tagged `v0.17.8-step17c-prep-complete`)](#17-17c08-landing-record--prep-phase-close-out-this-commit-2026-05-15-night-tagged-v0178-step17c-prep-complete)
- [§2. B16 forensic + fix — audit item B16 (this commit)](#2-b16-forensic--fix--audit-item-b16-this-commit)
  - [2.1 Why this section exists (post-17c.0.2 surface)](#21-why-this-section-exists-post-17c02-surface)
  - [2.2 Anchors at the start of the B16 sub-investigation](#22-anchors-at-the-start-of-the-b16-sub-investigation)
  - [2.3 The smoking gun — empirical reproduction at `019c9dd` 4cell year_outer Run B](#23-the-smoking-gun--empirical-reproduction-at-019c9dd-4cell-year_outer-run-b)
  - [2.4 Cumulative-across-cells cache design intent (source-level walkthrough)](#24-cumulative-across-cells-cache-design-intent-source-level-walkthrough)
  - [2.5 Why the eager check mis-models the cache (root cause)](#25-why-the-eager-check-mis-models-the-cache-root-cause)
  - [2.6 Recommended B16 fix design — G1-G4](#26-recommended-b16-fix-design--g1-g4)
  - [2.7 B17 acknowledgement (forensic surface in §3; fix deferred to 17c.0.4)](#27-b17-acknowledgement-forensic-surface-in-3-fix-deferred-to-17c04)
- [§3. B17 forensic surface — audit item B17 (this commit; fix in 17c.0.4)](#3-b17-forensic-surface--audit-item-b17-this-commit-fix-in-17c04)
  - [3.1 Why this section exists (post-17c.0.3 surface)](#31-why-this-section-exists-post-17c03-surface)
  - [3.2 Anchors at the start of the B17 sub-investigation](#32-anchors-at-the-start-of-the-b17-sub-investigation)
  - [3.3 B17(a) — row-emission-order divergence (cell-major vs year-major)](#33-b17a--row-emission-order-divergence-cell-major-vs-year-major)
  - [3.4 B17(b) — small ~1 ULP numerical drift in per-PFT-total / tot_runoff files](#34-b17b--small-1-ulp-numerical-drift-in-per-pft-total--tot_runoff-files)
  - [3.5 Build-agnostic confirmation (serial + single-process MPI both reproduce)](#35-build-agnostic-confirmation-serial--single-process-mpi-both-reproduce)
  - [3.6 Recommended B17 fix design — to be elaborated in 17c.0.4 commit](#36-recommended-b17-fix-design--to-be-elaborated-in-17c04-commit)
  - [3.7 Why B17 was not caught by 17c.0.0 forensic or 17c.0.1+17c.0.2 verification](#37-why-b17-was-not-caught-by-17c00-forensic-or-17c01172-verification)
  - [3.8 Reclassified B17(b) — stochastic-process sensitivity per cell-iteration-order RNG slip (NEW in 17c.0.4)](#38-reclassified-b17b--stochastic-process-sensitivity-per-cell-iteration-order-rng-slip-new-this-commit-17c04)
    - [3.8.5 Operational acceptance: provisional 2% tolerance (NEW in 17c.0.4-followup commit `2771939`; **NOW SUPERSEDED-BY-CLOSURE per §3.8.6**)](#385-operational-acceptance-provisional-2-tolerance-decided-2026-05-13-night-session-4-supersedes-139--36-formal-implementation-path)
    - [3.8.5.5 Re-evaluation cadence (NEW in 17c.0.5; user-authorised 2026-05-13 night-late session 4; **NOW SUPERSEDED-BY-CLOSURE per §3.8.6 — PERMITTED-revisit surface FIRED SUCCESSFULLY**)](#3855-re-evaluation-cadence-new-user-authorised-2026-05-13-night-late-session-4)
    - [3.8.6 B17(b) MECHANICAL CLOSURE — closed-form spinup_year_idx reproduction formula correction (NEW 2026-05-15; sub-phase 17c.0.6; SUPERSEDES §3.8.5 + §3.8.5.5)](#386-b17b-mechanical-closure--closed-form-spinup_year_idx-reproduction-formula-correction-new-2026-05-15-sub-phase-17c06-supersedes-385--3855-provisional-acceptance-regime)
  - [§3.10 Path α handshake-file write-path defect — forensic + fix (NEW 2026-05-15; sub-phase 17c.0.7)](#310-path-α-handshake-file-write-path-defect--forensic--fix-new-2026-05-15-sub-phase-17c07)
- [§4 onwards — 17c.1 through 17c.4 cluster phases](#4-onwards--17c1-through-17c4-cluster-phases) _(skeleton; populated when reached; renumbered from §2 in 17c.0.3 commit due to insertion of §2 (B16 forensic) + §3 (B17 forensic) above)_

---

## 0. Pre-flight forensic — audit items B15 + B16 (2026-05-12 session 3)

### 0.1 Why this section exists (session-3 onboarding audit finding)

The canonical anchors at the start of session 3 (per `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 0) were:
- HEAD at `f6c192e`, tagged `v0.17.5-step17b-c2-mpi-sync` (annotated tag object SHA `a572f848`; pushed to all 3 remotes).
- All four cross-validation scenarios (1cell × imogen, 1cell × imogencfx, 4cell × imogen, 4cell × imogencfx) reported PASS substantive (37/37 bit-exact + 0/37 NaN) by `scripts/cross_validate_year_outer.sh`.
- Working tree clean; both `lpjguess/build/` and `lpjguess/build_mpi/` builds pass 162/162 unit tests.
- Fortran engine clean build (`imogen/code/compile.sh`); `imogen_lpjg` 137 832 B; only pre-existing 8 warnings.
The session-3 prompt called for a 17c.0 PREP phase before cluster work, addressing the `mpirun -np 4` workstation mimic that was explicitly deferred at C2 core landing (`f13b302`) and never executed before the C2 close-out tag was issued at `f6c192e`. While auditing what "PASS" actually meant for the four xval scenarios, an inconsistency surfaced: nothing in the existing run.log artefacts contained the `[year_outer]` diagnostic banner that `framework.cpp:502` emits when the `year_outer` code path executes. This led to a forensic investigation across:
1. **Empirical reproduction on the clean post-stash HEAD** (no source-tree modifications) to confirm the defect exists right now in the tagged code.
2. **Cross-reference against `version_A/` and `version_B/` reference `.ins` setups** to establish the canonical syntax convention for parameters of this shape.
3. **Mechanistic walkthrough of the `plib` parser source + the `parameters.cpp` custom-block layer** to provide source-level certainty about why the observed behaviour happens.
All three streams converge on a single class-mismatch defect (B15) plus one downstream-of-B15 latent defect (B16). This section documents the full chain.
### 0.2 Anchors at the start of the audit (the apparent "PASS" state)

| Anchor | Pre-audit value | Source |
|---|---|---|
| HEAD | `f6c192e` | `git rev-parse HEAD` |
| Tag at HEAD | `v0.17.5-step17b-c2-mpi-sync` (annotated) | `git tag --points-at HEAD` |
| Tag annotation | "tight-coupling closed-loop year_outer mode is now feature-complete on workstation (single-process + mpirun mimic READY)" | `git cat-file -p v0.17.5-step17b-c2-mpi-sync` (excerpt) |
| `scripts/cross_validate_year_outer.sh 1cell imogen` | PASS substantive (37/37 + 0/37 NaN) | session-2 handoff Part 26 + session-3 handoff §0.3 |
| `scripts/cross_validate_year_outer.sh 1cell imogencfx` | PASS substantive (37/37 + 0/37 NaN) | session-2 handoff Part 26 + session-3 handoff §0.3 |
| `scripts/cross_validate_year_outer.sh 4cell imogen` | PASS substantive (37/37 + 0/37 NaN) | session-2 handoff Part 26 + session-3 handoff §0.3 |
| `scripts/cross_validate_year_outer.sh 4cell imogencfx` | PASS substantive (37/37 + 0/37 NaN) | session-2 handoff Part 26 + session-3 handoff §0.3 |
| `mpirun -np 4` workstation mimic | NOT verified at tag time (deferred per session-2 §17.7) | `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` §17.7 |
The tag annotation explicitly says "single-process + mpirun mimic READY" — i.e., the four single-process xval scenarios were the substantive validation at tag time; the mpirun mimic was a deferred obligation. The B15 finding is that even the single-process portion of that validation was a false positive.
### 0.3 The smoking gun — empirical reproduction on clean HEAD `f6c192e`

After stashing all WIP and rebuilding `lpjguess/build/guess` from clean HEAD source (Phase 1 + Phase 2 of the forensic; recorded in this commit's session-3 handoff Part 1.1 and Part 1.2), `scripts/cross_validate_year_outer.sh 1cell imogencfx` was executed on clean HEAD. The result:
| Anchor | Value | Notes |
|---|---|---|
| Harness exit code | `0` ("PASS substantive") | Same false-positive PASS that landed at C2 close-out |
| Run B `xval_wrapper.ins` line 13 (the framework_loop_mode override) | `param "framework_loop_mode" (str "year_outer")` | The HEAD wrapper-writer syntax (`scripts/cross_validate_year_outer.sh:138`) |
| `[year_outer]` banner count in Run B `run.log` | **0** | Banner is at `framework.cpp:502` (`dprintf("[year_outer] starting framework_loop_mode = \"year_outer\" ...");`); fires only when the gate at `framework.cpp:464` evaluates true |
| `[year_outer]` banner count in Run A `run.log` | 0 | Expected — Run A is the gridcell_outer baseline |
| `[F-10 caveat: per-gridcell-rolling]` flush count, Run A | 11 | Affirmative signature of `gridcell_outer` mode (`imogenoutput.cpp:373`) |
| `[F-10 caveat: per-gridcell-rolling]` flush count, Run B | 11 | **Identical to Run A** — Run B silently degraded to gridcell_outer |
| Run A vs Run B `run.log` sha256 | `43c278b00c7e15bc15768cd004c3120938a92bc80e797b2e84bc67e147542c10` (both) | **Byte-identical run logs** — possible only because both ran the same code path with the same inputs, completing in the same wall-clock second |
| Run A vs Run B `cmp` on `run.log` | exit 0 (zero differing bytes) | direct confirmation of byte-for-byte identity |
| Combined sha256 of all 37 `.out` files in Run A | `ab23ea8054b4131b1e49bd8ddc74a7722f6bb6665c911dd5b19a359ea0a4908d` | |
| Combined sha256 of all 37 `.out` files in Run B | `ab23ea8054b4131b1e49bd8ddc74a7722f6bb6665c911dd5b19a359ea0a4908d` | **Identical to Run A** — every `.out` byte-equal |
| Per-file `cmp` matches | 37 / 37 | none differ |
**The execution traces themselves are byte-identical**, not just the `.out` files. There is no mechanism by which two LPJ-GUESS invocations with two different intended `framework_loop_mode` values can produce byte-identical run logs (including identical timestamps because both finished within the same wall-clock second on a 1-cell smoke) UNLESS the value of `framework_loop_mode` is being completely ignored. Combined with the absence of `[year_outer]` banners in Run B, this is mechanistically conclusive: **Run B silently runs in `gridcell_outer` mode**.
The forensic artefacts are preserved at:
- `_chat_artifacts/forensic_clean_HEAD_xval_2026-05-12.log` — full harness output (4942 B; harness exit 0).
- `_chat_artifacts/forensic_clean_HEAD_run_A_run.log` — Run A `run.log` (7395 B; sha256 `43c278b0…`).
- `_chat_artifacts/forensic_clean_HEAD_run_B_run.log` — Run B `run.log` (7395 B; sha256 `43c278b0…` — identical to Run A).
(The 4cell scenarios were not re-run at this stage because the 1cell reproduction was already mechanistically conclusive and the 4cell case would surface the downstream B16 latent defect, masking the cleaner B15 demonstration. 4cell re-verification is part of the post-B15-fix Phase 4 of 17c.0 PREP.)
### 0.4 Canonical pattern from `version_A/` and `version_B/` reference setups

The two predecessor coupled-model framework trees `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/landsymm_imogen_setup/` and `version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/landsymm_imogen/` each ship 17 reference `.ins` files. A grep across both confirms a strict two-class syntax convention:
| Class | Syntax | Examples in `version_A/.../SSP1_RCP26/main.ins` and the rest of the tree |
|---|---|---|
| **Class 1** — integer / numeric / xtring framework parameters declared via `declare_parameter` (or `declareitem` directly in `parameters.cpp::plib_declarations`) | **bare keyword**: `key value` | `nyear_spinup 500`, `freenyears 100`, `firsthistyear 1901`, `firstoutyear 1901`, `lasthistyear 2100`, `lastoutyear 2100`, `ifdyn_phu_limit 1`, `nyear_dyn_phu 165` |
| **Class 2** — file paths and short-string variable names read from the `Paramlist param` dictionary via `param["key"].str` | **`param "key" (str "value")`** SET-block | `param "file_ndep" (str "...")`, `param "file_gridlist" (str "...")`, `param "ndep_timeseries" (str "RCP26")`, `param "variable_temp" (str "tas")`, `param "variable_relhum" (str "hurs")`, `param "file_lu" (str "...")`, `param "file_lucrop" (str "...")`, … |
`framework_loop_mode` does not exist in `version_A/B` (it's a new parameter added in this rebuild for F-12 sub-milestone C1). When we added it, we declared it via:

```cpp
declare_parameter("framework_loop_mode", &IMOGENConfig::framework_loop_mode, 20,
                  "Framework loop ordering: gridcell_outer (default) | year_outer (F-12 C1)");
```

at both `lpjguess/modules/imogencfx.cpp:353` and `lpjguess/modules/imogen_input.cpp:214`, binding it to the global C++ xtring `IMOGENConfig::framework_loop_mode` declared at `lpjguess/framework/parameters.cpp:288` with C++ initializer `"gridcell_outer"`. We consume it via direct C++ variable read at `lpjguess/framework/framework.cpp:464`:

```cpp
if (IMOGENConfig::framework_loop_mode == "year_outer") {
    ...
}
```

— **not** via `param["framework_loop_mode"].str` (Class-2 access). So `framework_loop_mode` is unambiguously **Class 1**. By the canonical version_A/B convention, it should therefore be set with bare-keyword syntax (`framework_loop_mode "year_outer"`).
But our base `.ins` (`runs/SSP1-2.6/main_xval_imogencfx.ins:176`) and the harness wrapper-writer (`scripts/cross_validate_year_outer.sh:138`) both use **Class-2 (param-block) syntax** for it:

```
! runs/SSP1-2.6/main_xval_imogencfx.ins:176
param "framework_loop_mode" (str "gridcell_outer")
```

```bash
# scripts/cross_validate_year_outer.sh:138 (template line in write_wrapper_ins())
param "framework_loop_mode" (str "$mode")
```

This is a **class-mismatch defect**: the parameter is Class-1 (declare_parameter-bound; consumed via the C++ variable directly) but is set with Class-2 syntax (which writes to the Paramlist dict that nothing reads for this key). Per the canonical convention, the fix is to switch the syntax to Class 1 (bare-keyword) at all three sites.
### 0.5 `plib` parser mechanism (source-level walkthrough)

The mechanism is fully traceable to the `plib` library + the `parameters.cpp` custom-block layer.
**(a) `plib` natively knows three syntaxes** (per `lpjguess/libraries/plib/plib.h` lines 9-48):
1. COMMANDS — bare identifiers followed by data: `identifier value`. Identifiers are declared with one of seven `declareitem(...)` overloads (xtring, std::string, int, double, bool, bool-flag, set-header). Each binds the identifier to a C++ pointer (or, for set-headers, to an integer ID).
2. SETS — named blocks: `keyword "name" ( ... )`. Declared via `declareitem(identifier, int id, int callback, ...)`. When the parser sees the keyword, it expects a string name and an open parenthesis, then calls `plib_declarations(id, name)` to allow the calling program to declare the items valid inside the SET.
3. GROUPS — macro-style named blocks: `group "name" ( ... )` — implicitly inserted wherever the group name appears later. Not relevant for our case.
**There is no `param` keyword native to plib.**
**(b) The `param "key" (str "value")` syntax is a custom SET layered on top of plib by `parameters.cpp`.** Specifically, in `parameters.cpp::plib_declarations` (the global scope branch), at line 991:

```cpp
declareitem("param", BLOCK_PARAM, CB_NONE, "Header for custom parameter block");
```

This declares `param` as a SET-header keyword that, when encountered, captures a name and triggers `plib_declarations(BLOCK_PARAM, name)`. Inside the BLOCK_PARAM scope (lines 1506-1514):

```cpp
case BLOCK_PARAM:

    paramname = setname;                       // captures "framework_loop_mode" into a module-static xtring
    declareitem("str", &strparam, 300, CB_STRPARAM,
        "String value for custom parameter");
    declareitem("num", &numparam, -1.0e38, 1.0e38, 1, CB_NUMPARAM,
        "Numerical value for custom parameter");

    break;
```

So inside the SET, only two sub-items are declared: `str` (writes the parsed string to the module-static `strparam` and fires CB_STRPARAM) and `num` (writes a number to module-static `numparam` and fires CB_NUMPARAM). When plib parses `(str "year_outer")`, it matches `str` → assigns `"year_outer"` to `strparam` → calls `plib_callback(CB_STRPARAM)`.

**(c) `CB_STRPARAM` does exactly one thing** (`parameters.cpp:1858-1860`):

```cpp
case CB_STRPARAM:
    param.addparam(paramname, strparam);
    break;
```

`param.addparam(...)` adds (or overwrites, per `parameters.h:787` documentation) an entry in the global `Paramlist param` object with key `paramname` and string value `strparam`. **It never touches any C++ variable bound via `declare_parameter`.** There is no lookup, no fallback, no cross-update.

**(d) `declare_parameter` is a separate, disjoint mechanism.** It is declared in `parameters.h:821-860` as 5 overloads (xtring*, std::string*, int*, double*, bool*) and implemented in `parameters.cpp:736-756`:

```cpp
void declare_parameter(const char* name, xtring* param, int maxlen, const char* help) {
    xtringParams.push_back(xtringParam(name, param, maxlen, help));
}
// ... and similarly for std::string*, int*, double*, bool*
```

These 5 functions only push the (name, &cppvar, ...) tuple into one of 5 module-static `std::vector`s (`xtringParams`, `stringParams`, `intParams`, `doubleParams`, `boolParams`). At the global-scope branch of `plib_declarations` (lines 995-1018), the 5 vectors are iterated and each entry is registered as a plib bare-keyword command via `declareitem(name, &cppvar, ...)`:

```cpp
for (size_t i = 0; i < xtringParams.size(); ++i) {
    const xtringParam& p = xtringParams[i];
    declareitem(p.name, p.param, p.maxlen, 0, p.help);
}
// ... and similarly for stringParams / intParams / doubleParams / boolParams
```

`declareitem` for an `xtring*` (plib.cpp:188-206) creates a `Plibitem` of type `PLIB_XTRING` with the C++ pointer stored in `item.param`, and pushes it onto the active SET's linked list (`pthislist->addtostart(item)`). When the parser later encounters the bare identifier and a string value follows, the value is written **directly to the C++ variable** through that pointer.
**(e) Storage paths are mechanically disjoint.**
- `param "framework_loop_mode" (str "year_outer")` → `param.addparam("framework_loop_mode", "year_outer")` → `Paramlist param["framework_loop_mode"].str = "year_outer"`. **`IMOGENConfig::framework_loop_mode` is never touched.**
- `framework_loop_mode "year_outer"` (bare) → plib looks up `framework_loop_mode` in its declared-items table → finds the `PLIB_XTRING` entry whose `item.param == &IMOGENConfig::framework_loop_mode` → writes `"year_outer"` to `IMOGENConfig::framework_loop_mode`. **`Paramlist param[...]` is never touched.**
There is no read-side fallback either. `framework.cpp:464` reads `IMOGENConfig::framework_loop_mode` directly, never `param["framework_loop_mode"].str`. The C++ initializer at `parameters.cpp:288` (`xtring framework_loop_mode = "gridcell_outer";`) means the variable's value at run start is `"gridcell_outer"`, and stays `"gridcell_outer"` through both Run A and Run B unless bare syntax is used to mutate it.
**(f) `import` semantics.** `import "file.ins"` is processed in `plib.cpp:535-545` as inline file substitution:

```cpp
else if (importstatement) {
    importstatement = false;
    addword = false;
    if (plibword.type != WORD_STRING) {
        err = PLIB_EXPECTSTRING;
        return;
    }
    else if (!in.addfile(plibword.string)) {
        err = PLIB_FILEOPEN;
        return;
    }
}
```

`in.addfile(...)` adds the imported file to the input stream — its contents are processed as if inlined at the import location. So in our wrapper:
1. `import "main_xval_imogencfx.ins"` is processed first; that file's `param "framework_loop_mode" (str "gridcell_outer")` line at line 176 writes `"gridcell_outer"` to the Paramlist dict.
2. The wrapper's own `param "framework_loop_mode" (str "$mode")` at line 13 (where `$mode` = `"year_outer"` for Run B) is processed second; per `Paramlist::addparam` "overwriting if it already existed", this overwrites the dict entry to `"year_outer"`.
3. After parsing finishes, `Paramlist param["framework_loop_mode"].str == "year_outer"` for Run B. Correct, but **nothing reads it**.
4. `IMOGENConfig::framework_loop_mode` is still `"gridcell_outer"` (the C++ initializer value) for both runs.
5. The gate at `framework.cpp:464` evaluates `"gridcell_outer" == "year_outer"` → false → year_outer block does NOT execute → Run B silently runs in gridcell_outer mode → byte-identical outputs to Run A.
**(g) Duplicate `declare_parameter` is harmless.** Both `imogencfx.cpp:353` and `imogen_input.cpp:214` call `declare_parameter("framework_loop_mode", &IMOGENConfig::framework_loop_mode, 20, ...)`. The two calls push two entries into `xtringParams`, both pointing to the same C++ variable. The 995-998 registration loop calls `declareitem` twice; `declareitem` pushes both onto plib's linked list via `pthislist->addtostart(item)` (LIFO). When plib looks up `framework_loop_mode`, it finds whichever entry is at the head of the list and mutates the same C++ variable through the same pointer. Result: bare syntax still works correctly. Not a separate bug.
**(h) "Same parameter set twice in nested imports" hypothesis is RULED OUT.** A grep across the entire xval `.ins` import cascade (`runs/SSP1-2.6/main_xval_imogencfx.ins` → `global.ins`, `crop_n.ins`, `wetlandpfts.ins` → `global_soiln.ins`, `crop.ins`, `crop_n_stlist.simplePFT.remap10_g2p.N0-60-200-1000.ins`, `crop_n_pftlist.simplePFT.remap10_g2p.ins`) shows `framework_loop_mode` is set in exactly two places per Run B parse:
1. Once in the imported base (`main_xval_imogencfx.ins:176`, `param "framework_loop_mode" (str "gridcell_outer")`).
2. Once in the harness wrapper (`xval_wrapper.ins:13`, `param "framework_loop_mode" (str "year_outer")`).
Both writes use the same Class-2 syntax, both target the same Paramlist dict slot. Last-write-wins within Paramlist correctly leaves the dict slot at `"year_outer"`. **The defect is NOT a last-write-wins ordering bug; it is a class-mismatch bug** — writes go to the Paramlist dict while reads come from the C++ variable.
### 0.6 Why the defect wasn't caught earlier (no signal-of-life assertion)

Three concurrent gaps in the harness design + the consumer-side observability allowed B15 to remain hidden through C1 close-out (2026-05-10) and C2 close-out (2026-05-11/12):
1. **No signal-of-life assertion in `compare_outputs()`.** The harness only checks `cmp -s` for byte-equality + a `grep -l 'nan'` NaN gate. Neither asserts that the year_outer code path actually executed in Run B. The harness has no concept of "the gated branch must be entered for the comparison to be meaningful".
2. **Bit-equal-of-identical-output is a degenerate-pass class.** Two runs that take the same code path with the same inputs trivially bit-match. `cmp` cannot distinguish "two runs of the intended different paths whose outputs happen to coincide" (the validation we _meant_ to do) from "two runs of the same wrong path" (the actual situation).
3. **No diagnostic print of `IMOGENConfig::framework_loop_mode` after `.ins` ingest.** LPJ-GUESS does not echo parsed config values, so the discrepancy between the wrapper's intent (`"year_outer"`) and the actual C++ variable value (`"gridcell_outer"`) was not visible in either run.log.
These gaps reinforce a more general operational lesson — see §0.10 below for the new persistent rule.
### 0.7 Three independent evidence streams converge on the same root cause

| # | Evidence stream | Conclusion |
|---|---|---|
| 1 | **Empirical reproduction on clean HEAD `f6c192e`** (§0.3) | Run A and Run B `.out` × 37 + `run.log` are byte-identical (sha256 `ab23ea80…` for `.out`, `43c278b0…` for `run.log`); zero `[year_outer]` banners in Run B; both runs show 11 `[F-10 caveat: per-gridcell-rolling]` flushes (gridcell_outer signature). The `framework_loop_mode` value supplied via Class-2 syntax has zero observable effect. |
| 2 | **Canonical pattern in `version_A/`+`version_B/`** (§0.4) | Strict two-class convention: Class 1 (declare_parameter-bound C++ vars) takes bare-keyword syntax; Class 2 (Paramlist-dict-only items) takes param-block syntax. `framework_loop_mode` is Class 1 (we declared it that way; we consume via `IMOGENConfig::framework_loop_mode`); we set it Class 2 → mismatch. |
| 3 | **`plib` parser source mechanism** (§0.5) | `param "..." (str "...")` writes only to `Paramlist param[...]` (via `CB_STRPARAM` → `param.addparam`); `declare_parameter` only binds bare-keyword syntax (via the 995-1018 registration loop in `plib_declarations` → `declareitem(name, &cppvar, ...)`). Storage paths are disjoint with zero cross-update. Mathematically, no value supplied via Class-2 syntax can reach a Class-1 variable. |
All three converge on the same conclusion: **B15 is a class-mismatch defect — the wrapper-writer (and the imported xval base `.ins`) use Class-2 syntax for a Class-1 parameter.**
### 0.8 Recommended B15 fix design

The fix is purely syntactic at three sites; ZERO C++ source change. Specifically:
**(F1) `runs/SSP1-2.6/main_xval_imogencfx.ins:176`** — change

```
param "framework_loop_mode" (str "gridcell_outer")
```

to

```
framework_loop_mode "gridcell_outer"
```

with an in-place doc comment block citing §0 of this file.
**(F2) `runs/SSP1-2.6/main_xval_loose.ins:182`** — symmetric change. Same comment block referencing §0 + the parallel comment in `main_xval_imogencfx.ins`.
**(F3) `scripts/cross_validate_year_outer.sh:138` (the `write_wrapper_ins` function)** — change the wrapper template line from

```bash
param "framework_loop_mode" (str "$mode")
```

to

```bash
framework_loop_mode "$mode"
```

with a doc comment block at the top of `write_wrapper_ins()` explaining (a) plib's two disjoint param mechanisms; (b) why bare syntax is required for Class-1 declare_parameter-bound variables; (c) cross-reference to §0 of this file.
**(F4) Add a signal-of-life banner-presence assertion to `compare_outputs()`** in `scripts/cross_validate_year_outer.sh`. Specifically, after the existing byte-equality + NaN checks, grep both run.logs for `[year_outer]` banners. Pass condition: `banner_a == 0` (Run A is gridcell_outer; banner must be absent) AND `banner_b >= 1` (Run B is year_outer; banner must be present at least once). Failure of either invariant exits the harness with code 4 (new exit class). Defensive-correctness rule: this assertion catches not just B15 but the general class of defects where one of two compared runs silently degrades to the same code path as the other.
**(F5) Optional but recommended: a runtime diagnostic line at LPJ-GUESS startup** that echoes `IMOGENConfig::framework_loop_mode` after `.ins` ingest, so the parsed-vs-intent discrepancy is visible in run.log. Sample: `dprintf("[framework] framework_loop_mode = \"%s\" (after .ins parse)\n", (const char*)IMOGENConfig::framework_loop_mode);`. Placement: somewhere in the post-plib initialization path before the framework loop entry. This is a small additive C++ change (~3 LOC) that materially hardens the codebase against future analogous regressions and would have surfaced B15 immediately if it had existed.
**Verification gates for the B15 fix commit:**
1. Clean rebuild of `lpjguess/build/` and `lpjguess/build_mpi/` with zero new warnings (regression check; F1-F4 should not affect C++ compilation, but F5 if included does).
2. 162/162 unit tests pass on both builds.
3. **All four xval scenarios re-run** (`1cell × imogen`, `1cell × imogencfx`, `4cell × imogen`, `4cell × imogencfx`) — for the first time actually exercising the year_outer code path in Run B. Pass conditions:
   - Each scenario's harness exit code = 0 (PASS).
   - Run B run.log contains ≥ 1 `[year_outer]` banner; Run A contains 0.
   - 37/37 bit-exact + 0/37 NaN.
4. **Note on possible new failures.** If any scenario fails at gate 3 because year_outer's outputs disagree with gridcell_outer's, that's a real C1+C2 substantive-validation failure that was masked pre-B15. Specifically expected:
   - 4cell scenarios may surface **B16** (the eager cache-fullness check defect; see §0.9). This is anticipated and should be handled in a separate commit AFTER B15 lands cleanly on the 1cell scenarios. The 4cell B16 manifestation will be debugged on top of a B15-fixed codebase, providing clean isolation.
   - 1cell scenarios should pass cleanly (B16 doesn't fire on 1-cell runs because `last_store_index >= nyears` only triggers on `cell_idx >= 1`).
If 4cell year_outer outputs differ structurally from 4cell gridcell_outer outputs even after B15+B16 are both fixed, that is a real C1+C2 validation failure and would require either a deeper code-correctness investigation or an explicit tolerance specification documented in `notes/STEP_17b.md` §3a.7 (the substantive-validation framework).
### 0.9 B16 acknowledgement (forensic + fix in subsequent commit)

While testing the proposed B15 fix end-to-end on the 4cell scenarios (during the WIP that has been stashed; see §0.12), a downstream-of-B15 latent defect surfaced in `ImogenInput::preload_all_climate` and `IMOGENCFXInput::preload_all_climate`. Specifically, the eager sanity check:

```cpp
if (last_store_index >= nyears) {
    fail("...: stored_years cache already full ...");
}
```

at the start of `preload_all_climate` (after the per-cell mapping update but BEFORE the per-imogen-year cache-miss loop) **mis-models the cache as per-cell**. The actual design intent (per the inner cache-miss branch's own comments — "Cache miss: load year-imogen_year climate for ALL cells") is that the `stored_years` cache is **cumulative across cells**: cell 0 fills the cache with all distinct imogen_years it needs; subsequent cells produce 100% cache hits if those same imogen_years are already loaded.
When `nyear_spinup * NCELLS / NYEAR_SPINUP_PERIOD > 1` (e.g., 4 cells × 2 spinup years = 8 cell-years vs `NYEAR_SPINUP=8`-style configs), `last_store_index >= nyears` evaluates true on entry to `cell_idx >= 1`, even though the cell is about to need zero new slots (all hits). The eager check fires and aborts the run with a misleading "cache already full" message.
This defect has been latent since C1.3 sub-step 7.3.2 (commit `d7f6c74`, 2026-05-10) — i.e., since the original `preload_all_climate` introduction. It went undetected because B15 silently prevented year_outer from ever executing in any C1 or C2 xval run; all four "PASS" cross-validation scenarios actually ran in `gridcell_outer` mode in both branches, never invoking `preload_all_climate`.
**The full B16 forensic + fix will land in a separate commit AFTER B15 lands.** Conservative ordering rationale:
1. B15 is the higher-level defect (the false-positive harness). Fixing it is a prerequisite for ANY substantive year_outer validation.
2. B16 surfaces only when B15 is fixed AND a multi-cell year_outer run is attempted. The B15-fixed harness running on 1cell scenarios will pass cleanly without ever triggering B16, providing a clean baseline.
3. B16's fix is mechanically simple (remove the eager check; the inner per-miss check at the cache-miss branch already provides correct fail-fast semantics with proper context). But the doc burden is non-trivial because the cache's cross-cell cumulative design needs clear inline documentation that's missing today.
4. Bundling B15 + B16 into a single commit would conflate two distinct defects with different surface (harness-level vs C++-source-level) and different audit lineages.
The B16 sub-section in this file (`§3` once we get there in a later commit) will document the full root cause + fix design + verification of cumulative cache correctness across all four xval scenarios on multi-cell runs. The pre-investigation B16 patch is in the stash (see §0.12); it will be re-derived from forensic-first principles in the dedicated B16 commit rather than applied directly from the stash.
### 0.10 New persistent operational heuristic — rule #8 (signal-of-life banner-presence assertion for every code-path-gated cross-validation)

**Rule #8.** Every cross-validation harness whose `Run A` and `Run B` exercise different gated code paths in the same binary (e.g., `framework_loop_mode == "year_outer"` vs `"gridcell_outer"`) MUST include a **signal-of-life banner-presence assertion**:
- Place a unique banner `dprintf` inside the gated branch (must appear at least once per Run B).
- The harness's compare phase MUST grep both run logs for the banner and assert:
  - Run A (the baseline): banner count == 0 (the gated branch should NOT execute).
  - Run B (the gated path): banner count >= 1 (the gated branch MUST execute at least once).
- Exit non-zero (new dedicated exit code) on either invariant violation.
**Rationale.** Bit-equality + NaN-cleanliness are necessary but not sufficient: they pass trivially when both runs collapse to the same code path. A signal-of-life assertion converts that degenerate-pass class into a hard fail.
**Application.** Beyond `framework_loop_mode`, this rule applies to every future audit item where xval-style verification compares gated code paths: `coupling_mode` variations (`tight` vs `prescribed` vs `loose`), `skip_inprocess_engine_run` variations, the C2 `MPI_Barrier` + `flush_year_globally_synchronized` paths (which in single-process mode are stubbed but still distinct from `flush_year`'s per-gridcell-rolling path), and any future `framework_loop_mode` extensions.
**Operational lineage.** Rule #8 joins the existing rule set in `notes/FOLLOWUPS.md` §"Operational heuristics — lessons learned":
- Rule #1 (when outputs are wacky, first-line forensic step = check our `.ins` files vs `version_A/B`'s `.ins` set).
- Rule #6 (asymmetric multi-year writer scaling → check for single OPEN/CLOSE-gating root cause).
- Rule #7 (stale forward-reference TODOs are architectural-finding triggers).
- **Rule #8** (signal-of-life banner-presence assertion for every code-path-gated cross-validation).
### 0.11 C2 close-out tag (`v0.17.5-step17b-c2-mpi-sync`) annotation — decision deferred

The current C2 close-out tag at `f6c192e` was issued with annotation language "tight-coupling closed-loop year_outer mode is now feature-complete on workstation (single-process + mpirun mimic READY)" plus "Verification at tag time: all 4 xval scenarios PASS substantive against build/guess + build_mpi/guess single-process". The B15 finding is that the four xval scenarios at tag time were false-positive PASSes — the year_outer code path was never actually exercised.
Three options are on the table for how to handle the existing tag:
| Option | Approach | Pros | Cons |
|---|---|---|---|
| (a) Errata-style | Leave the existing tag at `f6c192e` untouched. Document the validation-gap-vs-tag-annotation discrepancy in §0 of this file as the canonical errata. | Cleanest history; no force-push; no destructive operations. | Tag annotation message remains misleading without reading §0 of `notes/STEP_17c.md`. |
| (b) Retroactive correction | Delete + re-create the tag with amended annotation message acknowledging the validation gap; force-push to all 3 remotes. | Tag annotation accurately reflects the substantive-validation state at tag time. | Force-push on a multi-remote tag; destructive; requires stash-style discipline if any downstream tooling has cached the old tag object. |
| (c) Defer | Leave the tag for now. Decide after B15 is fixed and the four xval scenarios are re-run with year_outer actually exercised. If the re-verification on the same commit (`f6c192e`) substantively passes (i.e., the underlying code at the tag is correct, only the harness was broken), the existing tag is retroactively correct and option (a)'s minimal errata note suffices. If the re-verification reveals real correctness gaps in the year_outer block at `f6c192e`, then (b) becomes substantively justified. | Lets evidence drive the decision. | Brief window of ambiguity between B15 fix and re-verification. |
**Decision (2026-05-12 forensic commit): (c) defer.** Rationale: the B15 fix lands at HEAD, not at the tagged commit; the four-xval re-verification will exercise both `build/guess` and `build_mpi/guess` single-process builds at HEAD-with-B15-fix, but the underlying code logic at `f6c192e` is unchanged. So the re-verification effectively answers the question "does the year_outer block at the tagged commit substantively work?" — and the answer is what should drive the tag-amendment decision. This is recorded here as the canonical decision; option (a) or (b) will be selected and executed in a subsequent commit once the data is in.
### 0.12 Salvaged WIP — what we stashed and why

A pre-forensic exploratory pass at the B15 + B16 fixes (before the user-mandated forensic-first ordering was reasserted) produced 5 modified files in the working tree of `lpj-guess_imogen_landsymm/`. These were stashed before the empirical reproduction (Phase 1 of the forensic) so the reproduction would test true HEAD code, not WIP-modified code. The stash:
| File | Lines | Substance |
|---|---|---|
| `scripts/cross_validate_year_outer.sh` | +127 / −3 | B15 wrapper-writer fix (param → bare for `framework_loop_mode`) + signal-of-life banner-presence assertion in `compare_outputs()` (rule #8 prototype) + large justifying comment blocks |
| `runs/SSP1-2.6/main_xval_imogencfx.ins` | +15 / −1 | B15 syntax fix in the imported xval base ins (param → bare); large comment block |
| `runs/SSP1-2.6/main_xval_loose.ins` | +8 / −1 | B15 syntax fix (symmetric to imogencfx variant); shorter comment block |
| `lpjguess/modules/imogen_input.cpp` | +35 / −9 | B16 eager-cache-check removal in `preload_all_climate`; large justifying comment block |
| `lpjguess/modules/imogencfx.cpp` | +29 / −11 | B16 symmetric removal; parallel comment block |
The stash is preserved at `stash@{0}` with descriptive message; a patch backup is preserved at `_chat_artifacts/B15_B16_WIP_PRE_FORENSIC_2026-05-12.patch` (16 881 B; sha256 `a5d6c5b0bb2d2a4bc55f1a6342f461bce177dd79abde93f55d749c9860b59271`). Recovery: `git stash pop` OR `git apply _chat_artifacts/B15_B16_WIP_PRE_FORENSIC_2026-05-12.patch`.
The salvaged WIP will NOT be applied verbatim. It contains useful narrative reasoning (the comment blocks explain the parser-mechanism finding mid-investigation) but predates the formal forensic; some claims in the WIP comments are slightly imprecise compared to §0.5 above. The actual B15 fix commit will:
- Re-derive the F1-F4 changes from this §0 forensic.
- Use this file's §0.5 as the canonical citation in inline comment blocks at the modified sites (instead of the WIP's mid-investigation comment text).
- Optionally pull individual hunks from the stash if useful (via `git stash show -p stash@{0}` + selective application).
The B16 fix commit will follow the same pattern after its dedicated forensic in §3 of this file (when we get there).

---

## 1. 17c.0 PREP phase plan (revised post-B15 + post-B16 + post-B17 forensic + post-B17(a)-fix + post-B17(b)-provisional-acceptance + post-collapsed-renumbering)

The 17c.0 PREP phase as originally planned (per session-3 handoff §0.4 → 5-phase plan item 1) was a single workstation `mpirun -np 4` mimic verification, fulfilling the deferred-from-C2 obligation. The B15 forensic (17c.0.0) surfaced two prerequisites that must land first; the B16 fix (17c.0.3) further surfaced B17 (a third prerequisite); the B17 forensic deep-dive (17c.0.4 Phase A) materially revised B17 from a single combined (a)+(b) sub-phase into a B17(a) close + B17(b) decision-deferral split; the 17c.0.4-followup commit (`2771939`, doc-only) operationally accepted B17(b) at a provisional 2% tolerance per §3.8.5 and the user-authorised collapsed renumbering convention then re-cast 17c.0.5 from the originally-planned α/β decision sub-phase to the **full 4-xval re-verify on the B17(b)-provisionally-accepted HEAD** (see §3.8.5 "Sub-phase renumbering implication"). The current PREP phase plan:
| Sub-phase | Scope | Estimated effort | Status |
|---|---|---|---|
| 17c.0.0 | **B15 + B16 forensic record (commit `2beff31`).** Doc-only; ZERO source change. | 0.5 d (actual) | ✅ DONE 2026-05-12 |
| 17c.0.1 | **B15 fix + signal-of-life assertion (F1-F5 from §0.8; F5 included).** Three .ins/.sh changes + harness assertion + ~3-LOC C++ runtime diagnostic. | 0.5-1 d (actual: ~3-4 h elapsed including doc cascade) | ✅ DONE 2026-05-13 (commit `019c9dd`; bundled with 17c.0.2) |
| 17c.0.2 | **Four-xval re-verification on B15-fixed HEAD.** First time year_outer actually exercised. 1cell scenarios PASS substantive + signal-of-life clean; 4cell scenarios surface B16 as anticipated. | 0.5 d (actual: ~10 min wall-clock) | ✅ DONE 2026-05-13 (commit `019c9dd`; bundled with 17c.0.1) |
| 17c.0.3 | **B16 forensic + fix (G1-G4 from §2.6).** Eager-cache-check removal in `preload_all_climate` (both modules; G1+G2) + base-class doc augmentation in `inputmodule.h` (G3) + per-miss inner-fail tightening with `cell_idx` (G4). Full B16 forensic write-up as §2 of this file. Includes empirical surface of NEW audit item B17 from gates 7+8 controlled-fail (full B17 forensic surface as §3; B17 fix deferred to 17c.0.4). | 0.5-1 d (actual: ~3-4 h elapsed including doc cascade and recovery from MPI build mistake) | ✅ DONE 2026-05-13 (commit `4d09b62`; B16 mechanically fixed; B17 surface exposed) |
| 17c.0.4 | **B17 forensic deep-dive (Phase A; falsifies §3.4 hypothesis 1+2; reclassifies B17(b) as stochastic-process sensitivity per cell-iteration-order RNG slip; full empirical drift-magnitude characterization in new §3.8) + B17(a) fix (option (a1) from §3.6: harness sort-then-diff in `compare_outputs()` with `LC_ALL=C sort -k1,1n -k2,2n -k3,3n` on (Lon, Lat, Year), preserving header; ~100 LOC addition + 3 LOC modification in `scripts/cross_validate_year_outer.sh`).** B17(b) DECISION (α tolerance-based comparison vs β seed-tracking dprintf root-cause investigation) DEFERRED to 17c.0.5 (NOTE: subsequently SUPERSEDED by 17c.0.4-followup operational acceptance per §3.8.5). Full landing record as §1.3 of this file. | 1 d (actual: ~5-6 h elapsed including Phase A forensic + implementation + dry-run verification + 8-gate verification + doc cascade) | ✅ DONE 2026-05-13 evening (commit `027d90d`; B17(a) CLOSED via .sh-only harness change; B17(b) reclassified) |
| 17c.0.4-followup | **B17(b) operational acceptance at provisional 2% cell-total tolerance + sub-phase renumbering decision deferral.** Doc-only (3 in-tree files + 1 sibling-artifact); ZERO source-logic change. Lands the new §3.8.5 sub-section as the canonical forensic-record entry for the operational-acceptance decision. Full landing record as §1.4 of this file. | 0.2 d (actual: ~1.5 h elapsed including doc drafting + cascade + commit + push) | ✅ DONE 2026-05-13 night (commit `2771939`; B17(b) provisionally accepted at 2% with re-eval triggers per §3.8.5) |
| 17c.0.5 | **Full 4-xval re-verify on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD `2771939` (gates 1-8) + harness stale-reference cleanup post-collapsed-renumbering convention adoption (4 surgical -1/+1 edits at `scripts/cross_validate_year_outer.sh` lines 305-306, 429, 484, 630-633; ZERO behaviour change; +10/-5 LOC).** Per §3.8.5 collapsed-renumbering decision (user-authorised 2026-05-13 night-late session 4), this sub-phase replaces the originally-planned α/β decision sub-phase. The deferred formal Option α/β closure now reactivates as a future sub-phase TBD (identifier assigned at reactivation time) only on a §3.8.5 re-evaluation trigger firing per §3.8.5.5. Establishes the canonical baseline routine xval re-verify envelope (15+5+17 + exit 2) for the re-eval cadence. Full landing record as §1.5 of this file. | 0.5 d (actual: ~3-4 h elapsed including 8-gate verification + script cleanup + smoke-retest + doc cascade) | ✅ DONE 2026-05-13 night-late (this commit; verification-only + script cleanup; ZERO source-logic change; envelope BYTE-IDENTICAL to 17c.0.4 per §1.5.5+§1.5.6) |
| 17c.0.6 | **B17(b) MECHANICAL CLOSURE via 4-LOC surgical correction of the closed-form `spinup_year_idx` reproduction formula in `lpjguess/modules/imogen_input.cpp` + `lpjguess/modules/imogencfx.cpp` (4 source-side LOC at 4 symmetric sites + 6 doc-comment blocks at the same sites + 2 .h header doc-block updates) + C2 close-out tag (a)-refined annotation amendment BUNDLED in same commit/push event.** **EXERCISES THE §3.8.5.5 5TH CADENCE BULLET PERMITTED-REACTIVATION SURFACE** introduced at 17c.0.5-clarification (commit `e03ceb1`); user authorised proactive revisit of B17(b) per the verbatim 2026-05-14 night → 2026-05-15 early morning directive _"I would prefer that we try to see if we can resolve the issue"_ + _"Your recommended path sounds good to me"_. Phase A pre-instrumentation code review (per Phase A todo block in chat handoff §6.1) high-confidence-identified the root cause as the formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` derived in `notes/STEP_17a.md` §5.4 based on a false assumption that `spinup_year_idx` persists across cells in gridcell_outer mode (the actual code RESETS spinup_year_idx = 0 per cell in getgridcell() at `imogen_input.cpp:880` + `imogencfx.cpp:1122`); Phase B + Phase C instrumentation skipped as no longer needed; Phase D direct fix authoring + 8-gate verification CONFIRMS mechanical closure with `15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER` envelope on BOTH 4cell xval scenarios (gates 7+8) — the 17 previously-SORTED_DIFFER per-PFT-total + tot_runoff files are now ALL SORTED_EXACT (data identical between modes after row-order normalization). Bundled C2 close-out tag amendment per (a)-refined approach: amend `v0.17.5-step17b-c2-mpi-sync` annotation in place at `f6c192e`, preserving original annotation text within new updated message + adding post-B15 + post-B17(a) + post-B17(b)-mechanical-closure verification summary. Full landing record as §1.6 of this file + canonical forensic narrative as new §3.8.6. Originally-planned 17c.0.6 scope (C2 close-out tag amendment ALONE) absorbed into this expanded sub-phase per user-authorised recommended-path 2026-05-15 ~01:44 UTC+2; downstream sub-phase numbering preserved (17c.0.7 = workstation `mpirun -np 4` mimic; 17c.0.8 = PREP phase close-out). | 0.5 d (actual: ~3-4 h elapsed including Phase A code review + Phase D fix authoring + 8-gate verification + 6-surface cascade + commit + ff-merge + tag operations + 3-remote push) | ✅ DONE 2026-05-15 early morning (this commit; B17(b) mechanically CLOSED + C2 close-out tag (a)-refined amendment landed) |
| 17c.0.7 | **Workstation `mpirun -np 4` mimic verification** (the original PREP obligation; the deferred-from-C2 obligation per session-2 §17.7). NEW dedicated harness `scripts/cross_validate_mpi_4rank.sh` (per `notes/STEP_17c.md` §1.6 below) orchestrates baseline single-process + `mpirun -np 4` runs for 3 coupling modes (loose, prescribed, tight) on a 4-cell × 11-yr smoke scenario; compares aggregated `.out` files (per-cell + per-mode) AND the four LPJG-side handshake files (`imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt`, `imogen_lpjg.txt`, `done`) at `<DIR_COMMON>/LPJG_main/IMOGEN/`. **EMPIRICALLY CONFIRMS** `MPI_Barrier` + `MPI_Allreduce(MPI_SUM)` in `flush_year_globally_synchronized` produces bit-exact handshake files between single-process and 4-rank runs for all non-loose modes (loose mode correctly produces no handshake files — design-correct ABSENT_BY_DESIGN classification). ALSO landed: **Path α handshake-file write-path defect fix** at the xval harness layer (`DIR_COMMON` injection for non-loose modes; pre-fix the empty default caused `mkdir(/LPJG_main/IMOGEN/)` to fail permission-check at runtime; full Path α forensic in §3.10 of this file) + **5 LOC of TRUNK-RELEVANT unit doc-comment clarifications in `lpjguess/framework/guess.h`** (N2O_FIRE + N2O_SOIL + 3 sibling N-cycle flux types: N2_FIRE, NH3_SOIL, NO_SOIL — all previously had no unit comments) + **~8 LOC of TRUNK-IRRELEVANT-by-novelty comment-clarity cleanup in `lpjguess/modules/imogenoutput.cpp:75-79`** (N2O_PER_N constant; same numerical conversion 44/28; clearer wording). (Numbering preserved from prior table; renumbered from 17c.0.6 in 17c.0.3 commit due to insertion of B17-fix sub-phase above.) | 1 d (actual: ~6-8 h elapsed including harness authorship + Path α investigation + 6-surface doc cascade) | ✅ DONE 2026-05-15 (this commit; tagged `v0.17.7-step17c-mpi-4rank-mimic` post-merge) |
| 17c.0.8 | **PREP phase close-out.** Pure book-keeping doc cascade across 6 in-tree surfaces (`notes/STEP_17c.md` §1.7 NEW landing record + Status block update + §1 PREP table footer + Index entry; `notes/FOLLOWUPS.md` Status dashboard refresh + B19 + B20 PRIORITY: HIGH annotations + F-12 row update; `CHANGELOG.md` NEW dated entry; `EXECUTION_PLAN.md` row 17c update; `notes/TRUNK_R13078_BACKPORT_LEDGER.md` NEW step-17c-17c.0.8 entry; `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` NEW Part 8) + **tagged `v0.17.8-step17c-prep-complete`** (revised UP from the originally-planned un-tagged checkpoint per user-authorised 2026-05-15 ~22:30 UTC+2 in light of the 11-sub-phase 4-day PREP arc warranting a clean reference point). ZERO source-code change; backport-IRRELEVANT-by-novelty. (Numbering preserved from prior table; renumbered from 17c.0.7 in 17c.0.3 commit.) | 0.2 d (actual: ~1.5-2 h elapsed including 6-surface cascade drafting + commit + ff-merge + tag + 3-remote push) | ✅ DONE 2026-05-15 night (this commit; tagged `v0.17.8-step17c-prep-complete` post-merge; 3-remote-converged at `origin/main`/`kit/main`/`helmholtz/main`) |
| ~~(deferred future sub-phase TBD)~~ | ~~**Formal Option α (tolerance-based comparison upgrade to `compare_outputs()`) OR Option β (seed-tracking dprintf root-cause investigation per §3.8.4) for B17(b) closure.**~~ **RETIRED-SUPERSEDED at 17c.0.6** — B17(b) mechanically CLOSED via the spinup_year_idx formula correction per §3.8.6 (root-cause fix) without needing either Option α OR Option β. The deferred sub-phase mechanism was originally created to gate Option α/β against §3.8.5 re-evaluation triggers firing OR §3.8.5.5 5th cadence bullet PERMITTED-revisit firing; the PERMITTED surface FIRED on 2026-05-14 night (user proactive revisit) and yielded the §3.8.6 mechanical closure, retiring the entire deferred-sub-phase mechanism in the same operation. | ~~0.5-2 d~~ | ✅ **RETIRED-SUPERSEDED at 17c.0.6 via §3.8.6 mechanical closure** (PERMITTED-revisit fired successfully on 2026-05-14 night → 2026-05-15 early morning) |
Total revised PREP estimate: ~4.5-7 d (was: ~4.5-7 d at end of 17c.0.3). The 17c.0.4 split (B17(a) close + B17(b) defer) + 17c.0.4-followup operational acceptance + 17c.0.5 collapsed renumbering preserves the total budget — same total work, just sequenced for lower-risk delivery and with the formal Option α/β closure deferred outside the PREP critical path. Sub-phases 17c.0.0 + 17c.0.1 + 17c.0.2 + 17c.0.3 + 17c.0.4 + 17c.0.4-followup + 17c.0.5 + 17c.0.5-clarification + 17c.0.6 + 17c.0.7 + **17c.0.8 (this commit)** are ALL landed. **🎉 Step 17c.0 PREP phase is now OFFICIALLY COMPLETE — 11/11 sub-phases done; 0 d remaining in PREP.** Total actual PREP elapsed time (2026-05-12 morning → 2026-05-15 night): ~4 calendar days across 4 chat sessions (session 3 = 17c.0.0; session 4 morning = 17c.0.1+17c.0.2+17c.0.3+17c.0.4+17c.0.4-followup+17c.0.5+17c.0.5-clarification; session 4 continuation early morning 2026-05-15 = 17c.0.6; session 4 continuation evening 2026-05-15 = 17c.0.7; session 4 continuation night 2026-05-15 = 17c.0.8 this commit). **Next-task cluster (per user-authorised 2026-05-15 ~19:30 UTC+2 + ~22:30 UTC+2)**: **B19** (essential closed-loop pipeline verification of stages 2-7; ~2.5-4 d revised down from 3-7 d after 2026-05-15 night code-reality check confirming steps 10/11/12/13/14 are all already DONE) → **B20** (recommended literature-comparison sanity check; ~1-2 d) → **17c.1 → 17c.4 cluster phases** on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative). Full B19/B20 sub-item breakdowns in `notes/FOLLOWUPS.md` audit-items table.

### 1.1 17c.0.1 + 17c.0.2 landing record — B15 fix + signal-of-life assertion + four-xval re-verification (commit `019c9dd`, 2026-05-13)

The B15 fix design from §0.8 (F1-F5) was approved verbatim in session 4 with the user's authorisation to include F5 (the optional ~3-LOC C++ runtime diagnostic). The salvaged WIP at `stash@{0}` (per §0.12) was used as the starting point for F1-F4 via a hybrid cherry-pick strategy (per §0.12's "individual hunks may be pulled from the stash if useful" provision); F5 was authored fresh against the §0.5 + §0.8(F5) canonical citations.

#### 1.1.1 Strategy recap

- **F1-F4**: hybrid cherry-pick from `stash@{0}` for the three in-scope files (`scripts/cross_validate_year_outer.sh`, `runs/SSP1-2.6/main_xval_imogencfx.ins`, `runs/SSP1-2.6/main_xval_loose.ins`). The salvaged WIP comments aligned precisely with §0.5's plib-parser walkthrough; only one cosmetic anchor-text touch-up needed (`§0.B15` → `§0 (audit item B15)`; 6 occurrences across the 3 files). The C++ stash hunks for `lpjguess/modules/{imogen_input,imogencfx}.cpp` (B16 WIP; +35/-9 + +29/-11) were **NOT** applied; they remain in `stash@{0}` for use as a starting point in 17c.0.3.
- **F5**: authored fresh in `lpjguess/framework/framework.cpp` immediately after `read_instruction_file()` returns at line 337. ~3 LOC of `dprintf` + ~17 LOC of doc block (`§339-357`).
- **Stash retention**: `stash@{0}` is **NOT dropped** — its B16 hunks are useful starting material for 17c.0.3.

#### 1.1.2 Per-file diff stats

| File | LOC | Class | Backport |
|---|---|---|---|
| `scripts/cross_validate_year_outer.sh` (F3 + F4) | +127 / −3 | Harness; bash | **IRRELEVANT** (not in `trunk_r13078`) |
| `runs/SSP1-2.6/main_xval_imogencfx.ins` (F1) | +15 / −1 | Run config; plib `.ins` | **IRRELEVANT** (per-fork run config) |
| `runs/SSP1-2.6/main_xval_loose.ins` (F2) | +8 / −1 | Run config; plib `.ins` | **IRRELEVANT** (per-fork run config) |
| `lpjguess/framework/framework.cpp` (F5) | +21 / 0 | C++ source; framework | **RELEVANT** (lives in `trunk_r13078`'s framework as a near-identical sibling file) |

#### 1.1.3 F4 (signal-of-life assertion) — implementation per rule #8 + §0.8

Implements rule #8 verbatim. After the existing `cmp -s` byte-equality check + the B12 NaN gate, `compare_outputs()` greps both run.logs for the `[year_outer]` banner (emitted at `lpjguess/framework/framework.cpp:502` inside the gated branch). Pass condition: `banner_a == 0` AND `banner_b >= 1`. Failure exits the harness with code **4** (new exit class; non-overlapping with existing 0=PASS, 1=ZERO-out-files, 2=byte-mismatch, 3=NaN-substantive). Both failure cases (Run A wrongly entered the gated branch; Run B did not exercise year_outer) carry self-explanatory FAIL messages with cross-references back to §0 (audit item B15) of this file. The PASS message is updated to mention the banner count: `"PASS (substantive + signal-of-life): All .out files are bit-exact AND non-NaN between Run A and Run B, AND the year_outer banner appeared N time(s) in Run B's log (and 0 times in Run A's log) — confirming the year_outer code path was actually executed in Run B and NOT in Run A."`

A subtle bash gotcha around `grep -c` exit-code semantics is captured in an inline comment block in the harness: `grep -c` always prints `0` to stdout when there are no matches but exits with rc=1; the implementation uses `$(grep -c '\[year_outer\]' run.log || true)` per-file (with `[ -f file ]` guards) to suppress the rc-1-to-no-output issue. This pattern is non-trivial to re-derive from scratch and was preserved verbatim from the WIP.

#### 1.1.4 F5 (consumer-side runtime diagnostic) — implementation per §0.8(F5)

Placement: immediately after `read_instruction_file(args.get_instruction_file());` at `lpjguess/framework/framework.cpp:337`, before the existing `firsthistyear`/`lasthistyear` sanity check at line 362. The implementation:

```cpp
dprintf("[framework] framework_loop_mode = \"%s\" (after .ins parse)\n",
        (const char*)IMOGENConfig::framework_loop_mode);
```

`IMOGENConfig::framework_loop_mode` is in scope at this site (already accessed at line 464 for the gating decision; no new include needed). The idiomatic LPJ-GUESS `dprintf` (not libc `dprintf(int fd, ...)`) is used; matches the pattern at framework.cpp:346 + lines 502/504/507 + many other framework sites. The xtring-to-`const char*` cast follows §0.8(F5)'s canonical recommendation. ~17 LOC of explanatory doc block (§339-355) cite §0 (audit item B15) §0.6 + §0.8(F5) + the relationship to F4 (independent defense layers); also flags the B17-class detection capability (catches typo'd values like `"year_outter"` that the harness rule-#8 banner check cannot surface).

#### 1.1.5 Anchor-text touch-up

The salvaged WIP referenced `notes/STEP_17c.md §0.B15` (a non-existent anchor; the actual section is `§0` with the B15 forensic at `§0.3`-`§0.8` and B16 acknowledgement at `§0.9`). All 6 occurrences across the 3 stashed files were touched up in-flight (during stash extraction via `git show stash@{0}:path | sed 's/§0\.B15/§0 (audit item B15)/g'`) to read `§0 (audit item B15)`. This preserves the B15 association while pointing readers to the actual section anchor. Zero `§0.B15` literals remain in the repository post-fix. F5's freshly-authored doc block uses the consistent `§0 (audit item B15) §0.6 + §0.8(F5)` format from inception.

#### 1.1.6 Verification gates 1-4 — clean rebuilds + unit tests

| # | Gate | Result | Notes |
|---|---|---|---|
| 1 | `cd lpjguess/build && cmake --build . --target guess` | ✅ ZERO new warnings | Incremental rebuild: framework.cpp.o + relink |
| 2 | `cd lpjguess/build_mpi && cmake --build . --target guess` | ✅ ZERO new warnings | Incremental rebuild: framework.cpp.o + imogen_input.cpp.o + imogencfx.cpp.o + relink (the latter two recompiled due to slightly different mtime cache vs `build/`; not behavioural) |
| 3 | `lpjguess/build/runtests --reporter compact` | ✅ 25 cases / 162 assertions PASS | Regression baseline preserved |
| 4 | `lpjguess/build_mpi/runtests --reporter compact` | ✅ 25 cases / 162 assertions PASS | Regression baseline preserved |

Empirical warning grep on each rebuild log returns zero `warning|error` matches.

#### 1.1.7 Verification gates 5-8 — four-xval re-verification (THE substantive 17c.0.2 evidence)

| # | Gate | harness `rc` | Bit-exact | NaN | banner_a (run.log `[year_outer]` count) | banner_b | F5 echo | Result |
|---|---|---|---|---|---|---|---|---|
| 5 | `scripts/cross_validate_year_outer.sh 1cell imogen` | **0** | 37/37 | 0 | 0 | **5** | "gridcell_outer" / "year_outer" | ✅ **PASS substantive + signal-of-life** |
| 6 | `scripts/cross_validate_year_outer.sh 1cell imogencfx` | **0** | 37/37 | 0 | 0 | **5** | "gridcell_outer" / "year_outer" | ✅ **PASS substantive + signal-of-life** |
| 7 | `scripts/cross_validate_year_outer.sh 4cell imogen` | **99** | n/a | n/a | 0 | **3** | "gridcell_outer" / "year_outer" | ⚠️ **B16 surface (anticipated per §0.9)** — Run A clean (37 .out files); Run B exits 99 with `"ImogenInput::preload_all_climate: stored_years cache already full (last_store_index=9 >= nyears=9) when preloading cell (-95.75,80.25)"` |
| 8 | `scripts/cross_validate_year_outer.sh 4cell imogencfx` | **99** | n/a | n/a | 0 | **3** | "gridcell_outer" / "year_outer" | ⚠️ **B16 surface (anticipated per §0.9)** — symmetric: `IMOGENCFXInput::preload_all_climate` same fail at same cell `(-95.75,80.25)` |

**Interpretation of gates 5-6 (substantive value of this commit):** This is the **first time the year_outer code path has actually been exercised** in any cross-validation since C1 close-out (`v0.17.0-step17a-c1-year-outer-single-process` 2026-05-10) — equivalently: the entire C1 + C2 era's substantive validation status was a false positive per §0.3. Run B's run.log shows the F5 banner at line 3 (`[framework] framework_loop_mode = "year_outer" (after .ins parse)`) followed immediately by the year_outer initialization banner (`[year_outer] starting framework_loop_mode = "year_outer" (F-12 sub-milestone C1; step 17a)`), the per-cell setup banner, and the preload banner — **5 banners total in the 1cell case**. Run A's run.log shows the F5 banner at line 3 (`[framework] framework_loop_mode = "gridcell_outer"`) and zero `[year_outer]` banners. The contrast is observable, the gate is unambiguous, and the same 37 `.out` files match bit-for-bit. The byte-equality result that was a false positive at C2 close-out is now genuine — it's the first time bit-equality + non-NaN + signal-of-life all hold simultaneously.

**Interpretation of gates 7-8 (positive empirical evidence + 17c.0.3 trigger):** The fail messages are textbook §0.9 reproductions:
- `4cell imogen`: `ImogenInput::preload_all_climate: stored_years cache already full (last_store_index=9 >= nyears=9) when preloading cell (-95.75,80.25). Check init() nyears computation.`
- `4cell imogencfx`: `IMOGENCFXInput::preload_all_climate: stored_years cache already full (last_store_index=9 >= nyears=9) when preloading cell (-95.75,80.25). Check init() nyears computation (formula: nyears = (lasthistyear - FIRST_SPINUP_YEAR) + 1; should be >= the number of distinct imogen_year values needed across all cells x all spinup years; bump lasthistyear in .ins if too small).`
The fault site (`cell_idx=1`) and the `last_store_index=nyears=9` numerics match §0.9's prediction precisely (4 cells × 9 distinct imogen_years span = 9 cumulative slots; cell 0 fills all 9; cell 1 enters with `last_store_index >= nyears` true → eager check fires). Both Run A scenarios (gridcell_outer baseline) complete cleanly with 37 .out files, confirming the gridcell_outer code path is unaffected and the failure is exclusive to the year_outer `preload_all_climate` invocation. This is positive empirical evidence that:
1. **B15 is genuinely fixed**: year_outer is reaching `preload_all_climate` for the first time across `cell_idx >= 1` — pre-B15 this code path silently never executed for any Run B.
2. **B16 surfaces exactly as §0.9 predicted**: both modules; same cell; identical error semantics; same numerics.
3. **17c.0.3 (B16 forensic + fix) becomes the next sub-phase**, with this empirical reproduction as the canonical input data point (analogous to how §0.3's empirical reproduction became the canonical B15 input).

#### 1.1.8 Cross-check: F5 banner observability + year_outer banner counts

Banner-presence counts grepped from each scenario's two run.logs (`runs/SSP1-2.6/Common-directory/xval_runs/<scenario_name>/run.log`):

| Scenario | F5 banner present (Run A) | F5 banner present (Run B) | F5 echo Run A value | F5 echo Run B value | `[year_outer]` count Run A | `[year_outer]` count Run B |
|---|---|---|---|---|---|---|
| `1cell imogen` | ✅ | ✅ | `"gridcell_outer"` | `"year_outer"` | 0 | 5 |
| `1cell imogencfx` | ✅ | ✅ | `"gridcell_outer"` | `"year_outer"` | 0 | 5 |
| `4cell imogen` | ✅ | ✅ | `"gridcell_outer"` | `"year_outer"` | 0 | 3 (year_outer started, then exited 99 at preload) |
| `4cell imogencfx` | ✅ | ✅ | `"gridcell_outer"` | `"year_outer"` | 0 | 3 (year_outer started, then exited 99 at preload) |

This table is the canonical evidence that **both F4 and F5 are observably effective** in all four scenarios. F5's value is most directly visible in the 4cell B16-affected scenarios: even when Run B ultimately fails at `preload_all_climate`, the F5 banner at line 3 of Run B's run.log unambiguously reports `framework_loop_mode = "year_outer"` (the parsed value matches the override intent). Pre-F5, this would have been invisible.

#### 1.1.9 Backport classification

This commit is a **mixed cluster-config-only + source-level commit**:
- **Backport-IRRELEVANT** (cluster-config + harness; not in `trunk_r13078`): F1 (`runs/SSP1-2.6/main_xval_imogencfx.ins`), F2 (`runs/SSP1-2.6/main_xval_loose.ins`), F3 + F4 (`scripts/cross_validate_year_outer.sh`).
- **Backport-RELEVANT** (C++ source change in `lpjguess/framework/framework.cpp`, which exists in `trunk_r13078`): F5. The F5 dprintf placement (post-`read_instruction_file()`, pre-input-module-init) is structurally identical in `trunk_r13078`'s framework loop; the ~3-LOC `dprintf` + ~17-LOC doc block can be copied verbatim. The TRUNK_R13078_BACKPORT_LEDGER.md entry for step 17c.0.1 captures the F5 backport directive.

Per session-4 prompt §"Documentation cascade" + the carry-forward rule from session 3 §0.6(4): because F5 is included, this commit follows the **6-file source-level cascade**: STEP_17c.md (this section §1.1) + CHANGELOG.md + EXECUTION_PLAN.md row 17c + FOLLOWUPS.md status dashboard refresh + TRUNK_R13078_BACKPORT_LEDGER.md step-17c-17c.0.1 entry + session-3 chat handoff Part 2.

#### 1.1.10 What 17c.0.3 must do next

17c.0.3 will land the B16 fix per §0.9's recommended approach:
1. Remove the eager `if (last_store_index >= nyears) fail(...)` check at the start of `ImogenInput::preload_all_climate` (`lpjguess/modules/imogen_input.cpp`).
2. Symmetric removal at the start of `IMOGENCFXInput::preload_all_climate` (`lpjguess/modules/imogencfx.cpp`).
3. Document the cumulative-across-cells cache design intent inline at both sites + in `lpjguess/modules/inputmodule.h`'s `preload_all_climate` doc block.
4. Verify the inner cache-miss-branch's per-miss check at `imogen_input.cpp` (and the symmetric site in `imogencfx.cpp`) still provides correct fail-fast semantics with proper context (cell coordinates + offending imogen_year + cache size).
5. Re-run gates 5-8 (the four-xval scenarios) on B15+B16-fixed HEAD (this is sub-phase 17c.0.4); all four should pass cleanly with year_outer exercised in Run B.
The B16 forensic write-up (root cause + fix design + verification) will live as a new top-level section §2 of this file (analogous to §0's structure), pushing the current cluster-phases skeleton to §3.

#### 1.1.11 Stash entry retention

`stash@{0}: On main: B15+B16 WIP, pre-forensic salvage [session 3, 2026-05-12]` is **preserved unchanged** across this commit. Its B16 C++ hunks (`lpjguess/modules/imogen_input.cpp` +35/-9 + `lpjguess/modules/imogencfx.cpp` +29/-11) remain useful starting material for 17c.0.3 (analogous to how its in-scope hunks were used here for F1+F2+F3+F4). After 17c.0.3 lands, the stash will be evaluated for drop vs further retention.

### 1.2 17c.0.3 landing record — B16 forensic + fix + four-xval re-verification surfacing B17 (this commit, 2026-05-13)

The B16 fix design from §0.9 + §2.6 (G1-G4) was approved verbatim in session 4 with the user's authorisation to include G4 (the inner per-miss diagnostic tightening with `cell_idx`). The salvaged WIP at `stash@{0}` (per §0.12) was used as the starting point for G1+G2 via the same hybrid cherry-pick strategy used for 17c.0.1's F1-F4; G3 was authored fresh against the cumulative-cache contract documented in §2.4; G4 was authored fresh against the inner-fail diagnostic patterns inherited from 17c.0.1's banner-presence asserts.

#### 1.2.1 Strategy recap

- **G1+G2**: hybrid cherry-pick from `stash@{0}` for the two C++ source files (`lpjguess/modules/imogen_input.cpp` and `lpjguess/modules/imogencfx.cpp`). The salvaged WIP comments aligned with §2.4's cumulative-cache walkthrough; cosmetic anchor-text touch-ups: `§0.B16` → `§2 (audit item B16)` (multiple occurrences); date refresh `2026-05-12` → `2026-05-13`; and addition of the cross-reference to commit `019c9dd` (the B15-fix commit that unmasked B16 empirically). The C++ stash hunks for `imogen_input.cpp` (+35/-9) and `imogencfx.cpp` (+29/-11) **were applied** with the touch-ups described above.
- **G3**: authored fresh in `lpjguess/framework/inputmodule.h`. Augments the existing `InputModule::preload_all_climate` virtual function doc block with ~20 LOC of "IMPLEMENTATION GUIDANCE FOR SUBCLASSES" formalising the cumulative-across-cells cache contract (an implementation-level invariant that subclasses must respect; eager checks at function entry violate it).
- **G4**: authored fresh additions to the inner per-miss `fail()` messages in both modules (~4 LOC each). Each inner-fail now reports `cell_idx` alongside the existing `(lon, lat)` + `imogen_year` + cache-size context, providing unambiguous fault attribution when the inner check (correctly) fires on a real cache exhaustion.
- **Stash retention**: `stash@{0}` was the starting point for G1+G2; with G1+G2 now landed, the stash will be **dropped after this commit's 3-remote push converges** (recommended user disposition; the patch backup at `_chat_artifacts/B15_B16_WIP_PRE_FORENSIC_2026-05-12.patch` remains the canonical pre-fix snapshot).

#### 1.2.2 Per-file diff stats

| File | LOC | Class | Backport |
|---|---|---|---|
| `lpjguess/modules/imogen_input.cpp` (G1 + G4 part 1) | +38 / −9 | C++ source; modules | **TRUNK-IRRELEVANT-by-novelty** (`preload_all_climate` doesn't exist in `trunk_r13078`; introduced at C1.3 sub-step 7.3.2 commit `d7f6c74` 2026-05-10; per-fork addition) |
| `lpjguess/modules/imogencfx.cpp` (G2 + G4 part 2) | +20 / −11 | C++ source; modules | **TRUNK-IRRELEVANT-by-novelty** (same rationale; `imogencfx` module is a per-fork addition for IMOGEN tight-coupling) |
| `lpjguess/framework/inputmodule.h` (G3) | +20 / 0 | C++ source; framework | **TRUNK-IRRELEVANT-by-novelty** (the `preload_all_climate` virtual function is a per-fork addition to the `InputModule` base class for the cumulative-cache contract; not in `trunk_r13078`'s base class) |

All three files are TRUNK-IRRELEVANT-by-novelty (not by syntax/semantics): the `preload_all_climate` cumulative-cache machinery was added by this fork as part of the C1.3 inputmodule subclass refactor; trunk's `InputModule` base class doesn't have this virtual function. The TRUNK_R13078_BACKPORT_LEDGER.md entry for step 17c.0.3 documents this directly.

#### 1.2.3 G1+G2 (eager-check removal) — implementation per §0.9 + §2.6

The eager check at `imogen_input.cpp:1111-1118` (and its symmetric twin at `imogencfx.cpp:1366-1376`) reads:

```cpp
if (last_store_index >= nyears) {
    fail("ImogenInput::preload_all_climate: stored_years cache already full "
         "(last_store_index=%d >= nyears=%d) when preloading cell (%g,%g). "
         "Check init() nyears computation.", last_store_index, nyears, lon, lat);
}
```

This eager check is **deleted** at both sites and replaced with a substantial doc block (~38 LOC at `imogen_input.cpp`; ~20 LOC at `imogencfx.cpp`, deferring to the imogen_input.cpp forensic for the full walkthrough) explaining (a) why the eager check was wrong (mis-models the cache as per-cell when it is cumulative across cells); (b) what the correct invariant is (cells produce 100% cache hits if the imogen_years they need are already loaded by prior cells); (c) the inner-fail provides correct fail-fast semantics for genuine cache exhaustion; (d) cross-references to §0.9 + §2 of this file. Anchor-text cosmetics: all `§0.B16` references touched up to `§2 (audit item B16)`. The two doc blocks are anchored at the `[Step 17c (F-12 sub-milestone C3 PREP sub-phase 17c.0.3) — G1/G2: ...]` headers for grep-discovery.

#### 1.2.4 G3 (base-class doc augmentation) — implementation per §2.6

`lpjguess/framework/inputmodule.h:84-102` already contained a doc block for the `InputModule::preload_all_climate` virtual function (declared abstract; no default implementation). The augmentation adds ~20 LOC of "IMPLEMENTATION GUIDANCE FOR SUBCLASSES" formalising the cumulative-across-cells cache contract: subclasses MUST treat any per-cell cache as cumulative-across-cells; subclasses MUST NOT add eager early-exit checks at function entry that assume per-cell cache state; the rationale is the multi-cell year_outer scenario where one cell's cache state is the legitimate starting point for the next cell's preload. Cross-references §2.5 (root cause) + §2.6 (G1+G2 fix).

#### 1.2.5 G4 (inner per-miss diagnostic tightening) — implementation per §2.6

The inner per-miss `fail()` messages at `imogen_input.cpp:1158-1164` and `imogencfx.cpp:1421-1427` already carried `(lon, lat)` + `imogen_year` + `nyears` + `last_store_index` context. G4 adds `cell_idx` to both: this is the most diagnostically valuable single piece of context for distinguishing "cell 0 ran out of slots due to genuine cache-size misconfiguration" (extremely rare) from "cell N>0 ran out of slots due to a different upstream bug shifting the imogen_year sequence" (extremely informative). Augmented `fail()` messages now read:

```
ImogenInput::preload_all_climate: cache exhausted at cell_idx=N (lon,lat)=(...)
when preloading imogen_year=Y; last_store_index=K, nyears=M. ...
```

#### 1.2.6 Anchor-text touch-up

`§0.B16` → `§2 (audit item B16)` across all stash hunks (G1+G2 sites). Zero `§0.B16` literals remain in the repository post-fix. G3+G4 freshly-authored doc blocks use the consistent `§2 (audit item B16)` format from inception.

#### 1.2.7 Verification gates 1-4 — clean rebuilds + unit tests

| # | Gate | Result | Notes |
|---|---|---|---|
| 1 | `cd lpjguess/build && cmake --build . --target guess` | ✅ ZERO new warnings | Incremental rebuild: imogen_input.cpp.o + imogencfx.cpp.o + relink (inputmodule.h is included by both sources; triggers their recompile) |
| 2 | `cd lpjguess/build_mpi && cmake --build . --target guess` (after MPICH_CXX=g++ recovery; see §1.2.10) | ✅ ZERO new warnings (332 total, all pre-existing union of `guess` + `runtests` build outputs) | Clean reconfigure with `MPICH_CXX=g++` to bypass the broken-on-this-workstation Anaconda3 mpicxx-with-conda-gxx path |
| 3 | `lpjguess/build/runtests --reporter compact` | ✅ 25 cases / 162 assertions PASS | Regression baseline preserved |
| 4 | `lpjguess/build_mpi/runtests --reporter compact` | ✅ 25 cases / 162 assertions PASS | Regression baseline preserved |

Empirical warning grep on each rebuild log shows only pre-existing warnings (Timer in `gutil.h`, `cru/guessio` etc.); G1-G4 introduce zero new warnings touching `imogen_input.cpp` / `imogencfx.cpp` / `inputmodule.h`.

#### 1.2.8 Verification gates 5-8 — four-xval re-verification (THE substantive 17c.0.3 evidence)

| # | Gate | harness `rc` | Bit-exact | NaN | banner_a | banner_b | F5 echo | Result |
|---|---|---|---|---|---|---|---|---|
| 5 | `scripts/cross_validate_year_outer.sh 1cell imogen` | **0** | 37/37 | 0 | 0 | **5** | "gridcell_outer" / "year_outer" | ✅ **PASS substantive + signal-of-life** (regression: identical envelope to 17c.0.2 gate 5) |
| 6 | `scripts/cross_validate_year_outer.sh 1cell imogencfx` | **0** | 37/37 | 0 | 0 | **5** | "gridcell_outer" / "year_outer" | ✅ **PASS substantive + signal-of-life** (regression: identical envelope to 17c.0.2 gate 6) |
| 7 | `scripts/cross_validate_year_outer.sh 4cell imogen` | **2** | 15/37 | 0 | 0 | **5** | "gridcell_outer" / "year_outer" | ⚠️ **CONTROLLED-FAIL — surfaces B17 (newly identified)** — Run A clean (37 .out files); **Run B completes the full 9-year run AND emits all 37 .out files** (proving B16 mechanically fixed: pre-fix Run B aborted at `preload_all_climate` exit 99 after 3 banners; post-fix Run B emits all 5 banners and produces full output set). 22/37 .out files differ between Run A + Run B; full B17 forensic surface in §3 below |
| 8 | `scripts/cross_validate_year_outer.sh 4cell imogencfx` | **2** | 15/37 | 0 | 0 | **5** | "gridcell_outer" / "year_outer" | ⚠️ **CONTROLLED-FAIL — surfaces B17 (newly identified)** — symmetric: same 22/37 mismatch pattern; same banner counts; same F5 echo. Confirms B17 is **systemic year_outer multi-cell defect, not input-mode-specific** (identical between imogen and imogencfx variants) |

**Interpretation of gates 5-6 (regression-clean baseline):** The 1cell scenarios PASS with identical envelope to 17c.0.2's gate 5+6 — confirming G1-G4 introduce zero numerical regression in the year_outer 1cell code path. Banner counts match (5 per Run B; 0 per Run A). F5 banner contents match. 37/37 bit-exact. 0/37 NaN. The 1cell scenarios remain the canonical "year_outer-substantively-PASSes" baseline.

**Interpretation of gates 7-8 (B17 surface):** The 4cell scenarios run to **full completion** in both Run A (gridcell_outer baseline) and Run B (year_outer) — proving B16 is mechanically fixed (pre-G1+G2 the run aborted at `preload_all_climate` after `cell_idx=1` triggered the eager check; post-G1+G2 the run completes all 4 cells × 9 years = 36 cell-years emitting 5 `[year_outer]` banners + 37 .out files). However, 22/37 .out files differ byte-wise between Run A and Run B. **This is not B16 failure — B16 is fixed. It's a brand-new audit item (B17) surfacing now that B16 no longer masks the underlying year_outer multi-cell behaviour.** The full B17 forensic — comprising B17(a) (row-emission-order divergence; affects all 22 differing files; 5 of 22 are pure ordering with sort-then-diff returning 0 for those; the other 17 also have B17(b) drift) and B17(b) (small ~1 ULP numerical drift in 17 per-PFT-total / `tot_runoff` files, most prominently in southern-hemisphere cell `(-57.75, -33.75)`) — is documented in §3 of this file.

#### 1.2.9 Cross-check: F5 banner observability + year_outer banner counts

Banner-presence counts grepped from each scenario's two run.logs after gates 5-8:

| Scenario | F5 banner present (Run A) | F5 banner present (Run B) | F5 echo Run A value | F5 echo Run B value | `[year_outer]` count Run A | `[year_outer]` count Run B |
|---|---|---|---|---|---|---|
| `1cell imogen` | ✅ | ✅ | `"gridcell_outer"` | `"year_outer"` | 0 | 5 |
| `1cell imogencfx` | ✅ | ✅ | `"gridcell_outer"` | `"year_outer"` | 0 | 5 |
| `4cell imogen` | ✅ | ✅ | `"gridcell_outer"` | `"year_outer"` | 0 | 5 (year_outer ran to completion; B17 surface is at output-comparison stage, not at run-time) |
| `4cell imogencfx` | ✅ | ✅ | `"gridcell_outer"` | `"year_outer"` | 0 | 5 (same as 4cell imogen) |

**Critical comparison vs 17c.0.2 (B15-fixed-but-B16-still-present)**: at 17c.0.2, gates 7+8 showed `banner_b=3` (year_outer started but aborted at `preload_all_climate`). At 17c.0.3, gates 7+8 show `banner_b=5` (year_outer started, completed preload, completed simulate, emitted writer-flush banner — same banner count as the 1cell PASS scenarios). The 3→5 banner-count delta is the unambiguous mechanical evidence that B16 is fixed.

#### 1.2.10 MPI build recovery side-note (operational lesson)

During gate 2 verification, an unforced operational error wiped `lpjguess/build_mpi/CMakeFiles` + `CMakeCache.txt` based on a misread of an apparent "warning count discrepancy" (8 in MPI build vs 166 in serial build) that was actually a normal stdout/stderr capture artefact. The script's preferred `mpicxx` + Anaconda3 `conda-forge gxx_linux-64` path subsequently failed at link with system NetCDF/HDF5 ABI mismatches. Recovery: clean reconfigure with `MPICH_CXX=g++ cmake -DCMAKE_CXX_COMPILER=mpicxx -DCMAKE_PREFIX_PATH=/home/bampoh-d/anaconda3 -DNETCDF_INCLUDE_DIR=/home/bampoh-d/anaconda3/include -DNETCDF_C_LIBRARY=/home/bampoh-d/anaconda3/lib/libnetcdf.so ..` — i.e., option (a) of the build script's documented compiler-selection options (use system g++ via the mpicxx wrapper for MPI flags only). This worked on first attempt; the resulting `build_mpi/guess` is 2 974 248 bytes vs the serial `build/guess` 2 974 248 bytes (same size; differ at byte 913+ as expected for distinct MPI-flag compilations). Operational lesson logged in `notes/FOLLOWUPS.md` operational-heuristics section: **never `rm -rf` an apparently-working build state without first verifying the hypothesis that triggered the rm (e.g., touch a single source file to confirm incremental rebuild detection works)**.

#### 1.2.11 Backport classification

This commit is a **pure C++ source-level commit** with all changes TRUNK-IRRELEVANT-by-novelty (not by syntax/semantics):
- **TRUNK-IRRELEVANT-by-novelty**: G1 (`lpjguess/modules/imogen_input.cpp`), G2 (`lpjguess/modules/imogencfx.cpp`), G3 (`lpjguess/framework/inputmodule.h`), G4 (parts in both .cpp files). The `preload_all_climate` virtual function + cumulative-cache machinery + eager-check anti-pattern are all per-fork additions that don't exist in `trunk_r13078`. The TRUNK_R13078_BACKPORT_LEDGER.md entry for step-17c-17c.0.3 documents this with the rationale.

Per session-4 prompt §"Documentation cascade" + the carry-forward rule from session 3 §0.6(4): because the changes are all C++ source-level, this commit follows the **6-file source-level cascade**: STEP_17c.md (this section §1.2 + new §2 + new §3 + §4 renumbering) + CHANGELOG.md + EXECUTION_PLAN.md row 17c + FOLLOWUPS.md status dashboard refresh + TRUNK_R13078_BACKPORT_LEDGER.md step-17c-17c.0.3 entry + session-3 chat handoff Part 3.

#### 1.2.12 What 17c.0.4 must do next

17c.0.4 will land the B17 forensic deep-dive + fix per §3.6's recommended approach skeleton (to be elaborated in 17c.0.4 commit):
1. **B17(a) decision**: harness sort-then-diff comparison upgrade (lower-cost; preserves the engine's current per-row writer behaviour) OR engine row-buffering for cell-major emission in year_outer mode (higher-cost; preserves Decision-12 byte-equality strictly). Recommended: harness upgrade per Decision-12's substantive intent (data equality, not literal byte equality) + an explicit "year_outer emits in year-major order" doc note in the engine.
2. **B17(b) investigation**: localise the per-PFT-total / `tot_runoff` accumulator drift. Hypothesis 1: floating-point summation order differs between cell-major and year-major iteration when the per-PFT total is computed cumulatively across cells. Hypothesis 2: a global random-number-generator state advancement order differs (interp_climate or similar). Hypothesis 3: a per-cell intermediate state (e.g., `Gridcell::seed`) is not actually independent of cell-iteration order. Bisect by re-running with single-cell-at-a-time year_outer and comparing against gridcell_outer to isolate the cell-ordering dependency.
3. Re-run gates 5-8 (the four-xval scenarios) on B15+B16+B17-fixed HEAD (this is sub-phase 17c.0.5); all four should pass cleanly with year_outer fully exercised — OR pass with explicit tolerance per §3.6 if B17(b) is confirmed inherent-and-acceptable (e.g., float-summation-order-induced drift that is mathematically unavoidable).
The B17 forensic surface (root cause skeletons for both sub-defects + recommended fix design skeleton) lives as new §3 of this file (analogous to §0 and §2's structure but with the fix-design subsection marked as "to be elaborated in 17c.0.4").

#### 1.2.13 Stash entry retention recommendation

`stash@{0}: On main: B15+B16 WIP, pre-forensic salvage [session 3, 2026-05-12]` was the starting point for G1+G2 (cherry-pick of its B16 hunks for the two .cpp files). With G1+G2 now landed in cleaned-up form (anchor-text touch-ups + date refresh + `019c9dd` reference), the stash's substantive content has been consumed. **Recommended disposition: drop `stash@{0}` after this commit's 3-remote push converges**; the patch backup at `_chat_artifacts/B15_B16_WIP_PRE_FORENSIC_2026-05-12.patch` (16 881 B; sha256 `a5d6c5b0bb2d2a4bc55f1a6342f461bce177dd79abde93f55d749c9860b59271`) remains the canonical pre-fix snapshot for any future archaeology. The drop command is `git stash drop stash@{0}` (executed by the user after the push converges).

### 1.3 17c.0.4 landing record — B17 forensic deep-dive (Phase A) + B17(a) harness sort-then-diff fix + reclassification of B17(b) (this commit, 2026-05-13 evening)

The B17 fix design from §3.6 was approved by the user as **Option A: B17(a)-only narrow-scope landing in 17c.0.4 + defer B17(b) decision (α tolerance vs β root-cause) to 17c.0.5** after Phase A forensic deep-dive surfaced material findings that revised the §3.4 hypothesis space (per §1.3.3 below). The B17(a) sort-then-diff harness fix was authored fresh against the §3.3 mechanical-cause walkthrough + §3.6 option (a1) recommendation; the .ins / .cpp / .h source files in `lpjguess/` and `runs/` are UNCHANGED in this commit (.sh-only scope).

#### 1.3.1 Strategy recap

- **B17(a) FIX (option (a1) from §3.6)**: harness sort-then-diff comparison upgrade in `scripts/cross_validate_year_outer.sh::compare_outputs()`. ~100 LOC addition (new SORT-THEN-DIFF NORMALIZATION block with documentation) + ~3 LOC modification (effective-pass semantic update + final PASS/FAIL message refinement). Sort key: `LC_ALL=C sort -k1,1n -k2,2n -k3,3n` on (Lon, Lat, Year) preserving line-1 header verbatim via `head -1` + `tail -n+2 | sort`. IDEMPOTENT on already-sorted input (per-LC summed files; 1cell scenarios) — the SORT block is GUARDED by `if [ "$mismatches" -gt 0 ]; then ... fi` so it skips entirely when raw cmp -s already passes. Auto-cleanup of temp dir via `mktemp -d` + `trap 'rm -rf "$sort_tmp"' RETURN`. ZERO C++ source change; ZERO .ins / .cpp / .h touch.
- **B17 forensic deep-dive (Phase A; pre-fix)**: per §1.3.3 below, materially revised §3.4 hypothesis 1 (FP-summation roundoff: FALSIFIED by drift-magnitude evidence) and §3.4 hypothesis 2 (global RNG state: FALSIFIED by per-cell-isolated `gridcell.seed`+`stand.seed` architecture). Empirical localizer "cell 0 BIT-EXACT in ALL 17 drift files; cells 1, 2, 3 progressively diverge" reclassifies B17(b) as **stochastic-process sensitivity per cell-iteration-order RNG slip** (full forensic in new §3.8 below).
- **No stash needed**: this sub-phase's fix is .sh-only and was authored fresh from §3.6 option (a1) without recourse to any pre-existing WIP. There is no `stash@{1}` or analogous starting material.

#### 1.3.2 Per-file diff stats

| File | LOC | Class | Backport |
|---|---|---|---|
| `scripts/cross_validate_year_outer.sh` | +103/-3 (~+108/-13 NET including the 75-LOC doc block + 28-LOC SORT-THEN-DIFF block + 14-LOC effective-pass + revised PASS/FAIL message) | B17(a) FIX (the substantive code change) | TRUNK-IRRELEVANT (.sh harness only; no analogous file in trunk_r13078) |
| `notes/STEP_17c.md` | substantive amendment (~+200 LOC: new §1.3 landing record + §3.3 status mark CLOSED + §3.4 amendment with empirical drift-magnitude table + §3.6 status update + new §3.8 reclassified-B17(b) sub-section + header date/status updates) | DOC | TRUNK-IRRELEVANT (notes/) |
| `notes/FOLLOWUPS.md` | status dashboard update: B17 → SPLIT (B17(a) CLOSED 2026-05-13 in this commit; B17(b) RECLASSIFIED + decision deferred to 17c.0.5) | DOC | TRUNK-IRRELEVANT |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | new step-17c-17c.0.4 row | DOC | TRUNK-IRRELEVANT-by-novelty (the .sh harness does not exist in trunk_r13078) |
| `EXECUTION_PLAN.md` | row 17c update with 17c.0.4 landing entry | DOC | TRUNK-IRRELEVANT |
| `CHANGELOG.md` | new dated entry (2026-05-13 late evening) | DOC | TRUNK-IRRELEVANT |

Net code-change footprint: +103/-3 LOC across **1 source file** (`scripts/cross_validate_year_outer.sh`). All other deltas are documentation. **ZERO C++ source change**; **ZERO `.ins` change**; **ZERO `lpjguess/` touch**.

#### 1.3.3 Phase A forensic deep-dive — empirical findings that revised §3.4

Phase A (pre-fix forensic) ran 7 sub-investigations against the existing 17c.0.3 4cell xval output trees in `runs/SSP1-2.6/Common-directory/xval_runs/` (intact from gates 7+8 of `4d09b62`):

**A.2 — Sort-then-diff bisection envelope** (validates §3.4 prediction): exactly 15 BIT_EXACT + 5 PURE B17(a) + 17 B17(a)+(b) = 37/37 textbook match using `LC_ALL=C sort -k1,1n -k2,2n -k3,3n` on (Lon, Lat, Year). The 5 PURE B17(a) files are: `npool.out`, `mch4.out`, `mch4_diffusion.out`, `mch4_ebullition.out`, `mch4_plant.out` — all have ZERO post-sort diff. Confirms sort key choice is correct + B17(a) characterization in §3.3 is empirically valid.

**A.3 — Engine source-code per-cell row-emission paths** (confirms §3.3 mechanical-cause): both `framework.cpp::year_outer @ lines 588-628` (year-major loop) and `framework.cpp::gridcell_outer @ lines 736-817` (cell-major loop) call `output_modules.outannual(gridcell)` per (cell, year) tuple at end-of-year (line 628 + line 817 respectively). Output emission ORDER == loop ORDER. B17(a) is structurally inherent to the loop reorder and cannot be eliminated without engine row-buffering (the rejected option (a2) per §3.6).

**A.4 — Drift-magnitude characterization (FALSIFIES §3.4 hypothesis 1)**: drift magnitudes are NOT ~1 ULP. Worst-case examples for cell `(-57.75, -33.75)`:
| File | Cell-Year-Column | Run A val | Run B val | Abs diff | Rel diff |
|---|---|---|---|---|---|
| `lai.out` | (-57.75,-33.75,1876,TrIBE) | 0.0192 | 0.0158 | 0.0034 | **17.7%** |
| `lai.out` | (-57.75,-33.75,1876,TrBR) | 0.0240 | 0.0194 | 0.0046 | **19.2%** |
| `lai.out` | (-57.75,-33.75,1879,C4G) | 1.5651 | 1.5756 | 0.0105 | 0.67% |
| `cmass.out` | (-57.75,-33.75,1876,Total) | 0.134 | 0.131 | 0.003 | 2.2% |
| `cton_leaf.out` | (94.25,54.25,1879,IBS) | 36.8 | 0.0 | 36.8 | n/a (PFT-establishment event differs) |
| `tot_runoff.out` | (-57.75,-33.75,1876,Total) | 1434.0 | 1424.6 | 9.4 mm | 0.66% |
| `aaet.out` | (-57.75,-33.75,1877,Total) | 175.43 | 173.01 | 2.42 mm | 1.4% |
| `nflux.out` | (-57.75,-33.75,1877,fix) | -14.80 | -14.85 | 0.05 | 0.34% |
~1 ULP at value-magnitude 0.02 would be ~10⁻¹⁸; observed drift is 10⁻³ — six orders of magnitude too large for FP-summation roundoff. **§3.4 hypothesis 1 FALSIFIED**. Pattern fits stochastic-process sensitivity (large relative drift in low-biomass marginal-establishment PFTs like TrIBE, TrBR, IBS; small relative drift in established dominants like C4G, BNE, BINE; cell-total drift bounded ≤ 1.4% relative). The `cton_leaf` 36.8 vs 0.0 is NOT a 36.8-unit numerical drift — it is a discrete PFT-establishment-event difference (Run A: IBS established with C/N=36.8; Run B: IBS not established → C/N reported as 0).

**A.5 — RNG state architecture (FALSIFIES §3.4 hypothesis 2 if per-cell sequence identical)**: `randfrac(long& seed)` at `lpjguess/modules/driver.cpp:42` is a pure functional Park-Miller LCG taking seed by reference; advances seed deterministically per call; returns. **NO global RNG state**. All randomness uses either (a) `gridcell.seed` (per-cell) via `interp_climate(...,seed)` → `prdaily(...,seed)` for climate disaggregation in `imogen_input.cpp:991` + `imogencfx.cpp:1233` (gridcell_outer) AND `imogen_input.cpp:1350` + `imogencfx.cpp:1632` (year_outer); or (b) `stand.seed` (per-stand-per-cell) in `vegdynam.cpp:1018+1061+1218+1482` (fire/disturbance/mortality), `spitfire.cpp:1744+2669+2700+2717`, `blaze.cpp:515+655`. Both seed types initialize to 12345678 in their respective ctors (`Stand::Stand` at `guess.cpp:772`; `Gridcell::Gridcell` at `guess.cpp:2379`). If per-cell RNG call sequence is identical between modes (which it would be if the year_outer code paths preserve the per-cell semantics of getclimate / vegdynam / etc.), then per-cell results should be bit-exact. **§3.4 hypothesis 2 FALSIFIED** as written (no global RNG state to advance differently between modes).

**A.6 — Empirical localizer (much stronger than progressive-NCELLS bisection)**: per-cell drift profile across all 17 B17(b)-affected files:
| File | cell0(-103.75,76.25) | cell1(-95.75,80.25) | cell2(94.25,54.25) | cell3(-57.75,-33.75) |
|---|---|---|---|---|
| `lai.out` | 0 | 8 | 8 | 12 |
| `nflux.out` | 0 | 0 | 6 | 6 |
| `cmass.out` | 0 | 6 | 8 | 8 |
| `aaet.out` | 0 | 8 | 8 | 10 |
| (... 13 more files all show cell0=0; cells 1+ progressively diverge ...) | 0 | varies | varies | varies |
**Cell 0 (the first cell in `data/gridlist/gridlist_test2.txt`) is BIT-EXACT in ALL 17 drift files**. Cells 1, 2, 3 progressively diverge with drift growing approximately monotonically with cell index. This is a **textbook localizer**: the drift is per-cell-iteration-order-dependent and multi-cell-only (not visible in 1cell scenarios per gates 5+6 BIT-EXACT). NCELLS bisection (the original §3.6 plan) is REDUNDANT given this stronger empirical localizer — the existing 4cell data already proves the divergence is per-cell-position-N-dependent (cell N=0 always bit-exact; cells N>=1 progressively diverge).

**A.6 supplementary — drift cumulative-over-time profile (within-cell)**: for each affected cell, drift first appears at a specific year_idx and then propagates cumulatively to subsequent years. Cell 1 first-drift at year 1876 (year_idx 5; the 4th historical year); cell 2 first-drift at year 1876; cell 3 first-drift at year 1873 (the FIRST historical year). Years 1871-1872 (spinup) BIT-EXACT in ALL cells. This is consistent with: identical initial state for every cell (per-cell-isolated seeds = 12345678); identical per-cell setup pipeline (same getgridcell + reset + setup_multipart + climate.initdrivers + landcover_init); divergence accumulates only DURING the year-loop simulation (not during setup); ONE randfrac call slips at some point during simulation, propagating cumulatively through stochastic ecological dynamics (establishment / disturbance / mortality / patch-area-transfer).

**A.7 — Drift-signature inspection** (rules out remaining §3.4 hypotheses + identifies likely culprit class): drift signature is **stochastic-perturbation-like**, NOT FP-roundoff. Affected: per-PFT-total + tot_runoff. Unaffected: per-LC summed (npool_cropland/natural/pasture, anpp_cropland/natural/pasture, cflux_cropland/natural/pasture, nflux_cropland/natural/pasture, cpool_cropland/natural/pasture; 15 files). Affected drifts concentrate in low-biomass marginal-establishment PFTs (TrIBE, TrBR, IBS) where one-or-two-individual differences in stochastic-establishment events produce 17%+ relative drift in per-PFT biomass while cell-total drift stays ≤ 1.4% relative. **Likely culprit class** (NOT specifically identified without seed-tracking instrumentation): year_outer batches all-cell-setup BEFORE main loop; gridcell_outer interleaves per-cell-setup with per-cell-year-loop. Some side-channel state (NOT in: `gridcell.seed`, `stand.seed`, `landcover_init`, `setup_multipart`, `reset`, `preload_all_climate`, `getclimate` vs `getclimate_for_year`, `current_grid_index`, `spinup_year_idx`, `is_first_gridcell` — all checked and shown to be per-cell-isolated-or-equivalent in Phase A.5+) is advancing per-cell in a mode-dependent order. The exact code site requires **seed-tracking dprintf instrumentation** (every `randfrac` consumer dumps `(cell_idx, year, day, callsite, pre_seed, post_seed)` then diff the two modes' traces) — deferred to 17c.0.5 (β option) per scoping decision.

#### 1.3.4 B17(a) sort-then-diff harness fix — implementation

The implementation at `scripts/cross_validate_year_outer.sh::compare_outputs()` between line 266 (end of "RAW BYTE-EQUALITY SUMMARY" block) and line 268 (start of NaN-check block) inserts a SORT-THEN-DIFF NORMALIZATION block with the following structure:

1. **75-LOC documentation comment** explaining: (a) why B17(a) is structural (cell-major vs year-major loop), (b) sort key + invariant, (c) the BIT_EXACT / SORTED_EXACT / SORTED_DIFFER classification, (d) PASS/FAIL semantics (effective-pass = BIT_EXACT + SORTED_EXACT == total), (e) sort-key invariant assumption (Lon, Lat, Year as columns 1, 2, 3 verified empirically across all 37 files), (f) cleanup mechanism (mktemp + trap RETURN), (g) cross-references to §3.3, §3.6 (a1), §1.3, FOLLOWUPS B17 entry, and (h) backport classification (TRUNK-IRRELEVANT, .sh harness only).
2. **Conditional SORT-THEN-DIFF block**: guarded by `if [ "$mismatches" -gt 0 ]; then ... fi`. Skipped entirely when raw cmp -s already passes (per-LC summed files; 1cell scenarios). Inside the block: `mktemp -d -t b17a_sort_XXXXXX` for temp dir; `trap 'rm -rf "$sort_tmp"' RETURN` for auto-cleanup; per-file loop sorts body via `( head -1 "$fa"; tail -n+2 "$fa" | LC_ALL=C sort -k1,1n -k2,2n -k3,3n ) > "$sa"` (preserves header line verbatim); compares sorted versions via `cmp -s`; classifies as SORTED_EXACT (PURE B17(a)) or SORTED_DIFFER (B17(a) + B17(b) drift); accumulates `sorted_exact` + `sorted_differ` counters.
3. **B17(a) NORMALIZATION SUMMARY**: prints BIT_EXACT / SORTED_EXACT / SORTED_DIFFER counts + "Total accounted for" sanity check (always equals $total in correctly-functioning runs).
4. **Effective-pass semantic update** (replaces the 4-line `bit_exact_ok` block at the original line 313-316): new computation `effective_pass=$((matches + sorted_exact))` + `bit_exact_ok=1` iff `effective_pass == total && total > 0`. Includes inline 6-LOC comment explaining the semantic shift from "raw byte-equality" to "byte-equality of CONTENT (raw OR sorted)" per Decision-12 acceptance interpretation.
5. **Refined PASS/FAIL messages**: PASS message at line 432+ now mentions B17(a) sort-normalization explicitly when `sorted_exact > 0`; FAIL message at line 440+ now reports `sorted_differ` (B17(b) drift count) instead of raw `mismatches` and includes empirical-evidence summary (1.4% max cell-total drift; per-cell-isolated stochastic-process divergence; closure plan reference to §3 + 17c.0.5).

The fix preserves ALL existing semantics:
- Exit code 0: PASS substantive + signal-of-life (now requires BIT_EXACT + SORTED_EXACT == total instead of raw mismatches == 0).
- Exit code 2: FAIL byte-equality (now reports `sorted_differ` count for B17(b)).
- Exit code 3: FAIL NaN-presence (unchanged; the NaN check downstream from the SORT block uses `bit_exact_ok` for the message line but the check itself remains independent).
- Exit code 4: FAIL signal-of-life (unchanged; the F4 banner-presence check from 17c.0.1 is preserved exactly).

#### 1.3.5 Verification gates 1-4 — clean rebuilds + unit tests

Gates 1+2 (clean rebuilds) NOT EXECUTED in this sub-phase: no C++ source change → no rebuild needed; binaries from 17c.0.3 (`4d09b62`) at `lpjguess/build/guess` + `lpjguess/build_mpi/guess` are reused as-is. The skip is operationally safe because the 17c.0.4 fix is `.sh`-only.

Gate 3 (serial unit tests): `lpjguess/build/runtests --reporter compact` → **162/162 PASS** (25 test cases / 162 assertions). Confirms no regression from prior commits.
Gate 4 (MPI unit tests): `lpjguess/build_mpi/runtests --reporter compact` → **162/162 PASS** (same envelope). Build-agnostic regression-clean.

#### 1.3.6 Verification gates 5-8 — four-xval re-verification (THE substantive 17c.0.4 evidence)

All 4 xval scenarios re-run with the modified `compare_outputs()`. Results:

| Gate | Scenario | Run A exit | Run B exit | Run A `[year_outer]` | Run B `[year_outer]` | RAW match | Sort-classification | Compare exit | NaN |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 1cell imogen | 0 | 0 | 0 | 5 | 37/37 | (skipped per idempotency) | **0 PASS** | 0/0 |
| 6 | 1cell imogencfx | 0 | 0 | 0 | 5 | 37/37 | (skipped per idempotency) | **0 PASS** | 0/0 |
| 7 | 4cell imogen | 0 | 0 | 0 | 5 | 15/37 | **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER** | 2 (B17(b) drift) | 0/0 |
| 8 | 4cell imogencfx | 0 | 0 | 0 | 5 | 15/37 | **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER** | 2 (B17(b) drift) | 0/0 |

The 5 SORTED_EXACT files in gates 7+8 (PURE B17(a) cases successfully normalized via sort-then-diff): `npool.out`, `mch4.out`, `mch4_diffusion.out`, `mch4_ebullition.out`, `mch4_plant.out`. Identical across both .ins variants (build-agnostic + .ins-agnostic). The 17 SORTED_DIFFER files (B17(a) + B17(b) drift): `aaet.out` (34 lines), `agpp.out` (14), `anpp.out` (24), `cflux.out` (34), `clitter.out` (24), `cmass.out` (30), `cpool.out` (30), `cton_leaf.out` (26), `fpc.out` (30), `lai.out` (36), `nflux.out` (18), `ngases.out` (26), `nlitter.out` (24), `nmass.out` (34), `nsources.out` (28), `nuptake.out` (28), `tot_runoff.out` (22). Drift-line counts identical across both .ins variants (the divergence is in the engine simulation, not the input module).

**Substantive interpretation**: gates 5+6 confirm B17(a) fix preserves 1cell PASS exit 0 (regression-clean + idempotent). Gates 7+8 confirm B17(a) fix successfully normalizes the 5 PURE B17(a) files in 4cell scenarios, advancing the effective-pass count from 15/37 (pre-17c.0.4) to **20/37** (post-17c.0.4) — a 33% improvement on the controlled-fail surface. The remaining 17/37 SORTED_DIFFER files surface B17(b) cleanly with the §1.3.3 + §3.8 reclassified empirical characterization. Decision-12 acceptance criterion 1 (strict byte-equality) remains structurally unachievable for multi-cell year_outer scenarios; acceptance criterion 2 (within explicit tolerance) is the path for 17c.0.5.

#### 1.3.7 Cross-check: F5 banner observability + year_outer banner counts

Identical to 17c.0.3 §1.2.9 envelope: every Run B run.log contains exactly 5 `[year_outer]` banner lines (1 from `[year_outer] starting framework_loop_mode = "year_outer"`, 1 from `[year_outer] preloaded N gridcell(s)`, 2 from `[year_outer] nyear_spinup = N, firsthistyear = ... + total_years = ...`, 1 from `[year_outer] simulation complete: N cell(s) x M year(s)`). Plus the F5 dprintf `[framework] framework_loop_mode = "year_outer" (after .ins parse)` always present in Run B logs (gates 5+6+7+8) and `[framework] framework_loop_mode = "gridcell_outer" (after .ins parse)` always present in Run A logs. F4 + F5 + rule #8 signal-of-life triple-defense remains intact.

#### 1.3.8 Backport classification

**TRUNK-IRRELEVANT (.sh harness only).** `scripts/cross_validate_year_outer.sh` is a per-fork harness that does not exist in `trunk_r13078` (the upstream LPJ-GUESS trunk; the fork point for this repo's coupled-model variant). The B17(a) fix is purely a comparison-harness upgrade with no engine touch; nothing to backport. Recorded in `notes/TRUNK_R13078_BACKPORT_LEDGER.md` as a new step-17c-17c.0.4 row classified `IRRELEVANT-by-novelty` (no analogous file in trunk to receive the backport).

#### 1.3.9 What 17c.0.5 must do next

The remaining 17/37 SORTED_DIFFER files in 4cell scenarios surface B17(b) cleanly. The 17c.0.5 sub-phase (the next sub-phase in the revised PREP plan per §1) decides:

**Option α (tolerance-based comparison upgrade to `compare_outputs()`)** — recommended given Phase A's empirically-clarified picture (1.4% max cell-total drift; per-PFT splits up to ~20% in low-biomass marginal-establishment cases; classic stochastic-process sensitivity signature). Estimated effort ~0.5-1 d. Implementation: extend `compare_outputs()` SORTED_DIFFER classification to compute per-row per-column abs+rel diff; add `--tolerance abs=<eps_a>,rel=<eps_r>` CLI flag (or hard-coded thresholds with `notes/STEP_17b.md` §3a.7 cross-reference); reclassify SORTED_DIFFER → SORTED_WITHIN_TOL (counts toward PASS) or SORTED_EXCEEDS_TOL (counts toward FAIL). Documentation: amend `notes/STEP_17c.md` §3.4 + §3.6 + §3.8 with empirical tolerance derivation (e.g., abs ≤ 1.5e-2 for LAI; rel ≤ 2e-2 for cell totals; rel ≤ 2e-1 for per-PFT splits in low-biomass cases per the per-PFT analysis in §1.3.3). Aligns with Decision-12 acceptance criterion 2 ("PASS substantive within an explicit tolerance specified in `notes/STEP_17b.md` §3a.7"). Backport: TRUNK-IRRELEVANT (.sh-only).

**Option β (seed-tracking dprintf root-cause investigation)** — a focused +1-2 d investigation if (α) is rejected. Implementation: add `dprintf("[seed] cell_idx=%d year=%d day=%d callsite=%s pre=%ld post=%ld\\n", ...)` to every `randfrac` consumer (driver.cpp prdaily/randfrac itself; vegdynam.cpp 1018+1061+1218+1482; spitfire.cpp 1744+2669+2700+2717; blaze.cpp 515+655). Run gates 7+8 in BOTH modes; capture both run.log streams. Diff the two seed-trace logs to identify the FIRST cell (probably cell 1) and FIRST callsite where the seed-state diverges between modes. Author the targeted fix at that specific code site (likely a setup-phase-ordering interaction per §1.3.3 supplementary). Re-run gates 7+8; expect 37/37 BIT_EXACT or SORTED_EXACT. Backport: depends on the fix — likely `lpjguess/framework/framework.cpp` year_outer setup-phase reordering, which would be backport-IRRELEVANT (year_outer code is step-17a novelty; doesn't exist in trunk) but worth verifying per the BACKPORT_LEDGER discipline.

The (α)/(β) decision is the user's call when 17c.0.5 begins. My recommendation (carried forward from 17c.0.4): **(α)** unless there is a strong scientific or contractual reason to want true byte-equality. The drift is consistent with normal stochastic-model behavior; (β)'s +1-2 d engineering cost buys a divergence elimination that is scientifically meaningless (cell totals already agree to within ~1.4%; the per-PFT splits diverge in marginal-establishment cases that are precisely where stochastic models are expected to be sensitive to seed perturbation). But this is a 17c.0.5 decision; 17c.0.4 deliberately preserves both options.

#### 1.3.10 Stash entry retention

`stash@{0}` was dropped at the end of 17c.0.3 (per `4d09b62` Part 5; sha256 `a5d6c5b0bb2d2a4bc55f1a6342f461bce177dd79abde93f55d749c9860b59271` patch backup retained at `_chat_artifacts/B15_B16_WIP_PRE_FORENSIC_2026-05-12.patch`). No stash this sub-phase. The 17c.0.4 fix was authored fresh (no pre-existing WIP) and is small enough (.sh-only; ~100 LOC) that no salvage strategy was needed.

### 1.4 17c.0.4-followup landing record — B17(b) operational acceptance at provisional 2% tolerance + sub-phase renumbering decision deferral (commit `2771939`, 2026-05-13 night)

After 17c.0.4 landed at `027d90d` (3-remote-converged), the user reviewed Phase A's empirically-clarified picture (per §1.3.3 + §3.8.1 through §3.8.4) and directed an operational reframing of the originally-planned 17c.0.5 (α/β decision) sub-phase: **provisionally accept B17(b) drift within a 2% cell-total tolerance envelope WITHOUT writing any new harness code OR engine instrumentation**, deferring the formal Option α (tolerance-based comparison upgrade) AND Option β (seed-tracking dprintf root-cause investigation) to a future sub-phase TBD that reactivates only on a §3.8.5 re-evaluation trigger firing.

This sub-phase is **doc-only** (3 in-tree files: `notes/STEP_17c.md`, `notes/FOLLOWUPS.md`, `scripts/cross_validate_year_outer.sh` — the latter receives only an inline-comment block, ZERO logic change) + 1 sibling-artifact file (`_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 4). The substantive content lives in the new **§3.8.5 sub-section** (the canonical forensic-record entry for the operational-acceptance decision); §1.4 is a thin landing-record pointer to §3.8.5 to preserve the §1.x landing-record cadence.

#### 1.4.1 Strategy recap

Per the user's verbatim directive (2026-05-13 night, session 4):

> "Well I do not think we should implement anything in code for now, just simply documenting in the chat handoff that there is some divergence and we are accepting a 2% tolerance for now, but we may need to re-evaluate later. I suppose you could also include it as comment in the comparison code or something to that effect. It may be that we could come back and look at it and decide to do something about it."

The decision was scoped explicitly as **provisional**: the 2% cell-total tolerance is the operating envelope until ANY of the four §3.8.5 re-evaluation triggers fires, at which point Option α or Option β reactivates as the focused next step. The decision was **landed as a standalone commit** (not rolled into the next work commit) per the user's subsequent directive that the strategic significance warrants its own version-controlled history entry.

#### 1.4.2 Per-file diff stats

| File | LOC | Class | Backport |
|---|---|---|---|
| `notes/STEP_17c.md` | +~140 (new §3.8.5 sub-section: decision narrative + 4 re-evaluation triggers + sub-phase renumbering implication + documentation surface) | DOC | TRUNK-IRRELEVANT (notes/) |
| `notes/FOLLOWUPS.md` | "Last updated" header refresh + B17 row status update from "RECLASSIFIED + decision deferred to 17c.0.5" → "RECLASSIFIED + PROVISIONALLY ACCEPTED at 2% tolerance + (α)/(β) reactivates on re-evaluation trigger" | DOC | TRUNK-IRRELEVANT |
| `scripts/cross_validate_year_outer.sh` | +~30 inline comment block in `compare_outputs()` near the SORTED_DIFFER classification (cross-references to §3.8.5 + chat handoff §4.13); ZERO logic change | DOC (inline comment only) | TRUNK-IRRELEVANT (.sh harness only) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (sibling artifact, outside repo) | new Part 4 §4.13 documenting the operational-acceptance decision narrative | DOC (not in git) | n/a |

Net source-logic change: **ZERO** (no `compare_outputs()` logic change; no exit-code change; no harness behaviour change). Net documentation change: ~170 in-tree LOC + ~250 sibling-artifact LOC.

#### 1.4.3 Verification gates

No re-build needed (zero source change). Unit tests re-run as a sanity check: `lpjguess/build/runtests --reporter compact` → 25/25 / 162/162 PASS; `lpjguess/build_mpi/runtests --reporter compact` → 25/25 / 162/162 PASS. No xval re-verify in this sub-phase (the next sub-phase 17c.0.5 does the canonical 4-xval re-verify per §1.5).

#### 1.4.4 Backport classification

**TRUNK-IRRELEVANT** (doc-only + .sh-comment-only; no analogous file in `trunk_r13078`). Recorded in `notes/TRUNK_R13078_BACKPORT_LEDGER.md` as a new step-17c-17c.0.4-followup row. (Some chat-handoff invocations have referred to this commit as `17c.0.4 FOLLOW-UP` or `17c.0.4-followup`; both refer to commit `2771939`.)

#### 1.4.5 What 17c.0.5 must do next

Per the user-approved collapsed renumbering convention (per §3.8.5 "Sub-phase renumbering implication" sub-section; user-authorised 2026-05-13 night-late session 4), the next active sub-phase is the **full 4-xval re-verify on `2771939` HEAD** (gates 1-8). See §1.5 landing record for the canonical execution trace + regression-clean evidence.

### 1.5 17c.0.5 landing record — full 4-xval re-verify on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD (this commit, 2026-05-13 night-late)

Per the user-approved collapsed renumbering convention (per §3.8.5 "Sub-phase renumbering implication" sub-section), 17c.0.5 = **full 4-xval re-verify on `2771939` HEAD** (gates 1-8) confirming regression-clean status with the §3.8.5 provisional B17(b) acceptance envelope intact. The user-approved scope was **Full** (all 8 gates including clean rebuilds + unit tests + 1cell xval + 4cell xval, NOT abbreviated to gates 5-8 only). The user-approved re-evaluation cadence per §3.8.5.5 was applied to this verification as the **canonical baseline routine xval re-verify** that all future routine xval re-verifies on this branch will be compared against.

The verification effectively re-runs the 17c.0.4 + 17c.0.4-followup landing-evidence gates on the post-followup HEAD `2771939` to (a) confirm the doc-only follow-up did NOT regress any behaviour; (b) establish the canonical 17c.0.5 baseline envelope for the §3.8.5.5 cadence; (c) opportunistically resolve a 4-line stale-reference cleanup in `scripts/cross_validate_year_outer.sh` (lines 306, 429, 484, 630 — see §1.5.7) that the user-approved collapsed renumbering convention rendered factually incorrect.

#### 1.5.1 Strategy recap

- **All 8 gates re-executed** end-to-end (gates 1+2 incremental rebuild → gates 3+4 unit tests → gates 5+6 1cell xval → gates 7+8 4cell xval). Pre/post binary sha256 captured for gates 1+2 to confirm no-op rebuild (no source change since `4d09b62`).
- **Regression check**: per-gate envelope captured + diffed against the 17c.0.4 envelope at `027d90d` (per §1.3.5 + §1.3.6). Expected outcome: byte-identical envelope (no source change since `4d09b62` for the binaries; `027d90d` was .sh-only; `2771939` was doc + .sh-inline-comment-only).
- **Coupling-invariance check**: gate 7 (LOOSE) and gate 8 (TIGHT) SORTED_EXACT + SORTED_DIFFER manifests diffed for byte-identity. Expected outcome: empty diff (B17(b) is engine-side, not input-module-side; per §1.3.6 prediction).
- **Script renumbering cleanup (§1.5.7 below)**: 4-line surgical -1/+1 (mostly net-zero) edit to `scripts/cross_validate_year_outer.sh` to remove the stale "sub-phase 17c.0.5 (decision: tolerance-based comparison vs root-cause fix)" framing introduced in 17c.0.4 (when 17c.0.5 was planned as the α/β decision sub-phase) and replace with the post-acceptance §3.8.5 cross-references. ZERO behaviour change; the smoke-retest confirms gate 7 still controlled-fails at exit 2 with the new doc text appearing in the FAIL message.
- **No stash**: this sub-phase is verification-only (+ a small doc cleanup); no pre-existing WIP starting material; nothing to stash or unstash.

#### 1.5.2 Per-file diff stats

| File | LOC | Class | Backport |
|---|---|---|---|
| `scripts/cross_validate_year_outer.sh` | +10/-5 (4 surgical -1/+1-or-+2 edits at lines 305-306, 429, 484, 630-633; ZERO logic change; pure stale-reference cleanup post-collapsed-renumbering convention adoption) | DOC (in-tree script comment + echoed-text update) | TRUNK-IRRELEVANT (.sh harness only) |
| `notes/STEP_17c.md` | substantive amendment (~+250 LOC: new §1.4 + §1.5 landing records + §1 sub-phase table updates marking 17c.0.4-followup ✅ and 17c.0.5 ✅ + §3.8.5 closing-paragraph supersession + §3.8.5 sub-phase renumbering lock-in + new §3.8.5.5 re-evaluation cadence sub-section + header date refresh + status block update + Index updates for §1.3 + §1.4 + §1.5) | DOC | TRUNK-IRRELEVANT |
| `notes/FOLLOWUPS.md` | "Last updated" header refresh + dashboard line additions for collapsed-renumbering-adopted + re-eval-cadence-locked-in entries | DOC | TRUNK-IRRELEVANT |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | new step-17c-17c.0.5 row classified TRUNK-IRRELEVANT (verification-only + doc-only cleanup) | DOC | TRUNK-IRRELEVANT-by-novelty |
| `EXECUTION_PLAN.md` | row 17c update with 17c.0.5 landing entry above the prior 17c.0.4 entries | DOC | TRUNK-IRRELEVANT |
| `CHANGELOG.md` | new dated entry (2026-05-13 night-late) for 17c.0.5 landing | DOC | TRUNK-IRRELEVANT |

Net source-logic change: **ZERO** (no `compare_outputs()` logic change; no exit-code change; no harness behaviour change; the +10/-5 LOC `.sh` change is pure comment/echoed-text cleanup). Net documentation change: ~270 in-tree LOC + sibling-artifact updates (handoff Part 5).

#### 1.5.3 Verification gates 1+2 — incremental rebuild (NO-OP confirmation)

Both `lpjguess/build/` and `lpjguess/build_mpi/` `cmake --build . --target guess` invocations produced **`[100%] Built target guess` with ZERO recompile activity**. Pre/post binary state byte-identical:

| Build | Binary path | Pre-state sha256 | Post-state sha256 | Bytes | Timestamp |
|---|---|---|---|---|---|
| serial | `lpjguess/build/guess` | `8daa1339f167cff2d76d7fb74a1f66022629e40c756c8384bd9a49d57ef0bb72` | (identical) | 2 974 248 | 2026-05-13 16:43 |
| MPI | `lpjguess/build_mpi/guess` | `dd307488933b3e362659d118de03af76191a3aa0323564eac58446982950e2e3` | (identical) | 2 974 248 | 2026-05-13 16:59 |

Both binaries inherit cleanly from the **17c.0.3 build epoch** (commit `4d09b62`); 17c.0.4 (`027d90d`) was .sh-only and 17c.0.4-followup (`2771939`) was doc + .sh-inline-comment-only, so neither commit triggered any C++ recompile. Confirms the deferred-formal-Option-β path has **not** been silently activated (no C++ source change since `4d09b62`).

#### 1.5.4 Verification gates 3+4 — unit tests (REGRESSION-CLEAN)

| # | Gate | Result | Notes |
|---|---|---|---|
| 3 | `lpjguess/build/runtests --reporter compact` | ✅ **25 cases / 162 assertions PASS** | Identical to 17c.0.4 §1.3.5 + 17c.0.4-followup §1.4.3 (third independent confirmation) |
| 4 | `lpjguess/build_mpi/runtests --reporter compact` | ✅ **25 cases / 162 assertions PASS** | Build-agnostic regression-clean |

#### 1.5.5 Verification gates 5+6 — 1cell xval (CONTROLLED-PASS exit 0; identical to 17c.0.4 envelope)

| # | Gate | harness `rc` | RAW match | Sort-classification | NaN | banner_a (Run A) | banner_b (Run B) | Result |
|---|---|---|---|---|---|---|---|---|
| 5 | `scripts/cross_validate_year_outer.sh 1cell imogen` | **0** | 37/37 | (skipped per idempotency) | 0/0 | 0 | **5** | ✅ **PASS substantive + signal-of-life** |
| 6 | `scripts/cross_validate_year_outer.sh 1cell imogencfx` | **0** | 37/37 | (skipped per idempotency) | 0/0 | 0 | **5** | ✅ **PASS substantive + signal-of-life** |

Real wall-clock timing: ~0.54s per gate (1 cell × 11 calendar years × small PFT cohort runs in well under 1s on the test workstation). Run.log timestamps confirm fresh runs (May 14 00:06 wall-clock, contemporaneous with the gate-execution Part B of this sub-phase). Identical to 17c.0.4 §1.3.6 envelope — regression-clean for the 1cell B17(a) sort-then-diff idempotency.

#### 1.5.6 Verification gates 7+8 — 4cell xval (CONTROLLED-FAIL exit 2; envelope IDENTICAL to 17c.0.4)

| # | Gate | harness `rc` | RAW match | Sort-classification | NaN | banner_a | banner_b | Result |
|---|---|---|---|---|---|---|---|---|
| 7 | `scripts/cross_validate_year_outer.sh 4cell imogen` | **2** (CONTROLLED-FAIL) | 15/37 | **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER** | 0/0 | 0 | **5** | ⚠️ **CONTROLLED-FAIL surfacing B17(b) per §3.8.5 provisional acceptance envelope** |
| 8 | `scripts/cross_validate_year_outer.sh 4cell imogencfx` | **2** (CONTROLLED-FAIL) | 15/37 | **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER** | 0/0 | 0 | **5** | ⚠️ **CONTROLLED-FAIL surfacing B17(b) per §3.8.5 provisional acceptance envelope** |

The 5 SORTED_EXACT files (PURE B17(a); identical to 17c.0.4 §1.3.6 manifest): `mch4.out`, `mch4_diffusion.out`, `mch4_ebullition.out`, `mch4_plant.out`, `npool.out`. The 17 SORTED_DIFFER files (B17(a) + B17(b) drift; identical to 17c.0.4 §1.3.6 manifest): `aaet.out` (34 lines), `agpp.out` (14), `anpp.out` (24), `cflux.out` (34), `clitter.out` (24), `cmass.out` (30), `cpool.out` (30), `cton_leaf.out` (26), `fpc.out` (30), `lai.out` (36), `nflux.out` (18), `ngases.out` (26), `nlitter.out` (24), `nmass.out` (34), `nsources.out` (28), `nuptake.out` (28), `tot_runoff.out` (22). Drift-line counts identical to 17c.0.4 envelope.

**Coupling-invariance cross-check (per §1.3.6 prediction)**: `diff <(gate-7-manifest) <(gate-8-manifest)` returns **EMPTY** (zero output). The SORTED_EXACT + SORTED_DIFFER classification is identical between LOOSE (imogen) and TIGHT (imogencfx) coupling, confirming **B17(b) is coupling-invariant** (engine-side per-cell-iteration-order RNG slip per §3.8.3, NOT input-module-specific). This is a **stronger empirical confirmation** than 17c.0.4 provided, because it now spans two independent verification runs (17c.0.4 Phase C + 17c.0.5 baseline) with byte-identical envelope.

#### 1.5.7 Script renumbering cleanup (4 surgical -1/+1-or-+2 edits to `scripts/cross_validate_year_outer.sh`)

The 17c.0.4 commit (`027d90d`) introduced 4 references to "sub-phase 17c.0.5 (decision: tolerance-based comparison vs root-cause fix)" in the `compare_outputs()` block when 17c.0.5 was planned as the α/β decision sub-phase. Per the user-authorised collapsed renumbering convention (§3.8.5), 17c.0.5 is now the verification sub-phase (this commit), and the deferred formal Option α/β decision now reactivates only on a §3.8.5 re-evaluation trigger as a future sub-phase TBD. The 4 stale references are factually incorrect post-renumbering. The cleanup:

| Line (pre-cleanup) | Old text | New text |
|---|---|---|
| 305-306 (header doc-comment block) | `counted toward FAIL; B17(b) closure deferred to sub-` / `phase 17c.0.5 per notes/STEP_17c.md §3 + §3.6)` | `counted toward controlled-FAIL; B17(b) provisionally` / `accepted at 2% per notes/STEP_17c.md §3.8.5 + §3 + §3.6)` |
| 429 (B17(a) NORMALIZATION SUMMARY classification line) | `B17(a) + B17(b) drift; closure in 17c.0.5)` | `B17(a) + B17(b) drift; B17(b) accepted at 2% per §3.8.5)` |
| 484 (effective-pass block trailing comment) | `+ B17(b) drift) remain FAIL until 17c.0.5 closes B17(b). - DKB 2026-05-13]` | `+ B17(b) drift) remain controlled-FAIL per the B17(b) provisional` / `acceptance at 2% cell-total tolerance (notes/STEP_17c.md §3.8.5);` / `formal Option α/β closure deferred to a future sub-phase TBD that` / `reactivates only on a §3.8.5 re-eval trigger. - DKB 2026-05-13/14]` |
| 630 (FAIL message at SORTED_DIFFER > 0 path) | `+ sub-phase 17c.0.5 (decision: tolerance-based comparison vs root-cause fix).` | `+ §3.8.5 (B17(b) provisionally accepted at 2% per 2026-05-13 user directive;` / `formal Option α tolerance vs Option β root-cause closure deferred to a` / `future sub-phase TBD reactivated only on a §3.8.5 re-eval trigger).` |

Net cleanup diff: **+10/-5 LOC across 4 surgical sites; ZERO behaviour change**. Verified via:
- `bash -n scripts/cross_validate_year_outer.sh` → syntax OK
- `rg 'sub-phase 17c\.0\.5 \(decision'` → no matches (all 4 stale refs gone)
- `rg '§3\.8\.5'` → 4 new sites confirmed at lines 306, 429, 485, 633
- Smoke-retest of gate 7 (4cell imogen) → exit 2 (identical), 15+5+17 envelope (identical), new §3.8.5 message text appears correctly in FAIL output

The cleanup is rolled into the 17c.0.5 commit (rather than as a separate polish follow-up) because (a) it is a direct consequence of the user-approved renumbering convention; (b) it is small (4 surgical edits, +10/-5 LOC); (c) leaving the script self-contradictory between commits (script saying "17c.0.5 = decision" while landing "17c.0.5 = verification") would itself be a doc-staleness defect; (d) bundling preserves "one coherent commit per renumbering convention adoption" per the operational-heuristic rule.

#### 1.5.8 Cross-check: F5 banner observability + year_outer banner counts

Identical to 17c.0.4 §1.3.7 envelope: every Run B run.log contains exactly 5 `[year_outer]` banner lines + the F5 dprintf `[framework] framework_loop_mode = "year_outer" (after .ins parse)`. Run A logs contain `[framework] framework_loop_mode = "gridcell_outer" (after .ins parse)` and zero `[year_outer]` banners. F4 + F5 + rule #8 signal-of-life triple-defense remains intact.

#### 1.5.9 Backport classification

**TRUNK-IRRELEVANT (verification + .sh-comment-only).** No engine source change; `scripts/cross_validate_year_outer.sh` is per-fork harness (no analogous file in `trunk_r13078`). Recorded in `notes/TRUNK_R13078_BACKPORT_LEDGER.md` as a new step-17c-17c.0.5 row classified `IRRELEVANT-by-novelty + verification-only`.

#### 1.5.10 What 17c.0.6 must do next

Per the (now-locked-in) collapsed renumbering convention, 17c.0.6 is the **C2 close-out tag (`v0.17.5-step17b-c2-mpi-sync`) annotation amendment decision** (option a/b/c per §0.11). The 17c.0.5 verification empirically confirms that the underlying year_outer code at `f6c192e` (the C2 close-out tag commit) substantively passes within the §3.8.5 provisional-acceptance envelope when the four-xval is run with the post-B15+B16 fixes, so 17c.0.6 is now ACTIONABLE. Estimated effort: ~0.2 d. Decision option recommendation TBD with user when 17c.0.6 begins.

#### 1.5.11 Stash entry retention

No stash this sub-phase. The 17c.0.5 verification + cleanup was authored fresh (no pre-existing WIP) and is small enough (.sh stale-reference cleanup +10/-5 LOC + doc cascade) that no salvage strategy was needed.

### 1.6 17c.0.7 landing record — workstation `mpirun -np 4` mimic verified + Path α handshake-file write-path defect fix + tiny unit doc-comment clarifications (this commit, 2026-05-15)

The 17c.0.7 sub-phase fulfils the **deferred-from-C2 obligation** of session-2 §17.7: a workstation `mpirun -np 4` mimic verification of the C2-core MPI machinery (`MPI_Barrier` at year boundary + `flush_year_globally_synchronized` with `MPI_Allreduce(MPI_SUM)`). The harness was authored fresh as `scripts/cross_validate_mpi_4rank.sh` (analogous in spirit to the gridcell_outer-vs-year_outer xval harness `scripts/cross_validate_year_outer.sh` but targeting single-process-vs-4-rank under year_outer mode rather than gridcell_outer-vs-year_outer under single-process).

#### 1.6.1 Scope (what 17c.0.7 verifies and what it does NOT verify)

| In scope for 17c.0.7 | Out of scope for 17c.0.7 (scoped as B19; cross-linked to steps 11/13/19) |
|---|---|
| **Stage 1 of 8-stage coupled pipeline**: LPJG year_outer simulation completes end-to-end under `mpirun -np 4` for 3 coupling modes (loose, prescribed, tight) and emits identical aggregated `.out` files vs single-process baseline | Stage 2: intermediary_py anthropogenic computation pipeline (component A 28 .py files) |
| **Stage 8 of 8-stage coupled pipeline** (the lead-rank-only handshake-file write step): LPJG-side natural-emissions handshake files (`imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt`, `imogen_lpjg.txt`, `done`) are BIT_EXACT between single-process and 4-rank runs (for prescribed + tight modes) or correctly ABSENT_BY_DESIGN (for loose mode) | Stage 3: intermediary_py natural-emissions component (component B 5 .py files) |
| **MPI primitives**: `MPI_Barrier(MPI_COMM_WORLD)` at year boundary + `MPI_Allreduce(MPI_SUM)` over per-rank accumulators are exercised end-to-end (not just unit-tested) and produce bit-exact totals for 4 doubles between single-process and 4-rank summation | Stage 4: intermediary_py integration component (component C 9 .py files; the substitution algebra `New_total = RCMIP_total - RCMIP_agri + Our_agri`) |
| **Path α handshake-file write-path defect**: identified during 17c.0.7 harness authoring; root-caused; fixed by harness-layer `DIR_COMMON` injection for non-loose modes; pre-fix behaviour affected ALL prescribed/tight production runs (not just xval) that didn't import a `DIR_COMMON`-setting .ins file — this is a real defect closure, not just an xval-harness convenience | Stage 5: intermediary_py IMOGEN export component (component D 1 .py file) → `imogen_inputs_<SSP>.csv` |
| **Coupling-mode parity**: all 3 coupling modes (loose, prescribed, tight) exercise the new C2-core MPI machinery identically; loose mode is correctly identified as ABSENT_BY_DESIGN for handshake files (loose mode does NOT trigger handshake-file writes because the `imogen_intermediary.ins` consumer-side machinery is not invoked) | Stage 6: step-13 adapter that writes the 4 narrow IMOGEN-readable files (i.e., the bridge between `intermediary_py` outputs and the `FILE_LPJG_FLUX` + `FILE_LPJG_CH4_N2O_FLUX` IMOGEN-engine consumption paths) |
| **Tiny clarifications surfaced through Q&A**: 5 LOC of unit doc-comments at `lpjguess/framework/guess.h:1241-1252` (N2O_FIRE, N2O_SOIL, N2_FIRE, NH3_SOIL, NO_SOIL — clarifying the mass-of-N convention rather than the mass-of-N2O convention) + ~8 LOC of comment cleanup at `lpjguess/modules/imogenoutput.cpp:75-79` (N2O_PER_N constant; clearer wording removing the muddled "28 g/mol N2 basis" phrasing; same numerical conversion) | Stage 7: IMOGEN Fortran engine round-trip (`imogen/code/imogen_lpjg.f` consumes the 4 narrow files + produces `CO2.dat` + climate anomaly fields; for v1.0 the engine outputs CH4 + N2O concentrations as columns within `CO2.dat`, not separate `CH4.dat`/`N2O.dat` files; separate-file generation is a B19 sub-item) |

#### 1.6.2 The new harness: `scripts/cross_validate_mpi_4rank.sh`

NEW harness file added at `scripts/cross_validate_mpi_4rank.sh` (~+700 LOC including the comprehensive doc-block at file head; harness structure mirrors the proven `scripts/cross_validate_year_outer.sh` pattern). Key design points:

| Design choice | Rationale |
|---|---|
| **3 modes × 2 runs per mode = 6 runs per harness invocation** (loose-baseline, loose-mpi, prescribed-baseline, prescribed-mpi, tight-baseline, tight-mpi) | Exercises the full coupling-mode envelope of C2-core under both single-process and `mpirun -np 4` execution paths; comparison is BASELINE-vs-MPI within each mode (not LOOSE-vs-TIGHT across modes — the latter is already covered by `scripts/cross_validate_year_outer.sh` gates 7+8 at 17c.0.6) |
| **4-cell × 11-yr smoke scenario** (same 4 polar/cold cells as cross_validate_year_outer.sh: `(-95.75, 80.25)`, `(33.25, 76.25)`, `(133.75, 54.25)`, `(-57.75, -33.75)`; same `nyear_spinup=2` + `firsthistyear`/`lasthistyear` as the gridcell_outer-vs-year_outer xval) | Cross-comparable with the gridcell_outer-vs-year_outer baseline; small enough to complete in seconds on workstation; large enough to exercise multi-cell MPI work distribution (with `mpirun -np 4` each rank gets 1 cell, exercising the inter-rank `MPI_Allreduce` summation over all 4 contributions per year) |
| **Wrapper-writer pattern** (`write_baseline_wrapper()` + `write_mpi_wrapper()`): each generates a per-mode `.ins` file from the canonical `main_xval_imogencfx.ins` template + overrides for `coupling_mode "<mode>"` + `framework_loop_mode "year_outer"` + per-run `<output-dir>` paths + (NEW Path α) per-mode `DIR_COMMON "<absolute-path>"` for non-loose modes | The wrapper-writer pattern is portable (no `.ins` template-file modifications needed); each xval scenario gets its own isolated output directory; the (NEW Path α) `DIR_COMMON` injection ensures the C++-side `mkdir <DIR_COMMON>/LPJG_main/IMOGEN/` calls in `imogenoutput.cpp:140-142` succeed |
| **Per-mode comparison via `compare_outputs()` + (NEW) `compare_handshake_files()`**: per-cell `.out` files compared as before (BIT_EXACT or SORTED_EXACT via sort-then-diff); the 4 handshake files compared in addition (BIT_EXACT for prescribed/tight; ABSENT_BY_DESIGN for loose); composite exit codes per mode aggregate the per-comparison results | Decouples handshake-file verification from per-cell `.out` verification; ABSENT_BY_DESIGN is a clean classification that distinguishes "loose mode design-correctly emits no handshake files" from "files unexpectedly missing"; the per-mode aggregation preserves the gridcell_outer-vs-year_outer xval harness's exit-code conventions (0=PASS, 2=SORTED_DIFFER-or-handshake-MISSING, 99=run-time-fail) |
| **Per-mode-isolated output directories** (`runs/SSP1-2.6/Common-directory/xval_mpi_4rank_runs/<mode>_{baseline,mpi}/`) | Avoids cross-mode interference; each mode's `<DIR_COMMON>/LPJG_main/IMOGEN/` is per-mode-per-run-isolated |

#### 1.6.3 Path α handshake-file write-path defect — forensic + fix

**Defect**: pre-Path-α, the `lpjguess/modules/imogenoutput.cpp` lead-rank handshake-file writer (the `flush_year` body at lines ~283-365) attempts to write to `<DIR_COMMON>/LPJG_main/IMOGEN/<file>`. The `LPJG_main/` + `LPJG_main/IMOGEN/` subdirectories are auto-created via `mkdir` system calls at `imogenoutput.cpp:140-142` (canonical pattern: create `LPJG_main` first, then `LPJG_main/IMOGEN`). When `DIR_COMMON` is the empty string (its default value when no `.ins` file sets it via `param "DIR_COMMON" (str "<path>")`), the `mkdir` calls attempt to create `/LPJG_main/` (i.e., at filesystem root), which fails permission-check at runtime (the user is not root). The failure is caught and reported as a "WARNING: could not open" line in the run log, but the simulation continues (the handshake files are silently NOT written).

**Surface**: the xval setup at `runs/SSP1-2.6/main_xval_imogencfx.ins` does NOT `import imogen_intermediary.ins` (the canonical .ins file that sets `DIR_COMMON` for production runs). Pre-Path-α, ALL prescribed/tight xval runs silently failed to write handshake files. This was undetected before 17c.0.7 because no prior xval harness compared handshake files (only `.out` files). The 17c.0.7 harness exposed the defect by attempting to compare handshake files between baseline + mpi runs and finding them missing in both.

**Root cause**: `DIR_COMMON` defaults to the empty string when not set in any `.ins` file. The xval setup bypassed the canonical `imogen_intermediary.ins` consumer (which would have set it). The C++ engine layer assumes `DIR_COMMON` is set (no defensive default-to-CWD fallback), which is fine for production runs that always import `imogen_intermediary.ins` but breaks the xval setup.

**Fix (Path α)**: at the xval harness layer, inject `DIR_COMMON "<absolute-path-to-per-mode-output-dir>"` into the wrapper `.ins` files for non-loose modes (loose mode does not need it because it doesn't write handshake files). The fix is in the `write_baseline_wrapper()` + `write_mpi_wrapper()` functions of `scripts/cross_validate_mpi_4rank.sh`. The injection is conditional on `mode != "loose"`. The path is per-mode-per-run-isolated to avoid cross-mode interference.

**Why Path α (harness-layer fix) rather than a C++ engine-layer fix**: a C++ engine-layer fix would either (a) make `DIR_COMMON` mandatory in the engine (which would break legacy A/B run setups that work fine because they always import `imogen_intermediary.ins`), or (b) default `DIR_COMMON` to CWD (which would silently move handshake files from their canonical location, potentially confusing consumers that expect them at `<DIR_COMMON>`). The harness-layer fix is the lowest-risk option: it preserves all existing engine semantics + only adds defensive injection in the per-fork xval setup path that bypasses the canonical .ins import chain. Future work (potentially B19): consider whether the engine should warn-on-empty-DIR_COMMON-when-handshake-writes-are-enabled, as a defensive observability improvement (analogous to F4's signal-of-life banner-presence check at 17c.0.1 per rule #8); this could be authored as a tiny C++ runtime diagnostic similar in spirit to F5.

**Verification of Path α fix**: post-fix run of `scripts/cross_validate_mpi_4rank.sh` shows all 3 modes PASS cleanly. For prescribed + tight modes, the 4 handshake files are BIT_EXACT between baseline + MPI runs; for loose mode, the 4 handshake files are correctly ABSENT_BY_DESIGN. The pre-Path-α "WARNING: could not open" log lines are gone; replaced by clean handshake-write success traces showing the per-mode-isolated `<DIR_COMMON>/LPJG_main/IMOGEN/` paths.

#### 1.6.4 Empirical verification envelope

Per the 8-gate convention (analogous to gridcell_outer-vs-year_outer xval gates 1-8 at 17c.0.5+):

| # | Gate | Result | Notes |
|---|---|---|---|
| 1 | `cd lpjguess/build && cmake --build . --target guess` | ✅ exit 0 | NO-OP (no C++ source change since 17c.0.6 except the 5+8 LOC of doc-comment clarifications at `guess.h` + `imogenoutput.cpp`; both files recompiled; both binaries re-linked; only pre-existing Timer sprintf-overflow warnings) |
| 2 | `cd lpjguess/build_mpi && cmake --build . --target guess` | ✅ exit 0 | Symmetric to gate 1 |
| 3 | `lpjguess/build/runtests --reporter compact` | ✅ 25 cases / 162 assertions PASS | Regression baseline preserved |
| 4 | `lpjguess/build_mpi/runtests --reporter compact` | ✅ 25 cases / 162 assertions PASS | Regression baseline preserved |
| 5 | `scripts/cross_validate_year_outer.sh 1cell imogen` | ✅ exit 0; 37/37 raw BIT_EXACT | Regression-clean (B17(b) MECHANICAL CLOSURE at 17c.0.6 preserved) |
| 6 | `scripts/cross_validate_year_outer.sh 1cell imogencfx` | ✅ exit 0; 37/37 raw BIT_EXACT | Regression-clean |
| 7 | `scripts/cross_validate_year_outer.sh 4cell imogen` | ✅ exit 0; 15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER | Regression-clean (B17(b) MECHANICAL CLOSURE preserved; envelope IDENTICAL to 17c.0.6) |
| 8 | `scripts/cross_validate_year_outer.sh 4cell imogencfx` | ✅ exit 0; 15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER | Regression-clean |
| 9 (NEW) | `scripts/cross_validate_mpi_4rank.sh loose` | ✅ exit 0 (loose mode); per-cell `.out` BIT_EXACT; handshake files ABSENT_BY_DESIGN (correct for loose mode) | NEW gate; validates loose-mode MPI parity |
| 10 (NEW) | `scripts/cross_validate_mpi_4rank.sh prescribed` | ✅ exit 0; per-cell `.out` BIT_EXACT; 4/4 handshake files BIT_EXACT | NEW gate; validates prescribed-mode MPI parity + handshake-file writes |
| 11 (NEW) | `scripts/cross_validate_mpi_4rank.sh tight` | ✅ exit 0; per-cell `.out` BIT_EXACT; 4/4 handshake files BIT_EXACT | NEW gate; validates tight-mode MPI parity + handshake-file writes |

**Interpretation of gates 9-11 (substantive value of 17c.0.7)**: this is the **first empirical confirmation** that the C2-core MPI machinery (`MPI_Barrier(MPI_COMM_WORLD)` at year boundary + `MPI_Allreduce(MPI_SUM)` in `flush_year_globally_synchronized`) produces bit-exact results between single-process and 4-rank execution paths for the workstation MPICH implementation. The unit-test surface (gates 3-4) covers the MPI primitives in isolation but not the end-to-end year_outer execution with rank-distributed cells. The deferred-from-C2 obligation per session-2 §17.7 is now FULFILLED. Confidence in the C2-core machinery is upgraded from "unit-tested + single-process verified" to "unit-tested + single-process verified + workstation 4-rank MPI verified". The cluster-MPI verification (17c.1 → 17c.4) remains pending and will exercise the same machinery at larger rank counts on a different MPI implementation (openmpi on KIT IMK-IFU `owl`); 17c.0.7's success is a strong predictor of cluster-MPI success but not a substitute for it.

#### 1.6.5 Path α: source-data trace + unit accounting for the handshake-file content

Per user Q&A on 2026-05-15 (post-Path-α-success verification), the content of `imogen_lpjg_flux.txt` (annual NEE in PgC/yr) and `imogen_lpjg_ch4_n2o_flux.txt` (annual CH4 in TgCH4/yr + N2O in TgN2O/yr) was traced from canonical sources:

| Variable | Source aggregation in `imogenoutput.cpp::accumulate_year_contribution()` | Unit conversion in `flush_year()` | Final unit in handshake file |
|---|---|---|---|
| NEE | `patch.fluxes.get_annual_flux(Fluxes::NEE) * to_gc_avg * area_m2` summed over all patches/stands/gridcells; accumulator: `accum_NEE_kgC` (kgC/yr per cell, summed globally) | `* 1e-12` (kg → Pg) | PgC/yr |
| CH4 | Monthly `patch.fluxes.get_monthly_flux(Fluxes::CH4C, m)` summed over 12 months × `to_gc_avg` × `area_m2` summed over all patches/stands/gridcells; accumulator: `accum_CH4_gCH4C` (g CH4-C/yr per cell, summed globally) | `* CH4_PER_CH4C * 1e-12` where `CH4_PER_CH4C = 16/12` (molar mass CH4 / molar mass C); converts g CH4-C → g CH4 → Tg CH4 | Tg CH4/yr |
| N2O | Annual `patch.fluxes.get_annual_flux(Fluxes::N2O_FIRE) + Fluxes::N2O_SOIL` × `to_gc_avg` × `area_m2` summed over all patches/stands/gridcells; accumulator: `accum_N2O_kgN` (kg N-in-N2O/yr per cell, summed globally; "kg N-in-N2O" = mass of N atoms inside N2O molecules per the LPJG soil/fire N-cycle pool budget convention at `ntransform.cpp:93` and now explicitly documented at `guess.h:1241/1250` post-this-commit) | `* N2O_PER_N * 1e-9` where `N2O_PER_N = 44/28` (molar mass N2O / mass of 2 N atoms in N2O); converts kg N → kg N2O → Tg N2O | Tg N2O/yr |

**Critical clarification on the CH4 monthly-loop**: the monthly loop `for (m=0..11) get_monthly_flux(CH4C, m) * to_gc_avg` is **functionally equivalent** to `get_annual_flux(CH4C) * to_gc_avg` (per the `get_annual_flux(PerPatchFluxType)` overload at `guess.cpp:230` which returns the sum of `get_monthly_flux` over all months). The monthly loop is a **defensive style choice** mirroring `commonoutput.cpp:1400`'s pattern (which uses the monthly loop because it WANTS the monthly breakdown for `mch4.out`). For `imogenoutput.cpp`, only the annual total is needed; the monthly loop is redundant but produces numerically identical output. A future tiny refactor opportunity (NOT actioned in 17c.0.7): simplify to `get_annual_flux(CH4C) * to_gc_avg`. The annual aggregation itself is necessary (IMOGEN consumes annual CH4 emissions per the `imogen_lpjg_ch4_n2o_flux.txt` schema being annual `<year>\t<CH4>\t<N2O>`).

**Critical clarification on the N2O unit convention**: pre-this-commit, the `guess.h` declarations of `N2O_FIRE` (line 1241) and `N2O_SOIL` (line 1250) had **no unit doc-comments** — the units were inferable only from the sibling N-pool budget check at `ntransform.cpp:93` (which shows `n_budget_check = soil.NH4_mass + soil.NO3_mass + soil.NO2_mass + soil.NO_mass + soil.N2O_mass + soil.N2_mass` — all "kg N in <compound> form per m²" per standard N-cycle modeling convention). The 5-LOC of unit doc-comment clarifications added at `guess.h:1240/1251` (NEW; this commit; doc-comment start lines for the ENUMs at 1243/1256) + the parallel additions at `N2_FIRE`, `NH3_SOIL`, `NO_SOIL` (3 sibling N-cycle flux types; consistency improvement; same convention) lock in this convention so future maintainers don't have to grep through `n_budget_check` to figure out the units. Backport classification: TRUNK-RELEVANT (the units are inherent to the N-cycle pool budget convention; the comment was simply missing; upstream trunk_r13708 could accept this improvement).

**ADDITIONAL bundled clarification edits (NEW 2026-05-15 ~21:00-21:40 UTC+2; user-driven source-code rigorous unit re-verification)**: after the initial Phase 3a unit doc-comment additions to `guess.h` and the imogenoutput.cpp:75-79 N2O_PER_N comment rewording were already landed, the user verbatim challenged the inferred-by-sibling-pool conclusion ("instead of inferring by sibling-pool — which by the way, what do you mean by sibling pool?") and asked for absolute source-code-level certainty whether N2O_FIRE and N2O_SOIL are in `kgN/m²/yr` (mass-of-N basis) vs `kgN2O/m²/yr` (mass-of-N2O-molecule basis) vs `kgN/ha/yr` vs `kgN2O/ha/yr` — citing a half-remembered colleague suggestion that the ngases.out N2O might be in `kgN2O/ha/yr` or `kgN/ha/yr`. A 6-step source-code chain trace was performed with explicit smoking-gun proofs from each step:

1. **`guess.h:3850-3855` — soil pool declaration**: `soil.N2O_mass`/`N2O_mass_w`/`N2O_mass_d` are explicitly declared `(kgN/m2)` (with a typo: the doc-comment said "soil NO mass" not "soil N2O mass" — fixed in this commit per (i) below).
2. **`ntransform.cpp:442-454, 467` — soil-flux derivation**: `n2o_d_flux_inc = (dimensionless ftemp) × (dimensionless 1-min(1,wcont)) × soil.N2O_mass_d [kgN/m²]` = `kgN/m²` (per timestep). `report_flux(N2O_SOIL, n2o_d_flux_inc + n2o_w_flux_inc)` is in `kgN/m²` (per timestep; integrated annually by the report_flux accumulator).
3. **`guess.cpp:1530-1544` + `vegdynam.cpp:1452-1458` — fire-flux derivation**: `nflux_fire = (dimensionless mortality_fire) × (kgN/m² nmass_*)` = `kgN/m²`. Then `Fluxes::N2O_FIRERATIO × nflux_fire = 0.036 × kgN/m² = kgN/m²` passed to `report_flux(N2O_FIRE, ...)`.
4. **`guess.cpp:191-194` — `report_flux` is unit-preserving**: pure accumulation; NO unit conversion. So `monthly_fluxes_patch[N2O_FIRE/SOIL]` retains `kgN/m²` units; `get_annual_flux(N2O_FIRE/SOIL)` returns `kgN/m²/yr`.
5. **`commonoutput.cpp:1759-1767` — `ngases.out` writer applies `M2_PER_HA` conversion**: this is the EXACT code path the user's colleague half-remembered. `* M2_PER_HA` (where `M2_PER_HA = 1E4` per `guessmath.h:34`) converts `kgN/m²/yr → kgN/ha/yr`. So `ngases.out` reports N2O fluxes in `kgN/ha/yr` (mass-of-N basis, per hectare). Critically: the writer does NOT apply the `N2O_PER_N=44/28` mass-of-N→mass-of-N2O conversion — so ngases.out N2O columns are NOT in `kgN2O/ha/yr` (which the colleague's half-recollection conflated).
6. **`imogenoutput.cpp:213-285` — IMOGEN handshake reads RAW accumulator**: bypasses the `* M2_PER_HA` writer-side conversion (reads `get_annual_flux(N2O_FIRE/SOIL)` directly = `kgN/m²/yr`), then applies area in m² (NOT ha), then `N2O_PER_N=44/28` (kg-of-N → kg-of-N2O), then `1e-9` (kg → Tg). Result: `TgN2O/yr` (mass of N2O molecules, in teragrams, per year). **This unit chain is correct + matches legacy A's `imogen_lpjg_ch4_n2o_flux.txt` schema.**

**Verdict**: the user's colleague was HALF-RIGHT — the per-hectare part is correct (M2_PER_HA conversion at the ngases.out writer); the mass-of-N2O-molecule part is wrong (no 44/28 is applied at the ngases.out writer). The IMOGEN handshake (`imogen_lpjg_ch4_n2o_flux.txt`) is independent of `ngases.out` — both read the same underlying `kgN/m²/yr` accumulator but apply different unit conversions at the writer. Two BUNDLED additional clarification edits were landed in this commit to lock in this distinction:

- **(i) `guess.h:3850-3855` — typo fix + multi-line doc-comment expansion** (TRUNK-RELEVANT; +6 LOC / -1 LOC): the pre-existing doc-comment incorrectly said `/// soil NO mass in pool (kgN/m2)` for the variables `N2O_mass`/`N2O_mass_w`/`N2O_mass_d`. Replaced with a multi-line doc-block correctly identifying them as `(kgN/m2; mass-of-N basis -- i.e., kg of the N atoms residing inside N2O molecules, NOT kg of the N2O molecules themselves; multiply by 44/28 to convert to kg-N2O-molecules/m2)` + cross-refs to `Fluxes::N2O_FIRE/N2O_SOIL` doc-comments at `guess.h:1240/1251` and the `ntransform.cpp:93` N-pool conservation budget. Pure correction of a factual error in a doc-comment + lock-in of the convention.
- **(ii) `commonoutput.cpp:1759-1767` — NEW ~13 LOC inline-comment block above the ngases.out writer** (TRUNK-RELEVANT; +13 LOC / 0 LOC): explicitly documents the `* M2_PER_HA` writer-side conversion → output unit `kgN/ha/yr` (NOT `kgN2O/ha/yr`; NO mass-of-N→mass-of-N2O conversion is applied here; that conversion is applied separately at the IMOGEN handshake path via `N2O_PER_N=44/28` per `imogenoutput.cpp:84` to emit global `TgN2O/yr`). Locks in the convention to prevent the EXACT kind of half-remembered confusion the user described.
- **(iii) BONUS cross-ref precision fix at `imogenoutput.cpp:75-83`** (mostly TRUNK-IRRELEVANT-by-novelty; ~+10 LOC / -7 LOC): the doc-comment block previously cross-ref'd `guess.h:1241/1250` (off-by-one: doc-comment start lines are 1240/1251; ENUM declarations are at 1243/1256). Updated to be precise + add cross-ref to `guess.h:3850-3855` (the new soil pool doc-block per (i) above) + add NOTE that ngases.out N2O columns are emitted in kgN/ha/yr (NOT kgN2O/ha/yr) + that applying N2O_PER_N is what distinguishes the IMOGEN handshake's TgN2O/yr from ngases.out's kgN/ha/yr.

These 2 additional edits (+ the 1 bonus cross-ref fix) ARE bundled into the 17c.0.7 commit per user-authorised 2026-05-15 ~21:50 UTC+2 ("Ok go ahead and proceed as recommended"). NEW B20 follow-up captured for the future literature-comparison sanity check (per user verbatim aside about wanting to verify N2O magnitudes against published scholarship once the rebuild has a solid v1.0 — independent of B19's intra-codebase legacy A/B comparison).

#### 1.6.6 Per-file diff stats

| File | LOC | Class | Backport |
|---|---|---|---|
| `scripts/cross_validate_mpi_4rank.sh` (NEW; ~700 LOC including comprehensive doc block) | +700 / 0 | Harness; bash | **IRRELEVANT** (per-fork harness; not in `trunk_r13708`) |
| `.gitignore` (NEW entry for `runs/*/parallel_work_xval_mpi/` test-artifact dir) | +6 / 0 | Build hygiene | **IRRELEVANT** (per-fork test-artifact path) |
| `lpjguess/framework/guess.h` (unit doc-comment clarifications at N2O_FIRE + N2O_SOIL + 3 sibling N-cycle flux types AT lines 1240-1257 + typo fix + multi-line doc-block expansion at soil.N2O_mass declaration AT lines 3850-3855) | +20 / -11 | C++ header; framework | **RELEVANT** (lives in `trunk_r13708` as a near-identical sibling file; the units are inherent + the comment was missing/typo'd) |
| `lpjguess/modules/imogenoutput.cpp` (N2O_PER_N comment cleanup at lines 75-83 + cross-ref precision fix + new NOTE about ngases.out distinction) | +14 / -8 | C++ source; modules | **IRRELEVANT-by-novelty** (imogenoutput.cpp is a step-8 addition; no trunk analog) |
| `lpjguess/modules/commonoutput.cpp` (NEW ~13 LOC inline-comment block above ngases.out writer at lines 1759-1767 documenting the `* M2_PER_HA` writer-side conversion + that NO mass-of-N→mass-of-N2O conversion is applied at this writer; locks in the convention to prevent kgN/ha/yr vs kgN2O/ha/yr confusion) | +13 / 0 | C++ source; modules | **RELEVANT** (lives in `trunk_r13708` as a near-identical sibling file; the conversion is inherent + the comment was missing) |
| `notes/STEP_17c.md` (this section + header date row + §1 sub-phase table row + §3.10 forensic NEW + Index updates + §1.6.5 expansion for the 2 bundled additional clarifications + the 1 bonus cross-ref fix) | +~330 / -~4 | Doc; markdown | **IRRELEVANT** (per-fork notes) |
| `notes/FOLLOWUPS.md` (status dashboard refresh + new B19 follow-up cross-linked to steps 11/13/19 + new B20 follow-up for literature-comparison sanity check) | +~110 / -~5 | Doc; markdown | **IRRELEVANT** (per-fork notes) |
| `CHANGELOG.md` (new 17c.0.7 entry; expanded for 2 bundled additional clarifications + B20 cross-link) | +~80 / 0 | Doc; markdown | **IRRELEVANT** (per-fork notes) |
| `EXECUTION_PLAN.md` (row 17c update marking 17c.0.7 LANDED + 17c.0.8 NEXT + B19 + B20 mentioned) | +~7 / -~5 | Doc; markdown | **IRRELEVANT** (per-fork notes) |
| `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (NEW step-17c-17c.0.7 entry: TRUNK-IRRELEVANT-by-novelty for harness + TRUNK-RELEVANT for guess.h unit comments + TRUNK-RELEVANT for guess.h typo fix + TRUNK-RELEVANT for commonoutput.cpp ngases.out unit comment block) | +~60 / 0 | Doc; markdown | **IRRELEVANT** (per-fork notes) |
| `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (NEW Part 7 with §7.1-§7.11 covering all of this) | +~250 / 0 | Sibling artifact; doc; markdown | **IRRELEVANT** (per-session artifact) |

**Total**: ~1 600 LOC additive across 11 files (6 in-tree + 1 sibling artifact + 4 build-side doc surfaces). Source-side: ~700 LOC harness (NEW) + 20 LOC `guess.h` clarifications + 14 LOC `imogenoutput.cpp` cleanup + 13 LOC `commonoutput.cpp` ngases.out unit comment block = ~747 LOC source-affecting. Documentation cascade: ~840 LOC.

#### 1.6.7 What 17c.0.8 must do next

17c.0.8 is the **PREP phase close-out** sub-phase: a final doc cascade + un-tagged checkpoint commit confirming that the entire 17c.0 PREP phase is feature-complete and the workstation environment is ready for the cluster phases (17c.1 → 17c.4). Per the §0.4 forward-look + §1's plan, 17c.0.8 should:

1. Verify no `notes/STEP_17c.md` § references are dangling (post-17c.0.7's §1.6 + §3.10 additions, the Index needs to mention them).
2. Verify the `lpjguess/build_mpi/` build is reproducibly clean and the `runtests` suite passes on it.
3. Re-run all 3 xval harnesses one final time as a regression check (gridcell_outer-vs-year_outer + MPI-4-rank-mimic loose + prescribed + tight) and confirm all pass.
4. Update the `notes/FOLLOWUPS.md` status dashboard to reflect PREP-phase-complete status.
5. Tag the resulting commit `v0.17.8-step17c-prep-complete` (or similar; per user discretion at 17c.0.8 start).

Estimated effort for 17c.0.8: ~0.2 d (lightweight verification + tag).

After 17c.0.8, the focus shifts to 17c.1 (the actual cluster phase: env_owl.sh refinement against actual `module avail` output on KIT IMK-IFU `owl`). The B19 follow-up (intermediary_py + IMOGEN engine round-trip; cross-linked to steps 11/13/19) is recommended to land **before** 17c.1 begins (so the cluster phase exercises the full closed-loop pipeline, not just the LPJG side); this is the user-authorised default per 2026-05-15 ~19:30 UTC+2 ("hopefully before we get to the cluster work and tests").

#### 1.6.8 Stash entry retention

No stash this sub-phase. The 17c.0.7 harness was authored fresh (no pre-existing WIP). Path α was a same-session investigation + fix; no stash needed.

---

### 1.7 17c.0.8 landing record — PREP phase close-out (this commit, 2026-05-15 night; tagged `v0.17.8-step17c-prep-complete`)

This sub-phase formally closes Step 17c.0 PREP. It is pure book-keeping; ZERO source-code change; doc cascade across 6 in-tree surfaces + 1 sibling-artifact (CHAT_HANDOFF Part 8). The originally-planned 17c.0.8 scope per `notes/STEP_17c.md` §1 (per the post-17c.0.3 PREP table) was **"doc cascade + (un-tagged) checkpoint commit on top of the cascade"** at ~0.2 d. The actual landed scope **revised the un-tagged checkpoint to a tagged checkpoint** (`v0.17.8-step17c-prep-complete`) per user-authorised 2026-05-15 ~22:30 UTC+2 in light of the 11-sub-phase 4-day PREP arc warranting a clean reference point for the "PREP closed; B19/B20 began here" milestone.

#### 1.7.1 Trigger + scope decision narrative

User verbatim trigger (2026-05-15 ~22:30 UTC+2, session 4 continuation):

> _"Looks good?"_ [referring to the successful 17c.0.7 commit + ff-merge + tag + 3-remote push report]

After confirmation that 17c.0.7 had landed cleanly with all 3 remotes converged at SHA `6695ef2` + tag SHA `395199ac`, the user was offered four next-step options (per the agent's question prompt at 2026-05-15 ~22:30 UTC+2):

1. Pause for the night; resume tomorrow with 17c.0.8 PREP close-out.
2. Do 17c.0.8 PREP close-out NOW.
3. Skip 17c.0.8 for now; start sketching the B19 + B20 work-plan tonight.
4. Discuss something else.

User initially selected option 3 ("plan-b19-b20"); upon agent's presentation of the comprehensive B19 + B20 work-plan briefing (revised B19 estimate down from 3-7 d to ~2.5-4 d after 2026-05-15 night code-reality check confirmed steps 10/11/12/13/14 are all already DONE per `EXECUTION_PLAN.md`), the user changed their mind to **option 2 (do 17c.0.8 PREP close-out now)** + deferred the 3 B19 sub-decisions (i-spinup-firstcall ordering, Phase-4 tolerance choice, Phase-1 ↔ 17c.0.8 ordering revisit) to AFTER 17c.0.8 lands ("So we could discuss this after that or I could make a choice on this after that" + "I do not see any reason why we cannot discuss it today as well"). Subsequent option-A confirmations on scope (full 6-surface cascade) + tag (`v0.17.8-step17c-prep-complete`) + B19 discussion timing (after 17c.0.8 lands; tonight is OK) locked in this sub-phase's scope.

This sub-phase's content is therefore: (a) the doc cascade reflecting PREP-phase-complete status across all 6 surfaces; (b) a tagged-checkpoint commit on top of the cascade per the revised tag-it decision; (c) handoff to session-5 / next-task cluster (B19 + B20 + 17c.1+) with the 3 deferred B19 questions documented in CHAT_HANDOFF Part 8 §8.6 as the session-5 opening agenda.

#### 1.7.2 Why this sub-phase is the LAST PREP sub-phase (and not, e.g., bundled with B19-Phase-1)

Per the §1 PREP table footer, **17c.0 PREP is exclusively the pre-cluster preparation work for the LPJG side of the coupled pipeline + the C2-core MPI machinery + all latent defects surfaced during the C2-tagged HEAD audit**. Specifically:

- 17c.0.0-0.6 closed audit items B15 + B16 + B17(a) + B17(b) (all surfaced during the post-C2-close-out audit).
- 17c.0.7 fulfilled the deferred-from-C2 workstation `mpirun -np 4` mimic obligation per session-2 §17.7.
- 17c.0.8 (this commit) closes PREP with a pure-book-keeping cascade.

B19 (intermediary_py + IMOGEN engine round-trip + closed-loop validation) is **logically a B-bundle separate from PREP** because:

1. It exercises stages 2-7 of the 8-stage coupled pipeline (intermediary_py side); 17c.0 PREP exercised stages 1 + 8 (LPJG side). Different functional surface.
2. Its prerequisite steps (10/11/12/13/14 — intermediary_py imported + end-to-end-tested + adapter built + launcher built) are all already DONE per `EXECUTION_PLAN.md` rows; B19 is operational packaging of an existing-but-deferred-as-non-cluster-prerequisite verification, not new development.
3. Its scope spans Python + C++ + Fortran + cross-engine validation (much wider than any 17c.0 PREP sub-phase, which were narrowly-scoped C++/.sh fixes).
4. Its expected duration (~2.5-4 d essential + 1-3 d optional polish) exceeds the entire 17c.0 PREP arc (~4 calendar days for 11 sub-phases including discussion + drafting + verification).

Bundling B19 into a 17c.0.x sub-phase would obscure the PREP-vs-B-bundle distinction that has structured all prior step-17 work. Per the user's preference (2026-05-15 ~19:30 UTC+2: _"hopefully before we get to the cluster work and tests"_), B19 will land BEFORE 17c.1 cluster phases begin, but as its own commit/branch/tag-cycle separate from PREP.

#### 1.7.3 Scope of this commit (per-surface)

| # | Surface | Edits |
|---|---|---|
| 1 | `notes/STEP_17c.md` | (i) Header: NEW date line "Date 17c.0 PREP close-out landed (sub-phase 17c.0.8; FINAL PREP sub-phase): 2026-05-15 night"; (ii) update "Date 17c.1 → 17c.4 cluster phases" to reflect B19/B20-before-cluster preference; (iii) Status block: promote from "🔧 IN PROGRESS" to "✅ 17c.0 PREP COMPLETE / 🔧 cluster phases pending"; append new paragraph documenting the 17c.0.7 + 17c.0.8 landings + PREP-COMPLETE milestone + next-task cluster + 3-deferred-B19-questions handoff; (iv) Index: NEW §1.7 entry; (v) NEW §1.7 landing record (this section; ~150 LOC); (vi) §1 PREP table 17c.0.8 row: ⏳ pending → ✅ DONE with revised scope (tagged not un-tagged); (vii) §1 PREP table footer summary: rewrite to "🎉 PREP phase OFFICIALLY COMPLETE — 11/11 sub-phases done; 0 d remaining in PREP" + handoff to B19 + B20 + 17c.1+ |
| 2 | `notes/FOLLOWUPS.md` | (i) Status dashboard "Last updated:" entry: NEW 17c.0.8 close-out entry (PREP COMPLETE + handoff narrative); previous 17c.0.7 entry promoted to "Prior dashboard entry preserved for context" per the established convention; (ii) F-12 row: append "+17c.0.7 LANDED 2026-05-15 evening; +17c.0.8 LANDED 2026-05-15 night session 4 continuation; PREP COMPLETE; tag `v0.17.8-step17c-prep-complete`"; (iii) B19 row: prepend "**PRIORITY: HIGH (recommended BEFORE 17c.1 cluster phases per user preference 2026-05-15 ~19:30 UTC+2; revised effort estimate down from 3-7 d to ~2.5-4 d after 2026-05-15 night code-reality check)**"; (iv) B20 row: prepend "**PRIORITY: HIGH (recommended AFTER B19 completes; gates on B19 closed-loop pipeline output)**" |
| 3 | `CHANGELOG.md` | NEW dated entry under `## [Unreleased]` for 2026-05-15 night session 4 continuation: "Step 17c (F-12 sub-milestone C3 PREP sub-phase 17c.0.8): PREP phase close-out — 11/11 sub-phases DONE; doc-cascade-only; ZERO source-code change; tagged `v0.17.8-step17c-prep-complete` post-merge"; ~50 LOC entry summarising the 11-sub-phase arc + handoff to B19/B20/17c.1+ |
| 4 | `EXECUTION_PLAN.md` | Row 17c (line ~2021): prepend "17c.0.8 LANDED 2026-05-15 night session 4 continuation (this commit; tagged `v0.17.8-step17c-prep-complete` post-merge; PREP COMPLETE)" to the existing entry; refresh the Phase-7 / cluster work estimates if necessary |
| 5 | `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | NEW step-17c-17c.0.8 entry (above the 17c.0.7 entry per the descending-chronological convention): "TRUNK-IRRELEVANT-by-novelty (pure book-keeping; no source-code change)"; ~15 LOC entry |
| 6 | `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` | NEW Part 8 (after Part 7): "17c.0.8 PREP close-out + handoff to session 5 (B19/B20/17c.1)" — sections: §8.1 (this part exists) + §8.2 (state at session-4-close) + §8.3 (11-sub-phase PREP arc retrospective) + §8.4 (B19 work-plan summary; revised down from 3-7 d to ~2.5-4 d) + §8.5 (B20 work-plan summary) + §8.6 (3 deferred B19 questions for session-5 opening agenda) + §8.7 (operational heuristics retrospective) + §8.8 (recommended session-5 starting commands) |

Net source-logic change: **ZERO**. Net source-comment change: **ZERO**. Net documentation change across 6 in-tree surfaces: **~+450 LOC NEW + ~−15 LOC churn-removed** (NEW §1.7 of this file ~150 LOC; STEP_17c Status-block update ~+30 LOC; STEP_17c §1 PREP table 17c.0.8 row expansion ~+10 LOC; STEP_17c §1 PREP footer rewrite ~+10/-5 LOC; STEP_17c Index entry ~+1 LOC; FOLLOWUPS Status dashboard entry ~+50 LOC + B19/B20 priority annotations ~+15 LOC + F-12 row update ~+5 LOC; CHANGELOG NEW entry ~+50 LOC; EXECUTION_PLAN row 17c update ~+10 LOC; BACKPORT_LEDGER NEW entry ~+15 LOC; CHAT_HANDOFF Part 8 ~+200 LOC sibling). Backport classification: **TRUNK-IRRELEVANT-by-novelty** (pure book-keeping; no source-code change; the entire `notes/` + `CHANGELOG.md` + `EXECUTION_PLAN.md` doc surface doesn't exist in `trunk_r13078`).

#### 1.7.4 Verification

ZERO source-code change → no rebuild + no runtests + no xval needed. The verification surface is purely a **6-surface visual-review checklist + `git diff --stat` review**:

| Gate | Scope | Outcome |
|---|---|---|
| 1 | `git status --short` shows exactly 6 modified in-tree files + 1 sibling-artifact modification | (verified at commit time; see `git diff --stat` in CHAT_HANDOFF Part 8 §8.2 for the canonical record) |
| 2 | `notes/STEP_17c.md`: 5 sub-edits all present + Index entry + §1.7 NEW section; renders cleanly in standard markdown viewer | ✅ verified |
| 3 | `notes/FOLLOWUPS.md`: Status dashboard refresh + B19 + B20 PRIORITY: HIGH annotations + F-12 row update | ✅ verified |
| 4 | `CHANGELOG.md`: NEW dated entry under [Unreleased] follows the established 17c.0.x format + cross-references this §1.7 + the §1 PREP table footer | ✅ verified |
| 5 | `EXECUTION_PLAN.md` row 17c update: prepended 17c.0.8 LANDED status; total estimates refreshed if needed | ✅ verified |
| 6 | `notes/TRUNK_R13078_BACKPORT_LEDGER.md`: NEW step-17c-17c.0.8 entry above the 17c.0.7 entry; classified TRUNK-IRRELEVANT-by-novelty | ✅ verified |
| 7 | `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 8 NEW with 8 sub-sections (§8.1 through §8.8) | ✅ verified |
| 8 | `git log -1 --stat` post-commit shows expected file count + LOC delta (within ±20 LOC of the §1.7.3 estimate) | (verified at commit time; see CHAT_HANDOFF Part 8 §8.2) |

No engine-side or harness-side gates are exercised this sub-phase; the 11-gate envelope established at 17c.0.7 (gates 1+2 builds; gates 3+4 unit tests both builds; gates 5-8 1cell+4cell year_outer xval all 4 scenarios; gates 9-11 mpi-4rank xval all 3 modes) remains the canonical PREP-COMPLETE-state envelope and is implicitly preserved across this commit (no source-code change → byte-identical binaries → byte-identical xval envelopes).

#### 1.7.5 Operational heuristics retrospective (the 11-sub-phase PREP arc)

The 17c.0 PREP arc reinforced 4 operational heuristics from the rebuild's running canon (rules #6-#9 from `notes/FOLLOWUPS.md` "Operational heuristics — lessons learned"):

1. **Rule #6** (asymmetric multi-year writer scaling → check for single OPEN/CLOSE-gating root cause): added at 17b B6 closure (2026-05-11 night); not re-applied during PREP since no new asymmetric-scaling defects surfaced.
2. **Rule #7** (stale forward-reference TODOs are architectural-finding triggers): added at 17b B3 closure (2026-05-12 night); not re-applied during PREP since no stale TODOs were investigated.
3. **Rule #8** (signal-of-life banner-presence assertion for code-path-gated cross-validation): added at 17c.0.0 (2026-05-12); operationally validated at 17c.0.1 (banner-presence assertion in `compare_outputs()` would have surfaced B15 immediately at C1 close-out had it existed then); applied verbatim throughout 17c.0.2/0.3/0.4/0.5/0.6/0.7 verification cadence.
4. **Rule #9 candidate** (when a forensic note contains a derivation that source-side code materially relies on, an audit must re-check the SOURCE CODE against the DERIVATION, not just code against itself; trusted-input audits are independent-input audits): identified at 17c.0.6 §3.8.6.9 (B17(b) mechanical closure forensic — the spurious `cell_idx * nyear_spinup` term in the spinup_year_idx reproduction formula was a derivation-vs-code mismatch undetected for ~5 days because audits checked code against the derivation rather than the converse). **Status at PREP close-out: candidate; promotion to formal rule #9 deferred pending one more recurrence**. Worth flagging that the post-17c.0.7 user-driven N2O unit re-verification challenge (2026-05-15 ~21:00 UTC+2: _"I want you to confirm one last time by thoroughly examining the code (instead of inferring by sibling-pool)"_) is in the same family of intuition (do not trust an inferred-from-related-code conclusion; verify the ACTUAL code path) and produced 3 useful clarifications (the typo fix at `guess.h:3850`, the `commonoutput.cpp` ngases.out unit comment block, the `imogenoutput.cpp` cross-ref precision fix). If a third independent recurrence surfaces in B19 or 17c.1+, formal promotion to rule #9 should be reconsidered.

#### 1.7.6 Forecast-vs-actual retrospective (the 11-sub-phase PREP arc)

The original 17c.0 PREP forecast (per session-3 handoff §0.4 → 5-phase plan item 1) was a **single workstation `mpirun -np 4` mimic verification**, ~0.5-1 d. The actual landed PREP arc is **11 sub-phases over ~4 calendar days** (2026-05-12 morning → 2026-05-15 night). Materially over-budget by ~3-4× both in sub-phase count and in elapsed time, but exclusively because of latent defects surfaced during the post-C2-close-out audit:

| Forecast item | Actual outcome | Variance |
|---|---|---|
| Single mpirun-np4 mimic | 17c.0.7 (landed cleanly per forecast scope; 1 d actual) | 0× variance for the originally-planned scope |
| _(not forecast)_ | B15 + B16 + B17(a) + B17(b) audit items surfaced + 6 sub-phases to close (17c.0.0 through 17c.0.6); +3 calendar days; +6 sub-phases | Pure positive variance — these defects existed pre-audit + would have eventually surfaced in C3 cluster work where debugging cycles are 10-100× more expensive |
| _(not forecast)_ | Path α handshake-file write-path defect surfaced + fixed during 17c.0.7 | Pure positive variance — same logic |
| _(not forecast)_ | 5+13 LOC of TRUNK-RELEVANT N-cycle unit doc-comment clarifications surfaced via user Q&A on unit verification post-Path-α-handshake-file-content-inspection | Pure positive variance — addresses the user's colleague's half-remembered confusion ("kg N2O/HA/yr or kg N2O-N/HA/yr") + locks in the canonical convention to prevent future ambiguity |
| _(not forecast)_ | 17c.0.8 PREP close-out (this commit; ~0.2 d) | Originally planned; just renumbered through the PREP plan revisions |

**Net assessment**: the +3-4× PREP over-budget is fully justified by the latent-defect closures (4 audit items + Path α + N2O unit clarifications) that would otherwise have surfaced at much higher debugging cost in C3 cluster work or worse, in B19 closed-loop validation where a single hidden defect could masquerade as either an intermediary_py bug, a step-13 adapter bug, an IMOGEN engine bug, or an LPJG year_outer bug. This recurrence-pattern with rule #9 candidate (forensic-vs-code mismatch) reinforces that **harness-authoring + targeted verification routinely surface latent defects in the system under test** (B15 surfaced because we extended the harness to assert the year_outer code path actually executed; B16 surfaced because B15 fix unmasked the eager cache-fullness check; B17(b) surfaced because B16 fix unmasked the 4cell-multi-cell drift; Path α surfaced because the new MPI harness was the first to compare handshake files). The forecasting-refinement candidate for rule #9 (per `notes/STEP_17c.md` §3.7) is reinforced.

#### 1.7.7 Stash entry retention

No stash this sub-phase. 17c.0.8 is pure book-keeping; no pre-existing WIP exists.

#### 1.7.8 What's next (POST-B40 status update at 2026-05-19 evening session 7 continuation — LOCAL V1 VERIFICATION WINDOW IS NOW ✅ FULLY COMPLETE)

Per the user-authorised next-task cluster (originally locked-in 2026-05-15 night at 17c.0.8 PREP close-out; updated at B19 close 2026-05-18 evening; updated at B37 + B36 + B39 close-outs in session 7; **further updated at B40 close 2026-05-19 evening session 7 continuation to reflect the COMPLETION of the local v1 verification window**):

**LOCAL V1 VERIFICATION WINDOW SUMMARY (B37 + B36 + B39 + B40; all 4 items closed in session 7)**:

| Item | Commit | Effort estimate | Actual | One-line verdict |
|---|---|---|---|---|
| B37 Productive-year-ceiling explanatory study | `75811c0` | ~1-3 h | ~2 h | Root cause identified; path (iv) sidecar empirically confirmed; v1.0 paper-publication production-IMOGEN runs FEASIBLE without F-12 |
| B36 Fortran IMOGEN background-emission audit | `a77ea8f` | ~2-4 h | ~30 min | NO DOUBLE-COUNTING DEFECTS FOUND; all 4 sub-item criteria PASS |
| B39 CO2_INIT_PPMV per-YEAR1 configurability fix | `8026740` | ~1-2 h | ~45 min | STRICT_PASS empirically confirmed; CO2 drift -3.5 to -4.2% → -0.09 to -0.80%; CH4 also improved |
| B40 Modern-decade N2O hump explanatory study | **THIS commit** | ~2-4 h | ~30 min | Methodological characteristic NOT defect; Saikawa-aligned channel scope; paper §2.4.4 paragraph drafted |
| **TOTAL** | — | **6-13 h estimate** | **~4 h actual** | Significantly faster than estimate; all 4 items decisive at first-or-second reconnaissance |

**NEW post-v1.0 audit items filed across the window**: B44 (productise path-iv sidecar; MEDIUM; TRUNK-IRRELEVANT) + B45 (parametrise 3 hardcoded year sentinels in updateImogenControlData; LOW; TRUNK-RELEVANT) + B46 (split N2O_SOIL into separately-attributed channels; LOW; TRUNK-RELEVANT if option α). All POST-V1.0 enhancements; NONE v1.0-blocking.

**Cumulative backport-debt UNCHANGED at +145 LOC throughout the entire window** (none of the 4 window items touched canonical engine source).

**Rule #9 + Rule #10 datapoints**: clean operation across all 4 window items; ≥11 consecutive datapoints each since promotion at B19 Phase 5 close-out.

**What's next (post-window)**:

| Order | Item | Effort estimate | Priority |
|---|---|---|---|
| (optional) -3. | Local v1 verification window CLOSE-OUT tag candidate (e.g., `v0.21.0-local-v1-verification-window-complete`) + dedicated close-out doc cascade | ~30-60 min | OPTIONAL per the prompt's §"Suggested first action sequence" item 8 |
| (optional) -3b. | **B44** Productise path-iv sidecar in `scripts/run_coupled.sh` as new `--engine-only-mode` flag | ~20-30 min | MEDIUM (operational convenience for 17c.1+ cluster-orchestration sbatch) |
| 1. | **17c.1+ cluster phases** on KIT IMK-IFU `owl` (production-scale runs + paper-stage data generation per `notes/STEP_17c.md` §1.7.8) | ~1-2 weeks SSH-iterative | HIGH (paper-publication critical-path) |
| 2. | **Track 2 production runs** (5 SSP-RCPs; 1900-2100; 62538-cell gridlist; `-input imogencfx`; using B37 path-iv sidecar OR cluster-side workflow) | ~1-2 weeks compute + iteration | HIGH |
| 3. | **Validation triad execution + paper figures** (anthropogenic emissions plots + IMOGEN concentrations vs Law Dome / IPCC AR6 / Saunois / Tian + ISIMIP3b climate vs IMOGEN-emulator difference maps + Track 1 vs Track 2 LPJG ecosystem comparison) | ~1 week | HIGH |
| 4. | **Paper amendments + writing** (intro + methods + results + discussion + conclusion + §2.4.4 sector-ownership rule paragraph per B40 §4) | ongoing in parallel | HIGH |
| 5. | **v1.0 paper submission** to GMD or similar venue | target | TERMINAL |

Per `notes/PRODUCTION_RUN_CONFIG.md` §6.2 effort estimate: total estimated calendar time from this commit to v1.0 paper submission is **~6-10 weeks**.

---

**Per-item detailed close-out narratives** (chronological, most recent first):

-3. **B40 ✅ FULLY CLOSED 2026-05-19 evening session 7 continuation** (canonical landing record at `notes/B40.md`; no tag — investigation-only milestone). Actual elapsed time ~30 min (vs ~2-4 h estimate; faster because source-level smoking-gun decisively confirmed FOLLOWUPS hypothesis without empirical run). Verdict: **METHODOLOGICAL CHARACTERISTIC NOT DEFECT**. Source-level smoking gun at `lpjguess/modules/somdynam.cpp:1689-1691`: monthly N-input to soil mineral N pool SUMS atmospheric NHx + NOy deposition + biological N-fixation WITHOUT source-discrimination; `lpjguess/modules/ntransform.cpp:179-467` runs Xu-Ri 2008 + Ma 2022 JAMES nitrification + denitrification kinetics on combined pool producing aggregated `Fluxes::N2O_SOIL`; `lpjguess/modules/imogenoutput.cpp:221-223` propagates single channel to IMOGEN handshake. LPJG's N2O channel scope is Saikawa-2014-aligned (~14-24 TgN2O/yr modern decade; includes N-deposition-influenced natural pathway) rather than Tian-2020-narrow (~9-12 TgN2O/yr "purely natural" only). Full 1900-2100 time-mean (11.18 TgN2O/yr) WITHIN Tian envelope [8.3-11.5]. NEW B46 filed (optional v1.5+ source-edit; LOW priority). Paper §2.4.4 sector-ownership rule paragraph drafted (per `notes/B40.md` §4). NO new defect-class audit items filed. Classification: TRUNK-IRRELEVANT-by-finding. Rule #9 + Rule #10 at 11th consecutive datapoint each.

-2. **B39 ✅ FULLY CLOSED 2026-05-19 evening session 7 continuation** (canonical landing record at `notes/B39.md`; no tag — small functional-improvement milestone; cumulative backport-debt UNCHANGED at +145 LOC). Actual elapsed time ~45 min (vs ~1-2 h estimate per FOLLOWUPS B39 row; faster because the parameter was already configurable; only .ins values + cross-reference table + acceptance-test re-run needed). Verdict: **CO2_INIT_PPMV per-YEAR1 configurability fix (option α) APPLIED + EMPIRICALLY CONFIRMED STRICT_PASS**. Pre-fix CO2 drift -3.5 to -4.2% pre-fix → -0.09 to -0.80% post-fix across all 4 smoke-window years (1900-1903); ~5× tightening; STRICT_PASS achieved. User-authorized at session 7 q_b39_ch4_scope option A bundled CH4_INIT_PPBV 865.0 → 875.6 fix as B39 (α)' minor extension (also improved to STRICT_PASS +0.07 to +0.39%; sign-flipped + magnitude reduced). N2O_INIT_PPBV unchanged at 277.4 per user preference (already within 0.07% of Law Dome 1900 277.2; -0.18 to -1.37% drift unchanged from pre-fix). Per-cell breakdown: 8 of 12 STRICT_PASS pre-fix → **11 of 12 STRICT_PASS post-fix** (only 1903 N2O remains BALLPARK at -1.37%). 1 git-committed .ins file touched (main `runs/SSP1-2.6/imogen_intermediary.ins`) + 1 Python script POST-B39-NOTE prepend (Rule-#10 self-correction: 3 xval parallel `.ins` files are git-IGNORED + auto-inherit post-B39 main .ins via setup_run.sh copy mechanism at next xval re-activation; no separate xval source-edit needed); NEW `docs/scientific_framework.md` §6.1 cross-reference table (1850/1900/2005 Law Dome / Meinshausen 2017 / Mauna Loa baselines) + NEW row in `notes/PRODUCTION_RUN_CONFIG.md` §2.1 cross-referencing the §6.1 table. ZERO source-code change to `lpjguess/` or `imogen/` engine trees (per option α prescription). Classification: TRUNK-IRRELEVANT-by-novelty. NO new audit items filed. Rule #9 + Rule #10 at 10th consecutive datapoint each. Audit-item state at B39 close: B39 ✅ DONE; all other items unchanged from B36 close at `a77ea8f`.

-1. **B36 ✅ FULLY CLOSED 2026-05-19 evening session 7 continuation** (canonical landing record at `notes/B36.md`; no tag — audit-only milestone; cumulative backport-debt UNCHANGED at +145 LOC). Actual elapsed time ~30 min (vs ~2-4 h estimate; decisive at first reconnaissance because of engine's clean architecture). Verdict: **NO DOUBLE-COUNTING DEFECTS in `imogen/code/imogen_lpjg.f`**. All 4 sub-item criteria PASS: (a) zero hardcoded emission-rate DATA statements (only RF-level `Q_NON_CO2` fallback at line 3980, overridden when `FILE_NON_CO2=.TRUE.` which v1.0 sets; the other DATA statements are calendar metadata + ocean physical constants + humidity lookup + B33(c) SAVE guards); (b) zero default-filename fallback strings (`SUBROUTINE SETTIN` lines 1699-1707 init all FILE_* + DIR_* string vars to `' '`); (c) zero `BLOCK DATA` subroutines anywhere across 4700 LOC; (d) empirical cross-reference confirms intermediary_py Component A + B outputs feed the 4 active FILE_* channels via Option B per B31 launcher auto-rewrite (DR1 launcher banner + .ins active-line scan + 4-file inventory + magnitude plausibility all consistent). Two engine-source-level PRINT warnings at `imogen_lpjg.f:655` + `:742` document the user-data design invariants. NO new audit items filed. Classification: TRUNK-IRRELEVANT-by-finding. Rule #9 + Rule #10 at 9th consecutive datapoint each. Rule-#10 self-correction during writeup phase: initial draft proposed a `docs/scientific_framework.md` §5.3 IS92A→CMIP6 doc-drift fix, retracted via grep verification confirming the IS92A reference is in FOLLOWUPS B36 row pre-audit framing not in scientific_framework.md. Audit-item state at B36 close: B36 ✅ DONE; all other items unchanged from B37 close at `75811c0`.

0. **B37 ✅ FULLY CLOSED 2026-05-19 evening session 7** (canonical landing record at `notes/B37.md`; no tag at this commit per per-item-not-release-worthy convention). Actual elapsed time ~2 h (vs ~1-3 h estimate per FOLLOWUPS B37 row). Root cause IDENTIFIED: deterministic closed-form function of YEAR1 governed by 3 hardcoded year sentinels (`1901`, `2100`, `1871`) at `lpjguess/modules/climatemodel.cpp::updateImogenControlData()` lines 1185-1197. Formula `K_flip = ⌈(1900 - YEAR1 + 1) / 2⌉; productive_years = 2 × (K_flip + 1)` matches Run B (1871-start → 32 years) + Run C + DR2 (1900-start → 4 years) exactly. NEW path (iv) launcher-side `done`-marker sidecar (outside original 3-candidate scope) empirically confirmed in DR1: produced 202 year-dirs (1900-2101) in 12 min 48 sec wall on smoke 4-cell config; all 201 paper-publication-target years 1900-2100 have valid CO2.dat with physically-sensible SSP1-2.6 trajectory (1900: 285.8 → 2050 peak: 462.8 → 2100: 417.5 ppm); +1 over-shoot empty 2101 placeholder (cosmetic; benign). **v1.0 paper-publication production-IMOGEN-engine runs (full 1900-2100 × 5 SSP-RCP scenarios) ✅ FEASIBLE WITHOUT F-12 architectural fix**. F-12 + Track-2 cluster-MPI tight-coupling remain v1.1+ work per B43 (unchanged). Wall timing: ~3.78 sec/year on workstation; 5-SSP-RCP scaling ~63 min total local — operationally viable per Decision (c). B44 NEW filed (productise path-iv sidecar in `scripts/run_coupled.sh`; ~20-30 LOC bash; MEDIUM priority; TRUNK-IRRELEVANT-by-novelty); B45 NEW filed (parametrise 3 hardcoded year sentinels at `climatemodel.cpp:1185-1197`; ~5-15 LOC source-edit; LOW priority; TRUNK-RELEVANT). Cumulative B19+B20+B41+B42+B43+B37 backport-debt UNCHANGED at +145 LOC eligible-for-backport. Rule #9 + Rule #10 operating at 8th consecutive datapoint each. v1.0 % done estimate UNCHANGED at ~95-97% (investigation-only commit). Audit-item state at B37 close: B37 ✅ DONE; B44 ⏳ NEW filed; B45 ⏳ NEW filed; all other items unchanged from B41+B42+B43 close at `268837f`.

Per the user-authorised next-task cluster (further updated at B37 close to reflect verification window progress + remaining work):

1. **B19** ✅ **FULLY CLOSED 2026-05-18 evening** (tag `v0.19.0-b19-literature-validated` annotated + 3-remote-pushed at the B19 Phase 5 close-out commit). Actual elapsed time ~2.5-3 d across session 5 (2026-05-16 morning → 2026-05-18 evening; including the post-B34 hygiene + Phase 4 reframing detours). All 5 phases (0+1+2+3+3-ADDENDUM+4+5) ✅ DONE. Phase 4 plan PIVOTED from "compare against legacy A/B references" to "compare against Law Dome ice-core literature" (Option B; user-authorized 2026-05-18 evening) after Stage 4-pre confirmed legacy_A reference outputs are physically implausible for the early 20th century. Result: ✅ BALLPARK_PASS — v1.0 GHG concentrations within ≤5% (CO2) / ≤1% (CH4) / ≤1.5% (N2O) of authoritative published 1900-1903 SSP1-2.6 historical values per MacFarling Meure 2006 (canonical CMIP6 / IPCC AR6 historical concentration source). CO2 negative bias (~3.5-4.2%) fully attributable to CO2_INIT_PPMV=286.085 being a 1850s seed used for 1900-start sim — not engine bug; B39 NEW filed at Phase 5 to track per-YEAR1 configurability fix (~1-2 h; LOW-MEDIUM priority; deferred to local v1 verification window). Cumulative B19 backport-debt = +145 LOC eligible-for-backport (entirely from Phase 2 Commit 3 `6862d03`'s `imogen/code/imogen_lpjg.f::WARN_POSIX_CONCAT_COLLAPSE`). Audit-item state at B19 close: **CLOSED** — A3 + B28 + B31 + B32 + B33(a)+(b)+(c) + B34 + B35; **Deferred to local v1 verification window** — B36 + B37 + B39; **Deferred to future intermediary_py revision cycle** — B29 + B30. Rule promotions at B19 close: **Rule #9** (harness-authoring + targeted verification routinely surface latent defects; 5+ recurrences) ✅ PROMOTED to standing rule + **Rule #10** (verification-integrity discipline; 6 consecutive clean datapoints) ✅ PROMOTED to standing rule (both at `notes/FOLLOWUPS.md` Operational Heuristics §). v1.0 % done estimate revised UP to ~92-94%. Full B19 close-out narrative at `notes/B19.md` §7.4.1.

2. **B20** ✅ **DONE 2026-05-18 late evening at B20 close-out commit** (tag `v0.20.0-b20-literature-sanity-checked` annotated + 3-remote-pushed). Verdict `WITHIN_ENVELOPE_MEAN_WITH_TIME_VARIATION`. Actual elapsed time ~3 h (vs ~1-2 d original estimate; revised down at Phase 0 investigation when discovered that existing `runs/SSP1-2.6/inputs_baseline_may7/imogen_lpjg_ch4_n2o_flux.txt` from intermediary_py + step-13 adapter pipeline was already global-aggregated annual time series; NO new production-scale LPJG run needed). Sub-items (a)+(b)+(c)+(d) all ✅ DONE; sub-item (e) per-cell observational comparison NOT pursued per user-authorized scope. Result: full 1900-2100 time-mean of LPJG-natural CH4 (179.87 TgCH4/yr) + N2O (11.18 TgN2O/yr) BOTH WITHIN published Saunois 2020 ESSD + Tian 2020 Nature envelopes; modern-decade N2O hump (2000-2017 above envelope; declines back into envelope by 2050) classified per FOLLOWUPS B20 (c)(iii) original spec "systematic over time = climate-feedback realism issue, outside scope of unit verification but worth flagging" → filed as NEW **B40** for paper-stage explanatory follow-up. Combined with B19 Phase 4 BALLPARK_PASS (atm concentrations vs Law Dome ice core), v1.0 now has TWO independent literature validation lines. Cumulative B19+B20 backport-debt UNCHANGED at +145 LOC eligible-for-backport. Rule-#10 verification-integrity discipline operating cleanly at 7 consecutive datapoints. v1.0 % done estimate revised UP to ~95-97%. Full B20 close-out narrative at `CHANGELOG.md` + `notes/FOLLOWUPS.md` B20 row + `_chat_artifacts/CHAT_HANDOFF_2026-05-18_session5_post_b19.md` Part 1.

3. **Local v1 verification window** (between B19 close and 17c.1 start; ~4-9 h cumulative; can be done in any order, in parallel with B20 or before/after): **B36** (Fortran IMOGEN background-emission audit; ~2-4 h Fortran source-reading) + **B37** (productive-year-ceiling explanatory study; ~1-3 h C++ source-reading + 1-2 cross-config diagnostic runs) + **B39** (CO2_INIT_PPMV per-YEAR1 configurability; ~1-2 h fix; recommended option α = declare per-YEAR1 configurable parameter).

4. **17c.1 → 17c.4 cluster phases** on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative). Begins after B20 + (optionally) the local v1 verification window items. Production-scale runs + paper-stage data generation.

The three deferred B19 questions from session-5 opening agenda (Q1/Q2/Q3) are all ✅ RESOLVED at B19 close — see `notes/B19.md` §8 + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Parts 9-11 for the resolution narrative.

Three deferred B19 questions for session-5 opening agenda (deferred from this commit per user preference 2026-05-15 ~22:30 UTC+2 + user willingness to discuss tonight after 17c.0.8 lands):

| Q | Question |
|---|---|
| Q1 | B19 sub-item (i) `imogen_lpjg.txt` SPINUP/FIRSTCALL hardcoding investigation — should it be done BEFORE B19-Phase 4 closed-loop validation (to pre-empt a possible confounder) or AFTER (fail-fast-then-investigate)? |
| Q2 | B19-Phase 4 closed-loop validation tolerance vs legacy A — 1% relative per column? 0.5%? Mixed (BIT_EXACT for natural CO2/CH4/N2O + 1% for anthro CH4/N2O)? Defer-to-Phase-4-empirics? |
| Q3 | B19-Phase 1 ordering revisit — Phase 1 first then Phase 2-5, or any other re-sequencing surfaced by tonight's B19/B20 discussion? |

Full discussion narrative + decisions captured in `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 8 §8.6 (which will be appended-to during the post-17c.0.8-landing tonight discussion).

---

## 2. B16 forensic + fix — audit item B16 (this commit)

### 2.1 Why this section exists (post-17c.0.2 surface)

The 17c.0.0 forensic record (commit `2beff31`) established B16 as a **predicted** latent defect (per §0.9 acknowledgement). The 17c.0.1 + 17c.0.2 commit (commit `019c9dd`) fixed B15 and re-ran the four xval scenarios, surfacing B16 **empirically and textbook-exactly** (per §1.1.7's gates 7+8 evidence: `(IMOGENCFX|Imogen)Input::preload_all_climate: stored_years cache already full (last_store_index=9 >= nyears=9) when preloading cell (-95.75,80.25)` — fires at `cell_idx=1`, in BOTH input modules, in identical form). This section formalises B16 from prediction to landed fix, providing the same depth of forensic that §0 provided for B15 (analogous structure: anchors, smoking gun, source-level walkthrough, root cause, fix design, downstream surface acknowledgement).

### 2.2 Anchors at the start of the B16 sub-investigation

| Anchor | Value | Source |
|---|---|---|
| HEAD at start of 17c.0.3 sub-investigation | `019c9dd` | post-17c.0.1+17c.0.2 commit |
| B15 status | CLOSED (per `notes/FOLLOWUPS.md` status dashboard at `019c9dd`) | 17c.0.1 + 17c.0.2 verification |
| B16 status | PREDICTED + EMPIRICALLY-SURFACED (per §0.9 + §1.1.7); fix not yet landed | 17c.0.0 forensic + 17c.0.2 verification |
| 1cell xval scenarios at `019c9dd` | PASS substantive + signal-of-life clean | §1.1.7 gates 5+6 |
| 4cell xval scenarios at `019c9dd` | FAIL exit 99 in Run B at `preload_all_climate` (B16 surface; banner_b=3) | §1.1.7 gates 7+8 |
| Stash at `019c9dd` | `stash@{0}` preserved with B16 C++ hunks for `imogen_input.cpp` (+35/-9) and `imogencfx.cpp` (+29/-11) | §1.1.11 stash retention |
| Working tree at start | Clean | `git status --short` returns empty |

### 2.3 The smoking gun — empirical reproduction at `019c9dd` 4cell year_outer Run B

At `019c9dd`, `scripts/cross_validate_year_outer.sh 4cell imogen` Run B (year_outer override) produces (per §1.1.7 gate 7 evidence):

| Anchor | Value | Notes |
|---|---|---|
| Harness exit code | `99` (Run B aborted with `fail()` from `preload_all_climate`) | Run A baseline (gridcell_outer) completes cleanly with 37 .out files; Run B aborts at `preload_all_climate` with `cell_idx=1` |
| Run B `[year_outer]` banner count | 3 | year_outer code path entered + first cell setup completed + first cell preload entered, then `fail()` fires |
| Run B fail message (verbatim) | `ImogenInput::preload_all_climate: stored_years cache already full (last_store_index=9 >= nyears=9) when preloading cell (-95.75,80.25). Check init() nyears computation.` | Fault site: `imogen_input.cpp:1111-1118` (the eager check at the start of `preload_all_climate`); fault parameters: `cell_idx=1`, `last_store_index=9`, `nyears=9`, `(lon,lat)=(-95.75,80.25)` |
| Run B `[year_outer]` banner count for `imogencfx` variant | 3 | identical fault semantics; symmetric site at `imogencfx.cpp:1366-1376` |
| Run A `.out` file count | 37 | gridcell_outer code path is unaffected; runs through `preload_all_climate` correctly because (per §2.4) gridcell_outer doesn't call `preload_all_climate` (it uses the per-cell streaming path that doesn't engage the cumulative cache) |
| Run B `.out` file count | 0 | Run B aborted at `preload_all_climate` before any output flush |

Fault parameters numerically match §0.9's prediction precisely: `4 cells × 9 distinct imogen_years span = 9 cumulative slots; cell 0 fills all 9; cell 1 enters with last_store_index >= nyears true → eager check fires`. Both modules (`Imogen` + `IMOGENCFX`) reproduce identically. The 1cell scenarios (gates 5+6 at `019c9dd`) do NOT trigger B16 because there is no `cell_idx >= 1` cell — exactly per §0.9's prediction "B16 doesn't fire on 1-cell runs because `last_store_index >= nyears` only triggers on `cell_idx >= 1`".

### 2.4 Cumulative-across-cells cache design intent (source-level walkthrough)

The `stored_years` cache in `(Imogen|IMOGENCFX)Input::preload_all_climate` was designed at C1.3 sub-step 7.3.2 (commit `d7f6c74`, 2026-05-10) with **cumulative-across-cells** semantics. Source evidence:

**(a) Cache is a `std::map<int,YearClimate>` — implementation detail at `imogen_input.h` (analogous in `imogencfx.h`).** The cache is keyed by `imogen_year` (the year-index in the IMOGEN climate forcing dataset, NOT by `cell_idx`). Multiple cells that need the same `imogen_year` share the cached climate data; only the first cell to need a given `imogen_year` pays the load cost.

**(b) The inner cache-miss-branch comment says "Cache miss: load year-imogen_year climate for ALL cells".** The implementation at `imogen_input.cpp` (post-G1; the inner cache-miss branch is preserved) reads:

```cpp
// Cache miss: load year-imogen_year climate for ALL cells
// (the cache is cumulative across cells; this load benefits every
//  subsequent cell that needs imogen_year).
```

This comment was present at `019c9dd` (pre-G1+G2) and remains present post-G1+G2. It is the **canonical source-level statement of the cumulative-cache contract**.

**(c) The `last_store_index` variable advances on cache-miss-only.** When a cell finds an `imogen_year` already in the cache, no new slot is allocated; `last_store_index` does not advance. When a cell misses, the cache loads the climate for that `imogen_year` for ALL cells, advances `last_store_index` by 1, and proceeds. So `last_store_index` is the **count of distinct imogen_years loaded so far across ALL cells** — a cumulative quantity that monotonically increases as new (unique) imogen_years are encountered.

**(d) `nyears` is the **maximum** distinct imogen_years that any single run will need.** Specifically, `nyears = (lasthistyear - FIRST_SPINUP_YEAR) + 1` per the inner-fail message text. For a 4-cell × 9-year run, all 4 cells use the same imogen_year span (1871-1879), so `nyears=9` is correctly sized for the cumulative cache: cell 0 fills slots 0-8 (one per year 1871-1879); cells 1, 2, 3 each produce 100% cache hits (every imogen_year they need is already loaded).

**(e) Per-cell mapping is updated on entry but does NOT affect cache slot allocation.** The `update_per_cell_imogen_year_mapping(...)` call at the top of `preload_all_climate` updates the cell-local mapping `(year, imogen_year)` so the cell knows which cached slots correspond to its years. It does NOT read from or write to `last_store_index`; it does NOT add new slots. So this is a per-cell function executed once per cell, but the cache slot allocation is purely cumulative across cells.

The design intent is therefore clear: the cache is cumulative across cells; cell N>0 enters `preload_all_climate` with a non-empty cache (the union of all imogen_years loaded by cells 0 through N-1) and adds zero or more new slots only on genuine cache miss; `last_store_index >= nyears` at function entry is the **expected state for cell N>0** when the imogen_year span is fully covered by prior cells, NOT an error condition.

### 2.5 Why the eager check mis-models the cache (root cause)

The eager check at `imogen_input.cpp:1111-1118` (and symmetric at `imogencfx.cpp:1366-1376`) reads:

```cpp
if (last_store_index >= nyears) {
    fail("...: stored_years cache already full ...");
}
```

This check **assumes the cache is per-cell**: that on entry to `preload_all_climate` for any cell, the cache should have at least one free slot (`last_store_index < nyears`). This assumption was likely a copy-paste-and-think-too-fast error: a per-cell sanity check would naturally read this way; but the cache is cumulative (per §2.4), so cell N>0 will routinely enter with a full cache (`last_store_index == nyears`) representing **legitimate prior-cell loads**, not an error condition.

The check fires textbook-exactly on the 4-cell × 9-year run: cell 0 fills slots 0-8 (9 loads; `last_store_index = 9`); cell 1 enters with `last_store_index == 9 == nyears`; eager check evaluates true; `fail()` fires; run aborts with the misleading "cache already full" message. **The actual situation is the opposite of "error": the cache IS full because cell 0 did its job correctly; cell 1 will correctly produce 100% cache hits.**

The defect was undetected from C1.3 sub-step 7.3.2 (`d7f6c74` 2026-05-10) through 17c.0.0 forensic landing (`2beff31` 2026-05-12) because:
1. **C1 close-out (`v0.17.0` 2026-05-10)** validation only ran 1cell scenarios + the 4cell scenarios silently degenerated to gridcell_outer per B15 — `preload_all_climate` was never called in any 4cell xval Run B.
2. **C2 close-out (`v0.17.5` 2026-05-11)** validation reproduced the same B15 degeneracy — same outcome.
3. **17c.0.0 forensic (`2beff31` 2026-05-12)** acknowledged B16 as predicted (per §0.9) but did not exercise it: doc-only commit; ZERO source change.
4. **17c.0.1 + 17c.0.2 (`019c9dd` 2026-05-13)** fixed B15 → 4cell Run B finally entered year_outer mode → reached `preload_all_climate` for `cell_idx=1` → eager check fired → empirical surface of B16 textbook-exactly.

### 2.6 Recommended B16 fix design — G1-G4

The fix has four parts (G1-G4); G1+G2 are the substantive fix; G3+G4 are the correctness-and-clarity hardening.

**(G1) Remove eager check at `imogen_input.cpp:1111-1118`.** The 8-line eager-check block is deleted and replaced with a ~38-LOC doc block explaining (a) the cumulative-across-cells cache design intent (per §2.4); (b) why the eager check was wrong (mis-models cache as per-cell; per §2.5); (c) the inner-fail still provides correct fail-fast semantics for genuine cache exhaustion (cache cannot grow past `nyears` slots without a real misconfiguration); (d) cross-references to §0.9 + §2.4 + §2.5 of this file. The doc block is anchored at `[Step 17c (F-12 sub-milestone C3 PREP sub-phase 17c.0.3) — G1: ...]` for grep-discovery.

**(G2) Symmetric removal at `imogencfx.cpp:1366-1376`.** The 11-line eager check is deleted and replaced with a ~20-LOC doc block (shorter than G1 because it cross-references G1's full forensic in `imogen_input.cpp`). Anchor at `[Step 17c (F-12 sub-milestone C3 PREP sub-phase 17c.0.3) — G2: ...]`.

**(G3) Augment `InputModule::preload_all_climate` base-class doc block at `inputmodule.h:84-102`.** Add ~20 LOC of "IMPLEMENTATION GUIDANCE FOR SUBCLASSES" formalising the cumulative-cache contract: subclasses MUST treat any per-cell cache as cumulative-across-cells; subclasses MUST NOT add eager early-exit checks at function entry that assume per-cell cache state. This is the **base-class-level contract documentation** that would have prevented B16 from being introduced in the first place; it is also the canonical doc to cite when auditing future subclass implementations of `preload_all_climate`.

**(G4) Tighten inner per-miss `fail()` diagnostics in both modules.** The inner per-miss check at `imogen_input.cpp:1158-1164` (and symmetric at `imogencfx.cpp:1421-1427`) already provides correct fail-fast semantics with `(lon, lat)` + `imogen_year` + `nyears` + `last_store_index` context. G4 adds `cell_idx` to both `fail()` messages: this is the most diagnostically valuable single piece of context for distinguishing "cell 0 ran out of slots due to genuine cache-size misconfiguration" (extremely rare) from "cell N>0 ran out of slots due to an upstream bug shifting the imogen_year sequence" (extremely informative).

**Verification gates for the B16 fix commit (this commit; landed per §1.2.7-1.2.8):**
1. Clean rebuild of `lpjguess/build/` and `lpjguess/build_mpi/` with zero new warnings (G1-G4 are doc-block-heavy + small `fail()`-message strings; should not trigger any compile warnings).
2. 162/162 unit tests pass on both builds.
3. **All four xval scenarios re-run** — for the first time actually completing in 4cell year_outer mode. Pass conditions:
   - 1cell scenarios: regression-clean (identical envelope to 17c.0.2 gates 5+6).
   - 4cell scenarios: complete to **5 banners** in Run B (year_outer ran end-to-end; the 3→5 banner-count delta vs 17c.0.2 is the unambiguous mechanical evidence that B16 is fixed).
4. **Note on possible new failures.** If 4cell year_outer outputs differ structurally from 4cell gridcell_outer outputs, that is **B17** (a new audit item; see §3 below). Specifically expected:
   - 4cell scenarios may surface row-emission-order divergence (year_outer emits year-major; gridcell_outer emits cell-major) — making Decision-12 byte-equality structurally unachievable. This is **B17(a)**; documented in §3.3.
   - 4cell scenarios may surface small ~1 ULP numerical drift in per-PFT-total / `tot_runoff` files. This is **B17(b)**; documented in §3.4.
   - These were anticipated by §0.8(4)'s "Note on possible new failures" clause: "If 4cell year_outer outputs differ structurally from 4cell gridcell_outer outputs even after B15+B16 are both fixed, that is a real C1+C2 substantive-validation failure that was masked pre-B15."

### 2.7 B17 acknowledgement (forensic surface in §3; fix deferred to 17c.0.4)

While verifying the proposed B16 fix end-to-end on the 4cell scenarios (per §1.2.8 gates 7+8), a downstream-of-B16 substantive-correctness gap surfaced: 22/37 .out files differ byte-wise between Run A (gridcell_outer) and Run B (year_outer) in both 4cell scenarios. The differences split into two distinct sub-defects:
- **B17(a)**: row-emission-order divergence (gridcell_outer emits cell-major; year_outer emits year-major). 5/22 differing files are pure ordering (sort-then-diff returns 0). All 22 are affected by ordering.
- **B17(b)**: small ~1 ULP numerical drift in 17/22 differing files (per-PFT-total + `tot_runoff`; per-LC summed files unaffected). Most prominently in southern-hemisphere cell `(-57.75, -33.75)`.

**The full B17 forensic surface lives in §3 below.** The B17 fix is deferred to the next sub-phase (17c.0.4) per the same staged-discovery pattern that 17c.0.0 used for B16: this commit (17c.0.3) lands the B16 fix + the B17 forensic surface; the 17c.0.4 commit will land the B17 fix + the four-xval re-verification on B15+B16+B17-fixed HEAD. Conservative ordering rationale (analogous to §0.9's B16-deferral rationale):
1. B16 is the higher-level defect (without B16 fix, year_outer multi-cell never completes; B17 cannot be observed). Fixing it is a prerequisite for ANY substantive 4cell year_outer validation.
2. B17 surfaces only when B16 is fixed AND a multi-cell year_outer run completes. The B16-fixed harness running on 1cell scenarios passes cleanly without ever triggering B17, providing a clean baseline.
3. B17's fix is mechanically more involved than B16's (requires either harness sort-then-diff upgrade OR engine row-buffering for B17(a); requires deeper code-correctness investigation for B17(b)).
4. Bundling B16 + B17 into a single commit would conflate two distinct defects with different surface (cache-management vs output-ordering+numerical-correctness) and different audit lineages.

The B17 sub-section in this file (§3) below documents the full surface. The recommended-fix subsection (§3.6) is a skeleton that will be elaborated in the dedicated 17c.0.4 commit.

---

## 3. B17 forensic surface — audit item B17 (this commit; fix in 17c.0.4)

### 3.1 Why this section exists (post-17c.0.3 surface)

The 17c.0.3 four-xval re-verification (per §1.2.8 gates 7+8) ran the 4cell scenarios for the **first time end-to-end with year_outer fully exercised** (i.e., post-B15 fix → year_outer code path actually entered in Run B; post-B16 fix → year_outer multi-cell `preload_all_climate` completes for `cell_idx >= 1` and the run proceeds to full output emission). The result: gates 7+8 controlled-fail with 22/37 .out files differing byte-wise between Run A (gridcell_outer) and Run B (year_outer), even though both runs complete cleanly with 0 NaN and matching banner counts. **This is B17 — a brand-new audit item with two distinct sub-defects (B17(a) row-emission-order divergence + B17(b) small ~1 ULP numerical drift in per-PFT-total / `tot_runoff` files).** This section formalises the B17 surface analogous to §0 (B15 forensic) and §2 (B16 forensic) but with the recommended-fix subsection (§3.6) marked as "to be elaborated in 17c.0.4 commit" because the deep-dive investigation has not yet been completed.

### 3.2 Anchors at the start of the B17 sub-investigation

| Anchor | Value | Source |
|---|---|---|
| HEAD at start of B17 surface | post-G1+G2+G3+G4 (17c.0.3 work tree) | this commit |
| B15 status | CLOSED | `notes/FOLLOWUPS.md` status dashboard at `019c9dd` |
| B16 status | CLOSED (this commit) | §1.2 + §2.6 |
| B17 status | EMPIRICALLY-SURFACED; fix deferred to 17c.0.4 | this section |
| 1cell xval scenarios at 17c.0.3 | PASS substantive + signal-of-life clean (regression: identical envelope to 17c.0.2 gates 5+6) | §1.2.8 gates 5+6 |
| 4cell xval scenarios at 17c.0.3 | CONTROLLED-FAIL exit 2 with 22/37 differ + 0 NaN + banner_a=0 banner_b=5 | §1.2.8 gates 7+8 |
| Working tree at start | Modified (G1-G4 changes) | `git status --short` shows imogen_input.cpp, imogencfx.cpp, inputmodule.h modified |
| Build configuration | `lpjguess/build/` (serial, system g++) AND `lpjguess/build_mpi/` (MPICH_CXX=g++ recovery; per §1.2.10) | both produce 162/162 PASS at 17c.0.3 |

### 3.3 B17(a) — row-emission-order divergence (cell-major vs year-major) — CLOSED 2026-05-13 (this commit, 17c.0.4) via §3.6 option (a1)

**Status (updated this commit, 17c.0.4):** ✅ **CLOSED 2026-05-13 evening (this commit).** §3.6 option (a1) implemented as ~100-LOC SORT-THEN-DIFF NORMALIZATION block in `scripts/cross_validate_year_outer.sh::compare_outputs()` per §1.3.4. Verification gates 7+8 confirm the 5 PURE B17(a) files (`npool.out`, `mch4.out`, `mch4_diffusion.out`, `mch4_ebullition.out`, `mch4_plant.out`) successfully normalize via sort-then-diff to byte-identical content (per §1.3.6). Effective-pass count for 4cell scenarios advanced from 15/37 → 20/37 (33% improvement on the controlled-fail surface). The 1cell scenarios (gates 5+6) preserve PASS exit 0 idempotently (raw BIT_EXACT; sort block skipped per the `if mismatches > 0` guard). The remaining 17/37 SORTED_DIFFER files surface B17(b) cleanly (per §3.4 + §3.8 + §1.3.6).

**Symptom (original; preserved for archaeological context).** All 22 .out files that differ between Run A and Run B in the 4cell scenarios show different row sequences. Specifically:
- Run A (`gridcell_outer`): rows are emitted in **cell-major** order (cell 0 all 9 years, then cell 1 all 9 years, then cell 2 all 9 years, then cell 3 all 9 years).
- Run B (`year_outer`): rows are emitted in **year-major** order (all 4 cells for year 1871, then all 4 cells for year 1872, …, then all 4 cells for year 1879).

The data content is the same — same 4 cells × 9 years = 36 data rows + 1 header = 37 lines per file in both runs. Only the row sequence differs.

**Empirical confirmation by sort-then-diff.** For 5 of the 22 differing files (`npool.out`, `mch4.out`, `mch4_diffusion.out`, `mch4_ebullition.out`, `mch4_plant.out`), sorting both files by `(lon, lat, year)` then `diff`-ing returns **zero diff lines** — i.e., the data is identical, only the row order differs. These 5 files are the **pure-B17(a)** cases. The other 17 differing files have non-zero post-sort diff (per §3.4 below: B17(a) PLUS B17(b)).

**Mechanical cause.** The .out writer in LPJ-GUESS emits per-row as the simulation produces row-eligible state (typically annual flush per cell-year completion). gridcell_outer's loop is `for cell in cells: for year in years:`, so rows emit in cell-major order. year_outer's loop is `for year in years: for cell in cells:`, so rows emit in year-major order. The writer has no buffering layer that would re-emit in cell-major order regardless of loop structure.

**Why this is a Decision-12 contract issue.** Decision-12 (per session-1 §"Decision-12: byte-equality between gridcell_outer baseline and year_outer migration") specified that the year_outer migration must NOT change observable output. By the strict literal interpretation (byte-equality between the .out files), this contract is **structurally unachievable** for any multi-cell run as long as the writer is per-row-flush + the loop structure differs — because the loop structure is the very thing year_outer changes. The semantic interpretation (data equality, not literal byte equality) IS achievable: the data IS identical (per the sort-then-diff test for the 5 pure-B17(a) cases) — only the row sequence differs.

**Resolution options (to be elaborated in 17c.0.4 §3.6).** Two architectural paths:
- **(a) Harness upgrade**: modify `compare_outputs()` in `scripts/cross_validate_year_outer.sh` to sort both files by `(lon, lat, year)` before diff-ing. Lower-cost; preserves the engine's current per-row writer behaviour; aligns Decision-12 with semantic-equality interpretation. Requires explicit doc note in the engine that "year_outer emits in year-major order, year_outer-loop-aware downstream tooling must sort or otherwise normalize row order".
- **(b) Engine row-buffering**: add a buffer layer in year_outer mode that accumulates per-cell rows in memory and flushes in cell-major order at the end of the run (or at the end of each output-period). Higher-cost (memory + complexity); preserves Decision-12 byte-equality strictly. Required if any downstream tooling depends on cell-major row order without sorting.

### 3.4 B17(b) — small ~1 ULP numerical drift in per-PFT-total / `tot_runoff` files — RECLASSIFIED 2026-05-13 (this commit, 17c.0.4) per Phase A forensic in §1.3.3 + new §3.8

**Status (updated this commit, 17c.0.4):** ⚠️ **RECLASSIFIED + DECISION DEFERRED to 17c.0.5.** Phase A forensic deep-dive (per §1.3.3 above and full forensic in new §3.8 below) materially revised the §3.4 hypothesis space:
- **§3.4 hypothesis 1 (FP-summation roundoff): FALSIFIED.** Drift magnitudes are 0.67-17.7% relative (e.g., `lai.out` cell `(-57.75, -33.75)` yr 1876 TrIBE: 0.0192 vs 0.0158 = 17.7% relative). ~1 ULP at value-magnitude 0.02 would be ~10⁻¹⁸; observed drift is 10⁻³ — **six orders of magnitude too large** for FP-summation roundoff. Pattern fits stochastic-perturbation signature (large relative drift in low-biomass marginal-establishment PFTs; small relative drift in established dominants).
- **§3.4 hypothesis 2 (global RNG state): FALSIFIED.** `randfrac(long& seed)` at `lpjguess/modules/driver.cpp:42` is a pure functional Park-Miller LCG; ALL randomness uses per-cell-isolated `gridcell.seed` or per-stand `stand.seed` (both initialize to 12345678 in their ctors). NO global RNG state to advance differently between modes.
- **§3.4 hypothesis 3 (per-cell intermediate state init order): NOT YET CONFIRMED — most likely surviving candidate.** Empirical localizer "cell 0 BIT-EXACT in ALL 17 drift files; cells 1, 2, 3 progressively diverge" (per §1.3.3 A.6) plus drift-cumulative-over-time profile (cell 1+ first-drift at year 1873-1876; spinup years 1871-1872 BIT-EXACT in ALL cells; per §1.3.3 A.6 supplementary) is consistent with: identical initial state for every cell; identical per-cell setup pipeline; ONE randfrac call slips out-of-sequence at some point during the year-loop simulation (NOT during setup), propagating cumulatively through stochastic ecological dynamics. **Likely culprit class** = setup-phase-ordering interaction (year_outer batches all-cell-setup before main loop; gridcell_outer interleaves per-cell-setup with per-cell-year-loop). Specific code site requires seed-tracking dprintf instrumentation (deferred to 17c.0.5 (β) option).

The full reclassified B17(b) characterization lives in new **§3.8** below. The §3.4 archaeological symptom characterization is preserved verbatim below for reference; the table line counts (e.g., `lai.out` 36 lines) match the post-sort diff line counts produced by the implemented sort-then-diff harness in 17c.0.4.

**Symptom (original; preserved for archaeological context).** 17 of the 22 differing .out files show small numerical drift between Run A and Run B even after sorting by `(lon, lat, year)` (i.e., on top of the B17(a) row-ordering difference, there is a real numerical difference in some rows). Affected files (post-sort diff line count in parentheses):

| File | Post-sort diff lines | Class |
|---|---|---|
| `lai.out` | 36 | per-PFT total |
| `nmass.out` | 34 | per-PFT total |
| `cflux.out` | 34 | per-PFT total |
| `aaet.out` | 34 | per-PFT total |
| `fpc.out` | 30 | per-PFT total |
| `cpool.out` | 30 | per-PFT total |
| `cmass.out` | 30 | per-PFT total |
| `nuptake.out` | 28 | per-PFT total |
| `nsources.out` | 28 | per-PFT total |
| `ngases.out` | 26 | per-PFT total |
| `cton_leaf.out` | 26 | per-PFT total |
| `nlitter.out` | 24 | per-PFT total |
| `clitter.out` | 24 | per-PFT total |
| `anpp.out` | 24 | per-PFT total |
| `tot_runoff.out` | 22 | per-cell aggregate |
| `nflux.out` | 18 | per-PFT total |
| `agpp.out` | 14 | per-PFT total |

**Empirical example.** For cell `(-57.75, -33.75)` year 1877 in `nflux.out`:
- Run A (`gridcell_outer`): `... fix= -14.80 ... NEE= -14.93`
- Run B (`year_outer`):    `... fix= -14.85 ... NEE= -14.98`
Drift magnitude: 0.05 in 2-decimal-place printed output, which corresponds to ~5e-2 in single-precision-printed-but-double-precision-internal floating-point — i.e., approximately 1 ULP at the double-precision representation level after the formatted printf rounding chain.

**Cells most affected.** The drift is most prominent in southern-hemisphere cell `(-57.75, -33.75)` and the high-northern cells `(-103.75, 76.25)` and `(-95.75, 80.25)`. The mid-latitude cell `(94.25, 54.25)` is less affected. This pattern suggests the drift is not random floating-point noise but is correlated with cell properties (likely PFT mix, climate forcing magnitude, or accumulator depth).

**Files NOT affected (per-LC summed files: `npool_cropland`, `npool_natural`, `npool_pasture`, `nflux_cropland`, `nflux_natural`, `nflux_pasture`, `cflux_cropland`, `cflux_natural`, `cflux_pasture`, `cpool_cropland`, `cpool_natural`, `cpool_pasture`, `anpp_cropland`, `anpp_natural`, `anpp_pasture`).** All 15 files in this class are bit-exact (raw diff = 0). This is structurally informative: per-LC files aggregate per-LC quantities at the cell level (no cross-cell summation involved); per-PFT-total files aggregate per-PFT quantities possibly with cross-cell intermediate state. **The drift is in the per-PFT-total accumulation pathway.**

**Hypotheses for B17(b) root cause (to be investigated in 17c.0.4).**
1. **Floating-point summation order**. If a per-PFT-total quantity is computed by summing over cells in a per-PFT-total accumulator (rather than computed per-cell and summed at output time), then cell-major iteration vs year-major iteration produces different summation sequences, which produce different roundoff errors at the ~1 ULP level. This is the most likely hypothesis given the affected-file pattern (per-PFT totals + `tot_runoff` which is also a per-cell aggregate possibly going through a cross-cell accumulator).
2. **Global random-number-generator state advancement**. If `interp_climate(...)` or any other code path uses a global (non-per-cell) RNG state, then the order in which cells call into it determines the RNG sequence each cell sees. Cell-major and year-major iteration would produce different RNG sequences, leading to different stochastic disturbance / mortality / etc. outcomes that propagate into per-PFT-total numerics. Less likely than hypothesis 1 (the affected-cell pattern would be more uniform across cells under this hypothesis), but worth checking.
3. **Per-cell intermediate state ordering**. If a per-cell intermediate state (e.g., `Gridcell::seed`) is initialized based on cell-iteration order rather than cell identity, then cell-major and year-major iteration would produce different per-cell initial states. This should not happen for `Gridcell::seed` (which is set per-cell at gridcell construction), but worth verifying for any other per-cell stateful objects in the year_outer code path.

**Why drift IS observable now (post-B16 fix) but was NOT observable before.** Pre-B16 fix, the year_outer 4cell run aborted at `preload_all_climate` for `cell_idx=1` after 3 banners — the simulation never produced any .out emissions in Run B. Post-B16 fix, the year_outer 4cell run completes all 4 cells × 9 years, producing the full 37 .out files. So B17(b) is **brand-new surface**: it cannot have been observed at any previous commit (`v0.17.0`, `v0.17.5`, `2beff31`, `019c9dd`) because the run never reached the .out-emission stage.

### 3.5 Build-agnostic confirmation (serial + single-process MPI both reproduce)

To rule out the possibility that B17(b) is a build-config artefact (e.g., a side-effect of the `MPICH_CXX=g++` recovery; per §1.2.10), gates 7+8 were re-run with `GUESS_BIN=lpjguess/build_mpi/guess` (instead of the script's default `lpjguess/build/guess`). Result:

| Run | Binary | Harness exit | Files differ | banner_a | banner_b |
|---|---|---|---|---|---|
| `4cell imogen` | `build/guess` (serial; system g++) | 2 | 22/37 | 0 | 5 |
| `4cell imogen` | `build_mpi/guess` (MPI single-process; MPICH_CXX=g++ → system g++ via mpicxx) | 2 | 22/37 | 0 | 5 |

The two binaries differ at byte 913+ (cmp output: `lpjguess/build/guess lpjguess/build_mpi/guess differ: byte 913, line 1`) — confirming they are distinct compilations (likely the MPI build links additional MPI runtime symbols even though MPI calls are unused in single-process mode). Same fail pattern across both builds → **B17 is build-agnostic**, i.e., a real engine-level defect, not an artefact of the MPI build's compiler/linker configuration.

### 3.6 Recommended B17 fix design — option (a1) IMPLEMENTED in 17c.0.4 (this commit); option (β) for B17(b) deferred to 17c.0.5

**Status (updated this commit, 17c.0.4):** Option (a1) for B17(a) IMPLEMENTED + verified per §1.3.4 + §1.3.6. Option (a2) for B17(a) NOT TAKEN (higher engineering cost; not needed given (a1) achieves Decision-12 acceptance criterion via semantic-byte-equality interpretation). For B17(b), the recommended-fix sub-section was materially restructured by Phase A (per §1.3.3 + §3.4 status update + new §3.8): hypothesis 1 + 2 FALSIFIED; hypothesis 3 surviving but not specifically root-caused; **B17(b) DECISION (α tolerance-based comparison vs β seed-tracking root-cause investigation) DEFERRED to 17c.0.5**. The original sub-section text below is preserved verbatim for archaeological context, with specific updates inline marking hypothesis-falsification status.

**B17(a) — row-emission-order divergence.** Two architectural options (per §3.3 above):
- **(a1) Harness upgrade (recommended)** [✅ **IMPLEMENTED 17c.0.4 this commit per §1.3.4**]: modify `compare_outputs()` in `scripts/cross_validate_year_outer.sh` to sort both files by `(lon, lat, year)` before diff-ing. Lower-cost; aligns Decision-12 with semantic-equality interpretation. Requires explicit doc note in the engine that "year_outer emits in year-major order, year_outer-aware downstream tooling must sort or otherwise normalize row order".
- **(a2) Engine row-buffering** [❌ NOT TAKEN]: add a buffer layer in year_outer mode that accumulates per-cell rows in memory and flushes in cell-major order. Higher-cost; preserves Decision-12 byte-equality strictly. Not needed given (a1) achieves the same scientific outcome at lower cost.

**B17(b) — small ~1 ULP numerical drift.** [⚠️ SUB-SECTION RECLASSIFIED PER §1.3.3 + §3.4 STATUS UPDATE + NEW §3.8]. Three hypotheses to bisect (per §3.4 above), with Phase A (17c.0.4) results in [...] brackets:
1. Floating-point summation order in per-PFT-total accumulators [❌ FALSIFIED §1.3.3 A.4 — drift magnitudes are 0.67-17.7% relative, six orders too large for ~1 ULP roundoff].
2. Global RNG state advancement order [❌ FALSIFIED §1.3.3 A.5 — `randfrac(long& seed)` is pure functional Park-Miller LCG; all randomness per-cell-isolated via `gridcell.seed`+`stand.seed`; no global RNG state].
3. Per-cell intermediate state initialization order [⚠️ NOT YET CONFIRMED — surviving candidate; refined by §1.3.3 A.6 + A.6 supplementary as **"setup-phase-ordering interaction with stochastic dynamics"**; specific code site requires seed-tracking dprintf instrumentation deferred to 17c.0.5 (β option)].

Bisection strategy [REVISED per §1.3.3 A.6]: re-run year_outer with single-cell-at-a-time iteration was the original plan, but Phase A discovered a STRONGER empirical localizer: **cell 0 is BIT-EXACT in ALL 17 drift files; cells 1, 2, 3 progressively diverge with cell index**. Drift is also CUMULATIVE OVER TIME within each cell (first-drift at year 1873-1876; spinup years bit-exact). NCELLS bisection is REDUNDANT given this stronger evidence. Next-step bisection (deferred to 17c.0.5 (β) option): seed-tracking dprintf instrumentation at every `randfrac` consumer site, then diff the two modes' seed-trace logs to identify the FIRST cell + FIRST callsite where seeds diverge.

**Acceptance criteria for the 17c.0.4 fix [SUPERSEDED — this fix scope = B17(a) only; full PASS substantive deferred to 17c.0.5].** The 17c.0.4 acceptance criterion was scoped to B17(a) closure (gates 5+6 PASS exit 0; gates 7+8 effective-pass count advances by ≥5 via SORTED_EXACT classification of the 5 PURE B17(a) files). Both criteria met per §1.3.6. Full PASS substantive (BIT_EXACT + SORTED_EXACT == 37/37 OR explicit-tolerance acceptance) is the 17c.0.5 acceptance criterion, dependent on the (α)/(β) decision per §1.3.9.

The full 17c.0.4 fix design + landing record lives in **§1.3 above** (`#### 1.3.1` through `#### 1.3.10`). The full reclassified B17(b) characterization lives in **§3.8 below** (added this commit).

### 3.8 Reclassified B17(b) — stochastic-process sensitivity per cell-iteration-order RNG slip (NEW this commit, 17c.0.4)

This sub-section formalises the empirical Phase A reclassification of B17(b) from `§3.4`'s original "small ~1 ULP numerical drift in per-PFT-total / `tot_runoff` files" to its actual character: **stochastic-process sensitivity of the LPJ-GUESS ecological dynamics engine to per-cell-iteration-order RNG slip caused by an as-yet-unidentified setup-phase-ordering interaction between gridcell_outer mode (interleaved per-cell-setup + per-cell-year-loop) and year_outer mode (batched all-cell-setup BEFORE main year-major loop)**.

#### 3.8.1 Empirical signature (carried forward from §1.3.3)

- **Per-cell drift profile**: cell 0 BIT-EXACT in ALL 17 affected files; cells 1, 2, 3 progressively diverge (drift growing approximately monotonically with cell index, per §1.3.3 A.6 table).
- **Within-cell drift profile**: first-drift at year 1873-1876 (4-5 years into the historical window); spinup years 1871-1872 BIT-EXACT in ALL cells; drift cumulative over time after first appearance.
- **Drift magnitudes** (per §1.3.3 A.4 table): 0.67-17.7% relative for per-PFT splits in low-biomass marginal-establishment cases (TrIBE, TrBR, IBS); ≤ 1.4% relative for cell totals in worst case; bit-exact for established dominants (C4G, BNE, BINE) at the 4-decimal-place printed precision.
- **Affected file class**: per-PFT-total .out files (lai, cmass, anpp, cflux, cpool, fpc, agpp, nflux, nmass, nuptake, nsources, nlitter, ngases, cton_leaf, clitter, aaet) + the per-cell aggregate `tot_runoff.out`. **Unaffected file class**: per-LC summed .out files (npool/anpp/cflux/cpool/nflux × cropland/natural/pasture; 15 files all BIT-EXACT raw cmp -s) + the .csv handshake outputs (none in the test envelope).
- **Build-agnostic**: serial (`build/guess`) AND single-process MPI (`build_mpi/guess` with `MPICH_CXX=g++` per §1.2.10) produce IDENTICAL drift envelope per §3.5. Confirms the divergence is engine-level, not build-config artefact.
- **Input-module-agnostic**: imogen and imogencfx variants of the .ins both reproduce the IDENTICAL 15+5+17 classification per §1.3.6. Confirms the divergence is in the framework's year_outer code path (`framework.cpp:484-733`), not the input-module-specific code.

#### 3.8.2 Hypothesis-bisection summary (Phase A; carried forward from §1.3.3)

| Hypothesis | Phase A status | Evidence |
|---|---|---|
| §3.4 (1) FP-summation roundoff | ❌ FALSIFIED | Drift magnitudes 6 orders too large for ~1 ULP at value-magnitude 0.02 |
| §3.4 (2) Global RNG state | ❌ FALSIFIED | `randfrac` pure functional; per-cell-isolated `gridcell.seed`+`stand.seed`; no globals |
| §3.4 (3) Per-cell init order | ⚠️ Surviving — refined to **"setup-phase-ordering interaction"** | Cell 0 BIT-EXACT; cells 1+ progressively diverge; spinup years all BIT-EXACT; drift cumulative over time |
| (NEW) Hypothesis 4: side-channel state in setup pipeline (e.g., `landcover_input` / `management_input` / `current_grid_index` / `coord_line[]`) advancing per-cell with mode-dependent timing | ⚠️ NOT YET CONFIRMED — code-spelunking exhausted easy candidates per §1.3.3 A.7; specific identification requires seed-tracking instrumentation | All checked sites (`current_grid_index`, `spinup_year_idx`, `is_first_gridcell`, `Stand::seed`, `Gridcell::seed`, `landcover_init`, `setup_multipart`, `reset`, `preload_all_climate`, `getclimate` vs `getclimate_for_year`) are per-cell-isolated-or-equivalent under analysis but the empirical drift exists, so SOMETHING per-cell-iteration-order-dependent is being missed |

#### 3.8.3 Scientific interpretation

The drift signature is consistent with **stochastic ecological dynamics divergence** — exactly the kind of small-magnitude perturbation that would be observed in an ensemble run of LPJ-GUESS with the same ecosystem state but slightly different starting random seeds. The model's stochastic processes (PFT establishment via `randpoisson(est, stand.seed)` at `vegdynam.cpp:598`; fire occurrence via `randfrac(stand.seed)` at multiple sites in vegdynam/spitfire/blaze; mortality via `randfrac(stand.seed)`; precipitation disaggregation via `prdaily(..., gridcell.seed)`) are KNOWN to be sensitive to seed perturbation at the per-individual-tree / per-patch level. When small seed shifts produce one-tree-lives vs one-tree-dies discrete events in low-biomass marginal-establishment PFTs (e.g., TrIBE establishing in Run A but not Run B at cell `(-57.75, -33.75)` yr 1876), the observable per-PFT biomass differs by ~17% relative for that PFT — but the cell total biomass barely changes (~1.4% in the worst case across all 9 simulation years).

This is **NOT a structural bug** in the year_outer framework code path. It IS a deviation from Decision-12's strict literal byte-equality contract — but Decision-12's spirit (year_outer must produce scientifically equivalent output to gridcell_outer) is satisfied within the natural stochastic-sensitivity bounds of the model. Decision-12 acceptance criterion 2 ("PASS substantive within an explicit tolerance specified in `notes/STEP_17b.md` §3a.7") is the empirically-grounded acceptance path: implementing tolerance-based comparison (per the (α) option in §1.3.9 + 17c.0.5) closes B17(b) at a scientifically-honest level without overfitting to the LPJ-GUESS RNG implementation details.

#### 3.8.4 Why specific root-cause identification requires seed-tracking instrumentation (Phase A's wall)

Phase A code-spelunking examined ALL of: (a) `gridcell.seed` initialization + advancement sites; (b) `stand.seed` initialization + advancement sites including `Stand::clone` deserialization at `guess.cpp:1110-1138`; (c) `current_grid_index` advancement in `getgridcell`; (d) `spinup_year_idx` formula equivalence between `getclimate` (gridcell_outer accumulator) and `getclimate_for_year` (year_outer closed-form); (e) `is_first_gridcell` setting symmetric in both modes; (f) `landcover_init` deterministic + per-cell-isolated; (g) `setup_multipart` + `reset` + `climate.initdrivers` symmetric per-cell setup; (h) `preload_all_climate` does NOT advance `gridcell.seed` (only loads source monthly arrays + CO2); (i) `interp_climate` calls `prdaily(..., seed)` which advances `gridcell.seed` once per (cell, year) on day 0 — IDENTICAL in both modes per the day-0 conditional. EVERY checked site is per-cell-isolated-or-equivalent. The empirical drift exists despite this. **The bug must be in something not in the above list** — likely a side-channel state that interacts with `randfrac` via a less-obvious path. Without seed-tracking dprintf instrumentation (every `randfrac` consumer dumps `(cell_idx, year, day, callsite, pre_seed, post_seed)` then diff the two modes' traces), pinpointing the specific code site is infeasible by code review alone. This is the (β) option in §1.3.9 + 17c.0.5; estimated +1-2 d focused investigation.

The (α) option (tolerance-based comparison upgrade to `compare_outputs()`) does NOT require root-cause identification — it accepts the divergence as scientifically-bounded and adjusts the comparison contract to match the engine's actual stochastic-sensitivity envelope. Recommended in §1.3.9 unless there is a strong scientific or contractual reason to want true byte-equality.

#### 3.8.5 Operational acceptance: provisional 2% tolerance (decided 2026-05-13 night, session 4; supersedes §1.3.9 + §3.6 formal-implementation path) — **NOW SUPERSEDED-BY-CLOSURE per §3.8.6 (2026-05-15 early morning)**

> **§3.8.5 SUPERSEDED-BY-CLOSURE (added 2026-05-15 in 17c.0.6 commit):** The provisional-acceptance regime documented in this §3.8.5 sub-section was SUPERSEDED at sub-phase 17c.0.6 (this commit) when B17(b) was mechanically CLOSED via the closed-form `spinup_year_idx` reproduction formula correction per the new §3.8.6 closure record below. The provisional 2% cell-total tolerance is no longer the operating envelope because the underlying drift no longer exists (4cell xval gates 7+8 envelope is now `15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER` exit 0 IDENTICAL between LOOSE and TIGHT coupling). The four §3.8.5 re-evaluation triggers are RETIRED-because-no-longer-applicable. The §3.8.5 sub-section is preserved verbatim below for forensic record of the provisional-acceptance era (2026-05-13 night through 2026-05-15 early morning) and to document the strategic decision-making that led to the eventual proactive revisit. See §3.8.6 for the canonical closure narrative.

After 17c.0.4 landed at commit `027d90d` (3-remote-converged at `origin/main`/`kit/main`/`helmholtz/main`) and the user reviewed Phase A's empirical evidence (per §1.3.3 + §3.8.1 through §3.8.4 above), the operational decision for B17(b) was revised from the original §1.3.9 formal α-vs-β scoping to a **lighter-touch provisional acceptance**:

> "Well I do not think we should implement anything in code for now, just simply documenting in the chat handoff that there is some divergence and we are accepting a 2% tolerance for now, but we may need to re-evaluate later. I suppose you could also include it as comment in the comparison code or something to that effect. It may be that we could come back and look at it and decide to do something about it."
> — user, 2026-05-13 night, session 4 (canonical narrative in `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` §4.13)

##### Decision summary

- **No new code authored** for the formal Option α implementation as a standalone 17c.0.5 sub-phase. The harness `scripts/cross_validate_year_outer.sh::compare_outputs()` continues to controlled-fail (exit 2) on B17(b) drift in 4cell year_outer scenarios, with the 17c.0.4 SORT-THEN-DIFF NORMALIZATION block (per §1.3.4) surfacing the divergence cleanly via the SORTED_DIFFER classification.
- **Provisional 2% tolerance accepted** as the operating envelope for B17(b) drift, consistent with Phase A's empirical max cell-total drift bound of 1.4% relative (per §1.3.3 A.4 + §3.8.1) with ~40% headroom. The provisional tolerance applies to **cell-total magnitudes** (the scientifically-meaningful aggregate); per-PFT splits in low-biomass marginal-establishment cases (TrIBE, TrBR, IBS) may exceed 2% individually (up to ~17-20% empirically per §1.3.3 A.4) but are accepted under the same provisional acceptance because they reflect inherent stochastic-perturbation behaviour of the LPJ-GUESS engine, NOT a structural year_outer code-path defect (per §3.8.3 scientific interpretation).
- **Scope**: B17(b) is operationally acceptable for proceeding to subsequent 17c.0 PREP sub-phases AND to the C3-era cluster phases. The B17(b) drift signature (per-PFT-totals + tot_runoff in 4cell+ multi-cell scenarios; build-agnostic; .ins-agnostic; cumulative-over-time; per-cell-iteration-order-dependent) does NOT block the strategic v1.0 milestones gated on substantive 4cell year_outer working.

##### Re-evaluation triggers (the formal Option α or (β) reactivates if any of these fires)

The operational acceptance is **provisional**. The formal Option α implementation OR the (β) seed-tracking dprintf root-cause investigation per §3.8.4 + §3.6 reactivates as the focused next step IF:

1. **Cell-total drifts exceed 2%** on a real-world gridlist or NCELLS scaling beyond the test gridlist's 4-cell envelope (e.g., during C3-era cluster smoke runs on a 480-cell or 4000-cell gridlist).
2. **Per-PFT splits diverge in scientifically-consequential PFT/cell combinations** beyond the current empirical envelope (e.g., a dominant-biomass PFT like BNE or BINE shows >2% relative drift for a cell where it represents the majority of the total; this would suggest the stochastic-perturbation signature is propagating into ecological dynamics that matter for paper-stage analysis).
3. **C3-era cluster smoke runs reveal MPI-multi-rank-specific drift** not captured by the 4cell single-process xval (e.g., per-rank runs show rank-0-vs-rank-N drift that exceeds the per-cell drift profile in §3.8.1; this would suggest there's an MPI-side amplification of B17(b) that the workstation single-process envelope did not surface).
4. **Paper-stage analysis surfaces a quantitative finding sensitive to per-PFT noise** at the 0.67-17.7% magnitude (e.g., F-13 working-paper Axis 1/2/3 figures show qualitative differences that would be eliminated by closing B17(b)).

If any of these triggers fires, the closure path defaults to **(α)** (~0.5-1 d harness change) unless the trigger evidence specifically points to **(β)** as more appropriate.

##### Sub-phase renumbering implication

Per §4.13.2 of the chat handoff, the 17c.0 PREP sub-phase ledger had two valid renumbering conventions:

- **Placeholder convention**: 17c.0.5 held as a placeholder for the deferred formal Option α implementation (reactivates if a re-evaluation trigger fires); next active sub-phase = 17c.0.6 (4-xval re-verify on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD).
- **Collapsed convention**: 17c.0.5 = next active sub-phase = 4-xval re-verify; the deferred formal Option α reactivates as a future sub-phase 17c.0.X if the re-evaluation trigger fires.

**DECIDED (user-authorised 2026-05-13 night-late, session 4)**: **Collapsed convention adopted.** Sub-phase **17c.0.5 = full 4-xval re-verify on B15+B16+B17(a)+B17(b)-provisionally-accepted HEAD** (this verification commit; see §1.5 landing record). The deferred formal Option α implementation OR Option β seed-tracking dprintf root-cause investigation reactivates as a **future sub-phase TBD (identifier to be assigned at reactivation time)** only on a §3.8.5 re-evaluation trigger firing per §3.8.5.5. Downstream sub-phases preserve their existing numbering: 17c.0.6 = C2 close-out tag annotation amendment decision; 17c.0.7 = workstation `mpirun -np 4` mimic; 17c.0.8 = PREP phase close-out.

##### Documentation surface

The §3.8.5 operational-acceptance decision is documented in the following surfaces (so any future reader — human or AI — sees the operational context regardless of which document they enter through):

- `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` §4.13 — canonical chat-handoff record (the decision narrative).
- `notes/STEP_17c.md` §3.8.5 — this sub-section (the canonical forensic-record entry).
- `scripts/cross_validate_year_outer.sh::compare_outputs()` — inline comment near the SORTED_DIFFER classification (so the harness reader sees the operational context directly without leaving the code).
- `notes/FOLLOWUPS.md` — B17 dashboard line update reflecting the provisional acceptance.

The above 3 in-tree changes (the .sh comment + this §3.8.5 + the FOLLOWUPS dashboard line) were **landed as the standalone follow-up commit `2771939` on 2026-05-13 night** (the user revised the original "roll into next work commit" guidance after deciding the strategic significance of the operational acceptance warranted its own version-controlled history entry; full canonical narrative in `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 4 "17c.0.4-followup → 2771939" record). The renumbering convention has since been **locked in** as the collapsed convention per §3.8.5.5 below.

#### 3.8.5.5 Re-evaluation cadence (NEW; user-authorised 2026-05-13 night-late session 4) — **NOW SUPERSEDED-BY-CLOSURE per §3.8.6 (the PERMITTED-revisit surface FIRED SUCCESSFULLY on 2026-05-14 night → 2026-05-15 early morning)**

> **§3.8.5.5 SUPERSEDED-BY-CLOSURE (added 2026-05-15 in 17c.0.6 commit):** The cadence regime documented in this §3.8.5.5 sub-section enumerated TWO reactivation surfaces — the FORCED-reactivation surface (4 §3.8.5 triggers above) AND the PERMITTED-reactivation surface (proactive revisit at user discretion per the 5th cadence bullet introduced at 17c.0.5-clarification commit `e03ceb1`). The PERMITTED-reactivation surface FIRED SUCCESSFULLY on 2026-05-14 night → 2026-05-15 early morning when the user proactively revisited B17(b) per the verbatim directive _"I would prefer that we try to see if we can resolve the issue"_; this firing yielded the §3.8.6 mechanical closure of B17(b). The FORCED-reactivation surface is RETIRED because the underlying drift no longer exists (the four triggers each presupposed `>= 2%` drift envelope existence; that envelope is now bit-exact zero after sort normalization). The §3.8.5.5 sub-section is preserved verbatim below for forensic record of the cadence-era (2026-05-13 night-late through 2026-05-15 early morning) and to document the foresight that the PERMITTED-reactivation surface was specifically designed-in to permit user proactive revisit absent any FORCED-trigger firing — the actual closure path used. See §3.8.6 for the canonical closure narrative.

The provisional acceptance per §3.8.5 is **not a one-shot decision** — it remains conditional on ongoing surveillance per the four re-evaluation triggers above. The user-authorised re-evaluation cadence (2026-05-13 night-late, session 4) is:

- **Routine xval re-verify** (every 4-xval re-verify run on this branch; see §1.5 landing record for the canonical 17c.0.5 baseline): controlled-fail exit-code 2 + the `15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER` envelope is the **expected** routine outcome. ANY deviation from this envelope (e.g., an additional file becoming SORTED_DIFFER, the BIT_EXACT count dropping below 15, the SORTED_EXACT count dropping below 5, or a per-cell-total drift exceeding 2%) immediately fires re-evaluation trigger 1 or 2 and warrants closure-path investigation.
- **C3-era cluster smoke runs** (17c.1+ MPI-multi-rank scenarios): cell-total drift bound MUST hold across MPI rank boundaries; per-rank vs reference single-process drift profile MUST be inspected to detect any MPI-side amplification per re-evaluation trigger 3.
- **Paper-stage analysis** (F-13 working paper Axis 1/2/3 figure generation): per-PFT-noise-sensitive findings MUST be cross-checked against gridcell_outer baseline at the same (cell, year, PFT) tuples per re-evaluation trigger 4. If qualitative finding differences are observed, the closure-path investigation reactivates.
- **Ad-hoc** (ANY of the four triggers above firing outside the routine cadence): closure-path investigation reactivates immediately at the time of trigger detection; the deferred Option α (~0.5-1 d harness change) or Option β (~+1-2 d seed-tracking dprintf instrumentation per §3.8.4) becomes the focused next step.
- **Proactive revisit at user discretion (NEW; clarification commit on top of 17c.0.5 commit `29ccc87`)**: per the user's verbatim 2026-05-13 night directive — _"It may be that we could come back and look at it and decide to do something about it"_ — the user MAY at any time elect to proactively revisit the B17(b) provisional acceptance and pursue Option α (tolerance-based comparison upgrade) or Option β (seed-tracking dprintf root-cause investigation) **even absent any of the four §3.8.5 triggers firing**. Reasonable proactive-revisit prompts include (illustrative, not exhaustive): (a) a deliberate paper-readiness polish phase before F-13 working-paper figure generation; (b) a focused improvement sub-phase between substantive C3-era cluster work blocks where the user wants to consume slack capacity productively; (c) reviewer feedback on a draft paper or pull request that surfaces a comment about the 0.67-17.7% per-PFT-split drift even though no specific finding is sensitive to it; (d) the user simply deciding they would prefer the formal closure now for completeness or v1.0-release-readiness reasons. **The trigger list (1)-(4) above defines the FORCED-REACTIVATION surface (the situations where the closure-path investigation MUST resume); the proactive-revisit hook defines the PERMITTED-REACTIVATION surface (any other situation where the user CHOOSES to resume).** Both surfaces are first-class — the operational acceptance is provisional in both directions: it sticks until either a trigger forces it off OR the user decides to take it off voluntarily.

The cadence is documented in:
- `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 5 §5.3 "B17(b) Re-evaluation Cadence" — canonical chat-handoff record (the cadence narrative).
- `notes/STEP_17c.md` §3.8.5.5 — this sub-section (the canonical forensic-record entry).
- `notes/FOLLOWUPS.md` — B17 dashboard line update reflecting cadence enforcement at every routine xval re-verify.

#### 3.8.6 B17(b) MECHANICAL CLOSURE — closed-form `spinup_year_idx` reproduction formula correction (NEW 2026-05-15; sub-phase 17c.0.6; SUPERSEDES §3.8.5 + §3.8.5.5 provisional-acceptance regime)

> **TL;DR:** B17(b) was a **deterministic implementation defect** in the closed-form `spinup_year_idx` reproduction formula used by `(Imogen|IMOGENCFX)Input::preload_all_climate` + `(Imogen|IMOGENCFX)Input::getclimate_for_year`, NOT a stochastic-process sensitivity per §3.8.3. The formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (derived in `notes/STEP_17a.md` §5.4 at C1.1 introduction commit `90401f2`, 2026-05-10) was based on a false premise that `spinup_year_idx` persists across cells in gridcell_outer mode. The actual code in both ImogenInput::getgridcell() at `imogen_input.cpp:880` AND IMOGENCFXInput::getgridcell() at `imogencfx.cpp:1122` RESETS `spinup_year_idx = 0` at the start of every cell, making the per-cell behavior depend ONLY on `year_idx % NYEAR_SPINUP`. The spurious `cell_idx * nyear_spinup` term introduced a per-cell offset that gridcell_outer doesn't have, causing cell c (c >= 1) in year_outer to use spinup imogen_years shifted by c*nyear_spinup positions relative to gridcell_outer. Fixed in this commit at 4 source-side LOC across 4 symmetric closed-form formula sites (2 in `imogen_input.cpp` + 2 in `imogencfx.cpp`) + 6 doc-comment blocks at the same sites + 2 .h header doc-block updates. Full 8-gate verification CONFIRMS mechanical closure with `15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER` envelope on BOTH 4cell xval scenarios (gates 7+8) — the 17 previously-SORTED_DIFFER files are now ALL SORTED_EXACT (data identical between modes after row-order normalization).

##### 3.8.6.1 Trigger for the proactive revisit (PERMITTED-reactivation surface fires)

After 17c.0.5-clarification commit `e03ceb1` (2026-05-14 early morning) broadened the B17(b) reactivation surface from FORCED-only (4 §3.8.5 triggers) to FORCED + PERMITTED (proactive revisit at user discretion at any time per the new §3.8.5.5 5th cadence bullet), the user reviewed the C2 close-out tag amendment scoping options (a/b/c per §0.11) and **exercised the PERMITTED-reactivation surface** with the verbatim 2026-05-14 night directive:

> "rather than the recommended deferral, I think I would prefer that we try to see if we can resolve the issue — at least examine the various H4(a, b, c) options to see if any of them prove useful solutions — what do you think about that?"
> — user, 2026-05-14 night, session 4 continuation

This was **the first proactive use of the PERMITTED-reactivation surface introduced at 17c.0.5-clarification just hours earlier** — the surface's intended use case (proactive revisit at user discretion absent any FORCED-trigger firing) was realised in the very next sub-phase after its introduction. The user added an explicit rollback constraint:

> "in case our various h4 investigations do not yield meaningful corrective outcomes for the divergence issues..., we may want to just accept the divergences and roll things back to current state... and proceed from there to a proper close out and continue to what we had already planned next."
> — user, 2026-05-14 night, session 4 continuation

This rollback discipline shaped the investigation as a **branched feature investigation** with an explicit no-go-then-discard escape hatch, NOT a mid-flight irreversible change to `main`.

##### 3.8.6.2 Phased attack plan (Phase A → D → E)

The investigation was structured as 5 phases:

| Phase | Scope | Exit criterion | Outcome |
|---|---|---|---|
| **A** | **Pre-instrumentation code review** of H4 sub-hypotheses (H4a: cumulative-cache off-by-one; H4b: pointer-keyed STL containers; H4c: static accumulating across cells; H4d: output-module feedback) | High-confidence root-cause identification OR proceed to Phase B | ✅ **HIGH-CONFIDENCE H4a confirmation** (spinup_year_idx formula; H4b/c/d ruled out); Phase B + C skipped |
| ~~B~~ | ~~Targeted instrumentation on feature branch step17c-b17b-investigation~~ | ~~Bisect to specific call site~~ | ⏸ **SKIPPED** (Phase A high-confidence finding obviated) |
| ~~C~~ | ~~Full Option β seed-tracking dprintf at all `randfrac`/`randpoisson` consumers~~ | ~~Per §3.8.4 instrumentation plan~~ | ⏸ **SKIPPED** (Phase A high-confidence finding obviated) |
| **D** | **Author 4-LOC surgical fix + verify with full 8-gate re-run** | gates 7+8 envelope changes (full closure / partial / no-improvement) | ✅ **FULL CLOSURE** (`15 BIT + 22 SORTED + 0 DIFFER` exit 0 BOTH modules) |
| **E** | **6-surface documentation cascade + commit + ff-merge to main + 3-remote push + tag amendment** | This commit lands | ✅ **THIS COMMIT** |

Phase A's high-confidence H4a finding compressed the originally-planned 5-phase ~2-3 d work into ~3-4 h (Phase A code review + Phase D fix + 8-gate verification + Phase E cascade), illustrating the value of pre-instrumentation forensic code review before committing to instrumentation overhead.

##### 3.8.6.3 Root cause — incorrect closed-form formula derivation in `notes/STEP_17a.md` §5.4

The C1.1 implementation (commit `90401f2`, 2026-05-10) introduced two new methods on `ImogenInput`: `preload_all_climate(Gridcell&, int, int)` (write-side; pre-loads per-cell-per-year climate into the cache) and `getclimate_for_year(Gridcell&, int, int)` (read-side; serves cached climate per cell, year, day). Both methods needed to compute `imogen_year` for each (cell, year) tuple to drive the existing `readenv()` cache lookup. In gridcell_outer mode, the existing `getclimate()` method derives `imogen_year` from a stateful `spinup_year_idx` member that increments on day 0 of each spinup year. For year_outer mode to byte-exactly reproduce gridcell_outer's climate inputs (Decision-12 acceptance criterion), the new methods needed to reproduce this state-machine progression deterministically via a closed-form formula keyed on `(cell_idx, year_idx)`.

The derivation in `notes/STEP_17a.md` §5.4 (lines 215-245 of that file at C1.1 introduction) reasoned as follows:

- `init()` sets `spinup_year_idx = 0`
- For each (cell, spinup year, day 0) call, `spinup_year_idx` is incremented by 1 (modulo NYEAR_SPINUP) AFTER `imogen_year` is computed using the BEFORE value
- "Cell C, spinup year Y, day 0" has been preceded by `C * nyear_spinup + Y` such increment events (C cells × nyear_spinup spinup years + Y prior spinup years within cell C)
- Therefore `spinup_year_idx_BEFORE_THIS_CALL = (C * nyear_spinup + Y) % NYEAR_SPINUP`
- And `imogen_year = FIRST_SPINUP_YEAR + spinup_year_idx_BEFORE_THIS_CALL`

The §5.4 derivation included a verbatim worked example at line 226: _"Cell 1's spinup year 0, day 0: starts from `spinup_year_idx = 10` (carried from cell 0); `imogen_year = FIRST_SPINUP_YEAR + 10 = 1881`"_. This worked example is the smoking-gun encoding of the false assumption.

The actual code at `lpjguess/modules/imogen_input.cpp:880` (and symmetrically `lpjguess/modules/imogencfx.cpp:1122`) is:

```cpp
// new gridcell ensure, we start at index one for spinup
spinup_year_idx = 0;
```

This RESETS `spinup_year_idx = 0` at the start of every cell inside `getgridcell()`. Therefore the gridcell_outer reference behavior is: cell c, spinup year y → `imogen_year = FIRST_SPINUP_YEAR + (y % NYEAR_SPINUP)` for ALL cells (NO cell_idx dependence). The §5.4 derivation's worked example claim _"starts from spinup_year_idx = 10 (carried from cell 0)"_ is wrong; the actual code ALWAYS starts from `spinup_year_idx = 0` at every cell. The cumulative count `C * nyear_spinup + Y` overcounts by exactly `C * nyear_spinup` events (the per-cell reset wipes the increment history).

The correct closed-form formula is therefore:

```
spinup_year_idx_at_(cell_idx, year_idx)
    = year_idx % NYEAR_SPINUP    ← NO cell_idx term
```

##### 3.8.6.4 Empirical signature explained mechanically

For nyear_spinup=2 + 4-cell xval (cells 0..3) the buggy formula produced these spinup imogen_years per cell (vs gridcell_outer reference {1801, 1802} per cell):

| Cell | Spinup year 0 imogen_year (year_outer pre-fix) | Spinup year 1 imogen_year (year_outer pre-fix) | gridcell_outer reference (all cells) |
|---|---|---|---|
| 0 | (0 × 2 + 0) % 30 = 0 → 1801 | (0 × 2 + 1) % 30 = 1 → 1802 | {1801, 1802} ✓ matches |
| 1 | (1 × 2 + 0) % 30 = 2 → 1803 | (1 × 2 + 1) % 30 = 3 → 1804 | {1801, 1802} ✗ differs |
| 2 | (2 × 2 + 0) % 30 = 4 → 1805 | (2 × 2 + 1) % 30 = 5 → 1806 | {1801, 1802} ✗ differs |
| 3 | (3 × 2 + 0) % 30 = 6 → 1807 | (3 × 2 + 1) % 30 = 7 → 1808 | {1801, 1802} ✗ differs |

This **shift-by-c*nyear_spinup** pattern mechanically explains every empirical fingerprint of B17(b) catalogued in §3.8.1:

| Empirical fingerprint (§3.8.1) | Mechanical explanation from spinup_year_idx formula bug |
|---|---|
| Cell 0 BIT-EXACT in ALL 17 affected files | `cell_idx = 0` zeroes the spurious `cell_idx * nyear_spinup` term → cell 0 sees same spinup imogen_years as gridcell_outer → identical evolution |
| Cells 1, 2, 3 progressively diverge with cell_idx | The shift increases monotonically with cell_idx (cell 1 sees imogen_years +2, cell 2 sees +4, cell 3 sees +6 vs reference) → divergent climate inputs → divergent vegetation evolution |
| Spinup years 1801-1802 BIT-EXACT in ALL cells (per §3.8.1) | This is the gridcell_outer reference imogen_years range (FIRST_SPINUP_YEAR={1801, 1802}); year_outer pre-fix used DIFFERENT values for cell ≥ 1 → BUT the OUTPUT values during the spinup itself are not in the .out files (only historical years are emitted) → the divergence manifests in the historical-year .out files via inherited divergent spinup vegetation state, not in spinup-year .out output (which doesn't exist in the test envelope) |
| First-drift at year 1873-1876 (4-5 years into historical window) | The spinup divergence accumulates into divergent vegetation states at end of spinup; the divergent vegetation states then produce divergent stochastic ecological dynamics (PFT establishment via `randpoisson` with `stand.seed`; fire/mortality via `randfrac` with `stand.seed`) during the historical window; the first observable .out divergence appears 4-5 years into the historical window because the stochastic perturbations have to accumulate before they produce a visible per-PFT-total deviation |
| Drift cumulative over time after first appearance | Cumulative stochastic-perturbation propagation through the ecological dynamics |
| Per-PFT-total .out files affected; per-LC summed .out files unaffected | Per-LC summation conserves total biomass within each landcover across the spinup perturbation; only the inter-PFT distribution differs (consistent with §3.8.3 "stochastic ecological dynamics divergence" interpretation, except now we know the source is the spinup perturbation rather than a downstream RNG slip) |
| LOOSE-vs-TIGHT envelope IDENTICAL (§3.8.3 "coupling-invariance") | BOTH `imogen_input.cpp` (loose coupling C1.1+C1.2 path) AND `imogencfx.cpp` (tight coupling C1.3 sub-step 7.3.2 path) had IDENTICAL bug pattern in symmetric closed-form formula sites because the C1.3 sub-step 7.3.2 implementation (commit `7be595a`, 2026-05-10) intentionally mirrored the ImogenInput pattern verbatim, including the buggy formula. This is now mechanically confirmed rather than an unexplained empirical observation |
| 1cell xval BIT-EXACT throughout 17c.0.1+ era | `cell_idx = 0` zeroes the spurious term → 1cell xval was a structural false-positive PASS on the buggy formula that coincidentally matched the correct formula at cell_idx=0 |

##### 3.8.6.5 Latency analysis — why B17(b) survived through C1.1 → 17c.0.5

The bug was latent from C1.1 introduction (commit `90401f2`, 2026-05-10) through 17c.0.5-clarification (commit `e03ceb1`, 2026-05-14 early morning) — about 4 days. Three concurrent factors masked it:

1. **Audit item B15 (xval harness Class-1/Class-2 syntax false-positive; CLOSED 2026-05-13 at commit `019c9dd`)** silently degenerated ALL xval Run B to gridcell_outer mode. The "37/37 BIT-EXACT 4-cell" result reported in the C1 close-out tag annotation (`v0.17.0-step17a-c1-year-outer-single-process`; 2026-05-10) and in `notes/STEP_17a.md` §6.2 + CHANGELOG + FOLLOWUPS + TRUNK_R13078_BACKPORT_LEDGER as _"empirically validated for BOTH input modules across BOTH single-cell + multi-cell"_ was a B15-style structural false positive: Run A AND Run B both ran in gridcell_outer mode, producing identical output trivially without ever exercising the year_outer code path. After B15 was fixed at 17c.0.1+17c.0.2 (commit `019c9dd`, 2026-05-13), 1cell xval gates 5+6 PASSED BIT-EXACT for the FIRST TIME with year_outer actually exercised — but the bug remained masked because cell_idx=0 zeroes the spurious term.

2. **Audit item B16 (latent eager-cache-fullness check defect; CLOSED 2026-05-13 at commit `4d09b62`)** silently aborted ALL 4cell xval Run B at `preload_all_climate` post-B15-fix but pre-B16-fix. The 4cell Run B aborted at exit 99 after 3 banners — the simulation never produced any .out emissions, so B17 had no surface.

3. **Once B16 was fixed at 17c.0.3, the 4cell xval surfaced B17 (a + b sub-defects) for the first time** (gates 7+8 controlled-fail at 17c.0.3 + 17c.0.4 with `15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER` envelope). The 17 SORTED_DIFFER files were classified as "B17(a) row-emission-order divergence + B17(b) numerical drift" per §3 forensic. B17(a) was correctly mechanically closed at 17c.0.4 via harness sort-then-diff (which ALSO factored out part of the residual B17(b) drift in 5 PURE B17(a) files via row reordering). The remaining 17 SORTED_DIFFER files were classified as "B17(b) stochastic-process sensitivity" per §3.8 forensic (Phase A code-spelunking exhausted easy candidates per §1.3.3 A.7) and provisionally accepted at 2% per §3.8.5.

The §3.8 forensic correctly identified that "SOMETHING per-cell-iteration-order-dependent is being missed" (per §3.8.2 H4 row), and correctly identified that Phase A code review had exhausted the easy candidates (`current_grid_index`, `is_first_gridcell`, `Stand::seed`, `Gridcell::seed`, `landcover_init`, `setup_multipart`, `reset`, `preload_all_climate` cache-loading order, `getclimate` vs `getclimate_for_year`). What §3.8 MISSED was the **closed-form `spinup_year_idx` reproduction formula itself**: the §3.8.4 H4 enumeration explicitly checked _"`spinup_year_idx` formula equivalence between `getclimate` (gridcell_outer accumulator) and `getclimate_for_year` (year_outer closed-form)"_ but did NOT independently re-derive the formula against the actual code — it implicitly trusted the C1.1 derivation in `notes/STEP_17a.md` §5.4 as correct. The §5.4 derivation was the bug; trusting it was the missed audit.

##### 3.8.6.6 The fix — 4-LOC surgical change at 4 symmetric sites

The fix replaces `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` with `year_idx % NYEAR_SPINUP` at FOUR sites:

| # | File | Function | Side | Approx line (pre-fix) |
|---|---|---|---|---|
| 1 | `lpjguess/modules/imogen_input.cpp` | `ImogenInput::preload_all_climate` | write-side (cache populator) | ~1199 |
| 2 | `lpjguess/modules/imogen_input.cpp` | `ImogenInput::getclimate_for_year` | read-side (cache consumer) | ~1300 |
| 3 | `lpjguess/modules/imogencfx.cpp` | `IMOGENCFXInput::preload_all_climate` | write-side | ~1466 |
| 4 | `lpjguess/modules/imogencfx.cpp` | `IMOGENCFXInput::getclimate_for_year` | read-side | ~1601 |

Both write-side (preload) and read-side (getclimate_for_year) MUST use the IDENTICAL formula or the cache key won't match between the two paths; both pairs are corrected in this commit. The canonical forensic comment block lives at site #1 (~50 LOC inline comment); sites #2–#4 carry shorter cross-reference blocks back to the canonical site to avoid duplication while still providing local context for any future reader.

Two additional surfaces are updated for documentation consistency:

| # | File | Section | Change |
|---|---|---|---|
| 5 | `lpjguess/modules/imogen_input.h` | `ImogenInput::preload_all_climate` doc block | Updated formula in doc block (was: `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP`; now: `year_idx % NYEAR_SPINUP`) + added B17(b) closure annotation |
| 6 | `lpjguess/modules/imogencfx.h` | `IMOGENCFXInput::preload_all_climate` doc block | Symmetric change — updated formula + added B17(b) closure annotation |

The total source-side change is **+~150 LOC of inline doc/forensic comments + 4 net LOC of behaviour-affecting code** (the operative `spinup_year_idx_for_this = year_idx % NYEAR_SPINUP;` line at each of 4 sites; the previous formula was 2 lines, the new formula is 1 line, but I've kept the 2-line declaration-then-assignment structure for visual symmetry across sites). All doc comments cite this §3.8.6 + §3.8.5/§3.8.5.5 supersession + `notes/STEP_17a.md` §5.4 ERRATUM cross-reference.

##### 3.8.6.7 8-gate verification — full closure confirmed

| Gate | Scope | Pre-fix outcome (per §1.5 baseline) | Post-fix outcome (this commit) | Verdict |
|---|---|---|---|---|
| 1 | `lpjguess/build/` rebuild (single-process) | NO-OP (binary sha256 stable) | ✅ exit 0; `imogen_input.cpp.o` + `imogencfx.cpp.o` recompiled; `guess` + `runtests` re-linked; only pre-existing Timer sprintf-overflow warnings (none from the fix LOC) | PASS |
| 2 | `lpjguess/build_mpi/` rebuild (MPI variant) | NO-OP (binary sha256 stable) | ✅ exit 0; both .cpp recompiled; both binaries re-linked | PASS |
| 3 | `build/runtests` unit suite | 162/162 / 25 cases PASS | ✅ 162/162 / 25 cases PASS | PASS |
| 4 | `build_mpi/runtests` unit suite | 162/162 / 25 cases PASS | ✅ 162/162 / 25 cases PASS | PASS |
| 5 | `1cell imogen` xval (loose) | 37/37 BIT_EXACT exit 0 | ✅ 37/37 BIT_EXACT exit 0; banner_a=0 banner_b=5; NaN 0/0 | PASS regression-clean |
| 6 | `1cell imogencfx` xval (tight) | 37/37 BIT_EXACT exit 0 | ✅ 37/37 BIT_EXACT exit 0; banner_a=0 banner_b=5; NaN 0/0 | PASS regression-clean |
| **7** | **`4cell imogen` xval (loose)** | **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER + exit 2** (CONTROLLED-FAIL surfacing B17(b) per §3.8.5 envelope) | ✅ **`15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER + exit 0`**; banner_a=0 banner_b=5; NaN 0/0 | **B17(b) MECHANICALLY CLOSED** |
| **8** | **`4cell imogencfx` xval (tight)** | **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER + exit 2** (IDENTICAL envelope to gate 7 per §3.8.3 coupling-invariance) | ✅ **`15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER + exit 0`** IDENTICAL envelope to gate 7 | **B17(b) MECHANICALLY CLOSED — coupling-invariance preserved** |

The post-fix gate 7+8 envelope IDENTICALITY between LOOSE and TIGHT coupling confirms mechanically that the §3.8.3 "coupling-invariance of B17(b)" empirical observation arose from the IDENTICAL bug pattern existing in BOTH input modules' closed-form formula sites (4 sites total: 2 in each .cpp), and the IDENTICAL fix yields the IDENTICAL closure outcome. This was specifically PREDICTED in §3.8.6.4 above prior to running gate 8 and the prediction was verified.

##### 3.8.6.8 What this fix DOES NOT do

For forensic clarity, this fix has bounded scope. Specifically, it does NOT:

1. **Change the harness `compare_outputs()` semantics**: the B17(a) sort-then-diff normalization (added at 17c.0.4 commit `027d90d`) is RETAINED because B17(a) (row-emission-order divergence between cell-major gridcell_outer emission vs year-major year_outer emission) is a SEPARATE structural artifact of the year_outer loop's emission pattern, not B17(b). B17(a) remains CLOSED via the harness-side sort-then-diff (the .sh-only fix per §3.6 option (a1)); the post-fix gate 7+8 envelope `15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER` reflects 22 files that still need sort-normalization (purely B17(a)) but have IDENTICAL data after sort.
2. **Remove the §3.8.5 provisional 2% tolerance from the harness**: the harness's `if SORTED_DIFFER > 0` controlled-FAIL path is RETAINED because (a) it serves as a regression detector for any future divergence reintroduction, and (b) the §3.8.5 tolerance language in inline comments is updated in this commit (per the .sh surface in the cascade) to reflect the post-closure status without removing the controlled-FAIL machinery itself. The §3.8.5 tolerance no longer SEMANTICALLY APPLIES (it's preserved in commented form for forensic record), but the `SORTED_DIFFER > 0 → exit 2` mechanism is preserved as a structural regression detector.
3. **Re-run the full backport ledger entries for `step-17a-c1.1` / `step-17a-c1.2` / `step-17a-c1.3-7.3.2`**: those entries remain TRUNK-IRRELEVANT-by-novelty (the entire year_outer code path doesn't exist in trunk_r13078). The §3.8.6 closure adds a NEW `step-17c-17c.0.6-b17b-closure` entry classified TRUNK-IRRELEVANT-by-novelty for the same reason; the bug existed only in step-17a additions that themselves don't backport.
4. **Re-derive or update any other pre-existing `notes/STEP_17a.md` content beyond §5.4**: this fix limits its `notes/STEP_17a.md` touch to a NEW ERRATUM block at the head of §5.4 that marks the original derivation as superseded by §3.8.6 and includes a cross-reference. The §5.4 prose itself is preserved verbatim for forensic record of the original derivation premise.

##### 3.8.6.9 Forecasting lesson — independent re-derivation of trusted forensic inputs

The Phase A code-spelunking summary in §3.8.4 explicitly listed _"`spinup_year_idx` formula equivalence between `getclimate` (gridcell_outer accumulator) and `getclimate_for_year` (year_outer closed-form)"_ as a CHECKED candidate, but the check was a "trust-the-derivation" check rather than a "re-derive-from-actual-code" check. The §5.4 derivation in `notes/STEP_17a.md` was treated as the authoritative reference; no audit went back to `imogen_input.cpp:880` to re-verify that `spinup_year_idx` actually behaves as the derivation claims. Had such an independent re-derivation been performed at 17c.0.3 (when B16 was fixed and B17 surfaced), B17(b) would have been mechanically identifiable in ~30 minutes rather than provisionally accepted for 2 days.

**Forecasting lesson (candidate operational heuristic rule #9):** when a forensic note (`notes/STEP_*.md`) contains a derivation that is materially relied upon by source-side code (e.g., closed-form state-machine reproduction formulas), an audit that re-checks the SOURCE CODE against the DERIVATION should be a standard step in any subsequent forensic deep-dive, NOT just a check of the source code against itself. Trusted-input audits are independent-input audits.

This forecasting refinement should be considered for promotion to operational heuristic rule #9 if the 17c.0.6 closure pattern recurs in future forensic deep-dives.

##### 3.8.6.10 Documentation surface (6 in-tree files; +N/-M LOC; 4-LOC source-affecting + ~150-LOC doc-comment + cascade)

The §3.8.6 mechanical closure is documented in the following surfaces (so any future reader — human or AI — sees the closure context regardless of which document they enter through). Note: this matches the established 17c.0.5-clarification cascade pattern (§5.14 of chat handoff), extending it from 6-surface doc-only to 6-surface doc + 2-source-file fix:

| # | File | Change scope | Backport |
|---|---|---|---|
| 1 | `lpjguess/modules/imogen_input.cpp` | 4-LOC source change at 2 sites (preload_all_climate + getclimate_for_year) + ~80 LOC inline canonical forensic block at site 1 + ~25 LOC cross-ref block at site 2 | TRUNK-IRRELEVANT (year_outer code path is step-17a addition) |
| 2 | `lpjguess/modules/imogencfx.cpp` | 4-LOC source change at 2 sites (preload_all_climate + getclimate_for_year) + ~30 LOC cross-ref block at site 1 + ~25 LOC cross-ref block at site 2 + ~5 LOC update to existing C1.1-erratum comment | TRUNK-IRRELEVANT (same reason) |
| 3 | `lpjguess/modules/imogen_input.h` | Doc-block formula update (was `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP`; now `year_idx % NYEAR_SPINUP`) + B17(b) closure annotation block (~25 LOC) | TRUNK-IRRELEVANT |
| 4 | `lpjguess/modules/imogencfx.h` | Symmetric doc-block update + closure annotation (~25 LOC) | TRUNK-IRRELEVANT |
| 5 | `notes/STEP_17c.md` | Header dates block update (17c.0.6 added; deferred-future-TBD row → RETIRED-SUPERSEDED) + §1 sub-phase table 17c.0.6 row update + §3.8.5 + §3.8.5.5 SUPERSEDED-BY-CLOSURE blocks added + NEW §3.8.6 closure record (this sub-section, ~9 nested sub-sections) + Index updates for new §3.8.6 entry | DOC TRUNK-IRRELEVANT |
| 6 | `notes/STEP_17a.md` | NEW §5.4 ERRATUM block at the head of §5.4 marking the original derivation as superseded by §3.8.6, with cross-reference; §5.4 prose preserved verbatim | DOC TRUNK-IRRELEVANT |
| 7 | `notes/FOLLOWUPS.md` | "Last updated" header refresh + B17 row status update from "RECLASSIFIED + PROVISIONALLY ACCEPTED at 2% tolerance + (α)/(β) reactivates on re-evaluation trigger OR PROACTIVE REVISIT (FORCED + PERMITTED)" → "**MECHANICALLY CLOSED at 17c.0.6** via the spinup_year_idx formula correction per `notes/STEP_17c.md` §3.8.6; provisional-acceptance regime + reactivation cadence both retired" | DOC TRUNK-IRRELEVANT |
| 8 | `EXECUTION_PLAN.md` | Row 17c update reflecting 17c.0.6 landing + B17(b) MECHANICALLY CLOSED status | DOC TRUNK-IRRELEVANT |
| 9 | `CHANGELOG.md` | NEW dated entry for 2026-05-15 documenting the 17c.0.6 mechanical-closure commit (mirror of this §3.8.6) | DOC TRUNK-IRRELEVANT |
| 10 | `notes/TRUNK_R13078_BACKPORT_LEDGER.md` | NEW `step-17c-17c.0.6-b17b-closure` entry classified TRUNK-IRRELEVANT-by-novelty (year_outer code path is step-17a addition; nothing to backport) | DOC TRUNK-IRRELEVANT (self-referential: the ledger entry is itself trunk-irrelevant) |
| 11 | `scripts/cross_validate_year_outer.sh` | Inline comment updates near the SORTED_DIFFER classification + `Re-evaluation hook` + `effective-pass` block + FAIL message at `SORTED_DIFFER > 0` path: replace "B17(b) provisionally accepted at 2%" / "FORCED + PERMITTED reactivation" framing with "B17(b) MECHANICALLY CLOSED at 17c.0.6 via §3.8.6 formula correction; SORTED_DIFFER > 0 now indicates regression rather than expected-drift". ZERO logic change (controlled-FAIL machinery preserved as regression detector). | DOC (.sh-comment-only) TRUNK-IRRELEVANT (.sh harness only) |
| 12 (sibling) | `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` | NEW §6.1 "B17(b) Mechanical Closure" record (the canonical chat-handoff narrative of the proactive revisit + Phase A → D → E execution + 8-gate verification + this commit's landing); updates §5.14.x cross-references to include §3.8.6 supersession of §3.8.5 + §3.8.5.5 | DOC (sibling artifact, outside repo) |

The above 11 in-tree changes + 1 sibling-artifact change land **as a single commit** on the feature branch `step17c-b17b-investigation`, then ff-merged to `main`, then 3-remote pushed (origin/kit/helmholtz) per the established cadence + tagged `v0.17.6-step17c-b17b-closure` post-merge. The C2 close-out tag amendment is BUNDLED in the same commit/push event per user-authorised recommended-path 2026-05-15 ~01:44 UTC+2.

##### 3.8.6.11 Closure status

- **B17(a)** = **CLOSED** at 17c.0.4 commit `027d90d` (harness sort-then-diff per §3.6 option (a1)); preserved at this commit.
- **B17(b)** = **CLOSED at 17c.0.6 (this commit)** via the spinup_year_idx formula correction per this §3.8.6 (4-LOC source change + 6-surface cascade); SUPERSEDES the provisional 2% tolerance per §3.8.5 + the FORCED + PERMITTED reactivation cadence per §3.8.5.5.
- **Combined audit B17** = **CLOSED at 17c.0.6** (both sub-defects mechanically closed).

The §3.8 forensic narrative (§3.8.1 through §3.8.4) is preserved verbatim above this §3.8.6 sub-section because it accurately documents the empirical fingerprints + Phase A code-spelunking that eventually led to the closure. The §3.8.5 + §3.8.5.5 provisional-acceptance + cadence sub-sections are preserved with prepended SUPERSEDED-BY-CLOSURE blocks because they document the strategic decision-making during the provisional-acceptance era and the foresight of designing-in the PERMITTED-reactivation surface that ultimately enabled the mechanical closure path. Nothing prior to this §3.8.6 is rewritten or removed; only this §3.8.6 is added as the canonical closure record.



### 3.7 Why B17 was not caught by 17c.0.0 forensic or 17c.0.1+17c.0.2 verification

Three concurrent gaps allowed B17 to remain hidden through 17c.0.0 (`2beff31`) and 17c.0.1+17c.0.2 (`019c9dd`):
1. **B15 silently degenerated all 4cell xval Run B to gridcell_outer** until 17c.0.1 fixed B15. Pre-17c.0.1, the 4cell scenarios silently passed bit-equality (both runs took the same code path, producing identical .out files). B17(a) and B17(b) cannot manifest when both runs take the same code path with the same .out emission order.
2. **B16 silently aborted all 4cell xval Run B at `preload_all_climate`** after 17c.0.1 fixed B15 but before 17c.0.3 fixed B16. Post-17c.0.1, pre-17c.0.3, the 4cell Run B aborted at exit 99 after 3 banners — the simulation never produced any .out emissions, so B17(a) and B17(b) had no surface.
3. **The 17c.0.0 forensic predicted B16 (per §0.9) but did not predict B17.** This was a forecasting gap: §0.9 acknowledged "If 4cell year_outer outputs differ structurally from 4cell gridcell_outer outputs even after B15+B16 are both fixed, that is a real C1+C2 substantive-validation failure that was masked pre-B15" (per §0.8(4)) but did not bisect that residual into the row-ordering vs numerical-drift sub-categories that we now call B17(a) and B17(b). The 17c.0.0 forensic was correct that "deeper code-correctness investigation or explicit tolerance specification" might be needed; it is now needed (this is 17c.0.4's scope).

**Forecasting lesson (for §1.2.10's operational-heuristics carry-forward):** when a multi-stage staged-discovery defect chain is anticipated (B15 → B16 → ?), it is operationally valuable to enumerate the possible "?" sub-categories at the time of the initial forensic, even if they cannot be confirmed without first fixing the upstream defects. §0.8(4)'s "deeper code-correctness investigation OR explicit tolerance specification" was a coarse two-bucket forecast; a finer forecast would have enumerated row-ordering, summation-order roundoff, and global-RNG-state hypotheses explicitly. This forecasting refinement is recommended for any future analogous staged-discovery situations and could be added as **operational heuristic rule #9** if the 17c.0.4 investigation confirms the value (TBD).

### 3.10 Path α handshake-file write-path defect — forensic + fix (NEW 2026-05-15; sub-phase 17c.0.7)

The Path α handshake-file write-path defect was surfaced during 17c.0.7 harness authoring (the new `scripts/cross_validate_mpi_4rank.sh` harness; per §1.6 above) and fixed via harness-layer `DIR_COMMON` injection for non-loose modes. This section is the canonical forensic narrative + fix design + cross-references.

#### 3.10.1 Why this section exists (post-17c.0.7 harness-authoring surface)

When the 17c.0.7 harness was first run end-to-end in `prescribed` and `tight` coupling modes, the per-cell `.out` comparison portion succeeded (single-process vs MPI-4-rank produced bit-exact aggregated `.out` files) but the handshake-file comparison portion reported all 4 handshake files as MISSING in BOTH single-process and MPI-4-rank runs. The run logs contained "WARNING: could not open" lines naming `LPJG_main/IMOGEN/imogen_lpjg_flux.txt` (and analogous for the other 3 handshake files). The expected behaviour (per the C++ engine code at `lpjguess/modules/imogenoutput.cpp:140-142` + `:283-365`) was that the lead rank should auto-create `<DIR_COMMON>/LPJG_main/IMOGEN/` and write the 4 handshake files into it. The observed behaviour was that no `LPJG_main/IMOGEN/` directory existed anywhere under the xval output tree.

#### 3.10.2 The smoking gun — `DIR_COMMON` defaults to the empty string

Inspection of the xval setup at `runs/SSP1-2.6/main_xval_imogencfx.ins` revealed that the file does NOT import `imogen_intermediary.ins` (the canonical .ins file that sets `DIR_COMMON` for production runs). Consequently, `DIR_COMMON` defaulted to the empty string in the xval runs.

When `DIR_COMMON` is empty:
- The C++ engine constructs the handshake-directory path as `"" + "/LPJG_main/IMOGEN/"` = `/LPJG_main/IMOGEN/` (an absolute path at filesystem root).
- The `mkdir("/LPJG_main")` system call fails with `EACCES` (permission denied — the running user is not root).
- The error is caught (the C++ code uses `mkdir` with no error abort — only a warning is emitted).
- The subsequent `ofstream::open` of `/LPJG_main/IMOGEN/<file>` fails (the parent directory doesn't exist).
- The `ofstream` failure is detected via `!file_stream.is_open()` and emits "WARNING: could not open" to the run log.
- The simulation continues; the handshake files are silently NOT written.

#### 3.10.3 Production impact assessment

**Production runs are NOT affected** because production .ins files (e.g., `runs/SSP1-2.6/main_imogencfx.ins`, `runs/SSP1-2.6/main_loose.ins`) always import `imogen_intermediary.ins` which sets `DIR_COMMON` to a valid path. Inspection of every .ins file under `runs/SSP1-2.6/` confirms that ALL non-xval .ins files import `imogen_intermediary.ins`.

**Only the xval setup was affected** because `main_xval_imogencfx.ins` + `main_xval_loose.ins` were authored to be self-contained (no `imogen_intermediary.ins` import) to maximize xval-test independence from production-config drift. This was a reasonable authoring decision but had the unintended consequence of bypassing the canonical `DIR_COMMON` setting.

**Pre-17c.0.7 xval runs did not surface the defect** because no prior xval harness compared handshake files (only `.out` files). The 17c.0.7 harness is the first to compare handshake files; it surfaced the defect immediately on first end-to-end run.

#### 3.10.4 Path α fix design

**Path α (harness-layer fix; CHOSEN)**: at the xval harness layer, inject `DIR_COMMON "<absolute-path>"` into the wrapper `.ins` files for non-loose modes. The injection happens in the wrapper-writer functions `write_baseline_wrapper()` + `write_mpi_wrapper()` of `scripts/cross_validate_mpi_4rank.sh`. The injected path is per-mode-per-run-isolated (e.g., `<xval-root>/prescribed_baseline/`, `<xval-root>/prescribed_mpi/`, etc.) to avoid cross-run interference.

**Path β (C++ engine-layer fix; NOT CHOSEN)**: modify `lpjguess/modules/imogenoutput.cpp` to either (b1) default `DIR_COMMON` to CWD when empty, or (b2) abort-with-error when `DIR_COMMON` is empty but handshake writes are enabled.
- (b1) would silently move handshake files from their canonical location, potentially confusing consumers that expect them at `<DIR_COMMON>` (e.g., legacy A/B run setups that hardcode the expected location).
- (b2) would break legacy A/B run setups that work fine because they always import `imogen_intermediary.ins`.

**Path γ (template-layer fix; NOT CHOSEN)**: modify `runs/SSP1-2.6/main_xval_imogencfx.ins` + `main_xval_loose.ins` to import `imogen_intermediary.ins` (or to set `DIR_COMMON` directly). Would couple xval setup to production-config drift, defeating the original design intent of xval-test independence.

**Path α was chosen** because it is the lowest-risk option: it preserves all existing engine semantics + only adds defensive injection in the per-fork xval setup path that bypasses the canonical .ins import chain. It does not couple xval to production-config drift. It does not change C++ engine semantics. It is fully reversible (revert the harness change and the defect resurfaces — making the fix easy to validate post-hoc).

#### 3.10.5 Post-fix verification

Per the 8-gate convention extended with NEW gates 9-11 (per §1.6.4 above):
- Gates 9 (loose) + 10 (prescribed) + 11 (tight) all PASS exit 0.
- For prescribed + tight modes: 4/4 handshake files are BIT_EXACT between single-process baseline + MPI-4-rank runs (cmp -s exit 0 on all 4 files).
- For loose mode: 4/4 handshake files are correctly ABSENT_BY_DESIGN (loose mode does not trigger handshake-file writes because the LPJG-side coupling pathway is gated on non-loose modes).
- Pre-fix "WARNING: could not open" log lines are gone; replaced by clean handshake-write success traces showing the per-mode-isolated `<DIR_COMMON>/LPJG_main/IMOGEN/` paths.

#### 3.10.6 Future considerations (B19 sub-items)

- **Defensive observability improvement (recommended for B19 or later)**: the C++ engine could warn-on-empty-DIR_COMMON-when-handshake-writes-are-enabled, analogous to F4's signal-of-life banner-presence check at 17c.0.1 per rule #8. This would surface the defect earlier in any future xval-style setups that bypass the canonical .ins import chain. ~5 LOC C++ runtime diagnostic at the top of `flush_year` (warn if `DIR_COMMON.empty()` && `coupling_mode != "loose"`).
- **Engine-side `DIR_COMMON` documentation improvement (recommended for B19 or later)**: the engine could document the `DIR_COMMON` requirement explicitly in `lpjguess/modules/imogenoutput.cpp` + `lpjguess/modules/imogenoutput.h` (a doc block near the handshake-write entry point). Currently the requirement is implicit (no doc-comment mentions it). ~10 LOC doc-block addition.

These are deferred to B19 (or a tiny B-bundle) because they are nice-to-have observability improvements rather than essential fixes; 17c.0.7's Path α harness-layer fix is sufficient to unblock the cluster phases.

---

## 4 onwards — 17c.1 through 17c.4 cluster phases

_(Skeleton only at this commit; will be populated when reached. Renumbered from §2 in 17c.0.3 commit due to insertion of §2 (B16 forensic + fix) and §3 (B17 forensic surface) above.)_

| Phase | Scope (per session-3 handoff §0.4) |
|---|---|
| 17c.1 | `env_owl.sh` refinement against actual `module avail` output on owl |
| 17c.2 | Cluster MPI build via `make_guess.sh --mpi` against module-loaded NetCDF/HDF5/openmpi |
| 17c.3 | Cluster small smoke (4 ranks × 480-cell × 5-yr tight); xval-style match against workstation MPI mimic baseline |
| 17c.4 | Cluster production smoke (16 ranks × ~4 000-cell × 11-yr SSP1-2.6); validation against working-paper §2.5 thresholds |
| 17c.5 | C3 close-out tag `v0.18.0-step17c-c3-cluster-tight` |
