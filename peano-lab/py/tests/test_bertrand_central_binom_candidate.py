"""Fail-closed audit for conservative relational CentralBinom wrappers.

The public surfaces are rebuilt independently as raw
``Choose(n + n,n,value)`` formulas.  Every predecessor candidate is rebuilt
from source and each CentralBinom row is closed independently; no sibling row
or receipt is admitted as authority.
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
    bertrand_central_binom_candidate as module,
    bertrand_choose_diagonal_candidate as diagonal_module,
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_laws_candidate as laws_module,
    bertrand_choose_pascal_candidate as pascal_module,
    bertrand_choose_positive_candidate as positive_module,
    bertrand_choose_recurrence_candidate as recurrence_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_table_row_functional_candidate as table_functional_module,
    editions_v7,
    theorems as stable_module,
)
from peano_lab.library.bertrand_central_binom_candidate import (
    make_bertrand_central_binom_candidate_theorems,
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


CENTRAL_BINOM_EXISTS = "central_binom_exists"
CENTRAL_BINOM_FUNCTIONAL = "central_binom_functional"
CENTRAL_BINOM_POSITIVE = "central_binom_positive"
EXPECTED_NAMES = (
    CENTRAL_BINOM_EXISTS,
    CENTRAL_BINOM_FUNCTIONAL,
    CENTRAL_BINOM_POSITIVE,
)
EXPECTED_DEPENDENCIES = {
    CENTRAL_BINOM_EXISTS: ("choose_exists",),
    CENTRAL_BINOM_FUNCTIONAL: ("choose_functional",),
    CENTRAL_BINOM_POSITIVE: ("choose_positive",),
}
EXPECTED_DIRECT_CUTS = {
    CENTRAL_BINOM_EXISTS: 1,
    CENTRAL_BINOM_FUNCTIONAL: 1,
    CENTRAL_BINOM_POSITIVE: 1,
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
CENTRAL_SOURCE_SHA256 = (
    "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e"
)

# Fail closed until each isolated kernel gate prints a reproducible receipt.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CENTRAL_BINOM_EXISTS: (
        7265,
        "7281ef4fe7ac3be8cf5af50c1a4e37269fe20c7b69912fa022b19ccbfa16d14c",
        "ec5b7c8f45b0a093504668bf1f8ecdbb3a828c60e2fa2dbb8b4cfcbcf8856e2a",
        "b1dc6ec47df0105889249f3936fdaac8c605cbd83e4a903199c7338fcb720af3",
    ),
    CENTRAL_BINOM_FUNCTIONAL: (
        14034,
        "3eb46885745d48434d5f898e98ea9b568dab9a9f816d6268ef6f1e2c4a5daee8",
        "b190ccac7b8f0effda0356a019c8002f1837fcadf433092413a64b4fa283a33a",
        "af0cb4150198587fa0feb9ebf5c7cc515fe21a7841e06d52f21b2a655b9eedc6",
    ),
    CENTRAL_BINOM_POSITIVE: (
        7278,
        "1dcbea1ee3f1c2b5541f26a84788b6d8713e875f4004aad810ba3bdb3084f60c",
        "40ceaa51ccf5392036ec96488e2526eec2e567d829bc7f339eaab45b6d4f8d4a",
        "6beaed7dbea49d99ebd3c20241472d8e2cdbdd557f9d607ba20a8832570b4bba",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    CENTRAL_BINOM_EXISTS: (1, 4, 11, 7, 11, 10, 0),
    CENTRAL_BINOM_FUNCTIONAL: (1, 12, 27, 17, 27, 26, 0),
    CENTRAL_BINOM_POSITIVE: (1, 10, 22, 14, 22, 21, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CENTRAL_BINOM_EXISTS: (11, 11, 7, 4, 7),
    CENTRAL_BINOM_FUNCTIONAL: (27, 27, 17, 6, 17),
    CENTRAL_BINOM_POSITIVE: (22, 22, 14, 9, 16),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CENTRAL_BINOM_EXISTS: (
        89503,
        100,
        5359,
        5602,
        244,
        296635,
        100,
        "66dd369399e0cd43f9e8062a828156e46ae10ad40efaa2d4fb3405f88442f53b",
    ),
    CENTRAL_BINOM_FUNCTIONAL: (
        4562,
        80,
        1800,
        1844,
        45,
        23220,
        82,
        "9d18a0de093b384c01385dc560d40915201bf65e52f885957a063196b3d1af19",
    ),
    CENTRAL_BINOM_POSITIVE: (
        99729,
        104,
        8060,
        8343,
        284,
        364069,
        104,
        "4cfed31a80a56bf32d308b657d7065c26f30b815259fe593f32105bc8ef2941d",
    ),
}


def _central_binom_relation(
    n: str,
    value: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Independent copy of the frozen authoring-only expansion contract."""

    if not isinstance(variables, tuple):
        raise ValueError("central-binomial variables must be a tuple")
    context = [
        foundation._identifier(variable, "central-binomial context variable")
        for variable in variables
    ]
    if len(set(context)) != len(context):
        raise ValueError("central-binomial context variables must be distinct")

    parsed_terms = []
    for source, label in (
        (n, "central-binomial index"),
        (value, "central-binomial value"),
    ):
        if not isinstance(source, str) or not source:
            raise ValueError(f"{label} must be a nonempty Peano term")
        try:
            parsed_terms.append(parse_term_in_context(source, context))
        except ValueError as exc:
            raise ValueError(f"{label} must be a Peano term: {exc}") from None

    index_term, value_term = parsed_terms
    rendered_index = pretty_term(index_term, context).replace("·", "*")
    rendered_value = pretty_term(value_term, context).replace("·", "*")
    doubled_index = pretty_term(Add(index_term, index_term), context).replace(
        "·", "*"
    )
    return foundation._choose_relation_term(
        doubled_index,
        rendered_index,
        rendered_value,
        tag=tag,
        variables=variables,
    )


