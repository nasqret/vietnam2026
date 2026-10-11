"""AP001: construct the actual finite logarithm/root quotient and its range.

The intermediate graph contains computations only. Positivity and the bound
0 <= (3*x*d)/((D*p)*s) <= 1 are proved separately. No real logarithm,
canonical approximation algorithm, accuracy or irrationality is asserted.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_dyadic_sqrt2 import (
    ROOT,Scope,introduce,eliminate,witness,conjunction,apply,specialize,canonical,json_hash,
    definition_registry as dyadic_registry,dyadic_sqrt2_source_pins,_and,
    NAMED_SOURCE as DYADIC_SOURCE,RATIONAL_TAIL_ARCHIVE,COMPOSITION_ARCHIVE,
)
from sqrt2_power_atanh_coefficients import NAMED_SOURCE as ATANH_SOURCE,atanh_coefficients_source_pins
from sqrt2_power_ternary_atanh_bound import (
    definition_registry as series_registry,ternary_atanh_bound_source_pins,NAMED_SOURCE as BOUND_SOURCE,
)
from sqrt2_power_atanh_euler import ATANH_ARCHIVE
from sqrt2_power_ternary_prefix_bound import TERNARY_ARCHIVE
from sqrt2_power_quadratic_trace_exists import field
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-log-root-argument-v1"
OUTPUTS=("d","s","D","ab","ac","x","p")
DEFINITION_ID="ND0447"
DEFINITION_NAME="NatSqrt2LogArgument"
DEFINITION_PARAMETERS=("k",)+OUTPUTS
GRAPH_PARTS=("DyadicSqrt2(k,d,s)","NatAtanhPrefix(D,ab,ac,S(2*k))",
             "NatHornerValue(ab,ac,3,S(2*k),x)","Pow(3,S(2*k),p)")
DEFINITION_SOURCE=_and(GRAPH_PARTS)
DEFINITION_DEPENDENCIES=("DyadicSqrt2","NatAtanhPrefix","NatHornerValue","Pow")
DEFINITION_AST_SHA256="547c299a5c2059ad3f764625f200b8bab623263f81a59103c0c18a3ecfcaeceb"
GRAPH="NatSqrt2LogArgument(k,d,s,D,ab,ac,x,p)"
PARTS=(GRAPH,"~d=0","~s=0","~D=0","~p=0","~((D*p)*s)=0","Le((3*x)*d,(D*p)*s)")
NAMED_SOURCE="forall k. exists "+" ".join(OUTPUTS)+". "+_and(PARTS)
TARGET_SHA256="2b80a217cebb668c94e88b3a849c0738ad80d20aee1014489d6b8561839e89df"
HELPER_SOURCES={"bounds":"forall D p x d s. ~D=0 -> ~p=0 -> ~s=0 -> Le(d,s) -> Le(3*x+3*D,D*p) -> ~((D*p)*s)=0 /\\ Le((3*x)*d,(D*p)*s)"}
HELPER_TARGET_SHA256={"bounds":"6812deadbc771144ece227bebd8973b1031745405ec38e1b2a883e863d645d12"}
DYADIC_ARCHIVE=dict(case="SQ004",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-dyadic-sqrt2-v1/generation-process.json.gz",
    bytes=24378,sha256="68eebf016753816dc0634a9fa6bd8f6e6fe33200ed1437bdb8d5812eacc85981",
    raw_bytes=418458,raw_sha256="3438b55f5900ea460fe6dca8c5df4e40f2f851266896ceb27699ed2d19b445ef",
    bundle_bytes=252950,bundle_sha256="f73908713a8b4912da9bc340d3a4e9e51f8ef156993f9527040eaaad0cf34ebf",
    nodes=139,root=138,target_ast_sha256="949e42462649aba0033ab2dacf74c2aba14cced0c759d3efedb524aa34ee12ce")
ARCHIVES=(DYADIC_ARCHIVE,ATANH_ARCHIVE,TERNARY_ARCHIVE,RATIONAL_TAIL_ARCHIVE,COMPOSITION_ARCHIVE)
ENDPOINT_SOURCES={
    "dyadic_exists":DYADIC_SOURCE,"atanh_exists":ATANH_SOURCE,"inner_bound":BOUND_SOURCE,
    "value_exists":"forall ab ac t H. exists y. NatHornerValue(ab,ac,t,H,y)",
    "power_exists":"forall a k. exists p. Pow(a,k,p)",
    "power_nonzero":"forall a. ~a=0 -> forall k p. Pow(a,k,p) -> ~p=0",
    "succ_ne_zero":"forall a. ~S a=0","mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b)=0",
    "add_comm":"forall a b. a+b=b+a",
    "mul_left_mono":"forall a b c. Le(a,b) -> Le(c*a,c*b)",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
}
ENDPOINT_OWNERS={name:"CV075" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(dyadic_exists="SQ004",atanh_exists="CV025",inner_bound="CV086",
                      value_exists="CV061",power_exists="CV061")
HELPER_DEPENDENCIES={
    "bounds":("mul_ne_zero","add_comm","mul_left_mono","mul_right_mono","le_trans"),
    "AP001":("dyadic_exists","atanh_exists","value_exists","power_exists","power_nonzero","succ_ne_zero","inner_bound","bounds"),
}


class LogRootArgumentError(ValueError):
    """Changed actual finite input, quotient, conservative graph or source."""


def computation_registry():
    """Reuse just the transitive definition cone, comparing shared identities."""
    pool=dict(series_registry())
    for name,spec in dyadic_registry().items():
        identity=("stable_id","parameters","template_source","template_formula","conceptual_dependencies")
        if name in pool and any(getattr(pool[name],key)!=getattr(spec,key) for key in identity):
            raise LogRootArgumentError("series and dyadic conservative definition disagreement")
        pool[name]=spec
    selected={};visiting=set()
    def visit(name):
        if name in selected:
            return
        if name in visiting or name not in pool:
            raise LogRootArgumentError("missing or cyclic computation definition")
        visiting.add(name)
        for dependency in pool[name].conceptual_dependencies:
            visit(dependency)
        spec=pool[name]
        if spec.stable_id in {d.stable_id for d in selected.values()}:
            raise LogRootArgumentError("computation definition ID collision")
        selected[name]=spec;visiting.remove(name)
    for name in (*DEFINITION_DEPENDENCIES,"NatZeroBefore"):
        visit(name)
    return MappingProxyType(selected)


def definition_registry():
    from sqrt2_power_definitions import PARENT,parse_named
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.library.proof_bundle import encode_formula
    result=dict(computation_registry());parent=json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids={d.stable_id for d in result.values()}|{d["id"] for d in parent}|{f"ND{i:04d}" for i in range(382,447)}
    if DEFINITION_ID in ids or DEFINITION_NAME in result or any(d["name"]==DEFINITION_NAME for d in parent):
        raise LogRootArgumentError("logarithm/root argument definition collision")
    formula=parse_named(DEFINITION_SOURCE,DEFINITION_PARAMETERS,result)
    if json_hash(encode_formula(formula))!=DEFINITION_AST_SHA256:
        raise LogRootArgumentError("logarithm/root computation graph expansion changed")
    source=pretty_formula(formula,list(DEFINITION_PARAMETERS))
    spec=_definition(stable_id=DEFINITION_ID,name=DEFINITION_NAME,parameters=DEFINITION_PARAMETERS,
        template_source=source,summary="Finite dyadic root, odd-reciprocal table, base-three Horner value and power; no bounds or analytic claims.",
        category="irrationality_approximation_computation",conceptual_dependencies=DEFINITION_DEPENDENCIES)
    if spec.template_formula!=formula or parse_formula_in_context(source,list(DEFINITION_PARAMETERS))!=formula:
        raise LogRootArgumentError("logarithm/root definition conservative roundtrip failed")
    result[DEFINITION_NAME]=spec
    return MappingProxyType(result)


def frozen_log_root_argument_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise LogRootArgumentError("AP001 exact computation/range target changed")
    return target


def source_contract():
    return dict(code="AP001",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precision_indices_including_zero=True,actual_dyadic_and_log_polynomial_data_constructed=True,
        prefix_length="S(2*k)",argument_numerator="(3*x)*d",argument_denominator="(D*p)*s",
        denominator_nonzero_proved=True,argument_upper_one_proved=True,bounds_are_definition_clauses=False,
        new_definition_ids=[DEFINITION_ID],new_definition_ast_sha256=DEFINITION_AST_SHA256,
        definition_dependencies=list(DEFINITION_DEPENDENCIES),definition_admissions=0,
        actual_beta_and_power_witnesses_preserved=True,new_induction_needed=False,
        canonical_PR_approximation_algorithm_claim=False,odd_sum_identification_claim=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def log_root_argument_source_pins():
    result=dyadic_sqrt2_source_pins()
    for source in (atanh_coefficients_source_pins(),ternary_atanh_bound_source_pins()):
        for name,pin in source.items():
            if name in result and result[name]!=pin:
                raise LogRootArgumentError("logarithm/root source disagreement")
            result[name]=pin
    expected={"scripts/sqrt2_power_dyadic_sqrt2.py":"9c498535a2397cc43911427ae9cdd7e35a46b26c966e85aac294ba871e3e07dc",
              **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_log_root_argument.py","scripts/sqrt2_power_ternary_prefix_bound.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise LogRootArgumentError("logarithm/root source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _bounds(s):
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    three=Succ(Succ(Succ(Zero())))
    def finish(t):
        D,p,x,d,root=t.terms(("D","p","x","d","s"));dp=Mul(D,p);tx=Mul(three,x);td=Mul(three,D)
        dpnz=apply(specialize(t,"mul_ne_zero",D,p),t.hyp("D_nonzero"),t.hyp("p_nonzero"))
        nonzero=apply(specialize(t,"mul_ne_zero",dp,root),dpnz,t.hyp("s_nonzero"))
        first=witness((td,),specialize(t,"add_comm",td,tx))
        inner=apply(specialize(t,"le_trans",tx,Add(tx,td),dp),first,t.hyp("inner"))
        lower=apply(specialize(t,"mul_right_mono",tx,dp,d),inner)
        upper=apply(specialize(t,"mul_left_mono",d,root,dp),t.hyp("root_range"))
        bounded=apply(specialize(t,"le_trans",Mul(tx,d),Mul(dp,d),Mul(dp,root)),lower,upper)
        return conjunction(nonzero,bounded)
    return introduce(s,("D","p","x","d","s"),("D_nonzero","p_nonzero","s_nonzero","root_range","inner"),finish)


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ,Zero
    two=Succ(Succ(Zero()));three=Succ(two)
    def length(t):
        return Succ(Mul(two,t.term("k")))
    def finish(t):
        root=t.hyp("root_data");coeff=t.hyp("coefficient_data")
        prefix=field(coeff,1,3)
        pnz=apply(instantiate(apply(specialize(t,"power_nonzero",three),specialize(t,"succ_ne_zero",two)),length(t),t.term("p")),t.hyp("power"))
        inner=apply(specialize(t,"inner_bound",*t.terms(("D","ab","ac")),Mul(two,t.term("k")),*t.terms(("x","p"))),prefix,t.hyp("value"),t.hyp("power"))
        bounds=apply(specialize(t,"bounds",*t.terms(("D","p","x","d","s"))),field(coeff,0,3),pnz,field(root,2,6),field(root,3,6),inner)
        graph=conjunction(field(root,0,6),prefix,t.hyp("value"),t.hyp("power"))
        return witness(t.terms(OUTPUTS),conjunction(graph,field(root,1,6),field(root,2,6),field(coeff,0,3),pnz,AndElimL(bounds),AndElimR(bounds)))
    return introduce(s,("k",),(),lambda t:
        eliminate(t,specialize(t,"dyadic_exists",t.term("k")),("d","s"),"root_data",lambda u:
            eliminate(u,specialize(u,"atanh_exists",length(u)),("D","ab","ac"),"coefficient_data",lambda v:
                eliminate(v,specialize(v,"value_exists",*v.terms(("ab","ac")),three,length(v)),("x",),"value",lambda w:
                    eliminate(w,specialize(w,"power_exists",three,length(w)),("p",),"power",finish)))))


def prove_log_root_argument(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP001",target=frozen_log_root_argument_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"bounds":_bounds,"AP001":_root},pins=log_root_argument_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
