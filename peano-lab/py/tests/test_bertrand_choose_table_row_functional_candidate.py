"""Fail-closed audit for cross-encoding Pascal-table row extensionality.

The candidate stays outside Stable and Alpha authority.  Static gates pin its
fully expanded raw-PA surface, both predecessor sources, and its exact direct
dependency boundary.  Execution gates remain closed until deterministic
artifact, body, envelope, and empty-context closure receipts are reproduced.
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
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_row_functional_candidate as support_module,
    bertrand_choose_table_row_functional_candidate as module,
    editions_v7,
    theorems as stable_module,
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


TABLE_ROW_FUNCTIONAL = "beta_pascal_table_row_pointwise_functional"
EXPECTED_NAMES = (TABLE_ROW_FUNCTIONAL,)
SUPPORT_NAMES = (
    "beta_pascal_zero_row_pointwise_functional",
    "beta_pascal_row_step_pointwise_functional",
)
EXPECTED_DEPENDENCIES = {
    TABLE_ROW_FUNCTIONAL: (
        "beta_at_unique",
        "succ_ne_zero",
        "succ_injective",
        "lt_to_le",
        SUPPORT_NAMES[0],
        SUPPORT_NAMES[1],
    ),
}

FOUNDATION_SOURCE_SHA256 = (
    "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
)
ROW_FUNCTIONAL_SOURCE_SHA256 = (
    "dc1e9262e80090c304011728eb651690400b26b535cbf77d42b77c2a2e0f0edf"
)

# None is deliberately fail-closed and never carries logical authority.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    TABLE_ROW_FUNCTIONAL: (
        13_050,
        "c557cf8ea93f44cd422b7c11fbfe91d5338310fce90ea5644196e3364e4402b0",
        "1a03ef96a51946c37bf14d7a49001c9159d9205cd143f970636b41384e5af025",
        "c6757bd3f476a023498549d2fda887e1015e066bb0e1682c7b6523d26150ab42",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    TABLE_ROW_FUNCTIONAL: (6, 313, 467, 75, 467, 466, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    TABLE_ROW_FUNCTIONAL: (467, 467, 75, 1_371, 77),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    TABLE_ROW_FUNCTIONAL: (
        4_298,
        75,
        1_553,
        1_596,
        44,
        17_485,
        77,
        "a611f05422c00dcaddd4b697776aa7c1cf6559296bcfd42890ed28cfe4beff96",
    ),
}


def _agreement(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    left_width: str,
    right_width: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        foundation._identifier(value, label)
        for value, label in (
            (left_code, "left row code"),
            (left_scale, "left row scale"),
            (right_code, "right row code"),
            (right_scale, "right row scale"),
            (left_width, "left row width"),
            (right_width, "right row width"),
        )
    )
    index, left_value, right_value = foundation._binders(
        tag,
        variables,
        ("index", "left_value", "right_value"),
    )
    owned = variables + (index, left_value, right_value)
    left_bound = foundation._lt_term(
        index,
        left_width,
        tag=f"{tag}_left_bound",
        variables=owned,
    )
    right_bound = foundation._lt_term(
        index,
        right_width,
        tag=f"{tag}_right_bound",
        variables=owned,
    )
    left_entry = foundation._beta_at_term(
        left_code,
        left_scale,
        index,
        left_value,
        tag=f"{tag}_left_entry",
        variables=owned,
    )
    right_entry = foundation._beta_at_term(
        right_code,
        right_scale,
        index,
        right_value,
        tag=f"{tag}_right_entry",
        variables=owned,
    )
    return (
        f"forall {index} {left_value} {right_value}. "
        f"({left_bound}) -> ({right_bound}) -> "
        f"({left_entry}) -> ({right_entry}) -> "
        f"{left_value} = {right_value}"
    )


def _expected_statement() -> str:
    variables = (
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "r",
        "db",
        "dc",
        "eb",
        "ec",
        "v",
        "s",
        "i",
        "b",
        "c",
        "d",
        "e",
    )
    left_table = foundation._pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptrpf_left_table"
    )
    right_table = foundation._pascal_table_prefix(
        "db", "dc", "eb", "ec", "v", "s", tag="bptrpf_right_table"
    )
    left_bound = foundation._lt_term(
        "i", "r", tag="bptrpf_left_row_bound", variables=variables
    )
    right_bound = foundation._lt_term(
        "i", "s", tag="bptrpf_right_row_bound", variables=variables
    )
    left_code = foundation._beta_at_term(
        "bb",
        "bc",
        "i",
        "b",
        tag="bptrpf_left_code_at",
        variables=variables,
    )
    left_scale = foundation._beta_at_term(
        "sb",
        "sc",
        "i",
        "c",
        tag="bptrpf_left_scale_at",
        variables=variables,
    )
    right_code = foundation._beta_at_term(
        "db",
        "dc",
        "i",
        "d",
        tag="bptrpf_right_code_at",
        variables=variables,
    )
    right_scale = foundation._beta_at_term(
        "eb",
        "ec",
        "i",
        "e",
        tag="bptrpf_right_scale_at",
        variables=variables,
    )
    agreement = _agreement(
        "b", "c", "d", "e", "w", "v", tag="bptrpf_agree"
    )
    return (
        "forall bb bc sb sc w r db dc eb ec v s i b c d e. "
        f"({left_table}) -> ({right_table}) -> "
        f"({left_bound}) -> ({right_bound}) -> "
        f"({left_code}) -> ({left_scale}) -> "
        f"({right_code}) -> ({right_scale}) -> ({agreement})"
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_table_row_functional_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    table = {item.name: item for item in rows}
    assert len(table) == len(rows)
    return table


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    support = _table(_support_specs())
    assert tuple(support) == SUPPORT_NAMES
    assert not (set(public) & set(support))
    assert not (set(EXPECTED_NAMES) & set(public))
    assert not (set(EXPECTED_NAMES) & set(support))
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
            raise AssertionError("table-row functionality delegated through use")
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


def test_choose_table_row_functional_predecessor_sources_are_pinned() -> None:
    assert sha256(Path(foundation.__file__).read_bytes()).hexdigest() == (
        FOUNDATION_SOURCE_SHA256
    )
    assert sha256(Path(support_module.__file__).read_bytes()).hexdigest() == (
        ROW_FUNCTIONAL_SOURCE_SHA256
    )


def test_choose_table_row_functional_factory_is_exact_and_isolated() -> None:
    rows = _specs()
    item = rows[0]
    assert make_bertrand_choose_table_row_functional_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(entry.name for entry in rows) == EXPECTED_NAMES
    assert len(rows) == 1
    assert item.statement == _expected_statement()
    assert item.dependencies == EXPECTED_DEPENDENCIES[TABLE_ROW_FUNCTIONAL]
    assert module.__all__ == [
        "make_bertrand_choose_table_row_functional_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert set(item.dependencies[:4]) <= stable
    assert item.dependencies[4:] == SUPPORT_NAMES

    provider_token = "bertrand_choose_table_row_functional_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == _closed_formula(item.statement)
    assert all(dependency in _core() for dependency in item.dependencies)
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


def test_choose_table_row_functional_public_surface_order_is_exact() -> None:
    statement = _expected_statement()
    assert statement.startswith(
        "forall bb bc sb sc w r db dc eb ec v s i b c d e. "
    )
    left_table = foundation._pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptrpf_left_table"
    )
    right_table = foundation._pascal_table_prefix(
        "db", "dc", "eb", "ec", "v", "s", tag="bptrpf_right_table"
    )
    agreement = _agreement(
        "b", "c", "d", "e", "w", "v", tag="bptrpf_agree"
    )
    assert statement.find(left_table) < statement.find(right_table)
    assert statement.endswith(f"({agreement})")
    assert statement.count("forall bcf_row_index_bptrpf_") == 2
    assert statement.count("exists bcf_lt_gap_bptrpf_left_row_bound") == 1
    assert statement.count("exists bcf_lt_gap_bptrpf_right_row_bound") == 1
    assert statement.count("forall bcf_index_bptrpf_agree") == 1


def test_choose_table_row_functional_script_topology_is_sparse() -> None:
    script = _specs()[0].script
    assert script[:14] == (
        "intro bb",
        "intro bc",
        "intro sb",
        "intro sc",
        "intro w",
        "intro r",
        "intro db",
        "intro dc",
        "intro eb",
        "intro ec",
        "intro v",
        "intro s",
        "intro i",
        "induction i",
    )
    assert script.count("induction i") == 1
    assert script.count("rewrite <- hb") == 2
    assert script.count("rewrite <- hc") == 4
    assert script.count("rewrite <- hd") == 2
    assert script.count("rewrite <- he") == 4
    assert script.count("rewrite hleft_predecessor") == 4
    assert script.count("rewrite hright_predecessor") == 4
    assert not any(
        command in {"rewrite hb", "rewrite hc", "rewrite hd", "rewrite he"}
        for command in script
    )
    semantic_index = next(
        index
        for index, command in enumerate(script)
        if command.startswith("have hcurrent_semantic : forall ")
    )
    apply_index = script.index(
        "apply beta_pascal_row_step_pointwise_functional"
    )
    specialize_index = script.index("specialize hcurrent_semantic j")
    assert semantic_index < apply_index < specialize_index
    assert script[apply_index + 3] == "specialize IH x5"
    assert not any("rewrite" in command and "table" in command for command in script)


def test_choose_table_row_functional_helpers_are_hygienic() -> None:
    agree_a = module._row_pointwise_agreement(
        "b", "c", "d", "e", "w", "v", tag="hygiene_a"
    )
    agree_b = module._row_pointwise_agreement(
        "b", "c", "d", "e", "w", "v", tag="hygiene_b"
    )
    assert agree_a != agree_b
    parsed_a, free_a = parse_formula_with_names(agree_a)
    parsed_b, free_b = parse_formula_with_names(agree_b)
    assert parsed_a == parsed_b
    assert set(free_a) == set(free_b) == {"b", "c", "d", "e", "w", "v"}

    cell_a = module._table_row_cell(
        "bb", "bc", "sb", "sc", "w", "i", tag="hygiene_a"
    )
    cell_b = module._table_row_cell(
        "bb", "bc", "sb", "sc", "w", "i", tag="hygiene_b"
    )
    assert cell_a != cell_b
    parsed_cell_a, free_cell_a = parse_formula_with_names(cell_a)
    parsed_cell_b, free_cell_b = parse_formula_with_names(cell_b)
    assert parsed_cell_a == parsed_cell_b
    assert set(free_cell_a) == set(free_cell_b) == {
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "i",
    }

    with pytest.raises(ValueError):
        module._row_pointwise_agreement(
            "bcf_index_valid", "c", "d", "e", "w", "v", tag="valid"
        )
    with pytest.raises(ValueError):
        module._table_row_cell(
            "bb", "bc", "sb", "sc", "w", "i", tag="bad tag"
        )


def test_choose_table_row_functional_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


def test_choose_table_row_functional_artifact_receipt_is_frozen() -> None:
    item = _specs()[0]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CHOOSE TABLE ROW FUNCTIONAL ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[TABLE_ROW_FUNCTIONAL] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[TABLE_ROW_FUNCTIONAL]


def test_choose_table_row_functional_body_and_envelope_are_frozen() -> None:
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
        label="Choose table-row functionality body",
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
        f"CHOOSE TABLE ROW FUNCTIONAL BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    assert EXPECTED_BODIES[TABLE_ROW_FUNCTIONAL] is not None, (
        f"freeze body receipt: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[TABLE_ROW_FUNCTIONAL] is not None, (
        f"freeze envelope receipt: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[TABLE_ROW_FUNCTIONAL]
    assert envelope == EXPECTED_ENVELOPES[TABLE_ROW_FUNCTIONAL]


@pytest.mark.parametrize(
    "dependency",
    EXPECTED_DEPENDENCIES[TABLE_ROW_FUNCTIONAL],
)
def test_choose_table_row_functional_every_direct_dependency_is_live(
    dependency: str,
) -> None:
    item = _specs()[0]
    shortened = replace(
        item,
        dependencies=tuple(
            name for name in item.dependencies if name != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_core())


def test_choose_table_row_functional_false_conclusion_is_rejected() -> None:
    item = _specs()[0]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_core())


def _boundary_mutations() -> tuple[tuple[str, str, str], ...]:
    variables = (
        "bb",
        "bc",
        "sb",
        "sc",
        "w",
        "r",
        "db",
        "dc",
        "eb",
        "ec",
        "v",
        "s",
        "i",
        "b",
        "c",
        "d",
        "e",
    )
    row_old = foundation._lt_term(
        "i", "s", tag="bptrpf_right_row_bound", variables=variables
    )
    row_new = foundation._le_term(
        "i", "s", tag="bptrpf_right_row_bound", variables=variables
    )

    agreement_variables = ("b", "c", "d", "e", "w", "v")
    index, left_value, right_value = foundation._binders(
        "bptrpf_agree",
        agreement_variables,
        ("index", "left_value", "right_value"),
    )
    owned = agreement_variables + (index, left_value, right_value)
    agreement_old = foundation._lt_term(
        index,
        "v",
        tag="bptrpf_agree_right_bound",
        variables=owned,
    )
    agreement_new = foundation._le_term(
        index,
        "v",
        tag="bptrpf_agree_right_bound",
        variables=owned,
    )
    cases = (
        ("allow_right_terminal_row", row_old, row_new),
        ("require_right_terminal_cell", agreement_old, agreement_new),
    )
    statement = _expected_statement()
    assert all(statement.count(old) == 1 for _case_id, old, _new in cases)
    return cases


def test_choose_table_row_functional_boundary_mutations_have_witnesses() -> None:
    # A weak row bound permits i=s, where the right table semantics is silent.
    assert 0 <= 0
    assert not 0 < 0
    # Likewise a weak inner bound demands agreement at the omitted terminal
    # cell, which neither finite-row relation constrains.
    assert 1 <= 1
    assert not 1 < 1


@pytest.mark.parametrize(
    ("case_id", "old", "new"),
    _boundary_mutations(),
    ids=tuple(case[0] for case in _boundary_mutations()),
)
def test_choose_table_row_functional_boundary_mutations_are_rejected(
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


def test_choose_table_row_functional_empty_context_closure_is_frozen() -> None:
    item = _specs()[0]
    formula, certificate = _close(TABLE_ROW_FUNCTIONAL)
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
        label="Choose table-row functionality closure",
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
    print(f"CHOOSE TABLE ROW FUNCTIONAL CLOSURE actual={actual!r}", flush=True)
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
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    assert EXPECTED_CLOSURES[TABLE_ROW_FUNCTIONAL] is not None, (
        f"freeze empty-context closure receipt: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[TABLE_ROW_FUNCTIONAL]
