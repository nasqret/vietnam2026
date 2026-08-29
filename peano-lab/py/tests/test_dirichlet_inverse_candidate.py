"""Independent finite inverse contracts, actual beta diagnostics and HA checks.

The mathematical source is owned separately. These tests neither alter its
definitions nor turn conditional authoring checks into closed admission.
Every displayed inverse is a real two-sided convolution/delta graph; the
unit-at-one criterion is independently tested, not built into that graph.
"""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from pathlib import Path
from random import Random
import re
import sys

import pytest

from peano_lab.library import dirichlet_inverse_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.dirichlet_signed_unit_candidate import make_dirichlet_signed_unit_candidate_theorems
from peano_lab.library.dirichlet_triangular_candidate import make_dirichlet_triangular_candidate_theorems
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_dirichlet_convolution_candidate import (
    _conjoin, expected_table, expected_at, expected_le, expected_convolution_table,
    expected_positive_equal, expected_equal,
)
from tests.test_dirichlet_fubini_candidate import actual_convolution
from tests.test_dirichlet_signed_unit_candidate import expected_unit, actual_operation
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_mobius_inversion_candidate import core as parent_core, expected_delta
from tests.test_signed_rectangular_slice_candidate import actual_sum_trace, BoundedTestSelection
from tests.test_signed_table_operations_candidate import model_table, model_at, encode_signed, decode_signed


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

