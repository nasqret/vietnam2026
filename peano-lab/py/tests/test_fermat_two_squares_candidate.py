"""Bounded constructive audit of Fermat two-square foundational candidates."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_two_squares_candidate import (
    make_fermat_two_squares_candidate_theorems,
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
    "even_square_is_four_multiple",
    "odd_square_is_four_multiple_plus_one",
    "square_mod_four_zero_or_one",
    "sum_two_squares_mod_four_cases",
    "sum_two_squares_not_four_mod_three",
    "prime_mod_four_one_minus_one_square_exists",
    "prime_mod_four_one_bounded_minus_one_square_exists",
    "predecessor_square_congruence_yields_divisible_norm",
    "prime_mod_four_one_divisible_two_square_norm_exists",
    "prime_mod_four_one_bounded_divisible_two_square_norm_exists",
    "positive_multiple_below_twice_equals_base",
    "bounded_divisible_two_square_norm_equals_prime",
)

EXPECTED_DEPENDENCIES = {
    "even_square_is_four_multiple": ("mul_assoc", "mul_comm"),
    "odd_square_is_four_multiple_plus_one": (
        "mul_add",
        "add_mul",
        "mul_assoc",
        "mul_comm",
        "add_assoc",
        "add_comm",
        "zero_add",
        "mul_succ_left",
        "one_mul",
        "mul_zero_left",
        "mul_double_right",
        "four_mul_eq_double_double",
    ),
    "square_mod_four_zero_or_one": (
        "parity_cases",
        "even_square_is_four_multiple",
        "odd_square_is_four_multiple_plus_one",
    ),
    "sum_two_squares_mod_four_cases": (
        "square_mod_four_zero_or_one",
        "mul_add",
        "add_assoc",
        "add_comm",
    ),
    "sum_two_squares_not_four_mod_three": (
        "sum_two_squares_mod_four_cases",
        "division_remainder_unique",
    ),
    "prime_mod_four_one_minus_one_square_exists": (
        "mod4_one_is_odd",
        "quadratic_supplement_minus_one_residue_iff_mod_four_one",
    ),
    "prime_mod_four_one_bounded_minus_one_square_exists": (
        "prime_mod_four_one_minus_one_square_exists",
        "quadratic_residue_bounded_equiv",
    ),
    "predecessor_square_congruence_yields_divisible_norm": (
        "mod_eq_to_remainder_decomposition",
        "add_assoc",
        "add_comm",
        "zero_add",
        "mul_comm",
    ),
    "prime_mod_four_one_divisible_two_square_norm_exists": (
        "prime_mod_four_one_minus_one_square_exists",
        "predecessor_square_congruence_yields_divisible_norm",
    ),
    "prime_mod_four_one_bounded_divisible_two_square_norm_exists": (
        "prime_mod_four_one_bounded_minus_one_square_exists",
        "predecessor_square_congruence_yields_divisible_norm",
    ),
    "positive_multiple_below_twice_equals_base": (
        "zero_or_succ",
        "lt_not_le",
        "add_assoc",
        "add_comm",
        "zero_add",
    ),
    "bounded_divisible_two_square_norm_equals_prime": (
        "positive_multiple_below_twice_equals_base",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "even_square_is_four_multiple": (
        "8da0ba14e2f130007f946b0227daadd390946a7b6b38c1388853da386edbc20c"
    ),
    "odd_square_is_four_multiple_plus_one": (
        "39dad3bca1934b3e248453ad6815494963432471dcf30190917427440dd98142"
    ),
    "square_mod_four_zero_or_one": (
        "6c280c4d460aa5c0070a70a834cd5eb9691b1041876f518e5ab4b66e2414f45d"
    ),
    "sum_two_squares_mod_four_cases": (
        "a51d9619fa209e629a94e952305dd878667a4bfe5e64f279ad22c87723969aa1"
    ),
    "sum_two_squares_not_four_mod_three": (
        "b14f603bcd433eab5c6c1825ffa6f81778abe40d33d0e5c618fd02c0d7662222"
    ),
    "prime_mod_four_one_minus_one_square_exists": (
        "3e40de18079b36a4d0dc67de66e618afc4f7ea24f22dd5784bd87a3b6f09752a"
    ),
    "prime_mod_four_one_bounded_minus_one_square_exists": (
        "7078e696e6715beb27fd627eb3ea2cb77b919da24b8e8e85216d3d3d4e17583e"
    ),
    "predecessor_square_congruence_yields_divisible_norm": (
        "01123ffa627045c58f65f16dfdc7011838dce73ec9c5bf4557b990ecbed82387"
    ),
    "prime_mod_four_one_divisible_two_square_norm_exists": (
        "ea28433f776db3bfedaeabab09d2bded69cd86b440df534d7303107f999ea8e9"
    ),
    "prime_mod_four_one_bounded_divisible_two_square_norm_exists": (
        "6d839c60b5fa4a78fef0c13fc9ebe53aec0b022662984d9ed8c37e397807885c"
    ),
    "positive_multiple_below_twice_equals_base": (
        "38b6a9235ac1cfb0abd882c69475e4018990cecac368b716604cba154faf781c"
    ),
    "bounded_divisible_two_square_norm_equals_prime": (
        "19af39f5074273d8886a1795bcaebd9618909c5d654cbc55a752125572a1ea01"
    ),
}

# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_BODY_RECEIPTS = {
    "even_square_is_four_multiple": (2, 28, 106, 28, 106, 105, 0),
    "odd_square_is_four_multiple_plus_one": (12, 29, 232, 64, 205, 231, 27),
    "square_mod_four_zero_or_one": (3, 14, 36, 15, 36, 35, 0),
    "sum_two_squares_mod_four_cases": (4, 40, 218, 30, 196, 217, 22),
    "sum_two_squares_not_four_mod_three": (2, 74, 271, 27, 271, 270, 0),
    "prime_mod_four_one_minus_one_square_exists": (2, 19, 22, 15, 22, 21, 0),
    "prime_mod_four_one_bounded_minus_one_square_exists": (
        2,
        25,
        29,
        14,
        29,
        28,
        0,
    ),
    "predecessor_square_congruence_yields_divisible_norm": (
        5,
        64,
        124,
        31,
        121,
        123,
        3,
    ),
    "prime_mod_four_one_divisible_two_square_norm_exists": (
        2,
        20,
        26,
        15,
        26,
        25,
        0,
    ),
    "prime_mod_four_one_bounded_divisible_two_square_norm_exists": (
        2,
        27,
        33,
        15,
        33,
        32,
        0,
    ),
    "positive_multiple_below_twice_equals_base": (5, 43, 128, 31, 125, 127, 3),
    "bounded_divisible_two_square_norm_equals_prime": (1, 15, 17, 14, 17, 16, 0),
}

EXPECTED_GRAPH_SHA256 = (
    "dd2f4004c479d87f595cdba68bc6a08fbb368a64bc98bbec7934ad2ec68b6f3f"
)
BODY_DEADLINE_SECONDS = 20


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_fermat_two_squares_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    core.update(
        (item.name, item)
        for item in make_quadratic_supplement_minus_one_candidate_theorems(
            TheoremSpec
        )
    )
    return core


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


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Fermat two-square body replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_two_square_factory_is_exact_deterministic_isolated_and_acyclic() -> None:
    first = _candidate_specs()
    second = make_fermat_two_squares_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
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
        assert len(set(item.dependencies)) == len(item.dependencies)
        assert all(dependency in available for dependency in item.dependencies)
        available[item.name] = item
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "fermat_two_squares_candidate" not in registry_source


def test_two_square_contracts_are_closed_expanded_native_ha() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "Even(",
                "Odd(",
                "Dvd(",
                "Lt(",
                "ModEq(",
                "Prime(",
                "QRes(",
                "TwoSquares(",
                "%",
                "^",
                "∣",
                "≡",
                "↔",
            )
        )

    by_name = {item.name: item for item in _candidate_specs()}
    root = by_name["prime_mod_four_one_minus_one_square_exists"]
    bounded_root = by_name["prime_mod_four_one_bounded_minus_one_square_exists"]
    norm = by_name["prime_mod_four_one_divisible_two_square_norm_exists"]
    bounded_norm = by_name[
        "prime_mod_four_one_bounded_divisible_two_square_norm_exists"
    ]
    closing = by_name["bounded_divisible_two_square_norm_equals_prime"]
    obstruction = by_name["sum_two_squares_not_four_mod_three"]

    assert root.statement.startswith("forall p n. p = S n ->")
    assert "p = 4 * fts_four_prime_one + 1" in root.statement
    assert "qr_x_fts_predecessor * qr_x_fts_predecessor" in root.statement
    assert (
        "qr_h_fts_bounded_predecessor + S qr_x_fts_bounded_predecessor = p"
        in bounded_root.statement
    )
    assert "exists r k. r * r + 1 = p * k" in norm.statement
    assert "fts_gap_canonical_root + S (r) = p" in bounded_norm.statement
    assert "p = a * a + b * b" in closing.statement
    assert "a * a + b * b = 4 * fts_four_sum_three + 3" in obstruction.statement


def test_two_square_scripts_are_constructive_and_consume_first_supplement() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)

    assert (
        "apply quadratic_supplement_minus_one_residue_iff_mod_four_one"
        in commands
    )
    assert "apply mod_eq_to_remainder_decomposition" in commands
    assert "apply quadratic_residue_bounded_equiv" in commands
    assert "apply division_remainder_unique" in commands
    assert "apply positive_multiple_below_twice_equals_base" in commands
    assert all(not command.startswith(("auto", "ring", "use ")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_two_square_bodies_kernel_check_within_hard_laptop_limit() -> None:
    with _body_deadline(BODY_DEADLINE_SECONDS):
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
    assert max(receipt.proof_nodes for receipt in receipts) == 271
    assert max(receipt.proof_depth for receipt in receipts) == 64


def test_two_square_certificates_are_dne_free_and_reject_false_targets() -> None:
    for item in _candidate_specs():
        certificate, target = _body_certificate(item.name)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))
        false_statement = f"({item.statement}) /\\ 0 = 1"
        assert not check((), certificate, _curried_target(item, false_statement))

    mutations = (
        (
            "odd_square_is_four_multiple_plus_one",
            "z * z = 4 * q + 1",
            "z * z = 4 * q + 3",
        ),
        (
            "sum_two_squares_not_four_mod_three",
            "+ 3",
            "+ 2",
        ),
        (
            "prime_mod_four_one_divisible_two_square_norm_exists",
            "r * r + 1 = p * k",
            "r * r + 2 = p * k",
        ),
        (
            "bounded_divisible_two_square_norm_equals_prime",
            "= p + p",
            "= p + p + p",
        ),
    )
    for name, correct, false in mutations:
        item = next(item for item in _candidate_specs() if item.name == name)
        assert item.statement.count(correct) == 1
        certificate, _target = _body_certificate(name)
        false_statement = item.statement.replace(correct, false)
        assert not check((), certificate, _curried_target(item, false_statement))


def test_every_two_square_dependency_is_live_under_false_contract_mutation() -> None:
    available = _available_specs()
    with _body_deadline(BODY_DEADLINE_SECONDS):
        for item in _candidate_specs():
            for dependency in item.dependencies:
                mutated = dict(available)
                mutated[dependency] = replace(
                    available[dependency],
                    statement="0 = 1",
                )
                with pytest.raises(CandidateBodyError):
                    replay_candidate_bodies((item,), core=mutated)


@pytest.mark.parametrize("value", range(32))
def test_small_square_residues_match_the_exact_constructive_cases(value: int) -> None:
    quotient, remainder = divmod(value * value, 4)
    assert remainder in (0, 1)
    assert value * value == 4 * quotient + remainder
    if value % 2 == 0:
        assert quotient == (value // 2) ** 2
    else:
        half = value // 2
        assert quotient == half * half + half


@pytest.mark.parametrize("prime_value", (5, 13, 17, 29, 37, 41, 53, 61, 73, 89, 97))
def test_mod_four_one_prime_examples_have_root_and_divisible_norm(
    prime_value: int,
) -> None:
    roots = tuple(
        candidate
        for candidate in range(prime_value)
        if (candidate * candidate) % prime_value == prime_value - 1
    )

    assert prime_value % 4 == 1
    assert len(roots) == 2
    for root in roots:
        quotient, remainder = divmod(root * root + 1, prime_value)
        assert remainder == 0
        assert quotient > 0
        assert root * root + 1 == prime_value * quotient


@pytest.mark.parametrize("prime_value", (3, 7, 11, 19, 23, 31, 43, 47, 59, 67))
def test_mod_four_three_prime_examples_reject_two_square_representation(
    prime_value: int,
) -> None:
    assert prime_value % 4 == 3
    assert not any(
        first * first + second * second == prime_value
        for first in range(prime_value + 1)
        for second in range(prime_value + 1)
    )


@pytest.mark.parametrize("divisor", range(1, 20))
def test_bounded_positive_multiple_examples_force_exact_divisor(
    divisor: int,
) -> None:
    valid = tuple(
        value
        for value in range(1, 2 * divisor)
        if value % divisor == 0
    )
    assert valid == (divisor,)
