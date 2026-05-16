#!/usr/bin/env python3
"""
run_all.py — End-to-end pipeline driver
========================================

Runs all four components of the IMOGEN GHG Controller in dependency order.
Each individual script is independently runnable; this driver is purely a
convenience orchestrator.

Usage
-----
    python run_all.py                    # run everything
    python run_all.py --component A      # just Component A
    python run_all.py --component B C    # B then C
    python run_all.py --skip-plots       # processing only, no figures
    python run_all.py --dry-run          # print steps without executing
    python run_all.py --help

The runner respects the dependency graph: A → B → C → D. If you ask for C
without first having A and B outputs in place, the runner will still execute
C but Component C's scripts will fail loudly because the inputs aren't there.

Each component is a list of (script_path, label) tuples. The runner executes
each tuple via `subprocess.run(['python3', script_path], check=True)`.

Exit codes
----------
    0 — all requested components completed successfully
    1 — a script failed; the partial pipeline state is left intact

Logs are written to stderr. Use `--verbose` for sub-process stdout streaming.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root resolution (the src/ directory determines our root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
SRC = PROJECT_ROOT / 'src'

# ---------------------------------------------------------------------------
# Pipeline definition: ordered list of (script, kind, label) per component.
# kind ∈ {'processing', 'plotting'} — used by --skip-plots filtering.
# ---------------------------------------------------------------------------
COMPONENT_A = [
    # Historical sectors — six independent processing+plotting pairs
    ('component_a_anthropogenic/historical/ch4_ef_processing.py', 'processing', 'A historical: CH4 enteric fermentation'),
    ('component_a_anthropogenic/historical/ch4_ef_plotting.py',   'plotting',   'A historical: CH4 EF plot'),
    ('component_a_anthropogenic/historical/ch4_mm_processing.py', 'processing', 'A historical: CH4 manure management'),
    ('component_a_anthropogenic/historical/ch4_mm_plotting.py',   'plotting',   'A historical: CH4 MM plot'),
    ('component_a_anthropogenic/historical/ch4_rice_processing.py', 'processing', 'A historical: CH4 rice cultivation'),
    ('component_a_anthropogenic/historical/ch4_rice_plotting.py',   'plotting',   'A historical: CH4 rice plot'),
    ('component_a_anthropogenic/historical/n2o_mm_processing.py',  'processing', 'A historical: N2O manure management'),
    ('component_a_anthropogenic/historical/n2o_mm_plotting.py',    'plotting',   'A historical: N2O MM plot'),
    ('component_a_anthropogenic/historical/n2o_ms_processing.py',  'processing', 'A historical: N2O managed soils'),
    ('component_a_anthropogenic/historical/n2o_ms_plotting.py',    'plotting',   'A historical: N2O MS plot'),
    ('component_a_anthropogenic/historical/n2o_synfert_processing.py', 'processing', 'A historical: N2O synthetic fertilizers'),
    ('component_a_anthropogenic/historical/n2o_synfert_plotting.py',   'plotting',   'A historical: N2O syn-fert plot'),

    # Scenarios — livestock anchor first, then five sector pipelines
    ('component_a_anthropogenic/scenarios/00_scenario_livestock_anchor.py',     'processing', 'A scenario: 00 livestock anchor'),
    ('component_a_anthropogenic/scenarios/01_scenario_ch4_ef_processing.py',    'processing', 'A scenario: 01 CH4 EF'),
    ('component_a_anthropogenic/scenarios/01_scenario_ch4_ef_plotting.py',      'plotting',   'A scenario: 01 CH4 EF plot'),
    ('component_a_anthropogenic/scenarios/02_scenario_ch4_mm_processing.py',    'processing', 'A scenario: 02 CH4 MM'),
    ('component_a_anthropogenic/scenarios/02_scenario_ch4_mm_plotting.py',      'plotting',   'A scenario: 02 CH4 MM plot'),
    ('component_a_anthropogenic/scenarios/03_scenario_n2o_mm_processing.py',    'processing', 'A scenario: 03 N2O MM'),
    ('component_a_anthropogenic/scenarios/03_scenario_n2o_mm_plotting.py',      'plotting',   'A scenario: 03 N2O MM plot'),
    ('component_a_anthropogenic/scenarios/04_scenario_n2o_synfert_processing.py', 'processing', 'A scenario: 04 N2O syn-fert'),
    ('component_a_anthropogenic/scenarios/04_scenario_n2o_synfert_plotting.py',   'plotting',   'A scenario: 04 N2O syn-fert plot'),
    ('component_a_anthropogenic/scenarios/05_scenario_n2o_ms_processing.py',    'processing', 'A scenario: 05 N2O MS'),
    ('component_a_anthropogenic/scenarios/05_scenario_n2o_ms_plotting.py',      'plotting',   'A scenario: 05 N2O MS plot'),
    ('component_a_anthropogenic/scenarios/06_scenario_ch4_rice_processing.py',  'processing', 'A scenario: 06 CH4 rice'),
    ('component_a_anthropogenic/scenarios/06_scenario_ch4_rice_plotting.py',    'plotting',   'A scenario: 06 CH4 rice plot'),

    # RCMIP substitution and comparison plots
    ('component_a_anthropogenic/rcmip_substitution/rcmip_substitution_processing.py', 'processing', 'A: RCMIP Tier-1 substitution'),
    ('component_a_anthropogenic/rcmip_substitution/rcmip_comparison1_plotting.py',    'plotting',   'A: RCMIP comparison 1 (agri sectors)'),
    ('component_a_anthropogenic/rcmip_substitution/rcmip_comparison2_plotting.py',    'plotting',   'A: RCMIP comparison 2 (full totals)'),
]

# [B28 fix 2026-05-16: COMPONENT_B order corrected so that
#  lpjg_combined_and_fair_processing.py runs BEFORE lpjg_historical_plotting.py.
#  ROOT CAUSE: lpjg_historical_plotting.py:162 reads lpjg_ch4_combined_annual.csv
#  and needs the 14-column schema (Year + Wetland_TgCH4 + IFW_*best/lo/hi +
#  Combined_*best/lo/hi + DCC_*best/lo/hi + CombinedDCC_*best/lo/hi). ONLY
#  lpjg_combined_and_fair_processing.py writes that full 14-col schema (at
#  line 108). lpjg_historical_processing.py SECTION 5 (lines 296-322) writes
#  a SIMPLER 8-column variant (NO DCC columns; predates GMB 2025 DCC machinery)
#  to the same path — that schema divergence is tracked as B29 audit item for
#  future cleanup. Reordering here restores the documented design intent (per
#  combined_and_fair_processing.py docstring: "This standalone helper exists
#  for fast iteration on plot logic without re-streaming the large .gz
#  inputs"). The helper's 14-col write OVERWRITES the simpler 8-col file
#  produced by historical_processing SECTION 5 before the plotter consumes
#  it. Discovered during B19 Phase 1 reproducibility re-run when the
#  from-scratch run failed at step 30/43 with KeyError: 'CombinedDCC_TgCH4_best'.
#  Bug is pre-existing in version_A's identical copy of run_all.py too. -DKB]
COMPONENT_B = [
    ('component_b_natural/historical/lpjg_historical_processing.py',   'processing', 'B historical: LPJ-GUESS streaming 1901-2020'),
    ('component_b_natural/full_trajectory/lpjg_combined_and_fair_processing.py', 'processing', 'B: combined CH4 + FAIR-ERF baseline (B28: must run BEFORE historical_plotting; overwrites simpler 8-col file from historical_processing SECTION 5 with full 14-col DCC schema)'),
    ('component_b_natural/historical/lpjg_historical_plotting.py',     'plotting',   'B historical: LPJ-GUESS 4-panel plot'),
    ('component_b_natural/scenarios/lpjg_scenario_processing.py',      'processing', 'B scenarios: LPJ-GUESS streaming 2021-2100'),
    ('component_b_natural/full_trajectory/lpjg_historical_scenario_plotting.py', 'plotting',   'B: 1901-2100 full-trajectory plot'),
]

COMPONENT_C = [
    ('component_c_integration/rcmip_co2_processing.py',                    'processing', 'C: RCMIP CO2 EFOS extraction'),
    ('component_c_integration/integrated_emissions_processing.py',         'processing', 'C: integration assembly'),
    ('component_c_integration/integrated_emissions_plotting.py',           'plotting',   'C: integrated trajectories plot'),
    ('component_c_integration/external_comparators_processing.py',         'processing', 'C: top-down budget comparators'),
    ('component_c_integration/external_comparators_plotting.py',           'plotting',   'C: top-down comparator plot'),
    ('component_c_integration/hybrid_comparator_processing.py',            'processing', 'C: hybrid comparator (Option B)'),
    ('component_c_integration/hybrid_comparator_plotting.py',              'plotting',   'C: hybrid comparator plot'),
    ('component_c_integration/conventional_comparator_processing.py',      'processing', 'C: conventional comparator (Option A)'),
    ('component_c_integration/conventional_comparator_plotting.py',        'plotting',   'C: conventional comparator plot'),
]

COMPONENT_D = [
    ('component_d_imogen_export/imogen_inputs_export.py', 'processing', 'D: IMOGEN-input CSV export'),
]

COMPONENTS = {
    'A': COMPONENT_A,
    'B': COMPONENT_B,
    'C': COMPONENT_C,
    'D': COMPONENT_D,
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_one(script_rel_path, label, dry_run=False, verbose=False):
    """Execute one script. Returns True on success."""
    script_path = SRC / script_rel_path
    if not script_path.is_file():
        print(f'  ✗ MISSING: {script_path}', file=sys.stderr)
        return False

    print(f'  → {label}', file=sys.stderr)
    if dry_run:
        print(f'    (dry-run; would execute: {script_path})', file=sys.stderr)
        return True

    t0 = time.time()
    try:
        if verbose:
            subprocess.run(['python3', str(script_path)], check=True)
        else:
            r = subprocess.run(['python3', str(script_path)],
                               capture_output=True, text=True, check=True)
        elapsed = time.time() - t0
        print(f'    ✓ done in {elapsed:.1f}s', file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - t0
        print(f'    ✗ FAILED after {elapsed:.1f}s', file=sys.stderr)
        if e.stdout:
            print('    stdout:', file=sys.stderr)
            for line in (e.stdout or '').splitlines()[-20:]:
                print(f'      {line}', file=sys.stderr)
        if e.stderr:
            print('    stderr:', file=sys.stderr)
            for line in (e.stderr or '').splitlines()[-20:]:
                print(f'      {line}', file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser(
        description='Run the IMOGEN GHG Controller pipeline end-to-end.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument('--component', '-c', nargs='+',
                    choices=['A', 'B', 'C', 'D', 'all'],
                    default=['all'],
                    help='Component(s) to run (default: all)')
    ap.add_argument('--skip-plots', action='store_true',
                    help='Skip plotting scripts (processing only)')
    ap.add_argument('--dry-run', '-n', action='store_true',
                    help='Print steps without executing them')
    ap.add_argument('--verbose', '-v', action='store_true',
                    help='Stream sub-process stdout/stderr to console')
    args = ap.parse_args()

    # Resolve component list
    if 'all' in args.component:
        comps = ['A', 'B', 'C', 'D']
    else:
        comps = list(args.component)

    print(f'\n══ IMOGEN GHG Controller — pipeline driver ══', file=sys.stderr)
    print(f'  components: {" → ".join(comps)}', file=sys.stderr)
    print(f'  skip plots: {args.skip_plots}', file=sys.stderr)
    print(f'  dry run:    {args.dry_run}', file=sys.stderr)
    print('', file=sys.stderr)

    # [Step 11 of unified-codebase rebuild: output dir tree is auto-created
    #  by src/shared/paths.py on first import (which happens in every script
    #  via its bootstrap block). No explicit call needed here; the
    #  paths.py auto-call is idempotent (mkdir parents=True exist_ok=True)
    #  and doesn't fire when IMOGEN_GHG_NO_AUTO_MKDIR=1 is set.
    #  - DKB 2026-05-07]

    t_start = time.time()
    n_run = n_ok = 0
    for comp in comps:
        steps = COMPONENTS[comp]
        if args.skip_plots:
            steps = [s for s in steps if s[1] != 'plotting']
        print(f'┌── Component {comp} ── ({len(steps)} steps)', file=sys.stderr)
        for rel, kind, label in steps:
            n_run += 1
            ok = run_one(rel, label, dry_run=args.dry_run, verbose=args.verbose)
            if ok:
                n_ok += 1
            else:
                print(f'│', file=sys.stderr)
                print(f'└── pipeline aborted after failure in {comp}', file=sys.stderr)
                sys.exit(1)
        print(f'└── Component {comp} complete', file=sys.stderr)
        print('', file=sys.stderr)

    total = time.time() - t_start
    print(f'══ pipeline complete: {n_ok}/{n_run} steps in {total:.1f}s ══', file=sys.stderr)


if __name__ == '__main__':
    main()
