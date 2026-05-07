# `runs/SSP1-2.6/` — Coupled SSP1-2.6 scenario run setup

Step 9 of the V.1 rebuild plan. The first run-config setup that exercises
the unified codebase end-to-end (subject to F-10 architectural caveats —
see "Empirical findings" below).

## What's here

| File | Role |
|---|---|
| `main.ins` | LPJG entry point. Imports global / crop_n / wetlandpfts / imogen_intermediary; smoke-test overrides for nyear_spinup, freenyears, firsthistyear, lasthistyear, firstoutyear, lastoutyear, firemodel, run_landcover, npatch. |
| `imogen_intermediary.ins` | IMOGEN-coupling parameters (DIR_COMMON, DIR_PATT, FILE_*, coupling_mode, T_OCEAN_INIT, etc.). Embodies bug C5 + R-anom fixes; documents bug C35 fix attempt + F-10 deadlock empirically. |
| `crop.ins`, `crop_n.ins`, `crop_n_*.ins` | LandSyMM-fork crop PFTs + stand list (copied verbatim from version_A's predecessor SSP1_RCP26 setup; only paths to LU/Nfert/irrig data updated to point at version_A's actual tree). |
| `pasture_n_stlist*.ins` | Pasture stand list (copied from predecessor). |
| `landcover.ins` | Landcover fractions config (copied from predecessor; LU paths retargeted to version_A's actual tree). |
| `wetlandpfts.ins` | Wetland PFTs (copied from predecessor). |
| `global.ins`, `global_soiln.ins` | Standard LPJ-GUESS global PFTs + soil-N config (copied from predecessor). |

## Run command

```bash
cd runs/SSP1-2.6
mkdir -p Common-directory/LPJG_main/IMOGEN

# Bootstrap the handshake directory so the IMOGEN engine's polling
# loop can find at least imogen_lpjg.txt + done at startup. Without
# these, the engine deadlocks waiting for files that LPJG can't yet
# produce (it hasn't started its main loop). See "Empirical findings"
# below for why this bootstrap is necessary in v1.0.
cat > Common-directory/LPJG_main/IMOGEN/imogen_lpjg.txt <<'EOF'
YEAR1 1871 !IN First year of the numerical experiment
IYEND 1872 !IN Stop year of the ENTIRE run
YEAR1_LPJG 1871 !IN First year of the whole LPJ-GUESS simulation
SPINUP FALSE !IN Are we in the spin-up phase of LPJ-GUESS?
KEEPRUNNING TRUE !IN control flag to keep imogen running
FIRSTCALL TRUE !IN Is this the very first call to IMOGEN from LPJ-GUESS
EOF
echo "bootstrap" > Common-directory/LPJG_main/IMOGEN/done

# Then launch:
../../lpjguess/build/guess -input imogencfx main.ins
```

The engine will produce per-year climate ASCII files at
`Common-directory/IMOGEN/output/<YYYY>/{T_anom.dat, P_anom.dat, ...}`.

## Empirical findings — V.1 step 9 smoke (2026-05-07)

Worth reading before running. **The smoke runs successfully through
the IMOGEN-engine portion but cannot reach LPJG's main loop in v1.0.**

### Substantive successes

- ins-file infrastructure: parses cleanly, all `declare_parameter` calls satisfied
- bug C5 fix verified: engine emits to `IMOGEN/output/<YYYY>/` (not `ouput/`)
- bug R-anom fix verified: engine emits `Rh_anom.dat` (matches our `file_relhum` path)
- step-6 SSP126 NON_CO2 RF file added (was missing from our tree)
- IMOGEN engine read all required inputs successfully:
  - 12 monthly GCM pattern files (CMIP6 MRI-ESM2-0)
  - 251 years of CRUNCEP base climatology
  - 251 years of anthropogenic CO2 emissions
  - 251 years of NON_CO2 radiative forcing
  - 251 years of LPJG-style natural CH4+N2O fluxes (from absolute-path static IIASA file in prescribed mode)
- engine produced 32 years × 10 climate output files = 320 files in 3 minutes

### F-10 architectural deadlock empirically confirmed

In v1.0 single-process imogencfx mode, **regardless of `coupling_mode`
("tight" or "prescribed"), the engine cannot reach a clean termination
without LPJG-supplied handshake updates** — and LPJG cannot run its
main loop until `imogencfx::init()` returns, which it does not until
the engine terminates. The engine ran 32 years using the bootstrap
`imogen_lpjg.txt` we pre-populated, then deadlocked polling for year
1903's `done` file (which only LPJG can produce).

This means:
- step 8's writer (`ImogenOutput::flush_year`) NEVER FIRES in v1.0
  single-process mode, regardless of `coupling_mode`
- `Common-directory/LPJG_main/IMOGEN/imogen_lpjg_flux.txt` and
  `imogen_lpjg_ch4_n2o_flux.txt` are NEVER written in v1.0
- the V.1 step-9 verification milestone (NEE 2x perturbation → CO2
  trajectory shift) cannot be tested in v1.0; gated on follow-up F-12
  (multi-pass / two-process verification design)

### Why the bug C35 "fix" can't be tested in v1.0

When `FILE_LPJG_FLUX` is RELATIVE (the C35 fix), the engine's path-concat
produces `<DIR_COMMON>/LPJG_main/IMOGEN/imogen_lpjg_flux.txt` which
doesn't exist (LPJG hasn't written it). `RUNFLUX_EXIST=0` → polling loop
deadlocks IMMEDIATELY (before producing any climate).

When `FILE_LPJG_FLUX` is ABSOLUTE (the predecessor's "bug"), the static
file always exists, polling exits, engine runs through years using the
static-file flux → no need to wait for LPJG. This is what allowed the
predecessor framework to "appear to work" while actually running as
prescribed-emissions.

The fix is correct in the sense that it WOULD enable real two-way
coupling. But two-way coupling requires concurrent engine + LPJG, which
v1.0 single-process mode cannot provide.

## Production setup (post-V.1)

For a real coupled production run after F-12 is implemented:
- Replace the smoke gridlist (4 cells) with a production gridlist (e.g.,
  `data/gridlist/gridlist_in_62892_and_climate.txt`)
- Restore `nyear_spinup 500` (production value; predecessor used 500)
- Restore `freenyears 100` (production value)
- Restore `npatch 25` (production value; smoke uses 1)
- Restore `firemodel "BLAZE"` AFTER step 9.5 wires up wind+RH inputs to LPJG
- Adjust `firsthistyear`/`lasthistyear`/`firstoutyear`/`lastoutyear`/`YEAR1`/`IYEND`
  to your scenario window
- Consider switching to landsymm_py-generated LU instead of version_A's
  legacy LU (data/DATA.md describes the recipe)
- Run `tools/fetch_imogen_data.sh --component ndep` and update
  `param "file_ndep"` to point at the Lamarque archive

## v1.0 caveats summary (must-read)

- v1.0 single-process imogencfx mode does NOT actually achieve closed-loop
  IMOGEN ↔ LPJG coupling (F-10 architectural mismatch)
- Until F-12's multi-pass/two-process design is implemented, the engine
  must be run with `coupling_mode = "prescribed"` + absolute-path
  static-IIASA `FILE_LPJG_FLUX` and `FILE_LPJG_CH4_N2O_FLUX` to terminate
- This effectively reduces the v1.0 coupled run to a one-way IMOGEN-driven
  experiment with prescribed natural-emission backbone
- Production validity should be evaluated with this caveat understood
