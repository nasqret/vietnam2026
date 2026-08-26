"""Strict-HA audit for the elementary canonical signed-multiplication laws."""

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
from peano_lab.library import ha_signed_mul_laws_candidate as laws_module
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
from peano_lab.library.ha_signed_mul_candidate import (
    make_ha_signed_mul_candidate_theorems,
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
    "signed_mul_commutative",
    "signed_mul_zero_left",
    "signed_mul_zero_right",
    "signed_mul_one_left",
    "signed_mul_one_right",
)
EXPECTED_DEPENDENCIES = {
    "signed_mul_commutative": ("mul_comm", "add_comm"),
    "signed_mul_zero_left": (
        "signed_decode_total",
        "signed_mul_of_decoded_equation",
        "mul_zero_left",
    ),
    "signed_mul_zero_right": (
        "signed_mul_zero_left",
        "signed_mul_commutative",
    ),
    "signed_mul_one_left": (
        "signed_decode_total",
        "signed_mul_of_decoded_equation",
        "mul_one",
        "one_mul",
        "mul_zero_left",
        "add_comm",
    ),
    "signed_mul_one_right": (
        "signed_mul_one_left",
        "signed_mul_commutative",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_mul_commutative":
        "8e25f4cf6b48c125f7df426ee648ad9bae88fd6acc05257dde2afdffbeddd09c",
    "signed_mul_zero_left":
        "0b5d0d3aac940edbe0abe6eb750feb128870cb8d7aaf5c8d7ff1501556b712f6",
    "signed_mul_zero_right":
        "bcdea695be4d1c8d6102a1962ab9ede07e1ea7c79a31b7311702c5f02e0cce8c",
    "signed_mul_one_left":
        "c2a92014bb6e7752fe05c4c59071f12a4182a38e943893316eac10189cb12cc0",
    "signed_mul_one_right":
        "4739fd46ffd8ba093d92e56bccbe7fba593d5372c8b2a090f747785e6f862124",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_mul_commutative": (2, 42, 81, 41, 81, 80, 0),
    "signed_mul_zero_left": (3, 34, 57, 20, 56, 56, 1),
    "signed_mul_zero_right": (2, 7, 22, 13, 22, 21, 0),
    "signed_mul_one_left": (6, 43, 63, 23, 63, 62, 0),
    "signed_mul_one_right": (2, 7, 22, 13, 22, 21, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_mul_commutative": (
        376,
        41,
        281,
        303,
        23,
        8,
        "6bc3661f663bc26f85541485f1397b0b3da4dd4aee4f17e847deb53c49ff1ff6",
    ),
    "signed_mul_zero_left": (
        209,
        25,
        199,
        208,
        10,
        4,
        "78a9b2f876c73f601723e2ab21eb24f5bf0b2ce31a182cf9a5840eba33025153",
    ),
    "signed_mul_zero_right": (
        607,
        43,
        480,
        514,
        35,
        14,
        "30d11a08094266eee94edb5cee101f2fa1d80423b2754da61a69dead287c1174",
    ),
    "signed_mul_one_left": (
        347,
        25,
        307,
        330,
        24,
        10,
        "8d1406a347d46d83bd11baa5027088e4e761b1a740ba3f815632120eec8f2325",
    ),
    "signed_mul_one_right": (
        745,
        43,
        523,
        564,
        42,
        18,
        "fe3977029e00057909e7204631ce6f66b5ce2aff10a4132872ce011a899ef378",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "be074dfe1b79e3f27b2d48851c64f58360ee86fc3776ae681c451d38f67d25b2"
)
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_comm",
    "add_succ_left",
    "mul_comm",
    "mul_one",
    "mul_succ_left",
    "mul_zero_left",
    "one_mul",
    "parity_cases",
    "zero_add",
}
EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES = {
    "signed_decode_total",
    "signed_mul_commutative",
    "signed_mul_of_decoded_equation",
    "signed_mul_one_left",
    "signed_mul_zero_left",
}
FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
)
RFC_SIGNED_MUL = (
    "exists lp ln rp rn op on. (((left = 2 * lp /\\ ln = 0) \\/ "
    "exists left_half. ((left = 2 * left_half + 1 /\\ lp = 0) /\\ "
    "ln = S left_half)) /\\ (((right = 2 * rp /\\ rn = 0) \\/ "
    "exists right_half. ((right = 2 * right_half + 1 /\\ rp = 0) /\\ "
    "rn = S right_half)) /\\ (((output = 2 * op /\\ on = 0) \\/ "
    "exists output_half. ((output = 2 * output_half + 1 /\\ op = 0) /\\ "
    "on = S output_half)) /\\ (lp * rp + ln * rn) + on = "
    "(lp * rn + ln * rp) + op)))"
)
RFC_SIGNED_MUL_SHA256 = (
    "9b5a4a168cea119713e6892e590344fffd91c3abea6d349255edee0dcbe1af27"
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_mul_laws_candidate_theorems(TheoremSpec)


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


def _rfc_signed_mul_instance(left: str, right: str, output: str) -> str:
    return (
        "exists lp ln rp rn op on. "
        f"((({left} = 2 * lp /\\ ln = 0) \\/ exists left_half. "
        f"(({left} = 2 * left_half + 1 /\\ lp = 0) /\\ "
        "ln = S left_half)) /\\ "
        f"((({right} = 2 * rp /\\ rn = 0) \\/ exists right_half. "
        f"(({right} = 2 * right_half + 1 /\\ rp = 0) /\\ "
        "rn = S right_half)) /\\ "
        f"((({output} = 2 * op /\\ on = 0) \\/ exists output_half. "
        f"(({output} = 2 * output_half + 1 /\\ op = 0) /\\ "
        "on = S output_half)) /\\ "
        "(lp * rp + ln * rn) + on = (lp * rn + ln * rp) + op)))"
    )


def _decode(code: int) -> tuple[int, int]:
    return (code // 2, 0) if code % 2 == 0 else (0, code // 2 + 1)


def _signed_value(code: int) -> int:
    pos, neg = _decode(code)
    return pos - neg


def _encode(value: int) -> int:
    return 2 * value if value >= 0 else 2 * (-value) - 1


def _mul_code(left: int, right: int) -> int:
    return _encode(_signed_value(left) * _signed_value(right))


def _muls(left: int, right: int, output: int) -> bool:
    lp, ln = _decode(left)
    rp, rn = _decode(right)
    op, on = _decode(output)
    return (lp * rp + ln * rn) + on == (lp * rn + ln * rp) + op


def test_signed_mul_laws_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_mul_laws_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_mul_laws_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_mul_laws_are_base_language_and_rfc_d06_is_frozen() -> None:
    assert sha256(RFC_SIGNED_MUL.encode()).hexdigest() == RFC_SIGNED_MUL_SHA256
    source = SIGNED_RFC_PATH.read_text(encoding="utf-8")
    assert "### 4.6 `SignedMul(left,right,output)`" in source
    assert f"```text\n{RFC_SIGNED_MUL}\n```" in source
    assert f"| `HA-K3-SIGNED-D06` | `{RFC_SIGNED_MUL_SHA256}` |" in source

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


def test_literal_zero_one_expanders_are_hygienic_rfc_d06_instances() -> None:
    zero_left = laws_module._signed_mul_zero_left(
        "input", tag="audit_zero_left"
    )
    zero_right = laws_module._signed_mul_zero_right(
        "input", tag="audit_zero_right"
    )
    one_left = laws_module._signed_mul_one_left("input", tag="audit_one_left")
    one_right = laws_module._signed_mul_one_right(
        "input", tag="audit_one_right"
    )
    assert parse_formula(f"forall input. ({zero_left})") == parse_formula(
        f"forall input. ({_rfc_signed_mul_instance('0', 'input', '0')})"
    )
    assert parse_formula(f"forall input. ({zero_right})") == parse_formula(
        f"forall input. ({_rfc_signed_mul_instance('input', '0', '0')})"
    )
    assert parse_formula(f"forall input. ({one_left})") == parse_formula(
        f"forall input. ({_rfc_signed_mul_instance('2', 'input', 'input')})"
    )
    assert parse_formula(f"forall input. ({one_right})") == parse_formula(
        f"forall input. ({_rfc_signed_mul_instance('input', '2', 'input')})"
    )

    with pytest.raises(ValueError):
        laws_module._signed_mul_zero_left("0", tag="bad")
    with pytest.raises(ValueError):
        laws_module._signed_mul_zero_right("forall", tag="bad")
    with pytest.raises(ValueError):
        laws_module._signed_mul_one_left("sm_lp_capture", tag="capture")
    with pytest.raises(ValueError):
        laws_module._signed_mul_zero_left(
            "sd_half_capture_right", tag="capture"
        )
    with pytest.raises(ValueError):
        laws_module._signed_mul_one_left(
            "sd_half_capture_output", tag="capture"
        )
    with pytest.raises(ValueError):
        laws_module._signed_zero_decode(
            "sd_half_capture", "neg", tag="capture"
        )
    with pytest.raises(ValueError):
        laws_module._signed_one_decode(
            "pos", "sd_half_capture", tag="capture"
        )
    with pytest.raises(ValueError):
        laws_module._signed_mul_one_right("input", tag="bad-tag")


def test_signed_mul_laws_dependencies_are_transitively_strict_ha() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    assert "division_remainder_unique" not in public_closure
    assert not any(name.startswith("signed_add_") for name in local_closure)
    assert not any(name.startswith("signed_balance_") for name in local_closure)
    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_signed_mul_law_bodies_are_exact_and_mutation_sensitive() -> None:
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
            *_add_specs(),
            *_add_law_specs(),
            *_add_associative_specs(),
            *_mul_specs(),
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
        "signed_mul_commutative": lambda statement: statement.replace(
            " -> (exists sm_lp_comm_reverse",
            " -> left = right /\\ (exists sm_lp_comm_reverse",
            1,
        ),
        "signed_mul_zero_left": lambda statement: statement.replace(
            "forall input. (", "forall input. input = 0 /\\ (", 1
        ),
        "signed_mul_zero_right": lambda statement: statement.replace(
            "forall input. (", "forall input. input = 0 /\\ (", 1
        ),
        "signed_mul_one_left": lambda statement: statement.replace(
            "forall input. (", "forall input. input = 0 /\\ (", 1
        ),
        "signed_mul_one_right": lambda statement: statement.replace(
            "forall input. (", "forall input. input = 0 /\\ (", 1
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


def test_signed_mul_elementary_laws_bounded_semantic_oracle() -> None:
    for left in range(33):
        assert _mul_code(0, left) == 0
        assert _mul_code(left, 0) == 0
        assert _mul_code(2, left) == left
        assert _mul_code(left, 2) == left
        assert _muls(0, left, 0)
        assert _muls(left, 0, 0)
        assert _muls(2, left, left)
        assert _muls(left, 2, left)
        for right in range(33):
            output = _mul_code(left, right)
            assert output == _mul_code(right, left)
            assert _muls(left, right, output)
            assert _muls(right, left, output)


def test_signed_mul_law_mutations_are_genuinely_false() -> None:
    # Commutativity does not imply literal equality of the input codes.
    assert 2 != 0
    assert _mul_code(2, 0) == _mul_code(0, 2) == 0

    # Both annihilation laws hold at a nonzero input code.
    assert _mul_code(0, 2) == 0
    assert _mul_code(2, 0) == 0

    # Code 2, not raw numeral 1, is the canonical code for signed +1.
    assert _signed_value(2) == 1
    assert _signed_value(1) == -1
    assert _mul_code(2, 3) == 3
    assert _mul_code(3, 2) == 3
    assert _mul_code(1, 2) == 1
    assert _mul_code(2, 1) == 1

    # Raw multiplication of parity codes is not signed multiplication.
    assert 1 * 1 == 1
    assert _mul_code(1, 1) == 2


def test_signed_mul_laws_empty_context_closure_is_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 49
    assert len(_local_specs()) == len(_stack_specs())
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
