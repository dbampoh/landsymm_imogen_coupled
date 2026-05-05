# 01 – Documentation Inventory (Phase 2, Subagent 1)

Investigator: Subagent 1 / 8 (documentation only).
Scope: every `.docx`, `.pdf`, `.md`, `.txt`, `README*` and `readme*` file in the
two coupled-model trees, **except** files inside `Data/`, GCM-pattern stores,
build directories, and inside the upstream LPJ-GUESS svn trunk that were
explicitly out of scope (other subagents handle those).

Paths investigated (read-only):

- `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/References/`
- `version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/References/`
- Both top-level `README.md` files
- All sub-system `README.txt`, `README.txt.txt`, `README.md`, `HANDOFF.md`,
  `Quick_Start.md`, `TECHNICAL_MANUAL.md`, etc.
- The `IMOGEN-codebase/docs/` and `IMOGEN-codebase/patterns/readme.log`
- The upstream LPJ-GUESS 4.1 svn `readme.txt`, `releasenotes.txt`,
  `benchmarks/readme.txt`, `tests/README.md`, `windows_version/readme_guesswin.txt`
  (each summarised once because they are upstream LPJ-GUESS distribution
  files, not coupled-model docs).

`docx` text was extracted with `python-docx`; PDFs were sampled with
`pdftotext`. Verbatim quotations are rendered in fenced blocks; everything
else is paraphrase with explicit citations to the source path.

---

## 1. Executive summary

The coupled-model is documented through **three distinct documentation
strata**, in increasing order of authority:

1. **Project-internal drafts** (the "flimsy" technical manual and notes the
   user mentioned). Most are in `References/` as `.docx` / `.pdf` / `.txt`.
   They are practical, descriptive, and frequently incomplete. Several
   contain placeholder sections (e.g. `Troubleshooting`, `Case Studies`) or
   stale Windows-era assumptions.

2. **The supervisor-reviewed working paper draft**
   `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` (2026-04-24). This is the
   only document that names the framework as **"LandSyMM-IMOGEN"**, defines
   it as a *spatially-explicit, emissions-driven coupled framework* combining
   PLUM v2 + LPJ-GUESS + IPCC Tier-1 + IMOGEN (with FaIR v1.3 ERF), and
   commits to a closed two-stage protocol (open-loop yield generation → closed-
   loop emissions/feedback) under SSP1–RCP2.6 and SSP2–RCP4.5 with the
   ISIMIP-3b MRI-ESM2-0 GCM pattern, on a common 0.5° grid, 1850–2100. This
   is the definitive scientific source-of-truth for the framework's design
   intent, scope, units, harmonisation procedures, and acknowledged biases.

3. **Peer-reviewed papers in `References/`** that ground the science: Smith
   2014 (LPJ-GUESS with N), Lindeskog 2013 (managed land), Olin 2015a/b
   (yields), Wania 2010 (LPJ-WHyMe), Alexander 2018 (PLUM v2), Engström 2016
   (PLUM demand), Rabin 2020 (LandSyMM ecosystem services), Huntingford 2010
   (IMOGEN), Zelazowski 2018 (22-GCM patterns), Smith 2018 (FAIR v1.3),
   Mathison 2025 (PRIME — pattern that the working paper explicitly follows
   for FaIR-driven IMOGEN), Hayman 2021 (CH₄ mitigation with IMOGEN), Hurtt
   2020 (LUH2), Winkler 2021 (HILDA+ v2), Tian 2024 (GNB), Saunois 2020/2025
   (GMB), Friedlingstein 2023/2025 (GCB), IPCC 2006/2019 chapters and AR5/AR6.

In addition there is a fully self-contained, well-organised Python codebase
documentation set under `Intermediary_py/` (top-level `README.md`,
`HANDOFF.md`, `Quick_Start.md`, `TECHNICAL_MANUAL.md`, plus six per-component
markdowns). This documents the **emissions-integration intermediary
controller** — what the working paper calls the "Intermediary Controller
(IC)" — at code level. It is the most thorough and most up-to-date
description of how the integrated-emissions dataset is actually constructed.

The two repository versions (A and B) are nearly identical at the
documentation level. **Version B has six extra documents**: the Alexander
2017/2018 and Rabin 2020 PDFs (papers), four extra GMD/IPCC PDFs
(`gmd-11-541-2018` Zelazowski, `gmd-15-6709-2022` Martín Belda LPJ-
GUESS/LSMv1, `gmd-18-1785-2025` Mathison PRIME, `WG1AR5_Chapter06_FINAL`,
`V2_1_Ch1_Introduction`), and four B-only working notes
(`Emissions Handling Methodology.docx`, `NEE-NBP Changes Report.docx`/`.pdf`,
`Plots-Details.txt`, `Projets_Completion_Plan_Blueprint.txt`).

Across the documentation set there are several real contradictions — most
importantly, an **older static-fraction N₂O disaggregation methodology**
(`Brief Documentation of N2O Disaggregation Methodology.docx/.pdf`,
2023-12-19, based on Ciais 2013 IPCC AR5 Ch6 Table 6.9 → 59.81 % LPJG /
40.19 % non-LPJG) versus the **dynamic temporal-based proportion** described
in the supervisor-reviewed working paper (§2.3.2) sourced from Tian 2024
GNB. The working paper is authoritative; the older static doc is now
**outdated** and should be retired or annotated as historical.

Other contradictions are smaller but worth flagging: the `LPJG_IMOGEN
coupling docs.docx` describes Microsoft Visual Studio / MSVC build paths and
Windows-style `C:\GitHub\...` directory absolutes that the user has
explicitly told us to ignore (Linux-only project); the older
`Imogen_paper_GMD.docx` (2025-06-12, the user said to ignore) uses
SSP1–RCP2.6 + SSP5–RCP8.5 and IPSL-CM6-MR rather than the working paper's
SSP1–RCP2.6 + SSP2–RCP4.5 and MRI-ESM2-0; and the early `Adding Net Biome
Productivity Calculations to Technical Branch of LPJG v4.docx` (2023-04-29)
contains an *incorrect* NBP/NEE formula that was later explicitly corrected
in `NEE-NBP Changes Report.docx` (B-only, 2026-03-21).

The repository contains **at least three Word lock files / temp artefacts**
(`~$broutines Defined in imogen.docx`, `~$issions Handling Methodology.docx`
in B, `~WRL0536.tmp`) that should be removed during consolidation.

---

## 2. Per-document index

I organise the index by **scientific authority rank** rather than alphabetic
order, so it doubles as a reading order. Within each tier I order by
modification date (newest first). All sizes are in bytes; dates are file
mtimes. Where A and B copies are byte-identical (same size and content),
I report once and call out the duplication.

Authoritativeness ratings used:

- **AUTHORITATIVE** — current source-of-truth for its topic.
- **SUPPLEMENT** — useful but should be read together with an authoritative
  doc (e.g. low-level code snippets or sector-specific notes).
- **OUTDATED** — superseded by a newer doc; keep for historical record only.
- **JUNK** — Word lock files, temp files, empty stubs. Should be deleted in
  the unified codebase.
- **OUT-OF-SCOPE** — present in `References/` but the user has told us to
  ignore (cross-compiler / Windows / older fork-integration notes / older
  paper draft) or upstream LPJ-GUESS distribution files.

### 2.1 TIER 1 — Working paper draft (single source of scientific truth)

#### `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` ⭐
- **Path (A):** `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/References/IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`
- **Path (B):** identical copy at the corresponding path under `version_B/...` (same size 12 640 741 B, same mtime 2026-04-24 00:30).
- **A-only / B-only / both:** Both. Byte-identical.
- **Size / mtime:** 12 640 741 B / 2026-04-24 00:30 (most recent
  scientific-content edit in `References/`).
- **Authoritativeness:** **AUTHORITATIVE** for the science of the coupled
  framework. Marked by the user as "supervisor-reviewed working paper draft,
  intro+methods only — important source of truth".
- **Summary:** Working draft of the GMD paper. Explicitly names the
  framework "**LandSyMM-IMOGEN**" (Title:
  > "A novel coupled model framework to explore the influence of bottom-up
  >  agricultural, land use, and management emissions on climate-ecosystem
  >  interactions."
  ).  
  Sections covered: Abstract, §1 Introduction, §2 Methods (§2.1 the
  framework with §2.1.1 LPJ-GUESS / §2.1.2 PLUM v2 / §2.1.3 IMOGEN; §2.2
  Tier-1 emission modules with §2.2.1 enteric fermentation, §2.2.2 manure
  management CH₄, §2.2.3 rice cultivation, §2.2.4 manure-management N₂O,
  §2.2.5 managed soils N₂O, §2.2.6 biogenic CO₂ flux, §2.2.7 LPJ-WHyMe
  CH₄, §2.2.8 mechanistic biogenic N₂O, §2.2.9 SSP–RCP scenario projections;
  §2.3 Data Preprocessing/Harmonisation/Integration with §2.3.1 Backward
  Tapered Harmonisation, §2.3.2 Dynamic Emission Segregation and
  Substitution, §2.3.3 Hybrid Temporal Integration / Historical Benchmarking,
  §2.3.4 Post-Integration Smoothing; §2.4 Coupled-model architecture with
  §2.4.1 control layer, §2.4.2 cadence, §2.4.3 two-stage protocol, §2.4.4
  emissions integration & sector ownership / double-counting, §2.4.5 land-use
  harmonisation, §2.4.6 output products & coupling diagnostics, §2.4.7 output
  analysis & evaluation), §3 Results (placeholders), §4 Discussion
  (placeholders), Code & Data Availability, Author Contributions,
  References, Appendix A (Tables A1–A14: IPCC EFs, VSE, N excretion, TAM,
  B₀, MCF, AWMS regional fractions for cattle/buffalo/swine/sheep/goats/poultry,
  managed-soil EFs, rice CH₄ parameters).

  Critical methodological decisions documented here that any subsequent
  documentation should be consistent with:
  - SSP1–RCP2.6 + SSP2–RCP4.5 (NOT SSP5).
  - 1850–2100 horizon, 0.5° common grid, 500-yr soil/N spin-up.
  - Two-stage coupling: Stage I (open loop) drives LPJ-GUESS with prescribed
    ISIMIP-3b MRI-ESM2-0 climate to produce factorial-management potential
    yields for PLUM; Stage II (closed loop) is bottom-up emissions →
    Intermediary Controller → IMOGEN climate → final realised LPJ-GUESS run.
  - **FaIR v1.3 (Smith et al. 2018) is integrated as the ERF module
    upstream of IMOGEN's energy-balance model**, "extends the standard
    IMOGEN configuration of Huntingford et al. (2010) and follows the
    approach implemented in the PRIME framework (Mathison et al., 2025)".
  - LPJ-WHyMe wetland CH₄ activated only **>40°N**; managed peatlands
    disabled; tropical wetland CH₄ retained as IIASA residual (acknowledged
    limitation).
  - Tier-1 EFs **held static 2020–2100** (Eq. 2 = arithmetic mean across
    productivity systems); acknowledged as a Tier-1 limitation (§2.4.6).
  - Acknowledged biases listed explicitly (§2.2.3, §2.2.5, §2.4.6):
    rice continuous-flooding +15-40 % high; managed-soil N₂O ~−20-30 % low
    (EF₃, EF₄, EF₅ excluded); blended EF₁ = 0.01 vs IPCC-2019 0.011 → ~−6-7 %.
  - HILDA+ v2 historical land-use; LUH2-style 5-year-window harmonisation at
    2020 boundary.
  - Three temporal phases: 1850–1960 prescribed IIASA bedrock; 1961–2019
    FAOSTAT-driven historical validation; 2020–2100 PLUM-driven scenario.
  - Validation thresholds: ±15 % PBIAS for sectoral inventory; CO₂ RMSD ≤ 5
    ppm, CH₄ ≤ 50 ppb, N₂O ≤ 5 ppb on concentrations.
