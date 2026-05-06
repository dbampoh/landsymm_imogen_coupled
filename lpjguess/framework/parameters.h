///////////////////////////////////////////////////////////////////////////////////////
/// \file parameters.h
/// \brief The parameters module is responsible for reading in the instruction file
///
/// This module defines and makes available a lot of the instruction file parameters
/// used by the model, but also lets other modules define their own parameters or
/// access "custom" parameters without defining them.
///
/// A new parameter can be added by creating a new global variable here (or a new
/// Pft member variable if it's a PFT parameter), and then declaring it in
/// plib_declarations in parameters.cpp. See the many existing examples, and
/// documentation in the PLIB library for further documentation about this.
///
/// Sometimes, adding a new parameter shouldn't (or can't) be done here however.
/// A parameter specific for a certain input module, should only be declared if
/// that input module is used. In this case the input module should declare its
/// own parameters when it is created. This can also be a good idea simply to
/// make modules more independent. For parameters like this, we can either use
/// the "custom" parameters (\see Paramlist) which don't need to be declared at
/// all, or the parameters can be declared with the declare_parameter family of
/// functions.
///
/// \author Joe Siltberg
/// $Date$
///
///////////////////////////////////////////////////////////////////////////////////////

#ifndef LPJ_GUESS_PARAMETERS_H
#define LPJ_GUESS_PARAMETERS_H
#define GCP  // GCP related changes

#include "gutil.h"
#include <string>
#include <queue>
#include<iostream>

// SSR: GGCMI
#include <vector>

#define GCP  // GCP related changes

///////////////////////////////////////////////////////////////////////////////////////
// Enums needed by some of the global instruction file parameters defined below


/// Vegetation 'mode', i.e. what each Individual object represents
/** Can be one of:
 *  1. The average characteristics of all individuals comprising a PFT
 *     population over the modelled area (standard LPJ mode)
 *  2. A cohort of individuals of a PFT that are roughly the same age
 *  3. An individual plant
 */
typedef enum {NOVEGMODE, INDIVIDUAL, COHORT, POPULATION} vegmodetype;

/// Land cover type of a stand. NLANDCOVERTYPES keeps count of number of items.
/*  NB. set_lc_change_array() must be modified when adding new land cover types
 */
typedef enum {URBAN, CROPLAND, PASTURE, FOREST, NATURAL, PEATLAND, BARREN, NLANDCOVERTYPES} landcovertype;

/// Water uptake parameterisations
/** \see water_uptake in canexch.cpp
  */
typedef enum {WR_WCONT, WR_ROOTDIST, WR_SMART, WR_SPECIESSPECIFIC} wateruptaketype;

///bvoc: define monoterpene species used
typedef enum {APIN, BPIN, LIMO, MYRC, SABI, CAMP, TRIC, TBOC, OTHR, NMTCOMPOUNDTYPES} monoterpenecompoundtype;

/// Fire model setting. Either use 
/**	One of
 *	BLAZE 				Use the BLAZE model to generate fire fluxes
 *                      	(must be accompanied by ignitionmode; DEFAULT)
 *	GLOBFIRM			fire parameterization following Thonicke et al. 2001
 *	NOFIRE				no fire model
 *	SPITFIRE  			full SPITFIRE calculations using ignitions and fire area
 *  STAT_BURNT_AREA 	use DESPITE statistical model to calculate BA (with SPITFRE combustion, mortality etc)
 *  PRESCR_BURNT_AREA 	read in BA from a file "file_burnt_area" (with SPITFRE combustion, mortality etc)
 *  PRESCR_NUMBER_FIRES read in number if fires from "file_num_fires" (with SPITFRE combustion, mortality etc)
 *  FIXED_FIRE_RETURN 	burn patches based on a fixed fire regime (with SPITFRE combustion, mortality etc)
 *  RANDOM_FIRE_RETURN 	burn patches based on a fixed fire return probability (with SPITFRE combustion, mortality etc)
 */

typedef enum {BLAZE, GLOBFIRM, NOFIRE, SPITFIRE, STAT_BURNT_AREA, PRESCR_BURNT_AREA, PRESCR_NUMBER_FIRES, FIXED_FIRE_RETURN, RANDOM_FIRE_RETURN} firemodeltype;

