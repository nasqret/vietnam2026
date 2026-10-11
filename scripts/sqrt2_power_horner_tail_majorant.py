"""CV064: finite omitted-tail majorization at two ordered natural bases.

For a<=b construct the tail after N of length r+1, its value u at base b,
the whole value v at base a and p=a^r,q=b^r, proving p*u<=q*v.
For a=2,b=3 this is the integer core of the (2/3)^N tail estimate.
"""
from hashlib import sha256

from sqrt2_power_horner_base_comparison import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,horner_base_comparison_source_pins,
    NAMED_SOURCE as COMPARISON_SOURCE,HELPER_SOURCES as COMPARISON_HELPERS,
)
from sqrt2_power_horner_splitting import NAMED_SOURCE as SPLITTING_SOURCE
from sqrt2_power_row_horner_values import HELPER_SOURCES as ROW_HELPERS
from sqrt2_power_weighted_accumulation_evaluation import ROW_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-horner-tail-majorant-v1"
A,T = ("ab","ac"),("tb","tc")
PARAMETERS = A+("a","b","N","r")
OUTPUTS = T+("u","v","p","q")
SPLIT_OUTPUTS = T+("x","y","v","h")
COMPARE_OUTPUTS = ("p","q","u","w")
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". Le(a,b) -> exists "+" ".join(OUTPUTS)+". NatAffineSlice(ab,ac,N,1,tb,tc,S r) /\\ (NatHornerValue(tb,tc,b,S r,u) /\\ (NatHornerValue(ab,ac,a,N+S r,v) /\\ (Pow(a,r,p) /\\ (Pow(b,r,q) /\\ Le(p*u,q*v)))))"
TARGET_SHA256 = "adec9c34b4e9fd8be3a611ebe168b24c3cfbd3ca6d6b96568180e2849705609f"
HELPER_SOURCES = {}
HELPER_TARGET_SHA256 = {}
SPLITTING_ARCHIVE = dict(case="CV062",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-splitting-v1/generation-process.json.gz",
    bytes=30155,sha256="8d93f8a5f07eb49370b7b54c6bceaed17dc2cb7eae76e1ec652a7082e1021327",
    raw_bytes=461522,raw_sha256="e25e2c2304a015cec3bef2510ca055fcf4b38866adba1da3c28f7e54721283ba",
    bundle_bytes=256057,bundle_sha256="bfe45da726ddbbc6db9574b817d48471d27286387f9a56505fde8f0e6598baf9",
    nodes=124,root=123,target_ast_sha256="9cde54938675644bbc152c11b3e0270bf4ac303df68a8275b2e5ab6341e8f467")
COMPARISON_ARCHIVE = dict(case="CV063",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-horner-base-comparison-v1/generation-process.json.gz",
    bytes=30112,sha256="7d99e734d7f65c09e06d3d810fc18985fc292449c3b0c95e9e813170f0af3f29",
    raw_bytes=466610,raw_sha256="9a9dee375dbfaf28942e9f6f504fd95a1ac0bdabcbb259518ac5e83262d7f4eb",
    bundle_bytes=259517,bundle_sha256="de7052c68bfe61d50e1ecc04b1833a5040b0f84ed2385c881e5666c954485c4f",
    nodes=125,root=124,target_ast_sha256="9427a92cb26d4fcfea9d3160585b295d542e0c343f466f0326c7f8acbf25bbe0")
ARCHIVES = (SPLITTING_ARCHIVE,COMPARISON_ARCHIVE,ROW_ARCHIVE)
ENDPOINT_SOURCES = {
    "splitting":SPLITTING_SOURCE,"comparison":COMPARISON_SOURCE,"value_unique":ROW_HELPERS["value_unique"],
    "mul_left_mono":COMPARISON_HELPERS["mul_left_mono"],
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
}
ENDPOINT_OWNERS = dict(splitting="CV062",comparison="CV063",value_unique="CV059",mul_left_mono="CV063",le_trans="CV063")
HELPER_DEPENDENCIES = {"CV064":tuple(ENDPOINT_SOURCES)}


class HornerTailMajorantError(ValueError):
    """Changed true tail, whole comparison value or denominator factors."""


def frozen_horner_tail_majorant_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=6 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerTailMajorantError("CV064 exact finite tail majorant target changed")
    return target


def source_contract():
    return dict(code="CV064",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,base_order_required=True,actual_shifted_tail_and_two_values_constructed=True,
        actual_two_scaling_powers_constructed=True,inequality="p*u<=q*v; p=a^r; q=b^r",
        tail_length="r+1",whole_length="N+(r+1)",zero_bases_allowed=True,
        rational_division_transport_claimed=False,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def horner_tail_majorant_source_pins():
    result = horner_base_comparison_source_pins()
    expected = {"scripts/sqrt2_power_horner_base_comparison.py":"75a1f8d6983c871186d9cc2c948b3bf9325cda92522a47791d1c4acb0ca8928c",
        "scripts/sqrt2_power_horner_splitting.py":"17d330dc31b9e7c6aca718bbce4c4cbbeab881783cb42118b3e0a76c322fe27a",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_horner_tail_majorant.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerTailMajorantError("finite tail source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from peano_lab.kernel.proofs import EqSym
    from peano_lab.kernel.terms import Mul,Succ
    def chosen(t):
        split,comp = t.hyp("split"),t.hyp("comp")
        same = apply(specialize(t,"value_unique",*t.terms(T+("a",)),Succ(t.term("r")),*t.terms(("w","y"))),field(comp,1,6),field(split,2,6))
        compared = _subst(t,registry,"Le(p*u,q*slot)",same,field(comp,5,6))
        tail_below_whole = witness((Mul(*t.terms(("h","x"))),),EqSym(field(split,5,6)))
        scaled = apply(specialize(t,"mul_left_mono",*t.terms(("y","v","q"))),tail_below_whole)
        bound = apply(specialize(t,"le_trans",Mul(*t.terms(("p","u"))),Mul(*t.terms(("q","y"))),Mul(*t.terms(("q","v")))),compared,scaled)
        return witness(t.terms(OUTPUTS),conjunction(field(split,0,6),field(comp,0,6),field(split,3,6),field(comp,2,6),field(comp,3,6),bound))
    return introduce(s,PARAMETERS,("order",),lambda t:
        eliminate(t,specialize(t,"splitting",*t.terms(A+("a","N")),Succ(t.term("r"))),SPLIT_OUTPUTS,"split",lambda u:
            eliminate(u,apply(specialize(u,"comparison",*u.terms(T+("a","b","r"))),u.hyp("order")),COMPARE_OUTPUTS,"comp",chosen)))


def prove_horner_tail_majorant(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV064",target=frozen_horner_tail_majorant_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"CV064":lambda s:_root(s,registry)},pins=horner_tail_majorant_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
