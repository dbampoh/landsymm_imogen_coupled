
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
    EDGAR_N2O_NEW, FAO_DIR, FAO_EMISSIONS_CSV, FAO_PRODUCTION_CSV, OUT_A_DATA, OUT_A_FIGS, OUT_A_SUMMARIES,
)


import pandas as pd, numpy as np

PROD_CSV  = str(FAO_PRODUCTION_CSV)
EMISS_CSV = str(FAO_EMISSIONS_CSV)
YEAR_START=1970; YEAR_END=2020; YEAR_COLS=[f"Y{y}" for y in range(1970,2021)]
KG_TO_GG=1e-6; MW_N2O=44/28; EF4=0.010

R9=["North America","Western Europe","Eastern Europe","Oceania","Latin America","Africa","Middle East","Asia","Indian Subcontinent"]
DEVELOPED={"North America","Western Europe","Eastern Europe","Oceania"}

REGION_SETS={
"Indian Subcontinent":{"Afghanistan","Bangladesh","Bhutan","India","Maldives","Nepal","Pakistan","Sri Lanka"},
"North America":{"United States of America","Canada","Greenland","Saint Pierre and Miquelon"},
"Western Europe":{"Albania","Andorra","Austria","Belgium","Belgium-Luxembourg","Cyprus","Denmark","Finland","France and Monaco","France","Germany","Greece","Iceland","Ireland","Israel and Palestine, State of","Italy, San Marino and the Holy See","Italy","Luxembourg","Malta","Netherlands","Norway","Portugal","Spain and Andorra","Spain","Sweden","Switzerland and Liechtenstein","Switzerland","United Kingdom","Monaco","San Marino","Liechtenstein"},
"Eastern Europe":{"Armenia","Azerbaijan","Belarus","Bosnia and Herzegovina","Bulgaria","Croatia","Czechia","Czech Republic","Estonia","Georgia","Hungary","Kazakhstan","Kyrgyzstan","Latvia","Lithuania","Moldova","Montenegro","North Macedonia","Poland","Romania","Russia","Serbia","Serbia and Montenegro","Slovakia","Slovenia","Tajikistan","Türkiye","Turkey","Turkmenistan","Ukraine","Uzbekistan","Kosovo","Yugoslavia"},
"Oceania":{"Australia","Cook Islands","Fiji","Kiribati","Marshall Islands","Nauru","New Caledonia","New Zealand","Niue","Palau","Papua New Guinea","Samoa","Solomon Islands","Tonga","Tuvalu","Vanuatu","French Polynesia"},
"Latin America":{"Antigua and Barbuda","Argentina","Bahamas","Barbados","Belize","Bolivia (Plurinational State of)","Bolivia","Brazil","Chile","Colombia","Costa Rica","Cuba","Dominica","Dominican Republic","Ecuador","El Salvador","Grenada","Guatemala","Guyana","Haiti","Honduras","Jamaica","Mexico","Nicaragua","Panama","Paraguay","Peru","Saint Kitts and Nevis","Saint Lucia","Saint Vincent and the Grenadines","Suriname","Trinidad and Tobago","Uruguay","Venezuela (Bolivarian Republic of)","Venezuela","Puerto Rico","Aruba","Netherlands Antilles","Bermuda","Cayman Islands","British Virgin Islands","Turks and Caicos Islands"},
"Middle East":{"Bahrain","Egypt","Iran (Islamic Republic of)","Iran","Iraq","Jordan","Kuwait","Lebanon","Libya","Morocco","Oman","Qatar","Saudi Arabia","Syrian Arab Republic","Syria","Tunisia","United Arab Emirates","Yemen","Algeria","Djibouti","Israel","Mauritania","Somalia","Sudan","Sudan and South Sudan"},
"Africa":{"Angola","Benin","Botswana","Burkina Faso","Burundi","Cabo Verde","Cameroon","Central African Republic","Chad","Comoros","Congo","Côte d`Ivoire","Côte d'Ivoire","Democratic Republic of the Congo","Equatorial Guinea","Eritrea","Eswatini","Ethiopia","Gabon","Gambia","Ghana","Guinea","Guinea-Bissau","Kenya","Lesotho","Liberia","Madagascar","Malawi","Mali","Mauritius","Mozambique","Namibia","Niger","Nigeria","Rwanda","São Tomé and Príncipe","Sao Tome and Principe","Senegal","Seychelles","Sierra Leone","South Africa","South Sudan","Tanzania","Togo","Uganda","United Republic of Tanzania","Zambia","Zimbabwe","Ethiopia PDR","Cape Verde","Réunion","Mayotte"},
"Asia":{"Brunei Darussalam","Cambodia","China","China, mainland","China, Hong Kong SAR","China, Macao SAR","China, Taiwan Province of","Indonesia","Japan","Democratic People's Republic of Korea","North Korea","Korea, Republic of","South Korea","Republic of Korea","Lao People's Democratic Republic","Laos","Malaysia","Mongolia","Myanmar","Myanmar/Burma","Philippines","Singapore","Thailand","Timor-Leste","Viet Nam","Vietnam","Hong Kong","Macao","Taiwan"},
}
def get_region(c):
    for r,s in REGION_SETS.items():
        if c in s: return r
    return "Africa"

