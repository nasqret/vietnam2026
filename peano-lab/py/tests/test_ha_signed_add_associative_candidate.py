"""Strict-HA audit for canonical signed-addition associativity."""

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
    "add_cross_sum_chain",
    "signed_add_equations_associate",
    "signed_add_associative",
)
EXPECTED_DEPENDENCIES = {
    "add_cross_sum_chain": ("add_assoc", "add_comm", "add_left_cancel"),
    "signed_add_equations_associate": (
        "add_cross_sum_chain",
        "add_assoc",
        "add_comm",
        "add_permute_outer",
    ),
    "signed_add_associative": (
        "signed_add_to_decoded_equation",
        "signed_add_equations_associate",
        "signed_add_of_decoded_equation",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "add_cross_sum_chain":
        "fa68b8d6618ba4e355f74bb10e1b4fe86a9a567c19120533263f75347f690ef6",
    "signed_add_equations_associate":
        "f441723f3901a92c22c344c5f037d84ee858e8f1683493d91e6ad98baf6ac19b",
    "signed_add_associative":
        "62a4c1b9837905a14af15fc6a8931fa07fe338252787f2ce1ebb7d9a892ad094",
}
EXPECTED_BODY_RECEIPTS = {
    "add_cross_sum_chain": (3, 37, 66, 29, 66, 65, 0),
    "signed_add_equations_associate": (4, 91, 133, 35, 133, 132, 0),
    "signed_add_associative": (3, 97, 143, 47, 143, 142, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "add_cross_sum_chain": (
        315, 29, 231, 242, 12, 7,
        "dff8ac71df78d80bd9dfac3cdfd65f34a568d3a3ed6ef52236e40eaf91a80121",
    ),
    "signed_add_equations_associate": (
        703, 35, 407, 422, 16, 13,
        "ac5629e6081d3af7d0ba42c37ad0b5feca12eb30ff73d0ef5d453c85cc355f58",
    ),
    "signed_add_associative": (
        1695, 47, 1046, 1065, 20, 30,
        "dbac676cc5650d6f0d884dd2e4f9426d17342327cdf0abb59e71c40cc0a8a4cc",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "39ac0f7083ed54d2762289c7417b57a21c6dc97971b57efe2649ecb1cb7ec895"
)
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_comm",
    "add_eq_zero_right",
    "add_left_cancel",
    "add_permute_outer",
    "add_right_cancel",
    "add_succ_left",
    "mul_eq_zero",
    "mul_left_cancel_nonzero",
    "mul_ne_zero",
    "odd_half_unique",
    "succ_ne_zero",
    "zero_add",
    "zero_or_succ",
}
EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES = {
    "add_cross_sum_chain",
    "even_half_unique",
    "even_odd_exclusive_k1",
    "signed_add_equations_associate",
    "signed_add_of_decoded_equation",
    "signed_add_to_decoded_equation",
    "signed_decode_functional",
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_add_associative_candidate_theorems(TheoremSpec)


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


def _cold_closed_receipts() -> tuple[
    dict[str, tuple[int, int, int, int, int, int, str]], str
]:
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
            target = Imp(_closed_formula((local.get(dependency) or public[dependency]).statement), target)
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
            body = Cut(dependency_formula, formula, dependency_certificate, body)
        assert check((), body, formula)
        return formula, body

    candidate_names = set(EXPECTED_NAMES)
    receipts = {}
    stack_records = []
    for item in _stack_specs():
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        unique_nodes = tuple(_walk_unique(certificate))
        assert not any(type(node) is DNE for node in unique_nodes)
        digest = _proof_dag_digest(certificate)
        stack_records.append(f"{item.name}:{digest}")
        if item.name in candidate_names:
            nodes, depth = proof_metrics(certificate)
            objects, edges, reused = proof_identity_metrics(certificate)
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


def _adds(left: int, right: int, output: int) -> bool:
    return _value(left) + _value(right) == _value(output)


def test_signed_add_associative_factory_is_exact_and_registry_isolated() -> None:
    specs = _candidate_specs()
    assert make_ha_signed_add_associative_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {item.name: sha256(item.statement.encode()).hexdigest() for item in specs} == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_add_associative_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in specs)


def test_associative_statements_are_closed_base_language_graphs() -> None:
    specs = _candidate_specs()
    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in (
            "SignedDecode(", "SignedAdd(", "SignedBalance(", "DivRem(",
            "BetaAt(", "%", "<", "<=",
        ))
    expected_graph = (
        "forall a b c ab bc abc. "
        f"({signed_add('a', 'b', 'ab', tag='assoc_ab')}) -> "
        f"({signed_add('ab', 'c', 'abc', tag='assoc_abc')}) -> "
        f"({signed_add('b', 'c', 'bc', tag='assoc_bc')}) -> "
        f"({signed_add('a', 'bc', 'abc', tag='assoc_target')})"
    )
    assert specs[-1].statement == expected_graph


def test_associative_dependencies_and_bodies_are_strict_and_exact() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()
    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit = "\n".join((name, item.statement, *item.dependencies, *item.script, item.summary)).lower()
        assert all(marker not in audit for marker in FORBIDDEN_DEPENDENCY_MARKERS)

    core = dict(public) | {
        item.name: item for item in _stack_specs()[:-len(_candidate_specs())]
    }
    receipts = replay_candidate_bodies(_candidate_specs(), core=core)
    assert {r.name: (r.dependency_count, r.command_count, r.proof_nodes,
                     r.proof_depth, r.proof_objects, r.proof_edges,
                     r.reused_objects) for r in receipts} == EXPECTED_BODY_RECEIPTS
    forbidden_tactics = {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
    commands = [command for item in _candidate_specs() for command in item.script]
    assert all(command.split(maxsplit=1)[0] not in forbidden_tactics for command in commands)
    assert all(marker not in command.lower() for command in commands for marker in ("classical", "dne", "sorry"))


def test_associative_certificates_are_mutation_sensitive() -> None:
    mutations = {
        "add_cross_sum_chain": lambda s: s.replace("a + c = b + d", "a + c = S (b + d)", 1),
        "signed_add_equations_associate": lambda s: s.replace(
            "(ap + bcp) + outn = (an + bcn) + outp",
            "(ap + bcp) + outn = S ((an + bcn) + outp)", 1),
        "signed_add_associative": lambda s: s.replace(
            " -> (exists sa_lp_assoc_target",
            " -> abc = 0 /\\ (exists sa_lp_assoc_target", 1),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated = mutations[item.name](item.statement)
        assert mutated != item.statement
        _, free_names = parse_formula_with_names(mutated)
        assert not free_names
        assert not check((), certificate, _curried_target(item, mutated))


def test_general_algebra_helpers_hold_on_small_naturals() -> None:
    for a, b, x, y, c, d in product(range(4), repeat=6):
        if a + x == b + y and y + c == x + d:
            assert a + c == b + d

    for values in product(range(3), repeat=12):
        ap, an, bp, bn, cp, cn, abp, abn, bcp, bcn, outp, outn = values
        first = (ap + bp) + abn == (an + bn) + abp
        second = (abp + cp) + outn == (abn + cn) + outp
        third = (bp + cp) + bcn == (bn + cn) + bcp
        if first and second and third:
            assert (ap + bcp) + outn == (an + bcn) + outp


def test_signed_add_associativity_bounded_semantic_oracle() -> None:
    for a, b, c in product(range(17), repeat=3):
        ab = _add_code(a, b)
        left = _add_code(ab, c)
        bc = _add_code(b, c)
        right = _add_code(a, bc)
        assert left == right
        assert _adds(a, b, ab)
        assert _adds(ab, c, left)
        assert _adds(b, c, bc)
        assert _adds(a, bc, left)
    assert _add_code(_add_code(2, 1), 4) == 4
    assert _add_code(2, _add_code(1, 4)) == 4


def test_associative_empty_context_closure_and_stack_are_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()
    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 39
    assert len(_local_specs()) == 39
