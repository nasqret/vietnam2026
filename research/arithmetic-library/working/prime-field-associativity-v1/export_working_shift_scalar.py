#!/usr/bin/env python3
"""Author real shift/scalar proof data with unchanged HA and explicit seeds.

Only this new directory's uniquely named artifacts may be created. A prefix
is scheduling data, never a final checkpoint. Every supplied real seed and
every final body is checked by the original assembler; no observation is
read as proof authority. No existing archive or release can be overwritten.
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

import working_shift_scalar_support as support
from check_constructive_bottom_layers import authoring_rss_bytes

CPU_LIMITS, WALL_SECONDS = (170, 175), 180
ARTIFACT_DIRECTORY = support.ARTIFACT_DIRECTORY
OUTPUT_PREFIX = support.OUTPUT_PREFIX


def _directory_identity(path):
    value = path.lstat()
    support._require(stat.S_ISDIR(value.st_mode), "proof output has a linked or non-directory ancestor")
    return value.st_dev, value.st_ino, value.st_mode


def destination(value):
    support._require(isinstance(value, (str, Path)), "one exact new proof-data path is required")
    path = Path(value).absolute()
    support._require(".." not in path.parts and path.parent == ARTIFACT_DIRECTORY
                     and path.name.startswith(OUTPUT_PREFIX) and path.name.endswith(".json")
                     and support._safe_relative(path.name),
                     "proof data must use a separate new shift/scalar artifact basename")
    support._require(not path.exists() and not path.is_symlink(),
                     "existing mathematical proof data is never overwritten")
    for parent in ARTIFACT_DIRECTORY.parents:
        _directory_identity(parent)
    if ARTIFACT_DIRECTORY.exists() or ARTIFACT_DIRECTORY.is_symlink():
        _directory_identity(ARTIFACT_DIRECTORY)
        support._require(ARTIFACT_DIRECTORY.lstat().st_uid == os.getuid(),
                         "the new proof-data directory has a foreign owner")
    return path


def _resources():
    support._require(resource.getrlimit(resource.RLIMIT_CPU) == CPU_LIMITS
                     and time.monotonic() - _STARTED <= WALL_SECONDS,
                     "the original authoring CPU/wall limits changed")
    return authoring_rss_bytes()


def write_exclusive(path, payload):
    """Owned no-follow output; failed writes remove only the newly owned inode."""
    support._require(type(payload) is bytes and 0 < len(payload) <= support.MAX_BYTES,
                     "proof-data bytes exceed the unchanged payload ceiling")
    path = destination(path)
    ARTIFACT_DIRECTORY.mkdir(exist_ok=True)
    ancestors = tuple((parent, _directory_identity(parent))
                      for parent in (ARTIFACT_DIRECTORY, *ARTIFACT_DIRECTORY.parents))
    support._require(all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")),
                     "the original safe exclusive output flags are unavailable")
    descriptor = os.open(ARTIFACT_DIRECTORY, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    created = None
    try:
        opened = os.fstat(descriptor)
        support._require((opened.st_dev, opened.st_ino, opened.st_mode) == ancestors[0][1]
                         and opened.st_uid == os.getuid(), "the exact owned output directory changed")
        _resources()
        target = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=descriptor)
        with os.fdopen(target, "wb") as stream:
            info = os.fstat(stream.fileno())
            created = (info.st_dev, info.st_ino)
            support._require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1,
                             "the exclusive proof output is not an owned regular inode")
            support._require(stream.write(payload) == len(payload), "the exclusive proof-data write was incomplete")
            stream.flush()
        for parent, identity in ancestors:
            support._require(_directory_identity(parent) == identity,
                             "an output ancestor changed during the exclusive write")
        support.check_pin(support.FilePin(path.relative_to(support.ROOT).as_posix(), len(payload),
                                         sha256(payload).hexdigest()), support.ROOT, support.MAX_BYTES)
        _resources()
    except BaseException:
        if created is not None:
            info = os.stat(path.name, dir_fd=descriptor, follow_symlinks=False)
            support._require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                             and info.st_nlink == 1 and (info.st_dev, info.st_ino) == created,
                             "rollback refuses to remove a changed or foreign output inode")
            os.unlink(path.name, dir_fd=descriptor)
        raise
    finally:
        os.close(descriptor)


def export_authoring_bundle(owned_names, output, *, seed_bundles):
    output = destination(output)
    state = support.load_candidate_state()
    before = support.state_binding(state)
    seeds = support.seed_inventory(seed_bundles)
    selected = support.select_support(state, owned_names)
    coverage = support.seed_coverage(selected, seeds)
    support._require(not coverage["missing_names"],
                     "explicit real seeds lack inherited targets: " + ", ".join(coverage["missing_names"]))
    execution = support.execution_selection(state, owned_names)
    result = support.closure.assemble_bottom_layer_bundle(
        execution.frontier, seed_bundles=tuple(support.ROOT / pin.path for pin in seeds),
        batch_size=1, report=lambda message: print(message, flush=True))
    _resources()
    support._require(result.plan == execution.plan, "the original assembler returned a different dependency plan")
    payload = support.closure.encode_proof_bundle(result.bundle, result.target).encode("utf-8")
    support._require(len(payload) <= support.MAX_BYTES, "the canonical artifact exceeds its original byte ceiling")
    for pin in seeds:
        support.check_pin(pin, support.ROOT, support.MAX_BYTES)
    support._require(support.state_binding(support.load_candidate_state()) == before,
                     "actual proof inputs changed during original HA authoring")
    _resources()
    write_exclusive(output, payload)
    return {
        "schema": "peano-working-shift-scalar-authoring-v1",
        "artifact": output.relative_to(support.ROOT).as_posix(), "bytes": len(payload),
        "sha256": sha256(payload).hexdigest(), "nodes": result.receipt.node_count,
        "edges": result.receipt.dependency_edges, "body_nodes": result.receipt.total_body_nodes,
        "original_kernel_calls": result.receipt.kernel_calls,
        "selected_new_non_admitted_rows": len(selected.owned),
        "inherited_canonical_source_rows": len(selected.support),
        "complete_source_rows": len(selected.complete_specs),
        "maximal_roots": list(execution.plan.root_names),
        "explicit_seed_pins": [support.asdict(pin) for pin in seeds],
        "source_binding": before, "draft_proof_data_only": True, "original_ha_checked": True,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "global_current4092_novelty_checked": False, "complete_checkpoint_acceptance": False,
        "associativity_proved": False, "gcd_bezout_proved": False, "full_G091_proved": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "seconds": time.monotonic() - _STARTED, "peak_rss_bytes": _resources(),
        "cpu_limits": list(CPU_LIMITS), "wall_alarm_seconds": WALL_SECONDS,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=Path, action="append", required=True)
    parser.add_argument("--through", type=int, help="nonempty source-order draft prefix only")
    args = parser.parse_args(argv)
    rows = support.load_candidate_state().rows
    if args.through is not None:
        if not 0 < args.through <= len(rows):
            parser.error("--through must select an actual nonempty source-order prefix")
        rows = rows[:args.through]
    report = export_authoring_bundle(tuple(row.name for row in rows), args.output,
                                     seed_bundles=tuple(args.seed))
    print(support.canonical(report).decode(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
