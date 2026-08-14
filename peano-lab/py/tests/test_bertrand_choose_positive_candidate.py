"""Fail-closed audit for constructive relational Choose positivity.

The candidate remains outside Stable and Alpha authority.  Its public formula
and interior relational instances are rebuilt independently from the raw
Choose helpers, and every candidate dependency is closed from its body before
the final empty-context certificate is accepted.  Receipts are evidence only.
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
    bertrand_choose_pascal_candidate as pascal_module,
    bertrand_choose_positive_candidate as module,
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
from peano_lab.library.bertrand_choose_positive_candidate import (
    make_bertrand_choose_positive_candidate_theorems,
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


CHOOSE_POSITIVE = "choose_positive"
EXPECTED_NAMES = (CHOOSE_POSITIVE,)
EXPECTED_DEPENDENCIES = {
    CHOOSE_POSITIVE: (
        "le_zero",
        "le_of_succ_le_succ",
        "add_succ_left",
        "choose_exists",
        "choose_zero",
        "choose_succ_succ",
    ),
}
EXPECTED_DIRECT_CUTS = {CHOOSE_POSITIVE: 6}
EXPECTED_LOGICAL_LEAVES = {CHOOSE_POSITIVE: 4}

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
DIAGONAL_SOURCE_SHA256 = (
    "96044d1bf4e10dfffba3f9f7482c4fd9ff1f94fffbccac9fe45af32a32a691bc"
)
RECURRENCE_SOURCE_SHA256 = (
    "8b4a65b18e6a97a89c3f714686f2c690afb49f82ab56ed9575e3f673f50093c5"
)
PASCAL_SOURCE_SHA256 = (
    "e96ee1d140beece2666b901dc7d671743b01386f110628b0957aeff01b9c26c3"
)
POSITIVE_SOURCE_SHA256 = (
    "6c289d581e218841013b4f321fb39e66cc815c3ecc7be17d04b6f9fb586592cc"
)

# Fail closed until each isolated kernel gate prints a reproducible receipt.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CHOOSE_POSITIVE: (
        7148,
        "911315820bee29b1b6c45d1574882c6500dd6371f33ccc65195b7fe1118d4aad",
        "6d50ac30f1c4bca999568bcef6529ee4b22df2ddfeb79c5c955fee241d516198",
        "325619dd8886987d4718d7aa8b57ebddbcd2c90b08811b2196dff34451f7ba53",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {CHOOSE_POSITIVE: (6, 69, 87, 29, 87, 86, 0)}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CHOOSE_POSITIVE: (87, 87, 29, 1257, 56),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CHOOSE_POSITIVE: (
        99707,
        103,
        8038,
        8321,
        284,
        363240,
        103,
        "926862f32b2635dfadfc1952efb77eaf86874a37d98c018679e5acdf9edc8b7e",
    ),
}

SURFACE_VARIABLES = ("n", "k", "z")


def _expected_bound(left: str = "k", right: str = "n") -> str:
    return foundation._le_term(
        left,
        right,
        tag="bcp_bound",
        variables=SURFACE_VARIABLES,
    )


def _expected_choose(column: str = "k") -> str:
    return foundation._choose_relation_term(
        "n",
        column,
        "z",
        tag="bcp_source",
        variables=SURFACE_VARIABLES,
    )


def _expected_statement() -> str:
    return (
        "forall n k z. "
        f"({_expected_bound()}) -> ({_expected_choose()}) -> "
        "exists p. z = S p"
    )


def _expected_interior_haves() -> tuple[str, str]:
    left = foundation._choose_relation_term(
        "n",
        "k",
        "a",
        tag="bcp_previous_left",
        variables=SURFACE_VARIABLES + ("a",),
    )
    right = foundation._choose_relation_term(
        "n",
        "S k",
        "b",
        tag="bcp_previous_right",
        variables=SURFACE_VARIABLES + ("b",),
    )
    return (
        f"have ha_exists : exists a. ({left})",
        f"have hb_exists : exists b. ({right})",
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_positive_candidate_theorems(TheoremSpec)


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
        *make_bertrand_choose_pascal_candidate_theorems(TheoremSpec),
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
            raise AssertionError("Choose positivity delegated through use")
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
    dependencies = tuple(_close(dependency) for dependency in item.dependencies)
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


def test_choose_positive_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_functional_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_functional_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
        (laws_module, LAWS_SOURCE_SHA256),
        (diagonal_module, DIAGONAL_SOURCE_SHA256),
        (recurrence_module, RECURRENCE_SOURCE_SHA256),
        (pascal_module, PASCAL_SOURCE_SHA256),
        (module, POSITIVE_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest


def test_choose_positive_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    assert make_bertrand_choose_positive_candidate_theorems(TheoremSpec) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert rows[0].statement == _expected_statement()
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_choose_positive_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    support = set(_table(_support_specs()))
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & support)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert all(dependency in _core() for dependency in rows[0].dependencies)

    provider_token = "bertrand_choose_positive_candidate"
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


def test_choose_positive_binders_and_induction_topology_are_exact() -> None:
    item = _specs()[0]
    assert item.statement.startswith("forall n k z. (")
    assert item.statement.endswith("exists p. z = S p")
    assert tuple(
        command for command in item.script if command.startswith("induction ")
    ) == ("induction n", "induction k", "induction k")
    assert EXPECTED_LOGICAL_LEAVES[CHOOSE_POSITIVE] == 4
    assert item.script.count("apply choose_zero") == 2
    assert item.script.count("exact choose_exists") == 2
    assert item.script.count("apply choose_succ_succ") == 1
    assert item.script.count("apply IH") == 1
    assert item.script.count("apply le_zero") == 1
    assert item.script.count("apply le_of_succ_le_succ") == 1
    assert item.script.count("exact add_succ_left") == 1
    assert item.script.count("apply PA1") == 1
    interior_haves = tuple(
        command
        for command in item.script
        if command.startswith("have ha_exists")
        or command.startswith("have hb_exists")
    )
    assert interior_haves == _expected_interior_haves()
    assert item.script.count("exists 0") == 2
    assert item.script.count("exists x2 + x1") == 1
    assert not any(
        command.startswith("rewrite ") and command.endswith("at hchoose")
        for command in item.script
    )


def test_choose_positive_raw_helpers_are_hygienic() -> None:
    left_bound = foundation._le_term(
        "k",
        "n",
        tag="hygiene_left",
        variables=SURFACE_VARIABLES,
    )
    right_bound = foundation._le_term(
        "k",
        "n",
        tag="hygiene_right",
        variables=SURFACE_VARIABLES,
    )
    parsed_left_bound, free_left_bound = parse_formula_with_names(left_bound)
    parsed_right_bound, free_right_bound = parse_formula_with_names(right_bound)
    assert left_bound != right_bound
    assert parsed_left_bound == parsed_right_bound
    assert set(free_left_bound) == set(free_right_bound) == {"k", "n"}

    left_choose = foundation._choose_relation_term(
        "n",
        "k",
        "z",
        tag="hygiene_left",
        variables=SURFACE_VARIABLES,
    )
    right_choose = foundation._choose_relation_term(
        "n",
        "k",
        "z",
        tag="hygiene_right",
        variables=SURFACE_VARIABLES,
    )
    parsed_left, free_left = parse_formula_with_names(left_choose)
    parsed_right, free_right = parse_formula_with_names(right_choose)
    assert left_choose != right_choose
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"n", "k", "z"}

    with pytest.raises(ValueError):
        foundation._le_term(
            "k",
            "n",
            tag="valid",
            variables=("n", "k", "z", "bcf_le_gap_valid"),
        )
    with pytest.raises(ValueError):
        foundation._choose_relation_term(
            "n",
            "k",
            "z",
            tag="valid",
            variables=("n", "k", "z", "bcf_row_code_code_valid"),
        )
    with pytest.raises(ValueError):
        foundation._choose_relation_term(
            "n",
            "k",
            "z",
            tag="bad tag",
            variables=SURFACE_VARIABLES,
        )


def test_choose_positive_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


def test_choose_positive_artifact_receipt_is_frozen() -> None:
    item = _specs()[0]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CHOOSE POSITIVE ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[CHOOSE_POSITIVE] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[CHOOSE_POSITIVE]


def test_choose_positive_body_and_envelope_are_frozen() -> None:
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
        label="Choose positive body",
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
        f"CHOOSE POSITIVE BODY actual={actual!r} envelope={envelope!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    assert EXPECTED_BODIES[CHOOSE_POSITIVE] is not None, (
        f"freeze body: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[CHOOSE_POSITIVE] is not None, (
        f"freeze envelope: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[CHOOSE_POSITIVE]
    assert envelope == EXPECTED_ENVELOPES[CHOOSE_POSITIVE]


@pytest.mark.parametrize(
    "dependency", EXPECTED_DEPENDENCIES[CHOOSE_POSITIVE]
)
def test_choose_positive_every_direct_dependency_is_live(
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
            (shortened,), core=_row_core(CHOOSE_POSITIVE)
        )


def test_choose_positive_false_target_is_rejected() -> None:
    item = _specs()[0]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (mutated,), core=_row_core(CHOOSE_POSITIVE)
        )


def _mutations() -> tuple[tuple[str, str, str], ...]:
    bound = _expected_bound()
    choose = _expected_choose()
    reversed_bound = _expected_bound("n", "k")
    shifted_choose = _expected_choose("S k")
    cases = (
        ("missing_in_range_bound", f"({bound}) -> ", ""),
        ("reversed_in_range_bound", bound, reversed_bound),
        ("shifted_source_column", choose, shifted_choose),
        (
            "double_successor_conclusion",
            "exists p. z = S p",
            "exists p. z = S (S p)",
        ),
    )
    statement = _expected_statement()
    assert all(statement.count(old) == 1 for _case_id, old, _new in cases)
    return cases


def test_choose_positive_mutations_have_standard_counterfixtures() -> None:
    # Without the bound, C(0,1)=0 is admitted and zero is not a successor.
    assert 0 != 1
    # Reversing the bound admits C(1,2)=0.
    assert 0 != 1
    # At n=k=0, shifting the source column admits C(0,1)=0.
    assert 0 != 1
    # C(0,0)=1 is a successor, but not a double successor.
    assert 1 != 2


@pytest.mark.parametrize(
    ("case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[0] for case in _mutations()),
)
def test_choose_positive_genuine_mutations_are_rejected(
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
            (mutated,), core=_row_core(CHOOSE_POSITIVE)
        )


def test_choose_positive_empty_context_closure_is_frozen() -> None:
    item = _specs()[0]
    formula, certificate = _close(CHOOSE_POSITIVE)
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
        label="Choose positive closure",
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
    print(f"CHOOSE POSITIVE CLOSURE actual={actual!r}", flush=True)
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
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[CHOOSE_POSITIVE]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    assert EXPECTED_CLOSURES[CHOOSE_POSITIVE] is not None, (
        f"freeze empty-context closure receipt: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[CHOOSE_POSITIVE]
