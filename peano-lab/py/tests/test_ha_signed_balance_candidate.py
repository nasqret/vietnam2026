"""Focused strict-HA audit for the first SignedBalance candidate tranche."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_signed_balance_candidate import (
    make_ha_signed_balance_candidate_theorems,
    signed_balance,
)
from peano_lab.library.ha_signed_decode_candidate import (
    make_ha_signed_decode_candidate_theorems,
)
from peano_lab.library.ha_signed_parity_candidate import (
    make_ha_signed_parity_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "signed_balance_total",
    "signed_decode_to_balance",
    "signed_balance_equations_cross_sum",
)
EXPECTED_DEPENDENCIES = {
    "signed_balance_total": ("lt_trichotomy", "add_comm"),
    "signed_decode_to_balance": ("add_comm",),
    "signed_balance_equations_cross_sum": (
        "add_permute_outer",
        "add_left_cancel",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_balance_total":
        "7ead89bbc04f8c8d4fbc4140b5fcdbe37982210f4e0596054f018fd1e56ce6fc",
    "signed_decode_to_balance":
        "3a4143b972b6dda1418780424671004f112e2a0d2dbbb0fccb7301c25e2706dd",
    "signed_balance_equations_cross_sum":
        "d82a666a0a0f27f497b4e9f73bbd4e6f3718d2dd8b63ce64edc3f899022f9438",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_balance_total": (2, 60, 97, 24, 97, 96, 0),
    "signed_decode_to_balance": (1, 11, 18, 13, 18, 17, 0),
    "signed_balance_equations_cross_sum": (2, 53, 118, 29, 106, 117, 12),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_balance_total": (
        236,
        24,
        230,
        235,
        6,
        4,
        "831fdaf085ae6fe2afab086b476ef710a5284eefeebda7fbfb11bd7b1c179273",
    ),
    "signed_decode_to_balance": (
        91,
        13,
        85,
        90,
        6,
        3,
        "3d663431a6c17b936e2e7923b02de729ff738102715e48f4dbd505acc6175218",
    ),
    "signed_balance_equations_cross_sum": (
        410,
        29,
        314,
        337,
        24,
        8,
        "9124fbef806ad0b53255d76ebd6d9b726d933aad7b733426d9bcf725dfd6dac9",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "73018efa9746d91509e80752b7aa87495bea8528e86d2cf8055dce1d1a62f3e4"
)
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_comm",
    "add_eq_zero_right",
    "add_left_cancel",
    "add_permute_outer",
    "add_right_cancel",
    "add_succ_left",
    "lt_trichotomy",
    "mul_eq_zero",
    "mul_left_cancel_nonzero",
    "mul_ne_zero",
    "odd_half_unique",
    "parity_cases",
    "succ_ne_zero",
    "zero_add",
    "zero_or_succ",
}
EXPECTED_TRANSITIVE_LOCAL_DEPENDENCIES = {
    "even_half_unique",
    "even_odd_exclusive_k1",
    "signed_balance_equations_cross_sum",
    "signed_balance_total",
    "signed_decode_functional",
    "signed_decode_negative_constructor",
    "signed_decode_nonnegative_constructor",
    "signed_decode_normal",
    "signed_decode_to_balance",
    "signed_decode_total",
    "signed_decode_zero_iff",
    "signed_valid_all",
}
FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
)
RFC_SIGNED_BALANCE = (
    "exists pos neg. (((code = 2 * pos /\\ neg = 0) \\/ exists half. "
    "((code = 2 * half + 1 /\\ pos = 0) /\\ neg = S half)) /\\ "
    "left + neg = right + pos)"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SIGNED_RFC_PATH = (
    REPOSITORY_ROOT
    / "research"
    / "arithmetic-library"
    / "ha-canonical-signed-natural-rfc-v1.md"
)


@lru_cache(maxsize=1)
def _parity_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_parity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _decode_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_decode_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_balance_candidate_theorems(TheoremSpec)


def _stack_specs() -> tuple[TheoremSpec, ...]:
    return (*_parity_specs(), *_decode_specs(), *_candidate_specs())


def _local_specs() -> dict[str, TheoremSpec]:
    return {item.name: item for item in _stack_specs()}


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


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local_specs()


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


def _stack_dependency_closure() -> tuple[set[str], set[str]]:
    public = _specs_by_name()
    local = _local_specs()
    pending = list(local)
    public_seen: set[str] = set()
    local_seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in public_seen or name in local_seen:
            continue
        if name in local:
            local_seen.add(name)
            pending.extend(local[name].dependencies)
        else:
            assert name in public, f"candidate dependency {name!r} is unavailable"
            public_seen.add(name)
            pending.extend(public[name].dependencies)
    return public_seen, local_seen


def _cold_closed_receipts() -> tuple[
    dict[str, tuple[int, int, int, int, int, int, str]], str
]:
    """Close the full parity/decoder/balance stack from a cold public replay."""

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
            assert type(body) is ImpIntro, (
                f"{item.name} did not expose dependency {dependency}"
            )
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

    # Deliberately force the entire prerequisite stack, not merely the three
    # roots in this tranche.  This makes candidate-to-candidate resolution and
    # every public dependency part of the cold audit boundary.
    for item in _stack_specs():
        close(item.name)

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

    stack_digest = sha256(
        "\n".join(
            f"{item.name}:{_proof_dag_digest(close(item.name)[1])}"
            for item in _stack_specs()
        ).encode()
    ).hexdigest()
    return receipts, stack_digest


def _decode_semantics(code: int, pos: int, neg: int, bound: int) -> bool:
    return (code == 2 * pos and neg == 0) or any(
        code == 2 * half + 1 and pos == 0 and neg == half + 1
        for half in range(bound + 1)
    )


def _balance_semantics(code: int, left: int, right: int, bound: int) -> bool:
    return any(
        _decode_semantics(code, pos, neg, bound)
        and left + neg == right + pos
        for pos in range(bound + 1)
        for neg in range(bound + 1)
    )


def _rfc_template(identifier: str) -> str:
    source = SIGNED_RFC_PATH.read_text(encoding="utf-8")
    marker = f"Stable RFC identifier: `{identifier}`."
    assert source.count(marker) == 1
    suffix = source.split(marker, 1)[1]
    assert suffix.startswith("\n\n```text\n")
    return suffix.removeprefix("\n\n```text\n").split("\n```", 1)[0]


def test_signed_balance_factory_is_exact_ordered_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_balance_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_balance_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_balance_surface_is_hygienic_and_matches_rfc_d03() -> None:
    assert _rfc_template("HA-K3-SIGNED-D03") == RFC_SIGNED_BALANCE
    assert sha256(RFC_SIGNED_BALANCE.encode()).hexdigest() == (
        "8cf2a9b1678dfe5b774a01adf746df046b2056e1ae620c8b0de89c741b7e4997"
    )

    left = signed_balance("code", "left", "right", tag="alpha_left")
    right = signed_balance("code", "left", "right", tag="alpha_right")
    assert left != right
    assert parse_formula(left) == parse_formula(right)
    assert parse_formula(left) == parse_formula(RFC_SIGNED_BALANCE)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"code", "left", "right"}

    with pytest.raises(ValueError, match="Peano identifier"):
        signed_balance("code + 1", "left", "right", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        signed_balance("code", "left", "right", tag="bad tag")
    with pytest.raises(ValueError, match="SignedBalance binder captures"):
        signed_balance("sb_pos_capture", "left", "right", tag="capture")
    with pytest.raises(ValueError, match="SignedDecode binder captures"):
        signed_balance("sd_half_capture", "left", "right", tag="capture")


def test_signed_balance_contracts_are_exact_closed_base_ha_formulas() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedBalance(",
                "SignedDecode(",
                "DivRem(",
                "BetaAt(",
                "ModEq(",
                "%",
                "<",
                "<=",
            )
        )

    total, transport, helper = _candidate_specs()
    assert total.statement == (
        "forall left right. exists code. (exists sb_pos_total sb_neg_total. "
        "(((code = 2 * sb_pos_total /\\ sb_neg_total = 0) \\/ exists "
        "sd_half_total. ((code = 2 * sd_half_total + 1 /\\ "
        "sb_pos_total = 0) /\\ sb_neg_total = S sd_half_total)) /\\ "
        "left + sb_neg_total = right + sb_pos_total))"
    )
    assert transport.statement.startswith("forall code pos neg. ((code = 2 * pos")
    assert transport.statement.endswith(
        "pos + sb_neg_decode_output = neg + sb_pos_decode_output))"
    )
    assert helper.statement == (
        "forall left1 right1 pos1 neg1 left2 right2 pos2 neg2. "
        "left1 + neg1 = right1 + pos1 -> "
        "left2 + neg2 = right2 + pos2 -> "
        "left1 + right2 = right1 + left2 -> "
        "pos1 + neg2 = neg1 + pos2"
    )


def test_signed_balance_stack_dependencies_are_transitively_safe() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _stack_dependency_closure()

    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_LOCAL_DEPENDENCIES
    assert set(item.name for item in _parity_specs()) <= local_closure
    assert set(item.name for item in _decode_specs()) <= local_closure
    assert "even_odd_exclusive_pointwise" not in public_closure
    assert "division_remainder_unique" not in public_closure

    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_signed_balance_bodies_are_constructive_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    core = dict(_specs_by_name()) | {
        item.name: item for item in (*_parity_specs(), *_decode_specs())
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

    forbidden_tactics = {
        "auto",
        "compact_arith",
        "norm_num",
        "ring",
        "simp",
        "use",
    }
    commands = tuple(command for item in specs for command in item.script)
    assert all(
        command.split(maxsplit=1)[0] not in forbidden_tactics
        for command in commands
    )
    assert all(
        marker not in command.lower()
        for command in commands
        for marker in ("classical", "dne", "sorry")
    )

    mutations = {
        "signed_balance_total": lambda statement: statement.replace(
            "right + sb_pos_total))",
            "right + S sb_pos_total))",
        ),
        "signed_decode_to_balance": lambda statement: statement.replace(
            "neg + sb_pos_decode_output))",
            "neg + S sb_pos_decode_output))",
        ),
        "signed_balance_equations_cross_sum": lambda statement: (
            statement.removesuffix("pos1 + neg2 = neg1 + pos2")
            + "S pos1 + neg2 = neg1 + pos2"
        ),
    }
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_signed_balance_representation_mutations_break_boundary_semantics() -> None:
    def reversed_balance(code: int, left: int, right: int, bound: int) -> bool:
        return any(
            _decode_semantics(code, pos, neg, bound)
            and left + pos == right + neg
            for pos in range(bound + 1)
            for neg in range(bound + 1)
        )

    # +1 is code 2 and -1 is code 1.  Reversing the balance equation swaps
    # those meanings, so this is a semantic boundary rather than formatting.
    assert _balance_semantics(2, 1, 0, 4)
    assert not _balance_semantics(1, 1, 0, 4)
    assert reversed_balance(1, 1, 0, 4)
    assert not reversed_balance(2, 1, 0, 4)

    # Allowing a negative-zero odd branch would also destroy the canonical
    # zero boundary inherited from SignedDecode.
    negative_zero_allowed = (
        lambda code, pos, neg, half: code == 2 * half + 1
        and pos == 0
        and neg == half
    )
    assert negative_zero_allowed(1, 0, 0, 0)
    assert not _decode_semantics(1, 0, 0, 4)


def test_signed_balance_bounded_semantics_and_cross_sum_fixtures() -> None:
    for left in range(9):
        for right in range(9):
            difference = left - right
            expected_code = (
                2 * difference if difference >= 0 else 2 * (-difference - 1) + 1
            )
            solutions = [
                code
                for code in range(18)
                if _balance_semantics(code, left, right, 9)
            ]
            assert solutions == [expected_code]

    for code in range(18):
        decoded = [
            (pos, neg)
            for pos in range(10)
            for neg in range(10)
            if _decode_semantics(code, pos, neg, 9)
        ]
        assert len(decoded) == 1
        pos, neg = decoded[0]
        assert _balance_semantics(code, pos, neg, 9)

    # Exhaustive small-model check of the pure additive helper.
    for left1 in range(4):
        for right1 in range(4):
            for pos1 in range(4):
                for neg1 in range(4):
                    if left1 + neg1 != right1 + pos1:
                        continue
                    for left2 in range(4):
                        for right2 in range(4):
                            if left1 + right2 != right1 + left2:
                                continue
                            for pos2 in range(4):
                                for neg2 in range(4):
                                    if left2 + neg2 == right2 + pos2:
                                        assert pos1 + neg2 == neg1 + pos2


def test_signed_balance_empty_context_stack_closure_is_deterministic() -> None:
    first_receipts, first_stack_digest = _cold_closed_receipts()
    second_receipts, second_stack_digest = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack_digest == EXPECTED_STACK_DAG_SHA256
    assert second_stack_digest == first_stack_digest
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
