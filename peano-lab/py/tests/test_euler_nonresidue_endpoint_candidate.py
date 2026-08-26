"""Focused constructive audit for Euler's nonresidue endpoint."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.euler_nonresidue_endpoint_candidate import (
    make_euler_nonresidue_endpoint_candidate_theorems,
)
from peano_lab.library.euler_pair_product_candidate import (
    make_euler_pair_product_candidate_theorems,
)
from peano_lab.library.euler_scaled_inverse_prefix_candidate import (
    make_euler_scaled_inverse_prefix_candidate_theorems,
)
from peano_lab.library.euler_scaled_pair_order_iteration_candidate import (
    make_euler_scaled_pair_order_iteration_candidate_theorems,
)
from peano_lab.library.fermat_residue_map_candidate import (
    make_fermat_residue_map_candidate_theorems,
)
from peano_lab.library.finite_factorial_theorems import (
    make_finite_factorial_theorems,
)
from peano_lab.library.finite_product_reindex_candidate import (
    make_finite_product_reindex_candidate,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)
from peano_lab.library.wilson_endpoint_restoration_candidate import (
    make_wilson_endpoint_restoration_candidate_theorems,
)
from peano_lab.library.wilson_pair_order_paired_iteration_candidate import (
    make_wilson_pair_order_paired_iteration_candidate_theorems,
)


EXPECTED_NAMES = (
    "scaled_pair_order_successor_lift_adjacent_targets",
    "scaled_pair_order_successor_lift_product_is_factorial",
    "scaled_pair_order_terminal_power_mod_predecessor",
    "scaled_inverse_nonresidue_half_power_mod_predecessor",
    "quadratic_nonresidue_half_power_mod_predecessor",
)

EXPECTED_DEPENDENCIES = {
    "scaled_pair_order_successor_lift_adjacent_targets": (
        "pair_index_left_below_double",
        "pair_index_right_below_double",
        "beta_at_unique",
    ),
    "scaled_pair_order_successor_lift_product_is_factorial": (
        "beta_at_unique",
        "beta_range_entry_eq",
        "beta_product_permutation_invariant",
        "add_succ_left",
        "zero_add",
    ),
    "scaled_pair_order_terminal_power_mod_predecessor": (
        "beta_successor_lift_exists",
        "scaled_pair_order_successor_lift_adjacent_targets",
        "beta_product_exists",
        "beta_adjacent_target_pairs_product_power",
        "factorial_exists",
        "scaled_pair_order_successor_lift_product_is_factorial",
        "prime_factorial_wilson_congruence",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
    "scaled_inverse_nonresidue_half_power_mod_predecessor": (
        "scaled_inverse_pair_order_terminal_package",
        "scaled_pair_order_terminal_power_mod_predecessor",
    ),
    "quadratic_nonresidue_half_power_mod_predecessor": (
        "prime_scaled_inverse_prefix_exists",
        "scaled_inverse_nonresidue_half_power_mod_predecessor",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "scaled_pair_order_successor_lift_adjacent_targets": (
        "8040e253937213b8a010dd9b8763be75ece23552c47db8ff5eb32472a77c3c51"
    ),
    "scaled_pair_order_successor_lift_product_is_factorial": (
        "45db8213a9d1bf3109dc7ae9b18b07967a7ee341c3c269a60e26d5fb8179286d"
    ),
    "scaled_pair_order_terminal_power_mod_predecessor": (
        "797d40d89cf76d0070c84312441a1ed634a54737fdf113df743758c31a8d8848"
    ),
    "scaled_inverse_nonresidue_half_power_mod_predecessor": (
        "4317a5b226c2fcf494f55015b8f9da4aa4f8f375ccead8b68156e0b00764e94f"
    ),
    "quadratic_nonresidue_half_power_mod_predecessor": (
        "f178c6c9bcc5a2976233a48fff70767159c88f6d9c771802277044e1115176af"
    ),
}

# dependency count, command count, nodes, depth, objects, edges, reuse
EXPECTED_BODY_RECEIPTS = {
    "scaled_pair_order_successor_lift_adjacent_targets": (
        3,
        115,
        132,
        39,
        132,
        131,
        0,
    ),
    "scaled_pair_order_successor_lift_product_is_factorial": (
        5,
        82,
        144,
        45,
        144,
        143,
        0,
    ),
    "scaled_pair_order_terminal_power_mod_predecessor": (
        9,
        114,
        136,
        52,
        136,
        135,
        0,
    ),
    "scaled_inverse_nonresidue_half_power_mod_predecessor": (
        2,
        46,
        61,
        34,
        61,
        60,
        0,
    ),
    "quadratic_nonresidue_half_power_mod_predecessor": (
        2,
        37,
        49,
        30,
        49,
        48,
        0,
    ),
}

_BODY_CPU_LIMIT_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_euler_nonresidue_endpoint_candidate_theorems(TheoremSpec)


def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_fermat_residue_map_candidate_theorems,
        make_finite_product_reindex_candidate,
        make_euler_pair_product_candidate_theorems,
        make_finite_factorial_theorems,
        make_wilson_endpoint_restoration_candidate_theorems,
        make_euler_scaled_pair_order_iteration_candidate_theorems,
        make_euler_scaled_inverse_prefix_candidate_theorems,
        make_wilson_pair_order_paired_iteration_candidate_theorems,
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
        raise TimeoutError(f"Euler nonresidue replay exceeded {seconds}s CPU")

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


@lru_cache(maxsize=1)
def _body_receipts():
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    core = _dependency_core()
    rows = []

    for item in specs:
        with _cpu_deadline(_BODY_CPU_LIMIT_SECONDS):
            target = _closed_formula(item.statement)
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


def test_euler_nonresidue_factory_is_exact_and_isolated() -> None:
    specs = _candidate_specs()
    assert _candidate_specs() == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "euler_nonresidue_endpoint_candidate" not in registry_source


def test_euler_nonresidue_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "AdjacentPairs(",
        "BetaAt(",
        "Factorial(",
        "ModEq(",
        "Pow(",
        "Prime(",
        "Product(",
        "QRes(",
        "%",
        "<",
        "∣",
        "≡",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    endpoint = _candidate_specs()[-1]
    assert endpoint.statement.startswith("forall p a n h A. p = S n ->")
    assert "~(a = 0)" in endpoint.statement
    assert "n = h + h" in endpoint.statement
    assert "exists qr_x_enr_nonresidue" in endpoint.statement
    assert "exists ff_b_enr_terminal_power" in endpoint.statement
    assert endpoint.statement.endswith(
        "(A) + p * wpp_mod_left_enr_terminal_result = "
        "(n) + p * wpp_mod_right_enr_terminal_result)"
    )


def test_euler_nonresidue_scripts_use_no_classical_escape() -> None:
    commands = tuple(
        command for item in _candidate_specs() for command in item.script
    )
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_euler_nonresidue_bodies_are_constructive_and_bounded() -> None:
    observed = {
        name: (dependencies, commands, nodes, depth, objects, edges, reused)
        for (
            name,
            dependencies,
            commands,
            nodes,
            depth,
            objects,
            edges,
            reused,
        ) in _body_receipts()
    }
    assert observed == EXPECTED_BODY_RECEIPTS

