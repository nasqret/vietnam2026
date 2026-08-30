#!/usr/bin/env python3
"""Fresh original-HA authoring of separate working113 proof data.

Every supplied real seed is checked in full by the unchanged assembler.
An authoring prefix is staging data, never final combined acceptance. No
old working81 file is overwritten, and no runtime or admission is changed.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import resource
import signal
import time

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import working_euclidean_extension_support as support
import export_working_euclidean as previous_export
from check_constructive_bottom_layers import authoring_rss_bytes


CPU_LIMITS, WALL_SECONDS = (170, 175), 180
OUTPUT_PREFIX = "working-euclidean-extension-"
if Path(previous_export.__file__).resolve() != support.HERE / "export_working_euclidean.py":
    raise RuntimeError("the exact unchanged owned exclusive writer is required")


def destination(value):
    result = previous_export._destination(value)
    if not result.name.startswith(OUTPUT_PREFIX):
        raise support.ExtensionError("a separate extension artifact name is required")
    return result


def _resources():
    if resource.getrlimit(resource.RLIMIT_CPU) != CPU_LIMITS or time.monotonic() - _STARTED > WALL_SECONDS:
        raise support.ExtensionError("the unchanged authoring CPU/wall limits were not preserved")
    return authoring_rss_bytes()


def export_authoring_bundle(owned_names, output, *, seed_bundles):
    if (type(seed_bundles) is not tuple or not seed_bundles
            or any(not isinstance(path, (str, Path)) for path in seed_bundles)):
        raise support.ExtensionError("explicit real seed paths, freshly checked in full, are required")
    if (type(owned_names) is not tuple or not owned_names
            or any(type(name) is not str for name in owned_names)
            or len(set(owned_names)) != len(owned_names)):
        raise support.ExtensionError("an exact nonempty ordered working selection is required")
    support.closure._validate_seeds(seed_bundles)
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
        raise support.ExtensionError("the actual complete bytes exceed the original payload ceiling")
    if support.state_binding(support.load_candidate_state()) != before:
        raise support.ExtensionError("the exact extension inputs changed during original proof authoring")
    _resources()
    previous_export._write_exclusive(output, payload)
    peak = _resources()
    return {
        "schema": "peano-working-polynomial-euclidean-extension-authoring-v1",
        "artifact": output.relative_to(support.ROOT).as_posix(),
        "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
        "nodes": result.receipt.node_count, "edges": result.receipt.dependency_edges,
        "body_nodes": result.receipt.total_body_nodes, "original_kernel_calls": result.receipt.kernel_calls,
        "owned_working_rows": len(selected.owned),
        "prior_working81_rows": len(selected.previous_working_names),
        "added_working32_rows": len(selected.added_working_names),
        "inherited_alpha_v32_rows": len(selected.inherited_alpha_names),
        "prior_working_rows_reclassified_as_alpha": False,
        "draft_proof_data_only": True, "original_ha_checked": True,
        "independent_lean_checked": False, "ordinary_principals_checked": False,
        "complete_113_checkpoint_acceptance": False,
        "source_binding": before, "seconds": time.monotonic() - _STARTED,
        "peak_rss_bytes": peak, "cpu_limits": list(CPU_LIMITS), "wall_alarm_seconds": WALL_SECONDS,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=Path, action="append", required=True)
    parser.add_argument("--through", type=int, help="nonempty source-order authoring prefix only")
    args = parser.parse_args(argv)
    state = support.load_candidate_state()
    rows = state.rows
    if args.through is not None:
        if not 0 < args.through <= len(rows):
            parser.error("--through must select 1..113 actual source-order rows")
        rows = rows[:args.through]
    report = export_authoring_bundle(tuple(row.name for row in rows), args.output, seed_bundles=tuple(args.seed))
    print(support.canonical(report).decode(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
