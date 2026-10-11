"""CV079: transport N+1 weighted terms from power traces of depths N and N+1.

Restrict the larger trace explicitly, compare actual power rows through N,
and invoke consumed-row transport. No unused extra small power row is needed.
"""
from hashlib import sha256
import re

from sqrt2_power_consumed_row_transport import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,consumed_row_transport_source_pins,
    W,P,Q,R,S,U,V,NAMED_SOURCE as TRANSPORT_SOURCE,CONSUMED_MATCH,OUTPUT_MATCH,
)
from sqrt2_power_power_width_transport import HELPER_SOURCES as POWER_HELPERS
from sqrt2_power_composition_width_transport import POWER_WIDTH_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-successor-composition-transport-v1"
A = ("ab","ac","L")
PARAMETERS = A+("H","J")+W+P+Q+R+S+("N",)
POWER_FIXED = A+("H","J")+P+Q+("N",)
SOURCE_MATCH = re.sub(r"\bK\b","S N",CONSUMED_MATCH)
RESULT = re.sub(r"\bK\b","S N",OUTPUT_MATCH)


def power(codes,width,depth):
    return "NatPowerTrace("+",".join(A+(width,)+codes+(depth,))+")"


def weighted(width,source,acc):
    return "NatWeightedSeriesTrace("+",".join((width,)+W+source+acc+("S N",))+")"


PREMISES = ("Le(H,J)",power(P,"H","N"),power(Q,"J","S N"),weighted("H",P,R),weighted("J",Q,S))
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+" -> ".join(PREMISES+(RESULT,))
TARGET_SHA256 = "f7c56ab23847715134689855bfe86d7d7162eddbd0c52f9112dda1a9a5a89e2b"
HELPER_SOURCES = {
    "restrict":"forall "+" ".join(A+("H",)+P+("N",))+". "+power(P,"H","S N")+" -> "+power(P,"H","N"),
    "sources":"forall "+" ".join(POWER_FIXED)+". "+" -> ".join(PREMISES[:3]+(SOURCE_MATCH,)),
}
HELPER_TARGET_SHA256 = {
    "restrict":"504e394d288b1c3d0bf0c137bdac4edf1511fa10ecff60a1b5599b7c6855a9d9",
    "sources":"6e2aaec09c65c9eeda9d2f78f725bc796c8a31ec5c4dd8b80d00e4e1d1ba121d",
}
CONSUMED_ARCHIVE = dict(case="CV078",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-consumed-row-transport-v1/generation-process.json.gz",
    bytes=21020,sha256="28ffb2f8fedcc084cc3f578d03393773ffd50a30703a7cda392aea0ab1946ca2",
    raw_bytes=204631,raw_sha256="989340a7608930619bd27b99a472bc523a332995f846536803ac5be85f41d5f1",
    bundle_bytes=85206,bundle_sha256="040652ba1ae46390151d5fd1023a97f06f598cf6976a6ff1faf81d528a44d7f4",
    nodes=30,root=29,target_ast_sha256="2f33ca6e896147c1f9c2b66a154e0be06e18e77fd718ba4123744b81650ed78d")
ARCHIVES = (POWER_WIDTH_ARCHIVE,CONSUMED_ARCHIVE)
ENDPOINT_SOURCES = {
    "power_rows":POWER_HELPERS["all_rows"],"transport":TRANSPORT_SOURCE,
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_of_succ_le_succ":"forall a b. Le(S a,S b) -> Le(a,b)",
}
ENDPOINT_OWNERS = {name:"CV051" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS["transport"] = "CV078"
HELPER_DEPENDENCIES = {
    "restrict":("le_succ",),"sources":("restrict","power_rows","le_of_succ_le_succ"),
    "CV079":("sources","transport"),
}


class SuccessorCompositionTransportError(ValueError):
    """Changed supplied depth, width, weights or accumulation range."""


def frozen_successor_composition_transport_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=24 or len(premises)!=5 or type(conclusion) is not Forall or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SuccessorCompositionTransportError("CV079 exact successor-length transport changed")
    return target


def source_contract():
    return dict(code="CV079",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,width_order_required=True,same_input_and_weight_codes=True,
        supplied_small_power_depth="N",supplied_large_power_depth="N+1",accumulation_terms="N+1",
        larger_power_trace_restricted_explicitly=True,all_accumulation_rows_through_N_plus_one=True,
        low_coefficient_transport_only=True,zero_horizon_and_empty_width_allowed=True,
        unused_small_power_row_constructed=False,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        code_number_equality_claimed=False,analytic_limit_claim=False,closes_IR072=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def successor_composition_transport_source_pins():
    result = consumed_row_transport_source_pins()
    expected = {"scripts/sqrt2_power_consumed_row_transport.py":"f2aac51c47f9fbdf8a8dcbe2ff5402fe1b4a4bd85e38ca7f1ea2b5e1155808a8",
        "scripts/sqrt2_power_power_width_transport.py":"54ffb3d275dc532e4a8d3d88eefefc1a3ccfe1ed02ce96acae3bca8a9dcecacc",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_successor_composition_transport.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SuccessorCompositionTransportError("successor transport source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _restrict(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ
    def finish(t):
        step = introduce(t,("j",),("index",),lambda u:
            apply(instantiate(AndElimR(u.hyp("trace")),u.term("j")),
                apply(specialize(u,"le_succ",Succ(u.term("j")),u.term("N")),u.hyp("index"))))
        return conjunction(AndElimL(t.hyp("trace")),step)
    return introduce(s,A+("H",)+P+("N",),("trace",),finish)


def _sources(s):
    from sqrt2_power_native import instantiate
    def entry(t):
        restricted = apply(specialize(t,"restrict",*t.terms(A+("J",)+Q+("N",))),t.hyp("traceQ"))
        rows = apply(specialize(t,"power_rows",*t.terms(A+("H","J","N")+P+Q)),t.hyp("width"),t.hyp("traceP"),restricted)
        bound = apply(specialize(t,"le_of_succ_le_succ",*t.terms(("k","N"))),t.hyp("index"))
        return apply(instantiate(rows,*t.terms(("k",)+U+V+("i","a"))),bound,t.hyp("rowP"),t.hyp("rowQ"),t.hyp("coefficient_bound"),t.hyp("entry"))
    return introduce(s,POWER_FIXED,("width","traceP","traceQ"),lambda t:
        introduce(t,("k",)+U+V+("i","a"),("index","rowP","rowQ","coefficient_bound","entry"),entry))


def _root(s):
    from peano_lab.kernel.terms import Succ
    def finish(t):
        sources = apply(specialize(t,"sources",*t.terms(POWER_FIXED)),t.hyp("width"),t.hyp("traceP"),t.hyp("traceQ"))
        return apply(specialize(t,"transport",*t.terms(("H","J")+W+P+Q+R+S),Succ(t.term("N"))),
            t.hyp("width"),sources,t.hyp("traceR"),t.hyp("traceS"))
    return introduce(s,PARAMETERS,("width","traceP","traceQ","traceR","traceS"),finish)


def prove_successor_composition_transport(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV079",target=frozen_successor_composition_transport_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"restrict":_restrict,"sources":_sources,"CV079":_root},pins=successor_composition_transport_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
