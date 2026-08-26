"""Strict-HA audit for canonical signed-multiplication distributivity."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_signed_add_associative_candidate import (
    make_ha_signed_add_associative_candidate_theorems,
)
from peano_lab.library.ha_signed_add_candidate import (
    make_ha_signed_add_candidate_theorems,
    signed_add,
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
    signed_mul,
)
from peano_lab.library.ha_signed_mul_distributive_candidate import (
    make_ha_signed_mul_distributive_candidate_theorems,
)
from peano_lab.library.ha_signed_mul_laws_candidate import (
    make_ha_signed_mul_laws_candidate_theorems,
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
    "add_shuffle_middle",
    "add_cross_sum_pairwise",
    "signed_mul_distributive_component",
    "add_balance_outputs_compose",
    "signed_mul_left_cross_sum_distributes",
    "signed_mul_left_distributive",
    "signed_mul_right_distributive",
)
ENDPOINT_NAMES = {
    "signed_mul_left_distributive",
    "signed_mul_right_distributive",
}
EXPECTED_DEPENDENCIES = {
    "add_shuffle_middle": ("add_comm", "add_permute_outer"),
    "add_cross_sum_pairwise": ("add_shuffle_middle",),
    "signed_mul_distributive_component": (
        "mul_add",
        "add_shuffle_middle",
    ),
    "add_balance_outputs_compose": (
        "add_cross_sum_pairwise",
        "add_cross_sum_chain",
        "add_comm",
    ),
    "signed_mul_left_cross_sum_distributes": (
        "signed_pair_mul_cross_transport",
        "signed_mul_distributive_component",
    ),
    "signed_mul_left_distributive": (
        "signed_mul_to_decoded_equation",
        "add_balance_outputs_compose",
        "signed_mul_left_cross_sum_distributes",
        "add_cross_sum_chain",
        "signed_add_of_decoded_equation",
    ),
    "signed_mul_right_distributive": (
        "signed_mul_commutative",
        "signed_mul_left_distributive",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "add_shuffle_middle":
        "56292571581970f889ca14ff7e6f708005e3227af2279d40a09886b4e5385d2b",
    "add_cross_sum_pairwise":
        "979e3132826b571153f69243aead511b85f907b22082edde08e41027ffa0258d",
    "signed_mul_distributive_component":
        "51e3275f81a40c643a7f3fbd903c9dc668550282d58219e0cc6a6f91c769acb7",
    "add_balance_outputs_compose":
        "c20f95ccf62dbc9f0cf9c0f0f37caa212eae954d43afd95722f1c79ceef0e038",
    "signed_mul_left_cross_sum_distributes":
        "3653b7c5dffa62e95f0801c70b673c3e33490530869c4cdb286bc7161acf227a",
    "signed_mul_left_distributive":
        "78ef06cea880e1060206ba39e591685e26ecc96d3e7140695e791c0339763baa",
    "signed_mul_right_distributive":
        "11c87f1097377c7c61f2052be5fbd95ba40726c3f71c373399d1287533fb6001",
}
EXPECTED_BODY_RECEIPTS = {
    "add_shuffle_middle": (2, 13, 23, 13, 23, 22, 0),
    "add_cross_sum_pairwise": (1, 18, 27, 18, 27, 26, 0),
    "signed_mul_distributive_component": (2, 11, 23, 14, 23, 22, 0),
    "add_balance_outputs_compose": (3, 41, 48, 32, 48, 47, 0),
    "signed_mul_left_cross_sum_distributes": (2, 43, 42, 22, 42, 41, 0),
    "signed_mul_left_distributive": (5, 142, 199, 58, 199, 198, 0),
    "signed_mul_right_distributive": (2, 41, 44, 25, 44, 43, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "add_shuffle_middle": (
        245,
        17,
        161,
        172,
        12,
        6,
        "4dd61bd9bfabeb8900c1376d066fdef210b63c4b8fa7cbb60a52861afa857199",
    ),
    "add_cross_sum_pairwise": (
        272,
        18,
        188,
        199,
        12,
        7,
        "cb63dfdbd07345f18ee7eb250f19f428ffd6ad8a4c0d3b065b7c8ea9a93e15c0",
    ),
    "signed_mul_distributive_component": (
        345,
        19,
        224,
        240,
        17,
        9,
        "c4f2ccd30f6889281c06afea4b4804ed5d04673c8b2b89d013aa59283877b2ea",
    ),
    "add_balance_outputs_compose": (
        708,
        32,
        372,
        387,
        16,
        15,
        "9be646df81e74dbd7854cafc417114b321c5becdeefa30d07a91a82cb83956a8",
    ),
    "signed_mul_left_cross_sum_distributes": (
        1172,
        27,
        554,
        591,
        38,
        21,
        "a40d2cd61a2868b6681b85a3cb5c49289d1e9821814aa2b1feb5d3dfd7bb39c5",
    ),
    "signed_mul_left_distributive": (
        3297,
        58,
        1514,
        1561,
        48,
        49,
        "c02d8258cce2e4cbd6a16aa731c9ce3424f1cc4726f48c0bc55d80e9c19f6633",
    ),
    "signed_mul_right_distributive": (
        3717,
        60,
        1639,
        1688,
        50,
        53,
        "63d17772d42432a58c75064ff05ded34490519639625151c90c6cc591f7cf7d1",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "7befb7ae830b866a606e47f674730959e76599ded863aadd9868b850bcb190cd"
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
    "mul_add",
    "mul_comm",
    "mul_eq_zero",
    "mul_left_cancel_nonzero",
    "mul_ne_zero",
    "mul_succ_left",
    "mul_zero_left",
    "odd_half_unique",
    "succ_ne_zero",
    "zero_add",
    "zero_or_succ",
}
EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES = {
    "add_balance_outputs_compose",
    "add_cross_sum_chain",
    "add_cross_sum_pairwise",
    "add_shuffle_middle",
    "even_half_unique",
    "even_odd_exclusive_k1",
    "signed_add_of_decoded_equation",
    "signed_decode_functional",
    "signed_mul_commutative",
    "signed_mul_distributive_component",
    "signed_mul_left_cross_sum_distributes",
    "signed_mul_left_distributive",
    "signed_mul_to_decoded_equation",
    "signed_pair_mul_cross_transport",
}
FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_mul_distributive_candidate_theorems(TheoremSpec)


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
    """Close the complete 60-row signed stack from a cold public replay."""

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


def _value(code: int) -> int:
    pos, neg = _decode(code)
    return pos - neg


def _encode(value: int) -> int:
    return 2 * value if value >= 0 else 2 * (-value) - 1


def _add_code(left: int, right: int) -> int:
    return _encode(_value(left) + _value(right))


def _mul_code(left: int, right: int) -> int:
    return _encode(_value(left) * _value(right))


def _adds(left: int, right: int, output: int) -> bool:
    lp, ln = _decode(left)
    rp, rn = _decode(right)
    op, on = _decode(output)
    return (lp + rp) + on == (ln + rn) + op


def _muls(left: int, right: int, output: int) -> bool:
    lp, ln = _decode(left)
    rp, rn = _decode(right)
    op, on = _decode(output)
    return (lp * rp + ln * rn) + on == (lp * rn + ln * rp) + op


def test_signed_mul_distributive_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_mul_distributive_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_mul_distributive_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_distributive_statements_are_closed_and_graph_surfaces_are_exact() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedDecode(",
                "SignedMul(",
                "SignedAdd(",
                "DivRem(",
                "BetaAt(",
                "%",
                "<",
                "<=",
            )
        )

    left = (
        "forall a b c bc ab ac out. "
        f"({signed_add('b', 'c', 'bc', tag='distrib_left_bc')}) -> "
        f"({signed_mul('a', 'b', 'ab', tag='distrib_left_ab')}) -> "
        f"({signed_mul('a', 'c', 'ac', tag='distrib_left_ac')}) -> "
        f"({signed_mul('a', 'bc', 'out', tag='distrib_left_abc')}) -> "
        f"({signed_add('ab', 'ac', 'out', tag='distrib_left_products')})"
    )
    right = (
        "forall a b c bc ba ca out. "
        f"({signed_add('b', 'c', 'bc', tag='distrib_right_bc')}) -> "
        f"({signed_mul('b', 'a', 'ba', tag='distrib_right_ba')}) -> "
        f"({signed_mul('c', 'a', 'ca', tag='distrib_right_ca')}) -> "
        f"({signed_mul('bc', 'a', 'out', tag='distrib_right_bca')}) -> "
        f"({signed_add('ba', 'ca', 'out', tag='distrib_right_products')})"
    )
    specs = {item.name: item for item in _candidate_specs()}
    assert specs["signed_mul_left_distributive"].statement == left
    assert specs["signed_mul_right_distributive"].statement == right


def test_distributive_dependency_graph_is_strict_and_has_no_orphans() -> None:
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


def test_distributive_bodies_are_exact_and_mutation_sensitive() -> None:
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
        "add_shuffle_middle": lambda statement: statement.replace(
            "= (a + c) + (b + d)", "= S ((a + c) + (b + d))", 1
        ),
        "add_cross_sum_pairwise": lambda statement: statement.replace(
            "= (c + g) + (d + h)", "= S ((c + g) + (d + h))", 1
        ),
        "signed_mul_distributive_component": lambda statement: statement.replace(
            "= (a * b + c * d) + (a * e + c * f)",
            "= S ((a * b + c * d) + (a * e + c * f))",
            1,
        ),
        "add_balance_outputs_compose": lambda statement: statement.replace(
            "(u1 + u2) + w = (v1 + v2) + z",
            "(u1 + u2) + w = S ((v1 + v2) + z)",
            1,
        ),
        "signed_mul_left_cross_sum_distributes": lambda statement: statement.replace(
            "(ap * bcp + an * bcn))",
            "(ap * bcp + S (an * bcn)))",
            1,
        ),
        "signed_mul_left_distributive": lambda statement: statement.replace(
            " -> (exists sa_lp_distrib_left_products",
            " -> out = 0 /\\ (exists sa_lp_distrib_left_products",
            1,
        ),
        "signed_mul_right_distributive": lambda statement: statement.replace(
            " -> (exists sa_lp_distrib_right_products",
            " -> out = 0 /\\ (exists sa_lp_distrib_right_products",
            1,
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


def test_distributive_helpers_and_binary_equation_oracle() -> None:
    for a, b, c, d in product(range(5), repeat=4):
        assert (a + b) + (c + d) == (a + c) + (b + d)

    for a, b, c, d, e, f, g, h in product(range(2), repeat=8):
        if a + b == c + d and e + f == g + h:
            assert (a + e) + (b + f) == (c + g) + (d + h)

    for a, b, c, d, e, f in product(range(4), repeat=6):
        assert a * (b + e) + c * (d + f) == (
            a * b + c * d
        ) + (a * e + c * f)

    for values in product(range(2), repeat=10):
        p1, v1, n1, u1, p2, v2, n2, u2, w, z = values
        if (
            p1 + v1 == n1 + u1
            and p2 + v2 == n2 + u2
            and (p1 + p2) + w == (n1 + n2) + z
        ):
            assert (u1 + u2) + w == (v1 + v2) + z

    for ap, an, bp, bn, cp, cn, bcp, bcn in product(range(3), repeat=8):
        if (bp + cp) + bcn != (bn + cn) + bcp:
            continue
        assert (
            (ap * bp + an * bn) + (ap * cp + an * cn)
        ) + (ap * bcn + an * bcp) == (
            (ap * bn + an * bp) + (ap * cn + an * cp)
        ) + (ap * bcp + an * bcn)

    # The complete decoded distributivity checkpoint: all 2^14 tuples.
    for values in product(range(2), repeat=14):
        (
            ap,
            an,
            bp,
            bn,
            cp,
            cn,
            bcp,
            bcn,
            abp,
            abn,
            acp,
            acn,
            outp,
            outn,
        ) = values
        hbc = (bp + cp) + bcn == (bn + cn) + bcp
        hab = (ap * bp + an * bn) + abn == (
            ap * bn + an * bp
        ) + abp
        hac = (ap * cp + an * cn) + acn == (
            ap * cn + an * cp
        ) + acp
        hout = (ap * bcp + an * bcn) + outn == (
            ap * bcn + an * bcp
        ) + outp
        if hbc and hab and hac and hout:
            assert (abp + acp) + outn == (abn + acn) + outp


def test_both_distributive_graph_laws_on_first_seventeen_codes() -> None:
    for a, b, c in product(range(17), repeat=3):
        bc = _add_code(b, c)
        out = _mul_code(a, bc)
        ab = _mul_code(a, b)
        ac = _mul_code(a, c)
        assert _adds(b, c, bc)
        assert _muls(a, b, ab)
        assert _muls(a, c, ac)
        assert _muls(a, bc, out)
        assert _adds(ab, ac, out)

        ba = _mul_code(b, a)
        ca = _mul_code(c, a)
        right_out = _mul_code(bc, a)
        assert _muls(b, a, ba)
        assert _muls(c, a, ca)
        assert _muls(bc, a, right_out)
        assert _adds(ba, ca, right_out)
        assert right_out == out


def test_distributive_mutations_are_genuinely_false() -> None:
    # Every successor-strengthened helper conclusion fails at all-zero input.
    assert 0 == 0
    assert 0 != 1

    # Cancellation fixture: (-1)((-1) + 1) = 0.
    a, b, c = 1, 1, 2
    bc = _add_code(b, c)
    ab = _mul_code(a, b)
    ac = _mul_code(a, c)
    out = _mul_code(a, bc)
    assert (bc, ab, ac, out) == (0, 2, 1, 0)
    assert _adds(b, c, bc)
    assert _muls(a, b, ab)
    assert _muls(a, c, ac)
    assert _muls(a, bc, out)
    assert _adds(ab, ac, out)

    # The endpoint mutation forcing output zero fails for a nonzero product.
    a, b, c = 4, 2, 2
    bc = _add_code(b, c)
    out = _mul_code(a, bc)
    assert out == 8
    assert out != 0

    # Raw parity-code arithmetic is not canonical signed arithmetic.
    assert 1 * (1 + 2) == 3
    assert _mul_code(1, _add_code(1, 2)) == 0


def test_distributive_empty_context_closure_is_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 60
    assert len(_local_specs()) == len(_stack_specs())
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
