"""Focused body audit for Eisenstein semantic-row quotient bridges."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.eisenstein_division_threshold_candidate import (
    make_eisenstein_division_threshold_candidate_theorems,
)
from peano_lab.library.eisenstein_initial_segment_count_candidate import (
    make_eisenstein_initial_segment_count_candidate_theorems,
)
from peano_lab.library.eisenstein_quotient_bound_candidate import (
    make_eisenstein_quotient_bound_candidate_theorems,
)
from peano_lab.library.eisenstein_remainder_nonzero_candidate import (
    make_eisenstein_remainder_nonzero_candidate_theorems,
)
from peano_lab.library.eisenstein_row_quotient_candidate import (
    make_eisenstein_row_quotient_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "eisenstein_row_indicator_prefix_to_initial_segment",
    "distinct_odd_prime_row_bit_count_equals_division_quotient",
    "distinct_odd_prime_row_bit_count_equals_decoded_quotient",
    "distinct_odd_prime_semantic_row_equals_decoded_quotient",
)

EXPECTED_DEPENDENCIES = {
    "eisenstein_row_indicator_prefix_to_initial_segment": (
        "nonzero_remainder_division_positive_multiple_threshold",
        "le_or_lt",
    ),
    "distinct_odd_prime_row_bit_count_equals_division_quotient": (
        "distinct_primes_own_odd_half_scaled_remainder_nonzero",
        "odd_half_division_quotient_bounded",
        "eisenstein_row_indicator_prefix_to_initial_segment",
        "eisenstein_initial_segment_bit_count_exact",
        "bit_count_functional",
    ),
    "distinct_odd_prime_row_bit_count_equals_decoded_quotient": (
        "add_succ_left",
        "zero_add",
        "beta_at_unique",
        "distinct_odd_prime_row_bit_count_equals_division_quotient",
    ),
    "distinct_odd_prime_semantic_row_equals_decoded_quotient": (
        "distinct_odd_prime_row_bit_count_equals_decoded_quotient",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "eisenstein_row_indicator_prefix_to_initial_segment": (
        "3d091b94ac2ed1a7f6afb1246e2fb8b7604d32b38c7307e9fd589d9c64e5ab13"
    ),
    "distinct_odd_prime_row_bit_count_equals_division_quotient": (
        "dad4bd8f7016d3809269095bfa0250f3400b92bfa0c2f2d021173bad61cec3a2"
    ),
    "distinct_odd_prime_row_bit_count_equals_decoded_quotient": (
        "6e54a4d069677ab8178fde009dafb5e968e131def017ce33f09469df94b74e32"
    ),
    "distinct_odd_prime_semantic_row_equals_decoded_quotient": (
        "45d36cfcf536315ede9c4b3f0c539dcb9617add6b05252b55168fa06ba7eb276"
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "eisenstein_row_indicator_prefix_to_initial_segment": (
        2,
        55,
        78,
        36,
        78,
        77,
        0,
    ),
    "distinct_odd_prime_row_bit_count_equals_division_quotient": (
        5,
        79,
        95,
        45,
        95,
        94,
        0,
    ),
    "distinct_odd_prime_row_bit_count_equals_decoded_quotient": (
        4,
        96,
        111,
        55,
        111,
        110,
        0,
    ),
    "distinct_odd_prime_semantic_row_equals_decoded_quotient": (
        1,
        53,
        119,
        72,
        119,
        118,
        0,
    ),
}

_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_row_quotient_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    factories = (
        make_eisenstein_division_threshold_candidate_theorems,
        make_eisenstein_remainder_nonzero_candidate_theorems,
        make_eisenstein_quotient_bound_candidate_theorems,
        make_eisenstein_initial_segment_count_candidate_theorems,
    )
    for factory in factories:
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein row-quotient replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_row_quotient_factory_is_exact_dependency_ordered_and_isolated() -> None:
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


def test_row_quotient_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "AllBits(",
        "BetaAt(",
        "BitCount(",
        "DivRem(",
        "Floor(",
        "InitialSegment(",
        "Prime(",
        "RowIndicator(",
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

    transport, relational, decoded, semantic = _candidate_specs()
    assert transport.statement.startswith("forall p q i d r rb rc k.")
    assert "q * S i = p * d + r" in transport.statement
    assert relational.statement.startswith("forall p q h k i d r rb rc n.")
    assert relational.statement.endswith("n = d")
    assert decoded.statement.startswith(
        "forall p q h k i tb tc qb qc ub uc rb rc n d."
    )
    assert decoded.statement.endswith("n = d")
    assert semantic.statement.startswith(
        "forall p q h k i tb tc qb qc ub uc n d."
    )
    assert semantic.statement.endswith("n = d")


def test_row_quotient_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_row_quotient_bodies_kernel_check_within_laptop_limit() -> None:
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
        "EISENSTEIN ROW QUOTIENT BODY RECEIPTS "
        f"elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
