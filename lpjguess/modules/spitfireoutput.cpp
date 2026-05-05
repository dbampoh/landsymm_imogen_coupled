///////////////////////////////////////////////////////////////////////////////////////
/// \file outputmodule.cpp
/// \brief Implementation of the common output module
///
/// \author Joe Siltberg
/// $Date: 2016-12-16 16:21:33 +0100 (Fri, 16 Dec 2016) $
///
///////////////////////////////////////////////////////////////////////////////////////

#include "config.h"
#include "spitfireoutput.h"
#include "parameters.h"
#include "guess.h"

namespace GuessOutput {

REGISTER_OUTPUT_MODULE("SPITFIRE", SPITFIREOutput)

SPITFIREOutput::SPITFIREOutput() {

	// MF Fire season length and litter for re-fitting GlobFIRM
	declare_parameter("file_firesl", &file_firesl, 300, "Fire season length output file");
	declare_parameter("file_litter_wood", &file_litter_wood, 300, "wood litter for GLobFIRM studies");
	declare_parameter("file_litter_leaf", &file_litter_leaf, 300, "leaf litter for GLobFIRM studies");
	declare_parameter("file_litter_repr", &file_litter_repr, 300, "reproductive litter for GLobFIRM studies");

	// MF Mortality
	declare_parameter("file_monthly_nind_killed", &file_monthly_nind_killed, 300, "Total number of individuals killed per month by fire");
	declare_parameter("file_mtreecover_reduction_fire", &file_mtreecover_reduction_fire, 300, "Total tree cover reduction by fire per month");


	// New order for monthly variables, follows P. Anthoni's GCP code
	declare_parameter("file_monthly_burned_area_pft",&file_monthly_burned_area_pft,300, "Monthly burned area per pft output file (must have .out extension)");

	// *** FLUXES FROM FIRE ***

	// Annual per PFT C fire fluxes
	declare_parameter("file_cflux_fire", &file_cflux_fire, 300, "C flux from fire, per PFT (kgC/m2)");
	// Monthly C, CO, CO2 and CH4 fire fluxes
	declare_parameter("file_mfireflux_c", &file_mfireflux_c, 300, "monthly C flux from fire (kgC/m2)");
	declare_parameter("file_mfireflux_co", &file_mfireflux_co, 300, "monthly CO flux from fire (kgCO/m2))");
	declare_parameter("file_mfireflux_co2", &file_mfireflux_co2, 300, "monthly CO2 flux from fire (kgCO2/m2)");
	declare_parameter("file_mfireflux_ch4", &file_mfireflux_ch4, 300, "monthly CH4 flux from fire (kgCH4/m2)");
	// Monthly per PFT C flux
	declare_parameter("file_mfireflux_c_pft", &file_mfireflux_c_pft, 300, "monthly per-PFT C flux from fire (kgC/m2)");


	// MF DESPITE/SPITFIRE etc...
	//output
	declare_parameter("file_mfirefrac", &file_mfirefrac, 300, "monthly fire fraction output file used for fire effects");
	declare_parameter("file_mfirefrac_applied", &file_mfirefrac_applied, 300, "monthly fire fraction output file as calculated");
	declare_parameter("file_pyro_flux", &file_pyro_flux, 300, "annual pyrogenic flux output file");
	declare_parameter("file_mnfdi", &file_mnfdi, 300, "Average Monthly Nesterov Fire Danger Index output file");
	declare_parameter("file_mburn_prob", &file_mburn_prob, 300, "Average probability of burning (following Wilson 1985)");
	declare_parameter("file_mfireintens", &file_mfireintens, 300, "Average Monthly Fire Intensity");
	declare_parameter("file_afdays", &file_afdays, 300, "Annual fire season days (with Nesterov > 300 and > 1000) output file");
	declare_parameter("file_mavenest", &file_mavenest, 300, "Monthly average Nesterov index output file");
	declare_parameter("file_mRoS", &file_mRoS, 300, "Monthly average Rate of Spread");
	declare_parameter("file_mfiresize", &file_mfiresize, 300, "Monthly average fire size");
	declare_parameter("file_mhuman_ign", &file_mhuman_ign, 300, "Monthly average human ignitions per day");
	declare_parameter("file_mlightning_ign", &file_mlightning_ign, 300, "Monthly average human ignitions per day");
	declare_parameter("file_mhuman_pot_ign", &file_mhuman_pot_ign, 300, "Monthly average potential human ignitions per day");
	declare_parameter("file_mlightning_pot_ign", &file_mlightning_pot_ign, 300, "Monthly average potential human ignitions per day");

	declare_parameter("file_mlivegrass_fuel", &file_mlivegrass_fuel, 300, "Monthly average of livegrass fuel load");
	declare_parameter("file_m1hr_fuel", &file_m1hr_fuel, 300, "Monthly average of 1hr fuel load");
	declare_parameter("file_m10hr_fuel", &file_m10hr_fuel, 300, "Monthly average of 10hr fuel load");
	declare_parameter("file_m100hr_fuel", &file_m100hr_fuel, 300, "Monthly average of 100hr fuel load");
	declare_parameter("file_m1000hr_fuel", &file_m1000hr_fuel, 300, "Monthly average of 1000hr fuel load");

	declare_parameter("file_mlivegrass_fm", &file_mlivegrass_fm, 300, "Monthly average of livegrass fuel moisture");
	declare_parameter("file_m1hr_fm", &file_m1hr_fm, 300, "Monthly average of 1hr fuel moisture");
	declare_parameter("file_m10hr_fm", &file_m10hr_fm, 300, "Monthly average of 10hr fuel moisture");
	declare_parameter("file_m100hr_fm", &file_m100hr_fm, 300, "Monthly average of 100hr fuel moisture");
	declare_parameter("file_m1000hr_fm", &file_m1000hr_fm, 300, "Monthly average of 1000hr fuel  moisture");

	declare_parameter("file_mlivegrass_cc", &file_mlivegrass_cc, 300, "Monthly average combustion completeness of livegrass fuel");
	declare_parameter("file_m1hr_cc", &file_m1hr_cc, 300, "Monthly average combustion completeness of 1hr fuel");
	declare_parameter("file_m10hr_cc", &file_m10hr_cc, 300, "Monthly average combustion completeness of 10hr fuel");
	declare_parameter("file_m100hr_cc", &file_m100hr_cc, 300, "Monthly average combustion completeness of 100hr fuel");
	declare_parameter("file_m1000hr_cc", &file_m1000hr_cc, 300, "Monthly average combustion completeness of 1000hr fuel");

	declare_parameter("file_real_livegrass_cc", &file_real_livegrass_cc, 300, "Realised average combustion completeness of livegrass fuel");
	declare_parameter("file_real_1hr_cc", &file_real_1hr_cc, 300, "Realisedy average combustion completeness of 1hr fuel");
	declare_parameter("file_real_10hr_cc", &file_real_10hr_cc, 300, "Realisedy average combustion completeness of 10hr fuel");
	declare_parameter("file_real_100hr_cc", &file_real_100hr_cc, 300, "Realised average combustion completeness of 100hr fuel");
	declare_parameter("file_real_1000hr_cc", &file_real_1000hr_cc, 300, "Realised average combustion completeness of 1000hr fuel");


	declare_parameter("file_mFBD", &file_mFBD, 300, "Monthly average characteristic fuel bulk density");
	declare_parameter("file_mSAV", &file_mSAV, 300, "Monthly average characteristic fuel surface area to volume");
	declare_parameter("file_mMoE", &file_mMoE, 300, "Monthly average characteristic moisture of extinction");
	declare_parameter("file_mDFM", &file_mDFM, 300, "Monthly average characteristic daily fuel moisture");
	declare_parameter("file_meff_wind", &file_meff_wind, 300, "Monthly average effective windspeed");

	declare_parameter("file_mfire_durat", &file_mfire_durat, 300, "Monthly average of fire duration");
	declare_parameter("file_mtau_l", &file_mtau_l, 300, "Monthly average of fire residence time");
	declare_parameter("file_mscorch_height", &file_mscorch_height, 300, "Monthly average of scorch height");
	declare_parameter("file_allocation_fails", &file_allocation_fails, 300, "Number of days in a month that there were not enough suitable patches for fire allocation");
	declare_parameter("file_allocation_iters", &file_allocation_iters, 300, "Average number of iterations require to succesfully allocate fire in a month");

	declare_parameter("file_real_duration", &file_real_duration, 300, "Average durations of actual fires that month");
	declare_parameter("file_real_nesterov", &file_real_nesterov, 300, "Average nesterov during actual fires that month");
	declare_parameter("file_real_intensity", &file_real_intensity, 300, "Average intensity of actual fires that month");
	declare_parameter("file_real_residence_time", &file_real_residence_time, 300, "Average residence time of actual fires that month");
	declare_parameter("file_real_scorch_height", &file_real_scorch_height, 300, "Average scorch height of actual fires that month");
	declare_parameter("file_real_fire_size", &file_real_fire_size, 300, "Average size of actual fires that month");
	declare_parameter("file_real_num_fires", &file_real_num_fires, 300, "Realised number of fires that month");
	declare_parameter("file_real_fire_speed", &file_real_speed, 300, "Average macro speed of fires that month");
	declare_parameter("file_real_RoS", &file_real_RoS, 300, "Average rate of spread of fires that month");
	declare_parameter("file_real_DFM", &file_real_DFM, 300, "Average daily fuel moisture of fires that month");



	declare_parameter("file_potential_num_fires", &file_real_num_fires, 300, "Potential number of fires that month");

	//
	declare_parameter("file_mnbp", &file_mnbp, 300, "Monthly NBP output file (NEE and SPITFIRE fire flux)");



	// MF: Leaf shed output for checking performance of smooth raingreen phenology and and subannual turnover
	declare_parameter("file_mleafshed", &file_mleafshed, 300, "Monthly leaf shed (summed across all PFTs) as fraction of full leaf out status");
	declare_parameter("file_aleafshed", &file_aleafshed, 300, "Annual leaf shed for this PFT as fraction of full leaf out status");

	// MF: Fine fuel for checking litter/fuel dynamics
	declare_parameter("file_mfinefuel", &file_mfinefuel, 300, "Monthly fine fuel output file");




	// Daily output
	declare_parameter("first_year_daily_output", &first_year_daily_output, 0, 10000, "Year to start the daily output");
	declare_parameter("last_year_daily_output", &last_year_daily_output, 0, 10000, "Year to finish the daily output");
	declare_parameter("file_daily_fires", &file_daily_fires, 300, "Daily fire properties (averaged across active fires)");
	declare_parameter("file_daily_fires_diagnostics", &file_daily_fires_diagnostics, 300, "Daily fire properties (all calculated values weighted across flammable patches irrespective of number of fires burning)");
	declare_parameter("file_daily_fuel_moisture", &file_daily_fuel_moisture, 300, "Daily fuel moistures (averaged across active fires)");
	declare_parameter("file_daily_fuel_moisture_diagnostics", &file_daily_fuel_moisture_diagnostics, 300, "Daily fuel moistures (all calculated values weighted across flammable patches irrespective of number of fires burning)");
	declare_parameter("file_daily_flammability", &file_daily_flammability, 300, "Daily flammability (Nesterov FDI and Wilson's Burn Probability, averaged across active fires)");
	declare_parameter("file_daily_flammability_diagnostics", &file_daily_flammability_diagnostics, 300, "Daily flammability (Nesterov FDI and Wilson's Burn Probability, all calculated values weighted across flammable patches irrespective of number of fires burning)");


	// Annual outputs
	declare_parameter("file_annual_fuel_loads", &file_annual_fuel_loads, 300, "Mean annual fuel loads for the different fuel classes (weighted across flammable patches)");


}


SPITFIREOutput::~SPITFIREOutput() {
}

/// Define all output tables and their formats
void SPITFIREOutput::init() {

	define_output_tables();

}

/** This function specifies all columns in all output tables, their names,
 *  column widths and precision.
 *
 *  For each table a TableDescriptor object is created which is then sent to
 *  the output channel to create the table.
 */
void SPITFIREOutput::define_output_tables() {

	//Extra number of decimals when output for benchmarks
#ifdef RUN_BENCHMARKS	
	const int bm_extra_prec = 2;
#else
	const int bm_extra_prec =0;
#endif

	// create a vector with the pft names
	std::vector<std::string> pfts;

	// create a vector with the crop pft names
	std::vector<std::string> crop_pfts;

	pftlist.firstobj();
	while (pftlist.isobj) {
		Pft& pft=pftlist.getobj();

		pfts.push_back((char*)pft.name);

		if(pft.landcover==CROPLAND)
			crop_pfts.push_back((char*)pft.name);

		pftlist.nextobj();
	}
	ColumnDescriptors mpft_columns_8_3;
	mpft_columns_8_3 += ColumnDescriptors(pfts, 8, 3);

	// create a vector with the landcover column titles
	std::vector<std::string> landcovers;

	if (run_landcover) {
		const char* landcover_string[]={"Urban_sum", "Crop_sum", "Pasture_sum",
				"Forest_sum", "Natural_sum", "Peatland_sum", "Barren_sum"};
		for (int i=0; i<NLANDCOVERTYPES; i++) {
			if(run[i]) {
				landcovers.push_back(landcover_string[i]);
			}
		}
	}

	// Create the month columns
	ColumnDescriptors month_columns;
	ColumnDescriptors month_columns_fractions;
	ColumnDescriptors month_columns_wide;
	ColumnDescriptors month_columns_large;
	ColumnDescriptors month_columns_Nesterov;
	ColumnDescriptors ba_frac_month_columns;
	ColumnDescriptors month_flux_columns;
	xtring months[] = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};
	for (int i = 0; i < 12; i++) {
		month_columns      += ColumnDescriptor(months[i], 8,  3);
		month_columns_fractions  += ColumnDescriptor(months[i], 6,  3);
		month_columns_wide += ColumnDescriptor(months[i], 10, 3);
		ba_frac_month_columns += ColumnDescriptor(months[i], 8, 5); // 8,5
		month_flux_columns += ColumnDescriptor(months[i], 8, 5); // 10, 5
		month_columns_large += ColumnDescriptor(months[i], 10, 2);
	}


