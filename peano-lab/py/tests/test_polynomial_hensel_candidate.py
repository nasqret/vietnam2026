"""Unchanged-kernel audit of exact constructive polynomial differentiation."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import Exists, Forall, parse_formula_in_context
from peano_lab.library import editions_v23 as v23
from peano_lab.library import polynomial_hensel_candidate as candidate
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "beta_horner_derivative_trace_exists",
    "beta_horner_derivative_value_exists",
    "beta_horner_derivative_value_projection",
    "beta_horner_derivative_only_projection",
    "beta_horner_derivative_only_exists",
    "beta_horner_derivative_first_component_functional",
    "beta_horner_derivative_empty",
    "beta_horner_derivative_successor_decompose",
    "beta_horner_derivative_functional",
    "beta_horner_derivative_second_component_functional",
    "beta_horner_derivative_exists_unique",
    "beta_horner_derivative_only_functional",
    "beta_horner_derivative_only_exists_unique",
    "beta_horner_derivative_constant",
    "beta_horner_derivative_linear",
)
EXPECTED_ORDERED_NAMES_SHA256 = (
    "2f9f8f66433ce0f597fc5f8e1a71349996be02e2329700d70a33a97c4d4d52e1"
)
EXPECTED_ROOT_STATEMENT_SHA256 = {
    "beta_horner_derivative_trace_exists": (
        "5a7dbce648cc7ab15e0f82e80e7ba87888e8e709102920acd67f761d88b98f24"
    ),
    "beta_horner_derivative_value_exists": (
        "b012d6a0d97002529f35f80264535daa5c21fb1ca6ca67a7a1d0561c1c0c5c51"
    ),
    "beta_horner_derivative_successor_decompose": (
        "042cb58aec7a7a63eaef9c83958feefbc51b1ce89e927010c2e9427f401b7435"
    ),
    "beta_horner_derivative_functional": (
        "48bf3276ce3057494e1e9b46aca2ea063b9937db4659a35d4f879ac09abec09f"
    ),
    "beta_horner_derivative_exists_unique": (
        "171b5939376bfb9e9ec9469d3addd98e27584931fa7994dccb4b372c4d9a693f"
    ),
    "beta_horner_derivative_only_exists_unique": (
        "60a8a62113371b7c5ae1784f965d107b6f985af1fb059438ff42a222b796447d"
    ),
    "beta_horner_derivative_constant": (
        "e3b4e0f787e0acb66efae5dda93c207cff2c4c40bafa1c54e878d667b25f7aea"
    ),
    "beta_horner_derivative_linear": (
        "154adc2aae62495917763842a52646ccff31b05c36b09bc0250e3a8ed5e9437e"
    ),
}
EXPECTED_PROOF_NODES = (
    28, 53, 26, 9, 28, 93, 66, 157, 173, 25, 70, 50, 58, 90, 76
)
EXPECTED_PROOF_DEPTHS = (
    15, 24, 18, 9, 18, 40, 28, 40, 34, 23, 41, 30, 34, 28, 26
)


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_polynomial_hensel_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v23.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_exact_fifteen_theorem_constructive_derivative_frontier() -> None:
    assert tuple(item.name for item in rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        EXPECTED_ORDERED_NAMES_SHA256
    )
    assert len(rows()) == 15
    assert sum(len(item.dependencies) for item in rows()) == 27
    assert sum(len(item.script) for item in rows()) == 583


def test_every_dependency_is_checked_earlier_and_no_classical_shortcut_appears() -> None:
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert row.script
        assert not any(
            "DNE" in command or command.startswith("use ") for command in row.script
        )
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_every_new_candidate_is_absent_from_the_immutable_v23_parent(name: str) -> None:
    assert v23.entry(name, edition="alpha") is None
    assert v23.entry(name, edition="stable") is None


@pytest.mark.parametrize("name,expected", tuple(EXPECTED_ROOT_STATEMENT_SHA256.items()))
def test_major_exact_first_order_statement_hashes_are_frozen(name: str, expected: str) -> None:
    row = next(item for item in rows() if item.name == name)
    assert sha256(row.statement.encode()).hexdigest() == expected


def test_original_intuitionistic_kernel_accepts_every_real_candidate_body() -> None:
    actual = receipts()
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert tuple(item.proof_nodes for item in actual) == EXPECTED_PROOF_NODES
    assert tuple(item.proof_depth for item in actual) == EXPECTED_PROOF_DEPTHS
    assert sum(item.proof_nodes for item in actual) == 1_002
    assert max(item.proof_nodes for item in actual) == 173
    assert max(item.proof_depth for item in actual) == 41


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_corrupted_tactic_body_fails_closed(name: str) -> None:
    row = next(item for item in rows() if item.name == name)
    broken = replace(row, script=row.script[:-1] + ("exact nonexistent_derivative_proof",))
    public = {**core(), **{item.name: item for item in rows()}}
    with pytest.raises(CandidateBodyError, match="failed at command"):
        replay_candidate_bodies((broken,), core=public)


@pytest.mark.parametrize(
    "helper,arguments",
    (
        (
            candidate.horner_derivative_trace_relation,
            ("b", "c", "t", "l", "u", "v", "d", "e"),
        ),
        (candidate.horner_derivative_relation, ("b", "c", "t", "l", "n", "z")),
        (candidate.horner_derivative_only_relation, ("b", "c", "t", "l", "z")),
    ),
)
def test_named_derivative_relations_are_hygienic_conservative_formulas(
    helper,
    arguments: tuple[str, ...],
) -> None:
    first = helper(*arguments, tag="first")
    second = helper(*arguments, tag="another")
    assert parse_formula_in_context(first, list(arguments)) == (
        parse_formula_in_context(second, list(arguments))
    )
    assert "Horner" not in first
    assert "Derivative" not in first
    assert "Beta" not in first
    assert "oracle" not in first


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "x+y", "two words", "ff_x"))
def test_invalid_or_capturing_public_arguments_are_rejected(bad: str) -> None:
    with pytest.raises(candidate.PolynomialHenselError):
        candidate.horner_derivative_relation(bad, "c", "t", "l", "n", "z", tag="ok")


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "x+y", "two words"))
def test_invalid_derivative_binder_tags_are_rejected(bad: str) -> None:
    with pytest.raises(candidate.PolynomialHenselError):
        candidate.horner_derivative_relation("b", "c", "t", "l", "n", "z", tag=bad)


def test_repeated_public_arguments_fail_before_formula_generation() -> None:
    with pytest.raises(candidate.PolynomialHenselError, match="distinct"):
        candidate.horner_derivative_trace_relation(
            "b", "c", "t", "l", "u", "v", "u", "e", tag="bad"
        )


def test_major_pair_root_is_closed_universal_then_existential() -> None:
    formula = _closed_formula(
        next(item for item in rows() if item.name == "beta_horner_derivative_exists_unique").statement
    )
    for _ in range(4):
        assert type(formula) is Forall
        formula = formula.body
    assert type(formula) is Exists
    assert type(formula.body) is Exists


def test_exact_successor_root_contains_both_actual_derivative_recurrences() -> None:
    row = next(
        item for item in rows()
        if item.name == "beta_horner_derivative_successor_decompose"
    )
    assert "n = r * t + a" in row.statement
    assert "z = q * t + r" in row.statement
    assert "exists a r q" in row.statement


@pytest.mark.parametrize(
    "coefficients,base,value,derivative",
    (
        ((), 0, 0, 0),
        ((), 17, 0, 0),
        ((7,), 9, 7, 0),
        ((2, 3), 5, 13, 2),
        ((3, 2, 5), 4, 61, 26),
        ((1, 0, 1, 7), 3, 37, 28),
        ((0, 0, 4), 12, 4, 0),
        ((5, 4, 3, 2, 1), 0, 1, 2),
        ((1, 1, 1, 1, 1, 1), 2, 63, 129),
    ),
)
def test_concrete_coupled_horner_examples(
    coefficients: tuple[int, ...],
    base: int,
    value: int,
    derivative: int,
) -> None:
    receipt = candidate.evaluate_horner_derivative(coefficients, base)
    assert receipt.value == value
    assert receipt.derivative == derivative
    assert len(receipt.steps) == len(coefficients)
    assert candidate.verify_horner_derivative_evaluation(receipt)
    for step in receipt.steps:
        assert step.value == step.previous_value * base + step.coefficient
        assert step.derivative == step.previous_derivative * base + step.previous_value


@pytest.mark.parametrize("length", range(9))
@pytest.mark.parametrize("base", (0, 1, 2, 3, 7))
def test_concrete_formal_derivative_matches_independent_power_sum(
    length: int,
    base: int,
) -> None:
    coefficients = tuple(3 * index + 1 for index in range(length))
    receipt = candidate.evaluate_horner_derivative(coefficients, base)
    expected_value = sum(
        coefficient * base ** (length - index - 1)
        for index, coefficient in enumerate(coefficients)
    )
    expected_derivative = sum(
        coefficient * (length - index - 1) * base ** (length - index - 2)
        for index, coefficient in enumerate(coefficients)
        if index + 1 < length
    )
    assert (receipt.value, receipt.derivative) == (expected_value, expected_derivative)


@pytest.mark.parametrize(
    "bad_base",
    (-1, True, False, 1.0, "3", None),
)
def test_non_natural_evaluation_points_fail_closed(bad_base) -> None:
    with pytest.raises(candidate.PolynomialHenselError, match="natural"):
        candidate.evaluate_horner_derivative((1, 2), bad_base)


@pytest.mark.parametrize(
    "coefficients",
    ((1, -2), (True,), (1.0,), ("1",), (None,)),
)
def test_non_natural_coefficients_fail_closed(coefficients) -> None:
    with pytest.raises(candidate.PolynomialHenselError, match="natural"):
        candidate.evaluate_horner_derivative(coefficients, 2)


def test_non_iterable_coefficients_fail_closed() -> None:
    with pytest.raises(candidate.PolynomialHenselError, match="iterable"):
        candidate.evaluate_horner_derivative(None, 2)


def test_excessive_coefficient_length_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(candidate, "MAX_HORNER_COEFFICIENTS", 2)
    with pytest.raises(candidate.PolynomialHenselError, match="certificate size"):
        candidate.evaluate_horner_derivative((1, 2, 3), 2)


def test_excessive_output_bit_budget_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(candidate, "MAX_HORNER_OUTPUT_BITS", 5)
    with pytest.raises(candidate.PolynomialHenselError, match="bit budget"):
        candidate.evaluate_horner_derivative((7, 7), 8)


def test_forged_coupled_horner_certificate_fails_closed() -> None:
    receipt = candidate.evaluate_horner_derivative((3, 2, 5), 4)
    assert not candidate.verify_horner_derivative_evaluation(replace(receipt, value=62))
    assert not candidate.verify_horner_derivative_evaluation(replace(receipt, derivative=27))
    assert not candidate.verify_horner_derivative_evaluation(replace(receipt, base=5))
    assert not candidate.verify_horner_derivative_evaluation(
        replace(receipt, coefficients=(3, 5, 2))
    )
    assert not candidate.verify_horner_derivative_evaluation(
        replace(receipt, steps=receipt.steps[:-1])
    )
    changed = replace(receipt.steps[1], derivative=receipt.steps[1].derivative + 1)
    assert not candidate.verify_horner_derivative_evaluation(
        replace(receipt, steps=(receipt.steps[0], changed, receipt.steps[2]))
    )
    assert not candidate.verify_horner_derivative_evaluation(None)


@pytest.mark.parametrize(
    "name",
    (
        "simple_root_hensel_lifting",
        "polynomial_taylor_divisibility",
        "polynomial_hensel_lift_exists_unique",
        "finite_field_irreducible_factorization",
    ),
)
def test_unproved_hensel_lifting_is_not_silently_claimed(name: str) -> None:
    assert name not in {item.name for item in rows()}
    assert v23.entry(name, edition="alpha") is None
