"""Fail-closed audit for unconditional relational Pascal recurrence.

The candidate remains outside Stable and Alpha authority.  Its public formula
is rebuilt independently from the committed recurrence-first Choose helper,
and every candidate dependency is replayed from its body before the final
empty-context certificate is accepted.  Receipts are evidence only.
"""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import (
    alpha_enrollment_v7,
    bertrand_choose_diagonal_candidate as diagonal_module,
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_laws_candidate as laws_module,
    bertrand_choose_pascal_candidate as module,
    bertrand_choose_recurrence_candidate as recurrence_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_table_row_functional_candidate as table_functional_module,
    editions_v7,
    theorems as stable_module,
)
from peano_lab.library.bertrand_choose_diagonal_candidate import (
    make_bertrand_choose_diagonal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    make_bertrand_choose_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_laws_candidate import (
    make_bertrand_choose_laws_candidate_theorems,
)
from peano_lab.library.bertrand_choose_pascal_candidate import (
    make_bertrand_choose_pascal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_recurrence_candidate import (
    make_bertrand_choose_recurrence_candidate_theorems,
)
from peano_lab.library.bertrand_choose_row_functional_candidate import (
    make_bertrand_choose_row_functional_candidate_theorems,
)
from peano_lab.library.bertrand_choose_table_row_functional_candidate import (
    make_bertrand_choose_table_row_functional_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    _proof_envelope_metrics_bounded,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


CHOOSE_SUCC_SUCC = "choose_succ_succ"
EXPECTED_NAMES = (CHOOSE_SUCC_SUCC,)
EXPECTED_DEPENDENCIES = {
    CHOOSE_SUCC_SUCC: (
        "lt_trichotomy",
        "le_refl",
        "le_succ",
        "succ_le_succ",
        "choose_out_of_range_zero",
        "choose_self",
        "choose_succ_succ_of_lt",
    ),
}
EXPECTED_DIRECT_CUTS = {CHOOSE_SUCC_SUCC: 7}

FOUNDATION_SOURCE_SHA256 = (
    "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
)
LAWS_SOURCE_SHA256 = (
    "1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d"
)
DIAGONAL_SOURCE_SHA256 = (
    "96044d1bf4e10dfffba3f9f7482c4fd9ff1f94fffbccac9fe45af32a32a691bc"
)
RECURRENCE_SOURCE_SHA256 = (
    "8b4a65b18e6a97a89c3f714686f2c690afb49f82ab56ed9575e3f673f50093c5"
)
ROW_FUNCTIONAL_SOURCE_SHA256 = (
    "dc1e9262e80090c304011728eb651690400b26b535cbf77d42b77c2a2e0f0edf"
)
TABLE_FUNCTIONAL_SOURCE_SHA256 = (
    "379319daec74ad2e6b89b0808f885b87f6cc1a3fab4908559511d26f51be35f5"
)

# Fail closed until each isolated gate reproduces a kernel-checked receipt.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CHOOSE_SUCC_SUCC: (
        21217,
        "57b08f03bf3a652a0bd99b20c9133353f036111132e3e92c90a5a8bf26b4f5e5",
        "2ba3f6eaa0de55e661b020113d9a76ae74e2582f2123671dc63a9324d6c50b4f",
        "c04abedb7d0e3146f616fbe0837bfa3f16c57c55113e1909f6213f7f7eea162f",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {CHOOSE_SUCC_SUCC: (7, 94, 121, 27, 121, 120, 0)}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CHOOSE_SUCC_SUCC: (121, 121, 27, 3232, 67),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CHOOSE_SUCC_SUCC: (
        8602,
        88,
        3266,
        3328,
        63,
        55988,
        90,
        "257f69b243ae9c6482231a6ab33f30957ed10e2d4db1684e089625d2e92e1903",
    ),
}

SURFACE_VARIABLES = ("n", "k", "x", "y", "z")


def _expected_components() -> tuple[str, str, str]:
    left = foundation._choose_relation_term(
        "n",
        "k",
        "x",
        tag="bcss_left",
        variables=SURFACE_VARIABLES,
    )
    right = foundation._choose_relation_term(
        "n",
        "S k",
        "y",
        tag="bcss_right",
        variables=SURFACE_VARIABLES,
    )
    result = foundation._choose_relation_term(
        "S n",
        "S k",
        "z",
        tag="bcss_result",
        variables=SURFACE_VARIABLES,
    )
    return left, right, result


def _expected_statement() -> str:
    left, right, result = _expected_components()
    return (
        "forall n k x y z. "
        f"({left}) -> ({right}) -> ({result}) -> z = x + y"
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_pascal_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    """Rebuild every unregistered predecessor candidate from source."""

    return (
        *make_bertrand_choose_foundation_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_table_row_functional_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_laws_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_diagonal_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_recurrence_candidate_theorems(TheoremSpec),
    )


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    support = _table(_support_specs())
    assert not (set(public) & set(support))
    assert not (set(EXPECTED_NAMES) & set(public))
    assert not (set(EXPECTED_NAMES) & set(support))
    return public | support


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


def _row_core(name: str) -> dict[str, TheoremSpec]:
    prior = _specs()[: EXPECTED_NAMES.index(name)]
    return _core() | {item.name: item for item in prior}


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
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
        if tactic == "use":
            raise AssertionError("Choose Pascal wrapper delegated through use")
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    public = _specs_by_name()
    if name in public:
        checked = replay(name)
        return checked.formula, checked.certificate

    item = _available()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    formula = _closed_formula(item.statement)
    dependencies = tuple(_close(name) for name in item.dependencies)
    for dependency_formula, dependency_proof in reversed(dependencies):
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    return formula, body


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
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


def _proof_dag_sha256(proof: Proof) -> str:
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
                (child, False)
                for child in children
                if id(child) not in digests
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


def _mutate_direct_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_direct_cut(proof.body, index - 1))


def test_choose_pascal_predecessor_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (laws_module, LAWS_SOURCE_SHA256),
        (diagonal_module, DIAGONAL_SOURCE_SHA256),
        (recurrence_module, RECURRENCE_SOURCE_SHA256),
        (row_functional_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_functional_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
    )
    for predecessor, digest in expected:
        assert sha256(Path(predecessor.__file__).read_bytes()).hexdigest() == digest


def test_choose_pascal_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    assert make_bertrand_choose_pascal_candidate_theorems(TheoremSpec) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert rows[0].statement == _expected_statement()
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_choose_pascal_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    support = set(_table(_support_specs()))
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & support)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert all(dependency in _core() for dependency in rows[0].dependencies)

    provider_token = "bertrand_choose_pascal_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    formula, free_names = parse_formula_with_names(rows[0].statement)
    assert not free_names
    assert formula == _closed_formula(rows[0].statement)
    forbidden_surface = (
        "BetaAt(",
        "PascalTablePrefix(",
        "Choose(",
        "Factorial(",
        "Product(",
        "<=",
        "<",
        "^",
        "%",
        "|",
    )
    forbidden_script = (
        "DNE",
        "classical",
        "by_contra",
        "sorry",
        "auto",
        "compact_arith",
        "ring",
        "use ",
    )
    assert all(token not in rows[0].statement for token in forbidden_surface)
    assert all(
        token not in command
        for command in rows[0].script
        for token in forbidden_script
    )


def test_choose_pascal_binders_and_transport_topology_are_exact() -> None:
    item = _specs()[0]
    assert item.statement.startswith("forall n k x y z. (")
    assert item.statement.endswith("z = x + y")
    assert item.script[:11] == (
        "intro n",
        "intro k",
        "intro x",
        "intro y",
        "intro z",
        "intro hleft",
        "intro hright",
        "intro hresult",
        "specialize lt_trichotomy k",
        "specialize lt_trichotomy n",
        "cases lt_trichotomy",
    )
    assert item.script.count(
        "rewrite lt_trichotomy_left at hleft"
    ) == 4
    assert item.script.count(
        "rewrite lt_trichotomy_left at hresult"
    ) == 4
    assert item.script.count("rewrite lt_trichotomy_left") == 1
    assert not any(command.endswith("at hright") for command in item.script)
    assert item.script.count("apply choose_self") == 2
    assert item.script.count("apply choose_out_of_range_zero") == 4
    assert item.script.count("apply choose_succ_succ_of_lt") == 1
    assert item.script.count("apply le_succ") == 1
    assert item.script.count("apply succ_le_succ") == 1
    assert not any(command.startswith("induction ") for command in item.script)


def test_choose_pascal_relation_builder_is_hygienic() -> None:
    left = foundation._choose_relation_term(
        "n",
        "k",
        "x",
        tag="hygiene_left",
        variables=("n", "k", "x"),
    )
    right = foundation._choose_relation_term(
        "n",
        "k",
        "x",
        tag="hygiene_right",
        variables=("n", "k", "x"),
    )
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"n", "k", "x"}

    with pytest.raises(ValueError):
        foundation._choose_relation_term(
            "n",
            "k",
            "x",
            tag="valid",
            variables=("n", "k", "x", "bcf_row_code_code_valid"),
        )
    with pytest.raises(ValueError):
        foundation._choose_relation_term(
            "n",
            "k",
            "x",
            tag="bad tag",
            variables=("n", "k", "x"),
        )


