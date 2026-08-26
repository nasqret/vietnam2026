"""Ordinary Lean proof bodies are reconstructed without transitive replay."""

from __future__ import annotations

from dataclasses import replace
import re

import pytest

from peano_lab.kernel.formulas import Eq, parse_formula
from peano_lab.kernel.terms import Zero
from peano_lab.library import lean_proof_reconstruction, theorems
from peano_lab.library.lean import formula_to_lean
from peano_lab.library.lean_proof_reconstruction import (
    DEFAULT_AXIOM_REFERENCES,
    MAX_RECONSTRUCTION_STEPS,
    ReconstructionError,
    SUPPORTED_TACTICS,
    reconstruct_theorem,
)
from peano_lab.library.theorems import TheoremSpec, get


def _named(name: str, **kwargs: object):
    spec = get(name)
    assert spec is not None
    references = kwargs.pop(
        "dependency_references",
        {dependency: dependency for dependency in spec.dependencies},
    )
    return reconstruct_theorem(spec, dependency_references=references, **kwargs)


@pytest.mark.parametrize(
    "name",
    (
        "zero_add",
        "add_succ_left",
        "add_comm",
        "le_refl",
        "le_zero",
        "multiple_zero",
        "zero_le",
        "succ_ne_zero",
        "succ_injective",
        "eq_symm",
        "eq_trans",
        "succ_congr",
        "zero_or_succ",
        "nonzero_is_succ",
        "is_lcm_zero_left",
        "multiple_mul_left",
        "beta_modulus_nonzero",
        "qres_mod3_one",
    ),
)
def test_real_small_library_scripts_become_readable_dependency_relative_proofs(
    name: str,
) -> None:
    specification = get(name)
    assert specification is not None
    result = _named(name)

    assert result.name == name
    assert result.status == "translated"
    assert result.translated_steps == len(specification.script)
    assert result.unsupported_steps == ()
    assert result.diagnostics == ()
    assert result.lean_body.startswith("by\n")
    assert result.used_dependencies == specification.dependencies
    assert "Certificate" not in result.lean_body
    assert re.search(r"\bsorry\b|\bnative_decide\b|^\s*axiom\s+", result.lean_body, re.M) is None


def test_dependencies_are_checked_theorem_references_not_recursive_proof_copies() -> None:
    result = _named(
        "add_comm",
        dependency_references={
            "zero_add": "Earlier.Zero.verified_zero_add",
            "add_succ_left": "Earlier.Succ.«add_succ_left»",
        },
    )

    assert "have zero_add := Earlier.Zero.verified_zero_add" in result.lean_body
    assert "have add_succ_left := Earlier.Succ.«add_succ_left»" in result.lean_body
    assert result.used_dependencies == ("zero_add", "add_succ_left")


def test_actual_induction_and_its_exact_induction_hypothesis_are_structured() -> None:
    result = _named("zero_add")

    assert "  intro n\n  induction n with\n" in result.lean_body
    assert "  | zero =>\n    simp only [" in result.lean_body
    assert "  | succ n IH =>\n    simp only [" in result.lean_body
    assert "IH]" in result.lean_body


def test_actual_disjunction_and_existential_branches_keep_witness_names() -> None:
    result = _named("zero_or_succ")

    assert "  | zero =>\n    left\n    rfl" in result.lean_body
    assert "  | succ n IH =>\n    right\n    refine ⟨n, ?_⟩" in result.lean_body


def test_actual_equality_transitivity_has_two_lean_bullets() -> None:
    result = _named("eq_trans")

    assert "  apply Eq.trans (b := b)\n  · exact hab\n  · exact hbc" in result.lean_body


@pytest.mark.parametrize(
    "name",
    (
        "add_eq_zero_left",
        "le_of_succ_le_succ",
        "divisor_le_nonzero",
        "le_succ",
        "add_left_cancel",
    ),
)
def test_actual_prime_prerequisites_use_core_equality_transitivity(name: str) -> None:
    result = _named(name)

    assert result.status == "translated"
    assert "apply Eq.trans (b := " in result.lean_body
    assert re.search(r"^\s*trans\b", result.lean_body, re.MULTILINE) is None


def test_actual_existential_elimination_keeps_exact_surface_names() -> None:
    result = _named("le_zero")

    assert "obtain ⟨x, h_witness⟩ := h" in result.lean_body
    assert "apply add_eq_zero_right" in result.lean_body


def test_local_have_and_suffices_keep_their_actual_proof_branch_structure() -> None:
    have_result = _named("is_lcm_zero_left")
    suffices_result = _named("multiple_mul_left")

    assert "  have h : " in have_result.lean_body
    assert " := by\n    have is_lcm_zero_right_before" in have_result.lean_body
    assert "\n  have is_lcm_symm_before :=" in have_result.lean_body
    assert "suffices hswap : m * n = n * m by" in suffices_result.lean_body
    assert "    rewrite (occs := .pos [1]) [hswap]" in suffices_result.lean_body


