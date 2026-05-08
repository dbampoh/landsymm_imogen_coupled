#!/bin/bash
# =============================================================================
# scripts/cluster/append_files.sh — concatenate per-rank LPJ-GUESS .out files
# =============================================================================
#
# Adapted (verbatim) from: /home/bampoh-d/Desktop/landsymm_lpjg/landsymm_mat/
#                          owl_hpc_cluster_scripts/scripts/append_files.sh
# (already cluster-agnostic; pure bash + awk).
#
# What it does:
#   For each .out file in run1/, copy it to the work dir then append the
#   matching .out from run2/ ... runN/ (skipping the header line on each
#   subsequent rank's contribution).
#
# USAGE
# -----
#     append_files.sh <number_of_jobs> <file1> [<file2> ... <fileN>]
#
# Typically invoked via xargs from finishup_lpj_work.sh:
#     find run1 -name '*.out' | sed 's,run1/,,g' \
#       | xargs -n <NPROC> -P <NPROC> append_files.sh <number_of_jobs>
#
# AWK FILTER NOTES
# ----------------
# `awk 'NR!=1 || NF==0 || $1 == $1+0 { print $0 }'`:
# - NR!=1: skip the file's header line on rank-2+ contributions
# - NF==0: but keep blank lines (some LPJG outputs have section breaks)
# - $1 == $1+0: but also keep lines whose first field is numeric (defensive
#   against corner cases where the header detection misfires)
# =============================================================================

echo "$# $0 $1 $2 $3 $4 $5 $6 $7 $8"
number_of_jobs=$1
shift

while [[ $# -gt 0 ]]; do
  file=$1
  echo "${file}"
  if [[ -e "run1/${file}" ]]; then
    cp "run1/${file}" "${file}"
    for ((i=2; i <= number_of_jobs; i++)); do
      cat "run${i}/${file}" 2>/dev/null \
        | awk 'NR!=1 || NF==0 || $1 == $1+0 { print $0 }' \
        >> "${file}"
    done
  fi
  shift
done
