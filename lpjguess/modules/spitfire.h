///////////////////////////////////////////////////////////////////////////////////////
// MODULE HEADER FILE
//
// Module:                Fire: calculation of bruned area, fluxes and birned biomass
//                        Version adapted from spitfire by Kirsten Thonicke
// Header file name:      fire.h
// Source code file name: fire.cpp
// Written by:            Veiko Lehsten
// Version dated:         2006-11-22
//
// WHAT SHOULD THIS FILE CONTAIN?
// Module header files need normally contain only declarations of functions defined in
// the module that are to be accessible to the calling framework or to other modules.

#ifndef LPJ_GUESS_SPITFIRE_H
#define LPJ_GUESS_SPITFIRE_H

#include "guess.h"

// exported to calculate FBD for SOM pools in transfer litter in somdynam.cpp
double fuel_bulk_density(Pft& pft, double grass_biomass_kgDM, double gdd5);

void spitfire_daily(Patch& patch,Climate& climate);

void spitfire_dailyaccounting(Stand& stand, Climate& climate);

void dailyaccounting_gridcell_spitfire(Gridcell& gridcell);

// exported for use in somdynamics to set default values for SOM pools with sero or very little carbon
void set_standard_SOM_values(Sompool& pool);



#endif
