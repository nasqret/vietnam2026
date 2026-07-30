"""Focused native-body audit for Euler scaled-prefix extensionality."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.euler_scaled_inverse_candidate import (
    make_euler_scaled_inverse_candidate_theorems,
)
from peano_lab.library.euler_scaled_inverse_prefix_candidate import (
    make_euler_scaled_inverse_prefix_candidate_theorems,
)
from peano_lab.library.euler_scaled_inverse_prefix_extensional_candidate import (
    make_euler_scaled_inverse_prefix_extensional_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "scaled_inverse_prefix_entry_sound",
    "scaled_inverse_prefix_extensional",
    "scaled_inverse_prefix_no_fixed_of_not_qres",
    "scaled_inverse_prefix_mate_predecessor",
    "scaled_inverse_prefix_involutive",
    "scaled_inverse_prefix_injective",
)

EXPECTED_DEPENDENCIES = {
    "scaled_inverse_prefix_entry_sound": ("beta_at_unique",),
    "scaled_inverse_prefix_extensional": ("prime_scaled_inverse_unique",),
    "scaled_inverse_prefix_no_fixed_of_not_qres": (
        "scaled_inverse_prefix_entry_sound",
        "scaled_inverse_no_fixed_of_not_qres",
    ),
    "scaled_inverse_prefix_mate_predecessor": (
        "scaled_inverse_prefix_entry_sound",
        "nonzero_is_succ",
        "le_of_succ_le_succ",
    ),
    "scaled_inverse_prefix_involutive": (
        "scaled_inverse_prefix_mate_predecessor",
        "scaled_inverse_prefix_entry_sound",
        "scaled_inverse_symmetric",
        "scaled_inverse_prefix_extensional",
    ),
    "scaled_inverse_prefix_injective": (
        "scaled_inverse_prefix_entry_sound",
        "scaled_inverse_symmetric",
        "prime_scaled_inverse_unique",
        "succ_injective",
    ),
}

EXPECTED_HASHES = {
    "scaled_inverse_prefix_entry_sound": "f54fefd85c24c0384bb19a72ce04a6514b7e83ee14cae91d1085333596fba811",
    "scaled_inverse_prefix_extensional": "1fbd10fd9efa4fb5539daa419d56cdca4f9f3c3dc3d55309766c550fffed4fd2",
    "scaled_inverse_prefix_no_fixed_of_not_qres": "da9e726057ba11b9c5e407aea52b417e2e28a17f4eae14f6826795a3f04ff9c0",
    "scaled_inverse_prefix_mate_predecessor": "9e453da31a2510e8d546238ac657f8f57b38992abcf87a7e338642c53a4e5493",
    "scaled_inverse_prefix_involutive": "eafe66cac1fa35ae0842526a60e6cf262af6b2cef855c5dd2850181d368d18dd",
    "scaled_inverse_prefix_injective": "9cc9fc93045d05693e401a0a930d1b08b8756171d318c39287e7f63aa7480c67",
}

EXPECTED_METRICS = {
    "scaled_inverse_prefix_entry_sound": (58, 25, 58, 57, 0, 30),
    "scaled_inverse_prefix_extensional": (54, 26, 54, 53, 0, 33),
    "scaled_inverse_prefix_no_fixed_of_not_qres": (36, 27, 36, 35, 0, 31),
    "scaled_inverse_prefix_mate_predecessor": (67, 36, 67, 66, 0, 44),
    "scaled_inverse_prefix_involutive": (91, 39, 91, 90, 0, 77),
    "scaled_inverse_prefix_injective": (77, 36, 77, 76, 0, 71),
}


def _specs() -> tuple[TheoremSpec, ...]:
    return make_euler_scaled_inverse_prefix_extensional_candidate_theorems(
        TheoremSpec
    )


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _cpu_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Euler prefix extensional replay exceeded {seconds}s CPU")

    previous = signal.signal(signal.SIGPROF, expired)
    signal.setitimer(signal.ITIMER_PROF, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.signal(signal.SIGPROF, previous)


def _core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_euler_scaled_inverse_candidate_theorems,
        make_euler_scaled_inverse_prefix_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            assert item.name not in core
            core[item.name] = item
    return core


@lru_cache(maxsize=1)
def _receipts():
    specs = _specs()
    local = {item.name: item for item in specs}
    core = _core()
    rows = []
    with _cpu_deadline(60):
        for item in specs:
            target = _closed_formula(item.statement)
            for name in reversed(item.dependencies):
                dependency = local.get(name) or core[name]
                target = Imp(_closed_formula(dependency.statement), target)
            state = start(target)
            for name in item.dependencies:
                state = apply_tactic(state, "intro", name)
            for command in item.script:
                tactic, arguments = _primitive(command)
                state = apply_tactic(state, tactic, arguments)
            certificate = checked_final(state, target)
            assert check((), certificate, target)
            assert not any(type(node) is DNE for node in _walk(certificate))
            nodes, depth = proof_metrics(certificate)
            objects, edges, reused = proof_identity_metrics(certificate)
            rows.append(
                (item.name, nodes, depth, objects, edges, reused, len(item.script))
            )
    return tuple(rows)


def test_euler_prefix_extensional_contract_is_exact_and_isolated() -> None:
    first = _specs()
    assert _specs() == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_HASHES
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_euler_prefix_extensional_statements_are_closed_native_pa() -> None:
    forbidden = ("BetaAt(", "Prime(", "QRes(", "ScaledInverse(", "%", "∣")
    for item in _specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    involution = _specs()[-2].statement
    assert "exists j. y = S j" in involution
    assert "S i" in involution


def test_euler_prefix_extensional_dependencies_are_ordered_and_constructive() -> None:
    local_seen: set[str] = set()
    core = _core()
    for item in _specs():
        assert all(name in core or name in local_seen for name in item.dependencies)
        local_seen.add(item.name)
        assert all("DNE" not in command for command in item.script)


def test_euler_prefix_extensional_bodies_are_kernel_green_and_bounded() -> None:
    rows = _receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:] for row in rows} == EXPECTED_METRICS
