"""Focused body audit for the private K3B ``list_at_succ_iff`` row.

The tests leave all three declared dependencies as ordinary hypotheses.  No
recursive closure, admission, WMI replay, or campaign-wide gate occurs here.
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
    make_ha_cell_history_candidate_theorems,
)
from peano_lab.library.ha_cell_history_prefix_preservation_candidate import (
    make_ha_cell_history_prefix_preservation_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_succ_candidate import (
    make_ha_cell_list_lookup_succ_candidate_theorems,
)
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "list_at_succ_iff"
EXPECTED_DEPENDENCIES = (
    "cell_history_succ_elim",
    "cell_history_extend_preserves_prefix",
    "add_comm",
)
EXPECTED_STATEMENT_RECEIPT = (
    14_716,
    "004ef041acbcfbaaeda594f5f47fbea75ac6f8df87ca8bcf49774cfcbc3a978c",
)
EXPECTED_AST_RECEIPT = (884, 230)
EXPECTED_BODY_RECEIPT = (3, 124, 198, 38, 196, 197, 2)
EXACT_CELL = "z = S ((h + t) * S (h + t) + (t + t))"
SWAPPED_CELL = "z = S ((t + h) * S (t + h) + (h + h))"


def _successor_lookup(
    code: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    placeholder = f"succ_test_index_{tag}"
    expanded = cell_list_at(code, placeholder, value, tag=tag)
    assert expanded.count(placeholder) > 0
    return expanded.replace(placeholder, f"S {index}")


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (item,) = make_ha_cell_list_lookup_succ_candidate_theorems(TheoremSpec)
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
    available = dict(public) | private
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


def test_list_at_succ_surface_is_exact_oriented_closed_and_private() -> None:
    item = _candidate_spec()
    lookup_source = _successor_lookup(
        "z", "i", "a", tag="succ_source"
    )
    lookup_target = _successor_lookup(
        "z", "i", "a", tag="succ_target"
    )
    tail_target = cell_list_at("t", "i", "a", tag="succ_tail_target")
    tail_source = cell_list_at("t", "i", "a", tag="succ_tail_source")
    expected = (
        "forall z i a. "
        f"((({lookup_source}) -> exists t h. "
        f"(({EXACT_CELL}) /\\ ({tail_target}))) /\\ "
        f"((exists t h. (({EXACT_CELL}) /\\ "
        f"({tail_source}))) -> ({lookup_target})))"
    )

    assert make_ha_cell_list_lookup_succ_candidate_theorems(
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
    assert isinstance(formula.body.body, Forall)
    equivalence = formula.body.body.body
    assert isinstance(equivalence, And)
    assert isinstance(equivalence.left, Imp)
    assert isinstance(equivalence.right, Imp)
    assert isinstance(equivalence.left.left, Exists)
    assert isinstance(equivalence.left.right, Exists)
    assert isinstance(equivalence.left.right.body, Exists)
    assert isinstance(equivalence.left.right.body.body, And)
    assert isinstance(equivalence.left.right.body.body.right, Exists)
    assert isinstance(equivalence.right.left, Exists)
    assert isinstance(equivalence.right.left.body, Exists)
    assert isinstance(equivalence.right.left.body.body, And)
    assert isinstance(equivalence.right.left.body.body.right, Exists)
    assert isinstance(equivalence.right.right, Exists)

    assert item.statement.count(EXACT_CELL) == 2
    assert SWAPPED_CELL not in item.statement
    for tag in ("succ_source", "succ_target"):
        equation = (
            f"hclook_edge_{tag} + S S i = hclook_length_{tag}"
        )
        assert item.statement.count(equation) == 1
    for tag in ("succ_tail_target", "succ_tail_source"):
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
            "hclooksucc_successor_index_argument",
        )
    )

    public = _specs_by_name()
    assert item.name not in public
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_cell_list_lookup_succ_candidate" not in registry_source
    assert f'"{item.name}"' not in registry_source


def test_list_at_succ_body_is_pinned_constructive_and_shift_sensitive() -> None:
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
            "beta_at_unique",
            "le_refl",
            "cell_head_functional",
            "cell_tail_functional",
            "list_at_domain",
            "list_at_head_iff",
        }
    )

    # False mutation: erase the one-cell shift on both outer-list lookups
    # while retaining the original index in both tail lookups.
    mutated = item.statement
    for tag in ("succ_source", "succ_target"):
        old = f"hclook_edge_{tag} + S S i = hclook_length_{tag}"
        new = f"hclook_edge_{tag} + S i = hclook_length_{tag}"
        assert mutated.count(old) == 1
        mutated = mutated.replace(old, new)
    assert mutated != item.statement
    assert not check((), certificate, _candidate_target(mutated))


def test_list_at_succ_distinct_head_standard_models() -> None:
    # 0,1,15 modulo 7,13,19: outer head 2, selected inner head 0.
    first = (0, 1, 15)
    assert tuple(1288 % modulus for modulus in (7, 13, 19)) == first
    assert _history(first, 1288, 6)
    assert _history(first[:-1], 1288, 6)
    assert _cell(0, 0) == 1
    assert _cell(2, 1) == 15
    assert _lookup(first, 1288, 6, 1, 0)
    assert _lookup(first[:-1], 1288, 6, 0, 0)
    assert not _lookup(first, 1288, 6, 0, 0)
    assert not _lookup(first, 1288, 6, 1, 2)

    # 0,3,19 modulo 9,17,25: outer head 0, selected inner head 1.
    second = (0, 3, 19)
    assert tuple(819 % modulus for modulus in (9, 17, 25)) == second
    assert _history(second, 819, 8)
    assert _history(second[:-1], 819, 8)
    assert _cell(1, 0) == 3
    assert _cell(0, 3) == 19
    assert _lookup(second, 819, 8, 1, 1)
    assert _lookup(second[:-1], 819, 8, 0, 1)
    assert not _lookup(second, 819, 8, 0, 1)
    assert not _lookup(second, 819, 8, 1, 0)
