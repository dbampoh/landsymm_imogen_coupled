#!/usr/bin/env bash
# =============================================================================
# fetch_imogen_data.sh — acquire and verify IMOGEN reference data
# =============================================================================
#
# This script downloads (or copies from a local source), verifies the SHA256
# checksum of, and extracts the GCM patterns and CRUNCEP base climatology
# tarballs into imogen/patterns/ and imogen/CRUNCEP_1960_1989/. These data
# are not committed to git (see .gitignore) so they must be acquired via
# this script before the IMOGEN binary will run.
#
# Sources are flexible. The data location is supplied via the IMOGEN_DATA_BASE
# environment variable (or the --base argument). It can be:
#
#   1. A local directory path containing the four tarballs (e.g. an
#      external-drive copy, a sibling working directory, or a cluster
#      shared filesystem). Use this for first-time staging from version_A.
#
#   2. An https:// or http:// URL prefix that the script will append
#      each tarball filename to (e.g. a Zenodo record, a GitHub Release
#      assets URL, or an institutional bucket).
#
#   3. (Future) A Zenodo DOI; not yet implemented but a hook for it is in
#      the resolve_url() function.
#
# The fetched file's SHA256 is verified against tools/imogen_data_manifest.txt
# before extraction, so corrupt or stale data is detected up-front.
#
# Usage examples:
#
#   # Stage from the local version_A copy on the workstation:
#   IMOGEN_DATA_BASE=/path/to/lpj-guess_imogen_landsymm_data tools/fetch_imogen_data.sh
#
#   # Or as a flag:
#   tools/fetch_imogen_data.sh --base /path/to/lpj-guess_imogen_landsymm_data
#
#   # Fetch only the default-IPSL pattern + CRUNCEP (smallest viable smoke test):
#   tools/fetch_imogen_data.sh --base ... --component patterns-cmip5 --component cruncep
#
#   # Fetch from a (TBD) public Zenodo / GitHub Releases URL prefix:
#   tools/fetch_imogen_data.sh --base https://example.com/imogen-data/v1.0
#
#   # List what's in the manifest without doing anything:
#   tools/fetch_imogen_data.sh --list
#
#   # Verify already-extracted data without re-downloading (re-checksums
#   # the original tarballs if they're still in --base; useful in CI):
#   tools/fetch_imogen_data.sh --base ... --verify-only
#
# Exit codes: 0 = success, 1 = checksum mismatch / extraction failure,
#             2 = manifest missing or malformed, 3 = $IMOGEN_DATA_BASE not set
#             and not provided via --base.
#
# Authored at step 4 of the unified-codebase rebuild — DKB 2026-05-05.
# =============================================================================

set -euo pipefail

# Resolve the repo root from this script's location (tools/fetch_imogen_data.sh)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$SCRIPT_DIR/imogen_data_manifest.txt"

# -------- Defaults & arg parsing --------
BASE="${IMOGEN_DATA_BASE:-}"
COMPONENTS=()
LIST_ONLY=0
VERIFY_ONLY=0

usage() {
  sed -n '/^# =============/,/^# =============================================================================/p' "$0" \
    | sed -e 's/^# \?//' -e 's/^=*$//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base|-b)        BASE="$2"; shift 2 ;;
    --component|-c)   COMPONENTS+=("$2"); shift 2 ;;
    --list|-l)        LIST_ONLY=1; shift ;;
    --verify-only|-V) VERIFY_ONLY=1; shift ;;
    --help|-h)        usage; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; echo "(try --help)" >&2; exit 1 ;;
  esac
done

# -------- Manifest read --------
if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: manifest not found at $MANIFEST" >&2
  exit 2
fi

declare -a MANIFEST_RECORDS=()
while IFS= read -r line; do
  # Skip blank lines and comments
  [[ -z "${line// /}" ]] && continue
  [[ "${line:0:1}" == "#" ]] && continue
  MANIFEST_RECORDS+=("$line")
done < "$MANIFEST"

