"""
lpjg_scenario_processing.py
================================
Processes LPJ-GUESS scenario natural-emission output (2021-2100) into
global annual totals, one scenario at a time, with appended writes to
a single combined long-format CSV per gas.

Forcing: PLUMv2 SSP-RCP scenario land use (2021-2100), harmonized with
         HILDA+v2 historic (1900-2020) via the LUH2 protocol.

INPUT FILES (per scenario)
--------------------------
Each scenario lives in its own directory, e.g.
  {LPJG_SCEN_DIR}/ssp1_rcp26/
Containing three .gz files with internal structure identical to the
historical files:
  lpjg_cflux.out_<scen>.gz   — CO2 carbon fluxes (kg C m⁻² yr⁻¹)
  lpjg_mch4.out_<scen>.gz    — CH4 wetland fluxes (g CH4 m⁻² month⁻¹)
  lpjg_ngases.out_<scen>.gz  — N gas fluxes (kg N ha⁻¹ yr⁻¹)

Scenario tag inferred from directory basename, removing underscores:
  ssp1_rcp26 -> 'ssp1rcp26'

DATA SCALE
----------
80 years × 62,538 land grid cells = 5,000,960 data rows per file.
Streamed with `zcat` (same reasoning as historical processor).

UNIT-CONVERSION PIPELINE (identical to historical)
--------------------------------------------------
  CO2:  Σ(val_i × area_i) [kg C yr⁻¹]  ÷ 1e12 → Pg C yr⁻¹
  CH4:  Σ(annual_i × area_i) [g CH4 yr⁻¹] ÷ 1e12 → Tg CH4 yr⁻¹
  N2O:  Σ(val_i × area_i ÷ 1e4) [kg N yr⁻¹] ÷ 1e9 → Tg N yr⁻¹
        × 44/28 → Tg N2O yr⁻¹

CELL AREA
---------
  area(lat) = (0.5° × π/180)² × R_Earth² × cos(lat_rad)
  R_Earth = 6.371 × 10⁶ m

OUTPUT FILES (in OUT_DIR; long-format with Scenario + Year)
-----------------------------------------------------------
  lpjg_co2_annual_scenarios.csv         CO2 components (Pg C/yr)
  lpjg_ch4_annual_scenarios.csv         CH4 (Tg CH4/yr)
  lpjg_ch4_combined_annual_scenarios.csv  + GMB IFW + DCC adjustments
  lpjg_n2o_annual_scenarios.csv         N gas species (Tg N/yr; Tg N2O/yr)

If a scenario already exists in any output CSV, its rows are replaced.
This makes incremental processing safe: re-running with a single scenario
will not touch the others.

USAGE
-----
  python3 lpjg_scenario_processing.py <scenario_dir>
  e.g.
  python3 lpjg_scenario_processing.py {LPJG_SCEN_DIR}/ssp1_rcp26

Or from another script:
  process_scenario((str(LPJG_SCEN_DIR) + '/ssp1_rcp26'))
"""


# ---------------------------------------------------------------------------
# Project bootstrap: add project root to sys.path so we can import shared/
# ---------------------------------------------------------------------------
import sys as _sys
from pathlib import Path as _Path
_PROJ_ROOT = _Path(__file__).resolve()
while _PROJ_ROOT.name and not (_PROJ_ROOT / 'src').is_dir():
    if _PROJ_ROOT.parent == _PROJ_ROOT:
        break
    _PROJ_ROOT = _PROJ_ROOT.parent
if str(_PROJ_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_PROJ_ROOT))
from src.shared.paths import (
    LPJG_SCEN_DIR, OUT_B_DATA, OUT_B_FIGS, OUT_B_SUMMARIES,
)

import os
import sys
import time
import subprocess
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_B_DATA))
os.makedirs(OUT_DIR, exist_ok=True)

R_EARTH = 6.371e6
MW_N2O  = 44.0 / 28.0
MW_CH4_C = 12.0 / 16.0

# GMB 2025 inland-freshwater + DCC, applied uniformly to scenarios
GMB_IFW_BEST = 112.0; GMB_IFW_LO =  49.0; GMB_IFW_HI = 202.0
GMB_DCC_BEST = -23.0; GMB_DCC_LO =  -9.0; GMB_DCC_HI = -36.0

CO2_COLS = ['Manure','Veg','Repr','Soil','Fire','Est','Seed',
            'Harvest','LU_ch','Slow_h','NEE']
N_COLS = ['NH3_fire','NH3_soil','NOx_fire','NOx_soil',
          'N2O_fire','N2O_soil','N2_fire','N2_soil','Total']
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug',
          'Sep','Oct','Nov','Dec']

def cell_area_m2(lat_deg):
    return (0.5 * np.pi / 180.0) ** 2 * R_EARTH**2 * np.cos(np.radians(lat_deg))

def stream(gz_path):
    p = subprocess.Popen(['zcat', gz_path], stdout=subprocess.PIPE, bufsize=65536)
    header = p.stdout.readline().decode().split()
    return p, header

