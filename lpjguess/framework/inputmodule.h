///////////////////////////////////////////////////////////////////////////////////////
/// \file inputmodule.h
/// \brief Base class for input modules
///
/// \author Joe Siltberg
/// $Date$
///
///////////////////////////////////////////////////////////////////////////////////////

#ifndef LPJ_GUESS_INPUT_MODULE_H
#define LPJ_GUESS_INPUT_MODULE_H

#include <map>
#include <string>

class Gridcell;

/// Base class from which any input module must inherit
/** An input module supplies LPJ-GUESS with the forcing data it needs. The
 *  InputModule base class is an abstract class, meaning it only defines
 *  the interface which subclasses must implement.
 *
 *  To create a new input module, create a new class which inherits from
 *  this one, implement all the member functions below, and register it
 *  with the REGISTER_INPUT_MODULE macro (defined and documented below).
 */
class InputModule {
public:
	virtual ~InputModule() {}

	/// Called after the instruction file has been read
	/** Initialises the input module (e.g. opening files). Typically
	 *  reads in a gridlist.
	 */
	virtual void init() = 0;
	
	/// SSR: Used by CFXInput to delete cf_ variables before reading new ones, to avoid memory leaks.
	virtual void reset() = 0;

	/// Obtains coordinates and soil static parameters for the next grid cell to simulate 
	/** The function should return false if no grid cells remain to be simulated,
	 *  otherwise true. 
	 *
	 *  If the model is to be driven by quasi-daily values of the climate variables
	 *  derived from monthly means, this function may be the appropriate place to
	 *  perform the required interpolations. The utility functions interp_monthly_means_conserve
	 *  and interp_monthly_totals_conserve in driver.cpp may be called for this purpose.
	 */
	virtual bool getgridcell(Gridcell& gridcell) = 0;

	/// Obtains climate data (including atmospheric CO2 and insolation) for this day
	/** The function should return false if the simulation is complete for this grid cell,
	 *  otherwise true. This will normally require querying the year and day member
	 *  variables of the global class object date:
	 *
	 *  if (date.day==0 && date.year==nyear_spinup) return false;
	 *  // else
	 *  return true;
	 *
	 *  Currently the following member variables of the climate member of gridcell must be
	 *  initialised: co2, temp, prec, insol. If the model is to be driven by quasi-daily
	 *  values of the climate variables derived from monthly means, this day's values
	 *  will presumably be extracted from arrays containing the interpolated daily
	 *  values (see function getgridcell):
	 *
	 *  gridcell.climate.temp=dtemp[date.day];
	 *  gridcell.climate.prec=dprec[date.day];
	 *  gridcell.climate.insol=dsun[date.day];
	 *
	 *  Diurnal temperature range (dtr) added for calculation of leaf temperatures in 
	 *  BVOC:
	 *  gridcell.climate.dtr=ddtr[date.day]; 
	 *
	 *  If model is run in diurnal mode, which requires appropriate climate forcing data, 
	 *  additional members of the climate must be initialised: temps, insols. Both of the
	 *  variables must be of type std::vector. The length of these vectors should be equal
	 *  to value of date.subdaily which also needs to be set either in getclimate or 
	 *  getgridcell functions. date.subdaily is a number of sub-daily period in a single 
	 *  day. Irrespective of the BVOC settings, climate.dtr variable is not required in 
	 *  diurnal mode.
	 */
	virtual bool getclimate(Gridcell& gridcell) = 0;

	/// Pre-loads ALL climate data for a single gridcell across the year range.
	/** Used by the year_outer framework loop ordering (see
	 *  IMOGENConfig::framework_loop_mode = "year_outer"; added at
	 *  step 17a as F-12 sub-milestone C1 of the unified-codebase rebuild).
	 *  The default implementation here aborts with a clear error pointing
	 *  the user at the limitation; input modules that need to support the
	 *  year_outer ordering must override this and getclimate_for_year().
	 *
	 *  Called ONCE per cell after gridcell setup (getgridcell + reset +
	 *  setup_multipart + climate.initdrivers + landcover_init), before
	 *  the per-year-outer / per-cell-inner main loop begins.
	 *
	 *  \param gridcell             The cell whose climate to preload
	 *  \param first_calendar_year  First calendar year to preload (inclusive)
	 *  \param last_calendar_year   Last calendar year to preload (inclusive)
	 */
	virtual void preload_all_climate(Gridcell& gridcell,
	                                 int first_calendar_year,
	                                 int last_calendar_year);

