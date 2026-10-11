"""CV076: all in-range rational tail bounds of one constructed composition.

Retain the entire CV074 witness package, decode its actual terminal row,
and for every cutoff M<=J construct its genuine tail with bound 9*(2/3)^M.
The value, normalization and coefficients belong to the same computation.
"""
from hashlib import sha256
import re

from sqrt2_power_rational_tail_majorant import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,rational_tail_majorant_source_pins,
    NAMED_SOURCE as RATIONAL_TAIL_SOURCE,COMPOSITION_ARCHIVE,conjoin,
)
from sqrt2_power_composition_majorant import NAMED_SOURCE as COMPOSITION_SOURCE,OUTPUTS as COMPOSITION_OUTPUTS,PARTS as COMPOSITION_PARTS,J
from sqrt2_power_series_power_trace import HELPER_SOURCES as POWER_HELPERS
from sqrt2_power_scaled_exp_bound import _n
from sqrt2_power_quadratic_height import _chain
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-composition-tail-bound-v1"
U,T = ("ub","uc"),("tb","tc")
OUTPUTS = COMPOSITION_OUTPUTS+U
TAIL_OUTPUTS = T+("u","p0","q0","h")
CUT_OUTPUTS = ("r",)+TAIL_OUTPUTS
TAIL_PARTS = ("J=M+r","NatAffineSlice(ub,uc,M,1,tb,tc,S r)","NatHornerValue(tb,tc,3,S r,u)",
    "Pow(2,M,p0)","Pow(3,M,q0)","Pow(3,J,h)","~p0=0","~q0=0","~h=0","~(w0*h)=0",
    "Le(u*q0,(9*p0)*(w0*h))","IRatLe(u,0,w0*h,9*p0,0,q0)")
CUTS = "forall M. Le(M,J) -> exists "+" ".join(CUT_OUTPUTS)+". "+conjoin(TAIL_PARTS)
ROW = "NatPowerRow(rb,rc,sb,sc,S N,ub,uc)"
VALUE = "NatHornerValue(ub,uc,2,S "+J+",s)"
SPECIALIZED_CUTS = re.sub(r"\bJ\b",J,CUTS)
PARTS = COMPOSITION_PARTS+(ROW,VALUE,SPECIALIZED_CUTS)
NAMED_SOURCE = "forall k N. exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256 = "2baa8df68b336dc9d80d78e7f1d9797fdeb2859efc39377e00c1c0a18de9f83f"
HELPER_SOURCES = {
    "for_value":"forall ub uc J w0 s v. ~w0=0 -> NatHornerValue(ub,uc,2,S J,s) -> Pow(2,J,v) -> Le(s,9*(w0*v)) -> "+CUTS,
}
HELPER_TARGET_SHA256 = {"for_value":"69ea1d6859b855fddccbe8be311e9003e05af8dc9d3f8cdcb93fa805adc9d50c"}
MAJORANT_ARCHIVE = dict(case="CV074",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-composition-majorant-v1/generation-process.json.gz",
    bytes=97871,sha256="0b9dc655d19ddce1a289a2fb7cb2fc4e12188728681730f70d0ec084e5d73464",
    raw_bytes=2673911,raw_sha256="98e40f58d752dbc133fa1766b71da82c14261eb280abe078dbaed833ce9dfb22",
    bundle_bytes=1627627,bundle_sha256="1ec6611c5e094c392f09d2203b46e4ce9380c95ad0ab421a8c9f3d7c600aa221",
    nodes=325,root=324,target_ast_sha256="0a0ef5814cf4d9655010b47abf33ab8cbcb9f86f7d6f336cafcc1a6d7556273b")
RATIONAL_TAIL_ARCHIVE = dict(case="CV075",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-rational-tail-majorant-v1/generation-process.json.gz",
    bytes=38724,sha256="d4b1f9144fe037a63a80efa2e1eab5daba5b3c71ebdedf597493535513d461fa",
    raw_bytes=684788,raw_sha256="c08252f55cd3090f36f204982d2a64f36d927c7cecdbd1bbb225081b2ef703fa",
    bundle_bytes=389010,bundle_sha256="5e9943d53ae57de27108eb1c6c31783198b59e581ba08365f20e368274d9bbda",
    nodes=144,root=143,target_ast_sha256="afeaa7ea69229597287202c3420e527d2b96f2c2bbd77a455ad620d128c7edff")
