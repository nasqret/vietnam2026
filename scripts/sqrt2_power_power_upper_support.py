"""CV054: construct every power row with explicit upper support 1+k*L.

The conservative bound includes the unit at k=0, including empty inputs.
Convolution support is proved through each actual step; it is not a field
degree convention or an assumption included in NatPowerTrace.
"""
from hashlib import sha256
from types import MappingProxyType

from sqrt2_power_series_power_euler import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry as power_registry,series_power_euler_source_pins,
    HELPER_SOURCES as POWER_EULER_HELPERS,
)
from sqrt2_power_series_power_trace import NAMED_SOURCE as POWER_SOURCE,HELPER_SOURCES as POWER_HELPERS
from sqrt2_power_convolution_unit import HELPER_SOURCES as UNIT_HELPERS,_subst
from sqrt2_power_convolution_upper_support import (
    definition_registry as upper_registry,convolution_upper_support_source_pins,
    HELPER_SOURCES as UPPER_HELPERS,
)
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-power-upper-support-v1"
A = ("ab","ac","L")
P = ("pb","pc","qb","qc")
U,X = ("ub","uc"),("xb","xc")
PARAMETERS = A+("H","K")
FIXED = PARAMETERS+P


def row(index,codes):
    return "NatPowerRow("+",".join(P+(index,)+codes)+")"


TRACE = "NatPowerTrace("+",".join(A+("H",)+P+("K",))+")"
ALL_ROWS = "forall k ub uc. Le(k,K) -> "+row("k",U)+" -> NatZeroAfter(ub,uc,H,S(k*L))"
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". exists "+" ".join(P)+". "+TRACE+" /\\ ("+ALL_ROWS+")"
TARGET_SHA256 = "ef95e6269e88a485d4fd577edb6814ce45c9bf1f61fddfcc6aae499ce488e879"
HELPER_SOURCES = {
    "storage_support":"forall ab ac L. NatZeroAfter(ab,ac,L,L)",
    "unit_support":"forall ub uc H. NatUnitPrefix(ub,uc,H) -> NatZeroAfter(ub,uc,H,1)",
    "all_rows":"forall "+" ".join(FIXED)+". "+TRACE+" -> "+ALL_ROWS,
}
HELPER_TARGET_SHA256 = {
    "storage_support":"35d038fab8a585a3a6ab1322b86d2033e82b5089b5f2a09585e7195266ef1916",
    "unit_support":"fe492e98572f465dde218cb7e07b57854746a9cdd985824b8171cb793f3c74df",
    "all_rows":"9c747e8e0439642471bb66b2b53edab39b668be7485709938b90b4de46e27296",
}
POWER_ARCHIVE = dict(case="CV017",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-series-power-euler-v1/generation-process.json.gz",
    bytes=48035,sha256="334d64508b95ebb9165feda1ac1b9fc065b328b663566829862b0bf9e67b3fbb",
    raw_bytes=1257925,raw_sha256="0fbbe2501b089a92178194c173d59e19dcdc4e9a58e9fe15ddc638c18c022c5a",
    bundle_bytes=768657,bundle_sha256="d94cbf0c9fb9f42a645258b60f5d7ba325f8ec20a54a983922da9b13c990f208",
    nodes=193,root=192,target_ast_sha256="e71ae746c83206309479f65ede0e10c2e11d077b3ac2123df4942475e453d1e6")
UPPER_ARCHIVE = dict(case="CV053",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-upper-support-v1/generation-process.json.gz",
    bytes=25358,sha256="f9256a33cb0e817e438bcf35f4d87987aec2dbb0024023e756ddb26a820a0669",
    raw_bytes=437198,raw_sha256="ca1211f93b9d85010b54d66c2951d896d1222dfbec8b03081b6f18a42682d4b5",
    bundle_bytes=259719,bundle_sha256="eb53e85a3f7f6adb863962998a2b23b4c0e83382b1cec2a9e0e971829a777a45",
    nodes=127,root=126,target_ast_sha256="10fb7e6300ce6b56bf6d231d7f357343629838d1ed95469a0309b42e521c276a")
