"""AP077: symmetric error propagation through actual natural powers.

Split decidable natural order, extract the actual gap, compare it with the
supplied symmetric error and reuse AP076. No positive-base assumption, new
induction or classical real-order principle is needed.
"""
from hashlib import sha256

from sqrt2_power_ordered_power_difference import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,canonical,json_hash,
    definition_registry,ordered_power_difference_source_pins,
    NAMED_SOURCE as ORDERED_SOURCE,COMPARISON_HELPERS,POWER_ARCHIVE,BOUND_ARCHIVE,
)
from sqrt2_power_exp_two_sided_continuity import HELPER_SOURCES as ORDER_HELPERS
from sqrt2_power_quadratic_trace_exists import conjunction
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-symmetric-power-difference-v1'
PARAMETERS=('a','b','M','g','k','u','v','w')
POWER_PREMISES=('Pow(a,S k,u)','Pow(b,S k,v)','Pow(M,k,w)')
PREMISES=('Le(a,M)','Le(b,M)','Le(b,a+g)','Le(a,b+g)')+POWER_PREMISES
CONCLUSION='Le(v,u+(S k)*(g*w)) /\\ Le(u,v+(S k)*(g*w))'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='9f376fc95073195bee675f73105660651b69555fbeb652e7cd0ed1e8550cdc98'
HELPER_SOURCES={'oriented':'forall '+' '.join(PARAMETERS+('h',))+'. '+' -> '.join(('b=a+h','Le(b,M)','Le(b,a+g)')+POWER_PREMISES)+' -> '+CONCLUSION}
HELPER_TARGET_SHA256={'oriented':'1161995341e9a5a9043f648aa2313bd62a9394d96338faf81198b67d10f97edd'}
ORDERED_ARCHIVE=dict(case='AP076',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-ordered-power-difference-v1/generation-process.json.gz',
    bytes=34433,sha256='279fd98f88465c97589a9a58d8eb2bdbd5690cf4118241bb492dabd67e55a3dc',
    raw_bytes=239161,raw_sha256='461696fb3f93ea5250f9aaf88c6ac2920de20b0541f578b96368bbb986a9dfcf',
    bundle_bytes=95110,bundle_sha256='f0ca341bf0363808fabc242631285ec8ced1c63c25f227a557e94235f202c4f7',
    nodes=36,root=35,target_ast_sha256='d4d5beb6c20b976f94c1c1e219e65c4389e0dddce29a5b2f642ed9c3014a7b04')
ORDER_ARCHIVE=dict(case='AP007',path='research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-two-sided-continuity-v1/generation-process.json.gz',
    bytes=44186,sha256='a7054532adf6a26abc55c5abef8c4c7aa7961699d2de5164336b3bba5bd5b0cb',
    raw_bytes=831759,raw_sha256='1126098f18ff1c50d381e6f36451f8daf3883df8144fbeba52a601e5e7a0225e',
    bundle_bytes=483848,bundle_sha256='147d7fa32b4cefb244f3a689bf9241c30b0170bc7eb867723c690751b82423bc',
    nodes=164,root=163,target_ast_sha256='d6c797957cd58e4b92514bcc10063e71045c1cdbe995aeeef3bff5020d434a11')