/// Type of weathergenerator used 
/**     One of:
 *      GWGEN           Global Weather GENerator (needed by BLAZE, due to 
 *                      additional rel. humidity and wind; DEFAULT)
 *      INTERP          use standard interpolation scheme
 *      NONE            Should be set if daily input is used (e.g. in cfinput) 
 */
typedef enum {GWGEN, INTERP, NONE} weathergeneratortype;

///How to determine root distribution in soil layers
typedef enum {ROOTDIST_FIXED, ROOTDIST_JACKSON} rootdisttype;

/////////////////////////////////////////////////////////////////////////
// MF: SPITFIRE MODES


//typedef enum {NOFIRE2, SPITFIRE, STAT_BURNT_AREA, PRESCR_BURNT_AREA, PRESCR_NUMBER_FIRES, FIXED_FIRE_RETURN, RANDOM_FIRE_RETURN} firemodetype;
//	// Mode to calculate burnt area/number of fires:
//	// NONE = no fire, but allow calculation of some routines to run, eg SPITFIRE accounting etc


typedef enum {BOTH, HUMAN, LIGHTNING, NOINGITIONS} ignitionmodetype;
	// For full SPITFIRE runs select the ignitions sources
	// BOTH = include both HUMAN and LIGHTNING ignitions
	// HUMAN = include only human ignitions (using population density, slope and A(Nd) from "file_hum_ign")
	// LIGHTNING = include only lightning ignitions calculated from monthly flash rates (given in "file_lightn_ign")
	// NOIGNINTIONS = no ignitions, this allows for the full spitfire calculation (for diagnostics etc) but with no fire effects

typedef enum {ORIGINAL, DAILY_VPD} fuelmoisturemodeltype;
	// Select fuel moisture model
	// ORIGINAL = original SPITFIRE formulation for fuel moisture
	// DAILY_VPD = daily fuel moisture model from Nolan et al. 201? based on vapour pressure deficit

typedef enum {NO_PASTURE_BURNING, FULL_PASTURE_BURNING, LIGHTNING_PASTURE_BURNING, PRESCRIBED_PASTURE_BURNING, MODELLED_PASTURE_BURNING} pasturefiretype;
	// Select pasture fire type
	// NO_PASTURE_BURNING = pasture doesn't burn (at all)
	// FULL_PASTURE_BURNING = pasture burns as natural grasslands (ie standard SPITFIRE with full human ignitions)
	// LIGHTNING_PASTURE_BURNING = pasture burns only with lightning fire
	// PRESCRIBED_PASTURE_BURNING = read in pasture burnt fraction from a file
	// MODELLED_PASTURE_BURNING = some clever pasture fire model that doesn't exists yet


typedef enum {NO_CROPLAND_BURNING, FULL_CROPLAND_BURNING, LIGHTNING_CROPLAND_BURNING, PRESCRIBED_CROPLAND_BURNING, MODELLED_CROPLAND_BURNING} cropfiretype;
	// Select crop fire type
	// NO_CROPLAND_BURNING = croplands don't burn (at all)
	// FULL_CROPLAND_BURNING = croplands as natural grasslands (ie standard SPITFIRE with full human ignitions)
	// LIGHTNING_CROPLAND_BURNING = cropland burns only with lightning fire
	// PRESCRIBED_CROPLAND_BURNING = read in cropland burnt fraction from a file
	// MODELLED_CROPLAND_BURNING = some clever cropland fire model that doesn't exist yet

typedef enum {NOLIMIT, LASSLOP, ROTHERMEL, ANDREWS} windlimittype;
	// Select limit of windspeed on rate of spread
	// NOLIMIT = no limit of windspeed (original SPITFIRE implementation)
	// LASSLOP = effective windspeed decreases linearly from 100 feet/min to zero at 150 feet/min (Lasslop, Thonicke and Kloster 2014)
	// ROTHERMEL = original windspeed limit from Rothermel 1921
	// ANDREWS = updated windspeed limit from Andrews, Cruz and Rothermel 2013

