"""Focused audit for strict D06 head/tail component descent."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_cell_bounds_candidate import (
    make_ha_cell_bounds_candidate_theorems,
)
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
    "pair_left_le_code",
    "pair_right_le_code",
    "cell_head_lt_code",
    "cell_tail_lt_code",
)
EXPECTED_DEPENDENCIES = {
    "pair_left_le_code": (
        "le_add_right",
        "pair_code_shell_lower",
        "le_trans",
    ),
    "pair_right_le_code": (
        "le_add_left",
        "pair_code_shell_lower",
        "le_trans",
    ),
    "cell_head_lt_code": ("pair_left_le_code", "succ_le_succ"),
    "cell_tail_lt_code": ("pair_right_le_code", "succ_le_succ"),
}
EXPECTED_STATEMENTS = {
    "pair_left_le_code": (
        "forall code left right. code = "
        "(left + right) * S (left + right) + (right + right) -> "
        "exists k. k + left = code"
    ),
    "pair_right_le_code": (
        "forall code left right. code = "
        "(left + right) * S (left + right) + (right + right) -> "
        "exists k. k + right = code"
    ),
    "cell_head_lt_code": (
        "forall code head tail. code = S "
        "((head + tail) * S (head + tail) + (tail + tail)) -> "
        "exists k. k + S head = code"
    ),
    "cell_tail_lt_code": (
        "forall code head tail. code = S "
        "((head + tail) * S (head + tail) + (tail + tail)) -> "
        "exists k. k + S tail = code"
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "pair_left_le_code":
        "7975a8493f202e62b6949199396f92fd52c10bf6dad0cf11c0b8a8a053966159",
    "pair_right_le_code":
        "592ea096f736bbeb757f57b16996b1f6209973b21ada4d1ec85d70ab3bae7f9d",
    "cell_head_lt_code":
        "01c14044a7045b619d91f547260f624b4fe2e5e59a49536ff4b1f32dcbb74e9d",
    "cell_tail_lt_code":
        "fa147a1b1ef5eba0840b7b6cee35f90a1990938b45956ae80a5cd7dbb0801640",
}
EXPECTED_BODY_RECEIPTS = {
    "pair_left_le_code": (3, 31, 35, 16, 35, 34, 0),
    "pair_right_le_code": (3, 31, 35, 16, 35, 34, 0),
    "cell_head_lt_code": (2, 13, 34, 20, 34, 33, 0),
    "cell_tail_lt_code": (2, 13, 34, 20, 34, 33, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "pair_left_le_code": (
        257, 18, 173, 184, 12, 8,
        "2216484e9a09321c065b6fbac742ff1763b28f799720fb4b729468cdeaa8ce3c",
    ),
    "pair_right_le_code": (
        181, 18, 170, 180, 11, 7,
        "48ae46ea34331fc1cdadc03a0e510681748aeade658cf1d9783ab6e7a6740601",
    ),
    "cell_head_lt_code": (
        304, 20, 220, 231, 12, 10,
        "4cbccb9c232ff1ee40d05a3ee0520e5a99beeeebb645f3e5142a5c40681d1d3d",
    ),
    "cell_tail_lt_code": (
        228, 20, 217, 227, 11, 9,
        "145f2c4c0c00c4b7145a6f847e90af1dd72e500b1d88b03e7ed4fdd267d2867b",
    ),
}
EXPECTED_PUBLIC_CLOSURE = {
    "add_assoc",
    "add_comm",
    "add_succ_left",
    "le_add_left",
    "le_add_right",
    "le_trans",
    "succ_le_succ",
    "zero_add",
}
EXPECTED_PRIVATE_CLOSURE = {"pair_code_shell_lower"}
EXPECTED_LOCAL_CLOSURE = {"pair_left_le_code", "pair_right_le_code"}
FORBIDDEN_MARKERS = (
    "beta",
    "classical",
    "crt",
    "division",
    "dne",
    "remainder",
)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_cell_bounds_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _private_specs() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in make_ha_pair_shell_candidate_theorems(TheoremSpec)
        if item.name == "pair_code_shell_lower"
    }


def _local_specs() -> dict[str, TheoremSpec]:
    return {item.name: item for item in _candidate_specs()}


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _private_specs() | _local_specs()


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
    available = _available_specs()
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


def _dependency_closure() -> tuple[set[str], set[str], set[str]]:
    public = _specs_by_name()
    private = _private_specs()
    local = _local_specs()
    pending = [dependency for item in _candidate_specs() for dependency in item.dependencies]
    public_seen: set[str] = set()
    private_seen: set[str] = set()
    local_seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in public_seen or name in private_seen or name in local_seen:
            continue
        if name in local:
            local_seen.add(name)
            pending.extend(local[name].dependencies)
        elif name in private:
            private_seen.add(name)
            pending.extend(private[name].dependencies)
        else:
            assert name in public, f"candidate dependency {name!r} is unavailable"
            public_seen.add(name)
            pending.extend(public[name].dependencies)
    return public_seen, private_seen, local_seen


def _cold_closed_receipts():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    public = _specs_by_name()
    local = _private_specs() | _local_specs()

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


def _pair_code(left: int, right: int) -> int:
    shell = left + right
    return shell * (shell + 1) + 2 * right


def test_cell_bounds_factory_is_exact_closed_and_registry_isolated() -> None:
    specs = _candidate_specs()
    assert make_ha_cell_bounds_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {item.name: item.statement for item in specs} == EXPECTED_STATEMENTS
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_bounds_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in specs)

    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "PairCode(",
                "Cell(",
                "DivRem(",
                "BetaAt(",
                "ModEq(",
                "%",
                "<",
                "<=",
            )
        )


def test_cell_bounds_dependency_closure_is_exact_and_constructive() -> None:
    public, private, local = _dependency_closure()
    assert public == EXPECTED_PUBLIC_CLOSURE
    assert private == EXPECTED_PRIVATE_CLOSURE
    assert local == EXPECTED_LOCAL_CLOSURE

    closure = {
        name: _available_specs()[name]
        for name in public | private | local | set(EXPECTED_NAMES)
    }
    for item in closure.values():
        payload = "\n".join(
            (item.name, item.statement, *item.dependencies, *item.script, item.summary)
        ).casefold()
        assert all(marker not in payload for marker in FORBIDDEN_MARKERS)


def test_cell_bounds_bodies_are_exact_and_mutation_sensitive() -> None:
    core = dict(_specs_by_name()) | _private_specs()
    receipts = replay_candidate_bodies(_candidate_specs(), core=core)
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
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in commands
    )
    assert all(
        marker not in command.casefold()
        for command in commands
        for marker in ("classical", "dne", "sorry")
    )

    mutations = {
        "pair_left_le_code": lambda statement: statement.replace(
            "k + left = code", "k + S left = code"
        ),
        "pair_right_le_code": lambda statement: statement.replace(
            "k + right = code", "k + S right = code"
        ),
        "cell_head_lt_code": lambda statement: statement.replace(
            "k + S head = code", "k + S (S head) = code"
        ),
        "cell_tail_lt_code": lambda statement: statement.replace(
            "k + S tail = code", "k + S (S tail) = code"
        ),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk_unique(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _candidate_target(item, mutated_statement))


def test_cell_bounds_empty_context_closure_is_twice_cold_and_within_limits() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()
    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first

    assert MAX_LIVE_PROOF_NODES == MAX_USE_CERTIFICATE_NODES == 500_000
    assert MAX_LIVE_PROOF_OBJECTS == MAX_USE_CERTIFICATE_OBJECTS == 100_000
    assert MAX_LIVE_PROOF_DEPTH == MAX_USE_PROOF_DEPTH == 256
    for nodes, depth, objects, _edges, _reused, _cuts, _digest in first.values():
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS
        assert depth <= MAX_USE_PROOF_DEPTH


def test_cell_bounds_bounded_oracle_and_boundary_mutations() -> None:
    for left, right in product(range(12), repeat=2):
        pair_code = _pair_code(left, right)
        cell_code = pair_code + 1

        assert left <= pair_code
        assert right <= pair_code
        assert (pair_code - left) + left == pair_code
        assert (pair_code - right) + right == pair_code

        assert left < cell_code
        assert right < cell_code
        assert (cell_code - left - 1) + (left + 1) == cell_code
        assert (cell_code - right - 1) + (right + 1) == cell_code

    # The successor tag is essential at the zero/zero boundary.
    assert _pair_code(0, 0) == 0
    assert not (0 < _pair_code(0, 0))
    assert 0 < _pair_code(0, 0) + 1

    # Strengthening either strict bound by one is false for the nil pair cell.
    zero_cell = _pair_code(0, 0) + 1
    assert not (0 + 1 < zero_cell)
