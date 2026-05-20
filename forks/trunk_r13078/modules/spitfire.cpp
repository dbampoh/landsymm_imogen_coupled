///////////////////////////////////////////////////////////////////////////////////////
// MODULE SOURCE CODE FILE
//
// Module:                SPITFIRE: calculation of burned area, fluxes and burned biomass
//                        Version adapted from Spitfire fortran version 2006 by
// 						  Kirsten Thonicke and Allan Spessa
// Header file name:      spitfire.h requires also spitfire_io.h
// Source code file name: spitfire.cpp
// Written by:            Veiko Lehsten
// Re-written by:		  Matthew Forrest
// Version dated:         2012.09.20
//
//
// WHAT SHOULD THIS FILE CONTAIN?
// Module source code files should contain, in this order:
//   (1) a "#include" directive naming the framework header file. The framework header
//       file should define all classes used as arguments to functions in the present
//       module. It may also include declarations of global functions, constants and
//       types, accessible throughout the model code;
//   (2) other #includes, including header files for other modules accessed by the
//       present one;
//   (3) type definitions, constants and file scope global variables for use within
//       the present module only;
//   (4) declarations of functions defined in this file, if needed;
//   (5) definitions of all functions. Functions that are to be accessible to other
//       modules or to the calling framework should be declared in the module header
//       file.
//
// PORTING MODULES BETWEEN FRAMEWORKS:
// Modules should be structured so as to be fully portable between models (frameworks).
// When porting between frameworks, the only change required should normally be in the
// "#include" directive referring to the framework header file.
//
// 2012.09.25 	MF:  I basically ignored this and ended up integrating LPJ-GUESS and SPITFIRE rather tightly.
//      		Specifically, SPITFIRE now depends on heavily on the guess framework for its data structures,
//  			and objects of type Fuel_Patch and Fuel_PFT must be initialised in guess.h (included via spitfire_classes.h)

#include "guess.h"
#include "config.h"
#include "driver.h"  // MF - required for randfrac()
#include "spitfire.h"
#include "vegdynam.h" // MF - required for establish()


// Require 50kW/m surface intensity for a spreading fire cf. original SPITFIRE
// TODO consider making this an external parameter that can be tuned/adjusted
const double min_daily_intensity = 50;



/// Help function for reduce_biomass(), partitions nstore into leafs and roots
/**
 *  As leaf and roots can have a very low N concentration after growth and allocation,
 *  N in nstore() is split between them to saticfy relationship between their average C:N ratios
 */
void nstore_adjust_spitfire(double& cmass_leaf,double& cmass_root, double& nmass_leaf, double& nmass_root,
		double nstore, double cton_leaf, double cton_root) {

	// (1) cmass_leaf / ((nmass_leaf + leaf_ndemand) * cton_leaf) = cmass_root / ((nmass_root + root_ndemand) * cton_root)
	// (2) leaf_ndemand + root_ndemand = nstore

	// (1) + (2) leaf_ndemand = (cmass_leaf * ratio (nmass_root + nstore) - cmass_root * nmass_leaf) / (cmass_root + cmass_leaf * ratio)
	//
	// where ratio = cton_root / cton_leaf

	double ratio = cton_root / cton_leaf;

	double leaf_ndemand = (cmass_leaf * ratio * (nmass_root + nstore) - cmass_root * nmass_leaf) / (cmass_root + cmass_leaf * ratio);
	double root_ndemand = nstore - leaf_ndemand;

	nmass_leaf += leaf_ndemand;
	nmass_root += root_ndemand;
}

///////////////////////////////////////////////////////////////////////////////////////
// report_spitfire_fluxes - INTERNAL FUNCTION


void report_spitfire_fluxes_standard(Patch& patch, double cflux_fire, double nflux_fire) {

	// Total C flux from fire
	patch.fluxes.report_flux(Fluxes::FIREC, cflux_fire);

	// Report N fluxes in the standard way
	patch.fluxes.report_flux(Fluxes::NH3_FIRE, Fluxes::NH3_FIRERATIO * nflux_fire);
	patch.fluxes.report_flux(Fluxes::NOx_FIRE, Fluxes::NOx_FIRERATIO * nflux_fire);
	patch.fluxes.report_flux(Fluxes::N2O_FIRE, Fluxes::N2O_FIRERATIO * nflux_fire);
	patch.fluxes.report_flux(Fluxes::N2_FIRE,  Fluxes::N2_FIRERATIO  * nflux_fire);

	//if(cflux_fire > 0.00001) dprintf("Year = %i, day = %i, Reporting total flux = %.20f\n", date.get_calendar_year(), date.day, cflux_fire);
}



void report_spitfire_fluxes_other(Patch& patch, double cflux_fire, double em_CO2, double em_CO, double em_CH4, double em_TPM, double em_VOC) {

	// Oxidised and reduced C
	patch.fluxes.report_flux(Fluxes::CO2_FIRE, cflux_fire / DM_C * em_CO2 / 1000);
	patch.fluxes.report_flux(Fluxes::CO_FIRE, cflux_fire / DM_C * em_CO / 1000);
	patch.fluxes.report_flux(Fluxes::CH4_FIRE, cflux_fire / DM_C * em_CH4 / 1000); // kg species/m2

	// Oxidised and reduced C from Scholes (or something)
	patch.fluxes.report_flux(Fluxes::CO2s_FIRE, 1830 * patch.fuel.CE * cflux_fire / DM_C);
	patch.fluxes.report_flux(Fluxes::COs_FIRE, (1142 - patch.fuel.CE * 1141) * cflux_fire / DM_C);
	patch.fluxes.report_flux(Fluxes::CH4s_FIRE, (51.5 - patch.fuel.CE * 52.4) * cflux_fire / DM_C); // kg species/m2

	// Other species
	patch.fluxes.report_flux(Fluxes::TPM_FIRE,   cflux_fire / DM_C * em_TPM / 1000);
	patch.fluxes.report_flux(Fluxes::VOC_FIRE,   cflux_fire / DM_C * em_VOC / 1000);

}


void report_spitfire_fluxes_pft(Patch& patch, int pft_id, double cflux_fire, double nflux_fire) {

	// report standard fluxes (not PFT dependent)
	report_spitfire_fluxes_standard(patch, cflux_fire, nflux_fire);

	// report other fluxes (PFT dependent emission factors)
	report_spitfire_fluxes_other(patch, cflux_fire, pftlist[pft_id].em_CO2, pftlist[pft_id].em_CO, pftlist[pft_id].em_CH4, pftlist[pft_id].em_TPM, pftlist[pft_id].em_VOC);

	// report the per-PFT flux (note that this is a per PFT version of the standard FIREC flux, so they should/can be checked against each other)
	patch.fluxes.report_flux(Fluxes::C_FIRE, pft_id, cflux_fire);

	// if(cflux_fire > 0.00001) dprintf("Year = %i, day = %i, Reporting %i flux = %.20f\n", date.get_calendar_year(), date.day, pft_id, cflux_fire);


}


/////////////////////////////////////////////////////////////////////////////////////////
// SET CHARACTERISTIC SOM POOLS TO A STANDARD VALUE
// Sometimes an SOM pool will have zero or very small cmass.  In such a case this function is called to see all the
// characteristic fuel values and fluxes for that SOM pool to some standard values.  The actual values don't matter too much
// (since they will be weighted with zero or a very small number), but they should be set to something sensible to avoid triggering
// error messages ot maybe doing something else weird

void set_standard_SOM_values(Sompool& pool ){

	// intermediate values
	pool.moistureofextinction = 0.25;
	pool.fuelbulkdensity = 10.0;
	pool.surfacetovolume = 66;

	// values for C4G ('cos why not?)
	pool.em_CO2 = 1568.0;
	pool.em_CO = 106.0;
	pool.em_CH4 = 4.80;
	pool.em_VOC = 5.70;
	pool.em_TPM = 17.60;

}



/////////////////////////////////////////////////////////////////////////////////////////
//  DAILY SUMS
// MF Sums the daily patch fire variables and averages them if it is the last day of the month
// Should only be called ONCE per day

void spitfire_daily_sums(Patch& patch, double calculated_fire_fraction) {

	// If first day of year reset the total C burned for each PFT
	if (date.day == 0) {

		// zero the total annual C consumed array
		patch.pft.firstobj();
		while (patch.pft.isobj) {
			Patchpft& patchpft = patch.pft.getobj();
			patchpft.annual_fuel_consumed_gC = 0.0;
			for (int m = 0; m < 12; m++) {
				patchpft.monthly_ba_frac[m] = 0.0;
			}
			patch.pft.nextobj();
		}

	}

	if (date.dayofmonth == 0) {
		patch.fuel.monthly_fire_intensity[date.month] = 0;
		patch.fuel.monthly_RoS[date.month] = 0;

		patch.fuel.monthly_livegrass_fuel[date.month] = 0;
		patch.fuel.monthly_1hr_fuel[date.month] = 0;
		patch.fuel.monthly_10hr_fuel[date.month] = 0;
		patch.fuel.monthly_100hr_fuel[date.month] = 0;
		patch.fuel.monthly_1000hr_fuel[date.month] = 0;

		patch.fuel.monthly_livegrass_fm[date.month] = 0;
		patch.fuel.monthly_1hr_fm[date.month] = 0;
		patch.fuel.monthly_10hr_fm[date.month] = 0;
		patch.fuel.monthly_100hr_fm[date.month] = 0;
		patch.fuel.monthly_1000hr_fm[date.month] = 0;

		patch.fuel.monthly_livegrass_cc[date.month] = 0;
		patch.fuel.monthly_1hr_cc[date.month] = 0;
		patch.fuel.monthly_10hr_cc[date.month] = 0;
		patch.fuel.monthly_100hr_cc[date.month] = 0;
		patch.fuel.monthly_1000hr_cc[date.month] = 0;

		patch.fuel.monthly_fire_durat[date.month] = 0;
		patch.fuel.monthly_tau_l[date.month] = 0;
		patch.fuel.monthly_scorch_height[date.month] = 0;

		patch.fuel.monthly_FBD[date.month] = 0;
		patch.fuel.monthly_SAV[date.month] = 0;
		patch.fuel.monthly_MoE[date.month] = 0;
		patch.fuel.monthly_DFM[date.month] = 0;
		patch.fuel.monthly_effective_windspeed[date.month] = 0;

		// These are incrememented in the main SPITFIRE routine
		patch.fuel.monthly_lightning_ignitions[date.month] = 0;
		patch.fuel.monthly_human_ignitions[date.month] = 0;
		patch.fuel.monthly_lightning_potential_ignitions[date.month] = 0;
		patch.fuel.monthly_human_potential_ignitions[date.month] = 0;
		patch.fuel.monthly_fire_size[date.month] = 0;

		patch.fuel.monthly_nind_killed[date.month] = 0;
		patch.fuel.mtreecover_reduction_fire[date.month] = 0;


		patch.fuel.monthly_Nesterov[date.month] = 0;
		patch.fuel.monthly_FDI[date.month] = 0;
		patch.fuel.monthly_burn_prob[date.month] = 0;

		patch.fuel.monthly_burned_area_BareSoil[date.month] = 0;


	}

	double to_gridcell_average = patch.stand.get_gridcell_fraction() / (double)patch.stand.npatch();


	// report perPFT monthly burnt area (using Fluxes machinery, cf. gcpoutput)
	// BA is allocated to PFTs based on their fpc, so first calculate total fpc
	double total_fpc = 0.0;
	Vegetation& vegetation = patch.vegetation;
	for(unsigned int k = 0; k < vegetation.nobj; k++) {
		Individual& indiv = vegetation[k];
		if(indiv.alive) total_fpc += indiv.fpc;
	}


	// If total_fpc is negligible allocate all burned are to "BareSoil" output file
	if(negligible(total_fpc, -8)) {
		patch.fuel.monthly_burned_area_BareSoil[date.month] += calculated_fire_fraction;
	}
	// else report burnt area per PFT proportional to fpc
	else {

		// first check that the total fpc is greater than the burnt fraction,
		// if it is not, allocate the excess to BareSoil
		double fire_fraction_in_vegetation = calculated_fire_fraction;
		if(calculated_fire_fraction > total_fpc){
			patch.fuel.monthly_burned_area_BareSoil[date.month] += (calculated_fire_fraction  - total_fpc);
			fire_fraction_in_vegetation = total_fpc;
		}

		// and now report the BA depending on the fpc
		// this needs to be done per individual
		double total_fire_fraction = 0.0;
		for(unsigned int k = 0; k < vegetation.nobj; k++) {
			Individual& indiv = vegetation[k];
			indiv.report_flux(Fluxes::BA, fire_fraction_in_vegetation * indiv.fpc / total_fpc);
		}

	}




	// This factor weights this patch's contribution to the property *given* its contriubtion to the flammable area
	// ( calculated on the first day of the year in dailyaccounting_gridcell_spitfire().
	double  to_gridcell_average_flammable_only = patch.to_gridcell_average_flammable_only;

	// Fuel loading (per m2 basis in this patch, not conversion factor)
	patch.fuel.monthly_livegrass_fuel[date.month] += patch.fuel.fuel_livegrass_gDM * to_gridcell_average_flammable_only;
	patch.fuel.monthly_1hr_fuel[date.month] += patch.fuel.fuel_1hr_gDM * to_gridcell_average_flammable_only;
	patch.fuel.monthly_10hr_fuel[date.month] += patch.fuel.fuel_10hr_gDM * to_gridcell_average_flammable_only;
	patch.fuel.monthly_100hr_fuel[date.month] += patch.fuel.fuel_100hr_gDM * to_gridcell_average_flammable_only;
	patch.fuel.monthly_1000hr_fuel[date.month] += patch.fuel.fuel_1000hr_gDM * to_gridcell_average_flammable_only;

	// Fuel moisture
	patch.fuel.monthly_livegrass_fm[date.month] += patch.fuel.dlm_livegrass * to_gridcell_average_flammable_only;
	patch.fuel.monthly_1hr_fm[date.month] += patch.fuel.dlm_1hr * to_gridcell_average_flammable_only;
	patch.fuel.monthly_10hr_fm[date.month] += patch.fuel.dlm_10hr * to_gridcell_average_flammable_only;
	patch.fuel.monthly_100hr_fm[date.month] += patch.fuel.dlm_100hr * to_gridcell_average_flammable_only;
	patch.fuel.monthly_1000hr_fm[date.month] += patch.fuel.dlm_1000hr * to_gridcell_average_flammable_only;

	// Combustion completeness
	patch.fuel.monthly_livegrass_cc[date.month] += patch.fuel.fraction_consumed_livegrass * to_gridcell_average_flammable_only ;
	patch.fuel.monthly_1hr_cc[date.month] += patch.fuel.fraction_consumed_1hr * to_gridcell_average_flammable_only;
	patch.fuel.monthly_10hr_cc[date.month] += patch.fuel.fraction_consumed_10hr * to_gridcell_average_flammable_only;
	patch.fuel.monthly_100hr_cc[date.month] += patch.fuel.fraction_consumed_100hr * to_gridcell_average_flammable_only;
	patch.fuel.monthly_1000hr_cc[date.month] += patch.fuel.fraction_consumed_1000hr* to_gridcell_average_flammable_only;

	// Fire properties (note they area weighted be the patch's contribution to the flammable area not the actual number of fires,
	// to get a representative properties of the actual firess ee the "realised_xxx_" variables"
	patch.fuel.monthly_fire_intensity[date.month] += patch.fuel.daily_fire_intensity * to_gridcell_average_flammable_only;
	patch.fuel.monthly_RoS[date.month] += patch.fuel.ros_f * to_gridcell_average_flammable_only;
	patch.fuel.monthly_fire_durat[date.month] += patch.fuel.fire_durat * to_gridcell_average_flammable_only;
	patch.fuel.monthly_tau_l[date.month] += patch.fuel.tau_l * to_gridcell_average_flammable_only;
	patch.fuel.monthly_scorch_height[date.month] += patch.fuel.scorch_height * to_gridcell_average_flammable_only;

	// Characteristic fuel properties
	patch.fuel.monthly_FBD[date.month] += patch.fuel.char_FBD * to_gridcell_average_flammable_only; // kgDM/m^3
	patch.fuel.monthly_SAV[date.month] += patch.fuel.char_sigma * to_gridcell_average_flammable_only;
	patch.fuel.monthly_MoE[date.month] += patch.fuel.char_MoE * to_gridcell_average_flammable_only;
	patch.fuel.monthly_DFM[date.month] += patch.fuel.char_dlm * to_gridcell_average_flammable_only;

	//dprintf("FBD NAN: ACCUM: (%.2f, %.2f): Year = %i, Day = %i, : patch = %i, patch.fuel.monthly_FBD[date.month] = %f, patch.fuel.char_FBD =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, patch.id, patch.fuel.monthly_FBD[date.month], patch.fuel.char_FBD);

	// Misc. climate indexes etc
	patch.fuel.monthly_effective_windspeed[date.month] += patch.fuel.effective_wind * to_gridcell_average_flammable_only;
	patch.fuel.monthly_Nesterov[date.month] += patch.stand.get_gridcell().climate.gridcell.nesterov_cur * to_gridcell_average_flammable_only;
	patch.fuel.monthly_FDI[date.month] += patch.fuel.fdi * to_gridcell_average_flammable_only;
	patch.fuel.monthly_burn_prob[date.month] += patch.fuel.burn_probability * to_gridcell_average_flammable_only;

	// Ignitions - scaled to gridcell area in out_annual()
	patch.fuel.monthly_human_ignitions[date.month] += patch.fuel.potential_human_ign * patch.fuel.fdi;
	patch.fuel.monthly_lightning_ignitions[date.month] += patch.fuel.potential_lightning_ign * patch.fuel.fdi;
	patch.fuel.monthly_human_potential_ignitions[date.month] += patch.fuel.potential_human_ign;
	patch.fuel.monthly_lightning_potential_ignitions[date.month] += patch.fuel.potential_lightning_ign;



	if (date.islastday) {

		double days_in_month = (double) date.ndaymonth[date.month];

		patch.fuel.monthly_fire_intensity[date.month] /= days_in_month;
		patch.fuel.monthly_RoS[date.month] /= days_in_month;

		patch.fuel.monthly_livegrass_fuel[date.month] /= days_in_month;
		patch.fuel.monthly_1hr_fuel[date.month] /= days_in_month;
		patch.fuel.monthly_10hr_fuel[date.month] /= days_in_month;
		patch.fuel.monthly_100hr_fuel[date.month] /= days_in_month;
		patch.fuel.monthly_1000hr_fuel[date.month] /= days_in_month;

		patch.fuel.monthly_livegrass_fm[date.month] /= days_in_month;
		patch.fuel.monthly_1hr_fm[date.month] /= days_in_month;
		patch.fuel.monthly_10hr_fm[date.month] /= days_in_month;
		patch.fuel.monthly_100hr_fm[date.month] /= days_in_month;
		patch.fuel.monthly_1000hr_fm[date.month] /= days_in_month;

		patch.fuel.monthly_livegrass_cc[date.month] /= days_in_month;
		patch.fuel.monthly_1hr_cc[date.month] /= days_in_month;
		patch.fuel.monthly_10hr_cc[date.month] /= days_in_month;
		patch.fuel.monthly_100hr_cc[date.month] /= days_in_month;
		patch.fuel.monthly_1000hr_cc[date.month] /= days_in_month;

		// convert to kgC/m^2 from gDM/m^2 for consistency with the rest of the guess output
		patch.fuel.monthly_livegrass_fuel[date.month] *= DM_C / 1000;
		patch.fuel.monthly_1hr_fuel[date.month] *= DM_C / 1000;
		patch.fuel.monthly_10hr_fuel[date.month] *= DM_C / 1000;
		patch.fuel.monthly_100hr_fuel[date.month] *= DM_C / 1000;
		patch.fuel.monthly_1000hr_fuel[date.month] *= DM_C / 1000;

		patch.fuel.monthly_fire_durat[date.month] /= days_in_month;
		patch.fuel.monthly_tau_l[date.month] /= days_in_month;
		patch.fuel.monthly_scorch_height[date.month] /= days_in_month;

		patch.fuel.monthly_FBD[date.month] /= days_in_month;
		patch.fuel.monthly_SAV[date.month] /= days_in_month;
		patch.fuel.monthly_MoE[date.month] /= days_in_month;
		patch.fuel.monthly_DFM[date.month] /= days_in_month;
		patch.fuel.monthly_effective_windspeed[date.month] /= days_in_month;

		patch.fuel.monthly_lightning_ignitions[date.month] /= days_in_month;
		patch.fuel.monthly_human_ignitions[date.month] /= days_in_month;
		patch.fuel.monthly_lightning_potential_ignitions[date.month] /= days_in_month;
		patch.fuel.monthly_human_potential_ignitions[date.month] /= days_in_month;
		patch.fuel.monthly_fire_size[date.month] /= days_in_month;

		patch.fuel.monthly_Nesterov[date.month] /= days_in_month;
		patch.fuel.monthly_FDI[date.month] /= days_in_month;
		patch.fuel.monthly_burn_prob[date.month] /= days_in_month;

	}
}

