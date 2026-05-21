#!/bin/bash
# =============================================================================
# scripts/cluster/env_owl.sh — module-load template for KIT IMK-IFU `owl`
# =============================================================================
#
# This file is sourced by scripts/cluster/run_coupled.sbatch at run start to
# set up the cluster's compiler + MPI + NetCDF + HDF5 environment.
#
# STATUS: ✅ CANONICAL VALUES populated 2026-05-21 evening (block 8.1 close)
# per round 1 SSH paste-back capture from user's owl session. These 7 modules
# match the user's `.bash_profile` auto-load pattern (verified at session 9
# day 2 reconnaissance per `_chat_artifacts/b8_1_cluster_reconnaissance_2026-05-21/
# b81_user_bash_profile_inventory.log`). Architecture: AlmaLinux 9 x86_64 +
# Lmod + Spack 0.19.0; gcc-11.3.1 spack-base compiler family (system gcc
# 11.5.0 ABI-compatible).
#
# IMPORTANT: when the user invokes `setup_run_owl_with_scratch_lpj_work.sh`
# or `scripts/cluster/setup_run.sh` interactively after SSH login, the user's
# `.bash_profile` has ALREADY auto-loaded these 7 modules + dependencies
# (cyrus-sasl + bzip2 + gettext + sqlite + openssl + cuda transitively).
# This env_owl.sh is for: (a) future maintainers who don't have the user's
# bash profile; (b) the `scripts/cluster/run_coupled.sbatch` SLURM wrapper
# (which sources this) when the user's bash profile may not have been sourced
# in a batch context; (c) explicit documentation of the canonical cluster
# build environment.
#
# USAGE
# -----
#     source scripts/cluster/env_owl.sh
#
# REFERENCES
# ----------
# - `_chat_artifacts/b8_1_cluster_reconnaissance_2026-05-21/b81_user_bash_profile_inventory.log`
#   (round 1 SSH paste-back; canonical module list verified)
# - `_chat_artifacts/b8_1_cluster_reconnaissance_2026-05-21/b81_trunk_build_owl.log`
#   (G2 acceptance: trunk fork build PASS with these modules; sha1 40d36db64e5e...)
# - `_chat_artifacts/b8_1_cluster_reconnaissance_2026-05-21/b81_lpjguess_build_owl.log`
#   (G3 acceptance: lpjguess fork build PASS with these modules; sha1 4da4462a9f6b...)
# - User's `~/.bash_profile` on owl (canonical auto-load source)
# - `scripts/cluster/make_guess.sh` (consumes this env for cluster MPI build)
# - `scripts/cluster/run_coupled.sbatch` (consumes this env for SLURM batch)
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
# Canonical module loads (verified at block 8.1 close 2026-05-21)
# -----------------------------------------------------------------------------
# Per user's `.bash_profile` auto-load pattern verified at block 8.1 round 1.
# B48 hypothesis CONFIRMED Ubuntu-specific: cluster Spack-managed HDF5 1.12.2
# + libcurl 7.85.0 + rpath chain is consistent; no -lcurl workaround needed
# at cmake time (the workstation Ubuntu 24.04 B48 workaround is harmless
# but unnecessary on cluster). See `_chat_artifacts/b8_1_cluster_reconnaissance_2026-05-21/
# b81_trunk_build_owl.log` for G2 build evidence.
#
# CUDA module (loaded transitively via openmpi-cuda variant) is harmless for
# LPJ-GUESS which doesn't use GPUs; just inherited from the canonical openmpi
# variant the user prefers.

module purge

module load subversion/1.14.1-gcc-11.3.1
module load cmake/3.24.3-gcc-11.3.1
module load openmpi/4.1.4-gcc-11.3.1-cuda          # CUDA variant; OK; LPJG doesn't use GPUs
module load hdf5/1.12.2-gcc-11.3.1                 # NOT 1.14.5+ (avoids the Ubuntu B48 libcurl@CURL_OPENSSL_4 issue)
module load netcdf-c/4.9.0-gcc-11.3.1              # NetCDF C library (used by lpjguess + IMOGEN cfx + imogencfx)
module load zlib/1.2.13-gcc-11.3.1
module load netcdf-fortran/4.6.0-gcc-11.3.1        # for the Fortran IMOGEN engine

# -----------------------------------------------------------------------------
# Convenience env exports (Spack auto-populates these via module loads)
# -----------------------------------------------------------------------------
# After the module loads above, Spack has populated:
#   CMAKE_PREFIX_PATH    (cmake's find_package walks this chain)
#   MPICC + MPICXX + MPIF77 + MPIF90 (cmake's FindMPI uses these env vars)
#   NETCDF_C_ROOT + NETCDF_FORTRAN_ROOT + HDF5_ROOT + OPENMPI_ROOT
#   LD_LIBRARY_PATH (for runtime resolution of dynamic libs)
#   PKG_CONFIG_PATH (for nc-config + h5cc etc.)
# No manual export needed for the rebuild's cmake build to succeed.

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
