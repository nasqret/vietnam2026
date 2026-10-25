"""Derive pinned CPython checked-hash bytecode without importing any backend.

The original installation and failed gate remain unchanged. A fresh derived
tree retains every exact source/data file and adds deterministic bytecode only.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import py_compile
import resource
import signal
import sys
import time


HERE = Path(__file__).resolve().parent
BASE = HERE / "app/.runtime/advisers"
DESTINATION = BASE / "cp311-precompiled-01"
SOURCE_PIN = {"bytes": 264593, "sha256": "ea067a4ea690685589f7d3b6210ca12bd80e5ada20935d8aa7e43879343ac4c9"}
MAX_TOTAL_EXPANSION = 200 * 1024**2


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(60)
    if sys.version_info[:3] != (3, 11, 12):
        raise ValueError("The recorded worker interpreter is CPython 3.11.12.")
    started = time.monotonic()
    source_raw = (BASE / "manifest.json").read_bytes()
    if pin(source_raw) != SOURCE_PIN:
        raise ValueError("The original package manifest changed.")
    source = json.loads(source_raw)
    DESTINATION.mkdir(exist_ok=False)
    packages = DESTINATION / "packages"
    packages.mkdir()
    plan = {"schema": "hydra-adviser-bytecode-plan-v1", "source_manifest": SOURCE_PIN,
        "diagnosis": "First SymPy helper received actual SIGXCPU (-24) with the one-second CPU cap; source compilation was not cached.",
        "cpu_seconds": 30, "wall_seconds": 60, "max_total_expanded_bytes": MAX_TOTAL_EXPANSION,
        "backend_imports": 0, "backend_launches": 0, "network_bytes": 0,
        "source_interpreter": sys.version, "runtime_limits_changed": False,
        "invalidation": "CHECKED_HASH", "optimization": 0, "automatic_retry": False}
    (DESTINATION / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    files, bytecode = {}, {}
    total = 0
    for name, descriptor in source["files"].items():
        original = BASE / "packages" / name
        raw = original.read_bytes()
        if pin(raw) != descriptor:
            raise ValueError("An original dependency file changed.")
        path = packages / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o644)
        files[name] = descriptor
        total += len(raw)
        if path.suffix == ".py":
            cache = Path(importlib.util.cache_from_source(str(path), optimization=""))
            cache.parent.mkdir(exist_ok=True)
            py_compile.compile(str(path), cfile=str(cache), dfile="hydra-adviser-source-v1/" + name,
                               doraise=True, optimize=0,
                               invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)
            compiled = cache.read_bytes()
            if (compiled[:4] != importlib.util.MAGIC_NUMBER or int.from_bytes(compiled[4:8], "little") != 3
                    or compiled[8:16] != importlib.util.source_hash(raw)):
                raise ValueError("Compiled bytecode does not bind the exact source bytes.")
            relative = cache.relative_to(packages).as_posix()
            files[relative] = pin(compiled)
            bytecode[relative] = {"source": name, "source_sha256": descriptor["sha256"],
                                  "checked_source_hash": compiled[8:16].hex()}
            total += len(compiled)
            cache.chmod(0o644)
        if total + source["expanded_bytes"] > MAX_TOTAL_EXPANSION or len(files) > 10000:
            raise ValueError("Derived bytecode exceeds the bounded package allocation.")
    if "sympy" in sys.modules or "cvc5" in sys.modules:
        raise ValueError("Bytecode preparation must never import either backend.")
    if pin((BASE / "manifest.json").read_bytes()) != SOURCE_PIN:
        raise ValueError("Original package manifest changed during compilation.")
    manifest = {"schema": "hydra-adviser-bytecode-package-v1", "status": "prepared-not-executed",
        "platform": "darwin-arm64", "python_abi": "cp311", "python_version": "3.11.12",
        "source_manifest": SOURCE_PIN, "files": dict(sorted(files.items())),
        "expanded_bytes": total, "bytecode": dict(sorted(bytecode.items())),
        "bytecode_magic_hex": importlib.util.MAGIC_NUMBER.hex(), "invalidation": "CHECKED_HASH",
        "backend_imports": 0, "backend_launches": 0}
    encoded = (json.dumps(manifest, indent=2) + "\n").encode()
    if len(encoded) > 2 * 1024**2:
        raise ValueError("Derived inventory exceeds 2 MiB.")
    (DESTINATION / "manifest.json").write_bytes(encoded)
    result = {"status": "prepared-not-executed", "manifest": pin(encoded), "files": len(files),
        "compiled_files": len(bytecode), "derived_expanded_bytes": total,
        "source_and_derived_expanded_bytes": source["expanded_bytes"] + total,
        "elapsed_seconds": time.monotonic() - started, "backend_imports": 0, "backend_launches": 0,
        "source_manifest_unchanged": True, "runtime_limits_changed": False}
    (DESTINATION / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
