"""Fresh, dependency-closed evidence for the next local research tranche.

Old research checkpoints remain non-admitted support.  Only actual original
HA and pinned independently compiled Lean checks authorize verified labels;
stored records and source digests do not.  No edition or kernel is changed.
"""

from __future__ import annotations

from dataclasses import dataclass
import gc
from hashlib import sha256
from importlib import import_module
from typing import Any

import constructive_bottom_layer_checkpoints as previous
from constructive_lower_tier_support import ROOT, SupportSelection, select_support, statement_duplicates
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.proof_bundle import CheckedProofBundle, ProofBundle, decode_proof_bundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


SCHEMA = "peano-lab-local-lower-tier-checkpoints-v1"
Checkpoint = previous.Checkpoint
ModulePin = previous.ModulePin
CheckpointError = previous.CheckpointError
LEAN_BINARY_SHA256 = previous.LEAN_BINARY_SHA256
LEAN_BINARY_BYTES = previous.LEAN_BINARY_BYTES

# Exact mathematical sources and complete closed artifacts, not authoring
# placeholders.  The reused dataclass's frontier_count/specs fields describe
# this chapter's owned rows; SupportSelection separately closes inherited
# non-Alpha rows and records their distinct roles.
CHECKPOINTS: tuple[Checkpoint, ...] = (
    Checkpoint(
        "divisor-sums",
        (
            ModulePin("arithmetic_table_extension_candidate", "d39d08f7178b526daad51aaf4a75c325f567424bb8ae74906c030f4d72e9e294"),
            ModulePin("mobius_table_candidate", "7631337dd93f4a65e6f74ce9a5129d6701a496aa49969764c0945f4248676fc4"),
            ModulePin("divisor_mask_candidate", "740efabb5cbf6e0c804e901dae423e319c52c86f605ebe2a4ad0bffb033d9543"),
        ),
        "research/arithmetic-library/artifacts/lower-tier-divisor-sums-proof-bundle-v1.json",
        1_841_261, "96740bcedad194ebed5066ae03fa20cd922e702ae925b2c85f4ed45649aa0307", 37,
        ("mobius_table_exists", "signed_divisor_sum_positive_source_extensional", "signed_divisor_sum_exists_unique"),
        "research/arithmetic-library/mobius-tables-divisor-sums-rfc-v1.md",
        "9bfd07e098154dd119b767459f69f8670151b4acd5c3ab0fc3813a987b704870",
    ),
    Checkpoint(
        "signed-weighted-sums",
        (
            ModulePin("signed_table_operations_candidate", "465e623dbe3fcac0eb70ca72e890d1cc8046b3a476014dc65d187b3f30f4893f"),
            ModulePin("signed_sum_linearity_candidate", "8da9d92ec3e204583e7539fc2ff6ca7af5677a909a59831951e978deab9d69c0"),
            ModulePin("signed_weighted_sum_candidate", "2cbbb6486f0a75bbf97165018ef7539dd90c8a06317d0ed037ed95afcc72db07"),
        ),
        "research/arithmetic-library/artifacts/lower-tier-signed-weighted-sums-proof-bundle-v1.json",
        2_293_317, "e88ddec495a71d673e670299ea3943a5a996eecb1296fb746e107c8e0b81c967", 40,
        ("signed_weighted_sum_exists_unique", "signed_weighted_sum_scalar_linearity", "signed_weighted_sum_add_linearity"),
        "research/arithmetic-library/signed-weighted-sums-rfc-v1.md",
        "d1e23134d7f367d169f181c67939df5548101c83e9a73da43544c49e96590fae",
    ),
    Checkpoint(
        "prime-field-polynomials",
        (
            ModulePin("prime_field_polynomial_candidate", "644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72"),
            ModulePin("prime_field_polynomial_evaluation_candidate", "9638337f69bdc1f5491255b767dc90042244402e34ceab84902b0481c2eab802"),
        ),
        "research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json",
        688_987, "6e3a08c73b8a45de127e6d50a771f95b52fd54894b1c2e43468751421488a01a", 49,
        ("prime_field_polynomial_horner_exists_unique", "prime_field_polynomial_normalized_horner_iff", "prime_field_polynomial_reduce_and_evaluate_exists"),
        "research/arithmetic-library/prime-field-polynomials-rfc-v1.md",
        "0ff662d165003510ed2cd20d724762d9d4166e62cd67e361073e7e15bc5fcd8b",
    ),
)


