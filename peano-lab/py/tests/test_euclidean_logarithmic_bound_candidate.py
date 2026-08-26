"""Exact original-kernel closure and adversarial audit for campaign G101."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library import editions_v22 as v22
from peano_lab.library import euclidean_logarithmic_bound_candidate as candidate
from peano_lab.library.binary_length_candidate import binary_length_certificate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.euclidean_complexity_candidate import (
    certify_euclidean_execution,
    verify_euclidean_execution,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "euclidean_log_double_monotone",
    "euclidean_log_strict_half_cancel",
    "euclidean_log_halving_power_drop",
    "euclidean_log_double_successor",
    "euclidean_log_budget_weaken",
    "euclidean_log_budget_extend",
    "euclidean_log_budget_extend_twice",
    "euclidean_log_budget_zero_divisor",
    "euclidean_log_budget_successor_power",
    "euclidean_log_zero_below_power",
    "euclidean_log_power_zero_divisor",
    "euclidean_log_trace_below_power",
    "euclidean_log_binary_length_upper_power",
    "euclidean_log_trace_bound",
    "euclidean_log_execution_strong",
    "euclidean_gcd_execution_logarithmic_bound",
    "euclidean_gcd_execution_logarithmic_exists",
)

EXPECTED_PROOF_NODES = (
    24, 40, 34, 19, 38, 53, 30, 38, 13, 24, 20, 157, 91, 23, 46, 43, 26,
)

EXPECTED_ROOTS = {
    "euclidean_log_trace_below_power": (
        "915f2b77f40e08f8ed00cf72485d98432cab710e9b90415252c2b72573a028e3"
    ),
    "euclidean_log_trace_bound": (
        "c2558acd5302c364d3b9b37bc6cb5caa5b364c66e5f62054a714e74e95e24051"
    ),
    "euclidean_log_execution_strong": (
        "61e7a009a62e18fb46a29979815fa05ae53ac68cc1d054bff89b940e9ed76baf"
    ),
    "euclidean_gcd_execution_logarithmic_bound": (
        "decf1f8be3a9dcaf2e8bdf7bebd59e46d08e9f91fee375ca325c6b53847c8d6e"
    ),
    "euclidean_gcd_execution_logarithmic_exists": (
        "c9fd69a20e1ef3f4b71cb4fc58a8fb001f37d08fc1d8c51f541409070f016523"
    ),
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_euclidean_logarithmic_bound_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {row.name: row for row in v22.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def _row(name: str) -> TheoremSpec:
    return next(row for row in rows() if row.name == name)


def test_g101_candidates_are_new_closed_and_dependency_ordered() -> None:
    actual = rows()
    assert tuple(row.name for row in actual) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        "2f160f96931e8ff4262238d6b54d1e39406bbd232afd505078fe9faaf07aace4"
    )
    assert sum(len(row.dependencies) for row in actual) == 48
    assert sum(len(row.script) for row in actual) == 499
    known = set(core())
    for row in actual:
        formula, free_names = parse_formula_with_names(row.statement)
        assert not free_names
        assert formula == _closed_formula(row.statement)
        assert row.name not in known
        assert set(row.dependencies) <= known
        assert not any(
            command in {"sorry", "admit"}
            or "DNE" in command
            or command.startswith("use ")
            for command in row.script
        )
        known.add(row.name)


def test_every_g101_logarithmic_body_passes_the_unchanged_kernel() -> None:
    actual = receipts()
    assert tuple(receipt.name for receipt in actual) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in actual) == EXPECTED_PROOF_NODES
    assert sum(receipt.proof_nodes for receipt in actual) == 719
    assert max(receipt.proof_depth for receipt in actual) == 45


@pytest.mark.parametrize(("name", "expected"), EXPECTED_ROOTS.items())
def test_major_g101_statement_roots_are_frozen(name: str, expected: str) -> None:
    assert sha256(_row(name).statement.encode()).hexdigest() == expected


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_false_g101_conclusions_are_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {row.name: row for row in rows()}
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_g101_proof_bodies_are_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, script=original.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {row.name: row for row in rows()}
        )


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOTS))
def test_removed_major_g101_dependencies_are_rejected(name: str) -> None:
    original = _row(name)
    forged = replace(original, dependencies=original.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {row.name: row for row in rows()}
        )


@pytest.mark.parametrize(
    ("builder", "arguments", "names"),
    (
        (candidate.euclidean_bounded_trace, ("a", "b", "B"), {"a", "b", "B"}),
        (
            candidate.euclidean_logarithmic_execution,
            ("a", "b", "l", "g", "k"),
            {"a", "b", "l", "g", "k"},
        ),
    ),
)
def test_relations_are_conservative_hygienic_and_alpha_invariant(
    builder, arguments: tuple[str, ...], names: set[str]
) -> None:
    first, first_free = parse_formula_with_names(builder(*arguments, tag="first"))
    second, second_free = parse_formula_with_names(builder(*arguments, tag="second"))
    assert set(first_free) == set(second_free) == names
    assert first == second
    assert "BitLen" not in builder(*arguments, tag="first")
    assert "Euclid" not in builder(*arguments, tag="first")


@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_relations_reject_malicious_or_non_identifier_arguments(fragment: str) -> None:
    with pytest.raises(ValueError):
        candidate.euclidean_bounded_trace(fragment, "b", "B", tag="safe")
    with pytest.raises(ValueError):
        candidate.euclidean_logarithmic_execution(fragment, "b", "l", "g", "k", tag="safe")


@pytest.mark.parametrize("fragment", ("", "S", "forall", "a + b", "0", "a;b"))
def test_relations_reject_malicious_or_non_identifier_binder_tags(fragment: str) -> None:
    with pytest.raises(ValueError):
        candidate.euclidean_bounded_trace("a", "b", "B", tag=fragment)
    with pytest.raises(ValueError):
        candidate.euclidean_logarithmic_execution("a", "b", "l", "g", "k", tag=fragment)


def test_relations_reject_generated_binder_capture() -> None:
    with pytest.raises(ValueError, match="captures"):
        candidate.euclidean_bounded_trace("elb_list_capture", "b", "B", tag="capture")
    with pytest.raises(ValueError, match="captures"):
        candidate.euclidean_logarithmic_execution(
            "elb_bound_gap_capture", "b", "l", "g", "k", tag="capture"
        )


def test_exact_g101_root_has_bit_length_guard_gcd_anchor_and_blueprint_budget() -> None:
    formula = _closed_formula(_row(candidate.EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_BOUND).statement)
    for _ in range(3):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    assert isinstance(formula.consequent, Exists)
    assert isinstance(formula.consequent.body, Exists)
    conclusion = formula.consequent.body.body
    assert isinstance(conclusion, And)
    assert isinstance(conclusion.right, Exists)
    assert "2 * l + 1" in _row(candidate.EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_BOUND).statement


def test_all_witnesses_exist_unconditionally_in_the_closed_g101_root() -> None:
    formula = _closed_formula(_row(candidate.EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_EXISTS).statement)
    for _ in range(2):
        assert isinstance(formula, Forall)
        formula = formula.body
    for _ in range(3):
        assert isinstance(formula, Exists)
        formula = formula.body
    assert isinstance(formula, And)
    assert isinstance(formula.right, And)
    assert "2 * l + 1" in _row(candidate.EUCLIDEAN_GCD_EXECUTION_LOGARITHMIC_EXISTS).statement


@pytest.mark.parametrize(
    ("dividend", "divisor"),
    ((0, 0), (1, 0), (0, 1), (1, 1), (8, 5), (34, 21), (89, 55), (233, 144)),
)
def test_bounded_concrete_examples_agree_with_the_constructive_root(
    dividend: int, divisor: int
) -> None:
    certificate = certify_euclidean_execution(dividend, divisor)
    bit_length = binary_length_certificate(divisor)
    assert verify_euclidean_execution(certificate)
    assert certificate.step_count <= 2 * bit_length.length
    assert certificate.step_count <= 2 * bit_length.length + 1
    assert bit_length.length == max(1, divisor.bit_length())


def test_small_host_examples_are_demonstrations_not_formal_proof_authority() -> None:
    for dividend in range(65):
        for divisor in range(65):
            left, right = dividend, divisor
            steps = 0
            while right:
                left, right = right, left % right
                steps += 1
            assert steps <= 2 * max(1, divisor.bit_length())
