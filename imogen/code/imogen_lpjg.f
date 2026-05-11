!----------------------------------------------------------------------
C Main controller for the IMOGEN model.
C This version only calculates change in climatology (ready for LPJ
C implementation)
C C. Huntingford (August 2004).
C C. Huntingford (August 2014).
C
C Modified for coupling to LPJ-GUESS model
C T. Pugh
C 13.07.15
C
C Compile with:
C gfortran -c -ffixed-line-length-132 imogen_lpjg.f nonco2.f
C gfortran -o imogen_lpjg.exe imogen_lpjg.o nonco2.o

      PROGRAM IMOGEN
      IMPLICIT NONE

C Define basic timestepping variables
      INTEGER
     & YEAR1             !IN First year of the numerical experiment
     &,IYEND             !IN Stop year of the ENTIRE run
     &,YEAR1_LPJG        !IN First year of the whole LPJ-GUESS simulation - TP 13.07.15
     &,IYEAR             !WORK Year we are at in the run

      LOGICAL
     & FILE_NON_CO2      !IN If true, then non-CO2 radiative forcings ar
                         !contained within a file.

      INTEGER
     & IM,MM             !IN Monthly loop counter and number of months i
     &,MD                !WORK Number of days in (GCM) month
     &,STEP_DAY          !IN Number of daily timesteps of IMPACTS_MODEL
     &,ISTEP             !Looping parameter over suib-daily periods
     &,SEC_DAY           !WORK Number of seconds in each day
     &,NSDMAX            !IN Maximum number of possible subdaily
     &                   !increments
      PARAMETER(MM=12)
      PARAMETER(MD=30)   !At present hardwired as 30 days per month (as
     &                   !in GCM)
      PARAMETER(NSDMAX=24)
      PARAMETER(SEC_DAY=86400)

      INTEGER MTHDAY(12)     !Number of days per month - TP 13.07.15
      DATA MTHDAY /31,28,31,30,31,30,31,31,30,31,30,31/

      INTEGER
     & IGP,IMD,IMM,IND   !Loop counters for anomaly output - TP 13.07.15
C
      REAL
     & Q_CO2             !WORK Radiative forcing due to CO2 (W/m2)
     &,Q_NON_CO2         !WORK Radiative forcing due to non-CO2 (W/m2)
     &,Q_CH4             !WORK Radiative forcing due to CH4 (W/m2)
     &,Q_N2O             !WORK Radiative forcing due to N2O (W/m2)
     &,Q_CO2_FAIR        !WORK Radiative forcing due to CO2 as calculated by the FAIR model (W/m2)

      INTEGER
     & NYR_NON_CO2       !IN Number of years for which NON_CO2 forcing
C                        !is prescribed.
     &,TALLY_CO2_FILE    !WORK If used, checks CO2 value available in
C                        !file "FILE_SCEN_CO2_PPMV"
     &,YR_CO2_FILE       !WORK If used, reads in years available in
C                        !file "FILE_SCEN_CO2_PPMV"
      REAL
     & CO2_FILE_PPMV     !IN If used, is prescribed CO2 value for read
C                        !in years in "FILE_SCEN_CO2_PPMV"

