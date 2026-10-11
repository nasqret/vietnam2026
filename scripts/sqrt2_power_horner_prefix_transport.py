"""CV055: one actual Horner history works for matching shorter inputs.

Construct a length-N trace and preserve its actual history/endpoints for a
second input through M<=N when the input coefficients agree below M. No
equality of different-length endpoints is asserted and no factor is cancelled.
"""
from hashlib import sha256

from sqrt2_power_horner_trace import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,horner_trace_source_pins,
    NAMED_SOURCE as HORNER_SOURCE,
)
from sqrt2_power_geometric_horner import HORNER_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-horner-prefix-transport-v1"
A,B,H = ("ab","ac"),("bb","bc"),("hb","hc")
PARAMETERS = A+B+("t","M","N")
MATCH = "forall i a. Lt(i,M) -> BetaAt(ab,ac,i,a) -> BetaAt(bb,bc,i,a)"


def trace(inputs,length):
    return "NatScaledHornerTrace("+",".join(inputs+("t",length)+H)+")"


NAMED_SOURCE = ("forall "+" ".join(PARAMETERS)+". Le(M,N) -> ("+MATCH+") -> exists hb hc x. "+trace(A,"N")+
    " /\\ ("+trace(B,"M")+" /\\ BetaAt(hb,hc,M,x))")
TARGET_SHA256 = "6c091c8fbcbf99ab1176e5414d83f55bd66930b61f484841194d2dec7a45b4a4"
HELPER_SOURCES = {"transport":"forall "+" ".join(PARAMETERS+H)+". Le(M,N) -> ("+MATCH+") -> "+trace(A,"N")+" -> "+trace(B,"M")}
HELPER_TARGET_SHA256 = {"transport":"5b170d3968a5ea5c4d1a5fff08c8ea35ee1e67594f7326a70f9a3432415c29a1"}
ARCHIVES = (HORNER_ARCHIVE,)
ENDPOINT_SOURCES = {
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "horner_exists":HORNER_SOURCE,
}
ENDPOINT_OWNERS = {name:"CV032" for name in ENDPOINT_SOURCES}
HELPER_DEPENDENCIES = {"transport":("le_trans",),"CV055":("horner_exists","beta_exists","transport")}


class HornerPrefixTransportError(ValueError):
    """Changed input match, length order or actual shared Horner history."""


def frozen_horner_prefix_transport_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=7 or len(premises)!=2 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerPrefixTransportError("CV055 exact shared-prefix Horner target changed")
    return target


def source_contract():
    return dict(code="CV055",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=2,length_order_and_low_input_match_required=True,actual_shared_horner_history_constructed=True,
        actual_shorter_endpoint_constructed=True,coefficient_reencoding_and_prefix_restriction=True,
        empty_prefix_and_zero_multiplier_allowed=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        different_length_endpoint_equality=False,factors_cancelled=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def horner_prefix_transport_source_pins():
    result = horner_trace_source_pins()
    expected = {"scripts/sqrt2_power_horner_trace.py":"32feca5a71d2b82367e6321d7a276c8c7de0f0fbf9b97513e22e816f80ee0328",
        "scripts/sqrt2_power_geometric_horner.py":"6179fa42c4437ed53db78fdc4f806d281d4774b58544150c7007dcfa3b656adc",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_horner_prefix_transport.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerPrefixTransportError("Horner prefix source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _transport(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndIntro,AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ
    def finish(t):
        def step(u):
            def decoded(v):
                coefficient = apply(specialize(v,"match",*v.terms(("k","a"))),v.hyp("bound"),field(v.hyp("step_data"),1,3))
                return witness(v.terms(("h","a")),conjunction(field(v.hyp("step_data"),0,3),coefficient,field(v.hyp("step_data"),2,3)))
            bound = apply(specialize(u,"le_trans",Succ(u.term("k")),*u.terms(("M","N"))),u.hyp("bound"),u.hyp("order"))
            actual = apply(instantiate(AndElimR(u.hyp("trace")),u.term("k")),bound)
            return eliminate(u,actual,("h","a"),"step_data",decoded)
        return AndIntro(AndElimL(t.hyp("trace")),introduce(t,("k",),("bound",),step))
    return introduce(s,PARAMETERS+H,("order","match","trace"),finish)


def _root(s):
    from peano_lab.kernel.proofs import AndElimL
    def chosen(t):
        short = apply(specialize(t,"transport",*t.terms(PARAMETERS+H)),t.hyp("order"),t.hyp("match"),AndElimL(t.hyp("data")))
        return witness(t.terms(H+("x",)),conjunction(AndElimL(t.hyp("data")),short,t.hyp("endpoint")))
    return introduce(s,PARAMETERS,("order","match"),lambda t:
        eliminate(t,specialize(t,"horner_exists",*t.terms(A+("t","N"))),H,"data",lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(H+("M",))),("x",),"endpoint",chosen)))


def prove_horner_prefix_transport(*,limits=None):
    return assemble_mixed_certificate(code="CV055",target=frozen_horner_prefix_transport_target(),registry=definition_registry(),
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"transport":_transport,"CV055":_root},
        pins=horner_prefix_transport_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
