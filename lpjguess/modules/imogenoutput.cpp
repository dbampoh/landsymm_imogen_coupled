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

// =============================================================================
// [Step 17b (F-12 sub-milestone C2 core; 2026-05-11) — MPI integration]
//
// mpi.h must be included BEFORE stdio.h (and transitively before <fstream>
// via guess.h / shell.h) per the MPI-2 standard SEEK_SET / SEEK_CUR /
// SEEK_END pre-processor clash. Same discipline as parallel.cpp lines
// 10-15. Outside #ifdef HAVE_MPI guard, mpi.h is not pulled in and the
// MPI_Barrier / MPI_Allreduce calls below are stubbed out.
// =============================================================================
#ifdef HAVE_MPI
#include <mpi.h>
#endif

#include "config.h"
#include "imogenoutput.h"
#include "guess.h"
#include "parameters.h"
#include "parallel.h"      // GuessParallel::get_rank()
#include "shell.h"

#include <fstream>
#include <iomanip>
#include <cmath>
#include <sys/stat.h>      // for mkdir
#include <sys/types.h>

namespace GuessOutput {

// =============================================================================
// Step 17b (F-12 sub-milestone C2 core; 2026-05-11) — singleton-pointer
// static-member definition. Set to `this` in ctor; cleared in dtor. See
// imogenoutput.h for full design rationale + the singleton-vs-virtual-method
// design trade-off (we chose singleton to minimise touch surface on the
// OutputModule abstract base class which would otherwise need a new virtual
// method + corresponding stubs in 9+ existing output modules).
// =============================================================================
ImogenOutput* ImogenOutput::instance_ = nullptr;

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

/// Molar-mass conversion: kg N2O (molecule mass) per kg N (atom mass) when
/// the N atoms reside inside N2O molecules. N2O has 2 N atoms per molecule
/// (molecular formula N=N=O), so 1 mol of N2O contains 2 mol of N atoms,
/// i.e. 28 g of N (= 2 x 14). One mole of N2O weighs 44 g. Therefore the
/// conversion factor from kgN-as-N2O (the LPJG soil/fire N-cycle budget
/// convention; see Fluxes::N2O_FIRE + Fluxes::N2O_SOIL doc-comments at
/// guess.h:1240/1251 -- doc-comment start lines for ENUMs at lines 1243/1256
/// -- and the soil.N2O_mass pool doc-comment at guess.h:3850-3855) to kg of
/// N2O molecules is 44/28 = 1.5714... Cross-ref: this is the kgN -> kgN2O
/// conversion applied at flush_year() before the * 1e-9 kg -> Tg unit
/// conversion for imogen_lpjg_ch4_n2o_flux.txt. NOTE: the ngases.out N2O_fire
/// + N2O_soil columns are emitted in kgN/ha/yr (mass-of-N basis, NOT
/// mass-of-N2O-molecules basis -- see commonoutput.cpp:1759-1771 inline-
/// comment block); applying N2O_PER_N is what distinguishes the IMOGEN
/// handshake's TgN2O/yr output from the ngases.out kgN/ha/yr output.
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

	// [Step 17b C2 core 2026-05-11] Register this instance in the singleton
	// pointer so framework.cpp year_outer can look it up for the explicit
	// year-boundary flush_year_globally_synchronized() call. Only ONE
	// ImogenOutput is ever created (per OutputModuleRegistry::create_all_
	// modules contract), but we still guard against accidental re-creation.
	instance_ = this;
}

