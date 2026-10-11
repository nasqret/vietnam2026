"""CV067: actual factorials dominate the geometric tail denominator.

For every k construct f=(k+2)! and p=3^k with 2*p<=f. The proof keeps
actual factorial and power graphs and has no rational or analytic premise.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_atanh_majorant import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as previous_registry,atanh_majorant_source_pins,
)
from sqrt2_power_weight_factorials import (
    definition_registry as factorial_registry,weight_factorials_source_pins,
    ENDPOINT_SOURCES as FACTORIAL_ENDPOINTS,
)
from sqrt2_power_normalized_composition import FACTORIAL_ARCHIVE
from sqrt2_power_horner_tail_majorant import COMPARISON_ARCHIVE
from sqrt2_power_horner_base_comparison import HELPER_SOURCES as COMPARISON_HELPERS
from sqrt2_power_finite_power_evaluation import _multiplicative_equal
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-factorial-majorant-v1"
NAMED_SOURCE = "forall k. exists f p. Factorial(S(S k),f) /\\ (Pow(3,k,p) /\\ Le(2*p,f))"
TARGET_SHA256 = "906291d44d802e2ac53f432d1d7ae6b05c1920dda811c18335f095def75f9293"
HELPER_SOURCES = {
    "factorial_two":"forall f. Factorial(2,f) -> f=2",
    "all_values":"forall k f p. Factorial(S(S k),f) -> Pow(3,k,p) -> Le(2*p,f)",
}
HELPER_TARGET_SHA256 = {
    "factorial_two":"e8d5b9735603e1e3eead399357516714df90bf3f163480f9ca00766dc3a33a32",
    "all_values":"4e14a5e7450ec5e5742d27a36c841e39a864e9ea85ba6f729bb8b5a3b712da3e",
}
ARCHIVES = (FACTORIAL_ARCHIVE,COMPARISON_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:FACTORIAL_ENDPOINTS[name] for name in ("factorial_exists","factorial_zero","factorial_step","power_exists","power_zero","power_step","one_mul","mul_one","mul_assoc","mul_comm","le_refl","le_trans")},
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "mul_left_mono":COMPARISON_HELPERS["mul_left_mono"],
}
ENDPOINT_OWNERS = {name:"CV030" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(mul_right_mono="CV063",mul_left_mono="CV063")
HELPER_DEPENDENCIES = {
    "factorial_two":("factorial_step","factorial_zero","mul_one","one_mul"),
    "all_values":("factorial_two","power_zero","mul_one","le_refl","factorial_step","power_step","mul_right_mono","mul_left_mono","le_trans","mul_assoc","mul_comm"),
    "CV067":("factorial_exists","power_exists","all_values"),
}


class FactorialMajorantError(ValueError):
    """Changed factorial offset, exponential base or actual computation."""


def definition_registry():
    result = dict(previous_registry())
    for name,d in factorial_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise FactorialMajorantError("shared factorial definition mismatch")
        if name not in result and d.stable_id in {v.stable_id for v in result.values()}:
            raise FactorialMajorantError("cross-registry definition id collision")
        result[name] = d
    return MappingProxyType(result)


def frozen_factorial_majorant_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FactorialMajorantError("CV067 exact factorial lower bound target changed")
    return target


def source_contract():
    return dict(code="CV067",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_factorial_and_power_constructed=True,
        factorial_index="k+2",power="3^k",inequality="2*p<=f",arbitrary_supplied_values_helper=True,
        no_division=True,new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",analytic_limit_claim=False,finite_exp_sum_bound_claimed=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def factorial_majorant_source_pins():
    result = atanh_majorant_source_pins()
    for name,pin in weight_factorials_source_pins().items():
        if name in result and result[name]!=pin:
            raise FactorialMajorantError("source pin disagreement")
        result[name] = pin
    expected = {"scripts/sqrt2_power_atanh_majorant.py":"994b47e03f8b9021bef219df7f91270ad2d790f91d788be62d7839d9afdf419e",
        "scripts/sqrt2_power_weight_factorials.py":"cabf5acbe76204dc59c64130a45172440713577d2859f1672635d3a4cf6aacd7",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_factorial_majorant.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise FactorialMajorantError("factorial majorant source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _factorial_two(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl
    from peano_lab.kernel.terms import Succ,Zero
    one,two = Succ(Zero()),Succ(Succ(Zero()))
    def chosen(t):
        h1 = apply(specialize(t,"factorial_zero",Zero(),t.term("h")),EqRefl(Zero()),AndElimL(t.hyp("second")))
        g1 = _chain(AndElimR(t.hyp("second")),specialize(t,"mul_one",t.term("h")),h1)
        return _chain(AndElimR(t.hyp("first")),CongMul(g1,EqRefl(two)),specialize(t,"one_mul",two))
    return introduce(s,("f",),("factorial",),lambda t:
        eliminate(t,apply(specialize(t,"factorial_step",one,two,t.term("f")),EqRefl(two),t.hyp("factorial")),("g",),"first",lambda u:
            eliminate(u,apply(specialize(u,"factorial_step",Zero(),one,u.term("g")),EqRefl(one),AndElimL(u.hyp("first"))),("h",),"second",chosen)))


def _all_values(s,target,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongMul,CongS,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    zero = Zero();one = Succ(zero);two = Succ(one);three = Succ(two)
    def base(t):
        f,p = t.terms(("f","p"))
        f2 = apply(specialize(t,"factorial_two",f),t.hyp("factorial"))
        p1 = apply(specialize(t,"power_zero",three,zero,p),EqRefl(zero),t.hyp("power"))
        equal = _chain(CongMul(EqRefl(two),p1),specialize(t,"mul_one",two),EqSym(f2))
        return _subst(t,registry,"Le(2*p,slot)",equal,specialize(t,"le_refl",Mul(two,p)))
    def successor(t):
        def chosen(u):
            k,g,q,f,p = u.terms(("k","g","q","f","p"));next_index = Succ(Succ(Succ(k)))
            old = apply(specialize(u,"IH",g,q),AndElimL(u.hyp("factorial_data")),AndElimL(u.hyp("power_data")))
            first = apply(specialize(u,"mul_right_mono",Mul(two,q),g,three),old)
            gap = _chain(instantiate(Axiom("PA4"),k,two),CongS(instantiate(Axiom("PA4"),k,one)),
                CongS(CongS(instantiate(Axiom("PA4"),k,zero))),CongS(CongS(CongS(instantiate(Axiom("PA3"),k)))))
            second = apply(specialize(u,"mul_left_mono",three,next_index,g),witness((k,),gap))
            bound = apply(specialize(u,"le_trans",Mul(Mul(two,q),three),Mul(g,three),Mul(g,next_index)),first,second)
            lhs = _chain(CongMul(EqRefl(two),AndElimR(u.hyp("power_data"))),
                _multiplicative_equal(u,Mul(two,Mul(q,three)),Mul(Mul(two,q),three)))
            bound = _subst(u,registry,"Le(slot,g*S(S(S k)))",EqSym(lhs),bound)
            return _subst(u,registry,"Le(2*p,slot)",EqSym(AndElimR(u.hyp("factorial_data"))),bound)
        old_index = Succ(Succ(t.term("k")));next_index = Succ(old_index)
        return eliminate(t,apply(specialize(t,"factorial_step",old_index,next_index,t.term("f")),EqRefl(next_index),t.hyp("factorial")),("g",),"factorial_data",lambda u:
            eliminate(u,apply(specialize(u,"power_step",three,u.term("k"),Succ(u.term("k")),u.term("p")),EqRefl(Succ(u.term("k"))),u.hyp("power")),("q",),"power_data",chosen))
    motive = target.body
    return Ind(motive,introduce(s,("f","p"),("factorial","power"),base),
        introduce(s,("k",),("IH",),lambda t:introduce(t,("f","p"),("factorial","power"),successor)))


def _root(s):
    from peano_lab.kernel.terms import Succ,Zero
    def chosen(t):
        bound = apply(specialize(t,"all_values",*t.terms(("k","f","p"))),t.hyp("factorial"),t.hyp("power"))
        return witness(t.terms(("f","p")),conjunction(t.hyp("factorial"),t.hyp("power"),bound))
    return introduce(s,("k",),(),lambda t:
        eliminate(t,specialize(t,"factorial_exists",Succ(Succ(t.term("k")))),("f",),"factorial",lambda u:
            eliminate(u,specialize(u,"power_exists",Succ(Succ(Succ(Zero()))),u.term("k")),("p",),"power",chosen)))


def prove_factorial_majorant(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV067",target=frozen_factorial_majorant_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"factorial_two":_factorial_two,
            "all_values":lambda s:_all_values(s,parse_named(HELPER_SOURCES["all_values"],registry=registry),registry),"CV067":_root},
        pins=factorial_majorant_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
