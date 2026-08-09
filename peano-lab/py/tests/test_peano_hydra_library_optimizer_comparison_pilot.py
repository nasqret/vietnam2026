"""Focused adversarial contracts for the bounded Hydra A2.3a pilot.

The tests in this file deliberately exercise the small, pure proof-recovery
and comparison surfaces.  They must not build the three production layered
certificates; those builds belong on CI/WMI after the pilot's trust boundary
has been reviewed.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.engine.state import proof_resource_metrics  # noqa: E402
from peano_lab.kernel.artifact_codec import (  # noqa: E402
    encode_artifact_bounded,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check  # noqa: E402
from peano_lab.kernel.formulas import Eq, Imp  # noqa: E402
from peano_lab.kernel.proofs import Cut, EqRefl, EqTrans, Hyp, ImpIntro  # noqa: E402
from peano_lab.kernel.terms import Succ, Zero  # noqa: E402
import peano_lab.library.layered_replay as layered  # noqa: E402
import training.peano_hydra.library_optimizer_comparison_pilot as pilot  # noqa: E402


CLI_PATH = (
    ROOT / "scripts" / "build_peano_hydra_library_optimizer_comparison_pilot.py"
)
SCHEMA_PATH = (
    ROOT
    / "training"
    / "peano_hydra"
    / "library-optimizer-comparison-pilot-schema-v1.json"
)
RETAINED_A21 = ROOT / "artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json"
RETAINED_A22 = (
    ROOT / "artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json"
)
REPLAY_MANIFEST = ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1/manifest.json"
REPLAY_REPORT = ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"

EXPECTED_ROOTS = (
    (256, "odd_add_odd"),
    (376, "finite_bounded_injective_surjective"),
    (379, "beta_product_swap_last_invariant"),
)
EXPECTED_CANDIDATE_KINDS = (
    "retained-replay",
    "a2.2-direct-cut-rebuild",
    "layered-closure",
)
COMPARISON_METRICS = (
    "artifact_bytes",
    "proof_nodes",
    "proof_depth",
    "cut_nodes",
)
HISTORICAL_SHA256 = {
    RETAINED_A21: "4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040",
    RETAINED_A22: "6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182",
    REPLAY_MANIFEST: "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604",
    REPLAY_REPORT: "35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10",
}


class _DigestLike:
    def __str__(self) -> str:
        return "a" * 64


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_hash(value: object) -> str:
    return _sha(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _body_receipt(body, target, dependency_count: int) -> dict[str, object]:
    nodes, depth, objects, edges, reused = proof_resource_metrics(body)
    result: dict[str, object] = {
        "certificate_representation": "peano-lab-v2-encoded-proof",
        "certificate_sha256": _sha(encode_proof(body)),
        "dependency_count": dependency_count,
        "kernel_accepted": True,
        "metrics": {
            "proof_depth": depth,
            "proof_edges": edges,
            "proof_nodes": nodes,
            "proof_objects": objects,
            "reused_objects": reused,
        },
        "target_formula_sha256": _sha(encode_formula(target)),
    }
    result["receipt_sha256"] = _canonical_hash(result)
    return result


def _candidate(
    candidate_id: str,
    *,
    order: int,
    values: tuple[int, int, int, int],
    artifact_sha256: str | None = None,
) -> dict[str, object]:
    return {
        "artifact_sha256": artifact_sha256 or _sha(candidate_id.encode("utf-8")),
        "candidate_id": candidate_id,
        "candidate_kind_order": order,
        "metrics": dict(zip(COMPARISON_METRICS, values, strict=True)),
    }


def _load_cli():
    specification = importlib.util.spec_from_file_location(
        "_test_peano_hydra_optimizer_comparison_cli", CLI_PATH
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _producer_source_state() -> dict[str, object]:
    files = []
    for relative in pilot.PRODUCER_SOURCE_FILES:
        raw = (ROOT / relative).read_bytes()
        files.append(
            {
                "bytes": len(raw),
                "path": relative.as_posix(),
                "sha256": _sha(raw),
            }
        )
    body = {
        "commit_sha1": "0" * 40,
        "files": files,
        "format": pilot.PRODUCER_SOURCE_STATE_FORMAT,
        "git_verified": False,
        "tree_sha1": "1" * 40,
        "v": 1,
    }
    preimage = {
        "format": pilot.PRODUCER_SOURCE_STATE_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    return {
        **body,
        "root_preimage": preimage,
        "root_sha256": pilot._sha256_json(preimage, limit=pilot.MAX_SCHEMA_BYTES),
    }


def test_schema_fixes_exact_roots_candidate_universe_metrics_and_claim_boundary() -> None:
    raw = SCHEMA_PATH.read_bytes()
    schema = pilot.optimizer_comparison_pilot_schema()
    assert raw == pilot.canonical_document_bytes(schema, limit=pilot.MAX_SCHEMA_BYTES)
    assert tuple((row["index"], row["name"]) for row in schema["required_theorems"]) == (
        EXPECTED_ROOTS
    )
    assert tuple(schema["constants"]["comparison_metrics"]) == COMPARISON_METRICS
    assert schema["constants"]["candidate_count_per_theorem"] == 3
    assert schema["algorithm"]["candidate_universe"] == [
        {
            "candidate_id": "retained-replay",
            "candidate_kind_order": 0,
            "construction": "exact retained replay-pack artifact",
        },
        {
            "candidate_id": "a2.2-direct-cut-rebuild",
            "candidate_kind_order": 1,
            "construction": "exact A2.2 rebuilt direct-Cut artifact",
        },
        {
            "candidate_id": "layered-closure",
            "candidate_kind_order": 2,
            "construction": (
                "fresh layered-closure artifact compiled from recovered modular bodies"
            ),
        },
    ]
    assert schema["claim_boundary"]["comparison"].startswith(
        "only canonical artifact bytes and intrinsic proof-tree"
    )
    assert "Python identity/alias metrics are excluded" in schema["claim_boundary"][
        "comparison"
    ]
    identity = pilot.optimizer_comparison_pilot_schema_identity()
    assert identity["artifact_sha256"] == _sha(raw)
    assert identity["sha256"] == pilot.OPTIMIZER_COMPARISON_PILOT_SCHEMA_SHA256
    fuel_contract = schema["algorithm"]["artifact_fuel"]
    assert "proof_nodes" in fuel_contract
    assert "8" in fuel_contract
    assert "16" in fuel_contract
    assert schema["emitted_document_contract"]["artifact_metrics"]["types"] == {
        "artifact_bytes": "positive-integer",
        "cut_nodes": "nonnegative-integer",
        "proof_depth": "positive-integer",
        "proof_nodes": "positive-integer",
    }
    common_types = schema["emitted_document_contract"]["artifact_common"]["types"]
    assert common_types["candidate_id"] == "registered-safe-ascii-nonempty-string"
    assert common_types["candidate_kind_order"] == "nonnegative-integer"


def test_schema_loader_rejects_semantically_equal_noncanonical_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = json.loads(SCHEMA_PATH.read_bytes())
    compact = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert compact != pilot.canonical_document_bytes(value, limit=pilot.MAX_SCHEMA_BYTES)
    original = pilot._safe_file

    def substitute(path: Path, *, label: str, limit: int) -> bytes:
        if path == pilot.OPTIMIZER_COMPARISON_PILOT_SCHEMA_PATH:
            return compact
        return original(path, label=label, limit=limit)

    monkeypatch.setattr(pilot, "_safe_file", substitute)
    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="canonical",
    ):
        pilot.optimizer_comparison_pilot_schema()


def test_public_surface_has_no_publish_admit_or_best_known_entrypoint() -> None:
    assert set(pilot.__all__) == {
        "LibraryOptimizerComparisonPilotError",
        "RecoveredModularBody",
        "build_candidate_optimizer_comparison_pilot",
        "canonical_document_bytes",
        "componentwise_nondominated",
        "load_optimizer_comparison_pilot",
        "optimizer_comparison_pilot_schema",
        "optimizer_comparison_pilot_schema_identity",
        "recover_curried_modular_body",
        "select_pilot_representative",
        "validate_optimizer_comparison_pilot",
    }
    assert not any(
        fragment in name
        for name in pilot.__all__
        for fragment in ("publish", "admit", "freeze", "best_known", "minimal")
    )


def test_fresh_process_import_has_exact_origin_and_no_campaign_side_effects() -> None:
    code = r'''
from pathlib import Path
import sys
import training.peano_hydra.library_optimizer_comparison_pilot as pilot
expected = Path(sys.argv[1]).resolve(strict=True)
if Path(pilot.__file__).resolve(strict=True) != expected:
    raise SystemExit("optimizer module origin drifted")
for value in (
    pilot.RecoveredModularBody,
    pilot.componentwise_nondominated,
    pilot.recover_curried_modular_body,
):
    if value.__module__ != "training.peano_hydra.library_optimizer_comparison_pilot":
        raise SystemExit(f"public value origin drifted: {value!r}")
forbidden = [
    name for name in sys.modules
    if "quadratic_reciprocity_stack" in name
    or name.rsplit(".", 1)[-1].endswith("_candidate")
]
if forbidden:
    raise SystemExit(repr(sorted(forbidden)))
'''
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(ROOT / "peano-lab" / "py"), str(ROOT))
    )
    module_path = ROOT / "training/peano_hydra/library_optimizer_comparison_pilot.py"
    completed = subprocess.run(
        [sys.executable, "-c", code, str(module_path)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_producer_source_state_is_exact_live_and_explicitly_not_git_verified() -> None:
    source_state = _producer_source_state()
    validated = pilot._validate_producer_source_state(source_state, root=ROOT)
    assert validated == source_state
    assert validated["git_verified"] is False
    assert [row["path"] for row in validated["files"]] == [
        path.as_posix() for path in pilot.PRODUCER_SOURCE_FILES
    ]


@pytest.mark.parametrize(
    "mutate",
    (
        lambda value: value.__setitem__("git_verified", True),
        lambda value: value.__setitem__("unexpected", False),
        lambda value: value["files"][0].__setitem__("sha256", "0" * 64),
        lambda value: value["files"][0].__setitem__("bytes", 1),
        lambda value: value["files"].reverse(),
        lambda value: value.__setitem__("root_sha256", "0" * 64),
    ),
)
def test_producer_source_state_mutations_fail_closed(mutate) -> None:
    value = _producer_source_state()
    mutate(value)
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError):
        pilot._validate_producer_source_state(value, root=ROOT)


def test_recovery_peels_exact_direct_cut_and_hashes_final_curried_body() -> None:
    zero = Zero()
    one = Succ(zero)
    target = Eq(zero, zero)
    dependency_target = Eq(one, one)
    dependency_proof = EqRefl(one)

    # The residual body intentionally starts with a Cut.  Recovery must peel
    # exactly the named outer spine, not reject or accidentally peel this
    # tactic-generated internal Cut.
    residual = Cut(target, target, EqRefl(zero), Hyp(0))
    closed = Cut(dependency_target, target, dependency_proof, residual)
    curried = ImpIntro(residual)
    curried_target = Imp(dependency_target, target)
    receipt = _body_receipt(curried, curried_target, 1)
    assert check((), closed, target)
    assert check((), curried, curried_target)

    recovered = pilot.recover_curried_modular_body(
        name="fixture",
        target=target,
        proof=closed,
        dependencies=("dependency",),
        dependency_targets={"dependency": dependency_target},
        dependency_proof_sha256={"dependency": _sha(encode_proof(dependency_proof))},
        expected_body_receipt=receipt,
    )

    assert type(recovered) is pilot.RecoveredModularBody
    assert recovered.target == target
    assert recovered.dependencies == ("dependency",)
    assert recovered.curried_target == curried_target
    assert encode_proof(recovered.body) == encode_proof(curried)
    assert recovered.receipt == receipt
    assert recovered.receipt["certificate_sha256"] == _sha(encode_proof(curried))
    assert recovered.receipt["certificate_sha256"] != _sha(encode_proof(residual))


def test_recovery_treats_source_alias_metrics_as_nontransportable_observations() -> None:
    zero = Zero()
    one = Succ(zero)
    target = Eq(zero, zero)
    dependency_target = Eq(one, one)
    dependency_proof = EqRefl(one)
    residual = Cut(target, target, EqRefl(zero), Hyp(0))
    closed = Cut(dependency_target, target, dependency_proof, residual)
    curried = ImpIntro(residual)
    curried_target = Imp(dependency_target, target)
    source_receipt = _body_receipt(curried, curried_target, 1)

    # Artifact transport preserves the proof tree and its encoding, not Python
    # object aliases.  These two observation fields may therefore differ after
    # decode even though every transport-stable receipt is exact.
    source_receipt["metrics"]["proof_objects"] -= 1
    source_receipt["metrics"]["reused_objects"] += 1
    source_receipt["receipt_sha256"] = _canonical_hash(
        {
            key: value
            for key, value in source_receipt.items()
            if key != "receipt_sha256"
        }
    )

    recovered = pilot.recover_curried_modular_body(
        name="alias-erasure-fixture",
        target=target,
        proof=closed,
        dependencies=("dependency",),
        dependency_targets={"dependency": dependency_target},
        dependency_proof_sha256={"dependency": _sha(encode_proof(dependency_proof))},
        expected_body_receipt=source_receipt,
    )
    assert recovered.receipt["certificate_sha256"] == source_receipt[
        "certificate_sha256"
    ]
    assert recovered.receipt == source_receipt
    assert recovered.receipt["metrics"]["proof_objects"] == 3
    assert recovered.receipt["metrics"]["reused_objects"] == 1


def test_recovery_accepts_real_shared_subtree_after_artifact_erases_aliases() -> None:
    zero = Zero()
    target = Eq(zero, zero)
    shared = EqRefl(zero)
    source_body = EqTrans(shared, shared)
    source_receipt = _body_receipt(source_body, target, 0)
    assert source_receipt["metrics"] == {
        "proof_depth": 2,
        "proof_edges": 2,
        "proof_nodes": 3,
        "proof_objects": 2,
        "reused_objects": 1,
    }
    raw = encode_artifact_bounded(
        40, target, source_body, max_bytes=pilot.MAX_ARTIFACT_BYTES
    )
    _fuel, decoded_target, decoded_body = pilot.decode_artifact(
        raw,
        max_bytes=pilot.MAX_ARTIFACT_BYTES,
        max_nodes=100,
        max_depth=32,
    )
    assert proof_resource_metrics(decoded_body) == (3, 2, 3, 2, 0)
    assert encode_proof(decoded_body) == encode_proof(source_body)

    recovered = pilot.recover_curried_modular_body(
        name="shared-subtree-fixture",
        target=decoded_target,
        proof=decoded_body,
        dependencies=(),
        dependency_targets={},
        dependency_proof_sha256={},
        expected_body_receipt=source_receipt,
    )
    assert recovered.receipt == source_receipt
    assert proof_resource_metrics(recovered.body) == (3, 2, 3, 2, 0)


def test_rebuild_artifact_is_decode_reencode_and_empty_context_checked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zero = Zero()
    target = Eq(zero, zero)
    proof = EqRefl(zero)
    fuel = 24
    raw = encode_artifact_bounded(
        fuel, target, proof, max_bytes=pilot.MAX_ARTIFACT_BYTES
    )
    tree = pilot.proof_tree_metrics(proof)
    row = {
        "name": "fixture",
        "rebuilt_certificate": {
            "artifact_base64": base64.b64encode(raw).decode("ascii"),
            "artifact_bytes": len(raw),
            "artifact_sha256": _sha(raw),
            "fuel": fuel,
            "packed_tree_metrics": tree,
            "proof_term_sha256": _sha(encode_proof(proof)),
        },
    }
    replay_row = {"formula_sha256": _sha(encode_formula(target))}

    decoded_raw, decoded_fuel, decoded_target, decoded_proof = (
        pilot._decode_rebuild_artifact(row, replay_row=replay_row)
    )
    assert decoded_raw == raw
    assert decoded_fuel == fuel
    assert decoded_target == target
    assert encode_proof(decoded_proof) == encode_proof(proof)
    assert check((), decoded_proof, target)

    monkeypatch.setattr(pilot, "check", lambda *_args: False)
    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="failed exact replay",
    ):
        pilot._decode_rebuild_artifact(row, replay_row=replay_row)


def _receipt_route_fixture() -> tuple[dict[str, object], dict[str, object]]:
    zero = Zero()
    initial_body = ImpIntro(ImpIntro(Hyp(0)))
    accepted_body = ImpIntro(Hyp(0))
    target = Eq(zero, zero)
    initial_target = Imp(target, Imp(target, target))
    accepted_target = Imp(target, target)
    initial = _body_receipt(initial_body, initial_target, 2)
    accepted = _body_receipt(accepted_body, accepted_target, 1)
    attempt = {
        "after_dependencies": ["keep"],
        "attempt_index": 0,
        "before_dependencies": ["keep", "drop"],
        "omitted_dependency": "drop",
        "outcome": "kernel-accepted",
        "pass_index": 0,
        "positive_receipt": accepted,
        "record_sha256": "a" * 64,
    }
    audit_row = {
        "declared_dependencies": ["keep", "drop"],
        "readable": {"proof": initial},
        "recipe_audit": {
            "attempts": [attempt],
            "candidate_dependencies": ["keep"],
            "initial_dependencies": ["keep", "drop"],
            "positive_receipt": initial,
        },
    }
    rebuild_row = {
        "body_receipt": accepted,
        "candidate_direct_dependencies": ["keep"],
        "direct_cut_spine": {"omitted_direct_dependency": "drop"},
        "retained_direct_dependencies": ["keep", "drop"],
    }
    return audit_row, rebuild_row


def test_a21_a22_receipt_route_joins_the_unique_accepted_omission_exactly() -> None:
    audit_row, rebuild_row = _receipt_route_fixture()
    receipt, source = pilot._expected_body_receipt(
        "fixture", audit_row=audit_row, rebuild_row=rebuild_row
    )
    accepted = audit_row["recipe_audit"]["attempts"][0]
    assert receipt == rebuild_row["body_receipt"] == accepted["positive_receipt"]
    assert source["receipt_route"] == "a2.2-and-last-accepted-omission"
    assert source["a2_1_last_accepted_receipt_sha256"] == accepted[
        "positive_receipt"
    ]["receipt_sha256"]


def test_recovered_body_source_labels_alias_metrics_as_nontransportable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zero = Zero()
    target = Eq(zero, zero)
    proof = EqRefl(zero)
    receipt = _body_receipt(proof, target, 0)
    audit_rows = {
        "fixture": {
            "declared_dependencies": [],
            "readable": {"proof": receipt},
            "recipe_audit": {
                "attempts": [],
                "candidate_dependencies": [],
                "initial_dependencies": [],
                "positive_receipt": receipt,
            },
        }
    }
    replay_rows = {
        "fixture": {
            "artifact": {"sha256": "a" * 64},
            "declared_dependencies": [],
            "proof_term_sha256": _sha(encode_proof(proof)),
        }
    }
    monkeypatch.setattr(
        pilot,
        "_decode_replay_artifact",
        lambda *_args, **_kwargs: (b"fixture", 24, target, proof),
    )

    recovered, source = pilot._recover_node(
        "fixture",
        root=ROOT,
        audit_rows=audit_rows,
        rebuild_rows={},
        replay_rows=replay_rows,
        recovered_targets={},
    )
    assert recovered.receipt == receipt
    assert source["identity_metrics_comparable"] is False
    assert source["source_identity_metrics_transportable"] is False
    assert source["stable_receipt_fields_compared"] == [
        "certificate_representation",
        "certificate_sha256",
        "dependency_count",
        "kernel_accepted",
        "metrics.proof_depth",
        "metrics.proof_nodes",
        "target_formula_sha256",
    ]


@pytest.mark.parametrize(
    "mutate",
    (
        lambda audit, _rebuild: audit["recipe_audit"]["attempts"].append(
            deepcopy(audit["recipe_audit"]["attempts"][0])
        ),
        lambda audit, _rebuild: audit["recipe_audit"]["attempts"][0].__setitem__(
            "omitted_dependency", "other"
        ),
        lambda audit, _rebuild: audit["recipe_audit"]["attempts"][0].__setitem__(
            "after_dependencies", ["other"]
        ),
        lambda audit, _rebuild: audit["recipe_audit"]["attempts"][0].__setitem__(
            "positive_receipt", deepcopy(audit["recipe_audit"]["positive_receipt"])
        ),
    ),
)
def test_a21_a22_receipt_route_mutations_fail_closed(mutate) -> None:
    audit_row, rebuild_row = _receipt_route_fixture()
    mutate(audit_row, rebuild_row)
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError):
        pilot._expected_body_receipt(
            "fixture", audit_row=audit_row, rebuild_row=rebuild_row
        )


@pytest.mark.parametrize(
    "mutation, message",
    (
        ("wrong-proposition", "proposition|spine"),
        ("wrong-conclusion", "failed empty-context|conclusion|target|kernel"),
        ("wrong-lemma-hash", "spine|hash|lemma"),
        ("wrong-body-receipt", "receipt"),
        ("missing-cut", "Cut|spine"),
    ),
)
def test_recovery_fails_closed_on_spine_or_final_receipt_mutation(
    mutation: str, message: str
) -> None:
    zero = Zero()
    one = Succ(zero)
    target = Eq(zero, zero)
    dependency_target = Eq(one, one)
    dependency_proof = EqRefl(one)
    residual = EqRefl(zero)
    proof = Cut(dependency_target, target, dependency_proof, residual)
    dependency_hash = _sha(encode_proof(dependency_proof))
    curried = ImpIntro(residual)
    receipt = _body_receipt(curried, Imp(dependency_target, target), 1)

    if mutation == "wrong-proposition":
        proof = Cut(target, target, EqRefl(zero), residual)
    elif mutation == "wrong-conclusion":
        proof = Cut(dependency_target, dependency_target, dependency_proof, Hyp(0))
    elif mutation == "wrong-lemma-hash":
        dependency_hash = "0" * 64
    elif mutation == "wrong-body-receipt":
        receipt = deepcopy(receipt)
        receipt["certificate_sha256"] = "0" * 64
        receipt["receipt_sha256"] = _canonical_hash(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        )
    elif mutation == "missing-cut":
        proof = residual
    else:  # pragma: no cover - parametrization is closed above
        raise AssertionError(mutation)

    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError, match=message):
        pilot.recover_curried_modular_body(
            name="fixture",
            target=target,
            proof=proof,
            dependencies=("dependency",),
            dependency_targets={"dependency": dependency_target},
            dependency_proof_sha256={"dependency": dependency_hash},
            expected_body_receipt=receipt,
        )


def test_comparison_keeps_equality_and_incomparability_but_removes_dominance() -> None:
    dominant = _candidate("dominant", order=0, values=(10, 10, 10, 10))
    dominated = _candidate("dominated", order=1, values=(11, 11, 10, 10))
    equal = _candidate("equal", order=2, values=(10, 10, 10, 10))
    incomparable = _candidate("incomparable", order=3, values=(9, 12, 9, 12))

    assert pilot.componentwise_nondominated(
        (dominated, equal, incomparable, dominant)
    ) == ("equal", "incomparable", "dominant")


def test_comparison_rejects_empty_or_duplicate_candidate_universes() -> None:
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError, match="non-empty"):
        pilot.componentwise_nondominated(())
    row = _candidate("same", order=0, values=(1, 1, 1, 0))
    duplicate = deepcopy(row)
    duplicate["candidate_kind_order"] = 1
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError, match="unique"):
        pilot.componentwise_nondominated((row, duplicate))
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError, match="unique"):
        pilot.select_pilot_representative((row, duplicate))


def test_representative_order_is_exactly_schema_bound_and_totally_deterministic() -> None:
    # This pair distinguishes proof-nodes-first from bytes-first.  The schema
    # binds proof nodes first; changing that policy must change the schema too.
    bytes_first = _candidate("bytes-first", order=2, values=(9, 100, 10, 10))
    nodes_first = _candidate("nodes-first", order=0, values=(10, 9, 9, 9))
    assert pilot.select_pilot_representative((nodes_first, bytes_first)) == (
        "nodes-first"
    )

    equal_a = _candidate(
        "equal-a", order=1, values=(10, 10, 10, 10), artifact_sha256="1" * 64
    )
    equal_b = _candidate(
        "equal-b", order=0, values=(10, 10, 10, 10), artifact_sha256="f" * 64
    )
    assert pilot.select_pilot_representative((equal_a, equal_b)) == "equal-b"
    assert pilot.select_pilot_representative((equal_b, equal_a)) == "equal-b"


@pytest.mark.parametrize(
    "mutate",
    (
        lambda row: row["metrics"].__setitem__("proof_objects", 1),
        lambda row: row["metrics"].__setitem__("proof_nodes", True),
        lambda row: row["metrics"].__delitem__("cut_nodes"),
        lambda row: row["metrics"].__setitem__("artifact_bytes", 0),
        lambda row: row["metrics"].__setitem__("proof_nodes", 0),
        lambda row: row["metrics"].__setitem__("proof_depth", 0),
        lambda row: row.__setitem__("candidate_kind_order", True),
        lambda row: row.__setitem__("candidate_kind_order", -1),
        lambda row: row.__setitem__("artifact_sha256", "not-a-hash"),
        lambda row: row.__setitem__("artifact_sha256", _DigestLike()),
        lambda row: row.__setitem__("candidate_id", ""),
        lambda row: row.__setitem__("candidate_id", "contains space"),
        lambda row: row.__setitem__("candidate_id", "nonascii-é"),
        lambda row: row.__setitem__("candidate_id", "line\nbreak"),
    ),
)
def test_comparison_rejects_noncanonical_or_identity_metric_inputs(mutate) -> None:
    row = _candidate("candidate", order=0, values=(1, 1, 1, 0))
    mutate(row)
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError):
        pilot.componentwise_nondominated((row,))
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError):
        pilot.select_pilot_representative((row,))


def test_schema_separates_direct_vectors_from_closures_and_denies_global_flags() -> None:
    schema = pilot.optimizer_comparison_pilot_schema()
    semantics = schema["claim_boundary"]["dependency_semantics"]
    assert "direct vectors" in semantics
    assert "transitive closures" in semantics
    assert "separate" in semantics
    constants = schema["constants"]
    for field in (
        "a2_complete",
        "dependency_vectors_complete",
        "evaluation_eligible",
        "freeze_ready",
        "lineage_complete",
        "minimality_claim",
        "optimized_best_known",
        "optimized_vector_independently_audited",
        "publication_ready",
        "publication_union_complete",
        "publication_union_verified",
        "retrieval_eligible",
        "review_complete",
        "training_eligible",
    ):
        assert constants[field] is False
    assert constants["status"] == "candidate"


def test_schema_pins_every_layered_compiler_resource_limit_exactly() -> None:
    configured = pilot.optimizer_comparison_pilot_schema()["limits"][
        "layered_replay"
    ]
    defaults = layered.DEFAULT_LAYERED_REPLAY_LIMITS
    assert configured == {
        "max_body_annotation_occurrences": defaults.max_body_annotation_occurrences,
        "max_body_depth": defaults.max_body_depth,
        "max_body_envelope_depth": defaults.max_body_envelope_depth,
        "max_body_objects": defaults.max_body_objects,
        "max_body_occurrences": defaults.max_body_occurrences,
        "max_candidate_annotation_occurrences": (
            defaults.max_candidate_annotation_occurrences
        ),
        "max_candidate_envelope_depth": defaults.max_candidate_envelope_depth,
        "max_candidate_proof_depth": defaults.max_candidate_proof_depth,
        "max_candidate_proof_objects": defaults.max_candidate_proof_objects,
        "max_candidate_proof_occurrences": defaults.max_candidate_proof_occurrences,
        "max_dependencies_per_node": defaults.max_dependencies_per_node,
        "max_dependency_edges": defaults.max_dependency_edges,
        "max_formula_depth": defaults.max_formula_depth,
        "max_formula_occurrences_per_target": (
            defaults.max_formula_occurrences_per_target
        ),
        "max_nodes": defaults.max_nodes,
        "max_package_formula_depth": defaults.max_package_formula_depth,
        "max_package_formula_occurrences": defaults.max_package_formula_occurrences,
        "max_total_body_annotation_occurrences": (
            defaults.max_total_body_annotation_occurrences
        ),
        "max_total_body_objects": defaults.max_total_body_objects,
        "max_total_body_occurrences": defaults.max_total_body_occurrences,
        "max_total_formula_occurrences": defaults.max_total_formula_occurrences,
    }


def test_layered_none_is_typed_unknown_and_aborts_the_whole_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zero = Zero()
    target = Eq(zero, zero)
    dependency = pilot.RecoveredModularBody(
        target=target,
        dependencies=(),
        curried_target=target,
        body=EqRefl(zero),
        receipt={"certificate_sha256": _sha(encode_proof(EqRefl(zero)))},
    )
    root_body = ImpIntro(Hyp(0))
    recovered_root = pilot.RecoveredModularBody(
        target=target,
        dependencies=("dependency",),
        curried_target=Imp(target, target),
        body=root_body,
        receipt={"certificate_sha256": _sha(encode_proof(root_body))},
    )
    replay_rows = {
        "dependency": {"declared_dependencies": [], "index": 0},
        "root": {"declared_dependencies": ["dependency"], "index": 1},
    }
    rebuild_rows = {"root": {"candidate_direct_dependencies": ["dependency"]}}
    calls: list[str] = []

    def recover(name, *_args, recovered_targets, **_kwargs):
        calls.append(name)
        if name == "dependency":
            assert recovered_targets == {}
            return dependency, {"fixture": True}
        assert name == "root"
        assert recovered_targets == {"dependency": target}
        return recovered_root, {"fixture": True}

    monkeypatch.setattr(
        pilot,
        "_recover_node",
        recover,
    )
    monkeypatch.setattr(pilot, "compile_layered_replay", lambda *_args, **_kwargs: None)

    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="typed unknown",
    ):
        pilot._build_layered_candidate(
            "root",
            root=ROOT,
            audit_rows={},
            rebuild_rows=rebuild_rows,
            replay_rows=replay_rows,
        )
    assert calls == ["dependency", "root"]


def test_small_layered_candidate_uses_preregistered_fuel_and_replays(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zero = Zero()
    target = Eq(zero, zero)
    dependency = pilot.RecoveredModularBody(
        target=target,
        dependencies=(),
        curried_target=target,
        body=EqRefl(zero),
        receipt={"certificate_sha256": _sha(encode_proof(EqRefl(zero)))},
    )
    root_body = ImpIntro(Hyp(0))
    recovered_root = pilot.RecoveredModularBody(
        target=target,
        dependencies=("dependency",),
        curried_target=Imp(target, target),
        body=root_body,
        receipt={"certificate_sha256": _sha(encode_proof(root_body))},
    )
    replay_rows = {
        "dependency": {"declared_dependencies": [], "index": 0},
        "root": {"declared_dependencies": ["dependency"], "index": 1},
    }
    rebuild_rows = {"root": {"candidate_direct_dependencies": ["dependency"]}}

    def recover(name, *_args, recovered_targets, **_kwargs):
        if name == "dependency":
            assert recovered_targets == {}
            return dependency, {"fixture": True}
        assert recovered_targets == {"dependency": target}
        return recovered_root, {"fixture": True}

    monkeypatch.setattr(pilot, "_recover_node", recover)
    body_cache: dict[
        str, tuple[pilot.RecoveredModularBody, dict[str, object]]
    ] = {}
    raw, fuel, built_target, proof, diagnostics, closure, direct = (
        pilot._build_layered_candidate(
            "root",
            root=ROOT,
            audit_rows={},
            _shared_body_cache=body_cache,
            rebuild_rows=rebuild_rows,
            replay_rows=replay_rows,
        )
    )
    metrics = pilot.proof_tree_metrics(proof)
    assert fuel == 8 * metrics["proof_nodes"] + 16
    assert raw
    assert built_target == target
    assert check((), proof, target)
    assert diagnostics["node_names_in_replay_order"] == ["dependency", "root"]
    assert closure == ("dependency",)
    assert direct == ("dependency",)
    assert tuple(body_cache) == ("dependency", "root")


def test_layered_helpers_reuse_only_curried_bodies_across_the_fixed_pilot_union(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    zero = Zero()
    target = Eq(zero, zero)
    leaf = pilot.RecoveredModularBody(
        target=target,
        dependencies=(),
        curried_target=target,
        body=EqRefl(zero),
        receipt={"certificate_sha256": _sha(encode_proof(EqRefl(zero)))},
    )
    root_body = ImpIntro(Hyp(0))
    roots = {
        name: pilot.RecoveredModularBody(
            target=target,
            dependencies=("shared",),
            curried_target=Imp(target, target),
            body=root_body,
            receipt={"certificate_sha256": _sha(encode_proof(root_body))},
        )
        for name in ("root-a", "root-b")
    }
    replay_rows = {
        "shared": {"declared_dependencies": [], "index": 0},
        "root-a": {"declared_dependencies": ["shared"], "index": 1},
        "root-b": {"declared_dependencies": ["shared"], "index": 2},
    }
    rebuild_rows = {
        "root-a": {"candidate_direct_dependencies": ["shared"]},
        "root-b": {"candidate_direct_dependencies": ["shared"]},
    }
    calls: list[str] = []

    def recover(name, *_args, recovered_targets, **_kwargs):
        calls.append(name)
        if name == "shared":
            assert recovered_targets == {}
            return leaf, {"source": "curried-only"}
        assert recovered_targets["shared"] == target
        return roots[name], {"source": "curried-only"}

    monkeypatch.setattr(pilot, "_recover_node", recover)
    cache: dict[str, tuple[pilot.RecoveredModularBody, dict[str, object]]] = {}
    for root_name in ("root-a", "root-b"):
        raw, _fuel, built_target, proof, *_rest = pilot._build_layered_candidate(
            root_name,
            root=ROOT,
            audit_rows={},
            _shared_body_cache=cache,
            rebuild_rows=rebuild_rows,
            replay_rows=replay_rows,
        )
        assert raw
        assert built_target == target
        assert check((), proof, target)

    assert calls == ["shared", "root-a", "root-b"]
    assert set(cache) == {"shared", "root-a", "root-b"}
    assert all(
        type(value[0]) is pilot.RecoveredModularBody and type(value[1]) is dict
        for value in cache.values()
    )


def test_runtime_callable_and_source_drift_fail_before_any_candidate_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pilot, "check", lambda *_args: True)
    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="runtime callable drifted",
    ):
        pilot._require_implementation(ROOT)
    monkeypatch.undo()

    original = pilot._safe_file

    def tampered(path: Path, *, label: str, limit: int) -> bytes:
        raw = original(path, label=label, limit=limit)
        if "layered_replay.py" in label:
            return raw + b"\n"
        return raw

    monkeypatch.setattr(pilot, "_safe_file", tampered)
    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="implementation source .* drifted",
    ):
        pilot._require_implementation(ROOT)


def test_runtime_layered_limit_drift_fails_before_compilation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pilot,
        "PILOT_LAYERED_LIMITS",
        replace(pilot.PILOT_LAYERED_LIMITS, max_nodes=4_095),
    )
    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="layered.*limit.*drift|limit.*drift",
    ):
        pilot._require_implementation(ROOT)


def test_dependency_surface_keeps_direct_vector_and_closure_domain_separated() -> None:
    basis = "modular-input-graph-not-literal-final-certificate-cut-spine"
    surface = pilot._surface(
        ("direct",),
        ("direct", "transitive"),
        surface_basis=basis,
    )
    assert surface == {
        "direct_dependency_count": 1,
        "direct_dependencies": ["direct"],
        "direct_dependencies_lf_sha256": _sha(b"direct\n"),
        "surface_basis": basis,
        "transitive_closure_count": 2,
        "transitive_closure_dependencies_in_replay_order": [
            "direct",
            "transitive",
        ],
        "transitive_closure_lf_sha256": _sha(b"direct\ntransitive\n"),
    }


def test_registered_surface_basis_literals_distinguish_proof_shapes() -> None:
    assert pilot.SURFACE_BASES == {
        "a2.2-direct-cut-rebuild": "a2.2-rebuilt-literal-direct-cut-spine",
        "layered-closure": (
            "modular-input-graph-not-literal-final-certificate-cut-spine"
        ),
        "retained-replay": "retained-manifest-literal-direct-cut-spine",
    }


def test_fully_rerooted_flag_forgery_still_fails_exact_reconstruction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline = {
        "optimized_best_known": False,
        "producer_source_state": _producer_source_state(),
        "root_preimage": {
            "format": pilot.OPTIMIZER_COMPARISON_PILOT_ROOT_PREIMAGE_FORMAT,
            "payload": {"optimized_best_known": False},
            "v": 1,
        },
        "root_sha256": "0" * 64,
    }
    baseline["root_sha256"] = pilot._sha256_json(baseline["root_preimage"])
    forged = deepcopy(baseline)
    forged["optimized_best_known"] = True
    forged["root_preimage"]["payload"]["optimized_best_known"] = True
    forged["root_sha256"] = pilot._sha256_json(forged["root_preimage"])
    monkeypatch.setattr(pilot, "optimizer_comparison_pilot_schema", lambda: {})
    monkeypatch.setattr(
        pilot,
        "_build_candidate_optimizer_comparison_pilot",
        lambda _root, *, producer_source_state: deepcopy(baseline),
    )
    monkeypatch.setattr(pilot, "_repository_root", lambda _root: ROOT)

    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="fixed-source reconstruction",
    ):
        pilot.validate_optimizer_comparison_pilot(forged, repository_root=ROOT)


def test_historical_a21_a22_and_replay_inputs_remain_byte_identical() -> None:
    for path, expected in HISTORICAL_SHA256.items():
        assert _sha(path.read_bytes()) == expected


def test_fixed_a21_union_derives_exact_cache_and_bundle_bounds_without_building() -> None:
    audit = json.loads(RETAINED_A21.read_bytes())
    rebuild = json.loads(RETAINED_A22.read_bytes())
    manifest = json.loads(REPLAY_MANIFEST.read_bytes())
    audit_rows = {row["name"]: row for row in audit["theorems"]}
    rebuild_rows = {row["name"]: row for row in rebuild["theorems"]}
    replay_rows = {row["name"]: row for row in manifest["theorems"]}
    overrides = {
        name: tuple(row["candidate_direct_dependencies"])
        for name, row in rebuild_rows.items()
    }

    def dependencies(name: str) -> tuple[str, ...]:
        return overrides.get(name, tuple(replay_rows[name]["declared_dependencies"]))

    def inclusive_closure(root_name: str) -> set[str]:
        seen: set[str] = set()
        pending = [root_name]
        while pending:
            name = pending.pop()
            if name in seen:
                continue
            seen.add(name)
            pending.extend(dependencies(name))
        return seen

    roots = [name for _index, name in EXPECTED_ROOTS]
    closures = {name: inclusive_closure(name) for name in roots}
    union = set().union(*closures.values())

    def selected_body_nodes(name: str) -> int:
        if name in rebuild_rows:
            receipt = rebuild_rows[name]["body_receipt"]
        else:
            receipt = audit_rows[name]["recipe_audit"]["positive_receipt"]
        return receipt["metrics"]["proof_nodes"]

    assert {name: len(closures[name]) for name in roots} == {
        "beta_product_swap_last_invariant": 32,
        "finite_bounded_injective_surjective": 120,
        "odd_add_odd": 6,
    }
    assert len(union) == 127
    assert sum(len(dependencies(name)) for name in union) == 328
    node_counts = [selected_body_nodes(name) for name in union]
    assert sum(node_counts) == 7_365
    assert max(node_counts) == 373
    assert pilot.PILOT_BUNDLE_NODE_COUNTS == {
        name: len(closures[name]) for name in roots
    }
    assert pilot.PILOT_BODY_UNION_COUNT == len(union)
    assert pilot.PILOT_BODY_UNION_DIRECT_EDGES == 328
    assert pilot.PILOT_BODY_UNION_PROOF_NODES == sum(node_counts)
    assert pilot.PILOT_BODY_MAX_PROOF_NODES == max(node_counts)


def test_cli_publish_is_create_only_atomic_regular_and_exact(tmp_path: Path) -> None:
    cli = _load_cli()
    destination = tmp_path / "pilot.json"
    raw = b'{"fixture":true}\n'
    cli._publish(destination, raw)
    metadata = destination.lstat()
    assert stat.S_ISREG(metadata.st_mode)
    assert not stat.S_ISLNK(metadata.st_mode)
    assert destination.read_bytes() == raw
    cli._read_exact(destination, raw)
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError, match="already exists"):
        cli._publish(destination, b"replacement\n")
    assert destination.read_bytes() == raw


def test_cli_has_no_default_write(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = _load_cli()
    builds: list[object] = []
    writes: list[object] = []
    monkeypatch.setattr(
        cli,
        "build_candidate_optimizer_comparison_pilot",
        lambda **_kwargs: builds.append("build"),
    )
    monkeypatch.setattr(cli, "_publish", lambda *_args: writes.append("publish"))
    monkeypatch.setattr(cli, "_read_exact", lambda *_args: writes.append("read"))
    monkeypatch.setattr(sys, "argv", [str(CLI_PATH)])

    cli.main()

    assert builds == []
    assert writes == []
    assert "no build or retained write requested" in capsys.readouterr().out


def test_cli_refuses_build_or_check_without_external_producer_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    builds: list[object] = []
    monkeypatch.setattr(
        cli,
        "build_candidate_optimizer_comparison_pilot",
        lambda **_kwargs: builds.append("build"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [str(CLI_PATH), "--output", str(tmp_path / "pilot.json")],
    )
    with pytest.raises(SystemExit) as raised:
        cli.main()
    assert raised.value.code == 2
    assert builds == []


def test_loader_and_cli_reject_symlink_and_fifo_without_blocking(tmp_path: Path) -> None:
    cli = _load_cli()
    actual = tmp_path / "actual.json"
    actual.write_bytes(b"{}\n")
    linked = tmp_path / "linked.json"
    try:
        linked.symlink_to(actual)
    except OSError:
        pytest.skip("symlinks are unavailable")
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError, match="regular|open"):
        pilot.load_optimizer_comparison_pilot(linked, repository_root=ROOT)
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError, match="regular|open"):
        cli._read_exact(linked, b"{}\n")

    actual_parent = tmp_path / "actual-parent"
    actual_parent.mkdir()
    (actual_parent / "pilot.json").write_bytes(b"{}\n")
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(actual_parent, target_is_directory=True)
    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="parent contains a link|symlink",
    ):
        pilot._safe_file(
            linked_parent / "pilot.json",
            label="optimizer/comparison pilot",
            limit=pilot.MAX_DOCUMENT_BYTES,
        )
    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="parent contains a link",
    ):
        cli._read_exact(linked_parent / "pilot.json", b"{}\n")

    if not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"):
        return
    fifo = tmp_path / "fifo.json"
    os.mkfifo(fifo)
    with pytest.raises(pilot.LibraryOptimizerComparisonPilotError, match="regular"):
        pilot.load_optimizer_comparison_pilot(fifo, repository_root=ROOT)
    with pytest.raises(
        pilot.LibraryOptimizerComparisonPilotError,
        match="differs from the deterministic build",
    ):
        cli._read_exact(fifo, b"{}\n")
