"""Focused body audit for the Eisenstein quotient/rectangle sum bridge."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.eisenstein_outer_sum_bridge_candidate import (
    make_eisenstein_outer_sum_bridge_candidate_theorems,
)
from peano_lab.library.eisenstein_rectangle_count_candidate import (
    make_eisenstein_rectangle_count_candidate_theorems,
)
from peano_lab.library.eisenstein_row_quotient_candidate import (
    make_eisenstein_row_quotient_candidate_theorems,
)
from peano_lab.library.eisenstein_scaled_division_candidate import (
    make_eisenstein_scaled_division_candidate_theorems,
)
from peano_lab.library.finite_sum_transport_candidate import (
    make_finite_sum_transport_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "distinct_odd_prime_quotient_entry_matches_rectangle",
    "distinct_odd_prime_quotient_sum_transports_to_rectangle",
    "distinct_odd_prime_quotient_sum_equals_rectangle_total",
)

EXPECTED_DEPENDENCIES = {
    "distinct_odd_prime_quotient_entry_matches_rectangle": (
        "distinct_odd_prime_semantic_row_equals_decoded_quotient",
    ),
    "distinct_odd_prime_quotient_sum_transports_to_rectangle": (
        "distinct_odd_prime_quotient_entry_matches_rectangle",
        "beta_sum_transport_prefix",
    ),
    "distinct_odd_prime_quotient_sum_equals_rectangle_total": (
        "distinct_odd_prime_quotient_sum_transports_to_rectangle",
        "beta_sum_functional",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "distinct_odd_prime_quotient_entry_matches_rectangle": (
        "d886764a8fdcbbbb70fcade032ea3261b75aa1ed0e21a4adc14dc8c318af8ea4"
    ),
    "distinct_odd_prime_quotient_sum_transports_to_rectangle": (
        "0c9b5353a1ec92e6450c53b87bcb1d0c8317f007d636e87e533ac00df16cea15"
    ),
    "distinct_odd_prime_quotient_sum_equals_rectangle_total": (
        "93bc8e865c15f2dd2c23e705faedc2c1eab1a7b6ee2520c32fb720ae17b4084f"
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "distinct_odd_prime_quotient_entry_matches_rectangle": (
        1,
        58,
        104,
        52,
        104,
        103,
        0,
    ),
    "distinct_odd_prime_quotient_sum_transports_to_rectangle": (
        2,
        61,
        73,
        54,
        73,
        72,
        0,
    ),
    "distinct_odd_prime_quotient_sum_equals_rectangle_total": (
        2,
        56,
        67,
        51,
        67,
        66,
        0,
    ),
}

_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_outer_sum_bridge_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    factories = (
        make_eisenstein_row_quotient_candidate_theorems,
        make_finite_sum_transport_candidate_theorems,
        make_eisenstein_rectangle_count_candidate_theorems,
        make_eisenstein_scaled_division_candidate_theorems,
    )
    for factory in factories:
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein outer-sum replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_outer_sum_factory_is_exact_dependency_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = _candidate_specs()

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_outer_sum_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "BetaAt(",
        "BitCount(",
        "DivisionPrefix(",
        "Floor(",
        "Prime(",
        "Rectangle(",
        "ScaledPrefix(",
        "Sum(",
        "%",
        "<=",
        "<",
        "⌊",
        "∣",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    pointwise, transported, endpoint = _candidate_specs()
    assert pointwise.statement.startswith(
        "forall p q h k i tb tc qb qc ub uc cb cc d."
    )
    assert transported.statement.startswith(
        "forall p q h k tb tc qb qc ub uc cb cc Q."
    )
    assert endpoint.statement.startswith(
        "forall p q h k tb tc qb qc ub uc cb cc Q T."
    )
    assert endpoint.statement.endswith("Q = T")


def test_outer_sum_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_outer_sum_bodies_kernel_check_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_explicit_dependency_core()
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
        "EISENSTEIN OUTER SUM BODY RECEIPTS "
        f"elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
