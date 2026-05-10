///////////////////////////////////////////////////////////////////////////////////////
/// \file imogencfx.h
/// \brief Input module for IMOGEN climate files
///
/// \author Peter Anthoni,Extended by DBampoh
/// $Date: 2015-05-19 13:58:50 +0200 (Tue, 19 May 2015) $
///
///////////////////////////////////////////////////////////////////////////////////////

#ifndef LPJ_GUESS_IMOGEN_INPUT_H
#define LPJ_GUESS_IMOGEN_INPUT_H

#include "guess.h"
#include "soilinput.h"
#include "inputmodule.h"
#include <vector>
#include <map>
#include <utility>
#include "gutil.h"
#include "globalco2file.h"
#include "lamarquendep.h"
#include "externalinput.h"

class IMOGENCFXInput : public InputModule {
public:
	/// Constructor
	/** Declares the instruction file parameters used by the input module.
	 */
	IMOGENCFXInput();

	/// Destructor, cleans up used resources
	~IMOGENCFXInput();

	/// Reads in gridlist and initialises the input module
	/** Gets called after the instruction file has been read */
	void init();

	/// See base class for documentation about this function's responsibilities
	bool getgridcell(Gridcell& gridcell);

	/// DKB: 2022-10-19: added to support the new getgridcell() function
	void setup_multipart() {};

	/// See base class for documentation about this function's responsibilities
	bool getclimate(Gridcell& gridcell);

	/// See base class for documentation about this function's responsibilities
	void getlandcover(Gridcell& gridcell);

	/// Obtains land management data for one day
	void getmanagement(Gridcell& gridcell) { management_input.getmanagement(gridcell); }

	void getNfert(Gridcell& gridcell);

	bool getsoil(Gridcell& gridcell, const int soilmap_index);
	///
	int getfirsthistyear();

	int getnyear_hist();

	//  static const int NYEAR_SPINUP_DATA=30;

	double* getdprec() { return dprec; }

	bool supports_firsthistyear_in_insfile() { return true; }

	void year_init(int rank, int calendar_year);

	// ============================================================================
	// [Step 17a (F-12 sub-milestone C1.3 sub-step 7.3.2) of unified-codebase
	//  rebuild (2026-05-10 late evening): year_outer mode support for
	//  IMOGENCFXInput. Overrides InputModule's preload_all_climate +
	//  getclimate_for_year virtuals added at the C1 foundation step.
	//  Together these enable LPJ-GUESS's framework() to drive simulation
	//  in per-year-outer / per-gridcell-inner ordering (gated on
	//  IMOGENConfig::framework_loop_mode == "year_outer") while reproducing
	//  IMOGENCFXInput::getclimate()'s gridcell_outer mode semantics
	//  bit-exactly per cell-year-day.
	//
	//  Mirrors the C1.1 ImogenInput pattern at imogen_input.h with the
	//  IMOGENCFXInput-specific differences:
	//    1. NO K -> degC conversion in climate.temp = dtemp[date.day]
	//       (IMOGENCFXInput's existing getclimate at line ~1179 does NOT
	//       subtract 273.15; ImogenInput's getclimate at line ~876 DOES).
	//       Preserved here for byte-exact reproduction of IMOGENCFXInput's
	//       gridcell_outer behaviour.
	//    2. Additional climate fields populated from cache: relhum, u10,
	//       tmin, tmax (per step 9.5 wiring; IMOGENCFXInput-specific).
	//    3. BLAZE compatibility check fires on day 0 (mirror of imogencfx.cpp
	//       lines 884-893 in existing get_climate_for_gridcell).
	//
	//  Cross-references:
	//  - notes/STEP_17a.md §7.3.2 (sub-step 7.3.2 plan + erratum-corrected
	//    spinup_year_idx formula)
	//  - notes/FOLLOWUPS.md F-12 (canonical revised plan)
	//  - lpjguess/framework/framework.cpp year_outer additive block (the
	//    caller of these methods)
	//  - lpjguess/modules/imogen_input.h (C1.1 ImogenInput pattern; same
	//    cache-key + cache-value structure)
	//  - DKB 2026-05-10]

	/// year_outer mode override: pre-load all needed years' climate for
	/// ONE cell into the existing all_temp/all_prec/.../all_dtmax cache
	/// via readenv(). Caches per-cell cell_idx + per-cell NDepData
	/// value-copy in year_outer_cell_idx + year_outer_ndep_cache maps
	/// respectively. Uses the corrected spinup_year_idx state-machine
	/// reproduction formula:
	///
	///   spinup_year_idx_for_this = (cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP
	///
	/// NO `+1` in the formula. The existing getclimate() reads
	/// spinup_year_idx VALUE BEFORE incrementing it on day 0, so for
	/// cell C, spinup year Y, the value READ equals the count of PRIOR
	/// day-0 increments = (C * nyear_spinup + Y) modulo NYEAR_SPINUP.
	/// (C1.1 erratum: the foundation commit's docs incorrectly had `+1`;
	/// corrected at C1.1 commit `90401f2` and verified at sub-step 7.3.1
	/// 4-cell PASS commit `7be595a`.)
	void preload_all_climate(Gridcell& gridcell, int first_calendar_year, int last_calendar_year);

