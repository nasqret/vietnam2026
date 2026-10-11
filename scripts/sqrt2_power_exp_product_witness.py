"""AP067: construct positive factorial-normalized finite product approximations.

All three recurrence tables, positive heads, full sums and input prefixes
come from ordinary arithmetic existence proofs. The product error uses those
same witnesses. No analytic exponential-addition theorem is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_requested_product import (
    ROOT,Scope,introduce,eliminate,field,apply,specialize,conjunction,canonical,json_hash,
    source_registry,exp_requested_product_source_pins,NAMED_SOURCE as PRODUCT_SOURCE,
    COMPARISON_ARCHIVE,D,H,
)
from sqrt2_power_scaled_exp_terms import NAMED_SOURCE as CONSTRUCTED_SOURCE
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE
from sqrt2_power_exp_supplied_large_product import CONVOLUTION_ARCHIVE
from sqrt2_power_quadratic_trace_exists import witness
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-product-witness-v1'
PARAMETERS=('d','x','y','L','K','n')
PREMISES=('~d=0','Le(x+y,L*d)','Le(2*L,K)')
FIRST_OUTPUTS=('aw','az','ab','ac','a0','af','aq','aFull')
SECOND_OUTPUTS=('bw','bz','bb','bc','b0','bf','bq','bFull')
THIRD_OUTPUTS=('cw','cz','cb','cc','c0','cf','cq','w')
OUTPUTS=FIRST_OUTPUTS+SECOND_OUTPUTS+THIRD_OUTPUTS+('u','v','r')


def conjoin(parts):
    result=parts[-1]
    for part in reversed(parts[:-1]):result=f'({part}) /\\ ({result})'
    return result


def constructed_parts(argument,degree,outputs):
    wb,wc,tb,tc,h,f,q,s=outputs
    return (f'NatExpWeightTable(d,{degree},{wb},{wc})',
        f'NatPowerWeightedPrefix({argument},{wb},{wc},{tb},{tc},S({degree}))',
        f'BetaAt({wb},{wc},0,{h})',f'BetaAt({tb},{tc},0,{h})',f'~{h}=0',
        f'Factorial({degree},{f})',f'Pow(d,{degree},{q})',f'{h}={f}*{q}',
        f'Sum({tb},{tc},S({degree}),{s})',f'NatScaledExpRecurrence(d,{argument},{tb},{tc},{degree})',
        f'forall j a fj dj xj. Le(j,{degree}) -> BetaAt({tb},{tc},j,a) -> Factorial(j,fj) -> Pow(d,j,dj) -> Pow({argument},j,xj) -> (a*fj)*dj={h}*xj')


PARTS=constructed_parts('x',H,FIRST_OUTPUTS)+constructed_parts('y',H,SECOND_OUTPUTS)+constructed_parts('x+y',D,THIRD_OUTPUTS)+(
    f'Sum(ab,ac,S({D}),u)',f'Sum(bb,bc,S({D}),v)','Pow(2,n,r)','~r=0',
    'Le((a0*b0)*w,c0*(u*v))','Le(r*(c0*(u*v)),r*((a0*b0)*w)+c0*(a0*b0))')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> exists '+' '.join(OUTPUTS)+'. '+conjoin(PARTS)
TARGET_SHA256='90a7f53271dfd7883b4edc4850e14370009306488126a38310f44e94983de3fd'
PRODUCT_ARCHIVE=dict(case='AP064',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-requested-product-v1/generation-process.json.gz',
    bytes=103847,sha256='4c9a73a1442153550659cbe42384f066bbb65ba90bd5efc11e421f7b05172300',
    raw_bytes=1993918,raw_sha256='785a1e5c2baa36122e4e17a254703f02aeac96ec6263328b042717e33dde1165',
    bundle_bytes=1163417,bundle_sha256='cd072e20381973dfe744997e4f8b40cfb61735f27a0be2bd40f78caa95769495',
    nodes=266,root=265,target_ast_sha256='f0434acec36b8372e936d5c8e5f08cb7bacbc68bca03a222d3af6dfa45e2d636')
ARCHIVES=(PRODUCT_ARCHIVE,EXP_ARCHIVE,COMPARISON_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES={'product':PRODUCT_SOURCE,'constructed':CONSTRUCTED_SOURCE,
    'power_exists':'forall d n. exists p. Pow(d,n,p)',
    'sum_exists':'forall b c N. exists n. Sum(b,c,N,n)'}
ENDPOINT_OWNERS=dict(product='AP064',constructed='CV070',power_exists='AP010',sum_exists='CV003')
HELPER_DEPENDENCIES={'AP067':tuple(ENDPOINT_SOURCES)}


class ExpProductWitnessError(ValueError):
    """Changed positive tables, product inputs or requested finite accuracy."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','NatExpWeightTable','NatPowerWeightedPrefix','Factorial','Pow','Sum','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpProductWitnessError('product witness conservative definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_product_witness_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=3 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpProductWitnessError('AP067 exact positive three-table product witness changed')
    return target


