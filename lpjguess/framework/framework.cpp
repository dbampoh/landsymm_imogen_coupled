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

	// =====================================================================
	// [Step 17a (F-12 sub-milestone C1) ADDITIVE PATH: per-year-outer /
	//  per-gridcell-inner loop, gated on IMOGENConfig::framework_loop_mode.
	//  Default mode "gridcell_outer" SKIPS this block entirely (early-
	//  return pattern preserves the existing per-gridcell-outer code path
	//  below byte-exactly; no whitespace or indentation change there).
	//
	//  Design rationale (D1; per session-2 chat handoff Part 9 §9.3):
	//    - Pre-load all gridcells into memory + pre-load all years' climate
	//      per cell via the new InputModule::preload_all_climate virtual
	//    - Year-outer loop drives simulate_day per cell per day via the
	//      new InputModule::getclimate_for_year virtual (NOT the existing
	//      getclimate(gridcell), to avoid global-date state-machinery
	//      dependencies and per-input-module shared-mutable-state bugs
	//      like IMOGENCFXInput's spinup_year_idx)
	//    - 4 concerns per cell preserved (per session-2 §9.2 audit):
	//        (a) per-cell setup: getgridcell, reset, setup_multipart,
	//            climate.initdrivers, landcover_init -- ONCE at preload
	//        (b) restart load: deserialize_gridcell + date.year jump --
	//            NOT supported in C1; fail fast (gridcell_outer required)
	//        (c) per-day inner: simulate_day, outdaily, year-end outannual,
	//            balance.check_year, abort_check, date.next -- PER YEAR
	//            in the year-outer loop's inner cell pass
	//        (d) per-cell teardown: balance.check_period -- ONCE at end
	//
	//  C1 scope limitations (deliberately narrow; expand in C1.2/C1.3):
	//    - restart NOT supported in year_outer (use gridcell_outer)
	//    - save_state NOT supported in year_outer (use gridcell_outer)
	//    - crop_gs_out NOT supported in year_outer (use gridcell_outer)
	//    - printseparatestands NOT supported in year_outer (use gridcell_outer)
	//  All limitations fail fast with clear pointers to gridcell_outer
	//  fallback. Smoke test (4-5 cell × 50-yr SSP1-2.6 cross-validation)
	//  doesn't need any of these.
	//
	//  Cross-references:
	//    - notes/FOLLOWUPS.md F-12 (canonical revised plan; staged C1->C2->C3)
	//    - notes/STEP_17a.md (per-step verification record)
	//    - _chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md Part 9
	//      (full design rationale + D1/D2/D3 options considered)
	//    - inputmodule.h preload_all_climate + getclimate_for_year doc blocks
	//  - DKB 2026-05-10]
	// =====================================================================
	if (IMOGENConfig::framework_loop_mode == "year_outer") {

		// ----- C1 limitation guards: fail fast on unsupported features -----
		if (restart) {
			fail("framework_loop_mode = \"year_outer\" does not support "
			     "restart in the C1 sub-milestone (step 17a). Use "
			     "framework_loop_mode = \"gridcell_outer\" (the default) "
			     "for restarted runs. Restart support in year_outer mode "
			     "is planned for a subsequent C1 sub-milestone.");
		}
		if (save_state) {
			fail("framework_loop_mode = \"year_outer\" does not support "
			     "save_state in the C1 sub-milestone (step 17a). Use "
			     "framework_loop_mode = \"gridcell_outer\" (the default) "
			     "for save-state runs. save_state support in year_outer "
			     "mode is planned for a subsequent C1 sub-milestone.");
		}
		if (crop_gs_out) {
			fail("framework_loop_mode = \"year_outer\" does not support "
			     "crop_gs_out in the C1 sub-milestone (step 17a). Use "
			     "framework_loop_mode = \"gridcell_outer\" (the default) "
			     "for GGCMI crop runs.");
		}
		if (printseparatestands) {
			fail("framework_loop_mode = \"year_outer\" does not support "
			     "printseparatestands in the C1 sub-milestone (step 17a). "
			     "Use framework_loop_mode = \"gridcell_outer\" (the default) "
			     "for separate-stand outputs.");
		}

		// ----- 1. Determine year range for the simulation -----
		// total_years = nyear_spinup + (lasthistyear - firsthistyear + 1).
		// first_calendar_year = firsthistyear - nyear_spinup, matching the
		// gridcell_outer loop's date.year=0 convention (year 0 of the
		// simulation == first_calendar_year on the calendar).
		const int total_years = nyear_spinup + (lasthistyear - firsthistyear + 1);
		const int first_calendar_year = firsthistyear - nyear_spinup;

		dprintf("[year_outer] starting framework_loop_mode = \"year_outer\" "
		        "(F-12 sub-milestone C1; step 17a)\n");
		dprintf("[year_outer]   nyear_spinup = %d, firsthistyear = %d, "
		        "lasthistyear = %d\n",
		        nyear_spinup, firsthistyear, lasthistyear);
		dprintf("[year_outer]   total_years = %d (calendar %d .. %d)\n",
		        total_years, first_calendar_year,
		        first_calendar_year + total_years - 1);

		// ----- 2. Pre-load all gridcells + preload climate per cell -----
		// Each cell gets the same setup pipeline as gridcell_outer's lines
		// 425-452 (date.init(1), getgridcell, reset, setup_multipart,
		// climate.initdrivers, landcover_init). Then preload_all_climate
		// loads all years' climate up front (per the D1 design choice).
		std::vector<std::unique_ptr<Gridcell>> gridcells;

		while (true) {

			// Per-cell setup mirrors gridcell_outer lines 425-452.
			date.init(1);

			std::unique_ptr<Gridcell> gridcell_ptr(new Gridcell);
			Gridcell& gridcell = *gridcell_ptr;
			gridcell.is_first_gridcell = is_first_gridcell;

			input_module->setup_multipart();

			if (!input_module->getgridcell(gridcell)) {
				break;  // no more gridcells; preload phase complete
			}

			input_module->reset();
			input_module->setup_multipart();
			gridcell.climate.initdrivers(gridcell.get_lat());
			landcover_init(gridcell, input_module.get());

			// PRELOAD CLIMATE for all years for this cell (D1 design).
			// Default-fail virtual aborts here if the input module doesn't
			// override it; only IMOGENCFXInput in C1 (with the spinup_
			// year_idx state-machine reproduction; landed in subsequent
			// C1 sub-step) is expected to override.
			input_module->preload_all_climate(gridcell, first_calendar_year,
			                                  first_calendar_year + total_years - 1);

			gridcells.push_back(std::move(gridcell_ptr));
			is_first_gridcell = false;
		}

		const int num_cells = static_cast<int>(gridcells.size());
		dprintf("[year_outer] preloaded %d gridcell(s)\n", num_cells);

		if (num_cells == 0) {
			// No gridcells in gridlist; nothing to simulate.
			if (crop_gs_out) {
				output_modules.closelocalfiles_ggcmi();
			}
			return 0;
		}

		// ----- 3. Per-year outer loop -----
		// For each calendar year in the simulation, process all gridcells
		// for that year in inner-loop order. The inner loop's per-day
		// simulate_day calls advance global `date` per day; we reset
		// `date` to (year_idx, day=0) at the start of each (year, cell)
		// tuple so the per-day inner loop sees the same date semantics
		// as gridcell_outer mode would for the same (cell, year, day).
		for (int year_idx = 0; year_idx < total_years; ++year_idx) {

			const int calendar_year = first_calendar_year + year_idx;

			for (int cell_idx = 0; cell_idx < num_cells; ++cell_idx) {

				Gridcell& gridcell = *gridcells[cell_idx];

				// Reset date to start of this (cell, year). The init(1)
				// call resets all per-day fields cleanly; we then set
				// date.year manually to year_idx (relative to
				// first_calendar_year, which is set globally elsewhere).
				date.init(1);
				date.year = year_idx;

				// 365-day inner loop. day_of_year is purely a counter for
				// getclimate_for_year's day index; date.day is updated by
				// date.next() per iteration to keep the global-date view
				// consistent for simulate_day + output_modules.
				for (int day_of_year = 0;
				     day_of_year < Date::MAX_YEAR_LENGTH;
				     ++day_of_year) {

					if (!input_module->getclimate_for_year(gridcell,
					                                       calendar_year,
					                                       day_of_year)) {
						// Sim-done terminator from input module (mirrors
						// getclimate's false-return semantics). Treat as
						// end-of-simulation for this cell-year.
						break;
					}

					simulate_day(gridcell, input_module.get());

					output_modules.outdaily(gridcell);

					if (date.islastday && date.islastmonth) {
						// LAST DAY OF YEAR -- year-end actions per cell
						// (mirrors gridcell_outer lines 481-516).
						if (!just_phu_pvd) {
							output_modules.outannual(gridcell);
						}
						if (!just_phu_pvd) {
							gridcell.balance.check_year(gridcell);
						}
						if (abort_request_received()) {
							return 99;
						}
					}

					// Advance timer to next simulation day
					date.next();
				}
			}
		}

		// ----- 4. Per-cell teardown -----
		// Mirrors gridcell_outer lines 524-528.
		for (int cell_idx = 0; cell_idx < num_cells; ++cell_idx) {
			Gridcell& gridcell = *gridcells[cell_idx];
			if (!just_phu_pvd) {
				gridcell.balance.check_period(gridcell);
			}
		}

		// ----- 5. Cleanup (mirrors framework.cpp lines 537-538) -----
		// crop_gs_out is unsupported in year_outer (guarded above), so
		// closelocalfiles_ggcmi is unreachable here -- but call it
		// defensively to mirror gridcell_outer's structure.
		if (crop_gs_out) {
			output_modules.closelocalfiles_ggcmi();
		}

		dprintf("[year_outer] simulation complete: %d cell(s) x %d year(s)\n",
		        num_cells, total_years);

		// EARLY RETURN: skip the existing per-gridcell-outer code below.
		// The existing code is preserved byte-exactly as the default
		// gridcell_outer mode -- no whitespace or indentation change.
		return 0;
	}
	// ===== End of step-17a year_outer additive block =====

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
