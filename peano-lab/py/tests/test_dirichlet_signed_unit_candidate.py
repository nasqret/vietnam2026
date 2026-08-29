"""Independent scalar contracts and genuine ordinary-HA signed-unit checks.

Numerical cases are diagnostics only.  Proof authority for each candidate
body comes from the unchanged original kernel, with the exact declared
dependencies curried as hypotheses; complete closure is a separate gate.
"""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import dirichlet_signed_unit_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_mobius_value_candidate import core


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

EXPECTED = (
    (176, 48, 165), (672, 44, 623), (25, 11, 25),
    (57, 24, 57), (33, 20, 33), (67, 25, 67),
    (62, 28, 62), (27, 18, 27), (55, 26, 55),
)
STATEMENT_PINS = {
    "dirichlet_signed_unit_self_product": "780d9dd89725bbab5d855c954b515efebcc63f1144231844332dd12d51bde395",
    "dirichlet_signed_unit_product_classification": "4c6820280f2a7c6e35eb66968d2f4819ea3276baa1af24e495ec1626e963db08",
    "dirichlet_signed_unit_inverse_iff": "f1fc281c8f5c286aecce35c64d5751a85fdf238016f38868ac8dace9068d96b6",
    "dirichlet_signed_add_cancel_left": "70b035df7d0471a236eab2a9626f6df1a66c238b391acbf60f2389be001ae71a",
    "dirichlet_signed_add_solve": "f0508996bd81d5bd73e7917ca25d84471aec82c9cf856983a4a8cd9f754844b4",
    "dirichlet_signed_unit_multiply_involution": "847ae8b4b31d190bea6a648badd1059445bcc8e107b1d2527da3519ecaac52a0",
    "dirichlet_signed_unit_multiply_cancel_right": "4f10c8764cd2c581b41cc65310db45eeb7e61855aac510ccf57c6f56ca38ac5a",
    "dirichlet_signed_unit_affine_solve": "3c8f3184a683b282d0ef7f8d9f3671f71a9b9509599ff78b4ff47623c65660e4",
    "dirichlet_signed_unit_affine_unique": "68b300d496090f0911613338c333747776a606c71fd28d4c82849bfca1c32d11",
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_dirichlet_signed_unit_candidate_theorems(TheoremSpec)


def table():
    # The inherited helper authenticates the exact ac7111... catalog bytes,
    # 3,222 Alpha entries and Stable 432. No source-derived parent is trusted.
    return core() | {row.name: row for row in rows()}


def _conjunction(*formulas):
    if len(formulas) == 1:
        return formulas[0]
    return f"(({formulas[0]}) /\\ ({_conjunction(*formulas[1:])}))"


def expected_unit(u):
    return f"(({u})=2 \\/ ({u})=1)"


def expected_decode(z, p, n, tag):
    half = "independent_half_" + tag
    return (f"((({z})=2*({p}) /\\ ({n})=0) \\/ exists {half}. "
            f"((({z})=2*{half}+1 /\\ ({p})=0) /\\ ({n})=S {half}))")


def expected_operation(a, b, c, tag, *, multiply):
    p, n, q, m, u, v = ("independent_" + name + "_" + tag for name in ("p", "n", "q", "m", "u", "v"))
    equation = (f"({p}*{q}+{n}*{m})+{v}=({p}*{m}+{n}*{q})+{u}" if multiply
                else f"({p}+{q})+{v}=({n}+{m})+{u}")
    return f"exists {p} {n} {q} {m} {u} {v}. " + _conjunction(
        expected_decode(a, p, n, tag + "first"), expected_decode(b, q, m, tag + "second"),
        expected_decode(c, u, v, tag + "output"), equation,
    )


def expected_mul(a, b, c, tag):
    return expected_operation(a, b, c, tag, multiply=True)


def expected_add(a, b, c, tag):
    return expected_operation(a, b, c, tag, multiply=False)


def expected_statements():
    return (
        f"forall u. ({expected_unit('u')}) -> ({expected_mul('u','u','2','self')})",
        f"forall a b. ({expected_mul('a','b','2','classification')}) -> ((a=2 /\\ b=2) \\/ (a=1 /\\ b=1))",
        f"forall u. ((exists v. ({expected_mul('u','v','2','inverse')})) -> ({expected_unit('u')})) /\\ "
        f"(({expected_unit('u')}) -> exists v. ({expected_mul('u','v','2','inverse_back')}))",
        f"forall r a b e. ({expected_add('r','a','e','cancel_first')}) -> ({expected_add('r','b','e','cancel_second')}) -> a=b",
        f"forall r e. exists y. ({expected_add('r','y','e','solve_addend')})",
        f"forall u a b. ({expected_unit('u')}) -> ({expected_mul('a','u','b','involute_first')}) -> ({expected_mul('b','u','a','involute_second')})",
        f"forall u a b z. ({expected_unit('u')}) -> ({expected_mul('a','u','z','cancel_mul_first')}) -> ({expected_mul('b','u','z','cancel_mul_second')}) -> a=b",
        f"forall r u e. ({expected_unit('u')}) -> exists x y. "
        + _conjunction(expected_mul('x','u','y','affine_multiply'), expected_add('r','y','e','affine_add')),
        f"forall r u e a b c d. ({expected_unit('u')}) -> ({expected_mul('a','u','b','unique_first_product')}) -> "
        f"({expected_add('r','b','e','unique_first_sum')}) -> ({expected_mul('c','u','d','unique_second_product')}) -> "
        f"({expected_add('r','d','e','unique_second_sum')}) -> a=c /\\ b=d",
    )


@pytest.mark.parametrize("row,expected", tuple(zip(rows(), expected_statements())), ids=[row.name for row in rows()])
def test_every_public_theorem_has_independently_expanded_exact_ast(row, expected):
    _assert_same_ast(_closed_formula(row.statement), _closed_formula(expected))


@pytest.mark.parametrize("row", rows(), ids=lambda row: row.name)
def test_original_kernel_body(row):
    try:
        checked = replay_candidate_bodies((row,), core=table())[0]
        assert (checked.proof_nodes, checked.proof_depth, checked.proof_objects) == EXPECTED[rows().index(row)]
        assert checked.name == row.name
        assert checked.proof_depth <= 256
        assert checked.proof_objects <= checked.proof_nodes
    finally:
        gc.collect()


def test_exact_topology_metrics_and_all_statement_pins():
    assert len(rows()) == 9
    assert sum(len(row.dependencies) for row in rows()) == 36
    assert sum(len(row.script) for row in rows()) == 401
    assert sha256("\n".join(row.name for row in rows()).encode()).hexdigest() == "5fa7ad76083b6bd935f66698b4418e6ce85720b134ce19b40696ab87433a116c"
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        assert all(re.search(r"(?<![\w'])" + re.escape(name) + r"(?![\w'])", "\n".join(row.script))
                   for name in row.dependencies)
        assert not any(command.startswith(("use ", "admit", "sorry", "DNE", "ring")) for command in row.script)
        available.add(row.name)
    assert {row.name: sha256(row.statement.encode()).hexdigest() for row in rows()} == STATEMENT_PINS


def test_all_nine_statements_are_novel_against_3756_prior_rows_and_each_other():
    from constructive_dirichlet_inverse_support import PRIOR_THEOREM_COUNT, statement_duplicates
    assert PRIOR_THEOREM_COUNT == 3756
    assert statement_duplicates(rows()) == ()


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
def test_poisoned_dependency_cannot_substitute_for_exact_statement(row, dependency):
    altered = table()
    altered[dependency] = replace(altered[dependency], statement="0=1")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,), core=altered)


