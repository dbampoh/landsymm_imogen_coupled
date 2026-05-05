# `runs/` — per-scenario run setups

One subdirectory per (mode, scenario) combination. Populated incrementally
through Part V of the rebuild plan.

## Layout (post-v1.0)

```
runs/
├── historic/                             Phase 1: standalone HILDA+ historic
│   ├── main.ins                          1850-2020 (CFX mode, no IMOGEN)
│   ├── landcover.ins                     HILDA+ historic LU
│   ├── crop.ins, crop_n.ins, ...
│   ├── gridlist_in_62892_and_climate.txt
│   ├── saved_state_2020/                 ← OUTPUT: state file at year 2020
│   └── output/                           cflux.out, mch4.out, ngases.out, ...
│
├── SSP1-2.6/                             Phase 2: coupled scenario, restart
│   ├── main.ins                          from 2020 saved state
│   ├── imogen_intermediary.ins
│   ├── landcover.ins                     New PLUM LU 2021-2100 (landsymm_py)
│   ├── crop.ins, crop_n.ins, ...
│   ├── gridlist_in_62892_and_climate.txt
│   ├── inputs/                           output of tools/imogen_inputs_to_lpjg_format.py
│   │   ├── co2_anthro_emissions.txt
│   │   ├── ch4_n2o_anthro_emissions.txt
│   │   ├── imogen_lpjg_flux.txt          (seed for prescribed mode; populated live in tight mode)
│   │   └── imogen_lpjg_ch4_n2o_flux.txt
│   └── output/                           per-rank outputs after parallel run
│
├── SSP2-4.5/                             same shape as SSP1-2.6
├── SSP3-7.0/, SSP4-6.0/, SSP5-8.5/        (added per priority)
│
└── stage1_potyield/                      Stage I yield generation
    └── (DEFERRED to v2.0 — see EXECUTION_PLAN.md §I.B.4 and Decision #9.
         Documentation only in v1.0; the existing pre-computed yields in
         `Data/Intermediary/PLUM_data/` are reused.)
```

## LU strategy: save_state/restart (Decision #10)

Per `EXECUTION_PLAN.md` §I.C.1, the v1.0 LU strategy uses LPJ-GUESS's
`save_state`/`restart` machinery:

- `runs/historic/` runs standalone (no IMOGEN) for 1850-2020 with
  HILDA+ historic LU and ISIMIP-3b prescribed climate. Saves state
  at 2020.
- `runs/SSP1-2.6/` (and the other SSP runs) start with `restart=1`
  from `../historic/saved_state_2020/`, then run 2021-2100 with the
  new PLUM scenario LU at
  `/media/bampoh-d/lpjg_input/input/LU/plum_harm_lu/SSP<n>_RCP<r>/s1.HILDA+_remap_v10_old_62892_gL.harm.allow_unveg.forLPJG/`
  in coupled mode (`-input imogencfx`).

This avoids LU file concatenation and lets each scenario re-use the
common 2020 state.

## Coupling modes

Each scenario directory's `imogen_intermediary.ins` declares a
`coupling_mode` parameter:

- `coupling_mode "tight"` (default) — closed-loop two-way feedback;
  LPJG year N's NEE/CH4/N2O feed into IMOGEN year N+1's climate.
- `coupling_mode "prescribed"` — `FILE_LPJG_FLUX` etc. point at
  pre-computed static reference files; useful for sensitivity studies
  isolating climate-pattern or atmospheric-parameter effects from
  LPJG perturbations.
- `coupling_mode "loose"` — IMOGEN runs once standalone; LPJG reads
  pre-baked climate. Legacy compatibility.

The active mode is printed in the run-log startup banner (per the
`scripts/run_coupled.sh` discipline of §I.D.5).
