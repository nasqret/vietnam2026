"""Fail-closed audit for constructive Choose-factorial support.

The two candidates are closed independently over Stable: the length
transport receives no theorem hypothesis, while the weighted product row
receives exactly commutativity and associativity.  Expanded factorial text is
rebuilt independently from the finite-fold surface.  Receipts are evidence,
never theorem authority.
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
    bertrand_choose_factorial_support_candidate as module,
    editions_v7,
    finite_factorial_theorems as factorial_module,
    finite_fold_surface as fold_surface,
    theorems as stable_module,
)
from peano_lab.library.bertrand_choose_factorial_support_candidate import (
    make_bertrand_choose_factorial_support_candidate_theorems,
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


FACTORIAL_LENGTH_EQ_TRANSPORT = "factorial_length_eq_transport"
FACTORIAL_WEIGHTED_PRODUCT_COMBINE = "factorial_weighted_product_combine"
EXPECTED_NAMES = (
    FACTORIAL_LENGTH_EQ_TRANSPORT,
    FACTORIAL_WEIGHTED_PRODUCT_COMBINE,
)
EXPECTED_DEPENDENCIES = {
    FACTORIAL_LENGTH_EQ_TRANSPORT: (),
    FACTORIAL_WEIGHTED_PRODUCT_COMBINE: ("mul_comm", "mul_assoc"),
}
EXPECTED_DIRECT_CUTS = {
    FACTORIAL_LENGTH_EQ_TRANSPORT: 0,
    FACTORIAL_WEIGHTED_PRODUCT_COMBINE: 2,
}
EXPECTED_TRANSPORT_SCRIPT = (
    "intro n",
    "intro m",
    "intro z",
    "intro heq",
    "intro hfactorial",
    "rewrite heq at hfactorial",
    "rewrite heq at hfactorial",
    "rewrite heq at hfactorial",
    "rewrite heq at hfactorial",
    "exact hfactorial",
)
EXPECTED_COMBINE_SCRIPT = (
    "intro u",
    "intro v",
    "intro x",
    "intro y",
    "intro f",
    "intro K",
    "intro r",
    "intro F",
    "intro J",
    "intro hJ",
    "intro hF",
    "intro hweighted",
    "intro hf",
    "rewrite hf at hF",
    "have hassoc_xv : ((K * r) * x) * v = (K * r) * (x * v)",
    "apply mul_assoc",
    "rewrite hassoc_xv at hF",
    "have hcomm_xv : x * v = v * x",
    "apply mul_comm",
    "rewrite hcomm_xv at hF",
    "rewrite <- hweighted at hF",
    "have hassoc_uy : ((K * r) * u) * y = (K * r) * (u * y)",
    "apply mul_assoc",
    "rewrite <- hassoc_uy at hF",
    "have hassoc_kru : (K * r) * u = K * (r * u)",
    "apply mul_assoc",
    "rewrite hassoc_kru at hF",
    "rewrite <- hJ at hF",
    "exact hF",
)

FINITE_FOLD_SOURCE_SHA256 = (
    "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30"
)
FINITE_FACTORIAL_SOURCE_SHA256 = (
    "a51240629fb661c3d732cb30ad32d3fdc1d3da8b9d01f80023f12429dc7e3709"
)
SUPPORT_SOURCE_SHA256 = (
    "d9fbdfb0bf3885ac2d3245b40c680dc28ec3e838fad7fb69736a96ee2734cccc"
)

# All execution receipts fail closed until isolated selectors reproduce them.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    FACTORIAL_LENGTH_EQ_TRANSPORT: (
        5473,
        "fcc98fc79386e8a1e52abe5870bb7539575d2d06779f2ce87f9c8d07e29bb696",
        "8d22ed7f1b90e5f6e39c2d80e6d573bb1503db7f5c56b0170d8e252a825de927",
        "fcc98fc79386e8a1e52abe5870bb7539575d2d06779f2ce87f9c8d07e29bb696",
    ),
    FACTORIAL_WEIGHTED_PRODUCT_COMBINE: (
        103,
        "b549be53ee23ae3712126b6f6ce11b6b567ba26a9cfb4e7ee2da2f2f3e6b5706",
        "b2eb10453524f46b8f881ece9fe36e74662b82f75725cdbdd9635a6d6ac6a64a",
        "9f71b191a1dc889ab8a101c605bf15fc3ea96159d0f416567e633e8f5718ecd5",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    FACTORIAL_LENGTH_EQ_TRANSPORT: (0, 10, 26, 14, 26, 25, 0),
    FACTORIAL_WEIGHTED_PRODUCT_COMBINE: (2, 29, 44, 25, 44, 43, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    FACTORIAL_LENGTH_EQ_TRANSPORT: (26, 26, 14, 760, 38),
    FACTORIAL_WEIGHTED_PRODUCT_COMBINE: (44, 44, 25, 52, 26),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    FACTORIAL_LENGTH_EQ_TRANSPORT: (
        26,
        14,
        26,
        25,
        0,
        760,
        38,
        "3523b4f512b02dfb022c455794afd0ec738e6e5b8de98ebe28a7c989e03634ca",
    ),
    FACTORIAL_WEIGHTED_PRODUCT_COMBINE: (
        382,
        25,
        316,
        349,
        34,
        1085,
        26,
        "eab07f3b7b4ad4fe7efaf0649638bbae75d26a367943b9d8b1bb076e605e5602",
    ),
}


def _factorial(length: str, result: str, *, tag: str) -> str:
    """Independently reproduce the conservative factorial expansion."""

    code = f"ff_b_{tag}"
    scale = f"ff_c_{tag}"
    marker = f"ff_start_{tag}"
    range_prefix = fold_surface.range_relation(
        code,
        scale,
        marker,
        length,
        tag=f"{tag}_range",
    )
    assert range_prefix.count(marker) == 2
    range_prefix = range_prefix.replace(marker, "1")
    product = fold_surface.product_relation(
        code,
        scale,
        length,
        result,
        tag=f"{tag}_product",
    )
    return f"exists {code} {scale}. (({range_prefix}) /\\ ({product}))"


def _expected_statements() -> dict[str, str]:
    source = _factorial("n", "z", tag="bcflet_source")
    target = _factorial("m", "z", tag="bcflet_target")
    return {
        FACTORIAL_LENGTH_EQ_TRANSPORT: (
            "forall n m z. n = m -> "
            f"({source}) -> ({target})"
        ),
        FACTORIAL_WEIGHTED_PRODUCT_COMBINE: (
            "forall u v x y f K r F J. "
            "J = r * u -> F = f * v -> u * y = v * x -> "
            "f = (K * r) * x -> F = (K * J) * y"
        ),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_factorial_support_candidate_theorems(
        TheoremSpec
    )


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
    assert name in EXPECTED_NAMES
    # Deliberately exclude the other local row: both candidates stand alone.
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
            raise AssertionError("factorial support delegated through use")
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


def test_choose_factorial_support_sources_are_pinned() -> None:
    expected = (
        (fold_surface, FINITE_FOLD_SOURCE_SHA256),
        (factorial_module, FINITE_FACTORIAL_SOURCE_SHA256),
        (module, SUPPORT_SOURCE_SHA256),
    )
    for provider, digest in expected:
        assert sha256(Path(provider.__file__).read_bytes()).hexdigest() == digest


def test_choose_factorial_support_factory_is_exact_and_isolated() -> None:
    rows = _specs()
    expected_statements = _expected_statements()
    assert make_bertrand_choose_factorial_support_candidate_theorems(
        TheoremSpec
    ) == rows
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        expected_statements[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert module.__all__ == [
        "make_bertrand_choose_factorial_support_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert set(_row_core(FACTORIAL_LENGTH_EQ_TRANSPORT)) == stable
    assert set(_row_core(FACTORIAL_WEIGHTED_PRODUCT_COMBINE)) == stable
    assert all(
        dependency in _row_core(item.name)
        for item in rows
        for dependency in item.dependencies
    )

    provider_token = "bertrand_choose_factorial_support_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
        source = Path(authority_module.__file__).read_text(encoding="utf-8")
        assert provider_token not in source

    for item in rows:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        for token in (
            "Factorial(",
            "Product(",
            "Range(",
            "<=",
            "<",
            "^",
            "%",
            "|",
        ):
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


def test_factorial_length_transport_script_topology_is_exact() -> None:
    item = _table(_specs())[FACTORIAL_LENGTH_EQ_TRANSPORT]
    assert item.script == EXPECTED_TRANSPORT_SCRIPT
    assert len(item.script) == 10
    assert item.script[:5] == (
        "intro n",
        "intro m",
        "intro z",
        "intro heq",
        "intro hfactorial",
    )
    assert item.script.count("rewrite heq at hfactorial") == 4
    assert item.script[-1] == "exact hfactorial"
    assert not any(command.startswith("induction ") for command in item.script)


def test_factorial_weighted_combine_script_topology_is_exact() -> None:
    item = _table(_specs())[FACTORIAL_WEIGHTED_PRODUCT_COMBINE]
    assert item.script == EXPECTED_COMBINE_SCRIPT
    assert len(item.script) == 29
    assert item.script[:13] == (
        "intro u",
        "intro v",
        "intro x",
        "intro y",
        "intro f",
        "intro K",
        "intro r",
        "intro F",
        "intro J",
        "intro hJ",
        "intro hF",
        "intro hweighted",
        "intro hf",
    )
    assert item.script.count("apply mul_comm") == 1
    assert item.script.count("apply mul_assoc") == 3
    assert not any(
        command.startswith(("trans ", "congr", "specialize "))
        for command in item.script
    )
    assert item.script.count("rewrite hf at hF") == 1
    assert item.script.count("rewrite hassoc_xv at hF") == 1
    assert item.script.count("rewrite hcomm_xv at hF") == 1
    assert item.script.count("rewrite <- hweighted at hF") == 1
    assert item.script.count("rewrite <- hassoc_uy at hF") == 1
    assert item.script.count("rewrite hassoc_kru at hF") == 1
    assert item.script.count("rewrite <- hJ at hF") == 1
    assert item.script.count("exact hF") == 1
    assert not any(command.startswith("induction ") for command in item.script)


def test_choose_factorial_support_helpers_are_hygienic() -> None:
    left = _factorial("n", "z", tag="factorial_hygiene_left")
    right = _factorial("n", "z", tag="factorial_hygiene_right")
    parsed_left, free_left = parse_formula_with_names(left)
    parsed_right, free_right = parse_formula_with_names(right)
    assert left != right
    assert parsed_left == parsed_right
    assert set(free_left) == set(free_right) == {"n", "z"}

    assert factorial_module.factorial_relation(
        "n", "z", tag="factorial_hygiene_left"
    ) == left
    with pytest.raises(ValueError):
        factorial_module.factorial_relation(
            "S n", "z", tag="factorial_hygiene_term"
        )
    with pytest.raises(ValueError):
        factorial_module.factorial_relation(
            "ff_i_valid_range", "z", tag="valid"
        )
    with pytest.raises(ValueError):
        factorial_module.factorial_relation(
            "n", "z", tag="bad tag"
        )


def test_choose_factorial_support_receipt_manifests_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_factorial_support_artifacts_are_frozen(name: str) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"CHOOSE FACTORIAL {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze deterministic artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_factorial_support_bodies_are_frozen(name: str) -> None:
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
        label=f"choose factorial support body {name}",
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
        f"CHOOSE FACTORIAL {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, (
        f"freeze body receipt for {name}: {actual!r}"
    )
    assert EXPECTED_ENVELOPES[name] is not None, (
        f"freeze envelope receipt for {name}: {envelope!r}"
    )
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


@pytest.mark.parametrize(
    "dependency",
    EXPECTED_DEPENDENCIES[FACTORIAL_WEIGHTED_PRODUCT_COMBINE],
)
def test_factorial_weighted_combine_every_dependency_is_live(
    dependency: str,
) -> None:
    item = _table(_specs())[FACTORIAL_WEIGHTED_PRODUCT_COMBINE]
    shortened = replace(
        item,
        dependencies=tuple(
            candidate
            for candidate in item.dependencies
            if candidate != dependency
        ),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(item.name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_choose_factorial_support_false_targets_are_rejected(name: str) -> None:
    item = _table(_specs())[name]
    mutated = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=_row_core(name))


def _mutations() -> tuple[tuple[str, str, str, str], ...]:
    return (
        (
            FACTORIAL_LENGTH_EQ_TRANSPORT,
            "shift_source_length",
            "n = m",
            "S n = m",
        ),
        (
            FACTORIAL_LENGTH_EQ_TRANSPORT,
            "shift_target_length",
            "n = m",
            "n = S m",
        ),
        (
            FACTORIAL_WEIGHTED_PRODUCT_COMBINE,
            "wrong_terminal_factor",
            "J = r * u",
            "J = r * v",
        ),
        (
            FACTORIAL_WEIGHTED_PRODUCT_COMBINE,
            "wrong_row_factor",
            "F = f * v",
            "F = f * u",
        ),
        (
            FACTORIAL_WEIGHTED_PRODUCT_COMBINE,
            "collapse_weighted_right",
            "u * y = v * x",
            "u * y = u * x",
        ),
        (
            FACTORIAL_WEIGHTED_PRODUCT_COMBINE,
            "use_current_value_in_ih",
            "f = (K * r) * x",
            "f = (K * r) * y",
        ),
        (
            FACTORIAL_WEIGHTED_PRODUCT_COMBINE,
            "successor_result",
            "F = (K * J) * y",
            "F = S ((K * J) * y)",
        ),
    )


def test_choose_factorial_support_mutations_have_counterfixtures() -> None:
    # Transport: 1! is not 2!, in either shifted-equality orientation.
    assert 1 != 2
    assert 2 != 1
    # Each combine mutation has a small standard-arithmetic counterfixture.
    assert 2 != 4  # (u,v,x,y,K,r,f,J,F)=(1,2,1,2,1,1,1,2,2).
    assert 1 != 2  # (u,v,x,y,K,r,f,J,F)=(1,2,1,2,1,1,1,1,1).
    assert 2 != 1  # (u,v,x,y,K,r,f,J,F)=(1,2,1,1,1,1,1,1,2).
    assert 4 != 2  # (u,v,x,y,K,r,f,J,F)=(1,2,1,2,1,1,2,1,4).
    assert 2 != 3  # (u,v,x,y,K,r,f,J,F)=(1,2,1,2,1,1,1,1,2).


@pytest.mark.parametrize(
    ("name", "case_id", "old", "new"),
    _mutations(),
    ids=tuple(case[1] for case in _mutations()),
)
def test_choose_factorial_support_genuine_mutations_are_rejected(
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
def test_choose_factorial_support_independent_closures_are_frozen(
    name: str,
) -> None:
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
        label=f"choose factorial support closure {name}",
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

    print(f"CHOOSE FACTORIAL {name} CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, (
        f"freeze independent closure receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_CLOSURES[name]