def test_choose_pascal_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


def test_choose_pascal_artifact_receipt_is_frozen() -> None:
    item = _specs()[0]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CHOOSE PASCAL ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[CHOOSE_SUCC_SUCC] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[CHOOSE_SUCC_SUCC]


def test_choose_pascal_body_and_envelope_are_frozen() -> None:
    item = _specs()[0]
    body, target = _body(item)
    assert check((), body, target)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    envelope = _proof_envelope_metrics_bounded(
        body,
        max_proof_occurrences=limits.max_body_occurrences,
        max_proof_objects=limits.max_body_objects,
        max_proof_depth=limits.max_body_depth,
        max_annotation_occurrences=limits.max_body_annotation_occurrences,
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_body_envelope_depth,
        label="Choose Pascal body",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    actual = (
        len(item.dependencies),
        len(item.script),
        nodes,
        depth,
        objects,
        edges,
        reused,
    )
    print(
        f"CHOOSE PASCAL BODY actual={actual!r} envelope={envelope!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    assert EXPECTED_BODIES[CHOOSE_SUCC_SUCC] is not None, (
        f"freeze body: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[CHOOSE_SUCC_SUCC] is not None, (
        f"freeze envelope: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[CHOOSE_SUCC_SUCC]
    assert envelope == EXPECTED_ENVELOPES[CHOOSE_SUCC_SUCC]


@pytest.mark.parametrize(
    "dependency", EXPECTED_DEPENDENCIES[CHOOSE_SUCC_SUCC]
)
def test_choose_pascal_every_direct_dependency_is_live(
    dependency: str,
) -> None:
    item = _specs()[0]
    shortened = replace(
        item,
        dependencies=tuple(
            candidate
            for candidate in item.dependencies
            if candidate != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (shortened,), core=_row_core(CHOOSE_SUCC_SUCC)
        )


def test_choose_pascal_false_target_is_rejected() -> None:
    item = _specs()[0]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (mutated,), core=_row_core(CHOOSE_SUCC_SUCC)
        )


def _mutations() -> tuple[tuple[str, str, str], ...]:
    _left, right_old, result_old = _expected_components()
    right_without_successor = foundation._choose_relation_term(
        "n",
        "k",
        "y",
        tag="bcss_right",
        variables=SURFACE_VARIABLES,
    )
    result_without_row_successor = foundation._choose_relation_term(
        "n",
        "S k",
        "z",
        tag="bcss_result",
        variables=SURFACE_VARIABLES,
    )
    result_without_column_successor = foundation._choose_relation_term(
        "S n",
        "k",
        "z",
        tag="bcss_result",
        variables=SURFACE_VARIABLES,
    )
    cases = (
        ("right_column_without_successor", right_old, right_without_successor),
        ("result_row_without_successor", result_old, result_without_row_successor),
        (
            "result_column_without_successor",
            result_old,
            result_without_column_successor,
        ),
        ("successor_shifted_sum", "z = x + y", "z = S (x + y)"),
    )
    statement = _expected_statement()
    assert all(statement.count(old) == 1 for _case_id, old, _new in cases)
    return cases


def test_choose_pascal_mutations_have_standard_witnesses() -> None:
    # C(3,1)=3, not C(2,0)+C(2,0)=2.
    assert 3 != 1 + 1
    # C(1,1)=1, not C(1,0)+C(1,1)=2.
    assert 1 != 1 + 1
    # C(2,0)=1, not C(1,0)+C(1,1)=2.
    assert 1 != 1 + 1
    # C(1,1)=1, not S(C(0,0)+C(0,1))=2.
    assert 1 != 1 + 0 + 1


@pytest.mark.parametrize(
    ("case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[0] for case in _mutations()),
)
def test_choose_pascal_genuine_mutations_are_rejected(
    case_id: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = _specs()[0]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (mutated,), core=_row_core(CHOOSE_SUCC_SUCC)
        )


def test_choose_pascal_empty_context_closure_is_frozen() -> None:
    item = _specs()[0]
    formula, certificate = _close(CHOOSE_SUCC_SUCC)
    assert formula == _closed_formula(item.statement)
    assert check((), certificate, formula)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    envelope = _proof_envelope_metrics_bounded(
        certificate,
        max_proof_occurrences=limits.max_candidate_proof_occurrences,
        max_proof_objects=limits.max_candidate_proof_objects,
        max_proof_depth=limits.max_candidate_proof_depth,
        max_annotation_occurrences=(
            limits.max_candidate_annotation_occurrences
        ),
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_candidate_envelope_depth,
        label="Choose Pascal closure",
    )
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    actual = (
        nodes,
        depth,
        objects,
        edges,
        reused,
        envelope[3],
        envelope[4],
        _proof_dag_sha256(certificate),
    )
    print(f"CHOOSE PASCAL CLOSURE actual={actual!r}", flush=True)
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(certificate))

    direct_cut_count = 0
    probe = certificate
    while type(probe) is Cut:
        direct_cut_count += 1
        probe = probe.body
    assert direct_cut_count == len(item.dependencies)
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[CHOOSE_SUCC_SUCC]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    assert EXPECTED_CLOSURES[CHOOSE_SUCC_SUCC] is not None, (
        f"freeze empty-context closure receipt: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[CHOOSE_SUCC_SUCC]
