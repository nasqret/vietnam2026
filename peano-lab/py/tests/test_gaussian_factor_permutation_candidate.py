"""Original-kernel checks for witnessed Gaussian unit/permutation uniqueness."""

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
import time

import pytest

from peano_lab.library import gaussian_factor_permutation_candidate as candidate
from peano_lab.library import gaussian_product_reindex_candidate as reindex
from peano_lab.library import gaussian_euclidean_candidate as frozen
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.kernel.formulas import parse_formula_in_context
from test_gaussian_factorization_candidate import ROOT,core as factor_core,rows as factor_rows


SOURCE_SHA256='13d404c9870cf2ef2fb089749f60224b858d2954ec581bb37b09320c23055f1f'
NAMES_SHA256='9c6a54369036cbaede6a58dbcc7bd88a1b0d47309956ffbd5263f82d6d8a08b8'
PRINCIPAL_SHA256={
    'gaussian_irreducible_products_associate_unique':'5e1a53de75610e31309d21d16d2abed38033e440b31d6a39aaf07f2468097fe5',
    'gaussian_irreducible_factorizations_unique':'7d810c64c032063ac8f1cf0b13ee2f450f36853a898bbbf714939641d677db89',
    'gaussian_prime_factorizations_unique':'25362a390050bdd2b6b56a18b91f738860c534cb96779b0bdbeba3ef30064865',
    'gaussian_unique_prime_factorization':'57abdbebab6835ebe1fecb15f4229f2eee579b7d67c22638345cc0deb6e20219',
    'gaussian_zero_has_no_prime_factorization':'98f2d733c8b7cab7fce0324135b3985336b1cb9922936d723adf48379a213034',
    'gaussian_unit_prime_factorization_length_zero':'66bcf4d61ae664d21b59e77b66203fe3b2cffb1d360d4263f228984dd2f66b1b',
}
BODY_METRICS=(
    (18,12),(34,20),(129,40),(39,22),(59,20),(128,45),(57,38),(134,41),(381,64),
    (188,52),(42,24),(160,43),(827,74),(141,72),(98,45),(43,31),(54,31),(50,23),
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_gaussian_factor_permutation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return factor_core()|{row.name:row for row in (*factor_rows(),*reindex.make_gaussian_product_reindex_candidate_theorems(TheoremSpec))}


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
    elif mutation=='allow_zero':
        row=replace(row,statement=f"forall z. ({frozen._gaussian('z','mutated_domain')}) -> ({_unique('z','mutated_unique')})")
    elif mutation=='allow_invalid_code':
        row=replace(row,statement=f"forall z. ~(z=0) -> ({_unique('z','mutated_unique')})")
    elif mutation not in {'none'}:
        raise ValueError('unknown Gaussian factor-permutation mutation')
    if mutation!='none':
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,),core=table)
        return {'rejected':True,'mutation':mutation}
    return asdict(replay_candidate_bodies((row,),core=table)[0])


def isolated_body(name: str,mutation: str='none'):
    environment=os.environ.copy()
    environment['PYTHONPATH']=str(ROOT/'peano-lab/py')
    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--body',name,mutation],cwd=ROOT,env=environment,text=True,capture_output=True,timeout=185)
    assert result.returncode==0,result.stdout+result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize('name,metrics',tuple((row.name,m) for row,m in zip(rows(),BODY_METRICS,strict=True)))
