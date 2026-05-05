# Phase-2 Subagent 8 — Orchestration, Run Setups, and `Data/`

**Scope.** Walk one example coupled run end-to-end; diff `landsymm_imogen_setup`
(version A, workstation) vs `landsymm_imogen` (version B, cluster); inventory
`Data/` (1 level deep with samples); catalog top-level helper trees
(`Matlab-scripts`, `Python-scripts`, `Plots`, `NdepFastArchive`);
sample `Common-directory/IMOGEN/` to confirm the year-directory + per-variable
file + `done` marker model. Investigation is read-only.

**Repo paths used (root abbreviations).**
- `A_FW = landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK`
- `B_FW = landsymm_lpjg_imogen_coupled_model/version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK`

Both directories are independent git checkouts of the same upstream
(`https://github.com/dbampoh/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK`, branch `main`).
A is one commit ahead of the common ancestor (`454bff9 Merge ...`,
`59eeb64 Update`, `dc26cd8 Update`); B has two newer commits
(`5e982a0 Updates`, `93f111d Updates`, `59eeb64 Update`).

The Subagent 1–7 reports cover the model code itself (LPJ-GUESS C++,
IMOGEN C++, Intermediary, controller, FastRegrid, etc.). This report is the
view from "outside the binaries": run directories, ins-file wiring, gridlists,
data inputs, and the synchronization model.

---

## 1. `landsymm_imogen{,_setup}` — workstation vs cluster setups, full diff

### 1.1 Directory layout

| Item | A (workstation) | B (cluster) |
|---|---|---|
| Top dir under framework | `landsymm_imogen_setup/` | `landsymm_imogen/` |
| Inner SSP dir | `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/` | `landsymm_imogen/SSP1_RCP26/` |
| Other SSPs (SSP2_RCP45, SSP3_RCP70, SSP4_RCP60, SSP5_RCP85) | absent — only `SSP1_RCP26` | absent — only `SSP1_RCP26` |

A wraps the SSP run dir in an extra `landsymm_imogen_setup/landsymm_imogen/`
prefix; B drops the outer "setup" wrapper. Beyond that, the SSP1_RCP26 dir is
the **only** scenario realized on disk in either version. Other SSPs are
implied by file naming throughout `Data/Imogen/emiss/CMIP{5,6}/...`,
`Data/Intermediary/Emissions/...co2_ssp{1..5}.txt`, etc., but no
`SSP{2,3,4,5}_RCP{45,70,60,85}/` run directories exist.

### 1.2 Files in `SSP1_RCP26/` — identical sets

```bash
$ diff -rq A_FW/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/ \
           B_FW/landsymm_imogen/SSP1_RCP26/
```

The two directories contain the same 33 files. Differences:

| File | Differs? | Notes |
|---|---|---|
| `setup_run.sh` | identical (byte-for-byte) | Same launcher invocation |
| `global.ins` | identical | LPJ-GUESS global config |
| `global_soiln.ins` | identical | Soil-N config |
| `wetlandpfts.ins` | identical | Wetland PFT defs |
| `crop_n_pftlist.simplePFT.remap10_g2p.ins` | identical | 10 simplePFT defs |
| `crop_n_stlist.simplePFT.remap10_g2p.{N0-60-200-1000,agreed_treatments}.ins` | identical | Stand-type lists |
| `pasture_n_stlist*.ins` | identical | Pasture stand types |
| `crop_n.ins` | identical | Crop-N defs |
| All `gridlist_*.txt` (12 files) | identical | Same point sets in both versions |
| `main.ins` | **differs (paths)** | A: `/home/bampoh-d/Desktop/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/...`; B: `/bg/data/lpj/bampoh-d/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/...`; B uses bare `gridlist.txt` (split by SLURM driver) instead of an absolute path |
| `crop.ins` | **differs (paths)** | Same prefix swap |
| `landcover.ins` | **differs (paths)** | Same prefix swap |
| `imogen_intermediary.ins` | **differs (more)** | (1) path prefix swap; (2) A: `scenario "cmip6"` / CMIP6 emiss files for `ssp126`; B: `scenario "cmip5"` / CMIP5 emiss files for `rcp26`; (3) A: `DIR_COMMON_OUT "/home/.../Common-directory"`, B: `DIR_COMMON_OUT "./"` (per the comment, "must be `./` for parallel runs"); (4) A: `LPJG_CFLUX 1`, B: `LPJG_CFLUX 0` |
| `guess` symlink | **differs (target)** | A → `/home/bampoh-d/Desktop/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/build_imogen/guess` (resolves OK locally — separate sibling checkout); B → `/bg/data/lpj/bampoh-d/.../build_landsymm_imogen/guess` (resolves OK on cluster) |
| `guess.log`, `qsat_output.txt` | **A only** | Run residue from a partial in-place test (see § 9) |

### 1.3 The `setup_run.sh` (identical in A and B)

`A_FW/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/setup_run.sh`:

```1:4:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/setup_run.sh
#  args setup_run_owl_with_scratch_lpj_work.sh:
#  <runname>  <maininsfile> "all other ins files in quotes" <grid>  <inputmethod>  <nodelist> <nnodes> <keal|uc2> <appendqueue> <appendntasks> <runqueue> <cpu_per_node>"
setup_run_owl_with_scratch_lpj_work.sh $(basename $PWD) main.ins "global.ins global_soiln.ins imogen_intermediary.ins landcover.ins crop.ins crop_n.ins crop_n_pftlist.simplePFT.remap10_g2p.ins crop_n_stlist.simplePFT.remap10_g2p.agreed_treatments.ins crop_n_stlist.simplePFT.remap10_g2p.N0-60-200-1000.ins pasture_n_stlist.ins pasture_n_stlist_agreed_treatments.ins wetlandpfts.ins" gridlist_in_62892_and_climate.txt  imogencfx  "" 2 owl  haswell 8 haswell 40
```

