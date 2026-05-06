///////////////////////////////////////////////////////////////////////////////////////
/// \file imogenoutput.cpp
/// \brief Implementation of the LPJ-GUESS-side handshake writer (see imogenoutput.h)
///
/// Step 8 of the unified-codebase rebuild. See:
///   - imogenoutput.h for class documentation, cadence, mode-gating, and the
///     architectural caveat (follow-up F-10) regarding the per-gridcell-outer
///     framework loop ordering and its impact on tight-coupling synchronization.
///   - notes/STEP_8.md for the per-step verification record.
///   - EXECUTION_PLAN.md V.1 step 8 for the verification milestone.
///
/// \author Daniel Bampoh, 2026-05-06
///////////////////////////////////////////////////////////////////////////////////////

#include "config.h"
#include "imogenoutput.h"
#include "guess.h"
#include "parameters.h"
#include "shell.h"

#include <fstream>
#include <iomanip>
#include <cmath>
#include <sys/stat.h>      // for mkdir
#include <sys/types.h>

namespace GuessOutput {

// =============================================================================
// REGISTRATION
// =============================================================================

REGISTER_OUTPUT_MODULE("imogenoutput", ImogenOutput)

// =============================================================================
// CONSTANTS
// =============================================================================

/// Earth radius in metres for spherical-Earth gridcell-area approximation.
static const double EARTH_RADIUS_M = 6371000.0;

/// Grid resolution in degrees, assumed for the LPJ-GUESS / LPJG-IMOGEN-coupled
/// reference setup (the 62 538-cell production gridlist is on a 0.5 deg grid).
/// If a future setup uses a different resolution, this constant should be
/// promoted to an ins-file parameter or read from imogencfx::spatial_resolution.
static const double GRID_RES_DEG = 0.5;

/// Molar-mass conversion: CH4 (16 g/mol) per CH4-C (12 g/mol).
static const double CH4_PER_CH4C = 16.0 / 12.0;

/// Molar-mass conversion: N2O (44 g/mol) per N (28 g/mol N2 basis = 14 g/mol N
/// times 2 N atoms in N2O, hence 14 * 2 / 28 = 1; corrected: N2O contains 2 N
/// atoms, so 1 mol N2O has 28 g of N. Therefore 1 kgN -> kgN2O multiplier =
/// 44/28).
static const double N2O_PER_N = 44.0 / 28.0;

// =============================================================================
// ImogenOutput methods
// =============================================================================

ImogenOutput::ImogenOutput()
	: accum_year(-1),
	  accum_NEE_kgC(0.0),
	  accum_CH4_gCH4C(0.0),
	  accum_N2O_kgN(0.0),
	  accum_area_m2(0.0),
	  handshake_dir(""),
	  first_flush(true),
	  year_pending(false),
	  accum_gridcell_count(0) {
	// No declare_parameter calls -- coupling_mode is registered by imogencfx
	// (see imogencfx.cpp around line 333+). All paths for this module are
	// derived from IMOGENConfig::DIR_COMMON at init() time.
}

ImogenOutput::~ImogenOutput() {
	// Final-year flush. The framework's per-gridcell-outer loop means there
	// is no "end of year N+1" trigger after the LAST gridcell finishes year
	// N (its last year). The destructor catches this case at sim-end teardown.
	if (year_pending && accum_year >= 0) {
		dprintf("[ImogenOutput] Final-year flush at destructor: year=%d (gridcells_seen=%d)\n",
		        accum_year, accum_gridcell_count);
		flush_year(accum_year);
	}
}

void ImogenOutput::init() {
	// Capture handshake dir path; ensure the directory exists (mkdir -p
	// equivalent). LPJG framework calls init() AFTER ins-file is read, so
	// IMOGENConfig::DIR_COMMON is populated by this point.
	handshake_dir = std::string((char*)IMOGENConfig::DIR_COMMON) + "/LPJG_main/IMOGEN/";

	// Best-effort mkdir -p. Errors are non-fatal; the first write will fail
	// loudly if the directory truly cannot be created.
	const std::string lpjg_main = std::string((char*)IMOGENConfig::DIR_COMMON) + "/LPJG_main";
	mkdir(lpjg_main.c_str(),       0755);
	mkdir(handshake_dir.c_str(),   0755);

	reset_accumulators();
	accum_year = -1;
	first_flush = true;
	year_pending = false;
	accum_gridcell_count = 0;

	// Mode banner -- supports the "units-integrity discipline" startup-banner
	// rule (EXECUTION_PLAN section I.D.5 + CONTRIBUTING.md).
	dprintf("[ImogenOutput] init: handshake_dir=%s coupling_mode='%s'\n",
	        handshake_dir.c_str(),
	        (char*)IMOGENConfig::coupling_mode);
}

void ImogenOutput::outannual(Gridcell& gridcell) {
	// =========================================================================
	// 1. YEAR-CHANGE DETECTION
	// =========================================================================
	const int this_year = date.get_calendar_year();

	if (accum_year >= 0 && this_year != accum_year) {
		// New year started; flush the just-completed year and reset.
		// (See notes/FOLLOWUPS.md F-10 for caveats: in the per-gridcell-outer
		// framework loop, "just-completed" actually means "complete only for
		// gridcells processed so far". Documented limitation.)
		flush_year(accum_year);
		reset_accumulators();
	}
	accum_year = this_year;

	// =========================================================================
	// 2. ACCUMULATE THIS GRIDCELL'S CONTRIBUTION
	// =========================================================================
	// Mirror commonoutput.cpp's outannual flux-accumulation pattern (lines
	// ~1240-1273). The unit at gridcell-mean is kgC/m^2/yr for C, kgN/m^2/yr
	// for N, gC/m^2/yr (CH4-C basis) for CH4. We multiply by gridcell area
	// to get absolute mass per gridcell.

	double flux_man   = 0.0, flux_veg   = 0.0, flux_repr  = 0.0;
	double flux_soil  = 0.0, flux_fire  = 0.0, flux_est   = 0.0;
	double flux_n2o_fire_kgNm2 = 0.0, flux_n2o_soil_kgNm2 = 0.0;
	double flux_ch4_gCm2 = 0.0;  // annual sum of monthly mch4 contributions

	Gridcell::iterator gc_itr = gridcell.begin();
	while (gc_itr != gridcell.end()) {
		Stand& stand = *gc_itr;
		stand.firstobj();

		while (stand.isobj) {
			Patch& patch = stand.getobj();

			const double to_gc_avg =
				stand.get_gridcell_fraction() / static_cast<double>(stand.npatch());

			// Carbon fluxes in kgC/m^2/yr (gridcell-mean-weighted).
			// Sign convention mirrors commonoutput.cpp:1254-1259:
			//   man, veg, repr have the -1.0 sign baked into the assignment
			//   so that NEE = sum(all six) is positive when net source to atm.
			flux_man  += -patch.fluxes.get_annual_flux(Fluxes::MANUREC) * to_gc_avg;
			flux_veg  += -patch.fluxes.get_annual_flux(Fluxes::NPP)     * to_gc_avg;
			flux_repr += -patch.fluxes.get_annual_flux(Fluxes::REPRC)   * to_gc_avg;
			flux_soil +=  patch.fluxes.get_annual_flux(Fluxes::SOILC)   * to_gc_avg;
			flux_fire +=  patch.fluxes.get_annual_flux(Fluxes::FIREC)   * to_gc_avg;
			flux_est  +=  patch.fluxes.get_annual_flux(Fluxes::ESTC)    * to_gc_avg;

			// N2O in kgN/m^2/yr (gridcell-mean-weighted)
			flux_n2o_fire_kgNm2 +=
				patch.fluxes.get_annual_flux(Fluxes::N2O_FIRE) * to_gc_avg;
			flux_n2o_soil_kgNm2 +=
				patch.fluxes.get_annual_flux(Fluxes::N2O_SOIL) * to_gc_avg;

			// CH4: monthly fluxes in g(CH4-C)/m^2/month; sum over 12 months.
			for (int m = 0; m < 12; m++) {
				flux_ch4_gCm2 +=
					patch.fluxes.get_monthly_flux(Fluxes::CH4C, m) * to_gc_avg;
			}

			stand.nextobj();
		}

		++gc_itr;
	}

	// NEE per gridcell-m^2, kgC/m^2/yr. Positive = source to atmosphere.
	const double NEE_kgCm2 =
		flux_man + flux_veg + flux_repr + flux_soil + flux_fire + flux_est;

	// Convert to absolute mass per gridcell using cell area.
	const double area_m2 = gridcell_area_m2(gridcell.get_lat());

	accum_NEE_kgC    += NEE_kgCm2 * area_m2;
	accum_CH4_gCH4C  += flux_ch4_gCm2 * area_m2;
	accum_N2O_kgN    += (flux_n2o_fire_kgNm2 + flux_n2o_soil_kgNm2) * area_m2;
	accum_area_m2    += area_m2;
	accum_gridcell_count++;
	year_pending = true;
}

void ImogenOutput::flush_pending_year() {
	// Public escape hatch for climatemodel.cpp to call before its polling loop.
	// No-op if nothing pending.
	if (year_pending && accum_year >= 0) {
		dprintf("[ImogenOutput] flush_pending_year called externally: year=%d\n",
		        accum_year);
		flush_year(accum_year);
		reset_accumulators();
	}
}

void ImogenOutput::flush_year(int year) {
	// =========================================================================
	// MODE GATE: only "tight" or "prescribed" modes write the handshake files.
	// "loose" mode runs LPJG against pre-baked IMOGEN climate on disk; no
	// per-year handshake files are produced.
	// =========================================================================
	const std::string mode = std::string((char*)IMOGENConfig::coupling_mode);
	if (mode == "loose") {
		dprintf("[ImogenOutput] flush_year(%d) skipped: coupling_mode='loose'\n", year);
		year_pending = false;
		return;
	}

	// =========================================================================
	// UNIT CONVERSIONS to PgC / TgCH4 / TgN2O at global scale
	// =========================================================================
	// accum_NEE_kgC      -> PgC/yr:    *  1e-12  (kgC -> Pg)
	// accum_CH4_gCH4C    -> TgCH4/yr:  *  CH4_PER_CH4C  *  1e-12  (gC -> g CH4 -> Tg)
	// accum_N2O_kgN      -> TgN2O/yr:  *  N2O_PER_N     *  1e-9   (kgN -> kgN2O -> Tg)
	const double NEE_PgC    = accum_NEE_kgC   * 1e-12;
	const double CH4_TgCH4  = accum_CH4_gCH4C * CH4_PER_CH4C * 1e-12;
	const double N2O_TgN2O  = accum_N2O_kgN   * N2O_PER_N    * 1e-9;

	// =========================================================================
	// 1. imogen_lpjg_flux.txt -- timeseries of (year, NEE_PgC). APPEND mode
	//    after first flush, TRUNC on first to avoid stale data from prior runs.
	// =========================================================================
	{
		const std::ios_base::openmode mode_io =
			first_flush ? std::ios::out | std::ios::trunc
			            : std::ios::out | std::ios::app;
		std::ofstream f(handshake_dir + "imogen_lpjg_flux.txt", mode_io);
		if (f.is_open()) {
			f << year << "\t"
			  << std::fixed << std::setprecision(6) << NEE_PgC << "\n";
		} else {
			dprintf("[ImogenOutput] WARNING: could not open %simogen_lpjg_flux.txt\n",
			        handshake_dir.c_str());
		}
	}

	// =========================================================================
	// 2. imogen_lpjg_ch4_n2o_flux.txt -- timeseries of (year, CH4_TgCH4, N2O_TgN2O)
	// =========================================================================
	{
		const std::ios_base::openmode mode_io =
			first_flush ? std::ios::out | std::ios::trunc
			            : std::ios::out | std::ios::app;
		std::ofstream f(handshake_dir + "imogen_lpjg_ch4_n2o_flux.txt", mode_io);
		if (f.is_open()) {
			f << year << "\t"
			  << std::fixed << std::setprecision(6) << CH4_TgCH4 << "\t"
			  << std::fixed << std::setprecision(6) << N2O_TgN2O << "\n";
		} else {
			dprintf("[ImogenOutput] WARNING: could not open %simogen_lpjg_ch4_n2o_flux.txt\n",
			        handshake_dir.c_str());
		}
	}

	// =========================================================================
	// 3. imogen_lpjg.txt -- control state for IMOGEN's NEXT year. TRUNC each
	//    year (this file is overwritten, not appended).
	//    Schema mirrors version_A's predecessor reference:
	//      YEAR1 <next> !IN First year of the numerical experiment
	//      IYEND <next> !IN Stop year of the ENTIRE run
	//      YEAR1_LPJG <year1_lpjg> !IN First year of the whole LPJ-GUESS simulation
	//      SPINUP <bool>  !IN Are we in the spin-up phase?
	//      KEEPRUNNING <bool>  !IN keep imogen running
	//      FIRSTCALL <bool>  !IN very first call?
	// =========================================================================
	{
		const int next_year = year + 1;
		// SPINUP / KEEPRUNNING / FIRSTCALL flags: in v1.0 we conservatively
		// flag every year as non-spinup, keep-running, not-first-call so the
		// IMOGEN engine just advances year-by-year. For genuine spin-up phase
		// detection we'd need the first-historic-year and run-end year; that
		// would be reading from FIRSTHISTYEAR / IYEND ins parameters which
		// requires plumbing through the ins-file which is out of step-8 scope.
		// The IMOGEN-side polling loop's FIRSTCALL handling is fine with
		// FIRSTCALL=FALSE for year 2+ since the F-4 fix at step 7 makes the
		// first-call special case not needed.
		std::ofstream f(handshake_dir + "imogen_lpjg.txt",
		                std::ios::out | std::ios::trunc);
		if (f.is_open()) {
			f << "YEAR1 "      << next_year << " !IN First year of the numerical experiment\n";
			f << "IYEND "      << next_year << " !IN Stop year of the ENTIRE run\n";
			f << "YEAR1_LPJG " << next_year << " !IN First year of the whole LPJ-GUESS simulation\n";
			f << "SPINUP FALSE !IN Are we in the spin-up phase of LPJ-GUESS?\n";
			f << "KEEPRUNNING TRUE !IN control flag to keep imogen running\n";
			f << "FIRSTCALL FALSE !IN Is this the very first call to IMOGEN from LPJ-GUESS\n";
		} else {
			dprintf("[ImogenOutput] WARNING: could not open %simogen_lpjg.txt\n",
			        handshake_dir.c_str());
		}
	}

	// =========================================================================
	// 4. done -- handshake marker. Touched LAST so the IMOGEN engine never sees
	//    a "done" while data writes are still in progress.
	// =========================================================================
	{
		std::ofstream f(handshake_dir + "done", std::ios::out | std::ios::trunc);
		if (f.is_open()) {
			f << "Climate files written for year " << year << "\n";
		} else {
			dprintf("[ImogenOutput] WARNING: could not open %sdone\n",
			        handshake_dir.c_str());
		}
	}

	// =========================================================================
	// DIAGNOSTIC BANNER (units-integrity discipline section I.D.5)
	// =========================================================================
	dprintf("[ImogenOutput] flushed year=%d (gridcells_seen=%d, area_m2=%.3e):"
	        " NEE=%.6f PgC, CH4=%.6f TgCH4, N2O=%.6f TgN2O [F-10 caveat: per-gridcell-rolling]\n",
	        year, accum_gridcell_count, accum_area_m2,
	        NEE_PgC, CH4_TgCH4, N2O_TgN2O);

	first_flush = false;
	year_pending = false;
}

void ImogenOutput::reset_accumulators() {
	accum_NEE_kgC        = 0.0;
	accum_CH4_gCH4C      = 0.0;
	accum_N2O_kgN        = 0.0;
	accum_area_m2        = 0.0;
	accum_gridcell_count = 0;
}

// static
double ImogenOutput::gridcell_area_m2(double lat_deg) {
	// Spherical-Earth approximation; same convention used widely in LPJ-GUESS
	// adapter scripts and the predecessor framework's R post-processing tools.
	//
	//   area(lat, dlon, dlat) = R^2 * (dlon * pi/180) *
	//                           (sin((lat + dlat/2) * pi/180) -
	//                            sin((lat - dlat/2) * pi/180))
	//
	// For dlon = dlat = 0.5 deg this reduces to
	//   area(lat) ~ R^2 * (0.5 * pi/180)^2 * cos(lat * pi/180)   [for small dlat]
	// to leading order; we use the exact formula below.
	const double pi = 3.141592653589793;
	const double dlat_rad   = GRID_RES_DEG * pi / 180.0;
	const double dlon_rad   = GRID_RES_DEG * pi / 180.0;
	const double lat_rad    = lat_deg * pi / 180.0;
	const double sin_top    = std::sin(lat_rad + 0.5 * dlat_rad);
	const double sin_bottom = std::sin(lat_rad - 0.5 * dlat_rad);
	return EARTH_RADIUS_M * EARTH_RADIUS_M * dlon_rad * (sin_top - sin_bottom);
}

}  // namespace GuessOutput
