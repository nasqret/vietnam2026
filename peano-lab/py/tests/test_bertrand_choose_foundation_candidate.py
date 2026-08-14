"""Fail-closed audit for the recurrence-first Choose foundation.

The seven candidates stay outside Stable and Alpha authority.  Cheap gates
freeze their expanded raw-PA surfaces and topology; isolated gates check every
dependency-curried body and its bounded proof envelope.  A single root-pruned
LayeredReplay closure then shares the reachable Stable leaves and candidate
bodies before the unchanged kernel checks ``choose_exists`` in empty context.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
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
    bertrand_choose_foundation_candidate as module,
    editions_v7,
    theorems as stable_module,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    make_bertrand_choose_foundation_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayNode,
    _proof_envelope_metrics_bounded,
    compile_layered_replay,
    intern_layered_replay_bodies,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


ZERO_EXTEND = "beta_pascal_zero_row_extend"
ZERO_EXISTS = "beta_pascal_zero_row_exists"
STEP_EXTEND = "beta_pascal_row_step_extend"
STEP_EXISTS = "beta_pascal_row_step_exists"
TABLE_EXTEND = "beta_pascal_table_prefix_extend"
TABLE_EXISTS = "beta_pascal_table_prefix_exists"
CHOOSE_EXISTS = "choose_exists"

EXPECTED_NAMES = (
    ZERO_EXTEND,
    ZERO_EXISTS,
    STEP_EXTEND,
    STEP_EXISTS,
    TABLE_EXTEND,
    TABLE_EXISTS,
    CHOOSE_EXISTS,
)

EXPECTED_DEPENDENCIES = {
    ZERO_EXTEND: (
        "zero_or_succ",
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    ZERO_EXISTS: (
        "add_eq_zero_right",
        "succ_ne_zero",
        ZERO_EXTEND,
    ),
    STEP_EXTEND: (
        "zero_or_succ",
        "beta_at_exists",
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    STEP_EXISTS: (
        "add_eq_zero_right",
        "succ_ne_zero",
        STEP_EXTEND,
    ),
    TABLE_EXTEND: (
        "zero_or_succ",
        "le_refl",
        "lt_to_le",
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
        ZERO_EXISTS,
        STEP_EXISTS,
    ),
    TABLE_EXISTS: (
        "add_eq_zero_right",
        "succ_ne_zero",
        TABLE_EXTEND,
    ),
    CHOOSE_EXISTS: (
        "le_or_lt",
        "beta_at_exists",
        TABLE_EXISTS,
    ),
}

# Populated only after the corresponding isolated kernel check succeeds.
# These are fail-closed receipts, never logical authority or enrollment data.
EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    ZERO_EXTEND: (
        1311,
        "231dcf5179943bc707143267015d2b63fc6e055e4926a2b47ef567b3ec564724",
        "f0890ab8f35d469fc0107d82c845e80f8bcc2303c5d9bf18525b95c2a1e73476",
        "68bd0fabd0a2333c09e2f4e94feaf3cd9643490eec450de59e83d5011aa1a742",
    ),
    ZERO_EXISTS: (
        670,
        "7be0275ff8aba433425ea9529cc489e6fb8760e366d363b7999f28aff851bcac",
        "ad5b35d91fc61109753dab1ea0e84359a0a474c08ef0d6889be03b73e7df7146",
        "d6996c81e5540613606600cca0b40e5c98ed08c2aff808404ca57bdf6b76bde5",
    ),
    STEP_EXTEND: (
        2853,
        "4bd2c7afc0fe4912ecaba819855f606b9ac9dbe916cec6cc324a6439db6ccc51",
        "3ba2cc15687538ced3c909dafec43551fcc994b3f02973be3a5bfaba5a1f4c9c",
        "e5a4f2cfc2760e418f5ad48ef22e2e1da46e95e1e22ef777ea2c7cacbf0d0113",
    ),
    STEP_EXISTS: (
        1454,
        "cf5a4e850818c2f2cdb3fb1ecdbf1fe4527249b6f9ae9a3edfbcc1632d063bdd",
        "c69189bddd3e855455605ddee4d96589273269484564e12146ffefdd38cc513c",
        "88f6c65c4b1bd806d765405931c3228f2df62ac13f9238f0ff636be2e5e6cc02",
    ),
    TABLE_EXTEND: (
        9596,
        "4353a9d0cfb133af410f28440f768181282193c4768f34702b1c033a1230e17c",
        "d3d6cef9b8ec7f9aeacf9bf0f82db2b0fc214b13bdffeb3ddeb55d53bab18593",
        "d02d3b2b44d05b0fc9c5669931d1d84b7a90f4dda1f18eabe3096e36fd6fcf22",
    ),
    TABLE_EXISTS: (
        4861,
        "ead7361afcf431eff725a21c58b970b33cb4cc48ccf8bc390de6a3f33b1635cc",
        "30a61715ab5125cbedddd1d7a11ba284e416774839afe7a3f66614a3a48a27db",
        "92c10355c78856d254864231cb85b3780bfeb5318d9ec2c5da3682e76026a8fd",
    ),
    CHOOSE_EXISTS: (
        7070,
        "32f3234542b243ec448f2cb8bcfaa873c9531ac8afde9440698348df23b71fde",
        "c6284b552db54f04faf89a05dda9ea70e83d297a3d5d8e17750a79c32bf5d7e2",
        "1588a5bd6c1b7fcd1c25daab558777c1f3c0b3f5c12c403b372f5e508153b82d",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    ZERO_EXTEND: (3, 92, 117, 25, 117, 116, 0),
    ZERO_EXISTS: (3, 26, 31, 15, 31, 30, 0),
    STEP_EXTEND: (4, 112, 136, 31, 136, 135, 0),
    STEP_EXISTS: (3, 30, 35, 17, 35, 34, 0),
    TABLE_EXTEND: (7, 261, 362, 55, 362, 361, 0),
    TABLE_EXISTS: (3, 34, 41, 19, 41, 40, 0),
    CHOOSE_EXISTS: (3, 53, 56, 26, 56, 55, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    ZERO_EXTEND: (117, 117, 25, 133, 29),
    ZERO_EXISTS: (31, 31, 15, 64, 19),
    STEP_EXTEND: (136, 136, 31, 156, 34),
    STEP_EXISTS: (35, 35, 17, 122, 29),
    TABLE_EXTEND: (362, 362, 55, 324, 55),
    TABLE_EXISTS: (41, 41, 19, 304, 43),
    CHOOSE_EXISTS: (56, 56, 26, 24, 26),
}
EXPECTED_LAYERED_CLOSURE: dict[str, object] | None = {
    "topology_sha256": (
        "c6c759695cefc14ed1bb72c7f27b8fb853a1344834e292da3f59507369d5ef66"
    ),
    "node_count": 16,
    "stable_atomic_count": 9,
    "candidate_body_count": 7,
    "dependency_edge_count": 26,
    "layer_sizes": (9, 2, 2, 1, 1, 1),
    "proof_nodes": 30726,
    "proof_depth": 84,
    "proof_objects": 3531,
    "proof_edges": 4836,
    "reused_objects": 1306,
    "annotation_occurrences": 100996,
    "envelope_depth": 84,
    "package_formula_occurrences": 1995,
    "package_formula_depth": 46,
    "proof_dag_sha256": (
        "09fbea9ef49964e7301164d28650f607c9e6e95d58cafca6e797297cb07c2330"
    ),
    "kernel_accepted": True,
}


def _zero_row(
    code: str,
    scale: str,
    width: str,
    *,
    tag: str,
) -> str:
    return module._pascal_zero_row(code, scale, width, tag=tag)


def _row_step(
    previous_code: str,
    previous_scale: str,
    code: str,
    scale: str,
    width: str,
    *,
    tag: str,
) -> str:
    return module._pascal_row_step(
        previous_code,
        previous_scale,
        code,
        scale,
        width,
        tag=tag,
    )


def _table_prefix(
    row_code_code: str,
    row_code_scale: str,
    row_scale_code: str,
    row_scale_scale: str,
    width: str,
    rows: str,
    *,
    tag: str,
) -> str:
    return module._pascal_table_prefix(
        row_code_code,
        row_code_scale,
        row_scale_code,
        row_scale_scale,
        width,
        rows,
        tag=tag,
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_choose_foundation_candidate_theorems(TheoremSpec)


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


def _expected_statements() -> dict[str, str]:
    zero_before = _zero_row("b", "c", "w", tag="bpzre_before")
    zero_after = module._pascal_zero_row_term(
        "d",
        "e",
        "S (w)",
        tag="bpzre_after",
        variables=("b", "c", "w", "d", "e"),
    )
    step_before = _row_step(
        "pb", "pc", "b", "c", "w", tag="bpsre_before"
    )
    step_after = module._pascal_row_step_term(
        "pb",
        "pc",
        "d",
        "e",
        "S (w)",
        tag="bpsre_after",
        variables=("pb", "pc", "b", "c", "w", "d", "e"),
    )
    table_before = _table_prefix(
        "bb", "bc", "sb", "sc", "w", "r", tag="bptpe_before"
    )
    table_after = module._pascal_table_prefix_term(
        "db",
        "dc",
        "eb",
        "ec",
        "w",
        "S (r)",
        tag="bptpe_after",
        variables=(
            "bb",
            "bc",
            "sb",
            "sc",
            "w",
            "r",
            "db",
            "dc",
            "eb",
            "ec",
        ),
    )
    return {
        ZERO_EXTEND: (
            "forall b c w. "
            f"({zero_before}) -> exists d e. ({zero_after})"
        ),
        ZERO_EXISTS: (
            "forall w. exists b c. "
            f"({_zero_row('b', 'c', 'w', tag='bpzrx_result')})"
        ),
        STEP_EXTEND: (
            "forall pb pc b c w. "
            f"({step_before}) -> exists d e. ({step_after})"
        ),
        STEP_EXISTS: (
            "forall pb pc w. exists b c. "
            f"({_row_step('pb', 'pc', 'b', 'c', 'w', tag='bpsrx_result')})"
        ),
        TABLE_EXTEND: (
            "forall bb bc sb sc w r. "
            f"({table_before}) -> exists db dc eb ec. ({table_after})"
        ),
        TABLE_EXISTS: (
            "forall w r. exists bb bc sb sc. "
            f"({_table_prefix('bb', 'bc', 'sb', 'sc', 'w', 'r', tag='bptpx_result')})"
        ),
        CHOOSE_EXISTS: (
            "forall n k. exists z. "
            f"({module._choose_relation('n', 'k', 'z', tag='bce_result')})"
        ),
    }


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
    target = _closed_formula(item.statement)
    curried = target
    for dependency in reversed(item.dependencies):
        curried = Imp(_closed_formula(available[dependency].statement), curried)
    state = start(curried)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        if tactic == "use":
            raise AssertionError("Choose candidate body delegated through use")
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, curried), curried


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_unique_proof(proof: Proof):
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


@dataclass(frozen=True, slots=True)
class _Blueprint:
    names: tuple[str, ...]
    targets: tuple[Formula, ...]
    dependencies: tuple[tuple[int, ...], ...]
    layers: tuple[tuple[int, ...], ...]
    kinds: tuple[str, ...]
    root: int
    topology_sha256: str


@lru_cache(maxsize=1)
def _blueprint() -> _Blueprint:
    public = _specs_by_name()
    candidates = _table(_specs())
    stable_names: set[str] = set()
    candidate_order: list[str] = []
    marks: dict[str, int] = {}

    def visit(name: str) -> None:
        if name in public:
            stable_names.add(name)
            return
        item = candidates.get(name)
        if item is None:
            raise AssertionError(f"unknown Choose dependency {name!r}")
        mark = marks.get(name, 0)
        if mark == 1:
            raise AssertionError(f"cyclic Choose dependency at {name!r}")
        if mark == 2:
            return
        marks[name] = 1
        for dependency in item.dependencies:
            visit(dependency)
        marks[name] = 2
        candidate_order.append(name)

    visit(CHOOSE_EXISTS)
    names = tuple(sorted(stable_names)) + tuple(candidate_order)
    positions = {name: index for index, name in enumerate(names)}
    assert len(positions) == len(names)
    kinds = tuple(
        "stable_atomic" if name in stable_names else "candidate_body"
        for name in names
    )
    selected = tuple(
        public[name] if name in stable_names else candidates[name]
        for name in names
    )
    targets = tuple(_closed_formula(item.statement) for item in selected)
    dependencies = tuple(
        ()
        if kind == "stable_atomic"
        else tuple(positions[name] for name in item.dependencies)
        for kind, item in zip(kinds, selected, strict=True)
    )
    depths: list[int] = []
    for node_id, node_dependencies in enumerate(dependencies):
        assert all(dependency < node_id for dependency in node_dependencies)
        depths.append(
            0
            if not node_dependencies
            else 1 + max(depths[item] for item in node_dependencies)
        )
    layer_lists = [[] for _ in range(1 + max(depths, default=0))]
    for node_id, depth in enumerate(depths):
        layer_lists[depth].append(node_id)
    layers = tuple(tuple(layer) for layer in layer_lists)
    rows = (
        "\x1f".join(
            (
                str(node_id),
                name,
                kinds[node_id],
                selected[node_id].statement,
                "\x1e".join(names[item] for item in dependencies[node_id]),
            )
        )
        for node_id, name in enumerate(names)
    )
    return _Blueprint(
        names=names,
        targets=targets,
        dependencies=dependencies,
        layers=layers,
        kinds=kinds,
        root=positions[CHOOSE_EXISTS],
        topology_sha256=sha256("\x1c".join(rows).encode()).hexdigest(),
    )


@lru_cache(maxsize=1)
def _bundle() -> LayeredReplayBundle:
    blueprint = _blueprint()
    public = _specs_by_name()
    candidates = _table(_specs())
    targets = dict(zip(blueprint.names, blueprint.targets, strict=True))
    nodes: list[LayeredReplayNode] = []
    for node_id, name in enumerate(blueprint.names):
        if blueprint.kinds[node_id] == "stable_atomic":
            theorem = replay(name)
            assert theorem.formula == blueprint.targets[node_id]
            body = theorem.certificate
            expected_target = blueprint.targets[node_id]
        else:
            item = candidates[name]
            body, expected_target = _body(item)
            curried = blueprint.targets[node_id]
            for dependency in reversed(item.dependencies):
                curried = Imp(targets[dependency], curried)
            assert expected_target == curried
        assert check((), body, expected_target)
        nodes.append(
            LayeredReplayNode(
                node_id=node_id,
                target=blueprint.targets[node_id],
                dependencies=blueprint.dependencies[node_id],
                body=body,
            )
        )
    return LayeredReplayBundle(tuple(nodes), blueprint.root)


def test_choose_foundation_factory_is_exact_expanded_and_isolated() -> None:
    rows = _specs()
    table = _table(rows)
    assert make_bertrand_choose_foundation_candidate_theorems(TheoremSpec) == rows
    assert tuple(table) == EXPECTED_NAMES
    assert len(rows) == len(set(EXPECTED_NAMES)) == 7
    assert {item.name: item.statement for item in rows} == _expected_statements()
    assert {item.name: item.dependencies for item in rows} == EXPECTED_DEPENDENCIES
    assert module.__all__ == [
        "make_bertrand_choose_foundation_candidate_theorems"
    ]

    stable = set(_specs_by_name())
    alpha = {entry.spec.name for entry in editions_v7.ALPHA_ENTRIES}
    assert not (set(EXPECTED_NAMES) & stable)
    assert not (set(EXPECTED_NAMES) & alpha)
    assert all(
        "factorial" not in dependency
        for dependencies in EXPECTED_DEPENDENCIES.values()
        for dependency in dependencies
    )

    provider_token = "bertrand_choose_foundation_candidate"
    for authority_module in (stable_module, alpha_enrollment_v7, editions_v7):
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
                "PascalZeroRow(",
                "PascalRowStep(",
                "PascalTablePrefix(",
                "Choose(",
                "Factorial(",
                "Product(",
                "DivRem(",
                "<=",
                "%",
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
                "use ",
            )
        )
        available.add(item.name)


def test_choose_foundation_helpers_are_hygienic_and_structurally_exact() -> None:
    helper_cases = (
        (
            lambda tag: _zero_row("b", "c", "w", tag=tag),
            {"b", "c", "w"},
        ),
        (
            lambda tag: _row_step(
                "pb", "pc", "b", "c", "w", tag=tag
            ),
            {"pb", "pc", "b", "c", "w"},
        ),
        (
            lambda tag: _table_prefix(
                "bb", "bc", "sb", "sc", "w", "r", tag=tag
            ),
            {"bb", "bc", "sb", "sc", "w", "r"},
        ),
        (
            lambda tag: module._choose_relation("n", "k", "z", tag=tag),
            {"n", "k", "z"},
        ),
    )
    for builder, expected_free in helper_cases:
        first = builder("hygiene_a")
        second = builder("hygiene_b")
        assert first != second
        first_formula, first_free = parse_formula_with_names(first)
        second_formula, second_free = parse_formula_with_names(second)
        assert first_formula == second_formula
        assert first_free == second_free
        assert set(first_free) == expected_free

    with pytest.raises(ValueError):
        _zero_row("S", "c", "w", tag="valid")
    with pytest.raises(ValueError):
        _zero_row("bcf_index_valid", "c", "w", tag="valid")
    with pytest.raises(ValueError):
        _row_step("pb", "pc", "b", "c", "w", tag="bad-tag")
    with pytest.raises(ValueError):
        _table_prefix("bb", "bc", "sb", "sc", "w", "exists", tag="valid")
    with pytest.raises(ValueError):
        module._choose_relation("n", "k", "z", tag="forall")

    statements = _expected_statements()
    assert statements[ZERO_EXTEND].startswith("forall b c w. ")
    assert statements[STEP_EXTEND].startswith("forall pb pc b c w. ")
    assert statements[TABLE_EXTEND].startswith(
        "forall bb bc sb sc w r. "
    )
    assert statements[TABLE_EXISTS].startswith("forall w r. ")
    assert statements[CHOOSE_EXISTS].startswith("forall n k. exists z. ")
    choose = statements[CHOOSE_EXISTS]
    assert choose.count("bcf_lt_gap_bce_result_out_of_range") == 2
    assert choose.count("bcf_le_gap_bce_result_in_range") == 2
    assert choose.count("z = 0") == 1
    assert "S (n)" in choose
    table = statements[TABLE_EXTEND]
    assert "bb" in table and "bc" in table
    assert "sb" in table and "sc" in table
    assert "bptpe_after_decoded_previous_code" in table
    assert "bptpe_after_decoded_previous_scale" in table


def test_choose_foundation_receipt_manifests_are_fail_closed() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert EXPECTED_LAYERED_CLOSURE is None or set(
        EXPECTED_LAYERED_CLOSURE
    ) >= {"topology_sha256", "proof_dag_sha256", "kernel_accepted"}


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_choose_foundation_artifacts_are_frozen(row_name: str) -> None:
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
        f"CHOOSE FOUNDATION ARTIFACT row={row_name!r} actual={actual!r}",
        flush=True,
    )
    assert EXPECTED_ARTIFACTS[row_name] is not None, (
        f"freeze artifact receipt for {row_name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[row_name]


@pytest.mark.parametrize("row_name", EXPECTED_NAMES, ids=EXPECTED_NAMES)
def test_choose_foundation_bodies_and_envelopes_are_frozen(
    row_name: str,
) -> None:
    item = _table(_specs())[row_name]
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
        label=f"Choose foundation body {row_name}",
    )
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
    print(
        "CHOOSE FOUNDATION BODY "
        f"row={row_name!r} actual={actual_body!r} envelope={envelope!r}",
        flush=True,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_unique_proof(body))
    assert EXPECTED_BODIES[row_name] is not None, (
        f"freeze body receipt for {row_name}: {actual_body!r}"
    )
    assert EXPECTED_ENVELOPES[row_name] is not None, (
        f"freeze envelope receipt for {row_name}: {envelope!r}"
    )
    assert actual_body == EXPECTED_BODIES[row_name]
    assert envelope == EXPECTED_ENVELOPES[row_name]


@pytest.mark.parametrize(
    ("row_name", "dependency"),
    tuple(
        (row_name, dependency)
        for row_name, dependencies in EXPECTED_DEPENDENCIES.items()
        for dependency in dependencies
    ),
)
def test_choose_foundation_every_direct_dependency_is_live(
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
def test_choose_foundation_false_targets_are_rejected(row_name: str) -> None:
    item = _table(_specs())[row_name]
    false_item = replace(item, statement=f"({item.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((false_item,), core=_row_core(row_name))


def _boundary_mutations() -> tuple[tuple[str, str, str, str], ...]:
    statements = _expected_statements()
    zero_extend_old = " \\/ exists bcf_predecessor_bpzre_after. "
    zero_exists_old = " \\/ exists bcf_predecessor_bpzrx_result. "
    step_extend_old = " \\/ exists bcf_predecessor_bpsre_after "
    step_exists_old = " \\/ exists bcf_predecessor_bpsrx_result "
    table_extend_old = (
        "bcf_row_index_bptpe_after = S "
        "bcf_predecessor_bptpe_after"
    )
    table_exists_old = "bcf_row_index_bptpx_result = 0"
    choose_old = (
        "bcf_lt_gap_bce_result_out_of_range + S (n) = k"
    )
    cases = (
        (
            "zero_extend__require_zero_and_successor_boundary",
            ZERO_EXTEND,
            zero_extend_old,
            " /\\ exists bcf_predecessor_bpzre_after. ",
        ),
        (
            "zero_exists__require_zero_and_successor_boundary",
            ZERO_EXISTS,
            zero_exists_old,
            " /\\ exists bcf_predecessor_bpzrx_result. ",
        ),
        (
            "step_extend__require_zero_and_successor_boundary",
            STEP_EXTEND,
            step_extend_old,
            " /\\ exists bcf_predecessor_bpsre_after ",
        ),
        (
            "step_exists__require_zero_and_successor_boundary",
            STEP_EXISTS,
            step_exists_old,
            " /\\ exists bcf_predecessor_bpsrx_result ",
        ),
        (
            "table_extend__detach_successor_from_predecessor",
            TABLE_EXTEND,
            table_extend_old,
            (
                "bcf_row_index_bptpe_after = "
                "bcf_predecessor_bptpe_after"
            ),
        ),
        (
            "table_exists__move_zero_row_to_one",
            TABLE_EXISTS,
            table_exists_old,
            "bcf_row_index_bptpx_result = S 0",
        ),
        (
            "choose_exists__reverse_out_of_range_boundary",
            CHOOSE_EXISTS,
            choose_old,
            "bcf_lt_gap_bce_result_out_of_range + S (k) = n",
        ),
    )
    assert tuple(row_name for _, row_name, _, _ in cases) == EXPECTED_NAMES
    assert all(statements[row_name].count(old) == 1 for _, row_name, old, _ in cases)
    return cases


@pytest.mark.parametrize(
    ("case_id", "row_name", "old", "new"),
    _boundary_mutations(),
    ids=tuple(case[0] for case in _boundary_mutations()),
)
def test_choose_foundation_genuine_boundary_mutations_are_rejected(
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


def test_choose_foundation_root_pruned_layered_closure_is_frozen() -> None:
    blueprint = _blueprint()
    assert set(EXPECTED_NAMES) <= set(blueprint.names)
    assert blueprint.names[blueprint.root] == CHOOSE_EXISTS
    assert blueprint.root in blueprint.layers[-1]
    assert sum(map(len, blueprint.dependencies)) == sum(
        len(item.dependencies) for item in _specs()
    )
    reachable: set[int] = set()
    pending = [blueprint.root]
    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        pending.extend(blueprint.dependencies[node_id])
    assert reachable == set(range(len(blueprint.names)))

    raw_bundle = _bundle()
    interned = intern_layered_replay_bodies(
        raw_bundle,
        blueprint.targets[blueprint.root],
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    assert type(interned) is LayeredReplayBundle
    for raw, compact in zip(raw_bundle.nodes, interned.nodes, strict=True):
        assert raw.node_id == compact.node_id
        assert raw.target == compact.target
        assert raw.dependencies == compact.dependencies

    compilation = compile_layered_replay(
        interned,
        blueprint.targets[blueprint.root],
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    assert type(compilation) is LayeredReplayCandidate
    assert compilation.layers == blueprint.layers
    assert check((), compilation.certificate, compilation.target)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    assert compilation.proof_nodes <= limits.max_candidate_proof_occurrences
    assert compilation.proof_objects <= limits.max_candidate_proof_objects
    assert compilation.proof_depth <= limits.max_candidate_proof_depth
    assert (
        compilation.proof_annotation_occurrences
        <= limits.max_candidate_annotation_occurrences
    )
    assert compilation.proof_envelope_depth <= limits.max_candidate_envelope_depth
    assert (
        compilation.package_formula_occurrences
        <= limits.max_package_formula_occurrences
    )
    assert (
        compilation.maximum_package_formula_depth
        <= limits.max_package_formula_depth
    )
    assert not any(
        type(node) is DNE for node in _walk_unique_proof(compilation.certificate)
    )

    actual: dict[str, object] = {
        "topology_sha256": blueprint.topology_sha256,
        "node_count": len(blueprint.names),
        "stable_atomic_count": blueprint.kinds.count("stable_atomic"),
        "candidate_body_count": blueprint.kinds.count("candidate_body"),
        "dependency_edge_count": sum(map(len, blueprint.dependencies)),
        "layer_sizes": tuple(map(len, blueprint.layers)),
        "proof_nodes": compilation.proof_nodes,
        "proof_depth": compilation.proof_depth,
        "proof_objects": compilation.proof_objects,
        "proof_edges": compilation.proof_edges,
        "reused_objects": compilation.reused_objects,
        "annotation_occurrences": compilation.proof_annotation_occurrences,
        "envelope_depth": compilation.proof_envelope_depth,
        "package_formula_occurrences": compilation.package_formula_occurrences,
        "package_formula_depth": compilation.maximum_package_formula_depth,
        "proof_dag_sha256": _proof_dag_sha256(compilation.certificate),
        "kernel_accepted": True,
    }
    print(f"CHOOSE FOUNDATION LAYERED CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_LAYERED_CLOSURE is not None, (
        f"freeze layered closure receipt: {actual!r}"
    )
    assert actual == EXPECTED_LAYERED_CLOSURE

    direct_cut_count = 0
    probe = compilation.certificate
    while type(probe) is Cut:
        direct_cut_count += 1
        probe = probe.body
    assert direct_cut_count >= 3
    for index in range(direct_cut_count):
        corrupted = _mutate_direct_cut(compilation.certificate, index)
        assert not check((), corrupted, compilation.target)
