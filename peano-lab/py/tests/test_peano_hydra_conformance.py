"""Small native-only tests of authored H0 fixture bytes, never a Lean run."""

from __future__ import annotations

from collections import Counter
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel.checker import check, check_classical  # noqa: E402
from peano_lab.kernel.formulas import And, Forall, parse_formula_in_context  # noqa: E402
from peano_lab.kernel.proofs import AndIntro, DNE, Ind  # noqa: E402
from peano_lab.library.proof_bundle import decode_formula, decode_proof, encode_formula, encode_proof  # noqa: E402
from training.peano_hydra import conformance  # noqa: E402
from training.peano_hydra.conformance import (  # noqa: E402
    ConformanceCase, ConformanceError, build_conformance_cases,
    check_native_cases, conformance_manifest,
)
from training.peano_hydra.protocol import development_profile, validate_statement  # noqa: E402


@pytest.fixture(scope="module")
def cases() -> tuple[ConformanceCase, ...]:
    return build_conformance_cases()


@pytest.fixture(scope="module")
def manifest(cases: tuple[ConformanceCase, ...]) -> dict[str, object]:
    return conformance_manifest(cases)


@pytest.fixture(scope="module")
def native(cases: tuple[ConformanceCase, ...]) -> dict[str, object]:
    return check_native_cases(cases)