//DKB
typedef enum {ONLINE, OFFLINE}lpjgimogensimulationmode;
typedef enum {LPJG_OFFSET,MOVING_AVERAGE}lpjgimogenfeedbackmode;

///////////////////////////////////////////////////////////////////////////////////////
// Global instruction file parameters

/// Title for this run
extern xtring title;

/// Vegetation mode (population, cohort or individual)
extern vegmodetype vegmode;

/// Default number of patches in each stand
/** Should always be 1 in population mode,
 *  cropland stands always have 1 patch.
 *  Actual patch number for stand objects may differ and 
 *  should always be queried by stand.npatch()
 */
extern int npatch;

/// Number of patches in each stand for secondary stands
extern int npatch_secondarystand;

/// Whether to reduce equal percentage of all stands of a stand type at land cover change
extern bool reduce_all_stands;

/// Minimum age of stands to reduce at land cover change
extern int age_limit_reduce;

/// Patch area (m2) (individual and cohort mode only)
extern double patcharea;

/// Whether background establishment enabled (individual, cohort mode)
extern bool ifbgestab;

/// Whether spatial mass effect enabled for establishment (individual, cohort mode)
extern bool ifsme;

/// Whether establishment stochastic (individual, cohort mode)
extern bool ifstochestab;

/// Whether mortality stochastic (individual, cohort mode)
extern bool ifstochmort;

/// Fire-model switch
extern firemodeltype firemodel;

/// Weather Generator switch
extern weathergeneratortype weathergenerator;

/// Whether "generic" patch-destroying disturbance enabled (individual, cohort mode)
extern bool ifdisturb;

/// Generic patch-destroying disturbance interval (individual, cohort mode)
extern double distinterval;

/// Whether SLA calculated from leaf longevity (alt: prescribed)
extern bool ifcalcsla;

/// Whether leaf C:N ratio minimum calculated from leaf longevity (alt: prescribed)
extern bool ifcalccton;

/// Establishment interval in cohort mode (years)
extern int estinterval;

/// Whether C debt (storage between years) permitted
extern bool ifcdebt;

/// Water uptake parameterisation
extern wateruptaketype wateruptake;

/// Parameterisation of root distribution
extern rootdisttype rootdistribution;

/// whether CENTURY SOM dynamics (otherwise uses standard LPJ formalism)
extern bool ifcentury;

/// whether plant growth limited by available N
extern bool ifnlim;

/// number of years to allow spinup without nitrogen limitation
extern int freenyears;

/// fraction of nitrogen relocated by plants from roots and leaves
extern double nrelocfrac;

/// first term in nitrogen fixation eqn (Cleveland et al 1999)
extern double nfix_a;

/// second term in nitrogen fixation eqn (Cleveland et al 1999)
extern double nfix_b;

/// whether to use nitrification/denitrification in CENTURY SOM dynamics
extern bool ifntransform;
/// Fraction of microbial respiration assumed to produce DOC, 0.0,0.3
extern double frac_labile_carbon;

/// Soil pH (used for calculating N-transformation), 3.5,8.5
extern double pH_soil;
/// Maximum nitrification rate, 0.03,0.15
extern double f_nitri_max;
/// Constant in denitrification, 0.001,0.1
extern double k_N;
/// Constant in temperature function for denitrification, 0.005,0.05
extern double k_C;
/// Maximum gaseus losses in nitrification
extern double f_nitri_gas_max;
/// Maximum fraction of NO3 converted to NO2
extern double f_denitri_max;
/// Maximum fraction of NO2 converted to gaseus N
extern double f_denitri_gas_max;


///////////////////////////////////////////////////////////////////////////////////////
// Landuse and crop settings

/// Whether other landcovers than natural vegetation are simulated.
extern bool run_landcover;

/// Whether a specific landcover type is simulated (URBAN, CROPLAND, PASTURE, FOREST, NATURAL, PEATLAND, BARREN).
extern bool run[NLANDCOVERTYPES];

/// Whether landcover fractions are not read from input file.
extern bool lcfrac_fixed;

/// Whether fractions of stand types of a specific land cover are not read from input file.
extern bool frac_fixed[NLANDCOVERTYPES];

