#!/usr/bin/env bash
# Fetch the pinned third-party assets the Lambda Lab needs, for self-hosting.
# Everything is version-pinned; run from the repo root:  bash scripts/fetch_vendor.sh
# Output: lab-lambda/vendor/{pyodide,xterm,fonts}/  (~13 MB, gitignored — deploy artifact, not source)
set -euo pipefail
cd "$(dirname "$0")/.."
V=lab-lambda/vendor
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
curl -fsSL --retry 3 -A "$UA" "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" -o /tmp/gf.css
# keep only the latin blocks, extract font-family/weight/url triples, download each
python3 - "$V/fonts" /tmp/gf.css <<'PY'
import sys, re, urllib.request, pathlib
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
    urllib.request.urlretrieve(url, outdir/name)
    rules.append(
        "@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;"
        "src:url('%s') format('woff2');unicode-range:%s;}" % (fam, wt, name, ur))
    print(f"  {name}")
(outdir/"fonts.css").write_text("\n".join(rules) + "\n", encoding="utf-8")
print(f"  fonts.css ({len(rules)} faces)")
PY

echo "→ manifest (sha256)"
( cd "$V" && find . -type f ! -name MANIFEST.sha256 -exec shasum -a 256 {} + | sort -k2 > MANIFEST.sha256 )
echo "→ total: $(du -sh "$V" | cut -f1)"