ARCHIVES=(ORDERED_ARCHIVE,ORDER_ARCHIVE,POWER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={'ordered':ORDERED_SOURCE,'base_monotone':COMPARISON_HELPERS['base_monotone'],
    'le_gap':ORDER_HELPERS['le_gap'],'cancel_order':ORDER_HELPERS['cancel_order'],'allowance':ORDER_HELPERS['allowance'],
    'le_total':'forall a b. Le(a,b) \\/ Le(b,a)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'add_comm':'forall a b. a+b=b+a','le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)'}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(ordered='AP076',base_monotone='AP010',**{name:'AP007' for name in ('le_gap','cancel_order','allowance','le_total')})
HELPER_DEPENDENCIES={'oriented':('ordered','base_monotone','cancel_order','allowance','mul_left_mono','mul_right_mono','add_left_mono','add_comm','le_trans'),
    'AP077':('le_total','le_gap','oriented')}


class SymmetricPowerDifferenceError(ValueError):
    """Changed symmetric gap, bounded bases or actual supplied powers."""


def frozen_symmetric_power_difference_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=8 or len(premises)!=7 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SymmetricPowerDifferenceError('AP077 exact two-sided power-difference target changed')
    return target


def source_contract():
    return dict(code='AP077',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=7,all_three_actual_powers_preserved=True,both_base_bounds_preserved=True,
        symmetric_gap='abs(b-a)<=g',error_bound='(k+1)*g*M^k',input_order_assumed=False,
        actual_ordered_gap_extracted=True,zero_bases_gap_bound_and_k_allowed=True,
        positive_bases_required=False,division_or_denominator_cancellation_used=False,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        analytic_power_or_exponential_claimed=False,fixed_approximation_program_changed=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def symmetric_power_difference_source_pins():
    result=ordered_power_difference_source_pins()
    expected={'scripts/sqrt2_power_ordered_power_difference.py':'9ce10cdf5ff6ec60844b43a0d56024406c4b339ebe222e295061d6b2e477db0e',
        'scripts/sqrt2_power_exp_two_sided_continuity.py':'8fd98e4b6733be1271387cf515dbf88ed4fabd48603a1169bd712b5385291086',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_symmetric_power_difference.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SymmetricPowerDifferenceError('symmetric power-difference source or archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _oriented(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def finish(t):
        a,b,M,g,k,u,v,w,h=t.terms(PARAMETERS+('h',));sk=Succ(k)
        bound=_subst(t,registry,'Le(slot,a+g)',t.hyp('gap'),t.hyp('forward'))
        gap_bound=apply(specialize(t,'cancel_order',a,h,g),bound)
        error=apply(specialize(t,'mul_right_mono',h,g,w),gap_bound)
        error=apply(specialize(t,'mul_left_mono',Mul(h,w),Mul(g,w),sk),error)
        error=apply(specialize(t,'add_left_mono',Mul(sk,Mul(h,w)),Mul(sk,Mul(g,w)),u),error)
        forward=apply(specialize(t,'ordered',a,b,M,h,k,u,v,w),t.hyp('gap'),t.hyp('bound_b'),t.hyp('power_a'),t.hyp('power_b'),t.hyp('power_M'))
        forward=apply(specialize(t,'le_trans',v,Add(u,Mul(sk,Mul(h,w))),Add(u,Mul(sk,Mul(g,w)))),forward,error)
        ordered=witness((h,),_chain(specialize(t,'add_comm',h,a),EqSym(t.hyp('gap'))))
        monotone=apply(instantiate(apply(specialize(t,'base_monotone',a,b),ordered),sk,u,v),t.hyp('power_a'),t.hyp('power_b'))
        backward=apply(specialize(t,'allowance',u,v,Mul(sk,Mul(g,w))),monotone)
        return conjunction(forward,backward)
    return introduce(s,PARAMETERS+('h',),('gap','bound_b','forward','power_a','power_b','power_M'),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,OrElim
    def branch(t,reverse):
        a,b=t.terms(('a','b'));left,right=(b,a) if reverse else (a,b)
        def chosen(u):
            a,b,M,g,k,left_power,right_power,w,h=u.terms(PARAMETERS+('h',))
            if not reverse:
                names=('gap','bound_b','forward','power_a','power_b','power_M')
                return apply(specialize(u,'oriented',*u.terms(PARAMETERS),h),*(u.hyp(name) for name in names))
            result=apply(specialize(u,'oriented',b,a,M,g,k,right_power,left_power,w,h),
                *(u.hyp(name) for name in ('gap','bound_a','backward','power_b','power_a','power_M')))
            return conjunction(AndElimR(result),AndElimL(result))
        return eliminate(t,apply(specialize(t,'le_gap',left,right),t.hyp('ordered')),('h',),'gap',chosen)
    def finish(t):
        return OrElim(specialize(t,'le_total',*t.terms(('a','b'))),branch(t.hypothesis('ordered'),False),branch(t.hypothesis('ordered'),True))
    return introduce(s,PARAMETERS,('bound_a','bound_b','forward','backward','power_a','power_b','power_M'),finish)


def prove_symmetric_power_difference(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP077',target=frozen_symmetric_power_difference_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'oriented':lambda s:_oriented(s,registry),'AP077':lambda s:_root(s,registry)},
        pins=symmetric_power_difference_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
