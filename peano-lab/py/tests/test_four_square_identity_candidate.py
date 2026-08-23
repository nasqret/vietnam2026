"""Bounded, evidence-honest audit of constructive four-square foundations."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import editions_v12, theorems as theorem_registry
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_two_squares_classification_candidate import (
    make_fermat_two_squares_classification_candidate_theorems,
)
from peano_lab.library.four_square_identity_candidate import (
    FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL,
    FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE,
    FOUR_SQUARE_ADDITIVE_GAP_REORDER,
    FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL,
    FOUR_SQUARE_GAP_BALANCE_LEFT,
    FOUR_SQUARE_GAP_BALANCE_RIGHT,
    FOUR_SQUARE_NORM_DISTRIBUTES,
    FOUR_SQUARE_PRODUCT_SHUFFLE,
    FOUR_SQUARE_PRODUCT_SQUARE,
    FOUR_SQUARE_SUM_EXPANSION,
    FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY,
    FOUR_SQUARE_TWO_SQUARE_FACTOR_TOTAL,
    QUATERNION_COORDINATE_ABSOLUTE_TOTAL,
    QUATERNION_COORDINATE_BALANCE_TOTAL,
    QUATERNION_COORDINATE_SQUARE_BALANCE_TOTAL,
    QUATERNION_COORDINATE_SQUARE_TRANSPORT,
    SIGNED_BALANCE_ABSOLUTE_EXISTS,
    SIGNED_BALANCE_SQUARE_TRANSPORT,
    SIGNED_SQUARE_CROSS_TERM_ZERO,
    SIGNED_SQUARE_MAGNITUDE_EXPANDS,
    make_four_square_identity_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    SIGNED_SQUARE_CROSS_TERM_ZERO,
    SIGNED_SQUARE_MAGNITUDE_EXPANDS,
    SIGNED_BALANCE_ABSOLUTE_EXISTS,
    FOUR_SQUARE_NORM_DISTRIBUTES,
    QUATERNION_COORDINATE_BALANCE_TOTAL,
    QUATERNION_COORDINATE_ABSOLUTE_TOTAL,
    FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL,
    FOUR_SQUARE_ADDITIVE_GAP_REORDER,
    FOUR_SQUARE_SUM_EXPANSION,
    FOUR_SQUARE_GAP_BALANCE_RIGHT,
    FOUR_SQUARE_GAP_BALANCE_LEFT,
    FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE,
    SIGNED_BALANCE_SQUARE_TRANSPORT,
    FOUR_SQUARE_PRODUCT_SHUFFLE,
    FOUR_SQUARE_PRODUCT_SQUARE,
    QUATERNION_COORDINATE_SQUARE_TRANSPORT,
    QUATERNION_COORDINATE_SQUARE_BALANCE_TOTAL,
    FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL,
    FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY,
    FOUR_SQUARE_TWO_SQUARE_FACTOR_TOTAL,
)

EXPECTED_DEPENDENCIES = {
    SIGNED_SQUARE_CROSS_TERM_ZERO: ("signed_decode_normal", "mul_zero_left"),
    SIGNED_SQUARE_MAGNITUDE_EXPANDS: (
        "signed_decode_normal",
        "mul_zero_left",
        "zero_add",
    ),
    SIGNED_BALANCE_ABSOLUTE_EXISTS: ("signed_decode_normal",),
    FOUR_SQUARE_NORM_DISTRIBUTES: ("add_mul",),
    QUATERNION_COORDINATE_BALANCE_TOTAL: ("signed_balance_total",),
    QUATERNION_COORDINATE_ABSOLUTE_TOTAL: (
        QUATERNION_COORDINATE_BALANCE_TOTAL,
        SIGNED_BALANCE_ABSOLUTE_EXISTS,
    ),
    FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL: ("add_assoc", "add_comm"),
    FOUR_SQUARE_ADDITIVE_GAP_REORDER: (
        "add_shuffle_middle",
        "add_assoc",
        "add_comm",
        FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL,
    ),
    FOUR_SQUARE_SUM_EXPANSION: ("add_mul", "mul_add"),
    FOUR_SQUARE_GAP_BALANCE_RIGHT: (
        FOUR_SQUARE_SUM_EXPANSION,
        "add_mul",
        "mul_add",
        FOUR_SQUARE_ADDITIVE_GAP_REORDER,
    ),
    FOUR_SQUARE_GAP_BALANCE_LEFT: (
        FOUR_SQUARE_GAP_BALANCE_RIGHT,
        "add_comm",
    ),
    FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE: (
        FOUR_SQUARE_GAP_BALANCE_RIGHT,
        FOUR_SQUARE_GAP_BALANCE_LEFT,
    ),
    SIGNED_BALANCE_SQUARE_TRANSPORT: (
        SIGNED_BALANCE_ABSOLUTE_EXISTS,
        FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE,
    ),
    FOUR_SQUARE_PRODUCT_SHUFFLE: ("mul_assoc", "mul_comm"),
    FOUR_SQUARE_PRODUCT_SQUARE: (FOUR_SQUARE_PRODUCT_SHUFFLE,),
    QUATERNION_COORDINATE_SQUARE_TRANSPORT: (
        FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE,
    ),
    QUATERNION_COORDINATE_SQUARE_BALANCE_TOTAL: (
        QUATERNION_COORDINATE_ABSOLUTE_TOTAL,
        QUATERNION_COORDINATE_SQUARE_TRANSPORT,
    ),
    FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL: (
        "signed_balance_total",
        SIGNED_BALANCE_ABSOLUTE_EXISTS,
    ),
    FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY: (
        "add_assoc",
        "add_mul",
        "brahmagupta_fibonacci_two_square_identity",
    ),
    FOUR_SQUARE_TWO_SQUARE_FACTOR_TOTAL: (
        FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL,
        FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY,
        "add_assoc",
    ),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_four_square_identity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _alpha_core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in editions_v12.ALPHA_SPECS}


@lru_cache(maxsize=1)
def _external_candidate_core() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in make_fermat_two_squares_classification_candidate_theorems(
            TheoremSpec
        )
        if item.name == "brahmagupta_fibonacci_two_square_identity"
    }


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return (
        _alpha_core()
        | _external_candidate_core()
        | {item.name: item for item in _rows()[:index]}
    )


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _body(name: str):
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


def test_four_square_candidates_are_exact_isolated_and_dependency_ordered() -> None:
    rows = _rows()
    assert rows == make_four_square_identity_candidate_theorems(TheoremSpec)
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    assert {row.name: row.dependencies for row in rows} == EXPECTED_DEPENDENCIES

    stable = _specs_by_name()
    alpha = _alpha_core()
    external = _external_candidate_core()
    assert tuple(external) == ("brahmagupta_fibonacci_two_square_identity",)
    assert all(name not in stable and name not in alpha for name in external)
    seen: set[str] = set()
    for row in rows:
        assert row.name not in stable
        assert row.name not in alpha
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert all(
            name in alpha or name in external or name in seen
            for name in row.dependencies
        )
        seen.add(row.name)

    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "four_square_identity_candidate" not in registry_source


def test_four_square_contracts_expand_to_closed_native_ha() -> None:
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            token not in row.statement
            for token in (
                "SignedDecode(",
                "SignedBalance(",
                "FourSquare(",
                "Quaternion(",
                "abs(",
                "^",
                " - ",
            )
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_four_square_bodies_are_kernel_checked_and_constructive(name: str) -> None:
    proof, target = _body(name)
    nodes, depth = proof_metrics(proof)
    objects, edges, reused = proof_identity_metrics(proof)

    assert check((), proof, target)
    assert nodes <= 350
    assert depth <= 75
    assert objects <= nodes
    assert edges >= objects - 1
    assert reused >= 0
    assert not any(type(node) is DNE for node in _walk(proof))


def test_four_square_scripts_do_not_invoke_hidden_automation_or_classical_logic() -> None:
    commands = tuple(command for row in _rows() for command in row.script)
    assert "apply signed_decode_normal" in commands
    assert "exact signed_balance_total" in commands
    assert "apply signed_balance_absolute_exists" in commands
    assert all(not command.startswith(("auto", "ring", "use ")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


@pytest.mark.parametrize(
    ("name", "dependency"),
    (
        (SIGNED_SQUARE_CROSS_TERM_ZERO, "signed_decode_normal"),
        (FOUR_SQUARE_NORM_DISTRIBUTES, "add_mul"),
        (QUATERNION_COORDINATE_BALANCE_TOTAL, "signed_balance_total"),
        (
            QUATERNION_COORDINATE_ABSOLUTE_TOTAL,
            SIGNED_BALANCE_ABSOLUTE_EXISTS,
        ),
        (FOUR_SQUARE_GAP_BALANCE_RIGHT, FOUR_SQUARE_ADDITIVE_GAP_REORDER),
        (SIGNED_BALANCE_SQUARE_TRANSPORT, FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE),
        (FOUR_SQUARE_PRODUCT_SQUARE, FOUR_SQUARE_PRODUCT_SHUFFLE),
        (
            QUATERNION_COORDINATE_SQUARE_BALANCE_TOTAL,
            QUATERNION_COORDINATE_SQUARE_TRANSPORT,
        ),
        (
            FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY,
            "brahmagupta_fibonacci_two_square_identity",
        ),
        (
            FOUR_SQUARE_TWO_SQUARE_FACTOR_TOTAL,
            FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY,
        ),
    ),
)
def test_essential_four_square_dependencies_are_live(name: str, dependency: str) -> None:
    row = next(item for item in _rows() if item.name == name)
    mutated = replace(
        row,
        dependencies=tuple(item for item in row.dependencies if item != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def test_hamilton_coordinate_formulas_and_balanced_norm_are_numerically_exact() -> None:
    cases = 0
    for a, b, c, d, e, f, g, h in product(range(3), repeat=8):
        contributions = (
            (a * e, b * f + c * g + d * h),
            (a * f + b * e + c * h, d * g),
            (a * g + c * e + d * f, b * h),
            (a * h + b * g + d * e, c * f),
        )
        norm = (a * a + b * b + c * c + d * d) * (
            e * e + f * f + g * g + h * h
        )
        magnitudes = tuple(abs(positive - negative) for positive, negative in contributions)
        correction = sum(positive * negative for positive, negative in contributions)
        balanced_squares = sum(
            positive * positive + negative * negative
            for positive, negative in contributions
        )

        assert norm == sum(value * value for value in magnitudes)
        assert norm + 2 * correction == balanced_squares
        for (positive, negative), magnitude in zip(contributions, magnitudes):
            assert positive * positive + negative * negative == (
                magnitude * magnitude
                + positive * negative
                + negative * positive
            )
        cases += 1

    assert cases == 6_561


def test_signed_balance_oracles_cover_both_signs_and_the_zero_boundary() -> None:
    observed = set()
    for positive, negative in product(range(12), repeat=2):
        signed = positive - negative
        pos = max(signed, 0)
        neg = max(-signed, 0)
        magnitude = pos + neg

        assert positive + neg == negative + pos
        assert pos * neg == 0
        assert magnitude * magnitude == pos * pos + neg * neg
        assert positive == negative + magnitude or negative == positive + magnitude
        assert positive * positive + negative * negative == (
            magnitude * magnitude
            + positive * negative
            + negative * positive
        )
        observed.add((signed > 0) - (signed < 0))

    assert observed == {-1, 0, 1}


def test_two_square_factor_identity_has_explicit_four_coordinate_witnesses() -> None:
    cases = 0
    for a, b, c, d, e, f in product(range(4), repeat=6):
        coordinates = (
            a * e + b * f,
            abs(a * f - b * e),
            c * e + d * f,
            abs(c * f - d * e),
        )
        assert (a * a + b * b + c * c + d * d) * (e * e + f * f) == sum(
            value * value for value in coordinates
        )
        cases += 1

    assert cases == 4_096


def test_four_square_rfc_honestly_documents_the_exact_remaining_gap() -> None:
    repository = Path(__file__).resolve().parents[3]
    rfc = (
        repository
        / "research"
        / "arithmetic-library"
        / "four-square-identity-foundations-rfc-v1.md"
    ).read_text(encoding="utf-8")

    for name in EXPECTED_NAMES:
        assert f"`{name}`" in rfc
    assert "not Alpha admission, a closed Euler identity" in rfc
    assert "bounded\nfour-square multiple" in rfc
    assert "None of those results\nis claimed" in rfc