ARCHIVES = (MAJORANT_ARCHIVE,RATIONAL_TAIL_ARCHIVE)
ENDPOINT_SOURCES = {
    "majorant_exists":COMPOSITION_SOURCE,"rational_tail":RATIONAL_TAIL_SOURCE,
    "row_decode":POWER_HELPERS["decode"],
    "add_comm":"forall a b. a+b=b+a",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)",
}
ENDPOINT_OWNERS = {name:"CV074" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["rational_tail"] = "CV075"
HELPER_DEPENDENCIES = {
    "for_value":("rational_tail","add_comm","mul_assoc"),
    "CV076":("majorant_exists","row_decode","for_value"),
}


class CompositionTailBoundError(ValueError):
    """Changed actual terminal row, cutoff, normalization or rational bound."""


def frozen_composition_tail_bound_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=2 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise CompositionTailBoundError("CV076 exact same-composition rational tails changed")
    return target


def source_contract():
    return dict(code="CV076",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_CV074_data_retained=True,actual_terminal_row_constructed=True,
        same_row_value_and_normalization_for_every_tail=True,all_cutoffs="M<=J; J=(N+1)*(k+1)",
        actual_tail_for_every_in_range_cutoff=True,rational_bound="tail(1/3)/w0 <= 9*(2/3)^M",
        nonzero_rational_denominators_proved=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        empty_tail_case_claimed=False,analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def composition_tail_bound_source_pins():
    result = rational_tail_majorant_source_pins()
    expected = {"scripts/sqrt2_power_rational_tail_majorant.py":"9dc0903202c1c4922011503b997a6ad2556a8d59c8750f0a028b50da038a1776",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_composition_tail_bound.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise CompositionTailBoundError("composition tail source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _for_value(s,registry):
    from peano_lab.kernel.proofs import EqSym
    def equality(t):
        return _chain(EqSym(t.hyp("gap")),specialize(t,"add_comm",*t.terms(("r","M"))))
    def chosen(t):
        data = t.hyp("tail_data")
        power = _subst(t,registry,"Pow(3,slot,h)",EqSym(equality(t)),field(data,4,11))
        parts = tuple(field(data,i,11) if i!=4 else power for i in range(11))
        return witness(t.terms(CUT_OUTPUTS),conjunction(equality(t),*parts))
    def shifted(t):
        same = equality(t)
        value = _subst(t,registry,"NatHornerValue(ub,uc,2,S slot,s)",same,t.hyp("whole_value"))
        power = _subst(t,registry,"Pow(2,slot,v)",same,t.hyp("whole_power"))
        bound = _subst(t,registry,"Le(s,slot)",EqSym(specialize(t,"mul_assoc",_n(9),*t.terms(("w0","v")))),t.hyp("majorant"))
        return eliminate(t,apply(specialize(t,"rational_tail",*t.terms(U+("w0",)),_n(9),*t.terms(("M","r","s","v"))),
            t.hyp("nonzero"),value,power,bound),TAIL_OUTPUTS,"tail_data",chosen)
    return introduce(s,U+("J","w0","s","v"),("nonzero","whole_value","whole_power","majorant"),lambda t:
        introduce(t,("M",),("cut_bound",),lambda u:eliminate(u,u.hyp("cut_bound"),("r",),"gap",shifted)))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Mul,Succ
    def chosen(t):
        data = t.hyp("data");J = Mul(Succ(t.term("N")),Succ(t.term("k")))
        value = apply(instantiate(field(data,25,37),*t.terms(U)),t.hyp("row"))
        cuts = apply(specialize(t,"for_value",*t.terms(U),J,*t.terms(("w0","s","v"))),
            field(data,15,37),value,field(data,20,37),field(data,36,37))
        return witness(t.terms(OUTPUTS),conjunction(*(field(data,i,37) for i in range(37)),t.hyp("row"),value,cuts))
    return introduce(s,("k","N"),(),lambda t:
        eliminate(t,specialize(t,"majorant_exists",*t.terms(("k","N"))),COMPOSITION_OUTPUTS,"data",lambda u:
            eliminate(u,specialize(u,"row_decode",*u.terms(("rb","rc","sb","sc")),Succ(u.term("N"))),U,"row",chosen)))


def prove_composition_tail_bound(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV076",target=frozen_composition_tail_bound_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"for_value":lambda s:_for_value(s,registry),"CV076":_root},
        pins=composition_tail_bound_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
