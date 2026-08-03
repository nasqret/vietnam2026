"""Frozen semantic-profile and claim-boundary tests for Peano Hydra H0.1a."""

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

from peano_lab.kernel.formulas import Eq, Forall  # noqa: E402
from peano_lab.kernel.terms import Var, Zero  # noqa: E402
import training.peano_hydra.profile as profile_module  # noqa: E402
from training.peano_hydra.profile import (  # noqa: E402
    SEMANTIC_PROFILE_FORMAT,
    SEMANTIC_PROFILE_ID,
    SEMANTIC_PROFILE_VERSION,
    SemanticProfileError,
    canonical_profile_theorem,
    evidence_kind,
    semantic_profile,
    semantic_profile_identity,
    semantic_profile_sha256,
    validate_semantic_profile,
    well_scoped_formula,
)


EXPECTED_PROFILE_SHA256 = (
    "058b1644b066967919dae092e5e562b8845e4dd8415fff31d7cd209d51bc9e43"
)


def _canonical_document(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def test_registered_profile_is_canonical_detached_and_digest_pinned() -> None:
    first = semantic_profile()
    second = semantic_profile()

    assert first == second
    assert first is not second
    assert first["format"] == SEMANTIC_PROFILE_FORMAT
    assert first["v"] == SEMANTIC_PROFILE_VERSION
    assert first["id"] == SEMANTIC_PROFILE_ID
    assert profile_module.SEMANTIC_PROFILE_PATH.read_bytes() == _canonical_document(first)
    assert semantic_profile_sha256() == EXPECTED_PROFILE_SHA256
    assert semantic_profile_identity() == {
        "format": SEMANTIC_PROFILE_FORMAT,
        "v": SEMANTIC_PROFILE_VERSION,
        "id": SEMANTIC_PROFILE_ID,
        "sha256": EXPECTED_PROFILE_SHA256,
    }

    first["v"] = 99
    assert semantic_profile()["v"] == SEMANTIC_PROFILE_VERSION


def test_profile_matches_exact_kernel_axioms_rules_and_trust_boundary() -> None:
    profile = semantic_profile()
    axioms = profile["arithmetic"]["axioms"]
    assert [row["name"] for row in axioms] == [
        "PA1",
        "PA2",
        "PA3",
        "PA4",
        "PA5",
        "PA6",
    ]
    assert [row["formula"] for row in axioms] == [
        "∀ x. ¬S x = 0",
        "∀ x. ∀ y. S x = S y → x = y",
        "∀ x. x + 0 = x",
        "∀ x. ∀ y. x + S y = S (x + y)",
        "∀ x. x · 0 = 0",
        "∀ x. ∀ y. x · S y = x · y + x",
    ]

    calculus = profile["calculus"]
    constructors = calculus["proof_constructors"]
    assert constructors == [
        name
        for name in profile_module.kernel_proofs.__all__
        if name not in {"Proof", "DNE"}
    ]
    assert set(calculus["rules"]) == set(constructors)
    assert "DNE" not in constructors
    assert calculus["classical"] is False
    assert calculus["dne"] is False
    assert profile["authority"] == {
        "certificate_representation": "python-dataclass-repr-with-cut-v2",
        "classical_checker": "forbidden",
        "context": "empty",
        "goal": "original",
        "positive": "peano_lab.kernel.checker.check",
    }
    assert profile["arithmetic"]["induction"]["kind"] == (
        "unrestricted-formula-schema"
    )
    substitution = profile["substitution"]
    assert substitution["shift_variable_case"].endswith("otherwise-unchanged")
    assert "cutoff+1" in substitution["shift_formula_structural_recursion"]
    assert "depth+1" in substitution["formula_structural_recursion"]
    assert substitution["shift_term_structural_recursion"] == (
        "Zero:unchanged;Succ:recurse;Add/Mul:recurse-both"
    )


def test_profile_has_no_decision_or_negative_theoremhood_claim() -> None:
    profile = semantic_profile()
    claim = profile["claim"]
    evidence = profile["evidence"]

    assert claim["kind"] == "sound-theorem-prover"
    assert claim["decision_procedure"] is False
    assert claim["decision_fragment"] is None
    assert claim["decision_resource_bounds"] is None
    assert claim["not_theorem_supported"] is False
    assert evidence["kinds"] == ["proved", "unknown"]
    assert evidence["not_theorem"] == {
        "publication": "forbidden",
        "supported": False,
    }
    assert evidence["schema_status"] == "required-field-draft"
    assert evidence["additional_fields_policy"] == "not-yet-frozen"
    assert evidence["hash_preimages"] == "not-yet-frozen"
    assert "negative_evidence_sha256" in evidence["unknown"]["forbidden"]
    assert profile["translations"]["external"] == []


def test_surface_aliases_and_alpha_names_canonicalize_deterministically() -> None:
    ascii_source = "forall n m. ~(n <= m) -> n * 0 = 0 /\\ m = m"
    unicode_source = "∀ a b. ¬(a ≤ b) → a · 0 = 0 ∧ b = b"
    expected = "∀ x. ∀ y. ¬x ≤ y → x · 0 = 0 ∧ y = y"

    assert canonical_profile_theorem(ascii_source) == expected
    assert canonical_profile_theorem(unicode_source) == expected
    assert canonical_profile_theorem(expected) == expected
    assert canonical_profile_theorem("forall q. q = q") == "∀ x. x = x"


def test_profile_freezes_complete_preparser_admission_contract() -> None:
    profile = semantic_profile()
    assert profile["input"]["operational_admission"] == {
        "character_measure": "unicode-code-points",
        "decision_claim": False,
        "decimal_numeral_comparison": "normalized-base10-value",
        "forbidden_unicode_categories": ["Cc", "Cf", "Cs", "Zl", "Zp"],
        "hash_character": "forbidden",
        "kind": "source-preflight-v1",
        "line_policy": "one-line-no-outer-whitespace",
        "max_decimal_numeral": 256,
        "max_source_characters": 8_192,
        "nonempty": True,
        "numeral_literal_boundary": (
            "not-preceded-by-word-character-apostrophe-or-hash"
        ),
    }
    assert profile["claim"]["decision_resource_bounds"] is None
    numeral = next(
        item
        for item in profile["translations"]["surface"]
        if item["name"] == "numeral"
    )
    assert numeral["domain"] == "0<=n<=256"
    assert canonical_profile_theorem("256 = 256") == "256 = 256"
    assert canonical_profile_theorem("٢٥٦ = ٢٥٦") == "256 = 256"
    assert canonical_profile_theorem("２５６ = ２５６") == "256 = 256"
    for source in ("٢٥٧ = ٢٥٧", "２５７ = ２５７"):
        with pytest.raises(SemanticProfileError, match="resource-dangerous numeral"):
            canonical_profile_theorem(source)

    padding = " " * (profile_module.MAX_INPUT - len("0=0"))
    exact_transport_limit = "0" + padding + "=0"
    assert len(exact_transport_limit) == profile_module.MAX_INPUT
    assert canonical_profile_theorem(exact_transport_limit) == "0 = 0"


@pytest.mark.parametrize("field", ["MAX_INPUT", "MAX_NUMERAL"])
def test_profile_loader_rejects_live_admission_limit_drift(
    field: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(profile_module, field, getattr(profile_module, field) + 1)
    with pytest.raises(SemanticProfileError, match="target admission"):
        semantic_profile()


@pytest.mark.parametrize(
    "source,match",
    [
        ("n = n", "must be closed"),
        ("#0 = #0", "explicit de Bruijn"),
        ("forall x. #0 = #0", "explicit de Bruijn"),
        ("forall x. #1 = #1", "explicit de Bruijn"),
        (" 0 = 0", "one line"),
        ("0 = 0\n", "one line"),
        ("0 = 0\u200b", "unsafe character"),
        ("257 = 257", "resource-dangerous numeral"),
        ("forall. 0 = 0", "invalid profile theorem"),
    ],
)
def test_profile_theorem_admission_rejects_open_or_unsafe_inputs(
    source: str,
    match: str,
) -> None:
    with pytest.raises(SemanticProfileError, match=match):
        canonical_profile_theorem(source)


def test_profile_theorem_admission_applies_transport_bound_before_parsing() -> None:
    with pytest.raises(SemanticProfileError, match="transport bound"):
        canonical_profile_theorem("0" * (profile_module.MAX_INPUT + 1))


def test_profile_theorem_admission_handles_python_int_digit_limit() -> None:
    huge_numeral = "9" * 5_000
    assert len(huge_numeral + " = 0") < profile_module.MAX_INPUT
    with pytest.raises(SemanticProfileError, match="resource-dangerous numeral"):
        canonical_profile_theorem(huge_numeral + " = 0")


def test_structural_scope_rejects_free_indices_and_malformed_subclasses() -> None:
    assert well_scoped_formula(Eq(Zero(), Zero())) is True
    assert well_scoped_formula(Eq(Var(0), Var(0))) is False
    assert well_scoped_formula(Forall(Eq(Var(0), Var(0)))) is True
    assert well_scoped_formula(Forall(Eq(Var(1), Var(1)))) is False
    assert well_scoped_formula(Eq(Var(0), Var(0)), depth=1) is True

    class ForgedEq(Eq):
        pass

    assert well_scoped_formula(ForgedEq(Zero(), Zero())) is False
    with pytest.raises(ValueError, match="scope depth"):
        well_scoped_formula(Eq(Zero(), Zero()), depth=True)


def test_registered_schema_rejects_every_representative_mutation() -> None:
    mutations: list[dict[str, object]] = []

    extra = semantic_profile()
    extra["extra"] = True
    mutations.append(extra)

    wrong_version = semantic_profile()
    wrong_version["v"] = 2
    mutations.append(wrong_version)

    classical = semantic_profile()
    classical["calculus"]["classical"] = True
    mutations.append(classical)

    dropped_rule = semantic_profile()
    del dropped_rule["calculus"]["rules"]["Cut"]
    mutations.append(dropped_rule)

    negative_kind = semantic_profile()
    negative_kind["evidence"]["kinds"].append("not_theorem")
    mutations.append(negative_kind)

    external_translation = semantic_profile()
    external_translation["translations"]["external"].append("vampire")
    mutations.append(external_translation)

    bool_as_integer = semantic_profile()
    bool_as_integer["binding"]["top_level_scope_depth"] = False
    mutations.append(bool_as_integer)

    for mutation in mutations:
        with pytest.raises(SemanticProfileError, match="registered v1"):
            validate_semantic_profile(mutation)


@pytest.mark.parametrize("mutation", ["whitespace", "duplicate", "nan"])
def test_artifact_loader_rejects_noncanonical_or_non_strict_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    raw = profile_module.SEMANTIC_PROFILE_PATH.read_bytes()
    if mutation == "whitespace":
        bad = b" " + raw
    elif mutation == "duplicate":
        bad = raw.replace(b'{\n', b'{\n  "v": 1,\n', 1)
    else:
        bad = raw.replace(
            b'"top_level_scope_depth": 0',
            b'"top_level_scope_depth": NaN',
            1,
        )
    path = tmp_path / "semantic-profile-v1.json"
    path.write_bytes(bad)
    monkeypatch.setattr(profile_module, "SEMANTIC_PROFILE_PATH", path)

    with pytest.raises(SemanticProfileError):
        semantic_profile()


def test_runtime_alignment_rejects_kernel_axiom_or_constructor_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_axiom = profile_module.axiom_formula

    def missing_pa3(name: str):
        return None if name == "PA3" else original_axiom(name)

    monkeypatch.setattr(profile_module, "axiom_formula", missing_pa3)
    with pytest.raises(SemanticProfileError, match="PA3"):
        semantic_profile()
    monkeypatch.setattr(profile_module, "axiom_formula", original_axiom)

    original_inventory = profile_module.kernel_proofs.__all__
    monkeypatch.setattr(
        profile_module.kernel_proofs,
        "__all__",
        [*original_inventory, "ForgedRule"],
    )
    with pytest.raises(SemanticProfileError, match="constructors"):
        semantic_profile()


def test_evidence_mapping_cannot_turn_failure_into_negative_or_unchecked_proof() -> None:
    assert evidence_kind(proved=True, kernel_checked=True) == "proved"
    assert evidence_kind(proved=False, kernel_checked=False) == "unknown"
    with pytest.raises(SemanticProfileError, match="requires"):
        evidence_kind(proved=True, kernel_checked=False)
    with pytest.raises(SemanticProfileError, match="cannot be published"):
        evidence_kind(proved=False, kernel_checked=True)
    with pytest.raises(TypeError, match="Booleans"):
        evidence_kind(proved=1, kernel_checked=True)  # type: ignore[arg-type]


def test_semantic_digest_is_value_based_not_pretty_file_hash() -> None:
    artifact_sha256 = hashlib.sha256(
        profile_module.SEMANTIC_PROFILE_PATH.read_bytes()
    ).hexdigest()
    assert artifact_sha256 != semantic_profile_sha256()
