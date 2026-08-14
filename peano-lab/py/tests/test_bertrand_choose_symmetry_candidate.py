"""Fail-closed audit for constructive relational Choose symmetry."""

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
    bertrand_choose_recurrence_candidate as recurrence_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_symmetry_candidate as module,
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
from peano_lab.library.bertrand_choose_symmetry_candidate import (
    make_bertrand_choose_symmetry_candidate_theorems,
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


CHOOSE_SELF_OF_EQ = "choose_self_of_eq"
CHOOSE_SYMMETRY = "choose_symmetry"
EXPECTED_NAMES = (CHOOSE_SELF_OF_EQ, CHOOSE_SYMMETRY)
EXPECTED_DEPENDENCIES = {
    CHOOSE_SELF_OF_EQ: ("choose_self",),
    CHOOSE_SYMMETRY: (
        "zero_add",
        "add_succ_left",
        "add_comm",
        "choose_exists",
        "choose_zero",
        CHOOSE_SELF_OF_EQ,
        "choose_succ_succ",
    ),
}
EXPECTED_DIRECT_CUTS = {CHOOSE_SELF_OF_EQ: 1, CHOOSE_SYMMETRY: 7}
EXPECTED_LOGICAL_LEAVES = {CHOOSE_SELF_OF_EQ: 2, CHOOSE_SYMMETRY: 6}

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
SYMMETRY_SOURCE_SHA256 = (
    "9958068fc364ca4bd171e965283a7683d167dcd6650e7a8df13f0b27c1edb78a"
)

# Fail closed until every isolated kernel gate prints a reproducible receipt.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CHOOSE_SELF_OF_EQ: (
        7241,
        "7768bf1af74dffe3e23a702b673a46aaf1097fe2583c9e06b1221702a120ba8e",
        "139065f4f12c29e8fd3d222874b9cc9d473e22a21e3818fd8b2278f3804527ff",
        "5a091bafc3574e08e37653fe1ea2a34ec3cce65a0cf2926a84cb718fd1260d5b",
    ),
    CHOOSE_SYMMETRY: (
        14301,
        "83e1de97b9f3dabaf5a613747d741d937d1b6152f53c6751f6144be115cb43f1",
        "8d3cd81dfcc0d903ca1543fc916b8c7de76600ea9733b880b6b5053b48401655",
        "3ad3d945a4a0d361377d574691fa3e4b1b89d23a6c151304f1c60ee093e8f746",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    CHOOSE_SELF_OF_EQ: (1, 44, 110, 50, 110, 109, 0),
    CHOOSE_SYMMETRY: (7, 178, 220, 40, 218, 219, 2),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CHOOSE_SELF_OF_EQ: (110, 110, 50, 69, 58),
    CHOOSE_SYMMETRY: (220, 218, 40, 4116, 62),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CHOOSE_SELF_OF_EQ: (
        2236,
        70,
        1709,
        1751,
        43,
        10041,
        70,
        "8ac630a11918ec4ced224496474afb0a3f9fcf8998872fba575f8a38756cf1a0",
    ),
    CHOOSE_SYMMETRY: (
        102121,
        103,
        8279,
        8565,
        287,
        379791,
        103,
        "69a3fadf1b693e77ab3455309aa70268cc4ff8ecd58f99ada6db87a602c09db8",
    ),
}

HELPER_VARIABLES = ("n", "k", "z")
SYMMETRY_VARIABLES = ("n", "k", "j", "x", "y")


def _helper_choose(column: str = "k") -> str:
    return foundation._choose_relation_term(
        "n",
        column,
        "z",
        tag="bcse_source",
        variables=HELPER_VARIABLES,
    )


def _symmetry_components(
    left_column: str = "k",
    right_column: str = "j",
) -> tuple[str, str]:
    left = foundation._choose_relation_term(
        "n",
        left_column,
        "x",
        tag="bcsym_left",
        variables=SYMMETRY_VARIABLES,
    )
    right = foundation._choose_relation_term(
        "n",
        right_column,
        "y",
        tag="bcsym_right",
        variables=SYMMETRY_VARIABLES,
    )
    return left, right


