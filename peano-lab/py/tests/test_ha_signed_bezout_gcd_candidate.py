"""Focused K4 audit for the relational-gcd SignedBezout client."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from math import gcd
from pathlib import Path

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_signed_add_associative_candidate import (
    make_ha_signed_add_associative_candidate_theorems,
)
from peano_lab.library.ha_signed_balance_candidate import (
    make_ha_signed_balance_candidate_theorems,
)
from peano_lab.library.ha_signed_bezout_candidate import (
    make_ha_signed_bezout_candidate_theorems,
    signed_bezout,
)
from peano_lab.library.ha_signed_bezout_gcd_candidate import (
    make_ha_signed_bezout_gcd_candidate_theorems,
)
from peano_lab.library.ha_signed_mul_distributive_candidate import (
    make_ha_signed_mul_distributive_candidate_theorems,
)
from peano_lab.library.ha_signed_nat_scale_laws_candidate import (
    make_ha_signed_nat_scale_laws_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAME = "gcd_signed_bezout_exists"
EXPECTED_DEPENDENCIES = (
    "gcd_balanced_bezout_exists",
    "balanced_bezout_to_signed_bezout",
)
EXPECTED_STATEMENT_LENGTH = 592
EXPECTED_STATEMENT_SHA256 = (
    "2e729fe9d25b8afda315489713f0a4cd7980371bf621e8af9e557f4ffca7496e"
)
EXPECTED_BODY_RECEIPT = (2, 20, 25, 13, 25, 24, 0)
EXPECTED_CLOSED_RECEIPT = (
    3535,
    48,
    1734,
    1824,
    91,
    74,
    "4edeb4ffc7de0b9aa0a870d2125f7640f2447a7358ba454abba3db003f9044a3",
)
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_comm",
    "add_eq_zero_right",
    "add_left_cancel",
    "add_mul",
    "add_permute_outer",
    "add_right_cancel",
    "add_succ_left",
    "balanced_bezout_euclid_step",
    "divides_linear_step",
    "divides_remainder",
    "division_remainder_exists",
    "division_remainder_succ",
    "factor_difference",
    "gcd_balanced_bezout_exists",
    "gcd_balanced_bezout_exists_up_to",
    "is_gcd_euclid_forward",
    "is_gcd_zero_right",
    "le_eq_or_lt",
    "le_of_succ_le_succ",
    "le_refl",
    "le_zero",
    "lt_trichotomy",
    "mul_add",
    "mul_assoc",
    "mul_comm",
    "mul_one",
    "mul_succ_left",
    "mul_zero_left",
    "multiple_refl",
    "multiple_zero",
    "zero_add",
    "zero_or_succ",
}
EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES = {
    "add_balance_outputs_compose",
    "add_cross_sum_chain",
    "add_cross_sum_pairwise",
    "add_shuffle_middle",
    "balanced_bezout_equation_transport",
    "balanced_bezout_to_signed_bezout",
    "mul_cross_sum_left",
    "signed_balance_total",
}
EXPECTED_DIVISION_BOUNDARY = {
    "divides_remainder",
    "division_remainder_exists",
    "division_remainder_succ",
}
FORBIDDEN_BOUNDARY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "dne",
    "excluded_middle",
)


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    """Return the minimal local support containing the eight reached rows."""

    builders = (
        make_ha_signed_balance_candidate_theorems,
        make_ha_signed_add_associative_candidate_theorems,
        make_ha_signed_mul_distributive_candidate_theorems,
        make_ha_signed_nat_scale_laws_candidate_theorems,
        make_ha_signed_bezout_candidate_theorems,
    )
    return tuple(
        item
        for builder in builders
        for item in builder(TheoremSpec)
    )


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_bezout_gcd_candidate_theorems(TheoremSpec)


def _local_specs(*, include_client: bool = True) -> dict[str, TheoremSpec]:
    specs = _support_specs()
    if include_client:
        specs = (*specs, *_candidate_specs())
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


def _dependency_closure() -> tuple[set[str], set[str]]:
    public = _specs_by_name()
    local = _local_specs()
    pending = list(_candidate_specs()[0].dependencies)
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
            assert name in public, f"client dependency {name!r} is unavailable"
            public_seen.add(name)
            pending.extend(public[name].dependencies)
    return public_seen, local_seen


def _cold_closed_result() -> tuple[
    tuple[int, int, int, int, int, int, str], Proof
]:
    """Close the K4 endpoint from cold public replay and local sources."""

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
        for dependency_name in reversed(item.dependencies):
            dependency = local.get(dependency_name) or public[dependency_name]
            target = Imp(_closed_formula(dependency.statement), target)

        state = start(target)
        for dependency_name in item.dependencies:
            state = apply_tactic(state, "intro", dependency_name)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
        for dependency_name in item.dependencies:
            assert type(body) is ImpIntro, (
                f"{item.name} did not expose dependency {dependency_name}"
            )
            body = body.body
        for dependency_name in reversed(item.dependencies):
            dependency_formula, dependency_certificate = close(dependency_name)
            body = Cut(
                dependency_formula,
                formula,
                dependency_certificate,
                body,
            )
        assert check((), body, formula)
        return formula, body

    item = _candidate_specs()[0]
    formula, certificate = close(item.name)
    assert formula == _closed_formula(item.statement)
    assert check((), certificate, formula)
    unique_nodes = tuple(_walk_unique(certificate))
    assert not any(type(node) is DNE for node in unique_nodes)
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    assert objects == len(unique_nodes)
    receipt = (
        nodes,
        depth,
        objects,
        edges,
        reused,
        sum(type(node) is Cut for node in unique_nodes),
        _proof_dag_digest(certificate),
    )
    return receipt, certificate


def _decode(code: int) -> tuple[int, int]:
    return (code // 2, 0) if code % 2 == 0 else (0, code // 2 + 1)


def _signed_value(code: int) -> int:
    positive, negative = _decode(code)
    return positive - negative


def _signed_bezout(result: int, a: int, b: int, x: int, y: int) -> bool:
    return a * _signed_value(x) + b * _signed_value(y) == result


def _divides(divisor: int, value: int) -> bool:
    return value == 0 if divisor == 0 else value % divisor == 0


def _is_gcd(candidate: int, a: int, b: int) -> bool:
    if not (_divides(candidate, a) and _divides(candidate, b)):
        return False
    bound = max(candidate, a, b) + 1
    return all(
        not (_divides(common, a) and _divides(common, b))
        or _divides(common, candidate)
        for common in range(bound + 1)
    )


def test_gcd_signed_bezout_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_bezout_gcd_candidate_theorems(TheoremSpec)

    assert second == first
    assert len(first) == 1
    item = first[0]
    assert item.name == EXPECTED_NAME
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert len(item.statement) == EXPECTED_STATEMENT_LENGTH
    assert sha256(item.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    support = _local_specs(include_client=False)
    assert item.name not in public
    assert "gcd_balanced_bezout_exists" in public
    assert "balanced_bezout_to_signed_bezout" not in public
    assert "balanced_bezout_to_signed_bezout" in support
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_signed_bezout_gcd_candidate" not in registry_source
    assert f'"{item.name}"' not in registry_source


def test_gcd_signed_bezout_statement_is_exact_closed_and_not_functional() -> None:
    item = _candidate_specs()[0]
    gcd_relation = (
        "(((exists u. a = d * u) /\\ (exists v. b = d * v)) /\\ "
        "forall c. (exists s. a = c * s) -> "
        "(exists t. b = c * t) -> exists w. d = c * w)"
    )
    relation = signed_bezout("d", "a", "b", "x", "y", tag="gcd")
    expected = (
        f"forall a b. exists d x y. ({gcd_relation} /\\ ({relation}))"
    )
    assert item.statement == expected
    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.startswith("forall a b. exists d x y.")
    assert "forall x y" not in item.statement
    assert "unique" not in item.summary.lower()
    assert all(
        token not in item.statement
        for token in (
            "IsGCD(",
            "SignedBezout(",
            "SignedDecode(",
            "DivRem(",
            "BetaAt(",
            "%",
            "<",
            "<=",
        )
    )


def test_gcd_signed_bezout_boundary_is_exactly_k4_and_constructive() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    observed_division_boundary = {
        name
        for name in public_closure | local_closure
        if "division" in name or "remainder" in name
    }
    assert observed_division_boundary == EXPECTED_DIVISION_BOUNDARY
    assert "division_remainder_exists" in public_closure
    assert "balanced_bezout_to_signed_bezout" in local_closure
    assert "signed_bezout_to_balanced_bezout" not in local_closure

    for name in public_closure | local_closure:
        row = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, row.statement, *row.dependencies, *row.script, row.summary)
        ).lower()
        assert all(
            marker not in audit_text for marker in FORBIDDEN_BOUNDARY_MARKERS
        )


def test_gcd_signed_bezout_body_is_exact_and_false_mutation_is_rejected() -> None:
    item = _candidate_specs()[0]
    core = dict(_specs_by_name()) | _local_specs(include_client=False)
    receipt = replay_candidate_bodies((item,), core=core)[0]
    observed = (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    )
    assert observed == EXPECTED_BODY_RECEIPT
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in item.script
    )
    assert all(
        marker not in command.lower()
        for command in item.script
        for marker in ("classical", "dne", "sorry")
    )

    certificate, target = _body_certificate(item)
    assert check((), certificate, target)
    original = (
        "a * sbz_xp_gcd + b * sbz_yp_gcd = "
        "d + (a * sbz_xn_gcd + b * sbz_yn_gcd)"
    )
    mutation = (
        "a * sbz_xp_gcd + b * sbz_yp_gcd = "
        "S (d + (a * sbz_xn_gcd + b * sbz_yn_gcd))"
    )
    assert item.statement.count(original) == 1
    mutated_statement = item.statement.replace(original, mutation)
    _, free_names = parse_formula_with_names(mutated_statement)
    assert not free_names
    assert mutated_statement != item.statement
    assert not check((), certificate, _curried_target(item, mutated_statement))


def test_gcd_signed_bezout_two_cold_closures_match_frozen_receipt() -> None:
    first_receipt, first_certificate = _cold_closed_result()
    second_receipt, second_certificate = _cold_closed_result()

    assert first_certificate is not second_certificate
    assert first_receipt == second_receipt == EXPECTED_CLOSED_RECEIPT


def test_gcd_signed_bezout_bounded_semantics_and_nonuniqueness() -> None:
    for candidate, a, b in product(range(7), repeat=3):
        assert _is_gcd(candidate, a, b) == (candidate == gcd(a, b))

    for a, b in product(range(7), repeat=2):
        result = gcd(a, b)
        witnesses = {
            (x, y)
            for x, y in product(range(9), repeat=2)
            if _signed_bezout(result, a, b, x, y)
        }
        assert _is_gcd(result, a, b)
        assert witnesses, (a, b, result)

    assert _signed_bezout(0, 0, 0, 7, 10)
    assert _signed_bezout(1, 2, 3, 1, 2)  # -1 and +1
    assert _signed_bezout(1, 2, 3, 4, 1)  # +2 and -1
    assert not _signed_bezout(1, 2, 3, 2, 1)
    nonunique = {
        (x, y)
        for x, y in product(range(13), repeat=2)
        if _signed_bezout(1, 2, 3, x, y)
    }
    assert {(1, 2), (4, 1)} <= nonunique
    assert len(nonunique) > 1
