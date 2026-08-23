"""Bounded independent audit of constructive two-square multiplication."""

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
from peano_lab.library.fermat_two_squares_brahmagupta_candidate import (
    make_fermat_two_squares_brahmagupta_candidate_theorems,
)
from peano_lab.library.fermat_two_squares_collision_norm_candidate import (
    make_fermat_two_squares_collision_norm_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "two_square_add_left_comm",
    "two_square_mul_left_comm",
    "two_square_cross_products_equal",
    "two_square_product_norm_expanded",
    "two_square_balanced_difference_identity",
    "two_square_product_difference_forward",
    "two_square_product_difference_reverse",
    "two_square_product_explicit_witness",
    "two_square_product_is_two_square",
    "two_square_representations_closed_under_multiplication",
)

EXPECTED_STATEMENT_SHA256 = {
    "two_square_add_left_comm": "59eb4b0f1e4e6aba511d9a3cacc39d5369da8152e95b981012d32954c1502057",
    "two_square_mul_left_comm": "002d5157f026903a2607512293c27526a8be5245d0771bd79421d377b8dce828",
    "two_square_cross_products_equal": "fd0d611918933d28ce186ebe8c30ece9699bc7dc4a160baacea0e2e45beca71c",
    "two_square_product_norm_expanded": "3f62498f3a7f84bf810993bf2355a6fd2b2fe4efe7e0625719b253ed1ff9ce7c",
    "two_square_balanced_difference_identity": "948eb36fd48379d7b455baafdb0b419a97cd1ee43bbe6dad2395e4215bc15fc0",
    "two_square_product_difference_forward": "3b40ce660ef646dc3f5fc8f099bdf4e5ec9b4b3247c4ebad25f86f35bd143e59",
    "two_square_product_difference_reverse": "b41039228603d3701777487e5dbf5a707e7e0c95476dbc9b3597e77b9506ea6e",
    "two_square_product_explicit_witness": "12a23694d26f522fe35b17ef127ef076e2de185aaba51434f8c5d2b08e8fa275",
    "two_square_product_is_two_square": "8b7fd8a5d8d1b98f92057c6b119dff0d3ae93f41fbb3a740a5c173a90a899a0d",
    "two_square_representations_closed_under_multiplication": "d61118c9dc3c758b428cb70af7d9e920b082f28467776463c20363f0633b468e",
}

# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_BODY_RECEIPTS = {
    "two_square_add_left_comm": (2, 11, 21, 11, 21, 20, 0),
    "two_square_mul_left_comm": (2, 11, 21, 11, 21, 20, 0),
    "two_square_cross_products_equal": (3, 5, 72, 23, 64, 71, 8),
    "two_square_product_norm_expanded": (8, 5, 303, 67, 261, 302, 42),
    "two_square_balanced_difference_identity": (6, 17, 338, 71, 338, 337, 0),
    "two_square_product_difference_forward": (3, 23, 69, 39, 69, 68, 0),
    "two_square_product_difference_reverse": (5, 30, 41, 21, 41, 40, 0),
    "two_square_product_explicit_witness": (3, 25, 68, 27, 68, 67, 0),
    "two_square_product_is_two_square": (1, 13, 34, 21, 34, 33, 0),
    "two_square_representations_closed_under_multiplication": (
        1,
        15,
        36,
        20,
        36,
        35,
        0,
    ),
}


@lru_cache(maxsize=1)
def _rows() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_brahmagupta_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    result = dict(_specs_by_name())
    result.update(
        (item.name, item)
        for item in make_fermat_two_squares_collision_norm_candidate_theorems(
            TheoremSpec
        )
    )
    return result


def _available() -> dict[str, TheoremSpec]:
    return _core() | {item.name: item for item in _rows()}


def _target(item: TheoremSpec, statement: str | None = None):
    available = _available()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


