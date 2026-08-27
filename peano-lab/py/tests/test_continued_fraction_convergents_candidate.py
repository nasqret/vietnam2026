"""Original-kernel, dependency-curried tests for genuine convergent histories."""

from functools import lru_cache
from dataclasses import replace
import gc
from math import factorial, gcd
from hashlib import sha256
import re

import pytest

from peano_lab.library import continued_fraction_convergents_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from peano_lab.kernel.formulas import And, Exists, Forall, Imp, parse_formula_with_names
from peano_lab.library.continued_fraction_candidate import continued_fraction
from test_continued_fraction_approximation_candidate import core as parent_core, rows as arithmetic_rows, strict_nodes


@lru_cache(maxsize=1)
def rows():
    return candidate.make_continued_fraction_convergents_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return parent_core() | {row.name: row for row in arithmetic_rows()}


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_candidate_body_passes_the_original_kernel(name):
    table = {row.name: row for row in rows()}
    try:
        receipt = replay_candidate_bodies((table[name],), core=core() | table)[0]
        assert receipt.name == name
        assert receipt.proof_depth <= 256
        assert receipt.proof_objects <= receipt.proof_nodes
    finally:
        gc.collect()


def test_candidate_rows_are_fresh_and_dependency_ordered():
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(row.dependencies) == len(set(row.dependencies))
        available.add(row.name)


def test_frozen_g072_factory_inventory_and_minimal_declared_graph():
    arithmetic = arithmetic_rows()
    computations = rows()
    combined = arithmetic + computations
    assert (len(arithmetic), len(computations), len(combined)) == (39, 44, 83)
    assert sum(len(row.dependencies) for row in combined) == 247
    assert sum(len(row.script) for row in combined) == 4003
    names = ("\n".join(row.name for row in combined) + "\n").encode()
    assert sha256(names).hexdigest() == "837683363179ce24056cd96e6a313df8f96aee1dddb8378addd934ea79de6e44"
    assert max(len(row.statement.encode()) for row in combined) == 28715


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_poisoned_convergent_body_is_rejected_by_the_original_checker(name):
    table = {row.name: row for row in rows()}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(table[name], script=("refl",)),), core=core() | table)


PUBLIC_RELATIONS = (
    (candidate.convergent_matrix_state_code_relation, 6),
    (candidate.convergent_matrix_state_at_relation, 8),
    (candidate.convergent_matrix_trace_relation, 8),
    (candidate.convergent_relation, 4),
    (candidate.best_approximation_second_kind_relation, 4),
)


@pytest.mark.parametrize("relation,arity", PUBLIC_RELATIONS, ids=("state_code", "state_at", "matrix_trace", "convergent", "best_approximation"))
def test_public_computation_relations_are_hygienic_strict_ha(relation, arity):
    context = tuple("x" + str(i) for i in range(arity)) + ("z",)
    values = tuple("(" + context[i] + " + z) * S z" for i in range(arity))
    first, free = parse_formula_with_names(relation(*values, tag="first", variables=context))
    other, other_free = parse_formula_with_names(relation(*values, tag="other", variables=context))
    assert first == other and free == other_free
    assert set(free) == set(context)
    assert tuple(strict_nodes(first))


@pytest.mark.parametrize("relation,arity", PUBLIC_RELATIONS, ids=("state_code", "state_at", "matrix_trace", "convergent", "best_approximation"))
@pytest.mark.parametrize("bad", ("", "x-y", "x / y", "f(x)", "S", "unknown"))
def test_computation_relations_reject_nonterms_and_unbound_variables(relation, arity, bad):
    with pytest.raises(ValueError):
        relation(*((bad,) + ("x",) * (arity - 1)), tag="safe", variables=("x",))


@pytest.mark.parametrize("relation,arity", PUBLIC_RELATIONS, ids=("state_code", "state_at", "matrix_trace", "convergent", "best_approximation"))
@pytest.mark.parametrize("bad_tag", ("", "x-y", "x y", "x.y", "0bad"))
def test_computation_relations_reject_invalid_tags(relation, arity, bad_tag):
    with pytest.raises(ValueError):
        relation(*(("x",) * arity), tag=bad_tag, variables=("x",))


