"""Adversarial tests for Hydra's exact H0.1b evidence contract."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel.formulas import Bot, Eq, Imp  # noqa: E402
from peano_lab.kernel.proofs import DNE, EqRefl  # noqa: E402
from peano_lab.kernel.terms import Succ, Var, Zero  # noqa: E402
import training.peano_hydra.profile as profile_module  # noqa: E402
import training.peano_hydra.result_schema as schema_module  # noqa: E402
from training.peano_hydra.profile import (  # noqa: E402
    SEMANTIC_PROFILE_V1_DOCUMENT_SHA256,
    SEMANTIC_PROFILE_V1_PATH,
    SEMANTIC_PROFILE_V2_SHA256,
    semantic_profile,
    semantic_profile_identity,
    semantic_profile_v1,
)
from training.peano_hydra.result_schema import (  # noqa: E402
    CERTIFICATE_REPRESENTATION,
    HydraResultSchemaError,
    RESULT_FORMAT,
    RESULT_SCHEMA_SHA256,
    build_checked_proved_evidence,
    build_checked_proved_result,
    build_unknown_evidence,
    build_unknown_result,
    canonical_json_bytes,
    certificate_sha256,
    kernel_identity_sha256,
    original_theorem_sha256,
    replay_evidence_sha256,
    result_schema,
    result_schema_identity,
    run_evidence_sha256,
    validate_checked_proved_result,
    validate_result,
    validate_result_preimages,
)


TARGET = Eq(Zero(), Zero())
PROOF = EqRefl(Zero())
ARTIFACT = (
    b'["peano-lab-v2",24,["eq",["zero"],["zero"]],'
    b'["eq_refl",["zero"]]]\n'
)
PROVED_FIELDS = {
    "certificate_depth",
    "certificate_nodes",
    "certificate_representation",
    "certificate_sha256",
    "format",
    "kernel_accepted",
    "kernel_identity_sha256",
    "kind",
    "logic",
    "original_theorem",
    "original_theorem_sha256",
    "replay_evidence_sha256",
    "replay_outcome",
    "run_evidence_sha256",
    "semantic_profile_sha256",
    "v",
}
UNKNOWN_FIELDS = {
    "format",
    "kind",
    "logic",
    "original_theorem",
    "original_theorem_sha256",
    "reason",
    "run_evidence_sha256",
    "semantic_profile_sha256",
    "v",
}


def _proved():
    return build_checked_proved_evidence(TARGET, PROOF, run_id="schema-test")


def _unknown():
    return build_unknown_evidence(
        "0=0", reason="search-exhausted", run_id="schema-unknown"
    )


def _canonical_document(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _hash_envelope(field: str, payload: object) -> bytes:
    return canonical_json_bytes(
        {
            "field": field,
            "format": "peano-hydra-result-hash-preimage",
            "payload": payload,
            "v": 1,
        }
    )


def test_profile_v2_binds_exact_schema_without_rewriting_v1() -> None:
    assert hashlib.sha256(SEMANTIC_PROFILE_V1_PATH.read_bytes()).hexdigest() == (
        SEMANTIC_PROFILE_V1_DOCUMENT_SHA256
    )
    assert semantic_profile_v1()["evidence"]["schema_status"] == (
        "required-field-draft"
    )
    assert semantic_profile_identity()["sha256"] == SEMANTIC_PROFILE_V2_SHA256
    active = semantic_profile()
    assert active["authority"]["certificate_representation"] == "peano-lab-v2"
    assert active["evidence"]["schema"] == result_schema_identity()


def test_schema_artifact_is_canonical_closed_complete_and_digest_pinned() -> None:
    schema = result_schema()
    assert RESULT_SCHEMA_SHA256 == (
        "cf1caf1c867ddfbe3c247e42a18b730ea6790269718170a51f9733d5a7a36b26"
    )
    assert schema_module.RESULT_SCHEMA_PATH.read_bytes() == _canonical_document(schema)
    assert schema["additional_fields_policy"] == (
        "forbidden-at-every-schema-owned-object"
    )
    variants = [
        schema["result"]["proved"],
        schema["result"]["unknown"],
        schema["inner_objects"]["run_evidence"]["proved"],
        schema["inner_objects"]["run_evidence"]["unknown"],
        schema["inner_objects"]["kernel_identity"],
        schema["inner_objects"]["replay_evidence"],
        schema["hashes"]["json_preimage_envelope"],
    ]
    for variant in variants:
        assert variant["additional_properties"] is False
        assert set(variant["required"]) == set(variant["properties"])
        for field in variant["required"]:
            assert "type" in variant["properties"][field]
    assert set(schema["result"]["proved"]["required"]) == PROVED_FIELDS
    assert set(schema["result"]["unknown"]["required"]) == UNKNOWN_FIELDS
    expected_negative_text = [
        "negative_evidence",
        "negative_evidence_sha256",
        "not_theorem",
    ]
    run_schema = schema["inner_objects"]["run_evidence"]
    for variant in (run_schema["proved"], run_schema["unknown"]):
        assert variant["properties"]["run_id"][
            "forbidden_casefolded_separator_insensitive_substrings"
        ] == expected_negative_text


def test_checked_builder_derives_exact_artifact_metrics_and_all_hashes() -> None:
    bundle = _proved()
    result = bundle.result
    assert set(result) == PROVED_FIELDS
    assert result["format"] == RESULT_FORMAT
    assert result["kind"] == "proved"
    assert result["logic"] == "intuitionistic"
    assert result["kernel_accepted"] is True
    assert result["replay_outcome"] == "accepted"
    assert result["certificate_nodes"] == result["certificate_depth"] == 1
    assert result["certificate_representation"] == CERTIFICATE_REPRESENTATION
    assert bundle.certificate_artifact == ARTIFACT
    assert result["certificate_sha256"] == hashlib.sha256(ARTIFACT).hexdigest()
    assert result["original_theorem_sha256"] == hashlib.sha256(
        _hash_envelope("original_theorem_sha256", "0 = 0")
    ).hexdigest()
    assert result["kernel_identity_sha256"] == kernel_identity_sha256(
        bundle.kernel_identity
    )
    assert result["replay_evidence_sha256"] == replay_evidence_sha256(
        bundle.replay_evidence
    )
    assert result["run_evidence_sha256"] == run_evidence_sha256(
        bundle.run_evidence
    )
    assert certificate_sha256(ARTIFACT) == (
        "703a79d71660b9629a40c2890815f1a3e5d06220686c7ce6968019cd768c38c0"
    )
    assert original_theorem_sha256("0 = 0") == (
        "508f1b834bbab15c6d99d4ee43e969b35955fa09dbc547fd75f89fcfb2454210"
    )
    assert build_checked_proved_result(TARGET, PROOF, run_id="schema-test")[
        "certificate_sha256"
    ] == result["certificate_sha256"]


def test_positive_result_requires_authoritative_replay_against_original_goal() -> None:
    bundle = _proved()
    assert validate_checked_proved_result(
        bundle.result,
        TARGET,
        PROOF,
        run_evidence=bundle.run_evidence,
        kernel_identity=bundle.kernel_identity,
        replay_evidence=bundle.replay_evidence,
    ) == bundle.result
    with pytest.raises(HydraResultSchemaError, match="original target mismatch"):
        validate_checked_proved_result(
            bundle.result,
            Eq(Succ(Zero()), Succ(Zero())),
            EqRefl(Succ(Zero())),
            run_evidence=bundle.run_evidence,
            kernel_identity=bundle.kernel_identity,
            replay_evidence=bundle.replay_evidence,
        )
    with pytest.raises(HydraResultSchemaError, match="kernel rejection"):
        validate_checked_proved_result(
            bundle.result,
            TARGET,
            EqRefl(Succ(Zero())),
            run_evidence=bundle.run_evidence,
            kernel_identity=bundle.kernel_identity,
            replay_evidence=bundle.replay_evidence,
        )


def test_no_caller_boolean_or_text_can_mint_positive_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(TypeError):
        build_checked_proved_result(  # type: ignore[call-arg]
            TARGET, PROOF, run_id="bad", kernel_accepted=True
        )
    with pytest.raises(HydraResultSchemaError, match="kernel rejected"):
        build_checked_proved_result(
            TARGET, EqRefl(Succ(Zero())), run_id="wrong-proof"
        )
    proposition = Eq(Zero(), Zero())
    classical_target = Imp(Imp(Imp(proposition, Bot()), Bot()), proposition)
    with pytest.raises(HydraResultSchemaError, match="kernel rejected"):
        build_checked_proved_result(
            classical_target, DNE(proposition), run_id="classical-dne"
        )
    monkeypatch.setattr(schema_module.kernel_checker, "check", lambda *_: False)
    with pytest.raises(HydraResultSchemaError, match="kernel rejected"):
        build_checked_proved_result(TARGET, PROOF, run_id="forged-status")


def test_unknown_strictly_omits_all_positive_and_negative_claim_material() -> None:
    bundle = _unknown()
    result = bundle.result
    assert set(result) == UNKNOWN_FIELDS
    assert set(bundle.run_evidence) == {
        "degraded",
        "eligible_for_comparison",
        "format",
        "kind",
        "logic",
        "original_theorem",
        "original_theorem_sha256",
        "reason",
        "run_id",
        "semantic_profile_sha256",
        "status",
        "v",
    }
    forbidden = {
        "certificate_representation",
        "certificate_sha256",
        "kernel_accepted",
        "kernel_identity_sha256",
        "negative_evidence",
        "negative_evidence_sha256",
        "not_theorem",
        "replay_evidence_sha256",
        "replay_outcome",
    }
    assert forbidden.isdisjoint(result)
    assert forbidden.isdisjoint(bundle.run_evidence)
    assert bundle.certificate_artifact is None
    assert bundle.kernel_identity is None
    assert bundle.replay_evidence is None
    assert validate_result_preimages(result, run_evidence=bundle.run_evidence) == result
    with pytest.raises(HydraResultSchemaError, match="positive-evidence"):
        validate_result_preimages(
            result, run_evidence=bundle.run_evidence, certificate_artifact=ARTIFACT
        )
    for extra in forbidden | {"extra"}:
        mutation = dict(result)
        mutation[extra] = False
        with pytest.raises(HydraResultSchemaError):
            validate_result(mutation)
    assert build_unknown_result(
        "0=0", reason="timeout", run_id="unknown-result"
    )["reason"] == "timeout"


@pytest.mark.parametrize(
    "run_id",
    [
        "not_theorem",
        "not-theorem",
        "not.theorem",
        "not:theorem",
        "n.o-t:t.h-e:o.r_e.m",
        "negative_evidence",
        "negative-evidence",
        "negative.evidence",
        "negative:evidence:sha256",
    ],
)
def test_run_id_cannot_smuggle_separator_spelled_negative_claims(
    run_id: str,
) -> None:
    with pytest.raises(HydraResultSchemaError, match="negative-claim text"):
        build_unknown_evidence("0=0", reason="timeout", run_id=run_id)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("format", "peano-hydra-result-v2"),
        ("v", True),
        ("kind", "not_theorem"),
        ("logic", "classical"),
        ("semantic_profile_sha256", "0" * 64),
        ("original_theorem", "0=0"),
        ("original_theorem_sha256", "A" * 64),
        ("run_evidence_sha256", None),
        ("certificate_representation", "opaque"),
        ("certificate_sha256", "0"),
        ("certificate_nodes", True),
        ("certificate_depth", 0),
        ("certificate_depth", 2),
        ("kernel_accepted", False),
        ("replay_outcome", "not-run"),
    ],
)
def test_proved_result_rejects_wrong_types_constants_and_bindings(
    field: str, bad: object
) -> None:
    result = _proved().result
    result[field] = bad
    with pytest.raises(HydraResultSchemaError):
        validate_result(result)


def test_every_result_field_is_required_and_additions_are_rejected() -> None:
    for original in (_proved().result, _unknown().result):
        for field in tuple(original):
            mutation = dict(original)
            del mutation[field]
            with pytest.raises(HydraResultSchemaError):
                validate_result(mutation)
        mutation = dict(original)
        mutation["extra"] = None
        with pytest.raises(HydraResultSchemaError):
            validate_result(mutation)


def test_every_inner_preimage_is_exact_and_bound_to_the_result() -> None:
    bundle = _proved()
    for name in ("kernel_identity", "replay_evidence", "run_evidence"):
        value = deepcopy(getattr(bundle, name))
        value["extra"] = None
        kwargs = {
            "certificate_artifact": bundle.certificate_artifact,
            "kernel_identity": bundle.kernel_identity,
            "replay_evidence": bundle.replay_evidence,
            "run_evidence": bundle.run_evidence,
        }
        kwargs[name] = value
        with pytest.raises(HydraResultSchemaError):
            validate_result_preimages(bundle.result, **kwargs)
    replay = dict(bundle.replay_evidence)
    replay["certificate_depth"] = 2
    with pytest.raises(HydraResultSchemaError, match="cannot exceed"):
        replay_evidence_sha256(replay)
    changed = bytearray(bundle.certificate_artifact)
    changed[-2] ^= 1
    with pytest.raises(HydraResultSchemaError):
        validate_result_preimages(
            bundle.result,
            certificate_artifact=bytes(changed),
            kernel_identity=bundle.kernel_identity,
            replay_evidence=bundle.replay_evidence,
            run_evidence=bundle.run_evidence,
        )


def test_unknown_reason_is_bound_to_run_status_and_result() -> None:
    bundle = _unknown()
    changed_run = dict(bundle.run_evidence)
    changed_run["reason"] = "timeout"
    changed_run["status"] = "timeout"
    changed_result = dict(bundle.result)
    changed_result["run_evidence_sha256"] = run_evidence_sha256(changed_run)
    with pytest.raises(HydraResultSchemaError, match="reason mismatch"):
        validate_result_preimages(changed_result, run_evidence=changed_run)


def test_historical_validation_does_not_consult_the_future_active_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _proved()
    monkeypatch.setattr(profile_module, "semantic_profile_sha256", lambda: "f" * 64)
    assert validate_result(bundle.result) == bundle.result
    assert validate_result_preimages(
        bundle.result,
        certificate_artifact=bundle.certificate_artifact,
        kernel_identity=bundle.kernel_identity,
        replay_evidence=bundle.replay_evidence,
        run_evidence=bundle.run_evidence,
    ) == bundle.result


def test_evidence_bundle_returns_detached_objects() -> None:
    bundle = _proved()
    result = bundle.result
    kernel = bundle.kernel_identity
    replay = bundle.replay_evidence
    run = bundle.run_evidence
    result["kind"] = "unknown"
    kernel["logic"] = "classical"
    replay["kernel_accepted"] = False
    run["status"] = "error"
    assert bundle.result["kind"] == "proved"
    assert bundle.kernel_identity["logic"] == "intuitionistic"
    assert bundle.replay_evidence["kernel_accepted"] is True
    assert bundle.run_evidence["status"] == "proof"


@pytest.mark.parametrize(
    "bad",
    [1.5, 9_007_199_254_740_992, {"bad": object()}, {"bad": "\ud800"}],
)
def test_canonical_json_rejects_nonportable_values(bad: object) -> None:
    with pytest.raises(HydraResultSchemaError):
        canonical_json_bytes(bad)


def test_canonical_json_rejects_cycles_and_bad_limits() -> None:
    cycle: list[object] = []
    cycle.append(cycle)
    with pytest.raises(HydraResultSchemaError, match="cyclic"):
        canonical_json_bytes(cycle)
    with pytest.raises(TypeError, match="positive integer"):
        canonical_json_bytes({}, limit=True)
    with pytest.raises(HydraResultSchemaError, match="transport limit"):
        canonical_json_bytes({"x": "long"}, limit=1)


@pytest.mark.parametrize("mutation", ["whitespace", "duplicate", "float"])
def test_schema_loader_rejects_noncanonical_or_nonstrict_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    raw = schema_module.RESULT_SCHEMA_PATH.read_bytes()
    if mutation == "whitespace":
        bad = b" " + raw
    elif mutation == "duplicate":
        bad = raw.replace(b"{\n", b'{\n  "v": 1,\n', 1)
    else:
        bad = raw.replace(b'"maximum": 1000000', b'"maximum": 1.5', 1)
    path = tmp_path / "result-schema-v1.json"
    path.write_bytes(bad)
    monkeypatch.setattr(schema_module, "RESULT_SCHEMA_PATH", path)
    with pytest.raises(HydraResultSchemaError):
        result_schema()


def test_open_original_formula_and_bad_unknown_reason_are_rejected() -> None:
    with pytest.raises(HydraResultSchemaError, match="closed"):
        build_checked_proved_result(Eq(Var(0), Var(0)), EqRefl(Var(0)), run_id="open")
    with pytest.raises(HydraResultSchemaError, match="reason"):
        build_unknown_result(
            "0 = 0", reason="not-theorem", run_id="negative"  # type: ignore[arg-type]
        )
