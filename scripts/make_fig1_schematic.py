#!/usr/bin/env python3
"""Generate Figure 1: LandSyMM-IMOGEN coupled-framework schematic (graphviz).

Replaces the legacy hand-made PowerPoint schematic (image173) with a corrected,
publication-quality dataflow diagram. Corrections vs the legacy figure:
  - 5 SSP-RCP scenarios (was 2)
  - sequential / coupled (not "closed loop")
  - RCMIP (CMIP6) residual backbone (was "IIASA CMIP6")
  - temporal sector ownership 1900-1969 / 1970-2019 / 2020-2100 (was 1850-/1961-)
  - no export-tapering wording
Output: paper/_media/results/fig1_framework_schematic.png
"""
from graphviz import Digraph
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "paper" / "_media" / "results"
OUT.mkdir(parents=True, exist_ok=True)

g = Digraph("LandSyMM_IMOGEN", format="png")
g.attr(rankdir="TB", fontname="Helvetica", fontsize="11", labelloc="t",
       label="LandSyMM-IMOGEN coupled framework", splines="ortho", nodesep="0.35", ranksep="0.5")
g.attr("node", shape="box", style="rounded,filled", fontname="Helvetica", fontsize="11")
g.attr("edge", fontname="Helvetica", fontsize="9", color="gray30")

C_MODEL = "#d6f5d6"   # process models (green)
C_CLIM  = "#cfe8ff"   # climate (blue)
C_EMISS = "#ffe0cc"   # Tier-1 emissions (orange)
C_IC    = "#e6ccff"   # controller (purple)
C_BACK  = "#f0f0f0"   # background (grey)
C_DATA  = "#fff2cc"   # data products (yellow note)

# --- Stage I ---
with g.subgraph(name="cluster_s1") as s1:
    s1.attr(label="Stage I  -  open-loop spin-up (prescribed climate)",
            style="rounded,dashed", color="gray45", fontsize="12")
    s1.node("isimip", "ISIMIP-3b climate\n(MRI-ESM2-0, bias-corrected)", fillcolor=C_CLIM)
    s1.node("lpjg1", "LPJ-GUESS\npotential yields", fillcolor=C_MODEL)
    s1.node("yields", "Potential yield\ntables", shape="note", fillcolor=C_DATA)
    s1.edge("isimip", "lpjg1")
    s1.edge("lpjg1", "yields")

# --- Stage II ---
with g.subgraph(name="cluster_s2") as s2:
    s2.attr(label="Stage II  -  sequential coupled run",
            style="rounded", color="black", fontsize="12")
    s2.node("plum", "PLUM v2\nland use & management", fillcolor=C_MODEL)
    s2.node("tier1", "IPCC Tier-1\nagricultural CH4 & N2O", fillcolor=C_EMISS)
    s2.node("lpjg2", "LPJ-GUESS\nbiogenic CO2, CH4, N2O", fillcolor=C_MODEL)
    s2.node("rcmip", "RCMIP (CMIP6)\nresidual background sectors", fillcolor=C_BACK)
    s2.node("ic", "Intermediary Controller (IC)\nintegrate + harmonise", fillcolor=C_IC)
    s2.node("emiss", "Sector-complete emissions\n(CO2, CH4, N2O)", shape="note", fillcolor=C_DATA)
    s2.node("imogen", "IMOGEN\nFaIR + pattern-scaling\n(MRI-ESM2-0, 22-GCM set)", fillcolor=C_CLIM)
    s2.node("climate", "Emulated climate\nGHG conc. + monthly fields", shape="note", fillcolor=C_DATA)
    s2.node("lpjg3", "LPJ-GUESS\nrealised ecosystem trajectories", fillcolor=C_MODEL)
    s2.edge("plum", "tier1")
    s2.edge("plum", "lpjg2")
    s2.edge("tier1", "ic")
    s2.edge("lpjg2", "ic")
    s2.edge("rcmip", "ic")
    s2.edge("ic", "emiss")
    s2.edge("emiss", "imogen")
    s2.edge("imogen", "climate")
    s2.edge("climate", "lpjg3")

# Stage I -> Stage II hand-off
g.edge("yields", "plum", label="drive PLUM yields", style="dashed", constraint="true")

# annotation footer
g.node("notes",
       "5 SSP-RCP scenarios (SSP1-2.6 ... SSP5-8.5)  |  common 0.5 deg x 0.5 deg grid\n"
       "Sector ownership: 1900-1969 prescribed RCMIP  -  1970-2019 FAOSTAT activity  -  2020-2100 PLUM activity\n"
       "Cadence: annual system-boundary exchange  -  monthly climate forcing  -  daily biophysical processing",
       shape="box", style="filled", fillcolor="white", color="gray60", fontsize="9")
g.edge("lpjg3", "notes", style="invis")

p = g.render(filename="fig1_framework_schematic", directory=str(OUT), cleanup=True)
print("wrote", p)
