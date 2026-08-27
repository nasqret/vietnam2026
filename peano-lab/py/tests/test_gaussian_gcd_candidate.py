"""Fresh-process original HA tests for actual Gaussian gcd and Bézout proofs."""

from __future__ import annotations

from dataclasses import asdict,replace
from functools import lru_cache
from hashlib import sha256
import json
from math import isqrt
import os
from pathlib import Path
import re
import resource
import subprocess
import sys

import pytest

from peano_lab.library import gaussian_gcd_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import gaussian_euclidean_candidate as ge
from test_gaussian_ring_candidate import ROOT,core,rows as ring_rows,assert_family_contract,reference_divides,reference_associate,reference_irreducible,reference_prime,reference_code,GRID,numerical_mul,numerical_add,numerical_neg,numerical_norm
from test_gaussian_divisibility_candidate import rows as divisibility_rows,numerical_quotient


@lru_cache(maxsize=1)
def rows():
    return candidate.make_gaussian_gcd_candidate_theorems(TheoremSpec)


BODY_PROFILES=dict(zip((row.name for row in rows()),(
    (54,17,54),(62,22,62),(94,43,94),(93,39,93),(202,50,202),(170,44,170),(26,17,26),
    (68,34,68),(183,45,183),(79,32,79),(90,32,90),(67,38,67),(67,21,67),(20,9,20),
),strict=True))


def check_body(name: str, mutation: str='none'):
    table=core()|{row.name:row for row in (*ring_rows(),*divisibility_rows(),*rows())}
    row=table[name]
    if mutation=='false_conclusion':
        row=replace(row,statement=f'({row.statement}) /\\ false')
    elif mutation=='truncated_body':
        row=replace(row,script=row.script[:-1])
    elif mutation=='removed_dependency':
        row=replace(row,dependencies=row.dependencies[:-1])
    elif mutation=='corrupt_dependency':
        dep=row.dependencies[0]
        table=table|{dep:replace(table[dep],statement='0=0')}
    elif mutation=='missing_actual_carrier':
        assert row.name=='gaussian_gcd_bezout_exists'
        row=replace(row,statement=f"forall a b. ({reference_completion('a','b')})")
    elif mutation=='false_literal_gcd_uniqueness':
        assert row.name=='gaussian_gcd_unique_up_to_associate'
        row=replace(row,statement=f"forall g h a b. ({reference_gcd('g','a','b','wrong_gcd_first')}) -> ({reference_gcd('h','a','b','wrong_gcd_second')}) -> g=h")
    elif mutation=='prime_divides_both_factors':
        assert row.name=='gaussian_irreducible_dvd_product'
        row=replace(row,statement=f"forall p a b c. ({reference_irreducible('p')}) -> ({ge._code_mul('a','b','c','wrong_prime_product')}) -> ({reference_divides('p','c')}) -> ({reference_divides('p','a','wrong_first')}) /\\ ({reference_divides('p','b','wrong_second')})")
    if mutation!='none':
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,),core=table)
        return {'rejected':True,'mutation':mutation}
    return asdict(replay_candidate_bodies((row,),core=table)[0])


def isolated_body(name: str, mutation: str='none'):
    environment=os.environ.copy()
    environment['PYTHONPATH']=os.pathsep.join((str(ROOT/'peano-lab/py'),str(ROOT/'scripts')))
    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--body',name,mutation],cwd=ROOT,env=environment,text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
