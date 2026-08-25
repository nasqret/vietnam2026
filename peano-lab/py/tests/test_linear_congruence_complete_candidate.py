"""Unchanged-kernel audit of the complete constructive G012 campaign."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from math import gcd

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, Or, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v18
from peano_lab.library import linear_congruence_complete_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _primitive, _specs_by_name


EXPECTED_NAMES = (
    "linear_congruence_zero_residue_divides",
    "linear_congruence_solution_forces_gcd_divisibility",
    "linear_congruence_gcd_divisibility_constructs_solution",
    "linear_congruence_all_moduli_solvable_iff_gcd_divides",
    "linear_congruence_nonzero_modulus_bounded_constructor",
    "linear_congruence_solvable_iff_gcd_divides",
    "linear_congruence_zero_modulus_exact_divisibility",
    "linear_congruence_certified_decision",
    "linear_congruence_coprime_bounded_solution_unique",
)

EXPECTED_STATEMENT_SHA256 = {
    "linear_congruence_zero_residue_divides": "99a704757b826a6701a465152622e2dc31c9f41e5231be598d7bb2d2fc9de638",
    "linear_congruence_solution_forces_gcd_divisibility": "12ad93efc25ed5d19e370b574a5b110dad22e05b7cadae7d91f7dec73b119d95",
    "linear_congruence_gcd_divisibility_constructs_solution": "96ab3900241db0f8c119e1e616670676777e3633c5da4ed736370330e1dfdade",
    "linear_congruence_all_moduli_solvable_iff_gcd_divides": "1b882e712941cf407e2659df2c5d06d9638f1c945a2d3749d147080999f7e2c2",
    "linear_congruence_nonzero_modulus_bounded_constructor": "492687d1d6d632b8c0446a4e42aba3ed3aeb1b9043cd163f124153790b2d67e7",
    "linear_congruence_solvable_iff_gcd_divides": "808ae7b7b17bc3c2a027e76aff9d4f7d58157d50ce20ee50e323631b2b02296e",
    "linear_congruence_zero_modulus_exact_divisibility": "4530a8d5219a04d93eb9d7af6db0a58ba5191ba5a4b7c08d57158bcadbac86af",
    "linear_congruence_certified_decision": "05fd9ceef70345fc194dcd6ecd8ddd516c6914527fd513f82dd318278e2338ac",
    "linear_congruence_coprime_bounded_solution_unique": "0aff7df71c530f62e2aff992a54e2a61dd84a6899174b1de7f01e6c0283c2fd6",
}

# Dependency count, command count, structural nodes, depth, proof objects,
# proof edges, and intentionally reused object identities.
EXPECTED_BODY_RECEIPTS = {
    "linear_congruence_zero_residue_divides": (3, 17, 38, 22, 38, 37, 0),
    "linear_congruence_solution_forces_gcd_divisibility": (4, 35, 38, 22, 38, 37, 0),
    "linear_congruence_gcd_divisibility_constructs_solution": (4, 37, 42, 19, 42, 41, 0),
    "linear_congruence_all_moduli_solvable_iff_gcd_divides": (2, 24, 58, 23, 58, 57, 0),
    "linear_congruence_nonzero_modulus_bounded_constructor": (5, 50, 67, 29, 67, 66, 0),
    "linear_congruence_solvable_iff_gcd_divides": (2, 27, 69, 28, 69, 68, 0),
    "linear_congruence_zero_modulus_exact_divisibility": (2, 39, 57, 20, 57, 56, 0),
    "linear_congruence_certified_decision": (2, 26, 36, 19, 36, 35, 0),
    "linear_congruence_coprime_bounded_solution_unique": (4, 41, 48, 24, 48, 47, 0),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_linear_congruence_complete_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v18.ALPHA_CHECKED_SPECS}


def _available() -> dict[str, TheoremSpec]:
    return _core() | {row.name: row for row in _rows()}


def _row(name: str) -> TheoremSpec:
    return next(item for item in _rows() if item.name == name)


def _curried_certificate(name: str) -> tuple[Proof, object]:
    row = _row(name)
    target = _closed_formula(row.statement)
    available = _available()
    for dependency in reversed(row.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    state = start(target)
    for dependency in row.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in row.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _walk(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        yield item
        pending.extend(
            child
            for field in fields(item)
            if isinstance((child := getattr(item, field.name)), Proof)
        )


def test_linear_campaign_has_exact_deterministic_order_and_frozen_statements() -> None:
    rows = _rows()
    assert rows == candidate.make_linear_congruence_complete_candidate_theorems(
        TheoremSpec
    )
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert {
        row.name: sha256(row.statement.encode("utf-8")).hexdigest()
        for row in rows
    } == EXPECTED_STATEMENT_SHA256
    assert sha256("\n".join(EXPECTED_NAMES).encode("utf-8")).hexdigest() == (
        "385fb6bbf6fc423ffec7dfeee70740aae6b4796ec4138d5f8fac7028430333f5"
    )


def test_linear_campaign_depends_only_on_previous_rows_and_closed_v18_theorems() -> None:
    seen: set[str] = set()
    for row in _rows():
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(_core()) | seen
        external = set(row.dependencies) - seen
        assert all(editions_v18.ALPHA_EDITION.by_name[name].checked_use for name in external)
        assert all(
            editions_v18.ALPHA_EDITION.by_name[name].membership.value == "stable"
            for name in external
        )
        seen.add(row.name)


def test_candidates_remain_outside_the_sealed_alpha_v18_and_stable_registry() -> None:
    stable = _specs_by_name()
    for row in _rows():
        assert row.name not in stable
        assert row.name not in editions_v18.ALPHA_EDITION.by_name


def test_all_linear_campaign_formulas_are_closed_unextended_first_order_ha() -> None:
    for row in _rows():
        parsed, free = parse_formula_with_names(row.statement)
        assert not free
        assert parsed == _closed_formula(row.statement)
        assert all(
            forbidden not in row.statement
            for forbidden in (
                "IsGCD(",
                "Gcd(",
                "ModEq(",
                "Dvd(",
                "CRT(",
                "%",
                "^",
            )
        )
        assert all("DNE" not in command and "classical" not in command for command in row.script)


def test_all_nine_bodies_are_accepted_by_the_unchanged_independent_kernel() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_core())
    observed = {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    }
    assert observed == EXPECTED_BODY_RECEIPTS
    assert max(receipt.proof_nodes for receipt in receipts) == 69
    assert max(receipt.proof_depth for receipt in receipts) == 29


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_kernel_rejects_each_corrupted_linear_congruence_conclusion(name: str) -> None:
    row = _row(name)
    corrupted = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=_available())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_kernel_rejects_each_truncated_linear_congruence_script(name: str) -> None:
    row = _row(name)
    corrupted = replace(row, script=row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=_available())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_kernel_rejects_each_missing_declared_linear_congruence_dependency(name: str) -> None:
    row = _row(name)
    corrupted = replace(row, dependencies=row.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=_available())


def test_exact_g012_root_requires_nonzero_modulus_and_strictly_bounded_witness() -> None:
    formula = _closed_formula(
        _row(candidate.LINEAR_CONGRUENCE_SOLVABLE_IFF_GCD_DIVIDES).statement
    )
    for _ in range(4):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)  # The supplied relational gcd certificate.
    nonzero = formula.consequent
    assert isinstance(nonzero, Imp)
    assert isinstance(nonzero.antecedent, Imp)
    assert isinstance(nonzero.antecedent.antecedent, Eq)
    assert isinstance(nonzero.antecedent.consequent, Bot)
    equivalence = nonzero.consequent
    assert isinstance(equivalence, And)
    assert isinstance(equivalence.left, Imp)
    assert isinstance(equivalence.right, Imp)
    solvability = equivalence.left.antecedent
    assert isinstance(solvability, Exists)
    assert isinstance(solvability.body, And)
    assert isinstance(solvability.body.left, Exists)  # gap + S(x) = m.
    assert isinstance(solvability.body.left.body, Eq)
    assert isinstance(solvability.body.right, Exists)  # Balanced congruence.
    assert isinstance(equivalence.left.consequent, Exists)  # gcd | b.
    assert equivalence.right.antecedent == equivalence.left.consequent
    assert equivalence.right.consequent == solvability


def test_all_modulus_root_has_no_fictitious_positive_modulus_hypothesis() -> None:
    formula = _closed_formula(
        _row(candidate.LINEAR_CONGRUENCE_ALL_MODULI_SOLVABLE_IFF_GCD_DIVIDES).statement
    )
    for _ in range(4):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    assert isinstance(formula.consequent, And)
    assert isinstance(formula.consequent.left.antecedent, Exists)
    assert not isinstance(formula.consequent.left.antecedent.body, And)


def test_zero_modulus_root_requires_equality_not_an_impossible_bounded_residue() -> None:
    formula = _closed_formula(
        _row(candidate.LINEAR_CONGRUENCE_ZERO_MODULUS_EXACT_DIVISIBILITY).statement
    )
    for _ in range(4):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    boundary = formula.consequent
    assert isinstance(boundary, Imp)
    assert isinstance(boundary.antecedent, Eq)
    assert isinstance(boundary.consequent, And)
    exact = boundary.consequent.left.antecedent
    assert isinstance(exact, Exists)
    assert isinstance(exact.body, Eq)


def test_decision_root_is_a_constructive_witness_or_real_obstruction() -> None:
    formula = _closed_formula(
        _row(candidate.LINEAR_CONGRUENCE_CERTIFIED_DECISION).statement
    )
    for _ in range(4):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    assert isinstance(formula.consequent, Or)
    assert isinstance(formula.consequent.left, Exists)
    assert isinstance(formula.consequent.right, Imp)
    assert isinstance(formula.consequent.right.consequent, Bot)
    assert formula.consequent.right.antecedent == formula.consequent.left


@pytest.mark.parametrize(
    "name",
    (
        candidate.LINEAR_CONGRUENCE_ALL_MODULI_SOLVABLE_IFF_GCD_DIVIDES,
        candidate.LINEAR_CONGRUENCE_SOLVABLE_IFF_GCD_DIVIDES,
        candidate.LINEAR_CONGRUENCE_ZERO_MODULUS_EXACT_DIVISIBILITY,
        candidate.LINEAR_CONGRUENCE_CERTIFIED_DECISION,
        candidate.LINEAR_CONGRUENCE_COPRIME_BOUNDED_SOLUTION_UNIQUE,
    ),
)
def test_important_certificates_have_no_classical_double_negation_rule(name: str) -> None:
    certificate, formula = _curried_certificate(name)
    assert check((), certificate, formula)
    assert all(not isinstance(node, DNE) for node in _walk(certificate))


@pytest.mark.parametrize(
    ("a", "m", "b", "expected"),
    (
        (6, 15, 9, (4, 9, 14)),
        (6, 15, 8, ()),
        (3, 7, 5, (4,)),
        (0, 7, 0, tuple(range(7))),
        (0, 7, 1, ()),
        (4, 1, 9, (0,)),
        (12, 18, 6, (2, 5, 8, 11, 14, 17)),
        (7, 13, 11, (9,)),
    ),
)
def test_bounded_numeric_examples_match_the_exact_gcd_criterion(
    a: int, m: int, b: int, expected: tuple[int, ...]
) -> None:
    assert m > 0
    solutions = tuple(x for x in range(m) if (a * x - b) % m == 0)
    assert solutions == expected
    assert bool(solutions) == (b % gcd(a, m) == 0)
    if gcd(a, m) == 1:
        assert len(solutions) == 1


@pytest.mark.parametrize(
    ("a", "b", "solvable"),
    ((7, 21, True), (7, 20, False), (0, 0, True), (0, 3, False), (1, 9, True)),
)
def test_zero_modulus_numeric_examples_are_exact_equations(
    a: int, b: int, solvable: bool
) -> None:
    gcd_value = gcd(a, 0)
    divisible = b == 0 if gcd_value == 0 else b % gcd_value == 0
    exact_solution = b == 0 if a == 0 else b % a == 0
    assert divisible == exact_solution == solvable
