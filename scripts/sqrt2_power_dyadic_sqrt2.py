"""SQ004: a total, unique, positive dyadic sqrt(2) computation graph.

ND0446 records only actual Pow(2,k,d) and FloorSqrt(2*d*d,s) computations.
Positivity, integer bounds and uniqueness are proved, never definition clauses.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_scaled_sqrt2 import (
    ROOT,Scope,introduce,eliminate,witness,conjunction,apply,specialize,canonical,json_hash,
    definition_registry as floor_registry,scaled_sqrt2_source_pins,NAMED_SOURCE as SCALED_SOURCE,
)
from sqrt2_power_composition_tail_bound import RATIONAL_TAIL_ARCHIVE
from sqrt2_power_horner_splitting import COMPOSITION_ARCHIVE
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-dyadic-sqrt2-v1"
DEFINITION_ID="ND0446"
DEFINITION_NAME="DyadicSqrt2"
DEFINITION_PARAMETERS=("k","d","s")
DEFINITION_SOURCE="Pow(2,k,d) /\\ FloorSqrt(2*(d*d),s)"
DEFINITION_AST_SHA256="a5ac6da0f7cada4b9c8b38bf3327453cba6f7bb1d4cc374f51216e41c3f84e4a"
POWER_DEFINITION_NAMES=("BetaAt","Product","Repeat","Pow")


def _and(parts):
    result=parts[-1]
    for part in reversed(parts[:-1]):
        result="("+part+") /\\ ("+result+")"
    return result


PARTS=("DyadicSqrt2(k,d,s)","~d=0","~s=0","Le(d,s)","Lt(s,2*d)",
       "forall q t. DyadicSqrt2(k,q,t) -> q=d /\\ t=s")
NAMED_SOURCE="forall k. exists d s. "+_and(PARTS)
TARGET_SHA256="949e42462649aba0033ab2dacf74c2aba14cced0c759d3efedb524aa34ee12ce"
SCALED_ARCHIVE=dict(case="SQ003",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-scaled-sqrt2-v2/generation-process.json.gz",
    bytes=10300,sha256="f7c4f2156d7d849ba770fcc9c0da5799173a7f4d4eae140cecf19fb08a49bd89",
    raw_bytes=87647,raw_sha256="fc2cdecf457e2c438f5e6a8c60f476a5675a1cbea7e58e046b7532d9fa2212c3",
    bundle_bytes=43642,bundle_sha256="05d951bee0ed77b01b03ff51e51da3ea4e8349a397c563cbe6b119670a83271f",
    nodes=42,root=41,target_ast_sha256="4e1139169e23ee835cb5f0eb9371fa4b6a641079db34b76bcb25f692bd88efb8")
ARCHIVES=(SCALED_ARCHIVE,RATIONAL_TAIL_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={
    "scaled":SCALED_SOURCE,"power_exists":"forall a k. exists d. Pow(a,k,d)",
    "power_unique":"forall a k p q. Pow(a,k,p) -> Pow(a,k,q) -> p=q",
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0",
}
ENDPOINT_OWNERS=dict(scaled="SQ003",power_exists="CV061",power_unique="CV061",power_nonzero="CV075",succ_ne_zero="CV075")
HELPER_DEPENDENCIES={"SQ004":tuple(ENDPOINT_SOURCES)}


class DyadicSqrt2Error(ValueError):
    """Changed computation graph, conservative DAG, source or exact theorem."""


def power_floor_registry():
    from sqrt2_power_definitions import PARENT,PARENT_SHA256
    from peano_lab.library.defined_syntax import DEFINITIONS_BY_NAME
    registry=dict(floor_registry())
    raw=PARENT.read_bytes()
    if sha256(raw).hexdigest()!=PARENT_SHA256:
        raise DyadicSqrt2Error("sealed definition parent changed")
    historical={row["name"]:row for row in json.loads(raw)["reviewed_definitions"]}
    for name in POWER_DEFINITION_NAMES:
        d=DEFINITIONS_BY_NAME[name];old=historical[name]
        if (d.stable_id!=old["id"] or d.parameters!=tuple(old["parameters"])
                or sha256(d.template_source.encode()).hexdigest()!=old["expansion_sha256"]
                or d.conceptual_dependencies!=tuple(old["dependencies"])
                or not set(d.conceptual_dependencies)<=registry.keys()
                or d.stable_id in {x.stable_id for x in registry.values()}):
            raise DyadicSqrt2Error("reused power definition identity or dependency changed")
        registry[name]=d
    return MappingProxyType(registry)


def definition_registry():
    from sqrt2_power_definitions import PARENT,parse_named
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.library.proof_bundle import encode_formula
    registry=dict(power_floor_registry());parent=json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids={r["id"] for r in parent}|{d.stable_id for d in registry.values()}|{f"ND{i:04d}" for i in range(382,446)}
    names={r["name"] for r in parent}|set(registry)
    if DEFINITION_ID in ids or DEFINITION_NAME in names:
        raise DyadicSqrt2Error("dyadic computation definition collision")
    formula=parse_named(DEFINITION_SOURCE,DEFINITION_PARAMETERS,registry)
    if json_hash(encode_formula(formula))!=DEFINITION_AST_SHA256:
        raise DyadicSqrt2Error("dyadic computation expansion changed")
    expanded=pretty_formula(formula,list(DEFINITION_PARAMETERS))
    spec=_definition(stable_id=DEFINITION_ID,name=DEFINITION_NAME,parameters=DEFINITION_PARAMETERS,
        template_source=expanded,summary="Actual power-of-two denominator and integer floor root of twice its square; no accuracy clause.",
        category="irrationality_square_root",conceptual_dependencies=("Pow","FloorSqrt"))
    if spec.template_formula!=formula or parse_formula_in_context(expanded,list(DEFINITION_PARAMETERS))!=formula:
        raise DyadicSqrt2Error("dyadic definition failed conservative roundtrip")
    registry[DEFINITION_NAME]=spec
    return MappingProxyType(registry)


def frozen_dyadic_sqrt2_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise DyadicSqrt2Error("SQ004 exact unconditional dyadic computation target changed")
    return target


def source_contract():
    return dict(code="SQ004",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precision_indices_including_zero=True,actual_power_and_floor_root_constructed=True,
        denominator_and_root_nonzero_proved=True,unique_output_pair=True,integer_bounds="d<=s<2*d",
        new_definition_ids=[DEFINITION_ID],new_definition_ast_sha256=DEFINITION_AST_SHA256,
        definition_dependencies=["Pow","FloorSqrt"],definition_contains_accuracy_or_bounds=False,
        definition_admissions=0,new_induction_needed=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",dyadic_interval_width_proved=False,
        real_square_root_interpretation=False,analytic_limit_claim=False,
        closes_IR013=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def dyadic_sqrt2_source_pins():
    result=scaled_sqrt2_source_pins()
    expected={"scripts/sqrt2_power_scaled_sqrt2.py":"0efd0071acdea8b96a65b3f577fa6fa3737adbca633cb22299bd571614991d98",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_dyadic_sqrt2.py","scripts/sqrt2_power_composition_tail_bound.py",
                 "scripts/sqrt2_power_horner_splitting.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise DyadicSqrt2Error("dyadic computation source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _scaled_field(proof,index):
    """Select the exact left-associated five-part SQ003 conclusion."""
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    if type(index) is not int or not 0<=index<5:
        raise DyadicSqrt2Error("invalid supplied scaled-root field")
    for _ in range(4-index):
        proof=AndElimL(proof)
    return proof if index==0 else AndElimR(proof)


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Succ,Zero
    one=Succ(Zero());two=Succ(one)
    def nonzero(t):
        law=apply(specialize(t,"power_nonzero",two),specialize(t,"succ_ne_zero",one))
        return apply(instantiate(law,*t.terms(("k","d"))),t.hyp("power"))
    def unique(t):
        q,d,k=t.terms(("q","d","k"))
        equal=apply(specialize(t,"power_unique",two,k,q,d),AndElimL(t.hyp("rival")),t.hyp("power"))
        floor=_subst(t,registry,"FloorSqrt(2*(slot*slot),t)",equal,AndElimR(t.hyp("rival")))
        same=apply(instantiate(_scaled_field(t.hyp("scaled_data"),4),t.term("t")),floor)
        return conjunction(equal,same)
    def finish(t):
        data=t.hyp("scaled_data")
        graph=conjunction(t.hyp("power"),_scaled_field(data,0))
        return witness(t.terms(("d","s")),conjunction(graph,nonzero(t),_scaled_field(data,3),
            _scaled_field(data,1),_scaled_field(data,2),introduce(t,("q","t"),("rival",),unique)))
    def powered(t):
        return eliminate(t,apply(specialize(t,"scaled",t.term("d")),nonzero(t)),("s",),"scaled_data",finish)
    return introduce(s,("k",),(),lambda t:
        eliminate(t,specialize(t,"power_exists",two,t.term("k")),("d",),"power",powered))


def prove_dyadic_sqrt2(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="SQ004",target=frozen_dyadic_sqrt2_target(),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,endpoint_owners=ENDPOINT_OWNERS,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories={"SQ004":lambda s:_root(s,registry)},
        pins=dyadic_sqrt2_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