- **Cross-refs:**
  - Supersedes `Imogen_paper_GMD.docx` (older draft, see 2.3 below).
  - Authoritative over `LPJG_IMOGEN coupling docs.docx` for any clash on
    science/scope (the latter pre-dates the LandSyMM-IMOGEN naming).
  - Authoritative over `Brief Documentation of N2O Disaggregation
    Methodology.docx/.pdf` (the working paper's §2.3.2 prescribes a
    *dynamic* sector-by-year proportion sourced from IIASA CMIP6 sectoral
    decomposition + Tian 2024 GNB; the older brief uses a *static* 59.81 %
    split based on Ciais 2013 / IPCC AR5 Ch6 Table 6.9).
  - References many of the peer-reviewed PDFs in `References/`; most
    citations resolve to PDFs that are physically present (Alexander 2018 in
    B, Rabin 2020 in B, Smith 2014 — not in `References/` but cited; Olin
    2015a/b — only Olin 2015 (`esd-6-745-2015_Olin.pdf`) is present;
    Lindeskog 2013 — not in `References/`; Wania 2010 LPJ-WHyMe — not in
    `References/`; Hurtt 2020 LUH2 — not in `References/`).

### 2.2 TIER 2 — Authoritative project-internal technical docs

#### `LPJG_IMOGEN coupling docs.docx`
- **Path:** `…/References/LPJG_IMOGEN coupling docs.docx` in BOTH versions, byte-identical.
- **Size / mtime:** 589 546 B / 2026-05-01 15:31.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **AUTHORITATIVE for code/configuration interface**
  (i.e. exact contents of `imogen_settings.txt`, `imogen_lpjg.txt`, the
  `Imogen Controller` workflow, and the exact set of intermediary modules:
  Extractor, Adder, Calculator, PLUM Data Preprocessor, Maps); **OUTDATED for
  the science** (predates the LandSyMM-IMOGEN naming, refers to Microsoft
  Visual Studio + Windows + MSVC, and lists the early static C++ map
  implementation rather than the current Python pipeline).
  Note: this is the document the user described as "the flimsy coupled
  model description"; it has stub headers `Troubleshooting and debugging`,
  `Case Studies`, `Future Developments`, `Appendices/Glossary` that are
  empty in the current draft.
- **Summary:** Comprehensive technical manual structured as
  1.0 Introduction (purpose, scope, audience, significance);
  2.0 Model Description (LPJ-GUESS, IMOGEN);
  3.0 Model Coupling Framework (architecture, integration, data flow);
  Setup & Configuration (prerequisites, folder structure, installation);
  Forward coupling (start-up vegetation procedure, with the
  `imogen_input.cpp` module name); Setting up IMOGEN (`imogen_settings.txt`
  + `imogen_lpjg.txt` configuration), Backward coupling. Then several
  appended sub-documents:
  - Adding Net Biome Productivity Calculations to Technical Branch of LPJG
    v4.1 (the OLD formula — see Tier 4 below for the current corrected
    formula);
  - New Pasture Fertilization Routine in LPJG v4.1 (the `pasture_nfert()`
    routine);
  - Output Files Update and ANPP Printout Routine (`anpp_pasture_st.out`);
  - Re-assessment and validation of intermediary maps (Maps 1–15: enteric
    fermentation EF for buffalo/cattle, EF for other livestock, animal-
    category-to-PLUM mappings, country-to-region map, VSE rate, animal-mass
    map, regions-to-climate, MMS N₂O EF, wetland country-to-climate,
    wetlands-climate-to-diffusion EF, MCF for CH₄ MMS, AWMS).
  Includes verbatim Fortran/C++ snippets for `imogen_settings.txt`
  parameters with 30+ defaults (`STEP_DAY 1`, `T_OCEAN_INIT 289.28`,
  `KAPPA_O 280.0`, `F_OCEAN 0.71`, `LAMBDA_L 0.4`, `LAMBDA_O 1.9`, `MU 1.78`,
  `Q2CO2 3.74`, `TAU_DECAY_CH4 9.3`, `TAU_DECAY_N2O 121`, `CO2_INIT_PPMV
  286.085`, `CH4_INIT_PPBV 865.0`, `N2O_INIT_PPBV 277.4`, `NYR_NON_CO2 251`,
  `NYR_EMISS 251`, `NYR_LPJG_FLUX 251`, etc.). Mentions the **five LPJ-GUESS
  input modules**:
  > "1. **demo**, 2. **cfx**, 3. **imogen_cfx**, 4. **imogen_input**, 5. **cfinput**.
  >  The **demo** and **cfinput** modules come with the standard LPJG
  >  release and support basic functionality. **imogen_input**, **imogen_cfx**,
  >  and **cfx** modules are specifically designed to accommodate the unique
  >  functionality of this tight coupling setup."
- **Cross-refs / contradictions:**
  - Description of Microsoft Visual Studio + MSVC for Windows users
    contradicts the user's declared Linux-only stance; that section should
    be marked OUT-OF-SCOPE in the unified codebase. The MSVC/GCC cross-
    compiler issues are documented separately in `Addressing Cross-Compiler
    Incompatibilities Between MSVC and GCC.docx` (also OUT-OF-SCOPE per user
    instruction).
  - Maps 1–15 here are the C++ implementation; the working paper's §2.2 and
    Appendix A describe the same data in tabular form, and the
    `Intermediary_py/` codebase implements them in Python. The C++ maps,
    Python maps, and Appendix-A tables should all be reconciled against IPCC
    2019 Refinement Tables 10.10/10.11/10.13A/10.16a/10.17/10.19/10.21/10.22/
    10A.5/10A.6-10A.9/11.1/5.11.
  - The "Adding NBP" sub-section here uses the same OLD formula as the
    standalone `Adding Net Biome Productivity…docx` (see Tier 4); the
    `NEE-NBP Changes Report.docx` (B-only) explicitly supersedes it.

#### `Subroutines Defined in imogen.docx`
- **Path:** `…/References/Subroutines Defined in imogen.docx` in BOTH versions, byte-identical.
- **Size / mtime:** 15 363 B / 2025-06-12 22:20.
- **A-only / B-only / both:** Both, byte-identical (5 KB, very small).
- **Authoritativeness:** **AUTHORITATIVE** for documenting the IMOGEN
  Fortran subroutine surface; small, focused, accurate.
- **Summary:** One-page reference for nine subroutines defined in
  `imogen_lpjg.f`:
  - `SETTIN` — reads `imogen_settings.txt`, outputs all the parameters
    listed in `LPJG_IMOGEN coupling docs.docx`.
  - `SETTIN_LPJG` — reads LPJG-side coupling settings (year ranges, spin-up
    flag).
  - `RADF_CO2` — radiative forcing from CO₂ concentration.
  - `RADF_NON_CO2` — radiative forcing from non-CO₂ GHGs (or from a file).
  - `GCM_ANLG` — pattern-scaled GCM analogue model producing climate
    anomalies (T, P, RH15M, U/V wind, DTEMP, PSTAR, SW, LW).
  - `CLIM_CALC` — combines climatology + anomalies → daily/sub-daily driving
    fields for impacts/DGVM (note: the existence of `STEP_DAY` and
    `SEC_DAY` suggests sub-daily disaggregation is supported).
  - `OCEAN_CO2` — box-model ocean carbon uptake.
  - `RESPONSE` — ocean response function used inside `OCEAN_CO2`.
  - `QSAT` — saturation mixing ratio (Goff-Gratch formulation).
- **Cross-refs:** Names (e.g. `RADF_CO2`, `OCEAN_CO2`) match the variables
  documented in `LPJG_IMOGEN coupling docs.docx` and the parameters listed
  in `imogen_settings.txt`. Useful read-along when subagents 2-8 inspect the
  Fortran code.

### 2.3 TIER 3 — Authoritative documentation of the Python intermediary

The `Intermediary_py/` tree contains a self-contained Python codebase
("**imogen_ghg_controller**", v0.1.0, MIT-licensed) that implements what the
working paper calls the "Intermediary Controller" — i.e. building the
sector-complete annual emissions time-series that drives IMOGEN. The
documentation set here is **the most thorough technical documentation in
the entire repository**. The codebase is **physically triplicated** at
three sibling paths (top-level `Intermediary_py/`,
`Intermediary_py/imogen_ghg_controller_FULL/imogen_ghg_controller/`, and
`Intermediary_py/imogen_ghg_controller_SOURCE_ONLY/imogen_ghg_controller/`)
and each triplicate carries the same docs. The two version-A and version-B
copies are byte-identical to each other. **All three copies of every doc
are byte-identical** (verified via `diff -q`).

I therefore describe each document **once**; the path I cite is the
top-level one in `version_A`. When consolidating, only the top-level copy
should be retained.

#### `Intermediary_py/README.md`
- **Path:** `…/Intermediary_py/README.md`.
- **Size / mtime:** 25 064 B / 2026-04-28 20:47.
- **A-only / B-only / both:** Both, byte-identical (and triplicated).
- **Authoritativeness:** **AUTHORITATIVE** for the Python intermediary
  pipeline (Components A–D).
- **Summary:** Comprehensive user-facing README. Documents the deliverable:
  "*a set of CSV files at `outputs/imogen_inputs/`, one per SSP-RCP scenario,
  each containing 1900–2100 annual emission values for CH₄, N₂O, and CO₂
  (decomposed into anthropogenic, natural, and total components)*". Schema:
  Year + (anthro/natural/total per gas) in Mt-of-gas/yr; CO₂ split into
  EFOS/NEE/total. Pipeline overview: Component A (anthropogenic agricultural
  inventory: IPCC 2019 Tier-1 + FAO 1970–2020 + PLUMv2 2020–2100, with
  RCMIP substitution); Component B (LPJ-GUESS DGVM streaming aggregation);
  Component C (integration + three independent comparators); Component D
  (IMOGEN export). Lists inputs to obtain (FAO, PLUMv2, LPJ-GUESS .gz,
  RCMIP, FAIR-ERF, EDGAR, reference PDFs). Documents the EDGAR usage:
  "*All 16 of 17 EDGAR-touching scripts use the **NEW** EDGAR 2025 release …
  The single exception is `n2o_synfert_processing.py`, which uses the **OLD**
  ESSD release because the OLD release has IPCC code 4D11 'Synthetic
  Fertilizers' as a dedicated sub-category that the NEW release aggregates
  into 3.C.4 + 3.C.5*". Headlines historical-period validation: CO₂ within
  ±1σ of GCB partition for all six decades 1960s–2014–2023; CH₄ within
  range for 2000–2009; N₂O within range for all reported periods.
- **Five SSP–RCP scenarios:** SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP4-6.0,
  SSP5-8.5 — i.e. the Python pipeline runs **all five**, while the working
  paper's evaluation focuses on SSP1-2.6 + SSP2-4.5 only.
- **Cross-refs / contradictions:**
  - **Five-scenario coverage** here vs **two-scenario evaluation** in the
    working paper is not a contradiction in *capability* (the pipeline can
    produce all five) but is something to flag in the unified codebase: the
    paper is intentionally narrower.
  - **CMIP5 vs CMIP6**: the Python pipeline uses RCMIP Phase 2 (CMIP6-aligned)
    throughout. The working paper §2.3.1 mentions CMIP5 1850–1989 +
    CMIP6 1990–2100 spliced via Backward Tapered Harmonisation; the older
    `Intermediary/Code/config.txt` lists CMIP5-only IIASA inputs. The Python
    `HANDOFF.md` does not mention CMIP5 directly; the inferred reconciliation
    is that RCMIP Phase 2 already provides a continuous 1750–2100 series
    that subsumes the CMIP5/6 splice. **Worth confirming with subagent
    investigating the actual data files**.