def test_original_kernel_body(name,metrics):
    receipt=isolated_body(name)
    assert receipt['name']==name
    assert (receipt['proof_nodes'],receipt['proof_depth'])==metrics
    assert receipt['proof_objects']==receipt['proof_nodes']


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
@pytest.mark.parametrize('mutation',('false_conclusion','truncated_body'))
def test_false_or_incomplete_proof_is_rejected(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


@pytest.mark.parametrize('name',tuple(row.name for row in rows() if row.dependencies))
@pytest.mark.parametrize('mutation',('removed_dependency','corrupt_dependency'))
def test_missing_or_forged_prerequisite_is_rejected(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


@pytest.mark.parametrize('mutation',('allow_zero','allow_invalid_code'))
def test_full_unique_factorization_cannot_drop_domain_or_nonzero_guard(mutation):
    assert isolated_body('gaussian_unique_prime_factorization',mutation)['rejected'] is True


def check_nonvacuity(code: int):
    assert code in (6,20)
    table=core()|{row.name:row for row in rows()}
    call=lambda name,*args:(*(f'specialize {name} ({arg})' for arg in args),f'apply {name}')
    dependencies=['gaussian_unique_prime_factorization']
    script=call('gaussian_unique_prime_factorization',str(code))
    if code==6:
        dependencies.append('gaussian_one_valid')
        script+=('exact gaussian_one_valid',)
    else:
        dependencies+=['gaussian_representation_is_gaussian','gaussian_code_representation_transport','gaussian_natural_real_representation']
        script+=call('gaussian_representation_is_gaussian','20','2','0','0','0')
        script+=call('gaussian_code_representation_transport',frozen._pair('2*2','0'),'20','2','0','0','0')+('norm_num',)
        script+=call('gaussian_natural_real_representation','2')
    script+=('intro hzero','apply PA1','exact hzero')
    row=TheoremSpec('independent_gaussian_unique_example_'+str(code),_unique(str(code),'nonvacuous_example'),tuple(dependencies),script,'Checked actual-carrier nonvacuity instance, not an admitted catalogue row.')
    return asdict(replay_candidate_bodies((row,),core=table)[0])


@pytest.mark.parametrize('code',(6,20),ids=('gaussian_one','gaussian_real_two'))
def test_full_root_has_checked_unit_and_nonunit_carrier_instances(code):
    environment=os.environ.copy()
    environment['PYTHONPATH']=str(ROOT/'peano-lab/py')
    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--nonvacuity',str(code)],cwd=ROOT,env=environment,text=True,capture_output=True,timeout=185)
    assert result.returncode==0,result.stdout+result.stderr
    receipt=json.loads(result.stdout)
    assert receipt['proof_nodes']>0 and receipt['proof_depth']<=256


def test_exact_inventory_is_topological_and_not_an_admission_path():
    assert len(rows())==18
    assert sum(len(r.dependencies) for r in rows())==81
    assert sum(len(r.script) for r in rows())==1437
    assert sha256(('\n'.join(r.name for r in rows())+'\n').encode()).hexdigest()==NAMES_SHA256
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest()==SOURCE_SHA256
    seen=set(core())
    for row in rows():
        assert row.name not in seen and len(set(row.dependencies))==len(row.dependencies)
        assert set(row.dependencies)<=seen
        for dependency in row.dependencies:
            assert re.search(r'\b'+re.escape(dependency)+r'\b','\n'.join(row.script))
        assert row.script and not any(c.startswith(('use ','admit','sorry')) or 'DNE' in c for c in row.script)
        assert _closed_formula(row.statement) is not None
        seen.add(row.name)
    assert max(depth for _,depth in BODY_METRICS)==74
    assert max(nodes for nodes,_ in BODY_METRICS)==827


@pytest.mark.parametrize('name,expected',tuple(PRINCIPAL_SHA256.items()))
def test_exact_principal_statement_pin(name,expected):
    assert sha256(next(r.statement for r in rows() if r.name==name).encode()).hexdigest()==expected


# Expected contracts independently expand beta arithmetic, unit witnesses,
# RingPrime, products and finite bijections. Only frozen v28 G081 arithmetic
# graphs are reused; no new candidate-definition builder supplies an oracle.
def _and(*parts):
    result=f'({parts[-1]})'
    for part in reversed(parts[:-1]):
        result=f'({part}) /\\ ({result})'
    return result


def _lt(a,b,tag):
    return f'exists igfp_gap_{tag}. igfp_gap_{tag}+S ({a})=({b})'


def _at(b,c,i,a,tag):
    return _and(f'exists igfp_h_{tag}. igfp_h_{tag}+S ({a})=S ((S ({i}))*({c}))',
                f'exists igfp_q_{tag}. ({b})=igfp_q_{tag}*S ((S ({i}))*({c}))+({a})')


def _unit(z,tag):
    v='igfp_inverse_'+tag
    return f'exists {v}. ({frozen._code_mul(z,v,"6",tag+"mul")})'


def _associate(a,b,tag):
    u='igfp_unit_'+tag
    return f'exists {u}. '+_and(_unit(u,tag+'unit'),frozen._code_mul(u,a,b,tag+'mul'))


def _dvd(d,z,tag):
    q='igfp_quotient_'+tag
    return f'exists {q}. ({frozen._code_mul(d,q,z,tag+"mul")})'


def _prime(p,tag):
    a,b,c=('igfp_'+r+'_'+tag for r in ('prime_a','prime_b','prime_c'))
    property=f'forall {a} {b} {c}. ({frozen._code_mul(a,b,c,tag+"product")}) -> ({_dvd(p,c,tag+"divisor")}) -> ({_dvd(p,a,tag+"left")}) \\/ ({_dvd(p,b,tag+"right")})'
    return _and(frozen._gaussian(p,tag+'valid'),f'~(({p})=0)',f'~({_unit(p,tag+"nonunit")})',property)


def _all_prime(b,c,l,tag):
    i,p='igfp_index_'+tag,'igfp_factor_'+tag
    return f'forall {i} {p}. ({_lt(i,l,tag+"bound")}) -> ({_at(b,c,i,p,tag+"entry")}) -> ({_prime(p,tag+"prime")})'


def _product(b,c,l,P,tag):
    h,e,i,a,R,T=('igfp_'+r+'_'+tag for r in ('trace','scale','index','factor','before','after'))
    step=f'forall {i}. ({_lt(i,l,tag+"index")}) -> exists {a} {R} {T}. '+_and(
        _at(b,c,i,a,tag+'factor'),_at(h,e,i,R,tag+'before'),_at(h,e,f'S ({i})',T,tag+'after'),frozen._code_mul(R,a,T,tag+'multiply'))
    return f'exists {h} {e}. '+_and(_at(h,e,'0','6',tag+'start'),_at(h,e,l,P,tag+'end'),step)


def _prime_factor(z,u,b,c,l,tag):
    P='igfp_actual_product_'+tag
    return _and(_unit(u,tag+'unit'),_all_prime(b,c,l,tag+'all'),f'exists {P}. '+_and(_product(b,c,l,P,tag+'product'),frozen._code_mul(u,P,z,tag+'reconstruct')))


def _permutation(u,v,l,tag):
    i,j,a=('igfp_'+r+'_'+tag for r in ('map_index','map_second','map_image'))
    bounded=f'forall {i}. ({_lt(i,l,tag+"bound_i")}) -> exists {a}. '+_and(_at(u,v,i,a,tag+'bound_entry'),_lt(a,l,tag+'bound_a'))
    injective=f'forall {i} {j} {a}. ({_lt(i,l,tag+"inj_i")}) -> ({_lt(j,l,tag+"inj_j")}) -> ({_at(u,v,i,a,tag+"inj_first")}) -> ({_at(u,v,j,a,tag+"inj_second")}) -> {i}={j}'
    surjective=f'forall {a}. ({_lt(a,l,tag+"onto_a")}) -> exists {i}. '+_and(_lt(i,l,tag+'onto_i'),_at(u,v,i,a,tag+'onto_entry'))
    return _and(bounded,injective,surjective)


def _matching(b,c,d,e,u,v,l,tag):
    i,j,p,q=('igfp_'+r+'_'+tag for r in ('source_index','target_index','source_factor','target_factor'))
    return f'forall {i} {j} {p} {q}. ({_lt(i,l,tag+"index")}) -> ({_at(u,v,i,j,tag+"map")}) -> ({_at(b,c,i,p,tag+"source")}) -> ({_at(d,e,j,q,tag+"target")}) -> ({_associate(p,q,tag+"associate")})'


def _matched(b,c,d,e,u,v,l,tag):
    return _and(_permutation(u,v,l,tag+'permutation'),_matching(b,c,d,e,u,v,l,tag+'matching'))


def _permutation_relation(b,c,l,d,e,m,u,v,tag):
    return _and(f'({l})=({m})',_matched(b,c,d,e,u,v,l,tag+'matched'))


def _unique(z,tag):
    u,b,c,l,v,d,e,m,U,V=('igfp_'+r+'_'+tag for r in ('unit','code','scale','length','other_unit','other_code','other_scale','other_length','map','map_scale'))
    comparison=_and(f'{l}={m}',f'exists {U} {V}. ({_matched(b,c,d,e,U,V,l,tag+"matching")})')
    return f'exists {u} {b} {c} {l}. '+_and(_prime_factor(z,u,b,c,l,tag+'chosen'),f'forall {v} {d} {e} {m}. ({_prime_factor(z,v,d,e,m,tag+"other")}) -> ({comparison})')


PUBLIC=(
    (candidate.gaussian_factor_associate_matching_relation,_matching,('b','c','d','e','u','v','l')),
    (candidate.gaussian_factor_permutation_relation,_permutation_relation,('b','c','l','d','e','m','u','v')),
    (candidate.gaussian_unique_prime_factorization_relation,_unique,('z',)),
)


def _same_ast(first,second):
    """Exact iterative structural equality, including shared binary numerals.

    This test helper does not alter Python recursion limits, expand enormous
    unary integers, use hashes as equality, or change the mathematical AST.
    """
    pending=[(first,second)]
    seen=set()
    while pending:
        a,b=pending.pop()
        if a is b:
            continue
        if type(a) is not type(b):
            return False
        key=(id(a),id(b))
        if key in seen:
            continue
        seen.add(key)
        assert len(seen)<2_000_000
        if is_dataclass(a):
            pending.extend((getattr(a,f.name),getattr(b,f.name)) for f in fields(a))
        elif isinstance(a,(tuple,list)):
            if len(a)!=len(b):
                return False
            pending.extend(zip(a,b))
        elif a!=b:
            return False
    return True


@pytest.mark.parametrize('builder,expected,args',PUBLIC,ids=('matching','permutation','full_unique'))
def test_public_relation_exact_independent_ast(builder,expected,args):
    assert _same_ast(parse_formula_in_context(builder(*args,tag='public_test',variables=args),list(args)),parse_formula_in_context(expected(*args,'expected'),list(args)))


@pytest.mark.parametrize('builder,expected,args',PUBLIC,ids=('matching','permutation','full_unique'))
@pytest.mark.parametrize('term',('a+b','a*b','S (a+b)','0','6',str(2**96+7)))
def test_public_relations_accept_full_trusted_terms(builder,expected,args,term):
    terms=(term,)+args[1:]
    context=tuple(dict.fromkeys(('a','b',*args)))
    actual=builder(*terms,tag='compound',variables=context)
    explicit=expected(*('('+t+')' for t in terms),'compound_expected')
    assert _same_ast(parse_formula_in_context(actual,list(context)),parse_formula_in_context(explicit,list(context)))


@pytest.mark.parametrize('builder,expected,args',PUBLIC,ids=('matching','permutation','full_unique'))
def test_iterative_ast_comparison_rejects_an_actual_changed_large_term(builder,expected,args):
    context=tuple(dict.fromkeys(('a','b',*args)))
    first=builder(str(2**96+7),*args[1:],tag='large_first',variables=context)
    second=builder(str(2**96+8),*args[1:],tag='large_second',variables=context)
    assert not _same_ast(parse_formula_in_context(first,list(context)),parse_formula_in_context(second,list(context)))


def _capture_cases():
    for builder,_,args in PUBLIC:
        source=builder(*args,tag='capture',variables=args)
        names=sorted({name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()})
        for name in names:
            yield builder,args,name


@pytest.mark.parametrize('builder,args,binder',tuple(_capture_cases()),ids=lambda item:item if isinstance(item,str) else None)
def test_every_generated_binder_protects_even_unused_caller_names(builder,args,binder):
    with pytest.raises(ValueError):
        builder(*args,tag='capture',variables=(*args,binder))


@pytest.mark.parametrize('builder,expected,args',PUBLIC,ids=('matching','permutation','full_unique'))
@pytest.mark.parametrize('bad',('unknown','a = 0','exists a. a','-1','a; false','__import__(a)'))
def test_public_terms_do_not_accept_formula_or_code_injection(builder,expected,args,bad):
    with pytest.raises((ValueError,TypeError)):
        builder(bad,*args[1:],tag='reject',variables=args)


@pytest.mark.parametrize('builder,expected,args',PUBLIC,ids=('matching','permutation','full_unique'))
@pytest.mark.parametrize('bad_context',((),[],('a','a'),('a b',),('S',)))
def test_public_context_must_be_explicit_distinct_identifiers(builder,expected,args,bad_context):
    with pytest.raises((ValueError,TypeError)):
        builder(*args,tag='reject',variables=bad_context)


def test_full_g082_root_has_only_actual_carrier_and_nonzero_premises():
    row=next(row for row in rows() if row.name=='gaussian_unique_prime_factorization')
    expected=f'forall z. ({frozen._gaussian("z","independent_domain")}) -> ~(z=0) -> ({_unique("z","independent_full")})'
    assert _closed_formula(row.statement)==_closed_formula(expected)
    assert 'gaussian_prime_factorization_exists' in row.dependencies
    assert 'gaussian_prime_factorizations_unique' in row.dependencies


def test_uniqueness_compares_every_other_actual_prime_factorization():
    row=next(row for row in rows() if row.name=='gaussian_prime_factorizations_unique')
    expected=f'forall z u b c l v d e m. ({_prime_factor("z","u","b","c","l","first")}) -> ({_prime_factor("z","v","d","e","m","second")}) -> '+_and('l=m',f'exists U V. ({_matched("b","c","d","e","U","V","l","comparison")})')
    assert _closed_formula(row.statement)==_closed_formula(expected)


def test_full_contract_cannot_be_replaced_by_unit_only_or_tautological_factor_data():
    row=next(row for row in rows() if row.name=='gaussian_unique_prime_factorization')
    weak=f'forall z. ({frozen._gaussian("z","weak_domain")}) -> ~(z=0) -> exists u b c l. ({_prime_factor("z","u","b","c","l","existence_only")})'
    assert _closed_formula(row.statement)!=_closed_formula(weak)
    assert _closed_formula(row.statement)!=_closed_formula('forall z. z=z')


UNITS=((1,0),(-1,0),(0,1),(0,-1))


def _multiply(a,b):
    return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])


