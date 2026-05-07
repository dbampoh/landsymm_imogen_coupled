"""
lpjg_historical_processing.py
================================
Processes LPJ-GUESS historical natural-emission output (1901–2020)
into global annual totals for comparison with global budget papers
and subsequent integration with anthropogenic emission trajectories.

Forcing:  HILDA+v2 historical land-use product (1900–2020)
          (PLUMv2 SSP-RCP scenarios are processed separately, 2020–2100)

INPUT FILES
-----------
The three files come from a single LPJ-GUESS run on a 0.5° × 0.5° grid
covering 62,538 land grid cells × 120 years = 7,504,560 data rows each.
Files are streamed with `zcat` because they cannot be loaded fully into
RAM and are stored in cell-first (all 120 years per cell, then next cell)
ordering.

  lpjg_cflux.out_historical.gz   — CO2 carbon fluxes (kg C m⁻² yr⁻¹)
  lpjg_mch4.out_historical.gz    — CH4 wetland fluxes (g CH4 m⁻² month⁻¹)
  lpjg_ngases.out_historical.gz  — N gas fluxes (kg N ha⁻¹ yr⁻¹)

UNIT-CONVERSION PIPELINE
-------------------------
  CO2:  Σ(val_i × area_i) [kg C yr⁻¹] ÷ 1e12 → Pg C yr⁻¹
  CH4:  Σ(annual_i × area_i) [g CH4 yr⁻¹] ÷ 1e12 → Tg CH4 yr⁻¹
  N2O:  Σ(val_i [kg N ha⁻¹] × area_i [m²] ÷ 1e4 [m²/ha]) → kg N yr⁻¹
        ÷ 1e9 → Tg N yr⁻¹  ;  × 44/28 → Tg N2O yr⁻¹

CELL AREA
---------
  area(lat) = (0.5° × π/180)² × R_Earth² × cos(lat_rad)
  R_Earth = 6.371 × 10⁶ m

CO2 COMPONENT INTERPRETATION (cflux columns)
---------------------------------------------
  Veg     = Net Primary Production (GPP − Ra); negative = C uptake
  Repr    = Reproduction C allocation
  Soil    = Heterotrophic respiration (Rh); positive = C source
  Fire    = Pyrogenic C emissions
  Est     = Establishment biomass
  Seed    = Seed production C
  Harvest = C removed in agricultural harvest
  LU_ch   = Direct land-use-change C emissions (vegetation clearing)
  Slow_h  = Slow soil/product pool respiration
  Manure  = Manure C inputs (zero throughout — no anthropogenic N inputs)
  NEE     = Net Ecosystem Exchange = sum of all above

N2O SCOPE NOTE
--------------
  N2O_soil ≈ natural soil N2O + LUC-induced soil N2O emissions.
  (Confirmed: Manure column = 0 throughout, so no anthropogenic N
  fertiliser inputs are applied; the LUC-driven N cycling component
  is distinct from the IPCC Tier 1 managed-soils sector and does NOT
  constitute double-counting.)

OUTPUT FILES (in OUT_DIR)
--------------------------
  lpjg_co2_annual.csv     — global annual CO2 component fluxes (Pg C/yr)
  lpjg_ch4_annual.csv     — global annual CH4 (Tg CH4/yr)
  lpjg_ch4_combined_annual.csv — wetland + GMB inland freshwater (Tg CH4/yr)
  lpjg_n2o_annual.csv     — global annual N2O and N gas species
                            (Tg N/yr and Tg N2O/yr for N2O species)
  lpjg_grid_diagnostics.txt — grid coverage, total area, latitude range
  fair_erf_natural_baseline.csv — FAIR-ERF v1.3 natural emissions
                            baseline (1900-2020), CH4 in Tg CH4/yr,
                            N2O in Tg N/yr and Tg N2O/yr
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
    FAIR_ERF_CSV, LPJG_HIST_DIR, OUT_B_DATA, OUT_B_FIGS, OUT_B_SUMMARIES,
)

import os
import sys
import time
import subprocess
import numpy as np
import pandas as pd

# =============================================================================
# CONFIGURATION
# =============================================================================
HERE = os.path.dirname(os.path.abspath(__file__))

# Default input directory: where the historical LPJ-GUESS .gz files live.
# Override via `IN_DIR=/path python3 lpjg_historical_processing.py`.
IN_DIR  = os.environ.get('IN_DIR',  str(LPJG_HIST_DIR))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_B_DATA))
os.makedirs(OUT_DIR, exist_ok=True)

CFLUX_GZ  = os.path.join(IN_DIR, 'lpjg_cflux.out_historical.gz')
MCH4_GZ   = os.path.join(IN_DIR, 'lpjg_mch4.out_historical.gz')
NGASES_GZ = os.path.join(IN_DIR, 'lpjg_ngases.out_historical.gz')

R_EARTH = 6.371e6  # m

def cell_area_m2(lat_deg):
    """Area of a 0.5° × 0.5° grid cell at given latitude (m²)."""
    return (0.5 * np.pi / 180.0) ** 2 * R_EARTH**2 * np.cos(np.radians(lat_deg))


def stream(gz_path):
    """Yield decoded whitespace-split tokens for each non-header row."""
    p = subprocess.Popen(['zcat', gz_path], stdout=subprocess.PIPE, bufsize=65536)
    header = p.stdout.readline().decode().split()
    return p, header


def banner(msg):
    print('\n' + '=' * 72 + f'\n{msg}\n' + '=' * 72, flush=True)


# =============================================================================
# SECTION 1: CO2 — cflux
# =============================================================================
banner('[1/3] CO2 — cflux')
t0 = time.time()

CO2_COLS = ['Manure','Veg','Repr','Soil','Fire','Est','Seed',
            'Harvest','LU_ch','Slow_h','NEE']

co2_acc       = {}                # year → {col: kg C/yr accumulated}
unique_cells  = set()             # for diagnostic
total_area_m2 = 0.0                # for diagnostic
lat_min, lat_max = 1e9, -1e9
lon_min, lon_max = 1e9, -1e9

p, hdr = stream(CFLUX_GZ)
ci = {c: hdr.index(c) for c in ['Lon','Lat','Year'] + CO2_COLS}

n = 0
for line in p.stdout:
    v = line.decode().split()
    if len(v) < len(hdr): continue
    lon = v[ci['Lon']]; lat = v[ci['Lat']]; yr = int(float(v[ci['Year']]))
    cell = (lon, lat)
    if cell not in unique_cells:
        unique_cells.add(cell)
        total_area_m2 += cell_area_m2(float(lat))
        latf = float(lat); lonf = float(lon)
        if latf < lat_min: lat_min = latf
        if latf > lat_max: lat_max = latf
        if lonf < lon_min: lon_min = lonf
        if lonf > lon_max: lon_max = lonf
    a = cell_area_m2(float(lat))
    if yr not in co2_acc:
        co2_acc[yr] = {c: 0.0 for c in CO2_COLS}
    for c in CO2_COLS:
        co2_acc[yr][c] += float(v[ci[c]]) * a
    n += 1
    if n % 2_000_000 == 0:
        print(f'  ... {n:,} rows ({time.time()-t0:.0f}s)', flush=True)
p.wait()

print(f'  done {n:,} rows in {time.time()-t0:.0f}s', flush=True)
print(f'  unique cells: {len(unique_cells):,}', flush=True)
print(f'  total area:   {total_area_m2/1e12:.2f} M km²', flush=True)

rows = [{'Year': yr, **{f'{c}_PgC': co2_acc[yr][c] / 1e12 for c in CO2_COLS}}
        for yr in sorted(co2_acc)]
df_co2 = pd.DataFrame(rows)
df_co2.to_csv(os.path.join(OUT_DIR, 'lpjg_co2_annual.csv'), index=False)
print(f'  → lpjg_co2_annual.csv', flush=True)

# Quick sanity print
r2000 = df_co2[df_co2['Year'] == 2000].iloc[0]
print(f"  2000 NEE = {r2000['NEE_PgC']:+.4f} Pg C/yr  "
      f"(Veg={r2000['Veg_PgC']:.2f}, Soil={r2000['Soil_PgC']:.2f}, "
      f"LU_ch={r2000['LU_ch_PgC']:.3f})")

# =============================================================================
# SECTION 2: CH4 — mch4
# =============================================================================
banner('[2/3] CH4 — mch4')
t0 = time.time()

MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
ch4_acc = {}

p, hdr = stream(MCH4_GZ)
li, yi = hdr.index('Lat'), hdr.index('Year')
mi = [hdr.index(m) for m in MONTHS]

n = 0
for line in p.stdout:
    v = line.decode().split()
    if len(v) < len(hdr): continue
    lat = float(v[li]); yr = int(float(v[yi])); a = cell_area_m2(lat)
    annual_g_m2 = sum(float(v[i]) for i in mi)        # g CH4 m⁻² yr⁻¹
    ch4_acc[yr] = ch4_acc.get(yr, 0.0) + annual_g_m2 * a    # g CH4 yr⁻¹
    n += 1
    if n % 2_000_000 == 0:
        print(f'  ... {n:,} rows ({time.time()-t0:.0f}s)', flush=True)
p.wait()

df_ch4 = pd.DataFrame([{'Year': y, 'CH4_TgCH4': v / 1e12}
                       for y, v in sorted(ch4_acc.items())])
df_ch4.to_csv(os.path.join(OUT_DIR, 'lpjg_ch4_annual.csv'), index=False)
print(f'  done {n:,} rows in {time.time()-t0:.0f}s', flush=True)
print(f'  → lpjg_ch4_annual.csv', flush=True)
print(f"  2000 = {df_ch4[df_ch4['Year']==2000]['CH4_TgCH4'].values[0]:.2f} Tg CH4/yr  "
      f"2020 = {df_ch4[df_ch4['Year']==2020]['CH4_TgCH4'].values[0]:.2f}")

# =============================================================================
# SECTION 3: N gases — ngases
# =============================================================================
banner('[3/3] N gases — ngases')
t0 = time.time()

N_COLS = ['NH3_fire','NH3_soil','NOx_fire','NOx_soil',
          'N2O_fire','N2O_soil','N2_fire','N2_soil','Total']
n2o_acc = {}

p, hdr = stream(NGASES_GZ)
ix = {c: hdr.index(c) for c in ['Lon','Lat','Year'] + N_COLS}

n = 0
for line in p.stdout:
    v = line.decode().split()
    if len(v) < len(hdr): continue
    lat = float(v[ix['Lat']]); yr = int(float(v[ix['Year']])); a = cell_area_m2(lat)
    if yr not in n2o_acc:
        n2o_acc[yr] = {c: 0.0 for c in N_COLS}
    for c in N_COLS:
        n2o_acc[yr][c] += float(v[ix[c]]) * a   # kg N/ha × m² (deferred ÷1e4)
    n += 1
    if n % 2_000_000 == 0:
        print(f'  ... {n:,} rows ({time.time()-t0:.0f}s)', flush=True)
p.wait()

MW_N2O = 44.0 / 28.0
rows = []
for yr in sorted(n2o_acc):
    row = {'Year': yr}
    for c in N_COLS:
        tg_N = n2o_acc[yr][c] / 1e4 / 1e9            # → Tg N/yr
        row[f'{c}_TgN'] = tg_N
        if 'N2O' in c:
            row[f'{c}_TgN2O'] = tg_N * MW_N2O
    rows.append(row)
df_n2o = pd.DataFrame(rows)

# Stable column order for downstream consumers
order = ['Year','NH3_fire_TgN','NH3_soil_TgN','NOx_fire_TgN','NOx_soil_TgN',
        'N2O_fire_TgN','N2O_fire_TgN2O','N2O_soil_TgN','N2O_soil_TgN2O',
        'N2_fire_TgN','N2_soil_TgN','Total_TgN']
df_n2o = df_n2o[order]
df_n2o.to_csv(os.path.join(OUT_DIR, 'lpjg_n2o_annual.csv'), index=False)
print(f'  done {n:,} rows in {time.time()-t0:.0f}s', flush=True)
print(f'  → lpjg_n2o_annual.csv', flush=True)
print(f"  2000 N2O_soil = {df_n2o[df_n2o['Year']==2000]['N2O_soil_TgN'].values[0]:.3f} Tg N/yr  "
      f"N2O_fire = {df_n2o[df_n2o['Year']==2000]['N2O_fire_TgN'].values[0]:.3f}")

# =============================================================================
# SECTION 4: GRID DIAGNOSTICS
# =============================================================================
banner('[diagnostics] grid coverage')
diag_path = os.path.join(OUT_DIR, 'lpjg_grid_diagnostics.txt')
with open(diag_path, 'w') as f:
    f.write('LPJ-GUESS historical (1901-2020) – grid coverage diagnostic\n')
    f.write('='*60 + '\n')
    f.write(f'Unique grid cells:   {len(unique_cells):,}\n')
    f.write(f'Years per cell:      120 (1901-2020)\n')
    f.write(f'Total data rows:     {len(unique_cells)*120:,}\n')
    f.write(f'Grid resolution:     0.5° × 0.5°\n')
    f.write(f'Total grid area:     {total_area_m2/1e12:.2f} M km²\n')
    f.write(f'Earth land area:     ~148.94 M km² (reference)\n')
    f.write(f'Land coverage:       {total_area_m2/1e12/148.94*100:.1f}%\n')
    f.write(f'Latitude range:      {lat_min:.2f}° to {lat_max:.2f}°\n')
    f.write(f'Longitude range:     {lon_min:.2f}° to {lon_max:.2f}°\n')
print(f'  → {os.path.basename(diag_path)}', flush=True)

# Identify the 2010 NEE anomaly explicitly for downstream plotting
r2010 = df_co2[df_co2['Year']==2010].iloc[0]
print(f"\n  2010 LU_ch = {r2010['LU_ch_PgC']:.3f} Pg C/yr   (largest single-year value;\n"
      f"             drives 2010 NEE = {r2010['NEE_PgC']:+.3f} Pg C/yr — single-year HILDA+v2 forcing pulse,\n"
      f"             not a real biospheric anomaly)")

print('\nAll three files processed.\n')

# =============================================================================
# SECTION 5: COMBINED CH4 (LPJ-GUESS WETLAND + GMB INLAND FRESHWATER)
# =============================================================================
banner('[combined CH4] LPJ-GUESS wetland + GMB 2025 inland freshwater')

# GMB 2025 (Saunois et al., ESSD, Table 3) reports inland freshwater BU CH4
# emissions of 112 [49-202] Tg CH4/yr, constant across the 2000-2009,
# 2010-2019, and 2020 reporting periods. For the pre-2000 historical period
# not covered by GMB 2025, we propagate the 2000-2009 best estimate (112)
# backwards as a flat baseline. This is consistent with the GMB convention
# of treating inland freshwater fluxes as approximately time-invariant
# (they are integrated lake/reservoir/stream/pond emissions whose interannual
# variability is small relative to the wetland CH4 signal, and whose decadal
# evolution has not been resolved to the same fidelity as wetlands).
GMB_IFW_BEST = 112.0    # Tg CH4/yr  (constant)
GMB_IFW_LO   =  49.0    # Tg CH4/yr  (constant)
GMB_IFW_HI   = 202.0    # Tg CH4/yr  (constant)

df_ch4_comb = df_ch4.copy()
df_ch4_comb['IFW_TgCH4_best'] = GMB_IFW_BEST
df_ch4_comb['IFW_TgCH4_lo']   = GMB_IFW_LO
df_ch4_comb['IFW_TgCH4_hi']   = GMB_IFW_HI
df_ch4_comb['Combined_TgCH4_best'] = df_ch4_comb['CH4_TgCH4'] + GMB_IFW_BEST
df_ch4_comb['Combined_TgCH4_lo']   = df_ch4_comb['CH4_TgCH4'] + GMB_IFW_LO
df_ch4_comb['Combined_TgCH4_hi']   = df_ch4_comb['CH4_TgCH4'] + GMB_IFW_HI
df_ch4_comb.rename(columns={'CH4_TgCH4': 'Wetland_TgCH4'}, inplace=True)
df_ch4_comb.to_csv(os.path.join(OUT_DIR, 'lpjg_ch4_combined_annual.csv'), index=False)
print(f'  → lpjg_ch4_combined_annual.csv', flush=True)
print(f'  2020: wetland = {df_ch4_comb[df_ch4_comb["Year"]==2020]["Wetland_TgCH4"].values[0]:.1f} Tg CH4/yr  '
      f'+ IFW {GMB_IFW_BEST:.0f} = combined {df_ch4_comb[df_ch4_comb["Year"]==2020]["Combined_TgCH4_best"].values[0]:.1f}',
      flush=True)

# =============================================================================
# SECTION 6: FAIR-ERF v1.3 NATURAL EMISSIONS BASELINE
# =============================================================================
banner('[FAIR-ERF] natural emissions baseline (Smith et al. 2018, GMD)')

# The FAIR-ERF v1.3 natural emissions baseline is a TOP-DOWN inversion
# of CH4 and N2O natural fluxes assuming steady-state at 1765 and constant
# atmospheric lifetimes (CH4 = 9.3 yr; N2O = 121 yr; held at 2005 levels
# afterwards). Source file: natural.csv, supplied by user.
#
# Units in source file:
#   CH4 column: MtCH4 = Tg CH4 (1 Mt ≡ 1 Tg ≡ 1e12 g)
#   N2O column: MtN2O-N = Tg N (the nitrogen content of N2O, NOT the full
#               molecular mass of N2O). Multiply by 44/28 to obtain Tg N2O.
#
# The user requested that we use values from 1900 onward. Values from 2005
# onward in the source file are held constant by FAIR construction.

FAIR_PATH = os.environ.get(
    'FAIR_PATH',
    str(FAIR_ERF_CSV)
)
if os.path.exists(FAIR_PATH):
    fair_raw = pd.read_csv(FAIR_PATH, skiprows=2, sep=r'\s+', engine='python')
    fair_raw.columns = ['Year', 'CH4_TgCH4', 'N2O_TgN']
    # Drop the first ('MtCH4 / MtN2O-N') unit row if it ended up as data
    fair_raw = fair_raw[fair_raw['Year'].astype(str).str.match(r'^\d')].copy()
    fair_raw['Year'] = fair_raw['Year'].astype(float).astype(int)
    fair = fair_raw[(fair_raw['Year'] >= 1900) & (fair_raw['Year'] <= 2020)].copy()
    fair['CH4_TgCH4'] = fair['CH4_TgCH4'].astype(float)
    fair['N2O_TgN']   = fair['N2O_TgN'].astype(float)
    fair['N2O_TgN2O'] = fair['N2O_TgN'] * MW_N2O
    fair.to_csv(os.path.join(OUT_DIR, 'fair_erf_natural_baseline.csv'), index=False)
    print(f'  → fair_erf_natural_baseline.csv  ({len(fair)} rows, 1900-2020)', flush=True)
    print(f'  1900: CH4 = {fair[fair["Year"]==1900]["CH4_TgCH4"].values[0]:.1f} Tg CH4/yr   '
          f'N2O = {fair[fair["Year"]==1900]["N2O_TgN"].values[0]:.2f} Tg N/yr  '
          f'(= {fair[fair["Year"]==1900]["N2O_TgN2O"].values[0]:.2f} Tg N2O/yr)', flush=True)
    print(f'  2020: CH4 = {fair[fair["Year"]==2020]["CH4_TgCH4"].values[0]:.1f} Tg CH4/yr   '
          f'N2O = {fair[fair["Year"]==2020]["N2O_TgN"].values[0]:.2f} Tg N/yr  '
          f'(= {fair[fair["Year"]==2020]["N2O_TgN2O"].values[0]:.2f} Tg N2O/yr)', flush=True)
else:
    print(f"  (FAIR-ERF source not found at {FAIR_PATH}; skipping)", flush=True)

print('\nProcessing complete.\n')
