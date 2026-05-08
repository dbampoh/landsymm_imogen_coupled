#!/bin/bash
# =============================================================================
# scripts/cluster/env_owl.sh — module-load template for KIT IMK-IFU `owl`
# =============================================================================
#
# This file is sourced by scripts/cluster/run_coupled.sbatch at run start to
# set up the cluster's compiler + MPI + NetCDF + HDF5 environment.
#
# STATUS: PLACEHOLDER VALUES (2026-05-08 / step 16).
# The exact module names + versions on the KIT IMK-IFU `owl` cluster need to
# be confirmed via SSH session with the user on the actual cluster. Once
# confirmed, this file gets refined with the canonical module-load lines
# and committed as a step-16 follow-up.
#
# Likely versions per the prior chat handoff Part 4 §17 + Part 5 §16:
#   - gcc/14
#   - cmake/3.29
#   - netcdf-c/4.9
#   - netcdf-fortran/4.6
#   - openmpi/5.0
#
# These are PLACEHOLDERS; refine when the user does the SSH session-back-and-forth.
#
# USAGE
# -----
#     source scripts/cluster/env_owl.sh
#
# REFERENCES
# ----------
# - prior chat handoff Part 4 §17 (build environment specifics for cluster)
# - prior chat handoff Part 5 §16 (the cluster scripts plan)
# - scripts/cluster/make_guess.sh (consumes this env for cluster MPI build)
# =============================================================================

# Detect whether `module` is available (it is on most SLURM clusters; not on
# workstations). If not, no-op so this script can be safely sourced from
# the workstation parallel mimic test as well.
if ! command -v module &>/dev/null; then
  echo "[env_owl.sh] 'module' command not available; skipping module loads"
  echo "             (this is expected on the workstation parallel mimic test)"
  return 0 2>/dev/null || exit 0
fi

# -----------------------------------------------------------------------------
# Module loads (PLACEHOLDER VALUES; refine via SSH on owl)
# -----------------------------------------------------------------------------
# When uncommenting + populating, ensure module versions match what's actually
# available on owl. Use `module avail` on the cluster to enumerate.

# module purge

# module load gcc/14                      # or whatever the canonical compiler is
# module load cmake/3.29                  # cmake >= 3.10 required by lpjguess/CMakeLists.txt
# module load openmpi/5.0                 # for find_package(MPI) in cmake
# module load netcdf-c/4.9                # NetCDF C library (used by lpjguess + IMOGEN)
# module load netcdf-fortran/4.6          # for the Fortran IMOGEN engine

# -----------------------------------------------------------------------------
# Convenience env exports (uncomment + adapt as needed)
# -----------------------------------------------------------------------------
# export NETCDF_INCLUDE_DIR="$(pkg-config --variable=includedir netcdf 2>/dev/null)"
# export NETCDF_C_LIBRARY="$(pkg-config --libs-only-l netcdf 2>/dev/null | sed 's/-l/lib/')"

# -----------------------------------------------------------------------------
# Sanity check — print the loaded environment
# -----------------------------------------------------------------------------
echo "[env_owl.sh] Loaded modules:"
module list 2>&1 | head -20 || echo "  (module list unavailable)"

if command -v mpicxx &>/dev/null; then
  echo "[env_owl.sh] mpicxx: $(which mpicxx)"
  echo "[env_owl.sh] mpicxx --version: $(mpicxx --version 2>&1 | head -1)"
else
  echo "[env_owl.sh] WARNING: mpicxx not in PATH (MPI module not loaded?)"
fi

if command -v nc-config &>/dev/null; then
  echo "[env_owl.sh] nc-config --prefix: $(nc-config --prefix 2>/dev/null || echo 'unavailable')"
fi
