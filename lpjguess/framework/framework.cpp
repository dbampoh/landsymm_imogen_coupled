///////////////////////////////////////////////////////////////////////////////////////
/// \file framework.cpp
/// \brief Implementation of the framework() function
///
/// \author Ben Smith
/// $Date$
///
///////////////////////////////////////////////////////////////////////////////////////

#include "config.h"
#include "framework.h"
#include "commandlinearguments.h"
#include "guessserializer.h"
#include "parallel.h"

#include "inputmodule.h"
#include "driver.h"
#include "canexch.h"
#include "soilwater.h"
#include "somdynam.h"
#include "growth.h"
#include "vegdynam.h"
#include "blaze.h"
#include "simfire.h"
#include "landcover.h"
#include "bvoc.h"
#include "commonoutput.h"
#include "soilmethane.h"
#include "spitfire.h"
//#include "climatemodel.h"

#ifdef GCP
#include "gcpoutput.h"
#endif

#include <memory>

#include <string.h>
#include <sstream>
#include <sys/stat.h>
//#include "imogenlogger.h"

namespace {
	// I had the ff. in the gutil.cpp/h, but that one is somehow svn referenced
	// so just define am local.
	
	// Converts a value to a string
	template <typename T> xtring to_xtring(T value) {
		std::ostringstream os;
		os << value;
		return xtring(os.str().c_str());
	}
	
	
	static void _mkdir(const char *dir, int mode) {
		char tmp[256];
		char *p = NULL;
		size_t len;
		
		snprintf(tmp, sizeof(tmp),"%s",dir);
		len = strlen(tmp);
		if(tmp[len - 1] == '/')
			tmp[len - 1] = 0;
		for(p = tmp + 1; *p; p++)
			if(*p == '/') {
				*p = 0;
				_mkdir(tmp, mode);
				*p = '/';
			}
		_mkdir(tmp, mode);
	}
	
	
	xtring gen_filename(xtring dir, xtring fname, int year, bool fmakedir) {
		
		// insert the run year into the file pathname: /scratch/.../rundir/imogen/2015/
		//param "file_temp"     (str "/scratch/anthoni-p/PLUM/crop_runs/couple_test/imogen/YYYY/T_anom.dat")
		
		// check if fname is absolute or relative, absolute starts with "/"
		xtring pathbase = dir + xtring("/");
		if (fname[0] == '/' || fname[0] == '\0')
			pathbase = xtring("");
		
		long position = fname.find("%Y");
		if (position != -1) {
			xtring syear = to_xtring(year);
			
			if (fmakedir) {
				xtring pathname = pathbase + fname.left(position) + syear;
				_mkdir((char*) pathname, 0775);
			}
			
			fname = fname.left(position) + syear + fname.right(fname.len() - xtring("%Y").len() - position);
		}
		
		return pathbase + fname;
	}

//	bool create_directory(const std::string& path) {
//		// Log the attempt to create directory
//		ImogenLogger::getInstance().debug("Creating directory: " + path);
//
//		// Handle empty path
//		if (path.empty()) {
//			ImogenLogger::getInstance().error("Cannot create directory: empty path");
//			return false;
//		}
//
//		// Try creating the directory
//#if defined(_WIN32) || defined(_WIN64)
//		if (mkdir(path.c_str()) == 0) {
//			ImogenLogger::getInstance().debug("Directory created: " + path);
//			return true;
//		}
//#else
//		if (mkdir(path.c_str(), 0755) == 0) {
//			ImogenLogger::getInstance().debug("Directory created: " + path);
//			return true;
//		}
//#endif
//
//		// Check if directory already exists
//		if (errno == EEXIST) {
//			ImogenLogger::getInstance().debug("Directory already exists: " + path);
//			return true;
//		}
//
//		// If failed due to missing parent directories, create them recursively
//		if (errno == ENOENT) {
//			// Find parent directory
//			size_t pos = path.find_last_of("/\\");
//			if (pos == std::string::npos || pos == 0) {
//				ImogenLogger::getInstance().error("Cannot create directory: no parent path for " + path);
//				return false;
//			}
//
//			std::string parent = path.substr(0, pos);
//			// Recursively create parent directories
//			if (!create_directory(parent)) {
//				ImogenLogger::getInstance().error("Failed to create parent directory: " + parent);
//				return false;
//			}
//
//			// Try creating the directory again
//#if defined(_WIN32) || defined(_WIN64)
//			if (mkdir(path.c_str()) == 0) {
//				ImogenLogger::getInstance().debug("Directory created after parent: " + path);
//				return true;
//			}
//#else
//			if (mkdir(path.c_str(), 0755) == 0) {
//				ImogenLogger::getInstance().debug("Directory created after parent: " + path);
//				return true;
//			}
//#endif
//
//			ImogenLogger::getInstance().error("Failed to create directory: " + path + " (errno: " + std::to_string(errno) + ")");
//			return false;
//		}
//
//		// Other errors (e.g., EACCES)
//		ImogenLogger::getInstance().error("Failed to create directory: " + path + " (errno: " + std::to_string(errno) + ")");
//		return false;
//	}
	
}

