"""Body, dependency, and statement audit for the first K3C theorem tranche."""

from __future__ import annotations

from dataclasses import fields, replace
from hashlib import sha256
from math import factorial, gcd

import pytest

from peano_lab.kernel.formulas import Formula, parse_formula, parse_formula_with_names
from peano_lab.kernel.terms import Term
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.editions import ALPHA_SPECS
from peano_lab.library.ha_cell_list_membership_candidate import (
    make_ha_cell_list_membership_candidate_theorems,
)
from peano_lab.library.ha_cell_list_membership_surface_candidate import (
    cell_list_member,
)
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell
from peano_lab.library.ha_cell_list_interface_candidate import (
    make_ha_cell_list_interface_candidate_theorems,
)
from peano_lab.library.ha_cell_list_validity_candidate import (
    make_ha_cell_list_validity_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec


EXPECTED = {
    "cell_list_valid_nil": (
        3185,
        "5ec6b2e7ef6f193917b42834c4b0c51cfde4af18da2975e43f574ee0379458ec",
        132,
        35,
        (1, 4, 5, 5, 5, 4, 0),
    ),
    "cell_list_valid_cell_intro": (
        7779,
        "59a76ea4ba8f61e3b872d777eacac869254eef33709905018c644e658b74c649",
        284,
        76,
        (1, 18, 19, 13, 19, 18, 0),
    ),
    "cell_list_valid_cases": (
        6960,
        "8945d1b66d00c6fba46c1671873f6f597e7673480550962700f94623837eb287",
        288,
        78,
        (2, 35, 41, 22, 41, 40, 0),
    ),
    "cell_list_valid_cell_elim": (
        7107,
        "ee10fcc3b285e1f794211a3d4970d2fc057da18fcf5ec06c6f6270b32896c153",
        284,
        76,
        (3, 33, 56, 23, 56, 55, 0),
    ),
    "list_at_implies_cell_list_valid": (
        7834,
        "71299df15dfee548ac46ba9e42ebcd01f48fb2b1f42c346d64de75215c42d1d1",
        346,
        93,
        (1, 14, 15, 11, 15, 14, 0),
    ),
    "list_member_implies_cell_list_valid": (
        7660,
        "a281b55116f652714259c898542a85cd24941be57d14b45ef7c9902463dd04b9",
        346,
        93,
        (1, 9, 21, 13, 21, 20, 0),
    ),
    "list_member_nil_false": (
        4038,
        "24674ce7d90e8f21eae002ce1c8edf78ef091d96c1d29f9e2c77312fd4582018",
        214,
        58,
        (5, 33, 41, 19, 41, 40, 0),
    ),
    "list_member_cell_intro_head": (
        8513,
        "6a65cbdf21e84f6e4816ad3907b7d03a8c4471d02770b72f54448cec75de9ad9",
        363,
        96,
        (1, 18, 19, 13, 19, 18, 0),
    ),
    "list_member_cell_intro_tail": (
        9361,
        "25b0fdd45f0b5c7b3a7d3b7c91474f22de2697c61046d749d151733bc1e2b7f5",
        443,
        117,
        (1, 20, 21, 15, 21, 20, 0),
    ),
    "list_member_cell_elim": (
        8742,
        "55ebbef79b611124c4640f827011260ecc1484648456893f9a35df3896de613f",
        447,
        119,
        (3, 77, 100, 41, 100, 99, 0),
    ),
    "list_member_cell_iff": (
        21422,
        "9fa08a27b5a2d3aa21411924525736961a131fe83fd96c4526adf8ab13596ad4",
        1008,
        269,
        (3, 32, 79, 23, 79, 78, 0),
    ),
    "list_member_pointwise_transport": (
        22662,
        "2cec4de0dc94ada411ad0884d093baffdb8c3fba5297629251bca2a83c57b0e2",
        1128,
        303,
        (2, 37, 71, 25, 71, 70, 0),
    ),
    "list_at_exists_unique": (
        10925,
        "59f950707e749b1e9354d352881d8653c33cc55dde26fb8c2de03648963bbb19",
        570,
        154,
        (2, 25, 30, 19, 30, 29, 0),
    ),
    "cell_list_nonempty_iff_head_exists": (
        15140,
        "26d902cb638d60a8fe06fe2a15848764c21830bd021aab0314ed9277f1ae0e95",
        696,
        184,
        (2, 38, 46, 14, 46, 45, 0),
    ),
    "cell_list_code_eq_lookup_values": (
        8554,
        "cafd660a805a10d988458c61a3ba4b8e6b8c35e02e89f19f625eee4557afd7eb",
        434,
        118,
        (1, 17, 40, 24, 40, 39, 0),
    ),
    "cell_list_code_eq_iff_pointwise": (
        29456,
        "ff28e1e269f7309a68bec117518ae6c520b36295e40404eb8a0630e3fec8b6bb",
        1148,
        312,
        (2, 30, 62, 29, 62, 61, 0),
    ),
    "cell_list_decompose_unique": (
        6696,
        "74d498c91cdf9dac58e09c6167920d2d58f01aa7419dc28c7d388f348b991ccb",
        312,
        83,
        (2, 29, 36, 22, 36, 35, 0),
    ),
}


def _specs() -> tuple[TheoremSpec, ...]:
    return (
        make_ha_cell_list_validity_candidate_theorems(TheoremSpec)
        + make_ha_cell_list_membership_candidate_theorems(TheoremSpec)
        + make_ha_cell_list_interface_candidate_theorems(TheoremSpec)
    )


def _walk(value: Formula | Term):
    yield value
    for field in fields(value):
        child = getattr(value, field.name)
        if isinstance(child, (Formula, Term)):
            yield from _walk(child)


def _core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in ALPHA_SPECS}


