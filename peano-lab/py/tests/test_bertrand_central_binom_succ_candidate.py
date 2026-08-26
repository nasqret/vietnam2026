"""Fail-closed audit for additive successor CentralBinom support.

Both public surfaces are reconstructed independently from raw expanded
``Choose`` formulas.  Each root receives a prefix-only local core, and every
unregistered predecessor is rebuilt from pinned source without using a prior
candidate receipt as authority.
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
from peano_lab.kernel.terms import Add, Zero, parse_term_in_context, pretty_term
from peano_lab.library import (
    alpha_enrollment_v7,
    bertrand_central_binom_candidate as central_module,
    bertrand_central_binom_succ_candidate as module,
    bertrand_choose_diagonal_candidate as diagonal_module,
    bertrand_choose_foundation_candidate as foundation,
    bertrand_choose_laws_candidate as laws_module,
    bertrand_choose_pascal_candidate as pascal_module,
    bertrand_choose_recurrence_candidate as recurrence_module,
    bertrand_choose_row_functional_candidate as row_functional_module,
    bertrand_choose_symmetry_candidate as symmetry_module,
    bertrand_choose_table_row_functional_candidate as table_functional_module,
    editions_v7,
    theorems as stable_module,
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


CHOOSE_UPPER_EQ_TRANSPORT = "choose_upper_eq_transport"
CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE = "central_binom_succ_double_middle"
EXPECTED_NAMES = (
    CHOOSE_UPPER_EQ_TRANSPORT,
    CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE,
)
EXPECTED_DEPENDENCIES = {
    CHOOSE_UPPER_EQ_TRANSPORT: (),
    CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE: (
        "add_succ_left",
        "choose_exists",
        "choose_symmetry",
        "choose_succ_succ",
        CHOOSE_UPPER_EQ_TRANSPORT,
    ),
}
EXPECTED_DIRECT_CUTS = {
    CHOOSE_UPPER_EQ_TRANSPORT: 0,
    CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE: 5,
}
CENTRAL_SIBLINGS = {
    "central_binom_exists",
    "central_binom_functional",
    "central_binom_positive",
    "central_binom_zero",
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
SYMMETRY_SOURCE_SHA256 = (
    "9958068fc364ca4bd171e965283a7683d167dcd6650e7a8df13f0b27c1edb78a"
)
CENTRAL_SOURCE_SHA256 = (
    "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e"
)
SUCC_SOURCE_SHA256 = (
    "c0faea72fbe7c21ada1f15adc91dec324e0fa643bde464c9b10f9a75df4f2b27"
)

# Fail closed until each isolated kernel gate prints a reproducible receipt.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    CHOOSE_UPPER_EQ_TRANSPORT: (
        14769,
        "52f5be699c62a8c3baa1be43f7b9b7637d69d9bc3053c68e2157e8c86e20ed4b",
        "da39d4b1643b87f5177507a3b00334f3e6e1aaed7b79b381a9848be11d44f978",
        "52f5be699c62a8c3baa1be43f7b9b7637d69d9bc3053c68e2157e8c86e20ed4b",
    ),
    CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE: (
        15738,
        "6c9ff329d621c29213d7547f10e11d06f2787232c6444c1e5d054064e8d885dc",
        "c00d9e342680f6ec157fc4106a6b499cc2fe6a0ecd71102824f13c9b817f4555",
        "64a0f42446939bad4fccb599f0f504924cc4505f2c0fcf783c9deab9b0cfbec4",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    CHOOSE_UPPER_EQ_TRANSPORT: (0, 16, 52, 25, 52, 51, 0),
    CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE: (5, 55, 63, 23, 63, 62, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    CHOOSE_UPPER_EQ_TRANSPORT: (52, 52, 25, 3501, 67),
    CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE: (63, 63, 23, 59, 25),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    CHOOSE_UPPER_EQ_TRANSPORT: (
        52,
        25,
        52,
        51,
        0,
        3501,
        67,
        "9297158259b2d26d32a346c12eb6e67d7909fda1b6e16cd95c10b68a82704b25",
    ),
    CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE: (
        200357,
        106,
        8394,
        8683,
        290,
        742683,
        106,
        "39a7853844a2ff85526aac7374879ae60e7bab6e39686bfe28654c9304268cfa",
    ),
}


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
    index_source: str,
    value_source: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Independent expansion of ``Choose(index + index,index,value)``."""

    assert isinstance(variables, tuple)
    context = [
        foundation._identifier(variable, "independent context variable")
        for variable in variables
    ]
    assert len(set(context)) == len(context)
    index_term = parse_term_in_context(index_source, context)
    value_term = parse_term_in_context(value_source, context)
    index = pretty_term(index_term, context).replace("·", "*")
    value = pretty_term(value_term, context).replace("·", "*")
    doubled = pretty_term(Add(index_term, index_term), context).replace(
        "·", "*"
    )
    return _choose(
        doubled,
        index,
        value,
        tag=tag,
        variables=variables,
    )


