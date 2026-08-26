"""Strict-HA audit for canonical signed-code extensionality candidates."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_signed_code_extensional_candidate import (
    make_ha_signed_code_extensional_candidate_theorems,
)
from peano_lab.library.ha_signed_decode_candidate import (
    make_ha_signed_decode_candidate_theorems,
    signed_decode,
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
    "signed_decoded_balance_implies_code_eq",
    "signed_code_eq_implies_decoded_balance",
    "signed_code_eq_iff_balance",
)
EXPECTED_DEPENDENCIES = {
    "signed_decoded_balance_implies_code_eq": (
        "zero_add",
        "add_eq_zero_right",
        "add_eq_zero_left",
        "succ_ne_zero",
    ),
    "signed_code_eq_implies_decoded_balance": (
        "signed_decode_functional",
        "add_comm",
    ),
    "signed_code_eq_iff_balance": (
        "signed_decoded_balance_implies_code_eq",
        "signed_code_eq_implies_decoded_balance",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_decoded_balance_implies_code_eq":
        "bde0836138fa710f268ca0c771632932401bf55f4ece5fadef45df1f8350e8c4",
    "signed_code_eq_implies_decoded_balance":
        "9342f422ac0c8390c496ae7dd8cb81d95fb59c9c3539b4ffc312eb4134b13041",
    "signed_code_eq_iff_balance":
        "00c880f6aae1f6a4e01b76ff0339ebc112eda50c623080baa39fa00375d99fdd",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_decoded_balance_implies_code_eq": (4, 81, 127, 31, 127, 126, 0),
    "signed_code_eq_implies_decoded_balance": (2, 24, 48, 23, 48, 47, 0),
    "signed_code_eq_iff_balance": (2, 31, 75, 28, 75, 74, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_decoded_balance_implies_code_eq": (
        276,
        31,
        234,
        241,
        8,
        8,
        "61adea012248c208a24466c2cd21d3f72bbbb8737737931b8089d4f94664c1dc",
    ),
    "signed_code_eq_implies_decoded_balance": (
        830,
        28,
        512,
        520,
        9,
        17,
        "8799714212e5480e0b4fc8940f63e308115c94dd8db56fc6c5f9d3eef632aaa7",
    ),
    "signed_code_eq_iff_balance": (
        1181,
        32,
        734,
        747,
        14,
        25,
        "26dbecbb46fef4d1eda7a208dbdce26f924aabde0a4317092821b8a3f2833728",
    ),
}
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
    "succ_ne_zero",
    "zero_add",
    "zero_or_succ",
}
EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES = {
    "even_half_unique",
    "even_odd_exclusive_k1",
    "signed_code_eq_implies_decoded_balance",
    "signed_decode_functional",
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_code_extensional_candidate_theorems(TheoremSpec)


def _local_specs() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in (*_parity_specs(), *_decode_specs(), *_candidate_specs())
    }


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


def _cold_closed_receipts() -> dict[str, tuple[int, int, int, int, int, int, str]]:
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

    receipts = {}
    for item in _candidate_specs():
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        assert check((), certificate, formula)
        unique_nodes = tuple(_walk_unique(certificate))
        assert not any(type(node) is DNE for node in unique_nodes)
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
            _proof_dag_digest(certificate),
        )
    return receipts


def _decode(code: int) -> tuple[int, int]:
    return (code // 2, 0) if code % 2 == 0 else (0, code // 2 + 1)


def test_signed_code_extensional_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_code_extensional_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_code_extensional_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_code_extensional_contracts_are_hygienic_exact_rfc_formulas() -> None:
    left = signed_decode("code1", "pos1", "neg1", tag="extensional_left")
    right = signed_decode("code2", "pos2", "neg2", tag="extensional_right")
    prefix = (
        "forall code1 pos1 neg1 code2 pos2 neg2. "
        f"({left}) -> ({right}) -> "
    )
    balance = "pos1 + neg2 = neg1 + pos2"
    expected = (
        f"{prefix}{balance} -> code1 = code2",
        f"{prefix}code1 = code2 -> {balance}",
        f"{prefix}(({balance} -> code1 = code2) /\\ "
        f"(code1 = code2 -> {balance}))",
    )
    assert tuple(item.statement for item in _candidate_specs()) == expected

    alpha_left = signed_decode("code1", "pos1", "neg1", tag="audit_left")
    alpha_right = signed_decode("code2", "pos2", "neg2", tag="audit_right")
    alpha_prefix = (
        "forall code1 pos1 neg1 code2 pos2 neg2. "
        f"({alpha_left}) -> ({alpha_right}) -> "
    )
    alpha_expected = (
        f"{alpha_prefix}{balance} -> code1 = code2",
        f"{alpha_prefix}code1 = code2 -> {balance}",
        f"{alpha_prefix}(({balance} -> code1 = code2) /\\ "
        f"(code1 = code2 -> {balance}))",
    )
    for item, alpha_statement in zip(_candidate_specs(), alpha_expected, strict=True):
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert formula == parse_formula(alpha_statement)
        assert all(
            token not in item.statement
            for token in (
                "SignedDecode(",
                "SignedBalance(",
                "DivRem(",
                "BetaAt(",
                "%",
                "<",
                "<=",
            )
        )

    source = SIGNED_RFC_PATH.read_text(encoding="utf-8")
    assert "### 6.2 Decoder obligations" in source
    assert (
        "8. `signed_code_eq_iff_balance`: for decoded `x` and `y`, literal code\n"
        "   equality is equivalent to `xp + yn = xn + yp`;"
    ) in source
    assert (
        "The biconditionals above must be stored as a conjunction of the two\n"
        "intuitionistically valid implications"
    ) in source


def test_signed_code_extensional_dependencies_are_transitively_k1_only() -> None:
    public = _specs_by_name()
    local = _local_specs()
    public_closure, local_closure = _dependency_closure()

    assert public_closure == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    assert local_closure == EXPECTED_TRANSITIVE_CANDIDATE_DEPENDENCIES
    assert "even_odd_exclusive_pointwise" not in public_closure
    assert "division_remainder_unique" not in public_closure
    for name in public_closure | local_closure:
        item = public.get(name) or local[name]
        audit_text = "\n".join(
            (name, item.statement, *item.dependencies, *item.script, item.summary)
        ).lower()
        assert all(marker not in audit_text for marker in FORBIDDEN_DEPENDENCY_MARKERS)


def test_signed_code_extensional_bodies_are_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    core = dict(_specs_by_name()) | {
        item.name: item for item in (*_parity_specs(), *_decode_specs())
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
        "signed_decoded_balance_implies_code_eq": lambda statement: statement.replace(
            " -> code1 = code2", " -> S code1 = code2", 1
        ),
        "signed_code_eq_implies_decoded_balance": lambda statement: statement.replace(
            " -> pos1 + neg2 = neg1 + pos2",
            " -> S (pos1 + neg2) = neg1 + pos2",
            1,
        ),
        "signed_code_eq_iff_balance": lambda statement: statement.replace(
            " -> code1 = code2) /\\",
            " -> S code1 = code2) /\\",
            1,
        ),
    }
    for item in specs:
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_signed_code_extensional_bounded_semantic_oracle() -> None:
    for code1 in range(25):
        pos1, neg1 = _decode(code1)
        for code2 in range(25):
            pos2, neg2 = _decode(code2)
            balance = pos1 + neg2 == neg1 + pos2
            assert balance == (code1 == code2)

    assert _decode(0) == (0, 0)
    assert _decode(1) == (0, 1)
    assert _decode(2) == (1, 0)
    assert _decode(3) == (0, 2)


def test_signed_code_extensional_semantic_mutations_are_detected() -> None:
    def wrong_balance(code1: int, code2: int) -> bool:
        pos1, neg1 = _decode(code1)
        pos2, neg2 = _decode(code2)
        return pos1 + pos2 == neg1 + neg2

    assert wrong_balance(2, 1)
    assert 2 != 1

    def shifted_negative_decode(code: int) -> tuple[int, int]:
        return (code // 2, 0) if code % 2 == 0 else (0, code // 2)

    assert shifted_negative_decode(1) == (0, 0)
    assert _decode(1) == (0, 1)
    zero_pos, zero_neg = _decode(0)
    bad_pos, bad_neg = shifted_negative_decode(1)
    assert zero_pos + bad_neg == zero_neg + bad_pos
    assert 0 != 1


def test_signed_code_extensional_empty_context_closure_is_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()

    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
