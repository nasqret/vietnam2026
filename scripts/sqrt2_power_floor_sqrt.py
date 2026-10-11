"""SQ001: exact floor-square-root existence and uniqueness, audited reuse.

Select the inert 30-node dependency cone from the sealed historical Bertrand
archive before ordinary bounded decoding. Every retained body is replayed;
neither the old receipt nor an archive digest is a theorem oracle. The larger
historical input does not enlarge the final-certificate or kernel limits.
"""
from dataclasses import dataclass
from hashlib import sha256
import gc
import json
from pathlib import Path
from types import MappingProxyType

from sqrt2_power_quadratic_trace_exists import (
    ROOT,Scope,introduce,eliminate,witness,conjunction,apply,specialize,
    canonical,json_hash,_inert_metrics,quadratic_trace_exists_source_pins,
)

SCHEMA="sqrt2-power-floor-sqrt-v1"
NAMED_SOURCE="forall n. exists s. FloorSqrt(n,s) /\\ forall t. FloorSqrt(n,t) -> t=s"
TARGET_SHA256="da6b93cc7d0f9f4458be509f5f2405cac0063f79ab70acfef60768c09a0f2d5c"
ARTIFACT="research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json"
ARTIFACT_BYTES=14368763
ARTIFACT_SHA256="84078d40d2df7b072938975191fb70c95731059ced716a12050df4376e2d4883"
ANCESTOR_IDS=(0,1,2,3,4,5,6,7,11,12,14,15,16,17,18,19,23,30,40,43,44,45,47,49,52,53,54,254,255,256)
ANCESTOR_IDS_SHA256="cc47f0a76e927a67795f68f81b48bcf84e834741585b8adfa77e37aae8927af0"
ANCESTOR_ROWS_SHA256="3c822b766e465324a69d6e7b9d6f54fef64de0ae06d328aa73b71ea810a13746"
DEFINITION_ROWS=(
    ("PD0001","Le",("a","b"),"exists k. k+a=b",(),"41aa215143ee6830b61010c8a5f708440a429140bb4cad89663085337126eba0"),
    ("PD0002","Lt",("a","b"),"exists k. k+S a=b",(),"8245ec2119fd9d5b970a1d301ae58fa593733fff741593deb4858a5130b52cce"),
    ("PD0051","FloorSqrt",("n","s"),"Le(s*s,n) /\\ Lt(n,(S s)*(S s))",("Le","Lt"),"60d19f48168039fe515c016b1fa33b59e1029d2809e2332cf618fb0fbeff4505"),
)
DEFINITION_AST_SHA256={
    "Le":"5aad83c25902bc26b2fdbd296fabd3db359880ec4c568fe7e108ce1dc11dea46",
    "Lt":"d7bdf8ed287c3672fa78951c9cabe8f8814d7fcf1fb1ffcfee2d0d3b41251531",
    "FloorSqrt":"f4264cad2e3ce46c72dfca373ae2b34f13465abe4d8169062d7c2d37d2752cd7",
}
ENDPOINTS={
    "total":(255,"forall n. exists s. FloorSqrt(n,s)","732f6e3922851411296b6ff56cfc736d4261159720f56a110add5a90fe23d839"),
    "monotone":(256,"forall x y s t. FloorSqrt(x,s) -> FloorSqrt(y,t) -> Le(x,y) -> Le(s,t)","22d1ea4591f5523e145c05c43b0f32a0d19d456bf762007319a4e933c2232479"),
    "le_refl":(14,"forall a. Le(a,a)","5d67d5564fa913d869e0c0eefb7a980638c6e0a27629442d3e36a23f023641ec"),
    "le_antisym":(19,"forall a b. Le(a,b) -> Le(b,a) -> a=b","9569490fc966dfc81449d119d1e041a916dda90be8ae934111323b3c4e1217e9"),
}


class FloorSqrtError(ValueError):
    """Changed exact definition, proof cone, target, source or fixed limit."""