def test_k3c_statement_order_hashes_ast_and_dependency_surface_are_frozen() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert len({item.name for item in specs}) == len(specs) == 17
    assert not ({item.name for item in specs} & set(_core()))

    available = set(_core())
    for item in specs:
        expected = EXPECTED[item.name]
        assert (len(item.statement), sha256(item.statement.encode()).hexdigest()) == (
            expected[0],
            expected[1],
        )
        formula, free = parse_formula_with_names(item.statement)
        assert not free
        assert formula == parse_formula(item.statement)
        nodes = tuple(_walk(formula))
        assert (len(nodes), sum(isinstance(node, Formula) for node in nodes)) == (
            expected[2],
            expected[3],
        )
        assert all(dependency in available for dependency in item.dependencies)
        available.add(item.name)
        assert all(
            macro not in item.statement
            for macro in (
                "BetaAt(",
                "Cell(",
                "CellHistory(",
                "CellList(",
                "CellListValid(",
                "CellListLen(",
                "ListAt(",
                "ListMember(",
            )
        )


def test_k3c_all_seventeen_dependency_curried_bodies_are_kernel_checked_and_dne_free() -> None:
    specs = _specs()
    receipts = replay_candidate_bodies(specs, core=_core())
    assert tuple(receipt.name for receipt in receipts) == tuple(EXPECTED)
    for item, receipt in zip(specs, receipts, strict=True):
        assert (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        ) == EXPECTED[item.name][4]
        assert "DNE" not in item.script


def test_k3c_every_declared_direct_dependency_is_live_in_the_authored_body() -> None:
    specs = _specs()
    for item in specs:
        for dependency in item.dependencies:
            mutated = replace(
                item,
                dependencies=tuple(
                    name for name in item.dependencies if name != dependency
                ),
            )
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((mutated,), core={**_core(), **{
                    spec.name: spec for spec in specs
                }})


def test_k3c_false_conclusion_mutations_are_rejected() -> None:
    specs = _specs()
    for item in specs:
        mutated = replace(item, statement=f"({item.statement}) /\\ false")
        mutated_specs = tuple(
            mutated if candidate.name == item.name else candidate
            for candidate in specs
        )
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(mutated_specs, core=_core())