def _expected_relations() -> dict[str, tuple[str, ...]]:
    functional_variables = ("n", "x", "y")
    return {
        CENTRAL_BINOM_EXISTS: (
            _central_binom_relation(
                "n",
                "z",
                tag="bcbe_result",
                variables=("n", "z"),
            ),
        ),
        CENTRAL_BINOM_FUNCTIONAL: (
            _central_binom_relation(
                "n",
                "x",
                tag="bcbf_left",
                variables=functional_variables,
            ),
            _central_binom_relation(
                "n",
                "y",
                tag="bcbf_right",
                variables=functional_variables,
            ),
        ),
        CENTRAL_BINOM_POSITIVE: (
            _central_binom_relation(
                "n",
                "z",
                tag="bcbp_source",
                variables=("n", "z"),
            ),
        ),
    }


def _expected_statements() -> dict[str, str]:
    relations = _expected_relations()
    exists_relation = relations[CENTRAL_BINOM_EXISTS][0]
    functional_left, functional_right = relations[CENTRAL_BINOM_FUNCTIONAL]
    positive_relation = relations[CENTRAL_BINOM_POSITIVE][0]
    return {
        CENTRAL_BINOM_EXISTS: f"forall n. exists z. ({exists_relation})",
        CENTRAL_BINOM_FUNCTIONAL: (
            "forall n x y. "
            f"({functional_left}) -> ({functional_right}) -> x = y"
        ),
        CENTRAL_BINOM_POSITIVE: (
            f"forall n z. ({positive_relation}) -> exists p. z = S p"
        ),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_central_binom_candidate_theorems(TheoremSpec)


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
        *make_bertrand_choose_positive_candidate_theorems(TheoremSpec),
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
    assert name in EXPECTED_NAMES
    # The three wrappers are deliberately independent siblings.
    return _core()


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
            raise AssertionError("CentralBinom wrapper delegated through use")
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


def test_central_binom_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_functional_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_functional_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
        (laws_module, LAWS_SOURCE_SHA256),
        (diagonal_module, DIAGONAL_SOURCE_SHA256),
        (recurrence_module, RECURRENCE_SOURCE_SHA256),
        (pascal_module, PASCAL_SOURCE_SHA256),
        (positive_module, POSITIVE_SOURCE_SHA256),
        (module, CENTRAL_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest


def test_central_binom_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    assert make_bertrand_central_binom_candidate_theorems(TheoremSpec) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert {item.name: item.statement for item in rows} == (
        _expected_statements()
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_central_binom_candidate_theorems"
    ]
    for name, relations in _expected_relations().items():
        item = _table(rows)[name]
        assert all(relation in item.statement for relation in relations)
        assert "n + n" in item.statement
        assert "2 * n" not in item.statement

    stable = set(_specs_by_name())
    support = set(_table(_support_specs()))
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & support)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert all(
        dependency in _core()
        for item in rows
        for dependency in item.dependencies
    )
    assert all(
        not (set(item.dependencies) & set(EXPECTED_NAMES)) for item in rows
    )

    provider_token = "bertrand_central_binom_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    forbidden_surface = (
        "BetaAt(",
        "PascalTablePrefix(",
        "Choose(",
        "CentralBinom(",
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


def test_central_binom_helper_contract_and_scripts_are_exact() -> None:
    assert module._central_binom_relation_term(
        "n",
        "z",
        tag="bcbe_result",
        variables=("n", "z"),
    ) == _expected_relations()[CENTRAL_BINOM_EXISTS][0]

    exists, functional, positive = _specs()
    assert exists.script == (
        "intro n",
        "specialize choose_exists (n + n)",
        "specialize choose_exists n",
        "exact choose_exists",
    )
    assert functional.script == (
        "intro n",
        "intro x",
        "intro y",
        "intro hleft",
        "intro hright",
        "specialize choose_functional (n + n)",
        "specialize choose_functional n",
        "specialize choose_functional x",
        "specialize choose_functional y",
        "apply choose_functional",
        "exact hleft",
        "exact hright",
    )
    assert positive.script == (
        "intro n",
        "intro z",
        "intro hcentral",
        "specialize choose_positive (n + n)",
        "specialize choose_positive n",
        "specialize choose_positive z",
        "apply choose_positive",
        "exists n",
        "refl",
        "exact hcentral",
    )
    assert not any(
        command.startswith("induction ") or command.startswith("rewrite ")
        for item in (exists, functional, positive)
        for command in item.script
    )


def test_central_binom_helper_is_hygienic() -> None:
    left = module._central_binom_relation_term(
        "n",
        "z",
        tag="hygiene_left",
        variables=("n", "z"),
    )
    right = module._central_binom_relation_term(
        "n",
        "z",
        tag="hygiene_right",
        variables=("n", "z"),
    )
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"n", "z"}

    compound = module._central_binom_relation_term(
        "S n",
        "S z",
        tag="compound",
        variables=("n", "z"),
    )
    assert compound == _central_binom_relation(
        "S n",
        "S z",
        tag="compound",
        variables=("n", "z"),
    )
    parsed_compound, free_compound = parse_formula_with_names(compound)
    assert isinstance(parsed_compound, Formula)
    assert set(free_compound) == {"n", "z"}
    assert "S n + S n" in compound

    zero = module._central_binom_relation_term(
        "0",
        "0",
        tag="zero",
        variables=(),
    )
    assert zero == _central_binom_relation(
        "0",
        "0",
        tag="zero",
        variables=(),
    )
    parsed_zero, free_zero = parse_formula_with_names(zero)
    assert parsed_zero == _closed_formula(zero)
    assert not free_zero
    assert "0 + 0" in zero

    with pytest.raises(ValueError):
        module._central_binom_relation_term(
            "S missing",
            "z",
            tag="valid",
            variables=("n", "z"),
        )
    with pytest.raises(ValueError):
        module._central_binom_relation_term(
            "n",
            "S missing",
            tag="valid",
            variables=("n", "z"),
        )
    with pytest.raises(ValueError):
        module._central_binom_relation_term(
            "n",
            "z",
            tag="valid",
            variables=("n", "n", "z"),
        )
    with pytest.raises(ValueError):
        module._central_binom_relation_term(
            "n",
            "z",
            tag="valid",
            variables=["n", "z"],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError):
        module._central_binom_relation_term(
            "n",
            "z",
            tag="bad tag",
            variables=("n", "z"),
        )
    with pytest.raises(ValueError):
        module._central_binom_relation_term(
            "n",
            "z",
            tag="valid",
            variables=("n", "z", "bcf_row_code_code_valid"),
        )


