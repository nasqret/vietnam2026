"""AP010: joint base/exponent monotonicity for supplied actual natural powers.

The larger base must be nonzero; the smaller base may be zero. Same-exponent
comparison uses explicit HA induction. Actual power addition and a positive
factor extend the exponent. No unrelated polynomial encodings are introduced.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_argument_modulus import (
    ROOT,Scope,introduce,apply,specialize,canonical,json_hash,
    argument_modulus_source_pins,definition_registry as argument_registry,BOUND_ARCHIVE,
)
from sqrt2_power_exp_sample_modulus import INPUT_ARCHIVE
from sqrt2_power_exp_two_sided_continuity import _left,_right,_chain
from sqrt2_power_horner_splitting import ENDPOINT_SOURCES as POWER_ENDPOINTS
from sqrt2_power_quadratic_trace_exists import eliminate,witness
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-positive-power-comparison-v1"
NAMED_SOURCE="forall a b k l x y. Le(a,b) -> ~b=0 -> Pow(a,k,x) -> Pow(b,k+l,y) -> Le(x,y)"
TARGET_SHA256="4b0cf1709336ebd3b4aa2546b4ad7107701157fb692b6db7205344456192cd25"
HELPER_SOURCES={
    "step":"forall a b x y. Le(a,b) -> Le(x,y) -> Le(x*a,y*b)",
    "base_monotone":"forall a b. Le(a,b) -> forall k x y. Pow(a,k,x) -> Pow(b,k,y) -> Le(x,y)",
    "positive_factor":"forall a b. ~b=0 -> Le(a,a*b)",
}
HELPER_TARGET_SHA256={"step":"4b3eaab263c09f09bfce8f15c952c3de359224cf28ea948e876ff471ef27067a",
    "base_monotone":"1833ab47fa8c6f3a8a02e08c73f9accf172c84fc64522cbb99d2745b0376ec40",
    "positive_factor":"6cdb8cf7cc56d74e02dfd7c4d5c4f1282efc815693de5e17181f0392c5f09e66"}
ARCHIVES=(INPUT_ARCHIVE,BOUND_ARCHIVE)
ENDPOINT_SOURCES={
    **{n:POWER_ENDPOINTS[n] for n in ("power_zero","power_step","power_exists","le_refl","le_trans")},
    "power_add":"forall a e f s x y z. s=e+f -> Pow(a,e,x) -> Pow(a,f,y) -> Pow(a,s,z) -> z=x*y",
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "zero_or_succ":"forall n. n=0 \\/ exists k. n=S k",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
}
ENDPOINT_OWNERS={name:"AP006" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["mul_left_mono"]="CV071"
HELPER_DEPENDENCIES={
    "step":("mul_left_mono","mul_right_mono","le_trans"),
    "base_monotone":("power_zero","power_step","le_refl","step"),
    "positive_factor":("zero_or_succ",),
    "AP010":("base_monotone","positive_factor","power_exists","power_add","power_nonzero","le_trans"),
}


class PositivePowerComparisonError(ValueError):
    """Changed supplied powers, base order, positivity or exponent increment."""


def definition_registry():
    source=argument_registry();needed=set();pending=["Le","Pow"]
    while pending:
        name=pending.pop()
        if name not in needed:
            needed.add(name);pending.extend(source[name].conceptual_dependencies)
    result={name:spec for name,spec in source.items() if name in needed}
    seen=set();ids=set()
    for name,spec in result.items():
        if not set(spec.conceptual_dependencies)<=seen or spec.stable_id in ids:
            raise PositivePowerComparisonError("existing power definition DAG changed")
        seen.add(name);ids.add(spec.stable_id)
    return MappingProxyType(result)


def frozen_positive_power_comparison_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=6 or len(premises)!=4 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PositivePowerComparisonError("AP010 exact actual-power comparison target changed")
    return target


def source_contract():
    return dict(code="AP010",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=4,actual_supplied_powers_preserved=True,ordered_bases_required=True,larger_base_nonzero_required=True,
        zero_smaller_base_exponent_and_increment_allowed=True,same_exponent_base_comparison_by_explicit_induction=True,
        exponent_extension_uses_actual_power_addition=True,new_definition_ids=[],definition_admissions=0,
        new_induction_needed=True,analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def positive_power_comparison_source_pins():
    result=argument_modulus_source_pins()
    expected={"scripts/sqrt2_power_argument_modulus.py":"e8b4b0f02084fa368f60fcb69c6f265e15bb2cb7d35b16118c69cea174f2a451",
        "scripts/sqrt2_power_exp_sample_modulus.py":"1d78e9661a21956e9c483f98d61012a8e44831be7d597c54bf55bb5f7df509b8",
        "scripts/sqrt2_power_exp_two_sided_continuity.py":"8fd98e4b6733be1271387cf515dbf88ed4fabd48603a1169bd712b5385291086",
        "scripts/sqrt2_power_horner_splitting.py":"17d330dc31b9e7c6aca718bbce4c4cbbeab881783cb42118b3e0a76c322fe27a",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_positive_power_comparison.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PositivePowerComparisonError("power comparison source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _step(s):
    from peano_lab.kernel.terms import Mul
    def finish(t):
        a,b,x,y=t.terms(("a","b","x","y"))
        return apply(specialize(t,"le_trans",Mul(x,a),Mul(y,a),Mul(y,b)),
            apply(specialize(t,"mul_right_mono",x,y,a),t.hyp("values")),
            apply(specialize(t,"mul_left_mono",a,b,y),t.hyp("bases")))
    return introduce(s,("a","b","x","y"),("bases","values"),finish)


def _base_monotone(s,target,registry):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Mul,Succ,Zero
    zero=Zero();one=Succ(zero)
    def base(t):
        a,b,x,y=t.terms(("a","b","x","y"))
        px=apply(specialize(t,"power_zero",a,zero,x),EqRefl(zero),t.hyp("left_power"))
        py=apply(specialize(t,"power_zero",b,zero,y),EqRefl(zero),t.hyp("right_power"))
        result=_left(t,registry,specialize(t,"le_refl",one),one,EqSym(px))
        return _right(t,registry,result,x,EqSym(py))
    def successor(t):
        def chosen(u):
            a,b,k,x,y,p,q=u.terms(("a","b","k","x","y","p","q"))
            old=apply(specialize(u,"IH",p,q),AndElimL(u.hyp("previous_left")),AndElimL(u.hyp("previous_right")))
            bound=apply(specialize(u,"step",a,b,p,q),u.hyp("bases"),old)
            bound=_left(u,registry,bound,Mul(q,b),EqSym(AndElimR(u.hyp("previous_left"))))
            return _right(u,registry,bound,x,EqSym(AndElimR(u.hyp("previous_right"))))
        a,k,x=t.terms(("a","k","x"))
        return eliminate(t,apply(specialize(t,"power_step",a,k,Succ(k),x),EqRefl(Succ(k)),t.hyp("left_power")),("p",),"previous_left",lambda u:
            eliminate(u,apply(specialize(u,"power_step",u.term("b"),u.term("k"),Succ(u.term("k")),u.term("y")),
                EqRefl(Succ(u.term("k"))),u.hyp("right_power")),("q",),"previous_right",chosen))
    motive=target.body.body.right.body
    return introduce(s,("a","b"),("bases",),lambda t:Ind(motive,
        introduce(t,("x","y"),("left_power","right_power"),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,("x","y"),("left_power","right_power"),successor))))


def _positive_factor(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,BotElim,CongMul,EqRefl,EqSym,OrElim
    from peano_lab.kernel.terms import Mul
    def chosen(t):
        a,b,c=t.terms(("a","b","c"))
        return witness((Mul(a,c),),_chain(EqSym(instantiate(Axiom("PA6"),a,c)),CongMul(EqRefl(a),EqSym(t.hyp("successor")))))
    def finish(t):
        zero=t.hypothesis("zero");positive=t.hypothesis("positive")
        return OrElim(specialize(t,"zero_or_succ",t.term("b")),BotElim(apply(zero.hyp("nonzero"),zero.hyp("zero"))),
            eliminate(positive,positive.hyp("positive"),("c",),"successor",chosen))
    return introduce(s,("a","b"),("nonzero",),finish)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def chosen(t):
        a,b,k,l,x,y,p,q=t.terms(("a","b","k","l","x","y","p","q"))
        base=apply(instantiate(apply(specialize(t,"base_monotone",a,b),t.hyp("bases")),k,x,p),t.hyp("left_power"),t.hyp("middle"))
        nonzero=apply(instantiate(apply(specialize(t,"power_nonzero",b),t.hyp("nonzero")),l,q),t.hyp("factor"))
        extended=apply(specialize(t,"positive_factor",p,q),nonzero)
        bound=apply(specialize(t,"le_trans",x,p,Mul(p,q)),base,extended)
        same=apply(specialize(t,"power_add",b,k,l,Add(k,l),p,q,y),EqRefl(Add(k,l)),t.hyp("middle"),t.hyp("factor"),t.hyp("right_power"))
        return _right(t,registry,bound,x,EqSym(same))
    return introduce(s,("a","b","k","l","x","y"),("bases","nonzero","left_power","right_power"),lambda t:
        eliminate(t,specialize(t,"power_exists",t.term("b"),t.term("k")),("p",),"middle",lambda u:
            eliminate(u,specialize(u,"power_exists",u.term("b"),u.term("l")),("q",),"factor",chosen)))


def prove_positive_power_comparison(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP010",target=frozen_positive_power_comparison_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"step":_step,"base_monotone":lambda s:_base_monotone(s,parse_named(HELPER_SOURCES["base_monotone"],registry=registry),registry),
            "positive_factor":_positive_factor,"AP010":lambda s:_root(s,registry)},
        pins=positive_power_comparison_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