	// Create the columns for each output file
	// DESPITE Pyrogenic trace gases

	ColumnDescriptors pyro_flux_columns;
	pyro_flux_columns += ColumnDescriptor("C", 13, 3);
	pyro_flux_columns += ColumnDescriptor("CO2", 13, 5);
	pyro_flux_columns += ColumnDescriptor("CO", 13, 5);
	pyro_flux_columns += ColumnDescriptor("CH4", 13, 5);
	pyro_flux_columns += ColumnDescriptor("VOC", 13, 5);
	pyro_flux_columns += ColumnDescriptor("TPM", 13, 5);
	pyro_flux_columns += ColumnDescriptor("NOx", 13, 5);
	pyro_flux_columns += ColumnDescriptor("CO2s", 13, 3);
	pyro_flux_columns += ColumnDescriptor("COs", 13, 5);
	pyro_flux_columns += ColumnDescriptor("CH4s", 13, 5);

	// SPITFIRE
	ColumnDescriptors afdays_columns;
	afdays_columns += ColumnDescriptor("Nest.gt.300", 15, 0);
	afdays_columns += ColumnDescriptor("Nest.gt.1000", 15, 0);

	// SPITFIRE
	ColumnDescriptors allocation_diagnostics_columns;
	allocation_diagnostics_columns += ColumnDescriptor("Fails", 5, 0);
	allocation_diagnostics_columns += ColumnDescriptor("Mean_iters", 11, 5);

	// CFLUX-FIRE
	ColumnDescriptors cflux_fire_columns;
	cflux_fire_columns += ColumnDescriptors(pfts, 8, 5);

	// BA FRACTION (MONTHLY)
	ColumnDescriptors ba_frac_columns;
	ba_frac_columns = cflux_fire_columns;


	// Create the columns for each output file

	// MF ANNUAL LEAF SHED
	ColumnDescriptors aleafshed_columns;
	aleafshed_columns += ColumnDescriptors(pfts,      8, 2);

	// MF-FireMIP
	ColumnDescriptors month_pft_columns;
	month_pft_columns += ColumnDescriptors(pfts, 9, 5);

	// FIRE SEASON LENGTH - MF-FIRESL
	ColumnDescriptors firesl_columns;
	firesl_columns += ColumnDescriptor("FireSL", 8, 1);

	// LITTER
	ColumnDescriptors litter_columns;
	litter_columns += ColumnDescriptors(pfts, 8, 4);
	litter_columns += ColumnDescriptor("Total", 8, 4);

	// DAILY FIRE PROPS
	ColumnDescriptors daily_fire_columns;
	daily_fire_columns += ColumnDescriptor("Number",   7, 3);
	daily_fire_columns += ColumnDescriptor("Size",   10, 2);
	daily_fire_columns += ColumnDescriptor("Intens",   8, 1);
	daily_fire_columns += ColumnDescriptor("Durat",   7, 1);
	daily_fire_columns += ColumnDescriptor("Speed",   8, 4);
	daily_fire_columns += ColumnDescriptor("RoS",   7, 3);


	// DAILY FUEL MOISTURE
	ColumnDescriptors daily_fm_columns;
	daily_fm_columns += ColumnDescriptor("Grass",   6, 3);
	daily_fm_columns += ColumnDescriptor("1hr",   6, 3);
	daily_fm_columns += ColumnDescriptor("10hr",   6, 3);
	daily_fm_columns += ColumnDescriptor("100hr",   6, 3);
	daily_fm_columns += ColumnDescriptor("Char",   6, 3);

	// DAILY FLAMMABILITY
	ColumnDescriptors daily_flam_columns;
	daily_flam_columns += ColumnDescriptor("NFDI",   5, 3);
	daily_flam_columns += ColumnDescriptor("WBP",   5, 3);

	// ANNUAL FUEL LOAD
	ColumnDescriptors annual_fuel_columns;
	annual_fuel_columns += ColumnDescriptor("Grass",   7, 3);
	annual_fuel_columns += ColumnDescriptor("1hr",   7, 3);
	annual_fuel_columns += ColumnDescriptor("10hr",   7, 3);
	annual_fuel_columns += ColumnDescriptor("100hr",   7, 3);
	annual_fuel_columns += ColumnDescriptor("1000hr",   7, 3);



	create_output_table(out_firesl, file_firesl, firesl_columns); // MF
	create_output_table(out_litter_leaf, file_litter_leaf, litter_columns); // MF-LITTER
	create_output_table(out_litter_wood, file_litter_wood, litter_columns); // MF-LITTER
	create_output_table(out_litter_repr, file_litter_repr, litter_columns); // MF-LITTER

