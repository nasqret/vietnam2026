"""One bounded GET of the existing local website; no proof/model request."""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import html
import json
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
request = Request("http://127.0.0.1:8767/", headers={"Cache-Control": "no-cache"})
with urlopen(request, timeout=5) as response:
    raw = response.read(65537)
    assert response.status == 200 and len(raw) <= 65536
    assert raw == (ROOT / "hydra-playground/index.html").read_bytes()
    page = raw.decode()
    match = re.search(r'<pre id="study-evidence-json">(.*?)</pre>', page, re.S)
    assert match
    assert json.loads(html.unescape(match.group(1))) == json.loads((OUT / "snapshot.json").read_text())
    result = {"schema": "hydra-served-snapshot-verification-v1",
              "http_status": response.status, "bytes": len(raw),
              "sha256": hashlib.sha256(raw).hexdigest(),
              "cache_control": response.headers.get("Cache-Control"),
              "matches_live_file": True, "embedded_snapshot_matches": True,
              "http_requests": 1, "model_or_native_requests": 0,
              "server_restarted": False,
              "visual_browser_verification": False,
              "browser_limitation": "Browser skill bootstrap succeeded, but discovery returned no connected browsers."}
with (OUT / "http-verification.json").open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(result, indent=2))