/// Set to false by initio( ) if fraction input files have yearly data.
extern bool all_fracs_const;

/// If a slow harvested product pool is included in patchpft.
extern bool ifslowharvestpool;

// If grass is allowed to grow between crop growingseasons
extern bool ifintercropgrass;

// Whether to calculate dynamic potential heat units
extern bool ifcalcdynamic_phu;

// Whether to use gross land transfer: simulate gross lcc (1); read landcover transfer matrix input file (2); read stand type transfer matrix input file (3), or not (0)
extern int gross_land_transfer;

// Whether gross land transfer input read for this gridcell
extern bool gross_input_present;

// Whether to use primary/secondary land transition info in landcover transfer input file (1). or not (0)
extern bool ifprimary_lc_transfer;

// Whether to use primary-to-secondary land transition info (within land cover type) in landcover transfer input file (1). or not (0)
extern bool ifprimary_to_secondary_transfer;

// Pooling level of land cover transitions; 0: one big pool; 1: land cover-level; 2: stand type-level
extern int transfer_level;

// Whether to create new stands in transfer_to_new_stand() according to the rules in copy_stand_type()
extern bool iftransfer_to_new_stand;

// Whether to limit dynamic phu calculation to a period specified by nyear_dyn_phu
extern bool ifdyn_phu_limit;

// Number of years to calculate dynamic phu if dynamic_phu_limit is true
extern int nyear_dyn_phu;

/// number of spinup years
extern int nyear_spinup;

/// Whether to use sowingdates from input file
extern bool readsowingdates;

/// Whether to use harvestdates from input file
extern bool readharvestdates;

/// Whether to read N fertilization from input file
extern bool readNfert;

/// Whether to read manure N fertilization from input file
extern bool readNman;

/// Whether to read N fertilization (stand type level) from input file
extern bool readNfert_st;

/// Whether to use forest harvested fraction from input file (using LUC functionality)
extern bool readwoodharvest_frac;

/// Whether to use wood harvest C mass from input file (using LUC functionality)
extern bool readwoodharvest_cmass;

/// Whether to create new stands at clearcut of secondary stands when using wood harvest input (LUC functionality)
extern bool harvest_secondary_to_new_stand;

/// Whether to read disturbance intervals from input file
extern bool readdisturbance;

/// Whether to read disturbance intervals for stand types from input file
extern bool readdisturbance_st;

/// Whether to read cutinterval for stand types from input file
extern bool readcutinterval_st;

/// Whether to read stand type elevation from input file
extern bool readelevation_st;

/// Whether to read firstmanageyear for stand types from input file
extern bool readfirstmanageyear_st;

// Whether to read target-cutting distribution for selection in mt from input file
extern bool readtargetcutting;

/// Whether to burn thin trees during tree harvest (ignoring pft.harvest_slow_frac)
extern bool harvest_burn_thin_trees;

/// Whether to print multiple stands within a stand type (except cropland) separately
extern bool printseparatestands;

// SSR: GGCMI: Scaling factor for Nfert input (applies only to file_Nfert and file_Nfert_st)
extern double Nfert_scale_factor;

/// SSR: GGCMI: Manure C:N ratio
extern double manure_cn;

/// SSR: GGCMI: Manure organic fraction
extern double manure_organic_frac;

/// SSR: GGCMI: Whether to read phu sum from input file
extern bool readphu;

/// SSR: GGCMI: Whether to read pvd sum from input file
extern bool readpvd;

/// SSR: GGCMI: Whether to read growing season length from input file
extern bool readgrowseaslength;

/// SSR: GGCMI: Whether to read 2nd fertilization date from input file
extern bool readNfertdate2;

/// Whether to print multiple stands within a land cover type (except cropland) separately
extern bool printseparatestands;

/// SSR: GGCMI: Whether to do GGCMI2-specific stuff
extern bool ggcmi2;

/// SSR: GGCMI: Whether to do ISIMIP3-specific stuff
extern bool isimip3;

/// SSR: GGCMI: Whether to save per-growing-season outputs for each crop
extern bool crop_gs_out;

