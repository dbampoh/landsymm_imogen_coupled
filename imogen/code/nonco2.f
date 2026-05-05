!Subroutines in this file implement the update of CH4 and N2O mixing ratios and radiative forcing.
!Calculations are from the FAIR model:
!Smith et al. (2018). FAIR v1.3: a simple emissions-based impulse response and carbon cycle model.
!Geoscientific Model Development, 11(6), 2273–2297. https://doi.org/10.5194/gmd-11-2273-2018
!
!TODO??:  2.1.3 Methane oxidation to CO2 ???? eq. 6
!
!Thomas Pugh and Peter Anthoni
!17.11.19

!Calculate the effective radiative forcing from CH4 and N2O mixing ratios and add this to the non-CO2
!radiative forcing from other sources
      SUBROUTINE FAIR_NON_CO2_GHG(CH4_PPBV,N2O_PPBV,CH4_INIT_PPBV,N2O_INIT_PPBV,CO2_PPMV,
     &  CO2_INIT_PPMV,Q_CH4,Q_N2O,Q_CO2_FAIR)

      IMPLICIT NONE

      REAL CH4_PPBV !IN CH4 mixing ratio (ppbv)
      REAL N2O_PPBV !IN N2O mixing ratio (ppbv)
      REAL CO2_PPMV !IN CO2 mixing ratio (ppbv)
      REAL CH4_INIT_PPBV !IN Initial CH4 mixing ratio for model run (ppbv)
      REAL N2O_INIT_PPBV !IN Initial CH4 mixing ratio for model run (ppbv)
      REAL CO2_INIT_PPMV !IN Initial CH4 mixing ratio for model run (ppbv)

      REAL Q_NON_CO2 !IN/OUT Non-CO2 radiative forcing excluding CH4 and N2O (IN) and including them (OUT) (W m-2)
      REAL Q_NON_CO2_IN !WORK Non-CO2 radiative forcing excluding CH4 and N2O (IN) (W m-2)

      REAL Q_CH4 !WORK CH4 radiative forcing (W m-2)
      REAL Q_N2O !WORK N2O radiative forcing (W m-2)
      REAL Q_CO2_FAIR !WORK CO2 radiative forcing (W m-2)

      PRINT *,'In FAIR_NON_CO2_GHG'

      !FCO2 = [(-2.4*1e-7)*(C + Cpi)^2 + (7.2*1e-4)*|C - Cpi| - (1.05*1e-4)*(N + Npi) + 5.36] * log(C/Cpi)
      Q_CO2_FAIR = ( -2.4e-7*((CO2_PPMV+CO2_INIT_PPMV)**2) + 7.2e-4*(CO2_PPMV+CO2_INIT_PPMV) -
     &  1.05e-4*(N2O_PPBV+N2O_INIT_PPBV) + 5.36 ) * LOG(CO2_PPMV/CO2_INIT_PPMV)

      !FN2O = [(-4.0*1e-6)*(C + Cpi) + (2.1*1e-6)*(N + Npi) − (2.45*1e−6) * (M + Mpi) + 0.117] * (√N − √Npi)
      Q_N2O = ( -4.0e-6*(CO2_PPMV+CO2_INIT_PPMV) + 2.1e-6*(N2O_PPBV+N2O_INIT_PPBV) - 2.45e-6*(CH4_PPBV+CH4_INIT_PPBV) + 0.117)
     &  * ( SQRT(N2O_PPBV) - SQRT(N2O_INIT_PPBV))

      !FCH4 = [−(6.5*1e−7) * (M + Mpi) − (4.1*1e−6) * (N + Npi) + 0.043] * (√M − √Mpi)
      Q_CH4 = ( -6.5e-7*(CH4_PPBV + CH4_INIT_PPBV) - 4.1e-6*(N2O_PPBV + N2O_INIT_PPBV) + 0.043 )
     &  * (SQRT(CH4_PPBV) - SQRT(CH4_INIT_PPBV))

      RETURN
      END

