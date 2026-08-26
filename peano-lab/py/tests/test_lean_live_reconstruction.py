"""Lean-core proof reconstruction preserves every exact authored obligation."""

from __future__ import annotations

import re

import pytest

from peano_lab.kernel.formulas import parse_formula
from peano_lab.library import editions_v19, theorems
from peano_lab.library.lean_proof_reconstruction import reconstruct_theorem
from peano_lab.library.theorems import TheoremSpec, get


@pytest.fixture(scope="module")
def checked_specs() -> dict[str, TheoremSpec]:
    return {entry.spec.name: entry.spec for entry in editions_v19.ALPHA_ENTRIES}


def _reconstruct(spec: TheoremSpec, checked: dict[str, TheoremSpec] | None = None):
    formulas = None
    if checked is not None:
        formulas = {
            name: parse_formula(checked[name].statement)
            for name in spec.dependencies
        }
    return reconstruct_theorem(
        spec,
        dependency_references={name: name for name in spec.dependencies},
        dependency_formulas=formulas,
    )


@pytest.mark.parametrize(
    ("name", "command"),
    (
        ("succ_congr", "refine congrArg Nat.succ ?_"),
        ("add_congr", "refine congr (congrArg Nat.add ?_) ?_"),
        ("mul_congr", "refine congr (congrArg Nat.mul ?_) ?_"),
    ),
)
def test_constructor_congruence_uses_actual_lean_core_primitives(
    name: str,
    command: str,
) -> None:
    spec = get(name)
    assert spec is not None

    result = _reconstruct(spec)

    assert result.status == "translated"
    assert command in result.lean_body
    assert "congrArg₂" not in result.lean_body


@pytest.mark.parametrize("name", ("add_congr", "mul_congr"))
def test_binary_congruence_retains_both_original_proof_obligations(name: str) -> None:
    spec = get(name)
    assert spec is not None

    result = _reconstruct(spec)

    assert result.translated_steps == len(spec.script)
    assert "?_) ?_" in result.lean_body
    assert result.lean_body.count("· ") >= 2


def test_alpha_pythagorean_root_is_an_exact_twelve_step_readable_proof(
    checked_specs: dict[str, TheoremSpec],
) -> None:
    spec = checked_specs["pythagorean_double_product"]

    result = _reconstruct(spec, checked_specs)

    assert result.status == "translated"
    assert result.translated_steps == 12
    assert result.used_dependencies == ("mul_comm", "mul_succ_left", "one_mul")
    assert result.lean_body.count("refine congr (congrArg Nat.add ?_) ?_") == 2
    assert "congrArg₂" not in result.lean_body


def test_rewrite_does_not_close_an_authored_reflexivity_goal() -> None:
    spec = get("multiple_zero")
    assert spec is not None

    result = _reconstruct(spec)

    assert result.status == "translated"
    assert "rewrite (occs := .pos [1]) [Nat.mul_zero]\n  rfl" in result.lean_body
    assert re.search(r"(?m)^\s*rw\b", result.lean_body) is None


def test_each_authored_rewrite_changes_exactly_one_occurrence() -> None:
    spec = TheoremSpec(
        "separate_rewrites",
        "forall a b. a = b -> a + a = b + b",
        (),
        ("intro a", "intro b", "intro hab", "rewrite hab", "rewrite hab", "refl"),
        "Two occurrences remain two independently authored proof steps.",
    )

    result = _reconstruct(spec)

    assert result.status == "translated"
    assert result.lean_body.count("rewrite (occs := .pos [1]) [hab]") == 2
    assert "change a + a = b + b" not in result.lean_body
    assert result.translated_steps == len(spec.script)


def test_repeated_hypothesis_rewrites_keep_each_expanded_equality_state() -> None:
    spec = TheoremSpec(
        "repeated_hypothesis_rewrites",
        "forall a b c. a = b -> a + a = c -> b + b = c",
        (),
        (
            "intro a",
            "intro b",
            "intro c",
            "intro hab",
            "intro h",
            "rewrite hab at h",
            "rewrite hab at h",
            "exact h",
        ),
        "Repeated hypothesis transport exposes both distinct authored occurrences.",
    )

    result = _reconstruct(spec)

    assert result.status == "translated"
    assert result.translated_steps == len(spec.script)
    assert "have h_before := h" in result.lean_body
    assert result.lean_body.count("rewrite (occs := .pos [1]) [hab] at h") == 2
    assert "change a + a = c at h" not in result.lean_body


