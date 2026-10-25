"""One bounded, no-build/no-import extraction of the three exact PyPI wheels."""
from pathlib import Path, PurePosixPath
import email.parser
import hashlib
import json
import os
import platform
import resource
import signal
import stat
import sys
import time
import urllib.request
import zipfile


HERE = Path(__file__).resolve().parent
DESTINATION = HERE / "app/.runtime/advisers"
METADATA_SHA = "3e671122dd7922a00787296dce07e5a48e9eeec317e91eafec9646a80c0ae220"
MAX_EXPANDED = 200 * 1024**2
MAX_FILES = 10000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    signal.alarm(120)
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_EXPANDED, MAX_EXPANDED))
    require(sys.version_info[:2] == (3, 11) and sys.platform == "darwin" and platform.machine() == "arm64",
            "This exact dependency package requires Python 3.11 on macOS arm64.")
    metadata_bytes = (HERE / "dependency-metadata.json").read_bytes()
    require(hashlib.sha256(metadata_bytes).hexdigest() == METADATA_SHA, "Reviewed package metadata changed.")
    metadata = json.loads(metadata_bytes)
    require(not DESTINATION.exists(), "Preserving the existing adviser installation; no overwrite or retry.")
    DESTINATION.mkdir(parents=True)
    wheels, packages = DESTINATION / "wheels", DESTINATION / "packages"
    wheels.mkdir()
    packages.mkdir()
    started = time.monotonic()
    plan = {"schema": "hydra-adviser-install-plan-v1", "metadata_sha256": METADATA_SHA,
            "network_bytes": sum(row["wheel"]["bytes"] for row in metadata["packages"]),
            "max_network_bytes": 20 * 1024**2, "max_expanded_bytes": MAX_EXPANDED,
            "max_files": MAX_FILES, "wall_seconds": 120, "cpu_seconds": 60,
            "builds": 0, "backend_imports": 0, "backend_launches": 0, "automatic_retries": 0,
            "model_environment_modified": False, "packages": metadata["packages"]}
    require(plan["network_bytes"] <= plan["max_network_bytes"], "Reviewed downloads exceed the cap.")
    (DESTINATION / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    files, omitted_resources, expanded, downloaded = {}, {}, 0, 0
    for row in metadata["packages"]:
        wheel = row["wheel"]
        archive_path = wheels / wheel["filename"]
        digest, total = hashlib.sha256(), 0
        with urllib.request.urlopen(wheel["url"], timeout=30) as response, archive_path.open("xb") as stream:
            require(response.geturl() == wheel["url"], "Unexpected wheel redirect.")
            while part := response.read(1024 * 1024):
                total += len(part)
                downloaded += len(part)
                require(total <= wheel["bytes"] and downloaded <= plan["max_network_bytes"],
                        "Wheel download exceeded its exact byte bound.")
                stream.write(part)
                digest.update(part)
        require(total == wheel["bytes"] and digest.hexdigest() == wheel["sha256"], "Wheel SHA256/size mismatch.")
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            require(len(infos) <= MAX_FILES and sum(info.file_size for info in infos) + expanded <= MAX_EXPANDED,
                    "Expanded wheel exceeds its cap.")
            for info in infos:
                path = PurePosixPath(info.filename)
                require(not path.is_absolute() and path.parts and all(part not in {"", ".", ".."}
                        for part in path.parts) and "\\" not in info.filename and len(info.filename) <= 256,
                        "Unsafe archive member path.")
                mode = (info.external_attr >> 16) & 0xFFFF
                require(not stat.S_ISLNK(mode) and (not mode or stat.S_IFMT(mode) in
                        (0, stat.S_IFREG, stat.S_IFDIR)), "Non-regular wheel member.")
                if info.is_dir():
                    continue
                if any(part.endswith(".data") for part in path.parts):
                    # The SymPy wheel includes an operator man page. We do not
                    # install console tools or write outside this package tree.
                    allowed = {"sympy-1.14.0.data/data/share/man/man1/isympy.1",
                               "sympy-1.14.0.data/scripts/isympy"}
                    require(info.filename in allowed and info.file_size <= 65536,
                            "Unexpected wheel relocation resource.")
                    body = archive.read(info)
                    omitted_resources[info.filename] = {"bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "reason": "Operator console/man resource is not installed or executed."}
                    continue
                require(path.suffix not in {".pyc", ".pth"} and "__pycache__" not in path.parts,
                        "Wheel relocation, import hooks and bytecode are outside this installer.")
                name = path.as_posix()
                require(name not in files and len(files) < MAX_FILES, "Duplicate/oversized wheel inventory.")
                require(0 <= info.file_size <= MAX_EXPANDED, "Invalid archive member size.")
                target = packages.joinpath(*path.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                digest, size = hashlib.sha256(), 0
                with archive.open(info) as source, target.open("xb") as sink:
                    while part := source.read(1024 * 1024):
                        size += len(part)
                        expanded += len(part)
                        require(size <= info.file_size and expanded <= MAX_EXPANDED, "Expanded member exceeded its cap.")
                        sink.write(part)
                        digest.update(part)
                require(size == info.file_size, "Incomplete archive member.")
                target.chmod(0o644)
                files[name] = {"bytes": size, "sha256": digest.hexdigest()}
        dist_path = packages / f"{row['name']}-{row['version']}.dist-info/METADATA"
        parsed = email.parser.BytesParser().parsebytes(dist_path.read_bytes(), headersonly=True)
        require(parsed["Name"].lower() == row["name"] and parsed["Version"] == row["version"],
                "Installed metadata does not match the approved distribution.")
    manifest = {"schema": "hydra-adviser-package-v1", "status": "installed-not-executed",
        "platform": "darwin-arm64", "python_abi": "cp311", "metadata_sha256": METADATA_SHA,
        "wheels": [{"name": row["name"], "version": row["version"], **row["wheel"]}
                   for row in metadata["packages"]],
        "files": dict(sorted(files.items())), "expanded_bytes": expanded,
        "omitted_resources": omitted_resources,
        "backend_imports": 0, "backend_launches": 0}
    raw = (json.dumps(manifest, indent=2) + "\n").encode()
    (DESTINATION / "manifest.json").write_bytes(raw)
    receipt = {"status": "installed-not-executed", "manifest": {"bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest()}, "downloaded_bytes": downloaded,
        "expanded_bytes": expanded, "file_count": len(files),
        "elapsed_seconds": round(time.monotonic() - started, 4),
        "model_environment_modified": False, "backend_imports": 0, "backend_launches": 0}
    (DESTINATION / "install-result.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
