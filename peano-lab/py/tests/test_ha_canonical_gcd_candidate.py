"""Focused native-body audit for the canonical relational-gcd package."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    Imp,
    parse_formula,
    parse_formula_in_context,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.defined_syntax import parse_defined_formula_in_context
from peano_lab.library.ha_canonical_gcd_candidate import (
    is_gcd,
    make_ha_canonical_gcd_candidate_theorems,
    unique_gcd,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "canonical_gcd_exists",
    "canonical_gcd_functional",
    "canonical_gcd_exists_unique",
)
EXPECTED_DEPENDENCIES = {
    "canonical_gcd_exists": ("gcd_exists_relational",),
    "canonical_gcd_functional": ("is_gcd_unique",),
    "canonical_gcd_exists_unique": (
        "canonical_gcd_exists",
        "canonical_gcd_functional",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "canonical_gcd_exists":
        "d1264e3b8759b991bb02db9b764c0a8671da6a9199d2585cbbb96d5e0d9eff4d",
    "canonical_gcd_functional":
        "a14d92bb096070ab10132a6d095af01b1decc8a3437ca72f28cb9bf4e3d5036e",
    "canonical_gcd_exists_unique":
        "05fd381ea8bf40b071f47365e9ebd5ba3e409bbf588699a60b17e04d073517fb",
}
EXPECTED_BODY_RECEIPTS = {
    "canonical_gcd_exists": (1, 5, 12, 8, 12, 11, 0),
    "canonical_gcd_functional": (1, 13, 28, 18, 28, 27, 0),
    "canonical_gcd_exists_unique": (2, 19, 22, 16, 22, 21, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "canonical_gcd_exists": (
        1_280,
        47,
        845,
        892,
        48,
        36,
        "8e3b24c937725618f58d1fddaf36bac33d4ce5f16ae1f3f5da4e254763468350",
    ),
    "canonical_gcd_functional": (
        708,
        35,
        589,
        623,
        35,
        20,
        "7cca97c44c84e4b6331820e98da8d81abefb67a2861e04318f30b1afb375a51f",
    ),
    "canonical_gcd_exists_unique": (
        2_010,
        48,
        1_255,
        1_326,
        72,
        55,
        "20db8565558e7d08e343c4b168dde040f5ecea0479257fd10f0024d13a901b3a",
    ),
}


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_canonical_gcd_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


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


def _cold_closed_receipts() -> dict[str, tuple[int, int, int, int, int, int, str]]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    public = _specs_by_name()

    @lru_cache(maxsize=None)
    def close(name: str):
        if name in public:
            checked = replay(name)
            return checked.formula, checked.certificate

        item = local[name]
        formula = _closed_formula(item.statement)
        dependency_specs = tuple(
            local.get(dependency) or public[dependency]
            for dependency in item.dependencies
        )
        target = formula
        for dependency_spec in reversed(dependency_specs):
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in item.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
        for dependency in item.dependencies:
            assert type(body) is ImpIntro, (
                f"{item.name} did not expose dependency {dependency}"
            )
            body = body.body
        for dependency in reversed(item.dependencies):
            dependency_formula, dependency_certificate = close(dependency)
            body = Cut(
                dependency_formula,
                formula,
                dependency_certificate,
                body,
            )
        assert check((), body, formula)
        return formula, body

    receipts = {}
    for item in specs:
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        assert check((), certificate, formula)
        unique_nodes = tuple(_walk_unique(certificate))
        assert not any(type(node) is DNE for node in unique_nodes)
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        assert objects == len(unique_nodes)
        receipts[item.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in unique_nodes),
            _proof_dag_digest(certificate),
        )
    return receipts


def test_canonical_gcd_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_canonical_gcd_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    assert "gcd_exists_relational" in public
    assert "is_gcd_unique" in public
    assert first[0].dependencies == ("gcd_exists_relational",)
    assert first[1].dependencies == ("is_gcd_unique",)
    assert all(name not in public for name in first[2].dependencies)


def test_canonical_gcd_surfaces_are_hygienic_and_definition_exact() -> None:
    left = is_gcd("g", "a", "b", tag="alpha_left")
    right = is_gcd("g", "a", "b", tag="alpha_right")

    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"g", "a", "b"}
    assert parse_formula_in_context(left, ["g", "a", "b"]) == (
        parse_defined_formula_in_context("IsGCD(g,a,b)", ["g", "a", "b"])
    )

    unique_left = unique_gcd("a", "b", tag="alpha_left")
    unique_right = unique_gcd("a", "b", tag="alpha_right")
    assert unique_left != unique_right
    assert parse_formula(unique_left) == parse_formula(unique_right)
    _, unique_free_names = parse_formula_with_names(unique_left)
    assert set(unique_free_names) == {"a", "b"}
    assert "forall hag_comparison_alpha_left" in unique_left
    assert "hag_comparison_alpha_left = hag_chosen_alpha_left" in unique_left

    for surface in (left, unique_left):
        assert all(
            token not in surface
            for token in (
                "IsGCD(",
                "Dvd(",
                "GCD(",
                "Unique(",
                "exists unique",
                "%",
                "<",
                "<=",
            )
        )

    with pytest.raises(ValueError, match="Peano identifier"):
        is_gcd("g + 1", "a", "b", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        unique_gcd("a", "b", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        is_gcd("hag_left_factor_capture", "a", "b", tag="capture")
    with pytest.raises(ValueError, match="captures an argument"):
        unique_gcd("hag_chosen_capture", "b", tag="capture")


def test_canonical_gcd_contracts_are_closed_and_mathematically_strong() -> None:
    existence, functionality, packaged = _candidate_specs()
    for item in (existence, functionality, packaged):
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "IsGCD(",
                "Dvd(",
                "GCD(",
                "Unique(",
                "exists unique",
                "%",
                "<",
                "<=",
            )
        )

    assert existence.statement.startswith("forall a b. exists g.")
    assert functionality.statement.startswith("forall a b g h.")
    assert functionality.statement.endswith("-> g = h")
    assert packaged.statement.startswith("forall a b. (exists hag_chosen_package.")
    assert "forall hag_comparison_package." in packaged.statement
    assert packaged.statement.endswith(
        "-> hag_comparison_package = hag_chosen_package))"
    )
    assert not any(
        premise in item.statement
        for item in (existence, functionality, packaged)
        for premise in ("~(a = 0)", "~(b = 0)")
    )


def test_canonical_gcd_bodies_are_constructive_exact_and_mutation_sensitive() -> None:
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

    forbidden_tactics = {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
    commands = tuple(command for item in specs for command in item.script)
    assert all(command.split(maxsplit=1)[0] not in forbidden_tactics for command in commands)
    assert all(
        "DNE" not in command and "classical" not in command and "sorry" not in command
        for command in commands
    )

    mutations = {
        "canonical_gcd_exists": lambda statement: statement.replace(
            "b = g * hag_right_factor_existence",
            "S b = g * hag_right_factor_existence",
            1,
        ),
        "canonical_gcd_functional": lambda statement: statement.removesuffix(
            "g = h"
        ) + "S g = h",
        "canonical_gcd_exists_unique": lambda statement: statement.removesuffix(
            "hag_comparison_package = hag_chosen_package))"
        ) + "S hag_comparison_package = hag_chosen_package))",
    }
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_canonical_gcd_empty_context_closure_is_deterministic_and_constructive() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()

    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