def _signed_code(n):
    return 2*n if n>=0 else -2*n-1


def _code(z):
    a,b=map(_signed_code,z)
    return (a+b)*(a+b+1)+2*b


def _product_model(values):
    result=(1,0)
    for value in values:
        result=_multiply(result,value)
    return result


def _associate_unit(a,b):
    return next((u for u in UNITS if _multiply(u,a)==b),None)


def _matches(source,target,mapping):
    return len(source)==len(target)==len(mapping) and sorted(mapping)==list(range(len(source))) and all(_associate_unit(source[i],target[j]) is not None for i,j in enumerate(mapping))


def _irreducible_model(z):
    norm=z[0]*z[0]+z[1]*z[1]
    if norm<=1:
        return False
    limit=isqrt(norm)
    for a in range(-limit,limit+1):
        for b in range(-limit,limit+1):
            divisor_norm=a*a+b*b
            if 1<divisor_norm<norm:
                real=z[0]*a+z[1]*b
                imaginary=z[1]*a-z[0]*b
                if real%divisor_norm==imaginary%divisor_norm==0:
                    return False
    return True


@pytest.mark.parametrize('value,expected',(((1,1),True),((2,1),True),((3,0),True),((1,-1),True),((5,0),False),((0,0),False),*((u,False) for u in UNITS)))
def test_numeric_factor_examples_are_actual_irreducibles_not_just_labels(value,expected):
    assert _irreducible_model(value) is expected


