#!/usr/bin/env python3
"""Working-only syntax diagnostics and separate original proof windows.

Local/metadata phases confer no proof authority. A final bundle or principal
phase requires literal complete registration, actual every-body original HA,
and (for the bundle phase) the unchanged compiled Lean checker on the exact
same payload. No saved audit, partial prefix, or synthetic capability is read.
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
import sys
import time

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import working_euclidean_support as support
from check_constructive_bottom_layers import authoring_rss_bytes
import constructive_bottom_layer_checkpoints as independent
from peano_lab.kernel.checker import check
from peano_lab.library.proof_bundle import decode_proof_bundle
from peano_lab.library.theorems import _closed_formula


CPU_LIMITS, WALL_SECONDS = (170, 175), 180
SLUG = "working-prime-field-euclidean"


@dataclass(frozen=True, slots=True)
class ArtifactPin:
    path: str
    bytes: int
    sha256: str
    nodes: int
    edges: int
    body_nodes: int


# Actual complete every-body HA authoring output. This byte registration is
# not acceptance of independent Lean or any ordinary principal; those gates
# below always execute again against these exact bytes.
FINAL_ARTIFACT: ArtifactPin | None = ArtifactPin(
    support.WORKING_RELATIVE + "/artifacts/working-prime-field-euclidean-proof-bundle-v1.json",
    1635441, "3614e9504b84cfd24a52780d54ddc9eb16e49bf2df996c99664c9427e9a9fd83",
    314, 822, 21794,
)


def global_metadata_report():
    state = support.load_candidate_state()
    before = support.state_binding(state)
    selected = support.select_support(state.rows, tuple(row.name for row in state.rows))
    duplicates = support.statement_duplicates(state.rows)
    if support.state_binding(support.load_candidate_state()) != before:
        raise support.WorkingError("exact inputs changed during the actual syntax diagnostic")
    return {
        "schema": "peano-working-polynomial-euclidean-global-syntax-v1",
        "syntax_only": True, "parent_version": "v32", "parent_count": 3971, "stable_count": 432,
        "new_rows": len(selected.owned), "inherited_alpha_v32_rows": len(selected.parent_support),
        "inherited_rows_counted_as_new": False,
        "complete_theorem_count": len(selected.complete_specs),
        "prospective_bundle_nodes_including_packaging": len(selected.plan.rows) + 1,
        "complete_dependency_edges": selected.plan.dependency_edge_count,
        "maximal_roots": list(selected.plan.root_names),
        "ordered_complete_names_sha256": selected.plan.ordered_names_sha256,
        "new_specs_sha256": state.specs_sha256,
        "execution_frontier_rows": len(selected.frontier),
        "execution_frontier_specs_sha256": selected.plan.frontier_specs_sha256,
        "inherited_alpha_v32_names": list(selected.parent_support),
        "duplicate_statements": [list(pair) for pair in duplicates],
        "global_current_parent_novelty_checked": True,
        "whole_original_ha_checked": False, "independent_lean_checked": False,
        "ordinary_principals_checked": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def require_final_inventory():
    pin = FINAL_ARTIFACT
    if (type(pin) is not ArtifactPin
            or any(type(value) is not int or value <= 0 for value in (
                pin.bytes, pin.nodes, pin.edges, pin.body_nodes))
            or type(pin.path) is not str
            or Path(pin.path).parent != Path(support.WORKING_RELATIVE) / "artifacts"
            or not pin.path.endswith(".json") or ".." in Path(pin.path).parts
            or type(pin.sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", pin.sha256) is None):
        raise support.WorkingError("no actual complete 81-row working artifact is registered")
    support.require_final_registration()
    support.check_pin(support.FilePin(pin.path, pin.bytes, pin.sha256), support.ROOT,
                      support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    return pin


def _load_final():
    pin = require_final_inventory()
    state = support.load_candidate_state(final=True)
    before = support.state_binding(state, final=True)
    selected = support.select_support(state.rows, tuple(row.name for row in state.rows))
    payload = support.bounded_bytes(support.ROOT / pin.path, pin.bytes)
    if len(payload) != pin.bytes or sha256(payload).hexdigest() != pin.sha256:
        raise support.WorkingError("the final proof bytes changed before decoding")
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    if len(selected.owned) != 81 or selected.current_support or len(bundle.nodes) != pin.nodes:
        raise support.WorkingError("a partial authoring prefix is not a complete working checkpoint")
    return pin, state, selected, before, payload, bundle, target


def _rebind(before):
    if support.state_binding(support.load_candidate_state(final=True), final=True) != before:
        raise support.WorkingError("actual proof inputs changed during original verification")
    return authoring_rss_bytes()


def verify_complete_bundle():
    pin, state, selected, before, payload, bundle, target = _load_final()
    receipt = support.closure.check_bottom_layer_bundle(selected.frontier, bundle, target)
    if (receipt.node_count != pin.nodes or receipt.dependency_edges != pin.edges
            or receipt.total_body_nodes != pin.body_nodes or receipt.kernel_calls != pin.nodes
            or pin.nodes != len(selected.plan.rows) + 1):
        raise support.WorkingError("the exact whole-bundle HA accounting changed")
    checkpoint = independent.Checkpoint(
        SLUG, (), pin.path, pin.bytes, pin.sha256, 81, support.PRINCIPAL_ROOTS,
        support.WORKING_RELATIVE + "/working-euclidean-integration-rfc-v1.md", state.specs_sha256)
    independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)
    peak = _rebind(before)
    return {
        "schema": "peano-working-polynomial-euclidean-bundle-check-v1",
        "new_rows": 81, "parent_version": "v32", "parent_count": 3971, "stable_count": 432,
        "artifact_sha256": pin.sha256, "nodes": receipt.node_count,
        "edges": receipt.dependency_edges, "body_nodes": receipt.total_body_nodes,
        "kernel_calls": receipt.kernel_calls, "original_ha_checked": True,
        "independent_same_byte_lean_checked": True, "ordinary_principals_checked": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "peak_rss_bytes": peak,
    }


def verify_principal(name):
    if type(name) is not str or name not in support.PRINCIPAL_ROOTS:
        raise support.WorkingError("only an exact working principal may be replayed")
    pin, state, selected, before, payload, bundle, target = _load_final()
    exact_spec = next(row for row in selected.owned if row.name == name)
    position = next(row.node_id for row in selected.plan.rows if row.name == name)
    del state, payload
    gc.collect()
    # This unchanged function first checks every actual complete-bundle body,
    # then compiles and checks the exact ordinary empty-context target.
    proof = support.closure.replay_bottom_layer_theorem(selected.frontier, name, bundle, target)
    del bundle, target
    gc.collect()
    formula = _closed_formula(exact_spec.statement)
    if proof.spec != exact_spec or proof.formula != formula or not check((), proof.certificate, formula):
        raise support.WorkingError("the exact ordinary empty-context principal failed original HA")
    peak = _rebind(before)
    return {
        "schema": "peano-working-polynomial-euclidean-principal-check-v1",
        "name": name, "node_id": position, "statement_sha256": sha256(exact_spec.statement.encode()).hexdigest(),
        "artifact_sha256": pin.sha256, "ordinary_certificate_nodes": proof.proof_nodes,
        "complete_ordinary_ha_checked": True, "independent_lean_checked": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "peak_rss_bytes": peak,
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
        raise support.WorkingError("the original diagnostic/proof process bounds changed")
    report.update(seconds=elapsed, peak_rss_bytes=peak, cpu_limits=list(CPU_LIMITS), wall_alarm_seconds=WALL_SECONDS)
    print(support.canonical(report).decode(), flush=True)
    return 1 if report.get("duplicate_statements") else 0


if __name__ == "__main__":
    raise SystemExit(main())
