"""Strict-HA audit for the canonical signed Bezout bridge."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import ha_signed_bezout_candidate as bezout_module
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_signed_add_associative_candidate import (
    make_ha_signed_add_associative_candidate_theorems,
)
from peano_lab.library.ha_signed_add_candidate import (
    make_ha_signed_add_candidate_theorems,
)
from peano_lab.library.ha_signed_add_laws_candidate import (
    make_ha_signed_add_laws_candidate_theorems,
)
from peano_lab.library.ha_signed_balance_candidate import (
    make_ha_signed_balance_candidate_theorems,
)
from peano_lab.library.ha_signed_balance_complete_candidate import (
    make_ha_signed_balance_complete_candidate_theorems,
)
from peano_lab.library.ha_signed_bezout_candidate import (
    make_ha_signed_bezout_candidate_theorems,
    signed_bezout,
)
from peano_lab.library.ha_signed_code_extensional_candidate import (
    make_ha_signed_code_extensional_candidate_theorems,
)
from peano_lab.library.ha_signed_decode_candidate import (
    make_ha_signed_decode_candidate_theorems,
)
from peano_lab.library.ha_signed_mul_associative_candidate import (
    make_ha_signed_mul_associative_candidate_theorems,
)
from peano_lab.library.ha_signed_mul_candidate import (
    make_ha_signed_mul_candidate_theorems,
)
from peano_lab.library.ha_signed_mul_distributive_candidate import (
    make_ha_signed_mul_distributive_candidate_theorems,
)
from peano_lab.library.ha_signed_mul_laws_candidate import (
    make_ha_signed_mul_laws_candidate_theorems,
)
from peano_lab.library.ha_signed_nat_scale_candidate import (
    make_ha_signed_nat_scale_candidate_theorems,
)
from peano_lab.library.ha_signed_nat_scale_laws_candidate import (
    make_ha_signed_nat_scale_laws_candidate_theorems,
)
from peano_lab.library.ha_signed_negate_candidate import (
    make_ha_signed_negate_candidate_theorems,
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
    "balanced_bezout_equation_transport",
    "balanced_bezout_to_signed_bezout",
    "signed_bezout_to_balanced_bezout",
    "balanced_bezout_iff_signed_bezout_exists",
)
ENDPOINT_NAMES = {"balanced_bezout_iff_signed_bezout_exists"}
EXPECTED_DEPENDENCIES = {
    "balanced_bezout_equation_transport": (
        "mul_cross_sum_left",
        "add_balance_outputs_compose",
        "add_comm",
    ),
    "balanced_bezout_to_signed_bezout": (
        "signed_balance_total",
        "balanced_bezout_equation_transport",
    ),
    "signed_bezout_to_balanced_bezout": (),
    "balanced_bezout_iff_signed_bezout_exists": (
        "balanced_bezout_to_signed_bezout",
        "signed_bezout_to_balanced_bezout",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "balanced_bezout_equation_transport": (
        "352c2c9bff2c76025bd8f4a467b4d6b44409eed10d832e7e1e511e17636239c3"
    ),
    "balanced_bezout_to_signed_bezout": (
        "4e8141370b48a012fbb5940e5d5a63ea605116a7b4da84759481c39129bbb287"
    ),
    "signed_bezout_to_balanced_bezout": (
        "88039c1e4a15fc6f3a9d58588035762d330ae2216cc014557fce1d8290e3b18d"
    ),
    "balanced_bezout_iff_signed_bezout_exists": (
        "6054c489066d48e357e1a6df72a0f05d4c33657066e3a4b03c595d76e0974faa"
    ),
}
EXPECTED_BODY_RECEIPTS = {
    "balanced_bezout_equation_transport": (3, 56, 64, 33, 64, 63, 0),
    "balanced_bezout_to_signed_bezout": (2, 51, 62, 39, 62, 61, 0),
    "signed_bezout_to_balanced_bezout": (0, 17, 35, 23, 35, 34, 0),
    "balanced_bezout_iff_signed_bezout_exists": (2, 20, 50, 21, 50, 49, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "balanced_bezout_equation_transport": (
        943,
        34,
        497,
        518,
        22,
        20,
        "9e3f3b984b0c9bdd42e7747f5660541364bb5bee3655b95b9242e5ed3305e4cc",
    ),
    "balanced_bezout_to_signed_bezout": (
        1241,
        39,
        722,
        744,
        23,
        24,
        "f39a790749e8da2b6d6c36f3639e2b81ecdd1b5db892a543a7ece18941978923",
    ),
    "signed_bezout_to_balanced_bezout": (
        35,
        23,
        35,
        34,
        0,
        0,
        "f0fb3fa8d5f09c69d22721164468227765bab34b6f1eadb8d67593bfeb81fa28",
    ),
    "balanced_bezout_iff_signed_bezout_exists": (
        1326,
        40,
        807,
        829,
        23,
        26,
        "1bc7e28457b07b7aaf37b48aea0f3f86b58035797aeca50a022c73409f6eae1d",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "b7949148236ab243830a2bfebd80ddafeb31a63c5e70ace1c032de8bd2415f15"
)
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_comm",
    "add_left_cancel",
    "add_permute_outer",
    "add_right_cancel",
    "add_succ_left",
    "lt_trichotomy",
    "mul_add",
    "zero_add",
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
    "signed_bezout_to_balanced_bezout",
}
FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
)
RFC_SIGNED_BEZOUT = (
    "exists xp xn yp yn. (((x = 2 * xp /\\ xn = 0) \\/ exists x_half. "
    "((x = 2 * x_half + 1 /\\ xp = 0) /\\ xn = S x_half)) /\\ "
    "(((y = 2 * yp /\\ yn = 0) \\/ exists y_half. "
    "((y = 2 * y_half + 1 /\\ yp = 0) /\\ yn = S y_half)) /\\ "
    "a * xp + b * yp = result + (a * xn + b * yn)))"
)
RFC_SIGNED_BEZOUT_SHA256 = (
    "385bb4059c37669d69b2b069e59fb8ff32d6b48f097df79673cc193359ccfb78"
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
def _code_extensional_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_code_extensional_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _balance_seed_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_balance_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _balance_complete_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_balance_complete_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _negate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_negate_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _add_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_add_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _add_law_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_add_laws_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _add_associative_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_add_associative_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _mul_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_mul_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _mul_law_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_mul_laws_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _mul_associative_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_mul_associative_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _mul_distributive_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_mul_distributive_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _scale_core_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_nat_scale_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _scale_law_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_nat_scale_laws_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_bezout_candidate_theorems(TheoremSpec)


def _stack_specs() -> tuple[TheoremSpec, ...]:
    return (
        *_parity_specs(),
        *_decode_specs(),
        *_code_extensional_specs(),
        *_balance_seed_specs(),
        *_balance_complete_specs(),
        *_negate_specs(),
        *_add_specs(),
        *_add_law_specs(),
        *_add_associative_specs(),
        *_mul_specs(),
        *_mul_law_specs(),
        *_mul_associative_specs(),
        *_mul_distributive_specs(),
        *_scale_core_specs(),
        *_scale_law_specs(),
        *_candidate_specs(),
    )


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
    pending = [
        dependency
        for item in _candidate_specs()
        for dependency in item.dependencies
    ]
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


def _new_rows_reachable_from_endpoints() -> set[str]:
    new = {item.name: item for item in _candidate_specs()}
    pending = list(ENDPOINT_NAMES)
    reachable: set[str] = set()
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        if name in new:
            pending.extend(new[name].dependencies)
    return reachable & set(new)


def _cold_closed_receipts() -> tuple[
    dict[str, tuple[int, int, int, int, int, int, str]], str
]:
    """Close the complete 74-row signed stack from a cold public replay."""

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

    stack_records: list[str] = []
    candidate_names = set(EXPECTED_NAMES)
    receipts = {}
    for item in _stack_specs():
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        assert check((), certificate, formula)
        unique_nodes = tuple(_walk_unique(certificate))
        assert not any(type(node) is DNE for node in unique_nodes)
        digest = _proof_dag_digest(certificate)
        stack_records.append(f"{item.name}:{digest}")
        if item.name not in candidate_names:
            continue
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
            digest,
        )
    return receipts, sha256("\n".join(stack_records).encode()).hexdigest()


def _decode(code: int) -> tuple[int, int]:
    return (code // 2, 0) if code % 2 == 0 else (0, code // 2 + 1)


def _encode(value: int) -> int:
    return 2 * value if value >= 0 else 2 * (-value) - 1


def _value(code: int) -> int:
    pos, neg = _decode(code)
    return pos - neg


def _balanced(
    result: int,
    a: int,
    b: int,
    xp: int,
    yp: int,
    xn: int,
    yn: int,
) -> bool:
    return a * xp + b * yp == result + (a * xn + b * yn)


def _signed_bezout(result: int, a: int, b: int, x: int, y: int) -> bool:
    xp, xn = _decode(x)
    yp, yn = _decode(y)
    return _balanced(result, a, b, xp, yp, xn, yn)


def _strengthen_result_zero(statement: str, prefix: str) -> str:
    assert statement.startswith(prefix)
    return f"{prefix}(result = 0 /\\ ({statement[len(prefix):]}))"


def _transport_successor_mutation(statement: str) -> str:
    original = "a * xcp + b * ycp = result + (a * xcn + b * ycn)"
    mutation = "a * xcp + b * ycp = S (result + (a * xcn + b * ycn))"
    assert statement.endswith(original)
    return f"{statement[:-len(original)]}{mutation}"


def test_signed_bezout_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_bezout_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_signed_bezout_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_bezout_contract_is_hygienic_and_exact_rfc_d08() -> None:
    alpha_relation = signed_bezout(
        "result", "a", "b", "x", "y", tag="rfc_audit"
    )
    assert parse_formula(
        f"forall result a b x y. ({alpha_relation})"
    ) == parse_formula(
        f"forall result a b x y. ({RFC_SIGNED_BEZOUT})"
    )
    assert (
        sha256(RFC_SIGNED_BEZOUT.encode()).hexdigest()
        == RFC_SIGNED_BEZOUT_SHA256
    )

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedDecode(",
                "SignedBalance(",
                "SignedBezout(",
                "DivRem(",
                "BetaAt(",
                "%",
                "<",
                "<=",
            )
        )

    source = SIGNED_RFC_PATH.read_text(encoding="utf-8")
    assert "### 4.8 `SignedBezout(result,a,b,x,y)`" in source
    assert f"```text\n{RFC_SIGNED_BEZOUT}\n```" in source
    assert (
        f"| `HA-K3-SIGNED-D08` | `{RFC_SIGNED_BEZOUT_SHA256}` |"
        in source
    )

    assert signed_bezout("code", "code", "code", "code", "code", tag="same")
    with pytest.raises(ValueError):
        signed_bezout("0", "a", "b", "x", "y", tag="bad")
    with pytest.raises(ValueError):
        signed_bezout("result", "forall", "b", "x", "y", tag="bad")
    with pytest.raises(ValueError, match="captures an argument"):
        signed_bezout(
            "result", "a", "b", "sbz_xp_capture", "y", tag="capture"
        )
    with pytest.raises(ValueError, match="SignedDecode binder captures"):
        signed_bezout(
            "result", "a", "b", "sd_half_capture_x", "y", tag="capture"
        )
    with pytest.raises(ValueError, match="SignedDecode binder captures"):
        signed_bezout(
            "result", "a", "b", "x", "sd_half_capture_y", tag="capture"
        )
    with pytest.raises(ValueError):
        signed_bezout("result", "a", "b", "x", "y", tag="bad-tag")


def test_signed_bezout_statement_surfaces_preserve_both_witness_orders() -> None:
    forward_balanced = bezout_module._balanced_bezout(
        "result", "a", "b", tag="forward"
    )
    forward_signed = signed_bezout(
        "result", "a", "b", "x", "y", tag="forward"
    )
    reverse_balanced = bezout_module._balanced_bezout(
        "result", "a", "b", tag="reverse"
    )
    reverse_signed = signed_bezout(
        "result", "a", "b", "x", "y", tag="reverse"
    )
    iff_left = bezout_module._balanced_bezout(
        "result", "a", "b", tag="iff_left"
    )
    iff_forward = signed_bezout(
        "result", "a", "b", "x", "y", tag="iff_forward"
    )
    iff_reverse = signed_bezout(
        "result", "a", "b", "x", "y", tag="iff_reverse"
    )
    iff_right = bezout_module._balanced_bezout(
        "result", "a", "b", tag="iff_right"
    )
    expected = {
        "balanced_bezout_equation_transport": (
            "forall result a b xp yp xn yn xcp xcn ycp ycn. "
            "xp + xcn = xn + xcp -> yp + ycn = yn + ycp -> "
            "a * xp + b * yp = result + (a * xn + b * yn) -> "
            "a * xcp + b * ycp = result + (a * xcn + b * ycn)"
        ),
        "balanced_bezout_to_signed_bezout": (
            f"forall result a b. ({forward_balanced}) -> "
            f"exists x y. ({forward_signed})"
        ),
        "signed_bezout_to_balanced_bezout": (
            f"forall result a b x y. ({reverse_signed}) -> "
            f"({reverse_balanced})"
        ),
        "balanced_bezout_iff_signed_bezout_exists": (
            f"forall result a b. ((({iff_left}) -> exists x y. "
            f"({iff_forward})) /\\ ((exists x y. ({iff_reverse})) -> "
            f"({iff_right})))"
        ),
    }
    assert {item.name: item.statement for item in _candidate_specs()} == expected

    specs = {item.name: item for item in _candidate_specs()}
    reverse = specs["signed_bezout_to_balanced_bezout"]
    assert "exists bb_xp_reverse bb_yp_reverse bb_xn_reverse bb_yn_reverse." in (
        reverse.statement
    )
    assert reverse.script[-5:] == (
        "exists x1",
        "exists x3",
        "exists x2",
        "exists x4",
        "exact hsigned_witness_witness_witness_witness_right_right",
    )

    with pytest.raises(ValueError, match="captures an argument"):
        bezout_module._balanced_bezout(
            "bb_xp_capture", "a", "b", tag="capture"
        )


def test_signed_bezout_dependency_graph_is_strict_and_has_no_orphans() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

    assert _new_rows_reachable_from_endpoints() == set(EXPECTED_NAMES)
    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(
            marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS
        )


def test_signed_bezout_bodies_are_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    core = dict(_specs_by_name()) | {
        item.name: item for item in _stack_specs()[:-len(specs)]
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
        "balanced_bezout_equation_transport": _transport_successor_mutation,
        "balanced_bezout_to_signed_bezout": lambda statement: (
            _strengthen_result_zero(statement, "forall result a b. ")
        ),
        "signed_bezout_to_balanced_bezout": lambda statement: (
            _strengthen_result_zero(statement, "forall result a b x y. ")
        ),
        "balanced_bezout_iff_signed_bezout_exists": lambda statement: (
            _strengthen_result_zero(statement, "forall result a b. ")
        ),
    }
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        _, free_names = parse_formula_with_names(mutated_statement)
        assert not free_names
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_balanced_bezout_transport_oracle_is_exhaustive_on_ternary_cube() -> None:
    premise_cases = 0
    for values in product(range(3), repeat=11):
        result, a, b, xp, yp, xn, yn, xcp, xcn, ycp, ycn = values
        if not (
            xp + xcn == xn + xcp
            and yp + ycn == yn + ycp
            and _balanced(result, a, b, xp, yp, xn, yn)
        ):
            continue
        premise_cases += 1
        assert _balanced(result, a, b, xcp, ycp, xcn, ycn)
    assert premise_cases == 2_185


def test_forward_normalization_oracle_is_exhaustive_on_quinary_cube() -> None:
    balanced_cases = 0
    for result, a, b, xp, yp, xn, yn in product(range(5), repeat=7):
        if not _balanced(result, a, b, xp, yp, xn, yn):
            continue
        balanced_cases += 1
        x = _encode(xp - xn)
        y = _encode(yp - yn)
        assert _signed_bezout(result, a, b, x, y)
        assert _value(x) == xp - xn
        assert _value(y) == yp - yn
    assert balanced_cases == 5_736


def test_signed_bezout_direct_graph_oracle_and_pinned_fixtures() -> None:
    true_cases = 0
    for result, a, b in product(range(7), repeat=3):
        for x, y in product(range(13), repeat=2):
            if _signed_bezout(result, a, b, x, y):
                true_cases += 1
                assert a * _value(x) + b * _value(y) == result
    assert true_cases == 1_600

    # Canonical coefficients: 2*(-1) + 3*(+1) = 1.
    assert (_value(1), _value(2)) == (-1, 1)
    assert _signed_bezout(1, 2, 3, 1, 2)

    # Coefficients are not functional: a distinct canonical pair also works.
    assert (_value(4), _value(1)) == (2, -1)
    assert _signed_bezout(1, 2, 3, 4, 1)
    assert (1, 2) != (4, 1)

    # The all-zero linear form represents result zero for arbitrary codes.
    assert _signed_bezout(0, 0, 0, 7, 10)

    # Raw parity codes are not the integers they encode.
    assert 2 * 1 + 3 * 2 == 8
    assert _signed_bezout(1, 2, 3, 1, 2)
    assert not _signed_bezout(1, 2, 3, 2, 1)


def test_offset_normalization_witness_order_and_negative_controls() -> None:
    result, a, b, xp, yp, xn, yn = (1, 2, 3, 5, 8, 6, 7)
    assert a * xp + b * yp == 34
    assert result + (a * xn + b * yn) == 34
    assert _balanced(result, a, b, xp, yp, xn, yn)

    # Raw order is xp,yp,xn,yn; normalizing each coefficient pair gives -1,+1.
    x = _encode(xp - xn)
    y = _encode(yp - yn)
    assert (x, y) == (1, 2)
    assert _signed_bezout(result, a, b, x, y)

    # Pairing adjacent raw witnesses instead would silently change the theorem.
    wrong_x = _encode(xp - yp)
    wrong_y = _encode(xn - yn)
    assert (wrong_x, wrong_y) == (5, 1)
    assert a * _value(wrong_x) + b * _value(wrong_y) == -9
    assert not _signed_bezout(result, a, b, wrong_x, wrong_y)

    # SignedBezout is not arbitrarily total: 0*x + 0*y cannot represent 1.
    assert all(
        not _signed_bezout(1, 0, 0, candidate_x, candidate_y)
        for candidate_x, candidate_y in product(range(13), repeat=2)
    )
    assert 0 != 1

    # Each kernel mutation has a concrete false instance.
    assert _balanced(0, 0, 0, 0, 0, 0, 0)
    assert not (0 == 1)  # successor-strengthened transport at the zero tuple
    assert _balanced(1, 2, 3, 0, 1, 1, 0)
    assert _signed_bezout(1, 2, 3, 1, 2)
    assert result != 0


def test_signed_bezout_empty_context_closure_is_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 74
    assert len(_local_specs()) == len(_stack_specs())
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