/////////////////////////////////////////////////////////////////////////////////////////
// FIRE DAY SUMS
// Accumulated fire properties, weighted by fraction (and scaled by
// Should only be called ONCE per day

void tally_fire_properties(Patch& patch, double Nesterov) {

	// These values are for the *actual fires simulated* with each fire being weighted equally (the number of fires should be weighted by land cover class though)
	// Therefore per-patch values need to be accumulated to the gridcell level by multiply by the number of fires
	// (after that they need to be divided by the total number of fires in the month)

	// This scaling factor is the number of fires scaled to the gridcell level
	double daily_number_of_fires_scaled = patch.fuel.daily_number_fires * patch.stand.get_gridcell_fraction() / (double) patch.stand.nobj;


	patch.fuel.monthly_number_fires[date.month] += daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_intensity[date.month] += patch.fuel.daily_fire_intensity * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_nesterov[date.month] += Nesterov * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_duration[date.month] += patch.fuel.fire_durat * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_residence_time[date.month] += patch.fuel.tau_l * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_scorch_height[date.month] += patch.fuel.scorch_height * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_fire_size[date.month] += patch.fuel.fire_size * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_livegrass_cc[date.month] += patch.fuel.fraction_consumed_livegrass * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_1hr_cc[date.month] += patch.fuel.fraction_consumed_1hr * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_10hr_cc[date.month] += patch.fuel.fraction_consumed_10hr * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_100hr_cc[date.month] += patch.fuel.fraction_consumed_100hr * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_1000hr_cc[date.month] += patch.fuel.fraction_consumed_1000hr * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_DFM[date.month] += patch.fuel.char_dlm * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_RoS[date.month] += patch.fuel.ros_f * daily_number_of_fires_scaled;
	patch.fuel.monthly_realised_fire_speed[date.month] += (patch.fuel.ros_f * patch.fuel.fire_durat / 1000) * daily_number_of_fires_scaled;


	// NOTE:  when it comes to outputting these values, they need to be divided by the total number fires in the gridcell in the month
	// (which patch.fuel.monthly_number_fires[date.month] summed across all patches) but they *do not* need to be scaled to the gridcell level
	// since the code above already does that

}



//  CHECK VALID MODE
// MF Checks if SPITFIRE has been called with a valid mode and corresponding settings
// INTERNAL function

bool valid_spitfire_mode() {

	return (firemodel == SPITFIRE
			|| firemodel == STAT_BURNT_AREA
			|| firemodel == PRESCR_BURNT_AREA
			|| firemodel == PRESCR_NUMBER_FIRES
			|| (firemodel == FIXED_FIRE_RETURN && firereturninterval > 0 && fixburnday >= 0)
			|| (firemodel == RANDOM_FIRE_RETURN && firereturninterval > 0 && fixburnday >= 0)
			|| firemodel == NOFIRE);

}

///////////////////////////////////////////////////////////////////////////////////////
//  HUMAN IGNITIONS - original SPITFIRE
// MF Calculates human caused ignitions depending on population density and a(Nd)
//    via the original SPITFIRE formulation
//    inputs are in per Km^2  
//    output in per hectare 
//    In reference to the original formulation:
//    "P1" is a tuned parameter (here replaced by human_ignition_constant)
//    "P2" is defined as a constant
// INTERAL function

double human_ignitions(double pop_dens, double a_Nd) {

	//  parameter in SPITFIRE human ignitions burned area calculation see Thonicke et al 2010
	const double P2 = 0.5;

	if (pop_dens == -999999.000000)
		pop_dens = 0;
	double ign_sq_km = pop_dens * (human_ignition_constant * exp(-P2 * (pow(pop_dens, P2)))) * (a_Nd / 100);
	double ign_hect = ign_sq_km / 100;
	return (ign_hect);
}

///////////////////////////////////////////////////////////////////////////////////////
//  NATURAL IGNITIONS - original SPITFIREs
// MF Calculates natural (lightning) caused ignitions depending on flashrate
//    via the original SPITFIRE formulation
//    inputs are in per Km^2  
//    output in per hectare 
// INTERAL function

double lightning_ignitions(double FR_sq_km) {
	// lightning_ctg_factor is proportion of cloud-to-ground flashes (possibly also including an detection efficiency correction, for example with WLGC)
	double c2 = 0.04; // fire starting efficiency - original SPITFIRE value
	if (FR_sq_km == -999999.000000)
		FR_sq_km = 0;
	double ign_hect = (FR_sq_km / 100) * lightning_ctg_factor * c2;
	return (ign_hect);
}

///////////////////////////////////////////////////////////////////////////////////////
//  ROTHERMEL RATE OF SPREAD
//  This is based on the SI reformulation of Rothermel 1972 as given in Wilson 1980
//  Returns forward rate of spread in m/min
//  INTERAL function

double forward_Rothermel_ROS(Fuel_patch &fuel) {


	fuel.gamma_f = 0;

	//// RETURN VALUE
	double fROS;

	//// ROTHERMAL SPECIFIC CONSTANTS
	// Mineral damping coefficient
	const double MINER_DAMP = 0.41739;
	// Blah
	const double part_dens = 513.;

	//// PACKING DENSITY (See Rothermel 1972)
	// The actual packing ratio - refered to as beta in much literature (including Rothermel 1972) and gives a measure of the compactness of the fuel bed
	// Rothermel/Wilson Eqn. 31
	double packing_ratio = fuel.char_FBD / part_dens;
	// The packing density for optimal fire spread given characteristic surface-to-volume ratio
	// Rothermel/Wilson Eqn. 37
	double optimal_packing_ratio = 0.20395 * (pow(fuel.char_sigma, -0.8189));
	// ratio of actual-to-optimal packing ratio
	double packing_ratio_ratio = packing_ratio / optimal_packing_ratio;

	//// HEAT OF PREIGNITION (Rothermel 1972)
	// Rothermel/Wilson Eqn. 12
	double q_ig = 581 + 2594 * fuel.char_dlm;

	//// EFFECTIVE HEATING NUMBER  -
	//  Rothermel/Wilson Eqn. 14
	double eps = exp(-4.528 / fuel.char_sigma);


	//// PROPOGATING FLUX RATIO
	// Rothermel/Wilson Eqn 42
	double xi;
	// MF: Note sure why this check is here
	if (fuel.char_sigma <= 0.00001)
		xi = 0.;
	else {
		xi = (exp((0.792 + 3.7597 * pow(fuel.char_sigma, 0.5)) * (packing_ratio + 0.1))) / (192 + 7.9095 * fuel.char_sigma);
	}

	//// MAXIMUM AND OPTIMAL REACTION VELOCITY
	// maximum reaction velocity - in /min, Rothermel/Wilson Egn. 36
	double gamma_max = 1 / (0.0591 + 2.926 * pow(fuel.char_sigma, -1.5));
	// Rothermel/Wilson Eqn. 39, but note using the formulation from Albini 1976
	double A = 8.9033 * pow(fuel.char_sigma, -0.7913);
	// optimum reaction velocity  -  Rothermel Eqn 38
	double gamma_optimum = gamma_max * pow(packing_ratio_ratio, A) * exp(A * (1 - packing_ratio_ratio));

	//// MOISTURE DAMPING COEFFICIENT
	// Rothermel/Wilson Eqn. 29
	double moist_damp = max(0., (1 - (2.59 * fuel.mw_weight) + (5.11 * (fuel.mw_weight * fuel.mw_weight)) - (3.52 * pow(fuel.mw_weight, 3))));

	//// ACTUAL REACTION VELOCITY
	// Rothermel/Wilson Eqn. 26
	fuel.gamma_f = gamma_optimum * moist_damp * MINER_DAMP;

	//// REACTION INTENSITY
	// Rothermel/Wilson Eqn. 27
	// Check value for H?
	double reaction_intensity = gamma_optimum * (fuel.char_net_fuel_gDM / 1000) * H * moist_damp * MINER_DAMP; // MF - note conversion from gDM to kgDM as needed by Rothermel eqn


	//// WINDSPEED LIMIT - different formulations possible
	// also note unit shenaniganery

	// Lasslop, Thonicke and Kloster 2014 - reduction of windspeed multiplier at high windspeeds
	// simply limit doesn't mess with the units
	double modified_effective_wind = fuel.effective_wind;

	if(windlimit == LASSLOP) {
		double modified_effective_wind_feet = fuel.effective_wind *3.28084;
		if (modified_effective_wind_feet > 100) {
			modified_effective_wind_feet = max(0.0, 100 * (1.0 + 0.5) - 0.5 * modified_effective_wind_feet);
			modified_effective_wind = modified_effective_wind_feet / 3.28084;
			//if(fuel.effective_wind > modified_effective_wind) dprintf("LASSLOP limit: initial = %f, limited = %f (m/min) \n", fuel.effective_wind, modified_effective_wind);
		}
	}
	else if(windlimit == ROTHERMEL && reaction_intensity > 0.00001) {
		// covert reaction intensity to  Btu/ft^2/min
		// (factor from Andrews et al 2013 International Journal of Wildland Fire, http://dx.doi.org/10.1071/WF12122)
		double reaction_intensity_imperial = reaction_intensity * (1105 / 209.3);
		// Rothermel original version - U_eff = 0.9 * I_R where I_R in Btu/ft^2/min and so resulting max effective wind speed in ft/min
		double max_effective_windspeed = (0.9 * reaction_intensity_imperial) * 0.3048;
		modified_effective_wind = min(fuel.effective_wind, max_effective_windspeed);
		//if(fuel.effective_wind > modified_effective_wind && reaction_intensity > 0.00001) dprintf("ROTHERMEL limit: initial = %f, limited = %f (m/min) \n", fuel.effective_wind, modified_effective_wind);
	}
	else if(windlimit == ANDREWS  && reaction_intensity > 0.00001) {
		// covert reaction intensity to  Btu/ft^2/min
		// (factor from Andrews et al 2013 International Journal of Wildland Fire, http://dx.doi.org/10.1071/WF12122)
		double reaction_intensity_imperial = reaction_intensity * (1105 / 209.3);
		// Andrews 2013 calculation maximum effective windspeed (note conversion back to m/min from ft/min)
		double max_effective_windspeed = 96.8 * pow(reaction_intensity_imperial, 0.3333) * 0.3048;
		modified_effective_wind = min(fuel.effective_wind, max_effective_windspeed);
	}


	//// WINDSPEED COEFFICIENT
	// Rothermel/Wilson Eqn. 49
	double B = 0.15988 * pow(fuel.char_sigma, 0.54);
	// Rothermel/Wilson Eqn. 48
	double C = 7.47 * exp(-0.8711 * pow(fuel.char_sigma, 0.55));
	// Rothermel/Wilson Eqn. 50
	double E = 0.715 * exp(-0.01094 * fuel.char_sigma);


	// Rothermel/Wilson Eqn. 47 - Note, windspeed in m/min and errata in Wilson.
	double phi_wind = C * (pow((modified_effective_wind * 3.281), B)) * pow(packing_ratio_ratio, -E);
	//dprintf("phi_wind = %f, modified_effective_wind = %f\n", phi_wind, modified_effective_wind);



	////  FORWARD RATE OF SPREAD
	// Rothermel/Wilson Eqn 52
	if (((fuel.char_FBD <= 0.) | (eps <= 0.) | (q_ig <= 0.) | (reaction_intensity <= 0.)))
		fROS = 0.;
	else
		fROS = (reaction_intensity * xi * (1.0 + phi_wind)) / (fuel.char_FBD * eps * q_ig);

	//dprintf("MF patch.dlm = %40.40f, char_MoE = %40.40f, sigma = %40.40f, char_dens_fuel_ave = %40.40f, char_net_fuel_gDM,  = %40.40f\n", patch.char_dlm, patch.char_MoE, patch.char_sigma, patch.char_dens_fuel_avg, patch.char_net_fuel_gDM);
	//dprintf("MF gamma_aptr = %40.40f, moist_damp = %40.40f, phi_wind = %40.40f\n",gamma_aptr, moist_damp, phi_wind);
	//dprintf("MF gamma_f = %40.40f, mw_weight = %40.40f, fRos = %40.40f\n", patch.gamma_f, patch.mw_weight,  fROS);

	return (fROS);

}

///////////////////////////////////////////////////////////////////////////////////////
// calculate residence_time_PandR - INTERNAL FUNCTION
// CALCULATES RESIDENCE TIME (tau_L) FOR A PATCH USING THE PETERSON AND RYAN 1986 APPROACH


void calculate_residence_time_PandR(Fuel_patch& fuel) {

	double tau_b_livegrass = 39.4 * (fuel.fuel_livegrass_gDM / 1e4) * (1 - pow((1 - fuel.fraction_consumed_livegrass), 0.5));
	double tau_b_1hr = 39.4 * (fuel.fuel_1hr_gDM / 1e4) * (1 - pow((1 - fuel.fraction_consumed_1hr), 0.5));
	double tau_b_10hr = 39.4 * (fuel.fuel_10hr_gDM / 1e4) * (1 - pow((1 - fuel.fraction_consumed_10hr), 0.5));
	double tau_b_100hr = 39.4 * (fuel.fuel_100hr_gDM / 1e4) * (1 - pow((1 - fuel.fraction_consumed_100hr), 0.5));

	//fuel.tau_l = tau_b_livegrass + tau_b_1hr + tau_b_10hr + tau_b_100hr;
	fuel.tau_l = tau_b_livegrass + tau_b_1hr;

#if defined(ERRORDEBUG) || defined(FULLDEBUG)
	if (fuel.tau_l != fuel.tau_l) {
		printf("fuel.fuel_livegrass_gDM = %f,fuel.fraction_consumed_livegrass = %f\n", fuel.fuel_livegrass_gDM, fuel.fraction_consumed_livegrass);
		printf("fuel.fuel_1hr_gDM = %f,fuel.fraction_consumed_1hr = %f\n", fuel.fuel_1hr_gDM, fuel.fraction_consumed_1hr);
		printf("live_grass = %f,1hr = %f\n", tau_b_livegrass, tau_b_1hr);
		printf("SPITFIRE_ERROR: tau_l (critical time for cambial damage) gives nan\n");
	}
#endif

#if defined(FULLDEBUG)
	if (fuel.tau_l > 8) {
		printf("SPITFIRE_WARNING: tau_l > 8 mins (= %f mins)\n", fuel.tau_l);
	}
#endif

}


