"""Fetch only bounded primary package metadata; never import or launch a backend."""
from pathlib import Path
import hashlib
import json
import signal
import urllib.request


def main():
    signal.alarm(40)
    destination = Path(__file__).resolve().parent / "dependency-metadata.json"
    if destination.exists():
        raise SystemExit("Preserving an existing metadata record.")
    records = []
    for name, version in (("sympy", "1.14.0"), ("mpmath", "1.3.0"), ("cvc5", None)):
        url = f"https://pypi.org/pypi/{name}/" + (f"{version}/" if version else "") + "json"
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.geturl() != url:
                raise ValueError("Unexpected package metadata redirect.")
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("Package metadata exceeded 2 MiB.")
        data = json.loads(raw)
        selected = []
        for item in data["urls"]:
            filename = item["filename"]
            wanted = (filename.endswith("-py3-none-any.whl") or filename.endswith("-py2.py3-none-any.whl"))
            if name == "cvc5":
                wanted = "cp311-cp311-macosx" in filename and filename.endswith("_arm64.whl")
            if wanted:
                selected.append({"filename": filename, "bytes": item["size"],
                    "sha256": item["digests"]["sha256"], "url": item["url"],
                    "requires_python": item["requires_python"]})
        if len(selected) != 1:
            raise ValueError(f"Expected one exact compatible wheel for {name}.")
        records.append({"name": name, "version": data["info"]["version"], "source": url,
            "metadata_sha256": hashlib.sha256(raw).hexdigest(), "metadata_bytes": len(raw),
            "requires_python": data["info"]["requires_python"],
            "requires_dist": data["info"]["requires_dist"], "wheel": selected[0]})
    result = {"schema": "hydra-p8-dependency-metadata-v1", "platform": "macOS arm64",
        "python_abi": "cp311", "network_read_only": True, "backend_imports_or_launches": 0,
        "packages": records}
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
