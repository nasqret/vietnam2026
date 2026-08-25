"""Readable Lean modules remain conservative over fully checked certificates."""

from __future__ import annotations

from hashlib import sha256
import re

import pytest

from peano_lab.kernel.formulas import And, Eq, parse_formula, pretty_formula
from peano_lab.kernel.proofs import AndIntro, EqRefl
from peano_lab.kernel.terms import Succ, Zero
from peano_lab.library.defined_syntax import (
    DEFINITIONS_BY_NAME,
    parse_defined_formula,
)
from peano_lab.library.lean import formula_to_lean
from peano_lab.library import lean_presentation
from peano_lab.library.lean_certified import LeanCertificateError
from peano_lab.library.lean_presentation import (
    MAX_DEPENDENCIES,
    MAX_PREVIEW_BYTES,
    MAX_SCRIPT_BYTES,
    MAX_SCRIPT_LINES,
    MAX_SOURCE_BYTES,
    MAX_SUMMARY_BYTES,
    PRESENTATION_SCHEMA,
    SUPPORTED_ALIASES,
    LeanPresentationError,
    build_checked_presentation,
    preview_checked_presentation,
    readable_formula,
)
from peano_lab.library.proof_bundle import BundleNode, ProofBundle
from peano_lab.library.theorems import get, replay


ZERO = Zero()
ZERO_EQ_ZERO = Eq(ZERO, ZERO)


def _simple(**kwargs: object):
    return build_checked_presentation(
        "zero_reflexive",
        ZERO_EQ_ZERO,
        EqRefl(ZERO),
        **kwargs,
    )


def test_small_certificate_is_separated_from_the_readable_checked_theorem() -> None:
    presentation = _simple()

    assert presentation.name == "zero_reflexive"
    assert presentation.exact_statement == "0 = 0"
    assert presentation.readable_statement == "0 = 0"
    assert presentation.notation_module == "PeanoLab.Presentation"
    assert presentation.notation_relative_path == "PeanoLab/Presentation.lean"
    assert re.fullmatch(
        r"PeanoLab\.Generated\.ZeroReflexive_[0-9a-f]{16}\.Certificate",
        presentation.certificate_module,
    )
    assert presentation.presentation_module.endswith(".Theorem")
    assert f"namespace {presentation.certificate_module}" in presentation.certificate_code
    assert "private def " in presentation.certificate_code
    assert "private def " not in presentation.presentation_code
    assert f"import {presentation.certificate_module}" in presentation.presentation_code
    assert f"namespace {presentation.presentation_module}" in presentation.presentation_code
    assert "open PeanoLab.Presentation" in presentation.presentation_code
    assert f"exact {presentation.certificate_module}.«zero_reflexive»" in (
        presentation.presentation_code
    )
    assert len(presentation.presentation_code.splitlines()) < 20
    assert "PeanoLab.Artifact.check_sound accepted" in presentation.certificate_code


def test_three_source_files_are_deterministic_lf_complete_and_dependency_ordered() -> None:
    first = _simple()
    second = _simple()

    assert first == second
    assert [path for path, _ in first.files()] == [
        first.notation_relative_path,
        first.certificate_relative_path,
        first.presentation_relative_path,
    ]
    assert len({path for path, _ in first.files()}) == 3
    for path, content in first.files():
        assert path.startswith("PeanoLab/")
        assert path.endswith(".lean")
        assert ".." not in path
        assert content.endswith("\n")
        assert "\r" not in content


def test_manifest_binds_exact_file_hashes_and_does_not_claim_authority() -> None:
    presentation = _simple()
    manifest = presentation.manifest

    assert manifest["schema"] == PRESENTATION_SCHEMA
    assert manifest["name"] == "zero_reflexive"
    assert manifest["edition"] == "stable"
    assert manifest["exact_ast_equivalence"] is True
    assert manifest["proof_mode"] == "certificate"
    assert all(value is False for value in manifest["authority"].values())
    assert manifest["structure"] == {
        "term_nodes": 1,
        "formula_nodes": 1,
        "proof_nodes": 1,
        "bundle_nodes": 0,
        "private_declarations": 4,
    }
    records = manifest["files"]
    for record, (path, content) in zip(records, presentation.files(), strict=True):
        encoded = content.encode("utf-8")
        assert record["relative_path"] == path
        assert record["bytes"] == len(encoded)
        assert record["sha256"] == sha256(encoded).hexdigest()


def test_content_address_changes_with_edition_and_exact_certificate() -> None:
    stable = _simple()
    alpha = _simple(edition="alpha")
    unaudited = _simple(include_axiom_audit=False)

    assert stable.certificate_module != alpha.certificate_module
    assert stable.certificate_relative_path != alpha.certificate_relative_path
    assert stable.presentation_module != alpha.presentation_module
    assert f"namespace {stable.presentation_module}" in stable.presentation_code
    assert f"namespace {alpha.presentation_module}" in alpha.presentation_code
    assert stable.certificate_module != unaudited.certificate_module
    assert "#print axioms" not in unaudited.certificate_code
    assert "#print axioms" not in unaudited.presentation_code


