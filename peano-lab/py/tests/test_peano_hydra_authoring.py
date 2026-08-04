"""Adversarial tests for Hydra's native-PA A0 authoring contract."""

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

from peano_lab.kernel.formulas import Eq  # noqa: E402
from peano_lab.kernel.proofs import EqRefl  # noqa: E402
from peano_lab.kernel.terms import Succ, Zero  # noqa: E402
import training.peano_hydra.authoring as authoring  # noqa: E402
from training.peano_hydra.authoring import (  # noqa: E402
    DIAGNOSTIC_AUTHORITIES,
    AuthoringContractError,
    AuthoringDocument,
    ExportEvent,
    FormalizationCandidate,
    LifecycleEvent,
    ProofAttempt,
    SentenceUnit,
    TheoremProposal,
    authoring_schema,
    authoring_schema_identity,
    build_checked_theorem_proposal,
    build_diagnostic,
    build_document,
    build_draft_theorem_proposal,
    build_formalization_candidate,
    build_kernel_diagnostic,
    build_proof_attempt,
    build_sentence_unit,
    canonical_json_bytes,
    library_epoch_identity,
    load_diagnostic,
    load_document,
    load_export_event,
    load_formalization_candidate,
    load_lifecycle_event,
    load_proof_attempt,
    load_sentence_unit,
    load_theorem_proposal,
)


SOURCE = "Every natural number equals itself.\nThis line is exposition."
CLAIM = "Every natural number equals itself."
TARGET = Eq(Zero(), Zero())
PROOF = EqRefl(Zero())
SHA_A = "a" * 64
SHA_B = "b" * 64


def _document(*, revision: int = 1, source: str = SOURCE, consent="deny"):
    return build_document(
        source,
        document_id="number-theory-note",
        revision=revision,
        library_epoch=library_epoch_identity("L0-test", SHA_A),
        training_consent=consent,
    )


def _unit(document=None, *, unit_id: str = "sentence-1"):
    document = _document() if document is None else document
    return build_sentence_unit(
        document,
        unit_id=unit_id,
        kind="claim",
        start_utf8=0,
        end_utf8=len(CLAIM.encode("utf-8")),
    )


def _candidate(unit=None):
    unit = _unit() if unit is None else unit
    return build_formalization_candidate(
        unit,
        candidate_id="reading-1",
        statement="0=0",
        provenance_kind="model",
        provenance_id="qwen-fixture",
        request_sha256=SHA_A,
        response_sha256=SHA_B,
        ambiguities=("quantifier-scope",),
        alternative_readings=("S 0 = S 0",),
    )