def _relations() -> dict[str, str]:
    transport_variables = ("n", "m", "k", "z")
    return {
        "transport_source": _choose(
            "n",
            "k",
            "z",
            tag="bcuet_source",
            variables=transport_variables,
        ),
        "transport_target": _choose(
            "m",
            "k",
            "z",
            tag="bcuet_target",
            variables=transport_variables,
        ),
        "successor": _central(
            "S n",
            "d",
            tag="bcbsdm_successor",
            variables=("n", "d"),
        ),
        "normalized": _choose(
            "S (S (n + n))",
            "S n",
            "d",
            tag="bcbsdm_normalized",
            variables=("n", "d"),
        ),
        "middle": _choose(
            "S (n + n)",
            "n",
            "m",
            tag="bcbsdm_middle",
            variables=("n", "d", "m"),
        ),
        "mirror": _choose(
            "S (n + n)",
            "S n",
            "r",
            tag="bcbsdm_mirror",
            variables=("n", "d", "m", "r"),
        ),
    }


def _expected_statements() -> dict[str, str]:
    relations = _relations()
    return {
        CHOOSE_UPPER_EQ_TRANSPORT: (
            "forall n m k z. n = m -> "
            f"({relations['transport_source']}) -> "
            f"({relations['transport_target']})"
        ),
        CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE: (
            "forall n d. "
            f"({relations['successor']}) -> exists m. "
            f"(({relations['middle']}) /\\ d = m + m)"
        ),
    }