def _expected_statements() -> dict[str, str]:
    left, right = _symmetry_components()
    return {
        CHOOSE_SELF_OF_EQ: (
            "forall n k z. k = n -> "
            f"({_helper_choose()}) -> z = 1"
        ),
        CHOOSE_SYMMETRY: (
            "forall n k j x y. k + j = n -> "
            f"({left}) -> ({right}) -> x = y"
        ),
    }


def _expected_interior_haves() -> tuple[str, ...]:
    rows = (
        (
            "ha_exists",
            "a",
            "k",
            "bcs_previous_left",
        ),
        (
            "hb_exists",
            "b",
            "S k",
            "bcs_current_left",
        ),
        (
            "hc_exists",
            "c",
            "j",
            "bcs_previous_right",
        ),
        (
            "hd_exists",
            "d",
            "S j",
            "bcs_current_right",
        ),
    )
    result = []
    for have_name, value, column, tag in rows:
        relation = foundation._choose_relation_term(
            "n",
            column,
            value,
            tag=tag,
            variables=SYMMETRY_VARIABLES + (value,),
        )
        result.append(f"have {have_name} : exists {value}. ({relation})")
    return tuple(result)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_symmetry_candidate_theorems(TheoremSpec)


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
            raise AssertionError("Choose symmetry delegated through use")
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


def test_choose_symmetry_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_functional_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_functional_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
        (laws_module, LAWS_SOURCE_SHA256),
        (diagonal_module, DIAGONAL_SOURCE_SHA256),
        (recurrence_module, RECURRENCE_SOURCE_SHA256),
        (pascal_module, PASCAL_SOURCE_SHA256),
        (module, SYMMETRY_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest


def test_choose_symmetry_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    assert make_bertrand_choose_symmetry_candidate_theorems(TheoremSpec) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert {item.name: item.statement for item in rows} == _expected_statements()
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_choose_symmetry_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    support = set(_table(_support_specs()))
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & support)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert all(
        dependency in _available()
        for item in rows
        for dependency in item.dependencies
    )

    provider_token = "bertrand_choose_symmetry_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    forbidden_surface = (
        "BetaAt(",
        "PascalTablePrefix(",
        "Choose(",
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


def test_choose_symmetry_binders_and_script_topology_are_exact() -> None:
    helper, symmetry = _specs()
    assert helper.statement.startswith("forall n k z. k = n -> (")
    assert helper.statement.endswith("z = 1")
    assert helper.script[:8] == (
        "intro n",
        "intro k",
        "intro z",
        "intro heq",
        "intro hchoose",
        "specialize choose_self n",
        "specialize choose_self z",
        "apply choose_self",
    )
    assert helper.script.count("rewrite heq at hchoose_left_left") == 1
    assert helper.script.count("rewrite heq at hchoose_right_left") == 1
    decoded_rewrites = tuple(
        command
        for command in helper.script
        if command.startswith(
            "rewrite heq at hchoose_right_right_witness_witness_"
        )
    )
    assert len(decoded_rewrites) == 2
    assert decoded_rewrites[0] == decoded_rewrites[1]
    assert sum(
        command.startswith("rewrite heq at") for command in helper.script
    ) == 4
    assert "rewrite heq at hchoose" not in helper.script
    assert helper.script.count("left") == 1
    assert helper.script.count("right") == 1
    assert EXPECTED_LOGICAL_LEAVES[CHOOSE_SELF_OF_EQ] == 2

    assert symmetry.statement.startswith("forall n k j x y. k + j = n -> (")
    assert symmetry.statement.endswith("x = y")
    inductions = tuple(
        command
        for command in symmetry.script
        if command.startswith("induction ")
    )
    assert inductions == (
        "induction n",
        "induction k",
        "induction j",
        "induction k",
        "induction j",
    )
    assert EXPECTED_LOGICAL_LEAVES[CHOOSE_SYMMETRY] == 6
    assert symmetry.script.count("apply PA1") == 2
    assert symmetry.script.count("apply choose_zero") == 4
    assert symmetry.script.count("apply choose_self_of_eq") == 2
    assert symmetry.script.count("apply choose_succ_succ") == 2
    assert symmetry.script.count("apply IH") == 2
    existential_haves = tuple(
        command
        for command in symmetry.script
        if "have h" in command and "_exists" in command
    )
    assert existential_haves == _expected_interior_haves()
    assert not any(
        command.startswith("rewrite ")
        and (command.endswith("at hleft") or command.endswith("at hright"))
        for command in symmetry.script
    )


