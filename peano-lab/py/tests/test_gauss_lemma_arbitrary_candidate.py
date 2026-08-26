"""Focused native-body audit for arbitrary-representative Gauss lemma."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.euler_criterion_arbitrary_candidate import (
    make_euler_criterion_arbitrary_candidate_theorems,
)
from peano_lab.library.euler_criterion_bounded_candidate import (
    make_euler_criterion_bounded_candidate_theorems,
)
from peano_lab.library.gauss_lemma_arbitrary_candidate import (
    make_gauss_lemma_arbitrary_candidate_theorems,
)
from peano_lab.library.gauss_lemma_endpoint_candidate import (
    make_gauss_lemma_endpoint_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAME = "arbitrary_gauss_lemma_complete"
EXPECTED_DEPENDENCIES = (
    "gauss_lemma_power_congruence_exists",
    "pow_predecessor_parity_mod",
    "arbitrary_euler_criterion_complete",
    "parity_cases",
    "odd_prime_one_not_mod_predecessor",
    "mod_eq_symm",
    "mod_eq_trans",
    "mul_comm",
    "zero_add",
)
EXPECTED_STATEMENT_SHA256 = (
    "8520424f2215144d7374e9a7f45986f0ffeb4459a7a3f54cca5a8cd4888bbb44"
)
EXPECTED_BODY_RECEIPT = (9, 188, 547, 49, 513, 546, 34)
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_lemma_arbitrary_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_gauss_lemma_endpoint_candidate_theorems,
        make_euler_criterion_bounded_candidate_theorems,
        make_euler_criterion_arbitrary_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"arbitrary Gauss replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_arbitrary_gauss_factory_is_exact_deterministic_and_isolated() -> None:
    first = _candidate_specs()
    second = make_gauss_lemma_arbitrary_candidate_theorems(TheoremSpec)

    assert second == first
    assert len(first) == 1
    (item,) = first
    assert item.name == EXPECTED_NAME
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert sha256(item.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert item.name not in _specs_by_name()
    assert "gauss_lemma_arbitrary_candidate" not in Path(
        theorem_registry.__file__
    ).read_text()


def test_arbitrary_gauss_contract_is_closed_expanded_native_pa() -> None:
    (item,) = _candidate_specs()
    formula, free_names = parse_formula_with_names(item.statement)

    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.startswith("forall p h a b c. p = 2 * h + 1 ->")
    assert len(item.statement) == 6_285
    assert "frm_factor_gla_nondivisor" in item.statement
    assert "wpo_gap_glb_a_positive" not in item.statement
    assert "wpo_gap_glb_a_lt_p" not in item.statement
    assert item.statement.count("exists e.") == 1
    assert item.statement.count("exists mb mc sb sc.") == 1
    assert item.statement.count("e = 2 * gs_even_gla_even") == 2
    assert item.statement.count("e = 2 * gs_odd_gla_odd + 1") == 2
    assert all(
        token not in item.statement
        for token in (
            "BetaAt(",
            "BitCount(",
            "Even(",
            "HalfRange(",
            "ModEq(",
            "Odd(",
            "Prime(",
            "QRes(",
            "SignedHalfPrefix(",
            "%",
            "^",
            "∣",
            "≡",
            "↔",
        )
    )


def test_arbitrary_gauss_recipe_changes_only_the_entrance_and_euler_call() -> None:
    commands = _candidate_specs()[0].script

    assert commands[:9] == (
        "intro p",
        "intro h",
        "intro a",
        "intro b",
        "intro c",
        "intro hpodd",
        "intro hprime",
        "intro hnotdiv",
        "intro hhalf",
    )
    assert "specialize arbitrary_euler_criterion_complete p" in commands
    assert "specialize bounded_euler_criterion_complete p" not in commands
    assert "intro hpositive" not in commands
    assert "intro halt" not in commands
    assert "have ha0 : ~(a = 0)" not in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_arbitrary_gauss_body_kernel_checks_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        (receipt,) = replay_candidate_bodies(
            _candidate_specs(), core=_dependency_core()
        )
    elapsed = perf_counter() - started
    observed = (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    )
    assert observed == EXPECTED_BODY_RECEIPT
    assert elapsed < _BODY_DEADLINE_SECONDS
    print(
        "ARBITRARY GAUSS LEMMA BODY RECEIPT "
        f"elapsed={elapsed:.3f}s receipt={observed}",
        flush=True,
    )
