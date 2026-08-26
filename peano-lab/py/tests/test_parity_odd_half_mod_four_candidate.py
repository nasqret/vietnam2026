"""Focused body audit for odd-half/modulo-four parity bridges."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.parity_odd_half_mod_four_candidate import (
    make_parity_odd_half_mod_four_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "odd_half_of_mod4_one_exact",
    "odd_half_of_mod4_three_exact",
    "odd_half_even_iff_mod4_one",
    "odd_half_odd_iff_mod4_three",
)
EXPECTED_DEPENDENCIES = {
    "odd_half_of_mod4_one_exact": (
        "four_mul_eq_double_double",
        "odd_half_unique",
    ),
    "odd_half_of_mod4_three_exact": (
        "mul_add",
        "four_mul_eq_double_double",
        "odd_half_unique",
    ),
    "odd_half_even_iff_mod4_one": (
        "four_mul_eq_double_double",
        "odd_half_of_mod4_one_exact",
    ),
    "odd_half_odd_iff_mod4_three": (
        "mul_add",
        "four_mul_eq_double_double",
        "odd_half_of_mod4_three_exact",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "odd_half_of_mod4_one_exact":
        "f93e0e9d2eca8b347167988fe43200b2322babaf53c548603ca0ce3b716d48f9",
    "odd_half_of_mod4_three_exact":
        "a3a4df8e75e084841b5496af1a163b4fcb27874361a106ffe5be66fe994fd930",
    "odd_half_even_iff_mod4_one":
        "56612ac4a05607a59e80b77534b2aa03e4285a0467fe3b2f65e15d674d1327cc",
    "odd_half_odd_iff_mod4_three":
        "4dd913913ff4b504296283ed2a5b41944bdb1e357e40e3b56d9eb070bb9f7a2e",
}
EXPECTED_BODY_RECEIPTS = {
    "odd_half_of_mod4_one_exact": (2, 17, 20, 13, 20, 19, 0),
    "odd_half_of_mod4_three_exact": (3, 19, 78, 27, 69, 77, 9),
    "odd_half_even_iff_mod4_one": (2, 22, 42, 18, 42, 41, 0),
    "odd_half_odd_iff_mod4_three": (3, 24, 100, 30, 91, 99, 9),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_parity_odd_half_mod_four_candidate_theorems(TheoremSpec)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"odd-half modulo-four replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_odd_half_mod_four_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    assert make_parity_odd_half_mod_four_candidate_theorems(TheoremSpec) == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_odd_half_mod_four_contracts_are_closed_expanded_native_pa() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("Even(", "Odd(", "Mod4(", "%", "↔")
        )

    assert _candidate_specs()[0].statement.endswith("h = 2 * a")
    assert _candidate_specs()[1].statement.endswith("h = 2 * a + 1")


def test_odd_half_mod_four_scripts_are_constructive_and_explicit() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert "apply odd_half_unique" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_odd_half_mod_four_bodies_kernel_check_within_laptop_limit() -> None:
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs())
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