SOURCE_SHA256 = "05347563a82486859a49539e99055504720cc823e14b310389e1d90766a85379"
SPEC_SHA256 = "6ccb0ee24d871bffbdedb3100445411ec03cd1d515586f5b63fa9d4780bfdf20"
EXPECTED = (
    (14, 7), (30, 11), (69, 32), (31, 20), (28, 17), (49, 27), (39, 17),
    (208, 67), (119, 36), (46, 22), (25, 16), (20, 13), (72, 26), (141, 30),
    (93, 36), (96, 33), (51, 31), (43, 26), (38, 17), (31, 15), (35, 20),
)
STATEMENT_PINS = {
    "dirichlet_unit_at_one_witness": "15ba707af20687b894022ad429c2fb0eff7199fe2d86b0537eaaaf91f5a0fddc",
    "dirichlet_unit_at_one_from_value": "4a7116ac8ab9dba5c261f4a37c1b797c9a42ce16c2492302a1893f60f6fd547b",
    "dirichlet_kronecker_delta_table_restrict": "5d98d2f5c26cfc37feca7158548edee9c9337199b3931a2b82ce7d7a35afb73e",
    "dirichlet_inverse_from_right_delta": "9f4e47b961c53a87213af8d5b814f34a84a8d5526dd6c53fd02982e04e15eee3",
    "dirichlet_inverse_symmetric": "606ae234081fc7cb64c5528bb21e03ffe6a29e1ec74f6563c812da1830572db7",
    "dirichlet_inverse_actual_tables": "9af66253e8fdb972f292b1f5b6efb4f6e1aef678341b150f7bbd9775797c22e3",
    "dirichlet_inverse_zero": "d5112c0e6ecde11e8959eafa90bc889733fe1c2e5ae8a01dd2e90d7e291e6df1",
    "dirichlet_unit_equation_append": "70406a19e4d0e1a753f97df898de4b8fc2f0f317696f590869217e13a6fd4a86",
    "dirichlet_unit_equation_construct": "cbb0fc99f0f2eb3e77871b21e4a8d5cfe01d22c86b737e77b516f4c060f8644e",
    "dirichlet_inverse_from_unit": "1a2746c98a9702183fd7861de441c41d3ce9f0745d56098efa2aa9c6a8febe3b",
    "dirichlet_inverse_from_unit_at_one": "5910341c14f1da1c6eee58e046029c8eeefcdd2e159822a25bed9421820fd350",
    "dirichlet_inverse_zero_construct": "cef6be2e939bb529529e0da89b62b8ae6b5a113d46619d82e4881a65085d94f2",
    "dirichlet_inverse_construct": "a6dd40764e010f130261094e5e0bd352ffc1cc834ad401e9a586cdde02bd3c4d",
    "dirichlet_inverse_requires_unit_at_one": "ef61bee501b71b0f71182a836d46951d09e80a332369870aa5039ea9c1a573a9",
    "dirichlet_inverse_positive_unique": "e994f6705f3c11203d89eb694f887bc1466a7ab690520e3482e828e9d17df4df",
    "dirichlet_inverse_restrict": "af0ba57c75d5e9ff139646daf434818a059842b325ea1201b16390d6c7337be8",
    "dirichlet_inverse_prefix_compatible": "34013c77db0ab20b954698e1c69b065b34df43b34aa4306aafa670e145e7bc05",
    "dirichlet_inverse_involution": "7177f99394e6ef7dbbcb921e44c67e07ccec5caafa65ebbd0d1be1956cbad0cd",
    "dirichlet_inverse_criterion": "8c777567eae9fae4a3b6f0e0df4e4d80205c694f5b15f93f1808376e1b7d05fc",
    "dirichlet_inverse_positive_criterion": "b2130664b7580d7fbeaeb33ebed7c27718cd89676a2b893198751a39ce38d54d",
    "dirichlet_inverse_exists_positive_unique": "eb7703bdacfaca3d2d4a6c0cf5d2a43326be82107047a7609ce053da0fedd164",
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_dirichlet_inverse_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return parent_core() | {row.name: row for row in (
        *make_dirichlet_signed_unit_candidate_theorems(TheoremSpec),
        *make_dirichlet_triangular_candidate_theorems(TheoremSpec),
    )}


def table():
    return core() | {row.name: row for row in rows()}


def expected_unit_at_one(F, tag):
    return f"({expected_at(F,'1','2',tag+'positive')}) \\/ ({expected_at(F,'1','1',tag+'negative')})"


def expected_inverse(N, F, G, tag):
    E = "independent_inverse_delta_" + tag
    return f"exists {E}. " + _conjoin(
        expected_delta(N, E, tag + "delta"),
        expected_convolution_table(N, F, G, E, tag + "left"),
        expected_convolution_table(N, G, F, E, tag + "right"),
    )


def expected_statements():
    counter = 0
    def tagged(function):
        def call(*args):
            nonlocal counter
            counter += 1
            return function(*args, tag="inverse_" + str(counter))
        return call
    T, A, L, CT, PE, EQ, D, U, I = tuple(tagged(function) for function in (
        expected_table, expected_at, expected_le, expected_convolution_table,
        expected_positive_equal, expected_equal, expected_delta, expected_unit_at_one, expected_inverse,
    ))
    def all_(names, *clauses):
        return "forall " + names + ". " + " -> ".join("(" + clause + ")" for clause in clauses)
    condition = "N=0 \\/ (" + U("F") + ")"
    return {
        "dirichlet_unit_at_one_witness": all_("F", U("F"), "exists u. " + _conjoin(A("F","1","u"), expected_unit("u"))),
        "dirichlet_unit_at_one_from_value": all_("F u", A("F","1","u"), expected_unit("u"), U("F")),
        "dirichlet_kronecker_delta_table_restrict": all_("N K E", D("N","E"), L("K","N"), D("K","E")),
        "dirichlet_inverse_from_right_delta": all_("N F G E", D("N","E"), CT("N","G","F","E"), I("N","F","G")),
        "dirichlet_inverse_symmetric": all_("N F G", I("N","F","G"), I("N","G","F")),
        "dirichlet_inverse_actual_tables": all_("N F G", I("N","F","G"), _conjoin(T("N","F"), T("N","G"))),
        "dirichlet_inverse_zero": all_("F G", T("0","F"), T("0","G"), I("0","F","G")),
        "dirichlet_unit_equation_append": all_("N F T G u", T("S N","F"), T("S N","T"), A("F","1","u"), expected_unit("u"),
            CT("N","G","F","T"), "exists H. " + _conjoin(CT("S N","H","F","T"), EQ("G","H","S N"))),
        "dirichlet_unit_equation_construct": all_("N F T u w", T("N","F"), T("N","T"), A("F","1","u"), expected_unit("u"),
            "exists G. " + _conjoin(CT("N","G","F","T"), A("G","0","w"))),
        "dirichlet_inverse_from_unit": all_("N F u w", T("N","F"), A("F","1","u"), expected_unit("u"),
            "exists G. " + _conjoin(I("N","F","G"), A("G","0","w"))),
        "dirichlet_inverse_from_unit_at_one": all_("N F w", T("N","F"), U("F"),
            "exists G. " + _conjoin(I("N","F","G"), A("G","0","w"))),
        "dirichlet_inverse_zero_construct": all_("F w", T("0","F"), "exists G. " + _conjoin(I("0","F","G"), A("G","0","w"))),
        "dirichlet_inverse_construct": all_("N F w", T("N","F"), condition,
            "exists G. " + _conjoin(I("N","F","G"), A("G","0","w"))),
        "dirichlet_inverse_requires_unit_at_one": all_("N F G", I("N","F","G"), "~(N=0)", U("F")),
        "dirichlet_inverse_positive_unique": all_("N F G H", I("N","F","G"), I("N","F","H"), PE("G","H","N")),
        "dirichlet_inverse_restrict": all_("N K F G", I("N","F","G"), L("K","N"), I("K","F","G")),
        "dirichlet_inverse_prefix_compatible": all_("N K F G H", I("N","F","G"), I("K","F","H"), L("K","N"), PE("G","H","K")),
        "dirichlet_inverse_involution": all_("N F G H", I("N","F","G"), I("N","G","H"), PE("F","H","N")),
        "dirichlet_inverse_criterion": all_("N F", T("N","F"), _conjoin(
            f"(exists G. ({I('N','F','G')})) -> ({condition})", f"({condition}) -> exists G. ({I('N','F','G')})")),
        "dirichlet_inverse_positive_criterion": all_("N F", T("N","F"), "~(N=0)", _conjoin(
            f"(exists G. ({I('N','F','G')})) -> ({U('F')})", f"({U('F')}) -> exists G. ({I('N','F','G')})")),
        "dirichlet_inverse_exists_positive_unique": all_("N F w", T("N","F"), condition,
            "exists G. " + _conjoin(I("N","F","G"), A("G","0","w"),
                f"forall H. ({I('N','F','H')}) -> ({PE('G','H','N')})")),
    }


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_every_statement_has_independently_expanded_exact_contract(row):
    expected = expected_statements()
    assert tuple(expected) == tuple(item.name for item in rows())
    _assert_same_ast(_closed_formula(row.statement), _closed_formula(expected[row.name]))


def test_exact_frozen_source_topology_metrics_and_statement_pins():
    from peano_lab.library.campaign_bottom_layer_closure import _specs_digest
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest() == SOURCE_SHA256
    assert len(rows()) == 21
    assert sum(len(row.dependencies) for row in rows()) == 53
    assert sum(len(row.script) for row in rows()) == 764
    assert _specs_digest(rows()) == SPEC_SHA256
    assert sha256("\n".join(row.name for row in rows()).encode()).hexdigest() == "b320bb723eb16cb0784d550a4c28e0b41f154b466fecd7dddb1bd2d8ec8ccaea"
    assert {row.name: sha256(row.statement.encode()).hexdigest() for row in rows()} == STATEMENT_PINS
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= available
        assert all(re.search(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", "\n".join(row.script))
                   for name in row.dependencies)
        assert not any(command.startswith(("use ", "admit", "sorry", "DNE", "ring")) for command in row.script)
        available.add(row.name)


def test_all_40_new_statements_are_novel_against_3756_previous_and_each_other():
    from constructive_dirichlet_inverse_support import PRIOR_THEOREM_COUNT, statement_duplicates
    assert PRIOR_THEOREM_COUNT == 3756
    combined = (*make_dirichlet_signed_unit_candidate_theorems(TheoremSpec),
                *make_dirichlet_triangular_candidate_theorems(TheoremSpec), *rows())
    assert len(combined) == 40
    assert statement_duplicates(combined) == ()


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_original_kernel_body(row):
    try:
        checked = replay_candidate_bodies((row,), core=table())[0]
        assert checked.name == row.name
        assert (checked.proof_nodes, checked.proof_depth) == EXPECTED[rows().index(row)]
        assert checked.proof_depth <= 256
        assert checked.proof_objects <= checked.proof_nodes
        print(json.dumps({"name": row.name, "nodes": checked.proof_nodes, "depth": checked.proof_depth,
                          "objects": checked.proof_objects}), flush=True)
    finally:
        gc.collect()


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_false_target_cannot_reuse_body(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement="0=1"),), core=table())


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_missing_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=()),), core=table())


