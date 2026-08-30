#!/usr/bin/env python3
"""Freshly checked inherited-only proof data, not an 81-row checkpoint.

The exact old 210-node polynomial-products seed is checked in its entirety.
Three unchanged inherited theorem scripts are reconstructed against their
actual ordered premises, then the whole 214-node result is checked again.
The old packaging node remains a dependency of the new packaging node, so
no original seed body is discarded or left unreachable. No Alpha edition,
stored receipt, source catalogue row table, or new working factory is used
as proof authority. The ordinary original checker and codec decide validity.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
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
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula


SEED = support.FilePin(
    "research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json",
    745307, "55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3")
NAMES = ("add_le_cancel_right", "lt_of_lt_of_le", "matrix_rank_prefix_equality_symmetric")
MATRIX_SOURCE = "peano-lab/py/peano_lab/library/matrix_rank_finite_coding_candidate.py"
HELPERS = (Path(__file__).name, "working_euclidean_support.py", "export_working_euclidean.py")


def _read(pin, maximum):
    support.check_pin(pin, support.ROOT, maximum)
    raw = support.bounded_bytes(support.ROOT / pin.path, maximum)
    if (len(raw), sha256(raw).hexdigest()) != (pin.bytes, pin.sha256):
        raise support.WorkingError("an inherited seed/source changed during the bounded read")
    return raw


def _source_binding():
    # This authenticates the real installed catalogue bytes without importing
    # an edition or parsing its large logical row components.
    support.require_final_registration()
    for pin in support.inherited.PARENT_CONTROL_PINS:
        support.check_pin(pin, support.ROOT, support.MAX_SOURCE_BYTES)
    manifest = json.loads(_read(support.PARENT_CATALOG_PINS[0], support.MAX_CATALOG_COMPONENT_BYTES))
    entries = [record for record in manifest["metadata"]["evidence_documents"]
               if record["path"] == MATRIX_SOURCE]
    if len(entries) != 1:
        raise support.WorkingError("the exact inherited matrix source has no unique catalogue byte pin")
    entry = entries[0]
    matrix_pin = support.FilePin(MATRIX_SOURCE, entry["bytes"], entry["sha256"])
    _read(matrix_pin, support.MAX_SOURCE_BYTES)
    _read(SEED, support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    helpers = []
    for name in HELPERS:
        raw = support.bounded_bytes(support.HERE / name, support.MAX_SOURCE_BYTES)
        helpers.append((name, len(raw), sha256(raw).hexdigest()))
    return sha256(support.canonical({
        "matrix_source": [matrix_pin.path, matrix_pin.bytes, matrix_pin.sha256],
        "seed": [SEED.path, SEED.bytes, SEED.sha256],
        "helpers": helpers, "inherited_names": NAMES,
    })).hexdigest()


def _table():
    from peano_lab.library import matrix_rank_finite_coding_candidate as matrix
    if Path(matrix.__file__).resolve() != support.ROOT / MATRIX_SOURCE:
        raise support.WorkingError("the inherited matrix theorem source resolved elsewhere")
    table = {row.name: row for row in THEOREMS}
    for row in matrix.make_matrix_rank_finite_coding_candidate_theorems(TheoremSpec):
        if row.name in table:
            raise support.WorkingError("the selected inherited theorem factories repeat a name")
        table[row.name] = row
    if any(name not in table for name in NAMES):
        raise support.WorkingError("an exact inherited reconstruction target is absent")
    return table


def _exact_seed_position(bundle, table, name):
    row = table[name]
    target = _closed_formula(row.statement)
    premises = tuple(_closed_formula(table[dependency].statement) for dependency in row.dependencies)
    matches = [node.node_id for node in bundle.nodes
               if node.target == target and
               tuple(bundle.nodes[index].target for index in node.dependencies) == premises]
    if len(matches) != 1:
        raise support.WorkingError("the seed lacks one unique exact ordered inherited premise: " + name)
    return matches[0]


def augment(output):
    destination = _destination(output)
    before = _source_binding()
    table = _table()
    old, old_target = support.closure.decode_proof_bundle(
        _read(SEED, support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes).decode("utf-8"))
    if (len(old.nodes) != 210 or old.root != 209
            or tuple(node.node_id for node in old.nodes) != tuple(range(210))):
        raise support.WorkingError("the complete inherited seed inventory changed")
    seed_receipt = support.closure.check_proof_bundle(old, old_target)
    if seed_receipt.node_count != 210 or seed_receipt.kernel_calls != 210:
        raise support.WorkingError("not every original inherited seed body reached HA")
    print("inherited seed: all 210 original HA bodies accepted", flush=True)
    authoring_rss_bytes()

    nodes, rebuilt = list(old.nodes), []
    limits = support.closure.DEFAULT_LAYERED_REPLAY_LIMITS
    for name in NAMES:
        row = table[name]
        target = _closed_formula(row.statement)
        if any(node.target == target for node in old.nodes):
            raise support.WorkingError("a supposedly absent inherited target is already in the pinned seed")
        dependencies = tuple(_exact_seed_position(old, table, dependency) for dependency in row.dependencies)
        body = support.closure._reconstruct_body(row, table)
        occurrences, objects, *_ = support.closure._proof_envelope_metrics_bounded(
            body, max_proof_occurrences=support.closure.MAX_BATCH_PROOF_NODES,
            max_proof_objects=support.closure.MAX_BATCH_PROOF_OBJECTS,
            max_proof_depth=limits.max_body_depth,
            max_annotation_occurrences=limits.max_body_annotation_occurrences,
            max_annotation_depth=limits.max_formula_depth,
            max_envelope_depth=limits.max_body_envelope_depth,
            label="inherited seed body " + name)
        node_id = len(nodes)
        nodes.append(support.closure.BundleNode(node_id, target, dependencies, body))
        rebuilt.append({"name": name, "node_id": node_id, "role": "inherited_alpha_v32",
                        "dependency_names": list(row.dependencies), "dependencies": list(dependencies),
                        "body_nodes": occurrences, "body_objects": objects})
        print("inherited reconstruction: " + name + ": " + str(occurrences) + " nodes", flush=True)

    packaging_dependencies = (old.root, *(record["node_id"] for record in rebuilt))
    target, body = support.closure._packaging_root(tuple(nodes[index].target for index in packaging_dependencies))
    nodes.append(support.closure.BundleNode(len(nodes), target, packaging_dependencies, body))
    bundle = support.closure.ProofBundle(tuple(nodes), len(nodes) - 1)
    if (len(bundle.nodes) != 214 or bundle.root != 213
            or any(new is not original for new, original in zip(bundle.nodes[:210], old.nodes, strict=True))):
        raise support.WorkingError("the original complete seed or exact inherited-only augmentation changed")
    receipt = support.closure.check_proof_bundle(bundle, target)
    if receipt.node_count != 214 or receipt.kernel_calls != 214:
        raise support.WorkingError("not every augmented inherited body reached original HA")
    authoring_rss_bytes()
    payload = support.closure.encode_proof_bundle(bundle, target).encode("utf-8")
    if len(payload) > support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes:
        raise support.WorkingError("the inherited seed exceeds the unchanged canonical payload bound")
    if _source_binding() != before:
        raise support.WorkingError("actual inputs changed during inherited-only proof reconstruction")
    editions = sorted(name for name in sys.modules if name.startswith("peano_lab.library.editions_v"))
    if editions:
        raise support.WorkingError("the source-selected seed unexpectedly imported a full Alpha edition")
    if time.monotonic() - _STARTED > 180 or resource.getrlimit(resource.RLIMIT_CPU) != (170, 175):
        raise support.WorkingError("the inherited authoring window changed its original bounds")
    authoring_rss_bytes()
    _write_exclusive(destination, payload)
    return {
        "schema": "peano-working-polynomial-inherited-seed-authoring-v1",
        "artifact": destination.relative_to(support.ROOT).as_posix(),
        "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
        "original_seed_sha256": SEED.sha256, "original_seed_kernel_calls": seed_receipt.kernel_calls,
        "nodes": receipt.node_count, "edges": receipt.dependency_edges,
        "body_nodes": receipt.total_body_nodes, "whole_augmented_kernel_calls": receipt.kernel_calls,
        "inherited_reconstructed_rows": rebuilt, "original_seed_nodes_retained_unchanged": 210,
        "packaging_dependencies": list(packaging_dependencies), "source_binding": before,
        "all_mathematical_rows_inherited": True, "new_working_theorems": 0,
        "original_ha_checked": True, "independent_lean_checked": False,
        "ordinary_principals_checked": False, "complete_81_inventory_acceptance": False,
        "alpha_editions_imported": editions, "draft_seed_proof_data_only": True,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    report = augment(parser.parse_args(argv).output)
    report.update(seconds=time.monotonic() - _STARTED, peak_rss_bytes=authoring_rss_bytes(),
                  cpu_limits=[170, 175], wall_alarm_seconds=180)
    print(support.canonical(report).decode(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