def definition_registry():
    from sqrt2_power_definitions import PARENT,PARENT_SHA256,parse_named
    from peano_lab.kernel.formulas import parse_formula_in_context
    from peano_lab.library.defined_syntax import DEFINITIONS_BY_NAME,_definition
    from peano_lab.library.bertrand_ceil_sqrt_candidate import floor_sqrt_relation
    from peano_lab.library.proof_bundle import encode_formula
    raw=PARENT.read_bytes()
    if sha256(raw).hexdigest()!=PARENT_SHA256:
        raise FloorSqrtError("sealed conservative definition parent changed")
    historical={row["name"]:row for row in json.loads(raw)["reviewed_definitions"]}
    registry={}
    for identifier,name,parameters,source,dependencies,digest in DEFINITION_ROWS:
        old=historical[name]
        if (old["id"]!=identifier or tuple(old["parameters"])!=parameters
                or tuple(old["dependencies"])!=dependencies or old["expansion_sha256"]!=digest
                or not set(dependencies)<=registry.keys()):
            raise FloorSqrtError("historical definition identity or DAG changed")
        formula=parse_named(source,parameters,registry)
        if json_hash(encode_formula(formula))!=DEFINITION_AST_SHA256[name]:
            raise FloorSqrtError("historical definition expansion changed")
        expanded=(floor_sqrt_relation("n","s",tag="bertrand_defined_floor_sqrt")
                  if name=="FloorSqrt" else DEFINITIONS_BY_NAME[name].template_source)
        # The published expansion fingerprint hashes source text, not its AST.
        # Check both independently; preserve the original template unchanged.
        if sha256(expanded.encode()).hexdigest()!=digest:
            raise FloorSqrtError("historical definition source fingerprint changed")
        spec=_definition(stable_id=identifier,name=name,parameters=parameters,
            template_source=expanded,summary="Exact conservative reuse from the published proof library.",
            category="irrationality_square_root",conceptual_dependencies=dependencies)
        if spec.template_formula!=formula or parse_formula_in_context(expanded,list(parameters))!=formula:
            raise FloorSqrtError("historical definition failed capture-safe roundtrip")
        registry[name]=spec
    return MappingProxyType(registry)


def frozen_floor_sqrt_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion=strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise FloorSqrtError("SQ001 exact unconditional total-and-unique target changed")
    return target


def source_contract():
    return dict(code="SQ001",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,arbitrary_natural_input=True,zero_input_allowed=True,
        actual_floor_root_constructed=True,all_competing_roots_equal=True,
        audited_reuse_not_new_discovery=True,reused_definition_ids=["PD0001","PD0002","PD0051"],
        new_definition_ids=[],definition_admissions=0,new_induction_needed=False,
        real_square_root_or_dyadic_accuracy_claim=False,analytic_limit_claim=False,
        original_HA_checked=False,authority="source_contract_not_proof_authority",
        closes_IR013=False,closes_IR072=False,IR_parents_closed=0,library_admissions=0)


def floor_sqrt_source_pins():
    result=quadratic_trace_exists_source_pins()
    expected={
        "scripts/sqrt2_power_quadratic_trace_exists.py":"4269d6b9a2282fad3870b408578e2894544c4b172ea76ea2891945adce25ba1a",
        "scripts/sqrt2_power_definitions.py":"365f142974c3958aa5cad2430ed93fc3866e8abbadea0c357cb906574ff0220b",
        "scripts/sqrt2_power_binary_dag.py":"517535807fe06a317fae48c5fc5f47db944b0c32904fb8d02a0a1b102af12227",
        "peano-lab/py/peano_lab/library/bertrand_ceil_sqrt_candidate.py":"745db5174c6f9348ec97fc6076a909f1dd98e04e899e5a26ebd38b61b842b237",
        ARTIFACT:ARTIFACT_SHA256,
    }
    for name in (*expected,"scripts/sqrt2_power_floor_sqrt.py"):
        cap=ARTIFACT_BYTES if name==ARTIFACT else 2*1024**2
        with (ROOT/name).open("rb") as stream:
            raw=stream.read(cap+1)
        digest=sha256(raw).hexdigest()
        if len(raw)>cap or name in expected and digest!=expected[name]:
            raise FloorSqrtError("floor-square-root source or actual archive changed")
        result[name]=dict(bytes=len(raw),sha256=digest)
    return result


def inert_ancestor_rows(artifact_path=None):
    """Prune untrusted historical JSON, without decoding or trusting its proof."""
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    path=ROOT/ARTIFACT if artifact_path is None else Path(artifact_path)
    with path.open("rb") as stream:
        raw=stream.read(ARTIFACT_BYTES+1)
    if len(raw)!=ARTIFACT_BYTES or sha256(raw).hexdigest()!=ARTIFACT_SHA256:
        raise FloorSqrtError("sealed Bertrand archive bytes changed")
    value=json.loads(raw)
    del raw
    if (type(value) is not list or len(value)!=4 or value[0]!="peano-lab-bundle-v1"
            or value[1]!=543 or type(value[3]) is not list or len(value[3])!=544
            or value[2]!=value[3][543][1]):
        raise FloorSqrtError("sealed Bertrand archive envelope changed")
    for old,row in enumerate(value[3]):
        if (type(row) is not list or len(row)!=4 or type(row[0]) is not int or type(row[2]) is not list
                or any(type(d) is not int or not 0<=d<old for d in row[2]) or len(row[2])!=len(set(row[2]))):
            raise FloorSqrtError("historical ordered dependency row changed")
    seen,pending=set(),[row[0] for row in ENDPOINTS.values()]
    while pending:
        old=pending.pop()
        if old not in seen:
            seen.add(old);pending.extend(value[3][old][2])
    ids=tuple(sorted(seen));rows=tuple(value[3][old] for old in ids)
    if ids!=ANCESTOR_IDS or json_hash(ids)!=ANCESTOR_IDS_SHA256 or json_hash(rows)!=ANCESTOR_ROWS_SHA256:
        raise FloorSqrtError("exact historical dependency cone changed")
    registry=definition_registry()
    for old,source,digest in ENDPOINTS.values():
        row=value[3][old]
        if json_hash(row)!=digest or row[1]!=encode_formula(parse_named(source,registry=registry)):
            raise FloorSqrtError("exact historical endpoint differs from frozen formula or body")
    return ids,rows


