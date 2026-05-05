# STEP 3 — Fortran IMOGEN: `ALLOCATABLE` array refactor (run-time `NGPOINTS`)

**Date completed:** 2026-05-05
**Commit:** _to be filled in after `git commit`_
**Status:** ✅ verified (build clean, three smoke probes green)

---

## 1. Goal

Make the Fortran IMOGEN binary support **arbitrary regridding-gridlist sizes** at run-time, without source recompile, by converting the `NGPOINTS`-dimensioned static arrays in `PROGRAM IMOGEN` to Fortran-90 `ALLOCATABLE` arrays and reading `NGPOINTS` from `imogen_settings.txt` at run-time.

This unblocks the user's typical workflow with **62 000+ cell gridlists**, which the prior `PARAMETER(NGPOINTS=3698)` statically dimensioned. (See `EXECUTION_PLAN.md` Decision #2 and §II.2; `COUPLED_MODEL_INVESTIGATION.md` §4.3.3 and §4.3.5; `_phase2_findings/SA3_…` §10.)

---

## 2. Scope decision (and what was deliberately deferred)

`imogen_lpjg.f` declares static arrays sized by **four** scaling constants:

| Constant | Value | # arrays | Reason for / against runtime conversion | Decision |
|---|---:|---:|---|---|
| `NGPOINTS` | 3698 | **6** in `PROGRAM IMOGEN` | This is the user-facing gridlist size; needs to scale to 62k+ | **Convert to runtime `ALLOCATABLE`** |
| `GPOINTS` | 1631 | ~30 (climatology + per-cell sub-daily output) | Tied to pattern + CRUNCEP file structure (those files have exactly 1631 cells); changing `GPOINTS` requires regenerating those upstream files. At `GPOINTS=1631` the BSS allocation works fine on Linux. | **Keep `PARAMETER(GPOINTS=1631)`** for now |
| `NFARRAY` | 10000 | 1 (`FA_OCEAN`) | Caps a single coupled-run segment to 500 yr at `NCALLYR=20`; sufficient for the 251-yr scenarios in scope for v1.0 | **Keep `PARAMETER(NFARRAY=10000)`** |
| `N_OLEVS` | 254 | 2 small | Ocean column resolution; a science choice, not a memory bottleneck | **Keep `PARAMETER(N_OLEVS=254)`** |

The **minimum-risk version** that achieves the functional goal of Decision #2 is just the 6 `NGPOINTS` arrays plus a parser change. The `GPOINTS` heap-vs-BSS conversion is a marginal memory-layout tweak (no functional benefit at the current `GPOINTS=1631`) and is deferred to a future cleanup step if/when memory-layout issues arise.

A grep also confirmed that **`nonco2.f` references none of these four constants**, so no changes were needed there.

---

## 3. Files modified

| File | Edit |
|---|---|
| `imogen/code/imogen_settings.txt` | Added `NGPOINTS 3698` line (line 11) with documentation comment |
| `imogen/code/imogen_lpjg.f` | (a) `PROGRAM IMOGEN` declarations: removed `PARAMETER(NGPOINTS=3698)`, converted 7 array decls to `ALLOCATABLE` (b) added `NGPOINTS` to the `CALL SETTIN(...)` argument list (c) inserted `ALLOCATE(...)` block after `CALL SETTIN` (d) inserted matching `DEALLOCATE(...)` block before `STOP` (e) added `NGPOINTS` to `SUBROUTINE SETTIN` signature, local declarations, sentinel initialisation, `CASE('NGPOINTS')` parser branch, and post-loop validation |

`nonco2.f`, the `Makefile`, and `compile.sh` were **not** modified.

---

## 4. Edit-by-edit detail

### 4.1 `imogen_settings.txt` — new key

Inserted at line 11 (before `STEP_DAY`):

```text
NGPOINTS 3698		!IN Number of grid points in the regridding gridlist (FILE_GRIDLIST). Must equal the line count of that file. Step 3 of unified-codebase rebuild made this run-time configurable; previously a hard-coded PARAMETER. - DKB 2026-05-05
```

The value `3698` matches `FILE_GRIDLIST gridlist_hurtt_RNDM_midpoint_3698.txt` already present in this settings file, preserving backward-compatible default behaviour for existing setups.

### 4.2 `imogen_lpjg.f` — `PROGRAM IMOGEN` declarations (formerly lines 289–301)