def test_repeated_beta_alias_rewrites_expand_the_exact_hypothesis() -> None:
    spec = get("finite_contains_decidable")
    assert spec is not None

    result = _reconstruct(spec)

    assert result.status == "translated"
    assert result.translated_steps == len(spec.script)
    assert result.lean_body.count(
        "rewrite (occs := .pos [1]) [eq_decidable_left] at beta_at_exists_witness"
    ) == 2
    assert re.search(
        r"change \(∃ [^\n]+ at beta_at_exists_witness\n"
        r"\s+rewrite \(occs := \.pos \[1\]\) \[eq_decidable_left\] "
        r"at beta_at_exists_witness\n"
        r"\s+change \(∃ [^\n]+ at beta_at_exists_witness",
        result.lean_body,
    ) is not None


def test_reverse_rewrite_at_hypothesis_preserves_exact_prior_evidence() -> None:
    spec = TheoremSpec(
        "reverse_single_occurrence",
        "forall a b. a = b -> b = b -> a = b",
        (),
        (
            "intro a",
            "intro b",
            "intro hab",
            "intro hbb",
            "rewrite <- hab at hbb",
            "exact hbb",
        ),
        "Reverse one occurrence while preserving the original checked hypothesis.",
    )

    result = _reconstruct(spec)

    assert result.status == "translated"
    assert "have hbb_before := hbb" in result.lean_body
    assert "rewrite (occs := .pos [1]) [← hab] at hbb" in result.lean_body


def test_successor_addition_rewrite_keeps_its_authored_reflexivity_goal() -> None:
    spec = TheoremSpec(
        "successor_addition_rewrite",
        "forall a b. a + S b = S (a + b)",
        (),
        ("intro a", "intro b", "rewrite PA4", "refl"),
        "Each definitional addition rewrite retains its exact next proof goal.",
    )

    result = _reconstruct(spec)

    assert result.status == "translated"
    assert result.translated_steps == len(spec.script)
    assert "change Nat.succ (a + b) = Nat.succ (a + b)\n  rfl" in result.lean_body
    assert "rewrite (occs := .pos [1]) [Nat.add_succ]" not in result.lean_body


@pytest.mark.parametrize("name", ("lt_not_le", "lt_not_eq_add_middle"))
def test_nested_successor_addition_rewrites_preserve_exact_peano_states(name: str) -> None:
    spec = get(name)
    assert spec is not None

    result = _reconstruct(spec)

    assert result.status == "translated"
    assert result.translated_steps == len(spec.script)
    assert result.lean_body.count(" at hz\n") >= (4 if name == "lt_not_le" else 6)
    assert result.lean_body.count("\n      change ") >= 4
    assert "have hz_before := hz" in result.lean_body
    assert "rewrite (occs := .pos [1]) [Nat.add_succ]" not in result.lean_body


@pytest.mark.parametrize(
    "name",
    (
        "divisor_le_nonzero",
        "multiple_has_zero_remainder",
        "prime_nonzero",
        "factor_difference",
        "divides_remainder",
        "mul_eq_one_components",
    ),
)
def test_previously_compiler_rejected_prime_prerequisites_use_core_proofs(
    name: str,
) -> None:
    spec = get(name)
    assert spec is not None

    result = _reconstruct(spec)

    assert result.status == "translated"
    assert result.translated_steps == len(spec.script)
    assert "congrArg₂" not in result.lean_body
    assert "Certificate" not in result.lean_body
    assert re.search(r"(?m)^\s*rw\b", result.lean_body) is None


def test_constructor_and_rewrite_translation_never_replays_dependencies(
    checked_specs: dict[str, TheoremSpec],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("local readable reconstruction must not replay any dependency")

    monkeypatch.setattr(theorems, "replay", forbidden)

    assert _reconstruct(checked_specs["pythagorean_double_product"], checked_specs).status == "translated"
    assert _reconstruct(checked_specs["multiple_has_zero_remainder"], checked_specs).status == "translated"


@pytest.mark.parametrize(
    "name",
    (
        "succ_congr",
        "add_congr",
        "mul_congr",
        "multiple_zero",
        "prime_nonzero",
        "pythagorean_double_product",
    ),
)
def test_readable_construction_never_injects_imports_axioms_or_unproved_terms(
    name: str,
    checked_specs: dict[str, TheoremSpec],
) -> None:
    result = _reconstruct(checked_specs[name], checked_specs)

    assert result.status == "translated"
    assert re.search(
        r"(?m)^\s*(?:import|axiom)\b|\b(?:sorry|sorryAx|native_decide)\b",
        result.lean_body,
    ) is None
