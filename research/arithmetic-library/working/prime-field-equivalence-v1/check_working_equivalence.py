#!/usr/bin/env python3
"""Separate current-parent novelty, complete HA/Lean, and ordinary windows.

No saved report is read as acceptance. The final checker requires the full
registered prior113-plus-equivalence inventory and the unchanged original
checker/compiler limits. Partial authoring outputs are not final artifacts.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
from pathlib import Path
import resource
import signal
import time

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import working_equivalence_support as support
from check_constructive_bottom_layers import authoring_rss_bytes
import constructive_bottom_layer_checkpoints as independent
from peano_lab.kernel.checker import check
from peano_lab.library.proof_bundle import decode_proof_bundle, encode_formula
from peano_lab.library.theorems import _closed_formula


CPU_LIMITS, WALL_SECONDS = (170, 175), 180
SLUG = "working-prime-field-equivalence"


@dataclass(frozen=True, slots=True)
class ArtifactPin:
    path: str
    bytes: int
    sha256: str
    nodes: int
    edges: int
    body_nodes: int


# Actual complete original-HA authoring produced these exact bytes. This is
# data identity only; every final invocation executes its original gates.
FINAL_ARTIFACT: ArtifactPin | None = ArtifactPin(
    support.WORKING_RELATIVE + "/artifacts/working-equivalence-proof-bundle-v1.json",
    2449379, "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf",
    377, 1071, 30527,
)


def require_final_inventory():
    pin = FINAL_ARTIFACT
    if (type(pin) is not ArtifactPin
            or any(type(value) is not int or value <= 0 for value in (pin.bytes, pin.nodes, pin.edges, pin.body_nodes))
            or type(pin.path) is not str
            or Path(pin.path).parent != Path(support.WORKING_RELATIVE) / "artifacts"
            or not Path(pin.path).name.startswith("working-equivalence-")
            or not pin.path.endswith(".json") or ".." in Path(pin.path).parts
            or not support._digest(pin.sha256)):
        raise support.EquivalenceError("no actual complete equivalence artifact is registered")
    support._require_spec_pin()
    support.require_preserved_tree()
    support.require_source_registration()
    support.check_pin(support.FilePin(pin.path, pin.bytes, pin.sha256), support.ROOT,
                      support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    return pin


def global_metadata_report():
    state = support.load_candidate_state()
    before = support.state_binding(state)
    selected = support.select_support(state)
    duplicates = support.prior_base.statement_duplicates(state.rows)
    coverage = _seed_coverage(selected, state)
    if support.state_binding(support.load_candidate_state()) != before:
        raise support.EquivalenceError("actual inputs changed during global parsed-statement comparison")
    return {
        "schema": "peano-working-polynomial-equivalence-global-syntax-v1",
        "syntax_only": True, "parent_version": "v32", "parent_count": 3971, "stable_count": 432,
        "prior_non_admitted_working_rows": len(selected.previous_working_names),
        "added_non_admitted_working_rows": len(selected.added_working_names),
        "combined_working_rows": len(selected.owned),
        "inherited_alpha_v32_rows": len(selected.inherited_alpha_names),
        "prior113_reclassified_as_alpha": False,
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
        "prior113_seed_coverage": coverage,
        "original_ha_checked": False, "independent_lean_checked": False,
        "ordinary_principals_checked": False, "source_binding": before,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def _seed_coverage(selected, state):
    """Exact inert target/premise planning, never decoding/checking a proof."""
    pin = support.PRIOR113_ARTIFACT
    value = json.loads(support._read(pin))
    if (type(value) is not list or len(value) != 4 or value[0] != "peano-lab-bundle-v1"
            or type(value[1]) is not int or value[1] != 367
            or type(value[3]) is not list or len(value[3]) != 368):
        raise support.EquivalenceError("the exact old seed has unexpected inert graph metadata")
    nodes = value[3]
    if any(type(node) is not list or len(node) != 4 for node in nodes):
        raise support.EquivalenceError("a seed node has malformed inert metadata")
    added = {row.name for row in state.added_rows}
    wanted = tuple(row for row in selected.complete_specs if row.name not in added)
    table = {row.name: row for row in selected.complete_specs}
    targets = {row.name: support.canonical(encode_formula(_closed_formula(row.statement)))
               for row in selected.complete_specs}
    by_target = {}
    for row in wanted:
        by_target.setdefault(targets[row.name], []).append(row.name)
    encoded = tuple(support.canonical(node[1]) for node in nodes)
    matched = set()
    for index, node in enumerate(nodes):
        if (type(node[2]) is not list
                or any(type(edge) is not int or not 0 <= edge < index for edge in node[2])):
            raise support.EquivalenceError("a seed has malformed inert ordered-premise metadata")
        for name in by_target.get(encoded[index], ()):
            if tuple(encoded[edge] for edge in node[2]) == tuple(targets[dep] for dep in table[name].dependencies):
                matched.add(name)
    support.check_pin(pin, support.ROOT, support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    return {"path": pin.path, "bytes": pin.bytes, "sha256": pin.sha256,
            "inert_nodes": len(nodes), "preexisting_targets": len(wanted),
            "covered_targets": len(matched), "missing_names": sorted({row.name for row in wanted} - matched),
            "raw_json_only": True, "proof_bodies_decoded": False, "original_ha_checked": False,
            "proof_authority": False}


def _load_final():
    pin = require_final_inventory()
    state = support.load_candidate_state()
    before = support.state_binding(state)
    selected = support.select_support(state)
    payload = support.bounded_bytes(support.ROOT / pin.path, pin.bytes)
    if (len(payload), sha256(payload).hexdigest()) != (pin.bytes, pin.sha256):
        raise support.EquivalenceError("registered full proof bytes changed before original decoding")
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    count = support.require_source_registration()
    if (len(selected.owned) != support.PRIOR_WORKING_COUNT + count
            or len(selected.previous_working_names) != support.PRIOR_WORKING_COUNT
            or len(selected.added_working_names) != count or selected.selected.current_support
            or len(bundle.nodes) != pin.nodes or pin.nodes != len(selected.plan.rows) + 1):
        raise support.EquivalenceError("a prefix or altered inventory is not the complete checkpoint")
    return pin, state, selected, before, payload, bundle, target


def _rebind(before):
    if support.state_binding(support.load_candidate_state()) != before:
        raise support.EquivalenceError("actual proof inputs changed during original verification")
    return authoring_rss_bytes()


def verify_complete_bundle():
    pin, state, selected, before, payload, bundle, target = _load_final()
    receipt = support.closure.check_bottom_layer_bundle(selected.frontier, bundle, target)
    if (receipt.node_count != pin.nodes or receipt.dependency_edges != pin.edges
            or receipt.total_body_nodes != pin.body_nodes or receipt.kernel_calls != pin.nodes):
        raise support.EquivalenceError("the complete original HA proof accounting changed")
    checkpoint = independent.Checkpoint(
        SLUG, (), pin.path, pin.bytes, pin.sha256, len(state.rows), support.PRINCIPAL_ROOTS,
        support.WORKING_RELATIVE + "/working-polynomial-equivalence-rfc-v1.md", state.specs_sha256)
    independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)
    return {
        "schema": "peano-working-polynomial-equivalence-bundle-check-v1",
        "combined_working_rows": len(state.rows), "prior_non_admitted_working_rows": support.PRIOR_WORKING_COUNT,
        "added_non_admitted_working_rows": len(state.added_rows),
        "inherited_alpha_v32_rows": len(selected.inherited_alpha_names),
        "prior113_reclassified_as_alpha": False,
        "artifact_sha256": pin.sha256, "nodes": receipt.node_count,
        "edges": receipt.dependency_edges, "body_nodes": receipt.total_body_nodes,
        "kernel_calls": receipt.kernel_calls, "original_ha_checked": True,
        "independent_same_byte_lean_checked": True, "ordinary_principals_checked": False,
        "source_binding": before, "peak_rss_bytes": _rebind(before),
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def verify_principal(name):
    if type(name) is not str or name not in support.PRINCIPAL_ROOTS:
        raise support.EquivalenceError("only the four exact equivalence principals may be replayed")
    pin, state, selected, before, payload, bundle, target = _load_final()
    exact_spec = next(row for row in selected.owned if row.name == name)
    position = next(row.node_id for row in selected.plan.rows if row.name == name)
    del state, payload
    gc.collect()
    proof = support.closure.replay_bottom_layer_theorem(selected.frontier, name, bundle, target)
    del bundle, target
    gc.collect()
    formula = _closed_formula(exact_spec.statement)
    if proof.spec != exact_spec or proof.formula != formula or not check((), proof.certificate, formula):
        raise support.EquivalenceError("the exact ordinary empty-context principal failed original HA")
    return {
        "schema": "peano-working-polynomial-equivalence-principal-check-v1",
        "name": name, "node_id": position, "statement_sha256": sha256(exact_spec.statement.encode()).hexdigest(),
        "artifact_sha256": pin.sha256, "ordinary_certificate_nodes": proof.proof_nodes,
        "complete_ordinary_ha_checked": True, "independent_lean_checked": False,
        "source_binding": before, "peak_rss_bytes": _rebind(before),
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
    elapsed, peak = time.monotonic() - _STARTED, authoring_rss_bytes()
    if elapsed > WALL_SECONDS or resource.getrlimit(resource.RLIMIT_CPU) != CPU_LIMITS:
        raise support.EquivalenceError("the original process resource bounds changed")
    report.update(seconds=elapsed, peak_rss_bytes=peak, cpu_limits=list(CPU_LIMITS), wall_alarm_seconds=WALL_SECONDS)
    print(support.canonical(report).decode(), flush=True)
    return 1 if report.get("duplicate_statements") else 0


if __name__ == "__main__":
    raise SystemExit(main())
