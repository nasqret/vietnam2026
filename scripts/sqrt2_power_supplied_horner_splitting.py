"""CV082: split actual supplied Horner values using the supplied tail slice.

The whole, prefix and tail can have unrelated Horner-history codes. Their
values agree by proved extensionality, and z=t^N*x+y holds without replacing
the caller's tail or values. Zero base and empty parts are allowed.
"""
from hashlib import sha256

from sqrt2_power_horner_splitting import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,horner_splitting_source_pins,
    A,B,HA,HB,FIXED,SLICE,HELPER_SOURCES as SPLIT_HELPERS,
    ENDPOINT_SOURCES as SPLIT_ENDPOINTS,COMPOSITION_ARCHIVE,
)
from sqrt2_power_horner_tail_majorant import SPLITTING_ARCHIVE
from sqrt2_power_row_horner_values import HELPER_SOURCES as VALUE_HELPERS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-supplied-horner-splitting-v1"
PARAMETERS = A+B+("t","M","N","x","y","z","p")
PREMISES = (SLICE,"NatHornerValue(ab,ac,t,M,x)","NatHornerValue(bb,bc,t,N,y)",
    "NatHornerValue(ab,ac,t,M+N,z)","Pow(t,N,p)")
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES)+" -> z=p*x+y"
TARGET_SHA256 = "2060fe5fe40be2b8cca591f0f8c6e4703cbe9367a3616d60b77f5e6c457553fc"
HELPER_SOURCES,HELPER_TARGET_SHA256 = {},{}
ARCHIVES = (COMPOSITION_ARCHIVE,SPLITTING_ARCHIVE)
ENDPOINT_SOURCES = {"all_prefixes":SPLIT_HELPERS["all_prefixes"],"value_unique":VALUE_HELPERS["value_unique"],
    **{name:SPLIT_ENDPOINTS[name] for name in ("beta_exists","trace_transport","add_comm","le_refl")}}
ENDPOINT_OWNERS = {name:"CV062" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["value_unique"] = "CV061"
HELPER_DEPENDENCIES = {"CV082":tuple(ENDPOINT_SOURCES)}


class SuppliedHornerSplittingError(ValueError):
    """Changed actual slice, evaluated values or denominator-cleared split."""


def frozen_supplied_horner_splitting_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=11 or len(premises)!=5 or type(conclusion) is not Eq or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SuppliedHornerSplittingError("CV082 exact supplied-value splitting changed")
    return target


def source_contract():
    return dict(code="CV082",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,supplied_coefficient_and_tail_codes_preserved=True,
        supplied_prefix_tail_and_whole_values_preserved=True,independent_horner_histories_allowed=True,
        exact_identity="z=p*x+y; p=t^N",prefix_value_transported_by_proved_uniqueness=True,
        zero_base_and_empty_parts_allowed=True,no_nonzero_factor_cancelled=True,
        code_number_equality_claimed=False,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",analytic_limit_claim=False,
        closes_IR072=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,
        IR_parents_closed=0,library_admissions=0)


def supplied_horner_splitting_source_pins():
    result = horner_splitting_source_pins()
    expected = {"scripts/sqrt2_power_horner_splitting.py":"17d330dc31b9e7c6aca718bbce4c4cbbeab881783cb42118b3e0a76c322fe27a",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_supplied_horner_splitting.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SuppliedHornerSplittingError("supplied splitting source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Add
    def chosen(t):
        M,N = t.terms(("M","N"));whole = t.hyp("whole_data");tail = t.hyp("tail_data")
        order = witness((N,),specialize(t,"add_comm",N,M))
        same = introduce(t,("i","a"),("bound","entry"),lambda u:u.hyp("entry"))
        short = apply(specialize(t,"trace_transport",*t.terms(A+A+("t",)),M,Add(M,N),*t.terms(HA)),
            order,same,AndElimL(whole))
        decoded = witness(t.terms(HA),conjunction(short,t.hyp("decoded_prefix")))
        unique = apply(specialize(t,"value_unique",*t.terms(A+("t","M","h","x"))),decoded,t.hyp("prefix_value"))
        endpoint = _subst(t,registry,"BetaAt(ahb,ahc,M,slot)",unique,t.hyp("decoded_prefix"))
        invariant = apply(specialize(t,"all_prefixes",*t.terms(FIXED)),t.hyp("slice"),AndElimL(whole),endpoint,AndElimL(tail))
        return apply(instantiate(invariant,*t.terms(("N","z","y","p"))),specialize(t,"le_refl",N),
            AndElimR(whole),AndElimR(tail),t.hyp("power"))
    return introduce(s,PARAMETERS,("slice","prefix_value","tail_value","whole_value","power"),lambda t:
        eliminate(t,t.hyp("whole_value"),HA,"whole_data",lambda u:
            eliminate(u,u.hyp("tail_value"),HB,"tail_data",lambda v:
                eliminate(v,specialize(v,"beta_exists",*v.terms(HA+("M",))),("h",),"decoded_prefix",chosen))))


def prove_supplied_horner_splitting(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV082",target=frozen_supplied_horner_splitting_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"CV082":lambda s:_root(s,registry)},pins=supplied_horner_splitting_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
