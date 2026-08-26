"""Focused body audit for the quadratic-residue half of Euler's criterion."""

from __future__ import annotations

import signal
from dataclasses import fields
from hashlib import sha256

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.euler_criterion_residue_candidate import (
    make_euler_criterion_residue_candidate_theorems,
)
from peano_lab.library.fermat_endpoints_candidate import (
    make_fermat_endpoint_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "mod_eq_zero_to_dvd_nonzero",
    "quadratic_residue_half_power_mod_one",
)
EXPECTED_DEPENDENCIES = {
    "mod_eq_zero_to_dvd_nonzero": (
        "nonzero_is_succ",
        "mod_eq_to_remainder_decomposition",
        "mul_comm",
    ),
    "quadratic_residue_half_power_mod_one": (
        "mod_eq_zero_to_dvd_nonzero",
        "prime_nonzero",
        "multiple_mul_right",
        "dvd_to_mod_zero",
        "mod_eq_symm",
        "mod_eq_trans",
        "pow_exists",
        "pow_two",
        "pow_mul_exp",
        "fermat_predecessor_exponent_mod_one",
        "pow_mod_congruent",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "mod_eq_zero_to_dvd_nonzero": (
        "39876f761006c1db06c8e77cd6b655a7e05f199e75cd6df89942e1d573ffcfc6"
    ),
    "quadratic_residue_half_power_mod_one": (
        "36402b13cdcf0d5fc7c7f4566166ca43c2c9f733bcbc84bdca59b350b14b905b"
    ),
}
EXPECTED_BODY_METRICS = {
    "mod_eq_zero_to_dvd_nonzero": (48, 18, 47, 47, 1, 30),
    "quadratic_residue_half_power_mod_one": (148, 39, 148, 147, 0, 136),
}
_BODY_DEADLINE_SECONDS = 60


def _specs() -> tuple[TheoremSpec, ...]:
    return make_euler_criterion_residue_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _body_certificates():
    specs = _specs()
    local = {item.name: item for item in specs}
    core = dict(_specs_by_name())
    core.update(
        (item.name, item)
        for item in make_fermat_endpoint_candidate_theorems(TheoremSpec)
    )
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


def test_euler_residue_factory_is_exact_and_isolated() -> None:
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


def test_euler_residue_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "Dvd(",
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
    for item in _specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    zero_bridge, residue_branch = _specs()
    assert zero_bridge.statement.startswith("forall p a. ~(p = 0) ->")
    assert zero_bridge.statement.endswith("exists k. a = p * k")
    assert residue_branch.statement.startswith(
        "forall p h a A. p = 2 * h + 1 ->"
    )
    assert "exists qr_x_euler_residue" in residue_branch.statement
    assert "exists ff_b_euler_residue_half" in residue_branch.statement


def test_euler_residue_scripts_use_no_classical_escape() -> None:
    commands = tuple(command for item in _specs() for command in item.script)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_euler_residue_bodies_are_constructive_and_bounded() -> None:
    def expired(_signum, _frame):
        raise TimeoutError("Euler residue body replay exceeded 60s")

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
            "EULER RESIDUE BODY RECEIPT "
            f"name={item.name} nodes={nodes} depth={depth} "
            f"objects={objects} edges={edges} reused={reused} "
            f"commands={len(item.script)}",
            flush=True,
        )
    assert observed == EXPECTED_BODY_METRICS
