"""Fail-closed audit for finite-product pointwise and uniform order bounds.

The two rows remain isolated candidates.  The first closes through the exact
Alpha-v3 ``mul_le_mul`` body rather than through enrollment evidence; the
second closes through the first candidate body.  Static formulas, dependency
topology, artifacts, bodies, envelopes, mutations, and empty-context closures
are independently gated below.
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
    editions_v7,
    finite_product_order_candidate as module,
    theorems as stable_module,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.finite_fold_surface import (
    beta_at,
    power_relation,
    product_relation,
)
from peano_lab.library.finite_product_order_candidate import (
    make_finite_product_order_candidate_theorems,
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


POINTWISE_NAME = "beta_product_pointwise_le"
UNIFORM_NAME = "beta_product_uniform_le_pow"
EXPECTED_NAMES = (POINTWISE_NAME, UNIFORM_NAME)

EXPECTED_DEPENDENCIES = {
    POINTWISE_NAME: (
        "beta_product_zero",
        "beta_product_succ_decompose",
        "le_succ",
        "le_refl",
        "mul_le_mul",
    ),
    UNIFORM_NAME: (
        "beta_repeat_entry_eq",
        POINTWISE_NAME,
    ),
}

# These deterministic receipts are populated only after the corresponding
# isolated check succeeds.  None is deliberately fail-closed, not an axiom or
# an enrollment receipt.
EXPECTED_ARTIFACTS: dict[
    str, tuple[int, str, str, str] | None
] = {
    POINTWISE_NAME: (
        4_309,
        "cfba50ff943fb741207835583df50acf7b00867e98d90ac6e1eb734e850affef",
        "e33adae0f21aaa403bd39e96eb97a10277e68abe809fcac3dc35b2fd0bde48f0",
        "00a8d7e5dc543ec464df9757867a58cc5929918ea3a76a26b0a429f1c233ff45",
    ),
    UNIFORM_NAME: (
        5_450,
        "189186521ad0b0d3e03179bf58ae08e587720d0c89097eaee4aa46262da76583",
        "c9f542be9266e1572ecbeb7d3f79c645f5a8c4f7de2908e9dde051bff96b6008",
        "c861c218427be07156fc217ae032211c92a0deffd4f68aa03d03924aea4ec72e",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    POINTWISE_NAME: (5, 97, 122, 41, 122, 121, 0),
    UNIFORM_NAME: (2, 45, 58, 34, 58, 57, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    POINTWISE_NAME: (122, 122, 41, 434, 42),
    UNIFORM_NAME: (58, 58, 34, 21, 34),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, str] | None
] = {
    POINTWISE_NAME: (
        3_136,
        64,
        1_066,
        1_113,
        48,
        "fc279a490f98b0805e52b179dd3756156dee9dcf66a278d5b68c238afddafc18",
    ),
    UNIFORM_NAME: (
        4_338,
        66,
        1_147,
        1_195,
        49,
        "8277eef19b6206d326fb81e69a4f43a74d3e2b95064e3d6482b8a9bff706a508",
    ),
}


def _expected_statements() -> dict[str, str]:
    left_at = beta_at("b", "c", "i", "a", tag="bppl_left")
    right_at = beta_at("d", "e", "i", "z", tag="bppl_right")
    pointwise = (
        "forall i a z. (exists bppl_bound. bppl_bound + S i = l) -> "
        f"({left_at}) -> ({right_at}) -> "
        "exists bppl_factor_gap. bppl_factor_gap + a = z"
    )
    left_product = product_relation(
        "b", "c", "l", "n", tag="bppl_left_product"
    )
    right_product = product_relation(
        "d", "e", "l", "q", tag="bppl_right_product"
    )

    uniform_at = beta_at("b", "c", "i", "x", tag="bpulp_source")
    uniform = (
        "forall i x. (exists bpulp_bound. bpulp_bound + S i = l) -> "
        f"({uniform_at}) -> "
        "exists bpulp_factor_gap. bpulp_factor_gap + x = a"
    )
    source_product = product_relation(
        "b", "c", "l", "n", tag="bpulp_source_product"
    )
    target_power = power_relation(
        "a", "l", "q", tag="bpulp_target_power"
    )

    return {
        POINTWISE_NAME: (
            "forall b c d e l n q. "
            f"({pointwise}) -> ({left_product}) -> ({right_product}) -> "
            "exists bppl_result_gap. bppl_result_gap + n = q"
        ),
        UNIFORM_NAME: (
            "forall b c a l n q. "
            f"({uniform}) -> ({source_product}) -> ({target_power}) -> "
            "exists bpulp_result_gap. bpulp_result_gap + n = q"
        ),
    }


BOUNDARY_MUTATION_CASES = (
    (
        "pointwise__reverse_factor_order",
        POINTWISE_NAME,
        "exists bppl_factor_gap. bppl_factor_gap + a = z",
        "exists bppl_factor_gap. bppl_factor_gap + z = a",
    ),
    (
        "pointwise__reverse_product_order",
        POINTWISE_NAME,
        "exists bppl_result_gap. bppl_result_gap + n = q",
        "exists bppl_result_gap. bppl_result_gap + q = n",
    ),
    (
        "pointwise__omit_final_index",
        POINTWISE_NAME,
        "exists bppl_bound. bppl_bound + S i = l",
        "exists bppl_bound. bppl_bound + S S i = l",
    ),
    (
        "uniform__reverse_factor_order",
        UNIFORM_NAME,
        "exists bpulp_factor_gap. bpulp_factor_gap + x = a",
        "exists bpulp_factor_gap. bpulp_factor_gap + a = x",
    ),
    (
        "uniform__reverse_product_order",
        UNIFORM_NAME,
        "exists bpulp_result_gap. bpulp_result_gap + n = q",
        "exists bpulp_result_gap. bpulp_result_gap + q = n",
    ),
    (
        "uniform__change_power_exponent",
        UNIFORM_NAME,
        power_relation("a", "l", "q", tag="bpulp_target_power"),
        power_relation("a", "n", "q", tag="bpulp_target_power"),
    ),
)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_finite_product_order_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_order_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    table = {item.name: item for item in rows}
    assert len(table) == len(rows)
    return table


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    support = _table(_support_specs())
    collisions = set(public) & set(support)
    assert all(public[name] == support[name] for name in collisions)
    assert not (set(EXPECTED_NAMES) & set(public))
    assert not (set(EXPECTED_NAMES) & set(support))
    return public | {
        name: item for name, item in support.items() if name not in public
    }


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
    dependency_proofs = tuple(
        _close(dependency) for dependency in item.dependencies
    )
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


def _proof_dag_digest(proof: Proof) -> str:
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


def test_finite_product_order_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    table = _table(rows)
    expected_statements = _expected_statements()
    assert make_finite_product_order_candidate_theorems(TheoremSpec) == rows
    assert tuple(table) == EXPECTED_NAMES
    assert len(rows) == len(set(EXPECTED_NAMES)) == 2
    assert {item.name: item.statement for item in rows} == expected_statements
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_finite_product_order_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert set(table[POINTWISE_NAME].dependencies) - {"mul_le_mul"} <= stable
    assert table[UNIFORM_NAME].dependencies[0] in stable
    assert table[UNIFORM_NAME].dependencies[1] == POINTWISE_NAME

    alpha_mul = editions_v7.entry(
        "mul_le_mul", edition=editions_v7.EditionName.ALPHA
    )
    assert alpha_mul is not None
    assert alpha_mul.spec == _table(_support_specs())["mul_le_mul"]
    assert alpha_mul.membership is editions_v7.Membership.ALPHA_ONLY
    assert alpha_mul.evidence is editions_v7.EvidenceStatus.BODY_CHECKED
    assert not alpha_mul.checked_use
    assert editions_v7.entry(
        "mul_le_mul", edition=editions_v7.EditionName.STABLE
    ) is None

    provider_token = "finite_product_order_candidate"
    for authority_module in (
        stable_module,
        alpha_enrollment_v7,
        editions_v7,
    ):
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
                "Product(",
                "Pow(",
                "Le(",
                "<=",
                "^",
                "DNE",
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
            )
        )
        available.add(item.name)


def test_finite_product_order_public_binders_and_orientations_are_exact() -> None:
    statements = _expected_statements()
    pointwise = statements[POINTWISE_NAME]
    uniform = statements[UNIFORM_NAME]

    assert pointwise.startswith("forall b c d e l n q. ")
    assert uniform.startswith("forall b c a l n q. ")
    assert pointwise.count(
        "exists bppl_bound. bppl_bound + S i = l"
    ) == 1
    assert pointwise.count(
        "exists bppl_factor_gap. bppl_factor_gap + a = z"
    ) == 1
    assert pointwise.endswith(
        "exists bppl_result_gap. bppl_result_gap + n = q"
    )
    assert uniform.count(
        "exists bpulp_bound. bpulp_bound + S i = l"
    ) == 1
    assert uniform.count(
        "exists bpulp_factor_gap. bpulp_factor_gap + x = a"
    ) == 1
    assert uniform.endswith(
        "exists bpulp_result_gap. bpulp_result_gap + n = q"
    )


def test_omit_final_index_mutation_has_a_bounded_natural_counterexample() -> None:
    # Regression-only semantics: at length one the mutated premise is
    # vacuous, while the one-factor products 2 and 1 violate its conclusion.
    assert not any(index + 2 <= 1 for index in range(1))
    assert 2 > 1


def test_finite_product_order_placeholder_manifests_are_fail_closed() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    for case_id, row_name, old, new in BOUNDARY_MUTATION_CASES:
        assert case_id
        assert row_name in EXPECTED_NAMES
        assert old != new
        assert _expected_statements()[row_name].count(old) == 1


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_finite_product_order_artifact_receipts_are_frozen(
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
        f"FINITE PRODUCT ORDER ARTIFACT row={row_name!r} actual={actual!r}",
        flush=True,
    )
    assert EXPECTED_ARTIFACTS[row_name] is not None, (
        f"freeze deterministic artifact receipt for {row_name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[row_name]


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_finite_product_order_bodies_and_envelopes_are_frozen(
    row_name: str,
) -> None:
    item = _table(_specs())[row_name]
    body, target = _body(item)
    assert check((), body, target)
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    actual_body = (
        len(item.dependencies),
        len(item.script),
        nodes,
        depth,
        objects,
        edges,
        reused,
    )

    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    actual_envelope = _proof_envelope_metrics_bounded(
        body,
        max_proof_occurrences=limits.max_body_occurrences,
        max_proof_objects=limits.max_body_objects,
        max_proof_depth=limits.max_body_depth,
        max_annotation_occurrences=limits.max_body_annotation_occurrences,
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_body_envelope_depth,
        label=f"finite product order body {row_name}",
    )

    print(
        "FINITE PRODUCT ORDER BODY "
        f"row={row_name!r} actual={actual_body!r} "
        f"envelope={actual_envelope!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    assert EXPECTED_BODIES[row_name] is not None, (
        f"freeze body receipt for {row_name}: {actual_body!r}"
    )
    assert EXPECTED_ENVELOPES[row_name] is not None, (
        f"freeze envelope receipt for {row_name}: {actual_envelope!r}"
    )
    assert actual_body == EXPECTED_BODIES[row_name]
    assert actual_envelope == EXPECTED_ENVELOPES[row_name]


@pytest.mark.parametrize(
    ("row_name", "dependency"),
    tuple(
        (row_name, dependency)
        for row_name, dependencies in EXPECTED_DEPENDENCIES.items()
        for dependency in dependencies
    ),
)
def test_finite_product_order_every_direct_dependency_is_live(
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
def test_finite_product_order_false_conclusions_are_rejected(
    row_name: str,
) -> None:
    item = _table(_specs())[row_name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(row_name))


@pytest.mark.parametrize(
    ("case_id", "row_name", "old", "new"),
    BOUNDARY_MUTATION_CASES,
    ids=tuple(case[0] for case in BOUNDARY_MUTATION_CASES),
)
def test_finite_product_order_boundary_mutations_are_rejected(
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
def test_finite_product_order_empty_context_closures_are_frozen(
    row_name: str,
) -> None:
    item = _table(_specs())[row_name]
    formula, certificate = _close(row_name)
    assert formula == _closed_formula(item.statement)
    assert check((), certificate, formula)
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    actual = (
        nodes,
        depth,
        objects,
        edges,
        reused,
        _proof_dag_digest(certificate),
    )

    print(
        f"FINITE PRODUCT ORDER CLOSURE row={row_name!r} actual={actual!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(
        type(node) is DNE for node in _walk_proof(certificate)
    )
    for index in range(len(item.dependencies)):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    assert EXPECTED_CLOSURES[row_name] is not None, (
        f"freeze empty-context closure receipt for {row_name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[row_name]