# -- EF3 (from original script lines 425-441) --
EF3_CAT06 = [0.000,0.005,0.005,0.020,0.000,0.000,0.000,0.000,0.005]
EF3_CAT19 = [0.000,0.005,0.010,0.020,0.000,0.000,0.0006,0.000,0.010]
EF3_SW06  = [0.000,0.005,0.005,0.020,0.002,0.002,0.000,0.000,0.005]
EF3_SW19  = [0.000,0.005,0.010,0.020,0.002,0.002,0.000,0.0006,0.010]
EF3_SG19  = [0.000,0.000,0.010,0.020,0.000,0.000,0.000,0.000,0.010]
EF3_POUL  = 0.001; FG_POUL = 0.40

# -- FG (from original script lines 462-489) --
FG_D06  = [0.35,0.40,0.30,0.20,0.00,0.07,0.00,0.00,0.30]
FG_D19  = [0.35,0.39,0.14,0.20,0.00,0.07,0.00,0.00,0.14]
FG_O06  = [0.35,0.40,0.45,0.30,0.00,0.07,0.00,0.00,0.45]
FG_O19  = [0.35,0.39,0.17,0.30,0.00,0.07,0.00,0.00,0.17]
FG_B06  = FG_O06; FG_B19 = FG_O19
FG_SW06 = [0.40,0.48,0.45,0.20,0.25,0.25,0.00,0.00,0.45]
FG_SW19 = [0.40,0.48,0.22,0.20,0.25,0.25,0.00,0.00,0.22]
FG_SG19 = [0.35,0.35,0.12,0.12,0.00,0.07,0.00,0.00,0.12]
FG_BL06 = [(a+b)/2 for a,b in zip(FG_D06,FG_O06)]
FG_BL19 = [(a+b)/2 for a,b in zip(FG_D19,FG_O19)]

def rd(v): return dict(zip(R9,v))