@pytest.mark.parametrize("value", ("u", "u+1", "u*u", "S (u+v)", "0", "1", "2",
                                  "12345678901234567890123456789012345678901234567890"))
def test_public_unit_definition_accepts_explicit_context_compound_and_large_terms(value):
    context = ("u", "v", "unused")
    formula = candidate.dirichlet_signed_unit_relation(value, tag="contract", variables=context)
    _assert_same_ast(parse_formula_in_context(formula, list(context)), parse_formula_in_context(expected_unit(value), list(context)))


def test_unit_definition_has_no_hidden_binders_or_unused_context_capture():
    context = ("u", "unused", "sto_left_positive_contract", "mps_positive_contract", "dsu_unit_contract")
    actual = candidate.dirichlet_signed_unit_relation("u+unused", tag="contract", variables=context)
    assert not re.search(r"\b(?:exists|forall)\b", actual)
    _assert_same_ast(parse_formula_in_context(actual, list(context)), parse_formula_in_context(expected_unit("u+unused"), list(context)))


@pytest.mark.parametrize("tag", ("", "0bad", "forall", "exists", "a.b", "x -> 0=1", None))
def test_hostile_definition_tags_are_rejected(tag):
    with pytest.raises((ValueError, TypeError)):
        candidate.dirichlet_signed_unit_relation("u", tag=tag, variables=("u",))


@pytest.mark.parametrize("context", ((), ("u", "u"), ("u", "forall"), ("u", "bad name"), ["u"], None))
def test_invalid_or_ambiguous_declared_contexts_are_rejected(context):
    with pytest.raises((ValueError, TypeError)):
        candidate.dirichlet_signed_unit_relation("u", tag="safe", variables=context)


