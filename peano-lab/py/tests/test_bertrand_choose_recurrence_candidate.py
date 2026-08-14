"""Fail-closed audit for the first constructive Choose recurrence tranche.

The two candidates remain outside Stable and Alpha authority.  The first row
extracts the exact Pascal recurrence from a decoded successor table cell; the
second transports those predecessor values across independent Choose tables.
All expected formulas below are rebuilt from the committed foundation helpers
rather than copied from the candidate factory.  Receipts deliberately start
as ``None`` and must be frozen only after isolated body replay and unchanged-
kernel empty-context closure succeed.
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
    bertrand_choose_laws_candidate as laws_module,
    bertrand_choose_recurrence_candidate as module,
    bertrand_choose_row_functional_candidate as row_support_module,
    bertrand_choose_table_row_functional_candidate as table_support_module,
    editions_v7,
    theorems as stable_module,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    make_bertrand_choose_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_laws_candidate import (
    make_bertrand_choose_laws_candidate_theorems,
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


SUCCESSOR_CELL_RECURRENCE = (
    "beta_pascal_table_successor_cell_recurrence"
)
CHOOSE_SUCC_SUCC_OF_LT = "choose_succ_succ_of_lt"
EXPECTED_NAMES = (SUCCESSOR_CELL_RECURRENCE, CHOOSE_SUCC_SUCC_OF_LT)

ROW_SUPPORT_NAMES = (
    "beta_pascal_zero_row_pointwise_functional",
    "beta_pascal_row_step_pointwise_functional",
)
TABLE_ROW_FUNCTIONAL = "beta_pascal_table_row_pointwise_functional"

EXPECTED_DEPENDENCIES = {
    SUCCESSOR_CELL_RECURRENCE: (
        "beta_at_unique",
        "succ_ne_zero",
        "succ_injective",
    ),
    CHOOSE_SUCC_SUCC_OF_LT: (
        "lt_not_le",
        "lt_to_le",
        "le_refl",
        "le_succ",
        "succ_le_succ",
        TABLE_ROW_FUNCTIONAL,
        SUCCESSOR_CELL_RECURRENCE,
    ),
}
EXPECTED_DIRECT_CUTS = {
    SUCCESSOR_CELL_RECURRENCE: 3,
    CHOOSE_SUCC_SUCC_OF_LT: 7,
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
CHOOSE_LAWS_SOURCE_SHA256 = (
    "1a9001823508470d6b6164c6df00cbb4761e6f67e4a19bd114c7aad469860c5d"
)

# Fail-closed sentinels.  These are reproducibility receipts, never theorem
# authority, enrollment evidence, or substitutes for the kernel.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    SUCCESSOR_CELL_RECURRENCE: (
        7257,
        "41705b00e354c3ab6ae73236a8c718985c0f7b69dc4a6c5fbccdc466c80628c9",
        "5930088245a0690682f55104314760a7cef59d0f93f4e57c5b3be584181b3cc3",
        "1fff15b233665e6ecefa1b30e2875f8686f196bf928768b7906277eec9e824cc",
    ),
    CHOOSE_SUCC_SUCC_OF_LT: (
        22256,
        "55c25ccefb1f8bd85a20b20698570b5c314b2acae386b6bea927403e2a704f2d",
        "92521df4bf980c41fba8c88135c497d7fc063075d273fc764452236b1821d54e",
        "62a000adb47beeec4f348808a84e36f152a2417e4d9cced302e8e64490a27e16",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    SUCCESSOR_CELL_RECURRENCE: (3, 128, 206, 53, 206, 205, 0),
    CHOOSE_SUCC_SUCC_OF_LT: (7, 206, 311, 76, 311, 310, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    SUCCESSOR_CELL_RECURRENCE: (206, 206, 53, 324, 55),
    CHOOSE_SUCC_SUCC_OF_LT: (311, 311, 76, 128, 76),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    SUCCESSOR_CELL_RECURRENCE: (
        1329,
        60,
        900,
        936,
        37,
        4717,
        60,
        "73ba66b8ef1427938e41157f2ff996533ad2f0dd67df6282e6b1ba18caf15e0f",
    ),
    CHOOSE_SUCC_SUCC_OF_LT: (
        6116,
        81,
        2160,
        2209,
        50,
        32421,
        83,
        "4ae55847742e2c629a7492f03259e4462916fe1ed2a6fdea48b08534fa4bf584",
    ),
}


TABLE_SURFACE_VARIABLES = (
    "bb",
    "bc",
    "sb",
    "sc",
    "w",
    "r",
    "i",
    "j",
    "b",
    "c",
    "z",
)
CHOOSE_SURFACE_VARIABLES = ("n", "k", "x", "y", "z")
RESULT_STEMS = (
    "previous_code",
    "previous_scale",
    "left_value",
    "right_value",
)


def _successor_cell_result(
    row_code_code: str,
    row_code_scale: str,
    row_scale_code: str,
    row_scale_scale: str,
    row_index_term: str,
    cell_index_term: str,
    value_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Independently rebuild the frozen right-associated result payload."""

    previous_code, previous_scale, left_value, right_value = (
        foundation._binders(tag, variables, RESULT_STEMS)
    )
    owned = variables + (
        previous_code,
        previous_scale,
        left_value,
        right_value,
    )
    previous_code_at = foundation._beta_at_term(
        row_code_code,
        row_code_scale,
        row_index_term,
        previous_code,
        tag=f"{tag}_previous_code_at",
        variables=owned,
    )
    previous_scale_at = foundation._beta_at_term(
        row_scale_code,
        row_scale_scale,
        row_index_term,
        previous_scale,
        tag=f"{tag}_previous_scale_at",
        variables=owned,
    )
    left_at = foundation._beta_at_term(
        previous_code,
        previous_scale,
        cell_index_term,
        left_value,
        tag=f"{tag}_left_at",
        variables=owned,
    )
    right_at = foundation._beta_at_term(
        previous_code,
        previous_scale,
        f"S ({cell_index_term})",
        right_value,
        tag=f"{tag}_right_at",
        variables=owned,
    )
    return (
        f"exists {previous_code} {previous_scale} "
        f"{left_value} {right_value}. "
        f"({previous_code_at}) /\\ (({previous_scale_at}) /\\ "
        f"(({left_at}) /\\ (({right_at}) /\\ "
        f"{value_term} = {left_value} + {right_value})))"
    )


