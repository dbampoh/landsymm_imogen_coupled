///////////////////////////////////////////////////////////////////////////////////////
/// \file inputmodule.cpp
/// \brief Implemenation file for inputmodule.h
///
/// \author Joe Siltberg
/// $Date$
///
///////////////////////////////////////////////////////////////////////////////////////

#include "config.h"
#include "inputmodule.h"
#include "guess.h"

///////////////////////////////////////////////////////////////////////////////////////
/// InputModule -- default implementations of optional virtuals
///
/// preload_all_climate + getclimate_for_year are the year_outer-mode
/// virtuals added at step 17a (F-12 sub-milestone C1 of the unified-codebase
/// rebuild; 2026-05-10). The default implementations abort with a clear
/// error pointing the user at the limitation. Input modules that need to
/// be paired with framework_loop_mode = "year_outer" override these.
///
/// Cross-references:
///  - notes/FOLLOWUPS.md F-12 (canonical revised plan)
///  - notes/STEP_17a.md (per-step verification record)
///  - _chat_artifacts/CHAT_HANDOFF_2026-05-08_session2.md Part 9 (design
///    rationale + the 3 D1/D2/D3 design options that were considered;
///    D1 chosen)
///

void InputModule::preload_all_climate(Gridcell& /*gridcell*/,
                                      int /*first_calendar_year*/,
                                      int /*last_calendar_year*/) {
	fail("This input module does not support framework_loop_mode = "
	     "\"year_outer\". Either set framework_loop_mode = "
	     "\"gridcell_outer\" (the default), or use an input module "
	     "that overrides preload_all_climate + getclimate_for_year. "
	     "See notes/FOLLOWUPS.md F-12 + notes/STEP_17a.md for the "
	     "staged rollout plan.");
}

bool InputModule::getclimate_for_year(Gridcell& /*gridcell*/,
                                      int /*calendar_year*/,
                                      int /*day_of_year*/) {
	fail("This input module does not support framework_loop_mode = "
	     "\"year_outer\". Either set framework_loop_mode = "
	     "\"gridcell_outer\" (the default), or use an input module "
	     "that overrides preload_all_climate + getclimate_for_year. "
	     "See notes/FOLLOWUPS.md F-12 + notes/STEP_17a.md for the "
	     "staged rollout plan.");
	return false;
}

///////////////////////////////////////////////////////////////////////////////////////
/// InputModuleRegistry
///

InputModuleRegistry& InputModuleRegistry::get_instance() {
	static InputModuleRegistry instance;
	return instance;
}

void InputModuleRegistry::register_input_module(const char* name, 
                                                InputModuleCreator imc) {
	modules.insert(make_pair(std::string(name), imc));
}
            
InputModule* InputModuleRegistry::create_input_module(const char* name) const {
	std::map<std::string, InputModuleCreator>::const_iterator itr = modules.find(name);
	
	if (itr != modules.end()) {
		return (itr->second)();
	}
	else {
		fail("Couldn't find input module %s\n", name);
		return 0;
	}
}

void InputModuleRegistry::get_input_module_list(std::string& list) {

	list = "";
	std::map<std::string, InputModuleCreator>::iterator it = modules.begin();
	while (it!=modules.end()) {
		list += it->first + ";";
		it++;
	}

}