@pytest.mark.parametrize('length',range(9))
@pytest.mark.parametrize('leading',UNITS)
def test_model_repeated_associates_all_units_and_explicit_bijection(length,leading):
    basis=((1,1),(2,1),(3,0))
    source=tuple(basis[i%3] for i in range(length))
    mapping=tuple(reversed(range(length)))
    target=[None]*length
    multipliers=[]
    for i,j in enumerate(mapping):
        u=UNITS[(i+length)%4]
        target[j]=_multiply(u,source[i])
        multipliers.append(u)
    scale=_product_model(multipliers)
    adjusted=_multiply(leading,(scale[0],-scale[1]))
    assert _matches(source,target,mapping)
    assert _multiply(leading,_product_model(source))==_multiply(adjusted,_product_model(target))
    assert all(_multiply(multipliers[i],source[i])==target[j] for i,j in enumerate(mapping))
    assert all(_code(z)%2==0 for z in (*source,*target))


@pytest.mark.parametrize('bad',((0,0),(1,1),(0,2),(1,),()))
def test_equal_associate_predicates_do_not_replace_a_real_bijection(bad):
    p=(1,1)
    source=(p,p)
    target=(p,_multiply((0,1),p))
    assert not _matches(source,target,bad)
    assert _matches(source,target,(0,1))


