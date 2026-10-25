"""Four bounded read-only local GETs; no proof, model, restart or token output."""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import html
import json
import re
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SNAPSHOT = ROOT / "output/hydra-implementation-2026-09-04/paired-size-study-02/website-interim-03/snapshot.json"
rows = []
started = time.monotonic()
for route in ("/", "/styles.css", "/api/status", "/api/showcase"):
    with urlopen(Request("http://127.0.0.1:8767" + route,
                         headers={"Cache-Control": "no-cache"}), timeout=5) as response:
        raw = response.read(524289)
        assert len(raw) <= 524288 and response.status == 200
        row = {"route": route, "status": response.status, "bytes": len(raw)}
    if route in ("/", "/styles.css"):
        local = ROOT / "hydra-playground" / ("index.html" if route == "/" else "styles.css")
        assert raw == local.read_bytes()
        row.update(matches_live_file=True, sha256=hashlib.sha256(raw).hexdigest())
    if route == "/":
        match = re.search(r'<pre id="study-evidence-json">(.*?)</pre>', raw.decode(), re.S)
        assert match and json.loads(html.unescape(match.group(1))) == json.loads(SNAPSHOT.read_bytes())
        row["matches_latest_dated_snapshot"] = True
    if route == "/api/status":
        data = json.loads(raw)
        row["computation_active"] = data.get("computation_active")
        modes = data.get("search_modes")
        row["available_mode_count"] = len(modes) if isinstance(modes, (dict, list)) else None
        row["csrf_values_redacted"] = True
    if route == "/api/showcase":
        data = json.loads(raw)
        cases = data if isinstance(data, list) else data.get("cases")
        row["gallery_records"] = len(cases) if isinstance(cases, list) else None
    rows.append(row)
result = {"schema": "hydra-bounded-read-only-http-verification-v1", "requests": rows,
          "elapsed_seconds": time.monotonic() - started, "model_or_native_requests": 0,
          "server_restart": False, "visual_browser_verification": False, "csrf_values_saved": False}
with (OUT / "result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps(result, sort_keys=True))