if [[ ${#MANIFEST_RECORDS[@]} -eq 0 ]]; then
  echo "ERROR: manifest at $MANIFEST contains no records" >&2
  exit 2
fi

# -------- --list mode (just print and exit) --------
if [[ $LIST_ONLY -eq 1 ]]; then
  echo "Manifest: $MANIFEST"
  echo ""
  printf "%-25s %-50s %-12s %s\n" "COMPONENT" "FILENAME" "SIZE_BYTES" "SHA256 (truncated)"
  printf "%-25s %-50s %-12s %s\n" "---------" "--------" "----------" "-----------------"
  for rec in "${MANIFEST_RECORDS[@]}"; do
    read -r component filename sha256 size extract_to <<< "$rec"
    printf "%-25s %-50s %-12s %s...\n" "$component" "$filename" "$size" "${sha256:0:16}"
  done
  echo ""
  echo "Tip: pick components with --component <name> (multiple OK), or omit for all."
  exit 0
fi

# -------- Validate base --------
if [[ -z "$BASE" ]]; then
  echo "ERROR: data base location not specified." >&2
  echo "       Set IMOGEN_DATA_BASE or use --base <path-or-url>." >&2
  echo "       (try --help for usage)" >&2
  exit 3
fi

# -------- Helper: resolve full URL/path for a given filename --------
resolve_url() {
  local filename="$1"
  case "$BASE" in
    https://*|http://*) echo "${BASE%/}/${filename}" ;;
    file://*)           echo "${BASE#file://}/${filename}" ;;
    /*)                 echo "${BASE%/}/${filename}" ;;
    *)                  echo "${BASE%/}/${filename}" ;;
  esac
}

# -------- Helper: download or copy a tarball from BASE to a local path --------
fetch_one() {
  local src
  src="$(resolve_url "$1")"
  local dst="$2"
  case "$BASE" in
    https://*|http://*)
      if command -v curl >/dev/null 2>&1; then
        curl -L --fail --progress-bar -o "$dst" "$src"
      elif command -v wget >/dev/null 2>&1; then
        wget --show-progress -O "$dst" "$src"
      else
        echo "ERROR: neither curl nor wget available for HTTP fetch" >&2
        return 1
      fi
      ;;
    *)
      if [[ ! -f "$src" ]]; then
        echo "ERROR: source file not found: $src" >&2
        return 1
      fi
      cp -f "$src" "$dst"
      ;;
  esac
}

# -------- Main loop --------
TMPDIR_FETCH="${TMPDIR:-/tmp}/imogen_fetch.$$"
mkdir -p "$TMPDIR_FETCH"
trap 'rm -rf "$TMPDIR_FETCH"' EXIT

errors=0
processed=0

for rec in "${MANIFEST_RECORDS[@]}"; do
  read -r component filename sha256 size extract_to <<< "$rec"

  # If --component was used, filter
  if [[ ${#COMPONENTS[@]} -gt 0 ]]; then
    skip=1
    for c in "${COMPONENTS[@]}"; do
      [[ "$c" == "$component" ]] && skip=0 && break
    done
    [[ $skip -eq 1 ]] && continue
  fi

  echo "------------------------------------------------------------"
  echo "Component: $component   File: $filename"

  local_tarball="$TMPDIR_FETCH/$filename"

  if [[ $VERIFY_ONLY -eq 1 ]]; then
    # Verify-only: re-checksum the file at BASE without extracting.
    src="$(resolve_url "$filename")"
    case "$BASE" in
      https://*|http://*) echo "  --verify-only with HTTP base not supported"; ((errors++)); continue ;;
      *)
        if [[ ! -f "$src" ]]; then
          echo "  MISSING at $src"; errors=$((errors+1)); continue
        fi
        actual_sha=$(sha256sum "$src" | awk '{print $1}')
        actual_size=$(stat -c '%s' "$src")
        if [[ "$actual_sha" == "$sha256" && "$actual_size" -eq "$size" ]]; then
          echo "  OK    (size=$actual_size sha256=${actual_sha:0:16}...)"
        else
          echo "  FAIL  expected size=$size sha=${sha256:0:16}..."
          echo "        actual   size=$actual_size sha=${actual_sha:0:16}..."
          errors=$((errors+1))
        fi
        ;;
    esac
    processed=$((processed+1))
    continue
  fi

  echo "  Fetch  -> $local_tarball"
  fetch_one "$filename" "$local_tarball" || { errors=$((errors+1)); continue; }

  echo "  Verify -> sha256 + size"
  actual_sha=$(sha256sum "$local_tarball" | awk '{print $1}')
  actual_size=$(stat -c '%s' "$local_tarball")
  if [[ "$actual_sha" != "$sha256" || "$actual_size" -ne "$size" ]]; then
    echo "  FAIL  expected size=$size sha=${sha256:0:16}..."
    echo "        actual   size=$actual_size sha=${actual_sha:0:16}..."
    errors=$((errors+1))
    continue
  fi
  echo "  OK    (size=$actual_size sha256=${actual_sha:0:16}...)"

  echo "  Extract -> $REPO_ROOT/$extract_to"
  mkdir -p "$REPO_ROOT/$extract_to"
  tar -xzf "$local_tarball" -C "$REPO_ROOT/$extract_to"

  processed=$((processed+1))
done

echo "------------------------------------------------------------"
if [[ $errors -gt 0 ]]; then
  echo "FAILED: $errors error(s); $processed component(s) processed cleanly." >&2
  exit 1
fi
if [[ $processed -eq 0 ]]; then
  echo "No components matched. Check your --component selection (or run --list)." >&2
  exit 1
fi
echo "SUCCESS: processed $processed component(s) cleanly."
