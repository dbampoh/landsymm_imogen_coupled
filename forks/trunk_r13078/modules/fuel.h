///////////////////////////////////////////////////////////////////////////////////////
// MODULE HEADER FILE
//
// Module:                Fuel: fuel complex and fuel constants
// Header file name:      fuel.h
// Source code file name: fuel.cpp
// Written by:            Matthew Forrest
// Version dated:         2020-03-27
//
// WHAT SHOULD THIS FILE CONTAIN?
// Module header files need normally contain only declarations of functions defined in
// the module that are to be accessible to the calling framework or to other modules.
#ifndef LPJ_GUESS_FUEL_H
#define LPJ_GUESS_FUEL_H

// GLOBAL FUEL-RELATED CONSTANTS FOR SPITFIRE

// constants to partition wood into 1, 10, 100 and 1000 hour fuel classes
// revised value based on analysis of Pettinari fuel bed dataset (original values commented out)
const double wood_fraction_1hr = 0.023; // 0.045;
const double wood_fraction_10hr = 0.047; //0.075;
const double wood_fraction_100hr = 0.063; // 0.27;
const double wood_fraction_1000hr = 0.867; // 0.61;
const double wood_fraction_1_10_100hr = wood_fraction_1hr + wood_fraction_10hr + wood_fraction_100hr;

// surface to volume (cm^2/cm^3) of different fuel classes
// For 1hr fuel initial SPITFIRE sigma value was 66.0 which was representative of the average of 1hr fuels (leaves and twigs).
// Since leaves now have their own sigma, the value below is for 1/8" stick (see Wilson 1990)
const double sigma_1hr = 15.0;  // old 66.0
const double sigma_10hr = 3.58;
const double sigma_100hr = 0.98;
const double sigma_1000hr = 0.5;

//scalar to transform FBD of 10hr(100hr) fuels in to 1hr (not sure where these exactly came from)
const double fbd_a = 1.2;
const double fbd_b = 1.4;


// caloric heat content of litter (used in intensity calculations)
const double H = 18000.;

// conversion factor drymass to carbon
const double DM_C = 0.45;



// -------------------------------------------------------------------------------
// --------------------- Fuel class for SPITFIRE ---------------------------------
// -------------------------------------------------------------------------------
//
// Note: This class is just begging be set up properly with methods and private method variables etc.
//       This would allow considerable simplification of the rather large "spitfire.cpp" file
//       as well as nice conceptual separation. But that is not a priority for right now.

class Fuel_patch {

// MF: All variables in gDM as that is needed for Rothermel
// MF: char_<variable> refers to the characteristic for that patch, the weighted average of the dead fuel and live grass

public:

	// Miminal constructor, just need to make sure days_since_last_burn is initialised to zero
	Fuel_patch() {

		// Total fuel for patch
		fuel_1hr_gDM = 0.0;
		fuel_10hr_gDM = 0.0;
		fuel_100hr_gDM = 0.0;
		fuel_1000hr_gDM = 0.0;
		fuel_livegrass_gDM = 0.0;

		// Fuel consumed
		fuel_consumed_1hr_gDM = 0.0;
		fuel_consumed_10hr_gDM = 0.0;
		fuel_consumed_100hr_gDM = 0.0;
		fuel_consumed_1000hr_gDM = 0.0;
		fuel_consumed_livegrass_gDM = 0.0;

		// Fraction of fuel consumed
		fraction_consumed_1hr = 0.0;
		fraction_consumed_10hr = 0.0;
		fraction_consumed_100hr = 0.0;
		fraction_consumed_1000hr = 0.0;
		fraction_consumed_livegrass = 0.0;

		// Litter and fuel sums
		deadfuel_gDM = 0.0;  // MF This is just the 1hr, 10hr and 100hr fuel used for Rothermel ROS
		net_deadfuel_gDM = 0.0;
		char_net_fuel_gDM = 0.0;

		// total grass biomass for Hoffman et al. 2012 calculation of FBD (note in kg)
		total_grass_biomass_kgDM = 0.0;

		// Characterisitic fuel properties
		char_FBD = 0.0;
		char_MoE = 0.0;
		char_sigma = 0.0;


		// Daily litter moisture content
		dlm_livegrass = 0.0;
		dlm_1hr = 0.0;
		dlm_10hr = 0.0;
		dlm_100hr = 0.0;
		dlm_1000hr = 0.0;
		char_dlm = 0.0;	// characteristic daily litter moisture  -MF does currently include livegrass

		// Patch-level fire properties
		fdi = 0.0;
		effective_wind = 0.0;
		ros_f = 0.0;
		ros_b = 0.0;
		fire_durat = 0.0;
		gamma_f = 0.0;
		mw_weight = 0.0;
		fuel_consumed_CE_litter = 0.0;
		fuel_consumed_CE_grass = 0.0;
		CE = 0.0;
		daily_fire_intensity = 0.0;
		tau_l = 0.0;
		scorch_height = 0.0;
		fire_size = 0.0; // ha
		potential_human_ign = 0.0;
		potential_lightning_ign = 0.0;

		// MF new test
		burn_probability = 0.0;



		// for averaging across patching and outputting
		daily_number_fires = 0.0;
		for (int m = 0; m < 12; m++) {

			monthly_fire_intensity[m] = 0.0;
			monthly_RoS[m] = 0.0;
			monthly_fire_durat[m] = 0.0;
			monthly_tau_l[m] = 0.0;
			monthly_scorch_height[m] = 0.0;

			monthly_fire_size[m] = 0.0;
			monthly_human_ignitions[m] = 0.0;
			monthly_lightning_ignitions[m] = 0.0;

			monthly_livegrass_fuel[m] = 0.0;
			monthly_1hr_fuel[m] = 0.0;
			monthly_10hr_fuel[m] = 0.0;
			monthly_100hr_fuel[m] = 0.0;
			monthly_1000hr_fuel[m] = 0.0;

			monthly_livegrass_fm[m] = 0.0;
			monthly_1hr_fm[m] = 0.0;
			monthly_10hr_fm[m] = 0.0;
			monthly_100hr_fm[m] = 0.0;
			monthly_1000hr_fm[m] = 0.0;

			monthly_livegrass_cc[m] = 0.0;
			monthly_1hr_cc[m] = 0.0;
			monthly_10hr_cc[m] = 0.0;
			monthly_100hr_cc[m] = 0.0;
			monthly_1000hr_cc[m] = 0.0;

			monthly_realised_livegrass_cc[m] = 0.0;
			monthly_realised_1hr_cc[m] = 0.0;
			monthly_realised_10hr_cc[m] = 0.0;
			monthly_realised_100hr_cc[m] = 0.0;
			monthly_realised_1000hr_cc[m] = 0.0;

			monthly_FBD[m] = 0.0;
			monthly_SAV[m] = 0.0;
			monthly_MoE[m] = 0.0;
			monthly_DFM[m] = 0.0;
			monthly_effective_windspeed[m] = 0.0;

			monthly_number_fires[m] = 0.0;
			monthly_realised_intensity[m] = 0.0;
			monthly_realised_nesterov[m] = 0.0;
			monthly_realised_duration[m] = 0.0;
			monthly_realised_residence_time[m] = 0.0;
			monthly_realised_scorch_height[m] = 0.0;
			monthly_realised_fire_size[m] = 0.0;

			monthly_nind_killed[m] = 0.0;
			mtreecover_reduction_fire[m] = 0.0;


			//  Nesterov index
			monthly_Nesterov[m] = 0.0;
			monthly_FDI[m] = 0.0;
			monthly_burn_prob[m] = 0.0;

			monthly_burned_area_BareSoil[m] = 0.0;

		}


		// for distributing fires across patches
		// currently this code is not maintained
		FPC_high = 0.0;
		possible = 0.0;
		fire_prob = false;
		unnormalised_fire_prob = 0.0;

		for (int d = 0; d < 265; d++) {
			mean_PI_BA[d] = 0.0;
		}


	}

	// Total fuel for patch
	double fuel_1hr_gDM;
	double fuel_10hr_gDM;
	double fuel_100hr_gDM;
	double fuel_1000hr_gDM;
	double fuel_livegrass_gDM;