C Define variables needed by the GCM analogue model
      REAL
     & Q2CO2             !IN Radiative forcing due to doubling CO2 (W/m2
     &,F_OCEAN           !IN Fractional coverage of the ocean
     &,KAPPA_O           !IN Ocean eddy diffusivity (W/m/K)
     &,LAMBDA_L          !IN Inverse of climate sensitivity
C                        !over land (W/m2/K)
     &,LAMBDA_O          !IN Inverse of climate sensitivity
C                        !over ocean (W/m2/K)
     &,MU                !IN Ratio of land to ocean temperature
C                        !anomalies
     &,T_OCEAN_INIT      !IN Initial ocean temperature (K)

      REAL
     & TAU_DECAY_CH4     !IN Atmospheric lifetime of CH4 (years)
     &,TAU_DECAY_N2O     !IN Atmospheric lifetime of N2O (years)

      INTEGER
     & N_OLEVS           !Number of ocean levels in thermal calculation
     &,NFARRAY           !Array size for FA_OCEAN
      PARAMETER(NFARRAY=10000) !Must be at least as large as the total number of simulation years (across whole run) * NCALLYR, as legacy values of FA_OCEAN must be maintained. 10000 allows for 500 year runs.

      REAL
     & FA_OCEAN(NFARRAY)         ! IN/OUT CO2 fluxes
                                 ! from the atmosphere to the ocean
                                 ! (ie positive upwards) (ppm/m2/yr)
     &,OCEAN_AREA                ! WORK Ocean area (m2)
      PARAMETER(OCEAN_AREA=3.627E14)

      CHARACTER*180
     & DIR_PATT          !Directory containing the patterns
     &,DIR_CLIM          !Directory containing initialising climatology.
     &,DIR_ANOM          !Directory containing prescribed anomalies
     &,DIR_COMMON        !Directory containing files shared between LPJ-GUESS and IMOGEN - TP 13.07.15
     &,FILE_CLIM         !File containing initialising climatology.

      PARAMETER(N_OLEVS=254)

      REAL
     & DTEMP_O(N_OLEVS)  !IN/OUT Ocean temperature anomalies (K)
     &,DT_OCEAN          !Top level ocean anomaly (K)
C
C Define various conditions and switches for the runs.
C Note that switching off INCLUDE_CO2 and INCLUDE_NON_CO2 is effectively
      REAL
     & CO2_INIT_PPMV     !IN Initial CO2 concentration (ppmv)
     &,CONV              !WORK Converts global emission of C (Gt) into
     &                   !change in atmospheric CO2 (ppm)
      PARAMETER(CONV=0.471)

      REAL
     & CH4_INIT_PPBV     !IN Initial CH4 concentration (ppbv)
     &,N2O_INIT_PPBV     !IN Initial N2O concentration (ppbv)

      CHARACTER*180
     & FILE_SCEN_EMITS   !IN If used, file containing CO2 emissions in G
     &,FILE_NON_CO2_VALS !IN If used, file containing non-CO2 values
     &,FILE_SCEN_CO2_PPMV   !IN If used, file containing CO2 values (in
     &,FILE_LPJG_FLUX    !IN If used, file containing LPJ-GUESS flux values - TP 13.07.15
     &,FILE_CH4_N2O_EMITS !IN If used, file containing CH4 and N2O emission values
     &,FILE_LPJG_CH4_N2O_FLUX !IN If used, file containing LPJ-GUESS CH4 and N2O flux values
     &,FILE_GRIDLIST  !file containing gridlist :DKB 27/07/2022

      LOGICAL
     & ANLG              !IN If true, then use the GCM analogue model
     &,ANOM              !IN If true, then use the GCM analogue model
     &,C_EMISSIONS       !IN If true, means CO2 concentration is calcula
     &,C_EMISSIONS_IN       !IN If true, means CO2 concentration is calcula -TP 30.07.15
     &,LPJG_CFLUX        !IN If true, take land C flux from LPJ-GUESS output file - TP 13.07.15
     &,INCLUDE_CO2       !IN Are adjustments to CO2 values allowed?
     &,INCLUDE_CO2_IN       !IN Are adjustments to CO2 values allowed? -TP 30.07.15
     &,INCLUDE_NON_CO2   !IN Are adjustments to non-CO2 values allowed?
     &,DAILYOUT          !IN Are outputs daily (true) or monthly (false)?
     &,LAND_FEED         !IN Are land feedbacks allowed on atmospheric C
     &,OCEAN_FEED        !IN Are ocean feedbacks allowed on atmospheric
     &,SPINUP            !IN Are we in the spin-up phase of LPJ-GUESS? - TP 13.07.15
     &,NONCO2_EMISSIONS  !IN If true, use FAIR model for CH4 and N2O forcing
     &,NONCO2_EMISSIONS_LPJG !IN Whether to use LPJG to provide natural CH4 and N2O emissions (if NONCO2_EMISSIONS==T)
     &,CO2_RF_FAIR       !IN Whether to use the CO2 radiative forcing calculation from the FAIR model (T) or IMOGEN standard (F)

      INTEGER
     & NYR_EMISS         !IN Number of years of emission data in file.
     &,NYR_LPJG_FLUX     !IN Number of years of emission data in LPJ-GUESS C flux file - TP 13.07.15
     &,NYR_EMISS_NONCO2  !IN Number of years of CH4 and N2O emission data in file.
     &,YR_EMISS(300)     !IN Years in which CO2 emissions are prescribed
                         !(only first NYR_EMISS array components are used)
     &,YR_EMISS_NONCO2(300) !IN Years in which CO2 emissions are prescribed
                            !(only first NYR_EMISS array components are used)
                         !For this code, years must be sequential
     &,YR_LPJG(300)      !IN Years in which C fluxes from LPJG are prescribed - TP 13.07.15
                         !(only first NYR_LPJG_FLUX array components are used)
     &,YR_LPJG_NONCO2(300)      !IN Years in which non-CO2 fluxes from LPJG are prescribed
                                !(only first NYR_LPJG_FLUX array components are used)
     &,EMISS_TALLY       !Checks that datafile of emissions includes
     &                   !year of interest

      REAL
     & D_LAND_ATMOS      !Change in atmospheric CO2 concentration due to
                         !feedbacks (ppm/year).
     &,D_OCEAN_ATMOS     !Change in atmospheric CO2 concentration due to
                         !feedbacks (ppm/year).
      LOGICAL
     & L_IMPACTS         !.TRUE. if IMOGEN is used to drive an impacts
                         !model

      REAL
     & C_EMISS(300)      !IN Values of CO2 emissions read in (up to NYR_EMISS)
     &,C_EMISS_LOCAL     !WORK Local value of C_EMISS
     &,C_LPJG(300)       !IN Values of LPJG C flux read in (up to NYR_LPJG_FLUX) - TP 13.07.15
     &,C_LPJG_LOCAL      !WORK Local value of C_LPJG - TP 13.07.15
     &,CH4_EMISS(300)    !IN Values of CH4 emissions read in (up to NYR_EMISS)
     &,N2O_EMISS(300)    !IN Values of N2O emissions read in (up to NYR_EMISS)
     &,CH4_LPJG(300)     !IN Values of LPJG CH4 flux read in (up to NYR_LPJG_FLUX)
     &,N2O_LPJG(300)     !IN Values of LPJG N2O flux read in (up to NYR_LPJG_FLUX)

      CHARACTER*4
     & DRIVE_MONTH(12)   !WORK Month labels for reading in files

      INTEGER
     & GPOINTS           !IN Number of points, not including Antartica
      PARAMETER(GPOINTS=1631)

      REAL
     & T_ANOM(GPOINTS,MM)             !WORK Temperature anomalies (K)
     &,PRECIP_ANOM(GPOINTS,MM)        !WORK Precip anomalies (mm/day)
     &,RH15M_ANOM(GPOINTS,MM)         !WORK Relative humidity anomalies
     &,UWIND_ANOM(GPOINTS,MM)         !WORK u-wind anomalies (m/s)
     &,VWIND_ANOM(GPOINTS,MM)         !WORK v-wind anomalies (m/s)
     &,DTEMP_ANOM(GPOINTS,MM)         !WORK Diurnal Temperature (K)
     &,PSTAR_HA_ANOM(GPOINTS,MM)      !WORK Pressure anomalies (hPa)
     &,SW_ANOM(GPOINTS,MM)            !WORK Shortwave radiation anomalie
     &,LW_ANOM(GPOINTS,MM)            !WORK Longwave radiation anomalies
     &,LAT(GPOINTS)                   !WORK Latitudinal position of land
     &,LONG(GPOINTS)                  !WORK Longitudinal position of land

C Driving "control" climatology
      REAL
     & T_CLIM(GPOINTS,MM)                !IN Control climate temperature
     &,RAINFALL_CLIM(GPOINTS,MM)         !IN Control climate rainfall (m
     &,SNOWFALL_CLIM(GPOINTS,MM)         !IN Control climate snowfall (m
     &,RH15M_CLIM(GPOINTS,MM)            !IN Control climate relative hu
     &,UWIND_CLIM(GPOINTS,MM)            !IN Control climate u-wind (m/s
     &,VWIND_CLIM(GPOINTS,MM)            !IN Control climate v-wind (m/s
     &,DTEMP_CLIM(GPOINTS,MM)            !IN Control climate diurnal Tem
     &,PSTAR_HA_CLIM(GPOINTS,MM)         !IN Control climate pressure (h
     &,SW_CLIM(GPOINTS,MM)               !IN Control climate shortwave r
     &,LW_CLIM(GPOINTS,MM)               !IN Control climate longwave ra
     &,F_WET_CLIM(GPOINTS,MM)            !IN Control climate fraction we

C Create fine temperal resolution year of climatology (to be used by imp
C studies or DGVMs).
      REAL
     & T_OUT(GPOINTS,MM,MD,NSDMAX)       !OUT Calculated temperature (K)
     &,CONV_RAIN_OUT(GPOINTS,MM,MD,NSDMAX)  !OUT Calculated convective
C                                         !rainfall (mm/day)
     &,CONV_SNOW_OUT(GPOINTS,MM,MD,NSDMAX)  !OUT Calculated convective
C                                         !rainfall (mm/day)
     &,LS_RAIN_OUT(GPOINTS,MM,MD,NSDMAX) !OUT Calculated large scale
C                                         !rainfall (mm/day)
     &,LS_SNOW_OUT(GPOINTS,MM,MD,NSDMAX) !OUT Calculated large scale
C                                         !snowfall (mm/day)
     &,QHUM_OUT(GPOINTS,MM,MD,NSDMAX)    !OUT Calculated humidity (kg/kg
     &,WIND_OUT(GPOINTS,MM,MD,NSDMAX)    !OUT Calculated wind  (m/s)
     &,PSTAR_OUT(GPOINTS,MM,MD,NSDMAX)   !OUT Calculated pressure (Pa)
     &,SW_OUT(GPOINTS,MM,MD,NSDMAX)      !OUT Calculated shortwave radia
     &,LW_OUT(GPOINTS,MM,MD,NSDMAX)      !OUT Calculated longwave radiat
     &,DTEMP_OUT(GPOINTS,MM,MD)          !OUT Calculated daily temperature range
      INTEGER F_WET_CLIM_OUT(GPOINTS,MM)

      REAL
     & T_OUT_M(GPOINTS,MM,31,NSDMAX)       !OUT Calculated temperature for 365 day year - TP 13.07.15
     &,P_OUT_M(GPOINTS,MM,31,NSDMAX)       !OUT Calculated total precipitation for 365 day year - TP 13.07.15
     &,SW_OUT_M(GPOINTS,MM,31,NSDMAX)      !OUT Calculated shortwave radiation for 365 day year - TP 13.07.15
     &,DTEMP_OUT_M(GPOINTS,MM,31)          !OUT Calculated daily temperature range for 365 day year - TP 03.02.16

C Other variables
      REAL
     & CO2_PPMV          !WORK Atmospheric CO2 concentration (ppmv)
     &,CO2_LOCAL_PPMV    !WORK CO2 concentration after restart (ppmv)
     &,CO2_CHANGE_PPMV   !WORK Change in CO2 between restarts (ppmv)
     &,Q                 !WORK Total radiative forcing, both CO2 and NON CO2
     &,CH4_PPBV          !WORK Atmospheric CH4 concentration (ppbv)
     &,N2O_PPBV          !WORK Atmospheric N2O concentration (ppbv)

      REAL
     & MDI               !Missing data indicator
      PARAMETER(MDI=999.9)
      REAL DUMP          !Dump variable for data from file which is not needed - TP 13.07.15

      INTEGER
     & SEED_RAIN(4)                !WORK Seeding number for subdaily
                                   !rainfall.

      INTEGER
     & I,J,K,N,L                   !WORK General looping parameters
     &,II_CLIM                     !WORK Looping parameter to determine
C                                  !name of the climate data directory

      REAL LATMIN_CLIM,LATMAX_CLIM,LONGMIN_CLIM,LONGMAX_CLIM !Climatolog
      REAL LATMIN_AM,LATMAX_AM,LONGMIN_AM,LONGMAX_AM         !AM pattern
      REAL LATMIN_DAT,LATMAX_DAT,LONGMIN_DAT,LON  GMAX_DAT     !Anomaly pa

      DATA DRIVE_MONTH /'/jan','/feb','/mar','/apr','/may','/jun',
     &                  '/jul','/aug','/sep','/oct','/nov','/dec' /

      LOGICAL
     & RUNNOW_EXIST,    !WORK logical for existence of LPJ-GUESS input file - TP 29.07.15
     & RUNNOW_OPEN,     !WORK logical for whether LPJ-GUESS input file is open by another program - TP 29.07.15
     & RUNFLUX_EXIST,   !WORK logical for existence of LPJ-GUESS input file - TP 29.07.15
     & RUNFLUX_OPEN,    !WORK logical for whether LPJ-GUESS input file is open by another program - TP 29.07.15
     & RUNNONCO2FLUX_EXIST,   !WORK logical for existence of LPJ-GUESS input file - TP 29.07.15
     & RUNNONCO2FLUX_OPEN,    !WORK logical for whether LPJ-GUESS input file is open by another program - TP 29.07.15
     & DONE_EXIST,      !WORK logical for existence of LPJ-GUESS "done" marker file - TP 04.08.15
     & ERROR_EXIST,     !WORK logical for existence of LPJ-GUESS "error" marker file - TP 04.08.15
     & RUNNOW,          !WORK Exit logical for while loop - TP 29.07.15
     & KEEPRUNNING      !WORK Exit logical for while loop, provided by LPJ-GUESS - TP 29.07.15
      CHARACTER(LEN=10) SDATE,STIME !OUT Date and time for standard output - TP 29.07.15

      CHARACTER(LEN=4) THISYEAR !WORK string version of IYEAR for use in locating input/output files - TP 04.08.15
      CHARACTER(LEN=4) LASTYEAR !WORK string version of IYEAR-1 for use in locating input/output files - TP 04.08.15

      INTEGER NGPOINTS !Number of grid points in new gridlist used for nearest-neighbour regridding - TP 06.08.15
C [Step 3 of unified-codebase rebuild: NGPOINTS is now read from
C  imogen_settings.txt at run-time (was a hard-coded PARAMETER=3698).
C  This unblocks 62k+ cell gridlists without source recompile, per
C  Decision #2 of EXECUTION_PLAN.md. - DKB 2026-05-05]

      REAL, ALLOCATABLE :: T_OUT_M_REGRID(:,:,:,:)    !OUT Regridded calculated temperature for 365 day year - TP 06.08.15
      REAL, ALLOCATABLE :: P_OUT_M_REGRID(:,:,:,:)    !OUT Regridded calculated total precipitation for 365 day year - TP 06.08.15
      REAL, ALLOCATABLE :: SW_OUT_M_REGRID(:,:,:,:)   !OUT Regridded calculated shortwave radiation for 365 day year - TP 06.08.15
      REAL, ALLOCATABLE :: DTEMP_OUT_M_REGRID(:,:,:)  !OUT Regridded calculated daily temperature range for 365 day year - TP 03.02.16
      INTEGER, ALLOCATABLE :: F_WET_CLIM_REGRID(:,:)

      REAL, ALLOCATABLE :: LON_OUT(:)    !IN/OUT Longitude array to perform regridding to (read from file) - TP 06.08.15
      REAL, ALLOCATABLE :: LAT_OUT(:)    !IN/OUT Latitude array to perform regridding to (read from file) - TP 06.08.15

      LOGICAL REGRID        !IN If true use nearest-neighbour regridding - TP 06.08.15

      LOGICAL FIRSTCALL     !IN Is this the very first call to IMOGEN from LPJ-GUESS (start of spin-up)?

      INTEGER VARYEAR       !IN/OUT Year iterator for variability in base climatology - TP 02.02.16
      CHARACTER(LEN=4) VARYEAR_STR !WORK String version of VARYEAR - TP 02.02.16

C**************************************************************************
C Here set the parameters
C**************************************************************************

C Settings were previously hard-coded here.
C Now call the subroutine to read in the input settings file - TP 13.07.15
      CALL SETTIN(STEP_DAY,NYR_NON_CO2,NYR_EMISS,NYR_EMISS_NONCO2,
     & KAPPA_O,F_OCEAN,T_OCEAN_INIT,LAMBDA_L,LAMBDA_O,MU,Q2CO2,
     & CO2_INIT_PPMV,FILE_NON_CO2,C_EMISSIONS_IN,LPJG_CFLUX,
     & INCLUDE_CO2_IN, FILE_GRIDLIST,
     & INCLUDE_NON_CO2,DAILYOUT,LAND_FEED,OCEAN_FEED,ANLG,ANOM,DIR_PATT,
     & DIR_CLIM,FILE_SCEN_EMITS,FILE_NON_CO2_VALS,FILE_SCEN_CO2_PPMV,
     & FILE_LPJG_FLUX,NYR_LPJG_FLUX,DIR_COMMON,REGRID,
     & FILE_CH4_N2O_EMITS,CH4_INIT_PPBV,N2O_INIT_PPBV,TAU_DECAY_CH4,
     & TAU_DECAY_N2O,NONCO2_EMISSIONS,NONCO2_EMISSIONS_LPJG,FILE_LPJG_CH4_N2O_FLUX,
     & CO2_RF_FAIR,NGPOINTS) !NGPOINTS added in Step 3 of unified-codebase rebuild - DKB 2026-05-05

C [Step 3 of unified-codebase rebuild: ALLOCATE NGPOINTS-dimensioned
C  arrays now that NGPOINTS has been parsed from imogen_settings.txt.
C  This converts compile-time sizing to run-time sizing.]
      ALLOCATE(T_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX))
      ALLOCATE(P_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX))
      ALLOCATE(SW_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX))
      ALLOCATE(DTEMP_OUT_M_REGRID(NGPOINTS,MM,32))
      ALLOCATE(F_WET_CLIM_REGRID(NGPOINTS,MM))
      ALLOCATE(LON_OUT(NGPOINTS))
      ALLOCATE(LAT_OUT(NGPOINTS))
      PRINT *,'IMOGEN: ALLOCATEd regrid arrays for NGPOINTS=',NGPOINTS
      CALL FLUSH(6)

C**************************************************************************
C Now start the business
C**************************************************************************

      !Create a new CO2_all.dat file to keep CO2 data in for the whole run (for output purposes only) - TP 30.07.15
      OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/'//
     & 'CO2_all.dat',ACCESS='APPEND',STATUS='REPLACE')
      CLOSE(98) !Close CO2_all.dat file - TP 30.07.15

C [Step 7 of unified-codebase rebuild: bug F-4 fix — auto-create the
C  'done' handshake file in <DIR_COMMON>/LPJG_main/IMOGEN/ if it
C  doesn't exist. This eliminates the manual workaround required since
C  step 4 (where every standalone IMOGEN invocation needed a prior
C  "touch LPJG_main/IMOGEN/done") and is the Fortran twin of bugs C2/C3
C  fixed in lpjguess/modules/climatemodel.cpp at the same step.
C  In coupled mode, LPJ-GUESS controls this file's lifecycle yearly;
C  this auto-create only kicks in once on the very first invocation
C  when no prior handshake exists. - DKB 2026-05-06]
      CALL SYSTEM('mkdir -p '//TRIM(ADJUSTL(DIR_COMMON))//
     & '/LPJG_main/IMOGEN')
      CALL SYSTEM('touch '//TRIM(ADJUSTL(DIR_COMMON))//
     & '/LPJG_main/IMOGEN/done')

      !Loop around the whole program so that IMOGEN keeps running throughout the whole
      !LPJ-GUESS simulation . TP 29.07.15
      KEEPRUNNING=.TRUE.
      DO WHILE (KEEPRUNNING)

      !Look for input files provided by LPJ-GUESS, if those files are not available, wait - TP 29.07.15
      RUNNOW=.FALSE.
      RUNNOW_EXIST=.FALSE.
      RUNNOW_OPEN=.TRUE.
      RUNFLUX_EXIST=.FALSE.
      RUNFLUX_OPEN=.TRUE.
      RUNNONCO2FLUX_EXIST=.FALSE.
      RUNNONCO2FLUX_OPEN=.TRUE.
C [Step 7 fix: dead remnant '!DONE_EXIST=.TRUE.' deleted; the F-4
C  auto-create above now ensures DONE_EXIST=.TRUE. on the first
C  INQUIRE inside the polling loop below.]

      DO WHILE (RUNNOW.EQV..FALSE.)

        CALL SLEEP(3)
        WRITE(6,'(A1)',ADVANCE='NO') '.'
        CALL FLUSH(6);

        INQUIRE(FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     &  'done',EXIST=DONE_EXIST)

        INQUIRE(FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     &    'error',EXIST=ERROR_EXIST)

        INQUIRE(FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     &    'imogen_lpjg.txt',EXIST=RUNNOW_EXIST,OPENED=RUNNOW_OPEN)

        INQUIRE(FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     &    FILE_LPJG_FLUX,EXIST=RUNFLUX_EXIST,OPENED=RUNFLUX_OPEN)

        IF(NONCO2_EMISSIONS) THEN
          INQUIRE(FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     &      FILE_LPJG_CH4_N2O_FLUX,EXIST=RUNNONCO2FLUX_EXIST,OPENED=RUNNONCO2FLUX_OPEN)
        ENDIF
C        Print all the variable values to check them before the loop exits
        PRINT *, "RUNNOW_EXIST =", RUNNOW_EXIST
        PRINT *, "RUNNOW_OPEN =", RUNNOW_OPEN
        PRINT *, "RUNFLUX_EXIST =", RUNFLUX_EXIST
        PRINT *, "RUNFLUX_OPEN =", RUNFLUX_OPEN
        PRINT *, "DONE_EXIST =", DONE_EXIST
        PRINT *, "NONCO2_EMISSIONS =", NONCO2_EMISSIONS
        IF (NONCO2_EMISSIONS) THEN
            PRINT *, "RUNNONCO2FLUX_EXIST =", RUNNONCO2FLUX_EXIST
            PRINT *, "RUNNONCO2FLUX_OPEN =", RUNNONCO2FLUX_OPEN
        ENDIF
c        PAUSE

        IF ((RUNNOW_EXIST.AND.(RUNNOW_OPEN.EQV..FALSE.)) .AND.
     &    (RUNFLUX_EXIST.AND.(RUNFLUX_OPEN.EQV..FALSE.)) .AND. DONE_EXIST .AND.
     &    ((NONCO2_EMISSIONS.AND.RUNNONCO2FLUX_EXIST.AND.(RUNNONCO2FLUX_OPEN.EQV..FALSE.))
     &      .OR.(NONCO2_EMISSIONS.EQV..FALSE.))) THEN
          RUNNOW=.TRUE.
          !Some settings have to come from LPJ-GUESS
      
          CALL SETTIN_LPJG(DIR_COMMON,YEAR1,IYEND,SPINUP,YEAR1_LPJG,
     &      KEEPRUNNING,FIRSTCALL)
          CALL DATE_AND_TIME(SDATE,STIME)
          PRINT *,SDATE
          PRINT *,STIME
        ENDIF
        IF (ERROR_EXIST) THEN
          PRINT *,'Error in LPJ-GUESS'
          STOP
        ENDIF

      ENDDO

C Iterate a counter for the climate variability - TP 02.02.16
      IF(FIRSTCALL) THEN
        VARYEAR=0
      ELSE
        OPEN(97,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/VARYEAR.dat')
        READ(97,*) VARYEAR
        CLOSE(97)
      ENDIF

      IF(VARYEAR.EQ.30) THEN
        VARYEAR=1
      ELSE
        VARYEAR=VARYEAR+1
      ENDIF

      OPEN(97,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/VARYEAR.dat',STATUS='REPLACE')
      WRITE(97,*) VARYEAR
      CLOSE(97)
      PRINT *,'Variability iterator is ',VARYEAR
      WRITE(VARYEAR_STR,'(i4)') VARYEAR

C Do not allow the CO2 concentration to change if during the spin-up phase of LPJ-GUESS - TP 13.07.15
      IF(SPINUP) THEN
        INCLUDE_CO2=.FALSE.
        C_EMISSIONS=.FALSE.
        WRITE(THISYEAR,'(i4)') YEAR1
        PRINT *,'YEAR1 is ',YEAR1

C Make a new year folder for output - TP 04.08.15
        CALL SYSTEM('mkdir '//TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR)

        !Write a CO2.dat file with the spin-up CO2 concentration - TP 30.07.15
        IF(NONCO2_EMISSIONS) THEN
          OPEN(91,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//
     &     '/'//'CO2.dat')
          WRITE(91,*) THISYEAR,CO2_INIT_PPMV,0.0,0.0,0.0,0.0,CH4_INIT_PPBV,N2O_INIT_PPBV
          CLOSE(91)
        ELSE
          OPEN(91,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//
     &     '/'//'CO2.dat')
          WRITE(91,*) THISYEAR,CO2_INIT_PPMV,0.0,0.0,0.0,0.0
          CLOSE(91)
        ENDIF
      ELSE
        INCLUDE_CO2=INCLUDE_CO2_IN
        C_EMISSIONS=C_EMISSIONS_IN
      ENDIF

C Print to screen year
      DO IYEAR=YEAR1,IYEND
        PRINT *,'At year: ',IYEAR
        WRITE(THISYEAR,'(i4)') IYEAR
        WRITE(LASTYEAR,'(i4)') IYEAR-1

C Make a new year folder for output - TP 04.08.15
      CALL SYSTEM('mkdir '//TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR)

C NOTE - If LPJ requires a spin-up, then need to run with the below
C switched off. (i.e. so spins up at pre-industrial CO2 levels).
        !IF(IYEAR.EQ.YEAR1) THEN
        IF((IYEAR.EQ.YEAR1_LPJG).OR.SPINUP) THEN !TP 13.07.15

          CO2_PPMV = CO2_INIT_PPMV
          IF(INCLUDE_CO2) THEN
            CO2_CHANGE_PPMV=0.0
          ENDIF

          IF(NONCO2_EMISSIONS_LPJG) THEN
            CH4_PPBV = CH4_INIT_PPBV
            N2O_PPBV = N2O_INIT_PPBV
          ENDIF

          IF(ANLG) THEN
            DO I=1,N_OLEVS         !Set ocean temperature perturbation to
              DTEMP_O(I)=0.0
            ENDDO
            IF(INCLUDE_CO2.AND.OCEAN_FEED.AND.C_EMISSIONS) THEN
              DO I=1,NFARRAY
                FA_OCEAN(I)=0.0
              ENDDO
            ENDIF
          ENDIF

C Initiate seeding values for subdaily rainfall
          SEED_RAIN(1) = 9465
          SEED_RAIN(2) = 1484
          SEED_RAIN(3) = 3358
          SEED_RAIN(4) = 8350
        ENDIF

C If running for 1 year for coupling with LPJ-GUESS, then initialise
C DTEMP_O and FA_OCEAN from files - TP 13.07.15
        IF((IYEAR.GT.YEAR1_LPJG).AND.((IYEND-YEAR1).EQ.0)) THEN
          IF(OCEAN_FEED) THEN
            PRINT *,'Reading FA_OCEAN and DTEMP_O from file'
            OPEN(95,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//
     &        LASTYEAR//'/'//'fa_ocean.dat')
            OPEN(96,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//
     &        LASTYEAR//'/'//'dtemp_o.dat')
            DO I=1,NFARRAY
              READ(95,*) FA_OCEAN(I)
              !PRINT *,'FA_OCEAN is ',FA_OCEAN(I)
            ENDDO
            DO I=1,N_OLEVS
              READ(96,*) DTEMP_O(I)
              !PRINT *,'DTEMP_O is ',DTEMP_O(I)
            ENDDO
            CLOSE(95)
            CLOSE(96)
          ENDIF

          !Get the GHG values from the previous year from file
          OPEN(91,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//
     &     LASTYEAR//'/'//'CO2.dat')
          IF(NONCO2_EMISSIONS) THEN
            READ(91,*) YR_CO2_FILE,CO2_PPMV,DUMP,DUMP,DUMP,CO2_CHANGE_PPMV,CH4_PPBV,N2O_PPBV
          ELSE
            READ(91,*) YR_CO2_FILE,CO2_PPMV,DUMP,DUMP,DUMP,CO2_CHANGE_PPMV
          ENDIF
          CLOSE(91)
          PRINT *,YR_CO2_FILE,CO2_PPMV,CO2_CHANGE_PPMV,CH4_PPBV,N2O_PPBV
          IF ((YR_CO2_FILE+1).NE.IYEAR) THEN
            PRINT *,'ERROR: CO2 value from previous year not available'
            OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
            WRITE(98,*)'ERROR: CO2 value from previous year not available'
            CLOSE(98)
            STOP
          ENDIF
        ENDIF

C Capture CO2 concentration at beginning of year in variable "CO2_LOCAL_PPMV"
        IF(INCLUDE_CO2) THEN
          CO2_LOCAL_PPMV = CO2_PPMV
        ENDIF

C Now get the emissions/CO2 concentrations.
C At present only coded for reading in a file of emission/CO2 concentrat
C imogen projects of the future climate, with carbon cycle feedbacks) or
C in a file of CO2 concentrations for "Hydrology 20th Century" simulatio
        IF(C_EMISSIONS.AND.INCLUDE_CO2.AND.ANOM.AND.ANLG) THEN
          OPEN(62,FILE=FILE_SCEN_EMITS)
          DO N=1,NYR_EMISS
            READ(62,*) YR_EMISS(N),C_EMISS(N)
          ENDDO
          CLOSE(62)

          !Get non-CO2 GHG emissions as well if necessary
          IF(NONCO2_EMISSIONS) THEN
            OPEN(66,FILE=FILE_CH4_N2O_EMITS)
            DO N=1,NYR_EMISS_NONCO2
              READ(66,*) YR_EMISS_NONCO2(N),CH4_EMISS(N),N2O_EMISS(N)
            ENDDO
            CLOSE(66)
          ENDIF
        ENDIF

C Get land emissions/uptake from LPJ-GUESS - TP 13.07.15
        IF(C_EMISSIONS.AND.INCLUDE_CO2.AND.ANOM.AND.ANLG.AND.
     &   LAND_FEED.AND.LPJG_CFLUX) THEN
          OPEN(63,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     &      FILE_LPJG_FLUX)
          DO N=1,NYR_LPJG_FLUX
            READ(63,*) YR_LPJG(N),C_LPJG(N)
            PRINT *,'C flux from LPJG is ',C_LPJG(N),
     &       ' for year ',YR_LPJG(N)
          ENDDO
          !CLOSE(63,STATUS='DELETE')
          CLOSE(63)

          !Get non-CO2 GHG emissions as well if necessary
          IF(NONCO2_EMISSIONS_LPJG) THEN
            OPEN(64,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     &        FILE_LPJG_CH4_N2O_FLUX)
            DO N=1,NYR_LPJG_FLUX
              PRINT *,'Reading CH4 and N2O fluxes from LPJ-GUESS - ensure FILE_CH4_N2O_EMITS only contains anthropogenic emissions'
              READ(64,*) YR_LPJG_NONCO2(N),CH4_LPJG(N),N2O_LPJG(N)
              PRINT *,'CH4 flux from LPJG is ',CH4_LPJG(N),
     &         ' for year ',YR_LPJG_NONCO2(N)
              PRINT *,'N2O flux from LPJG is ',N2O_LPJG(N),
     &         ' for year ',YR_LPJG_NONCO2(N)
            ENDDO
            !CLOSE(64,STATUS='DELETE')
            CLOSE(64)
          ENDIF

          !Remove the "done" marker file
          OPEN(65,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//'done')
          CLOSE(65,STATUS='DELETE')
        ENDIF

C Hydrology 20th Century simulations (note also check for this run in
C subroutine IMOGEN_CONFIRMED_RUN which includes more stringent checks)
C OR analogue model simulations with CO2 prescribed.

        IF((.NOT.C_EMISSIONS).AND.INCLUDE_CO2) THEN
C This works by reading in a file of CO2 concentrations, and checks that
C year is represented.
          OPEN(60,FILE=FILE_SCEN_CO2_PPMV)
          TALLY_CO2_FILE=0
          DO WHILE (.TRUE.)
            READ(60,END=173,FMT=*) YR_CO2_FILE,CO2_FILE_PPMV
            IF(YR_CO2_FILE.EQ.IYEAR) THEN
              CO2_PPMV=CO2_FILE_PPMV
              TALLY_CO2_FILE=TALLY_CO2_FILE+1
            ENDIF
          ENDDO
 173      CONTINUE
          CLOSE(60)
C Check that value has been found.
          IF(TALLY_CO2_FILE.NE.1) THEN
            PRINT *,'CO2 value not found in file'
            OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
            WRITE(98,*)'CO2 value not found in file'
            CLOSE(98)
            STOP
          ENDIF

        !TODO: CONSIDER ADDING IN THE CONCENTRATION READING FOR CH4 AND N2O HERE!!

        ENDIF

C Now read in climatology and any anomalies/derived anomalies from AM.
C Start with climatology.
        DO I=1,LEN(DIR_CLIM)
          IF(DIR_CLIM(I:I).NE.' ') II_CLIM=I
        ENDDO

        DO J=1,MM
          FILE_CLIM=DIR_CLIM(:II_CLIM)//DRIVE_MONTH(J)//TRIM(ADJUSTL(VARYEAR_STR))
          OPEN(49,FILE=FILE_CLIM,STATUS='OLD')
          READ(49,*) LONGMIN_CLIM,LATMIN_CLIM,LONGMAX_CLIM,LATMAX_CLIM
            DO L=1,GPOINTS
          READ(49,*)LONG(L),LAT(L),T_CLIM(L,J),RH15M_CLIM(L,J),
     &              UWIND_CLIM(L,J),VWIND_CLIM(L,J),LW_CLIM(L,J),
     &              SW_CLIM(L,J),DTEMP_CLIM(L,J),RAINFALL_CLIM(L,J),
     &              SNOWFALL_CLIM(L,J),PSTAR_HA_CLIM(L,J),
     &              F_WET_CLIM(L,J)
          ENDDO
          CLOSE(49)
        ENDDO


C Now calculate the added monthly anomalies, either from analogue model
C or prescribed directly.
        IF(ANOM) THEN
          IF(ANLG) THEN
C This call is to the GCM analogue model. It is prescribed CO2
C concentration, and calculates non-CO2, and returns total change in
C radiative forcing, Q. Recall that the AM has a "memory" through
C DTEMP_0 - ie the ocean temperatures. Note that in this version of the
C code, the AM is updated yearly.

C Calculate the CO2 forcing
            IF(INCLUDE_CO2) THEN
              CALL RADF_CO2(CO2_PPMV,CO2_INIT_PPMV,Q2CO2,Q_CO2)
            ENDIF
C Calculate the non CO2 forcing
            IF(INCLUDE_NON_CO2) THEN
              CALL RADF_NON_CO2(IYEAR,Q_NON_CO2,NYR_NON_CO2,
     &                    FILE_NON_CO2,FILE_NON_CO2_VALS)
              IF(NONCO2_EMISSIONS) THEN
                PRINT *,'Including CH4 and N2O emissions directly - ensure FILE_NON_CO2 does not include them'
                CALL FAIR_NON_CO2_GHG(CH4_PPBV,N2O_PPBV,CH4_INIT_PPBV,N2O_INIT_PPBV,CO2_PPMV,
     &            CO2_INIT_PPMV,Q_CH4,Q_N2O,Q_CO2_FAIR)
                IF(CO2_RF_FAIR) THEN
                  Q_CO2=Q_CO2_FAIR
                ENDIF
              ENDIF
            ENDIF
C Calculate the total forcing
            IF(NONCO2_EMISSIONS) THEN
              !PRINT *, 'Q_CO2 is: ', Q_CO2
              !PAUSE
              Q=Q_CO2+Q_NON_CO2+Q_CH4+Q_N2O
            ELSE
              Q=Q_CO2+Q_NON_CO2
            ENDIF

C Now write the radiative forcing to an output file
            OPEN(99,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/'//'RF_all.dat',ACCESS='APPEND')
            IF(ANLG.AND.ANOM) THEN
              IF(NONCO2_EMISSIONS) THEN
                WRITE(99,*) IYEAR,Q,Q_CO2,Q_NON_CO2,Q_CH4,Q_N2O
              ELSE
                WRITE(99,*) IYEAR,Q,Q_CO2,Q_NON_CO2
              ENDIF
            ENDIF
            CLOSE(99)

C Call the GCM analogue model that responds to this forcing
            IF(INCLUDE_CO2.OR.INCLUDE_NON_CO2) THEN
              CALL GCM_ANLG(Q,GPOINTS,T_ANOM,PRECIP_ANOM,
     &        RH15M_ANOM,UWIND_ANOM,VWIND_ANOM,DTEMP_ANOM,
     &        PSTAR_HA_ANOM,SW_ANOM,LW_ANOM,
     &        N_OLEVS,DIR_PATT,F_OCEAN,KAPPA_O,LAMBDA_L,LAMBDA_O,MU,
     &        DTEMP_O,LONGMIN_AM,LATMIN_AM,
     &        LONGMAX_AM,LATMAX_AM,MM)

C Check driving files are compatible.
              !PRINT *, 'LONGMIN_CLIM = ', LONGMIN_CLIM
              !PRINT *, 'LATMIN_CLIM = ', LATMIN_CLIM
              !PRINT *, 'LONGMAX_CLIM = ', LONGMAX_CLIM
              !PRINT *, 'LATMAX_CLIM = ', LATMAX_CLIM
              !PRINT *, 'LONGMIN_AM = ', LONGMIN_AM
              !PRINT *, 'LATMIN_AM = ', LATMIN_AM
              !PRINT *, 'LONGMAX_AM = ', LONGMAX_AM
              !PRINT *, 'LATMAX_AM = ', LATMAX_AM
              !PAUSE

              IF((ABS(LONGMIN_CLIM-LONGMIN_AM).GE.1.0E-6).OR.
     &        (ABS(LATMIN_CLIM-LATMIN_AM).GE.1.0E-6).OR.
     &        (ABS(LONGMAX_CLIM-LONGMAX_AM).GE.1.0E-6).OR.
     &        (ABS(LATMAX_CLIM-LATMAX_AM).GE.1.0E-6)) THEN
                PRINT *,'Driving files are incompatible'
                OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
                WRITE(98,*)'Driving files are incompatible'
                CLOSE(98)
                STOP
              ENDIF
            ENDIF

          ENDIF
        ENDIF         !End of where anomalies are calculated

C Now incorporate anomalies with climate data.
C At this point, have climatology, WG if called and anomalies of either
C "_AM" or "_DAT". Now calculate the daily values of the driving data.
C This is calculated using subroutine CLIM_CALC

        CALL CLIM_CALC(ANOM,ANLG,GPOINTS,MM,MD,T_CLIM,SW_CLIM,
     &           LW_CLIM,PSTAR_HA_CLIM,RH15M_CLIM,RAINFALL_CLIM,
     &           SNOWFALL_CLIM,UWIND_CLIM,VWIND_CLIM,DTEMP_CLIM,
     &           F_WET_CLIM,
     &           T_ANOM,SW_ANOM,LW_ANOM,PSTAR_HA_ANOM,
     &           RH15M_ANOM,PRECIP_ANOM,UWIND_ANOM,
     &           VWIND_ANOM,DTEMP_ANOM,
     &           SW_OUT,T_OUT,LW_OUT,CONV_RAIN_OUT,CONV_SNOW_OUT,
     &           LS_RAIN_OUT,LS_SNOW_OUT,PSTAR_OUT,WIND_OUT,QHUM_OUT,
     &           DTEMP_OUT,NSDMAX,STEP_DAY,SEED_RAIN,SEC_DAY,LAT,LONG,MDI)

C Now do the carbon cycling update.
        IF(INCLUDE_CO2.AND.C_EMISSIONS.AND.ANOM.AND.ANLG) THEN
C Include anthropogenic carbon emissions.
          EMISS_TALLY=0
          DO N = 1,NYR_EMISS
            IF(YR_EMISS(N).EQ.IYEAR-1) THEN !TODO: SHOULD THIS BE IYEAR-1 RATHER THAN IYEAR??? - TP 30.07.15
              C_EMISS_LOCAL=C_EMISS(N)
              CO2_PPMV = CO2_PPMV + CONV*C_EMISS_LOCAL
              EMISS_TALLY=EMISS_TALLY+1
            ENDIF
          ENDDO

          IF(EMISS_TALLY.NE.1) THEN
            PRINT *,'Emission dataset does not match run'
            OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
            WRITE(98,*)'Emission dataset does not match run'
            CLOSE(98)
            STOP
          ENDIF

C Include the land carbon cycle feedback - TP 13.07.15
          IF(LAND_FEED.AND.LPJG_CFLUX) THEN
C Here, take the land C flux from LPJ-GUESS - TP 13.07.15
            EMISS_TALLY=0
            !DO N = 1,NYR_EMISS !TODO, SHOULD THIS BE NYR_LPJG_FLUX??
            DO N = 1,NYR_LPJG_FLUX !TODO, SHOULD THIS BE NYR_LPJG_FLUX??
              IF(YR_LPJG(N).EQ.IYEAR-1) THEN !TODO: SHOULD THIS BE IYEAR-1 RATHER THAN IYEAR??? - TP 30.07.15
                C_LPJG_LOCAL=C_LPJG(N)
                D_LAND_ATMOS=CONV*C_LPJG_LOCAL
                CO2_PPMV = CO2_PPMV + D_LAND_ATMOS
                EMISS_TALLY=EMISS_TALLY+1
              ENDIF
            ENDDO

            IF(EMISS_TALLY.NE.1) THEN
              PRINT *,'LPJG C flux dataset does not match run.'
              PRINT *,'EMISS_TALLY is ',EMISS_TALLY
              OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
              WRITE(98,*)'LPJG C flux dataset does not match run.'
              CLOSE(98)
              STOP
            ENDIF

            !Update non-GHG concentrations if necessary
            IF(NONCO2_EMISSIONS) THEN
            PRINT *,'YR_LPJG_NONCO2(1) is ',YR_LPJG_NONCO2(1)
              CALL FAIR_NON_CO2_GHG_BUDGET(IYEAR,NONCO2_EMISSIONS_LPJG,YR_LPJG_NONCO2,NYR_LPJG_FLUX,CH4_LPJG,N2O_LPJG,
     &          YR_EMISS,NYR_EMISS_NONCO2,CH4_EMISS,N2O_EMISS,CH4_PPBV,N2O_PPBV,TAU_DECAY_CH4,TAU_DECAY_N2O,DIR_COMMON,THISYEAR)
            ENDIF

          ELSEIF(LAND_FEED) THEN
C Here, temporarily made to be 25% of emissions for all times.
            PRINT *,'WARNING: Land C uptake defaulting to 25% of emissions'
            D_LAND_ATMOS=-CONV*0.25*C_EMISS_LOCAL
            CO2_PPMV = CO2_PPMV + D_LAND_ATMOS
          ENDIF

          IF(OCEAN_FEED) THEN
C Update with ocean feedbacks if required
            DT_OCEAN = DTEMP_O(1)
            CALL OCEAN_CO2
     &      (IYEAR-YEAR1_LPJG+1,1,CO2_PPMV,CO2_INIT_PPMV,DT_OCEAN, !YEAR1_LPJG instead of YEAR1 at both points in this call for FA_OCEAN bugfix - TP 07.02.18
     &       FA_OCEAN,OCEAN_AREA,
     &       CO2_CHANGE_PPMV,IYEND-YEAR1_LPJG+1,T_OCEAN_INIT,NFARRAY, !Added +1 to IYEND-YEAR1 to avoid loop in RESPONSE never being entered when running for 1 year. Results appear identical - TP 14.07.15
     &       D_OCEAN_ATMOS)
              CO2_PPMV = CO2_PPMV+D_OCEAN_ATMOS
          ENDIF
        ENDIF

        PRINT *, 'CO2 CHANGE PPV = ', CO2_CHANGE_PPMV
        IF(INCLUDE_CO2) CO2_CHANGE_PPMV=CO2_PPMV-CO2_LOCAL_PPMV

C Write out to a global here the different large scale CO2 fluxes if
C IMOGEN operated interactively.
        PRINT *,'INCLUDE_CO2 ',INCLUDE_CO2
        PRINT *,'C_EMISSIONS ',C_EMISSIONS
        IF(SPINUP.EQV..FALSE.) THEN
        !If in the spin-up period then writing to CO2.dat is carried out earlier on in the program
C [Step 17b (F-N B10 - symmetric Fortran engine writer fix) of
C  unified-codebase rebuild (2026-05-11): UNCONDITIONAL OPEN per IYEAR
C  iteration for the CO2.dat + CO2_all.dat writers (units 91, 98).
C  Symmetric with the C++ in-process port fix at commit 7be595a
C  (lpjguess/modules/climatemodel.cpp ~line 787). Same root cause +
C  same fix as the climate-anomalies block at line ~954 below
C  (canonical doc). Without this fix, the IYEND iteration of each
C  engine call silently dropped its CO2.dat write because units 91/98
C  were never opened on that iteration. unit 98 (CO2_all.dat
C  aggregator; ACCESS='APPEND') similarly: each iteration appends
C  iyear's entry exactly once. - DKB 2026-05-11]
          OPEN(91,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'CO2.dat') !Send to DIR_COMMON - TP 13.07.15
          OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/'//'CO2_all.dat',ACCESS='APPEND')

          IF(INCLUDE_CO2.AND.C_EMISSIONS.AND.ANLG.AND.ANOM.AND.
     &     OCEAN_FEED.AND.LAND_FEED) THEN
            IF(NONCO2_EMISSIONS) THEN
              WRITE(91,*) IYEAR,CO2_PPMV,CONV*C_EMISS_LOCAL,D_LAND_ATMOS,
     &              D_OCEAN_ATMOS,CO2_CHANGE_PPMV,CH4_PPBV,N2O_PPBV
              WRITE(98,*) IYEAR,CO2_PPMV,CONV*C_EMISS_LOCAL,D_LAND_ATMOS,
     &              D_OCEAN_ATMOS,CO2_CHANGE_PPMV,CH4_PPBV,N2O_PPBV
            ELSE
              WRITE(91,*) IYEAR,CO2_PPMV,CONV*C_EMISS_LOCAL,D_LAND_ATMOS,
     &              D_OCEAN_ATMOS,CO2_CHANGE_PPMV
              WRITE(98,*) IYEAR,CO2_PPMV,CONV*C_EMISS_LOCAL,D_LAND_ATMOS,
     &              D_OCEAN_ATMOS,CO2_CHANGE_PPMV
            ENDIF
          ELSE
            IF(NONCO2_EMISSIONS) THEN
              WRITE(91,*) IYEAR,CO2_PPMV,0.0,0.0,0.0,0.0,CH4_PPBV,N2O_PPBV
              WRITE(98,*) IYEAR,CO2_PPMV,0.0,0.0,0.0,0.0,CH4_PPBV,N2O_PPBV
            ELSE
              WRITE(91,*) IYEAR,CO2_PPMV,0.0,0.0,0.0,0.0
              WRITE(98,*) IYEAR,CO2_PPMV,0.0,0.0,0.0,0.0
            ENDIF
          ENDIF
        ENDIF

C [Step 17b (F-N B10 - symmetric Fortran engine writer fix) of
C  unified-codebase rebuild (2026-05-11): UNCONDITIONAL CLOSE per IYEAR
C  iteration for the CO2.dat + CO2_all.dat units 91, 98. Symmetric with
C  OPEN block at line ~854 above; closes the per-iteration writes
C  cleanly so the units are reusable on the next IYEAR iteration.
C  Symmetric with the C++ in-process port (which uses std::ofstream
C  RAII so an explicit close is implicit; Fortran requires explicit
C  CLOSE statements). - DKB 2026-05-11]
        CLOSE(91)
        CLOSE(98)

C Write out the climate anomalies here - TP 13.07.15

        IF(ANLG.AND.ANOM.AND.(STEP_DAY.EQ.1).AND.(MM.EQ.12).AND.
     &   (MD.EQ.30)) THEN
          !Only make outputs for specific combinations of MM, MD and STEP_DAY

          !Transfer the output variables to a 365 day year
          !by extending/shortening the respective months - TP 13.07.15
          DO IGP=1,GPOINTS
            DO IMM=1,MM !Months per year
              DO IMD=1,31 !Days per month

                IF(IMD.LE.MTHDAY(IMM)) THEN
                  DO IND=1,STEP_DAY
                    IF(IMD.LE.30) THEN
                      T_OUT_M(IGP,IMM,IMD,IND)=T_OUT(IGP,IMM,IMD,IND)
                      SW_OUT_M(IGP,IMM,IMD,IND)=SW_OUT(IGP,IMM,IMD,IND)
                      P_OUT_M(IGP,IMM,IMD,IND)=
     &                 LS_RAIN_OUT(IGP,IMM,IMD,IND)+
     &                 CONV_RAIN_OUT(IGP,IMM,IMD,IND)+
     &                 LS_SNOW_OUT(IGP,IMM,IMD,IND)+
     &                 CONV_SNOW_OUT(IGP,IMM,IMD,IND)
                    ELSE
                      T_OUT_M(IGP,IMM,IMD,IND)=T_OUT(IGP,IMM,IMD-1,IND)
                      SW_OUT_M(IGP,IMM,IMD,IND)=
     &                 SW_OUT(IGP,IMM,IMD-1,IND)
                      P_OUT_M(IGP,IMM,IMD,IND)=
     &                 LS_RAIN_OUT(IGP,IMM,IMD-1,IND)+
     &                 CONV_RAIN_OUT(IGP,IMM,IMD-1,IND)+
     &                 LS_SNOW_OUT(IGP,IMM,IMD-1,IND)+
     &                 CONV_SNOW_OUT(IGP,IMM,IMD-1,IND)
                    ENDIF
                  ENDDO
C                 Also want the DTEMP output, but this cannot be sub-daily - TP 03.02.16
                  IF(IMD.LE.30) THEN
                    DTEMP_OUT_M(IGP,IMM,IMD)=DTEMP_OUT(IGP,IMM,IMD)
                  ELSE
                    DTEMP_OUT_M(IGP,IMM,IMD)=DTEMP_OUT(IGP,IMM,IMD-1)
                  ENDIF
                ELSE
                  DO IND=1,STEP_DAY
                    T_OUT_M(IGP,IMM,IMD,IND)=MDI
                    P_OUT_M(IGP,IMM,IMD,IND)=MDI
                    SW_OUT_M(IGP,IMM,IMD,IND)=MDI
                  ENDDO
                  DTEMP_OUT_M(IGP,IMM,IMD)=MDI
                  CONTINUE
                ENDIF

              ENDDO
C             Also want the number of wet days per month as an output
              F_WET_CLIM_OUT(IGP,IMM)=INT(F_WET_CLIM(IGP,IMM)*MTHDAY(IMM))
              IF((F_WET_CLIM_OUT(IGP,IMM).EQ.0).AND.
     &         (RAINFALL_CLIM(IGP,IMM)+SNOWFALL_CLIM(IGP,IMM)+PRECIP_ANOM(IGP,IMM).GE.0.0005)) THEN
                F_WET_CLIM_OUT(IGP,IMM)=1
              ENDIF
            ENDDO
          ENDDO

          IF (REGRID) THEN
            !Regrid the output data using nearest-neighbour interpolation - TP 06.08.15
            CALL REGRID_CLIM(T_OUT_M,SW_OUT_M,P_OUT_M,DTEMP_OUT_M,F_WET_CLIM_OUT,MM,NSDMAX,GPOINTS,LONG,LAT
     &       ,T_OUT_M_REGRID,P_OUT_M_REGRID,SW_OUT_M_REGRID,DTEMP_OUT_M_REGRID,F_WET_CLIM_REGRID,NGPOINTS
     &       ,LON_OUT,LAT_OUT,DIR_COMMON,THISYEAR,FILE_GRIDLIST)

            PRINT *,'Writing regridded anomalies for year: ',IYEAR
C [Step 17b (F-N B10 - symmetric Fortran engine writer fix) of
C  unified-codebase rebuild (2026-05-11): UNCONDITIONAL OPEN per IYEAR
C  iteration for the regridded climate-anomaly writers (T/P/SW/WET/DTEMP).
C  CANONICAL DOC FOR ALL 7 B10 REMOVALS IN THIS FILE.
C
C  ROOT-CAUSE FIX: the previous IF(IYEAR.EQ.YEAR1) gate caused IYEND
C  iterations (year > YEAR1 in 2-year-window engine calls) to silently
C  skip the file open + writes. Combined with the persistent YEAR1++/
C  IYEND++ global increment per IYEAR iteration (advancing each call
C  by one year), each engine call effectively wrote climate data for
C  ONE year only (the call's YEAR1) while leaving the IYEND year as
C  an empty placeholder (just a 'done' marker, no climate). Net effect
C  across calls: ALTERNATING-YEAR staged climate (only ODD years 1871,
C  1873, ... fully populated; EVEN years 1872, 1874, ... empty).
C
C  This bug exists SYMMETRICALLY in two engines:
C    - lpjguess/modules/climatemodel.cpp::RUN_IMOGEN_ENGINE() (in-process
C      C++ port; FIXED at commit 7be595a, 2026-05-10, 5 conditional
C      removals at lines ~787, ~884, ~963, ~988, ~998); used by
C      imogencfx mode in v1.0.
C    - imogen/code/imogen_lpjg.f (standalone Fortran engine; THIS FIX,
C      7 conditional removals = 5 C++ analogues + 2 Fortran-specific
C      extras: explicit CO2.dat CLOSE at line ~883 (C++ uses RAII), and
C      a non-REGRID climate-anomaly OPEN/CLOSE pair at lines ~1013/
C      ~1071 absent in the C++ port which lacks the REGRID/native-grid
C      branch); used by imogen mode in v1.0 (canonical IMOGEN engine
C      for v1.0 per EXECUTION_PLAN.md Decision #2).
C
C  FIX: open ALL output files unconditionally per IYEAR iteration.
C  THISYEAR is already updated per iteration (WRITE(THISYEAR,...) at
C  line ~833), so each iteration's open targets that iteration's
C  correct year-folder. Symmetric removals applied at:
C    - line ~854 (CO2 writer OPEN; was gated IYEAR.EQ.YEAR1)
C    - line ~883 (CO2 writer CLOSE; was gated IYEAR.EQ.IYEND)
C    - line ~1013 (non-REGRID climate-anomaly OPEN; was gated YEAR1)
C    - line ~1071 (climate-anomaly CLOSE for both REGRID branches;
C                  was gated IYEAR.EQ.IYEND)
C    - line ~1088 (FA_OCEAN/DTEMP_O OPEN; was gated IYEAR.EQ.YEAR1)
C    - line ~1099 (FA_OCEAN/DTEMP_O CLOSE; was gated IYEAR.EQ.IYEND)
C
C  PRIMARY USE OF FORTRAN ENGINE: engine-only smoke testing + imogen
C  mode (canonical engine for v1.0). C1.2/C1.3 PASSes verified at
C  commit 7be595a were on the C++ port; this Fortran fix is for
C  symmetric correctness so the engines stay in lock-step (per F-3
C  Fortran<->C++ IMOGEN parity in notes/FOLLOWUPS.md).
C
C  Backport-relevant per F-11 + BACKPORT_LEDGER (Fortran source change
C  in imogen/code/; if trunk_r13078 has this engine file, apply the
C  same 7 removals mechanically).
C  - DKB 2026-05-11]
            OPEN(92,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'T_anom.dat',STATUS='REPLACE')
            OPEN(93,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'P_anom.dat',STATUS='REPLACE')
            OPEN(94,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'SW_anom.dat',STATUS='REPLACE')
            OPEN(95,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'WET.dat',STATUS='REPLACE')
            OPEN(11,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'DTEMP_anom.dat',STATUS='REPLACE')
C [Step 17b (F-N B2): NEW Tmin_anom.dat + Tmax_anom.dat writers in
C  Fortran engine, added symmetrically to BOTH REGRID + non-REGRID
C  branches. Algebraic derivation: Tmin = T - DTEMP/2; Tmax = T +
C  DTEMP/2 (same units as T = Kelvin; same dynamic range as T_anom);
C  per Decision #11 (steps 8-9.5 era; Tmin/Tmax derived rather than
C  directly modelled). Symmetric with C++ in-process port at
C  lpjguess/modules/climatemodel.cpp ~lines 952-953 (file100/file101
C  ofstream; non-REGRID branch only; REGRID-branch C++ addition is
C  B3's scope per the `// TODO at step 9.5b` comment in C++ source
C  ~line 894). Units 100/101 chosen to mirror the C++ ofstream
C  variable names (file100, file101); verified unused elsewhere in
C  this file (only units 1-99 + standard streams in use; unit 99 is
C  RF_all.dat at line 715). Format `(f10.3)` matches T_anom for
C  byte-level dimensional parity with the C++ port. Forensic +
C  design rationale: notes/STEP_17b.md §3d. Backport-RELEVANT
C  (Fortran source change in standalone engine; symmetric with the
C  in-process C++ port). - DKB 2026-05-12]
            OPEN(100,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'Tmin_anom.dat',STATUS='REPLACE')
            OPEN(101,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'Tmax_anom.dat',STATUS='REPLACE')

            DO IGP=1,NGPOINTS
              WRITE(92,'(f8.3)',ADVANCE='NO') LON_OUT(IGP) !Advance one line in the output file
              WRITE(92,'(f8.3)',ADVANCE='NO') LAT_OUT(IGP) !Advance one line in the output file
              WRITE(93,'(f8.3)',ADVANCE='NO') LON_OUT(IGP) !Advance one line in the output file
              WRITE(93,'(f8.3)',ADVANCE='NO') LAT_OUT(IGP) !Advance one line in the output file
              WRITE(94,'(f8.3)',ADVANCE='NO') LON_OUT(IGP) !Advance one line in the output file
              WRITE(94,'(f8.3)',ADVANCE='NO') LAT_OUT(IGP) !Advance one line in the output file
              WRITE(95,'(f8.3)',ADVANCE='NO') LON_OUT(IGP) !Advance one line in the output file
              WRITE(95,'(f8.3)',ADVANCE='NO') LAT_OUT(IGP) !Advance one line in the output file
              WRITE(11,'(f8.3)',ADVANCE='NO') LON_OUT(IGP) !Advance one line in the output file
              WRITE(11,'(f8.3)',ADVANCE='NO') LAT_OUT(IGP) !Advance one line in the output file
C [B2: Tmin_anom (unit 100) + Tmax_anom (unit 101) per-cell LON/LAT
C  headers; same format as T_anom. - DKB 2026-05-12]
              WRITE(100,'(f8.3)',ADVANCE='NO') LON_OUT(IGP) !B2 Tmin
              WRITE(100,'(f8.3)',ADVANCE='NO') LAT_OUT(IGP) !B2 Tmin
              WRITE(101,'(f8.3)',ADVANCE='NO') LON_OUT(IGP) !B2 Tmax
              WRITE(101,'(f8.3)',ADVANCE='NO') LAT_OUT(IGP) !B2 Tmax
              DO IMM=1,MM
                IF(DAILYOUT) THEN
                  DO IMD=1,31
                    DO IND=1,STEP_DAY
                      IF(IMD.LE.MTHDAY(IMM)) THEN
                        WRITE(92,'(f10.3)',ADVANCE='NO')
     &                   T_OUT_M_REGRID(IGP,IMM,IMD,IND)
                        WRITE(93,'(f10.3)',ADVANCE='NO')
     &                   P_OUT_M_REGRID(IGP,IMM,IMD,IND)
                        WRITE(94,'(f10.3)',ADVANCE='NO')
     &                   SW_OUT_M_REGRID(IGP,IMM,IMD,IND)
                        WRITE(11,'(f10.3)',ADVANCE='NO')
     &                   DTEMP_OUT_M_REGRID(IGP,IMM,IMD)
                        WRITE(95,'(i10)',ADVANCE='NO')
     &                   F_WET_CLIM_REGRID(IGP,IMM)
C [B2: Tmin = T - DTEMP/2; Tmax = T + DTEMP/2; same units as T (K).
C  REGRID DAILYOUT=TRUE branch. - DKB 2026-05-12]
                        WRITE(100,'(f10.3)',ADVANCE='NO')
     &                   T_OUT_M_REGRID(IGP,IMM,IMD,IND)
     &                  -DTEMP_OUT_M_REGRID(IGP,IMM,IMD)/2.0
                        WRITE(101,'(f10.3)',ADVANCE='NO')
     &                   T_OUT_M_REGRID(IGP,IMM,IMD,IND)
     &                  +DTEMP_OUT_M_REGRID(IGP,IMM,IMD)/2.0
                      ENDIF
                    ENDDO
                  ENDDO
                ELSE
                  WRITE(92,'(f10.3)',ADVANCE='NO')
     &              T_OUT_M_REGRID(IGP,IMM,1,1)
                  WRITE(93,'(f10.3)',ADVANCE='NO')
     &              P_OUT_M_REGRID(IGP,IMM,1,1)
                  WRITE(94,'(f10.3)',ADVANCE='NO')
     &              SW_OUT_M_REGRID(IGP,IMM,1,1)
                  WRITE(11,'(f10.3)',ADVANCE='NO')
     &              DTEMP_OUT_M_REGRID(IGP,IMM,1)
                  WRITE(95,'(i10)',ADVANCE='NO')
     &              F_WET_CLIM_REGRID(IGP,IMM)
C [B2: Tmin = T - DTEMP/2; Tmax = T + DTEMP/2; same units as T (K).
C  REGRID DAILYOUT=FALSE branch (monthly mean). - DKB 2026-05-12]
                  WRITE(100,'(f10.3)',ADVANCE='NO')
     &              T_OUT_M_REGRID(IGP,IMM,1,1)
     &             -DTEMP_OUT_M_REGRID(IGP,IMM,1)/2.0
                  WRITE(101,'(f10.3)',ADVANCE='NO')
     &              T_OUT_M_REGRID(IGP,IMM,1,1)
     &             +DTEMP_OUT_M_REGRID(IGP,IMM,1)/2.0
                ENDIF
              ENDDO
              WRITE(92,'()') !Advance one line in the output file
              WRITE(93,'()') !Advance one line in the output file
              WRITE(94,'()') !Advance one line in the output file
              WRITE(95,'()') !Advance one line in the output file
              WRITE(11,'()') !Advance one line in the output file
C [B2: per-cell newlines for Tmin_anom (unit 100) + Tmax_anom (unit
C  101). REGRID branch. - DKB 2026-05-12]
              WRITE(100,'()') !B2 Tmin
              WRITE(101,'()') !B2 Tmax
            ENDDO
          ELSE
            !Output in the native IMOGEN grid - TP 06.08.15
            PRINT *,'Writing native-grid anomalies for year: ',IYEAR
C [Step 17b (F-N B10): UNCONDITIONAL OPEN per IYEAR iteration for the
C  native-grid (non-REGRID) climate-anomaly writers. Same root cause +
C  same fix as the REGRID OPEN block at line ~954 (canonical doc).
C  This branch (non-REGRID) has NO C++ analogue: the C++ in-process
C  port (climatemodel.cpp) writes on a single grid throughout, so this
C  is one of the 2 Fortran-specific extras vs the C++ fix's 5
C  removals. - DKB 2026-05-11]
            OPEN(92,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'T_anom.dat',STATUS='REPLACE')
            OPEN(93,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'P_anom.dat',STATUS='REPLACE')
            OPEN(94,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'SW_anom.dat',STATUS='REPLACE')
            OPEN(95,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'WET.dat',STATUS='REPLACE')
            OPEN(11,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'DTEMP_anom.dat',STATUS='REPLACE')
C [B2: NEW Tmin_anom + Tmax_anom OPENs in non-REGRID branch.
C  Symmetric with REGRID OPEN block at line ~1023 (canonical doc).
C  - DKB 2026-05-12]
            OPEN(100,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'Tmin_anom.dat',STATUS='REPLACE')
            OPEN(101,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'Tmax_anom.dat',STATUS='REPLACE')

            DO IGP=1,GPOINTS
              WRITE(92,'(f8.3)',ADVANCE='NO') LONG(IGP) !Advance one line in the output file
              WRITE(92,'(f8.3)',ADVANCE='NO') LAT(IGP) !Advance one line in the output file
              WRITE(93,'(f8.3)',ADVANCE='NO') LONG(IGP) !Advance one line in the output file
              WRITE(93,'(f8.3)',ADVANCE='NO') LAT(IGP) !Advance one line in the output file
              WRITE(94,'(f8.3)',ADVANCE='NO') LONG(IGP) !Advance one line in the output file
              WRITE(94,'(f8.3)',ADVANCE='NO') LAT(IGP) !Advance one line in the output file
              WRITE(95,'(f8.3)',ADVANCE='NO') LONG(IGP) !Advance one line in the output file
              WRITE(95,'(f8.3)',ADVANCE='NO') LAT(IGP) !Advance one line in the output file
              WRITE(11,'(f8.3)',ADVANCE='NO') LONG(IGP) !Advance one line in the output file
              WRITE(11,'(f8.3)',ADVANCE='NO') LAT(IGP) !Advance one line in the output file
C [B2: Tmin/Tmax LON/LAT headers; non-REGRID branch (uses LONG, LAT
C  vs REGRID's LON_OUT, LAT_OUT). - DKB 2026-05-12]
              WRITE(100,'(f8.3)',ADVANCE='NO') LONG(IGP) !B2 Tmin
              WRITE(100,'(f8.3)',ADVANCE='NO') LAT(IGP) !B2 Tmin
              WRITE(101,'(f8.3)',ADVANCE='NO') LONG(IGP) !B2 Tmax
              WRITE(101,'(f8.3)',ADVANCE='NO') LAT(IGP) !B2 Tmax
              DO IMM=1,MM
                IF(DAILYOUT) THEN
                  DO IMD=1,31
                    DO IND=1,STEP_DAY
                      IF(IMD.LE.MTHDAY(IMM)) THEN
                        WRITE(92,'(f10.3)',ADVANCE='NO')
     &                   T_OUT_M(IGP,IMM,IMD,IND)
                        WRITE(93,'(f10.3)',ADVANCE='NO')
     &                   P_OUT_M(IGP,IMM,IMD,IND)
                        WRITE(94,'(f10.3)',ADVANCE='NO')
     &                   SW_OUT_M(IGP,IMM,IMD,IND)
                        WRITE(11,'(f10.3)',ADVANCE='NO')
     &                   DTEMP_OUT_M(IGP,IMM,IMD)
                        WRITE(95,'(i10)',ADVANCE='NO')
     &                   F_WET_CLIM_OUT(IGP,IMM)
C [B2: Tmin = T - DTEMP/2; Tmax = T + DTEMP/2; same units as T (K).
C  non-REGRID DAILYOUT=TRUE branch (uses T_OUT_M, DTEMP_OUT_M; no
C  _REGRID suffix). - DKB 2026-05-12]
                        WRITE(100,'(f10.3)',ADVANCE='NO')
     &                   T_OUT_M(IGP,IMM,IMD,IND)
     &                  -DTEMP_OUT_M(IGP,IMM,IMD)/2.0
                        WRITE(101,'(f10.3)',ADVANCE='NO')
     &                   T_OUT_M(IGP,IMM,IMD,IND)
     &                  +DTEMP_OUT_M(IGP,IMM,IMD)/2.0
                      ENDIF
                    ENDDO
                  ENDDO
                ELSE
                  WRITE(92,'(f10.3)',ADVANCE='NO')
     &             T_OUT_M(IGP,IMM,1,1)
                  WRITE(93,'(f10.3)',ADVANCE='NO')
     &             P_OUT_M(IGP,IMM,1,1)
                  WRITE(94,'(f10.3)',ADVANCE='NO')
     &             SW_OUT_M(IGP,IMM,1,1)
                  WRITE(11,'(f10.3)',ADVANCE='NO')
     &             DTEMP_OUT_M(IGP,IMM,1)
                  WRITE(95,'(i10)',ADVANCE='NO')
     &             F_WET_CLIM_OUT(IGP,IMM)
C [B2: Tmin = T - DTEMP/2; Tmax = T + DTEMP/2; same units as T (K).
C  non-REGRID DAILYOUT=FALSE branch (monthly mean). - DKB 2026-05-12]
                  WRITE(100,'(f10.3)',ADVANCE='NO')
     &             T_OUT_M(IGP,IMM,1,1)
     &            -DTEMP_OUT_M(IGP,IMM,1)/2.0
                  WRITE(101,'(f10.3)',ADVANCE='NO')
     &             T_OUT_M(IGP,IMM,1,1)
     &            +DTEMP_OUT_M(IGP,IMM,1)/2.0
                ENDIF
              ENDDO
              WRITE(92,'()') !Advance one line in the output file
              WRITE(93,'()') !Advance one line in the output file
              WRITE(94,'()') !Advance one line in the output file
              WRITE(95,'()') !Advance one line in the output file
              WRITE(11,'()') !Advance one line in the output file
C [B2: per-cell newlines for Tmin_anom (unit 100) + Tmax_anom (unit
C  101). non-REGRID branch. - DKB 2026-05-12]
              WRITE(100,'()') !B2 Tmin
              WRITE(101,'()') !B2 Tmax
            ENDDO
          ENDIF !End of REGRID conditional

C [Step 17b (F-N B10): UNCONDITIONAL CLOSE per IYEAR iteration for
C  T/P/SW/WET/DTEMP units (11, 92, 93, 94, 95). Symmetric with OPEN
C  blocks at lines ~954 (REGRID branch) + ~1013 (non-REGRID branch);
C  closes the per-iteration writes cleanly so units are reusable on
C  the next IYEAR iteration. Symmetric with the C++ in-process port
C  CLOSE fix at commit 7be595a (climatemodel.cpp ~line 963; C++ uses
C  std::ofstream RAII so its close is implicit, but the Fortran units
C  require explicit CLOSE to avoid carrying stale file-position state
C  forward). - DKB 2026-05-11]
          CLOSE(92)
          CLOSE(93)
          CLOSE(94)
          CLOSE(95)
          CLOSE(11)
C [B2: CLOSE Tmin_anom (unit 100) + Tmax_anom (unit 101); symmetric
C  with B10's unconditional-CLOSE-per-IYEAR-iteration semantics for
C  units 92/93/94/95/11 above. - DKB 2026-05-12]
          CLOSE(100)
          CLOSE(101)

          !Write a temporary file to tell LPJ-GUESS that IMOGEN has completed writing the climate files - TP 29.07.15
          OPEN(97,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'done',STATUS='REPLACE')
          WRITE(97,*)'Climate files written'
          CLOSE(97)
        ENDIF

C Write out FA_OCEAN and DTEMP_O here, to allow restart - TP 13.07.15

        IF(OCEAN_FEED) THEN
C [Step 17b (F-N B10): UNCONDITIONAL OPEN per IYEAR iteration for the
C  FA_OCEAN/DTEMP_O restart files (units 95, 96). Same root cause +
C  same fix as the climate-anomalies block at line ~954 (canonical
C  doc). Per-year writes ensure restart from any year is possible
C  (vs only-YEAR1 with the previous gate). Symmetric with the C++
C  in-process port fix at commit 7be595a (climatemodel.cpp ~line 988).
C  NOTE: this block reuses unit 95 already CLOSE'd at line ~1071
C  above; reopening here for the ocean feedback writer is intentional
C  (different file path: fa_ocean.dat vs WET.dat above). - DKB 2026-05-11]
          OPEN(95,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'fa_ocean.dat')
          OPEN(96,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'dtemp_o.dat')
          DO IGP=1,NFARRAY
            WRITE(95,*) FA_OCEAN(IGP)
          ENDDO
          DO IGP=1,N_OLEVS
            WRITE(96,*) DTEMP_O(IGP)
          ENDDO
        ENDIF
C [Step 17b (F-N B10): UNCONDITIONAL CLOSE per IYEAR iteration for
C  units 95 (fa_ocean.dat) + 96 (dtemp_o.dat). Symmetric with OPEN
C  block at line ~1088 above; symmetric with C++ fix at commit
C  7be595a (climatemodel.cpp ~line 998). - DKB 2026-05-11]
        CLOSE(95)
        CLOSE(96)

        CALL FLUSH(6)
      ENDDO !End of IYEAR loop

      ENDDO !End of KEEPRUNNING loop - TP 29.07.15

C [Step 3 of unified-codebase rebuild: deallocate the NGPOINTS-dimensioned
C  arrays (good hygiene; prevents leak warnings under valgrind/sanitisers).
C  - DKB 2026-05-05]
      IF(ALLOCATED(T_OUT_M_REGRID))     DEALLOCATE(T_OUT_M_REGRID)
      IF(ALLOCATED(P_OUT_M_REGRID))     DEALLOCATE(P_OUT_M_REGRID)
      IF(ALLOCATED(SW_OUT_M_REGRID))    DEALLOCATE(SW_OUT_M_REGRID)
      IF(ALLOCATED(DTEMP_OUT_M_REGRID)) DEALLOCATE(DTEMP_OUT_M_REGRID)
      IF(ALLOCATED(F_WET_CLIM_REGRID))  DEALLOCATE(F_WET_CLIM_REGRID)
      IF(ALLOCATED(LON_OUT))            DEALLOCATE(LON_OUT)
      IF(ALLOCATED(LAT_OUT))            DEALLOCATE(LAT_OUT)

      STOP
      END

!----------------------------------------------------------------------
! This subroutine regrids the climate data via nearest neighbour
! interpolation. The routine reads in a gridlist with length NGPOINTS
! and finds the closest IMOGEN climate data for each point in that gridlist.
! T. Pugh, 06.08.15
!----------------------------------------------------------------------

      SUBROUTINE REGRID_CLIM(T_OUT_M,SW_OUT_M,P_OUT_M,DTEMP_OUT_M,F_WET_CLIM_OUT,MM,NSDMAX,GPOINTS,LONG,LAT
     & ,T_OUT_M_REGRID,P_OUT_M_REGRID,SW_OUT_M_REGRID,DTEMP_OUT_M_REGRID,F_WET_CLIM_REGRID,NGPOINTS,LON_OUT
     & ,LAT_OUT,DIR_COMMON,THISYEAR,FILE_GRIDLIST)

      IMPLICIT NONE

      INTEGER MM,NSDMAX,GPOINTS     !IN Dimension size indicators from main programme
      INTEGER NGPOINTS              !IN Number of grid points in new gridlist

      CHARACTER*180
     & DIR_COMMON !IN Directory containing files shared between LPJ-GUESS and IMOGEN
      CHARACTER*4
     & THISYEAR !IN string version of IYEAR for use in locating input/output files
      CHARACTER*180
     & FILE_GRIDLIST

      REAL
     & T_OUT_M(GPOINTS,MM,31,NSDMAX)       !IN Calculated temperature for 365 day year
     &,P_OUT_M(GPOINTS,MM,31,NSDMAX)       !IN Calculated total precipitation for 365 day year
     &,SW_OUT_M(GPOINTS,MM,31,NSDMAX)      !IN Calculated shortwave radiation for 365 day year
     &,DTEMP_OUT_M(GPOINTS,MM,31)          !IN Calculated daily temperature range for 365 day year
      INTEGER F_WET_CLIM_OUT(GPOINTS,MM)

      REAL
     & LAT(GPOINTS)                   !WORK Latitudinal position of land
     &,LONG(GPOINTS)                  !WORK Longitudinal position of lan

      REAL
     & T_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)  !OUT Regridded calculated temperature for 365 day year
     &,P_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX)  !OUT Regridded calculated total precipitation for 365 day year
     &,SW_OUT_M_REGRID(NGPOINTS,MM,32,NSDMAX) !OUT Regridded calculated shortwave radiation for 365 day year
     &,DTEMP_OUT_M_REGRID(NGPOINTS,MM,32)     !OUT Regridded calculated daily temperature range for 365 day year
      INTEGER F_WET_CLIM_REGRID(NGPOINTS,MM)

      REAL
     & LON_OUT(NGPOINTS)            !IN/OUT Longitude array to perform regridding to (read from file)
     &,LAT_OUT(NGPOINTS)            !IN/OUT Latitude array to perform regridding to (read from file)
     &,LON_OUT_WORK(NGPOINTS)       !WORK Longitude array running from 0 to 360, instead of -180 to 180.

      REAL DDIFF,DDIFF_MIN          !WORK Variables for nearest neighbour calculation
      INTEGER IND_MIN               !WORK Index of nearest neighbour in array with dimension GPOINTS
      INTEGER NGP,GP,IMM,IMD,IND    !WORK Loop counters
      INTEGER CC,IOS                !WORK Loop counters

      LOGICAL FILEEXIST             !WORK Logical for existence of gridlist file

      PRINT *,'Performing nearest-neighbour interpolation of climate output'

      INQUIRE(FILE=FILE_GRIDLIST,EXIST=FILEEXIST)
      IF (FILEEXIST.EQV..FALSE.) THEN
        PRINT *,'ERROR: gridlist_out.txt not found'
        OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
        WRITE(98,*)'gridlist_out.txt not found'
        CLOSE(98)
        STOP
      ENDIF

!Read in gridlist at appropriate resolution. NOTE: File gridlist_out.txt must have the same length as NGPOINTS
      OPEN(21,FILE=FILE_GRIDLIST)
      IOS=0
      CC=0
      DO WHILE (IOS.EQ.0)
        CC=CC+1
        READ(21,*,IOSTAT=IOS) LON_OUT(CC), LAT_OUT(CC)

        !Adjust for any longitude values less than 0.0 for the IMOGEN calculations - 06.08.15
        IF (LON_OUT(CC).LT.0.0) THEN
          LON_OUT_WORK(CC)=LON_OUT(CC)+360.0
        ELSE
          LON_OUT_WORK(CC)=LON_OUT(CC)
        ENDIF

        IF (IOS.NE.0) CONTINUE

        !PRINT *,LON_OUT(CC), LAT_OUT(CC)
        IF (CC.GT.(NGPOINTS+1)) THEN
          PRINT *,'ERROR: Gridlist file and NGPOINTS not compatible'
          OPEN(98,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/IMOGEN/output/'//THISYEAR//'/'//'error',STATUS='REPLACE')
          WRITE(98,*)'Gridlist file and NGPOINTS not compatible'
          CLOSE(98)
          STOP
        ENDIF
      ENDDO
      CLOSE(21)

! Now make the nearest neighbour interpolation

      DO NGP=1,NGPOINTS
        DDIFF_MIN=10000.0 !Initialise to high value
        DO GP=1,GPOINTS
          DDIFF=ABS(LON_OUT_WORK(NGP)-LONG(GP)) + ABS(LAT_OUT(NGP)-LAT(GP))
          IF (DDIFF.LT.DDIFF_MIN) THEN
            DDIFF_MIN=DDIFF
            IND_MIN=GP
          ENDIF
        ENDDO
        !Now assign values from best fitting lat and lon to output arrays
        DO IMM=1,MM
          DO IMD=1,31
            DO IND=1,NSDMAX
              T_OUT_M_REGRID(NGP,IMM,IMD,IND)=T_OUT_M(IND_MIN,IMM,IMD,IND)
              P_OUT_M_REGRID(NGP,IMM,IMD,IND)=P_OUT_M(IND_MIN,IMM,IMD,IND)
              SW_OUT_M_REGRID(NGP,IMM,IMD,IND)=SW_OUT_M(IND_MIN,IMM,IMD,IND)
            ENDDO
            DTEMP_OUT_M_REGRID(NGP,IMM,IMD)=DTEMP_OUT_M(IND_MIN,IMM,IMD)
          ENDDO
          F_WET_CLIM_REGRID(NGP,IMM)=F_WET_CLIM_OUT(IND_MIN,IMM)
        ENDDO
      ENDDO

      RETURN
      END

!----------------------------------------------------------------------
! This subroutine reads the settings file
! T. Pugh, 17.07.15
!----------------------------------------------------------------------

      SUBROUTINE SETTIN(STEP_DAY,NYR_NON_CO2,NYR_EMISS,NYR_EMISS_NONCO2,
     & KAPPA_O,F_OCEAN,T_OCEAN_INIT,LAMBDA_L,LAMBDA_O,MU,Q2CO2,
     & CO2_INIT_PPMV,FILE_NON_CO2,C_EMISSIONS_IN,LPJG_CFLUX,
     & INCLUDE_CO2_IN,FILE_GRIDLIST,
     & INCLUDE_NON_CO2,DAILYOUT,LAND_FEED,OCEAN_FEED,ANLG,ANOM,DIR_PATT,
     & DIR_CLIM,FILE_SCEN_EMITS,FILE_NON_CO2_VALS,FILE_SCEN_CO2_PPMV,
     & FILE_LPJG_FLUX,NYR_LPJG_FLUX,DIR_COMMON,REGRID,
     & FILE_CH4_N2O_EMITS,CH4_INIT_PPBV,N2O_INIT_PPBV,TAU_DECAY_CH4,
     & TAU_DECAY_N2O,NONCO2_EMISSIONS,NONCO2_EMISSIONS_LPJG,FILE_LPJG_CH4_N2O_FLUX,
     & CO2_RF_FAIR,NGPOINTS) !NGPOINTS added in Step 3 of unified-codebase rebuild - DKB 2026-05-05

      IMPLICIT NONE

      INTEGER IOS,LINE
      INTEGER POS
      CHARACTER(LEN=180) BUFFER,LABEL

      INTEGER STEP_DAY      !IN Number of daily timesteps of IMPACTS_MODEL !NOTE: Formerly set to 24, appeared to cause random unreproducible segmentation fault on change to 1 - TP 13.07.15
      INTEGER NYR_NON_CO2   !IN Number of years for which NON_CO2 forcing is prescribed.
      INTEGER NYR_EMISS     !IN Number of years of emission data in file.
      INTEGER NYR_EMISS_NONCO2 !IN Number of years of CH4 and N2O emission data in file.
      INTEGER NYR_LPJG_FLUX !IN Number of years of emission data in LPJ-GUESS C flux file
      INTEGER NGPOINTS      !OUT Number of grid points in regridding gridlist (FILE_GRIDLIST). Added Step 3 of unified-codebase rebuild - DKB 2026-05-05

      REAL KAPPA_O      !IN Ocean eddy diffusivity (W/m/K)
      REAL F_OCEAN      !IN Fractional coverage of the ocean
      REAL T_OCEAN_INIT
      REAL LAMBDA_L     !IN Inverse of climate sensitivity over land (W/m2/K)
      REAL LAMBDA_O     !IN Inverse of climate sensitivity over ocean (W/m2/K)
      REAL MU           !IN Ratio of land to ocean temperature anomalies
      REAL Q2CO2        !IN Radiative forcing due to doubling CO2 (W/m2
      REAL CO2_INIT_PPMV !IN Initial CO2 concentration (ppmv)
      REAL CH4_INIT_PPBV !IN Initial CH4 concentration (ppbv)
      REAL N2O_INIT_PPBV !IN Initial N2O concentration (ppbv)
      REAL TAU_DECAY_CH4     !IN Atmospheric lifetime of CH4 (years)
      REAL TAU_DECAY_N2O     !IN Atmospheric lifetime of N2O (years)

      LOGICAL FILE_NON_CO2      !IN If true, then non-CO2 radiative forcings are contained within a file.
      LOGICAL C_EMISSIONS_IN    !IN If true, means CO2 concentration is calcula
      LOGICAL LPJG_CFLUX        !IN If true, take land C flux from LPJ-GUESS output file
      LOGICAL INCLUDE_CO2_IN    !IN Are adjustments to CO2 values allowed?
      LOGICAL INCLUDE_NON_CO2   !IN Are adjustments to non-CO2 values allowed?
      LOGICAL DAILYOUT          !IN Are outputs daily (true) or monthly (false)?
      LOGICAL LAND_FEED         !IN Are land feedbacks allowed on atmospheric C
      LOGICAL OCEAN_FEED        !IN Are ocean feedbacks allowed on atmospheric
      LOGICAL ANLG              !IN If true, then use the GCM analogue model
      LOGICAL ANOM              !IN If true, then use the GCM analogue model
      LOGICAL REGRID    !IN If true use nearest-neighbour regridding - TP 06.08.15
      LOGICAL NONCO2_EMISSIONS !IN If true, use FAIR model for CH4 and N2O forcing
      LOGICAL NONCO2_EMISSIONS_LPJG !IN Whether to use LPJG to provide natural CH4 and N2O emissions (if NONCO2_EMISSIONS==T)
      LOGICAL CO2_RF_FAIR       !IN Whether to use the CO2 radiative forcing calculation from the FAIR model (T) or IMOGEN standard (F)

      CHARACTER(LEN=180) DIR_PATT           !Directory containing the patterns
      CHARACTER(LEN=180) DIR_CLIM           !Directory containing initialising climatology.
      CHARACTER(LEN=180) DIR_COMMON         !Directory containing files shared between LPJ-GUESS and IMOGEN
      CHARACTER(LEN=180) FILE_SCEN_EMITS    !IN If used, file containing CO2 emissions in G
      CHARACTER(LEN=180) FILE_NON_CO2_VALS  !IN If used, file containing non-CO2 values
      CHARACTER(LEN=180) FILE_SCEN_CO2_PPMV !IN If used, file containing CO2 values (in
      CHARACTER(LEN=180) FILE_LPJG_FLUX     !IN If used, file containing LPJ-GUESS flux values
      CHARACTER(LEN=180) FILE_CH4_N2O_EMITS !IN If used, file containing CH4 and N2O emission values
      CHARACTER(LEN=180) FILE_LPJG_CH4_N2O_FLUX !IN If used, file containing LPJ-GUESS CH4 and N2O flux values
      CHARACTER(LEN=180) FILE_GRIDLIST


      DIR_PATT=' '
      DIR_CLIM=' '
      DIR_COMMON=' '
      FILE_SCEN_EMITS=' '
      FILE_NON_CO2_VALS=' '
      FILE_CH4_N2O_EMITS=' '
      FILE_SCEN_CO2_PPMV=' '
      FILE_LPJG_FLUX=' '
      FILE_LPJG_CH4_N2O_FLUX=' '
C [Step 3 of unified-codebase rebuild: sentinel value for NGPOINTS so we
C  can detect a missing setting after the parse loop completes.]
      NGPOINTS=-1

      OPEN(81,FILE='imogen_settings.txt') !TODO: Update folder path appropriately - TP 03.08.15

      IOS=0
      LINE=0

      DO WHILE (IOS.EQ.0)
        READ(81,'(A)',IOSTAT=IOS) BUFFER
        IF(IOS.EQ.0) THEN
          LINE=LINE+1

          POS=SCAN(BUFFER,' ')
          LABEL=BUFFER(1:POS)
          BUFFER=BUFFER(POS+1:)

          SELECT CASE (LABEL)
            CASE('DIR_PATT')
              DIR_PATT=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read DIR_PATT: '//TRIM(DIR_PATT)
            CASE('DIR_CLIM')
              DIR_CLIM=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read DIR_CLIM: '//TRIM(DIR_CLIM)
            CASE('DIR_COMMON')
              DIR_COMMON=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read DIR_COMMON: '//TRIM(DIR_COMMON)
            CASE('FILE_SCEN_EMITS')
              FILE_SCEN_EMITS=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read FILE_SCEN_EMITS: '//TRIM(FILE_SCEN_EMITS)
            CASE('FILE_NON_CO2_VALS')
              FILE_NON_CO2_VALS=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read FILE_NON_CO2_VALS: '//
     &         TRIM(FILE_NON_CO2_VALS)
            CASE('FILE_SCEN_CO2_PPMV')
              FILE_SCEN_CO2_PPMV=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read FILE_SCEN_CO2_PPMV: '//
     &         TRIM(FILE_SCEN_CO2_PPMV)
            CASE('FILE_LPJG_FLUX')
              FILE_LPJG_FLUX=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read FILE_LPJG_FLUX: '//TRIM(FILE_LPJG_FLUX)
            CASE('FILE_GRIDLIST')
              FILE_GRIDLIST=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read FILE_GRIDLIST: '//TRIM(FILE_GRIDLIST)
            CASE('FILE_CH4_N2O_EMITS')
              FILE_CH4_N2O_EMITS=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read FILE_CH4_N2O_EMITS: '//
     &         TRIM(FILE_CH4_N2O_EMITS)
            CASE('FILE_LPJG_CH4_N2O_FLUX')
              FILE_LPJG_CH4_N2O_FLUX=TRIM(ADJUSTL(BUFFER))
              PRINT *,'Read FILE_LPJG_CH4_N2O_FLUX: '//
     &         TRIM(FILE_LPJG_CH4_N2O_FLUX)
            CASE('STEP_DAY')
              READ(BUFFER,*,IOSTAT=IOS) STEP_DAY
              PRINT *,'Read STEP_DAY: ',STEP_DAY
            CASE('T_OCEAN_INIT')
              READ(BUFFER,*,IOSTAT=IOS) T_OCEAN_INIT
              PRINT *,'Read T_OCEAN_INIT: ',T_OCEAN_INIT
            CASE('KAPPA_O')
              READ(BUFFER,*,IOSTAT=IOS) KAPPA_O
              PRINT *,'Read KAPPA_O: ',KAPPA_O
            CASE('F_OCEAN')
              READ(BUFFER,*,IOSTAT=IOS) F_OCEAN
              PRINT *,'Read F_OCEAN: ',F_OCEAN
            CASE('LAMBDA_L')
              READ(BUFFER,*,IOSTAT=IOS) LAMBDA_L
              PRINT *,'Read LAMBDA_L: ',LAMBDA_L
            CASE('LAMBDA_O')
              READ(BUFFER,*,IOSTAT=IOS) LAMBDA_O
              PRINT *,'Read LAMBDA_O: ',LAMBDA_O
            CASE('MU')
              READ(BUFFER,*,IOSTAT=IOS) MU
              PRINT *,'Read MU: ',MU
            CASE('Q2CO2')
              READ(BUFFER,*,IOSTAT=IOS) Q2CO2
              PRINT *,'Read Q2CO2: ',Q2CO2
            CASE('TAU_DECAY_CH4')
              READ(BUFFER,*,IOSTAT=IOS) TAU_DECAY_CH4
              PRINT *,'Read TAU_DECAY_CH4: ',TAU_DECAY_CH4
            CASE('TAU_DECAY_N2O')
              READ(BUFFER,*,IOSTAT=IOS) TAU_DECAY_N2O
              PRINT *,'Read TAU_DECAY_N2O: ',TAU_DECAY_N2O
            CASE('FILE_NON_CO2')
              READ(BUFFER,*,IOSTAT=IOS) FILE_NON_CO2
              PRINT *,'Read FILE_NON_CO2: ',FILE_NON_CO2
            CASE('NYR_NON_CO2')
              READ(BUFFER,*,IOSTAT=IOS) NYR_NON_CO2
              PRINT *,'Read NYR_NON_CO2: ',NYR_NON_CO2
            CASE('CO2_INIT_PPMV')
              READ(BUFFER,*,IOSTAT=IOS) CO2_INIT_PPMV
              PRINT *,'Read CO2_INIT_PPMV: ',CO2_INIT_PPMV
            CASE('CH4_INIT_PPBV')
              READ(BUFFER,*,IOSTAT=IOS) CH4_INIT_PPBV
              PRINT *,'Read CH4_INIT_PPBV: ',CH4_INIT_PPBV
            CASE('N2O_INIT_PPBV')
              READ(BUFFER,*,IOSTAT=IOS) N2O_INIT_PPBV
              PRINT *,'Read N2O_INIT_PPBV: ',N2O_INIT_PPBV
            CASE('NYR_EMISS')
              READ(BUFFER,*,IOSTAT=IOS) NYR_EMISS
              PRINT *,'Read NYR_EMISS: ',NYR_EMISS
            CASE('NYR_EMISS_NONCO2')
              READ(BUFFER,*,IOSTAT=IOS) NYR_EMISS_NONCO2
              PRINT *,'Read NYR_EMISS_NONCO2: ',NYR_EMISS_NONCO2
            CASE('NYR_LPJG_FLUX')
              READ(BUFFER,*,IOSTAT=IOS) NYR_LPJG_FLUX
              PRINT *,'Read NYR_LPJG_FLUX: ',NYR_LPJG_FLUX
            CASE('C_EMISSIONS')
              READ(BUFFER,*,IOSTAT=IOS) C_EMISSIONS_IN
              PRINT *,'Read C_EMISSIONS: ',C_EMISSIONS_IN
            CASE('LPJG_CFLUX')
              READ(BUFFER,*,IOSTAT=IOS) LPJG_CFLUX
              PRINT *,'Read LPJG_CFLUX: ',LPJG_CFLUX
            CASE('INCLUDE_CO2')
              READ(BUFFER,*,IOSTAT=IOS) INCLUDE_CO2_IN
              PRINT *,'Read INCLUDE_CO2: ',INCLUDE_CO2_IN
            CASE('INCLUDE_NON_CO2')
              READ(BUFFER,*,IOSTAT=IOS) INCLUDE_NON_CO2
              PRINT *,'Read INCLUDE_NON_CO2: ',INCLUDE_NON_CO2
            CASE('DAILYOUT')
              READ(BUFFER,*,IOSTAT=IOS) DAILYOUT
              PRINT *,'Read DAILYOUT: ',DAILYOUT
            CASE('LAND_FEED')
              READ(BUFFER,*,IOSTAT=IOS) LAND_FEED
              PRINT *,'Read LAND_FEED: ',LAND_FEED
            CASE('OCEAN_FEED')
              READ(BUFFER,*,IOSTAT=IOS) OCEAN_FEED
              PRINT *,'Read OCEAN_FEED: ',OCEAN_FEED
            CASE('ANLG')
              READ(BUFFER,*,IOSTAT=IOS) ANLG
              PRINT *,'Read ANLG: ',ANLG
            CASE('ANOM')
              READ(BUFFER,*,IOSTAT=IOS) ANOM
              PRINT *,'Read ANOM: ',ANOM
            CASE('REGRID')
              READ(BUFFER,*,IOSTAT=IOS) REGRID
              PRINT *,'Read REGRID: ',REGRID
            CASE('NONCO2_EMISSIONS')
              READ(BUFFER,*,IOSTAT=IOS) NONCO2_EMISSIONS
              PRINT *,'Read NONCO2_EMISSIONS: ',NONCO2_EMISSIONS
            CASE('NONCO2_EMISSIONS_LPJG')
              READ(BUFFER,*,IOSTAT=IOS) NONCO2_EMISSIONS_LPJG
              PRINT *,'Read NONCO2_EMISSIONS_LPJG: ',NONCO2_EMISSIONS_LPJG
            CASE('CO2_RF_FAIR')
              READ(BUFFER,*,IOSTAT=IOS) CO2_RF_FAIR
              PRINT *,'Read CO2_RF_FAIR: ',CO2_RF_FAIR
            CASE('NGPOINTS')
              READ(BUFFER,*,IOSTAT=IOS) NGPOINTS
              PRINT *,'Read NGPOINTS: ',NGPOINTS
            CASE DEFAULT
              PRINT *,'Skipping invalid label "',LABEL,'" at line ',LINE
          ENDSELECT
        ENDIF
      ENDDO

      CLOSE(81)
      CALL FLUSH(6)

C [Step 3 of unified-codebase rebuild: validate NGPOINTS was actually set.
C  If absent or non-positive, abort with a clear message rather than letting
C  ALLOCATE() fail or (worse) allocate a garbage size and segfault later.]
      IF(NGPOINTS.LE.0) THEN
        PRINT *,'ERROR: imogen_settings.txt is missing or has invalid'
        PRINT *,'       NGPOINTS line. Add e.g. "NGPOINTS 3698" matching'
        PRINT *,'       the line count of your FILE_GRIDLIST.'
        PRINT *,'       Got NGPOINTS=',NGPOINTS
        CALL FLUSH(6)
        STOP 1
      ENDIF

      RETURN
      END

!----------------------------------------------------------------------
! This subroutine reads the settings file shared between LPJ-GUESS and IMOGEN
! T. Pugh, 17.07.15
!----------------------------------------------------------------------

      SUBROUTINE SETTIN_LPJG(DIR_COMMON,YEAR1,IYEND,SPINUP,YEAR1_LPJG,
     &  KEEPRUNNING,FIRSTCALL)

      IMPLICIT NONE

      INTEGER IOS,LINE
      INTEGER POS
      CHARACTER(LEN=180) BUFFER,LABEL

      CHARACTER(LEN=180) DIR_COMMON        !Directory containing files shared between LPJ-GUESS and IMOGEN

      INTEGER YEAR1         !IN First year of the numerical experiment
      INTEGER IYEND         !IN Stop year of the ENTIRE run
      INTEGER YEAR1_LPJG    !IN First year of the whole LPJ-GUESS simulation

      LOGICAL SPINUP        !IN Are we in the spin-up phase of LPJ-GUESS?
      LOGICAL KEEPRUNNING   !IN Is the LPJ-GUESS run ended?
      LOGICAL FIRSTCALL     !IN Is this the very first call to IMOGEN from LPJ-GUESS (start of spin-up)?

      OPEN(82,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     & 'imogen_lpjg.txt')

      IOS=0
      LINE=0

      DO WHILE (IOS.EQ.0)
        READ(82,'(A)',IOSTAT=IOS) BUFFER
        IF(IOS.EQ.0) THEN
          LINE=LINE+1

          POS=SCAN(BUFFER,' ')
          LABEL=BUFFER(1:POS)
          BUFFER=BUFFER(POS+1:)

          SELECT CASE (LABEL)
            CASE('YEAR1')
              READ(BUFFER,*,IOSTAT=IOS) YEAR1
              PRINT *,'Read YEAR1: ',YEAR1
            CASE('IYEND')
              READ(BUFFER,*,IOSTAT=IOS) IYEND
              PRINT *,'Read IYEND: ',IYEND
            CASE('YEAR1_LPJG')
              READ(BUFFER,*,IOSTAT=IOS) YEAR1_LPJG
              PRINT *,'Read YEAR1_LPJG: ',YEAR1_LPJG
            CASE('SPINUP')
              READ(BUFFER,*,IOSTAT=IOS) SPINUP
              PRINT *,'Read SPINUP: ',SPINUP
            CASE('KEEPRUNNING')
              READ(BUFFER,*,IOSTAT=IOS) KEEPRUNNING
              PRINT *,'Read KEEPRUNNING: ',KEEPRUNNING
            CASE('FIRSTCALL')
              READ(BUFFER,*,IOSTAT=IOS) FIRSTCALL
              PRINT *,'Read FIRSTCALL: ',FIRSTCALL
            CASE DEFAULT
              PRINT *,'Skipping invalid label at line ',LINE
          ENDSELECT
        ENDIF
      ENDDO

      OPEN(82,FILE=TRIM(ADJUSTL(DIR_COMMON))//'/LPJG_main/IMOGEN/'//
     & 'done')
      CLOSE(82,STATUS='DELETE')
      CALL FLUSH(6)

      RETURN
      END

!----------------------------------------------------------------------
! This routine calculates sub-daily variability
! C. Huntingford (April 2001) - based on earlier version by P. Cox
!----------------------------------------------------------------------

      SUBROUTINE DAY_CALC(POINTSM,STEP_DAY,DAY_MON,SW_L,
     &           PRECIP_L,T_L,DTEMP_DAY_L,
     &           LW_L,PSTAR_L,WIND_L,RH15M_L,
     &           SW_SD,T_SD,LW_SD,
     &           CONV_RAIN_SD,LS_RAIN_SD,LS_SNOW_SD,
     &           PSTAR_SD,WIND_SD,QHUM_SD,MONTH,IDAY,
     &           LAT,LONG,SEC_DAY,NSDMAX,SEED_RAIN)

      IMPLICIT NONE

      INTEGER
     & DAY_MON              !IN "Number of days in a month" (day)
     &,POINTSM              !IN Maximum number of points in grid.
     &,STEP_DAY             !IN WORK Calculated number
C                           !of timesteps per day
     &,SEC_DAY              !WORK Number of seconds in day (sec)
     &,NSDMAX               !IN Maximum possible number
C                           !of sub-daily timesteps.
     &,SEED_RAIN(4)         !WORK Seeding numbers
C                           !required to disaggregate
                            !the rainfall
     &,N_TALLY              !WORK Counting up number
C                           !of precipitation periods.

!-----------------------------------------------------------------------
! Single day arrays of incoming variables
!-----------------------------------------------------------------------

      REAL
     & SW_L(POINTSM)        ! IN Daily values for downward
C                           ! shortwave radiation (W/m2)
     &,PRECIP_L(POINTSM)    ! In Daily values of
C                           ! rain+snow (mm/day)
     &,T_L(POINTSM)         ! IN Daily values of
C                           ! temperature (K)
     &,DTEMP_DAY_L(POINTSM) ! IN Daily values of
C                           ! diurnal temperature range (K)
     &,LW_L(POINTSM)        ! IN Daily values of surface
C                           ! longwave radiation (W/m**2).
     &,PSTAR_L(POINTSM)     ! IN Daily values of
C                           ! pressure at level 1 (Pa).
     &,WIND_L(POINTSM)      ! IN Daily values of wind speed (m/s)
     &,QHUM_L(POINTSM)      ! Humidity deficit
C                           ! calculated from RH15M (kg/kg)
     &,RH15M_L(POINTSM)     ! Humidity (%)

!------------------------------------------------RAINFALL_CLIM-----------------------
! Single day (global) arrays of variables above, but for up to hourly
! periods. NOTE: DTEMP_DAY_SD does not exist as T_SD combines T_L
! and DTEMP_DAY_L
!-----------------------------------------------------------------------

      REAL
     & SW_SD(POINTSM,NSDMAX)        ! OUT Sub-daily values for downward
C                                   ! shortwave radiation (W/m2)
     &,T_SD(POINTSM,NSDMAX)         ! OUT Sub-daily values of
C                                   ! temperature (K)
     &,LW_SD(POINTSM,NSDMAX)        ! OUT Sub-daily values of surface
C                                   ! longwave radiation (W/m**2).
     &,PSTAR_SD(POINTSM,NSDMAX)     ! OUT Sub-daily values of
C                                   ! pressure at level 1 (Pa).
     &,WIND_SD(POINTSM,NSDMAX)      ! OUT Sub-daily values
C                                   ! of wind speed (m/s)
     &,QHUM_SD(POINTSM,NSDMAX)      ! OUT Sub_daily humidity deficit
C                                   ! calculated from RH15M (kg/kg)
     &,CONV_RAIN_SD(POINTSM,NSDMAX) ! OUT Sub-daily
C                                   ! convective rain (mm/day)
     &,LS_RAIN_SD(POINTSM,NSDMAX)   ! OUT Sub-daily
C                                   ! large scale rain (mm/day)
     &,LS_SNOW_SD(POINTSM,NSDMAX)   ! OUT Sub-daily
C                                   ! large scale snow (mm/day)

      INTEGER
     & N_EVENT(POINTSM,NSDMAX)      ! 1: if rains/snows during
C                                   ! timestep period, 0: otherwise
     &,N_EVENT_LOCAL(NSDMAX)        ! As N_EVENT, but for each gridpoint

      REAL
     & PREC_LOC(NSDMAX)         ! Temporary value of rainfall for each
C                               ! gridbox.

      REAL
     & T_SD_LOCAL(POINTSM)          ! WORK Intermediate
C                               ! calculation of temperature (K)
     &,PSTAR_SD_LOCAL(POINTSM)      ! WORK Intermediate
C                               ! calculation of pressure (Pa)
     &,QS_SD_LOCAL(POINTSM)         ! WORK Saturated humidity
C                               ! deficit associated
                                ! with T_SD_LOCAL and PSTAR_SD_LOCAL (g/

      INTEGER
     & ISTEP                    ! WORK Loop over sub-daily periods
     &,MONTH                    ! IN Month of interest
     &,IDAY                     ! IN Day number since beginning of month
     &,DAYNUMBER                ! WORK Daynumber since beginning of year
     &,L                        ! WORK Loop over land points

      REAL
     & SUN(POINTSM,NSDMAX)      ! WORK Normalised solar radiation
     &,TIME_MAX(POINTSM)        ! WORK GMT at which
                                ! temperature is maximum (hours)
     &,LAT(POINTSM)             ! IN Latitude (degrees)
     &,LONG(POINTSM)            ! IN Longitude (degrees)
     &,TIME_DAY                 ! WORK Time of day (hours)
     &,TIMESTEP                 ! WORK Timestep (seconds)
     &,PI                       ! WORK Pi (.)
     &,RANDOM_NUM_SD            ! WORK Random number associated with rai

      PARAMETER(PI=3.1415926535879323846)

      REAL
     & TEMP_CONV                ! WORK Temperature above which
                                ! rainfall is convective (K)
     &,TEMP_SNOW                ! WORK Temperature below which
                                ! snow occurs (K)

      PARAMETER(TEMP_CONV = 293.15)
      PARAMETER(TEMP_SNOW = 275.15)

      REAL
     & INIT_HOUR_CONV_RAIN      !WORK Start of convective
                                !rain event (hour)
     &,INIT_HOUR_LS_RAIN        !WORK Start of large scale
                                !rain event (hour)
     &,INIT_HOUR_LS_SNOW        !WORK Start of large scale
                                !snow event (hour)
     &,DUR_CONV_RAIN            !WORK Start of convective
                                !rain event (hour)
     &,DUR_LS_RAIN              !WORK Duration of large scale
                                !rain event (hour)
     &,DUR_LS_SNOW              !WORK Start of large scale
                                !snow event (hour)
     &,END_HOUR_CONV_RAIN       !WORK End of convective
                                !rain event (hour)
     &,END_HOUR_LS_RAIN         !WORK End of large scale
                                !rain event (hour)
     &,END_HOUR_LS_SNOW         !WORK End of large scale
                                !snow event (hour)
     &,HOUREVENT                !WORK Local variable
C                               !giving hours during
C                               !diurnal period for checking
C                               !if precip. event occurs
     &,MAX_PRECIP_RATE          !WORK Maximum allowed precip.
C                               !rate allowed within each sub-daily
C                               !timestep (mm/day). (This only
C                               !applies when STEP_DAY.GE.2)
     &,PERIOD_LEN               !WORK Length of period (hr)


!-----------------------------------------------------------------------
! Calculate the maximum precipitation rate. It is noted that 58 mm/day
! over 8 timesteps, and where all fell within a single 3 hour period
! caused numerical issues for MOSES. This corresponded to a rate of
! 464 mm/day during the 3-hour period. Hence, place a limit of 350
! mm/day.
!-----------------------------------------------------------------------

      PARAMETER(MAX_PRECIP_RATE = 350.0)

!-----------------------------------------------------------------------
! First check whether sub-daily calculations are required.
!-----------------------------------------------------------------------

C      DUR_CONV_RAIN = 2.0
C      DUR_LS_RAIN = 5.0
C      DUR_LS_SNOW = 5.0

      DUR_CONV_RAIN = 6.0
      DUR_LS_RAIN = 1.0
      DUR_LS_SNOW = 1.0

      PERIOD_LEN = 24.0/FLOAT(STEP_DAY)

! Initialise arrays - Moved up to front of routine to avoid non-initialisation of array when STEP_DAY=1 - TP 20.07.15
      DO L=1,POINTSM
        DO ISTEP=1,STEP_DAY
          CONV_RAIN_SD(L,ISTEP)=0.0
          LS_RAIN_SD(L,ISTEP)=0.0
          LS_SNOW_SD(L,ISTEP)=0.0
          N_EVENT(L,ISTEP) = 0
          N_EVENT_LOCAL(ISTEP) = 0
          PREC_LOC(ISTEP) = 0.0
        ENDDO
      ENDDO

!-----------------------------------------------------------------------
! First check whether sub-daily calculations are required.
!-----------------------------------------------------------------------

      IF(STEP_DAY.GE.2) THEN

!-----------------------------------------------------------------------
! Ensure that the durations are at least as long as a time period for
! the model to prevent solution "falling through gaps"
!-----------------------------------------------------------------------

        IF(DUR_CONV_RAIN.LE.PERIOD_LEN)
     &     DUR_CONV_RAIN = PERIOD_LEN+1.0E-6
        IF(DUR_LS_RAIN.LE.PERIOD_LEN)
     &     DUR_LS_RAIN = PERIOD_LEN+1.0E-6
        IF(DUR_LS_SNOW.LE.PERIOD_LEN)
     &     DUR_LS_SNOW = PERIOD_LEN+1.0E-6

        TIMESTEP = FLOAT(SEC_DAY)/FLOAT(STEP_DAY)

!-----------------------------------------------------------------------
! Calculate the diurnal cycle in the SW radiation
!-----------------------------------------------------------------------

        DAYNUMBER = INT((MONTH-1.0)*REAL(DAY_MON))+IDAY
        CALL SUNNY (DAYNUMBER,STEP_DAY,POINTSM,1990
     &,           LAT,LONG,SUN,TIME_MAX)

!-----------------------------------------------------------------------
! Loop over timesteps
!-----------------------------------------------------------------------

        DO ISTEP=1,STEP_DAY
!-----------------------------------------------------------------------
! Calculate timestep values of the driving data.
!-----------------------------------------------------------------------

          TIME_DAY = (REAL(ISTEP) - 0.5) * TIMESTEP

          DO L=1,POINTSM
            T_SD(L,ISTEP) = T_L(L) + 0.5*DTEMP_DAY_L(L)
     &         *COS(2*PI*(TIME_DAY-3600.0*TIME_MAX(L))/SEC_DAY)
            LW_SD(L,ISTEP) =
     &        LW_L(L) * (4.0 * T_SD(L,ISTEP) / T_L(L) - 3.0)
            SW_SD(L,ISTEP) = SW_L(L) * SUN(L,ISTEP)

          ENDDO

!-----------------------------------------------------------------------
! Calculate timestep values of the driving data that is not split up
! into diurnal behaviour.
!-----------------------------------------------------------------------

          DO L=1,POINTSM
            PSTAR_SD(L,ISTEP) = PSTAR_L(L)
            WIND_SD(L,ISTEP) = WIND_L(L)
          ENDDO

!-----------------------------------------------------------------------
! Check that humidity value is not greater than QSAT (but otherwise, QHU
! is not split up into diurnal behaviour).
!-----------------------------------------------------------------------

          DO L=1,POINTSM
            PSTAR_SD_LOCAL(L) = PSTAR_SD(L,ISTEP)
            T_SD_LOCAL(L) = T_SD(L,ISTEP)
          ENDDO

          
          !OPEN(UNIT=99, FILE='B_qsat_output.txt', STATUS='REPLACE', ACTION='WRITE')

          !DO L = 1, POINTSM
          !  WRITE(99, '(I5,3F12.5)') PSTAR_SD_LOCAL(L)
          !END DO
          !PAUSE

          CALL QSAT(QS_SD_LOCAL,T_SD_LOCAL,PSTAR_SD_LOCAL,POINTSM)
          DO L=1,POINTSM
            QHUM_SD(L,ISTEP) = 0.01*RH15M_L(L)*QS_SD_LOCAL(L)
          ENDDO

        ENDDO   ! End of timestep loop within the individual days.
!-----------------------------------------------------------------------
! Calculate daily rainfall disaggregation
!-----------------------------------------------------------------------

        DO L=1,POINTSM

!-----------------------------------------------------------------------
! Precipitation is split into four components,
! these being large scale rain, convective rain, large scale snow,
! convective snow. Call random number generator for different
! durations.
!-----------------------------------------------------------------------

          CALL RNDM(RANDOM_NUM_SD,SEED_RAIN)

!-----------------------------------------------------------------------
! Calculate type of precipitation. The decision is based purely up
! mean daily temperature, T_L. The cutoffs are:
!
! Convective scale rain (duration CONV_RAIN_DUR): T_L > 20.0oC
! Large scale rain (duration LS_RAIN_DUR) : 20.0oC > T_L > 2oC
! Large scale snow (duration LS_SNOW_DUR) : T_L < 2oC
! Convective snow - IGNORED
!
!-----------------------------------------------------------------------

! Initialise arrays - Moved to front of routine - TP 20.07.15
          !DO ISTEP=1,STEP_DAY
          !  CONV_RAIN_SD(L,ISTEP)=0.0
          !  LS_RAIN_SD(L,ISTEP)=0.0
          !  LS_SNOW_SD(L,ISTEP)=0.0
          !  N_EVENT(L,ISTEP) = 0
          !  N_EVENT_LOCAL(ISTEP) = 0
          !  PREC_LOC(ISTEP) = 0.0
          !ENDDO
C Calculate rainfall disaggregation.

C Start with convective rain
C (temperatures based upon mean daily temperature)

C First check if warm enough for convective rain
          IF(T_L(L).GE.TEMP_CONV) THEN

            INIT_HOUR_CONV_RAIN = RANDOM_NUM_SD*(24.0-DUR_CONV_RAIN)
            END_HOUR_CONV_RAIN = INIT_HOUR_CONV_RAIN+DUR_CONV_RAIN

            N_TALLY = 0
            DO ISTEP=1,STEP_DAY
              HOUREVENT = (REAL(ISTEP)-0.5)*PERIOD_LEN
              IF(HOUREVENT.GE.INIT_HOUR_CONV_RAIN.AND.
     &           HOUREVENT.LT.END_HOUR_CONV_RAIN) THEN
                N_EVENT(L,ISTEP) = 1
                N_TALLY = N_TALLY + 1
              ENDIF
            ENDDO

            DO ISTEP=1,STEP_DAY
              IF(N_EVENT(L,ISTEP).EQ.1) THEN      !Rains on this day
                CONV_RAIN_SD(L,ISTEP) =
     &            (REAL(STEP_DAY)/REAL(N_TALLY))*PRECIP_L(L)
                PREC_LOC(ISTEP) = CONV_RAIN_SD(L,ISTEP)
                N_EVENT_LOCAL(ISTEP) = N_EVENT(L,ISTEP)
              ENDIF
            ENDDO

C Check that no convective rain periods
C exceed MAX_PRECIP_RATE, or if so,
C then redistribute. The variable that is redistributed is local
C variable PREC_LOC - CONV_RAIN_SD is then set to this after the
C call to REDIS.

            CALL REDIS(NSDMAX,STEP_DAY,MAX_PRECIP_RATE,PREC_LOC,
     &                 N_EVENT_LOCAL,N_TALLY)
            DO ISTEP=1,STEP_DAY
              CONV_RAIN_SD(L,ISTEP) = PREC_LOC(ISTEP)
            ENDDO

C Now look at large scale rainfall components

          ELSE IF(T_L(L).LT.TEMP_CONV.AND.T_L(L).GE.TEMP_SNOW) THEN

            INIT_HOUR_LS_RAIN = RANDOM_NUM_SD*(24.0-DUR_LS_RAIN)
            END_HOUR_LS_RAIN = INIT_HOUR_LS_RAIN+DUR_LS_RAIN

            N_TALLY = 0

            DO ISTEP=1,STEP_DAY
              HOUREVENT = (REAL(ISTEP)-0.5)*PERIOD_LEN
              IF(HOUREVENT.GE.INIT_HOUR_LS_RAIN.AND.
     &           HOUREVENT.LT.END_HOUR_LS_RAIN) THEN
                N_EVENT(L,ISTEP) = 1
                N_TALLY = N_TALLY + 1
              ENDIF
            ENDDO

            DO ISTEP=1,STEP_DAY
              IF(N_EVENT(L,ISTEP).EQ.1) THEN      !Rains on this day
                LS_RAIN_SD(L,ISTEP) =
     &            (REAL(STEP_DAY)/REAL(N_TALLY))*PRECIP_L(L)
                PREC_LOC(ISTEP) = LS_RAIN_SD(L,ISTEP)
                N_EVENT_LOCAL(ISTEP) = N_EVENT(L,ISTEP)
              ENDIF
            ENDDO

C Check that no large scale rain periods
C exceed MAX_PRECIP_RATE, or if so,
C then redistribute.

            CALL REDIS(NSDMAX,STEP_DAY,MAX_PRECIP_RATE,PREC_LOC,
     &                 N_EVENT_LOCAL,N_TALLY)
            DO ISTEP=1,STEP_DAY
              LS_RAIN_SD(L,ISTEP) = PREC_LOC(ISTEP)
            ENDDO

C Now look at large scale snow components

          ELSE

            INIT_HOUR_LS_SNOW = RANDOM_NUM_SD*(24.0-DUR_LS_SNOW)
            END_HOUR_LS_SNOW = INIT_HOUR_LS_SNOW+DUR_LS_SNOW

            N_TALLY = 0

            DO ISTEP=1,STEP_DAY
              HOUREVENT = (REAL(ISTEP)-0.5)*PERIOD_LEN
              IF(HOUREVENT.GE.INIT_HOUR_LS_SNOW.AND.
     &           HOUREVENT.LT.END_HOUR_LS_SNOW) THEN
                N_EVENT(L,ISTEP) = 1
                N_TALLY = N_TALLY + 1
              ENDIF
            ENDDO

            DO ISTEP=1,STEP_DAY
              IF(N_EVENT(L,ISTEP).EQ.1) THEN       !Rains on this day
                LS_SNOW_SD(L,ISTEP) =
     &              (REAL(STEP_DAY)/REAL(N_TALLY))*PRECIP_L(L)
                PREC_LOC(ISTEP) = LS_SNOW_SD(L,ISTEP)
                N_EVENT_LOCAL(ISTEP) = N_EVENT(L,ISTEP)
              ENDIF
            ENDDO

C Check that no large scale snow periods exceed MAX_PRECIP_RATE,
C or if so, then redistribute.

            CALL REDIS(NSDMAX,STEP_DAY,MAX_PRECIP_RATE,PREC_LOC,
     &                 N_EVENT_LOCAL,N_TALLY)
            DO ISTEP=1,STEP_DAY
              LS_SNOW_SD(L,ISTEP) = PREC_LOC(ISTEP)
            ENDDO

          ENDIF

        ENDDO        ! End of large loop over different land points.
C in calculation of different rainfall behaviours

      ELSE           ! Now case where no subdaily variation (TSTEP=1)

        ISTEP=1 !Must be set here otherwise not defined - TP 13.07.15

        DO L=1,POINTSM
          PSTAR_SD_LOCAL(L) = PSTAR_SD(L,ISTEP)
          T_SD_LOCAL(L) = T_SD(L,ISTEP)
        ENDDO
        CALL QSAT(QS_SD_LOCAL,T_SD_LOCAL,PSTAR_SD_LOCAL,POINTSM)

        DO L = 1,POINTSM
          SW_SD(L,1) = SW_L(L)
          T_SD(L,1) = T_L(L)
          LW_SD(L,1) = LW_L(L)
          PSTAR_SD(L,1) = PSTAR_L(L)
          WIND_SD(L,1) = WIND_L(L)
          QHUM_SD(L,1) = 0.01*RH15M_L(L)*QS_SD_LOCAL(L)

          IF(T_L(L).GE.TEMP_CONV) THEN
            CONV_RAIN_SD(L,1) = PRECIP_L(L)
          ELSE IF(T_L(L).LT.TEMP_CONV.AND.T_L(L).GE.TEMP_SNOW) THEN
            LS_RAIN_SD(L,1) = PRECIP_L(L)
          ELSE
            LS_SNOW_SD(L,1) = PRECIP_L(L)
          ENDIF

        ENDDO

      ENDIF !End of loop to chose whether sub-daily is required

      RETURN
      END

C*********************************************************************
C Routine to redistribute rainfall if maximum precipitation rate is
C exceeded.
C
C Written by Chris Huntingford (September 2001)
C*********************************************************************

      SUBROUTINE REDIS(NSDMAX,STEP_DAY,MAX_PRECIP_RATE,PREC_LOC,
     &                 N_EVENT_LOCAL,N_TALLY)

      INTEGER
     & STEP_DAY             !IN WORK Calculated number
C                           !of timesteps per day
     &,NSDMAX               !IN Maximum possible number
C                           !of sub-daily timesteps.

      REAL
     & MAX_PRECIP_RATE      !WORK Maximum allowed precip.
C                           !rate allowed within each sub-daily
C                           !timestep (mm/day). (This only
C                           !applies when STEP_DAY.GE.2)
     &,PREC_LOC(NSDMAX)     ! Temporary value of rainfall for each
C                           ! gridbox.
     &,PREC_TOT             !WORK Total precip during entire day (mm/day
     &,PREC_TOT_ADJ         !WORK Temporary adjusted total (mm/day)
     &,PREC_CHANGE          !WORK The amount of precipitation to be
C                           !redistributed within day (mm/day)
     &,EXTRA_PER_REAL       !WORK Number of extra periods of rainfall
C                           !(expressed as a real number) that are
C                           !required.

      INTEGER
     & N_EVENT_LOCAL(NSDMAX)  ! 1: if rains/snows during
C                             ! timestep period, 0: otherwise
     &,N_TALLY              !WORK Number of precipitation
C                           !periods before redistribution.
     &,I                      ! WORK Looping parameter
     &,FIRST_PERIOD         ! First period of precipitation
     &,LAST_PERIOD          ! Last period of precipitation
     &,EXTRA_PER_INT        ! WORK Integer value
C                           ! of EXTRA_PER_REAL


C  Recalculate the total precipitation for the day (in units of mm)

      PREC_TOT = 0.0
      DO I = 1,STEP_DAY
        PREC_TOT = PREC_TOT + (1.0/FLOAT(STEP_DAY))*PREC_LOC(I)
      ENDDO

C Now limit the possible precipitation rate

      DO I = 1,STEP_DAY
        IF(PREC_LOC(I).GT.MAX_PRECIP_RATE) PREC_LOC(I)
     &            = MAX_PRECIP_RATE
      ENDDO

C Calculate the new total precipitation for the day

      PREC_TOT_ADJ = 0.0
      DO I = 1,STEP_DAY
        PREC_TOT_ADJ = PREC_TOT_ADJ +
     &                 (1.0/FLOAT(STEP_DAY))*PREC_LOC(I)
      ENDDO

C Now scatter remaining amount across other periods.
C First revisit the hours where the precipitation may be placed.
C This includes initially before the rainfall event, and then
C after. Start by finding the LAST period.


      DO I = 1,STEP_DAY
        IF(N_EVENT_LOCAL(I).EQ.1) LAST_PERIOD = I
      ENDDO
      FIRST_PERIOD = LAST_PERIOD-N_TALLY+1

      PREC_CHANGE = PREC_TOT - PREC_TOT_ADJ

C Calculate the number of extra periods required. Ideally this
C number is less than STEP_DAY-N_TALLY

C Check that only looking at case when PREC_CHANGE is non-zero

      IF(PREC_CHANGE.GT.0.0) THEN

        EXTRA_PER_REAL =
     & ((PREC_CHANGE*FLOAT(STEP_DAY))/MAX_PRECIP_RATE)
        EXTRA_PER_INT = INT(EXTRA_PER_REAL)

C First case where it is not possible to distribute all the rainfall.

        IF(EXTRA_PER_INT.GE.STEP_DAY-N_TALLY) THEN
          DO I = 1,STEP_DAY
            IF(N_EVENT_LOCAL(I).EQ.0) PREC_LOC(I) = MAX_PRECIP_RATE
          ENDDO
        ENDIF

C Now fill in the time periods before and after the storm.
C Periods are calculated and are moving away from FIRST_PERIOD
C and LAST_PERIOD. Options are as follows:
C
C 1) No periods available before storm, hence all distributed
C after the storm.
C
C 2) All may be accommodated before the storm and nothing after
C
C 3) Then case 3, whereby some of the rain must fall after the
C storm period.
C

C Do case (1); FIRST_PERIOD = 1, hence all precipitation is
C after the storm.

        IF(FIRST_PERIOD.EQ.1) THEN
          DO I = LAST_PERIOD+1,LAST_PERIOD+EXTRA_PER_INT
            PREC_LOC(I) = MAX_PRECIP_RATE
          ENDDO
          PREC_LOC(LAST_PERIOD+EXTRA_PER_INT+1) =
     &      MAX_PRECIP_RATE*(EXTRA_PER_REAL - FLOAT(EXTRA_PER_INT))

C Now do the case where all rain may be accommodated before storm.

        ELSE IF((EXTRA_PER_INT+1).LE.FIRST_PERIOD-1) THEN
          DO I = FIRST_PERIOD-1,FIRST_PERIOD-EXTRA_PER_INT,-1
            PREC_LOC(I) = MAX_PRECIP_RATE
          ENDDO
          PREC_LOC(FIRST_PERIOD-EXTRA_PER_INT-1) =
     &      MAX_PRECIP_RATE*(EXTRA_PER_REAL - FLOAT(EXTRA_PER_INT))

C Now do case where some rain falls after the storm, and all periods
C before the sotrm it rains.

        ELSE
          DO I = FIRST_PERIOD-1,1,-1
            PREC_LOC(I) = MAX_PRECIP_RATE
          ENDDO
          DO I = LAST_PERIOD+1,
     &         LAST_PERIOD+EXTRA_PER_INT-(FIRST_PERIOD-1)
            PREC_LOC(I) = MAX_PRECIP_RATE
          ENDDO
          PREC_LOC(LAST_PERIOD+EXTRA_PER_INT-(FIRST_PERIOD-1)+1) =
     &      MAX_PRECIP_RATE*(EXTRA_PER_REAL - FLOAT(EXTRA_PER_INT))
        ENDIF      !End of distribution options.
      ENDIF        !End of check whether redistribution is required.

      RETURN
      END

C**********************************************************************
C Routine to calculate the normalised solar radiation at each time and
C the time of the daily maximum temperature (GMT).
C
C Written by Peter Cox (March 1996)
C**********************************************************************
      SUBROUTINE SUNNY (DAYNUMBER,JDAY,POINTS,YEAR,LAT,LONG
     &,                 SUN,TIME_MAX)


      INTEGER
     & DAYNUMBER                       ! IN Day of the year.
     &,JDAY                            ! IN Number of timesteps in the
C                                      !    day.
     &,POINTS                          ! IN Number of spatial points.
     &,YEAR                            ! IN Calender year.

      REAL
     & LAT(POINTS)                     ! IN Latitude (degrees).
     &,LONG(POINTS)                    ! IN Longitude (degrees).
     &,SUN(POINTS,JDAY)                ! OUT Normalised solar radiation
C                                      !     at each time.
     &,TIME_MAX(POINTS)                ! OUT GMT at which temperature is
C                                      !     maximum (hrs).
     &,COSDEC                          ! WORK COS (solar declination).
     &,COSLAT                          ! WORK COS (latitude).
     &,COSZ(POINTS)                    ! WORK Timestep mean COSZ.
     &,COSZM(POINTS)                   ! WORK Daily mean COSZ.
     &,LATRAD                          ! WORK Latitude (radians).
     &,LIT(POINTS)                     ! WORK Sunlit fraction of the day
     &,LONGRAD(POINTS)                 ! WORK Longitude (radians).
     &,SCS                             ! WORK Factor for TOA solar.
     &,SINDEC                          ! WORK SIN (solar declination).
     &,SINLAT(POINTS)                  ! WORK SIN (latitude).
     &,TANDEC                          ! WORK TAN (solar declination).
     &,TANLAT                          ! WORK TAN (latitude).
     &,TANTAN                          ! WORK TANDEC*TANLAT.
     &,OMEGA_UP,OMEGA_DOWN             ! WORK Solar angle of sunrise and
C                                      !      sunset (radians).
     &,TIME_UP,TIME_DOWN               ! WORK GMT of sunrise and sunset
C                                      !      (hrs).
     &,TIMESTEP                        ! WORK Timestep (s).

      INTEGER
     & I,J                             ! WORK Loop counter.


      REAL PI,PI_OVER_180,RECIP_PI_OVER_180
      PARAMETER(
     & PI=3.1415926535879323846,! Pi
     & PI_OVER_180 =PI/180.0,   ! Conversion factor degrees to radians
     & RECIP_PI_OVER_180 = 180.0/PI ! Conversion factor radians to
     &                              ! degrees
     & )

      CALL SOLPOS (DAYNUMBER, YEAR, SINDEC, SCS)

      DO I=1,POINTS
        LATRAD=PI_OVER_180*LAT(I)
        LONGRAD(I)=PI_OVER_180*LONG(I)
        SINLAT(I)=SIN(LATRAD)
        COSZM(I)=0.0
      ENDDO

      COSDEC=SQRT(1-SINDEC**2)
      TANDEC=SINDEC/COSDEC
      TIMESTEP=86400.0/REAL(JDAY)

C----------------------------------------------------------------------
C Calculate the COSZ at each time
C----------------------------------------------------------------------
      DO J=1,JDAY

        TIME=(J-1)*TIMESTEP
        CALL SOLANG (SINDEC, TIME,
     &               TIMESTEP, SINLAT, LONGRAD, POINTS,
     &               LIT, COSZ)

        DO I=1,POINTS
          SUN(I,J)=COSZ(I)*LIT(I)
          COSZM(I)=COSZM(I)+SUN(I,J)/REAL(JDAY)
        ENDDO

      ENDDO

C----------------------------------------------------------------------
C Calculate the normalised solar radiation
C----------------------------------------------------------------------
      DO J=1,JDAY
        DO I=1,POINTS

          IF (COSZM(I) .GT. 0.0) THEN
            SUN(I,J)=SUN(I,J)/COSZM(I)
          ELSE
            SUN(I,J)=0.0
          ENDIF

        ENDDO
      ENDDO

C----------------------------------------------------------------------
C Calculate the time of maximum temperature. Assume this occurs 0.15
C of the daylength after local noon (guess !).
C----------------------------------------------------------------------
      DO I=1,POINTS

        COSLAT=SQRT(1-SINLAT(I)**2)
        TANLAT=SINLAT(I)/COSLAT
        TANTAN=TANLAT*TANDEC

        IF (ABS(TANTAN) .LE. 1.0) THEN      ! Sun sets and rises

          OMEGA_UP=-ACOS(-TANTAN)
          TIME_UP=0.5*24.0
     &           *((OMEGA_UP-LONGRAD(I))/PI+1)
          OMEGA_DOWN=ACOS(-TANTAN)
          TIME_DOWN=0.5*24.0
     &             *((OMEGA_DOWN-LONGRAD(I))/PI+1)

        ELSE                                ! Perpertual day or night
          TIME_UP=0.0
          TIME_DOWN=0.0

        ENDIF

        TIME_MAX(I) = 0.5*(TIME_UP+TIME_DOWN)
     &              + 0.15*(TIME_DOWN-TIME_UP)

      ENDDO

      RETURN
      END

C---------------------------------------------------------------------
CLL  Unified model deck SOLPOS, containing only routine SOLPOS.
CLL    This is part of logical component P233, performing the
CLL  calculations of the earth's orbit described in the first page of
CLL  the "Calculation of incoming insolation" section of UMDP 23, i.e.
CLL  from the day of the year (and, in forecast mode, whether it is a
CLL  leap year) and the orbital "constants" (which vary over
CLL  "Milankovitch" timescales) it calculates the sin of the solar
CLL  declination and the inverse-square scaling factor for the solar
CLL  "constant".  It is thus intrinsically scalar.  The FORTRAN code
CLL  present depends on whether *DEF CAL360 is set during UPDATE: this
CLL  replaces the Julian calendar with the climate-mode 360-day calendar
CLL    Written in FORTRAN 77, with the addition of "!" comments and
CLL  underscores in variable names.
CLL    Written to comply with 12/9/89 version of UMDP 4 (meteorological
CLL  standard).
CLL   Author:    William Ingram  22/3/89
CLL                      Reviewer: Clive Wilson Winter 1989/90
CLL  First version.
C*L
      SUBROUTINE  SOLPOS (DAY, YEAR, SINDEC, SCS)
      INTEGER!, INTENT(IN) ::
     &     DAY,                            !  Day-number in the year
     &     YEAR                            !  Calendar year
      REAL!, INTENT(OUT) ::
     &     SINDEC,                         !  sin(solar declination)
     &     SCS                             !  solar constant scaling
C*                                                            factor
CL This routine has no dynamically allocated work areas and no
CL  significant structure.  It calls the intrinsic functions FLOAT, SIN
CL  & COS, but no user functions or subroutines.
CL
      REAL GAMMA, E, TAU0, SINOBL,         ! Basic orbital constants
     &     TAU1, E1, E2, E3, E4,           ! Derived orbital constants
     &     TWOPI                           ! 2pi
      REAL DINY                            ! Number of days in the year
      REAL M, V                            ! Mean & true anomaly
      REAL PI,PI_OVER_180,RECIP_PI_OVER_180
      PARAMETER(
     & PI=3.1415926535879323846,! Pi
     & PI_OVER_180 =PI/180.0,   ! Conversion factor degrees to radians
     & RECIP_PI_OVER_180 = 180.0/PI ! Conversion factor radians to
     &                              ! degrees
     & )
C-----------------------------------------------------------------------
      PARAMETER ( TWOPI = 2. * PI )
      PARAMETER (GAMMA=1.352631, E=.0167,  ! Gamma, e
     &     TAU0 = 2.5,                     ! True date of perihelion
     &     SINOBL = .397789 )              ! Sin (obliquity)
      PARAMETER ( E1 = E * (2.-.25*E*E),
     &     E2 = 1.25 * E*E,                ! Coefficients for 3.1.2
     &     E3 = E*E*E * 13./12.,
     &     E4=( (1.+E*E*.5)/(1.-E*E) )**2 )! Constant for 3.1.4
      PARAMETER (DINY=360., TAU1=TAU0*DINY/365.25+0.71+.5)
C  In climate mode, DINY=360 always, and as well as applying 3.3.1,
C  TAU1 is modified so as to include the conversion of day-ordinal into
C  fractional-number-of-days-into-the-year-at-12-Z-on-this-day.
C
      M = TWOPI * (FLOAT(DAY)-TAU1) / DINY                    ! Eq 3.1.1
      V = M + E1*SIN(M) + E2*SIN(2.*M) + E3*SIN(3.*M)         ! Eq 3.1.2
      SCS = E4 * ( 1. + E * COS(V) ) **2                      ! Eq 3.1.4
      SINDEC = SINOBL * SIN (V - GAMMA)                       ! Eq 3.1.6
      RETURN
      END
CLL  Unified model deck SOLANG, containing only routine SOLANG.
CLL    This is part of logical component P233, performing the
CLL  calculations of the earth's orbit described in the second page of
CLL  the "Calculation of incoming insolation" section of UMDP 23, i.e.
CLL  from the sin of the solar  declination, the position of each point
CLL  and the time limits it calculates how much sunlight, if any, it
CLL  receives.
CLL    Written in FORTRAN 77 with the addition of "!" comments and
CLL  underscores in variable names.
CLL    Written to comply with 12/9/89 version of UMDP 4 (meteorological
CLL  standard).
CLL    Author:    William Ingram  21/3/89
CLL                      Reviewer: Clive Wilson Winter 1989/90
CLL  First version.
C*L
C
C*********************************************************************
C A01_2A selected for SCM use equivalent to frozen version
C physics 1/3/93 J.Lean
C*********************************************************************
C
      SUBROUTINE  SOLANG (SINDEC, T, DT, SINLAT, LONGIT, K,
     &     LIT, COSZ)
      INTEGER!, INTENT(IN) ::
     &     K                          ! Number of points
      REAL!, INTENT(IN) ::
     &     SINDEC,                    ! Sin(solar declination)
     &     T, DT,                     ! Start time (GMT) & timestep
     &     SINLAT(K),                 ! sin(latitude) & longitude
     &     LONGIT(K)                  ! of each point
      REAL!, INTENT(OUT) ::
     &     LIT(K),                    ! Sunlit fraction of the timestep
     &     COSZ(K)                    ! Mean cos(solar zenith angle)
C                                     ! during the sunlit fraction
C*
CL This routine has no dynamically allocated work areas.  It calls the
CL intrinsic functions SQRT, ACOS & SIN, but no user functions or
CL subroutines.  The only structure is a loop over all the points to be
CL dealt with, with IF blocks nested inside to cover the various
CL possibilities.
      INTEGER J                       ! Loop counter over points
      REAL TWOPI,                     ! 2*pi
     &     S2R                        ! Seconds-to-radians converter
      REAL SINSIN,            ! Products of the sines and of the cosines
     &     COSCOS,            ! of solar declination and of latitude.
     &     HLD,               ! Half-length of the day in radians (equal
     &                        ! to the hour-angle of sunset, and minus
     &     COSHLD,            ! the hour-angle of sunrise) & its cosine.
     &     HAT,               ! Local hour angle at the start time.
     &     OMEGAB,            ! Beginning and end of the timestep and
     &     OMEGAE,            ! of the period over which cosz is
     &     OMEGA1,            ! integrated, and sunset - all measured in
     &     OMEGA2,            ! radians after local sunrise, not from
     &     OMEGAS,            ! local noon as the true hour angle is.
     &     DIFSIN,            ! A difference-of-sines intermediate value
     &     DIFTIM,            ! and the corresponding time period
     &     TRAD, DTRAD
C     ! These are the start-time and length of the timestep (T & DT)
C     ! converted to radians after midday GMT, or equivalently, hour
C     ! angle of the sun on the Greenwich meridian.
      REAL PI,PI_OVER_180,RECIP_PI_OVER_180
      PARAMETER(
     & PI=3.1415926535879323846,! Pi
     & PI_OVER_180 =PI/180.0,   ! Conversion factor degrees to radians
     & RECIP_PI_OVER_180 = 180.0/PI ! Conversion factor radians to
     &                              ! degrees
     & )
C-----------------------------------------------------------------------
      PARAMETER ( TWOPI = 2. * PI, S2R = PI / 43200.)
C
      TRAD = T * S2R - PI
      DTRAD = DT * S2R
CDIR$ IVDEP
      DO 100 J = 1, K                          ! Loop over points
       HLD = 0.                                ! Logically unnecessary
C statement without which the CRAY compiler will not vectorize this code
       SINSIN = SINDEC * SINLAT(J)
       COSCOS = SQRT( (1.-SINDEC**2) * (1.-SINLAT(J)**2) )
       COSHLD = SINSIN / COSCOS
       IF (COSHLD.LT.-1.) THEN                 ! Perpetual night
          LIT(J) = 0.
          COSZ(J) = 0.
        ELSE
          HAT = LONGIT(J) + TRAD               ! (3.2.2)
          IF (COSHLD.GT.1.) THEN               !   Perpetual day - hour
             OMEGA1 = HAT                      ! angles for (3.2.3) are
             OMEGA2 = HAT + DTRAD              ! start & end of timestep
           ELSE                                !   At this latitude some
C points are sunlit, some not.  Different ones need different treatment.
             HLD = ACOS(-COSHLD)               ! (3.2.4)
C The logic seems simplest if one takes all "times" - actually hour
C angles - relative to sunrise (or sunset), but they must be kept in the
C range 0 to 2pi for the tests on their orders to work.
             OMEGAB = HAT + HLD
             IF (OMEGAB.LT.0.)   OMEGAB = OMEGAB + TWOPI
             IF (OMEGAB.GE.TWOPI) OMEGAB = OMEGAB - TWOPI
             IF (OMEGAB.GE.TWOPI) OMEGAB = OMEGAB - TWOPI
C            !  Line repeated - otherwise could have failure if
C            !  longitudes W are > pi rather than < 0.
             OMEGAE = OMEGAB + DTRAD
             IF (OMEGAE.GT.TWOPI) OMEGAE = OMEGAE - TWOPI
             OMEGAS = 2. * HLD
C Now that the start-time, end-time and sunset are set in terms of hour
C angle, can set the two hour-angles for (3.2.3).  The simple cases are
C start-to-end-of-timestep, start-to-sunset, sunrise-to-end and sunrise-
C -to-sunset, but two other cases exist and need special treatment.
             IF (OMEGAB.LE.OMEGAS .OR. OMEGAB.LT.OMEGAE) THEN
                OMEGA1 = OMEGAB - HLD
              ELSE
                OMEGA1 = - HLD
             ENDIF
             IF (OMEGAE.LE.OMEGAS) THEN
                OMEGA2 = OMEGAE - HLD
              ELSE
                OMEGA2 = OMEGAS - HLD
             ENDIF
             IF (OMEGAE.GT.OMEGAB.AND.OMEGAB.GT.OMEGAS) OMEGA2=OMEGA1
C  Put in an arbitrary marker for the case when the sun does not rise
C  during the timestep (though it is up elsewhere at this latitude).
C  (Cannot set COSZ & LIT within the ELSE ( COSHLD < 1 ) block
C  because 3.2.3 is done outside this block.)
          ENDIF           ! This finishes the ELSE (perpetual day) block
          DIFSIN = SIN(OMEGA2) - SIN(OMEGA1)             ! Begin (3.2.3)
          DIFTIM = OMEGA2 - OMEGA1
C Next, deal with the case where the sun sets and then rises again
C within the timestep.  There the integration has actually been done
C backwards over the night, and the resulting negative DIFSIN and DIFTIM
C must be combined with positive values representing the whole of the
C timestep to get the right answer, which combines contributions from
C the two separate daylit periods.  A simple analytic expression for the
C total sun throughout the day is used.  (This could of course be used
C alone at points where the sun rises and then sets within the timestep)
          IF (DIFTIM.LT.0.) THEN
            DIFSIN = DIFSIN + 2. * SQRT(1.-COSHLD**2)
            DIFTIM = DIFTIM + 2. * HLD
          ENDIF
          IF (DIFTIM.EQ.0.) THEN
C Pick up the arbitrary marker for night points at a partly-lit latitude
             COSZ(J) = 0.
             LIT(J) = 0.
           ELSE
             COSZ(J) = DIFSIN*COSCOS/DIFTIM + SINSIN     ! (3.2.3)
             LIT(J) = DIFTIM / DTRAD
          ENDIF
       ENDIF            ! This finishes the ELSE (perpetual night) block
  100 CONTINUE
      RETURN
      END


C**********************************************************************
C
C This routine calculates the random behaviour. Following the ITE
C model, the a random number generator is not called - instead,
C seed(1),..,seed(4) is updated.
C
C**********************************************************************

      SUBROUTINE RNDM(RANDOM_NUM,SEED)

      REAL
     & RANDOM_NUM          !OUT The random number.

      INTEGER
     & SEED(4)             !IN/OUT The seeding numbers
     &,I                   !WORK Integer

      SEED(4) = 3*SEED(4) + SEED(2)
      SEED(3) = 3*SEED(3) + SEED(1)
      SEED(2) = 3*SEED(2)
      SEED(1) = 3*SEED(1)

      I = INT(SEED(1)/1000.0)
      SEED(1) = SEED(1) - I*1000
      SEED(2) = SEED(2) + I
      I = INT(SEED(2)/100.0)
      SEED(2) = SEED(2) - 100*I
      SEED(3) = SEED(3) + I
      I = INT(SEED(3)/1000.0)
      SEED(3) = SEED(3) - I*1000
      SEED(4) = SEED(4) + I
      I = INT(SEED(4)/100.0)
      SEED(4) = SEED(4) - 100*I

      RANDOM_NUM = (((FLOAT(SEED(1))*0.001 + FLOAT(SEED(2)))*
     &             0.01 + FLOAT(SEED(3)))*0.001 + FLOAT(SEED(4)))*0.01

      RETURN
      END


      SUBROUTINE CLIM_CALC(ANOM,ANLG,GPOINTS,MM,MD,T_CLIM,SW_CLIM,
     &           LW_CLIM,PSTAR_HA_CLIM,RH15M_CLIM,RAINFALL_CLIM,
     &           SNOWFALL_CLIM,UWIND_CLIM,VWIND_CLIM,DTEMP_CLIM,
     &           F_WET_CLIM,
     &           T_ANOM,SW_ANOM,LW_ANOM,PSTAR_HA_ANOM,
     &           RH15M_ANOM,PRECIP_ANOM,UWIND_ANOM,
     &           VWIND_ANOM,DTEMP_ANOM,
     &           SW_OUT,T_OUT,LW_OUT,CONV_RAIN_OUT,CONV_SNOW_OUT,
     &           LS_RAIN_OUT,LS_SNOW_OUT,PSTAR_OUT,WIND_OUT,QHUM_OUT,
     &           DTEMP_OUT,NSDMAX,STEP_DAY,SEED_RAIN,SEC_DAY,LAT,LONG,MDI)

      IMPLICIT NONE

      INTEGER
     & IM,MM             !IN Monthly loop counter and number of months i
     &,MD                !WORK Number of days in (GCM) month
     &,STEP_DAY          !IN Number of daily timesteps of IMPACTS_MODEL
     &,ISTEP             !Looping parameter over suib-daily periods
     &,SEC_DAY           !WORK Number of seconds in each day
     &,NSDMAX            !IN Maximum number of possible subdaily
     &                   !increments
     &,L,J,K             !Loop parameters
     &,GPOINTS           !Number of points, not including Antartica
     &,SEED_RAIN(4)      !WORK Seeding number for subdaily
                         !rainfall.

      LOGICAL
     & ANLG              !IN If true, then use the GCM analogue model
     &,ANOM              !IN If true, then use the GCM analogue model

      REAL
     & T_ANOM(GPOINTS,MM)             !WORK Temperature anomalies fro
     &,PRECIP_ANOM(GPOINTS,MM)        !WORK Precip anomalies from AM
     &,RH15M_ANOM(GPOINTS,MM)         !WORK Relative humidity anomali
     &,UWIND_ANOM(GPOINTS,MM)         !WORK u-wind anomalies from AM
     &,VWIND_ANOM(GPOINTS,MM)         !WORK v-wind anomalies from AM
     &,DTEMP_ANOM(GPOINTS,MM)         !WORK Diurnal Temperature (K)
     &,PSTAR_HA_ANOM(GPOINTS,MM)      !WORK Pressure anomalies from A
     &,SW_ANOM(GPOINTS,MM)            !WORK Shortwave radiation anoma
     &,LW_ANOM(GPOINTS,MM)            !WORK Longwave radiation anomal
     &,LAT(GPOINTS)                      !WORK Latitudinal position of l
     &,LONG(GPOINTS)                     !WORK Longitudinal position of

C Driving "control" climatology
      REAL
     & T_CLIM(GPOINTS,MM)                !IN Control climate temperature
     &,RAINFALL_CLIM(GPOINTS,MM)         !IN Control climate rainfall (m
     &,SNOWFALL_CLIM(GPOINTS,MM)         !IN Control climate snowfall (m
     &,RH15M_CLIM(GPOINTS,MM)            !IN Control climate relative hu
     &,UWIND_CLIM(GPOINTS,MM)            !IN Control climate u-wind (m/s
     &,VWIND_CLIM(GPOINTS,MM)            !IN Control climate v-wind (m/s
     &,DTEMP_CLIM(GPOINTS,MM)            !IN Control climate diurnal Tem
     &,PSTAR_HA_CLIM(GPOINTS,MM)         !IN Control climate pressure (h
     &,SW_CLIM(GPOINTS,MM)               !IN Control climate shortwave r
     &,LW_CLIM(GPOINTS,MM)               !IN Control climate longwave ra
     &,F_WET_CLIM(GPOINTS,MM)            !IN Control climate fraction we

C Create "local" (in time) values of the arrays below
      REAL
     & T_OUT_LOCAL(GPOINTS,NSDMAX)          !WORK temperature (K)
     &,CONV_RAIN_OUT_LOCAL(GPOINTS,NSDMAX)  !WORK temperature (mm/day)
     &,LS_RAIN_OUT_LOCAL(GPOINTS,NSDMAX)    !WORK temperature (mm/day)
     &,LS_SNOW_OUT_LOCAL(GPOINTS,NSDMAX)    !WORK temperature (mm/day)
     &,QHUM_OUT_LOCAL(GPOINTS,NSDMAX)       !WORK humidity (kg/kg)
     &,WIND_OUT_LOCAL(GPOINTS,NSDMAX)       !WORK wind  (m/s)
     &,PSTAR_OUT_LOCAL(GPOINTS,NSDMAX)      !WORK pressure (Pa)
     &,SW_OUT_LOCAL(GPOINTS,NSDMAX)         !WORK shortwave radiation (W
     &,LW_OUT_LOCAL(GPOINTS,NSDMAX)         !WORK longwave radiation (W/

C Create fine temperal resolution year of climatology (to be used by imp
C studies or DGVMs).
      REAL
     & T_OUT(GPOINTS,MM,MD,NSDMAX)          !OUT Calculated temperature
     &,CONV_RAIN_OUT(GPOINTS,MM,MD,NSDMAX)  !OUT Calculated convective
C                                           !rainfall (mm/day)
     &,CONV_SNOW_OUT(GPOINTS,MM,MD,NSDMAX)  !OUT Calculated convective
C                                           !rainfall (mm/day)
     &,LS_RAIN_OUT(GPOINTS,MM,MD,NSDMAX)    !OUT Calculated large scale
C                                           !rainfall (mm/day)
     &,LS_SNOW_OUT(GPOINTS,MM,MD,NSDMAX)    !OUT Calculated large scale
C                                           !snowfall (mm/day)
     &,QHUM_OUT(GPOINTS,MM,MD,NSDMAX)       !OUT Calculated humidity (kg
     &,WIND_OUT(GPOINTS,MM,MD,NSDMAX)       !OUT Calculated wind  (m/s)
     &,PSTAR_OUT(GPOINTS,MM,MD,NSDMAX)      !OUT Calculated pressure (Pa
     &,SW_OUT(GPOINTS,MM,MD,NSDMAX)         !OUT Calculated shortwave ra
     &,LW_OUT(GPOINTS,MM,MD,NSDMAX)         !OUT Calculated longwave rad
     &,DTEMP_OUT(GPOINTS,MM,MD)             !OUT Calculated daily temperature range

C Variables for daily climatology
      REAL
     & T_DAILY(GPOINTS,MM,MD)            !WORK Calculated temperature (K
     &,PRECIP_DAILY(GPOINTS,MM,MD)       !WORK Calculated temperature (m
     &,QHUM_DAILY(GPOINTS,MM,MD)         !WORK Calculated humidity (g/kg
     &,UWIND_DAILY(GPOINTS,MM,MD)        !WORK Calculated "u"-wind  (m/s
     &,VWIND_DAILY(GPOINTS,MM,MD)        !WORK Calculated "v"-wind  (m/s
     &,WIND_DAILY(GPOINTS,MM,MD)         !WORK Calculated wind  (m/s)
     &,DTEMP_DAILY(GPOINTS,MM,MD)        !WORK Calculated diurnal Temper
     &,PSTAR_DAILY(GPOINTS,MM,MD)        !WORK Calculated pressure (Pa)
     &,SW_DAILY(GPOINTS,MM,MD)           !WORK Calculated shortwave radi
     &,LW_DAILY(GPOINTS,MM,MD)           !WORK Calculated longwave radia

C And "local" (in time) values of the DAILY variables.
      REAL
     & T_DAILY_LOCAL(GPOINTS)            !WORK Calculated temperature (K
     &,PRECIP_DAILY_LOCAL(GPOINTS)       !WORK Calculated temperature (m
     &,RH15M_DAILY_LOCAL(GPOINTS)        !WORK Calculated humidity (%)
     &,WIND_DAILY_LOCAL(GPOINTS)         !WORK Calculated wind  (m/s)
     &,DTEMP_DAILY_LOCAL(GPOINTS)        !WORK Calculated diurnal Temper
     &,PSTAR_DAILY_LOCAL(GPOINTS)        !WORK Calculated pressure (Pa)
     &,SW_DAILY_LOCAL(GPOINTS)           !WORK Calculated shortwave radi
     &,LW_DAILY_LOCAL(GPOINTS)           !WORK Calculated longwave radia

      REAL
     & RH15M_DAILY(GPOINTS,MM,MD)        !WORK Calculated relative humid
     &,QS                                !WORK Saturated humidity (kg/kg
     &,MDI                               !WORK Missing data indicator

      REAL
     & TLOCAL                            !WORK Local value of T_DAILY in
     &,PLOCAL                            !WORK Local value of PSTAR_DAIL

!NG---------------------------------------------------------------------
! Variables required to split rainfall up so that it rains roughly
! the correct no. of days/month when weather generator is switched off.

      INTEGER
     & NO_RAINDAY                ! WORK No. of rainy days in the month.
     &,INT_RAINDAY               ! WORK Rain day interval.
     &,IC_RAINDAY                ! WORK No. of rain days counter.
      REAL
     & TOT_RAIN                  ! WORK Total rain counter.

C      print *,'Top of CLIM_CALC'
!
! Calculate monthly means and add anomalies.
! Anomalies will be zero, if set ANOM=.F.

      DO J=1,MM                 !Loop over the months
         DO L=1,GPOINTS         !Loop over land points
            DO K=1,MD           !Loop over the days

              T_DAILY(L,J,K)=T_CLIM(L,J)+T_ANOM(L,J)
              SW_DAILY(L,J,K)=SW_CLIM(L,J)+SW_ANOM(L,J)
              RH15M_DAILY(L,J,K)=RH15M_CLIM(L,J)+RH15M_ANOM(L,J)
              DTEMP_DAILY(L,J,K)=DTEMP_CLIM(L,J)+DTEMP_ANOM(L,J)

              PRECIP_DAILY(L,J,K)=RAINFALL_CLIM(L,J)+
     &               SNOWFALL_CLIM(L,J)+PRECIP_ANOM(L,J)

C     Make sure precip anomalies do not produce negative rainfall
              PRECIP_DAILY(L,J,K) = MAX(PRECIP_DAILY(L,J,K),0.0)
C     Pressure (Pa)  ! Include unit conversion from HPa to Pa
              PSTAR_DAILY(L,J,K)=
     &              100.0*(PSTAR_HA_CLIM(L,J)+PSTAR_HA_ANOM(L,J))

C     Check on humidity bounds
              RH15M_DAILY(L,J,K)=MIN(RH15M_DAILY(L,J,K),100.0)
              RH15M_DAILY(L,J,K)=MAX(RH15M_DAILY(L,J,K),0.0)
C     Now convert humidity units into required (g/kg)
              TLOCAL=T_DAILY(L,J,K)
              PLOCAL=PSTAR_DAILY(L,J,K)

C     Check to make sure anomalies do not produce negative values
              DTEMP_DAILY(L,J,K) = MAX(DTEMP_DAILY(L,J,K),0.0)
C     Longwave radiation (W/m2)
              LW_DAILY(L,J,K)=LW_CLIM(L,J)+LW_ANOM(L,J)
C     Wind
              UWIND_DAILY(L,J,K)=UWIND_CLIM(L,J)+UWIND_ANOM(L,J)
              VWIND_DAILY(L,J,K)=VWIND_CLIM(L,J)+VWIND_ANOM(L,J)
              WIND_DAILY(L,J,K) = SQRT((UWIND_DAILY(L,J,K)**2) +
     &              (VWIND_DAILY(L,J,K)**2))
C     Check to make sure anomalies do not produce zero windspeed (ie
C     below measurement level).
              WIND_DAILY(L,J,K) = MAX(WIND_DAILY(L,J,K),0.01)
            ENDDO
         ENDDO
      ENDDO


C     Disaggregate down to sub-daily (ie TSTEP values)
C     This calls subroutine DAY_CALC which for each day converts values
C     "_daily" to "_out".

C     Variables going in (with units) are SW(W/m2), Precip (mm/day), Tem
C     (K), DTemp (K), LW (W/m2), PSTAR(Pa), Wind (m/2) and QHUM (kg/kg)

C     Variables coming out are subdaily estimates of above variables, ex
C     for DTEMP (which no longer has meaning), and temperature dependent
C     the splitting of precipitation back into LS_CONV, LS_SNOW and
C     Convective rainfall (there is no convective snow, and so below, th
C     set of have a zero value).

      DO J=1,MM                !Loop over the months
        DO K=1,MD              !Loop over the days
          DO L = 1,GPOINTS
            SW_DAILY_LOCAL(L) = SW_DAILY(L,J,K)
            PRECIP_DAILY_LOCAL(L) = PRECIP_DAILY(L,J,K)
            T_DAILY_LOCAL(L) = T_DAILY(L,J,K)
            DTEMP_DAILY_LOCAL(L) = DTEMP_DAILY(L,J,K)
            LW_DAILY_LOCAL(L) = LW_DAILY(L,J,K)
            PSTAR_DAILY_LOCAL(L) = PSTAR_DAILY(L,J,K)
            WIND_DAILY_LOCAL(L) = WIND_DAILY(L,J,K)
            RH15M_DAILY_LOCAL(L) = RH15M_DAILY(L,J,K)
          ENDDO

          CALL DAY_CALC(GPOINTS,STEP_DAY,MD,SW_DAILY_LOCAL,
     &         PRECIP_DAILY_LOCAL,T_DAILY_LOCAL,DTEMP_DAILY_LOCAL,
     &         LW_DAILY_LOCAL,PSTAR_DAILY_LOCAL,WIND_DAILY_LOCAL,
     &         RH15M_DAILY_LOCAL,
     &         SW_OUT_LOCAL,T_OUT_LOCAL,LW_OUT_LOCAL,
     &         CONV_RAIN_OUT_LOCAL,LS_RAIN_OUT_LOCAL,LS_SNOW_OUT_LOCAL,
     &         PSTAR_OUT_LOCAL,WIND_OUT_LOCAL,QHUM_OUT_LOCAL,J,K,
     &         LAT,LONG,SEC_DAY,NSDMAX,SEED_RAIN)

C Finalise value and set unused output values as MDI as a precaution.
          DO L = 1,GPOINTS
            DO ISTEP = 1,STEP_DAY
              SW_OUT(L,J,K,ISTEP) = SW_OUT_LOCAL(L,ISTEP)
              T_OUT(L,J,K,ISTEP) = T_OUT_LOCAL(L,ISTEP)
              LW_OUT(L,J,K,ISTEP) = LW_OUT_LOCAL(L,ISTEP)
              CONV_RAIN_OUT(L,J,K,ISTEP) = CONV_RAIN_OUT_LOCAL(L,ISTEP)
              CONV_SNOW_OUT(L,J,K,ISTEP) = 0.0
              LS_RAIN_OUT(L,J,K,ISTEP) = LS_RAIN_OUT_LOCAL(L,ISTEP)
              LS_SNOW_OUT(L,J,K,ISTEP) = LS_SNOW_OUT_LOCAL(L,ISTEP)
              PSTAR_OUT(L,J,K,ISTEP) = PSTAR_OUT_LOCAL(L,ISTEP)
              WIND_OUT(L,J,K,ISTEP) = WIND_OUT_LOCAL(L,ISTEP)
              QHUM_OUT(L,J,K,ISTEP) = QHUM_OUT_LOCAL(L,ISTEP)
            ENDDO

            DO ISTEP = STEP_DAY+1,NSDMAX
              SW_OUT(L,J,K,ISTEP) = MDI
              T_OUT(L,J,K,ISTEP) = MDI
              LW_OUT(L,J,K,ISTEP) = MDI
              CONV_RAIN_OUT(L,J,K,ISTEP) = MDI
              CONV_SNOW_OUT(L,J,K,ISTEP) = MDI
              LS_RAIN_OUT(L,J,K,ISTEP) = MDI
              LS_SNOW_OUT(L,J,K,ISTEP) = MDI
              PSTAR_OUT(L,J,K,ISTEP) = MDI
              WIND_OUT(L,J,K,ISTEP) = MDI
              QHUM_OUT(L,J,K,ISTEP) = MDI
            ENDDO
C           Also want a DTEMP output for LPJ-GUESS - TP 03.02.16
            DTEMP_OUT(L,J,K)=DTEMP_DAILY(L,J,K)
          ENDDO
        ENDDO                  !End of loop over days
      ENDDO                    !End of loop over months

      RETURN
      END

      SUBROUTINE DELTA_TEMP(N_OLEVS,
     &      F_OCEAN,KAPPA,LAMBDA_L,LAMBDA_O,MU,Q,DTEMP_L,DTEMP_O)

C-----------------------------------------------------------------------
C This subroutine calls a simple two-box
C thermal model in order to estimate
C the global mean land surface temperature.
C The code uses an implicit solver.
C C. Huntingford, 11/09/98.
C-----------------------------------------------------------------------

      IMPLICIT NONE

      INTEGER
     &N_OLEVS                 !IN Number of ocean thermal layers

      REAL
     &Q,                      !IN Increase in global
C                             !radiative forcing (W/m2)
     &LAMBDA_L,               !IN Inverse climate
C                             !sensitivity over land (W/K/m2)
     &LAMBDA_O,               !IN Inverse climate
C                             !sensitivity over ocean (W/K/m2)
     &MU,                     !IN Ratio of land-to-ocean
C                             !temperature anomalies (.)
     &F_OCEAN,                !IN Fractional coverage
C                             !of planet with ocean
     &KAPPA                   !IN Ocean eddy diffusivity (W/m/K)

      INTEGER
     &ITER_PER_YEAR,          !WORK Iterations per year
     &TIMESTEPS,              !WORK Number of iterations
C                             !per call to DELTA_TEMP
     &I,J                     !WORK Looping parameter

      PARAMETER(ITER_PER_YEAR = 20)

      REAL
     &DTEMP_L,                !OUT Land mean temperature anomaly
     &DTEMP_O(N_OLEVS)        !IN/OUT Land mean temperature anomaly

      REAL
     &RHOCP,                  !WORK Rho times cp
C                             !for the ocean (J/K/m3)
     &FLUX_TOP,               !WORK Flux into the top
C                             !of the ocean (W/m2)
     &FLUX_BOTTOM             !WORK Flux into the top
C                             !of the ocean (W/m2)

      REAL
     &DTIME,                  !WORK Timestep (s)
     &DZ(1:N_OLEVS),          !WORK Distance step (m)
     &SEC_YEAR                !WORK Seconds in a year (s)

      REAL
     &R1(1:N_OLEVS),          !WORK Mesh ratio
     &R2(1:N_OLEVS),          !WORK Mesh ratio
     &LAMBDA_OLD,             !WORK Inhomogenous component
C                             !in implicit scheme (/s)
     &LAMBDA_NEW,             !WORK Inhomogenous component
C                             !in implicit scheme (/s)
     &P                       !WORK ``Dirchlet'' part of mixed
C                             !bounday condition at ocean surface (/m)

      REAL
     &U_OLD(1:N_OLEVS),       !WORK Old ocean temperature anomalies
     &U_NEW(1:N_OLEVS)        !WORK New ocean temperature anomalies

      REAL
     &FACTOR_DEP,             !WORK Factor by which layers are changed
     &DEPTH,                  !WORK Cumulated depth of layers (m)
     &DZ_TOP                  !WORK Depth of the top layer (m)

      PARAMETER(RHOCP=4.04E6)
      PARAMETER(SEC_YEAR = 3.1536E7)
C-----------------------------------------------------------------------
C Set up parameters for the model
C-----------------------------------------------------------------------

      DTIME = SEC_YEAR/FLOAT(ITER_PER_YEAR)
      TIMESTEPS = ITER_PER_YEAR


C Here the variable depths are calculated, along with the "R" values

C The mesh is as follows
C
C      -------------            U(1)
C                  (This is the top layer, called TEM(0) at points)
C          R(1)
C
C      ------------             U(2)
C
C          R(2)
C
C
C           |
C           |
C          \ /
C
C      ------------             U(N_OLEVS) = 0.0

       DZ_TOP = 2.0
       DEPTH = 0.0
       DO I = 1,N_OLEVS
         FACTOR_DEP = 2.71828**(DEPTH/500.0)
         DZ(I) = DZ_TOP*FACTOR_DEP
         DEPTH = DEPTH + DZ(I)
       ENDDO

C Now arrange that the lowest depth (here DEPTH = U(N_OLEVS+1)) is at 50

       DZ_TOP = DZ_TOP * (5000.0/DEPTH)
       DO I = 1,N_OLEVS
         DZ(I) = DZ(I) * (5000.0/DEPTH)
       ENDDO

       R1(1) = (KAPPA/RHOCP)*(DTIME/(DZ_TOP*DZ_TOP))
       R2(1) = 0.0
       DO I = 2,N_OLEVS
         R1(I) = (KAPPA/RHOCP)*(DTIME/(DZ(I-1)*(DZ(I)+DZ(I-1))))
         R2(I) = (KAPPA/RHOCP)*(DTIME/(DZ(I)*(DZ(I)+DZ(I-1))))
       ENDDO

C Reset the new values of U_OLD for the start of this run.

      DO I = 1,N_OLEVS
        U_OLD(I) = DTEMP_O(I)
      ENDDO

      DO I = 1,TIMESTEPS

        LAMBDA_OLD = -Q/(KAPPA*F_OCEAN)
        LAMBDA_NEW = -Q/(KAPPA*F_OCEAN)

        P = ((1.0-F_OCEAN)*LAMBDA_L*MU)/(F_OCEAN*KAPPA)
     &    + (LAMBDA_O/KAPPA)

        CALL INVERT
     & (U_OLD,U_NEW,P,LAMBDA_OLD,LAMBDA_NEW,R1,R2,DZ_TOP,N_OLEVS)

C Now check that the flux out of the bottom is not too large.

        FLUX_TOP =  - 0.5*(KAPPA*LAMBDA_OLD*DTIME)
     &            -0.5*(KAPPA*LAMBDA_NEW*DTIME)
     &            -0.5*(P*KAPPA*U_OLD(1)*DTIME)
     &            -0.5*(P*KAPPA*U_NEW(1)*DTIME)
        FLUX_BOTTOM = (DTIME/(2.0*DZ(N_OLEVS)))*KAPPA*
     &              (U_OLD(N_OLEVS)+U_NEW(N_OLEVS))

        IF(ABS(FLUX_BOTTOM/(FLUX_TOP+0.0000001)).GT.0.01) THEN
          WRITE(6,*) 'Flux at bottom of the
     &    ocean is greater than 0.01 of top'
        ENDIF



C Set calculated values at now ``old'' values

        DO J = 1,N_OLEVS
          U_OLD(J) = U_NEW(J)
        ENDDO

      ENDDO

C At end of this model run, reset values of LAMBDA_L and LAMBDA_O

      DO J = 1,N_OLEVS
        DTEMP_O(J) = U_NEW(J)
      ENDDO
      DTEMP_L = MU*DTEMP_O(1)

      RETURN
      END

      SUBROUTINE INVERT
     & (U_OLD,U_NEW,P,LAMBDA_OLD,LAMBDA_NEW,R1,R2,DZ_TOP,N_OLEVS)

C This routine is designed to invert a tri-diagonal matrix
C and then test that all is OK.

C The matrix is of the form ``A u_new = B u_old + k''
C Matrix A and B are tri-diagonal

C The solution is du/dz - pu = lambda



      IMPLICIT NONE

      INTEGER               !IN Array size of matrix A etc.
     &N_OLEVS               !IN Number of layers in main routine above


      REAL
     &P,                    !IN P Value in mixed-boundary condition
     &LAMBDA_OLD,           !IN Lambda value at old timestep
     &LAMBDA_NEW,           !IN Lambda value at new timestep
     &R1(N_OLEVS),          !IN Mesh ratio
     &R2(N_OLEVS),          !IN Mesh ratio
     &DZ_TOP,               !IN Top layer mesh size
     &FACTOR,               !WORK Local dummy variable
     &DUMMY1,               !WORK Local dummy variable
     &DUMMY2                !WORK Local dummy variable

      REAL
     &A(N_OLEVS,N_OLEVS),   !WORK Matrix A
     &B(N_OLEVS,N_OLEVS),   !WORK Matrix B
     &K(N_OLEVS),           !WORK Matrix K
     &U_OLD(1:N_OLEVS),     !IN Old values of U
     &U_NEW(1:N_OLEVS)      !OUT New values of U

      REAL
     &A_L(N_OLEVS,N_OLEVS), !WORK A local working value of A - values ma
     &F_L(N_OLEVS)          !WORK Local working value of ``B u_old + k''


      INTEGER
     &I,J                   !WORK Looping parameters


C Set everything to zero in the first instance

      DO I = 1,N_OLEVS
        DO J = 1,N_OLEVS
          A(I,J) = 0.0
          B(I,J) = 0.0
          A_L(I,J) = 0.0
        ENDDO
        F_L(I) = 0.0
        K(I) = 0.0
      ENDDO


C Evaluate the values of A,B,K for the particular use here.

      A(1,1) = (1.0+R1(1)) + R1(1)*DZ_TOP*P
      A(1,2) = -R1(1)

      B(1,1) = (1.0-R1(1)) - R1(1)*DZ_TOP*P
      B(1,2) = R1(1)

      K(1) = -R1(1)*DZ_TOP*(LAMBDA_OLD + LAMBDA_NEW)

      DO I = 2,N_OLEVS-1
        A(I,I-1) = -R1(I)
        A(I,I) = 1.0+R1(I)+R2(I)
        A(I,I+1) = -R2(I)

        B(I,I-1) = R1(I)
        B(I,I) = 1.0-R1(I)-R2(I)
        B(I,I+1) = R2(I)
      ENDDO

      A(N_OLEVS,N_OLEVS-1) = -R1(N_OLEVS)
      A(N_OLEVS,N_OLEVS) = 1.0+R1(N_OLEVS)+R2(N_OLEVS)

      B(N_OLEVS,N_OLEVS-1) = R1(N_OLEVS)
      B(N_OLEVS,N_OLEVS) = 1.0-R1(N_OLEVS)-R2(N_OLEVS)


C First evaluate F_L (which is initially `` B u_old + k'')


      F_L(1) = B(1,1)*U_OLD(1) + B(1,2)*U_OLD(2) + K(1)

      DO I = 2,N_OLEVS-1
        F_L(I) = B(I,I-1)*U_OLD(I-1) + B(I,I)*U_OLD(I) +
     &           B(I,I+1)*U_OLD(I+1) + K(I)
      ENDDO

      F_L(N_OLEVS) = B(N_OLEVS,N_OLEVS-1)*U_OLD(N_OLEVS-1) +
     &       B(N_OLEVS,N_OLEVS)*U_OLD(N_OLEVS) + K(N_OLEVS)


C Now set A_L = A

      A_L(1,1) = A(1,1)
      A_L(1,2) = A(1,2)

      DO I = 2,N_OLEVS-1
        A_L(I,I-1) = A(I,I-1)
        A_L(I,I) = A(I,I)
        A_L(I,I+1) = A(I,I+1)
      ENDDO

      A_L(N_OLEVS,N_OLEVS-1) = A(N_OLEVS,N_OLEVS-1)
      A_L(N_OLEVS,N_OLEVS) = A(N_OLEVS,N_OLEVS)

C Now go through loops working back to find U_NEW(1)

      FACTOR = A_L(N_OLEVS-1,N_OLEVS)/A_L(N_OLEVS,N_OLEVS)
      A_L(N_OLEVS,N_OLEVS-1) = A_L(N_OLEVS,N_OLEVS-1) * FACTOR
      A_L(N_OLEVS,N_OLEVS) = A_L(N_OLEVS-1,N_OLEVS)
      F_L(N_OLEVS) = F_L(N_OLEVS) * FACTOR

      A_L(N_OLEVS-1,N_OLEVS-1) = A_L(N_OLEVS-1,N_OLEVS-1)
     &   - A_L(N_OLEVS,N_OLEVS-1)
      A_L(N_OLEVS-1,N_OLEVS) = 0.0
      F_L(N_OLEVS-1) = F_L(N_OLEVS-1) - F_L(N_OLEVS)


      DO I = N_OLEVS-1,2,-1

        FACTOR = A_L(I-1,I)/A_L(I,I)
        A_L(I,I-1) = A_L(I,I-1) * FACTOR
        A_L(I,I) = A_L(I-1,I)
        F_L(I) = F_L(I) * FACTOR

        A_L(I-1,I-1) = A_L(I-1,I-1) - A_L(I,I-1)
        A_L(I-1,I) = 0.0
        F_L(I-1) = F_L(I-1) - F_L(I)

      ENDDO

C Now explicitly calculate the U_NEW values

      U_NEW(1) = F_L(1)/A_L(1,1)

      DO I = 2,N_OLEVS

        U_NEW(I) = (F_L(I) - (A_L(I,I-1)*U_NEW(I-1)))/A_L(I,I)

      ENDDO

C Now perform a check

      DO I = 1,N_OLEVS
        DUMMY1 = 0.0
        DUMMY2 = 0.0
        DO J = 1,N_OLEVS
          DUMMY1 = DUMMY1 + A(I,J)*U_NEW(J)
          DUMMY2 = DUMMY2 + B(I,J)*U_OLD(J)
        ENDDO
        DUMMY2 = DUMMY2 + K(I)

        IF(ABS(DUMMY1-DUMMY2).GE.0.0001) THEN
          PRINT *,'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
          STOP
        ENDIF
      ENDDO


      RETURN
      END

!-----------------------------------------------------------------------
! GCM ANALOGUE Model     (C.Huntingford, P.Cox, 9/98)
! Simplified 3/04 to supply just the anomalies for change in radiative
! forcing. CO2 scenarios etc are calculated outside this routine.
!-----------------------------------------------------------------------
      SUBROUTINE GCM_ANLG(Q,LAND_PTS,T_ANOM_AM,PRECIP_ANOM_AM,
     &     RH15M_ANOM_AM,UWIND_ANOM_AM,VWIND_ANOM_AM,DTEMP_ANOM_AM,
     &     PSTAR_HA_ANOM_AM,SW_ANOM_AM,LW_ANOM_AM,
     &     N_OLEVS,DIR_PATT,F_OCEAN,KAPPA_O,LAMBDA_L,LAMBDA_O,MU,
     &     DTEMP_O,LONGMIN_AM,LATMIN_AM,
     &     LONGMAX_AM,LATMAX_AM,MM)

      IMPLICIT NONE

      INTEGER
     & LAND_PTS                  ! IN Number of land points.
     &,IM                        ! IN Loop over months
     &,N_OLEVS                   ! IN Number of ocean thermal layers.
     &,MM                        ! In Number of months in a year

      CHARACTER*180
     & DIR_PATT                  ! IN Directory containing anomaly
!                                !    patterns.
     &,DRIVER_PATT               ! WORK File containing anomaly
!                                ! patterns from analogue model.
      CHARACTER*4
     & DRIVE_MONTH(12)           ! WORK Labels for month of driving
!                                !      data.

      REAL
     & LAT_AM(LAND_PTS)          !Latitude read from file.
     &,LONG_AM(LAND_PTS)         !Longitude read from file.

!-----------------------------------------------------------------------
! Climatological forcing variables.
!-----------------------------------------------------------------------
      REAL
     & F_OCEAN                   ! IN Fractional coverage of the ocean.
     &,KAPPA_O                   ! IN Ocean eddy diffusivity (W/m/K).
     &,LAMBDA_L                  ! IN Inverse climate sensitivity over
!                                !    land (W/m2/K).
     &,LAMBDA_O                  ! IN Inverse climate sensitivity over
!                                !    ocean (W/m2/K).
     &,MU                        ! IN Ratio of land to ocean
!                                ! temperature anomalies.
     &,DTEMP_O(N_OLEVS)          ! INOUT Ocean mean
C                                ! temperature anomaly (K).
     &,DTEMP_L                   ! OUT Land mean
C                                ! temperature anomaly (K).
     &,DTEMP_ANOM_AM(LAND_PTS,MM)   ! OUT Diurnal temperature range (K).
     &,LW_ANOM_AM(LAND_PTS,MM)      ! OUT Downward surface longwave
!                                   !     radiation anomaly (W/m).
     &,RAINFALL_ANOM_AM(LAND_PTS,MM)! OUT Rainfall rate anomaly (mm/day)
     &,RH15M_ANOM_AM(LAND_PTS,MM)   ! OUT Relative humidity at 1.5m anom
     &,SNOWFALL_ANOM_AM(LAND_PTS,MM)! OUT Snowfall rate anomaly (mm/day)
     &,SW_ANOM_AM(LAND_PTS,MM)      ! OUT Downward surface shortwave
!                                   ! radiation anomaly (W/m2).
     &,T_ANOM_AM(LAND_PTS,MM)       ! OUT Air temperature anomaly (K).
     &,PRECIP_ANOM_AM(LAND_PTS,MM)  ! OUT Precipitation (snowfall
C                                   ! plus rainfall) anomaly (mm/day)
     &,UWIND_ANOM_AM(LAND_PTS,MM)   ! OUT Wind speed anomaly (m/s).
     &,VWIND_ANOM_AM(LAND_PTS,MM)   ! OUT Wind speed anomaly (m/s).
     &,LATMIN_AM,LATMAX_AM       ! WORK Latitudinal limits of the area
!                                !      (degrees).
     &,LONGMIN_AM,LONGMAX_AM     ! WORK Longitudinal limits of the area
!                                !      (degrees).
     &,PSTAR_HA_ANOM_AM(LAND_PTS,MM)! OUT Surface pressure (hPa).
     &,Q                         ! WORK Increase in radiative forcing
!                                !      (W/m2).
     &,UWIND,VWIND               ! WORK Windspeed components (m/s).

!-----------------------------------------------------------------------
! Anomaly patterns scaled to land mean temperature anomalies.
!-----------------------------------------------------------------------
      REAL
     & DDTEMP_DAY_PAT            ! WORK Diurnal temperature range (.).
     &,DLW_C_PAT                 ! WORK Downward surface longwave
!                                !      radiation (W/m2/K).
     &,DPSTAR_C_PAT              ! WORK Surface pressure (hPa/K).
     &,DRAINFALL_PAT             ! WORK Rainfall rate (mm/day/K).
     &,DRH15M_PAT                ! WORK Relative humidity at 1.5m (%/K).
     &,DSNOWFALL_PAT             ! WORK Snowfall rate (mm/day/K).
     &,DSW_C_PAT                 ! WORK Surface shortwave radiation
!                                !      (W/m2/K).
     &,DT_C_PAT                  ! WORK Air temperature (.).
     &,DUWIND_PAT,DVWIND_PAT     ! WORK Windspeed components (m/s/K).

!-----------------------------------------------------------------------
! Loop counters.
!-----------------------------------------------------------------------
      INTEGER
     & I,L,II,II_CLIM,K ! WORK

      DATA DRIVE_MONTH / '/jan','/feb','/mar','/apr','/may','/jun',
     &                   '/jul','/aug','/sep','/oct','/nov','/dec' /

!-----------------------------------------------------------------------
! Loop over months
!-----------------------------------------------------------------------

      DO IM=1,MM
!-----------------------------------------------------------------------
! Calculate new area mean temperature anomalies
!-----------------------------------------------------------------------
        IF (IM.EQ.1) THEN
          CALL DELTA_TEMP (N_OLEVS
     &,           F_OCEAN,KAPPA_O,LAMBDA_L,LAMBDA_O,MU,Q
     &,           DTEMP_L,DTEMP_O)

        ENDIF

!-----------------------------------------------------------------------
! Define the anomaly patterns and read the header
!-----------------------------------------------------------------------
        DO I=1,LEN(DIR_PATT)
          IF (DIR_PATT(I:I) .NE. ' ') II=I
        ENDDO

        DRIVER_PATT=DIR_PATT(:II)//DRIVE_MONTH(IM)
        WRITE(6,*) DRIVER_PATT
        OPEN(51,FILE=DRIVER_PATT,STATUS='OLD')
        READ(51,*) LONGMIN_AM,LATMIN_AM,LONGMAX_AM,LATMAX_AM
        print *,'DTEMP_L = ',DTEMP_L

!-----------------------------------------------------------------------
! Read in initial climatology and then define the new climate data.
!-----------------------------------------------------------------------
        DO L=1,LAND_PTS
          READ(51,*)LONG_AM(L),LAT_AM(L),DT_C_PAT,DRH15M_PAT
     &,       DUWIND_PAT,DVWIND_PAT
     &,       DLW_C_PAT,DSW_C_PAT
     &,       DDTEMP_DAY_PAT,DRAINFALL_PAT
     &,       DSNOWFALL_PAT,DPSTAR_C_PAT

          T_ANOM_AM(L,IM) = DT_C_PAT * DTEMP_L
          RH15M_ANOM_AM(L,IM) = DRH15M_PAT * DTEMP_L
          UWIND_ANOM_AM(L,IM) = DUWIND_PAT * DTEMP_L
          VWIND_ANOM_AM(L,IM) = DVWIND_PAT * DTEMP_L
          RAINFALL_ANOM_AM(L,IM) = DRAINFALL_PAT * DTEMP_L
          SNOWFALL_ANOM_AM(L,IM) = DSNOWFALL_PAT * DTEMP_L
          DTEMP_ANOM_AM(L,IM) = DDTEMP_DAY_PAT * DTEMP_L
          LW_ANOM_AM(L,IM) = DLW_C_PAT * DTEMP_L
          SW_ANOM_AM(L,IM) = DSW_C_PAT * DTEMP_L
          PSTAR_HA_ANOM_AM(L,IM) = DPSTAR_C_PAT * DTEMP_L

          PRECIP_ANOM_AM(L,IM) = RAINFALL_ANOM_AM(L,IM) +
     &                           SNOWFALL_ANOM_AM(L,IM)

        ENDDO     !End of loop over land points
      ENDDO     !End of loop over months

      CLOSE(51)
      RETURN
      END

      SUBROUTINE OCEAN_CO2
     &(IYEAR,YEAR_CO2,CO2_ATMOS_PPMV,CO2_ATMOS_INIT_PPMV,DT_OCEAN,
     & FA_OCEAN,OCEAN_AREA,
     & GRAD_CO2_ATMOS_PPMV,YEAR_RUN,T_OCEAN_INIT,NFARRAY,
     & D_OCEAN_ATMOS)

C-----------------------------------------------------------------------
C This subroutine describes a simple uptake
C by the oceans of atmospheric CO2
C The work is based upon the paper by Joos.

C The parameters chosen replicate those of the 3-D model, see
C Table 2 of Joos et al.
C-----------------------------------------------------------------------

C Huntingford and Cox (March 1999)

      IMPLICIT NONE

      INTEGER
     & I                  !WORK Looping counter
     &,J                  !WORK Looping counter
     &,ISTEP              !IN Looping counter from main subroutine that
                          !shows calls to Joos model
     &,IYEAR              !IN Years since start of run
     &,YEAR_CO2           !IN Years between updated atmospheric
                          !CO2 concentration (yr)
     &,NCALLYR            !IN Number of calls per year the ocean routine
                          !(with CO2 conc. fixed)
     &,YEAR_RUN           !IN Number of years in simulation (yr)
     &,NFARRAY            !IN Array size for FA_OCEAN

      PARAMETER(NCALLYR=20)

      REAL
     & DT_OCEAN           !IN Mixed-layer temperature anomaly (K)
     &,CO2_ATMOS_PPMV     !WORK Atmospheric CO2 concentation during
                          !period YEAR_CO2 (ppm)
     &,CO2_ATMOS_SHORT    !WORK Atmospheric CO2 concentation on the
C                         !shortime (1/NCALLYR) timescale (ppm)
     &,CO2_ATMOS_INIT_PPMV     !WORK Initial atmospheric concentration (
     &,DCO2_ATMOS         !WORK Perturbation in atmospheric
C                         !concentration (ppm)
     &,TIMESTEP_CO2           !WORK Timestep (yr)
     &,RS(YEAR_RUN*NCALLYR)  !WORK Response function values
     &,GRAD_CO2_ATMOS_PPMV        !IN Gradient of atmospheric CO2 (ppm/y
                                  !during YEAR_CO2 period


      REAL
     & FA_OCEAN(NFARRAY)  !IN/OUT CO2 fluxes
                          !from the atmosphere to
C                         !the ocean (ie positive downwards) (ppm/m2/yr)
     &,DCO2_OCEAN         !IN/OUT Carbon dioxide concentration
C                         !perturbation in mixed-layer (ppm)
     &,CO2_OCEAN          !OUT Carbon dioxide concentration
                          !in mixed-layer (ppm)
     &,CO2_OCEAN_INIT     !OUT Initial ocean carbon dioxide
                          !concentration (ppm)
     &,DCO2_OCEAN_MOL     !WORK Carbon dioxide concentration
C                         !perturbation of mixed-layer (umol/kg)
     &,T_MIXED_INIT       !WORK Initial global mean ocean
                          !surface temperature (C)
     &,T_OCEAN_INIT       !IN Initial global surface temperature
                          !of the ocean (K)
     &,H                  !WORK Mixed-layer depth (m)
     &,K_G                !WORK Gas exchange coefficient (/m2/yr)
     &,C                  !WORK Units conversion parameter (umol m3/ppm/
     &,OCEAN_AREA         !WORK Ocean area (m2)

      REAL
     & D_OCEAN_ATMOS      ! OUT Change in atmospheric CO2 concentration
                          ! a result of ocean-atmosphere feedbacks between
                          ! calls to SCENARIO (ppm/"YEAR_CO2")

      DATA K_G/0.1306/
      DATA H/40.0/
      DATA C/1.722E17/

      IF(YEAR_RUN*NCALLYR.GT.NFARRAY) THEN
        PRINT *,'Array size too small for FA_OCEAN'
      ENDIF

      CALL RESPONSE(NCALLYR,YEAR_RUN,RS)

      D_OCEAN_ATMOS = 0.0

C-----------------------------------------------------------------------
C Assume initial mixed-layer temperature identical to diagnosed global
C surface temperature.
C-----------------------------------------------------------------------

      T_MIXED_INIT= T_OCEAN_INIT - 273.15

      TIMESTEP_CO2 = 1.0/FLOAT(NCALLYR)

      DO J = 1,NCALLYR*YEAR_CO2         !Loops internally within the model.
C                                       !to cover iterations
C                                       !within period YEAR_CO2

        ISTEP = ((IYEAR-YEAR_CO2)*NCALLYR)+J
C                             !ISTEP is the integer that indexes calcula
C                             !using the Joos model. Recall this subrout
C                             !is called at end of period YEAR_CO2

        CO2_OCEAN_INIT = CO2_ATMOS_INIT_PPMV           !Assume starting
                                                       !from equilibrium.

C-----------------------------------------------------------------------
C Introduce linear correction in atmospheric CO2 concentration
C down to timescale 1/NCALLYR
C-----------------------------------------------------------------------

        CO2_ATMOS_SHORT = CO2_ATMOS_PPMV +
     &  GRAD_CO2_ATMOS_PPMV *
     &  ((FLOAT(J)/FLOAT(NCALLYR))-0.5*FLOAT(YEAR_CO2))

        DCO2_ATMOS = CO2_ATMOS_SHORT-CO2_ATMOS_INIT_PPMV

C-----------------------------------------------------------------------
C Calculate perturbation in dissolved inorganic carbon (Eqn (3) of Joos)
C for timestep indexed by ISTEP.
C-----------------------------------------------------------------------

        DCO2_OCEAN_MOL = 0.0 !Initialised for loop

        IF(ISTEP.GE.2) THEN
          DO I = 1,ISTEP-1
            DCO2_OCEAN_MOL = DCO2_OCEAN_MOL +
     &     (C/H)*FA_OCEAN(I)*RS(ISTEP-I)*TIMESTEP_CO2
          ENDDO
        ENDIF

C----------------------------------------------------------------------
C Relation between DCO2_OCEAN_MOL and DCO2_OCEAN:   Joos et al.
C ie Convert from umol/kg to ppm
C----------------------------------------------------------------------

        DCO2_OCEAN =
     &   (1.5568-(1.3993*1.0E-2*T_MIXED_INIT))*DCO2_OCEAN_MOL
     & + (7.4706-(0.20207*T_MIXED_INIT))*1.0E-3*(DCO2_OCEAN_MOL**2)
     & - (1.2748-(0.12015*T_MIXED_INIT))*1.0E-5*(DCO2_OCEAN_MOL**3)
     & + (2.4491-(0.12639*T_MIXED_INIT))*1.0E-7*(DCO2_OCEAN_MOL**4)
     & - (1.5468-(0.15326*T_MIXED_INIT))*1.0E-10*(DCO2_OCEAN_MOL**5)

C----------------------------------------------------------------------
C Now incorporate correction suggested by Joos
C----------------------------------------------------------------------

        CO2_OCEAN = CO2_OCEAN_INIT + DCO2_OCEAN
        CO2_OCEAN = CO2_OCEAN * EXP(0.0423*DT_OCEAN)

        FA_OCEAN(ISTEP) =
     &        (K_G/OCEAN_AREA)*(CO2_ATMOS_SHORT-CO2_OCEAN)


C----------------------------------------------------------------------
C Now calculate D_OCEAN_ATMOS (D_OCEAN_ATMOS is positive when
C flux is upwards)
C----------------------------------------------------------------------

         D_OCEAN_ATMOS = D_OCEAN_ATMOS -
     &         FA_OCEAN(ISTEP)*OCEAN_AREA*TIMESTEP_CO2

      ENDDO

      RETURN
      END

      SUBROUTINE RESPONSE(NCALLYR,YEAR_RUN,RS)

      IMPLICIT NONE

      INTEGER
     & I                      !WORK looping parameter
     &,YEAR_RUN                 !IN Number of years in the simulation
     &,NCALLYR                !IN Number of calls per year to the
C                             !ocean routine (with CO2 conc. fixed)

      REAL
     & TIME_RS                !IN Time delay required by
C                             !the response function (yr)
     &,RS(NCALLYR*YEAR_RUN)   !OUT Value of the response function (.)


      DO I = 1,NCALLYR*YEAR_RUN
        TIME_RS = FLOAT(I)/FLOAT(NCALLYR)
        IF(TIME_RS.GE.1.0) THEN
          RS(I) = 0.014819 + 0.70367*EXP(-TIME_RS/0.70177)
     &   +0.24966*EXP(-TIME_RS/2.3488) + 0.066485*EXP(-TIME_RS/15.281)
     &   +0.038344*EXP(-TIME_RS/65.359)+0.019439*EXP(-TIME_RS/347.55)
        ELSE
          RS(I) = 1.0-2.2617*TIME_RS + 14.002*(TIME_RS**2)
     &       -48.770*(TIME_RS**3) + 82.986*(TIME_RS**4)
     &       -67.527*(TIME_RS**5) + 21.037*(TIME_RS**6)
        ENDIF
      ENDDO

      RETURN
      END

C**********************************************************************
C Calculates the radiative forcing due to a given CO2 concentration
C
C Written by Peter Cox (August 1998)
C**********************************************************************
      SUBROUTINE RADF_CO2 (CO2,CO2REF,Q2CO2,Q_CO2)

      IMPLICIT NONE


      REAL
     & CO2                  ! IN CO2 concentration (ppmv).
     &,CO2REF               ! IN Reference CO2 concentration (ppmv).
     &,Q2CO2                ! IN Radiative forcing due to doubling
C                           !    CO2 (W/m2).
     &,Q_CO2                ! OUT Radiative forcing due to CO2 (W/m2).

      Q_CO2=(Q2CO2/(LOG(2.0)))*LOG(CO2/CO2REF)

      RETURN
      END
C**********************************************************************
C Calculates the radiative forcing due to non-CO2 GHGs. This version
C is consistent with the HadCM3 GHG run (AAXZE).
C
C Written by Peter Cox (Sept 1998)
C Adjusted by Chris Huntingford (Dec 1999) to include
C other scenarios copied from file.
C**********************************************************************
      SUBROUTINE RADF_NON_CO2 (YEAR,Q,
     &       NYR_NON_CO2,FILE_NON_CO2,FILE_NON_CO2_VALS)

      IMPLICIT NONE

      INTEGER
     + YEAR                ! IN Julian year.
     +,I                   ! WORK Loop counter.
     +,NYR_NON_CO2         ! IN Number of years
                           ! for which NON_CO2
                           ! forcing is prescribed.
      CHARACTER*180
     + FILE_NON_CO2_VALS   ! IN File of non-co2 radiative forcings

      LOGICAL
     + FILE_NON_CO2        ! .T. if non_co2 forcings are read in from
                           ! a data file

      REAL
     + Q                   ! OUT non-CO2 radiative forcing (W/m2).

C-----------------------------------------------------------------------
C Local parameters
C-----------------------------------------------------------------------

      INTEGER
     + YEARS(300)          ! Years for which radiative is
C                          ! prescribed.
      REAL
     + Q_NON_CO2(300)      ! Specified radiative forcings (W/m2).
     +,GROWTH_RATE         ! Growth rate in the forcing after the
C                          ! last prescribed value (%/pa).
      PARAMETER (GROWTH_RATE=0.0)

      IF(.NOT.FILE_NON_CO2.AND.NYR_NON_CO2.NE.21) THEN
        PRINT *,'Reset value of NYR_NON_CO2'
        STOP
      ENDIF

      IF(NYR_NON_CO2.GT.300) THEN
        PRINT *,'NYR_NON_CO2 too large'
        STOP
      ENDIF

      DATA YEARS   / 1859,  1875,  1890,  1900,  1917
     &,              1935,  1950,  1960,  1970,  1980
     &,              1990,  2005,  2020,  2030,  2040
     &,              2050,  2060,  2070,  2080,  2090
     &,              2100, 279*2100 /

      DATA Q_NON_CO2/ 0.0344,0.0557,0.0754,0.0912,0.1176
     &,               0.1483,0.1831,0.2387,0.3480,0.4987
     &,               0.6627,0.8430,0.9225,0.9763,1.0575
     &,               1.1486,1.2316,1.3025,1.3604,1.4102
     &,               1.4602,279*1.4602 /


!-----------------------------------------------------------------------
! File of non-co2 forcings read in if required
!-----------------------------------------------------------------------

      IF(FILE_NON_CO2) THEN
        OPEN(72,FILE=FILE_NON_CO2_VALS,STATUS='OLD')
        DO I = 1,NYR_NON_CO2
          READ(72,*) YEARS(I),Q_NON_CO2(I)
        ENDDO
        CLOSE(72)
      ENDIF

!-----------------------------------------------------------------------
! Now calculate the non_co2 forcing
!-----------------------------------------------------------------------

      IF (YEAR.LT.YEARS(1)) THEN
        !If year is before 1859 or first data in FILE_NON_CO2 then set non-CO2 radiative forcing to zero
        Q = 0.0

      ELSEIF (YEAR.GT.YEARS(NYR_NON_CO2)) THEN

        Q = Q_NON_CO2(NYR_NON_CO2)
     &    *((1.0+0.01*GROWTH_RATE)**(YEAR-YEARS(NYR_NON_CO2)))

      ELSE

        DO I=1,NYR_NON_CO2-1
          IF ((YEAR.GE.YEARS(I)) .AND. (YEAR.LE.YEARS(I+1))) THEN
            Q = Q_NON_CO2(I) + (YEAR-YEARS(I))
     &         * (Q_NON_CO2(I+1)-Q_NON_CO2(I))/ (YEARS(I+1)-YEARS(I))
          ENDIF
        ENDDO

      ENDIF

      RETURN
      END


CLL  SUBROUTINE QSAT---------------------------------------------------
CLL
CLL  PURPOSE : RETURNS A SATURATION MIXING RATIO GIVEN
CLL            A TEMPERATURE AND PRESSURE USING SATURATION
CLL            VAPOUR PRESSURES CALCULATED USING THE
CLL            GOFF-GRATCH FORMULAE, ADOPTED BY THE WMO AS
CLL            TAKEN FROM LANDOLT-BORNSTEIN, 1987 NUMERICAL
CLL            DATA AND FUNCTIONAL RELATIONSHIPS IN SCIENCE
CLL            AND TECHNOLOGY. GROUP V/VOL 4B METEOROLOGY.
CLL            PHYSICAL AND CHEMICAL PROPERTIES OF AIR, P35
CLL
CLL            VALUES IN THE LOOKUP TABLE ARE OVER WATER ABOVE
CLL            0 DEG C AND OVER ICE BELOW THIS TEMPERATURE
CLL
CLL  SUITABLE FOR SINGLE COLUMN MODEL USE
CLL
CLL  CODE REWORKED FOR CRAY Y-MP BY D.GREGORY AUTUMN/WINTER 1989/90
CLL
CLL  MODEL            MODIFICATION HISTORY:
CLL VERSION  DATE
CLL  4.5   25/06/98  Correct potential failure introduced by optimising:
CLL                  Extend lookup array from (1:) to (0:) to cater for
CLL                  special case of extreme low temperatures
CLL                  (.LE.T_LOW) for which the array index is rounded
CLL                  down due to machine precision. R.Rawlins
CLL
CLL  PROGRAMMING STANDARDS :
CLL
CLL  LOGICAL COMPONENTS COVERED:
CLL
CLL  LOGICAL COMPONENTS COVERED: P27
CLL
CLL  DOCUMENTATION :
CLL
CLLEND-----------------------------------------------------------------
C
C*L  ARGUMENTS---------------------------------------------------------
C
      SUBROUTINE QSAT (QS,T,P,NPNTS)
C
      IMPLICIT NONE
C
C----------------------------------------------------------------------
C MODEL CONSTANTS
C----------------------------------------------------------------------
C
C*L------------------COMDECK C_EPSLON-----------------------------------
C EPSILON IS RATIO OF MOLECULAR WEIGHTS OF WATER AND DRY AIR
      REAL EPSILON,C_VIRTUAL

      PARAMETER(EPSILON=0.62198,
     &          C_VIRTUAL=1./EPSILON-1.)
C*----------------------------------------------------------------------

C*L------------------COMDECK C_O_DG_C-----------------------------------
C ZERODEGC IS CONVERSION BETWEEN DEGREES CELSIUS AND KELVIN
C TFS IS TEMPERATURE AT WHICH SEA WATER FREEZES
C TM IS TEMPERATURE AT WHICH FRESH WATER FREEZES AND ICE MELTS
      REAL ZERODEGC,TFS,TM

      PARAMETER(ZERODEGC=273.15,
     &          TFS=271.35,
     &          TM=273.15)
C*----------------------------------------------------------------------

C
C----------------------------------------------------------------------
C LOCAL CONSTANTS
C----------------------------------------------------------------------
C
      REAL T_LOW           ! LOWEST TEMPERATURE FOR WHICH LOOK-UP
                           ! TABLE OF SATURATION WATER VAPOUR
                           ! PRESSURE IS VALID (K)
C
      REAL T_HIGH          ! HIGHEST TEMPERATURE FOR WHICH LOOK-UP
                           ! TABLE OF SATURATION WATER VAPOUR
                           ! PRESSURES IS VALID (K)
C
      REAL DELTA_T         ! TEMPERATURE INCREMENT OF THE LOOK-UP
                           ! TABLE OF SATURATION VAPOUR PRESSURES
C
      INTEGER N            ! SIZE OF LOOK-UP TABLE OF SATURATION
                           ! WATER VAPOUR PRESSURES
C
      PARAMETER ( T_LOW = 183.15,
     *            T_HIGH = 338.15,
     *            DELTA_T = 0.1,
     *            N = INT(((T_HIGH - T_LOW + (DELTA_T*0.5))/DELTA_T) + 1.0)
     *          )    ! gives N=1551
C
C
C----------------------------------------------------------------------
C VECTOR LENGTHS AND LOOP COUNTERS
C----------------------------------------------------------------------
C
      INTEGER NPNTS        ! VECTOR LENGTH
C
      INTEGER I            ! LOOP COUNTER
C
      INTEGER IES          ! LOOP COUNTER FOR DATA STATEMENT
                           ! LOOK-UP TABLE
      INTEGER UNIT_NO
C
C
C----------------------------------------------------------------------
C VARIABLES WHICH ARE INPUT
C----------------------------------------------------------------------
C
      REAL T(NPNTS)        ! IN TEMPERATURE (K)
C
      REAL P(NPNTS)        ! IN PRESSURE (PA)
C
C
C----------------------------------------------------------------------
C VARIABLES WHICH ARE OUTPUT
C----------------------------------------------------------------------
C
      REAL QS(NPNTS)       ! OUT SATURATION MIXING RATIO AT TEMPERATURE
                           !     T AND PRESSURE P (KG/KG)
C
C
C----------------------------------------------------------------------
C VARIABLES WHICH ARE DEFINED LOCALLY
C----------------------------------------------------------------------
C
      REAL ES(0:N+1)         ! TABLE OF SATURATION WATER VAPOUR
                           ! PRESSURE (PA) - SET BY DATA STATEMENT
                           ! CALCULATED FROM THE GOFF-GRATCH FORMULAE
                           ! AS TAKEN FROM LANDOLT-BORNSTEIN, 1987
                           ! NUMERICAL DATA AND FUNCTIONAL RELATIONSHIPS
                           ! IN SCIENCE AND TECHNOLOGY. GROUP V/ VOL 4B
                           ! METEOROLOGY. PHYSICAL AND CHEMICAL
                           ! PROPERTIES OF AIR, P35
C
      REAL ATABLE          ! WORK VARIABLES
C
      INTEGER ITABLE       ! WORK VARIABLES
C
C     VARIABLES INTRODUCED BY DLR.
C
      REAL FSUBW           ! FACTOR THAT CONVERTS FROM SAT VAPOUR
                           ! PRESSURE IN A PURE WATER SYSTEM TO
                           ! SAT VAPOUR PRESSURE IN AIR.
C
      REAL ONE_MINUS_EPSILON  ! ONE MINUS THE RATIO OF THE MOLECULAR
                              ! WEIGHTS OF WATER AND DRY AIR
      REAL TT
C
      PARAMETER(ONE_MINUS_EPSILON = 1.0 - EPSILON)
C
C*---------------------------------------------------------------------
CL
CL---------------------------------------------------------------------
CL NO SIGNIFICANT STRUCTURE
CL---------------------------------------------------------------------
CL
C
C----------------------------------------------------------------------
C SATURATION WATER VAPOUR PRESSURE
C
C ABOVE 0 DEG C VALUES ARE OVER WATER
C
C BELOW 0 DEC C VALUES ARE OVER ICE
C----------------------------------------------------------------------
C
C Note: 0 element is a repeat of 1st element to cater for special case
C       of low temperatures (.LE.T_LOW) for which the array index is
C       rounded down due to machine precision.
      DATA (ES(IES),IES=    0, 95) / 0.966483E-02,
     *0.966483E-02,0.984279E-02,0.100240E-01,0.102082E-01,0.103957E-01,
     *0.105865E-01,0.107803E-01,0.109777E-01,0.111784E-01,0.113825E-01,
     *0.115902E-01,0.118016E-01,0.120164E-01,0.122348E-01,0.124572E-01,
     *0.126831E-01,0.129132E-01,0.131470E-01,0.133846E-01,0.136264E-01,
     *0.138724E-01,0.141225E-01,0.143771E-01,0.146356E-01,0.148985E-01,
     *0.151661E-01,0.154379E-01,0.157145E-01,0.159958E-01,0.162817E-01,
     *0.165725E-01,0.168680E-01,0.171684E-01,0.174742E-01,0.177847E-01,
     *0.181008E-01,0.184216E-01,0.187481E-01,0.190801E-01,0.194175E-01,
     *0.197608E-01,0.201094E-01,0.204637E-01,0.208242E-01,0.211906E-01,
     *0.215631E-01,0.219416E-01,0.223263E-01,0.227172E-01,0.231146E-01,
     *0.235188E-01,0.239296E-01,0.243465E-01,0.247708E-01,0.252019E-01,
     *0.256405E-01,0.260857E-01,0.265385E-01,0.269979E-01,0.274656E-01,
     *0.279405E-01,0.284232E-01,0.289142E-01,0.294124E-01,0.299192E-01,
     *0.304341E-01,0.309571E-01,0.314886E-01,0.320285E-01,0.325769E-01,
     *0.331348E-01,0.337014E-01,0.342771E-01,0.348618E-01,0.354557E-01,
     *0.360598E-01,0.366727E-01,0.372958E-01,0.379289E-01,0.385717E-01,
     *0.392248E-01,0.398889E-01,0.405633E-01,0.412474E-01,0.419430E-01,
     *0.426505E-01,0.433678E-01,0.440974E-01,0.448374E-01,0.455896E-01,
     *0.463545E-01,0.471303E-01,0.479191E-01,0.487190E-01,0.495322E-01/
      DATA (ES(IES),IES= 96,190) /
     *0.503591E-01,0.511977E-01,0.520490E-01,0.529145E-01,0.537931E-01,
     *0.546854E-01,0.555924E-01,0.565119E-01,0.574467E-01,0.583959E-01,
     *0.593592E-01,0.603387E-01,0.613316E-01,0.623409E-01,0.633655E-01,
     *0.644053E-01,0.654624E-01,0.665358E-01,0.676233E-01,0.687302E-01,
     *0.698524E-01,0.709929E-01,0.721490E-01,0.733238E-01,0.745180E-01,
     *0.757281E-01,0.769578E-01,0.782061E-01,0.794728E-01,0.807583E-01,
     *0.820647E-01,0.833905E-01,0.847358E-01,0.861028E-01,0.874882E-01,
     *0.888957E-01,0.903243E-01,0.917736E-01,0.932464E-01,0.947407E-01,
     *0.962571E-01,0.977955E-01,0.993584E-01,0.100942E+00,0.102551E+00,
     *0.104186E+00,0.105842E+00,0.107524E+00,0.109231E+00,0.110963E+00,
     *0.112722E+00,0.114506E+00,0.116317E+00,0.118153E+00,0.120019E+00,
     *0.121911E+00,0.123831E+00,0.125778E+00,0.127755E+00,0.129761E+00,
     *0.131796E+00,0.133863E+00,0.135956E+00,0.138082E+00,0.140241E+00,
     *0.142428E+00,0.144649E+00,0.146902E+00,0.149190E+00,0.151506E+00,
     *0.153859E+00,0.156245E+00,0.158669E+00,0.161126E+00,0.163618E+00,
     *0.166145E+00,0.168711E+00,0.171313E+00,0.173951E+00,0.176626E+00,
     *0.179342E+00,0.182096E+00,0.184893E+00,0.187724E+00,0.190600E+00,
     *0.193518E+00,0.196473E+00,0.199474E+00,0.202516E+00,0.205604E+00,
     *0.208730E+00,0.211905E+00,0.215127E+00,0.218389E+00,0.221701E+00/
      DATA (ES(IES),IES=191,285) /
     *0.225063E+00,0.228466E+00,0.231920E+00,0.235421E+00,0.238976E+00,
     *0.242580E+00,0.246232E+00,0.249933E+00,0.253691E+00,0.257499E+00,
     *0.261359E+00,0.265278E+00,0.269249E+00,0.273274E+00,0.277358E+00,
     *0.281498E+00,0.285694E+00,0.289952E+00,0.294268E+00,0.298641E+00,
     *0.303078E+00,0.307577E+00,0.312135E+00,0.316753E+00,0.321440E+00,
     *0.326196E+00,0.331009E+00,0.335893E+00,0.340842E+00,0.345863E+00,
     *0.350951E+00,0.356106E+00,0.361337E+00,0.366636E+00,0.372006E+00,
     *0.377447E+00,0.382966E+00,0.388567E+00,0.394233E+00,0.399981E+00,
     *0.405806E+00,0.411714E+00,0.417699E+00,0.423772E+00,0.429914E+00,
     *0.436145E+00,0.442468E+00,0.448862E+00,0.455359E+00,0.461930E+00,
     *0.468596E+00,0.475348E+00,0.482186E+00,0.489124E+00,0.496160E+00,
     *0.503278E+00,0.510497E+00,0.517808E+00,0.525224E+00,0.532737E+00,
     *0.540355E+00,0.548059E+00,0.555886E+00,0.563797E+00,0.571825E+00,
     *0.579952E+00,0.588198E+00,0.596545E+00,0.605000E+00,0.613572E+00,
     *0.622255E+00,0.631059E+00,0.639962E+00,0.649003E+00,0.658144E+00,
     *0.667414E+00,0.676815E+00,0.686317E+00,0.695956E+00,0.705728E+00,
     *0.715622E+00,0.725641E+00,0.735799E+00,0.746082E+00,0.756495E+00,
     *0.767052E+00,0.777741E+00,0.788576E+00,0.799549E+00,0.810656E+00,
     *0.821914E+00,0.833314E+00,0.844854E+00,0.856555E+00,0.868415E+00/
      DATA (ES(IES),IES=286,380) /
     *0.880404E+00,0.892575E+00,0.904877E+00,0.917350E+00,0.929974E+00,
     *0.942771E+00,0.955724E+00,0.968837E+00,0.982127E+00,0.995600E+00,
     *0.100921E+01,0.102304E+01,0.103700E+01,0.105116E+01,0.106549E+01,
     *0.108002E+01,0.109471E+01,0.110962E+01,0.112469E+01,0.113995E+01,
     *0.115542E+01,0.117107E+01,0.118693E+01,0.120298E+01,0.121923E+01,
     *0.123569E+01,0.125234E+01,0.126923E+01,0.128631E+01,0.130362E+01,
     *0.132114E+01,0.133887E+01,0.135683E+01,0.137500E+01,0.139342E+01,
     *0.141205E+01,0.143091E+01,0.145000E+01,0.146933E+01,0.148892E+01,
     *0.150874E+01,0.152881E+01,0.154912E+01,0.156970E+01,0.159049E+01,
     *0.161159E+01,0.163293E+01,0.165452E+01,0.167640E+01,0.169852E+01,
     *0.172091E+01,0.174359E+01,0.176653E+01,0.178977E+01,0.181332E+01,
     *0.183709E+01,0.186119E+01,0.188559E+01,0.191028E+01,0.193524E+01,
     *0.196054E+01,0.198616E+01,0.201208E+01,0.203829E+01,0.206485E+01,
     *0.209170E+01,0.211885E+01,0.214637E+01,0.217424E+01,0.220242E+01,
     *0.223092E+01,0.225979E+01,0.228899E+01,0.231855E+01,0.234845E+01,
     *0.237874E+01,0.240937E+01,0.244040E+01,0.247176E+01,0.250349E+01,
     *0.253560E+01,0.256814E+01,0.260099E+01,0.263431E+01,0.266800E+01,
     *0.270207E+01,0.273656E+01,0.277145E+01,0.280671E+01,0.284248E+01,
     *0.287859E+01,0.291516E+01,0.295219E+01,0.298962E+01,0.302746E+01/
      DATA (ES(IES),IES=381,475) /
     *0.306579E+01,0.310454E+01,0.314377E+01,0.318351E+01,0.322360E+01,
     *0.326427E+01,0.330538E+01,0.334694E+01,0.338894E+01,0.343155E+01,
     *0.347456E+01,0.351809E+01,0.356216E+01,0.360673E+01,0.365184E+01,
     *0.369744E+01,0.374352E+01,0.379018E+01,0.383743E+01,0.388518E+01,
     *0.393344E+01,0.398230E+01,0.403177E+01,0.408175E+01,0.413229E+01,
     *0.418343E+01,0.423514E+01,0.428746E+01,0.434034E+01,0.439389E+01,
     *0.444808E+01,0.450276E+01,0.455820E+01,0.461423E+01,0.467084E+01,
     *0.472816E+01,0.478607E+01,0.484468E+01,0.490393E+01,0.496389E+01,
     *0.502446E+01,0.508580E+01,0.514776E+01,0.521047E+01,0.527385E+01,
     *0.533798E+01,0.540279E+01,0.546838E+01,0.553466E+01,0.560173E+01,
     *0.566949E+01,0.573807E+01,0.580750E+01,0.587749E+01,0.594846E+01,
     *0.602017E+01,0.609260E+01,0.616591E+01,0.623995E+01,0.631490E+01,
     *0.639061E+01,0.646723E+01,0.654477E+01,0.662293E+01,0.670220E+01,
     *0.678227E+01,0.686313E+01,0.694495E+01,0.702777E+01,0.711142E+01,
     *0.719592E+01,0.728140E+01,0.736790E+01,0.745527E+01,0.754352E+01,
     *0.763298E+01,0.772316E+01,0.781442E+01,0.790676E+01,0.800001E+01,
     *0.809435E+01,0.818967E+01,0.828606E+01,0.838343E+01,0.848194E+01,
     *0.858144E+01,0.868207E+01,0.878392E+01,0.888673E+01,0.899060E+01,
     *0.909567E+01,0.920172E+01,0.930909E+01,0.941765E+01,0.952730E+01/
      DATA (ES(IES),IES=476,570) /
     *0.963821E+01,0.975022E+01,0.986352E+01,0.997793E+01,0.100937E+02,
     *0.102105E+02,0.103287E+02,0.104481E+02,0.105688E+02,0.106909E+02,
     *0.108143E+02,0.109387E+02,0.110647E+02,0.111921E+02,0.113207E+02,
     *0.114508E+02,0.115821E+02,0.117149E+02,0.118490E+02,0.119847E+02,
     *0.121216E+02,0.122601E+02,0.124002E+02,0.125416E+02,0.126846E+02,
     *0.128290E+02,0.129747E+02,0.131224E+02,0.132712E+02,0.134220E+02,
     *0.135742E+02,0.137278E+02,0.138831E+02,0.140403E+02,0.141989E+02,
     *0.143589E+02,0.145211E+02,0.146845E+02,0.148501E+02,0.150172E+02,
     *0.151858E+02,0.153564E+02,0.155288E+02,0.157029E+02,0.158786E+02,
     *0.160562E+02,0.162358E+02,0.164174E+02,0.166004E+02,0.167858E+02,
     *0.169728E+02,0.171620E+02,0.173528E+02,0.175455E+02,0.177406E+02,
     *0.179372E+02,0.181363E+02,0.183372E+02,0.185400E+02,0.187453E+02,
     *0.189523E+02,0.191613E+02,0.193728E+02,0.195866E+02,0.198024E+02,
     *0.200200E+02,0.202401E+02,0.204626E+02,0.206871E+02,0.209140E+02,
     *0.211430E+02,0.213744E+02,0.216085E+02,0.218446E+02,0.220828E+02,
     *0.223241E+02,0.225671E+02,0.228132E+02,0.230615E+02,0.233120E+02,
     *0.235651E+02,0.238211E+02,0.240794E+02,0.243404E+02,0.246042E+02,
     *0.248704E+02,0.251390E+02,0.254109E+02,0.256847E+02,0.259620E+02,
     *0.262418E+02,0.265240E+02,0.268092E+02,0.270975E+02,0.273883E+02/
      DATA (ES(IES),IES=571,665) /
     *0.276822E+02,0.279792E+02,0.282789E+02,0.285812E+02,0.288867E+02,
     *0.291954E+02,0.295075E+02,0.298222E+02,0.301398E+02,0.304606E+02,
     *0.307848E+02,0.311119E+02,0.314424E+02,0.317763E+02,0.321133E+02,
     *0.324536E+02,0.327971E+02,0.331440E+02,0.334940E+02,0.338475E+02,
     *0.342050E+02,0.345654E+02,0.349295E+02,0.352975E+02,0.356687E+02,
     *0.360430E+02,0.364221E+02,0.368042E+02,0.371896E+02,0.375790E+02,
     *0.379725E+02,0.383692E+02,0.387702E+02,0.391744E+02,0.395839E+02,
     *0.399958E+02,0.404118E+02,0.408325E+02,0.412574E+02,0.416858E+02,
     *0.421188E+02,0.425551E+02,0.429962E+02,0.434407E+02,0.438910E+02,
     *0.443439E+02,0.448024E+02,0.452648E+02,0.457308E+02,0.462018E+02,
     *0.466775E+02,0.471582E+02,0.476428E+02,0.481313E+02,0.486249E+02,
     *0.491235E+02,0.496272E+02,0.501349E+02,0.506479E+02,0.511652E+02,
     *0.516876E+02,0.522142E+02,0.527474E+02,0.532836E+02,0.538266E+02,
     *0.543737E+02,0.549254E+02,0.554839E+02,0.560456E+02,0.566142E+02,
     *0.571872E+02,0.577662E+02,0.583498E+02,0.589392E+02,0.595347E+02,
     *0.601346E+02,0.607410E+02,0.613519E+02,0.619689E+02,0.625922E+02,
     *0.632204E+02,0.638550E+02,0.644959E+02,0.651418E+02,0.657942E+02,
     *0.664516E+02,0.671158E+02,0.677864E+02,0.684624E+02,0.691451E+02,
     *0.698345E+02,0.705293E+02,0.712312E+02,0.719398E+02,0.726542E+02/
      DATA (ES(IES),IES=666,760) /
     *0.733754E+02,0.741022E+02,0.748363E+02,0.755777E+02,0.763247E+02,
     *0.770791E+02,0.778394E+02,0.786088E+02,0.793824E+02,0.801653E+02,
     *0.809542E+02,0.817509E+02,0.825536E+02,0.833643E+02,0.841828E+02,
     *0.850076E+02,0.858405E+02,0.866797E+02,0.875289E+02,0.883827E+02,
     *0.892467E+02,0.901172E+02,0.909962E+02,0.918818E+02,0.927760E+02,
     *0.936790E+02,0.945887E+02,0.955071E+02,0.964346E+02,0.973689E+02,
     *0.983123E+02,0.992648E+02,0.100224E+03,0.101193E+03,0.102169E+03,
     *0.103155E+03,0.104150E+03,0.105152E+03,0.106164E+03,0.107186E+03,
     *0.108217E+03,0.109256E+03,0.110303E+03,0.111362E+03,0.112429E+03,
     *0.113503E+03,0.114588E+03,0.115684E+03,0.116789E+03,0.117903E+03,
     *0.119028E+03,0.120160E+03,0.121306E+03,0.122460E+03,0.123623E+03,
     *0.124796E+03,0.125981E+03,0.127174E+03,0.128381E+03,0.129594E+03,
     *0.130822E+03,0.132058E+03,0.133306E+03,0.134563E+03,0.135828E+03,
     *0.137109E+03,0.138402E+03,0.139700E+03,0.141017E+03,0.142338E+03,
     *0.143676E+03,0.145025E+03,0.146382E+03,0.147753E+03,0.149133E+03,
     *0.150529E+03,0.151935E+03,0.153351E+03,0.154783E+03,0.156222E+03,
     *0.157678E+03,0.159148E+03,0.160624E+03,0.162117E+03,0.163621E+03,
     *0.165142E+03,0.166674E+03,0.168212E+03,0.169772E+03,0.171340E+03,
     *0.172921E+03,0.174522E+03,0.176129E+03,0.177755E+03,0.179388E+03/
      DATA (ES(IES),IES=761,855) /
     *0.181040E+03,0.182707E+03,0.184382E+03,0.186076E+03,0.187782E+03,
     *0.189503E+03,0.191240E+03,0.192989E+03,0.194758E+03,0.196535E+03,
     *0.198332E+03,0.200141E+03,0.201963E+03,0.203805E+03,0.205656E+03,
     *0.207532E+03,0.209416E+03,0.211317E+03,0.213236E+03,0.215167E+03,
     *0.217121E+03,0.219087E+03,0.221067E+03,0.223064E+03,0.225080E+03,
     *0.227113E+03,0.229160E+03,0.231221E+03,0.233305E+03,0.235403E+03,
     *0.237520E+03,0.239655E+03,0.241805E+03,0.243979E+03,0.246163E+03,
     *0.248365E+03,0.250593E+03,0.252830E+03,0.255093E+03,0.257364E+03,
     *0.259667E+03,0.261979E+03,0.264312E+03,0.266666E+03,0.269034E+03,
     *0.271430E+03,0.273841E+03,0.276268E+03,0.278722E+03,0.281185E+03,
     *0.283677E+03,0.286190E+03,0.288714E+03,0.291266E+03,0.293834E+03,
     *0.296431E+03,0.299045E+03,0.301676E+03,0.304329E+03,0.307006E+03,
     *0.309706E+03,0.312423E+03,0.315165E+03,0.317930E+03,0.320705E+03,
     *0.323519E+03,0.326350E+03,0.329199E+03,0.332073E+03,0.334973E+03,
     *0.337897E+03,0.340839E+03,0.343800E+03,0.346794E+03,0.349806E+03,
     *0.352845E+03,0.355918E+03,0.358994E+03,0.362112E+03,0.365242E+03,
     *0.368407E+03,0.371599E+03,0.374802E+03,0.378042E+03,0.381293E+03,
     *0.384588E+03,0.387904E+03,0.391239E+03,0.394604E+03,0.397988E+03,
     *0.401411E+03,0.404862E+03,0.408326E+03,0.411829E+03,0.415352E+03/
      DATA (ES(IES),IES=856,950) /
     *0.418906E+03,0.422490E+03,0.426095E+03,0.429740E+03,0.433398E+03,
     *0.437097E+03,0.440827E+03,0.444570E+03,0.448354E+03,0.452160E+03,
     *0.455999E+03,0.459870E+03,0.463765E+03,0.467702E+03,0.471652E+03,
     *0.475646E+03,0.479674E+03,0.483715E+03,0.487811E+03,0.491911E+03,
     *0.496065E+03,0.500244E+03,0.504448E+03,0.508698E+03,0.512961E+03,
     *0.517282E+03,0.521617E+03,0.525989E+03,0.530397E+03,0.534831E+03,
     *0.539313E+03,0.543821E+03,0.548355E+03,0.552938E+03,0.557549E+03,
     *0.562197E+03,0.566884E+03,0.571598E+03,0.576351E+03,0.581131E+03,
     *0.585963E+03,0.590835E+03,0.595722E+03,0.600663E+03,0.605631E+03,
     *0.610641E+03,0.615151E+03,0.619625E+03,0.624140E+03,0.628671E+03,
     *0.633243E+03,0.637845E+03,0.642465E+03,0.647126E+03,0.651806E+03,
     *0.656527E+03,0.661279E+03,0.666049E+03,0.670861E+03,0.675692E+03,
     *0.680566E+03,0.685471E+03,0.690396E+03,0.695363E+03,0.700350E+03,
     *0.705381E+03,0.710444E+03,0.715527E+03,0.720654E+03,0.725801E+03,
     *0.730994E+03,0.736219E+03,0.741465E+03,0.746756E+03,0.752068E+03,
     *0.757426E+03,0.762819E+03,0.768231E+03,0.773692E+03,0.779172E+03,
     *0.784701E+03,0.790265E+03,0.795849E+03,0.801483E+03,0.807137E+03,
     *0.812842E+03,0.818582E+03,0.824343E+03,0.830153E+03,0.835987E+03,
     *0.841871E+03,0.847791E+03,0.853733E+03,0.859727E+03,0.865743E+03/
      DATA (ES(IES),IES=951,1045) /
     *0.871812E+03,0.877918E+03,0.884046E+03,0.890228E+03,0.896433E+03,
     *0.902690E+03,0.908987E+03,0.915307E+03,0.921681E+03,0.928078E+03,
     *0.934531E+03,0.941023E+03,0.947539E+03,0.954112E+03,0.960708E+03,
     *0.967361E+03,0.974053E+03,0.980771E+03,0.987545E+03,0.994345E+03,
     *0.100120E+04,0.100810E+04,0.101502E+04,0.102201E+04,0.102902E+04,
     *0.103608E+04,0.104320E+04,0.105033E+04,0.105753E+04,0.106475E+04,
     *0.107204E+04,0.107936E+04,0.108672E+04,0.109414E+04,0.110158E+04,
     *0.110908E+04,0.111663E+04,0.112421E+04,0.113185E+04,0.113952E+04,
     *0.114725E+04,0.115503E+04,0.116284E+04,0.117071E+04,0.117861E+04,
     *0.118658E+04,0.119459E+04,0.120264E+04,0.121074E+04,0.121888E+04,
     *0.122709E+04,0.123534E+04,0.124362E+04,0.125198E+04,0.126036E+04,
     *0.126881E+04,0.127731E+04,0.128584E+04,0.129444E+04,0.130307E+04,
     *0.131177E+04,0.132053E+04,0.132931E+04,0.133817E+04,0.134705E+04,
     *0.135602E+04,0.136503E+04,0.137407E+04,0.138319E+04,0.139234E+04,
     *0.140156E+04,0.141084E+04,0.142015E+04,0.142954E+04,0.143896E+04,
     *0.144845E+04,0.145800E+04,0.146759E+04,0.147725E+04,0.148694E+04,
     *0.149672E+04,0.150655E+04,0.151641E+04,0.152635E+04,0.153633E+04,
     *0.154639E+04,0.155650E+04,0.156665E+04,0.157688E+04,0.158715E+04,
     *0.159750E+04,0.160791E+04,0.161836E+04,0.162888E+04,0.163945E+04/
      DATA (ES(IES),IES=1046,1140) /
     *0.165010E+04,0.166081E+04,0.167155E+04,0.168238E+04,0.169325E+04,
     *0.170420E+04,0.171522E+04,0.172627E+04,0.173741E+04,0.174859E+04,
     *0.175986E+04,0.177119E+04,0.178256E+04,0.179402E+04,0.180552E+04,
     *0.181711E+04,0.182877E+04,0.184046E+04,0.185224E+04,0.186407E+04,
     *0.187599E+04,0.188797E+04,0.190000E+04,0.191212E+04,0.192428E+04,
     *0.193653E+04,0.194886E+04,0.196122E+04,0.197368E+04,0.198618E+04,
     *0.199878E+04,0.201145E+04,0.202416E+04,0.203698E+04,0.204983E+04,
     *0.206278E+04,0.207580E+04,0.208887E+04,0.210204E+04,0.211525E+04,
     *0.212856E+04,0.214195E+04,0.215538E+04,0.216892E+04,0.218249E+04,
     *0.219618E+04,0.220994E+04,0.222375E+04,0.223766E+04,0.225161E+04,
     *0.226567E+04,0.227981E+04,0.229399E+04,0.230829E+04,0.232263E+04,
     *0.233708E+04,0.235161E+04,0.236618E+04,0.238087E+04,0.239560E+04,
     *0.241044E+04,0.242538E+04,0.244035E+04,0.245544E+04,0.247057E+04,
     *0.248583E+04,0.250116E+04,0.251654E+04,0.253204E+04,0.254759E+04,
     *0.256325E+04,0.257901E+04,0.259480E+04,0.261073E+04,0.262670E+04,
     *0.264279E+04,0.265896E+04,0.267519E+04,0.269154E+04,0.270794E+04,
     *0.272447E+04,0.274108E+04,0.275774E+04,0.277453E+04,0.279137E+04,
     *0.280834E+04,0.282540E+04,0.284251E+04,0.285975E+04,0.287704E+04,
     *0.289446E+04,0.291198E+04,0.292954E+04,0.294725E+04,0.296499E+04/
      DATA (ES(IES),IES=1141,1235) /
     *0.298288E+04,0.300087E+04,0.301890E+04,0.303707E+04,0.305529E+04,
     *0.307365E+04,0.309211E+04,0.311062E+04,0.312927E+04,0.314798E+04,
     *0.316682E+04,0.318577E+04,0.320477E+04,0.322391E+04,0.324310E+04,
     *0.326245E+04,0.328189E+04,0.330138E+04,0.332103E+04,0.334073E+04,
     *0.336058E+04,0.338053E+04,0.340054E+04,0.342069E+04,0.344090E+04,
     *0.346127E+04,0.348174E+04,0.350227E+04,0.352295E+04,0.354369E+04,
     *0.356458E+04,0.358559E+04,0.360664E+04,0.362787E+04,0.364914E+04,
     *0.367058E+04,0.369212E+04,0.371373E+04,0.373548E+04,0.375731E+04,
     *0.377929E+04,0.380139E+04,0.382355E+04,0.384588E+04,0.386826E+04,
     *0.389081E+04,0.391348E+04,0.393620E+04,0.395910E+04,0.398205E+04,
     *0.400518E+04,0.402843E+04,0.405173E+04,0.407520E+04,0.409875E+04,
     *0.412246E+04,0.414630E+04,0.417019E+04,0.419427E+04,0.421840E+04,
     *0.424272E+04,0.426715E+04,0.429165E+04,0.431634E+04,0.434108E+04,
     *0.436602E+04,0.439107E+04,0.441618E+04,0.444149E+04,0.446685E+04,
     *0.449241E+04,0.451810E+04,0.454385E+04,0.456977E+04,0.459578E+04,
     *0.462197E+04,0.464830E+04,0.467468E+04,0.470127E+04,0.472792E+04,
     *0.475477E+04,0.478175E+04,0.480880E+04,0.483605E+04,0.486336E+04,
     *0.489087E+04,0.491853E+04,0.494623E+04,0.497415E+04,0.500215E+04,
     *0.503034E+04,0.505867E+04,0.508707E+04,0.511568E+04,0.514436E+04/
      DATA (ES(IES),IES=1236,1330) /
     *0.517325E+04,0.520227E+04,0.523137E+04,0.526068E+04,0.529005E+04,
     *0.531965E+04,0.534939E+04,0.537921E+04,0.540923E+04,0.543932E+04,
     *0.546965E+04,0.550011E+04,0.553064E+04,0.556139E+04,0.559223E+04,
     *0.562329E+04,0.565449E+04,0.568577E+04,0.571727E+04,0.574884E+04,
     *0.578064E+04,0.581261E+04,0.584464E+04,0.587692E+04,0.590924E+04,
     *0.594182E+04,0.597455E+04,0.600736E+04,0.604039E+04,0.607350E+04,
     *0.610685E+04,0.614036E+04,0.617394E+04,0.620777E+04,0.624169E+04,
     *0.627584E+04,0.631014E+04,0.634454E+04,0.637918E+04,0.641390E+04,
     *0.644887E+04,0.648400E+04,0.651919E+04,0.655467E+04,0.659021E+04,
     *0.662599E+04,0.666197E+04,0.669800E+04,0.673429E+04,0.677069E+04,
     *0.680735E+04,0.684415E+04,0.688104E+04,0.691819E+04,0.695543E+04,
     *0.699292E+04,0.703061E+04,0.706837E+04,0.710639E+04,0.714451E+04,
     *0.718289E+04,0.722143E+04,0.726009E+04,0.729903E+04,0.733802E+04,
     *0.737729E+04,0.741676E+04,0.745631E+04,0.749612E+04,0.753602E+04,
     *0.757622E+04,0.761659E+04,0.765705E+04,0.769780E+04,0.773863E+04,
     *0.777975E+04,0.782106E+04,0.786246E+04,0.790412E+04,0.794593E+04,
     *0.798802E+04,0.803028E+04,0.807259E+04,0.811525E+04,0.815798E+04,
     *0.820102E+04,0.824427E+04,0.828757E+04,0.833120E+04,0.837493E+04,
     *0.841895E+04,0.846313E+04,0.850744E+04,0.855208E+04,0.859678E+04/
      DATA (ES(IES),IES=1331,1425) /
     *0.864179E+04,0.868705E+04,0.873237E+04,0.877800E+04,0.882374E+04,
     *0.886979E+04,0.891603E+04,0.896237E+04,0.900904E+04,0.905579E+04,
     *0.910288E+04,0.915018E+04,0.919758E+04,0.924529E+04,0.929310E+04,
     *0.934122E+04,0.938959E+04,0.943804E+04,0.948687E+04,0.953575E+04,
     *0.958494E+04,0.963442E+04,0.968395E+04,0.973384E+04,0.978383E+04,
     *0.983412E+04,0.988468E+04,0.993534E+04,0.998630E+04,0.100374E+05,
     *0.100888E+05,0.101406E+05,0.101923E+05,0.102444E+05,0.102966E+05,
     *0.103492E+05,0.104020E+05,0.104550E+05,0.105082E+05,0.105616E+05,
     *0.106153E+05,0.106693E+05,0.107234E+05,0.107779E+05,0.108325E+05,
     *0.108874E+05,0.109425E+05,0.109978E+05,0.110535E+05,0.111092E+05,
     *0.111653E+05,0.112217E+05,0.112782E+05,0.113350E+05,0.113920E+05,
     *0.114493E+05,0.115070E+05,0.115646E+05,0.116228E+05,0.116809E+05,
     *0.117396E+05,0.117984E+05,0.118574E+05,0.119167E+05,0.119762E+05,
     *0.120360E+05,0.120962E+05,0.121564E+05,0.122170E+05,0.122778E+05,
     *0.123389E+05,0.124004E+05,0.124619E+05,0.125238E+05,0.125859E+05,
     *0.126484E+05,0.127111E+05,0.127739E+05,0.128372E+05,0.129006E+05,
     *0.129644E+05,0.130285E+05,0.130927E+05,0.131573E+05,0.132220E+05,
     *0.132872E+05,0.133526E+05,0.134182E+05,0.134842E+05,0.135503E+05,
     *0.136168E+05,0.136836E+05,0.137505E+05,0.138180E+05,0.138854E+05/
      DATA (ES(IES),IES=1426,1520) /
     *0.139534E+05,0.140216E+05,0.140900E+05,0.141588E+05,0.142277E+05,
     *0.142971E+05,0.143668E+05,0.144366E+05,0.145069E+05,0.145773E+05,
     *0.146481E+05,0.147192E+05,0.147905E+05,0.148622E+05,0.149341E+05,
     *0.150064E+05,0.150790E+05,0.151517E+05,0.152250E+05,0.152983E+05,
     *0.153721E+05,0.154462E+05,0.155205E+05,0.155952E+05,0.156701E+05,
     *0.157454E+05,0.158211E+05,0.158969E+05,0.159732E+05,0.160496E+05,
     *0.161265E+05,0.162037E+05,0.162811E+05,0.163589E+05,0.164369E+05,
     *0.165154E+05,0.165942E+05,0.166732E+05,0.167526E+05,0.168322E+05,
     *0.169123E+05,0.169927E+05,0.170733E+05,0.171543E+05,0.172356E+05,
     *0.173173E+05,0.173993E+05,0.174815E+05,0.175643E+05,0.176471E+05,
     *0.177305E+05,0.178143E+05,0.178981E+05,0.179826E+05,0.180671E+05,
     *0.181522E+05,0.182377E+05,0.183232E+05,0.184093E+05,0.184955E+05,
     *0.185823E+05,0.186695E+05,0.187568E+05,0.188447E+05,0.189326E+05,
     *0.190212E+05,0.191101E+05,0.191991E+05,0.192887E+05,0.193785E+05,
     *0.194688E+05,0.195595E+05,0.196503E+05,0.197417E+05,0.198332E+05,
     *0.199253E+05,0.200178E+05,0.201105E+05,0.202036E+05,0.202971E+05,
     *0.203910E+05,0.204853E+05,0.205798E+05,0.206749E+05,0.207701E+05,
     *0.208659E+05,0.209621E+05,0.210584E+05,0.211554E+05,0.212524E+05,
     *0.213501E+05,0.214482E+05,0.215465E+05,0.216452E+05,0.217442E+05/
      DATA (ES(IES),IES=1521,1552) /
     *0.218439E+05,0.219439E+05,0.220440E+05,0.221449E+05,0.222457E+05,
     *0.223473E+05,0.224494E+05,0.225514E+05,0.226542E+05,0.227571E+05,
     *0.228606E+05,0.229646E+05,0.230687E+05,0.231734E+05,0.232783E+05,
     *0.233839E+05,0.234898E+05,0.235960E+05,0.237027E+05,0.238097E+05,
     *0.239173E+05,0.240254E+05,0.241335E+05,0.242424E+05,0.243514E+05,
     *0.244611E+05,0.245712E+05,0.246814E+05,0.247923E+05,0.249034E+05,
     *0.250152E+05,0.250152E+05/
C
      DO 10 I=1,NPNTS
C      COMPUTE THE FACTOR THAT CONVERTS FROM SAT VAPOUR PRESSURE
C      IN A PURE WATER SYSTEM TO SAT VAPOUR PRESSURE IN AIR, FSUBW.
C      THIS FORMULA IS TAKEN FROM EQUATION A4.7 OF ADRIAN GILL'S
C      BOOK: ATMOSPHERE-ocean DYNAMICS. NOTE THAT HIS FORMULA
C      WORKS IN TERMS OF PRESSURE IN MB AND TEMPERATURE IN CELSIUS,
C      SO CONVERSION OF UNITS LEADS TO THE SLIGHTLY DIFFERENT
C      EQUATION USED HERE.
C
       FSUBW = 1.0 +1.0E-8*P(I)*( 4.5 +
     +   6.0E-4*( T(I) - ZERODEGC )*( T(I) - ZERODEGC ) )
C
C      USE THE LOOKUP TABLE TO FIND SATURATED VAAPOUR PRESSURE,
C      AND STORE IT IN QS.
C
C
       TT=MAX(T_LOW,T(I))
       TT=MIN(T_HIGH,TT)

       ATABLE = (TT - T_LOW + DELTA_T) / DELTA_T
          ITABLE = ATABLE
          ATABLE = ATABLE - ITABLE
C
          QS(I) = (1.0 - ATABLE)*ES(ITABLE)
     +           + ATABLE*ES(ITABLE+1)
C
C
C     MULTIPLY BY FSUBW TO CONVERT TO SATURATED VAPOUR PRESSURE
C     IN AIR (EQUATION A4.6 OF ADRIAN GILL'S BOOK).
C
       QS(I) = QS(I)*FSUBW
C
C     NOW FORM THE ACCURATE EXPRESSION FOR QS, WHICH IS A
C     REARRANGED VERSION OF EQUATION A4.3 OF GILL'S BOOK.
C
C     NOTE THAT AT VERY LOW PRESSURES WE APPLY A FIX, TO
C     PREVENT A SINGULARITY.
C
         QS(I) = ( EPSILON*QS(I) ) /
     +           ( MAX(P(I),QS(I)) - ONE_MINUS_EPSILON*QS(I) )
C
 10   CONTINUE
C
C [Step 2 of unified-codebase rebuild: removed qsat_output.txt debug-dump
C  + Fortran PAUSE statement that previously sat here. The dump opened
C  qsat_output.txt on every QSAT invocation (per cell x per sub-day step
C  x per day x per month) without closing — leaking file handles and
C  generating O(GB) of unused output. The PAUSE halted non-interactive
C  runs at the first QSAT call. See EXECUTION_PLAN.md V.1 step 2 and
C  COUPLED_MODEL_INVESTIGATION.md section 8.1 bugs C10/C11.]
C
      RETURN
      END