///////////////////////////////////////////////////////////////////////////////////////
// calculate residence_time_ROS - INTERNAL FUNCTION
// CALCULATES RESIDENCE TIME (tau_L) FOR A PATCH USING THE Rate of Spread (Rothermel) Approach


void calculate_residence_time_RoS(Fuel_patch& fuel) {

	if (fuel.gamma_f > 0) {

		double total_fuel = fuel.fuel_1hr_gDM + fuel.fuel_livegrass_gDM + fuel.fuel_10hr_gDM + fuel.fuel_100hr_gDM;
		double wgtd_prop_total_fuels_consumed = (fuel.fraction_consumed_1hr * fuel.fuel_1hr_gDM + fuel.fraction_consumed_livegrass * fuel.fuel_livegrass_gDM + fuel.fraction_consumed_10hr * fuel.fuel_10hr_gDM + fuel.fraction_consumed_100hr
				* fuel.fuel_100hr_gDM) / total_fuel;

		//fuel.tau_l = min(8,2*fuel.fraction_consumed_livegrass/fuel.gamma_f);
		//fuel.tau_l = min(8,2*wgtd_prop_total_fuels_consumed/fuel.gamma_f);  //ACS tau_l check 4 24.02.15
		fuel.tau_l = min(8.0, 4 * wgtd_prop_total_fuels_consumed / fuel.gamma_f); //ACS tau_l check 5 16.03.15

		if (fuel.tau_l < 0) {
			fuel.tau_l = 0;
		}
	} else {
		fuel.tau_l = 0;
	}

	/*

	 #if defined(ERRORDEBUG) || defined(FULLDEBUG)
	 if(fuel.tau_l != fuel.tau_l){
	 printf("fuel.fraction_consumed_livegrass = %f,\n", fuel.fraction_consumed_livegrass);
	 printf("fuel.gamma_f = %f\n", fuel.fuel_1hr_gDM, fuel.gamma_f);
	 printf("SPITFIRE_ERROR: tau_l (critical time for cambial damage) gives nan\n");
	 }
	 #endif

	 #if defined(FULLDEBUG)
	 if(fuel.tau_l > 8){
	 printf("fuel.fraction_consumed_livegrass = %f,\n", fuel.fraction_consumed_livegrass);
	 printf("fuel.gamma_f = %f\n", fuel.fuel_1hr_gDM, fuel.gamma_f);
	 printf("SPITFIRE_WARNING: tau_l > 8 mins (= %f mins)\n", fuel.tau_l);
	 }
	 #endif

	 */

}


//////////////////////////////////////////////////////////////////////////////////////


/// Calculates fire size for SPITFIRE
/** Calculates fire size for SPITFIRE in ha.
 *  Should be run every day.
 */

double fire_size(Patch& patch) {

	// calculate tree and grass FPC
	// first calculate "high" and "low" FPC sums
	// get the FPC sums
	double FPC_low = 0.0;
	double FPC_high = 0.0;
	patch.vegetation.firstobj();
	while (patch.vegetation.isobj) {
		Individual& indiv = patch.vegetation.getobj();
		if (indiv.pft.lifeform == TREE) { FPC_high += indiv.fpc; }
		else if (indiv.pft.lifeform == GRASS) {	FPC_low += indiv.fpc; }
		patch.vegetation.nextobj();
	};


	// calculate the length-to-breadth ratio of the fire ellipse
	double length_to_breadth = 0.0;
	// This first condition is that for windspeeds of less then 1km/h, length-to-breadth = 1.0
	// see Eqn. 81 in CFFBG: Development and structure of the Canadian Forest Fire Behaviour Predictions Systems
	if (patch.fuel.effective_wind < 16.67)
		length_to_breadth = 1.0;
	else if(FPC_high+FPC_low > 0.0){
		length_to_breadth = (FPC_high * (1. + (8.729 * (pow(1 - (exp(-0.03 * 0.06 * patch.fuel.effective_wind)), 2.155)))) + //Eq_24
				(FPC_low * 1.1 * pow((0.06 * patch.fuel.effective_wind), 0.0464))) / (FPC_high+FPC_low); //Eq_
	}
	else {
		length_to_breadth = 1.0;
	}


	double db = patch.fuel.ros_b * patch.fuel.fire_durat;
	double df = patch.fuel.ros_f * patch.fuel.fire_durat;

	if (patch.fuel.net_deadfuel_gDM <= 0.) {
		return(0.0);
	}
	else {
		// units:
		// duration is in mins and ros_b and ros_f are in m/min therefore db and df are in m,
		// so area would be in m^2 but the "/10000" converts the final fire size into ha
		return((PI / (4 * length_to_breadth)) * pow((db + df), 2) / 10000);
	}


}

/// Calculates fuel moisture for SPITFIRE using Nesterov
/** Calculates fire moisture for SPITFIRE using Nesterov (original Thonicke et al.)
 *  Should be run every day.
 */

void fuel_moisture_nesterov(Patch& patch, double Nesterov_index) {

	// dubious SPITFIRE alpha constants
	const double alpha_1hr = 0.001;
	const double alpha_10hr = 0.00005424;
	const double alpha_100hr = 0.0000149; //0.0000485; - MF Veiko had this value

	// Minimum Nesterov for a non-zero alpha_livegrass
	const double MIN_NESTEROV = 0.001;

	// Old south order, new northern horizon

	// calculate litter fuel daily fuel moisture (dfm) for the different classes
	if (Nesterov_index > MIN_NESTEROV) {
		patch.fuel.dlm_1hr = exp(-alpha_1hr * Nesterov_index);
		patch.fuel.dlm_10hr = exp(-alpha_10hr * Nesterov_index);
		patch.fuel.dlm_100hr= exp(-alpha_100hr * Nesterov_index);
	}
	// but if Nesterov index is too low (or maybe even negative) set all to 100% fuel moisture and return
	else {
		patch.fuel.dlm_1hr = 1.0;
		patch.fuel.dlm_10hr = 1.0;
		patch.fuel.dlm_100hr = 1.0;
		patch.fuel.char_dlm = 1.0;
		return;
	}


	// weight dfm across fuel classes - new, simple and experimental, ignored for now
	double char_dlm = 1.0;
	if(patch.fuel.deadfuel_gDM > 0.0 || patch.fuel.fuel_livegrass_gDM > 0.0) {

		char_dlm = (patch.fuel.dlm_1hr * patch.fuel.fuel_1hr_gDM) + (patch.fuel.dlm_10hr * patch.fuel.fuel_10hr_gDM) + (patch.fuel.dlm_100hr * patch.fuel.fuel_100hr_gDM) + (patch.fuel.fuel_livegrass_gDM * patch.fuel.dlm_livegrass);
		char_dlm /= (patch.fuel.deadfuel_gDM + patch.fuel.fuel_livegrass_gDM) ;

	}

	// the old and weird but effective way

	// "back-calculate" alpha_livegrass
	double alpha_livegrass = 0;
	// Note that this calculation *should* be safe because I have limited patch.fuel.dlm_livegrass to a maximum of 0.01,
	// so there can be no log of zero, and the case where Nesterov is very small or zero is covered above
	// However, if patch.fuel.dlm_livegrass is equal to 1.0 then the whole term becomes zero and alpha_livegrass becomes zero.
	// This is fine because alpha = 0.0 means the fuel doesn't dry at all (fuel moisture always equals 1.0) this will have the right effect
	// the the characteristic weighting equation below since it will reduce char_alpha which will increase characteristic fuel moisture
	alpha_livegrass = -(log(patch.fuel.dlm_livegrass) / Nesterov_index);


	// calculate the weighted char_alpha and from that the charactersitic fuel moisture
	double char_alpha = 0.0;
	if(patch.fuel.deadfuel_gDM > 0.0 || patch.fuel.fuel_livegrass_gDM > 0.0) {

		// calculate weighted alpha
		char_alpha = (alpha_1hr * patch.fuel.fuel_1hr_gDM) + (alpha_10hr * patch.fuel.fuel_10hr_gDM) + (alpha_100hr * patch.fuel.fuel_100hr_gDM) + (alpha_livegrass * patch.fuel.dlm_livegrass);
		char_alpha /= (patch.fuel.deadfuel_gDM + patch.fuel.fuel_livegrass_gDM) ;

		// now calculate fuel mositure, also capped at 1%
		patch.fuel.char_dlm = max(0.01, exp(-char_alpha * Nesterov_index));

	}
	// if no fuel at all return a nominal 1.0 for fuel moisture
	else {
		patch.fuel.char_dlm = 1.0;
	}

	// COMBINE FUEL MOISTURE WITH SOIL MOISTURE TO CONSIDER VERTICAL PROFILE OF MOISTURE IN A FUEL BED IN A SINMPLE WAY
	// **** I THINK THIS IDEA HAS BEEN SOMEWHAT DISCREDITED ****
	if(fractionsoilmoistureinfuel > 0.0) {

		patch.fuel.char_dlm = fractionsoilmoistureinfuel * patch.soil.get_soil_water_upper() + (1 - fractionsoilmoistureinfuel) * patch.fuel.char_dlm;
		patch.fuel.dlm_1hr = fractionsoilmoistureinfuel * patch.soil.get_soil_water_upper() + (1 - fractionsoilmoistureinfuel) * patch.fuel.dlm_1hr;
		patch.fuel.dlm_10hr = fractionsoilmoistureinfuel * patch.soil.get_soil_water_upper() + (1 - fractionsoilmoistureinfuel) * patch.fuel.dlm_10hr;
		patch.fuel.dlm_100hr = fractionsoilmoistureinfuel * patch.soil.get_soil_water_upper() + (1 - fractionsoilmoistureinfuel) * patch.fuel.dlm_100hr;


	}

}


/// Calculates fuel moisture for SPITFIRE using VPD
/** Calculates fire moisture for SPITFIRE using VPD
 *  Should be run every day.
 */

void fuel_moisture_VPD(Patch& patch, double VPD, double prec) {


	// zero some stuff
	patch.fuel.char_dlm = 0;

	// DAILY LITTER MOISTURE FROM RESCO DE DIOS FOR 1HR FUELS

	// calculate daily litter moisture for 1hr
	// note conversion from percent to fraction at the end
	double dlm_1hr_suspended = (6.79 + 27.43 * exp(-1.05 * VPD))/100;

	// DAILY LITTER MOISTURE FOR 10HR AND 100HR FUEL
	double dlm_10hr_suspended = (dlm_10hr_suspended * 0.5) + (dlm_1hr_suspended * 0.5);
	double dlm_100hr_suspended = (dlm_100hr_suspended * 0.8) + (dlm_1hr_suspended * 0.2);

	// WEIGHT TO GET CHARACTERISTIC DLM INCLUDING LIVE FUEL
	double char_dlm_suspended;

	// If dead fuel is present
	if (patch.fuel.deadfuel_gDM > 0.0) {

		double dlm_dead_fuel_suspended = (patch.fuel.fuel_1hr_gDM * dlm_1hr_suspended
				+ patch.fuel.fuel_10hr_gDM * dlm_10hr_suspended
				+ patch.fuel.fuel_100hr_gDM * dlm_100hr_suspended)
																				/ patch.fuel.deadfuel_gDM;

		if (patch.fuel.fuel_livegrass_gDM > 0.0) {
			char_dlm_suspended = (dlm_dead_fuel_suspended * patch.fuel.deadfuel_gDM + patch.fuel.dlm_livegrass * patch.fuel.fuel_livegrass_gDM) / (patch.fuel.deadfuel_gDM + patch.fuel.fuel_livegrass_gDM);
		}

		else {
			char_dlm_suspended = dlm_dead_fuel_suspended;
		}
	}

	// Else if livegrass fuel is present
	else if (patch.fuel.fuel_livegrass_gDM > 0.0) {
		char_dlm_suspended = patch.fuel.dlm_livegrass;
	}

	// Else if no fuel set dlm to 1.0
	else {
		char_dlm_suspended = 1.0;
	}

	// COMBINE FUEL MOISTURE WITH SOIL MOISTURE TO CONSIDER VERTICAL PROFILE OF MOISTURE IN A FUEL BED IN A SIMPLE WAY
	// Note that although dlm for 10 hr and 100 hr fuels are defined here, they not actually used
	// Currently consumption is based on characteristic dlm.
	// Note simple fuel wetting condition here
	if (prec < 3) {
		patch.fuel.char_dlm = fractionsoilmoistureinfuel * patch.soil.get_soil_water_upper() + (1 - fractionsoilmoistureinfuel) * char_dlm_suspended;
		patch.fuel.dlm_1hr = fractionsoilmoistureinfuel * patch.soil.get_soil_water_upper() + (1 - fractionsoilmoistureinfuel) * dlm_1hr_suspended;
		patch.fuel.dlm_10hr = fractionsoilmoistureinfuel * patch.soil.get_soil_water_upper() + (1 - fractionsoilmoistureinfuel) * dlm_10hr_suspended;
		patch.fuel.dlm_100hr = fractionsoilmoistureinfuel * patch.soil.get_soil_water_upper() + (1 - fractionsoilmoistureinfuel) * dlm_100hr_suspended;
	}
	// make all fuel totally wet
	else {
		patch.fuel.char_dlm = 1.0;
		patch.fuel.dlm_1hr = 1.0;
		patch.fuel.dlm_10hr = 1.0;
		patch.fuel.dlm_100hr = 1.0;
	}

}



/// Calculates effective wind speed for SPITFIRE
/** Calculates wind speed for SPITFIRE.
 *  Should be run every day.
 */

double effective_wind_speed(Patch& patch, double wind_speed) {

	// incoming wind speed is m/s, put into m/min
	double wind_mmin = wind_speed * 60;

	// first calculate "high" and "low" FPC sums
	// get the FPC sums
	double FPC_woody = 0.0;
	patch.vegetation.firstobj();
	while (patch.vegetation.isobj) {
		Individual& indiv = patch.vegetation.getobj();
		if (indiv.pft.lifeform == TREE) { FPC_woody += indiv.fpc; }
		patch.vegetation.nextobj();
	};

	// limit FPC_woody to 1
	FPC_woody = min(FPC_woody, 1.0);  // cap high at 1.0


	// reduce wind speed according to woody and other FPC
	double effective_wind = (FPC_woody * 0.4 + (1- FPC_woody) * 0.6)  * wind_mmin;


	//dprintf("effective_wind = %f, previous effect_wind = \n", (FPC_high * wind_mmin * 0.4) + (FPC_low * wind_mmin * 0.6), effective_wind);

	return(effective_wind);

}


/// Calculates Fire Danger Index for SPITFIRE
/** Calculates Fire Danger Index for SPITFIRE based on daily fuel moisture,
 *  which is in turn based on Nesterov index.
 *  Should be run every day.
 */

double fdi(Fuel_patch& fuel, double Nesterov_index) {

	//////////////////////////Calculate fire Danger Index                    Eq_9
	if (Nesterov_index <= 0.0)
		return(0.0);
	else
		return(max(0., (1 - ((1 / fuel.char_MoE) * fuel.char_dlm))));

}


/// Calculates Burn Probability (Wilson 1985)
/** Calculates Burn Probability following Wilson 1985
 *  (Combustion Science and Technology) using daily fuel moisture,
 *  characteristic sigma, fuel mass and fuel particle density
 *  Should be run every day.
 */

double burn_probability(double fuel_moisture, double sigma, double fuel_mass, double fuel_particle_density = 513) {

	// calculate total fuel surface (conversion to m^-1)
	double S = sigma * fuel_mass * fuel_particle_density / 10000;

	// partition index
	double k = max(log(4.48 * S) / (0.27 + fuel_moisture), 0.0);

	// probability based on a logistic function
	return(1/(1+exp(-PI * (k - 4.6) / (pow(3,0.5) * 1.3))));

}


/// Calculates Fuel Bulk Density
/** Calculates Fuel Bulk Density either using the fixed value for a PFT
 *  or as a function of patch grass biomass following Hoffman et al. 2012 for tropical woody PFTs
 *  Should be run every day.
 */

double fuel_bulk_density(Pft& pft, double grass_biomass_kgDM, double gdd5) {

	// Pfeiffer et al. 2013 option for making grass FBD a function of GDD5 for testing, currently disabled.
	if(pft.lifeform == GRASS && false){
		return( (20000/(gdd5+1000)) - 1);
	}

	// if dens_fuel is less than or equal to zero, calculate FBD from grass biomass
	if (pft.dens_fuel <= 0) {
		return(max(1.0, 15.84 * exp(-85.00 * grass_biomass_kgDM) + 2.29 * exp(-2.045 * grass_biomass_kgDM)));
	}
	// otherwise use PFT-specific value
	else{
		return(pft.dens_fuel);
	}

}


/// Calculates fuel loading for SPITFIRE
/** Calculates fuel loading for SPITFIRE (1hr, 10hr, 100hr, 1000hr and live grass fuels)
 *  and characteristic surface-area to volume ratio (sigma), fuel bulk density (FBD) and
 *  moisture of extinction (MoE).  Note characteristic sigma, FBD and MoE do not contain influence of 1000hr fuel.
 *  Should be run every day.
 */