def _expected_statements() -> dict[str, str]:
    table = foundation._pascal_table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptscr_table"
    )
    row_bound = foundation._lt_term(
        "S i",
        "r",
        tag="bptscr_row_bound",
        variables=TABLE_SURFACE_VARIABLES,
    )
    cell_bound = foundation._lt_term(
        "S j",
        "w",
        tag="bptscr_cell_bound",
        variables=TABLE_SURFACE_VARIABLES,
    )
    row_code_at = foundation._beta_at_term(
        "bb",
        "bc",
        "S i",
        "b",
        tag="bptscr_row_code_at",
        variables=TABLE_SURFACE_VARIABLES,
    )
    row_scale_at = foundation._beta_at_term(
        "sb",
        "sc",
        "S i",
        "c",
        tag="bptscr_row_scale_at",
        variables=TABLE_SURFACE_VARIABLES,
    )
    current_at = foundation._beta_at_term(
        "b",
        "c",
        "S j",
        "z",
        tag="bptscr_current_at",
        variables=TABLE_SURFACE_VARIABLES,
    )
    result = _successor_cell_result(
        "bb",
        "bc",
        "sb",
        "sc",
        "i",
        "j",
        "z",
        tag="bptscr_result",
        variables=TABLE_SURFACE_VARIABLES,
    )

    choose_bound = foundation._lt_term(
        "k",
        "n",
        tag="bcssol_bound",
        variables=CHOOSE_SURFACE_VARIABLES,
    )
    choose_left = foundation._choose_relation_term(
        "n",
        "k",
        "x",
        tag="bcssol_left",
        variables=CHOOSE_SURFACE_VARIABLES,
    )
    choose_right = foundation._choose_relation_term(
        "n",
        "S k",
        "y",
        tag="bcssol_right",
        variables=CHOOSE_SURFACE_VARIABLES,
    )
    choose_result = foundation._choose_relation_term(
        "S n",
        "S k",
        "z",
        tag="bcssol_result",
        variables=CHOOSE_SURFACE_VARIABLES,
    )

    return {
        SUCCESSOR_CELL_RECURRENCE: (
            "forall bb bc sb sc w r i j b c z. "
            f"({table}) -> ({row_bound}) -> ({cell_bound}) -> "
            f"({row_code_at}) -> ({row_scale_at}) -> "
            f"({current_at}) -> ({result})"
        ),
        CHOOSE_SUCC_SUCC_OF_LT: (
            "forall n k x y z. "
            f"({choose_bound}) -> ({choose_left}) -> "
            f"({choose_right}) -> ({choose_result}) -> z = x + y"
        ),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_recurrence_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    """Rebuild the full unregistered predecessor lineage recursively."""

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
            raise AssertionError("Choose recurrence delegated through use")
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


def test_choose_recurrence_predecessor_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_support_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_support_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
        (laws_module, CHOOSE_LAWS_SOURCE_SHA256),
    )
    for predecessor, digest in expected:
        assert sha256(Path(predecessor.__file__).read_bytes()).hexdigest() == digest