	// *** MONTHLY OUTPUT VARIABLES ***



	// MF: Leaf shed and fine fuel
	create_output_table(out_mleafshed, 		file_mleafshed, 	month_columns);
	create_output_table(out_aleafshed, 		file_aleafshed, 	aleafshed_columns);
	create_output_table(out_mfinefuel,      file_mfinefuel,     month_columns);



	// *** ANNUAL OUTPUT VARIABLES ***

	create_output_table(out_pyro_flux, file_pyro_flux, pyro_flux_columns); // DESPITE
	create_output_table(out_afdays, file_afdays, afdays_columns); // SPITFIRE

	// *** MONTHLY OUTPUT VARIABLES ***
	create_output_table(out_mnbp, file_mnbp, month_columns);

	create_output_table(out_mfirefrac, file_mfirefrac, ba_frac_month_columns); // DESPITE
	create_output_table(out_mfirefrac_applied, file_mfirefrac_applied, ba_frac_month_columns); // DESPITE
	create_output_table(out_mnfdi, file_mnfdi, month_columns); // SPITFIRE
	create_output_table(out_mburn_prob, file_mburn_prob, month_columns); // SPITFIRE
	create_output_table(out_mfireintens, file_mfireintens, month_columns_large); // SPITFIRE
	create_output_table(out_mavenest, file_mavenest, month_columns_large); // SPITFIRE
	create_output_table(out_mRoS, file_mRoS, month_columns); // SPITFIRE

	create_output_table(out_mfiresize, file_mfiresize, month_columns_large); // SPITFIRE
	create_output_table(out_mhuman_ign, file_mhuman_ign, month_columns); // SPITFIRE
	create_output_table(out_mlightning_ign, file_mlightning_ign, month_columns); // SPITFIRE
	create_output_table(out_mhuman_pot_ign, file_mhuman_pot_ign, month_columns); // SPITFIRE
	create_output_table(out_mlightning_pot_ign, file_mlightning_pot_ign, month_columns); // SPITFIRE


	create_output_table(out_mlivegrass_fuel, file_mlivegrass_fuel, month_columns_wide); // SPITFIRE
	create_output_table(out_m1hr_fuel, file_m1hr_fuel, month_columns_wide); // SPITFIRE
	create_output_table(out_m10hr_fuel, file_m10hr_fuel, month_columns_wide); // SPITFIRE
	create_output_table(out_m100hr_fuel, file_m100hr_fuel, month_columns_wide); // SPITFIRE
	create_output_table(out_m1000hr_fuel, file_m1000hr_fuel, month_columns_wide); // SPITFIRE

	create_output_table(out_mlivegrass_fm, file_mlivegrass_fm, month_columns_fractions); // SPITFIRE
	create_output_table(out_m1hr_fm, file_m1hr_fm, month_columns_fractions); // SPITFIRE
	create_output_table(out_m10hr_fm, file_m10hr_fm, month_columns_fractions); // SPITFIRE
	create_output_table(out_m100hr_fm, file_m100hr_fm, month_columns_fractions); // SPITFIRE
	create_output_table(out_m1000hr_fm, file_m1000hr_fm, month_columns_fractions); // SPITFIRE

	create_output_table(out_mlivegrass_cc, file_mlivegrass_cc, month_columns_fractions); // SPITFIRE
	create_output_table(out_m1hr_cc, file_m1hr_cc, month_columns_fractions); // SPITFIRE
	create_output_table(out_m10hr_cc, file_m10hr_cc, month_columns_fractions); // SPITFIRE
	create_output_table(out_m100hr_cc, file_m100hr_cc, month_columns_fractions); // SPITFIRE
	create_output_table(out_m1000hr_cc, file_m1000hr_cc, month_columns_fractions); // SPITFIRE

	create_output_table(out_real_livegrass_cc, file_real_livegrass_cc, month_columns_fractions); // SPITFIRE
	create_output_table(out_real_1hr_cc, file_real_1hr_cc, month_columns_fractions); // SPITFIRE
	create_output_table(out_real_10hr_cc, file_real_10hr_cc, month_columns_fractions); // SPITFIRE
	create_output_table(out_real_100hr_cc, file_real_100hr_cc, month_columns_fractions); // SPITFIRE
	create_output_table(out_real_1000hr_cc, file_real_1000hr_cc, month_columns_fractions); // SPITFIRE

	create_output_table(out_mtau_l, file_mtau_l, month_columns); // SPITFIRE
	create_output_table(out_mscorch_height, file_mscorch_height, month_columns); // SPITFIRE
	create_output_table(out_mfire_durat, file_mfire_durat, month_columns); // SPITFIRE
	create_output_table(out_allocation_fails, file_allocation_fails, month_columns); // SPITFIRE
	create_output_table(out_allocation_iters, file_allocation_iters, month_columns); // SPITFIRE


	create_output_table(out_real_duration, file_real_duration, month_columns_wide); // SPITFIRE
	create_output_table(out_real_scorch_height, file_real_scorch_height, month_columns); // SPITFIRE
	create_output_table(out_real_residence_time, file_real_residence_time, month_columns); // SPITFIRE
	create_output_table(out_real_intensity, file_real_intensity, month_columns_large); // SPITFIRE
	create_output_table(out_real_nesterov, file_real_nesterov, month_columns_large); // SPITFIRE
	create_output_table(out_real_fire_size, file_real_fire_size, month_columns_large); // SPITFIRE
	create_output_table(out_real_num_fires, file_real_num_fires, month_columns); // SPITFIRE
	create_output_table(out_real_speed, file_real_speed, month_columns); // SPITFIRE
	create_output_table(out_real_DFM, file_real_DFM, month_columns); // SPITFIRE
	create_output_table(out_real_RoS, file_real_RoS, month_columns); // SPITFIRE



	create_output_table(out_mSAV, file_mSAV, month_columns_wide); // SPITFIRE
	create_output_table(out_mFBD, file_mFBD, month_columns_wide); // SPITFIRE
	create_output_table(out_mMoE, file_mMoE, month_columns_wide); // SPITFIRE
	create_output_table(out_mDFM, file_mDFM, month_columns_fractions); // SPITFIRE
	create_output_table(out_meff_wind, file_meff_wind, month_columns_wide); // SPITFIRE

	create_output_table(out_cflux_fire, file_cflux_fire, cflux_fire_columns); // SPITFIRE


	create_output_table(out_mfireflux_c, file_mfireflux_c, month_flux_columns); // SPITFIRE
	create_output_table(out_mfireflux_co, file_mfireflux_co, month_flux_columns); // SPITFIRE
	create_output_table(out_mfireflux_co2, file_mfireflux_co2, month_flux_columns); // SPITFIRE
	create_output_table(out_mfireflux_ch4, file_mfireflux_ch4, month_flux_columns); // SPITFIRE


	create_output_table(out_monthly_nind_killed, file_monthly_nind_killed, month_columns); // SPITFIRE
	create_output_table(out_mtreecover_reduction_fire, file_mtreecover_reduction_fire, month_columns_fractions); // SPITFIRE


	// *** DAILY OUTPUT TABLES ***
	create_output_table(out_daily_fires, file_daily_fires, daily_fire_columns); // SPITFIRE
	create_output_table(out_daily_fires_diagnostics, file_daily_fires_diagnostics, daily_fire_columns); // SPITFIRE
	create_output_table(out_daily_fuel_moisture, file_daily_fuel_moisture, daily_fm_columns); // SPITFIRE
	create_output_table(out_daily_fuel_moisture_diagnostics, file_daily_fuel_moisture_diagnostics, daily_fm_columns); // SPITFIRE
	create_output_table(out_daily_flammability, file_daily_flammability, daily_flam_columns); // SPITFIRE
	create_output_table(out_daily_flammability_diagnostics, file_daily_flammability_diagnostics, daily_flam_columns); // SPITFIRE

	create_output_table(out_annual_fuel_loads, file_annual_fuel_loads, annual_fuel_columns ); // SPITFIRE

	// *** MONTHLY PER PFT OUTPUT VARIABLES ***
	// insert the PFT name (e.g. "TeNE") into before the .out
	long position;
	pftlist.firstobj();
	while (pftlist.isobj) {
		Pft& pft=pftlist.getobj();
		if (file_monthly_burned_area_pft != "") {
			position = file_monthly_burned_area_pft.find(".out");
			create_output_table(out_monthly_burned_area_pft[pft.id], file_monthly_burned_area_pft.left(position) + xtring("_") + xtring(pft.name) + ".out", ba_frac_month_columns);
			position = file_mfireflux_c_pft.find(".out");
			create_output_table(out_mfireflux_c_pft[pft.id], file_mfireflux_c_pft.left(position) + xtring("_") + xtring(pft.name) + ".out", ba_frac_month_columns);
		}
		pftlist.nextobj();

	}

	// also make an output file for per-PFT burnt area in "BareSoil"
	if(firemodel == SPITFIRE) {
		if (file_monthly_burned_area_pft != "") {
			position = file_monthly_burned_area_pft.find(".out");
			create_output_table(out_monthly_burned_area_pft[npftconst], file_monthly_burned_area_pft.left(position) + xtring("_") + "BareSoil" + ".out", ba_frac_month_columns);
		}
	}


}



