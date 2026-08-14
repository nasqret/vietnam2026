"""Fail-closed audit for the constructive weighted Choose identity.

The public theorem surface is rebuilt independently from the raw expanded
``Choose`` helper.  Every unregistered predecessor is rebuilt from pinned
source, and the sole local row receives only the exact support graph named by
its dependencies.  Receipts remain non-authoritative regression evidence.
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
    bertrand_choose_recurrence_candidate as recurrence_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_symmetry_candidate as symmetry_module,
    bertrand_choose_table_row_functional_candidate as table_functional_module,
    bertrand_choose_weighted_vertical_candidate as module,
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
from peano_lab.library.bertrand_choose_weighted_vertical_candidate import (
    make_bertrand_choose_weighted_vertical_candidate_theorems,
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


CHOOSE_WEIGHTED_VERTICAL = "choose_weighted_vertical"
EXPECTED_NAMES = (CHOOSE_WEIGHTED_VERTICAL,)
EXPECTED_DEPENDENCIES = {
    CHOOSE_WEIGHTED_VERTICAL: (
        "zero_or_succ",
        "zero_add",
        "add_succ_left",
        "add_assoc",
        "mul_succ_left",
        "mul_add",
        "choose_exists",
        "choose_zero",
        "choose_self_of_eq",
        "choose_succ_succ",
    ),
}
EXPECTED_DIRECT_CUTS = {CHOOSE_WEIGHTED_VERTICAL: 10}

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
WEIGHTED_SOURCE_SHA256 = (
    "e8629d085ccb2d69acb179ce2bcede5612edf290a39dac175476574f9ce76bd1"
)

# Fail closed until each isolated kernel gate reproduces its exact receipt.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CHOOSE_WEIGHTED_VERTICAL: (
        14170,
        "1ed4929816b14503ce183ef0fbd50a5f513c34f3c2ce36eac935a15dcd827679",
        "cd74135be8061c19a136b18018620921c40ef916fbf25a84480e81279175eca1",
        "ce4c2ab5f11c9b6dfe605c024d2018e570e78478697f72b16349e6b94cbb5e62",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    CHOOSE_WEIGHTED_VERTICAL: (10, 285, 375, 47, 368, 374, 7),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CHOOSE_WEIGHTED_VERTICAL: (375, 368, 47, 2747, 63),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CHOOSE_WEIGHTED_VERTICAL: (
        102493,
        106,
        8429,
        8723,
        295,
        381618,
        106,
        "6d550ab0647d8c491bf2da5fa263c8e37842d6bcd35da25d07a069c2862eb693",
    ),
}

SURFACE_VARIABLES = ("n", "k", "j", "x", "y")


def _choose(
    upper: str,
    column: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    return foundation._choose_relation_term(
        upper,
        column,
        value,
        tag=tag,
        variables=variables,
    )


def _relations() -> dict[str, str]:
    return {
        "lower": _choose(
            "n",
            "k",
            "x",
            tag="bcwv_lower",
            variables=SURFACE_VARIABLES,
        ),
        "upper": _choose(
            "S n",
            "k",
            "y",
            tag="bcwv_upper",
            variables=SURFACE_VARIABLES,
        ),
        "previous_left": _choose(
            "n",
            "k",
            "a",
            tag="bcwv_previous_left",
            variables=SURFACE_VARIABLES + ("a",),
        ),
        "previous_right": _choose(
            "n",
            "S k",
            "b",
            tag="bcwv_previous_right",
            variables=SURFACE_VARIABLES + ("b",),
        ),
        "diagonal_successor_left": _choose(
            "S n",
            "k",
            "b",
            tag="bcwv_successor_left",
            variables=SURFACE_VARIABLES + ("b",),
        ),
        "interior_successor_left": _choose(
            "S n",
            "k",
            "c",
            tag="bcwv_successor_left",
            variables=SURFACE_VARIABLES + ("c",),
        ),
    }


def _expected_statement() -> str:
    relations = _relations()
    return (
        "forall n k j x y. k + j = n -> "
        f"({relations['lower']}) -> ({relations['upper']}) -> "
        "S j * y = S n * x"
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_weighted_vertical_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    # Only the first symmetry row is an ancestor.  The public symmetry theorem
    # itself must not be available as a shortcut for this vertical proof.
    symmetry_prefix = make_bertrand_choose_symmetry_candidate_theorems(
        TheoremSpec
    )[:1]
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
        *symmetry_prefix,
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
    assert CHOOSE_WEIGHTED_VERTICAL not in public
    assert CHOOSE_WEIGHTED_VERTICAL not in support
    assert "choose_symmetry" not in support
    return public | support


def _row_core(name: str) -> dict[str, TheoremSpec]:
    assert name == CHOOSE_WEIGHTED_VERTICAL
    return _core()


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
            raise AssertionError("weighted Choose row delegated through use")
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


def test_choose_weighted_vertical_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_functional_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_functional_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
        (laws_module, LAWS_SOURCE_SHA256),
        (diagonal_module, DIAGONAL_SOURCE_SHA256),
        (recurrence_module, RECURRENCE_SOURCE_SHA256),
        (pascal_module, PASCAL_SOURCE_SHA256),
        (symmetry_module, SYMMETRY_SOURCE_SHA256),
        (module, WEIGHTED_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest


def test_choose_weighted_vertical_factory_is_exact_and_isolated() -> None:
    rows = _specs()
    assert make_bertrand_choose_weighted_vertical_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert rows[0].statement == _expected_statement()
    assert rows[0].dependencies == EXPECTED_DEPENDENCIES[
        CHOOSE_WEIGHTED_VERTICAL
    ]
    assert module.__all__ == [
        "make_bertrand_choose_weighted_vertical_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    support = set(_table(_support_specs()))
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert CHOOSE_WEIGHTED_VERTICAL not in stable
    assert CHOOSE_WEIGHTED_VERTICAL not in support
    assert CHOOSE_WEIGHTED_VERTICAL not in alpha
    assert "choose_symmetry" not in support
    assert all(
        dependency in _row_core(CHOOSE_WEIGHTED_VERTICAL)
        for dependency in rows[0].dependencies
    )

    provider_token = "bertrand_choose_weighted_vertical_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    formula, free_names = parse_formula_with_names(rows[0].statement)
    assert not free_names
    assert formula == _closed_formula(rows[0].statement)
    for token in (
        "BetaAt(",
        "PascalTablePrefix(",
        "Choose(",
        "Factorial(",
        "<=",
        "<",
        "^",
        "%",
        "|",
    ):
        assert token not in rows[0].statement
    for command in rows[0].script:
        assert all(
            token not in command
            for token in (
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


def test_choose_weighted_vertical_five_leaf_topology_is_exact() -> None:
    script = _specs()[0].script
    relations = _relations()
    assert script.count("induction n") == 1
    assert script.count("induction k") == 2
    assert not any(command == "induction j" for command in script)
    assert script.count("specialize zero_or_succ j") == 1
    assert script.count("cases zero_or_succ") == 1
    assert script.count("cases zero_or_succ_right") == 1
    assert script.count("exact choose_exists") == 5
    assert script.count("apply choose_zero") == 4
    assert script.count("apply choose_self_of_eq") == 2
    assert script.count("apply choose_succ_succ") == 3
    assert script.count("apply IH") == 3
    assert script.count("apply mul_add") == 3

    assert script.count(
        f"have ha_exists : exists a. ({relations['previous_left']})"
    ) == 2
    assert script.count(
        "have hb_exists : exists b. "
        f"({relations['diagonal_successor_left']})"
    ) == 1
    assert script.count(
        f"have hb_exists : exists b. ({relations['previous_right']})"
    ) == 1
    assert script.count(
        "have hc_exists : exists c. "
        f"({relations['interior_successor_left']})"
    ) == 1
    assert not any(
        command.startswith("rewrite ") and command.endswith("at hlower")
        for command in script
    )
    assert not any(
        command.startswith("rewrite ") and command.endswith("at hupper")
        for command in script
    )


def test_choose_weighted_vertical_helpers_are_hygienic() -> None:
    left = _choose(
        "n",
        "k",
        "x",
        tag="weighted_hygiene_left",
        variables=SURFACE_VARIABLES,
    )
    right = _choose(
        "n",
        "k",
        "x",
        tag="weighted_hygiene_right",
        variables=SURFACE_VARIABLES,
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
            variables=SURFACE_VARIABLES + ("bcf_row_code_code_valid",),
        )
    with pytest.raises(ValueError):
        foundation._choose_relation_term(
            "n",
            "k",
            "x",
            tag="bad tag",
            variables=SURFACE_VARIABLES,
        )


def test_choose_weighted_vertical_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert len(EXPECTED_DEPENDENCIES[CHOOSE_WEIGHTED_VERTICAL]) == 10


def test_choose_weighted_vertical_artifact_receipt_is_frozen() -> None:
    item = _specs()[0]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"WEIGHTED VERTICAL ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[CHOOSE_WEIGHTED_VERTICAL] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[CHOOSE_WEIGHTED_VERTICAL]


def test_choose_weighted_vertical_body_and_envelope_are_frozen() -> None:
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
        label="weighted vertical body",
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
        f"WEIGHTED VERTICAL BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[CHOOSE_WEIGHTED_VERTICAL] is not None, (
        f"freeze body: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[CHOOSE_WEIGHTED_VERTICAL] is not None, (
        f"freeze envelope: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[CHOOSE_WEIGHTED_VERTICAL]
    assert envelope == EXPECTED_ENVELOPES[CHOOSE_WEIGHTED_VERTICAL]


@pytest.mark.parametrize(
    "dependency",
    EXPECTED_DEPENDENCIES[CHOOSE_WEIGHTED_VERTICAL],
)
def test_choose_weighted_vertical_every_dependency_is_live(
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
            (shortened,),
            core=_row_core(CHOOSE_WEIGHTED_VERTICAL),
        )


def test_choose_weighted_vertical_false_target_is_rejected() -> None:
    item = _specs()[0]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (mutated,),
            core=_row_core(CHOOSE_WEIGHTED_VERTICAL),
        )


def _mutations() -> tuple[tuple[str, str, str], ...]:
    relations = _relations()
    predecessor_upper = _choose(
        "n",
        "k",
        "y",
        tag="bcwv_upper",
        variables=SURFACE_VARIABLES,
    )
    successor_column = _choose(
        "S n",
        "S k",
        "y",
        tag="bcwv_upper",
        variables=SURFACE_VARIABLES,
    )
    return (
        (
            "shifted_complement",
            "k + j = n",
            "k + j = S n",
        ),
        (
            "predecessor_upper_row",
            relations["upper"],
            predecessor_upper,
        ),
        (
            "successor_upper_column",
            relations["upper"],
            successor_column,
        ),
        (
            "drop_left_successor_factor",
            "S j * y",
            "j * y",
        ),
        (
            "drop_right_successor_factor",
            "S n * x",
            "n * x",
        ),
    )


def test_choose_weighted_vertical_mutations_have_counterfixtures() -> None:
    # Mutated 0 + 1 = S 0, but 2 * C(1,0) != 1 * C(0,0).
    assert 2 != 1
    # C(1,1)=1 in both premises, but 1 * 1 != 2 * 1.
    assert 1 != 2
    # C(1,0)=1 and C(2,1)=2, but 2 * 2 != 2 * 1.
    assert 4 != 2
    # At n=k=j=0 both values are one; dropping either successor gives 0 != 1.
    assert 0 != 1
    assert 1 != 0


@pytest.mark.parametrize(
    ("case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[0] for case in _mutations()),
)
def test_choose_weighted_vertical_genuine_mutations_are_rejected(
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
            (mutated,),
            core=_row_core(CHOOSE_WEIGHTED_VERTICAL),
        )


def test_choose_weighted_vertical_empty_context_closure_is_frozen() -> None:
    item = _specs()[0]
    formula, certificate = _close(CHOOSE_WEIGHTED_VERTICAL)
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
        label="weighted vertical closure",
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
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[
        CHOOSE_WEIGHTED_VERTICAL
    ]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    print(f"WEIGHTED VERTICAL CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[CHOOSE_WEIGHTED_VERTICAL] is not None, (
        f"freeze empty-context closure: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[CHOOSE_WEIGHTED_VERTICAL]
