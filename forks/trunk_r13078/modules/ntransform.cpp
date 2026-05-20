///////////////////////////////////////////////////////////////////////////////////////
/// \file ntransform.cpp
/// \brief Nitrogen transformation in soil - nitrification and denitrification
///
/// \author Xu-Ri and modified for LPJ-guess by Peter Eliasson, David Wårlind and Stefan Olin.
/// $Date: 2013-10-14 14:12:00 +0100 (Mon, 10 Sep 2013) $
///
/// This Source Code Form is subject to the terms of the Mozilla Public
/// License, v. 2.0. If a copy of the MPL was not distributed with this
/// file, You can obtain one at http://mozilla.org/MPL/2.0/.
///
///////////////////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////////////////
// MODULE SOURCE CODE FILE
//
// Module:                Nitrogen transformation processes in Soil
// Header file name:      ntransform.h
// Source code file name: ntransform.cpp
// Written by:            Stefan Olin, adopted from Xu-Ri 2007-08-18.
// Version dated:         2019.
//
// WHAT SHOULD THIS FILE CONTAIN?
// Module source code files should contain, in this order:
//   (1) a "#include" directive naming the framework header file. The framework header
//       file should define all classes used as arguments to functions in the present
//       module. It may also include declarations of global functions, consts and
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

#include "config.h"
#include "guess.h"
#include "driver.h"
#include "ntransform.h"
#include <assert.h>
#include <numeric>

/// Soil NH3 volatilization
/** Daily calculation of NH3 volatilization from soil
 *
 */
void nh3_volatilization(Patch& patch, Soil& soil, Climate& climate, double& n_budget_check) {

	double nh3_max = 0.0, f_nit_T = 0.0, nh3_inc = 0.0, f_pH = 0.0;  //-----JM-20231109
	double soil_T = soil.get_soil_temp_25();
	double wcont = soil.get_soil_water_upper();

	Gridcell& gridcell = patch.stand.get_gridcell();  //-----JM-20231109

	// calculating soil pH value, aprec = daily mean precip, based on annual average
	if (soil.soiltype.pH_value > 0.0) {     //-----JM-20231109
		soil.pH = soil.soiltype.pH_value;     //-----JM-20231109
	}
	else {
		soil.pH = 3810 / (762 + (climate.aprec_lastyear)) + 3.5; // Dawson -77
	}

	if (soil.pH > 6.5) {
		nh3_max = 0.025; // Maximum conversion ratio from NH4_mass to NH3 gas  0.025
	}
	else {
		nh3_max = 0.0025;   //-----JM-20231109   0.0025
	}

	// pH limiting factor for volatilization (Val Martin et al., 2023)
	if (soil.pH > 8.0) {                                         //-----JM-20231109
		f_pH = 1;                                                    //-----JM-20231109
	}

	if (soil.pH >= 5.0 && soil.pH <= 8.0) {                     //-----JM-20231109
		f_pH = 0.6 + 0.4 / 3 * (soil.pH - 5);                           //-----JM-20231109
	}                                                            //-----JM-20231109

	if (soil.pH < 5.0) {                                         //-----JM-20231109
		f_pH = 0.6;                                                  //-----JM-20231109
	}


	// N budget check
	// Total budget before N transformations
	n_budget_check = soil.NH4_mass + soil.NO3_mass + soil.NO2_mass + soil.NO_mass + soil.N2O_mass + soil.N2_mass;

	// temperature limiting factor for volatilization, 25 degree C == 1 (table 5, eqn 7, Xu-Ri 2008)
	if (soil_T >= -40.0) {
		f_nit_T = min(1.0, exp(308.56 * (1.0 / 71.02 - 1.0 / (soil_T + 46.02))));
	}
	else {
		f_nit_T = 0.0;
	}

	// NH3 increment (table 5, eqn 2, 3, 4, 6, Xu-Ri 2008)
	nh3_inc = min(soil.NH4_mass, nh3_max * min(1.0, wcont) * f_nit_T * soil.NH4_mass * f_pH * f_nit_T * (1.0 - min(1.0, wcont)));

	soil.NH4_mass -= nh3_inc;

	patch.fluxes.report_flux(Fluxes::NH3_SOIL, nh3_inc);

	// SSR: GGCMI
	patch.grs_n_losses += nh3_inc;

	// N budget check
	// N lost as NH3 gas
	n_budget_check -= nh3_inc;

	//////-----------------OUTPUT daily NH3-------------------JM-20231109

   // if (date.get_calendar_year()>=2001&&date.get_calendar_year()<=2001) { 
   //    
   //	if (date.day>=0&&date.day<=364) {
   //     
   //     if (patch.stand.id==0) {
   //  			
   //        static FILE *fptr11 = NULL;
   //                if (!fptr11) {
   //					fptr11 = fopen("NH3_volatilization_daily.out","w+");
   ////          fprintf(fptr11, "%s\n", "   Lon      Lat    year   day  patch.No  soil.water  soil.temp   f_t            soil.pH   f_pH            NH4.mass     NH4.mass.exch    max.conv.ratio   NH3.gas(gN/ha)");				
   //				}					
   ////          fprintf(fptr11, "%8g %8g %5d %4d %5d %12g %12g %12g %12g %12g %15g %15g %15g %15g\n",gridcell.get_lon(), gridcell.get_lat(),date.get_calendar_year(),date.day, patch.stand.id, wcont, soil_T, f_nit_T, soil.soiltype.pH_value, f_pH, soil.NH4_mass, soil.NH4_mass*f_nit_T*min(1.0, wcont), nh3_max, nh3_inc*10000000);
   //              
   //				if (date.day==0) {
   //				    fflush(fptr11);
   //               }		   			   			   
   // 
   //  }
   //  }
   //  }

	//////------------------OUTPUT ends here------------------JM-20231109  

}

