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

## 1. Recommended session-8+ ordering (the operational plan)

### 1.1 Headline strategy — local-first with cluster reconnaissance in parallel

Reasoning (carried forward from session-7 close analysis):

1. The current smoke-test setup (`runs/SSP1-2.6/main.ins`) has validated only a 4-cell × 2-year window. **Roughly 7 production knobs are unverified** (§2 below). Each is a potential failure mode (missing file, wrong path, schema mismatch, scaling bug). Catching these locally on a ~100-cell reduced gridlist takes minutes-to-hours per iteration; catching them on the cluster takes queue wait + node debugging + SCP cycles per iteration.
2. `notes/PRODUCTION_RUN_CONFIG.md` §6.1 readiness checklist explicitly endorses this ordering: "Test run on local workstation with reduced gridlist (e.g., 100 cells; verify full pipeline works) **before** cluster scaling".
3. However, **one cluster-side task has no local equivalent** and should happen ASAP: the `env_owl.sh` module-load refinement (per `scripts/cluster/README.md` lines 124-130). A 5-minute SSH `module avail` + report-back gives me the actual cluster module versions so I can commit refined values.

So the operational plan parallelises cluster reconnaissance (which is gated only on your SSH access) with local production-config setup (which is gated only on local edit work).

### 1.2 Concrete session-8 block ordering (proposal; user can adjust)

| Block | Effort | Mode | What |
|---|---|---|---|
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
