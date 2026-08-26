"""Strict-HA audit for the completed canonical signed-balance API."""

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
from peano_lab.library.ha_signed_balance_candidate import (
    make_ha_signed_balance_candidate_theorems,
    signed_balance,
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
    "signed_balance_extensional",
    "signed_balance_functional",
    "signed_balance_zero_iff",
)
EXPECTED_DEPENDENCIES = {
    "signed_balance_extensional": (
        "signed_balance_equations_cross_sum",
        "signed_decoded_balance_implies_code_eq",
    ),
    "signed_balance_functional": (
        "signed_balance_extensional",
        "add_comm",
    ),
    "signed_balance_zero_iff": (
        "signed_decode_functional",
        "signed_balance_functional",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "signed_balance_extensional":
        "adf834535e16e271a202db09e37655672956811c896ba057707305c4c093d1dc",
    "signed_balance_functional":
        "92ed87956adfc7bc5e403c390d03a96ea6fd5310d66b1352ef964c420a6264af",
    "signed_balance_zero_iff":
        "4884c5ea7e3c26aa4adf0e62946b02543bb7a1f0cf30c3b4ee6b6d473e5ce068",
}
EXPECTED_BODY_RECEIPTS = {
    "signed_balance_extensional": (2, 38, 50, 28, 50, 49, 0),
    "signed_balance_functional": (2, 16, 41, 24, 41, 40, 0),
    "signed_balance_zero_iff": (2, 52, 101, 24, 100, 100, 1),
}
EXPECTED_CLOSED_RECEIPTS = {
    "signed_balance_extensional": (
        736,
        33,
        531,
        557,
        27,
        16,
        "ba68aa6e0e09edabe56a5dcf5ff53de9488a596a01f2dfa6b59bfcd92c623c0d",
    ),
    "signed_balance_functional": (
        850,
        34,
        572,
        599,
        28,
        18,
        "900fbfc0c8139c56205a424d991eddda556374555ce08efeda3b6373ec0e00e0",
    ),
    "signed_balance_zero_iff": (
        1660,
        36,
        1008,
        1042,
        35,
        33,
        "d54bade5be975a27fc08a189ac552110ed8e85878137bc2e8e5268469c46b419",
    ),
}
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_comm",
    "add_eq_zero_left",
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
    "even_half_unique",
    "even_odd_exclusive_k1",
    "signed_balance_equations_cross_sum",
    "signed_balance_extensional",
    "signed_balance_functional",
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
RFC_SIGNED_BALANCE = (
    "exists pos neg. (((code = 2 * pos /\\ neg = 0) \\/ exists half. "
    "((code = 2 * half + 1 /\\ pos = 0) /\\ neg = S half)) /\\ "
    "left + neg = right + pos)"
)
RFC_SIGNED_BALANCE_SHA256 = (
    "8cf2a9b1678dfe5b774a01adf746df046b2056e1ae620c8b0de89c741b7e4997"
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_signed_balance_complete_candidate_theorems(TheoremSpec)


def _local_specs() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in (
            *_parity_specs(),
            *_decode_specs(),
            *_code_extensional_specs(),
            *_balance_seed_specs(),
            *_candidate_specs(),
        )
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


def _cold_closed_receipts() -> dict[
    str, tuple[int, int, int, int, int, int, str]
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


def _balance_code(left: int, right: int) -> int:
    if right <= left:
        return 2 * (left - right)
    return 2 * (right - left) - 1


def _balanced(code: int, left: int, right: int) -> bool:
    pos, neg = _decode(code)
    return left + neg == right + pos


def test_signed_balance_complete_factory_is_exact_and_registry_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_signed_balance_complete_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_signed_balance_complete_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_signed_balance_complete_contracts_are_hygienic_exact_rfc_d03() -> None:
    extensional_left = signed_balance(
        "code1", "left1", "right1", tag="ext_left"
    )
    extensional_right = signed_balance(
        "code2", "left2", "right2", tag="ext_right"
    )
    functional_left = signed_balance(
        "code1", "left", "right", tag="functional_left"
    )
    functional_right = signed_balance(
        "code2", "left", "right", tag="functional_right"
    )
    zero_balance = signed_balance("code", "left", "right", tag="zero")
    expected = (
        "forall code1 code2 left1 right1 left2 right2. "
        f"({extensional_left}) -> ({extensional_right}) -> "
        "left1 + right2 = right1 + left2 -> code1 = code2",
        "forall left right code1 code2. "
        f"({functional_left}) -> ({functional_right}) -> code1 = code2",
        f"forall code left right. ({zero_balance}) -> "
        "((code = 0 -> left = right) /\\ (left = right -> code = 0))",
    )
    assert tuple(item.statement for item in _candidate_specs()) == expected

    alpha_relation = signed_balance("code", "left", "right", tag="rfc_audit")
    assert parse_formula(
        f"forall code left right. ({alpha_relation})"
    ) == parse_formula(f"forall code left right. ({RFC_SIGNED_BALANCE})")
    assert sha256(RFC_SIGNED_BALANCE.encode()).hexdigest() == (
        RFC_SIGNED_BALANCE_SHA256
    )

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
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
    assert "### 4.3 `SignedBalance(code,left,right)`" in source
    assert f"```text\n{RFC_SIGNED_BALANCE}\n```" in source
    assert (
        f"| `HA-K3-SIGNED-D03` | `{RFC_SIGNED_BALANCE_SHA256}` |" in source
    )
    assert "- `signed_balance_functional`:" in source
    assert "- `signed_balance_extensional`:" in source
    assert "- `signed_balance_zero_iff`:" in source


def test_signed_balance_complete_dependencies_are_transitively_k1_only() -> None:
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


def test_signed_balance_complete_bodies_are_exact_and_mutation_sensitive() -> None:
    specs = _candidate_specs()
    core = dict(_specs_by_name()) | {
        item.name: item
        for item in (
            *_parity_specs(),
            *_decode_specs(),
            *_code_extensional_specs(),
            *_balance_seed_specs(),
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
        "signed_balance_extensional": lambda statement: statement.replace(
            " -> code1 = code2", " -> S code1 = code2", 1
        ),
        "signed_balance_functional": lambda statement: statement.replace(
            " -> code1 = code2", " -> S code1 = code2", 1
        ),
        "signed_balance_zero_iff": lambda statement: statement.replace(
            "code = 0 -> left = right",
            "code = 0 -> S left = right",
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


def test_signed_balance_complete_bounded_semantic_oracle() -> None:
    assert _balance_code(0, 0) == 0
    assert _balance_code(4, 1) == 6
    assert _balance_code(1, 4) == 5
    assert _balance_code(2, 2) == 0

    for left in range(13):
        for right in range(13):
            code = _balance_code(left, right)
            assert _balanced(code, left, right)
            assert (code == 0) == (left == right)
            matching = [
                candidate
                for candidate in range(49)
                if _balanced(candidate, left, right)
            ]
            assert matching == [code]

    for left1 in range(7):
        for right1 in range(7):
            code1 = _balance_code(left1, right1)
            for left2 in range(7):
                for right2 in range(7):
                    if left1 + right2 == right1 + left2:
                        assert _balance_code(left2, right2) == code1


def test_signed_balance_complete_semantic_mutations_are_genuinely_false() -> None:
    # Extensionality/functionality with a successor on the left code fails at
    # the zero balanced pair.
    assert _balanced(0, 0, 0)
    assert not (0 + 1 == 0)

    # The mutated forward half of zero-iff says S left = right.  Equality at
    # a nonzero diagonal pair is an explicit counterexample.
    code = _balance_code(3, 3)
    assert code == 0
    assert 3 == 3
    assert 3 + 1 != 3

    # Omitting the +1 in the negative constructor destroys the selected code.
    wrong_negative_code = 2 * (4 - 1)
    assert wrong_negative_code == 6
    assert _balance_code(1, 4) == 5
    assert not _balanced(wrong_negative_code, 1, 4)


def test_signed_balance_complete_empty_context_closure_is_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()

    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(name not in _specs_by_name() for name in EXPECTED_NAMES)
