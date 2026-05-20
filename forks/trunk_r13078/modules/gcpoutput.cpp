///////////////////////////////////////////////////////////////////////////////////////
/// \file gcpoutput.cpp
/// \brief Implementation of a special GCP output module
///
/// \author Peter Anthoni
/// $Date: $
///
///////////////////////////////////////////////////////////////////////////////////////

#include "config.h"
#include "gcpoutput.h"
#include "parameters.h"
#include "guess.h"

#ifndef GCP
#pragma message( "GCP is not defined " __FILE__ " will not be compiled, no gcpoutput available!")
#else

void gcp_growth_accounting_estc(Individual& indiv) {
	// indiv survived its first year, debit current biomass as establishment flux (see growth() reported Fluxes:ESTC)
	if (!indiv.istruecrop_or_intercropgrass()) {
		indiv.report_flux(Fluxes::PESTC,
											- (indiv.cmass_leaf + indiv.cmass_root + indiv.cmass_sap +
												 indiv.cmass_heart - indiv.cmass_debt));
	}
	
}

void gcp_dailyaccounting_patch(Patch& patch) {
	
	if (date.year>=nyear_spinup) {
		
		if (date.day==0) {
			for (int m=0;m<12;m++) {
			}
		}
		Stand& stand = patch.stand;
		Vegetation& vegetation = patch.vegetation;
		for(unsigned int k = 0; k < vegetation.nobj; k++) {
			
			Individual& indiv = vegetation[k];

			// we will sum the LAI and CMASS during the month
			// and later calculate the mean with reported_patch_monthsum/ndaysmonth
			indiv.report_flux(Fluxes::LAI, indiv.lai_today());
			indiv.report_flux(Fluxes::CMASS_LEAF, indiv.cmass_leaf_today());
			double cmass_wood = 0.0;
			if (indiv.pft.lifeform==TREE) {
				cmass_wood = indiv.cmass_wood();
			}
			indiv.report_flux(Fluxes::CMASS_WOOD, cmass_wood);
			indiv.report_flux(Fluxes::CMASS_ROOT, indiv.cmass_root_today());
			
			double cmass_veg=0.0;
			if(indiv.pft.landcover == CROPLAND) {
				cmass_veg += indiv.cmass_leaf_today() + indiv.cmass_root_today();
				if(indiv.cropindiv && indiv.patchpft().cropphen->growingseason) {
					// similar to indiv ccont()
					cmass_veg += indiv.cropindiv->grs_cmass_ho + indiv.cropindiv->grs_cmass_agpool + indiv.cropindiv->grs_cmass_dead_leaf + indiv.cropindiv->grs_cmass_stem;
				}
			} else {
				cmass_veg += indiv.cmass_leaf_today() + indiv.cmass_wood() + indiv.cmass_root_today();
			}
			indiv.report_flux(Fluxes::CMASS_VEG, cmass_veg);
			
			indiv.report_flux(Fluxes::AET, indiv.aet);

#ifndef GCP_INJECT_CODE
			// Note: this here only works if growth() was called and has let the indiv survive!
			if (indiv.alive && indiv.age == 1 && date.islastmonth && date.islastday) {
				// indiv survived its first year, debit current biomass as establishment flux (see growth() reported Fluxes:ESTC)
				gcp_growth_accounting_estc(indiv);
			}
#endif
		}
	}
}

namespace GuessOutput {
	
	// Nitrogen output is in kgN/ha instead of kgC/m2 as for carbon
	const double m2toha = 1000.0;
	
	REGISTER_OUTPUT_MODULE("gcp", GCPOutput)
	
	GCPOutput::GCPOutput() {
		
		
		// Monthly output variables
		declare_parameter("file_mplai",&file_mplai,300, "Monthly LAI per pft output file (must have .out extension)");
		declare_parameter("file_mpgpp",&file_mpgpp,300, "Monthly GPP per pft output file (must have .out extension)");
		declare_parameter("file_mpnpp",&file_mpnpp,300, "Monthly NPP per pft output file (must have .out extension)");
		declare_parameter("file_mpestc",&file_mpestc,300, "Monthly establishment C flux per pft output file (must have .out extension)");
		declare_parameter("file_mpaet",&file_mpaet,300, "Monthly AET per pft output file (must have .out extension)");
		declare_parameter("file_mpcmass_leaf",&file_mpcmass_leaf,300, "Monthly cmass leaf per pft output file (must have .out extension)");
		declare_parameter("file_mpcmass_root",&file_mpcmass_root,300, "Monthly cmass root per pft output file (must have .out extension)");
		declare_parameter("file_mpcmass_wood",&file_mpcmass_wood,300, "Monthly cmass wood per pft output file (must have .out extension)");
		declare_parameter("file_mpcmass_veg",&file_mpcmass_veg,300, "Monthly cmass vegetation (leaf+root+wood) per pft output file (must have .out extension)");
		
		// Monthly output variables
		declare_parameter("file_mestc", &file_mestc, 300, "Monthly establishment C flux output file");
		declare_parameter("file_soiltemp",&file_soiltemp,300, "Monthly soil temperature output file (in trunk v4.1 deprecated use file_msoiltempdepth25)");
		declare_parameter("file_mevtra", &file_mevtra, 300, "Monthly Evapotranspiration output file"); // sum of mevap, maet and mintercep
		declare_parameter("file_mprec", &file_mprec, 300, "Monthly precipitation output file");
		
		// Annual output variables
		declare_parameter("file_cpool_gcp", &file_cpool_gcp, 300, "Special GCP cpool output (handles ag&bg litter differently)");
		declare_parameter("file_npool_gcp", &file_npool_gcp, 300, "Special GCP cpool output (handles ag&bg litter differently)");
		declare_parameter("file_agclitter", &file_agclitter, 300, "Aboveground litter C output file");
		declare_parameter("file_agnlitter", &file_agnlitter, 300, "Aboveground litter N output file");
		declare_parameter("file_cmass_leaf", &file_cmass_leaf, 300, "C leaf biomass output file");
		declare_parameter("file_cmass_sap", &file_cmass_sap, 300, "C sapwood biomass output file");
		declare_parameter("file_cmass_heart", &file_cmass_heart, 300, "C heartwood biomass output file");
		declare_parameter("file_cmass_root", &file_cmass_root, 300, "C root biomass output file");
		declare_parameter("file_cflux_harvest", &file_cflux_harvest, 300, "CO2 Flux to Atmosphere from Harvesting");
		declare_parameter("file_nflux_harvest", &file_nflux_harvest, 300, "N Flux to Atmosphere from Harvesting");
		declare_parameter("file_gsirr",&file_gsirr,300,"Crop irrigation output file"); //Per CFT irrigation water output - TP 03.09.15
		declare_parameter("file_landcoverfrac",&file_landcoverfrac,300,"Landcover fraction");

	}
	
