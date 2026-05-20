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

	// [Block 8.0.2 T_seq Installment-1 (B4 8-field consumer wiring backport):
	//  Tmin / Tmax per-day arrays for IMOGEN engine's Tmin_anom.dat /
	//  Tmax_anom.dat outputs (per-year ASCII files written by the rebuild
	//  engine post-step-9.5-B2 / step-17b-B4 work). Backport from rebuild's
	//  lpjguess/modules/imogencfx.h lines 254-257.
	//  - DKB 2026-05-20 block 8.0.2]
	/// Tmin (daily minimum temperature) for current gridcell and current year (deg C; K->C conversion applied in get_climate_for_gridcell)
	double dtmin[Date::MAX_YEAR_LENGTH];
	/// Tmax (daily maximum temperature) for current gridcell and current year (deg C; K->C conversion applied in get_climate_for_gridcell)
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

	// [Block 8.0.2 T_seq Installment-1 (B4 8-field consumer wiring backport):
	//  file_tmin / file_tmax paths for IMOGEN engine's Tmin_anom.dat /
	//  Tmax_anom.dat per-year outputs. Backport from rebuild's
	//  lpjguess/modules/imogen_input.h lines 308-309 + corresponding
	//  imogencfx-side wiring. Set in .ins via file_tmin / file_tmax
	//  parameters pointing at <DIR_COMMON>/IMOGEN/output/YYYY/Tmin_anom.dat
	//  and Tmax_anom.dat. Empty path => engine output not consumed (graceful
	//  no-op in readenv per existing pattern). - DKB 2026-05-20 block 8.0.2]
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

	// [Block 8.0.3 T_seq Installment-1 surgical site (h) — added at session 8.0.3
	//  acceptance-test execution per `notes/B47.md` §4.2 amendment:
	//  FIRST_SPINUP_YEAR was 1871 (legacy era; assumed engine produces
	//  1871-1900 climate library for the spinup cycle). Under T_seq, the
	//  rebuild's engine library starts at year 1900 (no pre-1900 dirs —
	//  intermediary_py covers 1900-2100 only per B34(β); engine YEAR1=1900);
	//  trunk's spinup logic at imogencfx.cpp::getclimate uses
	//  `imogen_year = FIRST_SPINUP_YEAR + spinup_year_idx` which would
	//  attempt to open <DIR_COMMON>/IMOGEN/output/1871/T_anom.dat etc.
	//  → file-not-found failure. Mismatch surfaced at session 8.0.3
	//  pre-flight (classic Rule #9 datapoint — harness-authoring + pre-flight
	//  inventory surfaces latent defect dormant pre-T_seq because F-10
	//  deadlock blocked rebuild's LPJG main loop + trunk's exit(200) regression
	//  blocked trunk's). Fix: align FIRST_SPINUP_YEAR with engine library
	//  coverage (1900). Spinup now cycles imogen_year in [1900..1929]; all
	//  years in engine library coverage; physically reasonable (spinup against
	//  1900-1929 climate = 30 distinct early-historical years).
	//  NEW B49 filed for long-term parametrize-as-.ins fix (analogous to
	//  B45 for the 1900/1901/2100/1871 sentinels in climatemodel.cpp;
	//  TRUNK-RELEVANT to BOTH forks — rebuild's lpjguess/modules/imogencfx.h:294
	//  has same hardcoded 1871 + will need same fix in Installment-2 era
	//  when rebuild's LPJG main loop eventually runs against pre-baked library
	//  post-F-12 tight-coupling resolution).
	//  - DKB 2026-05-20 block 8.0.3]
	static const int FIRST_SPINUP_YEAR = 1900;  // was 1871; aligned with engine library coverage under T_seq
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
	// [Block 8.0.2 T_seq Installment-1 (B4 8-field consumer wiring backport):
	//  Tmin / Tmax 3D storage [year][grid][month|day]. Same shape as all_temp
	//  etc. Backport from rebuild's lpjguess/modules/imogencfx.h
	//  lines (analogous all_dtmin / all_dtmax addition).
	//  - DKB 2026-05-20 block 8.0.2]
	std::vector< std::vector< std::vector<double> > > all_dtmin;
	std::vector< std::vector< std::vector<double> > > all_dtmax;

	// Timers for keeping track of progress through the simulation
	Timer tprogress, tmute;
	static const int MUTESEC = 20; // minimum number of sec to wait between progress messages

};

#endif // LPJ_GUESS_IMOGEN_INPUT_H
