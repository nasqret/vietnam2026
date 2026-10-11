"""AP066: one positive finite exponential approximation for all later horizons.

Construct the coarse factorial-weighted table and precision power before
introducing the arbitrary extra horizon. Each later table is independently
constructed by CV070. AP065 compares those actual sums, without identifying
their codes or postulating a real exponential or a limit.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_independent_horizon import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,conjunction,canonical,json_hash,
    source_registry,exp_independent_horizon_source_pins,NAMED_SOURCE as HORIZON_SOURCE,
    BOUND_ARCHIVE,D,H,
)
from sqrt2_power_scaled_exp_terms import NAMED_SOURCE as CONSTRUCTED_SOURCE
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE
from sqrt2_power_exp_geometric_majorant import COMPARISON_ARCHIVE
from sqrt2_power_quadratic_trace_exists import witness
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-uniform-witness-v1'
PARAMETERS=('d','x','L','K','n')
PREMISES=('~d=0','Le(x,L*d)','Le(2*L,K)')
COARSE_OUTPUTS=('wb','wc','ab','ac','h','f','q','s')
OUTPUTS=COARSE_OUTPUTS+('r',)
FINE_OUTPUTS=('vb','vc','bb','bc','g','F','Q','t')


def conjoin(parts):
    result=parts[-1]
    for part in reversed(parts[:-1]):result=f'({part}) /\\ ({result})'
    return result


def constructed_parts(degree,outputs):
    wb,wc,tb,tc,h,f,q,s=outputs
    return (f'NatExpWeightTable(d,{degree},{wb},{wc})',
        f'NatPowerWeightedPrefix(x,{wb},{wc},{tb},{tc},S({degree}))',
        f'BetaAt({wb},{wc},0,{h})',f'BetaAt({tb},{tc},0,{h})',f'~{h}=0',
        f'Factorial({degree},{f})',f'Pow(d,{degree},{q})',f'{h}={f}*{q}',
        f'Sum({tb},{tc},S({degree}),{s})',f'NatScaledExpRecurrence(d,x,{tb},{tc},{degree})',
        f'forall j v fj dj xj. Le(j,{degree}) -> BetaAt({tb},{tc},j,v) -> Factorial(j,fj) -> Pow(d,j,dj) -> Pow(x,j,xj) -> (v*fj)*dj={h}*xj')


COARSE_PARTS=constructed_parts(D,COARSE_OUTPUTS)
FINE_PARTS=constructed_parts(H,FINE_OUTPUTS)+('Le(g*s,h*t)','Le(r*(h*t),r*(g*s)+h*g)')
LATER_SOURCE='forall N. exists '+' '.join(FINE_OUTPUTS)+'. '+conjoin(FINE_PARTS)
PARTS=COARSE_PARTS+('Pow(2,n,r)','~r=0',LATER_SOURCE)
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='1271edf53171c0ca044ba475b8805112ebf82d4ac21ba32f38e69819c32da8c8'
HORIZON_ARCHIVE=dict(case='AP065',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-independent-horizon-v1/generation-process.json.gz',
    bytes=76172,sha256='4f27ea62f443082d3cd6dc5648d74b146a08da45b380bd48da43c21fca06c248',
    raw_bytes=1052393,raw_sha256='444daa60653748433c750b20459d60dc31bb2742c59777e7cb656c383a83ace1',
    bundle_bytes=576250,bundle_sha256='2ad83c07ef353332351dba47fd70922980c533807a82e0ab7c479479d09f1e80',
    nodes=179,root=178,target_ast_sha256='650e729c29cf242dce7af6b0b54b08b896036d8256a6ec458c80134305b3ee39')
ARCHIVES=(HORIZON_ARCHIVE,EXP_ARCHIVE,COMPARISON_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'horizon':HORIZON_SOURCE,'constructed':CONSTRUCTED_SOURCE,
    'power_exists':'forall d n. exists p. Pow(d,n,p)',
    'power_nonzero':'forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0',
    'succ_ne_zero':'forall a. ~S a=0'}
ENDPOINT_OWNERS=dict(horizon='AP065',constructed='CV070',power_exists='AP010',power_nonzero='AP010',succ_ne_zero='CV071')
HELPER_DEPENDENCIES={'AP066':tuple(ENDPOINT_SOURCES)}


class ExpUniformWitnessError(ValueError):
    """Changed quantifier order, positive normalization or finite error."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatExpWeightTable','NatPowerWeightedPrefix','Factorial','Pow','Sum','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpUniformWitnessError('uniform witness conservative definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_uniform_witness_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=5 or len(premises)!=3 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpUniformWitnessError('AP066 exact coarse-before-horizon witness changed')
    return target