def test_same_norm_is_not_the_witnessed_associate_relation():
    assert 1*1+8*8==4*4+7*7
    assert _associate_unit((1,8),(4,7)) is None
    assert _associate_unit((1,8),(-8,1))==(0,1)


def test_literal_factor_and_leading_unit_uniqueness_would_be_false():
    p=(1,1)
    q=_multiply((0,1),p)
    assert p!=q and _code(p)!=_code(q)
    assert _multiply((1,0),p)==_multiply((0,-1),q)
    assert _matches((p,),(q,),(0,))


def test_gaussian_identity_is_code_six_and_empty_product_is_not_natural_one():
    assert _product_model(())==(1,0)
    assert _code(_product_model(()))==6
    assert {_code(u) for u in UNITS}=={2,4,6,10}
    assert _code((0,0))==0
    assert 1 not in {_code((a,b)) for a in range(-10,11) for b in range(-10,11)}


def test_large_signed_associate_examples_do_not_use_decimal_integer_conversion():
    value=(2**4096+1,-(2**3072+3))
    rotated=_multiply((0,1),value)
    assert _associate_unit(value,rotated)==(0,1)
    assert _matches((value,rotated),(rotated,value),(1,0))
    assert _code(value).bit_length()>8192


if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    if sys.argv[1:2]==['--body']:
        start=time.monotonic()
        result=check_body(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'none')
        result['elapsed_seconds']=time.monotonic()-start
        result['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        assert result['peak_rss_bytes']<1536*1024*1024
        print(json.dumps(result))
    elif sys.argv[1:2]==['--nonvacuity']:
        print(json.dumps(check_nonvacuity(int(sys.argv[2]))))
    else:
        for name in sys.argv[1:] or tuple(row.name for row in rows()):
            print(json.dumps(check_body(name)),flush=True)