/// SSR: GGCMI: Use time varying Nfert (fixed_nfert=0) or Nfert of fixed_nfert_year for the whole run (fixed_nfert=1), starting with that year and onward (fixed_nfert=2), or before that year (fixed_nfert=3).
extern int fixed_nfert;
extern int fixed_nfert_year;

/// SSR: GGCMI: Skip ALL processes except for PHU and PVD calculation
extern bool just_phu_pvd;

/// SSR: Ignore file_lucrop and just evenly split among stands marked as isforpotyield?
extern bool do_potyield;

/// Whether to simulate tillage by increasing soil respiration
extern bool iftillage;

/// Use silt/sand fractions per soiltype
extern bool textured_soil;

/// Whether pastures are affected by disturbance and fire (affects pastures' npatch)
extern bool disturb_pasture;

/// Whether to simulate cropland as pasture
extern bool grassforcrop;

/// SSR: Threshold for high-soil-moisture restriction on irrigation/inundation
extern double restrict_irr_wcont;

/// SSR: Threshold high-soil-ice restriction on irrigation/inundation
extern double restrict_irr_ice;

/// SSR: Remove small amounts of water/ice in update_ice_fraction(). Previously used DEBUG_SOIL_WATER for this.
extern bool remove_smallvolfrac;

#ifdef GCP // GCP related change: allow popdens to come a different source and be fixed in a certain year
/// source for the fire population density: 1=simfire.bin, 2=netCDF within cfxinput
extern int fire_popdens_method;

/// Keep popdens level at fixed_popdens_year (only applies within cfxinput)
// 1=popdens start in year fixed_popdens_year, 2=allways use popdens of fixed_popdens_year
extern int fixed_popdens_hist;

/// Year of popdens to use if fixed_popdens_hist>0 (only applies within cfxinput)
extern int fixed_popdens_year;
#endif


//////////IMOGEN-INTERMEDIARY RELATED PARAMS  HERE DKB: 08.04.2025////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////

namespace IMOGENConfig {
    // String parameters
    extern xtring DIR_COMMON;
	extern xtring DIR_COMMON_OUT;
    extern xtring DIR_PATT;
    extern xtring DIR_CLIM;
    extern xtring FILE_SCEN_EMITS;
    extern xtring FILE_NON_CO2_VALS;
    extern xtring FILE_CH4_N2O_EMITS;
    extern xtring FILE_LPJG_FLUX;
    extern xtring FILE_GRIDLIST;
    extern xtring FILE_LPJG_CH4_N2O_FLUX;
    extern xtring FILE_SCEN_CO2_PPMV;

    // Numeric parameters
    extern int STEP_DAY;
    extern double T_OCEAN_INIT;
    extern double KAPPA_O;
    extern double F_OCEAN;
    extern double LAMBDA_L;
    extern double LAMBDA_O;
    extern double MU;
    extern double Q2CO2;
    extern double TAU_DECAY_CH4;
    extern double TAU_DECAY_N2O;

    extern int NYR_NON_CO2;
    extern int NYR_EMISS_NONCO2;
    extern int NYR_EMISS;
    extern int NYR_LPJG_FLUX;

    extern double CO2_INIT_PPMV;
    extern double CH4_INIT_PPBV;
    extern double N2O_INIT_PPBV;

    // Boolean parameters
    extern bool NONCO2_EMISSIONS;
    extern bool NONCO2_EMISSIONS_LPJG;
    extern bool C_EMISSIONS;
    extern bool LPJG_CFLUX;
    extern bool INCLUDE_CO2;
    extern bool INCLUDE_NON_CO2;
    extern bool DAILYOUT;
    extern bool LAND_FEED;
    extern bool OCEAN_FEED;
    extern bool ANLG;
    extern bool ANOM;
    extern bool REGRID;
    extern bool CO2_RF_FAIR;
    extern bool FILE_NON_CO2;

    //Other booleans
    extern bool print_imogen_output;
	extern bool include_feedback;

	//Enums
	//extern lpjgimogensimulationmode simulation_mode;
	//extern lpjgimogenfeedbackmode feedback_mode;
	extern xtring simulation_mode;
	extern xtring feedback_mode;
	extern xtring interpolation_mode;

