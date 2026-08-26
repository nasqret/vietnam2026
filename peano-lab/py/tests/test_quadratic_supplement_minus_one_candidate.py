"""Focused constructive audit of the first quadratic supplementary law."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
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
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.euler_criterion_bounded_candidate import (
    make_euler_criterion_bounded_candidate_theorems,
)
from peano_lab.library.parity_odd_half_mod_four_candidate import (
    make_parity_odd_half_mod_four_candidate_theorems,
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
    "prime_predecessor_nonzero",
    "odd_predecessor_double_half",
    "quadratic_supplement_minus_one_half_parity",
    "quadratic_supplement_minus_one_residue_iff_mod_four_one",
    "quadratic_supplement_minus_one_nonresidue_iff_mod_four_three",
    "quadratic_supplement_minus_one_complete",
)

EXPECTED_DEPENDENCIES = {
    "prime_predecessor_nonzero": (),
    "odd_predecessor_double_half": ("mul_comm", "zero_add"),
    "quadratic_supplement_minus_one_half_parity": (
        "prime_predecessor_nonzero",
        "pow_exists",
        "bounded_euler_criterion_complete",
        "pow_predecessor_parity_mod",
        "parity_cases",
        "zero_add",
    ),
    "quadratic_supplement_minus_one_residue_iff_mod_four_one": (
        "odd_predecessor_double_half",
        "quadratic_supplement_minus_one_half_parity",
        "odd_half_even_iff_mod4_one",
    ),
    "quadratic_supplement_minus_one_nonresidue_iff_mod_four_three": (
        "odd_predecessor_double_half",
        "quadratic_supplement_minus_one_half_parity",
        "odd_half_odd_iff_mod4_three",
    ),
    "quadratic_supplement_minus_one_complete": (
        "quadratic_supplement_minus_one_residue_iff_mod_four_one",
        "quadratic_supplement_minus_one_nonresidue_iff_mod_four_three",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "prime_predecessor_nonzero": (
        "981f890dda85857cd047906cf398fcc9e195cc8c9f3642d89810a0bc24136cc0"
    ),
    "odd_predecessor_double_half": (
        "34a72fd5c00ef7946258390cd8c35d58cc3ec74049f23875f1d6ba705350bc9c"
    ),
    "quadratic_supplement_minus_one_half_parity": (
        "bda266c91596a44668d02dffceb0bdce7c900a46463f6d47c0d0b9561ea52aba"
    ),
    "quadratic_supplement_minus_one_residue_iff_mod_four_one": (
        "6c421211493d2f15a974fd7828e2bfdae80d4391cf65413efbf9e83c98e10c9d"
    ),
    "quadratic_supplement_minus_one_nonresidue_iff_mod_four_three": (
        "c99890cd3fa32b6fe2f6bb79ec3a0f773530a49e0288ce17f0b249a78f7b8b06"
    ),
    "quadratic_supplement_minus_one_complete": (
        "7ea81062b843e7fff4939ffce5b6fa14a87312619f7f49e3abd5993bfa02134e"
    ),
}

# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_BODY_RECEIPTS = {
    "prime_predecessor_nonzero": (0, 10, 22, 14, 22, 21, 0),
    "odd_predecessor_double_half": (2, 25, 51, 17, 50, 50, 1),
    "quadratic_supplement_minus_one_half_parity": (
        6,
        91,
        236,
        35,
        233,
        235,
        3,
    ),
    "quadratic_supplement_minus_one_residue_iff_mod_four_one": (
        3,
        38,
        69,
        22,
        69,
        68,
        0,
    ),
    "quadratic_supplement_minus_one_nonresidue_iff_mod_four_three": (
        3,
        40,
        72,
        23,
        72,
        71,
        0,
    ),
    "quadratic_supplement_minus_one_complete": (2, 18, 38, 16, 38, 37, 0),
}

_BODY_DEADLINE_SECONDS = 30


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_quadratic_supplement_minus_one_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_euler_criterion_bounded_candidate_theorems,
        make_parity_odd_half_mod_four_candidate_theorems,
    ):
        core.update((item.name, item) for item in factory(TheoremSpec))
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
        raise TimeoutError(f"minus-one supplementary replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_minus_one_supplement_factory_is_exact_deterministic_and_isolated() -> None:
    first = _candidate_specs()
    second = make_quadratic_supplement_minus_one_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "quadratic_supplement_minus_one_candidate" not in registry_source


def test_minus_one_supplement_contracts_are_closed_expanded_native_ha() -> None:
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
                "ModEq(",
                "Pow(",
                "Prime(",
                "QRes(",
                "%",
                "^",
                "∣",
                "≡",
                "↔",
            )
        )

    positive, negative, complete = _candidate_specs()[-3:]
    for endpoint in (positive, negative, complete):
        assert endpoint.statement.startswith("forall p n. p = S n ->")
        assert "p = 2 * qsm_odd_modulus + 1" in endpoint.statement
        assert "qr_x_qsm_predecessor * qr_x_qsm_predecessor" in endpoint.statement
    assert "p = 4 * qsm_four_one_modulus + 1" in positive.statement
    assert "p = 4 * qsm_four_three_modulus + 3" in negative.statement
    assert "p = 4 * qsm_four_one_modulus + 1" in complete.statement
    assert "p = 4 * qsm_four_three_modulus + 3" in complete.statement


def test_minus_one_supplement_scripts_are_constructive_and_provenance_preserving() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)

    assert "apply bounded_euler_criterion_complete" in commands
    assert "apply pow_predecessor_parity_mod" in commands
    assert "apply odd_half_even_iff_mod4_one" in commands
    assert "apply odd_half_odd_iff_mod4_three" in commands
    assert "specialize parity_cases h" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_minus_one_supplement_bodies_kernel_check_within_laptop_limit() -> None:
    with _body_deadline(_BODY_DEADLINE_SECONDS):
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


def test_minus_one_supplement_certificates_are_dne_free_and_reject_false_laws() -> None:
    for item in _candidate_specs():
        certificate, target = _body_certificate(item.name)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))

    positive, negative, complete = _candidate_specs()[-3:]
    mutations = (
        (
            positive,
            "p = 4 * qsm_four_one_modulus + 1",
            "p = 4 * qsm_four_one_modulus + 3",
        ),
        (
            negative,
            "p = 4 * qsm_four_three_modulus + 3",
            "p = 4 * qsm_four_three_modulus + 1",
        ),
        (
            complete,
            "p = 4 * qsm_four_one_modulus + 1",
            "p = 4 * qsm_four_one_modulus + 3",
        ),
    )
    for item, correct, false in mutations:
        assert correct in item.statement
        certificate, _ = _body_certificate(item.name)
        false_statement = item.statement.replace(correct, false)
        assert not check((), certificate, _curried_target(item, false_statement))


@pytest.mark.parametrize("prime_value", (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37))
def test_minus_one_supplement_matches_small_prime_witnesses(prime_value: int) -> None:
    predecessor = prime_value - 1
    roots = tuple(
        root
        for root in range(prime_value)
        if (root * root) % prime_value == predecessor
    )

    assert bool(roots) is (prime_value % 4 == 1)
    assert (not roots) is (prime_value % 4 == 3)
    if roots:
        assert len(roots) == 2
        assert sum(roots) == prime_value
