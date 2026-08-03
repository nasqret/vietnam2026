"""Focused native-body audit for the modulo-two parity interface."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.euler_criterion_residue_candidate import (
    make_euler_criterion_residue_candidate_theorems,
)
from peano_lab.library.parity_mod_two_candidate import (
    make_parity_mod_two_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "even_to_mod_two_zero",
    "mod_two_zero_to_even",
    "odd_to_mod_two_one",
    "mod_two_one_to_odd",
    "mod_two_preserves_parity",
)
EXPECTED_DEPENDENCIES = {
    "even_to_mod_two_zero": ("dvd_to_mod_zero",),
    "mod_two_zero_to_even": ("mod_eq_zero_to_dvd_nonzero",),
    "odd_to_mod_two_one": ("add_comm",),
    "mod_two_one_to_odd": ("mod_eq_to_remainder_decomposition", "mul_comm"),
    "mod_two_preserves_parity": (
        "even_to_mod_two_zero",
        "mod_two_zero_to_even",
        "odd_to_mod_two_one",
        "mod_two_one_to_odd",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "even_to_mod_two_zero":
        "43451bbe1ec195e850a8a10fef347a79fcf5e5cc8c488c202bec3e49036d3b9f",
    "mod_two_zero_to_even":
        "17819960c4cc0ea5c84ae28074af3d74746fa205c787b3dfda4b2761b3e0679c",
    "odd_to_mod_two_one":
        "ba5caea84cb223eea56e3c85199a61cba3078e50bd1a869628a32a16eabc6a0d",
    "mod_two_one_to_odd":
        "35f9626480f85ddc3f250930eeb21a8a7cd8dccd3cbc93dd18b4e1543c92f7d5",
    "mod_two_preserves_parity":
        "3af169ad5b910b9461d506d24689cd28d29a57316103eadabb8d897efe0da3f8",
}
EXPECTED_BODY_RECEIPTS = {
    "even_to_mod_two_zero": (1, 6, 14, 9, 14, 13, 0),
    "mod_two_zero_to_even": (1, 9, 20, 13, 20, 19, 0),
    "odd_to_mod_two_one": (1, 11, 42, 18, 39, 41, 3),
    "mod_two_one_to_odd": (2, 20, 50, 16, 50, 49, 0),
    "mod_two_preserves_parity": (6, 76, 86, 20, 86, 85, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_parity_mod_two_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for item in make_euler_criterion_residue_candidate_theorems(TheoremSpec):
        core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"modulo-two parity replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_mod_two_parity_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_parity_mod_two_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_mod_two_parity_contracts_are_closed_expanded_native_pa() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("Even(", "Odd(", "Mod(", "%", "<", "<=")
        )

    transport = _candidate_specs()[-1].statement
    assert transport.startswith("forall n m.")
    assert "n + 2 *" in transport
    assert "m + 2 *" in transport


def test_mod_two_parity_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_mod_two_parity_bodies_kernel_check_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_dependency_core()
        )
    elapsed = perf_counter() - started
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
    assert elapsed < _BODY_DEADLINE_SECONDS
    print(
        f"MOD TWO PARITY BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
