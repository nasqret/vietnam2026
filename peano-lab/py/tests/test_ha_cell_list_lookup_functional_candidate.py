"""Focused body audit for private K3B ``list_at_functional``.

Only the dependency-curried induction body is replayed.  This test performs
no recursive closure, admission, WMI replay, or campaign-wide validation.
"""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    Eq,
    Forall,
    Formula,
    Imp,
    parse_formula,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.kernel.terms import Term
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_cell_functional_candidate import (
    make_ha_cell_functional_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_functional_candidate import (
    make_ha_cell_list_lookup_functional_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_head_candidate import (
    make_ha_cell_list_lookup_head_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_succ_candidate import (
    make_ha_cell_list_lookup_succ_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _primitive


EXPECTED_NAME = "list_at_functional"
EXPECTED_DEPENDENCIES = (
    "list_at_head_iff",
    "list_at_succ_iff",
    "cell_functional",
)
EXPECTED_STATEMENT_RECEIPT = (
    8_895,
    "1eba38bb47901319d41e681ed77f218b437e4d2ff1d55f519fff82e7dc8f2361",
)
EXPECTED_AST_RECEIPT = (429, 115)
EXPECTED_BODY_RECEIPT = (3, 95, 119, 40, 119, 118, 0)


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (item,) = make_ha_cell_list_lookup_functional_candidate_theorems(
        TheoremSpec
    )
    return item


@lru_cache(maxsize=1)
def _available_specs() -> dict[str, TheoremSpec]:
    specs = (
        make_ha_cell_list_lookup_head_candidate_theorems(TheoremSpec)
        + make_ha_cell_list_lookup_succ_candidate_theorems(TheoremSpec)
        + make_ha_cell_functional_candidate_theorems(TheoremSpec)
    )
    available = {item.name: item for item in specs}
    return {name: available[name] for name in EXPECTED_DEPENDENCIES}


def _candidate_target(statement: str | None = None):
    item = _candidate_spec()
    target = _closed_formula(item.statement if statement is None else statement)
    available = _available_specs()
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    return target


def _body_certificate() -> tuple[Proof, object]:
    item = _candidate_spec()
    target = _candidate_target()
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _walk_pa_ast(node: Formula | Term):
    yield node
    for item in fields(node):
        child = getattr(node, item.name)
        if isinstance(child, (Formula, Term)):
            yield from _walk_pa_ast(child)


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_unique_proof(proof: Proof):
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


def _beta(code: int, scale: int, index: int, value: int) -> bool:
    modulus = 1 + (index + 1) * scale
    return value < modulus and code % modulus == value


def _cell(head: int, tail: int) -> int:
    shell = head + tail
    return 1 + shell * (shell + 1) + 2 * tail


def _history(values: tuple[int, ...], code: int, scale: int) -> bool:
    return (
        values[0] == 0
        and _beta(code, scale, 0, 0)
        and _beta(code, scale, len(values) - 1, values[-1])
        and all(
            any(
                values[index + 1] == _cell(head, values[index])
                for head in range(values[index + 1] + 1)
            )
            for index in range(len(values) - 1)
        )
    )


def _lookup(
    values: tuple[int, ...],
    code: int,
    scale: int,
    outer_index: int,
    value: int,
) -> bool:
    length = len(values) - 1
    return _history(values, code, scale) and any(
        edge + outer_index + 1 == length
        and _beta(code, scale, edge, values[edge])
        and _beta(code, scale, edge + 1, values[edge + 1])
        and values[edge + 1] == _cell(value, values[edge])
        for edge in range(length)
    )


def _successor_lookup(
    code: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    placeholder = f"functional_test_successor_{tag}"
    expanded = cell_list_at(code, placeholder, value, tag=tag)
    assert expanded.count(placeholder) > 0
    return expanded.replace(placeholder, f"S {index}")


def test_list_at_functional_surface_is_exact_closed_and_private() -> None:
    item = _candidate_spec()
    left = cell_list_at("z", "i", "a", tag="functional_target_left")
    right = cell_list_at("z", "i", "d", tag="functional_target_right")
    expected = (
        "forall z i a d. "
        f"({left}) -> ({right}) -> a = d"
    )

    assert make_ha_cell_list_lookup_functional_candidate_theorems(
        TheoremSpec
    ) == (item,)
    assert item.name == EXPECTED_NAME
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert item.statement == expected
    assert (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
    ) == EXPECTED_STATEMENT_RECEIPT

    formula, free_names = parse_formula_with_names(item.statement)
    assert not free_names
    assert formula == parse_formula(item.statement) == _closed_formula(
        item.statement
    )
    nodes = tuple(_walk_pa_ast(formula))
    assert (
        len(nodes),
        sum(isinstance(node, Formula) for node in nodes),
    ) == EXPECTED_AST_RECEIPT

    body = formula
    for _ in range(4):
        assert isinstance(body, Forall)
        body = body.body
    assert isinstance(body, Imp)
    assert isinstance(body.right, Imp)
    assert isinstance(body.right.right, Eq)

    assert item.statement.count("a = d") == 1
    assert "d = a" not in item.statement
    for tag in ("functional_target_left", "functional_target_right"):
        equation = f"hclook_edge_{tag} + S i = hclook_length_{tag}"
        assert item.statement.count(equation) == 1
    assert all(
        token not in item.statement
        for token in (
            "BetaAt(",
            "Cell(",
            "CellHistory(",
            "CellListLen(",
            "ListAt(",
            "<->",
            "%",
        )
    )

    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_list_lookup_functional_candidate" not in registry_source
    assert f'"{item.name}"' not in registry_source


def test_list_at_functional_body_is_pinned_inductive_and_sensitive() -> None:
    item = _candidate_spec()
    (receipt,) = replay_candidate_bodies((item,), core=_available_specs())
    assert (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    ) == EXPECTED_BODY_RECEIPT

    certificate, target = _body_certificate()
    assert check((), certificate, target)
    assert not any(type(node) is DNE for node in _walk_unique_proof(certificate))
    assert item.script.count("induction i") == 1
    assert item.script.count("apply cell_functional") == 2
    assert "apply IH" in item.script
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in item.script
    )
    payload = "\n".join((item.statement, *item.dependencies, *item.script)).casefold()
    assert all(
        marker not in payload
        for marker in ("classical", "dne", "excluded_middle", "sorry")
    )
    assert set(item.dependencies).isdisjoint(
        {
            "add_comm",
            "beta_at_unique",
            "list_at_domain",
            "list_at_external_bound",
            "list_at_exists",
            "cell_list_length_functional",
        }
    )

    right = cell_list_at("z", "i", "d", tag="functional_target_right")
    disconnected = item.statement.replace(
        right,
        cell_list_at("z", "i", "a", tag="functional_target_right"),
    )
    assert disconnected != item.statement
    assert not check((), certificate, _candidate_target(disconnected))

    shifted = item.statement.replace(
        right,
        _successor_lookup("z", "i", "d", tag="functional_target_right"),
    )
    assert shifted != item.statement
    assert not check((), certificate, _candidate_target(shifted))

    fixed_value = item.statement.replace("a = d", "a = 0")
    assert fixed_value != item.statement
    assert not check((), certificate, _candidate_target(fixed_value))


def test_list_at_functional_distinct_head_models() -> None:
    examples = (
        ((0, 1, 15), 1288, 6, (2, 0)),
        ((0, 3, 19), 819, 8, (0, 1)),
    )
    for values, code, scale, outer_heads in examples:
        assert _history(values, code, scale)
        for index, expected in enumerate(outer_heads):
            other = outer_heads[1 - index]
            assert _lookup(values, code, scale, index, expected)
            assert not _lookup(values, code, scale, index, other)

    # Countermodel for comparing different indices: the same represented
    # list returns 2 at index zero and 0 at index one.
    first = (0, 1, 15)
    assert _lookup(first, 1288, 6, 0, 2)
    assert _lookup(first, 1288, 6, 1, 0)
    assert 2 != 0

    # Countermodels for disconnecting d and forcing every result to zero.
    assert _lookup(first, 1288, 6, 0, 2)
    assert 2 != 1
    assert 2 != 0