def test_central_binom_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_central_binom_artifact_receipts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CENTRAL BINOM ARTIFACT {name} actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_central_binom_bodies_and_envelopes_are_frozen(name: str) -> None:
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
        label=f"CentralBinom body {name}",
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
        f"CENTRAL BINOM BODY {name} actual={actual!r} "
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
def test_central_binom_every_direct_dependency_is_live(
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
def test_central_binom_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    relations = _expected_relations()
    exists_relation = relations[CENTRAL_BINOM_EXISTS][0]
    functional_right = relations[CENTRAL_BINOM_FUNCTIONAL][1]
    positive_relation = relations[CENTRAL_BINOM_POSITIVE][0]
    functional_shifted = foundation._choose_relation_term(
        "n + n",
        "S n",
        "y",
        tag="bcbf_right",
        variables=("n", "x", "y"),
    )
    positive_shifted = foundation._choose_relation_term(
        "n + n",
        "S (n + n)",
        "z",
        tag="bcbp_source",
        variables=("n", "z"),
    )
    return (
        (
            CENTRAL_BINOM_EXISTS,
            "forced_zero_value",
            f"exists z. ({exists_relation})",
            f"exists z. (({exists_relation}) /\\ z = 0)",
        ),
        (
            CENTRAL_BINOM_FUNCTIONAL,
            "right_successor_column",
            functional_right,
            functional_shifted,
        ),
        (
            CENTRAL_BINOM_POSITIVE,
            "out_of_range_source_column",
            positive_relation,
            positive_shifted,
        ),
        (
            CENTRAL_BINOM_POSITIVE,
            "double_successor_conclusion",
            "exists p. z = S p",
            "exists p. z = S (S p)",
        ),
    )


def test_central_binom_mutations_have_standard_counterfixtures() -> None:
    # CentralBinom(0)=C(0,0)=1, not zero.
    assert 1 != 0
    # At n=1, C(2,1)=2 but the shifted right value C(2,2)=1.
    assert 2 != 1
    # Column S(n+n) is out of range and therefore zero.
    assert 0 != 1
    # CentralBinom(0)=1 is not a double successor.
    assert 1 != 2


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_central_binom_genuine_mutations_are_rejected(
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
def test_central_binom_empty_context_closures_are_frozen(name: str) -> None:
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
        label=f"CentralBinom closure {name}",
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
    print(f"CENTRAL BINOM CLOSURE {name} actual={actual!r}", flush=True)
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
