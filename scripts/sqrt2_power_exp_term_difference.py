"""CV094: monotonicity and finite differences of supplied exponential terms.

For a common nonzero denominator and equal supplied initial scales, y=x+g
implies A[k+1]<=B[k+1] and d*B[k+1]<=d*A[k+1]+g*B[k]. All statements concern
actual finite recurrence data. There is no derivative, infinite sum or choice.
"""
from hashlib import sha256

from sqrt2_power_scaled_exp_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,scaled_exp_bound_source_pins,
    HELPER_SOURCES as BOUND_HELPERS,
)
from sqrt2_power_scaled_exp_tail import BOUND_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-term-difference-v1"
A,B=("ab","ac"),("bb","bc")
FIXED=("d","x","y","g","N")+A+B+("a0",)
REC_A="NatScaledExpRecurrence(d,x,ab,ac,N)"
REC_B="NatScaledExpRecurrence(d,y,bb,bc,N)"
PREMISES=("~d=0","y=x+g",REC_A,REC_B,"BetaAt(ab,ac,0,a0)","BetaAt(bb,bc,0,a0)")
ROWS="forall k a b c. Le(S k,N) -> BetaAt(ab,ac,S k,a) -> BetaAt(bb,bc,S k,b) -> BetaAt(bb,bc,k,c) -> Le(a,b) /\\ Le(d*b,d*a+g*c)"
NAMED_SOURCE="forall "+" ".join(FIXED)+". "+" -> ".join(PREMISES)+" -> "+ROWS
TARGET_SHA256="b58a497476351e3cc07a976d42021351568e27076943567eb7a2186d2dbc51d9"
HELPER_SOURCES={
    "first":"forall d x y g a0 a b. ~d=0 -> y=x+g -> d*a=x*a0 -> d*b=y*a0 -> Le(a,b) /\\ d*b=d*a+g*a0",
    "step":"forall d x y g j a b u v w. ~d=0 -> y=x+g -> Le(a,b) -> Le(d*b,d*a+g*w) -> ((S j)*d)*u=x*a -> ((S j)*d)*v=y*b -> (j*d)*b=y*w -> Le(u,v) /\\ Le(d*v,d*u+g*b)",
}
HELPER_TARGET_SHA256={"first":"712e987c5c721255963cc432139d3cffa0a40514f2f7c4b066bcd76a3f8124e8",
    "step":"e056b519b061bbe5d6d396a0f213c9d7eefc7f1300bf6a901c82825cecd96237"}
