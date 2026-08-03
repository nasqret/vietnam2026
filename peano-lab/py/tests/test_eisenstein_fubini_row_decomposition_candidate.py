"""Focused body audit for successor-row decomposition in Eisenstein Fubini."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.eisenstein_fubini_row_decomposition_candidate import (
    eisenstein_successor_row_count_decomposition,
    eisenstein_successor_row_split_prefix,
    make_eisenstein_fubini_row_decomposition_candidate_theorems,
)
from peano_lab.library.eisenstein_rectangle_count_candidate import (
    make_eisenstein_rectangle_count_candidate_theorems,
)
from peano_lab.library.eisenstein_row_indicator_candidate import (
    make_eisenstein_row_indicator_candidate_theorems,
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
    "eisenstein_row_indicator_prefix_succ_restrict",
    "eisenstein_successor_row_count_decompose",
    "eisenstein_rectangle_decoded_successor_row_count_decompose",
    "eisenstein_successor_row_split_choices",
    "eisenstein_successor_row_split_prefix_extend",
    "eisenstein_successor_row_split_prefix_exists",
    "eisenstein_successor_rectangle_row_split_prefix_exists",
    "eisenstein_successor_row_split_decoded_add",
    "eisenstein_successor_row_split_sum_add",
    "eisenstein_cell_indicator_choice_unique",
    "eisenstein_successor_terminal_bit_matches_last_column",
    "eisenstein_successor_terminal_prefix_to_last_column",
    "eisenstein_successor_terminal_sum_matches_last_column",
    "eisenstein_rectangle_row_count_prefix_succ_restrict",
    "eisenstein_successor_row_split_reduced_rectangle_prefix",
    "eisenstein_zero_width_rectangle_sum_zero",
)

EXPECTED_DEPENDENCIES = {
    "eisenstein_row_indicator_prefix_succ_restrict": ("le_succ",),
    "eisenstein_successor_row_count_decompose": (
        "eisenstein_row_indicator_prefix_succ_restrict",
        "bit_count_succ_decompose",
    ),
    "eisenstein_rectangle_decoded_successor_row_count_decompose": (
        "eisenstein_rectangle_decoded_row_count",
        "eisenstein_successor_row_count_decompose",
    ),
    "eisenstein_successor_row_split_choices": (
        "eisenstein_successor_row_count_decompose",
    ),
    "eisenstein_successor_row_split_prefix_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "eisenstein_successor_row_split_prefix_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        "eisenstein_successor_row_split_prefix_extend",
    ),
    "eisenstein_successor_rectangle_row_split_prefix_exists": (
        "eisenstein_successor_row_split_choices",
        "eisenstein_successor_row_split_prefix_exists",
    ),
    "eisenstein_successor_row_split_decoded_add": ("beta_at_unique",),
    "eisenstein_successor_row_split_sum_add": (
        "eisenstein_successor_row_split_decoded_add",
        "beta_sum_pointwise_add",
    ),
    "eisenstein_cell_indicator_choice_unique": (),
    "eisenstein_successor_terminal_bit_matches_last_column": (
        "le_refl",
        "beta_at_unique",
        "eisenstein_row_indicator_decoded_choice",
        "eisenstein_cell_indicator_choice_unique",
    ),
    "eisenstein_successor_terminal_prefix_to_last_column": (
        "beta_at_exists",
        "eisenstein_successor_terminal_bit_matches_last_column",
    ),
    "eisenstein_successor_terminal_sum_matches_last_column": (
        "eisenstein_successor_terminal_prefix_to_last_column",
        "beta_sum_transport_prefix",
        "beta_sum_functional",
    ),
    "eisenstein_rectangle_row_count_prefix_succ_restrict": ("le_succ",),
    "eisenstein_successor_row_split_reduced_rectangle_prefix": (),
    "eisenstein_zero_width_rectangle_sum_zero": (
        "beta_repeat_exists",
        "eisenstein_rectangle_decoded_row_count",
        "bit_count_zero",
        "beta_sum_transport_prefix",
        "beta_repeat_sum_exact",
        "mul_comm",
        "mul_zero_left",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "eisenstein_row_indicator_prefix_succ_restrict": "b931855319afa55076390c5f943f738de6842fb1de14a89131ba7c5d145858eb",
    "eisenstein_successor_row_count_decompose": "96fa3bb4fa4813b6c20770c880846e628acd97f66ba3be0e3ff2a0fa31bd8ad4",
    "eisenstein_rectangle_decoded_successor_row_count_decompose": "926587c24495a8fa1ccf2139abb722aec54b61e1f483551cc4b2380cdb0cfb89",
    "eisenstein_successor_row_split_choices": "65ed68440b9c1d0d074a0fbf8bf28cf6520aa036f9a32976f16e51f417f1d157",
    "eisenstein_successor_row_split_prefix_extend": "12edc47ccdd135fa46e50c91f8a7f0645a24ed42729ef61a6624959778fd6ab5",
    "eisenstein_successor_row_split_prefix_exists": "3117dc381af0f188a0380fa5521b3c7cda965eafa9c4d041156e63b1c5e94c66",
    "eisenstein_successor_rectangle_row_split_prefix_exists": "08f7b28aa8ba29463e28018530ae13d3ad561bf61ec7575ce8aed8c17459d230",
    "eisenstein_successor_row_split_decoded_add": "e320bd59e3343e5c700e9ccff7647a1fd8d1b7fe51c91fc163c7f054a661c63e",
    "eisenstein_successor_row_split_sum_add": "2717d9d9409d734c4898b43b78015399b9670a4861bfcbacc55d6fadf46fc62e",
    "eisenstein_cell_indicator_choice_unique": "94a5f6b0e10dae98b882421d1b93c4b7c3d04d55d5c4f61b585fb55358095e29",
    "eisenstein_successor_terminal_bit_matches_last_column": "3db0b9e42aab77021730ca84cef7a0eae1491e07d1d429502fa9d31c4085e165",
    "eisenstein_successor_terminal_prefix_to_last_column": "41a4378b93fcb1371449109b7dfe73c407f5a46101922eb03935397aac5fc0ed",
    "eisenstein_successor_terminal_sum_matches_last_column": "b7594b3f1dff1dfa3a963016c9f99489ee1db182a1a3dbfb6b3a6aa1a77c1c2c",
    "eisenstein_rectangle_row_count_prefix_succ_restrict": "29f80beadf1b7cd126d8e823a5a57d101743310c5aca597904400e8e9292e708",
    "eisenstein_successor_row_split_reduced_rectangle_prefix": "73c5d701147bcd439122c53e73fbd4c147b24e5a5e3a164359017fa807753752",
    "eisenstein_zero_width_rectangle_sum_zero": "7c99ca6c1c3e57fb56d20086e3c148e0b6c5c63ee6ba17abb5463f4441ba61f0",
}

EXPECTED_BODY_RECEIPTS = {
    "eisenstein_row_indicator_prefix_succ_restrict": (1, 18, 34, 23, 34, 33, 0),
    "eisenstein_successor_row_count_decompose": (2, 53, 68, 31, 68, 67, 0),
    "eisenstein_rectangle_decoded_successor_row_count_decompose": (2, 35, 40, 28, 40, 39, 0),
    "eisenstein_successor_row_split_choices": (1, 35, 39, 23, 39, 38, 0),
    "eisenstein_successor_row_split_prefix_extend": (2, 99, 147, 44, 147, 146, 0),
    "eisenstein_successor_row_split_prefix_exists": (5, 62, 72, 33, 72, 71, 0),
    "eisenstein_successor_rectangle_row_split_prefix_exists": (2, 29, 32, 22, 32, 31, 0),
    "eisenstein_successor_row_split_decoded_add": (1, 67, 79, 37, 79, 78, 0),
    "eisenstein_successor_row_split_sum_add": (2, 63, 72, 50, 72, 71, 0),
    "eisenstein_cell_indicator_choice_unique": (0, 35, 110, 29, 110, 109, 0),
    "eisenstein_successor_terminal_bit_matches_last_column": (4, 111, 159, 51, 159, 158, 0),
    "eisenstein_successor_terminal_prefix_to_last_column": (2, 53, 90, 49, 90, 89, 0),
    "eisenstein_successor_terminal_sum_matches_last_column": (3, 64, 72, 51, 72, 71, 0),
    "eisenstein_rectangle_row_count_prefix_succ_restrict": (1, 18, 34, 23, 34, 33, 0),
    "eisenstein_successor_row_split_reduced_rectangle_prefix": (0, 39, 45, 28, 45, 44, 0),
    "eisenstein_zero_width_rectangle_sum_zero": (7, 82, 105, 40, 105, 104, 0),
}

_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_fubini_row_decomposition_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_eisenstein_rectangle_count_candidate_theorems,
        make_eisenstein_row_indicator_candidate_theorems,
        make_finite_sum_pointwise_add_candidate_theorems,
        make_finite_sum_transport_candidate_theorems,
        make_finite_repeat_sum_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein Fubini row replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_fubini_row_factory_is_exact_ordered_and_isolated() -> None:
    specs = _candidate_specs()
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {item.name: sha256(item.statement.encode()).hexdigest() for item in specs} == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in specs)


def test_fubini_row_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = ("BetaAt(", "BitCount(", "Prime(", "Rectangle(", "RowIndicator(", "Sum(", "%", "<=", "<", "⌊", "∣")
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    left = eisenstein_successor_row_count_decomposition("p", "q", "h", "sh", "i", "n", tag="left")
    right = eisenstein_successor_row_count_decomposition("p", "q", "h", "sh", "i", "n", tag="right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    prefix = eisenstein_successor_row_split_prefix("p", "q", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc", "l", tag="closed")
    assert set(parse_formula_with_names(prefix)[1]) == {"p", "q", "h", "sh", "bb", "bc", "db", "dc", "tb", "tc", "l"}


def test_fubini_row_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all(fragment not in command for command in commands for fragment in ("DNE", "by_contra", "classical", "sorry"))


def test_fubini_row_bodies_kernel_check_within_laptop_limit() -> None:
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
    print(f"EISENSTEIN FUBINI ROW BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}", flush=True)