def test_choose_recurrence_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    expected = _expected_statements()
    assert make_bertrand_choose_recurrence_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_choose_recurrence_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    support = set(_table(_support_specs()))
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & support)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert set(ROW_SUPPORT_NAMES) <= support
    assert TABLE_ROW_FUNCTIONAL in support
    assert all(
        dependency in _available()
        for item in rows
        for dependency in item.dependencies
    )

    provider_token = "bertrand_choose_recurrence_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    forbidden_surface = (
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
    for item in rows:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden_surface)
        assert all(
            token not in command
            for command in item.script
            for token in forbidden_script
        )


def test_choose_recurrence_public_binders_and_topology_are_exact() -> None:
    rows = _table(_specs())
    table_row = rows[SUCCESSOR_CELL_RECURRENCE]
    choose_row = rows[CHOOSE_SUCC_SUCC_OF_LT]
    assert table_row.statement.startswith(
        "forall bb bc sb sc w r i j b c z. ("
    )
    assert choose_row.statement.startswith("forall n k x y z. (")
    assert choose_row.statement.endswith("z = x + y")
    assert table_row.script[:17] == (
        "intro bb",
        "intro bc",
        "intro sb",
        "intro sc",
        "intro w",
        "intro r",
        "intro i",
        "intro j",
        "intro b",
        "intro c",
        "intro z",
        "intro htable",
        "intro hrow_bound",
        "intro hcell_bound",
        "intro hrow_code",
        "intro hrow_scale",
        "intro hcurrent",
    )
    assert table_row.script.count("apply succ_injective") == 2
    assert table_row.script.count("apply succ_ne_zero") == 2
    assert choose_row.script.count(
        "apply beta_pascal_table_row_pointwise_functional"
    ) == 2
    assert choose_row.script.count(
        "apply beta_pascal_table_successor_cell_recurrence"
    ) == 1
    assert not any(
        command.startswith("induction ")
        for item in rows.values()
        for command in item.script
    )


def test_choose_recurrence_authoring_helpers_are_hygienic() -> None:
    result_variables = ("bb", "bc", "sb", "sc", "i", "j", "z")
    result_left = module._successor_cell_result_term(
        "bb",
        "bc",
        "sb",
        "sc",
        "i",
        "j",
        "z",
        tag="hygiene_left",
        variables=result_variables,
    )
    result_right = module._successor_cell_result_term(
        "bb",
        "bc",
        "sb",
        "sc",
        "i",
        "j",
        "z",
        tag="hygiene_right",
        variables=result_variables,
    )
    parsed_left, free_left = parse_formula_with_names(result_left)
    parsed_right, free_right = parse_formula_with_names(result_right)
    assert result_left != result_right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == set(result_variables)

    agreement_variables = ("b", "c", "d", "e", "w", "v")
    agreement_left = module._row_pointwise_agreement_term(
        "b",
        "c",
        "d",
        "e",
        "S w",
        "S v",
        tag="agreement_left",
        variables=agreement_variables,
    )
    agreement_right = module._row_pointwise_agreement_term(
        "b",
        "c",
        "d",
        "e",
        "S w",
        "S v",
        tag="agreement_right",
        variables=agreement_variables,
    )
    parsed_agreement_left, free_agreement_left = parse_formula_with_names(
        agreement_left
    )
    parsed_agreement_right, free_agreement_right = parse_formula_with_names(
        agreement_right
    )
    assert agreement_left != agreement_right
    assert parsed_agreement_left == parsed_agreement_right
    assert set(free_agreement_left) == set(free_agreement_right) == set(
        agreement_variables
    )

    with pytest.raises(ValueError):
        module._successor_cell_result_term(
            "bb",
            "bc",
            "sb",
            "sc",
            "i",
            "j",
            "z",
            tag="valid",
            variables=result_variables + ("bcf_previous_code_valid",),
        )
    with pytest.raises(ValueError):
        module._row_pointwise_agreement_term(
            "b",
            "c",
            "d",
            "e",
            "w",
            "v",
            tag="valid",
            variables=agreement_variables + ("bcf_index_valid",),
        )
    with pytest.raises(ValueError):
        module._successor_cell_result_term(
            "bb",
            "bc",
            "sb",
            "sc",
            "i",
            "j",
            "z",
            tag="bad tag",
            variables=result_variables,
        )


