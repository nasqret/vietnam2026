"""Fail-closed original-kernel tests for actual Fermat-four infinite descent."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import editions_v25 as v25
from peano_lab.library import fermat_four_descent_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.coprime_square_factor_candidate import make_coprime_square_factor_candidate_theorems
from peano_lab.library.pythagorean_fermat_four_candidate import fermat_four_strict_descent
from peano_lab.library.pythagorean_inverse_candidate import make_pythagorean_inverse_candidate_theorems
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "fermat_four_product_nonzero",
    "fermat_four_square_nonzero",
    "fermat_four_coprime_squares",
    "fermat_four_scaled_fourth_identity",
    "fermat_four_scaled_equation",
    "fermat_four_cancel_scaled_equation",
    "fermat_four_lt_add_positive",
    "fermat_four_root_lt_norm",
    "fermat_four_even_square_root",
    "fermat_four_double_product_commute",
    "fermat_four_odd_double_square_factors",
    "fermat_four_primitive_normalization",
    "fermat_four_nested_primitive_triangle",
    "fermat_four_second_parameter_descent",
    "fermat_four_primitive_square_triangle",
    "fermat_four_primitive_counterexample_swap",
    "fermat_four_primitive_odd_even_descent",
    "fermat_four_primitive_descent",
    "fermat_four_strict_descent_proved",
    "fermat_four_no_square",
    "fermat_four_no_fourth",
    "fermat_four_equation_height_nonzero",
    "fermat_four_square_solutions_have_zero_coordinate",
    "fermat_four_solutions_have_zero_coordinate",
    "fermat_four_complete_classification",
    "fermat_four_positive_sum_not_square",
)
EXPECTED_NAMES_SHA256 = "08f056f73a80bab76d79464c97e7c4632e6b09cb2fbb3a00c6706f4c29d4edba"
EXPECTED_STATEMENTS = {
    "fermat_four_primitive_normalization": "cc973a8899e25fcdd918ae57abfb71a29e25cf64056588f3f755231a3ff4902a",
    "fermat_four_strict_descent_proved": "a3d8f109acbc3a7a254ad16d0bd5560807da349e8e7d6dabc5bb727dbafde85e",
    "fermat_four_no_square": "2931b656d7b3fa9d5a7abb43237803705f1871882fa07e14f5caac2d7d348786",
    "fermat_four_no_fourth": "9c058a04f2efb7f105017c15d34a94522937627b0008a4ea06305b66e0077cde",
    "fermat_four_complete_classification": "92c99d3f0a218c2706416d7c8b362aee310df0db1180729b85165d4ab11788bd",
    "fermat_four_positive_sum_not_square": "ae59505ab1243e444869a6385357022e648728cb483e36ae9f97a1f0a404409b",
}
EXPECTED_BODY_NODES = (
    18, 19, 27, 14, 49, 49, 28, 60, 29, 20, 82, 143, 38,
    157, 50, 55, 226, 49, 46, 5, 5, 42, 42, 24, 218, 20,
)


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_fermat_four_descent_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {
        row.name: row
        for row in (
            *v25.ALPHA_CHECKED_SPECS,
            *make_coprime_square_factor_candidate_theorems(TheoremSpec),
            *make_pythagorean_inverse_candidate_theorems(TheoremSpec),
        )
    }


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_frozen_twenty_six_theorem_inventory() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert sum(len(row.dependencies) for row in rows()) == 93
    assert sum(len(row.script) for row in rows()) == 852


def test_all_dependencies_precede_theorem_without_unproved_descent() -> None:
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert row.script
        _closed_formula(row.statement)
        assert not any(command.startswith("use ") or "DNE" in command for command in row.script)
        available.add(row.name)


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_new_theorems_do_not_rewrite_immutable_parent(name: str) -> None:
    assert v25.entry(name, edition="alpha") is None
    assert v25.entry(name, edition="stable") is None


@pytest.mark.parametrize("name,expected", tuple(EXPECTED_STATEMENTS.items()))
def test_exact_major_first_order_statements(name: str, expected: str) -> None:
    row = next(row for row in rows() if row.name == name)
    assert sha256(row.statement.encode()).hexdigest() == expected


def test_original_kernel_accepts_every_actual_body() -> None:
    actual = receipts()
    assert tuple(row.name for row in actual) == EXPECTED_NAMES
    assert tuple(row.proof_nodes for row in actual) == EXPECTED_BODY_NODES
    assert sum(row.proof_nodes for row in actual) == 1_515
    assert max(row.proof_depth for row in actual) == 45


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_final_proof_step_is_rejected(name: str) -> None:
    row = next(row for row in rows() if row.name == name)
    broken = replace(row, script=row.script[:-1] + ("exact forged_fermat_descent",))
    with pytest.raises(CandidateBodyError, match="failed at command"):
        replay_candidate_bodies((broken,), core={**core(), **{item.name: item for item in rows()}})


def test_strict_descent_has_the_exact_historical_obligation() -> None:
    row = next(row for row in rows() if row.name == "fermat_four_strict_descent_proved")
    assert _closed_formula(row.statement) == _closed_formula(fermat_four_strict_descent(tag="audit"))
    assert set(row.dependencies) == {
        "fermat_four_primitive_normalization", "fermat_four_primitive_descent", "lt_of_lt_of_le"
    }


def test_final_G078_has_no_height_positivity_or_descent_premise() -> None:
    row = next(row for row in rows() if row.name == "fermat_four_positive_sum_not_square")
    expected = "forall x y z. ~(x = 0) -> ~(y = 0) -> ~(x * x * x * x + y * y * y * y = z * z)"
    assert _closed_formula(row.statement) == _closed_formula(expected)
    assert "~(z = 0)" not in row.statement
    assert "forall pff_" not in row.statement


def test_orientation_proof_cannot_assume_its_inverse() -> None:
    row = next(row for row in rows() if row.name == "fermat_four_primitive_odd_even_descent")
    broken = replace(row, dependencies=tuple(dep for dep in row.dependencies if dep != "pythagorean_primitive_odd_even_inverse"))
    with pytest.raises(CandidateBodyError, match="failed at command"):
        replay_candidate_bodies((broken,), core={**core(), **{item.name: item for item in rows()}})


def test_false_zero_coordinate_strengthening_is_rejected() -> None:
    row = next(row for row in rows() if row.name == "fermat_four_positive_sum_not_square")
    broken = replace(row, statement=row.statement.replace("~(y = 0) -> ", ""))
    with pytest.raises(CandidateBodyError, match="failed at command"):
        replay_candidate_bodies((broken,), core={**core(), **{item.name: item for item in rows()}})


@pytest.mark.parametrize(
    "helper,args",
    (
        (candidate.primitive_four_counterexample, ("a", "b", "h")),
        (candidate.fermat_four_descent_witness, ("a", "b", "h", "z")),
        (candidate.fermat_four_trivial_solution, ("a", "b", "h")),
    ),
)
def test_relations_are_hygienic_conservative_expansions(helper, args) -> None:
    first = helper(*args, tag="first")
    second = helper(*args, tag="second")
    assert parse_formula_in_context(first, list(args)) == parse_formula_in_context(second, list(args))
    assert not any(token in first for token in ("Fermat", "Coprime", "oracle", "descent("))


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "a+b", "two words"))
@pytest.mark.parametrize(
    "helper,args",
    (
        (candidate.primitive_four_counterexample, ("b", "h")),
        (candidate.fermat_four_descent_witness, ("b", "h", "z")),
        (candidate.fermat_four_trivial_solution, ("b", "h")),
    ),
)
def test_invalid_definition_arguments_fail_closed(helper, args, bad) -> None:
    with pytest.raises(candidate.FermatFourDescentError):
        helper(bad, *args, tag="checked")


@pytest.mark.parametrize("bad", ("", "S", "forall", "0", "a+b", "two words"))
def test_invalid_descent_tags_fail_closed(bad: str) -> None:
    with pytest.raises(candidate.FermatFourDescentError):
        candidate.fermat_four_descent_witness("a", "b", "h", "z", tag=bad)


def test_capturing_or_repeated_descent_coordinates_fail_closed() -> None:
    with pytest.raises(candidate.FermatFourDescentError, match="capture"):
        candidate.primitive_four_counterexample("pff_divisor_test", "b", "h", tag="test")
    with pytest.raises(candidate.FermatFourDescentError, match="capture"):
        candidate.fermat_four_descent_witness("a", "b", "h", "ffd_gap_test", tag="test")
    with pytest.raises(candidate.FermatFourDescentError, match="distinct"):
        candidate.fermat_four_descent_witness("a", "b", "h", "h", tag="test")


def test_bounded_natural_classification_includes_exact_zero_boundary() -> None:
    for a in range(18):
        for b in range(18):
            for h in range(18):
                assert (a**4 + b**4 == h**4) == ((a == 0 and b == h) or (b == 0 and a == h))
                if a**4 + b**4 == h * h:
                    assert a == 0 or b == 0


def test_explicit_strict_norm_measure_on_small_positive_parameters() -> None:
    for u in range(1, 15):
        for n in range(1, 15):
            m = u * u
            h = m * m + n * n
            assert u < h