def _wire(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def test_fixed_suite_has_1024_distinct_positive_formulas_not_1024_independent_lineages(
    cases: tuple[ConformanceCase, ...], manifest: dict[str, object],
) -> None:
    positives = tuple(case for case in cases if case.kind == "positive")
    assert len(positives) == len({case.statement for case in positives}) == 1024
    assert manifest["distinct_positive_formula_count"] == 1024
    assert len(manifest["positive_family_counts"]) == 32
    assert set(manifest["positive_family_counts"].values()) == {32}
    assert len(cases) == manifest["case_count"] == 1321
    assert manifest["certificate_mutation_count"] == 280
    assert manifest["wire_mutation_count"] == 17
    assert "no assumptions or independent-lineage claim" in manifest["generation"]["uniqueness_marker"]
    assert "not Hydra search" in manifest["authorship"]
    assert build_conformance_cases() == cases


def test_every_positive_is_admitted_and_exactly_round_trips_through_existing_wire_codec(
    cases: tuple[ConformanceCase, ...],
) -> None:
    for case in cases:
        if case.kind != "positive":
            continue
        data = json.loads(case.artifact)
        target = decode_formula(data[2])
        proof = decode_proof(data[3])
        assert data[0:2] == ["peano-lab-v2", 4096]
        assert case.artifact == _wire(data)
        assert validate_statement(case.statement) == case.statement
        assert parse_formula_in_context(case.statement, []) == target
        assert encode_formula(target) == data[2]
        assert encode_proof(proof) == data[3]
        # The tag is a proved reflexive conjunct, never an extra possibly-false
        # premise that could hide semantic errors in the authored rule body.
        assert type(target) is And and type(proof) is AndIntro
        assert check((), proof.left, target.left)
        assert check((), proof.right, target.right)


def test_native_checks_accept_all_positives_reject_all_certificate_mutations_and_skip_wire(
    native: dict[str, object],
) -> None:
    assert native["positive_certificates_checked"] == native["positive_certificates_accepted"] == 1024
    assert native["certificate_mutations_rejected"] == 280
    assert native["wire_cases_skipped"] == 17
    assert native["all_expected_results"] is True
    assert native["mismatches"] == []
    assert native["checked_exact_artifact_bytes"] is True
    assert native["classical"] is False
    assert native["independent_reference_checked"] is False
    assert native["negative_theoremhood_claim"] is False
    unhashed = dict(native)
    assert unhashed.pop("report_sha256") == _digest(unhashed)


def test_all_constructive_rules_and_six_pa_axioms_have_positive_authored_coverage(
    manifest: dict[str, object],
) -> None:
    expected = {
        "hyp", "imp_intro", "imp_elim", "cut", "and_intro", "and_elim_l", "and_elim_r",
        "or_intro_l", "or_intro_r", "or_elim", "bot_elim", "forall_intro", "forall_elim",
        "exists_intro", "exists_elim", "eq_refl", "eq_sym", "eq_trans", "cong_s",
        "cong_add", "cong_mul", "eq_subst", "axiom", "ind",
    }
    assert set(manifest["authored_template_constructor_occurrences"]) == expected
    assert set(manifest["positive_proof_constructor_occurrences"]) == expected
    assert all(value >= 32 for value in manifest["authored_template_constructor_occurrences"].values())
    assert set(manifest["positive_axiom_occurrences"]) == {f"PA{i}" for i in range(1, 7)}


def test_mutations_target_actual_rules_binders_equality_motives_and_induction_parts(
    cases: tuple[ConformanceCase, ...], manifest: dict[str, object],
) -> None:
    coverage = manifest["mutation_coverage"]
    assert set(coverage) >= {
        "wrong-pa-axiom", "wrong-hypothesis-slot", "reversed-transitivity-premises",
        "wrong-conjunction-projection", "wrong-disjunction-injection", "invalid-case-context",
        "witness-proof-disagreement", "existential-eigenvariable-escape",
        "outer-inner-variable-confusion", "wrong-witness-binder-depth",
        "wrong-equality-motive", "capturing-substitution-motive", "context-specialization-shift",
        "wrong-cut-proposition", "wrong-induction-motive", "wrong-induction-base", "wrong-induction-step",
        "classical-rule-in-intuitionistic-mode",
    }
    families = Counter(case.family for case in cases if case.kind == "certificate_mutation")
    assert families["induction"] == 24 and families["dne-boundary"] == 8
    assert all(count == 8 for name, count in families.items() if name not in {"induction", "dne-boundary"})
    parents = {case.case_id: case for case in cases if case.kind == "positive"}
    for case in cases:
        if case.kind != "certificate_mutation" or case.parent_case_id is None:
            continue
        assert case.statement == parents[case.parent_case_id].statement
        assert case.artifact != parents[case.parent_case_id].artifact


def test_induction_uses_a_real_successor_hypothesis_and_not_only_reflexivity(
    cases: tuple[ConformanceCase, ...],
) -> None:
    for case in cases:
        if case.kind != "positive" or case.family != "induction":
            continue
        target, proof = decode_formula(json.loads(case.artifact)[2]), decode_proof(json.loads(case.artifact)[3])
        assert type(target.right) is Forall and type(proof.right) is Ind
        assert ["cong_s", ["hyp", 0]] in json.loads(case.artifact)[3][2][3][1][1][1:]
        assert check((), proof.right, target.right)


def test_dne_rejection_is_a_certificate_mode_boundary_not_a_non_theorem_label(
    cases: tuple[ConformanceCase, ...],
) -> None:
    selected = [case for case in cases if case.family == "dne-boundary"]
    assert len(selected) == 8
    for case in selected:
        data = json.loads(case.artifact)
        proof, target = decode_proof(data[3]), decode_formula(data[2])
        assert type(proof) is DNE
        assert check_classical((), proof, target) is True
        assert check((), proof, target) is False
        assert "no theoremhood-negative conclusion" in case.to_dict()["claim"]


def test_wire_cases_are_separate_and_do_not_claim_native_or_lean_execution(
    cases: tuple[ConformanceCase, ...], manifest: dict[str, object], monkeypatch: pytest.MonkeyPatch,
) -> None:
    wires = tuple(case for case in cases if case.kind == "wire_mutation")
    assert Counter(case.expected_lean for case in wires) == {"DECODE_ERROR": 15, "REJECT": 2}
    assert all(case.expected_native is None and case.statement is None for case in wires)
    def forbidden(*args: object) -> None:
        pytest.fail("wire-only fixture reached the native theorem checker")
    monkeypatch.setattr(conformance, "check", forbidden)
    report = check_native_cases(wires)
    assert report["wire_cases_skipped"] == 17
    assert report["positive_certificates_checked"] == 0
    assert report["independent_reference_checked"] is False
    assert manifest["expected_lean_counts"] == {"ACCEPT": 1024, "REJECT": 282, "DECODE_ERROR": 15}
    assert manifest["status"] == "fixtures-planned-reference-not-run"


def test_zero_fuel_and_open_target_probe_lean_artifact_gate_not_python_checker_semantics(
    cases: tuple[ConformanceCase, ...],
) -> None:
    for case in cases:
        if case.family not in {"zero-fuel", "open-target"}:
            continue
        data = json.loads(case.artifact)
        assert check((), decode_proof(data[3]), decode_formula(data[2])) is True
        assert case.expected_lean == "REJECT" and case.expected_native is None


def test_native_endpoint_decodes_actual_artifact_bytes(
    cases: tuple[ConformanceCase, ...], monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoded = []
    original_decode = conformance.decode_proof
    def audited(value: object):
        decoded.append(value)
        return original_decode(value)
    monkeypatch.setattr(conformance, "decode_proof", audited)
    report = check_native_cases((cases[0],))
    assert report["positive_certificates_accepted"] == 1
    assert decoded == [json.loads(cases[0].artifact)[3]]


def test_manifest_hashes_sources_profile_epoch_and_every_artifact_separately(
    cases: tuple[ConformanceCase, ...], manifest: dict[str, object],
) -> None:
    assert manifest["profile_sha256"] == development_profile()["profile_sha256"]
    assert manifest["epoch_sha256"] is None
    assert manifest["artifact_total_bytes"] == sum(len(case.artifact) for case in cases)
    assert manifest["artifact_total_bytes"] < 2 * 1024 * 1024 < manifest["limits"]["max_suite_bytes"]
    assert max(len(case.artifact) for case in cases) < manifest["limits"]["max_case_bytes"]
    for source in manifest["source_bindings"]:
        raw = (ROOT / source["path"]).read_bytes()
        assert source["bytes"] == len(raw)
        assert source["sha256"] == hashlib.sha256(raw).hexdigest()
    assert manifest["cases_sha256"] == _digest([case.to_dict() for case in cases])
    unhashed = dict(manifest)
    assert unhashed.pop("manifest_sha256") == _digest(unhashed)
    with_epoch = conformance_manifest(cases, epoch_sha256="a" * 64)
    assert with_epoch["epoch_sha256"] == "a" * 64
    assert with_epoch["cases_sha256"] == manifest["cases_sha256"]
    assert with_epoch["manifest_sha256"] != manifest["manifest_sha256"]
    assert "no catalog imports" in with_epoch["epoch_role"]


def test_fixtures_immutable_metadata_detached_and_claims_explicit(
    cases: tuple[ConformanceCase, ...],
) -> None:
    with pytest.raises(FrozenInstanceError):
        cases[0].artifact = b"other"  # type: ignore[misc]
    metadata = cases[0].to_dict()
    metadata["artifact_sha256"] = "forged"
    assert cases[0].to_dict()["artifact_sha256"] != "forged"
    original = conformance_manifest(cases)
    first_hash = original["manifest_sha256"]
    assert not any(original["claims"].values())
    original["claims"]["h0_complete"] = True
    original["cases"].clear()
    assert conformance_manifest(cases)["manifest_sha256"] == first_hash


@pytest.mark.parametrize("epoch", ["", "a" * 63, "A" * 64, True, 42, {}, []])
def test_invalid_epoch_identity_is_rejected(cases: tuple[ConformanceCase, ...], epoch: object) -> None:
    with pytest.raises(ConformanceError):
        conformance_manifest(cases, epoch_sha256=epoch)


@pytest.mark.parametrize("replacement", [
    {"case_id": "../escape"}, {"family": "Bad family"}, {"seed": True}, {"seed": 32},
    {"kind": "unknown"}, {"kind": []}, {"expected_native": 1}, {"expected_native": False},
    {"expected_lean": "REJECT"}, {"expected_lean": []}, {"artifact": "not bytes"}, {"artifact": b""},
    {"statement": "n = n"}, {"statement": "forall n. n = n"}, {"mutation": "bad\nname"},
    {"parent_case_id": "../wrong"},
])
def test_case_fields_fail_closed(cases: tuple[ConformanceCase, ...], replacement: dict[str, object]) -> None:
    with pytest.raises((ConformanceError, ValueError)):
        replace(cases[0], **replacement)


@pytest.mark.parametrize("payload", [b"not json\n", b"[true]\n", b"\xff", b"{}\n"])
def test_invalid_serialized_native_payload_never_reaches_kernel(
    cases: tuple[ConformanceCase, ...], payload: bytes, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object) -> None:
        pytest.fail("bad artifact reached the native checker")
    monkeypatch.setattr(conformance, "check", forbidden)
    with pytest.raises(ConformanceError):
        check_native_cases((replace(cases[0], artifact=payload),))


def test_native_target_binding_rejects_substitution_of_a_different_statement(
    cases: tuple[ConformanceCase, ...], monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object) -> None:
        pytest.fail("mismatched original target reached the native checker")
    monkeypatch.setattr(conformance, "check", forbidden)
    with pytest.raises(ConformanceError, match="bound statement"):
        check_native_cases((replace(cases[0], statement="0 = 1"),))


def test_a_corrupted_positive_certificate_is_reported_not_silently_reclassified(
    cases: tuple[ConformanceCase, ...],
) -> None:
    data = json.loads(cases[0].artifact)
    data[3] = ["hyp", 0]
    corrupt = replace(cases[0], artifact=_wire(data))
    report = check_native_cases((corrupt,))
    assert report["all_expected_results"] is False
    assert report["positive_certificates_accepted"] == 0
    assert report["mismatches"] == [corrupt.case_id]
    assert report["negative_theoremhood_claim"] is False


def test_noncanonical_bytes_and_fuel_changes_fail_before_native_check(cases: tuple[ConformanceCase, ...]) -> None:
    data = json.loads(cases[0].artifact)
    for fuel in (True, 4095, 0, 4096.0):
        altered = [data[0], fuel, *data[2:]]
        with pytest.raises(ConformanceError, match="envelope/fuel"):
            check_native_cases((replace(cases[0], artifact=_wire(altered)),))
    with pytest.raises(ConformanceError, match="envelope/fuel"):
        check_native_cases((replace(cases[0], artifact=b" " + cases[0].artifact),))


def test_suite_bounds_and_duplicate_ids_are_enforced_without_large_allocations(
    cases: tuple[ConformanceCase, ...], monkeypatch: pytest.MonkeyPatch,
) -> None:
    for altered in ((), [], list(cases[:1]), (cases[0], cases[0]), (None,), (cases[0],) * 2049):
        with pytest.raises(ConformanceError):
            check_native_cases(altered)
    monkeypatch.setattr(conformance, "MAX_SUITE_BYTES", 16)
    with pytest.raises(ConformanceError, match="aggregate"):
        check_native_cases((cases[0],))


def test_fixture_generation_uses_no_copied_python_reference_or_lean_execution() -> None:
    source = (ROOT / "training/peano_hydra/conformance.py").read_text(encoding="utf-8")
    for forbidden in ("from reference.python_kernel", "import subprocess", "import torch", "import transformers"):
        assert forbidden not in source
    assert "from peano_lab.library.proof_bundle import" in source
    assert "from peano_lab.kernel.checker import check" in source