def source_contract():
    return dict(code='AP066',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,coarse_witness_and_precision_chosen_before_arbitrary_horizon=True,
        actual_weights_terms_heads_factorizations_and_sums_constructed=True,
        both_heads_and_precision_power_proved_nonzero=True,all_index_factorial_normalizations_retained=True,
        argument_bound='x<=L*d',initial_cutoff='2*L<=K',coarse_degree='D=K+(L*K+n)',fine_degree='(D+1)+N',
        requested_scale='r=2^n',cross_normalized_bounds='g*s<=h*t; r*(h*t)<=r*(g*s)+h*g',
        uniform_in_extra_finite_horizon=True,zero_argument_precision_and_extra_horizon_allowed=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        code_number_equality_claimed=False,analytic_limit_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_uniform_witness_source_pins():
    result=exp_independent_horizon_source_pins()
    expected={'scripts/sqrt2_power_exp_independent_horizon.py':'f4fbdc322b965dfe9609a98f8f6e75be3a7901be4043f8dfe3b1913a8b2b0e91',
        'scripts/sqrt2_power_scaled_exp_terms.py':'329c4e741b144823db7d43c018756dd19033aa5beca1505b5f4d05ae7cbe316a',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_uniform_witness.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpUniformWitnessError('uniform witness source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish_fine(u):
        d,x=u.terms(('d','x'));coarse=u.hyp('coarse_data');fine=u.hyp('fine_data')
        bound=apply(specialize(u,'horizon',d,d,x,x,*u.terms(('L','K','n','N','ab','ac','bb','bc','h','g','s','t','r'))),
            u.hyp('nonzero'),u.hyp('nonzero'),EqRefl(Mul(x,d)),u.hyp('argument'),u.hyp('threshold'),
            field(coarse,9,11),field(fine,9,11),field(coarse,3,11),field(fine,3,11),
            field(coarse,8,11),field(fine,8,11),u.hyp('precision_power'))
        return witness(u.terms(FINE_OUTPUTS),conjunction(*(field(fine,i,11) for i in range(11)),field(bound,1,3),field(bound,2,3)))
    def later(u):
        D=Add(u.term('K'),Add(Mul(u.term('L'),u.term('K')),u.term('n')))
        return eliminate(u,apply(specialize(u,'constructed',*u.terms(('d','x')),Add(Succ(D),u.term('N'))),u.hyp('nonzero')),
            FINE_OUTPUTS,'fine_data',finish_fine)
    def powered(u):
        data=u.hyp('coarse_data')
        positive=apply(instantiate(apply(specialize(u,'power_nonzero',two),specialize(u,'succ_ne_zero',one)),*u.terms(('n','r'))),u.hyp('precision_power'))
        universal=introduce(u,('N',),(),later)
        return witness(u.terms(OUTPUTS),conjunction(*(field(data,i,11) for i in range(11)),u.hyp('precision_power'),positive,universal))
    def coarse(u):
        return eliminate(u,specialize(u,'power_exists',two,u.term('n')),('r',),'precision_power',powered)
    def start(u):
        D=Add(u.term('K'),Add(Mul(u.term('L'),u.term('K')),u.term('n')))
        return eliminate(u,apply(specialize(u,'constructed',*u.terms(('d','x')),D),u.hyp('nonzero')),COARSE_OUTPUTS,'coarse_data',coarse)
    return introduce(s,PARAMETERS,('nonzero','argument','threshold'),start)


def prove_exp_uniform_witness(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP066',target=frozen_exp_uniform_witness_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP066':_root},pins=exp_uniform_witness_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