@pytest.mark.parametrize("name", ("_123", "__", "prime'helper"))
def test_existing_legal_names_still_have_safe_importable_module_families(
    name: str,
) -> None:
    presentation = build_checked_presentation(name, ZERO_EQ_ZERO, EqRefl(ZERO))
    family = presentation.certificate_module.split(".")[-2]

    assert re.fullmatch(r"[A-Za-z][A-Za-z0-9]*_[0-9a-f]{16}", family)


@pytest.mark.parametrize("name", ("zero_add", "add_comm"))
def test_real_public_certificates_have_small_complete_readable_facades(name: str) -> None:
    specification = get(name)
    assert specification is not None
    checked = replay(name)

    presentation = build_checked_presentation(
        name,
        checked.formula,
        checked.certificate,
        source_statement=specification.statement,
        script=specification.script,
        dependencies=specification.dependencies,
        summary=specification.summary,
    )

    assert presentation.exact_statement == formula_to_lean(checked.formula)
    assert presentation.manifest["structure"]["proof_nodes"] > 0
    assert len(presentation.presentation_code.splitlines()) < 20
    assert "-- Original Peano tactic script:" in presentation.certificate_code
    assert re.search(
        r"\bsorry\b|\bnative_decide\b|^\s*axiom\s+",
        presentation.certificate_code + presentation.presentation_code,
        re.MULTILINE,
    ) is None


def test_prime_statement_retains_exact_binder_names_and_constructive_aliases() -> None:
    specification = get("prime_unbounded")
    assert specification is not None
    formula = parse_formula(specification.statement)

    assert readable_formula(formula, source_statement=specification.statement) == (
        "∀ n : Nat, ∃ p : Nat, Lt n p ∧ Prime p"
    )


def test_real_fta_statement_compacts_reviewed_finite_coding_without_replay() -> None:
    specification = get("fundamental_theorem_of_arithmetic")
    assert specification is not None
    formula = parse_formula(specification.statement)
    readable = readable_formula(formula, source_statement=specification.statement)

    for alias in ("Lt", "BetaAt", "Product", "AllPrime", "Sorted"):
        assert f"{alias} " in readable
    assert len(readable) < len(formula_to_lean(formula)) // 3


@pytest.mark.parametrize("alias", SUPPORTED_ALIASES)
def test_every_supported_lean_alias_matches_its_reviewed_exact_definition(
    alias: str,
) -> None:
    definition = DEFINITIONS_BY_NAME[alias]
    source = (
        "forall "
        + " ".join(definition.parameters)
        + ". "
        + definition.template_source
    )
    formula = parse_formula(source)
    readable = readable_formula(formula, source_statement=source)

    assert f"{alias} " in readable
    assert f"def {alias} " in _simple().notation_code


def test_unsupported_reviewed_alias_falls_back_to_exact_statement() -> None:
    definition = DEFINITIONS_BY_NAME["Even"]
    source = f"forall n. {definition.template_source}"
    formula = parse_formula(source)

    assert readable_formula(formula, source_statement=source) == formula_to_lean(formula)


def test_constructive_quadratic_residue_disjunction_is_never_replaced_by_iff() -> None:
    formula = parse_defined_formula(
        "forall p q. (QRes(p,q) /\\ QRes(q,p)) \\/ "
        "(~QRes(p,q) /\\ ~QRes(q,p))"
    )
    source = pretty_formula(formula, [])
    readable = readable_formula(formula, source_statement=source)

    assert readable.count("QRes ") == 4
    assert "∨" in readable
    assert "¬" in readable
    assert "↔" not in readable


def test_shared_prelude_contains_mathlib_free_proved_native_bridges() -> None:
    source = _simple().notation_code

    assert "theorem lt_iff (n p : Nat) : Lt n p ↔ n < p := by" in source
    assert "theorem dvd_iff (d n : Nat) : Dvd d n ↔ d ∣ n := by" in source
    assert "import PeanoLab.Codec" in source
    assert "Mathlib" not in source
    assert re.search(r"\bsorry\b|\bnative_decide\b|^\s*axiom\s+", source, re.M) is None


def test_readable_preview_never_calls_certificate_export_or_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("a theorem-only preview must not build or replay a proof")

    monkeypatch.setattr(lean_presentation, "export_checked_theorem", forbidden)
    monkeypatch.setattr(lean_presentation, "export_checked_bundle_theorem", forbidden)
    preview = preview_checked_presentation(
        "zero_reflexive",
        ZERO_EQ_ZERO,
        summary="An independently inspectable equality.",
    )

    assert preview.startswith("theorem «zero_reflexive» : 0 = 0")
    assert "import PeanoLab.Codec" in preview
    assert "PeanoLab.Artifact.check_sound" in preview
    assert "verification: NOT RUN" in preview
    assert "private def " not in preview


