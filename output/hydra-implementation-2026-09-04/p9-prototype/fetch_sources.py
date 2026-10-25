"""Fetch and inspect fixed public source archives; never run their code."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import resource
import signal
import tarfile
import time
import urllib.request


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "source-download-01"
MAX_NETWORK = 32 * 1024**2
MAX_EXPANDED = 256 * 1024**2
MAX_FILES = 16000
FIXED = (
    ("egg-0.11.0", "https://static.crates.io/crates/egg/egg-0.11.0.crate", "dd40cfd4196d7a8f882ace95d623d4d6734588e502b4e188675a7c2f55eb4fb4", 122598),
    ("serde_json-1.0.145", "https://static.crates.io/crates/serde_json/serde_json-1.0.145.crate", "402a6f66d8c709116cf22f558eab210f5a50187f702eb4d7e5ef38d9a7f1c79c", 155748),
    ("sha2-0.10.9", "https://static.crates.io/crates/sha2/sha2-0.10.9.crate", "a7507d819769d01a365ab707794a4084392c824f54a7a6a7862f8c3d0892b283", 29271),
    ("eprover-2f87cc42aae7780f197398dca7e1bb092081f0ca", "https://codeload.github.com/eprover/eprover/tar.gz/2f87cc42aae7780f197398dca7e1bb092081f0ca", None, None),
)


def main():
    signal.alarm(120)
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    started = time.monotonic()
    OUTPUT.mkdir(exist_ok=False)
    (OUTPUT / "archives").mkdir()
    (OUTPUT / "source").mkdir()
    metadata = json.loads((HERE / "dependency-metadata.json").read_bytes())
    # Crate checksums come from the observed official registry metadata. A
    # source tag/commit identifies E; its HTTPS archive digest is observed here.
    crates = {record["url"]: record for record in metadata["crates"]}
    network = expanded = files = 0
    records = []
    for root_name, url, digest, expected_size in FIXED:
        if url in crates:
            record = crates[url]
            # Require both independent literal values and pinned metadata.
            if record["sha256"] != digest or record["bytes"] != expected_size:
                raise ValueError("Source specification differs from official metadata.")
        elif url != metadata["e"]["url"]:
            raise ValueError("Unexpected E source URL.")
        archive = OUTPUT / "archives" / (root_name + ".tar.gz")
        sha = hashlib.sha256()
        received = 0
        request = urllib.request.Request(url, headers={"User-Agent": "Hydra-local-pinned-build/1"})
        with urllib.request.urlopen(request, timeout=20) as response, archive.open("xb") as stream:
            if response.geturl() != url:
                raise ValueError("Unexpected source download redirect.")
            while part := response.read(64 * 1024):
                network += len(part)
                received += len(part)
                if network > MAX_NETWORK:
                    raise ValueError("Combined source network limit exceeded.")
                sha.update(part)
                stream.write(part)
        if digest is not None and (sha.hexdigest() != digest or received != expected_size):
            raise ValueError("Pinned crate checksum or size changed.")
        inventory = {}
        with tarfile.open(archive, "r:gz") as source:
            for member in source:
                path = PurePosixPath(member.name)
                if path.is_absolute() or not path.parts or path.parts[0] != root_name or any(part in ("", ".", "..") for part in path.parts):
                    raise ValueError("Archive path escaped its fixed source directory.")
                destination = OUTPUT / "source" / str(path)
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile() or not 0 <= member.size <= 64 * 1024**2:
                    raise ValueError("Only bounded regular source files are extracted.")
                files += 1
                expanded += member.size
                if files > MAX_FILES or expanded > MAX_EXPANDED:
                    raise ValueError("Combined source expansion limit exceeded.")
                destination.parent.mkdir(parents=True, exist_ok=True)
                value = source.extractfile(member).read(member.size + 1)
                if len(value) != member.size:
                    raise ValueError("Incomplete source member.")
                with destination.open("xb") as stream:
                    stream.write(value)
                # Preserve only user execute when source requires it; no setuid.
                destination.chmod(0o700 if member.mode & 0o111 else 0o600)
                inventory[str(path.relative_to(root_name))] = {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
        records.append({"root": root_name, "url": url, "archive": {"bytes": received, "sha256": sha.hexdigest()},
                        "upstream_checksum_available": digest is not None, "files": inventory})
    result = {"schema": "hydra-p9-fixed-source-download-v1", "status": "downloaded-not-built-or-executed",
              "network_bytes": network, "expanded_bytes": expanded, "file_count": files,
              "limits": {"network_bytes": MAX_NETWORK, "expanded_bytes": MAX_EXPANDED, "files": MAX_FILES,
                         "wall_seconds": 120}, "sources": records,
              "elapsed_seconds": time.monotonic() - started, "solver_executions": 0}
    with (OUTPUT / "result.json").open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "sources"}, indent=2))


if __name__ == "__main__":
    main()