void fuel_loading(Patch& patch) {

	// DESCRIPTION
	// Sums the litter and live grass into fuel classes for SPITFIRE
	//
	// Contributions to fuel load:
	//
	//   (1) The patchpft litter pools (sap, heart, leaf and reproductive)
	//   (2) CENTURY SOM pools - SURFMETA and SURFSTRUCT go to 1hr fuel and SURFCWD and SURFFWD
	//		 are partitioned into 1hr, 10hr, 100hr and 1000hr according to standard fractions
	//   (3) Grass leaf biomass is either added to the live grass fuel type (if phenologically active)
	//		 or the 1hr pool (if phenologically inactive but has been active for at least one month
	//   (4) Tree leaf biomass is added to the  1hr pool (if phenologically inactive
	//       but has been active for at least one month, same as grasses)
	//
	// The following characteristic values are calculated for the patch fuel complex:
	//
	//	 (1) Surface-area to volume ratio (sigma). The 1000hr fuel does not currently contribute to this
	//       and it is not tracked through the CENTURY pools (since it is not a PFT specific parameter at the moment)
	//   (2) Fuel bulk density (FBD). 1000hr fuel also does not contribute to this.  Also a multiplier is applied for
	//       10hr and 100hr fuels (without any apparent justification).  This *is* tracked through the CENTURY SOM
	//       pools since it is PFT-specific
	//   (3) Moisture of extinction (MoE).  1000hr fuel *does* contribute here and it is tracked by through CENTURY


	// total mineral content of litter
	const double MINER_TOT = 0.055;

	double EPSILON = 0.1E-15f;


	// Zero fuel loads
	patch.fuel.fuel_1hr_gDM = 0; // gDM/m^2
	patch.fuel.fuel_10hr_gDM = 0; // gDM/m^2
	patch.fuel.fuel_100hr_gDM = 0; // gDM/m^2
	patch.fuel.fuel_1000hr_gDM = 0; // gDM/m^2
	patch.fuel.fuel_livegrass_gDM = 0; // gDM/m^2

	// Zero patch level fuel characteristics
	patch.fuel.char_FBD = 0; // kgDM/m^3
	patch.fuel.char_MoE = 0;
	patch.fuel.char_sigma = 0;

	// calculate the total grass biomass for the Hoffman et al 2012 Austral Ecology calculation of FBD
	patch.fuel.total_grass_biomass_kgDM = 0; // kgDM/m^2
	patch.vegetation.firstobj();
	while (patch.vegetation.isobj) {
		Individual& indiv = patch.vegetation.getobj();

		// alive check necessary?
		if (indiv.alive) {
			if (indiv.pft.lifeform == GRASS) {

				if(indiv.cmass_leaf > 0.0){
					patch.fuel.total_grass_biomass_kgDM += indiv.cmass_leaf / DM_C;
				}
				else {
					// dprintf("NEG GRASS CMASS LEAF: -will be ignored for fuel- : (%.2f, %.2f): Year = %i, Day = %i, PFT = %s, grass biomass = %f,  this.grass.biomass =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, (char*)indiv.pft.name,  indiv.cmass_leaf);
				}

			}  // end if grass
		} // end if alive

		patch.vegetation.nextobj();
	} // end loop



	// first the the contributions from each patch.pft in terms of litter
	// also set the FBD
	patch.pft.firstobj();
	while (patch.pft.isobj) {
		Patchpft& patchpft = patch.pft.getobj();

		// set the FBD, potentially according to Hoffman
		double current_pft_FBD = fuel_bulk_density(patchpft.pft, patch.fuel.total_grass_biomass_kgDM, patch.get_climate().gdd5);

		if(current_pft_FBD != current_pft_FBD || fabs(current_pft_FBD) > 35.0) {
			dprintf("FBD NAN: PFT LITTER: (%.2f, %.2f): Year = %i, Day = %i, PFT = %s, grass biomass = %f,  current_pft_FBD =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, (char*)patchpft.pft.name, patch.fuel.total_grass_biomass_kgDM,   current_pft_FBD);
		}



		// Allocate wood litter into fuel classes
		// conversion to get the right units - guess kg C; SPITFIRE g DM
		double cmass_litter_wood_gDM = (patchpft.cmass_litter_sap + patchpft.cmass_litter_heart) * 1000 / DM_C;

		// First check that litter_wood positive, it might be negative because of a large cmass_debt
		if (cmass_litter_wood_gDM >= 0.0) {

			// NOTE MoE not currently dependent on size classes (although arguably it should be,
			// perhaps as a function of surface area to volume, see Wilson 1990 Reexamination...)

			// 1hr fuel
			patch.fuel.fuel_1hr_gDM += wood_fraction_1hr * cmass_litter_wood_gDM;
			patch.fuel.char_sigma += sigma_1hr * wood_fraction_1hr * cmass_litter_wood_gDM;
			patch.fuel.char_FBD += current_pft_FBD * wood_fraction_1hr * cmass_litter_wood_gDM;
			patch.fuel.char_MoE += patchpft.pft.MoE * wood_fraction_1hr * cmass_litter_wood_gDM;

			// 10hr fuel
			patch.fuel.fuel_10hr_gDM += wood_fraction_10hr * cmass_litter_wood_gDM;
			patch.fuel.char_sigma += sigma_10hr *  wood_fraction_10hr * cmass_litter_wood_gDM;
			patch.fuel.char_FBD += current_pft_FBD * fbd_a * wood_fraction_10hr * cmass_litter_wood_gDM;
			patch.fuel.char_MoE += patchpft.pft.MoE * wood_fraction_10hr * cmass_litter_wood_gDM;

			// 100hr fuel
			patch.fuel.fuel_100hr_gDM += wood_fraction_100hr * cmass_litter_wood_gDM;
			patch.fuel.char_sigma += sigma_100hr *  wood_fraction_100hr * cmass_litter_wood_gDM;
			patch.fuel.char_FBD += current_pft_FBD * fbd_b * wood_fraction_100hr * cmass_litter_wood_gDM;
			patch.fuel.char_MoE += patchpft.pft.MoE * wood_fraction_100hr * cmass_litter_wood_gDM;


			// 1000hr fuel - no sigma, MoE or FBD contribution
			patch.fuel.fuel_1000hr_gDM += wood_fraction_1000hr * cmass_litter_wood_gDM;

		}
		// Wood litter negative give a warning
		else if (cmass_litter_wood_gDM < -1.0e-9) {
			dprintf("SPITFIRE: NEG_WOOD_LITTER_ERROR: PFT %s, year = %i, day = %i, litter_wood = %f(gDM), sap = %f(kgC), heart = %f(kgC)\n", (char*) patchpft.pft.name, date.year, date.day, cmass_litter_wood_gDM, patchpft.cmass_litter_sap, patchpft.cmass_litter_heart);
		}

		//  allocate fine litter (leaf/reproductive) into the fuel classes

		// sum and convert to get the right units - guess kg C; SPITFIRE g DM
		double litter_fine_gDM = (patchpft.cmass_litter_leaf + patchpft.cmass_litter_repr) * 1000 / DM_C;

		if (litter_fine_gDM >= 0.0) {
			patch.fuel.fuel_1hr_gDM += litter_fine_gDM;
			patch.fuel.char_sigma += patchpft.pft.sigma_leaf * litter_fine_gDM;
			patch.fuel.char_MoE += patchpft.pft.MoE * litter_fine_gDM;
			patch.fuel.char_FBD += current_pft_FBD * litter_fine_gDM;
		}
		else if (litter_fine_gDM < -1.0e-9) {
			dprintf("SPITFIRE: NEG_FINE_LITTER_ERROR: PFT %s, year = %i, day = %i, litter_fine = %f(gDM)\n", (char*) patchpft.pft.name, date.year, date.day, litter_fine_gDM);
		}

		patch.pft.nextobj();
	}



	//  contribution to fuel from vegetation C pools (live grass and senesced leaves)
	patch.vegetation.firstobj();
	while (patch.vegetation.isobj) {
		Individual& indiv = patch.vegetation.getobj();

		// set the FBD, potentially according to Hoffman
		double current_indiv_FBD = fuel_bulk_density(indiv.pft, patch.fuel.total_grass_biomass_kgDM, patch.get_climate().gdd5);

		if(current_indiv_FBD != current_indiv_FBD || fabs(current_indiv_FBD) > 35.0) {
			dprintf("FBD NAN: PFT INDIV: (%.2f, %.2f): Year = %i, Day = %i, PFT = %s, grass biomass = %f,  current_pft_FBD =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, (char*)indiv.pft.name, patch.fuel.total_grass_biomass_kgDM,   current_indiv_FBD);
		}

		// only do for positive leaf C (response to a bug where sometimes inter crop grasses have nagative leaf biomass)
		// alive check necessary?
		if (indiv.alive && indiv.cmass_leaf > 0.0) {

			double current_phen = patch.pft[indiv.pft.id].phen;

			//  allocate live (and phenologically active) grasses to live grass fuels
			//  If PFT is a grass, loop over individuals to find which ones contribute to the livegrass fuel
			//  could do this as a per individual loop outside the patch pft loop
			if (indiv.pft.lifeform == GRASS) {

				// add live fraction to live grass fuel
				patch.fuel.fuel_livegrass_gDM += indiv.cmass_leaf * current_phen * 1000 / DM_C; // in gDM/m^2
				// also the sigma
				patch.fuel.char_sigma += indiv.pft.sigma_leaf * indiv.cmass_leaf * current_phen * 1000 / DM_C ; // in gDM/m^2
				// also FBD
				patch.fuel.char_FBD += current_indiv_FBD * indiv.cmass_leaf * current_phen * 1000 / DM_C;
				// and live grass MoE
				patch.fuel.char_MoE += indiv.pft.MoE * indiv.cmass_leaf * current_phen * 1000 / DM_C;

			}  // end if grass


			//  allocate "senesced" leaves to 1hr fuel
			//  MF: because phenologically inactive leaves don't immediately go litter (rather they get transferred
			//  at the end of calendar year) here we also add 'live' leaves to 1hr fuel if they are currently off (phen < 1),
			//  provided they have been out already for at least one month of this calendar year
			if(indiv.aphen_raingreen > 30) {

				// add dead fraction to 1hr fuel
				patch.fuel.fuel_1hr_gDM += indiv.cmass_leaf * (1.0 - current_phen) * 1000 / DM_C ; // in gDM/m^2
				// also the sigma
				patch.fuel.char_sigma += indiv.pft.sigma_leaf * indiv.cmass_leaf * (1.0 - current_phen) * 1000 / DM_C ; // in gDM/m^2
				// also FBD
				patch.fuel.char_FBD += current_indiv_FBD * indiv.cmass_leaf * (1.0 -current_phen) * 1000 / DM_C;
				// and the MoE
				patch.fuel.char_MoE += indiv.pft.MoE * indiv.cmass_leaf * (1.0 - current_phen) * 1000 / DM_C ;

			} // end if leaves out for more than 30 days

		}  // end if alive

		patch.vegetation.nextobj();

	} // end for each individual loop


	// add the SOM pools to the fuel load if CENTURY is enabled
	if(ifcentury) {

		// NOTE: we ignore negligible pools with negligable C (both in the fuel load and the characteristic properties for consistency)

		// SURFSTRUCT Pool
		if(!negligible(patch.soil.sompool[SURFSTRUCT].cmass, -10)) {

			// add to the fuel load, converting to grams of dry matter
			patch.fuel.fuel_1hr_gDM += patch.soil.sompool[SURFSTRUCT].cmass * 1000 / DM_C;

			// accumulate the characteristics
			patch.fuel.char_sigma += (patch.soil.sompool[SURFSTRUCT].cmass * 1000 / DM_C) * patch.soil.sompool[SURFSTRUCT].surfacetovolume;
			patch.fuel.char_MoE += (patch.soil.sompool[SURFSTRUCT].cmass * 1000 / DM_C) * patch.soil.sompool[SURFSTRUCT].moistureofextinction;
			patch.fuel.char_FBD += patch.soil.sompool[SURFSTRUCT].cmass * 1000 / DM_C * patch.soil.sompool[SURFSTRUCT].fuelbulkdensity;

		}

		// SURFMETA Pool
		if(!negligible(patch.soil.sompool[SURFMETA].cmass, -10)) {

			// add to the fuel load, converting to grams of dry matter
			patch.fuel.fuel_1hr_gDM += patch.soil.sompool[SURFMETA].cmass * 1000 / DM_C;

			// accumulate the characteristics
			patch.fuel.char_sigma += (patch.soil.sompool[SURFMETA].cmass * 1000 / DM_C) * patch.soil.sompool[SURFMETA].surfacetovolume;
			patch.fuel.char_MoE += (patch.soil.sompool[SURFMETA].cmass * 1000 / DM_C) * patch.soil.sompool[SURFMETA].moistureofextinction;
			patch.fuel.char_FBD += patch.soil.sompool[SURFMETA].cmass * 1000 / DM_C * patch.soil.sompool[SURFMETA].fuelbulkdensity;

		}

		// SURFWD Pool
		if(!negligible(patch.soil.sompool[SURFFWD].cmass, -10)) {

			double SURFFWD_century_gDM = patch.soil.sompool[SURFFWD].cmass * 1000 / DM_C;

			// contribution to the fuel pools
			patch.fuel.fuel_1hr_gDM += wood_fraction_1hr * SURFFWD_century_gDM;
			patch.fuel.fuel_10hr_gDM += wood_fraction_10hr * SURFFWD_century_gDM;
			patch.fuel.fuel_100hr_gDM += wood_fraction_100hr * SURFFWD_century_gDM;
			patch.fuel.fuel_1000hr_gDM += wood_fraction_1000hr * SURFFWD_century_gDM;

			// characteristics
			patch.fuel.char_sigma += wood_fraction_1_10_100hr * SURFFWD_century_gDM  * patch.soil.sompool[SURFFWD].surfacetovolume;
			patch.fuel.char_MoE += wood_fraction_1_10_100hr * SURFFWD_century_gDM  * patch.soil.sompool[SURFFWD].moistureofextinction;
			patch.fuel.char_FBD += wood_fraction_1_10_100hr * SURFFWD_century_gDM * patch.soil.sompool[SURFFWD].fuelbulkdensity;

		}

		// SURFCWD Pool
		if(!negligible(patch.soil.sompool[SURFCWD].cmass, -10)) {

			double SURFCWD_century_gDM = patch.soil.sompool[SURFCWD].cmass * 1000 / DM_C;

			// contribution to the fuel pools
			patch.fuel.fuel_1hr_gDM += wood_fraction_1hr * SURFCWD_century_gDM;
			patch.fuel.fuel_10hr_gDM += wood_fraction_10hr * SURFCWD_century_gDM;
			patch.fuel.fuel_100hr_gDM += wood_fraction_100hr * SURFCWD_century_gDM;
			patch.fuel.fuel_1000hr_gDM += wood_fraction_1000hr * SURFCWD_century_gDM;

			// characteristics
			patch.fuel.char_sigma += wood_fraction_1_10_100hr * SURFCWD_century_gDM  * patch.soil.sompool[SURFCWD].surfacetovolume;
			patch.fuel.char_MoE += wood_fraction_1_10_100hr * SURFCWD_century_gDM  * patch.soil.sompool[SURFCWD].moistureofextinction;
			patch.fuel.char_FBD += wood_fraction_1_10_100hr * SURFCWD_century_gDM * patch.soil.sompool[SURFCWD].fuelbulkdensity;

		}



		if (!(patch.soil.sompool[SURFSTRUCT].moistureofextinction >= 0.195 && patch.soil.sompool[SURFSTRUCT].moistureofextinction <= 0.305)) {
			dprintf("MOE ERR: SURFSTRUCT: (%.2f, %.2f): Year = %i, Day = %i, Stand = %i, Patch = %i, patch.soil.sompool[SURFSTRUCT].moistureofextinction =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, patch.stand.id, patch.id, patch.soil.sompool[SURFSTRUCT].moistureofextinction);
		}
		if (!(patch.soil.sompool[SURFMETA].moistureofextinction >= 0.195 && patch.soil.sompool[SURFMETA].moistureofextinction <= 0.305)) {
			dprintf("MOE ERR: SURFMETA: (%.2f, %.2f): Year = %i, Day = %i, Stand = %i, Patch = %i, patch.soil.sompool[SURFMETA].moistureofextinction =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, patch.stand.id, patch.id, patch.soil.sompool[SURFMETA].moistureofextinction);
		}
		if (!(patch.soil.sompool[SURFCWD].moistureofextinction >= 0.195 && patch.soil.sompool[SURFCWD].moistureofextinction <= 0.305)) {
			dprintf("MOE ERR: SURFCWD: (%.2f, %.2f): Year = %i, Day = %i, Stand = %i, Patch = %i, patch.soil.sompool[SURFCWD].moistureofextinction =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, patch.stand.id, patch.id, patch.soil.sompool[SURFCWD].moistureofextinction);
		}
		if (!(patch.soil.sompool[SURFFWD].moistureofextinction >= 0.195 && patch.soil.sompool[SURFFWD].moistureofextinction <= 0.305)) {
			dprintf("MOE ERR: SURFFWD: (%.2f, %.2f): Year = %i, Day = %i, Stand = %i, Patch = %i, patch.soil.sompool[SURFFWD].moistureofextinction =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, patch.stand.id, patch.id, patch.soil.sompool[SURFFWD].moistureofextinction);
		}

	}


	// calculate characteristic values by dividing through by fuel overall fuel load
	double total_fuel_except_1000hr = patch.fuel.fuel_1hr_gDM + patch.fuel.fuel_10hr_gDM + patch.fuel.fuel_100hr_gDM + patch.fuel.fuel_livegrass_gDM;

	// divide sigma and FBD through by fuel mass to get characteristic (note livegrass included but 1000hr not included)
	if(!negligible(total_fuel_except_1000hr, -10)) {
		patch.fuel.char_sigma /= total_fuel_except_1000hr;
		patch.fuel.char_FBD /= total_fuel_except_1000hr;
		patch.fuel.char_MoE /= total_fuel_except_1000hr;
	}
	else {
		patch.fuel.char_MoE = 0.25;
		patch.fuel.char_FBD = 10.0;
		patch.fuel.char_sigma = 66.0;
	}

	if(patch.fuel.char_FBD != patch.fuel.char_FBD || fabs(patch.fuel.char_FBD) > 35.0) {
		dprintf("FBD NAN: CHAR: (%.2f, %.2f): Year = %i, Day = %i, grass biomass = %f, total_fuel_except_1000hr= %f,  current_pft_FBD =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, patch.fuel.total_grass_biomass_kgDM, total_fuel_except_1000hr, patch.fuel.char_FBD);
	}


	// Check MoE in range - replace with assert?
	//assert(patch.fuel.char_MoE >= 0.2 && patch.fuel.char_MoE <= 0.3);
	if (!(patch.fuel.char_MoE >= 0.195 && patch.fuel.char_MoE <= 0.305)) {
		dprintf("MOE ERR: CHAR: (%.2f, %.2f): Year = %i, Day = %i, patch.fuel.char_MoE =%f \n", patch.stand.get_gridcell().get_lon(), patch.stand.get_gridcell().get_lat(),  date.year, date.day, patch.fuel.char_MoE);

		//if(patch.stand.landcover == PASTURE) { dprintf("stand type = pasture\n");}
		//if(patch.stand.landcover == CROPLAND) { dprintf("stand type = cropland\n");}
		//if(patch.stand.landcover == NATURAL) { dprintf("stand type = natural \n");}


		//dprintf("Total above ground litter = %.20f gDM\n", patch.fuel.aboveground_litter_gDM);
		//patch.pft.firstobj();
		//while (patch.pft.isobj) {
		//	Patchpft& patchpft = patch.pft.getobj();
		//	dprintf("PFT = %s, aboveground_litter = %.20f gDM, MoE = %f\n", (char*) patchpft.pft.name, (patchpft.fuel.aboveground_litter_gC / DM_C), patchpft.pft.MoE);
		//	patch.pft.nextobj();
		//}

		//dprintf("Adding SOMPOOL SURFSTRUCT, cmass = %.20f, MoE = %f\n",	patch.soil.sompool[SURFSTRUCT].cmass, patch.soil.sompool[SURFSTRUCT].moistureofextinction );
		//dprintf("Adding SOMPOOL SURFMETA, cmass = %.20f, MoE = %f\n",	patch.soil.sompool[SURFMETA].cmass, patch.soil.sompool[SURFMETA].moistureofextinction );
		//dprintf("Adding SOMPOOL SURFCWD, cmass = %.20f, MoE = %f\n",	patch.soil.sompool[SURFCWD].cmass, patch.soil.sompool[SURFCWD].moistureofextinction );
		//dprintf("Adding SOMPOOL SURFFWD, cmass = %.20f, MoE = %f\n",	patch.soil.sompool[SURFFWD].cmass, patch.soil.sompool[SURFFWD].moistureofextinction );



	}

	// calculate characteristic net fuel loading

	// Calculate total dead fuel (not including 1000hr because this is used for Rothermel ROS calculation)
	patch.fuel.deadfuel_gDM = patch.fuel.fuel_1hr_gDM + patch.fuel.fuel_10hr_gDM + patch.fuel.fuel_100hr_gDM; // in gDM/m^2
	assert(patch.fuel.deadfuel_gDM >= 0.0);

	// Calculate net fuel (accounting for non-flammable mineral content)
	if (patch.fuel.deadfuel_gDM > 0.0) {
		patch.fuel.net_deadfuel_gDM = (1 - MINER_TOT) * patch.fuel.deadfuel_gDM; // gDM/m^2 - must be convert to kg in RoS
	} else {
		patch.fuel.net_deadfuel_gDM = 0;
	}


	patch.fuel.char_net_fuel_gDM = patch.fuel.net_deadfuel_gDM + ((1 - MINER_TOT) * patch.fuel.fuel_livegrass_gDM); // MF: note, still in gDM

}



////////////////////////////////////////////////////////////////////////////////////////
// calculate_fuel_consumption_patch - INTERNAL FUNCTION
// CALCULATES THE HOW MUCH FUEL IS CONSUMED BY A FIRE ACROSS THE WHOLE PATCH

void calculate_fuel_consumption(Fuel_patch& fuel) {

	// hard-coded moisture of extinction of live grass
	const double MoE_livegrass = 0.2; // moisture of extinction

	// zero everything
	fuel.fuel_consumed_1hr_gDM = 0; // gDM/m^2
	fuel.fuel_consumed_10hr_gDM = 0; // gDM/m^2
	fuel.fuel_consumed_100hr_gDM = 0; // gDM/m^2
	fuel.fuel_consumed_1000hr_gDM = 0; // gDM/m^2
	fuel.fuel_consumed_livegrass_gDM = 0; // gDM/m^2


	fuel.fraction_consumed_1hr = 0;
	fuel.fraction_consumed_10hr = 0;
	fuel.fraction_consumed_100hr = 0;
	fuel.fraction_consumed_1000hr = 0;
	fuel.fraction_consumed_livegrass = 0;


	// ratio of fuel moisture to moisture of extinction
	double moisture_ratio_1hr = 0.;
	double moisture_ratio_10_100hr = 0.;

	//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// M_21
	//fuel consumption depending on fuel moisture
	//influence of livefuel on 1hr fuel moisture content

	double moisture_ratio_livegrass = min(1.0, fuel.dlm_livegrass/MoE_livegrass);
	if (fuel.char_MoE > 0.0) {
		moisture_ratio_1hr = min(1.0, fuel.dlm_1hr / fuel.char_MoE);
		moisture_ratio_10_100hr = fuel.char_dlm / fuel.char_MoE;
	} else {
		moisture_ratio_1hr = 1.;
		moisture_ratio_10_100hr = 1.;
	}

	///////// Fraction of live grass fuel consumed

	if (moisture_ratio_livegrass >= 0.0 && moisture_ratio_livegrass <= 0.18) {
		fuel.fraction_consumed_livegrass = 1.;
	} else if (moisture_ratio_livegrass > 0.18 && moisture_ratio_livegrass <= 0.73) {
		fuel.fraction_consumed_livegrass = 1.1 - (0.62 * moisture_ratio_livegrass);
	} else if (moisture_ratio_livegrass > 0.73) {
		fuel.fraction_consumed_livegrass = 2.45 - (2.45 * moisture_ratio_livegrass);
	} else {
		fuel.fraction_consumed_livegrass = 0.;
		dprintf("fire.cpp>> moisture_ratio_livegrass = %f which is outside of expected range", moisture_ratio_livegrass);
	}

	///////// Fraction of 1hr fuel consumed
	if (moisture_ratio_1hr >= 0.0 && moisture_ratio_1hr <= 0.18) {
		fuel.fraction_consumed_1hr = 1.;
		//dprintf("1");
	} else if (moisture_ratio_1hr > 0.18 && moisture_ratio_1hr <= 0.73) {
		fuel.fraction_consumed_1hr = 1.1 - (0.62 * moisture_ratio_1hr);
		//dprintf("2");
	} else if (moisture_ratio_1hr > 0.73) {
		fuel.fraction_consumed_1hr = 2.45 - (2.45 * moisture_ratio_1hr);
		//dprintf("3");
	} else {
		fuel.fraction_consumed_1hr = 0.;
		dprintf("fire.cpp>> moist_1hr = %f which is outside of expected range", moisture_ratio_1hr);
	}

	///////// Fraction of 10hr fuel consumed                                 M_24
	if (moisture_ratio_10_100hr <= 0.12) {
		fuel.fraction_consumed_10hr = 1;
	} else {
		if ((moisture_ratio_10_100hr > 0.12 & moisture_ratio_10_100hr <= 0.51)) {
			fuel.fraction_consumed_10hr = min(1.0, 1.09 - 0.72 * moisture_ratio_10_100hr);
		} else {
			if ((moisture_ratio_10_100hr > 0.51 & moisture_ratio_10_100hr <= 1)) {
				fuel.fraction_consumed_10hr = 1.47 - (1.47 * moisture_ratio_10_100hr);
			} else {

				fuel.fraction_consumed_10hr = 0.;
			}
		}
	}

	///////// Fraction of 100hr fuel consumed                                 M_24
	if ((moisture_ratio_10_100hr <= 0.38)) {
		fuel.fraction_consumed_100hr = 0.98 - (0.85 * moisture_ratio_10_100hr);
	} else {
		if ((moisture_ratio_10_100hr > 0.38 & moisture_ratio_10_100hr <= 1)) {
			fuel.fraction_consumed_100hr = 1.06 - (1.06 * moisture_ratio_10_100hr);
		} else {
			fuel.fraction_consumed_100hr = 0.;
		}
	}

	////////// Fraction of 1000hr fuel consumed
	fuel.fraction_consumed_1000hr = (-0.80 * fuel.mw_weight) + 0.8;

	//////////////////////////Fuel consumption /////////////////////////////////////////////////////////////////////////////////////////////


	// note the minimum to ensure fuel_consumed is not even slightly greater than fuel (which would result in negative pools)
	fuel.fuel_consumed_livegrass_gDM = min(fuel.fuel_livegrass_gDM * fuel.fraction_consumed_livegrass, fuel.fuel_livegrass_gDM) ;
	fuel.fuel_consumed_1hr_gDM = min(fuel.fuel_1hr_gDM * fuel.fraction_consumed_1hr, fuel.fuel_1hr_gDM);
	fuel.fuel_consumed_10hr_gDM = min(fuel.fuel_10hr_gDM * fuel.fraction_consumed_10hr, fuel.fuel_10hr_gDM);
	fuel.fuel_consumed_100hr_gDM = min(fuel.fuel_100hr_gDM * fuel.fraction_consumed_100hr, fuel.fuel_100hr_gDM);
	fuel.fuel_consumed_1000hr_gDM =  min(fuel.fuel_1000hr_gDM * fuel.fraction_consumed_1000hr, fuel.fuel_1000hr_gDM);


	if (ifPandRresidencetime) {
		calculate_residence_time_PandR(fuel);
	} else {
		calculate_residence_time_RoS(fuel);
	};

	// MF - I don't undestand this code or the 'mixed fuel model' Veiko was talking about,
	//		I just tried to faithfully reproduce it.
	if (fuel.fuel_consumed_CE_grass > 0) {
		fuel.CE = 0.85 + 0.11 * pow(fuel.fuel_consumed_CE_grass / (fuel.fuel_consumed_CE_grass + fuel.fuel_consumed_CE_litter), 0.34);
	} else {
		fuel.CE = 0.; // no fire
	}
	//dprintf("fuel.CE = %f\n", fuel.CE);
}



////////////////////////////////////////////////////////////////////////////////////////
// remove_consumed_fuel_consumption_patch - INTERNAL FUNCTION
// REMOVES CONSUMED FUEL FROM A PATCH
// One needs to first have called calculate_fuel_consumption to know how much to remove
// Also update the standard LPJ-GUESS litter
// Seems to mostly replace the "calculate_emissions" function below

void combust_litter(Patch& patch) {


	patch.fuel.fuel_consumed_CE_litter = 0;
	patch.fuel.fuel_consumed_CE_grass = 0;

	// applied to both C and N pools for both heart and sapwood
	double wood_combustion_fraction = min(max(0.0, wood_fraction_1hr * patch.fuel.fraction_consumed_1hr + wood_fraction_10hr * patch.fuel.fraction_consumed_10hr + wood_fraction_100hr * patch.fuel.fraction_consumed_100hr + wood_fraction_1000hr * patch.fuel.fraction_consumed_1000hr), 1.0);
	double leaf_combustion_fraction =  min(max(0.0, patch.fuel.fraction_consumed_1hr), 1.0);


	////////////////////////////////////////////////////////////////////
	// First combust the old-style per PFT litter C and N pools

	patch.pft.firstobj();
	while (patch.pft.isobj) {
		Patchpft& patchpft = patch.pft.getobj();

		// Wood litter
		// Note only remove wood litter if it is initially positive
		if ((patchpft.pft.lifeform == TREE) && patchpft.cmass_litter_heart + patchpft.cmass_litter_sap >= 0.0) {

			// wood C combusted
			double combusted_C_wood_litter = wood_combustion_fraction * (patchpft.cmass_litter_sap + patchpft.cmass_litter_heart);

			// report fluxes
			report_spitfire_fluxes_pft(patch, patchpft.pft.id, combusted_C_wood_litter, wood_combustion_fraction * (patchpft.nmass_litter_sap + patchpft.nmass_litter_heart));

			// remove litter
			patchpft.cmass_litter_sap         *= (1.0 - wood_combustion_fraction);
			patchpft.cmass_litter_heart       *= (1.0 - wood_combustion_fraction);
			patchpft.nmass_litter_sap   *= (1.0 - wood_combustion_fraction);
			patchpft.nmass_litter_heart *= (1.0 - wood_combustion_fraction);

			// for the "mixed fuel emisisons model" whatever that this
			patch.fuel.fuel_consumed_CE_litter += combusted_C_wood_litter;

		}

		// Leaf and reproductive litter
		// litter C combusted
		double combusted_C_fine_litter = leaf_combustion_fraction * (patchpft.cmass_litter_leaf + patchpft.cmass_litter_repr);

		// report fluxes
		report_spitfire_fluxes_pft(patch, patchpft.pft.id, combusted_C_fine_litter, leaf_combustion_fraction * (patchpft.nmass_litter_leaf));

		// remove litter
		patchpft.cmass_litter_leaf        *= (1.0 - leaf_combustion_fraction);
		patchpft.cmass_litter_repr        *= (1.0 - leaf_combustion_fraction);
		patchpft.nmass_litter_leaf  *= (1.0 - leaf_combustion_fraction);

		// for the "mixed fuel emisisons model" whatever that this
		if (patchpft.pft.lifeform == TREE) patch.fuel.fuel_consumed_CE_litter += combusted_C_fine_litter;
		else  patch.fuel.fuel_consumed_CE_grass += combusted_C_fine_litter;

		patch.pft.nextobj();

	}

	// Second combust the SOM pools
	if(ifcentury){

		double total_C_emitted = 0;

		// Surface metabolic and structural litter
		// fluxes (note use of SOM-tracked emissions factors)
		report_spitfire_fluxes_standard(patch, leaf_combustion_fraction * (patch.soil.sompool[SURFMETA].cmass + patch.soil.sompool[SURFSTRUCT].cmass), leaf_combustion_fraction * (patch.soil.sompool[SURFMETA].nmass + patch.soil.sompool[SURFSTRUCT].nmass));
		report_spitfire_fluxes_other(patch, leaf_combustion_fraction * patch.soil.sompool[SURFSTRUCT].cmass,  patch.soil.sompool[SURFSTRUCT].em_CO2, patch.soil.sompool[SURFSTRUCT].em_CO, patch.soil.sompool[SURFSTRUCT].em_CH4, patch.soil.sompool[SURFSTRUCT].em_TPM, patch.soil.sompool[SURFSTRUCT].em_VOC);
		report_spitfire_fluxes_other(patch, leaf_combustion_fraction * patch.soil.sompool[SURFMETA].cmass,  patch.soil.sompool[SURFMETA].em_CO2, patch.soil.sompool[SURFMETA].em_CO, patch.soil.sompool[SURFMETA].em_CH4, patch.soil.sompool[SURFMETA].em_TPM, patch.soil.sompool[SURFMETA].em_VOC);

		total_C_emitted = leaf_combustion_fraction * (patch.soil.sompool[SURFMETA].cmass + patch.soil.sompool[SURFSTRUCT].cmass);


		//dprintf("patch.soil.sompool[SURFSTRUCT].em_CO2 = %f\n", patch.soil.sompool[SURFSTRUCT].em_CO2);
		//dprintf("patch.soil.sompool[SURFMETA].em_CO2 = %f\n", patch.soil.sompool[SURFMETA].em_CO2);
		//dprintf("patch.soil.sompool[SURFFWD].em_CO2 = %f\n", patch.soil.sompool[SURFFWD].em_CO2);
		//dprintf("patch.soil.sompool[SURFCWD].em_CO2 = %f\n", patch.soil.sompool[SURFCWD].em_CO2);

		// remove litter
		patch.soil.sompool[SURFMETA].cmass *=  1.0- leaf_combustion_fraction;
		patch.soil.sompool[SURFMETA].nmass *=  1.0- leaf_combustion_fraction;
		patch.soil.sompool[SURFSTRUCT].cmass *=  1.0- leaf_combustion_fraction;
		patch.soil.sompool[SURFSTRUCT].nmass *=  1.0- leaf_combustion_fraction;


		// Fine and coarse woody debris
		// fluxes (note use of SOM-tracked emissions factors)
		report_spitfire_fluxes_standard(patch, wood_combustion_fraction * (patch.soil.sompool[SURFFWD].cmass + patch.soil.sompool[SURFCWD].cmass), wood_combustion_fraction * (patch.soil.sompool[SURFFWD].nmass + patch.soil.sompool[SURFCWD].nmass));
		report_spitfire_fluxes_other(patch, wood_combustion_fraction * patch.soil.sompool[SURFFWD].cmass,  patch.soil.sompool[SURFFWD].em_CO2, patch.soil.sompool[SURFFWD].em_CO, patch.soil.sompool[SURFFWD].em_CH4, patch.soil.sompool[SURFFWD].em_TPM, patch.soil.sompool[SURFFWD].em_VOC);
		report_spitfire_fluxes_other(patch, wood_combustion_fraction * patch.soil.sompool[SURFCWD].cmass,  patch.soil.sompool[SURFCWD].em_CO2, patch.soil.sompool[SURFCWD].em_CO, patch.soil.sompool[SURFCWD].em_CH4, patch.soil.sompool[SURFCWD].em_TPM, patch.soil.sompool[SURFCWD].em_VOC);

		total_C_emitted += wood_combustion_fraction * (patch.soil.sompool[SURFFWD].cmass + patch.soil.sompool[SURFCWD].cmass);

		// remove litter
		patch.soil.sompool[SURFFWD].cmass *=  1.0- wood_combustion_fraction;
		patch.soil.sompool[SURFFWD].nmass *=  1.0- wood_combustion_fraction;
		patch.soil.sompool[SURFCWD].cmass *=  1.0- wood_combustion_fraction;
		patch.soil.sompool[SURFCWD].nmass *=  1.0- wood_combustion_fraction;


		// to report per-PFT fluxes from, the SOM pools, split emissions by land cover fractions i.e. FPC (following TRENDY protocol)
		// if there is negligible FPC we have a problem.  In this case, allocate emissions proportional to potential forest floor NPP for all PFTs that can establish.
		// Emissions is allocated to PFTs based on their FPC, so first calculate total FPC
		double total_fpc = 0.0;
		Vegetation& vegetation = patch.vegetation;
		for(unsigned int k = 0; k < vegetation.nobj; k++) {
			Individual& indiv = vegetation[k];
			if(indiv.alive) total_fpc += indiv.fpc;
		}

		// If total_fpc is not negligible, split emissions across proportional to FPC
		if(!negligible(total_fpc, -8)) {
			for(unsigned int k = 0; k < vegetation.nobj; k++) {
				Individual& indiv = vegetation[k];
				if(indiv.alive) indiv.report_flux(Fluxes::C_FIRE, total_C_emitted * indiv.fpc / total_fpc);
			}
		}
		// if FPC is neglibigle, then assign proportional to "NPP at the forest floor" of each patchpft
		else {

			// first get the total anetps_ff for all PFTs that can establish
			double total_anetps_ff = 0.0;
			patch.pft.firstobj();
			while (patch.pft.isobj) {
				Patchpft& pft = patch.pft.getobj();
				pft.establish = establish(patch, patch.stand.get_gridcell().climate, pft.pft);
				if(pft.establish) total_anetps_ff += pft.anetps_ff;
				patch.pft.nextobj();
			}

			if(total_anetps_ff > 0.0) {
				// now allocated proportionally to anetps_ff
				patch.pft.firstobj();
				while (patch.pft.isobj) {
					Patchpft& pft = patch.pft.getobj();
					if(pft.establish) patch.fluxes.report_flux(Fluxes::C_FIRE, pft.id, total_C_emitted * pft.anetps_ff / total_anetps_ff);
					patch.pft.nextobj();
				}
			}
			else {
				dprintf("SPITFIRE DEBUG:: Lost per-PFT emissions form SOM pools because no FPC or anetps_ff.");
			}

		} // if ngeligible FPC

	} // if CENTURY


	// TODO No contribution of SOM pools to mixed fuel emissions model yet


}


void combust_grass(Patch& patch, Individual& indiv, double fraction_consumed) {

	double leaf_frac_remaining = max(0.00, 1.0 - fraction_consumed);

	// first flush to atmosphere C and N
	// POTENTIAL BUG: MF 2020-07-21 Note that for an unknown reason intercrop grasses can have negative leaf biomass.  This should be resolved before we start burning croplands
	// and combusting them with the code below
	if(indiv.alive) {
		report_spitfire_fluxes_pft(patch, indiv.pft.id, indiv.cmass_leaf * (1.0 - leaf_frac_remaining) * patch.stand.scale_LC_change, indiv.nmass_leaf * (1.0 - leaf_frac_remaining));
	}
	// if not alive report only N (must be like this to balance N)
	else {
		report_spitfire_fluxes_pft(patch, indiv.pft.id, 0.0, indiv.nmass_leaf * (1.0 - leaf_frac_remaining));
	}

	// reduce leaf C and N
	indiv.cmass_leaf *= leaf_frac_remaining;
	indiv.nmass_leaf *= leaf_frac_remaining;

}


void combust_tree(Patch& patch, Individual& indiv, double crown_scorch_fraction, double prop_fire_affected){


	// proportion of live wood combusted (assuming all one-hour fuel and 5% of 10hr fuel (Thonicke et al. 2010))
	double prop_live_wood_burnt = wood_fraction_1hr + (0.05 * wood_fraction_10hr);


	// calculate how much C and N is combusted from each pool
	double cflux_fire_leaf = indiv.cmass_leaf * prop_fire_affected * crown_scorch_fraction;
	double cflux_fire_sap = indiv.cmass_sap * prop_fire_affected * crown_scorch_fraction * prop_live_wood_burnt;
	double cflux_fire_heart = indiv.cmass_heart* prop_fire_affected * crown_scorch_fraction * prop_live_wood_burnt;

	double nflux_fire_leaf = indiv.nmass_leaf * prop_fire_affected * crown_scorch_fraction;
	double nflux_fire_sap  = indiv.nmass_sap * prop_fire_affected * crown_scorch_fraction * prop_live_wood_burnt;
	double nflux_fire_heart = indiv.nmass_heart* prop_fire_affected * crown_scorch_fraction * prop_live_wood_burnt;

	// also make totals
	double cflux_fire = cflux_fire_leaf + cflux_fire_sap + cflux_fire_heart;
	double nflux_fire = nflux_fire_leaf + nflux_fire_sap + nflux_fire_heart;


	// send these total fluxes to the atmosphere
	// if alive report all
	if(indiv.alive) {
		report_spitfire_fluxes_pft(patch, indiv.pft.id, cflux_fire_leaf + cflux_fire_sap + cflux_fire_heart, nflux_fire_leaf + nflux_fire_sap + nflux_fire_heart);
	}
	// if not alive report only N (must be like this to balance N)
	else {
		report_spitfire_fluxes_pft(patch, indiv.pft.id, 0.0, nflux_fire_leaf + nflux_fire_sap + nflux_fire_heart);
	}

	// reduce the pools
	indiv.cmass_leaf -= cflux_fire_leaf;
	indiv.cmass_sap -= cflux_fire_sap;
	indiv.cmass_heart -= cflux_fire_heart;

	indiv.nmass_leaf -= nflux_fire_leaf;
	indiv.nmass_sap -= nflux_fire_sap;
	indiv.nmass_heart -= nflux_fire_heart;

}



bool tree_mortality_spitfire(Patch& patch, Individual& indiv, double postf_mort) {

	// This code very much follows the standard LPJ-GUESS means of handling mortality, except
	// 1. There is no "fire mortality" since all fluxes due do combustion have already been done
	// 2. Note the extra flux balancing when objects are killed to account for NPP accumulated in this year up to this point


	bool killed = false;

	int nindiv;
	int nindiv_prev;
	double frac_survive;

	if (ifstochmort) {

		// Impose stochastic mortality
		// Each individual in cohort dies with probability 'mort_fire'

		// Number of individuals represented by 'indiv'
		// (round up to be on the safe side)

		nindiv=(int)(indiv.densindiv*patcharea+0.5);
		nindiv_prev=nindiv;

		for (int i=0;i<nindiv_prev;i++) {
			if (randfrac(patch.stand.seed) < postf_mort) nindiv--;
		}

		if (nindiv_prev)
			frac_survive=(double)nindiv/(double)nindiv_prev;
		else
			frac_survive=0.0;
	}

	// Deterministic mortality (cohort mode only)
	else frac_survive=1.0-postf_mort;

	// TODO Remove this alive check, Individuals should potentially die in their first year
	// But currently this is needed to balance C :-/
	if(indiv.alive) {

		// Reduce individual biomass on patch area basis
		// to account for loss of killed individuals
		double mortality_temp = 1.0 - frac_survive;
		indiv.reduce_biomass(mortality_temp, 0.0);

		// accumulate tree cover reduction by fire
		patch.fuel.mtreecover_reduction_fire[date.month] += indiv.fpc * mortality_temp;

#ifdef FULLDEBUG


		dprintf("-----------------------------------------------------------------\n");
		dprintf("%s TREE BURNED!\n", (char*)indiv.pft.name);
		dprintf("Density initial = %f\n", indiv.densindiv);
		dprintf("Density killed = %f\n", nind_kill);
		dprintf("Fraction killed = %f\n", nind_kill/indiv.densindiv);
		dprintf("Fire intensity = %f kW/m\n", patch.fuel.daily_fire_intensity);
		dprintf("Age = %f years \n", indiv.age);
		dprintf("Height = %f m\n", indiv.height);
		dprintf("Diameter = %f cm\n", dbh);
		dprintf("Bark Thickness = %f cm\n", bark_thickness_cm);
		dprintf("Scorch Height = %f m\n", patch.fuel.scorch_height);
		dprintf("Canopy fraction burned = %f\n", ck);
		dprintf("Residence time (RoS) = %f minutes\n", patch.fuel.tau_l );
		dprintf("gamma_f = %f \n", patch.fuel.gamma_f);
		dprintf("Critical time = %f minutes\n", tau_c);
		dprintf("Soil moisture = %f\n", patch.soil.dwcontupper[date.day]);
		dprintf("DLM livegrass = %f\n", patch.fuel.dlm_livegrass);
		dprintf("Prob Cambial Kill = %f, Prob Crown Kill = %f\n", pm_tau, pm_ck);


#endif

		// Remove this cohort completely if all individuals killed
		// (in individual mode: removes individual if killed)
		if (negligible(indiv.densindiv)) {

			// First take care of the annual NPP of this individual so far, otherwise C won't balance
			if(indiv.anpp > 0.0) {
				patch.pft[indiv.pft.id].cmass_litter_leaf += indiv.anpp;
			}
			else {
				indiv.report_flux(Fluxes::NPP, -indiv.anpp);
			}

			patch.vegetation.killobj();
			killed=true;
		}

	} // if alive check


	return(killed);

}



////////////////////////////////////////////////////////////////////////////////////////
// calculate_fire_intensity - INTERNAL FUNCTION
// SIMPLE ROUTINE TO CALCULATE FIRE INTENSITY
// Must be called after for calculate_fuel_consumption and forward_Rothermel_ROS

void calculate_fire_intensity(Fuel_patch& fuel) {

	double fuel_consumed = (fuel.fuel_consumed_1hr_gDM + fuel.fuel_consumed_10hr_gDM + fuel.fuel_consumed_100hr_gDM + fuel.fuel_consumed_livegrass_gDM) * DM_C;

	fuel.daily_fire_intensity = H * (fuel_consumed / 1000 / DM_C) * fuel.ros_f / 60; // surface intensity in kW/m fireline


#if defined(ERRORDEBUG) || defined(FULLDEBUG)
	if ((fuel.daily_fire_intensity != fuel.daily_fire_intensity) || fuel.daily_fire_intensity > 1000000) {
		//printf("SPITFIRE_ERROR: Crazy fire intensity!  Fire intensity = %f\n", patch.fuel.daily_fire_intensity);
	}
#endif

#if defined(FULLDEBUG)
	if (patch.fuel.daily_fire_intensity > 100000) {
		//printf("SPITFIRE WARNING: Very high Fire Intensity (= %f)\n", patch.fuel.daily_fire_intensity);
	}
#endif

}

////////////////////////////////////////////////////////////////////////////////////////
// calculate_scorch_height - INTERNAL FUNCTION
// SIMPLE ROUTINE TO CALCULATE SCORCH HEIGHT
// Must be called after for calculate_fuel_consumption and forward_Rothermel_ROS

void calculate_scorch_height(Patch& patch) {

	//  MF COMMENT FROM VEIKO ON SCORCH HEIGHT
	//fire height is very high compared to empirical values, but since it represents scorch height and not flame heightis too high at low intensities according to the formula below
	//Cheney gives the following empirical values <500 kw/m ->max 1.5; 500-3000 ->max 6m 7000=15m this is approximal I/500*. pft.flame pft.flame is between 0.3 and 0.09 these values are not reasonable and not reproducable
	// Veiko: however these are the flame height which are lower than the scorch height this is one of the places where an improvement should occurr


	// get the weighted F parameter
	double char_F = 0.0;
	double woody_FPC = 0.0;

	patch.vegetation.firstobj();
	while (patch.vegetation.isobj) {
		Individual& indiv = patch.vegetation.getobj();

		// MF - either by chance or design, grasses were contributing with 0 towards F
		// currently reproducing that, but should maybe be reevaluated
		//if (indiv.pft.lifeform == TREE) {
		char_F += indiv.pft.flame * indiv.fpc;
		woody_FPC += indiv.fpc;
		//patch.pft[indiv.pft.id]}

		patch.vegetation.nextobj();
	};

	// divide through by FPC
	if(woody_FPC > 0) {	char_F /= woody_FPC; }
	else { char_F = 0.0; }

	// temp check
	// if(abs(char_F - patch.fuel.char_F) > 0.000001) dprintf("F parameters don't match %f != %f \n", patch.fuel.char_F, char_F);

	// MF Verified Eq. 16.
	patch.fuel.scorch_height = char_F * pow(patch.fuel.daily_fire_intensity, 0.667); //scorch height ... = flame height at which crown scorching occures SPITFIRE org

#if defined(ERRORDEBUG) || defined(FULLDEBUG)
	if ((patch.fuel.scorch_height != patch.fuel.scorch_height)) {
		printf("SPITFIRE: SCORCH_HEIGHT_WARNING: Scorch height  = %f, char_F = %f, fire_intensity = %f \n", patch.fuel.scorch_height, patch.fuel.char_F, patch.fuel.daily_fire_intensity);
	}
#endif

#if defined(FULLDEBUG)
	if (patch.fuel.scorch_height > 50) {
		printf("SPITFIRE: SCORCH_HEIGHT_WARNING: Scorch height  = %f, char_F = %f, fire_intensity = %f \n", patch.fuel.scorch_height, patch.fuel.char_F, patch.fuel.daily_fire_intensity);
	}
#endif

}


////////////////////////////////////////////////////////////////////////////////////////
// fire_intensity - INTERNAL FUNCTION
// SIMPLE ROUTINE TO CALCULATE FIRE INTENSITY
// Must be called after for calculate_fuel_consumption and forward_Rothermel_ROS

double fire_duration(double fdi, double daylength, double pop_dens ) {


	// calculate the absolute maximum duration based on the instructions file parameters
	double max_duration_mins;
	if(max_fire_duration == 0) max_duration_mins = daylength * 60;
	else max_duration_mins = max_fire_duration * 60;

	// if selected, reduce duration due to human suppression (down to a minimum of min_duration_mins)
	// note also that if pop density is not greater than zero, maximum durarion is not adjusted
	if(ifpopulationsuppression && pop_dens > 0.0){
		double min_duration_mins = min_fire_duration * 60;
		// Formula below is a generalization of the Hantson et al 2015 suppression formula (as implemented in JSBACH).
		// The original formaultion reduces duration linearly as a function of log10(pop_dens), with max duration of 12 hours at
		// pop_dens = 0.01 and below, and a minimum duration of 4 hours at pop_dens = 100 and above.
		// The formula below instead uses arbitrary min and max values but scales over the same population dens range.
		max_duration_mins = min(max(min_duration_mins + ((max_duration_mins - min_duration_mins) * (2-log10(pop_dens))/4), min_duration_mins), max_duration_mins);
	}

	// dprintf("max_duration_mins = %f, actual duration = %f\n", max_duration_mins, (max_duration_mins+1) / (1 + (max_duration_mins * exp(-11.06 * fdi))));

	// finally calculate the fire danger index suppression and return
	return((max_duration_mins+1) / (1 + (max_duration_mins * exp(-11.06 * fdi))));


}

////////////////////////////////////////////////////////////////////////////////////////
// check_fire_possibility - INTERNAL FUNCTION
// CHECKS FIRE POSSIBILITY BASED ON MINIMUM FUEL AND FIRE INTENSITY THRESHOLDS

void check_fire_possibility(Patch& patch, double min_fire_intensity, double min_finefuel_gC) {

	double finefuel_gC = (patch.fuel.fuel_1hr_gDM + patch.fuel.fuel_livegrass_gDM) * DM_C;

	//if (finefuel_gC >= min_finefuel_gC && patch.fuel.daily_fire_intensity >= min_fire_intensity) {
	if (finefuel_gC >= min_finefuel_gC) {
		patch.fuel.possible = true;
		//patch.fuel.allocation_fail_code = 0;
		//dprintf("Fire possible! Enough fuel (%f) and intensity (%f) \n",patch.fuel.net_fuel, patch.fuel.daily_fire_intensity);
	} else if (finefuel_gC >= min_finefuel_gC) {

		patch.fuel.possible = false;
		//patch.fuel.allocation_fail_code = 1;
		//dprintf("Enough fuel (%f) but not enough intensity (%f) Fire NOT possible!\n", patch.fuel.net_fuel, patch.fuel.daily_fire_intensity);
	} else if (patch.fuel.daily_fire_intensity >= min_fire_intensity) {

		patch.fuel.possible = false;
		//patch.fuel.allocation_fail_code = 2;

		//dprintf("Enough intensity (%f) but not enough fuel (%f) Fire NOT possible!\n", patch.fuel.daily_fire_intensity, patch.fuel.net_fuel);
	} else {

		patch.fuel.possible = false;
		//patch.fuel.allocation_fail_code = 3;

		//dprintf("Not enough intensity (%f) and not enough fuel (%f) Fire NOT possible!\n", patch.fuel.daily_fire_intensity, patch.fuel.net_fuel);
	}

}


///////////////////////////////////////////////////////////////////////////////////////
// ALLOCATE FIRE TO PATCHES (based on which patches can burn)
// Here, if we are using monthly prescribed BA, we check the fuel characteristics
// and ensure that only patches with sufficient fuel can burn

void allocate_fire_to_patches(Stand& stand, Climate& climate) {

	// initial thresholds for fire
	// these will be incrementally decreased until we can allocate all burnt area
	double min_fire_intensity = 0.0; // kW/m^2
	double min_finefuel_gC = fuelthreshold * 1000; //gC/m^2 - now read in from the .ins file

	// reset the diagnostics on the first day of the year
	if (date.dayofmonth == 0) {
		climate.monthly_mean_num_iterations[date.month] = 0;
		climate.monthly_num_fails[date.month] = 0;
	}

	// Calculate gridcell areas
	double area_km2 = (110.45 * pixeldegree) * (111.1944 * pixeldegree) * cos(climate.lat * (PI / 180));
	double area_ha = area_km2 * 100;

	//calculate gridcell areas THOMAS
	// mean radius of the earth (km)
	double radius_Earth = 6367.425;
	double lat_upper = climate.lat + pixeldegree / 2;
	double lat_lower = climate.lat - pixeldegree / 2;

	double h1 = radius_Earth * sin(lat_upper * PI / 180.0);
	double h2 = radius_Earth * sin(lat_lower * PI / 180.0);
	double area_band = 2.0 * PI * radius_Earth * (h1 - h2); //area of this latitude band

	if (area_band < 0) {
		dprintf("Woops - negative area of latitude bad. Area is %f\n", area_band);
		abort();
	}

	double area_km2_TH = area_band * (pixeldegree / 360);

	// BA this day
	double burnt_area = double(climate.burntarea[date.day]);

	//if(date.day == 260){
	// dprintf("allocate:: year = %i, day = %i, BA = %f\n ", date.year, date.day, burnt_area );
	//}


	// CASE 1 - IF BA = 0 (or negative), set all patches to not suitable and zero probability of fire and then exit
	// This will probably never get called, but just doing it to be safe
	if (burnt_area <= 0.0) {

		stand.firstobj();
		while (stand.isobj) {
			Patch& patch = stand.getobj();
			patch.fuel.fire_prob = 0;
			patch.fuel.possible = false;
			stand.nextobj();
		}

		// just in case as error in input data
		if (burnt_area == -999999.000000) {
			burnt_area = 0;
		}
		if (burnt_area < 0.0) {
			dprintf("spitfire.cpp>> Negative burnt area, unphysical input data!\n");
			dprintf("year = %i, BA = %f\n", date.year, burnt_area);
			abort();
		}

		return;
	}

	// CASE 2 - if we have positive BA
	// This is the main function of the code where we allocate BA (or rather probability of burning)
	// only to patches with conditions suitable for fire


	else {

		// boolean which is set to true if BA has been allocated
		bool all_allocated = false;

		// burning probability (dependent on the number of suitable patches)
		double burning_probability;

		// fractional area burned
		double fractional_burned_area;
		if (date.year - nyear_spinup + 1948 < 1996) {
			fractional_burned_area = burnt_area;
			//dprintf("date.year = %i, real.year = %i, BA (not divided) = %f\n", date.year, date.year - nyear_spinup + 1948,  fractional_burned_area);
		} else {
			fractional_burned_area = burnt_area / area_ha;
			//dprintf("date.year = %i, real.year = %i, BA (divided) = %f\n", date.year, date.year - nyear_spinup + 1948,  fractional_burned_area);
		}

		/****** FIRST FIND PATCHES WHICH CAN BURN (SUITABLE) BASED ON MINIMUM FUEL REQUIREMENTS ******/

		int num_suitable_patches = 0;
		int temp_counter = 0;
		while (!all_allocated) {

			// First calculate in which patches fire is considered possible and keep a tally
			num_suitable_patches = 0;
			stand.firstobj();
			while (stand.isobj) {
				Patch& patch = stand.getobj();
				check_fire_possibility(patch, min_fire_intensity, min_finefuel_gC);
				if (patch.fuel.possible)
					num_suitable_patches++;
				stand.nextobj();
			}

			// fraction of patches suitable for fire
			double fraction_patches_suitable = double(num_suitable_patches) / double(npatch);

			if (fraction_patches_suitable > 0.0 && fractional_burned_area / fraction_patches_suitable <= 0.5) {
				burning_probability = fractional_burned_area / fraction_patches_suitable;
				all_allocated = true;
				climate.monthly_mean_num_iterations[date.month] += temp_counter;
			} else {
				// if we haven't broken out of the loop reduce the thresholds by 10%
				min_fire_intensity *= 0.9;
				min_finefuel_gC *= 0.9;
				temp_counter++;

				/*

				 //  Here are some temporary diagnostic outputs
				 double mean_total_fuel = 0;
				 double mean_fire_intensity =0;
				 stand.firstobj();
				 while (stand.isobj) {
				 Patch& patch = stand.getobj();
				 mean_fire_intensity += patch.fuel.daily_fire_intensity;
				 mean_total_fuel += patch.fuel.deadfuel + patch.fuel.fuel_livegrass;
				 stand.nextobj();
				 }
				 mean_fire_intensity /= npatch;
				 mean_total_fuel /= npatch;

				 dprintf("Temp diagnostic. fuel = %f, intensity = %f\n", mean_total_fuel, mean_fire_intensity);

				 */

				// if after 20 tries we still don't have enough suitable patches,
				// allocat burned area to all patches equally and break
				if (temp_counter >= 20) {

					// set burning probability to BA fractopm
					burning_probability = fractional_burned_area;
					num_suitable_patches = npatch; //correctd 08.10.14

					// for diagnostics calculate mean fuel and intensity
					double mean_total_fuel = 0;
					double mean_fire_intensity = 0;

					// allow all patches to burn
					stand.firstobj();
					while (stand.isobj) {
						Patch& patch = stand.getobj();
						patch.fuel.possible = true;
						mean_fire_intensity += patch.fuel.daily_fire_intensity;
						mean_total_fuel += patch.fuel.deadfuel_gDM + patch.fuel.fuel_livegrass_gDM;
						stand.nextobj();
					}
					mean_fire_intensity /= npatch;
					mean_total_fuel /= npatch;

					//dprintf("NOT OK breaking out after 20 iterations. fuel = %f, intensity = %f\n", mean_total_fuel, mean_fire_intensity);
					all_allocated = true;
					climate.monthly_num_fails[date.month]++;

				} // end if more than 20 iterations

			} //end if/else allocation was successful

		} //end while !all_allocated


		stand.firstobj();
		while (stand.isobj) {
			Patch& patch = stand.getobj();
			if (patch.fuel.possible) {
				patch.fuel.fire_prob = burning_probability;
			} else {
				patch.fuel.fire_prob = 0;
			}
			stand.nextobj();
		}

		if (ifallocatebytreecover) {

			double total_unnormalised_prob = 0;

			stand.firstobj();
			while (stand.isobj) {
				Patch& patch = stand.getobj();
				if (patch.fuel.possible) {
					double X = min(patch.fuel.FPC_high, 1.0) * 100;
					double Mtreecover = 0.0;
					double a = -1.632927263;
					double b = 1.325719961;
					double c = -0.240939956;
					double d = 0.009068023;
					Mtreecover = exp(a + b * pow(X, 0.5) + c * X + d * pow(X, 1.5)) - 1;
					patch.fuel.unnormalised_fire_prob = burning_probability + (burning_probability * Mtreecover);
					total_unnormalised_prob += patch.fuel.unnormalised_fire_prob;

				}
				stand.nextobj();
			}

			double avg_unnormalised_probability = total_unnormalised_prob / num_suitable_patches;
			double normalising_factor = fractional_burned_area / max(avg_unnormalised_probability, 0.000000001);

			stand.firstobj();
			while (stand.isobj) {
				Patch& patch = stand.getobj();
				if (patch.fuel.possible) {
					patch.fuel.fire_prob = patch.fuel.unnormalised_fire_prob * normalising_factor;
					if (patch.fuel.fire_prob > 1) {
						dprintf("SPITFIRE_ERROR: patch.fuel.fire_prob > 1 (%f)\n", patch.fuel.fire_prob);
					}
				}
				stand.nextobj();
			}

		}

		double check_total_prob = 0;
		stand.firstobj();
		while (stand.isobj) {
			Patch& patch = stand.getobj();
			check_total_prob += patch.fuel.fire_prob;
			stand.nextobj();
		}

		if (fabs(check_total_prob / npatch - fractional_burned_area) > 0.0001) {

			dprintf("------- ALLOCATION ERROR ------------\n");
			dprintf("Initial prob = %f\n", fractional_burned_area);
			dprintf("Not OK! Iterations = %i\n", temp_counter);
			dprintf("Final   prob = %f\n", check_total_prob / npatch);
			dprintf("--------------------------\n");

		}

		return;

	} // end if/else burnt area positive

	return;

}

void dailyaccounting_gridcell_spitfire(Gridcell& gridcell) {

	// First day of year only
	if(date.day == 0){

		// Reset burnt area accumulators gridcell level burnt area accumulators
		gridcell.annual_burned_area = 0.0;
		for (int i = 0; i < 12; i++) {
			gridcell.monthly_burned_area[i] = 0.0;
		}


		// Update the special patch-level scaling factor for output based on the flammable area in the gridcell only

		// Determine flammable fraction
		double flammable_fraction = 0.0;
		Gridcell::iterator gc_itr = gridcell.begin();
		while (gc_itr != gridcell.end()) {
			Stand& stand = *gc_itr;
			// only look at first patch, assume that all patches in the stand have same flammability
			stand.firstobj();
			Patch& patch = stand.getobj();
			if(patch.has_fires()) flammable_fraction += stand.get_gridcell_fraction();
			++gc_itr;
		}

		// now that we have the flammable fraction, loop again to assign the scaling factor to the patch
		gc_itr = gridcell.begin();
		while (gc_itr != gridcell.end()) {
			Stand& stand = *gc_itr;

			// look at first patch, assume that all patches
			stand.firstobj();
			while (stand.isobj) {
				Patch& patch = stand.getobj();
				if(patch.has_fires()) patch.to_gridcell_average_flammable_only = (stand.get_gridcell_fraction() / (double)stand.npatch()) / flammable_fraction;
				else patch.to_gridcell_average_flammable_only = 0.0;
				stand.nextobj();
			}
			++gc_itr;
		}

	}

}




void spitfire_dailyaccounting(Stand& stand, Climate& climate) {




	// All the rest of the accounting is done for each patch
	stand.firstobj();
	while (stand.isobj) {
		Patch& patch = stand.getobj();

		// if first simulation days
		if (date.day == 0 && date.year == 0) {
			// set burnt area history variables to zero
			patch.days_since_last_burn = 0;
			for(int m = 0; m < 12; m++){
				patch.mfirefrac[m] = 0.0;
				patch.mfirefrac_applied[m] = 0.0;
			}

		}
		else {
			// Increment number of days since last burn
			patch.days_since_last_burn++;
		}

		// If first day on month set fire day variables to 0
		if (date.dayofmonth == 0) {

			patch.fuel.monthly_number_fires[date.month] = 0;
			patch.fuel.monthly_realised_intensity[date.month] = 0;
			patch.fuel.monthly_realised_nesterov[date.month] = 0;
			patch.fuel.monthly_realised_duration[date.month] = 0;
			patch.fuel.monthly_realised_residence_time[date.month] = 0;
			patch.fuel.monthly_realised_scorch_height[date.month] = 0;
			patch.fuel.monthly_realised_fire_size[date.month] = 0;
			patch.fuel.monthly_realised_livegrass_cc[date.month] = 0;
			patch.fuel.monthly_realised_1hr_cc[date.month] = 0;
			patch.fuel.monthly_realised_10hr_cc[date.month] = 0;
			patch.fuel.monthly_realised_100hr_cc[date.month] = 0;
			patch.fuel.monthly_realised_1000hr_cc[date.month] = 0;
			patch.fuel.monthly_realised_RoS[date.month] = 0;
			patch.fuel.monthly_realised_DFM[date.month] = 0;
			patch.fuel.monthly_realised_fire_speed[date.month] = 0;

			// monthly fire fractions
			patch.mfirefrac[date.month] = 0.0;
			patch.mfirefrac_applied[date.month] = 0.0;

		}

		stand.nextobj();

	}

	if (firemodel == PRESCR_BURNT_AREA) {

		stand.firstobj();
		while (stand.isobj) {
			Patch& patch = stand.getobj();

			// Calculate the fuel load, fuel consumption and intensity of each patch to determine which a suitable for fire
			// MF: probably need to add a lot of extra things here as a consequence of the code refactoring
			//     check start of spitfire_daily to see what
			//fuel_loading(patch);
			//calculate_fuel_consumption(patch.fuel);
			//calculate_fire_intensity(patch.fuel);

			stand.nextobj();
		}

		allocate_fire_to_patches(stand, climate);
	}
}

void print_fire(Patch& patch) {

	dprintf("*******************************************************************************************\n");
	dprintf("FIRE! in patch = %i, month = %i, year = %i\n", patch.id, date.month, date.year);
	dprintf("*******************************************************************************************\n");

	printf("Vegetation present:\n");

	patch.vegetation.firstobj();
	while (patch.vegetation.isobj) {

		Individual& indiv = patch.vegetation.getobj();

		dprintf("----  %s --------- \n", (char*) indiv.pft.name);
		dprintf("Density initial = %f\n", indiv.densindiv);
		dprintf("Age = %f years \n", indiv.age);
		dprintf("Height = %f m\n", indiv.height);

		// next individual
		patch.vegetation.nextobj();
	}

	dprintf("*******************************************************************************************\n");

}

double cambial_mortality_spitfire(double residence_time, Individual& indiv) {


	double tau_c; // critical time for cambial damage in min						[min]
	double pm_tau; // prob of mort due to cambial damage							[ratio]


	// some preamble to get some quantities for individuals in SPITFIRE-friendly form

	int pft = indiv.pft.id;

	double dbh = pow((indiv.height / indiv.pft.k_allom2), (1 / indiv.pft.k_allom3)) * 100.0; //in cm //!eqn (C)
	//calculate fire damage quantities for this individiual: tau_c, cl_t

	// Verified.  Eqs. 20 and 21 Thonicke et al. 2010
	double bark_thickness_cm;

	if (pftlist[pft].barka >= 0) {
		bark_thickness_cm = (pftlist[pft].barka * dbh + pftlist[pft].barkb) / 10; //BT in cms
	} else if ((pftlist[pft].barka > -667) && (pftlist[pft].barka < -665)) { //savanna tree flag = -666
		bark_thickness_cm = (28.77 - 26.898 * pow(0.97391, dbh)) / 10; //BT in cms
	} else if ((pftlist[pft].barka > -778) && (pftlist[pft].barka < -776)) { //rainforest tree flag = -777
		bark_thickness_cm = (15.95 - 14.23 * pow(0.98456, dbh)) / 10; //BT in cms
	}

	tau_c = 2.9 * pow(bark_thickness_cm, 2.0);

	// If fire residence twice critical time definitely kill tree
	if ((residence_time / tau_c) >= 2.)
		pm_tau = 1;
	// If ratio of residence to critical time is greater than 0.22 apply formula
	// also don't let it go negative
	else if ((residence_time / tau_c) > 0.22)
		pm_tau = max(0.0, (0.5363 * (residence_time / tau_c)) - 0.125);
	// If ratio of residence to critical time is less than 0.22 then no chance of cambial kill
	else
		pm_tau = 0.;

	return(pm_tau);

}

double scorched_crown_fraction(double scorch_height, double indiv_height, double crown_length_fraction) {


	double cl_t; // crown length per height class		[m]
	double ck; // proportion of crown scorched			[ratio]

	// Verified.
	cl_t = indiv_height * crown_length_fraction;


	//MF Verified.  Crown scorch damage - Eqn. 17 Thonicke et al. 2010
	if ((scorch_height >= indiv_height)) // If scorch height greater than tree height, whole crown is scorched
		ck = 1.;
	else if (scorch_height < (indiv_height - cl_t)) // If scorch height smaller than bottom of crown, no crown damage
		ck = 0.0;
	else if ((scorch_height >= (indiv_height - cl_t)) && (scorch_height < indiv_height)) // If scorch comes part way up, kill appropriate proportion of crown
		ck = ((scorch_height - indiv_height + cl_t) / cl_t);

	return(ck);

}

/////////////////////////////////////////////////////////////////////////////////////////////
// Tree combustion through crown scorch
// INTERNAL FUNCTION
// Note that the fluxes to the atmosphere are done here, immediately to help ensure correct reporting and C, N balances


///////////////////////////////////////////////////////////////////////////////////////
// Fire DYNAMICS
// Should be called in the main guess.cpp patch loop

void spitfire_daily(Patch& patch, Climate& climate) {

	// dprintf("STARTING SPITFIRE in patch = %i!\n", patch.id);

	// on the first day of the simulation check which mode despite is running in, and fail if not
	if (date.day == 0 && date.year == 0 && !valid_spitfire_mode()) {
		fail("spitfire.cpp >> invalid SPITFIRE configuration options, check your .ins file!");
	}


	double calculated_fire_fraction = 0; // This is the BA fraction calculated by SPITFIRE ignitions or from prescribed BA (after allocation)
	double applied_fire_fraction = 0; // This is the BA fraction applied to a patch for when considering mortality and emissions.  This should be unity ifburnfullcell is turned on, or the calculated_fire_fraction if not
	bool burnPatch = false; // Set true when using ifburnfullcell and patch rolls to burn

	// MF Puuhhhh....
	double CE = -1.0;

	// Calculate gridcell area -  'new and improved' formula from Allan, corrects bug in previous version
	double area_km2 = (110.45 * pixeldegree) * (111.1944 * pixeldegree) * cos(climate.lat * (PI / 180));
	double area_ha = area_km2 * 100;

	// calculate fuel loading and fuel characteristics
	fuel_loading(patch);

	// effective wind speed
	patch.fuel.effective_wind = effective_wind_speed(patch, climate.u10);

	// fuel moisture
	// daily fuel moisture of live grass depends only on soil moisture
	// note minimum grass fuel moisture of 1%, this is fairly conservative since I haven't seen field measurements below ~4-5%
	patch.fuel.dlm_livegrass = max(0.01, ((10.0 / 9.0) * patch.soil.get_soil_water_upper()) - (1.0 / 9.0));

	// dead fuel moisture can be calculate via different models
	if (fuelmoisturemodel == ORIGINAL) {
		fuel_moisture_nesterov(patch, climate.gridcell.nesterov_cur);
	}
	else if(fuelmoisturemodel == DAILY_VPD){
		fuel_moisture_VPD(patch, climate.vpd, climate.prec);
	}


	// critical moisture -  calculate the ratio of fuel moisture content to moisture of extinction
	// which is used in the folowing Rothermel calculation and FDI calculations
	if (!negligible(patch.fuel.char_MoE) && patch.fuel.char_MoE > 0.0) {
		patch.fuel.mw_weight = min(1.0, patch.fuel.char_dlm / patch.fuel.char_MoE);
	} else {
		patch.fuel.mw_weight = 0.;
	}

	// Fire Danger Index
	patch.fuel.fdi = fdi(patch.fuel, climate.gridcell.nesterov_cur);

	// test burn probability (Wilson 1985)
	patch.fuel.burn_probability = burn_probability(patch.fuel.char_dlm, patch.fuel.char_sigma, (patch.fuel.deadfuel_gDM + patch.fuel.fuel_livegrass_gDM)/1000);
	//dprintf("fdi = %f, burn_probability = %f, diff = %f\n", patch.fuel.fdi, patch.fuel.burn_probability, patch.fuel.fdi - patch.fuel.burn_probability);


	// do the main Rothermel calculation for forward ROS (and the backwards)
	patch.fuel.ros_f = forward_Rothermel_ROS(patch.fuel);
	patch.fuel.ros_b = patch.fuel.ros_f * exp(-0.012 * patch.fuel.effective_wind);
	// MF - not quite sure where this came from, consider testing and removing
	if (patch.fuel.ros_b < 0.05) //0.05
		patch.fuel.ros_b = 0.;


	// calculate fire duration
	patch.fuel.fire_durat = fire_duration(patch.fuel.fdi, patch.stand.get_climate().daylength, climate.gridcell.pop_density);

	// calculate fire effects
	calculate_fuel_consumption(patch.fuel);
	calculate_fire_intensity(patch.fuel);
	calculate_scorch_height(patch);

	// MAIN BURNT AREA CALCULATION - details obviously depend on the mode in which we are running

	//////////// SPITFIRE MODE - for fully prognostic fires
	if (firemodel == SPITFIRE) {

		//  ******************** IGNITIONS ********************

		// set to zero
		patch.fuel.potential_human_ign = 0;
		patch.fuel.potential_lightning_ign = 0;

		// calculate the ignitons to be used if the sources are enabled
		double full_human_ignitions = human_ignitions(climate.gridcell.pop_density, climate.gridcell.aNd) * area_ha;
		double full_lightning_ignitions = lightning_ignitions(climate.gridcell.lightning) * area_ha;


		// If "natural" ie NATURAL or FOREST (managed forest)
		if(patch.stand.landcover == NATURAL || patch.stand.landcover == FOREST) {
			if (ignitionmode == HUMAN || ignitionmode == BOTH) {
				patch.fuel.potential_human_ign = full_human_ignitions;
				//dprintf("year = %i, pop_dens = %f, human ignitions = %f\n", date.year, climate.population_density, patch.fuel.potential_human_ign);
			}
			if (ignitionmode == LIGHTNING || ignitionmode == BOTH) {
				patch.fuel.potential_lightning_ign = full_lightning_ignitions;
				//dprintf("year = %i, pop_dens = %f, human ignitions = %f\n", date.year, climate.population_density, patch.fuel.potential_human_ign);
			}
		}

		// If pasture
		else if(patch.stand.landcover == PASTURE) {


			// full ignitions
			if(pasturefiremode == FULL_PASTURE_BURNING){
				patch.fuel.potential_human_ign = full_human_ignitions;
				patch.fuel.potential_lightning_ign = full_lightning_ignitions;
			}
			// allow only lightning fires
			else if(pasturefiremode == LIGHTNING_PASTURE_BURNING){
				patch.fuel.potential_human_ign =  0.0;
				patch.fuel.potential_lightning_ign = full_lightning_ignitions;
			}
			// prescribed not ready
			else if(pasturefiremode == PRESCRIBED_PASTURE_BURNING){
				dprintf("Prescribed pasture burning not implemented\n");
				abort();
			}
			// modelled not ready
			else if(pasturefiremode == MODELLED_PASTURE_BURNING){
				dprintf("Modelled pasture burning not implemented\n");
				abort();
			}

		}

		// If cropland
		else if(patch.stand.landcover == CROPLAND) {

			// full ignitions
			if(cropfiremode == FULL_CROPLAND_BURNING){
				patch.fuel.potential_human_ign = full_human_ignitions;
				patch.fuel.potential_lightning_ign = full_lightning_ignitions;
				dprintf("full burning\n");
			}
			// allow only lightning fires
			else if(cropfiremode == LIGHTNING_CROPLAND_BURNING){
				patch.fuel.potential_human_ign =  0.0;
				patch.fuel.potential_lightning_ign = full_lightning_ignitions;
				dprintf("lightning burning\n");
			}
			// prescribed not ready
			else if(cropfiremode == PRESCRIBED_CROPLAND_BURNING){
				dprintf("Prescribed crop burning not implemented\n");
				abort();
			}
			// modelled not ready
			else if(cropfiremode == MODELLED_CROPLAND_BURNING){
				dprintf("Modelled crop burning not implemented\n");
				abort();
			}

			// dprintf("Crop: lightning ign = %f, human ign = %f\n",patch.fuel.potential_lightning_ign, patch.fuel.potential_human_ign);

		}

		// no burning in other stand types (currently URBAN, BARE and PEATLANDS)
		else {

			return;

		}

		// AREA OF A FIRE
		patch.fuel.fire_size = fire_size(patch);


		// if selected, reduce fire size based on crop fraction
		if(crop_fraction_suppression_exponent < 0.0) {

			// first calculate total crop fraction by looping across stands
			double crop_fraction = 0.0;
			Gridcell::iterator gc_itr = patch.stand.get_gridcell().begin();
			while (gc_itr != patch.stand.get_gridcell().end()) {
				Stand& stand = *gc_itr;
				if(stand.is_true_crop_stand()) {
					crop_fraction += stand.get_gridcell_fraction();
				}
				++gc_itr;
			} 

			// reduce for size accordingly
			// TODO also include fraction of recently burnt land as a fragmenter?
			patch.fuel.fire_size = patch.fuel.fire_size * exp(crop_fraction_suppression_exponent * crop_fraction);

		}


		patch.fuel.monthly_fire_size[date.month] += patch.fuel.fire_size / 100; // output now in km^2
		// if(patch.fuel.fire_size > 100000) abort();

		// REALISED IGNITIONS AND THEREFORE NUMBER OF FIRES
		double realised_ignitions = 0;
		// Check that conditions are generally suitable so that ignitions can be realised, otherwise no fires
		double finefuel_kgDM = (patch.fuel.fuel_1hr_gDM + patch.fuel.fuel_livegrass_gDM) / 1000;
		if (finefuel_kgDM > fuelthreshold && patch.fuel.daily_fire_intensity > min_daily_intensity && patch.days_since_last_burn > min_days_between_burns) {
			realised_ignitions = patch.fuel.fdi * (patch.fuel.potential_lightning_ign + patch.fuel.potential_human_ign);
		}

		patch.fuel.daily_number_fires = realised_ignitions;

		// CALCULATED BURNT AREA
		double area_burnt_ha = min(realised_ignitions * patch.fuel.fire_size, area_ha); //in ha natural
		calculated_fire_fraction = area_burnt_ha / area_ha;


		// FireMIP SF2.2 PRE-INDUSTRIAL FIRE SENSITIVITY EXPERIMENT
		if (iffixedburntarea) {
			int chrono_year = date.year - nyear_spinup + 1901;
			if (chrono_year == 1680) {
				patch.fuel.mean_PI_BA[date.day] = 0;
			}
			if (chrono_year >= 1680 && chrono_year <= 1699) {
				patch.fuel.mean_PI_BA[date.day] += calculated_fire_fraction / 20;
			}
			if (chrono_year >= 1700) {
				calculated_fire_fraction = patch.fuel.mean_PI_BA[date.day];
			}
		}

		//  APPLY BURNING BY BURNING PATCH BASED ON PROBABILITY
		if (ifburnfullcell) {
			if (randfrac(patch.stand.seed) < calculated_fire_fraction) {
				burnPatch = true;
				applied_fire_fraction = 1.0;
				patch.days_since_last_burn = 0;
				//dprintf("Year = %i, Burning patch = %i, prob = %f, random number = %f\n", date.year,  patch.id, burn_prob, random_fraction);
			}
		} else {
			applied_fire_fraction = calculated_fire_fraction;
		}

	}

	//////////// PRESCRIBE FIRES - for prescribing number of fires but not burnt area
	else if (firemodel == PRESCR_NUMBER_FIRES) {
		// simply read it in
		// rate of spread
		// someFunction()
		// burnt area
		//double area_burnt_ha = min(climate.spitfire_io.nfires[date.day] * ((3.14159 / (4 * patch.fuel.length_to_breadth)) * (pow((patch.fuel.ros_f + patch.fuel.ros_b), 2))) / 10000, area_ha); //in ha natural
		// double area_burnt_ha = min(10 * ((3.14159 / (4 * patch.fuel.length_to_breadth)) * (pow((patch.fuel.ros_f + patch.fuel.ros_b), 2))) / 10000, area_ha); //in ha natural
	}

	//////////// PRESCRIBE BURNT AREA - for prescribing burnt area
	else if (firemodel == PRESCR_BURNT_AREA) {

		//The calculated_fire_fraction was allocated previously...
		calculated_fire_fraction = patch.fuel.fire_prob;

		// MF Standard way
		// Note key assumption:  Chance of a patch burning (completely) is proportional to the calculated burnt area fraction
		if (ifburnfullcell) {
			if (randfrac(patch.stand.seed) < calculated_fire_fraction && patch.fuel.possible) {
				burnPatch = true;
				applied_fire_fraction = 1.0;
				//dprintf("Year = %i, Burning patch = %i, prob = %f, random number = %f\n", date.year,  patch.id, burn_prob, random_fraction);
			}
		} else {
			applied_fire_fraction = calculated_fire_fraction;
		}

	}

	//////////// STATISTICAL MODE - Veiko's GLM
	else if (firemodel == STAT_BURNT_AREA) {
		// ------- need a call in here ------------
	}

	/////////// RANDOM FIRE RETURN MODE
	else if (firemodel == RANDOM_FIRE_RETURN && date.day == fixburnday - 1 && randfrac(patch.stand.seed) < 1 / firereturninterval) {
		calculated_fire_fraction = 1.0;
		applied_fire_fraction = 1.0;
		burnPatch = true;
	}

	/////////// FIXED FIRE RETURN MODE
	else if (firemodel == FIXED_FIRE_RETURN > 0 && date.day == fixburnday - 1 && date.year % int(firereturninterval) == 0) {
		calculated_fire_fraction = 1.0;
		applied_fire_fraction = 1.0;
		burnPatch = true;
	} else {
		calculated_fire_fraction = 0.0;
		applied_fire_fraction = 0.0;
		burnPatch = false;
	}

	// shortcude to turn off burning
	//calculated_fire_fraction = 0;
	//applied_fire_fraction = 0;

	/////////////////////////////////////////////////////////////////////////////////////
	//  CALCULATE FIRE FRACTIONS AND SEND THEM TO THE FRAMEWORK
	//  And update other daily sums

	patch.mfirefrac[date.month] += calculated_fire_fraction;
	patch.mfirefrac_applied[date.month] += applied_fire_fraction;

	// use main GUESS-SIMFIRE-BLAZE output
	double to_gridcell_average = patch.stand.get_gridcell_fraction() / (double)patch.stand.npatch();
	climate.gridcell.annual_burned_area += calculated_fire_fraction * to_gridcell_average;
	climate.gridcell.monthly_burned_area[date.month] += calculated_fire_fraction * to_gridcell_average;


	spitfire_daily_sums(patch, calculated_fire_fraction);



	// Add the fire fraction to the per PFT per month total
	patch.pft.firstobj();
	while (patch.pft.isobj) {
		Patchpft& pft = patch.pft.getobj();
		if(patch.fpc_total > 0){
			pft.monthly_ba_frac[date.month] += calculated_fire_fraction * pft.fpc;// / patch.fpc_total;
		}
		patch.pft.nextobj();
	}

	//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	// MF everything for here on in is enclosed by the if statement below.

	if (burnPatch || !ifburnfullcell) { // otherwise no consumption etc.

		//dprintf("Burning! Year = %i, day =%i, patch = %i\n", date.year, date.day, patch.id);
		//print_fire(patch);

		// increment output variables which summarise fire day properties
		tally_fire_properties(patch, climate.gridcell.nesterov_cur);

		// remove litter from standard LPJ-GUESS pools based on calculated consumption fractions per litter fuel class
		combust_litter(patch);


		///////////////////////////////////////////////////////////////////////////////////
		//////////////////////////////////////////////FIRE EFFECTS/////////////////////////                                        M_27
		// Here the effects of the fire on vegetation as well as the fluxes are calculated

		// TODO Report mortality somehow
		double nind_kill; // number of killed individuals, not currently counted
		bool killed;

		// This is the individual mortality and fire effect loop
		Vegetation& vegetation=patch.vegetation;
		vegetation.firstobj();
		while (vegetation.isobj) {

			Individual& indiv = vegetation.getobj();

			killed = false;
			nind_kill = 0.;

			// Trees can suffer combustion (through crown scorch) and mortality from crown scorch and cambial damage
			if (indiv.pft.lifeform == TREE) {

				// calculate fraction of crown scorched
				double crown_scorch_fraction = scorched_crown_fraction(patch.fuel.scorch_height, indiv.height, pftlist[indiv.pft.id].crown_l);

				// scorch trees by removing combusted live biomass (and report the flux to the atmosphere)
				if (!(indiv.densindiv == 0)) {
					combust_tree(patch, indiv, crown_scorch_fraction, applied_fire_fraction);
				}

				// probability of crown kill using scorch fraction calculated above  (Eqn. 22 Thonikce et al 2010)
				double crown_kill_prob = pftlist[indiv.pft.id].r_ck * pow(crown_scorch_fraction, pftlist[indiv.pft.id].p);

				// cambial kill probability
				double cambial_kill_prob = cambial_mortality_spitfire(patch.fuel.tau_l, indiv);

				// total post-fire mortality -(Eq 18 Thonicke et al. 2010)
				double postf_mort = cambial_kill_prob + crown_kill_prob - (cambial_kill_prob * crown_kill_prob);

				// do mortality
				killed = tree_mortality_spitfire(patch, indiv, postf_mort * applied_fire_fraction);

			} // End if tree

			//  Grass just suffer combustion of leaf biomass
			else {

				//simply reduce grass leaf biomass by the fraction consumed and report fluxes
				combust_grass(patch, indiv, patch.fuel.fraction_consumed_livegrass * applied_fire_fraction);

			}  // else grass

			// next individual (only if this individual not killed)
			if (!killed) vegetation.nextobj();

		} // End individual fire mortality and effects loop

	} // if ~(ifburnfullcell & fire_frac<0.9)


	//dprintf("Finishing SPITFIRE!\n");

	return;


} // void fire