def source_contract():
    return dict(code='AP067',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=3,all_three_actual_tables_heads_factorizations_and_full_sums_constructed=True,
        both_actual_input_prefixes_constructed=True,three_heads_and_precision_power_proved_nonzero=True,
        all_three_indexwise_factorial_normalizations_retained=True,
        argument_bound='x+y<=L*d',initial_cutoff='2*L<=K',degree='D=K+(L*K+n)',input_degree='2*D+1',output_degree='D',
        requested_scale='r=2^n',lower='(a0*b0)*w<=c0*(u*v)',upper='r*(c0*(u*v))<=r*((a0*b0)*w)+c0*(a0*b0)',
        zero_arguments_and_precision_allowed=True,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_exponential_addition=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_product_witness_source_pins():
    result=exp_requested_product_source_pins()
    expected={'scripts/sqrt2_power_exp_requested_product.py':'ce9c81902f4511f83b78c2e9515bd4b0f0e75aaf5d7702144f1a7d37c06f781a',
        'scripts/sqrt2_power_scaled_exp_terms.py':'329c4e741b144823db7d43c018756dd19033aa5beca1505b5f4d05ae7cbe316a',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_product_witness.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpProductWitnessError('product witness source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def degree(u):return Add(u.term('K'),Add(Mul(u.term('L'),u.term('K')),u.term('n')))
    def finish(u):
        first,second,third=(u.hyp(name) for name in ('first_data','second_data','third_data'))
        bound=apply(specialize(u,'product',*u.terms(('d','x','y','L','ab','ac','bb','bc','cb','cc','K','n','a0','b0','c0','u','v','w','r'))),
            u.hyp('nonzero'),u.hyp('argument'),u.hyp('threshold'),
            field(first,9,11),field(second,9,11),field(third,9,11),
            field(first,3,11),field(second,3,11),field(third,3,11),
            u.hyp('first_prefix'),u.hyp('second_prefix'),field(third,8,11),u.hyp('precision_power'))
        return witness(u.terms(OUTPUTS),conjunction(*(field(data,i,11) for data in (first,second,third) for i in range(11)),
            u.hyp('first_prefix'),u.hyp('second_prefix'),u.hyp('precision_power'),*(field(bound,i,3) for i in range(3))))
    def third(u):
        return eliminate(u,specialize(u,'sum_exists',*u.terms(('ab','ac')),Succ(degree(u))),('u',),'first_prefix',lambda v:
            eliminate(v,specialize(v,'sum_exists',*v.terms(('bb','bc')),Succ(degree(v))),('v',),'second_prefix',lambda w:
                eliminate(w,specialize(w,'power_exists',Succ(Succ(Zero())),w.term('n')),('r',),'precision_power',finish)))
    def second(u):
        return eliminate(u,apply(specialize(u,'constructed',u.term('d'),Add(u.term('x'),u.term('y')),degree(u)),u.hyp('nonzero')),
            THIRD_OUTPUTS,'third_data',third)
    def first(u):
        D=degree(u)
        return eliminate(u,apply(specialize(u,'constructed',*u.terms(('d','y')),Add(Succ(D),D)),u.hyp('nonzero')),
            SECOND_OUTPUTS,'second_data',second)
    def start(u):
        D=degree(u)
        return eliminate(u,apply(specialize(u,'constructed',*u.terms(('d','x')),Add(Succ(D),D)),u.hyp('nonzero')),
            FIRST_OUTPUTS,'first_data',first)
    return introduce(s,PARAMETERS,('nonzero','argument','threshold'),start)


def prove_exp_product_witness(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP067',target=frozen_exp_product_witness_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP067':_root},pins=exp_product_witness_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
