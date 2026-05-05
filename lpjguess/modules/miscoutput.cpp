///////////////////////////////////////////////////////////////////////////////////////
/// \file outputmodule.cpp
/// \brief Implementation of the common output module
///
/// \author Joe Siltberg
/// $Date: 2015-04-09 18:40:34 +0200 (Thu, 09 Apr 2015) $
///
///////////////////////////////////////////////////////////////////////////////////////

#include "config.h"
#include "miscoutput.h"
#include "parameters.h"
#include "guess.h"
#include<iostream>

namespace GuessOutput {

// Nitrogen output is in kgN/ha instead of kgC/m2 as for carbon

REGISTER_OUTPUT_MODULE("misc", MiscOutput)

MiscOutput::MiscOutput() {
	// Annual output variables
	declare_parameter("file_cmass_cropland", &file_cmass_cropland, 300, "Annual cropland cmass output file");
	declare_parameter("file_cmass_pasture", &file_cmass_pasture, 300, "Annual pasture cmass output file");
	declare_parameter("file_cmass_natural", &file_cmass_natural, 300, "Annual natural vegetation cmass output file");
	declare_parameter("file_cmass_forest", &file_cmass_forest, 300, "Annual managed forest cmass output file");
	declare_parameter("file_cmass_peatland", &file_cmass_peatland, 300, "Annual peatland cmass output file");
	declare_parameter("file_anpp_cropland", &file_anpp_cropland, 300, "Annual cropland NPP output file");
	declare_parameter("file_anpp_pasture", &file_anpp_pasture, 300, "Annual pasture NPP output file");
	declare_parameter("file_anpp_natural", &file_anpp_natural, 300, "Annual natural vegetation NPP output file");
	declare_parameter("file_anpp_forest", &file_anpp_forest, 300, "Annual managed forest NPP output file");
	declare_parameter("file_anpp_peatland", &file_anpp_peatland, 300, "Annual peatland NPP output file");
	declare_parameter("file_yield",&file_yield,300, "Crop yield output file");
	declare_parameter("file_yield1",&file_yield1,300,"Crop first yield output file");
	declare_parameter("file_yield2",&file_yield2,300,"Crop second yield output file");
	declare_parameter("file_sdate1",&file_sdate1,300,"Crop first sowing date output file");
	declare_parameter("file_sdate2",&file_sdate2,300,"Crop second sowing date output file");
	declare_parameter("file_hdate1",&file_hdate1,300,"Crop first harvest date output file");
	declare_parameter("file_hdate2",&file_hdate2,300,"Crop second harvest date output file");
	declare_parameter("file_lgp",&file_lgp,300,"Crop length of growing period output file");
	declare_parameter("file_phu",&file_phu,300,"Crop potential heat units output file");
	declare_parameter("file_fphu",&file_fphu,300,"Crop attained fraction of potential heat units output file");
	declare_parameter("file_fhi",&file_fhi,300,"Crop attained fraction of harvest index output file");
	declare_parameter("file_irrigation",&file_irrigation,300,"Crop irrigation output file");
	declare_parameter("file_seasonality",&file_seasonality,300,"Seasonality output file");
	declare_parameter("file_cflux_cropland", &file_cflux_cropland, 300, "C fluxes output file");
	declare_parameter("file_cflux_pasture", &file_cflux_pasture, 300, "C fluxes output file");
	declare_parameter("file_cflux_natural", &file_cflux_natural, 300, "C fluxes output file");
	declare_parameter("file_cflux_forest", &file_cflux_forest, 300, "C fluxes output file");
	declare_parameter("file_cflux_peatland", &file_cflux_peatland, 300, "C fluxes output file");
	declare_parameter("file_dens_natural", &file_dens_natural, 300, "Natural vegetation tree density output file");
	declare_parameter("file_dens_forest", &file_dens_forest, 300, "Managed forest tree density output file");
	declare_parameter("file_cpool_cropland", &file_cpool_cropland, 300, "Soil C output file");
	declare_parameter("file_cpool_pasture", &file_cpool_pasture, 300, "Soil C output file");
	declare_parameter("file_cpool_natural", &file_cpool_natural, 300, "Soil C output file");
	declare_parameter("file_cpool_forest", &file_cpool_forest, 300, "Soil C output file");
	declare_parameter("file_cpool_peatland", &file_cpool_peatland, 300, "Soil C output file");
	declare_parameter("file_nflux_cropland", &file_nflux_cropland, 300, "N fluxes output file");
	declare_parameter("file_nflux_pasture", &file_nflux_pasture, 300, "N fluxes output file");
	declare_parameter("file_nflux_natural", &file_nflux_natural, 300, "N fluxes output file");
	declare_parameter("file_nflux_forest", &file_nflux_forest, 300, "N fluxes output file");
	declare_parameter("file_nflux_peatland", &file_nflux_peatland, 300, "N fluxes output file");
	declare_parameter("file_npool_cropland", &file_npool_cropland, 300, "Soil N output file");
	declare_parameter("file_npool_pasture", &file_npool_pasture, 300, "Soil N output file");
	declare_parameter("file_npool_natural", &file_npool_natural, 300, "Soil N output file");
	declare_parameter("file_npool_forest", &file_npool_forest, 300, "Soil N output file");
	declare_parameter("file_npool_peatland", &file_npool_peatland, 300, "Soil N output file");
    declare_parameter("file_gsirr",&file_gsirr,300,"Per-CFT irrigation output file"); // SSR: Per-CFT irrigation water output
	declare_parameter("file_gsirr_st",&file_gsirr_st,300,"Per-stand irrigation output file"); // SSR
	declare_parameter("file_gsirr_plantyear_st",&file_gsirr_plantyear_st,300,"Per-stand irrigation output file (year = year of PLANTING, not harvest as in file_gsirr_st"); // SSR
	declare_parameter("file_yield_plantyear",&file_yield_plantyear,300, "Crop yield output file (year = year of PLANTING, not harvest as in file_yield"); // SSR
	declare_parameter("file_yield_st",&file_yield_st,300, "Per-stand crop yield output file"); // SSR
	declare_parameter("file_yield1_st",&file_yield1_st,300, "Per-stand crop yield (1st harvest) output file"); // SSR
	declare_parameter("file_yield2_st",&file_yield2_st,300, "Per-stand crop yield (2nd harvest) output file"); // SSR
	declare_parameter("file_yield_plantyear_st",&file_yield_plantyear_st,300, "Crop yield output file (year = year of PLANTING, not harvest as in file_yield, columns STANDS not pfts"); // SSR
	declare_parameter("file_anpp_pasture_st",&file_anpp_pasture_st,300, "ANPP outputs for pasture stands in response to N-fertilizer application levels (N_appfert_mt) in columns STANDS not pfts"); // DKB: 31.05.2023
	declare_parameter("file_anpp_crop_st",&file_anpp_crop_st,300, "ANPP outputs for crop stands in response to N-fertilizer application levels (N_appfert_mt) in columns STANDS not pfts"); // DKB: 04.07.2023
	declare_parameter("file_yield_pasture_st",&file_yield_pasture_st, 300, "PEr-stand pasture yield output file"); // DKB: 04.07.2023

	declare_parameter("file_soil_nflux_cropland", &file_soil_nflux_cropland, 300, "Soil N fluxes output file");
	declare_parameter("file_soil_nflux_pasture", &file_soil_nflux_pasture, 300, "Soil N fluxes output file");
	declare_parameter("file_soil_nflux_natural", &file_soil_nflux_natural, 300, "Soil N fluxes output file");
	declare_parameter("file_soil_nflux_forest", &file_soil_nflux_forest, 300, "Soil N fluxes output file");
	//daily
	declare_parameter("file_daily_lai",&file_daily_lai,300,"Daily output.");
	declare_parameter("file_daily_npp",&file_daily_npp,300,"Daily output.");
	declare_parameter("file_daily_nmass",&file_daily_nmass,300,"Daily output.");
	declare_parameter("file_daily_ndemand",&file_daily_ndemand,300,"Daily output.");
	declare_parameter("file_daily_cmass",&file_daily_cmass,300,"Daily output.");
	declare_parameter("file_daily_cton",&file_daily_cton,300,"Daily output.");
	declare_parameter("file_daily_cmass_leaf",&file_daily_cmass_leaf,300,"Daily output.");
	declare_parameter("file_daily_nmass_leaf",&file_daily_nmass_leaf,300,"Daily output.");
	declare_parameter("file_daily_cmass_root",&file_daily_cmass_root,300,"Daily output.");
	declare_parameter("file_daily_nmass_root",&file_daily_nmass_root,300,"Daily output.");
	declare_parameter("file_daily_cmass_stem",&file_daily_cmass_stem,300,"Daily output.");
	declare_parameter("file_daily_nmass_stem",&file_daily_nmass_stem,300,"Daily output.");
	declare_parameter("file_daily_cmass_storage",&file_daily_cmass_storage,300,"Daily output.");
	declare_parameter("file_daily_nmass_storage",&file_daily_nmass_storage,300,"Daily output.");

	declare_parameter("file_daily_cmass_dead_leaf",&file_daily_cmass_dead_leaf,300,"Daily output.");
	declare_parameter("file_daily_nmass_dead_leaf",&file_daily_nmass_dead_leaf,300,"Daily output.");

	declare_parameter("file_daily_n_input_soil",&file_daily_n_input_soil,300,"Daily output.");
	declare_parameter("file_daily_avail_nmass_soil",&file_daily_avail_nmass_soil,300,"Daily output.");
	declare_parameter("file_daily_upper_wcont",&file_daily_upper_wcont,300,"Daily output.");
	declare_parameter("file_daily_lower_wcont",&file_daily_lower_wcont,300,"Daily output.");
	declare_parameter("file_daily_irrigation",&file_daily_irrigation,300,"Daily output.");

	declare_parameter("file_daily_nminleach",&file_daily_nminleach,300,"Daily output.");
	declare_parameter("file_daily_norgleach",&file_daily_norgleach,300,"Daily output.");
	declare_parameter("file_daily_nuptake",&file_daily_nuptake,300,"Daily output.");

	declare_parameter("file_daily_climate",&file_daily_climate,300,"Daily output.");

	declare_parameter("file_daily_fphu",&file_daily_fphu,300,"Daily DS output file"); //daglig ds
	declare_parameter("file_harvest_sts", &file_harvest_sts, 300, "stand level harvest output"); //DKB: 07-28-2024 Stand level harvested biomass output

	/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	//IMOGEN-RELATED FILES
	//std::cout << "print_imogen_output" << IMOGENConfig::print_imogen_output << std::endl;
	if (IMOGENConfig::print_imogen_output==true) { //use an input model based chek here: FIXME: DKB
		declare_parameter("file_t_anom", &file_t_anom, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_wet", &file_wet, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_sw_anom", &file_sw_anom, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_p_anom", &file_p_anom, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_fa_ocean", &file_fa_ocean, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_dtemp_o", &file_dtemp_o, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_dtemp_anom", &file_dtemp_anom, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_co2", &file_co2, 300, "Imogen Temperature Anomalies.");
		declare_parameter("file_relhum_anom", &file_relhum_anom, 300, "Imogen Relative Humidity Anomalies.");
		declare_parameter("file_tmin_anom", &file_tmin_anom, 300, "Imogen Minimum Temperature Anomalies.");
		declare_parameter("file_tmax_anom", &file_tmax_anom, 300, "Imogen Maximum Temperature Anomalies.");
		declare_parameter("file_wind_anom", &file_wind_anom, 300, "Imogen Wind Anomalies.");
	}
	///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

	if (ifnlim) {
		declare_parameter("file_daily_ds",&file_daily_ds,300,"Daily DS output file"); //daglig ds
		declare_parameter("file_daily_stem",&file_daily_stem,300,"Daily stem allocation output file");
		declare_parameter("file_daily_leaf",&file_daily_leaf,300,"Daily leaf allocation output file");
		declare_parameter("file_daily_root",&file_daily_root,300,"Daily root allocation output file");
		declare_parameter("file_daily_storage",&file_daily_storage,300,"Daily storage allocation output file");
	}

    if (firemodel==BLAZE) {
        declare_parameter("file_dblaze_ba", &file_dblaze_ba,300,"Daily BLAZE burned area");
    }

}

MiscOutput::~MiscOutput() {
}

/// Define all output tables and their formats
void MiscOutput::init() {
	
	define_output_tables();
}

/// Specify all columns in all output tables
/** This function specifies all columns in all output tables, their names,
 *  column widths and precision.
 *
 *  For each table a TableDescriptor object is created which is then sent to
 *  the output channel to create the table.
 */
void MiscOutput::define_output_tables() {
	
	if (just_phu_pvd) {
		return;
	}
	
	// create a vector with the pft names
	std::vector<std::string> pfts;

	// create a vector with the crop pft names
	std::vector<std::string> crop_pfts;

	pftlist.firstobj();
	while (pftlist.isobj) {
		Pft& pft=pftlist.getobj();

		pfts.push_back((char*)pft.name);

		if (pft.landcover==CROPLAND)
			crop_pfts.push_back((char*)pft.name);

		pftlist.nextobj();
	}
	
	// SSR: create a vector with the crop pft names
	std::vector<std::string> crop_sts;
	stlist.firstobj();
	while (stlist.isobj) {
		StandType& st=stlist.getobj();

		if (st.landcover==CROPLAND) {
			crop_sts.push_back((char*)st.name);
		}

		stlist.nextobj();
	}

	//DKB: 31.05.2023: Create vector to hold the stand names
	int counter=0;
	std::vector<std::string>pasture_sts;
	stlist.firstobj();
	while(stlist.isobj){
		StandType& st = stlist.getobj();

		//dprintf("The stand name for all stands loop is: %s\n",(char*)st.name);

		if(st.landcover==PASTURE){
			pasture_sts.push_back((char*)st.name);

			//pasture stand push into vector
			//debug print name of stand
			//dprintf("The pasture stand is: %s\n",(char*)st.name);

		}
		stlist.nextobj();
		//dprintf("Stand loop evaluated\n");
		//++counter;	
	}
	//dprintf("The number of stands is: %d\n",counter);

	// create a vector with the landcover column titles
	std::vector<std::string> landcovers;

	const char* landcover_string[]={"Urban_sum", "Crop_sum", "Pasture_sum",
			"Forest_sum", "Natural_sum", "Peatland_sum", "Barren_sum"};
	for (int i=0; i<NLANDCOVERTYPES; i++) {
		if (run[i]) {
			landcovers.push_back(landcover_string[i]);
		}
	}

	// Create the month columns
	ColumnDescriptors month_columns;
	ColumnDescriptors month_columns_wide;
	xtring months[] = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};
	for (int i = 0; i < 12; i++) {
		month_columns      += ColumnDescriptor(months[i], 8,  3);
		month_columns_wide += ColumnDescriptor(months[i], 10, 3);
	}

	// Create the columns for each output file

	// CMASS
	ColumnDescriptors cmass_columns;
	cmass_columns += ColumnDescriptors(pfts,               8, 3);
	cmass_columns += ColumnDescriptor("Total",             8, 3);
	ColumnDescriptors cmass_columns_lc = cmass_columns;
	cmass_columns += ColumnDescriptors(landcovers,        13, 3);

	// ANPP
	ColumnDescriptors anpp_columns = cmass_columns;
	ColumnDescriptors anpp_columns_lc = cmass_columns_lc;

	// DENS
	ColumnDescriptors dens_columns;
	dens_columns += ColumnDescriptors(pfts,                8, 4);
	dens_columns += ColumnDescriptor("Total",              8, 4);
	ColumnDescriptors dens_columns_lc = dens_columns;

	// CFLUX
	ColumnDescriptors cflux_columns;
	cflux_columns += ColumnDescriptor("Veg",               8, 3);
	cflux_columns += ColumnDescriptor("Repr",              8, 3);
	cflux_columns += ColumnDescriptor("Soil",              8, 3);
	cflux_columns += ColumnDescriptor("Fire",              8, 3);
	cflux_columns += ColumnDescriptor("Est",               8, 3);
	cflux_columns += ColumnDescriptor("Seed",         8, 3);
	cflux_columns += ColumnDescriptor("Harvest",      9, 3);
	cflux_columns += ColumnDescriptor("LU_ch",        9, 3);
	cflux_columns += ColumnDescriptor("Slow_h",       9, 3);
	cflux_columns += ColumnDescriptor("NEE",              10, 5);

	// CPOOL
	ColumnDescriptors cpool_columns;
	cpool_columns += ColumnDescriptor("VegC",              8, 3);

	if (!ifcentury) {
		cpool_columns += ColumnDescriptor("LittC",         8, 3);
		cpool_columns += ColumnDescriptor("SoilfC",        8, 3);
		cpool_columns += ColumnDescriptor("SoilsC",        8, 3);
	}
	else {
		cpool_columns += ColumnDescriptor("LitterC",       8, 3);
		cpool_columns += ColumnDescriptor("SoilC",         8, 3);
	}
	if (run_landcover && ifslowharvestpool) {
		 cpool_columns += ColumnDescriptor("HarvSlowC",   10, 3);
	}
	cpool_columns += ColumnDescriptor("Total",            10, 3);

	//CROP YIELD
	ColumnDescriptors crop_columns;
	crop_columns += ColumnDescriptors(crop_pfts,           8, 3);
	
	// SSR: Crop stuff by stand
	ColumnDescriptors crop_columns_st;
	crop_columns_st += ColumnDescriptors(crop_sts,           8, 3);

	//DKB Pasture stand outputs
	ColumnDescriptors pasture_columns_st;
	pasture_columns_st += ColumnDescriptors(pasture_sts,           8, 3);
	
	// SSR: Crop stuff by stand (wide)
	ColumnDescriptors crop_columns_st_wide;
	crop_columns_st_wide += ColumnDescriptors(crop_sts,           10, 3);
    
    //CROP STUFF (WIDE)
    ColumnDescriptors crop_columns_wide;
    crop_columns_wide += ColumnDescriptors(crop_pfts,           10, 3);

	//CROP SDATE & HDATE
	ColumnDescriptors date_columns;
	date_columns += ColumnDescriptors(crop_pfts,           8, 0);

	//IRRIGATION
	ColumnDescriptors irrigation_columns;
	irrigation_columns += ColumnDescriptor("Total",       10, 3);

	//SEASONALITY
	ColumnDescriptors seasonality_columns;
	seasonality_columns += ColumnDescriptor("Seasonal",   10, 0);
	seasonality_columns += ColumnDescriptor("V_temp",     10, 3);
	seasonality_columns += ColumnDescriptor("V_prec",     10, 3);
	seasonality_columns += ColumnDescriptor("temp_min",   10, 1);  
	seasonality_columns += ColumnDescriptor("temp_mean",  10, 1);
	seasonality_columns += ColumnDescriptor("temp_max",   10, 1);
	seasonality_columns += ColumnDescriptor("mtemp_max",  10, 1);
	seasonality_columns += ColumnDescriptor("temp_seas",  10, 0);
	seasonality_columns += ColumnDescriptor("gdd0",       10, 0);
	seasonality_columns += ColumnDescriptor("gdd5",       10, 0);
	seasonality_columns += ColumnDescriptor("prec_min",   10, 2);
	seasonality_columns += ColumnDescriptor("prec",       10, 1);
	seasonality_columns += ColumnDescriptor("prec_range", 12, 0);

	// NPOOL
	ColumnDescriptors npool_columns;
	npool_columns += ColumnDescriptor("VegN",              9, 4);
	npool_columns += ColumnDescriptor("LitterN",           9, 4);
	npool_columns += ColumnDescriptor("SoilN",             9, 4);

	if (run_landcover && ifslowharvestpool) {
		npool_columns += ColumnDescriptor("HarvSlowN",    10, 4);
	}

	npool_columns += ColumnDescriptor("Total",            10, 4);

	ColumnDescriptors daily_ba_columns;
	daily_ba_columns += ColumnDescriptor("Burnfr",        10, 6);

	// NFLUX
	ColumnDescriptors nflux_columns;
	nflux_columns += ColumnDescriptor("dep",               8, 2);
	nflux_columns += ColumnDescriptor("fix",               8, 2);
	nflux_columns += ColumnDescriptor("fert",              8, 2);
	nflux_columns += ColumnDescriptor("flux",              8, 2);
	nflux_columns += ColumnDescriptor("leach",             8, 2);
	if (run_landcover) {
		nflux_columns += ColumnDescriptor("seed",         8, 2);
		nflux_columns += ColumnDescriptor("harvest",       8, 2);
		nflux_columns += ColumnDescriptor("LU_ch",         8, 3);
		nflux_columns += ColumnDescriptor("Slow_h",        8, 3);
	}
	nflux_columns += ColumnDescriptor("NEE",               8, 2);
	// SOIL N TRANSFORMATION - fluxes
	ColumnDescriptors soil_nflux_columns;
	soil_nflux_columns += ColumnDescriptor("NH3",  12, 6);
	soil_nflux_columns += ColumnDescriptor("NO",    9, 3);
	soil_nflux_columns += ColumnDescriptor("N2O",  12, 6);
	soil_nflux_columns += ColumnDescriptor("N2",    9, 3);

	ColumnDescriptors daily_climate_columns;
	daily_climate_columns += ColumnDescriptor("Temp",   12, 6);
	daily_climate_columns += ColumnDescriptor("Prec",   12, 6);
	daily_climate_columns += ColumnDescriptor("Rad",    14, 3);

	ColumnDescriptors daily_columns;
	daily_columns += ColumnDescriptors(crop_pfts, 13, 3);

	// *** ANNUAL OUTPUT VARIABLES ***

	create_output_table(out_cmass_cropland, file_cmass_cropland, cmass_columns_lc);
	create_output_table(out_cmass_pasture,  file_cmass_pasture,  cmass_columns_lc);
	create_output_table(out_cmass_natural,  file_cmass_natural,  cmass_columns_lc);
	create_output_table(out_cmass_forest,   file_cmass_forest,   cmass_columns_lc);
	create_output_table(out_cmass_peatland,	file_cmass_peatland, cmass_columns_lc);
	create_output_table(out_anpp_cropland,  file_anpp_cropland,  anpp_columns_lc);
	create_output_table(out_anpp_pasture,   file_anpp_pasture,   anpp_columns_lc);
	create_output_table(out_anpp_natural,   file_anpp_natural,   anpp_columns_lc);
	create_output_table(out_anpp_forest,    file_anpp_forest,    anpp_columns_lc);
	create_output_table(out_anpp_peatland, file_anpp_peatland, anpp_columns_lc);
	create_output_table(out_dens_natural,   file_dens_natural,   dens_columns_lc);
	create_output_table(out_dens_forest,    file_dens_forest,    dens_columns_lc);
	create_output_table(out_cflux_cropland, file_cflux_cropland, cflux_columns);
	create_output_table(out_cflux_pasture,  file_cflux_pasture,  cflux_columns);
	create_output_table(out_cflux_natural,  file_cflux_natural,  cflux_columns);
	create_output_table(out_cflux_forest,	file_cflux_forest,   cflux_columns);
	create_output_table(out_cflux_peatland, file_cflux_peatland, cflux_columns);
	create_output_table(out_cpool_cropland, file_cpool_cropland, cpool_columns);
	create_output_table(out_cpool_pasture,  file_cpool_pasture,  cpool_columns);
	create_output_table(out_cpool_natural,  file_cpool_natural,  cpool_columns);
	create_output_table(out_cpool_forest,	file_cpool_forest,   cpool_columns);
	create_output_table(out_cpool_peatland, file_cpool_peatland, cpool_columns);

	if (run_landcover && run[CROPLAND]) {
		create_output_table(out_yield,      file_yield,          crop_columns);
		create_output_table(out_yield1,     file_yield1,         crop_columns);
		create_output_table(out_yield2,     file_yield2,         crop_columns);
		create_output_table(out_sdate1,     file_sdate1,         date_columns);
		create_output_table(out_sdate2,     file_sdate2,         date_columns);
		create_output_table(out_hdate1,     file_hdate1,         date_columns);
		create_output_table(out_hdate2,     file_hdate2,         date_columns);
		create_output_table(out_lgp,        file_lgp,            date_columns);
		create_output_table(out_phu,        file_phu,            date_columns);
		create_output_table(out_fphu,       file_fphu,           crop_columns);
		create_output_table(out_fhi,        file_fhi,            crop_columns);
        create_output_table(out_gsirr,      file_gsirr,          crop_columns_wide); // SSR: Per-CFT irrigation water output
		create_output_table(out_gsirr_st,   file_gsirr_st,       crop_columns_st_wide); // SSR
		create_output_table(out_gsirr_plantyear_st, file_gsirr_plantyear_st, crop_columns_st_wide); // SSR
		create_output_table(out_yield_plantyear, file_yield_plantyear, crop_columns);
		create_output_table(out_yield_st, file_yield_st, crop_columns_st);
		create_output_table(out_yield1_st, file_yield1_st, crop_columns_st);
		create_output_table(out_yield2_st, file_yield2_st, crop_columns_st);
		create_output_table(out_yield_plantyear_st, file_yield_plantyear_st, crop_columns_st);

		//DKB: File for printing out anpp for crop stands: Create variable 
		create_output_table(out_anpp_crop_st, file_anpp_crop_st, crop_columns_st);
	}

	//DKB: Create pasture stand outpt table
	if(run_landcover && run[PASTURE]){
		create_output_table(out_anpp_pasture_st, file_anpp_pasture_st, pasture_columns_st);
		create_output_table(out_yield_pasture, file_yield_pasture_st, pasture_columns_st);
		create_output_table(out_harvest_sts, file_harvest_sts, pasture_columns_st);//DKB: 07-28-2024 Stand level harvested biomass output 
	}

        create_output_table(out_seasonality,file_seasonality,    seasonality_columns);

	if(run_landcover)
		create_output_table(out_irrigation, file_irrigation,     irrigation_columns); 

	create_output_table(out_npool_cropland, file_npool_cropland, npool_columns);
	create_output_table(out_npool_pasture,  file_npool_pasture,  npool_columns);
	create_output_table(out_npool_natural,  file_npool_natural,  npool_columns);
	create_output_table(out_npool_forest,	file_npool_forest,   npool_columns);
	create_output_table(out_npool_peatland, file_npool_peatland, npool_columns);
	create_output_table(out_nflux_cropland, file_nflux_cropland, nflux_columns);
	create_output_table(out_nflux_pasture,  file_nflux_pasture,  nflux_columns);
	create_output_table(out_nflux_natural,  file_nflux_natural,  nflux_columns);
	create_output_table(out_nflux_forest,	file_nflux_forest,   nflux_columns);
	create_output_table(out_nflux_peatland, file_nflux_peatland, nflux_columns);
	create_output_table(out_soil_nflux_cropland, file_soil_nflux_cropland, soil_nflux_columns);
	create_output_table(out_soil_nflux_pasture,  file_soil_nflux_pasture,  soil_nflux_columns);
	create_output_table(out_soil_nflux_natural,  file_soil_nflux_natural,  soil_nflux_columns);
	create_output_table(out_soil_nflux_forest,	file_soil_nflux_forest,   soil_nflux_columns);
	// TODO		create_output_table(out_nflux_peatland, file_nflux_peatland, nflux_columns);

	//FireMIP
	create_output_table(out_dblaze_ba, file_dblaze_ba, daily_ba_columns);

	// *** DAILY OUTPUT VARIABLES ***

	create_output_table(out_daily_lai,					file_daily_lai,					daily_columns);
	create_output_table(out_daily_npp,					file_daily_npp,					daily_columns);
	create_output_table(out_daily_ndemand,				file_daily_ndemand,				daily_columns);
	create_output_table(out_daily_nmass,				file_daily_nmass,				daily_columns);
	create_output_table(out_daily_cmass,				file_daily_cmass,				daily_columns);
	create_output_table(out_daily_nmass_leaf,			file_daily_nmass_leaf,			daily_columns);
	create_output_table(out_daily_cmass_leaf,			file_daily_cmass_leaf,			daily_columns);
	create_output_table(out_daily_nmass_root,			file_daily_nmass_root,			daily_columns);
	create_output_table(out_daily_cmass_root,			file_daily_cmass_root,			daily_columns);
	create_output_table(out_daily_nmass_stem,			file_daily_nmass_stem,			daily_columns);
	create_output_table(out_daily_cmass_stem,			file_daily_cmass_stem,			daily_columns);
	create_output_table(out_daily_nmass_storage,        file_daily_nmass_storage,       daily_columns);
	create_output_table(out_daily_cmass_storage,        file_daily_cmass_storage,       daily_columns);
	create_output_table(out_daily_nmass_dead_leaf,      file_daily_nmass_dead_leaf,     daily_columns);
	create_output_table(out_daily_cmass_dead_leaf,      file_daily_cmass_dead_leaf,     daily_columns);
	create_output_table(out_daily_n_input_soil,         file_daily_n_input_soil,        daily_columns);
	create_output_table(out_daily_avail_nmass_soil,     file_daily_avail_nmass_soil,    daily_columns);

	create_output_table(out_daily_upper_wcont,			file_daily_upper_wcont,         daily_columns);
	create_output_table(out_daily_lower_wcont,			file_daily_lower_wcont,         daily_columns);
	create_output_table(out_daily_irrigation,			file_daily_irrigation,			daily_columns);

	create_output_table(out_daily_climate,					file_daily_climate,					daily_climate_columns);

	create_output_table(out_daily_cton,					file_daily_cton,				daily_columns);

	create_output_table(out_daily_nminleach,			file_daily_nminleach,			daily_columns);
	create_output_table(out_daily_norgleach,			file_daily_norgleach,			daily_columns);
	create_output_table(out_daily_nuptake,				file_daily_nuptake,				daily_columns);

	if (ifnlim) {
		create_output_table(out_daily_ds,				file_daily_ds,					daily_columns);
		create_output_table(out_daily_fphu,				file_daily_fphu,				daily_columns);
		create_output_table(out_daily_stem,				file_daily_stem,				daily_columns);
		create_output_table(out_daily_leaf,				file_daily_leaf,				daily_columns);
		create_output_table(out_daily_root,				file_daily_root,				daily_columns);
		create_output_table(out_daily_storage,			file_daily_storage,				daily_columns);
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
void outlimit_misc(OutputRows& out, const Table& table, double d, int year_offset = 0) {

	if (date.write_outputs(year_offset))
		out.add_value(table, d);
}

/// Output of simulation results at the end of each year
/** Output of simulation results at the end of each year, or for specific years in
  * the simulation of each stand or grid cell. 
  * This function does not have to provide any information to the framework.
  *
  * Restrict output to specific years in the local helper function outlimit_misc().
  *
  * Changes in the structure of CommonOutput::outannual() should be mirrored here.
  */
void MiscOutput::outannual(Gridcell& gridcell) {

	if (just_phu_pvd) {
		return;
	}

	double lon = gridcell.get_lon();
	double lat = gridcell.get_lat();

	Landcover& lc = gridcell.landcover;
	// The OutputRows object manages the next row of output for each
	// output table
	OutputRows out(output_channel, lon, lat, date.get_calendar_year());
	// SSR
	OutputRows out_lastyear(output_channel, lon, lat, date.get_calendar_year()-1);

	double landcover_cmass[NLANDCOVERTYPES]={0.0};
	double landcover_nmass[NLANDCOVERTYPES]={0.0};
	double landcover_clitter[NLANDCOVERTYPES]={0.0};
	double landcover_nlitter[NLANDCOVERTYPES]={0.0};
	double landcover_anpp[NLANDCOVERTYPES]={0.0};
	double landcover_densindiv_total[NLANDCOVERTYPES]={0.0};

	double mean_standpft_anpp_lc[NLANDCOVERTYPES]={0.0};
	double mean_standpft_cmass_lc[NLANDCOVERTYPES]={0.0};
	double mean_standpft_densindiv_total_lc[NLANDCOVERTYPES]={0.0};

	double irrigation_gridcell=0.0;
    double standpft_gsirr=0.0; // SSR: Per-CFT irrigation water output

	double standpft_cmass=0.0;
	double standpft_nmass=0.0;
	double standpft_clitter=0.0;
	double standpft_nlitter=0.0;
	double standpft_anpp=0.0;
	double standpft_yield=0.0;
	double standpft_yield_lastyear=0.0; // SSR
	double standpft_yield1=0.0;
	double standpft_yield2=0.0;
	double standpft_densindiv_total=0.0;
	
	// SSR
	// Loop through all stand types
	stlist.firstobj();
	while (stlist.isobj) {

		// Get this StandType
		StandType& st=stlist.getobj();
		if (st.landcover!=CROPLAND) {
			stlist.nextobj();
			continue;
		}

		double yield_st_lastyear = -1.0;
		double yield_st = 0.0;
		double yield1_st = 0.0;
		double yield2_st = 0.0;
		double gsirr_st_lastyear = -1.0;
		double gsirr_st = 0.0;
		double anpp_crop_st = 0.0; //DKB: Get anpp for crop stands here
		
		// Loop through Stands in this gridcell, looking for one of this StandType
		Gridcell::iterator gc_itr = gridcell.begin();
		while (gc_itr != gridcell.end()) {
			Stand& stand = *gc_itr;
			// If Stand of this StandType is found, save its yield to yield_st (converting to dry matter with factor 1/0.446).
			if (stand.stid == st.id) {
				stand.firstobj();
				
				// Don't need to loop through patches because crop stand should only have 1
				Patch& patch = stand.getobj();

				//DKB: Get anpp for crop stands here
					anpp_crop_st += patch.fluxes.get_annual_flux(Fluxes::NPP);
				
				// Get yield for harvest of crop planted last year
				Patchpft& patchpft = patch.pft[stand.pftid];
				yield_st_lastyear = patchpft.cmass_ho_harvest_lastyear;
				if (yield_st_lastyear > 0) {
					yield_st_lastyear /= 0.446;
				}
				
				// Get yield across all harvests that occurred this year
				Vegetation& vegetation = patch.vegetation;
				vegetation.firstobj();
				while (vegetation.isobj) {
					Individual& indiv=vegetation.getobj();
					if (indiv.id!=-1 && indiv.alive && indiv.pft.id==stand.pftid) {
						yield_st += indiv.cropindiv->harv_yield;
						yield1_st += indiv.cropindiv->yield_harvest[0];
						yield2_st += indiv.cropindiv->yield_harvest[1];
					}
					vegetation.nextobj();
				}
				
				// Get irrigation applied on crop planted last year
				gsirr_st_lastyear = patch.grs_w_irr_lastyear;
				
				// Get total irrigation applied this year (regardless of which growing season)
				gsirr_st = patch.irrigation_y;
				/*dprintf("Gsirr is: %f\n", gsirr_st);
				system("pause");*/
				
				break;
			}
			++gc_itr;
		}
		// Save last year's values
		outlimit_misc(out_lastyear, out_yield_plantyear_st, yield_st_lastyear, -1);
		outlimit_misc(out_lastyear, out_gsirr_plantyear_st, gsirr_st_lastyear, -1);
		// Save this year's values
		outlimit_misc(out, out_yield_st, yield_st);
		outlimit_misc(out, out_yield1_st, yield1_st);
		outlimit_misc(out, out_yield2_st, yield2_st);
		outlimit_misc(out, out_gsirr_st, gsirr_st);

		//DKB: Print out anpp values for crop stands here
		outlimit_misc(out, out_anpp_crop_st, anpp_crop_st);


		stlist.nextobj();
	}

		////DKB: 01.06.2023
		//New print out routine, pasture anpp
		stlist.firstobj();
		while (stlist.isobj) {

			// Get this StandType. If it's not pasture, skip loop
			StandType& st = stlist.getobj();
			if (st.landcover != PASTURE) {
				stlist.nextobj();
				continue;
			}

			double pasture_anpp = 0.0;
			double st_harvest = 0.0;
			Gridcell::iterator gc_itr_m = gridcell.begin();
			while (gc_itr_m != gridcell.end()) {
				Stand& stand = *gc_itr_m;

				if (stand.stid == st.id) {

					stand.firstobj();
					while (stand.isobj) {
						Patch& patch = stand.getobj();

						pasture_anpp += patch.fluxes.get_annual_flux(Fluxes::NPP);
						st_harvest += patch.fluxes.get_annual_flux(Fluxes::HARVESTC);
						stand.nextobj();
					}
					
				}

				++gc_itr_m;

			}
			outlimit_misc(out, out_anpp_pasture_st, pasture_anpp);
			outlimit_misc(out, out_harvest_sts, st_harvest);//DKB:07-28-2024
			pasture_anpp = 0.0;
			stlist.nextobj();
		}

	
	pftlist.firstobj();
	while (pftlist.isobj) {

		Pft& pft=pftlist.getobj();

		// Sum values across stands, patches and PFTs
		double mean_standpft_yield=0.0;
		double mean_standpft_yield1=0.0;
		double mean_standpft_yield2=0.0;
        double mean_standpft_gsirr=0.0; // SSR: Per-CFT irrigation water output
		double mean_standpft_yield_lastyear=0.0; // SSR

		for (int i=0; i<NLANDCOVERTYPES; i++) {
			mean_standpft_anpp_lc[i]=0.0;
			mean_standpft_cmass_lc[i]=0.0;
			mean_standpft_densindiv_total_lc[i]=0.0;
		}

		// Determine area fraction of stands where this pft is active:
		double active_fraction = 0.0;
		double active_fraction_lc[NLANDCOVERTYPES]={0.0};

		Gridcell::iterator gc_itr = gridcell.begin();

		while (gc_itr != gridcell.end()) {
			Stand& stand = *gc_itr;

			if (stand.pft[pft.id].active) {
				active_fraction += stand.get_gridcell_fraction();
				active_fraction_lc[stand.landcover] += stand.get_gridcell_fraction();
			}

			++gc_itr;
		}

		// Loop through Stands
		gc_itr = gridcell.begin();

		while (gc_itr != gridcell.end()) {
			Stand& stand = *gc_itr;

			Standpft& standpft=stand.pft[pft.id];
			if (!standpft.active) {
				++gc_itr;
				continue;
			}
			// Sum values across patches and PFTs
			standpft_cmass=0.0;
			standpft_nmass=0.0;
			standpft_clitter=0.0;
			standpft_nlitter=0.0;
			standpft_anpp=0.0;
			standpft_yield=0.0;
			standpft_yield1=0.0;
			standpft_yield2=0.0;
            standpft_gsirr=0.0; // SSR: Per-CFT irrigation water output
			standpft_yield_lastyear=0.0;
			standpft_densindiv_total = 0.0;

			stand.firstobj();

			// Loop through Patches
			while (stand.isobj) {
				Patch& patch = stand.getobj();
				Patchpft& patchpft = patch.pft[pft.id];
				Vegetation& vegetation = patch.vegetation;

				standpft_anpp += patch.fluxes.get_annual_flux(Fluxes::NPP, pft.id);

				standpft_clitter += patchpft.cmass_litter_leaf + patchpft.cmass_litter_root + patchpft.cmass_litter_sap + patchpft.cmass_litter_heart + patchpft.cmass_litter_repr;
				standpft_nlitter += patchpft.nmass_litter_leaf + patchpft.nmass_litter_root + patchpft.nmass_litter_sap + patchpft.nmass_litter_heart;
                
                standpft_gsirr += patch.irrigation_y; // SSR: Per-CFT irrigation water output

				vegetation.firstobj();
				while (vegetation.isobj) {
					Individual& indiv=vegetation.getobj();

					if (indiv.id!=-1 && indiv.alive && indiv.pft.id==pft.id) {

						standpft_cmass += indiv.ccont();
						standpft_nmass += indiv.ncont();

						if (pft.landcover == CROPLAND) {
							standpft_yield += indiv.cropindiv->harv_yield;
							standpft_yield_lastyear += patchpft.cmass_ho_harvest_lastyear; // SSR
							standpft_yield1 += indiv.cropindiv->yield_harvest[0];
							standpft_yield2 += indiv.cropindiv->yield_harvest[1];
						}
						else {

							if (vegmode==COHORT || vegmode==INDIVIDUAL) {
								if (pft.lifeform==TREE) {
									double diam=pow(indiv.height/indiv.pft.k_allom2,1.0/indiv.pft.k_allom3);
									standpft_densindiv_total+=indiv.densindiv; // indiv/m2
								}
							}
						}
					}
					vegetation.nextobj();
				}

				stand.nextobj();
			} // end of patch loop

			standpft_cmass/=(double)stand.npatch();
			standpft_nmass/=(double)stand.npatch();
			standpft_clitter/=(double)stand.npatch();
			standpft_nlitter/=(double)stand.npatch();
			standpft_anpp/=(double)stand.npatch();
			standpft_densindiv_total/=(double)stand.npatch();
			standpft_yield/=(double)stand.npatch();
			standpft_yield_lastyear/=(double)stand.npatch(); // SSR
			standpft_yield1/=(double)stand.npatch();
			standpft_yield2/=(double)stand.npatch();

			//Update landcover totals
			landcover_cmass[stand.landcover]+=standpft_cmass*stand.get_landcover_fraction();
			landcover_nmass[stand.landcover]+=standpft_nmass*stand.get_landcover_fraction();
			landcover_clitter[stand.landcover]+=standpft_clitter*stand.get_landcover_fraction();
			landcover_nlitter[stand.landcover]+=standpft_nlitter*stand.get_landcover_fraction();
			landcover_anpp[stand.landcover]+=standpft_anpp*stand.get_landcover_fraction();
			landcover_densindiv_total[stand.landcover]+=standpft_densindiv_total*stand.get_landcover_fraction();

			if(active_fraction) {
			//Update pft means for active stands
			mean_standpft_yield += standpft_yield * stand.get_gridcell_fraction() / active_fraction;
			mean_standpft_yield1 += standpft_yield1 * stand.get_gridcell_fraction() / active_fraction;
			mean_standpft_yield2 += standpft_yield2 * stand.get_gridcell_fraction() / active_fraction;
            mean_standpft_gsirr += standpft_gsirr * stand.get_gridcell_fraction() / active_fraction; // SSR: Per-CFT irrigation water output
			mean_standpft_yield_lastyear += standpft_yield_lastyear * stand.get_gridcell_fraction() / active_fraction; // SSR

			//Update pft mean for active stands in landcover
			mean_standpft_anpp_lc[stand.landcover] += standpft_anpp * stand.get_gridcell_fraction() / active_fraction_lc[stand.landcover];
			mean_standpft_cmass_lc[stand.landcover] += standpft_cmass * stand.get_gridcell_fraction() / active_fraction_lc[stand.landcover];
			mean_standpft_densindiv_total_lc[stand.landcover] += standpft_densindiv_total * stand.get_gridcell_fraction() / active_fraction_lc[stand.landcover];
			}

			//Update stand totals
			stand.anpp += standpft_anpp;
			stand.cmass += standpft_cmass;

			// Print per-stand pft values
			if (printseparatestands) {

				int id = stand.id;
				if(stand.id >= MAXNUMBER_STANDS)
					fail("Number of stands to high, increase MAXNUMBER_STANDS for output of individual stands !\n");

				if(!out_anpp_stand[id][stand.stid].invalid())
					out.add_value(out_anpp_stand[id][stand.stid],      standpft_anpp);
				if(!out_cmass_stand[id][stand.stid].invalid())
					out.add_value(out_cmass_stand[id][stand.stid],      standpft_cmass);
				}

			++gc_itr;
		}//End of loop through stands

		// Print to landcover files in case pft:s are common to several landcovers (currently only used in NATURAL and FOREST)
		if (run_landcover) {
			for (int i=0;i<NLANDCOVERTYPES;i++) {
				if (run[i]) {

					switch (i) {
					case CROPLAND:
						break;
					case PASTURE:
						if (run[NATURAL]) {
							outlimit_misc(out, out_anpp_pasture,			mean_standpft_anpp_lc[i]);
							outlimit_misc(out, out_cmass_pasture,			mean_standpft_cmass_lc[i]);
						}
						break;
					case BARREN:
						break;
					case NATURAL:
//						if(run[FOREST] || run[PASTURE]) {
						if(run[FOREST]) {
							outlimit_misc(out, out_anpp_natural,			mean_standpft_anpp_lc[i]);
							outlimit_misc(out, out_cmass_natural,			mean_standpft_cmass_lc[i]);
							outlimit_misc(out, out_dens_natural,			mean_standpft_densindiv_total_lc[i]);
						}
						break;
					case FOREST:
						if (run[NATURAL]) {
							outlimit_misc(out, out_anpp_forest,				mean_standpft_anpp_lc[i]);
							outlimit_misc(out, out_cmass_forest,			mean_standpft_cmass_lc[i]);
							outlimit_misc(out, out_dens_forest,				mean_standpft_densindiv_total_lc[i]);
						}
						break;
					case URBAN:
						break;
					case PEATLAND:
						if (run[PEATLAND]) {
							outlimit_misc(out, out_anpp_peatland,			mean_standpft_anpp_lc[i]);
							outlimit_misc(out, out_cmass_peatland,			mean_standpft_cmass_lc[i]);
						}
						break;
					default:
						if (date.is_firsthist_or_restart_year())
							dprintf("Modify code to deal with landcover output!\n");
					}
				}
			}
		}

		if (pft.landcover == CROPLAND) {
			outlimit_misc(out, out_yield,   mean_standpft_yield);
			outlimit_misc(out, out_yield1,  mean_standpft_yield1);
			outlimit_misc(out, out_yield2,  mean_standpft_yield2);
            outlimit_misc(out, out_gsirr,  mean_standpft_gsirr); // SSR: Per-CFT irrigation water output
			
			// SSR
			outlimit_misc(out_lastyear, out_yield_plantyear, mean_standpft_yield_lastyear/0.446, -1);

			int pft_sdate1=-1;
			int pft_sdate2=-1;
			int pft_hdate1=-1;
			int pft_hdate2=-1;
			int pft_lgp=-1;
			double pft_phu=-1;
			double pft_fphu=-1;
			double pft_fhi=-1;

			Gridcell::iterator gc_itr = gridcell.begin();
			while (gc_itr != gridcell.end()) {
				Stand& stand = *gc_itr;

				if (stlist[stand.stid].pftinrotation(pft.name) >= 0) {
					pft_sdate1=stand[0].pft[pft.id].cropphen->sdate_thisyear[0];
					pft_sdate2=stand[0].pft[pft.id].cropphen->sdate_thisyear[1];
					pft_hdate1=stand[0].pft[pft.id].cropphen->hdate_harvest[0];
					pft_hdate2=stand[0].pft[pft.id].cropphen->hdate_harvest[1];
					pft_lgp=stand[0].pft[pft.id].cropphen->lgp;
					pft_phu=stand[0].pft[pft.id].cropphen->phu;
					pft_fphu=stand[0].pft[pft.id].cropphen->fphu_harv;
					pft_fhi=stand[0].pft[pft.id].cropphen->fhi_harv;
				}

				++gc_itr;
			}
			outlimit_misc(out, out_sdate1, pft_sdate1);
			outlimit_misc(out, out_sdate2, pft_sdate2);
			outlimit_misc(out, out_hdate1, pft_hdate1);
			outlimit_misc(out, out_hdate2, pft_hdate2);
			outlimit_misc(out, out_lgp,    pft_lgp);
			outlimit_misc(out, out_phu,    pft_phu);
			outlimit_misc(out, out_fphu,   pft_fphu);
			outlimit_misc(out, out_fhi,    pft_fhi);
		}

		pftlist.nextobj();

	} // *** End of PFT loop ***

	double flux_veg_lc[NLANDCOVERTYPES], flux_repr_lc[NLANDCOVERTYPES],
		 flux_soil_lc[NLANDCOVERTYPES], flux_fire_lc[NLANDCOVERTYPES],
		 flux_est_lc[NLANDCOVERTYPES], flux_seed_lc[NLANDCOVERTYPES];
	double flux_charvest_lc[NLANDCOVERTYPES], c_org_leach_lc[NLANDCOVERTYPES];
	double c_litter_lc[NLANDCOVERTYPES], c_fast_lc[NLANDCOVERTYPES],
		  c_slow_lc[NLANDCOVERTYPES], c_harv_slow_lc[NLANDCOVERTYPES];
	double surfsoillitterc_lc[NLANDCOVERTYPES], cwdc_lc[NLANDCOVERTYPES],
		 centuryc_lc[NLANDCOVERTYPES];

	double n_harv_slow_lc[NLANDCOVERTYPES], availn_lc[NLANDCOVERTYPES],
		   andep_lc[NLANDCOVERTYPES], anfert_lc[NLANDCOVERTYPES];
	double anmin_lc[NLANDCOVERTYPES], animm_lc[NLANDCOVERTYPES],
		   anfix_lc[NLANDCOVERTYPES], n_org_leach_lc[NLANDCOVERTYPES],
		   n_min_leach_lc[NLANDCOVERTYPES];
	double flux_ntot_lc[NLANDCOVERTYPES], flux_nharvest_lc[NLANDCOVERTYPES],
		   flux_nseed_lc[NLANDCOVERTYPES];
	double surfsoillittern_lc[NLANDCOVERTYPES], cwdn_lc[NLANDCOVERTYPES],
		   centuryn_lc[NLANDCOVERTYPES];

	//N-transform
	double flux_NH3_soil[NLANDCOVERTYPES],flux_NOx_soil[NLANDCOVERTYPES],flux_N2O_soil[NLANDCOVERTYPES],flux_N2_soil[NLANDCOVERTYPES];
	for (int i=0; i<NLANDCOVERTYPES; i++) {
		flux_veg_lc[i]=0.0;
		flux_repr_lc[i]=0.0;
		flux_soil_lc[i]=0.0;
		flux_fire_lc[i]=0.0;
		flux_est_lc[i]=0.0;
		flux_seed_lc[i]=0.0;
		flux_charvest_lc[i]=0.0;
		c_org_leach_lc[i]=0.0;

		c_litter_lc[i]=0.0;
		c_fast_lc[i]=0.0;
		c_slow_lc[i]=0.0;
		c_harv_slow_lc[i]=0.0;
		surfsoillitterc_lc[i]=0.0;
		cwdc_lc[i]=0.0;
		centuryc_lc[i]=0.0;

		flux_ntot_lc[i]=0.0;
		flux_nharvest_lc[i]=0.0;
		flux_nseed_lc[i]=0.0;

		availn_lc[i]=0.0;
		andep_lc[i]=0.0;	// same value for all land covers
		anfert_lc[i]=0.0;
		anmin_lc[i]=0.0;
		animm_lc[i]=0.0;
		anfix_lc[i]=0.0;
		n_org_leach_lc[i]=0.0;
		n_min_leach_lc[i]=0.0;
		n_harv_slow_lc[i]=0.0;
		surfsoillittern_lc[i]=0.0;
		cwdn_lc[i]=0.0;
		centuryn_lc[i]=0.0;
		//N-transform
		flux_NH3_soil[i]=0.0;
		flux_NOx_soil[i]=0.0;
		flux_N2O_soil[i]=0.0;
		flux_N2_soil[i]=0.0;
	}

	// Sum C fluxes, dead C pools and runoff across patches

	Gridcell::iterator gc_itr = gridcell.begin();

	// Loop through Stands
	while (gc_itr != gridcell.end()) {
		Stand& stand = *gc_itr;
		stand.firstobj();

		//Loop through Patches
		while (stand.isobj) {
			Patch& patch = stand.getobj();

			double to_gridcell_average = stand.get_gridcell_fraction() / (double)stand.npatch();

			flux_nseed_lc[stand.landcover]+=patch.fluxes.get_annual_flux(Fluxes::SEEDN)*to_gridcell_average;
			flux_nharvest_lc[stand.landcover]+=patch.fluxes.get_annual_flux(Fluxes::HARVESTN)*to_gridcell_average;
			flux_ntot_lc[stand.landcover]+=(patch.fluxes.get_annual_flux(Fluxes::NH3_FIRE) +
					   patch.fluxes.get_annual_flux(Fluxes::NOx_FIRE) +
					   patch.fluxes.get_annual_flux(Fluxes::N2O_FIRE) +
					   patch.fluxes.get_annual_flux(Fluxes::N2_FIRE) +
					   patch.fluxes.get_annual_flux(Fluxes::NH3_SOIL) +
					   patch.fluxes.get_annual_flux(Fluxes::NO_SOIL) +
					   patch.fluxes.get_annual_flux(Fluxes::N2O_SOIL) +
					   patch.fluxes.get_annual_flux(Fluxes::N2_SOIL)) * to_gridcell_average;

			flux_veg_lc[stand.landcover]+=-patch.fluxes.get_annual_flux(Fluxes::NPP)*to_gridcell_average;
			flux_repr_lc[stand.landcover]+=-patch.fluxes.get_annual_flux(Fluxes::REPRC)*to_gridcell_average;
			flux_soil_lc[stand.landcover]+=patch.fluxes.get_annual_flux(Fluxes::SOILC)*to_gridcell_average;
			flux_fire_lc[stand.landcover]+=patch.fluxes.get_annual_flux(Fluxes::FIREC)*to_gridcell_average;
			flux_est_lc[stand.landcover]+=patch.fluxes.get_annual_flux(Fluxes::ESTC)*to_gridcell_average;
			flux_seed_lc[stand.landcover]+=patch.fluxes.get_annual_flux(Fluxes::SEEDC)*to_gridcell_average;
			flux_charvest_lc[stand.landcover]+=patch.fluxes.get_annual_flux(Fluxes::HARVESTC)*to_gridcell_average;

			c_fast_lc[stand.landcover]+=patch.soil.cpool_fast*to_gridcell_average;
			c_slow_lc[stand.landcover]+=patch.soil.cpool_slow*to_gridcell_average;

			//Sum slow pools of harvested products
			if (run_landcover && ifslowharvestpool) {
				for (int q=0;q<npft;q++) {
					Patchpft& patchpft=patch.pft[q];
					c_harv_slow_lc[stand.landcover]+=patchpft.cmass_harvested_products_slow*to_gridcell_average;		  //slow pool in receiving landcover (1)
					n_harv_slow_lc[stand.landcover]+=patchpft.nmass_harvested_products_slow*to_gridcell_average;
				}
			}

			//Gridcell irrigation
			irrigation_gridcell += patch.irrigation_y*to_gridcell_average;

			andep_lc[stand.landcover] += (gridcell.aNH4dep + gridcell.aNO3dep) * to_gridcell_average;
			anfert_lc[stand.landcover] += patch.anfert * to_gridcell_average;
			anmin_lc[stand.landcover] += patch.soil.anmin * to_gridcell_average;
			animm_lc[stand.landcover] += patch.soil.animmob * to_gridcell_average;
			anfix_lc[stand.landcover] += patch.soil.anfix * to_gridcell_average;
			n_min_leach_lc[stand.landcover] += patch.soil.aminleach * to_gridcell_average;
			n_org_leach_lc[stand.landcover] += patch.soil.aorgNleach * to_gridcell_average;
			c_org_leach_lc[stand.landcover] += patch.soil.aorgCleach * to_gridcell_average;
			availn_lc[stand.landcover] += (patch.soil.NH4_mass + patch.soil.NO3_mass + patch.soil.snowpack_NH4_mass + patch.soil.snowpack_NO3_mass) * to_gridcell_average;

			//N-transform
			flux_NH3_soil[stand.landcover]	+=patch.fluxes.get_annual_flux(Fluxes::NH3_SOIL)*to_gridcell_average;
			flux_NOx_soil[stand.landcover]	+=patch.fluxes.get_annual_flux(Fluxes::NO_SOIL)*to_gridcell_average;
			flux_N2O_soil[stand.landcover]	+=patch.fluxes.get_annual_flux(Fluxes::N2O_SOIL)*to_gridcell_average;
			flux_N2_soil[stand.landcover]	+=patch.fluxes.get_annual_flux(Fluxes::N2_SOIL)*to_gridcell_average;;

			for (int r = 0; r < NSOMPOOL; r++) {

				if (r == SURFMETA || r == SURFSTRUCT || r == SOILMETA || r == SOILSTRUCT){
					surfsoillitterc_lc[stand.landcover] += patch.soil.sompool[r].cmass * to_gridcell_average;
					surfsoillittern_lc[stand.landcover] += patch.soil.sompool[r].nmass * to_gridcell_average;
				}
				else if (r == SURFFWD || r == SURFCWD) {
					cwdc_lc[stand.landcover] += patch.soil.sompool[r].cmass * to_gridcell_average;
					cwdn_lc[stand.landcover] += patch.soil.sompool[r].nmass * to_gridcell_average;
				}
				else {
					centuryc_lc[stand.landcover] += patch.soil.sompool[r].cmass * to_gridcell_average;
					centuryn_lc[stand.landcover]  += patch.soil.sompool[r].nmass * to_gridcell_average;
				}
			}
			stand.nextobj();
		} // patch loop
		++gc_itr;
	} // stand loop

	// Print per-stand totals
	if (printseparatestands) {

		Gridcell::iterator gc_itr = gridcell.begin();
		while (gc_itr != gridcell.end()) {

			Stand& stand = *gc_itr;
			int id = stand.id;;

			if(!out_anpp_stand[id][stand.stid].invalid())
				out.add_value(out_anpp_stand[id][stand.stid],      stand.anpp);
			if(!out_cmass_stand[id][stand.stid].invalid())
				out.add_value(out_cmass_stand[id][stand.stid],      stand.cmass);

			++gc_itr;
		}
	}

	if (run[CROPLAND]) {
		outlimit_misc(out, out_irrigation,   irrigation_gridcell);
	}

	// Print landcover totals to files
	if (run_landcover) {
		for (int i=0;i<NLANDCOVERTYPES;i++) {
			if (run[i]) {
				switch (i) {
				case CROPLAND:
					break;
				case PASTURE:
					if (run[NATURAL]) {
						outlimit_misc(out, out_anpp_pasture,     landcover_anpp[i]);
						outlimit_misc(out, out_cmass_pasture,	landcover_cmass[i]);
					}
					break;
				case BARREN:
					break;
				case NATURAL:
//					if(run[FOREST] || run[PASTURE]) {
					if(run[FOREST]) {
						outlimit_misc(out, out_anpp_natural,		landcover_anpp[i]);
						outlimit_misc(out, out_cmass_natural,		landcover_cmass[i]);
						outlimit_misc(out, out_dens_natural,		landcover_densindiv_total[i]);
					}
					break;
				case FOREST:
					if (run[NATURAL]) {
						outlimit_misc(out, out_anpp_forest,			landcover_anpp[i]);
						outlimit_misc(out, out_cmass_forest,		landcover_cmass[i]);
						outlimit_misc(out, out_dens_forest,			landcover_densindiv_total[i]);
					}
					break;
				case URBAN:
					break;
				case PEATLAND:
					if (run[PEATLAND]) {
						outlimit_misc(out, out_anpp_peatland,		landcover_anpp[i]);
						outlimit_misc(out, out_cmass_peatland,		landcover_cmass[i]);
					}
					break;
				default:
					if (date.is_firsthist_or_restart_year())
						dprintf("Modify code to deal with landcover output!\n");
				}
			}
		}
	}

	// Print C fluxes to per-landcover files
	if (run_landcover) {
		for (int i=0;i<NLANDCOVERTYPES;i++) {
			if (run[i]) {

				GuessOutput::Table* table_p=NULL;
				GuessOutput::Table* table_p_N=NULL;

				GuessOutput::Table* table_p_N_soil=NULL;
				switch (i) {
				case CROPLAND:
					table_p=&out_cflux_cropland;
					table_p_N=&out_nflux_cropland;
					table_p_N_soil=&out_soil_nflux_cropland;
					break;
				case PASTURE:
					table_p=&out_cflux_pasture;
					table_p_N=&out_nflux_pasture;
					table_p_N_soil=&out_soil_nflux_pasture;
					break;
				case NATURAL:
					table_p=&out_cflux_natural;
					table_p_N=&out_nflux_natural;
					table_p_N_soil=&out_soil_nflux_natural;
					break;
				case FOREST:
					table_p=&out_cflux_forest;
					table_p_N=&out_nflux_forest;
					table_p_N_soil=&out_soil_nflux_forest;
					break;
				case URBAN:
					break;
				case PEATLAND:
					table_p=&out_cflux_peatland;
					table_p_N=&out_nflux_peatland;
					break;
				case BARREN:
					break;
				default:
					if (date.is_firsthist_or_restart_year())
						dprintf("Modify code to deal with landcover output!\n");
				}

				if (table_p) {
					outlimit_misc(out, *table_p, flux_veg_lc[i]);
					outlimit_misc(out, *table_p, -flux_repr_lc[i]);
					outlimit_misc(out, *table_p, flux_soil_lc[i] + c_org_leach_lc[i]);
					outlimit_misc(out, *table_p, flux_fire_lc[i]);
					outlimit_misc(out, *table_p, flux_est_lc[i]);

					outlimit_misc(out, *table_p_N, -andep_lc[i] * M2_PER_HA);
					outlimit_misc(out, *table_p_N, -anfix_lc[i] * M2_PER_HA);
					outlimit_misc(out, *table_p_N, -anfert_lc[i] * M2_PER_HA);
					outlimit_misc(out, *table_p_N, flux_ntot_lc[i] * M2_PER_HA);
					outlimit_misc(out, *table_p_N, (n_min_leach_lc[i] + n_org_leach_lc[i]) * M2_PER_HA);

					if (run_landcover) {
						 outlimit_misc(out, *table_p, flux_seed_lc[i]);
						 outlimit_misc(out, *table_p, flux_charvest_lc[i]);
						 outlimit_misc(out, *table_p, lc.acflux_landuse_change_lc[i]);
						 outlimit_misc(out, *table_p, lc.acflux_harvest_slow_lc[i]);
						 outlimit_misc(out, *table_p_N, flux_nseed_lc[i] * M2_PER_HA);
						 outlimit_misc(out, *table_p_N, flux_nharvest_lc[i] * M2_PER_HA);
						 outlimit_misc(out, *table_p_N, lc.anflux_landuse_change_lc[i] * M2_PER_HA);
						 outlimit_misc(out, *table_p_N, lc.anflux_harvest_slow_lc[i] * M2_PER_HA);
					}
				}

				double cflux_total = flux_veg_lc[i] - flux_repr_lc[i] + flux_soil_lc[i] + flux_fire_lc[i] + flux_est_lc[i] + c_org_leach_lc[i];
				double nflux_total = -andep_lc[i] - anfix_lc[i] - anfert_lc[i] + flux_ntot_lc[i] + n_min_leach_lc[i] + n_org_leach_lc[i];

				if (run_landcover) {
					cflux_total += flux_seed_lc[i];
					cflux_total += flux_charvest_lc[i];
					cflux_total += lc.acflux_landuse_change_lc[i];
					cflux_total += lc.acflux_harvest_slow_lc[i];
					nflux_total += flux_nseed_lc[i];
					nflux_total += flux_nharvest_lc[i];
					nflux_total += lc.anflux_landuse_change_lc[i];
					nflux_total += lc.anflux_harvest_slow_lc[i];
				}
				if (table_p) {
					outlimit_misc(out, *table_p,  cflux_total);
					outlimit_misc(out, *table_p_N,  nflux_total * M2_PER_HA);
				}
			}
		}

		// Print C pools to per-landcover files
		for (int i=0;i<NLANDCOVERTYPES;i++) {
			if (run[i]) {

				GuessOutput::Table* table_p=NULL;
				GuessOutput::Table* table_p_N=NULL;

				switch (i) {
				case CROPLAND:
					table_p=&out_cpool_cropland;
					table_p_N=&out_npool_cropland;
					break;
				case PASTURE:
					table_p=&out_cpool_pasture;
					table_p_N=&out_npool_pasture;
					break;
				case NATURAL:
					table_p=&out_cpool_natural;
					table_p_N=&out_npool_natural;
					break;
				case FOREST:
					table_p=&out_cpool_forest;
					table_p_N=&out_npool_forest;
					break;
				case URBAN:
					break;
				case PEATLAND:
					table_p=&out_cpool_peatland;
					table_p_N=&out_npool_peatland;
					break;
				case BARREN:
					break;
				default:
					if (date.is_firsthist_or_restart_year())
						dprintf("Modify code to deal with landcover output!\n");
				}

				if (table_p) {
					outlimit_misc(out, *table_p, landcover_cmass[i] * lc.frac[i]);
					outlimit_misc(out, *table_p_N, (landcover_nmass[i] + landcover_nlitter[i]) * lc.frac[i]);

					if (!ifcentury) {
						outlimit_misc(out, *table_p, landcover_clitter[i] * lc.frac[i]);
						outlimit_misc(out, *table_p, c_fast_lc[i]);
						outlimit_misc(out, *table_p, c_slow_lc[i]);
					}
					else {
						outlimit_misc(out, *table_p, landcover_clitter[i] * lc.frac[i] + surfsoillitterc_lc[i] + cwdc_lc[i]);
						outlimit_misc(out, *table_p, centuryc_lc[i]);
						outlimit_misc(out, *table_p_N, surfsoillittern_lc[i] + cwdn_lc[i]);
						outlimit_misc(out, *table_p_N, centuryn_lc[i] + availn_lc[i]);
					}

					if (run_landcover && ifslowharvestpool) {
						outlimit_misc(out, *table_p, c_harv_slow_lc[i]);
						outlimit_misc(out, *table_p_N, n_harv_slow_lc[i]);
					}
				}

				// Calculate total cpool, starting with cmass and litter...
				double cpool_total = (landcover_cmass[i] + landcover_clitter[i]) * lc.frac[i];
				double npool_total = (landcover_nmass[i] + landcover_nlitter[i]) * lc.frac[i];

				// Add SOM pools
				if (!ifcentury) {
					cpool_total += c_fast_lc[i] + c_slow_lc[i];
				}
				else {
					cpool_total += centuryc_lc[i] + surfsoillitterc_lc[i] + cwdc_lc[i];
					npool_total += centuryn_lc[i] + surfsoillittern_lc[i] + cwdn_lc[i] + availn_lc[i];
				}

				// Add slow harvest pool if needed
				if (run_landcover && ifslowharvestpool) {
					cpool_total += c_harv_slow_lc[i];
					npool_total += n_harv_slow_lc[i];
				}
				if (table_p) {
					outlimit_misc(out, *table_p, cpool_total);
					outlimit_misc(out, *table_p_N, npool_total);
				}
			}
		}
	}

	double gridcell_climate_agdd0_20_mean;
	if (gridcell.climate.agdd0_20.size()>0) {
		gridcell_climate_agdd0_20_mean = gridcell.climate.agdd0_20.mean();
	}
	else {
		gridcell_climate_agdd0_20_mean = -999;
	}

	//Output of seasonality variables
	outlimit_misc(out, out_seasonality,   gridcell.climate.seasonality);
	outlimit_misc(out, out_seasonality,   gridcell.climate.var_temp);
	outlimit_misc(out, out_seasonality,   gridcell.climate.var_prec);
	outlimit_misc(out, out_seasonality,   gridcell.climate.mtemp_min20);
	outlimit_misc(out, out_seasonality,   gridcell.climate.atemp_mean);
	outlimit_misc(out, out_seasonality,   gridcell.climate.mtemp_max20);
	outlimit_misc(out, out_seasonality,   gridcell.climate.mtemp_max);
	outlimit_misc(out, out_seasonality,   gridcell.climate.temp_seasonality);
	outlimit_misc(out, out_seasonality,   gridcell_climate_agdd0_20_mean);
	outlimit_misc(out, out_seasonality,   gridcell.climate.agdd5);
	outlimit_misc(out, out_seasonality,   gridcell.climate.mprec_petmin20);
	outlimit_misc(out, out_seasonality,   gridcell.climate.aprec);
	outlimit_misc(out, out_seasonality,   gridcell.climate.prec_range);
}

/// Output of simulation results at the end of each day
/** This function does not have to provide any information to the framework.
  */
void MiscOutput::outdaily(Gridcell& gridcell) {
	
	if (just_phu_pvd) {
		return;
	}

	double lon = gridcell.get_lon();
	double lat = gridcell.get_lat();
	OutputRows out(output_channel, lon, lat, date.get_calendar_year(), date.day);

	if (!date.write_outputs()) {
		return;
	}

	outlimit_misc(out, out_daily_climate, gridcell.climate.temp);
	outlimit_misc(out, out_daily_climate, gridcell.climate.prec);
	outlimit_misc(out, out_daily_climate, gridcell.climate.rad);

	if (firemodel==BLAZE) {
		outlimit_misc(out, out_dblaze_ba, gridcell.effective_burned_area*FRACT_TO_PERCENT);
	}
}

// SSR: GGCMI
void MiscOutput::outharvest(Gridcell& gridcell) {
    // DESCRIPTION
    // Output of simulation results at the end of each growing season. This function does not have to
    // provide any information to the framework.

	if (date.get_calendar_year()<firstoutyear) {
        return;
    }

    double lon = gridcell.get_lon();
    double lat = gridcell.get_lat();
//    if(printseparatestands){
//        output_modules.openlocalfiles(gridcell);
//    }else{
//        return;
//    }
    if(!crop_gs_out) {
        return;
    }

    Gridcell::iterator gc_itr = gridcell.begin();
    while (gc_itr != gridcell.end()) {

        Stand& stand = *gc_itr;
        if (stand.landcover != CROPLAND) {
			++gc_itr;
            continue;
        }

        stand.firstobj();
        while (stand.isobj) {
            Patch& patch = stand.getobj();

            int st=stand.stid;

            Vegetation& vegetation=patch.vegetation;

            vegetation.firstobj();
            Individual& indiv=vegetation.getobj();
            
            // SSR: GGCMI: If there was previously no cropland but now there is, you'll get an error in the next step. Skip instead.
            if (!vegetation.isobj) {
				if (date.day==0 || (date.islastday && date.islastmonth)) {
					dprintf("outharvest(): Skipping patch with no vegetation (%d, stand %d, patch %d)\n", date.get_calendar_year(), stand.id, patch.id);
				}
				stand.nextobj();
				continue;
            }
            
            cropphen_struct& cropphen = *(patch.pft[indiv.pft.id].cropphen);
            cropindiv_struct& cropindiv = *(indiv.cropindiv);
			bool is_harvest_date = cropphen.hdate == date.day;
			bool save_at_end_of_last_year = cropphen.growingseason && date.islastday && date.islastmonth && date.get_calendar_year()==lasthistyear;
			if (save_at_end_of_last_year) {
				int x=1;
			}
			if (is_harvest_date || save_at_end_of_last_year) {
                
                // We want year of PLANTING, not harvest
                int year = date.get_calendar_year();
                if (is_harvest_date && Date::stepfromdate(cropphen.planting_date, cropphen.dap_mat-1) < cropphen.planting_date)
                    year = year - 1 ;
				
                // Skip if not within outperiod
				if (year < firstoutyear || year > lastoutyear) {
					stand.nextobj();
                    continue;
				}
                
                OutputRows out(output_channel, lon, lat, year, date.day);
				out.add_value(out_misc_stand[st],!cropphen.bad_bioclimate); // ggcmi okbc (OK bioclimate?)
				out.add_value(out_misc_stand[st],cropindiv.cmass_ho_harvest_ggcmi/0.446*10.0); // ggcmi yield
				out.add_value(out_misc_stand[st],cropindiv.cmass_ho_harvest_ggcmi/cropindiv.nmass_ho_harvest_ggcmi); // ggcmi cn-yield
                out.add_value(out_misc_stand[st],cropindiv.cmass_ag_harvest/0.446*10.0); // ggcmi biom
                out.add_value(out_misc_stand[st],cropphen.planting_date); // ggcmi plant-day
                out.add_value(out_misc_stand[st],cropphen.dap_anth); // ggcmi anth-day
                out.add_value(out_misc_stand[st],cropphen.dap_mat); // ggcmi maty-day
                out.add_value(out_misc_stand[st],patch.grs_w_irr); // ggcmi pirrw
                out.add_value(out_misc_stand[st],patch.grs_w_evapo+patch.grs_w_transp+patch.grs_w_intercep); // ggcmi aet
                out.add_value(out_misc_stand[st],patch.grs_w_transp); // ggcmi transp
                out.add_value(out_misc_stand[st],patch.grs_w_evapo); // ggcmi evap
                out.add_value(out_misc_stand[st],patch.grs_w_runoff); // ggcmi runoff
                out.add_value(out_misc_stand[st],cropindiv.cmass_bg_harvest/0.446*10.0); // ggcmi rootm
                out.add_value(out_misc_stand[st],cropindiv.nmass_uptake_harvest*10000.0); // ggcmi tnrup kg/ha
                out.add_value(out_misc_stand[st],patch.grs_n_input*10000.0); // ggcmi tnrin kg/ha
                out.add_value(out_misc_stand[st],patch.grs_n_losses*10000.0); // ggcmi tnrloss kg/ha
				out.add_value(out_misc_stand[st],patch.soil.sminleach*1000.0); // ggcmi nleach g/m2
				out.add_value(out_misc_stand[st],patch.semis_n2o*1000.0); // ggcmi n2oemis g/m2
				out.add_value(out_misc_stand[st],patch.semis_n2*1000.0); // ggcmi n2emis g/m2
				out.add_value(out_misc_stand[st],patch.semis_c*1000.0); // ggcmi tcemis g/m2
                out.add_value(out_misc_stand[st],cropphen.husum); // ggcmi husum
                out.add_value(out_misc_stand[st],cropphen.vdsum); // ggcmi vdsum
                out.add_value(out_misc_stand[st],cropphen.phu); // ggcmi phu
                out.add_value(out_misc_stand[st],cropphen.pvd); // ggcmi pvd
                out.add_value(out_misc_stand[st],patch.snfert*10000.0); // ggcmi nfert
            }

            stand.nextobj();
			break; // Ensure that, if multiple crop patches for some reason, you're only saving the first one
        }
        ++gc_itr;
    }
}


// SSR: GGCMI
void MiscOutput::outannual_ggcmi(Gridcell& gridcell) {
    // DESCRIPTION
    // Output of simulation results at the end of each growing season. This function does not have to
    // provide any information to the framework.

    if (date.get_calendar_year() < firstoutyear || date.get_calendar_year() > lastoutyear) {
        return;
    }

    double lon = gridcell.get_lon();
    double lat = gridcell.get_lat();
	
	if(!crop_gs_out) {
		return;
	}

	Gridcell::iterator gc_itr = gridcell.begin();
	while (gc_itr != gridcell.end()) {

		Stand& stand = *gc_itr;
		if (stand.landcover != CROPLAND || stand.npatch() > 1) {
			++gc_itr;
			continue;
		}

		stand.firstobj();
		while (stand.isobj) {
			Patch& patch = stand.getobj();
			int st=stand.stid;
			
			OutputRows out(output_channel, lon, lat, date.get_calendar_year());
			int m;
			for (m = 0; m < 12; m++) {
				out.add_value(out_rootmoistm_stand[st],patch.soil.grs_mwcont_top1m[m]); // ggcmi yield
			}
			
			stand.nextobj();
		}
		++gc_itr;
	}
}

void MiscOutput::outharvest_justphupvd(Gridcell& gridcell) {
	
	if (date.get_calendar_year() < firstoutyear) {
		return;
	}

	double lon = gridcell.get_lon();
	double lat = gridcell.get_lat();
//    if(printseparatestands){
//        output_modules.openlocalfiles(gridcell);
//    }else{
//        return;
//    }

	if(!crop_gs_out) {
        return;
    }
	
	Gridcell::iterator gc_itr = gridcell.begin();
    while (gc_itr != gridcell.end()) {

        Stand& stand = *gc_itr;
        if (stand.landcover != CROPLAND || stand.npatch() > 1) {
            ++gc_itr;
            continue;
        }

        stand.firstobj();
        while (stand.isobj) {
            Patch& patch = stand.getobj();

            int st=stand.stid;

            Vegetation& vegetation=patch.vegetation;

            vegetation.firstobj();
            Individual& indiv=vegetation.getobj();
            
            // SSR: GGCMI: If there was previously no cropland but now there is, you'll get an error in the next step. Skip instead.
            if (!vegetation.isobj) {
				if (date.day==0 || (date.islastday && date.islastmonth)) {
					dprintf("outharvest_justphupvd(): Skipping patch with no vegetation (%d, stand %d, patch %d)\n", date.get_calendar_year(), stand.id, patch.id);
				}
				stand.nextobj();
				continue;
            }
            
            cropphen_struct& cropphen = *(patch.pft[indiv.pft.id].cropphen);
			bool is_harvest_date = cropphen.hdate == date.day;
			bool save_at_end_of_last_year = cropphen.growingseason && date.islastday && date.islastmonth && date.get_calendar_year()==lasthistyear;
			if (is_harvest_date || save_at_end_of_last_year){
                
                // We want year of PLANTING, not harvest
                int year = date.get_calendar_year();
                if (is_harvest_date && Date::stepfromdate(cropphen.planting_date, cropphen.dap_mat-1) < cropphen.planting_date)
                    year = year - 1 ;
				
                // Skip if not within outperiod
				if (year < firstoutyear || year > lastoutyear) {
					stand.nextobj();
                    continue;
				}
                
                OutputRows out(output_channel, lon, lat, year, date.day);
                out.add_value(out_phupvd_stand[st],cropphen.husum); // ggcmi husum
                out.add_value(out_phupvd_stand[st],cropphen.vdsum); // ggcmi vdsum
                out.add_value(out_phupvd_stand[st],cropphen.phu); // ggcmi phu
                out.add_value(out_phupvd_stand[st],cropphen.pvd); // ggcmi pvd

            }

            stand.nextobj();
        }
        ++gc_itr;
    }
}


void MiscOutput::openlocalfiles(Gridcell& gridcell) {

	if(!printseparatestands)
		return;

	if (!date.year) {
		for(int id=0;id<MAXNUMBER_STANDS;id++) {
			out_anpp_stand[id] = new Table[nst];
			out_cmass_stand[id] = new Table[nst];
		}
	}

	if(!(date.write_outputs() || ((file_yield_plantyear!="" || file_yield_plantyear_st!="" || file_gsirr_plantyear_st!="") && date.write_outputs(-1))))
		return;

	bool open[NLANDCOVERTYPES];
	double lon = gridcell.get_lon();
	double lat = gridcell.get_lat();

	for(int i=0;i<NLANDCOVERTYPES;i++)
		open[i] = false;

	Gridcell::iterator gc_itr = gridcell.begin();

	// Loop through Stands
	while (gc_itr != gridcell.end()) {
		Stand& stand = *gc_itr;

		stand.anpp=0.0;
		stand.cmass=0.0;

		if(stand.first_year == date.year || stand.clone_year == date.year) {
			if(stand.landcover == NATURAL) {
				open[NATURAL] = true;
			}
			else if(stand.landcover == FOREST) {
				open[FOREST] = true;
			}
		}

		++gc_itr;
	}

	if(PRINTFIRSTSTANDFROM1901 && date.year == nyear_spinup) {
		open[NATURAL] = true;
		open[FOREST] = true;
	}

	if(open[NATURAL] || open[FOREST]) {

		gc_itr = gridcell.begin();

		while (gc_itr != gridcell.end()) {

			Stand& stand = *gc_itr;
			StandType& st = stlist[stand.stid];

			int id = stand.id;
			char outfilename[100]={'\0'}, buffer[50]={'\0'};

			sprintf(buffer, "_%.1f_%.1f_%d",lon, lat, id);
			strcat(buffer, ".out");

			// create a vector with the pft names
			std::vector<std::string> pfts;

			pftlist.firstobj();
			while (pftlist.isobj) {

				 Pft& pft=pftlist.getobj();	 
				 Standpft& standpft=stand.pft[pft.id];

				 if(standpft.active)
					 pfts.push_back((char*)pft.name);

				 pftlist.nextobj();
			}
			ColumnDescriptors anpp_columns;
			anpp_columns += ColumnDescriptors(pfts,               8, 3);
			anpp_columns += ColumnDescriptor("Total",             8, 3);

			if(open[stand.landcover]) {

				strcpy(outfilename, "anpp_");
				strcat(outfilename, (char*)st.name);
				strcat(outfilename, buffer);

				if(out_anpp_stand[id][stand.stid].invalid())
					create_output_table(out_anpp_stand[id][stand.stid], outfilename, anpp_columns);

				outfilename[0] = '\0';
				strcpy(outfilename, "cmass_");
				strcat(outfilename, (char*)st.name);
				strcat(outfilename, buffer);

				if(out_cmass_stand[id][stand.stid].invalid())
					create_output_table(out_cmass_stand[id][stand.stid], outfilename, anpp_columns);
			}

			++gc_itr;
		}
	}
}

void MiscOutput::closelocalfiles(Gridcell& gridcell) {

	if(!printseparatestands)
		return;

	for(int id=0;id<MAXNUMBER_STANDS;id++) {

		for(int st=0;st<nst;st++) {
			if(!out_anpp_stand[id][st].invalid())
				close_output_table(out_anpp_stand[id][st]);
			if(!out_cmass_stand[id][st].invalid())
				close_output_table(out_cmass_stand[id][st]);
	}
}
	for(int id=0;id<MAXNUMBER_STANDS;id++) {
		if(out_anpp_stand[id])
			delete[] out_anpp_stand[id];
		if(out_cmass_stand[id])
			delete[] out_cmass_stand[id];
	}
}

// SSR: GGCMI
void MiscOutput::openlocalfiles_ggcmi() {

    // SSR: GGCMI
    ColumnDescriptors misc_columns;
	misc_columns += ColumnDescriptor("okbc",		     5, 0);
    misc_columns += ColumnDescriptor("yield",			10, 4);
	misc_columns += ColumnDescriptor("cnyield",			10, 4);
    misc_columns += ColumnDescriptor("biom",            10, 4);
    misc_columns += ColumnDescriptor("plantday",		10, 0);
    misc_columns += ColumnDescriptor("anthday",			10, 0);
    misc_columns += ColumnDescriptor("matyday",			10, 0);
    misc_columns += ColumnDescriptor("pirrww",			12, 3);
    misc_columns += ColumnDescriptor("aet",				12, 3);
    misc_columns += ColumnDescriptor("transp",			12, 3);
    misc_columns += ColumnDescriptor("evap",            12, 3);
    misc_columns += ColumnDescriptor("runoff",			12, 3);
    misc_columns += ColumnDescriptor("rootm",			12, 3);
    misc_columns += ColumnDescriptor("tnrup",			12, 5);
    misc_columns += ColumnDescriptor("tnrin",			12, 5);
    misc_columns += ColumnDescriptor("tnrloss",			12, 5);
	misc_columns += ColumnDescriptor("nleach",			12, 5);
	misc_columns += ColumnDescriptor("n2oemis",			12, 5);
	misc_columns += ColumnDescriptor("n2emis",			12, 5);
	misc_columns += ColumnDescriptor("tcemis",			12, 5);
    misc_columns += ColumnDescriptor("husum",			10, 2);
    misc_columns += ColumnDescriptor("vdsum",			10, 2);
    misc_columns += ColumnDescriptor("phu",				10, 2);
    misc_columns += ColumnDescriptor("pvd",				10, 2);
	misc_columns += ColumnDescriptor("nfert",			12, 6);
	
	ColumnDescriptors phupvd_columns;
    phupvd_columns += ColumnDescriptor("husum",			10, 2);
    phupvd_columns += ColumnDescriptor("vdsum",			10, 2);
    phupvd_columns += ColumnDescriptor("phu",				10, 2);
    phupvd_columns += ColumnDescriptor("pvd",				10, 2);

	// Create the month columns
	ColumnDescriptors month_columns;
	ColumnDescriptors month_columns_wide;
	xtring months[] = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};
	for (int i = 0; i < 12; i++) {
		month_columns      += ColumnDescriptor(months[i], 8,  3);
		month_columns_wide += ColumnDescriptor(months[i], 10, 3);
	}
	
    // create a vector with the pft names
    std::vector<std::string> stands;

    std::string filename;

    stlist.firstobj();

    while (stlist.isobj) {
		StandType& st=stlist.getobj();

		stands.push_back((char*)st.name);
		
		if (just_phu_pvd) {
			filename="phupvd_";
			filename+=st.name;
			filename+=".out";
			if(out_phupvd_stand[st.id].invalid())
				create_output_table(out_phupvd_stand[st.id], filename.c_str(), phupvd_columns);
		} else {
			filename="misc_";
			filename+=st.name;
			filename+=".out";
			if(out_misc_stand[st.id].invalid())
				create_output_table(out_misc_stand[st.id], filename.c_str(), misc_columns);
			
			filename="rootmoistm_";
			filename+=st.name;
			filename+=".out";
			if(out_rootmoistm_stand[st.id].invalid())
				create_output_table(out_rootmoistm_stand[st.id], filename.c_str(), month_columns);
		}
		
		stlist.nextobj();
    }

}

// SSR: GGCMI
void MiscOutput::closelocalfiles_ggcmi() {

    while (stlist.isobj) {
		StandType& st=stlist.getobj();
		int id = st.id;

        if (just_phu_pvd) {
			
			if(!out_phupvd_stand[id].invalid())
				close_output_table(out_phupvd_stand[id]);
			
		} else {
			
			if(!out_misc_stand[id].invalid())
				close_output_table(out_misc_stand[id]);
			
			if(!out_rootmoistm_stand[id].invalid())
				close_output_table(out_rootmoistm_stand[id]);
			
		}
		
		stlist.nextobj();
	}
}

} // namespace
