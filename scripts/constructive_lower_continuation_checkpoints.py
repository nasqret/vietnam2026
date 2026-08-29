"""Fresh exact HA/compiled-Lean evidence for the next lower-layer proofs.

All prior research rows remain real non-admitted proof support. No source pin,
saved report or success flag substitutes for checking every complete body.
"""

from __future__ import annotations

from dataclasses import dataclass
import gc
from hashlib import sha256
from importlib import import_module
from typing import Any

import constructive_bottom_layer_checkpoints as original
from constructive_lower_continuation_support import ROOT, SupportSelection, select_support, statement_duplicates
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.proof_bundle import CheckedProofBundle, ProofBundle, decode_proof_bundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


SCHEMA = "peano-lab-local-lower-continuation-checkpoints-v1"
Checkpoint, ModulePin, CheckpointError = original.Checkpoint, original.ModulePin, original.CheckpointError
LEAN_BINARY_SHA256, LEAN_BINARY_BYTES = original.LEAN_BINARY_SHA256, original.LEAN_BINARY_BYTES
EXPECTED_FAMILIES = {"divisor-involutions", "mobius-divisor-cancellation", "rectangular-sums", "polynomial-products"}

# Add only fully closed artifacts. Incomplete authoring modules are not a
# registered checkpoint and cannot acquire a verified display label.
CHECKPOINTS: tuple[Checkpoint, ...] = (
    Checkpoint(
        "divisor-involutions",
        (ModulePin("divisor_involution_candidate", "67297015bcfbeb16b9090f537a2771d5c3cbfa4000d5c83c90cd0ba16cb15be7"),),
        "research/arithmetic-library/artifacts/lower-continuation-divisor-involutions-proof-bundle-v1.json",
        292245, "deffb1e384e64cd2cb56b4c1603a0fdde7578cec15e80618f5b06197fabf6fed", 12,
        ("positive_divisor_quotient_exists_unique", "positive_divisor_involution_exists", "divisor_complement_prefix_involution"),
        "research/arithmetic-library/divisor-involution-rfc-v1.md",
        "c15344f6e8ca8335116cea82dec586421c75f66ff0e9badb06858fda12aee0c6",
    ),
    Checkpoint(
        "mobius-divisor-cancellation",
        (ModulePin("mobius_divisor_cancellation_candidate", "9af47fd019e5899586cb02c0e124579d82c4b65d093cfc73d721f411130b457f"),),
        "research/arithmetic-library/artifacts/lower-continuation-mobius-divisor-cancellation-proof-bundle-v1.json",
        2498683, "f858f6bd9e09d6ec33b48689b385222153ad9d326eccb8239ac5776b39955542", 28,
        ("mobius_divisor_sum_cancellation", "mobius_divisor_sum_cancellation_exists", "mobius_divisor_sum_cancellation_on_positive_values"),
        "research/arithmetic-library/mobius-divisor-cancellation-rfc-v1.md",
        "a305d44cc8c8e1274fc7832efb571bacc872ee84cb5f2538fd41cb65c7edfc3b",
    ),
    Checkpoint(
        "rectangular-sums",
        (ModulePin("signed_rectangular_slice_candidate", "d676600c931936ff00996209c7d744c269427eaf08611fb625e471f608861e5e"),
         ModulePin("signed_rectangular_sums_candidate", "0ce96c5155bb7bf47f5ae2b8151631bd981263f7d05c25f6ec8b3cd365d7a26e")),
        "research/arithmetic-library/artifacts/lower-continuation-rectangular-sums-proof-bundle-v1.json",
        2151122, "a6f62d8a0c89431b3596a0d15278643da6981afe166107cdc6aefa5433485395", 32,
        ("signed_rectangular_slice_exists_extensionally_unique", "signed_rectangular_fubini", "signed_rectangular_row_major_fubini"),
        "research/arithmetic-library/signed-rectangular-sums-rfc-v1.md",
        "3f774e07d82400c19850521fae1779bc363aff5e56bb32cbc1042a5d3dd4403d",
    ),
    Checkpoint(
        "polynomial-products",
        (ModulePin("prime_field_polynomial_convolution_candidate", "20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24"),
         ModulePin("prime_field_polynomial_degree_candidate", "3419cefca1f8e4b130a7c8935218815153eaf9865fe1eeed89118ced8bf339e5")),
        "research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json",
        745307, "55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3", 53,
        ("prime_field_polynomial_convolution_exists_unique", "prime_field_polynomial_convolution_outside_zero",
         "prime_field_polynomial_convolution_represented_degree_exists"),
        "research/arithmetic-library/prime-field-polynomial-convolution-rfc-v1.md",
        "4ee9ff43d58fac794947ac67349efd966b78472b2f9777c16fe222e5ca194eaa",
    ),
)