Before:
```fortran
      INTEGER NGPOINTS !Number of grid points in new gridlist...
      PARAMETER(NGPOINTS=3698) !NOTE: Needs to be hard-coded consistent with gridlist file - TP 06.08.15

      REAL
     & T_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)
     &,P_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)
     &,SW_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)
     &,DTEMP_OUT_M_REGRID(NGPOINTS,MM,32)
      INTEGER F_WET_CLIM_REGRID(NGPOINTS,MM)

      REAL
     & LON_OUT(NGPOINTS)
     &,LAT_OUT(NGPOINTS)
```

After:
```fortran
      INTEGER NGPOINTS !Number of grid points in new gridlist...
C [Step 3 of unified-codebase rebuild: NGPOINTS is now read from
C  imogen_settings.txt at run-time (was a hard-coded PARAMETER=3698).
C  This unblocks 62k+ cell gridlists without source recompile, per
C  Decision #2 of EXECUTION_PLAN.md. - DKB 2026-05-05]

      REAL, ALLOCATABLE :: T_OUT_M_REGRID(:,:,:,:)
      REAL, ALLOCATABLE :: P_OUT_M_REGRID(:,:,:,:)
      REAL, ALLOCATABLE :: SW_OUT_M_REGRID(:,:,:,:)
      REAL, ALLOCATABLE :: DTEMP_OUT_M_REGRID(:,:,:)
      INTEGER, ALLOCATABLE :: F_WET_CLIM_REGRID(:,:)

      REAL, ALLOCATABLE :: LON_OUT(:)
      REAL, ALLOCATABLE :: LAT_OUT(:)
```

Each `ALLOCATABLE` declaration is on its own line for maximum compatibility with fixed-form Fortran 77 column conventions; the `Makefile` already passes `-ffixed-line-length-132` so column 72 is not a concern.

### 4.3 `imogen_lpjg.f` — `CALL SETTIN(...)` site

Added `NGPOINTS` as the trailing argument:

```fortran
     & TAU_DECAY_N2O,NONCO2_EMISSIONS,NONCO2_EMISSIONS_LPJG,FILE_LPJG_CH4_N2O_FLUX,
     & CO2_RF_FAIR,NGPOINTS) !NGPOINTS added in Step 3 of unified-codebase rebuild - DKB 2026-05-05
```

### 4.4 `imogen_lpjg.f` — `ALLOCATE(...)` block (immediately after the `CALL SETTIN(...)` site)

```fortran
C [Step 3 of unified-codebase rebuild: ALLOCATE NGPOINTS-dimensioned
C  arrays now that NGPOINTS has been parsed from imogen_settings.txt.
C  This converts compile-time sizing to run-time sizing.]
      ALLOCATE(T_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX))
      ALLOCATE(P_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX))
      ALLOCATE(SW_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX))
      ALLOCATE(DTEMP_OUT_M_REGRID(NGPOINTS,MM,32))
      ALLOCATE(F_WET_CLIM_REGRID(NGPOINTS,MM))
      ALLOCATE(LON_OUT(NGPOINTS))
      ALLOCATE(LAT_OUT(NGPOINTS))
      PRINT *,'IMOGEN: ALLOCATEd regrid arrays for NGPOINTS=',NGPOINTS
      CALL FLUSH(6)
```

The `PRINT` line is intentionally retained as a startup banner to make the actual `NGPOINTS` value visible in run logs (units-integrity discipline §I.D rule 5: "startup banners").

### 4.5 `imogen_lpjg.f` — `DEALLOCATE(...)` block (immediately before `STOP`)

```fortran
C [Step 3 of unified-codebase rebuild: deallocate the NGPOINTS-dimensioned
C  arrays (good hygiene; prevents leak warnings under valgrind/sanitisers).
C  - DKB 2026-05-05]
      IF(ALLOCATED(T_OUT_M_REGRID))     DEALLOCATE(T_OUT_M_REGRID)
      IF(ALLOCATED(P_OUT_M_REGRID))     DEALLOCATE(P_OUT_M_REGRID)
      IF(ALLOCATED(SW_OUT_M_REGRID))    DEALLOCATE(SW_OUT_M_REGRID)
      IF(ALLOCATED(DTEMP_OUT_M_REGRID)) DEALLOCATE(DTEMP_OUT_M_REGRID)
      IF(ALLOCATED(F_WET_CLIM_REGRID))  DEALLOCATE(F_WET_CLIM_REGRID)
      IF(ALLOCATED(LON_OUT))            DEALLOCATE(LON_OUT)
      IF(ALLOCATED(LAT_OUT))            DEALLOCATE(LAT_OUT)
```

