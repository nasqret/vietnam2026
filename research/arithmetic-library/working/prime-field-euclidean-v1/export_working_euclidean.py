#!/usr/bin/env python3
"""Explicit-seed, working-only genuine HA proof-data authoring.

Partial prefixes are scheduling artifacts, never final checkpoints. Every
supplied seed is checked in full by the unchanged assembler. No historical
provider or original limit is modified, and no release directory is written.
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

import working_euclidean_support as support
from check_constructive_bottom_layers import authoring_rss_bytes


CPU_LIMITS, WALL_SECONDS = (170, 175), 180
ARTIFACT_DIRECTORY = support.HERE / "artifacts"


def _directory_identity(path):
    value = path.lstat()
    if not stat.S_ISDIR(value.st_mode):
        raise support.WorkingError("proof data has a linked or non-directory ancestor")
    return value.st_dev, value.st_ino, value.st_mode


def _destination(value):
    if not isinstance(value, (str, Path)):
        raise support.WorkingError("the working output needs an explicit path")
    path = Path(value).absolute()
    if (".." in path.parts or path.parent != ARTIFACT_DIRECTORY
            or not path.name.endswith(".json") or path.name.startswith(".")):
        raise support.WorkingError("proof data must name one new JSON file in the working artifacts directory")
    if path.exists() or path.is_symlink():
        raise support.WorkingError("mathematical proof data is never overwritten")
    for parent in ARTIFACT_DIRECTORY.parents:
        _directory_identity(parent)
    if ARTIFACT_DIRECTORY.exists() or ARTIFACT_DIRECTORY.is_symlink():
        _directory_identity(ARTIFACT_DIRECTORY)
        if ARTIFACT_DIRECTORY.lstat().st_uid != os.getuid():
            raise support.WorkingError("the working artifact directory has a foreign owner")
    return path


def _write_exclusive(path, payload):
    """One owned no-follow file; no old output is replaced or deleted."""
    if type(payload) is not bytes or not 0 < len(payload) <= support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
        raise support.WorkingError("the ordinary proof payload exceeds its unchanged bound")
    _destination(path)
    ARTIFACT_DIRECTORY.mkdir(exist_ok=True)
    ancestors = tuple((parent, _directory_identity(parent)) for parent in (ARTIFACT_DIRECTORY, *ARTIFACT_DIRECTORY.parents))
    required = ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")
    if any(not hasattr(os, name) for name in required):
        raise support.WorkingError("safe exclusive proof-data flags are unavailable")
    descriptor = os.open(ARTIFACT_DIRECTORY, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_mode) != ancestors[0][1] or opened.st_uid != os.getuid():
            raise support.WorkingError("the working output directory changed before open")
        authoring_rss_bytes()
        target = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=descriptor)
        with os.fdopen(target, "wb") as stream:
            if stream.write(payload) != len(payload):
                raise support.WorkingError("the exclusive proof-data write was incomplete")
        for parent, identity in ancestors:
            if _directory_identity(parent) != identity:
                raise support.WorkingError("a working output ancestor changed during the write")
    finally:
        os.close(descriptor)
    support.check_pin(support.FilePin(path.relative_to(support.ROOT).as_posix(), len(payload),
                                     sha256(payload).hexdigest()),
                      support.ROOT, support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)


def export_authoring_bundle(owned_names, output, *, seed_bundles):
    if (type(seed_bundles) is not tuple or not seed_bundles
            or any(not isinstance(path, (str, Path)) for path in seed_bundles)):
        raise support.WorkingError("authoring requires explicit real seed paths, checked in full")
    destination = _destination(output)
    state = support.load_candidate_state()
    before = support.state_binding(state)
    selected = support.select_support(state.rows, owned_names)
    # state_binding authenticates all 41 current providers. Only the explicit
    # selected seeds are decoded and freshly checked as seeds; unused provider
    # hashes never stand in for proof acceptance.
    result = support.closure.assemble_bottom_layer_bundle(
        selected.frontier, seed_bundles=seed_bundles, batch_size=1,
        report=lambda message: print(message, flush=True))
    authoring_rss_bytes()
    payload = support.closure.encode_proof_bundle(result.bundle, result.target).encode("utf-8")
    if len(payload) > support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
        raise support.WorkingError("the actual proof data exceeds the original payload ceiling")
    if support.state_binding(support.load_candidate_state()) != before:
        raise support.WorkingError("the sources changed during actual HA proof-data assembly")
    authoring_rss_bytes()
    _write_exclusive(destination, payload)
    peak = authoring_rss_bytes()
    return {
        "schema": "peano-working-polynomial-euclidean-authoring-v1",
        "artifact": destination.relative_to(support.ROOT).as_posix(),
        "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
        "nodes": result.receipt.node_count, "edges": result.receipt.dependency_edges,
        "body_nodes": result.receipt.total_body_nodes,
        "owned_rows": len(selected.owned), "cross_track_rows": len(selected.current_support),
        "inherited_alpha_v32_rows": len(selected.parent_support),
        "draft_proof_data_only": True, "original_ha_checked": True,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "final_complete_inventory_acceptance": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "peak_rss_bytes": peak,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=Path, action="append", required=True)
    parser.add_argument("--through", type=int, help="nonempty source-order draft prefix only")
    args = parser.parse_args(argv)
    state = support.load_candidate_state()
    rows = state.rows
    if args.through is not None:
        if not 0 < args.through <= len(rows):
            parser.error("--through must select a nonempty working prefix")
        rows = rows[:args.through]
    report = export_authoring_bundle(tuple(row.name for row in rows), args.output,
                                     seed_bundles=tuple(args.seed))
    if time.monotonic() - _STARTED > WALL_SECONDS or resource.getrlimit(resource.RLIMIT_CPU) != CPU_LIMITS:
        raise support.WorkingError("the original authoring process bounds changed")
    print(support.canonical(report).decode(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