/// Soil N substrate partitioning
/** Daily calculation of nitrogen substrate partition
 *  between aerobic and anaerobic soil fractions
 */
void substrate_partition(Soil& soil) {

	// An S-curve fitted to the linear increase in
	// denitrifier activity above roughly 50% WFPS with the steepest
	// change around 66% ending up at 100% around 75%.
	// Meaning that there is no nitrification at that WFPS.
	// Derived from Pilegaard 2013

	double wcont = soil.get_soil_water_upper();
	double wet = richards_curve(0.05, 0.95, 7.5, 0.5, wcont);

	soil.NH4_mass_w = soil.NH4_mass * wet;
	soil.NO3_mass_w = soil.NO3_mass * wet;
	soil.NO2_mass_w = soil.NO2_mass * wet;
	soil.N2O_mass_w = soil.N2O_mass * wet;
	soil.NO_mass_w = soil.NO_mass * wet;
	soil.labile_carbon_w = soil.labile_carbon * wet;

	soil.NH4_mass_d = soil.NH4_mass - soil.NH4_mass_w;
	soil.NO3_mass_d = soil.NO3_mass - soil.NO3_mass_w;
	soil.NO2_mass_d = soil.NO2_mass - soil.NO2_mass_w;
	soil.N2O_mass_d = soil.N2O_mass - soil.N2O_mass_w;
	soil.NO_mass_d = soil.NO_mass - soil.NO_mass_w;
	soil.labile_carbon_d = soil.labile_carbon - soil.labile_carbon_w;

}

/// Soil N nitrification
/** Daily calculation of nitrification, and nitrification
 *  induced trace gas emissions
 */