	/// year_outer mode override: serve cached climate per (cell, year, day).
	/// Looks up cached cell_idx + ndep, computes imogen_year via the same
	/// formula as preload_all_climate, finds store_index in the cache,
	/// then on day 0: BLAZE compatibility check + populates per-day arrays
	/// via get_climate_for_gridcell + ndep + co2; every day: assigns
	/// climate.{temp WITHOUT K->C conversion, prec, insol, dtr conditional,
	/// relhum, u10, tmin, tmax} + gridcell.{dNH4dep, dNO3dep}. Returns
	/// false at sim-done terminator (calendar_year > lasthistyear) or on
	/// missing-grid-point conditions.
	bool getclimate_for_year(Gridcell& gridcell, int calendar_year, int day_of_year);

private:

	/// Land cover input module
	LandcoverInput landcover_input;
	/// Management input module
	ManagementInput management_input;
	SoilInput soilinput;

	/// A list of Coord objects containing coordinates of the grid cells to simulate
	ListArray_id<Coord> gridlist;

	/// Flag for getgridcell(). True indicates that the first gridcell has not been read yet by getgridcell()
	bool first_call;

	/// sets the gridlist object to the gridcell location
	bool find_corresponding_gridlist(Gridcell gridcell);

	/// search radius to use when finding gridcell data
	double searchradius;

	/// in case imogene climate data have an offset to midpoint
	double offset_to_midpoint[2];

	/** extract the imogen formatted climate data

	 @param line    data line (lon lat [data for each day]
	   @param dlon    double longitude (adjusted to our -180..180 degree grid
	   @param dlat    double latitude
	   @param data    extracted data, NULL no data should get extracted
	 @return true = extraction ok
	 */
	bool extract_line_data(std::string line, double& dlon, double& dlat, double* data, bool monthly = true);

	/// Extract the <i>lines</i> out of the file <i>fname</i> into the supplied <i>data</i> array, either monthly or daily
	/// @param fname data file name
	/// @param lons all longtudes (more informational)
	/// @param lats all latitudes  (more informational)
	/// @param lines the lines to extract into data (can have duplicates)
	/// @param data the data array to fill
	/// @param monthly if true, we have monthly data else daily
	bool read_lines_from_file(xtring fname, std::vector<double> lons, std::vector<double> lats, std::vector<int> lines, std::vector<std::vector<double> >& data, bool monthly);

	bool read_lon_lat_in_file(xtring fname, std::vector<double>& lons, std::vector<double>& lats);
	bool lon_lat_lines_in_file(xtring fname, std::vector<double> lons, std::vector<double> lats, std::vector<int>& lines);

	/** read in the environmental input data for coord

	 @param lons all longitudes
	 @param lats all latitudes
	 @param calendar_year year to read in
	 @param store_index index in the year storage of the climate data
	 @param line_index line number in the climate files for all lons and lats

	 @return number of grid points found
	 */
	int readenv(std::vector<double> lons, std::vector<double> lats, int calendar_year, int store_index, std::vector<int> line_index);

	void get_climate_for_gridcell(int store_index, int igrid, long& seed);

	double parse_spatial_resolution();

	/// Temperature for current gridcell and current year (deg C)
	double dtemp[Date::MAX_YEAR_LENGTH];

	/// Precipitation for current gridcell and current year (mm/day)
	double dprec[Date::MAX_YEAR_LENGTH];

	/// Insolation for current gridcell and current year (\see instype)
	double dinsol[Date::MAX_YEAR_LENGTH];

	/// Diurnal temperature range and current year
	double ddtr[Date::MAX_YEAR_LENGTH];

	/// Relative humidty for current gridcell and current year
	double drelhum[Date::MAX_YEAR_LENGTH];

	/// Wind for current gridcell and current year
	double dwind[Date::MAX_YEAR_LENGTH];

	// [Step 9.5 of unified-codebase rebuild: per-day Tmin/Tmax arrays, populated
	//  from monthly IMOGEN engine output Tmin_anom.dat / Tmax_anom.dat (when
	//  the C++ engine emits them; Fortran-engine port deferred to step 9.5b).
	//  Mirrors the cfxinput.cpp dmax_temp/dmin_temp pattern. - DKB 2026-05-07]
	/// Minimum temperature for current gridcell and current year (deg C)
	double dtmin[Date::MAX_YEAR_LENGTH];

	/// Maximum temperature for current gridcell and current year (deg C)
	double dtmax[Date::MAX_YEAR_LENGTH];

	/// Daily N deposition for one year
	double dNH4dep[Date::MAX_YEAR_LENGTH], dNO3dep[Date::MAX_YEAR_LENGTH];