# -- AWMS (from original script lines 316-401) --
AWMS_D={
"North America":      [0.150,0.270,0.263,0.000,0.108,0.184,0.000,0.000,0.026],
"Western Europe":     [0.000,0.357,0.368,0.000,0.200,0.070,0.000,0.000,0.005],
"Eastern Europe":     [0.000,0.175,0.600,0.000,0.180,0.025,0.000,0.000,0.020],
"Oceania":            [0.160,0.010,0.000,0.000,0.760,0.080,0.000,0.000,0.000],
"Latin America":      [0.000,0.010,0.010,0.000,0.360,0.620,0.000,0.000,0.000],
"Africa":             [0.000,0.000,0.010,0.000,0.830,0.050,0.000,0.060,0.040],
"Middle East":        [0.000,0.010,0.020,0.000,0.800,0.020,0.000,0.170,0.000],
"Asia":               [0.040,0.380,0.000,0.000,0.200,0.290,0.020,0.070,0.000],
"Indian Subcontinent":[0.000,0.010,0.000,0.000,0.270,0.190,0.010,0.510,0.000],
}
AWMS_O={
"North America":      [0.000,0.002,0.000,0.184,0.815,0.000,0.000,0.000,0.000],
"Western Europe":     [0.000,0.252,0.390,0.000,0.320,0.018,0.000,0.000,0.020],
"Eastern Europe":     [0.000,0.225,0.440,0.000,0.200,0.000,0.000,0.000,0.135],
"Oceania":            [0.000,0.000,0.000,0.090,0.910,0.000,0.000,0.000,0.000],
"Latin America":      [0.000,0.000,0.000,0.000,0.990,0.000,0.000,0.000,0.010],
"Africa":             [0.000,0.000,0.000,0.010,0.950,0.010,0.000,0.030,0.000],
"Middle East":        [0.000,0.000,0.000,0.010,0.790,0.020,0.000,0.170,0.020],
"Asia":               [0.000,0.000,0.000,0.460,0.500,0.020,0.000,0.020,0.000],
"Indian Subcontinent":[0.000,0.010,0.000,0.040,0.220,0.200,0.010,0.530,0.000],
}
AWMS_B={
"North America":      [0.000,0.000,0.000,0.000,1.000,0.000,0.000,0.000,0.000],
"Western Europe":     [0.000,0.200,0.000,0.790,0.000,0.000,0.000,0.000,0.000],
"Eastern Europe":     [0.000,0.240,0.000,0.000,0.290,0.000,0.000,0.000,0.470],
"Oceania":            [0.000,0.000,0.000,0.000,1.000,0.000,0.000,0.000,0.000],
"Latin America":      [0.000,0.000,0.000,0.000,0.990,0.000,0.000,0.000,0.010],
"Africa":             [0.000,0.000,0.000,0.000,1.000,0.000,0.000,0.000,0.000],
"Middle East":        [0.000,0.000,0.000,0.000,0.200,0.190,0.000,0.420,0.190],
"Asia":               [0.000,0.000,0.000,0.410,0.500,0.040,0.000,0.050,0.000],
"Indian Subcontinent":[0.000,0.000,0.000,0.040,0.190,0.210,0.010,0.550,0.000],
}
AWMS_SW={
"North America":      [0.328,0.185,0.042,0.040,0.000,0.406,0.000,0.000,0.000],
"Western Europe":     [0.087,0.000,0.137,0.000,0.028,0.698,0.020,0.000,0.030],
"Eastern Europe":     [0.030,0.000,0.420,0.000,0.247,0.247,0.000,0.000,0.057],
"Oceania":            [0.540,0.000,0.030,0.150,0.000,0.000,0.000,0.000,0.280],
"Latin America":      [0.000,0.080,0.100,0.410,0.000,0.000,0.020,0.000,0.400],
"Africa":             [0.000,0.060,0.060,0.870,0.010,0.000,0.000,0.000,0.000],
"Middle East":        [0.000,0.140,0.000,0.690,0.000,0.170,0.000,0.000,0.000],
"Asia":               [0.000,0.400,0.000,0.540,0.000,0.000,0.000,0.060,0.000],
"Indian Subcontinent":[0.090,0.220,0.160,0.300,0.030,0.000,0.090,0.080,0.030],
}
AWMS_SG19={
"North America":      [0.000,0.000,0.200,0.180,0.620,0.000,0.000,0.000,0.000],
"Western Europe":     [0.000,0.000,0.130,0.000,0.870,0.000,0.000,0.000,0.000],
"Eastern Europe":     [0.000,0.000,0.150,0.150,0.700,0.000,0.000,0.000,0.000],
"Oceania":            [0.000,0.000,0.200,0.000,0.800,0.000,0.000,0.000,0.000],
"Latin America":      [0.000,0.000,0.100,0.000,0.900,0.000,0.000,0.000,0.000],
"Africa":             [0.000,0.000,0.050,0.000,0.950,0.000,0.000,0.000,0.000],
"Middle East":        [0.000,0.000,0.100,0.200,0.700,0.000,0.000,0.000,0.000],
"Asia":               [0.000,0.000,0.050,0.000,0.950,0.000,0.000,0.000,0.000],
"Indian Subcontinent":[0.000,0.000,0.050,0.000,0.950,0.000,0.000,0.000,0.000],
}
AWMS_BL={r:[(AWMS_D[r][i]+AWMS_O[r][i])/2 for i in range(9)] for r in R9}

