"""Fresh original-HA/compiled-Lean evidence for general Dirichlet inverses.

The four earlier research generations remain non-admitted prerequisites.
Literal source/spec/artifact pins identify inputs; they never replace a
complete proof check. The aggregate requires every exact current family.
"""

from __future__ import annotations

from dataclasses import dataclass
import gc
from hashlib import sha256
from importlib import import_module
from typing import Any

import constructive_bottom_layer_checkpoints as original
from constructive_dirichlet_inverse_support import ROOT, SupportSelection, select_support, statement_duplicates
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.proof_bundle import CheckedProofBundle, ProofBundle, decode_proof_bundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


SCHEMA = "peano-lab-local-dirichlet-inverse-checkpoints-v1"
Checkpoint, ModulePin, CheckpointError = original.Checkpoint, original.ModulePin, original.CheckpointError
LEAN_BINARY_SHA256, LEAN_BINARY_BYTES = original.LEAN_BINARY_SHA256, original.LEAN_BINARY_BYTES
EXPECTED_INVENTORY = (("dirichlet-signed-units", 9), ("dirichlet-triangular", 10),
                      ("dirichlet-inverses", 21))
EXPECTED_FAMILIES = {slug for slug, _ in EXPECTED_INVENTORY}

# Every literal artifact below was produced by actual complete original-HA
# authoring. These pins identify proof data; each verification rechecks it.
CHECKPOINTS: tuple[Checkpoint, ...] = (
    Checkpoint(
        "dirichlet-signed-units",
        (ModulePin("dirichlet_signed_unit_candidate", "263ae0497206cee991e34e08f03df3b1922fc4918e67d4d300887aa1ba7de4df"),),
        "research/arithmetic-library/artifacts/dirichlet-signed-units-proof-bundle-v1.json",
        214864, "5045f1feb2f21a79ecb3cb03f95aaefeb8f01e616a4aa8640cbada3da62ae47b", 9,
        ("dirichlet_signed_unit_product_classification", "dirichlet_signed_unit_affine_solve",
         "dirichlet_signed_unit_affine_unique"),
        "research/arithmetic-library/dirichlet-signed-unit-rfc-v1.md",
        "503e22e4a75aae8b39054144d2d3371f4c8c8f27ac584b18a1383d0e7c9660b7",
    ),
    Checkpoint(
        "dirichlet-triangular",
        (ModulePin("dirichlet_triangular_candidate", "5b6e585a4b2df25dee069ddec17e26cddc52c329d45ee7c5fcf307314b10f8ef"),),
        "research/arithmetic-library/artifacts/dirichlet-triangular-proof-bundle-v1.json",
        1488366, "d2d1b032400b46679658f6b196272df3e0869378a651e711e1b7985778e121e1", 10,
        ("dirichlet_convolution_first_input_append_step", "dirichlet_convolution_at_one_iff",
         "dirichlet_convolution_strict_prefix_exists"),
        "research/arithmetic-library/dirichlet-triangular-rfc-v1.md",
        "a91a79108e1a636bfdd78a67e3426d33edb2e493be1d43f379aef367db743733",
    ),
    Checkpoint(
        "dirichlet-inverses",
        (ModulePin("dirichlet_inverse_candidate", "05347563a82486859a49539e99055504720cc823e14b310389e1d90766a85379"),),
        "research/arithmetic-library/artifacts/dirichlet-inverses-proof-bundle-v1.json",
        7257507, "420f08dcb5c67a260a28f391bdaa5b1f75464c73dc174fbe5cdcd4d08336c826", 21,
        ("dirichlet_unit_equation_construct", "dirichlet_inverse_criterion",
         "dirichlet_inverse_exists_positive_unique"),
        "research/arithmetic-library/dirichlet-inverse-rfc-v1.md",
        "6ccb0ee24d871bffbdedb3100445411ec03cd1d515586f5b63fa9d4780bfdf20",
    ),
)


@dataclass(frozen=True, slots=True)
class DirichletInverseEvidence:
    checkpoint: Checkpoint
    selection: SupportSelection
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    report: dict[str, Any]

    @property
    def owned(self):
        return self.selection.owned

    @property
    def plan(self):
        return self.selection.plan


def _registered(checkpoint):
    if type(checkpoint) is not Checkpoint or checkpoint not in CHECKPOINTS:
        raise CheckpointError("only literal registered Dirichlet-inverse checkpoints may be verified")


def _require_complete_inventory():
    if (tuple((item.slug, item.frontier_count) for item in CHECKPOINTS) != EXPECTED_INVENTORY
            or {item.slug for item in CHECKPOINTS} != EXPECTED_FAMILIES):
        raise CheckpointError("all three exact Dirichlet-inverse checkpoints must be frozen before the tranche audit")


