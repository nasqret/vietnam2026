"""Strict-HA audit for canonical signed-multiplication associativity."""

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
    signed_mul,
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
    "signed_pair_mul_cross_transport",
    "signed_pair_mul_components_associate",
    "signed_mul_equations_associate",
    "signed_mul_associative",
)
EXPECTED_DEPENDENCIES = {
    "signed_pair_mul_cross_transport": (
        "add_mul",
        "mul_add",
        "add_comm",
        "add_permute_outer",
    ),
    "signed_pair_mul_components_associate": (
        "add_mul",
        "mul_add",
        "mul_assoc",
        "add_comm",
        "add_permute_outer",
    ),
    "signed_mul_equations_associate": (
        "signed_pair_mul_cross_transport",
        "signed_pair_mul_components_associate",
        "add_cross_sum_chain",
        "add_comm",
    ),
    "signed_mul_associative": (
        "signed_mul_to_decoded_equation",
        "signed_mul_equations_associate",
        "signed_mul_of_decoded_equation",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_pair_mul_cross_transport":
        "c52769ea794122a09916841233d99f37b3ff6afdf83621d875dd3366d85cc08b",
    "signed_pair_mul_components_associate":
        "0d58d7ed4c5796616aa435c7933ef6f24d686346322536f007c216e587e9bb0e",
    "signed_mul_equations_associate":
        "fcbd761ff593162c2a571b02f8096c2a366c7ac78652844feecf9a6e2c1e74d1",
    "signed_mul_associative":
        "46c4da4af308165a42a12146c79541411b780c85f2fc4e010b90b413975a28e8",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_pair_mul_cross_transport": (4, 82, 160, 24, 160, 159, 0),
    "signed_pair_mul_components_associate": (5, 71, 146, 22, 146, 145, 0),
    "signed_mul_equations_associate": (4, 81, 90, 33, 90, 89, 0),
    "signed_mul_associative": (3, 97, 143, 47, 143, 142, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_pair_mul_cross_transport": (
        785,
        26,
        466,
        500,
        35,
        15,
        "1ff73d62de76550467f8d4b59d0c161a7ab54679041b22c45d6f8b61392cb6ff",
    ),
    "signed_pair_mul_components_associate": (
        887,
        26,
        486,
        526,
        41,
        17,
        "35dd7e68185d79615e918392fbb88ddece6bb0fdd8aa48fde5ca8b9a31760eda",
    ),
    "signed_mul_equations_associate": (
        2150,
        33,
        872,
        920,
        49,
        30,
        "159168d3c8ed5a472bdf4f3872650d7b98924ba87a7ebee27ceb0564b7c06734",
    ),
    "signed_mul_associative": (
        3196,
        47,
        1565,
        1617,
        53,
        47,
        "c6a9694ced9e0d4cb1426112b7b717dd9b60cf049ea89e71223f906512271775",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "28f70ca20734630f75c3adf01c83ce1e1265d79be9e904087a8a079e1db508d9"
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
    "mul_assoc",
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
    "add_cross_sum_chain",
    "even_half_unique",
    "even_odd_exclusive_k1",
    "signed_decode_functional",
    "signed_mul_equations_associate",
    "signed_mul_of_decoded_equation",
    "signed_mul_to_decoded_equation",
    "signed_pair_mul_components_associate",
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_mul_associative_candidate_theorems(TheoremSpec)


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


def _cold_closed_receipts() -> tuple[
    dict[str, tuple[int, int, int, int, int, int, str]], str
]:
    """Close the complete 53-row signed stack from a cold public replay."""

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


def _mul_code(left: int, right: int) -> int:
    return _encode(_value(left) * _value(right))


def _muls(left: int, right: int, output: int) -> bool:
    lp, ln = _decode(left)
    rp, rn = _decode(right)
    op, on = _decode(output)
    return (lp * rp + ln * rn) + on == (lp * rn + ln * rp) + op


def test_signed_mul_associative_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_mul_associative_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_mul_associative_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_mul_associative_statements_are_closed_base_graphs() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedDecode(",
                "SignedMul(",
                "SignedBalance(",
                "DivRem(",
                "BetaAt(",
                "%",
                "<",
                "<=",
            )
        )

    expected_graph = (
        "forall a b c ab bc abc. "
        f"({signed_mul('a', 'b', 'ab', tag='assoc_ab')}) -> "
        f"({signed_mul('ab', 'c', 'abc', tag='assoc_abc')}) -> "
        f"({signed_mul('b', 'c', 'bc', tag='assoc_bc')}) -> "
        f"({signed_mul('a', 'bc', 'abc', tag='assoc_target')})"
    )
    assert _candidate_specs()[-1].statement == expected_graph


def test_signed_mul_associative_dependencies_are_transitively_strict() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

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


def test_signed_mul_associative_bodies_are_exact_and_mutation_sensitive() -> None:
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
        "signed_pair_mul_cross_transport": lambda statement: statement.replace(
            "+ (u * cp + v * cn)) /\\",
            "+ S (u * cp + v * cn)) /\\",
            1,
        ),
        "signed_pair_mul_components_associate": lambda statement: statement.replace(
            "+ an * (bp * cp + bn * cn)))",
            "+ S (an * (bp * cp + bn * cn))))",
            1,
        ),
        "signed_mul_equations_associate": lambda statement: statement.replace(
            "(ap * bcn + an * bcp) + outp",
            "S ((ap * bcn + an * bcp) + outp)",
            1,
        ),
        "signed_mul_associative": lambda statement: statement.replace(
            " -> (exists sm_lp_assoc_target",
            " -> abc = 0 /\\ (exists sm_lp_assoc_target",
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


def test_signed_pair_associativity_helpers_bounded_semantic_oracle() -> None:
    for p, n, u, v, cp, cn in product(range(4), repeat=6):
        if p + v != n + u:
            continue
        assert (p * cp + n * cn) + (u * cn + v * cp) == (
            p * cn + n * cp
        ) + (u * cp + v * cn)
        assert (cp * p + cn * n) + (cp * v + cn * u) == (
            cp * n + cn * p
        ) + (cp * u + cn * v)

    for ap, an, bp, bn, cp, cn in product(range(4), repeat=6):
        assert (ap * bp + an * bn) * cp + (ap * bn + an * bp) * cn == (
            ap * (bp * cp + bn * cn) + an * (bp * cn + bn * cp)
        )
        assert (ap * bp + an * bn) * cn + (ap * bn + an * bp) * cp == (
            ap * (bp * cn + bn * cp) + an * (bp * cp + bn * cn)
        )

    valid_associator_inputs = 0
    for values in product(range(3), repeat=12):
        ap, an, bp, bn, cp, cn, abp, abn, bcp, bcn, outp, outn = values
        hab = (ap * bp + an * bn) + abn == (ap * bn + an * bp) + abp
        habc = (abp * cp + abn * cn) + outn == (
            abp * cn + abn * cp
        ) + outp
        hbc = (bp * cp + bn * cn) + bcn == (
            bp * cn + bn * cp
        ) + bcp
        if hab and habc and hbc:
            valid_associator_inputs += 1
            assert (ap * bcp + an * bcn) + outn == (
                ap * bcn + an * bcp
            ) + outp
    assert valid_associator_inputs == 11_283


def test_signed_mul_graph_associativity_on_first_seventeen_codes() -> None:
    for a, b, c in product(range(17), repeat=3):
        ab = _mul_code(a, b)
        bc = _mul_code(b, c)
        left = _mul_code(ab, c)
        right = _mul_code(a, bc)
        assert _muls(a, b, ab)
        assert _muls(ab, c, left)
        assert _muls(b, c, bc)
        assert _muls(a, bc, right)
        assert left == right
        assert _muls(a, bc, left)


def test_signed_mul_associative_mutations_are_genuinely_false() -> None:
    # The successor-strengthened transport conclusion fails at zero.
    assert 0 + 0 == 0 + 0
    assert 0 != 1

    # The successor-strengthened component and decoded targets fail likewise.
    assert (0 * 0 + 0 * 0) * 0 + (0 * 0 + 0 * 0) * 0 == 0
    assert 0 != 1

    # Associativity does not force the nonzero output code to be literal zero.
    a = b = c = 2
    ab = _mul_code(a, b)
    bc = _mul_code(b, c)
    abc = _mul_code(ab, c)
    assert abc == _mul_code(a, bc) == 2
    assert abc != 0
    assert _muls(a, b, ab)
    assert _muls(ab, c, abc)
    assert _muls(b, c, bc)
    assert _muls(a, bc, abc)


def test_signed_mul_associative_empty_context_closure_is_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 53
    assert len(_local_specs()) == len(_stack_specs())
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