def _canonical_document(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _registry_event(kind: str, prefix: tuple[bytes, ...], record: dict[str, object]):
    value = deepcopy(record)
    value["sequence"] = len(prefix)
    previous_root = json.loads(prefix[-1])["registry_sha256"] if prefix else None
    value["registry_sha256"] = SHA_A
    value["registry_sha256"] = authoring._registry_step_sha256(
        kind, previous_root, value
    )
    raw = canonical_json_bytes(value)
    return raw, value["registry_sha256"], prefix + (raw,)


def test_schema_is_pinned_canonical_closed_and_machine_readable() -> None:
    schema = authoring_schema()
    identity = authoring_schema_identity()
    assert identity == {
        "format": "peano-hydra-authoring-schema",
        "v": 1,
        "id": "peano-hydra-native-pa-authoring-core-v1",
        "sha256": "31a344bbc0b22cfacf5803c85d25a80a0234cf7387395283c5e1ab25ada80553",
    }
    assert authoring.AUTHORING_SCHEMA_PATH.read_bytes() == _canonical_document(schema)
    assert hashlib.sha256(canonical_json_bytes(schema)).hexdigest() == identity["sha256"]
    assert schema["additional_fields_policy"] == (
        "forbidden-at-every-schema-owned-object"
    )
    assert set(schema["enums"]["diagnostic_authority"]) == set(
        DIAGNOSTIC_AUTHORITIES
    )
    assert schema["defined_syntax"] == {
        "id": "peano-lab.defined-predicates",
        "sha256": "924c8bc220f23ce772b72991b8234c3499be7698dc086d90509d39760a1ed0fe",
        "version": 2,
    }
    for item in schema["objects"].values():
        assert item["additional_fields"] == "forbidden"
        assert len(item["exact_fields"]) == len(set(item["exact_fields"]))


def test_schema_rejects_runtime_defined_syntax_registry_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(authoring, "DEFINED_SYNTAX_VERSION", 3)
    with pytest.raises(AuthoringContractError, match="runtime defined-syntax registry"):
        authoring_schema()


def test_document_binds_profile_logic_epoch_revision_and_exact_source() -> None:
    document = _document()
    record = document.record
    assert record["format"] == "peano-hydra-authoring-document"
    assert record["revision"] == 1
    assert record["logic"] == "intuitionistic"
    assert record["library_epoch"] == {
        "format": "peano-hydra-library-epoch",
        "v": 1,
        "id": "L0-test",
        "root_sha256": SHA_A,
    }
    assert record["source_text"] == SOURCE
    assert record["source_utf8_bytes"] == len(SOURCE.encode("utf-8"))
    assert record["source_sha256"] == hashlib.sha256(SOURCE.encode()).hexdigest()
    assert record["training_consent"] == "deny"
    assert load_document(document.canonical_bytes).record == record


@pytest.mark.parametrize("consent", ["deny", "allow-anonymized", "allow-exact"])
def test_training_consent_is_explicit_and_defaults_to_deny(consent: str) -> None:
    assert _document(consent=consent).record["training_consent"] == consent
    assert _document().record["training_consent"] == "deny"
    with pytest.raises(AuthoringContractError, match="consent"):
        _document(consent="implicit")


def test_document_loader_rejects_noncanonical_duplicate_extra_and_float_data() -> None:
    record = _document().record
    extra = deepcopy(record)
    extra["checked"] = True
    with pytest.raises(AuthoringContractError, match="additional"):
        load_document(canonical_json_bytes(extra))

    noncanonical = json.dumps(record, ensure_ascii=False, indent=1).encode()
    with pytest.raises(AuthoringContractError, match="canonical"):
        load_document(noncanonical)

    duplicate = b'{"document_id":"a","document_id":"b"}'
    with pytest.raises(AuthoringContractError, match="duplicate"):
        load_document(duplicate)

    floating = canonical_json_bytes(record).replace(b'"revision":1', b'"revision":1.0')
    with pytest.raises(AuthoringContractError, match="floating-point"):
        load_document(floating)

    boolean_version = deepcopy(record)
    boolean_version["v"] = True
    with pytest.raises(AuthoringContractError, match="version must be integer 1"):
        load_document(canonical_json_bytes(boolean_version))


@pytest.mark.parametrize("unsafe", ["bad\rtext", "bad\x00text", "bad\u202etext", "\ud800"])
def test_unsafe_document_text_fails_closed(unsafe: str) -> None:
    with pytest.raises(AuthoringContractError, match="unsafe|surrogate"):
        _document(source=unsafe)


def test_sentence_unit_preserves_exact_utf8_span_and_hash() -> None:
    source = "Liczba π jest symbolem. Dalej."
    first = "Liczba π jest symbolem."
    document = _document(source=source)
    unit = build_sentence_unit(
        document,
        unit_id="unicode-1",
        kind="claim",
        start_utf8=0,
        end_utf8=len(first.encode("utf-8")),
    )
    excerpt = unit.record["source"]
    assert excerpt["text"] == first
    assert excerpt["end_utf8"] == len(first.encode("utf-8"))
    assert excerpt["sha256"] == hashlib.sha256(first.encode()).hexdigest()
    assert load_sentence_unit(unit.canonical_bytes, document=document).sha256 == unit.sha256

    pi = source.encode().index("π".encode())
    with pytest.raises(AuthoringContractError, match="UTF-8"):
        build_sentence_unit(
            document,
            unit_id="split-code-point",
            kind="claim",
            start_utf8=0,
            end_utf8=pi + 1,
        )


def test_old_unit_is_rejected_against_a_new_document_revision_or_source() -> None:
    old_document = _document(revision=1)
    unit = _unit(old_document)
    new_revision = _document(revision=2)
    changed_source = _document(revision=1, source=SOURCE + " Changed.")
    with pytest.raises(AuthoringContractError, match="stale"):
        load_sentence_unit(unit.canonical_bytes, document=new_revision)
    with pytest.raises(AuthoringContractError, match="stale"):
        load_sentence_unit(unit.canonical_bytes, document=changed_source)


def test_candidate_is_canonical_native_pa_and_binds_exact_unit() -> None:
    unit = _unit()
    candidate = _candidate(unit)
    record = candidate.record
    assert record["readable_formula"] == "0 = 0"
    assert record["primitive_formula"] == "eq(zero,zero)"
    assert record["binder_table"] == []
    assert record["free_variables"] == []
    assert record["assumptions"] == []
    assert record["source"] == unit.record["source"]
    assert record["alternative_readings"][0]["primitive_formula"] == (
        "eq(succ(zero),succ(zero))"
    )
    assert record["surface_kind"] == "native-pa"
    assert record["expanded_formula"] == "0 = 0"
    assert record["definition_receipts"] == []
    assert record["unit_sha256"] == unit.sha256
    assert record["binding"] == unit.record["binding"]
    assert record["ambiguities"] == ["quantifier-scope"]
    assert record["provenance"] == {
        "format": "peano-hydra-authoring-provenance",
        "v": 1,
        "kind": "model",
        "id": "qwen-fixture",
        "request_sha256": SHA_A,
        "response_sha256": SHA_B,
    }
    assert load_formalization_candidate(
        candidate.canonical_bytes, unit=unit
    ).sha256 == candidate.sha256

    other = _unit(unit_id="sentence-2")
    with pytest.raises(AuthoringContractError, match="another sentence"):
        load_formalization_candidate(candidate.canonical_bytes, unit=other)


def test_candidate_rejects_bad_provenance_ambiguities_and_non_pa_text() -> None:
    unit = _unit()
    with pytest.raises(AuthoringContractError, match="request_sha256"):
        build_formalization_candidate(
            unit,
            candidate_id="bad-model",
            statement="0 = 0",
            provenance_kind="model",
            provenance_id="qwen",
        )
    with pytest.raises(AuthoringContractError, match="only model"):
        build_formalization_candidate(
            unit,
            candidate_id="bad-human",
            statement="0 = 0",
            provenance_kind="human",
            provenance_id="author",
            request_sha256=SHA_A,
            response_sha256=SHA_B,
        )
    with pytest.raises(AuthoringContractError, match="sorted and unique"):
        build_formalization_candidate(
            unit,
            candidate_id="bad-ambiguities",
            statement="0 = 0",
            provenance_kind="rule",
            provenance_id="fixture",
            ambiguities=("z-code", "a-code"),
        )
    with pytest.raises(AuthoringContractError, match="native PA"):
        build_formalization_candidate(
            unit,
            candidate_id="not-pa",
            statement="Prime(2)",
            provenance_kind="human",
            provenance_id="author",
        )


def test_diagnostics_retain_authority_exact_span_and_native_pa_repair() -> None:
    unit = _unit()
    start = unit.record["source"]["start_utf8"]
    end = start + len("Every".encode())
    for authority in ("untrusted-solver", "untrusted-model"):
        diagnostic = build_diagnostic(
            unit,
            diagnostic_id=f"diag-{authority}",
            code="possible-quantifier-error",
            severity="warning",
            authority=authority,
            message="Check the quantifier scope.",
            start_utf8=start,
            end_utf8=end,
            suggested_statement="0=0",
        )
        record = diagnostic.record
        assert record["authority"] == authority
        assert record["source"]["text"] == "Every"
        assert record["suggested_statement"] == "0 = 0"
        assert load_diagnostic(diagnostic.canonical_bytes, unit=unit).record == record

    unavailable = set(DIAGNOSTIC_AUTHORITIES) - {
        "untrusted-solver",
        "untrusted-model",
    }
    for trusted in unavailable:
        with pytest.raises(AuthoringContractError, match="dedicated authenticated builder"):
            build_diagnostic(
                unit,
                diagnostic_id=f"forged-{trusted}",
                code="checked-counterproof",
                severity="error",
                authority=trusted,
                message="A client cannot mint trusted authority.",
                start_utf8=start,
                end_utf8=end,
                evidence_sha256=SHA_A,
                suggested_statement="0 = 0",
            )

    forged = build_diagnostic(
        unit,
        diagnostic_id="forged-component-label",
        code="possible-quantifier-error",
        severity="warning",
        authority="untrusted-model",
        message="An untrusted diagnostic.",
        start_utf8=start,
        end_utf8=end,
    ).record
    for trusted in (
        "parser",
        "definition-expander",
        "library-graph",
        "bounded-evaluator",
    ):
        forged["authority"] = trusted
        with pytest.raises(
            AuthoringContractError, match="dedicated authenticated builder"
        ):
            load_diagnostic(canonical_json_bytes(forged), unit=unit)

    kernel = build_kernel_diagnostic(
        unit,
        TARGET,
        PROOF,
        diagnostic_id="kernel-replay",
        start_utf8=start,
        end_utf8=end,
        suggested_statement="0 = 0",
    )
    with pytest.raises(AuthoringContractError, match="requires"):
        load_diagnostic(kernel.canonical_bytes, unit=unit)
    assert load_diagnostic(
        kernel.canonical_bytes,
        unit=unit,
        original_formula=TARGET,
        proof=PROOF,
    ).record == kernel.record
    assert kernel.record["code"] == "kernel-verified-statement"
    assert kernel.record["severity"] == "info"
    assert "does not verify that the source prose" in kernel.record["message"]

    for field_name, forged_value in (
        ("code", "source-prose-is-false"),
        ("severity", "error"),
        ("message", "The kernel says that the author's prose is false."),
        ("source", authoring._diagnostic_excerpt(unit, start, end + 1)),
    ):
        forged_kernel = deepcopy(kernel.record)
        forged_kernel[field_name] = forged_value
        with pytest.raises(AuthoringContractError, match="fresh kernel evidence"):
            load_diagnostic(
                canonical_json_bytes(forged_kernel),
                unit=unit,
                original_formula=TARGET,
                proof=PROOF,
            )

    with pytest.raises(AuthoringContractError, match="inconsistent|differs"):
        build_kernel_diagnostic(
            unit,
            Eq(Succ(Zero()), Succ(Zero())),
            EqRefl(Succ(Zero())),
            diagnostic_id="wrong-kernel-formula",
            start_utf8=start,
            end_utf8=end,
            suggested_statement="0 = 0",
        )


def test_diagnostic_tampering_and_out_of_unit_spans_fail_closed() -> None:
    unit = _unit()
    end = unit.record["source"]["end_utf8"]
    with pytest.raises(AuthoringContractError, match="outside"):
        build_diagnostic(
            unit,
            diagnostic_id="outside",
            code="scope-error",
            severity="error",
            authority="untrusted-model",
            message="Outside span.",
            start_utf8=end,
            end_utf8=end + 1,
        )
    diagnostic = build_diagnostic(
        unit,
        diagnostic_id="tampered",
        code="scope-error",
        severity="error",
        authority="untrusted-model",
        message="Bad scope.",
        start_utf8=0,
        end_utf8=5,
    )
    tampered = diagnostic.record
    tampered["source"]["text"] = "Other"
    with pytest.raises(AuthoringContractError, match="inconsistent"):
        load_diagnostic(canonical_json_bytes(tampered), unit=unit)


def test_draft_proposal_has_no_checked_authority_or_certificate_channel() -> None:
    candidate = _candidate()
    proposal = build_draft_theorem_proposal(
        candidate,
        proposal_id="proposal-1",
        name="zero_reflexive",
        readable_dependencies=(),
        optimized_dependencies=(),
        readable_source_proof="exact refl(0)\n",
        explanation="Zero equals itself.",
    )
    assert proposal.record["proof_status"] == "draft"
    assert "checked" not in proposal.record
    assert "checked_result" not in proposal.record
    assert proposal.certificate_artifact is None
    assert load_theorem_proposal(
        proposal.canonical_bytes, candidate=candidate
    ).record == proposal.record
    with pytest.raises(AuthoringContractError, match="draft"):
        load_theorem_proposal(
            proposal.canonical_bytes,
            candidate=candidate,
            original_formula=TARGET,
            proof=PROOF,
        )


def test_checked_proposal_requires_real_formula_proof_and_fresh_kernel_replay() -> None:
    candidate = _candidate()
    proposal = build_checked_theorem_proposal(
        candidate,
        TARGET,
        PROOF,
        proposal_id="proposal-checked",
        name="zero_reflexive",
        readable_dependencies=(),
        optimized_dependencies=(),
        readable_source_proof="exact refl(0)\n",
        explanation="Zero equals itself.",
    )
    record = proposal.record
    assert record["proof_status"] == "checked"
    assert "checked" not in record
    assert record["checked_result"]["kind"] == "proved"
    assert record["checked_result"]["kernel_accepted"] is True
    assert proposal.certificate_artifact is not None
    assert load_theorem_proposal(
        proposal.canonical_bytes,
        candidate=candidate,
        original_formula=TARGET,
        proof=PROOF,
    ).record == record

    with pytest.raises(AuthoringContractError, match="requires"):
        load_theorem_proposal(proposal.canonical_bytes, candidate=candidate)
    with pytest.raises(AuthoringContractError, match="real kernel Proof"):
        build_checked_theorem_proposal(
            candidate,
            TARGET,
            object(),  # type: ignore[arg-type]
            proposal_id="fake-proof",
            name="zero_reflexive",
            readable_dependencies=(),
            optimized_dependencies=(),
            readable_source_proof="exact forged\n",
            explanation="Forged.",
        )
    with pytest.raises(AuthoringContractError, match="differs"):
        build_checked_theorem_proposal(
            candidate,
            Eq(Succ(Zero()), Succ(Zero())),
            EqRefl(Succ(Zero())),
            proposal_id="wrong-goal",
            name="zero_reflexive",
            readable_dependencies=(),
            optimized_dependencies=(),
            readable_source_proof="exact refl(1)\n",
            explanation="Wrong target.",
        )
    with pytest.raises(AuthoringContractError, match="kernel check"):
        build_checked_theorem_proposal(
            candidate,
            TARGET,
            EqRefl(Succ(Zero())),
            proposal_id="wrong-proof",
            name="zero_reflexive",
            readable_dependencies=(),
            optimized_dependencies=(),
            readable_source_proof="exact refl(1)\n",
            explanation="Wrong proof.",
        )


def test_forged_or_mutated_checked_proposal_cannot_be_loaded() -> None:
    candidate = _candidate()
    draft = build_draft_theorem_proposal(
        candidate,
        proposal_id="forged",
        name="zero_reflexive",
        readable_dependencies=(),
        optimized_dependencies=(),
        readable_source_proof="exact refl(0)\n",
        explanation="Forged status.",
    ).record
    draft["proof_status"] = "checked"
    with pytest.raises(AuthoringContractError, match="missing"):
        load_theorem_proposal(canonical_json_bytes(draft), candidate=candidate)

    checked = build_checked_theorem_proposal(
        candidate,
        TARGET,
        PROOF,
        proposal_id="mutated",
        name="zero_reflexive",
        readable_dependencies=(),
        optimized_dependencies=(),
        readable_source_proof="exact refl(0)\n",
        explanation="Mutated result.",
    ).record
    checked["checked_result"]["certificate_sha256"] = SHA_A
    with pytest.raises(AuthoringContractError, match="inconsistent|differs"):
        load_theorem_proposal(
            canonical_json_bytes(checked),
            candidate=candidate,
            original_formula=TARGET,
            proof=PROOF,
        )


def test_proposal_dependencies_are_ordered_unique_and_nonrecursive() -> None:
    candidate = _candidate()
    proposal = build_draft_theorem_proposal(
        candidate,
        proposal_id="dependencies",
        name="new_fact",
        readable_dependencies=("zero_add",),
        optimized_dependencies=("add_comm", "zero_add"),
        readable_source_proof="use zero_add; use add_comm\n",
        explanation="Uses two exact earlier facts.",
    )
    assert proposal.record["readable_dependencies"] == ["zero_add"]
    assert proposal.record["optimized_dependencies"] == ["add_comm", "zero_add"]
    assert proposal.record["publication_dependencies"] == ["zero_add", "add_comm"]
    with pytest.raises(AuthoringContractError, match="duplicate"):
        build_draft_theorem_proposal(
            candidate,
            proposal_id="duplicate",
            name="new_fact",
            readable_dependencies=("zero_add", "zero_add"),
            optimized_dependencies=(),
            readable_source_proof="use zero_add\n",
            explanation="Duplicate dependency.",
        )
    with pytest.raises(AuthoringContractError, match="itself"):
        build_draft_theorem_proposal(
            candidate,
            proposal_id="recursive",
            name="new_fact",
            readable_dependencies=("new_fact",),
            optimized_dependencies=(),
            readable_source_proof="use new_fact\n",
            explanation="Recursive dependency.",
        )


def test_record_carriers_cannot_be_constructed_or_mutated_by_callers() -> None:
    for carrier in (
        AuthoringDocument,
        ExportEvent,
        SentenceUnit,
        FormalizationCandidate,
        ProofAttempt,
        LifecycleEvent,
        TheoremProposal,
    ):
        with pytest.raises(AuthoringContractError, match="checked builders/loaders"):
            carrier(b"{}")
    document = _document()
    with pytest.raises(AttributeError, match="immutable"):
        document._json = b"{}"  # type: ignore[misc]


def test_defined_surface_reuses_registered_capture_safe_expander() -> None:
    candidate = build_formalization_candidate(
        _unit(),
        candidate_id="defined-reading",
        statement="Prime(2)",
        surface_kind="defined-pa",
        provenance_kind="human",
        provenance_id="author",
    )
    record = candidate.record
    assert record["surface_kind"] == "defined-pa"
    assert record["readable_formula"] == "Prime(2)"
    assert record["expanded_formula"] != record["readable_formula"]
    assert record["primitive_formula"].startswith("and(")
    assert record["definition_receipts"][0]["id"].startswith(
        "peano-lab.defined-predicates:v"
    )
    assert any(item["id"] == "PD0004" for item in record["definition_receipts"])

    with pytest.raises(AuthoringContractError, match="must use"):
        build_formalization_candidate(
            _unit(),
            candidate_id="fake-defined",
            statement="0 = 0",
            surface_kind="defined-pa",
            provenance_kind="human",
            provenance_id="author",
        )


def test_candidate_derives_binders_assumptions_and_primitive_expansion() -> None:
    candidate = build_formalization_candidate(
        _unit(),
        candidate_id="quantified-reading",
        statement="forall n. 0 = 0 -> n = n",
        provenance_kind="rule",
        provenance_id="fixture",
    )
    record = candidate.record
    assert record["binder_table"] == [
        {"index": 0, "path": "$", "quantifier": "forall", "name": "x", "depth": 0}
    ]
    assert record["free_variables"] == []
    assert record["assumptions"][0]["readable_formula"] == "0 = 0"
    assert record["assumptions"][0]["primitive_formula"] == "eq(zero,zero)"
    assert record["primitive_formula"].startswith("forall(imp(")


def test_malformed_nested_diagnostic_source_fails_with_contract_error() -> None:
    unit = _unit()
    diagnostic = build_diagnostic(
        unit,
        diagnostic_id="bad-source-shape",
        code="scope-error",
        severity="error",
        authority="untrusted-model",
        message="Malformed transport attack.",
        start_utf8=0,
        end_utf8=5,
    ).record
    diagnostic["source"] = None
    with pytest.raises(AuthoringContractError, match="source excerpt"):
        load_diagnostic(canonical_json_bytes(diagnostic), unit=unit)


def test_proof_attempt_is_revision_bound_untrusted_and_lineage_chained() -> None:
    candidate = _candidate()
    first = build_proof_attempt(
        candidate,
        attempt_id="attempt-1",
        lineage_id="lineage-1",
        engine="model",
        outcome="candidate-proof",
        readable_script="exact refl(0)\n",
        provenance_kind="model",
        provenance_id="qwen",
        request_sha256=SHA_A,
        response_sha256=SHA_B,
        transcript_receipts=(("model-transcript", SHA_A),),
    )
    assert "checked" not in first.record
    assert load_proof_attempt(first.canonical_bytes, candidate=candidate).sha256 == first.sha256
    second = build_proof_attempt(
        candidate,
        attempt_id="attempt-2",
        lineage_id="lineage-1",
        parent_attempt=first,
        engine="symbolic",
        outcome="search-exhausted",
        readable_script="auto\n",
        provenance_kind="rule",
        provenance_id="hydra",
    )
    assert second.record["lineage"]["parent_attempt_sha256"] == first.sha256
    with pytest.raises(AuthoringContractError, match="parent"):
        load_proof_attempt(second.canonical_bytes, candidate=candidate)
    assert load_proof_attempt(
        second.canonical_bytes, candidate=candidate, parent_attempt=first
    ).sha256 == second.sha256


def test_checked_proposal_retains_full_submitted_proof_metrics() -> None:
    candidate = _candidate()
    proposal = build_checked_theorem_proposal(
        candidate,
        TARGET,
        PROOF,
        proposal_id="pareto",
        name="zero_reflexive",
        readable_dependencies=(),
        optimized_dependencies=(),
        readable_source_proof="exact refl(0)\n",
        explanation="Exact replay metrics.",
        mutation_result_receipts=(("wrong-target", SHA_A),),
        transcript_receipts=(("search", SHA_B),),
        documentation_receipts=(
            ("explorer", SHA_A),
            ("book", SHA_B),
        ),
    )
    metrics = proposal.record["proof_metrics"]
    assert metrics == {
        "claim": "submitted",
        "certificate_sha256": proposal.record["checked_result"]["certificate_sha256"],
        "certificate_nodes": 1,
        "distinct_proof_objects": 1,
        "cut_nodes": 0,
        "certificate_bytes": len(proposal.certificate_artifact),
        "max_depth": 1,
        "replay_observation": "accepted",
        "readable_script_utf8_bytes": len("exact refl(0)\n".encode()),
    }
    assert [item["target"] for item in proposal.record["documentation_receipts"]] == [
        "book",
        "explorer",
    ]


def test_lifecycle_events_require_reviewed_registry_membership_and_exact_chain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = _candidate()
    proposal = build_checked_theorem_proposal(
        candidate,
        TARGET,
        PROOF,
        proposal_id="lifecycle",
        name="zero_reflexive",
        readable_dependencies=(),
        optimized_dependencies=(),
        readable_source_proof="exact refl(0)\n",
        explanation="Lifecycle fixture.",
    )
    session_owner = "browser-session-1"
    acceptance_record = {
        "format": "peano-hydra-authoring-lifecycle-event",
        "v": 1,
        "event_id": "accept-statement",
        "proposal_sha256": proposal.sha256,
        "previous_event_sha256": None,
        "from_state": "prose_only",
        "to_state": "formalized_unproved",
        "authority": "human-reviewer",
        "actor_id": "reviewer-1",
        "session_owner_id": session_owner,
        "evidence_sha256": SHA_B,
    }
    acceptance_raw, acceptance_root, acceptance_deposit = _registry_event(
        "lifecycle", (), acceptance_record
    )
    with pytest.raises(AuthoringContractError, match="reviewed registry"):
        load_lifecycle_event(
            acceptance_raw,
            proposal=proposal,
            expected_registry_sha256=acceptance_root,
            expected_actor_id="reviewer-1",
            expected_session_owner_id=session_owner,
        )
    monkeypatch.setitem(
        authoring._REVIEWED_EVENT_REGISTRIES,
        acceptance_root,
        acceptance_deposit,
    )
    with pytest.raises(AuthoringContractError, match="unauthenticated"):
        load_lifecycle_event(
            acceptance_raw,
            proposal=proposal,
            expected_registry_sha256=acceptance_root,
            expected_actor_id="forged-reviewer",
            expected_session_owner_id=session_owner,
        )
    acceptance = load_lifecycle_event(
        acceptance_raw,
        proposal=proposal,
        expected_registry_sha256=acceptance_root,
        expected_actor_id="reviewer-1",
        expected_session_owner_id=session_owner,
    )
    assert acceptance.record["sequence"] == 0

    proved_record = {
        "format": "peano-hydra-authoring-lifecycle-event",
        "v": 1,
        "event_id": "kernel-proved",
        "proposal_sha256": proposal.sha256,
        "previous_event_sha256": acceptance.sha256,
        "from_state": "formalized_unproved",
        "to_state": "proved",
        "authority": "kernel",
        "actor_id": "kernel-1",
        "session_owner_id": session_owner,
        "evidence_sha256": proposal.record["checked_result"]["replay_evidence_sha256"],
    }
    proved_raw, proved_root, proved_deposit = _registry_event(
        "lifecycle", acceptance_deposit, proved_record
    )
    monkeypatch.setitem(
        authoring._REVIEWED_EVENT_REGISTRIES,
        proved_root,
        proved_deposit,
    )
    proved = load_lifecycle_event(
        proved_raw,
        proposal=proposal,
        expected_registry_sha256=proved_root,
        expected_actor_id="kernel-1",
        expected_session_owner_id=session_owner,
        previous_event=acceptance,
    )
    assert proved.record["to_state"] == "proved"
    assert proved.record["sequence"] == 1

    reviewed_record = {
        "format": "peano-hydra-authoring-lifecycle-event",
        "v": 1,
        "event_id": "review-proposal",
        "proposal_sha256": proposal.sha256,
        "previous_event_sha256": proved.sha256,
        "from_state": "proved",
        "to_state": "reviewed",
        "authority": "human-reviewer",
        "actor_id": "reviewer-2",
        "session_owner_id": session_owner,
        "evidence_sha256": SHA_B,
    }
    reviewed_raw, reviewed_root, reviewed_deposit = _registry_event(
        "lifecycle", proved_deposit, reviewed_record
    )
    monkeypatch.setitem(
        authoring._REVIEWED_EVENT_REGISTRIES,
        reviewed_root,
        reviewed_deposit,
    )
    reviewed = load_lifecycle_event(
        reviewed_raw,
        proposal=proposal,
        expected_registry_sha256=reviewed_root,
        expected_actor_id="reviewer-2",
        expected_session_owner_id=session_owner,
        previous_event=proved,
    )

    admitted_record = {
        "format": "peano-hydra-authoring-lifecycle-event",
        "v": 1,
        "event_id": "admit-proposal",
        "proposal_sha256": proposal.sha256,
        "previous_event_sha256": reviewed.sha256,
        "from_state": "reviewed",
        "to_state": "admitted",
        "authority": "catalog-administrator",
        "actor_id": "catalog-admin-1",
        "session_owner_id": session_owner,
        "evidence_sha256": SHA_A,
    }
    admitted_raw, admitted_root, admitted_deposit = _registry_event(
        "lifecycle", reviewed_deposit, admitted_record
    )
    monkeypatch.setitem(
        authoring._REVIEWED_EVENT_REGISTRIES,
        admitted_root,
        admitted_deposit,
    )
    admitted = load_lifecycle_event(
        admitted_raw,
        proposal=proposal,
        expected_registry_sha256=admitted_root,
        expected_actor_id="catalog-admin-1",
        expected_session_owner_id=session_owner,
        previous_event=reviewed,
    )

    with pytest.raises(AuthoringContractError, match="unique head"):
        load_lifecycle_event(
            acceptance_raw,
            proposal=proposal,
            expected_registry_sha256=admitted_root,
            expected_actor_id="reviewer-1",
            expected_session_owner_id=session_owner,
        )

    fork_record = dict(proved_record)
    fork_record["event_id"] = "kernel-proved-fork"
    fork_record["actor_id"] = "kernel-fork"
    fork_raw, fork_root, fork_deposit = _registry_event(
        "lifecycle", acceptance_deposit, fork_record
    )
    monkeypatch.setitem(
        authoring._REVIEWED_EVENT_REGISTRIES,
        fork_root,
        fork_deposit,
    )
    with pytest.raises(AuthoringContractError, match="fork"):
        load_lifecycle_event(
            fork_raw,
            proposal=proposal,
            expected_registry_sha256=fork_root,
            expected_actor_id="kernel-fork",
            expected_session_owner_id=session_owner,
            previous_event=acceptance,
        )

    duplicate_record = dict(proved_record)
    duplicate_record["event_id"] = "accept-statement"
    duplicate_raw, duplicate_root, duplicate_deposit = _registry_event(
        "lifecycle", acceptance_deposit, duplicate_record
    )
    monkeypatch.setitem(
        authoring._REVIEWED_EVENT_REGISTRIES,
        duplicate_root,
        duplicate_deposit,
    )
    with pytest.raises(AuthoringContractError, match="duplicate"):
        load_lifecycle_event(
            duplicate_raw,
            proposal=proposal,
            expected_registry_sha256=duplicate_root,
            expected_actor_id="kernel-1",
            expected_session_owner_id=session_owner,
            previous_event=acceptance,
        )

    export_record = {
        "format": "peano-hydra-authoring-export-event",
        "v": 1,
        "export_id": "export-1",
        "proposal_sha256": proposal.sha256,
        "admitted_event_sha256": admitted.sha256,
        "actor_id": "exporter-1",
        "session_owner_id": session_owner,
        "patch_root_sha256": SHA_B,
        "destination": "nasqret/vietnam2026:peano-lab",
        "mode": "patch-only",
        "evidence_sha256": SHA_A,
    }
    export_raw, export_root, export_deposit = _registry_event(
        "export", (), export_record
    )
    with pytest.raises(AuthoringContractError, match="reviewed registry"):
        load_export_event(
            export_raw,
            proposal=proposal,
            admitted_event=admitted,
            expected_registry_sha256=export_root,
            expected_actor_id="exporter-1",
            expected_session_owner_id=session_owner,
        )
    monkeypatch.setitem(
        authoring._REVIEWED_EXPORT_REGISTRIES,
        export_root,
        export_deposit,
    )
    with pytest.raises(AuthoringContractError, match="binding"):
        load_export_event(
            export_raw,
            proposal=proposal,
            admitted_event=admitted,
            expected_registry_sha256=export_root,
            expected_actor_id="wrong-exporter",
            expected_session_owner_id=session_owner,
        )
    with pytest.raises(AuthoringContractError, match="binding"):
        load_export_event(
            export_raw,
            proposal=proposal,
            admitted_event=admitted,
            expected_registry_sha256=export_root,
            expected_actor_id="exporter-1",
            expected_session_owner_id="wrong-session",
        )
    exported = load_export_event(
        export_raw,
        proposal=proposal,
        admitted_event=admitted,
        expected_registry_sha256=export_root,
        expected_actor_id="exporter-1",
        expected_session_owner_id=session_owner,
    )
    assert exported.record["mode"] == "patch-only"
    assert exported.record["sequence"] == 0