/// Local analogue of OutputRows::add_value for restricting output
/** Use to restrict output to specified range of years
 * (or other user-specified limitation)
 *
 * If only yearly output between, say 1961 and 1990 is requred, use:
 *  if (date.get_calendar_year() >= 1961 && date.get_calendar_year() <= 1990)
 *  (assuming the input module has set the first calendar year in the date object)
 */
void outlimit_spitfire(OutputRows& out, const Table& table, double d) {

	if (date.year>=nyear_spinup)
		out.add_value(table, d);

}


/// Local analogue of OutputRows::add_value for restricting output
/** Use to restrict output to specified range of years
 * (or other user-specified limitation)
 *
 * If only yearly output between, say 1961 and 1990 is requred, use:
 *  if (date.get_calendar_year() >= 1961 && date.get_calendar_year() <= 1990)
 *  (assuming the input module has set the first calendar year in the date object)
 */
void SPITFIREOutput::outlimit_daily_spitfire(OutputRows& out, const Table& table, double d) {

	if (date.get_calendar_year() >= first_year_daily_output && date.get_calendar_year() <= last_year_daily_output)
		out.add_value(table, d);

}

/// Output of simulation results at the end of each year
/** Output of simulation results at the end of each year, or for specific years in
 * the simulation of each stand or grid cell.
 * This function does not have to provide any information to the framework.
 *
 * Restrict output to specific years in the local helper function outlimit().
 *
 * Changes in the structure of this function should be mirrored in outannual()
 * of the other output modules, e.g. MiscOutput::outannual().
 */