@dataclass(frozen=True, slots=True)
class LowerTierEvidence:
    checkpoint: Checkpoint
    selection: SupportSelection
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    report: dict[str, Any]

    @property
    def owned(self) -> tuple[TheoremSpec, ...]:
        return self.selection.owned

    @property
    def plan(self) -> closure.BottomLayerPlan:
        return self.selection.plan


def _registered(checkpoint: Checkpoint) -> None:
    if type(checkpoint) is not Checkpoint or checkpoint not in CHECKPOINTS:
        raise CheckpointError("only literal registered lower-tier checkpoints may be verified")


def load_rows(checkpoint: Checkpoint) -> tuple[TheoremSpec, ...]:
    """Authenticate complete factory output, not merely its source filename."""
    _registered(checkpoint)
    for pin in checkpoint.modules:
        previous._source_bytes(pin)
    rows = tuple(row for pin in checkpoint.modules
                 for row in getattr(import_module("peano_lab.library." + pin.module), pin.factory)(TheoremSpec))
    closure._validate_frontier(rows)
    if (len(rows) != checkpoint.frontier_count
            or not set(checkpoint.principal_roots) <= {row.name for row in rows}
            or closure._specs_digest(rows) != checkpoint.frontier_specs_sha256):
        raise CheckpointError("the literal ordered lower-tier theorem specifications changed")
    return rows


def all_new_rows() -> tuple[TheoremSpec, ...]:
    if not CHECKPOINTS:
        raise CheckpointError("no completed lower-tier checkpoint has been registered")
    return tuple(row for item in CHECKPOINTS for row in load_rows(item))


def verify_checkpoint(checkpoint: Checkpoint, *, ordinary_roots: bool = False) -> LowerTierEvidence:
    """Check every body in the exact cone, including non-Alpha prerequisites."""
    if type(ordinary_roots) is not bool:
        raise CheckpointError("ordinary_roots must be an explicit Boolean")
    _registered(checkpoint)
    owned = load_rows(checkpoint)
    selection = select_support(all_new_rows(), tuple(row.name for row in owned))
    payload = closure._read_pinned(ROOT / checkpoint.artifact,
                                   checkpoint.artifact_bytes, checkpoint.artifact_sha256)
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    receipt = closure.check_bottom_layer_bundle(selection.frontier, bundle, target)
    # Reuse the already audited byte-exact independent checker adapter.  It
    # receives the same immutable authenticated payload that HA just checked,
    # through a private snapshot rather than a racy mutable original path.
    previous._lean_check(checkpoint, receipt.node_count, bundle.root, payload)
    positions = {row.name: row.node_id for row in selection.plan.rows}
    by_name = {row.name: row for row in owned}
    roots = []
    for name in checkpoint.principal_roots:
        record: dict[str, Any] = {
            "name": name, "node_id": positions[name],
            "statement_sha256": sha256(by_name[name].statement.encode()).hexdigest(),
            "complete_ordinary_ha_checked": ordinary_roots,
        }
        if ordinary_roots:
            checked = closure.replay_bottom_layer_theorem(selection.frontier, name, bundle, target)
            exact = _closed_formula(by_name[name].statement)
            if (checked.spec != by_name[name] or checked.formula != exact
                    or not check((), checked.certificate, exact)):
                raise CheckpointError("the exact returned empty-context certificate failed original HA")
            record["ordinary_certificate_nodes"] = checked.proof_nodes
        roots.append(record)
    report = {
        "slug": checkpoint.slug, "membership": "local_non_admitting_checkpoint",
        "admitted_to_alpha": False, "alpha_checked_use": False, "stable_member": False,
        "new_theorem_count": len(owned),
        "ordered_new_names_sha256": sha256("\n".join(row.name for row in owned).encode()).hexdigest(),
        "new_specs_sha256": checkpoint.frontier_specs_sha256,
        "complete_non_alpha_specs_sha256": selection.plan.frontier_specs_sha256,
        "new_theorem_dependency_edges": sum(len(row.dependencies) for row in owned),
        "new_theorem_tactic_commands": sum(len(row.script) for row in owned),
        "sources": [{"path": pin.path, "sha256": pin.sha256, "factory": pin.factory}
                    for pin in checkpoint.modules],
        "rfc": checkpoint.rfc,
        "support": {
            "published_non_admitted_theorems": list(selection.published_support),
            "current_cross_track_theorems": list(selection.current_support),
            "published_non_admitted_count": len(selection.published_support),
            "current_cross_track_count": len(selection.current_support),
            "alpha_v30_count": len(selection.plan.rows) - len(selection.frontier),
            "counted_as_new_owned_theorems": False,
        },
        "bundle": {
            "path": checkpoint.artifact, "bytes": checkpoint.artifact_bytes,
            "sha256": checkpoint.artifact_sha256,
            "nodes_including_packaging_root": receipt.node_count,
            "dependency_edges_including_packaging": receipt.dependency_edges,
            "body_proof_nodes": receipt.total_body_nodes,
            "packaging_root_id": bundle.root,
            "original_ha_checked": True, "independent_lean_checked": True,
        },
        "all_maximal_owned_roots": list(selection.plan.root_names),
        "principal_roots": roots,
    }
    return LowerTierEvidence(checkpoint, selection, bundle, target, receipt, report)


