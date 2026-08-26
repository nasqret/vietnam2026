#!/usr/bin/env bash
# Fetch the pinned third-party assets both browser labs need, for self-hosting.
# Everything is version-pinned; run from the repo root:  bash scripts/fetch_vendor.sh
# Output: a conventional Lambda mirror and a version-namespaced Peano mirror.
# (~13 MB each, gitignored — deploy artifacts, not source)
set -euo pipefail
cd "$(dirname "$0")/.."
V=lab-lambda/vendor
PEANO_V=peano-lab/vendor
PEANO_VENDOR_ID=v-85fb3352e49c
mkdir -p "$V/pyodide" "$V/xterm" "$V/fonts"

PYODIDE=0.28.3
XTERM=5.5.0
FIT=0.10.0
WEBLINKS=0.11.0
UNICODE11=0.8.0

say() { printf '  %s\n' "$*"; }

echo "→ Pyodide $PYODIDE core (5 files)"
for f in pyodide.js pyodide.asm.js pyodide.asm.wasm python_stdlib.zip pyodide-lock.json; do
  curl -fsSL --retry 3 "https://cdn.jsdelivr.net/pyodide/v$PYODIDE/full/$f" -o "$V/pyodide/$f"
  say "$f  $(wc -c < "$V/pyodide/$f" | tr -d ' ') bytes"
done

echo "→ xterm $XTERM + addons"
curl -fsSL --retry 3 "https://cdn.jsdelivr.net/npm/@xterm/xterm@$XTERM/lib/xterm.js"   -o "$V/xterm/xterm.js"
curl -fsSL --retry 3 "https://cdn.jsdelivr.net/npm/@xterm/xterm@$XTERM/css/xterm.css"  -o "$V/xterm/xterm.css"
curl -fsSL --retry 3 "https://cdn.jsdelivr.net/npm/@xterm/addon-fit@$FIT/lib/addon-fit.js" -o "$V/xterm/addon-fit.js"
curl -fsSL --retry 3 "https://cdn.jsdelivr.net/npm/@xterm/addon-web-links@$WEBLINKS/lib/addon-web-links.js" -o "$V/xterm/addon-web-links.js"
curl -fsSL --retry 3 "https://cdn.jsdelivr.net/npm/@xterm/addon-unicode11@$UNICODE11/lib/addon-unicode11.js" -o "$V/xterm/addon-unicode11.js"
say "$(ls "$V/xterm" | tr '\n' ' ')"

echo "→ Fonts (Inter 400/600/700/800, JetBrains Mono 400/500/600 — latin woff2)"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
GF_CSS="$(mktemp)"
trap 'rm -f "$GF_CSS"' EXIT
curl -fsSL --retry 3 -A "$UA" "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" -o "$GF_CSS"
# keep only the latin blocks, extract font-family/weight/url triples, download each
python3 - "$V/fonts" "$GF_CSS" <<'PY'
import pathlib
import re
import subprocess
import sys

outdir = pathlib.Path(sys.argv[1])
css = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
blocks = re.findall(r'/\*\s*latin\s*\*/\s*@font-face\s*\{(.*?)\}', css, re.S)
rules = []
for b in blocks:
    fam = re.search(r"font-family:\s*'([^']+)'", b).group(1)
    wt  = re.search(r"font-weight:\s*(\d+)", b).group(1)
    url = re.search(r"url\((https://[^)]+\.woff2)\)", b).group(1)
    ur  = re.search(r"unicode-range:\s*([^;]+);", b).group(1)
    name = f"{fam.replace(' ','')}-{wt}.woff2"
    # Use the same system curl (and therefore the same OS trust store) as the
    # rest of this script.  Framework Python installations on macOS may not
    # have a populated urllib CA bundle even though curl is correctly set up.
    subprocess.run(
        ["curl", "-fsSL", "--retry", "3", url, "-o", str(outdir / name)],
        check=True,
    )
    rules.append(
        "@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;"
        "src:url('%s') format('woff2');unicode-range:%s;}" % (fam, wt, name, ur))
    print(f"  {name}")
(outdir/"fonts.css").write_text("\n".join(rules) + "\n", encoding="utf-8")
print(f"  fonts.css ({len(rules)} faces)")
PY

echo "→ manifest (sha256)"
( cd "$V" && find . -type f ! -name MANIFEST.sha256 -exec shasum -a 256 {} + | LC_ALL=C sort -k2 > MANIFEST.sha256 )
VENDOR_DIGEST="$(shasum -a 256 "$V/MANIFEST.sha256" | awk '{print substr($1, 1, 12)}')"
if [[ "v-$VENDOR_DIGEST" != "$PEANO_VENDOR_ID" ]]; then
  echo "Peano vendor content changed: expected $PEANO_VENDOR_ID, got v-$VENDOR_DIGEST" >&2
  echo "Bump PEANO_VENDOR_ID and the browser URLs deliberately." >&2
  exit 1
fi

echo "→ Peano Lab immutable mirror ($PEANO_VENDOR_ID)"
mkdir -p "$PEANO_V/$PEANO_VENDOR_ID"
rsync -a --delete --exclude MANIFEST.sha256 "$V/" "$PEANO_V/$PEANO_VENDOR_ID/"
( cd "$PEANO_V" && find . -type f ! -name MANIFEST.sha256 -exec shasum -a 256 {} + | LC_ALL=C sort -k2 > MANIFEST.sha256 )
echo "→ total per lab: $(du -sh "$V" | cut -f1)"
