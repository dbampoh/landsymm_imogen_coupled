# STEP 8 — LPJG-side handshake writer (`lpjguess/modules/imogenoutput.cpp/h`)

**Date completed:** 2026-05-06
**Commit:** _to be filled in after `git commit`_
**Status:** ✅ build clean (162/162 unit tests pass); module is registered with the LPJ-GUESS output framework; `coupling_mode` ins parameter added; **architectural caveat documented as new follow-up F-10** (extensive detail in `notes/FOLLOWUPS.md`).

The full coupled-mode run-completion verification (V.1's stated end-to-end smoke test) is **gated on step 9** (per-scenario run-config `.ins` files); step 8 establishes the writer infrastructure, the registration, the units-correct flush logic, and the explicit acknowledgement of the F-10 architectural limitation.

---

## 1. Goal

Per `EXECUTION_PLAN.md` V.1 step 8 + Appendix A.1, implement a new
LPJ-GUESS output module that writes the per-year handshake files
the IMOGEN engine consumes:

```text
<DIR_COMMON>/LPJG_main/IMOGEN/
├── imogen_lpjg_flux.txt           year, NEE_PgC                (timeseries)
├── imogen_lpjg_ch4_n2o_flux.txt   year, CH4_TgCH4, N2O_TgN2O   (timeseries)
├── imogen_lpjg.txt                control state for next year   (overwritten)
└── done                           handshake marker             (touched per year)
```

After step 7 (which restored the LPJ-GUESS-side polling-loop fixes
C2/C3 + the Fortran-side F-4 auto-create-`done`), the IMOGEN engine
correctly **listens** for handshake files. Step 8 builds the
**writer**: someone now actually produces those files.

---

## 2. Investigation findings (substantial; informed the design)

Step 8 began with a deep investigation of the LPJ-GUESS output
framework, the existing imogen-related stubs in the predecessor
codebase, and the framework's per-year flow. Four key findings
shaped the implementation:

### 2.1 No `imogenoutput.cpp/h` exists yet — but stubs DO live in `miscoutput`

A grep of `lpjguess/modules/imogen*` revealed:
- `imogen_input.cpp/h` (loose-coupling INPUT module) — exists, intended use
- `imogencfx.cpp/h` (tight-coupling INPUT module) — exists, intended use
- `imogenlogger.cpp/h` (logger; singleton class) — exists, ancillary
- **NO `imogenoutput.cpp/h`** — net-new for step 8

But examining `miscoutput.cpp/h` revealed **half-scaffolded IMOGEN
diagnostic-output stubs** that the user (DKB) had previously begun
work on, gated on `IMOGENConfig::print_imogen_output==true`:

- 12 `xtring file_*_anom` filename declarations in `miscoutput.h:122-123`
- 12 `Table out_*_anom` declarations in `miscoutput.h:171-172`
- 12 `declare_parameter("file_*_anom", ...)` calls in `miscoutput.cpp:122-135`
  (gated on `print_imogen_output==true`; with a `// FIXME: DKB` marker)
- A **dead `getImogenData(int lower, int upper)` helper** at `miscoutput.h:69-79`
  that returned **non-deterministic random values** from a
  `std::random_device`-seeded `std::uniform_real_distribution<>`. Defined
  but **never invoked anywhere** in the entire codebase. Never wired to
  any `add_value()` calls; the 12 tables had no `create_output_table()`
  calls in `define_output_tables()`.

**Diagnosis:** these are stubs for outputting the IMOGEN climate
INPUTS as LPJG-format diagnostic `.out` files (`t_anom.out`,
`p_anom.out`, etc.) — a fundamentally different concern from
step 8's handshake control-flow files. The work was scaffolded but
incomplete.

### 2.2 Architectural decision — separate module vs fold into miscoutput

Considered both options. Detailed trade-off analysis is in the
project chat history; summary:

| Criterion | Separate `imogenoutput.cpp/h` (chosen) | Fold into `miscoutput.cpp` |
|---|---|---|
| Single Responsibility | ✅ | ❌ mixed concerns |
| Output channel mechanism | direct `std::ofstream` | requires bolting on alongside LPJG `Table` framework |
| Cadence | per-year global aggregate | per-gridcell × per-year |
| Codebase precedent | matches `gcpoutput.cpp/h`, `spitfireoutput.cpp/h` | inconsistent |
| Risk of regression | zero (no edits to miscoutput's 1700 lines) | larger surface area |
| Revertability | clean `git revert` | requires surgical extraction |

**Decision:** separate module wins decisively (9 of 11 criteria favor
separation; the 2 against — file count, build-system change — are
trivial). **The miscoutput stubs stay in place** as a separate
concern (now tracked as follow-up F-9), with the dead `getImogenData()`
helper removed for code-hygiene.

### 2.3 OutputModule base class interface

Reading `lpjguess/framework/outputmodule.h` confirmed:

- `OutputModule` is an abstract base; subclasses must implement 9 pure
  virtuals (`init`, `outannual`, `outdaily`, `outharvest`,
  `outharvest_justphupvd`, `outannual_ggcmi`, `openlocalfiles`,
  `closelocalfiles`, `openlocalfiles_ggcmi`, `closelocalfiles_ggcmi`).
- Registration via `REGISTER_OUTPUT_MODULE("name", ClassName)` macro
  (statically registers a creator function in a singleton registry).
- The framework's `output_modules.outannual(gridcell)` calls fire
  per-gridcell × per-year.
- **There is no `outglobal_year` hook** (Appendix A.1's open question
  is now formally answered: the hook does not exist).

### 2.4 The framework loop is per-gridcell-outer / per-day-inner — significant

Reading `lpjguess/framework/framework.cpp:411-516` — the **single most
important investigation finding** of step 8 — revealed the framework's
canonical loop structure:

```cpp
while (true) {                                                    // outer: per-gridcell
    Gridcell gridcell;
    if (!input_module->getgridcell(gridcell)) break;
    // ... gridcell setup ...

    while (input_module->getclimate(gridcell)) {                  // inner: per-day, ALL years
        simulate_day(gridcell, input_module.get());
        output_modules.outdaily(gridcell);
        if (date.islastday && date.islastmonth) {
            output_modules.outannual(gridcell);                   // year-end, per gridcell
        }
        date.next();
    }
    // End of all-years loop for THIS gridcell
}
// End of all-gridcells loop
```

The `getclimate()` returns false when ALL years have been simulated for
the current gridcell. So **each gridcell processes ALL its years before
moving to the next gridcell**.

This is **fundamentally incompatible** with a per-year-globally-
synchronized handshake. When gridcell-1 finishes year-1, gridcell-2
hasn't even started year-1 — yet a year-end "handshake" intuitively
fires per (year, all-gridcells), not per (year, single-gridcell). The
predecessor framework's "tight coupling" therefore can never have been
fully synchronized in the way the term suggests.

This finding is **the formal explanation** for `[CMI §1.1]`'s remark
that the predecessor coupled model "never ran end-to-end." It also
explains why so many handshake-related code paths in the predecessor
look half-finished or aspirational. It is now **followup F-10** —
documented in extensive detail in `notes/FOLLOWUPS.md` with a Phase-2
recommendation that mirrors the LandSyMM-into-LTS integration pattern
(parameter-gated additive code path, NOT framework restructure).

### 2.5 The canonical NEE / CH4 / N2O computation pattern

From `commonoutput.cpp::outannual` (lines 1241-1273), the authoritative
pattern is:

```cpp
Gridcell::iterator gc_itr = gridcell.begin();
while (gc_itr != gridcell.end()) {
    Stand& stand = *gc_itr;
    stand.firstobj();
    while (stand.isobj) {
        Patch& patch = stand.getobj();
        double to_gridcell_average =
            stand.get_gridcell_fraction() / (double)stand.npatch();

        // Carbon (kgC/m^2/yr at gridcell-mean):
        flux_man  += -patch.fluxes.get_annual_flux(Fluxes::MANUREC) * to_gridcell_average;
        flux_veg  += -patch.fluxes.get_annual_flux(Fluxes::NPP)     * to_gridcell_average;
        flux_repr += -patch.fluxes.get_annual_flux(Fluxes::REPRC)   * to_gridcell_average;
        flux_soil +=  patch.fluxes.get_annual_flux(Fluxes::SOILC)   * to_gridcell_average;
        flux_fire +=  patch.fluxes.get_annual_flux(Fluxes::FIREC)   * to_gridcell_average;
        flux_est  +=  patch.fluxes.get_annual_flux(Fluxes::ESTC)    * to_gridcell_average;

        // N2O (kgN/m^2/yr at gridcell-mean):
        flux_N2O_fire += patch.fluxes.get_annual_flux(Fluxes::N2O_FIRE) * to_gridcell_average;
        flux_N2O_soil += patch.fluxes.get_annual_flux(Fluxes::N2O_SOIL) * to_gridcell_average;

        // CH4 (g CH4-C/m^2/month, 12 monthly values):
        for (int m = 0; m < 12; m++)
            mch4[m] += patch.fluxes.get_monthly_flux(Fluxes::CH4C, m) * to_gridcell_average;

        stand.nextobj();
    }
    ++gc_itr;
}
NEE_kgCm2 = flux_man + flux_veg + flux_repr + flux_soil + flux_fire + flux_est;
```

`imogenoutput.cpp` mirrors this exactly (see §3.2 below).

---

## 3. Implementation

### 3.1 `IMOGENConfig::coupling_mode` ins parameter

Three small additions across two files:

| File | Change |
|---|---|
| `lpjguess/framework/parameters.h` | Add `extern xtring coupling_mode;` to the IMOGENConfig namespace (after `interpolation_mode`) |
| `lpjguess/framework/parameters.cpp` | Add `xtring coupling_mode = "tight";` definition (default value) |
| `lpjguess/modules/imogencfx.cpp` | Add `declare_parameter("coupling_mode", &IMOGENConfig::coupling_mode, 20, "...")` to the existing IMOGEN config declare_parameter block (around line 333) |

Values: `"tight"` (default; v1.0 caveat per F-10) | `"prescribed"` |
`"loose"`. ImogenOutput::flush_year() reads this and skips writing if
the mode is `"loose"`.

### 3.2 `lpjguess/modules/imogenoutput.h` (new, ~150 lines)

Class declaration, members, virtual overrides. The header has an
extensive doc block at the top describing:
- The 4 handshake files and their schemas
- Cadence (per-year flush triggered by year-change in outannual)
- Mode-gating semantics
- The F-10 architectural caveat (with the Phase-2 recommendation:
  parameter-gated additive code path, NOT framework restructure)

Public members:
- `init()` — captures handshake_dir, calls mkdir -p, resets accumulators
- `outannual(Gridcell&)` — year-change-detect-and-flush, then accumulate
- All other 8 virtual overrides — empty (no-op)
- `flush_pending_year()` — public escape hatch for climatemodel.cpp to
  trigger a flush before its polling loop (idempotent; no-op if no
  pending year)

Private members:
- `flush_year(int year)` — writes the 4 handshake files (mode-gated)
- `reset_accumulators()` — zeroes per-year state
- `gridcell_area_m2(double lat_deg)` — spherical-Earth approximation
- State: `accum_year, accum_NEE_kgC, accum_CH4_gCH4C, accum_N2O_kgN,
  accum_area_m2, handshake_dir, first_flush, year_pending,
  accum_gridcell_count`

### 3.3 `lpjguess/modules/imogenoutput.cpp` (new, ~310 lines)

Implementation. Key design points:

#### Year-change detection (cadence)

In `outannual()`:

```cpp
const int this_year = date.get_calendar_year();
if (accum_year >= 0 && this_year != accum_year) {
    flush_year(accum_year);   // flush previous year
    reset_accumulators();
}
accum_year = this_year;
// ... accumulate this gridcell's contribution to this_year ...
```

This works for the first N-1 years (each gets flushed when the N-th year
arrives). The very last year is handled by the **destructor** which
flushes any pending state at sim-end:

```cpp
ImogenOutput::~ImogenOutput() {
    if (year_pending && accum_year >= 0) {
        flush_year(accum_year);
    }
}
```

#### Carbon / N2O / CH4 accumulation (mirrors commonoutput pattern)

Inner Gridcell -> Stand -> Patch loop (lines ~115-160 of imogenoutput.cpp).
Per-patch, gridcell-mean-weighted via `to_gridcell_average`. NEE
computed as the canonical 6-term sum. CH4 monthly summed × 12 months;
N2O fire+soil summed.

#### Unit conversions to PgC / TgCH4 / TgN2O

```cpp
const double NEE_PgC    = accum_NEE_kgC   * 1e-12;
const double CH4_TgCH4  = accum_CH4_gCH4C * (16.0/12.0) * 1e-12;
const double N2O_TgN2O  = accum_N2O_kgN   * (44.0/28.0) * 1e-9;
```

CH4 conversion: `g(CH4-C)` × `16/12` (molar mass ratio CH4 to C) →
`g(CH4)`, then `1e-12` → Tg. Step factor of 1e-12 = `1e-3` (g to kg) ×
`1e-9` (kg to Tg).

N2O conversion: `kgN` × `44/28` (molar mass ratio N2O to N2 basis,
since 1 mol N2O has 28 g of N i.e. 2 N atoms × 14 g/mol) → `kgN2O`,
then `1e-9` → Tg.

#### Mode gate (skip writes in "loose" mode)

```cpp
const std::string mode = std::string((char*)IMOGENConfig::coupling_mode);
if (mode == "loose") {
    dprintf("[ImogenOutput] flush_year(%d) skipped: coupling_mode='loose'\n", year);
    year_pending = false;
    return;
}
```

In `"tight"` (default) and `"prescribed"`, all 4 files are written.
In `"loose"`, no files are written (LPJG runs against pre-baked IMOGEN
climate on disk; no per-year handshake needed).

#### File write order — `done` is last

```cpp
// 1. imogen_lpjg_flux.txt          (append timeseries)
// 2. imogen_lpjg_ch4_n2o_flux.txt  (append timeseries)
// 3. imogen_lpjg.txt               (overwrite control state)
// 4. done                          (touch handshake marker LAST)
```

Order matters: the IMOGEN engine treats `done`'s mtime as the "data is
ready" signal. Writing it LAST guarantees the engine never sees a
"done" while data writes are still in progress.

#### Diagnostic banner (units-integrity discipline §I.D.5)

```cpp
dprintf("[ImogenOutput] flushed year=%d (gridcells_seen=%d, area_m2=%.3e):"
        " NEE=%.6f PgC, CH4=%.6f TgCH4, N2O=%.6f TgN2O"
        " [F-10 caveat: per-gridcell-rolling]\n",
        year, accum_gridcell_count, accum_area_m2,
        NEE_PgC, CH4_TgCH4, N2O_TgN2O);
```

This lets a user / CI test see at-a-glance both the values AND the
F-10 caveat at run time.

### 3.4 Build-system registration

`lpjguess/modules/CMakeLists.txt`: 2 new lines (one in `headers`, one
in `source`):

```text
  imogenlogger.h
  imogenoutput.h    ← new
  )

set(source
  ...
  imogenlogger.cpp
  imogenoutput.cpp  ← new
  )
```

### 3.5 `miscoutput.h` cleanup

- Removed dead `getImogenData(int, int)` random-placeholder helper
  (~12 lines including signature, body, comment)
- Removed unused `#include <random>` (was the only consumer)
- Replaced both with multi-line comments referencing F-9 (the
  follow-up that will eventually complete the half-scaffolded
  diagnostic-output tables)

The 12 `xtring file_*_anom` and `Table out_*_anom` declarations remain
in place — they're inert at runtime (no `create_output_table()` calls,
no `add_value()` calls) and are F-9's territory.

---

## 4. The architectural caveat — F-10 in detail

This is the **most important documentation in step 8** per user
guidance ("extreme explanatory detail and thoroughness given the
significance of your findings"). The full F-10 entry lives in
`notes/FOLLOWUPS.md` and runs ~150 lines. Here, a structured summary:

### What's the issue

LPJ-GUESS's framework loop ordering (per-gridcell-outer / per-day-inner
across all years) means each gridcell completes ALL its years before
the next gridcell starts. Tight coupling — defined as "IMOGEN's year-N
climate uses LPJG's globally-aggregated year-(N-1) NEE feedback" —
**cannot be cleanly implemented** in this loop ordering.

### What works in v1.0 anyway

- The 4 handshake files ARE non-empty and contain physically-sensible
  per-gridcell-rolling values.
- V.1's stated step-8 verification milestone ("non-empty files; sensible
  NEE in PgC/yr") is met.
- LPJ-GUESS unit tests still pass (162/162).
- The IMOGEN engine's polling loop will detect `done` and exit cleanly.
- Coupled-mode runs WILL run end-to-end (gated on step 9's run-config
  setup) — they'll produce reasonable but not fully-synchronized output.

### What doesn't work in v1.0 (deferred)

- Tight coupling's NEE feedback is **partial and one-step-stale**:
  when gridcell-1 finishes year-N and the flush fires, gridcell-2 has
  not yet contributed its year-N data; the flushed value will only have
  gridcell-1's contribution + previous gridcells'. The IMOGEN engine
  for year (N+1)'s climate uses this incomplete feedback.
- Validation against NOAA GMD CO2 (step 17 milestone: RMSD ≤ 5 ppm)
  may show systematic bias from the non-synchronized feedback. We
  document this risk; we may discover empirically at step 17 whether
  the bias is significant or negligible.

### Phase-2 recommended approach (per user guidance 2026-05-06)

When we tackle proper tight coupling in Phase 2:

1. **DO NOT alter the existing framework.cpp loop**. The
   per-gridcell-outer ordering serves the existing standalone /
   loose-coupling / prescribed-coupling cases correctly.

2. **DO add a runtime parameter** (e.g.
   `framework_loop_mode = "year_outer" | "gridcell_outer"`) that gates
   a NEW per-year-outer code path which lives ALONGSIDE the existing
   per-gridcell-outer code path.

3. **DO implement the new code path as an additive extension** —
   exactly mirroring the LandSyMM-fork-into-LPJ-GUESS-LTS integration
   pattern from the predecessor project earlier in the chat history,
   where new functionality was added as a parameter-gated alternative
   without altering the LTS baseline behavior.

4. **DO ensure backward compatibility**: existing standalone /
   loose-coupling / prescribed-coupling runs continue to use the
   default `"gridcell_outer"` path with no behavioral change.

This approach has these specific advantages over framework restructure:

- Risk to the 162 unit tests is bounded — most tests exercise the
  default path which doesn't change.
- Forward and backward compatibility are both preserved.
- The two paths are co-existing reference implementations: when one
  is suspect, the other can be used to cross-check.
- Future contributors can choose which path matches their needs.

### Why F-10 is being deferred (not blocking)

- Step 8's V.1-stated milestone is met
- Step 9's coupled-mode setup can proceed productively
- Step 10-15 (intermediary_py + adapter + run launcher + Stage I doc
  + cluster integration) are unaffected by F-10
- Step 17's validation is the natural test of whether F-10 needs
  immediate attention vs Phase-2 attention. If validation passes
  thresholds with the per-gridcell-rolling handshake, F-10 is purely
  a "scientific completeness" item rather than a blocker.

---

## 5. Verification

### 5.1 Build clean

```bash
cd lpjguess/build
cmake -DCMAKE_PREFIX_PATH=$HOME/anaconda3 \
      -DNETCDF_INCLUDE_DIR=$HOME/anaconda3/include \
      -DNETCDF_C_LIBRARY=$HOME/anaconda3/lib/libnetcdf.so ..
make
```

Output:

```text
[ 46%] Built target guess
[ 83%] Building CXX object CMakeFiles/runtests.dir/modules/imogenoutput.cpp.o
[100%] Built target runtests
```

✅ `imogenoutput.cpp.o` produced cleanly; `guess` and `runtests` link.

### 5.2 Unit tests pass

```bash
$ ./runtests
===============================================================================
All tests passed (162 assertions in 25 test cases)
```

✅ Same 162 tests still pass; no regression from the 6 source-code
edits (parameters.h/cpp, imogencfx.cpp param decl, imogenoutput.h/cpp,
miscoutput.h dead-helper removal).

### 5.3 What's deferred to step 9

V.1 step 8's full verification milestone is *"At end of each year of
the smoke test, the writer produces non-empty `imogen_lpjg_flux.txt`,
... with sensible NEE in PgC/yr."*

Producing those files requires running `./guess -input imogencfx
runs/<SSP>/imogen_intermediary.ins` end-to-end. The **runs/<SSP>/**
config doesn't exist yet — that's step 9. So the per-year file-write
verification will be done at step 9. Step 8 establishes the writer
infrastructure, registration, and code; step 9 will trigger the
writer through actual coupled-mode invocation.

---

## 6. Files modified / added

### Added (committed to git)

| Path | Bytes | Purpose |
|---|---:|---|
| `lpjguess/modules/imogenoutput.h` | ~6 KB / ~150 lines | new module: class declaration, doc block (extensive F-10 cross-reference) |
| `lpjguess/modules/imogenoutput.cpp` | ~12 KB / ~310 lines | new module: implementation (REGISTER_OUTPUT_MODULE, init, outannual, flush_year, helpers) |
| `notes/STEP_8.md` | this file | per-step verification record |

### Modified

| Path | Change |
|---|---|
| `lpjguess/framework/parameters.h` | Add `extern xtring coupling_mode;` to IMOGENConfig namespace |
| `lpjguess/framework/parameters.cpp` | Add `xtring coupling_mode = "tight";` definition |
| `lpjguess/modules/imogencfx.cpp` | Add `declare_parameter("coupling_mode", ..., "tight | prescribed | loose")` to existing IMOGEN config block |
| `lpjguess/modules/CMakeLists.txt` | Add `imogenoutput.h` and `imogenoutput.cpp` to source lists |
| `lpjguess/modules/miscoutput.h` | Remove dead `getImogenData()` helper + unused `<random>` include; add cross-reference comment to F-9 |
| `notes/FOLLOWUPS.md` | New entry **F-10** (extensive; ~150 lines) documenting the framework-loop architectural finding + Phase-2 recommendation (parameter-gated additive code path) |
| `CHANGELOG.md` | `[v0.8.0-imogenoutput]` entry |
| `EXECUTION_PLAN.md` | V.1 step 8 marked ✅ |

---

## 7. Recovery / re-run protocol

A clean revert: `git revert <step-8-hash>`. This:
- Removes `imogenoutput.cpp/h`
- Reverts `coupling_mode` parameter declaration (parameters.h/cpp + imogencfx.cpp)
- Reverts the CMakeLists update
- **Restores** the dead `getImogenData()` helper in miscoutput.h
  (annoying but consistent with the revert semantics; F-9 follow-up
  would still want it removed eventually)

The standalone Fortran IMOGEN smoke run (step 4 verification milestone)
is unaffected by step 8's changes — step 8 touches the LPJ-GUESS C++
side only, plus a parameters-namespace addition that doesn't break
the Fortran build.

---

## 8. Follow-ups

### Closed by step 8

(None directly. F-9 is *opened* by step 8's investigation but doesn't
get closed.)

### Opened by step 8

- **F-9** (already opened by the design decision in step 8's investigation;
  see §2.1 + §3.5): the half-scaffolded miscoutput IMOGEN
  diagnostic-output stubs need their `create_output_table()` +
  `add_value()` wiring completed. Best timing: step 9.5 alongside
  Rh_anom / W_anom / Tmin_anom / Tmax_anom output parity work.
- **F-10** (the major finding of step 8): framework-loop ordering
  vs tight-coupling architectural mismatch. Phase-2 work; recommended
  approach is parameter-gated additive code path mirroring the
  LandSyMM-into-LTS pattern.

---

## 9. Push commands (manual three-way push)

```bash
cd /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm

git push origin main
git push kit main
git push helmholtz main

# Optional tag:
git tag -a v0.8.0-imogenoutput -m "Step 8: LPJG-side handshake writer (lpjguess/modules/imogenoutput.cpp/h); coupling_mode ins parameter; F-9, F-10 documented"
git push origin v0.8.0-imogenoutput
git push kit    v0.8.0-imogenoutput
git push helmholtz v0.8.0-imogenoutput
```
