"""Focused audit for the independent ``HA-K3-PAIR-1`` shell layer."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_pair_shell_candidate import (
    make_ha_pair_shell_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "dt_shell_successor",
    "dt_shell_monotone",
    "dt_right_le_shell",
    "pair_code_shell_lower",
    "pair_code_below_next_shell",
    "pair_code_shell_separated",
)
EXPECTED_DEPENDENCIES = {
    "dt_shell_successor": ("mul_succ_left", "add_assoc", "add_comm"),
    "dt_shell_monotone": (
        "mul_le_mul_right",
        "succ_le_succ",
        "mul_le_mul_left",
        "le_trans",
    ),
    "dt_right_le_shell": (
        "le_add_left",
        "add_le_add_right",
        "add_le_add_left",
        "le_trans",
    ),
    "pair_code_shell_lower": ("add_comm",),
    "pair_code_below_next_shell": (
        "dt_right_le_shell",
        "add_le_add_left",
        "le_succ",
        "succ_le_succ",
        "dt_shell_successor",
    ),
    "pair_code_shell_separated": (
        "pair_code_below_next_shell",
        "dt_shell_monotone",
        "pair_code_shell_lower",
        "lt_of_lt_of_le",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "dt_shell_successor":
        "4de65f84b31ef5ded138a85e9f57db9763c363ec7364e04f8b3cc5e4858f4b03",
    "dt_shell_monotone":
        "64ebd7569b4923a6cd864404f8d4e4e727e9113b2125d5757e1b6718ceeb267b",
    "dt_right_le_shell":
        "add5fcbb6eaa853d8923f16ef0c5d81f248170eecf04533bef45583be8ba8dc5",
    "pair_code_shell_lower":
        "80e197c464b5241e57c4d15efdd3b07ca7b7d06467da1009566b0d8c51ddcad8",
    "pair_code_below_next_shell":
        "50e6bd0164dc1ce9cd0aef876c3a0a7ab75d78d29f6ec2b8a1a550107e21faa0",
    "pair_code_shell_separated":
        "53d7aacc96e356a2793f1f1174e34ba4f45cd9621c1489dc21224d304e6102ff",
}
EXPECTED_BODY_RECEIPTS = {
    "dt_shell_successor": (3, 2, 85, 24, 75, 84, 10),
    "dt_shell_monotone": (4, 26, 29, 14, 29, 28, 0),
    "dt_right_le_shell": (4, 24, 28, 13, 28, 27, 0),
    "pair_code_shell_lower": (1, 7, 12, 10, 12, 11, 0),
    "pair_code_below_next_shell": (5, 28, 32, 18, 32, 31, 0),
    "pair_code_shell_separated": (4, 39, 42, 22, 42, 41, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "dt_shell_successor": (
        363, 24, 228, 258, 31, 7,
        "52a39e68acc98d0c44c0b07c95f003eb6eff6ee8c4ca6e11adb9f9e275a03301",
    ),
    "dt_shell_monotone": (
        536, 27, 363, 395, 33, 16,
        "8fa6c58b51036c23d4bdfb6a3c58f8495d6d3ffb1a92cd14f82a5671327d210a",
    ),
    "dt_right_le_shell": (
        274, 19, 197, 209, 13, 10,
        "0db4ad7cc71c95435a1326d30e9ad67773da45eb1a94a553129ed6db3da71182",
    ),
    "pair_code_shell_lower": (
        85, 13, 79, 84, 6, 3,
        "ecec6b8a7ff41f1b28205a9f711ce7520e08511583c4d895257686d461214483",
    ),
    "pair_code_below_next_shell": (
        857, 29, 388, 424, 37, 21,
        "accbb0fc28dcdd8ccd9471ecf1142487ba751d4430907cc22995a59d5a9231d1",
    ),
    "pair_code_shell_separated": (
        1600, 30, 636, 692, 57, 38,
        "302d87068774ecbbe5bc6883ace27243e755627e6129d276938f31dd25dad72d",
    ),
}


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_pair_shell_candidate_theorems(TheoremSpec)


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


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


def _candidate_target(item: TheoremSpec, statement: str | None = None):
    available = dict(_specs_by_name()) | {
        candidate.name: candidate for candidate in _candidate_specs()
    }
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


def _body_certificate(item: TheoremSpec):
    target = _candidate_target(item)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _cold_closed_receipts():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    local = {item.name: item for item in _candidate_specs()}
    public = _specs_by_name()

    @lru_cache(maxsize=None)
    def close(name: str):
        if name in public:
            checked = replay(name)
            return checked.formula, checked.certificate

        item = local[name]
        formula = _closed_formula(item.statement)
        target = formula
        for dependency in reversed(item.dependencies):
            dependency_spec = local.get(dependency) or public[dependency]
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in item.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
        for _dependency in item.dependencies:
            assert type(body) is ImpIntro
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


def _shell(value: int) -> int:
    return value * (value + 1)


def _pair_code(left: int, right: int) -> int:
    return _shell(left + right) + 2 * right


def test_pair_shell_factory_is_exact_isolated_and_native() -> None:
    specs = _candidate_specs()
    second = make_ha_pair_shell_candidate_theorems(TheoremSpec)
    assert second == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    assert not hasattr(theorem_registry, "HA_PAIR_SHELL_THEOREMS")
    registry_source = Path(theorem_registry.__file__).read_text()
    assert "ha_pair_shell_candidate" not in registry_source
    assert all(item.name not in registry_source for item in specs)

    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "PairCode(", "BetaAt(", "DivRem(", "CRT(", "%", "<=>"
            )
        )

    local = {item.name: item for item in specs}
    pending = list(local)
    closure: dict[str, TheoremSpec] = {}
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        item = local.get(name) or public[name]
        closure[name] = item
        pending.extend(item.dependencies)
    assert set(closure) == {
        "add_assoc",
        "add_comm",
        "add_le_add_left",
        "add_le_add_right",
        "add_mul",
        "add_succ_left",
        "dt_right_le_shell",
        "dt_shell_monotone",
        "dt_shell_successor",
        "le_add_left",
        "le_succ",
        "le_trans",
        "lt_of_lt_of_le",
        "mul_add",
        "mul_comm",
        "mul_le_mul_left",
        "mul_le_mul_right",
        "mul_succ_left",
        "mul_zero_left",
        "pair_code_below_next_shell",
        "pair_code_shell_lower",
        "pair_code_shell_separated",
        "succ_le_succ",
        "zero_add",
    }
    forbidden_fragments = (
        "beta",
        "crt",
        "division",
        "remainder",
        "prime",
        "factorial",
        "classical",
        "by_contra",
        "sorry",
    )
    for item in closure.values():
        payload = "\n".join(
            (
                item.name,
                item.statement,
                " ".join(item.dependencies),
                "\n".join(item.script),
                item.summary,
            )
        ).casefold()
        assert all(fragment not in payload for fragment in forbidden_fragments)
        assert "DNE" not in item.statement
        assert all("DNE" not in command for command in item.script)


def test_pair_shell_bodies_are_constructive_and_mutation_sensitive() -> None:
    receipts = replay_candidate_bodies(_candidate_specs())
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

    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "use"}
        for command in commands
    )
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "classical", "by_contra", "sorry")
    )

    mutations = {
        "dt_shell_successor": lambda statement: statement.replace(
            "S (S (s * S s + (s + s)))",
            "S (S (S (s * S s + (s + s))))",
        ),
        "dt_shell_monotone": lambda statement: statement.replace(
            "= t * S t", "= S (t * S t)"
        ),
        "dt_right_le_shell": lambda statement: statement.replace(
            "= (left + right) + (left + right)",
            "= S ((left + right) + (left + right))",
        ),
        "pair_code_shell_lower": lambda statement: statement.replace(
            "= code", "= S code"
        ),
        "pair_code_below_next_shell": lambda statement: statement.replace(
            "= S (left + right) * S (S (left + right))",
            "= S (S (left + right) * S (S (left + right)))",
        ),
        "pair_code_shell_separated": lambda statement: statement.replace(
            "= c2", "= S c2"
        ),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _candidate_target(item, mutated_statement))


def test_pair_shell_empty_context_closures_are_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()
    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first


def test_pair_shell_bounded_semantics_and_boundary_mutations() -> None:
    for shell in range(10):
        assert _shell(shell + 1) == _shell(shell) + 2 * shell + 2
    for left, right in product(range(9), repeat=2):
        shell = left + right
        code = _pair_code(left, right)
        assert 2 * right <= 2 * shell
        assert _shell(shell) <= code < _shell(shell + 1)

    for left1, right1, left2, right2 in product(range(5), repeat=4):
        shell1 = left1 + right1
        shell2 = left2 + right2
        if shell1 < shell2:
            assert _pair_code(left1, right1) < _pair_code(left2, right2)

    # Nearby strengthened or weakened boundaries are genuinely false.
    assert _pair_code(0, 2) > _shell(2)
    assert not (_pair_code(0, 2) < _shell(2))
    assert not (_pair_code(0, 1) < _pair_code(1, 0))  # same shell
