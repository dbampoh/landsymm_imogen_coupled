# LandSyMM-IMOGEN — Execution Plan, Gap Inventory, and Strategic Decisions

> **Document role**
> This is the operational complement to `COUPLED_MODEL_INVESTIGATION.md`.
> The investigation document tells you *what is wrong*; this document
> tells you *what needs to happen, in what order, with what
> dependencies, with what scientific or operational alternatives, and
> with what residual uncertainties* before the coupled model can run a
> real closed-loop simulation that the working paper can defend.
>
> **Audience**
> The user (the project lead who is writing the GMD paper and will
> own the unified codebase), and any successor or collaborator who
> needs to think through the same decisions.
>
> **Tone**
> Specific, evidence-tied, decision-oriented. Where this document
> recommends an approach, the recommendation is given alongside the
> alternatives so the reader can disagree on first principles. Where
> this document flags something the audit could not resolve, the
> uncertainty is named explicitly so the reader can fill in or ask for
> further investigation.
>
> **How to use this document**
> - Part I (Necessities) is a prioritised checklist of all the items
>   that must be settled before a coupled run can succeed. Each item
>   has a status, a "what needs to happen", a "where in the code or
>   data", a "how (proposed approach)", and a "knowledge gap (where
>   the user might know more than the audit)".
> - Part II (Strategic decisions) walks through the major
>   either-or choices that shape the rest of the work — the kind that
>   change the paper's claims and the codebase's architecture. The two
>   you flagged explicitly (IIASA vs RCMIP for anthropogenic
>   substitution; Fortran vs C++ IMOGEN) are §II.1 and §II.2; the
>   others are unavoidable downstream consequences.
> - Part III (Open questions to the user) is a focused list of items
>   the audit could not answer from on-disk evidence. These are where
>   your own knowledge of the project is most likely to fill in gaps,
>   point me toward code I missed, or correct an assumption.
> - Part IV (Recommended sequencing) folds Parts I-III into a phased
>   plan with rough effort estimates.
>
> **Cross-references**
> All citations to source files use the form `path:line`. Citations to
> the master document use the form `[CMI §x.y]` (master doc section
> x.y) and to the eight subagent reports use `[SAn §x.y]`.

---

## Decisions settled (as of 5 May 2026)

This section records the user-confirmed strategic choices that govern
the rest of this document. Earlier subsections are written
forward-compatibly: where a decision was open at the time of writing
and has since been settled, the relevant subsection notes it
explicitly with a callout.

| # | Decision | Settled choice | Rationale |
|---|---|---|---|
| 1 | Anthropogenic substitution backbone (§II.1) | **RCMIP** | Python pipeline already produces validated outputs against RCMIP; the working paper §2.1.3 adopts the PRIME (Mathison 2025) framing which itself uses RCMIP; RCMIP Phase 2 is built atop IIASA + CEDS + GFED so the underlying scientific content is preserved. The working paper will be updated to cite RCMIP as the substitution backbone alongside IIASA as the upstream scenario source. |
| 2 | IMOGEN implementation strategy (§II.2) | **Phase 1 = Fortran with `ALLOCATABLE` arrays; Phase 2 = C++ refactor brought to numerical parity using Phase 1 as QC reference; both available as switchable backends in v1.0 or v1.1.** | The C++ refactor's heap-allocation IS a real practical benefit at large gridlists (62 000+ cells); revising the Fortran to use `ALLOCATABLE` arrays delivers the same scalability while keeping the working physics. The C++ refactor remains valuable as a second implementation for cross-validation. |
| 3 | LPJ-GUESS fork choice (new — §II.11) | **`trunk_r13078` (the standalone LandSyMM fork) is the canonical Phase-1 LPJ-GUESS; the integrated LTS becomes a switchable Phase-2 backend.** | The framework has historically worked with `trunk_r13078`; preserving that for the immediate rebuild reduces risk of cross-cutting integration issues. The integrated LTS the user previously produced is brought in as a second backend in Phase 2. |
| 4 | Coupling-mode default (§II.4) | **`coupling_mode = tight` (closed-loop) is the default; `prescribed` and `loose` available as opt-in via the same ins parameter.** | The working paper §2.4.3 specifies tight as the canonical mode. Prescribed and loose are valuable for sensitivity studies and reproduce the system's earlier de facto operating mode respectively. |
| 5 | Coupled-model rebuild approach (Part V) | **Build incrementally in `lpj-guess_imogen_landsymm/`, importing one component at a time from A/B with each step ending in a verifiable working state. A/B remain immutable archives.** | Lower risk than fix-in-place. Forces explicit per-component verification. Naturally yields a clean public-quality codebase. |
| 6 | Discipline on units and data-exchange integrity (§I.D) | **Every variable, every file, every transfer between components is documented with explicit units, sign conventions, and column orderings; cross-checked at component boundaries; tested in CI.** | Most of the latent bugs in A/B come from undocumented unit assumptions (the 1.25° vs 0.5° grid-resolution hardcoding, the IYEAR-vs-IYEAR-1 ambiguity, the `calcNitrogenExcretion` factor-10⁶ bug, the Mt CO2 vs Pg C confusions). A discipline of explicit units everywhere prevents recurrence. |
| 7 | Single codebase serves both workstation and cluster | **The unified `lpj-guess_imogen_landsymm/` codebase ships one set of binaries, one Python venv, one `scripts/run_coupled.sh`, and one `scripts/run_coupled.sbatch`; the workstation/cluster choice is made at run time by which launcher is invoked.** | The user's stated requirement: a single public version-controlled codebase that does both. Validated by the existing owl-cluster scripts being thin SLURM wrappers around the same `./guess` binary that runs locally; no separate "cluster build" needed. |
| 8 | Build-environment NetCDF library preference (workstation) | **Anaconda3-provided NetCDF libraries are preferred over native Ubuntu `libnetcdf-dev` on the user's workstation; the unified build documents the Anaconda path and falls back to the native library only if Anaconda is unavailable.** | The user reports that native Ubuntu NetCDF behaves less reliably than the Anaconda3 conda-forge build on their machine. Documenting the preferred path saves a class of "fails to build" support requests for any successor. |
| 9 | Stage I yield-generation scope (§I.B.4 reframed) | **Deferred for v1.0 (PLUM is not embedded; we use already-produced PLUM scenario LU + activity data); preserved in documentation as the design intent for a future v2.0 in which PLUM might be procured/embedded into the coupled framework.** | The user has yields and PLUM outputs from prior work; running Stage I again is unnecessary now. But the working paper §2.4.3 framing of Stage I as a foundational design feature should remain in the documentation so the eventual v2.0 PLUM-embedding effort has a clear specification to build to. |
| 10 | Land-use data strategy (§I.B reframed; new Option D) | **Use `save_state`/`restart` (Option D) to keep historic and scenario LU runs separated: Phase 1 standalone LPJ-GUESS run with HILDA+ historic 1850-2020 → save state at 2020; Phase 2 coupled run starts from 2020 saved state with new PLUM scenario LU 2021-2100 (no concatenation needed). Fallback: legacy concatenated 1901-2100 LU files (Option C) if save_state proves complex at integration time.** | The save_state machinery exists in LPJ-GUESS (used during the integrated-LTS work). It eliminates the concatenation step, naturally maps to the working paper's two-stage protocol, and lets us use the new `landsymm_py` scenario LU directly without column-order remapping. |
| 11 | Tmin/Tmax computation in IMOGEN | **IMOGEN computes `Tmin = T_mean − DTEMP/2` and `Tmax = T_mean + DTEMP/2` and writes `Tmin_anom.dat` and `Tmax_anom.dat`; `imogencfx` reads them and sets `climate.tmin` / `climate.tmax`. ~3 hours of code (small enhancement at step 9.5 of Part V).** | LandSyMM normally takes Tmin/Tmax as inputs (in non-IMOGEN modes). The current design has LPJG derive Tmin/Tmax internally from DTEMP, but explicit IMOGEN-derived inputs let the user verify numerical self-consistency and eliminate a hidden derivation. Fortran path: ~20 LOC. C++ path: ~30 LOC. |
| 12 | Rh_anom and W_anom output asymmetry (§II.2) | **The C++ refactor ALREADY writes `Rh_anom.dat` and `W_anom.dat` (with real engine data, verified at `climatemodel.cpp:875-876, 903-904, 915-916` with `//DKB` annotations); the Fortran does NOT. Phase 1 of the IMOGEN rebuild ports these two writers into Fortran-with-`ALLOCATABLE`. The LPJG-side consumer (`imogencfx::get_climate_for_gridcell`) needs ~30 LOC to read these files and set `climate.relhum` / `climate.u10`.** | The audit's earlier framing of "BLAZE wind/humidity unwired" applied to the consumer side only. The C++ producer side is wired and producing data. Bringing Fortran to parity, plus wiring the consumer, completes the BLAZE / wind / humidity story in one effort. |

