///////////////////////////////////////////////////////////////////////////////////////
/// \file imogenoutput.h
/// \brief LPJ-GUESS-side handshake writer for the LPJG <-> IMOGEN coupled-model loop
///
/// This module implements the "handshake" output side of the LPJ-GUESS <-> IMOGEN
/// coupling protocol. It writes four files at <DIR_COMMON>/LPJG_main/IMOGEN/:
///
///   imogen_lpjg_flux.txt           year, NEE_PgC                (timeseries)
///   imogen_lpjg_ch4_n2o_flux.txt   year, CH4_TgCH4, N2O_TgN2O   (timeseries)
///   imogen_lpjg.txt                control state for next year   (overwritten)
///   done                           handshake marker             (touched per year)
///
/// The IMOGEN engine (in-process via lpjguess/modules/climatemodel.cpp, or the
/// standalone Fortran binary at imogen/code/imogen_lpjg) reads these files at
/// each year boundary to obtain LPJ-GUESS's NEE / CH4 / N2O feedback for the
/// just-completed year.
///
/// CADENCE
///
///   - Per-gridcell accumulation in outannual()
///   - Year-change detection at start of outannual: if current year != accumulator's
///     year, the previous year's accumulator is FLUSHED (4 files written) and
///     reset for the new year.
///   - The very last year is flushed in the destructor (since no year-change
///     after the final outannual call would otherwise trigger the flush).
///
/// MODE-GATING
///
///   IMOGENConfig::coupling_mode is checked at the top of every flush_year() call:
///     - "tight"      -> all 4 files written; IMOGEN engine consumes them
///     - "prescribed" -> all 4 files written but the IMOGEN engine reads
///                       FILE_LPJG_FLUX from a static path in the ins file (bug
///                       C35; see CMI section 3.7) so the LPJG-side files act
///                       only as diagnostics
///     - "loose"      -> NO files written; LPJG runs against a pre-baked IMOGEN
///                       climate library on disk
///   Default is "tight" (set at parameters.cpp).
///
/// ARCHITECTURAL CAVEAT (FOLLOW-UP F-10)
///
///   The current LPJ-GUESS framework loop is per-gridcell-outer / per-day-inner
///   across all years (framework.cpp:411-516). Each gridcell processes ALL its
///   years before the next gridcell starts. This is FUNDAMENTALLY INCOMPATIBLE
///   with a globally-synchronized per-year handshake: when gridcell-1 finishes
///   year-1, gridcell-2 has not even started year-1, yet the handshake fires.
///
///   Consequence: in v1.0, the per-year flush writes per-gridcell-rolling
///   values, NOT globally-aggregated values. The 4 files contain non-empty,
///   per-gridcell-sensible numbers (which satisfies V.1 step 8's verification
///   milestone) but represent only the gridcells processed up to the moment of
///   the flush, not the full grid.
///
///   In tight-coupling production runs of v1.0, this means IMOGEN receives
///   one-step-stale and partial NEE feedback; CO2 trajectory at step 17's
///   validation against NOAA GMD may show systematic bias.
///
///   PHASE 2 RECOMMENDATION (per user guidance 2026-05-06):
///     Add a runtime parameter (e.g. "framework_loop_mode = year_outer") that
///     gates a NEW per-year-outer / per-gridcell-inner code path which lives
///     ALONGSIDE the existing per-gridcell-outer loop. Do NOT alter the
///     existing framework.cpp behavior; instead, add the alternate loop as
///     a sibling code path that runs when the parameter is set, leaving
///     existing default behavior unchanged. This mirrors the LandSyMM-fork-
///     into-LPJ-GUESS-LTS integration pattern from the predecessor project.
///
/// \author Daniel Bampoh, 2026-05-06
///////////////////////////////////////////////////////////////////////////////////////

#ifndef LPJ_GUESS_IMOGEN_OUTPUT_H
#define LPJ_GUESS_IMOGEN_OUTPUT_H

#include "outputmodule.h"
#include <string>

namespace GuessOutput {

/// LPJ-GUESS-side handshake writer for the LPJG <-> IMOGEN coupled-model loop.
class ImogenOutput : public OutputModule {
public:
	ImogenOutput();
	~ImogenOutput();

	// Implemented OutputModule interface (see outputmodule.h):
	void init();
	void outannual(Gridcell& gridcell);

	// No-op overrides (this module only emits at year boundaries):
	void outdaily(Gridcell& gridcell)                  {}
	void outharvest(Gridcell& gridcell)                {}
	void outharvest_justphupvd(Gridcell& gridcell)     {}
	void outannual_ggcmi(Gridcell& gridcell)           {}
	void openlocalfiles(Gridcell& gridcell)            {}
	void closelocalfiles(Gridcell& gridcell)           {}
	void openlocalfiles_ggcmi()                        {}
	void closelocalfiles_ggcmi()                       {}

	/// Public escape hatch so climatemodel.cpp's in-process IMOGEN engine can
	/// explicitly trigger a flush of the just-completed year's data right before
	/// its polling loop activates. Optional; useful for tight-coupling timing
	/// control. Idempotent: a no-op if no pending year is buffered.
	void flush_pending_year();

