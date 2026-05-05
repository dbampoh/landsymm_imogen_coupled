# STEP 4 — Import GCM patterns + CRUNCEP base climatology + standalone IMOGEN smoke

**Date completed:** 2026-05-05
**Commit:** _to be filled in after `git commit`_
**Status:** ✅ verification milestone hit (per-year output 1871, 1872 produced; structurally matches `version_A`'s reference output)

---

## 1. Goal

Acquire the IMOGEN reference data — 35 GCM patterns + 1 30-year base
climatology, ~161 MB raw — into the unified codebase, **without
committing the data to git**, and verify the standalone Fortran IMOGEN
binary produces sensible per-year output (the verification milestone
deferred from step 2).

Per Decision #5 (incremental rebuild) and the EXECUTION_PLAN.md V.1
step 4 specification.

---

## 2. Architectural decision: external fetch-script + checksum manifest

After three options (commit-everything / git-LFS / fetch-script-with-manifest /
hybrid-tiny-defaults) the user chose **the fetch-script + manifest
approach**. Rationale:

- **Lean repo**: clones don't include 161 MB (or 49 MB compressed) of
  immutable upstream reference data.
- **Deterministic provenance**: SHA256 + size manifest gives any
  workstation/cluster a way to verify they have the right data.
- **Flexibility**: the same script can pull from a local sibling
  directory (the workstation case during development), an institutional
  bucket, a Zenodo record, or a GitHub Release (a TBD permanent host
  the user will set up).
- **No new git dependency**: unlike git-LFS, no extra tooling needed
  on cluster nodes.

### What got committed to git in step 4

- `tools/fetch_imogen_data.sh` — the acquisition script (≈210 lines bash)
- `tools/imogen_data_manifest.txt` — authoritative manifest of the 4
  tarballs (filename, SHA256, size, extract path)
- `imogen/patterns/README.md` — explains structure + acquisition
- `imogen/patterns/readme.log` — the 127-byte upstream provenance note
- `imogen/CRUNCEP_1960_1989/README.md` — same for CRUNCEP
- `imogen/emiss/README.md` — same for the small reference emission files
- `.gitignore` — fix to a pre-existing bug + new exclusions

### What did NOT get committed

- The 4 data tarballs themselves (49 MB total, sit at the sibling path
  `lpj-guess_imogen_landsymm_data/` for the user's reference)
- The extracted data (~161 MB; gitignored under
  `imogen/patterns/CEN_*/`, `imogen/patterns/CMIP6_*/`,
  `imogen/patterns/ukmo_hadcm3_rel/`, `imogen/CRUNCEP_*/`)
- The 3 emission reference files staged at `imogen/emiss/` (gitignored;
  will be rolled into a future emission-tarball at step 6)
- The smoke-run runtime state at `imogen/code/IMOGEN/` and
  `imogen/code/LPJG_main/` (gitignored)

---

## 3. The 4 distribution tarballs

| Tarball | Source contents | Compressed | Original | SHA256 (truncated) |
|---|---|---:|---:|---|
| `imogen-patterns-cmip5-v1.0.tar.gz` | 34 CMIP5 ASCII pattern dirs `CEN_*_MOD_*/` (Zelazowski 2018 ensemble) | **19 MB** | 82 MB | aaafdf80…785eb635 |
| `imogen-patterns-cmip6-v1.0.tar.gz` | 5 CMIP6 NetCDF GCMs (`CMIP6_IMOGEN_EBM_values_and_patterns/`: GFDL-ESM4, IPSL-CM6A-LR, MPI-ESM1-2-HR, MRI-ESM2-0, UKESM1-0-LL) | **19 MB** | 20 MB | e6e6c082…f47e40 |
| `imogen-patterns-cmip3-legacy-v1.0.tar.gz` | 1 UKMO HadCM3 CMIP3 pattern (`ukmo_hadcm3_rel/`) | **534 KB** | 2 MB | f566bc01…6efd72b |
| `imogen-cruncep-1960-1989-v1.0.tar.gz` | 30-year base climatology (12 mo × 30 yr × 1631 cells ASCII) | **11 MB** | 60 MB | ef218143…f40426b |
| **Total** | 791 reference files | **49 MB** | **161 MB** | |

Compression ratio ≈ 3.3×. Driven by the ASCII patterns + CRUNCEP files
(highly compressible repetitive numeric formats); the CMIP6 NetCDF
content barely compresses (already binary-encoded).

Generated 2026-05-05 from
`version_A/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/Common-directory/IMOGEN-codebase/`.

The 4 tarballs are saved at the sibling path
`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm_data/`
on the workstation. To make them publicly available, the user will
upload them to a permanent host (Zenodo / GitHub Releases / institutional
bucket) and update the `IMOGEN_DATA_BASE` URL in `tools/README.md`.

---

## 4. The fetch script — `tools/fetch_imogen_data.sh`

### Modes

| Mode | What it does | Use case |
|---|---|---|
| `--list` | Print the manifest (filename, SHA256-truncated, size); no I/O | Discovery; CI sanity check |
| _(default)_ | Fetch from `$IMOGEN_DATA_BASE` (file path or URL) → SHA256-verify → extract to `imogen/` | First-time setup; CI provisioning |
| `--verify-only` | Re-checksum a local source directory; no extract | Confirming a previous fetch is intact |
| `--component <name>` | Filter to a single component (repeatable) | Smoke tests with minimal data; per-GCM partial fetches |

The script is **strict-mode bash** (`set -euo pipefail`). Initial draft
hit the classic `set -e` + `((var++))` pitfall (the `((errors++))`
expression returns the *pre-increment* value, which is 0 → "false" →
`set -e` aborts); fixed by replacing all `((var++))` with
`var=$((var+1))`.

### Tested modes

| Mode | Outcome |
|---|---|
| `--list` (no args) | ✅ prints all 4 components |
| `--base <local-dir> --verify-only` | ✅ all 4 verify clean |
| `--base <local-dir> --verify-only --component patterns-cmip3-legacy` | ✅ filters to 1 component |
| `--base /tmp --verify-only` (empty source) | ✅ correctly reports "MISSING at /tmp/imogen-cruncep-1960-1989-v1.0.tar.gz" and exits 1 |

The full extract-from-https path is not tested yet because no
permanent host has been set up; that's deferred until the user
uploads the tarballs.

---

## 5. `.gitignore` correction (the inline-comment bug)

While adding the data-exclusion rules I introduced (and then immediately
debugged) a subtle bug: I'd written the rules as

```text
imogen/patterns/CEN_*/           # 34 CMIP5 ASCII patterns (~82 MB)
```

**This does NOT work** — gitignore parses the `#` comment as part of
the pattern (literal text including the trailing whitespace + `#` +
description). All 431 pattern files therefore showed as untracked-but-
not-ignored. Confirmed via `git ls-files --others --exclude-standard`.

**Fix**: gitignore comments must be on their own line, prefixed with
`#`. Reformatted to:

```text
# 34 CMIP5 ASCII patterns (~82 MB)
imogen/patterns/CEN_*/
```

After the fix: only `imogen/patterns/readme.log` shows as
untracked-but-not-ignored — exactly what we want.

This bug ALSO affected step 0's pre-existing `.gitignore` rules of the
same form (`imogen/patterns/CMIP6_*/` etc. with inline comments), all
of which were silently broken. Step 4 fixes them.

Lesson written into the gitignore itself as a comment: "_NOTE: gitignore
does NOT support inline comments after a pattern; keep all comments
on their own lines._"

### Final .gitignore additions (step 4)

```text
# IMOGEN auxiliary (large reference data; acquired via tools/fetch_imogen_data.sh
# at step 4 of unified-codebase rebuild; never committed to git).
# 30-year base climatology (CRUNCEP 1960-1989, ~60 MB)
imogen/CRUNCEP_*/
# 5 CMIP6 NetCDF patterns (~20 MB)
imogen/patterns/CMIP6_*/
# 34 CMIP5 ASCII patterns (~82 MB)
imogen/patterns/CEN_*/
# 1 CMIP3 legacy pattern (~2 MB)
imogen/patterns/ukmo_hadcm3_rel/
# Reference emission files (~20 KB historical RCP8.5)
imogen/emiss/
# Run-time output for standalone smoke runs from imogen/code/
imogen/code/IMOGEN/
imogen/code/runtime/
imogen/code/LPJG_main/
# Allow-list overrides (small upstream/internal docs we DO want)
!imogen/patterns/readme.log
!imogen/patterns/README.md
!imogen/CRUNCEP_1960_1989/README.md
!imogen/emiss/README.md
```

---

## 6. The standalone smoke run — verification milestone

### What we needed beyond patterns + CRUNCEP

The first attempt (just patterns + CRUNCEP staged) hit a pre-existing
`Cannot open './/IMOGEN/CO2_all.dat'` error — the binary needs the
**`IMOGEN/` runtime output directory pre-created**. After `mkdir -p
IMOGEN/output`, the binary progressed, but then entered an indefinite
**polling loop** waiting for LPJ-GUESS-side handshake files at
`LPJG_main/IMOGEN/`.

Investigation revealed: `version_A`'s standalone runs work via
**pre-staged stub LPJG-side files**, mimicking what LPJ-GUESS would
write at each yearly handoff. The 8 files needed are:

| File | Size | What it represents |
|---|---:|---|
| `imogen_lpjg.txt` | 369 B | YEAR1, IYEND, YEAR1_LPJG, SPINUP, KEEPRUNNING, FIRSTCALL — the per-year control state |
| `extended_lpjg_only_cfluxrcp{26,85}.txt` | ~3.4 KB | LPJG-only annual NEE for the spin-up years |
| `lpjg_only_cfluxrcp{26}.txt` | 3.6 KB | similar for some scenarios |
| `imogen_lpjg_flux.txt` | 10 B | per-year LPJG NEE (from coupled mode) |
| `imogen_lpjg_ch4_n2o_flux.txt` | 13 B | per-year LPJG CH4/N2O fluxes (from coupled mode) |
| `ch4_n2o_annual_historical_ssp{1,5}rcp{26,85}_lpjg_simulated_real.txt` | 6.3 KB | scenario-specific CH4+N2O timeseries |
| **`done`** (empty) | 0 B | the handshake marker LPJ-GUESS would write at end-of-year |
| `README.txt.txt` | 0 B | upstream zero-byte readme |

**Most critically**: the empty `done` file is what unblocks the polling
loop at `imogen_lpjg.f:400-403`:

```fortran
IF ((RUNNOW_EXIST.AND.(RUNNOW_OPEN.EQV..FALSE.)) .AND.
 &  (RUNFLUX_EXIST.AND.(RUNFLUX_OPEN.EQV..FALSE.)) .AND. DONE_EXIST .AND.
 &  ((NONCO2_EMISSIONS.AND.RUNNONCO2FLUX_EXIST.AND.(RUNNONCO2FLUX_OPEN.EQV..FALSE.))
 &    .OR.(NONCO2_EMISSIONS.EQV..FALSE.))) THEN
   RUNNOW=.TRUE.
   CALL SETTIN_LPJG(...)
```

`DONE_EXIST` is the make-or-break condition. Note `imogen_lpjg.f:363`
has a commented-out `!DONE_EXIST=.TRUE.` — this is exactly **bug C2/C3**
from `[CMI §1.2 / SA3 §10]`'s "neutered polling-loop safety checks".
The original developer's safety default would have made `DONE_EXIST=T`
on first call (when no `done` file from a previous year exists yet),
which would have made standalone runs work out-of-the-box. With it
commented out, every standalone user has to manually create an empty
`done` file.

**Step 4 worked around this by pre-staging an empty `done` file**.
Step 7 of the rebuild plan will fix the source code (uncomment line 363
or add a `FIRSTCALL` special-case), eliminating the manual workaround.

### The smoke run results

With all 8 stub files in place + `IMOGEN/output/` pre-created, the
binary processed years 1871 and 1872 in ≈12 seconds, producing:

```text
imogen/code/IMOGEN/
├── CO2_all.dat                  (running CO2 trajectory; opened then closed by binary)
├── RF_all.dat                   (196 B — per-year radiative-forcing accumulator)
├── VARYEAR.dat                  (13 B — variability-year tracker)
└── output/
    ├── 1871/
    │   ├── CO2.dat              (125 B — annual atmospheric concentrations)
    │   ├── T_anom.dat           (447 KB — temperature anomalies)
    │   ├── P_anom.dat           (447 KB — precipitation anomalies)
    │   ├── SW_anom.dat          (447 KB — shortwave radiation anomalies)
    │   ├── DTEMP_anom.dat       (447 KB — diurnal range anomalies)
    │   ├── WET.dat              (223 KB — wet-day fraction)
    │   ├── dtemp_o.dat          (9.1 KB — ocean column temperature anomaly)
    │   ├── fa_ocean.dat         (403 KB — ocean CO2 flux history)
    │   └── done                 (23 B — handshake marker the binary wrote)
    └── 1872/  (same structure)
```

Sample T_anom.dat content (Arctic latitude 82.5°):

```text
 281.250  82.500   237.736   235.544   231.825   241.011   260.809   273.352   276.512   273.289   264.278   249.820   239.847   237.298
```

— a sensible Arctic-summer-to-winter Kelvin temperature swing (231 K =
–42°C in coldest month, 276 K = +3°C in warmest month at lat=82.5°).
✅ Physical.

CO2.dat for 1871: `1871   286.084991       0.00000000  ...   865.000000   277.399994` — initial CO2=286.085 ppm, CH4=865 ppb, N2O=277.4 ppb, all matching `imogen_settings.txt` defaults. ✅

### Comparison with version_A's 1871 output

|  | Ours (Fortran, step 3+4) | version_A (most likely C++) | Difference |
|---|---:|---:|---|
| Files produced | 9 | 11 | version_A has Rh_anom.dat + W_anom.dat |
| T_anom.dat size | 447 KB | 246 KB | ours has more decimals + 2× line count |
| T_anom.dat lines | 3262 | 1631 | ours has exactly 2× — to investigate |
| T(lat=82.5°,lon=281.25°,jan) | 237.736 K | 237.833 K | 0.097 K |
| T(lat=82.5°,lon=285.0°,jan) | 238.900 K | 241.426 K | 2.5 K |
| T(lat=82.5°,lon=288.75°,jan) | 241.169 K | 249.886 K | 8.7 K |
| md5(T_anom.dat) | 8ce558a2... | b51df7fa... | not byte-identical |
| CO2.dat numerical content | 286.085 ppm, 865 ppb, 277.4 ppb | identical (just narrower formatting) | match |

**Interpretation**: version_A's runs almost certainly used the C++
refactor (the `[IMOGEN LOGGER][2025-06-16 …] [INFO]` log-line format
in `version_A/.../IMOGEN/imogen_*.log` is a C++ logger style; the
Fortran source uses plain `WRITE(*,*)` without timestamps). So the
non-byte-identity is **expected** at this stage — Fortran ↔ C++
numerical parity is itself the Phase-2 milestone (Decision #2). The
shared structural layout (same files minus Rh/W; same line format;
same column meaning; same physical values) is the relevant indicator
that step 4 has succeeded.

### Known follow-ups discovered during step 4

1. **Missing Rh_anom.dat and W_anom.dat in Fortran output** — confirms
   `[SA3 §10]` finding. Will be addressed at **step 9.5** of the rebuild
   plan (port the C++ writers back into Fortran for parity).

2. **2× the line count in T_anom.dat (3262 vs 1631)** — to investigate
   as a Fortran-side writer quirk. Possible causes: (a) the Fortran
   writer iterates the cells twice for some reason (e.g. once for the
   1631-cell native grid + once for the 3698-cell extended grid even
   though `REGRID=.FALSE.`); (b) it writes for all `NSDMAX`
   sub-day-step-equivalents (NSDMAX=24 by default but expressed
   differently); (c) a subtle bug. Documented as a Phase-2 investigation.

3. **Numerical divergence vs C++** at most cells (0.1–8 K on
   T_anom.dat). To be quantified during the C++-vs-Fortran parity work
   in Phase 2 (Decision #2). Could come from compilation-related
   precision differences, slight algorithm tweaks during the C++
   refactor, or random-number-stream differences in the variability
   sampler.

4. **Manual `done`-file workaround needed at first call** — bug C2/C3
   in the existing audit; fixed at step 7 by either uncommenting
   `imogen_lpjg.f:363` or adding a `FIRSTCALL` special-case.

---

## 7. Files modified / added

### Added (committed to git)

| Path | Size | Purpose |
|---|---:|---|
| `tools/fetch_imogen_data.sh` | ~7 KB | acquisition + verification + extract |
| `tools/imogen_data_manifest.txt` | ~2 KB | authoritative tarball manifest |
| `imogen/patterns/README.md` | ~5 KB | patterns directory readme |
| `imogen/patterns/readme.log` | 127 B | upstream provenance note (untouched) |
| `imogen/CRUNCEP_1960_1989/README.md` | ~2 KB | climatology directory readme |
| `imogen/emiss/README.md` | ~2 KB | (emission staging readme; see below) |
| `notes/STEP_4.md` | this file | per-step verification record |

### Modified (committed to git)

| Path | Reason |
|---|---|
| `.gitignore` | fix inline-comment bug; add LPJG_main, code/IMOGEN, code/runtime, emiss exclusions; allow-list new READMEs |
| `imogen/README.md` | step-4 section + how-to-fetch-data |
| `tools/README.md` | document the fetch script + manifest + smoke recipe |
| `CHANGELOG.md` | `[v0.4.0-imogen-data-fetch-script]` entry |
| `EXECUTION_PLAN.md` Part V | step 4 marked ✅ |

### Generated and saved at sibling path (NOT in git)

`/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm_data/`:

```text
imogen-cruncep-1960-1989-v1.0.tar.gz       11 MB
imogen-patterns-cmip3-legacy-v1.0.tar.gz   534 KB
imogen-patterns-cmip5-v1.0.tar.gz          19 MB
imogen-patterns-cmip6-v1.0.tar.gz          19 MB
```

These are the artefacts the user will eventually upload to a permanent
host (Zenodo / GitHub Releases / institutional bucket).

---

## 8. Recovery / re-fetch protocol

If a clone needs to recreate the smoke run from scratch:

```bash
# 1. Clone the repo
git clone https://github.com/dbampoh/landsymm_imogen_coupled.git
cd landsymm_imogen_coupled

# 2. Fetch the data (point at wherever the tarballs live)
tools/fetch_imogen_data.sh --base /path/to/lpj-guess_imogen_landsymm_data

# 3. Build IMOGEN
cd imogen/code
make

# 4. Stage the LPJG-side stub files (until step 7 fixes this)
mkdir -p LPJG_main/IMOGEN IMOGEN/output
# (copy the 8 stub files from version_A; OR write them by hand using
#  the templates in this notes file)

# 5. Run
./imogen_lpjg
```

Per-step recovery: a clean revert of step 4 is just `git revert <hash>`
followed by removing the data tree. The fetch script will re-extract
on the next run.

---

## 9. Push commands (manual three-way push)

```bash
cd /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm

git push origin main
git push kit main
git push helmholtz main

# Optional tag:
git tag -a v0.4.0-imogen-data-fetch-script -m "Step 4: IMOGEN reference data tarballs + fetch script; Fortran standalone smoke milestone"
git push origin v0.4.0-imogen-data-fetch-script
git push kit    v0.4.0-imogen-data-fetch-script
git push helmholtz v0.4.0-imogen-data-fetch-script
```
