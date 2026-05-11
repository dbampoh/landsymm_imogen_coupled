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

  # ---------------------------------------------------------------------------
  # [Step 17b (F-12 sub-milestone C2 prep; 2026-05-11) — mpicxx-wrapper fix]
  #
  # Anaconda3's mpicxx wrapper (MPICH 4.1.1) is configured to invoke
  # `x86_64-conda-linux-gnu-c++` (the conda-shipped g++ wrapper). If that
  # binary isn't present in the conda env (the common case on the workstation
  # per session-2 §8.1 workstation-specs 2026-05-09), `mpicxx --version`
  # fails with `x86_64-conda-linux-gnu-c++: command not found` and no
  # build is possible.
  #
  # Two fixes investigated 2026-05-11 (see notes/STEP_17b.md §3 + session-2
  # handoff Part 16):
  #   (a) `MPICH_CXX=g++` env var override -- MPICH's documented mechanism
  #       to bypass the conda-wrapper-compiler lookup; uses system g++
  #       instead. NOT CHOSEN. Diagnostic empirical test 2026-05-11
  #       revealed the override hits an independent libstdc++ ABI issue:
  #       Anaconda3 ships libstdc++.so.6.0.29 (GCC 11.2 era; June 2022)
  #       which does NOT export __cxa_call_terminate. System g++ 15.2
  #       emits calls to __cxa_call_terminate in Catch2 destructors. The
  #       mpicxx wrapper command bakes -L/home/.../anaconda3/lib +
  #       -Wl,-rpath,/home/.../anaconda3/lib into the link line, so the
  #       linker finds Anaconda3's older libstdc++ first -> undefined
  #       reference at link time. Side-fix via rpath/-L surgery risks
  #       runtime libstdc++ resolution breakage.
  #   (b) `conda install -c conda-forge gxx_linux-64` -- provides the
  #       missing conda-shipped wrapper g++ AT the path mpicxx expects.
  #       The conda gxx_linux-64 package also ships a matching libstdc++
  #       (typically GCC 11.x+) which DOES export __cxa_call_terminate.
  #       Internal toolchain consistency: conda g++ + conda libstdc++ +
  #       conda libmpi + conda libnetcdf all from same vendor environment.
  #       CHOSEN. Per session-2 §8.1 "preferred" recommendation.
  #
  # NOTE: the inherited handoff Part 8.1 + the C2 prompt suggested
  # `OMPI_CXX=g++` -- that's OpenMPI's variant; Anaconda3 ships MPICH,
  # whose wrapper expects `MPICH_CXX`. Verified live 2026-05-11.
  #
  # For C2 xval testing: use build_mpi/guess for BOTH Run A (gridcell_outer)
  # AND Run B (year_outer) -- bit-exactness comparison stays compiler-internal-
  # consistent. The existing build/guess (system g++ 15.2.0) remains
  # available independently for non-MPI scenarios.
  # ---------------------------------------------------------------------------
  if ! mpicxx --version &>/dev/null; then
    echo "ERROR: Anaconda3 mpicxx wrapper failed compiler probe"
    echo "       (x86_64-conda-linux-gnu-c++ not found). Two fixes:"
    echo
    echo "       Preferred (per session-2 §8.1 + STEP_17b.md):"
    echo "           conda install -c conda-forge gxx_linux-64"
    echo
    echo "       Alternative (env-var override; see STEP_17b.md §3 caveat"
    echo "       about libstdc++ ABI mismatch):"
    echo "           MPICH_CXX=g++ scripts/cluster/make_guess.sh --mpi"
    exit 1
  fi

  CMAKE_ARGS+=(-DCMAKE_CXX_COMPILER=mpicxx)
fi

# NetCDF preference (Anaconda3 on workstation; module-loaded on cluster)
ANACONDA3_PREFIX="${ANACONDA3_PREFIX:-${CONDA_PREFIX:-}}"
if [[ -z "${ANACONDA3_PREFIX}" && -d "/home/${USER}/anaconda3" ]]; then
  ANACONDA3_PREFIX="/home/${USER}/anaconda3"
fi

# ---------------------------------------------------------------------------
# [Step 17b (F-12 sub-milestone C2 prep; 2026-05-11) — Anaconda3 NetCDF for
# workstation MPI build TOO]
#
# Previously the `&& ${USE_MPI} -eq 0` clause skipped Anaconda3 NetCDF for
# --mpi builds. The comment rationale was "cluster + MPI prefers
# module-loaded NetCDF; mixing Anaconda3 NetCDF with cluster MPI causes
# ABI issues". That logic is correct for cluster but WRONG for workstation:
# on workstation there's NO module-loaded NetCDF and Ubuntu native NetCDF
# is the broken libhdf5_serial.so.310 + libcurl@CURL_OPENSSL_4 ABI mismatch
# that Decision #8 specifically AVOIDS via the Anaconda3 NetCDF preference.
#
# Empirical evidence (2026-05-11): with --mpi skipping Anaconda3 NetCDF,
# the MPI workstation build fails at link time with:
#   undefined reference to `curl_global_init@CURL_OPENSSL_4`
#   undefined reference to `curl_easy_perform@CURL_OPENSSL_4`
#   ...
# (the canonical Decision #8 failure mode). On workstation Anaconda3
# already provides matching libmpi.so + libnetcdf.so + libhdf5.so +
# libcurl.so — same vendor environment, no ABI mismatch within Anaconda3.
#
# Fix: apply Anaconda3 NetCDF unconditionally when ANACONDA3_PREFIX is set;
# cluster builds with module-loaded NetCDF should NOT set
# ANACONDA3_PREFIX (env_owl.sh module loads will populate cluster-native
# NETCDF paths and leave ANACONDA3_PREFIX unset).
# ---------------------------------------------------------------------------
if [[ -n "${ANACONDA3_PREFIX:-}" ]]; then
  if [[ ${USE_MPI} -eq 1 ]]; then
    echo "Using Anaconda3 NetCDF for --mpi (workstation; consistent with"
    echo "non-MPI build/guess; cluster MPI builds skip this via unset"
    echo "ANACONDA3_PREFIX): ${ANACONDA3_PREFIX}"
  else
    echo "Using Anaconda3 NetCDF: ${ANACONDA3_PREFIX}"
  fi
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
