#!/usr/bin/env python3
"""Metadata-only exact runtime check; no package installation or ML imports."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from training.peano_hydra import frontier_pilot_launch as gate
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    gate.require(platform.python_version() == gate.RUNTIME["python_version"]
                 and platform.machine() == gate.RUNTIME["machine"], "reviewed ARM Python 3.13.5 required")
    path = "training/peano_policy/requirements-helios.lock"
    raw = gate.read(path, 16384)
    gate.require(hashlib.sha256(raw).hexdigest() == gate.RUNTIME["requirements_sha256"],
                 "the exact original Helios package lock is required")
    checked = {}
    markers = {"python_version": "3.13", "python_full_version": platform.python_version()}
    for line in raw.decode().splitlines():
        line = line.partition("#")[0].strip()
        if not line:
            continue
        requirement = Requirement(line)
        pins = tuple(requirement.specifier)
        gate.require(requirement.url is None and not requirement.extras and len(pins) == 1
                     and pins[0].operator == "==" and "*" not in pins[0].version,
                     "runtime lock must contain exact package pins")
        if requirement.marker is not None and not requirement.marker.evaluate(markers):
            continue
        name = canonicalize_name(requirement.name)
        gate.require(name not in checked and importlib.metadata.version(requirement.name) == pins[0].version,
                     "duplicate or mismatched reviewed runtime package: " + name)
        checked[name] = pins[0].version
    gate.require(len(checked) == 29 and not {"torch", "transformers", "peft"} & set(sys.modules),
                 "reviewed runtime must have exactly 29 active pins without model imports")
    print(json.dumps({"schema": "peano-hydra-frontier-runtime-lock-v1", "status": "verified",
                      "python": platform.python_version(), "machine": platform.machine(),
                      "requirements": {"path": path, "sha256": gate.RUNTIME["requirements_sha256"]},
                      "packages": checked, "model_imported": False}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