@pytest.mark.parametrize("relation,arity,captured", (
    (candidate.convergent_matrix_state_code_relation, 6, "cfc_left_t"),
    (candidate.convergent_matrix_state_at_relation, 8, "cfc_state_t"),
    (candidate.convergent_matrix_trace_relation, 8, "cfc_tail_t"),
    (candidate.convergent_relation, 4, "cfc_previous_numerator_t"),
    (candidate.best_approximation_second_kind_relation, 4, "cfc_numerator_t"),
))
def test_computation_binders_reject_capture(relation, arity, captured):
    with pytest.raises(ValueError, match="captures"):
        relation(*(("x + " + captured,) + ("x",) * (arity - 1)), tag="t", variables=("x", captured))


def all_binder_cases():
    for relation, arity in PUBLIC_RELATIONS:
        source = relation(*(("x",) * arity), tag="scope", variables=("x",))
        for binder in sorted({name for match in re.finditer(r"\b(?:forall|exists)\s+([^.]*)\.", source) for name in match.group(1).split()}):
            yield relation, arity, binder


@pytest.mark.parametrize("relation,arity,binder", tuple(all_binder_cases()))
def test_every_generated_binder_including_legacy_beta_guards_protects_unused_declared_variables(relation, arity, binder):
    with pytest.raises(ValueError, match="captures"):
        relation(*(("x",) * arity), tag="scope", variables=("x", binder))


def test_binder_hygiene_matrix_explicitly_covers_nested_legacy_beta_helpers():
    binders = {case[2] for case in all_binder_cases()}
    assert any(name.startswith("ff_h_") for name in binders)
    assert any(name.startswith("ff_q_") for name in binders)
    assert any(name.startswith("cfc_") for name in binders)
    assert any(name.startswith("cfba_gap_") for name in binders)


@pytest.mark.parametrize("bad", (1, 0, None, "signed", (), []))
def test_signed_domain_flag_requires_an_exact_boolean(bad):
    with pytest.raises(ValueError):
        candidate.best_approximation_second_kind_relation("a", "b", "u", "v", tag="safe", variables=("a", "b", "u", "v"), signed=bad)


def test_convergent_definition_contains_only_actual_computation_and_positive_denominator():
    actual = candidate.convergent_relation("s", "i", "u", "v", tag="audit", variables=("s", "i", "u", "v"))
    expected = "exists U V H E. ~(v = 0) /\\ (" + candidate._trace("s", "H", "E", "S i", "u", "U", "v", "V", "independent") + ")"
    assert parse_formula_with_names(actual) == parse_formula_with_names(expected)
    assert "~(u = 0)" not in actual
    assert "current_error" not in actual and "previous_error" not in actual
    node = parse_formula_with_names(actual)[0]
    for _ in range(4):
        assert type(node) is Exists
        node = node.body
    assert type(node) is And and type(node.left) is Imp
    assert type(node.right) is Exists


def test_public_natural_endpoint_has_the_exact_g072_domains_and_no_assumed_invariant():
    table = {row.name: row for row in rows()}
    cf = continued_fraction("a", "b", "s", tag="independent_cf")
    cv = candidate.convergent_relation("s", "i", "u", "v", tag="independent_cv", variables=("s", "i", "u", "v"))
    expected = (
        "forall a b s i u v. ((" + cf + ") /\\ (" + cv + ")) -> forall r t C D. ~(t = 0) -> "
        "(exists gap. gap + S t = v) -> ((a * v = b * u + C) \\/ (b * u = a * v + C)) -> "
        "((a * t = b * r + D) \\/ (b * r = a * t + D)) -> exists bound. bound + C = D"
    )
    assert _closed_formula(table["continued_fraction_convergent_best_approximation"].statement) == _closed_formula(expected)


