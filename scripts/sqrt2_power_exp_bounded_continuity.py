"""AP074: two-sided absolute continuity of actual bounded finite sums.

Construct the majorant via AP073. Split the decidable order of the two
natural cross-products, extract the actual ordered gap, bound it by the
supplied error and apply AP070. Neither order is assumed in the theorem.
This is a finite computation theorem, not an analytic limit assertion.
"""
from hashlib import sha256

from sqrt2_power_exp_bounded_majorant import (
    ROOT,Scope,introduce,eliminate,apply,specialize,canonical,json_hash,
    source_registry,definition_registry,exp_bounded_majorant_source_pins,
    NAMED_SOURCE as MAJORANT_SOURCE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_absolute_continuity import (
    NAMED_SOURCE as ABSOLUTE_SOURCE,exp_absolute_continuity_source_pins,
)
from sqrt2_power_exp_two_sided_continuity import (
    HELPER_SOURCES as ORDER_HELPERS,exp_two_sided_continuity_source_pins,
)
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-bounded-continuity-v1'
PARAMETERS=('L','d','e','x','y','g','N','ab','ac','bb','bc','a0','b0','s','t','C','r')
DATA_PREMISES=('NatScaledExpRecurrence(d,x,ab,ac,N)','NatScaledExpRecurrence(e,y,bb,bc,N)',
    'BetaAt(ab,ac,0,a0)','BetaAt(bb,bc,0,b0)','Sum(ab,ac,S N,s)','Sum(bb,bc,S N,t)')
DATA_HYPS=('recurrence_a','recurrence_b','head_a','head_b','sum_a','sum_b')
PREMISES=('~d=0','~e=0','Le(x,L*d)','Le(y,L*e)','Le(d*y,e*x+g)','Le(e*x,d*y+g)')+DATA_PREMISES+('Pow(9,S L,C)','Le((r*g)*C,d*e)')
CONCLUSION='Le(r*(b0*s),r*(a0*t)+a0*b0) /\\ Le(r*(a0*t),r*(b0*s)+a0*b0)'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='33db4b325e45a75d8927db006e7cc1ae244b680af38c9eda0005ba8149899723'
ORDERED_PARAMETERS=PARAMETERS+('k',)
ORDERED_PREMISES=('~d=0','~e=0','Le(y,L*e)','d*y=e*x+k','Le(d*y,e*x+g)')+DATA_PREMISES+('Pow(9,S L,C)','Le((r*g)*C,d*e)')
HELPER_SOURCES={'oriented':'forall '+' '.join(ORDERED_PARAMETERS)+'. '+' -> '.join(ORDERED_PREMISES)+' -> '+CONCLUSION}
HELPER_TARGET_SHA256={'oriented':'e194097410503023e7bd1d60f5277f34c288a5d2f4b6add232a4ae3b28a10fb5'}
MAJORANT_ARCHIVE=dict(case='AP073',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-bounded-majorant-v1/generation-process.json.gz',
    bytes=104302,sha256='ace1882bf3b33a572ff452494e5c83cb4900167871ac37f7aa6c0f860c1bdc57',
    raw_bytes=2096657,raw_sha256='711b2a03c2ab75ed0f301d354b8e74349d43d6d6ba9509b5a3af9aa1910edf61',
    bundle_bytes=1238445,bundle_sha256='9b94bb19dbf67b5b77d0f8e7315675f73673189d0c87d1989f2e93ee18c07d2f',
    nodes=281,root=280,target_ast_sha256='b50deb3120bcff57e9f7bb87d27d0227041c2cae062f4de207339d31f41a23ff')
ABSOLUTE_ARCHIVE=dict(case='AP070',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-absolute-continuity-v1/generation-process.json.gz',
    bytes=39749,sha256='5212d35f76db08dd1e3b5f101c380aae819a0fc9366aff55ce079f5b9b8ebb70',
    raw_bytes=697495,raw_sha256='531060217e21f7f9fd851602dc1f622fef7448b9b29b6aba4f8b8b8e8cfbdbe1',
    bundle_bytes=398512,bundle_sha256='1804aac88411201a7aba240f21ec51eb677f7c532748c43fd7c5ae9bd547a9a8',
    nodes=146,root=145,target_ast_sha256='a085e6805bd448394a0ee2f1cd547da010b34b51bebbfe4b683fe338d87aeba9')
ORDER_ARCHIVE=dict(case='AP007',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-two-sided-continuity-v1/generation-process.json.gz',
    bytes=44186,sha256='a7054532adf6a26abc55c5abef8c4c7aa7961699d2de5164336b3bba5bd5b0cb',
    raw_bytes=831759,raw_sha256='1126098f18ff1c50d381e6f36451f8daf3883df8144fbeba52a601e5e7a0225e',
    bundle_bytes=483848,bundle_sha256='147d7fa32b4cefb244f3a689bf9241c30b0170bc7eb867723c690751b82423bc',
    nodes=164,root=163,target_ast_sha256='d6c797957cd58e4b92514bcc10063e71045c1cdbe995aeeef3bff5020d434a11')
ARCHIVES=(MAJORANT_ARCHIVE,ABSOLUTE_ARCHIVE,ORDER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'majorant':MAJORANT_SOURCE,'absolute':ABSOLUTE_SOURCE,
    'le_gap':ORDER_HELPERS['le_gap'],'cancel_order':ORDER_HELPERS['cancel_order'],'allowance':ORDER_HELPERS['allowance'],
    'le_total':'forall a b. Le(a,b) \\/ Le(b,a)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'mul_comm':'forall a b. a*b=b*a','le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(majorant='AP073',absolute='AP070',**{name:'AP007' for name in ('le_gap','cancel_order','allowance','le_total')})
HELPER_DEPENDENCIES={'oriented':('majorant','absolute','cancel_order','allowance','mul_left_mono','mul_right_mono','le_trans'),
    'AP074':('le_total','le_gap','oriented','mul_comm')}


class ExpBoundedContinuityError(ValueError):
    """Changed actual bounded computations, symmetric argument error or budget."""


def frozen_exp_bounded_continuity_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=17 or len(premises)!=14 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpBoundedContinuityError('AP074 exact symmetric bounded finite continuity changed')
    return target


def source_contract():
    return dict(code='AP074',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=14,both_actual_recurrences_heads_sums_preserved=True,
        independent_denominators_heads_and_codes_allowed=True,
        argument_bounds=['x<=L*d','y<=L*e'],symmetric_cross_product_error='abs(d*y-e*x)<=g',
        argument_order_assumed=False,actual_ordered_gap_extracted=True,majorant_proved_via_AP073=True,
        supplied_power='C=9^(L+1)',symbolic_precision_budget='(r*g)*C<=d*e',
        conclusion='abs(r*(a0*t)-r*(b0*s))<=a0*b0',
        zero_arguments_gap_heads_horizon_and_precision_allowed=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        analytic_continuity_claimed=False,precision_power_constructed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_bounded_continuity_source_pins():
    result=exp_bounded_majorant_source_pins()
    for source in (exp_absolute_continuity_source_pins,exp_two_sided_continuity_source_pins):
        for name,pin in source().items():
            if name in result and result[name]!=pin:raise ExpBoundedContinuityError('bounded-continuity dependency source disagreement')
            result[name]=pin
    expected={'scripts/sqrt2_power_exp_bounded_majorant.py':'54faa97c1cc9af3488702da1af17a8006ec9cccd5d596b06e4b483b060c2e8d1',
        'scripts/sqrt2_power_exp_absolute_continuity.py':'330ccaf5cc490eb2c657ee548a246bcc7ef6b5b97a5a263224572902d5ad8014',
        'scripts/sqrt2_power_exp_two_sided_continuity.py':'8fd98e4b6733be1271387cf515dbf88ed4fabd48603a1169bd712b5385291086',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_bounded_continuity.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpBoundedContinuityError('bounded-continuity source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _oriented(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul
    def finish(t):
        L,d,e,x,y,g,N,a,b,u,v,C,r,k=t.terms(('L','d','e','x','y','g','N','a0','b0','s','t','C','r','k'))
        ordered=_subst(t,registry,'Le(slot,e*x+g)',t.hyp('gap'),t.hyp('forward'))
        gap_bound=apply(specialize(t,'cancel_order',Mul(e,x),k,g),ordered)
        budget=apply(specialize(t,'mul_left_mono',k,g,r),gap_bound)
        budget=apply(specialize(t,'mul_right_mono',Mul(r,k),Mul(r,g),C),budget)
        budget=apply(specialize(t,'le_trans',Mul(Mul(r,k),C),Mul(Mul(r,g),C),Mul(d,e)),budget,t.hyp('budget'))
        majorant=apply(specialize(t,'majorant',L,e,y,N,*t.terms(('bb','bc')),b,v,C),
            t.hyp('nonzero_e'),t.hyp('bound_b'),t.hyp('recurrence_b'),t.hyp('head_b'),t.hyp('sum_b'),t.hyp('power'))
        estimate=apply(specialize(t,'absolute',d,e,x,y,k,N,*t.terms(('ab','ac','bb','bc')),a,b,u,v,C,r),
            t.hyp('nonzero_d'),t.hyp('nonzero_e'),t.hyp('gap'),*(t.hyp(name) for name in DATA_HYPS),majorant,budget)
        monotone=apply(specialize(t,'mul_left_mono',Mul(b,u),Mul(a,v),r),AndElimL(estimate))
        monotone=apply(specialize(t,'allowance',Mul(r,Mul(b,u)),Mul(r,Mul(a,v)),Mul(a,b)),monotone)
        return conjunction(monotone,AndElimR(estimate))
    return introduce(s,ORDERED_PARAMETERS,('nonzero_d','nonzero_e','bound_b','gap','forward')+DATA_HYPS+('power','budget'),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,OrElim
    from peano_lab.kernel.terms import Mul
    def branch(t,reverse):
        d,e,x,y=t.terms(('d','e','x','y'))
        left,right=(Mul(d,y),Mul(e,x)) if reverse else (Mul(e,x),Mul(d,y))
        def chosen(u):
            L,d,e,x,y,g,N,ab,ac,bb,bc,a,b,out,v,C,r=u.terms(PARAMETERS)
            if not reverse:
                names=('nonzero_d','nonzero_e','bound_b','gap','forward')+DATA_HYPS+('power','budget')
                return apply(specialize(u,'oriented',*u.terms(PARAMETERS),u.term('k')),*(u.hyp(name) for name in names))
            budget=_subst(u,registry,'Le((r*g)*C,slot)',specialize(u,'mul_comm',d,e),u.hyp('budget'))
            params=(L,e,d,y,x,g,N,bb,bc,ab,ac,b,a,v,out,C,r,u.term('k'))
            names=('nonzero_e','nonzero_d','bound_a','gap','backward','recurrence_b','recurrence_a','head_b','head_a','sum_b','sum_a','power')
            result=apply(specialize(u,'oriented',*params),*(u.hyp(name) for name in names),budget)
            result=conjunction(AndElimR(result),AndElimL(result))
            return _subst(u,registry,'Le(r*(b0*s),r*(a0*t)+slot) /\\ Le(r*(a0*t),r*(b0*s)+slot)',specialize(u,'mul_comm',b,a),result)
        return eliminate(t,apply(specialize(t,'le_gap',left,right),t.hyp('ordered')),('k',),'gap',chosen)
    def finish(t):
        d,e,x,y=t.terms(('d','e','x','y'))
        return OrElim(specialize(t,'le_total',Mul(e,x),Mul(d,y)),branch(t.hypothesis('ordered'),False),branch(t.hypothesis('ordered'),True))
    return introduce(s,PARAMETERS,('nonzero_d','nonzero_e','bound_a','bound_b','forward','backward')+DATA_HYPS+('power','budget'),finish)


def prove_exp_bounded_continuity(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP074',target=frozen_exp_bounded_continuity_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'oriented':lambda s:_oriented(s,registry),'AP074':lambda s:_root(s,registry)},
        pins=exp_bounded_continuity_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
