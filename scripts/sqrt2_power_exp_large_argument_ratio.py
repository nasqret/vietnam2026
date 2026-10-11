"""AP051: exponential recurrence terms halve beyond twice an argument bound.

For x/d<=L, every recurrence step with j+1>=2*L satisfies 2*b<=a.
Cancel the positive full recurrence coefficient, not x or L: zero arguments
and L=0 remain covered. This finite arithmetic lemma assumes no analytic law.
"""
from hashlib import sha256

from sqrt2_power_half_log_root_comparison import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,definition_registry,
    half_log_root_comparison_source_pins,BOUND_ARCHIVE,
)
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-exp-large-argument-ratio-v1'
PARAMETERS=('d','x','L','j','a','b')
PREMISES=('~d=0','Le(x,L*d)','Le(2*L,S j)','((S j)*d)*b=x*a')
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> Le(2*b,a)'
TARGET_SHA256='0ed9c296638e7d978dbfb8e18e70dba5fbd546cda5f0e856d746cddb49f5ba40'
HELPER_SOURCES={'ratio':'forall c x a b. ~c=0 -> Le(2*x,c) -> c*b=x*a -> Le(2*b,a)'}
HELPER_TARGET_SHA256={'ratio':'d02d9f2b4539c157a371967bed40ca55e751c1697fb91a0e3015f936b8e4cfad'}
ARCHIVES=(BOUND_ARCHIVE,)
ENDPOINT_SOURCES={
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'mul_right_mono':'forall a b c. Le(a,b) -> Le(a*c,b*c)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a',
    'succ_ne_zero':'forall a. ~S a=0',
    'mul_ne_zero':'forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES={
    'ratio':('mul_right_mono','mul_le_cancel','mul_assoc','mul_comm'),
    'AP051':('ratio','mul_left_mono','mul_right_mono','le_trans','mul_assoc','succ_ne_zero','mul_ne_zero'),
}


class ExpLargeArgumentRatioError(ValueError):
    """Changed recurrence, argument threshold, positivity or exact target."""


def frozen_exp_large_argument_ratio_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpLargeArgumentRatioError('AP051 exact large-argument halving threshold changed')
    return target


def source_contract():
    return dict(code='AP051',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,argument_bound='x<=L*d',threshold='2*L<=j+1',ratio='2*b<=a',
        supplied_exact_recurrence_required=True,positive_denominator_required=True,
        cancelled_coefficient='(j+1)*d',zero_x_L_a_b_allowed=True,
        sum_or_tail_constructed=False,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_limit_claim=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_large_argument_ratio_source_pins():
    result=half_log_root_comparison_source_pins()
    expected={'scripts/sqrt2_power_half_log_root_comparison.py':'b478179b274b9f2d86f1a78c59782c36d3ed185b7194504a3e7c275205584476',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_exp_large_argument_ratio.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpLargeArgumentRatioError('large-argument ratio source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _ratio(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,parse_term
    two=parse_term('2')
    def finish(t):
        c,x,a,b=t.terms(('c','x','a','b'));left=Mul(c,Mul(two,b));right=Mul(c,a)
        equality=_chain(_multiplicative_equal(t,left,Mul(two,Mul(c,b))),
            CongMul(EqRefl(two),t.hyp('recurrence')),EqSym(specialize(t,'mul_assoc',two,x,a)))
        bound=apply(specialize(t,'mul_right_mono',Mul(two,x),c,a),t.hyp('threshold'))
        bound=_left(t,registry,bound,right,EqSym(equality))
        return apply(specialize(t,'mul_le_cancel',c,Mul(two,b),a),t.hyp('nonzero'),bound)
    return introduce(s,('c','x','a','b'),('nonzero','threshold','recurrence'),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Mul,Succ,parse_term
    two=parse_term('2')
    def finish(t):
        d,x,L,j,a,b=t.terms(PARAMETERS);sj=Succ(j);c=Mul(sj,d)
        first=apply(specialize(t,'mul_left_mono',x,Mul(L,d),two),t.hyp('argument'))
        first=_right(t,registry,first,Mul(two,x),EqSym(specialize(t,'mul_assoc',two,L,d)))
        second=apply(specialize(t,'mul_right_mono',Mul(two,L),sj,d),t.hyp('index'))
        threshold=apply(specialize(t,'le_trans',Mul(two,x),Mul(Mul(two,L),d),c),first,second)
        nz=apply(specialize(t,'mul_ne_zero',sj,d),specialize(t,'succ_ne_zero',j),t.hyp('nonzero'))
        return apply(specialize(t,'ratio',c,x,a,b),nz,threshold,t.hyp('recurrence'))
    return introduce(s,PARAMETERS,('nonzero','argument','index','recurrence'),finish)


def prove_exp_large_argument_ratio(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP051',target=frozen_exp_large_argument_ratio_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'ratio':lambda s:_ratio(s,registry),'AP051':lambda s:_root(s,registry)},
        pins=exp_large_argument_ratio_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
