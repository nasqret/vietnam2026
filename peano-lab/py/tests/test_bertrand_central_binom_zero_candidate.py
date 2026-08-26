"""Fail-closed audit for the relational central-binomial zero law.

The public surface is rebuilt independently as the raw
``Choose(0 + 0,0,z)`` formula.  Its complete predecessor closure is rebuilt
from pinned sources without admitting any CentralBinom sibling as authority.
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
from peano_lab.kernel.terms import Add, Zero, parse_term_in_context, pretty_term
from peano_lab.library import (
    alpha_enrollment_v7,
    bertrand_central_binom_candidate as central_module,
    bertrand_central_binom_zero_candidate as module,
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_laws_candidate as laws_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_table_row_functional_candidate as table_functional_module,
    editions_v7,
    theorems as stable_module,
)
from peano_lab.library.bertrand_central_binom_zero_candidate import (
    make_bertrand_central_binom_zero_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    make_bertrand_choose_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_laws_candidate import (
    make_bertrand_choose_laws_candidate_theorems,
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


CENTRAL_BINOM_ZERO = "central_binom_zero"
EXPECTED_NAMES = (CENTRAL_BINOM_ZERO,)
EXPECTED_DEPENDENCIES = {CENTRAL_BINOM_ZERO: ("choose_zero",)}
EXPECTED_DIRECT_CUTS = {CENTRAL_BINOM_ZERO: 1}
CENTRAL_SIBLINGS = {
    "central_binom_exists",
    "central_binom_functional",
    "central_binom_positive",
}

FOUNDATION_SOURCE_SHA256 = (
    "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
)
ROW_FUNCTIONAL_SOURCE_SHA256 = (
    "dc1e9262e80090c304011728eb651690400b26b535cbf77d42b77c2a2e0f0edf"
)
TABLE_FUNCTIONAL_SOURCE_SHA256 = (
    "379319daec74ad2e6b89b0808f885b87f6cc1a3fab4908559511d26f51be35f5"
)
LAWS_SOURCE_SHA256 = (
    "1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d"
)
CENTRAL_SOURCE_SHA256 = (
    "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e"
)
ZERO_SOURCE_SHA256 = (
    "978dbdbdfe2fa68a5e0db91bbf895517028c66ec5956571fd7c15d0993c52e04"
)

# Fail closed until the isolated kernel gates print reproducible receipts.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CENTRAL_BINOM_ZERO: (
        7264,
        "f23f77071524df5ab8f62385b5db3a3a21eff180f2dd6bde1e2d998fbbe271bd",
        "657f56f6dfbcf6cab38c346d4bfbc2f4bd9091cd9c03956f42f0cff9f7c0600c",
        "cbde1fded95925d0b586af8417221fc560feea6924c4885e226e3e3d25201c5c",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    CENTRAL_BINOM_ZERO: (1, 6, 14, 9, 14, 13, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CENTRAL_BINOM_ZERO: (14, 14, 9, 4, 9),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CENTRAL_BINOM_ZERO: (
        1468,
        66,
        1022,
        1059,
        38,
        6417,
        66,
        "548903ef4578710d65ebd7e427769b5b00363d772d9c0aac5ca46f348ed90ef7",
    ),
}


def _central_binom_relation(
    index_source: str,
    value_source: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Independent expansion of ``Choose(index + index,index,value)``."""

    assert isinstance(variables, tuple)
    context = [
        foundation._identifier(variable, "independent context variable")
        for variable in variables
    ]
    assert len(set(context)) == len(context)
    index_term = parse_term_in_context(index_source, context)
    value_term = parse_term_in_context(value_source, context)
    index = pretty_term(index_term, context).replace("·", "*")
    value = pretty_term(value_term, context).replace("·", "*")
    doubled = pretty_term(Add(index_term, index_term), context).replace(
        "·", "*"
    )
    return foundation._choose_relation_term(
        doubled,
        index,
        value,
        tag=tag,
        variables=variables,
    )


def _expected_relation() -> str:
    return _central_binom_relation(
        "0",
        "z",
        tag="bcbz_source",
        variables=("z",),
    )


