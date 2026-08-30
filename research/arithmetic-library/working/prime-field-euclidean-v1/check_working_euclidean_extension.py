#!/usr/bin/env python3
"""Separate, original-bound working113 syntax and genuine proof windows.

No phase consumes a stored success. Final proof phases require one registered
complete artifact, exact source-ordered targets and dependencies, every-body
original HA, and either same-byte compiled Lean or a separately materialized
ordinary empty-context principal. This script cannot admit or publish rows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gc
from hashlib import sha256
from pathlib import Path
import re
import resource
import signal
import time

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import working_euclidean_extension_support as support
from check_constructive_bottom_layers import authoring_rss_bytes
import constructive_bottom_layer_checkpoints as independent
from peano_lab.kernel.checker import check
from peano_lab.library.proof_bundle import decode_proof_bundle
from peano_lab.library.theorems import _closed_formula


CPU_LIMITS, WALL_SECONDS = (170, 175), 180
SLUG = "working-prime-field-euclidean-extension"


@dataclass(frozen=True, slots=True)
class ArtifactPin:
    path: str
    bytes: int
    sha256: str
    nodes: int
    edges: int
    body_nodes: int


# Actual complete source-bound original-HA authoring produced these bytes.
# This registration is data identity only; every final invocation still runs
# the original complete checker and its requested independent proof gate.
FINAL_ARTIFACT: ArtifactPin | None = ArtifactPin(
    support.WORKING_RELATIVE + "/artifacts/working-euclidean-extension-proof-bundle-v1.json",
    2219445, "c2e097f0e04c4b4f01bb219102405d0e93bc847c19625113eb48e55c7900734d",
    368, 1033, 29292,
)


def require_final_inventory():
    pin = FINAL_ARTIFACT
    if (type(pin) is not ArtifactPin
            or any(type(value) is not int or value <= 0 for value in (pin.bytes, pin.nodes, pin.edges, pin.body_nodes))
            or type(pin.path) is not str
            or Path(pin.path).parent != Path(support.WORKING_RELATIVE) / "artifacts"
            or not Path(pin.path).name.startswith("working-euclidean-extension-")
            or not pin.path.endswith(".json") or ".." in Path(pin.path).parts
            or type(pin.sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", pin.sha256) is None):
        raise support.ExtensionError("no actual complete working113 artifact is registered")
    support._require_spec_pin()
    support.require_preserved81()
    support.require_extension_sources()
    support.check_pin(support.FilePin(pin.path, pin.bytes, pin.sha256), support.ROOT,
                      support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    return pin


def global_metadata_report():
    state = support.load_candidate_state()
    before = support.state_binding(state)
    selected = support.select_support(state)
    duplicates = support.base.statement_duplicates(state.rows)
    if support.state_binding(support.load_candidate_state()) != before:
        raise support.ExtensionError("exact inputs changed during the actual113/3971 syntax comparison")
    return {
        "schema": "peano-working-polynomial-euclidean-extension-global-syntax-v1",
        "syntax_only": True, "parent_version": "v32", "parent_count": 3971, "stable_count": 432,
        "prior_working_rows": len(selected.previous_working_names),
        "added_working_rows": len(selected.added_working_names),
        "combined_working_rows": len(selected.owned),
        "inherited_alpha_v32_rows": len(selected.inherited_alpha_names),
        "prior_working_rows_reclassified_as_alpha": False,
        "complete_theorem_count": len(selected.complete_specs),
        "prospective_bundle_nodes_including_packaging": len(selected.plan.rows) + 1,
        "complete_dependency_edges": selected.plan.dependency_edge_count,
        "prospective_bundle_edges_including_packaging": selected.plan.dependency_edge_count + len(selected.plan.root_names),
        "maximal_working_roots": list(selected.plan.root_names),
        "ordered_complete_names_sha256": selected.plan.ordered_names_sha256,
        "combined_specs_sha256": state.specs_sha256,
        "execution_frontier_rows": len(selected.frontier),
        "execution_frontier_specs_sha256": selected.plan.frontier_specs_sha256,
        "inherited_alpha_v32_names": list(selected.inherited_alpha_names),
        "duplicate_statements": [list(pair) for pair in duplicates],
        "global_current3971_novelty_checked": True,
        "original_ha_checked": False, "independent_lean_checked": False,
        "ordinary_principals_checked": False, "source_binding": before,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def _load_final():
    pin = require_final_inventory()
    state = support.load_candidate_state()
    before = support.state_binding(state)
    selected = support.select_support(state)
    payload = support.bounded_bytes(support.ROOT / pin.path, pin.bytes)
    if (len(payload), sha256(payload).hexdigest()) != (pin.bytes, pin.sha256):
        raise support.ExtensionError("registered complete113 proof bytes changed before decoding")
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    if (len(selected.owned) != 113 or len(selected.previous_working_names) != 81
            or len(selected.added_working_names) != 32 or selected.selected.current_support
            or len(bundle.nodes) != pin.nodes or pin.nodes != len(selected.plan.rows) + 1):
        raise support.ExtensionError("a prefix or altered inventory is not the complete113 checkpoint")
    return pin, state, selected, before, payload, bundle, target


def _rebind(before):
    if support.state_binding(support.load_candidate_state()) != before:
        raise support.ExtensionError("actual proof inputs changed during complete original verification")
    return authoring_rss_bytes()


def verify_complete_bundle():
    pin, state, selected, before, payload, bundle, target = _load_final()
    receipt = support.closure.check_bottom_layer_bundle(selected.frontier, bundle, target)
    if (receipt.node_count != pin.nodes or receipt.dependency_edges != pin.edges
            or receipt.total_body_nodes != pin.body_nodes or receipt.kernel_calls != pin.nodes):
        raise support.ExtensionError("the complete113 original-HA accounting changed")
    checkpoint = independent.Checkpoint(
        SLUG, (), pin.path, pin.bytes, pin.sha256, 113, support.PRINCIPAL_ROOTS,
        support.WORKING_RELATIVE + "/working-euclidean-extension-rfc-v1.md", state.specs_sha256)
    independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)
    peak = _rebind(before)
    return {
        "schema": "peano-working-polynomial-euclidean-extension-bundle-check-v1",
        "combined_working_rows": 113, "prior_working_rows": 81, "added_working_rows": 32,
        "inherited_alpha_v32_rows": len(selected.inherited_alpha_names),
        "prior_working_rows_reclassified_as_alpha": False,
        "artifact_sha256": pin.sha256, "nodes": receipt.node_count,
        "edges": receipt.dependency_edges, "body_nodes": receipt.total_body_nodes,
        "kernel_calls": receipt.kernel_calls, "original_ha_checked": True,
        "independent_same_byte_lean_checked": True, "ordinary_principals_checked": False,
        "source_binding": before, "peak_rss_bytes": peak,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def verify_principal(name):
    if type(name) is not str or name not in support.PRINCIPAL_ROOTS:
        raise support.ExtensionError("only four exact extension principals may be replayed")
    pin, state, selected, before, payload, bundle, target = _load_final()
    exact_spec = next(row for row in selected.owned if row.name == name)
    position = next(row.node_id for row in selected.plan.rows if row.name == name)
    del state, payload
    gc.collect()
    # The unchanged replay first checks every body in the full combined
    # artifact, then materializes and checks the selected ordinary theorem.
    proof = support.closure.replay_bottom_layer_theorem(selected.frontier, name, bundle, target)
    del bundle, target
    gc.collect()
    formula = _closed_formula(exact_spec.statement)
    if proof.spec != exact_spec or proof.formula != formula or not check((), proof.certificate, formula):
        raise support.ExtensionError("the exact ordinary empty-context extension principal failed HA")
    peak = _rebind(before)
    return {
        "schema": "peano-working-polynomial-euclidean-extension-principal-check-v1",
        "name": name, "node_id": position, "statement_sha256": sha256(exact_spec.statement.encode()).hexdigest(),
        "artifact_sha256": pin.sha256, "ordinary_certificate_nodes": proof.proof_nodes,
        "complete_ordinary_ha_checked": True, "independent_lean_checked": False,
        "source_binding": before, "peak_rss_bytes": peak,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("local", "metadata", "bundle", "root"), required=True)
    parser.add_argument("--name", choices=support.PRINCIPAL_ROOTS)
    args = parser.parse_args(argv)
    if (args.task == "root") != (args.name is not None):
        parser.error("--name is required only for a separate ordinary-root window")
    if args.task == "local":
        report = support.local_manifest()
    elif args.task == "metadata":
        report = global_metadata_report()
    elif args.task == "bundle":
        report = verify_complete_bundle()
    else:
        report = verify_principal(args.name)
    elapsed = time.monotonic() - _STARTED
    peak = authoring_rss_bytes()
    if elapsed > WALL_SECONDS or resource.getrlimit(resource.RLIMIT_CPU) != CPU_LIMITS:
        raise support.ExtensionError("the original proof-window resource bounds changed")
    report.update(seconds=elapsed, peak_rss_bytes=peak, cpu_limits=list(CPU_LIMITS), wall_alarm_seconds=WALL_SECONDS)
    print(support.canonical(report).decode(), flush=True)
    return 1 if report.get("duplicate_statements") else 0


if __name__ == "__main__":
    raise SystemExit(main())