def banner(msg):
    print('\n' + '=' * 72 + f'\n{msg}\n' + '=' * 72, flush=True)


# ---------------------------------------------------------------------------
# Per-gas streaming routines (return per-year dictionaries / DataFrames)
# ---------------------------------------------------------------------------

def stream_co2(gz_path):
    """Stream cflux file → DataFrame [Year + 11 component fluxes in Pg C/yr]."""
    acc = {}
    p, hdr = stream(gz_path)
    ci = {c: hdr.index(c) for c in ['Lon','Lat','Year'] + CO2_COLS}
    n = 0
    for line in p.stdout:
        v = line.decode().split()
        if len(v) < len(hdr): continue
        lat = float(v[ci['Lat']]); yr = int(float(v[ci['Year']]))
        a = cell_area_m2(lat)
        if yr not in acc: acc[yr] = {c: 0.0 for c in CO2_COLS}
        for c in CO2_COLS:
            acc[yr][c] += float(v[ci[c]]) * a
        n += 1
    p.wait()
    rows = [{'Year': yr, **{f'{c}_PgC': acc[yr][c]/1e12 for c in CO2_COLS}}
            for yr in sorted(acc)]
    return pd.DataFrame(rows), n

def stream_ch4(gz_path):
    """Stream mch4 file → DataFrame [Year, CH4_TgCH4]."""
    acc = {}
    p, hdr = stream(gz_path)
    li, yi = hdr.index('Lat'), hdr.index('Year')
    mi = [hdr.index(m) for m in MONTHS]
    n = 0
    for line in p.stdout:
        v = line.decode().split()
        if len(v) < len(hdr): continue
        lat = float(v[li]); yr = int(float(v[yi])); a = cell_area_m2(lat)
        annual_g_m2 = sum(float(v[i]) for i in mi)
        acc[yr] = acc.get(yr, 0.0) + annual_g_m2 * a
        n += 1
    p.wait()
    return pd.DataFrame([{'Year': y, 'CH4_TgCH4': v/1e12}
                         for y, v in sorted(acc.items())]), n

def stream_n2o(gz_path):
    """Stream ngases file → DataFrame [Year + 11 species columns]."""
    acc = {}
    p, hdr = stream(gz_path)
    ix = {c: hdr.index(c) for c in ['Lon','Lat','Year'] + N_COLS}
    n = 0
    for line in p.stdout:
        v = line.decode().split()
        if len(v) < len(hdr): continue
        lat = float(v[ix['Lat']]); yr = int(float(v[ix['Year']])); a = cell_area_m2(lat)
        if yr not in acc: acc[yr] = {c: 0.0 for c in N_COLS}
        for c in N_COLS:
            acc[yr][c] += float(v[ix[c]]) * a
        n += 1
    p.wait()
    rows = []
    for yr in sorted(acc):
        row = {'Year': yr}
        for c in N_COLS:
            tg_N = acc[yr][c] / 1e4 / 1e9
            row[f'{c}_TgN'] = tg_N
            if 'N2O' in c:
                row[f'{c}_TgN2O'] = tg_N * MW_N2O
        rows.append(row)
    df = pd.DataFrame(rows)
    order = ['Year','NH3_fire_TgN','NH3_soil_TgN','NOx_fire_TgN','NOx_soil_TgN',
             'N2O_fire_TgN','N2O_fire_TgN2O','N2O_soil_TgN','N2O_soil_TgN2O',
             'N2_fire_TgN','N2_soil_TgN','Total_TgN']
    return df[order], n


# ---------------------------------------------------------------------------
# Long-format CSV append/replace logic
# ---------------------------------------------------------------------------

def _upsert_scenario_rows(out_path, scenario_tag, df_new):
    """Insert df_new (with Scenario column added) into out_path.
       If scenario_tag already exists, replace those rows."""
    df_new = df_new.copy()
    df_new.insert(0, 'Scenario', scenario_tag)
    if os.path.exists(out_path):
        df_old = pd.read_csv(out_path)
        df_old = df_old[df_old['Scenario'] != scenario_tag]
        combined = pd.concat([df_old, df_new], ignore_index=True)
    else:
        combined = df_new
    combined = combined.sort_values(['Scenario', 'Year']).reset_index(drop=True)
    combined.to_csv(out_path, index=False)
    return combined


# ---------------------------------------------------------------------------
# Top-level scenario processor
# ---------------------------------------------------------------------------