# -- Nrate 2006 (exact from original lines 515-551) --
NRATE_D06  = rd([0.44,0.48,0.35,0.44,0.48,0.60,0.70,0.47,0.47])
NRATE_O06  = rd([0.31,0.33,0.35,0.50,0.36,0.63,0.79,0.34,0.34])
NRATE_B06  = {r:0.32 for r in R9}
NRATE_MS06 = rd([0.42,0.51,0.55,0.53,1.57,1.57,1.57,0.42,0.42])
NRATE_BS06 = rd([0.24,0.42,0.46,0.46,0.55,0.55,0.55,0.24,0.24])
NRATE_L06  = {r:(0.96 if r=="Western Europe" else 0.82) for r in R9}
NRATE_BR06 = {r:1.10 for r in R9}
NRATE_TK   = {r:0.74 for r in R9}
NRATE_DK   = {r:0.83 for r in R9}
# -- Nrate 2019 (exact from original lines 597-633) --
NRATE_D19  = rd([0.59,0.54,0.42,0.72,0.39,0.44,0.50,0.44,0.65])
NRATE_O19  = rd([0.40,0.42,0.47,0.46,0.31,0.45,0.56,0.38,0.44])
NRATE_B19  = rd([0.32,0.45,0.35,0.32,0.41,0.42,0.39,0.44,0.58])
NRATE_SW19 = rd([0.39,0.65,0.63,0.54,0.59,0.44,0.66,0.61,0.68])
NRATE_L19  = rd([1.13,0.87,0.81,1.04,1.17,1.20,1.11,1.00,1.65])
NRATE_BR19 = rd([1.59,1.14,1.12,1.59,1.23,1.40,1.43,1.35,1.58])
NRATE_CH19B= rd([1.45,0.99,0.96,1.42,1.20,1.29,1.29,1.10,1.62])
NRATE_SH19 = rd([0.35,0.36,0.36,0.43,0.32,0.32,0.32,0.32,0.32])
NRATE_GT19 = rd([0.46,0.46,0.44,0.42,0.34,0.34,0.34,0.34,0.34])
# -- TAM 2006 (exact from original lines 555-587) --
TAM_D06  = rd([604,600,550,500,400,275,275,350,275])
TAM_O06  = rd([389,420,391,330,305,173,173,319,110])
TAM_B06  = rd([380,380,380,380,380,380,380,380,295])
TAM_MS06 = rd([46,50,50,45,28,28,28,28,28])
TAM_BS06 = rd([198,198,180,180,28,28,28,28,28])
TAM_L06  = {r:1.8 for r in R9}; TAM_BR06 = {r:0.9 for r in R9}
TAM_TK   = {r:6.8 for r in R9}; TAM_DK   = {r:2.7 for r in R9}
TAM_SH06 = {r:(48.5 if r in DEVELOPED else 28.0) for r in R9}
TAM_GT06 = {r:(38.5 if r in DEVELOPED else 30.0) for r in R9}
# -- TAM 2019 (exact from original lines 641-676) --
TAM_D19  = rd([650,600,550,488,508,260,349,386,285])
TAM_O19  = rd([407,405,389,359,303,236,275,299,226])
TAM_B19  = rd([380,509,467,380,315,339,381,336,321])
TAM_SW19 = rd([77,76,77,61,65,49,59,58,59])
TAM_L19  = rd([1.5,1.9,1.9,2.0,1.4,1.4,1.2,1.5,1.3])
TAM_BR19 = rd([1.4,1.2,1.1,1.2,0.9,0.8,0.7,0.8,0.8])
TAM_CH19B= rd([1.4,1.4,1.3,1.3,1.1,0.9,0.9,1.2,1.0])
TAM_SH19 = {r:(40.0 if r in DEVELOPED else 31.0) for r in R9}
TAM_GT19 = rd([41,40,36,33,24,24,24,24,24])

