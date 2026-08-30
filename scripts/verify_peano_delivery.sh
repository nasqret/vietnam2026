#!/usr/bin/env bash
# Verify a deployed Peano Lab against the exact local staged assembly.
# Usage: scripts/verify_peano_delivery.sh BASE_URL [STAGED_TREE]
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 BASE_URL [STAGED_TREE]" >&2
  exit 2
fi

BASE="${1%/}"
STAGE="${2:-_deploy/peano-lab}"
if [[ ! "$BASE" =~ ^https?:// ]] || [[ ! -f "$STAGE/index.html" ]]; then
  echo "BASE_URL must be HTTP(S), and STAGED_TREE must contain index.html" >&2
  exit 2
fi

BUILD="$(sed -n 's/.*const BUILD="\([^"]*\)".*/\1/p' "$STAGE/index.html")"
APP="$(sed -n 's/.*const APP_ROOT="releases\/\([^/]*\)\/".*/\1/p' "$STAGE/index.html")"
APP_ROOT="$STAGE/releases/$APP"
VENDOR="$(sed -n 's/.*const VENDOR_ROOT = ".*vendor\/\([^/]*\)\/".*/\1/p' "$APP_ROOT/worker.js")"
if [[ ! "$APP" =~ ^a-[0-9a-f]{12}$ ]] || \
    [[ ! "$VENDOR" =~ ^v-[0-9a-f]{12}$ ]] || \
    [[ -z "$BUILD" ]] || [[ ! -f "$APP_ROOT/APP_MANIFEST.sha256" ]]; then
  echo "Could not derive BUILD/application/vendor identities from $STAGE" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -f "$TMP_DIR"/*
  rmdir "$TMP_DIR"
}
trap cleanup EXIT

curl() {
  command curl --connect-timeout 20 --max-time 180 "$@"
}

require_header() {
  local file="$1" pattern="$2" description="$3"
  if ! tr -d '\r' < "$file" | grep -Eiq "$pattern"; then
    echo "Missing $description in response headers:" >&2
    tr -d '\r' < "$file" >&2
    exit 1
  fi
}

reject_header() {
  local file="$1" pattern="$2" description="$3"
  if tr -d '\r' < "$file" | grep -Eiq "$pattern"; then
    echo "Unexpected $description in response headers:" >&2
    tr -d '\r' < "$file" >&2
    exit 1
  fi
}

# The release pointer is byte-identical to staging and cannot be stored.
curl -fsS -D "$TMP_DIR/root.headers" -o "$TMP_DIR/root.body" "$BASE/"
cmp -s "$TMP_DIR/root.body" "$STAGE/index.html" || {
  echo "Deployed index differs from the staged index" >&2
  exit 1
}
require_header "$TMP_DIR/root.headers" '^cache-control:.*no-store' 'non-storable HTML policy'
curl -fsS -D "$TMP_DIR/index.headers" -o /dev/null "$BASE/index.html"
require_header "$TMP_DIR/index.headers" '^cache-control:.*no-store' 'non-storable index.html policy'
INDEX_ETAG="$(tr -d '\r' < "$TMP_DIR/root.headers" |
  awk 'tolower($1) == "etag:" {sub(/^[^:]*:[[:space:]]*/, ""); print; exit}')"
if [[ -z "$INDEX_ETAG" ]]; then
  echo "Deployed index has no ETag for the 304 cache-policy probe" >&2
  exit 1
fi
STATUS="$(curl -sS -H "If-None-Match: $INDEX_ETAG" -D "$TMP_DIR/index304.headers" \
  -o /dev/null -w '%{http_code}' "$BASE/")"
if [[ "$STATUS" != 304 ]]; then
  echo "Conditional index probe returned HTTP $STATUS, expected 304" >&2
  exit 1
fi
require_header "$TMP_DIR/index304.headers" '^cache-control:.*no-store' '304 HTML cache policy'

# The remote manifest and every application byte must match the immutable ID.
curl -fsS -D "$TMP_DIR/app.headers" \
  -o "$TMP_DIR/remote-app-manifest" "$BASE/releases/$APP/APP_MANIFEST.sha256"
cmp -s "$TMP_DIR/remote-app-manifest" "$APP_ROOT/APP_MANIFEST.sha256" || {
  echo "Remote application manifest differs from staging" >&2
  exit 1
}
require_header "$TMP_DIR/app.headers" '^cache-control:.*max-age=31536000.*immutable' \
  'immutable application cache policy'
APP_ETAG="$(tr -d '\r' < "$TMP_DIR/app.headers" |
  awk 'tolower($1) == "etag:" {sub(/^[^:]*:[[:space:]]*/, ""); print; exit}')"
if [[ -z "$APP_ETAG" ]]; then
  echo "Deployed application manifest has no ETag for the 304 cache-policy probe" >&2
  exit 1
fi
STATUS="$(curl -sS -H "If-None-Match: $APP_ETAG" -D "$TMP_DIR/app304.headers" \
  -o /dev/null -w '%{http_code}' "$BASE/releases/$APP/APP_MANIFEST.sha256")"
if [[ "$STATUS" != 304 ]]; then
  echo "Conditional application probe returned HTTP $STATUS, expected 304" >&2
  exit 1
fi
require_header "$TMP_DIR/app304.headers" '^cache-control:.*max-age=31536000.*immutable' \
  'immutable 304 application cache policy'

APP_PIDS=()
APP_EXPECTED=()
APP_PATHS=()
app_index=0
while read -r expected relative_path; do
  curl -fsS --compressed "$BASE/releases/$APP/$relative_path" \
    -o "$TMP_DIR/app-$app_index" &
  APP_PIDS+=("$!")
  APP_EXPECTED+=("$expected")
  APP_PATHS+=("$relative_path")
  app_index=$((app_index + 1))
done < "$APP_ROOT/APP_MANIFEST.sha256"

app_fetch_failed=false
for app_index in "${!APP_PIDS[@]}"; do
  if ! wait "${APP_PIDS[$app_index]}"; then
    echo "Could not fetch remote application file: ${APP_PATHS[$app_index]}" >&2
    app_fetch_failed=true
  fi
done
if $app_fetch_failed; then
  exit 1
fi
for app_index in "${!APP_PATHS[@]}"; do
  actual="$(shasum -a 256 "$TMP_DIR/app-$app_index" | awk '{print $1}')"
  if [[ "$actual" != "${APP_EXPECTED[$app_index]}" ]]; then
    echo "Remote application hash mismatch: ${APP_PATHS[$app_index]}" >&2
    exit 1
  fi
done

for relative_path in worker.js py/peano_lab/kernel/checker.py; do
  curl -fsS -H 'Accept-Encoding: br, gzip' -D "$TMP_DIR/source.headers" \
    -o /dev/null "$BASE/releases/$APP/$relative_path"
  require_header "$TMP_DIR/source.headers" '^content-encoding:[[:space:]]*(br|gzip)' \
    "compression for $relative_path"
  require_header "$TMP_DIR/source.headers" '^vary:.*accept-encoding' \
    "content negotiation Vary for $relative_path"
  require_header "$TMP_DIR/source.headers" '^cache-control:.*max-age=31536000.*immutable' \
    "immutable cache policy for $relative_path"
done

# Measure encoded WASM, then download/decode it and compare the pinned hash.
WASM_PATH="vendor/$VENDOR/pyodide/pyodide.asm.wasm"
WASM_URL="$BASE/$WASM_PATH"
EXPECTED_WASM="$(awk -v path="./$VENDOR/pyodide/pyodide.asm.wasm" \
  '$2 == path {print $1}' "$STAGE/vendor/MANIFEST.sha256")"
if [[ -z "$EXPECTED_WASM" ]]; then
  echo "Staged vendor manifest has no WASM entry" >&2
  exit 1
fi

ENCODED_SIZE="$(curl -fsS -H 'Accept-Encoding: br, gzip' \
  -D "$TMP_DIR/wasm.headers" -o "$TMP_DIR/wasm.encoded" \
  -w '%{size_download}' "$WASM_URL")"
require_header "$TMP_DIR/wasm.headers" '^content-type:.*application/wasm' 'WASM media type'
require_header "$TMP_DIR/wasm.headers" '^content-encoding:[[:space:]]*(br|gzip)' 'WASM compression'
require_header "$TMP_DIR/wasm.headers" '^vary:.*accept-encoding' 'WASM negotiation Vary'
require_header "$TMP_DIR/wasm.headers" '^cache-control:.*max-age=31536000.*immutable' \
  'immutable WASM cache policy'
if ! awk -v size="$ENCODED_SIZE" 'BEGIN { exit !(size > 0 && size < 3000000) }'; then
  echo "Encoded WASM transfer is not below 3,000,000 bytes: $ENCODED_SIZE" >&2
  exit 1
fi

curl -fsS --compressed -H 'Accept-Encoding: br, gzip' "$WASM_URL" -o "$TMP_DIR/wasm.decoded"
ACTUAL_WASM="$(shasum -a 256 "$TMP_DIR/wasm.decoded" | awk '{print $1}')"
if [[ "$ACTUAL_WASM" != "$EXPECTED_WASM" ]]; then
  echo "Decoded WASM differs from the pinned local bytes" >&2
  exit 1
fi

curl -fsS -H 'Accept-Encoding: gzip' -D "$TMP_DIR/gzip.headers" -o /dev/null "$WASM_URL"
require_header "$TMP_DIR/gzip.headers" '^content-encoding:[[:space:]]*gzip' 'gzip fallback'
curl -fsS -H 'Accept-Encoding: br;q=0, gzip' -D "$TMP_DIR/qzero.headers" -o /dev/null "$WASM_URL"
require_header "$TMP_DIR/qzero.headers" '^content-encoding:[[:space:]]*gzip' 'q=0-aware gzip fallback'
curl -fsS -H 'Accept-Encoding: identity' -D "$TMP_DIR/identity.headers" -o /dev/null "$WASM_URL"
reject_header "$TMP_DIR/identity.headers" '^content-encoding:' 'identity-response content encoding'
STATUS="$(curl -sS -H 'Accept-Encoding: identity' -H 'Range: bytes=0-0' \
  -D "$TMP_DIR/range.headers" -o "$TMP_DIR/range.body" -w '%{http_code}' "$WASM_URL")"
if [[ "$STATUS" != 206 ]] || [[ "$(wc -c < "$TMP_DIR/range.body" | tr -d ' ')" != 1 ]]; then
  echo "WASM range probe did not return one byte with HTTP 206" >&2
  exit 1
fi
require_header "$TMP_DIR/range.headers" '^cache-control:.*max-age=31536000.*immutable' \
  'immutable 206 vendor cache policy'

for relative_path in \
  "vendor/$VENDOR/pyodide/python_stdlib.zip" \
  "vendor/$VENDOR/fonts/Inter-400.woff2"; do
  curl -fsS -H 'Accept-Encoding: br, gzip' -D "$TMP_DIR/binary.headers" \
    -o /dev/null "$BASE/$relative_path"
  reject_header "$TMP_DIR/binary.headers" '^content-encoding:' "compression for $relative_path"
  require_header "$TMP_DIR/binary.headers" '^cache-control:.*max-age=31536000.*immutable' \
    "immutable cache policy for $relative_path"
done

STATUS="$(curl -sS -D "$TMP_DIR/missing.headers" -o /dev/null -w '%{http_code}' \
  "$BASE/definitely-missing-m14-probe")"
if [[ "$STATUS" != 404 ]]; then
  echo "Missing-resource probe returned HTTP $STATUS, expected 404" >&2
  exit 1
fi
require_header "$TMP_DIR/missing.headers" '^cache-control:.*no-store' 'non-storable error policy'

printf 'Verified %s: build=%s app=%s vendor=%s encoded_wasm=%s bytes\n' \
  "$BASE" "$BUILD" "$APP" "$VENDOR" "$ENCODED_SIZE"