def _reject_statement_mutation(name: str, statement: str) -> None:
    specs = _specs()
    original = next(item for item in specs if item.name == name)
    assert statement != original.statement
    mutated_specs = tuple(
        replace(item, statement=statement) if item.name == name else item
        for item in specs
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(mutated_specs, core=_core())


def _term_member(code_term: str, value: str, *, tag: str) -> str:
    marker = f"k3c_test_member_code_{tag}"
    expanded = cell_list_member(marker, value, tag=tag)
    assert marker in expanded
    return expanded.replace(marker, code_term)


def test_k3c_orientation_and_boundary_mutations_are_rejected() -> None:
    by_name = {item.name: item for item in _specs()}

    head_intro = by_name["list_member_cell_intro_head"]
    forward_cell = cell("z", "h", "t")
    reversed_cell = cell("z", "t", "h")
    assert head_intro.statement.count(forward_cell) == 1
    _reject_statement_mutation(
        head_intro.name,
        head_intro.statement.replace(forward_cell, reversed_cell),
    )

    nil_false = by_name["list_member_nil_false"]
    nil_member = _term_member("0", "a", tag="nil_source")
    singleton_member = _term_member("S 0", "a", tag="nil_source")
    assert nil_false.statement.count(nil_member) == 1
    _reject_statement_mutation(
        nil_false.name,
        nil_false.statement.replace(nil_member, singleton_member),
    )

    exists_unique = by_name["list_at_exists_unique"]
    original_bound = "k + S i = l"
    shifted_bound = "k + S S i = l"
    assert exists_unique.statement.count(original_bound) == 1
    _reject_statement_mutation(
        exists_unique.name,
        exists_unique.statement.replace(original_bound, shifted_bound),
    )

    member_elim = by_name["list_member_cell_elim"]
    tail_member = cell_list_member("t", "a", tag="elim_tail_target")
    head_or_tail = f"a = h \\/ ({tail_member})"
    assert member_elim.statement.count(head_or_tail) == 1
    _reject_statement_mutation(
        member_elim.name,
        member_elim.statement.replace(head_or_tail, f"({tail_member})"),
    )


def _cell_code(head: int, tail: int) -> int:
    shell = head + tail
    return 1 + shell * (shell + 1) + 2 * tail


def _beta_at(code: int, scale: int, index: int, value: int) -> bool:
    modulus = 1 + (index + 1) * scale
    return value < modulus and code % modulus == value


def _encode_reverse_history(heads_inner_to_outer: tuple[int, ...]):
    values = [0]
    for head in heads_inner_to_outer:
        values.append(_cell_code(head, values[-1]))
    if not heads_inner_to_outer:
        return tuple(values), 0, 0

    base = factorial(len(values))
    scale = ((max(values) + 1 + base - 1) // base) * base
    code = 0
    period = 1
    for index, value in enumerate(values):
        modulus = 1 + (index + 1) * scale
        assert gcd(period, modulus) == 1
        for multiplier in range(modulus):
            candidate = code + period * multiplier
            if candidate % modulus == value:
                code = candidate
                break
        else:  # pragma: no cover - pairwise coprimality makes this impossible
            raise AssertionError("bounded CRT witness was not found")
        period *= modulus
    return tuple(values), code, scale


def _history_holds(values: tuple[int, ...], code: int, scale: int) -> bool:
    return (
        _beta_at(code, scale, 0, 0)
        and _beta_at(code, scale, len(values) - 1, values[-1])
        and all(
            any(
                values[edge + 1] == _cell_code(head, values[edge])
                for head in range(values[edge + 1] + 1)
            )
            for edge in range(len(values) - 1)
        )
    )


def _list_at_holds(
    values: tuple[int, ...],
    trace_code: int,
    scale: int,
    index: int,
    head: int,
) -> bool:
    length = len(values) - 1
    if not _history_holds(values, trace_code, scale):
        return False
    return any(
        edge + index + 1 == length
        and _beta_at(trace_code, scale, edge, tail)
        and _beta_at(trace_code, scale, edge + 1, successor)
        and successor == _cell_code(head, tail)
        for edge, tail, successor in (
            (edge, values[edge], values[edge + 1])
            for edge in range(length)
        )
    )


@pytest.mark.parametrize(
    ("heads_inner_to_outer", "heads_outer_to_inner"),
    (
        ((), ()),
        ((2,), (2,)),
        ((4, 4), (4, 4)),
        ((0, 1, 2), (2, 1, 0)),
    ),
)
def test_k3c_nil_singleton_repeated_and_three_cell_standard_models(
    heads_inner_to_outer: tuple[int, ...],
    heads_outer_to_inner: tuple[int, ...],
) -> None:
    values, trace_code, scale = _encode_reverse_history(heads_inner_to_outer)
    assert _history_holds(values, trace_code, scale)
    assert all(
        _list_at_holds(values, trace_code, scale, index, head)
        for index, head in enumerate(heads_outer_to_inner)
    )
    assert not _list_at_holds(
        values,
        trace_code,
        scale,
        len(heads_outer_to_inner),
        0,
    )
    represented_members = {
        value
        for value in range(6)
        if any(
            _list_at_holds(values, trace_code, scale, index, value)
            for index in range(len(heads_outer_to_inner))
        )
    }
    assert represented_members == set(heads_outer_to_inner)
