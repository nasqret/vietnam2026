"""Focused strict-HA audit for exact D06 cell functionality."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_cell_functional_candidate import (
    make_ha_cell_functional_candidate_theorems,
)
from peano_lab.library.ha_pair_cell_seed_candidate import cell
from peano_lab.library.ha_pair_injective_candidate import (
    make_ha_pair_injective_candidate_theorems,
)
from peano_lab.library.ha_pair_shell_candidate import (
    make_ha_pair_shell_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "cell_functional",
    "cell_head_functional",
    "cell_tail_functional",
)
EXPECTED_DEPENDENCIES = {
    "cell_functional": ("pair_code_injective",),
    "cell_head_functional": ("cell_functional",),
    "cell_tail_functional": ("cell_functional",),
}
PAIR1 = "(head1 + tail1) * S (head1 + tail1) + (tail1 + tail1)"
PAIR2 = "(head2 + tail2) * S (head2 + tail2) + (tail2 + tail2)"
PREFIX = (
    f"forall code head1 tail1 head2 tail2. code = S ({PAIR1}) -> "
    f"code = S ({PAIR2}) -> "
)
EXPECTED_STATEMENTS = {
    "cell_functional": PREFIX + "head1 = head2 /\\ tail1 = tail2",
    "cell_head_functional": PREFIX + "head1 = head2",
    "cell_tail_functional": PREFIX + "tail1 = tail2",
}
EXPECTED_STATEMENT_SHA256 = {
    "cell_functional":
        "090f28cb4425b8e512218607f5ed10559784f36059b180454cc6487ef619c77f",
    "cell_head_functional":
        "5e177bb042df92bc4e59a06335ccb791d8db0aae7e67d0a9e653c08515dd856c",
    "cell_tail_functional":
        "7fcdf8eab469302e0d6e7bd0ac6e3715fcce825cf0a1e5250defb1a575cd215b",
}
EXPECTED_BODY_RECEIPTS = {
    "cell_functional": (1, 21, 25, 16, 25, 24, 0),
    "cell_head_functional": (1, 18, 19, 17, 19, 18, 0),
    "cell_tail_functional": (1, 18, 19, 17, 19, 18, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "cell_functional": (
        2550, 33, 1146, 1211, 66, 60,
        "e1cfdfcfbe2b1bfb70f51cc724280d3bc7ac046c4bd14865bf390952b412a45c",
    ),
    "cell_head_functional": (
        2569, 34, 1165, 1230, 66, 61,
        "289cb3b6a42ca39e424e40712e44a24e4b7d4c7b355c4c0bd697d75ae42dfc9f",
    ),
    "cell_tail_functional": (
        2569, 34, 1165, 1230, 66, 61,
        "e03fdd8affeba3e1c0c1cb6f6e496c6ac53b13469db8c9c5b517f0df9de72d5c",
    ),
}
EXPECTED_CLOSURE = {
    "add_assoc", "add_comm", "add_eq_zero_right", "add_le_add_left",
    "add_le_add_right", "add_left_cancel", "add_mul", "add_right_cancel",
    "add_succ_left", "cell_functional", "cell_head_functional",
    "cell_tail_functional", "double_add_injective", "dt_right_le_shell",
    "dt_shell_monotone", "dt_shell_successor", "le_add_left", "le_succ",
    "le_trans", "lt_irrefl_expanded", "lt_of_lt_of_le", "lt_trichotomy",
    "mul_add", "mul_comm", "mul_eq_zero", "mul_le_mul_left",
    "mul_le_mul_right", "mul_left_cancel_nonzero", "mul_ne_zero",
    "mul_succ_left", "mul_zero_left", "no_succ_add_fixed",
    "pair_code_below_next_shell", "pair_code_injective",
    "pair_code_shell_lower", "pair_code_shell_separated", "succ_le_succ",
    "succ_ne_zero", "zero_add",
}


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_cell_functional_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _local_specs() -> dict[str, TheoremSpec]:
    specs = (
        make_ha_pair_shell_candidate_theorems(TheoremSpec)
        + make_ha_pair_injective_candidate_theorems(TheoremSpec)
        + _candidate_specs()
    )
    assert len(specs) == len({item.name for item in specs})
    return {item.name: item for item in specs}


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_unique(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
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
                (child, False) for child in children if id(child) not in digests
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


def _candidate_target(item: TheoremSpec, statement: str | None = None):
    available = dict(_specs_by_name()) | _local_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


def _body_certificate(item: TheoremSpec):
    target = _candidate_target(item)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _cold_closed_receipts():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    public = _specs_by_name()
    local = _local_specs()

    @lru_cache(maxsize=None)
    def close(name: str):
        if name in public:
            checked = replay(name)
            return checked.formula, checked.certificate

        item = local[name]
        formula = _closed_formula(item.statement)
        target = formula
        for dependency in reversed(item.dependencies):
            dependency_spec = local.get(dependency) or public[dependency]
            target = Imp(_closed_formula(dependency_spec.statement), target)
        state = start(target)
        for dependency in item.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
        for _dependency in item.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency in reversed(item.dependencies):
            dependency_formula, dependency_certificate = close(dependency)
            body = Cut(
                dependency_formula, formula, dependency_certificate, body
            )
        assert check((), body, formula)
        return formula, body

    receipts = {}
    for item in _candidate_specs():
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        assert check((), certificate, formula)
        unique = tuple(_walk_unique(certificate))
        assert not any(type(node) is DNE for node in unique)
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        receipts[item.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in unique),
            _proof_dag_digest(certificate),
        )
    return receipts


def _pair_code(left: int, right: int) -> int:
    shell = left + right
    return shell * (shell + 1) + 2 * right


def _cell_code(head: int, tail: int) -> int:
    return 1 + _pair_code(head, tail)


def test_cell_functional_surface_is_exact_ordered_and_publicly_isolated() -> None:
    specs = _candidate_specs()
    assert make_ha_cell_functional_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {item.name: item.statement for item in specs} == EXPECTED_STATEMENTS
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_functional_candidate" not in registry_source
    assert all(item.name not in registry_source for item in specs)

    d06_left = cell("code", "head1", "tail1")
    d06_right = cell("code", "head2", "tail2")
    assert PREFIX.startswith(
        f"forall code head1 tail1 head2 tail2. {d06_left} -> {d06_right} -> "
    )
    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement) == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("Cell(", "PairCode(", "BetaAt(", "DivRem(", "CRT(", "%")
        )


def test_cell_functional_combined_private_closure_is_k0_k2_constructive() -> None:
    local = _local_specs()
    public = _specs_by_name()
    pending = list(EXPECTED_NAMES)
    closure: dict[str, TheoremSpec] = {}
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        item = local.get(name) or public[name]
        closure[name] = item
        pending.extend(item.dependencies)
    assert set(closure) == EXPECTED_CLOSURE
    assert {"pair_code_injective", *EXPECTED_NAMES} <= set(closure)
    assert {
        item.name for item in make_ha_pair_shell_candidate_theorems(TheoremSpec)
    } <= set(closure)

    forbidden = (
        "beta", "crt", "division", "remainder", "classical", "dne",
        "by_contra", "excluded_middle", "sorry", "admit",
    )
    for item in closure.values():
        payload = "\n".join(
            (item.name, item.statement, *item.dependencies, *item.script, item.summary)
        ).casefold()
        assert all(fragment not in payload for fragment in forbidden)


def test_cell_functional_bodies_use_pa2_and_are_mutation_sensitive() -> None:
    core = dict(_specs_by_name())
    core.update(
        {
            item.name: item
            for item in (
                make_ha_pair_shell_candidate_theorems(TheoremSpec)
                + make_ha_pair_injective_candidate_theorems(TheoremSpec)
            )
        }
    )
    receipts = replay_candidate_bodies(_candidate_specs(), core=core)
    assert {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == EXPECTED_BODY_RECEIPTS

    joint = _local_specs()["cell_functional"]
    assert joint.dependencies == ("pair_code_injective",)
    assert joint.script.count("apply PA2") == 1
    assert joint.script.count("apply pair_code_injective") == 1
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "use"}
        for item in _candidate_specs()
        for command in item.script
    )

    mutations = {
        "cell_functional": lambda statement: statement.replace(
            "head1 = head2 /\\ tail1 = tail2",
            "head1 = S head2 /\\ tail1 = tail2",
        ),
        "cell_head_functional": lambda statement: statement.replace(
            "-> head1 = head2", "-> head1 = S head2"
        ),
        "cell_tail_functional": lambda statement: statement.replace(
            "-> tail1 = tail2", "-> tail1 = S tail2"
        ),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))
        mutated = mutations[item.name](item.statement)
        assert mutated != item.statement
        assert not check((), certificate, _candidate_target(item, mutated))


def test_cell_functional_bounded_semantics_and_false_encoding_mutation() -> None:
    observed: dict[int, tuple[int, int]] = {}
    for head, tail in product(range(16), repeat=2):
        code = _cell_code(head, tail)
        assert code > 0
        assert code not in observed
        observed[code] = (head, tail)

    for head1, tail1, head2, tail2 in product(range(7), repeat=4):
        if _cell_code(head1, tail1) == _cell_code(head2, tail2):
            assert head1 == head2
            assert tail1 == tail2

    shell_only_cell = lambda head, tail: 1 + (head + tail) * (head + tail + 1)
    assert shell_only_cell(1, 0) == shell_only_cell(0, 1)
    assert _cell_code(1, 0) != _cell_code(0, 1)


def test_cell_functional_empty_context_closure_is_twice_cold_and_bounded() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()
    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first

    assert MAX_LIVE_PROOF_NODES == MAX_USE_CERTIFICATE_NODES == 500_000
    assert MAX_LIVE_PROOF_OBJECTS == MAX_USE_CERTIFICATE_OBJECTS == 100_000
    assert MAX_LIVE_PROOF_DEPTH == MAX_USE_PROOF_DEPTH == 256
    for nodes, depth, objects, _edges, _reused, _cuts, _digest in first.values():
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS
        assert depth <= MAX_USE_PROOF_DEPTH
