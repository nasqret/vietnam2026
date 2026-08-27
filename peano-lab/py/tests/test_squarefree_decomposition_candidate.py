"""Original-kernel candidate checks for constructive squarefree decomposition."""

from functools import lru_cache
from dataclasses import replace
import gc
from math import isqrt, prod
import re

import pytest

from peano_lab.library import squarefree_decomposition_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.fermat_residue_map_candidate import prime
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from test_prime_valuation_support_candidate import (
    _assert_same_ast, _integer_profile, core as parent_core, rows as support_rows,
)


BODY_METRICS = {
    "divides_square_of_divides": (16,11,16),
    "squarefree_excludes_prime_square": (55,29,55),
    "prime_square_ne_one": (23,15,23),
    "squarefree_squared_divisor_is_one": (72,22,72),
    "coprime_squared_pair": (27,13,27),
    "squarefree_coprime_square_factor_is_one": (56,29,56),
    "squarefree_square_factor_reassociate": (29,14,29),
    "nonzero_square_factor_root": (25,15,24),
    "bounded_prime_square_divisor_search": (110,26,110),
    "squarefree_or_prime_square_divisor": (38,18,38),
    "squarefree_decomposition_bounded_exists": (113,32,113),
    "squarefree_decomposition_exists": (21,12,21),
    "squarefree_one": (46,24,46),
    "squarefree_coprime_square_balance": (137,29,137),
    "squarefree_decomposition_functional": (369,48,359),
    "squarefree_decomposition_exists_unique": (38,23,38),
}


@lru_cache(maxsize=1)
def core():
    return parent_core() | {r.name:r for r in support_rows()}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_squarefree_decomposition_candidate_theorems(TheoremSpec)


@pytest.mark.parametrize("row",rows(),ids=lambda r:r.name)
def test_original_kernel_body(row):
    try:
        receipt = replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert receipt.proof_depth <= 256
        assert receipt.proof_objects <= receipt.proof_nodes
        assert (receipt.proof_nodes,receipt.proof_depth,receipt.proof_objects) == BODY_METRICS[row.name]
        print(f"{row.name}: {receipt.proof_nodes}/{receipt.proof_depth}/{receipt.proof_objects}")
    finally:
        gc.collect()


def test_additive_dependency_order_and_ordinary_commands():
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert all(re.search(r"(?<![\w'])"+re.escape(d)+r"(?![\w'])","\n".join(row.script)) for d in row.dependencies)
        assert not any(c.startswith(("use ","sorry","admit","DNE","ring")) for c in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


def _squarefree_reference(n,tag="audit"):
    p = "audit_prime_"+tag
    return (
        f"~(({n}) = 0) /\\ forall {p}. ({prime(p,tag=tag+'domain')}) -> "
        f"(exists gap. gap + {p} = ({n})) -> ~(exists quotient. ({n}) = ({p} * {p}) * quotient)"
    )


def _decomposition_reference(n,r,s,tag="audit"):
    return f"({_squarefree_reference(r,tag)}) /\\ ({n}) = ({r}) * (({s}) * ({s}))"


def test_public_squarefree_is_bounded_prime_square_freeness_not_a_kernel_oracle():
    actual = candidate.squarefree_relation("n",tag="definition",variables=("n",))
    assert _closed_formula("forall n. "+actual) == _closed_formula("forall n. "+_squarefree_reference("n"))


def test_full_unique_endpoint_independently_matches_blueprint():
    expected = (
        "forall n. ~(n = 0) -> exists r s. "
        f"({_decomposition_reference('n','r','s','first')}) /\\ forall u v. "
        f"({_decomposition_reference('n','u','v','second')}) -> u = r /\\ v = s"
    )
    actual = next(r for r in rows() if r.name == "squarefree_decomposition_exists_unique")
    assert _closed_formula(actual.statement) == _closed_formula(expected)


SURFACES = (
    (candidate.squarefree_relation,("n",)),
    (candidate.squarefree_decomposition_relation,("n","r","s")),
)


@pytest.mark.parametrize("builder,args",SURFACES)
def test_public_surfaces_are_hygienic_alpha_equivalent(builder,args):
    first,names = parse_formula_with_names(builder(*args,tag="first",variables=args))
    second,other = parse_formula_with_names(builder(*args,tag="second",variables=args))
    assert first == second and names == other and set(names) == set(args)


@pytest.mark.parametrize("builder,args",SURFACES)
@pytest.mark.parametrize("bad",["", "unknown", "n - 1", "n / 2", "n = 0", "n) -> false", None, 17])
def test_public_surfaces_reject_nonterms_or_undeclared_variables(builder,args,bad):
    with pytest.raises((ValueError,TypeError)):
        builder(bad,*args[1:],tag="audit",variables=args)


@pytest.mark.parametrize("builder,args",SURFACES)
@pytest.mark.parametrize("context",[(),("n","n"),["n"],("forall",)])
def test_public_surfaces_require_explicit_valid_context(builder,args,context):
    with pytest.raises((ValueError,TypeError)):
        builder(*args,tag="audit",variables=context)


@pytest.mark.parametrize("builder,args",SURFACES)
@pytest.mark.parametrize("tag",["", "S", "forall", "bad tag", "x) -> false", None, 17])
def test_public_surfaces_reject_bad_tags(builder,args,tag):
    with pytest.raises((ValueError,TypeError)):
        builder(*args,tag=tag,variables=args)


@pytest.mark.parametrize("value",["n + 1","n * n","123456789012345678901234567890"])
def test_squarefree_surface_preserves_compound_terms_and_large_numerals(value):
    actual = candidate.squarefree_relation(value,tag="compound",variables=("n",))
    _assert_same_ast(_closed_formula("forall n. "+actual),_closed_formula("forall n. "+_squarefree_reference(value)))


def test_squarefree_surface_rejects_its_bound_prime_capture():
    with pytest.raises(ValueError,match="capture"):
        candidate.squarefree_relation("sfd_prime_capture",tag="capture",variables=("sfd_prime_capture",))


@pytest.mark.parametrize("name",["bounded_prime_square_divisor_search","squarefree_decomposition_functional","squarefree_decomposition_exists_unique"])
def test_poisoned_squarefree_endpoint_rejected(name):
    row = next(r for r in rows() if r.name == name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement="0 = 1"),),core=core()|{r.name:r for r in rows()})


def _is_squarefree(n):
    return n > 0 and all(e == 1 for p,e,v in _integer_profile(n))


@pytest.mark.parametrize("n",range(1,101))
def test_independent_small_models_have_exactly_one_squarefree_decomposition(n):
    factors = _integer_profile(n)
    kernel = prod(p**(e%2) for p,e,v in factors)
    root = prod(p**(e//2) for p,e,v in factors)
    assert _is_squarefree(kernel) and n == kernel*root*root
    actual_pairs = [(n//(v*v),v) for v in range(1,isqrt(n)+1) if n%(v*v)==0 and _is_squarefree(n//(v*v))]
    assert actual_pairs == [(kernel,root)]


@pytest.mark.parametrize("n,expected",[(0,False),(1,True),(2,True),(6,True),(30,True),(4,False),(12,False),(45,False),(49,False)])
def test_squarefree_domain_and_prime_square_boundaries(n,expected):
    assert _is_squarefree(n) == expected
