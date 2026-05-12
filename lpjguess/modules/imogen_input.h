///////////////////////////////////////////////////////////////////////////////////////
/// \file imogen_input.h
/// \brief Input module for IMOGEN climate files
///
/// \author Peter Anthoni
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

class ImogenInput : public InputModule {
public:
	/// Constructor
	/** Declares the instruction file parameters used by the input module.
	 */
  ImogenInput();
  
	/// Destructor, cleans up used resources
  ~ImogenInput();
  
	/// Reads in gridlist and initialises the input module
	/** Gets called after the instruction file has been read */
  void init();
  
	/// See base class for documentation about this function's responsibilities
	bool getgridcell(Gridcell& gridcell);

  /// DKB: 2022-10-19: added to support the new getgridcell() function
  void setup_multipart(){};

	/// See base class for documentation about this function's responsibilities
	bool getclimate(Gridcell& gridcell);

	/// Year_outer mode support: pre-load all years' climate for one cell.
	/** Override of InputModule::preload_all_climate, added at step 17a as
	 *  F-12 sub-milestone C1.1 of the unified-codebase rebuild (2026-05-10).
	 *  Pre-loads all years' climate data for ONE cell into the existing
	 *  all_temp/all_prec/all_wetdays/all_insol/all_dtr cache via the
	 *  existing readenv() helper. Reproduces gridcell_outer mode's
	 *  per-cell-stateful spinup_year_idx selection deterministically via
	 *  the formula:
	 *
	 *      spinup_year_idx_at_(cell_idx, year_idx)
	 *          = (cell_idx * nyear_spinup + year_idx) % NYEAR_SPINUP
	 *
	 *  (NO +1; the existing getclimate() reads the spinup_year_idx VALUE
	 *  BEFORE incrementing it, on day 0 of each spinup year. cell_idx is
	 *  0-indexed in the order getgridcell returned cells; year_idx is
	 *  0-indexed within the spinup phase. For cell C, spinup year Y, the
	 *  cumulative spinup-year-increments before this point equals
	 *  C * nyear_spinup + Y, and spinup_year_idx is incremented exactly
	 *  that many times since init's 0; modulo NYEAR_SPINUP for wrap.)
	 *
	 *  Also caches per-cell ndep state (a copy of `ndep` member at
	 *  preload time, populated by getgridcell -> ndep.getndep) so
	 *  getclimate_for_year can serve per-cell ndep without mutating
	 *  the shared `ndep` member across cell-switches in year_outer mode.
	 *
	 *  Cross-references:
	 *  - notes/STEP_17a.md §5.4 (the spinup_year_idx state-machine finding)
	 *  - notes/FOLLOWUPS.md F-12 (canonical revised plan)
	 *  - inputmodule.h preload_all_climate doc block (base-class contract)
	 */
	void preload_all_climate(Gridcell& gridcell,
	                         int first_calendar_year,
	                         int last_calendar_year);

	/// Year_outer mode support: serve cached climate for one (cell, year, day).
	/** Override of InputModule::getclimate_for_year, added at step 17a.
	 *  Looks up the cell_idx + per-cell ndep from the cache populated by
	 *  preload_all_climate(); on day 0 of each (cell, year) tuple,
	 *  populates the per-day arrays via the existing
	 *  get_climate_for_gridcell() helper + ndep + co2; on every day
	 *  (including day 0) assigns gridcell.climate.{temp, prec, insol, dtr}
	 *  + gridcell.{dNH4dep, dNO3dep} from the per-day arrays
	 *  (mirrors getclimate lines 876-887 INCLUDING the K -> degC
	 *  temperature conversion specific to ImogenInput at line 876).
	 *
	 *  Returns false at the sim-done terminator (calendar_year > lasthistyear)
	 *  or on missing-grid-point conditions (mirrors getclimate's
	 *  false-return semantics).
	 */
	bool getclimate_for_year(Gridcell& gridcell,
	                         int calendar_year,
	                         int day_of_year);