def nex(nr,tm,r): return nr[r]*tm[r]/1000*365
def n2o(n,N,aws,ef3,fg):
    tN=n*N; d=iv=0.
    for i,f in enumerate(aws):
        if f<=0: continue
        x=tN*f; d+=x*ef3[i]*MW_N2O; iv+=x*fg[i]*EF4*MW_N2O
    return d,iv

print("Loading production data…")
df_raw=pd.read_csv(PROD_CSV,low_memory=False)
df_c=df_raw[df_raw["Area Code"]<5000].copy()
df_c[YEAR_COLS]=df_c[YEAR_COLS].fillna(0.)
def extr(it,el="Stocks"):
    m=(df_c["Item"]==it)&(df_c["Element"]==el)
    return df_c[m][["Area Code","Area"]+YEAR_COLS].set_index("Area Code")
ctdf=extr("Cattle"); budf=extr("Buffalo"); shdf=extr("Sheep")
gtdf=extr("Goats");  swdf=extr("Swine / pigs"); chdf=extr("Chickens")
dkdf=extr("Ducks");  tkdf=extr("Turkeys")
dadf=extr("Raw milk of cattle","Milk Animals")
ladf=extr("Hen eggs in shell, fresh","Laying")
def gv(ds,ac,yc):
    try:
        if ac in ds.index:
            v=ds.loc[ac,yc] if yc in ds.columns else 0.
            if isinstance(v,pd.Series): v=v.iloc[0]
            return float(v) if pd.notna(v) else 0.
    except: pass
    return 0.
acs=sorted(set(ctdf.index)|set(budf.index)|set(swdf.index)|set(chdf.index)|set(shdf.index)|set(gtdf.index))
an={}
for ds in [ctdf,budf,shdf,gtdf,swdf,chdf]:
    for ac in ds.index.unique():
        if ac not in an:
            v=ds.loc[ac,"Area"]; an[ac]=v if isinstance(v,str) else v.iloc[0]
ar={ac:get_region(an[ac]) for ac in acs}
print(f"  {len(acs)} countries.")
df_em=pd.read_csv(EMISS_CSV,low_memory=False)
fao_r=df_em[(df_em["Area"]=="World")&(df_em["Item"]=="Manure Management")&(df_em["Element"]=="Emissions (N2O)")&(df_em["Source"]=="FAO TIER 1")]
FAO_PUB=dict(zip(range(1970,2021),fao_r[YEAR_COLS].astype(float).values[0]))

