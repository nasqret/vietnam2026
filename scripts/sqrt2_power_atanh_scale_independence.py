"""CV092: supplied finite atanh values are independent of coefficient scaling.

Two independently coded coefficient tables and supplied Horner histories
give e*x=d*y. Only an odd coefficient index is cancelled, after proving it
nonzero. Zero scales, zero base and empty prefixes are allowed in this natural
identity; rational validity and analytic convergence are separate obligations.
"""
from hashlib import sha256

from sqrt2_power_atanh_truncation import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,atanh_truncation_source_pins,
)
from sqrt2_power_atanh_euler import HELPER_SOURCES as PARITY_HELPERS
from sqrt2_power_horner_linearity import (
    HELPER_SOURCES as LINEAR_HELPERS,horner_linearity_source_pins,
)
from sqrt2_power_logexp_recurrence import logexp_recurrence_source_pins
from sqrt2_power_composition_recurrence import ATANH_EULER_ARCHIVE,RECURRENCE_ARCHIVE
from sqrt2_power_weighted_accumulation_evaluation import LINEAR_ARCHIVE
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-atanh-scale-independence-v1"
A,B,HA,HB=("ab","ac"),("bb","bc"),("ahb","ahc"),("bhb","bhc")
FIXED=("d","e")+A+B+("N",)
PARAMETERS=FIXED+("t","x","y")
PREFIX_A="NatAtanhPrefix(d,ab,ac,N)"
PREFIX_B="NatAtanhPrefix(e,bb,bc,N)"
GRAPH="NatLinearTriple(e,0,d,ab,ac,ab,ac,bb,bc,N)"
NAMED_SOURCE="forall "+" ".join(PARAMETERS)+". "+PREFIX_A+" -> "+PREFIX_B+" -> NatHornerValue(ab,ac,t,N,x) -> NatHornerValue(bb,bc,t,N,y) -> e*x=d*y"
TARGET_SHA256="5b80b161ea46bbe0cbcdef8789de98218d6c1dfc077ff0023320f077fe3d8bc1"
HELPER_SOURCES={
    "coefficient_cross":"forall d e i a b. NatAtanhCoefficient(d,i,a) -> NatAtanhCoefficient(e,i,b) -> e*a=d*b",
    "linear_graph":"forall "+" ".join(FIXED)+". "+PREFIX_A+" -> "+PREFIX_B+" -> "+GRAPH,
}
HELPER_TARGET_SHA256={"coefficient_cross":"7534144c13032f101d9149c5ecf41d561187519962373a22651e7299ec17ce48",
    "linear_graph":"fd99647d655b5a473e45fc81cf8fda5ba7c2cd47b5f5ba1c435a9061c0c62433"}