def verify_all(*, ordinary_roots: bool = True) -> dict[str, Any]:
    if type(ordinary_roots) is not bool:
        raise CheckpointError("ordinary_roots must be an explicit Boolean")
    rows = all_new_rows()  # Also fails closed before an unfinished inventory.
    duplicates = statement_duplicates(rows)
    if duplicates:
        raise CheckpointError(f"new rows duplicate already represented statements: {duplicates!r}")
    reports = []
    for checkpoint in CHECKPOINTS:
        evidence = verify_checkpoint(checkpoint, ordinary_roots=ordinary_roots)
        reports.append(evidence.report)
        del evidence
        gc.collect()
    return {
        "schema": SCHEMA,
        "proof_authority": "fresh_original_ha_and_independent_compiled_lean_checks",
        "stored_receipt_is_proof_authority": False,
        "published": False, "alpha_admission_performed": False, "stable_admission_performed": False,
        "parent": {
            "version": "v30", "catalog": closure.PARENT_CATALOG,
            "catalog_sha256": closure.PARENT_CATALOG_SHA256,
            "alpha_checked_use_count": closure.PARENT_COUNT, "stable_count": 432,
        },
        "previous_research_theorems": 170,
        "prior_theorem_count_for_exact_ast_novelty_check": 3392,
        "statement_asts_distinct_from_prior_and_within_tranche": True,
        "previous_research_membership": "published_non_admitted_checkpoints",
        "previous_research_audit": "research/arithmetic-library/artifacts/bottom-layer-checkpoints-v2.json",
        "independent_checker": {
            "binary_sha256": LEAN_BINARY_SHA256, "binary_bytes": LEAN_BINARY_BYTES,
            "rebuilt_in_this_tranche": False,
        },
        "new_theorems": sum(row["new_theorem_count"] for row in reports),
        "checkpoints": reports,
    }


__all__ = (
    "CHECKPOINTS", "Checkpoint", "CheckpointError", "LEAN_BINARY_BYTES", "LEAN_BINARY_SHA256",
    "LowerTierEvidence", "ModulePin", "ROOT", "SCHEMA", "all_new_rows", "load_rows",
    "verify_all", "verify_checkpoint",
)