print(f"Computing {len(acs)}x{len(YEAR_COLS)} country-years…")
recs=[]
for ac in acs:
    cty=an[ac]; reg=ar[ac]
    for yc in YEAR_COLS:
        yr=int(yc[1:])
        ctot=gv(ctdf,ac,yc); dn=min(gv(dadf,ac,yc),ctot); on=ctot-dn
        bn=gv(budf,ac,yc); sn=gv(swdf,ac,yc)
        chtot=gv(chdf,ac,yc)*1000; ln=min(gv(ladf,ac,yc)*1000,chtot); brn=chtot-ln
        dkn=gv(dkdf,ac,yc)*1000; tkn=gv(tkdf,ac,yc)*1000
        shn=gv(shdf,ac,yc); gtn=gv(gtdf,ac,yc)
        d={v:0. for v in["s06","n06","s19","n19"]}
        iv={v:0. for v in["s06","n06","s19","n19"]}
        sp={k:0. for k in["Dairy","OtherCattle","Buffalo","Swine","Layers","Broilers","Ducks","Turkeys","Sheep","Goats"]}
        if dn>0:
            de,ie=n2o(dn,nex(NRATE_D06,TAM_D06,reg),AWMS_D[reg],EF3_CAT06,FG_D06)
            d["s06"]+=de; iv["s06"]+=ie; sp["Dairy"]+=(de+ie)*KG_TO_GG
            de,ie=n2o(dn,nex(NRATE_D19,TAM_D19,reg),AWMS_D[reg],EF3_CAT19,FG_D19)
            d["s19"]+=de; iv["s19"]+=ie
        if on>0:
            de,ie=n2o(on,nex(NRATE_O06,TAM_O06,reg),AWMS_O[reg],EF3_CAT06,FG_O06)
            d["s06"]+=de; iv["s06"]+=ie; sp["OtherCattle"]+=(de+ie)*KG_TO_GG
            de,ie=n2o(on,nex(NRATE_O19,TAM_O19,reg),AWMS_O[reg],EF3_CAT19,FG_O19)
            d["s19"]+=de; iv["s19"]+=ie
        if ctot>0:
            nx_d06=nex(NRATE_D06,TAM_D06,reg); nx_o06=nex(NRATE_O06,TAM_O06,reg)
            de,ie=n2o(ctot,(nx_d06+nx_o06)/2,AWMS_BL[reg],EF3_CAT06,FG_BL06)
            d["n06"]+=de; iv["n06"]+=ie
            nx_d19=nex(NRATE_D19,TAM_D19,reg); nx_o19=nex(NRATE_O19,TAM_O19,reg)
            de,ie=n2o(ctot,(nx_d19+nx_o19)/2,AWMS_BL[reg],EF3_CAT19,FG_BL19)
            d["n19"]+=de; iv["n19"]+=ie
        if bn>0:
            de,ie=n2o(bn,nex(NRATE_B06,TAM_B06,reg),AWMS_B[reg],EF3_CAT06,FG_B06)
            d["s06"]+=de;iv["s06"]+=ie;d["n06"]+=de;iv["n06"]+=ie;sp["Buffalo"]+=(de+ie)*KG_TO_GG
            de,ie=n2o(bn,nex(NRATE_B19,TAM_B19,reg),AWMS_B[reg],EF3_CAT19,FG_B19)
            d["s19"]+=de;iv["s19"]+=ie;d["n19"]+=de;iv["n19"]+=ie
        if sn>0:
            sw_acc=0.
            for frac,nr,tm in[(0.9,NRATE_MS06,TAM_MS06),(0.1,NRATE_BS06,TAM_BS06)]:
                de,ie=n2o(sn*frac,nex(nr,tm,reg),AWMS_SW[reg],EF3_SW06,FG_SW06)
                d["s06"]+=de;iv["s06"]+=ie;sw_acc+=(de+ie)
            sp["Swine"]+=sw_acc*KG_TO_GG
            nx_m=nex(NRATE_MS06,TAM_MS06,reg);nx_b=nex(NRATE_BS06,TAM_BS06,reg)
            de,ie=n2o(sn,0.9*nx_m+0.1*nx_b,AWMS_SW[reg],EF3_SW06,FG_SW06)
            d["n06"]+=de;iv["n06"]+=ie
            de,ie=n2o(sn,nex(NRATE_SW19,TAM_SW19,reg),AWMS_SW[reg],EF3_SW19,FG_SW19)
            d["s19"]+=de;iv["s19"]+=ie;d["n19"]+=de;iv["n19"]+=ie
        if ln>0:
            N=ln*nex(NRATE_L06,TAM_L06,reg); de=N*EF3_POUL*MW_N2O; ie=N*FG_POUL*EF4*MW_N2O
            d["s06"]+=de;iv["s06"]+=ie;sp["Layers"]+=(de+ie)*KG_TO_GG
            N=ln*nex(NRATE_L19,TAM_L19,reg); d["s19"]+=N*EF3_POUL*MW_N2O;iv["s19"]+=N*FG_POUL*EF4*MW_N2O
        if brn>0:
            N=brn*nex(NRATE_BR06,TAM_BR06,reg); de=N*EF3_POUL*MW_N2O; ie=N*FG_POUL*EF4*MW_N2O
            d["s06"]+=de;iv["s06"]+=ie;sp["Broilers"]+=(de+ie)*KG_TO_GG
            N=brn*nex(NRATE_BR19,TAM_BR19,reg); d["s19"]+=N*EF3_POUL*MW_N2O;iv["s19"]+=N*FG_POUL*EF4*MW_N2O
        if chtot>0:
            nx_bld=(TAM_BR06[reg]+TAM_L06[reg])/2*0.83/1000*365
            N=chtot*nx_bld; d["n06"]+=N*EF3_POUL*MW_N2O;iv["n06"]+=N*FG_POUL*EF4*MW_N2O
            nx_bld=NRATE_CH19B[reg]*TAM_CH19B[reg]/1000*365
            N=chtot*nx_bld; d["n19"]+=N*EF3_POUL*MW_N2O;iv["n19"]+=N*FG_POUL*EF4*MW_N2O
        if dkn>0:
            N=dkn*nex(NRATE_DK,TAM_DK,reg); de=N*EF3_POUL*MW_N2O; ie=N*FG_POUL*EF4*MW_N2O
            for v in["s06","n06","s19","n19"]: d[v]+=de; iv[v]+=ie
            sp["Ducks"]+=(de+ie)*KG_TO_GG
        if tkn>0:
            N=tkn*nex(NRATE_TK,TAM_TK,reg); de=N*EF3_POUL*MW_N2O; ie=N*FG_POUL*EF4*MW_N2O
            for v in["s06","n06","s19","n19"]: d[v]+=de; iv[v]+=ie
            sp["Turkeys"]+=(de+ie)*KG_TO_GG
        if shn>0:
            de,ie=n2o(shn,nex(NRATE_SH19,TAM_SH19,reg),AWMS_SG19[reg],EF3_SG19,FG_SG19)
            d["s19"]+=de;iv["s19"]+=ie;d["n19"]+=de;iv["n19"]+=ie;sp["Sheep"]+=(de+ie)*KG_TO_GG
        if gtn>0:
            de,ie=n2o(gtn,nex(NRATE_GT19,TAM_GT19,reg),AWMS_SG19[reg],EF3_SG19,FG_SG19)
            d["s19"]+=de;iv["s19"]+=ie;d["n19"]+=de;iv["n19"]+=ie;sp["Goats"]+=(de+ie)*KG_TO_GG
        recs.append({"Year":yr,"Area_Code":ac,"Country":cty,"Region":reg,
            "Direct_2006split_GgN2O":d["s06"]*KG_TO_GG,"Direct_2006nosplit_GgN2O":d["n06"]*KG_TO_GG,
            "Direct_2019split_GgN2O":d["s19"]*KG_TO_GG,"Direct_2019nosplit_GgN2O":d["n19"]*KG_TO_GG,
            "Indirect_2006split_GgN2O":iv["s06"]*KG_TO_GG,"Indirect_2006nosplit_GgN2O":iv["n06"]*KG_TO_GG,
            "Indirect_2019split_GgN2O":iv["s19"]*KG_TO_GG,"Indirect_2019nosplit_GgN2O":iv["n19"]*KG_TO_GG,
            "Total_2006split_GgN2O":(d["s06"]+iv["s06"])*KG_TO_GG,"Total_2006nosplit_GgN2O":(d["n06"]+iv["n06"])*KG_TO_GG,
            "Total_2019split_GgN2O":(d["s19"]+iv["s19"])*KG_TO_GG,"Total_2019nosplit_GgN2O":(d["n19"]+iv["n19"])*KG_TO_GG,
            "Dairy_GgN2O":sp["Dairy"],"OtherCattle_GgN2O":sp["OtherCattle"],"Buffalo_GgN2O":sp["Buffalo"],
            "Swine_GgN2O":sp["Swine"],"Layers_GgN2O":sp["Layers"],"Broilers_GgN2O":sp["Broilers"],
            "Ducks_GgN2O":sp["Ducks"],"Turkeys_GgN2O":sp["Turkeys"],
            "Sheep_GgN2O":sp["Sheep"],"Goats_GgN2O":sp["Goats"]})

