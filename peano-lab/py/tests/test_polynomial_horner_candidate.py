"""Exact constructive T12 audit: coded polynomial Horner traces."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import Exists, Forall, parse_formula_with_names
from peano_lab.library import editions_v19 as v19
from peano_lab.library import polynomial_horner_candidate as candidate
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "beta_prefix_horner_trace_exists",
    "beta_horner_eval_exists",
    "beta_horner_trace_functional",
    "beta_horner_eval_functional",
    "beta_horner_eval_exists_unique",
    "beta_horner_eval_empty",
    "beta_horner_eval_successor_decompose",
)

EXPECTED_ORDERED_NAMES_SHA256 = (
    "35bdc3b8db16900c372f840b08928484d6f1843bfeb483f8d58ced837d4274f3"
)
EXPECTED_ROOT_STATEMENT_SHA256 = (
    "bd1fa1601bd14a7dd6e769eb49bb646326d12f9a26d206c89eea1c7de54ac7d3"
)
EXPECTED_PROOF_NODES = (183, 29, 197, 62, 58, 51, 72)
EXPECTED_PROOF_DEPTHS = (44, 16, 43, 36, 34, 29, 29)


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_polynomial_horner_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v19.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_seven_exact_polynomial_theorems_are_closed_dependency_ordered() -> None:
    actual = rows()
    assert len(actual) == 7
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        EXPECTED_ORDERED_NAMES_SHA256
    )
    assert sum(len(item.dependencies) for item in actual) == 25
    assert sum(len(item.script) for item in actual) == 441
    prior: set[str] = set()
    for item in actual:
        parsed, free = parse_formula_with_names(item.statement)
        assert not free
        assert parsed == _closed_formula(item.statement)
        assert set(item.dependencies) <= set(core()) | prior
        assert item.name not in v19.ALPHA_EDITION.by_name
        assert not any(
            "DNE" in command or command.startswith("use ")
            for command in item.script
        )
        prior.add(item.name)


def test_every_polynomial_proof_body_passes_the_original_heyting_kernel() -> None:
    actual = receipts()
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert tuple(item.proof_nodes for item in actual) == EXPECTED_PROOF_NODES
    assert tuple(item.proof_depth for item in actual) == EXPECTED_PROOF_DEPTHS
    assert all(item.proof_nodes == item.proof_objects for item in actual)
    assert sum(item.proof_nodes for item in actual) == 652


def test_exact_t12_root_constructs_a_real_beta_coded_horner_execution() -> None:
    root = rows()[1]
    assert root.name == candidate.BETA_HORNER_EVAL_EXISTS
    assert sha256(root.statement.encode()).hexdigest() == (
        EXPECTED_ROOT_STATEMENT_SHA256
    )
    assert "* t +" in root.statement
    assert "S (0)" in root.statement
    formula = _closed_formula(root.statement)
    for _ in range(4):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Exists)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_polynomial_conclusions_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")
    available = core() | {item.name: item for item in rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=available)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_polynomial_scripts_cannot_become_evidence(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, script=original.script[:-1])
    available = core() | {item.name: item for item in rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=available)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_omitted_polynomial_dependencies_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, dependencies=original.dependencies[:-1])
    available = core() | {item.name: item for item in rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=available)


@pytest.mark.parametrize(
    ("argument", "value"),
    (
        (0, "forall"),
        (1, "c) -> false"),
        (2, "S"),
        (3, ""),
        (4, "n + 1"),
        (0, "ff_u_ph_x"),
    ),
)
def test_conservative_horner_surface_rejects_injection_and_capture(
    argument: int, value: str
) -> None:
    values = ["b", "c", "t", "l", "n"]
    values[argument] = value
    with pytest.raises(candidate.PolynomialHornerError):
        candidate.horner_relation(*values, tag="x")


@pytest.mark.parametrize("tag", ("", "forall", "tag) /\\ false", "S"))
def test_conservative_horner_surface_rejects_unsafe_tags(tag: str) -> None:
    with pytest.raises(candidate.PolynomialHornerError):
        candidate.horner_relation("b", "c", "t", "l", "n", tag=tag)


def test_duplicate_horner_arguments_are_rejected() -> None:
    with pytest.raises(candidate.PolynomialHornerError, match="distinct"):
        candidate.horner_relation("b", "c", "b", "l", "n", tag="safe")


@pytest.mark.parametrize(
    ("coefficients", "base", "value"),
    (
        ((), 0, 0),
        ((), 37, 0),
        ((0,), 19, 0),
        ((7,), 0, 7),
        ((7,), 11, 7),
        ((1, 2, 3), 0, 3),
        ((1, 2, 3), 1, 6),
        ((1, 2, 3), 2, 11),
        ((4, 0, 5, 8), 3, 131),
        ((9, 8, 7, 6, 5), 10, 98_765),
        ((1, 0, 0, 0, 0, 1), 2, 33),
        ((2, 3, 5, 7, 11, 13), 17, 3_117_065),
    ),
)
def test_executable_horner_trace_checks_concrete_research_examples(
    coefficients: tuple[int, ...], base: int, value: int
) -> None:
    receipt = candidate.evaluate_horner(coefficients, base)
    assert receipt.value == value
    assert len(receipt.steps) == len(coefficients)
    assert candidate.verify_horner_evaluation(receipt)
    assert receipt.value == sum(
        coefficient * base ** (len(coefficients) - index - 1)
        for index, coefficient in enumerate(coefficients)
    )


@pytest.mark.parametrize("base", (-1, True, 1.5, "2"))
def test_executable_horner_rejects_nonnatural_bases(base: object) -> None:
    with pytest.raises(candidate.PolynomialHornerError, match="base"):
        candidate.evaluate_horner((1, 2), base)  # type: ignore[arg-type]


@pytest.mark.parametrize("values", ((-1,), (True,), (1.5,), ("1",)))
def test_executable_horner_rejects_nonnatural_coefficients(
    values: tuple[object, ...],
) -> None:
    with pytest.raises(candidate.PolynomialHornerError, match="coefficient"):
        candidate.evaluate_horner(values, 2)  # type: ignore[arg-type]


def test_executable_horner_rejects_oversized_degree() -> None:
    with pytest.raises(candidate.PolynomialHornerError, match="certificate size"):
        candidate.evaluate_horner((0,) * (candidate.MAX_HORNER_COEFFICIENTS + 1), 2)


def test_executable_horner_rejects_oversized_bit_budget() -> None:
    with pytest.raises(candidate.PolynomialHornerError, match="bit budget"):
        candidate.evaluate_horner((1,), 1 << candidate.MAX_HORNER_OUTPUT_BITS)


def test_concrete_trace_verifier_rejects_altered_terminal_value() -> None:
    receipt = candidate.evaluate_horner((2, 5, 7), 11)
    assert not candidate.verify_horner_evaluation(replace(receipt, value=receipt.value + 1))


def test_concrete_trace_verifier_rejects_altered_step() -> None:
    receipt = candidate.evaluate_horner((2, 5, 7), 11)
    forged = replace(receipt.steps[1], result=receipt.steps[1].result + 1)
    assert not candidate.verify_horner_evaluation(
        replace(receipt, steps=(receipt.steps[0], forged, receipt.steps[2]))
    )


def test_concrete_trace_verifier_rejects_removed_and_reordered_steps() -> None:
    receipt = candidate.evaluate_horner((2, 5, 7), 11)
    assert not candidate.verify_horner_evaluation(replace(receipt, steps=receipt.steps[:-1]))
    assert not candidate.verify_horner_evaluation(
        replace(receipt, steps=tuple(reversed(receipt.steps)))
    )


@pytest.mark.parametrize("forged", (None, (), 0, True, {"value": 5}))
def test_concrete_trace_verifier_rejects_noncertificates(forged: object) -> None:
    assert not candidate.verify_horner_evaluation(forged)  # type: ignore[arg-type]