def process_scenario(scenario_dir):
    """Stream all three .gz files for the given scenario directory and
    update the four scenario long-format CSVs in OUT_DIR."""
    scen_basename = os.path.basename(os.path.normpath(scenario_dir))
    scenario_tag  = scen_basename.replace('_', '')   # 'ssp1_rcp26' -> 'ssp1rcp26'

    cflux_gz  = os.path.join(scenario_dir, f'lpjg_cflux.out_{scenario_tag}.gz')
    mch4_gz   = os.path.join(scenario_dir, f'lpjg_mch4.out_{scenario_tag}.gz')
    ngases_gz = os.path.join(scenario_dir, f'lpjg_ngases.out_{scenario_tag}.gz')

    for f in [cflux_gz, mch4_gz, ngases_gz]:
        if not os.path.exists(f):
            raise FileNotFoundError(f'Missing scenario file: {f}')

    banner(f'PROCESSING SCENARIO: {scen_basename} (tag = {scenario_tag})')

    # CO2
    print('[CO2] streaming ...', flush=True); t0 = time.time()
    df_co2, n_co2 = stream_co2(cflux_gz)
    print(f'  {n_co2:,} rows in {time.time()-t0:.0f}s; '
          f'years {df_co2.Year.min()}-{df_co2.Year.max()}', flush=True)
    _upsert_scenario_rows(os.path.join(OUT_DIR, 'lpjg_co2_annual_scenarios.csv'),
                          scenario_tag, df_co2)

    # CH4
    print('[CH4] streaming ...', flush=True); t0 = time.time()
    df_ch4, n_ch4 = stream_ch4(mch4_gz)
    print(f'  {n_ch4:,} rows in {time.time()-t0:.0f}s', flush=True)
    _upsert_scenario_rows(os.path.join(OUT_DIR, 'lpjg_ch4_annual_scenarios.csv'),
                          scenario_tag, df_ch4)

    # CH4 combined (with GMB IFW & DCC)
    df_cmb = df_ch4.rename(columns={'CH4_TgCH4': 'Wetland_TgCH4'}).copy()
    df_cmb['IFW_TgCH4_best'] = GMB_IFW_BEST
    df_cmb['IFW_TgCH4_lo']   = GMB_IFW_LO
    df_cmb['IFW_TgCH4_hi']   = GMB_IFW_HI
    df_cmb['Combined_TgCH4_best'] = df_cmb['Wetland_TgCH4'] + GMB_IFW_BEST
    df_cmb['Combined_TgCH4_lo']   = df_cmb['Wetland_TgCH4'] + GMB_IFW_LO
    df_cmb['Combined_TgCH4_hi']   = df_cmb['Wetland_TgCH4'] + GMB_IFW_HI
    df_cmb['DCC_TgCH4_best']      = GMB_DCC_BEST
    df_cmb['DCC_TgCH4_lo']        = GMB_DCC_LO
    df_cmb['DCC_TgCH4_hi']        = GMB_DCC_HI
    df_cmb['CombinedDCC_TgCH4_best'] = df_cmb['Wetland_TgCH4'] + GMB_IFW_BEST + GMB_DCC_BEST
    df_cmb['CombinedDCC_TgCH4_lo']   = df_cmb['Wetland_TgCH4'] + GMB_IFW_LO   + GMB_DCC_HI
    df_cmb['CombinedDCC_TgCH4_hi']   = df_cmb['Wetland_TgCH4'] + GMB_IFW_HI   + GMB_DCC_LO
    _upsert_scenario_rows(os.path.join(OUT_DIR, 'lpjg_ch4_combined_annual_scenarios.csv'),
                          scenario_tag, df_cmb)

    # N2O
    print('[N2O] streaming ...', flush=True); t0 = time.time()
    df_n2o, n_n2o = stream_n2o(ngases_gz)
    print(f'  {n_n2o:,} rows in {time.time()-t0:.0f}s', flush=True)
    _upsert_scenario_rows(os.path.join(OUT_DIR, 'lpjg_n2o_annual_scenarios.csv'),
                          scenario_tag, df_n2o)

    # Quick summary
    r2050 = df_co2[df_co2.Year==2050].iloc[0]
    r2100 = df_co2[df_co2.Year==2100].iloc[0]
    print(f'\n  CO2 NEE  2050={r2050["NEE_PgC"]:+.3f}  2100={r2100["NEE_PgC"]:+.3f} Pg C/yr')
    print(f'  CH4 wet  2050={df_ch4[df_ch4.Year==2050]["CH4_TgCH4"].values[0]:.2f}  '
          f'2100={df_ch4[df_ch4.Year==2100]["CH4_TgCH4"].values[0]:.2f} Tg CH4/yr')
    print(f'  N2O soil 2050={df_n2o[df_n2o.Year==2050]["N2O_soil_TgN2O"].values[0]:.2f}  '
          f'2100={df_n2o[df_n2o.Year==2100]["N2O_soil_TgN2O"].values[0]:.2f} Tg N2O/yr')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        for d in sys.argv[1:]:
            process_scenario(d)
    else:
        # Default: process all directories in {LPJG_SCEN_DIR}
        SCEN_ROOT = str(LPJG_SCEN_DIR)
        for d in sorted(os.listdir(SCEN_ROOT)):
            full = os.path.join(SCEN_ROOT, d)
            if os.path.isdir(full):
                process_scenario(full)
    print('\nDone.\n')