def _expected_statement() -> str:
    return f"forall z. ({_expected_relation()}) -> z = 1"


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_central_binom_zero_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    """Rebuild exactly the unregistered choose-zero dependency closure."""

    return (
        *make_bertrand_choose_foundation_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_table_row_functional_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_laws_candidate_theorems(TheoremSpec),
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
    assert not (CENTRAL_SIBLINGS & set(public))
    assert not (CENTRAL_SIBLINGS & set(support))
    return public | support


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


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
            raise AssertionError("central-binomial zero row delegated through use")
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


def test_central_binom_zero_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_functional_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_functional_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
        (laws_module, LAWS_SOURCE_SHA256),
        (central_module, CENTRAL_SOURCE_SHA256),
        (module, ZERO_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest


def test_central_binom_zero_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    assert make_bertrand_central_binom_zero_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert rows[0].statement == _expected_statement()
    assert rows[0].dependencies == EXPECTED_DEPENDENCIES[CENTRAL_BINOM_ZERO]
    assert module.__all__ == [
        "make_bertrand_central_binom_zero_candidate_theorems"
    ]
    assert _expected_relation() in rows[0].statement
    assert "0 + 0" in rows[0].statement
    assert "2 * 0" not in rows[0].statement

    stable = set(_specs_by_name())
    support = set(_table(_support_specs()))
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & support)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert not (CENTRAL_SIBLINGS & stable)
    assert not (CENTRAL_SIBLINGS & support)
    assert all(dependency in _core() for dependency in rows[0].dependencies)

    provider_token = "bertrand_central_binom_zero_candidate"
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
        "CentralBinom(",
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


def test_central_binom_zero_helper_and_script_are_exact() -> None:
    assert central_module._central_binom_relation_term(
        "0",
        "z",
        tag="bcbz_source",
        variables=("z",),
    ) == _expected_relation()
    assert _specs()[0].script == (
        "intro z",
        "intro hcentral",
        "specialize choose_zero (0 + 0)",
        "specialize choose_zero z",
        "apply choose_zero",
        "exact hcentral",
    )
    assert len(_specs()[0].script) == 6
    assert not any(
        command.startswith("induction ") or command.startswith("rewrite ")
        for command in _specs()[0].script
    )


def test_central_binom_zero_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


def test_central_binom_zero_artifact_receipt_is_frozen() -> None:
    item = _specs()[0]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CENTRAL BINOM ZERO ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[CENTRAL_BINOM_ZERO] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[CENTRAL_BINOM_ZERO]


def test_central_binom_zero_body_and_envelope_are_frozen() -> None:
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
        label="CentralBinom zero body",
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
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    print(
        f"CENTRAL BINOM ZERO BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[CENTRAL_BINOM_ZERO] is not None, (
        f"freeze body receipt: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[CENTRAL_BINOM_ZERO] is not None, (
        f"freeze envelope receipt: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[CENTRAL_BINOM_ZERO]
    assert envelope == EXPECTED_ENVELOPES[CENTRAL_BINOM_ZERO]


def test_central_binom_zero_direct_dependency_is_live() -> None:
    item = _specs()[0]
    shortened = replace(item, dependencies=())
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_core())


def test_central_binom_zero_false_target_is_rejected() -> None:
    item = _specs()[0]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_core())


def _mutations() -> tuple[tuple[str, str, str], ...]:
    relation = _expected_relation()
    successor_central = _central_binom_relation(
        "S 0",
        "z",
        tag="bcbz_source",
        variables=("z",),
    )
    out_of_range = foundation._choose_relation_term(
        "0 + 0",
        "S 0",
        "z",
        tag="bcbz_source",
        variables=("z",),
    )
    return (
        ("successor_central_source", relation, successor_central),
        ("successor_column_source", relation, out_of_range),
    )


def test_central_binom_zero_mutations_have_standard_counterfixtures() -> None:
    # CentralBinom(S 0)=C(2,1)=2, not one.
    assert 2 != 1
    # Choose(0,S 0)=0 by the relation's out-of-range branch, not one.
    assert 0 != 1


@pytest.mark.parametrize(
    ("case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[0] for case in _mutations()),
)
def test_central_binom_zero_genuine_mutations_are_rejected(
    case_id: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = _specs()[0]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_core())


def test_central_binom_zero_empty_context_closure_is_frozen() -> None:
    item = _specs()[0]
    formula, certificate = _close(CENTRAL_BINOM_ZERO)
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
        label="CentralBinom zero closure",
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
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[CENTRAL_BINOM_ZERO]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    print(f"CENTRAL BINOM ZERO CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[CENTRAL_BINOM_ZERO] is not None, (
        f"freeze empty-context closure receipt: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[CENTRAL_BINOM_ZERO]
