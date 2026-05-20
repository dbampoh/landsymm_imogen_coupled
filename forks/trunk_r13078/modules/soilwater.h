///////////////////////////////////////////////////////////////////////////////////////
/// \file soilwater.h
/// \brief Soil hydrology and snow
///
/// Version including evaporation from soil surface, based on work by Dieter Gerten,
/// Sibyll Schaphoff and Wolfgang Lucht, Potsdam
///
/// \author Ben Smith
/// $Date$
///
///////////////////////////////////////////////////////////////////////////////////////

// WHAT SHOULD THIS FILE CONTAIN?
// Module header files need normally contain only declarations of functions defined in
// the module that are to be accessible to the calling framework or to other modules.

#ifndef LPJ_GUESS_SOILWATER_H
#define LPJ_GUESS_SOILWATER_H

#include "guess.h"
void get_soil_water_status(Soil soil, int nlayers_to_use, double& total_potential,
						   double *Faw_layer, double *ice_layer, double *potential_layer,
						   bool& negative_potential);
void infiltrate_upland(Patch& patch);
void saturate_nonpeat_wetlands(Patch& patch);
void initial_infiltration(Patch& patch, Climate& climate);
void irrigation(Patch& patch);
void soilwater(Patch& patch, Climate& climate);

#endif // LPJ_GUESS_SOILWATER_H