DEPENDENCIES = tuple((row, dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize("row,dependency", DEPENDENCIES, ids=lambda value: value.name if hasattr(value, "name") else value)
def test_dropped_dependency_cannot_be_used(row, dependency):
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=table())


@pytest.mark.parametrize("row,dependency", DEPENDENCIES, ids=lambda value: value.name if hasattr(value, "name") else value)
def test_poisoned_dependency_cannot_replace_actual_statement(row, dependency):
    altered = table()
    altered[dependency] = replace(altered[dependency], statement="0=1")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,), core=altered)


SURFACES = (
    (candidate.dirichlet_unit_at_one_relation, expected_unit_at_one, ("F",)),
    (candidate.dirichlet_inverse_relation, expected_inverse, ("N", "F", "G")),
)


@pytest.mark.parametrize("builder,expected,arguments", SURFACES, ids=("unit_at_one", "actual_inverse"))
@pytest.mark.parametrize("mode", ("identifiers", "compound", "large", "zero", "repeated"))
def test_public_graphs_are_literal_conservative_expansions(builder, expected, arguments, mode):
    context = ("N", "F", "G", "unused")
    if mode == "compound":
        arguments = tuple(value + "+N*F" for value in arguments)
    if mode == "large":
        arguments = ("12345678901234567890123456789012345678901234567890", *arguments[1:])
    if mode == "zero":
        arguments = ("0",) * len(arguments)
    if mode == "repeated":
        arguments = ("F",) * len(arguments)
    prefix = "forall " + " ".join(context) + ". "
    _assert_same_ast(_closed_formula(prefix + builder(*arguments, tag="contract", variables=context)),
                     _closed_formula(prefix + expected(*arguments, tag="independent")))