def load_rows(checkpoint):
    _registered(checkpoint)
    for pin in checkpoint.modules:
        original._source_bytes(pin)
    rows = tuple(row for pin in checkpoint.modules
                 for row in getattr(import_module("peano_lab.library." + pin.module), pin.factory)(TheoremSpec))
    closure._validate_frontier(rows)
    if (len(rows) != checkpoint.frontier_count or not set(checkpoint.principal_roots) <= {row.name for row in rows}
            or closure._specs_digest(rows) != checkpoint.frontier_specs_sha256):
        raise CheckpointError("literal ordered Dirichlet-inverse specifications changed")
    return rows


def all_new_rows():
    if not CHECKPOINTS:
        raise CheckpointError("no completed Dirichlet-inverse checkpoint has been registered")
    return tuple(row for item in CHECKPOINTS for row in load_rows(item))


def verify_checkpoint(checkpoint, *, ordinary_roots=False):
    if type(ordinary_roots) is not bool:
        raise CheckpointError("ordinary_roots must be an explicit Boolean")
    _registered(checkpoint)
    owned = load_rows(checkpoint)
    selected = select_support(all_new_rows(), tuple(row.name for row in owned))
    payload = closure._read_pinned(ROOT / checkpoint.artifact, checkpoint.artifact_bytes, checkpoint.artifact_sha256)
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    receipt = closure.check_bottom_layer_bundle(selected.frontier, bundle, target)
    # The unchanged independent adapter authenticates the real compiled
    # checker and checks a private copy of exactly these already-HA-checked
    # bytes. Neither an imported success flag nor a mutable path is evidence.
    original._lean_check(checkpoint, receipt.node_count, bundle.root, payload)
    positions = {row.name: row.node_id for row in selected.plan.rows}
    by_name = {row.name: row for row in owned}
    roots = []
    for name in checkpoint.principal_roots:
        record = {"name": name, "node_id": positions[name],
                  "statement_sha256": sha256(by_name[name].statement.encode()).hexdigest(),
                  "complete_ordinary_ha_checked": ordinary_roots}
        if ordinary_roots:
            proof = closure.replay_bottom_layer_theorem(selected.frontier, name, bundle, target)
            exact = _closed_formula(by_name[name].statement)
            if proof.spec != by_name[name] or proof.formula != exact or not check((), proof.certificate, exact):
                raise CheckpointError("exact returned empty-context certificate failed original HA")
            record["ordinary_certificate_nodes"] = proof.proof_nodes
            del proof
            gc.collect()
        roots.append(record)
    report = {
        "slug": checkpoint.slug, "membership": "local_non_admitting_checkpoint",
        "admitted_to_alpha": False, "alpha_checked_use": False, "stable_member": False,
        "new_theorem_count": len(owned),
        "ordered_new_names_sha256": sha256("\n".join(row.name for row in owned).encode()).hexdigest(),
        "new_specs_sha256": checkpoint.frontier_specs_sha256,
        "complete_non_alpha_specs_sha256": selected.plan.frontier_specs_sha256,
        "new_theorem_dependency_edges": sum(len(row.dependencies) for row in owned),
        "new_theorem_tactic_commands": sum(len(row.script) for row in owned),
        "sources": [{"path": pin.path, "sha256": pin.sha256, "factory": pin.factory} for pin in checkpoint.modules],
        "rfc": checkpoint.rfc,
        "support": {
            "prior_bottom_layer_theorems": list(selected.bottom_support),
            "prior_lower_tier_theorems": list(selected.lower_support),
            "prior_lower_continuation_theorems": list(selected.continuation_support),
            "prior_dirichlet_theorems": list(selected.dirichlet_support),
            "current_cross_track_theorems": list(selected.current_support),
            "prior_bottom_layer_count": len(selected.bottom_support),
            "prior_lower_tier_count": len(selected.lower_support),
            "prior_lower_continuation_count": len(selected.continuation_support),
            "prior_dirichlet_count": len(selected.dirichlet_support),
            "published_non_admitted_count": len(selected.published_support),
            "local_non_admitted_count": len(selected.local_support),
            "current_cross_track_count": len(selected.current_support),
            "alpha_v30_count": len(selected.plan.rows) - len(selected.frontier),
            "counted_as_new_owned_theorems": False,
        },
        "bundle": {
            "path": checkpoint.artifact, "bytes": checkpoint.artifact_bytes, "sha256": checkpoint.artifact_sha256,
            "nodes_including_packaging_root": receipt.node_count,
            "dependency_edges_including_packaging": receipt.dependency_edges,
            "body_proof_nodes": receipt.total_body_nodes, "packaging_root_id": bundle.root,
            "original_ha_checked": True, "independent_lean_checked": True,
        },
        "all_maximal_owned_roots": list(selected.plan.root_names), "principal_roots": roots,
    }
    return DirichletInverseEvidence(checkpoint, selected, bundle, target, receipt, report)


