"""Focused body audit for odd-half Eisenstein quotient bounds."""

from __future__ import annotations

import signal
from dataclasses import fields
from hashlib import sha256

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.eisenstein_quotient_bound_candidate import (
    make_eisenstein_quotient_bound_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "odd_half_cross_product_gap",
    "odd_half_division_quotient_bounded",
)
EXPECTED_DEPENDENCIES = {
    "odd_half_cross_product_gap": (
        "mul_add",
        "add_mul",
        "mul_assoc",
        "mul_comm",
        "add_assoc",
        "add_comm",
        "one_mul",
        "mul_one",
        "mul_succ_left",
    ),
    "odd_half_division_quotient_bounded": (
        "odd_half_cross_product_gap",
        "le_or_lt",
        "mul_le_mul_left",
        "le_add_right",
        "le_trans",
        "lt_not_le",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "odd_half_cross_product_gap": (
        "edd40ccb178f7f97678f3d5e4160130f13ef97d3959cf5a6d8426db77016e309"
    ),
    "odd_half_division_quotient_bounded": (
        "106939409f0f1886c5e84296289a6a65a05f52f9bab270a909cdbe3d32f89253"
    ),
}
EXPECTED_BODY_METRICS = {
    "odd_half_cross_product_gap": (160, 45, 144, 159, 16, 13),
    "odd_half_division_quotient_bounded": (67, 29, 67, 66, 0, 62),
}
_BODY_DEADLINE_SECONDS = 60


def _specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_quotient_bound_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _body_certificates():
    specs = _specs()
    local = {item.name: item for item in specs}
    core = _specs_by_name()
    rows = []
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
        rows.append((item, checked_final(state, target), target))
    return tuple(rows)


def test_quotient_bound_factory_is_exact_and_isolated() -> None:
    first = _specs()
    second = _specs()
    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_quotient_bound_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = ("DivRem(", "Floor(", "Prime(", "%", "<", "<=", "⌊")
    for item in _specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    gap, quotient = _specs()
    assert gap.statement.startswith("forall h k. (exists")
    assert "(2 * k + 1) * h" in gap.statement
    assert "(2 * h + 1) * S k" in gap.statement
    assert quotient.statement.startswith(
        "forall p q h k i d r. p = 2 * h + 1 -> q = 2 * k + 1 ->"
    )
    assert "q * S i = p * d + r" in quotient.statement
    assert "r = 0" not in quotient.statement
    assert "r) = p" not in quotient.statement


def test_quotient_bound_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _specs() for command in item.script)
    assert all(not command.startswith("ring") for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_quotient_bound_bodies_are_constructive_and_bounded() -> None:
    def expired(_signum, _frame):
        raise TimeoutError("Eisenstein quotient-bound replay exceeded 60s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, _BODY_DEADLINE_SECONDS)
    try:
        rows = _body_certificates()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)

    observed = {}
    for item, certificate, target in rows:
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        observed[item.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            len(item.script),
        )
        print(
            "EISENSTEIN QUOTIENT BOUND BODY RECEIPT "
            f"name={item.name} nodes={nodes} depth={depth} "
            f"objects={objects} edges={edges} reused={reused} "
            f"commands={len(item.script)}",
            flush=True,
        )
    assert observed == EXPECTED_BODY_METRICS
