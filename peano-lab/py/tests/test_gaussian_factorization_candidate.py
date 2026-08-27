"""Independent actual-product, factor-witness, hygiene and HA proof audits.

Finite integer examples explain representation boundaries only. Every proof
body and every corruption probe reaches the original kernel in a fresh process.
"""

from __future__ import annotations

from dataclasses import asdict,replace
from functools import lru_cache
from hashlib import sha256
import json
from math import factorial,isqrt
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys

import pytest

from peano_lab.library import gaussian_factorization_candidate as candidate
from peano_lab.library import gaussian_gcd_candidate as gcd
from peano_lab.library import gaussian_euclidean_candidate as frozen
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.finite_fold_surface import _beta_at_term
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from test_gaussian_factor_search_candidate import (
    ROOT,core as search_core,rows as search_rows,_and,_assert_same_ast,
    _lt,_unit,_irreducible,_dvd,_gaussian_encode,_gaussian_decode,
    _norm_value,_multiply,_quotient,_proper_value,
)


SOURCE_SHA256='cb95534689e6155fdbb1a7e80be843bdd91153504f9b5df99bf6ee59e77e8d1e'
NAMES_SHA256='a603ed550e6e08abef2655574b9caa9234a8ac7a942a1790a1c3e30006bb104d'
PRINCIPAL_SHA256={
    'gaussian_product_empty_exists':'f87170ec5179c25be3984deb5dcc3d478300ab1b0334cf74c6ca487331973f11',
    'gaussian_product_empty_value':'db369a4162d09dd605adf3009a1db7c7aaa9ef5866567fa0ac1e166d8827b092',
    'gaussian_product_functional':'63f1db999746bbfc2bdd321dc624e36a385812af0ad166abdd2a251d9699834e',
    'gaussian_irreducible_factorization_exists':'937d06af5872f94374dc94a8a78f21b0ce248d15b05f5c1aabe0938c7b3a2d46',
    'gaussian_prime_factorization_exists':'86d207a622593e87fc60e4c852a6aabb8e6b1057b960cbadc7e2ac736aae827b',
    'gaussian_all_irreducible_product_nonzero':'2afdf285b599cdc94914eb242e416e6d9d3b2ac1257306ddf983c771ce6392a3',
    'gaussian_all_irreducible_product_unit_length_zero':'e935326faf7b6916452a7372e66fa5e64187c5f04089c06407d55d9a75055e42',
    'gaussian_factorization_value_valid':'287c3e10b11f20850b983fccafccff71dcd688966eabc0aecaf62ea187092edb',
    'gaussian_factorization_value_nonzero':'d8393588fe5bc9689e0000108833f18547cce3c5200c6dee4b1fa62fa8050c43',
    'gaussian_irreducible_divisor_product_member':'2c433815dbf5d55e4746235d7644a9dd67ef04e8e76fca8638ed1c2dbe16c9f7',
}
BODY_METRICS=(
    (18,12,18),(18,12,18),(747,39,747),(50,28,50),(59,29,59),(83,32,83),
    (165,44,165),(18,12,18),(23,14,23),(93,29,93),(42,18,42),(25,13,25),
    (43,26,43),(70,32,70),(45,17,45),(112,39,112),(140,39,140),(22,14,22),
    (50,31,50),(50,31,50),(30,20,30),(12,9,12),(72,27,72),(82,25,82),
    (70,33,70),(48,28,48),(44,20,44),(141,35,141),
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_gaussian_factorization_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return search_core()|{row.name:row for row in (*search_rows(),*gcd.make_gaussian_gcd_candidate_theorems(TheoremSpec))}


def check_body(name: str,mutation: str='none'):
    table=core()|{row.name:row for row in rows()}
    row=table[name]
    if mutation=='false_conclusion':
        row=replace(row,statement=f'({row.statement}) /\\ false')
    elif mutation=='truncated_body':
        row=replace(row,script=row.script[:-1])
    elif mutation=='removed_dependency':
        row=replace(row,dependencies=row.dependencies[:-1])
    elif mutation=='corrupt_dependency':
        dependency=row.dependencies[0]
        table=table|{dependency:replace(table[dependency],statement='0=0')}
    elif mutation in {'no_carrier','allow_zero'}:
        premise='~(z=0)' if mutation=='no_carrier' else frozen._gaussian('z','mutation_carrier')
        row=replace(row,statement=f'forall z. ({premise}) -> exists u b c l. ({_factor("z","u","b","c","l","mutation_factors",prime=True)})')
    elif mutation=='wrong_identity_seed':
        row=replace(row,statement='forall b c. ('+_product('b','c','0','1','wrong_empty_identity')+')')
    elif mutation!='none':
        raise ValueError('unknown Gaussian product proof mutation')
    if mutation!='none':
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,),core=table)
        return {'rejected':True,'mutation':mutation}
    return asdict(replay_candidate_bodies((row,),core=table)[0])


