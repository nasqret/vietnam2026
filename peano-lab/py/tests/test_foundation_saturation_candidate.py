"""Exact first-layer foundation endpoints, without weakening any premise."""

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import foundation_saturation_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.fermat_residue_product_candidate import coprime
from peano_lab.library.fermat_two_squares_factor_fold_candidate import all_prime_factor_prefix
from peano_lab.library.finite_fold_surface import product_relation
from peano_lab.library.ha_canonical_gcd_candidate import is_gcd
from peano_lab.library.ha_signed_bezout_candidate import signed_bezout
from peano_lab.library.theorems import TheoremSpec, _closed_formula


REPO=Path(__file__).resolve().parents[3]
PARENT_SHA256="481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"
EXPECTED_STATEMENTS={
    "foundation_division_exists_unique":"f43569ef56675e5aab556c26ad0606eea4f4de9c1c54078e6c51c3e96ef653ab",
    "foundation_signed_bezout_canonical_gcd":"3d20b5eb4e05f3b50ba301946c3fc791504ef4586ae3d2bed3f2bd58648790a6",
    "foundation_coprime_product_divisor":"4ec0d3dde7c6319356d61d282abed4edd22af6eeffba58e03162a18c4e58de42",
    "foundation_prime_factor_list_exists":"af68e2e841fe13eafddb375135f9f1abde79b0185d5722d3851c0fcf61af56dc",
    "foundation_primes_above_every_bound":"be3aeb8487e6cac71fa3093363e847f3afbdd176e23ebdbb5f003c080f518167",
}


@lru_cache(maxsize=1)
def _rows():
    return candidate.make_foundation_saturation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core():
    raw=(REPO/"artifacts/peano-library/alpha/catalog-v27.json").read_bytes()
    assert sha256(raw).hexdigest()==PARENT_SHA256
    rows=json.loads(raw)["theorems"]
    assert len(rows)==2560 and all(row["checked_use"] for row in rows)
    return {row["name"]:TheoremSpec(row["name"],row["statement"],tuple(row["dependencies"]),tuple(row["script"]),row.get("summary","")) for row in rows}


@lru_cache(maxsize=1)
def _all():
    return _core()|{row.name:row for row in _rows()}


def test_exact_additive_inventory_and_original_kernel_bodies():
    assert tuple(row.name for row in _rows())==tuple(EXPECTED_STATEMENTS)
    assert sha256("\n".join(EXPECTED_STATEMENTS).encode()).hexdigest()=="3fb216ba4a46248e14444b3927af3c5534f930ca0fa2757d7310927ae41751cb"
    available=set(_core())
    for row in _rows():
        assert row.name not in available and set(row.dependencies)<=available
        assert len(set(row.dependencies))==len(row.dependencies)
        assert all(not any(token in command for token in ("DNE","admit","sorry","oracle","axiom")) and not command.startswith("use ") for command in row.script)
        formula,free=parse_formula_with_names(row.statement)
        assert not free and formula==_closed_formula(row.statement)
        available.add(row.name)
    receipts=tuple(replay_candidate_bodies((row,),core=_all())[0] for row in _rows())
    assert tuple(item.proof_nodes for item in receipts)==(39,56,30,23,20)
    assert sum(item.dependency_count for item in receipts)==7
    assert sum(item.command_count for item in receipts)==92
    assert sum(item.proof_nodes for item in receipts)==168
    assert max(item.proof_depth for item in receipts)==33


@pytest.mark.parametrize(("name","digest"),EXPECTED_STATEMENTS.items())
def test_exact_statement_hash(name,digest):
    assert sha256(_all()[name].statement.encode()).hexdigest()==digest


@pytest.mark.parametrize("name",EXPECTED_STATEMENTS)
@pytest.mark.parametrize("mutation",("false_conclusion","truncated_body","removed_dependency","corrupt_dependency"))
def test_negative_proof_mutations(name,mutation):
    row=_all()[name]
    core=_all()
    if mutation=="false_conclusion":
        changed=replace(row,statement=f"({row.statement}) /\\ false")
    elif mutation=="truncated_body":
        changed=replace(row,script=row.script[:-1])
    elif mutation=="removed_dependency":
        changed=replace(row,dependencies=row.dependencies[:-1])
    else:
        changed=row
        dependency=row.dependencies[0]
        core=core|{dependency:replace(core[dependency],statement="0 = 0")}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core)


def test_exact_factor_list_definition_is_not_canonical_or_permuted_by_assumption():
    expected=f"~(n = 0) /\\ (({product_relation('b','c','l','n',tag='product')}) /\\ ({all_prime_factor_prefix('b','c','l',tag='prime')}))"
    actual=candidate.prime_factor_list_relation("n","b","c","l",tag="actual")
    assert parse_formula_with_names(actual)==parse_formula_with_names(expected)
    assert parse_formula_with_names(actual)==parse_formula_with_names(candidate.prime_factor_list_relation("n","b","c","l",tag="other"))
    assert set(parse_formula_with_names(actual)[1])=={"n","b","c","l"}
    assert "Sorted" not in actual and "Permutation" not in actual
    expected_root=f"forall n. ~(n = 0) -> exists l b c. ({expected})"
    assert _closed_formula(expected_root)==_closed_formula(_all()["foundation_prime_factor_list_exists"].statement)


def test_signed_canonical_gcd_keeps_real_coefficients_and_only_gcd_uniqueness():
    expected=f"forall a b. exists g u v. ({is_gcd('g','a','b',tag='g')}) /\\ (({signed_bezout('g','a','b','u','v',tag='signed')}) /\\ forall h. ({is_gcd('h','a','b',tag='h')}) -> h=g)"
    assert _closed_formula(expected)==_closed_formula(_all()["foundation_signed_bezout_canonical_gcd"].statement)


def test_exact_euclid_and_prime_bound_contracts():
    euclid=f"forall a b c. (({coprime('a','b',tag='coprime')}) /\\ (exists q. b*c=a*q)) -> exists q. c=a*q"
    unbounded=f"forall B. exists p. ({prime('p',tag='prime')}) /\\ (exists h. h+S B=p)"
    assert _closed_formula(euclid)==_closed_formula(_all()["foundation_coprime_product_divisor"].statement)
    assert _closed_formula(unbounded)==_closed_formula(_all()["foundation_primes_above_every_bound"].statement)


@pytest.mark.parametrize("position",range(4))
@pytest.mark.parametrize("fragment",("","S","forall","n+b","0","x;y","fsat_gap_test","ff_u_test","ftsf_index_test","frm_prime_left_test"))
def test_unsafe_or_capturing_factor_arguments_rejected(position,fragment):
    arguments=["n","b","c","l"]
    arguments[position]=fragment
    with pytest.raises(ValueError):
        candidate.prime_factor_list_relation(*arguments,tag="test")


@pytest.mark.parametrize("tag",("","S","forall","tag+name","0","x;y"))
def test_unsafe_definition_tags_rejected(tag):
    with pytest.raises(ValueError):
        candidate.prime_factor_list_relation("n","b","c","l",tag=tag)