	/// Obtains climate data for one specific (calendar_year, day_of_year)
	/// for a single gridcell, served from the per-cell cache populated by
	/// preload_all_climate.
	/** Used by the year_outer framework loop ordering. Mirrors getclimate's
	 *  per-day Climate-struct population semantics, but takes the year +
	 *  day as explicit parameters rather than reading them from the global
	 *  date object. This decouples climate data access from the global
	 *  date state machinery, which is needed because year_outer mode
	 *  drives date per-cell-per-year-per-day in a different ordering
	 *  than gridcell_outer mode.
	 *
	 *  Default implementation aborts with the same error message as
	 *  preload_all_climate. Input modules that override one MUST override
	 *  the other; the year_outer framework path calls them as a pair.
	 *
	 *  \param gridcell        The cell whose climate to populate
	 *  \param calendar_year   The calendar year to serve climate for
	 *  \param day_of_year     The day of year (0..364) to serve climate for
	 *  \return true if climate was populated; false if the cell is done
	 *          (sim-done terminator semantics, mirroring getclimate)
	 */
	virtual bool getclimate_for_year(Gridcell& gridcell,
	                                 int calendar_year,
	                                 int day_of_year);

	/// Obtains land transitions for one year
	virtual void getlandcover(Gridcell& gridcell) = 0;

	/// Obtains land management data for one day
	virtual void getmanagement(Gridcell& gridcell) = 0;
	
	/// SSR: Sets up multipart file information for a gridcell
	virtual void setup_multipart() = 0;
};


/// Keeps track of registered input modules
/** Input modules are registered with the REGISTER_INPUT_MODULE
 *  macro defined below. The framework can then ask the registry
 *  to create an input module by specifying its name.
 *
 *  The InputModuleRegistry is a singleton, meaning there's only
 *  one instance of this class, which is retrieved with the
 *  get_instance() member function.
 */
class InputModuleRegistry {
public:

	/// Function pointer type
	/** For each registered input module, we have a function which
	 *  creates an instance of that input module. The function is
	 *  created by the REGISTER_INPUT_MODULE macro below.
	 */
	typedef InputModule* (*InputModuleCreator)();

	/// Returns the one and only input module registry
	static InputModuleRegistry& get_instance();

	/// Registers an input module
	/** This function shouldn't be called directly, use the REGISTER_INPUT_MODULE
	 *  macro below instead.
	 */
	void register_input_module(const char* name, InputModuleCreator imc);

	/// Creates an input module given its name
	/** Used by the framework to instantiate the chosen input module. */
	InputModule* create_input_module(const char* name) const;

	/// Retrieves a semi-colon-separated list of available input modules
	/** Used by LPJ-GUESS Windows Shell  */
	void get_input_module_list(std::string& list);

private:

	/// Private constructor to make sure we only have one instance
	InputModuleRegistry() {}

	/// Also private to prevent copying
	InputModuleRegistry(const InputModuleRegistry&);

	/// The modules and their names
	std::map<std::string, InputModuleCreator> modules;
};

/// A macro used to register input modules
/** Each input module should use this macro somewhere in their
 *  cpp file. For instance:
 *
 *  REGISTER_INPUT_MODULE("cru_ncep", CRUInputModule)
 *
 *  where "cru_ncep" is the name of the module (used when chosing which
 *  input module to use), and CRUInputModule is the class to associate
 *  with that name.
 */
#define REGISTER_INPUT_MODULE(name, class_name) \
namespace class_name##_registration { \
\
InputModule* class_name##_creator() {\
	return new class_name();\
}\
\
int dummy() {\
	InputModuleRegistry::get_instance().register_input_module(name, class_name##_creator);\
	return 0;\
}\
\
int x = dummy();\
}


#endif // LPJ_GUESS_INPUT_MODULE_H
