///////////////////////////////////////////////////////////////////////////////////////
/// \file cropoutput.h
/// \brief Output module for the land use and management information
///
/// \author Joe Siltberg
/// $Date$
///
///////////////////////////////////////////////////////////////////////////////////////

#ifndef LPJ_GUESS_MISC_OUTPUT_H
#define LPJ_GUESS_MISC_OUTPUT_H

#include "outputmodule.h"
#include "outputchannel.h"
#include "gutil.h"
// [Step 8 of unified-codebase rebuild: removed unused <random> include that
//  was only used by the now-deleted getImogenData() dead helper. - DKB 2026-05-06]

namespace GuessOutput {

// Definitions for separate output files per NATURAL and FOREST stand (when
// instruction file parameter printseparatestands == true, printseparatestands
// is set to false in LandcoverInput::init() when input land cover
// fraction data file has data for > 50 gridcells)

/// Output module for the most commonly needed output files
class MiscOutput : public OutputModule {
public:

	MiscOutput();

	~MiscOutput();

	// implemented functions inherited from OutputModule
	// (see documentation in OutputModule)

	void init();

	void outannual(Gridcell& gridcell);

	void outdaily(Gridcell& gridcell);
    
    // SSR: GGCMI
    void outharvest(Gridcell& gridcell);
	void outharvest_justphupvd(Gridcell& gridcell);
	void outannual_ggcmi(Gridcell& gridcell);

private:

	/// Upper limit for files in multiple stand printout
	static const int MAXNUMBER_STANDS = 1000;
    
    /// Upper limit for files in multiple stand printout
    static const int MAXNUMBER_STANDS_GGCMI = 256;

	/// Printout of first stand from first historic year
	static const bool PRINTFIRSTSTANDFROM1901 = true;

	/// Defines all output tables
	void openlocalfiles(Gridcell& gridcell);

	void define_output_tables();

	void closelocalfiles(Gridcell& gridcell);
    
    /// SSR: GGCMI
    void openlocalfiles_ggcmi();
    void closelocalfiles_ggcmi();

	// [Step 8 of unified-codebase rebuild: removed dead helper getImogenData()
	//  that returned non-deterministic random placeholder values from
	//  uniform_real_distribution. It was defined but never called anywhere
	//  in the codebase, and is misleading semantically (a "data getter"
	//  that emits randomness). The half-scaffolded miscoutput IMOGEN
	//  diagnostic-output stubs (the 12 file_*_anom + Table out_*_anom
	//  declarations below this block and at lines 122-135 of miscoutput.cpp)
	//  are tracked separately as follow-up F-9 in notes/FOLLOWUPS.md;
	//  step 8 only owned the handshake-writer concern, implemented in
	//  the new lpjguess/modules/imogenoutput.cpp/h. - DKB 2026-05-06]

	// Output file names ...
	xtring file_yield, file_yield1, file_yield2, file_sdate1, file_sdate2,
		   file_hdate1, file_hdate2, file_lgp, file_phu, file_fphu, file_fhi,
		   file_irrigation, file_seasonality, file_cflux_cropland,
		   file_cflux_pasture, file_cflux_natural, file_cflux_forest,
		   file_cpool_cropland, file_cpool_pasture, file_cpool_natural,
		   file_cpool_forest, file_nflux_cropland, file_nflux_pasture,
		   file_nflux_natural, file_nflux_forest, file_npool_cropland,
		   file_npool_pasture, file_npool_natural, file_npool_forest,
		   file_anpp_cropland, file_anpp_pasture, file_anpp_natural,
		   file_anpp_forest, file_cmass_cropland, file_cmass_pasture,
		   file_cmass_natural, file_cmass_forest, file_dens_natural,
		   file_dens_forest, file_soil_nflux_cropland, file_soil_nflux_pasture,
		   file_soil_nflux_natural, file_soil_nflux_forest,
		   file_cmass_peatland, file_cflux_peatland,
		   file_cpool_peatland, file_nflux_peatland, file_npool_peatland,
		   file_anpp_peatland,
           file_gsirr, // SSR: Per-CFT irrigation water output
           // SSR: Outputs with year referring to year of planting and/or STAND instead of PFT
           file_yield_plantyear, file_yield_st, file_yield1_st, file_yield2_st, file_yield_plantyear_st,
           file_gsirr_st, file_gsirr_plantyear_st, file_anpp_pasture_st, file_anpp_crop_st, file_yield_pasture_st;
	xtring file_harvest_sts;//DKB: 07-28-2024 Stand level harvested biomass output