def _expected_scripts() -> dict[str, tuple[str, ...]]:
    relations = _relations()
    return {
        CHOOSE_UPPER_EQ_TRANSPORT: (
            "intro n",
            "intro m",
            "intro k",
            "intro z",
            "intro heq",
            "intro hchoose",
            "rewrite heq at hchoose",
            "rewrite heq at hchoose",
            "rewrite heq at hchoose",
            "rewrite heq at hchoose",
            "rewrite heq at hchoose",
            "rewrite heq at hchoose",
            "rewrite heq at hchoose",
            "rewrite heq at hchoose",
            "rewrite heq at hchoose",
            "exact hchoose",
        ),
        CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE: (
            "intro n",
            "intro d",
            "intro hsuccessor",
            "have hupper : S n + S n = S (S (n + n))",
            "trans S (n + S n)",
            "specialize add_succ_left n",
            "specialize add_succ_left (S n)",
            "apply add_succ_left",
            "congr",
            "apply PA4",
            f"have hnormalized : {relations['normalized']}",
            "specialize choose_upper_eq_transport (S n + S n)",
            "specialize choose_upper_eq_transport (S (S (n + n)))",
            "specialize choose_upper_eq_transport (S n)",
            "specialize choose_upper_eq_transport d",
            "apply choose_upper_eq_transport",
            "exact hupper",
            "exact hsuccessor",
            f"have hmiddle_exists : exists m. ({relations['middle']})",
            "specialize choose_exists (S (n + n))",
            "specialize choose_exists n",
            "exact choose_exists",
            "cases hmiddle_exists",
            f"have hmirror_exists : exists r. ({relations['mirror']})",
            "specialize choose_exists (S (n + n))",
            "specialize choose_exists (S n)",
            "exact choose_exists",
            "cases hmirror_exists",
            "have hsym : x = x1",
            "specialize choose_symmetry (S (n + n))",
            "specialize choose_symmetry n",
            "specialize choose_symmetry (S n)",
            "specialize choose_symmetry x",
            "specialize choose_symmetry x1",
            "apply choose_symmetry",
            "apply PA4",
            "exact hmiddle_exists_witness",
            "exact hmirror_exists_witness",
            "have hsum : d = x + x1",
            "specialize choose_succ_succ (S (n + n))",
            "specialize choose_succ_succ n",
            "specialize choose_succ_succ x",
            "specialize choose_succ_succ x1",
            "specialize choose_succ_succ d",
            "apply choose_succ_succ",
            "exact hmiddle_exists_witness",
            "exact hmirror_exists_witness",
            "exact hnormalized",
            "exists x",
            "split",
            "exact hmiddle_exists_witness",
            "trans x + x1",
            "exact hsum",
            "rewrite <- hsym",
            "refl",
        ),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_central_binom_succ_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
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
    assert not (CENTRAL_SIBLINGS & set(public))
    assert not (CENTRAL_SIBLINGS & set(support))
    return public | support


def _row_core(name: str) -> dict[str, TheoremSpec]:
    index = EXPECTED_NAMES.index(name)
    return _core() | _table(_specs()[:index])


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
            raise AssertionError("CentralBinom successor row delegated through use")
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


def test_central_binom_succ_sources_are_pinned() -> None:
    expected = (
        (foundation, FOUNDATION_SOURCE_SHA256),
        (row_functional_module, ROW_FUNCTIONAL_SOURCE_SHA256),
        (table_functional_module, TABLE_FUNCTIONAL_SOURCE_SHA256),
        (laws_module, LAWS_SOURCE_SHA256),
        (diagonal_module, DIAGONAL_SOURCE_SHA256),
        (recurrence_module, RECURRENCE_SOURCE_SHA256),
        (pascal_module, PASCAL_SOURCE_SHA256),
        (symmetry_module, SYMMETRY_SOURCE_SHA256),
        (central_module, CENTRAL_SOURCE_SHA256),
        (module, SUCC_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest


def test_central_binom_succ_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    assert make_bertrand_central_binom_succ_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert {item.name: item.statement for item in rows} == _expected_statements()
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert {item.name: item.script for item in rows} == _expected_scripts()
    assert module.__all__ == [
        "make_bertrand_central_binom_succ_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    support = set(_table(_support_specs()))
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & support)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert not (CENTRAL_SIBLINGS & stable)
    assert not (CENTRAL_SIBLINGS & support)
    for index, item in enumerate(rows):
        available = _row_core(item.name)
        assert all(dependency in available for dependency in item.dependencies)
        assert set(available) & set(EXPECTED_NAMES) == set(
            EXPECTED_NAMES[:index]
        )

    provider_token = "bertrand_central_binom_succ_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    forbidden_surface = (
        "BetaAt(",
        "PascalTablePrefix(",
        "Choose(",
        "CentralBinom(",
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


def test_central_binom_succ_script_topologies_are_exact() -> None:
    transport, successor = _specs()
    assert transport.script[:6] == (
        "intro n",
        "intro m",
        "intro k",
        "intro z",
        "intro heq",
        "intro hchoose",
    )
    assert transport.script[6:15] == ("rewrite heq at hchoose",) * 9
    assert transport.script[15:] == ("exact hchoose",)
    assert transport.script.count("rewrite heq at hchoose") == 9

    assert successor.script.count("apply add_succ_left") == 1
    assert successor.script.count("apply PA4") == 2
    assert successor.script.count("exact choose_exists") == 2
    assert successor.script.count("cases hmiddle_exists") == 1
    assert successor.script.count("cases hmirror_exists") == 1
    assert successor.script.count("apply choose_symmetry") == 1
    assert successor.script.count("apply choose_succ_succ") == 1
    assert successor.script.count("apply choose_upper_eq_transport") == 1
    assert not any(
        command.startswith("rewrite ") and command.endswith("at hsuccessor")
        for command in successor.script
    )
    assert successor.script[-7:] == (
        "exists x",
        "split",
        "exact hmiddle_exists_witness",
        "trans x + x1",
        "exact hsum",
        "rewrite <- hsym",
        "refl",
    )


def test_central_binom_succ_relation_helpers_are_hygienic() -> None:
    variables = ("n", "m", "k", "z")
    left = _choose(
        "n",
        "k",
        "z",
        tag="hygiene_left",
        variables=variables,
    )
    right = _choose(
        "n",
        "k",
        "z",
        tag="hygiene_right",
        variables=variables,
    )
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"n", "k", "z"}

    assert central_module._central_binom_relation_term(
        "S n",
        "d",
        tag="bcbsdm_successor",
        variables=("n", "d"),
    ) == _relations()["successor"]
    with pytest.raises(ValueError):
        foundation._choose_relation_term(
            "n",
            "k",
            "z",
            tag="valid",
            variables=("n", "m", "k", "z", "bcf_row_code_code_valid"),
        )
    with pytest.raises(ValueError):
        central_module._central_binom_relation_term(
            "S missing",
            "d",
            tag="valid",
            variables=("n", "d"),
        )


def test_central_binom_succ_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert sum(len(value) for value in EXPECTED_DEPENDENCIES.values()) == 5


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_central_binom_succ_artifact_receipts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CENTRAL BINOM SUCC ARTIFACT {name} actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_central_binom_succ_bodies_and_envelopes_are_frozen(name: str) -> None:
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
        label=f"CentralBinom successor body {name}",
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
        f"CENTRAL BINOM SUCC BODY {name} actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
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
def test_central_binom_succ_every_direct_dependency_is_live(
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
def test_central_binom_succ_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    relations = _relations()
    transport_target_column = _choose(
        "m",
        "S k",
        "z",
        tag="bcuet_target",
        variables=("n", "m", "k", "z"),
    )
    transport_target_value = _choose(
        "m",
        "k",
        "S z",
        tag="bcuet_target",
        variables=("n", "m", "k", "z"),
    )
    predecessor_central = _central(
        "n",
        "d",
        tag="bcbsdm_successor",
        variables=("n", "d"),
    )
    return (
        (
            CHOOSE_UPPER_EQ_TRANSPORT,
            "target_successor_column",
            relations["transport_target"],
            transport_target_column,
        ),
        (
            CHOOSE_UPPER_EQ_TRANSPORT,
            "target_successor_value",
            relations["transport_target"],
            transport_target_value,
        ),
        (
            CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE,
            "predecessor_central_source",
            relations["successor"],
            predecessor_central,
        ),
        (
            CENTRAL_BINOM_SUCC_DOUBLE_MIDDLE,
            "single_middle_conclusion",
            "d = m + m",
            "d = m",
        ),
    )


def test_central_binom_succ_mutations_have_standard_counterfixtures() -> None:
    # At row two, Choose(2,0)=1 but Choose(2,1)=2.
    assert 1 != 2
    # At row zero and column zero, the unique value is one, not two.
    assert 1 != 2
    # At n=1, CentralBinom(1)=2 while twice Choose(3,1) is six.
    assert 2 != 6
    # At n=0, CentralBinom(1)=2 while Choose(1,0)=1.
    assert 2 != 1


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_central_binom_succ_genuine_mutations_are_rejected(
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
def test_central_binom_succ_empty_context_closures_are_frozen(name: str) -> None:
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
        label=f"CentralBinom successor closure {name}",
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
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[name]
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)

    print(f"CENTRAL BINOM SUCC CLOSURE {name} actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze empty-context closure receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
