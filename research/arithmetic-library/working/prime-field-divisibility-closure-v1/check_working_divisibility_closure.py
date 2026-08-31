#!/usr/bin/env python3
"""Thirteen separate gates: current4092 novelty, full HA/Lean, eleven ordinary roots.

Actual bytes and original functions are checked anew, with unchanged limits.
Only metadata loads the full current catalogue. No receipt or observation
is accepted as proof authority, and no task performs Alpha/Stable admission.
Formal right-divisibility transitivity is one exact ordinary target;
this checkpoint makes no gcd/Bezout or complete-G091 claim.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gc
from hashlib import sha256
import resource
import signal
import time

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import working_divisibility_closure_support as support
import constructive_bottom_layer_checkpoints as independent
from check_constructive_bottom_layers import authoring_rss_bytes
from peano_lab.kernel.checker import check
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.proof_bundle import decode_proof_bundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula

CPU_LIMITS, WALL_SECONDS = (170, 175), 180
SLUG = "working-polynomial-divisibility-closure"


@dataclass(frozen=True, slots=True)
class ArtifactPin:
    path: str
    bytes: int
    sha256: str
    nodes: int
    edges: int
    body_nodes: int


# Actual complete candidate bytes from two successful original-HA stages.
# This data pin grants no acceptance: all thirteen fresh final windows remain
# mandatory after this actual registration and source/test freeze.
FINAL_ARTIFACT: ArtifactPin | None = ArtifactPin(
    support.WORKING_RELATIVE + "/artifacts/working-divisibility-closure-prefix-44-proof-bundle-v1.json",
    1757906, "6fb92e887c2ddd604e71574095fdf492814af9651e15f0b36386be3538b1a7e7",
    293, 846, 24049)


def _resources():
    support._require(resource.getrlimit(resource.RLIMIT_CPU) == CPU_LIMITS
                     and time.monotonic() - _STARTED <= WALL_SECONDS,
                     "the original proof/metadata CPU and wall bounds changed")
    return authoring_rss_bytes()


def require_final_inventory():
    pin = FINAL_ARTIFACT
    support._require(type(pin) is ArtifactPin,
                     "no actual complete44 artifact is registered")
    support._require(all(type(value) is int and value > 0
                         for value in (pin.bytes, pin.nodes, pin.edges, pin.body_nodes))
                     and pin.bytes <= support.MAX_BYTES and pin.nodes == 293 and pin.edges == 846
                     and support._safe_relative(pin.path)
                     and support.ROOT / pin.path == support.stage_path(44)
                     and support._digest(pin.sha256),
                     "an incomplete, foreign, or malformed artifact cannot be the final checkpoint")
    support.require_parent_registration()
    support.require_working_sources()
    support.check_pin(support.FilePin(pin.path, pin.bytes, pin.sha256), support.ROOT, support.MAX_BYTES)
    return pin


def _novelty_pairs(new_rows, parent_rows):
    """Compare actual parsed core ASTs, including new/new duplicate pairs."""
    indexed, duplicates = {}, []
    for row in new_rows:
        encoded = FormulaArena().freeze(_closed_formula(row.statement)).to_json()
        key = sha256(encoded.encode()).digest()
        duplicates.extend((row.name, name) for name, other in indexed.get(key, ()) if encoded == other)
        indexed.setdefault(key, []).append((row.name, encoded))
    for row in parent_rows:
        encoded = FormulaArena().freeze(_closed_formula(row.statement)).to_json()
        duplicates.extend((name, row.name) for name, other in indexed.get(sha256(encoded.encode()).digest(), ())
                          if encoded == other)
    return tuple(duplicates)


def global_metadata_report():
    artifact = require_final_inventory()
    state = support.load_candidate_state()
    before = support.state_binding(state, final=True)
    selected = support.select_support(state)
    from peano_catalog_shards_v33 import load_catalog
    pin = support.PARENT_CATALOG_PINS[0]
    catalog = load_catalog(support.ROOT / pin.path, expected_sha256=pin.sha256)
    support._require(catalog.get("schema") == "peano-library-alpha-snapshot-v33"
                     and catalog.get("theorem_count") == catalog.get("checked_use_count") == 4092
                     and catalog.get("stable_count") == 432
                     and catalog.get("edition_identity_sha256") == support.PARENT_IDENTITY_SHA256
                     and catalog.get("ordered_enrollment_root_sha256") == support.PARENT_ENROLLMENT_SHA256
                     and type(catalog.get("theorems")) is list and len(catalog["theorems"]) == 4092,
                     "novelty requires the exact actual current4092 checked catalogue")
    parent_rows = tuple(TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]),
                                   tuple(row["script"]), row["summary"]) for row in catalog["theorems"])
    parent = {row.name: row for row in parent_rows}
    support._require(len(parent) == 4092 and not parent.keys() & {row.name for row in state.rows}
                     and all(parent.get(row.name) == row for row in selected.support),
                     "working ownership or exact inherited source specifications differ from current Alpha")
    del catalog, parent
    gc.collect()
    duplicates = _novelty_pairs(state.rows, parent_rows)
    seeds = support.seed_inventory(support.required_seed_paths(44), through=44)
    coverage = support.seed_coverage(selected, seeds)
    support._require(not coverage["missing_names"], "the literal real seeds lost inherited coverage")
    support._require(support.state_binding(support.load_candidate_state(), final=True) == before,
                     "actual inputs changed during full parsed-AST novelty checking")
    return {
        "schema": "peano-working-divisibility-closure-global-syntax-v1", "syntax_only": True,
        "parent_version": "v33", "parent_count": 4092, "stable_count": 432,
        "non_admitted_rows": 44, "previous_non_admitted_rows": 37, "additional_non_admitted_rows": 7,
        "artifact_sha256": artifact.sha256, "inherited_alpha_v33_rows": len(selected.support),
        "complete_source_rows": len(selected.complete_specs), "specs_sha256": state.specs_sha256,
        "duplicate_statements": [list(pair) for pair in duplicates],
        "global_current4092_novelty_checked": True, "novel": not duplicates,
        "exact_current_parent_source_cone_checked": True, "seed_coverage": coverage,
        "source_binding": before, "original_ha_checked": False, "independent_lean_checked": False,
        "ordinary_principals_checked": False, "associativity_proved": False,
        "complete_checkpoint_acceptance": False,
        "gcd_bezout_proved": False, "full_G091_proved": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "peak_rss_bytes": _rebind(before),
    }


def _load_final():
    pin = require_final_inventory()
    state = support.load_candidate_state()
    before = support.state_binding(state, final=True)
    execution = support.execution_selection(state)
    payload = support.read_pin(support.FilePin(pin.path, pin.bytes, pin.sha256))
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    support._require(len(execution.source.owned) == 44 and len(execution.source.support) == 248
                     and len(execution.source.complete_specs) == 292
                     and execution.source.root_names == support.PRINCIPAL_ROOTS
                     and len(bundle.nodes) == pin.nodes == len(execution.plan.rows) + 1
                     and bundle.root == pin.nodes - 1,
                     "a draft prefix is not the complete292-theorem checkpoint")
    return pin, state, execution, before, payload, bundle, target


def _rebind(before):
    require_final_inventory()
    support._require(support.state_binding(support.load_candidate_state(), final=True) == before,
                     "actual proof sources changed during original verification")
    return _resources()


def verify_complete_bundle():
    pin, state, execution, before, payload, bundle, target = _load_final()
    receipt = support.closure.check_bottom_layer_bundle(execution.frontier, bundle, target)
    support._require(receipt.node_count == pin.nodes and receipt.kernel_calls == pin.nodes
                     and receipt.dependency_edges == pin.edges and receipt.total_body_nodes == pin.body_nodes,
                     "not every exact original body/premise has the registered proof accounting")
    checkpoint = independent.Checkpoint(
        SLUG, (), pin.path, pin.bytes, pin.sha256, len(state.rows), support.PRINCIPAL_ROOTS,
        support.WORKING_RELATIVE + "/working-divisibility-closure-rfc-v1.md", state.specs_sha256)
    # The unchanged transport validates its original pinned binary and feeds
    # the very same authenticated payload to compiled Lean, never a pathname.
    independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)
    return {
        "schema": "peano-working-divisibility-closure-bundle-check-v1",
        "non_admitted_rows": 44, "inherited_canonical_source_rows": 248,
        "artifact_sha256": pin.sha256, "nodes": receipt.node_count, "edges": receipt.dependency_edges,
        "body_nodes": receipt.total_body_nodes, "kernel_calls": receipt.kernel_calls,
        "original_ha_checked": True, "independent_same_byte_lean_checked": True,
        "ordinary_principals_checked": False, "global_current4092_novelty_checked": False,
        "source_binding": before, "peak_rss_bytes": _rebind(before),
        "complete_checkpoint_acceptance": False, "gcd_bezout_proved": False, "full_G091_proved": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def verify_principal(name):
    support._require(type(name) is str and name in support.PRINCIPAL_ROOTS,
                     "only the eleven exact maximal ordinary principals may be replayed")
    pin, state, execution, before, payload, bundle, target = _load_final()
    exact = next(row for row in state.rows if row.name == name)
    position = next(row.node_id for row in execution.plan.rows if row.name == name)
    del state, payload
    gc.collect()
    proof = support.closure.replay_bottom_layer_theorem(execution.frontier, name, bundle, target)
    del bundle, target
    gc.collect()
    formula = _closed_formula(exact.statement)
    support._require(proof.spec == exact and proof.formula == formula
                     and check((), proof.certificate, formula),
                     "the exact ordinary empty-context certificate failed original HA")
    return {
        "schema": "peano-working-divisibility-closure-principal-check-v1", "name": name, "node_id": position,
        "statement_sha256": sha256(exact.statement.encode()).hexdigest(),
        "artifact_sha256": pin.sha256, "ordinary_certificate_nodes": proof.proof_nodes,
        "complete_ordinary_ha_checked": True, "independent_lean_checked": False,
        "right_divisibility_transitivity_ordinary_checked": name == support.PRINCIPAL_ROOTS[-1],
        "source_binding": before, "peak_rss_bytes": _rebind(before),
        "complete_checkpoint_acceptance": False, "gcd_bezout_proved": False, "full_G091_proved": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("local", "metadata", "bundle", "root"), required=True)
    parser.add_argument("--name", choices=support.PRINCIPAL_ROOTS)
    args = parser.parse_args(argv)
    if (args.task == "root") != (args.name is not None):
        parser.error("--name is required only for a separate ordinary principal window")
    if args.task == "local":
        report = support.local_manifest()
    elif args.task == "metadata":
        report = global_metadata_report()
    elif args.task == "bundle":
        report = verify_complete_bundle()
    else:
        report = verify_principal(args.name)
    report.update(seconds=time.monotonic() - _STARTED, peak_rss_bytes=_resources(),
                  cpu_limits=list(CPU_LIMITS), wall_alarm_seconds=WALL_SECONDS)
    print(support.canonical(report).decode(), flush=True)
    return 1 if report.get("duplicate_statements") else 0


if __name__ == "__main__":
    raise SystemExit(main())