void SPITFIREOutput::outannual(Gridcell& gridcell) {

	int c, m;

	// MF: Intermediate valeus for
	// DESPITE
	double mfirefrac[12];
	double mfirefrac_applied[12];
	// SPITFIRE
	double mnfdi[12];
	double mburn_prob[12];
	double mfireintens[12];
	double mavenest[12];
	double mRoS[12];

	double mlivegrass_fuel[12];
	double m1hr_fuel[12];
	double m10hr_fuel[12];
	double m100hr_fuel[12];
	double m1000hr_fuel[12];

	double mlivegrass_fm[12];
	double m1hr_fm[12];
	double m10hr_fm[12];
	double m100hr_fm[12];
	double m1000hr_fm[12];

	double mlivegrass_cc[12];
	double m1hr_cc[12];
	double m10hr_cc[12];
	double m100hr_cc[12];
	double m1000hr_cc[12];

	double real_livegrass_cc[12];
	double real_1hr_cc[12];
	double real_10hr_cc[12];
	double real_100hr_cc[12];
	double real_1000hr_cc[12];

	double mtau_l[12];
	double mfire_durat[12];
	double mscorch_height[12];

	double mfiresize[12];
	double mhuman_ign[12];
	double mlightning_ign[12];
	double mhuman_pot_ign[12];
	double mlightning_pot_ign[12];

	double mFBD[12];
	double mSAV[12];
	double mMoE[12];
	double mDFM[12];
	double mdlm_deadfuel[12];
	double meff_wind[12];

	// Monthly fire fluxes
	double mfireflux_c[12];
	double mfireflux_co[12];
	double mfireflux_co2[12];
	double mfireflux_ch4[12];

	double mind_killed[12];
	double mtreecover_reduction_fire[12];


	double real_duration[12];
	double real_scorch_height[12];
	double real_residence_time[12];
	double real_intensity[12];
	double real_nesterov[12];
	double real_num_fires[12];
	double real_fire_size[12];
	double real_speed[12];
	double real_RoS[12];
	double real_DFM[12];


	int nestgt300 = 0;
	int nestgt1000 = 0;

	/* Per PFT fire variables */
	// no longer gcpft, now called mean_standpft
	double mean_standpft_cflux_fire =0;
	double mean_standpft_ba_frac =0;

	double mean_standpft_monthly_cflux_fire[12];

	double mean_standpft_litter_leaf = 0.0; // MF-LITTER
	double mean_standpft_litter_wood = 0.0; // MF-LITTER
	double mean_standpft_litter_repr = 0.0; // MF-LITTER



	// Per monthly, per pft
	double standpft_cflux_fire =0;
	double standpft_ba_frac =0;

	double standpft_monthly_cflux_fire[12];

	double standpft_litter_leaf = 0.0; // MF-LITTER
	double standpft_litter_wood = 0.0; // MF-LITTER
	double standpft_litter_repr = 0.0; // MF-LITTER


	// per PFT output (cf GCP)
	double standpft_monthly_burned_area_pft[npftconst][12]={{0.0}};
	double standpft_mfireflux_c_pft[npftconst][12]={{0.0}};


	double gcpft_monthly_burned_area_pft[npftconst][12]={{0.0}};
	double gcpft_mfireflux_c_pft[npftconst][12]={{0.0}};



	// not sure about this but it is used
	double mfire_cflux[12];



	// MF: Phenology check and fine fuel
	double mleafshed[12];
	double mfinefuel[12];


	double lon = gridcell.get_lon();
	double lat = gridcell.get_lat();

	// The OutputRows object manages the next row of output for each
	// output table
	OutputRows out(output_channel, lon, lat, date.get_calendar_year());

	// guess2008 - reset monthly average across patches each year
	for (m = 0; m < 12; m++) {
		mfirefrac[m] = mfirefrac_applied[m] = mnfdi[m] = mburn_prob[m] = mfireintens[m] = mavenest[m] = mRoS[m]  = 0.0;
		m1hr_fuel[m] = m10hr_fuel[m] = m100hr_fuel[m] = m1000hr_fuel[m] = mlivegrass_fuel[m] = 0.0;
		m1hr_fm[m] = m10hr_fm[m] = m100hr_fm[m] = m1000hr_fm[m] = mlivegrass_fm[m] = 0.0;
		m1hr_cc[m] = m10hr_cc[m] = m100hr_cc[m] = m1000hr_cc[m] = mlivegrass_cc[m] = 0.0;
		real_1hr_cc[m] = real_10hr_cc[m] = real_100hr_cc[m] = real_1000hr_cc[m] = real_livegrass_cc[m]= 0.0;
		mtau_l[m] = mscorch_height[m] = mfire_durat[m] = 0.0;
		real_duration[m] = real_scorch_height[m] = real_residence_time[m] = real_intensity[m] = real_nesterov[m] = real_num_fires[m] = real_fire_size[m] =0;
		real_speed[m] = real_RoS[m] = real_speed[m] = 0;
		mSAV[m] = mMoE[m] = mFBD[m] = mDFM[m] = mdlm_deadfuel[m] = meff_wind[m] = 0;
		mfiresize[m] = mhuman_ign[m] = mlightning_ign[m] = mhuman_pot_ign[m] = mlightning_pot_ign[m] = 0;
		mfireflux_ch4[m] = mfireflux_co2[m] = mfireflux_co[m] = mfireflux_c[m] =0;
		mind_killed[m] = mtreecover_reduction_fire[m] = 0;
	}


	// pyrogenic fluxes
	double pyro_flux_C = 0.0;
	double pyro_flux_CO = 0.0;
	double pyro_flux_CO2 = 0.0;
	double pyro_flux_CH4 = 0.0;
	double pyro_flux_VOC = 0.0;
	double pyro_flux_NOx = 0.0;
	double pyro_flux_TPM = 0.0;
	double pyro_flux_CO2s = 0.0;
	double pyro_flux_COs = 0.0;
	double pyro_flux_CH4s = 0.0;



	double landcover_litter_leaf[NLANDCOVERTYPES]={0.0};
	double landcover_litter_wood[NLANDCOVERTYPES]={0.0};
	double landcover_litter_repr[NLANDCOVERTYPES]={0.0};

	double landcover_cmass[NLANDCOVERTYPES]={0.0};


	double mean_standpft_cmass=0.0;

	// MF: Phenology checks
	double mean_standpft_aleafshed=0.0;


	double litter_leaf_gridcell = 0.0; // MF-LITTER
	double litter_wood_gridcell = 0.0; // MF-LITTER
	double litter_repr_gridcell = 0.0; // MF-LITTER




	// MF phenology checks
	double aleafshed_gridcell = 0.0;


	// annual fuel load values
	double annual_grass_fuel = 0.0;
	double annual_1hr_fuel = 0.0;
	double annual_10hr_fuel = 0.0;
	double annual_100hr_fuel = 0.0;
	double annual_1000hr_fuel = 0.0;



	// MF: phenology checks
	double standpft_aleafshed=0.0;

	// *** Loop through PFTs ***

	pftlist.firstobj();
	while (pftlist.isobj) {

		Pft& pft=pftlist.getobj();
		Gridcellpft& gridcellpft=gridcell.pft[pft.id];

		// Sum per-PFT output such as monthly C fluxes, litter, instances of leaf shedding across patches

		// MF: Phenology checks
		mean_standpft_aleafshed = 0.0;

		mean_standpft_litter_leaf = 0.0; // MF-LITTER
		mean_standpft_litter_wood = 0.0; // MF-LITTER
		mean_standpft_litter_repr = 0.0; // MF-LITTER

		mean_standpft_cflux_fire = 0;

		double heightindiv_total = 0.0;

		// Determine area fraction of stands where this pft is active:
		double active_fraction = 0.0;

		Gridcell::iterator gc_itr = gridcell.begin();

		while (gc_itr != gridcell.end()) {
			Stand& stand = *gc_itr;

			if(stand.pft[pft.id].active) {
				active_fraction += stand.get_gridcell_fraction();
			}

			++gc_itr;
		}

		// Loop through Stands
		gc_itr = gridcell.begin();

		while (gc_itr != gridcell.end()) {
			Stand& stand = *gc_itr;

			Standpft& standpft=stand.pft[pft.id];

//			if (!standpft.active) {
//				++gc_itr;
//				continue;
//			}

			// MF: Phenology checks
			standpft_aleafshed =0.0;
			standpft_litter_leaf = 0.0; // MF-LITTER
			standpft_litter_wood = 0.0; // MF-LITTER
			standpft_litter_repr = 0.0; // MF-LITTER
			for (m=0;m<12;m++) {
				standpft_monthly_burned_area_pft[pft.id][m]=0.0;
				standpft_mfireflux_c_pft[pft.id][m]=0.0;
			}

			stand.firstobj();

			// Loop through Patches
			while (stand.isobj) {
				Patch& patch = stand.getobj();
				Patchpft& patchpft = patch.pft[pft.id];
				Vegetation& vegetation = patch.vegetation;


				// MF-LITTER already stored per PFTs, so sum across patchs
				standpft_litter_leaf += patchpft.cmass_litter_leaf; // MF-LITTER
				standpft_litter_wood += patchpft.cmass_litter_sap + patchpft.cmass_litter_heart; //MF-LITTER
				standpft_litter_repr += patchpft.cmass_litter_repr; // MF-LITTER

				double to_gridcell_average = stand.get_gridcell_fraction() / (double) stand.nobj;
				standpft_cflux_fire += patch.pft[pft.id].annual_fuel_consumed_gC * to_gridcell_average;

				for (m=0;m<12;m++) {
					standpft_monthly_burned_area_pft[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::BA, pft.id, m);
					standpft_mfireflux_c_pft[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::C_FIRE, pft.id, m);

					if(patch.fluxes.get_monthly_flux(Fluxes::C_FIRE, pft.id, m) > 0.00001) {
						//dprintf("pft.id = %i, patch.pft[pft.id].id = %i, stand.pft[pft.id] =%i\n", pft.id, patch.pft[pft.id].id, patch.pft[pft.id].id,stand.pft[pft.id].id);
						//dprintf("Year = %i, month = %i, Retrieving PFT =%i flux = %.20f\n", date.get_calendar_year(), m, pft.id, patch.fluxes.get_monthly_flux(Fluxes::C_FIRE, pft.id, m));
					}
				}

				stand.nextobj();
			} // end of patch loop


			for (m=0;m<12;m++) {
				//standpft_monthly_burned_area_pft[pft.id][m] /=(double)stand.npatch();
				//standpft_mfireflux_c_pft[pft.id][m] /=(double)stand.npatch();

				if(standpft_mfireflux_c_pft[pft.id][m] > 0.00001) {
						//dprintf("Year = %i, month = %i, Intermediate 1 STAND PFT =%i flux = %.20f\n", date.get_calendar_year(), m, pft.id, standpft_mfireflux_c_pft[pft.id][m]);
						//dprintf("Year = %i, month = %i, Intermediate 1 GRIDCELL PFT =%i flux = %.20f\n", date.get_calendar_year(), m, pft.id, gcpft_mfireflux_c_pft[pft.id][m]);
				}

			}



			double to_gridcell_average = stand.get_gridcell_fraction() / (double)stand.npatch();

			// calculate the stands monthly means for the PFT w/ pft.id (c.f. GCP)
			for (m=0;m<12;m++) {
				gcpft_monthly_burned_area_pft[pft.id][m]+=standpft_monthly_burned_area_pft[pft.id][m]*to_gridcell_average;
				gcpft_mfireflux_c_pft[pft.id][m]+=standpft_mfireflux_c_pft[pft.id][m]*to_gridcell_average;


				if(gcpft_mfireflux_c_pft[pft.id][m] > 0.00001) {
					//printf("Year = %i, month = %i, Intermediate 2 STAND PFT =%i flux = %.20f\n", date.get_calendar_year(), m, pft.id, standpft_mfireflux_c_pft[pft.id][m]);
					//dprintf("Year = %i, month = %i, Intermediate 2 GRIDCELL PFT =%i flux = %.20f\n", date.get_calendar_year(), m, pft.id, gcpft_mfireflux_c_pft[pft.id][m]);
				}
			}


			// MF: Phenology checks
			standpft_aleafshed/=(double)stand.npatch();

			standpft_litter_leaf /=(double)stand.npatch(); // MF-LITTER
			standpft_litter_wood /= (double)stand.npatch(); //MF-LITTER
			standpft_litter_repr /=(double)stand.npatch(); //MF-LITTER



			//Update landcover totals
			//landcover_cmass[stand.landcover]+=standpft_cmass*stand.get_landcover_fraction();

			landcover_litter_leaf[stand.landcover]+=standpft_litter_leaf*stand.get_landcover_fraction();
			landcover_litter_repr[stand.landcover]+=standpft_litter_repr*stand.get_landcover_fraction();
			landcover_litter_wood[stand.landcover]+=standpft_litter_wood*stand.get_landcover_fraction();


			//Update pft means for active stands
			//mean_standpft_cmass += standpft_cmass * stand.get_gridcell_fraction() / active_fraction;

			// MF: Phenology checks
			mean_standpft_aleafshed += standpft_aleafshed * stand.get_gridcell_fraction() / active_fraction;

			mean_standpft_litter_leaf += standpft_litter_leaf; // MF-LITTER
			mean_standpft_litter_wood += standpft_litter_wood; //MF-LITTER
			mean_standpft_litter_repr += standpft_litter_repr; // MF-LITTER

			// Update gridcell totals
			double fraction_of_gridcell = stand.get_gridcell_fraction();

			litter_leaf_gridcell += standpft_litter_leaf * fraction_of_gridcell; // MF-LITTER
			litter_wood_gridcell += standpft_litter_wood * fraction_of_gridcell; //MF-LITTER
			litter_repr_gridcell += standpft_litter_repr * fraction_of_gridcell; // MF-LITTER


			if(standpft_mfireflux_c_pft[pft.id][m] > 0.00001) {
				//dprintf("Year = %i, day = %i, Intermediate 3 STAND PFT =%i flux = %.20f\n", date.get_calendar_year(), date.day, pft.id, standpft_mfireflux_c_pft[pft.id][m]);
				//dprintf("Year = %i, day = %i, Intermediate 3 GRIDCELL PFT =%i flux = %.20f\n", date.get_calendar_year(), date.day, pft.id, gcpft_mfireflux_c_pft[pft.id][m]);
			}

			++gc_itr;

		} //End of loop through stands

		// Print PFT sums to files
		//outlimit(out,out_cmass,     mean_standpft_cmass);


		outlimit_spitfire(out, out_litter_wood, mean_standpft_litter_wood); // MF-LITTER
		outlimit_spitfire(out, out_litter_leaf, mean_standpft_litter_leaf); // MF-LITTER
		outlimit_spitfire(out, out_litter_repr, mean_standpft_litter_repr); // MF-LITTER

		outlimit_spitfire(out,out_cflux_fire, mean_standpft_cflux_fire / 1000); // divide by 1000 to get output in kg C




		// MF: Phenology checks
		outlimit_spitfire(out,out_aleafshed, mean_standpft_aleafshed);

		// monthly, per-PFT output (following GCP output)
		// Print monthly output variables
		for (m=0;m<12;m++) {

			if(gcpft_mfireflux_c_pft[pft.id][m] > 0.00001) {
					//dprintf("Year = %i, month = %i, Writing PFT =%i flux = %.20f\n", date.get_calendar_year(), m, pft.id, gcpft_mfireflux_c_pft[pft.id][m]);
			}

			if(gcpft_mfireflux_c_pft[pft.id][m] > 0.00001) {
				//dprintf("Year = %i, month = %i, WRITING STAND PFT =%i flux = %.20f\n", date.get_calendar_year(), m, pft.id, standpft_mfireflux_c_pft[pft.id][m]);
				//dprintf("Year = %i, month = %i, WRITING GRIDCELL PFT =%i flux = %.20f\n", date.get_calendar_year(), m, pft.id, gcpft_mfireflux_c_pft[pft.id][m]);
			}

			if(firemodel == SPITFIRE){
				outlimit_spitfire(out, out_monthly_burned_area_pft[pft.id], gcpft_monthly_burned_area_pft[pft.id][m]);
				outlimit_spitfire(out, out_mfireflux_c_pft[pft.id], gcpft_mfireflux_c_pft[pft.id][m]);
			}
			else if(firemodel == BLAZE) {
				outlimit_spitfire(out, out_monthly_burned_area_pft[pft.id], gridcell.pft[pft.id].blaze_burned_area[m]);
			}
		}


		//outlimit(out,out_speciesheights, height);
		pftlist.nextobj();

	} // *** End of PFT loop ***


	// **** Special case for monthly perPFT burnt area ***
	// Add the BareSoil output as the last column of the file
	double gcpft_monthly_burned_area_BareSoil = 0.0;
	double standpft_monthly_burned_area_BareSoil = 0.0;
	for (m=0;m<12;m++) {

		// re-zero gricell total for this month
		gcpft_monthly_burned_area_BareSoil = 0.0;

		// Loop through Stands
		Gridcell::iterator gc_itr = gridcell.begin();
		while (gc_itr != gridcell.end()) {

			// re-zero the stand-level total
			standpft_monthly_burned_area_BareSoil = 0.0;

			// Loop through Patches and sum to the stand level total
			// including correction for number of patches and stand fraction
			Stand& stand = *gc_itr;
			stand.firstobj();
			while (stand.isobj) {
				Patch& patch = stand.getobj();
				standpft_monthly_burned_area_BareSoil += patch.fuel.monthly_burned_area_BareSoil[m] * patch.stand.get_gridcell_fraction() / (double)patch.stand.npatch();
				stand.nextobj();
			} // end patch loop

			// add the stand level total to the gridcell level total
			gcpft_monthly_burned_area_BareSoil+=standpft_monthly_burned_area_BareSoil ;

			++gc_itr;

		} // end stand loop

		// print gridcell total for BareSoil burned area
		outlimit_spitfire(out, out_monthly_burned_area_pft[npftconst], gcpft_monthly_burned_area_BareSoil);

	} // end monthly loop



	// MONTHLY OUTPUT VARIABLES

	// As discussed below

	Gridcell::iterator gc_itr = gridcell.begin();

	// Determine flammable fraction
	double flammable_fraction = 0.0;
	while (gc_itr != gridcell.end()) {
		Stand& stand = *gc_itr;

		// look at first patch, assume that all patches
		stand.firstobj();
		Patch& patch = stand.getobj();
		if(patch.has_fires()) flammable_fraction += stand.get_gridcell_fraction();

		++gc_itr;
	}

	// reset Stand counter for next loop
	gc_itr = gridcell.begin();

	// Loop through Stands
	while (gc_itr != gridcell.end()) {
		Stand& stand = *gc_itr;
		stand.firstobj();


		//Loop through Patches
		while (stand.isobj) {
			Patch& patch = stand.getobj();

			double to_gridcell_average = stand.get_gridcell_fraction() / (double)stand.npatch();

			pyro_flux_C += patch.fluxes.get_annual_flux(Fluxes::FIREC)*to_gridcell_average;
			pyro_flux_CO += patch.fluxes.get_annual_flux(Fluxes::CO_FIRE)*to_gridcell_average;
			pyro_flux_CO2 += patch.fluxes.get_annual_flux(Fluxes::CO2_FIRE)*to_gridcell_average;
			pyro_flux_CH4 += patch.fluxes.get_annual_flux(Fluxes::CH4_FIRE)*to_gridcell_average;
			pyro_flux_VOC += patch.fluxes.get_annual_flux(Fluxes::VOC_FIRE)*to_gridcell_average;
			pyro_flux_TPM += patch.fluxes.get_annual_flux(Fluxes::TPM_FIRE)*to_gridcell_average;
			pyro_flux_NOx += patch.fluxes.get_annual_flux(Fluxes::NOx_FIRE)*to_gridcell_average;
			pyro_flux_COs += patch.fluxes.get_annual_flux(Fluxes::COs_FIRE)*to_gridcell_average;
			pyro_flux_CO2s += patch.fluxes.get_annual_flux(Fluxes::CO2s_FIRE)*to_gridcell_average;
			pyro_flux_CH4s += patch.fluxes.get_annual_flux(Fluxes::CH4s_FIRE)*to_gridcell_average;


			// Monthly output variables

			// number of fires in this patch this month, temporary variable (scaled to gridcell)
			double num_fires_this_patch_this_month_scaled = 0.0;

			for (m=0;m<12;m++) {

				// SCALED TO THE GRIDCELL AREA

				// burnt areas, numbers of fires and potential ignitions are *not* scaled to the flammable area,
				// i.e. the are the burnt fractions and number of with respect to the whole gridcells

				// potential ignitions (before FDI suppression and other thresholds applied)
				mhuman_pot_ign[m] += patch.fuel.monthly_human_potential_ignitions[m] * to_gridcell_average;
				mlightning_pot_ign[m] += patch.fuel.monthly_lightning_potential_ignitions[m] * to_gridcell_average;

				//  actual ignitions (after FDI and threshholds)
				mhuman_ign[m] += patch.fuel.monthly_human_ignitions[m] * to_gridcell_average;
				mlightning_ign[m] += patch.fuel.monthly_lightning_ignitions[m] * to_gridcell_average;

				// fire fractions - first one can/should be deleted
				mfirefrac[m] += patch.mfirefrac[m] * to_gridcell_average;
				mfirefrac_applied[m] += patch.mfirefrac_applied[m] * to_gridcell_average;

				// number of fires/home/b/b380710/work/runs/ISIMIP3/SIMFIRE-BLAZE/ISIMIP3a/gswp3-w5e5/spinup/spinclim_1850soc_nofire
				// this variable is used to give the weighted contribution (weighted per fire) of the fires from this patch to the gridcell total
				// it has already been scaled by the flammable area in spitfire_daily_sums()
				num_fires_this_patch_this_month_scaled = patch.fuel.monthly_number_fires[m];
				// this variable also used to divide through the monthly real fire accumulated values totals below
				real_num_fires[m] += num_fires_this_patch_this_month_scaled;


				// SCALED TO THE TOTAL FLAMMABLE FRACTION OF THE GRIDCELL

				// These monthly variables which are intrinsic either to the fuel load or fire characteristics themselves.
				// Therefore they are only considered for flammable stands and so require patch-to-gridcell scaling/weighting based
				// on the flammable areas of the gridcell only.
				// *** NOTE *** This scaling has already been done in function spitfire_daily_sums() so does not need to be done here.


				mlivegrass_fuel[m] += patch.fuel.monthly_livegrass_fuel[m];
				m1hr_fuel[m] += patch.fuel.monthly_1hr_fuel[m];
				m10hr_fuel[m] += patch.fuel.monthly_10hr_fuel[m];
				m100hr_fuel[m] += patch.fuel.monthly_100hr_fuel[m];
				m1000hr_fuel[m] += patch.fuel.monthly_1000hr_fuel[m];

				mlivegrass_fm[m] += patch.fuel.monthly_livegrass_fm[m];
				m1hr_fm[m] += patch.fuel.monthly_1hr_fm[m];
				m10hr_fm[m] += patch.fuel.monthly_10hr_fm[m];
				m100hr_fm[m] += patch.fuel.monthly_100hr_fm[m];
				m1000hr_fm[m] += patch.fuel.monthly_1000hr_fm[m];

				mlivegrass_cc[m] += patch.fuel.monthly_livegrass_cc[m];
				m1hr_cc[m] += patch.fuel.monthly_1hr_cc[m];
				m10hr_cc[m] += patch.fuel.monthly_10hr_cc[m];
				m100hr_cc[m] += patch.fuel.monthly_100hr_cc[m];
				m1000hr_cc[m] += patch.fuel.monthly_1000hr_cc[m];

				mRoS[m] += patch.fuel.monthly_RoS[m];
				mfireintens[m] += patch.fuel.monthly_fire_intensity[m];
				mfiresize[m] += patch.fuel.monthly_fire_size[m];
				mtau_l[m] += patch.fuel.monthly_tau_l[m];
				mfire_durat[m] += patch.fuel.monthly_fire_durat[m];
				mscorch_height[m] += patch.fuel.monthly_scorch_height[m];

				mMoE[m] += patch.fuel.monthly_MoE[m];
				mSAV[m] += patch.fuel.monthly_SAV[m];
				mFBD[m] += patch.fuel.monthly_FBD[m];
				mDFM[m] += patch.fuel.monthly_DFM[m];

				meff_wind[m] += patch.fuel.monthly_effective_windspeed[m];
				mavenest[m] += patch.fuel.monthly_Nesterov[m];
				mnfdi[m] += patch.fuel.monthly_FDI[m];
				mburn_prob[m] += patch.fuel.monthly_burn_prob[m];

				// also annual fuel load values
				annual_grass_fuel += patch.fuel.monthly_livegrass_fuel[m];
				annual_1hr_fuel += patch.fuel.monthly_1hr_fuel[m];
				annual_10hr_fuel += patch.fuel.monthly_10hr_fuel[m];
				annual_100hr_fuel += patch.fuel.monthly_100hr_fuel[m];
				annual_1000hr_fuel += patch.fuel.monthly_1000hr_fuel[m];





				if (num_fires_this_patch_this_month_scaled > 0) {

					real_nesterov[m] += patch.fuel.monthly_realised_nesterov[m];
					real_scorch_height[m] += patch.fuel.monthly_realised_scorch_height[m];
					real_residence_time[m] += patch.fuel.monthly_realised_residence_time[m];
					real_intensity[m] += patch.fuel.monthly_realised_intensity[m];
					real_duration[m] += patch.fuel.monthly_realised_duration[m];
					real_fire_size[m] += patch.fuel.monthly_realised_fire_size[m];
					real_speed[m] += patch.fuel.monthly_realised_fire_speed[m];
					real_DFM[m] += patch.fuel.monthly_realised_DFM[m];
					real_RoS[m] += patch.fuel.monthly_realised_RoS[m];
					real_livegrass_cc[m] += patch.fuel.monthly_realised_livegrass_cc[m];
					real_1hr_cc[m] += patch.fuel.monthly_realised_1hr_cc[m];
					real_10hr_cc[m] += patch.fuel.monthly_realised_10hr_cc[m];
					real_100hr_cc[m] += patch.fuel.monthly_realised_100hr_cc[m];
					real_1000hr_cc[m] += patch.fuel.monthly_realised_1000hr_cc[m];

				}

				// TODO - check scaling of these
				if( patch.fluxes.get_monthly_flux(Fluxes::FIREC, m) > 0.0) {
					//dprintf("Year = %i, day = %i, Retrieving total flux = %.20f, to_gridcell_average = %.20f\n", date.get_calendar_year(), date.day, patch.fluxes.get_monthly_flux(Fluxes::FIREC, m), to_gridcell_average);
				}
				mfireflux_c[m] += patch.fluxes.get_monthly_flux(Fluxes::FIREC, m)*to_gridcell_average;
				mfireflux_co[m] += patch.fluxes.get_monthly_flux(Fluxes::CO_FIRE, m)*to_gridcell_average;
				mfireflux_co2[m] += patch.fluxes.get_monthly_flux(Fluxes::CO2_FIRE, m)*to_gridcell_average;
				mfireflux_ch4[m] += patch.fluxes.get_monthly_flux(Fluxes::CH4_FIRE, m)*to_gridcell_average;
				mind_killed[m] += patch.fuel.monthly_nind_killed[m] * to_gridcell_average;
				mtreecover_reduction_fire[m] += patch.fuel.mtreecover_reduction_fire[m] * to_gridcell_average;


			}  // monthly loop

			stand.nextobj();
		} // patch loop

		++gc_itr;
	} // stand loop


	// The "real" fire properties have been summed (with a weight of 1.0 per fire), so they need to be divided by the number of fires to get the
	// final gridcell mean across all fires
	for (m = 0; m < 12; m++) {
		if (real_num_fires[m] > 0.0) {
			real_nesterov[m] /= real_num_fires[m];
			real_scorch_height[m] /= real_num_fires[m];
			real_residence_time[m] /= real_num_fires[m];
			real_intensity[m] /= real_num_fires[m];
			real_duration[m] /= real_num_fires[m];
			real_livegrass_cc[m]/= real_num_fires[m];
			real_fire_size[m] /= real_num_fires[m];
			real_1hr_cc[m] /= real_num_fires[m];
			real_10hr_cc[m] /= real_num_fires[m];
			real_100hr_cc[m] /= real_num_fires[m];
			real_1000hr_cc[m] /= real_num_fires[m];
			real_speed[m] /= real_num_fires[m];
			real_DFM[m] /= real_num_fires[m];
			real_RoS[m] /= real_num_fires[m];
		} else {
			real_nesterov[m] = 0;
			real_scorch_height[m] = 0;
			real_residence_time[m] = 0;
			real_intensity[m] = 0;
			real_duration[m] = 0;
			real_fire_size[m] = 0;
			real_livegrass_cc[m] = 0;
			real_1hr_cc[m] = 0;
			real_10hr_cc[m] = 0;
			real_100hr_cc[m] = 0;
			real_1000hr_cc[m] = 0;
			real_speed[m] = 0;
			real_DFM[m] = 0;
			real_RoS[m] = 0;
		}

	} // monthly loop



	// Print gridcell totals to files

	// TODO - check the scaling of these

	// Annual values
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_C);
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_CO2);
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_CO);
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_CH4);
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_VOC);
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_TPM);
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_NOx);
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_CO2s);
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_COs);
	outlimit_spitfire(out, out_pyro_flux, pyro_flux_CH4s);

	// Annual days with above Nesterov threshold
	for (int i = 0; i < 365; i++) {
		//if (dnest[i] >= 300)
		nestgt300++;
		//if (dnest[i] >= 1000)
		nestgt1000++;
	}

	outlimit_spitfire(out, out_afdays, nestgt300);
	outlimit_spitfire(out, out_afdays, nestgt1000);



	outlimit_spitfire(out,out_litter_wood, litter_wood_gridcell); // MF-LITTER
	outlimit_spitfire(out,out_litter_leaf, litter_leaf_gridcell); // MF-LITTER
	outlimit_spitfire(out,out_litter_repr, litter_repr_gridcell); // MF-LITTER

	outlimit_spitfire(out, out_annual_fuel_loads,  annual_grass_fuel/12) ; // MF-LITTER
	outlimit_spitfire(out, out_annual_fuel_loads,  annual_1hr_fuel/12) ; // MF-LITTER
	outlimit_spitfire(out, out_annual_fuel_loads,  annual_10hr_fuel/12) ; // MF-LITTER
	outlimit_spitfire(out, out_annual_fuel_loads,  annual_100hr_fuel/12) ; // MF-LITTER
	outlimit_spitfire(out, out_annual_fuel_loads,  annual_1000hr_fuel/12) ; // MF-LITTER




	// Print landcover totals to files
	if (run_landcover) {
		for(int i=0;i<NLANDCOVERTYPES;i++) {
			if(run[i]) {

				// MF MAYBE WE NEED LANDCOVER TOTALS FOR SPITFIRE??
				outlimit_spitfire(out,out_litter_wood, landcover_litter_wood[i]);
				outlimit_spitfire(out,out_litter_repr,  landcover_litter_repr[i]);
				outlimit_spitfire(out,out_litter_leaf,  landcover_litter_leaf[i]);

				//outlimit(out,out_cmass, landcover_cmass[i]);

			}
		}
	}

	// Print monthly output variables
	for (m=0;m<12;m++) {

		outlimit_spitfire(out, out_mfirefrac, mfirefrac[m]);
		outlimit_spitfire(out, out_mfirefrac_applied, mfirefrac_applied[m]);
		outlimit_spitfire(out, out_mnfdi, mnfdi[m]);
		outlimit_spitfire(out, out_mburn_prob, mburn_prob[m]);
		outlimit_spitfire(out, out_mfireintens, mfireintens[m]);
		outlimit_spitfire(out, out_mavenest, mavenest[m]);
		outlimit_spitfire(out, out_mRoS, mRoS[m]);

		outlimit_spitfire(out, out_mlivegrass_fuel, mlivegrass_fuel[m]);
		outlimit_spitfire(out, out_m1hr_fuel, m1hr_fuel[m]);
		outlimit_spitfire(out, out_m10hr_fuel, m10hr_fuel[m]);
		outlimit_spitfire(out, out_m100hr_fuel, m100hr_fuel[m]);
		outlimit_spitfire(out, out_m1000hr_fuel, m1000hr_fuel[m]);

		outlimit_spitfire(out, out_mlivegrass_fm, mlivegrass_fm[m]);
		outlimit_spitfire(out, out_m1hr_fm, m1hr_fm[m]);
		outlimit_spitfire(out, out_m10hr_fm, m10hr_fm[m]);
		outlimit_spitfire(out, out_m100hr_fm, m100hr_fm[m]);
		outlimit_spitfire(out, out_m1000hr_fm, m1000hr_fm[m]);

		outlimit_spitfire(out, out_mlivegrass_cc, mlivegrass_cc[m]);
		outlimit_spitfire(out, out_m1hr_cc, m1hr_cc[m]);
		outlimit_spitfire(out, out_m10hr_cc, m10hr_cc[m]);
		outlimit_spitfire(out, out_m100hr_cc, m100hr_cc[m]);
		outlimit_spitfire(out, out_m1000hr_cc, m1000hr_cc[m]);

		outlimit_spitfire(out, out_real_livegrass_cc, real_livegrass_cc[m]);
		outlimit_spitfire(out, out_real_1hr_cc, real_1hr_cc[m]);
		outlimit_spitfire(out, out_real_10hr_cc, real_10hr_cc[m]);
		outlimit_spitfire(out, out_real_100hr_cc, real_100hr_cc[m]);
		outlimit_spitfire(out, out_real_1000hr_cc,real_1000hr_cc[m]);

		outlimit_spitfire(out, out_mtau_l, mtau_l[m]);
		outlimit_spitfire(out, out_mscorch_height, mscorch_height[m]);
		outlimit_spitfire(out, out_mfire_durat, mfire_durat[m]);

		// allocation diagnostics
		outlimit_spitfire(out, out_allocation_fails, gridcell.climate.monthly_num_fails[m]);
		outlimit_spitfire(out, out_allocation_iters, gridcell.climate.monthly_mean_num_iterations[m] / date.ndaymonth[m]);

		outlimit_spitfire(out, out_mSAV, mSAV[m]);
		outlimit_spitfire(out, out_mFBD, mFBD[m]);
		outlimit_spitfire(out, out_mMoE, mMoE[m]);
		outlimit_spitfire(out, out_mDFM, mDFM[m]);
		outlimit_spitfire(out, out_meff_wind, meff_wind[m]);

		outlimit_spitfire(out, out_mfiresize, mfiresize[m]);
		outlimit_spitfire(out, out_mhuman_ign, mhuman_ign[m]);
		outlimit_spitfire(out, out_mlightning_ign, mlightning_ign[m]);
		outlimit_spitfire(out, out_mhuman_pot_ign, mhuman_pot_ign[m]);
		outlimit_spitfire(out, out_mlightning_pot_ign, mlightning_pot_ign[m]);

		outlimit_spitfire(out, out_real_nesterov, real_nesterov[m]);
		outlimit_spitfire(out, out_real_scorch_height, real_scorch_height[m]);
		outlimit_spitfire(out, out_real_residence_time, real_residence_time[m]);
		outlimit_spitfire(out, out_real_intensity, real_intensity[m]);
		outlimit_spitfire(out, out_real_duration, real_duration[m]);
		outlimit_spitfire(out, out_real_fire_size, real_fire_size[m]);
		outlimit_spitfire(out, out_real_speed, real_speed[m]);
		outlimit_spitfire(out, out_real_RoS, real_RoS[m]);
		outlimit_spitfire(out, out_real_DFM, real_DFM[m]);
		outlimit_spitfire(out, out_real_num_fires, real_num_fires[m]);

		outlimit_spitfire(out, out_mfireflux_c, mfireflux_c[m]);
		outlimit_spitfire(out, out_mfireflux_co, mfireflux_co[m]);
		outlimit_spitfire(out, out_mfireflux_co2, mfireflux_co2[m]);
		outlimit_spitfire(out, out_mfireflux_ch4, mfireflux_ch4[m]);

		outlimit_spitfire(out, out_monthly_nind_killed, mind_killed[m]);
		outlimit_spitfire(out, out_mtreecover_reduction_fire, mtreecover_reduction_fire[m]);


		// MF: Phenology checks and fine fuel
		outlimit_spitfire(out,out_mleafshed,    mleafshed[m]);
		outlimit_spitfire(out,out_mfinefuel,    mfinefuel[m]);


	}

	// Loop through Stands
	while (gc_itr != gridcell.end()) {
		Stand& stand = *gc_itr;
		stand.firstobj();

	}
}


