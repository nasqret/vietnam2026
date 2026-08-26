"""Focused native-body and closure audit for canonical gcd boundary laws."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    Imp,
    parse_formula,
    parse_formula_in_context,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.defined_syntax import parse_defined_formula_in_context
from peano_lab.library.ha_canonical_gcd_candidate import (
    make_ha_canonical_gcd_candidate_theorems,
)
from peano_lab.library.ha_canonical_gcd_edges_candidate import (
    edge_is_gcd,
    make_ha_canonical_gcd_edges_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "canonical_gcd_zero_right_iff",
    "canonical_gcd_zero_left_iff",
    "canonical_gcd_one_left_iff",
    "canonical_gcd_one_right_iff",
    "canonical_gcd_swap_functional",
)
EXPECTED_DEPENDENCIES = {
    "canonical_gcd_zero_right_iff": (
        "is_gcd_zero_right",
        "canonical_gcd_functional",
    ),
    "canonical_gcd_zero_left_iff": (
        "is_gcd_symm",
        "canonical_gcd_zero_right_iff",
    ),
    "canonical_gcd_one_left_iff": (
        "is_gcd_dvd_left",
        "divisor_one",
        "one_multiple",
        "is_gcd_of_dvd",
    ),
    "canonical_gcd_one_right_iff": (
        "is_gcd_symm",
        "canonical_gcd_one_left_iff",
    ),
    "canonical_gcd_swap_functional": (
        "is_gcd_symm",
        "canonical_gcd_functional",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "canonical_gcd_zero_right_iff":
        "8eae442eaa8b347cd9f71b106b9b85c7ddd4de460b7cf498ba2bb04613296576",
    "canonical_gcd_zero_left_iff":
        "46965c33d414fc67bde4ed7b1e6a4cc2b02af87f69e4abb84d487d9f85d3e2ae",
    "canonical_gcd_one_left_iff":
        "278eb32964ddbc738e81303372f64cf1728d340a34035f4bcf079841913fd3e0",
    "canonical_gcd_one_right_iff":
        "06a3c3a600eea5f97b2987a34c2cded18322680bd4d50d8501e3dd02fc91bc8b",
    "canonical_gcd_swap_functional":
        "503a5cf41ddd3dac5fcb70c2df9605e218176d0f046b893c94c6242723fab34e",
}
EXPECTED_BODY_RECEIPTS = {
    "canonical_gcd_zero_right_iff": (2, 18, 46, 18, 46, 45, 0),
    "canonical_gcd_zero_left_iff": (2, 30, 38, 15, 38, 37, 0),
    "canonical_gcd_one_left_iff": (4, 24, 33, 15, 33, 32, 0),
    "canonical_gcd_one_right_iff": (2, 27, 29, 12, 29, 28, 0),
    "canonical_gcd_swap_functional": (2, 19, 22, 15, 22, 21, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "canonical_gcd_zero_right_iff": (
        819,
        37,
        667,
        702,
        36,
        25,
        "d140ad3b257626cc287b51d576feb4aac6930aa7da58e9d72e5e2b2c30e2e45f",
    ),
    "canonical_gcd_zero_left_iff": (
        893,
        39,
        741,
        776,
        36,
        27,
        "a720a0a90192a564ab908357a59838ed8b25395045b631705e8da112c19f8932",
    ),
    "canonical_gcd_one_left_iff": (
        329,
        30,
        287,
        303,
        17,
        12,
        "4e4c7ceaab45dc15f9378f08e981524d07044d9e7e35a5f827bc510a8a383727",
    ),
    "canonical_gcd_one_right_iff": (
        394,
        32,
        352,
        368,
        17,
        14,
        "b21067e80580a93f1d1e76d77cf20bb9846598c2971d643fb35d0d6ee2f1c98c",
    ),
    "canonical_gcd_swap_functional": (
        766,
        37,
        647,
        681,
        35,
        22,
        "55650ade915e38fd01207d48169d891e06761dd3a277c827ea7b32d0bbb96615",
    ),
}


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_canonical_gcd_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_canonical_gcd_edges_candidate_theorems(TheoremSpec)


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


def _available_specs() -> dict[str, TheoremSpec]:
    return (
        dict(_specs_by_name())
        | {item.name: item for item in _support_specs()}
        | {item.name: item for item in _candidate_specs()}
    )


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


def _cold_closed_receipts() -> dict[str, tuple[int, int, int, int, int, int, str]]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    candidates = _support_specs() + _candidate_specs()
    local = {item.name: item for item in candidates}
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
        for dependency in item.dependencies:
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
        assert not any(type(node) is DNE for node in unique_nodes)
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        assert objects == len(unique_nodes)
        receipts[item.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in unique_nodes),
            _proof_dag_digest(certificate),
        )
    return receipts


def test_canonical_gcd_edges_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_canonical_gcd_edges_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    support = {item.name for item in _support_specs()}
    assert all(item.name not in public for item in first)
    assert all(item.name not in support for item in first)
    assert "is_gcd_zero_right" in public
    assert "is_gcd_symm" in public
    assert "canonical_gcd_functional" in support


def test_edge_is_gcd_is_literal_safe_hygienic_and_definition_exact() -> None:
    zero_left = edge_is_gcd("g", "a", "0", tag="alpha_left")
    zero_right = edge_is_gcd("g", "a", "0", tag="alpha_right")
    one_left = edge_is_gcd("g", "1", "a", tag="one_left")

    assert zero_left != zero_right
    assert parse_formula(zero_left) == parse_formula(zero_right)
    _, free_names = parse_formula_with_names(zero_left)
    assert set(free_names) == {"g", "a"}
    assert parse_formula_in_context(zero_left, ["g", "a"]) == (
        parse_defined_formula_in_context("IsGCD(g,a,0)", ["g", "a"])
    )
    assert parse_formula_in_context(one_left, ["g", "a"]) == (
        parse_defined_formula_in_context("IsGCD(g,1,a)", ["g", "a"])
    )
    assert all(
        token not in zero_left
        for token in ("IsGCD(", "Dvd(", "GCD(", "%", "<", "<=")
    )

    with pytest.raises(ValueError, match="left operand"):
        edge_is_gcd("g", "a + 1", "0", tag="bad_term")
    with pytest.raises(ValueError, match="gcd value"):
        edge_is_gcd("0", "a", "1", tag="bad_gcd")
    with pytest.raises(ValueError, match="binder tag"):
        edge_is_gcd("g", "a", "0", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        edge_is_gcd(
            "hage_left_factor_capture", "a", "0", tag="capture"
        )


def test_canonical_gcd_edge_contracts_are_closed_and_nonredundant() -> None:
    zero_right, zero_left, one_left, one_right, swap = _candidate_specs()
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("IsGCD(", "Dvd(", "GCD(", "iff", "<->")
        )

    assert zero_right.statement.startswith("forall a g.")
    assert "-> g = a) /\\ (g = a ->" in zero_right.statement
    assert "0 = g *" in zero_right.statement
    assert "0 = g *" in zero_left.statement
    assert "-> g = 1) /\\ (g = 1 ->" in one_left.statement
    assert "-> g = 1) /\\ (g = 1 ->" in one_right.statement
    assert swap.statement.startswith("forall a b g h.")
    assert swap.statement.endswith("-> g = h")

    # Predicate symmetry and the zero-right constructor already exist publicly;
    # this tranche adds equality characterizations and cross-witness symmetry.
    assert "is_gcd_symm" in _specs_by_name()
    assert "is_gcd_zero_right" in _specs_by_name()
    assert all(item.name != "canonical_gcd_zero_zero_iff" for item in _candidate_specs())


def test_zero_zero_convention_is_an_exact_one_row_specialization() -> None:
    zero_zero_assumption = edge_is_gcd(
        "g", "0", "0", tag="zero_zero_assumption"
    )
    zero_zero_result = edge_is_gcd("g", "0", "0", tag="zero_zero_result")
    corollary = TheoremSpec(
        "canonical_gcd_zero_zero_iff",
        f"forall g. (({zero_zero_assumption}) -> g = 0) /\\ "
        f"(g = 0 -> ({zero_zero_result}))",
        ("canonical_gcd_zero_right_iff",),
        (
            "intro g",
            "specialize canonical_gcd_zero_right_iff 0",
            "specialize canonical_gcd_zero_right_iff g",
            "exact canonical_gcd_zero_right_iff",
        ),
        "Zero-zero is the a=0 instance of the zero-right characterization.",
    )
    core = _available_specs()
    receipt = replay_candidate_bodies((corollary,), core=core)[0]
    assert (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    ) == (1, 4, 11, 7, 11, 10, 0)


def test_canonical_gcd_edge_bodies_are_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    core = dict(_specs_by_name()) | {
        item.name: item for item in _support_specs()
    }
    receipts = replay_candidate_bodies(specs, core=core)
    observed = {
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
    }
    assert observed == EXPECTED_BODY_RECEIPTS

    forbidden_tactics = {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
    commands = tuple(command for item in specs for command in item.script)
    assert all(
        command.split(maxsplit=1)[0] not in forbidden_tactics
        for command in commands
    )
    assert all(
        "DNE" not in command and "classical" not in command and "sorry" not in command
        for command in commands
    )

    mutations = {
        "canonical_gcd_zero_right_iff": lambda statement: statement.replace(
            "-> g = a) /\\", "-> S g = a) /\\", 1
        ),
        "canonical_gcd_zero_left_iff": lambda statement: statement.replace(
            "-> g = a) /\\", "-> S g = a) /\\", 1
        ),
        "canonical_gcd_one_left_iff": lambda statement: statement.replace(
            "-> g = 1) /\\", "-> S g = 1) /\\", 1
        ),
        "canonical_gcd_one_right_iff": lambda statement: statement.replace(
            "-> g = 1) /\\", "-> S g = 1) /\\", 1
        ),
        "canonical_gcd_swap_functional": lambda statement: statement.removesuffix(
            "g = h"
        ) + "S g = h",
    }
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_canonical_gcd_edge_empty_context_closure_is_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()

    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