void nitrification(Patch& patch, Soil& soil, Climate& climate) {              //-----JM-20231109

	Gridcell& gridcell = patch.stand.get_gridcell();                            //-----JM-20231109

	double b = log(3.0) * 5.0;
	double a = exp(-b * 6.0 / 10.0);
	double wcont = soil.get_soil_water_upper();
	double act_dry = a * exp(wcont * b);
	double act_wet = max(0.0, 4.0 - 5.0 * wcont);
	double nit_act = min(act_dry, act_wet);
	double dry = soil.NH4_mass_d / soil.NH4_mass;                                //-----JM-20231109

	double f_nit_T, f_nit_pH, no3_inc, no_inc, n2o_inc, gross_nitrif;          //-----JM-20231109
	double soil_T = soil.get_soil_temp_25();

	// f_nit_T, temperature limiting factor for nitrification, 38 deg C == 1 (table 8, eqn 2, Xu-Ri 2008)
	if (soil_T < 70.0) {
		f_nit_T = min(1.0, pow((70.0 - soil_T) / (70.0 - 38.0), 12.0) * exp(12.0 * (soil_T - 38.0) / (70.0 - 38.0)));
	}
	else {
		f_nit_T = 0.0;
	}

	// calculating soil pH value, aprec = daily mean precip, based on annual average
	if (soil.soiltype.pH_value > 0.0) {                                                //-----JM-20231109
		soil.pH = soil.soiltype.pH_value;                                                //-----JM-20231109
	}
	else {                                                                             //-----JM-20231109
		soil.pH = 3810 / (762 + (climate.aprec_lastyear)) + 3.5;                         //-----JM-20231109
	}

	// pH limiting factor for gross nitrification rate (Parton et al., 1996)
	f_nit_pH = 0.56 + atan(3.1415926 * 0.45 * (soil.pH - 5)) / 3.1415926;                    //-----JM-20231109

	// gross nitrification rate, NH4_mass converted to NO3_mass (table 8, eqn 1, Xu-Ri 2008)
	no3_inc = f_nitri_max * nit_act * f_nit_T * f_nit_pH * soil.NH4_mass_d;   //-----JM-20231109
	gross_nitrif = no3_inc;
	soil.NH4_mass_d -= no3_inc;

	double ngas_inc = f_nitri_gas_max * no3_inc;                                       //-----JM-20231109

	double wfps = soil.wfps(0);

	// Pilegaard 2013
	// only NO and N2O in nitrification 
	double f_no = richards_curve(1.0, 0.5, 20.0, 0.375, wfps);

	no_inc = f_no * ngas_inc;
	no3_inc -= no_inc;
	soil.NO_mass_d += no_inc;

	n2o_inc = ngas_inc - no_inc;
	no3_inc -= n2o_inc;
	soil.N2O_mass_d += n2o_inc;

	// New NO3-
	soil.NO3_mass_d += no3_inc;

	// soil.NO3_mass_d += soil.NO2_mass_d;                                             //-----JM-20231109
	// soil.NO2_mass_d = 0.0;                                                          //-----JM-20231109

	// Report gross nitrification
	patch.fluxes.report_flux(Fluxes::GROSS_NITRIF, gross_nitrif);

	//////-----------------OUTPUT daily nitirfication-------------------JM-20231109

  // if (date.get_calendar_year()>=2001&&date.get_calendar_year()<=2003) {
  //    
  //	if (date.day>=0&&date.day<=364) {
  //     
  //     if (patch.stand.id==0) {  // site-level as 0, global level as 1
  //        
  //				static FILE *fptr22 = NULL;
  //                if (!fptr22) {
  //					fptr22 = fopen("Nitrification_daily.out","w+");
  ////          fprintf(fptr22, "%s\n", "   Lon      Lat    year   day  patch.No  soil.water   soil.wfps    f_w           f_t    f_nitri_max   dry_frac   NH4_mass_d    nitri_gas_max_frac  Ngas.pot  NO_fraction  NOgas.pot  N2Ogas.pot");				
  //				}					
  ////          fprintf(fptr22, "%8g %8g %5d %4d %5d %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g\n",gridcell.get_lon(), gridcell.get_lat(),date.get_calendar_year(),date.day, patch.stand.id, wcont, wfps, nit_act, f_nit_T, f_nitri_max, dry, soil.NH4_mass_d, f_nitri_gas_max, ngas_inc, f_no, no_inc, n2o_inc);
  //              
  //				if (date.day==0) {
  //				    fflush(fptr22);
  //               }		
  //  }
  //  }
  //  }

   //////------------------OUTPUT ends here------------------JM-20230823   



}

/// Soil N denitrification
/** Daily calculation of denitrification rate, and denitrification
 *  induced trace gas emissions
 */
