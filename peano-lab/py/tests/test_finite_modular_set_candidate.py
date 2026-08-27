"""Actual finite-set semantics and non-admitting original-HA body checks."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from math import factorial, prod
from pathlib import Path
import re

import pytest

from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library import finite_modular_set_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.finite_fold_surface import bit_count
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v26.json"
PARENT_SHA256 = "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534"
EXPECTED_NAMES = (
    "finite_bit_entry_cases", "finite_bit_membership_decidable", "finite_bit_count_positive_member",
    "finite_bit_subset_pointwise_le", "finite_bit_count_subset_le", "finite_add_le_add",
    "finite_add_lt_of_lt_of_le", "finite_add_lt_of_le_of_lt", "finite_sum_entry_le",
    "finite_bit_member_count_nonzero", "finite_sum_pointwise_strict_at", "finite_bit_count_proper_subset_lt",
    "finite_bit_count_missing_zero", "finite_bit_count_two_nonzero_member", "finite_sum_pointwise_balance",
    "finite_bit_product_cases", "finite_bit_intersection_from_product", "finite_bit_intersection_exists",
    "finite_bit_complement_exists", "finite_bit_complement_member_iff", "finite_bit_union_of_complements",
    "finite_bit_union_exists", "finite_bit_zero_one_conflict", "finite_beta_value_one_iff",
    "finite_bit_nonmember_zero", "finite_bit_union_intersection_values", "finite_bit_union_intersection_count_balance",
    "finite_beta_composition_exists", "finite_modular_translation_indices_exists", "finite_modular_translation_index_entry",
    "finite_modular_translation_indices_permutation", "finite_modular_composition_all_bits", "finite_modular_composition_pullback",
    "finite_modular_set_pullback_exists", "finite_bit_zero_nonmember", "finite_modular_residue_exists",
    "finite_modular_additive_complement", "finite_modular_inverse_shift", "finite_modular_pullback_membership_witness",
    "finite_modular_pushforward_membership_witness", "finite_modular_shifted_sum_congruence", "finite_beta_zero_code",
    "finite_bit_empty_count", "finite_partial_sumset_empty", "finite_partial_sumset_succ_absent",
    "finite_partial_sumset_succ_present", "finite_modular_sumset_prefix_exists", "finite_modular_sumset_exists",
    "finite_modular_sumset_cover",
)
EXPECTED_NAMES_SHA256 = "27e2e5f74640a12182409fb60c6828aaa9f2e54bcae68d5cfa3d294c1064049c"
EXPECTED_SUMSET_STATEMENT_SHA256 = "46420a141069c2696880ec30397f7cedaa2c8b7866ddc2791ec2aff0c799a9d9"
EXPECTED_PROOF_NODES = (42,51,36,64,87,54,21,20,103,65,238,116,55,81,264,53,186,126,161,73,163,109,14,45,40,289,298,177,92,42,89,41,255,147,40,32,26,90,60,88,63,40,56,42,94,181,166,98,34)
EXPECTED_PROOF_DEPTHS = (21,24,17,28,50,25,16,15,32,38,58,65,25,25,63,17,31,39,36,22,42,48,10,21,20,26,50,45,38,22,34,24,40,40,23,16,15,25,25,31,24,11,19,22,29,48,58,35,24)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    # This immutable snapshot supplies only the dependency hypotheses.  The
    # closed-kernel certificate and independent Lean checks are separate.
    raw = PARENT.read_bytes()
    assert sha256(raw).hexdigest() == PARENT_SHA256
    catalog = json.loads(raw)
    assert catalog["theorem_count"] == catalog["checked_use_count"] == 2138
    assert catalog["stable_count"] == 432
    assert all(row["checked_use"] for row in catalog["theorems"])
    return {
        row["name"]: TheoremSpec(row["name"], row["statement"], tuple(row["dependencies"]), tuple(row["script"]), row["summary"])
        for row in catalog["theorems"]
    }


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_finite_modular_set_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_exact_finite_set_foundation_inventory() -> None:
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert len(rows()) == 49
    assert sum(len(row.dependencies) for row in rows()) == 156
    assert sum(len(row.script) for row in rows()) == 2928
    root = next(row for row in rows() if row.name == "finite_modular_sumset_exists")
    assert sha256(root.statement.encode()).hexdigest() == EXPECTED_SUMSET_STATEMENT_SHA256


def test_finite_set_dependency_dag_is_additive_and_every_declared_edge_is_used() -> None:
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
    assert "induction l" in table["finite_modular_sumset_prefix_exists"].script
    assert "finite_modular_set_pullback_exists" in table["finite_modular_sumset_prefix_exists"].dependencies
    assert "finite_bit_union_exists" in table["finite_modular_sumset_prefix_exists"].dependencies
    assert "beta_sum_permutation_invariant" in table["finite_modular_set_pullback_exists"].dependencies


def test_all_forty_nine_finite_set_bodies_pass_the_original_kernel() -> None:
    actual = receipts()
    assert tuple(row.name for row in actual) == EXPECTED_NAMES
    assert tuple(row.proof_nodes for row in actual) == EXPECTED_PROOF_NODES
    assert tuple(row.proof_depth for row in actual) == EXPECTED_PROOF_DEPTHS
    assert sum(row.proof_nodes for row in actual) == 4807
    assert max(row.proof_depth for row in actual) == 65
    assert sum(row.dependency_count for row in actual) == 156
    assert sum(row.command_count for row in actual) == 2928


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_finite_set_bodies_fail_closed(name: str) -> None:
    row = next(row for row in rows() if row.name == name)
    broken = replace(row, script=("exact invented_finite_set_authority",))
    with pytest.raises(CandidateBodyError, match="failed at command"):
        replay_candidate_bodies((broken,), core={**core(), **{row.name: row for row in rows()}})


def manual_lt(a: str, b: str, tag: str) -> str:
    return f"exists audit_gap_{tag}. audit_gap_{tag}+S({a})={b}"


def manual_at(b: str, c: str, i: str, a: str, tag: str) -> str:
    modulus = f"S((S({i}))*({c}))"
    return f"((exists audit_height_{tag}. audit_height_{tag}+S({a})={modulus}) /\\ exists audit_quotient_{tag}. {b}=audit_quotient_{tag}*{modulus}+({a}))"


def manual_mod(p: str, a: str, b: str, tag: str) -> str:
    return f"exists audit_left_{tag} audit_right_{tag}. ({a})+{p}*audit_left_{tag}=({b})+{p}*audit_right_{tag}"


def manual_member(b: str, c: str, p: str, i: str, tag: str) -> str:
    return f"(({manual_lt(i,p,tag)}) /\\ ({manual_at(b,c,i,'1',tag)}))"


def manual_iff(a: str, b: str) -> str:
    return f"((({a})->({b})) /\\ (({b})->({a})))"


def _manual_surfaces():
    a = manual_at("ab","ac","i","1","A")
    b = manual_at("bb","bc","i","1","B")
    u = manual_at("ub","uc","i","1","U")
    bound = manual_lt("i","p","i")
    common = ("ab","ac","bb","bc","ub","uc","p")
    union, intersection = f"({a}) \\/ ({b})", f"({a}) /\\ ({b})"
    witness = f"exists i j. ({manual_member('ab','ac','p','i','A')}) /\\ (({manual_member('bb','bc','p','j','B')}) /\\ ({manual_mod('p','i+j','s','sum')}))"
    return (
        (candidate.finite_modular_set_relation, ("b","c","p","k"), bit_count("b","c","p","k",tag="audit_count")),
        (candidate.modular_set_member_relation, ("b","c","p","a"), manual_member("b","c","p","a","member")),
        (candidate.modular_set_subset_relation, ("ab","ac","bb","bc","p"), f"forall i. ({bound})->({a})->({b})"),
        (candidate.modular_set_union_relation, common, f"forall i. ({bound})->({manual_iff(u,union)})"),
        (candidate.modular_set_intersection_relation, common, f"forall i. ({bound})->({manual_iff(u,intersection)})"),
        (candidate.modular_set_pullback_relation, ("ab","ac","ub","uc","p","t"),
         f"forall i j. ({bound})->({manual_lt('j','p','j')})->({manual_mod('p','i+t','j','pull')})->({manual_iff(u,manual_at('ab','ac','j','1','source'))})"),
        (candidate.modular_set_sum_cover_relation, common,
         f"forall i j s. ({bound})->({manual_lt('j','p','j')})->({manual_lt('s','p','s')})->({a})->({manual_at('bb','bc','j','1','Bsum')})->({manual_mod('p','i+j','s','cover')})->({manual_at('ub','uc','s','1','Scover')})"),
        (candidate.modular_set_sum_relation, common,
         f"forall s. ({manual_lt('s','p','s')})->({manual_iff(manual_at('ub','uc','s','1','S'),witness)})"),
    )


@pytest.mark.parametrize("helper,arguments,expected", _manual_surfaces())
def test_all_eight_definitions_match_independently_written_primitive_semantics(helper, arguments, expected) -> None:
    context = list(arguments)
    actual = helper(*arguments, tag="first")
    assert parse_formula_in_context(actual, context) == parse_formula_in_context(expected, context)
    assert parse_formula_in_context(actual, context) == parse_formula_in_context(helper(*arguments, tag="second"), context)
    assert not any(symbol in actual for symbol in ("BitCount(", "FiniteSet(", "SetSum(", "Choice(", "<->"))


def test_partial_sumset_keeps_the_actual_second_index_outside_modular_witness_binders() -> None:
    # This guards the important nested-binder seam: the second summand must
    # remain the actual set index, never a congruence quotient witness.
    expected = (
        f"exists i j. ({manual_member('ab','ac','p','i','first')}) /\\ "
        f"(({manual_member('bb','bc','p','j','second')}) /\\ "
        f"(({manual_lt('j','l','cutoff')}) /\\ ({manual_mod('p','i+j','z','sum')})))"
    )
    arguments = ["ab","ac","bb","bc","p","l","z"]
    for tag in ("partial", "same", "v", "audit"):
        actual = candidate._partial_sums(*arguments,tag=tag)
        assert parse_formula_in_context(actual, arguments) == parse_formula_in_context(expected, arguments)


@pytest.mark.parametrize("helper,arguments,expected", _manual_surfaces())
def test_finite_set_arguments_fail_closed_at_every_position(helper, arguments, expected) -> None:
    del expected
    for index in range(len(arguments)):
        for bad in ("", "S", "forall", "0", "x+y", "two words", "fms_v_first", "ff_capture", "fs_capture"):
            invalid = list(arguments)
            invalid[index] = bad
            with pytest.raises(candidate.FiniteModularSetError):
                helper(*invalid,tag="test")
    invalid = list(arguments)
    invalid[1] = invalid[0]
    with pytest.raises(candidate.FiniteModularSetError, match="distinct"):
        helper(*invalid,tag="test")


@pytest.mark.parametrize("tag", ("", "S", "forall", "0", "x+y", "two words"))
def test_invalid_finite_set_tags_are_rejected(tag: str) -> None:
    with pytest.raises(candidate.FiniteModularSetError):
        candidate.modular_set_member_relation("b","c","p","a",tag=tag)


def _beta_code(bits: tuple[int, ...], *, multiple: int = 0) -> tuple[int,int]:
    scale = 2 * factorial(len(bits))
    moduli = tuple(1 + (i+1)*scale for i in range(len(bits)))
    modulus = prod(moduli)
    code = sum(bit*(modulus//m)*pow(modulus//m,-1,m) for bit,m in zip(bits,moduli)) % modulus
    return code + multiple*modulus, scale


@pytest.mark.parametrize("p", range(1,9))
def test_actual_beta_bitsets_operations_and_unrestricted_translations(p: int) -> None:
    # Numerical regression only; all mathematical authority is in kernel bodies.
    for mask in range(1 << p):
        A = {i for i in range(p) if mask & (1 << i)}
        bits = tuple(int(i in A) for i in range(p))
        code,scale = _beta_code(bits)
        recoded,_ = _beta_code(bits,multiple=2)
        assert tuple(code % (1+(i+1)*scale) for i in range(p)) == bits
        assert tuple(recoded % (1+(i+1)*scale) for i in range(p)) == bits
        assert sum(bits) == len(A)
        complement = set(range(p)) - A
        assert len(A) + len(complement) == p
        for shift in (0,1,p,p+1,3*p+2):
            indices = tuple((i+shift) % p for i in range(p))
            assert len(set(indices)) == p
            pulled = {i for i in range(p) if (i+shift) % p in A}
            assert len(pulled) == len(A)
        B = {i for i in range(p) if i % 2}
        assert len(A | B) + len(A & B) == len(A) + len(B)
        result = set()
        for cutoff in range(p+1):
            assert result == {(a+b) % p for a in A for b in B if b < cutoff}
            if cutoff in B:
                result |= {(a+cutoff) % p for a in A}


def test_empty_and_singleton_modulus_boundaries_of_sumset_constructor() -> None:
    for A in (set(),{0}):
        for B in (set(),{0}):
            S = {(a+b) % 1 for a in A for b in B}
            assert S == ({0} if A and B else set())
    assert all(0 % (1+(i+1)*0) == 0 for i in range(12))
