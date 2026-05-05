# `imogen/` — IMOGEN climate emulator

Will hold the Fortran IMOGEN with the `ALLOCATABLE`-array refactor
(Phase 1, primary) and the C++ refactor brought to numerical parity
(Phase 2, follow-on; both backends switchable).

**Phase 1 (step 2):** Import the working Fortran IMOGEN from
`Common-directory/IMOGEN-codebase/code/`:

- `imogen_lpjg.f` (4 138 lines, 17 subroutines), `nonco2.f` (174 lines,
  2 subroutines).
- `Makefile`, `compile.sh` (gfortran build).
- `imogen_settings.txt`, `imogen_settings_tmpl.txt` — but with paths
  rewritten from Windows `C:\GitHub\...` to relative.

Apply the small fixes immediately on import:
- Delete `PAUSE` at line 4134 (the `QSAT` debug-halt).
- Delete the `qsat_output.txt` debug-dump block (lines 4120-4128).
- Replace `\\` with `/` in `mkdir` calls (lines 435, 461).

**Phase 1 (step 3):** Convert the ~30 statically-declared arrays in
`imogen_lpjg.f` and `nonco2.f` that scale with `NGPOINTS` or
`GPOINTS` to `ALLOCATABLE`; add `ALLOCATE` calls keyed off the
gridlist file length. This delivers heap allocation and unblocks
62 000+ cell gridlists (Decision #2 in EXECUTION_PLAN §Decisions
Settled).

**Phase 1 (step 9.5):** Port the C++ Rh+W writers
(`Rh_anom.dat`, `W_anom.dat`) back into Fortran so both backends
produce parity output. Add `Tmin_anom.dat` and `Tmax_anom.dat`
writers (compute `Tmin = T - DTEMP/2`, `Tmax = T + DTEMP/2`).

**Phase 2 (step 20+):** Bring the C++ refactor (`IMOGENCXX/` from
the predecessor framework) to numerical parity using Fortran
outputs as QC reference. 25 catalogued bugs to fix; port `DAY_CALC`
and `SOLPOS` from Fortran; add a build system. Then expose both
as switchable backends via the `imogen_backend` ins parameter.

See `EXECUTION_PLAN.md` §II.2 for the strategic decision and
Part V for the implementation sequence.

## Subdirectories (to be populated)

- `code/` — Fortran source + Makefile + settings template.
- `patterns/` — 36 GCM-pattern dirs (34 CMIP5 ASCII + 1 CMIP3 legacy
  + 5 CMIP6 NetCDF converted to CMIP5 ASCII via
  `tools/cmip6_nc_to_cmip5_ascii.py`).
- `CRUNCEP_1960_1989/` — 30-year base climatology.
- `docs/` — Huntingford 2000, Huntingford 2010 PDFs.
