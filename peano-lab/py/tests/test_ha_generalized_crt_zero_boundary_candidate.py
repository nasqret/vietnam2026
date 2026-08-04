"""Focused audit for the zero-inclusive generalized binary CRT ladder."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from math import gcd, lcm

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_generalized_crt_congruence_candidate import (
    make_ha_generalized_crt_congruence_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_sufficiency_candidate import (
    make_ha_generalized_crt_sufficiency_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_zero_boundary_candidate import (
    make_ha_generalized_crt_zero_boundary_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "generalized_binary_crt_sufficient_zero_left",
    "generalized_binary_crt_sufficient_zero_right",
    "generalized_binary_crt_sufficient",
    "generalized_binary_crt_solvable_iff",
)
EXPECTED_DEPENDENCIES = {
    "generalized_binary_crt_sufficient_zero_left": (
        "is_gcd_symm",
        "is_gcd_zero_right",
        "is_gcd_unique",
        "mod_eq_refl",
    ),
    "generalized_binary_crt_sufficient_zero_right": (
        "is_gcd_zero_right",
        "is_gcd_unique",
        "mod_eq_symm",
        "mod_eq_refl",
    ),
    "generalized_binary_crt_sufficient": (
        "eq_decidable",
        "generalized_binary_crt_sufficient_zero_left",
        "generalized_binary_crt_sufficient_zero_right",
        "generalized_binary_crt_sufficient_nonzero",
    ),
    "generalized_binary_crt_solvable_iff": (
        "crt_common_solution_implies_gcd_compatible",
        "generalized_binary_crt_sufficient",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "generalized_binary_crt_sufficient_zero_left":
        "c3bf6a9bee05e47d46ba4f9aa6b2d7ca0d3abdc1a7ef0e413e8acf9fa34a3ee4",
    "generalized_binary_crt_sufficient_zero_right":
        "5bcc9e19a6d128a93af0aff4f682a35a970f6154b66cb1e08a0142ef745c0fb8",
    "generalized_binary_crt_sufficient":
        "11e891144c1e9802af5bc0b3ae6ab3e18d29f329e96da0f1a447240a42d71116",
    "generalized_binary_crt_solvable_iff":
        "a6f60d923d9543160f447e7f43d938f8fbf3eceb49ca17c0b6a3b45bc5b5872c",
}
EXPECTED_SCRIPT_REPR_SHA256 = {
    "generalized_binary_crt_sufficient_zero_left":
        "4929d80795d3b29d8ad4dfb32cecfb8c7de6b19e1b0110b238c4788221d0b318",
    "generalized_binary_crt_sufficient_zero_right":
        "7f648410409135e1a865d2cb5380d7125ebdcaced27f00693ca126b9f2590170",
    "generalized_binary_crt_sufficient":
        "5288b5fb78c2d7f88e95ad8c16740ffa145bc3b0aac70667d7da0f5f1cc90080",
    "generalized_binary_crt_solvable_iff":
        "cee4e54f4636033bd90edf951744ff447c8223960be52201993ac5be7065a8ea",
}
EXPECTED_BODY_RECEIPTS = {
    "generalized_binary_crt_sufficient_zero_left":
        (4, 31, 48, 21, 48, 47, 0),
    "generalized_binary_crt_sufficient_zero_right":
        (4, 29, 43, 22, 43, 42, 0),
    "generalized_binary_crt_sufficient":
        (4, 49, 71, 23, 71, 70, 0),
    "generalized_binary_crt_solvable_iff":
        (2, 27, 67, 26, 67, 66, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "generalized_binary_crt_sufficient_zero_left": (
        834, 37, 682, 717, 36, 26, 0,
        "074f07df173308477693b6e3bbfd3a3a4123078d8f7f5eaac9077666d3cbc763",
    ),
    "generalized_binary_crt_sufficient_zero_right": (
        805, 36, 653, 688, 36, 26, 0,
        "da2d830f65077816dfeecd1503a787cf8ba0f5ec99e93d13b5456e4ba772e2f6",
    ),
    "generalized_binary_crt_sufficient": (
        11_240, 78, 3_495, 3_662, 168, 160, 0,
        "931fbcc775154507996c768cb1de1cc8479c3ed805ce0d1a95fffb530e8b56c4",
    ),
    "generalized_binary_crt_solvable_iff": (
        11_825, 80, 3_658, 3_830, 173, 168, 0,
        "3f1d82f0f06df9e0d2a5c746405ee46406db71c57e4bbf32f68792be07af8b0c",
    ),
}


@lru_cache(maxsize=1)
def _congruence_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_congruence_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _sufficiency_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_sufficiency_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_zero_boundary_candidate_theorems(
        TheoremSpec
    )


def _local_specs() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in (
            *_congruence_specs(),
            *_sufficiency_specs(),
            *_candidate_specs(),
        )
    }


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local_specs()


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk(proof: Proof):
    yield proof
    for child in _proof_children(proof):
        yield from _walk(child)


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


def _curried_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency_name in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency_name].statement), target)
    return target


def _body_certificate(item: TheoremSpec):
    target = _curried_target(item)
    state = start(target)
    for dependency_name in item.dependencies:
        state = apply_tactic(state, "intro", dependency_name)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _cold_closed_receipts():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    local = _local_specs()
    public = _specs_by_name()

    @lru_cache(maxsize=None)
    def close(name: str):
        if name in public:
            checked = replay(name)
            return checked.formula, checked.certificate

        item = local[name]
        formula = _closed_formula(item.statement)
        dependency_specs = tuple(
            local.get(dependency) or public[dependency]
            for dependency in item.dependencies
        )
        target = formula
        for dependency_spec in reversed(dependency_specs):
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
                dependency_formula,
                formula,
                dependency_certificate,
                body,
            )
        assert check((), body, formula)
        return formula, body

    receipts = {}
    for item in _candidate_specs():
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        assert check((), certificate, formula)
        unique_nodes = tuple(_walk_unique(certificate))
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        receipts[item.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in unique_nodes),
            sum(type(node) is DNE for node in unique_nodes),
            _proof_dag_digest(certificate),
        )
    return receipts


def test_zero_boundary_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_generalized_crt_zero_boundary_candidate_theorems(
        TheoremSpec
    )
    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == (
        EXPECTED_DEPENDENCIES
    )
    assert {
        item.name: sha256(item.statement.encode()).hexdigest()
        for item in first
    } == EXPECTED_STATEMENT_SHA256
    assert {
        item.name: sha256(repr(item.script).encode()).hexdigest()
        for item in first
    } == EXPECTED_SCRIPT_REPR_SHA256
    assert all(item.name not in _specs_by_name() for item in first)
    assert not hasattr(
        theorem_registry, "HA_GENERALIZED_CRT_ZERO_BOUNDARY_THEOREMS"
    )


def test_zero_boundary_contracts_are_closed_native_and_bounded() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert len(item.statement) < 4000
        assert all(
            token not in item.statement
            for token in (
                "IsGCD(",
                "Coprime(",
                "ModEq(",
                "CRTSolution(",
                "Dvd(",
                "%",
                "<=",
                "<->",
            )
        )

    assert "0 = g *" in _candidate_specs()[0].statement
    assert "m = g *" in _candidate_specs()[1].statement
    assert "x + 0 *" in _candidate_specs()[1].statement
    assert _candidate_specs()[2].statement.startswith("forall g m n a b.")
    assert "/\\" in _candidate_specs()[3].statement


def test_zero_boundary_bodies_are_constructive_and_mutation_sensitive() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item
        for item in (*_congruence_specs(), *_sufficiency_specs())
    }
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

    commands = tuple(
        command for item in _candidate_specs() for command in item.script
    )
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in commands
    )
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "classical", "by_contra", "sorry")
    )

    mutations = {
        "generalized_binary_crt_sufficient_zero_left": lambda statement:
            statement.replace("a + 0 *", "S a + 0 *", 1),
        "generalized_binary_crt_sufficient_zero_right": lambda statement:
            statement.replace("b + 0 *", "S b + 0 *", 1),
        "generalized_binary_crt_sufficient": lambda statement:
            statement.replace("a + m *", "S a + m *", 1),
        "generalized_binary_crt_solvable_iff": lambda statement:
            statement.replace("a + m *", "S a + m *", 1),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_zero_boundary_empty_context_closures_are_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()
    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(
        receipt[6] == 0 for receipt in EXPECTED_CLOSED_RECEIPTS.values()
    )
    assert all(item.name not in _specs_by_name() for item in _candidate_specs())


def _mod_eq(modulus: int, left: int, right: int) -> bool:
    return left == right if modulus == 0 else left % modulus == right % modulus


def _crt_solution(
    value: int,
    left_modulus: int,
    right_modulus: int,
    left_residue: int,
    right_residue: int,
) -> bool:
    return _mod_eq(left_modulus, value, left_residue) and _mod_eq(
        right_modulus, value, right_residue
    )


def test_zero_boundary_bounded_semantics() -> None:
    for n, a, b in product(range(6), repeat=3):
        compatible = _mod_eq(gcd(0, n), a, b)
        if compatible:
            assert _crt_solution(a, 0, n, a, b)

    for m, a, b in product(range(6), repeat=3):
        compatible = _mod_eq(gcd(m, 0), a, b)
        if compatible:
            assert _crt_solution(b, m, 0, a, b)

    for m, n, a, b in product(range(6), repeat=4):
        compatible = _mod_eq(gcd(m, n), a, b)
        if m == 0:
            candidates = (a,)
        elif n == 0:
            candidates = (b,)
        else:
            candidates = range(lcm(m, n))
        solutions = tuple(
            value
            for value in candidates
            if _crt_solution(value, m, n, a, b)
        )
        assert bool(solutions) == compatible