#### `Intermediary_py/HANDOFF.md`
- **Path:** `…/Intermediary_py/HANDOFF.md`.
- **Size / mtime:** 92 662 B / 2026-04-28 20:47.
- **A-only / B-only / both:** Both, byte-identical (and triplicated).
- **Authoritativeness:** **AUTHORITATIVE** record of every methodological
  decision in the Python pipeline. Long but extremely comprehensive.
- **Summary:** Project mission statement; per-component sections; iteration
  history (16 numbered rounds); validated values vs published budgets; plot
  conventions; specific budget reference values cited from GMB 2025 / GNB
  2024 / GCB 2025 / FAIR-ERF v1.3 (with table-by-table provenance from
  source PDFs); end-of-century scenario endpoints by SSP; codebase
  reorganisation history; environment notes; complete file inventory.
  Notable methodological commitments documented here that are not in the
  working paper:
  - "**HIST_END = 2014**": the boundary used in plots and smoothing; the
    last year before RCMIP scenarios diverge (verified empirically: spread
    is 0 at 2014, jumps to 65 Mt CH₄ by 2020).
  - **"Black historical convention"** in plots: 1900–2014 drawn once in
    black; per-scenario colours from 2015.
  - **Option A vs Option B comparator decision**: Option B (hybrid: budget
    anchors 1980–2020, RCMIP+FAIR-ERF outside, with SLAND correction for
    CO₂) preferred as primary; Option A (RCMIP+FAIR-ERF throughout) retained
    as supplementary for reading off the LPJ-GUESS NEE sink magnitude per
    scenario directly from the CO₂ Δ panel.
  - **CH₄ combined natural** is *LPJ wetland + GMB IFW (+112 Mt) − GMB DCC
    (−23 Mt)*, applied uniformly 1901–2100. (This is **inland fresh water +
    dam/canal correction** from Saunois 2025 Table 3.)
  - **N₂O natural** is `N2O_soil + N2O_fire` from `lpjg_ngases.out`.
  - **CO₂ Option-A integration framing**: anthropogenic = RCMIP "MAGICC
    Fossil and Industrial" (EFOS-only); natural = LPJ-GUESS NEE; combined ≈
    GCB partition `EFOS + ELUC − SLAND`. Empirically validated: 2014–2020
    SSP2-4.5 mean = 7.93 Pg C/yr vs GCB = 7.60 ± 1.24.
  - LPJ-GUESS forcing: **HILDA+ v2 historical** for 1901–2020; **PLUMv2
    SSP-RCP land use harmonised with HILDA+v2 via the LUH2 protocol** for
    2021–2100. (Identical phrasing to the working paper §2.4.5.)
  - 0.5° × 0.5°, 62 538 land grid cells (140.28 M km² = 94.2 % of land
    area), latitude range −55.25° to 83.25°.
  - LPJ-GUESS scenario boundary discontinuity at 2020/2021: each scenario
    is an *independent* simulation with its own spin-up state, so N₂O drops
    by ~3 Tg N₂O between historical 2020 and scenario 2021. This is real
    model behaviour, not a bug. **Flag for the unified codebase: the working
    paper's harmonisation procedures (§2.3.4) do not explicitly address
    this LPJ-GUESS-internal discontinuity — they address the emissions-
    level boundary, not the simulation-state boundary.**
- **Cross-refs:** Strongly aligned with the working paper §2.3 and §2.4
  prose. Differences:
  - HANDOFF.md is concrete about exact years used as anchor midpoints
    (CH₄: 2005, 2015, 2020; N₂O: 1997, 2015, 2020; CO₂: 1965/1975/1985/
    1995/2005/2018) — the working paper §2.3.1 uses generic notation.
  - HANDOFF.md uses RCMIP+FAIR-ERF as the "conventional climate-emulator
    counterfactual"; the working paper uses "IIASA CMIP6 reference
    trajectories" + "FAIR-driven IMOGEN of pure IIASA". These are
    *similar but not identical* baselines; reconciling them in the unified
    codebase will require a careful prose pass.

#### `Intermediary_py/TECHNICAL_MANUAL.md`
- **Path:** `…/Intermediary_py/TECHNICAL_MANUAL.md`.
- **Size / mtime:** 111 470 B / 2026-04-28 20:47.
- **A-only / B-only / both:** Both, byte-identical (and triplicated).
- **Authoritativeness:** **AUTHORITATIVE** code-level technical manual. By
  far the longest single piece of documentation in the repository.
- **Summary:** 18 sections covering project context & scientific goals,
  architecture overview, repository layout in detail, installation,
  shared module, per-component deep dives (A/B/C/D), pipeline driver
  (`run_all.py`), inputs catalogue, outputs catalogue, tests &
  reproducibility, troubleshooting, **known issues and limitations**
  (§15 — important read for unification), opportunities for further
  development (§16), glossary, bibliography. Designed to complement
  `README.md` and `HANDOFF.md`.
- **Cross-refs:** Identical scope to HANDOFF.md but written for new
  readers/maintainers. Some redundancy with HANDOFF.md but not contradiction.

#### `Intermediary_py/Quick_Start.md`
- **Path:** `…/Intermediary_py/Quick_Start.md`.
- **Size / mtime:** 7 679 B / 2026-04-29 13:57.
- **A-only / B-only / both:** Both, byte-identical (and triplicated). **Note:** the version-B copy in `Intermediary_py/imogen_ghg_controller_*` is byte-identical with the same mtime.
- **Authoritativeness:** **SUPPLEMENT**. Hybrid file: lines 1-15 are an
  out-of-place chat-conversation excerpt about reproducibility verification
  (`FAOCountry` vs `Country` column-header diff); lines 16+ are the actual
  quick-start instructions for setting up a git repo and running the
  pipeline on Ubuntu. The chat excerpt at the top should be deleted in
  the unified codebase.
- **Summary (of useful section):** Step-by-step instructions to extract
  source tarball, populate `inputs/`, install Python dependencies,
  verify input layout via the `paths.py` constants, dry-run the pipeline,
  do a full run (~25–40 min), and verify outputs. Names runtime
  expectations: Component A 28 steps ~10–15 min; Component B 5 steps
  ~10–15 min (LPJ-GUESS streaming); Component C 9 steps ~1 min;
  Component D ~2 s. Memory note: the livestock anchor needs **6–8 GB
  RAM**.

#### `Intermediary_py/inputs_README.md`
- **Path:** `…/Intermediary_py/inputs_README.md`.
- **Size / mtime:** 6 932 B / 2026-04-28 20:47.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **AUTHORITATIVE** for input-data structure of the
  Python pipeline.
- **Summary:** Documents the expected `inputs/` directory layout: `fao/`,
  `plum/`, `lpjg/historical+scenarios/`, `rcmip/`, `fair_erf/`, `edgar/`,
  `reference_pdfs/`. Acquisition instructions for each public source (URLs,
  bulk-download CSVs); project-internal sources (PLUMv2, LPJ-GUESS .gz on
  request from the modeller). Disk-space estimates (~2.8 GB total). Inputs
  verification one-liner via `from src.shared.paths import …`.

#### Per-component docs in `Intermediary_py/imogen_ghg_controller_*/imogen_ghg_controller/docs/`

- `methodology.md` (≈3 KB): unified methodology summary; cross-references
  HANDOFF.md.
- `component_A.md` (≈3 KB): Component A scope (6 sectors × historical/
  scenario × Tier-1 substitution); names input data per sector (FAO
  livestock, FAO rice, FAO fertiliser).
- `component_B.md` (≈3 KB): Component B scope; cell-area formula
  `A(lat) = (0.5 × π/180)² × R² × cos(rad(lat))` with `R = 6.371e6 m`;
  unit-conversion pipeline per gas; validation values vs GMB 2025/GNB
  2024/GCB 2025.
- `component_C.md` (≈3 KB): Component C scope; comparator construction;
  Option-A vs Option-B reasoning; black-historical convention; HIST_END
  = 2014.
- `component_D.md` (≈2 KB): Component D scope; output schema (5 wide-format
  CSVs + 1 long-format CSV); unit notes (Mt CO₂, NOT Mt C: divide by
  `44/12 × 1000 = 3666.67` for Pg C).
- `budget_references.md` (≈4 KB): citation tables for GMB 2025 (Saunois
  Table 3), GNB 2024 (Tian executive summary), GCB 2025 (Friedlingstein
  Table 7), FAIR-ERF v1.3 (Smith 2018), RCMIP Phase 2 (Nicholls 2020).
  Note: the GMB 2025 values quoted here in *budget_references.md* are
  **Table 3 of Saunois et al. 2025** (`essd-17-1873-2025_GMB.pdf` is
  physically present in `References/`).

All of these per-component docs are present at three locations (top-level
`Intermediary_py/imogen_ghg_controller_FULL/…` and `_SOURCE_ONLY/…` and
trivially also in version_B); all byte-identical.

### 2.4 TIER 4 — Authoritative component-specific notes (B-only or both)

#### `Emissions Handling Methodology.docx` *(B-only)*
- **Path:** `version_B/.../References/Emissions Handling Methodology.docx`.
- **Size / mtime:** 17 908 B / 2026-03-21 22:37.
- **A-only / B-only / both:** **B-only**.
- **Authoritativeness:** **AUTHORITATIVE** for the *outline* of how
  emissions are handled at the integration level; **SUPPLEMENT** to the
  working paper §2.3.
- **Summary:** Seven sections: (1) Source and Access (IIASA SSP Database
  v2.0; CMIP6 Emissions section; SSP1-26/SSP2-45/SSP3-70/SSP4-60/SSP5-85);
  (2) Data Components and Coverage (CO₂ + CH₄ disaggregated to component
  level, N₂O totals only); (3) Disaggregation by Components (full sector
  list per gas); (4) Modelled vs Non-Modelled Components (table mapping
  modelled = LPJ-GUESS + IPCC-PLUM Tier 1, non-modelled = energy/industry/
  transport/etc.); (5) Estimation for N₂O (uses Tian 2024 GNB to derive a
  *temporal dynamic proportion* — a key statement that supersedes the older
  `Brief Documentation of N2O Disaggregation Methodology`); (6) **Spline
  Harmonisation Approach** (Univariate Spline ratio of modelled total
  to IIASA total to align long-term trajectories); (7) Summary Workflow.
- **Contradictions / Cross-refs:**
  - The "spline harmonisation" mentioned here is **partly different** from
    the working paper §2.3.4, which describes Backward Tapered
    Harmonisation + Regression-Based Trend Matching + 5-yr Centred Moving
    Average. The two could be complementary (spline harmonisation between
    modelled-total and IIASA-total at year level; tapering at boundaries),
    or one supersedes the other. **Flag for unification: confirm whether
    the production code uses one, both, or has switched between
    methodologies.** Looking at the Python pipeline's HANDOFF.md, neither
    Backward Tapering nor spline harmonisation is implemented as such; the
    Python pipeline uses **segmented running means** at the historical/
    scenario boundary instead, and pre-1970 anthropogenic uses RCMIP
    unchanged (no harmonisation needed because there is no LPJ-GUESS-derived
    anthropogenic before 1970). **There is therefore a real
    documentation-vs-code mismatch** that the unified codebase will need to
    resolve.
  - Aligns with `Brief Documentation of N2O Disaggregation Methodology.docx`
    only in *naming* the same problem (N₂O lacks IIASA component
    disaggregation); the *methodology* differs. This doc supersedes that
    older one.

#### `NEE-NBP Changes Report.docx` and `.pdf` *(B-only)*
- **Paths:** `version_B/.../References/NEE-NBP Changes Report.docx` (15 373 B)
  and `…/NEE-NBP Changes Report.pdf` (159 950 B).
