"""Strict-HA audit for the canonical signed-negation candidate tranche."""

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
    signed_negate,
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
    "signed_decode_swap_exists",
    "signed_negate_of_swapped_decode",
    "signed_negate_to_swapped_decode",
    "signed_negate_total",
    "signed_negate_functional",
    "signed_negate_zero",
    "signed_negate_symmetric",
    "signed_negate_involutive",
)
EXPECTED_DEPENDENCIES = {
    "signed_decode_swap_exists": ("zero_or_succ",),
    "signed_negate_of_swapped_decode": (),
    "signed_negate_to_swapped_decode": ("signed_decode_functional",),
    "signed_negate_total": (
        "signed_decode_total",
        "signed_decode_swap_exists",
        "signed_negate_of_swapped_decode",
    ),
    "signed_negate_functional": (
        "signed_negate_to_swapped_decode",
        "signed_decoded_balance_implies_code_eq",
        "add_comm",
    ),
    "signed_negate_zero": (),
    "signed_negate_symmetric": (),
    "signed_negate_involutive": (
        "signed_negate_symmetric",
        "signed_negate_functional",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_decode_swap_exists":
        "66a7c04b6554c293ee318f18c2dc88f1cfc58b35cf742acf072ae726946d999e",
    "signed_negate_of_swapped_decode":
        "0b58e851ecf158dad1e450b9493c0206bf5884f479d9c0837b5acca1bc288f07",
    "signed_negate_to_swapped_decode":
        "bb312c86dd5e6abece346e35d4e9e3f8163c59f39582d6af227460d293640608",
    "signed_negate_total":
        "53b646ca162886998385c937d599a75680f0fdbf960a0164516199f097c1bf06",
    "signed_negate_functional":
        "07b1b466ba524d943f95c39955c08ad9fc6e152123d8223b72af9208d67044ef",
    "signed_negate_zero":
        "fccdf1865ae3bff48d1a549b41afec8992e274c72d194197dc519832c63185dc",
    "signed_negate_symmetric":
        "c36d0368df382c028d5e78b63c0eb972a6f60ce6f01d0c730bb687f81950f3e6",
    "signed_negate_involutive":
        "f8fd0e6747c200b526941185c21a83ef6ae3790f104193f4b1ce91a6619f38ab",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_decode_swap_exists": (1, 33, 69, 21, 69, 68, 0),
    "signed_negate_of_swapped_decode": (0, 11, 11, 10, 11, 10, 0),
    "signed_negate_to_swapped_decode": (1, 24, 65, 22, 65, 64, 0),
    "signed_negate_total": (3, 19, 26, 15, 26, 25, 0),
    "signed_negate_functional": (3, 28, 37, 20, 37, 36, 0),
    "signed_negate_zero": (0, 13, 19, 9, 19, 18, 0),
    "signed_negate_symmetric": (0, 11, 20, 13, 20, 19, 0),
    "signed_negate_involutive": (2, 16, 19, 13, 19, 18, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_decode_swap_exists": (
        77,
        21,
        77,
        76,
        0,
        1,
        "77550f5f6828256036ddf632087f4ac53f1eb5814ebcbdc97388f5b8bb86cd0d",
    ),
    "signed_negate_of_swapped_decode": (
        11,
        10,
        11,
        10,
        0,
        0,
        "e06c193ec50fd071d95279763d09e0500aabc1abb0b8408bf14da10041785429",
    ),
    "signed_negate_to_swapped_decode": (
        774,
        28,
        462,
        464,
        3,
        14,
        "068786f8c3579d90250cceb732f0658be4517828adb8b274391488c75bcb5056",
    ),
    "signed_negate_total": (
        219,
        23,
        212,
        218,
        7,
        5,
        "fe693a95bba928c210c2186ec89a69ba8bfd01cd946f3741ea82f6bc291399cd",
    ),
    "signed_negate_functional": (
        1160,
        33,
        713,
        726,
        14,
        25,
        "43ba0ab3641498c1e87941e67bc07f3a67ae486356837fe3dd33a7ac3dfb2ac4",
    ),
    "signed_negate_zero": (
        19,
        9,
        19,
        18,
        0,
        0,
        "813a59731e04104d221ae984973d0eb2a71c6e77b1bff04605e1f09fd6b5286c",
    ),
    "signed_negate_symmetric": (
        20,
        13,
        20,
        19,
        0,
        0,
        "f911ecaee17a8a8359f6f5265c8992e9a86de1584c68fa8d27708f107af5336e",
    ),
    "signed_negate_involutive": (
        1199,
        35,
        752,
        765,
        14,
        27,
        "7aec997db1ea6393ff1192eea1b16a73b4a7424349b7670e1541fa34029c882b",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "89d806311b58860f130cabf862a17bd4e310710a9069b401b293609a0885ce3c"
)
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_comm",
    "add_eq_zero_left",
    "add_eq_zero_right",
    "add_right_cancel",
    "add_succ_left",
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
    "signed_decode_functional",
    "signed_decode_swap_exists",
    "signed_decode_total",
    "signed_decoded_balance_implies_code_eq",
    "signed_negate_functional",
    "signed_negate_of_swapped_decode",
    "signed_negate_symmetric",
    "signed_negate_to_swapped_decode",
}
FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
)
RFC_SIGNED_NEGATE = (
    "exists pos neg. (((input = 2 * pos /\\ neg = 0) \\/ exists input_half. "
    "((input = 2 * input_half + 1 /\\ pos = 0) /\\ neg = S input_half)) "
    "/\\ ((output = 2 * neg /\\ pos = 0) \\/ exists output_half. "
    "((output = 2 * output_half + 1 /\\ neg = 0) /\\ "
    "pos = S output_half)))"
)
RFC_SIGNED_NEGATE_SHA256 = (
    "67086486e367deed66d5dc66e2f7de5ec7aa280c542086aefd4be8e2330f1f11"
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_negate_candidate_theorems(TheoremSpec)


def _stack_specs() -> tuple[TheoremSpec, ...]:
    return (
        *_parity_specs(),
        *_decode_specs(),
        *_code_extensional_specs(),
        *_balance_seed_specs(),
        *_balance_complete_specs(),
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


def _negate_code(code: int) -> int:
    if code == 0:
        return 0
    return code - 1 if code % 2 == 0 else code + 1


def _negates(input_code: int, output_code: int) -> bool:
    pos, neg = _decode(input_code)
    return _decode(output_code) == (neg, pos)


def test_signed_negate_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_negate_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_negate_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_negate_contract_is_hygienic_and_exact_rfc_d04() -> None:
    alpha_relation = signed_negate("input", "output", tag="rfc_audit")
    assert parse_formula(
        f"forall input output. ({alpha_relation})"
    ) == parse_formula(f"forall input output. ({RFC_SIGNED_NEGATE})")
    assert sha256(RFC_SIGNED_NEGATE.encode()).hexdigest() == (
        RFC_SIGNED_NEGATE_SHA256
    )

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedDecode(",
                "SignedNegate(",
                "SignedBalance(",
                "DivRem(",
                "BetaAt(",
                "%",
                "<",
                "<=",
            )
        )

    source = SIGNED_RFC_PATH.read_text(encoding="utf-8")
    assert "### 4.4 `SignedNegate(input,output)`" in source
    assert f"```text\n{RFC_SIGNED_NEGATE}\n```" in source
    assert (
        f"| `HA-K3-SIGNED-D04` | `{RFC_SIGNED_NEGATE_SHA256}` |" in source
    )

    assert signed_negate("code", "code", tag="same")
    with pytest.raises(ValueError):
        signed_negate("0", "output", tag="bad")
    with pytest.raises(ValueError):
        signed_negate("input", "forall", tag="bad")
    with pytest.raises(ValueError):
        signed_negate("sn_pos_capture", "output", tag="capture")
    with pytest.raises(ValueError):
        signed_negate("sd_half_capture_input", "output", tag="capture")
    with pytest.raises(ValueError):
        signed_negate("input", "output", tag="bad-tag")


def test_signed_negate_dependencies_are_transitively_strict_ha() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    assert "even_odd_exclusive_pointwise" not in public_closure
    assert "division_remainder_unique" not in public_closure
    assert not any(name.startswith("signed_balance_") for name in local_closure)
    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_signed_negate_bodies_are_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    core = dict(_specs_by_name()) | {
        item.name: item
        for item in (
            *_parity_specs(),
            *_decode_specs(),
            *_code_extensional_specs(),
            *_balance_seed_specs(),
            *_balance_complete_specs(),
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
        "signed_decode_swap_exists": lambda statement: statement.replace(
            "exists output. (", "exists output. output = input /\\ (", 1
        ),
        "signed_negate_of_swapped_decode": lambda statement: statement.replace(
            " -> (exists sn_pos_intro", " -> output = input /\\ (exists sn_pos_intro", 1
        ),
        "signed_negate_to_swapped_decode": lambda statement: statement.replace(
            " -> ((output = 2 * neg", " -> output = input /\\ ((output = 2 * neg", 1
        ),
        "signed_negate_total": lambda statement: statement.replace(
            "exists output. (", "exists output. output = input /\\ (", 1
        ),
        "signed_negate_functional": lambda statement: statement.replace(
            " -> output1 = output2", " -> output1 = S output2", 1
        ),
        "signed_negate_zero": lambda statement: f"0 = 1 /\\ ({statement})",
        "signed_negate_symmetric": lambda statement: statement.replace(
            " -> (exists sn_pos_symmetric_reverse",
            " -> output = input /\\ (exists sn_pos_symmetric_reverse",
            1,
        ),
        "signed_negate_involutive": lambda statement: statement.replace(
            " -> output = input", " -> output = S input", 1
        ),
    }
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        parse_formula_with_names(mutated_statement)
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_signed_negate_bounded_semantic_oracle() -> None:
    assert [_negate_code(code) for code in range(5)] == [0, 2, 1, 4, 3]
    assert _negates(0, 0)
    assert _negates(1, 2)
    assert _negates(2, 1)

    for input_code in range(41):
        output_code = _negate_code(input_code)
        matching = [
            candidate for candidate in range(43) if _negates(input_code, candidate)
        ]
        assert matching == [output_code]
        assert _negates(input_code, output_code)
        assert _negates(output_code, input_code)
        assert _negate_code(output_code) == input_code

        pos, neg = _decode(input_code)
        assert _decode(output_code) == (neg, pos)


def test_signed_negate_semantic_mutations_are_genuinely_false() -> None:
    # Requiring the output to equal the input fails for either unit code.
    assert _negates(1, 2)
    assert not _negates(1, 1)
    assert _negates(2, 1)
    assert not _negates(2, 2)

    # A successor conclusion in functionality or involution already fails at zero.
    assert _negate_code(0) == 0
    assert 0 != 0 + 1

    # Omitting the successor magnitude creates a negative-zero decoding at code 1.
    wrong_odd_decode = (0, 1 // 2)
    assert wrong_odd_decode == (0, 0)
    assert _decode(1) == (0, 1)

    # Omitting the odd-code +1 maps the negation of +1 to zero, not -1.
    wrong_negative_one_code = 2 * 0
    assert wrong_negative_one_code == 0
    assert _negate_code(2) == 1
    assert not _negates(2, wrong_negative_one_code)


def test_signed_negate_empty_context_closure_and_stack_are_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 26
    assert len(_local_specs()) == len(_stack_specs())
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