These decisions resolve previously open questions in Part II and
Part III. The remaining open items (e.g. whether `do_potyield` is in
`trunk_r13078` or only in the integrated LTS — confirmed by the user
to be in `trunk_r13078`; the HPC environment specifics — to be
confirmed at step 16 with the user's terminal back-and-forth) settle
at the appropriate point in Part V's rebuild sequence.

---

## Table of contents

- [Decisions settled (as of 5 May 2026)](#decisions-settled-as-of-5-may-2026)
- [Part I — Necessities (item-by-item gap inventory)](#part-i--necessities-item-by-item-gap-inventory)
  - [I.A Code-level fixes that are already mapped](#ia-code-level-fixes-that-are-already-mapped)
  - [I.B Major missing components and wiring](#ib-major-missing-components-and-wiring)
    - [I.B.1 LPJG-side writer for the IMOGEN handshake files](#ib1-lpjg-side-writer-for-the-imogen-handshake-files)
    - [I.B.2 Python Intermediary → LPJG-format adapter](#ib2-python-intermediary--lpjg-format-adapter)
    - [I.B.3 Top-level coupled-run launcher](#ib3-top-level-coupled-run-launcher)
    - [I.B.4 Stage-I yield-generation pipeline](#ib4-stage-i-yield-generation-pipeline)
    - [I.B.5 CMIP6 GCM-pattern operationalisation](#ib5-cmip6-gcm-pattern-operationalisation)
    - [I.B.6 Boundary-harmonisation algorithm](#ib6-boundary-harmonisation-algorithm)
    - [I.B.7 NEE/NBP code-vs-doc audit on the LPJG side](#ib7-neenbp-code-vs-doc-audit-on-the-lpjg-side)
  - [I.C Data acquisition and staging](#ic-data-acquisition-and-staging)
  - [I.D Discipline on units and data-exchange integrity](#id-discipline-on-units-and-data-exchange-integrity)
- [Part II — Strategic decisions](#part-ii--strategic-decisions)
  - [II.1 IIASA vs RCMIP for the anthropogenic substitution backbone](#ii1-iiasa-vs-rcmip-for-the-anthropogenic-substitution-backbone)
  - [II.2 Fortran IMOGEN vs C++ refactor](#ii2-fortran-imogen-vs-c-refactor)
  - [II.3 CMIP5 vs CMIP6 emissions / GCM forcing](#ii3-cmip5-vs-cmip6-emissions--gcm-forcing)
  - [II.4 Tight (closed-loop) vs prescribed coupling default](#ii4-tight-closed-loop-vs-prescribed-coupling-default)
  - [II.5 IPCC 2006 vs 2019-Refinement parameter sets](#ii5-ipcc-2006-vs-2019-refinement-parameter-sets)
  - [II.6 N2O sectoral disaggregation methodology](#ii6-n2o-sectoral-disaggregation-methodology)
  - [II.7 Wetland CH4 framing](#ii7-wetland-ch4-framing)
  - [II.8 Year-indexing convention (IYEAR vs IYEAR-1)](#ii8-year-indexing-convention-iyear-vs-iyear-1)
  - [II.9 Tier-1 vs Tier-2/Tier-3 ambition for v1.0](#ii9-tier-1-vs-tier-23-ambition-for-v10)
  - [II.10 NEE/NBP unit and column definition](#ii10-neenbp-unit-and-column-definition)
  - [II.11 LPJ-GUESS fork choice — `trunk_r13078` vs integrated LTS](#ii11-lpj-guess-fork-choice--trunk_r13078-vs-integrated-lts)
- [Part III — Open questions to the user](#part-iii--open-questions-to-the-user)
- [Part IV — Recommended sequencing and effort estimates (deprecated; see Part V)](#part-iv--recommended-sequencing-and-effort-estimates-deprecated-see-part-v)
- [Part V — Formal incremental rebuild plan](#part-v--formal-incremental-rebuild-plan)
- [Appendix A — Implementation sketches](#appendix-a--implementation-sketches)
  - [A.1 LPJG-side handshake writer (sketch)](#a1-lpjg-side-handshake-writer-sketch)
  - [A.2 Python Intermediary → LPJG-format adapter (sketch)](#a2-python-intermediary--lpjg-format-adapter-sketch)
  - [A.3 CMIP6 NetCDF → CMIP5 ASCII converter (sketch)](#a3-cmip6-netcdf--cmip5-ascii-converter-sketch)
  - [A.4 Coupled-run launcher (sketch)](#a4-coupled-run-launcher-sketch)
  - [A.5 RCMIP-vs-IIASA backbone selector (sketch)](#a5-rcmip-vs-iiasa-backbone-selector-sketch)

---

## Part I — Necessities (item-by-item gap inventory)

This part lists, item by item, every piece of work the audit identified
as needed for a successful coupled run. Items are flagged with status:

- **🟢 Mapped** — the issue is clearly understood; the fix is known
  and bounded. Mostly source-file edits.
- **🟡 Partial** — the issue is identified but the fix is non-trivial,
  or has a sub-decision the user should make.
- **🔴 Open** — the audit could not find or specify the fix. The user
  may have knowledge that closes the gap, or further investigation is
  required.

### I.A Code-level fixes that are already mapped

These are the 35 catalogue entries from `[CMI §8.1]`. They are all
🟢 status and listed here only for completeness. See the master doc
for full source citations and proposed fixes; here we just summarise.

| ID | One-line | Status |
|---|---|---|
| C1 | Delete `exit(200);` at `imogencfx.cpp:483` | 🟢 |
| C2, C3 | Restore polling-loop guards in `climatemodel.cpp:330-350` | 🟢 |
| C4 | Uncomment `ndep.getndep(...)` at `imogen_input.cpp:728` | 🟢 |
| C5 | Fix `IMOGEN/ouput/` typo in `imogen_intermediary.ins` (×6) and `R_anom.dat`/`Rh_anom.dat` (×1) | 🟢 |
| C6 | Restore the commented-out Adder/Extractor/Wetlands block in C++ Intermediary `Main.cpp` (or retire C++ Intermediary entirely) | 🟢 |
| C7 | Adopt B's corrected `calcNitrogenExcretion` formula (or retire C++ Intermediary entirely) | 🟢 |
| C8 | Adopt B's corrected `n2ofertilizer.csv` getline (or retire C++ Intermediary entirely) | 🟢 |
| C9 | Fix `Adder::set_actual_lpjg_simulated_IIASA_*` global mutation at `Adder.cpp:239` (currently dead) | 🟢 |
| C10 | Delete `PAUSE` at `imogen_lpjg.f:4134` | 🟢 |
| C11 | Delete `qsat_output.txt` debug dump | 🟢 |
| C12 | Replace Windows `\\` with `/` in `imogen_lpjg.f:435,461` mkdir calls | 🟢 |
| C13 | Replace Windows paths in `imogen_settings.txt` with relative paths | 🟢 |
| C14-C28 | C++ IMOGEN refactor bugs (likely irrelevant — see §II.2) | 🟢 (or moot) |
| C29-C30 | Imogen-controller bugs (likely irrelevant — to be retired) | 🟢 (or moot) |
| C31, C32 | C++ Intermediary config + 1.25° grid (likely irrelevant — see §II) | 🟢 (or moot) |
| C33 | Add `openpyxl` to `requirements.txt` for Python Intermediary | 🟢 |
| C34 | Provide self-contained launcher (see I.B.3) | 🟢 (becomes I.B.3) |
| C35 | Rewrite `FILE_LPJG_FLUX` to relative filenames (only meaningful with I.B.1 + II.4) | 🟢 (depends on I.B.1) |

The 🟢 entries are mostly trivial. The non-trivial ones (C6, C35) are
strategic decisions and reduce to "retire C++ Intermediary in favour of
Python" + "decide tight vs prescribed coupling default" — see Part II.

### I.B Major missing components and wiring

These are the substantive engineering tasks. Each subsection is a
mini-spec.

#### I.B.1 LPJG-side writer for the IMOGEN handshake files

**Status: 🔴 Open — the audit could not locate this writer in the
existing codebase.**

##### What needs to happen

At the end of every LPJ-GUESS simulation year, the coupled framework
needs LPJ-GUESS itself to write three files to
`<DIR_COMMON>/LPJG_main/IMOGEN/`:

1. **`imogen_lpjg.txt`** — the per-call settings file the IMOGEN
   engine reads via `SETTIN_LPJG` (`imogen_lpjg.f:1439-1504`). 6 keys:
   `YEAR1`, `IYEND`, `YEAR1_LPJG`, `SPINUP`, `KEEPRUNNING`, `FIRSTCALL`.
   Written as `key value !comment` ASCII per the format in the
   existing 369-byte placeholder.

2. **`imogen_lpjg_flux.txt`** — the per-year LPJ-GUESS C-flux feedback
   file the engine reads at `imogen_lpjg.f:565-573`. Format:
   `<year> <flux>` per line, where `<flux>` is global net biome
   productivity in TgC/yr (or the unit the engine expects — see §II.10
   for the unit decision). The engine reads `NYR_LPJG_FLUX` rows; a
   year-by-year run would append one row per LPJG year and grow the
   file across years.

3. **`imogen_lpjg_ch4_n2o_flux.txt`** — the per-year LPJ-GUESS natural
   CH4+N2O feedback file. Format: `<year> <ch4> <n2o>` per line.
   Tg CH4/yr and Tg N2O/yr (with the same caveat — §II.10).

Plus the file LPJ-GUESS deletes/recreates as the synchronisation token:

4. **`<DIR_COMMON>/LPJG_main/IMOGEN/done`** — empty file written when
   LPJ-GUESS has finished writing (1)-(3) for the year. The IMOGEN
   engine polls for it (`climatemodel.cpp:330` *should* check this;
   currently bug C2 hardcodes `doneExist=true`).

##### Why it is needed

In a real two-way closed-loop tight-coupled run, the data flow is:

```
LPJG year N completes ─► writes (1)-(3)+(4) ─► engine reads (1)-(3)
   ▲                                                  │
   │                                                  ▼
   ◄───── engine writes IMOGEN/output/<N+1>/done + climate files
                  ◄──── LPJG reads climate, advances to year N+1
```

If LPJG never writes (1)-(3), the engine has nothing real to feed back
into its C-cycle. The current configuration sidesteps this by setting
`FILE_LPJG_FLUX` to a static IIASA reference file (the override
analysed in `[CMI §3.7]` and `[Findings 4]`), which has the side effect
of converting the run from "tight-coupled" to "prescribed-flux". To
get real two-way coupling, LPJG must actually write these files.

##### Where in the codebase

The audit's grep for the literal filenames `imogen_lpjg.txt`,
`imogen_lpjg_flux.txt`, `imogen_lpjg_ch4_n2o_flux.txt` in the LPJ-GUESS
trunk found **only the engine-side READS** (`climatemodel.cpp:300-394`,
`imogen_lpjg.f:357-590`), no writes anywhere on the LPJG output side.
The likely candidate locations for a writer would be:

- **`modules/commonoutput.cpp`** — already writes the standard `cflux.out`,
  `cpool.out`, `mch4.out`, `ngases.out`, etc. per year per gridcell.
  An additional **annual global-aggregation** pass at the end of the
  per-year writer would fit naturally.
- **`modules/miscoutput.cpp`** — already declares the 12 IMOGEN-output
  ins-file params (`miscoutput.cpp:121-136`) and the 12 dead `Table`
  objects (`miscoutput.h:172`); declares the random-number stub
  `getImogenData(int lower, int upper)` at `miscoutput.h:69-79`. This
  was scaffolded for IMOGEN-output integration but never finished.
- **A new module** `modules/imogenoutput.cpp/.h` parallel to the
  existing `imogen_input.cpp` / `imogencfx.cpp`. Cleaner separation.

##### How (proposed approach)

A small new output module that is invoked at the same point as the
standard per-year `commonoutput`. Pseudocode:

```cpp
// modules/imogenoutput.cpp (proposed)
#include "imogenoutput.h"
#include "framework.h"
#include "outputmodule.h"
#include "parameters.h"      // for IMOGENConfig::*
#include <fstream>

REGISTER_OUTPUT_MODULE("imogenoutput", ImogenOutput)

void ImogenOutput::init() {
    // No init needed — files are append-only and created on first call.
}

void ImogenOutput::outannual(Gridcell& gridcell) {
    // Per-gridcell hook; we use this to ACCUMULATE the global sum.
    // Actual file write happens once per year in outglobal_year (a new hook).
    // ...
}

void ImogenOutput::outglobal_year(int calendar_year) {
    if (!IMOGENConfig::tight_coupling) return;     // see §II.4

    const std::string dir = std::string((char*)IMOGENConfig::DIR_COMMON) + "/LPJG_main/IMOGEN/";

    // 1. Flux files — append year row.
    {
        std::ofstream f(dir + "imogen_lpjg_flux.txt", std::ios::app);
        f << calendar_year << "\t" << total_NEE_TgC_yr << std::endl;
    }
    {
        std::ofstream f(dir + "imogen_lpjg_ch4_n2o_flux.txt", std::ios::app);
        f << calendar_year << "\t"
          << total_CH4_TgCH4_yr << "\t"
          << total_N2O_TgN2O_yr << std::endl;
    }

    // 2. Per-call settings file — re-write each year for the next call.
    {
        std::ofstream f(dir + "imogen_lpjg.txt", std::ios::trunc);
        const int next = calendar_year + 1;
        const bool done_all = (next > IMOGENConfig::IYEND_LPJG);
        f << "YEAR1 " << next      << " !IN First year of the numerical experiment\n";
        f << "IYEND " << next      << " !IN Stop year of the ENTIRE run\n";
        f << "YEAR1_LPJG " << IMOGENConfig::YEAR1_LPJG << "\n";
        f << "SPINUP "      << (next < IMOGENConfig::FIRST_HIST_YEAR ? "TRUE" : "FALSE") << "\n";
        f << "KEEPRUNNING " << (done_all ? "FALSE" : "TRUE") << "\n";
        f << "FIRSTCALL FALSE\n";   // first-call only on year 0
    }

    // 3. Touch done file (at end, after everything else is on disk).
    {
        std::ofstream f(dir + "done");
    }
}
```

The accumulation of `total_NEE_TgC_yr`, `total_CH4_TgCH4_yr`,
`total_N2O_TgN2O_yr` would happen via the same area-weighted gridcell
aggregation that the Python Intermediary's Component B already does
(see `src/component_b_natural/historical/lpjg_historical_processing.py`)
— except in C++, in-process, on the live LPJG state rather than from
gzipped output files.

##### Knowledge gaps (where the user might know more than the audit)

1. **Does an LPJG-side writer for these files already exist somewhere
   the audit missed?** The integrated LTS work the user did earlier
   may have included annual flux-flushing infrastructure that I did
   not connect to this need. Worth grepping the integrated LTS
   codebase for `imogen_lpjg`, `IMOGEN/output`, etc.
2. **Was the writer ever started and abandoned?** The
   `getImogenData` random-number stub at `miscoutput.h:69-79` and the
   12 commented-but-declared `Table` objects suggest someone began
   scaffolding this but stopped. Knowing how far it got would inform
   whether to extend the stubs or write fresh.
3. **What is the canonical hook point in LPJ-GUESS for "after a year
   has been written"?** The framework's main loop in
   `framework.cpp` calls `outannual()` per gridcell per year. There
   may already be a "global, post-gridcell-loop, per-year" hook that
   the user knows about; if not, one would need to be added.
4. **Is "global sum" the right LPJG → IMOGEN aggregation level, or
   does IMOGEN expect per-grid (1631-cell) flux fields?** The Fortran
   reader at `imogen_lpjg.f:565-571` reads only `(year, value)`, i.e.
   **scalar per year**. That confirms global aggregation is correct.
   But the user's IMOGEN scientific intent may be different.

#### I.B.2 Python Intermediary → LPJG-format adapter

**Status: 🟡 Partial — the need is fully understood; the only
ambiguity is the IIASA vs RCMIP question (II.1) which determines
which Python output column maps to which LPJG file.**

##### What needs to happen

Convert the Python Intermediary's wide-format scenario CSV
(`outputs/imogen_inputs/imogen_inputs_<SSP>.csv`, 201 rows × 10 cols
per scenario) into the four narrow files the Fortran IMOGEN expects:

| LPJG/IMOGEN file (`imogen_intermediary.ins` key) | Format | Source column in Python wide CSV | Unit conversion |
|---|---|---|---|
| `FILE_LPJG_FLUX` | 2-col `year flux` | `CO2_NEE_Mt` | `Mt CO2/yr → TgC/yr` = divide by `(44/12) × 1000` (the inverse of `PgC_to_MtCO2`) — i.e. `Mt CO2/yr / 3666.67 = PgC/yr × 1000 = TgC/yr × 1`. So `TgC/yr = Mt_CO2/yr / 3.66667`. Cross-check the engine's expected unit by inspecting `imogen_lpjg.f:766-794`. |
| `FILE_LPJG_CH4_N2O_FLUX` | 3-col `year ch4 n2o` | `CH4_natural_Mt`, `N2O_natural_Mt` | Mt-of-gas/yr → Tg-of-gas/yr is **identity** (1 Mt = 1 Tg = 10⁹ kg); no conversion needed. |
| `FILE_SCEN_EMITS` | 2-col `year flux` | `CO2_EFOS_Mt` (or `CO2_total_Mt − CO2_NEE_Mt` depending on II.10 framing) | `Mt CO2/yr → PgC/yr` — same conversion as above |
| `FILE_CH4_N2O_EMITS` | 3-col `year ch4 n2o` | `CH4_anthro_Mt`, `N2O_anthro_Mt` | Identity |

Plus a fifth file that the Python pipeline does *not* produce:

| `FILE_NON_CO2_VALS` | 2-col `year W/m²` | not produced by Python pipeline | Would need to be sourced from FAIR ERF directly, or computed via FAIR step in the adapter |

##### Why it is needed

Without it, the Python Intermediary's `outputs/imogen_inputs/*.csv` are
read by *no one*. The pipeline's `Quick_Start.md` lines 165-166 say
explicitly:
> *"please share the IMOGEN code so I can determine the input data
> form/structure/format requirements and figure out how the 6
> IMOGEN-input CSVs we produce should be transformed for ingestion
> into IMOGEN."*

This adapter is the answer to that request.

##### Where in the codebase

A new file `tools/imogen_inputs_to_lpjg_format.py` in the unified
codebase. Single Python script, ~150 LOC. No new dependencies.

##### How (proposed approach)

See [Appendix A.2](#a2-python-intermediary--lpjg-format-adapter-sketch)
for an implementation sketch.

##### Knowledge gaps

1. **Confirmation of unit expectations.** The Fortran's `C_LPJG`
   variable has a `CONV` multiplier (`imogen_lpjg.f:768-783`) that
   converts the read value before adding to `CO2_PPMV`. Reverse-engineering
   `CONV` would confirm whether the engine wants TgC/yr, PgC/yr, or
   ppm-equivalent. The audit did not trace this in detail; I should
   re-read the apply block before committing.
2. **`FILE_NON_CO2_VALS` source.** The Python pipeline does not
   produce non-CO2 RF directly; the framework ships static IIASA
   reference files at `Data/Imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/
   nonco2_ch4_n2o_RF_historical_ssp126.txt`. For the unified codebase,
   either keep the static file, or compute the FAIR ERF in the
   adapter. The working paper §2.1.3 mentions FaIR v1.3 ERF integrated
   upstream of IMOGEN (per Mathison 2025 PRIME). The Python pipeline
   has FAIR ERF as `inputs/fair_erf/natural.csv`; the corresponding
   anthropogenic FAIR ERF would need to come from FAIR upstream.

#### I.B.3 Top-level coupled-run launcher

**Status: 🟡 Partial — the structure is clear; the cluster-specific
pieces depend on the user's HPC environment.**

##### What needs to happen

Two scripts:

1. **`scripts/run_coupled.sh`** — workstation Linux launcher.
   Self-contained. No external dependencies. One scenario per
   invocation.
2. **`scripts/run_coupled.sbatch`** — cluster SLURM template
   (assumes the user's HPC uses SLURM; the existing
   `landsymm_imogen/SSP1_RCP26/setup_run.sh` references an `owl`
   cluster with `haswell`/`uc2` partition names that suggest LSA
   Lund or KIT — confirm with user).

##### Why it is needed

The current shipped `setup_run.sh` calls
`setup_run_owl_with_scratch_lpj_work.sh`, which is not in the repo.
There is no functional launcher anywhere in either A or B
(`[SA8 §1.3, §3]`).

##### How (proposed approach)

See [Appendix A.4](#a4-coupled-run-launcher-sketch) for an
implementation sketch. The high-level flow:

```
1. Verify build artifacts (./guess, intermediary_py venv).
2. If imogen_inputs_<SSP>.csv missing: run Python Intermediary.
3. If LPJG-format files missing: run adapter (I.B.2).
4. Stage gridlist + soil + Ndep + LU forcing into runs/<SSP>/.
5. Set <DIR_COMMON> to a writable scratch dir; clean any stale
   handshake files.
6. Run ./guess -input imogencfx main.ins.
7. Post-run: collect output, run the standard validation
   (concentration RMSD vs observations).
```

##### Knowledge gaps

1. **The user's HPC environment.** Specifically: which scheduler
   (SLURM, PBS, LSF, none); which queue/partition naming
   convention; which `module load` lines (gcc/cmake/netcdf-c/openmpi
   versions); whether scratch is available and at which path; whether
   MPI is required or single-node is fine; expected wall-clock for
   a 251-year SSP run.
2. **Is `setup_run_owl_with_scratch_lpj_work.sh` available
   anywhere in the user's environment?** If the user has access to
   the Lund LSA cluster, that script could be retrieved and adapted
   — its design is presumably mature. Otherwise we write a fresh one.

#### I.B.4 Stage-I yield-generation pipeline

**Status (revised 5 May 2026): 🟢 Deferred for v1.0; documentation
retained for future v2.0 PLUM-embedding scenario.**

The user has confirmed:
- **Yields already exist.** They have already run LPJ-GUESS with
  `do_potyield=1` and factorial management treatments using the
  LandSyMM fork (per integrated-LTS verification testing in the
  prior integration project). The yield outputs were sent to the
  PLUM modelling team.
- **PLUM outputs already received.** The PLUM team produced scenario
  land use (cropfracs, irrig, nfert) + activity data (livestock counts,
  fertiliser application rates per country) and returned them. These
  are already in `Data/Intermediary/PLUM_data/` (5 SSPs) plus the
  newer `landsymm_py`-derived harmonised LU at `/media/bampoh-d/...
  /plum_harm_lu/`.
- **HILDA+ harmonisation already done.** The user has already
  harmonised PLUM scenario LU with HILDA+ historic via the
  `landsymm_py` codebase (the prior project).
- **`do_potyield` is in `trunk_r13078`.** The user has confirmed
  this; no need to merge from the integrated LTS for v1.0.

So **Stage I is a deferred future capability**, not a current
necessity:

##### What stays in the documentation

The working paper §2.4.3 framing of Stage I (open-loop factorial-
management yield generation: 3 fertilisation × 2 irrigation × 251
years × 0.5°-global) remains documented as the **scientific design
intent**. The unified codebase's `docs/scientific_framework.md` and
the paper's methodology section both retain the Stage I description
as a complete protocol, so anyone reading either understands the
two-stage closed-loop design.

##### What is deferred

The actual **operational machinery for re-running Stage I from
scratch within the unified codebase** is deferred:

- The `runs/stage1_potyield/` ins-file directory: deferred.
- A `do_potyield`-enabled Stage I cluster run: deferred (the
  existing yields are reused).
- Wiring PLUM into the coupled framework as a runtime-callable
  component: deferred to v2.0 (when PLUM may become procurable
  by the user's group).

##### Why preserved as a future-v2.0 capability

If/when the user's group procures PLUM (per the user's note in this
chat), the v2.0 unified codebase will:

1. **Embed PLUM** as a runtime-invokable component in
   `runs/stage1_potyield/`.
2. **Activate the `do_potyield` mode** (already in `trunk_r13078`).
3. **Run the closed-loop two-stage protocol** with PLUM in the inner
   loop:
   - Stage I: LPJ-GUESS factorial yields → PLUM scenario LU + activity → ...
   - Stage II: ... LPJG with PLUM-supplied LU + Intermediary +
     IMOGEN feedback (the v1.0 stage).
4. **Refresh PLUM scenarios** when ESM forcing or LU assumptions
   change.

So preserving the Stage I documentation in v1.0 is forward-looking
investment for v2.0 — the v2.0 work plan inherits a working v1.0
Stage II, plus a documented Stage I specification, plus the existing
yields-and-PLUM-outputs as a frozen reference snapshot.

##### v1.0 implications

For the v1.0 rebuild plan (Part V):

- **Step 15 (Stage I yield generation): deferred for v1.0.** The
  step is renamed from "Stage-I yield-generation pipeline integration"
  to "Stage-I documentation preservation" and reduced to ~2 hours
  (verifying that the existing PLUM outputs are usable as-is, plus
  documenting the Stage I framing for v2.0).
- **Step 6 (data import): use the existing PLUM outputs.** Either
  the legacy `Data/Intermediary/PLUM_data/animals_ssp{1..5}.txt`
  + `plum_land_use/` + `agg_land_use/`, or the newer
  `landsymm_py`-derived `/media/bampoh-d/.../plum_harm_lu/` (per
  Decision #10).
- **Step 7-14 (the Stage II work): unchanged**. Stage II is the v1.0
  focus.

This significantly de-risks the v1.0 release timeline — no need to
verify `do_potyield` (already confirmed present) or run a multi-day
cluster yield-generation job before the coupled framework comes up.

#### I.B.5 CMIP6 GCM-pattern operationalisation

**Status: 🟢 Mapped — the conversion is well-defined; the only
question is whether to do it offline (data-side only) or also extend
the IMOGEN reader to consume NetCDF natively.**

##### What needs to happen

The 5 CMIP6 NetCDF GCM patterns at
`Common-directory/IMOGEN-codebase/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/`
must become consumable by the Fortran IMOGEN. The working paper's
canonical GCM is **MRI-ESM2-0**, which is in this set.

##### Why it is needed

The current active `imogen_settings.txt` `DIR_PATT` points at
`CEN_IPSL_MOD_IPSL-CM5A-MR/` (a CMIP5 GCM, not the working paper's
chosen CMIP6 MRI-ESM2-0). Without this, the framework's runs cannot
reproduce the working paper's claimed scenarios.

##### How (proposed approach)

Two options:

**Option A (recommended): offline conversion.**
1. Write `tools/cmip6_nc_to_cmip5_ascii.py`. For each of the 5 NetCDF
   files (GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0,
   UKESM1-0-LL):
   - Read the 8 `_patt` variables (`tl1_patt`, `ql1_patt`,
     `precip_patt`, `wind_patt`, `pstar_patt`, `swdown_patt`,
     `lwdown_patt`, `range_tl1_patt`) from the 56×96 lat-lon grid.
   - Bilinearly sample onto the 1631-cell IMOGEN HadCM3 land grid
     (`patterns_gridlist.txt`).
   - Write 12 month files (`jan`…`dec`) in the CMIP5 layout: header
     `lon_min lat_min lon_max lat_max`, then `lon lat v1 v2 … v12`
     per cell. Pad zero columns to 12 (matching the CMIP5 12-column
     convention; the existing IPSL-CM5A-MR file has columns 6, 11, 13
     identically zero).
   - Write into a new directory `patterns/CEN_CMIP6_MOD_<gcm>/`.
   - Convert the JSON `<gcm>_params.json` into a Fortran-readable
     namelist for the EBM scalars.
2. Switch `imogen_settings.txt` `DIR_PATT` to `CEN_CMIP6_MOD_MRI-ESM2-0/`.
3. Done — Fortran IMOGEN needs zero changes.

See [Appendix A.3](#a3-cmip6-netcdf--cmip5-ascii-converter-sketch).

**Option B: native NetCDF in IMOGEN.**
Adds NetCDF + JSON readers to the Fortran IMOGEN. More invasive
(~500 LOC of Fortran + the gfortran-netcdf bindings); also requires
on-the-fly regridding from 56×96 to 1631-cell. Long-term cleaner but
not justified for v1.0.

##### Knowledge gaps

1. **The exact column-to-variable mapping in the CMIP5 ASCII format.**
   Subagent 7 inferred 8 forcing variables in 12 columns (with 4
   reserved/zero columns) based on the IPSL-CM5A-MR sample. The exact
   mapping should be confirmed by reading `imogen_lpjg.f::GCM_ANLG`
   `READ` statement at line 3226-3231 — done in §[CMI 4.7.2]:
   `T, RH15M, U-wind, V-wind, LW, SW, DTEMP_day, rainfall, snowfall,
    P*` — i.e. 10 visible. The 12-column layout has 2 extras that
   are zero in the IPSL sample. We can write zeros for them safely.
2. **The `imogen_drive` axis convention in the CMIP6 NetCDF.** Is
   `imogen_drive(0)` January or December? `int64` and no CF `time`
   metadata. Need to confirm with whoever generated the NetCDF
   (likely available from the working paper's authors — it's the
   PRIME framework Mathison 2025 deliverable).
3. **Provenance of the 5 CMIP6 GCM patterns.** Are they all that's
   needed, or will the user want a larger ensemble? CMIP6 itself has
   ~30 GCMs participating in the relevant MIPs.

#### I.B.6 Boundary-harmonisation algorithm

**Status: 🟡 Partial — the algorithm to use is a documentation choice
that the user makes and then the unified codebase implements. See
§II for the choices.**

##### What needs to happen

A method to smooth the IIASA-pre-1961 → IPCC/LPJG-post-1961 boundary
and the historic→scenario 2010/2020 boundary in the integrated
emissions trajectory.

##### Why it is needed

Without boundary harmonisation, the integrated trajectory has
discontinuities at 1961 (or 1990 for CMIP6) and at 2020 — visible
in the Python pipeline's plots and acknowledged in HANDOFF.md §2.5
as a 22 Mt CH4 / 117 Gg N2O step at 2020.

##### Where in the codebase

The Python pipeline currently implements **only segmented running
mean smoothing** at the historical/scenario boundary
(`Intermediary_py/.../HANDOFF.md` §8.6). The C++ Intermediary's
`Adder.cpp:114-164` smoothing block is commented out;
`centeredMovingAverage` is defined but never invoked.

##### How (proposed approach — three options)

| Option | Source | Description | Effort |
|---|---|---|---|
| 1 | Working paper §2.3.4 | **Backward Tapered Harmonisation** (B = 10 yr CO2, 30 yr CH4/N2O) + Regression-Based Trend Matching + 5-yr Centred Moving Average | 1-2 days Python |
| 2 | `Emissions Handling Methodology.docx` (B-only) | **Univariate Spline ratio** of modelled total to IIASA total to align long-term trajectories | 1 day Python |
| 3 | Python pipeline current | **Segmented running mean** at historical/scenario boundary only; no IIASA boundary smoothing | 0 (already done) |

##### Knowledge gaps

The user (and supervisor) wrote the working paper recommending Option
1. The Python pipeline as it stands implements Option 3. Either:
- Implement Option 1 in Python and update the paper to reflect the
  validated outputs, or
- Update the working paper to describe Option 3 (and justify it as
  empirically validated against GCB/GMB/GNB).

This is fundamentally the user's decision based on what the supervisor
will accept.

#### I.B.7 NEE/NBP code-vs-doc audit on the LPJG side

**Status: 🟡 Partial — the documentation says the corrected formula
is implemented; a code-level confirmation has not been done in this
audit.**

##### What needs to happen

Confirm that LPJ-GUESS's `commonoutput.cpp` writes `cflux.out` with
the **corrected** NEE/NBP formula per `NEE-NBP Changes Report.docx`
(B-only):
- `NEE = flux_veg − flux_repr + flux_soil + flux_fire`
- `NBP = NEE + c_disturb`, where
  `c_disturb = flux_est + flux_seed + flux_charvest + acflux_wood_harvest
               + acflux_harvest_slow + acflux_clearing + acflux_landuse_change
               + c_org_leach_gridcell`
- Sign convention: positive = net flux to atmosphere = source.

##### Why it is needed

The downstream consumers of `cflux.out` — the Python Intermediary
Component B, the C++ Intermediary's Adder, any LPJG-side writer for
the IMOGEN handshake (I.B.1) — all assume this corrected formula.
If the code disagrees with the doc, either the consumers must adapt
or the code must be patched.

##### How (proposed approach)

1. Read `Integrations/trunk/trunk_r13078/modules/commonoutput.cpp`
   line by line, looking for the `cflux.out` writer block.
2. Cross-check the column order and formula against the
   `NEE-NBP Changes Report.docx` text:
   - The corrected formula explicitly *adds* `flux_fire` (positive
     fire flux is a CO2 source).
   - The older formula at `Adding NBP…docx` *subtracts* `flux_fire`
     and is wrong.
3. If the code matches the corrected formula, document confirmation
   in the master doc. If not, patch the code to match.

##### Knowledge gaps

The user authored `NEE-NBP Changes Report.docx` (it's dated
2026-03-21 and is in version B's References only, B-authored). They
likely already know whether the code change was applied. Confirming
this is a 5-minute task either by reading the code or asking.

### I.C Data acquisition and staging

These are the data dependencies. Most have been partially or fully
staged in the framework's `Data/`; this subsection clarifies what is
needed for a clean unified-codebase deployment.

| Data | Source | Format | Location in current frameworks | Action for unified codebase |
|---|---|---|---|---|
| **PLUM v2 outputs** | Project-internal (PLUM modeller) | Custom text + zip | `Data/Intermediary/PLUM_data/animals_ssp{1..5}.txt`, `plum_land_use/`, `agg_land_use/`, plus zips for rice option B | Document acquisition path. Provide a converter from this format to `inputs/plum/plum_crop_s1.csv` + `Livestock_counts.txt` (the format the Python Intermediary expects). |
| **HILDA+ v2 historical land use** | Public — Winkler 2021 ESSD | NetCDF | Not raw; pre-processed via `landsymm_py` into `Data/LU/SSP*_RCP*_concatenated/` | Document acquisition + cite `landsymm_py` for processing. |
| **LPJ-GUESS yield surfaces (Stage I outputs)** | Internal (run by user) | LPJG `.out` files | Not on disk; needed for PLUM's input | Run Stage I (per I.B.4); cache outputs in `Data/Yields/`. |
| **LPJ-GUESS coupled-run outputs (.gz files for Python Component B)** | Live coupled run | gzipped LPJ-GUESS standard outputs | `Intermediary_py/.../inputs/lpjg/{historical,scenarios/<ssp>}/lpjg_<var>.out_<tag>.gz` | These come *from* the coupled run itself. Document the gzip step (`gzip cflux.out` etc.) at end of LPJG run. |
| **FAOSTAT bulk download** | Public — fao.org | wide CSV | `Data/Intermediary/Input/FAOSTAT.csv` (combined); `Production_Crops_Livestock_E_All_Data.csv` etc. (Python Intermediary) | Document download URL + version pinned (current is FAO 2025 release). |
| **EDGAR 2025** | Public — JRC | xlsx | `Intermediary_py/.../inputs/edgar/EDGAR_{CH4,N2O}_1970_2024.xlsx` + the OLD ESSD release for 4D11 | Document. Note: requires `openpyxl` (bug C33). |
| **IIASA SSP database** | Public — IIASA SSP DB v2.0 | XLSX + ZIP | `Data/Concentrations/IIASA/CMIP6/`, `Data/Emissions/IIASA/CMIP6/` | Document. **Decide IIASA vs RCMIP** (see §II.1). |
| **RCMIP Phase 2 v5.1.0** | Public — rcmip.org | long CSV | `Intermediary_py/.../inputs/rcmip/rcmip-emissions-annual-means-v5-1-0.csv` | Document. The Python pipeline's substitution algebra uses this. |
| **FAIR ERF v1.3** | Public — github.com/OMS-NetZero/FAIR | CSV | `Intermediary_py/.../inputs/fair_erf/natural.csv` | Document. Anthropogenic ERF would need to be computed if used. |
| **IPCC 2019 Refinement V4** (parameter source) | Public — IPCC | PDF (parameter tables embedded as Python dicts in scripts) | `References/19R_V4_Ch{05,10,11}*.pdf` | Document. Parameter tables would benefit from being moved out of `.py` source into a YAML/JSON config (per [CMI §12.7]). |
| **IMOGEN GCM patterns CMIP5** | Project-internal (Lund) | ASCII per-month files | `Common-directory/IMOGEN-codebase/patterns/CEN_*_MOD_*/` (34 GCMs) | Document. May not all be needed; the working paper uses MRI-ESM2-0 only. |
| **IMOGEN GCM patterns CMIP6** | Project-internal (PRIME deliverable) | NetCDF + JSON | `Common-directory/IMOGEN-codebase/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/` (5 GCMs) | Convert to CMIP5-style ASCII per I.B.5; document. |
| **CRUNCEP base climatology** | Public — Viovy 2018 | ASCII per-month-per-year | `Common-directory/IMOGEN-codebase/CRUNCEP_1960_1989/` | Document. |
| **N-deposition (Lamarque)** | Public — Lamarque 2010+ | FastArchive binary | `Data/Ndep/ndep_cruncep/*.bin` | Document. Reproducible from upstream Lamarque NetCDF + `NdepFastArchive/` utility. |
| **Soil map** | Project-internal | ASCII | `Data/soil/soilmap_center_interpolated.remapv10_old_62892_gL.dat` | Document; provenance unclear. |
| **NOAA GMD / AGAGE concentration observations** | Public — gml.noaa.gov, agage.mit.edu | NetCDF / CSV | Not in repo | Add for validation per [CMI §2.5] thresholds. |

#### I.C.1 Land-use data strategy — Option D (save_state/restart) selected

**Decision settled (5 May 2026, per Decisions table item #10):**
the unified codebase uses LPJ-GUESS's `save_state`/`restart`
machinery to keep historic and scenario LU data separate.

##### The four LU strategies considered

The framework had two candidate LU data sources at audit time:

- **Legacy** (`Data/LU/SSP1_RCP26_concatenated/`): single per-category
  files concatenated 1901-2100 (HILDA+ historic + PLUM scenario,
  pre-harmonised at the 2020 boundary). 4-col schema:
  `Lon Lat Year NATURAL CROPLAND PASTURE BARREN`. ~7.3 GB total.
- **New `landsymm_py`-derived** (`/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/SSP1_RCP26/s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/`):
  scenario-only files starting at 2021. 4-col schema:
  `Lon Lat Year PASTURE CROPLAND NATURAL BARREN` (column order
  swapped vs legacy). Plus a separate `landcover_peatland.txt`. ~3.5 GB total.

Four strategies were considered:

| Option | Approach | Effort | Pros / Cons |
|---|---|---|---|
| A | Concatenate HILDA+ historic 1901-2020 with new PLUM scenario 2021-2100 to produce framework-style 1901-2100 files. Apply 5-yr-window LUH2-style harmonisation at 2020. | 1-2 days Python in `landsymm_py` | Self-consistent with working paper §2.4.5; reproducible; single LU file per category. But adds a concatenation step and a column-order remap. |
| B | Configure LPJ-GUESS to read HILDA+ historic and the new scenario as two separate sources, splicing at runtime in the input module. | 1-2 days C++ in `landcover.cpp`/`landcoverinput.cpp` | Flexible (swap historic source independently); requires non-trivial LPJ-GUESS code change that may interact with `LandcoverInput` design. |
| C | Use the legacy concatenated 1901-2100 files for v1.0; defer the new data to v1.1. | 0 effort | Fastest path to working coupled run; downside is legacy data may be slightly older PLUM than the new. |
| **D** | **Use `save_state`/`restart`: Phase 1 standalone LPJ-GUESS run with HILDA+ historic 1850-2020 → save state at 2020. Phase 2 coupled run starts from 2020 saved state with new PLUM scenario LU 2021-2100 (no concatenation needed).** | **2-3 hours: configure save_state in Phase 1 ins file; configure restart in Phase 2 ins file; verify saved-state file is compatible across runs** | **Avoids concatenation entirely. Avoids re-running 1850-2020 every time we test a scenario. Maps naturally to the working paper's two-stage protocol. The save_state machinery is already in LPJ-GUESS (used during the integrated-LTS work). Uses the new `landsymm_py` data without column-order remap.** |

##### Why Option D is preferred

1. **Architectural cleanliness.** Phase 1 run owns historic; Phase 2
   run owns scenario + coupling. Each is independently testable. A
   change to one doesn't force a re-run of the other.
2. **Computational efficiency.** Once the historic state is saved,
   any number of scenario or sensitivity runs can re-use it. For
   ensemble scenario work this is dramatically faster than re-running
   1850-2020 each time.
3. **Reuse of existing infrastructure.** `save_state`/`restart` is
   already in LPJ-GUESS and was used during the integrated-LTS
   verification testing. No new code required.
4. **Direct use of the new `landsymm_py` data without remapping.**
   The new data starts at 2021 (no historic) and has the
   `PASTURE CROPLAND NATURAL BARREN` column order; the Phase-2
   ins file declares this column order and the data is consumable
   as-is.
5. **Reuses the working paper's two-stage protocol naturally.**
   The "Stage I yield generation" step would itself use save_state
   (Stage I ends with a saved 2020 state; Stage II coupled run
   restarts from it). For v2.0 PLUM embedding, this is a natural
   continuation.

##### Phase 1 (historic) — standalone run setup

```
runs/historic/
├── main.ins                     # imports global.ins, landcover.ins, etc.
├── landcover.ins                # uses HILDA+ historic LU 1850-2020
├── crop.ins, crop_n.ins, ...
├── gridlist_in_62892_and_climate.txt
└── (binaries via symlink to lpjguess/build/)
```

Key ins-file settings:
```
firsthistyear  1850
lasthistyear   2020
save_state     2020             ! save state at year 2020
state_path     "saved_state_2020/"
```

Run via `./guess -input cfx main.ins` (no IMOGEN). Produces
`saved_state_2020/` containing all LPJG state needed for restart.

##### Phase 2 (coupled scenario) — restart setup

```
runs/SSP1-2.6/
├── main.ins                     # imports imogen_intermediary.ins etc.
├── imogen_intermediary.ins
├── landcover.ins                # uses new landsymm_py PLUM scenario LU 2021-2100
├── crop.ins, ...
├── gridlist_in_62892_and_climate.txt
└── (binaries via symlink + saved_state_2020/ symlinked from Phase 1)
```

Key ins-file settings:
```
restart           1
restart_year      2020
state_path        "../historic/saved_state_2020/"
firsthistyear     2021
lasthistyear      2100
```

Run via `./guess -input imogencfx main.ins`.

##### Fallback

If save_state proves more complex than expected at integration
time (rare since the user has used it before), the fallback is
**Option C** (legacy concatenated files). Both paths are documented;
the user/successor can switch via a `runs/SSP1-2.6/main.ins`
parameter change.

### I.D Discipline on units and data-exchange integrity

Most of the latent bugs surfaced by the audit (`[CMI §8]`) come from
**undocumented unit assumptions at component boundaries**. A handful of
representative cases:

| Bug | Underlying issue |
|---|---|
| C7 — A's `calcNitrogenExcretion` off by 10⁶ | `rate*mass*1000/365` was written without comment about expected output unit (kg N animal⁻¹ yr⁻¹ vs g N animal⁻¹ day⁻¹) |
| C32 — `Extractor::cdtarea(lat, lon, 1.25, 1.25)` hardcoded 1.25° resolution | LPJG default is 0.5°; resulting per-cell area was off by a factor of ~6.25 |
| L18 — `F_WET_CLIM_OUT` silently bumps wet-day count to 1 when ≥ 0.5 µm | Unit of "0.5 µm" undocumented; threshold buried in the writer |
| L14 — multiple `IYEAR vs IYEAR-1` TODOs | Year-indexing convention for LPJG-flux year matching unspecified |
| L29 — Magic offset 160 in `Adder::startAddition` | Hardcodes `firstyear=1850` without documenting the assumption |
| Unit-conversion drift between Mt CO2 / Pg C / Tg C / kg C m⁻² yr⁻¹ across LPJG, Intermediary, and IMOGEN | No central units-table; each component declares its own |

The unified codebase enforces unit and data-exchange integrity through
**six concrete disciplines**, applied universally:

#### I.D.1 Per-file canonical units header

Every numeric data file in `data/` and `runs/` and `outputs/` carries
a header comment line (or a sidecar `<filename>.meta.yaml` for binary
files) declaring:

- Column names and order.
- Per-column unit (SI where possible; Mt-of-gas/yr or Tg/yr for GHGs;
  kg C m⁻² yr⁻¹ for per-area fluxes; PgC/yr for global C fluxes).
- Sign convention (positive = source to atmosphere, or positive =
  uptake by land/ocean — must be explicit).
- Spatial resolution (degree × degree if gridded; "global aggregate"
  if scalar).
- Time resolution (annual, monthly, daily).
- Year coverage (first-year, last-year, count).

Example header for `imogen_lpjg_flux.txt`:

```
# imogen_lpjg_flux.txt
# Per-year LPJ-GUESS-derived natural CO2 flux (NEE) for IMOGEN feedback.
# Cols: year [int], flux_PgC_per_yr [PgC/yr; positive = source to atmosphere]
# Spatial: global aggregate (LPJG gridcell sum × area_m2 × 1e-12)
# Time:    annual 1850-2100 (251 rows when complete)
# Source:  LPJ-GUESS commonoutput.cpp / imogenoutput.cpp (live tight-coupled)
#          OR data/imogen/emiss/CMIP6/Co2/co2_pg_emissions_natural_*.txt (prescribed)
1850   0.0540
1851   0.0577
...
```

(Header lines start with `#` so the Fortran `READ(*,*)` skips them
without modification — a small change to the existing reader to skip
`#`-prefixed lines.)

#### I.D.2 Unit-checked adapter functions

Every cross-component adapter (the I.B.2 Python adapter, the I.B.1
LPJG-side writer, the I.B.5 CMIP6→CMIP5 converter) carries explicit
unit-checking assertions at its boundaries. Examples:

```python
# tools/imogen_inputs_to_lpjg_format.py
def write_lpjg_flux(df, outpath):
    """
    Convert Python Intermediary's CO2_NEE_Mt (Mt CO2/yr) to PgC/yr
    and write to FILE_LPJG_FLUX format.

    Pre-condition: df['CO2_NEE_Mt'] is in Mt CO2/yr (positive = source).
    Post-condition: outfile has 'year flux_PgC_per_yr' columns.
    """
    PgC_to_MtCO2 = 44.0/12.0 * 1000.0   # 1 Pg C × (44 g CO2 / 12 g C) × 1000 Mt/Pg
    assert abs(PgC_to_MtCO2 - 3666.6667) < 1e-3, "Conversion constant drift"
    nee_pgc = df['CO2_NEE_Mt'] / PgC_to_MtCO2
    # ... write ...
```

```cpp
// lpjguess/modules/imogenoutput.cpp
void ImogenOutput::outglobal_year(int calendar_year) {
    // accum_NEE_kgC is per-year accumulation: kg C / yr (global sum)
    // CONV is Pg C → ppm CO2 conversion baked into IMOGEN engine,
    // so we must hand IMOGEN the value in PgC/yr (not kg C, not Mt CO2).
    const double NEE_PgC_per_yr = accum_NEE_kgC * 1.0e-12;
    assert(std::isfinite(NEE_PgC_per_yr));
    assert(std::abs(NEE_PgC_per_yr) < 100.0);   // sanity: |NEE| < 100 PgC/yr
    // ... write ...
}
```

#### I.D.3 Central unit-conversion table

A single Python module `intermediary_py/src/shared/units.py` and a
single C++ header `lpjguess/include/units.h` declare the canonical
conversion constants:

```python
# intermediary_py/src/shared/units.py
"""
Canonical unit conversions used across the coupled model framework.
Edit this file — and only this file — when conversion conventions change.
"""

# CO2-related
PG_C_PER_MT_CO2 = 12.0 / (44.0 * 1000.0)   # 1 Mt CO2 = (12/44)*1e-3 PgC
MT_CO2_PER_PG_C = 1.0 / PG_C_PER_MT_CO2    # = 3666.67

# CH4-related
TG_CH4_PER_MT_CH4 = 1.0   # identity (1 Mt = 1 Tg)
PPBV_CH4_PER_TG_CH4 = ...  # FAIR-derived

# N2O-related
TG_N2O_PER_TG_N = 44.0/28.0   # molar mass ratio

# Geometric
EARTH_RADIUS_KM = 6371.0
DEG_TO_RAD = 3.14159265358979323846 / 180.0

# Cell area at 0.5°
def cell_area_m2(lat_deg, dlon_deg=0.5, dlat_deg=0.5):
    """Area of a 0.5° × 0.5° grid cell at given latitude, in m²."""
    R = EARTH_RADIUS_KM * 1000.0
    dlat = dlat_deg * DEG_TO_RAD
    dlon = dlon_deg * DEG_TO_RAD
    return R * R * dlat * dlon * abs(math.cos(lat_deg * DEG_TO_RAD))
```

Both Python pipelines and the C++ Intermediary reference these
constants exclusively; no inline magic numbers.

#### I.D.4 Cross-component validation tests

CI tests verify that the units math at component boundaries is
self-consistent. Examples:

- `tests/test_lpjg_to_intermediary_units.py`: produces a known
  100 PgC/yr LPJG NEE; runs Python Intermediary B; asserts output
  `CO2_NEE_Mt` ≈ 100 × MT_CO2_PER_PG_C ≈ 366667.
- `tests/test_intermediary_to_imogen_units.py`: produces a known
  100 PgC/yr in `imogen_lpjg_flux.txt`; runs IMOGEN one year;
  asserts CO2 ppmv increase ≈ 100 × 0.471 = 47.1 ppm (the engine's
  `CONV` constant).
- `tests/test_n2o_units.py`: confirms 1 Tg N2O = 0.6364 Tg N
  (= 28/44).

#### I.D.5 Sign-convention banner at run start

The `run_coupled.sh` launcher prints a startup banner that
re-declares the active sign conventions and units, so a user
running the system has them visible in the run log:

```
=================================================================
LandSyMM-IMOGEN coupled run, scenario SSP2-4.5
=================================================================
Active conventions:
  NEE / NBP        : positive = source to atmosphere
  CO2 emissions    : Mt CO2/yr (Intermediary) → PgC/yr (IMOGEN), via 1/3666.67
  CH4 / N2O        : Tg-of-gas/yr; 1 Mt = 1 Tg by mass identity
  Year indexing    : LPJG year N flux drives IMOGEN year N+1 climate (IYEAR-1 lookup)
  Cell area        : Earth radius 6371 km; 0.5° × 0.5° grid; spherical
  Coupling mode    : tight (LPJG NEE feeds IMOGEN per-year live)
=================================================================
```

#### I.D.6 Unit drift detection in CI

After every bug fix or refactor, CI compares the run log's banner
against a checked-in reference banner. Any drift (e.g. a constant
that quietly changed from 3666.67 to 3666.67e3) fails the build.

#### I.D.7 Reciprocal producer/consumer checks

The Fortran-vs-C++ IMOGEN climate-output asymmetry the audit
surfaced (Decision #12 in the table above) is a special case of a
broader pattern: **producer and consumer for any data path can drift
independently**. Examples:

- IMOGEN engine writes `Rh_anom.dat` and `W_anom.dat` (in C++ only,
  not Fortran); LPJ-GUESS-side `imogencfx` declares `param "file_relhum"`
  / `param "file_wind"` but does not consume them. Producer wired,
  consumer not.
- LPJ-GUESS commonoutput writes `cflux.out` per the corrected
  NEE-NBP formula (per `NEE-NBP Changes Report.docx`); the Python
  Intermediary Component B reads it expecting the corrected schema.
  If LPJG ever reverts the formula, the Python pipeline silently
  produces wrong NEE.
- The Intermediary writes `imogen_inputs_<SSP>.csv` in 10-column
  wide format (Mt-of-gas/yr); the planned adapter (step 13) writes
  4 narrow files in `Tg/yr` and `PgC/yr`. Three independent unit
  conventions in three places.

The unified codebase enforces reciprocal producer/consumer checks
through:

1. **Per-data-path test fixtures.** Every cross-component data
   path (LPJG → handshake files → IMOGEN; Intermediary → adapter
   → IMOGEN; LPJG output `.out` files → Python Intermediary B
   ingestion) has at least one CI test fixture: producer writes a
   known-value file; consumer reads it; assertion that the consumer's
   parsed value matches the producer's intended value (modulo unit
   conversion).
2. **Schema files.** Each cross-component file format has a `.schema.yaml`
   declaring columns, units, sign conventions, year coverage. The
   producer and consumer both validate against the schema at run time.
3. **Both-backend cross-validation for IMOGEN** (step 16 onwards):
   any time the Fortran IMOGEN and C++ IMOGEN produce divergent
   outputs at NGPOINTS=3, NSDMAX=1 inputs, the divergence is treated
   as a regression and bisected. Phase 2 brings them to numerical
   parity within a documented tolerance; Phase 1 onwards uses the
   parity check as a regression gate.

---

## Part II — Strategic decisions

These are the decisions that meaningfully change the paper's claims,
the codebase's architecture, or the dataset universe. Each subsection
states the decision, lists the alternatives, recommends one with
justification, and flags the consequences.

### II.1 IIASA vs RCMIP for the anthropogenic substitution backbone

**This is the question the user explicitly raised.**

#### II.1.1 What the two datasets are, and how they differ

| Dataset | Source | What it provides | Coverage | Format |
|---|---|---|---|---|
| **IIASA SSP Database v2.0** | International Institute for Applied Systems Analysis | Per-SSP-RCP per-sector emissions trajectories for CH4, CO2 (sub-sector decomposition); N2O (totals only). The "official" CMIP6 forcing dataset for SSP-based ESMs. | 1850-2100 (some pre-1850). All 5 SSPs × 4 RCPs. | XLSX bulk download; per-sector individual CSVs. |
| **RCMIP Phase 2 v5.1.0** | Reduced Complexity Model Intercomparison Project (Nicholls 2020) | Harmonised CMIP6 / SSP-aligned emissions in long-format CSV; designed for forcing reduced-complexity models like FaIR, MAGICC. **Built atop IIASA + CEDS + GFED** with version-controlled harmonisation. | 1750-2500 (huge timeframe). All scenarios. Single CSV. | Long-format CSV with `Variable, Region, Scenario, Y1750..Y2500`. |

The crucial point: **RCMIP Phase 2 is largely a derivative of IIASA**.
Per Nicholls 2020 §2:
- Pre-2014 historical: harmonised CEDS (Hoesly 2018) + GFED (Randerson
  2017) per gas per region.
- 2015-2100 scenarios: IIASA SSP-RCP harmonised to historical at 2015.
- Available aggregations: total `Emissions|<gas>`, sub-sectors
  `Emissions|<gas>|MAGICC AFOLU`, `Emissions|<gas>|MAGICC Fossil and
  Industrial`, etc.

So RCMIP and IIASA are not exclusive: RCMIP repackages IIASA scenario
data and adds CEDS-based historical + per-gas/sector decomposition
that is convenient for substitution work. Anything you can substitute
into RCMIP, you can in principle do with IIASA — RCMIP is a more
operational form of IIASA + CEDS + GFED.

#### II.1.2 What the C++ Intermediary actually uses

`Intermediary/Code/config.txt` and `Adder.cpp::startAddition`
(`[CMI §4.5.4, §9 D8]`) read from per-RCP files like:
- `Data/Intermediary/Input/CMIP5/ch4_n2o_annual_historical_rcp{26,45,60,85}_lpjg_simulated.txt`
- `Data/Intermediary/Input/CMIP5/ch4_n2o_annual_historical_rcp{26,45,60,85}_non_lpjg_simulated.txt`
- `Data/Intermediary/Input/CMIP5/co2_emissions_annual_historical_rcp{26,45,60,85}_{lpjg,non_lpjg}.txt`

These are pre-disaggregated **IIASA** files where someone (the user
or upstream) has already split per-gas totals into "lpjg-simulated
component" (the natural + agricultural fluxes that LPJG and IPCC
tier-1 reproduce) and "non-lpjg-simulated component"
(fossil/industrial/transport/etc.). The Adder substitutes the former
with LPJG+IPCC outputs and keeps the latter at face value.

This is the **explicit IIASA substitution path** the working paper
documents.

#### II.1.3 What the Python Intermediary actually uses

`Intermediary_py/.../src/component_a_anthropogenic/rcmip_substitution/
rcmip_substitution_processing.py` reads from
`inputs/rcmip/rcmip-emissions-annual-means-v5-1-0.csv` and applies:

```
RCMIP_total = column "Emissions|<gas>"           filtered to (Region=World, Scenario=<SSP>)
RCMIP_agri  = column "Emissions|<gas>|MAGICC AFOLU|Agriculture"   for CH4
            = column "Emissions|<gas>|MAGICC AFOLU"               for N2O
Our_agri    = (CH4 enteric + manure + rice) | (N2O manure + soils + synfert)  from Component A historical and scenarios
RCMIP_nonagri = RCMIP_total - RCMIP_agri          (kept unchanged)

New_total = RCMIP_nonagri + Our_agri = RCMIP_total - RCMIP_agri + Our_agri
```

In other words: `New_total = RCMIP_total − RCMIP_agri + Our_agri`.
For 1900-1969 where Component A has no Tier-1 inventory,
`Our_agri = RCMIP_agri` so `New_total = RCMIP_total` (identity).

#### II.1.4 Side-by-side comparison

| Aspect | C++ (IIASA) | Python (RCMIP) |
|---|---|---|
| Scenario coverage | RCP 2.6/4.5/6.0/8.5 (CMIP5 era) | SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP4-6.0, SSP5-8.5 (CMIP6) |
| Aggregation | Pre-split lpjg/non_lpjg per-gas files | Live decomposition `MAGICC AFOLU` vs `total - AFOLU` |
| Historical period | 1850-2010 / 2014 (depending on file) | 1750-2014 from CEDS, 2015+ from IIASA scenarios |
| Sub-sector resolution | Pre-aggregated to "lpjg-simulated" lumps | Per-IPCC-2006-sub-sector resolved via `MAGICC AFOLU\|Agriculture\|...` keys |
| Substitution validity test | None recorded | Pre-1970 Our_agri = RCMIP_agri = identity check |
| Output | Per-RCP per-SSP `total_methane_nitrogen_rcp*ssp*.txt` | Per-SSP `imogen_inputs_<SSP>.csv` 10 cols |
| Unit | Tg/yr per gas (consistent with IMOGEN engine) | Mt/yr per gas (Mt=Tg) |
| Tested against | Pre-existing reference outputs in `Data/Intermediary/Emissions/` | Pre-existing reference outputs in `outputs/component_a/data/`, `_b/data/`, `_c/data/`, `imogen_inputs/`; 39/40 byte-identical reproducibility |
| Documentation | Older, internally inconsistent (paper draft says IIASA + CMIP6, but C++ config has CMIP5) | Self-consistent (HANDOFF.md, TECHNICAL_MANUAL.md, paper-ready) |

#### II.1.5 The user's flag: "in the paper we use IIASA but in the Python pipeline we use RCMIP"

This is a real inconsistency that must be resolved before the paper
can be submitted. There are three possible resolutions:

##### Option A: Update the paper to RCMIP

- Update working paper §2.3 to describe the substitution algebra as
  `New_total = RCMIP_total − RCMIP_agri + Our_agri`, citing Nicholls
  2020 RCMIP Phase 2.
- Note that RCMIP Phase 2 is built atop IIASA + CEDS + GFED, so the
  scientific content is largely preserved.
- Cite both IIASA (the underlying scenario data source) and RCMIP
  (the operational dataset).
- Pro: Python pipeline already produces validated outputs with this
  framing.
- Pro: RCMIP is a more modern, citable, version-controlled dataset.
- Pro: RCMIP's per-gas long-format CSV is much easier to maintain
  than the C++ Intermediary's pre-split per-RCP file system.
- Con: Requires re-running the working paper through the supervisor
  for the methodology change.

##### Option B: Operationalise IIASA in the Python pipeline

- Add an alternative ingestion path in
  `src/component_a_anthropogenic/iiasa_substitution/` parallel to
  `rcmip_substitution/`. Reads the IIASA SSP DB XLSX downloads at
  `Data/Concentrations/IIASA/CMIP6/`. Produces the same
  `iiasa_substitution_{ch4,n2o}.csv` schema.
- Document both modes; default to IIASA to match the paper.
- Pro: Paper is unchanged.
- Con: Significant Python work — re-implement what Component A's
  RCMIP path does, against IIASA's different format and fewer
  sub-sector keys (IIASA splits CO2/CH4 to component level but N2O
  as totals only — see `Emissions Handling Methodology.docx` §2).
- Con: Loses the Python pipeline's validated reproducibility against
  RCMIP-based outputs.

##### Option C: Use both (IIASA primary, RCMIP for validation)

- Keep Python's RCMIP path for what it does best (validation against
  `MAGICC AFOLU`).
- Add an IIASA path for the substitution backbone the paper describes.
- Document the two as alternative `--backbone IIASA|RCMIP` modes.
- Pro: Maximum flexibility; paper can show both in supplementary
  material.
- Con: Most work; ongoing maintenance of two parallel pipelines.

##### Recommendation

**Option A — selected (5 May 2026).** RCMIP becomes the canonical
substitution backbone in the unified codebase and the paper. RCMIP
is the operational standard for FaIR-driven runs (which the working
paper §2.1.3 explicitly adopts — *"follows the approach implemented
in the PRIME framework (Mathison et al., 2025)"*); PRIME also uses
RCMIP. Switching the paper to RCMIP brings it in line with the
codebase, with PRIME, and with the forward-looking standard.

The paper's methodology section will be revised to:
1. Cite **Nicholls et al. 2020 RCMIP Phase 2** as the substitution
   backbone for the anthropogenic CH4/N2O substitution algebra
   (`New_total = RCMIP_total − RCMIP_agri + Our_agri`).
2. Cite **IIASA SSP DB v2.0** as the upstream scenario data source
   that RCMIP harmonises with CEDS + GFED.
3. Document the substitution algebra explicitly with the per-gas
   pre-1970 / 1970-2019 / 2020-2100 regime split (the existing
   Python pipeline already implements this — see HANDOFF.md §2).

If, during paper revision, the supervisor pushes back, **Option C**
(support both IIASA and RCMIP via a `--backbone` selector) is the
fallback that preserves the Python pipeline's validated outputs
while honouring an IIASA paper claim. Implementation sketch is in
Appendix A.5.

The C++ Intermediary's IIASA-CMIP5 path (the source of the
contradictions D3, D4, D5 in `[CMI §9.1]`) is retired alongside the
broader retirement of the C++ Intermediary in favour of the Python
pipeline.

#### II.1.6 Implementation sketch for Option A or C

See [Appendix A.5](#a5-rcmip-vs-iiasa-backbone-selector-sketch).

#### II.1.7 Knowledge gaps

1. **Did the supervisor specifically endorse IIASA in the review of
   the working paper?** Or was IIASA the default the user used and
   the supervisor did not push back?
2. **Did the paper explicitly cite Nicholls 2020 RCMIP Phase 2?**
   If yes, switching to RCMIP is a re-naming, not a re-methodology.
3. **Are RCMIP's `MAGICC AFOLU|Agriculture` sub-sectors a
   *strict subset* of what IIASA's per-sector `lpjg_simulated`
   file contains?** This determines whether RCMIP can fully replace
   IIASA without losing scenario-period CH4 detail. For CH4, RCMIP
   has Agriculture sub-key. For N2O, RCMIP groups all of AFOLU into
   one. This may matter if the substitution wants finer N2O detail.

### II.2 Fortran IMOGEN vs C++ refactor

**This is also a question the user explicitly raised.**

#### II.2.1 The state of the two implementations

| Aspect | Fortran (`Common-directory/IMOGEN-codebase/code/imogen_lpjg.f`) | C++ refactor (`IMOGENCXX/ImogenCXX/src/Main.cpp`) |
|---|---|---|
| Status | **Working** (after 7-line fix: remove `PAUSE`, fix `mkdir \`) | **Non-functional** (25 distinct bugs; never run end-to-end) |
| LOC | 4 138 + 174 (`imogen_lpjg.f` + `nonco2.f`) | 2 631 (single TU, no headers) |
| Build system | `Makefile` + `compile.sh` (gfortran) | None at all (no CMakeLists, no Makefile) |
| Compilers tested | gfortran ≥ 7 | MSVC (Windows); never built on Linux |
| Sub-daily disaggregation | `DAY_CALC` is 462 lines, complete | `DAY_CALC` is empty stub (lines 1149-1162) |
| Solar position | `SOLPOS` is 60-line orbital-elements routine | `SOLPOS` is 1-line sinusoid placeholder |
| `DTEMP_OUT` | Computed and written | Assignment commented out (line 1293) |
| Year loop | proper `DO WHILE (KEEPRUNNING)` | `} while (KEEPRUNNING = true);` infinite loop (line 2626) |
| `done`-file polarity | **Deletes** acknowledged file (correct) | **Creates** instead of deletes (line 784-792, polarity inverted) |
| Spin-up state | `DO I=1,N_OLEVS; DTEMP_O(I)=0; ENDDO` | `for (i=1; i<N_OLEVS; i++) DTEMP_O.push_back(0)` — **appends instead of zeros** (line 2044-2058) |
| Settings file path | `OPEN(81, FILE='imogen_settings.txt')` (relative, working dir) | `std::ifstream("C:\\GitHub\\dbampoh\\…\\imogen_settings.txt")` (Windows absolute, hardcoded) |
| `system("pause")` / Windows API | `PAUSE` only (a Fortran intrinsic, easy to delete) | `system("pause")` (Windows shell call) AND `localtime_s` (Windows-only API) |
| Output formatting | `WRITE(95,'(i10)', …)` for `WET.dat` (integer fixed-width) | `<< std::fixed << setprecision(3)` (float format, integer values lost) |
| Files-on-disk-now from earlier runs | `Common-directory/IMOGEN/output/<YYYY>/` 230 dirs from 2025-06-16 (Fortran-produced) | None (never run end-to-end) |
| Gridlist size | `PARAMETER NGPOINTS=3698` — recompile to change | `const int NGPOINTS = 3698` — recompile to change |
| Memory model | Static / stack arrays | Heap (`std::vector`) — sidesteps Windows stack-overflow but doesn't enable runtime gridlist sizing |
| Faithfulness to physics | 100% (it's the original) | Structurally faithful for ~80% of subroutines; functionally incomplete on the rest |

#### II.2.2 The "larger gridlist" claim — corrected (5 May 2026)

The user's original motivation for the C++ refactor was that the
Fortran couldn't handle larger gridlists (the Fortran caps out around
~3700 cells; the user has run 62000-cell gridlists with the C++).
**An earlier draft of this document and `[CMI §4.3.3]` characterised
the C++ benefit as "mostly false". That framing was technically true
but practically misleading; the corrected analysis is below and is
also reflected in the updated `[CMI §4.3.3]`.**

The actual gridlist limitation has two components:

- **Internal IMOGEN grid `GPOINTS=1631`** is a hard cap in *both*
  Fortran and C++ tied to the underlying CMIP5 ASCII pattern files +
  CRUNCEP base climatology files. Changing it requires regenerating
  those files. In practice no one needs to.

- **Output user-facing gridlist `NGPOINTS=3698`** is the limit that
  matters. Both versions cap it via a compile-time constant. But the
  practical consequence at large gridlist sizes is **completely
  different** because of the memory-allocation strategy:

  | Aspect | Fortran (current) | C++ (current) |
  |---|---|---|
  | Array declaration | `REAL T_OUT_M_REGRID(NGPOINTS, 12, 32, NSDMAX)` | `std::vector<...>(NGPOINTS, ...)` |
  | Storage | BSS (uninitialised data segment) or stack | Heap |
  | Size at NGPOINTS=3698 | ~273 MB per `_REGRID` array; ~1.1 GB total for 4 such | Same |
  | Size at NGPOINTS=62000 | ~4.6 GB per array; ~14 GB total | Same |
  | Behaviour at NGPOINTS=62000 | **Fails at link/startup/first-reference** (BSS reservation exceeds default; stack overflows) | **Works on a system with ≥32 GB RAM** (heap allocation succeeds) |
  | Workarounds | `ulimit -s unlimited`, `-mcmodel=large`, hand-conversion to `ALLOCATABLE` (a real source-code change) | None needed |

So the C++ refactor's "larger gridlist" benefit is **real and
practical** — recompile with `const int NGPOINTS = 62000;` and run
on a workstation with ≥32 GB RAM works. The Fortran with the same
recompile dies at startup. That said, the benefit is *not* "runtime
configurable" — both still require recompile.

The right fix is not "keep C++ because of gridlist scalability"; it
is **"fix the Fortran's static allocation"** by converting the ~30
arrays that scale with `NGPOINTS` or `GPOINTS` into `ALLOCATABLE`
declarations and adding `ALLOCATE` calls keyed off the gridlist file
length. Modern gfortran (≥4.6) supports this fully. The Fortran-with-
ALLOCATABLE then has the same heap-allocation scalability the C++
already has, while keeping its complete and tested physics.

#### II.2.3 Effort comparison to bring each to a working state

**Fortran path:**
- Fix `PAUSE` in `QSAT` (1 line).
- Fix Windows `mkdir \\` paths (2 lines).
- Replace `imogen_settings.txt` Windows paths with relative
  paths or `$VARS` (10 lines + a setup script).
- Optional: increase `NGPOINTS` parameter and recompile, validate
  memory.
- **Total: 1-4 hours.**

**C++ refactor path:**
- Port the empty `DAY_CALC` from Fortran (462 lines of Fortran →
  ~600 lines of C++).
- Port the placeholder `SOLPOS` (60 lines of Fortran → 80 lines C++).
- Fix `DTEMP_OUT` assignment (1 line).
- Fix infinite year loop (1 character: `=` → `==`).
- Fix `done` polarity (replace `ofstream done(path)` with
  `std::filesystem::remove(path)`, ~3 lines).
- Fix spin-up vector init (replace `push_back(0)` with `std::fill`).
- Fix `OCEAN_CO2` indexing (1 line).
- Fix wrong flag passed to `FAIR_NON_CO2_GHG_BUDGET` (1 line).
- Fix Windows path separators (~5 places).
- Replace `localtime_s` and `system("pause")` (2 lines).
- Fix `ofstream` lifetime for per-year append files (~10 places).
- Fix `WET.dat` integer formatting (1 place).
- Fix duplicate first entry in `ES[]` table (1 line).
- Fix `SUNNY` off-by-one.
- Add a build system (CMakeLists or Makefile, ~30 lines).
- Add headers and split into multiple TUs (~200 lines of
  refactoring).
- Numerical-parity test against Fortran, gridcell-by-gridcell,
  year-by-year. This is the long pole — debugging numerical
  differences is hard.
- **Total: 1-3 weeks of careful porting + testing.**

#### II.2.4 Why the Fortran-with-ALLOCATABLE path is recommended (settled)

1. **Already working physics.** The Fortran has 230 year-dirs of
   validated output on disk; the C++ has none. All sub-daily
   disaggregation, orbital geometry, and EBM dynamics are implemented
   and have been used in published IMOGEN papers (Huntingford 2010,
   Zelazowski 2018, Hayman 2021, Mathison 2025 PRIME). The C++ has
   only ~80% of this — `DAY_CALC` is a 462-line empty stub.
2. **Compilation is trivial.** Single `gfortran` line, no
   dependencies, builds on every Linux distro and every HPC cluster.
3. **The gridlist scalability gap is closeable in 1-2 days.** The
   `ALLOCATABLE` refactor is bounded: identify the ~30 statically-
   declared arrays in `imogen_lpjg.f` and `nonco2.f` (the audit
   already lists them in `[SA3 §10]`), convert each declaration to
   `ALLOCATABLE`, add an `ALLOCATE` block at the top of the year
   loop or in `init` once `NGPOINTS` is known. Modern gfortran
   handles this without difficulty.
4. **The user's Linux-only declaration eliminates the Windows
   stack-overflow rationale** that motivated the C++ rewrite — and
   the heap-allocation benefit the C++ delivers can be replicated
   in Fortran via `ALLOCATABLE` without any of the C++'s 25 bugs.

#### II.2.5 The C++ refactor — preserved and brought to parity in Phase 2

**(Revised 5 May 2026 — earlier framing said "archive". This
recommendation has been updated to align with the user's preference
to have both implementations available eventually.)**

Phase 2 of the IMOGEN rebuild brings the C++ refactor to numerical
parity with the Fortran-with-ALLOCATABLE, using Fortran outputs as
the QC reference:

1. **Numerical-parity test infrastructure first.** Build a script
   that runs both backends on a 3-cell × 3-year smoke test, dumps
   `T_anom.dat`, `P_anom.dat`, `SW_anom.dat`, `WET.dat`,
   `DTEMP_anom.dat`, `CO2.dat` from each, and compares element-wise.
   Any divergence > `EPSILON` (the Fortran's documented numerical
   tolerance) is a regression.
2. **Fix the 25 catalogued bugs in `Main.cpp`** ([CMI §4.3.4],
   [SA4 §10] B1-B25). In priority order:
   - B7 (infinite year loop): `KEEPRUNNING = true` → `KEEPRUNNING == true`.
   - B1 (settings path): replace `C:\GitHub\dbampoh\…\imogen_settings.txt`
     with `getenv("IMOGEN_SETTINGS")` fallback `"./imogen_settings.txt"`.
   - B4 (DAY_CALC empty): port from Fortran `imogen_lpjg.f:1511-1972`.
   - B5 (SOLPOS placeholder): port from Fortran `imogen_lpjg.f:2267-2330`.
   - B6 (DTEMP_OUT not assigned): uncomment line 1293.
   - B8 (done polarity inverted): change `ofstream(done_path)` to
     `std::filesystem::remove(done_path)`.
   - B9 (spin-up push_back): replace with `std::fill`.
   - B10 (wrong flag passed to FAIR_BUDGET): pass
     `NONCO2_EMISSIONS_LPJG` not `NONCO2_EMISSIONS`.
   - B11 (Windows clim path separator): replace `\\` with `/`.
   - B12 (ofstream lifetime for per-year append): open once outside
     the IYEAR check.
   - B14 (WET.dat float format): use `setw(10)` integer cast.
   - B16 (ES table duplicated first entry): delete duplicate.
   - C2-C3, C15, C20, C24-C28, C29-C30 from `[CMI §8.1]`: misc.
3. **Add a build system.** A single `CMakeLists.txt` (~30 lines)
   targeting C++17 (`std::filesystem` requires this).
4. **Numerical parity check after each bug fix.** Run the smoke
   test; commit each fix individually so any divergence introduction
   can be bisected.
5. **Gridlist-scalability check.** Recompile with
   `const int NGPOINTS = 62000;`. Confirm 32-GB-RAM workstation runs
   complete without OOM.
6. **Both backends exposed via switchable parameter.** Add a
   `imogen_backend "fortran"` or `imogen_backend "cxx"` setting
   in `imogen_intermediary.ins`, or alternatively expose two
   binaries `imogen_lpjg_fortran` and `imogen_lpjg_cxx` that
   LPJ-GUESS picks between via the build configuration.

Effort estimate: 1-3 weeks of careful porting + parity testing.
Schedule for v1.1 or post-v1.0; not required for v1.0 release.

#### II.2.6 Knowledge gaps

1. **Did the user write the C++ refactor or inherit it?** If
   inherited, the Phase 2 fixes are uncomplicated — port from
   Fortran, fix bugs, parity test. If written by the user, Phase 2
   is also fine: the user has full design authority.
2. **Was the C++ refactor's Windows-only character a deliberate
   restriction (for a Windows-based collaborator) or a bug?** The
   user's Linux-only declaration suggests the latter; Phase 2 fixes
   Windows-isms as part of the bug fixes.

### II.3 CMIP5 vs CMIP6 emissions / GCM forcing

#### II.3.1 The current state

Across the framework:
- Working paper: CMIP6 + SSP1-2.6 + SSP2-4.5 + ISIMIP-3b MRI-ESM2-0.
- Older paper draft: CMIP5 + SSP1+SSP5 + IPSL-CM6-MR.
- `imogen_settings.txt` (Fortran active): IPSL-CM5A-MR (CMIP5 GCM).
- `imogen_intermediary.ins` A: `scenario "cmip6"` + SSP1-2.6 emiss files.
- `imogen_intermediary.ins` B: `scenario "cmip5"` + RCP2.6 emiss files.
- `Intermediary/Code/config.txt`: `scenario=cmip5, ssps=1,5, rcps=26,85`.
- Python pipeline: RCMIP Phase 2 (CMIP6-aligned).
- GCM patterns on disk: 34 CMIP5 + 1 CMIP3 + 5 CMIP6 (NetCDF).

#### II.3.2 Resolution

The framework should commit to **CMIP6 throughout**:
- Fortran IMOGEN reads CMIP6-converted ASCII patterns (per I.B.5).
- `imogen_intermediary.ins` is rewritten to consistent CMIP6/SSP1-2.6
  + SSP2-4.5 paths.
- `Data/Imogen/emiss/CMIP6/` becomes the canonical emissions input.
- `Data/Imogen/emiss/CMIP5/` is archived.
- The Python Intermediary is already CMIP6-aligned.

This is a single-line update to two ins files plus a directory rename.
The CMIP5 patterns can be retained for sensitivity studies but
the default GCM in `imogen_settings.txt` becomes
`CEN_CMIP6_MOD_MRI-ESM2-0/` after the conversion.

### II.4 Tight (closed-loop) vs prescribed coupling default

This is the decision flagged in `[CMI §3.7]` / Finding 4 of the
re-investigation.

#### II.4.1 The two modes

**Tight coupling (the working paper's intent):**
- LPJ-GUESS year N → produces NEE/CH4/N2O fluxes.
- These flow to IMOGEN year N+1 via `imogen_lpjg_flux.txt`,
  `imogen_lpjg_ch4_n2o_flux.txt`.
- IMOGEN's climate trajectory is a function of LPJG's behaviour.

**Prescribed coupling (the current default, by accident):**
- `FILE_LPJG_FLUX` points at a static IIASA reference file.
- IMOGEN reads the static file every year regardless of LPJG state.
- LPJG's NEE/CH4/N2O do not influence the climate.
- Useful for sensitivity studies (varying GCM patterns or atmospheric
  parameters while keeping fluxes fixed) but **not what the paper
  describes**.

#### II.4.2 Recommendation

The unified codebase should **default to tight coupling** and offer
prescribed as an explicit, named, opt-in mode via a `coupling_mode`
ins parameter:

```
coupling_mode "tight"        ! default: real two-way; LPJG fluxes feed back
! coupling_mode "prescribed"   ! sensitivity mode: read static reference fluxes
! coupling_mode "loose"        ! pre-generated IMOGEN climate; LPJG runs after
```

Implementation: a startup banner that prints the active mode, plus a
runtime check that the mode's preconditions are satisfied (per
`[CMI §3.7.6]`). For tight mode: `FILE_LPJG_FLUX` must be a relative
filename, the LPJG-side writer (I.B.1) must be wired, and the file
must start empty or with the spin-up year only. For prescribed mode:
the override paths must exist with the right number of rows.

#### II.4.3 Consequence

This decision cleanly resolves bug C35. It also means the unified
codebase has documented support for the **two scientifically
distinct experimental setups** that the framework's current ad hoc
configuration conflates.

### II.5 IPCC 2006 vs 2019-Refinement parameter sets

The Python Intermediary uses 2019 Refinement parameters for scenarios
but 2006 Guidelines parameters for historical, producing a step at
2020 (633 Gg N2O at 2020 historical vs 750.6 Gg SSP2 at 2020 scenario,
HANDOFF.md §2.5). The C++ Intermediary's parameter year is undocumented
in the code (the EFs are hardcoded in `Maps.h` without source citation
beyond comments naming "Chapter 10").

**Recommendation:** unify on **IPCC 2019 Refinement** for both
historical and scenarios. Document the change in HANDOFF and TECH
manuals. The 2006 → 2019 refinement updates are well-documented
(IPCC AR5 → 2019 Refinement Vol 4 Chs 10/11) and the discontinuity
disappears.

If the supervisor prefers the current 2006-historical / 2019-scenario
split, document it explicitly and add a `boundary_smoothing` step at
2020 to mask the discontinuity (per I.B.6).

### II.6 N2O sectoral disaggregation methodology

`Brief Documentation of N2O Disaggregation Methodology.docx` (the
OUTDATED doc) uses a static 59.81%/40.19% LPJG/non-LPJG split based
on Ciais 2013 IPCC AR5 Ch6 Table 6.9.

The working paper §2.3.2 prescribes a **dynamic temporal-based
proportion** sourced from Tian 2024 GNB.

The Python pipeline currently applies the dynamic method (per
HANDOFF.md cross-references to Tian 2024 — see GNB references).

**Recommendation:** stick with the dynamic Tian 2024 method (the
working paper's choice); retire the static doc. The Tian 2024 PDF is
already in `References/essd-16-2543-2024_GNB.pdf`.

### II.7 Wetland CH4 framing

Three potential framings:
1. Working paper §2.2.7: LPJ-WHyMe (Wania 2010) wetlands >40°N;
   tropical = IIASA residual (acknowledged bias); managed peatlands
   disabled.
2. Older `Imogen_paper_GMD.docx`: GSW DB max-water-extent static.
3. Python pipeline: LPJG `mch4.out` + GMB IFW (+112) − DCC (−23)
   constants applied uniformly 1901-2100.
4. C++ Intermediary: GLWD3 area-based Tier 1 Eq 3A.1 with
   year-broadcast — but already retired in the active C++ Adder
   logic (`removed methane here since LPJG is producing it now |
   30.05.2023` comment at `Adder.cpp:92,96`).

**Recommendation:** working paper § 2.2.7 + Python pipeline's IFW/DCC
correction = the most consistent picture. LPJ-WHyMe handles >40°N
explicitly via the wetland PFTs (`wetlandpfts.ins`); IIASA non-modelled
component covers tropical wetlands and other non-LPJG sources; GMB
IFW/DCC corrections are applied at integration time as a constant
adjustment.

This is fundamentally what the Python pipeline already does. The
unified codebase preserves this and the working paper §2.2.7 prose
matches.

### II.8 Year-indexing convention (IYEAR vs IYEAR-1)

Multiple TODO comments in the Fortran (`imogen_lpjg.f:751,772;
nonco2.f:107,127`) flag uncertainty over whether emissions/fluxes for
IYEAR should be read from row IYEAR or IYEAR-1.

**Why it matters:** affects C-budget closure between LPJG and IMOGEN.
A one-year offset in the flux read could shift the cumulative
atmospheric CO2 trajectory by ~0.5 ppm at end-of-century — small
but detectable.

**Recommendation:** **IYEAR-1 is the correct convention.** Reasoning:

- LPJG completes its simulation of year N and writes
  `imogen_lpjg_flux.txt` with row `<N> <flux_for_year_N>`.
- IMOGEN, at the start of year N+1, reads the file and applies
  `flux_for_year_N` as the previous year's land-atmosphere exchange,
  influencing atmospheric CO2 entering year N+1.
- So when IMOGEN is on `IYEAR=N+1`, the relevant LPJG flux is for
  `IYEAR-1 = N`.

The Fortran code's `IF(YR_LPJG(N).EQ.IYEAR-1) THEN` at `imogen_lpjg.f:751`
is therefore correct. The duplicate commented `IF(YR_LPJG(N).EQ.IYEAR)`
should be deleted.

### II.9 Tier-1 vs Tier-2/Tier-3 ambition for v1.0

The working paper §2.4.6 acknowledges Tier-1 limitations
(rice +15-40%, managed-soil N2O −20-30%, blended EF1 −6-7%). The
Python TECHNICAL_MANUAL §15 lists Tier-2/Tier-3 as future work.

**Recommendation:** ship v1.0 with Tier-1 only and document the
limitations. Add Tier-2 sectors (e.g. region-specific EFs for
temperate vs tropical livestock) as a v1.1 / v2.0 enhancement.
Building Tier-2 into v1.0 doubles the scope and delays the paper.

### II.10 NEE/NBP unit and column definition

The Fortran IMOGEN reads `<FILE_LPJG_FLUX>` as `(year, value)` where
`value` enters as `C_LPJG(N)`. At the apply site (`imogen_lpjg.f:776-777`):

```fortran
C_LPJG_LOCAL = C_LPJG(N)
D_LAND_ATMOS = CONV * C_LPJG_LOCAL
CO2_PPMV = CO2_PPMV + D_LAND_ATMOS
```

`CONV = 0.471` is the `PgC → ppm CO2` conversion constant
(`imogen_lpjg.f:73`: `1 PgC = 0.471 ppm CO2 atmospheric concentration`).

**So the engine expects `C_LPJG` in PgC/yr.** Sign: positive flux to
atmosphere = positive CO2 increment. If LPJG NEE is computed per
`NEE-NBP Changes Report` with positive = source convention, the unit
conversion from LPJG's typical `kg C m⁻² yr⁻¹` × area is:

```
Per-cell: flux_NEE_kgCm2yr × cell_area_m2 = kgC/yr/cell
Global:   sum over cells = kgC/yr × 1e-12 = PgC/yr
```

The Python Intermediary's Component B handles this via the
`PgC_to_MtCO2 = 44/12 × 1000 = 3666.67` constant. The adapter (I.B.2)
needs to invert this to write PgC/yr to the flux file.

**Recommendation:** explicitly document the unit in the unified
codebase's `runs/<SSP>/imogen_intermediary.ins`:

```
! FILE_LPJG_FLUX: 2-col (year, flux_PgC_per_yr); positive = source to atmosphere
FILE_LPJG_FLUX "imogen_lpjg_flux.txt"
```

For the CH4/N2O flux file, the Fortran reader at `nonco2.f:50` uses
`CH4_LPJG(N)` and `N2O_LPJG(N)` directly in the box-model concentration
update. Unit-checking at `nonco2.f:60-90` shows Tg/yr per gas (the
FAIR Tg/yr → ppbv conversion uses molar masses of 16.04 g/mol CH4
and 44.013 g/mol N2O). So:

```
! FILE_LPJG_CH4_N2O_FLUX: 3-col (year, ch4_TgCH4_per_yr, n2o_TgN2O_per_yr)
FILE_LPJG_CH4_N2O_FLUX "imogen_lpjg_ch4_n2o_flux.txt"
```

### II.11 LPJ-GUESS fork choice — `LandSyMM_LPJ-GUESS` (v1.0) vs `trunk_r13078` (backport target)

**Decision settled (5 May 2026, terminology clarified 6 May 2026):
v1.0 development happens on `LandSyMM_LPJ-GUESS/` (the user's
"integrated LTS" per their integration-project terminology).
`trunk_r13078` is the **backport target** for paper-stage
consistency; both forks become switchable backends after the
end-of-Phase-1 Backport Sprint (follow-up F-11; ledger at
`notes/TRUNK_R13078_BACKPORT_LEDGER.md`).**

#### II.11.0 Terminology — important

The user's integration project (predating this coupled-model
project) produced what they call **"integrated LTS"** — i.e., the
LandSyMM-fork features integrated into LPJ-GUESS. That artifact
lives at
`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`
and is what `notes/STEP_1.md` imported into our `lpjguess/`.

So in this document and throughout the rebuild documentation:

> **`LandSyMM_LPJ-GUESS/` ≡ "integrated LTS"** (synonymous; same
> artifact, two names. The terminology trace: the
> integration-project's working name was "integrated LTS"; the
> directory was named after the LandSyMM-LPJ-GUESS fork lineage.)

Adjacent in the same parent area is a *separate* directory
`lpjg_landsymm_integration/LPJ-GUESS-integrated/` which is
**not** what we imported and is **not** what the user calls "the
integrated LTS"; it appears to be a later separate experiment and
is out-of-scope for v1.0.

The third-party `trunk_r13078` lives at
`version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Integrations/trunk/trunk_r13078/`
(with an identical copy in `version_B/.../`) and is byte-identical
to `LandSyMM_LPJ-GUESS/` modulo 6 files (5 cosmetic, 1 critical:
the `exit(200)` at `imogencfx.cpp:483`).

#### II.11.1 The two LPJ-GUESS implementations to be supported in v1.0

| Implementation | What it is | Status in our rebuild | Practical effect |
|---|---|---|---|
| **`LandSyMM_LPJ-GUESS/`** (a.k.a. **"integrated LTS"** per user terminology) | The user's earlier integration-project artifact: ≈ `trunk_r13078` minus the `exit(200)` regression and 5 cosmetic touches. Source at `lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`. | **Active v1.0 development base.** Imported into `lpjguess/` at step 1. All steps 1-8 changes have been applied to this fork. | Lower-risk Phase-1 choice; no `exit(200)` regression to work around. |
| **`trunk_r13078`** (LandSyMM fork inside `version_A`/`version_B`) | The historical fork of LPJ-GUESS 4.1 that the coupled framework's predecessor versions A and B have always used. **Used in the working paper's Stage 1 PLUM yield runs.** Has the `exit(200)` regression that must be removed first. | **Backport target.** Will receive replicated copies of all `lpjguess/` changes via the Backport Sprint at end of Phase-1 (follow-up F-11). | Paper-stage consistency: Stage 1 used this fork; Stage 2 (our coupled model) will too once the Backport Sprint completes. Also exposed as a switchable build-time backend so users / CI can pick either. |

#### II.11.2 Why `LandSyMM_LPJ-GUESS/` ("integrated LTS") for v1.0

1. **No `exit(200)` regression.** The single critical diff between
   the two forks is the `exit(200)` short-circuit at
   `imogencfx.cpp:483` in `trunk_r13078`. `LandSyMM_LPJ-GUESS/` has
   it removed; starting development here saves us a "fix the fork
   first" step. (The Backport Sprint will simply remove it from
   `trunk_r13078` before replicating our changes.)
2. **Continuity with the user's existing work.** The user's
   integration-project work (preceding this coupled-model project)
   established `LandSyMM_LPJ-GUESS/` as the canonical fork they
   develop against; landsymm_py + the verification-test suite all
   ran against it. Continuing here preserves all that established
   muscle memory and tooling.
3. **Audit coverage.** The 8 phase-2 subagent reports audited
   `trunk_r13078`'s coupling-relevant code paths in detail.
   Because `LandSyMM_LPJ-GUESS/` differs only in 6 files (1
   critical + 5 cosmetic), that audit transfers directly: the
   coupling-framework integration points (`MiscOutput` IMOGEN
   stubs, `imogencfx::init` linkage, polling-loop fixes,
   `ndep.getndep()` un-comment, etc.) are byte-identical between
   the two forks.
4. **Bug-fix budget is bounded.** The 6-file diff vs `trunk_r13078`
   is well-characterised ([CMI §4.1.10] and `notes/STEP_1.md` §A).
   One-line revert of `exit(200)` plus 5 cosmetic touches and
   `trunk_r13078` is in known-good state — the Backport Sprint
   reconciles these as its first step before walking the ledger.

#### II.11.3 The Backport Sprint (end of Phase-1)

After v1.0 ships (i.e., after V.1 step 19's verification milestone
is met for the `LandSyMM_LPJ-GUESS/` backend), execute the
**Backport Sprint** documented in detail at
`notes/TRUNK_R13078_BACKPORT_LEDGER.md` §4. In summary:

1. **Setup** (~1 hour). Import
   `version_A/Integrations/trunk/trunk_r13078/` as a parallel
   tree under our repo (e.g. `lpjguess_trunk_r13078/`). Add a
   build-time switch
   (`-DLPJGUESS_BACKEND=landsymm_fork|trunk_r13078`,
   default `landsymm_fork`).
2. **Reconcile baseline** (~2 hours). Apply the 6-file delta
   (cosmetic + the critical `exit(200)` removal at
   `imogencfx.cpp:483`).
3. **Replicate ledger** (~4-6 hours). Walk
   `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 entries in step
   order; replicate each recorded edit in
   `lpjguess_trunk_r13078/`. Each entry has a "Backport
   guidance" field flagging trivial copies vs entries that
   need manual relocation due to surrounding-context drift.
4. **Verify** (~2-4 hours). Build cleanly; unit tests pass; run
   V.1 step-8 smoke and compare outputs. Functional similarity
   expected; any qualitative divergence is investigated.
5. **Document** (~2 hours). Update top-level `README.md`,
   `lpjguess/README.md`, and CHANGELOG to mention both backends.

**Estimated total: 1-2 days.** This is a one-shot operation;
after it lands, future steps make changes to BOTH trees in
lockstep (with the ledger continuing as a maintenance audit
trail; cf. the discipline section in
`TRUNK_R13078_BACKPORT_LEDGER.md` §6).

The maintenance discipline starts NOW (not at Phase-1 end):
every commit that touches `lpjguess/` C++ source files must add
a corresponding entry to the ledger §3. This is what makes the
eventual sprint mechanical instead of archaeological.

#### II.11.4 Knowledge gaps

1. **Does `do_potyield` exist in `trunk_r13078`?** This is the
   factorial-management mode for Stage I yield generation. The user
   added it to `LandSyMM_LPJ-GUESS/` (the "integrated LTS"); the
   audit's `[CMI Open Q §11.1.4]` flagged uncertainty about whether
   it's also in `trunk_r13078`. If not, Stage I yield generation
   in v1.0 either reuses pre-existing yield surfaces (cached from
   prior runs) or the Backport Sprint adds the `do_potyield` patch
   to `trunk_r13078` as a one-file merge — which is fine because
   the sprint is already walking source-level changes anyway.
2. **Has `LandSyMM_LPJ-GUESS/` ("integrated LTS") been tested with
   `imogencfx`?** Before this rebuild project, it was developed and
   tested only as a standalone DGVM (per the integration project)
   and against `landsymm_py`. Whether the coupling-framework
   integration points still work after the LTS merge is being
   answered **in real-time as we proceed through V.1**: steps 1-8
   have established that the build, unit tests, and IMOGEN
   handshake-writer registration all pass. The first true coupled
   smoke test (step 9) will be the first end-to-end exercise; if
   issues surface, they get fixed in `lpjguess/` and recorded in
   the Backport Ledger so the eventual sprint inherits the fixes.

---

## Part III — Open questions to the user

These are the items where the user's project knowledge most likely
trumps the audit. Listed in priority for the work in Part IV.

### Operational / code

1. **LPJG-side writer for the IMOGEN handshake files (I.B.1).**
   Does it exist somewhere the audit missed? The integrated LTS work
   may have it. If not, do the dead `MiscOutput` stubs
   (`miscoutput.cpp:121-136, miscoutput.h:69-79,172`) represent a
   started-but-abandoned scaffold that the user remembers, or were
   they simply scaffolded for a future hand?
2. **The HPC environment for Stage I and Stage II runs.** SLURM
   confirmed (the `submit.sh` template uses `#SBATCH` and `srun`).
   Cluster is **KIT IMK-IFU's owl** (the scripts directory name
   `owl_hpc_cluster_scripts/` confirms this). Partition: `cclake`.
   Default 2 nodes × 80 CPUs = 160 tasks. Walltime 3 days. Working
   dir at `/bg/data/lpj/work/<user>/<runname>/`. **Module-load
   conventions (gcc/cmake/netcdf/openmpi exact versions) — to be
   confirmed via terminal back-and-forth with the user at step 16.**
3. ~~**The `setup_run_owl_with_scratch_lpj_work.sh` helper.** Does the
   user have access to it from Lund, or must we write a fresh
   launcher?~~ **RESOLVED 5 May 2026: located at
   `/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/owl_hpc_cluster_scripts/scripts/`
   along with the full owl-cluster toolkit (mpi_run_guess_on_tmp.sh,
   finishup_lpj_work_owl.sh, make_guess.sh, append_runfiles.sh, etc.).
   Integrated at step 16 of the V.1 rebuild plan.**
4. ~~**Does `do_potyield` mode exist in trunk_r13078, or only in the
   user's integrated LTS work?**~~ **RESOLVED 5 May 2026: confirmed
   present in `trunk_r13078` (per user). No merge from integrated
   LTS needed for v1.0.**
5. ~~**Stage I outputs.** Have the per-CFT × management-treatment
   yield surfaces been generated and are they cached anywhere?~~
   **RESOLVED 5 May 2026: yes; user has run Stage I previously
   (during integrated-LTS verification testing); yields delivered
   to PLUM team; PLUM team returned scenario LU + activity data;
   activity data harmonised with HILDA+ via `landsymm_py`; new
   harmonised LU at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/`
   (Decision #10). Stage I deferred for v1.0; preserved in
   documentation as v2.0 capability.**

### Scientific

6. **IIASA vs RCMIP for the paper backbone (II.1).** What does the
   supervisor specifically want? RCMIP is the modern standard;
   IIASA is the dataset the paper currently cites; the choice is
   strategic.
7. **Fortran vs C++ IMOGEN (II.2).** Does the user prefer the
   working Fortran or want to invest 1-3 weeks in fixing the C++?
8. **2006 vs 2019-Refinement IPCC parameters (II.5).** The Python
   pipeline's hybrid (2006 historical + 2019 scenario) is
   methodologically inconsistent; is the supervisor open to
   unifying on 2019?
9. **N2O scope.** Does the user accept the ~5-8% double-counting bias
   between LPJG soil N2O and IPCC indirect (TECH §15.5), or do they
   want explicit subtraction of LPJG's indirect-emissions component?
10. **Working paper §2.3.4 boundary harmonisation (BTH+RBTM+5-yr MA)
    vs Python pipeline's segmented running mean (I.B.6, II equivalent).**
    Which does the supervisor want for v1.0?

### Datasets

11. **Is RCMIP Phase 2 v5.1.0 the right RCMIP version, or a newer
    release available?** RCMIP releases periodically; v5.1.0 is from
    2020. The current Phase 2 may have a newer minor version. (Also
    I should note: searching `rcmip.org` for the latest is fine.)
12. **PLUM v2 outputs format.** The Python pipeline expects
    `inputs/plum/plum_crop_s1.csv`; the framework has
    `Data/Intermediary/PLUM_data/animals_ssp{1..5}.txt` plus
    `plum_land_use/` and `agg_land_use/` directories. Do these
    contain the same content in different layouts, or different
    content? An adapter would be needed for the latter.
13. **GCM ensemble.** The CMIP6 NetCDF set has 5 GCMs. Is that the
    full ensemble the user wants, or a subset (e.g. for sensitivity
    studies the user wants 10-20)?

### Repository

14. **Target git remotes.** GitHub / KIT GitLab / Helmholtz GitLab?
    Same conventions as the previous integrated-LTS and `landsymm_py`
    work? Or a new GitHub org for the unified codebase?
15. **Authorship convention.** The unified codebase will draw from
    the user's previous work, the supervisor's contributions, and
    upstream LPJ-GUESS / IMOGEN / PLUM communities. CITATION.cff
    structure?

---

## Part IV — Recommended sequencing and effort estimates (deprecated; see Part V)

> **Note (5 May 2026):** Part IV below is the original effort-estimate
> sequencing written before the rebuild approach was settled. It is
> **superseded by Part V**, which reformulates the same work as a
> 16-step incremental-rebuild plan with explicit verification milestones
> at each step. Part IV is retained for historical reference and
> because some of its sub-totals (effort estimates per phase) are still
> useful for planning. New work should follow Part V.



Folded back into a phased plan (refined version of `[CMI §12]`). All
estimates assume one engineer working focused.

### Phase 0 — Strategic decisions (1-3 days)

Decide:
1. IIASA vs RCMIP backbone (II.1).
2. Fortran vs C++ IMOGEN (II.2).
3. Tight vs prescribed coupling default (II.4).
4. 2006 vs 2019 IPCC parameters (II.5).
5. Boundary harmonisation algorithm (I.B.6).

These are mostly conversations with the supervisor.

### Phase 1 — Code-level baseline (1-2 days)

Apply the 35 🟢 bug fixes from `[CMI §8.1]` + I.A.

### Phase 2 — Missing components (1-2 weeks)

In dependency order:

| Order | Task | Effort | Status |
|---:|---|---|:---:|
| 1 | Implement LPJG-side handshake writer (I.B.1) | 1-3 days | 🔴 |
| 2 | Wire the FILE_LPJG_FLUX rewiring (C35) once I.B.1 ships | 5 min | 🟢 |
| 3 | Write Python → LPJG-format adapter (I.B.2) | 4-8 hours | 🟡 |
| 4 | Provide top-level launcher (I.B.3) | 4-8 hours | 🟡 |
| 5 | Smoke test (3-cell × 3-year coupled run) | 2 hours | 🟢 |

### Phase 3 — Forcing data canonicalisation (3-5 days)

| Order | Task | Effort |
|---:|---|---|
| 1 | CMIP6 NetCDF → CMIP5 ASCII conversion (I.B.5 Option A) | 1 day |
| 2 | Switch `imogen_settings.txt` to CMIP6 MRI-ESM2-0 | 5 min |
| 3 | Rewrite `imogen_intermediary.ins` to consistent CMIP6/SSP1-2.6 + SSP2-4.5 paths | 2 hours |
| 4 | Audit and confirm NEE/NBP code-vs-doc (I.B.7) | 2 hours |
| 5 | If RCMIP backbone: Validate that Python pipeline's RCMIP-substitution outputs the right scenario set | 2 hours |
| 6 | If IIASA backbone: Implement IIASA-substitution path in Python (II.1 Option B/C) | 3-5 days |

### Phase 4 — Stage I yield generation (variable, days-weeks of cluster time)

| Order | Task | Effort |
|---:|---|---|
| 1 | Verify `do_potyield` mode is in trunk_r13078 OR merge from integrated LTS | 1-2 days |
| 2 | Provide Stage I run setup (`runs/stage1_potyield/`) | 4 hours |
| 3 | Run Stage I on cluster (251 yr × 6 treatments × 0.5° global) | 2-7 days wall-clock |
| 4 | Stage outputs in `Data/Yields/`; document for PLUM consumption | 2 hours |

(Phase 4 may be skippable if the existing `Data/Intermediary/PLUM_data/`
outputs are the result of a previous Stage I that the user can vouch
for.)

### Phase 5 — Validation (3-5 days)

1. Run a full SSP1-2.6 coupled simulation 1850-2100.
2. Verify atmospheric concentration trajectories meet `[CMI §2.5]`
   thresholds:
   - CO2 RMSD ≤ 5 ppm vs NOAA GMD 1958-present.
   - CH4 RMSD ≤ 50 ppb vs NOAA GMD / AGAGE 1983-present.
   - N2O RMSD ≤ 5 ppb vs NOAA GMD 1980-present.
3. Verify sectoral inventory PBIAS ≤ ±15% vs FAO/EDGAR.
4. Run SSP2-4.5 as a second validation.

### Phase 6 — Documentation, CI, public release (1-2 weeks)

1. Unified `docs/technical_manual.md`.
2. CI/CD pipeline (GitHub Actions / GitLab CI).
3. `paper/manuscript_draft.docx` updated with v1.0 results.
4. Tag v1.0; mirror to GitHub / KIT / Helmholtz.
5. Submit to GMD.

### Total effort to v1.0

Roughly **6-10 weeks of focused engineering**, plus cluster time for
Phase 4 + 5. The variable is whether IIASA-substitution (Option B/C
of II.1) is needed (+3-5 days) and whether `do_potyield` requires
merging in (+1-2 days).

---

## Part V — Formal incremental rebuild plan

This is the canonical work plan, superseding Part IV. It implements
the rebuild approach settled on 5 May 2026 (see Decisions Settled
table, item #5): build the unified codebase incrementally in
`lpj-guess_imogen_landsymm/`, importing one component at a time from
`version_A/B`, with each step ending in a verifiable working state.

### V.0 Conventions for the rebuild

- **Each step starts with a clean, verifiable predecessor state** and
  ends with a clean, verifiable successor state. If a step's
  verification fails, the prior state is restored and the step is
  re-investigated before proceeding.
- **Source preservation.** A and B remain untouched read-only
  archives. We copy or rewrite into `lpj-guess_imogen_landsymm/`,
  never modifying A or B.
- **Per-step git commits.** Each step ends in a single git commit
  with a descriptive message that names the verification milestone
  passed.
- **Per-step documentation.** Each step's verification protocol is
  recorded in a `notes/STEP_<n>.md` file in the unified codebase, so
  any reader (or successor) can reproduce the verification.
- **Units integrity (per §I.D)** is enforced at every step that
  involves cross-component data.
- **Effort estimates** are wall-clock days for one focused engineer.
  Cluster wall-clock for Stage I and validation runs is separate.

### V.1 Step-by-step rebuild sequence

| Step | What it does | Imported from | Verification milestone | Effort |
|---:|---|---|---|---|
| **0** | Initialise the unified repo. Create top-level structure per `[CMI §13]` (`lpjguess/`, `imogen/`, `intermediary_py/`, `tools/`, `runs/`, `data/`, `scripts/`, `ci/`, `archive/`, `docs/`, `paper/`). Add `.gitignore` excluding build artefacts, run output, large binaries. Add `README.md` (top-level navigation), `LICENSE` (MIT or equivalent), `CITATION.cff`, `CONTRIBUTING.md`, `CHANGELOG.md`. Move existing `COUPLED_MODEL_INVESTIGATION.md`, `EXECUTION_PLAN.md`, `_phase2_findings/` into the new structure. | (existing investigation docs) | `git init`; `git status` clean after first commit. Top-level `tree -L 2` shows clean structure. | 0.5 day |
| **1** | Import LPJ-GUESS LandSyMM fork → `lpjguess/`. Source from **`lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/`** (NOT `Integrations/trunk/trunk_r13078/` — to avoid the `exit(200)` regression and 5 cosmetic touches). Bring in: `framework/`, `modules/`, `libraries/`, `command_line_version/`, `cmake/`, `CMakeLists.txt`, `data/ins/`, `tests/`, `reference/`. Skip: `windows_version/`, `parallel_version/aurora.tmpl` etc. (re-add only if needed in V.11). Skip: `build_imogen/` (it's a build artefact), `.vscode/`. | `lpjg_landsymm_integration/LandSyMM_LPJ-GUESS/` | `cmake .. && make` produces `./guess` cleanly on Linux. Standalone CFX run (no IMOGEN) of `gridlist_test2.txt` (4 cells) for 3 years completes without warnings or errors. Output `cflux.out`, `mch4.out`, `ngases.out` produced. | 1 day |
| **2** | Import Fortran IMOGEN → `imogen/`. From `Common-directory/IMOGEN-codebase/code/`: bring in `imogen_lpjg.f`, `nonco2.f`, `Makefile`, `compile.sh`, `imogen_settings.txt`, `imogen_settings_tmpl.txt`. Skip: `Original Imogen Modified for LPJG Coupling/` (backup; archive only), `qsat_output.txt` (debug dump), `.vscode/`. From the same dir: bring in `gridlist_global.txt`, `gridlist_3deg.txt`, `gridlist_hurtt_RNDM_midpoint_3698.txt`, `patterns_gridlist.txt`. Apply the small fixes immediately on import: delete `PAUSE` (line 4134), delete `qsat_output.txt` debug dump (lines 4120-4128), replace `\\` with `/` in `mkdir` calls (lines 435, 461). | `Common-directory/IMOGEN-codebase/code/` | `gfortran -ffixed-line-length-132 -O imogen_lpjg.f nonco2.f -o imogen_lpjg` builds clean. Standalone IMOGEN run on the 1631-cell native grid for 3 years (1871-1873) produces `Common-directory/IMOGEN/output/<YYYY>/{T_anom.dat, P_anom.dat, …, done}` matching the existing run on disk in A. | 1 day |
| **3** ✅ | Convert Fortran static arrays to `ALLOCATABLE` (per Decisions #2 and §II.2). **Done 2026-05-05** with a deliberate scope reduction: only the **6 `NGPOINTS`-dimensioned arrays** in `PROGRAM IMOGEN` (`T_OUT_M_REGRID`, `P_OUT_M_REGRID`, `SW_OUT_M_REGRID`, `DTEMP_OUT_M_REGRID`, `F_WET_CLIM_REGRID`, `LON_OUT`, `LAT_OUT`) were converted, plus `NGPOINTS` was promoted from `PARAMETER` to a run-time setting (new `NGPOINTS` key in `imogen_settings.txt`; new `CASE('NGPOINTS')` branch in `SETTIN`; sentinel-`-1` initialisation and post-loop validation that aborts cleanly on a missing key). The `~30 GPOINTS-dimensioned arrays` were **deferred** because (a) they cannot be made truly run-time (the upstream pattern + CRUNCEP files have exactly `GPOINTS=1631` cells), and (b) at `GPOINTS=1631` the BSS allocation works fine on Linux — no functional benefit. `nonco2.f` references none of the four scaling constants → no changes there. The `NGPOINTS=62000` smoke verification is **deferred to step 6/16** (requires a 62k-cell gridlist and patterns + CRUNCEP from step 4). See `notes/STEP_3.md` for full per-edit detail. | (refactor) | ✅ Build clean (`gfortran -ffixed-line-length-132 -O`, no warnings). ✅ Positive smoke: parser reads `NGPOINTS=3698`, ALLOCATE block runs, terminates at expected later runtime input read (no LPJ-GUESS partner). ✅ Negative smoke: `NGPOINTS` line removed → validation fires, clean abort, `STOP 1`. ✅ Scaling smoke: `NGPOINTS=10000` → ALLOCATEs ~90 MB heap successfully → terminates at same expected later runtime input read. The full byte-identical-output verification is itself deferred to step 4 (requires patterns + CRUNCEP for a real IMOGEN run); the three smoke probes here establish that the refactor is purely additive and structurally sound. | 1 day actual (under estimate) |
| **4** ✅ | Import GCM patterns + CRUNCEP base climatology + verify standalone Fortran IMOGEN. **Done 2026-05-05** with an architectural twist: instead of committing 161 MB of upstream reference data to git, we built **4 distribution tarballs** (~49 MB compressed total) that sit outside git at the sibling path `lpj-guess_imogen_landsymm_data/`, plus a **manifest-driven fetch script** at `tools/fetch_imogen_data.sh` that downloads/copies + SHA256-verifies + extracts. `tools/imogen_data_manifest.txt` is the authoritative manifest (filename, SHA256, size, extract-path per tarball). Per-component breakdown: `imogen-patterns-cmip5-v1.0.tar.gz` (19 MB; 34 CMIP5 ASCII GCMs), `imogen-patterns-cmip6-v1.0.tar.gz` (19 MB; 5 CMIP6 NetCDF GCMs), `imogen-patterns-cmip3-legacy-v1.0.tar.gz` (534 KB; 1 UKMO HadCM3 pattern), `imogen-cruncep-1960-1989-v1.0.tar.gz` (11 MB; 30-yr base climatology). Also fixed a silent **`.gitignore` bug** (inline comments after a pattern broke 4 ignore rules) and discovered the **bug C2/C3 work-around** required at run-time (pre-stage an empty `done` file in `LPJG_main/IMOGEN/`; source fix at step 7). The actual upload of the tarballs to a permanent host (Zenodo / GitHub Releases / institutional bucket) is a TBD follow-up the user will do post-step-4. See `notes/STEP_4.md` for full per-edit detail. | `version_A/.../IMOGEN-codebase/{patterns,CRUNCEP_1960_1989}/` | ✅ All 4 tarballs verify clean via `tools/fetch_imogen_data.sh --verify-only`. ✅ Standalone Fortran IMOGEN run with default `DIR_PATT=patterns/CEN_IPSL_MOD_IPSL-CM5A-MR/` + `DIR_CLIM=CRUNCEP_1960_1989/` + the 8 LPJG-side stub files produces years 1871, 1872 of output at `imogen/code/IMOGEN/output/<YYYY>/{T_anom.dat, P_anom.dat, SW_anom.dat, DTEMP_anom.dat, WET.dat, dtemp_o.dat, fa_ocean.dat, CO2.dat, done}`. ✅ Numerical content is physically plausible (Arctic 82.5° N monthly Kelvin temperatures 231–276 K). ⚠️ Output is NOT byte-identical to `version_A`'s reference: `Rh_anom.dat`+`W_anom.dat` are missing (expected per `[SA3 §10]`; will be ported in step 9.5); T values diverge 0.1–8 K vs version_A (which appears to have been generated by the C++ refactor, not Fortran — Fortran↔C++ parity is the Phase-2 milestone per Decision #2); `T_anom.dat` has 2× the line count of version_A (a Fortran writer quirk to investigate). The full 1850-2100 CO2 trajectory check is deferred until step 7's source-level fix to bug C2/C3 makes multi-year runs no-fuss. | 0.5 day actual (under estimate) |
| **5** ✅ | CMIP6 NetCDF → CMIP5 ASCII converter → `tools/cmip6_nc_to_cmip5_ascii.py`. **Done 2026-05-06**. ~340 Python lines (xarray + scipy bilinear); two operating modes (single-GCM via `--nc/--json/--output`; batch via `--input-dir/--output-base` discovers all 5 GCMs in 1.6 sec wall-clock). Authoritative column ordering taken from `imogen_lpjg.f::GCM_ANLG`'s READ statement at line 3270-3274 (10 pattern columns + 2 coord columns; the Appendix A.3 sketch had 12 mapped vars which was incorrect). Mapping resolves three CMIP6→CMIP5 mismatches with documented caveats: (A) `ql1_patt` (units "K-1") passed through directly into `DRH15M_PAT` col 4; upstream RH-sensitivity convention to be confirmed (followup F-6); (B) `wind_patt` (magnitude only) split equally to U/V via 1/√2 factor (followup F-8 at step 9.5); (C) `precip_patt` lumped to RAIN, SNOW=0 (followup F-8). 5 output dirs `CEN_CMIP6_MOD_<gcm>/` and 5 namelists `<gcm>_ebm.nml` produced; both gitignored as derivative output (regenerated by re-running the converter). | (new tool) | ✅ Build clean; --help, --list, single-GCM, batch all tested. ✅ Standalone IMOGEN run with `DIR_PATT=patterns/CEN_CMIP6_MOD_MRI-ESM2-0/` and the same step-4 LPJG_main stub setup produces years 1871, 1872 with all expected climate files written. ✅ Numerical comparison vs step 4's CMIP5/IPSL-CM5A-MR run for cell (lat=82.5°, lon=281.25°): T_jan diff = 0.06 K, T_feb = 0.06 K, T_mar = 0.04 K — exactly the inter-GCM scatter from pattern differences scaled by year-1871's small ~0.1-0.2 K land-mean anomaly. ⚠️ Pstar pattern shows 150× magnitude difference + opposite sign vs CMIP5/IPSL at the same cell — likely Pa-vs-hPa unit difference in the source NetCDF (followup F-7). The CMIP6 column-mapping caveats are documented in `notes/STEP_5.md` and `notes/FOLLOWUPS.md` items F-6, F-7, F-8. | 0.5 day actual (under estimate) |
| **6** ✅ | Import reference data → `data/`. **Done 2026-05-06**, partitioned into 3 tiers: (Tier 1) committed directly to git: `data/soil/soilmap_…dat` (3.5 MB), `data/gridlist/*.txt` (7 files, 3.4 MB; the spec said 8 but only 7 are at the source — `gridlist_test480.txt` not present), `data/concentrations/{EPA,IIASA}/{CMIP5,CMIP6}/...` (TXT/CSV/DAT only — XLSX/ZIP raw downloads excluded; 7.5 MB; 31 files); total Tier 1 ~14 MB. (Tier 2) tarballed + manifest-registered + fetch-script-ready: `imogen-emiss-reference-v1.0.tar.gz` (311 KB compressed, 5.2 MB raw, full `Data/Imogen/emiss/` tree including CMIP5/, CMIP6/{Co2,CH4-N2O,Non-Co2-CH4-N2O-RF}/, DKB_dataset_totals/, new_emission_data/, rcp_database/, 6 loose files — closes followup **F-5**); `imogen-ndep-lamarque-v1.0.tar.gz` (460 MB compressed, 501 MB raw, 5 Lamarque .bin files). (Tier 3) documented in new `data/DATA.md`: PLUM scenario LU at `/media/bampoh-d/lpjg_input/...` (86 GB, mounted, per Decision #10 used via save_state/restart), legacy `Data/LU/SSP1_RCP26_concatenated/` (7.3 GB, superseded fallback), legacy `Data/Intermediary/` (2.2 GB, superseded by `intermediary_py` step 10), predecessor's pre-baked IMOGEN outputs (~2 GB each, reproducible), public datasets (HILDA+, FAOSTAT, EDGAR 2025, RCMIP, FAIR, IIASA SSP db, NOAA GMD, AGAGE). **Side effect**: `imogen/emiss/` restructured from step-4's flat-3-files stop-gap to the full tree because the active coupled-mode `imogen_intermediary.ins` references the deeper subdir paths; `imogen/code/imogen_settings.txt`'s 3 `FILE_*_EMITS` keys updated correspondingly (3-line edit). | `Data/{soil,Gridlist,Concentrations,Imogen,Ndep}/` plus `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/` | ✅ Tier 1: 31 trackable files (14 MB), no XLSX/ZIP leaked. ✅ Tier 2 manifest verifies all 6 components clean (`tools/fetch_imogen_data.sh --verify-only`). ✅ Tier 3: `data/DATA.md` written. ✅ Standalone IMOGEN regression smoke run after the `imogen_settings.txt` path update still produces years 1871, 1872 with all expected climate files (no regression from the path restructure). The full coupled-run-completion verification is gated on step 7 (the source-level coupling fixes including bug-C2/C3). | 0.5 day actual |
| **7** ✅ | Apply LPJ-GUESS coupling source-level fixes. **Done 2026-05-06**, with a smaller-than-spec scope after step 1's import-choice and step 7's investigation: (a) C1 `exit(200)`: ✅ already absent in the imported LandSyMM fork (that's specifically why we picked it over `trunk_r13078` at step 1); (b) C2 `INQUIRE` for `done`: ✅ restored at `lpjguess/modules/climatemodel.cpp:332-333` (replacing the hard-coded `doneExist = true` short-circuit) PLUS added a first-call bypass via the existing `firstCall` local (so the very first iteration doesn't hang); (c) C3 3 polling guards: ✅ restored at `climatemodel.cpp:336, 343, 352` (the `runnowOpen`, `runfluxOpen`, `runnonco2fluxOpen` `*Open = !file.is_open()` lines); (d) C4 `ndep.getndep(...)`: ✅ uncommented at `lpjguess/modules/imogen_input.cpp:728`; (e) C5 `IMOGEN/ouput/` typos + `R_anom.dat`→`Rh_anom.dat`: deferred to step 9 (those typos live in the predecessor's run-config `.ins` files, not in the imported source tree; our `runs/<SSP>/...` dirs don't exist yet — they get created at step 9 with correct paths from the start); (f) Fortran path / mkdir cleanups: ✅ already done at step 2. **Bonus**: also closed follow-up **F-4** (the Fortran-side twin of C2/C3) by adding a `CALL SYSTEM('mkdir -p ...; touch ... /LPJG_main/IMOGEN/done')` block at `imogen/code/imogen_lpjg.f` before the `DO WHILE (KEEPRUNNING)` outer loop. This eliminates the manual `touch done` workaround required since step 4 for every standalone smoke run. | (apply diffs) | ✅ LPJ-GUESS rebuilds clean. ✅ All **162 unit tests still pass** (`./runtests` reports `All tests passed`). ✅ Fortran IMOGEN rebuilds clean. ✅ Standalone IMOGEN smoke run produces years 1871-1872 **without** any manual `touch done` workaround — bug F-4 fully resolved. The full coupled-mode end-to-end run-completion test (the V.1 spec's `./guess -input imogencfx main.ins` over a 3-cell × 3-year smoke test) is gated on step 8 (LPJG-side handshake writer) + step 9 (run-config `.ins` files); step 7's verification was the structural/regression check. | 0.5 day actual (under estimate) |
| **8** ✅ | Implemented the LPJG-side handshake writer (per Appendix A.1) → `lpjguess/modules/imogenoutput.cpp/h`. **Done 2026-05-06.** Registered with the LPJ-GUESS output framework via `REGISTER_OUTPUT_MODULE("imogenoutput", ImogenOutput)`. Provided `coupling_mode` ins parameter ("tight"/"prescribed"/"loose"; default "tight") declared in `IMOGENConfig` namespace and registered via `imogencfx.cpp` `declare_parameter` block; mode-gates the 4 file writes (loose mode skips writes entirely). Per-year cadence implemented as year-change-detection at start of `outannual` triggers `flush_year(prev_year)`; final year flushed in destructor. Carbon/CH4/N2O accumulation mirrors `commonoutput::outannual` Gridcell→Stand→Patch flux loop (kgC/m^2/yr × gridcell_area_m2 → kgC; × 1e-12 → PgC; CH4 g(C)→g(CH4) via 16/12; N2O kgN→kgN2O via 44/28). Removed dead `getImogenData()` random-placeholder helper from `miscoutput.h` (was never invoked). **Per Appendix A.1's open question 4 (per-year aggregation hook in framework.cpp) — answered: there is no `outglobal_year` hook; `outannual(Gridcell&)` fires per-gridcell in the per-gridcell-outer / per-day-inner-across-all-years framework loop (lines 411-516); this finding is logged as the new follow-up F-10** (architectural mismatch between framework loop ordering and proper per-year-globally-synchronized tight coupling; documented extensively in `notes/FOLLOWUPS.md` with Phase-2 recommendation: parameter-gated additive `framework_loop_mode` code path, not framework restructure). v1.0 emits per-gridcell-rolling values at flush time (V.1's stated milestone met) but NOT globally-synchronized values; bias risk evaluated empirically at step 17. | `lpjguess/modules/imogenoutput.h` (~150 LOC), `imogenoutput.cpp` (~310 LOC), `parameters.h/cpp` (+13 LOC for `coupling_mode`), `imogencfx.cpp` (+7 LOC for declare_parameter), `modules/CMakeLists.txt` (+2 LOC), `miscoutput.h` (-16 LOC, +5 LOC for cleanup) | Build clean (162/162 unit tests still pass). Per-year file-write end-to-end smoke gated on step 9's run-config setup. | 2-3 days (actual: ~0.5 day for code + ~0.5 day for documentation including F-10 deep-dive) |
| **9** ⚠️ | **Done 2026-05-07 with empirical limitation**. Created `runs/SSP1-2.6/main.ins` + `imogen_intermediary.ins` + 11 stand/PFT/landcover ins files (copied from version_A predecessor, LU paths retargeted to version_A's actual tree per user guidance to use legacy LU). Embodied bug C5 fix (`output` not `ouput`), bug R-anom fix (`Rh_anom.dat` not `R_anom.dat`), and bug C35 fix (relative filenames in commented-out block). Imported missing SSP126 NON_CO2 RF file (3.5 KB) from version_B into our `imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/`. Smoke test ran successfully through engine setup, CRUNCEP read, GCM-pattern read (CMIP6 MRI-ESM2-0), all 251-year emissions reads, and produced 32 years × 10 climate output files (T_anom, P_anom, SW_anom, DTEMP_anom, Rh_anom, W_anom, WET, CO2, dtemp_o, fa_ocean) — proving bug C5 + R-anom fixes work. **EMPIRICAL F-10 CONFIRMATION**: in v1.0 single-process `imogencfx` mode, regardless of `coupling_mode`, the engine cannot terminate without LPJG-supplied per-year handshake updates AND LPJG cannot run its main loop until `imogencfx::init()` returns — hard deadlock. Step 8's writer NEVER FIRES in v1.0 single-process mode. Bug C35 fix is correct in code but un-testable in v1.0 (relative paths cause immediate `RUNFLUX_EXIST=0` deadlock). **The V.1 step-9 verification milestone (NEE 2x → CO2 shift) is gated on follow-up F-12** (multi-pass / two-process verification design; recommended Option B = split engine into separate concurrent process). The `imogen_nee_perturbation_factor` runtime parameter was added at step 9 then REMOVED at step 9 wrap-up because it cannot affect anything observable in v1.0 (LPJG main loop never runs); see `notes/STEP_9.md` §3.6 for the add-then-remove discipline rationale. | `runs/SSP1-2.6/main.ins` (NEW), `runs/SSP1-2.6/imogen_intermediary.ins` (NEW), `runs/SSP1-2.6/README.md` (NEW), `runs/SSP1-2.6/{global,crop,landcover,...}.ins` (11 copied), `imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_ssp126.txt` (NEW, 3.5 KB), `notes/STEP_9.md` (NEW), `notes/FOLLOWUPS.md` (+F-12) | Build clean (162/162 unit tests). Engine end-to-end runs (32 years climate output). Bug C5 + R-anom proven. Bug C35 fix in code; F-12 gates the actual feedback verification. **Major architectural finding F-10 empirically confirmed.** | 2-3 days actual (1 day budgeted; +1 day for the 4 iterative .ins fixes and the F-10 empirical investigation) |
| **9.5** ⚠️ | **Climate-output enhancements (Decisions #11/#12). PARTIAL DONE 2026-05-07 with significant scope refinement. Items (a)+(b)+(c)+F-9 EXPLICITLY OUTSTANDING per 2026-05-11 audit; aggregated to ~5-7 days of remaining in-v1.0-scope work; tracked under `notes/FOLLOWUPS.md` "Comprehensive outstanding-work audit" section A.B.1-B.5. Plus: ImogenInput consumer wiring expansion for Rh/W/Tmin/Tmax (loose-mode symmetry with IMOGENCFXInput; ~1 day) added per user 2026-05-10 late-evening clarification.** Phase A investigation surfaced TWO unanticipated infrastructure dependencies: (i) Fortran engine does NOT compute Rh/wind at all (assumed it just didn't write them) — the C++ port added the entire physics pipeline; porting to Fortran is ~70-100 LOC of Fortran physics work, not 20 LOC of writer-only addition. **Item (a) deferred to step 9.5b**. (ii) `Climate` class has no per-month accumulator arrays (only single-day fields + 20-year-window aggregates); F-9 closure as originally planned (`outlimit(out_t_anom, gridcell.climate.mtemp[m])`) doesn't compile because `mtemp` is a single-value field, not `mtemp[12]`. **Item (e) F-9 closure deferred** with refined entry in `notes/FOLLOWUPS.md` documenting the per-month-accumulator blocker (Option A: add accumulators to `Climate`; Option B: cross-module getter from `IMOGENCFXInput::dtemp[]`; Option A recommended). **What WAS implemented at step 9.5**: (c) full LPJG-side consumer wiring (4 param reads, 4 `read_lines_from_file` calls with empty-path guards, BLAZE compatibility check restored with actionable error message, monthly→daily interpolation via `interp_monthly_means_conserve`, daily-mode passthrough, 4 `climate.{relhum,u10,tmin,tmax}` assignments mirroring `cfxinput.cpp:1940-1945`); (d) BLAZE check at `imogencfx.cpp:803-804` RESTORED with empty-path safety; (b)-partial: C++ engine `climatemodel.cpp` non-REGRID branch writes `Tmin_anom.dat` + `Tmax_anom.dat` per year (TODO step 9.5b: replicate in REGRID branch). **End-to-end verification of (c) gated on F-12** (LPJG main loop never enters in v1.0 single-process mode per F-10). **Verifiable in v1.0 smoke**: 64 new files (`Tmin_anom.dat` + `Tmax_anom.dat` × 32 engine years) appear in `Common-directory/IMOGEN/output/<YYYY>/`. | `lpjguess/modules/imogencfx.h` (+9 LOC across 3 blocks); `lpjguess/modules/imogencfx.cpp` (+80 LOC across 5 spots); `lpjguess/modules/climatemodel.cpp` (+25 LOC in non-REGRID branch); refined `notes/FOLLOWUPS.md` F-9 entry; `notes/STEP_9.5.md` (NEW) | Build clean (162/162 unit tests still pass). End-to-end run-output verification gated on F-12. | 1 day budgeted; partial done in ~0.5 day; deferred items 9.5b for separate ~1-2 day session and set `climate.relhum`, `climate.u10`, `climate.tmin`, `climate.tmax` (~16 LOC). (d) **Restore the BLAZE check** at `imogencfx.cpp:792-794` (uncomment) — now that wind and humidity are wired, BLAZE can run safely. (e) **Verify units carefully** per §I.D: T in K (with K→°C for `climate.temp`); RH as fraction or % (LPJG `climate.relhum` convention is %); wind in m/s. | (Fortran + C++ refactor) | After this step: **Fortran and C++ IMOGEN produce parity output**, including `Rh_anom.dat`, `W_anom.dat`, `Tmin_anom.dat`, `Tmax_anom.dat`. LPJ-GUESS's `imogencfx` consumes all of these and populates the `Climate` struct. BLAZE fire model runs without silent zero-default for humidity/wind. | 0.5-1 day |
| **10** ✅ | **Done 2026-05-07.** Imported `imogen_ghg_controller v0.1.0` from `version_A/Intermediary_py/imogen_ghg_controller_SOURCE_ONLY/imogen_ghg_controller/` to our `intermediary_py/imogen_ghg_controller/` (7.9 MB, 78 files: 59 Python source + 3 pytest tests + 16 docs/config). Verified A vs B SOURCE_ONLY are byte-identical (no diff in code/docs/etc.; only fork-shared figure PNG presence differs). Excluded `inputs/` (Tier-3 ~1.8 GB; in `data/DATA.md`), `outputs/` (generated), `archive/`, `__pycache__`. Pipeline structure verified via `python3 run_all.py --dry-run` reporting all 43 steps cleanly (Component A: 28; B: 5; C: 9; D: 1) with exit code 0 and no missing-imports errors. **Bug C33 (`openpyxl≥3.0`)** and **bug K21 (chat excerpt in Quick_Start.md)** observed in the imported source but NOT fixed at step 10 (predecessor file is reproducibility artifact; openpyxl needed only when running EDGAR loaders at step 11 — fix when first hit). End-to-end pipeline run gated on **step 11** (Tier-3 input acquisition: RCMIP, FAIR ERF, EDGAR, PLUM, LPJG outputs). Pytest run gated on populated `outputs/` per step 11. Adapter (`tools/imogen_inputs_to_lpjg_format.py`) for converting intermediary_py's 6 CSVs into 4 narrow IMOGEN-readable files lives at **step 13**. | `intermediary_py/imogen_ghg_controller/` (NEW; 7.9 MB / 78 files); `intermediary_py/README.md` (imported-status update); `notes/STEP_10.md` (NEW); `notes/FOLLOWUPS.md` (+Status dashboard); `CHANGELOG.md` (`[v0.11.0-step10-intermediary-py-import]`); `EXECUTION_PLAN.md` (this row marked DONE) | dry-run reports 43/43 clean; package structure intact; deps documented; Tier-3 acquisition recipe in `data/DATA.md` | 0.5 day budgeted; actual ~1 hour (clean import + dry-run + docs) |
| **11** ✅ | **DONE 2026-05-07.** Per user guidance, sidestepped piecemeal acquisition and used version_A's existing `imogen_ghg_controller_FULL/inputs/` (5.1 GB, 7 subdirs: edgar/fao/fair_erf/lpjg/plum/rcmip/reference_pdfs) as input source via 7 gitignored symlinks at `intermediary_py/imogen_ghg_controller/inputs/<subdir>` — zero disk overhead, fully reproducible. **Pipeline ran end-to-end**: `python3 run_all.py --skip-plots` completed all 23 steps (Components A→D, processing-only) in 540.3s (~9 min) with zero errors after fixing 4 source-level bugs surfaced during the run: (1) `paths.py::ensure_output_dirs()` only created level-2 dirs — extended to enumerate all 14 level-3 sub-subdirs + added auto-call on module import (idempotent; gated by `IMOGEN_GHG_NO_AUTO_MKDIR=1` env var); (2) 3 scenario scripts (`01_scenario_ch4_ef_processing.py`, `02_scenario_ch4_mm_processing.py`, `03_scenario_n2o_mm_processing.py`) used `os.makedirs` without `import os` — added; (3) `01_scenario_ch4_ef_processing.py:187` referenced stale column name `FAOCountry` — changed to `Country` (single occurrence; matches version_A's reference outputs which use `Country`); (4) `rcmip_substitution_processing.py:376-377` wrote outputs to its OWN src/ dir via `HERE` — changed to `OUT_A_DATA` so producer-consumer chain works without manual copy. Plus bug C33 fix (`openpyxl>=3.0` added to requirements.txt + pyproject.toml). All 6 final IMOGEN-input CSVs produced (5 wide + 1 long; 201×10 + 3016×N rows). **Pytest 10/10 passed.** **Reproducibility**: ALL 9 columns byte-identical for historical 1900-2019; CO2 + CH4_natural + N2O_natural also byte-identical for scenarios 2020-2100; CH4_anthro/N2O_anthro within 0.17-0.22% mean relative drift (matches Quick_Start.md's documented "slightly earlier code revision" provenance for FAOCountry→Country reconciliation). NET source-level change in `lpjguess/`: ZERO (intermediary_py is fork-agnostic). | `intermediary_py/imogen_ghg_controller/{src/shared/paths.py, src/component_a_anthropogenic/{rcmip_substitution/rcmip_substitution_processing.py, scenarios/0[1-3]_scenario_*_processing.py}, run_all.py, requirements.txt, pyproject.toml}` (9 files modified, +95 LOC); `.gitignore` (+10 LOC); `notes/STEP_11.md` (NEW, ~14 KB) | `python3 run_all.py --skip-plots`: 23/23 steps in 540.3s; pytest: 10/10 pass; reproducibility verified (CO2 + natural fluxes byte-identical to reference) | 1 day budgeted; actual ~1.5 hours (4 bug fixes + 9-min pipeline + reproducibility validation + docs) |
| **12** ✅ | **DONE 2026-05-07 (consolidated with step 11).** The end-to-end Python Intermediary run + reference validation that step 12 was originally scoped for was completed as part of step 11 (which leveraged version_A's `imogen_ghg_controller_FULL/inputs/` to sidestep input acquisition and went straight to the live run). Pipeline ran 23/23 steps in 540.3s (`python3 run_all.py --skip-plots`); all 5 SSP scenarios produced (not just SSP1-2.6 + SSP2-4.5 as originally scoped). Pytest 10/10 (more than the 3 originally scoped). Reproducibility verified: `imogen_inputs_SSP1-2.6.csv` shape (201, 10) ✓, no NaNs ✓; ALL 9 columns byte-identical to version_A reference for historical (1900-2019); CO2 + natural CH4/N2O byte-identical for scenarios; anthro CH4/N2O within 0.17-0.22% mean rel drift (matches Quick_Start's documented "slightly earlier code revision" provenance). **NOT yet validated** at step 12: the `--skip-plots` mode skipped the 13/14 reference-plot comparisons. Plot validation deferred to step 19 (release polish) when wall-clock budget allows the full 25-40 min `python3 run_all.py` (no `--skip-plots`) run. See `notes/STEP_11.md` §4 for the full execution + reproducibility data. | covered by step 11 deliverables | covered by step 11 verification | 0 (consolidated; budgeted 1-2 hrs in original plan but actual work folded into step 11) |
| **13** ✅ | **DONE 2026-05-07.** Implemented `tools/imogen_inputs_to_lpjg_format.py` (~270 LOC Python) with full unit-checked-adapter discipline per §I.D.2: schema validation (10 expected columns), no-NaNs assertion, monotonic Year column check, per-column sanity-bounds (e.g. `CO2_EFOS_Mt: [-50000, 100000]` Mt/yr to allow SSP1-2.6's negative-emissions late-century BECCS pathway), explicit named conversion constants (`PgC_TO_MtCO2 = (44/12)*1000 = 3666.6667`; CH4/N2O pass-through since Mt=Tg=1e12g), startup + end-of-run unit-conventions banners, end-of-run "next-step" banner with exact ins-file edits the user needs. **Tested end-to-end on SSP1-2.6**: 4 files written in <1s, 201 rows each (1900-2100), format matches predecessor's static IIASA files verbatim (2-col space-separated for CO2; 3-col tab-separated for CH4/N2O), unit conversion verified to 6 decimals against hand-math (1788.821 MtCO2 / 3666.667 = 0.487860 PgC). Late-century rows correctly show negative CO2 anthropogenic emissions (~-1.56 PgC/yr in 2099-2100) reflecting SSP1-2.6's BECCS pathway. **Wired** into `runs/SSP1-2.6/imogen_intermediary.ins` as new "Option B" alongside existing "Option A" (predecessor's static-IIASA; v1.0 default) and "Option C" (relative-path tight-mode; un-testable in v1.0 due to F-10 deadlock). Year-range mismatch (intermediary_py 1900-2100 vs engine default 1850-2100) documented; `--pad-to-year 1850` flag offered as compatibility shim with explicit "NOT scientifically defensible" warning. **End-to-end coupled run with adapter-driven backbone gated on F-12** (F-10 deadlock blocks LPJG main loop regardless of emissions backbone; adapter is scientifically validated but integrated run awaits Phase-2 multi-pass / two-process design). NET source-level change in `lpjguess/`: ZERO (fork-agnostic Python tool). | `tools/imogen_inputs_to_lpjg_format.py` (NEW, ~10 KB / ~270 LOC); `runs/SSP1-2.6/imogen_intermediary.ins` (+Option B block); `tools/README.md` (+adapter entry, -planned row); `.gitignore` (comment annotation); `notes/STEP_13.md` (NEW, ~14 KB) | adapter ran end-to-end <1 sec; format + units + value ranges all verified scientifically | 0.5-1 day budgeted; actual ~1 hour (implement + test + verify + wire + docs) |
| **14** ✅ | **DONE 2026-05-07.** Implemented `scripts/run_coupled.sh` (~330 LOC bash) — production-quality workstation launcher walking 7 pipeline steps: (1) idempotent LPJ-GUESS build with **Anaconda3 NetCDF auto-detection** (4-tier priority per Decision #8: explicit `--anaconda3-prefix`, then `$CONDA_PREFIX`, then `$ANACONDA_PREFIX`, then `/home/$USER/anaconda3`); (2) intermediary_py end-to-end run if `--backbone intermediary-py`; (3) Python → LPJG-format adapter (step 13) if `--backbone intermediary-py`; (4) bootstrap `LPJG_main/IMOGEN/{imogen_lpjg.txt, done}` per step-9 F-10 workaround; (5) clean stale per-year IMOGEN output; (6) launch `./guess -input imogencfx main.ins` in scenario's run dir; (7) collect summary. CLI flags: `--scenario`, `--coupling-mode tight\|prescribed\|loose` (default prescribed; v1.0 F-10 workaround), `--backbone static-iiasa\|intermediary-py` (default static-iiasa), `--smoke\|--production`, `--no-build/--no-intermediary/--no-adapter`, `--anaconda3-prefix`, `-h`. Each flag validated against allowed values. **F-10 deadlock awareness**: prints WARNING when `--coupling-mode tight` or `--production` requested. **Banner per §I.D.5**: prints scenario + coupling mode + backbone + run mode + canonical units conventions (NEE sign, CO2 conversion, CH4/N2O units, year indexing, cell area). Structured colored logging (info/warn/error/ok); date-stamped log at `logs/run_coupled_<SCENARIO>_<TS>.log`; trap-based error handler. **89-line self-documenting `--help`** via awk-based comment-block extraction. Plus **collateral fix**: added `param "file_tmin" / "file_tmax"` directives to `imogen_intermediary.ins` (step-9.5 follow-up; the launcher's first smoke surfaced "Paramlist: file_tmin not found"). **Verification**: `--help` works (89 lines); end-to-end smoke run produces 30+ engine year-output dirs before F-10 deadlock at year 1903 (matches step 9 empirical pattern); launcher exits cleanly with documented warning rather than failing on the deadlock; Anaconda3 NetCDF detected at `/home/bampoh-d/anaconda3` ✓. **Plus `docs/build.md`** (~150 lines): Anaconda3 NetCDF preference + manual build paths + manual intermediary_py setup (7-symlink recipe) + manual adapter run + how-to-verify + cluster placeholder + troubleshooting + cross-references. **NET `lpjguess/` C++ change: ZERO** (launcher is shell + docs are markdown + .ins fix is config). End-to-end run with LPJG main loop firing remains gated on F-12 (architectural deadlock). | `scripts/run_coupled.sh` (NEW, ~12 KB / ~330 LOC); `docs/build.md` (NEW, ~150 lines); `runs/SSP1-2.6/imogen_intermediary.ins` (+2 param dirs); `.gitignore` (+runs/*/Common-directory/); `notes/STEP_14.md` (NEW, ~12 KB) | `--help` 89 lines clean; smoke run produces 30+ engine year-dirs; deadlock handled gracefully; Anaconda3 detected | 1 day budgeted; actual ~2 hours (launcher + docs + collateral fix + smoke verification) | | (new) | A full SSP1-2.6 coupled run for the 4-cell `gridlist_test2.txt` for years 1850-1860 (11 years) completes successfully, end-to-end, on the user's workstation with Anaconda3 NetCDF. Outputs at `runs/SSP1-2.6/output/{cflux.out,mch4.out,ngases.out,...}` and `Common-directory/IMOGEN/output/<YYYY>/`. | 1 day |
| **15** ✅ | **DONE 2026-05-08.** Documentation-only step per Decision #9; Stage I deferred for v1.0; existing PLUM-harm `forLPJG` outputs (~85 GB total across 5 SSPs) at `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/` and `/media/bampoh-d/ISIMIP/inputs/landuse/plum_harm_lu/` verified live and inventoried. **Format delta surfaced**: PLUM-harm forLPJG (5 files; column ordering `PASTURE CROPLAND NATURAL BARREN`; 21 crop columns with `OilNfix`/`OilOther` split; year coverage 2021-2100 scenario-only) differs from predecessor's concatenated 1901-2100 (4 files; column ordering `NATURAL CROPLAND PASTURE BARREN`; 19 crop columns with `Oilcrops` merged; year coverage 1901-2100 concatenated). Switching v1.0 from Option C (currently used; legacy concatenated) to Option B (PLUM-harm forLPJG) requires either format conversion OR `save_state`/`restart` pattern (Decision #10 Option D); both deferred to v1.1 per `docs/v2_roadmap.md` §3. **Verified `lpjguess/` already has all required parameters wired** (per `lpjg_landsymm_integration/landsymm_runtime_parameters.md`): `restart`/`save_state`/`state_year`/`state_path` (§2.1-2.3); `do_potyield`/`isforpotyield`/`N_appfert_mt`/`hydrology` enum (§6.1-6.3, §5.1) — no source-level work needed for v2.0 PLUM embedding. **Bundled errata cleanup**: `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 — 5 stale step-1-5 commit hashes corrected (verified via `git rev-list -n 1 <tag>`) + 9 `_TBD_` placeholders (steps 9-14) filled in (per the prior chat handoff Part 11 §82.3 maintenance follow-up). NET source-level change in `lpjguess/`: ZERO. | `docs/scientific_framework.md` (NEW, ~13 KB), `docs/v2_roadmap.md` (NEW, ~13 KB), `notes/STEP_15.md` (NEW, ~12 KB), `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (§3 errata + step-15 row), `CHANGELOG.md` (`[v0.15.0-step15-stage1-deferral]`), `EXECUTION_PLAN.md` (this row marked DONE), `notes/FOLLOWUPS.md` (status dashboard date) | `docs/scientific_framework.md` includes complete Stage I specification + Decision #10 save_state/restart pattern + F-10 caveat narrative; `docs/v2_roadmap.md` outlines v1.1 (PLUM-harm save_state wiring + F-12 Option B two-process) + v2.0 (F-12 Option C in-process restructure + PLUM embedding) trajectory. PLUM outputs verified accessible at both `/media/bampoh-d/...` mount paths. | 0.25 day budgeted; actual ~4-4.5 hours (over budget; the "verify PLUM outputs" sub-step required surfacing format delta + investigating the predecessor's concatenated vs PLUM-harm forLPJG distinction; this is recorded as input for v1.1 wiring) |
| **16** ✅ | **DONE 2026-05-08 for v1.0 LOOSE-only baseline.** Cluster orchestration toolkit at `scripts/cluster/` (7 files; ~50 KB) implementing the gridlist-split / per-rank-runNN / SLURM-submit / dependency-chained-finishup pattern adapted from the IMK-IFU `owl_hpc_cluster_scripts/scripts/` toolkit. Plus workstation-parallel mimic test (`scripts/run_parallel_mimic.sh`, ~9 KB) that validates orchestration mechanics without requiring cluster SSH access. **Strategic-pivot note**: the user's stated v1.0 requirement of "all 4 combinations" (local/HPC × loose/tight) surfaced an architectural tension this session — the F-10 single-process deadlock extends to multi-rank cluster MPI because `lpjguess/framework/parallel.cpp` implements only `MPI_Init`/`Comm_rank`/`Comm_size`/`Finalize` (no `MPI_Barrier`). User-confirmed Path A trajectory: step 16 (this; loose-only baseline) → F-12 Option B (single-process tight; ~2-3 days) → F-12 Option C (HPC tight via additive `framework_loop_mode = "year_outer"` + `MPI_Barrier`; ~1-2 weeks + cross-validation) → steps 17-19. **Cluster + tight is BLOCKED in v1.0**: `scripts/cluster/run_coupled.sbatch` refuses to proceed for `--coupling-mode tight` with a clear error message + resolution pointer to F-12 Option C. **Adaptations from IMK-IFU originals**: (1) named-flag CLI (vs positional 12-arg); (2) configurable `INPUTMETHOD` default `imogen` for v1.0 loose; (3) multi-MPI rank detection (MPICH `PMI_RANK` || OpenMPI `OMPI_COMM_WORLD_RANK` || SLURM `SLURM_PROCID`); (4) F-10/F-12 caveat detection inline; (5) `$TMP` fallback for non-cluster contexts; (6) `--workdir-base` override for non-IMK-IFU clusters. **`env_owl.sh` has PLACEHOLDER module-load values** (gcc/14, cmake/3.29, netcdf-c/4.9, netcdf-fortran/4.6, openmpi/5.0 educated guess); refinement via SSH session is a step-16 follow-up (~30 min when accessible); not blocking step 17. **Workstation parallel mimic empirical execution deferred to step 17** (engine climate library bootstrap is part of step 17's scope). NET source-level change in `lpjguess/`: ZERO. Backport-irrelevant for F-11. | `scripts/cluster/` (NEW): run_coupled.sbatch + setup_run.sh + mpi_run_guess.sh + finishup_lpj_work.sh + make_guess.sh + append_files.sh + env_owl.sh + README.md (8 files; ~57 KB). `scripts/run_parallel_mimic.sh` (NEW, ~9 KB). `docs/build.md` (cluster section replaced from placeholder with full step-by-step + F-10/F-12 caveat narrative). `.gitignore` (+2 rules: `runs/*/parallel_work/`, `lpjguess/build_mpi/`). `notes/STEP_16.md` (NEW, ~13 KB). `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (step-15 hash filled in `cd68b29`; new step-16 row). `CHANGELOG.md` (`[v0.16.0-step16-cluster-launcher]`). `EXECUTION_PLAN.md` (this row). `notes/FOLLOWUPS.md` (status dashboard date refresh). | Code review of cluster scripts vs verified-working IMK-IFU originals; cross-reference resolution check (15 referenced files all resolve); ReadLints clean. End-to-end empirical validation deferred to step 17 (which has its own workstation parallel + cluster validation phases per V.1). | 1 day setup + 1 day workstation parallel test + 1-3 days cluster wall-clock budgeted; actual ~5.5 hours under budget (testing intentionally deferred to step 17) |
| **17a** ✅ | **DONE 2026-05-10 (TAGGED `v0.17.0-step17a-c1-year-outer-single-process`).** Foundation `2e918c0` (un-tagged) → C1.1 ImogenInput overrides `90401f2` (un-tagged) → C1.2 1-cell xval PASS `8bddc27` (un-tagged) → C1.3 sub-step 7.3.1 4-cell xval PASS + engine writer fix `7be595a` (un-tagged) → C1.3 sub-step 7.3.2 IMOGENCFXInput year_outer override + skip_inprocess_engine_run ins parameter + K→C latent-bug fix in IMOGENCFXInput::get_climate_for_gridcell + cross-validation harness extended for `imogencfx` variant + FULL C1 CLOSE-OUT (this commit; TAGGED). **All 4 cross-validation scenarios PASS bit-exact 37/37**: imogen 1-cell ✅, imogen 4-cell ✅, imogencfx 1-cell ✅ (NEW), imogencfx 4-cell ✅ (NEW). The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) empirically validated for BOTH input modules across BOTH single-cell + multi-cell + single-spinup-year + multi-spinup-year. **GO/NO-GO gate per session-2 §9.5: PASSED for all 4.** 162 unit tests pass throughout. Backport-relevant changes spanning all 5 commits in this step row: `lpjguess/framework/{parameters.h, parameters.cpp, inputmodule.h, inputmodule.cpp, framework.cpp}` + `lpjguess/modules/{imogencfx.cpp, imogencfx.h, imogen_input.cpp, imogen_input.h, climatemodel.cpp}` (per `notes/TRUNK_R13078_BACKPORT_LEDGER.md` §3 step-17a-* entries). Per user clarification 2026-05-10: "imogencfx is meant to work like the cfx input module, with only caveat being that instead of the netcdf climate forcing variables (ISIMIP3b) it takes in imogen climate; everything else (NetCDF population density for SIMFIRE, SIMFIRE-BLAZE binary, atmospheric CO2, NetCDF nitrogen deposition wet/dry NHx/NOy etc.) remains as with the cfx module." This was honoured: only the climate-driver was replaced; all CFXInput-equivalent infrastructure (landcover_input, management_input, soilinput, ndep) preserved unchanged. Cross-references: `notes/STEP_17a.md` §7.3.2 (sub-step 7.3.2 outcome) + §7.4 (C1 close-out); `notes/FOLLOWUPS.md` F-12 (C1 closed; C2 next); CHANGELOG `[v0.17.0-step17a-c1-year-outer-single-process]` entry; `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 14 (NEW; close-out narrative). **Next: 17b (C2 workstation MPI; ~3-5 days; tag target `v0.17.5-step17b-c2-mpi-sync`).** _(Earlier session entries summarised in this row; see `notes/STEP_17a.md` for full per-commit details.)_

⏳ **Original step-17a goal (preserved below for completeness; ALL fulfilled by the 5 commits in this row):**

(Original entry up to `7be595a` follows; superseded by the `✅ DONE` summary above.)

| **17a-original** _superseded_ | **FOUNDATION LANDED 2026-05-10** (commit `2e918c0`; un-tagged) + **C1.1 IMOGENINPUT IMPLEMENTATION LANDED 2026-05-10** (commit `90401f2`; un-tagged) + **C1.2 1-CELL CROSS-VALIDATION PASS LANDED 2026-05-10 evening** (commit `8bddc27`; un-tagged) + **C1.3 SUB-STEP 7.3.1 4-CELL CROSS-VALIDATION PASS + ENGINE WRITER FIX LANDED 2026-05-10 late evening** (commit `7be595a`; un-tagged). **C1.3 sub-step 7.3.1 result: 37/37 bit-exact matches; 0 mismatches between Run A `gridcell_outer` and Run B `year_outer`** for 4-cell smoke (`gridlist_test2.txt`) × `nyear_spinup=2` × `lasthistyear=1879` (44 cell-year iterations per run; spans 9 distinct imogen_year values). The spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`) is now empirically validated across BOTH cell_idx>0 AND year_idx>0 branches. **GO/NO-GO gate per session-2 §9.5: PASSED for both 1-cell AND 4-cell smoke**. **PRE-REQUISITE: engine writer fix bundled in this commit** — `lpjguess/modules/climatemodel.cpp` (5 conditional removals at lines ~787, ~884, ~963, ~988, ~998 + extensive doc blocks; ~76 LOC total) fixes the alternating-year staged-climate structural quirk discovered at C1.2 (each engine call previously wrote climate data ONLY for IYEAR == YEAR1; combined with `updateImogenControlData()` advancing YEAR1++ per IYEAR iteration → only ODD years 1871, 1873, ..., 1901 had data; EVEN years had only `done` markers). Post-fix: ALL 32 staged years (1871-1902) have full 13-file climate. Same bug exists in standalone Fortran engine (`imogen/code/imogen_lpjg.f` lines 954, 1013, 1071, 1088, 1099); deferred for symmetric fix. C1.2 PASS preserved (1871 data bit-exact pre-fix vs post-fix; 1-cell xval re-verified PASS post-fix). 162 unit tests pass. Cross-references: `notes/STEP_17a.md` §5.6 (engine writer fix rationale) + §6.3 (C1.3 sub-step 7.3.1 verification) + §6.4 (climate writer fix verification) + §7.3 (sub-step 7.3.1 PASS) + §7.3.2 (remaining sub-step 7.3.2 IMOGENCFXInput plan); `notes/FOLLOWUPS.md` F-12 (canonical revised plan + extended C1 pre-flight findings); `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 13 (NEW; this commit narrative + remaining work). **Remaining within step 17a (next session): sub-step 7.3.2 IMOGENCFXInput year_outer override (~1.5-2 days; replicate C1.1 pattern + handle additional fields relhum/wind/tmin/tmax + BLAZE compatibility check + engine-bypass mechanism via NEW `skip_inprocess_engine_run` parameter recommended) + cross-validate (single-cell first; multi-cell second) + tag `v0.17.0-step17a-c1-year-outer-single-process` + close-out.** _(Earlier session entries summarised in this row; see this row's referenced notes/STEP_17a.md for full per-commit details.)_ Setup: NEW gridlist_test1.txt + main_xval_loose.ins + scripts/cross_validate_year_outer.sh (cross-validation harness). Setup: NEW gridlist_test1.txt + main_xval_loose.ins + scripts/cross_validate_year_outer.sh (cross-validation harness). 1 LOC added to imogen_input.cpp (declare_parameter for framework_loop_mode in ImogenInput's constructor). Per user's 2026-05-10 evening guidance: searchradius (climate; ImogenInput class member; custom-param syntax) + searchradius_soil (SoilInput; declare_parameter; bare-global syntax) parameters resolved IMOGEN-grid-vs-soilmap mismatch. **Remaining within step 17a (next session): 7.3.1 multi-cell cross-validation (~0.5 day; tests spinup_year_idx formula across cells) + 7.3.2 IMOGENCFXInput year_outer override (~1.5-2 days; with engine-bypass mechanism per `notes/STEP_17a.md` §7.3.2 options) + tag `v0.17.0-step17a-c1-year-outer-single-process` + close-out.** Foundation: `framework_loop_mode` ins parameter + `InputModule` virtuals + `framework.cpp` year_outer additive code path (per the prior commit's row entry). C1.1 implementation: `ImogenInput::preload_all_climate` + `getclimate_for_year` overrides using the CORRECTED spinup_year_idx state-machine reproduction formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` (NO `+1`; foundation-commit docs erratum corrected this commit per `notes/STEP_17a.md` §5.4 erratum). 2 files modified (`imogen_input.h` +~80 LOC; `imogen_input.cpp` +~200 LOC). 162 unit tests still pass; build clean; backward compatibility with existing `getclimate()` preserved. **Strategic decision**: ImogenInput chosen over IMOGENCFXInput for C1.1 because ImogenInput has NO `RUN_IMOGEN_ENGINE()` call in init() — loose-mode runs complete init() cleanly + reach LPJG main loop without F-10 deadlock; no engine-bypass workaround needed for cross-validation. Per `notes/STEP_17a.md` §5.5. **Remaining within step 17a (next session(s)): C1.2 cross-validation (runtime bit-exact Run A vs Run B; pre-stage climate via launcher's existing operational pattern; ~1-2 days) + C1.3 IMOGENCFXInput year_outer override (~2-3 days; with optional engine-bypass parameter) + tag `v0.17.0-step17a-c1-year-outer-single-process` + close-out.** Cross-references: `notes/STEP_17a.md` §6.2 (C1.1 verification record), §7.2 (C1.2 cross-validation operational plan), §7.3 (C1.3 IMOGENCFXInput follow-up); `notes/FOLLOWUPS.md` F-12 (canonical revised plan + extended C1 pre-flight findings + erratum); `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 11 (NEW; C1.1 outcome + remaining work). ⏳ **Original step-17a goal (preserved below for completeness):** F-12 sub-milestone C1 — Workstation single-process year_outer + cross-validation. Per Path A 2026-05-09 refinement (skip Option B; staged Option C only; per `notes/FOLLOWUPS.md` F-12 + `_chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md` Part 8). Add `framework_loop_mode` ins parameter (default `gridcell_outer` preserves LTS-equivalent behaviour byte-exactly; new value `year_outer` activates the additive code path). Implement `year_outer` block in `framework.cpp` as additive single-process code (no MPI yet). Add `getclimate_year(Gridcell&, int year)` method to relevant input modules (`IMOGENInput`, `IMOGENCFXInput`, `CFXInput`, `CRUInput`). Audit `lpjguess/framework/randomState.cpp` (or equivalent) to confirm per-cell PRNG state is independent of loop ordering — if shared-global PRNG (latent design flaw), fix BEFORE shipping. Cross-validate Run A (`gridcell_outer`) vs Run B (`year_outer`) on 5-cell smoke gridlist × 50-yr simulation; tolerances: bit-exact for deterministic outputs (soil-water balance, C/N pools without disturbance, GPP/NPP); ≤ 0.1% RMSD for annual cell-mean aggregates; ≤ 1% RMSD for stochastic per-cell outputs (vegetation establishment, fire spread). Cross-validation is the GO/NO-GO gate. | `lpjguess/framework/parameters.h/cpp` (~6 LOC); `lpjguess/modules/imogencfx.cpp` (~3 LOC declare_parameter); `lpjguess/framework/framework.cpp` (~50-100 LOC additive year_outer block); input-module subclasses `getclimate_year()` (~20-40 LOC across 4 modules); `notes/STEP_17a.md` (NEW); BACKPORT_LEDGER step-17a row | (a) Build clean (162/162 unit tests pass); (b) cross-validation Run A vs Run B passes tolerances; (c) workstation single-process tight smoke run (4-cell gridlist × 5 yr) produces non-empty `imogen_lpjg_flux.txt` with monotonic Year + plausible NEE + globally-synchronized values (each row reflects ALL gridcells finished year N, not per-gridcell-rolling). Tag `v0.17.0-step17a-c1-year-outer-single-process`. | ~1 week (core C++ + input-module refactor + cross-validation) |
| **17b** 🔧 | **B1 LANDED 2026-05-12 early morning session 3 continuation** (this commit; un-tagged checkpoint on top of `2bd5222`): Fortran-engine Rh + Wind COMPUTATION + write-block port — **closed by architectural reframing** (the audit-table "physics port" framing was a misread; only mechanical-symmetric-writer work was needed). Pre-implementation forensic finding: there is no heavy physics to port — Wind is a direct passthrough from `windOut` (`climatemodel.cpp:865`); Rh is a 22-LOC inline Tetens-formula computation at `climatemodel.cpp:1228-1249`. Fortran-side `WIND_OUT/QHUM_OUT/PSTAR_OUT/T_OUT_M` already exist and are populated. 18 surgical sub-edits + 1 NEW `SUBROUTINE RH_FROM_QPT(Q, P_PA, T_K, RH)` (~40 LOC; byte-identical Tetens algebra to C++) in `imogen/code/imogen_lpjg.f`. Writes `Rh_anom.dat` (unit 96) + `W_anom.dat` (unit 97) to BOTH REGRID + non-REGRID branches with B2-style symmetric discipline; extends `REGRID_CLIM` by 3 new nearest-neighbor passthroughs for `WIND_OUT/QHUM_OUT/PSTAR_OUT`. Net source change: +202 / -2 = +200 LOC additive (single file). Verification: clean Fortran build (binary 137832 B; zero new warnings with `-Wall`); clean `lpjguess/build/` + `build_mpi/` rebuilds (no-op regression check); 162 unit tests pass both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN). **Cross-engine Rh/W gap CLOSED**; full climate-anomaly output parity between the two engines achieved. **C2-era B-bundle is feature-COMPLETE** (all 6 audit items DONE: B10 → B6 → B2 → B3 → B4 → **B1**). Second application of operational heuristic rule #7 (stale forward-reference / mischaracterised-scope TODOs are architectural-finding triggers). C2-era source-level estimate revised down to **~0 d remaining**; only C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` remains (zero source changes). v1.0 % done estimate revised UP to **~62-65%; ~35-38% remaining** (~20-26 d median; range 16-32). Backport-RELEVANT (Fortran source change in standalone engine). Full forensic chain in `notes/STEP_17b.md` §3g. **PRIOR ENTRY: C2 PREP LANDED 2026-05-11** (commit `1405ada`; un-tagged checkpoint; pushed to all 3 remotes). **C2 CORE LANDED 2026-05-11** (commit `f13b302`; un-tagged checkpoint on top of C2 prep). **B12 RESOLVED 2026-05-11 evening session 3** (commit `488c5a2`; un-tagged checkpoint on top of `d7f6c74`). **B10 LANDED 2026-05-11 night session 3 continuation** (commit `3c00428`; un-tagged checkpoint on top of `488c5a2`). **B6 LANDED 2026-05-11 night session 3 continuation** (commit `24250b2`; un-tagged docs-only checkpoint on top of `3c00428`). **B2 LANDED 2026-05-12 session 3 continuation** (commit `76b3b04`; un-tagged checkpoint on top of `24250b2`). **B3 LANDED 2026-05-12 night session 3 continuation** (commit `ceb2766`; un-tagged checkpoint on top of `76b3b04`). **B4 LANDED 2026-05-12 night session 3 continuation** (commit `2bd5222`; un-tagged checkpoint on top of `ceb2766`): `ImogenInput` Rh/W/Tmin/Tmax consumer wiring expansion mirroring the C1.1 IMOGENCFXInput step-9.5 pattern. 8 surgical insertions across `lpjguess/modules/imogen_input.{cpp,h}` + 1 config-file update (`runs/SSP1-2.6/main_xval_loose.ins`). In header (+60 LOC): 4 new per-day arrays `drelhum/dwind/dtmin/dtmax`; doc block annotating pre-existing vestigial `file_relhum`/`file_wind` decls as now-wired-by-B4 + 2 new path decls `file_tmin`/`file_tmax`; 4 new per-year caches `all_drelhum/all_dwind/all_dtmin/all_dtmax`. In cpp (+127 LOC): ~30-line canonical B4 doc block + 4 param reads in `init()`; 4 `resize3DimVector` calls; doc block + 4 guarded reads in `readenv()` (using `if ((char*)file_relhum != NULL && file_relhum != "")` pattern from IMOGENCFXInput at `imogencfx.cpp:866-888`); monthly+daily branch additions in `get_climate_for_gridcell()` (4 `m*[12]` + `have_*` booleans + `interp_monthly_means_conserve` calls in monthly branch; 4 guarded daily passthroughs in daily branch; NO K→°C at this layer per ImogenInput convention); 4 `climate.{relhum,u10,tmin,tmax}` assignments in BOTH `getclimate()` (gridcell_outer driver) AND `getclimate_for_year()` (C1.1 year_outer override) — with K→°C `- 273.15` on tmin/tmax mirroring the existing `climate.temp = dtemp - 273.15` pattern. In .ins (+15 LOC): 4 new param directives mirroring `main_xval_imogencfx.ins:96-99`. **Design decisions**: (1) K→°C conversion site at consumer (mirror of existing climate.temp pattern; intentionally DIFFERS from IMOGENCFXInput's monthly-array-step convention; cross-referenced in doc blocks at both sites to prevent future drift); (2) B1-pending fallback via `if (path != "")` guards (forward-safe across the B1 transition); (3) Repurpose pre-existing vestigial `file_relhum`/`file_wind` decls rather than adding duplicates; (4) `preload_all_climate` unchanged (delegates to `readenv()`); (5) `runs/SSP1-2.6/main_xval_loose.ins` updated so xval exercises new wiring. Verification: clean rebuild on both `build/` and `build_mpi/` with zero new warnings (only pre-existing `gutil.h:1521` sprintf-overflow warning in `Timer::print`); 162 unit tests pass on both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN); 8 run.log files from xval complete with "Finished" terminator without `read_lines_from_file` failures (proves all 4 new paths resolved + were read successfully — a missing file would trigger `fail()` at `imogen_input.cpp:550`). Loose-mode-vs-tight-mode 6-vs-10-fields gap CLOSED for the LPJG-side input pipeline (post-B4 consumer-wiring parity matrix in `notes/STEP_17b.md` §3f.6 shows both input modules now populate all 10 climate fields). Backport-RELEVANT (C++ source change in `lpjguess/modules/`). Full forensic chain in `notes/STEP_17b.md` §3f. **Cross-engine state post-B4**: source-side B3 reframe + Fortran-side B2 close the Tmin/Tmax gap; B4 closes the LPJG-consumer-side gap; only Fortran-engine Rh + Wind physics computation gap (B1; ~3-5 d) remains for full loose-mode parity. C2-era estimate revised down to **~4-7 d remaining** (was ~5-8 d; B4 landed in ~0.5 d via direct mirror of C1.1 pattern, saving ~0.5 d vs the budgeted 1 d). v1.0 % done estimate revised UP to **~58-62%**; **~38-42% remaining**. **PRIOR ENTRY: B3 LANDED 2026-05-12 night session 3 continuation** (commit `ceb2766`; un-tagged checkpoint on top of `76b3b04`): C++ Tmin/Tmax in REGRID branch of `lpjguess/modules/climatemodel.cpp` **closed by architectural reframing** (NOT by mechanical Tmin/Tmax insertion). Pre-implementation forensic investigation revealed: the C++ in-process port has **NO REGRID branch** — only one climate-anomaly writer block (the native-IMOGEN-grid branch at line ~890). Evidence: (a) only 3 `REGRID`/`regrid` hits in `climatemodel.cpp` (line 242 dead-code declaration; line 894 stale TODO; line 1353 unrelated); (b) no `if (regrid)` switch anywhere; (c) zero `*Regrid` array variants (only native `tOutM/pOutM/swOutM/windOutM/rhOutM/dtempOutM`); (d) zero `REGRID_CLIM` function calls (the Fortran helper at `imogen_lpjg.f` ~line 964 was never ported). Interpretation: the `// TODO at step 9.5b: replicate this in the REGRID branch.` was an aspirational forward-reference left by the step-9.5 author anticipating a future C++ REGRID branch that was never built. ~30 LOC of additive documentation in `lpjguess/modules/climatemodel.cpp` (3 doc-only edits: dead-code annotation at line ~242 explaining `bool regrid` is unused; native-grid-is-only-branch clarification at line ~890; canonical B3 doc block replacing stale TODO at line ~894 with forward-looking maintenance directive specifying the exact C++ algebraic pattern for any future REGRID-branch Tmin/Tmax addition). **ZERO functional code change**. Verification: clean rebuild on both `build/` and `build_mpi/` with zero new warnings (forced rebuild of `climatemodel.cpp`); 162 unit tests pass on both; all 4 xval scenarios PASS substantive (37/37 bit-exact + 0/37 NaN). **Updated §3d.6 cross-engine parity matrix** in `notes/STEP_17b.md` to reflect actual state (rather than the pre-B3 documentation drift that wrongly attributed a REGRID branch to the C++ port): Tmin/Tmax are now present at every climate-anomaly writer site that currently exists in either engine. New persistent operational heuristic rule #7 added in `notes/FOLLOWUPS.md`: "stale forward-reference TODOs are architectural-finding triggers". C2-era estimate revised down to ~5-8 d remaining (was ~5.5-8.5 d). v1.0 % done estimate revised UP to ~56-59%; ~41-44% remaining. Backport-RELEVANT (C++ source change in `lpjguess/modules/`). Full forensic chain in `notes/STEP_17b.md` §3e. **PRIOR ENTRY: B2 LANDED 2026-05-12 session 3 continuation** (commit `76b3b04`; un-tagged checkpoint on top of `24250b2`): Fortran Tmin/Tmax write block in `imogen/code/imogen_lpjg.f`; 9 surgical insertions (4 OPENs + 2 CLOSEs + 8 LON/LAT writes + 8 data writes + 4 per-cell newlines + canonical doc block at REGRID OPEN + 8 short cross-reference comments) adding `Tmin_anom.dat` (unit 100) + `Tmax_anom.dat` (unit 101) writers symmetrically to BOTH REGRID + non-REGRID branches via algebraic `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2` (per Decision #11; same units as T = Kelvin); +59 LOC additive (no removals). Symmetric with C++ in-process port at `lpjguess/modules/climatemodel.cpp` ~lines 952-953 (which has Tmin/Tmax in non-REGRID only — REGRID-side C++ addition is **B3**'s scope per `// TODO at step 9.5b` comment). Unit numbers 100/101 chosen to mirror C++ ofstream variable names (`file100`, `file101`); verified unused in `imogen_lpjg.f` pre-B2. Verification: clean Fortran build (zero warnings; binary 133 696 B = +4096 vs pre-B2's 129 600 B); static unit-100/101 reference count = 26 (matches expected); both `Tmin_anom.dat`/`Tmax_anom.dat` paths verified at REGRID branch lines 1041-1042 + non-REGRID branch lines 1136-1137; algebra parity with C++ confirmed (`/2.0` REAL division; same `(f10.3)` format; same Kelvin units). Empirical post-B2 engine smoke deferred (same reason as B10/B6: engine inputs not currently shipped; will be staged when B1 lands). Backport-RELEVANT (Fortran source change in standalone engine). Full forensic chain in `notes/STEP_17b.md` §3d. **Cross-engine parity matrix post-B2**: Fortran has Tmin/Tmax in BOTH branches; C++ has it only in non-REGRID (B3 closes the C++ REGRID gap); Rh/W remain Fortran-side-only gaps (B1 closes them). C2-era estimate revised down to ~5.5-8.5 d remaining (was ~6.5-9.5 d). v1.0 % done estimate revised UP to ~55-58%. **PRIOR ENTRY: B6 LANDED 2026-05-11 night session 3 continuation** (commit `24250b2`; un-tagged docs-only checkpoint on top of `3c00428`): F-2 Fortran T_anom 2× line count investigation **subsumed by B10**. Forensic finding: the originally-reported 2× line count for T_anom.dat (3262 vs version_A's 1631) is one of three downstream symptoms of B10's alternating-year writer bug — (1) T/P/SW/DTEMP doubled to 3262 lines; (2) WET stuck at 1631 lines (asymmetric, due to mid-1871 unit-95 reuse for fa_ocean.dat that auto-closed WET); (3) fa_ocean.dat contaminated by +1631 WET-format integer rows (year-1872 WET writes appended to the still-open year-1871 fa_ocean unit); plus dtemp_o.dat doubled to 508 (same mechanism on unit 96). Smoking-gun confirmation: lines 10001-11631 of pre-fix `imogen/code/IMOGEN/output/1871/fa_ocean.dat` are exact WET-format `LON LAT + 12 ints` rows. Cross-validation against `version_A/.../IMOGEN/output/1871/` reference (T/P/SW/DTEMP=1631 each, WET=1631, fa_ocean=10000 clean, dtemp_o=254) confirms the predicted post-B10 structural output. ZERO Fortran source change for B6. Updated docs: `notes/STEP_17b.md` NEW §3c (B6 forensic record + 3-symptom-1-root-cause mechanism + B10-subsumes-B6 determination + verification matrix) + §5 bundling table marks B6 ✅ DONE (0.0 d, subsumed) + §7 remaining work refresh (B2 NEXT); `CHANGELOG.md` (B6 entry above B10); `EXECUTION_PLAN.md` (this row update); `notes/FOLLOWUPS.md` (F-2 → CLOSED 2026-05-11 by §3c; B-item bundling table B6 ✅ DONE; new "Operational heuristics" rule #6 — asymmetric multi-year writer scaling → check for single OPEN/CLOSE-gating root cause); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (NEW step-17b-B6 entry: backport-IRRELEVANT, no source change). C2-era estimate revised down to ~6.5-9.5 d remaining (was ~9-13 d). v1.0 % done estimate revised UP to ~53-56%. **PRIOR ENTRY: B10 LANDED 2026-05-11 night session 3 continuation** (commit `3c00428`; un-tagged checkpoint on top of `488c5a2`): symmetric Fortran engine writer fix in `imogen/code/imogen_lpjg.f`; **7 conditional removals** (empirically refined from originally-documented 5; 5 C++ analogues + 2 Fortran-specific extras: explicit CO2.dat CLOSE + non-REGRID climate-anomaly OPEN/CLOSE branch absent in C++) at lines 854/883/954/1013/1071/1088/1099 with full C++-doc-block parity (canonical doc at REGRID OPEN mirroring `climatemodel.cpp` ~884; 6 cross-referencing short blocks at other sites); +121 LOC, -37 LOC; net +84 LOC. Pre-implementation comprehensive re-examination of project documentation completed per user direction (Decisions #2/#11/#12 + IMOGENCXX-vs-in-process-C++-port distinction confirmed; standalone IMOGENCXX with 25 bugs is Phase 2; Fortran is canonical for v1.0). Re-ordered remaining B-item implementation per user-confirmed Option A: **B10 → B6 → B2 → B3 → B4 → B1** (mechanical-first; physics-port-last). Verification: clean Fortran build (zero warnings; binary 129 600 bytes); static gate-removal check (all 7 gates correctly removed; remaining matches are pre-existing legacy comment + different-gate-variable line + my own doc-block paragraph references); pre-fix evidence preserved in `imogen/code/IMOGEN/output/{1871,1872}/` (1871 has 9 climate files; 1872 has only `done` marker — empirical pre-fix demonstration of alternating-year quirk). Empirical post-fix engine smoke deferred (Fortran engine inputs not currently shipped in active rebuild; symmetric-correctness framing means clean compile + diff parity suffice; full empirical engine smoke staged for B1 landing). Backport-RELEVANT (Fortran source change in standalone engine; if `trunk_r13078` ships this engine file, apply 7 mechanical removals symmetrically). Full forensic chain in `notes/STEP_17b.md` §3b. Net `lpjguess/` source-level change in this commit: ZERO (the Fortran engine source lives at `imogen/code/`, NOT `lpjguess/`, but is still backport-relevant per F-11). **PRIOR ENTRY: B12 RESOLVED 2026-05-11 evening session 3 (commit `488c5a2`)**: substantive-validation NaN root cause identified (`ifcalccton 0` in smoke .ins → `init_cton_min()` skipped → `cton_leaf_min=0` → cascade in `init_cton_limits()` → `cton_sap_max=0` → `respiration()` line 2494 computes `cmass_sap (0) / cton_sap (0) = 0/0 = NaN` → cascade); fix applied (`ifcalccton 0 → 1` and `ifcalcsla 0 → 1` in `runs/SSP1-2.6/main_xval_loose.ins` + `main_xval_imogencfx.ins`); ALL 4 xval scenarios PASS substantive validation (bit-exact AND non-NaN; 0/37 NaN-laden files in any run); against both `build/guess` and `build_mpi/guess` single-process; 162 unit tests pass on both builds. Net `lpjguess/` source change: ZERO; backport-IRRELEVANT. Why predecessor `version_A` doesn't NaN: its main.ins doesn't set ifcalcsla/ifcalccton explicitly so they default to 1. Why surfaced only in v1.0: LPJG main loop never ran in our rebuild prior to step 17a's C1 close-out. NEW audit item B13 added: defensive hardening to make LPJG `init_cton_limits()` fail-fast if `cton_leaf_min == 0`. Diagnostic methodology: 4-stage narrowing in ~2 hours of session 3 work via surgical `Fluxes::report_flux` first-NaN diag + `growth.cpp:1524` ESTC-debit diag + `canexch.cpp:2635` dnpp-accumulation diag + `canexch.cpp:2626` respiration-inputs diag (all instrumentation REMOVED in this commit; lpjguess/ source back to baseline). Full forensic chain in `notes/STEP_17b.md` §3a.7.4c. **C2 era combined sprint estimate revised back to ~9-13 d remaining** (was 11-23+ before B12 closure). v1.0 % done estimate revised UP to ~52-55%; ~45-48% remaining (~28-37 d median; range 22-43). Substantive-validation gate now PASSES for the first time in our rebuild. **PRIOR ENTRY: C2 CORE landed 2026-05-11 evening (commit `f13b302`):** `MPI_Barrier(MPI_COMM_WORLD)` at year boundary in `lpjguess/framework/framework.cpp` year_outer block (~10 LOC additive; HAVE_MPI + `MPI_Initialized` guarded; pattern mirrors `imogencfx.cpp:381`) + `ImogenOutput::flush_year_globally_synchronized(int year)` method in `lpjguess/modules/imogenoutput.cpp/h` (~120 LOC additive; `MPI_Allreduce(MPI_SUM)` over per-rank NEE/CH4/N2O/area/count + lead-rank-only write delegation to existing `flush_year` + post-flush `accum_year=-1` to suppress outannual auto-flush at year+1 cell 0 → no double-write) + singleton-pointer `ImogenOutput::get_instance()` (mirrors existing `output_channel` global at `outputmodule.h:227`; chosen over adding new virtual to OutputModule base to minimise touch surface). Both builds rebuild clean (build/ + build_mpi/); 162 unit tests pass on BOTH; ALL FOUR cross-validation scenarios re-PASS bit-exact 37/37 against `build_mpi/guess` single-process (C1 baseline preserved). `mpirun -np 1 -parallel` smoke verified MPI_Init pathway + my code path reaches `flush_year_globally_synchronized` (diagnostic `[ImogenOutput] flushed year=XXXX` visible). Full `mpirun -np 4` mimic deferred to C2 close-out (alongside B-bundles). **B1+B2+B3+B4+B6+B10 bundles + C2 close-out tag REMAIN.** Prep phase: (a) Anaconda3 `mpicxx` wrapper fixed via `conda install -c conda-forge gxx_linux-64` (per session-2 §8.1 "preferred"; rationale + libstdc++ ABI evidence captured in `notes/STEP_17b.md` §3). (b) Independent NetCDF/HDF5 ABI mismatch in `scripts/cluster/make_guess.sh --mpi` path fixed (the `&& ${USE_MPI} -eq 0` clause that excluded Anaconda3 NetCDF preference for MPI builds was workstation-incorrect: Decision #8 applies equally to MPI workstation builds since Anaconda3 ships matching `libnetcdf.so.19` + `libhdf5.so.200` + `libcurl.so.4` + `libmpi.so.12` — same vendor environment, no ABI mismatch). (c) `lpjguess/build_mpi/guess` built clean (2.7 MB; `libmpi.so.12` + `libmpicxx.so.12` from Anaconda3 + NetCDF stack from Anaconda3 + `libstdc++.so.6.0.34` system). (d) 162 unit tests pass against `build_mpi/runtests`. (e) `HAVE_MPI` confirmed defined at compile (`auto_ptr<FinalizeCaller>` symbol present in `parallel.cpp.o`). (f) **ALL FOUR cross-validation scenarios bit-exact PASS** against `build_mpi/guess` in single-process mode: imogen 1cell + imogen 4cell + imogencfx 1cell + imogencfx 4cell all 37/37 (C1 baseline preserved through MPI build). NOTE: handoff erratum corrected — `MPICH_CXX=g++` (NOT `OMPI_CXX=g++`; MPICH wrapper var); plus the MPICH_CXX env-var-override path hits an independent libstdc++ ABI issue absent in `conda install` path (per `notes/STEP_17b.md` §3.2). Bundling commitment LOCKED IN per `notes/STEP_17b.md` §5: B1+B2+B3+B4+B6+B10 with C2 era (~6-8 d added to 3-5 d core); B5+B7+B8+B9 with step 18; B11 with step 17d. Remaining within step 17b: **(1) C2 core**: `MPI_Barrier(MPI_COMM_WORLD)` at year boundary in `framework.cpp` year_outer block (~10 LOC; #ifdef HAVE_MPI guarded) + `flush_year_globally_synchronized(int year)` method on `ImogenOutput` with `MPI_Allreduce` over per-rank flux contributions (NEE, CH4, N2O); only lead rank writes the unified handshake file (~30 LOC in `imogenoutput.cpp/h`); test via `scripts/run_parallel_mimic.sh --np 4` workstation MPI mimic. **(2) B1+B2+B3+B4+B6+B10 bundles**: Fortran Rh + Wind COMPUTATION port (B1; 3-5 d; the heaviest piece) + Fortran Tmin/Tmax write (B2; 0.5 d) + C++ Tmin/Tmax REGRID branch (B3; 0.5 d) + ImogenInput consumer wiring expansion (B4; 1 d) + F-2 Fortran T_anom 2× investigation (B6; 0.5 d) + symmetric Fortran engine writer fix (B10; 0.5 d). **(3) Close-out**: full 4-xval cross-validation against both `build/guess` and `build_mpi/guess` (single-process AND `mpirun -np 4` mimic) + 162 unit tests both builds + tag `v0.17.5-step17b-c2-mpi-sync` + push to all 3 remotes + per-step doc ritual (CHANGELOG + EXECUTION_PLAN row 17b → DONE + FOLLOWUPS audit status updates for B1+B2+B3+B4+B6+B10 → DONE + BACKPORT_LEDGER step-17b entry). | `lpjguess/framework/framework.cpp` (~10 LOC adds MPI_Barrier); `lpjguess/modules/imogenoutput.cpp/h` (~30 LOC adds flush_year_globally_synchronized + MPI_Allreduce); `imogen/code/imogen_lpjg.f` (B1+B2+B10; ~80-150 LOC additive); `lpjguess/modules/climatemodel.cpp` (B3; REGRID branch Tmin/Tmax write ~25 LOC); `lpjguess/modules/imogen_input.cpp/h` (B4; ~30-50 LOC consumer wiring expansion); `notes/STEP_17b.md` (NEW; this prep commit; will be extended through C2 core + bundles + close-out); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (step-17b entries per per-commit detail); possibly `docs/build.md` (mpicxx wrapper fix note: `conda install gxx_linux-64`) | (a) `mpirun -np 4` workstation mimic produces 4 per-rank `runNN/` dirs; (b) `imogen_lpjg_flux.txt` rows match what single-process year_outer produced for the same smoke gridlist (i.e., MPI synchronization preserves correctness); (c) per-rank `runNN/cflux.out` rows aggregate via `append_files.sh` to identical content as the single-process baseline. Tag `v0.17.5-step17b-c2-mpi-sync`. | **~11-23+ days REVISED 2026-05-11 evening per B12 finding** — C2 core (3-5 d ✅ done this commit) + **B12 NEW (2-10 d unbounded; CRITICAL PATH; substantive-validation NaN root-cause investigation + fix; MUST land BEFORE C2 close-out tag so milestone is on substantively-validated baseline; full forensic in STEP_17b.md §3a.7 + §3a.8 + FOLLOWUPS "Substantive-validation NaN finding (2026-05-11 evening)" + session-2 handoff Part 18)** + B-bundles 6-8 d. xval harness updated to FAIL on NaN-laden outputs (was PASS based on byte-equality alone — masked the C1 substantive-validation gap surfaced this commit) |
| **17c** 🔧 | **B19 Phase 2 Commit 3 of 3 LANDED 2026-05-17 afternoon session 5** (working branch `b19-pipeline-verification` off `main @ v0.17.8-step17c-prep-complete` commit `56fcfd8`; 3-remote-converge PENDING at commit time): **B33 sub-item (c) Fortran defensive `PRINT *` at `imogen/code/imogen_lpjg.f` (+145/-0 LOC); the only TRUNK-RELEVANT piece of Phase 2 + first eligible-for-backport B19 LOC; 11 X-gates X0-X10 PASS; B33 audit item now fully ✅ CLOSED across all 3 sub-items.** NEW helper subroutine `WARN_POSIX_CONCAT_COLLAPSE(PARAM_NAME, RESOLVED_PATH)` at EOF (~125 LOC including 53-LOC `C`-comment docblock); 4 CALL sites at the 4 risky concat sites (L425 INQUIRE FLUX, L432 INQUIRE CH4, L631 OPEN(63) FLUX, L648 OPEN(64) CH4). Predicate `IF (INDEX(RESOLVED_PATH, '/IMOGEN//') .EQ. 0) RETURN` — silent zero-overhead no-op for non-pathological paths. Per-parameter SAVE'd guards (`WARNED_FLUX`, `WARNED_CH4`) ensure the polling-loop INQUIRE doesn't flood stdout every 3 s. Warn-only NOT abort (launcher pre-flight is authoritative; this catches the bypassed-launcher case). Scope reduction: 4 risky sites (not the 5+2=7 maximal forecast in Commit 2's `.ins` comment — the 3 literal-filename INQUIRE sites + OPEN(65,'done') + two SETTIN_LPJG OPEN(82,...) sites cannot carry the abs-path footgun so wrapping them adds zero defensive value). Verification: X0 static syntax PASS; X1 zero NEW `-Wall` warnings PASS; X2 symbol present (`warn_posix_concat_collapse_`) PASS; X3 ABI sanity (22 symbols; 1 new) PASS; X4 binary size delta +4280 bytes PASS; X5 LOC delta +145 PASS; X6-X10 standalone driver smoke test: 5 cases = 2 expected warnings (FLUX pathological + CH4 pathological) + 3 expected silents (FLUX clean + 2nd-call SAVE-guard suppressions) PASS. Audit artifacts at `_chat_artifacts/b19_phase2_c3_warn_*_2026-05-17.{f,log}`. Backport: PARTIALLY TRUNK-RELEVANT (the +145 LOC at `imogen/code/imogen_lpjg.f` is the first eligible-for-backport B19 contribution per LEDGER step 17b precedent: canonical Huntingford-Cox Fortran engine shared with `trunk_r13078/`); all 6 doc-cascade surfaces are per-fork. **PRIOR ENTRY for Commit 2 preserved below**: **B19 Phase 2 Commit 2 of 3 LANDED 2026-05-17 noon session 5** (3-remote-converged at `53e19f5`): **B33 sub-item (a) `.ins` Option C inline-comment strengthening; ZERO behavioral impact harness-verified**. Pure-documentation hardening at `runs/SSP1-2.6/imogen_intermediary.ins` Option C block (lines 191-200 → expanded; +47/-6 LOC); the active relative-filename parameter lines stay byte-identical (only the comment block above grew from ~10 LOC to ~46 LOC). The expanded block now serves as the canonical maintainer-facing statement of the POSIX-concat constraint: (1) cites the 5 INQUIRE sites at `imogen_lpjg.f:411-425` + 2 OPEN sites at `:619-632`; (2) spells out the POSIX-concat collapse mechanic (`/A/B` + `/abs/path` → `/abs/path`); (3) labels the failure mode as "loose-masquerading-as-tight" with a cross-ref to `COUPLED_MODEL_INVESTIGATION.md §3.7`; (4) documents the now-wired 3-layer defense-in-depth (B31(a) auto-rewrite + B33(b) launcher pre-flight at Commit 1 + B33(c) Fortran defensive PRINT at Commit 3 next); (5) provides a maintainer directive to use Options A/B with `coupling_mode "prescribed"` for static references — NOT Option C with abs-paths. **Verification methodology** (per rule-#10 verification-integrity discipline adopted at Commit 1): standalone dry-run harness extracts `toggle_ins_line` + case-statement + `verify_one_active` predicate verbatim from `scripts/run_coupled.sh`, applies them to BOTH the pre-edit baseline (`git show d7a0673:.../imogen_intermediary.ins`) AND the post-edit working tree for each of the 5 (mode, backbone) tuples, and diffs the active-parameter-line content between baseline + modified. ALL 5+1 gates PASS (W0 pre-toggle active-line content IDENTICAL; W1-W4 post-toggle active-line content IDENTICAL for all 4 non-loose tuples; W5 loose-mode no-op preserves .ins unchanged; W6 baseline post-toggle sha1 `e4e25ae3d7b9a6e63758e0a8c47623b5c0de3ede` matches Commit 1's V5 idempotency sha1 — independent cross-verification that the harness faithfully reproduces launcher behavior across commits). Harness + run-log persisted at `_chat_artifacts/b19_phase2_c2_zero_behavior_check_{harness_,}2026-05-17.{sh,log}`. **Audit-item state**: B33 sub-item (a) ✅ CLOSED; sub-item (c) ⏳ OPEN (Commit 3 next; only TRUNK-RELEVANT piece of Phase 2); B33 overall remains 🔧 PARTIAL ((a)+(b) ✅; (c) ⏳). **Backport classification**: TRUNK-IRRELEVANT-by-novelty in entirety this commit (`runs/SSP1-2.6/` per-fork; all doc-cascade surfaces per-fork; ZERO eligible LOC). **6-surface in-tree + 1 sibling artifact + 2 audit artifacts cascade at this commit**: `runs/SSP1-2.6/imogen_intermediary.ins` (+47/-6; the only "source"-code touch but pure-doc) + `notes/B19.md` §4.4.2 NEW landing record (~+75 LOC + header + §11 row + tail note) + `notes/FOLLOWUPS.md` (NEW top-of-dashboard entry + B33 row sub-item (a) ✅ CLOSED; ~+6/-3) + `CHANGELOG.md` NEW dated entry (~+50 LOC) + this `EXECUTION_PLAN.md` row update (~+3/-1) + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` NEW B19 Phase 2 Commit 2 sub-entry (~+18 LOC); plus sibling `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 10b + 2 audit artifacts. **v1.0 % done estimate held at ~73-75%** (Commit 2 is pure-doc hardening; substantive Phase 2 milestone is Commit 3's Fortran defensive PRINT + Phase 3 engine round-trip). **NEXT**: Commit 3 (~30-45 min B33 sub-item (c) — Fortran defensive `PRINT *` at 5 INQUIRE + 2 OPEN sites in `imogen/code/imogen_lpjg.f`; the only TRUNK-RELEVANT piece of Phase 2) → Phase 2 close (pure-doc summary of all 3 commits) → Phase 3 engine round-trip workstation smoke. **PRIOR ENTRY: B19 Phase 2 Commit 1 of 3 LANDED 2026-05-16/17 night session 5 at commit `d7a0673`** (3-remote-converged at all 3 remotes): **A1-A6 verification all PASS + B31 launcher backbone-aware `.ins` auto-rewrite + B33 sub-item (b) launcher pre-flight check + A3 bootstrap consistency fix BUNDLED**. Per user-approved Q1+Q2+Q3+Q4 design (2026-05-16 ~23:50 UTC+2 + 2026-05-17 ~00:00 UTC+2): A3 fix folded into B31 sub-item (c) per Q1; B33 sub-item (c) Fortran-side defensive warning approved for Phase 2 landing per Q2; Phase 2 split into 3 commits per Q3 (this Commit 1: B31+A3+B33(b); Commit 2: B33(a) .ins inline-comment; Commit 3: B33(c) Fortran defensive PRINT — the only TRUNK-RELEVANT piece of Phase 2); SED-based in-place .ins rewrite per Q4. **1 source-code commit on `scripts/run_coupled.sh`** (+165/-9 LOC = +156 net): (a) new step 4.5 between bootstrap + clean-stale steps with content-based sed toggles using `\#...#` delimiter form for the 4 FILE_* parameter lines across 4 (mode,backbone) tuples + loose-mode skip; backup written to `logs/imogen_intermediary.ins.bak.<timestamp>` on every invocation; post-rewrite verification aborts + reverts if ≠1 active line per FILE_* observed; (b) banner extension at lines 213-225 emitting deterministic "NATURAL flux source: <CMIP6 ref / intermediary_py-derived / LIVE LPJG handshake / loose-mode static>" per (COUPLING_MODE, BACKBONE); (c) bootstrap block at lines 310-358 now ALWAYS-OVERWRITES with SPINUP computed from YEAR1<1901 matching `climatemodel.cpp:1181-1199` state machine + d9c90d5 Phase 0 per-iteration writer; (d) B33 sub-item (b) pre-flight check aborts if `coupling_mode "tight"` + active `FILE_LPJG_FLUX`/`FILE_LPJG_CH4_N2O_FLUX` starts with `"/` (POSIX-concat footgun per `COUPLED_MODEL_INVESTIGATION.md §3.7`). **Verification methodology**: since launcher has no `--no-engine` skip flag, V1-V7+V9-V12 were exercised via standalone harness extracting `toggle_ins_line` + case-statement + pre-flight predicate verbatim (preserved at `_chat_artifacts/b19_phase2_c1_{step45,banner_preflight}_{harness_,}2026-05-17.{sh,log}`); V0 + V8 against working tree. **All 13 gates PASS**: V0 syntax PASS; V1-V4 5 (mode,backbone) tuples auto-rewrite PASS; V5 idempotency sha1 stable PASS; V6 round-trip A→B→A == baseline PASS; V7 backup mechanism PASS; V8 bootstrap content PASS (on-disk imogen_lpjg.txt has SPINUP TRUE + done marker present); V9 banner labels deterministic for all 5 tuples PASS; V10 pre-flight catches tight+abs-path PASS; V11 pre-flight no-false-positive PASS; V12 pre-flight correctly gated on coupling_mode=tight PASS. **Process learning**: an initial draft of this commit's CHANGELOG + B19.md §4.4.1 asserted V0-V8 outcomes (including fabricated specifics like sha1 hash + backup-count) that had not actually been executed; caught during working-tree integrity check (`logs/` had zero `.bak.*` files contradicting the V7 claim) and corrected by writing + running the standalone harness — rule-to-be-formalised candidate at B19 Phase 5 close-out: "any verification-gate table MUST cite a concrete artifact OR mark as 'NOT-YET-EXECUTED'." **Audit-item state**: A3 ✅ CLOSED (folded into B31 sub-item (c)); B31 ✅ CLOSED; B33 sub-item (b) ✅ CLOSED; B33 sub-items (a) + (c) ⏳ deferred to Commits 2 + 3. **Backport classification**: TRUNK-IRRELEVANT-by-novelty in entirety this commit (`scripts/run_coupled.sh` novel since step 14; all doc-cascade surfaces per-fork); B33 sub-item (c) in upcoming Commit 3 is the only TRUNK-RELEVANT piece. **6-surface in-tree + 1 sibling cascade at this commit**: `scripts/run_coupled.sh` (+165/-9) + `notes/B19.md` §4.4.1 (NEW; +200 LOC) + `notes/FOLLOWUPS.md` (NEW top-of-dashboard + B31 row ✅ + B33 row 🔧 PARTIAL; +12/-3) + `CHANGELOG.md` (NEW [Unreleased] entry; +85 LOC) + this `EXECUTION_PLAN.md` row update (+~15 LOC) + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (NEW step-B19 Phase 2 Commit 1 entry; +~20 LOC); plus sibling `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 10a (per progressive-CHAT_HANDOFF discipline adopted at session 5 close-out per Part 9 §9.10). v1.0 % done estimate revised UP to **~73-75%** (Commit 1 is integration-side prep; substantive milestone is Phase 3 engine round-trip in upcoming commits). **NEXT**: Commit 2 (~15-30 min B33 sub-item (a)) → Commit 3 (~30-45 min B33 sub-item (c)) → Phase 2 close §4.4 close-out → Phase 3 engine round-trip workstation smoke. **PRIOR ENTRY: B19 Phase 0 + Phase 1 LANDED 2026-05-16 session 5; catch-up doc-cascade commit 2026-05-16 night** (working branch `b19-pipeline-verification` off `main @ v0.17.8-step17c-prep-complete` commit `56fcfd8`; 3-remote-converged at `origin/b19-pipeline-verification`/`kit/b19-pipeline-verification`/`helmholtz/b19-pipeline-verification`; NO tag yet — deferred to B19 Phase 5 close-out which will issue `v0.19.0-b19-closed-loop-verified` + ff-merge `b19-pipeline-verification` onto `main`): **B19 closed-loop coupled-pipeline verification work in progress** (essential gate before 17c.1 cluster phases per user-authorised 2026-05-15 ~19:30 UTC+2 directive "hopefully before we get to the cluster work and tests"). **Phase 0 ✅ DONE at commit `d9c90d5`** (2026-05-16 morning; ~3 h): SPINUP/FIRSTCALL hardcoding investigation OUTCOME (β) FIX LANDED at `lpjguess/modules/imogenoutput.cpp:341-401` (+54/-12 LOC: 3 substantive LOC corrupting hardcoded `bool SPINUP=true, FIRSTCALL=true` ofstream writes to read `IMOGENConfig::firsthistyear` + `iyend` runtime state dynamically via the existing `climatemodel.cpp:1181-1199 updateImogenControlData()` state machine + ~45-LOC inline-comment forensic rewrite + 5-LOC dprintf observability); **B19 sub-item (i) CLOSED** at this commit per user AskQuestion approval; full landing record in `notes/B19.md` §2.5. **Phase 1 INTERIM = B28 fix ✅ DONE at commit `4c83561`** (2026-05-16 afternoon; ~2 h): orchestrator-order bug fix in `intermediary_py/imogen_ghg_controller/run_all.py` (+18/-1 LOC; reordered `COMPONENT_B` to move `lpjg_combined_and_fair_processing.py` from position 4 to position 2; must run BEFORE `lpjg_historical_plotting.py` to populate `CombinedDCC_TgCH4_best` column the plotter requires; pre-existing in `version_A` confirmed); 2 NEW audit items filed (B29 schema-divergence + B30 in-`src/` plot writes); full forensic in `notes/B19.md` §3.4.1. **Phase 1 CLOSE ✅ DONE at commit `9c7417c`** (2026-05-16 evening; ~3 h): pure doc cascade (`notes/B19.md` +95/-10 + `notes/FOLLOWUPS.md` +10/-1 + 7 B30-evidence PNG reverts); ALL 4 reproducibility gates PASS byte-exact (R1 narrow 6/6 + R1 extended 67/67 + R2 4/4 + R3 10/10 pytest); 20 publication-grade PNGs generated as bonus; user-raised double-counting concern resolved NEGATIVE (architecture enforces mutually-exclusive natural-flux wiring at `runs/<SCEN>/imogen_intermediary.ins` layer per `COUPLED_MODEL_INVESTIGATION.md` §2.3 + §3.7); 3 NEW audit items filed (B31 launcher backbone auto-rewrite + B32 `docs/scientific_framework.md` §1.5 natural-flux mutual-exclusion invariant doc + B33 Option C POSIX-path robustness); full landing record in `notes/B19.md` §3.4.2. **This catch-up commit ✅ DONE at this commit** (2026-05-16 night; ~1 h): pure 3-surface doc cascade closing the under-cascade gap from the prior 3 B19 commits (Phase 0 + Phase 1 INTERIM + Phase 1 CLOSE each used a lighter 3-file cascade instead of the full 6-surface convention); surfaced by user check-in at 2026-05-16 ~22:42 UTC+2 after Phase 1 CLOSE 3-remote push; closes 3 of 4 missing surfaces (`CHANGELOG.md` + this `EXECUTION_PLAN.md` row update + `notes/TRUNK_R13078_BACKPORT_LEDGER.md`); the CHAT_HANDOFF sibling-artifact is deferred to next session boundary OR B19 Phase 5 close-out. **Discipline note for going-forward** (Phase 2 + Phase 3 + Phase 4 + Phase 5): each B19 sub-phase commit should match the full 6-surface cascade convention from its initial commit, not retroactively. **Backport classification**: MIXED — all already-landed B19 work + this catch-up is TRUNK-IRRELEVANT-by-novelty in entirety (`imogenoutput.cpp` is novel since step 8; `intermediary_py/` is novel since step 10; per-fork notes + plan + ledger); forward-look B33 sub-item (c) Fortran-side defensive runtime warning at `imogen/code/imogen_lpjg.f:565-566` (~5 LOC) IS TRUNK-RELEVANT pending its actual landing at B19 Phase 2. **NEXT-TASK CLUSTER (unchanged from 17c.0.8 dashboard)**: **B19 Phase 2** (engine state-machine prep + B31 + B33 landing; ~3-5 h) → **B19 Phase 3** (engine round-trip workstation smoke 4-cell × 2-year; ~1-2 h) → **B19 Phase 4** (closed-loop validation vs legacy A/B, no-gate first per Q2δ; ~2-6 h) → **B19 Phase 5** (6-surface doc cascade + B32 landing + tag `v0.19.0-b19-closed-loop-verified` + 3-remote push + ff-merge `b19-pipeline-verification` onto `main`; ~2-3 h) → **B20** (literature-comparison sanity check vs Tian et al. 2020 GCB + Saikawa et al. 2014 ACP + IPCC AR6 WG1 Ch. 5 + optionally Saunois et al. 2020 ESSD; ~1-2 d) → **17c.1 → 17c.4** cluster phases on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative) → step 17d (end-to-end validation across 4 combinations) → step 18 (docs harmonisation) → step 19 (CI/CD + Zenodo DOI + v1.0.0 tag). v1.0 % done estimate at end of session 5: **~72-74%** (up modestly from B19 Phase 0's ~71-73%). **Forecasting lesson reinforced (4th independent recurrence; rule #9 promotion now well-justified)**: Phase 1 surfaced B28+B29+B30+B31+B32+B33 (6 items) — meticulous from-scratch re-runs + user-driven scientific challenges routinely surface latent defects + architectural concerns. Rule #9 promotion recommended at B19 Phase 5 close-out. 3-surface catch-up cascade at this commit: `CHANGELOG.md` (NEW dated entry combining all 4 B19 commits; ~90 LOC) + this `EXECUTION_PLAN.md` row update (+~15 LOC; B19-status prepend) + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (NEW step-B19 entry covering all 3 substantive commits + this catch-up; ~80 LOC). Plus 1 deferred sibling-artifact: `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 9 (deferred to next session boundary OR B19 Phase 5 close-out). **PRIOR ENTRY: 17c.0.8 LANDED 2026-05-15 night session 4 continuation** (this commit; tagged `v0.17.8-step17c-prep-complete` post-merge; 3-remote-converged at `origin/main`/`kit/main`/`helmholtz/main`): **PREP phase OFFICIAL CLOSE-OUT — 11/11 sub-phases DONE; doc-cascade-only across 6 in-tree surfaces + 1 sibling-artifact (CHAT_HANDOFF Part 8); ZERO source-code change**. Pure-bookkeeping commit formally marking Step 17c.0 PREP phase OFFICIALLY COMPLETE. The 11-sub-phase arc (17c.0.0 → 17c.0.1 → 17c.0.2 → 17c.0.3 → 17c.0.4 → 17c.0.4-followup → 17c.0.5 → 17c.0.5-clarification → 17c.0.6 → 17c.0.7 → **17c.0.8** this commit) spanned 4 calendar days (2026-05-12 morning → 2026-05-15 night) across 4 chat sessions, closing 4 audit items (B15 + B16 + B17(a) + B17(b)) + 1 latent defect (Path α handshake-file write-path) + landing the deferred-from-C2 workstation `mpirun -np 4` mimic obligation per session-2 §17.7 + 18 LOC of TRUNK-RELEVANT N-cycle unit doc-comment clarifications. **Net `lpjguess/` source-level change in THIS commit: ZERO**. **Backport classification: TRUNK-IRRELEVANT-by-novelty** (the entire `notes/` + `CHANGELOG.md` + `EXECUTION_PLAN.md` doc surface doesn't exist in `trunk_r13078`); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` 17c.0.8 entry captures this with rationale. **NEXT-TASK CLUSTER (per user-authorised 2026-05-15 ~22:30 UTC+2)**: **B19** (essential ~2.5-4 d closed-loop pipeline verification of stages 2-7; revised estimate down from 3-7 d after code-reality check confirmed steps 10/11/12/13/14 are all already DONE per this `EXECUTION_PLAN.md`; only sub-items (c) IMOGEN engine round-trip + (e) closed-loop validation vs legacy A/B + recommended (i) SPINUP/FIRSTCALL hardcoding investigation are essential; rest is optional polish) → **B20** (recommended ~1-2 d literature-comparison sanity check vs published literature ranges) → **17c.1 → 17c.4** cluster phases on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative) → step 17d (end-to-end validation across 4 combinations) → step 18 (docs harmonisation) → step 19 (CI/CD + Zenodo DOI + v1.0.0 tag). Three deferred B19 questions for session-5 opening agenda (Q1 SPINUP/FIRSTCALL ordering + Q2 closed-loop validation tolerance vs legacy A + Q3 B19-Phase 1 ordering revisit) per `notes/STEP_17c.md` §1.7.10 + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 8 §8.6. v1.0 % done estimate at 17c.0.8 close-out: **~70-72%** (held from 17c.0.7; pure book-keeping with no fresh substantive milestone). **Forecasting lesson reinforced (rule #9 candidate)**: harness-authoring + targeted verification routinely surface latent defects in the system under test (B15 + B16 + B17(a) + B17(b) + Path α + the 18 LOC of unit doc-comment clarifications all surfaced this way during the 11-sub-phase PREP arc); promotion to formal rule #9 still deferred pending one more independent recurrence in B19 or 17c.1+. 6 in-tree + 1 sibling cascade: `notes/STEP_17c.md` (NEW §1.7 ~150 LOC + header + Status + table + Index updates) + `notes/FOLLOWUPS.md` (status dashboard refresh + B19/B20 PRIORITY: HIGH annotations + F-12 row update + footer NEXT-TASK CLUSTER summary) + `CHANGELOG.md` (NEW dated entry) + this `EXECUTION_PLAN.md` row update + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` (NEW 17c.0.8 entry) + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (NEW Part 8). **PRIOR ENTRY: 17c.0.7 LANDED 2026-05-15 evening session 4 continuation** (commit `6695ef2`; tagged `v0.17.7-step17c-mpi-4rank-mimic` post-merge; 3-remote-converged at `origin/main`/`kit/main`/`helmholtz/main`): **Workstation `mpirun -np 4` mimic verification of C2-core MPI machinery for all 3 coupling modes (loose, prescribed, tight) on a 4-cell × 11-yr smoke scenario via NEW dedicated harness `scripts/cross_validate_mpi_4rank.sh` (~+700 LOC including comprehensive doc block) + Path α handshake-file write-path defect fix at the xval harness layer (`DIR_COMMON` injection for non-loose modes; pre-fix the empty default caused `mkdir(/LPJG_main/IMOGEN/)` to fail permission-check at runtime affecting ALL prescribed/tight xval runs not just the mpirun mimic — production runs unaffected because they always import `imogen_intermediary.ins` which sets `DIR_COMMON`; full Path α forensic in NEW `notes/STEP_17c.md` §3.10) + 2 BUNDLED ADDITIONAL clarification edits (NEW 2026-05-15 ~21:00-21:40 UTC+2; user-driven source-code rigorous unit re-verification per user verbatim challenge to the inferred-by-sibling-pool conclusion + "I trust your conclusions"; full narrative in `notes/STEP_17c.md` §1.6.5): (i) `guess.h:3850` typo fix `/// soil NO mass in pool (kgN/m2)` → expanded multi-line doc-comment correctly labelling `N2O_mass`/`N2O_mass_w`/`N2O_mass_d` as `(kgN/m2; mass-of-N basis ...)`; +6/-1 LOC; TRUNK-RELEVANT (pure correction of an existing factual error in a doc-comment); (ii) NEW ~13 LOC inline-comment block at `commonoutput.cpp:1759-1767` documenting the `* M2_PER_HA` writer-side conversion → output unit `kgN/ha/yr` (NOT `kgN2O/ha/yr`; locks in the convention to prevent the half-remembered confusion the user described from his colleague); TRUNK-RELEVANT; + bonus cross-ref precision fix at `imogenoutput.cpp:75-83` (off-by-one fix + new ngases.out distinction NOTE); + NEW B20 follow-up captured for future literature-comparison sanity check (per user verbatim aside about wanting to verify N2O magnitudes against published scholarship once the rebuild has a solid v1.0; distinct from B19's intra-codebase legacy A/B comparison; recommended after B19 completes; ~1-2 d effort) + 5 LOC of TRUNK-RELEVANT unit doc-comment clarifications in `lpjguess/framework/guess.h` (N2O_FIRE + N2O_SOIL + 3 sibling N-cycle flux types: N2_FIRE, NH3_SOIL, NO_SOIL) + ~8 LOC of TRUNK-IRRELEVANT-by-novelty comment-clarity cleanup in `lpjguess/modules/imogenoutput.cpp:75-79` (N2O_PER_N constant)** for Step 17c.0 PREP sub-phase 17c.0.7. Fulfills the deferred-from-C2 obligation per session-2 §17.7. **Verification 8-gate-extended-to-11**: gates 1+2 rebuild PASS exit 0 (only `guess.h` + `imogenoutput.cpp` recompiled for doc-comment changes); gates 3+4 unit tests 162/162 PASS; gates 5-8 gridcell_outer-vs-year_outer xval regression check (4 scenarios) all PASS exit 0 with envelope IDENTICAL to 17c.0.6's `15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER` (B17(b) MECHANICAL CLOSURE preserved); **NEW gates 9-11 (loose + prescribed + tight MPI-4-rank mimic)** all PASS exit 0 with per-cell `.out` BIT_EXACT between single-process baseline + MPI-4-rank runs for ALL 3 coupling modes + handshake files BIT_EXACT (prescribed + tight, post-Path-α-fix) OR correctly ABSENT_BY_DESIGN (loose). First empirical confirmation that `MPI_Barrier(MPI_COMM_WORLD)` at year boundary + `MPI_Allreduce(MPI_SUM)` in `flush_year_globally_synchronized` produce bit-exact results between single-process and 4-rank execution paths for the workstation MPICH implementation. Deferred-from-C2 obligation per session-2 §17.7 is FULFILLED. **NEW B19 follow-up cross-linked to already-planned steps 11/13/19** (per `intermediary_py/README.md` scoping at step 10): 17c.0.7 verifies stages 1 + 8 of the 8-stage coupled pipeline (LPJG year_outer simulation + LPJG-side natural-emissions handshake-file writes); B19 verifies stages 2-7 (intermediary_py components A+B+C+D + step-13 adapter + IMOGEN Fortran engine round-trip + CO2.dat write with CH4 + N2O concentrations as columns); recommended timing per user-authorised 2026-05-15 ~19:30 UTC+2 ("hopefully before we get to the cluster work and tests"): before 17c.1 cluster phases begin. **Backport classification**: MIXED — TRUNK-IRRELEVANT-by-novelty for harness + `imogenoutput.cpp:75-79` cleanup; TRUNK-RELEVANT for `guess.h` N-cycle unit doc-comments (at Backport Sprint time post-step 19, apply same 5 LOC to `trunk_r13708`'s `framework/guess.h`); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17c-17c.0.7 entry captures this. 11 in-tree files + 1 sibling-artifact cascade: `scripts/cross_validate_mpi_4rank.sh` (NEW ~700 LOC) + `lpjguess/framework/guess.h` (+14/-10) + `lpjguess/modules/imogenoutput.cpp` (+9/-5) + `notes/STEP_17c.md` (+~280 LOC: NEW §1.6 + NEW §3.10 + header date row + §1 table row + Index updates) + `notes/FOLLOWUPS.md` (+~50 LOC: status dashboard refresh + NEW B19 follow-up) + this `EXECUTION_PLAN.md` row update + `CHANGELOG.md` NEW dated entry + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` NEW step-17c-17c.0.7 entry + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` NEW Part 7 (sibling). **Step 17c.0 PREP status post-this-commit**: 17c.0.0 + 17c.0.1 + 17c.0.2 + 17c.0.3 + 17c.0.4 + 17c.0.4-followup + 17c.0.5 + 17c.0.5-clarification + 17c.0.6 + **17c.0.7 ✅ DONE**; **17c.0.8 (PREP close-out; ~0.2 d) NEXT**. After 17c.0.8: B19 (recommended before 17c.1; ~3-7 d median ~5 d) then 17c.1 → 17c.4 cluster phases on KIT IMK-IFU `owl` (~1-2 weeks SSH-iterative). Total remaining 17c.0 PREP: **~0.2 d**. C3-era cluster phases ~1-2 weeks SSH-iterative thereafter — unchanged. v1.0 % done estimate revised UP to **~70-72%** (17c.0.7 closes the deferred-from-C2 obligation + Path α handshake-write-path defect; meaningful operational milestone). Full forensic + landing chain in `notes/STEP_17c.md` §1.6 (NEW; ~165 LOC) + NEW §3.10 (~120 LOC; Path α forensic). **PRIOR ENTRY: 17c.0.6 LANDED 2026-05-15 early morning session 4 continuation** (tagged `v0.17.6-step17c-b17b-closure` post-merge): **B17(b) MECHANICAL CLOSURE via 4-LOC surgical correction of the closed-form `spinup_year_idx` reproduction formula in `lpjguess/modules/imogen_input.cpp` + `lpjguess/modules/imogencfx.cpp` per new `notes/STEP_17c.md` §3.8.6 + C2 close-out tag (a)-refined annotation amendment BUNDLED in same commit/push event** for Step 17c.0 PREP sub-phase 17c.0.6. **Exercises the §3.8.5.5 5th cadence bullet PERMITTED-reactivation surface** introduced just hours earlier at 17c.0.5-clarification (commit `e03ceb1`) per the user's verbatim 2026-05-14 night directive _"I would prefer that we try to see if we can resolve the issue"_ + 2026-05-15 ~01:44 UTC+2 _"Your recommended path sounds good to me"_. Phase A code review high-confidence-identified the root cause: the formula `(cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP` derived in `notes/STEP_17a.md` §5.4 was based on a false assumption that `spinup_year_idx` persists across cells in gridcell_outer mode (the actual code at `imogen_input.cpp:880` + `imogencfx.cpp:1122` RESETS spinup_year_idx = 0 at start of every cell in getgridcell()); the spurious `cell_idx * nyear_spinup` term introduced a per-cell offset that gridcell_outer doesn't have, causing cell c (c >= 1) in year_outer to use spinup imogen_years shifted by c*nyear_spinup positions; cell 0 was bit-exact pre-fix because cell_idx=0 zeroes the spurious term — also the reason 1cell xval false-positive-PASSED through the entire 17c.0.1+ era. Phase B + Phase C instrumentation skipped as no longer needed; Phase D direct fix authoring + 8-gate verification CONFIRMS mechanical closure. **Verification gates 1-8 ALL PASS exit 0**: gates 1+2 build/+build_mpi/ rebuild PASS exit 0 (incremental, both .cpp recompiled, both binaries re-linked; only pre-existing Timer sprintf-overflow warnings (none from fix LOC)); gates 3+4 unit tests 162/162 / 25 cases both builds PASS; gates 5+6 1cell xval 37/37 raw BIT_EXACT exit 0 (regression-clean — predicted from cell_idx=0 zeroes spurious term); **gates 7+8 4cell xval `15 BIT_EXACT + 22 SORTED_EXACT + 0 SORTED_DIFFER + 0 NaN + banner_a=0 + banner_b=5` exit 0 IDENTICAL between LOOSE (gate 7) and TIGHT (gate 8) coupling — the 17 previously-SORTED_DIFFER per-PFT-total + tot_runoff files are now ALL SORTED_EXACT (data identical between modes after row-order normalization); the residual difference is pure B17(a) row-emission-order which is the documented harness-side normalization, NOT model-state divergence**. The post-fix gate 7+8 envelope IDENTICALITY between LOOSE and TIGHT coupling mechanically confirms the §3.8.3 "coupling-invariance of B17(b)" empirical observation arose from the IDENTICAL bug pattern existing in BOTH input modules' closed-form formula sites (4 sites total: 2 in each .cpp), and the IDENTICAL fix yields the IDENTICAL closure outcome. **B17(b) status changes from "RECLASSIFIED + PROVISIONALLY ACCEPTED at 2% tolerance per §3.8.5 + (α)/(β) reactivates on re-evaluation trigger OR PROACTIVE REVISIT (FORCED + PERMITTED reactivation surfaces per §3.8.5.5)" → "MECHANICALLY CLOSED at 17c.0.6 via the spinup_year_idx formula correction per `notes/STEP_17c.md` §3.8.6"; combined audit B17 = CLOSED at 17c.0.6**. The §3.8.5 provisional 2% tolerance is RETIRED-because-no-longer-applicable; the §3.8.5.5 FORCED + PERMITTED reactivation cadence is RETIRED-with-honour-of-PERMITTED-surface-FIRING-ONCE-SUCCESSFULLY (the 2026-05-14 night → 2026-05-15 early morning proactive revisit is the realisation of that surface and yielded this mechanical closure); the deferred-future-sub-phase-TBD slot for Option α/β is RETIRED-SUPERSEDED in the same operation (no longer needed since the underlying drift no longer exists). **C2 close-out tag (a)-refined annotation amendment LANDED in this commit**: `v0.17.5-step17b-c2-mpi-sync` annotation amended in place at `f6c192e` to reflect post-B15 + post-B17(a) + post-B17(b)-mechanical-closure verification status, preserving original annotation text within the new updated message for forensic completeness; SHA `f6c192e` preserved per (a) approach choice. **Forecasting lesson (candidate operational heuristic rule #9)**: when a forensic note (`notes/STEP_*.md`) contains a derivation that is materially relied upon by source-side code (e.g., closed-form state-machine reproduction formulas), an audit that re-checks the SOURCE CODE against the DERIVATION should be a standard step in any subsequent forensic deep-dive, NOT just a check of the source code against itself; trusted-input audits are independent-input audits. Per `notes/STEP_17c.md` §3.8.6.9 — promotion to formal rule #9 deferred pending recurrence. **Backport classification**: TRUNK-IRRELEVANT-by-novelty (the year_outer code path + the spinup_year_idx state-machine reproduction formula are step-17a additions; the entire year_outer code path doesn't exist in trunk_r13078); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17c-17c.0.6-b17b-closure entry captures this. 11 in-tree files + 1 sibling-artifact cascade: `lpjguess/modules/imogen_input.cpp` (+~150 LOC inline forensic + 4-LOC source change at 2 sites) + `lpjguess/modules/imogencfx.cpp` (symmetric + ~5-LOC update to existing C1.1-erratum comment) + `lpjguess/modules/imogen_input.h` (doc-block formula update + closure annotation) + `lpjguess/modules/imogencfx.h` (symmetric) + `notes/STEP_17c.md` (~+650 LOC: NEW §3.8.6 closure record + §3.8.5/§3.8.5.5 SUPERSEDED-BY-CLOSURE blocks + header date/status block update + §1 sub-phase table 17c.0.6 row + Index entry) + `notes/STEP_17a.md` (NEW §5.4 ERRATUM block at head of §5.4 marking the original derivation as superseded) + this `EXECUTION_PLAN.md` row update + `CHANGELOG.md` NEW dated entry + `notes/FOLLOWUPS.md` status dashboard refresh + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` NEW step-17c-17c.0.6-b17b-closure entry + `scripts/cross_validate_year_outer.sh` inline-comment updates (ZERO logic change; controlled-FAIL machinery preserved as regression detector) + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` NEW §6.1 (sibling). **Step 17c.0 PREP status post-this-commit**: 17c.0.0 + 17c.0.1 + 17c.0.2 + 17c.0.3 + 17c.0.4 + 17c.0.4-followup + 17c.0.5 + 17c.0.5-clarification + 17c.0.6 ✅ DONE; **17c.0.7 (workstation `mpirun -np 4` mimic; deferred-from-C2 obligation; ~1 d) NEXT**; 17c.0.8 (PREP close-out; ~0.2 d). Total remaining 17c.0 PREP: **~1.2 d** (down from ~1.4 d at 17c.0.5 — 0.2 d saved by retiring the deferred Option α/β sub-phase as no-longer-needed). C3-era cluster phases ~1-2 weeks SSH-iterative thereafter — unchanged. v1.0 % done estimate revised UP to **~67-70%** (B17(b) mechanical closure is a meaningful substantive milestone — moves the 4cell year_outer envelope from "controlled-FAIL within 2% tolerance" to "BIT-EXACT after row-order normalization"; strengthens foundation for C3-era cluster work). Full forensic + landing chain in `notes/STEP_17c.md` §3.8.6 (NEW; ~650 LOC; canonical closure narrative with 11 nested sub-sections including root-cause forensic, empirical-fingerprint mechanical-explanation table, latency analysis, fix description, 8-gate verification table, scope bounds, forecasting lesson, documentation surface, closure status). **PRIOR ENTRY: 17c.0.5-clarification LANDED 2026-05-14 early morning session 4 continuation** (commit `e03ceb1`; un-tagged checkpoint on top of `29ccc87`): doc-only 6-surface in-tree cascade broadening B17(b) reactivation surface from FORCED-only (§3.8.5 trigger firing) to FORCED + PERMITTED (proactive revisit at user discretion at any time per NEW §3.8.5.5 5th cadence bullet); ZERO source-logic change; ZERO behaviour change; pure-doc clarification. **PRIOR ENTRY: 17c.0.5 LANDED 2026-05-13 night-late session 4** (commit `29ccc87`; un-tagged checkpoint on top of `2771939`): **FULL 4-XVAL RE-VERIFY ON B15+B16+B17(a)+B17(b)-PROVISIONALLY-ACCEPTED HEAD (gates 1-8) per USER-AUTHORISED COLLAPSED RENUMBERING CONVENTION + harness stale-reference cleanup post-collapsed-renumbering convention adoption** for Step 17c.0 PREP sub-phase 17c.0.5. Per the user-authorised collapsed renumbering convention (per `notes/STEP_17c.md` §3.8.5 "Sub-phase renumbering implication" sub-section; user-authorised 2026-05-13 night-late session 4), 17c.0.5 = full 4-xval re-verify on `2771939` HEAD (gates 1-8) confirming regression-clean status with the §3.8.5 provisional B17(b) acceptance envelope intact — REPLACING the originally-planned 17c.0.5 (α/β decision) sub-phase. The deferred formal Option α (tolerance-based comparison upgrade to `compare_outputs()`) OR Option β (seed-tracking dprintf root-cause investigation per §3.8.4) reactivates as a future sub-phase TBD (identifier assigned at reactivation time) **either on a §3.8.5 re-evaluation trigger firing (FORCED reactivation) per the new §3.8.5.5 cadence (routine xval re-verify + C3-era cluster smoke + paper-stage analysis + ad-hoc on any §3.8.5 trigger) OR proactively at user discretion at any time even absent a trigger (PERMITTED reactivation) per §3.8.5.5 5th cadence bullet** (clarification commit on top of 17c.0.5 commit `29ccc87` per user's verbatim 2026-05-13 night directive _"we could come back and look at it and decide to do something about it"_). **Verification gates 1-8 ALL PASS (or controlled-PASS within §3.8.5 envelope)**: gates 1+2 (incremental rebuild of `lpjguess/build/` + `lpjguess/build_mpi/`) → NO-OP confirmed (binary sha256 + size + timestamp byte-identical pre/post; `build/guess` sha256 `8daa1339...`, `build_mpi/guess` sha256 `dd307488...`, both 2 974 248 B, both timestamped May 13 16:43/16:59 → no source change since `4d09b62` 17c.0.3 build epoch); gates 3+4 (unit tests both builds) → 25 cases / 162 assertions PASS each; gates 5+6 (1cell xval imogen + imogencfx) → exit 0 / 37/37 raw BIT_EXACT / 0/0 NaN / banner_a=0 / banner_b=5 (sort block skipped per idempotency); gates 7+8 (4cell xval imogen + imogencfx) → exit 2 (CONTROLLED-FAIL within §3.8.5 envelope) / **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER** classification IDENTICAL between LOOSE (gate 7) and TIGHT (gate 8) coupling — **stronger empirical confirmation than 17c.0.4 provided that B17(b) is coupling-invariant** (engine-side per-cell-iteration-order RNG slip per `notes/STEP_17c.md` §3.8.3, NOT input-module-specific). The 5 SORTED_EXACT files (PURE B17(a); identical to 17c.0.4 manifest): `mch4.out`, `mch4_diffusion.out`, `mch4_ebullition.out`, `mch4_plant.out`, `npool.out`. The 17 SORTED_DIFFER files (B17(a) + B17(b) drift; identical to 17c.0.4 manifest + drift-line counts): `aaet`, `agpp`, `anpp`, `cflux`, `clitter`, `cmass`, `cpool`, `cton_leaf`, `fpc`, `lai`, `nflux`, `ngases`, `nlitter`, `nmass`, `nsources`, `nuptake`, `tot_runoff`. **Opportunistic harness cleanup rolled in**: 4 surgical -1/+1-or-+2 stale-reference cleanups at `scripts/cross_validate_year_outer.sh` lines 305-306, 429, 484, 630-633 (post-collapsed-renumbering convention adoption rendered the prior "sub-phase 17c.0.5 (decision: tolerance-based comparison vs root-cause fix)" framing factually incorrect; +10/-5 LOC; ZERO behaviour change; bash syntax + smoke-retest verified — gate 7 still controlled-fails at exit 2 with new §3.8.5 message text appearing in FAIL output). Detailed before/after table in `notes/STEP_17c.md` §1.5.7. **NEW §3.8.5.5 RE-EVALUATION CADENCE LOCKED IN**: routine xval re-verify (every 4-xval re-verify run on this branch — establishes the canonical 17c.0.5 baseline envelope `15+5+17+exit 2` as the **expected** routine outcome; ANY deviation immediately fires §3.8.5 trigger 1 or 2) + C3-era cluster smoke runs (per re-eval trigger 3) + paper-stage analysis (per re-eval trigger 4) + ad-hoc on any §3.8.5 trigger firing outside routine cadence. Cadence canonicalised in `notes/STEP_17c.md` §3.8.5.5. **17c.0.4-followup decision narrative now formally documented** as new §1.4 of `notes/STEP_17c.md` (the 17c.0.4-followup commit `2771939` lacked a §1.x landing record because its substantive content was concentrated in §3.8.5; §1.4 added now as a thin landing-record pointer to §3.8.5 for the §1.x cadence). **Backport classification**: TRUNK-IRRELEVANT (verification + .sh-comment-only; no engine source change; `scripts/cross_validate_year_outer.sh` is per-fork harness; doesn't exist in `trunk_r13078`). 6-file source-level cascade (verification + .sh-comment-only): `scripts/cross_validate_year_outer.sh` (+10/-5 LOC stale-ref cleanup; the only source-touch this commit) + `notes/STEP_17c.md` (~+250 LOC: NEW §1.4 + §1.5 landing records + §1 sub-phase table updates marking 17c.0.4-followup ✅ + 17c.0.5 ✅ + §3.8.5 closing-paragraph supersession + §3.8.5 sub-phase renumbering lock-in + NEW §3.8.5.5 re-evaluation cadence sub-section + header date refresh + status block update + Index updates) + this `EXECUTION_PLAN.md` row update + `CHANGELOG.md` NEW dated entry + `notes/FOLLOWUPS.md` status dashboard refresh + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17c-17c.0.5 entry + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 5 NEW. **Step 17c.0 PREP status post-this-commit**: 17c.0.0 + 17c.0.1 + 17c.0.2 + 17c.0.3 + 17c.0.4 + 17c.0.4-followup + 17c.0.5 ✅ DONE; **17c.0.6 (C2 close-out tag annotation amendment decision per `notes/STEP_17c.md` §0.11; ~0.2 d) NEXT** (now ACTIONABLE since 17c.0.5 has confirmed underlying year_outer code at `f6c192e` substantively passes within §3.8.5 envelope); 17c.0.7 (workstation `mpirun -np 4` mimic; deferred-from-C2 obligation; ~1 d) → 17c.0.8 (PREP close-out; ~0.2 d). Total remaining 17c.0 PREP: **~1.4 d**. Deferred Option α/β closure for B17(b) is now an EXTRA-PREP sub-phase (identifier TBD) reactivated **either on §3.8.5.5 trigger firing (FORCED reactivation) OR proactively at user discretion at any time even absent a trigger (PERMITTED reactivation)** per user's verbatim 2026-05-13 night directive _"we could come back and look at it and decide to do something about it"_; clarification commit on top of 17c.0.5 commit `29ccc87` adds NEW §3.8.5.5 5th cadence bullet "Proactive revisit at user discretion" formalising the dual-surface reactivation policy. C3-era estimate still ~1-2 weeks SSH-iterative cluster work (17c.1 → 17c.4) on top of PREP. v1.0 % done estimate revised UP slightly to **~63-66%** (17c.0.5 establishes the canonical regression-clean baseline + §3.8.5.5 cadence; meaningful operational milestone — even though zero source-logic change, it locks in the operational envelope for all downstream sub-phases). Full forensic + landing chain in `notes/STEP_17c.md` §1.4 (NEW; ~75 LOC; 17c.0.4-followup landing record) + §1.5 (NEW; ~180 LOC; 17c.0.5 landing record) + §3.8.5 amendments + NEW §3.8.5.5 (~25 LOC). **PRIOR ENTRY: 17c.0.4-followup LANDED 2026-05-13 night session 4** (commit `2771939`; un-tagged checkpoint on top of `027d90d`): **B17(b) OPERATIONAL ACCEPTANCE AT PROVISIONAL 2% TOLERANCE + sub-phase renumbering decision deferral** for Step 17c.0 PREP sub-phase 17c.0.4 FOLLOW-UP. Doc-only commit (3 in-tree files: `notes/STEP_17c.md` NEW §3.8.5 sub-section + `notes/FOLLOWUPS.md` "Last updated" header refresh + B17 row status update + `scripts/cross_validate_year_outer.sh` ~30-LOC inline comment block in `compare_outputs()` near the SORTED_DIFFER classification — ZERO logic change) + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 4 (sibling artifact, outside repo). The user reviewed Phase A's empirically-clarified picture (per §1.3.3 + §3.8.1 through §3.8.4) and directed an operational reframing of the originally-planned 17c.0.5 (α/β decision) sub-phase: **provisionally accept B17(b) drift within a 2% cell-total tolerance envelope WITHOUT writing any new harness code OR engine instrumentation**, deferring the formal Option α (tolerance-based comparison upgrade) AND Option β (seed-tracking dprintf root-cause investigation) to a future sub-phase TBD that reactivates only on a §3.8.5 re-evaluation trigger firing. User verbatim directive (2026-05-13 night, session 4): _"Well I do not think we should implement anything in code for now, just simply documenting in the chat handoff that there is some divergence and we are accepting a 2% tolerance for now, but we may need to re-evaluate later. I suppose you could also include it as comment in the comparison code or something to that effect. It may be that we could come back and look at it and decide to do something about it."_ The decision was scoped explicitly as **provisional**: the 2% cell-total tolerance is the operating envelope until ANY of the four §3.8.5 re-evaluation triggers fires. Decision was landed as a **standalone commit** (not rolled into the next work commit) per the user's subsequent directive that the strategic significance warrants its own version-controlled history entry. Net source-logic change: **ZERO** (no `compare_outputs()` logic change; no exit-code change; no harness behaviour change). Net documentation change: ~170 in-tree LOC + ~250 sibling-artifact LOC. **Backport classification**: TRUNK-IRRELEVANT (doc-only + .sh-comment-only). 4 re-evaluation triggers per §3.8.5: (1) cell-total drifts exceed 2% on real-world gridlist or NCELLS scaling beyond 4-cell envelope; (2) per-PFT splits diverge in scientifically-consequential PFT/cell combinations beyond current empirical envelope; (3) C3-era cluster smoke runs reveal MPI-multi-rank-specific drift not captured by 4cell single-process xval; (4) paper-stage analysis surfaces a quantitative finding sensitive to per-PFT noise at 0.67-17.7% magnitude. Sub-phase renumbering convention TBD with user at start of next sub-phase: placeholder OR collapsed (subsequently RESOLVED in 17c.0.5 above: COLLAPSED CONVENTION ADOPTED + RE-EVAL CADENCE LOCKED IN). v1.0 % done estimate held at ~62-65% (this decision is doc-only; no fresh substantive milestone landed). Full forensic in `notes/STEP_17c.md` §3.8.5 (NEW; ~140 LOC) + canonical narrative in chat handoff §4.13. **PRIOR ENTRY: 17c.0.4 LANDED 2026-05-13 late-evening session 4** (commit `027d90d`; un-tagged checkpoint on top of `4d09b62`): **B17 FORENSIC DEEP-DIVE (PHASE A) + B17(a) ROW-EMISSION-ORDER DIVERGENCE FIX (.sh-only sort-then-diff harness upgrade) + B17(b) RECLASSIFIED FROM "~1 ULP NUMERICAL ROUNDOFF" TO "STOCHASTIC-PROCESS SENSITIVITY PER CELL-ITERATION-ORDER RNG SLIP"** for Step 17c.0 PREP sub-phase 17c.0.4. The B17 fix design from `notes/STEP_17c.md` §3.6 was approved by the user as **Option A: B17(a)-only narrow-scope landing in 17c.0.4 + defer B17(b) decision to 17c.0.5** after Phase A forensic deep-dive surfaced material findings revising §3.4 hypothesis space. **B17(a) FIX (option (a1) from §3.6)**: ~100-LOC SORT-THEN-DIFF NORMALIZATION block in `scripts/cross_validate_year_outer.sh::compare_outputs()` per `notes/STEP_17c.md` §1.3.4: 75-LOC documentation comment + conditional sort-then-diff block (mktemp+trap RETURN auto-cleanup; LC_ALL=C sort -k1,1n -k2,2n -k3,3n on (Lon, Lat, Year) preserving header line verbatim via head -1 + tail -n+2 | sort) + BIT_EXACT/SORTED_EXACT/SORTED_DIFFER classification + effective-pass semantic update (effective_pass = matches + sorted_exact; bit_exact_ok iff effective_pass == total) + refined PASS/FAIL messages with B17(b) drift count reporting. Block IDEMPOTENT (guarded by `if mismatches > 0`; skipped when raw cmp -s passes). Net code diff: **+103 / −3** across **1 source file** (`scripts/cross_validate_year_outer.sh`); ZERO C++ source change; ZERO `.ins` / `.cpp` / `.h` touch. **B17 forensic deep-dive (Phase A; pre-fix)**: per §1.3.3, materially revised §3.4 hypothesis space — **§3.4 hypothesis 1 (FP-summation roundoff): FALSIFIED** by drift magnitudes 0.67-17.7% relative (e.g., `lai.out` cell `(-57.75,-33.75)` yr 1876 TrIBE: 0.0192 vs 0.0158 = 17.7% relative; cell-total drift bounded ≤ 1.4% relative — six orders too large for ~1 ULP at value-magnitude 0.02); **§3.4 hypothesis 2 (global RNG state): FALSIFIED** by `randfrac(long& seed)` pure functional Park-Miller LCG architecture (per-cell-isolated `gridcell.seed`+`stand.seed`; both initialise to 12345678; no global RNG state); **§3.4 hypothesis 3 (per-cell init order): NOT YET CONFIRMED — surviving candidate** refined to "setup-phase-ordering interaction with stochastic dynamics" via STRONG empirical localizer "cell 0 BIT-EXACT in ALL 17 drift files; cells 1, 2, 3 progressively diverge with cell index; drift cumulative-over-time within cell (first-drift at year 1873-1876; spinup years 1871-1872 BIT-EXACT in ALL cells)". Specific code site requires seed-tracking dprintf instrumentation deferred to 17c.0.5 (β option). Full reclassified-B17(b) characterization in NEW `notes/STEP_17c.md` §3.8 (this commit). **Verification gates 1-8** (per `notes/STEP_17c.md` §1.3.5+§1.3.6): gates 1+2 SKIPPED (no C++ rebuild needed; .sh-only fix); gates 3+4 (unit tests both builds) → **162/162 PASS** (regression-clean); gates 5+6 (1cell xval imogen + imogencfx) → **PASS exit 0** (37/37 raw BIT_EXACT; sort block skipped per idempotency); gates 7+8 (4cell xval imogen + imogencfx) → **CONTROLLED-FAIL exit 2** with EXACTLY-PREDICTED **15 BIT_EXACT + 5 SORTED_EXACT + 17 SORTED_DIFFER** classification on BOTH .ins variants. The 5 SORTED_EXACT files (PURE B17(a); successfully normalized): `npool.out`, `mch4.out`, `mch4_diffusion.out`, `mch4_ebullition.out`, `mch4_plant.out`. The 17 SORTED_DIFFER files (B17(a) + B17(b) drift): `aaet`, `agpp`, `anpp`, `cflux`, `clitter`, `cmass`, `cpool`, `cton_leaf`, `fpc`, `lai`, `nflux`, `ngases`, `nlitter`, `nmass`, `nsources`, `nuptake`, `tot_runoff`. Effective-pass count for 4cell scenarios advanced from 15/37 (pre-17c.0.4) to **20/37** (post-17c.0.4; 33% improvement on the controlled-fail surface). **Backport classification**: TRUNK-IRRELEVANT-by-novelty (`scripts/cross_validate_year_outer.sh` is per-fork harness; doesn't exist in `trunk_r13078`); `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17c-17c.0.4 entry captures this. **No stash needed** this sub-phase: 17c.0.4 fix authored fresh from §3.6 option (a1) without recourse to any pre-existing WIP. 6-file source-level cascade: scripts/cross_validate_year_outer.sh (the substantive code change) + STEP_17c.md (NEW §1.3 landing record + §3.3+§3.4+§3.6 status updates + NEW §3.8 reclassified-B17(b) sub-section + header date/status updates) + this row update + CHANGELOG.md NEW dated entry + FOLLOWUPS.md status dashboard refresh + TRUNK_R13078_BACKPORT_LEDGER.md step-17c-17c.0.4 entry + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 4 NEW. **Step 17c.0 PREP status post-this-commit**: 17c.0.0 + 17c.0.1 + 17c.0.2 + 17c.0.3 + 17c.0.4 ✅ DONE; **17c.0.5 (B17(b) decision: α tolerance vs β root-cause; ~0.5-2 d) NEXT**. **17c.0.5 decision pending** (user's call when 17c.0.5 begins): **Option α (tolerance-based comparison upgrade; ~0.5-1 d; recommended)** = extend SORTED_DIFFER classification to per-row per-column abs+rel diff with `--tolerance abs=<eps_a>,rel=<eps_r>` thresholds reclassifying SORTED_DIFFER → SORTED_WITHIN_TOL (PASS) or SORTED_EXCEEDS_TOL (FAIL); aligns with Decision-12 acceptance criterion 2 ("PASS substantive within an explicit tolerance specified in `notes/STEP_17b.md` §3a.7"). **Option β (seed-tracking root-cause investigation; +1-2 d)** if α rejected = surgical seed-tracking dprintf at every `randfrac` consumer; diff seed-trace logs to identify FIRST cell + FIRST callsite where seeds diverge; targeted fix at that specific code site. Then 17c.0.6 (4-xval re-verify on B15+B16+B17-fixed HEAD; ~0.5 d) → 17c.0.7 (C2 close-out tag annotation amendment per `notes/STEP_17c.md` §0.11; ~0.2 d; renumbered from 17c.0.6) → 17c.0.8 (workstation `mpirun -np 4` mimic; deferred-from-C2 obligation; ~1 d; renumbered from 17c.0.7) → 17c.0.9 (PREP close-out; ~0.2 d; renumbered from 17c.0.8). Total remaining 17c.0 PREP: ~2.4-4 d. C3-era estimate still ~1-2 weeks SSH-iterative cluster work (17c.1 → 17c.4) on top of PREP. v1.0 % done estimate held at ~62-65% (this commit closes B17(a) mechanically + materially reclassifies B17(b) but doesn't unblock substantive 4cell year_outer until 17c.0.5 closes B17(b)). **Operational heuristics**: rule #8 (added in 17c.0.0; operationally validated in 17c.0.1; applied verbatim in 17c.0.2/3/4) remains canonical; **forecasting-refinement candidate for future rule #9** (initially identified in 17c.0.3 §3.7) is reinforced by 17c.0.4's experience (Phase A's empirical refutation of two of the three §3.4-forecast hypotheses validates the operational value of structured hypothesis enumeration over coarse two-bucket forecasts). Whether this becomes formal rule #9 will be decided after 17c.0.5 confirms B17(b) closure path. Full forensic + landing chain in `notes/STEP_17c.md` §1.3 (NEW; ~250 LOC) + §3.3+§3.4+§3.6 amendments + NEW §3.8 (~120 LOC). **PRIOR ENTRY: 17c.0.3 LANDED 2026-05-13 evening session 4** (commit `4d09b62`; un-tagged checkpoint on top of `019c9dd`): **B16 LATENT EAGER-CACHE-FULLNESS CHECK FIX (G1-G4)** for Step 17c.0 PREP sub-phase 17c.0.3, plus **B17 NEW AUDIT ITEM SURFACE forensic** (forensic surface only; B17 fix deferred to 17c.0.4 = this commit). The B16 fix design from `notes/STEP_17c.md` §0.9 (forecast) + §2.6 (G1-G4 design) was approved verbatim in session 4 with the user's authorisation to include G4 (the inner per-miss diagnostic tightening with `cell_idx`). **G1**: `lpjguess/modules/imogen_input.cpp:1111-1118` — DELETE 8-line eager check `if (last_store_index >= nyears) fail("...: stored_years cache already full ...")`; REPLACE with ~38-LOC doc block explaining (a) cumulative-across-cells cache design intent (per §2.4); (b) why eager check was wrong (mis-models cache as per-cell; per §2.5); (c) inner-fail still provides correct fail-fast semantics for genuine cache exhaustion; (d) cross-references to §0.9 + §2.4 + §2.5. **G2**: `lpjguess/modules/imogencfx.cpp:1366-1376` — symmetric DELETE 11-line eager check; REPLACE with ~20-LOC doc block (cross-references G1's full forensic in `imogen_input.cpp` rather than duplicating). **G3**: `lpjguess/framework/inputmodule.h:84-102` — AUGMENT existing `InputModule::preload_all_climate` virtual function doc block with ~20 LOC of "IMPLEMENTATION GUIDANCE FOR SUBCLASSES" formalising cumulative-across-cells cache contract: subclasses MUST treat any per-cell cache as cumulative-across-cells; subclasses MUST NOT add eager early-exit checks at function entry that assume per-cell cache state. **G4**: inner per-miss `fail()` messages at `imogen_input.cpp:1158-1164` + `imogencfx.cpp:1421-1427` — add `cell_idx` to both (~4 LOC each) for unambiguous fault attribution: distinguishes "cell 0 ran out of slots due to genuine cache-size misconfiguration" from "cell N>0 ran out of slots due to upstream bug shifting imogen_year sequence". **Strategy**: hybrid stash cherry-pick of `stash@{0}` (per `notes/STEP_17c.md` §0.12's "individual hunks" provision) for G1+G2 (cosmetic touch-ups: `§0.B16` → `§2 (audit item B16)` multiple occurrences, date `2026-05-12` → `2026-05-13`, `019c9dd` cross-reference); fresh authorship for G3 + G4 against §2.4 + §2.6 canonical citations. Net code diff: **+78 / −20** across 3 C++ files (`imogen_input.cpp`: +38/-9; `imogencfx.cpp`: +20/-11; `inputmodule.h`: +20/0). **Verification gates 1-4 (clean rebuilds + unit tests; all PASS)**: `lpjguess/build/` rebuild — ZERO new warnings (incremental: imogen_input.cpp.o + imogencfx.cpp.o + relink; inputmodule.h is included → triggers .cpp recompile); `lpjguess/build_mpi/` rebuild — ZERO new warnings touching G1-G4 sites (after one-time `MPICH_CXX=g++` recovery; the script's preferred `mpicxx` + Anaconda3 `conda-forge gxx_linux-64` path failed at link with system NetCDF/HDF5 ABI mismatches; recovery via option (a) of `scripts/cluster/make_guess.sh`'s documented compiler-selection options; full doc in `notes/STEP_17c.md` §1.2.10); `lpjguess/build/runtests --reporter compact` — 25 cases / 162 assertions PASS; `lpjguess/build_mpi/runtests --reporter compact` — 25 cases / 162 assertions PASS. **Verification gates 5-8 (four-xval re-verification — THE substantive 17c.0.3 evidence)**: 1cell scenarios PASS substantive + signal-of-life clean (gate 5: `1cell imogen` rc=0, 37/37 bit-exact, 0/37 NaN, banner_a=0/banner_b=5; gate 6: `1cell imogencfx` same metrics) — regression-clean baseline confirming G1-G4 introduce zero numerical regression. 4cell scenarios CONTROLLED-FAIL exit 2 surfacing **B17 (NEW audit item with two sub-defects)** (gate 7: `4cell imogen` rc=2, 15/37 bit-exact, 0/37 NaN, banner_a=0/banner_b=**5** — year_outer ran END-TO-END; the 3→5 banner-count delta vs 17c.0.2 is the unambiguous mechanical evidence B16 is fixed; 22/37 differ between Run A + Run B; gate 8: `4cell imogencfx` symmetric — same 22/37 mismatch pattern + same banner counts; confirms B17 is **systemic year_outer multi-cell defect, not input-mode-specific**). **B17 sub-defects fully characterised in this commit (full forensic in `notes/STEP_17c.md` §3)**: **B17(a)** = row-emission-order divergence (gridcell_outer emits cell-major: per-cell-then-year; year_outer emits year-major: per-year-then-cell); Decision-12 byte-equality structurally unachievable for any multi-cell xval scenario without harness sort-then-diff comparison upgrade or engine row-buffering; 5/22 differing files are pure ordering — `sort A | diff sort B` returns 0 (`npool.out`, 4× `mch4*.out`). **B17(b)** = small ~1 ULP numerical drift in 17 per-PFT-total / `tot_runoff` files (`lai`, `nmass`, `cflux`, `aaet`, `fpc`, `cpool`, `cmass`, `nuptake`, `nsources`, `ngases`, `cton_leaf`, `nlitter`, `clitter`, `anpp`, `tot_runoff`, `nflux`, `agpp`); per-LC summed files unaffected (15/15 bit-exact: `nflux_pasture`, `npool_cropland/natural/pasture`, `cflux_*`, `cpool_*`, `anpp_*`); most prominent in southern-hemisphere cell `(-57.75, -33.75)` (e.g., `nflux fix` -14.80 → -14.85; `tot_runoff` similarly). Both build-agnostic (serial AND single-process MPI exhibit identical pattern; binaries `lpjguess/build/guess` and `lpjguess/build_mpi/guess` differ at byte 913+ confirming distinct compilations). **Backport classification**: G1, G2, G3, G4 all **TRUNK-IRRELEVANT-by-novelty** (not by syntax/semantics): the `preload_all_climate` virtual function + cumulative-cache machinery + eager-check anti-pattern are per-fork additions introduced at C1.3 sub-step 7.3.2 (commit `d7f6c74`, 2026-05-10). `trunk_r13078`'s `InputModule` base class doesn't have this virtual function. `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17c-17c.0.3 entry captures this with rationale. 6-file source-level cascade (per the carry-forward rule: C++ source-level changes trigger full cascade): `notes/STEP_17c.md` §1.2 NEW landing record + §2 NEW B16 forensic + §3 NEW B17 forensic surface + index/header/§1-table/§4-renumbering refresh + `CHANGELOG.md` NEW dated entry + this `EXECUTION_PLAN.md` row update + `notes/FOLLOWUPS.md` status dashboard refresh + `notes/TRUNK_R13078_BACKPORT_LEDGER.md` step-17c-17c.0.3 entry + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 3 NEW. **Operational heuristics**: rule #8 (added in 17c.0.0; operationally validated in 17c.0.1) remains canonical — banner_b=5 in gates 7+8 is a textbook rule-#8 success even with the controlled-fail outcome (gates correctly distinguish "year_outer ran end-to-end with substantive output divergence vs gridcell_outer baseline" from "year_outer silently degenerated"). **Forecasting-refinement candidate for future rule #9** (per `notes/STEP_17c.md` §3.7): when staged-discovery defect chains are anticipated (B15 → B16 → ?), enumerate possible "?" sub-categories in initial forensic — §0.8(4)'s coarse two-bucket forecast ("deeper code-correctness OR explicit tolerance") would have been more operationally valuable as finer enumeration of row-ordering, summation-order roundoff, and global-RNG-state hypotheses; whether this becomes formal rule #9 will be decided after 17c.0.4 confirms B17(b) root cause. **Step 17c.0 PREP status post-this-commit**: 17c.0.0 + 17c.0.1 + 17c.0.2 + 17c.0.3 all ✅ DONE; **17c.0.4 (B17 forensic deep-dive + fix; combined B17(a)+(b) scope) NEXT** (~1-2 d; empirically triggered by gates 7+8; B17(a) resolution: harness sort-then-diff comparison upgrade in `compare_outputs()` (recommended; lower-cost) OR engine row-buffering for cell-major emission in year_outer mode (alternative; higher-cost; preserves Decision-12 byte-equality strictly); B17(b) resolution: bisect among hypotheses (1) FP summation order in per-PFT-total accumulators (most likely), (2) global RNG state advancement order, (3) per-cell intermediate state initialization order via NCELLS=1, 2, 3, 4 progressive comparison); 17c.0.5 (4-xval re-verify on B15+B16+B17-fixed HEAD; ~0.5 d; should pass cleanly OR pass with explicit tolerance per `notes/STEP_17b.md` §3a.7) → 17c.0.6 (C2 close-out tag annotation amendment per `notes/STEP_17c.md` §0.11; ~0.2 d; renumbered from 17c.0.5) → 17c.0.7 (workstation `mpirun -np 4` mimic; deferred-from-C2 obligation; ~1 d; renumbered from 17c.0.6) → 17c.0.8 (PREP close-out; ~0.2 d; renumbered from 17c.0.7). Total remaining 17c.0 PREP: ~2.5-4 d. C3-era estimate still ~1-2 weeks SSH-iterative cluster work (17c.1 → 17c.4) on top of PREP. v1.0 % done estimate held at ~62-65% (this commit closes B16 mechanically but doesn't unblock substantive 4cell year_outer until 17c.0.4 closes B17). **`stash@{0}` recommended disposition**: drop after this commit's 3-remote push converges (its B16 hunks have been consumed by G1+G2; the patch backup at `_chat_artifacts/B15_B16_WIP_PRE_FORENSIC_2026-05-12.patch` remains the canonical pre-fix snapshot). Forensic artefacts at `_chat_artifacts/forensic_clean_HEAD_xval_2026-05-12.log` + `forensic_clean_HEAD_run_{A,B}_run.log` preserved unchanged. Full forensic + landing chain in `notes/STEP_17c.md` §1.2 (NEW; ~115 LOC) + §2 (NEW; ~120 LOC) + §3 (NEW; ~110 LOC). **PRIOR ENTRY: 17c.0.1 + 17c.0.2 LANDED 2026-05-13 afternoon session 4** (commit `019c9dd`; un-tagged checkpoint on top of `2beff31`): **B15 FIX + SIGNAL-OF-LIFE ASSERTION + FOUR-XVAL RE-VERIFICATION** for Step 17c.0 PREP sub-phases 17c.0.1 + 17c.0.2 (bundled per `notes/STEP_17c.md` §1's plan). The B15 fix design from `notes/STEP_17c.md` §0.8 (F1-F5) was approved verbatim in session 4 with the user's authorisation to include F5 (the optional ~3-LOC C++ runtime diagnostic). **F1**: `runs/SSP1-2.6/main_xval_imogencfx.ins:176` Class-2→Class-1 syntax (`param "framework_loop_mode" (str "gridcell_outer")` → `framework_loop_mode "gridcell_outer"`) + 13-line in-place doc block. **F2**: `runs/SSP1-2.6/main_xval_loose.ins:182` symmetric change + shorter doc block referencing the parallel imogencfx comment. **F3**: `scripts/cross_validate_year_outer.sh:138` (the `write_wrapper_ins` here-doc) `param "framework_loop_mode" (str "$mode")` → `framework_loop_mode "$mode"` + 27-line top-of-template doc block citing the two-class plib mechanism walkthrough (`parameters.cpp:991 + 1506-1514 + 1858-1862` SET-block scope + `parameters.cpp:288` C++ initialiser + `framework.cpp:464` consumer; corollary that `outputdirectory` is also Class-1 declare_parameter-bound at `outputmodule.cpp:38`). **F4**: NEW signal-of-life banner-presence assertion in `compare_outputs()` per **rule #8**: greps both run.logs for `[year_outer]` banner emitted at `framework.cpp:502`; pass requires `banner_a == 0` AND `banner_b >= 1`; failure exits with new code **4** (non-overlapping with existing 0=PASS, 1=ZERO-out-files, 2=byte-mismatch, 3=NaN-substantive). Captures bash-`grep -c`-exit-rc gotcha with `[ -f file ]` guards + `(grep -c ... \|\| true)` defensive pattern. PASS message updated to mention banner counts. ~92 LOC additive (~62 LOC code + ~30 LOC doc). **F5**: NEW runtime diagnostic at `lpjguess/framework/framework.cpp:339-357` (immediately after `read_instruction_file()` at line 337) — `dprintf("[framework] framework_loop_mode = \"%s\" (after .ins parse)\n", (const char*)IMOGENConfig::framework_loop_mode);` + ~17-line doc block citing §0.6 (the third gap = no consumer-side observability) + §0.8(F5) + relationship to F4 (independent defense layers; F5 fires unconditionally and catches typo'd values like `"year_outter"` that F4's banner check cannot surface). **Strategy**: hybrid stash cherry-pick of `stash@{0}` (per `notes/STEP_17c.md` §0.12's "individual hunks" provision) for F1-F4 (saves ~1 h doc-writing time; preserves a non-trivial `bash`-`grep -c` defensive pattern); fresh authorship for F5 against §0.5 + §0.8(F5) canonical citations. Cosmetic anchor-text touch-up `§0.B15` → `§0 (audit item B15)` (6 occurrences across 3 files; the `§0.B15` literal was a non-existent anchor in `notes/STEP_17c.md`; preserves B15 association while pointing to the actual section anchor). The two C++ B16 stash hunks (`lpjguess/modules/imogen_input.cpp` +35/-9 + `lpjguess/modules/imogencfx.cpp` +29/-11) **NOT applied**; remain in `stash@{0}` as starting material for 17c.0.3. Net code diff: **+171 / −5** across 4 files. **Verification gates 1-4 (clean rebuilds + unit tests; all PASS)**: `lpjguess/build/` rebuild — ZERO new warnings (incremental: framework.cpp.o + relink); `lpjguess/build_mpi/` rebuild — ZERO new warnings (incremental: framework.cpp.o + imogen_input.cpp.o + imogencfx.cpp.o + relink; the latter two recompiled due to mtime cache, not behavioural); `lpjguess/build/runtests --reporter compact` — 25 cases / 162 assertions PASS; `lpjguess/build_mpi/runtests --reporter compact` — 25 cases / 162 assertions PASS. **Verification gates 5-8 (four-xval re-verification — THE substantive 17c.0.2 evidence)**: 1cell scenarios PASS substantive + signal-of-life clean (gate 5: `1cell imogen` rc=0, 37/37 bit-exact, 0/37 NaN, banner_a=0/banner_b=5, F5 echoes "gridcell_outer"/"year_outer"; gate 6: `1cell imogencfx` same metrics) — **the first time the year_outer code path has actually been exercised in any cross-validation since C1 close-out** (`v0.17.0-step17a-c1-year-outer-single-process` 2026-05-10). 4cell scenarios surface **B16 textbook-exactly per `notes/STEP_17c.md` §0.9** (gate 7: `4cell imogen` rc=99 with `"ImogenInput::preload_all_climate: stored_years cache already full (last_store_index=9 >= nyears=9) when preloading cell (-95.75,80.25)"`, banner_a=0/banner_b=3 — year_outer started + 3 setup banners then aborted at preload; gate 8: `4cell imogencfx` symmetric `IMOGENCFXInput::preload_all_climate` same fail at same cell; both modules; same numerics; same fault site `cell_idx=1`) — **positive empirical evidence** that B15 is genuinely fixed (year_outer reaches `preload_all_climate` for the first time across `cell_idx >= 1`) and that B16 surfaces exactly as predicted. This becomes the canonical input data point for 17c.0.3 (B16 forensic + fix). **Backport classification**: F1-F4 IRRELEVANT (per-fork cluster config + harness; not in `trunk_r13078`); F5 RELEVANT (`framework.cpp` exists in `trunk_r13078`; F5 dprintf + doc block can be copied verbatim at the analogous post-`read_instruction_file()` site). 6-file source-level cascade (per F5 RELEVANT classification): STEP_17c.md §1.1 (NEW landing record) + CHANGELOG.md (NEW 2026-05-13 entry) + EXECUTION_PLAN.md (this row update) + FOLLOWUPS.md status dashboard refresh + TRUNK_R13078_BACKPORT_LEDGER.md step-17c-17c.0.1 entry + `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` Part 2 (NEW). **Operational heuristics**: no new rules surface; rule #8 (added in 17c.0.0) is now operationally validated — F4 implements it verbatim and would have surfaced B15 immediately at C1 close-out had it existed then. **Step 17c.0 PREP status post-this-commit**: 17c.0.0 + 17c.0.1 + 17c.0.2 all ✅ DONE; **17c.0.3 (B16 forensic + fix) NEXT** (~0.5-1 d; empirically triggered by gates 7+8 above; remove eager `if (last_store_index >= nyears) fail(...)` check at function entry in both `(IMOGENCFX|Imogen)Input::preload_all_climate`; document cumulative-across-cells cache design intent inline + in `inputmodule.h`'s `preload_all_climate` doc block; B16 forensic write-up will land as new top-level §2 of `notes/STEP_17c.md`, renumbering cluster-phases skeleton to §3); 17c.0.4 (4-xval re-verify on B15+B16-fixed HEAD; ~0.5 d) → 17c.0.5 (C2 close-out tag annotation amendment decision per `notes/STEP_17c.md` §0.11; ~0.2 d) → 17c.0.6 (workstation `mpirun -np 4` mimic; ~1 d) → 17c.0.7 (PREP phase close-out; ~0.2 d). Total remaining 17c.0 PREP: ~2.5-3.5 d. C3-era estimate still ~1-2 weeks SSH-iterative cluster work (17c.1 → 17c.4) on top of PREP. v1.0 % done estimate held at ~62-65% (this commit lands the B15 fix but does not unblock substantive 4cell year_outer until 17c.0.3 closes B16; the substantive year_outer-actually-exercised milestone for 1cell cases is the meaningful step-forward). Forensic artefact `_chat_artifacts/forensic_clean_HEAD_xval_2026-05-12.log` + the two `forensic_clean_HEAD_run_*.log` artefacts + `B15_B16_WIP_PRE_FORENSIC_2026-05-12.patch` + `git stash@{0}` all preserved unchanged. Full forensic + landing chain in `notes/STEP_17c.md` §1.1 (NEW; ~190 LOC). **PRIOR ENTRY: 17c.0.0 LANDED 2026-05-12 afternoon-evening session 3** (commit `2beff31`; un-tagged checkpoint on top of `f6c192e`): **B15+B16 FORENSIC RECORD** for Step 17c.0 PREP first sub-phase — forensic-only; ZERO `lpjguess/` and `imogen/code/` source change. Comprehensive forensic write-up of two audit items surfaced during session-3 onboarding audit of the C2 close-out tag at `f6c192e`. **B15 (class-mismatch defect; xval harness false-positive root-caused)**: the `framework_loop_mode` parameter — declared via `declare_parameter("framework_loop_mode", &IMOGENConfig::framework_loop_mode, 20, ...)` at `lpjguess/modules/imogencfx.cpp:353` + `lpjguess/modules/imogen_input.cpp:214` (Class 1; bound to a C++ `xtring` variable; consumed via direct C++ variable read at `framework.cpp:464`) — was being set in the xval harness wrapper-writer (`scripts/cross_validate_year_outer.sh:138`) and the imported xval base ins (`runs/SSP1-2.6/main_xval_imogencfx.ins:176`) using **Class-2 syntax** (`param "framework_loop_mode" (str "$mode")`), which writes only to the global `Paramlist param[...]` dictionary via `CB_STRPARAM` → `param.addparam(...)` and **never touches** the C++ variable. Result: gate at `framework.cpp:464` always evaluated false; **all four C1+C2 xval scenarios silently ran in `gridcell_outer` mode in BOTH Run A and Run B**; the "PASS substantive 37/37 bit-exact + 0/37 NaN" reports at C2 close-out were false positives. Three independent evidence streams converge on the class-mismatch root cause: (1) empirical reproduction on clean HEAD `f6c192e` after stashing all WIP — Run A and Run B `run.log` sha256-byte-identical at `43c278b0…`; combined `.out` sha256 identical at `ab23ea80…`; zero `[year_outer]` banners in Run B; both runs show 11 `[F-10 caveat: per-gridcell-rolling]` flushes (the gridcell_outer signature); (2) `plib` parser source-level forensic walkthrough proving the two storage paths (`Paramlist param[...]` via `CB_STRPARAM` → `param.addparam` vs. `declare_parameter`-bound C++ vars via the `declareitem(name, &cppvar, ...)` registration loop in `parameters.cpp:995-1018`) are mechanically disjoint with zero cross-update; (3) canonical pattern from `version_A/`+`version_B/` reference setups — strict two-class convention (Class 1 takes bare-keyword syntax; Class 2 takes param-block syntax). **B16 (latent eager cache-fullness check; downstream of B15)**: `ImogenInput::preload_all_climate` + `IMOGENCFXInput::preload_all_climate` contain `if (last_store_index >= nyears) fail("...: stored_years cache already full ...")` at function entry; mis-models the `stored_years` cache as per-cell when the actual design intent is cumulative-across-cells. Latent since C1.3 sub-step 7.3.2 (commit `d7f6c74`, 2026-05-10); undetected because B15 silently prevented year_outer from ever executing. **Recommended B15 fix (DEFERRED to commit 17c.0.1; presented for user review)**: F1 (`runs/SSP1-2.6/main_xval_imogencfx.ins:176` Class-2→Class-1 syntax) + F2 (`runs/SSP1-2.6/main_xval_loose.ins:182` symmetric) + F3 (`scripts/cross_validate_year_outer.sh:138` wrapper-writer Class-2→Class-1) + F4 (signal-of-life banner-presence assertion in `compare_outputs()` per **rule #8**) + optional F5 (~3 LOC C++ runtime diagnostic). All forensic-only; ZERO source change in this commit. **NEW persistent operational heuristic rule #8** (signal-of-life banner-presence assertion for code-path-gated cross-validation) added to `notes/FOLLOWUPS.md` "Operational heuristics — lessons learned". **C2 close-out tag annotation amendment decision DEFERRED to 17c.0.5** (option (c) per `notes/STEP_17c.md` §0.11; decide AFTER B15 fix re-verification at `f6c192e`-equivalent reveals whether the underlying year_outer code at the tagged commit substantively works). **17c.0 PREP plan REVISED 5→8 sub-phases**: 17c.0.0 (this commit) → 17c.0.1 (B15 fix; NEXT; ~0.5-1 d) → 17c.0.2 (4-xval re-verify on B15-fixed HEAD; ~0.5 d) → 17c.0.3 (B16 forensic + fix; gated on 17c.0.2 surfacing the failure on 4cell; ~0.5-1 d) → 17c.0.4 (4-xval re-verify on B15+B16-fixed HEAD; ~0.5 d) → 17c.0.5 (C2 close-out tag annotation amendment decision; ~0.2 d) → 17c.0.6 (workstation `mpirun -np 4` mimic verification; deferred-from-C2 obligation; ~1 d) → 17c.0.7 (PREP phase close-out; ~0.2 d). **Total revised PREP estimate: ~3.5-5 d** (was ~0.5-1 d). C3-era estimate still ~1-2 weeks SSH-iterative cluster work (17c.1 → 17c.4) on top of PREP. v1.0 % done estimate held at ~62-65% (this commit is doc-only; substantive progress comes in 17c.0.1+). Backport-IRRELEVANT (forensic record only). Forensic artefacts preserved at `_chat_artifacts/forensic_clean_HEAD_xval_2026-05-12.log` + `forensic_clean_HEAD_run_{A,B}_run.log` + `B15_B16_WIP_PRE_FORENSIC_2026-05-12.patch` (16 881 B; sha256 `a5d6c5b0bb2d2a4bc55f1a6342f461bce177dd79abde93f55d749c9860b59271`; pre-forensic exploratory WIP, also preserved as `git stash@{0}`). Full forensic chain in `notes/STEP_17c.md` §0 (full B15 + B16 forensic + fix design + rule #8 + PREP plan; ~370 lines NEW). **PRIOR PLAN (preserved for context):** ⏳ **F-12 sub-milestone C3 — Cluster MPI year_outer + production verification.** Per Path A 2026-05-09. Iterative SSH session work with the user on KIT IMK-IFU `owl` cluster: (a) refine `scripts/cluster/env_owl.sh` placeholders against actual `module avail` output on owl; (b) cluster MPI build via `make_guess.sh --mpi` against module-loaded NetCDF/HDF5/openmpi (workstation Anaconda3 preference inverts on cluster per Decision #8); (c) small smoke run (4 ranks × 480-cell × 5-yr tight; verify `imogen_lpjg_flux.txt` globally-synchronized per-year rows match workstation MPI mimic for the same gridlist+seed); (d) production-scale smoke (16 ranks × ~4000-cell × 11-yr); (e) iterate on cluster-specific issues. Compare against `version_B/landsymm_imogen/SSP1_RCP26/` predecessor cluster setup as side-by-side reference (predecessor was set up but never ran end-to-end per `[CMI §1.1]`; F-10 was the architectural blocker). | `notes/STEP_17c.md` (NEW; this commit; ~370 lines comprehensive B15+B16 forensic + revised PREP plan + cluster-phase skeleton); `CHANGELOG.md` (NEW 17c.0.0 entry); `EXECUTION_PLAN.md` (this row update); `notes/FOLLOWUPS.md` (status dashboard refresh + NEW rule #8); `_chat_artifacts/CHAT_HANDOFF_2026-05-12_session3.md` (NEW Part 1). PLANNED for 17c.0.1+: `runs/SSP1-2.6/main_xval_imogencfx.ins` (~1 LOC F1 syntax change + ~10 LOC doc block); `runs/SSP1-2.6/main_xval_loose.ins` (~1 LOC F2 symmetric); `scripts/cross_validate_year_outer.sh` (~1 LOC F3 syntax + ~30 LOC F4 banner-presence assertion + ~50 LOC doc blocks); optional ~3 LOC F5 C++ runtime diagnostic in `lpjguess/framework/framework.cpp` or similar startup path. PLANNED for 17c.0.3 (B16 fix): `lpjguess/modules/imogen_input.cpp` + `lpjguess/modules/imogencfx.cpp` (eager-cache-check removal + cumulative-cache documentation). PLANNED for 17c.1+: `scripts/cluster/env_owl.sh` (refined module loads); `scripts/cluster/run_coupled.sbatch` (any cluster-specific tweaks surfaced); `notes/STEP_17c.md` (extended with cluster-phase records); BACKPORT_LEDGER step-17c row (when source-level cluster changes land); `docs/build.md` cluster section refinement. NET `lpjguess/` source-level change at C3 close-out: still ZERO if no cluster-side C++ fixes surface (cluster work is config + scripts; the code work was at C1 + C2; B16 fix at 17c.0.3 will be C++ source change). | (a) 17c.0.0 forensic record committed (this commit); (b) 17c.0.1 B15 fix landed + four-xval substantive re-verification PASS with `[year_outer]` banner in Run B run.log (rule #8 assertion green); (c) 17c.0.3 B16 fix landed (gated on 17c.0.2); (d) 17c.0.6 workstation `mpirun -np 4` mimic completes with 4 per-rank `runNN/` dirs producing aggregate `imogen_lpjg_flux.txt` matching single-process year_outer baseline; (e) cluster MPI build clean; (f) cluster small smoke completes with all 4 ranks producing per-rank output dirs + globally-synchronized handshake; (g) cluster `imogen_lpjg_flux.txt` matches workstation MPI mimic baseline (within tolerance); (h) cluster production-scale smoke completes within walltime; (i) `cflux.out`, `mch4.out`, `ngases.out` post-`append_files.sh`-concatenation contain non-zero data for all simulated years. Tag `v0.18.0-step17c-c3-cluster-tight`. | **~3.5-5 d for 17c.0 PREP** (revised UP from ~0.5-1 d at session-3 start due to B15+B16 surface) **+ ~1-2 weeks iterative SSH cluster work** for 17c.1 → 17c.4 (depends on user availability for cluster session-back-and-forth) |
| **17d** | **End-to-end validation across all 4 combinations** (formerly: step 17). Now actually runnable for all 4 (local/HPC × loose/tight) per F-12 sub-milestones C1+C2+C3. Validation against working paper §2.5 thresholds: CO2 RMSD ≤ 5 ppm vs NOAA GMD; CH4 RMSD ≤ 50 ppb vs NOAA/AGAGE; N2O RMSD ≤ 5 ppb vs NOAA. Run SSP1-2.6 + SSP2-4.5 as primary scenarios (per Decision #1 + working paper §2.5). Document results in `validation/v1_results.md`. | (validation scripts; possibly NEW `tools/validate_against_NOAA_AGAGE.py`) | All thresholds met for both SSPs; reference outputs cached for paper figures (Axis 1, 2, 3 per F-13). | ~2-3 days |
| **18** | Documentation harmonisation per `[CMI §12.6]`. Build the unified `docs/technical_manual.md` covering: scientific framework (per working paper), build instructions, run instructions (workstation + cluster, all 5 SSPs), output catalogue, known issues, validation procedure, troubleshooting. Retire OUTDATED docs into `archive/references/`. Update `paper/manuscript_draft.docx` to RCMIP backbone. | (consolidate) | One self-consistent technical manual; OUTDATED docs archived; paper draft updated; CHANGELOG.md captures the v1.0 changes. | 1-2 weeks |
| **19** | CI/CD pipeline. `.github/workflows/ci.yml` (or `.gitlab-ci.yml`) builds LPJ-GUESS + Fortran IMOGEN, builds Python venv, runs the 3 pytest tests + the units-integrity tests (§I.D.4), runs the smoke coupled-run test, confirms reference outputs match expected (md5 or pandas tolerance). | (new) | CI passes on every commit. | 2-3 days |
| **v1.0** | **Tag and release.** GitHub + KIT GitLab + Helmholtz GitLab. Submit paper to GMD. | (release) | v1.0 tagged; mirrors green; paper submitted. | 0.5 day |
| **20+ (post-v1.0)** | Phase 2 additions: C++ IMOGEN brought to parity (per §II.2.5); integrated LTS as switchable backend (per §II.11.3); other §12.7 stretch goals. | (per §II.2, §II.11) | Both backends switchable; cross-validation passes. | 2-4 weeks |

### V.2 Total effort to v1.0 (revised after 5 May 2026 decisions)

| Phase | Step(s) | Effort |
|---|---|---|
| Phase 0 (strategic decisions) | settled | 0 days remaining |
| Phase 1 (code-level baseline) | steps 1, 2, 3, 7, 10 | ~5-6 days |
| Phase 2 (missing components + LU strategy) | steps 8, 9, 9.5, 13 | ~4-6 days |
| Phase 3 (forcing data canonicalisation + climate-output enhancements) | steps 4, 5, 6, 9.5 | ~3 days |
| Phase 4 (Stage I documentation, no run) | step 15 | ~0.25 day (was 1-2 days) |
| Phase 5 (validation) | steps 14, 17 | ~3-4 days |
| Phase 6 (cluster integration) | step 16 | ~2 days setup + 1-3 days cluster wall-clock |
| Phase 7 (documentation harmonisation) | step 18 | ~1-2 weeks |
| Phase 8 (CI/CD) | step 19 | ~2-3 days |
| **Total** | | **~25-35 person-days** + **~3-4 days cluster wall-clock** |

This is roughly 5-10 days less than the earlier estimate, primarily
because Stage I has dropped from "1-2 day investigation + days of
cluster runs" to "0.25 day documentation only" (Decision #9), and the
HPC-environment + cluster-scripts uncertainties are resolved
(Decisions #3 + Part III #2-#5).

Calendar-time estimate at 3-4 productive days/week: **~7-10 weeks
to v1.0**.

### V.3 What can run in parallel

Several steps are independent and can be done by separate engineers
or in parallel:

- Steps 0-1 (repo init + LPJ-GUESS import) and steps 4 (patterns) +
  10 (Python Intermediary) + 11 (Python inputs) are independent of
  each other.
- Steps 2-3 (Fortran IMOGEN + ALLOCATABLE) and step 5 (CMIP6
  conversion) are independent.
- Steps 7 (LPJG fixes) and 8 (handshake writer) require steps 1-3
  but are independent of steps 4-6.
- Step 13 (adapter) requires steps 10+ but not 1-9.

So with 2 engineers, total calendar time can probably halve to
~6 weeks.

### V.4 What must be sequential

The critical-path dependency chain (revised to include step 9.5):

```
0 → 1 → 2 → 3 → 7 → 8 → 9 → 9.5 → 13 → 14 → 16 → 17 → 18 → 19 → v1.0
                                  ↑
                                 10 (parallel branch from step 0)
                                  ↑
                                 11
                                  ↑
                                 12
                                                    ↑
                                                   15 (deferred → 0.25 day documentation only)
```

i.e. roughly 13 sequential steps on the critical path, which is the
~25-35 day total.

### V.5 Re-investigation triggers

If any step fails its verification milestone, the recovery protocol
is:

1. **Capture the failure state** in `notes/STEP_<n>_failure.md` —
   what was expected, what happened, what `git diff` shows vs the
   prior verified state.
2. **Re-investigate the relevant subagent report** in
   `_phase2_findings/`. The eight reports collectively cover every
   subsystem at depth; the bug or gap may already be documented
   there.
3. **Spawn a focused investigation** of the specific area (e.g. via
   another subagent or a manual deep-read).
4. **Update `EXECUTION_PLAN.md`** with the new finding before
   retrying the step.
5. **Roll back the working-tree state** to the prior verified
   commit; retry the step with the new understanding.

This is the value of the rebuild approach: each step is small enough
that a verification failure is bounded and recoverable.

---

## Appendix A — Implementation sketches

### A.1 LPJG-side handshake writer (sketch)

A new module `modules/imogenoutput.cpp/h` registered with the LPJ-GUESS
output framework. ~150 LOC. Pseudocode:

```cpp
// modules/imogenoutput.h
#ifndef LPJ_GUESS_IMOGEN_OUTPUT_H
#define LPJ_GUESS_IMOGEN_OUTPUT_H

#include "outputmodule.h"

class ImogenOutput : public OutputModule {
public:
    void init();
    void outannual(Gridcell& gridcell);   // accumulate per gridcell
    void outglobal_year(int calendar_year); // write per year (NEW HOOK)

private:
    // Year-running accumulators
    double accum_NEE_kgC;          // kg C / yr (positive = source to atmosphere)
    double accum_CH4_kgCH4;        // kg CH4 / yr
    double accum_N2O_kgN2O;        // kg N2O / yr
    double accum_area_m2;
    int    accum_year;
    bool   first_call;
};
#endif
```

```cpp
// modules/imogenoutput.cpp
#include "imogenoutput.h"
#include "framework.h"
#include "parameters.h"
#include <fstream>
#include <iomanip>

REGISTER_OUTPUT_MODULE("imogenoutput", ImogenOutput)

void ImogenOutput::init() {
    accum_year = -1;
    accum_NEE_kgC = 0;
    accum_CH4_kgCH4 = 0;
    accum_N2O_kgN2O = 0;
    accum_area_m2 = 0;
    first_call = true;
}

void ImogenOutput::outannual(Gridcell& gridcell) {
    // Called once per gridcell per year by framework.
    // Per the corrected NEE-NBP formula:
    //   NEE_per_m2 = flux_veg - flux_repr + flux_soil + flux_fire     (kg C / m2 / yr)
    // Get from gridcell's accumulated annual fluxes.
    const double nee_kgCm2 = gridcell.balance.aflux_veg
                            - gridcell.balance.aflux_repr
                            + gridcell.balance.aflux_soil
                            + gridcell.balance.aflux_fire;

    const double area_m2 = gridcell.area_m2();   // standard LPJ-GUESS gridcell area helper

    accum_NEE_kgC   += nee_kgCm2 * area_m2;
    accum_area_m2   += area_m2;

    // CH4 from mch4.out columns (12 monthly, g CH4 / m2 / month)
    double ch4_kgCH4_yr_m2 = 0;
    for (int m = 0; m < 12; m++) ch4_kgCH4_yr_m2 += gridcell.mch4[m] * 1e-3;
    accum_CH4_kgCH4 += ch4_kgCH4_yr_m2 * area_m2;

    // N2O from N2O_soil + N2O_fire (kg N / ha / yr); convert to kg N2O / m2 / yr
    const double n_kgNm2 = (gridcell.aflux_n2o_soil + gridcell.aflux_n2o_fire) * 1e-4;  // ha → m²
    const double n2o_kgN2O_m2 = n_kgNm2 * 44.0/28.0;
    accum_N2O_kgN2O += n2o_kgN2O_m2 * area_m2;
}

void ImogenOutput::outglobal_year(int calendar_year) {
    if (!IMOGENConfig::tight_coupling) return;

    const std::string dir = std::string((char*)IMOGENConfig::DIR_COMMON)
                          + "/LPJG_main/IMOGEN/";

    // Convert global accumulators to required units
    const double NEE_PgC      = accum_NEE_kgC   * 1e-12;
    const double CH4_TgCH4    = accum_CH4_kgCH4 * 1e-9;
    const double N2O_TgN2O    = accum_N2O_kgN2O * 1e-9;

    // 1. Append flux to imogen_lpjg_flux.txt
    {
        const auto mode = first_call ? std::ios::trunc : std::ios::app;
        std::ofstream f(dir + "imogen_lpjg_flux.txt", mode);
        f << calendar_year << "\t"
          << std::fixed << std::setprecision(6) << NEE_PgC << "\n";
    }

    // 2. Append CH4/N2O to imogen_lpjg_ch4_n2o_flux.txt
    {
        const auto mode = first_call ? std::ios::trunc : std::ios::app;
        std::ofstream f(dir + "imogen_lpjg_ch4_n2o_flux.txt", mode);
        f << calendar_year << "\t"
          << std::fixed << std::setprecision(6) << CH4_TgCH4 << "\t"
          << N2O_TgN2O << "\n";
    }

    // 3. Re-write imogen_lpjg.txt for the next call
    {
        std::ofstream f(dir + "imogen_lpjg.txt", std::ios::trunc);
        const int next = calendar_year + 1;
        const bool done_all = (next > IMOGENConfig::lasthistyear);
        const bool spinup = (next < IMOGENConfig::firsthistyear);
        f << "YEAR1 "      << next << " !IN First year\n";
        f << "IYEND "      << next << " !IN Stop year\n";
        f << "YEAR1_LPJG " << IMOGENConfig::firsthistyear << " !IN LPJG start\n";
        f << "SPINUP "      << (spinup   ? "TRUE" : "FALSE") << "\n";
        f << "KEEPRUNNING " << (done_all ? "FALSE" : "TRUE") << "\n";
        f << "FIRSTCALL "  << (first_call ? "TRUE" : "FALSE") << "\n";
    }

    // 4. Touch done file (last so engine doesn't see partial data)
    {
        std::ofstream f(dir + "done");
        f << "Climate files written\n";  // Consistent with what IMOGEN writes
    }

    // Reset accumulators
    accum_NEE_kgC   = 0;
    accum_CH4_kgCH4 = 0;
    accum_N2O_kgN2O = 0;
    accum_area_m2   = 0;
    first_call      = false;
}
```

Open question: where in the LPJ-GUESS framework does
`outglobal_year` get called from? The standard `OutputModule`
interface (`outputmodule.h`) has `outannual` (per gridcell) and
`outdaily` (per gridcell per day). A new "post-gridcell-loop, per-year"
hook may need to be added — or the writer can hijack the last
gridcell's `outannual` call (using `gridlist.last() == gridcell`).
The user's framework knowledge would clarify the cleanest approach.

### A.2 Python Intermediary → LPJG-format adapter (sketch)

```python
#!/usr/bin/env python3
"""
tools/imogen_inputs_to_lpjg_format.py

Convert the Python Intermediary's wide-format CSV into the four
narrow files the Fortran IMOGEN expects.

Usage:
    python tools/imogen_inputs_to_lpjg_format.py \
        --input outputs/imogen_inputs/imogen_inputs_SSP2-4.5.csv \
        --output runs/SSP2-4.5/inputs/

The output directory will contain four files:
    imogen_lpjg_flux.txt              (year, CO2_PgC_per_yr)
    imogen_lpjg_ch4_n2o_flux.txt      (year, CH4_Tg, N2O_Tg)
    co2_anthro_emissions.txt          (year, CO2_PgC_per_yr — for FILE_SCEN_EMITS)
    ch4_n2o_anthro_emissions.txt      (year, CH4_Tg, N2O_Tg — for FILE_CH4_N2O_EMITS)
"""

import argparse
import pandas as pd
import sys
from pathlib import Path

# --- conversion constants --------------------------------------------------
PgC_to_MtCO2 = 44/12 * 1000   # = 3666.6667
MtCO2_to_PgC = 1.0 / PgC_to_MtCO2

# --- main -----------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    expected_cols = {"Year", "CH4_anthro_Mt", "CH4_natural_Mt", "CH4_total_Mt",
                     "N2O_anthro_Mt", "N2O_natural_Mt", "N2O_total_Mt",
                     "CO2_EFOS_Mt", "CO2_NEE_Mt", "CO2_total_Mt"}
    missing = expected_cols - set(df.columns)
    if missing:
        sys.exit(f"Input CSV missing columns: {missing}")

    args.output.mkdir(parents=True, exist_ok=True)

    # 1. FILE_LPJG_FLUX: year, NEE in PgC/yr
    nee_pgc = df["CO2_NEE_Mt"] * MtCO2_to_PgC
    out1 = args.output / "imogen_lpjg_flux.txt"
    with open(out1, "w") as f:
        for y, v in zip(df["Year"], nee_pgc):
            f.write(f"{int(y)}\t{v:.6f}\n")

    # 2. FILE_LPJG_CH4_N2O_FLUX: year, CH4_natural_Tg, N2O_natural_Tg
    out2 = args.output / "imogen_lpjg_ch4_n2o_flux.txt"
    with open(out2, "w") as f:
        for y, ch4, n2o in zip(df["Year"], df["CH4_natural_Mt"], df["N2O_natural_Mt"]):
            f.write(f"{int(y)}\t{ch4:.6f}\t{n2o:.6f}\n")

    # 3. FILE_SCEN_EMITS: year, CO2_anthro in PgC/yr (= EFOS only)
    efos_pgc = df["CO2_EFOS_Mt"] * MtCO2_to_PgC
    out3 = args.output / "co2_anthro_emissions.txt"
    with open(out3, "w") as f:
        for y, v in zip(df["Year"], efos_pgc):
            f.write(f"{int(y)}\t{v:.6f}\n")

    # 4. FILE_CH4_N2O_EMITS: year, CH4_anthro_Tg, N2O_anthro_Tg
    out4 = args.output / "ch4_n2o_anthro_emissions.txt"
    with open(out4, "w") as f:
        for y, ch4, n2o in zip(df["Year"], df["CH4_anthro_Mt"], df["N2O_anthro_Mt"]):
            f.write(f"{int(y)}\t{ch4:.6f}\t{n2o:.6f}\n")

    print(f"Wrote 4 IMOGEN-format files to {args.output}")
    print(f"  {out1}: {len(df)} rows, NEE PgC/yr")
    print(f"  {out2}: {len(df)} rows, CH4/N2O Tg/yr")
    print(f"  {out3}: {len(df)} rows, EFOS PgC/yr")
    print(f"  {out4}: {len(df)} rows, anthro CH4/N2O Tg/yr")

if __name__ == "__main__":
    main()
```

The corresponding update to `imogen_intermediary.ins`:
```
FILE_LPJG_FLUX           "imogen_lpjg_flux.txt"
FILE_LPJG_CH4_N2O_FLUX   "imogen_lpjg_ch4_n2o_flux.txt"
FILE_SCEN_EMITS          "co2_anthro_emissions.txt"
FILE_CH4_N2O_EMITS       "ch4_n2o_anthro_emissions.txt"
```

(All relative to `<DIR_COMMON>/LPJG_main/IMOGEN/`. Both flux files
become *seeds* that LPJG then appends to; the engine reads them at
the start of each year-loop iteration.)

### A.3 CMIP6 NetCDF → CMIP5 ASCII converter (sketch)

```python
#!/usr/bin/env python3
"""
tools/cmip6_nc_to_cmip5_ascii.py

Convert IMOGEN CMIP6 NetCDF patterns into CMIP5-style ASCII directories
that the Fortran IMOGEN reader can consume directly.

Usage:
    python tools/cmip6_nc_to_cmip5_ascii.py \
        --nc Common-directory/IMOGEN-codebase/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/mri-esm2-0_patterns.nc \
        --json Common-directory/IMOGEN-codebase/patterns/CMIP6_IMOGEN_EBM_values_and_patterns/mri-esm2-0_params.json \
        --gridlist Common-directory/IMOGEN-codebase/code/patterns_gridlist.txt \
        --output Common-directory/IMOGEN-codebase/patterns/CEN_CMIP6_MOD_MRI-ESM2-0/
"""
import argparse, json, sys
import numpy as np
import xarray as xr
from pathlib import Path
from scipy.interpolate import RegularGridInterpolator

MONTH_NAMES = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]

# CMIP5-ASCII column order (per imogen_lpjg.f::GCM_ANLG line 3226-3231 read):
#    T, RH15M, U-wind, V-wind, LW, SW, DTEMP_day, rainfall, snowfall, P*
# Plus 2 reserved columns observed-zero in IPSL-CM5A-MR sample.
# Total 12 columns.
CMIP6_TO_CMIP5_COLUMN_MAP = [
    "tl1_patt",         # col 1: T
    "ql1_patt",         # col 2: RH15M (specific humidity → relative humidity? need to confirm)
    None,               # col 3: U-wind (CMIP6 has only wind speed magnitude in wind_patt, not vector)
    None,               # col 4: V-wind (same)
    "lwdown_patt",      # col 5: LW
    "swdown_patt",      # col 6: SW
    "range_tl1_patt",   # col 7: DTEMP_day
    "precip_patt",      # col 8: rainfall (combined in CMIP6)
    None,               # col 9: snowfall (CMIP6 has only total precip)
    "pstar_patt",       # col 10: P*
    None,               # col 11: reserved
    None,               # col 12: reserved
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nc",       required=True, type=Path)
    parser.add_argument("--json",     required=True, type=Path)
    parser.add_argument("--gridlist", required=True, type=Path)
    parser.add_argument("--output",   required=True, type=Path)
    args = parser.parse_args()

    # 1. Read NetCDF
    ds = xr.open_dataset(args.nc)
    # ds has dims (imogen_drive=12, lat=56, lon=96)
    src_lon = ds.lon.values   # 0..360 ascending
    src_lat = ds.lat.values   # -90..90 ascending or descending — confirm

    # 2. Read target IMOGEN HadCM3 land gridlist (1631 cells)
    target = []
    with open(args.gridlist) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                tlon, tlat = float(parts[0]), float(parts[1])
                if tlon < 0: tlon += 360   # normalise to 0..360 if needed
                target.append((tlon, tlat))
    target = np.array(target)
    assert len(target) == 1631, f"Expected 1631 cells, got {len(target)}"

    # 3. Read JSON params
    with open(args.json) as f:
        params = json.load(f)
    # params is {model_name: {kappa_o, lambda_l, lambda_o, mu, f_ocean}}

    # 4. Per-month: bilinear interpolate each of 8 _patt vars onto target grid
    args.output.mkdir(parents=True, exist_ok=True)
    for m_idx, mname in enumerate(MONTH_NAMES):
        rows = []
        # Header: bbox of source grid
        lon_min, lon_max = float(src_lon.min()), float(src_lon.max())
        lat_min, lat_max = float(src_lat.min()), float(src_lat.max())
        rows.append(f"{lon_min:8.2f}{lat_min:8.2f}{lon_max:8.2f}{lat_max:8.2f}")

        # Build interpolators for each variable (12 columns)
        interps = []
        for col_var in CMIP6_TO_CMIP5_COLUMN_MAP:
            if col_var is None:
                interps.append(None)   # zero column
            else:
                arr = ds[col_var].isel(imogen_drive=m_idx).values
                # arr shape (lat, lon); RegularGridInterpolator wants (lat, lon)
                interps.append(RegularGridInterpolator(
                    (src_lat, src_lon), arr,
                    method="linear", bounds_error=False, fill_value=0.0))

        # Interpolate per target cell
        for tlon, tlat in target:
            row = [f"{tlon:7.2f}", f"{tlat:7.2f}"]
            for ip in interps:
                if ip is None:
                    row.append("0.0000")
                else:
                    v = float(ip([[tlat, tlon]]))
                    row.append(f"{v:9.5f}")
            rows.append("  ".join(row))

        # Write
        outfile = args.output / mname
        with open(outfile, "w") as fout:
            fout.write("\n".join(rows) + "\n")
        print(f"Wrote {outfile} ({len(target)+1} lines)")

    # 5. Write Fortran namelist for EBM scalars
    model_name = list(params.keys())[0]
    p = params[model_name]
    nl = args.output.parent.parent / f"{model_name}_ebm.nml"
    with open(nl, "w") as fout:
        fout.write(f"&IMOGEN_EBM\n")
        fout.write(f"  KAPPA_O  = {p['kappa_o']:.6f}\n")
        fout.write(f"  LAMBDA_L = {p['lambda_l']:.6f}\n")
        fout.write(f"  LAMBDA_O = {p['lambda_o']:.6f}\n")
        fout.write(f"  MU       = {p['mu']:.6f}\n")
        fout.write(f"  F_OCEAN  = {p['f_ocean']:.6f}\n")
        fout.write(f"/\n")
    print(f"Wrote {nl}")

if __name__ == "__main__":
    main()
```

Caveats:
- The CMIP6 → CMIP5 column mapping above has open questions (U/V wind
  vector not directly available; specific vs relative humidity may
  need a unit conversion). To be settled with the author of the
  CMIP6 NetCDF (likely PRIME / Mathison 2025).
- The `imogen_drive` axis convention (Jan..Dec or Dec..Jan?) needs to
  be confirmed against the upstream pattern-generation code.

### A.4 Coupled-run launcher (sketch)

```bash
#!/bin/bash
# scripts/run_coupled.sh  —  workstation Linux launcher
# Usage:
#   ./scripts/run_coupled.sh <SCENARIO> [<GRIDLIST>]
# Examples:
#   ./scripts/run_coupled.sh SSP1-2.6
#   ./scripts/run_coupled.sh SSP2-4.5 gridlist_test480.txt
set -euo pipefail

SCENARIO=${1:-SSP1-2.6}
GRIDLIST=${2:-gridlist_in_62892_and_climate.txt}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${ROOT}/runs/${SCENARIO}"
LOG_DIR="${ROOT}/logs"
SCRATCH="${RUN_DIR}/scratch"
mkdir -p "${LOG_DIR}" "${SCRATCH}/IMOGEN" "${SCRATCH}/LPJG_main/IMOGEN"

echo "[$(date '+%F %T')] Starting coupled run: SCENARIO=${SCENARIO}, GRIDLIST=${GRIDLIST}"

# === Step 1: build LPJ-GUESS if needed ===
if [ ! -x "${ROOT}/lpjguess/build_imogen/guess" ]; then
  echo "[$(date '+%F %T')] Building LPJ-GUESS"
  cd "${ROOT}/lpjguess/build_imogen"
  cmake .. > "${LOG_DIR}/cmake.log"
  make -j$(nproc) > "${LOG_DIR}/make.log"
fi

# === Step 2: ensure Python Intermediary venv ===
if [ ! -d "${ROOT}/intermediary_py/.venv" ]; then
  echo "[$(date '+%F %T')] Creating Python venv"
  cd "${ROOT}/intermediary_py"
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt openpyxl
fi

# === Step 3: run Python Intermediary if outputs missing ===
PY_OUT="${ROOT}/intermediary_py/outputs/imogen_inputs/imogen_inputs_${SCENARIO}.csv"
if [ ! -f "${PY_OUT}" ]; then
  echo "[$(date '+%F %T')] Running Python Intermediary"
  cd "${ROOT}/intermediary_py"
  .venv/bin/python run_all.py 2>&1 | tee "${LOG_DIR}/intermediary_${SCENARIO}.log"
fi

# === Step 4: run adapter ===
echo "[$(date '+%F %T')] Running Python → LPJG-format adapter"
"${ROOT}/intermediary_py/.venv/bin/python" \
  "${ROOT}/tools/imogen_inputs_to_lpjg_format.py" \
  --input "${PY_OUT}" \
  --output "${SCRATCH}/LPJG_main/IMOGEN/" \
  2>&1 | tee "${LOG_DIR}/adapter_${SCENARIO}.log"

# === Step 5: stage non-CO2 RF (currently from static IIASA file) ===
cp "${ROOT}/data/imogen/emiss/CMIP6/Non-Co2-CH4-N2O-RF/nonco2_ch4_n2o_RF_historical_${SCENARIO,,}_1850_2100.txt" \
   "${SCRATCH}/LPJG_main/IMOGEN/non_co2_rf.txt"

# === Step 6: clean stale IMOGEN run output ===
rm -rf "${SCRATCH}/IMOGEN"/output 2>/dev/null
rm -f "${SCRATCH}/LPJG_main/IMOGEN/done" 2>/dev/null

# === Step 7: run LPJ-GUESS ===
echo "[$(date '+%F %T')] Running LPJ-GUESS coupled (-input imogencfx)"
cd "${RUN_DIR}"
DIR_COMMON="${SCRATCH}" \
  "${ROOT}/lpjguess/build_imogen/guess" \
  -input imogencfx main.ins \
  2>&1 | tee "${LOG_DIR}/coupled_${SCENARIO}.log"

# === Step 8: collect results ===
echo "[$(date '+%F %T')] Coupled run complete; outputs at ${RUN_DIR}/output/"
ls -la "${RUN_DIR}/output/"

echo "[$(date '+%F %T')] Run summary in ${LOG_DIR}/coupled_${SCENARIO}.log"
```

```bash
#!/bin/bash
# scripts/run_coupled.sbatch  —  cluster SLURM template
# Replace {{...}} placeholders with cluster-specific values

#SBATCH --job-name=landsymm-imogen-{{SCENARIO}}
#SBATCH --partition={{PARTITION}}                # e.g. owl, haswell
#SBATCH --nodes={{NODES}}                        # e.g. 2
#SBATCH --ntasks-per-node={{TASKS}}              # e.g. 40
#SBATCH --time=72:00:00                           # 3 days
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

# Cluster-specific module setup:
module load gcc/14 cmake/3.29 netcdf-c/4.9 netcdf-fortran/4.6 openmpi/5.0
# Or, if the cluster uses Spack / EnvironmentModules / Lmod, adapt:
# spack load gcc@14 cmake netcdf-c netcdf-fortran openmpi

# Use scratch
export DIR_COMMON="/scratch/${USER}/landsymm-imogen-${SLURM_JOB_ID}"
mkdir -p "${DIR_COMMON}"

# Run
srun ./scripts/run_coupled.sh {{SCENARIO}} {{GRIDLIST}}

# Copy results back to permanent storage
rsync -av runs/{{SCENARIO}}/output/ \
       /work/${USER}/landsymm_imogen_runs/{{SCENARIO}}-${SLURM_JOB_ID}/
```

### A.5 RCMIP-vs-IIASA backbone selector (sketch)

If the user chooses Option C of II.1 (support both):

```python
# Intermediary_py/.../src/component_a_anthropogenic/__init__.py
"""
Adds a --backbone CLI option to run_all.py that selects either
RCMIP or IIASA as the substitution backbone.
"""
import argparse
import os

BACKBONE = os.environ.get("INTERMEDIARY_BACKBONE", "rcmip")
assert BACKBONE in ("rcmip", "iiasa"), \
    f"Unknown backbone: {BACKBONE}. Use 'rcmip' (default) or 'iiasa'."

def get_substitution_module():
    if BACKBONE == "rcmip":
        from .rcmip_substitution import rcmip_substitution_processing as mod
    else:
        from .iiasa_substitution import iiasa_substitution_processing as mod
    return mod
```

The `iiasa_substitution/` directory would contain:
```
iiasa_substitution/
├── iiasa_substitution_processing.py   # Reads Data/Concentrations/IIASA/CMIP6/*.xlsx
├── iiasa_lpjg_simulated_decomposer.py  # Splits IIASA per-gas total into lpjg/non-lpjg
└── iiasa_comparison_plotting.py        # Validation plots vs RCMIP backbone
```

Internal logic:

```python
# iiasa_substitution/iiasa_substitution_processing.py
"""
Reads IIASA SSP DB v2.0 CMIP6 emissions and produces the
'lpjg-simulated' and 'non-lpjg-simulated' decomposition files
the C++ Adder expected.

Outputs in same schema as rcmip_substitution_*.csv for downstream
compatibility with Component C.
"""
import pandas as pd
from pathlib import Path
from src.shared.paths import IIASA_INPUTS_DIR, OUT_A_DATA

# IIASA per-sector classifications:
#   "AFOLU|Agriculture" → LPJG/IPCC simulates (substitute)
#   "AFOLU|Land Use Change" → LPJG simulates via NEE (substitute for CO2)
#   "Energy", "Industry", "Transport", "Waste" → not modelled (keep)
LPJG_SIMULATED_SECTORS = ["AFOLU|Agriculture", "AFOLU|Land Use Change"]

def decompose(scenario, gas):
    df = pd.read_excel(IIASA_INPUTS_DIR / f"{scenario.lower()}.xlsx")
    df_lpjg = df[df["Sector"].isin(LPJG_SIMULATED_SECTORS)].sum()
    df_non = df[~df["Sector"].isin(LPJG_SIMULATED_SECTORS)].sum()
    # ... write to outputs/component_a/data/iiasa_substitution_{gas}.csv
```

This is ~200 lines of Python; not difficult but takes a day to write
and validate.

---

*End of execution plan.*

*This document is a working instrument: please mark items as resolved
or annotate corrections in-place. The sequencing in Part IV is a
suggestion; reorder as the supervisor's priorities dictate.*