- **mtime:** 2026-03-21 22:37 for both.
- **A-only / B-only / both:** **B-only**.
- **Authoritativeness:** **AUTHORITATIVE**. Explicitly corrects an earlier
  incorrect formula and is the definitive reference for what `cflux.out`
  contains today.
- **Summary:** Authored by Daniel Kojo Bampoh, dated 29.04.2023 in document
  text but mtime 2026-03-21 (so the doc is dated by *content authorship*
  but file-system-modified more recently). Documents the changes to LPJ-
  GUESS v4.1's `commonoutput.cpp` to:
  - **Correct NEE** to *strictly physiological* eco-atmosphere CO₂ exchange
    (= `flux_veg − flux_repr + flux_soil + flux_fire`), removing the
    disturbance/management/lateral terms that were incorrectly grouped
    under NEE in the older code.
  - **Add NBP** as a new column in `cflux.out` defined as
    `NBP = NEE + c_disturb`, where
    `c_disturb = flux_est + flux_seed + flux_charvest +
                 lc.acflux_wood_harvest + lc.acflux_harvest_slow +
                 lc.acflux_clearing + lc.acflux_landuse_change +
                 c_org_leach_gridcell`.
  - Sign convention (positive = net flux to atmosphere = source).
- **Cross-refs / contradictions:**
  - **Explicitly supersedes** `Adding Net Biome Productivity Calculations
    to Technical Branch of LPJG v4.docx` (2024-11-12), which gives the
    *incorrect* formula
    `anbp = flux_veg − flux_repr + flux_soil − flux_fire − flux_est +
            c_org_leach_gridcell + flux_seed + flux_charvest +
            lc.acflux_landuse_change + lc.acflux_harvest_slow −
            sum(mrh) − sum(mra)`. The older formula notably *subtracts*
    `flux_fire`, whereas the corrected formula *adds* it (because positive
    fire flux is a CO₂ source).
  - The same older incorrect NBP description is also embedded inside the
    `LPJG_IMOGEN coupling docs.docx` Tier-2 manual; that manual should be
    updated when the unified codebase is built.

#### `Plots-Details.txt` *(B-only)*
- **Path:** `version_B/.../References/Plots-Details.txt`.
- **Size / mtime:** 3 010 B / 2026-03-21 22:37.
- **A-only / B-only / both:** **B-only**.
- **Authoritativeness:** **SUPPLEMENT** — a working list of plots to make
  for the paper, with open questions in inline `[…]` annotations.
- **Summary:** Two sections. First section enumerates 15 named plots
  needed: e.g. (1) Historic CH₄ enteric fermentation modelled vs FAO vs
  EDGAR vs IIASA; (2) historic CH₄ manure management same; …; (5) historic
  N₂O manure management; (6–10) corresponding future-scenario versions
  with annotation `[should 126 and 245 be on the same graph?]`; (11–13)
  Full pure IIASA CH₄/N₂O/CO₂ CMIP5 (1850–1960) + CMIP6 (1960–2100)
  concatenated trajectories smoothed and unsmoothed; (14–15) IIASA + Base
  Remaining + Modelled historic & scenario concatenated. Second section
  re-lists the IIASA-data variants (annual historic and scenario CH₄/N₂O
  emissions trends from each sector).
- **Cross-refs / contradictions:**
  - The five-scenario set named here is "**126 and 245**" only — but the
    Python pipeline produces all five SSPs and the GMD paper draft also
    formally focuses on SSP1-2.6 + SSP2-4.5. Consistent with the paper.
  - The plot taxonomy here aligns with `Component A` figures in the Python
    pipeline (per-sector global CSVs + RCMIP comparison plots).

#### `Projets_Completion_Plan_Blueprint.txt` *(B-only)*
- **Path:** `version_B/.../References/Projets_Completion_Plan_Blueprint.txt`
  (sic, "Projets" is a typo for "Project's").
- **Size / mtime:** 5 339 B / 2026-03-21 22:37.
- **A-only / B-only / both:** **B-only**.
- **Authoritativeness:** **SUPPLEMENT** — looks like a chat-pasted
  task list / handover from supervisor to DKB.
- **Summary:** Three top-level work items:
  1. Coupled-model setup, simulation, analysis: GHG magnitude/trend
     analysis to debug differences between modelled vs replaced
     emissions (decomposing by sector, reviewing PLUMv2 raw data,
     retracing the IIASA → IPCC[PLUMv2] + LPJ-GUESS[PLUMv2] → IIASA
     processing chain); execute complete IMOGEN→LPJG(PLUM)+IPCC(PLUM)→
     IMOGEN→LPJG cycle on cluster + local; verify the cluster vector-
     allocation optimisation fix.
  2. Land-use input files: verify the Python `plum_harmonization`
     against the original Matlab; compare `MIN_NATURAL_RATE = NaN` vs
     `0`; ratify the Python remapping codebase against Matlab.
  3. Test a parameterised oil-palm PFT: full PFT parameter listing
     embedded in the file (`oilpalm_group` group with `tropical`,
     `shade_intolerant`, `evergreen`, `leaflong 2`, `crownarea_max
     25.0`, `height_max 15.0`, `wooddens 300`, `sla 18.0`, `cnleaf
     25.0`, `harvestfrac 0.5`, `harv_eff 0.95`, `eps_iso 22.0`, full
     `eps_mon`/`storfrac_mon`/`pstemp_*`/`tb`/`phu` calibration; plus
     `OilPalm_nlim` extension with `T_veg_*`, `T_rep_*`, `dev_rate_*`,
     sigmoidal-uptake `a/b/c/d` 1/2/3, `photo`, `fertrate 0.30 0.40`,
     `N_appfert 0.02`, `fertdates 60 210`).
  4. Notes a need to use the remapping codebase to generate HILDA+-based
     baseline LU + cropfracs + nfert inputs after the oil-palm test.
- **Cross-refs:** Useful as a "what's outstanding" checklist; the oil-palm
  PFT is not yet documented elsewhere in the repository.

### 2.5 TIER 4b — LPJ-GUESS code-change notes (both, but mostly older)

#### `Adding Net Biome Productivity Calculations to Technical Branch of LPJG v4.docx`
- **Path:** `…/References/Adding Net Biome Productivity Calculations to Technical Branch of LPJG v4.docx`.
- **Size / mtime:** 16 821 B / 2024-11-12 13:41.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **OUTDATED**. The NBP formula stated here is
  incorrect; supersession is documented in `NEE-NBP Changes Report.docx/.pdf`
  in version B.
- **Summary:** Documents the addition of `anbp` as a new column in
  `cflux.out`, with the formula
  `anbp = flux_veg − flux_repr + flux_soil − flux_fire − flux_est +
          c_org_leach_gridcell + flux_seed + flux_charvest +
          lc.acflux_landuse_change + lc.acflux_harvest_slow −
          sum(mrh) − sum(mra)`. Also notes that monthly NBP is not output
  because monthly fire/establishment fluxes are not computed.
- **Cross-refs / contradictions:** Superseded by `NEE-NBP Changes Report`
  (B-only). Same stale formula appears inside `LPJG_IMOGEN coupling
  docs.docx`.

#### `Pasture_Fert_Doc.docx`
- **Path:** `…/References/Pasture_Fert_Doc.docx`.
- **Size / mtime:** 25 828 B / 2024-11-12 13:41.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **AUTHORITATIVE** for the pasture fertilization
  routine in LPJ-GUESS v4.1.
- **Summary:** Documents `pasture_nfert(Patch& patch)` in `management.cpp/.h`
  (with full source listing) and its integration via `nfert(Patch& patch)`,
  which dispatches CROPLAND → `nfert_crop()`, PASTURE → `pasture_nfert()`,
  default → uniform daily nfert. Uses `N_appfert_mt` from `StandType`
  management; checks `pft.fertrate[0]+pft.fertrate[1] == 1.0`; applies
  fraction on `pft.fertdates[0]` and `[1]`. Includes `outlimit_misc(out,
  out_anpp_pasture_st, pasture_anpp)` ANPP printout routine to
  `anpp_pasture_st.out`.
- **Cross-refs:** Same content also appears verbatim inside `LPJG_IMOGEN
  coupling docs.docx`. Pasture fertilization is part of LandSyMM-IMOGEN's
  managed-land representation.

#### `Brief Documentation of N2O Disaggregation Methodology.docx` and `.pdf`
- **Path:** `…/References/Brief Documentation of N2O Disaggregation
  Methodology.docx` (15 754 B) and `.pdf` (125 336 B).
