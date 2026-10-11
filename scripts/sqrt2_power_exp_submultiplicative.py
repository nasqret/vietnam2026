"""AP071: an unrestricted finite exponential sum at x+y is submultiplicative.

All three actual recurrences and sums use the same finite degree, with
independent heads and codes. Construct the finite Cauchy table, restrict its
prefix, prove its added-argument recurrence, and use AP060 to identify its
value. Only the lower side of the finite convolution sandwich is needed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_product_error import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,canonical,json_hash,
    source_registry,exp_product_error_source_pins,SANDWICH_SOURCE,PREFIX_HELPERS,
    SANDWICH_ARCHIVE,PREFIX_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_convolution_prefix import CONVOLUTION_ARCHIVE
from sqrt2_power_exp_recurrence_independence import NAMED_SOURCE as SAME_VALUE_SOURCE,exp_recurrence_independence_source_pins
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-submultiplicative-v1'
PARAMETERS=('d','x','y','N','ab','ac','bb','bc','cb','cc','a0','b0','c0','u','v','w')
PREMISES=('~d=0','NatScaledExpRecurrence(d,x,ab,ac,N)','NatScaledExpRecurrence(d,y,bb,bc,N)',
    'NatScaledExpRecurrence(d,x+y,cb,cc,N)','BetaAt(ab,ac,0,a0)','BetaAt(bb,bc,0,b0)',
    'BetaAt(cb,cc,0,c0)','Sum(ab,ac,S N,u)','Sum(bb,bc,S N,v)','Sum(cb,cc,S N,w)')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> Le((a0*b0)*w,c0*(u*v))'
TARGET_SHA256='172dd2d034e151140ec0f7866fbfea14a1de644c3bc4f01e38d61a48f66c9873'
INDEPENDENCE_ARCHIVE=dict(case='AP060',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-recurrence-independence-v1/generation-process.json.gz',
    bytes=20503,sha256='11527328b71d3e1396fa162123e08b6b35c35a6f1dd24c52e93887123939f457',
    raw_bytes=216008,raw_sha256='c8106c1f53e50d849635c76b238330f6ba1065ec10b9622c87020f451b7bb1b6',
    bundle_bytes=94980,bundle_sha256='87bd710ef99048e7cafb38dc72a681d8ea931d8054616880a6d04f87f4ecc748',
    nodes=37,root=36,target_ast_sha256='7beddbf0b9c56535b34cc9097c02c1dd441a5ba9cb163ee87131584651dfc897')
ARCHIVES=(SANDWICH_ARCHIVE,PREFIX_ARCHIVE,INDEPENDENCE_ARCHIVE,CONVOLUTION_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'sandwich':SANDWICH_SOURCE,'recurrence':PREFIX_HELPERS['recurrence'],
    'head':PREFIX_HELPERS['head'],'same_value':SAME_VALUE_SOURCE,
    'sum_unique':'forall b c N n m. Sum(b,c,N,n) -> Sum(b,c,N,m) -> n=m',
    'le_refl':'forall a. Le(a,a)','le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)'}
ENDPOINT_OWNERS=dict(sandwich='AP041',recurrence='AP039',head='AP039',same_value='AP060',
    sum_unique='CV003',le_refl='CV071',le_trans='CV071',mul_left_mono='CV071')
HELPER_DEPENDENCIES={'AP071':tuple(ENDPOINT_SOURCES)}


class ExpSubmultiplicativeError(ValueError):
    """Changed same finite degree, actual codes or cross-normalized product."""


def definition_registry():
    pool=source_registry();needed=set();pending=['Le','Sum','NatConvolutionPrefix','NatScaledExpRecurrence']
    while pending:
        name=pending.pop()
        if name not in needed:needed.add(name);pending.extend(pool[name].conceptual_dependencies)
    result={name:spec for name,spec in pool.items() if name in needed};seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpSubmultiplicativeError('submultiplicative conservative definition DAG changed')
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_submultiplicative_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=16 or len(premises)!=10 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSubmultiplicativeError('AP071 exact same-degree unrestricted product bound changed')
    return target


def source_contract():
    return dict(code='AP071',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=10,all_three_supplied_recurrences_heads_and_sums_preserved=True,
        all_three_degrees_equal=True,argument_upper_bound_required=False,
        independent_heads_and_codes_allowed=True,cross_normalized_bound='(a0*b0)*w<=c0*(u*v)',
        actual_convolution_constructed_and_value_identified=True,
        no_extra_input_horizon_required=True,zero_arguments_heads_and_horizon_allowed=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        analytic_addition_claimed=False,absolute_majorant_claimed=False,rational_validity_claimed=False,
        fixed_approximation_program_changed=False,original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_submultiplicative_source_pins():
    result=exp_product_error_source_pins()
    for name,pin in exp_recurrence_independence_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpSubmultiplicativeError('submultiplicative dependency source disagreement')
        result[name]=pin
    expected={'scripts/sqrt2_power_exp_product_error.py':'a22255f53ef7749da9a1cc7e25d18db4fe175a4cd73a74f638bdd0cf2d7316e7',
        'scripts/sqrt2_power_exp_recurrence_independence.py':'683487ceef52ea2116f955d71e185356cf15f9d82f7a27daaf9ec5871c4ca149',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_submultiplicative.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSubmultiplicativeError('submultiplicative source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def shortened(t):
        i=t.term('i');length=Succ(t.term('N'));whole=Add(length,length)
        bound=apply(specialize(t,'le_trans',Succ(i),length,whole),t.hyp('inside'),witness((length,),EqRefl(whole)))
        return apply(instantiate(field(t.hyp('sandwich_data'),0,7),i),bound)
    def finish(t):
        d,x,y,N,a,b,c,u,v,w,u0,v0,z=t.terms(('d','x','y','N','a0','b0','c0','u','v','w','u0','v0','z'))
        data=t.hyp('sandwich_data');length=Succ(N)
        prefix=introduce(t,('i',),('inside',),shortened)
        recurrence=apply(specialize(t,'recurrence',d,x,y,*t.terms(('ab','ac','bb','bc')),N,*t.terms(('eb','ec'))),
            t.hyp('recurrence_a'),t.hyp('recurrence_b'),prefix)
        head=apply(specialize(t,'head',*t.terms(('ab','ac','bb','bc')),N,a,b,*t.terms(('eb','ec'))),
            prefix,t.hyp('head_a'),t.hyp('head_b'))
        first=apply(specialize(t,'sum_unique',*t.terms(('ab','ac')),length,u0,u),field(data,1,7),t.hyp('sum_a'))
        second=apply(specialize(t,'sum_unique',*t.terms(('bb','bc')),length,v0,v),field(data,2,7),t.hyp('sum_b'))
        lower=_subst(t,registry,'Le(z,slot)',CongMul(first,second),field(data,5,7))
        lower=apply(specialize(t,'mul_left_mono',z,Mul(u,v),c),lower)
        same=apply(specialize(t,'same_value',d,d,Add(x,y),Add(x,y),N,*t.terms(('cb','cc','eb','ec')),c,Mul(a,b),w,z),
            t.hyp('nonzero'),t.hyp('nonzero'),EqRefl(Mul(Add(x,y),d)),t.hyp('recurrence_c'),recurrence,
            t.hyp('head_c'),head,t.hyp('sum_c'),field(data,3,7))
        return _subst(t,registry,'Le(slot,c0*(u*v))',EqSym(same),lower)
    def start(t):
        length=Succ(t.term('N'))
        return eliminate(t,apply(specialize(t,'sandwich',*t.terms(('ab','ac','bb','bc')),length,length),specialize(t,'le_refl',length)),
            ('eb','ec','u0','v0','z','full'),'sandwich_data',finish)
    return introduce(s,PARAMETERS,('nonzero','recurrence_a','recurrence_b','recurrence_c','head_a','head_b','head_c','sum_a','sum_b','sum_c'),start)


def prove_exp_submultiplicative(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP071',target=frozen_exp_submultiplicative_target(_registry=registry),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'AP071':lambda s:_root(s,registry)},pins=exp_submultiplicative_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
