"""Focused body audit for the private K3B ``list_at_head_iff`` row.

The checks stop at the dependency-curried candidate body.  They do not close
the beta/CRT dependency graph, admit a theorem, or run any campaign-wide gate.
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
    And,
    Exists,
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
from peano_lab.library.ha_cell_history_candidate import (
    cell_list_len,
    make_ha_cell_history_candidate_theorems,
)
from peano_lab.library.ha_cell_history_prefix_preservation_candidate import (
    make_ha_cell_history_prefix_preservation_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_head_candidate import (
    make_ha_cell_list_lookup_head_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "list_at_head_iff"
EXPECTED_DEPENDENCIES = (
    "cell_history_succ_elim",
    "cell_history_extend_preserves_prefix",
    "beta_at_unique",
    "le_refl",
)
EXPECTED_STATEMENT_RECEIPT = (
    12_530,
    "9f0b3e7496f79b7cc6f4833edc14431dd614081b6f02b2d384aa80c521e2f8ed",
)
EXPECTED_AST_RECEIPT = (723, 189)
EXPECTED_BODY_RECEIPT = (4, 119, 265, 36, 255, 264, 10)
EXACT_CELL = "z = S ((a + t) * S (a + t) + (t + t))"
SWAPPED_CELL = "z = S ((t + a) * S (t + a) + (a + a))"


def _zero_lookup(code: str, value: str, *, tag: str) -> str:
    placeholder = f"head_test_zero_index_{tag}"
    expanded = cell_list_at(code, placeholder, value, tag=tag)
    assert expanded.count(placeholder) > 0
    return expanded.replace(placeholder, "0")


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (item,) = make_ha_cell_list_lookup_head_candidate_theorems(TheoremSpec)
    return item


@lru_cache(maxsize=1)
def _available_specs() -> dict[str, TheoremSpec]:
    private = {
        item.name: item
        for item in (
            make_ha_cell_history_candidate_theorems(TheoremSpec)
            + make_ha_cell_history_prefix_preservation_candidate_theorems(
                TheoremSpec
            )
        )
    }
    public = _specs_by_name()
    return {
        name: private.get(name, public.get(name))
        for name in EXPECTED_DEPENDENCIES
    }


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


def test_list_at_head_surface_is_exact_oriented_closed_and_private() -> None:
    item = _candidate_spec()
    lookup_source = _zero_lookup("z", "a", tag="head_source")
    lookup_target = _zero_lookup("z", "a", tag="head_target")
    source_tail = cell_list_len(
        "t", "l", tag="head_source_tail_length"
    )
    target_tail = cell_list_len(
        "t", "l", tag="head_target_tail_length"
    )
    expected = (
        "forall z a. "
        f"((({lookup_source}) -> exists t l. "
        f"(({EXACT_CELL}) /\\ ({source_tail}))) /\\ "
        f"((exists t l. (({EXACT_CELL}) /\\ "
        f"({target_tail}))) -> ({lookup_target})))"
    )

    assert make_ha_cell_list_lookup_head_candidate_theorems(
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

    assert isinstance(formula, Forall)
    assert isinstance(formula.body, Forall)
    equivalence = formula.body.body
    assert isinstance(equivalence, And)
    assert isinstance(equivalence.left, Imp)
    assert isinstance(equivalence.right, Imp)
    assert isinstance(equivalence.left.left, Exists)
    assert isinstance(equivalence.left.right, Exists)
    assert isinstance(equivalence.left.right.body, Exists)
    assert isinstance(equivalence.left.right.body.body, And)
    assert isinstance(equivalence.right.left, Exists)
    assert isinstance(equivalence.right.left.body, Exists)
    assert isinstance(equivalence.right.left.body.body, And)
    assert isinstance(equivalence.right.right, Exists)

    assert item.statement.count(EXACT_CELL) == 2
    assert SWAPPED_CELL not in item.statement
    assert item.statement.count(
        "hclook_edge_head_source + S 0 = hclook_length_head_source"
    ) == 1
    assert item.statement.count(
        "hclook_edge_head_target + S 0 = hclook_length_head_target"
    ) == 1
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
            "hclookhead_zero_index_argument",
        )
    )

    public = _specs_by_name()
    assert item.name not in public
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_list_lookup_head_candidate" not in registry_source
    assert f'"{item.name}"' not in registry_source


def test_list_at_head_body_is_pinned_constructive_and_mutation_sensitive() -> None:
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
            "cell_head_functional",
            "cell_tail_functional",
            "cell_list_succ_iff_cell",
            "list_at_domain",
        }
    )

    assert item.statement.count(EXACT_CELL) == 2
    mutated = item.statement.replace(EXACT_CELL, SWAPPED_CELL)
    assert mutated != item.statement
    assert not check((), certificate, _candidate_target(mutated))


def test_list_at_head_distinct_head_standard_models() -> None:
    # Singleton: 7 = Cell(2,0), encoded as 0,7 modulo 5,9.
    singleton = (0, 7)
    assert _history(singleton, 25, 4)
    assert _history(singleton[:-1], 25, 4)
    assert _cell(2, 0) == 7
    assert _lookup(singleton, 25, 4, 0, 2)

    # Distinct outer head and tail: residues 0,1,15 modulo 7,13,19.
    # The represented list has inner head 0 and outer head 2:
    # 1 = Cell(0,0), then 15 = Cell(2,1).
    values = (0, 1, 15)
    assert tuple(1288 % modulus for modulus in (7, 13, 19)) == values
    assert _history(values, 1288, 6)
    assert _history(values[:-1], 1288, 6)
    assert _cell(0, 0) == 1
    assert _cell(2, 1) == 15
    assert _lookup(values, 1288, 6, 0, 2)
    assert not _lookup(values, 1288, 6, 0, 1)
    assert _lookup(values, 1288, 6, 1, 0)
    assert not _lookup(values, 1288, 6, 1, 2)

    # The false statement mutation swaps the fixed head with the existential
    # tail.  No natural head paired with fixed tail 2 produces code 15.
    assert _cell(1, 2) == 17
    assert all(_cell(head, 2) != 15 for head in range(16))
