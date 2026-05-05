///////////////////////////////////////////////////////////////////////////////////////
/// \file commonoutput.h
/// \brief Output module for the most commonly needed output files
///
/// \author Joe Siltberg
/// $Date: 2016-12-16 16:21:33 +0100 (Fri, 16 Dec 2016) $
///
///////////////////////////////////////////////////////////////////////////////////////

#ifndef LPJ_GUESS_SPITFIRE_OUTPUT_H
#define LPJ_GUESS_SPITFIRE_OUTPUT_H

#include "guess.h"  // to access npftconst
#include "outputmodule.h"
#include "outputchannel.h"
#include "gutil.h"

namespace GuessOutput {

/// Output module for the most commonly needed output files
class SPITFIREOutput : public OutputModule {
public:

	SPITFIREOutput();

	~SPITFIREOutput();

	// implemented functions inherited from OutputModule
	// (see documentation in OutputModule)

	void init();

	void outannual(Gridcell& gridcell);

	void outdaily(Gridcell& gridcell);

	void openlocalfiles(Gridcell& gridcell) {};

	void closelocalfiles(Gridcell& gridcell) {};
	
	// SSR: Dummy implementations to inherit purely virtual functions I added to OutputModule in GGCMI branch
	void outharvest(Gridcell& gridcell);
    void outharvest_justphupvd(Gridcell& gridcell);
	void outannual_ggcmi(Gridcell& gridcell);
    void openlocalfiles_ggcmi();
    void closelocalfiles_ggcmi();

	
private:

	/// Defines all output tables
	void define_output_tables();

	// MF: SPITFIRE (and other) output file name parameters
	xtring file_mlai_grass;
	xtring file_pyro_flux;
	xtring file_mfirefrac; // Cfluxes and annual burned areas
	xtring file_mfirefrac_applied; // Cfluxes and annual burned areas
	xtring file_mnfdi; // summed over the month
	xtring file_mburn_prob; // summed over the month
	xtring file_mavenest; // average monthly Nesterov
	xtring file_mfireintens; // summed over the month
	xtring file_afdays; // annual fire days
	xtring file_mRoS; // average monthly Rate of Spread
	xtring file_mdlm_livegrass; // average monthly Rate of Spread
	xtring file_mfiresize; // average monthly fire size
	xtring file_mhuman_ign; // average daily human ignitions across month
	xtring file_mlightning_ign; // average daily lightning ignitions across month
	xtring file_mhuman_pot_ign; // average daily human potential ignitions across month
	xtring file_mlightning_pot_ign; // average daily lightning potential ignitions across month


	xtring file_mlivegrass_fuel; // average monthly 1hr fuel load
	xtring file_m1hr_fuel; // average monthly 1hr fuel load
	xtring file_m10hr_fuel; // average monthly 10hr fuel load
	xtring file_m100hr_fuel; // average monthly 100hr fuel load
	xtring file_m1000hr_fuel; // average monthly 1000hr fuel load

	xtring file_mlivegrass_fm; // average monthly 1hr fuel moisture
	xtring file_m1hr_fm; // average monthly 1hr fuel moisture
	xtring file_m10hr_fm; // average monthly 10hr fuel moisture
	xtring file_m100hr_fm; // average monthly 100hr fuel moisture
	xtring file_m1000hr_fm; // average monthly 1000hr fuel moisture

	xtring file_mlivegrass_cc; // average monthly livegrass combustion completeness
	xtring file_m1hr_cc; // average monthly 1hr fuel combustion completeness
	xtring file_m10hr_cc; // average monthly 10hr fuel combustion completeness
	xtring file_m100hr_cc; // average monthly 100hr fuel combustion completeness
	xtring file_m1000hr_cc; // average monthly 1000hr fuel combustion completeness

	xtring file_ag_cmass; // above-ground carbon mass per PFT
	xtring file_mfire_durat; // fire duration
	xtring file_mscorch_height; // obv.
	xtring file_mtau_l; //residence time
	xtring file_allocation_fails; // diagnostics for fire allocation to suitable patches
	xtring file_allocation_iters; // diagnostics for fire allocation to suitable patches