def test_public_signed_endpoint_quantifies_arbitrary_two_component_numerators():
    table = {row.name: row for row in rows()}
    cf = continued_fraction("a", "b", "s", tag="independent_cf")
    cv = candidate.convergent_relation("s", "i", "u", "v", tag="independent_cv", variables=("s", "i", "u", "v"))
    expected = (
        "forall a b s i u v. (" + cf + ") -> (" + cv + ") -> forall rp rn t C D. ~(t = 0) -> "
        "(exists gap. gap + S t = v) -> ((a * v = b * u + C) \\/ (b * u = a * v + C)) -> "
        "((a * t + b * rn = b * rp + D) \\/ (b * rp = (a * t + b * rn) + D)) -> exists bound. bound + C = D"
    )
    assert _closed_formula(table["continued_fraction_convergent_best_approximation_signed"].statement) == _closed_formula(expected)


PRINCIPAL_STATEMENT_SHA256 = {
    "continued_fraction_convergent_best_approximation": "f77356be459116bfcf711c13c7d70777afc2a7a5e93a91f28ee464d07c4bca2c",
    "continued_fraction_convergent_best_approximation_signed": "d1401bdb17320a1fc10ebfa605c42972b850cd596d1a6d114ad82b5be8f5492b",
    "continued_fraction_convergent_exists_unique_at_history_index": "a2350b3a79e730cf6c26001c3c5e8b515a6757a5d32cb64d83cd55853e6e6c5b",
    "continued_fraction_initial_zero_over_one": "f3f23d230d72430e8d5af7462c5bf58a2d931e50d74083053c8d6374153ded00",
    "continued_fraction_has_exact_terminal_convergent": "4f2ff1801b78a9b8142e1e104bea9e49a5251d5c165f2982332e6a70fe966ea0",
    "continued_fraction_adjacent_convergent_determinant": "5666bd5d85b19e815856e29a5c93bfa0c07e9e28b8e9aa651e08e9978dbded41",
    "continued_fraction_convergent_coprime": "dc7cd76880ad898f76cdcc22f0602e7ec51b08c4ac99e1e43afa1dd682fa859b",
}


@pytest.mark.parametrize("name,expected", tuple(PRINCIPAL_STATEMENT_SHA256.items()))
def test_principal_statement_literals_remain_exact(name, expected):
    table = {row.name: row for row in rows()}
    assert sha256(table[name].statement.encode()).hexdigest() == expected


@pytest.mark.parametrize("mutation", ("zero_denominator", "equal_denominator", "no_computation"))
def test_g072_guard_or_computation_mutation_is_rejected(mutation):
    table = {row.name: row for row in rows()}
    row = table["continued_fraction_convergent_best_approximation"]
    if mutation == "zero_denominator":
        source = row.statement.replace("~(cfc_denominator_best_natural = 0) -> ", "", 1)
    elif mutation == "equal_denominator":
        source = row.statement.replace("+ S (cfc_denominator_best_natural)", "+ (cfc_denominator_best_natural)", 1)
    else:
        computation = candidate.convergent_relation("s", "i", "u", "v", tag="best_actual_convergent", variables=("s", "i", "u", "v"))
        source = row.statement.replace(computation, "v = v", 1)
    assert source != row.statement
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=source),), core=core() | table)


def pair(left, right):
    return (left + right) * (left + right + 1) + 2 * right


def list_code(values):
    code = 0
    for value in reversed(values):
        code = 1 + pair(value, code)
    return code


def quotient_list(a, b):
    result = []
    while b:
        q, r = divmod(a, b)
        result.append(q)
        a, b = b, r
    return result


def prefix_matrix(quotients):
    u, U, v, V = 1, 0, 0, 1
    for q in reversed(quotients):
        u, U, v, V = q * u + v, q * U + V, u, U
    return u, U, v, V


@pytest.mark.parametrize("a,b", tuple((a, b) for a in range(1, 17) for b in range(1, 17)))
def test_actual_prefix_semantics_match_forward_convergents_and_full_signed_comparison(a, b):
    quotients = quotient_list(a, b)
    pm2, pm1, qm2, qm1 = 0, 1, 1, 0
    for i, coefficient in enumerate(quotients):
        numerator = coefficient * pm1 + pm2
        denominator = coefficient * qm1 + qm2
        u, U, v, V = prefix_matrix(quotients[: i + 1])
        assert (u, U, v, V) == (numerator, pm1, denominator, qm1)
        assert v > 0 and gcd(u, v) == 1 and abs(u * V - U * v) == 1
        error = abs(a * v - b * u)
        previous_error = abs(a * V - b * U)
        assert error < previous_error <= b
        for t in range(1, v):
            for r in range(-3, u + 4):
                assert error <= abs(a * t - b * r)
        pm2, pm1, qm2, qm1 = pm1, numerator, qm1, denominator
    assert a * denominator == b * numerator
    if a < b:
        assert quotients[0] == 0 and prefix_matrix(quotients[:1]) == (0, 1, 1, 0)