/// Prints the date and time together with the name of this simulation
void print_logfile_heading() {
	xtring datetime;
	unixtime(datetime);

	xtring header = xtring("[LPJ-GUESS  ") + datetime + "]\n\n";
	dprintf((char*)header);

	// Print the title of this run
	std::string dashed_line(50, '-');
	dprintf("\n\n%s\n%s\n%s\n",
	        dashed_line.c_str(), (char*)title, dashed_line.c_str());
}

/// Simulate one day for a given Gridcell
/**
 * The climate object in the gridcell needs to be set up with
 * the day's forcing data before calling this function.
 *
 * \param gridcell            The gridcell to simulate
 * \param input_module        Used to get land cover fractions
 */
void simulate_day(Gridcell& gridcell, InputModule* input_module) {

	// Update daily climate drivers etc
	dailyaccounting_gridcell(gridcell);

	// Calculate daylength, insolation and potential evapotranspiration
	daylengthinsoleet(gridcell.climate);

	// Update crop sowing date calculation framework
	crop_sowing_gridcell(gridcell);

	// Dynamic landcover and crop fraction data during historical
	// period and create/kill stands.
	if (!just_phu_pvd || date.year < 2) {
		landcover_dynamics(gridcell, input_module);
	}

	// Update dynamic management options
	input_module->getmanagement(gridcell);

	// Set forest management for all stands this year
	if (!just_phu_pvd || date.year < 2) {
		manage_forests(gridcell);
	}

	// Reset burnt area fractions and calculate the patch-level scaling fractions for sacling out considering only flammable stands
	// Note that unlike the standard dailyaccounting_gridcell(), this should be done *after* landcover_dynamics()
  	if(firemodel == SPITFIRE) dailyaccounting_gridcell_spitfire(gridcell);


	Gridcell::iterator gc_itr = gridcell.begin();
	while (gc_itr != gridcell.end()) {

		// START OF LOOP THROUGH STANDS
		Stand& stand = *gc_itr;

		dailyaccounting_stand(stand);

		// MF SPITFIRE daily accounting
		if(firemodel == SPITFIRE) spitfire_dailyaccounting(stand, gridcell.climate);

		stand.firstobj();
		while (stand.isobj) {

			// START OF LOOP THROUGH PATCHES

			// Get reference to this patch
			Patch& patch = stand.getobj();
			// Update daily soil drivers including soil temperature
			dailyaccounting_patch(patch);

			// Calculate crop sowing dates
			crop_sowing_patch(patch);
			// Crop phenology
			crop_phenology(patch);
			
			// Determine nitrogen fertilisation amount
			if(run_landcover && !just_phu_pvd)
				nfert(patch);

			if (!just_phu_pvd) {
				// Leaf phenology for PFTs and individuals
				leaf_phenology(patch, gridcell.climate);
				// Interception
				interception(patch, gridcell.climate);
				initial_infiltration(patch, gridcell.climate);
				// Photosynthesis, respiration, evapotranspiration
				canopy_exchange(patch, gridcell.climate);
				// Sum total required irrigation
				irrigation(patch);
				// Soil water accounting, snow pack accounting
				soilwater(patch, gridcell.climate);
				// Daily C allocation (cropland)
				growth_daily(patch);
				// Soil organic matter and litter dynamics
				som_dynamics(patch, gridcell.climate);
				// Methane production/consumption on wetlands and peatlands (no methane dynamics for other stand types at present)
				methane_dynamics(patch);
				// BLAZE fire model
				blaze_driver(patch,gridcell.climate);
				// MF: SPITFIRE
				if(firemodel == SPITFIRE) spitfire_daily(patch, gridcell.climate);
				
#ifdef GCP_INJECT_CODE
				gcp_dailyaccounting_patch(patch);
#endif

				if (date.islastday && date.islastmonth) {

					// LAST DAY OF YEAR
					// Tissue turnover, allocation to new biomass and reproduction,
					// updated allometry
					growth(stand, patch);
				}
			}
			stand.nextobj();
		}// End of loop through patches

		// Update crop rotation status
		crop_rotation(stand);

		if (date.islastday && date.islastmonth && (!just_phu_pvd || date.year < 2)) {
			// LAST DAY OF YEAR
			stand.firstobj();
			while (stand.isobj) {

				// For each patch ...
				Patch& patch = stand.getobj();
				// Establishment, mortality and disturbance by fire
				vegetation_dynamics(stand, patch);
				stand.nextobj();
			}
		}

		++gc_itr;
	}	// End of loop through stands
}