	xtring file_real_duration;
	xtring file_real_scorch_height;
	xtring file_real_residence_time;
	xtring file_real_intensity;
	xtring file_real_nesterov;
	xtring file_real_fire_size;
	xtring file_real_num_fires;
	xtring file_real_speed;
	xtring file_real_RoS;
	xtring file_real_DFM;


	xtring file_real_livegrass_cc;
	xtring file_real_1hr_cc;
	xtring file_real_10hr_cc;
	xtring file_real_100hr_cc;
	xtring file_real_1000hr_cc;

	xtring file_mSAV;
	xtring file_mFBD;
	xtring file_mMoE;
	xtring file_mDFM;
	xtring file_meff_wind;

	xtring file_mnbp;

	// MF: phenology, leaf shed and fine fuel
	xtring file_mleafshed, file_aleafshed, file_mfinefuel;

	// MF Per month, per PFT variables, for FireMIP. Uff...
	// C flux from fire
	xtring file_cflux_fire_jan, file_cflux_fire_feb, file_cflux_fire_mar, file_cflux_fire_apr, file_cflux_fire_may, file_cflux_fire_jun, file_cflux_fire_jul, file_cflux_fire_aug, file_cflux_fire_sep, file_cflux_fire_oct, file_cflux_fire_nov, file_cflux_fire_dec;
	// BA fraction per PFT ???
	xtring file_ba_frac_jan, file_ba_frac_feb, file_ba_frac_mar, file_ba_frac_apr, file_ba_frac_may, file_ba_frac_jun, file_ba_frac_jul, file_ba_frac_aug, file_ba_frac_sep, file_ba_frac_oct, file_ba_frac_nov, file_ba_frac_dec;
	// C mass
	xtring file_cmass_jan, file_cmass_feb, file_cmass_mar, file_cmass_apr, file_cmass_may, file_cmass_jun, file_cmass_jul, file_cmass_aug, file_cmass_sep, file_cmass_oct, file_cmass_nov, file_cmass_dec;
	// GPP
	xtring file_gpp_jan, file_gpp_feb, file_gpp_mar, file_gpp_apr, file_gpp_may, file_gpp_jun, file_gpp_jul, file_gpp_aug, file_gpp_sep, file_gpp_oct, file_gpp_nov, file_gpp_dec;
	// NPP
	xtring file_npp_jan, file_npp_feb, file_npp_mar, file_npp_apr, file_npp_may, file_npp_jun, file_npp_jul, file_npp_aug, file_npp_sep, file_npp_oct, file_npp_nov, file_npp_dec;
	xtring file_mnpppft;
	// NBP
	xtring file_nbp_jan, file_nbp_feb, file_nbp_mar, file_nbp_apr, file_nbp_may, file_nbp_jun, file_nbp_jul, file_nbp_aug, file_nbp_sep, file_nbp_oct, file_nbp_nov, file_nbp_dec;


	// MF-FIRESL
	xtring file_firesl;
	// MF-LITTER
	xtring file_litter_wood, file_litter_leaf, file_litter_repr;


	// // *** FLUXES FROM FIRE ***
	xtring file_cflux_fire;
	xtring file_mfireflux_c;
	xtring file_mfireflux_co;
	xtring file_mfireflux_co2;
	xtring file_mfireflux_ch4;
	xtring file_mfireflux_c_pft;

	// MF-MORTALITY
	xtring file_monthly_nind_killed;
	xtring file_mtreecover_reduction_fire;

	// Per-PFT, monthly (New Order, replaced above based in P. Antoni's GCP code)
	xtring file_monthly_burned_area_pft;



	// Daily output

	// "real" daily values (averaged across all actual fires)
	xtring file_daily_fires;
	xtring file_daily_fuel_moisture;
	xtring file_daily_flammability;


