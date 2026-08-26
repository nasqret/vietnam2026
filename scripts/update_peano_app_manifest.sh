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
BUNDLE_DIR=research/arithmetic-library/artifacts
PROOF_BUNDLES=(
  quadratic-reciprocity-proof-bundle-v1.json
  supplementary-laws-proof-bundle-v1.json
  lucas-proof-bundle-v1.json
  kummer-proof-bundle-v1.json
  bertrand-proof-bundle-v1.json
  four-square-proof-bundle-v1.json
  two-square-proof-bundle-v1.json
  alpha-v19-residual-proof-bundle-v1.json
  alpha-v19-campaign-frontier-proof-bundle-v1.json
  alpha-v20-next-layer-proof-bundle-v1.json
  alpha-v21-advanced-layer-proof-bundle-v1.json
  alpha-v22-transport-layer-proof-bundle-v1.json
  alpha-v23-milestone-closure-proof-bundle-v1.json
  alpha-v24-research-layer-proof-bundle-v1.json
  alpha-v25-breakthrough-layer-proof-bundle-v1.json
)
TMP_MANIFEST="$(mktemp)"
trap 'rm -f "$TMP_MANIFEST"' EXIT

python3 scripts/update_peano_worker_sources.py --check
for bundle_name in "${PROOF_BUNDLES[@]}"; do
  if [[ ! -f "$BUNDLE_DIR/$bundle_name" ]]; then
    echo "Missing independently checked proof bundle: $BUNDLE_DIR/$bundle_name" >&2
    exit 1
  fi
done

(
  cd "$APP"
  {
    shasum -a 256 worker.js
    find py -type f -name '*.py' ! -path 'py/tests/*' \
      -exec shasum -a 256 {} +
    for bundle_name in "${PROOF_BUNDLES[@]}"; do
      shasum -a 256 "../$BUNDLE_DIR/$bundle_name" |
        awk -v target="proof-artifacts/$bundle_name" '{print $1 "  " target}'
    done
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