@pytest.mark.parametrize("builder,expected,arguments", SURFACES, ids=("unit_at_one", "actual_inverse"))
def test_every_generated_binder_rejects_unused_context_capture(builder, expected, arguments):
    context = ("N", "F", "G", "unused")
    source = builder(*arguments, tag="capture", variables=context)
    binders = {name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", source) for name in clause.split()}
    assert binders and not binders.intersection(context)
    for binder in binders:
        with pytest.raises(ValueError):
            builder(*arguments, tag="capture", variables=context + (binder,))


@pytest.mark.parametrize("builder,expected,arguments", SURFACES, ids=("unit_at_one", "actual_inverse"))
@pytest.mark.parametrize("bad", ("undeclared", "formula", "empty-context", "duplicate-context", "list-context", "bad-tag", "reserved-tag"))
def test_hostile_public_term_context_and_tag_inputs_are_rejected(builder, expected, arguments, bad):
    context, tag = ("N", "F", "G"), "hostile"
    if bad == "undeclared": arguments = ("missing", *arguments[1:])
    if bad == "formula": arguments = ("N -> 0=1", *arguments[1:])
    if bad == "empty-context": context = ()
    if bad == "duplicate-context": context = context + ("N",)
    if bad == "list-context": context = list(context)
    if bad == "bad-tag": tag = "invalid tag"
    if bad == "reserved-tag": tag = "forall"
    with pytest.raises(ValueError):
        builder(*arguments, tag=tag, variables=context)


@pytest.mark.parametrize("mutation", ("necessity_at_zero", "necessity_without_nonempty_guard", "zero_value_unique", "table_code_unique", "positive_only_criterion_at_zero"))
def test_stronger_invalid_inverse_claims_are_rejected(mutation):
    if mutation == "necessity_at_zero":
        row = next(row for row in rows() if row.name == "dirichlet_inverse_requires_unit_at_one")
        changed = f"forall N F G. ({expected_inverse('N','F','G','bad_zero')}) -> N=0 -> ({expected_unit_at_one('F','bad_unit')})"
    elif mutation == "necessity_without_nonempty_guard":
        row = next(row for row in rows() if row.name == "dirichlet_inverse_requires_unit_at_one")
        changed = f"forall N F G. ({expected_inverse('N','F','G','bad_unguarded')}) -> ({expected_unit_at_one('F','bad_unguarded_unit')})"
    elif mutation in ("zero_value_unique", "table_code_unique"):
        row = next(row for row in rows() if row.name == "dirichlet_inverse_positive_unique")
        conclusion = ("G=H" if mutation == "table_code_unique" else
                      f"forall a b. ({expected_at('G','0','a','bad_zero_first')}) -> ({expected_at('H','0','b','bad_zero_second')}) -> a=b")
        changed = f"forall N F G H. ({expected_inverse('N','F','G','bad_first')}) -> ({expected_inverse('N','F','H','bad_second')}) -> ({conclusion})"
    else:
        row = next(row for row in rows() if row.name == "dirichlet_inverse_criterion")
        existence = f"exists G. ({expected_inverse('N','F','G','bad_criterion_inverse')})"
        condition = expected_unit_at_one("F", "bad_criterion_unit")
        changed = f"forall N F. ({expected_table('N','F','bad_criterion_table')}) -> " + _conjoin(
            f"({existence}) -> ({condition})", f"({condition}) -> ({existence})")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=changed),), core=table())