	// "diagnostic" daily values (averaged across flammable patches)
	xtring file_daily_fires_diagnostics;
	xtring file_daily_fuel_moisture_diagnostics;
	xtring file_daily_flammability_diagnostics;


	// new annual variables for convenience and benchmarking with reduced file sizes
	xtring file_annual_fuel_loads;


	// MF: SPITFIRE (and other) output file tables
	// MF Above ground C mass
	Table out_ag_cmass;

	// MF-FIRESL
	Table out_firesl;

	// MF-LITTER
	Table out_litter_wood, out_litter_leaf, out_litter_repr;

	Table out_mfirefrac;
	Table out_mfirefrac_applied;
	Table out_pyro_flux;
	Table out_mnfdi;
	Table out_mburn_prob;
	Table out_mfireintens;
	Table out_afdays;
	Table out_mavenest;
	Table out_mRoS;
	Table out_mdlm_livegrass;

	Table out_mlivegrass_fuel;
	Table out_m1hr_fuel;
	Table out_m10hr_fuel;
	Table out_m100hr_fuel;
	Table out_m1000hr_fuel;

	Table out_mlivegrass_fm;
	Table out_m1hr_fm;
	Table out_m10hr_fm;
	Table out_m100hr_fm;
	Table out_m1000hr_fm;

	Table out_mlivegrass_cc;
	Table out_m1hr_cc;
	Table out_m10hr_cc;
	Table out_m100hr_cc;
	Table out_m1000hr_cc;

	Table out_real_livegrass_cc;
	Table out_real_1hr_cc;
	Table out_real_10hr_cc;
	Table out_real_100hr_cc;
	Table out_real_1000hr_cc;

	Table out_mtau_l;
	Table out_mfire_durat;
	Table out_mscorch_height;
	Table out_allocation_fails;
	Table out_allocation_iters;

	Table out_real_duration;
	Table out_real_scorch_height;
	Table out_real_residence_time;
	Table out_real_intensity;
	Table out_real_nesterov;
	Table out_real_fire_size;
	Table out_real_num_fires;
	Table out_real_speed;
	Table out_real_RoS;
	Table out_real_DFM;


	Table out_mFBD;
	Table out_mSAV;
	Table out_mMoE;
	Table out_mDFM;
	Table out_meff_wind;

	Table out_mnbp;

	Table out_mfiresize;
	Table out_mhuman_ign;
	Table out_mlightning_ign;
	Table out_mhuman_pot_ign;
	Table out_mlightning_pot_ign;



	// *** FLUXES FROM FIRE ***
	Table out_cflux_fire;
	Table out_mfireflux_c;
	Table out_mfireflux_co;
	Table out_mfireflux_co2;
	Table out_mfireflux_ch4;
	Table out_mfireflux_c_pft[npftconst];

	// MF Mortality
	Table out_monthly_nind_killed;
	Table out_mtreecover_reduction_fire;


	// MF: phenology, leaf shed and fine fuel
	Table out_mleafshed, out_aleafshed, out_mfinefuel;


	// Per-PFT, monthly (New Order, replaced above based in P. Antoni's GCP code)
	// Note the additional output layer for BareSoil
	Table out_monthly_burned_area_pft[npftconst+1];

	// Daily output

	// "real" daily values (averaged across all actual fires)
	Table out_daily_fires;
	Table out_daily_fuel_moisture;
	Table out_daily_flammability;


	// "diagnostic" daily values (averaged across flammable patches)
	Table out_daily_fires_diagnostics;
	Table out_daily_fuel_moisture_diagnostics;
	Table out_daily_flammability_diagnostics;



	int first_year_daily_output;
	int last_year_daily_output;


	// new annual variables for convenience and benchmarking with reduced file sizes
	Table out_annual_fuel_loads;

	void outlimit_daily_spitfire(OutputRows& out, const Table& table, double d);

};

}

#endif // LPJ_GUESS_SPITFIRE_OUTPUT_H