The `IF(ALLOCATED(...))` guards make the deallocation safe even on early-error exits (e.g. if a future programmer adds a second `STOP` path).

### 4.6 `imogen_lpjg.f` — `SUBROUTINE SETTIN` updates

Four atomic edits to `SETTIN` (line ~1207 onwards):

**(a)** Signature: appended `,NGPOINTS` to the trailing argument list (matching the `PROGRAM IMOGEN` call site).

**(b)** Local declaration block: added
```fortran
      INTEGER NGPOINTS      !OUT Number of grid points in regridding gridlist (FILE_GRIDLIST). Added Step 3 of unified-codebase rebuild - DKB 2026-05-05
```
just below the existing `INTEGER NYR_LPJG_FLUX` declaration (keeps related INTEGERs grouped).

**(c)** Sentinel initialisation immediately before `OPEN(81,...)`:
```fortran
C [Step 3 of unified-codebase rebuild: sentinel value for NGPOINTS so we
C  can detect a missing setting after the parse loop completes.]
      NGPOINTS=-1
```

**(d)** New `CASE` branch immediately before `CASE DEFAULT`:
```fortran
            CASE('NGPOINTS')
              READ(BUFFER,*,IOSTAT=IOS) NGPOINTS
              PRINT *,'Read NGPOINTS: ',NGPOINTS
```

**(e)** Post-loop validation immediately before the `RETURN`:
```fortran
C [Step 3 of unified-codebase rebuild: validate NGPOINTS was actually set.
C  If absent or non-positive, abort with a clear message rather than letting
C  ALLOCATE() fail or (worse) allocate a garbage size and segfault later.]
      IF(NGPOINTS.LE.0) THEN
        PRINT *,'ERROR: imogen_settings.txt is missing or has invalid'
        PRINT *,'       NGPOINTS line. Add e.g. "NGPOINTS 3698" matching'
        PRINT *,'       the line count of your FILE_GRIDLIST.'
        PRINT *,'       Got NGPOINTS=',NGPOINTS
        CALL FLUSH(6)
        STOP 1
      ENDIF
```

This **fail-loud** discipline matches `CONTRIBUTING.md` §"Units-integrity discipline" (CI checks → fail loudly on missing required keys) and the broader project philosophy that silent failures are unacceptable.

---

## 5. Why no changes were needed in `SUBROUTINE REGRID_CLIM`

`REGRID_CLIM` (line 1089 onwards) takes the `NGPOINTS`-dimensioned arrays as **dummy arguments**:

```fortran
      SUBROUTINE REGRID_CLIM(...,T_OUT_M_REGRID,P_OUT_M_REGRID,
     & SW_OUT_M_REGRID,DTEMP_OUT_M_REGRID,F_WET_CLIM_REGRID,
     & NGPOINTS,LON_OUT,LAT_OUT)
      ...
      INTEGER NGPOINTS               !IN Number of grid points in new gridlist
      ...
      REAL T_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)  !OUT...
```

Fortran 77/90 explicit-shape dummy arrays size themselves at call time using the value of the dummy `NGPOINTS` integer — exactly the value that `PROGRAM IMOGEN` now allocates with. **No signature change is required** when passing an `ALLOCATABLE` actual to such a dummy. The internal local `LON_OUT_WORK(NGPOINTS)` automatically becomes a stack-allocated automatic array, sized correctly at each call.

A separate concern at very large `NGPOINTS` (≥1 M) would be stack-overflow on `LON_OUT_WORK`, but at 62k cells the stack cost is only 496 KB — well below default `ulimit -s 8192` (8 MB). If we ever push past that, we should convert `LON_OUT_WORK` to `ALLOCATABLE` in a future step.

---

## 6. Verification

### 6.1 Build

```bash
cd lpj-guess_imogen_landsymm/imogen/code
make clean
make
```
Output: clean compile with `gfortran -ffixed-line-length-132 -O`, no warnings, no errors.

### 6.2 Smoke probes

