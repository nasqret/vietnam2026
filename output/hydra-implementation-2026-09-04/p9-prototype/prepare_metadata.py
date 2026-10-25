"""Bounded official metadata only; no solver, package import or build."""
from pathlib import Path
import hashlib
import json
import signal
import urllib.request


HERE = Path(__file__).resolve().parent


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Hydra-local-pinned-build/1"})
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.geturl() != url:
            raise ValueError("Unexpected metadata redirect.")
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("Official metadata exceeded one MiB.")
    return json.loads(raw), {"url": url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    signal.alarm(45)
    destination = HERE / "dependency-metadata.json"
    if destination.exists():
        raise ValueError("Preserving existing metadata.")
    crates = []
    for name, version in (("egg", "0.11.0"), ("serde_json", "1.0.145"), ("sha2", "0.10.9")):
        data, source = fetch(f"https://crates.io/api/v1/crates/{name}/{version}")
        record = data["version"]
        if record["crate"] != name or record["num"] != version or record["yanked"]:
            raise ValueError("Pinned crate metadata does not match.")
        crates.append({"name": name, "version": version, "sha256": record["checksum"],
                       "bytes": record["crate_size"], "metadata": source,
                       "url": f"https://static.crates.io/crates/{name}/{name}-{version}.crate"})
    data, source = fetch("https://api.github.com/repos/eprover/eprover/git/ref/tags/E-3.3.6")
    if data["object"]["type"] != "commit":
        raise ValueError("Expected the official E tag to point directly to a commit.")
    commit = data["object"]["sha"]
    result = {"schema": "hydra-p9-dependency-metadata-v1", "status": "metadata-only",
              "platform": "darwin-arm64", "network_limit_bytes": 4 * 1024**2,
              "crates": crates, "e": {"tag": "E-3.3.6", "commit": commit,
              "metadata": source, "url": f"https://codeload.github.com/eprover/eprover/tar.gz/{commit}"},
              "solver_executions": 0, "backend_imports": 0}
    with destination.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
