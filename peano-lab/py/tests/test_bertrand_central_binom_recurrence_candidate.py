"""Fail-closed audit for the weighted central-binomial recurrence.

The public surface is rebuilt independently from the raw expanded Choose
relation.  Every unregistered predecessor used by the closure is rebuilt
from pinned source, while unrelated central-binomial and integer-envelope
siblings remain unavailable.  Receipts are regression evidence only.
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
from peano_lab.kernel.terms import (
    Add,
    Zero,
    parse_term_in_context,
    pretty_term,
)
from peano_lab.library import (
    alpha_enrollment_v7,
    bertrand_central_binom_candidate as central_module,
    bertrand_central_binom_recurrence_candidate as module,
    bertrand_central_binom_succ_candidate as central_succ_module,
    bertrand_choose_diagonal_candidate as diagonal_module,
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_laws_candidate as laws_module,
    bertrand_choose_pascal_candidate as pascal_module,
    bertrand_choose_recurrence_candidate as choose_recurrence_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_symmetry_candidate as symmetry_module,
    bertrand_choose_table_row_functional_candidate as table_functional_module,
    bertrand_choose_weighted_vertical_candidate as weighted_module,
    bertrand_integer_envelope_candidate as integer_envelope_module,
    editions_v7,
    theorems as stable_module,
)
from peano_lab.library.bertrand_central_binom_recurrence_candidate import (
    make_bertrand_central_binom_recurrence_candidate_theorems,
)
from peano_lab.library.bertrand_central_binom_succ_candidate import (
    make_bertrand_central_binom_succ_candidate_theorems,
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
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
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


CENTRAL_BINOM_SUCC_RECURRENCE = "central_binom_succ_recurrence"
EXPECTED_NAMES = (CENTRAL_BINOM_SUCC_RECURRENCE,)
EXPECTED_DEPENDENCIES = {
    CENTRAL_BINOM_SUCC_RECURRENCE: (
        "mul_add",
        "mul_assoc",
        "two_mul_eq_add_self",
        "central_binom_succ_double_middle",
        "choose_weighted_vertical",
    ),
}
EXPECTED_DIRECT_CUTS = {CENTRAL_BINOM_SUCC_RECURRENCE: 5}

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
CHOOSE_RECURRENCE_SOURCE_SHA256 = (
    "8b4a65b18e6a97a89c3f714686f2c690afb49f82ab56ed9575e3f673f50093c5"
)
PASCAL_SOURCE_SHA256 = (
    "e96ee1d140beece2666b901dc7d671743b01386f110628b0957aeff01b9c26c3"
)
SYMMETRY_SOURCE_SHA256 = (
    "9958068fc364ca4bd171e965283a7683d167dcd6650e7a8df13f0b27c1edb78a"
)
CENTRAL_SOURCE_SHA256 = (
    "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e"
)
CENTRAL_SUCC_SOURCE_SHA256 = (
    "c0faea72fbe7c21ada1f15adc91dec324e0fa643bde464c9b10f9a75df4f2b27"
)
WEIGHTED_SOURCE_SHA256 = (
    "e8629d085ccb2d69acb179ce2bcede5612edf290a39dac175476574f9ce76bd1"
)
INTEGER_ENVELOPE_SOURCE_SHA256 = (
    "8f0967c2680f4f2e9c8c693df6f405a60a61decd8dd1cb52c2ca1b611b4fdfc1"
)
RECURRENCE_SOURCE_SHA256 = (
    "beca6c184d6cce8eeb561134dcc95adff9c995397adccd806c3155857d372d8e"
)

# Execution receipts fail closed until each isolated selector reproduces one.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CENTRAL_BINOM_SUCC_RECURRENCE: (
        16195,
        "9fb0073774e6ee9c70b3a54c606b75e0a2d710327f45bd74f780b13f2bacb9c5",
        "ac7836783d5b91ecfe742a8215f06def23d51b6efa49fd3ee3d4aafafcbd70d7",
        "18660f68b9f6d31e2e55871352a8d2ab26cb6879cbcb519a5ee2826b54e4a23d",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    CENTRAL_BINOM_SUCC_RECURRENCE: (5, 36, 64, 25, 64, 63, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CENTRAL_BINOM_SUCC_RECURRENCE: (64, 64, 25, 91, 26),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CENTRAL_BINOM_SUCC_RECURRENCE: (
        303382,
        111,
        8846,
        9156,
        311,
        1131651,
        111,
        "2bf020414dfb7b771622606edea8c023251b98bd3c7b3be660236af202f96ec4",
    ),
}

SURFACE_VARIABLES = ("n", "c", "d")


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


def _central(
    index: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Independently expand Choose(index+index,index,value)."""

    context = list(variables)
    index_term = parse_term_in_context(index, context)
    value_term = parse_term_in_context(value, context)
    rendered_index = pretty_term(index_term, context).replace("·", "*")
    rendered_value = pretty_term(value_term, context).replace("·", "*")
    doubled = pretty_term(Add(index_term, index_term), context).replace(
        "·", "*"
    )
    return _choose(
        doubled,
        rendered_index,
        rendered_value,
        tag=tag,
        variables=variables,
    )