void denitrification(Patch& patch, Soil& soil, Climate& climate) {                       //-----JM-20231109

	Gridcell& gridcell = patch.stand.get_gridcell();                                      //-----JM-20231109

	double soil_T = soil.get_soil_temp_25();
	double wcont = soil.get_soil_water_upper();
	// used to remove the per m3 from the constants KC and KN.
	double water_cont_m3 = wcont * soil.soiltype.gawc[0] / 1000.0;

	double wfps_upper = soil.wfps(0);

	double f_den_T, f_N_no3, f_LC, f_den_pH_no3, no2_inc, no_inc, n2o_inc, ngas_inc, gross_denitrif, n2_inc;  //-----JM-20231109

	double f_den_w, f_N_no2, f_den_pH_ngas, f_n2o_no_w, f_n2o_n2_T, f_n2o_n2_w, f_n2o_n2_pH, no_frac;  //-----JM-20231109

	if (water_cont_m3 > 0.0 && wfps_upper > 0.4) {

		// temperature limiting factor for denitrification (table S1, eqn 13, Ma et al., 2022 in JAMES)
		if (soil_T >= -40.0) {
			f_den_T = min(1.0, exp(-1 * (soil_T - 37) * (soil_T - 37) / (25 * 25)));                                 //-----JM-20231109
		}
		else {
			f_den_T = 0.0;
		}
		// Effect of labile carbon availability on denitrification (table 9, eqn 2, Xu-Ri 2008)
		f_LC = soil.labile_carbon_w / (k_C * water_cont_m3 + soil.labile_carbon_w);                   //-----JM-20231109

		// Effect of N availability on denitrification (table 9, eqn 2, Xu-Ri 2008)     
		f_N_no3 = soil.NO3_mass_w / (k_N * water_cont_m3 + soil.NO3_mass_w);                          //-----JM-20231109


		// calculating soil pH value, aprec = daily mean precip, based on annual average
		if (soil.soiltype.pH_value > 0.0) {                                                              //-----JM-20231109
			soil.pH = soil.soiltype.pH_value;                                                              //-----JM-20231109
		}
		else {                                                                                           //-----JM-20231109
			soil.pH = 3810 / (762 + (climate.aprec_lastyear)) + 3.5;                                       //-----JM-20231109
		}

		// Effect of soil pH on NO3- denitrification (table S1, eqn 21, Ma et al., 2022 in JAMES)
		f_den_pH_no3 = 1 - 0.6 / (1 + exp((soil.pH - 5.0) / 1.5));                                              //-----JM-20231109    


		// Gross denitrification ratio NO3 to NO2 (table 9, eqn 3, Xu-Ri 2008)
		no2_inc = min(soil.NO3_mass_w, soil.NO3_mass_w * f_denitri_max * f_LC * f_den_T * f_N_no3 * f_den_pH_no3);  //-----JM-20231109

		gross_denitrif = no2_inc;
		soil.NO3_mass_w -= no2_inc;
		soil.NO2_mass_w += no2_inc;

		// Gross transformation of NO2- to N2 (table 9, eqn 4, Xu-Ri 2008)

		// Denitrification rate dependence on moisture (table S1, eqn 17, Ma et al., 2022 in JAMES)
		f_den_w = min(1.0, 0.624 + 0.8 * atan(0.45 * 3.1415926 * (10 * wfps_upper - 8.0)) / 2.85);                   //-----JM-20231109

		f_N_no2 = soil.NO2_mass_w / (k_N * water_cont_m3 + soil.NO2_mass_w);


		// pH limiting factor for Gross transformation of NO2- to N2 (Blanc-Betes et al., 2020; Wagena et al., 2017)
		if (soil.pH >= 7.0) {                                                                            //-----JM-20231109
			f_den_pH_ngas = 1;                                                                             //-----JM-20231109
		}

		if (soil.pH > 4.0 && soil.pH < 7.0) {                                                           //-----JM-20231109
			f_den_pH_ngas = 0.001 + (soil.pH - 4) / 3;                                                       //-----JM-20231109
		}                                                                                                //-----JM-20231109

		if (soil.pH <= 4.0) {                                                                            //-----JM-20231109
			f_den_pH_ngas = 0.001;                                                                         //-----JM-20231109
		}

		ngas_inc = min(soil.NO2_mass_w, soil.NO2_mass_w * f_denitri_gas_max * f_LC * f_den_w * f_den_T * f_N_no2 * f_den_pH_ngas);

		soil.NO2_mass_w -= ngas_inc;

		f_n2o_no_w = max(0.0, min(1.0, 3.3333 * wfps_upper - 1.0000));                                   //-----JM-20231109

		f_n2o_n2_T = 1.0 / (1.0 + exp((soil_T - 5.0) / 10.0));                                           //-----JM-20231109

		f_n2o_n2_w = richards_curve(1.0, 0.0, 62.0, 0.875, wfps_upper);

		f_n2o_n2_pH = min(1.0, 7.23 * exp(-0.497 * soil.pH));                                            //-----JM-20231109  


		// Above 0.7 WFPS, no NO is produced and below the same threshold no N2 production. Pilegaard 2013
		if (wfps_upper < 0.7) {                                                                          //-----JM-20231109
			n2_inc = 0.0;
			no_frac = 1 / (1 + f_n2o_no_w);                                                                   //-----JM-20231109      
			no_inc = ngas_inc * no_frac;                                                                   //-----JM-20231109
			n2o_inc = ngas_inc - no_inc;
		}
		else {
			no_inc = 0.0;
			n2o_inc = ngas_inc * f_n2o_n2_w * f_n2o_n2_T * f_n2o_n2_pH;                                    //-----JM-20231109
			n2_inc = ngas_inc - n2o_inc;
		}

		soil.NO_mass_w += no_inc;
		soil.N2O_mass_w += n2o_inc;
		soil.N2_mass += n2_inc;


		//////------------OUTPUT daily denitrification---------JM-20231109

// if (date.get_calendar_year()>=2001&&date.get_calendar_year()<=2003) {
//    
//	if (date.day>=0&&date.day<=364) {
//     
//     if (patch.stand.id==0) {
//    
//				static FILE *fptr33 = NULL;
//                if (!fptr33) {
//					fptr33 = fopen("Denitrification_daily.out","w+");
////          fprintf(fptr33, "%s\n", "   Lon      Lat    year   day  patch.No  soil.water  soil.water.m3    Kc         Kn     LC_mass_w    NO3_mass_w          f_t        f_LC       f_N_no3   f_denitri_max  NO2_mass_w     f_w         f_N_no2  denitri_gas_max_frac  Ngas.pot  NO_fraction   NOgas.pot  N2O_fraction  f_n2o_n2_T  N2Ogas.pot    N2gas.pot");				
//				}					
////          fprintf(fptr33, "%8g %8g %5d %4d %5d %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g\n",gridcell.get_lon(), gridcell.get_lat(),date.get_calendar_year(),date.day, patch.stand.id, wcont, water_cont_m3, k_C, k_N, soil.labile_carbon_w, soil.NO3_mass_w, f_den_T, f_LC, f_N_no3, f_denitri_max, soil.NO2_mass_w, f_den_w,f_N_no2, f_denitri_gas_max, ngas_inc, no_frac, no_inc, f_n2o_n2_w, f_n2o_n2_T, n2o_inc, n2_inc);
//              
//				if (date.day==0) {
//				    fflush(fptr33);
//               }		   			   			   
// 
//  }
//  }
//  }

 //////-------------------OUTPUT ends here------------------JM-20231109 


	}
	else {
		gross_denitrif = 0.0;
	}
	// Report fluxes of gross denitrification
	patch.fluxes.report_flux(Fluxes::GROSS_DENITRIF, gross_denitrif);
}

