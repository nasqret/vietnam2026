"""CV051: construct two power traces and transport every low coefficient.

For the same actual input and H<=J, all rows through K agree below H.
Induction uses actual unit rows, actual convolution steps and CV050 locality;
no equality of truncated and full evaluations or omitted tails is asserted.
"""
from hashlib import sha256

from sqrt2_power_series_power_euler import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,series_power_euler_source_pins,
    HELPER_SOURCES as POWER_EULER_HELPERS,CONVOLUTION_ARCHIVE,
)
from sqrt2_power_series_power_trace import NAMED_SOURCE as POWER_SOURCE,HELPER_SOURCES as POWER_HELPERS
from sqrt2_power_convolution_unit import HELPER_SOURCES as UNIT_HELPERS,_subst
from sqrt2_power_convolution_locality import (
    HELPER_SOURCES as LOCAL_HELPERS,convolution_locality_source_pins,
)
from sqrt2_power_natural_convolution import HELPER_SOURCES as CONVOLUTION_HELPERS
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-power-width-transport-v1"
A = ("ab","ac","L")
P,Q = ("pb","pc","qb","qc"),("rb","rc","sb","sc")
U,V,X,Y = ("ub","uc"),("vb","vc"),("xb","xc"),("yb","yc")
PARAMETERS = A+("H","J","K")
FIXED = PARAMETERS+P+Q


def row(codes,index,values):
    return "NatPowerRow("+",".join(codes+(index,)+values)+")"


def trace(codes,width):
    return "NatPowerTrace("+",".join(A+(width,)+codes+("K",))+")"


ALL_ROWS = ("forall k "+" ".join(U+V+("i","a"))+". Le(k,K) -> "+row(P,"k",U)+" -> "+row(Q,"k",V)+
    " -> Lt(i,H) -> BetaAt(ub,uc,i,a) -> BetaAt(vb,vc,i,a)")
NAMED_SOURCE = ("forall "+" ".join(PARAMETERS)+". Le(H,J) -> exists "+" ".join(P+Q)+". "+trace(P,"H")+
    " /\\ ("+trace(Q,"J")+" /\\ ("+ALL_ROWS+"))")
TARGET_SHA256 = "d22452396ee9b966bdb17b27cd501a09a8cda4e1433e5d3885685cd54982e6eb"
HELPER_SOURCES = {
    "unit_unique":"forall i a b. NatUnitCoefficient(i,a) -> NatUnitCoefficient(i,b) -> a=b",
    "unit_transport":"forall ub uc H vb vc J i a. NatUnitPrefix(ub,uc,H) -> NatUnitPrefix(vb,vc,J) -> Lt(i,H) -> Lt(i,J) -> BetaAt(ub,uc,i,a) -> BetaAt(vb,vc,i,a)",
    "all_rows":"forall "+" ".join(FIXED)+". Le(H,J) -> "+trace(P,"H")+" -> "+trace(Q,"J")+" -> "+ALL_ROWS,
}
HELPER_TARGET_SHA256 = {
    "unit_unique":"372401fac2b064f67a5a20f7ea685b5ec09b75f33e5361a2bf15452884565bc1",
    "unit_transport":"54148f92f8f77066840a7c9e5c44b985f6bb74f65fd074f420b128dac588a847",
    "all_rows":"88e88241411a0c62986ddcad1c578fbfc32fe7e56827bb6321aeccabd3763373",
}
POWER_ARCHIVE = dict(case="CV017",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-series-power-euler-v1/generation-process.json.gz",
    bytes=48035,sha256="334d64508b95ebb9165feda1ac1b9fc065b328b663566829862b0bf9e67b3fbb",
    raw_bytes=1257925,raw_sha256="0fbbe2501b089a92178194c173d59e19dcdc4e9a58e9fe15ddc638c18c022c5a",
    bundle_bytes=768657,bundle_sha256="d94cbf0c9fb9f42a645258b60f5d7ba325f8ec20a54a983922da9b13c990f208",
    nodes=193,root=192,target_ast_sha256="e71ae746c83206309479f65ede0e10c2e11d077b3ac2123df4942475e453d1e6")
LOCAL_ARCHIVE = dict(case="CV050",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-locality-v1/generation-process.json.gz",
    bytes=21228,sha256="5bf953f756412227ae191c701f3fef6096d29c72022d01769e6c9033ff73cd9a",
    raw_bytes=355619,raw_sha256="a817a0e447318eaa7dfbf4e9e61a7b6d7763208b6828ce381f27582fb8e679df",
    bundle_bytes=213329,bundle_sha256="eefa1a560700fd4767facdeeb2765dd01c5c6caed05d6d6b4653f75e84619e07",
    nodes=117,root=116,target_ast_sha256="750e75f60ad34a2d8fa423359399e8fcd60a9a1c90dbde559a2faf8a856457c0")
