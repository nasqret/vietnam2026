"""Fresh original-HA/compiled-Lean evidence for actual Dirichlet arithmetic.

The three earlier research generations remain non-admitted prerequisites.
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
from constructive_dirichlet_support import ROOT, SupportSelection, select_support, statement_duplicates
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.proof_bundle import CheckedProofBundle, ProofBundle, decode_proof_bundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


SCHEMA = "peano-lab-local-dirichlet-checkpoints-v1"
Checkpoint, ModulePin, CheckpointError = original.Checkpoint, original.ModulePin, original.CheckpointError
LEAN_BINARY_SHA256, LEAN_BINARY_BYTES = original.LEAN_BINARY_SHA256, original.LEAN_BINARY_BYTES
EXPECTED_INVENTORY = (("finite-support", 8), ("dirichlet-convolution", 40),
                      ("dirichlet-fubini", 32), ("dirichlet-units", 25), ("mobius-inversion", 8))
EXPECTED_FAMILIES = {slug for slug, _ in EXPECTED_INVENTORY}

# Register only completed, exactly source-bound proof data. A partially
# populated authoring registry cannot pass the full-tranche gate below.
CHECKPOINTS: tuple[Checkpoint, ...] = (
    Checkpoint(
        "finite-support",
        (ModulePin("signed_finite_support_candidate", "624040e65e0852e652ecda46d2078703e8c0d062dcb06566e24e7d86e9878191"),),
        "research/arithmetic-library/artifacts/dirichlet-finite-support-proof-bundle-v1.json",
        587407, "99d889c64fb066f79247afa4310e0143f42bfffbc2cf56e4bd9be3735e0cac47", 8,
        ("signed_prefix_sum_zero_tail", "signed_prefix_sum_last_value", "signed_prefix_sum_zero_padding_iff"),
        "research/arithmetic-library/signed-finite-support-rfc-v1.md",
        "55874e400c4ecca7dce6e05d5d66e93ef23c091dcf9e8e5ec0a1cc772d9fa5e0",
    ),
    Checkpoint(
        "dirichlet-convolution",
        (ModulePin("dirichlet_convolution_candidate", "cec111fbad76f106a5a3f79e2d78fc2a8d483267baa1b19738d4cbfb0c0fb342"),
         ModulePin("dirichlet_commutativity_candidate", "1408ca915b4c335afc679b617c4189164b6701730746d3a8aa7f2a260bf75e8d")),
        "research/arithmetic-library/artifacts/dirichlet-convolution-proof-bundle-v1.json",
        2756953, "313316e788a10dc281dfb0541a447bad9b7b26bbbd68b1030db89d8d28c5a38b", 40,
        ("dirichlet_convolution_table_exists_extensionally_unique", "dirichlet_convolution_table_commutative",
         "dirichlet_convolution_padded_prefix_iff"),
        "research/arithmetic-library/dirichlet-convolution-rfc-v1.md",
        "8780d9e343234b030e0cd2de518df0ddd9c5c5b4bee89eb00251f770d3ff29ce",
    ),
    Checkpoint(
        "dirichlet-fubini",
        (ModulePin("dirichlet_fubini_candidate", "f18fc61cff3d778568611abebc9698e4c7da9a7dbba37d3b361597dfc988710f"),
         ModulePin("dirichlet_associativity_candidate", "598b0b5658dcba34f97eec4f432de111452ad734a3171832aa2e08bb13a90692")),
        "research/arithmetic-library/artifacts/dirichlet-fubini-proof-bundle-v1.json",
        4455766, "05cb102ae5fb423e325223589eb17b8f1dd0aa8d3cb8419425142f9be087d9f3", 32,
        ("dirichlet_convolution_fubini_interchange", "dirichlet_convolution_associative",
         "dirichlet_convolution_associative_tables_exists"),
        "research/arithmetic-library/dirichlet-fubini-associativity-rfc-v1.md",
        "f00c81c55fe725c7595315fbec8345305bebb3e20f532e6c844c2156fa2fc6cf",
    ),
    Checkpoint(
        "dirichlet-units",
        (ModulePin("dirichlet_units_candidate", "4821a0e7a8ecac28080db207dd96abf4d02a285a85da6d1173b6a1349a82b77c"),),
        "research/arithmetic-library/artifacts/dirichlet-units-proof-bundle-v1.json",
        2158014, "232ddd461eb83d97c1a6255a872be7e970b635ce1d4e958c8bed7706419687b7", 25,
        ("dirichlet_delta_unit_exists", "dirichlet_constant_one_sum_iff",
         "dirichlet_constant_one_realizes_divisor_sum"),
        "research/arithmetic-library/dirichlet-units-rfc-v1.md",
        "954a654694207db14acb799d843520fb12b3ff2233153b07cadb7bb5c7940911",
    ),
    Checkpoint(
        "mobius-inversion",
        (ModulePin("mobius_inversion_candidate", "79309dd26c6f434c2e8bb76858dfada758b4a2b489065403b41c70785e1bf183"),),
        "research/arithmetic-library/artifacts/mobius-inversion-proof-bundle-v1.json",
        6488786, "22e7e61d5d4567df695d67830b465664fbe5a070f0367196e5cfd542ccba5b75", 8,
        ("mobius_inversion_for_actual_mobius_table", "mobius_inversion_arithmetic_tables", "mobius_inversion_iff"),
        "research/arithmetic-library/mobius-inversion-rfc-v1.md",
        "4c40808fd2d52ae3feee2f9ab24039f2ae66aa584327c11f8bb2251cab77ef29",
    ),
)


@dataclass(frozen=True, slots=True)
class DirichletEvidence:
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
        raise CheckpointError("only literal registered Dirichlet checkpoints may be verified")


def _require_complete_inventory():
    if (tuple((item.slug, item.frontier_count) for item in CHECKPOINTS) != EXPECTED_INVENTORY
            or {item.slug for item in CHECKPOINTS} != EXPECTED_FAMILIES):
        raise CheckpointError("all five exact Dirichlet checkpoints must be frozen before the tranche audit")


def load_rows(checkpoint):
    _registered(checkpoint)
    for pin in checkpoint.modules:
        original._source_bytes(pin)
    rows = tuple(row for pin in checkpoint.modules
                 for row in getattr(import_module("peano_lab.library." + pin.module), pin.factory)(TheoremSpec))
    closure._validate_frontier(rows)
    if (len(rows) != checkpoint.frontier_count or not set(checkpoint.principal_roots) <= {row.name for row in rows}
            or closure._specs_digest(rows) != checkpoint.frontier_specs_sha256):
        raise CheckpointError("literal ordered Dirichlet specifications changed")
    return rows


def all_new_rows():
    if not CHECKPOINTS:
        raise CheckpointError("no completed Dirichlet checkpoint has been registered")
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
            "prior_lower_continuation_theorems": list(selected.local_support),
            "current_cross_track_theorems": list(selected.current_support),
            "prior_bottom_layer_count": len(selected.bottom_support),
            "prior_lower_tier_count": len(selected.lower_support),
            "prior_lower_continuation_count": len(selected.local_support),
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
    return DirichletEvidence(checkpoint, selected, bundle, target, receipt, report)


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
        raise CheckpointError("aggregate reports do not describe all five exact Dirichlet checkpoints")
    inversion = reports[-1]
    inversion_principals = inversion["principal_roots"]
    full_inversion = (inversion["bundle"]["original_ha_checked"] is True
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
        "previous_research_theorems": 421, "previous_research_generations": [170, 126, 125],
        "prior_theorem_count_for_exact_ast_novelty_check": 3643,
        "statement_asts_distinct_from_prior_and_within_tranche": True,
        "full_G007_inversion_proved": full_inversion,
        "full_G009_dirichlet_convolution_theory_proved": False,
        "general_G091_prime_power_fields_proved": False,
        "independent_checker": {"binary_sha256": LEAN_BINARY_SHA256, "binary_bytes": LEAN_BINARY_BYTES,
                                "rebuilt_in_this_tranche": False},
        "new_theorems": sum(report["new_theorem_count"] for report in reports), "checkpoints": reports,
    }