def test_specialization_preserves_the_old_hypothesis_and_parenthesizes_terms() -> None:
    result = _named("beta_modulus_nonzero")

    assert "have succ_ne_zero_before := succ_ne_zero" in result.lean_body
    assert "specialize succ_ne_zero (Nat.succ (i) * c)" in result.lean_body


def test_arithmetic_axioms_are_core_lean_theorems_not_new_axioms() -> None:
    pa1 = _named("succ_ne_zero")
    pa2 = _named("succ_injective")
    rewrite = _named("multiple_zero")

    assert "apply Nat.succ_ne_zero" in pa1.lean_body
    assert pa1.used_axioms == ("PA1",)
    assert "apply Nat.succ.inj" in pa2.lean_body
    assert pa2.used_axioms == ("PA2",)
    assert "rewrite (occs := .pos [1]) [Nat.mul_zero]" in rewrite.lean_body
    assert rewrite.used_axioms == ("PA5",)


def test_custom_checked_arithmetic_lemmas_support_dependency_strand_namespaces() -> None:
    result = _named(
        "zero_add",
        available_axioms={
            "PA3": "pa3_sound",
            "PA4": "pa4_sound",
            "PA5": "pa5_sound",
            "PA6": "pa6_sound",
        },
    )

    assert "simp only [pa3_sound, pa4_sound, pa5_sound, pa6_sound" in result.lean_body
    assert result.used_axioms == ("PA3", "PA4", "PA5", "PA6")


def test_rewrite_direction_and_local_hypothesis_history_are_preserved() -> None:
    source = TheoremSpec(
        "reverse_at",
        "forall a b. a = b -> b = b -> a = b",
        (),
        ("intro a", "intro b", "intro hab", "intro hbb", "rewrite <- hab at hbb", "exact hbb"),
        "Reverse rewrite at a retained hypothesis.",
    )
    result = reconstruct_theorem(source, dependency_references={})

    assert result.status == "translated"
    assert "have hbb_before := hbb" in result.lean_body
    assert "rewrite (occs := .pos [1]) [← hab] at hbb" in result.lean_body


def test_small_closed_norm_num_becomes_kernel_checked_decision() -> None:
    source = TheoremSpec("small_number", "2 + 3 = 5", (), ("norm_num",), "Small arithmetic.")
    result = reconstruct_theorem(source, dependency_references={})

    assert result.status == "translated"
    assert result.lean_body == "by\n  decide"
    assert "native_decide" not in result.lean_body


def test_nontrivial_norm_num_truthfully_requests_a_checked_local_fallback() -> None:
    source = TheoremSpec(
        "open_number",
        "forall n. n + (2 + 3) = n + 5",
        (),
        ("norm_num",),
        "An open arithmetic normalization.",
    )
    result = reconstruct_theorem(source, dependency_references={})

    assert result.status == "fallback_required"
    assert result.lean_body == ""
    assert result.unsupported_steps == ("norm_num",)
    assert "fallback" in result.diagnostics[0]


def test_alpha_only_dependency_can_be_reconstructed_from_its_exact_formula() -> None:
    specification = TheoremSpec(
        "alpha_relative",
        "0 = 0",
        ("earlier_alpha",),
        ("exact earlier_alpha",),
        "One earlier checked Alpha-v18 lemma.",
    )
    result = reconstruct_theorem(
        specification,
        dependency_references={"earlier_alpha": "Alpha.Checked.earlier_alpha"},
        dependency_formulas={"earlier_alpha": parse_formula("0 = 0")},
    )

    assert result.status == "translated"
    assert result.lean_body == (
        "by\n"
        "  have earlier_alpha := Alpha.Checked.earlier_alpha\n"
        "  exact earlier_alpha"
    )


def test_missing_alpha_dependency_formula_fails_closed_without_lookup_authority() -> None:
    specification = TheoremSpec(
        "alpha_relative",
        "0 = 0",
        ("earlier_alpha",),
        ("exact earlier_alpha",),
        "One earlier checked Alpha-v18 lemma.",
    )
    result = reconstruct_theorem(
        specification,
        dependency_references={"earlier_alpha": "Alpha.Checked.earlier_alpha"},
    )

    assert result.status == "fallback_required"
    assert "no exact closed formula" in result.diagnostics[0]


def test_missing_checked_dependency_reference_is_an_honest_fallback() -> None:
    result = _named("add_comm", dependency_references={"zero_add": "zero_add"})

    assert result.status == "fallback_required"
    assert result.translated_steps == 0
    assert "add_succ_left" in result.diagnostics[0]


def test_reconstruction_never_calls_recursive_library_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("readable proof reconstruction must never replay dependencies")

    monkeypatch.setattr(theorems, "replay", forbidden)
    result = _named("add_comm")

    assert result.status == "translated"


def test_repeated_local_reconstruction_is_deterministic() -> None:
    assert _named("add_comm") == _named("add_comm")


