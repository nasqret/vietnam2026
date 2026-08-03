"""Focused body audit for the complete constructive bounded Gauss lemma."""

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
from peano_lab.library.euler_criterion_bounded_candidate import (
    make_euler_criterion_bounded_candidate_theorems,
)
from peano_lab.library.gauss_lemma_bounded_candidate import (
    make_gauss_lemma_bounded_candidate_theorems,
)
from peano_lab.library.gauss_lemma_endpoint_candidate import (
    make_gauss_lemma_endpoint_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAME = "bounded_gauss_lemma_complete"
EXPECTED_DEPENDENCIES = (
    "lt_irrefl_expanded",
    "bounded_nonzero_not_divides",
    "gauss_lemma_power_congruence_exists",
    "pow_predecessor_parity_mod",
    "bounded_euler_criterion_complete",
    "parity_cases",
    "odd_prime_one_not_mod_predecessor",
    "mod_eq_symm",
    "mod_eq_trans",
    "mul_comm",
    "zero_add",
)
EXPECTED_STATEMENT_SHA256 = (
    "30f9a62162c2d1fe6e589ba3a5b5e5653bf5e527ab5b86a29ae394c448893b39"
)
# dependencies, commands, nodes, depth, objects, edges, reused objects
EXPECTED_BODY_RECEIPT = (11, 204, 597, 53, 559, 596, 38)
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_lemma_bounded_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_gauss_lemma_endpoint_candidate_theorems,
        make_euler_criterion_bounded_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"bounded Gauss replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_bounded_gauss_factory_is_exact_deterministic_and_isolated() -> None:
    first = _candidate_specs()
    second = _candidate_specs()

    assert second == first
    assert len(first) == 1
    (item,) = first
    assert item.name == EXPECTED_NAME
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert sha256(item.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert item.name not in _specs_by_name()
    assert "gauss_lemma_bounded_candidate" not in Path(
        theorem_registry.__file__
    ).read_text()


def test_bounded_gauss_contract_is_closed_expanded_native_pa() -> None:
    (item,) = _candidate_specs()
    formula, free_names = parse_formula_with_names(item.statement)

    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.startswith(
        "forall p h a b c. p = 2 * h + 1 ->"
    )
    assert len(item.statement) == 6_343
    assert "wpo_gap_glb_a_positive" in item.statement
    assert all(
        token not in item.statement
        for token in (
            "BetaAt(",
            "BitCount(",
            "Even(",
            "HalfRange(",
            "ModEq(",
            "Odd(",
            "Pow(",
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


def test_bounded_gauss_endpoint_retains_count_provenance_and_both_iffs() -> None:
    statement = _candidate_specs()[0].statement
    outer_count = statement.index("exists e.")
    hidden_prefix = statement.index("exists mb mc sb sc.", outer_count)

    assert outer_count < hidden_prefix
    assert statement.count("exists e.") == 1
    assert statement.count("exists mb mc sb sc.") == 1
    assert "exists e A R." not in statement
    assert statement.count("e = 2 * gs_even_glb_even") == 2
    assert statement.count("e = 2 * gs_odd_glb_odd + 1") == 2
    assert statement.count("exists qr_x_glb_qres.") == 4


def test_bounded_gauss_script_has_no_automation_or_classical_escape() -> None:
    commands = _candidate_specs()[0].script

    assert "specialize parity_cases x" in commands
    assert "specialize mod_eq_symm p" in commands
    assert "specialize mod_eq_trans p" in commands
    assert "specialize odd_prime_one_not_mod_predecessor p" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_bounded_gauss_body_kernel_checks_within_laptop_limit() -> None:
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
        "BOUNDED GAUSS LEMMA BODY RECEIPT "
        f"elapsed={elapsed:.3f}s receipt={observed}",
        flush=True,
    )
