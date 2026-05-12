# STEP 17c — F-12 sub-milestone C3 (HPC cluster integration tests on KIT IMK-IFU `owl`)

**Date opened:** 2026-05-12 (session 3)

**Date 17c.0 PREP B15+B16 forensic record landed:** 2026-05-12 (this commit; un-tagged checkpoint)

**Date 17c.0 PREP B15 fix + signal-of-life assertion landed:** _pending_

**Date 17c.0 PREP four-xval re-verification (year_outer actually exercised):** _pending_

**Date 17c.0 PREP B16 forensic + fix landed:** _pending_ (gated on B15 landing first)

**Date 17c.0 PREP workstation `mpirun -np 4` mimic verified (deferred-from-C2 obligation):** _pending_

**Date 17c.0 PREP C2 close-out tag annotation amendment (if any):** _pending_ (deferred until post-fix re-verification clarifies whether `f6c192e` substantively passes year_outer xval)

**Date 17c.1 → 17c.4 cluster phases:** _pending_

**Date C3 close-out tag `v0.18.0-step17c-c3-cluster-tight`:** _pending_

**Status:** 🔧 IN PROGRESS — Step 17c entered the forensic root-cause stage instead of going directly to the workstation `mpirun -np 4` mimic. Reason: a session-3 onboarding audit of the C2 close-out tag `v0.17.5-step17b-c2-mpi-sync` at `f6c192e` revealed that **all four C1 + C2 cross-validation passes silently never executed the `year_outer` code path** (audit item **B15**, root-caused 2026-05-12 session 3 morning–afternoon). A second, downstream-of-B15 latent defect was also identified (audit item **B16**, an eager cache-fullness check in `preload_all_climate` that mis-models a cumulative cache as per-cell). This commit lands the **B15 forensic + B16 acknowledgement** (forensic-only; ZERO `lpjguess/` source change). Subsequent commits will land the B15 fix + harness signal-of-life assertion + four-xval re-verification, then the B16 forensic + fix, then the deferred-from-C2 `mpirun -np 4` mimic, then the cluster phases.

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
- [§1. 17c.0 PREP phase plan (revised post-B15 forensic)](#1-17c0-prep-phase-plan-revised-post-b15-forensic) _(skeleton; populated as PREP sub-phases land)_
- [§2 onwards — 17c.1 through 17c.4 cluster phases](#2-onwards--17c1-through-17c4-cluster-phases) _(skeleton; populated when reached)_

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

## 1. 17c.0 PREP phase plan (revised post-B15 forensic)

_(Skeleton only at this commit; will be populated as PREP sub-phases land.)_

The 17c.0 PREP phase as originally planned (per session-3 handoff §0.4 → 5-phase plan item 1) was a single workstation `mpirun -np 4` mimic verification, fulfilling the deferred-from-C2 obligation. The B15 forensic surfaced two prerequisites that must land first. The revised PREP phase plan:
| Sub-phase | Scope | Estimated effort | Status |
|---|---|---|---|
| 17c.0.0 | **B15 + B16 forensic record (this commit).** Doc-only; ZERO source change. | 0.5 d (actual) | ✅ DONE 2026-05-12 |
| 17c.0.1 | **B15 fix + signal-of-life assertion (F1-F4 from §0.8).** Three .ins/.sh changes + harness assertion. ZERO C++ source change. Plus optional F5 (runtime diagnostic ~3 LOC C++) if user authorises. | 0.5-1 d | ⏳ NEXT |
| 17c.0.2 | **Four-xval re-verification on B15-fixed HEAD.** First time year_outer actually exercised. 1cell scenarios should pass cleanly; 4cell scenarios may surface B16. | 0.5 d | ⏳ pending |
| 17c.0.3 | **B16 forensic + fix.** Eager-cache-check removal in `preload_all_climate` (both modules). Full forensic write-up as §3 of this file. | 0.5-1 d | ⏳ pending (gated on 17c.0.2 surfacing the failure mode on 4cell) |
| 17c.0.4 | **Four-xval re-verification on B15+B16-fixed HEAD.** All four scenarios should pass cleanly with year_outer exercised. | 0.5 d | ⏳ pending |
| 17c.0.5 | **C2 close-out tag annotation amendment decision (option a/b/c from §0.11).** Errata note OR re-tag based on 17c.0.4 evidence. | 0.2 d | ⏳ pending |
| 17c.0.6 | **Workstation `mpirun -np 4` mimic verification** (the original PREP obligation). Adapts `scripts/run_parallel_mimic.sh` to support `coupling_mode "prescribed"` + `imogencfx` tight-mode variant for proper C2-core exercise. | 1 d | ⏳ pending |
| 17c.0.7 | **PREP phase close-out.** Doc cascade + (un-tagged) checkpoint commit on top of the cascade. | 0.2 d | ⏳ pending |
Total revised PREP estimate: ~3.5-5 d (was: ~0.5-1 d for `mpirun -np 4` only). The B15+B16 surface adds ~3 d of necessary work but produces durable artefacts (rule #8 + the signal-of-life assertion + the cumulative-cache documentation) that will benefit every future code-path-gated cross-validation.

---

## 2 onwards — 17c.1 through 17c.4 cluster phases

_(Skeleton only at this commit; will be populated when reached.)_

| Phase | Scope (per session-3 handoff §0.4) |
|---|---|
| 17c.1 | `env_owl.sh` refinement against actual `module avail` output on owl |
| 17c.2 | Cluster MPI build via `make_guess.sh --mpi` against module-loaded NetCDF/HDF5/openmpi |
| 17c.3 | Cluster small smoke (4 ranks × 480-cell × 5-yr tight); xval-style match against workstation MPI mimic baseline |
| 17c.4 | Cluster production smoke (16 ranks × ~4 000-cell × 11-yr SSP1-2.6); validation against working-paper §2.5 thresholds |
| 17c.5 | C3 close-out tag `v0.18.0-step17c-c3-cluster-tight` |
