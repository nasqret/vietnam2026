"""Exact full Cauchy--Davenport semantics and bounded original-HA checks."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import re

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import cauchy_davenport_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula

from test_finite_modular_set_candidate import (
    core as parent_core, rows as foundation_rows, manual_at, manual_iff,
    manual_lt, manual_member, manual_mod,
)


EXPECTED_NAMES = (
    "finite_modular_add_modulus", "prime_modular_additive_orbit_hits", "finite_modular_orbit_member_or_boundary",
    "prime_modular_set_translation_boundary_exists", "finite_modular_dyson_upper_from_union",
    "finite_modular_dyson_lower_from_pullback", "finite_modular_dyson_transform_exists",
    "finite_modular_dyson_upper_member", "finite_modular_dyson_lower_subset", "finite_modular_dyson_lower_zero_member",
    "finite_modular_dyson_lower_boundary_nonmember", "finite_modular_dyson_sum_cover", "finite_modular_dyson_strict_sizes",
    "finite_modular_zero_sum_left_subset", "finite_modular_singleton_cover_bound", "prime_modular_normalized_boundary_exists",
    "prime_cauchy_davenport_normalized_bounded_induction", "prime_cauchy_davenport_normalized_cover_bound",
    "finite_modular_pullback_zero_member", "finite_modular_opposite_translates_sum_cover", "prime_cauchy_davenport_cover_bound",
    "prime_cauchy_davenport_sumset_bound", "prime_cauchy_davenport_sumset_exists",
)
EXPECTED_NAMES_SHA256 = "bc5d1ae5154493dd5f86c8606084cb7bfc087070dc36be11de3c2ce7c309d86e"
EXPECTED_MAJOR_STATEMENTS = {
    "finite_modular_dyson_transform_exists": "b26bc5fc26d6f7f8f12183a0805b69b6d9c2f93c94727641d1bd9b89be09b012",
    "prime_cauchy_davenport_sumset_bound": "634e3a5403ad025cef1e894dc2b9c3401691bb84bb57c2b70cb3aba185b806fb",
    "prime_cauchy_davenport_sumset_exists": "7f2babcbea49f9ebe8e3a5d2339d0009d16d61afbe33341fcf7b951ede80b6e1",
}
EXPECTED_PROOF_NODES = (27,107,161,61,83,163,182,24,20,36,109,120,155,37,63,117,384,84,40,114,156,104,76)
EXPECTED_PROOF_DEPTHS = (13,34,44,31,38,42,59,17,18,22,30,42,50,23,33,47,78,50,21,47,50,56,41)


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_cauchy_davenport_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    result = dict(parent_core())
    for row in foundation_rows():
        assert row.name not in result and set(row.dependencies) <= set(result)
        result[row.name] = row
    return result


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_exact_twenty_three_theorem_cauchy_davenport_frontier() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert len(rows()) == 23
    assert sum(len(row.dependencies) for row in rows()) == 99
    assert sum(len(row.script) for row in rows()) == 1698


def test_dyson_and_orbit_dependency_dag_contains_no_oracles_or_unused_edges() -> None:
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= available
        assert all(re.search(r"(?<![a-zA-Z0-9_])" + re.escape(name) + r"(?![a-zA-Z0-9_])", "\n".join(row.script)) for name in row.dependencies)
        assert not any(command.startswith(("admit", "sorry", "ring", "DNE", "use ")) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)
    table = {row.name: row for row in rows()}
    induction = table["prime_cauchy_davenport_normalized_bounded_induction"]
    assert induction.script[0] == "induction N"
    assert set(induction.dependencies) >= {"finite_modular_dyson_transform_exists", "finite_modular_dyson_strict_sizes", "finite_modular_dyson_sum_cover"}
    assert "induction n" in table["finite_modular_orbit_member_or_boundary"].script
    assert "prime_bounded_nonzero_mod_inverse" in table["prime_modular_additive_orbit_hits"].dependencies
    assert "finite_modular_sumset_exists" in table["prime_cauchy_davenport_sumset_exists"].dependencies


@pytest.mark.parametrize("name,expected", EXPECTED_MAJOR_STATEMENTS.items())
def test_full_unrestricted_cauchy_davenport_statement_is_pinned(name: str, expected: str) -> None:
    row = next(row for row in rows() if row.name == name)
    assert sha256(row.statement.encode()).hexdigest() == expected


def test_all_cauchy_davenport_bodies_pass_the_original_intuitionistic_kernel() -> None:
    actual = receipts()
    assert tuple(row.name for row in actual) == EXPECTED_NAMES
    assert tuple(row.proof_nodes for row in actual) == EXPECTED_PROOF_NODES
    assert tuple(row.proof_depth for row in actual) == EXPECTED_PROOF_DEPTHS
    assert sum(row.proof_nodes for row in actual) == 2423
    assert max(row.proof_depth for row in actual) == 78


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_cauchy_davenport_proofs_fail_closed(name: str) -> None:
    row = next(row for row in rows() if row.name == name)
    broken = replace(row, script=("exact invented_cauchy_davenport_authority",))
    with pytest.raises(CandidateBodyError, match="failed at command"):
        replay_candidate_bodies((broken,), core={**core(), **{row.name: row for row in rows()}})


@pytest.mark.parametrize("premise", ("~(k=0) -> ", "~(l=0) -> "))
def test_dropping_either_nonemptiness_guard_is_rejected(premise: str) -> None:
    row = next(row for row in rows() if row.name == "prime_cauchy_davenport_sumset_bound")
    assert premise in row.statement
    broken = replace(row, statement=row.statement.replace(premise,"",1))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((broken,),core={**core(), **{row.name: row for row in rows()}})


def _manual_surfaces():
    boundary = (
        f"({manual_member('b','c','p','a','boundary_source')}) /\\ "
        f"(({manual_lt('r','p','boundary_target')}) /\\ "
        f"(({manual_mod('p','a+d','r','boundary_edge')}) /\\ ~({manual_at('b','c','r','1','boundary_outside')})))"
    )
    # Build explicitly and independently, without the author's private helpers.
    upper_witness = f"exists j. ({manual_member('bb','bc','p','j','upper_source')}) /\\ ({manual_mod('p','j+t','i','upper_shift')})"
    lower_witness = f"exists j. ({manual_member('ab','ac','p','j','lower_source')}) /\\ ({manual_mod('p','i+t','j','lower_shift')})"
    upper_condition = f"({manual_at('ab','ac','i','1','upper_A')}) \\/ ({upper_witness})"
    lower_condition = f"({manual_at('bb','bc','i','1','lower_B')}) /\\ ({lower_witness})"
    upper = f"forall i. ({manual_lt('i','p','upper_bound')})->({manual_iff(manual_at('ub','uc','i','1','upper_U'),upper_condition)})"
    lower = f"forall i. ({manual_lt('i','p','lower_bound')})->({manual_iff(manual_at('vb','vc','i','1','lower_V'),lower_condition)})"
    return (
        (candidate.modular_translation_boundary_relation, ("b","c","p","d","a","r"), boundary),
        (candidate.modular_dyson_transform_relation, ("ab","ac","bb","bc","ub","uc","vb","vc","p","t"), f"({upper}) /\\ ({lower})"),
        (candidate.cauchy_davenport_bound_relation, ("p","k","l","m"), "(exists first_gap. first_gap+p=m) \\/ (exists second_gap. second_gap+(k+l)=S m)"),
    )


@pytest.mark.parametrize("helper,arguments,expected", _manual_surfaces())
def test_boundary_dyson_and_sharp_bound_match_independent_primitive_definitions(helper, arguments, expected) -> None:
    context = list(arguments)
    actual = helper(*arguments,tag="first")
    assert parse_formula_in_context(actual,context) == parse_formula_in_context(expected,context)
    assert parse_formula_in_context(actual,context) == parse_formula_in_context(helper(*arguments,tag="second"),context)
    assert not any(symbol in actual for symbol in ("Dyson(", "Card(", "Boundary(", "min(", " - "))


@pytest.mark.parametrize("helper,arguments,expected", _manual_surfaces())
def test_cauchy_davenport_definition_arguments_are_hygienic(helper, arguments, expected) -> None:
    del expected
    for index in range(len(arguments)):
        for bad in ("", "S", "forall", "0", "a+b", "two words", "cd_source_first", "fms_v_first", "ff_capture", "fs_capture"):
            invalid = list(arguments)
            invalid[index] = bad
            with pytest.raises(candidate.CauchyDavenportError):
                helper(*invalid,tag="audit")
    invalid = list(arguments)
    invalid[1] = invalid[0]
    with pytest.raises(candidate.CauchyDavenportError,match="distinct"):
        helper(*invalid,tag="audit")


@pytest.mark.parametrize("tag", ("", "S", "forall", "0", "x+y", "two words"))
def test_cauchy_davenport_invalid_tags_fail_closed(tag: str) -> None:
    with pytest.raises(candidate.CauchyDavenportError):
        candidate.cauchy_davenport_bound_relation("p","k","l","m",tag=tag)


def _subsets(p: int):
    for mask in range(1 << p):
        yield {i for i in range(p) if mask & (1 << i)}


def _sumset(A: set[int], B: set[int], p: int) -> set[int]:
    return {(a+b) % p for a in A for b in B}


@pytest.mark.parametrize("p", (2,3,5,7))
def test_exhaustive_small_prime_sumsets_normalization_and_genuine_dyson_descent(p: int) -> None:
    # Numerical regression, not formal theorem authority.
    nonempty = tuple(A for A in _subsets(p) if A)
    for A in nonempty:
        for B in nonempty:
            S = _sumset(A,B,p)
            assert len(S) >= min(p,len(A)+len(B)-1)
            bzero = min(B)
            An = {(a+bzero) % p for a in A}
            Bn = {(b-bzero) % p for b in B}
            assert 0 in Bn and len(An) == len(A) and len(Bn) == len(B)
            assert _sumset(An,Bn,p) == S
            if len(Bn) <= 1 or len(S) == p:
                continue
            direction = min(Bn - {0})
            shift = next(a for a in sorted(An) if (a+direction) % p not in An)
            upper = An | {(b+shift) % p for b in Bn}
            lower = {b for b in Bn if (b+shift) % p in An}
            assert upper and 0 in lower and direction not in lower
            assert 0 < len(lower) < len(Bn)
            assert len(upper)+len(lower) == len(An)+len(Bn)
            assert _sumset(upper,lower,p) <= S


@pytest.mark.parametrize("p", (2,3,5,7))
def test_first_exit_orbit_is_an_actual_finite_witness(p: int) -> None:
    for A in _subsets(p):
        if not A or len(A) == p:
            continue
        start = min(A)
        outside = min(set(range(p)) - A)
        for direction in range(1,p):
            steps = ((outside-start) * pow(direction,-1,p)) % p
            assert steps > 0
            orbit = tuple((start+n*direction) % p for n in range(steps+1))
            assert orbit[0] in A and orbit[-1] == outside and outside not in A
            first_exit = next(n for n in range(1,len(orbit)) if orbit[n] not in A)
            assert orbit[first_exit-1] in A
            assert (orbit[first_exit-1]+direction) % p == orbit[first_exit]


@pytest.mark.parametrize("p", (2,3,5,7,11))
def test_bound_is_sharp_for_intervals_and_subtraction_free_form_is_exact(p: int) -> None:
    for k in range(1,p+1):
        for l in range(1,p+1):
            assert len(_sumset(set(range(k)),set(range(l)),p)) == min(p,k+l-1)
            for m in range(p+1):
                assert (m >= min(p,k+l-1)) == (p <= m or k+l <= m+1)


@pytest.mark.parametrize("p,A", ((6,{0,3}),(8,{0,4}),(9,{0,3,6})))
def test_composite_moduli_are_a_real_counterexample_to_dropping_primality(p: int, A: set[int]) -> None:
    S = _sumset(A,A,p)
    assert len(S) < min(p,2*len(A)-1)
    direction = min(A-{0})
    assert all((a+direction) % p in A for a in A)


def test_both_nonemptiness_guards_are_mathematically_necessary() -> None:
    p = 5
    for A,B in ((set(),{0,1}),({0,1},set())):
        assert len(_sumset(A,B,p)) < min(p,len(A)+len(B)-1)