This invokes a `setup_run_owl_with_scratch_lpj_work.sh` that **does not exist
inside this repository** (verified with both `Glob "**/setup_run_owl*"` and
`Grep "setup_run_owl_with_scratch_lpj_work"` over the workspace). It is part of
the LPJ-GUESS Lund cluster-side helper toolkit, expected on `$PATH` — the same
helper used by other `Integrations/trunk_r13078_test/*/setup_run.sh`. On a
plain workstation without that helper, this script does **nothing useful**;
the user must invoke `./guess` directly.

The args expanded are: runname = directory basename; maininsfile = `main.ins`;
ancillary ins list (12 files); gridlist = `gridlist_in_62892_and_climate.txt`
(62 538 cells); LPJ-GUESS input module = `imogencfx`; node placement (`""
2 owl haswell 8 haswell 40`) is cluster scheduler metadata.

**Inconsistency.** In `Integrations/trunk_r13078_test/{lsa_hist_base_ipsl,
integrated-4.1-ins2,integrated-4.1-ins2-wsl}/setup_run.sh` the comment header
says `setup_run_keal_with_scratch_lpj_work.sh` while the call below uses
`setup_run_owl_with_scratch_lpj_work.sh` — owl/keal are two different LSA
clusters; the comment was not updated.

### 1.4 Key path / scenario differences — `imogen_intermediary.ins`

A (workstation, CMIP6/SSP1-2.6, lines 5–10, 56–88):
```5:10:landsymm_lpjg_imogen_coupled_model/version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/imogen_intermediary.ins
scenario "cmip6"
firstyear 1850
lastyear 2100
lpjg_start_year 1901
lpjg_end_year 2100
baseDirectory "/home/bampoh-d/Desktop/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/"
```

B (cluster, CMIP5/RCP2.6 — but in the same directory still labelled SSP1_RCP26):
- `scenario "cmip5"` (vs `"cmip6"` in A)
- `DIR_COMMON_OUT "./"` (vs absolute Common-dir path in A)
- `FILE_SCEN_EMITS = .../CMIP5/Co2/co2_emissions_fossilonly_historical_rcp26.txt` (vs CMIP6 SSP126 files in A)
- `LPJG_CFLUX 0` (vs `1` in A) — controls whether IMOGEN reads land C flux from LPJ-GUESS

So A and B are not just "same setup, different roots" — the chosen IMOGEN
forcing-data scenario is genuinely different (CMIP6/SSP1-2.6 in A, CMIP5/RCP2.6
in B), even though the *directory name* is `SSP1_RCP26` in both. This is a
silent semantic divergence and worth flagging.

### 1.5 Key gridlist used

`gridlist_in_62892_and_climate.txt` (62 538 lines, 780 KB; identical between
A and B). First lines:
```
-91.25 17.75
-121.75 37.25
69.25 44.75
```
Other gridlists in the run dir are subsets / variants for tests:
`gridlist_test1.txt` (1 cell, 13 B), `gridlist_test2.txt` (2 cells, 27 B),
`gridlist_test480.txt` (480 cells), `gridlist_germany_HiRes_005deg_RNDM.txt`
(0.05° Germany grid), `gridlist_germany_LoRes_05deg_RNDM.txt` (0.5° Germany),
`gridlist_hurtt_RNDM_midpoint{,_3698,_3698_10cells,_3711,_eu}.txt`,
`gridlist_in_57{393,819,824}_plumharm2lpjg{,_rem,_random}.txt`. Only the
single 62k file is wired up via `setup_run.sh`. All gridlists are 2-column
"lon lat" (with optional 3rd-col cell name) plain text.

### 1.6 What is *not* in the run dir

- **No SLURM `.sbatch` / `.slurm`** anywhere in either A or B (`Glob`
  `**/*.sbatch` and `**/*.slurm` returned 0 hits). The framework relies on the
  external `setup_run_owl_with_scratch_lpj_work.sh` helper to generate SLURM
  jobs; nothing in this repo carries `#SBATCH` in any user-visible launcher
  except the LPJ-GUESS upstream `parallel_version/{aurora,gimle,simba}.tmpl`
  templates and the auto-generated `Integrations/trunk/trunk_r13078/build_imogen/submit.sh`.
- **No `module load`** anywhere except the same upstream LPJ-GUESS templates.
- **No `Imogen-controller` invocation** (the controller binary built by
  `Imogen-controller/Makefile` is not started anywhere in the run scripts).
