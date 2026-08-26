"""Strict-HA audit for the canonical signed-addition core candidates."""

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
from peano_lab.library.ha_signed_add_candidate import (
    make_ha_signed_add_candidate_theorems,
    signed_add,
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
    "signed_add_of_decoded_equation",
    "signed_add_to_decoded_equation",
    "signed_add_decoded_iff_equation",
    "signed_add_total",
    "signed_add_functional",
)
EXPECTED_DEPENDENCIES = {
    "signed_add_of_decoded_equation": (),
    "signed_add_to_decoded_equation": ("signed_decode_functional",),
    "signed_add_decoded_iff_equation": (
        "signed_add_of_decoded_equation",
        "signed_add_to_decoded_equation",
    ),
    "signed_add_total": (
        "signed_decode_total",
        "signed_balance_total",
        "signed_add_of_decoded_equation",
    ),
    "signed_add_functional": (
        "signed_add_to_decoded_equation",
        "signed_balance_functional",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_add_of_decoded_equation":
        "5dc9418496dca84f3818322391e6bdee0e82fa53949e9ed5d7d552ddeb4dcf16",
    "signed_add_to_decoded_equation":
        "c4e7a1b55f01ac1043f3bd4e7b1ddfb12e390b049c99449994b8f4de49a2f999",
    "signed_add_decoded_iff_equation":
        "5a8a65a37d5046a45a6be2026d023c2d749cdb22beb55ea561c97aa765736d3d",
    "signed_add_total":
        "a833317e218667421cc08336f1ad6a3575c29b6b52114437234900023bff1c64",
    "signed_add_functional":
        "09bcd858c7bddac1940bc48cbbccd32b26b83963408b8da3165f2b6a529b11a6",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_add_of_decoded_equation": (0, 26, 26, 23, 26, 25, 0),
    "signed_add_to_decoded_equation": (1, 59, 114, 35, 114, 113, 0),
    "signed_add_decoded_iff_equation": (2, 43, 107, 39, 107, 106, 0),
    "signed_add_total": (3, 35, 44, 27, 44, 43, 0),
    "signed_add_functional": (2, 58, 81, 38, 81, 80, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_add_of_decoded_equation": (
        26,
        23,
        26,
        25,
        0,
        0,
        "94c77cd7434e17a8fd103bb23ab06575443024062a47de838de02a54a6f215ed",
    ),
    "signed_add_to_decoded_equation": (
        823,
        35,
        511,
        513,
        3,
        14,
        "77bb73fbc7418d7b725b1c5c720b6b27417ce6e7d85dc4dc26186e31f07dc17c",
    ),
    "signed_add_decoded_iff_equation": (
        956,
        39,
        644,
        646,
        3,
        16,
        "376faba0f2bfbbe505f119864c5b590dcaa6d4eefb533d59ebf5756104e3e159",
    ),
    "signed_add_total": (
        411,
        27,
        396,
        410,
        15,
        8,
        "793ef15dc81c4f2fb2a359c2b62769993f2fe0da8bf953db0005c06b074eebd5",
    ),
    "signed_add_functional": (
        1754,
        38,
        1103,
        1136,
        34,
        34,
        "63eb78997ade1da36271de19138643f20e5e48666a1318d6a4982e616a6b9b87",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "11f41d395be9597892e2d5577ff80b54d04a61a57c81e50d02bc335c7e6012da"
)
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_comm",
    "add_eq_zero_left",
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
EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES = {
    "even_half_unique",
    "even_odd_exclusive_k1",
    "signed_add_of_decoded_equation",
    "signed_add_to_decoded_equation",
    "signed_balance_equations_cross_sum",
    "signed_balance_extensional",
    "signed_balance_functional",
    "signed_balance_total",
    "signed_decode_functional",
    "signed_decode_total",
    "signed_decoded_balance_implies_code_eq",
}
FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
)
RFC_SIGNED_ADD = (
    "exists lp ln rp rn op on. (((left = 2 * lp /\\ ln = 0) \\/ "
    "exists left_half. ((left = 2 * left_half + 1 /\\ lp = 0) /\\ "
    "ln = S left_half)) /\\ (((right = 2 * rp /\\ rn = 0) \\/ "
    "exists right_half. ((right = 2 * right_half + 1 /\\ rp = 0) /\\ "
    "rn = S right_half)) /\\ (((output = 2 * op /\\ on = 0) \\/ "
    "exists output_half. ((output = 2 * output_half + 1 /\\ op = 0) /\\ "
    "on = S output_half)) /\\ (lp + rp) + on = (ln + rn) + op)))"
)
RFC_SIGNED_ADD_SHA256 = (
    "29eaf592586c3bc9ec951b09b17d08c184284950f1997a3c109a048a8e610629"
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_add_candidate_theorems(TheoremSpec)


def _stack_specs() -> tuple[TheoremSpec, ...]:
    return (
        *_parity_specs(),
        *_decode_specs(),
        *_code_extensional_specs(),
        *_balance_seed_specs(),
        *_balance_complete_specs(),
        *_negate_specs(),
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
    """Close the complete signed stack from a cold public replay."""

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
    stack_digest = sha256("\n".join(stack_records).encode()).hexdigest()
    return receipts, stack_digest


def _decode(code: int) -> tuple[int, int]:
    return (code // 2, 0) if code % 2 == 0 else (0, code // 2 + 1)


def _signed_value(code: int) -> int:
    pos, neg = _decode(code)
    return pos - neg


def _encode(value: int) -> int:
    return 2 * value if value >= 0 else 2 * (-value) - 1


def _add_code(left: int, right: int) -> int:
    return _encode(_signed_value(left) + _signed_value(right))


def _adds(left: int, right: int, output: int) -> bool:
    lp, ln = _decode(left)
    rp, rn = _decode(right)
    op, on = _decode(output)
    return (lp + rp) + on == (ln + rn) + op


def test_signed_add_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_add_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_add_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_add_contract_is_hygienic_and_exact_rfc_d05() -> None:
    alpha_relation = signed_add("left", "right", "output", tag="rfc_audit")
    assert parse_formula(
        f"forall left right output. ({alpha_relation})"
    ) == parse_formula(f"forall left right output. ({RFC_SIGNED_ADD})")
    assert sha256(RFC_SIGNED_ADD.encode()).hexdigest() == RFC_SIGNED_ADD_SHA256

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedDecode(",
                "SignedAdd(",
                "SignedBalance(",
                "DivRem(",
                "BetaAt(",
                "%",
                "<",
                "<=",
            )
        )

    source = SIGNED_RFC_PATH.read_text(encoding="utf-8")
    assert "### 4.5 `SignedAdd(left,right,output)`" in source
    assert f"```text\n{RFC_SIGNED_ADD}\n```" in source
    assert f"| `HA-K3-SIGNED-D05` | `{RFC_SIGNED_ADD_SHA256}` |" in source

    assert signed_add("code", "code", "code", tag="same")
    with pytest.raises(ValueError):
        signed_add("0", "right", "output", tag="bad")
    with pytest.raises(ValueError):
        signed_add("left", "forall", "output", tag="bad")
    with pytest.raises(ValueError):
        signed_add("left", "right", "sa_lp_capture", tag="capture")
    with pytest.raises(ValueError):
        signed_add("sd_half_capture_left", "right", "output", tag="capture")
    with pytest.raises(ValueError):
        signed_add("left", "right", "output", tag="bad-tag")


def test_signed_add_dependencies_are_transitively_strict_ha() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    assert "even_odd_exclusive_pointwise" not in public_closure
    assert "division_remainder_unique" not in public_closure
    assert not any(name.startswith("signed_negate_") for name in local_closure)
    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_signed_add_bodies_are_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    core = dict(_specs_by_name()) | {
        item.name: item
        for item in (
            *_parity_specs(),
            *_decode_specs(),
            *_code_extensional_specs(),
            *_balance_seed_specs(),
            *_balance_complete_specs(),
            *_negate_specs(),
        )
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
        "signed_add_of_decoded_equation": lambda statement: statement.replace(
            " -> (exists sa_lp_intro",
            " -> output = left /\\ (exists sa_lp_intro",
            1,
        ),
        "signed_add_to_decoded_equation": lambda statement: statement.replace(
            " -> (lp + rp) + on = (ln + rn) + op",
            " -> (lp + rp) + on = S ((ln + rn) + op)",
            1,
        ),
        "signed_add_decoded_iff_equation": lambda statement: statement.replace(
            "((lp + rp) + on = (ln + rn) + op -> ",
            "((lp + rp) + on = S ((ln + rn) + op) -> ",
            1,
        ),
        "signed_add_total": lambda statement: statement.replace(
            "exists output. (", "exists output. output = left /\\ (", 1
        ),
        "signed_add_functional": lambda statement: statement.replace(
            " -> output1 = output2", " -> output1 = S output2", 1
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


def test_signed_add_bounded_semantic_oracle() -> None:
    assert _add_code(0, 0) == 0
    assert _add_code(2, 1) == 0
    assert _add_code(2, 2) == 4
    assert _add_code(1, 1) == 3
    assert _add_code(4, 3) == 0

    for left in range(17):
        for right in range(17):
            output = _add_code(left, right)
            matching = [
                candidate
                for candidate in range(65)
                if _adds(left, right, candidate)
            ]
            assert matching == [output]
            assert _adds(left, right, output)
            assert _add_code(right, left) == output
            assert _signed_value(output) == (
                _signed_value(left) + _signed_value(right)
            )


def test_signed_add_semantic_mutations_are_genuinely_false() -> None:
    # Requiring the output to equal the left input fails for +1 + +1.
    output = _add_code(2, 2)
    assert output == 4
    assert output != 2
    assert _adds(2, 2, output)

    # The successor-shifted decoded equation holds for +1 + 0 with zero
    # output, but the genuine SignedAdd equation does not.
    lp, ln = _decode(2)
    rp, rn = _decode(0)
    op, on = _decode(0)
    assert (lp + rp) + on == ((ln + rn) + op) + 1
    assert not _adds(2, 0, 0)

    # Successor functionality is already false for the unique zero sum.
    assert _add_code(0, 0) == 0
    assert 0 != 0 + 1

    # Omitting the successor in the odd decoder creates a negative zero and
    # changes the selected result of -1 + +1.
    wrong_negative_one_value = 0 - (1 // 2)
    assert wrong_negative_one_value == 0
    assert _signed_value(1) == -1
    assert _add_code(1, 2) == 0


def test_signed_add_empty_context_closure_and_stack_are_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 31
    assert len(_local_specs()) == len(_stack_specs())
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