@pytest.mark.parametrize("term", ("undeclared", "u+unknown", "u=2", "exists k. k=0", "", "u;0"))
def test_undeclared_variables_and_formula_injection_are_rejected(term):
    with pytest.raises((ValueError, TypeError)):
        candidate.dirichlet_signed_unit_relation(term, tag="safe", variables=("u", "unused"))


@pytest.mark.parametrize("mutation", ("positive_and_negative_swapped", "target_minus_one", "zero_claimed_unit", "unrestricted_affine", "nonunit_affine"))
def test_stronger_or_miscoded_contracts_are_not_proved(mutation):
    if mutation in ("positive_and_negative_swapped", "target_minus_one"):
        row = rows()[1]
        changed = (f"forall a b. ({expected_mul('a','b','2','wrong_sign')}) -> ((a=2 /\\ b=1) \\/ (a=1 /\\ b=2))"
                   if mutation == "positive_and_negative_swapped" else
                   f"forall a b. ({expected_mul('a','b','1','wrong_output')}) -> ((a=2 /\\ b=2) \\/ (a=1 /\\ b=1))")
    elif mutation == "zero_claimed_unit":
        row = rows()[0]
        changed = f"forall u. (u=0) -> ({expected_mul('u','u','2','zero_nonunit')})"
    else:
        row = rows()[7]
        premises = "" if mutation == "unrestricted_affine" else "(u=4) -> "
        changed = "forall r u e. " + premises + "exists x y. " + _conjunction(
            expected_mul("x", "u", "y", "bad_affine_mul"), expected_add("r", "y", "e", "bad_affine_add"))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, statement=changed),), core=table())


def decode_components(code):
    return (code // 2, 0) if code % 2 == 0 else (0, code // 2 + 1)


def decode_integer(code):
    p, n = decode_components(code)
    return p - n


def encode_integer(value):
    return 2 * value if value >= 0 else -2 * value - 1


def actual_operation(a, b, c, *, multiply):
    """Evaluate the actual normalized witness equations, not a unit oracle."""
    ap, an = decode_components(a)
    bp, bn = decode_components(b)
    cp, cn = decode_components(c)
    return ((ap * bp + an * bn) + cn == (ap * bn + an * bp) + cp if multiply
            else (ap + bp) + cn == (an + bn) + cp)


def test_canonical_codes_and_exhaustive_small_product_classification_diagnostic():
    assert [decode_integer(code) for code in (0, 1, 2, 3, 4)] == [0, -1, 1, -2, 2]
    for a in range(65):
        for b in range(65):
            actual = actual_operation(a, b, 2, multiply=True)
            assert actual == ((a == 2 and b == 2) or (a == 1 and b == 1))


@pytest.mark.parametrize("r", (0, 1, 2, 3, 4, 17, 28))
@pytest.mark.parametrize("u", (2, 1))
@pytest.mark.parametrize("e", (0, 1, 2, 5, 12))
def test_actual_affine_witness_equations_include_zero_and_both_signs(r, u, e):
    y = encode_integer(decode_integer(e) - decode_integer(r))
    x = encode_integer(decode_integer(y) * decode_integer(u))
    assert actual_operation(x, u, y, multiply=True)
    assert actual_operation(r, y, e, multiply=False)
    for other in range(25):
        other_y = encode_integer(decode_integer(other) * decode_integer(u))
        if actual_operation(r, other_y, e, multiply=False):
            assert (other, other_y) == (x, y)


def test_zero_factor_cannot_be_cancelled_and_nonunits_do_not_solve_every_affine_equation():
    assert actual_operation(2, 0, 0, multiply=True)
    assert actual_operation(1, 0, 0, multiply=True)
    assert 2 != 1
    for nonunit in (0, 3, 4, 5, 6):
        for x in range(101):
            y = encode_integer(decode_integer(x) * decode_integer(nonunit))
            assert not actual_operation(0, y, 2, multiply=False)


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
    arguments = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    if arguments.pytest_select is not None:
        status = pytest.main(["-q", "--tb=short", __file__, "-k", arguments.pytest_select])
    else:
        selected = (tuple(row for row in rows() if row.name == arguments.body) if arguments.body
                    else rows()[arguments.start:arguments.start + arguments.count])
        if not selected:
            raise SystemExit("unknown theorem body")
        for row in selected:
            test_original_kernel_body(row)
            print(json.dumps({"name": row.name, "metrics": EXPECTED[rows().index(row)]}), flush=True)
        status = 0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    assert peak <= 1536 * 1024 * 1024
    print(json.dumps({"status": status, "seconds": time.monotonic() - started, "peak_rss_bytes": peak}), flush=True)
    raise SystemExit(status)
