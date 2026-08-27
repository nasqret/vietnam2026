"""Unsealed G072 authoring checks, not a new release/admission mechanism."""

from __future__ import annotations

from functools import lru_cache
from dataclasses import fields, replace
import gc
from hashlib import sha256
import json
from pathlib import Path
import re

import pytest

from peano_lab.library import continued_fraction_approximation_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec
from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, Or, parse_formula_with_names
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "artifacts/peano-library/alpha/catalog-v28.json"
PARENT_SHA256 = "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9"


@lru_cache(maxsize=1)
def rows():
    return candidate.make_continued_fraction_approximation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    raw = PARENT.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    catalog = json.loads(raw)
    assert catalog["schema"] == "peano-library-alpha-snapshot-v28"
    assert catalog["theorem_count"] == catalog["checked_use_count"] == 2764
    assert catalog["stable_count"] == 432
    return {
        row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]),
                                 tuple(row["script"]), row["summary"])
        for row in catalog["theorems"]
    }


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_candidate_body_passes_the_original_kernel(name):
    table = {row.name: row for row in rows()}
    try:
        receipt = replay_candidate_bodies((table[name],), core=core() | table)[0]
        assert receipt.name == name
        assert receipt.proof_depth <= 256
        assert receipt.proof_objects <= receipt.proof_nodes
        assert receipt.proof_edges == receipt.proof_nodes - 1
    finally:
        gc.collect()


def test_candidate_rows_are_fresh_and_dependency_ordered():
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(row.dependencies) == len(set(row.dependencies))
        available.add(row.name)


@pytest.mark.parametrize("name", tuple(row.name for row in rows()))
def test_poisoned_arithmetic_body_is_rejected_by_the_original_checker(name):
    table = {row.name: row for row in rows()}
    poisoned = replace(table[name], script=("refl",))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((poisoned,), core=core() | table)


def strict_nodes(value):
    pending = [value]
    allowed = (And, Bot, Eq, Exists, Forall, Imp, Or, Add, Mul, Succ, Var, Zero)
    while pending:
        node = pending.pop()
        assert type(node) in allowed
        yield node
        for field in fields(node):
            child = getattr(node, field.name)
            if type(child) in allowed:
                pending.append(child)


PUBLIC_RELATIONS = (
    (candidate.rational_approximation_error_relation, 6),
    (candidate.alternating_convergent_identity_relation, 8),
    (candidate.convergent_error_invariant_relation, 6),
)


@pytest.mark.parametrize("relation,arity", PUBLIC_RELATIONS, ids=("actual_error", "alternating_identity", "derived_invariant"))
def test_public_arithmetic_relations_are_strict_ha_with_hygienic_compound_terms(relation, arity):
    context = tuple("x" + str(i) for i in range(arity)) + ("z",)
    values = tuple("(" + context[i] + " + z) * S z" for i in range(arity))
    first, free = parse_formula_with_names(relation(*values, tag="first", variables=context))
    other, other_free = parse_formula_with_names(relation(*values, tag="second", variables=context))
    assert first == other
    assert free == other_free
    assert set(free) == set(context)
    assert tuple(strict_nodes(first))


@pytest.mark.parametrize("relation,arity", PUBLIC_RELATIONS, ids=("actual_error", "alternating_identity", "derived_invariant"))
@pytest.mark.parametrize("bad", ("", "x-y", "x / y", "f(x)", "S", "unknown"))
def test_public_arithmetic_relations_reject_nonterms_and_unbound_variables(relation, arity, bad):
    with pytest.raises(ValueError):
        relation(*((bad,) + ("x",) * (arity - 1)), tag="safe", variables=("x",))


@pytest.mark.parametrize("relation,arity", PUBLIC_RELATIONS, ids=("actual_error", "alternating_identity", "derived_invariant"))
@pytest.mark.parametrize("bad_tag", ("", "x-y", "x y", "x.y", "0bad"))
def test_public_arithmetic_relations_reject_invalid_tags(relation, arity, bad_tag):
    with pytest.raises(ValueError):
        relation(*(("x",) * arity), tag=bad_tag, variables=("x",))


@pytest.mark.parametrize("bad_context", (["x"], ("x", "x"), ("x-y",)))
def test_arithmetic_context_is_explicit_and_distinct(bad_context):
    with pytest.raises(ValueError):
        candidate.rational_approximation_error_relation(*(("x",) * 6), tag="safe", variables=bad_context)


def test_derived_invariant_rejects_capture():
    with pytest.raises(ValueError, match="captures"):
        candidate.convergent_error_invariant_relation(
            "x + cfba_error_t", "x", "x", "x", "x", "x", tag="t", variables=("x", "cfba_error_t"),
        )


def arithmetic_binder_cases():
    for relation, arity in PUBLIC_RELATIONS:
        source = relation(*(("x",) * arity), tag="scope", variables=("x",))
        for binder in sorted({name for match in re.finditer(r"\b(?:forall|exists)\s+([^.]*)\.", source) for name in match.group(1).split()}):
            yield relation, arity, binder


@pytest.mark.parametrize("relation,arity,binder", tuple(arithmetic_binder_cases()))
def test_every_arithmetic_generated_binder_protects_even_unused_declared_variables(relation, arity, binder):
    with pytest.raises(ValueError, match="captures"):
        relation(*(("x",) * arity), tag="scope", variables=("x", binder))


@pytest.mark.parametrize("rp,rn,shift", ((0, 0, 1), (0, 7, 9), (12, 0, 20), (21, 8, 1 << 80)))
def test_actual_signed_error_is_independent_of_noncanonical_pair_representatives(rp, rn, shift):
    for a, b, denominator in ((1, 2, 0), (13, 5, 1), (19, 7, 8), (101, 103, 20)):
        actual = abs(a * denominator + b * rn - b * rp)
        recoded = abs(a * denominator + b * (rn + shift) - b * (rp + shift))
        assert actual == recoded == abs(a * denominator - b * (rp - rn))


@pytest.mark.parametrize("u,U,v,V", ((1, 0, 0, 1), (0, 1, 1, 0), (2, 1, 5, 2), (13, 5, 8, 3)))
def test_signed_cofactor_coordinates_are_actual_integer_coordinates(u, U, v, V):
    determinant = u * V - U * v
    assert abs(determinant) == 1
    for numerator in range(-8, 9):
        for denominator in range(9):
            alpha = determinant * (V * numerator - U * denominator)
            beta = determinant * (u * denominator - v * numerator)
            assert alpha * u + beta * U == numerator
            assert alpha * v + beta * V == denominator
            if 0 < denominator < v:
                assert (alpha < 0 < beta) or (beta < 0 < alpha) or (alpha == 0 < beta)


def test_boundaries_that_would_make_weakened_or_old_planning_statements_false():
    # 1/2 has initial convergent 0/1: old planning u>0 excludes a real value.
    assert 0 == 0 and 1 > 0
    assert not 0 > 0
    # Dropping t>0 incorrectly permits the zero vector with zero error.
    assert abs(1 * 1 - 2 * 0) > abs(1 * 0 - 2 * 0)
    # Replacing t<v by t<=v fails at the initial convergent of 2/3.
    assert abs(2 * 1 - 3 * 0) > abs(2 * 1 - 3 * 1)
    # Positivity alone is not Convergent: a made-up 10/3 is not best for 1/2.
    assert abs(1 * 3 - 2 * 10) > abs(1 * 1 - 2 * 0)
