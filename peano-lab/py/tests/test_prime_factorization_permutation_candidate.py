"""Full unordered factorization uniqueness with constructed index bijections."""

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import json
from math import factorial,prod
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import prime_factorization_permutation_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.fermat_two_squares_factor_fold_candidate import all_prime_factor_prefix
from peano_lab.library.finite_fold_surface import beta_at,product_relation
from peano_lab.library.finite_permutation_theorems import permutation_prefix
from peano_lab.library.foundation_saturation_candidate import make_foundation_saturation_candidate_theorems
from peano_lab.library.theorems import TheoremSpec,_closed_formula


REPO=Path(__file__).resolve().parents[3]
PARENT_SHA256="481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"
EXPECTED_STATEMENTS={
    "factor_permutation_below_zero_impossible":"428642bc43c859af24a624ea749108442792aa41e6bc19fb3106c59e81ece9ca",
    "factor_permutation_prefix_reflect":"918397b87490798004ccace18687c1240bae6706332bdf051fde07dcd2641858",
    "factor_permutation_all_prime_entry":"914f138403b55522ed73cce87bb7d08f5bafd89c6142a7668f6af69c5eef04f7",
    "factor_permutation_product_exists":"980b71d16531ed4981890ae7dc71e590078a87faefd1d36b3c7aed8186fb299a",
    "factor_permutation_cancel_last":"041f2f5d3ab4302b2626090ce067ebc1cb7415fad5fa3244896ec9b03bbca1da",
    "factor_permutation_successor_decompose":"f7df0404117e5ce0d9bf34b7000cbb334d3c57bb35b62e6f3ba9f11edeb804cb",
    "factor_permutation_unit_length_zero":"bb16a740d4c971c54429a2a9491e8d28abf1a2756c732cca6e72aca17c802e85",
    "factor_permutation_prime_member":"2eb9ede42f86ddd65b87209bbb055ba0710059750b8dca3116b969a7a16b34b1",
    "factor_permutation_empty_matching":"adaddae14b56db6e37804fe5a1a2426c62d334f13c3be32266677c0bb1c22306",
    "factor_permutation_index_extend":"9342b26708a00053eeb8f0d3d1a58802c17d53e0615e3bd7be6104bbedea1eb7",
    "factor_permutation_matching_append":"28f285c92b7a9db4825b92c14d26f928100f6b69e22f2f02d014a013fcd5d137",
    "factor_permutation_matched_append":"2a6ad41acf6f134f43512462c99bdb008c72061ff357bd525fbfa89a7d669474",
    "factor_permutation_matched_append_exists":"7bccaae0f683527092b3abaeb5d34128a9b57f7e0b3a344cf2c2736b9f3ab4fa",
    "factor_permutation_swap_reflect_unchanged":"7ab5ea3a86a33d084cfd25a27be62c9d1ed11ef82d55e7ae69141b6413aa6cd0",
    "factor_permutation_swap_bijection":"b8a2e3c35f5309423acb885aa3274050090e59619bc203f8339560321ece0a15",
    "factor_permutation_swap_all_prime":"145a7e875574f246b3322154a86f07012792f15efb5067977d9a9a4f68c7f12e",
    "factor_permutation_swap_factorization":"887972ad8b50e3176a9c3c95de0e08b5955906e8a8a6e196ffe57365d79b1e3d",
    "factor_permutation_swapped_factorization_exists":"8b1b8a5a033debfb547053d63ad0acb2f025a3a11d299ad17315b8de5d9210fa",
    "factor_permutation_matching_unswap":"a58406de5cd4f5d5b6efc2759c34108a0e1494a32d307753e07661b8e47b94bb",
    "factor_permutation_matched_unswap_exists":"e279a76ccf0f80c2242c19671008d4a43d1429dc205f3e797d4d2ea86487de71",
    "prime_factor_lists_matching_by_length":"95c94b01fda58b534085977b14f017960ce2479b3e7bb38ba30f2631523798d2",
    "prime_factor_lists_permutation_exists":"89df5c484cb30ab9c74dd04af9a5700c635ae402d01f8088ff934f75e0254518",
    "prime_factorization_exists_unique_up_to_permutation":"622f8362d88b818d10462b55bca228e06f0c517174001c7ea039b85bb054ab7c",
}
EXPECTED_NODES=(13,54,42,28,145,63,23,54,57,313,120,52,34,75,188,178,132,80,424,183,713,46,34)
RELATIONS=(
    (candidate.factor_list_matching_relation,("b","c","d","e","u","v","l")),
    (candidate.prime_factor_list_permutation_relation,("b","c","l","d","e","m","u","v")),
)