print(f"  {len(recs):,} records.")
df=pd.DataFrame(recs)
df.to_csv((str(OUT_A_DATA) + "/n2o_mm/n2o_mm_country.csv"),index=False); print("Saved country CSV")
SCOLS=["Dairy_GgN2O","OtherCattle_GgN2O","Buffalo_GgN2O","Swine_GgN2O","Layers_GgN2O","Broilers_GgN2O","Ducks_GgN2O","Turkeys_GgN2O","Sheep_GgN2O","Goats_GgN2O"]
TCOLS=["Total_2006split_GgN2O","Total_2006nosplit_GgN2O","Total_2019split_GgN2O","Total_2019nosplit_GgN2O","Direct_2006split_GgN2O","Direct_2019split_GgN2O","Indirect_2006split_GgN2O","Indirect_2019split_GgN2O"]
dg=df.groupby("Year")[TCOLS+SCOLS].sum().reset_index()
dg["FAO_published_GgN2O"]=dg["Year"].map(FAO_PUB)
for t,c in[("2006split","Total_2006split_GgN2O"),("2006nosplit","Total_2006nosplit_GgN2O"),("2019split","Total_2019split_GgN2O"),("2019nosplit","Total_2019nosplit_GgN2O")]:
    dg[f"Ratio_{t}_to_FAO"]=dg[c]/dg["FAO_published_GgN2O"]
