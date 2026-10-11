"""AP002: total actual finite exponential samples of the log/root quotient.

Retain all coefficient/weight/term codes, exact factorial and power witnesses,
nonzero normalization and the actual sum. ND0448 records computations only;
neither convergence nor identification with (sqrt(2))^(sqrt(2)) is asserted.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from sqrt2_power_log_root_argument import (
    ROOT,Scope,introduce,eliminate,witness,conjunction,apply,specialize,field,canonical,json_hash,_and,
    definition_registry as argument_registry,log_root_argument_source_pins,
    NAMED_SOURCE as ARGUMENT_SOURCE,GRAPH as ARGUMENT_GRAPH,OUTPUTS as ARGUMENT_OUTPUTS,
)
from sqrt2_power_scaled_exp_terms import (
    definition_registry as exponential_registry,scaled_exp_terms_source_pins,NAMED_SOURCE as EXP_SOURCE,
)
from sqrt2_power_scaled_exp_bound import EXP_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA="sqrt2-power-exp-sample-v1"
EXP_OUTPUTS=("wb","wc","tb","tc","w0","f","h","y")
OUTPUTS=ARGUMENT_OUTPUTS+EXP_OUTPUTS
DEFINITION_ID="ND0448"
DEFINITION_NAME="NatSqrt2ExpSample"
DEFINITION_PARAMETERS=("k",)+OUTPUTS
NUMERATOR="((3*x)*d)"
DENOMINATOR="((D*p)*s)"
DEGREE="(k+2)"
GRAPH_PARTS=(ARGUMENT_GRAPH,
    f"NatExpWeightTable({DENOMINATOR},{DEGREE},wb,wc)",
    f"NatPowerWeightedPrefix({NUMERATOR},wb,wc,tb,tc,S {DEGREE})",
    "BetaAt(wb,wc,0,w0)","BetaAt(tb,tc,0,w0)",f"Factorial({DEGREE},f)",
    f"Pow({DENOMINATOR},{DEGREE},h)","w0=f*h",f"Sum(tb,tc,S {DEGREE},y)")
DEFINITION_SOURCE=_and(GRAPH_PARTS)
DEFINITION_DEPENDENCIES=("NatSqrt2LogArgument","NatExpWeightTable","NatPowerWeightedPrefix","BetaAt","Factorial","Pow","Sum")
DEFINITION_AST_SHA256="4d641d9ac1e39550399589fb8a5575ff014956ee6f1d6dd34e387ad595547f40"
GRAPH=DEFINITION_NAME+"("+",".join(DEFINITION_PARAMETERS)+")"
RECURRENCE=f"NatScaledExpRecurrence({DENOMINATOR},{NUMERATOR},tb,tc,{DEGREE})"
NORMALIZATION=f"forall j t f0 p0 q. Le(j,{DEGREE}) -> BetaAt(tb,tc,j,t) -> Factorial(j,f0) -> Pow({DENOMINATOR},j,p0) -> Pow({NUMERATOR},j,q) -> (t*f0)*p0=w0*q"
PARTS=(GRAPH,"~w0=0",f"~{DENOMINATOR}=0",f"Le({NUMERATOR},{DENOMINATOR})",RECURRENCE,NORMALIZATION)
NAMED_SOURCE="forall k. exists "+" ".join(OUTPUTS)+". "+_and(PARTS)
TARGET_SHA256="934fbe9c81ad757420933f697a47c0e82aa1b3e12a326f07d6080b94c7c3e24f"
ARGUMENT_ARCHIVE=dict(case="AP001",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-log-root-argument-v1/generation-process.json.gz",
    bytes=36868,sha256="a17185fef056d7c42ff883558b52653f744604189f5c64af567e93cd7306728c",
    raw_bytes=591277,raw_sha256="ba6ad03af1ca663cac58bb8555f9ebe1f591fd52209d475bb9d422e40fb51fa4",
    bundle_bytes=331302,bundle_sha256="8097cee51aafd444321e288943d96cc527f06ab8e4f5dd4fd3b06e8366c9dd10",
    nodes=161,root=160,target_ast_sha256="2b80a217cebb668c94e88b3a849c0738ad80d20aee1014489d6b8561839e89df")
ARCHIVES=(ARGUMENT_ARCHIVE,EXP_ARCHIVE)
ENDPOINT_SOURCES={"argument_exists":ARGUMENT_SOURCE,"exponential_exists":EXP_SOURCE}
ENDPOINT_OWNERS=dict(argument_exists="AP001",exponential_exists="CV070")
HELPER_DEPENDENCIES={"AP002":tuple(ENDPOINT_SOURCES)}


class ExpSampleError(ValueError):
    """Changed actual computation, normalization, graph or supplied source."""


def computation_registry():
    pool=dict(exponential_registry());result=dict(argument_registry())
    identity=("stable_id","parameters","template_source","template_formula","conceptual_dependencies")
    for name,spec in result.items():
        if name in pool and any(getattr(pool[name],key)!=getattr(spec,key) for key in identity):
            raise ExpSampleError("argument and exponential definition disagreement")
    visiting=set()
    def visit(name):
        if name in result:
            return
        if name in visiting or name not in pool:
            raise ExpSampleError("missing or cyclic exponential definition")
        visiting.add(name)
        for dependency in pool[name].conceptual_dependencies:
            visit(dependency)
        spec=pool[name]
        if spec.stable_id in {d.stable_id for d in result.values()}:
            raise ExpSampleError("exponential definition ID collision")
        result[name]=spec;visiting.remove(name)
    for name in (*DEFINITION_DEPENDENCIES,"NatScaledExpRecurrence"):
        visit(name)
    return MappingProxyType(result)


def definition_registry():
    from sqrt2_power_definitions import PARENT,parse_named
    from peano_lab.kernel.formulas import pretty_formula,parse_formula_in_context
    from peano_lab.library.defined_syntax import _definition
    from peano_lab.library.proof_bundle import encode_formula
    result=dict(computation_registry());parent=json.loads(PARENT.read_bytes())["reviewed_definitions"]
    ids={d.stable_id for d in result.values()}|{d["id"] for d in parent}|{f"ND{i:04d}" for i in range(382,448)}
    if DEFINITION_ID in ids or DEFINITION_NAME in result or any(d["name"]==DEFINITION_NAME for d in parent):
        raise ExpSampleError("finite exponential sample definition collision")
    formula=parse_named(DEFINITION_SOURCE,DEFINITION_PARAMETERS,result)
    if json_hash(encode_formula(formula))!=DEFINITION_AST_SHA256:
        raise ExpSampleError("finite exponential sample computation expansion changed")
    source=pretty_formula(formula,list(DEFINITION_PARAMETERS))
    spec=_definition(stable_id=DEFINITION_ID,name=DEFINITION_NAME,parameters=DEFINITION_PARAMETERS,
        template_source=source,summary="Actual finite log/root argument, factorial weights, power terms, heads, normalization arithmetic and sum; no accuracy clause.",
        category="irrationality_approximation_computation",conceptual_dependencies=DEFINITION_DEPENDENCIES)
    if spec.template_formula!=formula or parse_formula_in_context(source,list(DEFINITION_PARAMETERS))!=formula:
        raise ExpSampleError("exponential sample definition conservative roundtrip failed")
    result[DEFINITION_NAME]=spec
    return MappingProxyType(result)


def frozen_exp_sample_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ExpSampleError("AP002 exact total finite sample target changed")
    return target


def source_contract():
    return dict(code="AP002",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,all_precision_indices_including_zero=True,exponential_degree="k+2",output_rational="y/w0",
        all_actual_argument_weight_term_and_sum_computations_constructed=True,actual_factorial_and_denominator_power_retained=True,
        output_denominator_nonzero_proved=True,argument_denominator_nonzero_proved=True,
        exact_same_table_recurrence_proved=True,all_index_factorial_normalization_proved=True,
        new_definition_ids=[DEFINITION_ID],new_definition_ast_sha256=DEFINITION_AST_SHA256,
        definition_dependencies=list(DEFINITION_DEPENDENCIES),bounds_are_definition_clauses=False,definition_admissions=0,
        no_opaque_unused_trace=True,new_induction_needed=False,canonical_PR_approximation_algorithm_claim=False,
        value_independence_claim=False,analytic_identity_claim=False,analytic_limit_claim=False,original_HA_checked=False,
        authority="source_contract_not_proof_authority",closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def exp_sample_source_pins():
    result=log_root_argument_source_pins()
    for name,pin in scaled_exp_terms_source_pins().items():
        if name in result and result[name]!=pin:
            raise ExpSampleError("exponential sample source disagreement")
        result[name]=pin
    expected={"scripts/sqrt2_power_log_root_argument.py":"75d8f43a8b74ded5164c2d445c5dccc202eec4ec1987340c9f484b3f53024f38",
              "scripts/sqrt2_power_scaled_exp_terms.py":"329c4e741b144823db7d43c018756dd19033aa5beca1505b5f4d05ae7cbe316a",
              "scripts/sqrt2_power_scaled_exp_bound.py":"717128c4845645cca66209b12512d4de2905d6ecc4eebad8c04c197647f9ee0c",
              **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_exp_sample.py"):
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(2*1024**2+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ExpSampleError("exponential sample source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def _root(s):
    from peano_lab.kernel.terms import Add,Mul,Succ,Zero
    two=Succ(Succ(Zero()));three=Succ(two)
    def finish(t):
        arg=t.hyp("argument_data");exp=t.hyp("exponential_data")
        graph=conjunction(field(arg,0,7),*(field(exp,i,11) for i in (0,1,2,3,5,6,7,8)))
        return witness(t.terms(OUTPUTS),conjunction(graph,field(exp,4,11),field(arg,5,7),field(arg,6,7),field(exp,9,11),field(exp,10,11)))
    def argument(t):
        D,p,root,x,d,k=t.terms(("D","p","s","x","d","k"))
        constructed=apply(specialize(t,"exponential_exists",Mul(Mul(D,p),root),Mul(Mul(three,x),d),Add(k,two)),field(t.hyp("argument_data"),5,7))
        return eliminate(t,constructed,EXP_OUTPUTS,"exponential_data",finish)
    return introduce(s,("k",),(),lambda t:
        eliminate(t,specialize(t,"argument_exists",t.term("k")),ARGUMENT_OUTPUTS,"argument_data",argument))


def prove_exp_sample(*,limits=None):
    registry=definition_registry()
    return assemble_mixed_certificate(code="AP002",target=frozen_exp_sample_target(),registry=registry,
        helper_sources={},helper_hashes={},endpoint_sources=ENDPOINT_SOURCES,endpoint_owners=ENDPOINT_OWNERS,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories={"AP002":_root},
        pins=exp_sample_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
