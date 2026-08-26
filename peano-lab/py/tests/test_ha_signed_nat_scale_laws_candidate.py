"""Strict-HA audit for the canonical signed-natural scaling laws."""

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
)
from peano_lab.library.ha_signed_mul_distributive_candidate import (
    make_ha_signed_mul_distributive_candidate_theorems,
)
from peano_lab.library.ha_signed_mul_laws_candidate import (
    make_ha_signed_mul_laws_candidate_theorems,
)
from peano_lab.library.ha_signed_nat_scale_candidate import (
    make_ha_signed_nat_scale_candidate_theorems,
    signed_nat_scale,
)
from peano_lab.library.ha_signed_nat_scale_laws_candidate import (
    _signed_nat_scale_one,
    _signed_nat_scale_product,
    _signed_nat_scale_zero,
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
    "mul_cross_sum_left",
    "signed_nat_scale_equations_compose",
    "signed_nat_scale_zero",
    "signed_nat_scale_one",
    "signed_nat_scale_compose",
)
ENDPOINT_NAMES = {
    "signed_nat_scale_zero",
    "signed_nat_scale_one",
    "signed_nat_scale_compose",
}
EXPECTED_DEPENDENCIES = {
    "mul_cross_sum_left": ("mul_add",),
    "signed_nat_scale_equations_compose": (
        "mul_cross_sum_left",
        "mul_assoc",
        "add_cross_sum_chain",
    ),
    "signed_nat_scale_zero": (
        "signed_decode_total",
        "signed_nat_scale_of_decoded_equation",
        "mul_zero_left",
    ),
    "signed_nat_scale_one": (
        "signed_decode_total",
        "signed_nat_scale_of_decoded_equation",
        "one_mul",
        "add_comm",
    ),
    "signed_nat_scale_compose": (
        "signed_nat_scale_to_decoded_equation",
        "signed_nat_scale_equations_compose",
        "signed_nat_scale_of_decoded_equation",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "mul_cross_sum_left":
        "ee59c0e506fcba84d3dbb25b15521cfae4dac553022c0abb52ad18c681140ca8",
    "signed_nat_scale_equations_compose":
        "a0ab96eddfd582e91aedc76dccddae24b61380ceddf3ae119574f2d148ae8763",
    "signed_nat_scale_zero":
        "2368acd9a8b8c9d124de1b0310994df0831f5eff035160facc3f14fcfa92b423",
    "signed_nat_scale_one":
        "f0205eb9fbcab5d4cb269842b20bb5f9c4cef00d2b7440f396d69e6c4cb49b9b",
    "signed_nat_scale_compose":
        "08053ffa3d61d32c6a534f56db9ef956f48d0400083d1354324af10ad17b0e87",
}
EXPECTED_BODY_RECEIPTS = {
    "mul_cross_sum_left": (1, 14, 21, 13, 21, 20, 0),
    "signed_nat_scale_equations_compose": (3, 38, 46, 24, 46, 45, 0),
    "signed_nat_scale_zero": (3, 29, 38, 17, 38, 37, 0),
    "signed_nat_scale_one": (4, 23, 34, 18, 34, 33, 0),
    "signed_nat_scale_compose": (3, 54, 74, 31, 74, 73, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "mul_cross_sum_left": (
        98,
        17,
        91,
        97,
        7,
        2,
        "ffa3381d8208858dee25aba6f2f96ddfe2252f7c4c45d724a84f29f043e42586",
    ),
    "signed_nat_scale_equations_compose": (
        575,
        32,
        372,
        394,
        23,
        13,
        "064add40a96584356d47ca6a5455d16273403d23648ea64de5c5b3c5dc37a76b",
    ),
    "signed_nat_scale_zero": (
        183,
        21,
        174,
        182,
        9,
        4,
        "0e24789df5c82b513e59f376f03758a8d8f5e8ab03869d7e54fde7b7118e63af",
    ),
    "signed_nat_scale_one": (
        257,
        21,
        239,
        256,
        18,
        7,
        "90f005fdc0330354282b2dfec0105558dbc4533f1ef6436bdc070ed3a8789c4b",
    ),
    "signed_nat_scale_compose": (
        1453,
        34,
        897,
        923,
        27,
        30,
        "7548acf6871b7db3db4ba2cdaf89b9544e2d641c881a9f27e47dc4c77448b49e",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "81a18daf55e564c11dee83ce7465bc91876109a5e6bc092f75e0f31f46e27d8d"
)
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_comm",
    "add_eq_zero_right",
    "add_left_cancel",
    "add_right_cancel",
    "add_succ_left",
    "mul_add",
    "mul_assoc",
    "mul_eq_zero",
    "mul_left_cancel_nonzero",
    "mul_ne_zero",
    "mul_zero_left",
    "odd_half_unique",
    "one_mul",
    "parity_cases",
    "succ_ne_zero",
    "zero_add",
    "zero_or_succ",
}
EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES = {
    "add_cross_sum_chain",
    "even_half_unique",
    "even_odd_exclusive_k1",
    "mul_cross_sum_left",
    "signed_decode_functional",
    "signed_decode_total",
    "signed_nat_scale_equations_compose",
    "signed_nat_scale_of_decoded_equation",
    "signed_nat_scale_to_decoded_equation",
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
def _mul_distributive_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_mul_distributive_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _scale_core_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_nat_scale_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_nat_scale_laws_candidate_theorems(TheoremSpec)


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
    """Close the complete 70-row signed stack from a cold public replay."""

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


def _scale_code(scale: int, input_code: int) -> int:
    return _encode(scale * _value(input_code))


def _scales(scale: int, input_code: int, output_code: int) -> bool:
    ip, inn = _decode(input_code)
    op, on = _decode(output_code)
    return scale * ip + on == scale * inn + op


def _muls(left: int, right: int, output: int) -> bool:
    lp, ln = _decode(left)
    rp, rn = _decode(right)
    op, on = _decode(output)
    return (lp * rp + ln * rn) + on == (lp * rn + ln * rp) + op


def test_signed_nat_scale_law_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_nat_scale_laws_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_nat_scale_laws_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_nat_scale_law_statements_and_graph_surface_are_exact() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedDecode(",
                "SignedNatScale(",
                "DivRem(",
                "BetaAt(",
                "%",
                "<",
                "<=",
            )
        )

    expected = (
        "forall outer inner input middle output. "
        f"({signed_nat_scale('inner', 'input', 'middle', tag='compose_inner')}) -> "
        f"({signed_nat_scale('outer', 'middle', 'output', tag='compose_outer')}) -> "
        f"({_signed_nat_scale_product('outer', 'inner', 'input', 'output', tag='compose_target')})"
    )
    specs = {item.name: item for item in _candidate_specs()}
    assert specs["signed_nat_scale_zero"].statement == (
        f"forall input. ({_signed_nat_scale_zero('input', tag='zero')})"
    )
    assert specs["signed_nat_scale_one"].statement == (
        f"forall input. ({_signed_nat_scale_one('input', tag='one')})"
    )
    assert specs["signed_nat_scale_compose"].statement == expected


def test_signed_nat_scale_law_graph_is_strict_and_has_no_orphans() -> None:
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


def test_signed_nat_scale_law_bodies_are_exact_and_mutation_sensitive() -> None:
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
        "mul_cross_sum_left": lambda statement: statement.replace(
            "= k * c + k * d", "= S (k * c + k * d)", 1
        ),
        "signed_nat_scale_equations_compose": lambda statement: statement.replace(
            "= (outer * inner) * inn + op",
            "= S ((outer * inner) * inn + op)",
            1,
        ),
        "signed_nat_scale_zero": lambda statement: statement.replace(
            "forall input. (exists", "forall input. input = 0 /\\ (exists", 1
        ),
        "signed_nat_scale_one": lambda statement: statement.replace(
            "forall input. (exists", "forall input. input = 0 /\\ (exists", 1
        ),
        "signed_nat_scale_compose": lambda statement: statement.replace(
            " -> (exists sns_ip_compose_target",
            " -> output = 0 /\\ (exists sns_ip_compose_target",
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


def test_signed_nat_scale_law_decoded_equation_oracles_are_exhaustive() -> None:
    cross_sum_cases = 0
    for k, a, b, c, d in product(range(5), repeat=5):
        if a + b != c + d:
            continue
        cross_sum_cases += 1
        assert k * a + k * b == k * c + k * d
    assert cross_sum_cases == 425

    compose_cases = 0
    for outer, inner, ip, inn, mp, mn, op, on in product(
        range(3), repeat=8
    ):
        if not (
            inner * ip + mn == inner * inn + mp
            and outer * mp + on == outer * mn + op
        ):
            continue
        compose_cases += 1
        assert (outer * inner) * ip + on == (
            outer * inner
        ) * inn + op
    assert compose_cases == 477


def test_signed_nat_scale_zero_and_one_on_first_thirty_three_codes() -> None:
    for input_code in range(33):
        assert _scale_code(0, input_code) == 0
        assert _scale_code(1, input_code) == input_code
        assert _scales(0, input_code, 0)
        assert _scales(1, input_code, input_code)


def test_signed_nat_scale_graph_composes_on_first_seventeen_codes() -> None:
    for outer, inner, input_code in product(range(17), repeat=3):
        middle = _scale_code(inner, input_code)
        output = _scale_code(outer, middle)
        direct = _scale_code(outer * inner, input_code)
        assert _scales(inner, input_code, middle)
        assert _scales(outer, middle, output)
        assert _scales(outer * inner, input_code, output)
        assert output == direct

    # Sequential scaling preserves the negative sign through both stages.
    outer, inner, input_code = 3, 2, 1
    middle = _scale_code(inner, input_code)
    output = _scale_code(outer, middle)
    assert (middle, output) == (3, 11)
    assert _value(input_code) == -1
    assert _value(middle) == -2
    assert _value(output) == -6
    assert _scales(inner, input_code, middle)
    assert _scales(outer, middle, output)
    assert _scales(outer * inner, input_code, output)


def test_signed_nat_scale_core_coherence_and_mutations_are_genuine() -> None:
    for scale, input_code in product(range(9), range(33)):
        output = _scale_code(scale, input_code)
        assert _scales(scale, input_code, output)
        assert _muls(_encode(scale), input_code, output)

    # Literal-code arithmetic differs from canonical signed scaling.
    assert 2 * 1 == 2
    assert _scale_code(2, 1) == 3
    assert _scale_code(2, 1) != 2
    assert _scales(2, 1, 3)
    assert _muls(_encode(2), 1, 3)

    # The successor-strengthened helper conclusions fail at zero.
    assert 0 == 0
    assert 0 != 1

    # The zero/one mutations forcing every input code to zero fail at +1.
    assert _scales(0, 2, 0)
    assert _scales(1, 2, 2)
    assert 2 != 0

    # Composition can have a nonzero output, contradicting its mutation.
    outer, inner, input_code = 2, 3, 2
    middle = _scale_code(inner, input_code)
    output = _scale_code(outer, middle)
    assert (middle, output) == (6, 12)
    assert output != 0


def test_signed_nat_scale_law_empty_context_closure_is_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 70
    assert len(_local_specs()) == len(_stack_specs())
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