	// Fuel consumed
	double fuel_consumed_1hr_gDM;
	double fuel_consumed_10hr_gDM;
	double fuel_consumed_100hr_gDM;
	double fuel_consumed_1000hr_gDM;
	double fuel_consumed_livegrass_gDM;

	// Fraction of fuel consumed
	double fraction_consumed_1hr;
	double fraction_consumed_10hr;
	double fraction_consumed_100hr;
	double fraction_consumed_1000hr;
	double fraction_consumed_livegrass;

	// Litter and fuel sums
	double deadfuel_gDM;  // MF This is just the 1hr, 10hr and 100hr fuel used for Rothermel ROS
	double net_deadfuel_gDM;
	double char_net_fuel_gDM;

	// total grass biomass for Hoffman et al. 2012 calculation of FBD (note in kg)
	double total_grass_biomass_kgDM;

	// Characterisitic fuel properties
	double char_FBD;
	double char_MoE;
	double char_sigma;


	// Daily litter moisture content
	double dlm_livegrass;
	double dlm_1hr;
	double dlm_10hr;
	double dlm_100hr;
	double dlm_1000hr;
	double char_dlm;	// characteristic daily litter moisture  -MF does currently include livegrass

	// Patch-level fire properties
	double fdi;
	double effective_wind;
	double ros_f;
	double ros_b;
	double fire_durat;
	double gamma_f;
	double mw_weight;
	double fuel_consumed_CE_litter;
	double fuel_consumed_CE_grass;
	double CE;
	double daily_fire_intensity;
	double tau_l;
	double scorch_height;
	double fire_size; // ha
	double potential_human_ign;
	double potential_lightning_ign;

	// MF new test
	double burn_probability;



	// for averaging across patching and outputting
	double daily_number_fires;


	double monthly_fire_intensity[12];
	double monthly_RoS[12];
	double monthly_fire_durat[12];
	double monthly_tau_l[12];
	double monthly_scorch_height[12];

	double monthly_fire_size[12]; // km2 for output
	double monthly_human_ignitions[12];
	double monthly_lightning_ignitions[12];
	double monthly_human_potential_ignitions[12];
	double monthly_lightning_potential_ignitions[12];


	double monthly_livegrass_fuel[12];
	double monthly_1hr_fuel[12];
	double monthly_10hr_fuel[12];
	double monthly_100hr_fuel[12];
	double monthly_1000hr_fuel[12];

	double monthly_livegrass_fm[12];
	double monthly_1hr_fm[12];
	double monthly_10hr_fm[12];
	double monthly_100hr_fm[12];
	double monthly_1000hr_fm[12];

	double monthly_livegrass_cc[12];
	double monthly_1hr_cc[12];
	double monthly_10hr_cc[12];
	double monthly_100hr_cc[12];
	double monthly_1000hr_cc[12];

	double monthly_realised_livegrass_cc[12];
	double monthly_realised_1hr_cc[12];
	double monthly_realised_10hr_cc[12];
	double monthly_realised_100hr_cc[12];
	double monthly_realised_1000hr_cc[12];

	double monthly_FBD[12];
	double monthly_SAV[12];
	double monthly_MoE[12];
	double monthly_DFM[12];
	double monthly_effective_windspeed[12];

		double monthly_number_fires[12];
	double monthly_realised_intensity[12];
	double monthly_realised_nesterov[12];
	double monthly_realised_duration[12];
	double monthly_realised_residence_time[12];
	double monthly_realised_scorch_height[12];
	double monthly_realised_fire_size[12];
	double monthly_realised_fire_speed[12];
	double monthly_realised_RoS[12];
	double monthly_realised_DFM[12];


	double monthly_nind_killed[12];
	double mtreecover_reduction_fire[12];


	//  Nesterov index
	double monthly_Nesterov[12];
	double monthly_FDI[12];
	double monthly_burn_prob[12];

	// assigning burned area to "BareSoil" in case of no vegetation
	double monthly_burned_area_BareSoil[12];


	// for distributing fires across patches
	// currently this code is not maintained
	double FPC_high;
	bool possible;
	double fire_prob;
	double unnormalised_fire_prob;


	double mean_PI_BA[365];


};




#endif ///LPJ_GUESS_FUEL_H
