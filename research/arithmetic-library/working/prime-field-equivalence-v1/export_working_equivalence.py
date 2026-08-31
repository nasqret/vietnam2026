#!/usr/bin/env python3
"""Original-HA, explicit-seed proof-data authoring in the new directory only.

Every real seed and every resulting body is checked by the unchanged
assembler. A --through prefix is scheduling data, not final acceptance.
The old113 artifact is never overwritten, and no row is admitted to Alpha.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import os
from pathlib import Path
import resource
import signal
import stat
import time

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import working_equivalence_support as support
from check_constructive_bottom_layers import authoring_rss_bytes


CPU_LIMITS, WALL_SECONDS = (170, 175), 180
ARTIFACT_DIRECTORY = support.HERE / "artifacts"
OUTPUT_PREFIX = "working-equivalence-"


def _directory_identity(path):
    value = path.lstat()
    if not stat.S_ISDIR(value.st_mode):
        raise support.EquivalenceError("proof data has a linked or non-directory ancestor")
    return value.st_dev, value.st_ino, value.st_mode


def destination(value):
    if not isinstance(value, (str, Path)):
        raise support.EquivalenceError("one exact new working output path is required")
    path = Path(value).absolute()
    if (".." in path.parts or path.parent != ARTIFACT_DIRECTORY
            or not path.name.startswith(OUTPUT_PREFIX) or not path.name.endswith(".json")):
        raise support.EquivalenceError("proof data must use a separate new equivalence artifact name")
    if path.exists() or path.is_symlink():
        raise support.EquivalenceError("mathematical proof data is never overwritten")
    for parent in ARTIFACT_DIRECTORY.parents:
        _directory_identity(parent)
    if ARTIFACT_DIRECTORY.exists() or ARTIFACT_DIRECTORY.is_symlink():
        _directory_identity(ARTIFACT_DIRECTORY)
        if ARTIFACT_DIRECTORY.lstat().st_uid != os.getuid():
            raise support.EquivalenceError("the new working artifact directory has a foreign owner")
    return path


def _resources():
    if resource.getrlimit(resource.RLIMIT_CPU) != CPU_LIMITS or time.monotonic() - _STARTED > WALL_SECONDS:
        raise support.EquivalenceError("the original authoring CPU/wall limits changed")
    return authoring_rss_bytes()


def write_exclusive(path, payload):
    """The existing narrow owned no-follow writer pattern, for this new root."""
    if type(payload) is not bytes or not 0 < len(payload) <= support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
        raise support.EquivalenceError("the canonical proof bytes exceed the unchanged payload limit")
    destination(path)
    ARTIFACT_DIRECTORY.mkdir(exist_ok=True)
    ancestors = tuple((parent, _directory_identity(parent))
                      for parent in (ARTIFACT_DIRECTORY, *ARTIFACT_DIRECTORY.parents))
    if any(not hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")):
        raise support.EquivalenceError("the original safe exclusive output flags are unavailable")
    descriptor = os.open(ARTIFACT_DIRECTORY, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_mode) != ancestors[0][1] or opened.st_uid != os.getuid():
            raise support.EquivalenceError("the owned new output directory changed before open")
        _resources()
        target = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=descriptor)
        with os.fdopen(target, "wb") as stream:
            if stream.write(payload) != len(payload):
                raise support.EquivalenceError("the exclusive proof-data write was incomplete")
        for parent, identity in ancestors:
            if _directory_identity(parent) != identity:
                raise support.EquivalenceError("an output ancestor changed during the exclusive write")
    finally:
        os.close(descriptor)
    support.check_pin(support.FilePin(path.relative_to(support.ROOT).as_posix(), len(payload),
                                     sha256(payload).hexdigest()),
                      support.ROOT, support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)


def export_authoring_bundle(owned_names, output, *, seed_bundles):
    if (type(seed_bundles) is not tuple or not seed_bundles
            or any(not isinstance(path, (str, Path)) for path in seed_bundles)):
        raise support.EquivalenceError("explicit real seed paths are required")
    support.closure._validate_seeds(seed_bundles)
    if support.ROOT / support.PRIOR113_ARTIFACT.path not in tuple(Path(path).absolute() for path in seed_bundles):
        raise support.EquivalenceError("the exact preserved113 artifact must be an explicit real seed")
    if (type(owned_names) is not tuple or not owned_names
            or any(type(name) is not str for name in owned_names)
            or len(set(owned_names)) != len(owned_names)):
        raise support.EquivalenceError("an exact nonempty ordered working selection is required")
    output = destination(output)
    state = support.load_candidate_state()
    before = support.state_binding(state)
    selected = support.select_support(state, owned_names)
    result = support.closure.assemble_bottom_layer_bundle(
        selected.frontier, seed_bundles=seed_bundles, batch_size=1,
        report=lambda message: print(message, flush=True))
    _resources()
    payload = support.closure.encode_proof_bundle(result.bundle, result.target).encode("utf-8")
    if len(payload) > support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
        raise support.EquivalenceError("the actual canonical proof data exceeds the unchanged ceiling")
    if support.state_binding(support.load_candidate_state()) != before:
        raise support.EquivalenceError("actual sources changed during original proof-data authoring")
    _resources()
    write_exclusive(output, payload)
    return {
        "schema": "peano-working-polynomial-equivalence-authoring-v1",
        "artifact": output.relative_to(support.ROOT).as_posix(),
        "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
        "nodes": result.receipt.node_count, "edges": result.receipt.dependency_edges,
        "body_nodes": result.receipt.total_body_nodes, "original_kernel_calls": result.receipt.kernel_calls,
        "owned_working_rows": len(selected.owned),
        "prior_non_admitted_working_rows": len(selected.previous_working_names),
        "added_non_admitted_working_rows": len(selected.added_working_names),
        "inherited_alpha_v32_rows": len(selected.inherited_alpha_names),
        "prior113_reclassified_as_alpha": False,
        "draft_proof_data_only": True, "original_ha_checked": True,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "complete_checkpoint_acceptance": False,
        "source_binding": before, "seconds": time.monotonic() - _STARTED,
        "peak_rss_bytes": _resources(), "cpu_limits": list(CPU_LIMITS), "wall_alarm_seconds": WALL_SECONDS,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=Path, action="append", required=True)
    parser.add_argument("--through", type=int, help="nonempty source-order authoring prefix only")
    args = parser.parse_args(argv)
    rows = support.load_candidate_state().rows
    if args.through is not None:
        if not 0 < args.through <= len(rows):
            parser.error("--through must select an actual nonempty source-order prefix")
        rows = rows[:args.through]
    report = export_authoring_bundle(tuple(row.name for row in rows), args.output, seed_bundles=tuple(args.seed))
    print(support.canonical(report).decode(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