	/// See base class for documentation about this function's responsibilities
	void getlandcover(Gridcell& gridcell);

	/// Obtains land management data for one day
	void getmanagement(Gridcell& gridcell) {management_input.getmanagement(gridcell);}
  
	void getNfert(Gridcell& gridcell);
  
	bool getsoil(Gridcell& gridcell, const int soilmap_index);
	///
	int getfirsthistyear();
  
	int getnyear_hist();
  
//  static const int NYEAR_SPINUP_DATA=30;
  
  double* getdprec() {return dprec;}
  
  bool supports_firsthistyear_in_insfile() { return true;}
  
  void year_init(int rank, int calendar_year);

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
  bool find_corresponding_gridlist (Gridcell gridcell);
  
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
	bool extract_line_data(std::string line, double& dlon, double& dlat, double *data, bool monthly = true);
	
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
  
  /// Daily N deposition for one year
	double dNH4dep[Date::MAX_YEAR_LENGTH],dNO3dep[Date::MAX_YEAR_LENGTH];

	// [Step 17b (F-12 sub-milestone C2; audit item B4) of unified-codebase
	//  rebuild (2026-05-12): per-day arrays for Rh / Wind / Tmin / Tmax
	//  consumer wiring expansion. Mirrors IMOGENCFXInput's step-9.5 wiring
	//  (`lpjguess/modules/imogencfx.h` lines ~204-218 + `imogencfx.cpp`
	//  lines ~990-1027 + ~1264-1277) but follows ImogenInput's existing
	//  K-stored-in-per-day-array convention (cf. `dtemp[]` semantics here at
	//  `imogen_input.cpp:639` / `:649`; K -> Celsius conversion applied at
	//  the consumer site in `getclimate()` line ~885 + `getclimate_for_year()`
	//  line ~1153, NOT at the monthly-array population step in
	//  `get_climate_for_gridcell()`). This intentionally DIFFERS from
	//  IMOGENCFXInput's post-step-17a-7.3.2 K -> C-at-monthly-array convention
	//  (cited at `imogencfx.cpp:1587-1590` doc block); preserved separately
	//  because the two input modules have intentionally distinct K<->C
	//  handling sites (see also `getclimate_for_year()` doc block at
	//  `imogen_input.cpp:1147-1152` for the same K-convention rationale
	//  applied to climate.temp).
	//
	//  Source files consumed (post-B2 commit `ceb2766` / B1 pending):
	//  - file_relhum -> Rh_anom.dat   (B1-pending; Fortran engine port to land)
	//  - file_wind   -> W_anom.dat    (B1-pending; Fortran engine port to land)
	//  - file_tmin   -> Tmin_anom.dat (B2-available; commit `76b3b04`)
	//  - file_tmax   -> Tmax_anom.dat (B2-available; commit `76b3b04`)
	//
	//  Unit conventions (post-B4):
	//  - Rh:   fraction or %         (no unit conversion; stored as-read)
	//  - Wind: m/s (per IMOGEN's `W_anom.dat`)  (no unit conversion;
	//          `climate.u10` per `guess.h:843-844` documents "km/h" but
	//          IMOGENCFXInput passes through m/s untransformed at
	//          `imogencfx.cpp:1605`; B4 preserves that for cross-input-module
	//          parity. A formal unit-alignment audit is a follow-up.)
	//  - Tmin/Tmax: Kelvin in per-day array; K -> degC at consumer site
	//          (mirror of `climate.temp = dtemp[date.day] - 273.15`).
	//  - DKB 2026-05-12]
	/// Relative humidity for current gridcell and current year (Rh as-read; fraction or %)
	double drelhum[Date::MAX_YEAR_LENGTH];

	/// Wind for current gridcell and current year (m/s; passed through to climate.u10)
	double dwind[Date::MAX_YEAR_LENGTH];

