# Cluster setup + production-runs — comprehensive working document

**Version**: v0.1 (initial draft; session 7 evening close 2026-05-19; iteratively updated through session 8+ cluster + production-run work)
**Status**: 🔧 LIVING DOCUMENT — populated incrementally as session 8+ reconnaissance + production-config setup + cluster setup + Track 2 production runs proceed; intentionally kept open-ended so newly-surfaced findings + open questions + decisions can be appended in real time without breaking the document's structure.
**Last updated**: 2026-05-19 evening (session 7 close); first authoring + initial framing.

**Audience**: anyone (current + future maintainers + future chat agents) needing to:
- Plan + execute the v1.0 paper-publication production-run sequence (local + cluster)
- Understand the architectural decisions about cluster + `-input imogencfx` vs `-input imogen`
- Understand the B44 + cluster integration story honestly (including the §C caveat surfaced at session 7 close)
- Find the right canonical docs for any specific cluster / production-run question

**Companions**:
- `notes/PRODUCTION_RUN_CONFIG.md` — the consolidated smoke→production parameter delta + LU dataset map + cluster path translation + two-track architecture (THE canonical reference for what production-config looks like)
- `scripts/run_coupled.sh` — local workstation launcher (now with `--engine-only-mode` per B44)
- `scripts/cluster/run_coupled.sbatch` + `scripts/cluster/README.md` — cluster SLURM launcher + architecture overview
- `scripts/cluster/env_owl.sh` — cluster module-load template (PLACEHOLDER VALUES; needs SSH refinement)
- `notes/B37.md` (path-iv `done`-marker sidecar mechanism; root cause of pre-B44 4/32-year ceilings)
- `notes/B44.md` (productisation of path-iv as `--engine-only-mode` flag; per-session-7 LOCAL-launcher; cluster integration story below in §4-5)
- `notes/STEP_17c.md` §1.7.8 — 17c.1+ cluster phases ACTIVE NEXT roadmap
- `notes/FOLLOWUPS.md` F-10 + F-12 — architectural deadlock + tight-coupling resolution
- IMK-IFU legacy cluster orchestration: `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/` (~17 scripts; prior-art the current `scripts/cluster/` adapted from)
- Predecessor production-style `.ins` files: `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/` (Track 1 `cfx` mode reference; cluster path translation worked examples)

---

## ✅ 0.2 STRATEGIC RESOLUTION at session 8.0 C5 (2026-05-20 afternoon) — Option T_seq adopted

