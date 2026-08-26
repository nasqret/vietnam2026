"""Fail-closed original-kernel audit of constructive Taylor/Hensel lifting."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from math import gcd

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import editions_v24 as v24
from peano_lab.library import polynomial_taylor_hensel_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "hensel_predecessor_annihilates_residue",
    "horner_mod_congruence_successor_step",
    "horner_derivative_mod_congruence_successor_step",
    "beta_horner_eval_mod_congruence",
    "beta_horner_derivative_mod_congruence",
    "hensel_add_swap_nested",
    "horner_taylor_successor_identity",
    "beta_horner_taylor_remainder_exists",
    "hensel_correction_exists",
    "hensel_correction_unique",
    "hensel_correction_exists_unique",
    "horner_derivative_coprime_bounded_inverse",
    "beta_horner_taylor_square_congruence",
    "beta_horner_taylor_remainder_total",
    "hensel_correction_implies_multiple",
    "hensel_linear_correction_multiple",
    "hensel_square_shift_multiple",
    "beta_horner_hensel_lift_divisibility",
    "beta_horner_hensel_lift_exists",
)
EXPECTED_ORDERED_NAMES_SHA256 = (
    "f909e072a84a460d63971e51c54e034b10c54295b368ef2ce49b09d469c63e40"
)
EXPECTED_MAJOR_STATEMENTS = {
    "beta_horner_eval_mod_congruence": "dfd08efce5a7956818a6ae16d57d51a06f04625bd6fe7cf86322b413a421e085",
    "beta_horner_derivative_mod_congruence": "75e0e5ba874eafcc31d275521728a51b9634f6c97692fb75e2da5ebd858c992d",
    "horner_taylor_successor_identity": "6a7aa1e4d1bab4b7a5d29d77eff56da13b8c3c7e4bb467d4affa5909acd58f9a",
    "beta_horner_taylor_remainder_exists": "5df4c9bd62d28df38c7fdcd0daf41c5fddf518942db92a74ac3a17676033ed82",
    "hensel_correction_exists_unique": "116197e3bebc5a3e2ee9290c2826b209e4d7f3047121533cc22c8e32324c3d70",
    "horner_derivative_coprime_bounded_inverse": "de5bcdaf858ff49862071764ee8315dc577f85f85b298a8ff3821acaa0c48b6a",
    "beta_horner_taylor_square_congruence": "5081c247a8e789b8273d5139f87f576faad382e242f9d5b11f8158fe28700952",
    "beta_horner_taylor_remainder_total": "ae19d576245bae81bcdc62e9b26608a24cb9ad997ae7a84ebf89119accae48f4",
    "beta_horner_hensel_lift_divisibility": "9ddf76110a1036269b8a07f6d80cd83bd26ea3ed7c6416508e1193dc7bbc506b",
    "beta_horner_hensel_lift_exists": "9cfc4633ea27c492b0deb35a56fe44b25b8dbf50d56fb27f29285f74b6c58a8b",
}
EXPECTED_PROOF_NODES = (
    11, 32, 31, 112, 215, 21, 262, 151, 70, 57, 35, 24, 36, 45, 28, 46, 42, 80, 64
)
EXPECTED_PROOF_DEPTHS = (
    9, 21, 22, 34, 41, 11, 58, 38, 27, 24, 22, 18, 23, 23, 18, 21, 20, 37, 43
)


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_polynomial_taylor_hensel_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {row.name: row for row in v24.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_exact_nineteen_theorem_checked_frontier() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_ORDERED_NAMES_SHA256
    assert len(rows()) == 19
    assert sum(len(row.dependencies) for row in rows()) == 69
    assert sum(len(row.script) for row in rows()) == 867


def test_every_dependency_is_checked_earlier_without_classical_shortcuts() -> None:
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert row.script
        assert not any("DNE" in command or command.startswith("use ") for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_every_candidate_is_absent_from_immutable_v24_parent(name: str) -> None:
    assert v24.entry(name, edition="alpha") is None
    assert v24.entry(name, edition="stable") is None


@pytest.mark.parametrize("name,expected", tuple(EXPECTED_MAJOR_STATEMENTS.items()))
def test_major_expanded_first_order_statements_are_frozen(name: str, expected: str) -> None:
    row = next(item for item in rows() if item.name == name)
    assert sha256(row.statement.encode()).hexdigest() == expected


def test_unchanged_intuitionistic_kernel_accepts_all_nineteen_real_bodies() -> None:
    actual = receipts()
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert tuple(item.proof_nodes for item in actual) == EXPECTED_PROOF_NODES
    assert tuple(item.proof_depth for item in actual) == EXPECTED_PROOF_DEPTHS
    assert sum(item.proof_nodes for item in actual) == 1_362
    assert max(item.proof_nodes for item in actual) == 262
    assert max(item.proof_depth for item in actual) == 58


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_corrupted_tactic_body_fails_closed(name: str) -> None:
    row = next(item for item in rows() if item.name == name)
    broken = replace(row, script=row.script[:-1] + ("exact forged_taylor_proof",))
    with pytest.raises(CandidateBodyError, match="failed at command"):
        replay_candidate_bodies((broken,), core={**core(), **{item.name: item for item in rows()}})


@pytest.mark.parametrize(
    "helper,arguments",
    (
        (candidate.hensel_correction_relation, ("d", "p", "q", "t")),
        (
            candidate.horner_taylor_remainder_relation,
            ("b", "c", "a", "h", "l", "n", "d", "y", "q"),
        ),
    ),
)
def test_public_relations_are_hygienic_conservative_formulas(helper, arguments) -> None:
    first = helper(*arguments, tag="first")
    second = helper(*arguments, tag="second")
    assert parse_formula_in_context(first, list(arguments)) == parse_formula_in_context(
        second, list(arguments)
    )
    assert not any(word in first for word in ("Horner", "Taylor", "Beta", "oracle"))


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "x+y", "two words", "pth_x"))
def test_invalid_or_capturing_relation_arguments_fail_closed(bad: str) -> None:
    with pytest.raises(candidate.PolynomialTaylorHenselError):
        candidate.hensel_correction_relation(bad, "p", "q", "t", tag="ok")


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "x+y", "two words"))
def test_invalid_binder_tags_fail_closed(bad: str) -> None:
    with pytest.raises(candidate.PolynomialTaylorHenselError):
        candidate.hensel_correction_relation("d", "p", "q", "t", tag=bad)


def test_repeated_relation_argument_is_rejected() -> None:
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="distinct"):
        candidate.hensel_correction_relation("d", "p", "q", "d", tag="bad")


def test_taylor_root_contains_an_actual_quadratic_witness() -> None:
    row = next(item for item in rows() if item.name == "beta_horner_taylor_remainder_exists")
    assert "exists q. z = (n + h * d) + (h * h) * q" in row.statement


def test_actual_one_step_root_lift_has_exact_factor_and_divisibility_hypotheses() -> None:
    row = next(item for item in rows() if item.name == "beta_horner_hensel_lift_exists")
    assert "m = p * s" in row.statement
    assert "n = m * q" in row.statement
    assert "exists t y." in row.statement
    assert "exists w. y = (p * m) * w" in row.statement


@pytest.mark.parametrize("length", range(7))
@pytest.mark.parametrize("point", (0, 1, 2, 5))
@pytest.mark.parametrize("shift", (0, 1, 2, 4))
def test_exhaustive_bounded_taylor_identity(length: int, point: int, shift: int) -> None:
    coefficients = tuple(3 * index + 1 for index in range(length))
    receipt = candidate.evaluate_horner_taylor(coefficients, point, shift)
    assert candidate.verify_horner_taylor_evaluation(receipt)
    assert receipt.shifted_value == (
        receipt.value + shift * receipt.derivative + shift * shift * receipt.remainder
    )
    if shift == 0:
        assert receipt.remainder == 0


def test_exhaustive_small_coprime_canonical_corrections() -> None:
    for modulus in range(1, 13):
        for derivative in range(14):
            for quotient in range(11):
                if gcd(derivative, modulus) != 1:
                    with pytest.raises(candidate.PolynomialTaylorHenselError, match="coprime"):
                        candidate.compute_hensel_correction(derivative, modulus, quotient)
                    continue
                receipt = candidate.compute_hensel_correction(derivative, modulus, quotient)
                assert candidate.verify_hensel_correction(receipt)
                assert 0 <= receipt.digit < modulus
                assert (quotient + derivative * receipt.digit) % modulus == 0
                assert sum(
                    (quotient + derivative * digit) % modulus == 0
                    for digit in range(modulus)
                ) == 1


@pytest.mark.parametrize("bad", (-1, True, False, 1.0, "3", None))
def test_non_natural_taylor_points_and_shifts_fail_closed(bad) -> None:
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="natural"):
        candidate.evaluate_horner_taylor((1, 2), bad, 2)
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="natural"):
        candidate.evaluate_horner_taylor((1, 2), 2, bad)


@pytest.mark.parametrize("coefficients", ((1, -2), (True,), (1.0,), ("1",), (None,)))
def test_non_natural_taylor_coefficients_fail_closed(coefficients) -> None:
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="natural"):
        candidate.evaluate_horner_taylor(coefficients, 2, 1)


@pytest.mark.parametrize("bad", (-1, True, False, 1.0, "3", None))
def test_non_natural_correction_inputs_fail_closed(bad) -> None:
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="natural"):
        candidate.compute_hensel_correction(bad, 7, 1)
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="natural"):
        candidate.compute_hensel_correction(2, bad, 1)
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="natural"):
        candidate.compute_hensel_correction(2, 7, bad)


def test_zero_modulus_and_noncoprime_derivative_fail_closed() -> None:
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="nonzero"):
        candidate.compute_hensel_correction(1, 0, 2)
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="coprime"):
        candidate.compute_hensel_correction(6, 9, 2)


def test_oversized_inputs_and_coefficients_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(candidate, "MAX_HORNER_COEFFICIENTS", 2)
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="certificate size"):
        candidate.evaluate_horner_taylor((1, 2, 3), 2, 1)
    monkeypatch.setattr(candidate, "MAX_HORNER_OUTPUT_BITS", 5)
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="bit budget"):
        candidate.evaluate_horner_taylor((1,), 64, 1)
    with pytest.raises(candidate.PolynomialTaylorHenselError, match="bit budget"):
        candidate.compute_hensel_correction(65, 7, 2)


def test_forged_taylor_receipts_fail_closed() -> None:
    receipt = candidate.evaluate_horner_taylor((1, 2, 3), 2, 3)
    for field in ("point", "shift", "value", "derivative", "shifted_value", "remainder"):
        assert not candidate.verify_horner_taylor_evaluation(
            replace(receipt, **{field: getattr(receipt, field) + 1})
        )
    assert not candidate.verify_horner_taylor_evaluation(replace(receipt, remainder=True))
    assert not candidate.verify_horner_taylor_evaluation(replace(receipt, coefficients=(1, 3, 2)))
    assert not candidate.verify_horner_taylor_evaluation(None)


def test_forged_canonical_correction_receipts_fail_closed() -> None:
    receipt = candidate.compute_hensel_correction(3, 7, 5)
    for field in ("derivative", "modulus", "quotient", "inverse", "digit"):
        assert not candidate.verify_hensel_correction(
            replace(receipt, **{field: getattr(receipt, field) + 1})
        )
    assert not candidate.verify_hensel_correction(replace(receipt, digit=True))
    assert not candidate.verify_hensel_correction(None)


@pytest.mark.parametrize(
    "name",
    (
        "simple_root_hensel_lifting",
        "polynomial_hensel_lift_exists_unique",
        "prime_power_simple_root_hensel_lift",
    ),
)
def test_full_canonical_prime_power_hensel_milestone_is_not_silently_claimed(name: str) -> None:
    assert name not in {row.name for row in rows()}
    assert v24.entry(name, edition="alpha") is None