/// Soil N gas emissions
/** Daily calculation of soil N gas emissions.
 */
void n_gas_emission(Patch& patch, Fluxes& fluxes, Soil& soil, double& n_budget_check) {

	Gridcell& gridcell = patch.stand.get_gridcell();                                                     //-----JM-20231109

	//for book keeping
	soil.labile_carbon = soil.labile_carbon_w + soil.labile_carbon_d;

	double soil_T = soil.get_soil_temp_25();
	double wcont = soil.get_soil_water_upper();
	double ftemp, no_d_flux_inc, n2o_d_flux_inc, no_w_flux_inc, n2o_w_flux_inc, n2_flux_inc;
	double no_flux_inc, n2o_flux_inc;	                                                                   //-----JM-20231109
	double net_nitrif = 0.0;
	double net_denitrif = 0.0;

	// ftemp, temperature limiting factor for gas emission, 25 degree C == 1 (table 10, eqn 1, Xu-Ri 2008)
	if (soil_T >= -40.0) {
		ftemp = min(1.0, exp(308.56 * (1.0 / 71.02 - 1.0 / (soil_T + 46.02))));
	}
	else {
		ftemp = 0.0;
	}

	// Nitrification fluxes
	// Daily NO gas released from aerobic soil to atmosphere (table 10, eqn 2, Xu-Ri 2008)
	no_d_flux_inc = ftemp * (1.0 - min(1.0, wcont)) * soil.NO_mass_d;
	soil.NO_mass_d -= no_d_flux_inc;
	net_nitrif += no_d_flux_inc;
	// Daily N2O gas released from aerobic soil to atmosphere (table 10, eqn 2, Xu-Ri 2008)
	n2o_d_flux_inc = ftemp * (1.0 - min(1.0, wcont)) * soil.N2O_mass_d;
	soil.N2O_mass_d -= n2o_d_flux_inc;
	net_nitrif += n2o_d_flux_inc;


	// Denitrification fluxes
	// Daily NO gas released from anaerobic soil to atmosphere (table 10, eqn 2, Xu-Ri 2008)
	no_w_flux_inc = ftemp * (1.0 - min(1.0, wcont)) * soil.NO_mass_w;
	soil.NO_mass_w -= no_w_flux_inc;
	net_denitrif += no_w_flux_inc;
	// Daily N2O gas released from anaerobic soil to atmosphere (table 10, eqn 2, Xu-Ri 2008)
	n2o_w_flux_inc = ftemp * (1.0 - min(1.0, wcont)) * soil.N2O_mass_w;
	soil.N2O_mass_w -= n2o_w_flux_inc;
	net_denitrif += n2o_w_flux_inc;

	// Daily N2 gas released from soil to atmosphere (table 10, eqn 2, Xu-Ri 2008)
	n2_flux_inc = ftemp * (1.0 - min(1.0, wcont)) * soil.N2_mass;
	soil.N2_mass -= n2_flux_inc;

	// SSR: GGCMI
	patch.semis_n2o += n2o_d_flux_inc + n2o_w_flux_inc;
	patch.grs_n_losses += no_d_flux_inc + no_w_flux_inc + patch.semis_n2o;
	patch.semis_n2 += n2_flux_inc;

	patch.fluxes.report_flux(Fluxes::NO_SOIL, no_d_flux_inc + no_w_flux_inc);
	patch.fluxes.report_flux(Fluxes::N2O_SOIL, n2o_d_flux_inc + n2o_w_flux_inc);

	patch.fluxes.report_flux(Fluxes::N2_SOIL, n2_flux_inc);
	patch.fluxes.report_flux(Fluxes::NET_NITRIF, net_nitrif);
	patch.fluxes.report_flux(Fluxes::NET_DENITRIF, net_denitrif);

	// substrates after N gas emissions
	soil.NH4_mass = soil.NH4_mass_w + soil.NH4_mass_d;
	soil.NO3_mass = soil.NO3_mass_w + soil.NO3_mass_d;
	soil.NO2_mass = soil.NO2_mass_w + soil.NO2_mass_d;
	soil.NO_mass = soil.NO_mass_w + soil.NO_mass_d;
	soil.N2O_mass = soil.N2O_mass_w + soil.N2O_mass_d;
	soil.labile_carbon = soil.labile_carbon_w + soil.labile_carbon_d;

	// N budget check
	// N lost through emissions and existing pool sizes
	n_budget_check -= (no_d_flux_inc + no_w_flux_inc + n2o_d_flux_inc + n2o_w_flux_inc + n2_flux_inc +
		soil.NH4_mass + soil.NO3_mass + soil.NO2_mass + soil.NO_mass + soil.N2O_mass + soil.N2_mass);

	//////-----------------OUTPUT daily Ngases--------------JM-20231109
   // 
   // if (date.get_calendar_year()>=2001&&date.get_calendar_year()<=2003) {
   //    
   //	if (date.day>=0&&date.day<=364) {
   //     
   //     if (patch.stand.id==0) {
   //    
   //				static FILE *fptr44 = NULL;
   //                if (!fptr44) {
   //					fptr44 = fopen("Ngases_daily.out","w+");
   ////          fprintf(fptr44, "%s\n", "   Lon      Lat    year   day  patch.No  soil.water  soil.temp    f_w           f_t      NOgas.nit     NOgas.den  NOgas.total  NOgas.nit.frac  N2Ogas.nit N2Ogas.den   N2Ogas.total  N2Ogas.nit.frac  N2gas.den (gN/ha)");				
   //				}					
   ////          fprintf(fptr44, "%8g %8g %5d %4d %5d %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g %12g\n",gridcell.get_lon(), gridcell.get_lat(),date.get_calendar_year(),date.day, patch.stand.id, wcont, soil_T, 1-min(1.0,wcont), ftemp, no_d_flux_inc*10000000, no_w_flux_inc*10000000, (no_d_flux_inc + no_w_flux_inc)*10000000,no_d_flux_inc/(no_d_flux_inc + no_w_flux_inc), n2o_d_flux_inc*10000000, n2o_w_flux_inc*10000000, (n2o_d_flux_inc + n2o_w_flux_inc)*10000000, n2o_d_flux_inc/(n2o_d_flux_inc + n2o_w_flux_inc), n2_flux_inc*10000000);
   //              
   //				if (date.day==0) {
   //				    fflush(fptr44);
   //               }	
   //               
   //      }
   //    
   //    }           	
   //  }

	//////------------------OUTPUT ends here------------------JM-20231109 


}