@lru_cache(maxsize=1)
def _rows():
    return candidate.make_prime_factorization_permutation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _core():
    raw=(REPO/"artifacts/peano-library/alpha/catalog-v27.json").read_bytes()
    assert sha256(raw).hexdigest()==PARENT_SHA256
    records=json.loads(raw)["theorems"]
    assert len(records)==2560 and all(row["checked_use"] for row in records)
    table={row["name"]:TheoremSpec(row["name"],row["statement"],tuple(row["dependencies"]),tuple(row["script"]),row.get("summary","")) for row in records}
    foundations=make_foundation_saturation_candidate_theorems(TheoremSpec)
    assert len(foundations)==5
    assert sha256("\n".join(row.name for row in foundations).encode()).hexdigest()=="3fb216ba4a46248e14444b3927af3c5534f930ca0fa2757d7310927ae41751cb"
    for row in foundations:
        assert row.name not in table and set(row.dependencies)<=set(table)
        table[row.name]=row
    return table


@lru_cache(maxsize=1)
def _all():
    return _core()|{row.name:row for row in _rows()}


def _factor(n,b,c,l,tag):
    return f"~({n}=0) /\\ (({product_relation(b,c,l,n,tag=tag+'product')}) /\\ ({all_prime_factor_prefix(b,c,l,tag=tag+'primes')}))"


def _matching(b,c,d,e,u,v,l,tag):
    return f"forall i j a. (exists h. h+S i={l}) -> ({beta_at(u,v,'i','j',tag=tag+'map')}) -> ({beta_at(b,c,'i','a',tag=tag+'source')}) -> ({beta_at(d,e,'j','a',tag=tag+'target')})"


def _permutation(b,c,l,d,e,m,u,v,tag):
    return f"{l}={m} /\\ (({permutation_prefix(u,v,l,tag=tag+'indices')}) /\\ ({_matching(b,c,d,e,u,v,l,tag+'matching')}))"


def test_exact_additive_topological_inventory_and_original_kernel():
    assert tuple(row.name for row in _rows())==tuple(EXPECTED_STATEMENTS)
    assert sha256("\n".join(EXPECTED_STATEMENTS).encode()).hexdigest()=="a2049a742e30b1939d5f13475bbccabbfbb6e87f67ff48ccd37eaf397e8caff1"
    available=set(_core())
    for row in _rows():
        assert row.name not in available and set(row.dependencies)<=available
        assert len(set(row.dependencies))==len(row.dependencies)
        formula,free=parse_formula_with_names(row.statement)
        assert not free and formula==_closed_formula(row.statement)
        assert all(not any(token in command for token in ("DNE","admit","sorry","oracle","axiom")) and not command.startswith("use ") for command in row.script)
        available.add(row.name)
    receipts=tuple(replay_candidate_bodies((row,),core=_all())[0] for row in _rows())
    assert tuple(item.proof_nodes for item in receipts)==EXPECTED_NODES
    assert sum(item.dependency_count for item in receipts)==79
    assert sum(item.command_count for item in receipts)==1504
    assert sum(item.proof_nodes for item in receipts)==3051
    assert sum(item.proof_objects for item in receipts)==3033
    assert max(item.proof_depth for item in receipts)==60
    assert max(item.proof_nodes for item in receipts)==713


@pytest.mark.parametrize(("name","digest"),EXPECTED_STATEMENTS.items())
def test_frozen_statement_hash(name,digest):
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
        core=core|{dependency:replace(core[dependency],statement="0=0")}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core)


def test_exact_unordered_root_and_constructed_existence_root():
    factorA=_factor("n","b","c","l","source")
    factorB=_factor("n","d","e","m","target")
    perm=_permutation("b","c","l","d","e","m","u","v","witness")
    exact=f"forall n b c l d e m. (({factorA}) /\\ ({factorB})) -> exists u v. ({perm})"
    complete=f"forall n. ~(n=0) -> exists l b c. ({factorA}) /\\ forall m d e. ({factorB}) -> exists u v. ({perm})"
    assert _closed_formula(exact)==_closed_formula(_all()["prime_factor_lists_permutation_exists"].statement)
    assert _closed_formula(complete)==_closed_formula(_all()["prime_factorization_exists_unique_up_to_permutation"].statement)


