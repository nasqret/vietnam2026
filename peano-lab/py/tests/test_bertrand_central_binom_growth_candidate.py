"""Fail-closed audit for strict central-binomial growth arithmetic.

Both candidates are rebuilt over Stable only.  The successor-step row sees
the strict-scaling row solely through its exact local prefix.  Expanded order
relations are reproduced independently, and receipts are evidence rather
than theorem authority.
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
    bertrand_central_binom_growth_candidate as module,
    editions_v7,
    theorems as stable_module,
)
from peano_lab.library.bertrand_central_binom_growth_candidate import (
    make_bertrand_central_binom_growth_candidate_theorems,
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


MUL_LT_MUL_RIGHT_NONZERO = "mul_lt_mul_right_nonzero"
FOUR_POWER_CENTRAL_RECURRENCE_STEP = (
    "four_power_central_recurrence_step"
)
EXPECTED_NAMES = (
    MUL_LT_MUL_RIGHT_NONZERO,
    FOUR_POWER_CENTRAL_RECURRENCE_STEP,
)
EXPECTED_DEPENDENCIES = {
    MUL_LT_MUL_RIGHT_NONZERO: (
        "mul_comm",
        "mul_lt_mul_succ_left_nonzero",
        "mul_le_mul_right",
        "lt_of_lt_of_le",
    ),
    FOUR_POWER_CENTRAL_RECURRENCE_STEP: (
        "add_eq_zero_right",
        "add_comm",
        "mul_comm",
        "mul_assoc",
        "mul_add",
        "add_mul",
        MUL_LT_MUL_RIGHT_NONZERO,
        "lt_trans",
    ),
}
EXPECTED_DIRECT_CUTS = {
    MUL_LT_MUL_RIGHT_NONZERO: 4,
    FOUR_POWER_CENTRAL_RECURRENCE_STEP: 8,
}
GROWTH_SOURCE_SHA256 = (
    "de43bd809ebd10cc31fc2ebcc12df10328e3571f491446545e34585b5a6fb66b"
)

# Execution receipts fail closed until isolated selectors reproduce them.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    MUL_LT_MUL_RIGHT_NONZERO: (
        176,
        "b45605933aa2a918c1b19cc05a142c55de1314cbed7123567263ad153f8e83f6",
        "5eb8108835e83aa086d8cb3b71cf04694a96fa743fbc14ff10fd81e27adbab60",
        "53e683e2bfe6b82ad51a1ea9b657bb97e62c8fb1df3634d66f19bb43914064ca",
    ),
    FOUR_POWER_CENTRAL_RECURRENCE_STEP: (
        209,
        "51c3f1ceebf88a2f0f4a37a2183b4fea85b699c46faddfcfc19f09883b468349",
        "a25517233bc82c4b28ac12a29ef4cfaed63482dccf0ec18e05d66957fb6a443a",
        "987cef79a5800fe73f547c1bb26fdf04558a9445cd7b23fdb6ff16d9ba867eb1",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    MUL_LT_MUL_RIGHT_NONZERO: (4, 34, 34, 17, 34, 33, 0),
    FOUR_POWER_CENTRAL_RECURRENCE_STEP: (8, 75, 131, 37, 131, 130, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    MUL_LT_MUL_RIGHT_NONZERO: (34, 34, 17, 40, 18),
    FOUR_POWER_CENTRAL_RECURRENCE_STEP: (131, 131, 37, 177, 39),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    MUL_LT_MUL_RIGHT_NONZERO: (
        783,
        29,
        392,
        425,
        34,
        2151,
        30,
        "ee26db77d8b201396589b30497ca7ee9d229e971665fd9bc3b5273a3e8e55c41",
    ),
    FOUR_POWER_CENTRAL_RECURRENCE_STEP: (
        1836,
        37,
        605,
        650,
        46,
        5310,
        39,
        "93fa73736a28fd6b33178915a93d70f8f866b6cdb8a1d61ed82969ecf5b9c13c",
    ),
}


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _binder(tag: str, variables: tuple[str, ...], stem: str) -> str:
    safe_tag = _identifier(tag, "binder tag")
    name = f"bcf_{stem}_{safe_tag}"
    if name in variables:
        raise ValueError("generated order binder captures an argument")
    return name


def _lt(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    gap = _binder(tag, variables, "lt_gap")
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _le(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    gap = _binder(tag, variables, "le_gap")
    return f"exists {gap}. {gap} + ({left}) = {right}"


def _relations() -> dict[str, str]:
    scaling_variables = ("a", "b", "c")
    step_variables = ("n", "q", "c", "d")
    return {
        "scaling_source": _lt(
            "a", "b", tag="mlmrn_source", variables=scaling_variables
        ),
        "scaling_raw_step": _lt(
            "c * a",
            "c * S a",
            tag="mlmrn_raw_step",
            variables=scaling_variables,
        ),
        "scaling_step": _lt(
            "a * c",
            "S a * c",
            tag="mlmrn_step",
            variables=scaling_variables,
        ),
        "scaling_tail": _le(
            "S a * c",
            "b * c",
            tag="mlmrn_tail",
            variables=scaling_variables,
        ),
        "scaling_result": _lt(
            "a * c",
            "b * c",
            tag="mlmrn_result",
            variables=scaling_variables,
        ),
        "step_source": _lt(
            "q", "n * c", tag="bfpcrs_source", variables=step_variables
        ),
        "step_scaled": _lt(
            "q * 4",
            "(n * c) * 4",
            tag="bfpcrs_scaled",
            variables=step_variables,
        ),
        "step_coefficient": _lt(
            "4 * n",
            "2 * S (n + n)",
            tag="bfpcrs_coefficient",
            variables=step_variables,
        ),
        "step_coefficient_product": _lt(
            "(4 * n) * c",
            "(2 * S (n + n)) * c",
            tag="bfpcrs_coefficient_product",
            variables=step_variables,
        ),
        "step_gap": _lt(
            "(n * c) * 4",
            "S n * d",
            tag="bfpcrs_gap",
            variables=step_variables,
        ),
        "step_result": _lt(
            "q * 4",
            "S n * d",
            tag="bfpcrs_result",
            variables=step_variables,
        ),
    }


def _expected_statements() -> dict[str, str]:
    relation = _relations()
    return {
        MUL_LT_MUL_RIGHT_NONZERO: (
            "forall a b c. "
            f"({relation['scaling_source']}) -> ~(c = 0) -> "
            f"({relation['scaling_result']})"
        ),
        FOUR_POWER_CENTRAL_RECURRENCE_STEP: (
            "forall n q c d. "
            f"({relation['step_source']}) -> "
            "S n * d = (2 * S (n + n)) * c -> "
            f"({relation['step_result']})"
        ),
    }


def _expected_scripts() -> dict[str, tuple[str, ...]]:
    relation = _relations()
    return {
        MUL_LT_MUL_RIGHT_NONZERO: (
            "intro a",
            "intro b",
            "intro c",
            "intro hab",
            "intro hc",
            f"have hraw : {relation['scaling_raw_step']}",
            "specialize mul_lt_mul_succ_left_nonzero c",
            "specialize mul_lt_mul_succ_left_nonzero a",
            "apply mul_lt_mul_succ_left_nonzero",
            "exact hc",
            "have hleft_comm : c * a = a * c",
            "specialize mul_comm c",
            "specialize mul_comm a",
            "exact mul_comm",
            "have hright_comm : c * S a = S a * c",
            "specialize mul_comm c",
            "specialize mul_comm (S a)",
            "exact mul_comm",
            "rewrite hleft_comm at hraw",
            "rewrite hright_comm at hraw",
            f"have hstep : {relation['scaling_step']}",
            "exact hraw",
            f"have htail : {relation['scaling_tail']}",
            "specialize mul_le_mul_right (S a)",
            "specialize mul_le_mul_right b",
            "specialize mul_le_mul_right c",
            "apply mul_le_mul_right",
            "exact hab",
            "specialize lt_of_lt_of_le (a * c)",
            "specialize lt_of_lt_of_le (S a * c)",
            "specialize lt_of_lt_of_le (b * c)",
            "apply lt_of_lt_of_le",
            "exact hstep",
            "exact htail",
        ),
        FOUR_POWER_CENTRAL_RECURRENCE_STEP: (
            "intro n",
            "intro q",
            "intro c",
            "intro d",
            "intro hstrict",
            "intro hrecurrence",
            "have hc : ~(c = 0)",
            "intro hc_zero",
            "cases hstrict",
            "apply PA1",
            "specialize add_eq_zero_right x",
            "specialize add_eq_zero_right (S q)",
            "apply add_eq_zero_right",
            "trans n * c",
            "exact hstrict_witness",
            "rewrite hc_zero",
            "apply PA5",
            f"have hscaled : {relation['step_scaled']}",
            "specialize mul_lt_mul_right_nonzero q",
            "specialize mul_lt_mul_right_nonzero (n * c)",
            "specialize mul_lt_mul_right_nonzero 4",
            "apply mul_lt_mul_right_nonzero",
            "exact hstrict",
            "intro hfour_zero",
            "apply PA1",
            "exact hfour_zero",
            "have hfour : 4 * n = 2 * n + 2 * n",
            "trans (2 + 2) * n",
            "congr",
            "norm_num",
            "refl",
            "apply add_mul",
            f"have hcoefficient : {relation['step_coefficient']}",
            "exists 1",
            "trans S (1 + 4 * n)",
            "apply PA4",
            "trans S (4 * n + 1)",
            "congr",
            "apply add_comm",
            "trans 4 * n + 2",
            "symm",
            "apply PA4",
            "trans (2 * n + 2 * n) + 2",
            "congr",
            "exact hfour",
            "refl",
            "trans 2 * (n + n) + 2",
            "congr",
            "symm",
            "apply mul_add",
            "refl",
            "symm",
            "apply PA6",
            f"have hcoefficient_product : "
            f"{relation['step_coefficient_product']}",
            "specialize mul_lt_mul_right_nonzero (4 * n)",
            "specialize mul_lt_mul_right_nonzero (2 * S (n + n))",
            "specialize mul_lt_mul_right_nonzero c",
            "apply mul_lt_mul_right_nonzero",
            "exact hcoefficient",
            "exact hc",
            "have hshuffle : (n * c) * 4 = (4 * n) * c",
            "trans 4 * (n * c)",
            "apply mul_comm",
            "symm",
            "apply mul_assoc",
            f"have hgap : {relation['step_gap']}",
            "rewrite hshuffle",
            "rewrite hrecurrence",
            "exact hcoefficient_product",
            "specialize lt_trans (q * 4)",
            "specialize lt_trans ((n * c) * 4)",
            "specialize lt_trans (S n * d)",
            "apply lt_trans",
            "exact hscaled",
            "exact hgap",
        ),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_central_binom_growth_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    public = dict(_specs_by_name())
    assert not (set(EXPECTED_NAMES) & set(public))
    return public


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
            raise AssertionError("growth arithmetic delegated through use")
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
    dependencies = tuple(_close(name) for name in item.dependencies)
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


def test_growth_source_is_pinned() -> None:
    assert sha256(Path(module.__file__).read_bytes()).hexdigest() == (
        GROWTH_SOURCE_SHA256
    )


def test_growth_factory_is_exact_prefix_only_and_isolated() -> None:
    rows = _specs()
    statements = _expected_statements()
    scripts = _expected_scripts()
    assert make_bertrand_central_binom_growth_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        statements[name] for name in EXPECTED_NAMES
    )
    assert tuple(item.script for item in rows) == tuple(
        scripts[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_central_binom_growth_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert set(_row_core(MUL_LT_MUL_RIGHT_NONZERO)) == stable
    assert set(_row_core(FOUR_POWER_CENTRAL_RECURRENCE_STEP)) == (
        stable | {MUL_LT_MUL_RIGHT_NONZERO}
    )
    for item in rows:
        assert all(
            dependency in _row_core(item.name)
            for dependency in item.dependencies
        )
    assert _row_core(FOUR_POWER_CENTRAL_RECURRENCE_STEP)[
        MUL_LT_MUL_RIGHT_NONZERO
    ] is rows[0]

    provider_token = "bertrand_central_binom_growth_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    for item in rows:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        for token in ("Lt(", "Le(", "<=", "<", "^", "%", "|"):
            assert token not in item.statement
        for command in item.script:
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


def test_growth_relation_helpers_are_hygienic() -> None:
    variables = ("a", "b", "c")
    left = _lt("a", "b", tag="hygiene_left", variables=variables)
    right = _lt("a", "b", tag="hygiene_right", variables=variables)
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"a", "b"}
    assert module._lt_term(
        "a", "b", tag="hygiene_left", variables=variables
    ) == left
    with pytest.raises(ValueError):
        module._lt_term(
            "a",
            "b",
            tag="valid",
            variables=("a", "b", "bcf_lt_gap_valid"),
        )
    with pytest.raises(ValueError):
        module._lt_term("a", "b", tag="bad tag", variables=variables)


def test_growth_script_topology_is_exact() -> None:
    rows = _table(_specs())
    scaling = rows[MUL_LT_MUL_RIGHT_NONZERO]
    step = rows[FOUR_POWER_CENTRAL_RECURRENCE_STEP]
    assert scaling.script == _expected_scripts()[MUL_LT_MUL_RIGHT_NONZERO]
    assert step.script == _expected_scripts()[
        FOUR_POWER_CENTRAL_RECURRENCE_STEP
    ]
    assert len(scaling.script) == 34
    assert len(step.script) == 75
    assert scaling.script.count("apply mul_lt_mul_succ_left_nonzero") == 1
    assert scaling.script.count("apply mul_le_mul_right") == 1
    assert scaling.script.count("apply lt_of_lt_of_le") == 1
    assert step.script.count("apply mul_lt_mul_right_nonzero") == 2
    assert step.script.count("apply lt_trans") == 1
    assert not any(command.startswith("induction ") for command in step.script)


def test_growth_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert sum(len(value) for value in EXPECTED_DEPENDENCIES.values()) == 12


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_growth_artifact_receipts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CENTRAL GROWTH ARTIFACT {name} actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_growth_bodies_and_envelopes_are_frozen(name: str) -> None:
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
        label=f"central growth body {name}",
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
        f"CENTRAL GROWTH BODY {name} actual={actual!r} "
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
def test_growth_every_direct_dependency_is_live(
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
def test_growth_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    relation = _relations()
    scaling_variables = ("a", "b", "c")
    step_variables = ("n", "q", "c", "d")
    return (
        (
            MUL_LT_MUL_RIGHT_NONZERO,
            "weak_source_order",
            relation["scaling_source"],
            _le("a", "b", tag="mlmrn_source", variables=scaling_variables),
        ),
        (
            MUL_LT_MUL_RIGHT_NONZERO,
            "drop_nonzero_factor",
            "~(c = 0)",
            "c = c",
        ),
        (
            MUL_LT_MUL_RIGHT_NONZERO,
            "successor_left_product",
            relation["scaling_result"],
            _lt(
                "S a * c",
                "b * c",
                tag="mlmrn_result",
                variables=scaling_variables,
            ),
        ),
        (
            MUL_LT_MUL_RIGHT_NONZERO,
            "collapse_result_interval",
            relation["scaling_result"],
            _lt(
                "a * c",
                "a * c",
                tag="mlmrn_result",
                variables=scaling_variables,
            ),
        ),
        (
            FOUR_POWER_CENTRAL_RECURRENCE_STEP,
            "weak_source_order",
            relation["step_source"],
            _le(
                "q",
                "n * c",
                tag="bfpcrs_source",
                variables=step_variables,
            ),
        ),
        (
            FOUR_POWER_CENTRAL_RECURRENCE_STEP,
            "tautological_recurrence",
            "S n * d = (2 * S (n + n)) * c",
            "S n * d = S n * d",
        ),
        (
            FOUR_POWER_CENTRAL_RECURRENCE_STEP,
            "halve_recurrence_coefficient",
            "S n * d = (2 * S (n + n)) * c",
            "S n * d = (1 * S (n + n)) * c",
        ),
        (
            FOUR_POWER_CENTRAL_RECURRENCE_STEP,
            "fivefold_power_step",
            relation["step_result"],
            _lt(
                "q * 5",
                "S n * d",
                tag="bfpcrs_result",
                variables=step_variables,
            ),
        ),
        (
            FOUR_POWER_CENTRAL_RECURRENCE_STEP,
            "predecessor_target",
            relation["step_result"],
            _lt(
                "q * 4",
                "n * d",
                tag="bfpcrs_result",
                variables=step_variables,
            ),
        ),
    )


def test_growth_mutations_have_standard_counterfixtures() -> None:
    assert 1 <= 1 and not (1 < 1)
    assert 0 < 1 and 0 == 0 and not (0 < 0)
    assert 1 < 2 and not (2 < 2)
    assert 1 < 2 and not (1 < 1)

    assert 0 <= 0 and 1 * 0 == (2 * 1) * 0 and not (0 < 0)
    assert 0 < 1 and 1 * 0 == 1 * 0 and not (0 < 0)
    assert 5 < 2 * 3 and 3 * 5 == (1 * 5) * 3 and not (20 < 15)
    assert 59 < 3 * 20 and 4 * 70 == (2 * 7) * 20
    assert not (59 * 5 < 4 * 70)
    assert 11 < 2 * 6 and 3 * 20 == (2 * 5) * 6
    assert not (11 * 4 < 2 * 20)


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_growth_genuine_mutations_are_rejected(
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
def test_growth_empty_context_closures_are_frozen(name: str) -> None:
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
        label=f"central growth closure {name}",
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

    print(f"CENTRAL GROWTH CLOSURE {name} actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze empty-context closure receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
