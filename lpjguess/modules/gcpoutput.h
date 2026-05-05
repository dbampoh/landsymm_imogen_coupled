///////////////////////////////////////////////////////////////////////////////////////
/// \file gcpoutput.h
/// \brief Output module for the GCP output information
/// 
/// \author Peter Anthoni
/// $Date: $
///
///////////////////////////////////////////////////////////////////////////////////////

#ifndef LPJ_GUESS_GCP_OUTPUT_H
#define LPJ_GUESS_GCP_OUTPUT_H

#include "guess.h"
#include "outputmodule.h"
#include "outputchannel.h"
#include "gutil.h"

#ifdef GCP

#define GCP_INJECT_CODE
// option to inject some calls into the simulation_day() and growth() function.
// injecting has the advantage that the data are tracked within the simulation_day(), but requires code changes there
// not injecting has the disadvantege that indivs killed in growth() are no longer present on day 364 in outdaily()
// but that is similar to the situation in any output outannual().

// this would need to be injected into the growth.cpp:growth() into if(!killed) { ... } where the reported Fluxes:ESTC is.
void gcp_growth_accounting_estc(Individual& indiv);

// gcp accounting during the simulation, need to be injected into the framework.cpp:simulation_day()
// somewhere after the daily calc. but before growth()!!
void gcp_dailyaccounting_patch(Patch& patch);

namespace GuessOutput {

/// Output module for the GCP output files
class GCPOutput : public OutputModule {
public:

	GCPOutput();

	~GCPOutput();

	// implemented functions inherited from OutputModule
	// (see documentation in OutputModule)

	void init();

	void outannual(Gridcell& gridcell);

	void outdaily(Gridcell& gridcell);

private:

	/// Defines all output tables
	void openlocalfiles(Gridcell& gridcell);

	void define_output_tables();

	void closelocalfiles(Gridcell& gridcell);
	
	// SSR: Dummy implementations to inherit purely virtual functions I added to OutputModule in GGCMI branch
	void outharvest(Gridcell& gridcell);
    void outharvest_justphupvd(Gridcell& gridcell);
	void outannual_ggcmi(Gridcell& gridcell);
    void openlocalfiles_ggcmi();
    void closelocalfiles_ggcmi();

	// Output file names ...
	xtring file_mplai, file_mpgpp,file, file_mpnpp, file_mpestc, file_mpaet, file_mestc, file_soiltemp;

	xtring file_mpcmass_leaf,file_mpcmass_root,file_mpcmass_wood,file_mpcmass_veg; // stem and root, should not change within year
	
	xtring file_agclitter, file_agnlitter, file_cpool_gcp, file_npool_gcp;
	
	xtring file_cflux_harvest, file_nflux_harvest;
	xtring file_landcoverfrac;
	xtring file_gsirr;
	xtring file_mevtra, /* file_mevap, file_mintercep, */ file_mprec;
	xtring file_cmass_leaf,file_cmass_sap,file_cmass_heart,file_cmass_root,file_cmass_veg;

	// Output tables
	Table out_mplai[npftconst], out_mpgpp[npftconst], out_mpnpp[npftconst], out_mpestc[npftconst], out_mpaet[npftconst], out_mestc, out_soiltemp;
	Table out_mpcmass_leaf[npftconst],out_mpcmass_root[npftconst],out_mpcmass_wood[npftconst],out_mpcmass_veg[npftconst];

	Table out_agclitter, out_agnlitter, out_cpool_gcp, out_npool_gcp;
	
	Table out_cflux_harvest, out_nflux_harvest;
	Table out_landcoverfrac, out_gsirr;
	Table out_mevtra, /* out_mevap, out_mintercep, */ out_mprec;
	Table out_cmass_leaf,out_cmass_sap,out_cmass_heart,out_cmass_root, out_cmass_veg;

	double mprec[12];
	double soiltemp[12];
	
};

}
#endif

#endif // LPJ_GUESS_GCP_OUTPUT_H