def actual_solution(F, T, N, *, zero, offset):
    """Diagnostic finite construction with actual beta prefix/append tables."""
    values = [zero]
    G = model_table(values, offset=offset, endpoint=991)
    if N:
        unit = decode_signed(model_at(F, 1))
        assert unit in (1, -1)
    history = []
    for n in range(1, N + 1):
        previous = G
        proper = tuple(0 if d == 0 or n % d else decode_signed(model_at(previous, d)) * decode_signed(model_at(F, n // d))
                       for d in range(n))
        prefix = model_table(proper, offset=offset + n, endpoint=-997)
        remainder = actual_sum_trace(prefix, n)
        desired = model_at(T, n)
        product = encode_signed(decode_signed(desired) - decode_signed(remainder))
        value = encode_signed(decode_signed(product) * unit)
        assert actual_operation(value, encode_signed(unit), product, multiply=True)
        assert actual_operation(remainder, product, desired, multiply=False)
        values.append(decode_signed(value))
        G = model_table(values, offset=offset + n + 7, endpoint=1009)
        assert all(model_at(previous, i) == model_at(G, i) for i in range(n))
        assert model_at(G, n) == value
        # Check every earlier equation using fresh literal summand and
        # cumulative beta witnesses, not merely a Python convolution sum.
        for k in range(1, n + 1):
            actual, mask = actual_convolution(G, F, k, offset=offset + k)
            assert actual == model_at(T, k)
            if k == n:
                assert all(model_at(mask, i) == model_at(prefix, i) for i in range(n))
                assert model_at(mask, n) == product
        history.append((previous, prefix, remainder, value, G))
    assert model_at(G, 0) == encode_signed(zero)
    return G, tuple(history)


def actual_inverse(F, N, *, zero, offset, delta_zero=67):
    delta = model_table(tuple([delta_zero] + [1 if n == 1 else 0 for n in range(1, N + 1)]),
                        offset=offset + 3, endpoint=-1013)
    G, history = actual_solution(F, delta, N, zero=zero, offset=offset)
    for n in range(1, N + 1):
        assert actual_convolution(F, G, n)[0] == actual_convolution(G, F, n)[0] == model_at(delta, n)
        assert model_at(delta, n) == (2 if n == 1 else 0)
    return G, delta, history


@pytest.mark.parametrize("N", (0, 1, 2, 4, 6))
@pytest.mark.parametrize("unit", (1, -1))
@pytest.mark.parametrize("seed", (0, 17, 101))
def test_actual_beta_arbitrary_target_solutions_preserve_each_constructed_prefix(N, unit, seed):
    random = Random(seed)
    inputs = [113, unit] + [random.randint(-4, 4) for _ in range(max(0, N - 1))]
    F = model_table(inputs, offset=3, endpoint=-997)
    T = model_table(tuple([-127] + [random.randint(-6, 6) for _ in range(N)]), offset=7, endpoint=991)
    G, history = actual_solution(F, T, N, zero=131, offset=11)
    assert len(history) == N
    assert model_at(G, 0) != model_at(F, 0) != model_at(T, 0)
    for n in range(1, N + 1):
        assert actual_convolution(G, F, n)[0] == model_at(T, n)


@pytest.mark.parametrize("N", (0, 1, 3, 6))
@pytest.mark.parametrize("unit", (1, -1))
def test_actual_inverse_witnesses_both_orders_and_noncanonical_table_representatives(N, unit):
    F = model_table(tuple([137, unit] + [(-1) ** n * n for n in range(2, N + 1)]), offset=5, endpoint=983)
    G, E, _ = actual_inverse(F, N, zero=139, offset=7, delta_zero=-149)
    H, D, _ = actual_inverse(F, N, zero=-151, offset=19, delta_zero=157)
    assert G[0] != H[0] and G[1] != H[1]
    assert E[0] != D[0]
    assert model_at(G, 0) != model_at(H, 0)
    assert model_at(E, 0) != model_at(D, 0)
    for n in range(1, N + 1):
        assert model_at(G, n) == model_at(H, n)
        assert actual_convolution(F, G, n)[0] == actual_convolution(G, F, n)[0] == model_at(E, n)


@pytest.mark.parametrize("unit", (1, -1))
@pytest.mark.parametrize("K", (0, 1, 2, 4))
def test_independently_constructed_inverse_prefixes_and_involution_agree_only_positively(unit, K):
    N = 5
    F = model_table((163, unit, -2, 3, 0, -1), offset=3, endpoint=977)
    G, _, _ = actual_inverse(F, N, zero=-167, offset=5)
    H, _, _ = actual_inverse(F, K, zero=173, offset=13)
    twice, _, _ = actual_inverse(G, N, zero=-179, offset=17)
    assert G[0] != H[0] and model_at(G, 0) != model_at(H, 0)
    assert F[0] != twice[0] and model_at(F, 0) != model_at(twice, 0)
    for n in range(1, K + 1):
        assert model_at(G, n) == model_at(H, n)
    for n in range(1, N + 1):
        assert model_at(F, n) == model_at(twice, n)


@pytest.mark.parametrize("nonunit", (0, 2, -2, 3, -3, 19))
def test_zero_window_has_real_inverse_witnesses_despite_nonunit_at_one(nonunit):
    F = model_table((181, nonunit), offset=7, endpoint=971)
    G, E, history = actual_inverse(F, 0, zero=-191, offset=11)
    assert decode_signed(model_at(F, 1)) == nonunit
    assert model_at(F, 1) not in (1, 2)
    assert history == ()
    assert model_at(G, 0) == encode_signed(-191)
    assert model_at(E, 0) == encode_signed(67)
    assert F[0] != G[0] and model_at(F, 0) != model_at(G, 0)


@pytest.mark.parametrize("nonunit", (0, 2, -2, 3, -3, 19))
def test_nonunit_obstruction_is_at_actual_in_domain_one_not_at_zero(nonunit):
    F = model_table((193, nonunit), offset=5, endpoint=967)
    for value in range(-6, 7):
        G = model_table((-197, value), offset=11, endpoint=953)
        result, mask = actual_convolution(F, G, 1)
        assert result != 2
        assert model_at(mask, 0) == 0
        assert actual_operation(model_at(F, 1), model_at(G, 1), result, multiply=True)
        assert model_at(F, 0) != model_at(G, 0)


if __name__ == "__main__":
    import argparse
    import resource
    import signal
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument("--body")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--pytest-select")
    parser.add_argument("--case-start", type=int, default=0)
    parser.add_argument("--case-count", type=int)
    arguments = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    if arguments.pytest_select is not None:
        plugins = [] if arguments.case_count is None else [BoundedTestSelection(arguments.case_start, arguments.case_count)]
        status = pytest.main(["-q", "-s", "--tb=short", __file__, "-k", arguments.pytest_select], plugins=plugins)
    else:
        selected = (tuple(row for row in rows() if row.name == arguments.body) if arguments.body
                    else rows()[arguments.start:arguments.start + arguments.count])
        if not selected:
            raise SystemExit("unknown theorem body")
        for row in selected:
            test_original_kernel_body(row)
        status = 0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    assert peak <= 1536 * 1024 * 1024
    print(json.dumps({"status": status, "seconds": time.monotonic() - started, "peak_rss_bytes": peak}), flush=True)
    raise SystemExit(status)
