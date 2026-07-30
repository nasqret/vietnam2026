"""Focused native-body audit for Wilson endpoint restoration."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)
from peano_lab.library.wilson_endpoint_restoration_candidate import (
    _factorial_term,
    _range_prefix_term,
    make_wilson_endpoint_restoration_candidate_theorems,
)
from peano_lab.library.wilson_inverse_prefix_candidate import (
    make_wilson_inverse_prefix_candidate_theorems,
)
from peano_lab.library.wilson_terminal_product_candidate import (
    make_wilson_terminal_product_candidate_theorems,
)


EXPECTED_NAMES = (
    "factorial_one_value",
    "beta_range_two_product_is_factorial_succ",
    "beta_range_two_product_restore_last",
    "mod_one_product_restore_predecessor",
    "prime_two_or_terminal_odd_shape",
    "prime_terminal_range_two_product_mod_one_exists",
    "prime_factorial_wilson_congruence",
)

EXPECTED_DEPENDENCIES = {
    "factorial_one_value": (
        "factorial_succ_decompose",
        "factorial_zero",
        "mul_one",
    ),
    "beta_range_two_product_is_factorial_succ": (
        "factorial_one_value",
        "beta_product_zero",
        "beta_product_succ_decompose",
        "beta_range_entry_eq",
        "factorial_exists",
        "factorial_succ_decompose",
        "factorial_functional",
        "le_succ",
        "le_refl",
        "add_succ_left",
        "zero_add",
        "mul_congr",
    ),
    "beta_range_two_product_restore_last": (
        "beta_range_two_product_is_factorial_succ",
        "factorial_succ_decompose",
        "factorial_functional",
        "mul_congr",
    ),
    "mod_one_product_restore_predecessor": ("mod_eq_mul_right", "one_mul"),
    "prime_two_or_terminal_odd_shape": (
        "eq_decidable",
        "prime_ne_two_is_odd",
        "nonzero_is_succ",
        "mul_succ_left",
        "mul_zero_left",
        "zero_add",
        "add_succ_left",
        "add_assoc",
        "add_comm",
    ),
    "prime_terminal_range_two_product_mod_one_exists": (
        "prime_inverse_prefix_exists",
        "prime_wilson_terminal_product_package_exists",
    ),
    "prime_factorial_wilson_congruence": (
        "prime_two_or_terminal_odd_shape",
        "succ_injective",
        "factorial_one_value",
        "mod_eq_refl",
        "prime_terminal_range_two_product_mod_one_exists",
        "beta_range_two_product_restore_last",
        "mod_one_product_restore_predecessor",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "factorial_one_value": (
        "c74bba0e52f8c7af575d467dcd6f35f0283c3132e5bb60171cd0b21404d28b47"
    ),
    "beta_range_two_product_is_factorial_succ": (
        "e38e20d59ad1fee544cab0dd135372e0be5f1835c205de7b4f13a35d81621220"
    ),
    "beta_range_two_product_restore_last": (
        "625e8efa35d787f91c4424b88af53d674d57bdd8341231622722d3c47d5eebf2"
    ),
    "mod_one_product_restore_predecessor": (
        "b93a58a2b881d2fbce8a763fee62831fa4d3fc56a443484099ed232698f65687"
    ),
    "prime_two_or_terminal_odd_shape": (
        "07f8821d53585752c65f52c449df341cd6794059a374d6bdae5a2c479e1b5c0d"
    ),
    "prime_terminal_range_two_product_mod_one_exists": (
        "5bab0e70859889caf0728454858c2c9d012a528b93e70d82f4cb8b2d383944c6"
    ),
    "prime_factorial_wilson_congruence": (
        "e8e28d505ac0981c1ee059704a373abf8f9264dbbce83bed358390e0f433acf0"
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "factorial_one_value": (3, 25, 30, 15, 30, 29, 0),
    "beta_range_two_product_is_factorial_succ": (
        12,
        115,
        258,
        45,
        257,
        257,
        1,
    ),
    "beta_range_two_product_restore_last": (4, 45, 63, 29, 63, 62, 0),
    "mod_one_product_restore_predecessor": (2, 19, 21, 16, 21, 20, 0),
    "prime_two_or_terminal_odd_shape": (9, 36, 104, 30, 99, 103, 5),
    "prime_terminal_range_two_product_mod_one_exists": (
        2,
        57,
        94,
        35,
        94,
        93,
        0,
    ),
    "prime_factorial_wilson_congruence": (7, 77, 110, 31, 110, 109, 0),
}

_BODY_CPU_LIMIT_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_wilson_endpoint_restoration_candidate_theorems(TheoremSpec)


def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_wilson_inverse_prefix_candidate_theorems,
        make_wilson_terminal_product_candidate_theorems,
    ):
        core.update((item.name, item) for item in factory(TheoremSpec))
    return core


def _walk(proof: Proof):
    pending = [proof]
    while pending:
        node = pending.pop()
        yield node
        pending.extend(
            child
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )


@contextmanager
def _cpu_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Wilson endpoint replay exceeded {seconds}s CPU")

    previous_handler = signal.signal(signal.SIGPROF, expired)
    previous_timer = signal.getitimer(signal.ITIMER_PROF)
    signal.setitimer(signal.ITIMER_PROF, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.signal(signal.SIGPROF, previous_handler)
        if previous_timer != (0.0, 0.0):
            signal.setitimer(signal.ITIMER_PROF, *previous_timer)


def _dependency_curried_rows():
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    core = _explicit_dependency_core()
    rows = []

    with _cpu_deadline(_BODY_CPU_LIMIT_SECONDS):
        for item in specs:
            formula = _closed_formula(item.statement)
            target = formula
            for dependency_name in reversed(item.dependencies):
                dependency = local.get(dependency_name) or core[dependency_name]
                target = Imp(_closed_formula(dependency.statement), target)

            state = start(target)
            for dependency_name in item.dependencies:
                state = apply_tactic(state, "intro", dependency_name)
            for command in item.script:
                tactic, arguments = _primitive(command)
                state = apply_tactic(state, tactic, arguments)

            certificate = checked_final(state, target)
            assert check((), certificate, target)
            assert not any(type(node) is DNE for node in _walk(certificate))
            nodes, depth = proof_metrics(certificate)
            objects, edges, reused = proof_identity_metrics(certificate)
            rows.append(
                (
                    item.name,
                    len(item.dependencies),
                    len(item.script),
                    nodes,
                    depth,
                    objects,
                    edges,
                    reused,
                )
            )
    return tuple(rows)


def test_wilson_endpoint_contracts_are_exact_ordered_and_isolated() -> None:
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
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "wilson_endpoint_restoration_candidate" not in registry_source


def test_wilson_endpoint_helpers_and_contracts_are_hygienic_native_pa() -> None:
    range_left = _range_prefix_term(
        "b",
        "c",
        "2",
        "S l",
        tag="endpoint_audit_range_left",
        avoid=("b", "c", "l"),
    )
    range_right = _range_prefix_term(
        "b",
        "c",
        "2",
        "S l",
        tag="endpoint_audit_range_right",
        avoid=("b", "c", "l"),
    )
    assert range_left != range_right
    assert parse_formula(range_left) == parse_formula(range_right)
    _, range_free = parse_formula_with_names(range_left)
    assert set(range_free) == {"b", "c", "l"}

    factorial_left = _factorial_term(
        "S l", "P", tag="endpoint_audit_factorial_left", avoid=("l", "P")
    )
    factorial_right = _factorial_term(
        "S l", "P", tag="endpoint_audit_factorial_right", avoid=("l", "P")
    )
    assert factorial_left != factorial_right
    assert parse_formula(factorial_left) == parse_formula(factorial_right)
    _, factorial_free = parse_formula_with_names(factorial_left)
    assert set(factorial_free) == {"l", "P"}

    forbidden_surface_tokens = (
        "AdjacentUnitPairs(",
        "BetaAt(",
        "Factorial(",
        "InversePrefix(",
        "ModEq(",
        "PairOrderState(",
        "Prime(",
        "Product(",
        "Range(",
        "SuccessorLift(",
        "%",
        "^",
        "<",
        "∣",
        "≡",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden_surface_tokens)
        assert all("DNE" not in command for command in item.script)


def test_wilson_endpoint_bodies_are_constructive_within_process_cpu_cap() -> None:
    started = perf_counter()
    rows = _dependency_curried_rows()
    elapsed = perf_counter() - started
    observed = {row[0]: row[1:] for row in rows}
    assert observed == EXPECTED_BODY_RECEIPTS

    print(
        "WILSON ENDPOINT BODY RECEIPTS "
        f"elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