def test_unordered_uniqueness_does_not_use_sorted_factorization_uniqueness():
    visited=set()
    pending=["prime_factor_lists_permutation_exists"]
    while pending:
        name=pending.pop()
        if name not in visited:
            visited.add(name)
            pending.extend(_all()[name].dependencies)
    assert "gauss_coprime_cancel" in visited
    assert "finite_bounded_injective_surjective" in visited
    assert "beta_prefix_swap_last_from_entries" in visited
    assert not any("sorted" in name or name.startswith(("beta_canonical_","prime_factorization_unique")) for name in visited)


@pytest.mark.parametrize(("builder","arguments"),RELATIONS)
def test_hygienic_native_definitions_and_alpha_invariant_tags(builder,arguments):
    first,free=parse_formula_with_names(builder(*arguments,tag="first"))
    second,other=parse_formula_with_names(builder(*arguments,tag="second"))
    assert first==second and set(free)==set(other)==set(arguments)
    assert "Permutation" not in builder(*arguments,tag="audit")
    assert "Sorted" not in builder(*arguments,tag="audit")


def test_permutation_definition_requires_actual_bounded_injective_surjective_alignment():
    expected=_permutation("b","c","l","d","e","m","u","v","expected")
    actual=candidate.prime_factor_list_permutation_relation("b","c","l","d","e","m","u","v",tag="actual")
    assert parse_formula_with_names(actual)==parse_formula_with_names(expected)
    matching=_matching("b","c","d","e","u","v","l","independent")
    assert parse_formula_with_names(candidate.factor_list_matching_relation("b","c","d","e","u","v","l",tag="matching"))==parse_formula_with_names(matching)


@pytest.mark.parametrize(("builder","arguments","position"),tuple((builder,arguments,position) for builder,arguments in RELATIONS for position in range(len(arguments))))
@pytest.mark.parametrize("fragment",("","S","forall","x+y","0","x;y","pfp_i_test","ff_h_test","fp_i_test","fsat_gap_test","frm_left_test","ftsf_index_test"))
def test_unsafe_or_capturing_arguments_rejected(builder,arguments,position,fragment):
    changed=list(arguments)
    changed[position]=fragment
    with pytest.raises(ValueError):
        builder(*changed,tag="test")


@pytest.mark.parametrize(("builder","arguments"),RELATIONS)
@pytest.mark.parametrize("tag",("","S","forall","tag+name","0","x;y"))
def test_unsafe_tags_rejected(builder,arguments,tag):
    with pytest.raises(ValueError):
        builder(*arguments,tag=tag)


def _encode(values):
    """Small independent arithmetic examples, never a proof/admission oracle."""
    scale=factorial(len(values))*(max(values,default=0)+1)
    moduli=tuple(1+(i+1)*scale for i in range(len(values)))
    modulus=prod(moduli)
    code=sum(value*(modulus//m)*pow(modulus//m,-1,m) for value,m in zip(values,moduli))%modulus
    assert tuple(code%m for m in moduli)==tuple(values)
    return code,scale,len(values),modulus


def _decoded(code,scale,length):
    return tuple(code%(1+(i+1)*scale) for i in range(length))


@pytest.mark.parametrize(("source","target","mapping"),(
    ((),(),()),((2,),(2,),(0,)),((3,2),(2,3),(1,0)),
    ((2,3,2),(2,2,3),(0,2,1)),((5,2,3,2),(2,5,2,3),(1,0,3,2)),
))
def test_concrete_beta_bijections_include_unsorted_duplicate_and_empty_lists(source,target,mapping):
    b,c,l,_=_encode(source)
    d,e,m,_=_encode(target)
    u,v,L,_=_encode(mapping)
    assert l==m==L
    actual=_decoded(u,v,L)
    assert set(actual)==set(range(l)) and len(set(actual))==l
    assert all(b%(1+(i+1)*c)==d%(1+(j+1)*e) for i,j in enumerate(actual))
    assert prod(source)==prod(target)>0


def test_alignment_alone_is_not_a_permutation_with_repeated_factors():
    source=(2,2)
    target=(2,2)
    false_map=(0,0)
    assert all(source[i]==target[j] for i,j in enumerate(false_map))
    assert len(set(false_map))!=len(source)
    assert set(false_map)!=set(range(len(target)))


def test_equal_lists_need_not_have_equal_raw_beta_codes():
    b,c,l,period=_encode((2,3,2))
    assert b!=b+period
    assert _decoded(b,c,l)==_decoded(b+period,c,l)
    assert _decoded(*_encode(tuple(range(l)))[:3])==tuple(range(l))