	// =========================================================================
	// Step 17b (F-12 sub-milestone C2 core; 2026-05-11) — globally-
	// synchronized year-boundary flush for year_outer + MPI mode
	// =========================================================================
	//
	// Sibling to flush_year() but designed for the year_outer code path
	// (framework.cpp; gated on IMOGENConfig::framework_loop_mode == "year_outer")
	// + multi-rank MPI scenarios. Performs MPI_Allreduce(MPI_SUM) over per-rank
	// flux contributions (accum_NEE_kgC, accum_CH4_gCH4C, accum_N2O_kgN,
	// accum_area_m2, accum_gridcell_count) so the lead rank (rank 0) writes a
	// GLOBALLY-AGGREGATED handshake file rather than the per-rank-local values
	// that flush_year() would produce.
	//
	// IN SINGLE-PROCESS MODE (non-MPI build OR no -parallel CLI flag): falls
	// back to local flush semantics — the per-rank accumulators ARE the
	// global values when there's only one rank, so the MPI_Allreduce reduces
	// to a no-op and only rank 0 (= self) writes. Functionally identical to
	// the existing flush_year() in single-process; just called explicitly by
	// framework.cpp at the year boundary instead of implicitly by outannual's
	// year-change-detection. Sets accum_year=-1 after flush, which naturally
	// suppresses outannual's subsequent auto-flush on year+1 cell 0.
	//
	// CALLED BY: framework.cpp year_outer block, after the per-year cell inner
	// loop completes, gated on IMOGENConfig::framework_loop_mode == "year_outer".
	// In gridcell_outer mode this method is NEVER called; the existing
	// outannual/dtor auto-flush mechanism remains active.
	//
	// RESOLVES the F-10 architectural caveat for multi-rank MPI year_outer
	// mode: globally-aggregated values rather than per-gridcell-rolling.
	void flush_year_globally_synchronized(int year);

	/// Singleton-pointer accessor for framework.cpp year_outer's explicit
	/// flush call. Returns nullptr if ImogenOutput hasn't been instantiated
	/// (e.g., the output module wasn't registered for this run, or the
	/// destructor has already fired during program teardown). Pattern mirrors
	/// the existing `output_channel` global at outputmodule.h:227.
	///
	/// Set in ImogenOutput::ImogenOutput() constructor.
	/// Cleared in ImogenOutput::~ImogenOutput() destructor.
	///
	/// In the (current) v1.0 design only ONE ImogenOutput instance exists per
	/// process (the registry creates exactly one at startup); the static
	/// pointer simply caches that instance for fast lookup from framework.cpp.
	static ImogenOutput* get_instance() { return instance_; }

private:

	/// Write the 4 handshake files for the given year using the current
	/// accumulators. Called from outannual on year-change and from the
	/// destructor for the final year. Mode-gated by IMOGENConfig::coupling_mode.
	void flush_year(int year);

	/// Reset the per-year accumulators to zero.
	void reset_accumulators();

	/// Compute approximate gridcell area in m^2 from latitude and the standard
	/// 0.5 deg LPJ-GUESS grid resolution. Spherical-Earth approximation.
	static double gridcell_area_m2(double lat_deg);

	// =========================================================================
	// Per-year rolling accumulators (units below at gridcell-area-weighted scale)
	// =========================================================================

	/// Calendar year currently being accumulated; -1 means "no year yet".
	int accum_year;

	/// Accumulated net-ecosystem-exchange of carbon for accum_year, in kgC.
	/// Sign convention: positive = source to atmosphere (NEE > 0 emits CO2).
	double accum_NEE_kgC;

	/// Accumulated CH4 emissions for accum_year, in g (CH4-C basis).
	/// Multiplied by 16/12 at flush time to convert CH4-C -> CH4 (molar mass).
	double accum_CH4_gCH4C;

	/// Accumulated N2O emissions for accum_year, in kgN.
	/// Multiplied by 44/28 at flush time to convert N -> N2O (molar mass).
	double accum_N2O_kgN;

	/// Cumulative gridcell area (m^2) summed over all gridcells contributing
	/// to accum_year. Used as a sanity-check / diagnostic; not strictly needed
	/// for the flux conversions (each per-gridcell flux is already
	/// area-multiplied at accumulation time).
	double accum_area_m2;

	/// Path to <DIR_COMMON>/LPJG_main/IMOGEN/ where the 4 handshake files live.
	/// Captured once at init() for performance; re-derived from IMOGENConfig
	/// if needed.
	std::string handshake_dir;

	/// True before the first year is flushed (so we know to TRUNC the
	/// timeseries files at first write rather than APPEND).
	bool first_flush;

	/// True if accumulator state is non-zero (i.e. there's a pending year to
	/// flush at destructor time). Set to false after every flush_year() call.
	bool year_pending;

	/// Bookkeeping: count of gridcells contributing to accum_year. Useful for
	/// diagnostic banner at flush time and for F-10 documentation.
	int accum_gridcell_count;

	// =========================================================================
	// Step 17b (F-12 sub-milestone C2 core; 2026-05-11) — singleton-pointer
	// for framework.cpp year_outer to look up the live ImogenOutput instance
	// =========================================================================
	//
	// Mirrors the existing `output_channel` global at outputmodule.h:227. Set
	// to `this` in ImogenOutput::ImogenOutput() constructor; cleared (set to
	// nullptr) in ImogenOutput::~ImogenOutput() destructor. Accessed via the
	// public get_instance() static accessor above.
	//
	// In the (current) v1.0 design only ONE ImogenOutput instance exists per
	// process (the OutputModuleRegistry creates exactly one at startup); the
	// pointer caches that one instance for fast lookup from framework.cpp.
	static ImogenOutput* instance_;
};

}

#endif // LPJ_GUESS_IMOGEN_OUTPUT_H
