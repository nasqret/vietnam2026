"""Strict-HA audit for the canonical signed-natural scaling core."""

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
    "signed_nat_scale_of_decoded_equation",
    "signed_nat_scale_to_decoded_equation",
    "signed_nat_scale_decoded_iff_equation",
    "signed_nat_scale_total",
    "signed_nat_scale_functional",
)
EXPECTED_DEPENDENCIES = {
    "signed_nat_scale_of_decoded_equation": (),
    "signed_nat_scale_to_decoded_equation": ("signed_decode_functional",),
    "signed_nat_scale_decoded_iff_equation": (
        "signed_nat_scale_of_decoded_equation",
        "signed_nat_scale_to_decoded_equation",
    ),
    "signed_nat_scale_total": (
        "signed_decode_total",
        "signed_balance_total",
        "signed_nat_scale_of_decoded_equation",
    ),
    "signed_nat_scale_functional": (
        "signed_nat_scale_to_decoded_equation",
        "signed_balance_functional",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_nat_scale_of_decoded_equation":
        "fb0ecd88212759c2e4738f71f4f6510780752ba20b8e6d116dee148b5cf2a54d",
    "signed_nat_scale_to_decoded_equation":
        "2684b0acddfebe0c560bc445e3ea556dd68cd5c427f5a7de1f99f13270d993fc",
    "signed_nat_scale_decoded_iff_equation":
        "3776eec3c4043edda05b115c8d421cfe0e3d9d74b548818a1389efc6714d54f6",
    "signed_nat_scale_total":
        "fa60d2e36928200cc18353abb06120a4da204ea61d5ba06bd3b3133350d176d2",
    "signed_nat_scale_functional":
        "caf780f30a600411d0f11263f70abc9dc489bbed67dc67f86292f26a0d9e6ae9",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_nat_scale_of_decoded_equation": (0, 19, 19, 17, 19, 18, 0),
    "signed_nat_scale_to_decoded_equation": (1, 41, 76, 28, 76, 75, 0),
    "signed_nat_scale_decoded_iff_equation": (2, 34, 84, 31, 84, 83, 0),
    "signed_nat_scale_total": (3, 23, 71, 39, 71, 70, 0),
    "signed_nat_scale_functional": (2, 49, 63, 31, 63, 62, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_nat_scale_of_decoded_equation": (
        19,
        17,
        19,
        18,
        0,
        0,
        "348988d2b7802c5c319975a537c568f51b55b894890638b1465bc7c8617eb918",
    ),
    "signed_nat_scale_to_decoded_equation": (
        785,
        28,
        473,
        475,
        3,
        14,
        "66ef87988a3703a713a4ce0a16e235228df640be182c22d51d01f082ca5df1bd",
    ),
    "signed_nat_scale_decoded_iff_equation": (
        888,
        31,
        576,
        578,
        3,
        16,
        "1b96a56388461895781783b29c091b55a61f562b198a93c8c1a7449049ec1e6a",
    ),
    "signed_nat_scale_total": (
        431,
        39,
        416,
        430,
        15,
        8,
        "e1ee2921a7e967369bd70cd70564ef340ad643926c15c62dba394ae535e76947",
    ),
    "signed_nat_scale_functional": (
        1698,
        36,
        1047,
        1080,
        34,
        34,
        "59f948b0d2c8335cd3cd0098fb4acec9f895d8db2f930393d4dad33375ee2727",
    ),
}
EXPECTED_STACK_DAG_SHA256 = (
    "511aa0ba4a6dac1a22f52db740f539c675307b5b77b6b1a7d9ef2e00dd8a5331"
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
    "signed_balance_equations_cross_sum",
    "signed_balance_extensional",
    "signed_balance_functional",
    "signed_balance_total",
    "signed_decode_functional",
    "signed_decode_total",
    "signed_decoded_balance_implies_code_eq",
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
RFC_SIGNED_NAT_SCALE = (
    "exists ip inn op on. (((input = 2 * ip /\\ inn = 0) \\/ "
    "exists input_half. ((input = 2 * input_half + 1 /\\ ip = 0) /\\ "
    "inn = S input_half)) /\\ (((output = 2 * op /\\ on = 0) \\/ "
    "exists output_half. ((output = 2 * output_half + 1 /\\ op = 0) /\\ "
    "on = S output_half)) /\\ scale * ip + on = scale * inn + op))"
)
RFC_SIGNED_NAT_SCALE_SHA256 = (
    "ea3c130a4f8fe5f1a9d18cdbfbc5017175801db23d2e8ac66e6429fdfa1dfa6a"
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_nat_scale_candidate_theorems(TheoremSpec)


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
    """Close the complete 65-row signed stack from a cold public replay."""

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
    positive, negative = _decode(code)
    return positive - negative


def _encode(value: int) -> int:
    return 2 * value if value >= 0 else 2 * (-value) - 1


def _scale_code(scale: int, input_code: int) -> int:
    return _encode(scale * _value(input_code))


def _scales(scale: int, input_code: int, output_code: int) -> bool:
    ip, inn = _decode(input_code)
    op, on = _decode(output_code)
    return scale * ip + on == scale * inn + op


def test_signed_nat_scale_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_nat_scale_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_nat_scale_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_nat_scale_contract_is_hygienic_and_exact_rfc_d07() -> None:
    alpha_relation = signed_nat_scale(
        "scale", "input", "output", tag="rfc_audit"
    )
    assert parse_formula(
        f"forall scale input output. ({alpha_relation})"
    ) == parse_formula(
        f"forall scale input output. ({RFC_SIGNED_NAT_SCALE})"
    )
    assert (
        sha256(RFC_SIGNED_NAT_SCALE.encode()).hexdigest()
        == RFC_SIGNED_NAT_SCALE_SHA256
    )

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedDecode(",
                "SignedNatScale(",
                "SignedBalance(",
                "DivRem(",
                "BetaAt(",
                "%",
                "<",
                "<=",
            )
        )

    source = SIGNED_RFC_PATH.read_text(encoding="utf-8")
    assert "### 4.7 `SignedNatScale(scale,input,output)`" in source
    assert f"```text\n{RFC_SIGNED_NAT_SCALE}\n```" in source
    assert (
        f"| `HA-K3-SIGNED-D07` | `{RFC_SIGNED_NAT_SCALE_SHA256}` |"
        in source
    )

    assert signed_nat_scale("code", "code", "code", tag="same")
    with pytest.raises(ValueError):
        signed_nat_scale("0", "input", "output", tag="bad")
    with pytest.raises(ValueError):
        signed_nat_scale("scale", "forall", "output", tag="bad")
    with pytest.raises(ValueError):
        signed_nat_scale("scale", "input", "sns_ip_capture", tag="capture")
    with pytest.raises(ValueError):
        signed_nat_scale(
            "scale", "sd_half_capture_input", "output", tag="capture"
        )
    with pytest.raises(ValueError):
        signed_nat_scale("scale", "input", "output", tag="bad-tag")


def test_signed_nat_scale_dependencies_are_transitively_strict_ha() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    assert "even_odd_exclusive_pointwise" not in public_closure
    assert "division_remainder_unique" not in public_closure
    assert not any(name.startswith("signed_add_") for name in local_closure)
    assert not any(name.startswith("signed_mul_") for name in local_closure)
    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_signed_nat_scale_bodies_are_exact_and_mutation_sensitive() -> None:
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
        "signed_nat_scale_of_decoded_equation": lambda statement: statement.replace(
            " -> (exists sns_ip_intro",
            " -> output = input /\\ (exists sns_ip_intro",
            1,
        ),
        "signed_nat_scale_to_decoded_equation": lambda statement: statement.replace(
            " -> scale * ip + on = scale * inn + op",
            " -> scale * ip + on = S (scale * inn + op)",
            1,
        ),
        "signed_nat_scale_decoded_iff_equation": lambda statement: statement.replace(
            "((scale * ip + on = scale * inn + op -> ",
            "((scale * ip + on = S (scale * inn + op) -> ",
            1,
        ),
        "signed_nat_scale_total": lambda statement: statement.replace(
            "exists output. (", "exists output. output = input /\\ (", 1
        ),
        "signed_nat_scale_functional": lambda statement: statement.replace(
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


def test_signed_nat_scale_total_and_functional_on_bounded_domain() -> None:
    checked_pairs = 0
    for scale in range(17):
        for input_code in range(17):
            output = _scale_code(scale, input_code)
            matching = [
                candidate
                for candidate in range(257)
                if _scales(scale, input_code, candidate)
            ]
            assert matching == [output]
            assert _scales(scale, input_code, output)
            assert _value(output) == scale * _value(input_code)
            checked_pairs += 1
    assert checked_pairs == 17 * 17


def test_signed_nat_scale_pinned_fixtures_and_raw_code_trap() -> None:
    assert _scale_code(0, 16) == 0
    assert _scale_code(1, 1) == 1
    assert _scale_code(2, 1) == 3
    assert _scale_code(3, 2) == 6
    assert _scale_code(4, 3) == 15
    assert _scale_code(16, 16) == 256

    for scale, input_code, output in (
        (0, 16, 0),
        (1, 1, 1),
        (2, 1, 3),
        (3, 2, 6),
        (4, 3, 15),
        (16, 16, 256),
    ):
        assert _scales(scale, input_code, output)

    # Natural multiplication of the parity code is not signed scaling:
    # twice code 1 is naturally 2, while twice (-1) has code 3.
    assert 2 * 1 == 2
    assert _scale_code(2, 1) == 3


def test_signed_nat_scale_semantic_mutations_are_genuinely_false() -> None:
    # Requiring output=input contradicts scaling +1 by two.
    output = _scale_code(2, 2)
    assert output == 4
    assert output != 2
    assert _scales(2, 2, output)

    # A successor-shifted equation accepts zero as an alleged image of +1,
    # while the genuine scaling graph selects code 2.
    ip, inn = _decode(2)
    op, on = _decode(0)
    assert 1 * ip + on == (1 * inn + op) + 1
    assert not _scales(1, 2, 0)
    assert _scale_code(1, 2) == 2

    # Successor functionality fails already for the unique zero output.
    assert _scale_code(0, 7) == 0
    assert 0 != 0 + 1

    # Omitting the successor in the odd decoder would turn -1 into zero.
    wrong_negative_one_value = 0 - (1 // 2)
    assert wrong_negative_one_value == 0
    assert _value(1) == -1
    assert _scale_code(3, 1) == 5


def test_signed_nat_scale_empty_context_closure_is_deterministic() -> None:
    first_receipts, first_stack = _cold_closed_receipts()
    second_receipts, second_stack = _cold_closed_receipts()

    assert first_receipts == EXPECTED_CLOSED_RECEIPTS
    assert second_receipts == first_receipts
    assert first_stack == EXPECTED_STACK_DAG_SHA256
    assert second_stack == first_stack
    assert len(_stack_specs()) == 65
    assert len(_local_specs()) == len(_stack_specs())
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