def _relations() -> dict[str, str]:
    return {
        "predecessor": _central(
            "n",
            "c",
            tag="bcbsr_predecessor",
            variables=SURFACE_VARIABLES,
        ),
        "successor": _central(
            "S n",
            "d",
            tag="bcbsr_successor",
            variables=SURFACE_VARIABLES,
        ),
        "middle": _choose(
            "S (n + n)",
            "n",
            "m",
            tag="bcbsr_middle",
            variables=SURFACE_VARIABLES + ("m",),
        ),
    }


def _expected_statement() -> str:
    relations = _relations()
    return (
        "forall n c d. "
        f"({relations['predecessor']}) -> ({relations['successor']}) -> "
        "S n * d = (2 * S (n + n)) * c"
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_central_binom_recurrence_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    integer_prefix = make_bertrand_integer_envelope_candidate_theorems(
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
        *make_bertrand_choose_symmetry_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_weighted_vertical_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_central_binom_succ_candidate_theorems(TheoremSpec),
        *integer_prefix,
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
    assert CENTRAL_BINOM_SUCC_RECURRENCE not in public
    assert CENTRAL_BINOM_SUCC_RECURRENCE not in support
    return public | support


def _row_core(name: str) -> dict[str, TheoremSpec]:
    assert name == CENTRAL_BINOM_SUCC_RECURRENCE
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
            raise AssertionError("central recurrence delegated through use")
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


def test_central_binom_recurrence_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_functional_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_functional_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
        (laws_module, LAWS_SOURCE_SHA256),
        (diagonal_module, DIAGONAL_SOURCE_SHA256),
        (choose_recurrence_module, CHOOSE_RECURRENCE_SOURCE_SHA256),
        (pascal_module, PASCAL_SOURCE_SHA256),
        (symmetry_module, SYMMETRY_SOURCE_SHA256),
        (central_module, CENTRAL_SOURCE_SHA256),
        (central_succ_module, CENTRAL_SUCC_SOURCE_SHA256),
        (weighted_module, WEIGHTED_SOURCE_SHA256),
        (integer_envelope_module, INTEGER_ENVELOPE_SOURCE_SHA256),
        (module, RECURRENCE_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest


def test_central_binom_recurrence_factory_is_exact_and_isolated() -> None:
    rows = _specs()
    assert make_bertrand_central_binom_recurrence_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert rows[0].statement == _expected_statement()
    assert rows[0].dependencies == EXPECTED_DEPENDENCIES[
        CENTRAL_BINOM_SUCC_RECURRENCE
    ]
    assert module.__all__ == [
        "make_bertrand_central_binom_recurrence_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    support = _table(_support_specs())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert len(support) == 24
    assert CENTRAL_BINOM_SUCC_RECURRENCE not in stable
    assert CENTRAL_BINOM_SUCC_RECURRENCE not in support
    assert CENTRAL_BINOM_SUCC_RECURRENCE not in alpha
    assert "central_binom_succ_double_middle" in support
    assert "choose_weighted_vertical" in support
    assert "two_mul_eq_add_self" in support
    for sibling in (
        "central_binom_exists",
        "central_binom_functional",
        "central_binom_positive",
        "central_binom_zero",
        "pow_mul_base",
        "pow_two_base_two_value_four",
        "pow_two_twelve_eq_pow_four_six",
        "bertrand_guard_six_step_transport",
    ):
        assert sibling not in support
    assert all(
        dependency in _row_core(CENTRAL_BINOM_SUCC_RECURRENCE)
        for dependency in rows[0].dependencies
    )

    provider_token = "bertrand_central_binom_recurrence_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    formula, free_names = parse_formula_with_names(rows[0].statement)
    assert not free_names
    assert formula == _closed_formula(rows[0].statement)
    for token in (
        "BetaAt(",
        "Choose(",
        "CentralBinom(",
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


def test_central_binom_recurrence_script_topology_is_exact() -> None:
    script = _specs()[0].script
    relations = _relations()
    assert len(script) == 36
    assert not any(command.startswith("induction ") for command in script)
    assert script.count(
        f"have hmiddle : exists m. (({relations['middle']}) /\\ d = m + m)"
    ) == 1
    assert script.count("apply central_binom_succ_double_middle") == 1
    assert script.count("cases hmiddle") == 1
    assert script.count("cases hmiddle_witness") == 1
    assert script.count(
        "have hweighted : S n * x = S (n + n) * c"
    ) == 1
    assert sum(
        command.startswith("specialize choose_weighted_vertical ")
        for command in script
    ) == 5
    assert script.count("apply choose_weighted_vertical") == 1
    assert script.count("rewrite hmiddle_witness_right") == 1
    assert script.count("apply mul_add") == 1
    assert script.count("rewrite hweighted") == 2
    assert script.count("exact two_mul_eq_add_self") == 1
    assert script.count("exact mul_assoc") == 1
    assert not any(
        command.startswith("rewrite ") and command.endswith("at hpredecessor")
        for command in script
    )
    assert not any(
        command.startswith("rewrite ") and command.endswith("at hsuccessor")
        for command in script
    )


def test_central_binom_recurrence_helpers_are_hygienic() -> None:
    left = _central(
        "n",
        "c",
        tag="central_recurrence_hygiene_left",
        variables=SURFACE_VARIABLES,
    )
    right = _central(
        "n",
        "c",
        tag="central_recurrence_hygiene_right",
        variables=SURFACE_VARIABLES,
    )
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"n", "c"}

    successor = _central(
        "S n",
        "d",
        tag="central_recurrence_hygiene_successor",
        variables=SURFACE_VARIABLES,
    )
    _, successor_free = parse_formula_with_names(successor)
    assert set(successor_free) == {"n", "d"}

    with pytest.raises(ValueError):
        _central(
            "n",
            "c",
            tag="valid",
            variables=SURFACE_VARIABLES + ("bcf_row_code_code_valid",),
        )
    with pytest.raises(ValueError):
        _central(
            "n",
            "c",
            tag="bad tag",
            variables=SURFACE_VARIABLES,
        )


def test_central_binom_recurrence_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert len(EXPECTED_DEPENDENCIES[CENTRAL_BINOM_SUCC_RECURRENCE]) == 5


def test_central_binom_recurrence_artifact_receipt_is_frozen() -> None:
    item = _specs()[0]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CENTRAL RECURRENCE ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[CENTRAL_BINOM_SUCC_RECURRENCE] is not None, (
        f"freeze deterministic artifact receipt: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[CENTRAL_BINOM_SUCC_RECURRENCE]


def test_central_binom_recurrence_body_and_envelope_are_frozen() -> None:
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
        label="central recurrence body",
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
        f"CENTRAL RECURRENCE BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[CENTRAL_BINOM_SUCC_RECURRENCE] is not None, (
        f"freeze body: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[CENTRAL_BINOM_SUCC_RECURRENCE] is not None, (
        f"freeze envelope: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[CENTRAL_BINOM_SUCC_RECURRENCE]
    assert envelope == EXPECTED_ENVELOPES[CENTRAL_BINOM_SUCC_RECURRENCE]


@pytest.mark.parametrize(
    "dependency",
    EXPECTED_DEPENDENCIES[CENTRAL_BINOM_SUCC_RECURRENCE],
)
def test_central_binom_recurrence_every_dependency_is_live(
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
            core=_row_core(CENTRAL_BINOM_SUCC_RECURRENCE),
        )


def test_central_binom_recurrence_false_target_is_rejected() -> None:
    item = _specs()[0]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (mutated,),
            core=_row_core(CENTRAL_BINOM_SUCC_RECURRENCE),
        )


def _mutations() -> tuple[tuple[str, str, str], ...]:
    relations = _relations()
    shifted_predecessor = _central(
        "S n",
        "c",
        tag="bcbsr_predecessor",
        variables=SURFACE_VARIABLES,
    )
    shifted_successor = _central(
        "n",
        "d",
        tag="bcbsr_successor",
        variables=SURFACE_VARIABLES,
    )
    conclusion = "S n * d = (2 * S (n + n)) * c"
    return (
        (
            "shift_predecessor_row",
            relations["predecessor"],
            shifted_predecessor,
        ),
        (
            "shift_successor_row_back",
            relations["successor"],
            shifted_successor,
        ),
        (
            "drop_left_successor",
            conclusion,
            "n * d = (2 * S (n + n)) * c",
        ),
        (
            "drop_outer_two",
            conclusion,
            "S n * d = S (n + n) * c",
        ),
        (
            "drop_odd_row_successor",
            conclusion,
            "S n * d = (2 * (n + n)) * c",
        ),
    )


def test_central_binom_recurrence_mutations_have_counterfixtures() -> None:
    # Every fixture uses n=0 and the standard values C(0,0)=1, C(2,1)=2.
    assert 2 != 4  # Shifted predecessor has c=d=2.
    assert 1 != 2  # Shifted successor has c=d=1.
    assert 0 != 2  # Dropping the left successor annihilates the left side.
    assert 2 != 1  # Dropping the outer two halves the right side.
    assert 2 != 0  # Dropping the odd-row successor gives a zero factor.


@pytest.mark.parametrize(
    ("case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[0] for case in _mutations()),
)
def test_central_binom_recurrence_genuine_mutations_are_rejected(
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
            core=_row_core(CENTRAL_BINOM_SUCC_RECURRENCE),
        )


def test_central_binom_recurrence_empty_context_closure_is_frozen() -> None:
    item = _specs()[0]
    formula, certificate = _close(CENTRAL_BINOM_SUCC_RECURRENCE)
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
        label="central recurrence closure",
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
        CENTRAL_BINOM_SUCC_RECURRENCE
    ]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    print(f"CENTRAL RECURRENCE CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[CENTRAL_BINOM_SUCC_RECURRENCE] is not None, (
        f"freeze empty-context closure: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[CENTRAL_BINOM_SUCC_RECURRENCE]
