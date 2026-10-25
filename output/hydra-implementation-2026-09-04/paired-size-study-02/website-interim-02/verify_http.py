"""Four bounded, read-only GETs; never start a proof/model or save CSRF values."""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import html
import json
import re
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
rows = []
started = time.monotonic()
for route in ("/", "/styles.css", "/api/status", "/api/showcase"):
    request = Request("http://127.0.0.1:8767" + route,
                      headers={"Cache-Control": "no-cache"})
    with urlopen(request, timeout=5) as response:
        raw = response.read(524289)
        assert len(raw) <= 524288 and response.status == 200
        row = {"route": route, "status": response.status, "bytes": len(raw),
               "content_type": response.headers.get("Content-Type"),
               "cache_control": response.headers.get("Cache-Control")}
    if route in ("/", "/styles.css"):
        local = ROOT / "hydra-playground" / ("index.html" if route == "/" else "styles.css")
        assert raw == local.read_bytes()
        row.update(matches_live_file=True, sha256=hashlib.sha256(raw).hexdigest())
    if route == "/":
        page = raw.decode()
        match = re.search(r'<pre id="study-evidence-json">(.*?)</pre>', page, re.S)
        assert match
        observed = json.loads(html.unescape(match.group(1)))
        assert observed == json.loads((OUT / "snapshot.json").read_text())
        assert "Stopped before inference" in page and "Not evaluated" in page
        assert "Running when recorded" not in page
        row["embedded_snapshot_matches"] = True
    if route == "/api/status":
        data = json.loads(raw)
        row["computation_active"] = data.get("computation_active")
        modes = data.get("available_modes", data.get("modes"))
        row["available_mode_count"] = len(modes) if isinstance(modes, (dict, list)) else None
        row["csrf_redacted"] = True
        row["safe_top_level_keys"] = [k for k in data
                                     if not any(t in k.lower() for t in ("token", "secret", "csrf"))]
    if route == "/api/showcase":
        data = json.loads(raw)
        if isinstance(data, list):
            row["gallery_records"] = len(data)
        else:
            counts = {k: len(v) for k, v in data.items() if isinstance(v, list)}
            row["list_counts"] = counts
            row["gallery_records"] = counts.get("cases")
    rows.append(row)
result = {"schema": "hydra-bounded-read-only-http-verification-v1",
          "elapsed_seconds": time.monotonic() - started, "requests": rows,
          "model_or_native_requests": 0, "server_restart": False,
          "visual_browser_verification": False, "csrf_values_saved": False,
          "prior_sandbox_attempt": {"actual_exit_code": 1, "completion_chunk": "8610eb",
                                    "error": "loopback socket denied before first GET"}}
with (OUT / "http-verification.json").open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(result, indent=2))
