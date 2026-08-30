#!/usr/bin/env python3
"""Produce one freshly HA-checked old theorem as non-authorizing seed data.

The unchanged ``succ_injective`` entry has no premises and uses ``apply PA2``.
Its actual existing script is reconstructed by the original tactic compiler;
the original kernel checks its exact ordinary target, the complete one-node
bundle, and the decoded canonical bytes. No working row or Alpha edition is
loaded, and no existing file is overwritten. This is not the 113-row gate.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import resource
import signal
import sys
import time

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import working_euclidean_support as support
from check_constructive_bottom_layers import authoring_rss_bytes
from export_working_euclidean import _destination, _write_exclusive
from peano_lab.kernel.checker import check
from peano_lab.library import theorems


SOURCE = support.FilePin(
    "peano-lab/py/peano_lab/library/theorems.py", 536011,
    "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919")
NAME = "succ_injective"
STATEMENT = "forall n m. S n = S m -> n = m"
OUTPUT_NAME = "inherited-successor-injective-seed-v1.json"


def _binding():
    support.require_final_registration()
    for pin in support.inherited.PARENT_CONTROL_PINS:
        support.check_pin(pin, support.ROOT, support.MAX_SOURCE_BYTES)
    support.check_pin(SOURCE, support.ROOT, support.MAX_SOURCE_BYTES)
    if Path(theorems.__file__).resolve() != support.ROOT / SOURCE.path:
        raise support.WorkingError("the exact existing theorem source resolved elsewhere")
    helpers = []
    for name in (Path(__file__).name, "working_euclidean_support.py", "export_working_euclidean.py"):
        raw = support.bounded_bytes(support.HERE / name, support.MAX_SOURCE_BYTES)
        helpers.append([name, len(raw), sha256(raw).hexdigest()])
    return sha256(support.canonical({
        "source": [SOURCE.path, SOURCE.bytes, SOURCE.sha256], "helpers": helpers,
        "name": NAME, "statement": STATEMENT, "dependencies": [], "script": ["apply PA2"],
    })).hexdigest()


def author(output):
    destination = _destination(output)
    if destination.name != OUTPUT_NAME:
        raise support.WorkingError("only the separate inherited successor seed path is permitted")
    before = _binding()
    matches = tuple(row for row in theorems.THEOREMS if row.name == NAME)
    if len(matches) != 1:
        raise support.WorkingError("the actual old theorem has no unique entry")
    row = matches[0]
    if (row.statement, row.dependencies, row.script) != (STATEMENT, (), ("apply PA2",)):
        raise support.WorkingError("the exact inherited statement, premises or script changed")
    target = theorems._closed_formula(STATEMENT)
    body = support.closure._reconstruct_body(row, {NAME: row})
    limits = support.closure.DEFAULT_LAYERED_REPLAY_LIMITS
    occurrences, objects, *_ = support.closure._proof_envelope_metrics_bounded(
        body, max_proof_occurrences=support.closure.MAX_BATCH_PROOF_NODES,
        max_proof_objects=support.closure.MAX_BATCH_PROOF_OBJECTS,
        max_proof_depth=limits.max_body_depth,
        max_annotation_occurrences=limits.max_body_annotation_occurrences,
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_body_envelope_depth,
        label="exact inherited successor seed")
    if not check((), body, target):
        raise support.WorkingError("the ordinary inherited target failed original HA")
    # The unchanged codec materializes this exact default allowance. Make it
    # explicit so full structural equality also compares the fuel field.
    bundle = support.closure.ProofBundle((support.closure.BundleNode(0, target, (), body, 8 * occurrences + 16),), 0)
    receipt = support.closure.check_proof_bundle(bundle, target)
    if (receipt.node_count, receipt.dependency_edges, receipt.kernel_calls) != (1, 0, 1):
        raise support.WorkingError("the complete inherited-only seed accounting changed")
    payload = support.closure.encode_proof_bundle(bundle, target).encode("utf-8")
    if not 0 < len(payload) <= support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
        raise support.WorkingError("the canonical seed exceeds the unchanged payload bound")
    decoded, decoded_target = support.closure.decode_proof_bundle(payload.decode("utf-8"))
    if decoded != bundle or decoded_target != target:
        raise support.WorkingError("the original codec did not preserve the exact complete seed")
    decoded_receipt = support.closure.check_proof_bundle(decoded, target)
    if decoded_receipt != receipt:
        raise support.WorkingError("the decoded canonical seed did not pass the same original checks")
    if _binding() != before:
        raise support.WorkingError("the actual inherited inputs changed during reconstruction")
    editions = sorted(name for name in sys.modules if name.startswith("peano_lab.library.editions_v"))
    if editions:
        raise support.WorkingError("the source-selected single theorem unexpectedly imported Alpha")
    if time.monotonic() - _STARTED > 180 or resource.getrlimit(resource.RLIMIT_CPU) != (170, 175):
        raise support.WorkingError("the original seed-authoring CPU/wall bounds changed")
    authoring_rss_bytes()
    _write_exclusive(destination, payload)
    return {
        "schema": "peano-working-inherited-successor-seed-authoring-v1",
        "artifact": destination.relative_to(support.ROOT).as_posix(),
        "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
        "name": NAME, "role": "inherited_alpha_v32", "statement": STATEMENT,
        "source": [SOURCE.path, SOURCE.bytes, SOURCE.sha256],
        "dependencies": [], "script": ["apply PA2"],
        "nodes": receipt.node_count, "edges": receipt.dependency_edges,
        "body_nodes": occurrences, "body_objects": objects,
        "original_kernel_calls": receipt.kernel_calls,
        "decoded_kernel_calls": decoded_receipt.kernel_calls,
        "original_ordinary_ha_checked": True, "original_whole_bundle_ha_checked": True,
        "decoded_canonical_bytes_ha_checked": True, "source_binding": before,
        "new_working_theorems": 0, "alpha_editions_imported": editions,
        "independent_lean_checked": False, "complete_113_checkpoint_acceptance": False,
        "draft_seed_proof_data_only": True,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    report = author(parser.parse_args(argv).output)
    report.update(seconds=time.monotonic() - _STARTED, peak_rss_bytes=authoring_rss_bytes(),
                  cpu_limits=[170, 175], wall_alarm_seconds=180)
    print(support.canonical(report).decode(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