def test_only_exact_or_reviewed_conservative_statements_may_override_rendering() -> None:
    specification = get("le_refl")
    assert specification is not None
    formula = parse_formula(specification.statement)
    exact = formula_to_lean(formula)
    exact_result = _named("le_refl", statement=exact)

    assert exact_result.lean_statement == exact
    with pytest.raises(ReconstructionError, match="differs"):
        _named("le_refl", statement="False")


@pytest.mark.parametrize(
    "reference",
    (
        "",
        "Earlier.bad; axiom fake : False",
        "Earlier.bad\naxiom fake : False",
        "../escape",
        "A..B",
        "A B",
        1,
    ),
)
def test_malicious_dependency_references_cannot_inject_lean_source(
    reference: object,
) -> None:
    with pytest.raises(ReconstructionError, match="reference"):
        _named(
            "add_comm",
            dependency_references={"zero_add": reference, "add_succ_left": "ok"},
        )


def test_undeclared_dependency_references_or_formulas_are_rejected() -> None:
    with pytest.raises(ReconstructionError, match="undeclared"):
        _named("zero_add", dependency_references={"forged": "Forged.lemma"})
    with pytest.raises(ReconstructionError, match="undeclared"):
        _named("zero_add", dependency_formulas={"forged": Eq(Zero(), Zero())})


def test_nonformula_alpha_dependency_and_fabricated_arithmetic_axioms_are_rejected() -> None:
    with pytest.raises(ReconstructionError, match="formula"):
        _named("add_comm", dependency_formulas={"zero_add": True})
    with pytest.raises(ReconstructionError, match="PA1 through PA6"):
        _named("zero_add", available_axioms={"PA7": "invented"})
    with pytest.raises(ReconstructionError, match="reference"):
        _named("zero_add", available_axioms={"PA3": "bad; axiom fake : False"})


@pytest.mark.parametrize("limit", (0, -1, True, 1.0, MAX_RECONSTRUCTION_STEPS + 1))
def test_step_limits_require_exact_bounded_positive_integers(limit: object) -> None:
    with pytest.raises(ReconstructionError, match="max_steps"):
        _named("zero_add", max_steps=limit)


def test_step_limit_rejects_script_before_any_local_proof_execution() -> None:
    with pytest.raises(ReconstructionError, match="script"):
        _named("zero_add", max_steps=2)


def test_classical_dne_and_unsupported_tactics_never_produce_lean_proofs() -> None:
    base = get("zero_add")
    assert base is not None
    for command in ("apply DNE", "ring", "undo", "admit"):
        result = reconstruct_theorem(
            replace(base, script=(command,)),
            dependency_references={},
        )
        assert result.status == "fallback_required"
        assert result.unsupported_steps == (command,)
        assert result.lean_body == ""


def test_invalid_local_script_and_remaining_goals_fail_closed() -> None:
    base = get("zero_add")
    assert base is not None
    invalid = reconstruct_theorem(
        replace(base, script=("exact missing",)),
        dependency_references={},
    )
    incomplete = reconstruct_theorem(
        replace(base, script=("intro n",)),
        dependency_references={},
    )

    assert invalid.status == "fallback_required"
    assert invalid.unsupported_steps == ("exact missing",)
    assert incomplete.status == "fallback_required"
    assert "unproved" in incomplete.diagnostics[0]


def test_malformed_theorem_specs_names_dependencies_and_scripts_are_rejected() -> None:
    base = get("zero_add")
    assert base is not None
    with pytest.raises(ReconstructionError, match="exact TheoremSpec"):
        reconstruct_theorem(True, dependency_references={})  # type: ignore[arg-type]
    with pytest.raises((ReconstructionError, ValueError)):
        reconstruct_theorem(replace(base, name="bad/name"), dependency_references={})
    with pytest.raises(ReconstructionError, match="duplicate"):
        reconstruct_theorem(
            replace(base, dependencies=("same", "same")),
            dependency_references={"same": "same"},
        )
    with pytest.raises(ReconstructionError, match="blank"):
        reconstruct_theorem(replace(base, script=("",)), dependency_references={})
    with pytest.raises(ReconstructionError, match="free variables"):
        reconstruct_theorem(replace(base, statement="n = n"), dependency_references={})


def test_declared_supported_tactics_are_all_constructive_and_bounded() -> None:
    assert "undo" not in SUPPORTED_TACTICS
    assert "ring" not in SUPPORTED_TACTICS
    assert "intro" in SUPPORTED_TACTICS
    assert "induction" in SUPPORTED_TACTICS
    assert "norm_num" in SUPPORTED_TACTICS
    assert set(DEFAULT_AXIOM_REFERENCES) == {"PA1", "PA2", "PA3", "PA4", "PA5", "PA6"}


def test_translation_does_not_invoke_certificate_export(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("a readable proof must not manufacture a full certificate")

    monkeypatch.setattr(theorems, "replay", forbidden)
    result = lean_proof_reconstruction.reconstruct_theorem(
        get("multiple_zero"),  # type: ignore[arg-type]
        dependency_references={},
    )

    assert result.status == "translated"
