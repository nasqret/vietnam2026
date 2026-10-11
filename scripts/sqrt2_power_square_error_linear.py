"""AP048: convert finite natural square errors into two linear errors.

The positive comparison scale is bounded by x+y. Decidable natural order
provides an additive gap, difference of squares bounds that gap, and only
the proved positive scale is cancelled. No real square-root axiom is used.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_half_log_square import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as source_registry,half_log_square_source_pins,
)
from sqrt2_power_exp_two_sided_continuity import HELPER_SOURCES as ORDER_HELPERS,_left,_right
from sqrt2_power_exp_two_sided_horizons import CONTINUITY_ARCHIVE
from sqrt2_power_scaled_exp_tail import BOUND_ARCHIVE
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-square-error-linear-v1'
PARAMETERS=('r','x','y','k','a','b')
PREMISES=('~k=0','Le(k,x+y)','Le(r*(x*x),r*(y*y)+a*(k*k))','Le(r*(y*y),r*(x*x)+b*(k*k))')
CONCLUSION='Le(r*x,r*y+a*k) /\\ Le(r*y,r*x+b*k)'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='f1e75bcb47244d65e8f878a65bf2a5d7d7328ac4d6b03d2211b360a44946610c'
HELPER_SOURCES={
    'gap_square':'forall x y g. x=y+g -> x*x=y*y+g*(x+y)',
    'oriented':'forall r x y k e g. ~k=0 -> Le(k,x+y) -> x=y+g -> Le(r*(x*x),r*(y*y)+e*(k*k)) -> Le(r*x,r*y+e*k)',
    'one_sided':'forall r x y k e. ~k=0 -> Le(k,x+y) -> Le(r*(x*x),r*(y*y)+e*(k*k)) -> Le(r*x,r*y+e*k)',
}
HELPER_TARGET_SHA256={
    'gap_square':'541b5036500ac0cdb1f9e61abf5abd5498a76afbf9dc1b17fd52ffc5ef818f10',
    'oriented':'671f1b48472332738626f963786a0a3a5d70faccde849d1c411ff2205c878db4',
    'one_sided':'c60a8c74d0cb8b2fc82bafce5e3d4b1cbba2f2cd389d5b8675bc7a80891eb398',
}
ARCHIVES=(CONTINUITY_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    'le_gap':ORDER_HELPERS['le_gap'],'cancel_order':ORDER_HELPERS['cancel_order'],'allowance':ORDER_HELPERS['allowance'],
    'le_total':'forall a b. Le(a,b) \\/ Le(b,a)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_add':'forall a b c. a*(b+c)=a*b+a*c',
    'add_mul':'forall a b c. (a+b)*c=a*c+b*c',
    'add_assoc':'forall a b c. (a+b)+c=a+(b+c)','add_comm':'forall a b. a+b=b+a',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update({name:'AP007' for name in ('le_gap','cancel_order','allowance','le_total')})
HELPER_DEPENDENCIES={
    'gap_square':('mul_add','add_mul','add_assoc','add_comm','mul_comm'),
    'oriented':('gap_square','cancel_order','mul_left_mono','add_left_mono','le_trans','mul_le_cancel','mul_comm','mul_assoc','mul_add'),
    'one_sided':('le_total','le_gap','oriented','mul_left_mono','allowance'),
    'AP048':('one_sided','add_comm'),
}


class SquareErrorLinearError(ValueError):
    """Changed supplied square error, positive scale or exact target."""


def definition_registry():
    spec=source_registry()['Le']
    if spec.conceptual_dependencies:
        raise SquareErrorLinearError('existing natural order gained a dependency')
    return MappingProxyType({'Le':spec})


def frozen_square_error_linear_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=4 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SquareErrorLinearError('AP048 exact finite square-to-linear error changed')
    return target


def source_contract():
    return dict(code='AP048',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,positive_cancellation_factor='k',scale_lower_bound='k<=x+y',
        both_supplied_square_errors_preserved=True,allows_zero_r_x_y_a_b=True,
        natural_decidable_order_and_actual_additive_gap=True,
        new_induction_needed=False,new_induction_count=0,new_definition_ids=[],definition_admissions=0,
        square_root_construction=False,analytic_identity_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority='source_contract_not_proof_authority',
        closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def square_error_linear_source_pins():
    result=half_log_square_source_pins()
    expected={'scripts/sqrt2_power_half_log_square.py':'4a65a86196f134092448c7a8601da69d9ff499e22571f7015a3d49975d7bb5b6',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_square_error_linear.py'):
        with (ROOT/name).open('rb') as stream:raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SquareErrorLinearError('square-error arithmetic source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _gap_square(s):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        x,y,g=t.terms(('x','y','g'));yy,yg,gx=Mul(y,y),Mul(y,g),Mul(g,x)
        return _chain(CongMul(t.hyp('gap'),EqRefl(x)),specialize(t,'add_mul',y,g,x),
            CongAdd(CongMul(EqRefl(y),t.hyp('gap')),EqRefl(gx)),
            CongAdd(specialize(t,'mul_add',y,y,g),EqRefl(gx)),specialize(t,'add_assoc',yy,yg,gx),
            CongAdd(EqRefl(yy),_chain(CongAdd(specialize(t,'mul_comm',y,g),EqRefl(gx)),
                specialize(t,'add_comm',Mul(g,y),gx),EqSym(specialize(t,'mul_add',g,x,y)))))
    return introduce(s,('x','y','g'),('gap',),finish)


def _oriented(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        r,x,y,k,e,g=t.terms(('r','x','y','k','e','g'))
        xx,yy,xy=Mul(x,x),Mul(y,y),Add(x,y)
        base=Mul(r,yy);gap=Mul(r,Mul(g,xy));error=Mul(e,Mul(k,k));rg=Mul(r,g)
        square=apply(specialize(t,'gap_square',x,y,g),t.hyp('gap'))
        expansion=_chain(CongMul(EqRefl(r),square),specialize(t,'mul_add',r,yy,Mul(g,xy)))
        bound=_left(t,registry,t.hyp('square'),Add(base,error),expansion)
        bound=apply(specialize(t,'cancel_order',base,gap,error),bound)
        lower=apply(specialize(t,'mul_left_mono',k,xy,rg),t.hyp('scale'))
        lower=_right(t,registry,lower,Mul(rg,k),specialize(t,'mul_assoc',r,g,xy))
        joined=apply(specialize(t,'le_trans',Mul(rg,k),gap,error),lower,bound)
        joined=_left(t,registry,joined,error,specialize(t,'mul_comm',rg,k))
        joined=_right(t,registry,joined,Mul(k,rg),_multiplicative_equal(t,error,Mul(k,Mul(e,k))))
        gap_bound=apply(specialize(t,'mul_le_cancel',k,rg,Mul(e,k)),t.hyp('nonzero'),joined)
        linear=apply(specialize(t,'add_left_mono',rg,Mul(e,k),Mul(r,y)),gap_bound)
        norm=_chain(CongMul(EqRefl(r),t.hyp('gap')),specialize(t,'mul_add',r,y,g))
        return _left(t,registry,linear,Add(Mul(r,y),Mul(e,k)),EqSym(norm))
    return introduce(s,('r','x','y','k','e','g'),('nonzero','scale','gap','square'),finish)


def _one_sided(s):
    from peano_lab.kernel.proofs import OrElim
    from peano_lab.kernel.terms import Mul
    def forward(t):
        r,x,y,k,e=t.terms(('r','x','y','k','e'))
        mono=apply(specialize(t,'mul_left_mono',x,y,r),t.hyp('ordered'))
        return apply(specialize(t,'allowance',Mul(r,x),Mul(r,y),Mul(e,k)),mono)
    def backward(t):
        x,y=t.terms(('x','y'))
        return eliminate(t,apply(specialize(t,'le_gap',y,x),t.hyp('ordered')),('g',),'gap',
            lambda u:apply(specialize(u,'oriented',*u.terms(('r','x','y','k','e','g'))),
                *(u.hyp(n) for n in ('nonzero','scale','gap','square'))))
    def finish(t):
        return OrElim(specialize(t,'le_total',*t.terms(('x','y'))),
            forward(t.hypothesis('ordered')),backward(t.hypothesis('ordered')))
    return introduce(s,('r','x','y','k','e'),('nonzero','scale','square'),finish)


def _root(s,registry):
    def finish(t):
        r,x,y,k,a,b=t.terms(PARAMETERS)
        upper=apply(specialize(t,'one_sided',r,x,y,k,a),t.hyp('nonzero'),t.hyp('scale'),t.hyp('upper'))
        scale=_right(t,registry,t.hyp('scale'),k,specialize(t,'add_comm',x,y))
        lower=apply(specialize(t,'one_sided',r,y,x,k,b),t.hyp('nonzero'),scale,t.hyp('lower'))
        return conjunction(upper,lower)
    return introduce(s,PARAMETERS,('nonzero','scale','upper','lower'),finish)


def prove_square_error_linear(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP048',target=frozen_square_error_linear_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'gap_square':_gap_square,'oriented':lambda s:_oriented(s,registry),'one_sided':_one_sided,
            'AP048':lambda s:_root(s,registry)},pins=square_error_linear_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
