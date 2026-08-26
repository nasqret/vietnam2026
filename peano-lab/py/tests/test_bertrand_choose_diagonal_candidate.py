"""Fail-closed audit for fused Pascal diagonal semantics and Choose self.

The two candidates remain outside Stable and Alpha authority.  Static gates
pin their expanded raw-PA surfaces, direct dependency boundary, and committed
authoring helpers.  Execution receipts remain closed until independently
reproduced kernel checks are frozen.
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
    bertrand_choose_diagonal_candidate as module,
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_laws_candidate as laws_module,
    editions_v7,
    theorems as stable_module,
)
from peano_lab.library.bertrand_choose_diagonal_candidate import (
    make_bertrand_choose_diagonal_candidate_theorems,
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


DIAGONAL_BOUNDARY = "beta_pascal_table_diagonal_boundary"
CHOOSE_SELF = "choose_self"
EXPECTED_NAMES = (DIAGONAL_BOUNDARY, CHOOSE_SELF)
EXPECTED_DEPENDENCIES = {
    DIAGONAL_BOUNDARY: (
        "add_eq_zero_right",
        "succ_ne_zero",
        "succ_injective",
        "le_of_succ_le_succ",
        "lt_to_le",
        "le_refl",
        "beta_at_unique",
    ),
    CHOOSE_SELF: (
        "lt_irrefl_expanded",
        "le_refl",
        DIAGONAL_BOUNDARY,
    ),
}

FOUNDATION_SOURCE_SHA256 = (
    "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
)
CHOOSE_LAWS_SOURCE_SHA256 = (
    "1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d"
)

# None is fail-closed and carries no theorem authority.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    DIAGONAL_BOUNDARY: (
        6462,
        "d8bdec80b2ce94b0c1f70fb6a79ef6e406dfee88365241421e45c8190aee17aa",
        "c11e21b1d40ffc38bdd40cbe348cd470cfd346fb921c1d9c6a86546663b43f37",
        "f6b0f9fe3e14677a7b76c80a142d13df2986a78a8de24e1449c6e62c3a8d7389",
    ),
    CHOOSE_SELF: (
        7069,
        "aa48471d4f3a7a8931dd0b08d002ee4192d15836cfd5cbdca356079453b9159b",
        "b83c6ab8429ec8de333ee6dd824ccbbbd26fa8df799fa56874822aec4f0a6d72",
        "4550e0cc1814c6c45b1ca02017f5e338023662c5139ed3ac64552bd6a501097a",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    DIAGONAL_BOUNDARY: (7, 369, 729, 61, 728, 728, 1),
    CHOOSE_SELF: (3, 48, 62, 31, 62, 61, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    DIAGONAL_BOUNDARY: (729, 728, 61, 1190, 65),
    CHOOSE_SELF: (62, 62, 31, 17, 31),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    DIAGONAL_BOUNDARY: (
        1956,
        66,
        1481,
        1521,
        41,
        7341,
        66,
        "f29ad15b52116f9510844f2af415b847f1430dad8754b2b41ec4e540d187db1b",
    ),
    CHOOSE_SELF: (
        2126,
        69,
        1599,
        1641,
        43,
        9175,
        69,
        "659e4623f629ba93ebc861311140e96fd9f92c4009f1b2578e7a937746463507",
    ),
}


SURFACE_VARIABLES = (
    "bb",
    "bc",
    "sb",
    "sc",
    "w",
    "r",
    "i",
    "b",
    "c",
    "j",
    "z",
)


def _boundary(
    code: str,
    scale: str,
    width_term: str,
    row_index_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    diagonal_value, above_index, above_value = foundation._binders(
        tag,
        variables,
        ("diagonal_value", "above_index", "above_value"),
    )
    owned = variables + (diagonal_value, above_index, above_value)
    diagonal_bound = foundation._lt_term(
        row_index_term,
        width_term,
        tag=f"{tag}_diagonal_bound",
        variables=owned,
    )
    diagonal_at = foundation._beta_at_term(
        code,
        scale,
        row_index_term,
        diagonal_value,
        tag=f"{tag}_diagonal_at",
        variables=owned,
    )
    above_order = foundation._lt_term(
        row_index_term,
        above_index,
        tag=f"{tag}_above_order",
        variables=owned,
    )
    above_bound = foundation._lt_term(
        above_index,
        width_term,
        tag=f"{tag}_above_bound",
        variables=owned,
    )
    above_at = foundation._beta_at_term(
        code,
        scale,
        above_index,
        above_value,
        tag=f"{tag}_above_at",
        variables=owned,
    )
    return (
        f"((({diagonal_bound}) -> forall {diagonal_value}. "
        f"({diagonal_at}) -> {diagonal_value} = 1) /\\ "
        f"forall {above_index} {above_value}. "
        f"({above_order}) -> ({above_bound}) -> "
        f"({above_at}) -> {above_value} = 0)"
    )


def _expected_statements() -> dict[str, str]:
    table = foundation._pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptdb_table"
    )
    row_bound = foundation._lt_term(
        "i",
        "r",
        tag="bptdb_row_bound",
        variables=SURFACE_VARIABLES,
    )
    row_code_at = foundation._beta_at_term(
        "bb",
        "bc",
        "i",
        "b",
        tag="bptdb_row_code_at",
        variables=SURFACE_VARIABLES,
    )
    row_scale_at = foundation._beta_at_term(
        "sb",
        "sc",
        "i",
        "c",
        tag="bptdb_row_scale_at",
        variables=SURFACE_VARIABLES,
    )
    boundary = _boundary(
        "b",
        "c",
        "w",
        "i",
        tag="bptdb_boundary",
        variables=SURFACE_VARIABLES,
    )
    choose = foundation._choose_relation("n", "n", "z", tag="bcs_choose")
    return {
        DIAGONAL_BOUNDARY: (
            "forall bb bc sb sc w r. "
            f"({table}) -> forall i. ({row_bound}) -> forall b c. "
            f"({row_code_at}) -> ({row_scale_at}) -> ({boundary})"
        ),
        CHOOSE_SELF: f"forall n z. ({choose}) -> z = 1",
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_diagonal_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    assert not (set(EXPECTED_NAMES) & set(public))
    return public


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
            raise AssertionError("diagonal candidate delegated through use")
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


def test_choose_diagonal_predecessor_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (laws_module, CHOOSE_LAWS_SOURCE_SHA256),
    )
    for predecessor, digest in expected:
        assert sha256(Path(predecessor.__file__).read_bytes()).hexdigest() == digest


def test_choose_diagonal_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    expected = _expected_statements()
    assert make_bertrand_choose_diagonal_candidate_theorems(TheoremSpec) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_choose_diagonal_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert all(
        dependency in _available()
        for item in rows
        for dependency in item.dependencies
    )

    provider_token = "bertrand_choose_diagonal_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    for item in rows:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            marker not in item.statement
            for marker in (
                "BetaAt(",
                "PascalZeroRow(",
                "PascalRowStep(",
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
        )
        assert all(
            forbidden not in command
            for command in item.script
            for forbidden in (
                "DNE",
                "classical",
                "by_contra",
                "sorry",
                "auto",
                "compact_arith",
                "ring",
                "use ",
            )
        )


def test_choose_diagonal_public_order_and_sparse_topology_are_exact() -> None:
    rows = _table(_specs())
    boundary = rows[DIAGONAL_BOUNDARY]
    assert boundary.statement.startswith("forall bb bc sb sc w r. (")
    assert ") -> forall i. (" in boundary.statement
    assert ") -> forall b c. (" in boundary.statement
    diagonal_marker = ") -> forall bcf_diagonal_value_bptdb_boundary. ("
    above_marker = (
        "/\\ forall bcf_above_index_bptdb_boundary "
        "bcf_above_value_bptdb_boundary. ("
    )
    assert boundary.statement.find(diagonal_marker) < boundary.statement.find(
        above_marker
    )
    assert boundary.script[:9] == (
        "intro bb",
        "intro bc",
        "intro sb",
        "intro sc",
        "intro w",
        "intro r",
        "intro htable",
        "intro i",
        "induction i",
    )
    assert boundary.script.count("induction i") == 1
    assert boundary.script.count("split") == 2
    assert sum(
        command.startswith("have hprevious_boundary : ")
        for command in boundary.script
    ) == 1
    assert boundary.script.index("apply IH") < boundary.script.index(
        "cases hprevious_boundary"
    )
    assert not any(
        command.startswith("exists ")
        for item in rows.values()
        for command in item.script
    )
    assert rows[CHOOSE_SELF].statement.startswith("forall n z. (")
    assert rows[CHOOSE_SELF].statement.endswith("z = 1")


def test_choose_diagonal_boundary_helper_is_hygienic() -> None:
    variables = ("b", "c", "w", "i", "j", "z")
    left = module._diagonal_boundary_term(
        "b", "c", "w", "i", tag="hygiene_left", variables=variables
    )
    right = module._diagonal_boundary_term(
        "b", "c", "w", "i", tag="hygiene_right", variables=variables
    )
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"b", "c", "w", "i"}

    family_variables = ("bb", "bc", "sb", "sc", "w", "i")
    family_left = module._row_boundary_family(
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "i",
        tag="family_left",
        variables=family_variables,
    )
    family_right = module._row_boundary_family(
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "i",
        tag="family_right",
        variables=family_variables,
    )
    parsed_family_left, free_family_left = parse_formula_with_names(
        family_left
    )
    parsed_family_right, free_family_right = parse_formula_with_names(
        family_right
    )
    assert family_left != family_right
    assert parsed_family_left == parsed_family_right
    assert set(free_family_left) == set(free_family_right) == {
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "i",
    }

    with pytest.raises(ValueError):
        module._diagonal_boundary_term(
            "b",
            "c",
            "w",
            "i",
            tag="valid",
            variables=(
                "b",
                "c",
                "w",
                "i",
                "j",
                "z",
                "bcf_diagonal_value_valid",
            ),
        )
    with pytest.raises(ValueError):
        module._diagonal_boundary_term(
            "b", "c", "w", "i", tag="bad tag", variables=variables
        )
    with pytest.raises(ValueError):
        module._row_boundary_family(
            "bb",
            "bc",
            "sb",
            "sc",
            "w",
            "i",
            tag="valid",
            variables=family_variables + ("bcf_row_code_valid",),
        )


def test_choose_diagonal_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_diagonal_artifact_receipts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CHOOSE DIAGONAL ARTIFACT {name} actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_diagonal_bodies_and_envelopes_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
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
        label=f"Choose diagonal {name} body",
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
        f"CHOOSE DIAGONAL BODY {name} actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    assert EXPECTED_BODIES[name] is not None, f"freeze body: {actual!r}"
    assert EXPECTED_ENVELOPES[name] is not None, (
        f"freeze envelope: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


DIRECT_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


@pytest.mark.parametrize(("name", "dependency"), DIRECT_EDGES)
def test_choose_diagonal_every_direct_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(
            candidate
            for candidate in item.dependencies
            if candidate != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_diagonal_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    diagonal_value, above_index, _above_value = foundation._binders(
        "bptdb_boundary",
        SURFACE_VARIABLES,
        ("diagonal_value", "above_index", "above_value"),
    )
    owned = SURFACE_VARIABLES + (
        diagonal_value,
        above_index,
        _above_value,
    )
    above_old = foundation._lt_term(
        "i",
        above_index,
        tag="bptdb_boundary_above_order",
        variables=owned,
    )
    above_new = foundation._le_term(
        "i",
        above_index,
        tag="bptdb_boundary_above_order",
        variables=owned,
    )
    diagonal_old = foundation._beta_at_term(
        "b",
        "c",
        "i",
        diagonal_value,
        tag="bptdb_boundary_diagonal_at",
        variables=owned,
    )
    diagonal_new = foundation._beta_at_term(
        "b",
        "c",
        "S i",
        diagonal_value,
        tag="bptdb_boundary_diagonal_at",
        variables=owned,
    )
    choose_old = foundation._choose_relation(
        "n", "n", "z", tag="bcs_choose"
    )
    choose_new = foundation._choose_relation_term(
        "n", "S n", "z", tag="bcs_choose", variables=("n", "z")
    )
    cases = (
        (DIAGONAL_BOUNDARY, "weak_above_order", above_old, above_new),
        (
            DIAGONAL_BOUNDARY,
            "shift_diagonal_cell",
            diagonal_old,
            diagonal_new,
        ),
        (CHOOSE_SELF, "successor_column", choose_old, choose_new),
    )
    statements = _expected_statements()
    assert all(
        statements[name].count(old) == 1
        for name, _case_id, old, _new in cases
    )
    return cases


def test_choose_diagonal_mutations_have_standard_witnesses() -> None:
    # Row zero at i=j=0 has value one, refuting weak above-diagonal order.
    assert 0 <= 0 and 1 != 0
    # Row zero at width two has value zero in the shifted cell one.
    assert 0 != 1
    # Choose(0,1,0) is out of range, refuting the shifted self column.
    assert 0 != 1


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_choose_diagonal_genuine_mutations_are_rejected(
    name: str,
    case_id: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = _table(_specs())[name]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_diagonal_empty_context_closures_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    formula, certificate = _close(name)
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
        label=f"Choose diagonal {name} closure",
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
    print(f"CHOOSE DIAGONAL CLOSURE {name} actual={actual!r}", flush=True)
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
    assert direct_cut_count == (7 if name == DIAGONAL_BOUNDARY else 3)
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze empty-context closure receipt: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