@pytest.mark.parametrize("a,b", ((1 << 80, (1 << 100) + 1), ((1 << 95) + 23, (1 << 70) + 19), (610, 987)), ids=("large_below_one", "large_above_one", "fibonacci"))
def test_large_and_long_history_cases(a, b):
    quotients = quotient_list(a, b)
    for k in range(1, len(quotients) + 1):
        u, U, v, V = prefix_matrix(quotients[:k])
        error = abs(a * v - b * u)
        assert error < abs(a * V - b * U) <= b
        for t in sorted({1, 2, 3, max(1, v - 1)}):
            if t < v:
                nearest = (a * t) // b
                for r in (-2, -1, 0, nearest, nearest + 1):
                    assert error <= abs(a * t - b * r)
    assert a * v == b * u


def beta_encode(values):
    # Independent numerical witness construction for semantics only. The HA
    # existence authority is the separately replayed beta-prefix proof body.
    scale = factorial(len(values)) * (max(values) + 1)
    code, product = 0, 1
    for i, value in enumerate(values):
        modulus = 1 + (i + 1) * scale
        correction = ((value - code) * pow(product, -1, modulus)) % modulus
        code += product * correction
        product *= modulus
    return code, scale


def matrix_state_code(s, matrix):
    u, U, v, V = matrix
    return pair(s, pair(pair(u, U), pair(v, V)))


@pytest.mark.parametrize("a,b", ((1, 2), (2, 1), (13, 5), (19, 7), (5, 12), (1, 1)))
def test_concrete_old_and_new_beta_histories_satisfy_the_actual_encoded_equations(a, b):
    quotients = quotient_list(a, b)
    actual_a, actual_b = a, b
    forward = []
    for i in range(len(quotients) + 1):
        forward.append((actual_a, actual_b, list_code(quotients[i:])))
        if actual_b:
            actual_a, actual_b = actual_b, actual_a % actual_b
    reverse = list(reversed(forward))
    old_values = [pair(x, pair(y, s)) for x, y, s in reverse]
    old_h, old_e = beta_encode(old_values)
    assert reverse[0] == (gcd(a, b), 0, 0)
    assert reverse[-1] == (a, b, list_code(quotients))
    assert all(old_h % (1 + (i + 1) * old_e) == value for i, value in enumerate(old_values))
    for before, after in zip(reverse, reverse[1:]):
        dividend, divisor, head = after
        old_dividend, remainder, tail = before
        quotient = (dividend - remainder) // divisor
        assert divisor == old_dividend and dividend == divisor * quotient + remainder and remainder < divisor
        assert head == 1 + pair(quotient, tail)
    for k in range(len(quotients) + 1):
        tail = list_code(quotients[k:])
        matrix = (1, 0, 0, 1)
        states = [(tail, matrix)]
        for coefficient in reversed(quotients[:k]):
            u, U, v, V = matrix
            matrix = (coefficient * u + v, coefficient * U + V, u, U)
            tail = 1 + pair(coefficient, tail)
            states.append((tail, matrix))
        values = [matrix_state_code(s, matrix) for s, matrix in states]
        h, e = beta_encode(values)
        assert all(h % (1 + (j + 1) * e) == value for j, value in enumerate(values))
        assert states[-1] == (list_code(quotients), prefix_matrix(quotients[:k]))


def test_exact_old_planning_counterexample_one_half():
    assert quotient_list(1, 2) == [0, 2]
    assert list_code([0, 2]) == 71
    assert prefix_matrix([0]) == (0, 1, 1, 0)
    assert prefix_matrix([0, 2]) == (1, 0, 2, 1)
    assert 0 * 1 == 0  # Actual initial numerator, not a suppressed degenerate case.
    assert not (0 > 0 and 1 > 0)  # The old planning-only Convergent predicate was false here.