	/// DKB Reset virtual function
	void reset();

	/// Path to co2 data
	xtring file_co2;

	/// Yearly CO2 data read from file
  // might need to re-re-re-read in the co2 from imogen!!!!
	/**
	 * This object is indexed with calendar years, so to get co2 value for
	 * year 1990, use co2[1990]. See documentation for GlobalCO2File for
	 * more information.
	 */
	GlobalCO2File co2;
	std::vector<double> all_co2;

	/// Path to CRU binary archive
	xtring file_cru;

	/// Path to temperature data
	xtring file_temp;

	/// Path to precipitation data
	xtring file_prec;

	/// Path to number of precipitation days data
	xtring file_wetdays;

	/// Path to radiation data
	xtring file_insol;

	/// Path to diurnal temperature range
	xtring file_dtr;

	// for Blaze need from imogen:
	xtring file__pres;
	//	int historic_timestep_specifichum;
	xtring file_relhum;
	xtring file_wind;

	// [Step 9.5: paths to IMOGEN engine's per-year Tmin_anom.dat / Tmax_anom.dat
	//  output. Wired in init() + read in read_climate_for_year(). - DKB 2026-05-07]
	xtring file_tmin;
	xtring file_tmax;

	/// Nitrogen deposition forcing for current gridcell
	Lamarque::NDepData ndep;

	/// Nitrogen deposition time series to use (historic,rcp26,...)
	std::string ndep_timeseries;

	double spatial_resolution;

	// TODO: might have to fix this for imogen.
	static const int FIRST_HIST_YEAR = 1901;
	//static const int FIRST_HIST_YEAR = 2012;
	static const int NYEAR_RUN = 200;

	static const int FIRST_SPINUP_YEAR = 1871;
	static const int NYEAR_SPINUP = 30;

	int spinup_year_idx; // year index for spinup (0..NYEAR_SPINUP-1)

	// FIXME: move to parameters.cpp/h as in the PLUM code
	//int firsthistyear;  // the first year of this run
	//int lasthistyear;  // the last year of this run
	int nyears;

	bool reread_file;
	int ngrid;  // number of gridpoints in this process
	//  static const int MAX_STORE_YEARS = NYEAR_SPINUP;
	std::vector<int> stored_years;
	int last_store_index;
	// true=input is monthly, false=daily
	bool monthly;

	int current_grid_index; // range [0 .. ngrid-1]

	std::vector<double> all_lon; // [ngrid];
	std::vector<double> all_lat; // [ngrid];
	std::vector<int> coord_line; // [ngrid];

	// data arrays for climate data for years, gridpoints, and (month or days), data[year,grid,month|day]
	std::vector< std::vector< std::vector<double> > > all_temp;
	std::vector< std::vector< std::vector<double> > > all_prec;
	std::vector< std::vector< std::vector<double> > > all_wetdays;
	std::vector< std::vector< std::vector<double> > > all_insol;
	std::vector< std::vector< std::vector<double> > > all_dtr;
	std::vector< std::vector< std::vector<double> > > all_drelhum;
	std::vector< std::vector< std::vector<double> > > all_dwind;

	// [Step 9.5: storage for IMOGEN engine's per-year Tmin/Tmax across all
	//  gridcells × all months/days in the smoke window. Resized in
	//  read_climate_for_year() the same way all_temp is. - DKB 2026-05-07]
	std::vector< std::vector< std::vector<double> > > all_dtmin;
	std::vector< std::vector< std::vector<double> > > all_dtmax;

	// [Step 17a (F-12 sub-milestone C1.3 sub-step 7.3.2) of unified-codebase
	//  rebuild (2026-05-10 late evening): per-cell cache for year_outer mode.
	//  Maps (lon, lat) coordinate keys to the cell-specific state captured
	//  during preload_all_climate(). Mirrors imogen_input.h's C1.1 cache
	//  member pattern (year_outer_cell_idx + year_outer_ndep_cache).
	//
	//  Why (lon, lat) keys vs Gridcell* identity: the framework re-creates
	//  Gridcell objects between phases; pointer-identity is unreliable.
	//  Coordinate keys are stable throughout the run.
	//
	//  Why NDepData is value-copied (not reference): NDepData is a value
	//  type containing only arrays (no pointers/references); std::map
	//  value-copies on insert; no aliasing issues. Per-cell cache holds
	//  cell-specific Lamarque NDep state so getclimate_for_year doesn't
	//  need to re-fetch ndep from the shared `ndep` member (which gets
	//  overwritten as gridcells iterate).
	//  - DKB 2026-05-10]
	std::map< std::pair<double, double>, int > year_outer_cell_idx;
	std::map< std::pair<double, double>, Lamarque::NDepData > year_outer_ndep_cache;

	// Timers for keeping track of progress through the simulation
	Timer tprogress, tmute;
	static const int MUTESEC = 20; // minimum number of sec to wait between progress messages

};

#endif // LPJ_GUESS_IMOGEN_INPUT_H