	// daily
	xtring file_daily_lai, file_daily_npp, file_daily_nmass, file_daily_cmass,
		   file_daily_cton, file_daily_ndemand, file_daily_cmass_leaf,
		   file_daily_nmass_leaf, file_daily_cmass_root, file_daily_nmass_root,
		   file_daily_cmass_stem, file_daily_nmass_stem,
		   file_daily_cmass_storage, file_daily_nmass_storage,
		   file_daily_n_input_soil, file_daily_avail_nmass_soil, 
		   file_daily_upper_wcont, file_daily_lower_wcont,
		   file_daily_irrigation, file_daily_climate,
		   file_daily_cmass_dead_leaf, file_daily_nmass_dead_leaf, 
		   file_daily_fphu, file_daily_nminleach,
		   file_daily_norgleach, file_daily_nuptake, file_daily_ds,
		   file_daily_stem, file_daily_leaf, file_daily_root,
		   file_daily_storage;

	//FireMIP BLAZE
	xtring file_dblaze_ba;

	//IMOGEN-RELATED FILES //DKB
	xtring file_t_anom, file_wet, file_sw_anom, file_p_anom, file_fa_ocean, file_dtemp_o, file_dtemp_anom, file_co2, file_relhum_anom, file_tmin_anom, file_tmax_anom, file_wind_anom;

	// Output tables
	Table out_yield, out_yield1, out_yield2, out_sdate1, out_sdate2,
		  out_hdate1, out_hdate2, out_lgp, out_phu, out_fhi, out_fphu,
		  out_irrigation, out_seasonality, out_cflux_cropland,
		  out_cflux_pasture, out_cflux_natural, out_cflux_forest,
		  out_cpool_cropland, out_cpool_pasture, out_cpool_natural,
		  out_cpool_forest, out_nflux_cropland, out_nflux_pasture,
		  out_nflux_natural, out_nflux_forest, out_npool_cropland,
		  out_npool_pasture, out_npool_natural, out_npool_forest,
		  out_anpp_cropland, out_anpp_pasture, out_anpp_natural,
		  out_anpp_forest, out_cmass_cropland, out_cmass_pasture,
		  out_cmass_natural, out_cmass_forest, out_dens_natural,
		  out_dens_forest, out_soil_nflux_cropland, out_soil_nflux_pasture,
		  out_soil_nflux_natural, out_soil_nflux_forest,
		  out_cflux_peatland, out_cpool_peatland,
		  out_nflux_peatland, out_npool_peatland, out_cmass_peatland,
		  out_anpp_peatland,
          out_gsirr, // SSR: Per-CFT irrigation water output
          // SSR: Outputs with year referring to year of planting
          out_yield_plantyear, out_yield_st, out_yield1_st, out_yield2_st, out_yield_plantyear_st,
          out_gsirr_st, out_gsirr_plantyear_st, out_anpp_pasture_st, out_anpp_crop_st, out_yield_pasture;
	Table out_harvest_sts; //DKB: 07-28-2024 Stand level harvest output

	Table* out_anpp_stand[MAXNUMBER_STANDS];
	Table* out_cmass_stand[MAXNUMBER_STANDS];
    
    // SSR: GGCMI
    Table out_misc_stand[MAXNUMBER_STANDS_GGCMI];
	Table out_phupvd_stand[MAXNUMBER_STANDS_GGCMI];
	Table out_rootmoistm_stand[12];

	//daily
	Table out_daily_lai, out_daily_npp, out_daily_cton, out_daily_nmass,
		  out_daily_cmass, out_daily_ndemand, out_daily_cmass_leaf,
		  out_daily_nmass_leaf, out_daily_cmass_root, out_daily_nmass_root,
		  out_daily_cmass_stem, out_daily_nmass_stem, out_daily_cmass_storage,
		  out_daily_nmass_storage, out_daily_n_input_soil,
		  out_daily_cmass_dead_leaf, out_daily_nmass_dead_leaf, out_daily_fphu,
		  out_daily_avail_nmass_soil, out_daily_upper_wcont,
		  out_daily_lower_wcont, out_daily_irrigation, out_daily_climate,
		  out_daily_nminleach, out_daily_norgleach, out_daily_nuptake, out_daily_ds, 
		  out_daily_stem, out_daily_leaf, out_daily_root, out_daily_storage;

	// FireMIP BLAZE
	Table out_dblaze_ba;

	//IMOGEN-RELATED FILES //DKB
	Table out_t_anom, out_wet, out_sw_anom, out_p_anom, out_fa_ocean, out_dtemp_o, out_dtemp_anom, out_co2, out_relhum_anom, out_tmin_anom, out_tmax_anom, out_wind_anom;
	
};

}

#endif // LPJ_GUESS_MISC_OUTPUT_H
