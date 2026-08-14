"""Fail-closed audit for cross-encoding Pascal-row functionality.

The two candidates remain outside Stable and Alpha authority.  Static gates
pin their raw-PA surfaces and the committed Choose-foundation authoring source;
isolated execution gates deliberately remain closed until artifact, body,
envelope, and empty-context closure receipts are independently reproduced.
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
    bertrand_choose_row_functional_candidate as module,
    editions_v7,
    theorems as stable_module,
)
from peano_lab.library.bertrand_choose_row_functional_candidate import (
    make_bertrand_choose_row_functional_candidate_theorems,
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


ZERO_FUNCTIONAL = "beta_pascal_zero_row_pointwise_functional"
STEP_FUNCTIONAL = "beta_pascal_row_step_pointwise_functional"
EXPECTED_NAMES = (ZERO_FUNCTIONAL, STEP_FUNCTIONAL)

EXPECTED_DEPENDENCIES = {
    ZERO_FUNCTIONAL: ("beta_at_unique", "succ_ne_zero"),
    STEP_FUNCTIONAL: (
        "beta_at_unique",
        "succ_ne_zero",
        "succ_injective",
        "lt_to_le",
    ),
}

FOUNDATION_SOURCE_SHA256 = (
    "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d"
)

# None is deliberately fail-closed.  Receipts are reproducibility assertions,
# never theorem authority, enrollment evidence, or substitutes for the kernel.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    ZERO_FUNCTIONAL: (
        1_818,
        "8acab8a32bd1d6766db1c8cd480343e635b89c181597eaa8cb6892668621dfc7",
        "91509f94170936a662c04e067c285ffebebafbc6ebd1729a4793a7c642afbd9e",
        "94f06325d2021e19c63926c587d66584892e444699c3fcbf3c3bfd3eda1f84a3",
    ),
    STEP_FUNCTIONAL: (
        4_111,
        "49af702636a9537dfff811b30bde5be71e816c92c901d123f1990689e3060463",
        "e015a4700307f4cc8ffb68863dbccd357afa53c2dc83b6e78c96cfdaad4d5fe5",
        "0147d30df93c32af7942086863f82cb5d5bc27d7d412ae105aa718456cedd7f9",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    ZERO_FUNCTIONAL: (2, 93, 124, 35, 124, 123, 0),
    STEP_FUNCTIONAL: (4, 164, 251, 47, 251, 250, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    ZERO_FUNCTIONAL: (124, 124, 35, 24, 35),
    STEP_FUNCTIONAL: (251, 251, 47, 173, 51),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    ZERO_FUNCTIONAL: (
        1_246,
        60,
        817,
        853,
        37,
        3_254,
        60,
        "499633e5e274550920a7a4266ca69f3f87da55dba196086cf8677c9d05cfbd21",
    ),
    STEP_FUNCTIONAL: (
        1_418,
        60,
        962,
        999,
        38,
        4_649,
        60,
        "8508082ba60c72459cae9c6576fce5ccb6b2b58bed8827609dd0ee6c02c07e9a",
    ),
}


def _zero_statement() -> str:
    variables = ("b", "c", "d", "e", "w", "v", "i", "x", "y")
    left = foundation._pascal_zero_row(
        "b", "c", "w", tag="bzrpf_left"
    )
    right = foundation._pascal_zero_row(
        "d", "e", "v", tag="bzrpf_right"
    )
    left_bound = foundation._lt_term(
        "i", "w", tag="bzrpf_left_bound", variables=variables
    )
    right_bound = foundation._lt_term(
        "i", "v", tag="bzrpf_right_bound", variables=variables
    )
    left_at = foundation._beta_at_term(
        "b",
        "c",
        "i",
        "x",
        tag="bzrpf_left_at",
        variables=variables,
    )
    right_at = foundation._beta_at_term(
        "d",
        "e",
        "i",
        "y",
        tag="bzrpf_right_at",
        variables=variables,
    )
    return (
        "forall b c d e w v i x y. "
        f"({left}) -> ({right}) -> ({left_bound}) -> ({right_bound}) -> "
        f"({left_at}) -> ({right_at}) -> x = y"
    )


def _step_components() -> dict[str, str]:
    outer = ("pb", "pc", "qb", "qc", "b", "c", "d", "e", "w", "v")
    variables = outer + ("i", "x", "y")
    left = foundation._pascal_row_step(
        "pb", "pc", "b", "c", "w", tag="bpspf_left"
    )
    right = foundation._pascal_row_step(
        "qb", "qc", "d", "e", "v", tag="bpspf_right"
    )
    previous_left_bound = foundation._lt_term(
        "i",
        "w",
        tag="bpspf_previous_left_bound",
        variables=variables,
    )
    previous_right_bound = foundation._lt_term(
        "i",
        "v",
        tag="bpspf_previous_right_bound",
        variables=variables,
    )
    previous_left_at = foundation._beta_at_term(
        "pb",
        "pc",
        "i",
        "x",
        tag="bpspf_previous_left_at",
        variables=variables,
    )
    previous_right_at = foundation._beta_at_term(
        "qb",
        "qc",
        "i",
        "y",
        tag="bpspf_previous_right_at",
        variables=variables,
    )
    previous = (
        f"forall i x y. ({previous_left_bound}) -> "
        f"({previous_right_bound}) -> ({previous_left_at}) -> "
        f"({previous_right_at}) -> x = y"
    )
    current_left_bound = foundation._lt_term(
        "i", "w", tag="bpspf_current_left_bound", variables=variables
    )
    current_right_bound = foundation._lt_term(
        "i", "v", tag="bpspf_current_right_bound", variables=variables
    )
    current_left_at = foundation._beta_at_term(
        "b",
        "c",
        "i",
        "x",
        tag="bpspf_current_left_at",
        variables=variables,
    )
    current_right_at = foundation._beta_at_term(
        "d",
        "e",
        "i",
        "y",
        tag="bpspf_current_right_at",
        variables=variables,
    )
    current = (
        f"forall i x y. ({current_left_bound}) -> "
        f"({current_right_bound}) -> ({current_left_at}) -> "
        f"({current_right_at}) -> x = y"
    )
    return {
        "left": left,
        "right": right,
        "previous": previous,
        "current": current,
        "previous_left_bound": previous_left_bound,
        "current_right_bound": current_right_bound,
    }


def _step_statement() -> str:
    pieces = _step_components()
    return (
        "forall pb pc qb qc b c d e w v. "
        f"({pieces['left']}) -> ({pieces['right']}) -> "
        f"({pieces['previous']}) -> ({pieces['current']})"
    )


def _expected_statements() -> dict[str, str]:
    return {
        ZERO_FUNCTIONAL: _zero_statement(),
        STEP_FUNCTIONAL: _step_statement(),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    table = {item.name: item for item in rows}
    assert len(table) == len(rows)
    return table


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    assert not (set(EXPECTED_NAMES) & set(public))
    return public


def _row_core(row_name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(row_name)
    return _core() | {item.name: item for item in _specs()[:index]}


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
            raise AssertionError("row-functionality body delegated through use")
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
    dependency_proofs = tuple(_close(name) for name in item.dependencies)
    for dependency_formula, dependency_proof in reversed(dependency_proofs):
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


def test_choose_row_functional_foundation_source_is_pinned() -> None:
    path = Path(foundation.__file__)
    assert sha256(path.read_bytes()).hexdigest() == FOUNDATION_SOURCE_SHA256


def test_choose_row_functional_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    table = _table(rows)
    expected = _expected_statements()
    assert make_bertrand_choose_row_functional_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(table) == EXPECTED_NAMES
    assert len(rows) == len(set(EXPECTED_NAMES)) == 2
    assert {item.name: item.statement for item in rows} == expected
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_choose_row_functional_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert all(
        dependency in stable
        for dependencies in EXPECTED_DEPENDENCIES.values()
        for dependency in dependencies
    )

    provider_token = "bertrand_choose_row_functional_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    positions = {name: index for index, name in enumerate(EXPECTED_NAMES)}
    available = set(_core())
    for item in rows:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(dependency in available for dependency in item.dependencies)
        assert all(
            dependency not in positions
            or positions[dependency] < positions[item.name]
            for dependency in item.dependencies
        )
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
        available.add(item.name)


def test_choose_row_functional_public_binders_and_order_are_exact() -> None:
    statements = _expected_statements()
    zero = statements[ZERO_FUNCTIONAL]
    step = statements[STEP_FUNCTIONAL]
    pieces = _step_components()

    assert zero.startswith("forall b c d e w v i x y. ")
    assert zero.endswith("x = y")
    assert step.startswith("forall pb pc qb qc b c d e w v. ")
    assert step.endswith("x = y)")
    zero_left = foundation._pascal_zero_row(
        "b", "c", "w", tag="bzrpf_left"
    )
    zero_right = foundation._pascal_zero_row(
        "d", "e", "v", tag="bzrpf_right"
    )
    assert zero.find(zero_left) < zero.find(zero_right)
    assert zero.count("forall bcf_index_bzrpf_") == 2
    assert zero.count("exists bcf_lt_gap_bzrpf_") == 4
    assert zero.count("bcf_height_bzrpf_") == 8

    positions = tuple(
        step.find(pieces[name])
        for name in ("left", "right", "previous", "current")
    )
    assert positions == tuple(sorted(positions))
    assert all(position >= 0 for position in positions)
    assert step.count("forall i x y.") == 2


def test_choose_row_functional_authoring_helpers_are_hygienic() -> None:
    zero_a = foundation._pascal_zero_row("b", "c", "w", tag="hygiene_a")
    zero_b = foundation._pascal_zero_row("b", "c", "w", tag="hygiene_b")
    assert zero_a != zero_b
    parsed_zero_a, free_zero_a = parse_formula_with_names(zero_a)
    parsed_zero_b, free_zero_b = parse_formula_with_names(zero_b)
    assert parsed_zero_a == parsed_zero_b
    assert set(free_zero_a) == set(free_zero_b) == {"b", "c", "w"}

    step_a = foundation._pascal_row_step(
        "pb", "pc", "b", "c", "w", tag="hygiene_a"
    )
    step_b = foundation._pascal_row_step(
        "pb", "pc", "b", "c", "w", tag="hygiene_b"
    )
    assert step_a != step_b
    parsed_step_a, free_step_a = parse_formula_with_names(step_a)
    parsed_step_b, free_step_b = parse_formula_with_names(step_b)
    assert parsed_step_a == parsed_step_b
    assert set(free_step_a) == set(free_step_b) == {
        "pb",
        "pc",
        "b",
        "c",
        "w",
    }

    cell_a = module._zero_row_cell("b", "c", "i", tag="hygiene_a")
    cell_b = module._zero_row_cell("b", "c", "i", tag="hygiene_b")
    assert cell_a != cell_b
    parsed_cell_a, free_cell_a = parse_formula_with_names(cell_a)
    parsed_cell_b, free_cell_b = parse_formula_with_names(cell_b)
    assert parsed_cell_a == parsed_cell_b
    assert set(free_cell_a) == set(free_cell_b) == {"b", "c", "i"}

    with pytest.raises(ValueError):
        foundation._pascal_zero_row(
            "bcf_index_valid", "c", "w", tag="valid"
        )
    with pytest.raises(ValueError):
        module._zero_row_cell("S", "c", "i", tag="valid")
    with pytest.raises(ValueError):
        module._row_step_cell(
            "pb", "pc", "b", "c", "i", tag="bad tag"
        )


def test_choose_row_functional_receipt_manifests_are_fail_closed() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_choose_row_functional_artifact_receipts_are_frozen(
    row_name: str,
) -> None:
    item = _table(_specs())[row_name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(
        f"CHOOSE ROW FUNCTIONAL ARTIFACT row={row_name!r} "
        f"actual={actual!r}",
        flush=True,
    )
    assert EXPECTED_ARTIFACTS[row_name] is not None, (
        f"freeze deterministic artifact receipt for {row_name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[row_name]


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_choose_row_functional_bodies_and_envelopes_are_frozen(
    row_name: str,
) -> None:
    item = _table(_specs())[row_name]
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
        label=f"Choose row-functional body {row_name}",
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
        f"CHOOSE ROW FUNCTIONAL BODY row={row_name!r} actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    assert EXPECTED_BODIES[row_name] is not None, (
        f"freeze body receipt for {row_name}: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[row_name] is not None, (
        f"freeze envelope receipt for {row_name}: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[row_name]
    assert envelope == EXPECTED_ENVELOPES[row_name]


@pytest.mark.parametrize(
    ("row_name", "dependency"),
    tuple(
        (row_name, dependency)
        for row_name, dependencies in EXPECTED_DEPENDENCIES.items()
        for dependency in dependencies
    ),
)
def test_choose_row_functional_every_direct_dependency_is_live(
    row_name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[row_name]
    shortened = replace(
        item,
        dependencies=tuple(
            name for name in item.dependencies if name != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(row_name))


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_choose_row_functional_false_conclusions_are_rejected(
    row_name: str,
) -> None:
    item = _table(_specs())[row_name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(row_name))


def _boundary_mutations() -> tuple[tuple[str, str, str, str], ...]:
    zero_variables = ("b", "c", "d", "e", "w", "v", "i", "x", "y")
    zero_old = foundation._lt_term(
        "i", "v", tag="bzrpf_right_bound", variables=zero_variables
    )
    zero_new = foundation._le_term(
        "i", "v", tag="bzrpf_right_bound", variables=zero_variables
    )

    step_outer = (
        "pb",
        "pc",
        "qb",
        "qc",
        "b",
        "c",
        "d",
        "e",
        "w",
        "v",
    )
    step_variables = step_outer + ("i", "x", "y")
    previous_old = foundation._lt_term(
        "i",
        "w",
        tag="bpspf_previous_left_bound",
        variables=step_variables,
    )
    previous_new = foundation._lt_term(
        "S i",
        "w",
        tag="bpspf_previous_left_bound",
        variables=step_variables,
    )
    current_old = foundation._lt_term(
        "i",
        "v",
        tag="bpspf_current_right_bound",
        variables=step_variables,
    )
    current_new = foundation._le_term(
        "i",
        "v",
        tag="bpspf_current_right_bound",
        variables=step_variables,
    )
    cases = (
        (
            "zero__allow_right_terminal_index",
            ZERO_FUNCTIONAL,
            zero_old,
            zero_new,
        ),
        (
            "step__omit_previous_terminal_index",
            STEP_FUNCTIONAL,
            previous_old,
            previous_new,
        ),
        (
            "step__allow_current_right_terminal_index",
            STEP_FUNCTIONAL,
            current_old,
            current_new,
        ),
    )
    statements = _expected_statements()
    assert all(
        statements[row_name].count(old) == 1
        for _case_id, row_name, old, _new in cases
    )
    return cases


def test_choose_row_functional_boundary_mutations_have_standard_witnesses(
) -> None:
    # Zero-row mutation: i=0 is below width 1 and only weakly below width 0;
    # the width-zero semantic premise is vacuous, so its external entry need
    # not equal the forced value 1 of the nonempty row.
    assert 0 < 1
    assert 0 <= 0
    assert not 0 < 0
    assert 1 != 0

    # Step mutation: for width 2, strengthening the previous-row premise to
    # S i < 2 omits index 1, although the current value at index 1 consumes
    # both predecessor entries 0 and 1.
    covered = tuple(index for index in range(2) if index + 1 < 2)
    assert covered == (0,)
    assert 1 not in covered


@pytest.mark.parametrize(
    ("case_id", "row_name", "old", "new"),
    _boundary_mutations(),
    ids=tuple(case[0] for case in _boundary_mutations()),
)
def test_choose_row_functional_genuine_boundary_mutations_are_rejected(
    case_id: str,
    row_name: str,
    old: str,
    new: str,
) -> None:
    del case_id
    item = _table(_specs())[row_name]
    assert item.statement.count(old) == 1
    mutated = replace(item, statement=item.statement.replace(old, new, 1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(row_name))


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_choose_row_functional_empty_context_closures_are_frozen(
    row_name: str,
) -> None:
    item = _table(_specs())[row_name]
    formula, certificate = _close(row_name)
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
        label=f"Choose row-functional closure {row_name}",
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
    print(
        f"CHOOSE ROW FUNCTIONAL CLOSURE row={row_name!r} "
        f"actual={actual!r}",
        flush=True,
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
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    assert EXPECTED_CLOSURES[row_name] is not None, (
        f"freeze empty-context closure receipt for {row_name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[row_name]
