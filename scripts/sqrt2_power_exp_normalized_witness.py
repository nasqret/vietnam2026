"""AP058: construct actual normalized large-argument truncation data.

The existing total finite exponential construction supplies weights, terms,
positive normalization and every factorial/power identity. Construct the
binary and majorant powers and the short sum, then apply AP057 to those same
values. The result is finite arithmetic, not a real exponential object.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_normalized_truncation import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,canonical,json_hash,
    source_registry,exp_normalized_truncation_source_pins,NAMED_SOURCE as TRUNCATION_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_geometric_majorant import COMPARISON_ARCHIVE
from sqrt2_power_scaled_exp_terms import NAMED_SOURCE as CONSTRUCTED_SOURCE,COMPOSITION_ARCHIVE
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE
from sqrt2_power_quadratic_trace_exists import field
from sqrt2_power_log_exp_witness import conjoin
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-normalized-witness-v1'
PARAMETERS=('d','x','L','K','m','N')
W,T=('wb','wc'),('tb','tc')
H='(K+m)+N'
PREMISES=('~d=0','Le(x,L*d)','Le(2*L,K)')
CONSTRUCTED_OUTPUTS=W+T+('h','f','q','t')
OUTPUTS=CONSTRUCTED_OUTPUTS+('p','B','s')
NORMALIZATION=f'forall j v fj dj xj. Le(j,{H}) -> BetaAt(tb,tc,j,v) -> Factorial(j,fj) -> Pow(d,j,dj) -> Pow(x,j,xj) -> (v*fj)*dj=h*xj'
PARTS=(f'NatExpWeightTable(d,{H},wb,wc)',f'NatPowerWeightedPrefix(x,wb,wc,tb,tc,S({H}))',
    'BetaAt(wb,wc,0,h)','BetaAt(tb,tc,0,h)','~h=0',f'Factorial({H},f)',f'Pow(d,{H},q)','h=f*q',
    f'Sum(tb,tc,S({H}),t)',f'NatScaledExpRecurrence(d,x,tb,tc,{H})',NORMALIZATION,
    'Pow(2,m,p)','~p=0','Pow(L,K,B)','Sum(tb,tc,K+m,s)','Le(s,t)','Le(p*t,p*s+2*(B*h))')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='d7fe383cf8b88b0d32538bcdd03ef48992ec2b80666f1188f153a402dde188e5'
TRUNCATION_ARCHIVE=dict(case='AP057',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-normalized-truncation-v1/generation-process.json.gz',
    bytes=67570,sha256='d1c91829178a68f405c22b7a9b0eb0b6f6857195d4f0be117a05ac69e3e50856',
    raw_bytes=801026,raw_sha256='cb4089aea9cd6f88f3448559704714f3bbf25cba2f352c266a78ed901be2d525',
    bundle_bytes=422324,bundle_sha256='cc59b8f6360dec4a08b2e261e02420319cf7924020589c9285163adb763d294c',
    nodes=160,root=159,target_ast_sha256='f74987c7317766d697ca0d5792985ab700e38691f10bd6149d8c1ca141fc33b9')
ARCHIVES=(TRUNCATION_ARCHIVE,EXP_ARCHIVE,COMPARISON_ARCHIVE,COMPOSITION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'truncation':TRUNCATION_SOURCE,'constructed':CONSTRUCTED_SOURCE,
    'power_exists':'forall d n. exists p. Pow(d,n,p)',
    'power_nonzero':'forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0',
    'succ_ne_zero':'forall a. ~S a=0',
    'sum_exists':'forall b c N. exists n. Sum(b,c,N,n)',
}
ENDPOINT_OWNERS=dict(truncation='AP057',constructed='CV070',power_exists='AP010',power_nonzero='AP010',succ_ne_zero='CV071',sum_exists='CV061')
HELPER_DEPENDENCIES={'AP058':tuple(ENDPOINT_SOURCES)}


class ExpNormalizedWitnessError(ValueError):
    """Changed actual table, original normalization, power or error witness."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatExpWeightTable','NatPowerWeightedPrefix','Factorial','Pow','Sum','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpNormalizedWitnessError('existing normalized witness definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_normalized_witness_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=3 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpNormalizedWitnessError('AP058 exact normalized finite witness changed')
    return target


def source_contract():
    return dict(code='AP058',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,argument_bound='x<=L*d',initial_cutoff='2*L<=K',degree='K+m+N',
        actual_weights_terms_head_normalization_powers_and_sums_constructed=True,
        positive_original_head_and_binary_power_proved=True,all_term_factorial_normalization_retained=True,
        finite_bounds='s<=t; p*t<=p*s+2*(B*h)',powers='p=2^m; B=L^K',
        uniform_in_extra_finite_horizon=True,zero_argument_bound_and_empty_prefix_allowed=True,
        large_ground_power_materialized=False,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,infinite_tail_or_exponential_claimed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_normalized_witness_source_pins():
    result=exp_normalized_truncation_source_pins()
    expected={'scripts/sqrt2_power_exp_normalized_truncation.py':'e8eb0a5f6c20ff2f4abbd5b2c55261484c40bb75f00e2cb9743fdc27be14d4fd',**{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_normalized_witness.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpNormalizedWitnessError('normalized witness source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def summed(t):
        data=t.hyp('constructed_data')
        bound=apply(specialize(t,'truncation',*t.terms(('d','x','L')+T+('K','m','N','h','s','t','p','B'))),
            t.hyp('nonzero'),t.hyp('argument'),t.hyp('threshold'),field(data,9,11),field(data,3,11),
            t.hyp('prefix'),field(data,8,11),t.hyp('power'),t.hyp('majorant_power'))
        positive=apply(instantiate(apply(specialize(t,'power_nonzero',two),specialize(t,'succ_ne_zero',one)),*t.terms(('m','p'))),t.hyp('power'))
        return witness(t.terms(OUTPUTS),conjunction(*(field(data,i,11) for i in range(11)),
            t.hyp('power'),positive,t.hyp('majorant_power'),t.hyp('prefix'),AndElimL(bound),AndElimR(bound)))
    def powered(t):
        return eliminate(t,specialize(t,'sum_exists',*t.terms(T),Add(t.term('K'),t.term('m'))),('s',),'prefix',summed)
    def constructed(t):
        return eliminate(t,specialize(t,'power_exists',two,t.term('m')),('p',),'power',lambda u:
            eliminate(u,specialize(u,'power_exists',*u.terms(('L','K'))),('B',),'majorant_power',powered))
    def start(t):
        degree=Add(Add(t.term('K'),t.term('m')),t.term('N'))
        return eliminate(t,apply(specialize(t,'constructed',*t.terms(('d','x')),degree),t.hyp('nonzero')),
            CONSTRUCTED_OUTPUTS,'constructed_data',constructed)
    return introduce(s,PARAMETERS,('nonzero','argument','threshold'),start)


def prove_exp_normalized_witness(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP058',target=frozen_exp_normalized_witness_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP058':_root},pins=exp_normalized_witness_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