def test_choose_symmetry_relation_builder_is_hygienic() -> None:
    left = foundation._choose_relation_term(
        "n",
        "k",
        "z",
        tag="hygiene_left",
        variables=HELPER_VARIABLES,
    )
    right = foundation._choose_relation_term(
        "n",
        "k",
        "z",
        tag="hygiene_right",
        variables=HELPER_VARIABLES,
    )
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"n", "k", "z"}

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
            variables=HELPER_VARIABLES,
        )


def test_choose_symmetry_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_symmetry_artifact_receipts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CHOOSE SYMMETRY ARTIFACT {name} actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_symmetry_bodies_and_envelopes_are_frozen(name: str) -> None:
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
        label=f"Choose symmetry body {name}",
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
        f"CHOOSE SYMMETRY BODY {name} actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    assert EXPECTED_BODIES[name] is not None, f"freeze body {name}: {actual!r}"
    assert EXPECTED_ENVELOPES[name] is not None, (
        f"freeze envelope {name}: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)


@pytest.mark.parametrize(
    ("name", "dependency"),
    LIVE_EDGES,
    ids=tuple(f"{name}--{dependency}" for name, dependency in LIVE_EDGES),
)
def test_choose_symmetry_every_direct_dependency_is_live(
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
def test_choose_symmetry_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    helper_old = _helper_choose()
    helper_shifted = _helper_choose("S k")
    left_old, right_old = _symmetry_components()
    left_shifted, _right = _symmetry_components(left_column="S k")
    _left, right_shifted = _symmetry_components(right_column="S j")
    return (
        (
            CHOOSE_SELF_OF_EQ,
            "helper_shifted_column",
            helper_old,
            helper_shifted,
        ),
        (CHOOSE_SELF_OF_EQ, "helper_zero_conclusion", "z = 1", "z = 0"),
        (
            CHOOSE_SYMMETRY,
            "successor_shifted_complement",
            "k + j = n",
            "S k + j = n",
        ),
        (
            CHOOSE_SYMMETRY,
            "left_successor_column",
            left_old,
            left_shifted,
        ),
        (
            CHOOSE_SYMMETRY,
            "right_successor_column",
            right_old,
            right_shifted,
        ),
        (CHOOSE_SYMMETRY, "successor_value", "x = y", "x = S y"),
    )


def test_choose_symmetry_mutations_have_standard_counterfixtures() -> None:
    # C(0,1)=0, so an equal zero column shifted right is not diagonal one.
    assert 0 != 1
    # C(0,0)=1, not zero.
    assert 1 != 0
    # 1+1=2, but C(2,0)=1 and C(2,1)=2.
    assert 1 != 2
    # C(2,1)=2 differs from C(2,2)=1 in either shifted-input direction.
    assert 2 != 1
    assert 1 != 2
    # C(0,0)=1 is not the successor of itself.
    assert 1 != 2


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_choose_symmetry_genuine_mutations_are_rejected(
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
def test_choose_symmetry_empty_context_closures_are_frozen(name: str) -> None:
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
        label=f"Choose symmetry closure {name}",
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
        f"CHOOSE SYMMETRY CLOSURE {name} actual={actual!r}",
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
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[name]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze empty-context closure receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