/// Output of simulation results at the end of each day
/// and accumulates monthly
/** This function does not have to provide any information to the framework.
 */
void SPITFIREOutput::outdaily(Gridcell& gridcell) {


	double lon = gridcell.get_lon();
	double lat = gridcell.get_lat();
	OutputRows out(output_channel, lon, lat, date.get_calendar_year(), date.day);

	// number of fires in this patch (for weighting by number of fires)
	double num_fires_patch = 0.0;

	// Sum daily fire properties across stands/patches
	double num_fires = 0.0;
	double fire_intensity = 0.0;
	double fire_size = 0.0;
	double fire_duration = 0.0;
	double fire_speed = 0.0;
	double fire_ros = 0.0;
	double fm_grass = 0.0;
	double fm_1hr = 0.0;
	double fm_10hr = 0.0;
	double fm_100hr = 0.0;
	double fm_char = 0.0;
	double flam_NFDI = 0.0;
	double flam_WBP = 0.0;



	// diagnostic variables (equally weighted across patches) which are outputted even if there are no fires
	double fire_intensity_diagnostic = 0.0;
	double fire_size_diagnostic = 0.0;
	double fire_duration_diagnostic = 0.0;
	double fire_speed_diagnostic = 0.0;
	double fire_ros_diagnostic = 0.0;
	double fm_grass_diagnostic = 0.0;
	double fm_1hr_diagnostic = 0.0;
	double fm_10hr_diagnostic = 0.0;
	double fm_100hr_diagnostic = 0.0;
	double fm_char_diagnostic = 0.0;
	double flam_NFDI_diagnostic = 0.0;
	double flam_WBP_diagnostic = 0.0;



	double this_speed = 0.0;

	// daily values

	Gridcell::iterator gc_itr = gridcell.begin();


	// Loop through Stands
	while (gc_itr != gridcell.end()) {
		Stand& stand = *gc_itr;
		stand.firstobj();

		// re-zero the totals

		//Loop through Patches
		while (stand.isobj) {
			Patch& patch = stand.getobj();

			double to_gridcell_average = stand.get_gridcell_fraction() / (double)stand.npatch();

			// speed     = distance / time
			// (km/day)  = rate of fire spread forward (m/min) * duration (mins) / 1000 (m -> km) / "apparent time of observational period" (1 day)
			this_speed = (patch.fuel.ros_f * patch.fuel.fire_durat) / 1000.0;

			// calculate the number of fires
			num_fires_patch = patch.fuel.daily_number_fires * to_gridcell_average;

			// accumulate and weight by the number of fires in the patch
			num_fires += num_fires_patch;
			// fire properties
			fire_intensity += patch.fuel.daily_fire_intensity * num_fires_patch;
			fire_size += patch.fuel.fire_size / 100 * num_fires_patch;  // output in km^2
			fire_duration += patch.fuel.fire_durat * num_fires_patch;
			fire_speed += this_speed * num_fires_patch;
			fire_ros += patch.fuel.ros_f * num_fires_patch;
			// fuel moistures
			fm_grass += patch.fuel.dlm_livegrass * num_fires_patch;
			fm_1hr += patch.fuel.dlm_1hr * num_fires_patch;
			fm_10hr += patch.fuel.dlm_10hr * num_fires_patch;
			fm_100hr += patch.fuel.dlm_100hr * num_fires_patch;
			fm_char += patch.fuel.char_dlm * num_fires_patch;
			// flammability
			flam_WBP += patch.fuel.burn_probability * num_fires_patch;
			flam_NFDI += patch.fuel.fdi * num_fires_patch;



			// diagnostic variables (simply weight by the burnable area of the gridcell)
			//fire properties
			fire_intensity_diagnostic += patch.fuel.daily_fire_intensity  * patch.to_gridcell_average_flammable_only;
			fire_size_diagnostic += patch.fuel.fire_size / 100 * patch.to_gridcell_average_flammable_only; // output in km^2
			fire_duration_diagnostic += patch.fuel.fire_durat * patch.to_gridcell_average_flammable_only;
			fire_speed_diagnostic += this_speed * patch.to_gridcell_average_flammable_only;
			fire_ros_diagnostic += patch.fuel.ros_f * patch.to_gridcell_average_flammable_only;
			// fuel moistures
			fm_grass_diagnostic += patch.fuel.dlm_livegrass * patch.to_gridcell_average_flammable_only;
			fm_1hr_diagnostic += patch.fuel.dlm_1hr * patch.to_gridcell_average_flammable_only;
			fm_10hr_diagnostic += patch.fuel.dlm_10hr * patch.to_gridcell_average_flammable_only;
			fm_100hr_diagnostic += patch.fuel.dlm_100hr * patch.to_gridcell_average_flammable_only;
			fm_char_diagnostic += patch.fuel.char_dlm * patch.to_gridcell_average_flammable_only;
			// flammability
			flam_WBP_diagnostic += patch.fuel.burn_probability * patch.to_gridcell_average_flammable_only;
			flam_NFDI_diagnostic += patch.fuel.fdi * patch.to_gridcell_average_flammable_only;


			stand.nextobj();

		} // patch loop
		++gc_itr;

	} // stand loop

	if(!negligible(num_fires, -10)){

		outlimit_daily_spitfire(out, out_daily_fires, num_fires);
		outlimit_daily_spitfire(out, out_daily_fires, fire_size/num_fires);
		outlimit_daily_spitfire(out, out_daily_fires, fire_intensity/num_fires);
		outlimit_daily_spitfire(out, out_daily_fires, fire_duration/num_fires);
		outlimit_daily_spitfire(out, out_daily_fires, fire_speed/num_fires);
		outlimit_daily_spitfire(out, out_daily_fires, fire_ros/num_fires);
		outlimit_daily_spitfire(out, out_daily_fuel_moisture, fm_grass/num_fires);
		outlimit_daily_spitfire(out, out_daily_fuel_moisture, fm_1hr/num_fires);
		outlimit_daily_spitfire(out, out_daily_fuel_moisture, fm_10hr/num_fires);
		outlimit_daily_spitfire(out, out_daily_fuel_moisture, fm_100hr/num_fires);
		outlimit_daily_spitfire(out, out_daily_fuel_moisture, fm_char/num_fires);
		outlimit_daily_spitfire(out, out_daily_flammability, flam_NFDI/num_fires);
		outlimit_daily_spitfire(out, out_daily_flammability, flam_WBP/num_fires);

	}

	outlimit_daily_spitfire(out, out_daily_fires_diagnostics, num_fires);
	outlimit_daily_spitfire(out, out_daily_fires_diagnostics, fire_size_diagnostic);
	outlimit_daily_spitfire(out, out_daily_fires_diagnostics, fire_intensity_diagnostic);
	outlimit_daily_spitfire(out, out_daily_fires_diagnostics, fire_duration_diagnostic);
	outlimit_daily_spitfire(out, out_daily_fires_diagnostics, fire_speed_diagnostic);
	outlimit_daily_spitfire(out, out_daily_fires_diagnostics, fire_ros_diagnostic);
	outlimit_daily_spitfire(out, out_daily_fuel_moisture_diagnostics, fm_grass_diagnostic);
	outlimit_daily_spitfire(out, out_daily_fuel_moisture_diagnostics, fm_1hr_diagnostic);
	outlimit_daily_spitfire(out, out_daily_fuel_moisture_diagnostics, fm_10hr_diagnostic);
	outlimit_daily_spitfire(out, out_daily_fuel_moisture_diagnostics, fm_100hr_diagnostic);
	outlimit_daily_spitfire(out, out_daily_fuel_moisture_diagnostics, fm_char_diagnostic);
	outlimit_daily_spitfire(out, out_daily_flammability_diagnostics, flam_NFDI_diagnostic);
	outlimit_daily_spitfire(out, out_daily_flammability_diagnostics, flam_WBP_diagnostic);


}

// SSR: Dummy implementations to inherit purely virtual functions I added to OutputModule in GGCMI branch
void SPITFIREOutput::outharvest(Gridcell& gridcell) {
}
void SPITFIREOutput::outharvest_justphupvd(Gridcell& gridcell) {
}
void SPITFIREOutput::outannual_ggcmi(Gridcell& gridcell) {
}
void SPITFIREOutput::openlocalfiles_ggcmi() {
}
void SPITFIREOutput::closelocalfiles_ggcmi() {
}

} // namespace
