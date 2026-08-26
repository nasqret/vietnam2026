"""Independent constructive audit for the exact Lagrange prime reduction."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from math import isqrt
from pathlib import Path

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Forall, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v12
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_two_squares_classification_candidate import (
    make_fermat_two_squares_classification_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_factor_fold_candidate import (
    make_fermat_two_squares_factor_fold_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_pairing_candidate import (
    make_fermat_two_squares_pairing_candidate_theorems,
)
from peano_lab.library.four_square_euler_candidate import (
    make_four_square_euler_candidate_theorems,
)
from peano_lab.library.four_square_identity_candidate import (
    make_four_square_identity_candidate_theorems,
)
from peano_lab.library.four_square_lagrange_candidate import (
    FOUR_SQUARE_ELEVEN_REPRESENTED,
    FOUR_SQUARE_LAGRANGE_BOUNDED_FROM_PRIMES,
    FOUR_SQUARE_LAGRANGE_FROM_ALL_PRIMES,
    FOUR_SQUARE_LAGRANGE_FROM_THREE_MOD_FOUR_PRIMES,
    FOUR_SQUARE_LAGRANGE_IFF_THREE_MOD_FOUR_PRIMES,
    FOUR_SQUARE_ONE_REPRESENTED,
    FOUR_SQUARE_PRIME_CASE_REDUCTION,
    FOUR_SQUARE_PRIME_MODULAR_SEED_MULTIPLE,
    FOUR_SQUARE_PRIME_TWO_OR_ONE_MOD_FOUR,
    FOUR_SQUARE_PRIME_UNIT_SEED_REPRESENTED,
    FOUR_SQUARE_SEVEN_REPRESENTED,
    FOUR_SQUARE_THREE_REPRESENTED,
    FOUR_SQUARE_TWO_REPRESENTED,
    FOUR_SQUARE_TWO_SQUARE_EMBEDDING,
    FOUR_SQUARE_ZERO_REPRESENTED,
    four_square_representation,
    make_four_square_lagrange_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    FOUR_SQUARE_ZERO_REPRESENTED,
    FOUR_SQUARE_ONE_REPRESENTED,
    FOUR_SQUARE_TWO_REPRESENTED,
    FOUR_SQUARE_THREE_REPRESENTED,
    FOUR_SQUARE_SEVEN_REPRESENTED,
    FOUR_SQUARE_ELEVEN_REPRESENTED,
    FOUR_SQUARE_TWO_SQUARE_EMBEDDING,
    FOUR_SQUARE_PRIME_TWO_OR_ONE_MOD_FOUR,
    FOUR_SQUARE_PRIME_MODULAR_SEED_MULTIPLE,
    FOUR_SQUARE_PRIME_UNIT_SEED_REPRESENTED,
    FOUR_SQUARE_PRIME_CASE_REDUCTION,
    FOUR_SQUARE_LAGRANGE_BOUNDED_FROM_PRIMES,
    FOUR_SQUARE_LAGRANGE_FROM_ALL_PRIMES,
    FOUR_SQUARE_LAGRANGE_FROM_THREE_MOD_FOUR_PRIMES,
    FOUR_SQUARE_LAGRANGE_IFF_THREE_MOD_FOUR_PRIMES,
)

PINNED_ENDPOINTS = {
    FOUR_SQUARE_LAGRANGE_BOUNDED_FROM_PRIMES:
        "efd0f14a1f72b0fc99e177cf2d85119277ef11f5d7e3ba787a05b68aba4bd049",
    FOUR_SQUARE_LAGRANGE_FROM_ALL_PRIMES:
        "d373edd2a0775d7a1c37579e03decd1b958bc1c0337d17e255c752552c1a9a31",
    FOUR_SQUARE_LAGRANGE_FROM_THREE_MOD_FOUR_PRIMES:
        "3fd036aef0aeaeee2a01875484a2071f47c484538e3e37907398b410e6222d47",
    FOUR_SQUARE_LAGRANGE_IFF_THREE_MOD_FOUR_PRIMES:
        "67c703fb011e9abe5c79cb74d1eef56d754da9f9313053675e8f783f79dc238c",
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_lagrange_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _base_core() -> dict[str, TheoremSpec]:
    result = {row.name: row for row in editions_v12.ALPHA_SPECS}
    factories = (
        make_fermat_two_squares_classification_candidate_theorems,
        make_fermat_two_squares_factor_fold_candidate_theorems,
        make_fermat_two_squares_pairing_candidate_theorems,
        make_four_square_identity_candidate_theorems,
        make_four_square_euler_candidate_theorems,
    )
    for factory in factories:
        result.update({row.name: row for row in factory(TheoremSpec)})
    return result


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _base_core() | {row.name: row for row in _rows()[:index]}


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _body(name: str) -> tuple[Proof, object]:
    row = next(item for item in _rows() if item.name == name)
    core = _row_core(name)
    target = _closed_formula(row.statement)
    for dependency in reversed(row.dependencies):
        target = Imp(_closed_formula(core[dependency].statement), target)
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
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(
            child
            for field in fields(node)
            if isinstance((child := getattr(node, field.name)), Proof)
        )


def test_lagrange_candidates_are_deterministic_closed_and_isolated() -> None:
    rows = _rows()
    assert rows == make_four_square_lagrange_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == EXPECTED_NAMES

    alpha = {row.name for row in editions_v12.ALPHA_SPECS}
    stable = _specs_by_name()
    seen: set[str] = set()
    for row in rows:
        assert row.name not in alpha
        assert row.name not in stable
        assert set(row.dependencies) <= set(_base_core()) | seen
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            forbidden not in row.statement
            for forbidden in ("FourSquare(", "Prime(", " - ", "^", "abs(")
        )
        assert all(
            not command.startswith(("ring", "omega", "auto"))
            for command in row.script
        )
        seen.add(row.name)

    assert {
        row.name: sha256(row.statement.encode("utf-8")).hexdigest()
        for row in rows
        if row.name in PINNED_ENDPOINTS
    } == PINNED_ENDPOINTS


def test_lagrange_candidate_bodies_are_independently_checked_and_bounded() -> None:
    receipts = replay_candidate_bodies(_rows(), core=_base_core())
    assert len(receipts) == len(EXPECTED_NAMES)
    assert max(receipt.proof_nodes for receipt in receipts) <= 180
    assert max(receipt.proof_depth for receipt in receipts) <= 45


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_lagrange_bodies_are_constructive_and_reject_false_targets(name: str) -> None:
    proof, target = _body(name)
    assert check((), proof, target)
    assert all(type(node) is not DNE for node in _walk(proof))
    row = next(item for item in _rows() if item.name == name)
    corrupted = replace(row, statement=f"({row.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=_row_core(name))


def test_universal_lagrange_is_explicitly_conditional_on_the_missing_prime_family() -> None:
    from_all = next(
        row for row in _rows() if row.name == FOUR_SQUARE_LAGRANGE_FROM_ALL_PRIMES
    )
    from_three = next(
        row
        for row in _rows()
        if row.name == FOUR_SQUARE_LAGRANGE_FROM_THREE_MOD_FOUR_PRIMES
    )
    equivalence = next(
        row
        for row in _rows()
        if row.name == FOUR_SQUARE_LAGRANGE_IFF_THREE_MOD_FOUR_PRIMES
    )

    assert type(_closed_formula(from_all.statement)) is Imp
    assert type(_closed_formula(from_three.statement)) is Imp
    assert type(_closed_formula(from_three.statement).right) is Forall
    assert type(_closed_formula(equivalence.statement)) is And
    assert "4 * fsl_three_residue_universal + 3" in from_three.statement
    assert not any(
        type(_closed_formula(row.statement)) is Forall
        and row.statement.startswith("forall n.")
        and " -> " not in row.statement
        for row in _rows()
    )


@pytest.mark.parametrize("value", tuple(range(48)))
def test_small_naturals_have_computable_four_square_witnesses(value: int) -> None:
    limit = isqrt(value)
    witness = next(
        (
            (first, second, third, fourth)
            for first in range(limit + 1)
            for second in range(limit + 1)
            for third in range(limit + 1)
            for fourth in range(limit + 1)
            if value
            == first * first + second * second + third * third + fourth * fourth
        ),
        None,
    )
    assert witness is not None


def test_representation_surface_rejects_bad_tags_and_expands_four_witnesses() -> None:
    with pytest.raises(ValueError):
        four_square_representation("n", tag="bad-tag")
    surface = four_square_representation("n", tag="audit")
    assert surface.startswith("exists fsl_a_audit fsl_b_audit")
    assert "fsl_d_audit * fsl_d_audit" in surface


def test_lagrange_rfc_identifies_the_exact_remaining_prime_gap() -> None:
    repository = Path(__file__).resolve().parents[3]
    text = (
        repository / "research/arithmetic-library/four-square-lagrange-rfc-v1.md"
    ).read_text(encoding="utf-8")
    assert "four_square_lagrange_iff_three_mod_four_primes" in text
    assert "not an unconditional proof of universal Lagrange" in text
    assert "No Alpha or Stable admission" in text
