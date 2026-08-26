"""Fail-closed audit for the first recurrence-defined Choose laws.

The three candidates stay outside Stable and Alpha authority.  Static gates
pin their expanded raw-PA surfaces and all committed predecessor sources.
Execution gates remain closed until deterministic artifact, body, envelope,
and independent empty-context closure receipts have been reproduced.
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
    bertrand_choose_laws_candidate as module,
    bertrand_choose_row_functional_candidate as row_support_module,
    bertrand_choose_table_row_functional_candidate as table_support_module,
    editions_v7,
    theorems as stable_module,
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


CHOOSE_FUNCTIONAL = "choose_functional"
CHOOSE_OUT_OF_RANGE_ZERO = "choose_out_of_range_zero"
CHOOSE_ZERO = "choose_zero"
EXPECTED_NAMES = (
    CHOOSE_FUNCTIONAL,
    CHOOSE_OUT_OF_RANGE_ZERO,
    CHOOSE_ZERO,
)
SUPPORT_NAMES = (
    "beta_pascal_zero_row_pointwise_functional",
    "beta_pascal_row_step_pointwise_functional",
    "beta_pascal_table_row_pointwise_functional",
)
EXPECTED_DEPENDENCIES = {
    CHOOSE_FUNCTIONAL: (
        "lt_not_le",
        "le_refl",
        "succ_le_succ",
        SUPPORT_NAMES[2],
    ),
    CHOOSE_OUT_OF_RANGE_ZERO: ("lt_not_le",),
    CHOOSE_ZERO: (
        "zero_le",
        "lt_not_le",
        "le_refl",
        "succ_le_succ",
        "succ_ne_zero",
        "beta_at_unique",
    ),
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

# None is deliberately fail-closed.  Receipts are reproducibility assertions,
# never theorem authority, enrollment evidence, or substitutes for the kernel.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CHOOSE_FUNCTIONAL: (
        13_964,
        "16d6f030614cd588035c6b8543fea4a3bc992ba27b9bdbf10eb011c18d659e7b",
        "4acac1568abf4d20970de87fb909fd47024cf0c3faae520e0fc557f14e7180eb",
        "e0e2437f58eb24a250df10904b6a6e50182da770ec8f8ec726e3c3d0911ace8b",
    ),
    CHOOSE_OUT_OF_RANGE_ZERO: (
        7_627,
        "fca50599b7293c5e4580858815d05005d325f2712ff4a919626f7460f3c468fe",
        "1e46329dc7b4ac4242c5ae3472824f50069757c107242c999cc03348d7fd5979",
        "3f66db3d5a5e782fb56849d30b4a80654fdf73e157879c74bffc0a19f07c69a9",
    ),
    CHOOSE_ZERO: (
        7_230,
        "e21abead73e5ab69cb78d7eeaafad85fcba534923ac6f38ec4cc9640d6233340",
        "1d9ae92221439a634be1dad1c59768051f5c21ef2ff2369a6c696d6376c07554",
        "29fd7273cadaa6faea031af1ef4b89c6fd949a6eeb84aacb3b4969b5bc20e6aa",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    CHOOSE_FUNCTIONAL: (4, 92, 143, 57, 143, 142, 0),
    CHOOSE_OUT_OF_RANGE_ZERO: (1, 15, 39, 19, 39, 38, 0),
    CHOOSE_ZERO: (6, 130, 231, 38, 231, 230, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CHOOSE_FUNCTIONAL: (143, 143, 57, 36, 57),
    CHOOSE_OUT_OF_RANGE_ZERO: (39, 39, 19, 2, 19),
    CHOOSE_ZERO: (231, 231, 38, 200, 39),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CHOOSE_FUNCTIONAL: (
        4_535,
        79,
        1_773,
        1_817,
        45,
        21_605,
        81,
        "3e725ec2d3c70af84f988265d839b110b34b52640e5fd8516ee3ceb239f54c8b",
    ),
    CHOOSE_OUT_OF_RANGE_ZERO: (
        95,
        24,
        95,
        94,
        0,
        490,
        49,
        "6a16a27f00aadedaf933a534350f7648af998db99dc610b4ae80718526227406",
    ),
    CHOOSE_ZERO: (
        1_454,
        65,
        1_008,
        1_045,
        38,
        5_604,
        65,
        "fa2400179ebc8a6250dcefdbe467189f27966e7cfc8fb8ebdac147564d52a3d7",
    ),
}


def _expected_statements() -> dict[str, str]:
    functional_left = foundation._choose_relation(
        "n", "k", "x", tag="bclf_left"
    )
    functional_right = foundation._choose_relation(
        "n", "k", "y", tag="bclf_right"
    )
    out_bound = foundation._lt_term(
        "n", "k", tag="bcloor_bound", variables=("n", "k", "z")
    )
    out_choose = foundation._choose_relation(
        "n", "k", "z", tag="bcloor_choose"
    )
    zero_choose = foundation._choose_relation_term(
        "n", "0", "z", tag="bclz_choose", variables=("n", "z")
    )
    return {
        CHOOSE_FUNCTIONAL: (
            "forall n k x y. "
            f"({functional_left}) -> ({functional_right}) -> x = y"
        ),
        CHOOSE_OUT_OF_RANGE_ZERO: (
            "forall n k z. "
            f"({out_bound}) -> ({out_choose}) -> z = 0"
        ),
        CHOOSE_ZERO: f"forall n z. ({zero_choose}) -> z = 1",
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_laws_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_table_row_functional_candidate_theorems(
            TheoremSpec
        ),
    )


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


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
            raise AssertionError("Choose law delegated through use")
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


def test_choose_law_predecessor_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_support_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_support_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
    )
    for predecessor, digest in expected:
        assert sha256(Path(predecessor.__file__).read_bytes()).hexdigest() == digest


def test_choose_law_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    expected_statements = _expected_statements()
    assert make_bertrand_choose_laws_candidate_theorems(TheoremSpec) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        expected_statements[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_choose_laws_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert all(
        dependency in _core()
        for item in rows
        for dependency in item.dependencies
    )

    provider_token = "bertrand_choose_laws_candidate"
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


def test_choose_law_public_surfaces_and_script_topology_are_exact() -> None:
    rows = _table(_specs())
    assert rows[CHOOSE_FUNCTIONAL].statement.startswith("forall n k x y. ")
    assert rows[CHOOSE_FUNCTIONAL].statement.endswith("x = y")
    assert rows[CHOOSE_OUT_OF_RANGE_ZERO].statement.startswith(
        "forall n k z. "
    )
    assert rows[CHOOSE_OUT_OF_RANGE_ZERO].statement.endswith("z = 0")
    assert rows[CHOOSE_ZERO].statement.startswith("forall n z. ")
    assert rows[CHOOSE_ZERO].statement.endswith("z = 1")
    assert sum(
        command.startswith("have hagree : ")
        for command in rows[CHOOSE_FUNCTIONAL].script
    ) == 1
    assert rows[CHOOSE_ZERO].script.count("rewrite <- hscale") == 2
    assert not any(
        command.startswith("exists ")
        for item in rows.values()
        for command in item.script
    )


def test_choose_law_term_helpers_are_hygienic() -> None:
    variables = ("b", "c", "d", "e", "n")
    agree_a = module._row_pointwise_agreement_term(
        "b",
        "c",
        "d",
        "e",
        "S n",
        "S n",
        tag="hygiene_a",
        variables=variables,
    )
    agree_b = module._row_pointwise_agreement_term(
        "b",
        "c",
        "d",
        "e",
        "S n",
        "S n",
        tag="hygiene_b",
        variables=variables,
    )
    parsed_a, free_a = parse_formula_with_names(agree_a)
    parsed_b, free_b = parse_formula_with_names(agree_b)
    assert agree_a != agree_b
    assert parsed_a == parsed_b
    assert set(free_a) == set(free_b) == {"b", "c", "d", "e", "n"}

    row_a = module._table_row_cell_term(
        "bb",
        "bc",
        "sb",
        "sc",
        "S n",
        "n",
        tag="hygiene_a",
        variables=("bb", "bc", "sb", "sc", "n"),
    )
    row_b = module._table_row_cell_term(
        "bb",
        "bc",
        "sb",
        "sc",
        "S n",
        "n",
        tag="hygiene_b",
        variables=("bb", "bc", "sb", "sc", "n"),
    )
    parsed_row_a, free_row_a = parse_formula_with_names(row_a)
    parsed_row_b, free_row_b = parse_formula_with_names(row_b)
    assert row_a != row_b
    assert parsed_row_a == parsed_row_b
    assert set(free_row_a) == set(free_row_b) == {"bb", "bc", "sb", "sc", "n"}

    with pytest.raises(ValueError):
        module._zero_row_cell(
            "bcf_cell_value_valid",
            "c",
            "0",
            tag="valid",
            variables=("bcf_cell_value_valid", "c"),
        )
    with pytest.raises(ValueError):
        module._row_pointwise_agreement_term(
            "b",
            "c",
            "d",
            "e",
            "S n",
            "S n",
            tag="bad tag",
            variables=variables,
        )


def test_choose_law_receipt_manifests_are_fail_closed() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_law_artifact_receipts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CHOOSE LAW ARTIFACT {name} actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_law_bodies_and_envelopes_are_frozen(name: str) -> None:
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
        label=f"Choose law {name} body",
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
        f"CHOOSE LAW BODY {name} actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    assert EXPECTED_BODIES[name] is not None, f"freeze body receipt: {actual!r}"
    assert EXPECTED_ENVELOPES[name] is not None, (
        f"freeze envelope receipt: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


DIRECT_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


@pytest.mark.parametrize(("name", "dependency"), DIRECT_EDGES)
def test_choose_law_every_direct_dependency_is_live(
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
        replay_candidate_bodies((shortened,), core=_core())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_law_false_conclusions_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_core())


def _boundary_mutations() -> tuple[tuple[str, str, str, str], ...]:
    functional_old = foundation._choose_relation(
        "n", "k", "y", tag="bclf_right"
    )
    functional_new = foundation._choose_relation_term(
        "S n",
        "k",
        "y",
        tag="bclf_right",
        variables=("n", "k", "y"),
    )
    out_old = foundation._lt_term(
        "n", "k", tag="bcloor_bound", variables=("n", "k", "z")
    )
    out_new = foundation._le_term(
        "n", "k", tag="bcloor_bound", variables=("n", "k", "z")
    )
    zero_old = foundation._choose_relation_term(
        "n", "0", "z", tag="bclz_choose", variables=("n", "z")
    )
    zero_new = foundation._choose_relation_term(
        "n", "S 0", "z", tag="bclz_choose", variables=("n", "z")
    )
    cases = (
        (
            CHOOSE_FUNCTIONAL,
            "successor_right_row",
            functional_old,
            functional_new,
        ),
        (
            CHOOSE_OUT_OF_RANGE_ZERO,
            "allow_equal_indices",
            out_old,
            out_new,
        ),
        (CHOOSE_ZERO, "successor_column", zero_old, zero_new),
    )
    statements = _expected_statements()
    assert all(
        statements[name].count(old) == 1
        for name, _case, old, _new in cases
    )
    return cases


def test_choose_law_boundary_mutations_have_standard_witnesses() -> None:
    # C(1,1)=1 while C(2,1)=2, refuting the shifted right-row law.
    assert 1 != 2
    # n=k=0 satisfies the weakened n<=k premise, but C(0,0)=1.
    assert 0 <= 0 and 1 != 0
    # C(2,1)=2, so the successor-column variant of choose_zero is false.
    assert 2 != 1


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _boundary_mutations(),
    ids=tuple(case[1] for case in _boundary_mutations()),
)
def test_choose_law_genuine_boundary_mutations_are_rejected(
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
        replay_candidate_bodies((mutated,), core=_core())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_law_empty_context_closures_are_frozen(name: str) -> None:
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
        label=f"Choose law {name} closure",
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
    print(f"CHOOSE LAW CLOSURE {name} actual={actual!r}", flush=True)
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

    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze empty-context closure receipt: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