/// N transformation processes in soil
/** Daily calculation of nitrification, denitrification, and trace gases emissions.
 *  To be called each simulation day for each modelled area or patch, following update
 *  of soil organic matter dynamic submodel.
 */
void ntransform(Patch& patch, Climate& climate) {
	if (ifntransform) {
		const double EPS = 1.0e-14;
		double n_budget_check;

		// Obtain reference to Soil object
		Soil& soil = patch.soil;

		// Obtain referenc to flux object
		Fluxes& fluxes = patch.fluxes;

		// NH3 volatilization
		nh3_volatilization(patch, soil, climate, n_budget_check);

		// N substrate partition
		substrate_partition(soil);

		// Nitrification
		nitrification(patch, soil, climate);      //-----------JM-20231109

		// Denitrification
		denitrification(patch, soil, climate);    //-----------JM-20231109

		// N gas emission
		n_gas_emission(patch, fluxes, soil, n_budget_check);

		// Warning if soil N transform does not hold mass balance
		assert(fabs(n_budget_check) < EPS);
	}
}



//////////////////////////////////////////////////////////////////////////
// REFERENCES
//
// Xu-Ri & Prentice IC 2008 Terrestrial nitrogen cycle simulated with a
//    dynamic global vegetation model. Global Change Biology 14,1745-1764.
// Dawson, G. A. (1977). "Atmospheric Ammonia from Undisturbed Land." 
//    Transactions-American Geophysical Union 58(6): 554-554.
// Pilegaard K. 2013.  Processes regulating nitric oxide emissions from soils.
// 	  Philosophical Transactions of the Royal Society of London B: Biological Sci-
//    ences, 368(1621), 2013. ISSN 0962-8436. doi: 10.1098/rstb.2013.0126.
// K. L. Weier et al. 1993. Denitrification and the dinitrogen/nitrous oxide
//    ratio as affected by soil water, available carbon, and nitrate.
//    Soil Science Society of America Journal, 57 (1):66–72.