ARCHIVES = (POWER_ARCHIVE,UPPER_ARCHIVE)
ENDPOINT_SOURCES = {
    "add_comm":"forall a b. a+b=b+a","mul_zero_left":"forall a. 0*a=0",
    "mul_succ_left":"forall a b. (S a)*b=a*b+b",
    "le_refl":"forall a. Le(a,a)","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "power_exists":POWER_SOURCE,"row_decode":POWER_HELPERS["decode"],
    "trace_unit":POWER_EULER_HELPERS["trace_unit"],"trace_step":POWER_EULER_HELPERS["trace_step"],
    "unit_positive":UNIT_HELPERS["unit_positive"],"prefix_support":UPPER_HELPERS["prefix_support"],
}
ENDPOINT_OWNERS = {name:"CV017" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["prefix_support"] = "CV053"
HELPER_DEPENDENCIES = {
    "storage_support":("lt_not_le",),
    "unit_support":("le_refl","lt_not_le","unit_positive"),
    "all_rows":("trace_unit","trace_step","unit_support","storage_support","row_decode","prefix_support",
        "le_refl","le_succ","le_trans","mul_zero_left","mul_succ_left","add_comm"),
    "CV054":("power_exists","all_rows"),
}


class PowerUpperSupportError(ValueError):
    """Changed actual power execution or upper support, including the unit."""


def definition_registry():
    result = dict(power_registry())
    for name,d in upper_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise PowerUpperSupportError("shared power/support definitions disagree")
        result[name] = d
    return MappingProxyType(result)


def frozen_power_upper_support_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=5 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PowerUpperSupportError("CV054 exact constructed all-power upper-support target changed")
    return target


def source_contract():
    return dict(code="CV054",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,actual_power_trace_constructed=True,all_rows_through_exponent_bounded=True,
        support_bound="1+k*L",arbitrary_storage_width=True,zero_width_and_empty_input_allowed=True,
        unit_at_exponent_zero_retained=True,execution_contains_support_claim=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",finite_power_evaluation_identity=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def power_upper_support_source_pins():
    result = series_power_euler_source_pins()
    for name,pin in convolution_upper_support_source_pins().items():
        if name in result and result[name]!=pin:
            raise PowerUpperSupportError("shared proof-source pins disagree")
        result[name] = pin
    expected = {"scripts/sqrt2_power_series_power_euler.py":"f00d1180a96ba497a5c961b850e660941d6c608d70ebc7071a51e53344b5205c",
        "scripts/sqrt2_power_convolution_upper_support.py":"1d5e9cb3287218cfed8b57d1e9527cbdf7e23fe43dfc7f8fc2c90837638eb2e8",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_power_upper_support.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PowerUpperSupportError("power upper-support source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _storage_support(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,OrElim
    def pointwise(t):
        inside,outside = t.hypothesis("inside"),t.hypothesis("outside")
        impossible = BotElim(apply(specialize(inside,"lt_not_le",*inside.terms(("i","L"))),AndElimL(inside.hyp("inside")),inside.hyp("bound")))
        return OrElim(t.hyp("padded"),impossible,AndElimR(outside.hyp("outside")))
    return introduce(s,A,(),lambda t:introduce(t,("i","a"),("bound","padded"),pointwise))


def _unit_support(s,registry):
    from peano_lab.kernel.terms import Zero
    def pointwise(t):
        def contradiction(u):
            impossible = _subst(u,registry,"Le(1,slot)",u.hyp("equation"),u.hyp("bound"))
            return apply(specialize(u,"lt_not_le",Zero(),Zero()),impossible,specialize(u,"le_refl",Zero()))
        nonzero = introduce(t,(),("equation",),contradiction)
        return apply(specialize(t,"unit_positive",*t.terms(U+("H","i","a"))),t.hyp("unit"),nonzero,t.hyp("padded"))
    return introduce(s,U+("H",),("unit",),lambda t:introduce(t,("i","a"),("bound","padded"),pointwise))


def _all_rows(s,target,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import Axiom,CongS,EqSym,EqTrans,Ind
    from peano_lab.kernel.terms import Mul,Succ
    def base(t):
        unit = apply(specialize(t,"trace_unit",*t.terms(A+("H",)+P+("K",)+U)),t.hyp("trace"),t.hyp("row"))
        support = apply(specialize(t,"unit_support",*t.terms(U+("H",))),unit)
        equation = CongS(specialize(t,"mul_zero_left",t.term("L")))
        return _subst(t,registry,"NatZeroAfter(ub,uc,H,slot)",EqSym(equation),support)
    def successor(t):
        def chosen(u):
            k,K,L,H = u.terms(("k","K","L","H"))
            previous_bound = apply(specialize(u,"le_trans",k,Succ(k),K),
                apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            previous = apply(specialize(u,"IH",*u.terms(X)),previous_bound,u.hyp("previous"))
            convolution = apply(specialize(u,"trace_step",*u.terms(A+("H",)+P+("K","k")+X+U)),
                u.hyp("trace"),u.hyp("bound"),u.hyp("previous"),u.hyp("row"))
            result = apply(specialize(u,"prefix_support",*u.terms(A+X),H,L,Succ(Mul(k,L)),*u.terms(U),H),
                specialize(u,"storage_support",*u.terms(A)),previous,convolution)
            cutoff = EqTrans(instantiate(Axiom("PA4"),L,Mul(k,L)),EqTrans(CongS(specialize(u,"add_comm",L,Mul(k,L))),
                CongS(EqSym(specialize(u,"mul_succ_left",k,L)))))
            return _subst(u,registry,"NatZeroAfter(ub,uc,H,slot)",cutoff,result)
        return eliminate(t,specialize(t,"row_decode",*t.terms(P+("k",))),X,"previous",chosen)
    motive = target
    for _ in FIXED:
        motive = motive.body
    motive = motive.right.body
    return introduce(s,FIXED,("trace",),lambda t:Ind(motive,
        introduce(t,U,("bound","row"),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,U,("bound","row"),successor))))


def _root(s):
    from peano_lab.kernel.proofs import AndIntro
    def chosen(t):
        support = apply(specialize(t,"all_rows",*t.terms(FIXED)),t.hyp("trace"))
        return witness(t.terms(P),AndIntro(t.hyp("trace"),support))
    return introduce(s,PARAMETERS,(),lambda t:
        eliminate(t,specialize(t,"power_exists",*t.terms(PARAMETERS)),P,"trace",chosen))


def prove_power_upper_support(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV054",target=frozen_power_upper_support_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"storage_support":_storage_support,"unit_support":lambda s:_unit_support(s,registry),
            "all_rows":lambda s:_all_rows(s,parse_named(HELPER_SOURCES["all_rows"],registry=registry),registry),"CV054":_root},
        pins=power_upper_support_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
