#!/bin/bash
# =============================================================================
# scripts/cluster/make_guess.sh — cluster-side build helper for LPJ-GUESS
# =============================================================================
#
# Simplified version of the IMK-IFU `make_guess.sh` (which had elaborate
# git/svn version-embedding + compiled/<archvariant>/ symlink machinery).
# Our unified-codebase rebuild's `lpjguess/build/` (workstation) and
# `lpjguess/build_mpi/` (cluster) provide simpler binary locations.
#
# USAGE
# -----
#     scripts/cluster/make_guess.sh [--mpi]
#
# OPTIONS
#   --mpi    Build with MPI enabled (uses mpicxx; produces lpjguess/build_mpi/guess)
#            Default: no-mpi (uses native cxx; produces lpjguess/build/guess)
#
# REQUIREMENTS
# ------------
# - cmake 3.x
# - c++ compiler (gcc-14 / clang on workstation; module-loaded gcc on cluster)
# - NetCDF C library + headers (Anaconda3 on workstation per Decision #8;
#   module-loaded netcdf-c on cluster)
# - Optional: mpicxx (for --mpi build)
#
# REFERENCES
# ----------
# - lpjguess/CMakeLists.txt lines 73-87: MPI auto-detection block
# - scripts/run_coupled.sh: workstation build path (Anaconda3 NetCDF)
# - scripts/cluster/env_owl.sh: cluster module-load template
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Parse args
# -----------------------------------------------------------------------------
USE_MPI=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mpi)  USE_MPI=1; shift ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \?//' | head -40
      exit 0
      ;;
    *) echo "ERROR: unknown arg '$1'"; exit 1 ;;
  esac
done

# -----------------------------------------------------------------------------
# Resolve repo root (script lives at scripts/cluster/)
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LPJG_DIR="${REPO_ROOT}/lpjguess"

if [[ ${USE_MPI} -eq 1 ]]; then
  BUILD_DIR="${LPJG_DIR}/build_mpi"
  echo "Building LPJ-GUESS with MPI enabled (build_mpi/)"
else
  BUILD_DIR="${LPJG_DIR}/build"
  echo "Building LPJ-GUESS without MPI (build/; workstation default)"
fi

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# -----------------------------------------------------------------------------
# CMake invocation
# -----------------------------------------------------------------------------
CMAKE_ARGS=()

if [[ ${USE_MPI} -eq 1 ]]; then
  # When --mpi: use mpicxx as the C++ compiler so find_package(MPI) succeeds
  # and HAVE_MPI is defined (per lpjguess/CMakeLists.txt lines 75-87)
  if ! command -v mpicxx &>/dev/null; then
    echo "ERROR: mpicxx not found in PATH. On cluster: run module loads first"
    echo "       (source scripts/cluster/env_owl.sh). On workstation: ensure"
    echo "       Anaconda3's MPICH is in PATH (PATH=\$ANACONDA_PREFIX/bin:\$PATH)."
    exit 1
  fi
  CMAKE_ARGS+=(-DCMAKE_CXX_COMPILER=mpicxx)
fi

# NetCDF preference (Anaconda3 on workstation; module-loaded on cluster)
ANACONDA3_PREFIX="${ANACONDA3_PREFIX:-${CONDA_PREFIX:-}}"
if [[ -z "${ANACONDA3_PREFIX}" && -d "/home/${USER}/anaconda3" ]]; then
  ANACONDA3_PREFIX="/home/${USER}/anaconda3"
fi

if [[ -n "${ANACONDA3_PREFIX:-}" && ${USE_MPI} -eq 0 ]]; then
  # Only use Anaconda3 NetCDF for non-MPI build (workstation case).
  # On cluster + MPI, prefer module-loaded NetCDF (consistent with cluster's
  # MPI implementation; mixing Anaconda3 NetCDF with cluster MPI causes ABI issues).
  echo "Using Anaconda3 NetCDF: ${ANACONDA3_PREFIX}"
  CMAKE_ARGS+=(
    "-DCMAKE_PREFIX_PATH=${ANACONDA3_PREFIX}"
    "-DNETCDF_INCLUDE_DIR=${ANACONDA3_PREFIX}/include"
    "-DNETCDF_C_LIBRARY=${ANACONDA3_PREFIX}/lib/libnetcdf.so"
  )
fi

cmake "${CMAKE_ARGS[@]}" ..

make -j"$(nproc 2>/dev/null || echo 4)"

if [[ -f "${BUILD_DIR}/guess" ]]; then
  echo
  echo "Build successful: ${BUILD_DIR}/guess"
  ls -la "${BUILD_DIR}/guess"
  if [[ ${USE_MPI} -eq 1 ]]; then
    echo "Run with: mpirun -np N ${BUILD_DIR}/guess -parallel -input <module> <ins>"
    echo "MPI symbol check (libmpi.so.* should appear):"
    ldd "${BUILD_DIR}/guess" 2>/dev/null | grep -iE "libmpi|libopen-pal|libpmi" | head -5
  fi
else
  echo "ERROR: build failed; ${BUILD_DIR}/guess not produced"
  exit 1
fi