	GCPOutput::~GCPOutput() {
	}
	
	void GCPOutput::init() {
		// Define all output tables and their formats
		define_output_tables();
	}
	
	/** This function specifies all columns in all output tables, their names,
	 *  column widths and precision.
	 *
	 *  For each table a TableDescriptor object is created which is then sent to
	 *  the output channel to create the table.
	 */
	void GCPOutput::define_output_tables() {
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
		
		// create a vector with the landcover column titles
		std::vector<std::string> landcovers;
		
		const char* landcover_string[]={"Urban_sum", "Crop_sum", "Pasture_sum",	"Forest_sum", "Natural_sum", "Peatland_sum", "Barren_sum"};
		for (int i=0; i<NLANDCOVERTYPES; i++) {
			if (run[i]) {
				landcovers.push_back(landcover_string[i]);
			}
		}
		
		// Create the month columns
		ColumnDescriptors month_columns;
		ColumnDescriptors month_columns_wide;
		ColumnDescriptors month_columns_dec5;
		xtring months[] = {"Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"};
		for (int i = 0; i < 12; i++) {
			month_columns += ColumnDescriptor(months[i], 8, 4);
			month_columns_wide += ColumnDescriptor(months[i], 8, 5); // 10, 5 in commonoutput
			month_columns_dec5 += ColumnDescriptor(months[i], 8, 5);
		}
		
		// Create the columns for each output file
		
		// *** ANNUAL OUTPUT VARIABLES ***
		ColumnDescriptors cmass_columns;
		cmass_columns += ColumnDescriptors(pfts, 8, 5);
		cmass_columns += ColumnDescriptor("Total", 8, 5);
		cmass_columns += ColumnDescriptors(landcovers, 13, 5);
		
		ColumnDescriptors nmass_columns;
		nmass_columns += ColumnDescriptors(pfts, 9, 6);
		nmass_columns += ColumnDescriptor("Total", 9, 6);
		nmass_columns += ColumnDescriptors(landcovers, 13, 5);
		
		create_output_table(out_agclitter, file_agclitter, cmass_columns);
		create_output_table(out_agnlitter, file_agnlitter, nmass_columns);
		
		ColumnDescriptors harvest_columns;
		harvest_columns += ColumnDescriptors(landcovers, 13, 5);
		harvest_columns += ColumnDescriptor("Total", 8, 5);

		create_output_table(out_cflux_harvest, file_cflux_harvest, harvest_columns);
		create_output_table(out_nflux_harvest, file_nflux_harvest, harvest_columns);
		create_output_table(out_cmass_leaf, file_cmass_leaf, cmass_columns);
		create_output_table(out_cmass_sap, file_cmass_sap, cmass_columns);
		create_output_table(out_cmass_heart, file_cmass_heart, cmass_columns);
		create_output_table(out_cmass_root, file_cmass_root, cmass_columns);
		
		ColumnDescriptors cpool_columns; // some are not really need, but lets write them out for info purposes
		// GCP wants:
		// Carbon in Vegetation	kg C m-2		cVeg
		// Carbon in Above-ground Litter Pool	kg C m-2		cLitter
		// Carbon in Soil (including below-ground litter)	kg C m-2	 cSoil
		// Note: GCP_wants the below ground litter in SoilC, hence have special GCP LitC and SoilC column
		// Carbon in Leaves	kg C m-2		cLeaf
		// Carbon in Wood	kg C m-2	including sapwood and hardwood.	 cWood (Note: lpjg incl. hard-, sapwood and coarse roots))
		// Carbon in Roots	kg C m-2	including fine and coarse roots. cRoot (Note: lpjg excl. coarse roots)
		// Carbon in Coarse Woody Debris	kg C m-2		cCwd
		cpool_columns += ColumnDescriptor("LeafC", 8, 5);
		cpool_columns += ColumnDescriptor("WoodC", 8, 5);
		cpool_columns += ColumnDescriptor("RootC", 8, 5);
		cpool_columns += ColumnDescriptor("DebtC", 8, 5);
		cpool_columns += ColumnDescriptor("CWDC", 8, 5);
		cpool_columns += ColumnDescriptor("AGLitC", 8, 5);
		cpool_columns += ColumnDescriptor("BGLitC", 8, 5);
		cpool_columns += ColumnDescriptor("LitC", 8, 5);
		cpool_columns += ColumnDescriptor("SoilC", 9, 5);
		create_output_table(out_cpool_gcp, file_cpool_gcp, cpool_columns);
		
		ColumnDescriptors npool_columns;
		// GCP wants:
		// Nitrogen in Vegetation	kg N m-2		nVeg  (w/o nlitter)
		// Nitrogen in Above-ground Litter Pool	kg N m-2		nLitter
		// Nitrogen in Soil (including below-ground litter)	kg N m-2		nSoil
		// Note: GCP_wants the litter N in other pools, hence add extra VegNGCP, LitNGCP, and SoilNGCP column
		// VegN w/o nlitter_gridcell and nlitter_gridcell splitted into an above ground (AGLitN) (added to LitN) and below ground litter BGLitN (added to SoilN)
		npool_columns += ColumnDescriptor("VegN", 9, 4);
		npool_columns += ColumnDescriptor("AGLitN", 9, 4);
		npool_columns += ColumnDescriptor("BGLitN", 9, 4);
		npool_columns += ColumnDescriptor("LitN", 9, 4); // GCP nLitter
		npool_columns += ColumnDescriptor("SoilN", 9, 4); // GCP nSoil
		create_output_table(out_npool_gcp, file_npool_gcp, npool_columns);
		
		//landcoverfrac
		ColumnDescriptors landcoverfrac_columns;
		landcoverfrac_columns += ColumnDescriptors(landcovers, 13, 5);
		
		// at present just for information purposes
		create_output_table(out_landcoverfrac, file_landcoverfrac, landcoverfrac_columns);
		
		//CROP YIELD
		ColumnDescriptors crop_columns;
		crop_columns += ColumnDescriptors(crop_pfts, 8, 3);
		
		create_output_table(out_gsirr, file_gsirr, crop_columns); //Per CFT irrigation water output - TP 03.09.15
		
		// *** MONTHLY OUTPUT VARIABLES ***
		create_output_table(out_mevtra, file_mevtra, month_columns_wide);
		//create_output_table(out_mevap, file_mevap, month_columns_wide);
		//create_output_table(out_mintercep, file_mintercep, month_columns_wide);
		create_output_table(out_mestc, file_mestc, month_columns_dec5);
		create_output_table(out_soiltemp, file_soiltemp, month_columns);
		
		// useful for tracking input climate problems
		create_output_table(out_mprec, file_mprec, month_columns);
		
		// *** MONTHLY PER PFT OUTPUT VARIABLES ***
		// insert the PFT name (e.g. "TeNE") into before the .out
		long position;
		pftlist.firstobj();
		while (pftlist.isobj) {
			Pft& pft=pftlist.getobj();
			if (file_mplai != "") {
				position = file_mplai.find(".out");
				create_output_table(out_mplai[pft.id], file_mplai.left(position) + xtring("_") + xtring(pft.name) + ".out", month_columns);
				// we don't write the previous used implementation out, remove comments if you want to see the difference
				//				create_output_table(out_mplai2[pft.id], file_mplai.left(position) + xtring("2_") + xtring(pft.name) + ".out", month_columns);
			}
			if (file_mpgpp != "") {
				position = file_mpgpp.find(".out");
				create_output_table(out_mpgpp[pft.id], file_mpgpp.left(position) + xtring("_") + xtring(pft.name) + ".out", month_columns_dec5);
			}
			if (file_mpnpp != "") {
				position = file_mpnpp.find(".out");
				create_output_table(out_mpnpp[pft.id], file_mpnpp.left(position) + xtring("_") + xtring(pft.name) + ".out", month_columns_dec5);
				//				ColumnDescriptors cmass_columns;
				//				cmass_columns += ColumnDescriptors(pfts, 8, 5);
				//				cmass_columns += ColumnDescriptor("Total", 8, 5);
				//				cmass_columns += ColumnDescriptors(landcovers, 13, 5);
				//				create_output_table(out_anpp2, "anpp2.out", cmass_columns);
				
			}
			if (file_mpestc != "") {
				position = file_mpestc.find(".out");
				create_output_table(out_mpestc[pft.id], file_mpestc.left(position) + xtring("_") + xtring(pft.name) + ".out", month_columns_dec5);
			}
			if (file_mpaet != "") {
				position = file_mpaet.find(".out");
				create_output_table(out_mpaet[pft.id], file_mpaet.left(position) + xtring("_") + xtring(pft.name) + ".out", month_columns_dec5); //-- MK: 5 digits
			}
			if (file_mpcmass_leaf != "") {
				position = file_mpcmass_leaf.find(".out");
				create_output_table(out_mpcmass_leaf[pft.id], file_mpcmass_leaf.left(position) + xtring("_") + xtring(pft.name) + ".out", month_columns_dec5);
			}
			if (file_mpcmass_root != "") {
				position = file_mpcmass_root.find(".out");
				create_output_table(out_mpcmass_root[pft.id], file_mpcmass_root.left(position) + xtring("_") + xtring(pft.name) + ".out", month_columns_dec5);
			}
			if (file_mpcmass_wood != "") {
				position = file_mpcmass_wood.find(".out");
				create_output_table(out_mpcmass_wood[pft.id], file_mpcmass_wood.left(position) + xtring("_") + xtring(pft.name) + ".out", month_columns_dec5);
			}
			if (file_mpcmass_veg != "") {
				position = file_mpcmass_veg.find(".out");
				create_output_table(out_mpcmass_veg[pft.id], file_mpcmass_veg.left(position) + xtring("_") + xtring(pft.name) + ".out", month_columns_dec5);
			}
			pftlist.nextobj();
		}
		
	}
	
