"""Focused strict-HA audit for the balanced Bertrand power seed.

The candidate intentionally collides by name with the established
``pow_two_seed_bundle_from_total`` row.  Its statement is byte-identical, but
its dependencies and proof body are not.  Consequently this test treats it
as an explicit substitution provider and never concatenates the two specs or
merges them through a collision-tolerant theorem table.
"""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256

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
from peano_lab.library.bertrand_integer_envelope_candidate import (
    make_bertrand_integer_envelope_candidate_theorems,
)
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.bertrand_power_seed_balanced_candidate import (
    make_bertrand_power_seed_balanced_candidate_theorems,
)
from peano_lab.library.bertrand_power_total_candidate import (
    make_bertrand_power_total_candidate_theorems,
    power_total_relation,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    _proof_envelope_metrics_bounded,
)
from peano_lab.library.power_algebra_theorems import _power_terms
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


SQUARE_HELPER_NAME = "eight_times_eight_eq_sixty_four"
HELPER_NAME = "eight_times_sixteen_eq_one_twenty_eight"
THEOREM_NAME = "pow_two_seed_bundle_from_total"
EXPECTED_NAMES = (SQUARE_HELPER_NAME, HELPER_NAME, THEOREM_NAME)
EXPECTED_DEPENDENCIES = {
    SQUARE_HELPER_NAME: (),
    HELPER_NAME: ("mul_add", SQUARE_HELPER_NAME),
    THEOREM_NAME: (
        "pow_successor_compose_from_total",
        "pow_two_base_two_value_four",
        "pow_add",
        HELPER_NAME,
    ),
}
EXPECTED_SEED_STATEMENT = (
    8_248,
    "8631f7c13e6e77fa51ae1b98393eadbebd792e592528a10725a38f5405fee5f6",
)

# These receipts remain deliberately fail-closed until each proof is replayed
# in a fresh, serially authorized process.  Candidate-body checking is not an
# admission or Stable-enrollment receipt.
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    SQUARE_HELPER_NAME: (0, 82, 397, 84, 397, 396, 0),
    HELPER_NAME: (2, 77, 408, 74, 408, 407, 0),
    THEOREM_NAME: (4, 61, 770, 41, 705, 769, 65),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    SQUARE_HELPER_NAME: (397, 397, 84, 11_153, 147),
    HELPER_NAME: (408, 408, 74, 17_829, 201),
    THEOREM_NAME: (770, 705, 41, 3_787, 149),
}
EXPECTED_CLOSURES: dict[str, tuple[int, int, int, int, int] | None] = {
    SQUARE_HELPER_NAME: (397, 84, 397, 396, 0),
    HELPER_NAME: (882, 86, 875, 881, 7),
    THEOREM_NAME: (20_248, 90, 3_336, 3_469, 134),
}
HELPER_BOUNDARY_MUTATION_CASES = (
    (
        "eight_square__off_by_one_result",
        SQUARE_HELPER_NAME,
        "8 * 8 = 63",
    ),
    (
        "eight_sixteen__off_by_one_result",
        HELPER_NAME,
        "8 * 16 = 127",
    ),
)


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    """Return support rows with the original colliding seed removed."""

    rows = (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_integer_envelope_candidate_theorems(TheoremSpec),
        *make_bertrand_power_total_candidate_theorems(TheoremSpec),
    )
    return tuple(item for item in rows if item.name != THEOREM_NAME)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_seed_balanced_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    rows = _specs()
    table = {item.name: item for item in rows}
    assert len(table) == len(rows)
    assert tuple(table) == EXPECTED_NAMES
    return table


def _replacement() -> TheoremSpec:
    return _local()[THEOREM_NAME]


def _helper() -> TheoremSpec:
    return _local()[HELPER_NAME]


def _square_helper() -> TheoremSpec:
    return _local()[SQUARE_HELPER_NAME]


@lru_cache(maxsize=1)
def _original() -> TheoremSpec:
    rows = make_bertrand_power_total_candidate_theorems(TheoremSpec)
    return next(item for item in rows if item.name == THEOREM_NAME)


def _core() -> dict[str, TheoremSpec]:
    """Build a collision-free support table, excluding both seed bodies."""

    support = _support_specs()
    support_by_name = {item.name: item for item in support}
    assert len(support_by_name) == len(support)
    assert THEOREM_NAME not in support_by_name

    public = dict(_specs_by_name())
    assert THEOREM_NAME not in public
    assert HELPER_NAME not in public
    assert SQUARE_HELPER_NAME not in public
    collisions = set(public) & set(support_by_name)
    assert all(public[name] == support_by_name[name] for name in collisions)
    return public | {
        name: item
        for name, item in support_by_name.items()
        if name not in public
    }


def _available() -> dict[str, TheoremSpec]:
    core = _core()
    assert THEOREM_NAME not in core
    assert HELPER_NAME not in core
    assert SQUARE_HELPER_NAME not in core
    return core | _local()


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = _available()
    target = _closed_formula(item.statement)
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
        theorem = replay(name)
        return theorem.formula, theorem.certificate

    available = _available()
    item = available[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body

    formula = _closed_formula(item.statement)
    for dependency in reversed(item.dependencies):
        dependency_formula, dependency_proof = _close(dependency)
        body = Cut(dependency_formula, formula, dependency_proof, body)
    return formula, body


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(_proof_children(node))


def _mutate_direct_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_direct_cut(proof.body, index - 1))