dg.to_csv((str(OUT_A_DATA) + "/n2o_mm/n2o_mm_global.csv"),index=False); print("Saved global CSV")
dr=df.groupby(["Region","Year"])[TCOLS+SCOLS].sum().reset_index()
dr["_o"]=dr["Region"].apply(lambda r:R9.index(r) if r in R9 else 99)
dr=dr.sort_values(["_o","Year"]).drop(columns="_o")
dr.to_csv((str(OUT_A_DATA) + "/n2o_mm/n2o_mm_regional.csv"),index=False); print("Saved regional CSV")
d20=df[df["Year"]==2020]
sr=d20.groupby("Region")[SCOLS+["Total_2006split_GgN2O","Total_2019split_GgN2O"]].sum().reindex(R9).reset_index()
sr.to_csv((str(OUT_A_DATA) + "/n2o_mm/n2o_mm_species2020.csv"),index=False); print("Saved species2020 CSV")
print("\nVERIFICATION:")
ref={1970:419.1,1975:470.6,1980:488.5,1985:514.9,1990:551.7,1995:612.4,2000:607.0,2005:593.4,2010:612.2,2015:616.2,2020:633.1}
print(f"  Year  Computed  Ref      Delta")
for yr,rv in sorted(ref.items()):
    row=dg[dg["Year"]==yr]; v=row["Total_2006split_GgN2O"].values[0]
    print(f"  {yr}  {v:8.2f}  {rv:7.1f}  {v-rv:+7.2f}")

# Add EDGAR N2O MM column to global CSV
import pandas as _pd2, numpy as _np2
_dfe = _pd2.ExcelFile(str(EDGAR_N2O_NEW)).parse('IPCC 2006', header=9)
_yc  = [f'Y_{y}' for y in range(1970,2021)]
_ev  = _dfe[_dfe['ipcc_code_2006_for_standard_report']=='3.A.2'][_yc].apply(_pd2.to_numeric,errors='coerce').fillna(0).sum().values
_dg2 = _pd2.read_csv((str(OUT_A_DATA) + '/n2o_mm/n2o_mm_global.csv'))
_dg2['EDGAR_GgN2O'] = _np2.round(_ev, 3)
_dg2.to_csv((str(OUT_A_DATA) + '/n2o_mm/n2o_mm_global.csv'), index=False)
print('Added EDGAR_GgN2O to n2o_mm_global.csv')
