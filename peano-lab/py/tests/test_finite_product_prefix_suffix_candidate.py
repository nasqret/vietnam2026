"""Fail-closed audit for exact beta-product prefix/suffix splitting.

The two rows remain isolated candidates.  This focused harness freezes their
expanded contracts, hygienic compound-term builders, dependency topology,
artifacts, bodies, envelopes, mutations, and empty-context closures.  Every
receipt starts as ``None`` and therefore fails closed until its own successful
audit run supplies the exact deterministic value.
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
from peano_lab.kernel.formulas import (
    Eq,
    Formula,
    Imp,
    parse_formula,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import (
    alpha_enrollment_v7,
    editions_v7,
    finite_product_prefix_suffix_candidate as module,
    theorems as stable_module,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.finite_fold_surface import product_relation
from peano_lab.library.finite_product_prefix_suffix_candidate import (
    make_finite_product_prefix_suffix_candidate_theorems,
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


SPLIT_NAME = "beta_product_prefix_suffix_split"
CONCAT_NAME = "beta_product_prefix_suffix_concat"
EXPECTED_NAMES = (SPLIT_NAME, CONCAT_NAME)

EXPECTED_DEPENDENCIES = {
    SPLIT_NAME: (
        "beta_product_exists",
        "beta_product_zero",
        "beta_product_succ_decompose",
        "beta_product_succ_append",
        "le_succ",
        "le_refl",
        "mul_one",
        "mul_assoc",
    ),
    CONCAT_NAME: (
        "beta_product_exists",
        "beta_product_functional",
        SPLIT_NAME,
    ),
}

# These manifests deliberately fail closed until each corresponding isolated
# audit succeeds.  They are comparison receipts, never proof authority.
EXPECTED_ARTIFACTS: dict[
    str, tuple[int, str, str, str] | None
] = {
    SPLIT_NAME: (
        6_422,
        "3184387b27765bcf01dee70c6722e14d817881404475f1a1d592c41d7955e1a9",
        "b2747e1330717bacad7b69c48d3a50ebc0194227c280a63faad23af13c582b12",
        "837e157648372236e13bdb92f7fdb3fa298fced45e2906ada0d82976d6620f1b",
    ),
    CONCAT_NAME: (
        6_583,
        "09f2d10e4bd8e545bf3aa107b3c71e312b445a56229338dbce2e5b7de7b8928e",
        "9c696e813e564c3f71ceda4a085e164cef4b0533375891d6f8c37d6739b04ca3",
        "3c5306cbdcd2ab9f1b31706dfc87fdd269d4427d42eb92a23e058aa309e1dcf2",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    SPLIT_NAME: (8, 107, 148, 35, 144, 147, 4),
    CONCAT_NAME: (3, 75, 130, 43, 130, 129, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    SPLIT_NAME: (148, 144, 35, 1_508, 48),
    CONCAT_NAME: (130, 130, 43, 392, 49),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, str] | None
] = {
    SPLIT_NAME: (
        62_637,
        87,
        5_153,
        5_406,
        254,
        "822650022d2b1cabdb6550ccac1b6b41e0a7022b7a6bf9e4585b553048aa5929",
    ),
    CONCAT_NAME: (
        94_636,
        90,
        5_479,
        5_736,
        258,
        "ddbafd38041cdb16ca7b637f31119ed6453f595f557f84c3c57b698bf787f419",
    ),
}


def _expected_statements() -> dict[str, str]:
    split_shift = module._shifted_prefix(
        "b", "c", "z", "d", "l", "m", tag="bps_split_shift"
    )
    split_total = module._product_sum_relation(
        "b", "c", "l", "m", "n", tag="bps_split_total"
    )
    split_prefix = product_relation(
        "b", "c", "l", "p", tag="bps_split_prefix"
    )
    split_suffix = product_relation(
        "z", "d", "m", "q", tag="bps_split_suffix"
    )

    concat_shift = module._shifted_prefix(
        "b", "c", "z", "d", "l", "m", tag="bps_concat_shift"
    )
    concat_prefix = product_relation(
        "b", "c", "l", "p", tag="bps_concat_prefix"
    )
    concat_suffix = product_relation(
        "z", "d", "m", "q", tag="bps_concat_suffix"
    )
    concat_total = module._product_sum_mul_relation(
        "b", "c", "l", "m", "p", "q", tag="bps_concat_total"
    )

    return {
        SPLIT_NAME: (
            "forall b c z d l m n. "
            f"({split_shift}) -> ({split_total}) -> exists p q. "
            f"({split_prefix}) /\\ (({split_suffix}) /\\ n = p * q)"
        ),
        CONCAT_NAME: (
            "forall b c z d l m p q. "
            f"({concat_shift}) -> ({concat_prefix}) -> "
            f"({concat_suffix}) -> ({concat_total})"
        ),
    }


def _off_by_one_shift_source(statement_tag: str) -> tuple[str, str]:
    source = module._offset_beta_at(
        "b",
        "c",
        "l",
        "i",
        "a",
        tag=f"{statement_tag}_source",
    )
    shifted = source.replace("l + i", "l + S i")
    assert source.count("l + i") == 2
    assert shifted.count("l + S i") == 2
    return source, shifted


_SPLIT_OFF_BY_ONE = _off_by_one_shift_source("bps_split_shift")
_CONCAT_OFF_BY_ONE = _off_by_one_shift_source("bps_concat_shift")
_SPLIT_TOTAL = module._product_sum_relation(
    "b", "c", "l", "m", "n", tag="bps_split_total"
)
_SPLIT_TOTAL_SUCCESSOR_LEFT = _SPLIT_TOTAL.replace(
    "l + m", "S l + m"
)
_CONCAT_TOTAL = module._product_sum_mul_relation(
    "b", "c", "l", "m", "p", "q", tag="bps_concat_total"
)
_CONCAT_TOTAL_BAD_RESULT = _CONCAT_TOTAL.replace("p * q", "p * S q")
_CONCAT_SUFFIX = product_relation(
    "z", "d", "m", "q", tag="bps_concat_suffix"
)

BOUNDARY_MUTATION_CASES = (
    (
        "split__off_by_one_source_index",
        SPLIT_NAME,
        _SPLIT_OFF_BY_ONE[0],
        _SPLIT_OFF_BY_ONE[1],
    ),
    (
        "split__successor_left_total_length",
        SPLIT_NAME,
        _SPLIT_TOTAL,
        _SPLIT_TOTAL_SUCCESSOR_LEFT,
    ),
    (
        "split__successor_suffix_factor",
        SPLIT_NAME,
        "n = p * q",
        "n = p * S q",
    ),
    (
        "concat__off_by_one_source_index",
        CONCAT_NAME,
        _CONCAT_OFF_BY_ONE[0],
        _CONCAT_OFF_BY_ONE[1],
    ),
    (
        "concat__omit_suffix_product",
        CONCAT_NAME,
        f"({_CONCAT_SUFFIX}) -> ",
        "",
    ),
    (
        "concat__successor_suffix_result",
        CONCAT_NAME,
        _CONCAT_TOTAL,
        _CONCAT_TOTAL_BAD_RESULT,
    ),
)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_finite_product_prefix_suffix_candidate_theorems(TheoremSpec)


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


def test_product_prefix_suffix_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    table = _table(rows)
    expected_statements = _expected_statements()

    assert make_finite_product_prefix_suffix_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(table) == EXPECTED_NAMES
    assert len(rows) == len(set(EXPECTED_NAMES)) == 2
    assert {item.name: item.statement for item in rows} == expected_statements
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_finite_product_prefix_suffix_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert set(table[SPLIT_NAME].dependencies) <= stable
    assert set(table[CONCAT_NAME].dependencies[:-1]) <= stable
    assert table[CONCAT_NAME].dependencies[-1] == SPLIT_NAME

    provider_token = "finite_product_prefix_suffix_candidate"
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
                "Shift(",
                "Interval(",
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


def test_product_prefix_suffix_public_binders_and_associations_are_exact() -> None:
    statements = _expected_statements()
    split = statements[SPLIT_NAME]
    concat = statements[CONCAT_NAME]

    assert split.startswith("forall b c z d l m n. ")
    assert concat.startswith("forall b c z d l m p q. ")
    assert split.count("forall i a.") == 1
    assert concat.count("forall i a.") == 1
    assert split.count("l + i") == concat.count("l + i") == 2
    assert split.count("l + m") == concat.count("l + m") == 3
    assert split.count("n = p * q") == 1
    assert split.endswith("n = p * q)")
    assert "exists p q." in split
    assert "exists q p." not in split
    assert split.count("fps_bound_bps_split_shift + S i = m") == 1
    assert concat.count("fps_bound_bps_concat_shift + S i = m") == 1
    assert _SPLIT_TOTAL_SUCCESSOR_LEFT != _SPLIT_TOTAL
    assert _CONCAT_TOTAL_BAD_RESULT != _CONCAT_TOTAL


def test_product_prefix_suffix_compound_helpers_are_hygienic() -> None:
    first = module._offset_beta_at(
        "b", "c", "l", "i", "a", tag="helper_first"
    )
    second = module._offset_beta_at(
        "b", "c", "l", "i", "a", tag="helper_second"
    )
    assert first != second
    assert parse_formula(first) == parse_formula(second)
    assert first.count("l + i") == second.count("l + i") == 2

    sum_first = module._product_sum_relation(
        "b", "c", "l", "m", "n", tag="helper_sum_first"
    )
    sum_second = module._product_sum_relation(
        "b", "c", "l", "m", "n", tag="helper_sum_second"
    )
    assert sum_first != sum_second
    assert parse_formula(sum_first) == parse_formula(sum_second)
    assert sum_first.count("l + m") == sum_second.count("l + m") == 3

    with pytest.raises(ValueError):
        module._offset_beta_at(
            "b", "c", "l + i", "i", "a", tag="bad_compound"
        )
    with pytest.raises(ValueError):
        module._offset_beta_at(
            "fps_height_collision",
            "c",
            "l",
            "i",
            "a",
            tag="collision",
        )
    with pytest.raises(ValueError):
        module._product_sum_relation(
            "fps_accumulator_collision",
            "c",
            "l",
            "m",
            "n",
            tag="collision",
        )
    with pytest.raises(ValueError):
        module._shifted_prefix(
            "b", "c", "z", "d", "i", "m", tag="captured_index"
        )
    with pytest.raises(ValueError):
        module._shifted_prefix(
            "b", "c", "z", "d", "l", "a", tag="captured_value"
        )
    with pytest.raises(ValueError):
        module._shifted_prefix(
            "fps_bound_collision",
            "c",
            "z",
            "d",
            "l",
            "m",
            tag="collision",
        )


def test_product_prefix_suffix_mutations_have_genuine_boundaries() -> None:
    # For l=0,m=1, source [2,3] and suffix [3], the off-by-one Shift holds
    # while the intended split 2 = 3 fails.
    source = (2, 3)
    suffix = (3,)
    assert source[0 + 1] == suffix[0]
    assert source[0] != suffix[0]
    assert 1 + 0 != 1 + 1
    assert 2 * 3 != 2 * (3 + 1)
    assert 2 + 1 != 1 + 1
    for case_id, row_name, old, new in BOUNDARY_MUTATION_CASES:
        assert case_id
        assert row_name in EXPECTED_NAMES
        assert old != new
        assert _expected_statements()[row_name].count(old) == 1


def test_product_prefix_suffix_manifests_are_ordered_and_fail_closed() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_product_prefix_suffix_artifact_receipts_are_frozen(
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
        f"PRODUCT PREFIX SUFFIX ARTIFACT row={row_name!r} actual={actual!r}",
        flush=True,
    )
    assert EXPECTED_ARTIFACTS[row_name] is not None, (
        f"freeze deterministic artifact receipt for {row_name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[row_name]


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_product_prefix_suffix_bodies_and_envelopes_are_frozen(
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
        label=f"product prefix/suffix body {row_name}",
    )

    print(
        "PRODUCT PREFIX SUFFIX BODY "
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
def test_product_prefix_suffix_every_direct_dependency_is_live(
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
def test_product_prefix_suffix_false_conclusions_are_rejected(
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
def test_product_prefix_suffix_boundary_mutations_are_rejected(
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
def test_product_prefix_suffix_empty_context_closures_are_frozen(
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
        f"PRODUCT PREFIX SUFFIX CLOSURE row={row_name!r} actual={actual!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(
        type(node) is DNE for node in _walk_proof(certificate)
    )
    for index in range(len(item.dependencies)):
        print(
            "PRODUCT PREFIX SUFFIX DIRECT CUT BEGIN "
            f"row={row_name!r} index={index}",
            flush=True,
        )
        corrupted = _mutate_direct_cut(certificate, index)
        assert not check((), corrupted, formula)
        print(
            "PRODUCT PREFIX SUFFIX DIRECT CUT REJECTED "
            f"row={row_name!r} index={index}",
            flush=True,
        )

    print(
        f"PRODUCT PREFIX SUFFIX RECEIPT CHECK row={row_name!r}",
        flush=True,
    )
    assert EXPECTED_CLOSURES[row_name] is not None, (
        f"freeze empty-context closure receipt for {row_name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[row_name]