int framework(const CommandLineArguments& args) {

	// The 'mission control' of the model, responsible for maintaining the
	// primary model data structures and containing all explicit loops through
	// space (grid cells/stands) and time (days and years).

	using std::auto_ptr;

	const char* input_module_name = args.get_input_module();

	auto_ptr<InputModule> input_module(InputModuleRegistry::get_instance().create_input_module(input_module_name));

	GuessOutput::OutputModuleContainer output_modules;
	GuessOutput::OutputModuleRegistry::get_instance().create_all_modules(output_modules);

	// Read the instruction file to obtain PFT static parameters and
	// simulation settings
	read_instruction_file(args.get_instruction_file());

	// Initialise input/output
    
    // SSR
    if (firsthistyear<0 || lasthistyear<0) {
        fail("\n\nfirsthistyear and lasthistyear must be specified in ins-file and >0!");
    }
    else if (firsthistyear>lasthistyear){
        dprintf("\nWarning: firsthistyear (%d) is  < lasthistyear (%d)\n", firsthistyear, lasthistyear);
    }

	input_module->init();
	output_modules.init();

	print_logfile_heading();

	// Nitrogen limitation
	if (ifnlim && !ifcentury) {
		fail("\n\nIf nitrogen limitation is switched on then century soil module also needs to be switched on!");
	}

	// bvoc
	if (ifbvoc) {
		initbvoc();
	}
	
	// We've already sorted save_years. Now ignore the ones that won't be possible given the first year of this run.
	while (save_state && !save_years.empty() && ((restart && save_years.front()<=restart_year) || (!restart && save_years.front()<=date.first_calendar_year))) {
		save_years.pop();
	}

	// Create objects for (de)serializing grid cells
	std::vector<std::unique_ptr<GuessSerializer>> serializer_list(std::max(static_cast<int>(save_years.size()), 1));//DKB
	//auto_ptr<GuessSerializer> serializer_list[std::max((int)save_years.size(),1)];
	auto_ptr<GuessDeserializer> deserializer;
	// SSR: GGCMI: Handling multiple save years

	if (save_state) {
		int serializer_id = 0;
		if (save_years.empty()) {
			// Original behavior
			if (save_year==-9999) {
				save_year = firsthistyear;
			}
			if (restart && save_year<=restart_year) {
				fail("save_year (%d) is <= restart_year (%d)", save_year, restart_year);
			}
			//xtring save_path = gen_filename(".", state_path, save_year, true);
			serializer_list[serializer_id] = auto_ptr<GuessSerializer>(new GuessSerializer(state_path, GuessParallel::get_rank(), GuessParallel::get_num_processes(), serializer_id));
		} else {
			// Multiple save years are specified
			
			save_years_remaining = save_years;
			while (!save_years_remaining.empty()) {
				int this_year = save_years_remaining.front() ;
				save_years_remaining.pop();
				xtring save_path = gen_filename(".", state_path, this_year, true);
				serializer_list[serializer_id] = auto_ptr<GuessSerializer>(new GuessSerializer(save_path, GuessParallel::get_rank(), GuessParallel::get_num_processes(), serializer_id));
				serializer_id++;
			}
			
		}
	}

	if (restart) {
		if (restart_year==-9999) {
			restart_year = firsthistyear;
		}
		xtring restart_path = gen_filename(".", state_path, restart_year, false);
		deserializer = auto_ptr<GuessDeserializer>(new GuessDeserializer(restart_path));
	}
	
	if (crop_gs_out) {
		output_modules.openlocalfiles_ggcmi();
	}
	
	// SSR: GGCMI
	if (crop_gs_out) {
		output_modules.openlocalfiles_ggcmi();
	}
	
	// SSR
	bool is_first_gridcell = true;

	while (true) {

		// START OF LOOP THROUGH GRID CELLS
		
		// SSR: GGCMI: Deal with multiple save years
		if (save_state && !save_years.empty()) {
			save_years_remaining = save_years;
			save_year = save_years_remaining.front();
			save_years_remaining.pop();
		}
		int save_year_index = 0;

		// Initialise global variable date
		// (argument nyear not used in this implementation)
		date.init(1);

		// Create and initialise a new Gridcell object for each locality
		Gridcell gridcell;
		
		// SSR
		gridcell.is_first_gridcell = is_first_gridcell;
		
		// SSR: GGCMI
		input_module->setup_multipart();
		
		// Call input module to obtain latitude and driver data for this grid cell.
		if (!input_module->getgridcell(gridcell)) {
			break;
		}
		
		// SSR: Multi-part
		input_module->reset();
		
		// SSR: GGCMI
		input_module->setup_multipart();

		// Initialise certain climate and soil drivers
		gridcell.climate.initdrivers(gridcell.get_lat());

		// Read landcover and cft fraction data from 
		// data files for the spinup period and create stands
		landcover_init(gridcell, input_module.get());

		if (restart) {
			// Get the whole grid cell from file...
			deserializer->deserialize_gridcell(gridcell);
			// ...and jump to the restart year
			date.year = restart_year - (firsthistyear - nyear_spinup);
		}

        // Call input/output to obtain climate, insolation and CO2 for this
		// day of the simulation. Function getclimate returns false if last year
		// has already been simulated for this grid cell
		
		while (input_module->getclimate(gridcell)) {

			// START OF LOOP THROUGH SIMULATION DAYS

			simulate_day(gridcell, input_module.get());

            // SSR: GGCMI
			output_modules.outdaily(gridcell);
            if (crop_gs_out) {
				if (just_phu_pvd) {
					output_modules.outharvest_justphupvd(gridcell);
				} else {
					output_modules.outharvest(gridcell);
				}
            }

			if (date.islastday && date.islastmonth) {
				// LAST DAY OF YEAR
				
				if (crop_gs_out && !just_phu_pvd) {
					output_modules.outannual_ggcmi(gridcell);
				}
				if(printseparatestands)
					output_modules.openlocalfiles(gridcell);
				// Call output module to output results for end of year
				// or end of simulation for this grid cell
				if (!just_phu_pvd) {
					output_modules.outannual(gridcell);
				}

				if (!just_phu_pvd) {
					gridcell.balance.check_year(gridcell);
				}

				// Time to save state?
				if (date.get_calendar_year() == save_year-1 && save_state) {
										
					serializer_list[save_year_index]->serialize_gridcell(gridcell);
					save_year_index++;
					
					if (!save_years_remaining.empty()) {
						save_year = save_years_remaining.front();
						save_years_remaining.pop();
					}
					
				}

				// Check whether to abort
				if (abort_request_received()) {
					return 99;
				}
			}

			// Advance timer to next simulation day
			date.next();

			// End of loop through simulation days
		}	//while (getclimate())

		if(printseparatestands)
			output_modules.closelocalfiles(gridcell);
        
        if (!just_phu_pvd) {
			gridcell.balance.check_period(gridcell);
		}
		
		// SSR
		is_first_gridcell = false;

	}		// End of loop through grid cells
	
	// SSR: GGCMI
	if (crop_gs_out)
		output_modules.closelocalfiles_ggcmi();

	// END OF SIMULATION
	
	return 0;
}