	/// Minimum daily temperature for current gridcell and current year (Kelvin; K -> degC at consumer)
	double dtmin[Date::MAX_YEAR_LENGTH];

	/// Maximum daily temperature for current gridcell and current year (Kelvin; K -> degC at consumer)
	double dtmax[Date::MAX_YEAR_LENGTH];

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
	// [Step 17b (B4): repurposed from pre-existing vestigial declarations.
	//  Prior to commit `ceb2766` (B3), `file_relhum` + `file_wind` were
	//  declared in this header (header-only; never referenced in the .cpp
	//  pre-B4). B4 wires them in init() + readenv() + get_climate_for_gridcell()
	//  + getclimate()/getclimate_for_year(). - DKB 2026-05-12]
	xtring file_relhum;
	xtring file_wind;

	// [Step 17b (B4): NEW path declarations for Tmin_anom.dat / Tmax_anom.dat.
	//  Mirrors `imogencfx.h:265-266` step-9.5 wiring. Wired in init() +
	//  readenv() + get_climate_for_gridcell() + getclimate()/getclimate_for_year().
	//  - DKB 2026-05-12]
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
	int firsthistyear;  // the first year of this run
	int lasthistyear;  // the last year of this run
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

	// [Step 17b (B4): per-year caches for Rh / Wind / Tmin / Tmax across all
	//  gridcells x all months/days in the smoke window. Same shape as
	//  `all_temp` etc. so the `read_lines_from_file` calls in `readenv()`
	//  index correctly when the corresponding `file_*` paths are set in the
	//  ins file. When paths are unset, these vectors are still resized but
	//  the file-read is skipped (see `readenv()` guards); leaves prior-cycle
	//  values in storage (same behaviour as IMOGENCFXInput; see `imogencfx.cpp:
	//  996-999` `have_*` guards). Defensive zero-init on unset-path is a
	//  recommended follow-up hardening (B15-style). Mirrors `imogencfx.h:
	//  311-318`. - DKB 2026-05-12]
	std::vector< std::vector< std::vector<double> > > all_drelhum;
	std::vector< std::vector< std::vector<double> > > all_dwind;
	std::vector< std::vector< std::vector<double> > > all_dtmin;
	std::vector< std::vector< std::vector<double> > > all_dtmax;

	// Timers for keeping track of progress through the simulation
	Timer tprogress,tmute;
	static const int MUTESEC=20; // minimum number of sec to wait between progress messages

	// [Step 17a (F-12 sub-milestone C1.1) of unified-codebase rebuild
	//  (2026-05-10): per-cell state cache for year_outer mode, populated
	//  by preload_all_climate(gridcell, ...) and consumed by
	//  getclimate_for_year(gridcell, ...). Allows year_outer to serve
	//  per-cell-per-year climate without invoking the existing per-day
	//  stateful getclimate() driver, which would otherwise leak per-cell
	//  state (current_grid_index, ndep, spinup_year_idx) across
	//  year-outer's cell-switches.
	//
	//  Both maps keyed by (lon, lat) coordinate pair to identify the
	//  cell — avoids Gridcell* identity issues if the framework
	//  re-creates Gridcell objects between phases (preload phase uses
	//  a different Gridcell instance than the year-outer per-cell-inner
	//  loop's main Gridcell objects in framework.cpp).
	//  - DKB 2026-05-10]

	/// Per-cell cache of cell_idx (== current_grid_index at preload time);
	/// looked up by getclimate_for_year via (lon, lat).
	std::map<std::pair<double,double>, int> year_outer_cell_idx;

	/// Per-cell cache of NDepData state. Each entry is a value-copy of
	/// `ndep` taken right after getgridcell -> ndep.getndep set it for
	/// that cell. getclimate_for_year calls get_one_calendar_year on the
	/// cached NDepData (NOT on the shared `ndep` member).
	std::map<std::pair<double,double>, Lamarque::NDepData> year_outer_ndep_cache;

};

#endif // LPJ_GUESS_IMOGEN_INPUT_H
