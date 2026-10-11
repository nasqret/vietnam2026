"""AP045: combine finite square and reference-to-two errors by natural algebra.

The square/source comparison is supplied, not built into a definition. At
r<=p, a product error 2/p and reference error 1/r give upper error 3/r and
lower error 1/r. Only positive b,p are cancelled; a,s,r may vanish.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_supplied_product import (
    ROOT,Scope,introduce,apply,specialize,conjunction,canonical,json_hash,
    source_registry,exp_supplied_product_source_pins,BOUND_ARCHIVE,
)
from sqrt2_power_exp_two_sided_continuity import _left,_right
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA='sqrt2-power-half-square-error-transfer-v1'
PARAMETERS=('r','p','b','a','s','v')
PREMISES=('~b=0','~p=0','Le(r,p)','Le(a*v,b*s)','Le(p*(b*s),p*(a*v)+2*(b*a))',
    'Le(r*v,(r*2)*b+b)','Le((r*2)*b,r*v+b)')
CONCLUSION='Le(r*s,(r*2)*a+3*a) /\\ Le((r*2)*a,r*s+a)'
NAMED_SOURCE='forall '+' '.join(PARAMETERS)+'. '+' -> '.join(PREMISES)+' -> '+CONCLUSION
TARGET_SHA256='3d7f11a02582d2bf7b63377cc8ec2bbabf74c584db7e7e1f5627256c208e7c84'
HELPER_SOURCES={
    'triple':'forall a. 3*a=a+2*a',
    'weaken':'forall p r s t e. ~p=0 -> Le(r,p) -> Le(p*s,p*t+2*e) -> Le(r*s,r*t+2*e)',
    'upper':'forall r b a s v. ~b=0 -> Le(r*(b*s),r*(a*v)+2*(b*a)) -> Le(r*v,(r*2)*b+b) -> Le(r*s,(r*2)*a+3*a)',
    'lower':'forall r b a s v. ~b=0 -> Le(a*v,b*s) -> Le((r*2)*b,r*v+b) -> Le((r*2)*a,r*s+a)',
}
HELPER_TARGET_SHA256={'triple':'7b544d1ce50c84623fd5df8b0302f03a096f179e89f8380f56c0491ce6b342f3',
    'weaken':'f822aecef7246ad0fb0a576bfe5fa86ca579b4b89c06e920b7b581a9cf4049a9',
    'upper':'e58f590fd5bd39b0180c925152551a4c34e3e11b96ef7a7bec6d749dbcd6153d',
    'lower':'a8d8a687a72832d6050a31b451cc5bc678150bc0298a71fb9c1dc1e0f06e4077'}
ARCHIVES=(BOUND_ARCHIVE,)
ENDPOINT_SOURCES={
    'mul_left_mono':'forall a b c. Le(a,b) -> Le(c*a,c*b)',
    'add_left_mono':'forall a b c. Le(a,b) -> Le(c+a,c+b)',
    'add_right_mono':'forall a b c. Le(a,b) -> Le(a+c,b+c)',
    'le_trans':'forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)',
    'mul_le_cancel':'forall c a b. ~c=0 -> Le(c*a,c*b) -> Le(a,b)',
    'mul_assoc':'forall a b c. (a*b)*c=a*(b*c)',
    'mul_comm':'forall a b. a*b=b*a','mul_add':'forall a b c. a*(b+c)=a*b+a*c',
    'add_assoc':'forall a b c. (a+b)+c=a+(b+c)','add_comm':'forall a b. a+b=b+a',
    'mul_succ_left':'forall a b. (S a)*b=a*b+b',
}
ENDPOINT_OWNERS={name:'CV071' for name in ENDPOINT_SOURCES}
ARITHMETIC=('mul_left_mono','add_left_mono','add_right_mono','le_trans','mul_le_cancel','mul_assoc','mul_comm','mul_add','add_assoc')
HELPER_DEPENDENCIES={'triple':('mul_succ_left','add_comm'),
    'weaken':ARITHMETIC,'upper':ARITHMETIC+('triple',),'lower':ARITHMETIC,
    'AP045':('weaken','upper','lower')}


class HalfSquareErrorTransferError(ValueError):
    """Changed supplied cross bounds, precision order, guards or error scale."""


def definition_registry():
    pool=source_registry();spec=pool['Le']
    if spec.conceptual_dependencies:
        raise HalfSquareErrorTransferError('existing natural order gained a dependency')
    return MappingProxyType({'Le':spec})


def frozen_half_square_error_transfer_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=7 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HalfSquareErrorTransferError('AP045 exact finite square-error transfer changed')
    return target


def source_contract():
    return dict(code='AP045',schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=7,all_five_supplied_natural_inequalities_preserved=True,
        positive_cancellation_factors=['b','p'],precision_order='r<=p',
        allows_zero_r_a_s_v=True,upper_error_coefficient=3,lower_error_coefficient=1,
        square_or_exponential_construction_claimed=False,new_induction_needed=False,new_induction_count=0,
        new_definition_ids=[],definition_admissions=0,analytic_limit_claim=False,original_HA_checked=False,
        authority='source_contract_not_proof_authority',closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def half_square_error_transfer_source_pins():
    result=exp_supplied_product_source_pins()
    expected={'scripts/sqrt2_power_exp_supplied_product.py':'3a05743cbfecb01fd2a4cc907dea3e7808a5c98396b5329fd908a6ec445d905f',
        **{pin['path']:pin['sha256'] for pin in ARCHIVES}}
    for name in (*expected,'scripts/sqrt2_power_half_square_error_transfer.py'):
        with (ROOT/name).open('rb') as stream: raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HalfSquareErrorTransferError('finite square-error source or actual archive changed')
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _triple(s):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()))
    return introduce(s,('a',),(),lambda t:_chain(specialize(t,'mul_succ_left',two,t.term('a')),
        specialize(t,'add_comm',Mul(two,t.term('a')),t.term('a'))))


def _weaken(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        p,r,s,v,e=t.terms(('p','r','s','t','e'));two=Succ(Succ(Zero()));E=Mul(two,e)
        rs,rv=Mul(r,s),Mul(r,v);left=Mul(p,rs);base=Mul(p,rv)
        bound=apply(specialize(t,'mul_left_mono',Mul(p,s),Add(Mul(p,v),E),r),t.hyp('bound'))
        bound=_left(t,registry,bound,Mul(r,Add(Mul(p,v),E)),_multiplicative_equal(t,Mul(r,Mul(p,s)),left))
        expanded=_chain(specialize(t,'mul_add',r,Mul(p,v),E),CongAdd(_multiplicative_equal(t,Mul(r,Mul(p,v)),base),EqRefl(Mul(r,E))))
        bound=_right(t,registry,bound,left,expanded)
        tail=apply(specialize(t,'mul_left_mono',r,p,E),t.hyp('order'))
        tail=_left(t,registry,tail,Mul(E,p),specialize(t,'mul_comm',E,r))
        tail=_right(t,registry,tail,Mul(r,E),specialize(t,'mul_comm',E,p))
        tail=apply(specialize(t,'add_left_mono',Mul(r,E),Mul(p,E),base),tail)
        joined=apply(specialize(t,'le_trans',left,Add(base,Mul(r,E)),Add(base,Mul(p,E))),bound,tail)
        joined=_right(t,registry,joined,left,EqSym(specialize(t,'mul_add',p,rv,E)))
        return apply(specialize(t,'mul_le_cancel',p,rs,Add(rv,E)),t.hyp('nonzero'),joined)
    return introduce(s,('p','r','s','t','e'),('nonzero','order','bound'),finish)


def _upper(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        r,b,a,s,v=t.terms(('r','b','a','s','v'));two=Succ(Succ(Zero()));three=Succ(two)
        base=Mul(Mul(r,two),a);ba=Mul(b,a);extra=Mul(two,ba)
        X=Mul(r,Mul(a,v));Y=Mul(r,Mul(b,s));Z=Add(Mul(b,base),ba)
        source_right=Add(Mul(Mul(r,two),b),b)
        order=apply(specialize(t,'mul_left_mono',Mul(r,v),source_right,a),t.hyp('reference'))
        order=_left(t,registry,order,Mul(a,source_right),_multiplicative_equal(t,Mul(a,Mul(r,v)),X))
        expanded=_chain(specialize(t,'mul_add',a,Mul(Mul(r,two),b),b),
            CongAdd(_multiplicative_equal(t,Mul(a,Mul(Mul(r,two),b)),Mul(b,base)),specialize(t,'mul_comm',a,b)))
        order=_right(t,registry,order,X,expanded)
        order=apply(specialize(t,'add_right_mono',X,Z,extra),order)
        joined=apply(specialize(t,'le_trans',Y,Add(X,extra),Add(Z,extra)),t.hyp('product'),order)
        norm=_chain(specialize(t,'add_assoc',Mul(b,base),ba,extra),
            CongAdd(EqRefl(Mul(b,base)),CongAdd(EqRefl(ba),_multiplicative_equal(t,extra,Mul(b,Mul(two,a))))),
            CongAdd(EqRefl(Mul(b,base)),EqSym(specialize(t,'mul_add',b,a,Mul(two,a)))),
            CongAdd(EqRefl(Mul(b,base)),CongMul(EqRefl(b),EqSym(specialize(t,'triple',a)))),
            EqSym(specialize(t,'mul_add',b,base,Mul(three,a))))
        joined=_right(t,registry,joined,Y,norm)
        joined=_left(t,registry,joined,Mul(b,Add(base,Mul(three,a))),_multiplicative_equal(t,Y,Mul(b,Mul(r,s))))
        return apply(specialize(t,'mul_le_cancel',b,Mul(r,s),Add(base,Mul(three,a))),t.hyp('nonzero'),joined)
    return introduce(s,('r','b','a','s','v'),('nonzero','product','reference'),finish)


def _lower(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    def finish(t):
        r,b,a,s,v=t.terms(('r','b','a','s','v'));two=Succ(Succ(Zero()))
        base=Mul(Mul(r,two),a);ba=Mul(b,a);X=Mul(r,Mul(a,v));Y=Mul(r,Mul(b,s));left=Mul(b,base)
        order=apply(specialize(t,'mul_left_mono',Mul(Mul(r,two),b),Add(Mul(r,v),b),a),t.hyp('reference'))
        order=_left(t,registry,order,Mul(a,Add(Mul(r,v),b)),_multiplicative_equal(t,Mul(a,Mul(Mul(r,two),b)),left))
        expanded=_chain(specialize(t,'mul_add',a,Mul(r,v),b),
            CongAdd(_multiplicative_equal(t,Mul(a,Mul(r,v)),X),specialize(t,'mul_comm',a,b)))
        order=_right(t,registry,order,left,expanded)
        comparison=apply(specialize(t,'mul_left_mono',Mul(a,v),Mul(b,s),r),t.hyp('product'))
        comparison=apply(specialize(t,'add_right_mono',X,Y,ba),comparison)
        joined=apply(specialize(t,'le_trans',left,Add(X,ba),Add(Y,ba)),order,comparison)
        norm=_chain(CongAdd(_multiplicative_equal(t,Y,Mul(b,Mul(r,s))),EqRefl(ba)),EqSym(specialize(t,'mul_add',b,Mul(r,s),a)))
        joined=_right(t,registry,joined,left,norm)
        return apply(specialize(t,'mul_le_cancel',b,base,Add(Mul(r,s),a)),t.hyp('nonzero'),joined)
    return introduce(s,('r','b','a','s','v'),('nonzero','product','reference'),finish)


def _root(s):
    from peano_lab.kernel.terms import Mul
    def finish(t):
        r,p,b,a,s,v=t.terms(PARAMETERS)
        weakened=apply(specialize(t,'weaken',p,r,Mul(b,s),Mul(a,v),Mul(b,a)),t.hyp('p_nonzero'),t.hyp('order'),t.hyp('product_upper'))
        upper=apply(specialize(t,'upper',r,b,a,s,v),t.hyp('b_nonzero'),weakened,t.hyp('reference_upper'))
        lower=apply(specialize(t,'lower',r,b,a,s,v),t.hyp('b_nonzero'),t.hyp('product_lower'),t.hyp('reference_lower'))
        return conjunction(upper,lower)
    return introduce(s,PARAMETERS,('b_nonzero','p_nonzero','order','product_lower','product_upper','reference_upper','reference_lower'),finish)


def prove_half_square_error_transfer(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code='AP045',target=frozen_half_square_error_transfer_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={'triple':_triple,'weaken':lambda s:_weaken(s,registry),'upper':lambda s:_upper(s,registry),
            'lower':lambda s:_lower(s,registry),'AP045':_root},
        pins=half_square_error_transfer_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