	// [Step 8 of unified-codebase rebuild: gates ImogenOutput's per-year
	//  handshake-file writes. Values: "tight" | "prescribed" | "loose".
	//  Default at parameters.cpp is "tight". See followup F-10 in
	//  notes/FOLLOWUPS.md for the framework-loop ordering caveat that
	//  applies to "tight" in v1.0. - DKB 2026-05-06]
	extern xtring coupling_mode;

    //LPJG-IMOGEN Coupling config params
    extern int  YEAR1; //!IN First year of the numerical experiment
    extern int  IYEND;  //!IN Stop year of the ENTIRE run
    extern int  YEAR1_LPJG; //!IN First year of the whole LPJ - GUESS simulation
    extern bool SPINUP; //!IN Are we in the spin - up phase of LPJ - GUESS?
    extern bool KEEPRUNNING;	//!IN control flag to keep imogen running
    extern bool FIRSTCALL; //!IN Is this the very first call to IMOGEN from LPJ - GUESS(start of spin - up) ?

	// Scenario and year settings
	extern xtring scenario;
	extern int firstyear;
	extern int lastyear;
	extern int lpjg_start_year;
	extern int lpjg_end_year;

	// Base directories and paths
	extern xtring baseDirectory;
	extern xtring pathToLogFile;
	extern xtring myPLUMDataFilePath;
	extern xtring lpjgOutputDirectory;

	// Emission output files
	extern xtring methaneEmissionOutputFilePath;
	extern xtring entericFermentationMethaneOutputFilePath;
	extern xtring manureManagementMethaneOutputFilePath;
	extern xtring nitrogenEmissionOutputFilePath;
	extern xtring methaneNitrogenTotalOutputFilePath;

	// Fertilizer and arable lands input
	extern xtring historic_nitrogen_fertiizer_file_path;
	extern xtring arable_lands_nitrogen_fertilizer_path;

	// Wetlands data
	extern xtring wetlandsAreaFilePath;
	extern xtring wetlandsMethaneEmissionsOutputPath;

	// PLUM data paths
	extern xtring basePathPLUMdata;
	extern xtring basePathPLUMdata_v2;
	extern xtring plumFertilizerOutputPath;
	extern xtring plumFertlizerPath;

	// LPJG and emissions combined output
	extern xtring file_LPJG_IPCC_Path;
	extern xtring lpjgMethane;
	extern xtring lpjgNitrogen;
	extern xtring lpjgCflux;
	extern xtring lpjgCflux_plus_IIASA_lpjg_co2;

	// IIASA and CMIP5 data inputs
	extern xtring IIASA_lpjg_co2_file_path;
	extern xtring IIASA_non_lpjg_1850_2100;
	extern xtring IIASA_lpjg_1850_2100;

	// Additional datasets
	extern xtring livestock_counts_path;
	extern xtring fao_stats_path;

	extern xtring ssprcp;

    extern void print_all();
    
}




///////////////////////////////////////////////////////////////////////////////////////
// Settings controlling the saving and loading from state files

/// Location of state files
extern xtring state_path;

/// Whether to restart from state files
extern bool restart;

/// Whether to save state files
extern bool save_state;

/// Whether to write land use fraction data to memory; enables efficient usage of randomised gridlists for parallel simulations
// SSR: GGCMI: Moved from const bool LUTOMEMORY in indata.cpp
extern bool lutomemory;

/// Save/restart year
extern int save_year;
extern int restart_year;

/// SSR: Queues of save years
extern std::queue<int> save_years;
extern std::queue<int> save_years_remaining;

/// SSR: First and last years of forcing to use
extern int firsthistyear;
extern int lasthistyear;

/// SSR: First and last years to output results for
extern int firstoutyear;
extern int lastoutyear;

// SSR (moved from hard-coding into input code files): Minimum number of sec to wait between progress messages
extern int mutesec;

/// The level of verbosity
extern int verbosity;

/// whether to vary mort_greff smoothly with growth efficiency (1) or to use the standard step-function (0)
extern bool ifsmoothgreffmort;

/// whether establishment is limited by growing season drought
extern bool ifdroughtlimitedestab;

