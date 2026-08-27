"""Independent witnesses, hygiene and bounded original-HA Gaussian search tests.

Numeric models explain boundaries only. Actual proof authority comes from
fresh original-kernel body replays, not from these finite semantic samples.
"""

from __future__ import annotations

from dataclasses import asdict,fields,is_dataclass,replace
from functools import lru_cache
from hashlib import sha256
import json
from math import isqrt
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys

import pytest

from peano_lab.library import gaussian_factor_search_candidate as candidate
from peano_lab.library import gaussian_ring_candidate as ring
from peano_lab.library import gaussian_divisibility_candidate as divisibility
from peano_lab.library import gaussian_euclidean_candidate as frozen
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.theorems import TheoremSpec,_closed_formula


ROOT=Path(__file__).resolve().parents[3]
PARENT_SHA256='897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9'
SOURCE_SHA256='039bb7e5d7bb3c3fe1acd3177904c99c62ecfd78424685e78c8c5dc28cd1b6ce'
NAMES_SHA256='dfaafb2936490caa68249b49d11eb4387384f99cf6b8d9395b555575f98b3d0f'
PRINCIPAL_SHA256={
    'gaussian_factor_search_complete':'9926344b2a34492cb1928b617220da4a3615ec961af22669528c3aa256b8c24f',
    'gaussian_irreducible_or_strict_nonunit_factorization':'6928892156d2f3665c38c75cf24c30ef6b0889513d0005682aa427db2389502b',
    'gaussian_irreducible_decidable':'d2dda07b5adbba8a24df4aacbc1921b52c969822b96f7bbd9a61b484784bc3e9',
    'gaussian_irreducible_divisor_exists':'2a02aba7eb6203e77da394745ecdbb8149b1191fc3223a0eaa59e75d32524e94',
    'gaussian_nonunit_divisor_strict_quotient':'8cbf9d7d2d8dfb012b94575c204d0b1c7cd3d010b57f008a5b6baf462842fd0b',
    'gaussian_irreducible_factor_reduction':'18ffc5a77578c848d446aa5f180a4b98bd09f0adeadd4e8f1ef57366a44fe146',
}
BODY_METRICS=(
    (31,13,29),(236,37,220),(24,16,24),(94,29,94),(17,12,17),(30,16,30),
    (22,13,22),(79,27,79),(108,31,108),(123,31,123),(47,19,47),(89,25,89),
    (42,25,42),(97,29,95),(90,37,90),(20,13,20),(202,39,199),(98,34,98),
    (82,24,82),(132,39,132),(25,16,25),(137,39,135),(74,24,74),
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_gaussian_factor_search_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    payload=(ROOT/'artifacts/peano-library/alpha/catalog-v28.json').read_bytes()
    assert sha256(payload).hexdigest()==PARENT_SHA256
    document=json.loads(payload)
    assert document['theorem_count']==document['checked_use_count']==2764
    assert document['stable_count']==432
    result={r['name']:TheoremSpec(r['name'],r['statement'],tuple(r['dependencies']),tuple(r['script']),r.get('summary','')) for r in document['theorems']}
    result.update((row.name,row) for factory in (ring.make_gaussian_ring_candidate_theorems,divisibility.make_gaussian_divisibility_candidate_theorems) for row in factory(TheoremSpec))
    return result


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
        name=row.dependencies[0]
        table=table|{name:replace(table[name],statement='0=0')}
    elif mutation in {'no_norm','allow_zero','allow_unit'}:
        premises=[_norm('z','N','guard_norm'),'~(z=0)',f'~({_unit("z","guard_nonunit")})']
        premises.pop({'no_norm':0,'allow_zero':1,'allow_unit':2}[mutation])
        statement='forall z N. '+' -> '.join(f'({p})' for p in premises)+f' -> ({_reduction("z","N","guard_result")})'
        row=replace(row,statement=statement)
    elif mutation!='none':
        raise ValueError('unknown Gaussian search proof mutation')
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


@pytest.mark.parametrize('mutation',('no_norm','allow_zero','allow_unit'))
def test_factor_reduction_cannot_drop_actual_domain_or_nonzero_nonunit_guards(mutation):
    assert isolated_body('gaussian_irreducible_factor_reduction',mutation)['rejected'] is True


def test_exact_candidate_inventory_is_topological_constructive_and_has_no_unused_edges():
    assert len(rows())==23 and sum(len(r.dependencies) for r in rows())==107
    assert sum(len(r.script) for r in rows())==1140
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
    assert sum(m[0] for m in BODY_METRICS)==1899
    assert sum(m[2] for m in BODY_METRICS)==1874
    assert max(m[0] for m in BODY_METRICS)==236 and max(m[1] for m in BODY_METRICS)==39


@pytest.mark.parametrize('name,expected',tuple(PRINCIPAL_SHA256.items()))
def test_exact_principal_statement_pin(name,expected):
    assert sha256(next(r.statement for r in rows() if r.name==name).encode()).hexdigest()==expected


# Independent first-order expansions. Only unchanged v28 carrier arithmetic
# is reused; none of the new search-definition builders supplies an expected AST.
def _and(*parts):
    result=f'({parts[-1]})'
    for part in reversed(parts[:-1]):
        result=f'({part}) /\\ ({result})'
    return result


def _le(a,b,tag):
    return f'exists independent_le_{tag}. independent_le_{tag}+({a})=({b})'


def _lt(a,b,tag):
    return f'exists independent_lt_{tag}. independent_lt_{tag}+S ({a})=({b})'


def _pair(a,b):
    return f'(({a})+({b}))*S (({a})+({b}))+(({b})+({b}))'


def _unit(z,tag):
    return f'exists independent_inverse_{tag}. ({frozen._code_mul(z,"independent_inverse_"+tag,"6",tag+"unit")})'


def _norm(z,N,tag):
    return frozen._code_norm(z,N,tag+'norm')


def _dvd(d,z,tag):
    return f'exists independent_quotient_{tag}. ({frozen._code_mul(d,"independent_quotient_"+tag,z,tag+"divisor")})'


def _irreducible(z,tag):
    a,b='independent_first_'+tag,'independent_second_'+tag
    return _and(frozen._gaussian(z,tag+'valid'),f'~(({z})=0)',f'~({_unit(z,tag+"nonunit")})',
        f'forall {a} {b}. ({frozen._code_mul(a,b,z,tag+"factor")}) -> ({_unit(a,tag+"left")}) \\/ ({_unit(b,tag+"right")})')


def _coordinates(z,N,tag):
    r,i='independent_real_'+tag,'independent_imaginary_'+tag
    return f'exists {r} {i}. '+_and(f'({z})={_pair(r,i)}',_le(r,f'2*({N})',tag+'real'),_le(i,f'2*({N})',tag+'imaginary'))


def _proper(d,z,N,tag):
    D='independent_norm_'+tag
    return _and(f'~({_unit(d,tag+"nonunit")})',_dvd(d,z,tag+'divisor'),
                f'exists {D}. '+_and(_norm(d,D,tag+'norm'),_lt(D,N,tag+'strict')))


def _split(z,N,a,b,A,B,tag):
    return _and(frozen._code_mul(a,b,z,tag+'product'),_norm(a,A,tag+'first'),_norm(b,B,tag+'second'),
                f'~({_unit(a,tag+"firstnonunit")})',f'~({_unit(b,tag+"secondnonunit")})',
                _lt(A,N,tag+'firststrict'),_lt(B,N,tag+'secondstrict'))


def _reduction(z,N,tag):
    p,q,Q='independent_prime_'+tag,'independent_factor_'+tag,'independent_norm_'+tag
    return f'exists {p} {q} {Q}. '+_and(_irreducible(p,tag+'irreducible'),
        frozen._code_mul(p,q,z,tag+'product'),_norm(q,Q,tag+'norm'),_lt(Q,N,tag+'strict'),f'~({q}=0)')


def _assert_same_ast(left,right):
    pending=[(left,right)]
    while pending:
        a,b=pending.pop()
        assert type(a) is type(b)
        if is_dataclass(a):
            pending.extend((getattr(a,f.name),getattr(b,f.name)) for f in fields(a))
        elif isinstance(a,tuple):
            assert len(a)==len(b)
            pending.extend(zip(a,b,strict=True))
        else:
            assert a==b


SURFACES=(
    (candidate.gaussian_norm_bounded_coordinates_relation,('z','N'),_coordinates),
    (candidate.gaussian_proper_norm_divisor_relation,('d','z','N'),_proper),
    (candidate.gaussian_strict_nonunit_factorization_relation,('z','N','a','b','A','B'),_split),
)


@pytest.mark.parametrize('builder,arguments,independent',SURFACES,ids=('coordinates','proper_divisor','strict_split'))
@pytest.mark.parametrize('variant',('plain','compound','large_numeral'))
def test_public_relations_have_exact_independent_hygienic_asts(builder,arguments,independent,variant):
    context=tuple(arguments)+('unused',)
    actual=arguments
    if variant=='compound':
        actual=tuple(f'S ({x}+unused)' for x in arguments)
    elif variant=='large_numeral':
        actual=(str((1<<96)+31),*arguments[1:])
    expression=builder(*actual,tag='public_alpha',variables=context)
    expected=independent(*actual,'public_independent')
    _assert_same_ast(parse_formula_in_context(expression,list(context)),parse_formula_in_context(expected,list(context)))
    alternate=builder(*actual,tag='public_beta',variables=context)
    _assert_same_ast(parse_formula_in_context(expression,list(context)),parse_formula_in_context(alternate,list(context)))


def _generated_binder_cases():
    result=[]
    for builder,args,_ in SURFACES:
        expression=builder(*args,tag='collision_audit',variables=args)
        binders=sorted({name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',expression) for name in clause.split()})
        assert binders
        result.extend((builder,args,binder) for binder in binders)
    return tuple(result)


@pytest.mark.parametrize('builder,args,binder',_generated_binder_cases(),ids=lambda item:getattr(item,'__name__',str(item)))
def test_every_generated_and_nested_legacy_binder_rejects_full_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='collision_audit',variables=(*args,binder))


@pytest.mark.parametrize('builder,args,_',SURFACES)
@pytest.mark.parametrize('context',([],(),None,'z N',('z','z'),('bad variable',)))
def test_invalid_public_contexts_are_rejected(builder,args,_,context):
    with pytest.raises(ValueError):
        builder(*args,tag='context_audit',variables=context)


@pytest.mark.parametrize('builder,args,_',SURFACES)
@pytest.mark.parametrize('term',('','undeclared','z = z','forall k. k','z) -> false -> (z'))
def test_nonterms_or_unknown_variables_cannot_enter_public_relations(builder,args,_,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='term_audit',variables=args)


@pytest.mark.parametrize('builder,args,_',SURFACES)
@pytest.mark.parametrize('tag',('',None,'not-a-tag','1bad'))
def test_invalid_definition_tags_are_rejected(builder,args,_,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


def test_full_factor_reduction_statement_has_no_supplied_factor_or_choice_oracle():
    expected='forall z N. ('+_norm('z','N','expected_norm')+') -> ~(z=0) -> ~('+_unit('z','expected_nonunit')+') -> ('+_reduction('z','N','expected_result')+')'
    actual=next(r.statement for r in rows() if r.name=='gaussian_irreducible_factor_reduction')
    _assert_same_ast(_closed_formula(actual),_closed_formula(expected))


def test_complete_finite_search_returns_witness_or_absence_for_all_gaussian_divisors():
    expected='forall z N. ('+_norm('z','N','complete_norm')+') -> ((exists d. ('+_proper('d','z','N','complete_yes')+')) \\/ (forall e. ~('+_proper('e','z','N','complete_no')+')))'
    actual=next(r.statement for r in rows() if r.name=='gaussian_factor_search_complete')
    _assert_same_ast(_closed_formula(actual),_closed_formula(expected))


# Independent integer model for explanatory boundary checks, not proof authority.
def _signed_encode(value):
    return 2*value if value>=0 else -2*value-1


def _signed_decode(code):
    return code//2 if code%2==0 else -(code//2+1)


def _pair_value(a,b):
    return (a+b)*(a+b+1)+2*b


def _gaussian_encode(z):
    return _pair_value(_signed_encode(z[0]),_signed_encode(z[1]))


def _gaussian_decode(code):
    if code<0 or code%2:
        return None
    length=(isqrt(4*code+1)-1)//2
    second=(code-length*(length+1))//2
    assert 0<=second<=length
    return _signed_decode(length-second),_signed_decode(second)


def _norm_value(z):
    return z[0]*z[0]+z[1]*z[1]


def _multiply(a,b):
    return a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]


def _quotient(z,d):
    D=_norm_value(d)
    if D==0:
        return (0,0) if z==(0,0) else None
    real=z[0]*d[0]+z[1]*d[1]
    imaginary=z[1]*d[0]-z[0]*d[1]
    return None if real%D or imaginary%D else (real//D,imaginary//D)


def _proper_value(d,z,N):
    return _norm_value(d)!=1 and _norm_value(d)<N and _quotient(z,d) is not None


def test_canonical_gaussian_identity_zero_units_and_invalid_natural_codes():
    assert _gaussian_encode((0,0))==0 and _gaussian_encode((1,0))==6
    assert {_gaussian_encode(z) for z in ((1,0),(-1,0),(0,1),(0,-1))}=={2,4,6,10}
    assert _gaussian_decode(1) is None
    for a in range(-9,10):
        for b in range(-9,10):
            assert _gaussian_decode(_gaussian_encode((a,b)))==(a,b)
    for code in range(128):
        decoded=_gaussian_decode(code)
        assert (decoded is None)==(code%2==1)
        if decoded is not None:
            assert _gaussian_encode(decoded)==code


@pytest.mark.parametrize('value',range(-12,13))
def test_signed_coordinate_bound_handles_both_signs_zero_and_sharp_positive_unit(value):
    square=value*value
    code=_signed_encode(value)
    assert code<=2*square
    assert _signed_decode(code)==value
    if value==1:
        assert code==2*square
    if value==0:
        assert code==square==0


@pytest.mark.parametrize('z',((0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(2,0),(-2,0),(0,2),(3,0),(2,1),(2,-1),(3,2),(4,0),(3,3),(5,0)))
def test_actual_coordinate_rectangle_matches_independent_integer_divisor_search(z):
    N=_norm_value(z)
    actual=[]
    for real_code in range(2*N+1):
        for imaginary_code in range(2*N+1):
            d=_signed_decode(real_code),_signed_decode(imaginary_code)
            code=_pair_value(real_code,imaginary_code)
            assert _gaussian_decode(code)==d
            if _proper_value(d,z,N):
                actual.append(d)
                assert real_code<=2*N and imaginary_code<=2*N
                q=_quotient(z,d)
                assert q is not None and _multiply(d,q)==z
                assert _norm_value(d)!=1 and _norm_value(q)!=1
                assert _norm_value(d)<N and _norm_value(q)<N
    bound=isqrt(N)
    independent={(a,b) for a in range(-bound,bound+1) for b in range(-bound,bound+1) if _proper_value((a,b),z,N)}
    assert set(actual)==independent
    if z in ((0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(3,0),(2,1),(2,-1),(3,2)):
        assert not actual
    if z in ((2,0),(-2,0),(0,2),(4,0),(3,3),(5,0)):
        assert actual


@pytest.mark.parametrize('p',((1,1),(1,-1),(2,1),(3,0),(-3,0)))
def test_reduction_of_an_irreducible_allows_the_unit_quotient(p):
    q=_quotient(p,p)
    assert q==(1,0) and _norm_value(q)==1
    assert _norm_value(q)<_norm_value(p)
    assert _multiply(p,q)==p and _gaussian_encode(q)==6
    assert not _proper_value(p,p,_norm_value(p))


def test_zero_units_and_invalid_codes_are_real_counterexamples_to_dropped_reduction_guards():
    assert not any(_proper_value((a,b),(0,0),0) for a in range(-3,4) for b in range(-3,4))
    for unit in ((1,0),(-1,0),(0,1),(0,-1)):
        for a in range(-3,4):
            for b in range(-3,4):
                d=(a,b)
                if _quotient(unit,d) is not None:
                    assert _norm_value(d)==1
    assert _gaussian_decode(1) is None


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
