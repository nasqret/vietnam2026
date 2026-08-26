"""Exact constructive binary-length candidates and adversarial proof checks."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import binary_length_candidate as candidate
from peano_lab.library import editions_v21 as v21
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "binary_length_digit_bounded",
    "binary_length_digit_split_exists",
    "binary_length_digit_split_functional",
    "binary_length_digit_split_exists_unique",
    "binary_power_two_exists",
    "binary_power_two_functional",
    "binary_power_two_zero_value",
    "binary_power_two_nonzero",
    "binary_power_two_successor_double",
    "binary_power_two_strict_growth",
    "binary_power_two_exponent_monotone",
    "binary_power_two_exponent_strict",
    "binary_length_zero",
    "binary_length_one",
    "binary_length_zero_input_value",
    "binary_length_successor_step",
    "binary_length_exists",
    "binary_length_zero_input_general",
    "binary_length_functional",
    "binary_length_exists_unique",
    "binary_length_power_exact",
)

EXPECTED_PROOF_NODES = (
    37, 7, 47, 43, 11, 27, 20, 34, 27, 36, 47, 39,
    4, 96, 57, 140, 20, 32, 170, 31, 44,
)

EXPECTED_ROOTS = {
    "binary_length_digit_split_exists_unique": (
        "bf2906055d6d4f86dfc8239c3c88f26883d7ea77b438166a14efa629ea28ffbf"
    ),
    "binary_power_two_exponent_strict": (
        "c5d8952c8ff9fdcf592f00cb18ec79a7d83792f5761c64799f03d796f11a3cdc"
    ),
    "binary_length_exists": (
        "53b6739ac80ec864c4b36aecdbca366e4bc997a8a45e5a1ef2daaf05dbde7778"
    ),
    "binary_length_functional": (
        "4b14a06b7b09b4b54be5cbc0c0a22110d029c5e57a16e126f2f9298eca7f9e7f"
    ),
    "binary_length_exists_unique": (
        "4365c8d9b855b85331e421d1c5e82349c598097f22dfe65141738573ee7ae89e"
    ),
    "binary_length_power_exact": (
        "69eace7cc1b3f3f0b2a5b3694e4c43d54124099b5f2c7102ed705bb73cd7868f"
    ),
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_binary_length_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v21.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_binary_length_theorems_are_closed_fresh_and_dependency_ordered() -> None:
    actual = rows()
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        "150dae13f4587c0787717d537e98612c022a655eb9721a5db6ee84af921e281c"
    )
    assert sum(len(item.dependencies) for item in actual) == 50
    assert sum(len(item.script) for item in actual) == 542
    known = set(core())
    for item in actual:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert set(item.dependencies) <= known
        assert item.name not in core()
        assert not any(
            command in {"sorry", "admit"}
            or "DNE" in command
            or command.startswith("use ")
            for command in item.script
        )
        known.add(item.name)


def test_every_binary_length_body_passes_the_original_kernel() -> None:
    actual = receipts()
    assert tuple(receipt.name for receipt in actual) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in actual) == EXPECTED_PROOF_NODES
    assert sum(receipt.proof_nodes for receipt in actual) == 969


@pytest.mark.parametrize(("name", "expected"), EXPECTED_ROOTS.items())
def test_binary_length_major_statement_roots_are_immutable(name: str, expected: str) -> None:
    row = next(item for item in rows() if item.name == name)
    assert sha256(row.statement.encode()).hexdigest() == expected


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_binary_length_conclusions_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_binary_length_proof_bodies_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, script=original.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


@pytest.mark.parametrize("name", tuple(EXPECTED_ROOTS))
def test_missing_binary_length_dependencies_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    assert original.dependencies
    forged = replace(original, dependencies=original.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


@pytest.mark.parametrize(
    ("surface", "arguments", "expected"),
    (
        (candidate.binary_power_relation, ("e", "p"), {"e", "p"}),
        (candidate.binary_digit_relation, ("n", "h", "b"), {"n", "h", "b"}),
        (candidate.binary_length_relation, ("n", "l"), {"n", "l"}),
    ),
)
def test_binary_surfaces_are_conservative_and_hygienic(surface, arguments, expected) -> None:
    formula, free_names = parse_formula_with_names(surface(*arguments, tag="safe"))
    assert formula is not None
    assert set(free_names) == expected
    assert "PowTwo" not in surface(*arguments, tag="safe")
    with pytest.raises(candidate.BinaryLengthError):
        surface("n + 1", *arguments[1:], tag="safe")
    with pytest.raises(candidate.BinaryLengthError):
        surface(*arguments, tag="safe) -> false")


def test_binary_power_rejects_generated_power_binder_capture() -> None:
    with pytest.raises(candidate.BinaryLengthError, match="captures"):
        candidate.binary_power_relation("pa_b_bl_safe", "p", tag="safe")


def test_binary_length_rejects_generated_exponent_binder_capture() -> None:
    with pytest.raises(candidate.BinaryLengthError, match="captures"):
        candidate.binary_length_relation("ff_exponent_bl_safe", "l", tag="safe")


def test_blueprint_zero_convention_is_explicit_and_exact() -> None:
    source = candidate.binary_length_relation("n", "l", tag="safe")
    assert "((n) = 0 /\\ (l) = 1)" in source
    zero = candidate.binary_length_certificate(0)
    assert zero.length == 1
    assert zero.digits_least_significant_first == (0,)
    assert zero.quotient_history == (0, 0)


def test_all_small_concrete_binary_histories_are_complete() -> None:
    for value in range(2049):
        certificate = candidate.binary_length_certificate(value)
        assert certificate.length == max(1, value.bit_length())
        assert len(certificate.digits_least_significant_first) == certificate.length
        assert len(certificate.quotient_history) == certificate.length + 1
        assert certificate.quotient_history[0] == value
        assert certificate.quotient_history[-1] == 0
        reconstructed = sum(
            digit << index
            for index, digit in enumerate(certificate.digits_least_significant_first)
        )
        assert reconstructed == value
        if value:
            assert certificate.lower_power <= value < certificate.upper_power


@pytest.mark.parametrize("value", (-1, True, False, 1.0, "2", None))
def test_non_natural_binary_certificate_inputs_are_rejected(value) -> None:
    with pytest.raises(candidate.BinaryLengthError):
        candidate.binary_length_certificate(value)


def test_binary_certificate_rejects_unbounded_integer_inputs() -> None:
    with pytest.raises(candidate.BinaryLengthError, match="bit cap"):
        candidate.binary_length_certificate(1 << candidate.MAX_BINARY_LENGTH_VALUE_BITS)


def test_binary_certificate_rejects_histories_past_the_entry_cap(monkeypatch) -> None:
    monkeypatch.setattr(candidate, "MAX_BINARY_LENGTH_HISTORY_ENTRIES", 2)
    with pytest.raises(candidate.BinaryLengthError, match="entry cap"):
        candidate.binary_length_certificate(4)
