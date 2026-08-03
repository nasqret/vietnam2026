"""Focused body audit for universal Eisenstein Fubini and its exact endpoint."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.eisenstein_fubini_row_decomposition_candidate import (
    make_eisenstein_fubini_row_decomposition_candidate_theorems,
)
from peano_lab.library.eisenstein_fubini_total_candidate import (
    eisenstein_fubini_column_count_prefix,
    eisenstein_fubini_column_count_witness,
    make_eisenstein_fubini_total_candidate_theorems,
)
from peano_lab.library.eisenstein_rectangle_count_candidate import (
    make_eisenstein_rectangle_count_candidate_theorems,
)
from peano_lab.library.eisenstein_row_indicator_candidate import (
    make_eisenstein_row_indicator_candidate_theorems,
)
from peano_lab.library.eisenstein_transposed_column_candidate import (
    make_eisenstein_transposed_column_candidate_theorems,
)
from peano_lab.library.eisenstein_transposed_column_count_candidate import (
    make_eisenstein_transposed_column_count_candidate_theorems,
)
from peano_lab.library.finite_repeat_sum_candidate import (
    make_finite_repeat_sum_candidate_theorems,
)
from peano_lab.library.finite_sum_pointwise_add_candidate import (
    make_finite_sum_pointwise_add_candidate_theorems,
)
from peano_lab.library.finite_sum_transport_candidate import (
    make_finite_sum_transport_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "eisenstein_transposed_column_decoded_choice",
    "eisenstein_transposed_column_counts_extensional",
    "eisenstein_fubini_column_count_witness_retarget",
    "eisenstein_fubini_column_count_prefix_succ_restrict",
    "eisenstein_fubini_column_count_prefix_retarget_predecessor",
    "eisenstein_fubini_universal",
    "eisenstein_transposed_column_count_prefix_forget",
    "eisenstein_constructed_column_total_equals_swapped_total",
    "eisenstein_rectangle_floor_sum_identity",
)

EXPECTED_DEPENDENCIES = {
    "eisenstein_transposed_column_decoded_choice": (
        "beta_at_unique",
        "eisenstein_row_indicator_decoded_choice",
    ),
    "eisenstein_transposed_column_counts_extensional": (
        "beta_at_exists",
        "eisenstein_transposed_column_decoded_choice",
        "eisenstein_cell_indicator_choice_unique",
        "beta_sum_transport_prefix",
        "beta_sum_functional",
    ),
    "eisenstein_fubini_column_count_witness_retarget": (
        "eisenstein_transposed_outer_column_choices",
        "eisenstein_transposed_column_prefix_exists",
        "eisenstein_transposed_column_prefix_all_bits",
        "bit_count_exists",
        "eisenstein_transposed_column_counts_extensional",
    ),
    "eisenstein_fubini_column_count_prefix_succ_restrict": ("le_succ",),
    "eisenstein_fubini_column_count_prefix_retarget_predecessor": (
        "le_succ",
        "eisenstein_fubini_column_count_witness_retarget",
    ),
    "eisenstein_fubini_universal": (
        "beta_sum_zero",
        "eisenstein_zero_width_rectangle_sum_zero",
        "eisenstein_successor_rectangle_row_split_prefix_exists",
        "eisenstein_successor_row_split_reduced_rectangle_prefix",
        "beta_sum_exists",
        "eisenstein_successor_row_split_sum_add",
        "eisenstein_fubini_column_count_prefix_succ_restrict",
        "eisenstein_fubini_column_count_prefix_retarget_predecessor",
        "beta_sum_succ_decompose",
        "le_refl",
        "beta_at_unique",
        "eisenstein_successor_terminal_sum_matches_last_column",
    ),
    "eisenstein_transposed_column_count_prefix_forget": (),
    "eisenstein_constructed_column_total_equals_swapped_total": (
        "eisenstein_transposed_column_count_prefix_forget",
        "eisenstein_fubini_universal",
    ),
    "eisenstein_rectangle_floor_sum_identity": (
        "eisenstein_rectangle_plus_column_count_total",
        "eisenstein_constructed_column_total_equals_swapped_total",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "eisenstein_transposed_column_decoded_choice": "6b665b9371e7b8659972bbafce5310782fda05c73af67dc858114dff715eb1fa",
    "eisenstein_transposed_column_counts_extensional": "eb28d4edef3bc9daa3153d4cb2c7efb581a007587b3cbf7dc2a4d48ed7a5d466",
    "eisenstein_fubini_column_count_witness_retarget": "c21dfd9718a8c2263bfadbcaf449cb7ade8b7d1a8d45c81e922b131d04e76f9c",
    "eisenstein_fubini_column_count_prefix_succ_restrict": "fd15eee93df9684bcd3a75f21476aa00fb9984eaab7460400001426da0df8f59",
    "eisenstein_fubini_column_count_prefix_retarget_predecessor": "a1f24c6784776a78205621b7f73793161e0c74882d1f8ce3160ac22c4b58af52",
    "eisenstein_fubini_universal": "894d0bfaf8f6df5f754601a6868c3f950af7b298a3d16535f197b4319b82f9fd",
    "eisenstein_transposed_column_count_prefix_forget": "dd9990aa28affcc12e27e0a9139792db17972838833475b0dde5e347a85115ec",
    "eisenstein_constructed_column_total_equals_swapped_total": "0722716fff058bd6c00c9b0f69a5f7306a73f5995c58034a69639d9e21f79458",
    "eisenstein_rectangle_floor_sum_identity": "4d630158591dbb67821f5ded43864829753c0adf24377c89f13a3aa6e09b2469",
}

EXPECTED_BODY_RECEIPTS = {
    "eisenstein_transposed_column_decoded_choice": (2, 52, 72, 35, 72, 71, 0),
    "eisenstein_transposed_column_counts_extensional": (5, 100, 160, 56, 160, 159, 0),
    "eisenstein_fubini_column_count_witness_retarget": (5, 92, 139, 54, 139, 138, 0),
    "eisenstein_fubini_column_count_prefix_succ_restrict": (1, 20, 36, 25, 36, 35, 0),
    "eisenstein_fubini_column_count_prefix_retarget_predecessor": (2, 49, 55, 37, 55, 54, 0),
    "eisenstein_fubini_universal": (12, 216, 264, 65, 264, 263, 0),
    "eisenstein_transposed_column_count_prefix_forget": (0, 33, 38, 25, 38, 37, 0),
    "eisenstein_constructed_column_total_equals_swapped_total": (2, 44, 49, 33, 49, 48, 0),
    "eisenstein_rectangle_floor_sum_identity": (2, 53, 65, 37, 65, 64, 0),
}

_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_fubini_total_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_eisenstein_fubini_row_decomposition_candidate_theorems,
        make_eisenstein_rectangle_count_candidate_theorems,
        make_eisenstein_row_indicator_candidate_theorems,
        make_eisenstein_transposed_column_candidate_theorems,
        make_eisenstein_transposed_column_count_candidate_theorems,
        make_finite_sum_transport_candidate_theorems,
        make_finite_sum_pointwise_add_candidate_theorems,
        make_finite_repeat_sum_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein Fubini total replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_fubini_total_factory_is_exact_ordered_and_isolated() -> None:
    specs = _candidate_specs()
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {item.name: sha256(item.statement.encode()).hexdigest() for item in specs} == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in specs)


def test_fubini_total_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = ("BetaAt(", "BitCount(", "Prime(", "Rectangle(", "RowIndicator(", "Sum(", "%", "<=", "<", "⌊", "∣")
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    left = eisenstein_fubini_column_count_witness("p", "q", "h", "bb", "bc", "i", "k", "n", tag="left")
    right = eisenstein_fubini_column_count_witness("p", "q", "h", "bb", "bc", "i", "k", "n", tag="right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    prefix = eisenstein_fubini_column_count_prefix("p", "q", "h", "bb", "bc", "db", "dc", "h", "k", tag="closed")
    assert set(parse_formula_with_names(prefix)[1]) == {"p", "q", "h", "bb", "bc", "db", "dc", "k"}

    universal = _candidate_specs()[5]
    equality = _candidate_specs()[7]
    endpoint = _candidate_specs()[8]
    assert universal.statement.endswith("M = T")
    assert equality.statement.endswith("M = T")
    assert endpoint.statement.endswith("N + T = h * k")


def test_fubini_total_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all(fragment not in command for command in commands for fragment in ("DNE", "by_contra", "classical", "sorry"))


def test_fubini_total_bodies_kernel_check_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs(), core=_dependency_core())
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
    print(f"EISENSTEIN FUBINI TOTAL BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}", flush=True)