def test_preview_is_hard_bounded_even_for_long_tactic_lines() -> None:
    preview = preview_checked_presentation(
        "zero_reflexive",
        ZERO_EQ_ZERO,
        script=tuple("x" * 5_000 for _ in range(16)),
    )

    assert len(preview.encode("utf-8")) <= MAX_PREVIEW_BYTES
    assert "[preview truncated;" in preview


def test_summary_and_tactic_newlines_cannot_escape_lean_comments() -> None:
    presentation = _simple(
        summary="safe explanation\naxiom injected : False",
        script=("exact proof\naxiom tactic_injected : False",),
    )

    assert "-- axiom injected : False" in presentation.presentation_code
    assert "--   axiom tactic_injected : False" in presentation.preview
    assert re.search(r"^axiom ", presentation.presentation_code, re.MULTILINE) is None
    assert re.search(r"^axiom ", presentation.preview, re.MULTILINE) is None


def test_closed_shared_bundle_remains_independently_checked() -> None:
    target = And(ZERO_EQ_ZERO, ZERO_EQ_ZERO)
    bundle = ProofBundle(
        nodes=(
            BundleNode(7, target, (), AndIntro(EqRefl(ZERO), EqRefl(ZERO))),
        ),
        root=7,
    )

    presentation = build_checked_presentation("shared_reflexive", target, None, bundle=bundle)

    assert "import PeanoLab.ProofBundle" in presentation.certificate_code
    assert "PeanoLab.checkBundle_sound accepted" in presentation.certificate_code
    assert presentation.manifest["proof_mode"] == "bundle"
    assert presentation.manifest["structure"]["bundle_nodes"] == 1
    assert "private def " not in presentation.presentation_code


def test_false_or_wrong_proof_is_rejected_before_presentation() -> None:
    with pytest.raises(LeanCertificateError, match="rejected"):
        build_checked_presentation(
            "false_equality",
            Eq(ZERO, Succ(ZERO)),
            EqRefl(ZERO),
        )


@pytest.mark.parametrize("source", ("0 = 1", "forall x. x = x", "0 ="))
def test_source_statement_must_parse_to_the_exact_closed_checked_target(
    source: str,
) -> None:
    with pytest.raises(LeanPresentationError):
        readable_formula(ZERO_EQ_ZERO, source_statement=source)


def test_source_statement_length_is_hard_bounded() -> None:
    with pytest.raises(LeanPresentationError, match="limit"):
        readable_formula(
            ZERO_EQ_ZERO,
            source_statement=" " * (MAX_SOURCE_BYTES + 1),
        )


@pytest.mark.parametrize("edition", ("", "../escape", "stable/evil", "a" * 33, 1, True))
def test_edition_rejects_path_traversal_and_nonexact_types(edition: object) -> None:
    with pytest.raises((LeanPresentationError, TypeError)):
        _simple(edition=edition)


@pytest.mark.parametrize("name", ("_", "a/b", "a.b", "a-b", "x" * 129))
def test_theorem_name_is_safe_for_lean_identifiers_and_module_paths(name: str) -> None:
    with pytest.raises((LeanPresentationError, ValueError)):
        build_checked_presentation(name, ZERO_EQ_ZERO, EqRefl(ZERO))


def test_duplicate_or_unbounded_dependencies_are_rejected() -> None:
    with pytest.raises(LeanPresentationError, match="duplicate"):
        _simple(dependencies=("zero_add", "zero_add"))
    with pytest.raises(TypeError, match="bounded"):
        _simple(dependencies=("zero_add",) * (MAX_DEPENDENCIES + 1))
    with pytest.raises(TypeError, match="bounded"):
        _simple(dependencies="zero_add")


def test_summary_script_audit_and_certificate_types_are_exact_and_bounded() -> None:
    with pytest.raises(LeanPresentationError, match="summary"):
        _simple(summary="x" * (MAX_SUMMARY_BYTES + 1))
    with pytest.raises(LeanPresentationError, match="line"):
        _simple(script=("x",) * (MAX_SCRIPT_LINES + 1))
    with pytest.raises(LeanPresentationError, match="byte"):
        _simple(script="x" * (MAX_SCRIPT_BYTES + 1))
    with pytest.raises(LeanPresentationError, match="byte"):
        _simple(script=("x" * MAX_SCRIPT_BYTES, "x"))
    with pytest.raises(TypeError, match="boolean"):
        _simple(include_axiom_audit=1)
    with pytest.raises(TypeError, match="proof certificate"):
        build_checked_presentation("bad", ZERO_EQ_ZERO, None)
    with pytest.raises(TypeError, match="ProofBundle"):
        build_checked_presentation("bad", ZERO_EQ_ZERO, None, bundle=True)


def test_reserved_source_binder_names_are_replaced_safely() -> None:
    source = "forall match. match = match"
    formula = parse_formula(source)

    assert readable_formula(formula, source_statement=source) == "∀ x : Nat, x = x"
