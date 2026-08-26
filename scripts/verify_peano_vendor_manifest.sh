#!/usr/bin/env bash
# Verify that the Peano vendor inventory is exact and its current namespace is
# the canonical C-locale digest of the pinned source-vendor manifest.
set -euo pipefail

cd "$(dirname "$0")/.."
VENDOR=peano-lab/vendor
MANIFEST="$VENDOR/MANIFEST.sha256"
TMP_AGGREGATE="$(mktemp)"
TMP_CURRENT="$(mktemp)"
trap 'rm -f "$TMP_AGGREGATE" "$TMP_CURRENT"' EXIT

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing $MANIFEST; run: bash scripts/fetch_vendor.sh" >&2
  exit 1
fi

(
  cd "$VENDOR"
  find . -type f ! -name MANIFEST.sha256 -exec shasum -a 256 {} + |
    LC_ALL=C sort -k2
) > "$TMP_AGGREGATE"
if ! cmp -s "$TMP_AGGREGATE" "$MANIFEST"; then
  echo "Peano vendor inventory is missing, stale, or contains unmanifested files" >&2
  exit 1
fi

PEANO_VENDOR_ID="$(sed -n 's/^PEANO_VENDOR_ID=//p' scripts/fetch_vendor.sh)"
if [[ ! "$PEANO_VENDOR_ID" =~ ^v-[0-9a-f]{12}$ ]] || \
    [[ ! -d "$VENDOR/$PEANO_VENDOR_ID" ]]; then
  echo "Current Peano vendor namespace is invalid or missing: $PEANO_VENDOR_ID" >&2
  exit 1
fi

(
  cd "$VENDOR/$PEANO_VENDOR_ID"
  find . -type f ! -name MANIFEST.sha256 -exec shasum -a 256 {} + |
    LC_ALL=C sort -k2
) > "$TMP_CURRENT"
CURRENT_DIGEST="$(shasum -a 256 "$TMP_CURRENT" | cut -c1-12)"
if [[ "$PEANO_VENDOR_ID" != "v-$CURRENT_DIGEST" ]]; then
  echo "Vendor namespace $PEANO_VENDOR_ID does not match v-$CURRENT_DIGEST" >&2
  exit 1
fi

(cd "$VENDOR" && shasum -a 256 -c MANIFEST.sha256 >/dev/null)
printf 'Peano vendor manifest verified: %s\n' "$PEANO_VENDOR_ID"
