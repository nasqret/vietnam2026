"""Bounded independent audit of constructive two-square pigeonhole bridges."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from math import isqrt

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.bertrand_floor_sqrt_total_candidate import (
    make_bertrand_floor_sqrt_total_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_two_squares_candidate import (
    make_fermat_two_squares_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_pigeonhole_candidate import (
    make_fermat_two_squares_pigeonhole_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "prime_is_not_natural_square",
    "natural_square_monotone_expanded",
    "prime_floor_square_strictly_below_prime",
    "prime_floor_bounded_coordinate_square_strict",
    "two_strict_values_sum_below_double",
    "prime_floor_bounded_two_square_norm_below_double",
    "floor_square_successor_grid_strictly_exceeds_input",
    "floor_square_oversized_grid_exists",
    "prime_floor_bounded_divisible_norm_represents_prime",
    "finite_bounded_into_oversized_not_injective",
    "floor_square_oversized_bounded_grid_not_injective",
    "finite_bounded_into_collision_from_constructive_decision",
)

EXPECTED_STATEMENT_SHA256 = {
    "prime_is_not_natural_square": "feeeebe26c5341bbb612b47a9a5f96788e12a7ec35e45319d2df46fb5ae82acb",
    "natural_square_monotone_expanded": "fd6e8dac9130e6bec44ae9e5ff9e286074a49d4d2864204dda939023c3ed0244",
    "prime_floor_square_strictly_below_prime": "55430d45328e8bef1236ef97ca65c54b9bf5643d591b00bc33395b8343da64f5",
    "prime_floor_bounded_coordinate_square_strict": "1c20955af1dce8fe7c83bf779e430ef9759a591c0a5e877e4c31270641ff4608",
    "two_strict_values_sum_below_double": "0bdd7be47c0a19b8e15f20e12c7c164dfbf983e0e4b0e51b6533768426785d5f",
    "prime_floor_bounded_two_square_norm_below_double": "56b5d419a7448cead4664ff334b21b62c0f7fc9449fd3b6fd37892eb8ef2a449",
    "floor_square_successor_grid_strictly_exceeds_input": "8d45d499eb88f60f65e25ede809c480451a87863f4a87b269e2e908feafa00b4",
    "floor_square_oversized_grid_exists": "2c4e81143ffe859436907efc74eea83e4d448fd14bb151c37ca8600bb22f5039",
    "prime_floor_bounded_divisible_norm_represents_prime": "ade8bc9ee800ba6d1930dca16d4d37f9ac43383cfd01ae81018e6ba504b9ee03",
    "finite_bounded_into_oversized_not_injective": "7c53db5855f093875477b5e6d26e2be3a2a0e0d035fdd5c7910f0ce46269d59a",
    "floor_square_oversized_bounded_grid_not_injective": "ba316988e91461397a65a2c678ba7c8e6e459bfc89b1b3c7d54d0fbce5198fca",
    "finite_bounded_into_collision_from_constructive_decision": "d79cbdab8d6d7f15727e9d723f587a1279a0e8e391fba05361268d5b7c859852",
}

# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_BODY_RECEIPTS = {
    "prime_is_not_natural_square": (0, 21, 89, 17, 89, 88, 0),
    "natural_square_monotone_expanded": (3, 21, 24, 13, 24, 23, 0),
    "prime_floor_square_strictly_below_prime": (2, 19, 23, 13, 23, 22, 0),
    "prime_floor_bounded_coordinate_square_strict": (3, 23, 27, 15, 27, 26, 0),
    "two_strict_values_sum_below_double": (3, 23, 103, 35, 95, 102, 8),
    "prime_floor_bounded_two_square_norm_below_double": (2, 30, 36, 19, 36, 35, 0),
    "floor_square_successor_grid_strictly_exceeds_input": (0, 5, 12, 8, 12, 11, 0),
    "floor_square_oversized_grid_exists": (2, 12, 14, 10, 14, 13, 0),
    "prime_floor_bounded_divisible_norm_represents_prime": (2, 27, 34, 22, 34, 33, 0),
    "finite_bounded_into_oversized_not_injective": (4, 88, 117, 33, 117, 116, 0),
    "floor_square_oversized_bounded_grid_not_injective": (2, 23, 29, 19, 29, 28, 0),
    "finite_bounded_into_collision_from_constructive_decision": (1, 18, 35, 22, 35, 34, 0),
}

EXPECTED_GRAPH_SHA256 = (
    "4c2306775e0da73eb56c56c25e0c1acbfdc5e38a4732db4232554d69a86a7e80"
)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_pigeonhole_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    available = dict(_specs_by_name())
    available.update(
        (item.name, item)
        for item in make_bertrand_floor_sqrt_total_candidate_theorems(TheoremSpec)
    )
    available.update(
        (item.name, item)
        for item in make_fermat_two_squares_candidate_theorems(TheoremSpec)
    )
    return available


def _available_specs() -> dict[str, TheoremSpec]:
    return _dependency_core() | {item.name: item for item in _candidate_specs()}


def _curried_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


@lru_cache(maxsize=None)
def _body_certificate(name: str):
    item = next(item for item in _candidate_specs() if item.name == name)
    target = _curried_target(item)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _walk_unique(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        for item in fields(current):
            child = getattr(current, item.name)
            if isinstance(child, Proof):
                pending.append(child)


def test_pigeonhole_factory_is_exact_deterministic_isolated_and_acyclic() -> None:
    first = _candidate_specs()
    assert first == make_fermat_two_squares_pigeonhole_candidate_theorems(TheoremSpec)
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    payload = "\x1c".join(
        "\x1f".join(
            (
                item.name,
                item.statement,
                "\x1e".join(item.dependencies),
                "\x1e".join(item.script),
            )
        )
        for item in first
    )
    assert sha256(payload.encode()).hexdigest() == EXPECTED_GRAPH_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    available = _dependency_core()
    for item in first:
        assert len(item.dependencies) == len(set(item.dependencies))
        assert all(dependency in available for dependency in item.dependencies)
        available[item.name] = item


def test_pigeonhole_contracts_are_closed_native_first_order_ha() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "Prime(",
                "FloorSqrt(",
                "BetaAt(",
                "BoundedInto(",
                "Injective(",
                "Dvd(",
                "Lt(",
                "%",
                "^",
                "∣",
                "≡",
            )
        )


def test_pigeonhole_scripts_stay_constructive_and_use_existing_bridges() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert "apply finite_bounded_injective_surjective" in commands
    assert "apply bounded_divisible_two_square_norm_equals_prime" in commands
    assert "exact floor_sqrt_total" in commands
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_pigeonhole_candidate_bodies_are_independently_kernel_checked() -> None:
    receipts = replay_candidate_bodies(_candidate_specs(), core=_dependency_core())
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
    assert max(receipt.proof_nodes for receipt in receipts) == 117
    assert max(receipt.proof_depth for receipt in receipts) == 35


def test_pigeonhole_certificates_are_dne_free_and_reject_false_targets() -> None:
    for item in _candidate_specs():
        certificate, target = _body_certificate(item.name)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))
        assert not check(
            (),
            certificate,
            _curried_target(item, f"({item.statement}) /\\ 0 = 1"),
        )


def test_every_pigeonhole_dependency_is_live_under_false_contract_mutation() -> None:
    available = _available_specs()
    for item in _candidate_specs():
        for dependency in item.dependencies:
            mutated = dict(available)
            mutated[dependency] = replace(available[dependency], statement="0 = 1")
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((item,), core=mutated)


@pytest.mark.parametrize("prime_value", (2, 3, 5, 7, 13, 17, 29, 37, 41, 53, 97))
def test_prime_floor_grid_and_norm_bounds_hold_on_numerical_examples(
    prime_value: int,
) -> None:
    root = isqrt(prime_value)
    assert root * root < prime_value < (root + 1) * (root + 1)
    assert all(
        first * first + second * second < 2 * prime_value
        for first in range(root + 1)
        for second in range(root + 1)
    )


@pytest.mark.parametrize("prime_value", (5, 13, 17, 29, 37, 41, 53, 61, 73, 89, 97))
def test_actual_two_square_witnesses_fit_the_checked_floor_grid(
    prime_value: int,
) -> None:
    root = isqrt(prime_value)
    witnesses = tuple(
        (first, second)
        for first in range(root + 1)
        for second in range(root + 1)
        if first * first + second * second == prime_value
    )
    assert witnesses
    for first, second in witnesses:
        norm = first * first + second * second
        assert 0 < norm < 2 * prime_value
        assert norm % prime_value == 0


@pytest.mark.parametrize("modulus", range(1, 20))
def test_oversized_bounded_residue_maps_have_explicit_host_collisions(
    modulus: int,
) -> None:
    root = isqrt(modulus)
    length = (root + 1) * (root + 1)
    values = tuple(index % modulus for index in range(length))
    assert length > modulus
    assert all(value < modulus for value in values)
    assert len(set(values)) < len(values)