!Update the mixing ratios of CH4 and N2O based on a simple box model approach
      SUBROUTINE FAIR_NON_CO2_GHG_BUDGET(IYEAR,NONCO2_EMISSIONS_LPJG,YR_LPJG_NONCO2,NYR_LPJG_FLUX,CH4_LPJG,N2O_LPJG,
     &  YR_EMISS,NYR_EMISS_NONCO2,CH4_EMISS,N2O_EMISS,CH4_PPBV,N2O_PPBV,TAU_DECAY_CH4,TAU_DECAY_N2O,DIR_COMMON,THISYEAR)

      IMPLICIT NONE

      !Set some molar masses in g/mol (https://www.engineeringtoolbox.com/molecular-mass-air-d_679.html)
      REAL MM_AIR,MM_CH4,MM_N2O,MM_N2
      PARAMETER(MM_AIR=28.9647)
      PARAMETER(MM_CH4=16.04)
      PARAMETER(MM_N2O=44.01)
      PARAMETER(MM_N2=2*14.0067)

      !Mass of the atmosphere https://doi.org/10.1175/JCLI-3299.1 the dry air mass as 5.1352 ± 0.0003 × 10^18 kg
      REAL MA
      PARAMETER(MA = 5.1352e18) !kg

      INTEGER IYEAR !IN Year we are at in the run
      INTEGER YR_LPJG_NONCO2(300) !IN Years in which non-CO2 fluxes from LPJG are prescribed
      INTEGER YR_EMISS(300) !IN Years in which CO2 emissions are prescribed
      INTEGER NYR_EMISS_NONCO2  !IN Number of years of CH4 and N2O emission data in file.
      INTEGER NYR_LPJG_FLUX     !IN Number of years of emission data in LPJ-GUESS C flux file

      LOGICAL NONCO2_EMISSIONS_LPJG !IN Whether to use LPJG to provide natural CH4 and N2O emissions

      REAL CH4_LPJG(300) !IN Values of LPJG CH4 flux read in (up to NYR_LPJG_FLUX)
      REAL N2O_LPJG(300) !IN Values of LPJG N2O flux read in (up to NYR_LPJG_FLUX)
      REAL CH4_EMISS(300) !IN Values of CH4 emissions read in (up to NYR_EMISS)
      REAL N2O_EMISS(300) !IN Values of N2O emissions read in (up to NYR_EMISS)
      REAL CH4_PPBV !IN/OUT Atmospheric CH4 mixing ratio (ppbv) for last year (IN) and this year (OUT)
      REAL N2O_PPBV !IN/OUT Atmospheric N2O mixing ratio (ppbv) for last year (IN) and this year (OUT)

      REAL CH4_EMISS_LOCAL !WORK CH4 emission for this year of model run
      REAL N2O_EMISS_LOCAL !WORK N2O emission for this year of model run
      REAL DGHG_DT_CH4 !WORK Equivalent of CH4 emissions in molar mixing ratios
      REAL DGHG_DT_N2O !WORK Equivalent of N2O emissions in molar mixing ratios

      REAL TAU_DECAY_CH4 !IN Atmospheric lifetime of CH4 (years)
      REAL TAU_DECAY_N2O !IN Atmospheric lifetime of N2O (years)

      REAL CH4_PPBV_IN !WORK Initial CH4 mixing ratio before update in this subroutine
      REAL N2O_PPBV_IN !WORK Initial N2O mixing ratio before update in this subroutine

      CHARACTER(LEN=4) THISYEAR !WORK string version of IYEAR for use in locating input/output files
      CHARACTER(LEN=180) DIR_COMMON !Directory containing files shared between LPJ-GUESS and IMOGEN

      INTEGER EMISS_TALLY
      INTEGER N

      PRINT *,'In FAIR_NON_CO2_GHG_BUDGET'

      !Save input for later and convert from ppbv and ppb to mixing ratios
      CH4_PPBV_IN=CH4_PPBV*1.0e-9
      N2O_PPBV_IN=N2O_PPBV*1.0e-9

      !Find the value of anthropogenic (+natural if NONCO2_EMISSIONS_LPJG=.FALSE.) CH4 and N2O emissions for this year
      EMISS_TALLY=0
      DO N = 1,NYR_EMISS_NONCO2
        IF(YR_EMISS(N).EQ.IYEAR-1) THEN !TODO: SHOULD THIS BE IYEAR-1 RATHER THAN IYEAR??? - TP 30.07.15
          CH4_EMISS_LOCAL=CH4_EMISS(N)
          N2O_EMISS_LOCAL=N2O_EMISS(N)
          EMISS_TALLY=EMISS_TALLY+1
        ENDIF
      ENDDO

      IF(EMISS_TALLY.NE.1) THEN
        PRINT *,'Non-CO2 emission dataset does not match run'
        OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
        WRITE(98,*)'Non-CO2 emission dataset does not match run'
        CLOSE(98)
        STOP
      ENDIF

      IF (NONCO2_EMISSIONS_LPJG) THEN
      !Find the value of LPJ-GUESS CH4 and N2O emissions for this year
        EMISS_TALLY=0
        DO N = 1,NYR_LPJG_FLUX
        PRINT *,'YR_LPJG_NONCO2(N) ',YR_LPJG_NONCO2(N)
          IF(YR_LPJG_NONCO2(N).EQ.IYEAR-1) THEN !TODO: SHOULD THIS BE IYEAR-1 RATHER THAN IYEAR??? - TP 30.07.15
            CH4_EMISS_LOCAL=CH4_EMISS_LOCAL+CH4_LPJG(N)
            N2O_EMISS_LOCAL=N2O_EMISS_LOCAL+N2O_LPJG(N)
            EMISS_TALLY=EMISS_TALLY+1
          ENDIF
        ENDDO

        IF(EMISS_TALLY.NE.1) THEN
          PRINT *,'LPJG C flux dataset does not match run.'
          OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
          WRITE(98,*)'LPJG non-CO2 flux dataset does not match run.',IYEAR-1,EMISS_TALLY
          CLOSE(98)
          STOP
        ENDIF
      ENDIF

      !emiss.annual.ghg are for CH4 (CH4 emissions TgCH4/yr) and N2O (N2O emissions TgN2O/yr)
      !CH4  anthropogenic + natural emissions
      !N2O  anthropogenic + natural emissions, FAIR converts to a N2 equivalent mass from TgN2O/yr

      !need the E(t) also in kg/yr if Ma (Eq.4) is in kg, convert TgCH4/yr to kg/yr for use in Eq.4!
      !!emiss.annual.ghg[emiss.annual.ghg[,"Year"]%in%c(1850,1900,1950,2000,2050),]
      !!emiss.annual.ghg.kg.yr=emiss.annual.ghg
      !convert ch4 from TgCH4/yr to kgCh4/yr
      CH4_EMISS_LOCAL = CH4_EMISS_LOCAL * (1.0e12/1.0e3)
      !convert n2o from TgN2O/yr to kgN2/yr
      N2O_EMISS_LOCAL = N2O_EMISS_LOCAL * (MM_N2/MM_N2O) * (1.0e12/1.0e3)

      !Equivalent increase in molar mixing ratios δC:
      ! Eq. 4 dC(t)=E(t)/Ma * mol.weight.air/mol.weight.gas
      DGHG_DT_CH4=CH4_EMISS_LOCAL/MA * MM_AIR/MM_CH4
      DGHG_DT_N2O=N2O_EMISS_LOCAL/MA * MM_AIR/MM_N2
      !CHECK: do we need to use mol weight of n2 or n2o here, since we converted to TgN2eq/yr above????

      !The model updates the atmospheric molar mixing ratios C for this year based on new emissions
      !and the natural lifetime decay (tau):
      !Eq. 5: C[t] = C[t−1] + 1/2*(δC[t−1] +δC[t] ) − C[t−1]*(1−exp(−1/tau))
      !Simplify to just use values from this year
      CH4_PPBV = CH4_PPBV_IN + DGHG_DT_CH4 - (CH4_PPBV_IN*(1-exp(-1.0/TAU_DECAY_CH4)))
      N2O_PPBV = N2O_PPBV_IN + DGHG_DT_N2O - (N2O_PPBV_IN*(1-exp(-1.0/TAU_DECAY_N2O)))

      !Convert back to ppbv
      CH4_PPBV = CH4_PPBV*1e9
      N2O_PPBV = N2O_PPBV*1e9


      RETURN
      END
