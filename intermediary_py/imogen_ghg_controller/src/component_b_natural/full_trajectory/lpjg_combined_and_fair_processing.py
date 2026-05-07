"""
lpjg_combined_and_fair_processing.py
=====================================
Helper script that produces the auxiliary output CSVs needed by the
historical plotting routine, WITHOUT re-streaming the large .gz files
(which take ~30-90 s each via zcat):

OUTPUT FILES
------------
  lpjg_ch4_combined_annual.csv
      LPJ-GUESS wetland CH4 (loaded from lpjg_ch4_annual.csv) augmented
      with GMB 2025 inland freshwater (IFW) emissions and the GMB 2025
      double-counting correction (DCC). Columns:
        Year, Wetland_TgCH4
        IFW_TgCH4_best/lo/hi          GMB IFW best & range, constant
                                       112 [49, 202] Tg CH4/yr
        Combined_TgCH4_best/lo/hi     wetland + IFW (naive sum)
        DCC_TgCH4_best/lo/hi          GMB DCC, -23 [-9, -36] Tg CH4/yr
        CombinedDCC_TgCH4_best/lo/hi  wetland + IFW + DCC (corrected)

  fair_erf_natural_baseline.csv
      FAIR-ERF v1.3 natural emissions baseline (Smith et al. 2018, GMD 11,
      2273-2297) parsed from natural.csv. Columns:
        Year, CH4_TgCH4, N2O_TgN, N2O_TgN2O
      Source file convention: CH4 is in Tg CH4 directly; N2O is in
      Tg N (nitrogen content of N2O), so we multiply by 44/28 to obtain
      Tg N2O. Values from 2005 onward held constant by FAIR construction.

INPUT EXPECTATIONS
------------------
  Reads lpjg_ch4_annual.csv from OUT_DIR (must already exist; produced
  by lpjg_historical_processing.py).
  Reads natural.csv from FAIR_PATH (default:
  {FAIR_ERF_CSV}).

USAGE
-----
  These steps are also embedded in lpjg_historical_processing.py
  (Sections 5 & 6), so re-running the full processor produces the same
  files. This standalone helper exists for fast iteration on plot
  logic without re-streaming the large .gz inputs.
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
    FAIR_ERF_CSV, OUT_B_DATA, OUT_B_FIGS, OUT_B_SUMMARIES,
)

import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_B_DATA))

# --- Combined CH4 (with optional DCC correction) ---------------------------
GMB_IFW_BEST = 112.0    # Tg CH4/yr  (constant; GMB 2025 Table 3)
GMB_IFW_LO   =  49.0
GMB_IFW_HI   = 202.0

# GMB 2025 Table 3 reports a Double-Counting Correction (DCC) of
# -23 [-9, -36] Tg CH4/yr applied to the COMBINED wetland+freshwater
# estimate to remove overlap between BU wetland and inland freshwater
# inventories. GMB only reports DCC explicitly for 2010+ periods. We
# apply the DCC uniformly across the full historical period (1901-2020)
# for consistency with the constant IFW propagation, with the caveat
# that GMB itself only reports DCC for recent decades.
GMB_DCC_BEST = -23.0   # Tg CH4/yr
GMB_DCC_LO   =  -9.0   # less correction (more positive net)
GMB_DCC_HI   = -36.0   # more correction (more negative net)

ch4 = pd.read_csv(os.path.join(OUT_DIR, 'lpjg_ch4_annual.csv'))
df = ch4.rename(columns={'CH4_TgCH4': 'Wetland_TgCH4'}).copy()

# Inland freshwater
df['IFW_TgCH4_best']      = GMB_IFW_BEST
df['IFW_TgCH4_lo']        = GMB_IFW_LO
df['IFW_TgCH4_hi']        = GMB_IFW_HI

# Naive combined (wetland + IFW, NO double-counting correction)
df['Combined_TgCH4_best'] = df['Wetland_TgCH4'] + GMB_IFW_BEST
df['Combined_TgCH4_lo']   = df['Wetland_TgCH4'] + GMB_IFW_LO
df['Combined_TgCH4_hi']   = df['Wetland_TgCH4'] + GMB_IFW_HI

# Double-counting correction
df['DCC_TgCH4_best']      = GMB_DCC_BEST
df['DCC_TgCH4_lo']        = GMB_DCC_LO
df['DCC_TgCH4_hi']        = GMB_DCC_HI

# DCC-corrected combined: wetland + IFW + DCC
# Bounds: combine IFW range + DCC range pairwise
#   net low  = IFW_lo + DCC_hi (smallest IFW + largest correction = smallest net)
#   net high = IFW_hi + DCC_lo (largest IFW + smallest correction = largest net)
df['CombinedDCC_TgCH4_best'] = df['Wetland_TgCH4'] + GMB_IFW_BEST + GMB_DCC_BEST
df['CombinedDCC_TgCH4_lo']   = df['Wetland_TgCH4'] + GMB_IFW_LO   + GMB_DCC_HI
df['CombinedDCC_TgCH4_hi']   = df['Wetland_TgCH4'] + GMB_IFW_HI   + GMB_DCC_LO

df.to_csv(os.path.join(OUT_DIR, 'lpjg_ch4_combined_annual.csv'), index=False)
print(f"Saved lpjg_ch4_combined_annual.csv  ({len(df)} rows, "
      f"with naive Combined_* and DCC-corrected CombinedDCC_* columns)")

# --- FAIR-ERF v1.3 baseline -----------------------------------------------
FAIR_PATH = os.environ.get('FAIR_PATH',
                           str(FAIR_ERF_CSV))
MW_N2O = 44.0 / 28.0

fair_raw = pd.read_csv(FAIR_PATH, skiprows=2, sep=r'\s+', engine='python',
                        names=['Year', 'CH4_TgCH4', 'N2O_TgN'])
fair_raw = fair_raw[fair_raw['Year'].astype(str).str.match(r'^\d')].copy()
fair_raw['Year'] = fair_raw['Year'].astype(float).astype(int)
fair = fair_raw[(fair_raw['Year'] >= 1900) & (fair_raw['Year'] <= 2020)].copy()
fair['CH4_TgCH4'] = fair['CH4_TgCH4'].astype(float)
fair['N2O_TgN']   = fair['N2O_TgN'].astype(float)
fair['N2O_TgN2O'] = fair['N2O_TgN'] * MW_N2O
fair = fair[['Year', 'CH4_TgCH4', 'N2O_TgN', 'N2O_TgN2O']]
fair.to_csv(os.path.join(OUT_DIR, 'fair_erf_natural_baseline.csv'), index=False)
print(f"Saved fair_erf_natural_baseline.csv  ({len(fair)} rows, 1900-2020)")
print(f"  1900: CH4={fair[fair.Year==1900]['CH4_TgCH4'].values[0]:.1f} Tg/yr  "
      f"N2O={fair[fair.Year==1900]['N2O_TgN'].values[0]:.2f} Tg N/yr  "
      f"({fair[fair.Year==1900]['N2O_TgN2O'].values[0]:.2f} Tg N2O/yr)")
print(f"  2020: CH4={fair[fair.Year==2020]['CH4_TgCH4'].values[0]:.1f} Tg/yr  "
      f"N2O={fair[fair.Year==2020]['N2O_TgN'].values[0]:.2f} Tg N/yr  "
      f"({fair[fair.Year==2020]['N2O_TgN2O'].values[0]:.2f} Tg N2O/yr)")