@lru_cache(maxsize=len(EXPECTED_NAMES))
def _certificate(name: str):
    item = next(row for row in _rows() if row.name == name)
    target = _target(item)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _proof_nodes(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        yield current
        for field in fields(current):
            child = getattr(current, field.name)
            if isinstance(child, Proof):
                pending.append(child)


def test_brahmagupta_factory_is_exact_deterministic_and_registry_isolated() -> None:
    rows = _rows()
    assert rows == make_fermat_two_squares_brahmagupta_candidate_theorems(
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

    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "fermat_two_squares_brahmagupta_candidate" not in registry_source
    assert len(editions_v12.ALPHA_CHECKED_SPECS) == 570


def test_brahmagupta_statements_expand_to_closed_first_order_ha() -> None:
    for row in _rows():
        formula, free = parse_formula_with_names(row.statement)
        assert not free
        assert formula == _closed_formula(row.statement)
        assert all(
            forbidden not in row.statement
            for forbidden in ("Signed(", "abs(", "TwoSquare(", " - ", "^")
        )

    witness = next(row for row in _rows() if row.name == "two_square_product_explicit_witness")
    assert "exists m." in witness.statement
    assert "a * d = b * c + m" in witness.statement
    assert "b * c = a * d + m" in witness.statement


def test_brahmagupta_bodies_are_independently_checked_and_bounded() -> None:
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
    assert max(receipt.proof_nodes for receipt in receipts) == 338
    assert max(receipt.proof_depth for receipt in receipts) == 71


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_brahmagupta_certificates_are_constructive_and_reject_false_targets(
    name: str,
) -> None:
    row = next(item for item in _rows() if item.name == name)
    certificate, target = _certificate(name)
    assert check((), certificate, target)
    assert not any(type(item) is DNE for item in _proof_nodes(certificate))
    assert not check(
        (),
        certificate,
        _target(row, f"({row.statement}) /\\ 0 = 1"),
    )


@pytest.mark.parametrize(
    ("name", "dependency"),
    (
        ("two_square_add_left_comm", "add_assoc"),
        ("two_square_cross_products_equal", "two_square_mul_left_comm"),
        ("two_square_product_norm_expanded", "mul_add"),
        (
            "two_square_balanced_difference_identity",
            "two_square_add_left_comm",
        ),
        (
            "two_square_product_difference_forward",
            "two_square_cross_products_equal",
        ),
        (
            "two_square_product_explicit_witness",
            "natural_absolute_difference_exists",
        ),
        (
            "two_square_representations_closed_under_multiplication",
            "two_square_product_is_two_square",
        ),
    ),
)
def test_brahmagupta_named_dependencies_are_live(name: str, dependency: str) -> None:
    item = next(row for row in _rows() if row.name == name)
    mutated = replace(
        item,
        dependencies=tuple(name for name in item.dependencies if name != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_available())


def test_brahmagupta_scripts_never_invoke_classical_logic_or_ring_automation() -> None:
    commands = tuple(command for row in _rows() for command in row.script)
    assert "exact natural_absolute_difference_exists_witness" in commands
    assert "apply two_square_balanced_difference_identity" in commands
    assert all(not command.startswith(("ring", "auto", "omega")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_brahmagupta_explicit_witness_handles_both_signs_and_zero() -> None:
    observed_signs: set[int] = set()
    count = 0
    for first, second, third, fourth in product(range(9), repeat=4):
        signed_difference = first * fourth - second * third
        magnitude = abs(signed_difference)
        coordinate = first * third + second * fourth
        source = (first * first + second * second) * (
            third * third + fourth * fourth
        )
        assert source == coordinate * coordinate + magnitude * magnitude
        assert (
            first * fourth == second * third + magnitude
            or second * third == first * fourth + magnitude
        )
        observed_signs.add((signed_difference > 0) - (signed_difference < 0))
        count += 1

    assert count == 6_561
    assert observed_signs == {-1, 0, 1}


@pytest.mark.parametrize(
    ("first", "second"),
    (
        (5, 13),
        (5, 17),
        (13, 29),
        (17, 37),
        (25, 65),
        (0, 89),
        (1, 73),
    ),
)
def test_represented_integers_have_constructive_product_examples(
    first: int,
    second: int,
) -> None:
    first_pairs = [
        (left, right)
        for left in range(first + 1)
        for right in range(first + 1)
        if first == left * left + right * right
    ]
    second_pairs = [
        (left, right)
        for left in range(second + 1)
        for right in range(second + 1)
        if second == left * left + right * right
    ]
    assert first_pairs and second_pairs
    a, b = first_pairs[0]
    c, d = second_pairs[0]
    x = a * c + b * d
    y = abs(a * d - b * c)
    assert first * second == x * x + y * y


def test_brahmagupta_rfc_preserves_the_candidate_evidence_boundary() -> None:
    repository = Path(__file__).resolve().parents[3]
    document = (
        repository
        / "research"
        / "arithmetic-library"
        / "fermat-two-squares-brahmagupta-rfc-v1.md"
    ).read_text(encoding="utf-8")
    assert "two_square_representations_closed_under_multiplication" in document
    assert "not enrolled in Alpha" in document
    assert "not a complete all-integer classification" in document