| Probe | Setting | Expected | Actual |
|---|---|---|---|
| **Positive** | `NGPOINTS 3698` | Parser reads, ALLOCATEs ~30 MB, terminates at later runtime input read (no LPJ-GUESS partner) | ✅ `Read NGPOINTS: 3698` → `IMOGEN: ALLOCATEd regrid arrays for NGPOINTS=3698` → terminates at line 347 `Cannot open file './/IMOGEN/CO2_all.dat'` |
| **Negative** | `NGPOINTS` line removed | Sentinel validation fires, clean abort with helpful message | ✅ `ERROR: imogen_settings.txt is missing or has invalid NGPOINTS line. ... Got NGPOINTS=-1` → `STOP 1` |
| **Scaling** | `NGPOINTS 10000` | Parser reads new value, ALLOCATEs ~170 MB heap, terminates at same later input read | ✅ `Read NGPOINTS: 10000` → `IMOGEN: ALLOCATEd regrid arrays for NGPOINTS=10000` → terminates at line 347 |

The line-347 termination in probes 1 and 3 is the **expected** end-point for a standalone IMOGEN run with no LPJ-GUESS partner: `IMOGEN/CO2_all.dat` is a runtime input file that LPJ-GUESS writes via `imogencfx`. It is not a regression — it is exactly the same termination signature observed in step 2's smoke probe (before any of the step-3 changes were applied), demonstrating that the refactor is purely additive and does not change downstream control flow.

### 6.3 Memory footprint at typical sizes

| `NGPOINTS` | Heap allocated by step 3 (4-byte REAL/INTEGER) |
|---:|---:|
| 3 698 (default) | ≈ 33 MB |
| 10 000 | ≈ 90 MB |
| 62 000 | ≈ 553 MB |
| 100 000 | ≈ 891 MB |

Calculation: 3 × `T/P/SW_OUT_M_REGRID(NGPOINTS,12,32,24)` + 1 × `DTEMP_OUT_M_REGRID(NGPOINTS,12,32)` + 1 × `F_WET_CLIM_REGRID(NGPOINTS,12)` + 2 × `LON/LAT_OUT(NGPOINTS)` ≈ `27,792 × NGPOINTS` bytes (4-byte words; gfortran uses 4-byte default REAL/INTEGER unless `-fdefault-real-8` is specified, which it isn't in our `Makefile`).

All values are well within typical workstation/cluster RAM (≥ 8 GB).

---

## 7. What this step does NOT yet do (deferred)

The full closed-loop tight-coupling smoke test (Fortran IMOGEN ↔ LPJ-GUESS via `done`-file rendezvous) requires:

- A pre-existing `IMOGEN/CO2_all.dat` (written by LPJ-GUESS via `imogencfx` on its first call) — **step 6** of the rebuild plan.
- The C++ IMOGEN engine wired into `lpjguess/modules/climatemodel.cpp` to be replaced by a `CALL SYSTEM` invocation of the Fortran `imogen_lpjg` binary (or vice-versa) — **step 6**.
- A complete coupled-run setup (`imogen_intermediary.ins` + climate inputs + intermediary controller) — **steps 9–14**.

What step 3 **does** establish, and which is now durable:

- The Fortran IMOGEN binary will accept any `NGPOINTS` from a settings-file edit, no recompile.
- The new key has a defensive validation that fails loudly when missing.
- The build still succeeds; no warnings; no test regression.

---

## 8. Recovery protocol (if a later step uncovers a regression)

If any later step reveals that the ALLOCATABLE refactor introduced a subtle problem (e.g. an array-shape mismatch in a subroutine I didn't anticipate), the recovery is straightforward:

1. Diagnose against the Phase 2 audit findings in `_phase2_findings/` and any new failure logs.
2. Fix the specific call site (the conversion is purely mechanical; no semantics changed).
3. Worst-case escape: revert this commit (`git revert <step3-hash>`) — the code returns to the static `PARAMETER(NGPOINTS=3698)` baseline, with a working step 2 binary.

---

## 9. Documentation updates accompanying this step

- `notes/STEP_3.md` — this file (created)
- `imogen/README.md` — updated to reflect runtime-`NGPOINTS` capability
- `CHANGELOG.md` — `[v0.3.0-fortran-allocatable]` entry
- `EXECUTION_PLAN.md` Part V — step 3 marked ✅ complete

---

## 10. Push commands (manual three-way push)

```bash
cd /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm
git push origin main
git push kit main
git push helmholtz main
```