ARCHIVES=(BOUND_ARCHIVE,)
ENDPOINT_SOURCES={
    "mul_le_cancel":BOUND_HELPERS["mul_le_cancel"],
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)","succ_ne_zero":"forall a. ~S a=0",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)","mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "add_left_mono":"forall a b c. Le(a,b) -> Le(c+a,c+b)","add_right_mono":"forall a b c. Le(a,b) -> Le(a+c,b+c)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)","le_refl":"forall a. Le(a,a)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c","add_mul":"forall a b c. (a+b)*c=a*c+b*c",
    "add_assoc":"forall a b c. (a+b)+c=a+(b+c)","add_comm":"forall a b. a+b=b+a",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b","one_mul":"forall a. 1*a=a",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
}
ENDPOINT_OWNERS={name:"CV071" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES={
    "first":("mul_le_cancel","add_mul","add_comm"),
    "step":("mul_le_cancel","mul_ne_zero","succ_ne_zero","mul_left_mono","mul_right_mono",
        "add_left_mono","add_right_mono","le_trans","mul_assoc","mul_comm","mul_add","add_mul","add_assoc","add_comm","mul_succ_left"),
    "CV094":("first","step","beta_exists","beta_unique","one_mul","le_refl","le_succ","le_trans"),
}


class ExpTermDifferenceError(ValueError):
    """Changed finite recurrence, shared head, positive guard or difference."""


def frozen_exp_term_difference_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=10 or len(premises)!=6 or type(conclusion) is not Forall or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpTermDifferenceError("CV094 exact finite term difference changed")
    return target


def source_contract():
    return dict(code="CV094",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=6,two_supplied_recurrences_preserved=True,common_actual_initial_scale_required=True,
        explicit_nonnegative_argument_gap_required=True,nonzero_common_denominator_required=True,
        all_available_positive_indices=True,term_monotonicity_proved=True,
        finite_difference="d*B[k+1]<=d*A[k+1]+g*B[k]; y=x+g",
        zero_argument_gap_and_initial_scale_allowed=True,empty_horizon_allowed=True,
        only_proved_nonzero_successor_times_denominator_cancelled=True,
        derivative_claim=False,infinite_sum_claim=False,analytic_limit_claim=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def exp_term_difference_source_pins():
    result=scaled_exp_bound_source_pins()
    expected={
        "scripts/sqrt2_power_scaled_exp_bound.py":"717128c4845645cca66209b12512d4de2905d6ecc4eebad8c04c197647f9ee0c",
        "scripts/sqrt2_power_scaled_exp_tail.py":"df81a3c92b26346a1955ba92e763d932201649183604309f17bd156b2abbaeb3",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_term_difference.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpTermDifferenceError("term-difference source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _first(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        d,x,y,g,a0,a,b=t.terms(("d","x","y","g","a0","a","b"))
        exact=_chain(t.hyp("rec_b"),CongMul(t.hyp("argument_gap"),EqRefl(a0)),
            specialize(t,"add_mul",x,g,a0),CongAdd(EqSym(t.hyp("rec_a")),EqRefl(Mul(g,a0))))
        order=witness((Mul(g,a0),),_chain(specialize(t,"add_comm",Mul(g,a0),Mul(d,a)),EqSym(exact)))
        return conjunction(apply(specialize(t,"mul_le_cancel",d,a,b),t.hyp("nonzero"),order),exact)
    return introduce(s,("d","x","y","g","a0","a","b"),("nonzero","argument_gap","rec_a","rec_b"),finish)


def _step(s,registry):
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul,Succ
    def finish(t):
        d,x,y,g,j,a,b,u,v,w=t.terms(("d","x","y","g","j","a","b","u","v","w"))
        c=Mul(Succ(j),d);r=Mul(Mul(g,d),b)
        cnz=apply(specialize(t,"mul_ne_zero",Succ(j),d),specialize(t,"succ_ne_zero",j),t.hyp("nonzero"))
        xy=witness((g,),_chain(specialize(t,"add_comm",g,x),EqSym(t.hyp("argument_gap"))))
        mono=apply(specialize(t,"le_trans",Mul(x,a),Mul(x,b),Mul(y,b)),
            apply(specialize(t,"mul_left_mono",a,b,x),t.hyp("old_monotone")),
            apply(specialize(t,"mul_right_mono",x,y,b),xy))
        mono=_subst(t,registry,"Le(slot,y*b)",EqSym(t.hyp("next_a")),mono)
        mono=_subst(t,registry,"Le(((S j)*d)*u,slot)",EqSym(t.hyp("next_b")),mono)
        mono=apply(specialize(t,"mul_le_cancel",c,u,v),cnz,mono)

        old=apply(specialize(t,"mul_left_mono",Mul(d,b),Add(Mul(d,a),Mul(g,w)),x),t.hyp("old_difference"))
        old=apply(specialize(t,"add_right_mono",Mul(x,Mul(d,b)),Mul(x,Add(Mul(d,a),Mul(g,w))),r),old)
        left=_chain(_multiplicative_equal(t,Mul(c,Mul(d,v)),Mul(d,Mul(c,v))),
            CongMul(EqRefl(d),t.hyp("next_b")),CongMul(EqRefl(d),CongMul(t.hyp("argument_gap"),EqRefl(b))),
            CongMul(EqRefl(d),specialize(t,"add_mul",x,g,b)),specialize(t,"mul_add",d,Mul(x,b),Mul(g,b)),
            CongAdd(_multiplicative_equal(t,Mul(d,Mul(x,b)),Mul(x,Mul(d,b))),
                _multiplicative_equal(t,Mul(d,Mul(g,b)),r)))
        old=_subst(t,registry,"Le(slot,x*(d*a+g*w)+(g*d)*b)",EqSym(left),old)
        distributed=CongAdd(specialize(t,"mul_add",x,Mul(d,a),Mul(g,w)),EqRefl(r))
        old=_subst(t,registry,"Le(((S j)*d)*(d*v),slot)",distributed,old)
        xa,xgw,ygw=Mul(x,Mul(d,a)),Mul(x,Mul(g,w)),Mul(y,Mul(g,w))
        grow=apply(specialize(t,"mul_right_mono",x,y,Mul(g,w)),xy)
        grow=apply(specialize(t,"add_left_mono",xgw,ygw,xa),grow)
        grow=apply(specialize(t,"add_right_mono",Add(xa,xgw),Add(xa,ygw),r),grow)
        combined=apply(specialize(t,"le_trans",Mul(c,Mul(d,v)),Add(Add(xa,xgw),r),Add(Add(xa,ygw),r)),old,grow)
        first=_chain(_multiplicative_equal(t,xa,Mul(d,Mul(x,a))),CongMul(EqRefl(d),EqSym(t.hyp("next_a"))),
            _multiplicative_equal(t,Mul(d,Mul(c,u)),Mul(c,Mul(d,u))))
        second=_chain(_multiplicative_equal(t,ygw,Mul(g,Mul(y,w))),CongMul(EqRefl(g),EqSym(t.hyp("previous_b"))),
            _multiplicative_equal(t,Mul(g,Mul(Mul(j,d),b)),Mul(j,r)))
        right=_chain(CongAdd(CongAdd(first,second),EqRefl(r)),specialize(t,"add_assoc",Mul(c,Mul(d,u)),Mul(j,r),r),
            CongAdd(EqRefl(Mul(c,Mul(d,u))),EqSym(specialize(t,"mul_succ_left",j,r))),
            CongAdd(EqRefl(Mul(c,Mul(d,u))),_multiplicative_equal(t,Mul(Succ(j),r),Mul(c,Mul(g,b)))),
            EqSym(specialize(t,"mul_add",c,Mul(d,u),Mul(g,b))))
        combined=_subst(t,registry,"Le(((S j)*d)*(d*v),slot)",right,combined)
        difference=apply(specialize(t,"mul_le_cancel",c,Mul(d,v),Add(Mul(d,u),Mul(g,b))),cnz,combined)
        return conjunction(mono,difference)
    return introduce(s,("d","x","y","g","j","a","b","u","v","w"),
        ("nonzero","argument_gap","old_monotone","old_difference","next_a","next_b","previous_b"),finish)


def _root(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def base(t):
        d,x,y,g,a0,a,b,c=t.terms(("d","x","y","g","a0","a","b","c"))
        rec_a=apply(specialize(t,"recurrence_a",Zero(),a0,a),t.hyp("bound"),t.hyp("head_a"),t.hyp("value_a"))
        rec_b=apply(specialize(t,"recurrence_b",Zero(),a0,b),t.hyp("bound"),t.hyp("head_b"),t.hyp("value_b"))
        rec_a=_chain(EqSym(CongMul(specialize(t,"one_mul",d),EqRefl(a))),rec_a)
        rec_b=_chain(EqSym(CongMul(specialize(t,"one_mul",d),EqRefl(b))),rec_b)
        first=apply(specialize(t,"first",d,x,y,g,a0,a,b),t.hyp("nonzero"),t.hyp("argument_gap"),rec_a,rec_b)
        difference=_subst(t,registry,"Le(d*b,slot)",AndElimR(first),specialize(t,"le_refl",Mul(d,b)))
        head=apply(specialize(t,"beta_unique",*t.terms(B),Zero(),c,a0),t.hyp("previous_b"),t.hyp("head_b"))
        difference=_subst(t,registry,"Le(d*b,d*a+g*slot)",EqSym(head),difference)
        return conjunction(AndElimL(first),difference)
    def successor(t):
        def chosen(u):
            d,x,y,g,k,N,a,b,c,old_a,older_b=u.terms(("d","x","y","g","k","N","a","b","c","old_a","older_b"))
            sk=Succ(k)
            earlier=apply(specialize(u,"le_trans",sk,Succ(sk),N),apply(specialize(u,"le_succ",sk,sk),specialize(u,"le_refl",sk)),u.hyp("bound"))
            old=apply(specialize(u,"IH",old_a,c,older_b),earlier,u.hyp("old_a_entry"),u.hyp("previous_b"),u.hyp("older_b_entry"))
            next_a=apply(specialize(u,"recurrence_a",sk,old_a,a),u.hyp("bound"),u.hyp("old_a_entry"),u.hyp("value_a"))
            next_b=apply(specialize(u,"recurrence_b",sk,c,b),u.hyp("bound"),u.hyp("previous_b"),u.hyp("value_b"))
            previous_b=apply(specialize(u,"recurrence_b",k,older_b,c),earlier,u.hyp("older_b_entry"),u.hyp("previous_b"))
            return apply(specialize(u,"step",d,x,y,g,sk,old_a,c,a,b,older_b),u.hyp("nonzero"),u.hyp("argument_gap"),
                AndElimL(old),AndElimR(old),next_a,next_b,previous_b)
        return eliminate(t,specialize(t,"beta_exists",*t.terms(A),Succ(t.term("k"))),("old_a",),"old_a_entry",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(B),u.term("k")),("older_b",),"older_b_entry",chosen))
    motive=target
    for _ in FIXED:
        motive=motive.body
    for _ in PREMISES:
        motive=motive.right
    motive=motive.body
    rows=("a","b","c");hyps=("bound","value_a","value_b","previous_b")
    return introduce(s,FIXED,("nonzero","argument_gap","recurrence_a","recurrence_b","head_a","head_b"),lambda t:
        Ind(motive,introduce(t,rows,hyps,base),introduce(t,("k",),("IH",),lambda u:introduce(u,rows,hyps,successor))))


def prove_exp_term_difference(*,limits=None):
    registry=definition_registry();target=frozen_exp_term_difference_target()
    return assemble_mixed_certificate(code="CV094",target=target,registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"first":lambda s:_first(s,registry),"step":lambda s:_step(s,registry),"CV094":lambda s:_root(s,target,registry)},
        pins=exp_term_difference_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