ARCHIVES=(ATANH_EULER_ARCHIVE,LINEAR_ARCHIVE,RECURRENCE_ARCHIVE)
ENDPOINT_SOURCES={
    "even_not_odd":PARITY_HELPERS["even_not_odd"],"horner_linear":LINEAR_HELPERS["all_rows"],
    "mul_cancel":"forall a b c. ~a=0 -> a*b=a*c -> b=c",
    "succ_ne_zero":"forall a. ~S a=0","mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
    "mul_comm":"forall a b. a*b=b*a","zero_mul":"forall a. 0*a=0",
    "le_refl":"forall a. Le(a,a)",
}
ENDPOINT_OWNERS={name:"CV026" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(horner_linear="CV035",mul_cancel="CV002")
HELPER_DEPENDENCIES={
    "coefficient_cross":("even_not_odd","mul_cancel","succ_ne_zero","mul_assoc","mul_comm"),
    "linear_graph":("coefficient_cross","zero_mul"),
    "CV092":("linear_graph","horner_linear","le_refl","zero_mul"),
}


class AtanhScaleIndependenceError(ValueError):
    """Changed supplied coefficient/history data or exact cross identity."""


def frozen_atanh_scale_independence_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=10 or len(premises)!=4 or type(conclusion) is not Eq or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise AtanhScaleIndependenceError("CV092 exact independent-table scaling changed")
    return target


def source_contract():
    return dict(code="CV092",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,two_actual_atanh_prefixes_required=True,two_supplied_horner_values_preserved=True,
        independent_coefficient_and_history_codes_allowed=True,exact_identity="e*x=d*y",
        zero_scales_base_and_empty_prefix_allowed=True,only_proved_nonzero_odd_index_cancelled=True,
        all_row_linearity_reused=True,code_number_equality_claimed=False,
        rational_denominator_validity_claimed=False,analytic_limit_claim=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def atanh_scale_independence_source_pins():
    result=atanh_truncation_source_pins()
    for pins in (horner_linearity_source_pins(),logexp_recurrence_source_pins()):
        for name,pin in pins.items():
            if name in result and result[name]!=pin:
                raise AtanhScaleIndependenceError("independent-scale source disagreement")
            result[name]=pin
    expected={
        "scripts/sqrt2_power_atanh_truncation.py":"6d9366b12889d5eb98f47827f7e9ac216e57ed8b46300d16dde078ad51a6f4c7",
        "scripts/sqrt2_power_atanh_euler.py":"d24e8fc4fcf12b22f2971877ab3bb55be42991b6b9a34938d99e97920d4cffe2",
        "scripts/sqrt2_power_horner_linearity.py":"914a08b5ebdf667c247330ca79d99e81956ff47a3c0c77195435ae8cc2113618",
        "scripts/sqrt2_power_composition_recurrence.py":"8989d3b556c1b00602e75b34807a98b5d730864271edfacf329c6898863f9547",
        "scripts/sqrt2_power_weighted_accumulation_evaluation.py":"464f6bf6c392132d50a3eeeea49554d51e15763ed064908c3bd4d4993d36e0fd",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_atanh_scale_independence.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise AtanhScaleIndependenceError("independent-scale source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _coefficient_cross(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,BotElim,CongMul,EqRefl,EqSym,OrElim
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()))
    def decoded(t,odd_a,odd_b):
        d,e,i,a,b,ja,jb=t.terms(("d","e","i","a","b","ja","jb"))
        ad,bd=t.hyp("a_data"),t.hyp("b_data")
        if odd_a!=odd_b:
            left,right=(jb,ja) if odd_a else (ja,jb)
            equality=_chain(EqSym(AndElimL(bd)),AndElimL(ad)) if odd_a else _chain(EqSym(AndElimL(ad)),AndElimL(bd))
            return BotElim(apply(specialize(t,"even_not_odd",left,right),equality))
        if not odd_a:
            return _chain(CongMul(EqRefl(e),AndElimR(ad)),instantiate(Axiom("PA5"),e),
                EqSym(instantiate(Axiom("PA5"),d)),CongMul(EqRefl(d),EqSym(AndElimR(bd))))
        nonzero=_subst(t,registry,"~slot=0",EqSym(AndElimL(ad)),specialize(t,"succ_ne_zero",Mul(two,ja)))
        equality=_chain(_multiplicative_equal(t,Mul(i,Mul(e,a)),Mul(e,Mul(i,a))),
            CongMul(EqRefl(e),AndElimR(ad)),
            _multiplicative_equal(t,Mul(e,Mul(two,d)),Mul(d,Mul(two,e))),
            CongMul(EqRefl(d),EqSym(AndElimR(bd))),
            _multiplicative_equal(t,Mul(d,Mul(i,b)),Mul(i,Mul(d,b))))
        return apply(specialize(t,"mul_cancel",i,Mul(e,a),Mul(d,b)),nonzero,equality)
    def b_case(t,odd_a,odd_b):
        return eliminate(t,t.hyp("b_case"),("jb",),"b_data",lambda u:decoded(u,odd_a,odd_b))
    def a_case(t,odd_a):
        return eliminate(t,t.hyp("a_case"),("ja",),"a_data",lambda u:
            OrElim(u.hyp("coefficient_b"),b_case(u.hypothesis("b_case"),odd_a,False),b_case(u.hypothesis("b_case"),odd_a,True)))
    return introduce(s,("d","e","i","a","b"),("coefficient_a","coefficient_b"),lambda t:
        OrElim(t.hyp("coefficient_a"),a_case(t.hypothesis("a_case"),False),a_case(t.hypothesis("a_case"),True)))


def _linear_graph(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul
    def coefficient(t):
        i,a,c=t.terms(("i","a","c"))
        ca=apply(specialize(t,"prefix_a",i,a),t.hyp("bound"),t.hyp("entry_a"))
        cb=apply(specialize(t,"prefix_b",i,c),t.hyp("bound"),t.hyp("entry_b"))
        cross=apply(specialize(t,"coefficient_cross",*t.terms(("d","e","i","a","c"))),ca,cb)
        ea=Mul(t.term("e"),a)
        return _chain(EqSym(cross),EqSym(instantiate(Axiom("PA3"),ea)),
            CongAdd(EqRefl(ea),EqSym(specialize(t,"zero_mul",t.term("b")))))
    return introduce(s,FIXED,("prefix_a","prefix_b"),lambda t:
        introduce(t,("i","a","b","c"),("bound","entry_a","unused_entry_a","entry_b"),coefficient))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Zero
    def chosen(t):
        d,e,N,base,x,y=t.terms(("d","e","N","t","x","y"))
        graph=apply(specialize(t,"linear_graph",*t.terms(FIXED)),t.hyp("prefix_a"),t.hyp("prefix_b"))
        ha,hb=t.hyp("history_a"),t.hyp("history_b")
        arguments=(e,Zero(),d)+t.terms(A+A+B)+(base,N)+t.terms(HA+HA+HB)
        rows=apply(specialize(t,"horner_linear",*arguments),graph,AndElimL(ha),AndElimL(ha),AndElimL(hb))
        endpoint=apply(instantiate(rows,N,x,x,y),specialize(t,"le_refl",N),AndElimR(ha),AndElimR(ha),AndElimR(hb))
        return EqSym(_chain(endpoint,CongAdd(EqRefl(Mul(e,x)),specialize(t,"zero_mul",x)),instantiate(Axiom("PA3"),Mul(e,x))))
    return introduce(s,PARAMETERS,("prefix_a","prefix_b","value_a","value_b"),lambda t:
        eliminate(t,t.hyp("value_a"),HA,"history_a",lambda u:
            eliminate(u,u.hyp("value_b"),HB,"history_b",chosen)))


def prove_atanh_scale_independence(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="CV092",target=frozen_atanh_scale_independence_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"coefficient_cross":lambda s:_coefficient_cross(s,registry),"linear_graph":_linear_graph,"CV092":_root},
        pins=atanh_scale_independence_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
