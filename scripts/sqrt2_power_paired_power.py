"""AP018: normalize actual odd powers to the paired squared base.

Two successive power decompositions at base t match one at base t*t.
The proof preserves both supplied computations and permits t=0 and k=0.
No cancellation, positivity premise or analytic exponent law is assumed.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_positive_power_comparison import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,BOUND_ARCHIVE,
    definition_registry as source_registry,positive_power_comparison_source_pins,
    ENDPOINT_SOURCES as POWER_ENDPOINTS,_chain,
)
from sqrt2_power_approximation_power_bounds import COMPARISON_ARCHIVE
from sqrt2_power_atanh_odd_slice import atanh_odd_slice_source_pins,ATANH_EULER_ARCHIVE
from sqrt2_power_quadratic_trace_exists import eliminate
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-paired-power-v1"
NAMED_SOURCE="forall t k x y. Pow(t,S(2*k),x) -> Pow(t*t,k,y) -> x=t*y"
TARGET_SHA256="1c4010443924fa4b57d39c7f9952916050880d32d433ee211b5b5cef8a1a4f0f"
HELPER_SOURCES={"even_power":"forall t k x y. Pow(t,2*k,x) -> Pow(t*t,k,y) -> x=y"}
HELPER_TARGET_SHA256={"even_power":"1f81f83f5d30e731d4fad44d198b09d8afe4e1f44eea3f937e86d876d6403a4f"}
ARCHIVES=(COMPARISON_ARCHIVE,ATANH_EULER_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={**{name:POWER_ENDPOINTS[name] for name in ("power_zero","power_step")},
    "double_succ":"forall j. 2*(S j)=S(S(2*j))",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a"}
ENDPOINT_OWNERS=dict(power_zero="AP010",power_step="AP010",double_succ="CV026",mul_assoc="CV071",mul_comm="CV071")
HELPER_DEPENDENCIES={"even_power":("power_zero","power_step","double_succ","mul_assoc"),
    "AP018":("even_power","power_step","mul_comm")}


class PairedPowerError(ValueError):
    """Changed supplied power graphs, doubled exponent or squared base."""


def definition_registry():
    source=source_registry();needed=set();pending=["Pow"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed}
    seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise PairedPowerError("paired-power conservative definition DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_paired_power_target(*,_registry=None):
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry() if _registry is None else _registry)
    binders,premises,conclusion=strip_target(target)
    if binders!=4 or len(premises)!=2 or type(conclusion) is not Eq or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PairedPowerError("AP018 exact paired-power target changed")
    return target


def source_contract():
    return dict(code="AP018",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,both_actual_supplied_power_graphs_preserved=True,paired_base="t*t",
        odd_exponent="S(2*k)",exact_identity="x=t*y",even_power_compared_by_explicit_induction=True,
        zero_base_and_zero_index_allowed=True,cancellation_used=False,positivity_premise_required=False,
        new_definition_ids=[],definition_admissions=0,new_induction_needed=True,
        analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def paired_power_source_pins():
    result=positive_power_comparison_source_pins()
    for name,pin in atanh_odd_slice_source_pins().items():
        if name in result and result[name]!=pin:
            raise PairedPowerError("paired-power source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_positive_power_comparison.py":"381cd294ff30012ed53978ec2590eb3d8da009339ea342af90fa3ec876bbebd4",
        "scripts/sqrt2_power_approximation_power_bounds.py":"ef4401c17fb3c3ddf0ef47aaea1ea5396a5c658ed6eb4e88d4349256cf5f9856",
        "scripts/sqrt2_power_atanh_odd_slice.py":"91fcf50ee5a35c19605a11497e6d7aca2970257cb468f383997b1a62d3208210",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_paired_power.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PairedPowerError("paired-power source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _even_power(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    zero=Zero();two=Succ(Succ(zero))
    def base(t):
        a,x,y=t.terms(("t","x","y"))
        power=_subst(t,registry,"Pow(t,slot,x)",instantiate(Axiom("PA5"),two),t.hyp("left"))
        first=apply(specialize(t,"power_zero",a,zero,x),EqRefl(zero),power)
        second=apply(specialize(t,"power_zero",Mul(a,a),zero,y),EqRefl(zero),t.hyp("right"))
        return _chain(first,EqSym(second))
    def successor(t):
        def chosen(u):
            a,oldx,oldy=u.terms(("t","old_x","old_y"))
            equal=apply(specialize(u,"IH",oldx,oldy),AndElimL(u.hyp("second")),AndElimL(u.hyp("short")))
            return _chain(AndElimR(u.hyp("first")),CongMul(AndElimR(u.hyp("second")),EqRefl(a)),
                specialize(u,"mul_assoc",oldx,a,a),CongMul(equal,EqRefl(Mul(a,a))),EqSym(AndElimR(u.hyp("short"))))
        def first(t):
            a,k=t.terms(("t","k"));index=Mul(two,k)
            earlier=apply(specialize(t,"power_step",a,index,Succ(index),t.term("middle")),EqRefl(Succ(index)),AndElimL(t.hyp("first")))
            return eliminate(t,earlier,("old_x",),"second",lambda u:
                eliminate(u,apply(specialize(u,"power_step",Mul(u.term("t"),u.term("t")),u.term("k"),Succ(u.term("k")),u.term("y")),
                    EqRefl(Succ(u.term("k"))),u.hyp("right")),("old_y",),"short",chosen))
        a,k,x=t.terms(("t","k","x"));index=Succ(Mul(two,k))
        power=_subst(t,registry,"Pow(t,slot,x)",specialize(t,"double_succ",k),t.hyp("left"))
        step=apply(specialize(t,"power_step",a,index,Succ(index),x),EqRefl(Succ(index)),power)
        return eliminate(t,step,("middle",),"first",first)
    return introduce(s,("t",),(),lambda t:Ind(target.body.body,
        introduce(t,("x","y"),("left","right"),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,("x","y"),("left","right"),successor))))


def _root(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,CongMul,EqRefl
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()))
    def chosen(t):
        a,k,old,y=t.terms(("t","k","old","y"))
        equal=apply(specialize(t,"even_power",a,k,old,y),AndElimL(t.hyp("step")),t.hyp("right"))
        return _chain(AndElimR(t.hyp("step")),CongMul(equal,EqRefl(a)),specialize(t,"mul_comm",y,a))
    def start(t):
        a,k,x=t.terms(("t","k","x"));index=Mul(two,k)
        step=apply(specialize(t,"power_step",a,index,Succ(index),x),EqRefl(Succ(index)),t.hyp("left"))
        return eliminate(t,step,("old",),"step",chosen)
    return introduce(s,("t","k","x","y"),("left","right"),start)


def prove_paired_power(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry();even=parse_named(HELPER_SOURCES["even_power"],registry=registry)
    return assemble_mixed_certificate(code="AP018",target=frozen_paired_power_target(_registry=registry),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"even_power":lambda s:_even_power(s,even,registry),"AP018":_root},
        pins=paired_power_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
