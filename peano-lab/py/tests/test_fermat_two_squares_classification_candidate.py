"""Bounded constructive audit of Fermat two-square classification bridges."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v12
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_two_squares_classification_candidate import (
    make_fermat_two_squares_classification_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_candidate import (
    make_fermat_two_squares_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_collision_norm_candidate import (
    make_fermat_two_squares_collision_norm_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_prime_candidate import (
    make_fermat_two_squares_prime_candidate_theorems,
)
from peano_lab.library.quadratic_supplement_minus_one_candidate import (
    make_quadratic_supplement_minus_one_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "two_square_add_swap_nested",
    "two_square_sum_square_expands",
    "two_square_absolute_difference_square_balance",
    "two_square_cross_product_interchange",
    "two_square_product_expands",
    "two_square_product_norm_blocks",
    "two_square_sum_square_blocks",
    "brahmagupta_fibonacci_two_square_identity",
    "two_square_representation_multiplicatively_closed",
    "zero_one_and_two_have_two_square_representations",
    "every_natural_square_is_sum_of_two_squares",
    "prime_is_two_or_odd",
    "prime_mod_four_trichotomy",
    "two_square_scaled_norm_identity",
    "negative_one_norm_multiple_yields_predecessor_residue",
    "prime_divisible_two_square_norm_unit_coordinate_yields_negative_one_root",
    "three_mod_four_prime_has_no_negative_one_root",
    "three_mod_four_prime_norm_divisor_forces_second_coordinate",
    "three_mod_four_prime_divides_two_square_norm_divides_both",
    "prime_is_two_squares_iff_two_or_one_mod_four",
)

EXPECTED_STATEMENT_SHA256 = {
    "two_square_add_swap_nested": "3e4f0e2202c60e8ecc760a871829c50f8abcd7a571f593126d1137fd0424a0e7",
    "two_square_sum_square_expands": "b8cb719bfab8b405216bc5c77ba44aaa6f5ba4dbe52c3afe9ef5ef1455b1a4d9",
    "two_square_absolute_difference_square_balance": "e50ecffb141f267a1eca543cf1613ebc7642bbf63856c33758fa899433f7b8a8",
    "two_square_cross_product_interchange": "fd0d611918933d28ce186ebe8c30ece9699bc7dc4a160baacea0e2e45beca71c",
    "two_square_product_expands": "70933a406d8f55ba82c80786454db9adb6d9cc94bad98755514abb0636d67479",
    "two_square_product_norm_blocks": "3f62498f3a7f84bf810993bf2355a6fd2b2fe4efe7e0625719b253ed1ff9ce7c",
    "two_square_sum_square_blocks": "8014c1d4320ef0cea27a3873d7bcd3043ab97c21ec4b558b2f0d8a47e592ea6f",
    "brahmagupta_fibonacci_two_square_identity": "9131766952969d2d05e170ce8bcd4cff48b629848c0ccb9eb5665cbe6ee770a7",
    "two_square_representation_multiplicatively_closed": "8e82cb5f76a2148032c1bce4e4a3a5b2d763af8cd26dd91d09512a7ad11b6e9f",
    "zero_one_and_two_have_two_square_representations": "45d884f5a28fcabb5d27a20c9afb30b60ba83fd137a55b3e553c1ffa9d680bb4",
    "every_natural_square_is_sum_of_two_squares": "a5669d80fce48f0c8f927c6a2ea0bc7dbba92a226a0253127fa8faed6936e785",
    "prime_is_two_or_odd": "16f7c86d7d08b95889beedb993cd702ea865293e12a2e1094226f39df896553e",
    "prime_mod_four_trichotomy": "9c0b74a6637891b14d8ae5dce4f12f4d7142f6f1075c5c8ff2778f1500a7c042",
    "two_square_scaled_norm_identity": "56703a8b2ca7983f1168e8fd575bade9a4fcd836afaca0a1ff90714262166d30",
    "negative_one_norm_multiple_yields_predecessor_residue": "852009fe029e7ff474dd64093b859f74ea93d012ddac652b0941d16e897889ed",
    "prime_divisible_two_square_norm_unit_coordinate_yields_negative_one_root": "1bee6ebe29a6e7ee2f84c4a7ae9a7c67dc42614254c25786d02ec780fff98f66",
    "three_mod_four_prime_has_no_negative_one_root": "5e5e6af2bc8345375f38893d63cb65baf96aac14076e4cc33b96e22ffd44d9f5",
    "three_mod_four_prime_norm_divisor_forces_second_coordinate": "124e56ceb225a3e6873e072d6538406d1327c429785cb3b7f1ef426880e1278d",
    "three_mod_four_prime_divides_two_square_norm_divides_both": "042e2ab7c4566a661204e54f8945e4101fec83bcec12f2614293917528f3fa7c",
    "prime_is_two_squares_iff_two_or_one_mod_four": "84184c6c9fccba3457f8db4cb5716f0e75e85fa2749f1db6471f902cbbe415d7",
}

# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_BODY_RECEIPTS = {
    "two_square_add_swap_nested": (2, 11, 21, 11, 21, 20, 0),
    "two_square_sum_square_expands": (4, 3, 46, 17, 43, 45, 3),
    "two_square_absolute_difference_square_balance": (7, 37, 220, 38, 205, 219, 15),
    "two_square_cross_product_interchange": (2, 12, 24, 13, 24, 23, 0),
    "two_square_product_expands": (3, 12, 48, 17, 47, 47, 1),
    "two_square_product_norm_blocks": (3, 11, 24, 14, 24, 23, 0),
    "two_square_sum_square_blocks": (4, 14, 28, 14, 28, 27, 0),
    "brahmagupta_fibonacci_two_square_identity": (6, 34, 53, 23, 53, 52, 0),
    "two_square_representation_multiplicatively_closed": (2, 24, 34, 22, 34, 33, 0),
    "zero_one_and_two_have_two_square_representations": (0, 11, 124, 16, 124, 123, 0),
    "every_natural_square_is_sum_of_two_squares": (0, 4, 12, 8, 12, 11, 0),
    "prime_is_two_or_odd": (2, 26, 35, 14, 35, 34, 0),
    "prime_mod_four_trichotomy": (2, 13, 16, 9, 16, 15, 0),
    "two_square_scaled_norm_identity": (2, 7, 22, 12, 22, 21, 0),
    "negative_one_norm_multiple_yields_predecessor_residue": (5, 14, 63, 28, 61, 62, 2),
    "prime_divisible_two_square_norm_unit_coordinate_yields_negative_one_root": (
        13,
        88,
        103,
        39,
        103,
        102,
        0,
    ),
    "three_mod_four_prime_has_no_negative_one_root": (1, 18, 22, 17, 22, 21, 0),
    "three_mod_four_prime_norm_divisor_forces_second_coordinate": (
        5,
        51,
        59,
        25,
        59,
        58,
        0,
    ),
    "three_mod_four_prime_divides_two_square_norm_divides_both": (
        4,
        46,
        55,
        21,
        55,
        54,
        0,
    ),
    "prime_is_two_squares_iff_two_or_one_mod_four": (5, 49, 122, 25, 122, 121, 0),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_classification_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    result = {row.name: row for row in editions_v12.ALPHA_SPECS}
    for factory in (
        make_fermat_two_squares_candidate_theorems,
        make_fermat_two_squares_collision_norm_candidate_theorems,
        make_fermat_two_squares_prime_candidate_theorems,
        make_quadratic_supplement_minus_one_candidate_theorems,
    ):
        result.update((row.name, row) for row in factory(TheoremSpec))
    return result


def _available() -> dict[str, TheoremSpec]:
    return _core() | {row.name: row for row in _rows()}


def _target(row: TheoremSpec, statement: str | None = None):
    available = _available()
    result = _closed_formula(row.statement if statement is None else statement)
    for dependency in reversed(row.dependencies):
        result = Imp(_closed_formula(available[dependency].statement), result)
    return result


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _certificate(name: str):
    row = next(item for item in _rows() if item.name == name)
    target = _target(row)
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


def test_classification_candidates_are_exact_ordered_and_registry_isolated() -> None:
    rows = _rows()
    assert rows == make_fermat_two_squares_classification_candidate_theorems(
        TheoremSpec
    )
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert {
        row.name: sha256(row.statement.encode("utf-8")).hexdigest() for row in rows
    } == EXPECTED_STATEMENT_SHA256

    stable = _specs_by_name()
    alpha = editions_v12.ALPHA_EDITION.by_name
    seen: set[str] = set()
    for row in rows:
        assert row.name not in stable
        assert row.name not in alpha
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= set(_core()) | seen
        seen.add(row.name)

    source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "fermat_two_squares_classification_candidate" not in source
    assert len(editions_v12.ALPHA_CHECKED_SPECS) == 570


def test_classification_formulas_are_closed_first_order_constructive_ha() -> None:
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            forbidden not in row.statement
            for forbidden in (
                "Prime(",
                "QuadraticResidue(",
                "TwoSquare(",
                "Dvd(",
                "abs(",
                "^",
            )
        )

    obstruction = next(
        row
        for row in _rows()
        if row.name == "three_mod_four_prime_divides_two_square_norm_divides_both"
    )
    assert "forall p a b." in obstruction.statement
    assert "(a) = (p) *" in obstruction.statement
    assert "(b) = (p) *" in obstruction.statement


def test_classification_candidate_bodies_have_exact_bounded_kernel_receipts() -> None:
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
    assert max(receipt.proof_nodes for receipt in receipts) == 220
    assert max(receipt.proof_depth for receipt in receipts) == 39


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_classification_certificates_are_dne_free_and_reject_false_targets(
    name: str,
) -> None:
    row = next(item for item in _rows() if item.name == name)
    certificate, target = _certificate(name)
    assert check((), certificate, target)
    assert not any(type(node) is DNE for node in _walk(certificate))
    assert not check(
        (),
        certificate,
        _target(row, f"({row.statement}) /\\ 0 = 1"),
    )


@pytest.mark.parametrize(
    ("name", "dependency"),
    (
        (
            "brahmagupta_fibonacci_two_square_identity",
            "two_square_absolute_difference_square_balance",
        ),
        (
            "two_square_representation_multiplicatively_closed",
            "natural_absolute_difference_exists",
        ),
        (
            "prime_divisible_two_square_norm_unit_coordinate_yields_negative_one_root",
            "prime_mod_inverse",
        ),
        (
            "three_mod_four_prime_has_no_negative_one_root",
            "quadratic_supplement_minus_one_nonresidue_iff_mod_four_three",
        ),
        (
            "three_mod_four_prime_norm_divisor_forces_second_coordinate",
            "prime_divisible_two_square_norm_unit_coordinate_yields_negative_one_root",
        ),
        (
            "three_mod_four_prime_divides_two_square_norm_divides_both",
            "three_mod_four_prime_norm_divisor_forces_second_coordinate",
        ),
    ),
)
def test_classification_essential_dependencies_are_live(
    name: str,
    dependency: str,
) -> None:
    row = next(item for item in _rows() if item.name == name)
    mutated = replace(
        row,
        dependencies=tuple(item for item in row.dependencies if item != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_available())


def test_classification_scripts_avoid_classical_logic_and_hidden_automation() -> None:
    commands = tuple(command for row in _rows() for command in row.script)
    assert "apply prime_mod_inverse" in commands
    assert "apply prime_coprime_or_divides" in commands
    assert "apply brahmagupta_fibonacci_two_square_identity" in commands
    assert all(not command.startswith(("ring", "auto", "omega")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


@pytest.mark.parametrize("modulus", (3, 7, 11, 19, 23, 31, 43, 47, 59))
def test_three_mod_four_prime_norm_divisors_force_both_coordinates(
    modulus: int,
) -> None:
    assert modulus % 4 == 3
    witnessed = 0
    for first, second in product(range(2 * modulus), repeat=2):
        if (first * first + second * second) % modulus == 0:
            assert first % modulus == 0
            assert second % modulus == 0
            witnessed += 1
    assert witnessed == 4


@pytest.mark.parametrize("modulus", (5, 13, 17, 29, 37, 41, 53, 61))
def test_one_mod_four_primes_are_real_counterexamples_to_the_obstruction(
    modulus: int,
) -> None:
    assert modulus % 4 == 1
    witnesses = [
        (first, second)
        for first, second in product(range(modulus), repeat=2)
        if first and second and (first * first + second * second) % modulus == 0
    ]
    assert witnesses


@pytest.mark.parametrize("first", range(7))
def test_two_square_multiplication_constructs_explicit_coordinates(
    first: int,
) -> None:
    for second, third, fourth in product(range(7), repeat=3):
        coordinate = first * third + second * fourth
        difference = abs(first * fourth - second * third)
        assert (first * first + second * second) * (
            third * third + fourth * fourth
        ) == coordinate * coordinate + difference * difference


def test_classification_rfc_distinguishes_foundations_from_completed_iff() -> None:
    repository = Path(__file__).resolve().parents[3]
    document = (
        repository
        / "research"
        / "arithmetic-library"
        / "fermat-two-squares-classification-rfc-v1.md"
    ).read_text(encoding="utf-8")
    assert "three_mod_four_prime_divides_two_square_norm_divides_both" in document
    assert "brahmagupta_fibonacci_two_square_identity" in document
    assert "not a complete all-integer classification" in document
    assert "two_square_iff_zero_or_even_three_mod_four_prime_valuations" in document
    assert "not enrolled in Alpha" in document
