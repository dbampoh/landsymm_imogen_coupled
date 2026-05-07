"""
integrated_emissions_processing.py
====================================
Component C, Step 2: combines anthropogenic and natural emission trajectories
per gas (CH4, N2O, CO2) into a single integrated CSV ready for plotting and
IMOGEN ingestion.

ARCHITECTURE
------------
For each gas, the integrated trajectory is:
    Total_Mt(t, SSP) = Anthropogenic_Mt(t, SSP) + Natural_Mt(t, SSP)

Where:
    Anthropogenic side:
        CH4: rcmip_substitution_ch4.csv "New_total" (Mt CH4)
             = full anthropogenic with our IPCC Tier 1 agri sub-totals replacing
               RCMIP's MAGICC AFOLU/Agriculture component
        N2O: rcmip_substitution_n2o.csv "New_total" (Mt N2O)
             = same logic
        CO2: rcmip_co2.csv "EFOS_MtCO2" (Mt CO2)
             = RCMIP's Emissions|CO2|MAGICC Fossil and Industrial only
               (Option A framing — no AFOLU here, since AFOLU/ELUC is captured
                inside LPJ-GUESS NEE on the natural side)

    Natural side (LPJ-GUESS):
        CH4: lpjg_ch4_combined_annual*.csv "CombinedDCC_TgCH4_best" (Tg CH4)
             = LPJ-GUESS wetland + GMB IFW (112) − GMB DCC (-23 best)
             1 Tg = 1 Mt → no unit conversion
        N2O: lpjg_n2o_annual*.csv "N2O_soil_TgN2O + N2O_fire_TgN2O" (Tg N2O)
             = combined natural N2O (soil + fire)
             1 Tg = 1 Mt → no unit conversion
        CO2: lpjg_co2_annual*.csv "NEE_PgC" (Pg C)
             × 44/12 → Pg CO2  → × 1000 → Mt CO2

TEMPORAL HARMONIZATION
----------------------
LPJ-GUESS coverage:
    Historical: 1901-2020 (single shared trajectory)
    Scenarios:  2021-2100 (per-SSP trajectory)
For year 1900 (no LPJ-GUESS data): use 1901 historical value (replicated).
For 1901-2020: replicate historical LPJ-GUESS value across all 5 scenarios.
For 2021-2100: use scenario-specific LPJ-GUESS values.

RCMIP-substitution coverage: full 1900-2100, all 5 scenarios.
RCMIP CO2 EFOS coverage: full 1900-2100, all 5 scenarios.

For continuity, we also include reference values:
    RCMIP_total: full RCMIP anthropogenic total (BEFORE substitution)
                 = "what climate models would normally use as anthropogenic"
                 = baseline for comparison plotting
    FAIR_natural: FAIR-ERF v1.3 natural baseline (constant after 2005)
                 = "what climate emulators traditionally use as natural"
                 = baseline for comparison plotting
                 Held constant for years > 2020 by extending 2020 value forward.

OUTPUT FILES
------------
    integrated_emissions_ch4.csv
    integrated_emissions_n2o.csv
    integrated_emissions_co2.csv

    Columns (per gas):
        Year, Scenario, Period
        Anthro_Mt           — our anthropogenic (post-substitution where applicable)
        Natural_Mt          — LPJ-GUESS natural
        Total_Mt            — integrated total = Anthro + Natural
        RCMIP_total_Mt      — RCMIP published anthropogenic (pre-substitution baseline)
        FAIR_natural_Mt     — FAIR-ERF v1.3 natural baseline (for comparison)
        Default_total_Mt    — RCMIP_total + FAIR_natural (the conventional "default")

    1005 rows each = 5 scenarios × 201 years (1900-2100), in Mt of the gas.

VALIDATION CHECKS (printed)
---------------------------
    1. CH4 in Mt CH4: integrated 2020 SSP2 ≈ 393 (anthro) + 179 (nat) = 572 Mt
    2. N2O in Mt N2O: integrated 2020 SSP2 ≈ 12.34 (anthro) + 14.4 (nat) = 26.7 Mt
    3. CO2 in Mt CO2: integrated 2020 SSP2 ≈ 37388 (EFOS) + (-7300) (NEE) = ~30100 Mt
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
    OUT_A_DATA, OUT_B_DATA, OUT_C_DATA, OUT_C_FIGS, OUT_C_SUMMARIES,
)

import os
import pandas as pd
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR_LPJ = os.environ.get('DATA_DIR_LPJ', str(OUT_B_DATA))
DATA_DIR_RCMIP = os.environ.get('DATA_DIR_RCMIP',
                                str(OUT_A_DATA))
OUT_DIR = os.environ.get('OUT_DIR', str(OUT_C_DATA))
os.makedirs(OUT_DIR, exist_ok=True)

SCENARIOS = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP4-6.0', 'SSP5-8.5']
LPJG_TAG_MAP = {                       # plot-style label → LPJ-GUESS file tag
    'SSP1-2.6': 'ssp1rcp26',
    'SSP2-4.5': 'ssp2rcp45',
    'SSP3-7.0': 'ssp3rcp70',
    'SSP4-6.0': 'ssp4rcp60',
    'SSP5-8.5': 'ssp5rcp85',
}

# Unit-conversion constant for CO2: Pg C × 44/12 × 1000 → Mt CO2
PgC_to_MtCO2 = (44.0 / 12.0) * 1000.0


def banner(msg):
    print('\n' + '=' * 72 + f'\n{msg}\n' + '=' * 72, flush=True)


# =============================================================================
# 1. LOAD ALL INPUT DATA
# =============================================================================
banner("LOADING INPUTS")

# --- Anthropogenic ---
ch4_anthro = pd.read_csv(os.path.join(DATA_DIR_RCMIP, 'rcmip_substitution_ch4.csv'))
n2o_anthro = pd.read_csv(os.path.join(DATA_DIR_RCMIP, 'rcmip_substitution_n2o.csv'))
# rcmip_co2.csv is produced in our local OUT_DIR, not in the legacy work dir
co2_path = os.path.join(OUT_DIR, 'rcmip_co2.csv')
if not os.path.exists(co2_path):
    co2_path = os.path.join(DATA_DIR_RCMIP, 'rcmip_co2.csv')
co2_anthro = pd.read_csv(co2_path)

print(f"  rcmip_substitution_ch4.csv: {ch4_anthro.shape}")
print(f"  rcmip_substitution_n2o.csv: {n2o_anthro.shape}")
print(f"  rcmip_co2.csv             : {co2_anthro.shape}")

# --- Natural (LPJ-GUESS) ---
lpj_ch4_h = pd.read_csv(os.path.join(DATA_DIR_LPJ, 'lpjg_ch4_combined_annual.csv'))
lpj_ch4_s = pd.read_csv(os.path.join(DATA_DIR_LPJ, 'lpjg_ch4_combined_annual_scenarios.csv'))
lpj_n2o_h = pd.read_csv(os.path.join(DATA_DIR_LPJ, 'lpjg_n2o_annual.csv'))
lpj_n2o_s = pd.read_csv(os.path.join(DATA_DIR_LPJ, 'lpjg_n2o_annual_scenarios.csv'))
lpj_co2_h = pd.read_csv(os.path.join(DATA_DIR_LPJ, 'lpjg_co2_annual.csv'))
lpj_co2_s = pd.read_csv(os.path.join(DATA_DIR_LPJ, 'lpjg_co2_annual_scenarios.csv'))

print(f"  lpjg_ch4_combined hist: {lpj_ch4_h.shape}, scenarios: {lpj_ch4_s.shape}")
print(f"  lpjg_n2o          hist: {lpj_n2o_h.shape}, scenarios: {lpj_n2o_s.shape}")
print(f"  lpjg_co2          hist: {lpj_co2_h.shape}, scenarios: {lpj_co2_s.shape}")

# --- FAIR-ERF natural baseline ---
fair = pd.read_csv(os.path.join(DATA_DIR_LPJ, 'fair_erf_natural_baseline.csv'))
print(f"  fair_erf_natural_baseline : {fair.shape}")


# =============================================================================
# 2. BUILD PER-SCENARIO TIME SERIES FOR LPJ-GUESS NATURAL EMISSIONS
# =============================================================================
# LPJ-GUESS has historical 1901-2020 (shared) + scenarios 2021-2100 (per SSP).
# We need a unified 1900-2100 trajectory per scenario in Mt-of-gas units.
banner("BUILDING LPJ-GUESS NATURAL TIME SERIES (Mt-of-gas, 1900-2100)")

def lpj_natural_series(scenario_label):
    """Returns dict {year: dict_of_per_gas_natural_Mt} for 1900-2100 for the
    given scenario label. Historical replicated across scenarios; 2021-2100
    uses the scenario-specific LPJ-GUESS run; 1900 backfilled from 1901."""
    tag = LPJG_TAG_MAP[scenario_label]
    ch4_nat, n2o_nat, co2_nat = {}, {}, {}

    # Historical 1901-2020 (shared across scenarios)
    for _, r in lpj_ch4_h.iterrows():
        y = int(r['Year'])
        ch4_nat[y] = float(r['CombinedDCC_TgCH4_best'])      # Tg CH4 = Mt CH4
    for _, r in lpj_n2o_h.iterrows():
        y = int(r['Year'])
        n2o_nat[y] = float(r['N2O_soil_TgN2O']) + float(r['N2O_fire_TgN2O'])  # Tg N2O = Mt N2O
    for _, r in lpj_co2_h.iterrows():
        y = int(r['Year'])
        co2_nat[y] = float(r['NEE_PgC']) * PgC_to_MtCO2      # Pg C → Mt CO2

    # Scenario 2021-2100 (per SSP)
    sub_ch4 = lpj_ch4_s[lpj_ch4_s.Scenario == tag]
    sub_n2o = lpj_n2o_s[lpj_n2o_s.Scenario == tag]
    sub_co2 = lpj_co2_s[lpj_co2_s.Scenario == tag]
    for _, r in sub_ch4.iterrows():
        y = int(r['Year'])
        ch4_nat[y] = float(r['CombinedDCC_TgCH4_best'])
    for _, r in sub_n2o.iterrows():
        y = int(r['Year'])
        n2o_nat[y] = float(r['N2O_soil_TgN2O']) + float(r['N2O_fire_TgN2O'])
    for _, r in sub_co2.iterrows():
        y = int(r['Year'])
        co2_nat[y] = float(r['NEE_PgC']) * PgC_to_MtCO2

    # Backfill 1900 from 1901 (LPJ-GUESS coverage starts at 1901)
    if 1900 not in ch4_nat: ch4_nat[1900] = ch4_nat[1901]
    if 1900 not in n2o_nat: n2o_nat[1900] = n2o_nat[1901]
    if 1900 not in co2_nat: co2_nat[1900] = co2_nat[1901]

    return ch4_nat, n2o_nat, co2_nat


# =============================================================================
# 3. BUILD PER-SCENARIO FAIR-ERF NATURAL BASELINE
# =============================================================================
# FAIR coverage: 1900-2020. Held constant for 2021-2100 by extending 2020 value.
# Same FAIR baseline for all scenarios (it has no scenario dependency).
fair_ch4 = {int(r['Year']): float(r['CH4_TgCH4']) for _, r in fair.iterrows()}
fair_n2o = {int(r['Year']): float(r['N2O_TgN2O']) for _, r in fair.iterrows()}
# CO2 not in FAIR-ERF natural baseline — set to 0 (no natural CO2 emission baseline)
# (FAIR-ERF treats CO2 differently; natural CO2 is assumed in equilibrium with land sink)
fair_co2 = {y: 0.0 for y in range(1900, 2021)}

last_year = max(fair_ch4)   # 2020
for y in range(last_year + 1, 2101):
    fair_ch4[y] = fair_ch4[last_year]
    fair_n2o[y] = fair_n2o[last_year]
    fair_co2[y] = 0.0


# =============================================================================
# 4. ASSEMBLE PER-GAS LONG-FORMAT INTEGRATED CSVs
# =============================================================================
banner("ASSEMBLING INTEGRATED CSVs")

def assemble_gas(gas_name, anthro_df, anthro_col, lpj_nat_dict_idx,
                 fair_dict, out_filename):
    """Build a long-format integrated CSV for one gas."""
    rows = []
    for scen in SCENARIOS:
        ch4_nat, n2o_nat, co2_nat = lpj_natural_series(scen)
        nat_dict = [ch4_nat, n2o_nat, co2_nat][lpj_nat_dict_idx]

        # Subset anthro_df for this scenario
        sub = anthro_df[anthro_df.Scenario == scen]
        anthro_lookup = {int(r['Year']): float(r[anthro_col]) for _, r in sub.iterrows()}

        # RCMIP_total (anthro before substitution) — only present in CH4 / N2O CSVs
        if 'RCMIP_total' in anthro_df.columns:
            rcmip_lookup = {int(r['Year']): float(r['RCMIP_total']) for _, r in sub.iterrows()}
        else:
            rcmip_lookup = anthro_lookup    # for CO2, RCMIP_total = EFOS = our anthro

        period_lookup = {int(r['Year']): r['Period'] for _, r in sub.iterrows()}

        for year in range(1900, 2101):
            anthro = anthro_lookup.get(year)
            natural = nat_dict.get(year)
            rcmip_total = rcmip_lookup.get(year)
            fair_nat = fair_dict.get(year, 0.0)
            period = period_lookup.get(year, 'unknown')

            rows.append({
                'Year': year,
                'Scenario': scen,
                'Period': period,
                'Anthro_Mt': anthro,
                'Natural_Mt': natural,
                'Total_Mt': anthro + natural,
                'RCMIP_total_Mt': rcmip_total,
                'FAIR_natural_Mt': fair_nat,
                'Default_total_Mt': rcmip_total + fair_nat,
            })

    df = pd.DataFrame(rows).sort_values(['Scenario', 'Year']).reset_index(drop=True)
    out_path = os.path.join(OUT_DIR, out_filename)
    df.to_csv(out_path, index=False)
    print(f"\n  Saved: {out_path}")
    print(f"  Shape: {df.shape}")
    return df


df_ch4 = assemble_gas('CH4', ch4_anthro, 'New_total', 0, fair_ch4,
                      'integrated_emissions_ch4.csv')
df_n2o = assemble_gas('N2O', n2o_anthro, 'New_total', 1, fair_n2o,
                      'integrated_emissions_n2o.csv')
df_co2 = assemble_gas('CO2', co2_anthro, 'EFOS_MtCO2', 2, fair_co2,
                      'integrated_emissions_co2.csv')


# =============================================================================
# 5. VALIDATION CHECKS
# =============================================================================
banner("VALIDATION CHECKS")

print("--- 2020 SSP2-4.5 spot checks ---")
def show_2020(df, gas, unit_label):
    r = df[(df.Year == 2020) & (df.Scenario == 'SSP2-4.5')].iloc[0]
    print(f"  {gas}: anthro={r.Anthro_Mt:.2f} + natural={r.Natural_Mt:.2f} "
          f"= total={r.Total_Mt:.2f} {unit_label}")
    print(f"        RCMIP_total={r.RCMIP_total_Mt:.2f}, FAIR_natural={r.FAIR_natural_Mt:.2f}, "
          f"Default_total={r.Default_total_Mt:.2f}")
show_2020(df_ch4, 'CH4', 'Mt CH4/yr')
show_2020(df_n2o, 'N2O', 'Mt N2O/yr')
show_2020(df_co2, 'CO2', 'Mt CO2/yr')

print("\n--- 2014-2020 mean (to compare with GCB partition) ---")
co2_overlap = df_co2[(df_co2.Year >= 2014) & (df_co2.Year <= 2020)
                     & (df_co2.Scenario == 'SSP2-4.5')]
mean_anthro = co2_overlap['Anthro_Mt'].mean()
mean_natural = co2_overlap['Natural_Mt'].mean()
mean_total = co2_overlap['Total_Mt'].mean()
print(f"  CO2 EFOS  (anthro):   {mean_anthro:.0f} Mt CO2 = {mean_anthro/PgC_to_MtCO2:.2f} Pg C")
print(f"  CO2 NEE   (natural):  {mean_natural:.0f} Mt CO2 = {mean_natural/PgC_to_MtCO2:.2f} Pg C")
print(f"  CO2 total (Option A): {mean_total:.0f} Mt CO2 = {mean_total/PgC_to_MtCO2:.2f} Pg C")
print(f"\n  GCB 2025 reference (2014-2023, Pg C/yr):")
print(f"    EFOS = 9.7 ± 0.5; ELUC = 1.1 ± 0.7; SLAND = 3.2 ± 0.9")
print(f"    EFOS + ELUC − SLAND = atmospheric source = {9.7 + 1.1 - 3.2:.2f} ± "
      f"{(0.5**2 + 0.7**2 + 0.9**2)**0.5:.2f} Pg C/yr")
print(f"  Our Option A         = EFOS + NEE         = "
      f"{mean_total/PgC_to_MtCO2:.2f} Pg C/yr")
print(f"  Gap (GCB − Ours): {(9.7 + 1.1 - 3.2) - mean_total/PgC_to_MtCO2:.2f} Pg C/yr "
      "(should be small if Option A is sound)")

print("\n--- 2091-2100 mean integrated totals (Mt-of-gas) ---")
print(f"  {'Scenario':<10} {'CH4':>10} {'N2O':>8} {'CO2':>10}")
for scen in SCENARIOS:
    ch4_v = df_ch4[(df_ch4.Year >= 2091) & (df_ch4.Year <= 2100)
                    & (df_ch4.Scenario == scen)]['Total_Mt'].mean()
    n2o_v = df_n2o[(df_n2o.Year >= 2091) & (df_n2o.Year <= 2100)
                    & (df_n2o.Scenario == scen)]['Total_Mt'].mean()
    co2_v = df_co2[(df_co2.Year >= 2091) & (df_co2.Year <= 2100)
                    & (df_co2.Scenario == scen)]['Total_Mt'].mean()
    print(f"  {scen:<10} {ch4_v:>10.1f} {n2o_v:>8.2f} {co2_v:>10.0f}")

print("\nDone.")
