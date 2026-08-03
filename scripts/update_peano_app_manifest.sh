#!/usr/bin/env bash
# Rebuild or check the content manifest for the immutable Peano browser app.
# Usage: scripts/update_peano_app_manifest.sh [--check]
set -euo pipefail

CHECK=false
if [[ ${1:-} == "--check" && $# -eq 1 ]]; then
  CHECK=true
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--check]" >&2
  exit 2
fi

cd "$(dirname "$0")/.."
APP=peano-lab
TMP_MANIFEST="$(mktemp)"
trap 'rm -f "$TMP_MANIFEST"' EXIT

python3 scripts/update_peano_worker_sources.py --check

(
  cd "$APP"
  {
    shasum -a 256 worker.js
    shasum -a 256 shadow-worker.js
    shasum -a 256 peano_kernel_shadow.wasm
    find py -type f -name '*.py' ! -path 'py/tests/*' \
      -exec shasum -a 256 {} +
  } | LC_ALL=C sort -k2
) > "$TMP_MANIFEST"

if $CHECK; then
  if [[ ! -f "$APP/APP_MANIFEST.sha256" ]] || \
      ! cmp -s "$TMP_MANIFEST" "$APP/APP_MANIFEST.sha256"; then
    echo "Peano application manifest is missing or stale; regenerate it with $0" >&2
    exit 1
  fi
else
  mv "$TMP_MANIFEST" "$APP/APP_MANIFEST.sha256"
  chmod 0644 "$APP/APP_MANIFEST.sha256"
fi

digest="$(shasum -a 256 "$APP/APP_MANIFEST.sha256" | cut -c1-12)"
printf 'Peano application release: a-%s\n' "$digest"
if ! $CHECK; then
  printf '%s\n' 'Update PEANOAPPID, APP_ROOT, and the human-facing BUILD before promotion.'
fi