def _root(s):
    def unique(t):
        n,root,other=t.terms(("n","s","t"))
        refl=specialize(t,"le_refl",n)
        lower=apply(specialize(t,"monotone",n,n,other,root),t.hyp("other"),t.hyp("floor"),refl)
        upper=apply(specialize(t,"monotone",n,n,root,other),t.hyp("floor"),t.hyp("other"),refl)
        return apply(specialize(t,"le_antisym",other,root),lower,upper)
    def finish(t):
        return witness((t.term("s"),),conjunction(t.hyp("floor"),introduce(t,("t",),("other",),unique)))
    return introduce(s,("n",),(),lambda t:
        eliminate(t,specialize(t,"total",t.term("n")),("s",),"floor",finish))


@dataclass(frozen=True)
class FloorSqrtCertificate:
    target: object
    bundle: object
    payload: str
    receipt: object
    max_proof_depth: int
    provenance: dict


def prove_floor_sqrt(*,limits=None,artifact_path=None):
    from sqrt2_power_binary_dag import BinaryDAGLimits,_body_metrics,_row_preflight
    from peano_lab.library.proof_bundle import encode_formula,encode_proof,decode_proof_bundle,check_proof_bundle
    limits=BinaryDAGLimits() if limits is None else limits
    if type(limits) is not BinaryDAGLimits:
        raise FloorSqrtError("expected unchanged BinaryDAGLimits")
    before=floor_sqrt_source_pins();target=frozen_floor_sqrt_target()
    ids,original=inert_ancestor_rows(artifact_path)
    remap={old:new for new,old in enumerate(ids)}
    rows=[];total=deepest=0
    for old,row in zip(ids,original):
        count,depth=_inert_metrics(row[3],limits)
        total+=count;deepest=max(deepest,depth)
        if row[0]<8*count+16:
            raise FloorSqrtError("historical proof fuel below body bound")
        rows.append([row[0],row[1],[remap[d] for d in row[2]],row[3]])
    ancestor_total=total
    body=introduce(Scope(),(),tuple(ENDPOINTS),_root)
    count,depth=_body_metrics(body,limits);total+=count;deepest=max(deepest,depth)
    if total>limits.max_total_body_nodes or len(rows)+1>limits.max_nodes:
        raise FloorSqrtError("floor-root ordinary certificate resource bound exceeded")
    _row_preflight(target,body,limits)
    rows.append([8*count+16,encode_formula(target),[remap[v[0]] for v in ENDPOINTS.values()],encode_proof(body)])
    payload=canonical(["peano-lab-bundle-v1",len(rows)-1,encode_formula(target),rows]).decode()+"\n"
    if len(payload.encode())>limits.max_payload_bytes:
        raise FloorSqrtError("floor-root canonical byte bound exceeded")
    del original,rows,body
    gc.collect()
    bundle,decoded=decode_proof_bundle(payload,limits=limits.bundle_limits())
    if decoded!=target:
        raise FloorSqrtError("decoded target differs from exact floor-root contract")
    receipt=check_proof_bundle(bundle,target,limits=limits.bundle_limits())
    if receipt.target!=target or floor_sqrt_source_pins()!=before:
        raise FloorSqrtError("floor-root source or target changed during replay")
    provenance=dict(source_contract(),source_pins=before,original_HA_checked=True,
        empty_context=True,canonical_bytes_replayed=True,actual_ancestor_nodes=len(ids),
        actual_ancestor_body_nodes=ancestor_total,actual_ancestor_ids=list(ids),
        actual_ancestor_rows_sha256=ANCESTOR_ROWS_SHA256,ordered_dependency_remapping_only=True,
        historical_input_bytes=ARTIFACT_BYTES,historical_input_not_decoded_as_certificate=True,
        endpoint_bundle_indices={name:remap[v[0]] for name,v in ENDPOINTS.items()},
        new_induction_count=0,solver_calls=0,ring_normalizer_calls=0,local_have_compiler_calls=0,
        new_axioms=[],external_certificate_references=[],independent_lean_checked=False)
    return FloorSqrtCertificate(target,bundle,payload,receipt,deepest,provenance)