	/// Local analogue of OutputRows::add_value for restricting output
	/** Use to restrict output to specified range of years
	 * (or other user-specified limitation)
	 *
	 * If only yearly output between, say 1961 and 1990 is requred, use:
	 * if (date.get_calendar_year() >= 1961 && date.get_calendar_year() <= 1990)
	 * (assuming the input module has set the first calendar year in the date object)
	 */
	void outlimit_gcp(OutputRows& out, const Table& table, double d) {
		//	int out_year_idx=nyear_spinup;
		//	if (param.isparam("out_year_idx")) out_year_idx=(int) param["out_year_idx"].num;
		
		if (date.year >= nyear_spinup) {
			out.add_value(table, d);
		}
	}
	
	void GCPOutput::outannual(Gridcell& gridcell) {
		// DESCRIPTION
		// Output of simulation results at the end of each year, or for specific years in
		// the simulation of each stand or grid cell. This function does not have to
		// provide any information to the framework.
		if (date.year < nyear_spinup) {
			return;
		}
		
		// sanity check
		if (npft > npftconst)
			fail("increase the guess.h npftconst value to at least %d and recompile\n", npft);
		
		double lon = gridcell.get_lon();
		double lat = gridcell.get_lat();
		
		// The OutputRows object manages the next row of output for each
		// output table
		OutputRows out(output_channel, lon, lat, date.get_calendar_year());
		
		Landcover& lc = gridcell.landcover;
		
		//double landcover_mplai[NLANDCOVERTYPES][npftconst][12]={{{0.0}}};
		double landcover_agclitter[NLANDCOVERTYPES]={0.0};
		double landcover_agnlitter[NLANDCOVERTYPES]={0.0};
		double landcover_cmass_leaf[NLANDCOVERTYPES]={0.0};
		double landcover_cmass_root[NLANDCOVERTYPES]={0.0};
		double landcover_cmass_sap[NLANDCOVERTYPES]={0.0};
		double landcover_cmass_heart[NLANDCOVERTYPES]={0.0};
		double landcover_cmass_wood[NLANDCOVERTYPES]={0.0};
//		double landcover_cmass_veg[NLANDCOVERTYPES]={0.0};
		double landcover_nmass_leaf[NLANDCOVERTYPES]={0.0};
		double landcover_nmass_sap[NLANDCOVERTYPES]={0.0};
		double landcover_nmass_heart[NLANDCOVERTYPES]={0.0};
		double landcover_nmass_root[NLANDCOVERTYPES]={0.0};
		double landcover_nmass_wood[NLANDCOVERTYPES]={0.0};
		double landcoverfrac[NLANDCOVERTYPES]={0.0};
		
		double mean_standpft_nmass=0.0;
		double mean_standpft_cmass_leaf=0.0;
		double mean_standpft_cmass_leaf_grass=0.0;
		double mean_standpft_nmass_leaf=0.0;
		double mean_standpft_agclitter=0.0;
		double mean_standpft_bgclitter=0.0;
		double mean_standpft_agnlitter=0.0;
		double mean_standpft_bgnlitter=0.0;
		double mean_standpft_cmass_wood=0.0;
		double mean_standpft_cmass_root=0.0;
		double mean_standpft_cmass_sap=0.0;
		double mean_standpft_cmass_heart=0.0;
		double mean_standpft_nmass_sap=0.0;
		double mean_standpft_nmass_heart=0.0;
		double mean_standpft_nmass_root=0.0;
		double mean_standpft_cmass_debt=0.0;
//		double mean_standpft_cmass_veg=0.0;
		
		double mean_standpft_gsirr=0.0; //Per CFT irrigation water output
		
		double nmass_gridcell=0.0;
		double agclitter_gridcell=0.0;
		double bgclitter_gridcell=0.0;
		double agnlitter_gridcell=0.0;
		double bgnlitter_gridcell=0.0;
		double cmass_wood_gridcell=0.0;
		double cmass_root_gridcell=0.0;
		double cmass_sap_gridcell=0.0;
		double cmass_heart_gridcell=0.0;
//		double cmass_veg_gridcell=0.0;
		double nmass_root_gridcell=0.0;
		double nmass_sap_gridcell=0.0;
		double nmass_heart_gridcell=0.0;
		double cmass_debt_gridcell=0.0;
		
		double cmass_leaf_gridcell=0.0;;
		double nmass_leaf_gridcell=0.0;
		
		// need to set to zero for each pft
		double standpft_nmass=0.0;
		double standpft_cmass_leaf=0.0;
		double standpft_cmass_leaf_grass=0.0;
		double standpft_nmass_leaf=0.0;
		
		double standpft_agclitter=0.0;
		double standpft_bgclitter=0.0;
		double standpft_agnlitter=0.0;
		double standpft_bgnlitter=0.0;
		
		double standpft_cmass_sap=0.0;
		double standpft_cmass_heart=0.0;
		double standpft_cmass_wood=0.0;
		double standpft_cmass_root=0.0;
//		double standpft_cmass_veg=0.0;
		double standpft_cmass_debt=0.0;
		double standpft_nmass_sap=0.0;
		double standpft_nmass_heart=0.0;
		double standpft_nmass_root=0.0;
		
		double standpft_gsirr=0.0; //Per CFT irrigation water output
		
		double standpft_mplai[npftconst][12]={{0.0}};
		double standpft_mpgpp[npftconst][12]={{0.0}};
		double standpft_mpnpp[npftconst][12]={{0.0}};
		double standpft_mpestc[npftconst][12]={{0.0}};
		double standpft_mpaet[npftconst][12]={{0.0}};
		double standpft_mpcmass_root[npftconst][12]={{0.0}};
		double standpft_mpcmass_leaf[npftconst][12]={{0.0}};
		double standpft_mpcmass_wood[npftconst][12]={{0.0}};
		double standpft_mpcmass_veg[npftconst][12]={{0.0}};
		
		double gcpft_mplai[npftconst][12]={{0.0}};
		double gcpft_mpphen[npftconst][12]={{0.0}};
		double gcpft_mpgpp[npftconst][12]={{0.0}};
		double gcpft_mpnpp[npftconst][12]={{0.0}};
		double gcpft_mpestc[npftconst][12]={{0.0}};
		double gcpft_mpaet[npftconst][12]={{0.0}};
		double gcpft_mpcmass_leaf[npftconst][12]={{0.0}};
		double gcpft_mpcmass_root[npftconst][12]={{0.0}};
		double gcpft_mpcmass_wood[npftconst][12]={{0.0}};
		double gcpft_mpcmass_veg[npftconst][12]={{0.0}};
		
		// *** Loop through PFTs ***
		
		pftlist.firstobj();
		while (pftlist.isobj) {
			
			Pft& pft=pftlist.getobj();
			
			mean_standpft_nmass=0.0;
			mean_standpft_cmass_leaf=0.0;
			mean_standpft_cmass_leaf_grass=0.0;
			mean_standpft_nmass_leaf=0.0;
			mean_standpft_gsirr=0.0;
			mean_standpft_agclitter=0.0;
			mean_standpft_bgclitter=0.0;
			mean_standpft_agnlitter=0.0;
			mean_standpft_bgnlitter=0.0;
			
			mean_standpft_cmass_wood=0.0;
			mean_standpft_cmass_sap=0.0;
			mean_standpft_cmass_heart=0.0;
			mean_standpft_cmass_root=0.0;
			mean_standpft_nmass_sap=0.0;
			mean_standpft_nmass_heart=0.0;
			mean_standpft_nmass_root=0.0;
			mean_standpft_cmass_debt=0.0;
			
			// Determine area fraction of stands where this pft is active:
			double active_fraction = 0.0;
			double active_fraction_lc[NLANDCOVERTYPES]={0.0};
			double total_fraction = 0.0;
			double sum_frac = 0.0;
			
			Gridcell::iterator gc_itr = gridcell.begin();
			
			while (gc_itr != gridcell.end()) {
				Stand& stand = *gc_itr;
				
				total_fraction += stand.get_gridcell_fraction();
				if (stand.pft[pft.id].active) {
					// active fraction of this pft in all stands over all landcovers
					// only matters if the same PFT is used in more than one landcover
					active_fraction += stand.get_gridcell_fraction();
					// active fraction of this pft in this landcover
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
				
				standpft_nmass=0.0;
				standpft_cmass_leaf=0.0;
				standpft_cmass_leaf_grass=0.0;
				standpft_nmass_leaf=0.0;
				
				standpft_agclitter=0.0;
				standpft_bgclitter=0.0;
				standpft_agnlitter=0.0;
				standpft_bgnlitter=0.0;
				
				standpft_cmass_sap=0.0;
				standpft_cmass_heart=0.0;
				standpft_cmass_wood=0.0;
				standpft_cmass_root=0.0;
//				standpft_cmass_veg=0.0;
				standpft_cmass_debt=0.0;
				standpft_nmass_sap=0.0;
				standpft_nmass_heart=0.0;
				standpft_nmass_root=0.0;
				
				standpft_gsirr=0.0; //Per CFT irrigation water output
				
				for (int m=0;m<12;m++) {
					standpft_mplai[pft.id][m]=0.0;
					standpft_mpgpp[pft.id][m]=0.0;
					standpft_mpnpp[pft.id][m]=0.0;
					standpft_mpestc[pft.id][m]=0.0;
					standpft_mpaet[pft.id][m]=0.0;
					standpft_mpcmass_leaf[pft.id][m]=0.0;
					standpft_mpcmass_root[pft.id][m]=0.0;
					standpft_mpcmass_wood[pft.id][m]=0.0;
					standpft_mpcmass_veg[pft.id][m]=0.0;
				}
				
				stand.firstobj();
				
				int npatches_mphen=0;
				// Loop through Patches
				while (stand.isobj) {
					Patch& patch = stand.getobj();
					Patchpft& patchpft = patch.pft[pft.id];
					Vegetation& vegetation = patch.vegetation;
					
					standpft_gsirr += patch.irrigation_y; //Per CFT irrigation water output - TP 03.09.15
					
					standpft_bgclitter += patchpft.cmass_litter_root;
					standpft_agclitter += patchpft.cmass_litter_leaf + patchpft.cmass_litter_sap + patchpft.cmass_litter_heart + patchpft.cmass_litter_repr;
					standpft_bgnlitter += patchpft.nmass_litter_root;
					standpft_agnlitter += patchpft.nmass_litter_leaf + patchpft.nmass_litter_sap + patchpft.nmass_litter_heart;
					
					int pft_nindiv=0;
					
					vegetation.firstobj();
					while (vegetation.isobj) {
						Individual& indiv=vegetation.getobj();
						
						if (indiv.id!=-1 && indiv.alive) {
							
							if (indiv.pft.id==pft.id) {
								
								pft_nindiv++;
								standpft_cmass_leaf += indiv.cmass_leaf;
								standpft_cmass_wood += indiv.cmass_wood();
								//standpft_cmass += indiv.ccont();
								standpft_nmass += indiv.ncont();
								
								standpft_nmass_leaf += indiv.cmass_leaf / indiv.cton_leaf_aavr;
								
								if (pft.lifeform == GRASS) {
									standpft_cmass_leaf_grass += indiv.cmass_leaf;
								}
								
								if(pft.landcover == CROPLAND) {
//									standpft_cmass_veg += indiv.cmass_leaf + indiv.cmass_root;
									if(indiv.cropindiv) {
//										standpft_cmass_veg += indiv.cropindiv->cmass_ho + indiv.cropindiv->cmass_agpool + indiv.cropindiv->cmass_stem;
										standpft_nmass_leaf += indiv.cropindiv->ynmass_leaf + indiv.cropindiv->ynmass_dead_leaf;
									}
								}	else {
//									standpft_cmass_veg += indiv.cmass_veg;
								}
								
								if(pft.landcover == CROPLAND) {
									standpft_cmass_root+=indiv.cmass_root;
									standpft_cmass_debt+=indiv.cmass_debt;
									if(indiv.cropindiv) {
										standpft_nmass_leaf += indiv.cropindiv->ynmass_leaf + indiv.cropindiv->ynmass_dead_leaf;
									}
									
								} else {
									//Note: wood might not work, herbacious have no sap and heart wood
									standpft_cmass_sap+=indiv.cmass_sap;
									standpft_cmass_heart+=indiv.cmass_heart;
									standpft_cmass_root+=indiv.cmass_root;
									standpft_nmass_sap+=indiv.nmass_sap;
									standpft_nmass_heart+=indiv.nmass_heart;
									standpft_nmass_root+=indiv.nmass_root;
									standpft_cmass_debt+=indiv.cmass_debt;
								}
							}
						}
						vegetation.nextobj();
					}
					
					if (pft_nindiv) {
						for (int m=0;m<12;m++) {
						}
					}
					
					double pestc_monthly = patch.fluxes.get_annual_flux(Fluxes::PESTC, pft.id)/12;
					
					for (int m=0;m<12;m++) {
						standpft_mpgpp[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::GPP, pft.id, m);
						standpft_mpnpp[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::NPP, pft.id, m);
						// monthsum(dlai)/ndayspermonth = monthly mean LAI
						standpft_mplai[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::LAI, pft.id, m)/(double) date.ndaymonth[m];
						// need to use an average pestc, since the estabalishement is reported only once in a year. //patch.fluxes.get_monthly_flux(Fluxes::PESTC,pft.id, m);
						standpft_mpestc[pft.id][m] += pestc_monthly;
						standpft_mpaet[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::AET, pft.id, m);
						
						// calculate monthly mean reported cmass pool for this patch
						standpft_mpcmass_leaf[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::CMASS_LEAF, pft.id, m)/(double) date.ndaymonth[m];
						standpft_mpcmass_root[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::CMASS_ROOT, pft.id, m)/(double) date.ndaymonth[m];
						standpft_mpcmass_wood[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::CMASS_WOOD, pft.id, m)/(double) date.ndaymonth[m];
						standpft_mpcmass_veg[pft.id][m] += patch.fluxes.get_monthly_flux(Fluxes::CMASS_VEG, pft.id, m)/(double) date.ndaymonth[m];
					}
					
					stand.nextobj();
				} // end of patch loop
				
				standpft_cmass_leaf/=(double)stand.npatch();
				standpft_cmass_leaf_grass/=(double)stand.npatch();
				
				standpft_cmass_wood/=(double)stand.npatch();
				standpft_cmass_sap/=(double)stand.npatch();
				standpft_cmass_heart/=(double)stand.npatch();
				standpft_cmass_root/=(double)stand.npatch();
//				standpft_cmass_veg/=(double)stand.npatch();
				standpft_cmass_debt/=(double)stand.npatch();
				
				standpft_nmass_leaf/=(double)stand.npatch();
				standpft_nmass_sap/=(double)stand.npatch();
				standpft_nmass_heart/=(double)stand.npatch();
				standpft_nmass_root/=(double)stand.npatch();
				
				standpft_agclitter/=(double)stand.npatch();
				standpft_agnlitter/=(double)stand.npatch();
				
				standpft_gsirr/=(double)stand.npatch();

				//Update landcover totals
				landcover_agclitter[stand.landcover]+=standpft_agclitter*stand.get_landcover_fraction();
				landcover_agnlitter[stand.landcover]+=standpft_agnlitter*stand.get_landcover_fraction();
				
				landcover_cmass_leaf[stand.landcover]+=standpft_cmass_leaf*stand.get_landcover_fraction();
				landcover_cmass_wood[stand.landcover]+=standpft_cmass_wood*stand.get_landcover_fraction();
				landcover_cmass_sap[stand.landcover]+=standpft_cmass_sap*stand.get_landcover_fraction();
				landcover_cmass_heart[stand.landcover]+=standpft_cmass_heart*stand.get_landcover_fraction();
				landcover_cmass_root[stand.landcover]+=standpft_cmass_root*stand.get_landcover_fraction();
//				landcover_cmass_veg[stand.landcover]+=standpft_cmass_veg*stand.get_landcover_fraction();
				
				landcover_nmass_leaf[stand.landcover]+=standpft_nmass_leaf*stand.get_landcover_fraction();
				landcover_nmass_sap[stand.landcover]+=standpft_nmass_sap*stand.get_landcover_fraction();
				landcover_nmass_heart[stand.landcover]+=standpft_nmass_heart*stand.get_landcover_fraction();
				landcover_nmass_root[stand.landcover]+=standpft_nmass_root*stand.get_landcover_fraction();
				
				//Update pft means for active stands
				if(active_fraction) {
					//mean_standpft_cmass += standpft_cmass * stand.get_gridcell_fraction() / active_fraction;
					//mean_standpft_nmass += standpft_nmass * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_cmass_leaf += standpft_cmass_leaf * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_cmass_leaf_grass += standpft_cmass_leaf_grass * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_cmass_wood += standpft_cmass_wood * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_cmass_sap += standpft_cmass_sap * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_cmass_heart += standpft_cmass_heart * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_cmass_root += standpft_cmass_root * stand.get_gridcell_fraction() / active_fraction;
//					mean_standpft_cmass_veg += standpft_cmass_veg * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_cmass_debt += standpft_cmass_debt * stand.get_gridcell_fraction() / active_fraction;
					
					mean_standpft_nmass_leaf += standpft_nmass_leaf * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_nmass_sap += standpft_nmass_sap * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_nmass_heart += standpft_nmass_heart * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_nmass_root += standpft_nmass_root * stand.get_gridcell_fraction() / active_fraction;
					
					mean_standpft_gsirr += standpft_gsirr * stand.get_gridcell_fraction() / active_fraction; //Per CFT irrigation water output - TP 03.09.15
					
					mean_standpft_agclitter += standpft_agclitter * stand.get_gridcell_fraction() / active_fraction;
					mean_standpft_agnlitter += standpft_agnlitter * stand.get_gridcell_fraction() / active_fraction;
					
					//Update pft mean for active stands in landcover
					if(active_fraction_lc[stand.landcover]) {
					}
				}
				
				// calculate the stands monthly means for the PFT w/ pft.id
				for (int m=0;m<12;m++) {
					standpft_mplai[pft.id][m]/=(double)stand.npatch();
					standpft_mpgpp[pft.id][m]/=(double)stand.npatch();
					standpft_mpnpp[pft.id][m]/=(double)stand.npatch();
					standpft_mpestc[pft.id][m]/=(double)stand.npatch();
					standpft_mpaet[pft.id][m]/=(double)stand.npatch();
					
					standpft_mpcmass_leaf[pft.id][m]/=(double)stand.npatch();
					standpft_mpcmass_root[pft.id][m]/=(double)stand.npatch();
					standpft_mpcmass_wood[pft.id][m]/=(double)stand.npatch(); // was missing: 2019-08-05/pa all mpcmass_wood_PFT.out mpcmass_veg_PFT.out are wrong before 2019-08-05
//					standpft_mpcmass_veg[pft.id][m]/=(double)stand.npatch();
				}
				
				if(active_fraction) {
					//					mean_standpft_anpp += standpft_anpp * stand.get_gridcell_fraction() / active_fraction;
					//					mean_standpft_cmass_leaf += standpft_cmass_leaf * stand.get_gridcell_fraction() / active_fraction;
					double fraction_of_gridcell_active = stand.get_gridcell_fraction() / active_fraction; // '/ active_fraction;' this will scale up as if it covers whole gridcell
					// 2018-06-05/pa added the '/ active_fraction to have the same handling as in the above mean_standpft* calcs, but one needs to multiply by landcover later on
					// sum the stand means weighted by their fractional cover within the gridcell
					for (int m=0;m<12;m++) {
						gcpft_mplai[pft.id][m]+=standpft_mplai[pft.id][m]*fraction_of_gridcell_active;
						gcpft_mpgpp[pft.id][m]+=standpft_mpgpp[pft.id][m]*fraction_of_gridcell_active;
						gcpft_mpnpp[pft.id][m]+=standpft_mpnpp[pft.id][m]*fraction_of_gridcell_active;
						gcpft_mpestc[pft.id][m]+=standpft_mpestc[pft.id][m]*fraction_of_gridcell_active;
						gcpft_mpaet[pft.id][m]+=standpft_mpaet[pft.id][m]*fraction_of_gridcell_active;
						
						gcpft_mpcmass_leaf[pft.id][m]+=standpft_mpcmass_leaf[pft.id][m]*fraction_of_gridcell_active;
						gcpft_mpcmass_root[pft.id][m]+=standpft_mpcmass_root[pft.id][m]*fraction_of_gridcell_active;
						gcpft_mpcmass_wood[pft.id][m]+=standpft_mpcmass_wood[pft.id][m]*fraction_of_gridcell_active;
						gcpft_mpcmass_veg[pft.id][m]+=standpft_mpcmass_veg[pft.id][m]*fraction_of_gridcell_active;
					}
					//					sum_frac+=stand.get_gridcell_fraction();
					
				}
				
				
				// Update gridcell totals
				double fraction_of_gridcell = stand.get_gridcell_fraction();
				
				cmass_leaf_gridcell+=standpft_cmass_leaf*fraction_of_gridcell;
				
				cmass_wood_gridcell+=standpft_cmass_wood*fraction_of_gridcell;
				cmass_sap_gridcell+=standpft_cmass_sap*fraction_of_gridcell;
				cmass_heart_gridcell+=standpft_cmass_heart*fraction_of_gridcell;
				cmass_root_gridcell+=standpft_cmass_root*fraction_of_gridcell;
//				cmass_veg_gridcell+=standpft_cmass_veg*fraction_of_gridcell;
				cmass_debt_gridcell+=standpft_cmass_debt*fraction_of_gridcell;

				agclitter_gridcell+=standpft_agclitter*fraction_of_gridcell;
				bgclitter_gridcell+=standpft_bgclitter*fraction_of_gridcell;
				
				nmass_gridcell+=standpft_nmass*fraction_of_gridcell;
				nmass_leaf_gridcell+=standpft_nmass_leaf*fraction_of_gridcell;
				nmass_sap_gridcell+=standpft_nmass_sap*fraction_of_gridcell;
				nmass_heart_gridcell+=standpft_nmass_heart*fraction_of_gridcell;
				nmass_root_gridcell+=standpft_nmass_root*fraction_of_gridcell;
				
				agnlitter_gridcell+=standpft_agnlitter*fraction_of_gridcell;
				bgnlitter_gridcell+=standpft_bgnlitter*fraction_of_gridcell;
				
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
								}
								break;
							case BARREN:
								break;
							case NATURAL:
								if (run[FOREST] || run[PASTURE]) {
								}
								break;
							case FOREST:
								if (run[NATURAL]) {
								}
								break;
							case URBAN:
								break;
							case PEATLAND:
								break;
							default:
								if (date.year == nyear_spinup)
									dprintf("Modify code to deal with landcover output!\n");
						}
					}
				}
			}
			
			if (pft.landcover == CROPLAND) {
				outlimit_gcp(out, out_gsirr,  mean_standpft_gsirr); //Per CFT irrigation water output - TP 03.09.15
			}
			
			outlimit_gcp(out,out_agclitter, mean_standpft_agclitter);
			outlimit_gcp(out,out_agnlitter, mean_standpft_agnlitter * M2_PER_HA);
			outlimit_gcp(out,out_cmass_leaf, mean_standpft_cmass_leaf);
			outlimit_gcp(out,out_cmass_sap, mean_standpft_cmass_sap);
			outlimit_gcp(out,out_cmass_heart, mean_standpft_cmass_heart);
			outlimit_gcp(out,out_cmass_root, mean_standpft_cmass_root);
