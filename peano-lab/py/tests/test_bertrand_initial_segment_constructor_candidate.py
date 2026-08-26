"""Kernel, mutation, and closure audit for Bertrand constructor prerequisites."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.bertrand_initial_segment_constructor_candidate import (
    BERTRAND_INITIAL_SEGMENT_CONSTRUCTOR_NAMES,
    LIVE_PREFIX_EXISTS_DEPENDENCIES,
    ORIGINAL_PREFIX_EXISTS_DEPENDENCIES,
    SOURCE_FACTORY_NAMES,
    make_bertrand_initial_segment_constructor_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.eisenstein_initial_segment_count_candidate import (
    make_eisenstein_initial_segment_count_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_DEPENDENCIES = {
    "eisenstein_initial_segment_indicator_choice": ("le_or_lt",),
    "eisenstein_initial_segment_prefix_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "eisenstein_initial_segment_prefix_exists": LIVE_PREFIX_EXISTS_DEPENDENCIES,
}

EXPECTED_STATEMENT_SHA256 = {
    "eisenstein_initial_segment_indicator_choice": (
        "fd63fc3d003ddc6b31729bdc3b1408b45f7e3e435920baa5bf39470619e99d23"
    ),
    "eisenstein_initial_segment_prefix_extend": (
        "e6bdc012743870d4ebce325d86d78e4138a796dfcec67f825ea24de87374e364"
    ),
    "eisenstein_initial_segment_prefix_exists": (
        "d8da07c23b4358a3de037d7469eca479edd099362e5a70e6266365c7534d10ef"
    ),
}

# The first two body receipts are unchanged by projection; the third records
# the exact optimized four-edge body from the serialized replay.
EXPECTED_BODY_RECEIPTS: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    "eisenstein_initial_segment_indicator_choice": (1, 15, 23, 12, 23, 22, 0),
    "eisenstein_initial_segment_prefix_extend": (2, 46, 63, 25, 63, 62, 0),
    "eisenstein_initial_segment_prefix_exists": (4, 33, 38, 17, 38, 37, 0),
}

# Exact empty-context closure receipts from the serialized kernel replay.
EXPECTED_CLOSURES: dict[str, tuple[int, int, int, int, int]] = {
    "eisenstein_initial_segment_indicator_choice": (71, 18, 71, 70, 0),
    "eisenstein_initial_segment_prefix_extend": (
        29_248,
        81,
        4_585,
        4_811,
        227,
    ),
    "eisenstein_initial_segment_prefix_exists": (
        29_377,
        85,
        4_694,
        4_922,
        229,
    ),
}

_REPLAY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_initial_segment_constructor_candidate_theorems(
        TheoremSpec
    )


def _local() -> dict[str, TheoremSpec]:
    rows = _specs()
    assert len({row.name for row in rows}) == len(rows)
    return {row.name: row for row in rows}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


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
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(_proof_children(node))


@contextmanager
def _deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(
            f"Bertrand constructor replay exceeded {seconds} seconds"
        )

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _curried_body(item: TheoremSpec) -> tuple[Proof, Formula]:
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
    return checked_final(state, target), formula


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    local = _local()
    if name not in local:
        theorem = replay(name)
        return theorem.formula, theorem.certificate

    item = local[name]
    curried, formula = _curried_body(item)
    body = curried
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    for dependency in reversed(item.dependencies):
        dependency_formula, dependency_proof = _close(dependency)
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    return formula, body


def _mutate_direct_cut(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(
            certificate,
            proposition=Eq(zero, zero),
            lemma=EqRefl(zero),
        )
    return replace(
        certificate,
        body=_mutate_direct_cut(certificate.body, index - 1),
    )


def test_constructor_projection_is_exact_isolated_and_topological() -> None:
    source = make_eisenstein_initial_segment_count_candidate_theorems(
        TheoremSpec
    )
    specs = _specs()
    assert tuple(item.name for item in source) == SOURCE_FACTORY_NAMES
    assert tuple(item.name for item in specs) == (
        BERTRAND_INITIAL_SEGMENT_CONSTRUCTOR_NAMES
    )
    assert specs[:2] == source[:2]
    assert source[2].dependencies == ORIGINAL_PREFIX_EXISTS_DEPENDENCIES
    assert specs[2].dependencies == LIVE_PREFIX_EXISTS_DEPENDENCIES
    assert (
        specs[2].name,
        specs[2].statement,
        specs[2].script,
        specs[2].summary,
    ) == (
        source[2].name,
        source[2].statement,
        source[2].script,
        source[2].summary,
    )
    assert {item.name: item.dependencies for item in specs} == (
        EXPECTED_DEPENDENCIES
    )
    assert not (
        set(BERTRAND_INITIAL_SEGMENT_CONSTRUCTOR_NAMES)
        & set(_specs_by_name())
    )

    available = set(_specs_by_name())
    for item in specs:
        assert all(dependency in available for dependency in item.dependencies)
        available.add(item.name)
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert sha256(item.statement.encode()).hexdigest() == (
            EXPECTED_STATEMENT_SHA256[item.name]
        )

    commands = tuple(command for item in specs for command in item.script)
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "by_contra", "classical", "sorry")
    )


def test_constructor_bodies_are_exact_constructive_and_bounded() -> None:
    with _deadline(_REPLAY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_specs(), core=_specs_by_name())
    actual = {
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
    for name, receipt in actual.items():
        print(
            "BERTRAND INITIAL SEGMENT CONSTRUCTOR BODY RECEIPT "
            f"name={name} receipt={receipt!r}",
            flush=True,
        )
    missing = tuple(
        name for name, expected in EXPECTED_BODY_RECEIPTS.items() if expected is None
    )
    assert not missing, (
        "freeze the reported constructor body receipt before release: "
        f"missing={missing!r}, actual={actual!r}"
    )
    assert actual == EXPECTED_BODY_RECEIPTS


def test_constructor_false_targets_and_every_removed_edge_are_rejected() -> None:
    available = _available()
    removed_edges = 0
    for item in _specs():
        false_item = replace(item, statement=f"({item.statement}) /\\ false")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((false_item,), core=available)

        for dependency in item.dependencies:
            without_edge = replace(
                item,
                dependencies=tuple(
                    candidate
                    for candidate in item.dependencies
                    if candidate != dependency
                ),
            )
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((without_edge,), core=available)
            removed_edges += 1

    assert removed_edges == 7


def test_constructor_closures_and_every_direct_cut_are_checked() -> None:
    actual: dict[str, tuple[int, int, int, int, int]] = {}
    direct_cut_mutations = 0
    for item in _specs():
        with _deadline(_REPLAY_DEADLINE_SECONDS):
            formula, certificate = _close(item.name)
            assert check((), certificate, formula)
            assert not any(
                type(node) is DNE for node in _walk_unique(certificate)
            )
            nodes, depth = proof_metrics(certificate)
            objects, edges, reused = proof_identity_metrics(certificate)
            receipt = (nodes, depth, objects, edges, reused)
            actual[item.name] = receipt
            assert nodes <= MAX_USE_CERTIFICATE_NODES
            assert depth <= MAX_USE_PROOF_DEPTH
            assert objects <= MAX_USE_CERTIFICATE_OBJECTS

            print(
                "BERTRAND INITIAL SEGMENT CONSTRUCTOR CLOSURE RECEIPT "
                f"name={item.name} receipt={receipt!r}",
                flush=True,
            )

            for index, _dependency in enumerate(item.dependencies):
                assert not check(
                    (),
                    _mutate_direct_cut(certificate, index),
                    formula,
                ), f"accepted mutated direct Cut {item.name}[{index}]"
                direct_cut_mutations += 1

    assert direct_cut_mutations == 7
    missing = tuple(
        name for name, expected in EXPECTED_CLOSURES.items() if expected is None
    )
    assert not missing, (
        "freeze the reported constructor closure receipts before release: "
        f"missing={missing!r}, actual={actual!r}"
    )
    assert actual == EXPECTED_CLOSURES
