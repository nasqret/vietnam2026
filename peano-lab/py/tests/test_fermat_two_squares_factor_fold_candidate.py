"""Bounded kernel audit of constructive beta-coded two-square factor folds."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from math import isqrt, prod

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.fermat_two_squares_classification_candidate import (
    make_fermat_two_squares_classification_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_factor_fold_candidate import (
    admissible_prime_factor_prefix,
    all_prime_factor_prefix,
    grouped_prime_square_factor_prefix,
    make_fermat_two_squares_factor_fold_candidate_theorems,
    represented_factor_prefix,
    witnessed_represented_factor_prefix,
)
from peano_lab.library.fermat_two_squares_prime_candidate import (
    make_fermat_two_squares_prime_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "beta_two_square_prefix_drop_last",
    "beta_witnessed_two_square_prefix_implies_pointwise",
    "beta_two_square_prefix_last_represented",
    "beta_two_square_represented_factor_product",
    "beta_witnessed_two_square_factor_product",
    "prime_two_or_one_mod_four_is_sum_of_two_squares",
    "beta_all_prime_entry_is_prime",
    "beta_admissible_prime_factor_product_is_two_square",
    "represented_factor_product_times_square_is_two_square",
    "beta_grouped_prime_square_factor_product_is_two_square",
    "beta_product_adjacent_equal_pair_decomposes_as_square",
    "beta_two_square_prefix_append_equal_pair",
    "positive_number_with_admissible_prime_divisors_is_two_square",
)

EXPECTED_STATEMENT_SHA256 = {
    "beta_two_square_prefix_drop_last": "4c6f56681a0ab5b4459d96116ed6bc7c4aad07c5ec2ba03ae8fd797d11caba51",
    "beta_witnessed_two_square_prefix_implies_pointwise": "acd93c2b023b60c5a7c1042783d55a409ff1746df4a22f73991b9b864e22edce",
    "beta_two_square_prefix_last_represented": "80931105b1568bd4a027e0c0f67ebe5d695976917d2218f090f1ea87ae4f64a2",
    "beta_two_square_represented_factor_product": "66d4cf4c158802e854386ea6f68e565c64d34c1e3e0be7185c3d95782c833929",
    "beta_witnessed_two_square_factor_product": "9c4402743b3507e63989c7f73f6759fefa56ee8f09b0f641e1b958525f8ea875",
    "prime_two_or_one_mod_four_is_sum_of_two_squares": "17c7dd09ca15d3fc1aced5a5ff5c2472a8c92312c7b1cda31bf3ea18b17a6589",
    "beta_all_prime_entry_is_prime": "d62b71ab206b2ce20bbfc64b58ad7d0916baca7042b240e51c244337fb488410",
    "beta_admissible_prime_factor_product_is_two_square": "be01957e2cef2d73ba750277fc2a9a91b07d96b4eec8daa995859b5900cab703",
    "represented_factor_product_times_square_is_two_square": "9d0694a8e94a8464f5fc8c8b515b39b4e4bbc95a4aa0b3f271c86e2adf65f9c5",
    "beta_grouped_prime_square_factor_product_is_two_square": "01d0e9f98fa4f55a8b1ff4958ce1c5436c756be7e1e3b29dedf7705a85eeb20f",
    "beta_product_adjacent_equal_pair_decomposes_as_square": "764f04f04f5e218f9ecbd4a11821fa06fa22877dc00dc5d533f2ab72099cf0bb",
    "beta_two_square_prefix_append_equal_pair": "3424623feb8013a0d62b80f2f4f05e60f826c94685584f45fb74be0d52b8dd69",
    "positive_number_with_admissible_prime_divisors_is_two_square": "4f1877c55982623acfdc8c10d6244f00d0c97073e3701854c9f1243ce665fce1",
}

# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_BODY_RECEIPTS = {
    "beta_two_square_prefix_drop_last": (1, 16, 32, 21, 32, 31, 0),
    "beta_witnessed_two_square_prefix_implies_pointwise": (1, 29, 35, 24, 35, 34, 0),
    "beta_two_square_prefix_last_represented": (1, 12, 24, 16, 24, 23, 0),
    "beta_two_square_represented_factor_product": (5, 55, 106, 26, 106, 105, 0),
    "beta_witnessed_two_square_factor_product": (2, 17, 43, 25, 43, 42, 0),
    "prime_two_or_one_mod_four_is_sum_of_two_squares": (3, 22, 104, 22, 104, 103, 0),
    "beta_all_prime_entry_is_prime": (1, 26, 42, 21, 42, 41, 0),
    "beta_admissible_prime_factor_product_is_two_square": (2, 27, 40, 21, 40, 39, 0),
    "represented_factor_product_times_square_is_two_square": (3, 26, 31, 22, 31, 30, 0),
    "beta_grouped_prime_square_factor_product_is_two_square": (3, 35, 48, 22, 48, 47, 0),
    "beta_product_adjacent_equal_pair_decomposes_as_square": (3, 60, 78, 30, 78, 77, 0),
    "beta_two_square_prefix_append_equal_pair": (2, 31, 39, 22, 39, 38, 0),
    "positive_number_with_admissible_prime_divisors_is_two_square": (4, 47, 76, 27, 76, 75, 0),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_factor_fold_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    result = dict(_specs_by_name())
    for factory in (
        make_fermat_two_squares_classification_candidate_theorems,
        make_fermat_two_squares_prime_candidate_theorems,
    ):
        result.update((row.name, row) for row in factory(TheoremSpec))
    return result


def _target(row: TheoremSpec, statement: str | None = None):
    available = _core() | {item.name: item for item in _rows()}
    result = _closed_formula(row.statement if statement is None else statement)
    for dependency in reversed(row.dependencies):
        result = Imp(_closed_formula(available[dependency].statement), result)
    return result


@lru_cache(maxsize=4)
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


def test_factor_fold_candidates_are_exact_ordered_registry_isolated() -> None:
    rows = _rows()
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert {
        row.name: sha256(row.statement.encode("utf-8")).hexdigest() for row in rows
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    alpha = editions_v12.ALPHA_EDITION.by_name
    seen: set[str] = set()
    for row in rows:
        assert row.name not in public
        assert row.name not in alpha
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= set(_core()) | seen
        seen.add(row.name)
    assert len(editions_v12.ALPHA_CHECKED_SPECS) == 570


def test_factor_fold_formulas_are_closed_expanded_constructive_ha() -> None:
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            forbidden not in row.statement
            for forbidden in (
                "Prime(",
                "Product(",
                "BetaAt(",
                "TwoSquare(",
                "PowerValuation(",
                "Dvd(",
                "abs(",
                "^",
            )
        )
        assert all(
            forbidden not in command
            for command in row.script
            for forbidden in ("DNE", "by_contra", "classical", "sorry")
        )


def test_factor_fold_bodies_have_exact_bounded_kernel_receipts() -> None:
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
    assert max(receipt.proof_nodes for receipt in receipts) == 106
    assert max(receipt.proof_depth for receipt in receipts) == 30


@pytest.mark.parametrize(
    "name",
    (
        "beta_two_square_represented_factor_product",
        "beta_grouped_prime_square_factor_product_is_two_square",
        "beta_product_adjacent_equal_pair_decomposes_as_square",
        "positive_number_with_admissible_prime_divisors_is_two_square",
    ),
)
def test_factor_fold_flagship_certificates_reject_false_mutations(name: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    proof, target = _certificate(name)
    assert check((), proof, target)
    assert not check((), proof, _target(row, f"({row.statement}) /\\ 0 = 1"))
    assert all(not isinstance(node, DNE) for node in _walk(proof))


@pytest.mark.parametrize(
    "surface",
    (
        represented_factor_prefix,
        witnessed_represented_factor_prefix,
        all_prime_factor_prefix,
        admissible_prime_factor_prefix,
        grouped_prime_square_factor_prefix,
    ),
)
def test_factor_fold_surface_helpers_are_hygienic_and_expanded(surface) -> None:
    formula, free = parse_formula_with_names(
        f"forall b c l. ({surface('b', 'c', 'l', tag='audit')})"
    )
    assert not free
    assert formula == _closed_formula(
        f"forall b c l. ({surface('b', 'c', 'l', tag='audit')})"
    )
    with pytest.raises(ValueError):
        surface("b + c", "c", "l", tag="audit")
    with pytest.raises(ValueError):
        surface("b", "c", "l", tag="invalid-tag")


@pytest.mark.parametrize(
    ("good_factors", "paired_bad_primes"),
    (
        ((), ()),
        ((2,), ()),
        ((5,), ()),
        ((13,), ()),
        ((17, 29), ()),
        ((), (3,)),
        ((), (7,)),
        ((), (3, 7)),
        ((2,), (3,)),
        ((5,), (3,)),
        ((13,), (7,)),
        ((2, 5, 13), (3,)),
        ((5, 17), (3, 11)),
        ((2, 13, 29), (7,)),
    ),
)
def test_grouped_prime_blocks_have_small_constructive_examples(
    good_factors: tuple[int, ...], paired_bad_primes: tuple[int, ...]
) -> None:
    assert all(factor == 2 or factor % 4 == 1 for factor in good_factors)
    assert all(prime % 4 == 3 for prime in paired_bad_primes)
    number = prod(good_factors) * prod(prime * prime for prime in paired_bad_primes)
    assert any(
        (second := isqrt(number - first * first)) ** 2 == number - first * first
        for first in range(isqrt(number) + 1)
    )


@pytest.mark.parametrize("number", (3, 6, 7, 11, 15, 21, 27, 33, 42, 63))
def test_unpaired_bad_prime_examples_are_not_falsely_classified(number: int) -> None:
    assert not any(
        (second := isqrt(number - first * first)) ** 2 == number - first * first
        for first in range(isqrt(number) + 1)
    )
