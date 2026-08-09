"""Focused kernel and mutation audit for Bertrand power-growth candidates."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, Imp, Term, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED = {
    "one_le_pow": (
        2_501,
        "52c15a620b3303df1dd639722843445b568cd9587e53556acde3522cc0166a05",
        (
            "pow_zero",
            "pow_successor_decompose",
            "le_refl",
            "le_mul_of_one_le_right",
            "le_trans",
        ),
        (5, 46, 61, 22, 61, 60, 0),
        (4_049, 65, 1_115, 1_163, 49, "f415fa38a01c807fe2f5a9d9600bee57c111bf6b6f74e062357a80323135ab21"),
    ),
    "pow_nonzero_of_one_le": (
        2_460,
        "0cfed99b44eeebba9e89ae38dac56cf5769114b989d4b5f96512c4c65d4f2899",
        ("one_le_pow", "ne_zero_of_one_le"),
        (2, 17, 21, 16, 21, 20, 0),
        (4_091, 66, 1_157, 1_205, 49, "ca8b41130a4aa2b649988c3a4ec99b63920c7012d0aaf829caa2deaf1ca03245"),
    ),
    "pow_exponent_monotone": (
        5_489,
        "d75f9fad0d708e8ead82ded1b89de60a49fb47b3e6e9a866289019c63837c5af",
        (
            "pow_exists",
            "pow_add",
            "one_le_pow",
            "le_mul_of_one_le_right",
            "add_comm",
        ),
        (5, 47, 55, 30, 55, 54, 0),
        (70_898, 89, 5_818, 6_082, 265, "48da5c03f5fcdd7613146f1dc7128fea9ccb8c273f12508fe26f85419bd695a2"),
    ),
}


@lru_cache(maxsize=1)
def _order_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_order_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_growth_candidate_theorems(TheoremSpec)


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for field in fields(proof)
        if isinstance((child := getattr(proof, field.name)), Proof)
    )


def _walk_proof(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
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
        for field in fields(node):
            value = getattr(node, field.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _local() -> dict[str, TheoremSpec]:
    items = (*_order_specs(), *_specs())
    assert len({item.name for item in items}) == len(items)
    return {item.name: item for item in items}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    public = _specs_by_name()
    local = _local()
    if name in local:
        assert name not in public
        item = local[name]
    else:
        checked = replay(name)
        return checked.formula, checked.certificate
    available = _available()
    formula = _closed_formula(item.statement)
    target = formula
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)

    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    closed = checked_final(state, target)

    for dependency in item.dependencies:
        assert type(closed) is ImpIntro
        closed = closed.body
    dependency_proofs = tuple(_close(dependency) for dependency in item.dependencies)
    for dependency_formula, dependency_proof in reversed(dependency_proofs):
        closed = Cut(dependency_formula, formula, dependency_proof, closed)

    assert check((), closed, formula)
    return formula, closed


def test_bertrand_power_growth_surface_is_frozen_native_and_topological() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert len({item.name for item in specs}) == len(specs)
    assert not ({item.name for item in specs} & set(_specs_by_name()))
    assert not ({item.name for item in specs} & {item.name for item in _order_specs()})

    available = set(_specs_by_name()) | {item.name for item in _order_specs()}
    for item in specs:
        length, digest, dependencies, _body, _closed = EXPECTED[item.name]
        assert len(item.statement) == length
        assert sha256(item.statement.encode()).hexdigest() == digest
        assert item.dependencies == dependencies
        assert all(dependency in available for dependency in dependencies)
        available.add(item.name)
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            marker not in item.statement
            for marker in ("Pow(", "Le(", "<", "<=", "^", "DNE")
        )


def test_bertrand_power_growth_bodies_kernel_check_constructively() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item for item in _order_specs()
    }
    receipts = replay_candidate_bodies(_specs(), core=core)
    for receipt in receipts:
        assert (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        ) == EXPECTED[receipt.name][3]


def test_bertrand_power_growth_every_direct_dependency_is_live() -> None:
    for item in _specs():
        for dependency in item.dependencies:
            mutated = replace(
                item,
                dependencies=tuple(
                    name for name in item.dependencies if name != dependency
                ),
            )
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((mutated,), core=_available())


def test_bertrand_power_growth_false_conclusions_are_rejected() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item for item in _order_specs()
    }
    for item in _specs():
        mutated = replace(item, statement=f"({item.statement}) /\\ false")
        mutated_specs = tuple(
            mutated if candidate.name == item.name else candidate
            for candidate in _specs()
        )
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(mutated_specs, core=core)


def test_bertrand_power_growth_closes_without_dne_within_live_limits() -> None:
    for item in _specs():
        formula, certificate = _close(item.name)
        assert check((), certificate, formula)
        assert not any(type(node) is DNE for node in _walk_proof(certificate))
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        assert nodes <= MAX_LIVE_PROOF_NODES
        assert depth <= MAX_LIVE_PROOF_DEPTH
        assert objects <= MAX_LIVE_PROOF_OBJECTS
        expected_nodes, expected_depth, expected_objects, expected_edges, expected_reused, digest = EXPECTED[item.name][4]
        assert (nodes, depth, objects, edges, reused) == (
            expected_nodes,
            expected_depth,
            expected_objects,
            expected_edges,
            expected_reused,
        )
        assert _proof_dag_digest(certificate) == digest


def test_bertrand_power_growth_orientation_matches_standard_naturals() -> None:
    for base in range(1, 7):
        for exponent in range(7):
            assert 1 <= base**exponent
            assert base**exponent != 0
            for larger_exponent in range(exponent, 7):
                assert base**exponent <= base**larger_exponent
