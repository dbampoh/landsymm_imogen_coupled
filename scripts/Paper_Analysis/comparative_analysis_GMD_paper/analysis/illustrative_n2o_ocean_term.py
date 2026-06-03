#!/usr/bin/env python3
"""ILLUSTRATIVE ONLY - sense-check of adding the ocean/non-land natural N2O source.

NOT a FaIR recalibration and NOT a change to any model output. We simply re-run the
documented one-box IMOGEN/FaIR N2O budget (climatemodel.cpp fair_non_co2_ghg_budget)
on emissions that ALREADY EXIST in integrated_emissions_n2o.csv:
  - 'Total_Mt'         = anthropogenic + LPJ-GUESS land natural  (what was actually fed -> our low N2O)
  - 'Default_total_Mt' = RCMIP anthropogenic + FaIR natural (= land + ocean/non-land natural)
The second curve is the illustrative "what if the missing ocean/non-land natural source
were included" trajectory. Output is a standalone figure for visual sense only.
"""
import csv, math
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

A = Path(__file__).resolve().parent
EMI = A / "outputs_concentration" / ".." / ".." / "comparative_analysis_GMD_paper"  # placeholder; set below
EMISS = Path("/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm/intermediary_py/imogen_ghg_controller/outputs/component_c/data/integrated_emissions_n2o.csv")
OBSCSV = Path("/home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/landsymm_lpjg_imogen_coupled_model/lpj-guess_imogen_landsymm/data/concentrations/EPA/ghg-concentrations_n2o.csv")
OUT = A / "outputs_concentration" / "fig_ILLUSTRATIVE_n2o_ocean_term.png"

# one-box budget constants (from climatemodel.cpp)
MM_AIR=28.9647; MM_N2O=44.01; MM_N2=2*14.0067; MA=5.1352e18
TAU=121.0; N2O_INIT=277.4; Y0=1900

SCEN=["SSP1-2.6","SSP2-4.5","SSP3-7.0","SSP4-6.0","SSP5-8.5"]
COL={"SSP1-2.6":"#1f4e79","SSP2-4.5":"#2a9d8f","SSP3-7.0":"#e9c46a","SSP4-6.0":"#f4a261","SSP5-8.5":"#e63946"}

def load_emiss():
    rows={}
    with open(EMISS) as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(r["Scenario"],[]).append(
                (int(r["Year"]), float(r["Total_Mt"]), float(r["Default_total_Mt"])))
    for s in rows: rows[s].sort()
    return rows

def budget(years_emiss):
    """years_emiss: list of (year, emiss_TgN2O). Returns dict year->ppbv via one-box budget."""
    out={}; c=N2O_INIT*1e-9
    decay=(1.0-math.exp(-1.0/TAU))
    for yr,e in years_emiss:
        e_kgN2 = e*(MM_N2/MM_N2O)*(1e12/1e3)
        dghg = e_kgN2/MA*MM_AIR/MM_N2
        c = c + dghg - c*decay
        out[yr]=c*1e9
    return out

def load_obs():
    yrs=[];val=[]
    with open(OBSCSV) as fh:
        for r in csv.reader(fh):
            try:
                y=float(r[0]); v=float(r[1])
                yrs.append(y);val.append(v)
            except: pass
    return yrs,val

emi=load_emiss(); 
fig,ax=plt.subplots(figsize=(10,5.5))
for s in SCEN:
    yrs=[y for y,_,_ in emi[s]]
    our=budget([(y,t) for y,t,_ in emi[s]])
    cor=budget([(y,d) for y,_,d in emi[s]])
    ax.plot(yrs,[our[y] for y in yrs],color=COL[s],lw=1.3,label=f"as run (land-only natural): {s}")
    ax.plot(yrs,[cor[y] for y in yrs],color=COL[s],lw=1.3,ls="--")
oy,ov=load_obs()
ax.plot(oy,ov,"k.",ms=4,label="Observed (EPA/NOAA)")
ax.plot([],[]," ",label="(dashed = ILLUSTRATIVE: + ocean/non-land natural source)")
ax.set_xlabel("Year"); ax.set_ylabel("N$_2$O (ppb)")
ax.set_title("ILLUSTRATIVE one-box check: effect of adding the ocean/non-land natural N$_2$O source\n(no FaIR recalibration; existing emissions data; solid = as run, dashed = + ocean/non-land natural)")
ax.set_xlim(1900,2100); ax.grid(alpha=.3); ax.legend(fontsize=7,ncol=2,loc="upper left")
fig.tight_layout(); fig.savefig(str(OUT),dpi=150); print("wrote",OUT)
