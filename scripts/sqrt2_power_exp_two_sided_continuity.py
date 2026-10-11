"""AP007: two-sided finite exponential continuity without input monotonicity.

Split the decidable order of natural cross-products, extract its actual gap,
and replay CV098 in that orientation. Keep the common error multiplier: it
need not divide either denominator and it may be zero. No analytic axiom.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_exp_cross_continuity import (
    ROOT,Scope,introduce,eliminate,witness,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as continuity_registry,exp_cross_continuity_source_pins,
    NAMED_SOURCE as CONTINUITY_SOURCE,
)
from sqrt2_power_exp_rational_continuity import CROSS_ARCHIVE
from sqrt2_power_quadratic_height import _chain,_additive_equal
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-two-sided-continuity-v1"
PARAMETERS=("d","e","x","y","C","R","H","N","ab","ac","bb","bc","a0","b0","s","t")
DATA_PREMISES=("NatScaledExpRecurrence(d,x,ab,ac,N)","NatScaledExpRecurrence(e,y,bb,bc,N)",
    "BetaAt(ab,ac,0,a0)","BetaAt(bb,bc,0,b0)","Sum(ab,ac,S N,s)","Sum(bb,bc,S N,t)")
PREMISES=("~d=0","~e=0","Le(x,d)","Le(y,e)","Le(C*(d*y),C*(e*x)+R)",
    "Le(C*(e*x),C*(d*y)+H)")+DATA_PREMISES
CONCLUSION=("Le(C*((d*e)*(a0*t)),C*((d*e)*(b0*s))+9*(R*(a0*b0))) /\\ "
    "Le(C*((d*e)*(b0*s)),C*((d*e)*(a0*t))+9*(H*(a0*b0)))")
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> "+CONCLUSION
TARGET_SHA256="d6c797957cd58e4b92514bcc10063e71045c1cdbe995aeeef3bff5020d434a11"
ORDERED_PARAMETERS=PARAMETERS+("g",)
ORDERED_PREMISES=("~d=0","~e=0","Le(y,e)","d*y=e*x+g","Le(C*(d*y),C*(e*x)+R)")+DATA_PREMISES
HELPER_SOURCES={
    "bound_two":"forall a b. Le(a,b) -> Le(a,2*b)",
    "le_gap":"forall a b. Le(a,b) -> exists g. b=a+g",
    "cancel_order":"forall a u v. Le(a+u,a+v) -> Le(u,v)",
    "scaled_gap":"forall a b g C R. b=a+g -> Le(C*b,C*a+R) -> Le(C*g,R)",
    "error_transport":"forall a b C g R w. Le(a,b+9*(g*w)) -> Le(C*g,R) -> Le(C*a,C*b+9*(R*w))",
    "allowance":"forall a b z. Le(a,b) -> Le(a,b+z)",
    "oriented":"forall "+" ".join(ORDERED_PARAMETERS)+". "+" -> ".join(ORDERED_PREMISES)+" -> "+CONCLUSION,
}
HELPER_TARGET_SHA256={
    "bound_two":"4bedee01192037e86762e6767a5e12cad0b2dc565703e855278895e255f26f17",
    "le_gap":"a7e272606b7b3cedfe9ca66427b7303616b83a7ec77bb642704cf37fe79da5b7",
    "cancel_order":"fc3af5c3007c72be1b50b26e003e8862332bc42180826851b47801fd46bb4f5a",
    "scaled_gap":"18f93c8754661db7dac0c02ac7f06e997c7f600e495c7bb9a939f150e0c248e8",
    "error_transport":"4d4bd1fe9122d864ca93da6c1df96040dc2f02bd6e08372c8b7364e9d02e1b63",
    "allowance":"da9bec09bf6fd686d23664b5d4982d5fc8f0ef7321672d6d6448d44fc68d68d7",
    "oriented":"b16ed6bc5805db151d41acbdd658087cb619fc2aa8d748bd340dd48b5ab0fa69",
}
ARCHIVES=(CROSS_ARCHIVE,)
ENDPOINT_SOURCES={
    "continuity":CONTINUITY_SOURCE,
    "le_total":"forall a b. Le(a,b) \\/ Le(b,a)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "add_left_cancel":"forall a b c. a+b=a+c -> b=c",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)","add_comm":"forall a b. a+b=b+a",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b","one_mul":"forall a. 1*a=a",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)",
}
ENDPOINT_OWNERS={name:"CV098" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES={
    "bound_two":("mul_succ_left","one_mul","le_trans"),
    "le_gap":("add_comm",),
    "cancel_order":("add_assoc","add_comm","add_left_cancel"),
    "scaled_gap":("mul_add","cancel_order"),
    "error_transport":("mul_left_mono","mul_right_mono","add_left_mono","mul_add","mul_assoc","mul_comm","le_trans"),
    "allowance":("add_comm","le_trans"),
    "oriented":("bound_two","continuity","scaled_gap","error_transport","allowance","mul_left_mono"),
    "AP007":("le_total","le_gap","oriented","mul_assoc","mul_comm"),
}


class ExpTwoSidedContinuityError(ValueError):
    """Changed supplied recurrences, error scales, ordinary bodies or target."""


def definition_registry():
    source=continuity_registry();needed=set();pending=["Le","Lt","BetaAt","Sum","NatScaledExpRecurrence"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed}
    seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise ExpTwoSidedContinuityError("reused recurrence definition DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_exp_two_sided_continuity_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=16 or len(premises)!=12 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpTwoSidedContinuityError("AP007 exact two-sided scaled continuity target changed")
    return target


def source_contract():
    return dict(code="AP007",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=12,both_supplied_recurrences_heads_sums_preserved=True,same_degree_required=True,
        common_error_multiplier_preserved=True,zero_error_multiplier_and_heads_allowed=True,
        positive_input_denominators_required=True,argument_monotonicity_assumed=False,
        natural_cross_product_order_case_split=True,actual_additive_gap_eliminated=True,
        independent_denominator_and_head_scales=True,finite_lipschitz_constant=9,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_two_sided_continuity_source_pins():
    result=exp_cross_continuity_source_pins()
    expected={"scripts/sqrt2_power_exp_cross_continuity.py":"df8ebc21517107b814a6f1e55903bb412d37a5b09917eeef6a47930b557b0bcd",
        "scripts/sqrt2_power_exp_rational_continuity.py":"70c6fce20acd01244345eb8e443a262cb6361992b806d6404bb54cabf6df11da",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_two_sided_continuity.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpTwoSidedContinuityError("two-sided continuity source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _left(t,registry,proof,right,equality):
    from peano_lab.kernel.terms import pretty_term
    return _subst(t,registry,"Le(slot,"+pretty_term(right,list(t.variables))+")",equality,proof)


def _right(t,registry,proof,left,equality):
    from peano_lab.kernel.terms import pretty_term
    return _subst(t,registry,"Le("+pretty_term(left,list(t.variables))+",slot)",equality,proof)


def _bound_two(s):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def finish(t):
        a,b=t.terms(("a","b"))
        double=_chain(specialize(t,"mul_succ_left",one,b),CongAdd(specialize(t,"one_mul",b),EqRefl(b)))
        return apply(specialize(t,"le_trans",a,b,Mul(two,b)),t.hyp("bound"),witness((b,),EqSym(double)))
    return introduce(s,("a","b"),("bound",),finish)


def _le_gap(s):
    from peano_lab.kernel.proofs import EqSym
    return introduce(s,("a","b"),("bound",),lambda t:eliminate(t,t.hyp("bound"),("g",),"gap",
        lambda u:witness((u.term("g"),),_chain(EqSym(u.hyp("gap")),specialize(u,"add_comm",*u.terms(("g","a")))))))


def _cancel_order(s):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Add
    def decoded(u):
        a,x,y,h=u.terms(("a","u","v","h"))
        equal=_chain(EqSym(_additive_equal(u,Add(h,Add(a,x)),Add(a,Add(h,x)))),u.hyp("gap"))
        return witness((h,),apply(specialize(u,"add_left_cancel",a,Add(h,x),y),equal))
    return introduce(s,("a","u","v"),("bound",),lambda t:eliminate(t,t.hyp("bound"),("h",),"gap",decoded))


def _scaled_gap(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl
    from peano_lab.kernel.terms import Add,Mul
    def finish(t):
        a,b,g,C,R=t.terms(("a","b","g","C","R"));right=Add(Mul(C,a),R)
        p=_left(t,registry,t.hyp("bound"),right,CongMul(EqRefl(C),t.hyp("gap")))
        p=_left(t,registry,p,right,specialize(t,"mul_add",C,a,g))
        return apply(specialize(t,"cancel_order",Mul(C,a),Mul(C,g),R),p)
    return introduce(s,("a","b","g","C","R"),("gap","bound"),finish)


def _error_transport(s,registry):
    from peano_lab.kernel.proofs import CongAdd,EqRefl
    from peano_lab.kernel.terms import Add,Mul,parse_term
    nine=parse_term("9")
    def finish(t):
        a,b,C,g,R,w=t.terms(("a","b","C","g","R","w"))
        ca,cb,cg=Mul(C,a),Mul(C,b),Mul(C,g);err=Mul(nine,Mul(g,w));miderr=Mul(nine,Mul(cg,w));finalerr=Mul(nine,Mul(R,w))
        p=apply(specialize(t,"mul_left_mono",a,Add(b,err),C),t.hyp("bound"))
        p=_right(t,registry,p,ca,specialize(t,"mul_add",C,b,err))
        p=_right(t,registry,p,ca,CongAdd(EqRefl(cb),_multiplicative_equal(t,Mul(C,err),miderr)))
        q=apply(specialize(t,"mul_right_mono",cg,R,w),t.hyp("gap_bound"))
        q=apply(specialize(t,"mul_left_mono",Mul(cg,w),Mul(R,w),nine),q)
        q=apply(specialize(t,"add_left_mono",miderr,finalerr,cb),q)
        return apply(specialize(t,"le_trans",ca,Add(cb,miderr),Add(cb,finalerr)),p,q)
    return introduce(s,("a","b","C","g","R","w"),("bound","gap_bound"),finish)


def _allowance(s):
    from peano_lab.kernel.terms import Add
    def finish(t):
        a,b,z=t.terms(("a","b","z"))
        return apply(specialize(t,"le_trans",a,b,Add(b,z)),t.hyp("bound"),witness((z,),specialize(t,"add_comm",z,b)))
    return introduce(s,("a","b","z"),("bound",),finish)


def _oriented(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,parse_term
    def finish(t):
        d,e,x,y,C,R,H,N,ab,ac,bb,bc,a0,b0,u,v,g=t.terms(ORDERED_PARAMETERS)
        p=apply(specialize(t,"continuity",d,e,x,y,g,N,ab,ac,bb,bc,a0,b0,u,v),
            t.hyp("d_nonzero"),t.hyp("e_nonzero"),t.hyp("gap"),apply(specialize(t,"bound_two",y,e),t.hyp("bound_b")),
            *(t.hyp(n) for n in ("recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b")))
        gap=apply(specialize(t,"scaled_gap",Mul(e,x),Mul(d,y),g,C,R),t.hyp("gap"),t.hyp("forward"))
        de=Mul(d,e);av=Mul(a0,v);bu=Mul(b0,u);heads=Mul(a0,b0)
        forward=apply(specialize(t,"error_transport",Mul(de,av),Mul(de,bu),C,g,R,heads),AndElimR(p),gap)
        backward=apply(specialize(t,"mul_left_mono",bu,av,de),AndElimL(p))
        backward=apply(specialize(t,"mul_left_mono",Mul(de,bu),Mul(de,av),C),backward)
        backward=apply(specialize(t,"allowance",Mul(C,Mul(de,bu)),Mul(C,Mul(de,av)),Mul(parse_term("9"),Mul(H,heads))),backward)
        return conjunction(forward,backward)
    return introduce(s,ORDERED_PARAMETERS,("d_nonzero","e_nonzero","bound_b","gap","forward",
        "recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b"),finish)


def _root(s,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongAdd,OrElim
    from peano_lab.kernel.terms import Add,Mul,parse_term
    def branch(t,reverse):
        d,e,x,y=t.terms(("d","e","x","y"));a,b=(Mul(d,y),Mul(e,x)) if reverse else (Mul(e,x),Mul(d,y))
        def decoded(u):
            d,e,x,y,C,R,H,N,ab,ac,bb,bc,a0,b0,v,w=u.terms(PARAMETERS)
            params=(e,d,y,x,C,H,R,N,bb,bc,ab,ac,b0,a0,w,v) if reverse else u.terms(PARAMETERS)
            names=("e_nonzero","d_nonzero","bound_a","gap","backward","recurrence_b","recurrence_a","head_b","head_a","sum_b","sum_a") if reverse else (
                "d_nonzero","e_nonzero","bound_b","gap","forward","recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b")
            p=apply(specialize(u,"oriented",*params,u.term("g")),*(u.hyp(n) for n in names))
            if not reverse:
                return p
            de,ed=Mul(d,e),Mul(e,d);av,bu=Mul(a0,w),Mul(b0,v);heads,swapped=Mul(a0,b0),Mul(b0,a0);nine=parse_term("9")
            def align(proof,left,right,err):
                oldleft,oldright=Mul(C,Mul(ed,left)),Mul(C,Mul(ed,right))
                newleft,newright=Mul(C,Mul(de,left)),Mul(C,Mul(de,right))
                olderr,newerr=Mul(nine,Mul(err,swapped)),Mul(nine,Mul(err,heads))
                proof=_left(u,registry,proof,Add(oldright,olderr),_multiplicative_equal(u,oldleft,newleft))
                return _right(u,registry,proof,newleft,CongAdd(_multiplicative_equal(u,oldright,newright),_multiplicative_equal(u,olderr,newerr)))
            return conjunction(align(AndElimR(p),av,bu,R),align(AndElimL(p),bu,av,H))
        return eliminate(t,apply(specialize(t,"le_gap",a,b),t.hyp("ordered")),("g",),"gap",decoded)
    def finish(t):
        d,e,x,y=t.terms(("d","e","x","y"))
        return OrElim(specialize(t,"le_total",Mul(e,x),Mul(d,y)),branch(t.hypothesis("ordered"),False),branch(t.hypothesis("ordered"),True))
    return introduce(s,PARAMETERS,("d_nonzero","e_nonzero","bound_a","bound_b","forward","backward",
        "recurrence_a","recurrence_b","head_a","head_b","sum_a","sum_b"),finish)


def prove_exp_two_sided_continuity(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP007",target=frozen_exp_two_sided_continuity_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"bound_two":_bound_two,"le_gap":_le_gap,"cancel_order":_cancel_order,
            "scaled_gap":lambda s:_scaled_gap(s,registry),"error_transport":lambda s:_error_transport(s,registry),
            "allowance":_allowance,"oriented":_oriented,"AP007":lambda s:_root(s,registry)},
        pins=exp_two_sided_continuity_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