def test_choose_recurrence_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_recurrence_artifact_receipts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CHOOSE RECURRENCE ARTIFACT {name} actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_recurrence_bodies_and_envelopes_are_frozen(name: str) -> None:
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
        label=f"Choose recurrence {name} body",
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
        f"CHOOSE RECURRENCE BODY {name} actual={actual!r} "
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
def test_choose_recurrence_every_direct_dependency_is_live(
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
def test_choose_recurrence_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    current_old = foundation._beta_at_term(
        "b",
        "c",
        "S j",
        "z",
        tag="bptscr_current_at",
        variables=TABLE_SURFACE_VARIABLES,
    )
    current_new = foundation._beta_at_term(
        "b",
        "c",
        "j",
        "z",
        tag="bptscr_current_at",
        variables=TABLE_SURFACE_VARIABLES,
    )
    previous_code, previous_scale, left_value, right_value = (
        foundation._binders(
            "bptscr_result",
            TABLE_SURFACE_VARIABLES,
            RESULT_STEMS,
        )
    )
    owned = TABLE_SURFACE_VARIABLES + (
        previous_code,
        previous_scale,
        left_value,
        right_value,
    )
    returned_right_old = foundation._beta_at_term(
        previous_code,
        previous_scale,
        "S (j)",
        right_value,
        tag="bptscr_result_right_at",
        variables=owned,
    )
    returned_right_new = foundation._beta_at_term(
        previous_code,
        previous_scale,
        "j",
        right_value,
        tag="bptscr_result_right_at",
        variables=owned,
    )
    choose_right_old = foundation._choose_relation_term(
        "n",
        "S k",
        "y",
        tag="bcssol_right",
        variables=CHOOSE_SURFACE_VARIABLES,
    )
    choose_right_new = foundation._choose_relation_term(
        "n",
        "k",
        "y",
        tag="bcssol_right",
        variables=CHOOSE_SURFACE_VARIABLES,
    )
    choose_result_old = foundation._choose_relation_term(
        "S n",
        "S k",
        "z",
        tag="bcssol_result",
        variables=CHOOSE_SURFACE_VARIABLES,
    )
    choose_result_new = foundation._choose_relation_term(
        "n",
        "S k",
        "z",
        tag="bcssol_result",
        variables=CHOOSE_SURFACE_VARIABLES,
    )
    cases = (
        (
            SUCCESSOR_CELL_RECURRENCE,
            "current_cell_without_successor",
            current_old,
            current_new,
        ),
        (
            SUCCESSOR_CELL_RECURRENCE,
            "returned_right_without_successor",
            returned_right_old,
            returned_right_new,
        ),
        (
            CHOOSE_SUCC_SUCC_OF_LT,
            "right_column_without_successor",
            choose_right_old,
            choose_right_new,
        ),
        (
            CHOOSE_SUCC_SUCC_OF_LT,
            "result_row_without_successor",
            choose_result_old,
            choose_result_new,
        ),
    )
    statements = _expected_statements()
    assert all(
        statements[name].count(old) == 1
        for name, _case_id, old, _new in cases
    )
    return cases


def test_choose_recurrence_mutations_have_standard_witnesses() -> None:
    # Row two at cell one is 2, not row-one cells one plus two (= 1).
    assert 2 != 1 + 0
    # Row one at cell one is 1, not twice row-zero cell zero (= 2).
    assert 1 != 1 + 1
    # C(3,1)=3, while C(2,0)+C(2,0)=2.
    assert 3 != 1 + 1
    # C(2,1)=2, while C(2,0)+C(2,1)=3.
    assert 2 != 1 + 2


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_choose_recurrence_genuine_mutations_are_rejected(
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
def test_choose_recurrence_empty_context_closures_are_frozen(
    name: str,
) -> None:
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
        label=f"Choose recurrence {name} closure",
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
    print(f"CHOOSE RECURRENCE CLOSURE {name} actual={actual!r}", flush=True)
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
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[name]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze empty-context closure receipt: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