ImogenOutput::~ImogenOutput() {
	// Final-year flush. The framework's per-gridcell-outer loop means there
	// is no "end of year N+1" trigger after the LAST gridcell finishes year
	// N (its last year). The destructor catches this case at sim-end teardown.
	//
	// In year_outer mode (per step 17b C2 core), framework.cpp already calls
	// flush_year_globally_synchronized() at the end of EVERY year_idx (including
	// the last one), which sets year_pending=false + accum_year=-1. So this
	// destructor's flush_year guard is a no-op in that case. The guard is
	// kept in place for gridcell_outer mode (where it's still the only
	// final-year flush trigger).
	if (year_pending && accum_year >= 0) {
		dprintf("[ImogenOutput] Final-year flush at destructor: year=%d (gridcells_seen=%d)\n",
		        accum_year, accum_gridcell_count);
		flush_year(accum_year);
	}

	// [Step 17b C2 core 2026-05-11] Clear the singleton pointer. After this
	// returns, get_instance() returns nullptr and any framework.cpp
	// year_outer flush attempt is silently skipped (defensive null-check).
	if (instance_ == this) {
		instance_ = nullptr;
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
	//
	// [Step 9: imogen_nee_perturbation_factor multiplier (V.1 step-9
	//  verification helper) was applied here briefly then REMOVED at step
	//  9's wrap-up because the F-10 architectural deadlock means LPJG
	//  main loop never runs in v1.0 single-process mode -- so the helper
	//  could never affect anything observable. Resolution at follow-up
	//  F-12. - DKB 2026-05-07]
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

// =============================================================================
// [Step 17b (F-12 sub-milestone C2 core; 2026-05-11) — globally-synchronized
//  year-boundary flush for year_outer + MPI mode]
//
// Sibling to flush_year(). Performs MPI_Allreduce(MPI_SUM) over per-rank flux
// contributions before delegating the write to flush_year(); only the lead
// rank (rank 0) actually opens + writes the unified handshake file. All ranks
// participate in the Allreduce + reset_accumulators afterwards.
//
// IN SINGLE-PROCESS MODE (HAVE_MPI undefined OR GuessParallel::parallel false):
// MPI_Allreduce is skipped; rank-local accumulators ARE the global values when
// there's only one rank; rank 0 (= self via GuessParallel::get_rank()) writes
// via the existing flush_year() path. Functionally identical to outannual's
// implicit year-change-driven flush_year() in single-process — just called
// explicitly by framework.cpp at year-boundary instead.
//
// Sets accum_year=-1 after flush so outannual's subsequent year-change-
// detection at year+1 cell 0 is suppressed (existing logic at line 118:
// `if (accum_year >= 0 && this_year != accum_year)` is false when -1 < 0).
// This avoids double-flush in year_outer mode.
//
// Cross-references:
//   - imogenoutput.h public docstring for flush_year_globally_synchronized
//     (full design rationale + single-process fallback semantics)
//   - notes/STEP_17b.md §4.2 (C2 core implementation plan)
//   - notes/FOLLOWUPS.md F-10 (architectural caveat resolved by this method
//     in year_outer + MPI mode)
//   - framework/parallel.cpp (GuessParallel::parallel + get_rank() infrastructure)
//
// - DKB 2026-05-11
// =============================================================================
void ImogenOutput::flush_year_globally_synchronized(int year) {
	// =========================================================================
	// MODE GATE: only "tight" or "prescribed" modes write the handshake files.
	// Mirror the gate in flush_year (line 213-218) so we exit early in "loose"
	// mode WITHOUT calling MPI_Allreduce (which would otherwise block other
	// ranks if any of them have non-loose mode -- but coupling_mode is set
	// once at .ins-file parse time + shared across ranks, so all ranks agree).
	// =========================================================================
	const std::string mode = std::string((char*)IMOGENConfig::coupling_mode);
	if (mode == "loose") {
		dprintf("[ImogenOutput] flush_year_globally_synchronized(%d) skipped: coupling_mode='loose'\n", year);
		// Still need to reset state so outannual doesn't double-fire on year+1 cell 0
		reset_accumulators();
		year_pending = false;
		accum_year   = -1;
		return;
	}

	// =========================================================================
	// MPI Allreduce: aggregate per-rank contributions into per-rank-identical
	// global values. After this block, every rank has the same accum_* values
	// (the sum across all ranks). Only rank 0 will then write the file.
	//
	// MPI_Initialized() guard pattern mirrors imogencfx.cpp:381 +
	// imogen_input.cpp:221: queries MPI directly rather than relying on the
	// `GuessParallel::parallel` flag (which isn't exposed via parallel.h).
	// =========================================================================
#ifdef HAVE_MPI
	{
		int mpi_initialized_flag = 0;
		const bool mpi_active =
		    (MPI_Initialized(&mpi_initialized_flag) == MPI_SUCCESS) &&
		    (mpi_initialized_flag == 1);
		if (mpi_active) {
			// Each rank contributes its local accum_*; MPI_SUM across all
			// ranks produces the global aggregate. We use MPI_Allreduce so
			// every rank has the global values (useful for per-rank
			// diagnostic dprintfs below); the slight extra cost vs MPI_Reduce
			// is negligible for 4-rank workstation mimic or 16-rank cluster
			// smoke runs.

			double global_NEE = 0.0, global_CH4 = 0.0, global_N2O = 0.0;
			double global_area = 0.0;
			int    global_count = 0;

			MPI_Allreduce(&accum_NEE_kgC,        &global_NEE,   1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
			MPI_Allreduce(&accum_CH4_gCH4C,      &global_CH4,   1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
			MPI_Allreduce(&accum_N2O_kgN,        &global_N2O,   1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
			MPI_Allreduce(&accum_area_m2,        &global_area,  1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
			MPI_Allreduce(&accum_gridcell_count, &global_count, 1, MPI_INT,    MPI_SUM, MPI_COMM_WORLD);

			// Swap globals into accum_* so flush_year() below writes the
			// globally-aggregated values. The accum_* fields will be reset
			// shortly anyway via reset_accumulators(), so no need to save+restore.
			accum_NEE_kgC        = global_NEE;
			accum_CH4_gCH4C      = global_CH4;
			accum_N2O_kgN        = global_N2O;
			accum_area_m2        = global_area;
			accum_gridcell_count = global_count;
		}
	}
#endif

	// =========================================================================
	// Lead-rank-only write: avoid race conditions on the shared handshake
	// file. In single-process mode get_rank() returns 0 -> self writes (correct).
	// In multi-rank MPI mode, only rank 0 opens + writes the file; the other
	// ranks proceed directly to reset_accumulators below.
	// =========================================================================
	const int rank = GuessParallel::get_rank();
	if (rank == 0) {
		// flush_year() handles the actual file open + write + diagnostic
		// dprintf banner. We rely on it for correctness (mode gate already
		// passed above; flush_year's mode gate is a redundant safety check).
		flush_year(year);
	}

	// =========================================================================
	// All ranks reset state. After this returns, accum_* are zero +
	// accum_year=-1 + year_pending=false. outannual's subsequent year-change-
	// detection on year+1 cell 0 sees accum_year < 0 and skips its own
	// flush_year() auto-trigger (existing logic at imogenoutput.cpp:118).
	// =========================================================================
	reset_accumulators();
	accum_year   = -1;
	year_pending = false;

	// Per-rank diagnostic banner (useful for forensic debugging of MPI runs):
	// non-lead ranks log that they participated in the Allreduce + reset.
#ifdef HAVE_MPI
	{
		int mpi_initialized_flag = 0;
		const bool mpi_active =
		    (MPI_Initialized(&mpi_initialized_flag) == MPI_SUCCESS) &&
		    (mpi_initialized_flag == 1);
		if (mpi_active && rank != 0) {
			dprintf("[ImogenOutput rank=%d] flush_year_globally_synchronized(%d): "
			        "participated in MPI_Allreduce; reset_accumulators done; "
			        "lead rank wrote the unified handshake file\n",
			        rank, year);
		}
	}
#endif
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