//			outlimit_gcp(out,out_cmass_veg, mean_standpft_cmass_veg);

			pftlist.nextobj();
			
		} // *** End of PFT loop ***
		
		if (run_landcover) {
			for (int i=0;i<NLANDCOVERTYPES;i++) {
				if (run[i]) {
				}
			}
		}
		
		// Sum C fluxes, dead C pools and runoff across patches
		
		double mestc[12];
		double maet[12];
		double mevap[12];
		double mintercep[12];
		double mevtra[12];
		
		double surfsoillitterc,surfsoillittern,cwdc,cwdn,centuryc,centuryn,n_harv_slow,availn;
		
		double flux_charvest_lc[NLANDCOVERTYPES], flux_nharvest_lc[NLANDCOVERTYPES];
		double flux_charvest_gridcell=0.0;
		double flux_nharvest_gridcell=0.0;
		
		for (int i=0; i<NLANDCOVERTYPES; i++) {
			flux_charvest_lc[i]=0.0;
			flux_nharvest_lc[i]=0.0;
			landcoverfrac[i]=0.0;
		}
		
		for (int m=0;m<12;m++) {
			mestc[m]=0.0;
			maet[m]=0.0;
			mevap[m]=0.0;
			mintercep[m]=0.0;
			mevtra[m]=0.0;
		}
		
		surfsoillitterc = surfsoillittern = cwdc = cwdn = centuryc = centuryn = n_harv_slow = availn = 0.0;
		
		Gridcell::iterator gc_itr = gridcell.begin();
		
		// Loop through Stands
		while (gc_itr != gridcell.end()) {
			Stand& stand = *gc_itr;
			stand.firstobj();

			landcoverfrac[stand.landcover] += stand.get_gridcell_fraction();

			//Loop through Patches
			while (stand.isobj) {
				Patch& patch = stand.getobj();
				
				double to_gridcell_average = stand.get_gridcell_fraction() / (double)stand.npatch();
				
				flux_charvest_gridcell += patch.fluxes.get_annual_flux(Fluxes::HARVESTC)*to_gridcell_average;
				flux_nharvest_gridcell += patch.fluxes.get_annual_flux(Fluxes::HARVESTN)*to_gridcell_average;
				flux_charvest_lc[stand.landcover]+=patch.fluxes.get_annual_flux(Fluxes::HARVESTC)*to_gridcell_average; // no need to scale by landcover anymore as in the old charvest.out, it is now already the contribution to the total
				flux_nharvest_lc[stand.landcover]+=patch.fluxes.get_annual_flux(Fluxes::HARVESTN)*to_gridcell_average;

				for (int r = 0; r < NSOMPOOL-1; r++) {
					
					if(r == SURFMETA || r == SURFSTRUCT || r == SOILMETA || r == SOILSTRUCT){
						surfsoillitterc += patch.soil.sompool[r].cmass * to_gridcell_average;
						surfsoillittern += patch.soil.sompool[r].nmass * to_gridcell_average;
					}
					else if (r == SURFFWD || r == SURFCWD) {
						cwdc += patch.soil.sompool[r].cmass * to_gridcell_average;
						cwdn += patch.soil.sompool[r].nmass * to_gridcell_average;
					}
					else {
						centuryc += patch.soil.sompool[r].cmass * to_gridcell_average;
						centuryn += patch.soil.sompool[r].nmass * to_gridcell_average;
					}
				}
				
				double estc_monthly = patch.fluxes.get_annual_flux(Fluxes::ESTC)/12;
				
				// Monthly output variables
				for (int m=0;m<12;m++) {
					mestc[m] += estc_monthly*to_gridcell_average; // we use a monthly average from annual establishemnt. //patch.fluxes.get_monthly_flux(Fluxes::PESTC, m)*to_gridcell_average; // would just be in Dec or Jan
					
					maet[m] += patch.maet[m]*to_gridcell_average;
					mevap[m] += patch.mevap[m]*to_gridcell_average;
					mintercep[m] += patch.mintercep[m]*to_gridcell_average;
					mevtra[m] = maet[m]+mevap[m]+mintercep[m];
				}
				
				// if we have any more indiv things to calculate across stands and patches
				Vegetation& vegetation = patch.vegetation;
				vegetation.firstobj();
				while (vegetation.isobj) {
					Individual& indiv = vegetation.getobj();
					
					if (indiv.id != -1 && indiv.alive) {
						// add stuff here
						
					} // alive?
					
					vegetation.nextobj();
					
				} // while/vegetation loop
				stand.nextobj();
			} // patch loop
			++gc_itr;
		} // stand loop
		
		
		// Print gridcell totals to files
		outlimit_gcp(out, out_agclitter,agclitter_gridcell);
		outlimit_gcp(out, out_agnlitter,agnlitter_gridcell * M2_PER_HA);
		outlimit_gcp(out, out_cmass_leaf,cmass_leaf_gridcell);
		outlimit_gcp(out, out_cmass_sap,cmass_sap_gridcell);
		outlimit_gcp(out, out_cmass_heart,cmass_heart_gridcell);
		outlimit_gcp(out, out_cmass_root,cmass_root_gridcell);
		
		// Print landcover totals to files
		if (run_landcover) {
			for(int i=0;i<NLANDCOVERTYPES;i++) {
				if(run[i]) {
					outlimit_gcp(out, out_landcoverfrac, landcoverfrac[i]);
					outlimit_gcp(out, out_agclitter, landcover_agclitter[i]);
					outlimit_gcp(out, out_agnlitter, landcover_agnlitter[i] * M2_PER_HA);
					outlimit_gcp(out, out_cmass_leaf, landcover_cmass_leaf[i]);
					outlimit_gcp(out, out_cmass_sap, landcover_cmass_sap[i]);
					outlimit_gcp(out, out_cmass_heart, landcover_cmass_heart[i]);
					outlimit_gcp(out, out_cmass_root, landcover_cmass_root[i]);
					outlimit_gcp(out, out_cflux_harvest,  flux_charvest_lc[i]);
					outlimit_gcp(out, out_nflux_harvest,  flux_nharvest_lc[i] * M2_PER_HA);
				}
			}
		}

		outlimit_gcp(out, out_cflux_harvest, flux_charvest_gridcell);
		outlimit_gcp(out, out_nflux_harvest, flux_nharvest_gridcell * M2_PER_HA);

		// Print monthly output variables
		for (int m=0;m<12;m++) {
			outlimit_gcp(out, out_mestc, mestc[m]);
			outlimit_gcp(out, out_soiltemp, soiltemp[m]);
			//outlimit(out, out_mevap, mevap[m]); // are in commonoutput.cpp
			//outlimit(out, out_mintercep, mintercep[m]); // are in commonoutput.cpp
			outlimit_gcp(out, out_mevtra, mevtra[m]);
			outlimit_gcp(out,out_mprec, mprec[m]);
			
			pftlist.firstobj();
			while (pftlist.isobj) {
				Pft& pft=pftlist.getobj();
				
				outlimit_gcp(out, out_mplai[pft.id], gcpft_mplai[pft.id][m]);
				outlimit_gcp(out, out_mpgpp[pft.id], gcpft_mpgpp[pft.id][m]);
				outlimit_gcp(out, out_mpnpp[pft.id], gcpft_mpnpp[pft.id][m]);
				outlimit_gcp(out, out_mpestc[pft.id], gcpft_mpestc[pft.id][m]);
				outlimit_gcp(out, out_mpaet[pft.id], gcpft_mpaet[pft.id][m]);
				
				outlimit_gcp(out, out_mpcmass_leaf[pft.id], gcpft_mpcmass_leaf[pft.id][m]);
				outlimit_gcp(out, out_mpcmass_root[pft.id], gcpft_mpcmass_root[pft.id][m]);
				outlimit_gcp(out, out_mpcmass_wood[pft.id], gcpft_mpcmass_wood[pft.id][m]);
				outlimit_gcp(out, out_mpcmass_veg[pft.id], gcpft_mpcmass_veg[pft.id][m]); // no longer just sum leaf + root + wood, since crops have not just wood, this might not relate perfectly to the annual cmass.out (cmass.out should be the max in the year)
				
				pftlist.nextobj();
			}
		}
		
		// CHECK: LeafC + WoodC + RootC do not sum to VegC (VegC is reduced by carbon debt!)
		// could remove a fractional portion, but what if debt > sum of them?
		outlimit_gcp(out, out_cpool_gcp, cmass_leaf_gridcell); // leafC
		outlimit_gcp(out, out_cpool_gcp, cmass_wood_gridcell); // WoodC
		outlimit_gcp(out, out_cpool_gcp, cmass_root_gridcell); // RootC
		outlimit_gcp(out, out_cpool_gcp, cmass_debt_gridcell); // DebtC
		outlimit_gcp(out, out_cpool_gcp, cwdc); // coarse wood C CWDC
		outlimit_gcp(out, out_cpool_gcp, agclitter_gridcell); // agc separated AGLitC
		outlimit_gcp(out, out_cpool_gcp, bgclitter_gridcell); // agc separated BGLitC
		outlimit_gcp(out, out_cpool_gcp, agclitter_gridcell + surfsoillitterc + cwdc); // LitCGCP -- agclitter added (instead of total litter)
		outlimit_gcp(out, out_cpool_gcp, bgclitter_gridcell + centuryc); // SoilCGCP -- below ground litter added
		
		outlimit_gcp(out, out_npool_gcp, nmass_gridcell * M2_PER_HA); // VegNGCP w/o nlitter_gridcell (AG and BG), npool.out has nmass_gridcell + nlitter_gridcell
		outlimit_gcp(out, out_npool_gcp, agnlitter_gridcell * M2_PER_HA); // AGLitN
		outlimit_gcp(out, out_npool_gcp, bgnlitter_gridcell * M2_PER_HA); // BGLitN
		outlimit_gcp(out, out_npool_gcp, (agnlitter_gridcell + surfsoillittern + cwdn) * M2_PER_HA); // LitN GCP has AGLitN added
		outlimit_gcp(out, out_npool_gcp, (bgnlitter_gridcell + centuryn + availn) * M2_PER_HA); // SoilN GCP has BGLitN added
		
	}
	
	void GCPOutput::outdaily(Gridcell& gridcell) {
		
		if (date.year>=nyear_spinup) {

			if (date.day==0) {
				for (int m=0;m<12;m++) {
					soiltemp[m]=0.0;
					mprec[m]=0.0;
				}
			}
			
			int month = date.month;
			mprec[month] += gridcell.climate.prec; // we want total monthly /(double) date.ndaymonth[month];
			
			for(unsigned int i = 0; i < gridcell.size(); i++) { // through all stands in the gridcell
				Stand& stand = gridcell[i];
				for(unsigned int j = 0; j < stand.nobj; j++) { // through all patches in the stand
					Patch& patch = stand[j];
					double to_gridcell_average = stand.get_gridcell_fraction() / (double)stand.npatch();
					// soiltemp[month] += patch.soil.temp*to_gridcell_average  / (double) date.ndaymonth[month]; // for crop_ncep
					soiltemp[month] += patch.soil.get_soil_temp_25()*to_gridcell_average /(double) date.ndaymonth[month] ;
					
#ifndef GCP_INJECT_CODE
					gcp_dailyaccounting_patch(patch);
#endif

				}
			}
		}
	}
	
	void GCPOutput::openlocalfiles(Gridcell& gridcell) {
	}
	
	void GCPOutput::closelocalfiles(Gridcell& gridcell) {
	}

	// SSR: Dummy implementations to inherit purely virtual functions I added to OutputModule in GGCMI branch
	void GCPOutput::outharvest(Gridcell& gridcell) {
	}
	void GCPOutput::outharvest_justphupvd(Gridcell& gridcell) {
	}
	void GCPOutput::outannual_ggcmi(Gridcell& gridcell) {
	}
	void GCPOutput::openlocalfiles_ggcmi() {
	}
	void GCPOutput::closelocalfiles_ggcmi() {
	}
	
} // namespace
#endif