- **mtime:** 2024-11-12 13:41 for both, in both versions.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **OUTDATED**. The static 59.81 % LPJG / 40.19 %
  non-LPJG split based on Ciais 2013 IPCC AR5 Ch6 Table 6.9 is superseded
  by the **Dynamic Temporal-Based Proportion** described in the working
  paper §2.3.2 (sourced from IIASA CMIP6 sectoral decomposition + Tian
  2024 GNB). The user even labels this in the older
  `LPJG_IMOGEN coupling docs.docx` as a temporary methodology pending a
  better source ("In the special case of N2O where no disaggregation
  exists, a dynamic temporal-based proportion is employed to estimate the
  proportion of LPJG + IPCC simulated emissions, with data from //link to
  paper here").
- **Summary:** Authored by D. Bampoh on 19.12.2023. References Ciais et al.
  2013 (IPCC AR5 Ch6 Table 6.9) as source for the 2006/2011 N₂O budget.
  LPJ-GUESS-Simulated total: 10.7 Gt CO₂-eq/yr (soils under natural
  vegetation 6.6 + agriculture 4.1). LPJ-GUESS Non-Simulated total: 7.19
  Gt CO₂-eq/yr (fossil 0.7 + biomass burning 0.7 + human excreta 0.2 +
  rivers/estuaries/coastal 0.6 + atm. deposition on land 0.4 + on ocean
  0.2 + surface sink −0.01 + oceans 3.8 + lightning 0 + atm. chemistry 0.6).
  Calculation: `n2o_lpjg = n2o_t × (10.7 / (10.7 + 7.19))` and
  `n2o_non_lpjg = n2o_t × (7.19 / (10.7 + 7.19))`. Result: 59.81 %
  simulated / 40.19 % non-simulated.
- **Cross-refs:** Source paper (`WG1AR5_Chapter06_FINAL.pdf`) is present
  *only in version B*. Replaced in current methodology by Tian 2024 GNB
  (`essd-16-2543-2024_GNB.pdf` in both versions).

### 2.6 TIER 4c — Map re-assessment notes

#### `IPCC_Maps_Reassessment_Validation.docx`
- **Path:** `…/References/IPCC_Maps_Reassessment_Validation.docx`.
- **Size / mtime:** 122 154 B / 2026-05-01 15:32.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **AUTHORITATIVE** annotated review of the
  intermediary maps; flags concrete bugs in the C++ implementation
  (placeholder values, duplicate keys, missing-region entries). Useful
  cross-check both for the C++ Intermediary and the Python re-implementation.
- **Summary:** Same map list as the Maps section of `LPJG_IMOGEN coupling
  docs.docx` (Maps 1–N: enteric fermentation EF for cattle/buffalo, EF for
  other livestock, mappings of PLUM categories to IPCC categories,
  countries-to-regions, VSE rate, animal mass map TAM, regions-to-climate,
  MMS N₂O EF, wetlands country-to-climate, wetlands-climate-to-diffusion EF,
  CH₄ MMS by climate zone, AWMS regional fractions). Annotated with
  question-marks where the C++ code is broken or inconsistent — e.g. Map 1
  shows missing values for Western Europe Buffalo and Asia Buffalo
  (rendered as `{"Buffalo", }` in the C++ snippet); Map 2 shows missing
  values for Sheep/Goats/Poultry (rendered as `{"Sheep", }`); Map 4 has
  empty mappings for `Milk whole fresh goat`, `Meat sheep`, etc.; Map 5
  duplicates `Canada` and references regions absent from PLUM countries
  data (`Africa`, `Asia`, `Europe`, `Oceania`, `South America`).
- **Cross-refs:** Strongly aligned with the working paper Appendix A
  parameter tables; the working paper's Tier-1 EF tables can be used to
  audit the C++ map values systematically. **For the unified codebase,
  this document is the authoritative bug list for the C++ Intermediary.**

#### `Reassessment of maps.docx`
- **Path:** `…/References/Reassessment of maps.docx`.
- **Size / mtime:** 76 663 B / 2024-11-12 13:41.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **OUTDATED** — earlier draft of the
  `IPCC_Maps_Reassessment_Validation.docx` above. Contains only Map 1 and
  partial preamble.
- **Summary:** First-pass reassessment; says
  > "These parameters whose readily available default values, in most
  >  cases, have been tabulated in different sections of the 2019
  >  Refinement to the 2006 IPCC Guidelines …",
  but unlike the newer `IPCC_Maps_Reassessment_Validation.docx`, the prose
  is incomplete and only one map (`MAP_ENTERIC_FERMENTATION_EMISSION_
  FACTORS_FOR_BUFFALO_CATTLE`) is shown.

### 2.7 TIER 4d — Project status / integration notes

#### `LPJG Integration Work Overview and Updates[28-05-2024].docx`
- **Path:** `…/References/LPJG Integration Work Overview and Updates[28-05-2024].docx`.
- **Size / mtime:** 16 953 B / 2024-11-12 13:41.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **OUT-OF-SCOPE** per user instruction ("older notes
  on early landsymm fork integration attempts (unrelated to coupled model
  itself)"). I include the brief summary for completeness only.
- **Summary:** DKB integration plan dated 28.05.2024. Lists branches to
  integrate into LPJG Trunk v4.1: Hector v4.0 (`newcrops_sensitivity`,
  `ozone`); Sam v4.1 (`LandSyMM_agric`, `LandSyMM_agric_water_stress_Ks`,
  `LandSyMM_forest`); plus features to add to Trunk v4.1 (Pasture
  Fertilization, Imogen Input Model, CFX Input Model, NBP, N_appFert).
  Pending: review/remove `landsymm_cleach`, `landsymm_cleach_bugfix_1/2`
  commits because they "turn land into a carbon source rather than a sink";
  integrate `landsymm-main` branch incl. `landsymm-dev-crops` and
  `landsymm-dev-forest`.

#### `Ecosystems Modelling Project Update Report.pdf`
- **Path:** `…/References/Ecosystems Modelling Project Update Report.pdf`.
- **Size / mtime:** 105 830 B / 2024-11-12 13:41.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **OUT-OF-SCOPE** (older fork integration notes).
  PDF first-page text:
  > "Ecosystems Modelling Project Update Report. Project Overview. This is
  >  an integration of several key components and versions of LPJG into the
  >  latest Trunk version (LPJG v4.1). The primary objective was to merge
  >  unique features from different versions of …".

#### `Bringing LandSyMM crop water stuff into LPJ-GUESS 4.1.pdf`
- **Path:** `…/References/Bringing LandSyMM crop water stuff into LPJ-GUESS 4.1.pdf`.
- **Size / mtime:** 133 187 B / 2024-11-12 13:41.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **SUPPLEMENT** — code-level integration notes for
  LandSyMM-flavoured crop water functionality in LPJ-GUESS v4.1 (cites
  `LPJ-GUESS r10115 (tag 4.1_211013)`). Useful background reading for
  subagents inspecting `canexch.cpp` / `soilwater.cpp`.

#### `Irrigation and water stress changes for LandSyMM work.pdf`
- **Path:** `…/References/Irrigation and water stress changes for LandSyMM work.pdf`.
- **Size / mtime:** 320 914 B / 2024-11-12 13:41.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **SUPPLEMENT** — companion to `Bringing LandSyMM
  crop water stuff…`.

#### `Addressing Cross-Compiler Incompatibilities Between MSVC and GCC.docx` / `.pdf`
- **Paths:** `…/References/Addressing Cross-Compiler Incompatibilities
  Between MSVC and GCC.docx` (18 763 B) and `.pdf` (140 933 B).
- **mtime:** 2024-11-12 13:41 for both, in both versions.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **OUT-OF-SCOPE** per user instruction (Linux-only
  project). Documents replacing GCC variable-length-array (VLA) usages with
  `std::vector<double>` in `canexch.cpp::irrigated_water_uptake` and
  `soilwater.cpp::infiltrate_upland`. Useful only if cross-compilation is
  ever revisited.

### 2.8 TIER 5 — Older paper draft (user-flagged ignore)

#### `Imogen_paper_GMD.docx`
- **Path:** `…/References/Imogen_paper_GMD.docx`.
- **Size / mtime:** 442 928 B / 2025-06-12 22:20.
- **A-only / B-only / both:** Both, byte-identical.
- **Authoritativeness:** **OUTDATED**. Explicitly user-flagged to ignore.
  Superseded by `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`.
- **Summary (so we can reconcile contradictions if any):** Title:
  > "Modelling the response of future global climate-ecosystem dynamics to
  >  socioeconomically driven changes in agricultural, land use and
  >  management emissions."

  Differences vs the newer working paper draft:
  - Two SSP-RCPs are **SSP1–RCP2.6 + SSP5–RCP8.5** (not SSP2–RCP4.5).
  - GCM is **IPSL-CM6-MR** (not MRI-ESM2-0).
  - Uses **LUH2 (Hurtt et al. 2011)** for historical land use, not HILDA+
    v2 (Winkler 2021).
  - Uses **Global Surface Water (GSW) database** for wetland area, with a
    static average of 1984 and 2018 max-water-extent — the new draft drops
    this in favour of LPJ-WHyMe simulation >40°N + IIASA residual.
  - References table for sector ownership (Table 1 in the older draft):
    Agriculture/Wetlands modelled by IPCC[PLUM+FAO]; grassland burning and
    LUC modelled by LPJ-GUESS; everything else IIASA-prescribed.
  - The older draft has many duplicated boilerplate sentences ("To validate
    outputs, LPJ-GUESS simulations were compared against observed ecosystem
    trends, ensuring the model's accuracy and reliability for predictive
    scenarios.") suggesting AI-rephrase artefacts; the newer draft is far
    more polished.

### 2.9 TIER 6 — Top-level READMEs

#### Top-level `README.md` (both versions, byte-identical, 9 604 B / 2024-11-12)
- **Path (A):** `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/README.md`.
- **Path (B):** identical at corresponding `version_B` path.
- **Authoritativeness:** **SUPPLEMENT** for the top-level coupled-model
  setup (folder structure, module list, done-marker protocol). Predates the
  LandSyMM-IMOGEN naming and the FaIR-driven integration; should be retired
  or fully rewritten in the unified codebase.
- **Summary:** Names the framework "**LPJG-IMOGEN coupling setup for
  Ecosystems Modelling**". Lists the three core models — IMOGEN (climate
  emulator), LPJ-GUESS (DGVM), IPCC (Tier 1 emissions estimator) — in three
  bullet points. Lists the **five LPJ-GUESS input modules** (`demo`, `cfx`,
  `imogen_cfx`, `imogen_input`, `cfinput`) with usage guidance:
  > "**imogen_input** allows standalone, loose, and tight coupling of LPJG
  >  using only IMOGEN data, supporting basic functionalities like the
  >  BLAZE fire model but with limited resolution for nitrogen deposition.
  >  **imogen_cfx** enables both loose and tight coupling while supporting
  >  more advanced features like the Simfire model, finely resolved
  >  nitrogen deposition data, humidity, wind data, and other climate
  >  parameters."

  Defines:
  - "**forward coupling**" = LPJG output → IMOGEN input.
  - "**backward coupling**" = IMOGEN output → LPJG input.
  - "**standalone**" = uncoupled.
  - "**tightly coupled**" = year-by-year real-time exchange.
  - "**loosely coupled**" = full-run-then-pass.
- Names the **done-marker file** synchronisation protocol:
  > "When IMOGEN completes a simulation year, it creates a file named
  >  `done` in the folder for that specific year. LPJG monitors the
  >  presence of this file and, once detected, proceeds with its
  >  simulation for that year using the corresponding climate data."

  Notes a planned but not-yet-built bash script that would invoke both
  models simultaneously. Briefly discusses datasets: IIASA, ISIMIP3b, OWI,
  FAO, PLUM (with the standard "PLUM is a socioeconomically-based land
  use/cover model that uses least-cost-optimization …" boilerplate).

  **Important inconsistency with newer docs:** the README states "LPJG
  handles its own spinup and historical data via netCDF files, while
  IMOGEN provides climate data for the scenario years (usually from 2000
  to 2100). Historical data prior to 2000 is processed entirely through
  netCDF files." — this contradicts the working paper, which has IMOGEN
  producing the entire 1850–2100 monthly forcing in Stage II and uses
  ISIMIP-3b for *Stage I* (potential-yield generation) only.

### 2.10 TIER 7 — Subsystem README stubs

These are tiny files. Most are single-line descriptions in `.txt.txt`
(double extension is a Windows-era artefact and should be normalised to
`.txt` or `.md` during consolidation).

| Path | Size | Authoritativeness | Summary |
|---|---|---|---|
| `Common-directory/README.txt.txt` | 399 B | SUPPLEMENT | Verbatim quote: *"The Common directory serves as the foundational hub for the entire coupled framework. As the root or parent folder, it encapsulates all essential components required for the comprehensive execution of the coupled system."* |
| `Common-directory/LPJG_main/IMOGEN/README.txt.txt` | 0 B | JUNK (empty) | Empty placeholder. |
| `Common-directory/IMOGEN-codebase/patterns/readme.log` | 127 B | SUPPLEMENT | Verbatim: *"#imogen CMIP5 patterns. see also /pd/data/lpj/input_data/IMOGEN_patterns/CMIP5/patterns/. and copy needed patterns folder here"* — points to a server-local patterns store. |
| `Imogen-controller/README.txt` | 1 688 B | AUTHORITATIVE for the C++ controller | Documents `automate_imogen.exe`: monitors/creates the `done` marker file at 2 s intervals; supports `automate_imogen.exe reset` (delete created folders, reset settings) and `automate_imogen.exe move RCP60` (move outputs into named folder). |
| `Imogen-controller/config.txt` | 38 B | JUNK | Verbatim: *"Future implementation of a config file"*. Empty placeholder. |
| `Matlab-scripts/README.txt.txt` | 151 B | SUPPLEMENT | *"MATLAB scripts needed to preprocess and post process data from coupled model framework as well as prepare datasets for usage by coupled model framework"*. |
| `Python-scripts/README.txt.txt` | 151 B | SUPPLEMENT | Same wording but for Python. |
| `References/README.txt.txt` | 186 B | SUPPLEMENT | *"Folder for all references and docs. Main coupled framework doc available on OneDrive for the sake of progressive updates."* + a OneDrive link. Confirms that `LPJG_IMOGEN coupling docs.docx` is the "Main coupled framework doc" mirrored from OneDrive. |
| `Intermediary/Code/config.txt` | 2 270 B | OUTDATED | Configuration file for the older C++ Intermediary, with Windows-style paths (`C:\GitHub\LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK\`) and **CMIP5-only** scenario settings (`scenario=cmip5`, `ssps=1,5`, `rcps=26,85`). **This contradicts the working paper's CMIP6 + Backward Tapered Harmonisation**; the file is a legacy artefact from the C++ Intermediary and is replaced by `Intermediary_py/`. Should be retired in the unified codebase. |

### 2.11 TIER 8 — Upstream LPJ-GUESS 4.1 distribution docs

These are part of the LPJ-GUESS svn release that was vendored into
`Integrations/trunk/trunk_r13078/`. They are upstream distribution files;
the user has implicitly considered the LPJ-GUESS source (other subagents
investigate this); for completeness here, with one-line summaries.

| Path | Size | Auth | Summary |
|---|---|---|---|
| `Integrations/trunk/trunk_r13078/readme.txt` | 5 061 B | OUT-OF-SCOPE | LPJ-GUESS 4.1 release readme — *"This directory contains source code files and other files necessary to run a demonstration version of LPJ-GUESS … in population mode (i.e. as LPJ-DGVM) or cohort mode (i.e. as GUESS) on the Unix or Windows operating system"*. Useful when subagents read the LPJ-GUESS code. |
| `Integrations/trunk/trunk_r13078/reference/releasenotes.txt` | 12 288 B | OUT-OF-SCOPE | LPJ-GUESS 4.0→4.1 release notes (N transformations, BLAZE & SIMFIRE, GWGEN, soil input, …). Useful background. |
| `Integrations/trunk/trunk_r13078/benchmarks/readme.txt` | 5 188 B | OUT-OF-SCOPE | Auto-benchmarking suite docs. PBS/SLURM cluster instructions. |
| `Integrations/trunk/trunk_r13078/tests/README.md` | 3 925 B | OUT-OF-SCOPE | Unit-testing conventions in the LPJ-GUESS C++ codebase. |
| `Integrations/trunk/trunk_r13078/windows_version/readme_guesswin.txt` | 899 B | OUT-OF-SCOPE | Windows-only `guesswin.exe` download link. User explicitly out of scope. |

### 2.12 TIER 9 — Peer-reviewed PDFs (ground-truth science)

Each is the published paper. Per the user, these are the **ground truth for
the science**. I don't summarise them here (they have their own abstracts
and the working paper cites them); I list them, identify which version they
appear in, and flag duplicates.

| Path (relative to `References/`) | Size | A | B | Identification |
|---|---|---|---|---|
| `IMOGEN-gmd-3-679-2010.pdf` | 1.74 MB | ✓ | ✓ | Huntingford et al. 2010 IMOGEN GMD paper — the reference IMOGEN paper. |
| `Common-directory/IMOGEN-codebase/docs/huntingford_et_al_10.pdf` | 1.74 MB | ✓ | ✓ | Same Huntingford 2010 paper, *duplicated* inside `IMOGEN-codebase/docs/`. Should be deduped in the unified codebase. |
| `Common-directory/IMOGEN-codebase/docs/huntingford_and_cox_00.pdf` | 2.08 MB | ✓ | ✓ | Huntingford & Cox 2000 IMOGEN-precursor paper (cited from the Intermediary_py TECHNICAL_MANUAL.md). |
| `Zelazowski_et_al_2018_Climate pattern-scaling set for an ensemble of 22 GCMs– adding uncertainty to the IMOGEN version 2.0 impact system.pdf` | 11.47 MB | ✓ | ✓ | Zelazowski et al. 2018 — the 22-GCM-pattern paper underpinning IMOGEN's pattern-scaling. |
| `gmd-11-541-2018.pdf` | 11.5 MB | – | ✓ | **B-only.** Same paper as above (Zelazowski 2018), GMD canonical filename. **Duplicate of the longer-named PDF.** |
| `Smith_2001_LPJ-GUESS – an ecosystem modelling framework - LPG-guess_software.pdf` | 655 KB | ✓ | ✓ | Smith 2001 LPJ-GUESS framework paper (note: the full paper is Smith et al. 2001 *Global Ecology and Biogeography*; what's in `References/` looks like an early/draft version with section structure). |
| `Lindeskog-al-Accounting_for_forest_management_in_the_estimation.pdf` | 10.92 MB | ✓ | ✓ | Lindeskog et al. forest-management paper. |
| `esd-6-745-2015_Olin.pdf` | 1.37 MB | ✓ | ✓ | Olin et al. 2015 ESD paper. (One of the two Olin 2015 papers cited in the working paper; the other Olin 2015b BG paper is not present.) |
| `Hayman-esd-12-513-2021.pdf` | 7.0 MB | ✓ | ✓ | Hayman et al. 2021 ESD paper on regional CH₄ mitigation with IMOGEN. |
| `gmd-11-2273-2018.pdf` and `gmd-11-2273-2018-1.pdf` | 3.73 MB each | ✓ | ✓ | Smith et al. 2018 FAIR v1.3 paper; **two byte-identical copies** in each version (the `-1.pdf` is a duplicate). Should be deduped. |
| `gmd-15-6709-2022.pdf` | 6.96 MB | – | ✓ | **B-only.** Martín Belda et al. 2022 *LPJ-GUESS/LSMv1.0: a next-generation land surface model with high ecological realism* — relevant for next-generation LPJ-GUESS / land-surface coupling. Not cited by the current working paper. |
| `gmd-18-1785-2025.pdf` | 7.32 MB | – | ✓ | **B-only.** Mathison et al. 2025 PRIME framework paper — *explicitly cited by the working paper* (§2.1.3: "follows the approach implemented in the PRIME framework (Mathison et al., 2025)"). Critical for understanding the FaIR-IMOGEN integration design. |
| `essd-16-2543-2024_GNB.pdf` | 24.79 MB | ✓ | ✓ | Tian et al. 2024 Global N₂O Budget — used for Component C N₂O comparator and for the dynamic N₂O sectoral proportion (working paper §2.3.2). |
| `essd-17-1873-2025_GMB.pdf` | 4.81 MB | ✓ | ✓ | Saunois et al. 2025 Global Methane Budget — used for Component C CH₄ comparator and for the IFW (+112) / DCC (−23) wetland corrections in Component B. |
| `essd-17-965-2025_GCB.pdf` | 12.98 MB | ✓ | ✓ | Friedlingstein et al. 2025 Global Carbon Budget — used for Component C CO₂ comparator (Table 7 partition). |
| `19R_V4_Ch05_Cropland.pdf` | 3.09 MB | ✓ | ✓ | IPCC 2019 Refinement Vol 4 Ch 5 — Cropland (rice CH₄ source). |
| `19R_V4_Ch10_Livestock.pdf` | 4.10 MB | ✓ | ✓ | IPCC 2019 Refinement Vol 4 Ch 10 — Livestock and Manure Management (enteric fermentation EF, MMS, AWMS). |
| `19R_V4_Ch11_Soils_N2O_CO2.pdf` | 1.43 MB | ✓ | ✓ | IPCC 2019 Refinement Vol 4 Ch 11 — N₂O from managed soils, EF₁/EF₂/EF₃/EF₄/EF₅. |
| `V4_07_Ch7_Wetlands.pdf` | 366 KB | ✓ | ✓ | IPCC Wetlands Supplement Ch 7. |
| `V4_p_Ap3_WetlandsCH4.pdf` | 196 KB | ✓ | ✓ | IPCC Wetlands Supplement Appendix 3 — CH₄. |
| `Wetlands_Supplement_Entire_Report.pdf` | 8.04 MB | ✓ | ✓ | Full Wetlands Supplement (large). |
| `WG1AR5_Chapter06_FINAL.pdf` | 24.36 MB | – | ✓ | **B-only.** IPCC AR5 WG1 Ch 6 Carbon and Other Biogeochemical Cycles — the source for the older `Brief Documentation of N2O Disaggregation Methodology` (Ciais et al. 2013). |
| `V2_1_Ch1_Introduction.pdf` | 876 KB | – | ✓ | **B-only.** IPCC 2006 Guidelines Vol 2 Ch 1 Introduction. Tier-1/2/3 conceptual definitions. |
| `Alexander et al 2017 Adaptation of global land use and management intensity to changes in climate and atmospheric carbon dioxide.pdf` | 15.80 MB | – | ✓ | **B-only.** Alexander et al. 2018 GCB paper (despite "2017" in filename), foundational PLUM v2 paper cited as `Alexander et al. 2018` in the working paper. |
| `Rabin et al 2020 Impacts of future agricultural change on ecosystem service indicators.pdf` | 4.33 MB | – | ✓ | **B-only.** Rabin et al. 2020 ESD paper — the foundational LandSyMM ecosystem-services paper. |

### 2.13 TIER 10 — Junk / temp / lock files

These should all be deleted in the unified codebase.

| Path | Size | Type |
|---|---|---|
| `version_A/.../References/~$broutines Defined in imogen.docx` | 162 B | Word lock file (open document marker). |
| `version_B/.../References/~$broutines Defined in imogen.docx` | 162 B | Same; B copy. |
| `version_B/.../References/~$issions Handling Methodology.docx` | 162 B | Word lock file. |
| `version_A/.../References/~WRL0536.tmp` | 15 556 B | Word temp save file (corrupted save buffer). |
| `version_B/.../References/~WRL0536.tmp` | 15 556 B | Same; B copy. |
| All `README.txt.txt` files | various | Windows double-extension artefact. Not strictly junk but should be normalised to `README.md` or `README.txt` during consolidation. |
| `Common-directory/LPJG_main/IMOGEN/README.txt.txt` | 0 B | Empty file. |
| `Imogen-controller/config.txt` | 38 B | Single-line "Future implementation of a config file" placeholder. |

---

## 3. Authoritative source-of-truth ranking by topic

For each topic, the docs are listed in **trust order**: top of each list
is the one to cite if there's any disagreement. *Do not cite docs ranked
lower as authoritative on the topic*.

### 3.1 Framework name, scope, scientific design intent

1. `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` (working paper draft).
2. `Intermediary_py/HANDOFF.md` and `TECHNICAL_MANUAL.md` (for the emissions-
   integration controller specifically; consistent with the working paper).
3. `LPJG_IMOGEN coupling docs.docx` — *only* for naming of input modules,
   `imogen_settings.txt` parameter list, and the C++ Intermediary modules
   (Extractor/Adder/Calculator/PLUM Data Preprocessor/Maps). Outdated for
   the framework name (uses "LPJG-IMOGEN", not "LandSyMM-IMOGEN").
4. Top-level `README.md` — same caveat as above; outdated for science.
5. `Imogen_paper_GMD.docx` — **do not cite** (user-flagged ignore).

### 3.2 Coupling protocol (year-by-year, done-marker, etc.)

1. `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` §2.4.2/§2.4.3 (annual
   system-boundary, monthly within-year, daily within-month; two-stage
   protocol).
2. `LPJG_IMOGEN coupling docs.docx` — for the operational mechanics of the
   done-marker file and the `imogen_lpjg.txt` state-machine file.
3. Top-level `README.md` — for the model-communication paragraph (done file).
4. `Imogen-controller/README.txt` — for the controller executable (`reset`,
   `move`).

### 3.3 IMOGEN configuration variables and Fortran subroutines

1. `Subroutines Defined in imogen.docx` — concise authoritative reference
   for the eight subroutines.
2. `LPJG_IMOGEN coupling docs.docx` — for the full `imogen_settings.txt` /
   `imogen_lpjg.txt` parameter listing with default values.
3. *Source code itself* (subagents 2-8 will need to confirm against
   `imogen_lpjg.f`).

### 3.4 IPCC Tier-1 emission factors and intermediary maps

1. `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` Appendix A (Tables
   A1–A14) — current-of-record parameter tables.
2. The IPCC 2019 Refinement PDFs (`19R_V4_Ch10_Livestock.pdf`,
   `19R_V4_Ch11_Soils_N2O_CO2.pdf`, `19R_V4_Ch05_Cropland.pdf`).
3. `IPCC_Maps_Reassessment_Validation.docx` — bug list and annotations on
   the C++ map implementation; useful for code audits.
4. `LPJG_IMOGEN coupling docs.docx` Maps section — same map listing but
   without the bug annotations; outdated relative to the reassessment.
5. `Reassessment of maps.docx` — outdated draft; do not cite.

### 3.5 Sector ownership, double-counting, and emission integration

1. `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` §2.4.4 (Table 8
   "Emissions ownership and residualisation rules").
2. `Intermediary_py/HANDOFF.md` §6 (specific integration recipes per gas).
3. `Intermediary_py/.../docs/methodology.md` and `component_C.md`.
4. `Emissions Handling Methodology.docx` (B-only) — for the SSP-scenario
   download / restructure / spline-harmonisation workflow.

### 3.6 Boundary harmonisation (1961, 2020)

1. `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` §2.3.1 (Backward
   Tapered Harmonisation, B = 10 yr for CO₂, 30 yr for CH₄/N₂O) +
   §2.3.4 (regression-based trend matching + 5-year centred MA).
2. `Emissions Handling Methodology.docx` (B-only) — spline-based
   harmonisation. **Possibly contradictory**: see §4 below.
3. `Intermediary_py/HANDOFF.md` — describes only segmented running-mean
   smoothing in Python plotting; the actual boundary harmonisation
   algebra is **not implemented in the Python pipeline**.

### 3.7 N₂O sectoral disaggregation

1. `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` §2.3.2 (Dynamic
   Temporal-Based Proportion via Tian 2024 GNB).
2. `Emissions Handling Methodology.docx` (B-only) §5 ("Estimation for N₂O
   … temporal dynamic proportioning based on the Global N₂O Budget").
3. `Brief Documentation of N2O Disaggregation Methodology.docx/.pdf`
   (Ciais 2013 / IPCC AR5 Ch6 Table 6.9) — **OUTDATED, do not cite**.

### 3.8 NEE / NBP definitions in `cflux.out`

1. `NEE-NBP Changes Report.docx/.pdf` (B-only). Authoritative formula:
   `NEE = flux_veg − flux_repr + flux_soil + flux_fire`;
   `c_disturb = flux_est + flux_seed + flux_charvest + acflux_wood_harvest
                + acflux_harvest_slow + acflux_clearing + acflux_landuse_change
                + c_org_leach_gridcell`;
   `NBP = NEE + c_disturb`.
2. `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` §2.2.6 — defines the
   biogenic CO₂ flux LPJ-GUESS provides; consistent with the corrected NEE
   above.
3. `Adding Net Biome Productivity Calculations to Technical Branch of LPJG
   v4.docx` — **OUTDATED** (incorrect formula).
4. The same incorrect formula in `LPJG_IMOGEN coupling docs.docx` —
   **OUTDATED** (the manual should be updated when consolidating).

### 3.9 Pasture fertilisation

1. `Pasture_Fert_Doc.docx` (and the same content embedded in
   `LPJG_IMOGEN coupling docs.docx`).
2. *Source code itself* (`management.cpp` / `management.h`).

### 3.10 LPJ-GUESS data ingestion (cell area, units, streaming)

1. `Intermediary_py/HANDOFF.md` §3 + `…/docs/component_B.md`. The exact
   formula `A(lat) = (0.5° × π/180)² × R² × cos(rad(lat))`,
   `R = 6.371 × 10⁶ m`, plus the `subprocess.Popen(['zcat', …])` streaming
   pattern and full unit-conversion pipeline per gas.
2. *Source code itself* (LPJ-GUESS `commonoutput.cpp`,
   `cflux.out`/`mch4.out`/`ngases.out` writers).

### 3.11 SSP–RCP scenarios

1. `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` §2.2.9 — SSP1-RCP2.6 +
   SSP2-RCP4.5.
2. `Intermediary_py/README.md` — all five (SSP1-2.6, SSP2-4.5, SSP3-7.0,
   SSP4-6.0, SSP5-8.5).
3. `Plots-Details.txt` — also reflects SSP1+SSP2 framing.
4. `Imogen_paper_GMD.docx` — SSP1+SSP5 (**outdated**).
5. `Intermediary/Code/config.txt` — SSP1+SSP5 + CMIP5 (**outdated**).

### 3.12 Validation / benchmarking thresholds

1. `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` §2.4.7 — ±15 % PBIAS;
   CO₂ RMSD ≤ 5 ppm, CH₄ ≤ 50 ppb, N₂O ≤ 5 ppb.
2. `Intermediary_py/HANDOFF.md` §4 — actual measured values per scenario
   and decade.

---

## 4. Contradictions and gaps

### 4.1 Contradictions confirmed

| # | Topic | Source A says … | Source B says … | Adjudication |
|---|---|---|---|---|
| 1 | NBP formula in `cflux.out` | Older `Adding NBP …docx` and embedded copy in `LPJG_IMOGEN coupling docs.docx` give a formula that *subtracts* `flux_fire`. | `NEE-NBP Changes Report.docx/.pdf` (B-only) gives a corrected formula that *adds* `flux_fire` and decomposes into `NEE + c_disturb`. | **B is correct**. The older docs should be retired or annotated as superseded. |
| 2 | N₂O sectoral disaggregation | `Brief Documentation of N2O Disaggregation Methodology.docx/.pdf` uses a *static* 59.81 % LPJG / 40.19 % non-LPJG split. | Working paper §2.3.2 + `Emissions Handling Methodology.docx` use a *dynamic temporal-based proportion* via Tian 2024 GNB. | **Working paper is correct**; the Brief Doc is OUTDATED. |
| 3 | SSP scenarios in scope | Older `Imogen_paper_GMD.docx`: SSP1 + SSP5. `Intermediary/Code/config.txt`: SSP1 + SSP5. | Working paper: SSP1 + SSP2. `Intermediary_py/README.md`: all five (capability) but evaluation focuses on SSP1+SSP2. | **Working paper is correct** for the unified evaluation; the Python pipeline retains the *capability* to do all five. |
| 4 | GCM choice | Older `Imogen_paper_GMD.docx`: IPSL-CM6-MR. | Working paper: ISIMIP-3b MRI-ESM2-0. | **Working paper is correct**. |
| 5 | Historical land-use forcing | Older `Imogen_paper_GMD.docx`: LUH2 (Hurtt 2011). | Working paper §2.4.5 + `Intermediary_py/HANDOFF.md`: HILDA+ v2 (Winkler 2021), with LUH2-style harmonisation as a *technique* (not LUH2 the data product). | **Working paper is correct**; LUH2 is the harmonisation methodology, HILDA+ v2 is the data. |
| 6 | Climate forcing in LPJ-GUESS Stage I | Top-level `README.md`: "LPJG handles its own spinup and historical data via netCDF files; IMOGEN provides scenario-year climate (2000-2100); pre-2000 is netCDF". | Working paper §2.4.3: Stage I LPJ-GUESS uses **prescribed ISIMIP-3b MRI-ESM2-0 climate for the entire 1850–2100** (not just historical), to produce potential yields. Stage II uses IMOGEN climate for the realised run. | **Working paper is correct**. The top-level README is a much earlier scoping. |
| 7 | Emission-time-series scope | Top-level `README.md`: "IMOGEN provides climate data for the scenario years (usually from 2000 to 2100)". | Working paper §2.3 + `Intermediary_py/HANDOFF.md`: emissions assembled 1850–2100 (paper) and 1900–2100 (Python pipeline) — i.e. scenario period ends at 2100 but historical+pre-industrial extends much earlier than 2000. | **Working paper is correct**. |
| 8 | Boundary harmonisation algorithm | Working paper §2.3.4: Backward Tapered Harmonisation + Regression Trend Matching + 5-yr centred MA. | `Emissions Handling Methodology.docx`: Univariate Spline ratio (modelled vs IIASA total). `Intermediary_py/HANDOFF.md`: segmented running-mean smoothing only, no boundary harmonisation algebra. | **Documentation-vs-code mismatch.** Both paper-described methods (taper + spline) appear absent from the actual Python pipeline. Subagents investigating the code need to confirm what is actually implemented; the paper may need to be updated, or the code extended. |
| 9 | Build environment | `LPJG_IMOGEN coupling docs.docx` and `Addressing Cross-Compiler Incompatibilities.docx`: Microsoft Visual Studio + MSVC for Windows + CMake on Linux. | User instruction: Linux-only project. | **User instruction takes precedence.** All Windows-specific build instructions should be retired in the unified codebase. |
| 10 | Wetland CH₄ data source | Older `Imogen_paper_GMD.docx`: GSW database max-water-extent (1984+2018 average), static. | Working paper §2.2.7: LPJ-WHyMe (Wania 2010) simulation **>40°N only**; tropical wetlands as IIASA residual. `Intermediary_py/HANDOFF.md`: LPJ-GUESS `mch4.out` + GMB IFW (+112 Mt) − GMB DCC (−23 Mt) corrections. | **Working paper is correct**. The GMB IFW/DCC corrections in the Python pipeline are an additional refinement consistent with §2.2.7. |
| 11 | Source of the term "Intermediary" | `LPJG_IMOGEN coupling docs.docx` uses "Intermediary" to describe a C++ codebase with Extractor, Adder, Calculator, PLUM Data Preprocessor, Maps modules. | Working paper §2.4.1 introduces the term "**Intermediary Controller (IC)**" as a dedicated workflow layer (i.e. the Python codebase). `Intermediary_py/` codebase implements the IC. | The C++ "Intermediary" is the legacy implementation; the Python "Intermediary Controller" is the current implementation. **The unified codebase should retire the C++ Intermediary** (other subagents will confirm what is still wired). |

### 4.2 Gaps in the documentation

The documentation does **not** authoritatively answer the following:

1. **What is the actual operational coupling at run time?** The `LPJG_IMOGEN
   coupling docs.docx` describes manual invocation (`make imogen`,
   `imogen.exe`, `automate_imogen.exe`) and a "planned bash script". The
   working paper describes the IC orchestration but does not specify how
   it is invoked end-to-end in the current code. It is unclear whether the
   IC actually exists today as a single orchestration script, or whether it
   is the Python pipeline (Components A-D) that is run separately and the
   resulting CSVs hand-fed into IMOGEN at run time.

2. **What is the actual code path that connects IMOGEN ↔ LPJ-GUESS in the
   Stage II coupled run?** Done-marker file synchronisation (`automate_imogen.exe`)
   is documented for the older C++ workflow; the working paper §2.4 mentions
   "annual system-boundary exchanges" but doesn't specify whether the done-
   marker mechanism is still in use, or whether IMOGEN and LPJ-GUESS exchange
   data through netCDF/binary files at run time (the older config files
   suggest this was the case).

3. **What is the actual harmonisation algorithm in the production code?**
   See contradiction #8 above.

4. **The exact list of LPJ-GUESS PFTs/CFTs/standtypes** used in the
   coupled runs is not in the documentation. The working paper §2.1.1
   names "C3 cereals, C4 cereals, rice, oil crops, pulses, starchy roots,
   monogastrics, ruminants" (PLUM commodity categories) and "winter and
   spring C3 cereals, C4 cereals, pulses, rice" (LPJ-GUESS CFTs in Stage I);
   `Projets_Completion_Plan_Blueprint.txt` adds an experimental oil-palm
   PFT. But the actual `.ins` instruction file content is not documented.

5. **The exact spin-up procedure** is described in two places with different
   detail. Working paper §2.4.3 says 500 yr at 1850–1900 climatology with
   pre-industrial CO₂ (~285 ppm). The older docs describe a more elaborate
   procedure with potential-yield setup runs vs main runs. **Inconsistency
   to flag**: the working paper is the authoritative target.

6. **Output products from coupled runs** — i.e. exactly which `.out` files
   are produced and how they are post-processed. The working paper §2.4.6
   names categories; `NEE-NBP Changes Report` documents `cflux.out` columns;
   the Python intermediary documents `mch4.out`/`ngases.out`/`cflux.out` for
   Component B input. But there is no central registry of all `.out` files
   the coupled framework writes (e.g. `anpp_pasture_st.out`, `seasonality.out`,
   etc.).

7. **Failure modes and known issues at run time** — the
   `LPJG_IMOGEN coupling docs.docx` has the section header "Troubleshooting
   and debugging" but it is empty. The Python `TECHNICAL_MANUAL.md` has
   §14 Troubleshooting and §15 Known Issues for the Python pipeline only.

8. **The provenance of GCM patterns** — the only documentation is
   `IMOGEN-codebase/patterns/readme.log` ("see also
   /pd/data/lpj/input_data/IMOGEN_patterns/CMIP5/patterns/"), pointing to
   a server-local store, and the `Zelazowski 2018` paper for the 22-GCM
   set. This is for *another subagent* to investigate.

9. **The exact Intermediary intermediary maps in the current code** — the
   `LPJG_IMOGEN coupling docs.docx` and `IPCC_Maps_Reassessment_Validation.docx`
   document the C++ maps; the Python pipeline implements equivalent
   mappings in `src/component_a_anthropogenic/`; but a side-by-side
   comparison of the C++ and Python mappings is not in any single document.

10. **The relationship between the "C++ Intermediary"
    (`Intermediary/Code/`) and the "Python Intermediary Controller"
    (`Intermediary_py/`)** — whether C++ is still wired into the
    coupled-run path, or fully retired in favour of Python. The working
    paper §2.4.1 mentions an "Intermediary Controller (IC)" without
    specifying the language; `Intermediary_py/HANDOFF.md` describes a
    self-contained Python pipeline; `Intermediary/Code/config.txt` still
    has `C:\GitHub\…` paths (likely fossil).

---

## 5. Recommendations for retirement / consolidation

For the unified codebase, my recommendations (read-only investigator: the
unification will be done by other subagents or the user). All file paths
below are relative to either `version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/`
or `version_B/...`.

### 5.1 DELETE (junk / lock files / Word temp files)

- All `~$*.docx` files (Word lock files): `~$broutines Defined in imogen.docx`
  in both A and B; `~$issions Handling Methodology.docx` in B.
- `~WRL0536.tmp` in both A and B.
- `Common-directory/LPJG_main/IMOGEN/README.txt.txt` (empty 0-byte file).
- `Imogen-controller/config.txt` ("Future implementation of a config file"
  placeholder).

### 5.2 RETIRE (move to `archive/` or delete; superseded)

- `Imogen_paper_GMD.docx` — superseded by
  `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx`.
- `Adding Net Biome Productivity Calculations to Technical Branch of LPJG
  v4.docx` — superseded by `NEE-NBP Changes Report.docx/.pdf` (B-only).
- `Brief Documentation of N2O Disaggregation Methodology.docx/.pdf` —
  superseded by working paper §2.3.2 + `Emissions Handling Methodology.docx`.
- `Reassessment of maps.docx` — superseded by
  `IPCC_Maps_Reassessment_Validation.docx`.
- `Intermediary/Code/config.txt` — Windows paths + CMIP5 settings; superseded
  by Python intermediary; reproduce as a *historical* note if needed.
- `LPJG Integration Work Overview and Updates[28-05-2024].docx` — older fork-
  integration notes; the user has flagged these as out-of-scope.
- `Ecosystems Modelling Project Update Report.pdf` — same.
- `Addressing Cross-Compiler Incompatibilities Between MSVC and GCC.docx/.pdf`
  — Linux-only project per user instruction.

### 5.3 DEDUPLICATE

- `gmd-11-2273-2018.pdf` and `gmd-11-2273-2018-1.pdf` — keep one.
- `Zelazowski_et_al_2018…pdf` and `gmd-11-541-2018.pdf` — same paper; keep one.
- `IMOGEN-gmd-3-679-2010.pdf` and `Common-directory/IMOGEN-codebase/docs/
  huntingford_et_al_10.pdf` — same paper; keep one (in the new
  `references/` directory).
- The triplicated `Intermediary_py/` (top-level vs `imogen_ghg_controller_FULL`
  vs `imogen_ghg_controller_SOURCE_ONLY`) — keep top-level only.
- The duplicated docx-coupled-content (e.g. NBP / Pasture Fert / Maps) that
  is *both* in `LPJG_IMOGEN coupling docs.docx` *and* in standalone docs.
  In the unified codebase, choose one canonical version (probably the
  standalone for ease of maintenance).

### 5.4 CONSOLIDATE / NORMALISE

- Normalise all `README.txt.txt` to `README.md` (or at least `README.txt`).
- Replace top-level `README.md` with a current-of-record version derived
  from the working paper §1+§2.1 (renamed to "LandSyMM-IMOGEN" instead of
  "LPJG-IMOGEN coupling setup"; corrected scope; explicit pointer to
  `Intermediary_py/` for the IC; explicit pointer to the working paper
  for the science).
- Update `LPJG_IMOGEN coupling docs.docx` to:
  - Drop the empty stub sections (`Troubleshooting`, `Case Studies`,
    `Future Developments`, `Glossary`).
  - Drop the Microsoft Visual Studio / MSVC / Windows-only sections.
  - Replace the old NBP formula with the corrected one from
    `NEE-NBP Changes Report`.
  - Replace the inline C++ Maps section with a pointer to either the C++
    code (if retained) or the Python `imogen_ghg_controller` (if the C++
    Intermediary is retired).
- Promote `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` to a
  top-level location (e.g. a `paper/` directory) so it is recognisable as
  the source-of-truth.
- Consolidate the two B-only docs `Plots-Details.txt` and
  `Projets_Completion_Plan_Blueprint.txt` into a single `TODO.md` or
  `paper_assets.md`.
- The `Intermediary_py/Quick_Start.md` should have its top 15-line chat
  excerpt removed.

### 5.5 KEEP AS-IS (authoritative)

- `IMOGEN-PAPER-GMD_updated_intro_methods-aa.docx` (working paper).
- `Intermediary_py/{README.md, HANDOFF.md, TECHNICAL_MANUAL.md,
  inputs_README.md}` and `…/docs/*.md`.
- `Subroutines Defined in imogen.docx`.
- `Pasture_Fert_Doc.docx`.
- `Emissions Handling Methodology.docx` (B-only).
- `NEE-NBP Changes Report.docx/.pdf` (B-only).
- `IPCC_Maps_Reassessment_Validation.docx`.
- All peer-reviewed PDFs (ground truth).

### 5.6 Add the B-only docs and PDFs to the unified codebase

Six "B-only" documents are the result of explicit content additions
(March/April 2026) and should be carried into the unified codebase: the
two B-only documents that supersede A material (`Emissions Handling
Methodology.docx`, `NEE-NBP Changes Report.docx/.pdf`), plus the two
B-only working notes (`Plots-Details.txt`, `Projets_Completion_Plan_
Blueprint.txt`), plus the four B-only PDFs that the working paper actually
cites or that the documentation needs (`gmd-15-6709-2022.pdf` Martín Belda
LPJ-GUESS/LSMv1; `gmd-18-1785-2025.pdf` Mathison PRIME — *cited by the
working paper*; `Alexander et al 2017 …pdf` Alexander 2018 — *cited by the
working paper*; `Rabin et al 2020 …pdf` Rabin 2020 — *cited by the
working paper*). The remaining B-only PDFs (`WG1AR5_Chapter06_FINAL.pdf`
and `V2_1_Ch1_Introduction.pdf`) are background references and can be
retained for context.

The `gmd-11-541-2018.pdf` is a duplicate of the longer-named Zelazowski
PDF; deduplicate.

---

## 6. Open questions the documentation does NOT answer

Compiling the gaps from §4.2 and adding subagent-relevant follow-ups:

1. **Is the C++ Intermediary still in the production run path?** The docs
   describe both a C++ Intermediary (with Extractor/Adder/Calculator/PLUM
   Preprocessor/Maps) and a Python intermediary controller. Subagent N
   investigating `Intermediary/` source code will need to confirm.

2. **Where exactly is the boundary-harmonisation algebra implemented?**
   The working paper §2.3.4 prescribes Backward Tapered Harmonisation +
   regression trend matching + centred MA. The Python pipeline appears
   not to implement these; it uses segmented running-mean smoothing only.
   Either the paper or the code is wrong.

3. **What is the actual coupling protocol used today?** Done-marker file
   (older docs), or netCDF exchange, or in-memory exchange via a single
   driver script? The `LPJG_IMOGEN coupling docs.docx` says "Plans are
   underway to develop a bash script that will automate the simultaneous
   execution of both models" — has that bash script been built?

4. **Has the LPJG `cflux.out` actually been updated** to match the
   corrected NEE/NBP formula? The doc says yes (`NEE-NBP Changes Report`),
   but a code-level audit is required.

5. **Are the C++ intermediary maps' missing values** (per the
   `IPCC_Maps_Reassessment_Validation.docx` annotations: missing `Buffalo`
   for Western Europe and Asia, missing values for Sheep/Goats/Poultry,
   missing region mappings for Pakistan & Afghanistan, Egypt, etc.) still
   present, or have they been fixed? If the C++ Intermediary is retired,
   this question becomes moot.

6. **What is the current state of the planned oil-palm PFT?** Documented
   in `Projets_Completion_Plan_Blueprint.txt` as a draft parameterisation
   awaiting test runs; not present in any current run setup.

7. **Where do the `IMOGEN-codebase/patterns/` files come from on the
   user's local system?** `readme.log` points to
   `/pd/data/lpj/input_data/IMOGEN_patterns/CMIP5/patterns/`, which is a
   server path. For the Linux workstation deployment (per Quick_Start.md),
   the patterns must be copied in.

8. **What is the actual scenario coverage of each LPJ-GUESS run-output
   `.gz` file** (which scenarios, which years, which forcing)?
   Documentation claims HILDA+v2 historical + PLUMv2 SSP-RCP scenarios;
   investigators of the data files (other subagents) will need to confirm.

9. **Are the SSP-RCP "126" and "245" labels in `Plots-Details.txt`
   shorthand for SSP1-RCP2.6 and SSP2-RCP4.5 only, or are SSP3+SSP4+SSP5
   also part of the planned figures?**

10. **What is the relationship between the `Common-directory/LPJG_main/`
    files (e.g. `imogen_lpjg.txt`, `imogen_lpjg_flux.txt`,
    `extended_lpjg_only_cfluxrcp26.txt`, `lpjg_only_cfluxrcp26.txt`) and
    the working paper's emissions-integration?** The directory structure
    suggests the older C++ Intermediary writes/reads these files at run
    time; this is for other subagents to verify.

11. **Why are there `gridlist_*.txt` files at every Integration test
    directory?** Documentation does not explain whether these are
    test-specific (covering specific Germany/Hurtt random grids) or
    canonical. Other subagents investigating run setups will need to
    confirm.

12. **What is the role of `IMOGENCXX/`?** No README; not mentioned in any
    of the docs I read. May be a C++ port of the IMOGEN Fortran code.
    Subagents investigating source code will need to confirm.

13. **What is `FastRegrid/` vs `Regrid/` vs `RegridLPJG/`?** Three
    differently-named regridding directories with no top-level docs. Out
    of scope for this subagent (other subagents handle it).

14. **What is `NdepFastArchive/`?** Likely contains the SimfireInput.bin /
    fast-archive Ndep that LPJ-GUESS 4.1 needs (per `releasenotes.txt`).
    No README.

---

End of report.
