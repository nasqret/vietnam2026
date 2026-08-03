"""Strict-HA audit for the canonical signed-multiplication core candidates."""

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
from peano_lab.library.ha_signed_add_associative_candidate import (
    make_ha_signed_add_associative_candidate_theorems,
)
from peano_lab.library.ha_signed_add_candidate import (
    make_ha_signed_add_candidate_theorems,
)
from peano_lab.library.ha_signed_add_laws_candidate import (
    make_ha_signed_add_laws_candidate_theorems,
)
from peano_lab.library.ha_signed_mul_candidate import (
    make_ha_signed_mul_candidate_theorems,
    signed_mul,
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
    "signed_mul_of_decoded_equation",
    "signed_mul_to_decoded_equation",
    "signed_mul_decoded_iff_equation",
    "signed_mul_total",
    "signed_mul_functional",
)
EXPECTED_DEPENDENCIES = {
    "signed_mul_of_decoded_equation": (),
    "signed_mul_to_decoded_equation": ("signed_decode_functional",),
    "signed_mul_decoded_iff_equation": (
        "signed_mul_of_decoded_equation",
        "signed_mul_to_decoded_equation",
    ),
    "signed_mul_total": (
        "signed_decode_total",
        "signed_balance_total",
        "signed_mul_of_decoded_equation",
    ),
    "signed_mul_functional": (
        "signed_mul_to_decoded_equation",
        "signed_balance_functional",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_mul_of_decoded_equation":
        "e59f2ef5302c2d027a6411187b2068f097038ccbbacb4161681e416974376677",
    "signed_mul_to_decoded_equation":
        "ecbb03cddbeb270c58a41f63d65ff8581de8f37698e575e3dbe411215505df85",
    "signed_mul_decoded_iff_equation":
        "4b59be743142aa5fcc0d18df84450c37c53a28848f9d0e55570b9bc94032ab42",
    "signed_mul_total":
        "68ddcb2c4357f12cbedd89908414452a6a1b1684adcc6e2822a7ae1cfafcd3b7",
    "signed_mul_functional":
        "6493bb4d1759df101717a003411aaf38c80794559b9b4504987b96937f0c49eb",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_mul_of_decoded_equation": (0, 26, 26, 23, 26, 25, 0),
    "signed_mul_to_decoded_equation": (1, 63, 168, 39, 168, 167, 0),
    "signed_mul_decoded_iff_equation": (2, 43, 107, 39, 107, 106, 0),
    "signed_mul_total": (3, 35, 44, 27, 44, 43, 0),
    "signed_mul_functional": (2, 58, 81, 38, 81, 80, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_mul_of_decoded_equation": (
        26,
        23,
        26,
        25,
        0,
        0,
        "94c77cd7434e17a8fd103bb23ab06575443024062a47de838de02a54a6f215ed",
    ),
    "signed_mul_to_decoded_equation": (
        877,
        39,
        565,
        567,
        3,
        14,
        "d50b8c46989e457f406c4f1d22ec51e8bf3bddc9a6a34528c632114f7d7105c0",
    ),
    "signed_mul_decoded_iff_equation": (
        1010,
        41,
        698,
        700,
        3,
        16,
        "14adcb23ed89c2ca8a10947859e23ee6239715f19438a0ca7ae8a21ae917fd43",
    ),
    "signed_mul_total": (
        411,
        27,
        396,
        410,
        15,
        8,
        "85d12bb18f09de2679d060626067ae1e9d2d23beb54c7cc96498074ed2c10f46",
    ),
    "signed_mul_functional": (
        1808,
        40,
        1157,
        1190,
        34,
        34,
        "632bd740e1f6a5a00497205379dd64f3cdc3e45d75a33c8c02d46f727f05f410",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "2230cd2b67196ccec58ab5259052b08f9ef3f43275ef0b717fc35cf581cd0f6c"
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
    "signed_mul_of_decoded_equation",
    "signed_mul_to_decoded_equation",
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_mul_candidate_theorems(TheoremSpec)


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


def _mul_code(left: int, right: int) -> int:
    return _encode(_signed_value(left) * _signed_value(right))


def _muls(left: int, right: int, output: int) -> bool:
    lp, ln = _decode(left)
    rp, rn = _decode(right)
    op, on = _decode(output)
    return (lp * rp + ln * rn) + on == (lp * rn + ln * rp) + op


def test_signed_mul_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_mul_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_mul_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_mul_contract_is_hygienic_and_exact_rfc_d06() -> None:
    alpha_relation = signed_mul("left", "right", "output", tag="rfc_audit")
    assert parse_formula(
        f"forall left right output. ({alpha_relation})"
    ) == parse_formula(f"forall left right output. ({RFC_SIGNED_MUL})")
    assert sha256(RFC_SIGNED_MUL.encode()).hexdigest() == RFC_SIGNED_MUL_SHA256

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

    source = SIGNED_RFC_PATH.read_text(encoding="utf-8")
    assert "### 4.6 `SignedMul(left,right,output)`" in source
    assert f"```text\n{RFC_SIGNED_MUL}\n```" in source
    assert f"| `HA-K3-SIGNED-D06` | `{RFC_SIGNED_MUL_SHA256}` |" in source

    assert signed_mul("code", "code", "code", tag="same")
    with pytest.raises(ValueError):
        signed_mul("0", "right", "output", tag="bad")
    with pytest.raises(ValueError):
        signed_mul("left", "forall", "output", tag="bad")
    with pytest.raises(ValueError):
        signed_mul("left", "right", "sm_lp_capture", tag="capture")
    with pytest.raises(ValueError):
        signed_mul("sd_half_capture_left", "right", "output", tag="capture")
    with pytest.raises(ValueError):
        signed_mul("left", "right", "output", tag="bad-tag")


def test_signed_mul_dependencies_are_transitively_strict_ha() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    assert "even_odd_exclusive_pointwise" not in public_closure
    assert "division_remainder_unique" not in public_closure
    assert not any(name.startswith("signed_negate_") for name in local_closure)
    assert not any(name.startswith("signed_add_") for name in local_closure)
    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_signed_mul_bodies_are_exact_and_mutation_sensitive() -> None:
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
        "signed_mul_of_decoded_equation": lambda statement: statement.replace(
            " -> (exists sm_lp_intro",
            " -> output = left /\\ (exists sm_lp_intro",
            1,
        ),
        "signed_mul_to_decoded_equation": lambda statement: statement.replace(
            " -> (lp * rp + ln * rn) + on = (lp * rn + ln * rp) + op",
            " -> (lp * rp + ln * rn) + on = "
            "S ((lp * rn + ln * rp) + op)",
            1,
        ),
        "signed_mul_decoded_iff_equation": lambda statement: statement.replace(
            "((lp * rp + ln * rn) + on = "
            "(lp * rn + ln * rp) + op -> ",
            "((lp * rp + ln * rn) + on = "
            "S ((lp * rn + ln * rp) + op) -> ",
            1,
        ),
        "signed_mul_total": lambda statement: statement.replace(
            "exists output. (", "exists output. output = left /\\ (", 1
        ),
        "signed_mul_functional": lambda statement: statement.replace(
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


def test_signed_mul_bounded_semantic_oracle() -> None:
    assert _mul_code(0, 0) == 0
    assert _mul_code(2, 1) == 1
    assert _mul_code(2, 2) == 2
    assert _mul_code(1, 1) == 2
    assert _mul_code(4, 3) == 7

    for left in range(17):
        for right in range(17):
            output = _mul_code(left, right)
            matching = [
                candidate
                for candidate in range(129)
                if _muls(left, right, candidate)
            ]
            assert matching == [output]
            assert _muls(left, right, output)
            assert _mul_code(right, left) == output
            assert _signed_value(output) == (
                _signed_value(left) * _signed_value(right)
            )


def test_signed_mul_semantic_mutations_are_genuinely_false() -> None:
    # Requiring the output to equal the left input fails for +2 * +2.
    output = _mul_code(4, 4)
    assert output == 8
    assert output != 4
    assert _muls(4, 4, output)

    # The successor-shifted decoded equation holds for +1 * +1 with zero
    # output, but the genuine SignedMul equation does not.
    lp, ln = _decode(2)
    rp, rn = _decode(2)
    op, on = _decode(0)
    assert (lp * rp + ln * rn) + on == (
        (lp * rn + ln * rp) + op
    ) + 1
    assert not _muls(2, 2, 0)

    # Successor functionality is already false for the unique zero product.
    assert _mul_code(0, 0) == 0
    assert 0 != 0 + 1

    # Omitting the successor in the odd decoder creates a negative zero and
    # changes the selected result of -1 * +1.
    wrong_negative_one_value = 0 - (1 // 2)
    assert wrong_negative_one_value == 0
    assert _signed_value(1) == -1
    assert _mul_code(1, 2) == 1

    # Raw multiplication of parity codes is not signed multiplication:
    # code 1 times code 1 is naturally 1, but (-1)*(-1) has code 2.
    assert 1 * 1 == 1
    assert _mul_code(1, 1) == 2


def test_signed_mul_empty_context_closure_and_stack_are_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 44
    assert len(_local_specs()) == len(_stack_specs())
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