@dataclass(frozen=True, slots=True)
class ContinuationEvidence:
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
        raise CheckpointError("only literal registered continuation checkpoints may be verified")


def load_rows(checkpoint):
    _registered(checkpoint)
    for pin in checkpoint.modules:
        original._source_bytes(pin)
    rows = tuple(row for pin in checkpoint.modules
                 for row in getattr(import_module("peano_lab.library." + pin.module), pin.factory)(TheoremSpec))
    closure._validate_frontier(rows)
    if (len(rows) != checkpoint.frontier_count or not set(checkpoint.principal_roots) <= {row.name for row in rows}
            or closure._specs_digest(rows) != checkpoint.frontier_specs_sha256):
        raise CheckpointError("literal ordered continuation specifications changed")
    return rows


def all_new_rows():
    if not CHECKPOINTS:
        raise CheckpointError("no completed continuation checkpoint has been registered")
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
    # Exact authenticated bytes, privately snapshotted by the unchanged
    # independently compiled verifier adapter; never a racy mutable pathname.
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
            "current_cross_track_theorems": list(selected.current_support),
            "prior_bottom_layer_count": len(selected.bottom_support),
            "prior_lower_tier_count": len(selected.lower_support),
            "published_non_admitted_count": len(selected.published_support),
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
    return ContinuationEvidence(checkpoint, selected, bundle, target, receipt, report)


def verify_all(*, ordinary_roots=True):
    if type(ordinary_roots) is not bool:
        raise CheckpointError("ordinary_roots must be an explicit Boolean")
    if (tuple(item.slug for item in CHECKPOINTS) != (
            "divisor-involutions", "mobius-divisor-cancellation", "rectangular-sums", "polynomial-products")
            or {item.slug for item in CHECKPOINTS} != EXPECTED_FAMILIES):
        raise CheckpointError("all four exact continuation checkpoints must be frozen before the tranche audit")
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
    """Format already checked reports; this helper does not verify proofs.

    The in-process verifier calls it after actual proof checks. The bounded
    CLI calls it only after fresh, authenticated worker checks and the exact
    whole-tranche novelty check. No saved receipt is an accepted input path.
    """
    return {
        "schema": SCHEMA, "proof_authority": "fresh_original_ha_and_independent_compiled_lean_checks",
        "stored_receipt_is_proof_authority": False, "published": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "parent": {"version": "v30", "catalog": closure.PARENT_CATALOG,
                   "catalog_sha256": closure.PARENT_CATALOG_SHA256, "alpha_checked_use_count": 3222, "stable_count": 432},
        "previous_research_theorems": 296, "previous_research_generations": [170, 126],
        "prior_theorem_count_for_exact_ast_novelty_check": 3518,
        "statement_asts_distinct_from_prior_and_within_tranche": True,
        "full_G007_inversion_proved": False, "general_G091_prime_power_fields_proved": False,
        "independent_checker": {"binary_sha256": LEAN_BINARY_SHA256, "binary_bytes": LEAN_BINARY_BYTES,
                                "rebuilt_in_this_tranche": False},
        "new_theorems": sum(report["new_theorem_count"] for report in reports), "checkpoints": reports,
    }