- **No coupled-mode driver script** (sequence "spawn IMOGEN, then spawn LPJG,
  watch `done`, advance year") exists anywhere in either version.

So both A and B are *single-binary launches*: they invoke the LPJ-GUESS binary
with the `imogencfx` input module, and the LPJ-GUESS process is expected to
make the IMOGEN calls in-process via the linked-in IMOGEN sources
(see Subagent-2/3/4 reports for the link/in-process model). The Imogen-
controller (and the README "Plans are underway to develop a bash script that
will automate the simultaneous execution of both models") describe a
**second**, file-based external coupling design that is **not used** in the
SSP1_RCP26 setup as shipped.

---

## 2. Cluster-specific artifacts (B vs A)

There are essentially **none in the repo itself**. Concrete differences B vs A:

| Artifact | A | B |
|---|---|---|
| Path prefix in ins files | `/home/bampoh-d/Desktop/...` | `/bg/data/lpj/bampoh-d/...` |
| `landcover.ins` `file_soildata` | `Data/soil/...` (in-repo) | `/bg/data/lpj/bampoh-d/soil/...` (out-of-repo cluster path) |
| `landcover.ins` `file_gridlist` | absolute repo path | bare `"gridlist.txt"` (split per process by parallel driver) |
| `imogen_intermediary.ins` `DIR_COMMON_OUT` | absolute Common-dir path | `"./"` (per-process working-dir, required for parallel) |
| `guess` symlink target | local `build_imogen/guess` | cluster `build_landsymm_imogen/guess` |
| `Data/soil/` | present (`soilmap_center_interpolated.remapv10_old_62892_gL.dat`, 3.5 MB) | **absent** — relies on out-of-repo `/bg/data/lpj/bampoh-d/soil/` |
| `Data/Concentrations/`, `Data/Imogen/` | present | **absent** (only `Concentrations`, `Emissions`, `Gridlist`, `Imogen`, `Intermediary`, `LU`, `Ndep` — `Imogen` directory listed but the `Climate/output/ssp*` placeholders may be empty as in A; soil missing entirely) |

Confirmed: B has no `Data/soil` (`ls .../Data/soil` returns "No such file or
directory"). The `landcover.ins` therefore *must* point outside the repo on
the cluster.

There is no environment-modules file (`modulefile`, `*.lua`, `module load`),
no `.sbatch`/`.slurm`/`.sub` job script, no Spack/Conda manifest tied to the
cluster — none of the things you would expect for a cluster checkout. All
cluster-specific behaviour comes from the (out-of-repo) `setup_run_owl_*`
helper plus the per-host LPJ-GUESS `parallel_version/*.tmpl` infrastructure.

---

## 3. End-to-end launch sequence — the actual commands

The "documented" tightly coupled flow (per `README.md` and Imogen-controller
`README.txt`) is *not* what is actually wired up. What the repo, as shipped,
*supports* is:

### 3.1 Build (out of scope here; see Subagent 3 / 5)

```bash
# LPJ-GUESS with the IMOGEN-coupled `imogencfx` input module
cd Integrations/trunk/trunk_r13078/build_imogen
cmake .. && make            # produces ./guess (the binary symlinked into SSP1_RCP26)
```

### 3.2 What a user would actually run for SSP1_RCP26

There is **no top-level orchestration script**. To run the only realized
scenario, a user would (workstation A):

```bash
cd version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26

# Path 1 — what setup_run.sh tries to do (cluster-only, requires
# setup_run_owl_with_scratch_lpj_work.sh on $PATH; the script is NOT in this repo)
./setup_run.sh

# Path 2 — direct, what actually works on a workstation (single process):
./guess -input imogencfx main.ins
# (12 ancillary ins files are all `import`-ed transitively by main.ins)
```

The LPJ-GUESS process, because it was built with the IMOGEN sources linked in
(`build_imogen/`), produces the IMOGEN climate year by year and writes it to
`Common-directory/IMOGEN/output/<YYYY>/{T_anom.dat, P_anom.dat, SW_anom.dat,
WET.dat, DTEMP_anom.dat, W_anom.dat, Rh_anom.dat, CO2.dat, dtemp_o.dat,
fa_ocean.dat, done}` — confirmed in §6 below — and reads the same files back
in for the next year via `imogencfx`'s `param "file_temp"` etc. So in this
shipped configuration the "two models" are one OS process; the `done` marker
file is being written and the LPJ-GUESS code-path that consumes `done` lives
inside the same binary (see `Integrations/trunk/trunk_r13078/modules/climatemodel.cpp:875`
which references `dirCommonOut + "/IMOGEN/output/" + thisYear + "/Rh_anom.dat"`).

### 3.3 What the README *describes* (and what is missing)

`README.md` § "Setting Up a Coupled Run" closes with: *"Plans are underway to
develop a bash script that will automate the simultaneous execution of both
models, streamlining the process."* That script does not exist in the repo.

The Imogen-controller README also describes a 2-process file-based polling
loop ("the executable iteratively (in 2 sec interval) comes in to check if
the done marker file exists. If it doesn't, this executable creates it"), but
the Imogen-controller binary is never invoked from `setup_run.sh`,
`main.ins`, or any Makefile target other than `Imogen-controller/Makefile`'s
own `make run`. So the polling-loop external orchestrator design is built but
not wired in.

---

## 4. `done`-file orchestration

### 4.1 Where the `done` file lands

Confirmed by inspecting `A_FW/Common-directory/IMOGEN/output/` (a real run from
2025-06-16): each year subdir 1871..2100 (230 dirs) contains exactly one
`done` file alongside the per-variable `*.dat` files. Sample:

```
$ ls Common-directory/IMOGEN/output/1871/
CO2.dat  DTEMP_anom.dat  P_anom.dat  Rh_anom.dat  SW_anom.dat
T_anom.dat  WET.dat  W_anom.dat  done  dtemp_o.dat  fa_ocean.dat

$ cat Common-directory/IMOGEN/output/1871/done
Climate files written
```

`done` is a 22-byte plain-text file with the literal payload
`Climate files written\n`. It sits inside `<DIR_COMMON_OUT>/IMOGEN/output/<YYYY>/`.

### 4.2 Who writes it / who polls it

In the shipped single-process build:
- The IMOGEN code (linked into the LPJ-GUESS binary) writes `done` after it
  finishes generating that year's `*.dat` files.
- The same binary's `imogencfx` input-module / `climatemodel.cpp` then reads
  the same year directory's `Rh_anom.dat` etc. to drive LPJ-GUESS for the
  next step. (Subagent 3 covers the C++ side; this report only confirms the
  files exist on disk.)

In the *intended* 2-process design (per Imogen-controller README):
- LPJG would write `done` after finishing its year.
- IMOGEN-controller (`Imogen-controller/Imogen-controller-cross.cpp:158, 202,
  245`) polls `commonDirectory + "LPJG_main\\IMOGEN\\done"` every 2 s,
  re-creates it, and toggles a settings file. **Note the Windows `\\` path
  separator hardcoded in source — would need patching for Linux.**
- The IMOGEN side, also Fortran-based per the readme, would block on the same
  marker.

The discrepancy between "lands in `Common-directory/IMOGEN/output/<YYYY>/done`"
(what was actually produced) vs "lands in `Common-directory/LPJG_main/IMOGEN/done`"
(what Imogen-controller polls) suggests **the controller path was never
reconciled with the actual IMOGEN output layout**. So even if the controller
were started, it would never see the `done` file.

### 4.3 230 done files / 230 year dirs

Spot-check across `1871, 1900, 1950, 2000, 2050, 2100`: every dir has 11
files including `done`. So the IMOGEN run that produced
`Common-directory/IMOGEN/output/` ran successfully through 2100 — but the
`imogen_*.log` files (3 logs from 2025-06-16) show 4–5 second gaps between
years, which is too fast to include a real LPJG step. This was a
**standalone IMOGEN-only seeding run**, not a coupled run.

---

## 5. `Data/` — per-subdir inventory

Top-level (`A_FW/Data/`):

| Subdir | Size | Role |
|---|---|---|
| `Concentrations/` | 9.5 MB | GHG concentration time series (drives IMOGEN) |
| `Emissions/` | 916 KB | IIASA-only GHG emissions inventories (legacy / reference) |
| `Gridlist/` | 3.4 MB | LPJ-GUESS grid lists (in addition to the run-dir copies) |
| `Imogen/` | 5.2 MB | IMOGEN-specific climate placeholders + emissions inputs |
| `Intermediary/` | 2.2 GB | Intermediary processing inputs/outputs (CO2/CH4/N2O ledgers, PLUM data) |
| `LU/` | 7.3 GB | Land-use forcings (LU/cropfracs/nfert/irrig) for LPJ-GUESS |
| `Ndep/` | 501 MB | N-deposition binary archives (Lamarque-format) |
| `soil/` | 3.5 MB | LPJ-GUESS soil-property table |

(B mirrors most of these but has **no `Data/soil/`**, no `Data/Concentrations/`,
and no `Data/Imogen/`; B's ins files compensate by pointing outside the repo
to `/bg/data/lpj/bampoh-d/soil/...`.)

### 5.1 `Data/Concentrations/`

- `CO2_all.dat` — 1901–onward time series, columns: `year ppm? + ?? ?? ??
  ?? CH4-ppb N2O-ppb`. First line:
  ```
        1901   296.763672      0.251513988       0.00000000      -5.78501262E-02  0.193664551       891.328857       276.470886
  ```
- `EPA/` — `ghg-concentrations_{ch4,co2,n2o}.csv` (CSV, 2-col `year,ppm/ppb`)
  plus `XLSX/` raw spreadsheets. Sample first 3 lines of `_co2.csv`:
  `1850,284 / 1851,288.79 / 1854,288.05`.
- `IIASA/CMIP6/` and `IIASA/CMIP5/` — IIASA-published RCP/SSP concentration
  scenario files (XLSX + ZIP for CMIP6, plus rcp26/85 N2O `.txt`
  interpolations); `IIASA/CMIP5/TXT/` has DAT-format MAGICC files
  (`PICNTRL_MIDYR_CONC.DAT`, `PRE2005_MIDYR_CONC.DAT`, `RCP{3PD,45,6,85}_MIDYR_CONC.DAT`)
  and `rcp{26,45,60,85}_{ch4,co2,n2o}_interpolated.txt`.
- `IIASA/IAM Scenarios/` — additional IAM scenarios (not opened).

### 5.2 `Data/Emissions/`

Single subdir `IIASA/{CMIP5,CMIP6}/`. CMIP-format emission inventories,
companion to `Concentrations/`. Used as alternate IMOGEN inputs.

### 5.3 `Data/Gridlist/` (different file set from the run-dir gridlists)

```
gridlist_hilda+.txt                       62864 lines, 784K
gridlist_hurtt_RNDM_midpoint.txt          59191 lines, 984K
gridlist_hurtt_RNDM_midpoint_3698.txt      3696 lines,  64K
gridlist_in_62892_and_climate.txt         62538 lines, 780K   <- the active one
gridlist_test2.txt                            4 lines, 4.0K
ndep_gridlist.txt                         59191 lines, 800K
patterns_gridlist.txt                      1631 lines,  28K   <- IMOGEN pattern grid
```
All are 2-column (lon lat) plain text. `patterns_gridlist.txt` uses 0..360
longitude (e.g. `281.25 82.50`) consistent with the IMOGEN pattern files in
`Common-directory/IMOGEN-codebase/patterns/`; the LPJG gridlists use −180..180
(e.g. `-91.25 17.75`).

### 5.4 `Data/Imogen/`

- `Climate/output/ssp{126,245,370,460,585}/` — 5 *empty* placeholder dirs
  (28 KB total). Where IMOGEN climate would land if `DIR_COMMON_OUT` pointed
  here. The actual run output sits in `Common-directory/IMOGEN/output/` (§6).
- `emiss/CMIP5/{Co2, CH4-N2O, Non-Co2-CH4-N2O-RF}/` — IMOGEN emission inputs
  for the CMIP5/RCP scenarios, e.g. `co2_emissions_{fossilonly,landuseonly,
  total}_historical_rcp{26,45,60,85}.txt`,
  `ch4_n2o_annual_historical_natural_rcp26_1850_2100.txt`,
  `nonco2_ch4_n2o_RF_historical_rcp26.txt`. Sample
  `co2_emissions_fossilonly_historical_rcp26.txt` first 3 lines:
  `1850 0.0540 / 1851 0.0577 / 1852 0.0614`.
- `emiss/CMIP6/{Co2, CH4-N2O, Non-Co2-CH4-N2O-RF}/` — equivalents for SSP1-5.
  Sample `co2_pg_emissions_anthropogenic_historical_ssp126_1850_2100.txt`:
  `1850 0.000000 / 1851 0.482350 / 1852 0.957810`.
- `emiss/{rcp_database, new_emission_data, DKB_dataset_totals}` and
  loose files (`RF_NONCO2_GHG_IS92A.dat`, `emiss_co2.dat`,
  `hist_rcp{2p6,4p5,6p0,8p5}_emiss_ch4_n2o_total_cmip5.txt`).

### 5.5 `Data/Intermediary/` (the largest "logical" tree)

| Sub | Sample files | First line |
|---|---|---|
| `Emissions/` | `co2_ssp1.txt`, `methane_ssp1.txt`, `nitrogen_ssp1.txt`, `enteric_fermentation_methane_ssp1.txt`, `IPCC_OWI_FAO_methane_1961_2009_ssp1.txt`, `ch4_n2o_annual_historical_ssp1rcp26_lpjg_simulated_real.txt`, plus ssp5 mirrors | `1850   0.07620` |
| `IPCC_OWI_FAO/` | `IPCC_OWI_FAO_{methane,nitrogen}_1961_2009.txt` | `1961  136.84163` |
| `IPCC_PLUM/` | `IPCC_PLUM_{methane,nitrogen}_2010_2100_ssp{1,5}.txt`, `nitrogen_ssp1.txt` | `2010   37.16664` |
| `Input/` | `CMIP5/`, `CMIP6/`, `FAOSTAT.csv`, `PLUM_Fertilizer_SSP{1..5}.txt`, `arablelands.csv`, `countries.txt`, `livestock-counts.csv`, `n2ofertilizer.csv` | (CSVs vary) |
| `Input/CMIP5/` | `ch4_n2o_annual_historical_rcp{26,45,60,85}_{lpjg_simulated, non_lpjg_simulated}.txt`, plus `CH4/` and `N2O/` subdirs | (split LPJG vs non-LPJG totals) |
| `PLUM_data/` | `agg_land_use/`, `plum_land_use/`, `animals_ssp{1..5}.txt` | (PLUM SSP scenario assets) |

These are exactly the files referenced symbolically (with `sspSSP`, `rcpRCP`
placeholders) in `imogen_intermediary.ins` (lines 11–36), so this is the
Intermediary's working file system.

### 5.6 `Data/LU/SSP1_RCP26_concatenated/`

Only one scenario realised (others would be analogous). Contents:

```
LU_SSP1_RCP26_1901_2100_final.txt              + .map.bin (binary index)
cropfracs_SSP1_RCP26_1901_2100_final.txt       + .map.bin
nfert_SSP1_RCP26_1901_2100_final.txt           + .map.bin
irrig_SSP1_RCP26_1901_2100_final.txt
```

Sample `LU_..._final.txt`:
```
Lon Lat Year NATURAL CROPLAND PASTURE BARREN
-179.75 65.75 1901 0.427431 0.000000 0.132850 0.439719
-179.75 65.75 1902 0.427431 0.000000 0.132850 0.439719
```
Sample `nfert_..._final.txt` has 22 cropPFT-specific fertilization-rate
columns (CerealsC3, CerealsC4, Rice, ..., Miscanthusi). The `.map.bin` files
are a binary lookup index produced by LPJ-GUESS to accelerate gridcell access
to the text data. `file` reports them as raw `data` (no magic header).

### 5.7 `Data/Ndep/ndep_cruncep/`

```
GlobalNitrogenDeposition.bin                <- historic
GlobalNitrogenDepositionRCP26.bin
GlobalNitrogenDepositionRCP45.bin
GlobalNitrogenDepositionRCP60.bin
GlobalNitrogenDepositionRCP85.bin
```

Each is a binary "FastArchive" produced by the program in `NdepFastArchive/`;
header layout described by the `.h` files in that dir (see §7.4). These are
the files the `landcover.ins` `file_ndep` param points at.

### 5.8 `Data/soil/`

One file: `soilmap_center_interpolated.remapv10_old_62892_gL.dat` (3.5 MB).
Header + first row:
```
Lon   Lat   clay silt sand orgC CN pH cellfraction
-123.25 38.25 0.331 0.285 0.384 0.019 11.913 5.740 0.474
```
This is the same soil map referenced in `main.ins`'s `param "file_soildata"`.
It pairs cell-by-cell with the 62 892-cell gridlist. Confirmed identical
between A and B by file name, but the file itself is **only present in A**;
B replaces it with `/bg/data/lpj/bampoh-d/soil/soilmap_center_interpolated.remapv10_old_62892_gL.dat`.

---

## 6. `Common-directory/IMOGEN/` — IMOGEN run output (A only)

Layout under `A_FW/Common-directory/IMOGEN/`:

```
CO2_all.dat   <- 1901..present cumulative CO2 ledger (1901 296.76 ... )
RF_all.dat    <- radiative-forcing ledger
VARYEAR.dat   <- per-year scalar dump
imogen_20250616_011807.log
imogen_20250616_075821.log
imogen_20250616_094324.log
output/{1871, 1872, ..., 2100}/   <- 230 year dirs
```

Each year dir has the canonical 11-file set (sample 1871):
```
CO2.dat (39 B)        DTEMP_anom.dat (240 KB)  P_anom.dat (240 KB)
Rh_anom.dat (240 KB)  SW_anom.dat (240 KB)     T_anom.dat (240 KB)
WET.dat (240 KB)      W_anom.dat (240 KB)      done (22 B)
dtemp_o.dat (2.9 KB)  fa_ocean.dat (20 KB)
```

`CO2.dat` first line (1871):
```
1871 286.085 0.0 0.0 0.0 0.0 865 277.4
```
i.e. `year, CO2-ppm, ?, ?, ?, ?, CH4-ppb, N2O-ppb`. Last year (2100):
```
2100 3775.43 37.7128 1.25103 -2.81775 36.1461 2552.97 228.713
```
(CO2 = 3775 ppm by 2100 → this run was clearly an unconstrained emission
test, not a real RCP/SSP trajectory.)

`T_anom.dat` is a gridded 5°×5° anomaly field — first row is
`281.25 82.50 237.83 235.59 231.87 ...` (lon, lat, then 12 monthly values),
matching the 1631-cell `patterns_gridlist.txt`.

Log shows the run is purely sequential (≈ 4–5 s per year, no LPJG-step in
between):
```
[2025-06-16 09:43:24] IMOGEN Logger initialized.
[2025-06-16 09:43:28] Processing year: 1871
[2025-06-16 09:43:28] Created output directory: .../output/1871
[2025-06-16 09:43:28] Read Climatology Complete
[2025-06-16 09:43:33] Processing year: 1872
...
[2025-06-16 10:02:29] Processing year: 2100
```

So this run, although it physically produced the artifacts a coupled run
would, was **IMOGEN-only**, with no LPJG feedback in the loop. The "year
directory + per-variable file + done marker" model is fully confirmed.

`Common-directory/` also contains `IMOGEN-codebase/` (the upstream IMOGEN
source/data with `compile.sh`, `code/`, `CRUNCEP_1960_1989/`, `patterns/`,
`R_wrappers/`, `emiss/`, `patch_add_ch4_n2o_conc.diff`), `LPJG_main/IMOGEN/`
(historic LPJG-derived flux files such as
`ch4_n2o_annual_historical_ssp1rcp26_lpjg_simulated_real.txt`,
`extended_lpjg_only_cfluxrcp26.txt`, `imogen_lpjg.txt`,
`imogen_lpjg_ch4_n2o_flux.txt`, `imogen_lpjg_flux.txt` that prime IMOGEN at
startup), and 5 sibling **`IMOGEN_SSP{1..5}_RCP{26,45,70,60,85}_Clim/`**
directories, each ~396 MB and structured exactly like `IMOGEN/` (its own
`output/<YYYY>/` tree). These are pre-archived per-scenario climate runs from
the same era (2025-06-15/16 logs), evidently checkpointed so subsequent
LPJG-only experiments can read climate without re-running IMOGEN.

---

## 7. `Matlab-scripts/`, `Python-scripts/`, `Plots/`, `NdepFastArchive/`

### 7.1 `Matlab-scripts/`

Three preprocessing scripts plus a one-line README ("MATLAB scripts needed to
preprocess and post process data from coupled model framework as well as
prepare datasets for usage by coupled model framework"):
`new_iiasa_cmip6_ch4_plots_17_10_23.m`,
`new_iiasa_cmip6_co2_plots_21_10_23.m`,
`new_iiasa_cmip6_n2o_plots_21_10_23.m`. Each reads from a hardcoded relative
base `IIASA_DATABASE/Emissions/CMIP6/{CO2,CH4,N2O}/` and produces aggregate
SSP scenario plots from the `ssp_*.xlsx` IIASA workbooks. Path
`IIASA_DATABASE/...` does **not** exist in the repo — these scripts assume
the user manually downloaded the IIASA database into a sibling directory.

### 7.2 `Python-scripts/`

A single notebook + Python export
(`LPJG_IMOGEN_COUPLED_MODEL_FRAMEWORK_PLOTS.ipynb`,
`lpjg_imogen_coupled_model_framework_plots.py`) plus the matching one-line
README. The Python file is auto-exported from a Google Colab notebook
(`https://colab.research.google.com/drive/1zYwLsXeq9JPldRhBm0Of2NdjwV0GH3XG`)
and reads files like `IPCC_OWI_FAO_methane_1961_2009.txt`,
`IPCC_methane_2010_2100_ssp1.txt`, `lpjg_only_ch4_emissions_Mt_126_1901_2100.txt`
relative to its working dir, expecting them to be linked in from
`Data/Intermediary/`. Hardcodes `/content/drive/MyDrive/LPJG_IMOGEN_DATABASE/...`
in some paths, so these scripts are **Colab-only as written**.

### 7.3 `Plots/`

Static PNG outputs from the Matlab/Python scripts above:
`CMIP6_{CH4,CO2,N2O}_LPJG_IPCC_{NON_,}SIMULATED.png` and
`CMIP6_{CH4,CO2,N2O}_TOTAL.png` (9 PNGs total). Pre-rendered comparison plots
of LPJG-derived vs IIASA-published global emission trajectories.

### 7.4 `NdepFastArchive/`

Standalone C++ source tree (`Main.cpp`, `archive.h`, `guess{math,string}.{h,cpp}`,
`gutil.{h,cpp}`, `lamarquendep.{h,cpp}`, `shell.{h,cpp}`) plus 5
auto-generated FastArchive header files
(`GlobalNitrogenDeposition{,RCP26,RCP45,RCP60,RCP85}.h`, ~13.5 KB each).

Purpose: companion utility to read / re-pack the `Data/Ndep/ndep_cruncep/
GlobalNitrogenDeposition*.bin` archives that LPJ-GUESS consumes for
N-deposition forcing. The headers are in the FastArchive format produced by
the same template used by the LPJG `cru.bin` reader; per the file comment,
they were "Created automatically by FastArchive on Tue Nov 03 10:04:28 2015".
`Main.cpp` opens `GlobalNitrogenDeposition.bin`, iterates all records, and
writes lon/lat to `output_gridlist.txt` — i.e. it derives the cell list of an
N-dep archive (handy for matching it to a gridlist before a run). There is no
Makefile / CMakeLists in this dir; the `Main.cpp` references a Windows path
in a string (`C:\\GitHub\\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\\NdepFastArchive\\bin\\x64\\Debug\\GlobalNitrogenDeposition.bin`),
so it was developed on Visual Studio. The pre-archived RCP26/45/60/85
headers exist so future scenario-specific N-dep archives can be regenerated
with a one-line edit (`#include` swap).

---

## 8. Top-level `Makefile` / build orchestration

There is **no top-level Makefile** for the framework. The only Makefiles are
component-level:
- `Imogen-controller/Makefile` — builds `Imogen-controller` executable from
  `Imogen-controller-cxx.cpp` (g++ -std=c++17). Targets: `build`, `run`,
  `clean`. `make run` calls `./Imogen-controller` with no arguments.
- `Integrations/trunk/trunk_r13078/build_imogen/Makefile` — auto-generated by
  CMake; builds the LPJ-GUESS binary linked with the IMOGEN sources for the
  `imogencfx` input module. (Subagents 2/3 cover this.)
- `Common-directory/IMOGEN-codebase/compile.sh` — stand-alone IMOGEN compile
  script (covered by Subagent 3).
- `NdepFastArchive/` — *no* Makefile in-tree (would need manual `g++` invocation
  or a Visual Studio solution).

There is no top-level orchestration Makefile that ties build → run → analyze.

---

## 9. Bugs, hardcoded paths, broken scripts, TODO/FIXME

1. **Misspelled `IMOGEN/ouput/` path in both A and B's
   `imogen_intermediary.ins`** (lines 102–109):
   ```
   param "file_temp" (str "./IMOGEN/ouput/YYYY/T_anom.dat")
   param "file_prec" (str "./IMOGEN/ouput/YYYY/P_anom.dat")
   ...
   param "file_relhum" (str "./IMOGEN/ouput/YYYY/R_anom.dat")
   ```
   Actual data is written under `IMOGEN/output/` (correct spelling) and the
   C++ code uses the correct spelling too
   (`Integrations/trunk/trunk_r13078/modules/climatemodel.cpp:875`:
   `dirCommonOut + "/IMOGEN/output/" + thisYear + "/Rh_anom.dat"`). So either
   these `param`s are silently overridden by hardcoded paths in C++, or the
   reads from `./IMOGEN/ouput/...` are silently failing. Either way it is
   misleading.

2. **`R_anom.dat` vs `Rh_anom.dat`** — `imogen_intermediary.ins` line 109 sets
   `param "file_relhum" (str "./IMOGEN/ouput/YYYY/R_anom.dat")` but the IMOGEN
   binary writes `Rh_anom.dat` and the C++ reader reads `Rh_anom.dat`. Same
   file in `Integrations/trunk_r13078_test/integrated-4.1-ins2{,-wsl}/` uses
   the correct `Rh_anom.dat` filename, so the SSP1_RCP26 ins file appears to
   have been hand-edited and broken.

3. **`landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/main.ins` lines 37–38**
   hardcode `/home/bampoh-d/Desktop/landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/gridlist_in_62892_and_climate.txt`
   — a path that lives **outside** the actual `landsymm_lpjg_imogen_coupled_model/`
   checkout and may not exist. The same gridlist is also present alongside in
   the run directory; the absolute path here is a fragile leftover.

4. **`setup_run.sh` calls a script not in the repo.** `setup_run_owl_with_scratch_lpj_work.sh`
   is not present anywhere under the workspace (verified). The framework
   relies on it being installed system-wide on the LSA cluster. Comment block
   in `Integrations/trunk_r13078_test/.../setup_run.sh` mismatches the call
   (says `keal_with_scratch`, calls `owl_with_scratch`).

5. **Imogen-controller `done` path uses Windows separator and wrong subdir.**
   `Imogen-controller/Imogen-controller-cross.cpp:158`:
   `string fileNameDone = commonDirectory + "LPJG_main\\IMOGEN\\done";`
   Both Windows separator (`\\`) and the wrong location (`LPJG_main/IMOGEN/`,
   where there is no `done` file in the actual run output). The actual `done`
   files live in `Common-directory/IMOGEN/output/<YYYY>/done`. Even if the
   controller were started, it would never see them.

6. **Imogen-controller is never invoked from any shipped script.** The
   `Makefile` has a `run` target but `setup_run.sh` does not call it. So the
   2-process file-polling design described in `Imogen-controller/README.txt`
   is dead code as far as the SSP1_RCP26 setup is concerned.

7. **`Data/Imogen/Climate/output/ssp{126,245,370,460,585}/` dirs are empty.**
   They exist as 28 KB worth of empty placeholders; the actual climate is
   written elsewhere (`Common-directory/IMOGEN/output/`). Likely vestigial.

8. **A and B's `SSP1_RCP26/imogen_intermediary.ins` use *different scenarios*
   under the same directory name.** A: `scenario "cmip6"` + SSP1-2.6 emission
   files; B: `scenario "cmip5"` + RCP2.6 emission files. So nominally
   "running SSP1_RCP26 in the cluster setup" runs CMIP5/RCP2.6, not CMIP6/SSP1-2.6.

9. **A `LPJG_CFLUX 1` vs B `LPJG_CFLUX 0`.** Whether IMOGEN takes its land C
   flux from LPJ-GUESS output is configured oppositely between the workstation
   and cluster setups. Probably intentional (B's run is more constrained/
   parallel-safe), but undocumented and easy to get wrong.

10. **Test residue in A.** `landsymm_imogen_setup/landsymm_imogen/SSP1_RCP26/`
    contains `guess.log` (2 bytes — empty newlines) and `qsat_output.txt`
    (24 KB — debug dump from a saturation-humidity routine, columns
    `Index QS T(K) P(Pa)`). These are stale outputs from in-place test
    invocations of `./guess`, not part of the setup template.

11. **NdepFastArchive `Main.cpp` hardcodes a Windows path** `C:\\GitHub\\
    LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\\NdepFastArchive\\bin\\x64\\Debug\\
    GlobalNitrogenDeposition.bin`. Won't compile/link on the cluster without
    edits. No Makefile in the dir.

12. **Matlab/Python plot scripts depend on out-of-repo data.** They reference
    `IIASA_DATABASE/...` and `/content/drive/MyDrive/LPJG_IMOGEN_DATABASE/...`
    paths that the repo does not provide; the IIASA XLSX bundles in
    `Data/Concentrations/IIASA/CMIP6/XLSX/` and `Data/Intermediary/Input/`
    look like they were intended to be the source, but the script paths were
    never updated.

13. **B has no `Data/soil/`.** Cluster runs depend on
    `/bg/data/lpj/bampoh-d/soil/...` existing on shared storage; this is an
    out-of-repo dependency.

14. **No top-level orchestration script.** README explicitly notes that
    "Plans are underway to develop a bash script that will automate the
    simultaneous execution of both models" — that script does not exist.

No string `TODO`, `FIXME`, `HACK`, `XXX` was found inside `landsymm_imogen{,_setup}/`
in either version (clean ins files), but the issues above are de-facto TODOs.

---

## 10. Open questions

1. **Is there *any* working end-to-end runner in the repo as committed?**
   Reading the artifacts on disk, the answer appears to be **no**. The single
   shipped launcher (`SSP1_RCP26/setup_run.sh`) is a one-liner that calls a
   cluster-only helper missing from the repo. There is no `submit*.sh`,
   `launch*.sh`, or `run*.sh` at the framework root. The Imogen-controller
   binary has no caller. Real coupled runs presumably proceed by:
   (a) building `build_imogen/guess` with the `imogencfx` module, then
   (b) cd-ing into `SSP1_RCP26/` and invoking `./guess -input imogencfx
   main.ins` directly (single process).

2. **Is `imogen_intermediary.ins`'s `IMOGEN/ouput/` typo a string-template
   placeholder, dead text, or a real path read?** This needs Subagent 3/4/5
   to confirm whether `param "file_temp"` etc. are consumed at all by the
   `imogencfx` code path (climatemodel.cpp uses a hardcoded `dirCommonOut +
   "/IMOGEN/output/..."` form, which suggests the `param` strings are
   ignored — but then why ship them?).

3. **What runs the IMOGEN binary in the seeded `Common-directory/IMOGEN/output/`
   tree?** The 230 year directories with `done` markers were produced
   2025-06-16 by an "IMOGEN LOGGER" that logs every 4–5 s. Not LPJG-driven.
   Possibly a manually started `IMOGEN-codebase/code/...` build with
   `compile.sh` (covered by Subagent 3). Worth confirming whether it can be
   invoked standalone or only via LPJG.

4. **Why ship A with workstation paths and B with cluster paths committed
   into the same git remote?** They are pushed to the same GitHub repo;
   pulling either to the wrong host immediately breaks paths in 4 ins files.
   A `.envrc`-style mechanism or an `@CONFIG_PATH@` substitution in setup
   would be safer. (Several other LPJG ports use a `runinfo.sh` for this.)

5. **Are the 5 `IMOGEN_SSP{1..5}_RCP{26,45,70,60,85}_Clim/` directories under
   `Common-directory/` (A only, ~2 GB total) intended as canonical climate
   archives consumed by all later runs?** They have the same layout as
   `IMOGEN/output/` and the timestamps suggest they were pre-baked one after
   another. If yes, the setup should symlink or `DIR_COMMON_OUT` into them
   per-scenario; if no, they are stale and could be archived out of git.

6. **Is the `setup_run_owl_with_scratch_lpj_work.sh` helper available
   anywhere in the user's environment, or is it a planned-but-never-shared
   utility?** Worth grabbing a copy and adding to the repo or `tools/`
   directory if it is the actual launcher; otherwise replace `setup_run.sh`
   with something self-contained.

7. **Does the `imogencfx` LPJ-GUESS input module support a single-process,
   shared-memory coupling, or does it actually fork an external IMOGEN per
   year?** Subagent 3/4 should confirm. The on-disk evidence (no separate
   IMOGEN process in any shipped script, but `done` files written nonetheless)
   strongly suggests in-process linkage.

---

**End of report.**