ARCHIVES = (POWER_ARCHIVE,LOCAL_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {
    "succ_ne_zero":"forall a. ~S a=0",
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "prefix_entry":CONVOLUTION_HELPERS["prefix_entry"],"coefficient_unique":CONVOLUTION_HELPERS["coefficient_unique"],
    "power_exists":POWER_SOURCE,"row_decode":POWER_HELPERS["decode"],
    "trace_unit":POWER_EULER_HELPERS["trace_unit"],"trace_step":POWER_EULER_HELPERS["trace_step"],
    "unit_entry":UNIT_HELPERS["unit_entry"],"coefficient_transport":LOCAL_HELPERS["coefficient_transport"],
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(**{name:"CV017" for name in ("power_exists","row_decode","trace_unit","trace_step","unit_entry")},coefficient_transport="CV050")
HELPER_DEPENDENCIES = {
    "unit_unique":("succ_ne_zero",),
    "unit_transport":("beta_exists","unit_entry","unit_unique"),
    "all_rows":("le_trans","le_succ","le_refl","lt_not_le","trace_unit","trace_step","unit_transport",
        "row_decode","beta_exists","prefix_entry","coefficient_unique","coefficient_transport"),
    "CV051":("power_exists","all_rows"),
}


class PowerWidthTransportError(ValueError):
    """Changed actual power rows, common cutoff, width order or ancestry."""


def frozen_power_width_transport_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=6 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PowerWidthTransportError("CV051 exact constructed cross-width power target changed")
    return target


def source_contract():
    return dict(code="CV051",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,width_order_required=True,both_actual_power_traces_constructed=True,
        every_row_through_exponent_preserved=True,coefficients_preserved_only_below_smaller_width=True,
        same_actual_input=True,zero_width_and_exponent_allowed=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",all_degree_product_equality=False,
        truncated_full_evaluation_equality=False,analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def power_width_transport_source_pins():
    result = series_power_euler_source_pins()
    for name,pin in convolution_locality_source_pins().items():
        if name in result and result[name]!=pin:
            raise PowerWidthTransportError("shared proof-source pins disagree")
        result[name] = pin
    expected = {"scripts/sqrt2_power_series_power_euler.py":"f00d1180a96ba497a5c961b850e660941d6c608d70ebc7071a51e53344b5205c",
        "scripts/sqrt2_power_convolution_locality.py":"6425412569658b50990434fb1c7a4b39ae4e6340621515faf8e3402ac427d986",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_power_width_transport.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PowerWidthTransportError("power width source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _unit_unique(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,EqSym,EqTrans,OrElim
    def finish(t):
        def first_zero(u):
            left = u.hypothesis("second_zero")
            same = EqTrans(AndElimR(left.hyp("first_zero")),EqSym(AndElimR(left.hyp("second_zero"))))
            def impossible(v):
                equation = EqTrans(EqSym(AndElimL(v.hyp("positive"))),AndElimL(v.hyp("first_zero")))
                return BotElim(apply(specialize(v,"succ_ne_zero",v.term("h")),equation))
            right = u.hypothesis("second_positive")
            contradiction = eliminate(right,right.hyp("second_positive"),("h",),"positive",impossible)
            return OrElim(u.hyp("second"),same,contradiction)
        def first_positive(u):
            def decoded(v):
                left = v.hypothesis("second_zero")
                equation = EqTrans(EqSym(AndElimL(left.hyp("positive"))),AndElimL(left.hyp("second_zero")))
                contradiction = BotElim(apply(specialize(left,"succ_ne_zero",left.term("h")),equation))
                right = v.hypothesis("second_positive")
                def same(w):
                    return EqTrans(AndElimR(w.hyp("positive")),EqSym(AndElimR(w.hyp("other_positive"))))
                return OrElim(v.hyp("second"),contradiction,
                    eliminate(right,right.hyp("second_positive"),("g",),"other_positive",same))
            return eliminate(u,u.hyp("first_positive"),("h",),"positive",decoded)
        return OrElim(t.hyp("first"),first_zero(t.hypothesis("first_zero")),first_positive(t.hypothesis("first_positive")))
    return introduce(s,("i","a","b"),("first","second"),finish)


def _unit_transport(s,registry):
    from peano_lab.kernel.proofs import EqSym
    def chosen(t):
        first = apply(specialize(t,"unit_entry",*t.terms(U+("H","i","a"))),t.hyp("unitU"),t.hyp("small"),t.hyp("input"))
        second = apply(specialize(t,"unit_entry",*t.terms(V+("J","i","b"))),t.hyp("unitV"),t.hyp("large"),t.hyp("output"))
        same = apply(specialize(t,"unit_unique",*t.terms(("i","a","b"))),first,second)
        return _subst(t,registry,"BetaAt(vb,vc,i,slot)",EqSym(same),t.hyp("output"))
    return introduce(s,U+("H",)+V+("J","i","a"),("unitU","unitV","small","large","input"),lambda t:
        eliminate(t,specialize(t,"beta_exists",*t.terms(V+("i",))),("b",),"output",chosen))


def _all_rows(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR,BotElim,EqSym,Ind,OrElim,OrIntroL
    from peano_lab.kernel.terms import Succ,Zero
    variables,premises = U+V+("i","a"),("bound","rowU","rowV","small","input")
    def base(t):
        unitU = apply(specialize(t,"trace_unit",*t.terms(A+("H",)+P+("K",)+U)),t.hyp("traceP"),t.hyp("rowU"))
        unitV = apply(specialize(t,"trace_unit",*t.terms(A+("J",)+Q+("K",)+V)),t.hyp("traceQ"),t.hyp("rowV"))
        large = apply(specialize(t,"le_trans",Succ(t.term("i")),*t.terms(("H","J"))),t.hyp("small"),t.hyp("width"))
        return apply(specialize(t,"unit_transport",*t.terms(U+("H",)+V+("J","i","a"))),unitU,unitV,t.hyp("small"),large,t.hyp("input"))
    def successor(t):
        def chosen(u):
            def right(v):
                inside = v.hypothesis("inside")
                old_bound = apply(specialize(inside,"le_trans",inside.term("k"),Succ(inside.term("k")),inside.term("K")),
                    apply(specialize(inside,"le_succ",inside.term("k"),inside.term("k")),specialize(inside,"le_refl",inside.term("k"))),inside.hyp("bound"))
                old_value = apply(specialize(inside,"IH",*inside.terms(X+Y+("j","b"))),
                    old_bound,inside.hyp("previousP"),inside.hyp("previousQ"),inside.hyp("index"),AndElimR(inside.hyp("inside")))
                large = apply(specialize(inside,"le_trans",Succ(inside.term("j")),*inside.terms(("H","J"))),inside.hyp("index"),inside.hyp("width"))
                moved = OrIntroL(AndIntro(large,old_value))
                outside = v.hypothesis("outside")
                impossible = BotElim(apply(specialize(outside,"lt_not_le",*outside.terms(("j","H"))),outside.hyp("index"),AndElimL(outside.hyp("outside"))))
                return OrElim(v.hyp("padded"),moved,impossible)
            left_match = introduce(u,("j","b"),("index","padded"),lambda v:v.hyp("padded"))
            right_match = introduce(u,("j","b"),("index","padded"),right)
            first = apply(specialize(u,"trace_step",*u.terms(A+("H",)+P+("K","k")+X+U)),
                u.hyp("traceP"),u.hyp("bound"),u.hyp("previousP"),u.hyp("rowU"))
            second = apply(specialize(u,"trace_step",*u.terms(A+("J",)+Q+("K","k")+Y+V)),
                u.hyp("traceQ"),u.hyp("bound"),u.hyp("previousQ"),u.hyp("rowV"))
            first_coeff = apply(specialize(u,"prefix_entry",*u.terms(A+X+("H",)+U+("H","i","a"))),first,u.hyp("small"),u.hyp("input"))
            transported = apply(specialize(u,"coefficient_transport",*u.terms(A+X+("H",)+A+Y+("J","H","i","a"))),
                left_match,right_match,u.hyp("small"),first_coeff)
            large = apply(specialize(u,"le_trans",Succ(u.term("i")),*u.terms(("H","J"))),u.hyp("small"),u.hyp("width"))
            second_coeff = apply(specialize(u,"prefix_entry",*u.terms(A+Y+("J",)+V+("J","i","c"))),second,large,u.hyp("output"))
            same = apply(specialize(u,"coefficient_unique",*u.terms(A+Y+("J","i","a","c"))),transported,second_coeff)
            return _subst(u,registry,"BetaAt(vb,vc,i,slot)",EqSym(same),u.hyp("output"))
        return eliminate(t,specialize(t,"row_decode",*t.terms(P+("k",))),X,"previousP",lambda u:
            eliminate(u,specialize(u,"row_decode",*u.terms(Q+("k",))),Y,"previousQ",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(V+("i",))),("c",),"output",chosen)))
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.right.right.right.body
    return introduce(s,FIXED,("width","traceP","traceQ"),lambda t:Ind(motive,
        introduce(t,variables,premises,base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,variables,premises,successor))))


def _root(s):
    def chosen(t):
        preservation = apply(specialize(t,"all_rows",*t.terms(FIXED)),t.hyp("width"),t.hyp("traceP"),t.hyp("traceQ"))
        return witness(t.terms(P+Q),conjunction(t.hyp("traceP"),t.hyp("traceQ"),preservation))
    return introduce(s,PARAMETERS,("width",),lambda t:
        eliminate(t,specialize(t,"power_exists",*t.terms(A+("H","K"))),P,"traceP",lambda u:
            eliminate(u,specialize(u,"power_exists",*u.terms(A+("J","K"))),Q,"traceQ",chosen)))


def prove_power_width_transport(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV051",target=frozen_power_width_transport_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"unit_unique":_unit_unique,"unit_transport":lambda s:_unit_transport(s,registry),
            "all_rows":lambda s:_all_rows(s,parse_named(HELPER_SOURCES["all_rows"],registry=registry),registry),"CV051":_root},
        pins=power_width_transport_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