**Per `notes/B47.md` canonical landing record (~400 LOC) + session 8.0 C0-C5 verification + U1-U4 pre-flight reconnaissance**: the strategic question raised at session 7 close (preserved verbatim below this banner for forensic continuity per Rule #10 amendment-vs-rewrite corollary) is **resolved in favor of Option T_seq** — a sequential-standalone refinement of the original Option T family that wasn't in the original 4-options-list (R/T1/T2/T3) at session 7 close.

### Resolution summary

**Option T_seq**: bring `trunk_r13078` into rebuild repo at `forks/trunk_r13078/` (sibling to `lpjguess/`) → apply minimal source-edit (~180-310 LOC C++) to make trunk's `imogencfx` consume the rebuild engine's per-year ASCII climate library + skip the in-process engine call → run Track 2 in **sequential-standalone** mode (Step A: rebuild engine standalone via `scripts/run_coupled.sh --engine-only-mode` produces 1900-2100 × 8-field climate + per-year CO2 + non-CO2 atm-conc library; Step B: `scp -r` library to cluster ~2.5 GB; Step C: trunk-T_seq LPJG runs on cluster as pure pre-baked-library consumer using legacy `owl_hpc_cluster_scripts/scripts/` pattern).

**Total effort**: ~2-3 working days across blocks 8.0.1 (~0.5 d structural import) + 8.0.2 (~1-1.5 d source-edit + .ins authoring) + 8.0.3 (~0.5-1 d acceptance test).

**Sub-decisions adopted at C5**:
- (i) **Landing path**: `forks/trunk_r13078/` (cleaner organization per LEDGER §1.1's two-fork policy)
- (ii) **CO2 bridge**: option-α (in-source per-year CO2.dat reader; ~30-50 LOC trunk source-edit; matches existing T_anom.dat pattern); option-β Python aggregator deferred as fallback

**Two-fork long-term trajectory** (user-clarified at session 8.0 afternoon): `lpjguess/` (rebuild) = primary active-dev for v1.0+; `forks/trunk_r13078/` = backport fork brought to bare-minimum Track-2-runnable state at T_seq Installment-1 + eventually full fork-parity at post-paper Backport Sprint Installment-2 (~2900-3100 LOC remaining); both forks switchable alternatives, not replacements.

### Why T_seq vs the original 4-options (R / T1 / T2 / T3)

The session-7-close 4-options-list assumed the strategic question was **in-process trunk-imogencfx-with-engine** (T1 = with sidecar; T2 = with skip-flag; T3 = via NetCDF translation; R = rebuild). User's session 8.0 mid-discussion refinement reframed to **sequential-standalone trunk-LPJG-only-consumer-of-pre-baked-library** (T_seq) which drops out:

| Concern in T1/T2 | T_seq resolution |
|---|---|
| Per-rank in-process engine sidecar (~30-50 LOC bash) | N/A — engine has already finished standalone before LPJG runs |
| year_outer scaffolding (~400 LOC) | N/A — trunk runs gridcell_outer mode; year_outer never exercised |
| `imogenoutput.cpp` + `imogenoutput.h` (~821 LOC NEW) | N/A — LPJG never writes handshake files in T_seq (no engine waiting) |
| `climatemodel.cpp` engine-side delta (~263 LOC) | N/A — trunk's `RUN_IMOGEN_ENGINE` never executed (skip-engine flag bypasses it) |
| Fortran `imogen_lpjg.f` ~562 LOC delta (incl. B33(c) +145 LOC) | N/A — trunk has no Fortran; rebuild's engine (with all its Fortran fixes) is what runs |

**Net**: T_seq scope is ~180-310 LOC (Installment-1; first installment toward eventual full fork-parity in Installment-2 post-paper).

### Session-7-close preliminary estimate vs post-C0-C4 honest re-baselining (Rule #10 self-correction)

The session-7-close "~150-300 LOC; few-hour to ~1-day" preliminary T-estimate was **over-optimistic by ~5-10× when interpreted as in-process T1/T2** (actual C0-C4 measurement: ~1300-1600 LOC). User's T_seq refinement at session 8.0 mid-discussion brought scope back down close to the original session-7-close estimate (~180-310 LOC). Per Rule #10 amendment-vs-rewrite corollary, both the preliminary estimate and the C0-C4 honest re-baselining are preserved (preliminary at the section below this banner; honest re-baselining in `notes/B47.md` §2-§4).

### Cluster integration story under T_seq

Simpler than T1/T2 per §4.3 — the §4.3 architectural options table (Options α/α′/β/β′/γ) was framed for in-process engine + LPJG concurrent execution. Under T_seq:

- **Step A** (engine standalone): runs locally via B44 `--engine-only-mode`; ~12.5 min × 5 SSPs = ~1 h; produces 8-field climate library + per-year CO2.dat + non-CO2 atm-conc per-year files at `runs/<SCEN>/Common-directory/IMOGEN/output/<year>/`
- **Step B** (SCP/rsync to cluster): ~2.5 GB total (~500 MB per SSP × 5 SSPs; per U3 inspection of B44 acceptance-test output; 246 KB × 10 climate files × ~200 years per SSP + small CO2/done/internal files)
- **Step C** (trunk-LPJG on cluster): legacy `owl_hpc_cluster_scripts/scripts/mpi_run_guess_on_tmp.sh` + `setup_run_owl_with_scratch_lpj_work.sh` pattern with `INPUTMETHOD=imogencfx`; per-rank gridcell split; no per-rank sidecar; no in-process engine; no F-10 deadlock concern

**Blocks 8.1-8.7 retargeted under T_seq** (originally framed for in-process integration options under §4.3 + §5):
- 8.1 cluster reconnaissance + 8.2 LPJG-on-owl walkthrough: cover trunk-build module dependencies for `forks/trunk_r13078/build_owl/` (alongside rebuild's `lpj-guess_imogen_landsymm/build_owl/`)
- 8.3 source-read of trunk's imogencfx confirms T_seq integration works (NO need to investigate `-input imogen` auxiliary handling since T_seq uses `-input imogencfx`)
- 8.4 production-config delta authoring targets `forks/trunk_r13078_runs/SSP*/` (or similar structure-decision at 8.4 start)
- 8.5 local 100-cell production test for trunk-T_seq with full production knobs (BLAZE, popdens, ndep, _peatland LU)
- 8.6 local Track-1 paired 100-cell sample run with trunk's `-input cfx`
- 8.7 cluster sbatch wrapper update for trunk-T_seq (or use legacy launcher as-is)

### Cross-references for the T_seq resolution

- `notes/B47.md` (canonical landing record; ~400 LOC; full C0-C4 evidence + U1-U4 verification + design + acceptance gates)
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` ✅ STRATEGIC RESOLUTION section at top (two-installment trajectory + dual-fork lifestyle)
- `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1.4 (Axis 4 LPJG-version concern now resolved)
- `notes/FOLLOWUPS.md` top-of-dashboard + B47 row
- `EXECUTION_PLAN.md` row 17c (status update)
- `CHANGELOG.md` `[Unreleased]` dated entry for this commit
- `_chat_artifacts/b47_tseq_decision_2026-05-20/` (audit-evidence bundle: C0-C4 source-diff outputs + U1-U4 verification logs + this decision-record commit message)
- `_chat_artifacts/CHAT_HANDOFF_2026-05-18_session5_post_b19.md` Part 9 (sibling session-8 narrative)

---

## 0.2 STRATEGIC QUESTION raised at session 7 close (2026-05-19 12:53 AM) — Track 2 LPJG version: rebuild repo vs `trunk_r13078` minimally updated

_(Preserved verbatim below per Rule #10 amendment-vs-rewrite corollary. The session 8.0 C5 resolution in the banner above is the operational answer.)_

**TL;DR**: Before block 8.1, **session 8.0 needs a ~1-2 hour strategic decision** on which LPJ-GUESS version runs Track 2 (and therefore the cluster phase 1-3). Two options; the decision fundamentally reshapes the §1.2 8-block plan.

### Why this question is being raised

- **Track 1 used `trunk_r13078`** (earlier LPJ-GUESS 4.1 base + the user's prior IMOGEN integration; produced the LPJG-natural-flux outputs that feed `intermediary_py` Component B)
- **The rebuild repo uses LATER-LPJ-GUESS-4.1 base + ported trunk_r13078 features** (best-effort forward-port during the rebuild)
- **For paper-reviewer-defensibility**: "we held LPJ-GUESS constant + varied ONLY the climate-driver source between Track 1 and Track 2" is materially cleaner than "we used LPJG revision A for Track 1 + revision B for Track 2"; the Track 1 vs Track 2 comparison (validation triad Axis 4 per `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1.4) is confounded by 2 variables if LPJG version differs
- **trunk_r13078 already has `imogencfx`** integration (located at `~/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/version_{A,B}/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/modules/imogencfx.{cpp,h}` + `imogen_input.{cpp,h}` + `imogenlogger.{cpp,h}`); it is NOT a vanilla LPJ-GUESS 4.1 — it's the version the user actually used in production (Track 1 used `-input cfx` but the IMOGEN files are present)
- **The minimalist backport scope is therefore bounded**: not "port `imogencfx` from scratch" but "verify trunk_r13078's existing `imogencfx` works with rebuild IMOGEN engine outputs + apply ONLY the deltas that diverged during rebuild iteration (~150-300 LOC; see `notes/TRUNK_R13078_BACKPORT_LEDGER.md`)"

### Two options at session 8.0

| Option | Use this LPJG for Track 2 | Cluster work targets | Backport effort | Compatibility risk |
|---|---|---|---|---|
| **Option R** (rebuild) — current default | `lpj-guess_imogen_landsymm/` (rebuild repo) | `lpj-guess_imogen_landsymm/scripts/cluster/` + `runs/SSP1-2.6/main.ins` (production-config delta per §6) | ZERO (rebuild already integrated) | Paper integrity: Track 1 vs Track 2 confounded by LPJG version |
| **Option T** (trunk_r13078 minimally updated) — user proposal at session-7 close | `version_{A,B}/.../trunk_r13078/` minimally updated for Track 2 IMOGEN engine reads | `~/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_*` `.ins` files (already production-grade per `notes/PRODUCTION_RUN_CONFIG.md` §7) + the legacy cluster scripts at `~/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/` (the prior-art that worked for Track 1) | ~150-300 LOC well-bounded port (per `notes/TRUNK_R13078_BACKPORT_LEDGER.md` accumulator + session 8.0 enumeration); few-hour to ~1-day work | Paper integrity: LPJG version held constant; Track 1 vs Track 2 isolates climate driver as the ONLY variable |

### Three Option-T sub-options for HOW Track 2 reads rebuild IMOGEN engine outputs

| Sub-option | Mechanism | trunk_r13078 source-edit | Engine location | Compatibility risk |
|---|---|---|---|---|
| **T1** | Apply minimalist backport delta to trunk_r13078; trunk_r13078 runs `-input imogencfx` reading rebuild-IMOGEN-engine per-year ASCII directly (engine runs in-process via B44-style sidecar) | ~150-300 LOC backport + B44 sidecar mechanism into trunk_r13078's launcher | In-process | Low — both `imogencfx` lineages from same family |
| **T2** | Apply minimalist backport + add skip-engine flag (per CLUSTER_SETUP §4.3 Option α′/β′); rebuild's IMOGEN engine runs separately (locally via B44 `--engine-only-mode`); per-year ASCII library staged for trunk_r13078 to read | ~150-300 LOC backport + ~50-100 LOC skip-engine flag in trunk_r13078's `imogencfx.cpp` | Decoupled (engine local; LPJG on cluster) | Low — adds small interface; reuses existing code paths |
| **T3** | Convert rebuild IMOGEN engine output to ISIMIP3b-style daily NetCDFs; trunk_r13078 runs `-input cfx` (same as Track 1) | ZERO source-edit to trunk_r13078 | Decoupled | **Higher** — temporal-resolution conversion (IMOGEN monthly anomalies → ISIMIP3b daily) requires careful disaggregation logic; introduces a translation layer that could distort the IMOGEN climate signal we're trying to compare; **probably not worth the integrity risk** |

### Preliminary recommendation (subject to session 8.0 verification)

**Option T (trunk_r13078), with T1 or T2 sub-option.**

- **T1 is the simplest**: minimalist backport + B44 sidecar into trunk_r13078's launcher; engine and LPJG run together; matches the current rebuild operational pattern
- **T2 decouples cleanly**: minimalist backport + skip-engine flag; engine runs locally (smaller, faster, can use B44 `--engine-only-mode` directly); LPJG runs on cluster with no engine dependency
- **T3 is high-risk + low-elegance**: avoid unless T1/T2 prove infeasible

### Session 8.0 verification checklist (before block 8.1)

| Check | Question | Method |
|---|---|---|
| C0 | Does trunk_r13078's `imogencfx.cpp` accept the rebuild's IMOGEN engine per-year ASCII output format (same `T_anom.dat`, `CO2.dat`, etc. file names + columns)? | Diff `version_A/.../trunk_r13078/modules/imogencfx.cpp` vs `lpj-guess_imogen_landsymm/lpjguess/modules/imogencfx.cpp` |
| C1 | What's the actual backport delta size (LOC + commits) needed to bring trunk_r13078's `imogen*` files up to rebuild equivalence? | Enumerate via `notes/TRUNK_R13078_BACKPORT_LEDGER.md` accumulator + a clean `diff` between the trunk_r13078 + rebuild `lpjguess/modules/imogen*.{cpp,h}` and `imogen/code/imogen_lpjg.f` |
| C2 | Does trunk_r13078 have an equivalent of B19 + B20 + B36 + B39 fixes that v1.0 paper validation passed against? | Check `notes/B19.md`, `notes/B20.md`, `notes/B36.md`, `notes/B39.md` for files touched + verify whether trunk_r13078 has the equivalent fixes |
| C3 | Does trunk_r13078's launcher pattern (legacy `~/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/`) support the B44 path-iv sidecar (T1) OR have a clean way to support the skip-engine flag (T2)? | Read the launcher + decide insertion point for sidecar OR skip-flag |
| C4 | Effort estimate: backport + verification + cluster integration for trunk_r13078 — ~1-2 days vs ~1-2 days for rebuild Option R cluster integration. Which is actually shorter? | Per-option timing breakdown after C0-C3 |
| C5 | **Decision**: Option R (rebuild; current default) or Option T (trunk_r13078; cleaner paper consistency) | User after C0-C4 evidence presented |

**Estimated session 8.0 effort**: ~1-2 hours reconnaissance + decision. Then sessions 8.1+ proceed per chosen option.

### Cross-references for this strategic question

- `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1.4 (Axis 4 validation interpretation; previously tacitly assumed Option R; now flagged for Option T consideration)
- `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (the backport direction may **invert** from "rebuild → trunk_r13078 for upstream contribution" to "trunk_r13078 ← minimal-rebuild-additions for Track 2 paper consistency"; per session-7-close note added to that ledger)
- `notes/PRODUCTION_RUN_CONFIG.md` §7 (production-style `.ins` examples; the `lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_*` paths already production-grade; would be the canonical .ins for Option T)
- `notes/B44.md` (the path-iv `--engine-only-mode` mechanism; would need port-equivalent into trunk_r13078 under T1, or accompanying skip-engine flag under T2)
- `notes/FOLLOWUPS.md` top-of-dashboard session-7-close note

---

## 1. Recommended session-8+ ordering (the operational plan)

### ✅ BLOCK 8.3 LANDED + FULL ADDENDUM (2026-05-29 ~00:30 CEST session 13 day 1 close) — Track 2 production strategy LOCKED IN: PLUM-mask gridlist + Track-1-style shared HIST (SSP2-4.5 = shared baseline) + milan/8×64=512 default (genius/4×128=512 interchangeable) + 3-day walltime + 4 SCEN main.ins state_path retargeting + B64 NEW v1+ investigation

**FULL Addendum** (post-tag-landing through ~midnight session 13 day 1; ~3-4 h aggregate work). Daniel's Rule #13 follow-up on Block 8.3 SCEN smoke 1-cell missing-output edge case + Q1 (HIST climate sharing across SSPs) + Q2 (SCEN per-biome sensibility) led to multiple Track-2-production-strategy refinements all consolidated into this single addendum.

**6 refinements landed**:

1. **Production gridlist PLUM-mask alignment** — NEW `data/gridlist/gridlist_in_62892_and_climate_and_PLUMmask.txt` (62,512 cells; production ∩ PLUM mask). 26 missing cells: 23 Svalbard archipelago + 1 NW Canadian Arctic + 1 Yukon/Mackenzie + 1 SE Russia/Caspian-Aral; all 100% barren in HILDA+ historical with zero analytical value. Both HIST + SCEN now produce 62,512 cells consistently.

2. **Track-1-style shared HIST with SSP2-4.5 as shared baseline** — Q1 investigation revealed: (a) SSP1/2/3/5 byte-identical for 1900-2000 (max abs T_anom diff = exactly 0.000K vs SSP2-4.5); (b) SSP4-6.0 anomalous throughout 1900-2014 (max 0.32K + mean 8 microkelvin globally); (c) all 5 diverge starting 2014 (CMIP6 SSP-divergence period; max 0.08K + 1.5 ppm CO2 spread at 2020). Magnitude across 5 SSPs at year 2020: mean global T_anom diff ~0.002K + CO2 spread ~1.5 ppm — scientifically negligible. **Decision (option B): run 1 HIST for SSP2-4.5** (middle-of-the-road business-as-usual; in SSP1/2/3/5 byte-identical cluster avoiding SSP4 anomaly) + 5 SCEN restart from SSP2-4.5_cluster_hist/state/ → saves ~9 days cluster wall. Paper Methods §2.2 footnote: "HIST simulations 1900-2020 use SSP2-4.5 IMOGEN engine climate library as shared baseline; cross-SSP differences in HIST climate forcing are <0.002K mean global T_anom and <1.5 ppm CO2 by 2020 — well below model precision; ecosystem state at 2020 is effectively SSP-invariant; per-SSP divergence emerges from 2021 onward via SSP-specific SCEN climate libraries."

3. **setup_run_tseq.sh allocation defaults → milan/8×64=512** (interchangeable with genius/4×128=512; both = 512 ranks). Cluster-citizenship + immediate availability + 1.75× speedup over milan/4 baseline. **Interchangeability**: state files are per-rank (run0.state…run511.state); HIST + SCEN must use SAME total rank count for state-restart alignment, but partition + per-node CPU layout can vary. Drop-in alternative: `NNODES=4 CPU_PER_NODE=128 PARTITION=genius ./setup_run_tseq.sh` when milan is busy + genius has ≥4 idle nodes.

4. **WALLTIME default → 3-00:00:00** (3-day; max for milan + genius). Production HIST per-SSP wall on milan/8×64=512 ~52h / on genius/4×128=512 ~38h; both within 3-day budget.

5. **4 SCEN main.ins state_path retargeted** to SSP2-4.5_cluster_hist/state/ (SSP1-2.6, SSP3-7.0, SSP4-6.0, SSP5-8.5 SCEN); SSP2-4.5 SCEN already correctly points at its own. Original lines preserved at `.preB83close_track1.bak` per Rule #10 amendment-vs-rewrite.

6. **B64 ✅ CLOSED at session 13 day 2 2026-05-29 ~14:00 CEST** (Hypothesis 2 ✅ RESOLVED; **Hypothesis 1 ✅ CONFIRMED + REMEDIATION LANDED + EMPIRICALLY VALIDATED**; Hypothesis 3 MOOT). **Remediation complete**: Daniel's workstation chat agent did the 5-step splice fix (~33 min total wall) + rsynced corrected 18 GB SSP4-6.0 climate library to cluster (~02:30-03:30 CEST); cluster-side verification ~03:35 CEST confirmed 5-way SSP T_anom byte-identity 1900-2010 (corrupted +21% bias removed; year 2000 non-CO2 RF = 1.133761 W/m² canonical). **Rule #10 self-correction #26**: actual splice boundary = **2010/2011** (not 2014/2015 as planned-remediation docs assumed; rebuild's intermediary_py RF files use 2010/2011 scenario-start). **CO2-decoupling nuance**: SSP4-6.0 year-2100 CO2 = 631.42 ppm UNCHANGED (engine-evolved CO2 decoupled from prescribed non-CO2 RF; only per-cell climate vars 1900-2010 changed). Phase 3a/3b split ELIMINATED → all 5 SCEN parallel-ready. Original detail (filed-at-addendum): **Concrete evidence**: workstation-agent 5-SSP RF cross-comparison at year 2000 → ssp126/245/370/585 = 1.133761 W/m² (4-way byte-identical CMIP6 historical baseline) vs **ssp460 = 1.369924 W/m² (~21% higher; synthetic monotonic ~2%/yr exponential growth, not real CMIP6 historical with Pinatubo signal)**. Root cause: `imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp460.txt` has corrupted historical (1850-2014) from Tier-2 SSP4-6.0 generation pathway gap; scenario period (2015-2100) is reasonable. Anthropogenic emissions provenance ✅ confirmed clean (intermediary_py-derived; legacy IIASA paths INERT preserved for predecessor-comparison reproducibility per Axis 1; FILE_NON_CO2_VALS prescribed-RF design intentional per Huntingford2010+Smith2018 GMD). **REMEDIATION PLANNED on workstation** (~30-45 min total wall): backup → splice (shared CMIP6 historical 1850-2014 from ssp126 source-of-truth + ssp460 scenario 2015-2100) → re-run trunk-cpp-engine for SSP4-6.0 → re-FastRegrid → re-rsync 18 GB SSP4-6.0 climate library to cluster. **Cluster Track 2 launch NOT blocked**: Phase 1 (SSP2-4.5 HIST shared baseline) + Phase 3a (4-of-5 SCEN: SSP1, SSP2, SSP3, SSP5) UNAFFECTED + can launch as planned in parallel with workstation remediation. Phase 3b (SSP4-6.0 SCEN) waits for corrected library rsync. See `notes/FOLLOWUPS.md` B64 row + `_chat_artifacts/b8_3_cluster_smoke_2026-05-28/B8_3_evaluation_2026-05-28.md` §13.8.6 for full detail + 5-step remediation recipe.

**Track 2 production launch sequence (REVISED — Track-1-style shared HIST)**:

```bash
ssh owl  # or use Cursor Remote-SSH-attached terminal
cd /bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm

# === PHASE 1: Run 1 HIST for SSP2-4.5 (shared baseline) ===
# Defaults: NNODES=8 CPU_PER_NODE=64 PARTITION=milan WALLTIME=3-00:00:00 GRIDLIST=PLUM-mask 62512-cell
cd forks/trunk_r13078_runs/SSP2-4.5_cluster_hist
./setup_run_tseq.sh   # if milan busy: NNODES=4 CPU_PER_NODE=128 PARTITION=genius ./setup_run_tseq.sh
cd $WORK_BASE/SSP2-4.5_cluster_hist
bash startguess.sh
# Estimated wall: ~52h (milan/8x64) or ~38h (genius/4x128); within 3-day max

# === PHASE 2: WAIT for HIST to complete + state/ populated ===
# Verify: ls forks/trunk_r13078_runs/SSP2-4.5_cluster_hist/state/ | wc -l = 513 (512 .state + meta.bin)

# === PHASE 3: Launch ALL 5 SCEN runs in parallel (each restarts from SSP2-4.5_cluster_hist/state/) ===
# [B64 CLOSED 2026-05-29 session 13 day 2]: Phase 3a/3b split ELIMINATED. SSP4-6.0 ssp460 RF file
# remediation complete + corrected 18 GB SSP4-6.0 climate library rsync'd to cluster + empirically
# validated (5-way SSP T_anom byte-identity 1900-2010). All 5 SCEN now launch together.
# CRITICAL: same NNODES + CPU_PER_NODE as HIST (NPROCESS=512) for state-restart alignment.
# If HIST ran genius/4x128=512, SCEN must also use 512 ranks (genius/4x128 OR milan/8x64; interchangeable).
cd /bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm
for SSP in SSP1-2.6 SSP2-4.5 SSP3-7.0 SSP4-6.0 SSP5-8.5; do
  cd forks/trunk_r13078_runs/${SSP}_cluster_scen
  NNODES=4 CPU_PER_NODE=128 PARTITION=genius ./setup_run_tseq.sh   # match HIST 512-rank allocation; SCEN main.ins state_path → SSP2-4.5_cluster_hist/state/
  cd $WORK_BASE/${SSP}_cluster_scen
  bash startguess.sh
  cd /bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm
done
# Each SCEN ~10h wall (no spinup; restart from shared HIST state at year 2020)

# === PHASE 4: Total estimated cluster wall ~3-4 days (vs ~13 days for original 5 SSP-specific HIST plan) ===
```

**Allocation flexibility — milan/8×64=512 ↔ genius/4×128=512**:
- Both yield NPROCESS=512 ranks (state-restart-compatible)
- HIST + SCEN can use DIFFERENT partitions if each maintains the 512-rank total
- Example: HIST on milan/8x64 (52h) → state/ populated → SCEN on genius/4x128 (10h each) if milan is then busy + genius has 4 idle nodes
- setup_run.sh's gridlist split is deterministic given NPROCESS: per-rank chunks identical between milan/8x64 and genius/4x128 → state files align across partition variants

**Sequencing decision (Daniel's choice for SCEN parallel vs serial)**:
- **Parallel** (5 SBATCH jobs simultaneously): 5 SCEN concurrent if 5 × allocation = ≤ partition capacity; ~10h total cluster wall
- **Serial** (1 SBATCH at a time): 5 × 10h = ~50h total cluster wall
- **Hybrid** (2-3 SCEN at a time): balanced

---

### ✅ BLOCK 8.3 LANDED — Cluster end-to-end smoke validated; chosen-pipeline Track 2 production workflow operational on owl (2026-05-28 evening session 13 day 1 close; cluster-native via Cursor Remote-SSH owl01amd; tag `v0.25.0-cluster-trunk-tseq-smoke-complete`)

**Block 8.3 ✅ DONE** at session 13 day 1 close commit. Cluster path validated end-to-end for the chosen-pipeline (δ-B-variant trunk-C++ engine throughout) Track 2 production workflow on KIT IMK-IFU owl, milan partition × 4 nodes × 64 CPUs/node = 256 ranks. Both HIST + SCEN smoke phases ran cleanly: HIST main `601955` ExitCode 0:0 in 1h29m (256-rank; 4 cells/rank; 500yr spinup loop FIRST_SPINUP_YEAR=1900 + history 1901-2020) + SCEN main `602049` ExitCode 0:0 in 9m45s (~9× faster; restart=1 + restart_year=2020 + state_path absolute; G6.1 NEW gate ✅ SCEN restart from HIST state empirically validated). **8/9 acceptance gates ✅ PASS + 1/9 ⚠️ PARTIAL** (benign Svalbard barren-cell SCEN edge case; HIST showed Total cmass=0.000 throughout for that cell; not a defect; matches block 8.0.3 cell-2 high-Arctic LU-mismatch pattern). **Rule #9 datapoint #35 NEW**: finishup_lpj_work.sh SLURM script-cache portability bug surfaced empirically when HIST finishup `601956` failed instantly + fix landed (env-overridable FINISHUP_SCRIPT_DIR with BASH_SOURCE fallback in finishup_lpj_work.sh + `--export=ALL,FINISHUP_SCRIPT_DIR=${SCRIPT_DIR}` in setup_run.sh's startguess.sh HEREDOC) + empirically validated by SCEN finishup `602050` running cleanly under SLURM in 54s vs HIST's 0s instant-fail. Per-biome physical sensibility (G5): 36/50 anchor cells within Phase F published Smith2014/Pugh2019/Hickler2012/Friedlingstein2025GCB literature ranges; matches Phase F's 7-8/10 standard. Audit-evidence bundle at `_chat_artifacts/b8_3_cluster_smoke_2026-05-28/B8_3_evaluation_2026-05-28.md` (~365 LOC; 12 sections; gitignored). Full 9-surface doc cascade landed at this commit per Rule #1.

**POST-BLOCK-8.3 NEXT — Track 2 production runs** (5 SSPs × HIST + SCEN; ~3-7 days cluster wall + monitoring):

| # | Step | Notes |
|---|---|---|
| 1 | (Optional) **Block 8.7 1000-cell intermediate smoke** for production-config wall extrapolation | 1024-cell smoke wall (HIST 1h29m at 4 cells/rank with `npatch=25, nyear_spinup=500, freenyears=100`) extrapolates to ~90h per-SSP for full 62538-cell production — exceeds 3-day milan walltime budget. A 1000-cell intermediate (~244 cells/rank for 256-rank, similar to production per-rank workload) would refine the wall estimate before committing to full 5-SSP × HIST production launches. Could be subsumed by launching first SSP (e.g., SSP1-2.6) as the "Block 8.7 surrogate" + observe wall before launching the other 4 SSPs in parallel. |
| 2 | **Track 2 production HIST** (5 SSPs) | `cd forks/trunk_r13078_runs/<SSP>_cluster_hist && NNODES=4 CPU_PER_NODE=64 PARTITION=milan WALLTIME=3-00:00:00 ./setup_run_tseq.sh && cd $WORK_BASE/<SSP>_cluster_hist && bash startguess.sh` for each SSP. Production gridlist `gridlist_in_62892_and_climate.txt` is the default in `setup_run_tseq.sh` (62538 cells; 244 cells/rank for 256-rank MPI; clean rank loading per Rule #9 #34 fix). Each HIST job will save state to `forks/trunk_r13078_runs/<SSP>_cluster_hist/state/`. **CRITICAL**: same NNODES + CPU_PER_NODE for HIST + SCEN (state files are per-rank; rank-count change breaks state restart). |
| 3 | **WAIT for all 5 HIST runs to complete** + state/ populated for each SSP | Verify via `ls forks/trunk_r13078_runs/<SSP>_cluster_hist/state/ | wc -l` = 257 (256 .state + meta.bin) for each SSP. |
| 4 | **Track 2 production SCEN** (5 SSPs; restart from corresponding HIST state) | `cd forks/trunk_r13078_runs/<SSP>_cluster_scen && NNODES=4 CPU_PER_NODE=64 PARTITION=milan WALLTIME=1-00:00:00 ./setup_run_tseq.sh && cd $WORK_BASE/<SSP>_cluster_scen && bash startguess.sh` for each SSP. SCEN will restart from `<SSP>_cluster_hist/state/` per main.ins state_path absolute + restart=1 + restart_year=2020. SCEN walltime budget can be tighter (1-day) since smoke 9m45s × ~61 = ~10h estimated wall; well within 1-day budget. |
| 5 | **SCP/rsync outputs back to workstation** | After all 10 SCEN+HIST jobs complete, rsync each `<SSP>_cluster_<phase>/output-2026-05-28/` (now ~few-hundred-MB compressed per phase × 5 SSPs × 2 phases ≈ ~few GB total) back to workstation for paper analysis (validation triad axes 1-4). |
| 6 | **Validation triad + paper figures + Methods §2.2 update + Results + Discussion writing** | Per `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1; ~3-5 weeks paper writing on workstation. |
| 7 | **v1.0 GMD paper submission** | Target ~5-9 weeks calendar from session 12 close commit per session-12-prompt §G. |

**Pre-launch checklist for Track 2 production** (per B8_3_evaluation §12):
1. **Re-verify cluster main.ins gridlist + production paths** for each of the 5 SSPs: file_gridlist `(str "gridlist.txt")` placeholder ✓ (Patch 1 from PREP commit); cluster paths for climate/LU/ndep/popdens/simfire/soilmap absolute ✓; ndep histsoc-wetdry-lpjguess fallback for SSP2-4.5+SSP4-6.0 per block 8.1 D5 ✓.
2. **Verify cluster δ-B-variant 62892 library coverage** for all 5 SSPs (5 × 18 GB at `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/`) ✓.
3. **Decide HIST sequencing**: parallel (5 SBATCH jobs concurrently; ~few-day wall) vs serial (queue-friendly; ~1-2 week wall). Daniel's preference per the iterative-checkpoint pattern.
4. **Walltime**: production HIST may need >3-day extension; consider partition with longer walltime (e.g., do submit-to-multiple-partitions canary first) OR checkpoint/restart pattern (save_state mid-spinup).
5. **State files cluster-side disk usage**: per-SSP state/ ~2.3 GB × 5 SSPs = ~11.5 GB total state files; well within /bg capacity.

**Path A (run_coupled.sbatch unified launcher) vs Path B (per-cluster-dir setup_run_tseq.sh)** comparison preserved at `scripts/cluster/README.md` §"Block 8.4 pre-cluster prep — Track 2 T_seq cluster launch"; **Path B (per-dir wrapper) is the validated path at Block 8.3** + remains RECOMMENDED for Track 2 production per matching Daniel's Track-1 muscle memory + cleaner environment override semantics.

---

### 🔧 BLOCK 8.3 CLUSTER SMOKE PREP — Rule #9 datapoint #34 fix landed BEFORE smoke launch (2026-05-28 afternoon session 13 day 1; cluster-native via Cursor Remote-SSH owl01amd)

**Block 8.3 itself remains in progress** (smoke staging next; tag `v0.25.0-cluster-trunk-tseq-smoke-complete` REMAINS RESERVED). At this PREP commit, Rule #9 datapoint #34 surfaced + fixed BEFORE any cluster wall-time burned: tracing the LPJ-GUESS `-parallel` gridlist-resolution mechanism (per `forks/trunk_r13078/command_line_version/main.cpp:69-77` — each rank cd's into `./run<rank+1>` so all relative .ins paths resolve from `runNN/`) revealed that all 10 cluster `main.ins` files authored at block 8.4 Phase H (commit `0b2806e7`) had `file_gridlist` set to absolute path → under MPI every rank would resolve to the same 62538-cell production gridlist independently → 256× duplicated work + finishup-concat broken + state/ misalignment for SCEN restart. Fix matches Daniel's Track-1 wpeat reference convention (`(str "gridlist.txt")` placeholder; setup_run.sh sed-replaces with --gridlist basename per rank for proper gridlist-split-parallelism). Patches landed: (1) Patch 1: 10 cluster main.ins file_gridlist + file_gridlist_cf → `(str "gridlist.txt")` (~50/-20 LOC tracked; +3-line Rule #9 #34 fix annotation per file with `.preR9_34.bak` safety-backup reference); (2) Patch 2: `scripts/cluster/setup_run_tseq_template.sh` + 10 cp's `<SSP>_cluster_<phase>/setup_run_tseq.sh` GRIDLIST env-overridable via `${GRIDLIST:-default}` idiom (~55/-11 LOC tracked); (3) NEW `data/gridlist/gridlist_b830_cluster_smoke_1024cells_seed42.txt` (1024 cells; 50 Phase F anchor cells preserved at lines 1-50 + 974 random seed=42 from production-minus-Phase-F; clean 4 cells/rank for 256-rank MPI; subsumes Block 8.5 cluster MPI pre-flight scope); (4) pre-flight cluster-native fixes (gitignored: state/ subdirs + ./guess symlinks for all 10 dirs); (5) audit-evidence bundle stub at `_chat_artifacts/b8_3_cluster_smoke_2026-05-28/`. **Verified other suspect cluster .ins paths safe** under T_seq mode (`skip_inprocess_engine_run=1` bypasses imogen_intermediary.ins `../../../` paths per imogencfx.cpp:547; main.ins lines 107-111 null FILE_LPJG_*/FILE_*_EMITS workstation paths to ""). **Block 8.3 cluster smoke launch recipe** (revised post-Rule #9 #34 fix; cluster-citizenship optimized for current cluster load — milan partition 9 idle nodes vs genius 75% busy with 2 pending jobs in queue):

```bash
ssh owl  # or use Cursor Remote-SSH-attached terminal
cd /bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm/forks/trunk_r13078_runs/SSP1-2.6_cluster_hist

# Stage smoke run-dir at /bg/data/lpj/work/bampoh-d/...; does NOT sbatch yet
GRIDLIST="$(realpath ../../../data/gridlist/gridlist_b830_cluster_smoke_1024cells_seed42.txt)" \
  NNODES=4 CPU_PER_NODE=64 PARTITION=milan WALLTIME=06:00:00 \
  ./setup_run_tseq.sh

# Inspect staged work-dir BEFORE submitting (verify rank dirs + gridlist split)
ls -la /bg/data/lpj/work/bampoh-d/lpj-guess_imogen_landsymm/forks/trunk_r13078_runs/SSP1-2.6_cluster_hist/run1/
wc -l /bg/data/lpj/work/.../SSP1-2.6_cluster_hist/run1/gridlist_b830_cluster_smoke_1024cells_seed42.txt
# Expected: 4 cells per rank × 256 ranks = 1024 cells total

# Submit + monitor (cluster-citizenship: gentle on partition load)
cd /bg/data/lpj/work/bampoh-d/lpj-guess_imogen_landsymm/forks/trunk_r13078_runs/SSP1-2.6_cluster_hist
bash startguess.sh
squeue -u $USER

# Post-run: 8-acceptance-gate evaluation + diff vs Phase F first-50-cells subset
# (G0 SLURM exits clean; G1 256 ranks all completed; G2 year-range coverage 1900-2020 spinup+hist;
#  G3 output file presence; G4 apples-to-apples diff vs Phase F first 50 cells; G5 physical sensibility;
#  G6 state/ populated for SCEN restart; G7 cluster citizenship clean — no scratch overflow + quota OK)
```

Rule #9 datapoint #34 + concrete Patch 1 + Patch 2 details + verification math (1024/256 = 4 cells/rank exact; setup_run.sh split produces 256 chunks; 0 idle ranks; finishup_lpj_work.sh `--dependency=afterok` chain proceeds cleanly) at `notes/FOLLOWUPS.md` Status dashboard top entry + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 NEW "Block 8.3 cluster smoke PREP" entry + `CHANGELOG.md` [Unreleased] full ~70-LOC narrative entry. Audit-evidence bundle stub + 1024-cell gridlist composition + reproducibility script + 8-acceptance-gate scope at `_chat_artifacts/b8_3_cluster_smoke_2026-05-28/gridlist_b830_cluster_smoke_1024cells_seed42_metadata.txt` (~6.3 KB; gitignored).

**POST-BLOCK-8.3-PREP NEXT**: stage smoke per recipe above (STOP for Daniel review pre-sbatch) → `bash startguess.sh` post-review → 8-acceptance-gate evaluation + diff vs Phase F → block 8.3 close commit + tag `v0.25.0-cluster-trunk-tseq-smoke-complete` + full 9-surface cascade (folds in 4 deferred surfaces: STEP_17c §1.7.8 + PAPER_COMPLETION §4.5.0 [methodology unaffected; just acknowledge cluster smoke landed] + forks/README.md + forks/trunk_r13078_runs/README.md) → block 8.5 cluster MPI pre-flight (likely subsumed by 4 cells/rank smoke) → Track 2 production runs.

---

### ✅ BLOCK 8.2.5 LANDED + BLOCK 8.4 PRE-CLUSTER PREP CONSOLIDATED + POST-BLOCK-8.2.5+8.4 OPERATIONAL ORDERING (2026-05-27 evening session 12 day 2)

**Block 8.2.5 ✅ DONE** at this close commit — switchable-regrid-strategy wiring Phase A-H ALL LANDED. Both pipelines built (5 × 18 GB δ-B Fortran 62892-grid library at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892/` + 5 × 18 GB δ-B-variant trunk-C++ 62892-grid library at `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/`; both 62538-line per climate-var per year-dir post Rule #9 #33 auto-detect-numeric-header fix; both PAPER-READY). **Phase G user choice (~15:30 CEST 2026-05-27) = δ-B-variant** (trunk-C++ engine throughout) for v1.0 GMD paper Track 2 cluster production runs per Methods §2.2 framing locked at block 8.2.4 + double-precision numerics (B62-clean) + warm/wet biome NPP fidelity. **δ-B Fortran-engine pipeline retained as v1+ switchable alternative** per B57/B59 v1+ trajectory. **B57 + B59 ✅ CLOSED**. Full evidence at `_chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_evaluation_2026-05-27.md` (~430 LOC).

**Block 8.4 pre-cluster prep ✅ ALSO DONE** at this close commit (PULLED FORWARD per user direction at session 12 day 2 ~16:23 CEST to consolidate cluster setup into ONE commit + minimize cluster-side firefighting): 10 cluster production run-dirs at `forks/trunk_r13078_runs/<SSP>_cluster_<phase>/` (5 SSPs × hist+scen mirroring user's wpeat hist+ssp{126,…}_wpeat layout) × 14 .ins files each (140 .ins total) with production-grade knobs (`nyear_spinup=500`, `freenyears=100`, `npatch=25`, `save_state`/`restart` per user's wpeat pattern) + cluster paths for climate/LU/ndep/popdens/simfire/soilmap (ndep histsoc-wetdry-lpjguess fallback for SSP2-4.5+SSP4-6.0 per block 8.1 D5); NEW `scripts/cluster/setup_run_tseq_template.sh` (~150 LOC) cp'd to each cluster run-dir as `setup_run_tseq.sh`; `scripts/cluster/README.md` ~100 LOC expansion documenting original Track-1 vs revamped workflow comparison + T_seq launch Path A + Path B + pre-cluster checklist. **Existing `forks/trunk_r13078_runs/<SSP>/` dirs kept as-is** (implicit `_local` role; have block-8.0.3 acceptance + block-8.2.4 trunk-engine library); `<SSP>_cluster_<phase>/` added as siblings (less disruptive than session-11 two-track-restructure proposal).

**POST-BLOCK-8.2.5+8.4 NEXT** (user direction = cluster path; rejected local 3696-grid alternative due to spatial-resolution disclosure concerns + Track-1 apples-to-apples comparison preservation):

| # | Block | Wall | Notes |
|---|---|---|---|
| 1 | **Cluster prep** | ~half-day | git pull cluster mirror at `/bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm/` to v0.24.0 tag (cluster mirror was at HEAD `9561f1e6` per block 8.1 reconnaissance; needs jump to v0.24.0); trunk binary rebuild via cmake+make in `forks/trunk_r13078/build_owl/`; rsync 90 GB δ-B-variant 62892 library workstation→cluster (target: `/bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm/forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/`) + 2.2 GB native 1631 library for provenance; optional `./guess` symlink creation per cluster run-dir per Track-1 muscle memory |
| 2 | **Block 8.3 cluster end-to-end smoke** | ~0.5-1 day | Cluster .ins for small smoke gridlist (override `file_gridlist` in `forks/trunk_r13078_runs/SSP1-2.6_cluster_hist/main.ins` temporarily OR use Path A `--scenario` override) + launch via Path B `./setup_run_tseq.sh` (recommended; mirrors Track-1 mental model) OR Path A `scripts/cluster/run_coupled.sbatch` (unified launcher) + first cluster runtime test on owl genius/256 × ~1-2 hour walltime + SCP outputs back + diff vs local Phase F smoke results; tag candidate `v0.25.0-cluster-trunk-tseq-smoke-complete` |
| 3 | ~~Block 8.4 cluster production-config delta + two-track restructure~~ | ~~~1-1.5 days~~ | **✅ DONE at this close commit (pulled forward into Phase H per user direction)**. Cluster .ins + setup_run_tseq.sh wrappers + workflow docs all consolidated. See §1.1 "Block 8.4 pre-cluster prep artifacts" subsection below for inventory. |
| 4 | **Block 8.5 cluster MPI pre-flight** | ~0.5 day | Verify chosen-pipeline trunk-T_seq scales correctly on genius/256 × 3-day walltime; may be inferable from block 8.3 smoke if smoke uses full 256-rank allocation |
| 5 | **(Optional) Block 8.7 intermediate-cell production smoke** | ~0.5 day | ~1000-cell confidence-builder before full 62538-cell launch; may be subsumed into block 8.3/8.5 depending on smoke gridlist choice |
| 6 | **Track 2 production runs** | ~5-15 h cluster wall | 5 SSPs × 62538 cells × 1900-2100 × strict production (npatch=25, spinup=500, save_state/restart per user's wpeat hist+ssp126 pattern) on owl genius/256 × 3-day walltime; outputs to cluster scratch then SCP back. HIST phase first (5 SSPs; can be parallel via 5 SBATCH jobs or serial for queue-friendliness; each via `cd <SSP>_cluster_hist && ./setup_run_tseq.sh && cd $WORK_BASE/<runname> && bash startguess.sh`); SCEN phase after HIST + state/ populated (each restarts from corresponding `<SSP>_cluster_hist/state/`) |
| 7 | **Track 1 baseline** | already done | user's existing wpeat production runs at `/bg/data/lpj/bampoh-d/landsymm_imogen_runs/integrated-4.1-ins2_landsymm_{hist,ssp*}_wpeat/` (no re-run needed; block 8.6 moot) |
| 8 | **SCP Track 2 outputs back + validation triad + paper figures + Methods §2.2 update + Results + Discussion writing** | ~3-5 weeks paper writing | Axis 1 rebuild vs predecessor (per F-13 scripts) + Axis 2 physical sensibility (vs IPCC AR6 / Friedlingstein 2025 GCB; ecosystem vs Smith2014/Pugh2019/Hickler2012/Saunois2020/Davidson2000/Tian2020) + Axis 3 Track 1 vs Track 2 + Axis 4 framework consistency; Methods §2.2 fold §4.5.0a chosen-pipeline disclosure text from `notes/PAPER_COMPLETION_AND_VALIDATION.md` |
| 9 | **v1.0 GMD submission** | target ~5-9 weeks from this close | — |

**Total active work to start of validation phase: ~3-5 working days cluster prep + ~5-15 hours cluster wall** (Block 8.4 already done; was ~4-6 days pre-consolidation).

#### 1.1 Block 8.4 pre-cluster prep artifacts inventory + Path A vs Path B launch options

**Artifacts landed at this close commit** (per `_chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_evaluation_2026-05-27.md` §7):

- **10 cluster production run-dirs**: `forks/trunk_r13078_runs/<SSP>_cluster_<phase>/` for SSP ∈ {SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5} × phase ∈ {hist, scen}. Each contains 14 .ins files (main + landcover + crop + nitrogen + dispersal + global_cf + global_co2_*.ins + Nfert_v3.ins + soil_cf.ins + 4 other paramfiles) + `setup_run_tseq.sh` (cp from `scripts/cluster/setup_run_tseq_template.sh`) + (for `_hist` dirs) a `state/` subdir for save_state checkpoint.
- **Production knobs** (wpeat-mirror exactly): `nyear_spinup=500`, `freenyears=100`, `npatch=25`, `run_landcover=1`, `run_peatland=1`. HIST: `save_state=1` + `save_years="2020"` + `state_path=<absolute path to state/>`. SCEN: `restart=1` + `restart_year=2020` + `state_path=<same absolute path as HIST's save_path>`.
- **Cluster paths** in main.ins / landcover.ins / crop.ins: climate from `/bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm/forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/<YYYY>/` (chosen δ-B-variant pipeline); LU from `/bg/data/lpj/bampoh-d/landsymm_lu/{hildaplus_hist,plum_scen/ssp<NNN>}/...` per user's wpeat pattern; ndep from `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/n-deposition/{histsoc-ssp<NNN>soc-wetdry-lpjguess,histsoc-wetdry-lpjguess}/...` with histsoc-wetdry-lpjguess fallback for SSP2-4.5+SSP4-6.0 per block 8.1 D5; popdens from `/bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/pop/lpjg-popd/...`; simfire from `/bg/data/lpj/LPJ-GUESS/input/fire/SimfireInput.bin`; soilmap from `/bg/data/lpj/bampoh-d/soil/soilmap_center_interpolated.remapv10_old_62892_gL.dat`.
- **NEW launcher template**: `scripts/cluster/setup_run_tseq_template.sh` (~150 LOC) — T_seq-specific cluster launcher. Auto-detects runname + scenario-dir from `$(pwd)`; hardcodes `--inputmethod imogencfx`; points `--binary` at `forks/trunk_r13078/build_owl/guess`; passes through allocation knobs via env (`NNODES`, `CPU_PER_NODE`, `PARTITION`, `WALLTIME`); invokes the workhorse `scripts/cluster/setup_run.sh` with all the right named-flag args + pre-flight sanity checks (binary exists, main.ins exists, climate libraries exist on cluster).
- **Workflow doc expansion**: `scripts/cluster/README.md` +~100 LOC NEW section "Block 8.4 pre-cluster prep — Track 2 T_seq cluster launch" documenting (a) original Track-1 cluster workflow as verified from user's narrative + script inspection, (b) revamped-vs-original scripts side-by-side comparison table, (c) **Path A + Path B T_seq launch options** (full bash recipes for each + pros/cons + when-to-use guidance), (d) pre-cluster checklist (git pull + binary rebuild + 90 GB rsync + optional `./guess` symlinks).

**Path A — Unified `run_coupled.sbatch` launcher** (alternative; uses rebuild's `--scenario` CLI pattern):

```bash
# From repo root:
sbatch scripts/cluster/run_coupled.sbatch \
  --scenario SSP1-2.6 \
  --coupling-mode tseq \
  --inputmethod imogencfx \
  --binary forks/trunk_r13078/build_owl/guess \
  --nnodes 1 --cpu-per-node 256 --partition genius --walltime 3-00:00:00
# Then check job status with sacct/squeue; outputs land per-rank in scratch, finishup_lpj_work.sh concatenates back
```

**Path B — Per-cluster-dir `setup_run_tseq.sh` wrapper** (RECOMMENDED; mirrors your Track-1 mental model exactly):

```bash
# 1. cd to the target cluster run-dir:
cd forks/trunk_r13078_runs/SSP1-2.6_cluster_hist

# 2. (Optional) override allocation via env:
# NNODES=2 CPU_PER_NODE=128 PARTITION=genius WALLTIME=03:00:00 ./setup_run_tseq.sh

# 3. Invoke per-cluster-dir wrapper (auto-detects runname + scenario-dir + invokes scripts/cluster/setup_run.sh):
./setup_run_tseq.sh

# 4. Output at end: "Work dir at /bg/scratch/$JOBID/.../" — note this path

# 5. cd to work dir + start runs (mirrors your Track-1 manual two-step pattern):
cd $WORK_BASE/SSP1-2.6_cluster_hist  # adjust per setup_run_tseq.sh actual output
bash startguess.sh

# 6. (Wait for SLURM job + finishup_lpj_work.sh; outputs land back in original run-dir + state/ at <SSP>_cluster_hist/state/ for SCEN restart)
```

**When to use which path** (per `scripts/cluster/README.md` §"Block 8.4 pre-cluster prep — Track 2 T_seq cluster launch"):

- **Path B is RECOMMENDED for Track 2 T_seq cluster production runs** — matches your established Track-1 muscle memory precisely (cd to run-dir → ./setup_run.sh → cd to work dir → bash startguess.sh → outputs back in run-dir). The wrapper auto-detects everything; only allocation knobs are env-overridable.
- **Path A is provided for unified-launcher consistency** with rebuild's other operational scripts (the `scripts/run_coupled.sh` workstation orchestrator uses the same CLI pattern). Useful if you ever want to script multi-SSP batched launches from a single command-line.

For full Path A + Path B + workflow comparison + pre-cluster checklist details, see **`scripts/cluster/README.md` §"Block 8.4 pre-cluster prep — Track 2 T_seq cluster launch"** (~100 LOC NEW section landed at this close commit).

---

### 🔧 BLOCK 8.2.5 PARTIAL + POST-CHECKPOINT NEXT (2026-05-26 evening session 11 day 2 mid-block) — **[SUPERSEDED by Block 8.2.5 LANDED entry above; preserved for forensic value per Rule #10 amendment-vs-rewrite corollary]**

**Block 8.2.5 PARTIAL ✅** at this checkpoint commit — Phase A-D + Phase E δ-B LANDED + Phase E δ-B-variant + Phases F/G/H PENDING. Switchable-regrid-strategy wiring substantively in place: δ-B Fortran-engine pipeline FULLY OPERATIONAL (5-SSP × 201-year × ~915 MB Fortran 3698-grid libraries at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output/` + 5-SSP × ~18 GB FastRegrid 62892-grid PAPER-READY libraries at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892/`; ~90 GB total gitignored available for SCP to cluster); tools/FastRegrid/ infrastructure built; per-SSP imogen_settings.txt aligned with intermediary_py (RCMIP/CMIP6 backboned, not legacy IIASA) + CMIP6 MRI-ESM2-0 patterns + B39 init seeds + STANDALONE=.TRUE.; Fortran source-edits per Rule #9 #26 (IYEAR-1→IYEAR matches C++ port semantics + resolves author TODO 30.07.15) + Rule #9 #30 (NEW STANDALONE auto-exit flag); 9 Rule #9 datapoints surfaced + fixed across Phase A-E early (#23-#31).

**Audit-evidence bundle PARTIAL** at `_chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/` (~3 files): B8_2_5_wiring_plan.md (Phase A inspection + plan ~430 LOC; user-approved) + phase_bc_complete.md (Phase B+C close marker). Full B8_2_5_evaluation_2026-05-XX.md awaits Phase H block-close. Large engine + FastRegrid logs gitignored per Rule #9 #29 (regenerable; ~36 MB v5 canary log alone).

**POST-CHECKPOINT NEXT** (block 8.2.5 continuation):

- **Phase E δ-B ✅ DONE** at checkpoint: 5 × 18 GB libraries at `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_62892/` (gitignored; paper-ready for δ-B Track 2 cluster runs).
- **Phase E δ-B-variant launch** (~30-60 min wall; can be 5-way parallel like Phase D + Phase E δ-B): chained FastRegrid NN 1631→3698 + IDW 3698→62892 on trunk-cpp-engine libraries from block 8.2.4 (`forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/`). Output at `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/` (gitignored).
- **Phase F 4-cell smoke side-by-side acceptance** (~30 min wall + ~1h analysis): trunk-T_seq LPJG (build_b824/guess from block 8.2.4) × both δ-B + δ-B-variant pipelines × gridlist_test2.txt 4-cell smoke. Author `forks/trunk_r13078_runs/SSP1-2.6_b825_smoke_delta_b/` + `forks/trunk_r13078_runs/SSP1-2.6_b825_smoke_delta_b_variant/` run-dirs (per the block 8.2.5 wiring plan §1.5). Compare cflux + cmass + anpp + mch4 + ngases ecosystem outputs side-by-side.
- **Phase G user-pick-ONE-pipeline-for-paper** based on Phase F evidence + operational considerations. Likely lean δ-B-variant per the trunk-engine-throughout paper Methods §2.2 framing locked at block 8.2.4 (per `notes/PAPER_COMPLETION_AND_VALIDATION.md` §4.5.0 "trunk_r13078 throughout: engine + LPJG + natural-emission preprocessor"). User makes final call at Phase G AskQuestion.
- **Phase H block-close**: full multi-surface doc cascade (9 surfaces; FOLLOWUPS dashboard + B57 + B59 closure + LEDGER §3 NEW block 8.2.5 FULL entry replacing this PARTIAL section + CHANGELOG full block-close entry + EXECUTION_PLAN row 17c + STEP_17c §1.7.8 + PAPER_COMPLETION §4.5.0 update with chosen-pipeline disclosure + CLUSTER_SETUP §1 POST-BLOCK-8.2.5 ordering + forks/README.md + forks/trunk_r13078_runs/README.md) + audit-evidence bundle close + commit + tag `v0.24.0-switchable-regrid-strategy-complete` + 3-remote push.

After block 8.2.5 FULL close: block 8.3 cluster end-to-end smoke (chosen pipeline's library SCP'd to owl + first cluster runtime test) → block 8.4 cluster production-config delta + two-track directories → blocks 8.5-8.7 → sessions 9-11 Track 2 cluster production runs (5 SSPs × 62538 cells × 1900-2100; ~5-15 hours total cluster wall on genius/256) → sessions 11-12 validation triad + paper figures + writing → v1.0 GMD paper submission (~5-9 weeks calendar from this checkpoint).

### ✅ BLOCK 8.2.4 LANDED + POST-BLOCK-8.2.4 OPERATIONAL ORDERING (2026-05-26 afternoon session 11 day 2 close)

**Block 8.2.4 ✅ DONE** at session 11 day 2 close (THIS commit). Forward-ports the **engine-side slice of LEDGER §1.2 Installment-2** (~1300 LOC TRUNK-RELEVANT) into `forks/trunk_r13078/`, bringing trunk's C++ IMOGEN engine to **functional byte-identity** with `lpjguess/`'s engine for the engine portion. Source-edits in 5 files (`framework/parameters.{h,cpp}` ~30 LOC + `modules/climatemodel.cpp` wholesale cp + `modules/imogencfx.cpp` head+tail reconstruction ~200 LOC non-year_outer + `modules/CMakeLists.txt` 2 LOC) + 2 NEW files (`modules/imogenoutput.{h,cpp}` 821 LOC NEW). Phase G byte-identity verification: **250/250 ✅ md5 matches** (5 SSPs × 5 sentinel years × 10 climate variables) confirms trunk's engine produces functionally IDENTICAL output to lpjguess's. **B61 ✅ CLOSED**. Block 8.2.4 unblocks "trunk_r13078 throughout: engine + LPJG + natural-emission preprocessor" paper methodological framing (per `notes/PAPER_COMPLETION_AND_VALIDATION.md` §4.5.0 LOCKED IN at this block).

**Acceptance**: 8 of 8 Phase D gates ✅ PASS (per `_chat_artifacts/b8_2_4_trunk_engine_forwardport_2026-05-24/B8_2_4_evaluation_2026-05-26.md` §1.4 Phase D scorecard); 4 SSPs successfully completed at Phase E (each 202 year-dirs / 443M / engine exit code 99 = expected B37/B44 overshoot); 250/250 Phase G byte-identity matches.

**Rule #9 datapoints surfaced at block 8.2.4**: #20 missing bootstrap `imogen_lpjg.txt` write in `scripts/run_trunk_engine_only.sh` (engine polling loop stuck with `RUNNOW_EXIST=0`; fix = ~20 LOC bootstrap block mirroring lpjguess's wrapper); #21 trunk-runs `imogen_intermediary.ins` predecessor-era 169 LOC structure vs rebuild's B34(β)-aligned 370 LOC (engine read YEAR1=1871 instead of 1900; fix = wholesale replace all 5 SSPs from rebuild's runs/<SSP>/); #22 relative-path depth mismatch (rebuild's `runs/<SSP>/` is depth 2 from project root; trunk's `forks/trunk_r13078_runs/<SSP>/` is depth 3; `../../` paths don't resolve; fix = `../../` → `../../../` adjustments at DIR_PATT + DIR_CLIM + FILE_NON_CO2_VALS + FILE_GRIDLIST + main_engine_only.ins FILE_NON_CO2_VALS override). **Rule #10 datapoint #24**: scope-vs-Installment-2 honest re-estimate (B61's ~263 LOC under-counted; actual block 8.2.4 ~1300 LOC = ~80% of LEDGER §1.2's ~2900-3100 LOC; residual ~1300 LOC for v1+ Backport Sprint).

**POST-BLOCK-8.2.4 NEXT** (replaces POST-BLOCK-8.2 ordering below since block 8.2.4 has now LANDED the engine slice; blocks 8.2.5/8.3/8.4/8.5/8.6/8.7 remain ACTIVE NEXT):

- **Block 8.2.5 switchable-regrid-strategy wiring** (~1.5-2 d) — Fortran engine settings alignment at `imogen/code/imogen_settings.txt` (REGRID=.TRUE. + NGPOINTS=3698 + B39 init values + intermediary_py adapter input paths) + clone `version_B/FastRegrid/` → `tools/FastRegrid/` + extend `file_types` vector for all 10 climate variables (~5 LOC per block 8.1.5 §3) + δ-B Fortran-engine standalone × 5 SSPs (~5 × ~13 min wall serial OR ~15 min 5-way parallel) + δ-B FastRegrid IDW 3698→62892 + **δ-B-variant chained FastRegrid NN 1631→3698 + IDW 3698→62892 (reading from `forks/trunk_r13078_runs/<SSP>/Common-directory/IMOGEN/output/` — TRUNK'S OWN engine output post-block-8.2.4)** + 4-cell smoke side-by-side acceptance (trunk-T_seq LPJG × both pipelines; compare ecosystem outputs cflux/cmass/anpp/mch4/ngases) + user picks ONE for paper main Track 2 cluster production runs; tag candidate `v0.24.0-switchable-regrid-strategy-complete`
- **Block 8.3 cluster end-to-end smoke test** (~0.5 d) — first actual cluster runtime test on `owl` smoke gridlist; SCP trunk's engine library `forks/trunk_r13078_runs/SSP1-2.6/Common-directory/IMOGEN/output/` → cluster + post-FastRegrid library + run `forks/trunk_r13078/build_owl/guess -input imogencfx main_cluster.ins`; expected ~1-2 hours wall on genius/256; tag candidate `v0.25.0-cluster-trunk-tseq-smoke-complete`
- **Block 8.4 production-config delta authoring + two-track directories** (~1-1.5 d) — author cluster `main_hist.ins` + `main_scen.ins` per-SSP templates; restructure `forks/trunk_r13078_runs/` to `integrated_tseq_<SSP>_wpeat_{cppengine,fortranengine}_{local,cluster}/` (per user's Q2=B selection at session 11 day 1; physical separation via γ-physical-separation policy extended to host-track variants); update `scripts/cluster/setup_run.sh` + `run_coupled.sbatch` for T_seq retargeting; aux input dirs standardized on `/media/bampoh-d/ISIMIP/` where complete; spot-check `/media/bampoh-d/lpjg_input/` for unique gaps
- **Block 8.5 cluster MPI pre-flight** (~0.5 d) — verify chosen-pipeline's trunk-T_seq runs with MPI on `owl` genius/256
- **Block 8.6 Track 1 baseline cluster runs** (~0.5-1 d) — Track 1 (`-input cfx` + ISIMIP3b MRI-ESM2-0 climate) for all 5 SSPs as Axis 4 validation comparison baseline
- **Block 8.7 (optional) intermediate-cell production smoke** (~0.5 d) — confidence-builder before full 62538-cell launch
- **Sessions 9-11 Track 2 cluster production runs** — 5 SSP-RCPs × 62538 cells × 1900-2100 on genius/256; ~5-15 hours total cluster wall
- **Sessions 11-12 validation triad** (Axes 1-4 per `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1) + paper figures + Methods/Results/Discussion writing
- **v1.0 GMD paper submission** — target ~5-9 weeks calendar from this block 8.2.4 close

### ✅ BLOCK 8.2 LANDED + POST-BLOCK-8.2 OPERATIONAL ORDERING (2026-05-23 early morning session 10 day 1 close)

**Block 8.2 ✅ DONE** at session 10 day 1 close (this commit). Spans Phase A (template inspection) + Phase B (production-grade .ins alignment at `runs/SSP1-2.6/main.ins` per user direction; preserves architectural setup for v1+ live-coupling development) + Phase C (paired scaffolding `runs/SSP{2-4.5,3-7.0,4-6.0,5-8.5}/` via cp + sed; SSP-specific ndep fallback for SSP2-4.5 + SSP4-6.0 per block 8.1 D5) + Phase C2 (γ-physical Common-directory separation per user direction; trunk-runs/SSP1-2.6 symlink → physical cp; 4 new SSPs scaffolded) + Phase D (5-SSP C++ engine library production via lpjguess `--engine-only-mode`; ~2.2 GB total) + Phase E (γ-physical cp to trunk-runs side; additional ~2.2 GB; total ~4.4 GB engine libraries) + Phase F (NEW main_engine_only.ins × 5 + scripts/run_trunk_engine_only.sh wrapper as v1+ groundwork; deferred per Rule #10 datapoint #23 self-correction on climatemodel.cpp byte-identity — ~263 LOC divergence between forks; NEW **B61** quantifies as Installment-2 sub-item).

**Acceptance**: 8 of 8 gates ✅ PASS (per `_chat_artifacts/b8_2_engine_libraries_2026-05-22/B8_2_engine_libraries_evaluation_2026-05-22.md` §2). All 5 SSP engine libraries 202 year-dirs / 443 MB / physically sensible CO2 trajectories vs IPCC AR6 / Friedlingstein 2025 GCB. All 5 use intermediary_py adapter outputs (RCMIP/CMIP6-backboned per Option B; legacy IIASA paths COMMENTED OUT).

**γ-physical-separation policy** (per user direction at session 10 day 1; cluster-deployment-readiness + true filesystem-level independence between rebuild + trunk forks; forward-compatible with v1+ tight coupling): each tree's Common-directory is a **physical directory** (no symlinks across trees); cp at Phase E achieves this for all 5 SSPs; same pattern extends to block 8.4 cluster restructure with `_cppengine` / `_fortranengine` per-pipeline variants (each variant gets its own physical Common-directory containing the post-FastRegrid 62,892-grid library).

**Rule #9 datapoints surfaced at block 8.2**: #17 pre-existing block-8.0.2 ssprcp "245" typo at trunk-runs/SSP1-2.6/imogen_intermediary.ins:43 (fixed); #18 SANITY_RANGES upper bound too restrictive for SSP5-8.5 peak ~131 GtCO2/yr (Friedlingstein 2025 GCB; fixed CO2_EFOS_Mt + CO2_total_Mt bounds 100,000 → 200,000 Mt CO2/yr at tools/imogen_inputs_to_lpjg_format.py:117-145); #19 climatemodel.cpp non-byte-identity between forks (NEW B61 filed). **Rule #10 datapoints**: #22 Option A→B→C-hybrid pivot honest framing on C++ REGRID port effort estimate (~150-250 LOC → ~250-400 LOC); #23 climatemodel.cpp byte-identity self-correction (block 8.1.5 §6 was about IMOGENCXX, NOT climatemodel.cpp between forks).

**POST-BLOCK-8.2 NEXT** (replaces POST-BLOCK-8.1.5 ordering below since block 8.2 is now DONE; blocks 8.2.5/8.3/8.4/8.5/8.6/8.7 remain ACTIVE NEXT per `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §0.2 ✅ STRATEGIC RESOLUTION):

- **Block 8.2.5 switchable-regrid-strategy wiring** (~1.5-2 d) — Fortran engine settings alignment at `imogen/code/imogen_settings.txt` (REGRID=.TRUE. + NGPOINTS=3698 + B39 init values + intermediary_py adapter input paths) + clone `version_B/FastRegrid/` → `tools/FastRegrid/` + extend `file_types` vector for all 10 climate variables (~5 LOC per block 8.1.5 §3) + δ-B Fortran-engine standalone × 5 SSPs (~5 × ~13 min wall = ~1 h serial OR ~15 min 5-way parallel) + δ-B FastRegrid IDW 3698→62892 + **δ-B-variant chained FastRegrid NN 1631→3698 + IDW 3698→62892** (Option C-hybrid; no in-engine C++ REGRID port at v1.0 per B59 + B61) + 4-cell smoke side-by-side acceptance (trunk-T_seq LPJG × both pipelines; compare ecosystem outputs cflux/cmass/anpp/mch4/ngases) + user picks ONE for paper main Track 2 cluster production runs; tag candidate `v0.24.0-switchable-regrid-strategy-complete`
- **Block 8.3 cluster end-to-end smoke test** (~0.5 d) — first actual cluster runtime: SCP chosen-pipeline's engine library workstation → cluster (~443 MB SSP1-2.6 minimum; ~5-85 GB if all 5 SSPs SCP'd) + symlink/cp Common-directory + run `forks/trunk_r13078/build_owl/guess -input imogencfx main.ins` on `owl` smoke gridlist; expected ~1-2 hours wall on genius/256; tag candidate `v0.23.0-cluster-trunk-tseq-smoke-complete`
- **Block 8.4 production-config delta authoring** (~1-1.5 d) — author cluster `main_hist.ins` + `main_scen.ins` per-SSP templates mirroring user's canonical wpeat .ins-config pattern; restructure `forks/trunk_r13078_runs/` with `_cppengine` / `_fortranengine` per-pipeline variant suffix per session-10-day-1 naming convention (`integrated_tseq_<scenario>_wpeat_{cppengine,fortranengine}/`); update `scripts/cluster/setup_run.sh` + `run_coupled.sbatch` for T_seq retargeting per block 8.1 D2-D8 reconciliation points
- **Block 8.5 cluster MPI pre-flight** (~0.5 d) — verify chosen pipeline's trunk-T_seq runs with MPI on `owl` genius/256
- **Block 8.6 Track 1 baseline cluster runs** (~0.5-1 d) — Track 1 cluster runs as Axis 4 validation comparison baseline
- **Block 8.7 (optional) intermediate-cell production smoke** (~0.5 d) — confidence-builder before full 62538-cell launch
- **Sessions 9-11 Track 2 cluster production runs** — 5 SSP-RCPs × 62538 cells × 1900-2100 on genius/256; ~5-15 hours total cluster wall (single run-set with chosen pipeline only per Option C-hybrid + block 8.2.5 user choice; the unchosen pipeline's plumbing preserved as v1+ alternative)
- **Sessions 11-12 validation triad** (Axes 1-4 per `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1) + paper figures + Methods/Results/Discussion writing
- **v1.0 GMD paper submission** — target ~5-10 weeks calendar from block 8.2 close

### ✅ BLOCK 8.1.5 LANDED + POST-BLOCK-8.1.5 OPERATIONAL ORDERING (2026-05-22 afternoon session 9 day 3 + session 10 day 1 cascade-gap-fill)

**Block 8.1.5 architectural clarification ✅ DONE** at commit `184a5007` (2026-05-22 ~16:54). Systematic investigation (I-1 to I-6 + C1 + C2; 8 items) triggered by user's "don't we need to run IMOGEN on cluster too?" question revealed: (1) **v1.0 production-IMOGEN engine = C++ port `lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` via `-input imogencfx`** (NOT standalone Fortran as some project docs implied; doc drift filed as B53); (2) **REGRID is DEAD CODE in C++ port** (B3 forensic 2026-05-12; engine always outputs 1631-point native grid); (3) **predecessor architecture = IMOGEN@3698 (Fortran REGRID) + LPJG@62892**; (4) **Fortran standalone engine ALREADY BUILT + OPERATIONAL** (binary May 17 2026; ALLOCATABLE NGPOINTS per STEP_3); (5) **FastRegrid version_B = production-grade** (IDW + Haversine + variable-agnostic; climate-var extension = ~5 LOC). **Switchable-regrid-strategy adopted**: β + δ-A + δ-B as interchangeable alternatives sharing same infrastructure. **6 NEW B-rows filed** (B53-B58). Full evidence: `_chat_artifacts/b8_1_5_architectural_clarification_2026-05-22/B8_1_5_architectural_clarification_findings_2026-05-22.md` (390 LOC; 18 sections).

**Session 10 day 1 cascade-gap-fill + NEW B59 δ-B-variant decision (2026-05-22 evening)**: Block 8.1.5 commit `184a5007` left this §1 operational ordering partially out-of-sync with the new block-plan reality (§1 still jumped block 8.1 → 8.3 without 8.2 + 8.2.5). This sub-banner fills that cascade gap + records the **NEW B59 δ-B-variant decision** per user direction at session 10 day 1 ~18:40-18:56: build BOTH δ-B (Fortran engine) AND δ-B-variant (C++ engine via `climatemodel.cpp`) pipelines at block 8.2.5 acceptance, then choose ONE for v1.0 paper Track 2 cluster production runs based on smoke comparison + operational maneuverability for v1+ live-coupling trajectory.

**POST-BLOCK-8.1.5 + B59 OPERATIONAL ORDERING** (supersedes POST-BLOCK-8.1 NEXT below):

- **Block 8.2 engine library completion** (~0.5 d wall on workstation; ~40 min if 4-way parallelized in terminal tabs) — produce C++ engine libraries (`--engine-only-mode`) for the 4 remaining SSPs (SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5; SSP1-2.6 already done at B44/B47). Outputs 5 × ~443 MB libraries at `runs/<SSP>/Common-directory/IMOGEN/output/<year>/`. These C++ engine libraries feed **δ-B-variant** directly + provide an Option α baseline-set if needed for sensitivity studies.
- **Block 8.2.5 switchable-regrid-strategy wiring** (~1.5-2 d focused work) — BOTH pipelines built + 4-cell smoke acceptance tested:
  - **δ-B (Fortran engine; predecessor architecture)**: align `imogen/code/imogen_settings.txt` (REGRID=.TRUE., NGPOINTS=3698, B39 init values 296.1/875.6/277.4, adapter input paths) + clone `version_B/FastRegrid/` into `tools/FastRegrid/` + extend `FastRegrid.cpp:66 file_types` vector for all 10 climate variables (~5 LOC) + Fortran-engine@3698 smoke + FastRegrid IDW 3698→62,892 smoke + 4-cell end-to-end δ-B acceptance test
  - **δ-B-variant (C++ engine; rebuild-native engine)**: reuse Block 8.2's C++ engine library at 1631 native + run FastRegrid IDW 1631→62,892 (same FastRegrid; different source-grid config) + 4-cell end-to-end δ-B-variant acceptance test on existing SSP1-2.6 1631-grid library
  - **Block 8.2.5 close acceptance comparison**: side-by-side 4-cell ecosystem outputs from δ-B vs δ-B-variant → user picks ONE for paper main Track 2 (likely based on operational preference; unchosen path's plumbing preserved as v1+ alternative)
- **Block 8.3 cluster end-to-end smoke test** (~0.5 d) — first actual cluster runtime test: SCP chosen-option's engine library (raw or post-FastRegrid 62,892) workstation → cluster + run `forks/trunk_r13078/build_owl/guess -input imogencfx main.ins` on `owl` smoke gridlist; expected ~1-2 hours wall on genius/256; tag candidate `v0.23.0-cluster-trunk-tseq-smoke-complete`
- **Block 8.4 production-config delta authoring** (~1-1.5 d) — author cluster `main_hist.ins` + `main_scen.ins` templates per SSP mirroring user's canonical wpeat .ins-config pattern (per `/media/bampoh-d/landsymm_imogen_runs_cluster_mirror_2026-05-21/integrated-4.1-ins2_landsymm_{hist,ssp126,ssp245,ssp370,ssp460,ssp585}_wpeat/main.ins` reference with `cfx → imogencfx` swap + `skip_inprocess_engine_run 1` + add `imogen_intermediary.ins` to extra .ins set + chosen-option's engine-library climate substitution); restructure `forks/trunk_r13078_runs/` to mirror cluster naming convention with engine-tag suffix per **NEW naming convention** = `integrated_tseq_<scenario>_wpeat_fortranengine/` (for δ-B; Fortran-engine pipeline) + `integrated_tseq_<scenario>_wpeat_cppengine/` (for δ-B-variant; C++-engine pipeline; v1+ plumbing reserved even if unchosen for paper); update `scripts/cluster/setup_run.sh` + `run_coupled.sbatch` for T_seq retargeting (per agenda §3.1+3.2+3.4 reconciliation points); adopt the newer site-wide orchestrator improvements (per agenda §3.6); 4-LOC `/bg/home → /bg/data/lpj/work` path-translation case-add in `scripts/cluster/setup_run.sh:113-123` (per agenda §3.4 D4)
- **Block 8.5 cluster MPI pre-flight** (~0.5 d) — verify chosen-option's trunk-T_seq runs with MPI on `owl` genius/256
- **Block 8.6 Track 1 baseline cluster runs** (~0.5-1 d) — Track 1 (`-input cfx` + ISIMIP3b MRI-ESM2-0 climate) for all 5 SSPs as Axis 4 validation comparison baseline
- **Block 8.7 (optional) intermediate-cell production smoke** (~0.5 d) — confidence-builder before full 62538-cell launch
- **Sessions 9-11 Track 2 cluster production runs** — 5 SSP-RCPs × 62538 cells × 1900-2100 on genius/256; ~5-15 hours total cluster wall (estimated; user note "cluster is always in use" → check availability before allocating + use milan/cclake fallback if genius busy); single run-set with chosen δ-B or δ-B-variant
- **Sessions 11-12 validation triad** (Axes 1-4 per `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1) + paper figures + Methods/Results/Discussion writing
- **v1.0 GMD paper submission** — target ~5-10 weeks calendar from block 8.1.5 close (block 8.2.5 adds ~1.5-2 d vs prior α-only ~0 d; still within budget)

**Naming convention summary (NEW; per block 8.4 onward)**:

| Component | δ-B (Fortran engine pipeline) | δ-B-variant (C++ engine pipeline) |
|---|---|---|
| Engine source | `imogen/code/imogen_lpjg.f` | `lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE()` |
| Engine binary path | `imogen/code/imogen_lpjg` | `lpjguess/build/guess --engine-only-mode` (via `scripts/run_coupled.sh`) |
| Engine native output grid | 3698 (REGRID=.TRUE.; NGPOINTS=3698) | 1631 (REGRID is dead code; always native) |
| Engine library directory | `runs/<SSP>/Common-directory-fortranengine/IMOGEN/output_3698/<year>/` (raw) + `output_62892/<year>/` (post-FastRegrid) | `runs/<SSP>/Common-directory/IMOGEN/output/<year>/` (existing 1631 native) + `runs/<SSP>/Common-directory/IMOGEN/output_62892_cppengine/<year>/` (post-FastRegrid) |
| Trunk-T_seq run directory (cluster) | `forks/trunk_r13078_runs/integrated_tseq_<scenario>_wpeat_fortranengine/` | `forks/trunk_r13078_runs/integrated_tseq_<scenario>_wpeat_cppengine/` |
| FastRegrid invocation | 3698 → 62,892 IDW (Haversine; power=2; max_points=5; radius=100 km) | 1631 → 62,892 IDW (same params; different source grid) |
| Climate resolution at LPJG | 3698 source IDW-interpolated to 62,892 | 1631 source IDW-interpolated to 62,892 |
| Predecessor parity (architectural) | ✅ Match | ❌ Different engine source grid (1631 vs predecessor's 3698) |
| C++/Fortran engine cross-validation | Reference | Variant — useful for v1+ live-coupling (which uses C++ engine) |

Block 8.2.5 acceptance close decides which pipeline becomes Track 2 paper production. Both stay in repo as switchable infrastructure for v1+ post-paper development.

### ✅ BLOCK 8.1 LANDED status update (2026-05-21 evening session 9 day 2 close)

**Block 8.1 cluster reconnaissance under T_seq retargeting ✅ FULLY COMPLETE** at this close. All 5 acceptance gates G0-G4 PASS via 7 rounds of iterative SSH paste-back + local mirror rsync of `/bg/data/lpj/bampoh-d/landsymm_imogen_runs/` to `/media/bampoh-d/landsymm_imogen_runs_cluster_mirror_2026-05-21/` (121 MB; canonical reference for meticulous direct-file inspection per Rule #11 + #13).

**Headline outcome**: KIT IMK-IFU `owl` ready for T_seq Track 2 production runs at canonical resource allocation **`genius × 2 nodes × 128 CPUs/node = 256 ranks × 3-day walltime`** (matches user's recent wpeat Track 1 production setup_run.sh + sacct PNV_unmanage_guess 256 NCPUs 1h07m wall = ~2.5× faster than legacy cclake/160 baseline). Both fork binaries built cleanly on cluster (`forks/trunk_r13078/build_owl/guess` 2,594,392 bytes sha1 `40d36db6…` + `lpjguess/build_owl/guess` 2,639,744 bytes sha1 `4da4462a…`) without B48 `-lcurl` workaround (Spack-managed dep chain is Ubuntu-immune). Project mirror cloned at `/bg/data/lpj/bampoh-d/lpj-guess_imogen_landsymm/` (63 MB; HEAD matches workstation `9561f1e6…`; tag `v0.22.0-tseq-installment-1-complete` present). All 5 cluster input categories verified present + ndep fallback strategy for SSP2-4.5 + SSP4-6.0 already encoded in user's wpeat runs (use `histsoc-wetdry-lpjguess/` 1850-2015 historical fallback; established by user 2026-03-14/15).

**8 substantive discoveries** (D1-D8 per Rule #9 datapoint #17; full details at `_chat_artifacts/b8_1_cluster_reconnaissance_2026-05-21/B81_AGENDA_2026-05-21.md` §2): D1 B48-immunity + D2 genius/256 canonical allocation + D3 site-wide newer orchestrator at `/bg/data/lpj/scripts/` + D4 HOME=/bg/home/ path-translation case-add + D5 ndep fallback pre-encoded + D6 Rule #10 self-correction on canonical reference dir framing + D7 cross-SSP _wpeat parallelism perfect + **D8 NEW v1.1+ trajectory** = IMOGENCXX C++ legacy backport from version_A/B as switchable-alternative to rebuild's improved Fortran IMOGEN (filed as **B52 NEW** at `notes/FOLLOWUPS.md` this commit).

**Acceptance gate scorecard**:

| Gate | Verdict | Evidence |
|---|---|---|
| G0 SSH + bash env | ✅ PASS | AlmaLinux 9 + Spack 0.19.0 + 7 auto-loaded modules in user's `.bash_profile` |
| G1 cluster discovery | ✅ PASS | 11 partitions; canonical genius/256 + milan/cclake alternatives; site-wide newer orchestrator |
| G2 trunk fork build | ✅ PASS | 2,594,392 bytes sha1 40d36db6...; B48-immune |
| G3 lpjguess fork build | ✅ PASS | 2,639,744 bytes sha1 4da4462a...; Step A migration optionality |
| G4 cluster input paths + ndep strategy | ✅ PASS | 5/5 categories present; ndep fallback pre-encoded |

**Block 8.1 close commit artifacts** (per `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 NEW "Block 8.1 LANDED" entry; per `_chat_artifacts/b8_1_cluster_reconnaissance_2026-05-21/B81_cluster_reconnaissance_evaluation_2026-05-21.md` 5-gate scorecard with concrete-artifact citations per Rule #10): 1 source-edit (`scripts/cluster/env_owl.sh` canonical module-load population; ~20 LOC; TRUNK-IRRELEVANT-by-novelty) + 7 doc updates + 1 sibling Part 13 of session5_post_b19 handoff + comprehensive audit-evidence bundle (10 files; 2328 LOC; 162 KB).

**POST-BLOCK-8.1 NEXT** (replaces §1.2 8-block plan ordering below since blocks 8.0 + 8.1 are now DONE; blocks 8.2/8.3/8.4/8.5/8.6/8.7 are renumbered + retargeted under T_seq per `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §0.2 ✅ STRATEGIC RESOLUTION):

- **Block 8.3 cluster end-to-end smoke test** (~0.5 d) — first actual cluster runtime: SCP engine library workstation → cluster (~443 MB SSP1-2.6) + symlink Common-directory + run `forks/trunk_r13078/build_owl/guess -input imogencfx main.ins` on `owl` smoke gridlist; expected ~1-2 hours wall on genius/256 per cluster runtime extrapolation; tag candidate `v0.23.0-cluster-trunk-tseq-smoke-complete`
- **Block 8.4 production-config delta authoring** (~1-1.5 d) — author cluster `main_hist.ins` + `main_scen.ins` templates per SSP mirroring user's canonical wpeat .ins-config pattern (per `/media/bampoh-d/landsymm_imogen_runs_cluster_mirror_2026-05-21/integrated-4.1-ins2_landsymm_{hist,ssp126,ssp245,ssp370,ssp460,ssp585}_wpeat/main.ins` reference with `cfx → imogencfx` swap + `skip_inprocess_engine_run 1` + add `imogen_intermediary.ins` to extra .ins set + engine-library climate substitution); restructure `forks/trunk_r13078_runs/` to mirror cluster naming convention (hist + 5 scenarios × _wpeat); update `scripts/cluster/setup_run.sh` + `run_coupled.sbatch` for T_seq retargeting (per agenda §3.1+3.2+3.4 reconciliation points); adopt the newer site-wide orchestrator improvements (per agenda §3.6); 4-LOC `/bg/home → /bg/data/lpj/work` path-translation case-add in `scripts/cluster/setup_run.sh:113-123` (per agenda §3.4 D4)
- **Block 8.5 cluster MPI pre-flight** (~0.5 d) — verify trunk-T_seq runs with MPI on `owl` genius/256
- **Block 8.6 Track 1 baseline cluster runs** (~0.5-1 d) — Track 1 (`-input cfx` + ISIMIP3b MRI-ESM2-0 climate) for all 5 SSPs as Axis 4 validation comparison baseline
- **Block 8.7 (optional) intermediate-cell production smoke** (~0.5 d) — confidence-builder before full 62538-cell launch
- **Sessions 9-11 Track 2 cluster production runs** — 5 SSP-RCPs × 62538 cells × 1900-2100 on genius/256; ~5-15 hours total cluster wall (estimated; user note "cluster is always in use" → check availability before allocating + use milan/cclake fallback if genius busy)
- **Sessions 11-12 validation triad** (Axes 1-4 per `notes/PAPER_COMPLETION_AND_VALIDATION.md` §1) + paper figures + Methods/Results/Discussion writing
- **v1.0 GMD paper submission** — target ~6-11 weeks calendar from block 8.1 close

**Below**: §1 8-block original ordering preserved for forensic continuity per Rule #10 amendment-vs-rewrite corollary (the original session-7-close framing where blocks 8.1 was preliminary cluster reconnaissance + 8.2-8.7 were the in-process integration options; T_seq retargeting at session 8.0 C5 changed the meaning of blocks 8.2-8.7 to T_seq-specific; this block 8.1 close confirms all reconnaissance work is done).

---

### 1.1 Headline strategy — local-first with cluster reconnaissance in parallel

Reasoning (carried forward from session-7 close analysis):

1. The current smoke-test setup (`runs/SSP1-2.6/main.ins`) has validated only a 4-cell × 2-year window. **Roughly 7 production knobs are unverified** (§2 below). Each is a potential failure mode (missing file, wrong path, schema mismatch, scaling bug). Catching these locally on a ~100-cell reduced gridlist takes minutes-to-hours per iteration; catching them on the cluster takes queue wait + node debugging + SCP cycles per iteration.
2. `notes/PRODUCTION_RUN_CONFIG.md` §6.1 readiness checklist explicitly endorses this ordering: "Test run on local workstation with reduced gridlist (e.g., 100 cells; verify full pipeline works) **before** cluster scaling".
3. However, **one cluster-side task has no local equivalent** and should happen ASAP: the `env_owl.sh` module-load refinement (per `scripts/cluster/README.md` lines 124-130). A 5-minute SSH `module avail` + report-back gives me the actual cluster module versions so I can commit refined values.

So the operational plan parallelises cluster reconnaissance (which is gated only on your SSH access) with local production-config setup (which is gated only on local edit work).

### 1.2 Concrete session-8 block ordering (proposal; user can adjust)

| Block | Effort | Mode | What |
|---|---|---|---|
| **8.0** | ~1-2 h | source-diff + decision | **STRATEGIC DECISION** per §0.2: Option R (rebuild repo for Track 2; current default) vs Option T (trunk_r13078 minimally updated for Track 2; cleaner paper consistency). Execute C0-C5 verification checklist; user decides. **All subsequent blocks depend on this outcome** — they describe Option R below; under Option T they retarget to `version_{A,B}/.../trunk_r13078/` + `lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_*` + legacy `owl_hpc_cluster_scripts/scripts/` |
| 8.1 — Cluster reconnaissance | ~30-60 min | SSH + paste-back | You SSH to `owl`; `module avail` for the module families; `sinfo` for partition names + max walltime + per-partition node specs; `sacct` for your recent LPJG run examples + their resource footprint; `df -h /bg/data/lpj/` for storage; we refine `scripts/cluster/env_owl.sh` + commit |
| 8.2 — Your LPJG-on-owl workflow walkthrough | ~30 min | screen-share narrative + paste-back | You show me how you submit + monitor + post-process a typical LPJG cluster run; I take notes on conventions; this informs how I should adapt `scripts/cluster/run_coupled.sbatch` to fit your familiar workflow + your `imogen` cluster-orchestration intuitions |
| 8.3 — `-input imogencfx` cluster-feasibility investigation | ~30-60 min | source-read + design-doc | Investigate the open question in §4 below (does `-input imogen` handle the production auxiliaries? does cluster + `-input imogencfx` require the B44 sidecar mechanism per rank?); recommend concrete cluster sbatch wrapper update plan; record findings here |
| 8.4 — Local production-config delta authoring | ~2-3 h | local edits | Draft `runs/SSP1-2.6/main.ins` production-config update + `landcover.ins`/`crop.ins` updated `_peatland` LU + add popdens + 4-NetCDF wet/dry NHx+NOy ndep + SimFire references; pause for your review before commit |
| 8.5 — Local 100-cell production test run | ~1-2 h | local execute | Run the production-config locally on a reduced 100-cell gridlist with `--engine-only-mode` + `--production` flags; capture full-stack outcome; ANY surfaced bugs get fixed locally before cluster scaling; bundle audit evidence per Rule #10 |
| 8.6 — If 8.5 passes — local Track-1 paired 100-cell sample run | ~1-2 h | local execute | Sanity-check: ALSO run the 100-cell config in Track 1 mode (`-input cfx`) so we have local-paired Track 1 vs Track 2 100-cell outputs; useful for the validation-triad comparison-script porting work (per `notes/PAPER_COMPLETION_AND_VALIDATION.md`) |
| 8.7 — Cluster sbatch wrapper update | ~1-2 h | source-edit + commit | Update `scripts/cluster/run_coupled.sbatch` per the §4 decision: bring it up to speed with B44 + the 1900-2100 productive-year fix; remove outdated 32-year-deadlock warnings; add the path-iv sidecar mechanism appropriately for cluster (whether per-rank or via Option α local-engine + cluster-loose adaptation per the §4 decision) |
| 8.8 — Cluster setup decision point | ~discussion | discussion | Based on 8.1-8.7 outcomes, decide cluster scaling strategy + commit; pause for your approval before SCP/cluster scaling |

This is **not a rigid plan** — adjust as discoveries land. The ordering minimises risk by surfacing all production-config bugs locally (cheap) before cluster scaling (expensive).

### 1.3 Sessions 9+ (post-session-8 outlook; revisit at session-8 close)

| Session | Block | What |
|---|---|---|
| 9 | Cluster setup + SCP + first cluster smoke run | Cluster MPI build (`make_guess.sh --mpi`); SCP production-config from local; first cluster smoke run (4-cell or 100-cell) to validate the cluster path works end-to-end |
| 9-10 | Cluster scaling + first production-IMOGEN cluster run | One SSP scenario (probably SSP1-2.6 first as the canonical reference scenario) full 62538-cell 1900-2100 production-IMOGEN run on cluster; debug + iterate |
| 10-11 | Remaining 4 SSP scenarios | SSP2-4.5 + SSP3-7.0 + SSP4-6.0 + SSP5-8.5 production runs on cluster; iterate based on session-9-10 learnings |
| 11-12 | Validation triad + paper figures | Run the 4-axis validation triad per `notes/PAPER_COMPLETION_AND_VALIDATION.md`; generate paper figures |
| 12-15+ | Paper amendments + writing | Draft results + discussion + conclusion sections; iterate; per `notes/PAPER_COMPLETION_AND_VALIDATION.md` |

Total estimated calendar time from session 8 to v1.0 paper submission: **~6-10 weeks** (matches `notes/PRODUCTION_RUN_CONFIG.md` §6.2 estimate).

---

## 2. Production-config knobs UNVERIFIED at smoke (the catch-locally-first list)

These are the production parameters the smoke configuration does NOT exercise. Each is a potential local-test failure mode worth catching before cluster scaling.

| # | Knob | Smoke | Production | Risk |
|---|---|---|---|---|
| 1 | `firemodel` + SimFire binary | `"NOFIRE"` + empty `file_simfire` | `"BLAZE"` + `SimfireInput.bin` | Binary path or file-format failure if simfire binary differs between local + cluster |
| 2 | `npatch` | 1 | 25 | Memory scaling; per-patch initialization may surface bugs |
| 3 | `nyear_spinup` | 1 | 500 | Long spinup may surface state-initialization bugs or run-time issues |
| 4 | N-deposition | pre-industrial-constant 2 kgN/ha/yr fallback (empty `file_ndep` + no 4 NHx/NOy NetCDFs) | 4 wet/dry NHx + NOy NetCDFs (`ndep_drynhx_*.nc4`, `ndep_wetnhx_*.nc4`, `ndep_drynoy_*.nc4`, `ndep_wetnoy_*.nc4`) | NetCDF file paths, schema mismatches, temporal coverage gaps |
| 5 | LU forcing | legacy `version_A/.../LU_SSP1_RCP26_1901_2100_final.txt` (4-cell coverage) | `LU.remapv10_old_62892_gL_peatland.txt` (hist) + `landcover_peatland.txt` (SSP) at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/output_hildaplus_remap_10b_3/remaps_v10_old_62892_gL/` | Schema differences between legacy + `_peatland` variants; gridlist alignment |
| 6 | Population density | not set (firemodel=NOFIRE) | Population NetCDF for SimFire ignition at `/media/bampoh-d/lpjg_input/input/pop_dens/...` | NetCDF format + temporal coverage |
| 7 | State save/restart | not used (smoke) | Historical run saves at year 2020; SSP runs restart from the historical state | New code path; per-scenario state-handoff workflow |

This list is **the local-test acceptance checklist for block 8.5**. The 100-cell test run should exercise all 7 knobs simultaneously; bundle the outcome per Rule #10.

---

## 3. Cluster reconnaissance — concrete SSH paste-back tasks for session 8.1

### 3.1 env_owl.sh module-load refinement

Per `scripts/cluster/README.md` lines 124-130, the current `env_owl.sh` placeholders are:

```bash
module load gcc/14
module load cmake/3.29
module load netcdf-c/4.9
module load netcdf-fortran/4.6
module load openmpi/5.0
```

These are educated guesses from the prior chat handoff Part 4 §17. The actual `owl` cluster has IT-managed module names + versions that may differ. SSH paste-back needed:

```bash
# On owl login node:
ssh <user>@owl-login.<cluster-domain>
module avail gcc 2>&1 | head -30
module avail cmake 2>&1 | head -10
module avail netcdf 2>&1 | head -30
module avail openmpi 2>&1 | head -20
module avail mpi 2>&1 | head -20      # in case openmpi isn't the only MPI flavour
module avail hdf5 2>&1 | head -20     # NetCDF depends on HDF5
which gcc cmake mpicc mpicxx 2>&1     # baseline what's on PATH without explicit module loads
```

Copy the output back to chat; we refine `scripts/cluster/env_owl.sh` with the actual module names + versions; commit.

### 3.2 Partition + node + queue reconnaissance

```bash
# Partition + node specs:
sinfo -o "%P %l %a %D %c %m %f"     # partitions; max walltime; state; nodes; CPUs; mem; features
sinfo -p <partition_name> -N -o "%N %c %m %T %f"   # per-node specs in a specific partition

# Queue policies:
sacctmgr show qos
scontrol show partition <partition_name>

# Your typical run profile (for understanding scaling expectations):
sacct -u $USER --starttime=2025-01-01 --format=JobID,JobName,Partition,NCPUS,Elapsed,State -X | head -30
```

### 3.3 Storage paths reconnaissance

```bash
# Storage availability:
df -h /bg/data/lpj/
df -h /scratch/
df -h /tmp
df -h $HOME

# Existing user data:
ls -la /bg/data/lpj/$USER/ 2>/dev/null | head -20
ls -la /bg/data/lpj/$USER/landsymm_lu/ 2>/dev/null | head -10    # per PRODUCTION_RUN_CONFIG.md §3.2

# Permissions on shared inputs (existing LPJ-GUESS inputs the rebuild can reuse):
ls -la /bg/data/lpj/LPJ-GUESS/input/fire/SimfireInput.bin 2>/dev/null
ls -la /bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/pop/ 2>/dev/null
ls -la /bg/data/lpj/LPJ-GUESS/input/isimip/isimip3/n-deposition/ 2>/dev/null
```

The cluster path layouts in `notes/PRODUCTION_RUN_CONFIG.md` §3.2 are based on existing assumptions; this reconnaissance verifies them.

### 3.4 Your LPJG-on-owl workflow walkthrough (block 8.2)

You mentioned you have substantial LPJ-GUESS experience on owl (but NOT IMOGEN). Walk me through a typical LPJG run end-to-end:

1. Where do you stage `.ins` files + input data?
2. How do you split gridlists across ranks (manual? script?)
3. What's your typical sbatch template (resource request, walltime, modules)?
4. How do you monitor jobs (`squeue`, `tail -f`, custom scripts)?
5. How do you post-process (concatenate per-rank outputs, gzip, archive)?
6. Where do you store results?
7. Any cluster-specific gotchas / lessons-learned worth noting?

This walkthrough informs whether `scripts/cluster/run_coupled.sbatch` (as currently written) actually fits your operational pattern, or needs reshaping.

---

## 4. THE KEY ARCHITECTURAL QUESTION — cluster + imogencfx vs imogen (session 8.3)

### 4.1 User constraint (clarified at session-7 close, 2026-05-19 evening)

**Production cluster runs MUST use `-input imogencfx` (not `-input imogen`)** because they require the cfx-style auxiliaries:
- SimFire BLAZE binary (`SimfireInput.bin`)
- Population density NetCDF (for SimFire ignition)
- 4 wet/dry NHx + NOy ndep NetCDFs (modern N-deposition forcing)
- Updated `_peatland` LU forcing
- Soil + gridlist auxiliaries

The user's stated uncertainty: "I do not know if `-input imogen` can handle [these auxiliaries] the way `imogencfx` can".

### 4.2 What I (preliminarily) know (NOT yet verified at source level)

| Input module | Source file | What it reads (preliminary) |
|---|---|---|
| `cf` | `cfinput.cpp` | Older CF-NetCDF climate reader (deprecated) |
| `cfx` | `cfxinput.cpp` | Extended CF-NetCDF: ISIMIP3b climate + CO2 + popdens + SimFire + 4-NetCDF ndep + LU |
| `imogen` | `imogen_input.cpp` | LPJG reads pre-baked IMOGEN climate from disk; presumed climate-only (NEEDS VERIFICATION at source) |
| **`imogencfx`** | **`imogencfx.cpp`** | IMOGEN-engine climate + CO2 + cfx-style auxiliaries (popdens, SimFire, ndep, LU). **The integrated path** |

**Open investigation for session 8.3**: read `lpjguess/modules/imogen_input.cpp` to verify whether `-input imogen` handles the cfx-style auxiliaries (popdens, SimFire, ndep, LU) or is climate-only. If climate-only, then `imogen` is unsuitable for production runs, and the cluster path MUST use `imogencfx`.

### 4.3 Architectural options for cluster + production-runs (paths to investigate)

Given the user's `imogencfx` constraint, the architectural options for cluster integration become:

| Option | Mechanism | Pros | Cons | Source-edit effort |
|---|---|---|---|---|
| **Option α — local-engine + cluster-imogen-loose** | (1) Run IMOGEN engine ONCE locally via B44 `--engine-only-mode` per SSP; produces 1900-2100 climate library at `runs/<SSP>/Common-directory/IMOGEN/output/<year>/*.dat`; (2) SCP that library to cluster; (3) Run LPJG on cluster with `-input imogen` reading the pre-baked library | Reuses existing cluster + loose pattern; engine runs serially (already validated by B44) | **PROBABLY UNSUITABLE for v1.0 production** because `-input imogen` may NOT carry SimFire BLAZE + popdens + ndep + LU (NEEDS VERIFICATION in §4.2 source-read); SCP ~10 GB of climate library; engine + LPJG on different hardware | 0 source edits if `-input imogen` handles auxiliaries; otherwise N/A |
| **Option α′ — local-engine + cluster-imogencfx with skip-engine flag** | (1) Run IMOGEN engine ONCE locally via B44 `--engine-only-mode` per SSP; (2) SCP the climate library to cluster; (3) Run LPJG on cluster with `-input imogencfx` BUT with a new "skip-in-process-engine-run" flag that makes the imogencfx reader pull the pre-baked library from disk instead of running the engine in-process | Combines B44 local-engine validation with cfx-style auxiliaries cluster reading; cluster runs are embarrassingly parallel (engine already done); SCP ~10 GB | Requires a new flag in `imogencfx.cpp` to skip the in-process engine run (small source-edit; possibly TRUNK-RELEVANT); the imogencfx reader needs to know how to load pre-baked engine output from disk instead of from in-process engine memory | ~50-100 LOC source-edit in `imogencfx.cpp` + ins parameter handling |
| **Option β — cluster-engine + cluster-imogencfx via per-rank sidecar** | All ranks run their own engine instance + their own path-iv sidecar (B44-style); each rank produces identical climate (wasteful); cfx-style auxiliaries handled natively by each rank's imogencfx | No SCP needed; everything happens on cluster; reuses existing imogencfx code path with minimal cluster sbatch wrapper changes | N-fold engine compute waste (each rank re-runs the engine); MPI orchestration of N sidecars (~potentially racy); the sbatch wrapper needs B44 sidecar integration per rank | ~30-50 LOC bash in `scripts/cluster/run_coupled.sbatch` + `mpi_run_guess.sh` to spawn per-rank sidecars + clean up |
| **Option β′ — cluster-engine on rank-0 + cluster-imogencfx-skip on ranks 1..N-1** | Rank-0 runs the engine via path-iv sidecar; produces climate library at a shared cluster path (`/scratch/$JOBID/IMOGEN_OUTPUT/`); all other ranks wait via MPI_Barrier; then all ranks run `-input imogencfx` with the skip-engine flag from §α′ pointing to the shared library | No SCP; engine runs once; cluster ranks reuse the library; closer to Option α′ but no local + SCP step | Requires BOTH the new skip-engine flag in imogencfx.cpp (per Option α′) AND MPI orchestration in the cluster sbatch wrapper (rank-0 engine + barrier + all-rank LPJG); more complex than either α′ or β | ~50-100 LOC source-edit in `imogencfx.cpp` + ~50-80 LOC bash in cluster sbatch + `mpi_run_guess.sh` |
| **Option γ (post-v1.0 F-12 Option C)** | Per-year-outer / per-gridcell-inner framework loop with MPI_Barrier at year boundary; the "real" tight-coupling cluster solution | The architecturally correct solution; closes the F-10 + F-12 loop properly | Substantial multi-week LPJG-framework refactor; explicitly deferred to v1.1+ per `notes/STEP_17c.md` + B43 decision | ~1000+ LOC engine-framework rewrite; PER-FORK in entirety |

### 4.4 Recommendation framing (to discuss + decide at session 8.3)

**My preliminary lean** (subject to source-read verification in 8.3):

- **If `-input imogen` handles auxiliaries** (unlikely but possible): Option α is the cleanest v1.0 path — minimal source edit, reuses existing cluster + loose pattern, engine runs once locally.
- **If `-input imogen` is climate-only** (more likely): **Option β′** is the v1.0 paper-publication recommendation — the engine runs ONCE on rank-0 with B44 sidecar; ranks 1..N-1 wait + then all ranks run `-input imogencfx` with a small skip-engine flag pointing to the shared library. Tradeoffs: ~100-180 LOC effort but avoids both SCP (cluster-only workflow) and engine-compute waste (Option β's per-rank duplicate runs).
- **Option β** (per-rank engine + per-rank sidecar) is the **fallback** if Option β′ proves architecturally too complex — wasteful but simple.

The session 8.3 source-read verifies the `imogen_input.cpp` capability + makes Option α vs β/β′ a concrete decision. The session 8.7 cluster sbatch wrapper update implements the chosen option.

### 4.5 Self-correction on the B44 close (Rule #10)

In `notes/B44.md` §4 I claimed "the cluster sbatch wrapper needs a 1-line `--engine-only-mode` passthrough" at 17c.1 setup. This was **over-simplified** — the user's `imogencfx` constraint surfaced at session-7 close makes the cluster integration substantially more nuanced (per §4.3 options above). The B44 productisation is sound LOCAL launcher work; the cluster integration is a separate session-8 design decision (options α/α′/β/β′) that may require additional source-edit work in `imogencfx.cpp` (TRUNK-RELEVANT if option α′ or β′ chosen).

**Action item for session 8 start**: update `notes/B44.md` §4 + the FOLLOWUPS dashboard B44 entry to reflect this more accurate cluster-integration framing. NOT urgent (B44 itself is closed correctly; this is a clarification of the post-B44 cluster integration story).

---

## 5. B44 + cluster integration — bringing `run_coupled.sbatch` up to speed

### 5.1 Current cluster sbatch wrapper state (pre-session-8)

`scripts/cluster/run_coupled.sbatch` lines 197-222 (verified at session-7 close):

| Coupling mode | Current behavior | Post-B44 + post-§4 decision behavior |
|---|---|---|
| `tight` | **REFUSES** to proceed (F-12 Option C blocker; lines 197-216) | UNCHANGED in v1.0 (F-12 still deferred to v1.1+ per B43) |
| `prescribed` | **WARNS** "engine will produce ~32 years per rank then deadlock" + recommends loose (lines 218-222) | **OUTDATED**; must be updated post-§4 decision to reflect that the 32-year ceiling is solved by the path-iv sidecar (B37/B44) + chosen integration mechanism |
| `loose` | DEFAULT; works end-to-end on cluster per existing pattern | LIKELY UNSUITABLE for v1.0 production due to `imogen`-vs-`imogencfx` auxiliary handling (per §4) |

### 5.2 Required cluster sbatch wrapper updates (post-§4 decision)

Once §4.3 option chosen, the sbatch wrapper needs:

1. **Remove outdated 32-year-deadlock warnings** (the path-iv sidecar mechanism solves this; B37 + B44 established the fix LOCALLY)
2. **Add `--engine-only-mode` flag handling** (if Option β or β′ chosen)
3. **Add `--skip-inprocess-engine-run` flag handling** (if Option α′ or β′ chosen; requires accompanying `imogencfx.cpp` source-edit)
4. **Add per-rank sidecar orchestration** (if Option β chosen)
5. **Add MPI rank-0-engine + barrier + all-rank-LPJG orchestration** (if Option β′ chosen)
6. **Update the architecture overview in `scripts/cluster/README.md`** to reflect the new flow (post-§4 decision; B44 + chosen option)
7. **Update v1.0 status section in `scripts/cluster/README.md`** to reflect the productive-year-ceiling fix (no longer "blocked at ~32 years per rank")

Estimated total effort: ~3-6 h source-edit + cascade depending on chosen option. Bundle with session 8.7.

### 5.3 Cross-reference to local launcher improvements

For maintainer-discoverability, the cluster sbatch wrapper's header doc-comment should explicitly cross-reference:

- `scripts/run_coupled.sh` — local launcher analogue
- `notes/B37.md` §5 — path-iv mechanism narrative
- `notes/B44.md` — local launcher `--engine-only-mode` flag (productisation of path-iv)
- THIS document `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` §4 — cluster integration option choice + rationale

---

## 6. Local production-config delta authoring (session 8.4)

Per `notes/PRODUCTION_RUN_CONFIG.md` §2 (the canonical reference), session 8.4 work:

### 6.1 `runs/SSP1-2.6/main.ins` updates (smoke → production)

| Parameter | Current (smoke) | Target (production) | Notes |
|---|---|---|---|
| `firsthistyear` | 1900 | 1900 | (unchanged historical start) |
| `lasthistyear` | 1901 | 2020 | full historical horizon |
| `firstoutyear` | 1900 | 1900 | (unchanged) |
| `lastoutyear` | 1901 | 2020 | full historical horizon for output |
| `file_gridlist` | `data/gridlist/gridlist_test2.txt` (4 cells) | **For 100-cell local test**: create `gridlist_test_100cells.txt` (subset of full production gridlist); **For cluster scale**: `gridlist_in_62892_and_climate.txt` (62538 valid cells) |
| `nyear_spinup` | 1 (B19 ADDENDUM smoke) | 500 | LPJG production default |
| `freenyears` | (smoke default) | 100 | per `integrated-4.1-ins2_landsymm_hist:41` |
| `firemodel` | `"NOFIRE"` | `"BLAZE"` | requires SimFire binary file path below |
| `npatch` | 1 | 25 | LPJG production default |
| `file_simfire` | `""` | `/media/bampoh-d/lpjg_input/input/fire/SimfireInput.bin` | LOCAL path; cluster path is `/bg/data/lpj/LPJ-GUESS/input/fire/SimfireInput.bin` (per PRODUCTION_RUN_CONFIG.md §3.2) |
| `file_popdens` | (not set) | `/media/bampoh-d/lpjg_input/input/pop_dens/...` (LOCAL) | per PRODUCTION_RUN_CONFIG.md §3.2 |
| `file_mNHxdrydep` | (not set) | `/media/bampoh-d/lpjg_input/input/ndep/ndep_drynhx_*.nc4` (LOCAL) | per-SSP file |
| `file_mNHxwetdep` | (not set) | (similar, wetnhx) | per-SSP file |
| `file_mNOydrydep` | (not set) | (similar, drynoy) | per-SSP file |
| `file_mNOywetdep` | (not set) | (similar, wetnoy) | per-SSP file |
| `state_path` | not used | (set if doing hist save → SSP restart) | possibly defer to a follow-up; first 100-cell test could be hist-only |
| `save_state` | not used | (set for hist save) | (see above) |
| `restart` | not used | (set for SSP restart) | (see above) |

### 6.2 `runs/SSP1-2.6/landcover.ins` + `crop.ins` updates

| Parameter | Smoke | Production | Path |
|---|---|---|---|
| `file_lu` | legacy `version_A/.../LU_SSP1_RCP26_1901_2100_final.txt` | **`LU.remapv10_old_62892_gL_peatland.txt`** (hist) | `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/output_hildaplus_remap_10b_3/remaps_v10_old_62892_gL/LU.remapv10_old_62892_gL_peatland.txt` |
| `file_lucrop` | legacy `cropfracs_SSP1_RCP26_1901_2100_final.txt` | `cropfracs.remapv10_old_62892_gL.txt` | same dir |
| `file_Nfert` | legacy `nfert_SSP1_RCP26_1901_2100_final.txt` | `nfert.remapv10_old_62892_gL.txt` | same dir |
| `file_irrigintens` | legacy `irrig_SSP1_RCP26_1901_2100_final.txt` | (hist: empty `""` — no irrig file); (SSP: `irrig.txt`) | same dir for SSP |

For the SSP scenario period (2021-2100), additional files at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/SSP1_RCP26/s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/`:
- `landcover_peatland.txt` (315 MB; peatland-tagged scenario LU)
- `cropfractions.txt` (1.05 GB; per-pixel-per-year crop fractions)
- `nfert.txt` (1.05 GB; per-pixel-per-year nitrogen fertilization)
- `irrig.txt` (1.05 GB; per-pixel-per-year irrigation)

### 6.3 `imogen_intermediary.ins` (already at production values post-B39)

The B39 close-out set `CO2_INIT_PPMV=296.1`, `CH4_INIT_PPBV=875.6`, `N2O_INIT_PPBV=277.4` (Law Dome 1900 baseline matching the `YEAR1=1900` production-IMOGEN starting epoch). No change needed for 1900-start production runs. For 1850-start spinup runs (NOT the v1.0 paper-publication default), use 284.3 / 815 / 273.0 per `docs/scientific_framework.md` §6.1.

---

## 7. Local 100-cell test plan (session 8.5)

### 7.1 Acceptance gates (per Rule #10 discipline)

| Gate | Criterion | Verification method |
|---|---|---|
| G0 | All 7 production knobs from §2 simultaneously active | Pre-flight `.ins` parameter verification + file-existence check |
| G1 | Launcher exit code 0 | `echo $?` after invocation |
| G2 | All ~100 year-dirs produced (1900-2020 historical → could extend to 2100 if SSP block included) | `ls Common-directory/IMOGEN/output/ | wc -l` |
| G3 | All 100 cells processed (no MPI/parallel-related cell drops) | LPJG `*.out` files have 100 cell-rows per year |
| G4 | No ERROR/SEVERE/FATAL in launcher log or LPJG log | `grep -icE 'ERROR|SEVERE|FATAL|abort' logs/*` |
| G5 | SimFire BLAZE fire-loss output non-zero (i.e., the BLAZE fire model actually ran + produced output, not silently inactive) | `head firert.out` or equivalent; non-zero `fire_loss` column |
| G6 | NHx/NOy ndep values realistic (not stuck at 2 kgN/ha/yr fallback) | `mean(ndep.out)` or similar; expect ~5-15× pre-industrial in modern years |
| G7 | LU forcing applied correctly (peatland fraction non-zero in known peatland regions) | spot-check `landcover.out` against known boreal-peatland cells |
| G8 | State save/restart workflow (if exercised) | hist `state/` dir populated; SSP restart loads the state cleanly |

### 7.2 Audit-evidence bundle location

`_chat_artifacts/local_production_100cell_test_2026-05-XX/` (XX = actual session-8.5 date).

Contents:
- Full launcher log
- LPJG `*.out` files (selected key ones: cflux.out, ngases.out, firert.out, landcover.out, ndep.out)
- 8-gate acceptance evaluation Markdown (per Rule #10 pattern)
- Configuration diff vs smoke (clear which knobs were activated)

---

## 8. Cluster scaling phases (sessions 9+)

### 8.1 Phase 1 — cluster smoke (4-cell or 100-cell on cluster)

Once env_owl.sh refined + cluster sbatch wrapper updated (per §5 + §4 decision), first cluster invocation should be a **cluster equivalent of the local 100-cell test** to validate that the cluster path works end-to-end. Same 8 acceptance gates as §7.1 but on cluster.

### 8.2 Phase 2 — single-SSP full-cluster production-IMOGEN run

After phase 1 passes, scale to full 62538-cell × 200-year (1900-2100) for SSP1-2.6 (the canonical reference scenario). Iterate as bugs surface.

### 8.3 Phase 3 — remaining 4 SSP scenarios

SSP2-4.5 + SSP3-7.0 + SSP4-6.0 + SSP5-8.5. After phase 2 lessons-learned + cluster setup is stable.

### 8.4 Phase 4 — Track 1 paired cluster runs (if needed for validation triad)

If the existing Track 1 outputs at the cluster `/bg/data/lpj/...` paths are not directly usable for the validation triad (e.g., different gridlist, different LU vintage), a fresh Track 1 paired-cluster-run set may be needed. **Decision deferred to post-phase-3** based on validation triad needs (per `notes/PAPER_COMPLETION_AND_VALIDATION.md`).

---

## 9. Iteration discipline (Rule #9 + #10 carry-forward)

- **Rule #9 (harness-authoring routinely surfaces latent defects)**: every cluster + production-run iteration should bundle audit-evidence at `_chat_artifacts/<phase>_<date>/` so newly-surfaced findings (e.g., a missing input file; a cluster-specific path mismatch; a scaling bug at npatch=25 that didn't manifest at npatch=1) are captured for future maintainers.
- **Rule #10 (verification-integrity discipline)**: every cluster + production-run claim ("the run completed", "the outputs match X", "the cluster scaled cleanly") must cite concrete artifacts (log + output sample + acceptance gates Markdown). Honest framing of failures / partial successes (e.g., "the run completed but the LU forcing on 12 cells showed schema mismatch; outcome reported honestly here") is preferred over hiding or minimizing.

The cluster + production-run work is **multi-week** (per §1.3 outlook) and **iterative** (per user note "the cluster work will likely be iterative"). The Rule #9 + #10 discipline keeps the work auditable + handoff-ready throughout.

---

## 10. Cross-references

- `notes/PRODUCTION_RUN_CONFIG.md` — the canonical smoke→production reference (THE source-of-truth for what production-config looks like; this document operationalises that into a session-ordered plan)
- `notes/PAPER_COMPLETION_AND_VALIDATION.md` — sibling document covering validation triad + paper-stage analysis + writing
- `notes/B37.md` §5 — path-iv `done`-marker sidecar mechanism (root cause of pre-B44 productive-year ceilings)
- `notes/B44.md` — `--engine-only-mode` flag productisation in `scripts/run_coupled.sh` (local launcher; cluster integration deferred per this document §4)
- `notes/STEP_17c.md` §1.7.8 — 17c.1+ cluster phases ACTIVE NEXT roadmap (this document operationalises it)
- `notes/FOLLOWUPS.md` F-10 + F-12 — architectural deadlock + tight-coupling resolution path
- `notes/FOLLOWUPS.md` B45 + B46 — post-v1.0 source-edit items (brittle year sentinels; optional N2O channel split)
- `notes/LOCAL_V1_VERIFICATION_WINDOW.md` — local v1 verification window summary (the prerequisite gate that's now ✅ FULLY COMPLETE)
- `scripts/run_coupled.sh` — local launcher (post-B44; `--engine-only-mode` enabled)
- `scripts/cluster/run_coupled.sbatch` + `scripts/cluster/README.md` — cluster launcher + architecture overview (pre-B44; needs the §5 updates)
- `scripts/cluster/env_owl.sh` — cluster module-load template (PLACEHOLDER; needs §3.1 SSH refinement)
- `docs/scientific_framework.md` §5 (F-10 caveat) + §6.1 (per-YEAR1 atm-conc seed table)
- IMK-IFU legacy cluster orchestration: `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/`
- Predecessor production-style `.ins`: `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/integrated-4.1-ins2_landsymm_{hist,ssp126}/`

---

## 11. Open items / questions for session 8+ (append as they arise)

| # | Item | Surfaced | Owner | Resolution timing |
|---|---|---|---|---|
| 1 | Does `-input imogen` (via `lpjguess/modules/imogen_input.cpp`) handle cfx-style auxiliaries (SimFire BLAZE, popdens, ndep, LU) or is it climate-only? | session 7 close 2026-05-19 | session 8.3 source-read | session 8.3 |
| 2 | Which §4.3 cluster integration option (α / α′ / β / β′) is the v1.0 paper-publication path? | session 7 close 2026-05-19 | session 8.3 decision; user approval at 8.7 | session 8.3-8.7 |
| 3 | `env_owl.sh` actual module names + versions (gcc, cmake, netcdf-c, netcdf-fortran, openmpi, hdf5) | session 7 close 2026-05-19 | session 8.1 SSH paste-back | session 8.1 |
| 4 | KIT IMK-IFU `owl` partition specs + queue policies + storage paths verification | session 7 close 2026-05-19 | session 8.1 SSH paste-back | session 8.1 |
| 5 | User's typical LPJG-on-owl workflow conventions (for sbatch wrapper adaptation) | session 7 close 2026-05-19 | session 8.2 walkthrough | session 8.2 |
| 6 | NEEDS-UPDATE `notes/B44.md` §4 + FOLLOWUPS B44 entry: reflect more accurate cluster-integration framing per this document §4 | session 7 close 2026-05-19 | session 8 start (low-priority fold-in) | session 8 start or with session-8.7 cluster sbatch commit |
| 7 | Production gridlist: `gridlist_in_62892_and_climate.txt` (62538 valid cells from 62892 nominal); verify the local copy at `data/gridlist/` exists + matches the cluster copy | session 7 close 2026-05-19 | session 8.4 pre-flight | session 8.4 |
| 8 | State save/restart workflow: hist run saves at year 2020, SSP run restarts; first 100-cell test could be hist-only; full workflow validated separately at phase 2 | session 7 close 2026-05-19 | session 8.4-8.5 decision | session 8.4-8.5 |

(Append new items as discoveries surface.)

---

_End of `notes/CLUSTER_SETUP_AND_PRODUCTION_RUNS.md` v0.1 — initial draft 2026-05-19 evening session 7 close; iteratively updated through session 8+ cluster + production-run work._
