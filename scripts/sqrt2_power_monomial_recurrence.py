"""CV072: adjacent recurrence of supplied actual scaled monomial values.

Reuse CV061's exact row-value monomial formula. The nonzero scale p permits
ordinary guarded cancellation of the actual value p^k; no analytic identity,
code-number equality or unguarded division is introduced.
"""
from hashlib import sha256

from sqrt2_power_scaled_exp_terms import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,scaled_exp_terms_source_pins,
    COMPOSITION_ARCHIVE,
)
from sqrt2_power_full_composition_evaluation import MONOMIALS
from sqrt2_power_composition_evaluation import GEOMETRIC_ARCHIVE
from sqrt2_power_composition_recurrence import RECURRENCE_ARCHIVE
from sqrt2_power_geometric_horner import HELPER_SOURCES as GEOMETRIC_HELPERS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-monomial-recurrence-v1"
V = ("vb","vc")
PARAMETERS = ("p","t","x","v","K")+V
ADJACENT = "forall k y z. Lt(S k,K) -> BetaAt(vb,vc,k,y) -> BetaAt(vb,vc,S k,z) -> p*z=(t*x)*y"
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". ~p=0 -> ("+MONOMIALS+") -> (Lt(0,K) -> BetaAt(vb,vc,0,v)) /\\ ("+ADJACENT+")"
TARGET_SHA256 = "1cac9f24c8b7573372bdfab838b9e0b9248a42d1681fde0d65e7da2768df79c8"
HELPER_SOURCES = {
    "head":"forall "+" ".join(PARAMETERS)+". ("+MONOMIALS+") -> Lt(0,K) -> BetaAt(vb,vc,0,v)",
    "adjacent":"forall "+" ".join(PARAMETERS)+". ~p=0 -> ("+MONOMIALS+") -> "+ADJACENT,
}
HELPER_TARGET_SHA256 = {
    "head":"68ae142297fe18fd15d8085f2d335fac86be90f25c6bb1fe9c37b057aea03e6a",
    "adjacent":"27efb6cef7fad1cab6c2a7c66aa46618c7c188c11f56e9b8fc046b2a46189a14",
}
ARCHIVES = (COMPOSITION_ARCHIVE,GEOMETRIC_ARCHIVE,RECURRENCE_ARCHIVE)
ENDPOINT_SOURCES = {
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "power_exists":"forall d n. exists p. Pow(d,n,p)",
    "power_zero":"forall d n p. n=0 -> Pow(d,n,p) -> p=1",
    "power_step":"forall d n sn p. sn=S n -> Pow(d,sn,p) -> exists q. Pow(d,n,q) /\\ p=q*d",
    "power_nonzero":GEOMETRIC_HELPERS["power_nonzero"],
    "mul_cancel":"forall a b c. ~a=0 -> a*b=a*c -> b=c",
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "one_mul":"forall a. 1*a=a","mul_one":"forall a. a*1=a",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(power_nonzero="CV033",mul_cancel="CV002")
HELPER_DEPENDENCIES = {
    "head":("beta_exists","power_exists","power_zero","one_mul","mul_one"),
    "adjacent":("power_exists","power_step","power_nonzero","mul_cancel","le_refl","le_succ","le_trans","mul_assoc","mul_comm"),
    "CV072":("head","adjacent"),
}


class MonomialRecurrenceError(ValueError):
    """Changed actual row values, common scale or guarded recurrence."""


def frozen_monomial_recurrence_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or len(premises)!=2 or type(conclusion) is not And or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise MonomialRecurrenceError("CV072 exact scaled monomial recurrence changed")
    return target


def source_contract():
    return dict(code="CV072",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,nonzero_scale_required=True,exact_CV061_monomial_premise=True,
        same_decoded_row_values=True,nonempty_head_value="v",adjacent_recurrence="p*z=(t*x)*y",
        actual_power_nonvanishing_and_guarded_cancellation=True,zero_argument_and_base_allowed=True,
        empty_prefix_allowed=True,new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",actual_composition_constructed=False,
        finite_sum_bound_claimed=False,analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def monomial_recurrence_source_pins():
    result = scaled_exp_terms_source_pins()
    expected = {"scripts/sqrt2_power_scaled_exp_terms.py":"329c4e741b144823db7d43c018756dd19033aa5beca1505b5f4d05ae7cbe316a",
        "scripts/sqrt2_power_full_composition_evaluation.py":"1f072083655a535b2116b2e6f7dcac7c5459fb83e15899b485347b456bb6f544",
        "scripts/sqrt2_power_geometric_horner.py":"6179fa42c4437ed53db78fdc4f806d281d4774b58544150c7007dcfa3b656adc",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_monomial_recurrence.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise MonomialRecurrenceError("monomial recurrence source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _head(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(u):
        p,t,x,v,y,a,b,c = u.terms(("p","t","x","v","y","a","b","c"))
        one = Succ(Zero())
        ae = apply(specialize(u,"power_zero",p,Zero(),a),EqRefl(Zero()),u.hyp("p_power"))
        be = apply(specialize(u,"power_zero",t,Zero(),b),EqRefl(Zero()),u.hyp("t_power"))
        ce = apply(specialize(u,"power_zero",x,Zero(),c),EqRefl(Zero()),u.hyp("x_power"))
        law = apply(specialize(u,"monomials",Zero(),y,a,b,c),u.hyp("bound"),u.hyp("entry"),u.hyp("p_power"),u.hyp("t_power"),u.hyp("x_power"))
        eq = _chain(EqSym(specialize(u,"one_mul",y)),EqSym(CongMul(ae,EqRefl(y))),law,
            CongMul(CongMul(EqRefl(v),be),ce),CongMul(specialize(u,"mul_one",v),EqRefl(one)),specialize(u,"mul_one",v))
        return _subst(u,registry,"BetaAt(vb,vc,0,slot)",eq,u.hyp("entry"))
    return introduce(s,PARAMETERS,("monomials","bound"),lambda u:
        eliminate(u,specialize(u,"beta_exists",*u.terms(V),Zero()),("y",),"entry",lambda z:
            eliminate(z,specialize(z,"power_exists",z.term("p"),Zero()),("a",),"p_power",lambda a:
                eliminate(a,specialize(a,"power_exists",a.term("t"),Zero()),("b",),"t_power",lambda b:
                    eliminate(b,specialize(b,"power_exists",b.term("x"),Zero()),("c",),"x_power",chosen)))))


def _adjacent(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def entry(u):
        def chosen(z):
            p,t,x,v,k,y,w,a,b,c = z.terms(("p","t","x","v","k","y","z","a","b","c"))
            ap,bp,cp = z.terms(("ap","bp","cp"));sk = Succ(k)
            kb = apply(specialize(z,"le_trans",sk,Succ(sk),z.term("K")),
                apply(specialize(z,"le_succ",sk,sk),specialize(z,"le_refl",sk)),z.hyp("bound"))
            old = apply(specialize(z,"monomials",k,y,a,b,c),kb,z.hyp("entry_y"),
                AndElimL(z.hyp("p_data")),AndElimL(z.hyp("t_data")),AndElimL(z.hyp("x_data")))
            new = apply(specialize(z,"monomials",sk,w,ap,bp,cp),z.hyp("bound"),z.hyp("entry_z"),
                z.hyp("p_next"),z.hyp("t_next"),z.hyp("x_next"))
            left,right = Mul(p,w),Mul(Mul(t,x),y)
            eq = _chain(_multiplicative_equal(z,Mul(a,left),Mul(Mul(a,p),w)),
                EqSym(CongMul(AndElimR(z.hyp("p_data")),EqRefl(w))),new,
                CongMul(CongMul(EqRefl(v),AndElimR(z.hyp("t_data"))),AndElimR(z.hyp("x_data"))),
                _multiplicative_equal(z,Mul(Mul(v,Mul(b,t)),Mul(c,x)),Mul(Mul(t,x),Mul(Mul(v,b),c))),
                CongMul(EqRefl(Mul(t,x)),EqSym(old)),
                _multiplicative_equal(z,Mul(Mul(t,x),Mul(a,y)),Mul(a,right)))
            nz = apply(instantiate(apply(specialize(z,"power_nonzero",p),z.hyp("nonzero_p")),k,a),AndElimL(z.hyp("p_data")))
            return apply(specialize(z,"mul_cancel",a,left,right),nz,eq)
        def choose_power(z,base,next_name,old_name,label,finish):
            return eliminate(z,specialize(z,"power_exists",z.term(base),Succ(z.term("k"))),(next_name,),label+"_next",lambda a:
                eliminate(a,apply(specialize(a,"power_step",a.term(base),a.term("k"),Succ(a.term("k")),a.term(next_name)),
                    EqRefl(Succ(a.term("k"))),a.hyp(label+"_next")),(old_name,),label+"_data",finish))
        return choose_power(u,"p","ap","a","p",lambda a:
            choose_power(a,"t","bp","b","t",lambda b:
                choose_power(b,"x","cp","c","x",chosen)))
    return introduce(s,PARAMETERS,("nonzero_p","monomials"),lambda u:
        introduce(u,("k","y","z"),("bound","entry_y","entry_z"),entry))


def _root(s):
    from peano_lab.kernel.proofs import ImpIntro
    def finish(u):
        v = u.hypothesis("head_bound")
        head = ImpIntro(apply(specialize(v,"head",*v.terms(PARAMETERS)),v.hyp("monomials"),v.hyp("head_bound")))
        adjacent = apply(specialize(u,"adjacent",*u.terms(PARAMETERS)),u.hyp("nonzero_p"),u.hyp("monomials"))
        return conjunction(head,adjacent)
    return introduce(s,PARAMETERS,("nonzero_p","monomials"),finish)


def prove_monomial_recurrence(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV072",target=frozen_monomial_recurrence_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"head":lambda s:_head(s,registry),"adjacent":_adjacent,"CV072":_root},
        pins=monomial_recurrence_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