def verify_principal_root(checkpoint, name):
    """One exact ordinary principal proof in a fresh bounded worker.

    The unchanged replay helper rechecks the complete source-bound bundle
    and every interned body before constructing its ordinary certificate.
    This report makes no Lean claim: a separate family worker performs the
    independent compiled-Lean check of the same authenticated artifact.
    """
    _registered(checkpoint)
    if type(name) is not str or name not in checkpoint.principal_roots:
        raise CheckpointError("only an exact registered principal root may be verified")
    owned = load_rows(checkpoint)
    selected = select_support(all_new_rows(), tuple(row.name for row in owned))
    payload = closure._read_pinned(ROOT / checkpoint.artifact, checkpoint.artifact_bytes, checkpoint.artifact_sha256)
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    spec = next(row for row in owned if row.name == name)
    positions = {row.name: row.node_id for row in selected.plan.rows}
    proof = closure.replay_bottom_layer_theorem(selected.frontier, name, bundle, target)
    exact = _closed_formula(spec.statement)
    if proof.spec != spec or proof.formula != exact or not check((), proof.certificate, exact):
        raise CheckpointError("exact returned empty-context certificate failed original HA")
    record = {"name": name, "node_id": positions[name],
              "statement_sha256": sha256(spec.statement.encode()).hexdigest(),
              "complete_ordinary_ha_checked": True,
              "ordinary_certificate_nodes": proof.proof_nodes}
    return {"slug": checkpoint.slug, "bundle_sha256": checkpoint.artifact_sha256,
            "principal_roots": [record]}


def verify_all(*, ordinary_roots=True):
    if type(ordinary_roots) is not bool:
        raise CheckpointError("ordinary_roots must be an explicit Boolean")
    _require_complete_inventory()
    rows = all_new_rows()
    duplicates = statement_duplicates(rows)
    if duplicates:
        raise CheckpointError(f"new rows duplicate existing statements: {duplicates!r}")
    reports = []
    for checkpoint in CHECKPOINTS:
        evidence = verify_checkpoint(checkpoint, ordinary_roots=ordinary_roots)
        reports.append(evidence.report)
        del evidence
        gc.collect()
    return _aggregate_reports(reports)


def _aggregate_reports(reports):
    """Format freshly checked reports; never an alternative proof verifier.

    Both callers perform every real proof check and exact whole-tranche
    novelty first: verify_all in-process, or the bounded fresh-worker CLI.
    No saved JSON receipt is an accepted authority input.
    """
    _require_complete_inventory()
    if tuple((report["slug"], report["new_theorem_count"]) for report in reports) != EXPECTED_INVENTORY:
        raise CheckpointError("aggregate reports do not describe all three exact Dirichlet-inverse checkpoints")
    inversion = reports[-1]
    inversion_principals = inversion["principal_roots"]
    general_inverse = (inversion["bundle"]["original_ha_checked"] is True
                      and inversion["bundle"]["independent_lean_checked"] is True
                      and tuple(root["name"] for root in inversion_principals) == CHECKPOINTS[-1].principal_roots
                      and bool(inversion_principals)
                      and all(root["complete_ordinary_ha_checked"] is True
                              and type(root.get("ordinary_certificate_nodes")) is int
                              and root["ordinary_certificate_nodes"] > 1 for root in inversion_principals))
    return {
        "schema": SCHEMA, "proof_authority": "fresh_original_ha_and_independent_compiled_lean_checks",
        "stored_receipt_is_proof_authority": False, "published": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "parent": {"version": "v30", "catalog": closure.PARENT_CATALOG,
                   "catalog_sha256": closure.PARENT_CATALOG_SHA256, "alpha_checked_use_count": 3222, "stable_count": 432},
        "previous_research_theorems": 534, "previous_research_generations": [170, 126, 125, 113],
        "prior_theorem_count_for_exact_ast_novelty_check": 3756,
        "statement_asts_distinct_from_prior_and_within_tranche": True,
        "general_dirichlet_inverse_criterion_proved": general_inverse,
        "full_G009_dirichlet_convolution_theory_proved": False,
        "general_G091_prime_power_fields_proved": False,
        "independent_checker": {"binary_sha256": LEAN_BINARY_SHA256, "binary_bytes": LEAN_BINARY_BYTES,
                                "rebuilt_in_this_tranche": False},
        "new_theorems": sum(report["new_theorem_count"] for report in reports), "checkpoints": reports,
    }
