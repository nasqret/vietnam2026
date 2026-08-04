"""Focused strict-HA audit for exact doubled-Cantor pair injectivity."""

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


EXPECTED_NAMES = ("double_add_injective", "pair_code_injective")
EXPECTED_DEPENDENCIES = {
    "double_add_injective": (
        "mul_left_cancel_nonzero",
        "succ_ne_zero",
        "mul_succ_left",
        "mul_zero_left",
        "zero_add",
    ),
    "pair_code_injective": (
        "double_add_injective",
        "pair_code_shell_separated",
        "lt_trichotomy",
        "lt_irrefl_expanded",
        "add_left_cancel",
        "add_right_cancel",
    ),
}
EXPECTED_STATEMENTS = {
    "double_add_injective": "forall a b. a + a = b + b -> a = b",
    "pair_code_injective": (
        "forall code l1 r1 l2 r2. code = "
        "(l1 + r1) * S (l1 + r1) + (r1 + r1) -> code = "
        "(l2 + r2) * S (l2 + r2) + (r2 + r2) -> "
        "l1 = l2 /\\ r1 = r2"
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "double_add_injective":
        "9a7cfdd4513598881e04ccd832c6e76923d935141a8dbe8f468d3cb32b71d4b9",
    "pair_code_injective":
        "be57f575eb538308784fb75d9be99c53c6a2c1982145e7cb8e47040800ac1a4a",
}
EXPECTED_BODY_RECEIPTS = {
    "double_add_injective": (5, 23, 58, 19, 58, 57, 0),
    "pair_code_injective": (6, 63, 99, 27, 99, 98, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "double_add_injective": (
        493, 25, 408, 430, 23, 15,
        "b0905453455317eb8e7bb8e7835fd049ad6afb98dabbf865719c02e2cc5b33ec",
    ),
    "pair_code_injective": (
        2525, 32, 1121, 1186, 66, 59,
        "7dc47f845a11797827e8682f4223af1e083afd48af60e0e22cd56862c44d06d8",
    ),
}
EXPECTED_CLOSURE = {
    "add_assoc", "add_comm", "add_eq_zero_right", "add_le_add_left",
    "add_le_add_right", "add_left_cancel", "add_mul", "add_right_cancel",
    "add_succ_left", "double_add_injective", "dt_right_le_shell",
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
def _injective_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_pair_injective_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _local_specs() -> dict[str, TheoremSpec]:
    specs = (
        make_ha_pair_shell_candidate_theorems(TheoremSpec)
        + _injective_specs()
    )
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
    for item in _injective_specs():
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


def test_pair_injective_factory_surface_is_exact_and_registry_isolated() -> None:
    specs = _injective_specs()
    assert make_ha_pair_injective_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {item.name: item.statement for item in specs} == EXPECTED_STATEMENTS
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_pair_injective_candidate" not in registry_source
    assert all(item.name not in registry_source for item in specs)

    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement) == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("PairCode(", "BetaAt(", "DivRem(", "CRT(", "%")
        )


def test_pair_injective_dependency_closure_is_foundational_and_constructive() -> None:
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

    forbidden = (
        "beta", "crt", "division", "remainder", "classical", "dne",
        "by_contra", "sorry",
    )
    for item in closure.values():
        payload = "\n".join(
            (item.name, item.statement, *item.dependencies, *item.script, item.summary)
        ).casefold()
        assert all(fragment not in payload for fragment in forbidden)


def test_pair_injective_bodies_are_exact_constructive_and_mutation_sensitive() -> None:
    core = dict(_specs_by_name())
    core.update(
        {
            item.name: item
            for item in make_ha_pair_shell_candidate_theorems(TheoremSpec)
        }
    )
    receipts = replay_candidate_bodies(_injective_specs(), core=core)
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

    pair_commands = _local_specs()["pair_code_injective"].script
    assert pair_commands.count("rewrite <- lt_trichotomy_left at hpair2") == 2
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "use"}
        for item in _injective_specs()
        for command in item.script
    )

    mutations = {
        "double_add_injective": lambda statement: statement.replace(
            "-> a = b", "-> a = S b"
        ),
        "pair_code_injective": lambda statement: statement.replace(
            "l1 = l2 /\\ r1 = r2", "l1 = S l2 /\\ r1 = r2"
        ),
    }
    for item in _injective_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))
        mutated = mutations[item.name](item.statement)
        assert mutated != item.statement
        assert not check((), certificate, _candidate_target(item, mutated))


def test_pair_injective_bounded_oracle_and_false_mutations() -> None:
    observed: dict[int, tuple[int, int]] = {}
    for left, right in product(range(12), repeat=2):
        code = _pair_code(left, right)
        assert code not in observed
        observed[code] = (left, right)

    for left1, right1, left2, right2 in product(range(6), repeat=4):
        if _pair_code(left1, right1) == _pair_code(left2, right2):
            assert (left1, right1) == (left2, right2)

    assert all((2 * a == 2 * b) == (a == b) for a, b in product(range(40), repeat=2))
    shell_only = lambda left, right: (left + right) * (left + right + 1)
    assert shell_only(1, 0) == shell_only(0, 1)
    assert _pair_code(1, 0) != _pair_code(0, 1)


def test_pair_injective_empty_context_closure_is_twice_cold_and_bounded() -> None:
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
