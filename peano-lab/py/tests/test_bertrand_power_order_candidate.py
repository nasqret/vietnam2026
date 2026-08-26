"""Focused kernel and mutation audit for Bertrand power-order candidates."""

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
from peano_lab.kernel.formulas import Formula, Imp, Term, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
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
    "mul_le_mul": (
        203,
        "4fdfbe8aa9b250cc3e9854d76d39ee91f02ef017af4dddcce8b0a7774db3d00c",
        ("mul_le_mul_right", "mul_le_mul_left", "le_trans"),
        (3, 24, 27, 16, 27, 26, 0),
        (521, 27, 348, 380, 33, "614a64ac65162c3f5781e5c22df2924369dc60c78472bee6946a003cb1fcfe92"),
    ),
    "le_mul_of_one_le_right": (
        146,
        "584e0652e0149327135c578e570566ac80bb074a31b0faf9718b83778575b384",
        ("mul_le_mul_left", "mul_one"),
        (2, 12, 14, 11, 14, 13, 0),
        (141, 18, 130, 140, 11, "eb1094a91c04bb3e7cd960b7bd280f2a711f4f3efd61652d3d913b696cec5449"),
    ),
    "le_mul_of_one_le_left": (
        142,
        "44ee6ef882e766c5ffab36f55ea4a0a89cbc07077adcd3deb902a853dbcd6511",
        ("mul_le_mul_right", "one_mul"),
        (2, 12, 14, 11, 14, 13, 0),
        (383, 27, 316, 350, 35, "b56a189ac01d0b3cd21009723c773ffa5b5987989f053cda4a61154d324164e5"),
    ),
    "pow_base_monotone": (
        4_836,
        "f4dc16c983802fce44d8b264004340317ad4aa7631f51282288e65014f19681f",
        ("pow_zero", "pow_successor_decompose", "le_refl", "mul_le_mul"),
        (4, 68, 90, 28, 90, 89, 0),
        (4_401, 65, 1_185, 1_234, 50, "8dfc05500072540a92ab37b941651f6fcaf7a1e46d5bd199a6291e7388750780"),
    ),
}


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_order_candidate_theorems(TheoremSpec)


def _walk_syntax(value: Formula | Term):
    yield value
    for field in fields(value):
        child = getattr(value, field.name)
        if isinstance(child, (Formula, Term)):
            yield from _walk_syntax(child)


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


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | {item.name: item for item in _specs()}


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    public = _specs_by_name()
    if name in public:
        checked = replay(name)
        return checked.formula, checked.certificate

    item = next(candidate for candidate in _specs() if candidate.name == name)
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
    body = checked_final(state, target)

    closed = body
    for dependency in item.dependencies:
        assert type(closed) is ImpIntro
        closed = closed.body
    dependency_proofs = tuple(_close(dependency) for dependency in item.dependencies)
    for (dependency_formula, dependency_proof) in reversed(dependency_proofs):
        closed = Cut(dependency_formula, formula, dependency_proof, closed)

    assert check((), closed, formula)
    return formula, closed


def test_bertrand_power_order_surface_is_frozen_native_and_topological() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert len({item.name for item in specs}) == len(specs) == 4
    assert not ({item.name for item in specs} & set(_specs_by_name()))

    available = set(_specs_by_name())
    for item in specs:
        length, digest, dependencies, _body, _closed = EXPECTED[item.name]
        assert len(item.statement) == length
        assert sha256(item.statement.encode()).hexdigest() == digest
        assert item.dependencies == dependencies
        assert all(dependency in available for dependency in dependencies)
        available.add(item.name)

        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert tuple(_walk_syntax(formula))
        assert all(
            marker not in item.statement
            for marker in ("Pow(", "Le(", "<", "<=", "^", "DNE")
        )


def test_bertrand_power_order_bodies_kernel_check_constructively() -> None:
    receipts = replay_candidate_bodies(_specs())
    assert tuple(receipt.name for receipt in receipts) == tuple(EXPECTED)
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


def test_bertrand_power_order_every_direct_dependency_is_live() -> None:
    specs = _specs()
    core = _available()
    for item in specs:
        for dependency in item.dependencies:
            mutated = replace(
                item,
                dependencies=tuple(
                    name for name in item.dependencies if name != dependency
                ),
            )
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((mutated,), core=core)


def test_bertrand_power_order_false_conclusions_are_rejected() -> None:
    specs = _specs()
    for item in specs:
        mutated = replace(item, statement=f"({item.statement}) /\\ false")
        mutated_specs = tuple(
            mutated if candidate.name == item.name else candidate
            for candidate in specs
        )
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(mutated_specs)


def test_bertrand_power_order_closes_without_dne_within_live_limits() -> None:
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


def test_bertrand_power_order_orientation_matches_standard_naturals() -> None:
    for a in range(6):
        for b in range(a, 6):
            for c in range(6):
                for d in range(c, 6):
                    assert a * c <= b * d
            for exponent in range(6):
                assert a**exponent <= b**exponent