def isolated_body(name: str,mutation: str='none'):
    environment=os.environ.copy()
    environment['PYTHONPATH']=str(ROOT/'peano-lab/py')
    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--body',name,mutation],
                          cwd=ROOT,env=environment,text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize('name,metrics',tuple((row.name,metrics) for row,metrics in zip(rows(),BODY_METRICS,strict=True)))
def test_original_kernel_body(name,metrics):
    receipt=isolated_body(name)
    assert receipt['name']==name
    assert (receipt['proof_nodes'],receipt['proof_depth'],receipt['proof_objects'])==metrics


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
@pytest.mark.parametrize('mutation',('false_conclusion','truncated_body'))
def test_false_or_incomplete_proof_is_rejected(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


@pytest.mark.parametrize('name',tuple(row.name for row in rows() if row.dependencies))
@pytest.mark.parametrize('mutation',('removed_dependency','corrupt_dependency'))
def test_missing_or_forged_actual_prerequisite_is_rejected(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


@pytest.mark.parametrize('mutation',('no_carrier','allow_zero'))
def test_prime_factorization_cannot_drop_actual_carrier_or_nonzero_guards(mutation):
    assert isolated_body('gaussian_prime_factorization_exists',mutation)['rejected'] is True


def test_proof_cannot_silently_replace_gaussian_identity_by_natural_one():
    assert isolated_body('gaussian_product_empty_exists','wrong_identity_seed')['rejected'] is True


def test_exact_candidate_inventory_is_topological_constructive_and_has_no_unused_edges():
    assert len(rows())==28 and sum(len(r.dependencies) for r in rows())==91
    assert sum(len(r.script) for r in rows())==1125
    assert sha256(('\n'.join(r.name for r in rows())+'\n').encode()).hexdigest()==NAMES_SHA256
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest()==SOURCE_SHA256
    seen=set(core())
    for row in rows():
        assert row.name not in seen and len(set(row.dependencies))==len(row.dependencies)
        assert set(row.dependencies)<=seen
        for dependency in row.dependencies:
            assert re.search(r'\b'+re.escape(dependency)+r'\b','\n'.join(row.script))
        assert row.script and not any(c.startswith(('use ','admit','sorry')) or 'DNE' in c for c in row.script)
        seen.add(row.name)
    assert sum(m[0] for m in BODY_METRICS)==sum(m[2] for m in BODY_METRICS)==2372
    assert max(m[0] for m in BODY_METRICS)==747 and max(m[1] for m in BODY_METRICS)==44


@pytest.mark.parametrize('name,expected',tuple(PRINCIPAL_SHA256.items()))
def test_exact_principal_statement_pin(name,expected):
    assert sha256(next(r.statement for r in rows() if r.name==name).encode()).hexdigest()==expected


# Expected definitions use only immutable v28 arithmetic and independent
# quantifier structure. No new factorization builder defines its expected AST.
def _at(b,c,i,a,tag):
    return _beta_at_term(b,c,i,a,tag='independent_factor_'+tag,avoid=())


def _product(b,c,l,P,tag,*,seed='6'):
    h,e='independent_trace_'+tag,'independent_scale_'+tag
    i,a,R,Q=('independent_'+role+'_'+tag for role in ('index','factor','before','after'))
    steps=f'forall {i}. ({_lt(i,l,tag+"bound")}) -> exists {a} {R} {Q}. '+_and(
        _at(b,c,i,a,tag+'factor'),_at(h,e,i,R,tag+'before'),
        _at(h,e,f'S ({i})',Q,tag+'after'),frozen._code_mul(R,a,Q,tag+'multiplication'))
    return f'exists {h} {e}. '+_and(_at(h,e,'0',seed,tag+'start'),_at(h,e,l,P,tag+'end'),steps)


def _prime(p,tag):
    a,b,c=('independent_'+role+'_'+tag for role in ('left','right','product'))
    return _and(frozen._gaussian(p,tag+'carrier'),f'~(({p})=0)',f'~({_unit(p,tag+"nonunit")})',
        f'forall {a} {b} {c}. ({frozen._code_mul(a,b,c,tag+"multiply")}) -> ({_dvd(p,c,tag+"divisor")}) -> ({_dvd(p,a,tag+"left")}) \\/ ({_dvd(p,b,tag+"right")})')


def _all_factors(b,c,l,tag,*,prime=False):
    i,p='independent_index_'+tag,'independent_value_'+tag
    predicate=_prime(p,tag+'prime') if prime else _irreducible(p,tag+'irreducible')
    return f'forall {i} {p}. ({_lt(i,l,tag+"bound")}) -> ({_at(b,c,i,p,tag+"entry")}) -> ({predicate})'


def _all_prime(b,c,l,tag):
    return _all_factors(b,c,l,tag,prime=True)


def _factor(z,u,b,c,l,tag,*,prime=False):
    P='independent_product_'+tag
    return _and(_unit(u,tag+'unit'),_all_factors(b,c,l,tag+'factors',prime=prime),
                f'exists {P}. '+_and(_product(b,c,l,P,tag+'trace'),frozen._code_mul(u,P,z,tag+'reconstruction')))


def _prime_factor(z,u,b,c,l,tag):
    return _factor(z,u,b,c,l,tag,prime=True)


SURFACES=(
    (candidate.gaussian_product_relation,('b','c','l','P'),_product),
    (candidate.gaussian_all_irreducible_relation,('b','c','l'),_all_factors),
    (candidate.gaussian_all_prime_relation,('b','c','l'),_all_prime),
    (candidate.gaussian_irreducible_factorization_relation,('z','u','b','c','l'),_factor),
    (candidate.gaussian_prime_factorization_relation,('z','u','b','c','l'),_prime_factor),
)


@pytest.mark.parametrize('builder,args,independent',SURFACES,ids=('product','irreducibles','primes','factorization','prime_factorization'))
@pytest.mark.parametrize('variant',('plain','compound','large_numeral'))
def test_public_relations_have_exact_independent_hygienic_asts(builder,args,independent,variant):
    context=(*args,'unused')
    actual=args
    if variant=='compound':
        actual=tuple(f'S ({x}+unused)' for x in args)
    elif variant=='large_numeral':
        actual=(str((1<<96)+31),*args[1:])
    first=builder(*actual,tag='factor_alpha',variables=context)
    expected=independent(*actual,'factor_independent')
    _assert_same_ast(parse_formula_in_context(first,list(context)),parse_formula_in_context(expected,list(context)))
    other=builder(*actual,tag='factor_beta',variables=context)
    _assert_same_ast(parse_formula_in_context(first,list(context)),parse_formula_in_context(other,list(context)))


def _generated_binder_cases():
    result=[]
    for builder,args,_ in SURFACES:
        expression=builder(*args,tag='factor_collision',variables=args)
        binders=sorted({name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',expression) for name in clause.split()})
        assert binders
        result.extend((builder,args,binder) for binder in binders)
    return tuple(result)


@pytest.mark.parametrize('builder,args,binder',_generated_binder_cases(),ids=lambda item:getattr(item,'__name__',str(item)))
def test_every_nested_legacy_and_generated_binder_rejects_full_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='factor_collision',variables=(*args,binder))


@pytest.mark.parametrize('builder,args,_',SURFACES)
@pytest.mark.parametrize('context',([],(),None,'b c l',('b','b'),('bad variable',)))
def test_invalid_public_contexts_are_rejected(builder,args,_,context):
    with pytest.raises(ValueError):
        builder(*args,tag='factor_context',variables=context)


@pytest.mark.parametrize('builder,args,_',SURFACES)
@pytest.mark.parametrize('term',('','undeclared','b = b','forall k. k','b) -> false -> (b'))
def test_nonterms_or_unknown_variables_cannot_enter_public_relations(builder,args,_,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='factor_term',variables=args)


@pytest.mark.parametrize('builder,args,_',SURFACES)
@pytest.mark.parametrize('tag',('',None,'not-a-tag','1bad'))
def test_invalid_definition_tags_are_rejected(builder,args,_,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


@pytest.mark.parametrize('prime',(False,True))
def test_unrestricted_factorization_existence_has_no_supplied_norm_unit_factors_or_choice(prime):
    name='gaussian_prime_factorization_exists' if prime else 'gaussian_irreducible_factorization_exists'
    expected='forall z. ('+frozen._gaussian('z','existence_carrier')+') -> ~(z=0) -> exists u b c l. ('+_factor('z','u','b','c','l','existence_result',prime=prime)+')'
    actual=next(r.statement for r in rows() if r.name==name)
    _assert_same_ast(_closed_formula(actual),_closed_formula(expected))


def test_gaussian_prime_is_not_merely_renamed_irreducibility_in_the_public_list():
    prime=_closed_formula('forall b c l. ('+candidate.gaussian_all_prime_relation('b','c','l',tag='real_prime',variables=('b','c','l'))+')')
    irreducible=_closed_formula('forall b c l. ('+candidate.gaussian_all_irreducible_relation('b','c','l',tag='real_irreducible',variables=('b','c','l'))+')')
    assert prime!=irreducible
    names={r.name for r in rows()}
    assert {'gaussian_irreducible_factorization_is_prime','gaussian_prime_factorization_is_irreducible'}<=names


def test_unit_empty_factorization_uses_the_actual_unit_itself_and_identity_trace():
    expected='forall z. ('+_unit('z','unit_given')+') -> ('+_factor('z','z','0','0','0','empty_factors')+')'
    actual=next(r.statement for r in rows() if r.name=='gaussian_unit_empty_factorization')
    _assert_same_ast(_closed_formula(actual),_closed_formula(expected))


# Independent explicit beta encodings, with CRT used only for finite examples.
def _beta_value(b,c,i):
    return b%(1+(i+1)*c)


def _beta_encode(values,*,scale=1):
    values=tuple(values)
    assert all(type(v) is int and v>=0 for v in values)
    c=scale*factorial(len(values))*(max(values,default=0)+1)
    b=0
    modulus=1
    for i,value in enumerate(values):
        current=1+(i+1)*c
        correction=((value-b)*pow(modulus,-1,current))%current
        b+=modulus*correction
        modulus*=current
    assert all(_beta_value(b,c,i)==value for i,value in enumerate(values))
    return b,c


def _product_example(factors,*,scale=1):
    factor_codes=tuple(_gaussian_encode(z) for z in factors)
    before=(1,0)
    products=[_gaussian_encode(before)]
    for factor in factors:
        before=_multiply(before,factor)
        products.append(_gaussian_encode(before))
    b,c=_beta_encode(factor_codes,scale=scale)
    h,e=_beta_encode(products,scale=scale)
    return b,c,len(factors),h,e,products[-1]


def _trace_holds(b,c,l,h,e,P):
    if _beta_value(h,e,0)!=6 or _beta_value(h,e,l)!=P:
        return False
    for i in range(l):
        factor=_gaussian_decode(_beta_value(b,c,i))
        before=_gaussian_decode(_beta_value(h,e,i))
        after=_gaussian_decode(_beta_value(h,e,i+1))
        if factor is None or before is None or after is None or _multiply(before,factor)!=after:
            return False
    return True


def _irreducible_value(z):
    if z is None or _norm_value(z)<=1:
        return False
    N=_norm_value(z)
    bound=isqrt(N)
    return not any(_proper_value((a,b),z,N) for a in range(-bound,bound+1) for b in range(-bound,bound+1))


def _factorization_holds(z,u,b,c,l,h,e,P):
    coefficient=_gaussian_decode(u)
    product=_gaussian_decode(P)
    result=_gaussian_decode(z)
    if coefficient is None or product is None or result is None or _norm_value(coefficient)!=1:
        return False
    if not _trace_holds(b,c,l,h,e,P) or _multiply(coefficient,product)!=result:
        return False
    return all(_irreducible_value(_gaussian_decode(_beta_value(b,c,i))) for i in range(l))


EXAMPLES=(
    (),((1,1),),((1,-1),),((3,0),),((2,1),),
    ((1,1),(1,1)),((1,1),(1,-1)),((2,1),(2,-1)),
    ((1,1),(1,1),(3,0)),((-1,-1),(2,1),(0,3)),
)


@pytest.mark.parametrize('factors',EXAMPLES)
def test_real_beta_factor_entries_and_every_actual_gaussian_product_step(factors):
    b,c,l,h,e,P=_product_example(factors)
    assert _trace_holds(b,c,l,h,e,P)
    assert _beta_value(h,e,0)==6
    assert all(_gaussian_decode(_beta_value(b,c,i))==factors[i] for i in range(l))
    before=(1,0)
    for i,factor in enumerate(factors):
        assert _gaussian_decode(_beta_value(h,e,i))==before
        before=_multiply(before,factor)
        assert _gaussian_decode(_beta_value(h,e,i+1))==before
    assert _gaussian_decode(P)==before
    assert _factorization_holds(P,6,b,c,l,h,e,P)


@pytest.mark.parametrize('unit',((1,0),(-1,0),(0,1),(0,-1)))
def test_each_actual_unit_has_empty_factorization_and_nonunique_leading_units_are_allowed(unit):
    b,c,l,h,e,P=_product_example(())
    u=_gaussian_encode(unit)
    assert l==0 and P==6
    assert _factorization_holds(u,u,b,c,l,h,e,P)
    assert _beta_value(6,6,0)==6
    assert _trace_holds(0,0,0,6,6,6)
    assert not _trace_holds(0,0,0,1,1,1)


@pytest.mark.parametrize('factors',EXAMPLES)
def test_different_beta_codes_preserve_the_same_actual_finite_factors_and_product(factors):
    first=_product_example(factors,scale=1)
    second=_product_example(factors,scale=2)
    b,c,l,h,e,P=first
    B,C,L,H,E,Q=second
    assert l==L and P==Q
    assert c!=C and e!=E
    assert all(_beta_value(b,c,i)==_beta_value(B,C,i) for i in range(l))
    assert _trace_holds(*first) and _trace_holds(*second)


@pytest.mark.parametrize('mutation',('factor','before','after','output','seed','raw_integer_multiply'))
def test_corrupted_beta_products_do_not_satisfy_the_actual_trace(mutation):
    factors=((1,1),(1,-1))
    b,c,l,h,e,P=_product_example(factors)
    values=[_beta_value(h,e,i) for i in range(l+1)]
    if mutation=='factor':
        b,c=_beta_encode([0,_gaussian_encode(factors[1])])
    elif mutation=='before':
        values[1]=1
        h,e=_beta_encode(values)
    elif mutation=='after':
        values[-1]=_gaussian_encode((3,0))
        h,e=_beta_encode(values)
    elif mutation=='output':
        P=_gaussian_encode((3,0))
    elif mutation=='seed':
        values[0]=1
        h,e=_beta_encode(values)
    else:
        values=[6,6*_gaussian_encode(factors[0]),6*_gaussian_encode(factors[0])*_gaussian_encode(factors[1])]
        h,e=_beta_encode(values)
        P=values[-1]
    assert not _trace_holds(b,c,l,h,e,P)


def test_zero_units_and_invalid_codes_cannot_be_listed_as_irreducible_factors():
    for value in ((0,0),(1,0),(-1,0),(0,1),(0,-1),(2,0)):
        b,c,l,h,e,P=_product_example((value,))
        assert _trace_holds(b,c,l,h,e,P)
        assert not _factorization_holds(P,6,b,c,l,h,e,P)
    assert not _irreducible_value(_gaussian_decode(1))
    for factors in EXAMPLES:
        b,c,l,h,e,P=_product_example(factors)
        assert _gaussian_decode(P)!=(0,0)
        assert not _factorization_holds(0,6,b,c,l,h,e,P)
        assert not _factorization_holds(P,0,b,c,l,h,e,P)


def test_repeated_associates_and_changed_unit_coefficient_give_real_distinct_factorizations():
    first=_product_example(((1,1),(1,1)))
    second=_product_example(((1,1),(1,-1)))
    target=_gaussian_encode((2,0))
    assert _factorization_holds(target,_gaussian_encode((0,-1)),*first)
    assert _factorization_holds(target,6,*second)
    assert first[2]==second[2]==2
    assert _beta_value(first[0],first[1],1)!=_beta_value(second[0],second[1],1)
    assert _multiply((0,-1),(1,1))==(1,-1)
    assert _gaussian_encode((0,-1))!=6


if __name__=='__main__':
    if sys.argv[1:2]==['--body']:
        resource.setrlimit(resource.RLIMIT_CPU,(45,50))
        signal.alarm(55)
        print(json.dumps(check_body(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'none')),flush=True)
    else:
        resource.setrlimit(resource.RLIMIT_CPU,(170,175))
        signal.alarm(180)
        for name in sys.argv[1:] or tuple(row.name for row in rows()):
            print(json.dumps(check_body(name)),flush=True)