def test_balanced_seed_factory_is_exact_substitution_only_surface() -> None:
    item = _replacement()
    helper = _helper()
    square_helper = _square_helper()
    original = _original()
    rebuilt = make_bertrand_power_seed_balanced_candidate_theorems(TheoremSpec)

    assert rebuilt == _specs()
    assert tuple(row.name for row in rebuilt) == EXPECTED_NAMES
    assert tuple(case[0] for case in HELPER_BOUNDARY_MUTATION_CASES) == (
        "eight_square__off_by_one_result",
        "eight_sixteen__off_by_one_result",
    )
    assert len({case[0] for case in HELPER_BOUNDARY_MUTATION_CASES}) == 2
    assert item.name == original.name == THEOREM_NAME
    assert item.statement == original.statement
    assert item != original
    assert {row.name: row.dependencies for row in rebuilt} == (
        EXPECTED_DEPENDENCIES
    )
    assert item.dependencies != original.dependencies
    assert (len(item.statement), sha256(item.statement.encode()).hexdigest()) == (
        EXPECTED_SEED_STATEMENT
    )
    assert helper.statement == "8 * 16 = 128"
    assert square_helper.statement == "8 * 8 = 64"

    # Only statement equality licenses explicit graph substitution.  In
    # particular, concatenating both providers would be a duplicate-name bug.
    assert len({item.name, original.name}) == 1
    assert THEOREM_NAME not in _core()
    assert HELPER_NAME not in _core()
    assert SQUARE_HELPER_NAME not in _core()
    assert _available()[THEOREM_NAME] is item
    assert _available()[HELPER_NAME] is helper
    assert _available()[SQUARE_HELPER_NAME] is square_helper

    for row in rebuilt:
        formula, free_names = parse_formula_with_names(row.statement)
        assert not free_names
        assert formula == _closed_formula(row.statement)
        assert all(
            marker not in row.statement
            for marker in ("PowTotal", "Pow(", "^", "**", "DNE")
        )
        assert all(
            forbidden not in command
            for command in row.script
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


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_balanced_seed_body_and_default_envelope_are_checked_and_frozen(
    row_name: str,
) -> None:
    item = _local()[row_name]
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
        label="balanced seed body",
    )

    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert actual_envelope[2] <= limits.max_body_depth
    assert actual_envelope[4] <= limits.max_body_envelope_depth
    assert not any(type(node) is DNE for node in _walk(body))

    assert EXPECTED_BODIES[row_name] is not None, (
        f"freeze isolated body receipt for {row_name}: {actual_body!r}; "
        f"envelope receipt: {actual_envelope!r}"
    )
    assert EXPECTED_ENVELOPES[row_name] is not None
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
def test_balanced_seed_every_direct_dependency_is_live(
    row_name: str, dependency: str
) -> None:
    item = _local()[row_name]
    shortened = replace(
        item,
        dependencies=tuple(
            name for name in item.dependencies if name != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_available())


@pytest.mark.parametrize(
    "mutated_statement",
    (
        lambda item: f"({item.statement}) /\\ false",
        lambda item: item.statement.replace(
            power_total_relation(tag="seed"), "0 = 0"
        ),
        lambda item: item.statement.replace(
            _power_terms("2", "2", "4", tag="bpt_seed_two"),
            _power_terms("2", "2", "5", tag="bpt_seed_two"),
        ),
        lambda item: item.statement.replace(
            _power_terms("2", "7", "128", tag="bpt_seed_seven"),
            _power_terms("2", "7", "127", tag="bpt_seed_seven"),
        ),
        lambda item: item.statement.replace(
            _power_terms("2", "7", "128", tag="bpt_seed_seven"),
            _power_terms("2", "6", "128", tag="bpt_seed_seven"),
        ),
    ),
    ids=(
        "false-conjunction",
        "delete-totality",
        "wrong-two-square",
        "off-by-one-result",
        "off-by-one-exponent",
    ),
)
def test_balanced_seed_false_and_boundary_contracts_are_rejected(
    mutated_statement,
) -> None:
    item = _replacement()
    statement = mutated_statement(item)
    assert statement != item.statement
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=statement),),
            core=_available(),
        )


@pytest.mark.parametrize(
    "row_name",
    (SQUARE_HELPER_NAME, HELPER_NAME),
    ids=(
        "eight-square-false-target",
        "eight-sixteen-false-target",
    ),
)
def test_balanced_seed_helper_false_targets_are_rejected(row_name: str) -> None:
    item = _local()[row_name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_available())


@pytest.mark.parametrize(
    ("case_id", "row_name", "statement"),
    HELPER_BOUNDARY_MUTATION_CASES,
    ids=tuple(case[0] for case in HELPER_BOUNDARY_MUTATION_CASES),
)
def test_balanced_seed_helper_boundary_mutations_are_rejected(
    case_id: str,
    row_name: str,
    statement: str,
) -> None:
    del case_id
    item = _local()[row_name]
    assert statement != item.statement
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=statement),),
            core=_available(),
        )


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_balanced_seed_empty_context_closure_is_checked_and_frozen(
    row_name: str,
) -> None:
    item = _local()[row_name]
    formula, certificate = _close(row_name)
    assert formula == _closed_formula(item.statement)
    assert check((), certificate, formula)
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    actual = (nodes, depth, objects, edges, reused)

    assert nodes < MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects < MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk(certificate))
    for index in range(len(item.dependencies)):
        assert not check((), _mutate_direct_cut(certificate, index), formula)

    assert EXPECTED_CLOSURES[row_name] is not None, (
        f"freeze isolated closure receipt for {row_name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[row_name]


def test_balanced_seed_standard_natural_semantics_are_regression_only() -> None:
    # Host arithmetic validates orientation only; it produces no certificate.
    assert 2**2 == 4
    assert 2**3 == 8
    assert 2**4 == 16
    assert 3 + 4 == 7
    assert 16 == 8 + 8
    assert 8 * 8 == 64
    assert 64 + 64 == 128
    assert (2**3) * (2**4) == 2**7 == 128