/// rain on wet days only (1, true), or a little every day (0, false);
extern bool ifrainonwetdaysonly;

/// whether BVOC calculations are included
extern bool ifbvoc;

///////////////////////////////////////////////////////////////////////////////////////
// Arctic and wetland inputs

/// Use the original LPJ-GUESS v4 soil scheme, or not. If true, override many of the switches below.
extern bool iftwolayersoil; 

/// Use multilayer snow scheme, or the original LPJ-GUESS v4 scheme
extern bool ifmultilayersnow;

/// whether to reduce GPP if there's inundation (1), or not (0)
extern bool ifinundationstress;

/// Whether to limit soilC decomposition below 0 degC in upland soils (1), or not (0)
extern bool ifcarbonfreeze;

/// Extra daily water input or output, in mm, to wetlands. Positive values are run ON, negative run OFF.
extern double wetland_runon;

/// Whether methane calculations are included
extern bool ifmethane;

/// Whether soil C pool input is used to update soil properties
extern bool iforganicsoilproperties;

/// Whether to take water from runoff to saturate low latitide wetlands
extern bool ifsaturatewetlands;


///////////////////////////////////////////////////////////////////////////////////////
// MF: SPITFIRE

extern bool ifburnfullcell; 						// whether to burn the full cell interpreting the burnedarea ratio as a probability
extern bool ifnesterovdistr;              		 	// Whether to distribute the monthly fires using probabilites proportional to daily Nesterov (0,1)
extern double firereturninterval; 		   			// fire return interval for fixed or random fire return regimes
extern double pixeldegree; 						// size of a pixel, used in fire
extern double sapsizedecrease;          			// in gap models Sapling size is very high and might be already outside the flame zone this gives the number to divide the sapsize by
extern int fixburnday;					   			// ! if larger than -1 prescribed fire will be applied on this day in the year
extern double fuelthreshold;						// minimum fuel required for a ptach to burn
extern double mouillotmultiplier;					// multiplier for the Mouillot data as this data is not totally trustedminimum fuel required for a ptach to burn
extern bool ifPandRresidencetime;          		// whether to use Peterson and Ryan for residence time (default is residence time from Rothermel Ros)
extern bool ifallocatebytreecover;         		// whether to allocate fire using the empirical distribution from GFED4/MODIS treecover
extern int min_days_between_burns;       			// minimum numbers of days between patches burning
extern double human_ignition_constant;				// constant in the equation for human ignitions
extern double fractionsoilmoistureinfuel;			// fraction with which to weight soil moisture with fuel moisture
extern int max_fire_duration;						// maximum fire duration (hours), zero means day length
extern int min_fire_duration;						// min fire duration (hours), zero means zero (fire can be completely suppressed)
extern bool ifpopulationsuppression; 				// whether or not to suppress fire duration based on population density
extern double lightning_ctg_factor;				// scaling factor to convert input lightning data to cloud-to-ground strikes (also potentially containing dataset-specific detection efficiency correction)
extern double crop_fraction_suppression_exponent;	// Exponential coefficient for reducing fire size as a function of crop fraction (0 = OFF, -4 = recommended)

// extern firemodetype firemode;						//the mode for burnt area/fire return interval calculation
extern ignitionmodetype ignitionmode;				//the mode for ignitions when using full SPITFIRE
extern fuelmoisturemodeltype  fuelmoisturemodel; 	// which fuel moisture model to use
extern pasturefiretype  pasturefiremode; 	// which pasture fire mode to use
extern cropfiretype  cropfiremode; 			// which crop fire mode to use
extern windlimittype windlimit; 			// which limit limitation function to use

// FireMIP
extern bool iffixedco2;					// Whether or not to hold CO2 constant at PI value
extern bool iffixedlightning;  			// Whether or not to hold lighning constant at PI values
extern bool iffixedburntarea;  			// Whether or not to hold burnt area constant at PI values
extern bool iffixedlanduse;  				// Whether or not to hold land use constant at PI values
extern bool iffixedhumanpopulation;  		// Whether or not to hold human population constant at PI values


//DKB: fert rate not summing up to 1 check, ensures warning is printed out once
extern bool fertrate_error;

