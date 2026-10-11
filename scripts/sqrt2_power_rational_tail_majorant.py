"""CV075: actual finite omitted-tail bound in valid rational order.

From a base-two whole-table majorant y<=(B*D)*2^(M+r), D!=0,
construct the tail after M and certify tail(1/3)/D <= B*(2/3)^M.
All powers and denominators are actual arithmetic data. No limit is used.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_composition_majorant import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as base_registry,composition_majorant_source_pins,
    COMPOSITION_ARCHIVE,BOUND_ARCHIVE,WEIGHTED_ARCHIVE,conjoin,
)
from sqrt2_power_horner_tail_majorant import NAMED_SOURCE as TAIL_SOURCE
from sqrt2_power_scaled_exp_bound import HELPER_SOURCES as BOUND_HELPERS
from sqrt2_power_geometric_horner import HELPER_SOURCES as GEOMETRIC_HELPERS
from sqrt2_power_row_horner_values import HELPER_SOURCES as ROW_HELPERS
from sqrt2_power_convolution_weights import ENDPOINT_SOURCES as POWER_ENDPOINTS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-rational-tail-majorant-v1"
A,T = ("ab","ac"),("tb","tc")
PARAMETERS = A+("D","B","M","r","y","v")
OUTPUTS = T+("u","p","q","h")
TAIL_OUTPUTS = T+("u","w","a","b")
DEFINITIONS = (
    ("ND0444","IRatLe",("p","m","d","P","M","D"),
     "IRatValid(p,m,d) /\\ (IRatValid(P,M,D) /\\ Le(p*D+M*d,m*D+P*d))",
     ("IRatValid","Le"),"4f2c5a223cacf41df91ce383d1d5c5e498d6ed0602375998eb52a1104e3bdced"),
)
PARTS = ("NatAffineSlice(ab,ac,M,1,tb,tc,S r)","NatHornerValue(tb,tc,3,S r,u)",
    "Pow(2,M,p)","Pow(3,M,q)","Pow(3,M+r,h)","~p=0","~q=0","~h=0","~(D*h)=0",
    "Le(u*q,(B*p)*(D*h))","IRatLe(u,0,D*h,B*p,0,q)")
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". ~D=0 -> NatHornerValue(ab,ac,2,S(M+r),y) -> Pow(2,M+r,v) -> Le(y,(B*D)*v) -> exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256 = "afeaa7ea69229597287202c3420e527d2b96f2c2bbd77a455ad620d128c7edff"
HELPER_SOURCES = {
    "positive_order":"forall u v a b. ~a=0 -> ~b=0 -> Le(u*b,v*a) -> IRatLe(u,0,a,v,0,b)",
    "cross_bound":"forall a b D B v p q h u y. ~a=0 -> Le(a*u,b*y) -> Le(y,(B*D)*v) -> v=p*a -> h=q*b -> Le(u*q,(B*p)*(D*h))",
}
HELPER_TARGET_SHA256 = {
    "positive_order":"123f28171cc7bc83426cfc2f25b38593b87b685ddb730b48c702d5eda0ed2f4a",
    "cross_bound":"f95c6e9d9950046d2e87cd33f5396f7a68cc6115faa000b523325c11e6bc73f6",
}
TAIL_ARCHIVE = dict(case="CV064",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-tail-majorant-v1/generation-process.json.gz",
    bytes=32399,sha256="2eb95852e1754c0996c57cadece728c08e2d68140eb4000c166846cdd9b159b2",
    raw_bytes=540306,raw_sha256="912a1f452314c6c8bfe1fc986ca38fdf3070c7e4d605ade0a51e10c1fed62079",
    bundle_bytes=305518,bundle_sha256="19b994fd3a6014407807961c23e963367e51814be7a6231a0e0fd337f8eb7d0f",
    nodes=132,root=131,target_ast_sha256="adec9c34b4e9fd8be3a611ebe168b24c3cfbd3ca6d6b96568180e2849705609f")
ARCHIVES = (COMPOSITION_ARCHIVE,TAIL_ARCHIVE,BOUND_ARCHIVE,WEIGHTED_ARCHIVE)
ENDPOINT_SOURCES = {
    "tail_exists":TAIL_SOURCE,"value_unique":ROW_HELPERS["value_unique"],
    "power_exists":"forall d n. exists p. Pow(d,n,p)","power_add":POWER_ENDPOINTS["power_add"],
    "power_nonzero":GEOMETRIC_HELPERS["power_nonzero"],
    "mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
    "succ_ne_zero":"forall a. ~S a=0","le_refl":"forall a. Le(a,a)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "mul_le_cancel":BOUND_HELPERS["mul_le_cancel"],
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "zero_mul":"forall a. 0*a=0","zero_add":"forall a. 0+a=a",
}
ENDPOINT_OWNERS = {name:"CV061" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(tail_exists="CV064",mul_left_mono="CV071",mul_le_cancel="CV071",power_nonzero="CV073")
HELPER_DEPENDENCIES = {
    "positive_order":("zero_mul","zero_add"),
    "cross_bound":("mul_left_mono","mul_right_mono","le_trans","mul_le_cancel","mul_assoc","mul_comm"),
    "CV075":("tail_exists","value_unique","power_exists","power_add","power_nonzero","mul_ne_zero",
        "succ_ne_zero","le_refl","le_succ","cross_bound","positive_order"),
}


class RationalTailMajorantError(ValueError):
    """Changed valid rational order, finite tail or denominator factors."""


def definition_registry():
    from sqrt2_power_definitions import parse_named,PARENT,DEFINITIONS as RATIONAL_DEFINITIONS
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    result = dict(base_registry())
    validity = RATIONAL_DEFINITIONS["IRatValid"]
    if ("IRatValid" in result and result["IRatValid"]!=validity or
            "IRatValid" not in result and validity.stable_id in {d.stable_id for d in result.values()}):
        raise RationalTailMajorantError("rational validity identity collision")
    result["IRatValid"] = validity
    parent = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids = {d["id"] for d in parent}|{d.stable_id for d in result.values()}
    names = {d["name"] for d in parent}|set(result)
    for identifier,name,params,source,deps,digest in DEFINITIONS:
        if identifier in ids or name in names or not set(deps)<=result.keys():
            raise RationalTailMajorantError("rational order definition collision or forward dependency")
        formula = parse_named(source,params,result)
        if json_hash(encode_formula(formula))!=digest:
            raise RationalTailMajorantError("rational order conservative expansion changed")
        text = pretty_formula(formula,list(params))
        d = _definition(stable_id=identifier,name=name,parameters=params,template_source=text,
            summary="Valid signed rational non-strict order via an exact natural cross-product gap.",
            category="irrationality_rationals",conceptual_dependencies=deps)
        if d.template_formula!=formula or parse_formula_in_context(text,list(params))!=formula:
            raise RationalTailMajorantError("rational order failed exact conservative roundtrip")
        result[name] = d;ids.add(identifier);names.add(name)
    return MappingProxyType(result)


def frozen_rational_tail_majorant_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=8 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise RationalTailMajorantError("CV075 exact finite rational tail estimate changed")
    return target


def source_contract():
    return dict(code="CV075",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,nonzero_normalization_required=True,whole_table_majorant_required=True,
        actual_tail_and_base_three_value_constructed=True,actual_powers_and_nonzero_denominators_constructed=True,
        cutoff="M",tail_length="r+1",whole_length="M+r+1",whole_bound="y<=(B*D)*2^(M+r)",
        rational_bound="u/(D*3^(M+r)) <= B*2^M/3^M",zero_bound_and_zero_cutoff_allowed=True,
        rational_division_transport_proved=True,new_definition_ids=["ND0444"],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        actual_composition_constructed=False,empty_tail_case_claimed=False,analytic_limit_claim=False,
        closes_IR072=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def rational_tail_majorant_source_pins():
    result = composition_majorant_source_pins()
    expected = {"scripts/sqrt2_power_composition_majorant.py":"6ddac1c4c4d11addb4cf7f110eb9d6ad2b8aa0371d8caecd05b3b47cca256aca",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_rational_tail_majorant.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise RationalTailMajorantError("rational tail source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _positive_order(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Zero
    def finish(t):
        u,v,a,b = t.terms(("u","v","a","b"));ub,va = Mul(u,b),Mul(v,a)
        left = _chain(CongAdd(EqRefl(ub),specialize(t,"zero_mul",a)),instantiate(Axiom("PA3"),ub))
        right = _chain(CongAdd(specialize(t,"zero_mul",b),EqRefl(va)),specialize(t,"zero_add",va))
        bound = _subst(t,registry,"Le(slot,v*a)",EqSym(left),t.hyp("bound"))
        bound = _subst(t,registry,"Le(u*b+0*a,slot)",EqSym(right),bound)
        return conjunction(t.hyp("left_valid"),t.hyp("right_valid"),bound)
    return introduce(s,("u","v","a","b"),("left_valid","right_valid","bound"),finish)


def _cross_bound(s,registry):
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def finish(t):
        a,b,D,B,v,p,q,h,u,y = t.terms(("a","b","D","B","v","p","q","h","u","y"))
        BD = Mul(B,D);C = Mul(Mul(BD,p),b)
        lifted = apply(specialize(t,"mul_left_mono",y,Mul(BD,v),b),t.hyp("whole_bound"))
        bound = apply(specialize(t,"le_trans",Mul(a,u),Mul(b,y),Mul(b,Mul(BD,v))),t.hyp("tail_bound"),lifted)
        equal = _chain(CongMul(EqRefl(b),CongMul(EqRefl(BD),t.hyp("power_two"))),
            _multiplicative_equal(t,Mul(b,Mul(BD,Mul(p,a))),Mul(a,C)))
        bound = _subst(t,registry,"Le(a*u,slot)",equal,bound)
        bound = apply(specialize(t,"mul_le_cancel",a,u,C),t.hyp("nonzero"),bound)
        bound = apply(specialize(t,"mul_right_mono",u,C,q),bound)
        equal = _chain(_multiplicative_equal(t,Mul(C,q),Mul(Mul(B,p),Mul(D,Mul(q,b)))),
            CongMul(EqRefl(Mul(B,p)),CongMul(EqRefl(D),EqSym(t.hyp("power_three")))))
        return _subst(t,registry,"Le(u*q,slot)",equal,bound)
    return introduce(s,("a","b","D","B","v","p","q","h","u","y"),
        ("nonzero","tail_bound","whole_bound","power_two","power_three"),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,EqRefl
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two = Succ(Succ(Zero()));three = Succ(two)
    def chosen(t):
        D,B,M,r,y,v,u,p,q,h,a,b = t.terms(("D","B","M","r","y","v","u","p","q","h","a","b"));Mr = Add(M,r)
        data = t.hyp("tail")
        whole = _subst(t,registry,"NatHornerValue(ab,ac,2,slot,w)",instantiate(Axiom("PA4"),M,r),field(data,2,6))
        same = apply(specialize(t,"value_unique",*t.terms(A),two,Succ(Mr),t.term("w"),y),whole,t.hyp("whole_value"))
        bound = _subst(t,registry,"Le(a*u,b*slot)",same,field(data,5,6))
        peq = apply(specialize(t,"power_add",two,M,r,Mr,p,a,v),EqRefl(Mr),t.hyp("power_p"),field(data,3,6),t.hyp("whole_power"))
        heq = apply(specialize(t,"power_add",three,M,r,Mr,q,b,h),EqRefl(Mr),t.hyp("power_q"),field(data,4,6),t.hyp("power_h"))
        def power_nonzero(base,exponent,value,proof):
            nz = specialize(t,"succ_ne_zero",base.term)
            return apply(instantiate(apply(specialize(t,"power_nonzero",base),nz),exponent,value),proof)
        an = power_nonzero(two,r,a,field(data,3,6));pn = power_nonzero(two,M,p,t.hyp("power_p"))
        qn = power_nonzero(three,M,q,t.hyp("power_q"));hn = power_nonzero(three,Mr,h,t.hyp("power_h"))
        dn = apply(specialize(t,"mul_ne_zero",D,h),t.hyp("denominator"),hn)
        bound = apply(specialize(t,"cross_bound",a,b,D,B,v,p,q,h,u,y),an,bound,t.hyp("majorant"),peq,heq)
        rational = apply(specialize(t,"positive_order",u,Mul(B,p),Mul(D,h),q),dn,qn,bound)
        return witness(t.terms(OUTPUTS),conjunction(field(data,0,6),field(data,1,6),t.hyp("power_p"),
            t.hyp("power_q"),t.hyp("power_h"),pn,qn,hn,dn,bound,rational))
    return introduce(s,PARAMETERS,("denominator","whole_value","whole_power","majorant"),lambda t:
        eliminate(t,apply(specialize(t,"tail_exists",*t.terms(A),two,three,*t.terms(("M","r"))),
            apply(specialize(t,"le_succ",two,two),specialize(t,"le_refl",two))),TAIL_OUTPUTS,"tail",lambda u:
            eliminate(u,specialize(u,"power_exists",two,u.term("M")),("p",),"power_p",lambda p:
                eliminate(p,specialize(p,"power_exists",three,p.term("M")),("q",),"power_q",lambda q:
                    eliminate(q,specialize(q,"power_exists",three,Add(*q.terms(("M","r")))),("h",),"power_h",chosen)))))


def prove_rational_tail_majorant(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV075",target=frozen_rational_tail_majorant_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"positive_order":lambda s:_positive_order(s,registry),"cross_bound":lambda s:_cross_bound(s,registry),"CV075":lambda s:_root(s,registry)},
        pins=rational_tail_majorant_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
