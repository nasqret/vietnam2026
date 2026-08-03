"""Focused strict-HA audit for the signed-code parity prerequisites."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_signed_parity_candidate import (
    make_ha_signed_parity_candidate_theorems,
)
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "even_odd_exclusive_k1",
    "even_half_unique",
)
EXPECTED_DEPENDENCIES = {
    "even_odd_exclusive_k1": ("zero_or_succ",),
    "even_half_unique": ("mul_left_cancel_nonzero",),
}
EXPECTED_STATEMENT_SHA256 = {
    "even_odd_exclusive_k1":
        "d46a72512d65b2053572326b93f2c0279e8fdea4b08abd542f8fe22e4e66808f",
    "even_half_unique":
        "ed519f4aef419a494c3784ca94560e4027d41e4439621a17adcde6b2e2093037",
}
EXPECTED_BODY_RECEIPTS = {
    "even_odd_exclusive_k1": (1, 38, 72, 20, 72, 71, 0),
    "even_half_unique": (1, 18, 21, 12, 21, 20, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "even_odd_exclusive_k1": (
        80,
        20,
        80,
        79,
        0,
        1,
        "d2ebac65fdad664fd883d467a6482b47be819c05fc39d928a91e4980f0b3a3f9",
    ),
    "even_half_unique": (
        245,
        24,
        198,
        198,
        1,
        7,
        "03df34e8e967b1b25e14a19461baeb44dec25a185a16d12eb72ffa8d17438fda",
    ),
}
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_eq_zero_right",
    "add_right_cancel",
    "mul_eq_zero",
    "mul_left_cancel_nonzero",
    "mul_ne_zero",
    "succ_ne_zero",
    "zero_or_succ",
}
FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_parity_candidate_theorems(TheoremSpec)


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk(proof: Proof):
    yield proof
    for child in _proof_children(proof):
        yield from _walk(child)


def _walk_unique(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(_proof_children(node))


def _proof_dag_digest(proof: Proof) -> str:
    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = _proof_children(node)
        if not expanded:
            pending.append((node, True))
            pending.extend(
                (child, False) for child in children if id(child) not in digests
            )
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | {
        item.name: item for item in _candidate_specs()
    }


def _curried_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency_name in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency_name].statement), target)
    return target


def _body_certificate(item: TheoremSpec):
    target = _curried_target(item)
    state = start(target)
    for dependency_name in item.dependencies:
        state = apply_tactic(state, "intro", dependency_name)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _transitive_public_dependencies() -> set[str]:
    public = _specs_by_name()
    pending = [
        dependency
        for item in _candidate_specs()
        for dependency in item.dependencies
    ]
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        assert name in public, f"candidate dependency {name!r} is not public"
        seen.add(name)
        pending.extend(public[name].dependencies)
    return seen


def _cold_closed_receipts() -> dict[str, tuple[int, int, int, int, int, int, str]]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    public = _specs_by_name()
    receipts = {}

    for item in _candidate_specs():
        formula = _closed_formula(item.statement)
        body, target = _body_certificate(item)
        assert target == _curried_target(item)
        for dependency in item.dependencies:
            assert type(body) is ImpIntro, (
                f"{item.name} did not expose dependency {dependency}"
            )
            body = body.body
        for dependency in reversed(item.dependencies):
            dependency_formula = _closed_formula(public[dependency].statement)
            checked_dependency = replay(dependency)
            assert checked_dependency.formula == dependency_formula
            body = Cut(
                dependency_formula,
                formula,
                checked_dependency.certificate,
                body,
            )
        assert check((), body, formula)
        unique_nodes = tuple(_walk_unique(body))
        assert not any(type(node) is DNE for node in unique_nodes)
        nodes, depth = proof_metrics(body)
        objects, edges, reused = proof_identity_metrics(body)
        assert objects == len(unique_nodes)
        receipts[item.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in unique_nodes),
            _proof_dag_digest(body),
        )
    return receipts


def test_signed_parity_factory_is_exact_ordered_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_parity_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_parity_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_parity_contracts_are_exact_closed_base_ha_formulas() -> None:
    separation, uniqueness = _candidate_specs()
    assert separation.statement == (
        "forall n even_half odd_half. n = 2 * even_half -> "
        "n = 2 * odd_half + 1 -> false"
    )
    assert uniqueness.statement == (
        "forall n a b. n = 2 * a -> n = 2 * b -> a = b"
    )

    for item in (separation, uniqueness):
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "Even(",
                "Odd(",
                "DivRem(",
                "BetaAt(",
                "ModEq(",
                "%",
                "<",
                "<=",
            )
        )


def test_signed_parity_dependencies_are_transitively_k1_only() -> None:
    public = _specs_by_name()
    closure = _transitive_public_dependencies()

    assert closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert "even_odd_exclusive_pointwise" not in closure
    assert "division_remainder_unique" not in closure
    for name in closure:
        item = public[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_signed_parity_bodies_are_constructive_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    receipts = replay_candidate_bodies(specs, core=dict(_specs_by_name()))
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

    forbidden_tactics = {
        "auto",
        "compact_arith",
        "norm_num",
        "ring",
        "simp",
        "use",
    }
    commands = tuple(command for item in specs for command in item.script)
    assert all(
        command.split(maxsplit=1)[0] not in forbidden_tactics
        for command in commands
    )
    assert all(
        marker not in command.lower()
        for command in commands
        for marker in ("classical", "dne", "sorry")
    )

    mutations = {
        "even_odd_exclusive_k1": lambda statement: statement.replace(
            "2 * odd_half + 1",
            "2 * odd_half + 2",
        ),
        "even_half_unique": lambda statement: statement.removesuffix(
            "a = b"
        ) + "S a = b",
    }
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_signed_parity_empty_context_closure_is_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()

    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