def test_original_kernel_body_in_fresh_process(name):
    receipt=isolated_body(name)
    assert receipt['name']==name
    assert receipt['proof_nodes']>0 and receipt['proof_depth']<=256
    assert (receipt['proof_nodes'],receipt['proof_depth'],receipt['proof_objects'])==BODY_PROFILES[name]


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
@pytest.mark.parametrize('mutation',('false_conclusion','truncated_body'))
def test_negative_proof_mutation_in_fresh_process(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


@pytest.mark.parametrize('name',tuple(row.name for row in rows() if row.dependencies))
@pytest.mark.parametrize('mutation',('removed_dependency','corrupt_dependency'))
def test_dependency_mutation_in_fresh_process(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


def test_exact_gcd_prime_inventory_and_every_local_formula():
    assert_family_contract(rows(),(*ring_rows(),*divisibility_rows()),(14,76,777,'dc4ec4831a201fb835bf086827d75b342cd1d4835b46911e95ac178346834173'))


ROOT_PINS={
    'gaussian_gcd_bezout_exists':'67d09aa8ff5c895839b29eb5f9f44d9d91087f8f2316698b47530795b800f981',
    'gaussian_gcd_unique_up_to_associate':'2ea8e4c57a49cecb2aee00f5611ef247500d39fe0f1fc1b239b478a49bd3a7c5',
    'gaussian_irreducible_dvd_product':'e2fb26736c7080feea9c73498dc0609b2e08cfdd89bdf16857afd0e6a9eb7620',
    'gaussian_irreducible_iff_prime':'aa8c5f0706fbabf6c9069ae0fd2a7f7b3ecf9651b30bad9d7b4483fbd6d2689e',
}


@pytest.mark.parametrize('name,digest',ROOT_PINS.items())
def test_principal_gcd_prime_statement_hashes(name,digest):
    assert sha256(next(row.statement for row in rows() if row.name==name).encode()).hexdigest()==digest


def reference_bezout(g,a,b,u,v,tag='reference_bezout'):
    return f"exists first_product second_product. ({ge._code_mul(a,u,'first_product',tag+'first')}) /\\ " \
           f"(({ge._code_mul(b,v,'second_product',tag+'second')}) /\\ ({ge._code_add('first_product','second_product',g,tag+'sum')}))"


def reference_gcd(g,a,b,tag='reference_gcd'):
    return f"({reference_divides(g,a,tag+'first')}) /\\ (({reference_divides(g,b,tag+'second')}) /\\ " \
           f"forall divisor. ({reference_divides('divisor',a,tag+'common_first')}) -> ({reference_divides('divisor',b,tag+'common_second')}) -> ({reference_divides('divisor',g,tag+'greatest')}))"


def reference_completion(a,b,tag='reference_completion'):
    return f"exists gcd first_coefficient second_coefficient. ({reference_gcd('gcd',a,b,tag+'gcd')}) /\\ ({reference_bezout('gcd',a,b,'first_coefficient','second_coefficient',tag+'bezout')})"


def test_full_gcd_bezout_exists_has_only_actual_carrier_premises():
    expected=f"forall a b. ({ge._gaussian('a','expected_first_valid')}) -> ({ge._gaussian('b','expected_second_valid')}) -> ({reference_completion('a','b')})"
    row=next(row for row in rows() if row.name=='gaussian_gcd_bezout_exists')
    assert _closed_formula(row.statement)==_closed_formula(expected)
    assert row.dependencies==('gaussian_norm_exists','gaussian_gcd_bezout_bounded_exists','le_refl')
    bounded=next(row for row in rows() if row.name=='gaussian_gcd_bezout_bounded_exists')
    assert 'induction k' in bounded.script
    assert 'gaussian_euclidean_division_exists' in bounded.dependencies
    assert 'gaussian_bezout_euclidean_backward' in bounded.dependencies
    assert 'le_of_succ_le_succ' in bounded.dependencies


def test_zero_right_base_contains_actual_identity_coefficient_six():
    expected=f"forall a. ({ge._gaussian('a','expected_zero_valid')}) -> ({reference_gcd('a','a','0')}) /\\ ({reference_bezout('a','a','0','6','0')})"
    row=next(row for row in rows() if row.name=='gaussian_gcd_bezout_zero_right')
    assert _closed_formula(row.statement)==_closed_formula(expected)


def test_gcd_uniqueness_is_witnessed_unit_equivalence_not_code_equality():
    expected=f"forall g h a b. ({reference_gcd('g','a','b','expected_first')}) -> ({reference_gcd('h','a','b','expected_second')}) -> ({reference_associate('g','h')})"
    row=next(row for row in rows() if row.name=='gaussian_gcd_unique_up_to_associate')
    assert _closed_formula(row.statement)==_closed_formula(expected)


def test_irreducibles_are_actual_prime_divisors_via_constructed_bezout():
    expected=f"forall p a b c. ({reference_irreducible('p')}) -> ({ge._code_mul('a','b','c','expected_prime_product')}) -> ({reference_divides('p','c','expected_product_divisor')}) -> ({reference_divides('p','a','expected_first')}) \\/ ({reference_divides('p','b','expected_second')})"
    row=next(row for row in rows() if row.name=='gaussian_irreducible_dvd_product')
    assert _closed_formula(row.statement)==_closed_formula(expected)
    assert 'gaussian_gcd_bezout_exists' in row.dependencies
    assert 'gaussian_bezout_unit_divisor_cancel' in row.dependencies


def test_literal_irreducible_prime_biconditional_retains_all_definition_clauses():
    irred=reference_irreducible('p')
    prime=reference_prime('p')
    expected=f"forall p. (({irred}) -> ({prime})) /\\ (({prime}) -> ({irred}))"
    row=next(row for row in rows() if row.name=='gaussian_irreducible_iff_prime')
    assert _closed_formula(row.statement)==_closed_formula(expected)


PUBLIC_BUILDERS=(
    (candidate.gaussian_gcd_relation,('g','a','b'),reference_gcd),
    (candidate.gaussian_bezout_relation,('g','a','b','u','v'),reference_bezout),
)


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
def test_gcd_bezout_definitions_are_independent_conservative_graphs(builder,arguments,reference):
    prefix='forall '+' '.join(arguments)+'. '
    actual=builder(*arguments,tag='actual',variables=arguments)
    assert _closed_formula(prefix+actual)==_closed_formula(prefix+reference(*arguments))
    assert set(parse_formula_with_names(actual)[1])==set(arguments)
    assert _closed_formula(prefix+actual)==_closed_formula(prefix+builder(*arguments,tag='other',variables=arguments))


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
def test_gcd_bezout_graphs_accept_terms_repeated_parameters_and_zero(builder,arguments,reference):
    for changed in (('x+0',)*len(arguments),('0',)*len(arguments),('x*y',)*len(arguments)):
        actual=builder(*changed,tag='actual',variables=('x','y'))
        assert _closed_formula('forall x y. '+actual)==_closed_formula('forall x y. '+reference(*changed))


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
@pytest.mark.parametrize('bad',('', 'S','forall','unknown','x y','x;y','x)','a /\\ b'))
def test_gcd_bezout_graphs_reject_invalid_terms(builder,arguments,reference,bad):
    for index in range(len(arguments)):
        changed=list(arguments)
        changed[index]=bad
        with pytest.raises(ValueError):
            builder(*changed,tag='actual',variables=arguments)


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
@pytest.mark.parametrize('bad',('', 'S','forall','1','a+b','x;y'))
def test_gcd_bezout_graphs_reject_invalid_tags(builder,arguments,reference,bad):
    with pytest.raises(ValueError):
        builder(*arguments,tag=bad,variables=arguments)


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
@pytest.mark.parametrize('context',((),('x','x'),('S',),('x y',),['x']))
def test_gcd_bezout_graphs_require_explicit_valid_context(builder,arguments,reference,context):
    with pytest.raises(ValueError):
        builder(*arguments,tag='actual',variables=context)


@pytest.mark.parametrize('builder,arguments,reference',PUBLIC_BUILDERS)
def test_gcd_bezout_graphs_reject_every_nested_binder_namespace_capture(builder,arguments,reference):
    formula=builder(*arguments,tag='actual',variables=arguments)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',formula) for name in clause.split()}
    representatives={}
    for name in sorted(binders):
        representatives.setdefault(name.split('_',1)[0],name)
    assert representatives
    for name in representatives.values():
        changed=(name,*arguments[1:])
        with pytest.raises(ValueError):
            builder(*changed,tag='actual',variables=changed)


@pytest.mark.parametrize('name,mutation',(
    ('gaussian_gcd_bezout_exists','missing_actual_carrier'),
    ('gaussian_gcd_unique_up_to_associate','false_literal_gcd_uniqueness'),
    ('gaussian_irreducible_dvd_product','prime_divides_both_factors'),
))
def test_gcd_prime_statement_boundary_mutations_are_rejected(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


def numerical_euclidean_step(a,b):
    denominator=numerical_norm(b)
    assert denominator>0
    real=a[0]*b[0]+a[1]*b[1]
    imaginary=a[1]*b[0]-a[0]*b[1]
    q=((2*real+denominator)//(2*denominator),(2*imaginary+denominator)//(2*denominator))
    r=numerical_add(a,numerical_neg(numerical_mul(b,q)))
    assert numerical_norm(r)<denominator
    return q,r


def numerical_gcd_bezout(a,b):
    old,current=a,b
    old_u,u=(1,0),(0,0)
    old_v,v=(0,0),(1,0)
    while current!=(0,0):
        q,r=numerical_euclidean_step(old,current)
        old,current=current,r
        old_u,u=u,numerical_add(old_u,numerical_neg(numerical_mul(q,u)))
        old_v,v=v,numerical_add(old_v,numerical_neg(numerical_mul(q,v)))
    return old,old_u,old_v


@pytest.mark.parametrize('a',GRID)
def test_independent_euclidean_gcd_and_signed_bezout_microaudit(a):
    for b in GRID:
        g,u,v=numerical_gcd_bezout(a,b)
        assert numerical_add(numerical_mul(a,u),numerical_mul(b,v))==g
        assert numerical_quotient(g,a) is not None
        assert numerical_quotient(g,b) is not None
        for d in GRID:
            if numerical_quotient(d,a) is not None and numerical_quotient(d,b) is not None:
                assert numerical_quotient(d,g) is not None


def numerical_irreducible(p):
    norm=numerical_norm(p)
    if norm<=1:
        return False
    bound=isqrt(norm)
    for real in range(-bound,bound+1):
        for imaginary in range(-bound,bound+1):
            d=(real,imaginary)
            if 1<numerical_norm(d)<norm and numerical_quotient(d,p) is not None:
                return False
    return True


@pytest.mark.parametrize('p',GRID)
def test_independent_gaussian_prime_divisor_microaudit(p):
    if numerical_irreducible(p):
        for a in GRID:
            for b in GRID:
                if numerical_quotient(p,numerical_mul(a,b)) is not None:
                    assert numerical_quotient(p,a) is not None or numerical_quotient(p,b) is not None


def test_zero_gcd_unit_ambiguity_and_disjunctive_prime_boundary_examples():
    assert numerical_gcd_bezout((0,0),(0,0))==((0,0),(1,0),(0,0))
    assert reference_code((1,0))==6 and reference_code((-1,0))==2
    assert numerical_quotient((-1,0),(1,0)) is not None
    p=(1,1)
    assert numerical_irreducible(p)
    assert numerical_quotient(p,numerical_mul(p,(1,0))) is not None
    assert numerical_quotient(p,(1,0)) is None
    assert numerical_irreducible((3,0))
    assert not numerical_irreducible((2,0))


if __name__=='__main__':
    assert sys.argv[1]=='--body'
    resource.setrlimit(resource.RLIMIT_CPU,(45,50))
    print(json.dumps(check_body(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'none')))