///////////////////////////////////////////////////////////////////////////////////////
// The Paramlist class (and Paramtype)
//

/// Represents one custom "param" item
/** \see Paramlist */
struct Paramtype {
	xtring name;
	xtring str;
	double num;
};

/// List for the "custom" parameters
/** Functionality for storing and retrieving custom "param" items from the instruction
 *  script. "Custom" parameters can be accessed by other modules without the need to
 *  define them beforehand. This of course also means there is no help text associated
 *  with these parameters, so the user can't get any documentation about them from
 *  the command line.
 *
 * Custom keywords may be included in the instruction script using syntax similar to
 * the following examples:
 *
 * \code
 *     param "co2" (num 340)
 *     param "file_gridlist" (str "gridlist.txt")
 * \endcode
 *
 * To retrieve the values associated with the "param" strings in the above examples,
 * use the following function calls (may appear anywhere in this file; instruction
 * script must have been read in first):
 *
 * \code
 *     param["co2"].num
 *     param["file_gridlist"].str
 * \endcode
 *
 * Each "param" item can store EITHER a number (int or double) OR a string, but not
 * both types of data. Function fail is called to terminate output if a "param" item
 * with the specified identifier was not read in.
 */
class Paramlist : public ListArray<Paramtype> {

public:
	/// Adds a parameter with a numeric value, overwriting if it already existed
	void addparam(xtring name,xtring value);

	/// Adds a parameter with a string value, overwriting if it already existed
	void addparam(xtring name,double value);

	/// Fetches a parameter from the list, aborts the program if it didn't exist
	Paramtype& operator[](xtring name);

	/// Tests if param exists
	bool isparam(xtring name);

	/// Tries to find the parameter in the list
	/** \returns 0 if it wasn't there. */
	Paramtype* find(xtring name);
};

/// The global Paramlist object
/** Contains all the custom parameters after reading in the instruction file */
extern Paramlist param;

/// Reads in the instruction file
/** Uses PLIB library functions to read instructions from file specified by
 * 'insfilename'.
 */
void read_instruction_file(const char* insfilename);

/// Displays documentation about the instruction file parameters to the user
void printhelp();


///////////////////////////////////////////////////////////////////////////////////////
// Interface for declaring parameters from other modules

/// Declares an xtring parameter
/** \param name     The name of the parameter
 *  \param param    Pointer to variable where the value of the parameter is to be placed
 *  \param maxlen   Maximum allowed length of the parameter in the ins file
 *  \param help     Documentation describing the parameter to the user
 */
void declare_parameter(const char* name, xtring* param, int maxlen, const char* help = "");

/// Declares a std:string parameter
/** \param name     The name of the parameter
 *  \param param    Pointer to variable where the value of the parameter is to be placed
 *  \param maxlen   Maximum allowed length of the parameter in the ins file
 *  \param help     Documentation describing the parameter to the user
 */
void declare_parameter(const char* name, std::string* param, int maxlen, const char* help = "");

/// Declares an int parameter
/** \param name     The name of the parameter
 *  \param param    Pointer to variable where the value of the parameter is to be placed
 *  \param min      Minimum allowed value of the parameter in the ins file
 *  \param max      Maximum allowed value of the parameter in the ins file
 *  \param help     Documentation describing the parameter to the user
 */
void declare_parameter(const char* name, int* param, int min, int max, const char* help = "");

/// Declares a double parameter
/** \param name     The name of the parameter
 *  \param param    Pointer to variable where the value of the parameter is to be placed
 *  \param min      Minimum allowed value of the parameter in the ins file
 *  \param max      Maximum allowed value of the parameter in the ins file
 *  \param help     Documentation describing the parameter to the user
 */
void declare_parameter(const char* name, double* param, double min, double max, const char* help = "");

/// Declares a bool parameter
/** \param name     The name of the parameter
 *  \param param    Pointer to variable where the value of the parameter is to be placed
 *  \param help     Documentation describing the parameter to the user
 */
void declare_parameter(const char* name, bool* param, const char* help = "");

#endif // LPJ_GUESS_PARAMETERS_H
